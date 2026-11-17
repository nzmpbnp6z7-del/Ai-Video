# -*- coding: utf-8 -*-
"""The Night Watchman's Rules – Blocklook-Version (englisch, Stimme: ElevenLabs Roger).

Aufruf:  python3 film.py [teil ...]   |   python3 film.py --preview N  (Einzelbilder)
"""
import os, sys, math, json, subprocess, wave
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ND = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ND)
import story_en as story
import sound
import stage as stg
import chars as CH
import sets as SETS
import post
from engine import Mesh, rot_y, translate

W, H, FPS, SR = 1080, 1920, 30, 44100
VOICE = os.path.join(ND, "voice_en")
BUILD = os.path.join(ND, "build", "en")
OUT = os.path.join(ND, "output_en")
os.makedirs(BUILD, exist_ok=True)
os.makedirs(OUT, exist_ok=True)
LILITA = os.path.join(HERE, "fonts", "LilitaOne.woff")
INTER = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
INTER_R = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
INTER_B = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SYM = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


@lru_cache(None)
def font(p, s):
    return ImageFont.truetype(p, s)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


# =====================================================================
#  AUDIO
# =====================================================================
def load_mp3(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768


def rubberband(x, pitch):
    tmp_in, tmp_out = os.path.join(BUILD, "rb_in.wav"), os.path.join(BUILD, "rb_out.wav")
    write_wav(tmp_in, x)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp_in, "-af", f"rubberband=pitch={pitch}", tmp_out], check=True)
    with wave.open(tmp_out) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768


def fx(x, who, hall=False):
    if who == "mama":
        x = np.tanh(sound.fft_filter(x, 350, 3400) * 1.6) * 0.7
    elif who == "mama_door":
        x = sound.reverb(sound.fft_filter(x, 120, 1700) * 1.5, 2.4, 0.5)
    elif who == "walter_door":
        x = sound.reverb(sound.fft_filter(x, 150, 2800) * 1.2, 1.2, 0.3)
    elif who == "creature":
        lo = rubberband(x, 0.72)
        n = max(len(lo), len(x))
        y = np.zeros(n)
        y[:len(lo)] += lo
        y[:len(x)] += x * 0.35
        x = sound.reverb(y, 3.0, 0.5)
    elif who == "mia_dark":
        x = sound.reverb(rubberband(x, 0.8), 2.5, 0.45)
    if hall:
        x = sound.reverb(x, 2.4, 0.5)
    return x / (np.abs(x).max() + 1e-9) * 0.85


def part_voice(n):
    audio = load_mp3(os.path.join(VOICE, f"p{n}a.mp3"))
    words = json.load(open(os.path.join(VOICE, f"p{n}_words.json")))["words"]
    segs, cur = [], []
    for w in words:
        t = w["text"]
        if t == "[pause]":
            segs.append(cur)
            cur = []
        elif not (t.startswith("[") or t.endswith("]")):
            cur.append(w)
    segs.append(cur)
    out = []
    for i, ws in enumerate(segs):
        a = max(0.0, ws[0]["start"] - 0.06)
        nxt = segs[i + 1][0]["start"] - 0.03 if i + 1 < len(segs) else len(audio) / SR
        b = min(nxt, ws[-1]["end"] + 0.22)
        clip = audio[int(a * SR):int(b * SR)].copy()
        fade = int(0.02 * SR)
        clip[:fade] *= np.linspace(0, 1, fade)
        clip[-fade:] *= np.linspace(1, 0, fade)
        rel = [dict(text=w["text"], start=w["start"] - a, end=w["end"] - a) for w in ws]
        out.append((clip, rel, b - a))
    return out


def envelope(x):
    hop = SR // FPS
    n = len(x) // hop + 1
    xx = np.pad(x, (0, n * hop - len(x)))
    e = np.sqrt((xx.reshape(n, hop) ** 2).mean(axis=1))
    return e / (np.percentile(e, 95) + 1e-9)


def write_wav(path, x):
    with wave.open(path, "wb") as w_:
        w_.setnchannels(1)
        w_.setsampwidth(2)
        w_.setframerate(SR)
        w_.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


# =====================================================================
#  TIMELINE
# =====================================================================
COUNTDOWN = 5


def build_timeline(part):
    voice = part_voice(part["n"])
    assert len(voice) == len(part["segs"]), "Segmentanzahl passt nicht"
    segs, t, prev = [], 0.0, None
    for i, (s0, (clip, words, cdur)) in enumerate(zip(part["segs"], voice)):
        s = dict(s0)
        s.setdefault("opt", {})
        s["audio"] = fx(clip, s["who"], s.get("hall")) * s.get("gain", 1.0)
        s["env"] = envelope(clip)
        s["tts_start"] = 0.12 + (0.45 if i == 0 else 0.0)
        s["tts_dur"] = cdur
        s["words"] = [dict(w, start=w["start"] + s["tts_start"], end=w["end"] + s["tts_start"]) for w in words]
        dur = s["tts_start"] + cdur + s.get("pad", 0.2)
        if "choice" in s:
            s["cd_start"] = s["tts_start"] + cdur + 0.25
            dur = s["cd_start"] + COUNTDOWN + 0.35
        s["start"], s["dur"] = t, max(dur, 1.4)
        s["new_shot"] = s["shot"] != prev
        prev = s["shot"]
        t += s["dur"]
        segs.append(s)
    g0, gi = 0, 0
    for s in segs:
        if s["new_shot"]:
            g0, gi = s["start"], 0
        s["g0"], s["gi"] = g0, gi
        gi += 1
    for s in segs:
        s["gend"] = max(x["start"] + x["dur"] for x in segs if x["g0"] == s["g0"])
    return segs, t


# =====================================================================
#  HILFSBILDER (Handy, Karte)
# =====================================================================
def vgrad(size, top, bot):
    w, h = size
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top)[None, None] * (1 - t) + np.array(bot)[None, None] * t
    return Image.fromarray(np.repeat(a, w, axis=1).astype(np.uint8))


def phone_frame():
    im = Image.new("RGBA", (360, 720), 0)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 359, 719], 40, fill=(16, 16, 18, 255), outline=(80, 80, 86, 255), width=6)
    return im


@lru_cache(32)
def phone_call_img(active, secs, pulse):
    im = phone_frame()
    scr = vgrad((330, 690), (34, 46, 74), (10, 12, 20)).convert("RGBA")
    d = ImageDraw.Draw(scr)
    d.text((24, 14), "12:30", font=font(INTER_B, 18), fill=(230, 230, 240))
    d.ellipse([110, 110, 220, 220], fill=(200, 120, 140))
    tw = d.textlength("M", font=font(INTER, 64))
    d.text((165 - tw / 2, 128), "M", font=font(INTER, 64), fill=(255, 255, 255))
    tw = d.textlength("Mom", font=font(INTER, 48))
    d.text((165 - tw / 2, 240), "Mom", font=font(INTER, 48), fill=(255, 255, 255))
    d.text((165 + tw / 2 + 6, 248), "♥", font=font(SYM, 36), fill=(255, 90, 110))
    sub = "incoming call…" if not active else f"0:{secs:02d}  ·  speaker on"
    tw = d.textlength(sub, font=font(INTER_R, 20))
    d.text((165 - tw / 2, 306), sub, font=font(INTER_R, 20), fill=(190, 200, 220))
    if not active:
        for cx, col, sym in ((90, (230, 60, 60), "✕"), (240, (60, 200, 100), "✆")):
            if col[1] == 200 and pulse:
                r = 40 + pulse * 3
                d.ellipse([cx - r, 560 - r, cx + r, 560 + r], outline=(60, 200, 100), width=3)
            d.ellipse([cx - 40, 520, cx + 40, 600], fill=col)
            tw = d.textlength(sym, font=font(SYM, 40))
            d.text((cx - tw / 2, 534), sym, font=font(SYM, 40), fill=(255, 255, 255))
    else:
        for i, (lab, on) in enumerate((("mute", False), ("keypad", False), ("speaker", True))):
            cx = 60 + i * 105
            d.ellipse([cx - 34, 400, cx + 34, 468], fill=(240, 240, 245) if on else (60, 66, 80))
            tw = d.textlength(lab, font=font(INTER_R, 16))
            d.text((cx - tw / 2, 476), lab, font=font(INTER_R, 16), fill=(200, 205, 215))
        d.ellipse([125, 560, 205, 640], fill=(230, 60, 60))
    mask = Image.new("L", scr.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, 329, 689], 32, fill=255)
    im.paste(scr, (15, 15), mask)
    return im


