# -*- coding: utf-8 -*-
"""Prozedurale Hintergründe (PIL): Gang, Wachraum, Lagertür, Haupteingang,
Regelkarte, Handy-Bildschirme. Alle in Welt-Auflösung BW x BH."""
import math
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

BW, BH = 1188, 2112
FD = "/usr/share/fonts/"
F_CAP = FD + "opentype/inter/Inter-ExtraBold.otf"
F_BOLD = FD + "opentype/inter/Inter-Bold.otf"
F_REG = FD + "opentype/inter/Inter-Regular.otf"
F_SEMI = FD + "opentype/inter/Inter-SemiBold.otf"
F_MONO = FD + "truetype/dejavu/DejaVuSansMono-Bold.ttf"
F_HAND = FD + "truetype/liberation/LiberationSerif-Italic.ttf"
F_HANDB = FD + "truetype/liberation/LiberationSerif-BoldItalic.ttf"
F_SYM = FD + "truetype/dejavu/DejaVuSans.ttf"


@lru_cache(None)
def font(path, size):
    return ImageFont.truetype(path, size)


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


def wrap(text, fnt, maxw, draw=None):
    draw = draw or ImageDraw.Draw(Image.new("RGB", (10, 10)))
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


# ===================================================================== GANG
def corridor():
    img = Image.new("RGB", (BW, BH), (5, 7, 11))
    glow = Image.new("RGB", (BW, BH), 0)
    d, g = ImageDraw.Draw(img), ImageDraw.Draw(glow)
    vx, vy, k = BW / 2, BH * 0.43, 780
    FY, CY = 1.2, -1.25

    def P(x, y, z):
        return (vx + x * k / z, vy + y * k / z)

    def sh(c, z, m=1.0):
        f = math.exp(-(z - 0.5) / 4.5) * m
        return tuple(int(v * f) for v in c)

    for z0 in np.arange(14.0, 0.45, -0.25):
        z1 = z0 - 0.25
        floor_c = (34, 38, 46) if int(z0 * 2) % 2 else (28, 31, 38)
        d.polygon([P(-1, FY, z1), P(1, FY, z1), P(1, FY, z0), P(-1, FY, z0)], fill=sh(floor_c, z0))
        d.polygon([P(-1, CY, z1), P(1, CY, z1), P(1, CY, z0), P(-1, CY, z0)], fill=sh((22, 24, 30), z0))
        for s in (-1, 1):
            d.polygon([P(s, CY, z1), P(s, FY, z1), P(s, FY, z0), P(s, CY, z0)], fill=sh((30, 32, 40), z0))
    for x in np.arange(-1, 1.01, 0.25):
        d.line([P(x, FY, 0.5), P(x, FY, 14)], fill=(14, 16, 20), width=2)
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
                g.polygon([P(side, -0.5, za + 0.3), P(side, -0.37, za + 0.3), P(side, -0.37, zb - 0.3), P(side, -0.5, zb - 0.3)], fill=sh(c, za, 0.9))
            d.polygon([P(side, CY, zb), P(side, FY, zb), P(side, FY, zb + 0.3), P(side, CY, zb + 0.3)], fill=sh((44, 46, 54), zb))
    for i, z in enumerate(np.arange(1.3, 13, 1.5)):
        on = i not in (2, 5)
        col = (200, 215, 230) if on else (30, 32, 36)
        poly = [P(-0.18, CY + 0.01, z - 0.25), P(0.18, CY + 0.01, z - 0.25), P(0.18, CY + 0.01, z + 0.25), P(-0.18, CY + 0.01, z + 0.25)]
        (g if on else d).polygon(poly, fill=sh(col, z, 1.2))
        if on:
            x0, y0 = P(-0.2, FY, z)
            x1, y1 = P(0.2, FY, z + 0.6)
            g.ellipse([x0, y1 - 4, x1, y0 + 4], fill=sh((26, 28, 34), z))
    ex, ey = P(0, -0.8, 13.5)
    g.rectangle([ex - 26, ey - 10, ex + 26, ey + 10], fill=(40, 200, 90))
    img = add_glow(img, glow, 28, 1.1)
    img = Image.blend(img, ImageChops.multiply(img, Image.new("RGB", img.size, (200, 220, 255))), 0.5)
    return texture(img, 9, 3)


