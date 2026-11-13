# -*- coding: utf-8 -*-
"""Die Regeln des Nachtwächters – Renderer v2 (TikTok 1080x1920, 30 fps).

Figuren (SVG via Chromium), Stimmen (Piper), Sounddesign (numpy), Animation (PIL/numpy).
Aufruf:  python3 render.py [teil ...]
"""
import os, sys, math, subprocess, wave
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import story, voices, scenes, art, sound
from scenes import font, F_CAP, F_BOLD, F_MONO, wrap, BW, BH

W, H, FPS, SR = 1080, 1920, 30, 44100
ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)


# =====================================================================
#  ASSETS
# =====================================================================
@lru_cache(None)
def png(name):
    return Image.open(os.path.join(art.ART, name + ".png")).convert("RGBA")


@lru_cache(160)
def sprite(name, scale=1.0, rot=0.0):
    im = png(name)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if scale != 1.0:
        im = im.resize((max(1, int(im.size[0] * scale)), max(1, int(im.size[1] * scale))), Image.BILINEAR)
    return im


def darken(im, f):
    return Image.eval(im, lambda v: int(v * f))


_BG = {}


@lru_cache(None)
def bg(name):
    if name == "corridor":
        return scenes.corridor()
    if name == "corridor_dark":
        return darken(bg("corridor"), 0.6)
    if name == "corridor_dark_blur":
        return darken(bg("corridor").filter(ImageFilter.GaussianBlur(16)), 0.45)
    if name == "office_back":
        return scenes.office(with_desk=False)
    if name == "office_full":
        return scenes.office(with_desk=True)
    if name == "office_front":
        f = bg("office_full").convert("RGBA")
        f.putalpha(scenes.office_front_mask())
        return f
    if name == "office_blur":
        return darken(bg("office_full").filter(ImageFilter.GaussianBlur(14)), 0.5)
    if name == "door":
        return scenes.door("3")
    if name in ("ent_back", "ent_front", "ent_refl"):
        if "ent_back" not in _BG:
            b, f, r = scenes.entrance(False)
            _BG.update(ent_back=b, ent_front=f, ent_refl=r)
        return _BG[name]
    if name in ("dawn_back", "dawn_front", "dawn_refl"):
        if "dawn_back" not in _BG:
            b, f, r = scenes.entrance(True)
            _BG.update(dawn_back=b, dawn_front=f, dawn_refl=r)
        return _BG[name]
    if name == "dawn_blur":
        im = bg("dawn_back").copy()
        im.paste(bg("dawn_front"), (0, 0), bg("dawn_front"))
        return im.filter(ImageFilter.GaussianBlur(18))
    if name in ("exterior_on", "exterior_off", "escalator"):
        return png(name).convert("RGB")
    if name == "escalator_blur":
        return darken(bg("escalator").filter(ImageFilter.GaussianBlur(16)), 0.6)
    if name == "drops":
        return make_drops()
    raise ValueError(name)


def make_drops():
    lay = Image.new("RGBA", (BW, BH), 0)
    d = ImageDraw.Draw(lay)
    r = np.random.default_rng(4)
    x0, y0, x1, y1 = scenes.GLASS
    for _ in range(420):
        x, y = r.uniform(x0, x1), r.uniform(y0, y1)
        s = r.uniform(3, 9)
        d.ellipse([x - s * 0.7, y - s, x + s * 0.7, y + s], fill=(200, 220, 255, 70))
        d.ellipse([x - s * 0.3, y - s * 0.6, x, y - s * 0.2], fill=(255, 255, 255, 110))
        if r.random() < 0.15:
            l = r.uniform(30, 140)
            d.line([(x, y), (x + r.uniform(-4, 4), y + l)], fill=(200, 220, 255, 50), width=3)
    return lay


@lru_cache(None)
def rain_layer():
    lay = Image.new("RGBA", (W, H * 2), 0)
    d = ImageDraw.Draw(lay)
    r = np.random.default_rng(9)
    for _ in range(900):
        x, y = r.uniform(0, W), r.uniform(0, H * 2)
        l = r.uniform(40, 110)
        a = int(r.uniform(30, 80))
        d.line([(x, y), (x - l * 0.12, y + l)], fill=(190, 210, 240, a), width=2)
    return lay


@lru_cache(64)
def card_img(reveal, hl):
    return scenes.rule_card(reveal, hl, story.RULES)


@lru_cache(64)
def phone_call_img(active, secs, pulse):
    return scenes.phone_call(active, secs, pulse / 10)


@lru_cache(4)
def phone_msg_img(show_last):
    return scenes.phone_msg(show_last)


def place(world, sp, cx, bottom):
    world.paste(sp, (int(cx - sp.size[0] / 2), int(bottom - sp.size[1])), sp)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def blink(t, s=0.0):
    return ((t + s * 1.7) % 3.9) < 0.13


@lru_cache(8)
def hands_layer(knock_q=0):
    """Zwei Handflächen, die von außen gegen die Glastür drücken."""
    knock = knock_q / 4
    lay = Image.new("RGBA", (BW, BH), 0)
    d = ImageDraw.Draw(lay)
    for cx, sgn in ((300, 1), (890, -1)):
        cy = 1180 - knock * 14
        s = 1.0 + knock * 0.05
        col = (196, 160, 140, 235)
        d.ellipse([cx - 62 * s, cy - 40 * s, cx + 62 * s, cy + 75 * s], fill=col)
        for k in range(4):
            fx = cx - 48 * s + k * 32 * s
            d.rounded_rectangle([fx - 12 * s, cy - 150 * s + abs(k - 1.5) * 18, fx + 12 * s, cy - 20 * s], 12, fill=col)
        d.rounded_rectangle([min(cx + sgn * 50 * s - 14, cx + sgn * 110 * s), cy - 40,
                             max(cx + sgn * 50 * s - 14, cx + sgn * 110 * s), cy + 2], 14, fill=col)
        d.ellipse([cx - 40, cy - 10, cx + 40, cy + 50], fill=(230, 200, 185, 120))
    return lay.filter(ImageFilter.GaussianBlur(1.5))


