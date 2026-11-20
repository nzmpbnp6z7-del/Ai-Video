"""MATHESTUNDE – ein Film in sehr schlechtem 3D.

Ein Apfel (Kevin) schläft im Matheunterricht ein, träumt von Schafen auf
Drogen, gerät in eine Schlafparalyse und wird von seinem Lehrer, Herrn
Banane, geweckt. Ohne Ton, mit eingebrannten Untertiteln.

Aufruf:  python3 film.py [ausgabe.mp4] [--preview SEKUNDE ...]
"""
import math
import subprocess
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from engine import (W, H, Scene, T, S, R, Rx, Ry, Rz, SPH, SPH_LO, BOX, CYL, CONE,
                    PYR, hsv, mix, gradient, hue_shift, vignette, grain, tint,
                    desat, glitch)
from chars import (apple, orange, pear, grape, lemon, banana, sheep, desk,
                   classroom, meadow, fence, mushroom, bedroom, WHITE)

FPS = 15                      # ruckelig mit Absicht
OUT_W, OUT_H = 1080, 1920
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
PI = math.pi


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


def step(t, fps=6):
    """Animation mit noch weniger Bildern (stotterig)."""
    return math.floor(t * fps) / fps


# ---------------------------------------------------------------- Tafel
def make_board(text_lines, sheep_doodle=False):
    img = Image.new("RGB", (480, 180), (38, 70, 48))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, 34)
    for i, line in enumerate(text_lines):
        d.text((24, 18 + i * 52), line, font=f, fill=(235, 235, 225))
    if sheep_doodle:
        for cx, cy in ((380, 120), (430, 60)):
            d.ellipse((cx - 30, cy - 18, cx + 30, cy + 18), outline=(235, 235, 225), width=3)
            d.ellipse((cx + 22, cy - 14, cx + 40, cy + 4), outline=(235, 235, 225), width=3)
    return img


BOARD = make_board(["x² + 7x − 3 = 0", "x = ???", "(KLAUSUR MORGEN!!)"])

STUDENTS = [  # (Art, x, z)
    ("orange", -3.5, -1.0), ("pear", 0.0, -1.0), ("grape", 3.5, -1.0),
    ("lemon", -3.5, 2.5), ("pear", 0.0, 2.5), ("apple", 3.5, 2.5),
]
KEVIN = np.array([3.5, 1.75, 2.5])
FRUIT_FN = {"orange": orange, "pear": pear, "grape": grape, "lemon": lemon}


def class_scene(t, teacher_x=0.0, teacher_z=-4.3, teacher_kw=None, kevin_kw=None,
                kevin_tilt=0.0, kevin_yaw=PI, students_look=None, board=BOARD,
                with_teacher=True, kevin_dy=0.0):
    sc = Scene()
    classroom(sc, t, board)
    for kind, x, z in STUDENTS:
        desk(sc, x, z - 0.8)
        if kind == "apple":
            kw = dict(arms=((-1.3, -0.9, 0.9), (1.3, -0.9, 0.9)))
            kw.update(kevin_kw or {})
            M = T(KEVIN[0], KEVIN[1] + kevin_dy, KEVIN[2]) @ Ry(kevin_yaw) @ Rx(kevin_tilt) @ S(0.55)
            apple(sc, M, **kw)
        else:
            yaw = PI
            look = (0, 0)
            if students_look is not None:
                dx, dz = KEVIN[0] - x, KEVIN[2] - z
                tgt = math.atan2(dx, dz)
                yaw = lerp(PI, tgt if tgt > 0 else tgt + 2 * PI, students_look)
                look = (0.8 * students_look, 0)
            FRUIT_FN[kind](sc, T(x, 1.75, z) @ Ry(yaw) @ S(0.5), look=look,
                           mouth="line" if students_look else "smile")
    if with_teacher:
        banana(sc, T(teacher_x, 1.6, teacher_z) @ S(0.75), **(teacher_kw or {}))
    return sc