def corridor_floor_y(z):
    """Bildschirm-y (Welt) des Bodens in Tiefe z – zum Platzieren von Figuren."""
    return BH * 0.43 + 1.2 * 780 / z


# ===================================================================== WACHRAUM
def _radio(d, glow, x, y, w, h):
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
    d.line([x + 40, y, x - 60, y - 300], fill=(120, 120, 125), width=5)


RADIO_BOX = (110, 1180, 430, 330)


def office(with_desk=True):
    img = vgrad((BW, BH), (14, 18, 18), (6, 8, 8))
    glow = Image.new("RGB", (BW, BH), 0)
    d = ImageDraw.Draw(img)
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
    # Poster/Plan an der Wand
    d.rectangle([60, 1060, 130, 1300], fill=(30, 34, 30))
    if with_desk:
        d.polygon([(-50, 1480), (BW + 50, 1480), (BW + 300, BH), (-300, BH)], fill=(46, 32, 22))
        for i in range(14):
            yy = 1500 + i * 45
            d.line([(-300, yy), (BW + 300, yy + rng.integers(-15, 15))], fill=(38, 26, 18), width=3)
        d.rectangle([-50, 1460, BW + 50, 1490], fill=(30, 20, 14))
        _radio(d, glow, *RADIO_BOX)
        d.rounded_rectangle([760, 1340, 1060, 1530], 40, fill=(140, 20, 20), outline=(40, 5, 5), width=5)
        d.rounded_rectangle([740, 1280, 1080, 1360], 40, fill=(160, 26, 24), outline=(40, 5, 5), width=5)
        for i in range(3):
            for j in range(3):
                d.ellipse([845 + j * 50, 1380 + i * 45, 875 + j * 50, 1408 + i * 45], fill=(225, 215, 200))
        # Thermoskanne + Logbuch
        d.rounded_rectangle([600, 1330, 690, 1560], 20, fill=(60, 70, 64), outline=(20, 24, 22), width=4)
        d.rectangle([590, 1320, 700, 1350], fill=(30, 34, 32))
        lamp = radial((BW, BH), 620, 1700, 650, (120, 95, 60), 1.6)
    else:
        lamp = radial((BW, BH), 620, 1400, 750, (70, 56, 36), 1.6)
    img = ImageChops.add(img, lamp)
    img = add_glow(img, glow, 40, 0.8)
    return texture(img, 8, 4)


def office_front_mask():
    m = Image.new("L", (BW, BH), 0)
    d = ImageDraw.Draw(m)
    d.polygon([(-50, 1458), (BW + 50, 1458), (BW + 300, BH), (-300, BH)], fill=255)
    x, y, w, h = RADIO_BOX
    d.rounded_rectangle([x - 4, y - 4, x + w + 4, y + h + 4], 18, fill=255)
    d.line([x + 40, y, x - 60, y - 300], fill=255, width=7)
    d.rounded_rectangle([738, 1276, 1082, 1534], 40, fill=255)
    d.rounded_rectangle([588, 1318, 702, 1562], 20, fill=255)
    return m.filter(ImageFilter.GaussianBlur(1.2))