# =====================================================================
#  SHOTS  (liefern Welt-Bild + Kamera + Licht)
# =====================================================================
class C:
    pass


def mouth(c, who):
    if c.seg.get("talk") and c.seg["who"] == who and c.env is not None:
        k = int((c.lt - c.seg["tts_start"]) * FPS)
        if 0 <= k < len(c.env):
            v = c.env[k]
            return "0" if v < 0.12 else ("1" if v < 0.42 else "2")
    return "0"


def sh_hook(c):
    w = bg("corridor_dark_blur").copy()
    place(w, sprite("mia_black_grin", 1.55), 594, BH + 20)
    z = 1.0 + 0.3 * ease(c.lt / c.dur)
    return dict(img=w, zoom=z, cx=594, cy=1150, light=dict(amb=0.08, beams=[(594, 1250, 560, 1.0)]),
                flick=0.7, shake=3, grade=(1.0, 0.86, 0.86))


def sh_exterior(c):
    off = (c.fi // 2) % 37 in (0, 3) or ((c.fi // 2) % 53 in (5, 6))
    w = bg("exterior_off" if off else "exterior_on")
    p = c.gt / c.gdur
    if c.opt.get("push"):
        z, cy = 1.0 + 0.06 + 0.5 * ease(c.lt / c.dur), 1056 - 180 * ease(c.lt / c.dur)
    else:
        z, cy = 1.0 + 0.06 * p, 1056
    flash = 0.0
    for name, o in c.seg.get("sfx", []):
        if name == "thunder" and c.lt >= o:
            dt = c.lt - o
            flash = math.exp(-dt / 0.12) + (0.6 * math.exp(-(dt - 0.25) / 0.1) if dt > 0.25 else 0)
    return dict(img=w, zoom=z, cx=594, cy=cy, rain=True, flash=flash * 0.8, grade=(0.9, 0.95, 1.1))


def sh_walter(c):
    w = bg("office_back").copy()
    e = "closed" if blink(c.t) else ("serious" if c.opt.get("serious") else "open")
    m = mouth(c, "walter")
    bob = 3 * math.sin(c.t * 1.7)
    place(w, sprite(f"walter_{e}_{m}", 1.25), 594, 1790 + bob)
    w.paste(bg("office_front"), (0, 0), bg("office_front"))
    if c.opt.get("close"):
        z = 1.45 + 0.12 * ease(c.lt / c.dur)
        return dict(img=w, zoom=z, cx=594, cy=1060, grade=(1.05, 0.97, 0.88))
    return dict(img=w, zoom=1.0 + 0.1 * c.gt / c.gdur, cx=594, cy=1100, grade=(1.05, 0.97, 0.88))


def sh_card(c):
    w = bg("office_blur").copy()
    rv, hl = c.opt.get("reveal", 4), c.opt.get("hl")
    card = card_img(rv, hl)
    prev = c.prev_opt if c.prev_shot == "card" else None
    if rv > 0 and prev is not None and (prev.get("reveal"), prev.get("hl")) != (rv, hl) and c.lt < 0.5:
        old = card_img(prev.get("reveal", 4), prev.get("hl"))
        card = Image.blend(old, card, ease(c.lt / 0.5))
    y = 150
    if rv == 0:
        y += int(900 * (1 - ease(c.lt / 0.7)))
    w.paste(card, (int(594 - card.size[0] / 2), y), card)
    return dict(img=w, zoom=1.0 + 0.04 * c.gt / c.gdur, cx=594, cy=1000, grade=(1.05, 1.0, 0.9))


def sh_leave(c):
    w = bg("ent_back").copy()
    p = ease(c.lt / c.dur)
    s = round(0.85 - 0.45 * p, 2)
    place(w, sprite("walter_back", s), 594 + 60 * p, 1690 - 300 * p)
    w.paste(bg("drops"), (0, 0), bg("drops"))
    w.paste(bg("ent_refl"), (0, 0), bg("ent_refl"))
    w.paste(bg("ent_front"), (0, 0), bg("ent_front"))
    return dict(img=w, zoom=1.0 + 0.05 * p, cx=594, cy=1080, rain_region=scenes.GLASS, grade=(0.9, 0.95, 1.1))


def sh_corridor_jonas(c):
    w = bg("corridor").copy()
    bob = 12 * abs(math.sin(c.t * 3.1))
    sp = sprite("jonas_back", 1.05)
    w.paste(sp, (-70, int(BH - sp.size[1] + 40 + bob)), sp)
    bx = 594 + 50 * math.sin(c.t * 0.8)
    return dict(img=w, zoom=1.0 + 0.06 * c.gt / c.gdur, cx=594, cy=1056 + bob * 0.3,
                light=dict(amb=0.42, beams=[(bx, 940, 470, 1.0), (760, 1250, 320, 0.6)]), flick=0.15, grade=(0.9, 0.97, 1.1))


def sh_phone_call(c):
    w = bg("corridor_dark_blur").copy()
    active = bool(c.opt.get("active"))
    pulse = int(((c.lt * 1.3) % 1.0) * 10) if not active else 0
    ph = phone_call_img(active, 7 + int(c.lt) if active else 0, pulse)
    dx = 0
    for name, o in c.seg.get("sfx", []):
        if name == "buzz" and 0 <= c.lt - o < 1.0 and ((c.lt - o) % 0.6) < 0.4:
            dx = 7 * math.sin(c.fi * 2.3)
    w.paste(ph, (int(594 - ph.size[0] / 2 + dx), 440), ph)
    return dict(img=w, zoom=1.0 + 0.05 * c.gt / c.gdur, cx=594, cy=1100)


def sh_watcher(c):
    w = bg("corridor").copy()
    appear = ease((c.lt - 0.8) / 1.4)
    tilt = 14 * ease((c.lt - 2.4) / 1.2)
    sp = sprite("creature_sil", 0.21, round(tilt))
    x = 700 - 90 * appear
    if c.lt > 0.6:
        place(w, sp, x, scenes.corridor_floor_y(11) + 4)
    z = 1.0 + 0.45 * ease(c.lt / c.dur)
    return dict(img=w, zoom=z, cx=600, cy=950, light=dict(amb=0.5, beams=[(x, 930, 260, 1.0)]), flick=0.3, grade=(0.9, 0.95, 1.1))


def sh_jonas_office(c):
    w = bg("office_back").copy()
    e = "wide" if c.opt.get("scared") else ("closed" if blink(c.t, 0.4) else "open")
    place(w, sprite(f"jonas_{e}_{mouth(c, 'jonas')}", 1.25), 594, 1790 + 2 * math.sin(c.t * 2))
    w.paste(bg("office_front"), (0, 0), bg("office_front"))
    lvl = c.seg.get("radio", 0.3)
    return dict(img=w, zoom=1.0 + 0.1 * c.gt / c.gdur, cx=594, cy=1100, grade=(0.95, 1.02, 1.0), flick=0.15,
                light=dict(amb=0.85, beams=[(470, 1240, 300, 0.4 * lvl * (0.6 + 0.4 * abs(math.sin(c.fi * 0.7))))]))


def sh_door3(c):
    w = bg("door").copy()
    if c.opt.get("feet"):
        d = ImageDraw.Draw(w)
        x1 = 500 + 60 * math.sin(c.t * 0.7)
        for x in (x1, x1 + 120):
            d.ellipse([x - 45, scenes.DOOR_GAP_Y - 8, x + 45, scenes.DOOR_GAP_Y + 6], fill=(8, 5, 3))
    shake = 0
    for name, o in c.seg.get("sfx", []):
        if name == "knock" and 0 <= c.lt - o < 0.75:
            shake = 7
    if c.opt.get("push"):
        z, cy = 1.0 + 0.4 * ease(c.lt / c.dur), 1150
    else:
        z, cy = 1.0 + 0.08 * c.gt / c.gdur, 1100
    return dict(img=w, zoom=z, cx=594, cy=cy, shake=shake, flick=0.35, grade=(1.0, 0.97, 0.95))


def sh_radio(c):
    w = bg("office_full")
    lvl = c.seg.get("radio", 1.0)
    puls = 0.6 + 0.4 * abs(math.sin(c.fi * 0.9))
    z = 2.3 + 0.25 * c.gt / c.gdur
    return dict(img=w, zoom=z, cx=330, cy=1340, shake=2.5 * lvl, grade=(1.05, 0.98, 0.9),
                light=dict(amb=0.75, beams=[(470, 1240, 220, 0.6 * puls)]))


def sh_phone_msg(c):
    w = bg("office_blur").copy()
    ph, ylast = phone_msg_img(c.lt > 0.35 or c.seg_index_in_group > 0)
    w.paste(ph, (int(594 - ph.size[0] / 2), 330), ph)
    if c.opt.get("zoom"):
        z = 1.0 + 0.7 * ease(c.lt / 1.5)
        return dict(img=w, zoom=z, cx=594, cy=330 + ylast - 60, grade=(0.95, 0.98, 1.05))
    return dict(img=w, zoom=1.0 + 0.04 * c.lt / c.dur, cx=594, cy=1050)


def sh_escalator(c):
    w = bg("escalator").copy()
    sway = 3 * math.sin(c.t * 1.4)
    place(w, sprite("mia_sitting", 0.8, round(sway)), 712, 1300)
    z = 1.15 + 0.35 * ease(c.lt / c.dur)
    return dict(img=w, zoom=z, cx=700, cy=1120, light=dict(amb=0.35, beams=[(712, 1060, 360, 1.0)]), flick=0.2, grade=(0.92, 0.97, 1.1))


def sh_mia(c):
    w = bg("escalator_blur").copy()
    dark = c.opt.get("dark")
    if dark:
        e, m = "black", "grin"
    else:
        e = "open" if (c.opt.get("freeze") or not blink(c.t, 0.9)) else "closed"
        m = "0" if c.opt.get("freeze") else mouth(c, "mia")
    tilt = 0
    if c.opt.get("tilt"):
        tilt = -int(12 * ease(c.gt / 1.4)) if c.seg_index_in_group == 0 else -12
    sp = sprite(f"mia_{e}_{m}", 1.62, tilt)
    place(w, sp, 594, BH + 60 + (abs(tilt) * 4))
    if dark:
        z = 1.15 + 0.35 * ease(c.lt / 0.6)
        return dict(img=w, zoom=z, cx=594, cy=1150, shake=6, flick=0.9, grade=(1.15, 0.75, 0.75),
                    light=dict(amb=0.25, beams=[(594, 1150, 560, 1.0)]))
    z = 1.0 + 0.12 * c.gt / c.gdur + (0.15 * ease(c.lt / c.dur) if c.opt.get("freeze") else 0)
    return dict(img=w, zoom=z, cx=594, cy=1150, light=dict(amb=0.5, beams=[(594, 1150, 620, 1.0)]), flick=0.15, grade=(0.95, 0.97, 1.08))


def sh_jonas_close(c):
    dawn = c.opt.get("dawn")
    w = bg("dawn_blur" if dawn else "corridor_dark_blur").copy()
    e = "closed" if blink(c.t, 0.2) else ("open" if dawn else "wide")
    place(w, sprite(f"jonas_{e}_{mouth(c, 'jonas')}", 1.6), 594, BH + 30)
    if dawn:
        return dict(img=w, zoom=1.0 + 0.06 * c.lt / c.dur, cx=594, cy=1100, grade=(1.08, 1.0, 0.95))
    return dict(img=w, zoom=1.0 + 0.08 * c.lt / c.dur, cx=594, cy=1100, light=dict(amb=0.45, beams=[(594, 1100, 650, 1.0)]),
                flick=0.2, grade=(0.9, 0.97, 1.1))


def sh_blackout(c):
    w = bg("corridor_dark")
    if c.lt < 0.35:
        return dict(img=w, zoom=1.0, cx=594, cy=1056, light=dict(amb=1.0, beams=[]))
    if c.lt < 2.6:
        a = max(0.0, 1 - (c.lt - 0.35) / 0.5)
        return dict(img=w, zoom=1.0, cx=594, cy=1056, light=dict(amb=a * 0.9, beams=[]), flick=0.4 if a > 0 else 0)
    p = ease((c.lt - 2.6) / 1.4)
    return dict(img=w, zoom=1.0, cx=594, cy=1056, light=dict(amb=0.02, beams=[(250 + 400 * p, 1000, 380, 1.0)]), flick=0.2)


def sh_escalator_empty(c):
    w = darken(bg("escalator"), 0.8)
    place(w, sprite("rabbit", 0.75), 650, 1385)
    p = ease(c.lt / 1.6)
    bx, by = 712 + (650 - 712) * p, 1060 + (1330 - 1060) * p
    z = 1.0 + 0.3 * ease(c.lt / c.dur)
    return dict(img=w, zoom=z, cx=660, cy=1260, light=dict(amb=0.08, beams=[(bx, by, 330, 1.0)]), flick=0.2, grade=(0.92, 0.97, 1.1))


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
    w = bg("corridor_dark").copy()
    d, dark = creature_pose(c)
    z = 1.0 + 3.6 * d
    hpx = 2.6 * 780 / z
    s = round(hpx / 1560, 3)
    floor = scenes.corridor_floor_y(z)
    fing = "creature_1" if (c.fi // 9) % 3 == 0 else "creature_0"
    place(w, sprite(fing, s), 600, floor + 25 * s)
    by = floor - hpx * 0.7
    beams = [] if dark else [(600, by, hpx * 0.6 + 160, 1.0)]
    zoom = 1.12 + 0.1 * ease(c.lt / c.dur)
    return dict(img=w, zoom=zoom, cx=594, cy=min(1056, by + 250), light=dict(amb=0.03 if dark else 0.22, beams=beams),
                flick=0.35, grade=(0.95, 0.95, 1.05))


def sh_creature_close(c):
    w = bg("corridor_dark").copy()
    fing = "creature_1" if (c.fi // 7) % 2 else "creature_0"
    sp = sprite(fing, 1.35)
    w.paste(sp, (int(594 - sp.size[0] / 2), 260), sp)
    z = 1.0 + 0.15 * ease(c.lt / c.dur)
    return dict(img=w, zoom=z, cx=594, cy=1000, light=dict(amb=0.18, beams=[(600, 520, 460, 1.0), (594, 1700, 380, 0.5)]),
                flick=0.25, shake=1.5, grade=(0.95, 0.95, 1.05))


def glass_scene(who_sprite, scale, bottom, hands=False, knock=0.0, dawn=False):
    pre = "dawn" if dawn else "ent"
    w = bg(f"{pre}_back").copy()
    if who_sprite:
        place(w, sprite(who_sprite, scale), 594, bottom)
    if hands:
        hl = hands_layer(int(round(knock * 4)))
        w.paste(hl, (0, 0), hl)
    if not dawn:
        w.paste(bg("drops"), (0, 0), bg("drops"))
    w.paste(bg(f"{pre}_refl"), (0, 0), bg(f"{pre}_refl"))
    w.paste(bg(f"{pre}_front"), (0, 0), bg(f"{pre}_front"))
    return w


def knock_amount(c, name="glass_knock"):
    k = 0.0
    for n_, o in c.seg.get("sfx", []):
        if n_ == name and 0 <= c.lt - o < 0.8:
            k = max(k, abs(math.sin((c.lt - o) * math.pi / 0.2)))
    return k


def sh_cctv(c):
    k = knock_amount(c)
    w = glass_scene("walterwet_open_0", 0.42, 1660)
    return dict(img=w, zoom=1.0, cx=594, cy=1056, cctv=True, rain_region=scenes.GLASS, shake=2 * k)


def sh_glass_walter(c):
    o = c.opt
    if o.get("black"):
        e = "black"
    elif o.get("panic") or o.get("grin"):
        e = "open"
    else:
        e = "closed" if blink(c.t, 0.6) else "open"
    if o.get("grin"):
        m = "grin" if (c.lt > c.dur * 0.35 or o.get("black")) else "0"
    else:
        m = mouth(c, "walter_door")
    k = knock_amount(c)
    w = glass_scene(f"walterwet_{e}_{m}", 1.5, 1950, hands=True, knock=k)
    if o.get("close"):
        z = 1.55 + 0.25 * ease(c.lt / 0.8)
        return dict(img=w, zoom=z, cx=594, cy=1040, shake=5, flick=0.6, grade=(1.0, 0.85, 0.9), rain_region=scenes.GLASS)
    z = 1.0 + 0.12 * c.gt / c.gdur + (0.25 * ease(c.lt / c.dur) if o.get("grin") else 0)
    return dict(img=w, zoom=z, cx=594, cy=1060, shake=(6 if o.get("shake") else 0) + 4 * k,
                rain_region=scenes.GLASS, grade=(0.9, 0.95, 1.12), flick=0.15)


def sh_entrance(c):
    w = glass_scene(None, 1, 0)
    return dict(img=w, zoom=1.0 + 0.06 * c.lt / c.dur, cx=594, cy=1060, rain_region=scenes.GLASS, grade=(0.9, 0.95, 1.12))


def sh_dawn(c):
    p = ease(c.lt / c.dur)
    w = glass_scene("walter_open_0", round(0.45 + 0.35 * p, 2), 1420 + 300 * p, dawn=True)
    return dict(img=w, zoom=1.0 + 0.05 * p, cx=594, cy=1060, grade=(1.1, 1.0, 0.92))


def sh_walter_dawn(c):
    w = bg("dawn_blur").copy()
    e = "serious" if c.opt.get("serious") else ("closed" if blink(c.t, 0.3) else "open")
    place(w, sprite(f"walter_{e}_{mouth(c, 'walter')}", 1.6), 594, BH + 30)
    z = 1.0 + 0.08 * c.gt / c.gdur + (0.12 * ease(c.lt / c.dur) if c.opt.get("serious") else 0)
    return dict(img=w, zoom=z, cx=594, cy=1100, grade=(1.1, 1.0, 0.92))


def sh_walter_end(c):
    w = bg("corridor").copy()
    p = ease(c.gt / c.gdur)
    zdep = 2.4 + 6 * p
    s = round(1.75 * 780 / zdep / 870, 3)
    place(w, sprite("walter_back", s), 594, scenes.corridor_floor_y(zdep) + 10)
    res = dict(img=w, zoom=1.0 + 0.05 * p, cx=594, cy=1000, grade=(1.0, 1.0, 1.05), flick=0.1)
    if c.opt.get("turn") and 1.0 <= c.lt < 1.35:
        w2 = bg("corridor_dark_blur").copy()
        place(w2, sprite("walter_black_grin", 1.6), 594, BH + 30)
        res = dict(img=w2, zoom=1.2, cx=594, cy=1100, shake=8, flick=0.0, grade=(1.2, 0.8, 0.8))
    return res


SHOTS = {k[3:]: v for k, v in list(globals().items()) if k.startswith("sh_")}


# =====================================================================
#  OVERLAYS
# =====================================================================
SPEAKERS = {
    "jonas": ("JONAS", (255, 255, 255)), "walter": ("WALTER", (255, 179, 71)), "walter_door": ("WALTER", (255, 179, 71)),
    "mama": ("MAMA", (130, 205, 255)), "mama_door": ("???", (255, 95, 95)), "mia": ("MIA", (255, 160, 210)),
    "mia_dark": ("MIA", (255, 70, 70)), "creature": ("???", (255, 60, 60)),
}
YELLOW = (255, 214, 0)


def text_img(text, fnt, fill, stroke=8, stroke_fill=(0, 0, 0)):
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bb = tmp.textbbox((0, 0), text, font=fnt, stroke_width=stroke)
    im = Image.new("RGBA", (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8), 0)
    ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), text, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def word_timings(seg):
    text = seg.get("cap", seg["say"])
    words = text.split()
    wts = [len(w_) + 2 + (7 if w_[-1] in ".!?“" else (3 if w_[-1] in ",:;–" else 0)) for w_ in words]
    tot = sum(wts)
    t, out = seg["tts_start"], []
    for w_, wt in zip(words, wts):
        d = seg["tts_dur"] * wt / tot
        out.append((t, t + d, w_))
        t += d
    return out


def chunks(timed, max_chars=22, max_words=4):
    res, cur = [], []
    for item in timed:
        cand = " ".join(x[2] for x in cur + [item])
        if cur and (len(cand) > max_chars or len(cur) >= max_words):
            res.append(cur)
            cur = []
        cur.append(item)
        if item[2][-1] in ".!?:“" and len(" ".join(x[2] for x in cur)) > 6:
            res.append(cur)
            cur = []
    if cur:
        res.append(cur)
    return res


@lru_cache(1024)
def caption_block(words, hi, base_col, hi_col):
    fnt = font(F_CAP, 82)
    imgs = [text_img(w_, fnt, hi_col if i == hi else base_col, 10) for i, w_ in enumerate(words)]
    space = 22
    lines, cur, cw = [], [], 0
    for idx, im in enumerate(imgs):
        if cur and cw + space + im.size[0] > 980:
            lines.append(cur)
            cur, cw = [], 0
        cur.append((idx, im))
        cw += im.size[0] + (space if len(cur) > 1 else 0)
    lines.append(cur)
    lh = 100
    out = Image.new("RGBA", (W, lh * len(lines) + 10), 0)
    for li, ln in enumerate(lines):
        tw = sum(im.size[0] for _, im in ln) + space * (len(ln) - 1)
        x = (W - tw) // 2
        for idx, im in ln:
            dy = -5 if idx == hi else 0
            out.paste(im, (x, li * lh + dy + (lh - im.size[1]) // 2), im)
            x += im.size[0] + space
    return out


@lru_cache(16)
def tag_img(label, col):
    f = font(F_CAP, 40)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw = tmp.textlength(label, font=f)
    im = Image.new("RGBA", (int(tw) + 60, 66), 0)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.size[0] - 1, 65], 33, fill=(0, 0, 0, 190), outline=col + (255,), width=4)
    d.text((30, 8), label, font=f, fill=col + (255,))
    return im


@lru_cache(64)
def choice_card(a, b, hint):
    im = Image.new("RGBA", (W, H), 0)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, H], fill=(0, 0, 0, 135))
    q = text_img("WAS SOLL ICH TUN?", font(F_CAP, 86), (255, 255, 255), 9)
    im.paste(q, ((W - q.size[0]) // 2, 330), q)
    for k, (lab, txt, col) in enumerate((("A", a, (230, 50, 60)), ("B", b, (60, 140, 240)))):
        y0 = 500 + k * 300
        d.rounded_rectangle([60, y0, W - 60, y0 + 250], 36, fill=(10, 10, 14, 230), outline=col + (255,), width=8)
        d.ellipse([95, y0 + 55, 235, y0 + 195], fill=col + (255,))
        lt = text_img(lab, font(F_CAP, 96), (255, 255, 255), 0)
        im.paste(lt, (165 - lt.size[0] // 2, y0 + 125 - lt.size[1] // 2 - 4), lt)
        lines = wrap(txt, font(F_CAP, 58), W - 60 - 290, d)
        ly = y0 + 125 - (len(lines) * 70) // 2
        for ln in lines:
            d.text((275, ly), ln, font=font(F_CAP, 58), fill=(255, 255, 255, 255))
            ly += 70
    if hint:
        ht = text_img(hint, font(F_BOLD, 46), YELLOW, 6)
        im.paste(ht, ((W - ht.size[0]) // 2, 1110), ht)
    return im


@lru_cache(32)
def countdown_img(num, frac_bucket):
    im = Image.new("RGBA", (260, 260), 0)
    d = ImageDraw.Draw(im)
    d.ellipse([10, 10, 250, 250], fill=(0, 0, 0, 180), outline=(80, 80, 80, 255), width=10)
    d.arc([10, 10, 250, 250], -90, -90 + 360 * frac_bucket / 20, fill=(255, 60, 60, 255), width=12)
    t = text_img(str(num), font(F_CAP, 130), (255, 255, 255), 0)
    im.paste(t, (130 - t.size[0] // 2, 130 - t.size[1] // 2 - 8), t)
    return im


@lru_cache(8)
def title_img(n, name):
    im = Image.new("RGBA", (W, 560), 0)
    l1 = text_img("DIE REGELN DES", font(F_CAP, 72), (240, 240, 240), 9)
    l2 = text_img("NACHTWÄCHTERS", font(F_CAP, 106), (232, 36, 44), 10)
    im.paste(l1, ((W - l1.size[0]) // 2, 30), l1)
    im.paste(l2, ((W - l2.size[0]) // 2, 112), l2)
    d = ImageDraw.Draw(im)
    label = f"TEIL {n}" + (" · FINALE" if n == 5 else "")
    f = font(F_CAP, 54)
    tw = d.textlength(label, font=f)
    d.rounded_rectangle([(W - tw) / 2 - 34, 268, (W + tw) / 2 + 34, 352], 42, fill=(255, 255, 255, 245))
    d.text(((W - tw) / 2, 278), label, font=f, fill=(10, 10, 10, 255))
    sub = text_img(name, font(F_BOLD, 52), (255, 220, 120), 7)
    im.paste(sub, ((W - sub.size[0]) // 2, 385), sub)
    return im


@lru_cache(64)
def time_img(clock, colon):
    f = font(F_MONO, 92)
    txt = clock if colon else clock.replace(":", " ")
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw = tmp.textlength("00:00", font=f)
    im = Image.new("RGBA", (int(tw) + 120, 130), 0)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.size[0] - 1, 129], 26, fill=(0, 0, 0, 170))
    d.ellipse([28, 52, 54, 78], fill=(230, 30, 30, 255))
    d.text((74, 12), txt, font=f, fill=(255, 255, 255, 255))
    return im


@lru_cache(4)
def end_badge(n, final):
    txt = "ENDE … ODER?" if final else f"TEIL {n + 1} FOLGT ↓"
    return text_img(txt, font(F_CAP, 66), YELLOW, 9)


@lru_cache(None)
def cctv_overlay():
    im = Image.new("RGBA", (W, H), 0)
    d = ImageDraw.Draw(im)
    for y in range(0, H, 4):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, 60))
    d.rectangle([40, 120, W - 40, H - 380], outline=(220, 255, 220, 140), width=3)
    return im


# =====================================================================
#  TIMELINE + AUDIO
# =====================================================================
COUNTDOWN = 5


def speech(seg):
    who = seg["who"]
    x = voices.creature(seg["say"]) if who == "creature" else voices.speak(seg["say"], who)
    dry = len(x)
    if seg.get("hall"):
        x = sound.reverb(x, 2.4, 0.5)
    return x * seg.get("gain", 1.0), dry


def envelope(x):
    hop = SR // FPS
    n = len(x) // hop + 1
    xx = np.pad(x, (0, n * hop - len(x)))
    e = np.sqrt((xx.reshape(n, hop) ** 2).mean(axis=1))
    return e / (np.percentile(e, 95) + 1e-9)


def build_timeline(part):
    segs, t = [], 0.0
    prev_shot = None
    for i, s in enumerate(part["segs"]):
        s = dict(s)
        s.setdefault("opt", {})
        s["audio"], dry = speech(s)
        s["env"] = envelope(s["audio"][:dry])
        s["tts_start"] = 0.25 + (0.5 if i == 0 else 0)
        s["tts_dur"] = dry / SR
        dur = s["tts_start"] + s["tts_dur"] + s.get("pad", 0.3)
        if "choice" in s:
            s["cd_start"] = s["tts_start"] + s["tts_dur"] + 0.3
            dur = s["cd_start"] + COUNTDOWN + 0.4
        s["start"], s["dur"] = t, max(dur, 1.6)
        s["new_shot"] = s["shot"] != prev_shot
        prev_shot = s["shot"]
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
    speech_bus = np.zeros(L)
    tension = np.zeros(L)
    radio_env = np.zeros(L)
    rain_env = np.zeros(L)

    def put(buf, x, at, g=1.0):
        a = int(at * SR)
        if a >= L or a < 0:
            return
        e = min(L, a + len(x))
        buf[a:e] += x[:e - a] * g

    for s in segs:
        a, b = int(s["start"] * SR), int((s["start"] + s["dur"]) * SR)
        tension[a:b] = s.get("tense", 0.3)
        radio_env[a:b] = s.get("radio", 0.06)
        rain_env[a:b] = RAIN_SHOTS.get(s["shot"], 0.0)
        put(speech_bus, s["audio"], s["start"] + s["tts_start"])
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

    tension = smooth(tension, 1.2)
    radio_env = smooth(radio_env, 0.4)
    rain_env = smooth(rain_env, 0.5)
    duck = 1 - 0.6 * np.clip(smooth(np.abs(speech_bus), 0.3) * 6, 0, 1)
    mix += sound.music(L, tension, n) * duck
    mix += sound.ambience(L, n)
    mix += sound.static(L, n) * radio_env * (0.6 + 0.4 * duck)
    mix += sound.rain(L, n) * rain_env * 0.5
    mix += speech_bus
    act = np.abs(speech_bus) > 0.01
    peak = np.percentile(np.abs(speech_bus[act]), 99.5) if act.any() else 0.8
    mix = sound.soft_limit(mix, peak * 1.25)
    end = int((total + 0.15) * SR)
    fade = int(0.8 * SR)
    mix[end - fade:end] *= np.linspace(1, 0, fade)
    return mix[:end]


def write_wav(path, x):
    with wave.open(path, "wb") as w_:
        w_.setnchannels(1)
        w_.setsampwidth(2)
        w_.setframerate(SR)
        w_.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


# =====================================================================
#  FRAME-PIPELINE
# =====================================================================
def static_maps():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / (W * 0.62)) ** 2 + ((y - H / 2) / (H * 0.6)) ** 2)
    vig = np.clip(1.06 - d ** 2.2 * 0.7, 0.2, 1.0).astype(np.float32)
    rng = np.random.default_rng(1)
    grains = [np.repeat(np.repeat(rng.normal(0, 3.0, (H // 3, W // 3)), 3, 0), 3, 1).astype(np.float32) for _ in range(4)]
    return vig, grains


QH, QW = H // 8, W // 8
_qy, _qx = np.mgrid[0:QH, 0:QW]


def light_mask(light, box):
    amb = light.get("amb", 1.0)
    x0, y0, x1, y1 = box
    sx, sy = W / (x1 - x0), H / (y1 - y0)
    acc = np.zeros((QH, QW), np.float32)
    for (bx, by, r, st) in light.get("beams", []):
        cx, cy, rr = (bx - x0) * sx / 8, (by - y0) * sy / 8, r * sx / 8
        d = np.sqrt((_qx - cx) ** 2 + (_qy - cy) ** 2) / max(rr, 1)
        acc += st * np.clip(1 - d, 0, 1) ** 1.4
    m = amb + (1 - amb) * np.clip(acc, 0, 1.15)
    return np.asarray(Image.fromarray(m.astype(np.float32), "F").resize((W, H), Image.BILINEAR))


def compose_frame(part, segs, si, fi, total, vig, grains, caps):
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
    rr = np.random.default_rng(fi * 7919 + n)
    res = SHOTS[s["shot"]](c)
    # ---- Kamera
    z = res.get("zoom", 1.0)
    cw_, ch_ = BW / z, BH / z
    cx, cy = res.get("cx", BW / 2), res.get("cy", BH / 2)
    shake = res.get("shake", 0)
    for name, o in s.get("sfx", []):
        if name == "sting" and 0 <= c.lt - o < 0.5:
            shake = max(shake, 10 * (1 - (c.lt - o) / 0.5))
    if shake:
        cx += rr.uniform(-shake, shake)
        cy += rr.uniform(-shake, shake)
    cx = min(max(cx, cw_ / 2), BW - cw_ / 2)
    cy = min(max(cy, ch_ / 2), BH - ch_ / 2)
    box = (cx - cw_ / 2, cy - ch_ / 2, cx + cw_ / 2, cy + ch_ / 2)
    frame = res["img"].resize((W, H), Image.BILINEAR, box=box)
    # ---- Regen
    if res.get("rain") or res.get("rain_region"):
        rl = rain_layer()
        off = (fi * 61) % H
        layer = rl.crop((0, off, W, off + H))
        if res.get("rain_region"):
            gx0, gy0, gx1, gy1 = res["rain_region"]
            sx, sy = W / (box[2] - box[0]), H / (box[3] - box[1])
            m = Image.new("L", (W, H), 0)
            ImageDraw.Draw(m).rectangle([int((gx0 - box[0]) * sx), int((gy0 - box[1]) * sy),
                                         int((gx1 - box[0]) * sx), int((gy1 - box[1]) * sy)], fill=255)
            layer.putalpha(ImageChops.multiply(layer.getchannel("A"), m))
        frame.paste(layer, (0, 0), layer)
    # ---- Effekte
    arr = np.asarray(frame).astype(np.float32)
    mult = vig.copy()
    if res.get("light"):
        mult *= light_mask(res["light"], box)
    flick = res.get("flick", 0.1)
    b = 1.0
    if rr.random() < 0.06 + 0.3 * flick:
        b -= rr.uniform(0.04, 0.15 + 0.5 * flick)
    flash = res.get("flash", 0.0)
    for name, o in s.get("sfx", []):
        if name == "sting" and 0 <= c.lt - o < 0.12:
            flash = max(flash, 0.9)
    grade = np.array(res.get("grade", (1, 1, 1)), np.float32)
    arr *= (mult * b)[..., None] * grade[None, None, :]
    if flash > 0:
        arr += flash * 140 * np.array([0.85, 0.9, 1.0], np.float32)
    if res.get("cctv"):
        g = arr.mean(axis=2, keepdims=True)
        arr = g * np.array([0.78, 1.0, 0.82], np.float32) * 1.15 + \
            rr.normal(0, 14, (H // 4, W // 4)).repeat(4, 0).repeat(4, 1)[..., None].astype(np.float32)
    arr += grains[(fi // 2) % len(grains)][..., None]
    if s["new_shot"] and si > 0 and c.lt < 0.1:
        arr *= c.lt / 0.1 * 0.7 + 0.3
    if t < 0.35:
        arr *= t / 0.35
    if t > total - 0.7:
        arr *= max(0.0, (total - t) / 0.7)
    frame = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    # ---- Overlays
    if res.get("cctv"):
        ov = cctv_overlay()
        frame.paste(ov, (0, 0), ov)
        d = ImageDraw.Draw(frame)
        if (fi // 15) % 2 == 0:
            d.ellipse([70, 150, 100, 180], fill=(240, 30, 30))
        d.text((115, 144), "REC  CAM 03  HAUPTEINGANG", font=font(F_MONO, 34), fill=(230, 255, 230))
        d.text((W - 260, 144), f"05:41:{int(c.lt) + 10:02d}", font=font(F_MONO, 34), fill=(230, 255, 230))
    if "time" in s and c.lt < 2.4 and s["shot"] != "cctv":
        ti = time_img(s["time"], (fi // 15) % 2 == 0)
        frame.paste(ti, ((W - ti.size[0]) // 2, 200), ti)
    if s.get("title") and c.lt < 3.4:
        ti = title_img(n, part["name"])
        a = min(1, c.lt / 0.3) * min(1, (3.4 - c.lt) / 0.5)
        if a < 1:
            ti = ti.copy()
            ti.putalpha(ti.getchannel("A").point(lambda v: int(v * a)))
        frame.paste(ti, (0, 330), ti)
    if "choice" in s:
        card = choice_card(s["choice"][0], s["choice"][1], s.get("hint"))
        a_in = min(1, c.lt / 0.3)
        if a_in < 1:
            card = card.copy()
            card.putalpha(card.getchannel("A").point(lambda v: int(v * a_in)))
        frame.paste(card, (0, 0), card)
        if c.lt >= s["cd_start"]:
            el = c.lt - s["cd_start"]
            cd = countdown_img(max(1, COUNTDOWN - int(el)), int(min(1, el / COUNTDOWN) * 20))
            frame.paste(cd, ((W - 260) // 2, 1240), cd)
    elif caps[si]:
        who = s["who"]
        label, col = SPEAKERS[who]
        dialog = who != "jonas" or bool(s.get("talk"))
        base = col if dialog else (255, 255, 255)
        hi_col = (255, 255, 255) if dialog else YELLOW
        ycap = 1450 if s["shot"] == "card" else 1330
        for ch in caps[si]:
            a_, b_ = ch[0][0], ch[-1][1]
            last = ch is caps[si][-1]
            if a_ <= c.lt < (s["dur"] if last else b_):
                words = tuple(x[2] for x in ch)
                hi = max([i for i, x in enumerate(ch) if x[0] <= c.lt] or [0])
                if c.lt >= b_:
                    hi = -1
                blk = caption_block(words, hi, base, hi_col)
                frame.paste(blk, (0, ycap - blk.size[1] // 2), blk)
                if dialog:
                    tg = tag_img(label, col)
                    frame.paste(tg, ((W - tg.size[0]) // 2, ycap - blk.size[1] // 2 - 78), tg)
                break
        if s.get("end") and (int(c.lt * 2) % 2 == 0 or c.lt > s["tts_start"] + s["tts_dur"]):
            eb = end_badge(n, bool(s.get("final")))
            frame.paste(eb, ((W - eb.size[0]) // 2, 1500), eb)
    return frame


def render_part(part, preview=None):
    n = part["n"]
    art.build()
    segs, total = build_timeline(part)
    print(f"Teil {n}: {total:.1f}s, {len(segs)} Segmente", flush=True)
    vig, grains = static_maps()
    caps = [chunks(word_timings(s)) if s.get("say") else [] for s in segs]
    if preview is not None:
        # Einzelbilder (Sekunden) für schnelle Kontrolle
        outs = []
        for ts in preview:
            fi = int(ts * FPS)
            si = max(i for i, s in enumerate(segs) if s["start"] <= ts)
            outs.append(compose_frame(part, segs, si, fi, total, vig, grains, caps))
        return outs, segs
    wav = os.path.join(BUILD, f"teil{n}_v2.wav")
    write_wav(wav, mix_audio(segs, total, n))
    out = os.path.join(OUT, f"nachtwaechter_teil{n}.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                           "-maxrate", "3500k", "-bufsize", "7000k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                           "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    nframes = int(total * FPS)
    si = 0
    for fi in range(nframes):
        t = fi / FPS
        while si < len(segs) - 1 and t >= segs[si]["start"] + segs[si]["dur"]:
            si += 1
        frame = compose_frame(part, segs, si, fi, total, vig, grains, caps)
        ff.stdin.write(frame.tobytes())
        if fi % 300 == 0:
            print(f"  Teil {n}: Frame {fi}/{nframes}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("fertig:", out, flush=True)
    return out


def remux(part):
    """Nur die Tonspur neu erzeugen und ins vorhandene Video einsetzen."""
    n = part["n"]
    segs, total = build_timeline(part)
    wav = os.path.join(BUILD, f"teil{n}_v2.wav")
    write_wav(wav, mix_audio(segs, total, n))
    out = os.path.join(OUT, f"nachtwaechter_teil{n}.mp4")
    tmp = out + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out)
    print("Ton erneuert:", out, flush=True)


if __name__ == "__main__":
    if "--audio" in sys.argv:
        which = [int(a) for a in sys.argv[1:] if a.isdigit()] or [p["n"] for p in story.PARTS]
        for p in story.PARTS:
            if p["n"] in which:
                remux(p)
        sys.exit(0)
    which = [int(a) for a in sys.argv[1:] if a.isdigit()] or [p["n"] for p in story.PARTS]
    for p in story.PARTS:
        if p["n"] in which:
            render_part(p)