# ---------------------------------------------------------------- Shots
# Jeder Shot: (Dauer, Renderfunktion(t) -> (Bild, Overlays), Untertitel)
# Untertitel: (start, ende, Sprecher, Text) relativ zum Shot.
SHOTS = []


def shot(dur, subs=()):
    def deco(fn):
        SHOTS.append((dur, fn, list(subs)))
        return fn
    return deco


@shot(3.2)
def s_title(t):
    sc = Scene()
    a = step(t, 8) * 2.2
    apple(sc, T(0, 0.2 + 0.15 * math.sin(t * 5), 0) @ Ry(a) @ Rz(0.2 * math.sin(t * 3)),
          eye_open=1.0, mouth="smile",
          arms=((-1.4, 0.3 + 0.4 * math.sin(t * 9), 0.2), (1.4, -0.7, 0.2)))
    img, _ = sc.render((0, 0.4, 6.0), (0, 0.2, 0), fov=50,
                       bg=gradient((40, 0, 70), (220, 60, 160)), light=(0.3, 0.6, 0.8))
    wob = math.sin(t * 6) * 4
    ov = [dict(text="MATHESTUNDE", x=540, y=430, size=120, fill=(255, 230, 0),
               stroke=(120, 0, 120), sw=10, angle=wob),
          dict(text="ein Film in hochwertigem 3D*", x=540, y=560, size=50,
               fill=(255, 255, 255), stroke=(0, 0, 0), sw=5)]
    if t > 1.6:
        ov.append(dict(text="*nicht hochwertig", x=540, y=1500, size=38,
                       fill=(255, 255, 255), stroke=(0, 0, 0), sw=4))
    return img, ov


@shot(7.0, [(0.2, 3.5, "Herr Banane", "Also, Kinder. Heute: quadratische Gleichungen."),
            (3.5, 7.0, "Herr Banane", "Wenn x² plus 7x minus 3 gleich null ist, dann ist x ... äh ... irgendwas.")])
def s_class_wide(t):
    tx = math.sin(t * 0.9) * 1.8  # rutscht ohne Beinbewegung hin und her
    talk = "talk" if int(t * 6) % 2 else "line"
    sc = class_scene(t, teacher_x=tx, teacher_kw=dict(
        arm_r=0.4 + 0.5 * math.sin(t * 4), mouth=talk))
    cam = (1.2 + 0.3 * math.sin(t * 0.5), 6.2, 10.0)
    img, _ = sc.render(cam, (0.5, 2.6, -4), fov=62, bg=(0, 0, 0), light=(-0.3, 0.8, 0.6))
    return img, []


@shot(8.0, [(0.3, 3.0, "Kevin (denkt)", "Mathe ... so ... langweilig ..."),
            (3.0, 5.8, "Kevin (denkt)", "Nur fünf Sekunden die Augen zumachen ..."),
            (5.9, 6.8, None, "*KLONK*"),
            (6.8, 8.0, "Kevin", "Zzzzz ... Mäh ...")])
def s_kevin_sleepy(t):
    # Augen: zu - auf (Schreck) - zu - ganz zu
    if t < 2.0:
        eo = lerp(1.0, 0.45, ease(t / 2.0))
    elif t < 2.4:
        eo = 1.0
    elif t < 5.5:
        eo = lerp(1.0, 0.0, ease((t - 2.4) / 2.8))
    else:
        eo = 0.0
    tilt = 0.1 + 0.06 * math.sin(t * 2)
    if t > 2.4:
        tilt = lerp(0.1, 0.45, ease((t - 2.4) / 3.0))
    if t > 5.8:
        tilt = 1.35  # Kopf knallt durch den Tisch
    mouth = "line" if t < 5.8 else "snore"
    shake = 0.12 if 5.8 < t < 6.3 else 0.0
    sc = class_scene(t, teacher_x=-1.0, teacher_kw=dict(mouth="talk", arm_r=0.8),
                     kevin_tilt=tilt, kevin_kw=dict(eye_open=eo, mouth=mouth,
                                                    look=(0, -0.5)))
    jx = shake * math.sin(t * 90)
    img, proj = sc.render((3.5 + jx, 2.35, 0.3), (3.5, 1.7, 2.5), fov=58, bg=(0, 0, 0),
                          light=(0.2, 0.7, -0.7))
    ov = []
    if t > 6.6:
        p = proj((3.6, 2.6, 2.3))
        if p:
            for k in range(3):
                tt = (t - 6.6 - k * 0.35)
                if tt > 0:
                    ov.append(dict(text="Z", x=p[0] * 3 + 60 * k + tt * 60,
                                   y=p[1] * 3 - 90 * k - tt * 120, size=90 + 20 * k,
                                   fill=(255, 255, 255), stroke=(40, 40, 120), sw=6))
    return img, ov