# ===================================================================== LAGERTÜR
def door(num="3"):
    img = vgrad((BW, BH), (32, 33, 34), (16, 17, 18))
    glow = Image.new("RGB", (BW, BH), 0)
    d, g = ImageDraw.Draw(img), ImageDraw.Draw(glow)
    rng = np.random.default_rng(11)
    for i in range(40):
        y = int(rng.integers(0, 1700))
        d.line([(0, y), (BW, y)], fill=(28, 29, 30), width=2)
    d.polygon([(0, 1720), (BW, 1720), (BW, BH), (0, BH)], fill=(20, 21, 22))
    for i in range(8):
        d.line([(BW / 2 + (i - 3.5) * 120, 1720), (BW / 2 + (i - 3.5) * 520, BH)], fill=(14, 15, 16), width=3)
    x0, y0, x1, y1 = 300, 560, 890, 1720
    d.rectangle([x0 - 30, y0 - 30, x1 + 30, y1], fill=(12, 12, 13))
    dr = vgrad((x1 - x0, y1 - y0 - 12), (78, 84, 88), (44, 46, 50))
    img.paste(dr, (x0, y0))
    d.rectangle([x0, y0, x1, y1 - 12], outline=(20, 20, 22), width=4)
    for yy in (y0 + 200, y1 - 260):
        d.line([(x0 + 30, yy), (x1 - 30, yy)], fill=(36, 38, 40), width=3)
    d.rounded_rectangle([x1 - 110, y0 + 560, x1 - 40, y0 + 590], 10, fill=(150, 150, 150))
    d.rectangle([x1 - 92, y0 + 590, x1 - 62, y0 + 650], fill=(70, 70, 70))
    # Vorhängeschloss + Riegel (von außen abgeschlossen!)
    d.rectangle([x1 - 160, y0 + 700, x1 + 20, y0 + 730], fill=(110, 110, 105))
    d.rounded_rectangle([x1 - 40, y0 + 720, x1 + 10, y0 + 790], 8, fill=(160, 130, 40))
    d.arc([x1 - 35, y0 + 690, x1 + 5, y0 + 740], 180, 360, fill=(170, 170, 170), width=8)
    d.rectangle([BW / 2 - 170, y0 + 90, BW / 2 + 170, y0 + 210], fill=(225, 225, 215), outline=(20, 20, 20), width=5)
    t = f"LAGER {num}"
    tw = d.textlength(t, font=font(F_BOLD, 74))
    d.text((BW / 2 - tw / 2, y0 + 105), t, font=font(F_BOLD, 74), fill=(20, 20, 20))
    lc = (255, 170, 80)
    g.rectangle([x0 + 10, y1 - 14, x1 - 10, y1 - 4], fill=lc)
    g.polygon([(x0, y1), (x1, y1), (x1 + 160, BH), (x0 - 160, BH)], fill=tuple(int(c * 0.12) for c in lc))
    g.ellipse([BW / 2 - 28, 360, BW / 2 + 28, 420], fill=(200, 200, 170))
    img = ImageChops.add(img, radial((BW, BH), BW / 2, 390, 700, (60, 60, 50), 1.8))
    d = ImageDraw.Draw(img)
    for i in range(5):
        d.line([(BW / 2 - 34 + i * 17, 350), (BW / 2 - 34 + i * 17, 430)], fill=(30, 30, 30), width=3)
    img = add_glow(img, glow, 34, 1.2)
    img = ImageChops.multiply(img, radial((BW, BH), BW / 2, BH * 0.45, 1300, (255, 255, 255), 0.6))
    return texture(img, 11, 12)


DOOR_GAP_Y = 1706          # Lichtspalt unter der Tür
DOOR_X0, DOOR_X1 = 310, 880


# ===================================================================== HAUPTEINGANG
GLASS = (168, 520, 1020, 1640)


