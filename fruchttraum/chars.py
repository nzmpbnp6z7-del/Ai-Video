"""Figuren und Kulissen aus Primitiven (Kugeln, Kisten, Zylinder)."""
import math
import numpy as np
from engine import (T, S, R, Rx, Ry, Rz, seg, SPH, SPH_LO, SPH_HI, BOX, CYL,
                    CYL5, CONE, PYR, hsv, mix)

WHITE = (245, 245, 240)
BLACK = (20, 15, 15)
DARK = (60, 25, 25)
BROWN = (110, 70, 35)
GREEN = (60, 160, 50)


def transform_point(M, p):
    return (M @ np.array([p[0], p[1], p[2], 1.0]))[:3]


# ---------------------------------------------------------------- Gesicht
def face(sc, M, r=1.0, eye_open=1.0, look=(0, 0), mouth="smile", ex=0.33,
         ey=0.25, eye_size=1.0, pupil=(1.0, 1.0), white=WHITE, iris=None,
         brows=None, glasses=False, eye_col=None):
    """Augen + Mund auf der +z-Seite einer Kugel mit Radius r."""
    ez = r * 0.82
    for i, sx in enumerate((-1, 1)):
        x = ex * sx * r
        es = eye_size * r
        op = max(eye_open, 0.07)
        if glasses:
            sc.add(BOX, M @ T(x, ey * r, ez + 0.06 * r) @ S(0.3 * es, 0.25 * es, 0.04 * r), BLACK)
        sc.add(SPH, M @ T(x, ey * r, ez + 0.02 * r) @ S(0.24 * es, 0.27 * es * op, 0.15 * es),
               eye_col or white, emissive=eye_col is not None)
        if eye_open > 0.3:
            ps = pupil[i]
            px = x + look[0] * 0.08 * r
            py = ey * r + look[1] * 0.08 * r
            if iris is not None:
                sc.add(SPH_LO, M @ T(px, py, ez + 0.12 * es) @ S(0.15 * es * ps, 0.15 * es * ps * eye_open, 0.05 * es), iris)
            sc.add(SPH_LO, M @ T(px, py, ez + 0.15 * es) @ S(0.09 * es * ps, 0.09 * es * ps * eye_open, 0.05 * es), BLACK)
        else:
            sc.add(BOX, M @ T(x, ey * r, ez + 0.17 * es) @ S(0.22 * es, 0.025 * r, 0.02 * r), BLACK)
        if brows is not None:
            sc.add(BOX, M @ T(x, (ey + 0.32) * r, ez - 0.02) @ Rz(brows * sx) @ S(0.22 * r, 0.04 * r, 0.04 * r), BLACK)
    if glasses:
        sc.add(BOX, M @ T(0, ey * r, ez + 0.1 * r) @ S(0.1 * r, 0.03 * r, 0.03 * r), BLACK)
    my = -0.3 * r
    mz = r * 0.9
    if mouth == "smile":
        sc.add(BOX, M @ T(0, my, mz) @ S(0.22 * r, 0.04 * r, 0.06 * r), DARK)
        for sx in (-1, 1):
            sc.add(BOX, M @ T(0.22 * r * sx, my + 0.05 * r, mz - 0.02 * r) @ Rz(0.6 * sx) @ S(0.07 * r, 0.035 * r, 0.05 * r), DARK)
    elif mouth == "line":
        sc.add(BOX, M @ T(0, my, mz) @ S(0.18 * r, 0.025 * r, 0.06 * r), DARK)
    elif mouth == "o":
        sc.add(SPH_LO, M @ T(0, my, mz) @ S(0.1 * r, 0.13 * r, 0.06 * r), DARK)
    elif mouth == "scream":
        sc.add(SPH, M @ T(0, my - 0.05 * r, mz - 0.03 * r) @ S(0.22 * r, 0.3 * r, 0.08 * r), DARK)
        sc.add(SPH_LO, M @ T(0, my - 0.22 * r, mz) @ S(0.12 * r, 0.06 * r, 0.06 * r), (220, 90, 110))
    elif mouth == "talk":
        sc.add(SPH_LO, M @ T(0, my, mz) @ S(0.18 * r, 0.1 * r, 0.06 * r), DARK)
    elif mouth == "snore":
        sc.add(SPH_LO, M @ T(0.05 * r, my, mz) @ S(0.08 * r, 0.06 * r, 0.06 * r), DARK)
        sc.add(SPH_LO, M @ T(0.1 * r, my - 0.18 * r, mz) @ S(0.05 * r, 0.14 * r, 0.05 * r), (120, 180, 255))
    elif mouth == "wobble":
        for k in range(4):
            sc.add(BOX, M @ T((-0.18 + 0.12 * k) * r, my + (0.04 if k % 2 else -0.04) * r, mz) @ Rz(0.7 if k % 2 else -0.7) @ S(0.08 * r, 0.03 * r, 0.05 * r), DARK)