@lru_cache(4)
def phone_msg_img(show_last):
    im = phone_frame()
    scr = Image.new("RGBA", (330, 690), (14, 16, 22, 255))
    d = ImageDraw.Draw(scr)
    d.text((24, 14), "1:14", font=font(INTER_B, 18), fill=(230, 230, 240))
    d.rectangle([0, 48, 330, 112], fill=(26, 30, 40))
    d.ellipse([16, 58, 60, 102], fill=(200, 120, 140))
    d.text((30, 64), "M", font=font(INTER, 26), fill=(255, 255, 255))
    d.text((72, 60), "Mom", font=font(INTER, 24), fill=(255, 255, 255))
    d.text((72, 88), "online", font=font(INTER_R, 15), fill=(140, 200, 150))

    def bubble(y, text, time, mine=False):
        f = font(INTER_R, 19)
        words, lines, cur = text.split(), [], ""
        for w_ in words:
            t = (cur + " " + w_).strip()
            if d.textlength(t, font=f) < 210:
                cur = t
            else:
                lines.append(cur)
                cur = w_
        lines.append(cur)
        h = len(lines) * 25 + 36
        x0 = 14 if not mine else 76
        d.rounded_rectangle([x0, y, x0 + 240, y + h], 16, fill=(40, 46, 60) if not mine else (30, 90, 70))
        for i, ln in enumerate(lines):
            d.text((x0 + 14, y + 10 + i * 25), ln, font=f, fill=(240, 240, 245))
        d.text((x0 + 190, y + h - 22), time, font=font(INTER_R, 13), fill=(160, 170, 185))
        return y + h + 14

    y = 130
    y = bubble(y, "Good luck on your first night shift, honey!", "9:30 PM")
    y = bubble(y, "Thanks Mom :)", "9:41 PM", mine=True)
    if show_last:
        y0 = y
        bubble(y, "Been lying in bed for hours, can't sleep. Be careful!", "1:14 AM")
        d.text((236, y0 + 6), "♥", font=font(SYM, 20), fill=(255, 90, 110))
    mask = Image.new("L", scr.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, 329, 689], 32, fill=255)
    im.paste(scr, (15, 15), mask)
    return im


@lru_cache(16)
def card_tex(reveal, hl):
    return SETS.card_img(story.RULES, reveal, hl)


# =====================================================================
#  SHOTS
# =====================================================================
class C:
    pass


def head_pos(name, pose):
    c = CH.get(name)
    m = c.matrices(pose)["head"]
    hp = [p for p in c.parts if p.name == "head"][0]
    hy = (hp.hi[1] + hp.lo[1]) / 2 * CH.P
    v = m @ np.array([0, hy, 0, 1.0])
    return tuple(v[:3])


def mouth_state(c, who):
    if c.seg.get("talk") and c.seg["who"] == who:
        k = int((c.lt - c.seg["tts_start"]) * FPS)
        if 0 <= k < len(c.env):
            v = c.env[k]
            return "0" if v < 0.12 else ("1" if v < 0.42 else "2")
    return "0"


def shake(c, amp, speed=1.0):
    t = c.t * speed
    return (amp * (math.sin(t * 13.1) + 0.5 * math.sin(t * 29.7)) / 1.5,
            amp * (math.sin(t * 11.3 + 1) + 0.5 * math.sin(t * 23.9)) / 1.5, 0)


def handheld(eye, c, amp=0.025):
    s = shake(c, amp, 0.35)
    return (eye[0] + s[0], eye[1] + s[1], eye[2])


def angle(c, angles, cut=2.9):
    """Wählt Kamerawinkel nach Gruppenzeit (schnelle Schnitte wie im Referenzvideo)."""
    k = int(c.gt / cut)
    u = (c.gt - k * cut) / cut
    return angles[k % len(angles)], u, k


def cam_from(a, u):
    e0, t0, e1, t1, fov = a
    u = ease(u)
    return lerp(e0, e1, u), lerp(t0, t1, u), fov


def sit_pose(pos, yaw=0.0, seat=1.05, size=1.0, legs=12):
    p = CH.pose_sit()
    p.update(pos=(pos[0], seat - legs * CH.P * size, pos[2]), yaw=yaw)
    return p


def S(**k):
    return k


# ---------------------------------------------------------------- einzelne Einstellungen
def sh_hook(c):
    pose = sit_pose((13.3, 0, 23.5), seat=3.5, size=0.78, legs=9)
    pose["head"] = (0.05, 0, -0.18)
    hp = head_pos("mia", pose)
    z = ease(c.lt / c.dur)
    eye = (hp[0] + 0.05, hp[1] + 0.05, hp[2] + 2.3 - 0.7 * z)
    return S(set="atrium", eye=handheld(eye, c, 0.03), target=hp, fov=42,
             chars=[("mia", pose, "black", "grin")],
             spot=dict(pos=(hp[0] + 0.2, hp[1] - 0.3, hp[2] + 2.5), dir=(0, 0.05, -1), col=(3.0, 2.8, 2.5), angle=18, range=12),
             env=dict(light_scale=0.15, amb=0.35), post=dict(grade=(1.05, 0.9, 0.9), flick=0.5))