def entrance(dawn=False):
    if dawn:
        img = vgrad((BW, BH), (70, 90, 130), (30, 30, 40))
    else:
        img = vgrad((BW, BH), (6, 10, 22), (2, 3, 6))
    glow = Image.new("RGB", (BW, BH), 0)
    d, g = ImageDraw.Draw(img), ImageDraw.Draw(glow)
    if dawn:
        sky = vgrad((BW - 320, 760), (60, 90, 150), (230, 150, 110))
        img.paste(sky, (160, 500))
        d.polygon([(160, 1250), (BW - 160, 1250), (BW - 160, 1650), (160, 1650)], fill=(60, 60, 70))
        g.ellipse([700, 1180, 900, 1300], fill=(255, 190, 120))
    else:
        d.rectangle([160, 500, BW - 160, 1650], fill=(10, 16, 32))
        d.polygon([(160, 1250), (BW - 160, 1250), (BW - 160, 1650), (160, 1650)], fill=(14, 16, 22))
    for lx, ly, s in ((300, 1000, 1.0), (800, 1060, 0.7), (520, 1110, 0.5), (960, 980, 1.1)):
        d.line([(lx, ly), (lx, 1250 + 20 * s)], fill=(30, 30, 36), width=int(8 * s))
        if not dawn:
            g.ellipse([lx - 18 * s, ly - 12 * s, lx + 18 * s, ly + 12 * s], fill=(255, 150, 60))
            g.ellipse([lx - 90 * s, 1240, lx + 90 * s, 1265], fill=(50, 28, 12))
    img = add_glow(img, glow, 40 if dawn else 30, 1.2)
    full = img.copy()
    d = ImageDraw.Draw(full)
    fc = (40, 44, 52) if not dawn else (70, 74, 84)
    wallc = (14, 15, 18) if not dawn else (40, 40, 46)
    d.rectangle([140, 480, BW - 140, 520], fill=fc)
    d.rectangle([140, 1640, BW - 140, 1680], fill=fc)
    for x in (140, BW - 168):
        d.rectangle([x, 480, x + 28, 1680], fill=fc)
    d.line([(BW / 2, 520), (BW / 2, 1640)], fill=(60, 66, 78) if not dawn else (90, 94, 104), width=3)
    for x in (360, 820):
        d.rounded_rectangle([x, 1050, x + 18, 1200], 8, fill=(90, 94, 100))
    d.rectangle([0, 0, BW, 480], fill=(12, 13, 16) if not dawn else (34, 34, 40))
    d.rectangle([0, 0, 140, BH], fill=wallc)
    d.rectangle([BW - 140, 0, BW, BH], fill=wallc)
    t = "HAUPTEINGANG"
    tw = d.textlength(t, font=font(F_BOLD, 54))
    d.text((BW / 2 - tw / 2, 390), t, font=font(F_BOLD, 54), fill=(120, 130, 150))
    d.polygon([(0, 1680), (BW, 1680), (BW, BH), (0, BH)], fill=(22, 24, 28) if not dawn else (60, 58, 62))
    for i in range(9):
        d.line([(BW / 2 + (i - 4) * 130, 1680), (BW / 2 + (i - 4) * 520, BH)], fill=(16, 17, 20), width=3)
    full = texture(full, 9, 41 + dawn)
    back = texture(img, 9, 51 + dawn)
    mask = Image.new("L", (BW, BH), 255)
    ImageDraw.Draw(mask).rectangle([168, 520, BW - 168, 1640], fill=0)
    # Türgriffe gehören zum Vordergrund
    for x in (360, 820):
        ImageDraw.Draw(mask).rounded_rectangle([x, 1050, x + 18, 1200], 8, fill=255)
    front = full.convert("RGBA")
    front.putalpha(mask)
    # Glasreflexe
    refl = Image.new("RGBA", (BW, BH), 0)
    rd = ImageDraw.Draw(refl)
    for x in (380, 470, 880):
        rd.polygon([(x, 520), (x + 50, 520), (x - 200, 1640), (x - 250, 1640)], fill=(150, 170, 210, 26))
    refl = refl.filter(ImageFilter.GaussianBlur(10))
    return back, front, refl