def limbs(sc, M, arms, color, legs=True, hand_col=None, leg_len=0.7, r=1.0):
    hand_col = hand_col or color
    for sx, hand in zip((-1, 1), arms):
        a = transform_point(M, (0.92 * sx * r, -0.15 * r, 0))
        b = transform_point(M, hand)
        Mseg = seg(a, b, 0.07 * np.linalg.norm(M[:3, 0]))
        sc.add(CYL5, Mseg, color)
        sc.add(SPH_LO, T(*b) @ S(0.14 * np.linalg.norm(M[:3, 0])), hand_col)
    if legs:
        for sx in (-1, 1):
            a = transform_point(M, (0.4 * sx * r, -0.85 * r, 0))
            b = transform_point(M, (0.45 * sx * r, -0.85 * r - leg_len, 0))
            sc.add(CYL5, seg(a, b, 0.07 * np.linalg.norm(M[:3, 0])), color)
            sc.add(SPH_LO, T(*b) @ R(ry=0) @ S(0.18, 0.1, 0.25) @ S(np.linalg.norm(M[:3, 0])), BLACK)


DEFAULT_ARMS = ((-1.4, -0.7, 0.2), (1.4, -0.7, 0.2))


# ---------------------------------------------------------------- Früchte
def apple(sc, M, eye_open=1.0, look=(0, 0), mouth="smile", arms=DEFAULT_ARMS,
          legs=True, sweat=0.0, brows=None, eye_size=1.0, pupil=(1, 1)):
    red = (205, 30, 35)
    sc.add(SPH_HI, M @ S(1, 0.92, 1), red)
    sc.add(CYL5, M @ T(0.05, 1.05, 0) @ Rz(-0.25) @ S(0.06, 0.25, 0.06), BROWN)
    # Blatt steckt halb im Kopf (Clipping ist ein Feature)
    sc.add(SPH_LO, M @ T(0.32, 1.05, 0) @ Rz(-0.5) @ S(0.38, 0.06, 0.2), GREEN)
    face(sc, M, 1.0, eye_open, look, mouth, brows=brows, eye_size=eye_size, pupil=pupil)
    limbs(sc, M, arms, (120, 20, 25), legs)
    if sweat > 0:
        for k, (x, y) in enumerate(((0.85, 0.55), (-0.9, 0.4), (0.7, 0.85))):
            if k < sweat * 3:
                sc.add(SPH_LO, M @ T(x, y, 0.5) @ S(0.09, 0.14, 0.09), (120, 190, 255))


def orange(sc, M, eye_open=1.0, look=(0, 0), mouth="smile", arms=DEFAULT_ARMS):
    sc.add(SPH_HI, M, (240, 140, 20))
    sc.add(SPH_LO, M @ T(0, 1.0, 0) @ S(0.12, 0.06, 0.12), (70, 110, 30))
    face(sc, M, 1.0, eye_open, look, mouth)
    limbs(sc, M, arms, (190, 100, 10))