def sh_exterior(c):
    p = ease(c.gt / c.gdur)
    jpos = (2.0 - 1.5 * p, 0, 15.0 - 9.0 * p)
    jp = CH.pose_walk(c.t, 1.0, 0.55)
    jp.update(pos=jpos, yaw=math.pi)
    if c.opt.get("push"):
        u = ease(c.lt / c.dur)
        eye, tgt, fov = lerp((4, 2.5, 24), (1.5, 9.5, 12), u), lerp((0, 8, -12), (0, 14.5, -12), u), 55
    else:
        a, u, _ = angle(c, [((6, 2.0, 27), (0, 7.5, -12), (5, 2.6, 23), (0, 8.5, -12), 52),
                             ((-5.5, 1.5, jpos[2] - 1), (jpos[0], 1.4, jpos[2]), (-5.5, 1.6, jpos[2] + 1), (jpos[0], 1.5, jpos[2] - 1), 45)])
        eye, tgt, fov = cam_from(a, u)
        if a[0][0] < 0:
            eye, tgt = (-5.5, 1.5, jpos[2] - 0.5), (jpos[0], 1.4, jpos[2] - 1.0)
    flash = 0.0
    for name, o in c.seg.get("sfx", []):
        if name == "thunder" and c.lt >= o:
            dt = c.lt - o
            flash = math.exp(-dt / 0.12) + (0.6 * math.exp(-(dt - 0.25) / 0.1) if dt > 0.25 else 0)
    neon_off = (c.fi // 2) % 41 in (0, 3)
    return S(set="exterior", eye=handheld(eye, c), target=tgt, fov=fov, chars=[("jonas", jp)],
             env=dict(amb=1.0 + 2.5 * flash), post=dict(flash=flash * 0.6, grade=(0.92, 0.96, 1.1)), rain=True,
             neon_off=neon_off)


def walter_seated(c, serious=False):
    e = "closed" if CH.blink(c.t) else ("serious" if serious else "open")
    pose = sit_pose((6.5, 0, 3.0), seat=1.05)
    tk = 0.04 * math.sin(c.t * 5.3) if c.seg.get("talk") else 0
    pose.update(arm_r=(-0.95, 0, 0.05), arm_l=(-0.95, 0, -0.05), head=(0.04 + tk, 0.08 * math.sin(c.t * 0.7), 0))
    return pose, e


def sh_walter(c):
    pose, e = walter_seated(c, c.opt.get("serious"))
    hp = head_pos("walter", pose)
    if c.opt.get("close"):
        u = ease(c.lt / c.dur)
        eye, tgt, fov = lerp((hp[0] + 0.6, hp[1] + 0.1, hp[2] + 3.2), (hp[0] + 0.35, hp[1] + 0.05, hp[2] + 2.5), u), (hp[0], hp[1] - 0.15, hp[2]), 40
    else:
        a, u, _ = angle(c, [((6.5, 2.9, 9.0), hp, (6.5, 2.8, 8.2), hp, 42),
                             ((hp[0] + 0.7, hp[1] + 0.1, hp[2] + 2.9), (hp[0], hp[1] - 0.15, hp[2]), (hp[0] + 0.5, hp[1] + 0.05, hp[2] + 2.6), (hp[0], hp[1] - 0.15, hp[2]), 40),
                             ((9.4, 3.2, 8.4), hp, (9.0, 3.1, 8.0), hp, 42)], cut=2.6)
        eye, tgt, fov = cam_from(a, u)
    return S(set="office", eye=handheld(eye, c, 0.015), target=tgt, fov=fov, chars=[("walter", pose, e, mouth_state(c, "walter"))],
             post=dict(grade=(1.05, 0.98, 0.9)))


CARD_POS = (5.6, 1.295, 5.65)


def sh_card(c):
    rv, hl = c.opt.get("reveal", 4), c.opt.get("hl")
    img = card_tex(rv, hl)
    prev = c.prev_opt if c.prev_shot == "card" else None
    if prev is not None and (prev.get("reveal"), prev.get("hl")) != (rv, hl) and c.lt < 0.45:
        img = Image.blend(card_tex(prev.get("reveal", 4), prev.get("hl")), img, ease(c.lt / 0.45))
        key = ("blend", int(c.lt * 30))
    else:
        key = (rv, hl)
    dz = 0.0
    if rv == 0:
        dz = 1.4 * (1 - ease(c.lt / 0.6))
    x, y, z = CARD_POS
    hw, hd = 0.55, 0.675
    corners = [(x - hw, y, z + hd + dz), (x + hw, y, z + hd + dz), (x + hw, y, z - hd + dz), (x - hw, y, z - hd + dz)]
    dec = ("card", img, corners, key)
    u = c.gt / c.gdur
    eye = (x + 0.05 * math.sin(c.t * 0.5), 3.35 - 0.12 * u, z + 1.0 - 0.08 * u)
    return S(set="office", eye=eye, target=(x, y, z + 0.32), fov=44, decals=[dec],
             lights_extra=[((x, 2.4, z + 0.8), (0.6, 0.5, 0.35), 4)], post=dict(grade=(1.05, 1.0, 0.92), bloom=0.25))


def sh_leave(c):
    p = ease(c.lt / c.dur)
    wp = CH.pose_walk(c.t, 0.8, 0.45)
    wp.update(pos=(0.3 + 1.2 * p, 0, -1.2 - 9 * p), yaw=math.pi)
    eye = (0.6, 1.9, 6.5 - 1.0 * p)
    return S(set="entrance", eye=handheld(eye, c), target=(0.8, 1.4, -8), fov=48, chars=[("walter", wp)],
             rain_region=True, post=dict(grade=(0.92, 0.96, 1.1)))


def jonas_walk_pos(c, z0=92.0, speed=1.6):
    return (11.2, 0, z0 - speed * c.gt)


def torch_spot(origin, target, col=(3.6, 3.4, 3.0), angle=17, rng=45, on=True):
    if not on:
        return None
    d = np.subtract(target, origin)
    d = d / (np.linalg.norm(d) + 1e-9)
    return dict(pos=tuple(origin), dir=tuple(d), col=col, angle=angle, soft=0.05, range=rng)


def sh_corridor_jonas(c):
    jpos = jonas_walk_pos(c)
    jp = CH.pose_walk(c.t, 0.85, 0.45)
    jp.update(pos=jpos, yaw=math.pi, arm_r=(-1.45, 0, 0))
    hand = (jpos[0] - 0.36, 1.05, jpos[2] - 0.55)
    spot = torch_spot(hand, (jpos[0] + 0.3 * math.sin(c.t * 0.6), 0.6, jpos[2] - 14))
    a, u, k = angle(c, [((jpos[0] + 0.85, 2.25, jpos[2] + 2.3), (jpos[0] - 0.3, 1.4, jpos[2] - 12)),
                        ((jpos[0] - 0.4, 1.55, jpos[2] - 4.2), (jpos[0], 1.5, jpos[2])),
                        ((jpos[0] - 6.5, 0.5, jpos[2] - 2.5), (jpos[0], 1.2, jpos[2] - 6))], cut=2.6)[0], 0, 0
    eye, tgt = a
    return S(set="corridor", eye=handheld(eye, c, 0.03), target=tgt, fov=55, chars=[("jonas", jp)], spot=spot,
             lights_extra=[((jpos[0] + 1.2, 2.5, jpos[2] + 2.5), (0.25, 0.27, 0.35), 4.5)],
             post=dict(grade=(0.92, 0.97, 1.1)))


def phone_decal(c, img, key, eye, fwd_t, dist=0.75, drop=-0.05, size=0.2, buzz=False):
    e = np.array(eye, float)
    f = np.subtract(fwd_t, eye)
    f = f / np.linalg.norm(f)
    right = np.cross(f, (0, 1, 0))
    right /= np.linalg.norm(right)
    up = np.cross(right, f)
    cen = e + f * dist - up * drop
    if buzz:
        cen = cen + right * 0.012 * math.sin(c.fi * 2.3)
    hw, hh = size / 2, size
    tilt = up * 0.0
    corners = [tuple(cen - right * hw - up * hh + f * 0.05), tuple(cen + right * hw - up * hh + f * 0.05),
               tuple(cen + right * hw + up * hh - f * 0.05), tuple(cen - right * hw + up * hh - f * 0.05)]
    return ("phone", img, corners, key)


def sh_phone_call(c):
    active = bool(c.opt.get("active"))
    pulse = int(((c.lt * 1.3) % 1.0) * 10) if not active else 0
    secs = 7 + int(c.lt) if active else 0
    img = phone_call_img(active, secs, pulse)
    buzz = any(n == "buzz" and 0 <= c.lt - o < 1.0 and ((c.lt - o) % 0.6) < 0.4 for n, o in c.seg.get("sfx", []))
    eye = handheld((11.0, 1.72, 86.0), c, 0.02)
    tgt = (11.0, 1.35, 70.0)
    dec = phone_decal(c, img, ("call", active, secs, pulse), eye, tgt, buzz=buzz)
    return S(set="corridor", eye=eye, target=tgt, fov=55, decals=[dec], decal_emit=1.0,
             lights_extra=[((11.0, 1.4, 85.2), (0.25, 0.3, 0.45), 2.5)], post=dict(grade=(0.92, 0.97, 1.1)))


def sh_watcher(c):
    appear = ease((c.lt - 0.8) / 1.4)
    tilt = 0.45 * ease((c.lt - 2.4) / 1.2)
    pose = {"pos": (13.0 - 2.0 * appear, 0, 34.0), "yaw": 0.0, "head": (0, 0, tilt),
            "arm_r": (0.04, 0, 0.04), "arm_l": (0.04, 0, -0.04)}
    chs = [("creature", pose, "open", "0", (0.08, 0.08, 0.09))] if c.lt > 0.6 else []
    z = ease(c.lt / c.dur)
    return S(set="corridor", eye=handheld((11.0, 1.75, 88.0), c, 0.02), target=(11.0, 1.9, 34.0), fov=50 - 30 * z, chars=chs,
             lights_extra=[((11.0, 3.5, 29.0), (1.4, 1.4, 1.5), 10)], env=dict(light_scale=0.5), post=dict(grade=(0.9, 0.95, 1.1)))


def jonas_seated(c, scared=False):
    e = "wide" if scared else ("closed" if CH.blink(c.t, 0.4) else "open")
    pose = sit_pose((6.5, 0, 3.0), seat=1.05)
    tr = 0.02 * math.sin(c.t * 31) if scared else 0
    pose.update(arm_r=(-0.95, 0, 0.05), arm_l=(-0.95, 0, -0.05), head=(0.03 + tr, 0.15 * math.sin(c.t * 0.45), 0))
    return pose, e


def sh_jonas_office(c):
    pose, e = jonas_seated(c, c.opt.get("scared"))
    hp = head_pos("jonas", pose)
    a, u, _ = angle(c, [((6.5, 2.8, 8.6), hp, (6.5, 2.7, 7.9), hp, 42),
                        ((hp[0] - 0.6, hp[1] + 0.05, hp[2] + 2.8), (hp[0], hp[1] - 0.15, hp[2]), (hp[0] - 0.4, hp[1], hp[2] + 2.5), (hp[0], hp[1] - 0.15, hp[2]), 40)], cut=2.8)
    eye, tgt, fov = cam_from(a, u)
    lvl = c.seg.get("radio", 0.3)
    puls = 0.6 + 0.4 * abs(math.sin(c.fi * 0.7))
    return S(set="office", eye=handheld(eye, c, 0.02), target=tgt, fov=fov, chars=[("jonas", pose, e, mouth_state(c, "jonas"))],
             lights_extra=[((3.9, 2.0, 6.3), (1.2 * lvl * puls, 0.6 * lvl * puls, 0.15 * lvl), 4)],
             post=dict(grade=(0.96, 1.0, 1.0)))


def sh_door3(c):
    knock = any(n == "knock" and 0 <= c.lt - o < 0.75 for n, o in c.seg.get("sfx", []))
    a, u, k = angle(c, [((5.5, 1.8, 9.5), (5.5, 2.0, 2.0), (5.5, 1.7, 8.2), (5.5, 1.9, 2.0), 52),
                        ((4.6, 0.35, 4.2), (5.5, 0.12, 2.0), (4.8, 0.3, 3.8), (5.5, 0.1, 2.0), 50)], cut=2.7)
    eye, tgt, fov = cam_from(a, u)
    if c.opt.get("push"):
        u2 = ease(c.lt / c.dur)
        eye, tgt, fov = lerp((5.5, 1.8, 9.5), (5.5, 1.9, 4.2), u2), (5.5, 1.9, 2.0), 50
    if knock:
        s = shake(c, 0.05, 3)
        eye = (eye[0] + s[0], eye[1] + s[1], eye[2])
    props = []
    if c.opt.get("feet"):
        x1 = 4.9 + 0.5 * math.sin(c.t * 0.7)
        for x in (x1, x1 + 0.75):
            props.append(("foot", [(0, 0.0, 2.03, 0.45, 0.09, 2.08, "black")], translate(x, 0, 0)))
    return S(set="service", eye=handheld(eye, c, 0.02), target=tgt, fov=fov, props=props, post=dict(grade=(1.0, 0.96, 0.92), flick=0.35))


def sh_radio(c):
    lvl = c.seg.get("radio", 1.0)
    puls = 0.6 + 0.4 * abs(math.sin(c.fi * 0.9))
    u = ease(c.gt / c.gdur)
    eye = lerp((5.2, 2.6, 8.6), (4.6, 2.35, 7.7), u)
    s = shake(c, 0.012 * lvl, 4)
    eye = (eye[0] + s[0], eye[1] + s[1], eye[2])
    return S(set="office", eye=eye, target=(3.4, 1.75, 5.4), fov=42,
             lights_extra=[((3.9, 2.0, 6.4), (1.6 * puls, 0.8 * puls, 0.2), 3.5)], post=dict(grade=(1.05, 0.98, 0.9), bloom=0.7))


def sh_phone_msg(c):
    img = phone_msg_img(c.lt > 0.35 or c.seg_index_in_group > 0)
    eye = handheld((6.5, 2.35, 7.6), c, 0.012)
    tgt = (6.5, 1.3, 5.4)
    dist = 0.75 - (0.22 * ease(c.lt / 1.5) if c.opt.get("zoom") else 0)
    dec = phone_decal(c, img, ("msg", c.lt > 0.35 or c.seg_index_in_group > 0), eye, tgt, dist=dist, drop=(-0.11 if c.opt.get("zoom") else -0.05))
    return S(set="office", eye=eye, target=tgt, fov=50, decals=[dec], decal_emit=1.0, post=dict(grade=(0.96, 0.98, 1.04)))


def mia_pose(c, tilt=0.0):
    pose = sit_pose((13.3, 0, 23.5), seat=3.5, size=0.78, legs=9)
    sway = 0.06 * math.sin(c.t * 1.4)
    pose.update(head=(0.05, 0, sway + tilt), arm_r=(-0.7, 0, 0.25), arm_l=(-0.7, 0, -0.25))
    return pose


def sh_escalator(c):
    pose = mia_pose(c)
    hp = head_pos("mia", pose)
    a, u, _ = angle(c, [((13.3, 1.7, 33.0), hp, (13.3, 2.0, 30.8), hp, 45),
                        ((18.0, 4.6, 26.5), hp, (17.0, 4.5, 25.8), hp, 40)], cut=3.0)
    eye, tgt, fov = cam_from(a, u)
    spot = torch_spot((13.6, 1.6, 31.5), hp, col=(2.8, 2.7, 2.4), angle=10)
    return S(set="atrium", eye=handheld(eye, c), target=tgt, fov=fov, chars=[("mia", pose, "closed" if CH.blink(c.t, 0.9) else "open", "0")],
             spot=spot, env=dict(light_scale=0.6), post=dict(grade=(0.92, 0.97, 1.1)))


def sh_mia(c):
    dark = c.opt.get("dark")
    tilt = 0.0
    if c.opt.get("tilt"):
        tilt = -0.35 * ease(c.gt / 1.4) if c.seg_index_in_group == 0 else -0.35
    pose = mia_pose(c, tilt)
    hp = head_pos("mia", pose)
    if dark:
        e, m = "black", "grin"
    else:
        e = "open" if (c.opt.get("freeze") or not CH.blink(c.t, 0.9)) else "closed"
        m = "0" if c.opt.get("freeze") else mouth_state(c, "mia")
    d = 2.3
    if c.opt.get("freeze"):
        d -= 0.45 * ease(c.lt / c.dur)
    if dark:
        d = 1.9 - 0.5 * ease(c.lt / 0.6)
    eye = (hp[0] + 0.3, hp[1] + 0.05, hp[2] + d)
    if dark:
        s = shake(c, 0.03, 3)
        eye = (eye[0] + s[0], eye[1] + s[1], eye[2])
    spot = torch_spot((hp[0] + 0.3, hp[1] - 0.5, hp[2] + 3.0), hp, col=(2.6, 2.5, 2.3) if not dark else (3.0, 1.2, 1.1), angle=16, rng=10)
    return S(set="atrium", eye=handheld(eye, c, 0.012), target=(hp[0], hp[1] - 0.12, hp[2]), fov=40, chars=[("mia", pose, e, m)], spot=spot,
             env=dict(light_scale=0.5 if not dark else 0.1), post=dict(grade=(0.95, 0.97, 1.08) if not dark else (1.15, 0.8, 0.8),
                                                                       flick=0.2 if not dark else 0.8))


def sh_jonas_close(c):
    dawn = c.opt.get("dawn")
    e = "closed" if CH.blink(c.t, 0.2) else ("open" if dawn else "wide")
    if dawn:
        pose = {"pos": (1.5, 0, 3.5), "yaw": 0.0}
        pose = CH.pose_idle(c.t, pose)
        hp = head_pos("jonas", pose)
        eye = (hp[0] + 0.45, hp[1] + 0.05, hp[2] + 2.6)
        return S(set="entrance_dawn", eye=handheld(eye, c, 0.012), target=(hp[0], hp[1] - 0.15, hp[2]), fov=40, chars=[("jonas", pose, e, mouth_state(c, "jonas"))],
                 post=dict(grade=(1.08, 1.0, 0.95)))
    pose = {"pos": (11.0, 0, 70.0), "yaw": 0.0, "arm_r": (-0.3, 0, 0.1)}
    pose = CH.pose_idle(c.t, pose)
    hp = head_pos("jonas", pose)
    eye = (hp[0] - 0.4, hp[1] + 0.02, hp[2] + 2.6 - 0.25 * ease(c.lt / c.dur))
    spot = torch_spot((hp[0] + 0.2, hp[1] - 0.6, hp[2] + 2.5), hp, col=(1.8, 1.8, 1.7), angle=22, rng=8)
    return S(set="corridor", eye=handheld(eye, c, 0.012), target=(hp[0], hp[1] - 0.15, hp[2]), fov=40, chars=[("jonas", pose, e, mouth_state(c, "jonas"))],
             spot=spot, env=dict(light_scale=0.6), post=dict(grade=(0.92, 0.97, 1.1)))


def sh_blackout(c):
    eye = handheld((11.0, 1.72, 82.0), c, 0.02)
    tgt = (11.0, 1.4, 60)
    if c.lt < 0.35:
        return S(set="corridor", eye=eye, target=tgt, fov=55)
    if c.lt < 2.6:
        a = max(0.0, 1 - (c.lt - 0.35) / 0.5)
        return S(set="corridor", eye=eye, target=tgt, fov=55, env=dict(light_scale=a, amb=max(0.05, a), emit=a), post=dict(flick=0.4 if a > 0 else 0))
    p = ease((c.lt - 2.6) / 1.4)
    aim = (8.0 + 6.0 * p, 0.8, 68)
    return S(set="corridor", eye=eye, target=tgt, fov=55, spot=torch_spot((11.3, 1.4, 81.5), aim), env=dict(light_scale=0.0, amb=0.05, emit=0.0),
             post=dict(flick=0.2))


def sh_escalator_empty(c):
    p = ease(c.lt / 1.6)
    aim = lerp((13.3, 3.8, 23.5), (13.0, 3.1, 24.5), p)
    u = ease(c.lt / c.dur)
    eye = lerp((13.4, 1.7, 33.0), (13.3, 2.4, 29.5), u)
    bunny = [(12.7, 3.0, 24.3, 13.2, 3.25, 24.9, "grey"), (12.5, 3.0, 24.3, 12.8, 3.4, 24.6, "grey"),
             (12.55, 3.4, 24.35, 12.62, 3.75, 24.42, "grey"), (12.68, 3.4, 24.35, 12.75, 3.72, 24.42, "grey")]
    return S(set="atrium", eye=handheld(eye, c), target=(13.1, 3.1, 24.5), fov=45, props=[("bunny", bunny, np.eye(4, dtype="f4"))],
             spot=torch_spot((13.6, 1.5, 32.0), aim, angle=12), env=dict(light_scale=0.04, amb=0.12, emit=0.2),
             post=dict(grade=(0.92, 0.97, 1.1), flick=0.25))


CAM_Z = 85.0


def creature_pose(c):
    d0 = c.opt.get("dist", 1.0)
    dark = False
    d = d0
    if c.opt.get("approach"):
        marks = [1.3, 2.6, 3.6, 4.4, 5.0, 5.5]
        k = sum(1 for m in marks if c.lt >= m)
        d = max(0.32, d0 - 0.1 * k)
        dark = any(m <= c.lt < m + 0.22 for m in marks)
    if c.opt.get("recede"):
        d = d0 + 0.7 * ease(c.lt / c.dur)
    if "choice" in c.seg:
        dark = (c.fi % 47) < 4
    return d, dark


def sh_creature(c):
    d, dark = creature_pose(c)
    cz = CAM_Z - (5 + 18 * d)
    tw = 0.06 * math.sin(c.fi * 1.7) if (c.fi // 9) % 3 == 0 else 0
    pose = {"pos": (11.0, 0, cz), "yaw": 0.0, "head": (0.05, 0, 0.55), "arm_r": (0.05 + tw, 0, 0.05), "arm_l": (0.05 - tw, 0, -0.05),
            "body": (0.06, 0, 0)}
    hp = head_pos("creature", pose)
    eye = handheld((11.2, 1.75, CAM_Z), c, 0.035)
    tgt = (11.0, 0.55 * hp[1] + 0.6, cz)
    spot = torch_spot((11.5, 1.45, CAM_Z - 0.6), (11.0, hp[1] * 0.6, cz), col=(5.0, 4.7, 4.2), angle=14, rng=60, on=not dark)
    return S(set="corridor", eye=eye, target=tgt, fov=48, chars=[("creature", pose)], spot=spot,
             env=dict(light_scale=0.0, amb=0.14 if not dark else 0.03, emit=0.15), post=dict(grade=(0.95, 0.95, 1.05), flick=0.3))


def sh_creature_close(c):
    tw = 0.09 * math.sin(c.fi * 2.1) if (c.fi // 7) % 2 else 0
    pose = {"pos": (11.0, 0, 70.0), "yaw": 0.0, "head": (0.05, 0, 0.55), "arm_r": (0.05 + tw, 0, 0.05), "arm_l": (0.05 - tw * 0.7, 0, -0.05)}
    hp = head_pos("creature", pose)
    u = ease(c.lt / c.dur)
    eye = (hp[0] + 0.25, hp[1] - 0.2, hp[2] + 3.2 - 0.6 * u)
    spot = torch_spot((hp[0] + 0.25, hp[1] - 0.9, hp[2] + 4.0), hp, angle=14, rng=12)
    return S(set="corridor", eye=handheld(eye, c, 0.02), target=hp, fov=42, chars=[("creature", pose)], spot=spot,
             env=dict(light_scale=0.0, amb=0.14, emit=0.15), post=dict(grade=(0.95, 0.95, 1.05)))


def knock_amount(c):
    k = 0.0
    for n_, o in c.seg.get("sfx", []):
        if n_ == "glass_knock" and 0 <= c.lt - o < 0.8:
            k = max(k, abs(math.sin((c.lt - o) * math.pi / 0.2)))
    return k


def walter_glass_pose(c, knock):
    return {"pos": (0.0, 0, -0.78), "yaw": 0.0, "arm_r": (-1.9 - 0.25 * knock, 0, -0.32), "arm_l": (-1.9 - 0.25 * knock, 0, 0.32),
            "head": (0.05, 0, 0.03 * math.sin(c.t * 2))}


def sh_cctv(c):
    k = knock_amount(c)
    pose = walter_glass_pose(c, k)
    return S(set="entrance", eye=(-9.5, 7.5, 9.5), target=(0, 1.2, -1), fov=58, chars=[("walter", pose, "open", "0")],
             cctv=True, rain_region=True)


def sh_glass_walter(c):
    o = c.opt
    k = knock_amount(c)
    pose = walter_glass_pose(c, k)
    if o.get("black"):
        e = "black"
    elif o.get("panic") or o.get("grin"):
        e = "open"
    else:
        e = "closed" if CH.blink(c.t, 0.6) else "open"
    if o.get("grin"):
        m = "grin" if (c.lt > c.dur * 0.35 or o.get("black")) else "0"
    else:
        m = mouth_state(c, "walter_door")
    hp = head_pos("walter", pose)
    if o.get("close"):
        u = ease(c.lt / 0.8)
        eye = lerp((hp[0] + 0.1, hp[1], 2.4), (hp[0] + 0.05, hp[1] - 0.02, 1.5), u)
        s = shake(c, 0.025, 3)
        eye = (eye[0] + s[0], eye[1] + s[1], eye[2])
        return S(set="entrance", eye=eye, target=hp, fov=40, chars=[("walter", pose, e, m)], rain_region=True,
                 post=dict(grade=(1.05, 0.85, 0.9), flick=0.6))
    a, u, _ = angle(c, [((0.5, 1.95, 3.4), hp, (0.4, 1.9, 3.0), hp, 46),
                        ((hp[0] - 0.4, hp[1] + 0.05, 2.4), hp, (hp[0] - 0.3, hp[1], 2.1), hp, 40)], cut=2.8)
    eye, tgt, fov = cam_from(a, u)
    if o.get("grin"):
        uu = ease(c.lt / c.dur)
        eye, fov = lerp((0.4, 1.9, 3.2), (0.15, hp[1], 1.6), uu), 42
    sh = (0.04 if o.get("shake") else 0) + 0.03 * k
    if sh:
        s = shake(c, sh, 3)
        eye = (eye[0] + s[0], eye[1] + s[1], eye[2])
    return S(set="entrance", eye=handheld(eye, c, 0.015), target=tgt, fov=fov, chars=[("walter", pose, e, m)], rain_region=True,
             post=dict(grade=(0.92, 0.96, 1.12), flick=0.15))


def sh_entrance(c):
    u = ease(c.lt / c.dur)
    return S(set="entrance", eye=handheld(lerp((0.3, 1.8, 6.5), (0.2, 1.7, 4.2), u), c), target=(0, 1.5, -10), fov=50, rain_region=True,
             post=dict(grade=(0.92, 0.96, 1.12)))


def sh_dawn(c):
    p = ease(c.lt / c.dur)
    wp = CH.pose_walk(c.t, 0.8, 0.45)
    wp.update(pos=(3.0 - 2.6 * p, 0, -12.0 + 10.5 * p), yaw=0.0)
    return S(set="entrance_dawn", eye=handheld((0.8, 1.8, 6.0 - 1.0 * p), c), target=(0.5, 1.5, -8), fov=48, chars=[("walter", wp)],
             post=dict(grade=(1.1, 1.0, 0.92), bloom=0.7))


def sh_walter_dawn(c):
    serious = c.opt.get("serious")
    e = "serious" if serious else ("closed" if CH.blink(c.t, 0.3) else "open")
    pose = CH.pose_idle(c.t, {"pos": (0.0, 0, 3.0), "yaw": 0.0, "head": (0.03, 0, 0)})
    hp = head_pos("walter", pose)
    d = 2.8 - (0.5 * ease(c.lt / c.dur) if serious else 0)
    eye = (hp[0] + 0.45, hp[1] + 0.05, hp[2] + d)
    return S(set="entrance_dawn", eye=handheld(eye, c, 0.012), target=(hp[0], hp[1] - 0.15, hp[2]), fov=40, chars=[("walter", pose, e, mouth_state(c, "walter"))],
             post=dict(grade=(1.08, 1.0, 0.93), bloom=0.5))


def sh_walter_end(c):
    p = ease(c.gt / c.gdur)
    wp = CH.pose_walk(c.t, 0.7, 0.4)
    wp.update(pos=(11.0, 0, 80.0 - 22 * p), yaw=math.pi)
    res = S(set="corridor_lit", eye=handheld((11.6, 2.1, 86.0), c), target=(11.0, 1.4, 55), fov=46, chars=[("walter", wp)],
            post=dict(grade=(1.0, 1.0, 1.05)))
    if c.opt.get("turn") and 1.0 <= c.lt < 1.35:
        pose = {"pos": (11.0, 0, 70.0), "yaw": 0.0}
        hp = head_pos("walter", pose)
        res = S(set="corridor", eye=(hp[0], hp[1], hp[2] + 1.7), target=hp, fov=40, chars=[("walter", pose, "black", "grin")],
                spot=torch_spot((hp[0], hp[1] - 0.4, hp[2] + 2), hp, col=(3.2, 1.4, 1.3), angle=20, rng=6),
                env=dict(light_scale=0.1, amb=0.2), post=dict(grade=(1.2, 0.8, 0.8)))
    return res


SHOTS = {k[3:]: v for k, v in list(globals().items()) if k.startswith("sh_")}


# =====================================================================
#  OVERLAYS
# =====================================================================
SPEAKERS = {"walter": ("WALTER", (255, 179, 71)), "walter_door": ("WALTER", (255, 179, 71)), "mama": ("MOM", (130, 205, 255)),
            "mama_door": ("???", (255, 95, 95)), "mia": ("MIA", (255, 160, 210)), "mia_dark": ("MIA", (255, 70, 70)),
            "creature": ("???", (255, 60, 60)), "jonas": ("JONAS", (255, 255, 255))}
YEL = (255, 228, 64)


def outlined(text, fnt, fill, stroke=10, sfill=(30, 20, 8), shadow=True):
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bb = tmp.textbbox((0, 0), text, font=fnt, stroke_width=stroke)
    w, h = bb[2] - bb[0] + 20, bb[3] - bb[1] + 20
    im = Image.new("RGBA", (w, h), 0)
    d = ImageDraw.Draw(im)
    if shadow:
        d.text((10 - bb[0] + 4, 10 - bb[1] + 6), text, font=fnt, fill=(0, 0, 0, 140), stroke_width=stroke, stroke_fill=(0, 0, 0, 140))
    d.text((10 - bb[0], 10 - bb[1]), text, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return im


@lru_cache(2048)
def word_img(word, col, scale_q):
    size = int(118 * (1 + scale_q * 0.04))
    return outlined(word, font(LILITA, size), col)


def clean_word(w):
    return w.strip(".,!?:;…\"“”").replace("...", "")


@lru_cache(16)
def tag_img(label, col):
    f = font(LILITA, 46)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw = tmp.textlength(label, font=f)
    im = Image.new("RGBA", (int(tw) + 56, 70), 0)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.size[0] - 1, 69], 34, fill=(0, 0, 0, 170), outline=col + (255,), width=4)
    d.text((28, 9), label, font=f, fill=col + (255,))
    return im


@lru_cache(64)
def choice_card(a, b, hint):
    im = Image.new("RGBA", (W, H), 0)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, H], fill=(0, 0, 0, 120))
    q = outlined("WHAT SHOULD I DO?", font(LILITA, 92), (255, 255, 255))
    im.paste(q, ((W - q.size[0]) // 2, 330), q)
    for k, (lab, txt, col) in enumerate((("A", a, (230, 50, 60)), ("B", b, (60, 140, 240)))):
        y0 = 500 + k * 300
        d.rounded_rectangle([60, y0, W - 60, y0 + 250], 40, fill=(10, 10, 14, 225), outline=col + (255,), width=8)
        d.ellipse([95, y0 + 55, 235, y0 + 195], fill=col + (255,))
        lt = outlined(lab, font(LILITA, 100), (255, 255, 255), 0, shadow=False)
        im.paste(lt, (165 - lt.size[0] // 2, y0 + 125 - lt.size[1] // 2 - 2), lt)
        f = font(LILITA, 60)
        words, lines, cur = txt.split(), [], ""
        for w_ in words:
            t = (cur + " " + w_).strip()
            if d.textlength(t, font=f) < W - 60 - 300:
                cur = t
            else:
                lines.append(cur)
                cur = w_
        lines.append(cur)
        ly = y0 + 125 - (len(lines) * 72) // 2
        for ln in lines:
            d.text((275, ly), ln, font=f, fill=(255, 255, 255, 255))
            ly += 72
    if hint:
        ht = outlined(hint, font(LILITA, 54), YEL, 6)
        im.paste(ht, ((W - ht.size[0]) // 2, 1100), ht)
    return im


@lru_cache(32)
def countdown_img(num, frac):
    im = Image.new("RGBA", (260, 260), 0)
    d = ImageDraw.Draw(im)
    d.ellipse([10, 10, 250, 250], fill=(0, 0, 0, 180), outline=(80, 80, 80, 255), width=10)
    d.arc([10, 10, 250, 250], -90, -90 + 360 * frac / 20, fill=(255, 60, 60, 255), width=12)
    t = outlined(str(num), font(LILITA, 140), (255, 255, 255), 0, shadow=False)
    im.paste(t, (130 - t.size[0] // 2, 130 - t.size[1] // 2 - 6), t)
    return im


@lru_cache(8)
def title_img(n, name):
    im = Image.new("RGBA", (W, 600), 0)
    l1 = outlined("THE NIGHT", font(LILITA, 112), (255, 255, 255))
    l2 = outlined("WATCHMAN'S RULES", font(LILITA, 104), (255, 70, 70))
    im.paste(l1, ((W - l1.size[0]) // 2, 10), l1)
    im.paste(l2, ((W - l2.size[0]) // 2, 135), l2)
    d = ImageDraw.Draw(im)
    label = f"PART {n}" + (" · FINALE" if n == 5 else "")
    f = font(LILITA, 64)
    tw = d.textlength(label, font=f)
    d.rounded_rectangle([(W - tw) / 2 - 36, 290, (W + tw) / 2 + 36, 380], 45, fill=(255, 228, 64, 250))
    d.text(((W - tw) / 2, 298), label, font=f, fill=(30, 20, 8, 255))
    sub = outlined(name, font(LILITA, 64), (255, 255, 255), 8)
    im.paste(sub, ((W - sub.size[0]) // 2, 400), sub)
    return im


def ampm(hhmm):
    h, m = map(int, hhmm.split(":"))
    suf = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {suf}"


@lru_cache(32)
def time_img(clock, colon):
    txt = ampm(clock)
    if not colon:
        txt = txt.replace(":", " ")
    f = font(LILITA, 86)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw = tmp.textlength("12:00 AM", font=f)
    im = Image.new("RGBA", (int(tw) + 130, 130), 0)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.size[0] - 1, 129], 30, fill=(0, 0, 0, 175))
    d.ellipse([30, 50, 58, 78], fill=(230, 30, 30, 255))
    d.text((80, 14), txt, font=f, fill=(255, 255, 255, 255))
    return im


@lru_cache(4)
def end_badge(n, final):
    txt = "THE END... OR IS IT?" if final else f"PART {n + 1} COMING ↓"
    f = font(LILITA, 76) if final else font(LILITA, 76)
    if not final:
        im = outlined(f"PART {n + 1} COMING", f, YEL)
        return im
    return outlined(txt, f, YEL)


@lru_cache(None)
def rain_layer():
    lay = Image.new("RGBA", (W, H * 2), 0)
    d = ImageDraw.Draw(lay)
    r = np.random.default_rng(9)
    for _ in range(1000):
        x, y = r.uniform(0, W), r.uniform(0, H * 2)
        l = r.uniform(40, 110)
        d.line([(x, y), (x - l * 0.12, y + l)], fill=(190, 210, 240, int(r.uniform(30, 80))), width=2)
    return lay


@lru_cache(None)
def cctv_overlay():
    im = Image.new("RGBA", (W, H), 0)
    d = ImageDraw.Draw(im)
    for y in range(0, H, 4):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, 60))
    d.rectangle([40, 120, W - 40, H - 380], outline=(220, 255, 220, 140), width=3)
    return im


# =====================================================================
#  RENDER
# =====================================================================
class Film:
    def __init__(self, msaa=4):
        self.st = stg.Stage(W, H, msaa=msaa)
        self.dyn = {}

    def frame_dict(self, res):
        st = self.st
        name = res["set"]
        s = st.get_set(name)
        env = dict(s.env)
        em = res.get("env", {})
        scale_l = em.get("light_scale", 1.0)
        if "amb" in em:
            a = em["amb"]
            env["amb_sky"] = tuple(v * a for v in env["amb_sky"])
            env["amb_ground"] = tuple(v * a for v in env["amb_ground"])
        if "emit" in em:
            env["emit_gain"] = env.get("emit_gain", 1.0) * em["emit"]
        lights = [(p, tuple(v * scale_l for v in col), r) for (p, col, r) in s.lights] + list(res.get("lights_extra", []))
        draws = st.set_draws(name)
        for ch in res.get("chars", []):
            nm, pose = ch[0], ch[1]
            eyes = ch[2] if len(ch) > 2 else ("closed" if CH.blink(self.c.t, hash(nm) % 7 / 7) else "open")
            mouth = ch[3] if len(ch) > 3 else "0"
            tint = ch[4] if len(ch) > 4 else (1, 1, 1)
            draws += st.char_draws(nm, pose, eyes, mouth, tint=tint)
        for key, boxes, M in res.get("props", []):
            k = st.prop(key, boxes)
            draws.append((k, "atlas", M, {}))
        for key, img, corners, tkey in res.get("decals", []):
            dk = f"dyn:{key}"
            m = Mesh()
            m.add_quad(corners, (0, 0, 1), [(0, 1), (1, 1), (1, 0), (0, 0)], (1, 1, 1, 1), res.get("decal_emit", 0.6))
            arr = m.array()
            old = st.r.vaos.get(dk)
            if old:
                old[2].write(arr.tobytes())
            else:
                st.r.vao(dk, arr)
            if self.dyn.get(dk) != tkey:
                st.r.update_texture(dk, img)
                self.dyn[dk] = tkey
            draws.append((dk, dk, np.eye(4, dtype="f4"), {"transparent": True}))
        f = dict(eye=res["eye"], target=res["target"], fov=res.get("fov", 50), env=env, lights=lights, draws=draws, spot=res.get("spot"))
        return f

    def compose(self, part, segs, si, fi, total, caps=None):
        n = part["n"]
        t = fi / FPS
        s = segs[si]
        c = C()
        c.fi, c.t, c.seg, c.opt = fi, t, s, s["opt"]
        c.lt, c.dur = t - s["start"], s["dur"]
        c.gt, c.gdur = t - s["g0"], s["gend"] - s["g0"]
        c.seg_index_in_group = s["gi"]
        c.env = s["env"]
        c.prev_shot = segs[si - 1]["shot"] if si > 0 else None
        c.prev_opt = segs[si - 1]["opt"] if si > 0 else None
        self.c = c
        res = SHOTS[s["shot"]](c)
        # Neon-Flackern außen
        if res.get("neon_off"):
            res.setdefault("env", {})["emit"] = 0.55
        frame = self.st.render(self.frame_dict(res))
        pp = res.get("post", {})
        rr = np.random.default_rng(fi * 7919 + n)
        flick = pp.get("flick", 0.1)
        dark = 1.0
        if rr.random() < 0.05 + 0.3 * flick:
            dark -= rr.uniform(0.04, 0.12 + 0.45 * flick)
        flash = pp.get("flash", 0.0)
        for name, o in s.get("sfx", []):
            if name == "sting" and 0 <= c.lt - o < 0.1:
                flash = max(flash, 0.7)
        arr = post.finish(frame, fi, grade=pp.get("grade", (1, 1, 1)), bloom_s=pp.get("bloom", 0.5), flash=flash, dark=dark)
        if res.get("cctv"):
            g = arr.astype(np.float32).mean(axis=2, keepdims=True)
            arr = np.clip(g * np.array([0.78, 1.0, 0.82]) * 1.15 + rr.normal(0, 12, (H // 4, W // 4)).repeat(4, 0).repeat(4, 1)[..., None], 0, 255).astype(np.uint8)
        if s["new_shot"] and si > 0 and c.lt < 0.08:
            arr = (arr * (0.35 + 0.65 * c.lt / 0.08)).astype(np.uint8)
        if t < 0.3:
            arr = (arr * (t / 0.3)).astype(np.uint8)
        if t > total - 0.6:
            arr = (arr * max(0.0, (total - t) / 0.6)).astype(np.uint8)
        img = Image.fromarray(arr)
        # Regen
        if res.get("rain") or res.get("rain_region"):
            rl = rain_layer()
            off = (fi * 61) % H
            layer = rl.crop((0, off, W, off + H))
            if res.get("rain_region"):
                a = np.asarray(layer.getchannel("A")).astype(np.float32) * 0.6
                layer.putalpha(Image.fromarray(a.astype(np.uint8)))
            img.paste(layer, (0, 0), layer)
        self.overlays(img, part, s, c, fi, res)
        return img

    def overlays(self, img, part, s, c, fi, res):
        n = part["n"]
        if res.get("cctv"):
            ov = cctv_overlay()
            img.paste(ov, (0, 0), ov)
            d = ImageDraw.Draw(img)
            if (fi // 15) % 2 == 0:
                d.ellipse([70, 150, 100, 180], fill=(240, 30, 30))
            d.text((115, 144), "REC  CAM 03  MAIN ENTRANCE", font=font(MONO, 32), fill=(230, 255, 230))
            d.text((W - 250, 144), f"05:41:{int(c.lt) + 10:02d}", font=font(MONO, 32), fill=(230, 255, 230))
        if "time" in s and c.lt < 2.3 and s["shot"] != "cctv":
            ti = time_img(s["time"], (fi // 15) % 2 == 0)
            img.paste(ti, ((W - ti.size[0]) // 2, 190), ti)
        if s.get("title") and c.lt < 3.3:
            ti = title_img(n, part["name"])
            a = min(1, c.lt / 0.25) * min(1, (3.3 - c.lt) / 0.45)
            if a < 1:
                ti = ti.copy()
                ti.putalpha(ti.getchannel("A").point(lambda v: int(v * a)))
            img.paste(ti, (0, 340), ti)
        if "choice" in s:
            card = choice_card(s["choice"][0], s["choice"][1], s.get("hint"))
            a_in = min(1, c.lt / 0.3)
            if a_in < 1:
                card = card.copy()
                card.putalpha(card.getchannel("A").point(lambda v: int(v * a_in)))
            img.paste(card, (0, 0), card)
            if c.lt >= s["cd_start"]:
                el = c.lt - s["cd_start"]
                cd = countdown_img(max(1, COUNTDOWN - int(el)), int(min(1, el / COUNTDOWN) * 20))
                img.paste(cd, ((W - 260) // 2, 1240), cd)
            return
        # Einzelwort-Untertitel
        ws = s["words"]
        cur = None
        for i, w in enumerate(ws):
            nxt = ws[i + 1]["start"] if i + 1 < len(ws) else w["end"] + 0.4
            if w["start"] <= c.lt < min(nxt, w["end"] + 0.45):
                cur = (i, w)
                break
        ycap = 1320 if s["shot"] != "card" else 1600
        who = s["who"]
        dialog = who != "jonas" or bool(s.get("talk"))
        if cur:
            i, w = cur
            txt = clean_word(w["text"])
            if txt:
                age = c.lt - w["start"]
                sq = max(0, 4 - int(age / 0.025))
                col = YEL if not dialog else (255, 255, 255)
                wi = word_img(txt, col, sq)
                img.paste(wi, ((W - wi.size[0]) // 2, ycap - wi.size[1] // 2), wi)
        if dialog and ws and ws[0]["start"] - 0.1 <= c.lt <= ws[-1]["end"] + 0.3:
            label, col = SPEAKERS[who]
            tg = tag_img(label, col)
            img.paste(tg, ((W - tg.size[0]) // 2, ycap - 150), tg)
        if s.get("end") and (int(c.lt * 2) % 2 == 0 or c.lt > s["tts_start"] + s["tts_dur"]):
            eb = end_badge(n, bool(s.get("final")))
            img.paste(eb, ((W - eb.size[0]) // 2, 1480), eb)


RAIN_SHOTS = {"exterior": 1.0, "leave": 0.6, "glass_walter": 0.8, "entrance": 0.8, "cctv": 0.5}


def smooth(x, sec):
    k = max(1, int(sec * SR))
    cs = np.concatenate([[0], np.cumsum(x)])
    i1 = np.clip(np.arange(len(x)) + k // 2, 0, len(x))
    i0 = np.clip(np.arange(len(x)) - k // 2, 0, len(x))
    return (cs[i1] - cs[i0]) / np.maximum(1, i1 - i0)


def mix_audio(segs, total, n):
    L = int((total + 4) * SR)
    mix = np.zeros(L)
    sp = np.zeros(L)
    ten, rad, rain = np.zeros(L), np.zeros(L), np.zeros(L)

    def put(buf, x, at, g=1.0):
        a = int(at * SR)
        if a >= L or a < 0:
            return
        e = min(L, a + len(x))
        buf[a:e] += x[:e - a] * g

    for s in segs:
        a, b = int(s["start"] * SR), int((s["start"] + s["dur"]) * SR)
        ten[a:b] = s.get("tense", 0.3)
        rad[a:b] = s.get("radio", 0.06)
        rain[a:b] = RAIN_SHOTS.get(s["shot"], 0.0)
        put(sp, s["audio"], s["start"] + s["tts_start"])
        for name, o in s.get("sfx", []):
            put(mix, sound.sfx(name), s["start"] + o, sound.SFX_GAIN.get(name, 0.6))
        if s["new_shot"] and s["start"] > 0:
            put(mix, sound.sfx("whoosh"), s["start"] - 0.25, 0.5)
        if "choice" in s:
            for k in range(COUNTDOWN):
                put(mix, sound.sfx("tick"), s["start"] + s["cd_start"] + k, 0.8)
        if s.get("final"):
            put(mix, sound.sfx("sting"), s["start"] + s["dur"] - 0.4, 0.5)
        if s.get("opt", {}).get("turn"):
            put(mix, sound.sfx("sting"), s["start"] + 1.0, 0.7)
    ten, rad, rain = smooth(ten, 1.2), smooth(rad, 0.4), smooth(rain, 0.5)
    duck = 1 - 0.6 * np.clip(smooth(np.abs(sp), 0.3) * 6, 0, 1)
    mix += sound.music(L, ten, n) * duck
    mix += sound.ambience(L, n)
    mix += sound.static(L, n) * rad * (0.6 + 0.4 * duck)
    mix += sound.rain(L, n) * rain * 0.5
    mix += sp
    act = np.abs(sp) > 0.01
    peak = np.percentile(np.abs(sp[act]), 99.5) if act.any() else 0.8
    mix = sound.soft_limit(mix, peak * 1.25)
    end = int((total + 0.15) * SR)
    fade = int(0.8 * SR)
    mix[end - fade:end] *= np.linspace(1, 0, fade)
    return mix[:end]


def render_part(part, preview=None, msaa=4):
    n = part["n"]
    segs, total = build_timeline(part)
    print(f"Part {n}: {total:.1f}s, {len(segs)} segments", flush=True)
    film = Film(msaa=msaa)
    if preview is not None:
        out = []
        for ts in preview:
            fi = int(ts * FPS)
            si = max(i for i, s in enumerate(segs) if s["start"] <= ts)
            out.append(film.compose(part, segs, si, fi, total))
        return out, segs
    wav = os.path.join(BUILD, f"part{n}.wav")
    write_wav(wav, mix_audio(segs, total, n))
    out = os.path.join(OUT, f"night_watchman_part{n}.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                           "-maxrate", "4500k", "-bufsize", "9000k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                           "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    nf = int(total * FPS)
    si = 0
    import time
    t0 = time.time()
    for fi in range(nf):
        t = fi / FPS
        while si < len(segs) - 1 and t >= segs[si]["start"] + segs[si]["dur"]:
            si += 1
        img = film.compose(part, segs, si, fi, total)
        ff.stdin.write(img.tobytes())
        if fi % 150 == 0:
            el = time.time() - t0
            print(f"  Part {n}: frame {fi}/{nf}  ({el / max(1, fi):.2f}s/frame)", flush=True)
    ff.stdin.close()
    ff.wait()
    print("done:", out, flush=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--preview":
        n = int(args[1])
        part = [p for p in story.PARTS if p["n"] == n][0]
        segs, total = build_timeline(part)
        ts = [s["start"] + min(s["dur"] * 0.55, s["dur"] - 0.2) for s in segs]
        frames, _ = render_part(part, preview=ts, msaa=2)
        cols, tw, th = 6, 270, 480
        rows = (len(frames) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows * th))
        for i, f in enumerate(frames):
            sheet.paste(f.resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
        sheet.save(args[2])
        print("total", round(total, 1))
        sys.exit(0)
    which = [int(a) for a in args if a.isdigit()] or [p["n"] for p in story.PARTS]
    for p in story.PARTS:
        if p["n"] in which:
            render_part(p)