# ===================================================================== REGELKARTE
def rule_card(reveal, hl=None, rules=None):
    """Alte, vergilbte Karteikarte mit Walters Regeln (RGBA)."""
    pw, ph = 980, 1180
    paper = Image.new("RGBA", (pw, ph), (232, 222, 192, 255))
    arr = np.asarray(paper).astype(np.int16)
    n = np.random.default_rng(5).normal(0, 7, (ph, pw))
    arr[..., :3] = np.clip(arr[..., :3] + n[..., None], 0, 255)
    yy = np.linspace(-1, 1, ph)[:, None]
    xx = np.linspace(-1, 1, pw)[None]
    edge = np.clip(1 - 0.25 * (xx ** 8 + yy ** 8) - 0.06 * (xx ** 2), 0, 1)
    arr[..., :3] = (arr[..., :3] * edge[..., None]).astype(np.int16)
    paper = Image.fromarray(arr.astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(paper)
    for y in range(250, ph - 40, 62):
        d.line([(30, y), (pw - 30, y)], fill=(150, 175, 205, 255), width=2)
    d.line([(30, 205), (pw - 30, 205)], fill=(200, 80, 80, 255), width=3)
    stain = Image.new("RGBA", paper.size, 0)
    sd = ImageDraw.Draw(stain)
    sd.ellipse([pw - 260, ph - 300, pw - 50, ph - 90], outline=(140, 95, 50, 70), width=14)
    sd.ellipse([40, 30, 120, 110], fill=(140, 95, 50, 30))
    paper = Image.alpha_composite(paper, stain.filter(ImageFilter.GaussianBlur(2)))
    # Klebestreifen
    tape = Image.new("RGBA", (220, 60), (240, 240, 220, 120))
    paper.alpha_composite(tape.rotate(-8, expand=True), (pw // 2 - 110, -18))
    d = ImageDraw.Draw(paper)
    ink = (26, 32, 78, 255)
    d.text((70, 70), "DIE REGELN", font=font(F_HANDB, 92), fill=ink)
    d.text((pw - 330, 120), "– Walter", font=font(F_HAND, 52), fill=(26, 32, 78, 200))
    fnt = font(F_HAND, 54)
    y = 250
    for i, r in enumerate(rules):
        lines = wrap(r, fnt, pw - 210)
        hgt = len(lines) * 62
        if i < reveal:
            a = 255 if (hl is None or i == hl) else 110
            if hl is not None and i == hl:
                mark = Image.new("RGBA", paper.size, 0)
                ImageDraw.Draw(mark).rectangle([118, y + 2, pw - 50, y + hgt + 6], fill=(255, 226, 40, 150))
                paper = Image.alpha_composite(paper, mark)
                d = ImageDraw.Draw(paper)
                d.ellipse([36, y - 6, 112, y + 66], outline=(200, 25, 25, 255), width=6)
            d.text((56, y - 4), f"{i + 1}.", font=font(F_HANDB, 62), fill=ink[:3] + (a,))
            for j, ln in enumerate(lines):
                d.text((130, y + j * 62), ln, font=fnt, fill=ink[:3] + (a,))
        y += hgt + 62
    paper = paper.rotate(-1.5, expand=True, resample=Image.BICUBIC)
    return paper


# ===================================================================== HANDY
def _phone_frame():
    pw, ph = 720, 1440
    ph_img = Image.new("RGBA", (pw, ph), 0)
    d = ImageDraw.Draw(ph_img)
    d.rounded_rectangle([0, 0, pw, ph], 90, fill=(18, 18, 20, 255), outline=(70, 70, 76, 255), width=6)
    return ph_img, (34, 34, pw - 34, ph - 34)


def phone_call(active=False, seconds=0, pulse=0.0):
    ph, (sx0, sy0, sx1, sy1) = _phone_frame()
    scr = vgrad((sx1 - sx0, sy1 - sy0), (34, 44, 70), (10, 12, 20)).convert("RGBA")
    mask = Image.new("L", scr.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, scr.size[0], scr.size[1]], 64, fill=255)
    d = ImageDraw.Draw(scr)
    cw = scr.size[0]
    d.text((50, 30), "00:30", font=font(F_SEMI, 34), fill=(230, 230, 240))
    d.rounded_rectangle([cw - 120, 38, cw - 60, 62], 6, outline=(230, 230, 240), width=3)
    d.rectangle([cw - 116, 42, cw - 90, 58], fill=(230, 230, 240))
    d.ellipse([cw / 2 - 110, 220, cw / 2 + 110, 440], fill=(200, 120, 140))
    tw = d.textlength("M", font=font(F_BOLD, 120))
    d.text((cw / 2 - tw / 2, 255), "M", font=font(F_BOLD, 120), fill=(255, 255, 255))
    t = "Mama ♥"
    tw = d.textlength("Mama", font=font(F_BOLD, 88)) + 70
    d.text((cw / 2 - tw / 2, 480), "Mama", font=font(F_BOLD, 88), fill=(255, 255, 255))
    d.text((cw / 2 - tw / 2 + tw - 60, 492), "♥", font=font(F_SYM, 70), fill=(255, 90, 110))
    sub = "eingehender Anruf …" if not active else f"00:{seconds:02d}  ·  Lautsprecher an"
    tw = d.textlength(sub, font=font(F_REG, 40))
    d.text((cw / 2 - tw / 2, 600), sub, font=font(F_REG, 40), fill=(190, 200, 220))
    if not active:
        for (cx, col, sym) in ((cw * 0.27, (230, 60, 60), "✕"), (cw * 0.73, (60, 200, 100), "✆")):
            if col[1] == 200 and pulse > 0:
                r = 80 + 60 * pulse
                d.ellipse([cx - r, 1120 - r, cx + r, 1120 + r], outline=(60, 200, 100), width=4)
            d.ellipse([cx - 80, 1040, cx + 80, 1200], fill=col)
            tw = d.textlength(sym, font=font(F_SYM, 80))
            d.text((cx - tw / 2, 1068), sym, font=font(F_SYM, 80), fill=(255, 255, 255))
    else:
        for i, (lab, on) in enumerate((("stumm", False), ("Tasten", False), ("Lautspr.", True))):
            cx = cw * (0.22 + i * 0.28)
            d.ellipse([cx - 70, 800, cx + 70, 940], fill=(240, 240, 245) if on else (60, 66, 80))
            tw = d.textlength(lab, font=font(F_REG, 32))
            d.text((cx - tw / 2, 960), lab, font=font(F_REG, 32), fill=(200, 205, 215))
        d.ellipse([cw / 2 - 80, 1110, cw / 2 + 80, 1270], fill=(230, 60, 60))
    ph.paste(scr, (sx0, sy0), mask)
    return ph


def phone_msg(show_last=True):
    ph, (sx0, sy0, sx1, sy1) = _phone_frame()
    scr = Image.new("RGBA", (sx1 - sx0, sy1 - sy0), (14, 16, 22, 255))
    mask = Image.new("L", scr.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, scr.size[0], scr.size[1]], 64, fill=255)
    d = ImageDraw.Draw(scr)
    cw = scr.size[0]
    d.text((50, 30), "01:14", font=font(F_SEMI, 34), fill=(230, 230, 240))
    d.rectangle([0, 90, cw, 220], fill=(26, 30, 40))
    d.ellipse([40, 115, 120, 195], fill=(200, 120, 140))
    d.text((64, 128), "M", font=font(F_BOLD, 48), fill=(255, 255, 255))
    d.text((145, 118), "Mama", font=font(F_BOLD, 46), fill=(255, 255, 255))
    d.text((145, 170), "online", font=font(F_REG, 30), fill=(140, 200, 150))

    def bubble(y, text, time, mine=False):
        f = font(F_REG, 40)
        lines = wrap(text, f, cw - 230)
        h = len(lines) * 52 + 70
        x0 = 40 if not mine else cw - 40 - (cw - 160)
        d.rounded_rectangle([x0, y, x0 + cw - 160, y + h], 30, fill=(40, 46, 60) if not mine else (30, 90, 70))
        for i, ln in enumerate(lines):
            d.text((x0 + 30, y + 22 + i * 52), ln, font=f, fill=(240, 240, 245))
        d.text((x0 + cw - 160 - 110, y + h - 44), time, font=font(F_REG, 28), fill=(160, 170, 185))
        return y + h + 30

    y = 280
    y = bubble(y, "Viel Glück bei deiner ersten Nachtschicht, Schatz!", "21:30")
    y = bubble(y, "Danke Mama :)", "21:41", mine=True)
    if show_last:
        y0 = y
        y = bubble(y, "Liege schon seit Stunden im Bett und kann nicht schlafen. Pass auf dich auf!", "01:14")
        d.text((cw - 120, y0 + 20), "♥", font=font(F_SYM, 46), fill=(255, 90, 110))
    ph.paste(scr, (sx0, sy0), mask)
    return ph, y