def pear(sc, M, eye_open=1.0, look=(0, 0), mouth="smile", arms=DEFAULT_ARMS):
    g = (170, 200, 60)
    sc.add(SPH_HI, M, g)
    sc.add(SPH, M @ T(0, 0.9, 0) @ S(0.62), g)
    sc.add(CYL5, M @ T(0, 1.55, 0) @ S(0.05, 0.2, 0.05), BROWN)
    face(sc, M, 1.0, eye_open, look, mouth)
    limbs(sc, M, arms, (120, 150, 40))


def grape(sc, M, eye_open=1.0, look=(0, 0), mouth="smile", arms=DEFAULT_ARMS):
    p = (110, 40, 140)
    for (x, y, z) in ((0, 0, 0), (0.5, 0.4, -0.2), (-0.5, 0.4, -0.2), (0, 0.7, -0.3),
                      (0.45, -0.3, -0.3), (-0.45, -0.3, -0.3)):
        sc.add(SPH, M @ T(x, y, z) @ S(0.62), p)
    sc.add(CYL5, M @ T(0, 1.2, -0.3) @ S(0.05, 0.25, 0.05), BROWN)
    face(sc, M @ S(0.7), 1.0, eye_open, look, mouth)
    limbs(sc, M, arms, (80, 30, 100))


def lemon(sc, M, eye_open=1.0, look=(0, 0), mouth="line", arms=DEFAULT_ARMS):
    y = (245, 225, 40)
    sc.add(SPH_HI, M @ S(1.15, 0.85, 0.9), y)
    for sx in (-1, 1):
        sc.add(CONE, M @ T(1.2 * sx, 0, 0) @ Rz(-sx * math.pi / 2) @ S(0.15, 0.2, 0.15), y)
    face(sc, M @ S(0.9), 1.0, eye_open, look, mouth, brows=0.4)
    limbs(sc, M, arms, (200, 180, 20))


FRUITS = {"apple": apple, "orange": orange, "pear": pear, "grape": grape, "lemon": lemon}


# ---------------------------------------------------------------- Herr Banane
def banana(sc, M, eye_open=1.0, look=(0, 0), mouth="line", arm_r=0.0,
           arm_l=0.0, brows=None, pointer=True, legs=True):
    yel = (250, 215, 50)
    tip = (90, 60, 20)
    Rr = 2.4
    angs = np.linspace(-0.68, 0.68, 8)
    pts = [np.array([Rr - Rr * math.cos(a) - 0.0, Rr * math.sin(a), 0]) for a in angs]
    rad = [0.13 + 0.42 * math.sqrt(max(0, 1 - (a / 0.72) ** 2)) for a in angs]
    for i in range(len(pts) - 1):
        a = transform_point(M, pts[i])
        b = transform_point(M, pts[i + 1])
        rr = (rad[i] + rad[i + 1]) / 2 * np.linalg.norm(M[:3, 0])
        sc.add(CYL5, seg(a, b, rr), yel)
        if 0 < i:
            sc.add(SPH_LO, T(*a) @ S(rad[i] * np.linalg.norm(M[:3, 0]) * 0.98), yel)
    for p, q in ((pts[0], pts[0] + np.array([0.15, -0.3, 0])), (pts[-1], pts[-1] + np.array([0.18, 0.32, 0]))):
        sc.add(CYL5, seg(transform_point(M, p), transform_point(M, q), 0.1 * np.linalg.norm(M[:3, 0])), tip)
    # brauner Fleck (Altersfleck, Herr Banane ist nicht mehr der Jüngste)
    sc.add(SPH_LO, M @ T(0.15, -0.65, 0.42) @ S(0.12, 0.09, 0.05), tip)
    # Gesicht
    FM = M @ T(0.05, 0.45, 0.0)
    face(sc, FM, 0.5, eye_open, look, mouth, ex=0.42, ey=0.25, eye_size=0.9,
         glasses=True, brows=brows)
    sc.add(BOX, FM @ T(0, -0.04, 0.47) @ S(0.2, 0.04, 0.05), (80, 50, 20))  # Schnurrbart
    # Krawatte
    sc.add(BOX, M @ T(0.02, -0.15, 0.5) @ Rz(0.05) @ S(0.08, 0.28, 0.03), (200, 30, 40))
    sc.add(BOX, M @ T(0.02, 0.15, 0.51) @ S(0.11, 0.06, 0.03), (160, 20, 30))
    # Arme
    sh_r = transform_point(M, (0.42, 0.0, 0))
    hand_r = transform_point(M, (0.42 + 0.9 * math.cos(arm_r), 0.0 + 0.9 * math.sin(arm_r), 0.25))
    sh_l = transform_point(M, (-0.38, 0.0, 0))
    hand_l = transform_point(M, (-0.38 - 0.85 * math.cos(arm_l), -0.6 + 0.6 * math.sin(arm_l) - 0.0, 0.2))
    s = np.linalg.norm(M[:3, 0])
    for a, b in ((sh_r, hand_r), (sh_l, hand_l)):
        sc.add(CYL5, seg(a, b, 0.06 * s), (200, 170, 40))
        sc.add(SPH_LO, T(*b) @ S(0.12 * s), WHITE)  # Handschuhe
    if pointer:
        d = hand_r - sh_r
        d /= np.linalg.norm(d)
        sc.add(CYL5, seg(hand_r, hand_r + d * 1.3 * s, 0.03 * s), (140, 90, 40))
    if legs:
        for sx in (-1, 1):
            a = transform_point(M, (0.35 + 0.18 * sx, -1.35, 0))
            b = transform_point(M, (0.35 + 0.22 * sx, -2.1, 0))
            sc.add(CYL5, seg(a, b, 0.06 * s), (200, 170, 40))
            sc.add(SPH_LO, T(*b) @ S(0.2 * s, 0.1 * s, 0.28 * s), BLACK)


