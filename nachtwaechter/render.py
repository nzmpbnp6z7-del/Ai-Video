# -*- coding: utf-8 -*-
"""Rendert "Die Regeln des Nachtwächters" als TikTok-Videos (1080x1920, 30 fps).

Alles wird prozedural erzeugt: Szenen (PIL), Sprache (espeak-ng + MBROLA),
Atmo/Soundeffekte (numpy). Aufruf:  python3 render.py [teil ...]
"""
import os, sys, math, hashlib, subprocess, wave, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import story

W, H, FPS, SR = 1080, 1920, 30, 44100
BW, BH = 1188, 2112          # Hintergrund 1.1x für Ken-Burns-Zoom
ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "output")
os.makedirs(BUILD, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

FD = "/usr/share/fonts/"
F_CAP = FD + "opentype/inter/Inter-ExtraBold.otf"
F_BOLD = FD + "opentype/inter/Inter-Bold.otf"
F_MONO = FD + "truetype/dejavu/DejaVuSansMono-Bold.ttf"
F_HAND = FD + "truetype/liberation/LiberationSerif-Italic.ttf"
F_HANDB = FD + "truetype/liberation/LiberationSerif-BoldItalic.ttf"
F_SERIF = FD + "truetype/dejavu/DejaVuSerif-Bold.ttf"


@lru_cache(None)
def font(path, size):
    return ImageFont.truetype(path, size)


def rng_for(*key):
    return random.Random(hashlib.md5(repr(key).encode()).hexdigest())


# =====================================================================
#  SZENEN
# =====================================================================
def add_glow(img, layer, radius, strength=1.0):
    g = layer.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1.0:
        g = Image.eval(g, lambda v: min(255, int(v * strength)))
    return ImageChops.add(ImageChops.add(img, g), layer)


def texture(img, amount=10, seed=1, blur=1.2):
    a = np.asarray(img).astype(np.int16)
    n = np.random.default_rng(seed).normal(0, amount, (img.size[1] // 2, img.size[0] // 2))
    n = np.asarray(Image.fromarray(np.clip(n + 128, 0, 255).astype(np.uint8)).resize(img.size, Image.BILINEAR)
                   .filter(ImageFilter.GaussianBlur(blur))).astype(np.int16) - 128
    return Image.fromarray(np.clip(a + n[..., None], 0, 255).astype(np.uint8))


def vgrad(size, top, bot):
    w, h = size
    t = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(top)[None, None] * (1 - t) + np.array(bot)[None, None] * t)
    return Image.fromarray(np.repeat(arr, w, axis=1).astype(np.uint8))


def radial(size, cx, cy, r, color, power=2.0):
    w, h = size
    y, x = np.mgrid[0:h, 0:w]
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** power
    return Image.fromarray((a[..., None] * np.array(color)[None, None]).astype(np.uint8))


def scene_corridor():
    img = Image.new("RGB", (BW, BH), (5, 7, 11))
    glow = Image.new("RGB", (BW, BH), 0)
    d, g = ImageDraw.Draw(img), ImageDraw.Draw(glow)
    vx, vy, k = BW / 2, BH * 0.43, 780
    FY, CY = 1.2, -1.25

    def P(x, y, z):
        return (vx + x * k / z, vy + y * k / z)

    def fog(z):
        return math.exp(-(z - 0.5) / 4.5)

    def sh(c, z, m=1.0):
        f = fog(z) * m
        return tuple(int(v * f) for v in c)

    zs = np.arange(14.0, 0.45, -0.25)
    for z0 in zs:
        z1 = z0 - 0.25
        tile = (int(z0 * 2) % 2)
        floor_c = (34, 38, 46) if tile else (28, 31, 38)
        d.polygon([P(-1, FY, z1), P(1, FY, z1), P(1, FY, z0), P(-1, FY, z0)], fill=sh(floor_c, z0))
        d.polygon([P(-1, CY, z1), P(1, CY, z1), P(1, CY, z0), P(-1, CY, z0)], fill=sh((22, 24, 30), z0))
        for s in (-1, 1):
            d.polygon([P(s, CY, z1), P(s, FY, z1), P(s, FY, z0), P(s, CY, z0)], fill=sh((30, 32, 40), z0))
    # Bodenfugen
    for x in np.arange(-1, 1.01, 0.25):
        d.line([P(x, FY, 0.5), P(x, FY, 14)], fill=(14, 16, 20), width=2)
    # Läden
    shops = [(1.0, 2.5), (2.8, 4.3), (4.6, 6.1), (6.4, 7.9), (8.2, 9.7), (10.0, 11.5)]
    signs = [(170, 40, 60), (40, 120, 170), (160, 120, 40), (60, 150, 90), (140, 60, 160), (170, 40, 60)]
    for side in (-1, 1):
        for i, (za, zb) in enumerate(shops):
            d.polygon([P(side, -0.25, za), P(side, FY, za), P(side, FY, zb), P(side, -0.25, zb)], fill=sh((16, 17, 22), za))
            for y in np.arange(-0.2, FY, 0.07):
                d.line([P(side, y, za), P(side, y, zb)], fill=sh((40, 42, 50), za), width=max(1, int(3 / za)))
            d.polygon([P(side, -0.55, za), P(side, -0.32, za), P(side, -0.32, zb), P(side, -0.55, zb)], fill=sh((12, 12, 16), za))
            if (i + side) % 3 != 0:
                c = signs[(i * 2 + (side > 0)) % len(signs)]
                poly = [P(side, -0.5, za + 0.3), P(side, -0.37, za + 0.3), P(side, -0.37, zb - 0.3), P(side, -0.5, zb - 0.3)]
                g.polygon(poly, fill=sh(c, za, 0.9))
            d.polygon([P(side, CY, zb), P(side, FY, zb), P(side, FY, zb + 0.3), P(side, CY, zb + 0.3)], fill=sh((44, 46, 54), zb))
    # Deckenlichter (einige aus)
    for i, z in enumerate(np.arange(1.3, 13, 1.5)):
        on = i not in (2, 5)
        col = (200, 215, 230) if on else (30, 32, 36)
        poly = [P(-0.18, CY + 0.01, z - 0.25), P(0.18, CY + 0.01, z - 0.25), P(0.18, CY + 0.01, z + 0.25), P(-0.18, CY + 0.01, z + 0.25)]
        (g if on else d).polygon(poly, fill=sh(col, z, 1.2))
        if on:
            x0, y0 = P(-0.2, FY, z)
            x1, y1 = P(0.2, FY, z + 0.6)
            g.ellipse([x0, y1 - 4, x1, y0 + 4], fill=sh((26, 28, 34), z))
    # Notausgang hinten
    ex, ey = P(0, -0.8, 13.5)
    g.rectangle([ex - 26, ey - 10, ex + 26, ey + 10], fill=(40, 200, 90))
    img = add_glow(img, glow, 28, 1.1)
    img = Image.blend(img, ImageChops.multiply(img, Image.new("RGB", img.size, (200, 220, 255))), 0.5)
    return texture(img, 9, 3)


def draw_radio(d, glow, x, y, w, h):
    gd = ImageDraw.Draw(glow)
    d.rounded_rectangle([x, y, x + w, y + h], 18, fill=(48, 36, 28), outline=(20, 14, 10), width=5)
    d.rounded_rectangle([x + 20, y + 20, x + w * 0.55, y + h - 20], 12, fill=(26, 20, 16))
    for gx in range(int(x + 40), int(x + w * 0.55 - 10), 22):
        for gy in range(int(y + 40), int(y + h - 30), 22):
            d.ellipse([gx, gy, gx + 9, gy + 9], fill=(8, 6, 5))
    dx = x + w * 0.6
    gd.rounded_rectangle([dx, y + 30, x + w - 25, y + 95], 8, fill=(190, 110, 30))
    d.rounded_rectangle([dx, y + 30, x + w - 25, y + 95], 8, outline=(20, 14, 10), width=3)
    for t in range(int(dx + 10), int(x + w - 30), 16):
        d.line([t, y + 40, t, y + 55], fill=(60, 30, 10), width=2)
    d.line([dx + (x + w - dx) * 0.45, y + 34, dx + (x + w - dx) * 0.45, y + 92], fill=(160, 20, 10), width=4)
    for i, kx in enumerate((dx + 40, x + w - 80)):
        d.ellipse([kx - 34, y + h - 110, kx + 34, y + h - 42], fill=(70, 60, 52), outline=(15, 10, 8), width=4)
        d.line([kx, y + h - 76, kx + 20 * (1 if i else -0.4), y + h - 100], fill=(15, 10, 8), width=5)
    d.line([x + w - 40, y, x + w + 120, y - 330], fill=(120, 120, 125), width=5)


def scene_office():
    img = vgrad((BW, BH), (14, 18, 18), (6, 8, 8))
    glow = Image.new("RGB", (BW, BH), 0)
    d, g = ImageDraw.Draw(img), ImageDraw.Draw(glow)
    # Monitorwand
    rng = np.random.default_rng(7)
    for r in range(2):
        for c in range(2):
            x0, y0 = 150 + c * 455, 360 + r * 330
            d.rectangle([x0 - 14, y0 - 14, x0 + 430, y0 + 300], fill=(10, 10, 10))
            n = rng.normal(0, 1, (75, 108))
            n = (np.clip(n * 18 + 70 + np.linspace(-20, 20, 108)[None], 0, 255)).astype(np.uint8)
            scr = Image.fromarray(n).resize((416, 286), Image.BILINEAR).filter(ImageFilter.GaussianBlur(1.4))
            scr = Image.merge("RGB", (Image.eval(scr, lambda v: int(v * 0.55)), scr, Image.eval(scr, lambda v: int(v * 0.7))))
            sd = ImageDraw.Draw(scr)
            sd.text((12, 10), f"CAM 0{r * 2 + c + 2}", font=font(F_MONO, 22), fill=(220, 255, 220))
            if (r, c) == (1, 0):
                sd.rectangle([180, 90, 236, 260], fill=(20, 30, 22))
                sd.text((160, 60), "LAGER 3", font=font(F_MONO, 20), fill=(200, 230, 200))
            glow.paste(Image.eval(scr, lambda v: int(v * 0.35)), (x0 + 7, y0 + 7))
            img.paste(scr, (x0 + 7, y0 + 7))
    # Tisch
    d.polygon([(-50, 1480), (BW + 50, 1480), (BW + 300, BH), (-300, BH)], fill=(46, 32, 22))
    for i in range(14):
        yy = 1500 + i * 45
        d.line([(-300, yy), (BW + 300, yy + rng.integers(-15, 15))], fill=(38, 26, 18), width=3)
    d.rectangle([-50, 1460, BW + 50, 1490], fill=(30, 20, 14))
    draw_radio(d, glow, 110, 1180, 430, 330)
    # Telefon
    d.rounded_rectangle([700, 1300, 1040, 1520], 40, fill=(140, 20, 20), outline=(40, 5, 5), width=5)
    d.rounded_rectangle([680, 1230, 1060, 1320], 40, fill=(160, 26, 24), outline=(40, 5, 5), width=5)
    for i in range(3):
        for j in range(3):
            d.ellipse([790 + j * 55, 1345 + i * 50, 822 + j * 55, 1375 + i * 50], fill=(225, 215, 200))
    # Zettel
    paper = Image.new("RGBA", (360, 260), (235, 228, 205, 255))
    pd = ImageDraw.Draw(paper)
    for i in range(7):
        pd.line([(30, 50 + i * 28), (30 + rng.integers(180, 300), 50 + i * 28)], fill=(40, 40, 60, 255), width=4)
    pd.text((30, 12), "REGELN", font=font(F_HANDB, 30), fill=(20, 20, 40, 255))
    paper = paper.rotate(-8, expand=True, resample=Image.BICUBIC)
    img.paste(paper, (420, 1620), paper)
    # Lampe
    lamp = radial((BW, BH), 620, 1700, 650, (120, 95, 60), 1.6)
    img = ImageChops.add(img, lamp)
    img = add_glow(img, glow, 40, 0.8)
    return texture(img, 8, 4)


def scene_door(num="3"):
    img = vgrad((BW, BH), (32, 33, 34), (16, 17, 18))
    glow = Image.new("RGB", (BW, BH), 0)
    d, g = ImageDraw.Draw(img), ImageDraw.Draw(glow)
    rng = np.random.default_rng(11)
    for i in range(40):
        y = rng.integers(0, 1700)
        d.line([(0, y), (BW, y)], fill=(28, 29, 30), width=2)
    d.polygon([(0, 1720), (BW, 1720), (BW, BH), (0, BH)], fill=(20, 21, 22))
    for i in range(8):
        d.line([(BW / 2 + (i - 3.5) * 120, 1720), (BW / 2 + (i - 3.5) * 520, BH)], fill=(14, 15, 16), width=3)
    x0, y0, x1, y1 = 300, 560, 890, 1720
    d.rectangle([x0 - 30, y0 - 30, x1 + 30, y1], fill=(12, 12, 13))
    door = vgrad((x1 - x0, y1 - y0 - 12), (78, 84, 88) if num == "3" else (70, 52, 40), (44, 46, 50) if num == "3" else (34, 24, 18))
    img.paste(door, (x0, y0))
    d.rectangle([x0, y0, x1, y1 - 12], outline=(20, 20, 22), width=4)
    for yy in (y0 + 200, y1 - 260):
        d.line([(x0 + 30, yy), (x1 - 30, yy)], fill=(36, 38, 40), width=3)
    d.rounded_rectangle([x1 - 110, y0 + 560, x1 - 40, y0 + 590], 10, fill=(150, 150, 150))
    d.rectangle([x1 - 92, y0 + 590, x1 - 62, y0 + 650], fill=(70, 70, 70))
    if num == "4":
        for i in range(25):
            cx, cy = rng.integers(x0, x1), rng.integers(y0, y1)
            d.ellipse([cx, cy, cx + rng.integers(10, 60), cy + rng.integers(10, 90)], fill=(80, 40, 20))
        for i in range(5):
            xs = rng.integers(x0 + 40, x1 - 40)
            d.line([(xs, y0 + 600), (xs + rng.integers(-30, 30), y1 - 20)], fill=(60, 20, 14), width=4)
    # Schild
    d.rectangle([BW / 2 - 170, y0 + 90, BW / 2 + 170, y0 + 210], fill=(225, 225, 215) if num == "3" else (150, 140, 120), outline=(20, 20, 20), width=5)
    t = f"LAGER {num}"
    tw = d.textlength(t, font=font(F_BOLD, 74))
    d.text((BW / 2 - tw / 2, y0 + 105), t, font=font(F_BOLD, 74), fill=(20, 20, 20))
    # Licht unter der Tür
    lc = (255, 170, 80) if num == "3" else (255, 40, 30)
    g.rectangle([x0 + 10, y1 - 14, x1 - 10, y1 - 4], fill=lc)
    g.polygon([(x0, y1), (x1, y1), (x1 + 160, BH), (x0 - 160, BH)], fill=tuple(int(c * 0.12) for c in lc))
    # Käfiglampe
    g.ellipse([BW / 2 - 28, 360, BW / 2 + 28, 420], fill=(200, 200, 170))
    img = ImageChops.add(img, radial((BW, BH), BW / 2, 390, 700, (60, 60, 50), 1.8))
    d = ImageDraw.Draw(img)
    for i in range(5):
        d.line([(BW / 2 - 34 + i * 17, 350), (BW / 2 - 34 + i * 17, 430)], fill=(30, 30, 30), width=3)
    img = add_glow(img, glow, 34, 1.2)
    img = ImageChops.multiply(img, radial((BW, BH), BW / 2, BH * 0.45, 1300, (255, 255, 255), 0.6))
    return texture(img, 11, 12)


def mannequin(d, cx, base, s, facing, col=(196, 186, 172)):
    hr = 52 * s
    hy = base - 760 * s
    dark = tuple(int(c * 0.55) for c in col)
    d.rectangle([cx - 8 * s, hy, cx + 8 * s, base], fill=(40, 40, 42))
    d.ellipse([cx - 90 * s, base - 14 * s, cx + 90 * s, base + 14 * s], fill=(30, 30, 32))
    d.polygon([(cx - 110 * s, hy + 110 * s), (cx + 110 * s, hy + 110 * s), (cx + 70 * s, hy + 420 * s), (cx - 70 * s, hy + 420 * s)], fill=col)
    d.polygon([(cx - 70 * s, hy + 420 * s), (cx + 70 * s, hy + 420 * s), (cx + 80 * s, hy + 540 * s), (cx - 80 * s, hy + 540 * s)], fill=dark)
    for sgn in (-1, 1):
        d.line([(cx + sgn * 105 * s, hy + 120 * s), (cx + sgn * 135 * s, hy + 460 * s)], fill=col, width=int(34 * s))
    d.rectangle([cx - 18 * s, hy + 60 * s, cx + 18 * s, hy + 115 * s], fill=col)
    d.ellipse([cx - hr * 0.85, hy - hr, cx + hr * 0.85, hy + hr], fill=col)
    if facing:
        for sgn in (-1, 1):
            d.ellipse([cx + sgn * 26 * s - 13 * s, hy - 14 * s, cx + sgn * 26 * s + 13 * s, hy + 12 * s], fill=(10, 8, 8))
        d.line([(cx - 16 * s, hy + 34 * s), (cx + 16 * s, hy + 30 * s)], fill=(70, 50, 50), width=int(4 * s))
    else:
        d.ellipse([cx - hr * 0.5, hy - hr * 0.7, cx + hr * 0.2, hy + hr * 0.3], fill=tuple(min(255, c + 14) for c in col))


def scene_mannequins(turned=False):
    img = vgrad((BW, BH), (10, 10, 14), (4, 4, 6))
    glow = Image.new("RGB", (BW, BH), 0)
    d, g = ImageDraw.Draw(img), ImageDraw.Draw(glow)
    d.rectangle([60, 300, BW - 60, 1760], fill=(8, 8, 10))
    inner = vgrad((BW - 160, 1360), (26, 22, 28), (12, 10, 14))
    img.paste(inner, (80, 380))
    d.polygon([(80, 1500), (BW - 80, 1500), (BW - 80, 1740), (80, 1740)], fill=(22, 18, 22))
    d.rectangle([80, 380, BW - 80, 1500], outline=(16, 14, 18), width=3)
    for i in range(3):
        d.line([(80, 600 + i * 300), (BW - 80, 600 + i * 300)], fill=(20, 18, 22), width=2)
    # Schild
    d.rectangle([60, 180, BW - 60, 300], fill=(14, 12, 16))
    t = "MODE KESSLER"
    tw = d.textlength(t, font=font(F_SERIF, 78))
    g.text((BW / 2 - tw / 2, 196), t, font=font(F_SERIF, 78), fill=(150, 40, 90) if not turned else (110, 25, 60))
    spots = [(300, 1640, 0.82, False), (594, 1660, 0.9, turned), (890, 1640, 0.82, False)]
    beam_x = 594
    img = ImageChops.add(img, radial((BW, BH), beam_x, 1050, 560, (120, 112, 96) if not turned else (150, 140, 120), 1.4))
    d = ImageDraw.Draw(img)
    for cx, base, s, f in spots:
        mannequin(d, cx, base, s, f)
    img = ImageChops.multiply(img, Image.fromarray(np.clip(
        np.asarray(radial((BW, BH), beam_x, 1050, 760, (255, 255, 255), 0.8)).astype(np.int16) + 70, 0, 255).astype(np.uint8)))
    # Glasreflexe
    refl = Image.new("RGB", (BW, BH), 0)
    rd = ImageDraw.Draw(refl)
    for x in (150, 230, 720, 790):
        rd.polygon([(x, 380), (x + 60, 380), (x - 240, 1500), (x - 300, 1500)], fill=(22, 24, 30))
    img = ImageChops.add(img, refl.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(img)
    for x in (60, BW / 2 - 6, BW - 72):
        d.rectangle([x, 300, x + 12, 1760], fill=(30, 30, 34))
    img = add_glow(img, glow, 26, 1.3)
    return texture(img, 10, 21 + turned)


def scene_phone():
    img = vgrad((BW, BH), (10, 12, 12), (4, 5, 5))
    glow = Image.new("RGB", (BW, BH), 0)
    d, g = ImageDraw.Draw(img), ImageDraw.Draw(glow)
    d.polygon([(-200, 1100), (BW + 200, 1100), (BW + 600, BH), (-600, BH)], fill=(42, 29, 20))
    rng = np.random.default_rng(5)
    for i in range(18):
        yy = 1120 + i * 55
        d.line([(-600, yy), (BW + 600, yy + rng.integers(-20, 20))], fill=(34, 23, 16), width=3)
    img = ImageChops.add(img, radial((BW, BH), 560, 1400, 800, (90, 66, 42), 1.5))
    d = ImageDraw.Draw(img)
    # Telefon groß
    cx = 560
    d.rounded_rectangle([cx - 360, 1180, cx + 360, 1700], 90, fill=(120, 16, 16), outline=(30, 4, 4), width=8)
    d.rounded_rectangle([cx - 400, 1030, cx + 400, 1200], 80, fill=(150, 22, 20), outline=(30, 4, 4), width=8)
    d.rounded_rectangle([cx - 420, 1000, cx - 230, 1220], 70, fill=(160, 26, 24), outline=(30, 4, 4), width=8)
    d.rounded_rectangle([cx + 230, 1000, cx + 420, 1220], 70, fill=(160, 26, 24), outline=(30, 4, 4), width=8)
    g.rounded_rectangle([cx - 300, 1050, cx + 260, 1080], 12, fill=(60, 30, 26))
    d.ellipse([cx - 220, 1260, cx + 220, 1660], fill=(100, 12, 12), outline=(30, 4, 4), width=6)
    for i in range(10):
        a = -math.pi * 0.75 + i * (math.pi * 1.5 / 9)
        x, y = cx + math.cos(a) * 150, 1460 + math.sin(a) * 150
        d.ellipse([x - 32, y - 32, x + 32, y + 32], fill=(225, 215, 200), outline=(60, 10, 10), width=4)
        d.text((x - 10, y - 18), str((i + 1) % 10), font=font(F_BOLD, 30), fill=(40, 10, 10))
    d.ellipse([cx - 60, 1400, cx + 60, 1520], fill=(225, 215, 200))
    # Wecker 03:33
    d.rounded_rectangle([110, 520, 980, 860], 30, fill=(14, 14, 16), outline=(40, 40, 44), width=6)
    t = "03:33"
    tw = d.textlength(t, font=font(F_MONO, 230))
    g.text((BW / 2 - tw / 2 - 50, 540), t, font=font(F_MONO, 230), fill=(255, 30, 20))
    img = add_glow(img, glow, 30, 1.4)
    return texture(img, 9, 31)


def scene_entrance(man=False):
    img = vgrad((BW, BH), (6, 10, 22), (2, 3, 6))
    glow = Image.new("RGB", (BW, BH), 0)
    d, g = ImageDraw.Draw(img), ImageDraw.Draw(glow)
    # Außen: Parkplatz
    d.rectangle([160, 500, BW - 160, 1650], fill=(10, 16, 32))
    d.polygon([(160, 1250), (BW - 160, 1250), (BW - 160, 1650), (160, 1650)], fill=(14, 16, 22))
    for lx, ly, s in ((300, 1000, 1.0), (800, 1060, 0.7), (520, 1110, 0.5), (960, 980, 1.1)):
        d.line([(lx, ly), (lx, 1250 + 20 * s)], fill=(30, 30, 36), width=int(8 * s))
        g.ellipse([lx - 18 * s, ly - 12 * s, lx + 18 * s, ly + 12 * s], fill=(255, 150, 60))
        g.ellipse([lx - 90 * s, 1240, lx + 90 * s, 1265], fill=(50, 28, 12))
    img = add_glow(img, glow, 30, 1.2)
    glow = Image.new("RGB", (BW, BH), 0)
    d, g = ImageDraw.Draw(img), ImageDraw.Draw(glow)
    if man:
        cx, base = 600, 1600
        sil = (3, 3, 5)
        d.ellipse([cx - 60, 860, cx + 60, 1000], fill=sil)
        d.polygon([(cx - 85, 880), (cx + 85, 880), (cx + 110, 860), (cx - 110, 860)], fill=sil)
        d.rectangle([cx - 80, 840, cx + 80, 880], fill=sil)
        d.polygon([(cx - 150, 1020), (cx + 150, 1020), (cx + 120, 1330), (cx - 120, 1330)], fill=sil)
        d.rectangle([cx - 30, 990, cx + 30, 1030], fill=sil)
        d.polygon([(cx - 120, 1330), (cx + 120, 1330), (cx + 100, base), (cx + 20, base), (cx, 1400), (cx - 20, base), (cx - 100, base)], fill=sil)
        d.line([(cx - 140, 1030), (cx - 175, 1330)], fill=sil, width=55)
        d.line([(cx + 140, 1030), (cx + 230, 1180)], fill=sil, width=55)
        g.ellipse([cx - 38, 925, cx - 20, 937], fill=(170, 170, 150))
        g.ellipse([cx + 20, 925, cx + 38, 937], fill=(170, 170, 150))
        # Taschenlampe
        img = ImageChops.add(img, radial((BW, BH), cx + 240, 1185, 900, (190, 190, 170), 2.4))
        d = ImageDraw.Draw(img)
        g.ellipse([cx + 210, 1155, cx + 270, 1215], fill=(255, 255, 240))
        for a in range(0, 360, 30):
            r = math.radians(a)
            g.line([(cx + 240, 1185), (cx + 240 + math.cos(r) * 260, 1185 + math.sin(r) * 260)], fill=(70, 70, 60), width=3)
    # Türrahmen innen
    fc = (40, 44, 52)
    d.rectangle([140, 480, BW - 140, 520], fill=fc)
    d.rectangle([140, 1640, BW - 140, 1680], fill=fc)
    for x in (140, BW / 2 - 14, BW - 168):
        d.rectangle([x, 480, x + 28, 1680], fill=fc)
    for x in (360, 820):
        d.rounded_rectangle([x, 1050, x + 18, 1200], 8, fill=(90, 94, 100))
    d.rectangle([0, 0, BW, 480], fill=(12, 13, 16))
    d.rectangle([0, 0, 140, BH], fill=(14, 15, 18))
    d.rectangle([BW - 140, 0, BW, BH], fill=(14, 15, 18))
    t = "HAUPTEINGANG"
    tw = d.textlength(t, font=font(F_BOLD, 54))
    g.text((BW / 2 - tw / 2, 390), t, font=font(F_BOLD, 54), fill=(120, 130, 150))
    d.polygon([(0, 1680), (BW, 1680), (BW, BH), (0, BH)], fill=(22, 24, 28))
    for i in range(9):
        d.line([(BW / 2 + (i - 4) * 130, 1680), (BW / 2 + (i - 4) * 520, BH)], fill=(16, 17, 20), width=3)
    # Glasreflex
    refl = Image.new("RGB", (BW, BH), 0)
    rd = ImageDraw.Draw(refl)
    for x in (380, 470, 880):
        rd.polygon([(x, 520), (x + 50, 520), (x - 200, 1640), (x - 250, 1640)], fill=(18, 22, 30))
    img = ImageChops.add(img, refl.filter(ImageFilter.GaussianBlur(10)))
    img = add_glow(img, glow, 22, 1.3)
    return texture(img, 9, 41 + man)


# ------------------------------------------------------------- Zettel
def wrap(text, fnt, maxw, draw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if draw.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def make_note(reveal, hl=None, final=False):
    pw = 960
    fnt = font(F_HAND, 39)
    fnum = font(F_HANDB, 41)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    lh = 47
    blocks = []
    for i, (txt, _) in enumerate(story.RULES):
        blocks.append(wrap(txt, fnt, pw - 150, tmp))
    y_start = 200
    total = y_start + sum(len(b) * lh + 18 for b in blocks) + 60
    r8 = wrap(story.RULE8, font(F_HANDB, 42), pw - 110, tmp)
    if final:
        total += len(r8) * 52 + 40
    ph = total
    paper = Image.new("RGBA", (pw, ph), (236, 229, 207, 255))
    arr = np.asarray(paper).astype(np.int16)
    n = np.random.default_rng(99).normal(0, 6, (ph, pw))
    arr[..., :3] = np.clip(arr[..., :3] + n[..., None], 0, 255)
    yy = np.linspace(-1, 1, ph)[:, None]
    xx = np.linspace(-1, 1, pw)[None]
    edge = np.clip(1 - 0.18 * (xx ** 6 + yy ** 6), 0, 1)
    arr[..., :3] = (arr[..., :3] * edge[..., None]).astype(np.int16)
    paper = Image.fromarray(arr.astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(paper)
    for y in range(y_start - 10, ph - 30, lh):
        d.line([(40, y + 44), (pw - 40, y + 44)], fill=(170, 185, 205, 255), width=1)
    d.line([(95, 0), (95, ph)], fill=(210, 140, 140, 255), width=2)
    stain = Image.new("RGBA", paper.size, 0)
    ImageDraw.Draw(stain).ellipse([pw - 210, 12, pw - 40, 182], outline=(150, 110, 60, 55), width=12)  # Kaffeefleck
    paper = Image.alpha_composite(paper, stain)
    d = ImageDraw.Draw(paper)
    ink = (24, 30, 70, 255)
    d.text((120, 40), "REGELN FÜR DEN NACHTDIENST", font=font(F_HANDB, 48), fill=ink)
    d.text((120, 108), "EKZ Lindenhof – unbedingt einhalten!", font=font(F_HAND, 36), fill=(120, 20, 20, 255))
    y = y_start
    for i, lines in enumerate(blocks):
        hgt = len(lines) * lh
        if i < reveal:
            if hl is not None and i == hl:
                mark = Image.new("RGBA", paper.size, 0)
                ImageDraw.Draw(mark).rectangle([105, y - 2, pw - 40, y + hgt + 6], fill=(255, 225, 40, 140))
                paper = Image.alpha_composite(paper, mark)
                d = ImageDraw.Draw(paper)
            col = ink if (hl is None or i == hl) else (24, 30, 70, 120)
            d.text((50, y - 1), f"{i + 1}.", font=fnum, fill=col)
            for j, ln in enumerate(lines):
                d.text((120, y + j * lh), ln, font=fnt, fill=col)
            if hl is not None and i == hl:
                d.ellipse([28, y - 12, 100, y + 56], outline=(200, 20, 20, 255), width=5)
        y += hgt + 18
    if final:
        y += 20
        for j, ln in enumerate(r8):
            d.text((60, y + j * 52), ln, font=font(F_HANDB, 42), fill=(150, 10, 10, 255))
    paper = paper.rotate(1.2, expand=True, resample=Image.BICUBIC)
    return paper


def scene_note(reveal, hl=None, final=False):
    bg = get_scene("office").filter(ImageFilter.GaussianBlur(12))
    bg = Image.eval(bg, lambda v: int(v * 0.45))
    paper = make_note(reveal, hl, final)
    maxh = 1400
    if paper.size[1] > maxh:
        s = maxh / paper.size[1]
        paper = paper.resize((int(paper.size[0] * s), maxh), Image.LANCZOS)
    shadow = Image.new("RGBA", (paper.size[0] + 80, paper.size[1] + 80), 0)
    shadow.paste((0, 0, 0, 200), (40, 50), paper.split()[3])
    shadow = shadow.filter(ImageFilter.GaussianBlur(20))
    x = (BW - paper.size[0]) // 2
    y = 180
    bg.paste(shadow, (x - 40, y - 30), shadow)
    bg.paste(paper, (x, y), paper)
    lamp = radial((BW, BH), BW / 2, y + 500, 1100, (255, 245, 225), 0.7)
    bg = ImageChops.multiply(bg, Image.fromarray(np.clip(np.asarray(lamp).astype(np.int16) + 60, 0, 255).astype(np.uint8)))
    return bg


_SC = {}


def get_scene(name):
    if name in _SC:
        return _SC[name]
    if name == "corridor":
        im = scene_corridor()
    elif name == "office":
        im = scene_office()
    elif name == "door3":
        im = scene_door("3")
    elif name == "door4":
        im = scene_door("4")
    elif name == "mann_n":
        im = scene_mannequins(False)
    elif name == "mann_t":
        im = scene_mannequins(True)
    elif name == "phone":
        im = scene_phone()
    elif name == "entrance":
        im = scene_entrance(False)
    elif name == "entrance_man":
        im = scene_entrance(True)
    elif name == "note_final":
        im = scene_note(7, None, True)
    elif name.startswith("note:"):
        p = name.split(":")
        im = scene_note(int(p[1]), int(p[2]) if len(p) > 2 else None)
    else:
        raise ValueError(name)
    _SC[name] = im
    return im


CAMS = {"corridor": ("CAM 02", "EG – PASSAGE"), "office": ("CAM 01", "WACHRAUM"), "phone": ("CAM 01", "WACHRAUM"),
        "door3": ("CAM 07", "LAGER 3"), "door4": ("CAM ??", "LAGER 4"), "mann_n": ("CAM 04", "1. OG – MODE KESSLER"),
        "mann_t": ("CAM 04", "1. OG – MODE KESSLER"), "entrance": ("CAM 03", "HAUPTEINGANG"),
        "entrance_man": ("CAM 03", "HAUPTEINGANG")}


# =====================================================================
#  AUDIO
# =====================================================================
def fft_filter(x, lo=None, hi=None):
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    m = np.ones_like(f)
    if lo:
        m *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** 4)
    if hi:
        m *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * m, n)


def reverb(x, t60=1.8, wet=0.35, seed=0):
    n = int(SR * t60)
    t = np.arange(n) / SR
    ir = np.random.default_rng(seed).normal(0, 1, n) * np.exp(-6.9 * t / t60)
    ir = fft_filter(ir, 120, 5000)
    ir /= np.sqrt((ir ** 2).sum())
    L = len(x) + n
    nf = 1 << (L - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, nf) * np.fft.rfft(ir, nf), nf)[:L]
    out = np.zeros(L)
    out[:len(x)] = x * (1 - wet)
    return out + y * wet


def tsec(d):
    return np.arange(int(d * SR)) / SR


def sfx(name):
    r = np.random.default_rng(abs(hash(name)) % 1000)
    if name in ("footsteps", "footsteps_slow"):
        gap = 0.62 if name == "footsteps" else 1.0
        n_steps = 6 if name == "footsteps" else 4
        out = np.zeros(int(SR * (gap * n_steps + 1)))
        for i in range(n_steps):
            s = int(i * gap * SR)
            b = r.normal(0, 1, int(0.09 * SR)) * np.exp(-np.arange(int(0.09 * SR)) / (0.018 * SR))
            b = fft_filter(b, 60, 1400) * (0.9 if i % 2 else 0.7)
            out[s:s + len(b)] += b
        return reverb(out * 0.9, 1.6, 0.45)
    if name == "paper":
        out = np.zeros(int(SR * 1.2))
        for i in range(14):
            s = int(r.uniform(0, 1.0) * SR)
            b = r.normal(0, 1, int(0.05 * SR)) * np.exp(-np.arange(int(0.05 * SR)) / (0.012 * SR))
            out[s:s + len(b)] += b * r.uniform(0.2, 0.6)
        return fft_filter(out, 1800, 9000) * 0.8
    if name == "sting":
        t = tsec(4.0)
        boom = np.sin(2 * np.pi * (55 * t - 6 * t ** 2)) * np.exp(-t / 1.1)
        cl = sum(np.sin(2 * np.pi * f * t + p) for f, p in ((1870, 0), (1990, 1), (2120, 2), (2390, 3)))
        cl *= np.clip(t / 0.05, 0, 1) * np.exp(-t / 1.2) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t)) * 0.12
        hit = r.normal(0, 1, len(t)) * np.exp(-t / 0.08) * 0.5
        return reverb(boom * 0.9 + cl + fft_filter(hit, 40, 2000), 3.0, 0.5)
    if name == "thud":
        t = tsec(1.5)
        x = np.sin(2 * np.pi * 70 * t * (1 - 0.3 * t)) * np.exp(-t / 0.15) + fft_filter(r.normal(0, 1, len(t)) * np.exp(-t / 0.06), 30, 900) * 0.8
        clatter = np.zeros(len(t))
        for i in range(5):
            s = int((0.12 + i * 0.09 + r.uniform(0, 0.04)) * SR)
            b = r.normal(0, 1, 2000) * np.exp(-np.arange(2000) / 300)
            clatter[s:s + 2000] += fft_filter(b, 800, 6000) * 0.3 / (i + 1)
        return reverb(x + clatter, 2.6, 0.55)
    if name == "ring":
        t = tsec(1.3)
        tone = (np.sin(2 * np.pi * 820 * t) + 0.7 * np.sin(2 * np.pi * 1230 * t) + 0.3 * np.sin(2 * np.pi * 2460 * t))
        am = (np.sin(2 * np.pi * 22 * t) > 0).astype(float)
        env = np.clip(t / 0.01, 0, 1) * np.clip((1.3 - t) / 0.05, 0, 1)
        one = tone * am * env * 0.28
        out = np.zeros(int(SR * 4.5))
        for k in range(2):
            s = int(k * 2.4 * SR)
            out[s:s + len(one)] += one[:len(out) - s]
        return reverb(out, 1.0, 0.3)
    if name == "door":
        t = tsec(2.2)
        sw = fft_filter(r.normal(0, 1, len(t)), 200, 1800) * np.sin(np.pi * t / 2.2) ** 2 * 0.25
        motor = np.sin(2 * np.pi * 110 * t) * 0.08 * np.sin(np.pi * t / 2.2)
        clunk = np.zeros(len(t))
        b = r.normal(0, 1, 4000) * np.exp(-np.arange(4000) / 600)
        clunk[int(1.9 * SR):int(1.9 * SR) + 4000] = fft_filter(b, 80, 1500) * 0.6
        return reverb(sw + motor + clunk, 1.4, 0.35)
    if name == "whoosh":
        t = tsec(0.5)
        x = r.normal(0, 1, len(t)) * np.sin(np.pi * t / 0.5) ** 2
        return fft_filter(x, 300, 3000) * 0.18
    if name == "glitch":
        t = tsec(0.18)
        x = r.normal(0, 1, len(t)) * 0.25 + 0.2 * np.sign(np.sin(2 * np.pi * 180 * t))
        return fft_filter(x, 300, 6000) * np.exp(-t / 0.1)
    if name == "tick":
        t = tsec(0.06)
        return np.sin(2 * np.pi * 1600 * t) * np.exp(-t / 0.008) * 0.35
    if name == "heart":
        t = tsec(0.9)
        b = lambda s: np.sin(2 * np.pi * 48 * (t - s)) * np.exp(-np.clip(t - s, 0, None) / 0.07) * (t >= s)
        return (b(0) + 0.7 * b(0.28)) * 0.7
    if name == "bell":
        t = tsec(3)
        return reverb(sum(np.sin(2 * np.pi * f * t) * a for f, a in ((392, 1), (784, .4), (1176, .2))) * np.exp(-t / 0.8) * 0.2, 2, 0.4)
    raise ValueError(name)