@shot(1.6)
def s_swirl(t):
    sc = class_scene(8 + t, teacher_x=-1.0, kevin_tilt=1.35,
                     kevin_kw=dict(eye_open=0, mouth="snore"))
    img, _ = sc.render((3.5, 2.35, 0.3), (3.5, 1.7, 2.5), fov=58, bg=(0, 0, 0),
                       light=(0.2, 0.7, -0.7))
    img = img.rotate(step(t, 10) * 400, resample=Image.NEAREST)
    img = img.resize((int(W * (1 + t)), int(H * (1 + t))), Image.NEAREST)
    img = img.crop(((img.width - W) // 2, (img.height - H) // 2,
                    (img.width - W) // 2 + W, (img.height - H) // 2 + H))
    img = hue_shift(img, t * 0.6)
    return tint(img, (255, 255, 255), ease((t - 1.0) / 0.6)), [
        dict(text="~ TRAUMLAND ~", x=540, y=900, size=90, fill=(255, 150, 255),
             stroke=(60, 0, 80), sw=8, angle=t * 40)]


def dream_bg(t):
    return gradient(hsv(0.85 + t * 0.07, 0.45, 1.0), hsv(0.55 + t * 0.09, 0.4, 1.0))


def dream_props(sc, t):
    for k, (x, z, s) in enumerate(((-5, -6, 1.6), (6, -8, 2.2), (-8, 2, 1.3), (7, 1, 1.0))):
        mushroom(sc, x, z, s, t * (1 + k * 0.3), 0.0 + 0.1 * math.sin(t + k))
    for k in range(6):  # schwebende Würfel und Pyramiden
        a = t * 0.5 + k
        M = T(math.cos(a) * 7, 4 + math.sin(t * 1.3 + k) * 1.2, -6 + math.sin(a) * 3) @ R(t * 2 + k, t * 3, k)
        sc.add(BOX if k % 2 else PYR, M @ S(0.5), hsv(k / 6 + t * 0.2, 0.8, 1.0))
    # Sonne mit Gesicht (schaut zu)
    M = T(5, 9, -15) @ Ry(math.sin(t) * 0.3)
    sc.add(SPH, M @ S(2.2), (255, 220, 60), emissive=True)
    from chars import face
    face(sc, M @ S(2.2), 1.0, 1.0, (math.sin(t * 2), 0), "smile")


@shot(6.5, [(0.3, 3.3, "Kevin (träumt)", "Okay ... Schäfchen zählen. Eins ... zwei ..."),
            (3.3, 6.5, "Kevin", "... Moment. Warum drehen die sich?")])
def s_counting(t):
    sc = Scene()
    meadow(sc, t, wild=0.6)
    dream_props(sc, t)
    fence(sc, -1.5, 1.5, 0)
    apple(sc, T(-3.6, 1.65, 1.5) @ Ry(0.9) @ S(0.7), eye_open=1.0,
          look=(0.6, 0.2), mouth="smile" if t < 3.3 else "o",
          arms=((-1.4, -0.6, 0.2), (1.2, 0.4 + 0.3 * math.sin(t * 8), 0.6)), legs=True)
    for k in range(4):
        tt = (t * 0.7 - k * 0.42) % 1.6
        x = lerp(4.5, -4.5, tt / 1.6)
        y = 1.3 + max(0, math.sin(tt / 1.6 * PI)) * 2.4
        spin = 0.0 if t < 2.5 else (t - 2.5) * 3.0 * (1 + k)
        sheep(sc, T(x, y, -0.3 - 0.1 * k) @ Ry(-PI / 2) @ Rx(-spin) @ S(0.75),
              wool=mix(WHITE, hsv(k * 0.25 + t * 0.3, 0.6, 1), min(1, t / 6)),
              leg_phase=t * 12, eye_size=1.0 + 0.4 * (k % 2), pupil=(1.3, 0.7),
              tongue=t > 3.3)
    img, _ = sc.render((0.5, 2.6, 8.5), (0, 1.5, 0), fov=62, bg=dream_bg(t),
                       light=(0.3, 0.8, 0.6))
    return img, []


@shot(10.2, [(0.2, 3.4, "Schaf 1", "Määäh ... Bruder ... ich kann Farben schmecken. Lila schmeckt nach Montag."),
             (3.4, 6.8, "Schaf 2", "Das Gras hier ist NICHT normales Gras. Ich hab drei Bissen genommen und jetzt seh ich Mathe."),
             (6.8, 10.2, "Schaf 3", "ICH BIN EINE WOLKE. ICH WAR SCHON IMMER EINE WOLKE.")])
def s_sheep_closeups(t):
    sc = Scene()
    meadow(sc, t, wild=1.2)
    dream_props(sc, t)
    if t < 3.4:
        wob = math.sin(t * 7) * 0.25
        sheep(sc, T(0, 1.2, 0) @ Ry(0.3 + wob) @ Rz(wob * 0.6), wool=hsv(t * 0.5, 0.5, 1),
              eye_size=1.7, pupil=(1.6, 0.4), iris=hsv(t * 2, 1, 1), tongue=True,
              look=(math.sin(t * 13), math.cos(t * 11)))
        cam, tgt = (0.7, 1.9, 3.3), (0, 1.5, 0.6)
    elif t < 6.8:
        tt = t - 3.4
        sheep(sc, T(0, 1.1 + 0.3 * math.sin(tt * 3), 0) @ Ry(0.4) @ Rz(PI + 0.2 * math.sin(tt * 2)) @ S(1.0),
              wool=hsv(0.3 + tt * 0.4, 0.55, 1), eye_size=1.4, pupil=(0.3, 0.3),
              iris=(255, 40, 40), mouth="wobble")
        # liegt auf dem Rücken und schwebt trotzdem; daneben das "Gras"
        for k in range(7):
            sc.add(CONE, T(-1.8 + k * 0.6, 0.35, 1.5 + (k % 2) * 0.4) @ S(0.12, 0.35, 0.12),
                   hsv(0.75 + k * 0.05 + tt, 1, 1), emissive=True)
        cam, tgt = (-0.3, 1.3, 4.8), (0, 0.8, 0.6)
    else:
        tt = t - 6.8
        h = 2.5 + tt * 0.4
        sheep(sc, T(0, h, 0) @ R(tt * 0.8, tt * 2.5, math.sin(tt * 2) * 0.5) @ S(1.1),
              wool=WHITE, eye_size=1.5, pupil=(1.8, 1.8), iris=(80, 160, 255),
              mouth="scream", tongue=True)
        for k in range(10):  # Regenbogen-Ring
            a = k / 10 * 2 * PI + tt * 2
            sc.add(SPH_LO, T(math.cos(a) * 2.2, h + math.sin(a) * 2.2, -0.8) @ S(0.35),
                   hsv(k / 10, 1, 1), emissive=True)
        cam, tgt = (0.0, 1.0, 5.5), (0, h, 0)
    img, _ = sc.render(cam, tgt, fov=60, bg=dream_bg(t), light=(0.3, 0.8, 0.7))
    if t > 6.8:
        img = hue_shift(img, math.sin(t * 3) * 0.1)
    return img, []


@shot(6.4, [(0.2, 3.2, "Kevin", "Äh ... Leute? Geht's euch gut?"),
            (3.6, 6.4, "Alle Schafe", "MÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄH.")])
def s_circle(t):
    sc = Scene()
    snap = t > 3.5
    meadow(sc, t, wild=1.0 if not snap else 0.0, hue0=0.3 if not snap else 0.0)
    if not snap:
        dream_props(sc, t)
    apple(sc, T(0, 1.65, 0) @ Ry(0.2 * math.sin(t * 2)) @ S(0.7),
          eye_open=1.0, eye_size=1.0 if not snap else 1.4, look=(math.sin(t * 3), 0),
          mouth="o" if not snap else "scream", sweat=0 if not snap else 1,
          arms=((-1.4, -0.5, 0.3), (1.4, -0.5, 0.3)))
    n = 7
    for k in range(n):
        a = k / n * 2 * PI + (t * 0.7 if not snap else 3.5 * 0.7)
        x, z = math.cos(a) * 4.2, math.sin(a) * 4.2
        if snap:
            yaw = math.atan2(0.0 - x, 8.0 - z)  # alle starren in die Kamera
        else:
            yaw = a + PI + math.sin(t * 5 + k) * 0.6
        sheep(sc, T(x, 1.2 + (0 if snap else 0.4 * abs(math.sin(t * 4 + k))), z) @ Ry(yaw) @ S(0.75),
              wool=hsv(k / n + t * 0.4, 0.5, 1) if not snap else (230, 230, 230),
              eye_size=1.4 if snap else 1.2, pupil=(1.4, 0.5) if not snap else (0.35, 0.35),
              tongue=not snap, leg_phase=t * 10, mouth="scream" if snap else None)
    shake = (0.15 * math.sin(t * 70)) if snap else 0.0
    cam = (shake, 4.2 + shake, 8.5)
    bg = dream_bg(t) if not snap else gradient((120, 0, 0), (20, 0, 0))
    img, _ = sc.render(cam, (0, 1.5, 0), fov=62, bg=bg, light=(0.2, 0.8, 0.6))
    if snap:
        img = tint(desat(img, 0.8), (150, 0, 0), 0.25)
    return img, []


@shot(0.8)
def s_glitch(t):
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(int(t * FPS))
    for _ in range(30):
        x, y = rng.integers(0, W), rng.integers(0, H)
        d.rectangle((x, y, x + rng.integers(10, 120), y + rng.integers(2, 20)),
                    fill=tuple(int(c) for c in rng.integers(0, 255, 3)))
    return glitch(img, int(t * FPS)), [dict(text="FEHLER: TRAUM.EXE REAGIERT NICHT", x=540,
                                            y=960, size=48, fill=(255, 255, 255),
                                            stroke=(0, 0, 0), sw=5)]


def night_post(img, t, dark=0.0):
    img = desat(img, 0.6)
    img = vignette(img, 1.6)
    img = grain(img, 18, int(t * FPS) + 7)
    if dark:
        img = tint(img, (0, 0, 0), dark)
    return img


def kevin_in_bed(sc, t, eye_look):
    M = T(0, 1.55, 1.5) @ Rx(-PI / 2) @ Rz(PI) @ S(0.6)
    apple(sc, M, eye_open=1.0, eye_size=1.3, pupil=(0.6, 0.6), look=eye_look,
          mouth="line", arms=((-1.3, -1.0, -0.5), (1.3, -1.0, -0.5)), legs=False,
          brows=-0.4, sweat=1)


@shot(6.4, [(0.3, 3.4, "Kevin", "Wo ... bin ich? Warum kann ich mich nicht bewegen?!"),
            (3.4, 6.4, "Kevin", "Meine Arme ... gehorchen nicht ... und ich hab gar keine Arme ... oder?")])
def s_paralysis_top(t):
    sc = Scene()
    bedroom(sc)
    look = (math.sin(step(t, 3) * 7) * 1.2, math.cos(step(t, 3) * 5) * 0.8)
    kevin_in_bed(sc, t, look)
    cam = (0.05, 5.6 - t * 0.15, 1.7)
    img, _ = sc.render(cam, (0, 1.5, 1.45), fov=55, bg=(5, 5, 10),
                       light=(0.4, 0.9, -0.3), amb=0.25)
    return night_post(img, t), []


@shot(6.4, [(1.2, 3.4, "???", "määäh."),
            (3.4, 6.4, "Kevin (kann nicht schreien)", "...!!! ...!!!! ...!!!!!")])
def s_paralysis_pov(t):
    sc = Scene()
    bedroom(sc)
    # Schatten-Schaf teleportiert ruckartig näher (Keyframes vergessen)
    stage = min(3, int(max(0, t - 1.0) / 1.4))
    zpos = [-5.0, -3.6, -2.0, -0.6][stage]
    if t > 1.0:
        sheep(sc, T(0, 1.4 + 0.2 * stage, zpos) @ Ry(0) @ S(0.9 + 0.15 * stage),
              wool=(18, 18, 22), skin=(8, 8, 10), red_eyes=True, eye_size=1.0 + 0.3 * stage)
    cam = (0.0 + 0.03 * math.sin(t * 40), 2.4, 2.2)
    img, _ = sc.render(cam, (0, 1.5, -4.5), fov=60, bg=(5, 5, 10),
                       light=(0.4, 0.9, 0.3), amb=0.22)
    img = night_post(img, t)
    if t > 1.0 and int(t * FPS) % 9 == 0:
        img = glitch(img, int(t * 100))
    return img, []


@shot(3.2, [(0.2, 3.2, "Schatten-Schaf", "Du hast ... deine Hausaufgaben ... nicht gemacht.")])
def s_shadow_close(t):
    sc = Scene()
    bedroom(sc)
    sheep(sc, T(0, 2.0, -2.2) @ Ry(math.sin(t * 9) * 0.1) @ S(1.4), wool=(18, 18, 22),
          skin=(8, 8, 10), red_eyes=True, eye_size=1.6 + t * 0.2)
    cam = (0.05 * math.sin(t * 50), 2.7, 2.3 - t * 0.2)
    img, _ = sc.render(cam, (0, 2.6, -2.0), fov=60, bg=(0, 0, 0), light=(0.3, 0.9, 0.4), amb=0.2)
    img = night_post(img, t)
    if int(t * FPS) % 5 < 2:
        img = tint(img, (200, 0, 0), 0.4)
    return img, []


@shot(1.4, [(0.0, 1.4, "???", "KEEEEEEVIN!!!")])
def s_wake_flash(t):
    a = min(1, t / 0.5)
    img = Image.new("RGB", (W, H), mix((0, 0, 0), (255, 250, 200), a))
    sc = Scene()
    banana(sc, T(0, 0.3, 0) @ Ry(math.sin(t * 30) * 0.2) @ S(1.3), mouth="scream",
           brows=-0.5, arm_r=1.2, arm_l=1.2)
    img2, _ = sc.render((0, 0.6, 5.5), (0, 0.6, 0), fov=60, bg=(255, 250, 200),
                        light=(0.2, 0.8, 0.7))
    if t > 0.5:
        img = img2
    off = int(8 * math.sin(t * 80))
    return img.rotate(off, resample=Image.NEAREST), []


@shot(6.2, [(0.2, 2.6, "Herr Banane", "KEVIN! AUFWACHEN!"),
            (2.6, 6.2, "Herr Banane", "Wenn du schon schläfst: Was ist die Lösung?")])
def s_wake(t):
    jolt = t < 0.7
    sc = class_scene(t, with_teacher=False, kevin_tilt=0.0 if not jolt else -0.4,
                     kevin_dy=0.35 if jolt else 0.0,
                     kevin_kw=dict(eye_open=1.0, eye_size=1.5, pupil=(0.5, 0.5),
                                   mouth="scream" if t < 2.6 else "line", sweat=1,
                                   arms=((-1.5, 0.6, 0.3), (1.5, 0.6, 0.3)) if jolt else
                                   ((-1.3, -0.9, 0.9), (1.3, -0.9, 0.9))))
    # Herr Banane steht direkt vor Kevin, Nase an Nase
    talk = "scream" if t < 2.6 else ("talk" if int(t * 6) % 2 else "line")
    banana(sc, T(3.4, 1.5, 0.3) @ Ry(0.15) @ S(0.75), mouth=talk, brows=-0.5,
           arm_r=1.0 + 0.3 * math.sin(t * 8), look=(0.3, 0))
    cam = (7.5, 3.0, -0.6)
    img, _ = sc.render(cam, (3.4, 2.0, 1.4), fov=58, bg=(0, 0, 0), light=(0.6, 0.8, 0.3))
    return img, []


@shot(4.0, [(1.0, 4.0, "Kevin", "... Määäh?")])
def s_answer(t):
    sc = class_scene(t + 20, with_teacher=False,
                     kevin_kw=dict(eye_open=1.0, eye_size=1.1, pupil=(0.6, 1.5),
                                   mouth="o" if t > 1.0 else "line", sweat=min(1, t / 2),
                                   look=(0.6, 0.3)))
    img, _ = sc.render((3.5, 2.3, 0.6), (3.5, 1.9, 2.5), fov=50, bg=(0, 0, 0),
                       light=(0.2, 0.7, -0.7))
    return img, []


@shot(3.6, [(0.0, 1.5, None, "*alle starren*"),
            (1.5, 3.6, "Herr Banane", "... Nachsitzen.")])
def s_stare(t):
    look = 1.0 if t > 0.4 else 0.0  # alle drehen sich gleichzeitig. Ohne Animation.
    sc = class_scene(t + 25, teacher_x=2.0, teacher_z=-1.8, students_look=look,
                     teacher_kw=dict(mouth="line" if t < 1.5 else "talk", brows=-0.4,
                                     arm_r=-0.5))
    img, _ = sc.render((5.2, 3.3, 5.6), (0.5, 1.6, -1.2), fov=64, bg=(0, 0, 0),
                       light=(0.2, 0.8, 0.5))
    return img, []


@shot(4.4, [(1.4, 3.2, "Mini-Schaf", "määäh."),
            (3.2, 4.4, "Kevin", "NEIN.")])
def s_final(t):
    sc = class_scene(t + 30, with_teacher=False,
                     kevin_kw=dict(eye_open=1.0 if t > 3.0 else 0.6, eye_size=1.0 if t < 3 else 1.6,
                                   pupil=(1, 1) if t < 3 else (0.4, 0.4),
                                   mouth="line" if t < 3.2 else "scream", look=(0.9, -0.2)))
    # Mini-Schaf fährt durch die Tischplatte nach oben (Kollision? Nie gehört.)
    y = lerp(0.2, 1.45, ease((t - 0.6) / 0.9))
    sheep(sc, T(4.25, y, 1.7) @ Ry(PI + 0.4) @ Rz(0.2 * math.sin(t * 8)) @ S(0.25),
          wool=hsv(t * 0.6, 0.5, 1), eye_size=1.6, pupil=(1.6, 0.4), iris=(0, 220, 0),
          tongue=True)
    img, _ = sc.render((3.6, 2.4, 0.2), (3.8, 1.7, 2.3), fov=55, bg=(0, 0, 0),
                       light=(0.2, 0.7, -0.7))
    return img, []


@shot(3.4)
def s_end(t):
    sc = Scene()
    sc.add(BOX, R(step(t, 8) * 1.3, step(t, 8) * 2, 0.3) @ S(0.8), hsv(t * 0.3, 0.7, 1))
    img, _ = sc.render((0, 0, 6), (0, 0, 0), fov=50, bg=(0, 0, 0), light=(0.3, 0.6, 0.8))
    return img, [dict(text="ENDE", x=540, y=500, size=150, fill=(255, 230, 0),
                      stroke=(120, 0, 120), sw=10),
                 dict(text="Bei den Dreharbeiten wurden", x=540, y=1380, size=40,
                      fill=(255, 255, 255), stroke=(0, 0, 0), sw=4),
                 dict(text="keine Schafe nüchtern.", x=540, y=1440, size=40,
                      fill=(255, 255, 255), stroke=(0, 0, 0), sw=4)]


# ---------------------------------------------------------------- Text
_font_cache = {}


def font(size):
    if size not in _font_cache:
        _font_cache[size] = ImageFont.truetype(FONT, size)
    return _font_cache[size]


def draw_overlay(img, o):
    f = font(o["size"])
    if o.get("angle"):
        tmp = Image.new("RGBA", (1080, 400), (0, 0, 0, 0))
        d = ImageDraw.Draw(tmp)
        d.text((540, 200), o["text"], font=f, fill=o["fill"], anchor="mm",
               stroke_width=o.get("sw", 0), stroke_fill=o.get("stroke"))
        tmp = tmp.rotate(o["angle"], resample=Image.BICUBIC)
        img.paste(tmp, (int(o["x"] - 540), int(o["y"] - 200)), tmp)
    else:
        d = ImageDraw.Draw(img)
        d.text((o["x"], o["y"]), o["text"], font=f, fill=o["fill"], anchor="mm",
               stroke_width=o.get("sw", 0), stroke_fill=o.get("stroke"))


def wrap(text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if f.getlength(test) <= maxw:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_subtitle(img, speaker, text):
    d = ImageDraw.Draw(img)
    f = font(58)
    lines = wrap(text, f, 960)
    y = 1450
    if speaker:
        d.text((540, y), speaker + ":", font=font(44), fill=(255, 225, 60), anchor="mm",
               stroke_width=5, stroke_fill=(0, 0, 0))
        y += 66
    for line in lines:
        d.text((540, y), line, font=f, fill=(255, 255, 255), anchor="mm",
               stroke_width=6, stroke_fill=(0, 0, 0))
        y += 72


WATERMARK = "MeshMaster 3D – TESTVERSION"


def frame(gt):
    acc = 0.0
    for dur, fn, subs in SHOTS:
        if gt < acc + dur:
            t = gt - acc
            low, ov = fn(t)
            img = low.resize((OUT_W, OUT_H), Image.NEAREST)
            for o in ov:
                draw_overlay(img, o)
            for a, b, who, txt in subs:
                if a <= t < b:
                    draw_subtitle(img, who, txt)
            d = ImageDraw.Draw(img)
            d.text((1060, 40), WATERMARK, font=font(26), fill=(255, 255, 255),
                   anchor="ra", stroke_width=2, stroke_fill=(0, 0, 0))
            return img
        acc += dur
    return Image.new("RGB", (OUT_W, OUT_H))


def total():
    return sum(s[0] for s in SHOTS)


def main():
    args = sys.argv[1:]
    if args and args[0] == "--preview":
        for s in args[1:]:
            frame(float(s)).save(f"preview_{float(s):05.1f}.png")
        return
    out = args[0] if args else "output/mathestunde.mp4"
    n = int(round(total() * FPS))
    print(f"{n} Frames, {total():.1f} s")
    p = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{OUT_W}x{OUT_H}", "-framerate", str(FPS), "-i", "-",
         "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "27",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", out],
        stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(i / FPS).tobytes())
        if i % 60 == 0:
            print(f"  {i}/{n}", flush=True)
    p.stdin.close()
    p.wait()
    print("fertig:", out)


if __name__ == "__main__":
    main()