# ---------------------------------------------------------------- Schafe
def sheep(sc, M, wool=WHITE, eye_size=1.0, pupil=(1, 1), look=(0, 0),
          tongue=False, leg_phase=0.0, iris=None, red_eyes=False, skin=(45, 40, 40),
          mouth=None, eye_open=1.0):
    puffs = [(0, 0, 0, 0.75), (0, 0.2, 0.55, 0.6), (0, 0.2, -0.55, 0.6),
             (0.45, 0.15, 0, 0.55), (-0.45, 0.15, 0, 0.55), (0, 0.55, 0, 0.55),
             (0.35, 0.4, 0.4, 0.45), (-0.35, 0.4, -0.4, 0.45), (0.35, 0.4, -0.4, 0.45),
             (-0.35, 0.4, 0.4, 0.45), (0, -0.25, 0, 0.6)]
    for x, y, z, r in puffs:
        sc.add(SPH_LO, M @ T(x, y, z) @ S(r), wool)
    for k, (x, z) in enumerate(((0.3, 0.45), (-0.3, 0.45), (0.3, -0.45), (-0.3, -0.45))):
        sw = math.sin(leg_phase + (k % 2) * math.pi) * 0.25
        a = transform_point(M, (x, -0.4, z))
        b = transform_point(M, (x, -1.15, z + sw))
        sc.add(CYL5, seg(a, b, 0.09 * np.linalg.norm(M[:3, 0])), skin)
    HM = M @ T(0, 0.45, 1.05)
    sc.add(SPH, HM @ S(0.36, 0.42, 0.42), skin)
    sc.add(SPH_LO, HM @ T(0, 0.38, -0.1) @ S(0.3, 0.18, 0.28), wool)  # Haartolle
    for sx in (-1, 1):
        sc.add(SPH_LO, HM @ T(0.42 * sx, 0.12, -0.1) @ Rz(0.5 * sx) @ S(0.22, 0.07, 0.12), skin)
    if red_eyes:
        for sx in (-1, 1):
            sc.add(SPH_LO, HM @ T(0.16 * sx, 0.12, 0.36) @ S(0.1 * eye_size, 0.06 * eye_size, 0.05),
                   (255, 30, 20), emissive=True)
    else:
        face(sc, HM @ S(0.45), 1.0, eye_open, look, mouth or "line", ex=0.38, ey=0.3,
             eye_size=eye_size, pupil=pupil, iris=iris)
    if tongue:
        sc.add(BOX, HM @ T(0.05, -0.28, 0.4) @ Rx(0.4) @ S(0.07, 0.14, 0.03), (240, 100, 130))