def ambience(dur, seed):
    r = np.random.default_rng(seed)
    t = tsec(dur)
    drone = (0.5 * np.sin(2 * np.pi * 41.2 * t) + 0.35 * np.sin(2 * np.pi * 61.7 * t + 0.6 * np.sin(2 * np.pi * 0.07 * t))
             + 0.18 * np.sin(2 * np.pi * 82.9 * t + np.sin(2 * np.pi * 0.11 * t)))
    drone *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t) ** 2
    room = fft_filter(r.normal(0, 1, len(t)), 40, 400) * 0.9
    hum = (np.sin(2 * np.pi * 100 * t) * 0.03 + np.sin(2 * np.pi * 200 * t) * 0.012 + np.sin(2 * np.pi * 300 * t) * 0.006)
    hum *= (1 + 0.5 * np.sin(2 * np.pi * 0.3 * t))
    return drone * 0.06 + room * 0.05 + hum * 0.6


def static(dur, seed=3):
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    x = fft_filter(r.normal(0, 1, n), 600, 5200) * 0.5
    cr = np.zeros(n)
    idx = r.integers(0, n, int(dur * 25))
    cr[idx] = r.normal(0, 3, len(idx))
    x += fft_filter(cr, 1000, 8000)
    x *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.4 * np.arange(n) / SR)
    return x * 0.22