# ---------------------------------------------------------------- Kulissen
def desk(sc, x, z, top=1.1, w=1.0, d=0.6, col=(170, 120, 70)):
    sc.add(BOX, T(x, top, z) @ S(w, 0.06, d), col)
    for sx in (-1, 1):
        for sz in (-1, 1):
            sc.add(BOX, T(x + sx * (w - 0.08), top / 2, z + sz * (d - 0.08)) @ S(0.05, top / 2, 0.05), (90, 90, 95))


def tiles(sc, origin, u, v, nu, nv, color, layer=0, thick=0.05, checker=None):
    """Fläche aus vielen flachen Kisten (sonst verschwindet sie an der Near-Plane)."""
    o, u, v = (np.asarray(a, float) for a in (origin, u, v))
    du, dv = u / nu, v / nv
    nrm = np.cross(du, dv)
    nrm = nrm / np.linalg.norm(nrm) * thick
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2] = du / 2, dv / 2, nrm
    for i in range(nu):
        for j in range(nv):
            c = o + du * (i + 0.5) + dv * (j + 0.5)
            col = color if checker is None or (i + j) % 2 == 0 else checker
            sc.add(BOX, T(*c) @ m, col, layer=layer, jitter=0)


def classroom(sc, t, board_img, clock_speed=1.0):
    tiles(sc, (-8.2, 0, -5.6), (16.4, 0, 0), (0, 0, 16.6), 8, 8, (150, 105, 65), checker=(140, 98, 60))
    tiles(sc, (-8.2, 0, -5.6), (16.4, 0, 0), (0, 8, 0), 4, 2, (170, 200, 160))
    tiles(sc, (-8.2, 0, 11), (16.4, 0, 0), (0, 8, 0), 6, 3, (165, 195, 155))
    tiles(sc, (-8.2, 0, -5.6), (0, 0, 16.6), (0, 8, 0), 6, 3, (150, 185, 150))
    tiles(sc, (8.2, 0, -5.6), (0, 0, 16.6), (0, 8, 0), 6, 3, (150, 185, 150))
    tiles(sc, (-8.2, 8, -5.6), (16.4, 0, 0), (0, 0, 16.6), 6, 6, (215, 215, 205))
    # Tafel
    sc.add(BOX, T(-0.5, 3.4, -5.45) @ S(3.4, 1.35, 0.06), (100, 70, 40), layer=0.3)
    sc.quad([(-3.7, 4.6, -5.36), (2.7, 4.6, -5.36), (2.7, 2.2, -5.36), (-3.7, 2.2, -5.36)],
            board_img, layer=0.4)
    # Fenster
    sc.add(BOX, T(5.6, 3.6, -5.47) @ S(1.4, 1.2, 0.05), (230, 230, 235), layer=0.3)
    sc.add(BOX, T(5.6, 3.6, -5.42) @ S(1.25, 1.05, 0.05), (150, 210, 250), layer=0.35, emissive=True)
    sc.add(BOX, T(5.6, 3.6, -5.38) @ S(0.05, 1.05, 0.03), (230, 230, 235), layer=0.36)
    # Uhr (dreht viel zu schnell)
    sc.add(CYL, T(-5.5, 5.6, -5.45) @ Rx(math.pi / 2) @ S(0.6, 0.05, 0.6), WHITE, layer=0.3)
    for L, sp, wd in ((0.45, 6.0, 0.04), (0.3, 0.5, 0.06)):
        a = t * sp * clock_speed
        sc.add(BOX, T(-5.5 + math.sin(a) * L / 2, 5.6 + math.cos(a) * L / 2, -5.36) @ Rz(-a) @ S(wd, L / 2, 0.02),
               BLACK, layer=0.4)
    # Lehrerpult
    sc.add(BOX, T(3.5, 0.8, -3.6) @ S(1.4, 0.8, 0.6), (130, 85, 50))
    sc.add(SPH_LO, T(3.0, 1.75, -3.6) @ S(0.25), (200, 30, 30))  # Apfel für den Lehrer (Kevins Cousin)


def meadow(sc, t, n=6, size=2.0, hue0=0.3, wild=1.0):
    for i in range(-n, n):
        for j in range(-n, n + 2):
            h = hue0 + wild * 0.08 * math.sin(i * 0.9 + j * 0.7 + t * 3) + wild * ((i + j) % 2) * 0.05
            sc.add(BOX, T(i * size + size / 2, -0.1, j * size + size / 2) @ S(size / 2, 0.1, size / 2),
                   hsv(h + wild * t * 0.05, 0.55, 0.85), layer=0, jitter=0)


def fence(sc, x0, x1, z):
    for x in np.arange(x0, x1 + 0.01, 1.0):
        sc.add(BOX, T(x, 0.6, z) @ S(0.08, 0.6, 0.08), (180, 130, 80))
    for y in (0.5, 1.0):
        sc.add(BOX, T((x0 + x1) / 2, y, z + 0.05) @ S((x1 - x0) / 2 + 0.1, 0.06, 0.04), (200, 150, 95))


def mushroom(sc, x, z, s, t, hue):
    sc.add(CYL, T(x, s * 0.6, z) @ S(s * 0.25, s * 0.6, s * 0.25), (240, 230, 210))
    sc.add(SPH, T(x, s * 1.25, z) @ Ry(t) @ S(s * 0.8, s * 0.45, s * 0.8), hsv(hue, 0.8, 0.95))
    for k in range(4):
        a = k * 1.6 + t
        sc.add(SPH_LO, T(x + math.cos(a) * s * 0.5, s * 1.55, z + math.sin(a) * s * 0.5) @ S(s * 0.12), WHITE)


def bedroom(sc):
    tiles(sc, (-4.5, 0, -6), (9, 0, 0), (0, 0, 10.5), 6, 6, (40, 40, 60))
    tiles(sc, (-4.5, 0, -6), (9, 0, 0), (0, 6, 0), 4, 3, (45, 45, 70))
    tiles(sc, (-4.5, 0, 4.5), (9, 0, 0), (0, 6, 0), 4, 3, (45, 45, 70))
    tiles(sc, (-4.5, 0, -6), (0, 0, 10.5), (0, 6, 0), 5, 3, (38, 38, 62))
    tiles(sc, (4.5, 0, -6), (0, 0, 10.5), (0, 6, 0), 5, 3, (38, 38, 62))
    tiles(sc, (-4.5, 6, -6), (9, 0, 0), (0, 0, 10.5), 4, 4, (30, 30, 50))
    # Tür am Fußende (dunkel)
    sc.add(BOX, T(0, 1.6, -5.88) @ S(1.0, 1.65, 0.05), (90, 70, 60), layer=0.3)
    sc.add(BOX, T(0, 1.5, -5.82) @ S(0.85, 1.5, 0.05), (5, 5, 10), layer=0.4, emissive=True)
    # Bett
    sc.add(BOX, T(0, 0.45, 0) @ S(1.4, 0.45, 2.6), (90, 60, 50))
    sc.add(BOX, T(0, 1.0, 1.9) @ S(0.9, 0.18, 0.5), (200, 200, 220))  # Kissen
    sc.add(BOX, T(0, 1.2, -0.8) @ S(1.45, 0.45, 1.9), (70, 80, 150))  # Decke
    sc.add(BOX, T(0, 1.4, 2.7) @ S(1.5, 1.4, 0.1), (80, 55, 45))  # Kopfteil