VOICES = {
    "narr": (["-v", "mb-de6", "-s", "142", "-p", "38"], "highpass=f=70,lowpass=f=7500,aecho=0.8:0.5:35|70:0.12|0.06", 1.0),
    "call": (["-v", "de+whisper", "-s", "100", "-p", "12", "-a", "200"], "lowpass=f=3800,aecho=0.8:0.9:220|480|800:0.55|0.4|0.25", 0.9),
    "phone": (["-v", "mb-de4", "-s", "165", "-p", "55"], "highpass=f=480,lowpass=f=3000", 0.75),
    "man": (["-v", "mb-de4", "-s", "118", "-p", "22"], "lowpass=f=6000,aecho=0.8:0.7:55|120:0.3|0.18", 0.9),
}


def tts(text, voice="narr"):
    args, chain, gain = VOICES[voice]
    h = hashlib.md5((voice + repr(args) + chain + text).encode()).hexdigest()[:16]
    raw, out = os.path.join(BUILD, f"tts_{h}_raw.wav"), os.path.join(BUILD, f"tts_{h}.wav")
    if not os.path.exists(out):
        subprocess.run(["espeak-ng", *args, "-w", raw, text], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", chain + ",aresample=44100",
                        "-ac", "1", out], check=True)
    with wave.open(out) as w_:
        x = np.frombuffer(w_.readframes(w_.getnframes()), np.int16).astype(np.float64) / 32768
    # Stille am Ende abschneiden
    nz = np.nonzero(np.abs(x) > 0.01)[0]
    if len(nz):
        x = x[: nz[-1] + int(0.08 * SR)]
    x = x / (np.abs(x).max() + 1e-9) * 0.8 * gain
    if voice == "phone":
        x = np.tanh(x * 2.5) * 0.5
    if voice == "call":
        x = reverb(x, 2.5, 0.45)
    return x


# =====================================================================
#  TIMELINE
# =====================================================================
COUNTDOWN = 5


def build_timeline(part):
    segs, t = [], 0.0
    for i, s in enumerate(part["segs"]):
        s = dict(s)
        s.setdefault("voice", "narr")
        audio = tts(s["say"], s["voice"]) if s.get("say") else np.zeros(1)
        s["audio"] = audio
        s["tts_start"] = 0.18
        s["tts_dur"] = len(audio) / SR
        dur = s["tts_start"] + s["tts_dur"] + s.get("pad", 0.25)
        if "choice" in s:
            s["cd_start"] = s["tts_start"] + s["tts_dur"] + 0.3
            dur = s["cd_start"] + COUNTDOWN + 0.4
        if i == 0:
            s["tts_start"] += 0.6
            dur += 0.6
        s["start"], s["dur"] = t, dur
        t += dur
        segs.append(s)
    return segs, t


def mix_audio(segs, total, n):
    L = int((total + 3.5) * SR)
    mix = np.zeros(L)
    amb = ambience(total + 3.5, n)
    mix += amb
    st = static(total + 3.5, n)
    radio_env = np.zeros(L)

    def place(x, at, gain=1.0):
        s = int(at * SR)
        if s >= L:
            return
        e = min(L, s + len(x))
        mix[s:e] += x[: e - s] * gain

    prev_scene = None
    for s in segs:
        place(s["audio"], s["start"] + s["tts_start"], 1.0)
        a, b = int(s["start"] * SR), int((s["start"] + s["dur"]) * SR)
        radio_env[a:b] = s.get("radio", 0.08)
        for name, off in s.get("sfx", []):
            g = {"footsteps": 0.7, "footsteps_slow": 0.6, "paper": 0.5, "sting": 0.55, "thud": 0.9, "ring": 0.6, "door": 0.8}.get(name, 0.6)
            place(sfx(name), s["start"] + off, g)
        if prev_scene is not None and s["scene"] != prev_scene:
            place(sfx("glitch"), s["start"], 0.35)
            place(sfx("whoosh"), s["start"] - 0.2, 0.6)
        prev_scene = s["scene"]
        if "choice" in s:
            for k in range(COUNTDOWN):
                place(sfx("tick"), s["start"] + s["cd_start"] + k, 0.8)
                place(sfx("heart"), s["start"] + s["cd_start"] + k + 0.05, 0.8)
        if s.get("final"):
            place(sfx("sting"), s["start"] + s["dur"] - 0.3, 0.5)
    k = int(0.4 * SR)
    cs = np.concatenate([[0], np.cumsum(radio_env)])
    idx = np.clip(np.arange(L) + k // 2, 0, L)
    idx0 = np.clip(np.arange(L) - k // 2, 0, L)
    radio_env = (cs[idx] - cs[idx0]) / k
    mix += st * radio_env
    # Sanfter Limiter
    peak = np.percentile(np.abs(mix), 99.95)
    mix = np.tanh(mix / max(peak, 1e-6) * 1.1) * 0.85
    fade = int(0.8 * SR)
    end = int((total + 0.2) * SR)
    mix[end - fade:end] *= np.linspace(1, 0, fade)
    mix[end:] = 0
    return mix[:end]


def write_wav(path, x):
    with wave.open(path, "wb") as w_:
        w_.setnchannels(1)
        w_.setsampwidth(2)
        w_.setframerate(SR)
        w_.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


# =====================================================================
#  OVERLAYS
# =====================================================================
def text_img(text, fnt, fill, stroke=8, stroke_fill=(0, 0, 0)):
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bb = tmp.textbbox((0, 0), text, font=fnt, stroke_width=stroke)
    im = Image.new("RGBA", (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8), 0)
    ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), text, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def chunk_words(text, max_chars=24, max_words=5):
    words, chunks, cur = text.split(), [], []
    for w_ in words:
        cand = " ".join(cur + [w_])
        if cur and (len(cand) > max_chars or len(cur) >= max_words):
            chunks.append(" ".join(cur))
            cur = [w_]
        else:
            cur.append(w_)
        if w_.endswith((".", "!", "?", ":")) and len(" ".join(cur)) > 8:
            chunks.append(" ".join(cur))
            cur = []
    if cur:
        chunks.append(" ".join(cur))
    merged = []
    for c in chunks:
        if merged and (len(c) <= 7 or len(merged[-1]) <= 5):
            merged[-1] = merged[-1] + " " + c
        else:
            merged.append(c)
    return merged


@lru_cache(512)
def caption_img(text, color):
    fnt = font(F_CAP, 76)
    tmp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines = wrap(text, fnt, 940, tmp)
    imgs = [text_img(l, fnt, color, 9) for l in lines]
    w_ = max(i.size[0] for i in imgs)
    h_ = sum(i.size[1] for i in imgs) + 6 * (len(imgs) - 1)
    out = Image.new("RGBA", (w_, h_), 0)
    y = 0
    for i in imgs:
        out.paste(i, ((w_ - i.size[0]) // 2, y), i)
        y += i.size[1] + 6
    return out


def caption_schedule(seg):
    text = seg.get("cap", seg["say"])
    chunks = chunk_words(text, 26 if seg["scene"].startswith("note") else 24)
    weights = [len(c) + 4 for c in chunks]
    tot = sum(weights)
    out, t = [], seg["tts_start"]
    for c, w_ in zip(chunks, weights):
        d = seg["tts_dur"] * w_ / tot
        out.append((t, t + d, c))
        t += d
    # letzter Chunk bleibt bis Segmentende
    if out:
        a, _, c = out[-1]
        out[-1] = (a, seg["dur"], c)
    return out


@lru_cache(64)
def choice_card(a, b, hint):
    im = Image.new("RGBA", (W, H), 0)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, H], fill=(0, 0, 0, 120))
    q = text_img("WAS SOLL ICH TUN?", font(F_CAP, 84), (255, 255, 255), 8)
    im.paste(q, ((W - q.size[0]) // 2, 360), q)
    for k, (lab, txt, col) in enumerate((("A", a, (230, 50, 60)), ("B", b, (60, 140, 240)))):
        y0 = 520 + k * 300
        d.rounded_rectangle([70, y0, W - 70, y0 + 250], 36, fill=(10, 10, 14, 225), outline=col + (255,), width=8)
        d.ellipse([105, y0 + 55, 245, y0 + 195], fill=col + (255,))
        lt = text_img(lab, font(F_CAP, 96), (255, 255, 255), 0)
        im.paste(lt, (175 - lt.size[0] // 2, y0 + 125 - lt.size[1] // 2 - 4), lt)
        lines = wrap(txt, font(F_CAP, 60), W - 70 - 290, d)
        ly = y0 + 125 - (len(lines) * 72) // 2
        for ln in lines:
            d.text((285, ly), ln, font=font(F_CAP, 60), fill=(255, 255, 255, 255))
            ly += 72
    if hint:
        ht = text_img(hint, font(F_BOLD, 46), (255, 220, 80), 6)
        im.paste(ht, ((W - ht.size[0]) // 2, 1135), ht)
    return im


@lru_cache(16)
def countdown_img(num, frac_bucket):
    im = Image.new("RGBA", (260, 260), 0)
    d = ImageDraw.Draw(im)
    d.ellipse([10, 10, 250, 250], fill=(0, 0, 0, 170), outline=(80, 80, 80, 255), width=10)
    d.arc([10, 10, 250, 250], -90, -90 + 360 * frac_bucket / 20, fill=(255, 60, 60, 255), width=12)
    t = text_img(str(num), font(F_CAP, 130), (255, 255, 255), 0)
    im.paste(t, (130 - t.size[0] // 2, 130 - t.size[1] // 2 - 8), t)
    return im


@lru_cache(8)
def title_img(n):
    im = Image.new("RGBA", (W, 520), 0)
    l1 = text_img("DIE REGELN DES", font(F_CAP, 70), (235, 235, 235), 8)
    l2 = text_img("NACHTWÄCHTERS", font(F_CAP, 104), (230, 40, 40), 10)
    im.paste(l1, ((W - l1.size[0]) // 2, 40), l1)
    im.paste(l2, ((W - l2.size[0]) // 2, 120), l2)
    label = f"TEIL {n}" if n < 5 else "TEIL 5 · FINALE"
    d = ImageDraw.Draw(im)
    tw = d.textlength(label, font=font(F_CAP, 58))
    d.rounded_rectangle([(W - tw) / 2 - 34, 270, (W + tw) / 2 + 34, 360], 45, fill=(255, 255, 255, 240))
    d.text(((W - tw) / 2, 280), label, font=font(F_CAP, 58), fill=(10, 10, 10, 255))
    return im


@lru_cache(64)
def hud_img(cam, label, clock, rec_on):
    im = Image.new("RGBA", (W, 260), 0)
    d = ImageDraw.Draw(im)
    f = font(F_MONO, 40)
    if rec_on:
        d.ellipse([60, 170, 92, 202], fill=(240, 30, 30, 255))
    d.text((106, 164), "REC", font=f, fill=(255, 255, 255, 230), stroke_width=2, stroke_fill=(0, 0, 0))
    d.text((60, 214), f"{cam}  {label}", font=font(F_MONO, 30), fill=(230, 230, 230, 210), stroke_width=2, stroke_fill=(0, 0, 0))
    tw = d.textlength(clock, font=f)
    d.text((W - 60 - tw, 164), clock, font=f, fill=(255, 255, 255, 230), stroke_width=2, stroke_fill=(0, 0, 0))
    return im


@lru_cache(4)
def end_badge(n, final):
    txt = "ENDE … ODER?" if final else f"TEIL {n + 1} FOLGT ↓"
    im = text_img(txt, font(F_CAP, 64), (255, 220, 70), 8)
    return im


# =====================================================================
#  FRAMES
# =====================================================================
def make_static_maps():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / (W * 0.62)) ** 2 + ((y - H / 2) / (H * 0.62)) ** 2)
    vig = np.clip(1.05 - d ** 2.2 * 0.75, 0.15, 1.0).astype(np.float32)
    rng = np.random.default_rng(1)
    grains = [np.repeat(np.repeat(rng.normal(0, 3.5, (H // 3, W // 3)), 3, 0), 3, 1).astype(np.int16) for _ in range(6)]
    scan = (1 - 0.06 * (np.arange(H) % 4 < 2)).astype(np.float32)[:, None]
    return vig * scan, grains


def render_part(part):
    n = part["n"]
    segs, total = build_timeline(part)
    print(f"Teil {n}: {total:.1f}s, {len(segs)} Segmente", flush=True)
    wav = os.path.join(BUILD, f"teil{n}.wav")
    write_wav(wav, mix_audio(segs, total, n))
    for s in segs:
        get_scene(s["scene"])
    vig, grains = make_static_maps()
    caps = [caption_schedule(s) for s in segs]

    # Ken-Burns-Gruppen + Uhrzeit
    groups, gstart, prev = [], 0, None
    clock_base, clock_t = 0, 0.0
    for i, s in enumerate(segs):
        key = "note" if s["scene"].startswith("note") else s["scene"]
        if key != prev:
            gstart = s["start"]
        prev = key
        if "time" in s:
            hh, mm = map(int, s["time"].split(":"))
            clock_base, clock_t = hh * 3600 + mm * 60, s["start"]
        s["g0"] = gstart
        s["clock"] = (clock_base, clock_t)
    gends = {}
    for s in segs:
        gends[s["g0"]] = s["start"] + s["dur"]

    out = os.path.join(OUT, f"nachtwaechter_teil{n}.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "26", "-maxrate", "2200k", "-bufsize", "4400k",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
                          stdin=subprocess.PIPE)
    nframes = int(total * FPS)
    si = 0
    for fi in range(nframes):
        t = fi / FPS
        while si < len(segs) - 1 and t >= segs[si]["start"] + segs[si]["dur"]:
            si += 1
        s = segs[si]
        lt = t - s["start"]
        r = rng_for(n, fi)
        # --- Hintergrund mit Ken Burns
        bg = get_scene(s["scene"])
        g0, g1 = s["g0"], gends[s["g0"]]
        p = (t - g0) / max(0.1, g1 - g0)
        z = 1.0 + 0.085 * p
        cw, chh = BW / z, BH / z
        drift = math.sin((g0 + 1) * 2.1) * 0.5
        cx = BW / 2 + drift * (BW - cw) * 0.5 * p
        cy = BH / 2 + (0.3 if s["scene"].startswith("note") else 0) * (BH - chh) * 0.5 * p * 0
        if s.get("shake"):
            cx += r.uniform(-6, 6)
            cy += r.uniform(-6, 6)
        if s.get("shake"):
            cw, chh = cw * 0.985, chh * 0.985
        cx = min(max(cx, cw / 2), BW - cw / 2)
        cy = min(max(cy, chh / 2), BH - chh / 2)
        box = (cx - cw / 2, cy - chh / 2, cx + cw / 2, cy + chh / 2)
        frame = bg.resize((W, H), Image.BILINEAR, box=box)
        # --- Overlays
        if s["scene"] in CAMS:
            cam, lab = CAMS[s["scene"]]
            cb, ct = s["clock"]
            sec = int(cb + (t - ct) * 1.0)
            clock = f"{(sec // 3600) % 24:02d}:{(sec // 60) % 60:02d}:{sec % 60:02d}"
            hud = hud_img(cam, lab, clock, int(t * 1.6) % 2 == 0)
            frame.paste(hud, (0, 0), hud)
        if n and t < 3.2 and si == 0:
            ti = title_img(n)
            a = min(1, t / 0.3) * min(1, (3.2 - t) / 0.5)
            if a < 1:
                ti = ti.copy()
                ti.putalpha(ti.getchannel("A").point(lambda v: int(v * a)))
            jitter = int(r.uniform(-8, 8)) if r.random() < 0.12 else 0
            frame.paste(ti, (jitter, 300), ti)
        if "choice" in s:
            a_in = min(1, lt / 0.35)
            card = choice_card(s["choice"][0], s["choice"][1], s.get("hint"))
            if a_in < 1:
                card = card.copy()
                card.putalpha(card.getchannel("A").point(lambda v: int(v * a_in)))
            frame.paste(card, (0, 0), card)
            if lt >= s["cd_start"]:
                el = lt - s["cd_start"]
                num = max(1, COUNTDOWN - int(el))
                cd = countdown_img(num, int(min(1, el / COUNTDOWN) * 20))
                frame.paste(cd, ((W - 260) // 2, 1220), cd)
        else:
            for a, b, c in caps[si]:
                if a <= lt < b:
                    col = {"narr": (255, 255, 255), "call": (255, 70, 70), "phone": (255, 214, 90), "man": (255, 214, 90)}[s["voice"]]
                    if s["voice"] != "narr":
                        c = "„" + c.strip("„“\"") + "“" if True else c
                    ci = caption_img(c, col)
                    y = 1440 if s["scene"].startswith("note") else 1250
                    pop = min(1.0, (lt - a) / 0.08)
                    if pop < 1:
                        ci = ci.resize((max(1, int(ci.size[0] * (0.9 + 0.1 * pop))), max(1, int(ci.size[1] * (0.9 + 0.1 * pop)))), Image.BILINEAR)
                    frame.paste(ci, ((W - ci.size[0]) // 2, y - ci.size[1] // 2), ci)
                    break
            if s.get("end"):
                eb = end_badge(n, bool(s.get("final")))
                if int(lt * 2) % 2 == 0 or lt > s["tts_start"] + s["tts_dur"]:
                    frame.paste(eb, ((W - eb.size[0]) // 2, 1450 if not s["scene"].startswith("note") else 1560), eb)
        # --- Effekte
        arr = np.asarray(frame).astype(np.float32)
        flick = s.get("flick", 0.12)
        b = 1.0
        if r.random() < 0.08 + 0.25 * flick:
            b -= r.uniform(0.05, 0.25 + 0.55 * flick)
        if flick > 0.9 and r.random() < 0.15:
            b = 0.15
        arr *= (vig * b)[..., None]
        arr = arr.astype(np.int16) + grains[(fi // 2) % len(grains)][..., None]
        # Glitch bei Szenenwechsel
        if si > 0 and segs[si - 1]["scene"] != s["scene"] and lt < 0.14:
            for _ in range(10):
                y0 = r.randrange(0, H - 40)
                hgt = r.randrange(10, 90)
                arr[y0:y0 + hgt] = np.roll(arr[y0:y0 + hgt], r.randrange(-120, 120), axis=1)
            arr = (arr * 0.7 + np.random.default_rng(fi).normal(60, 50, (H // 4, W // 4)).repeat(4, 0).repeat(4, 1)[..., None] * 0.3).astype(np.int16)
        if t < 0.4:
            arr = (arr * (t / 0.4)).astype(np.int16)
        if t > total - 0.6:
            arr = (arr * max(0, (total - t) / 0.6)).astype(np.int16)
        ff.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
        if fi % 300 == 0:
            print(f"  Teil {n}: Frame {fi}/{nframes}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("fertig:", out, flush=True)
    return out


if __name__ == "__main__":
    which = [int(a) for a in sys.argv[1:]] or [p["n"] for p in story.PARTS]
    for p in story.PARTS:
        if p["n"] in which:
            render_part(p)
