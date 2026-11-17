# -*- coding: utf-8 -*-
"""Blockwelt-Sets: Mall außen, Gang, Wachraum, Lagertür, Atrium mit Rolltreppe, Haupteingang."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from engine import World

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

# 3x5-Pixelschrift für Leuchtbuchstaben (eigene Bitmaps)
GLYPHS = {
    "L": ["X...", "X...", "X...", "X...", "XXXX"], "I": ["XXX", ".X.", ".X.", ".X.", "XXX"],
    "N": ["X...X", "XX..X", "X.X.X", "X..XX", "X...X"], "D": ["XXX.", "X..X", "X..X", "X..X", "XXX."],
    "E": ["XXXX", "X...", "XXX.", "X...", "XXXX"], "M": ["X...X", "XX.XX", "X.X.X", "X...X", "X...X"],
    "A": [".XX.", "X..X", "XXXX", "X..X", "X..X"], " ": ["..", "..", "..", "..", ".."],
}


def pixel_text(text, fg, bg=None, h=12, pad=2, font=FONT, up=8):
    f = ImageFont.truetype(font, h)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bb = tmp.textbbox((0, 0), text, font=f)
    w, hh = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    im = Image.new("RGBA", (w, hh), bg or (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - bb[0], pad - bb[1]), text, font=f, fill=fg)
    # harte Pixelkanten
    a = np.asarray(im).copy()
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0) if bg is None else 255
    im = Image.fromarray(a)
    return im.resize((w * up, hh * up), Image.NEAREST)


def register_blocks(w):
    for name in w.atlas.names:
        w.block(name, transparent=(name in ("glass", "window_dark", "glass_clear")))
    w.block("grass", top="grass_top", side="grass_side", bottom="dirt")
    w.block("log_y", top="log", side="log")
    w.block("tree_leaves", side="leaves")


class Set:
    """Eine Blockwelt + statische Lichter + Decals + Anker."""

    def __init__(self, name, atlas, size, offset=(0, 0, 0)):
        self.name = name
        self.w = World(atlas, size)
        self.w.offset = np.array(offset)
        register_blocks(self.w)
        self.lights = []
        self.decals = []          # (key, img, corners, emit, transparent)
        self.anchors = {}
        self.env = dict(amb_sky=(0.10, 0.11, 0.14), amb_ground=(0.05, 0.05, 0.06), fog=(0.02, 0.02, 0.03), fog_dens=0.03)

    def rot_box(self, center, size, ax, tile, transparent=False):
        """Quader um seinen Mittelpunkt um die x-Achse gedreht (für Schrägen)."""
        import engine as E
        tmp = E.World(self.w.atlas, (1, 1, 1))
        sx, sy, sz = size
        tmp.box(-sx / 2, -sy / 2, -sz / 2, sx / 2, sy / 2, sz / 2, tile, transparent=transparent)
        src = (tmp.props_t if transparent else tmp.props).array()
        M = E.translate(*center) @ E.rot_x(ax)
        out = src.copy()
        p = np.c_[src[:, 0:3], np.ones(len(src))] @ M.T
        out[:, 0:3] = p[:, :3]
        out[:, 3:6] = src[:, 3:6] @ M[:3, :3].T
        (self.w.props_t if transparent else self.w.props).data.extend(out.tolist())

    def light(self, pos, col, rad):
        self.lights.append((tuple(pos), tuple(col), rad))

    def decal(self, key, img, corners, emit=0.0, transparent=True):
        self.decals.append((f"{self.name}:{key}", img, corners, emit, transparent))

    def wall_decal(self, key, img, x0, y0, x1, y1, z, facing=1, emit=0.0):
        """Rechteck in Ebene z=const (facing +1: Blickrichtung +z)."""
        if facing > 0:
            cs = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
        else:
            cs = [(x1, y0, z), (x0, y0, z), (x0, y1, z), (x1, y1, z)]
        self.decal(key, img, cs, emit)

    def side_decal(self, key, img, z0, y0, z1, y1, x, facing=1, emit=0.0):
        if facing > 0:   # Blick +x
            cs = [(x, y0, z1), (x, y0, z0), (x, y1, z0), (x, y1, z1)]
        else:
            cs = [(x, y0, z0), (x, y0, z1), (x, y1, z1), (x, y1, z0)]
        self.decal(key, img, cs, emit)

    def floor_decal(self, key, img, x0, z0, x1, z1, y, emit=0.0):
        cs = [(x0, y, z1), (x1, y, z1), (x1, y, z0), (x0, y, z0)]
        self.decal(key, img, cs, emit)


def neon_text(s, text, x0, y0, z, block="neon_red", off=()):
    x = x0
    for i, ch in enumerate(text):
        g = GLYPHS[ch]
        for r, row in enumerate(g):
            for c, v in enumerate(row):
                if v == "X":
                    s.w.set(x + c, y0 + (4 - r), z, "neon_off" if i in off else block)
        x += len(g[0]) + 1


def tree(s, x, y, z, h=5):
    s.w.fill(x, y, z, x, y + h - 1, z, "log_y")
    s.w.fill(x - 2, y + h - 2, z - 2, x + 2, y + h, z + 2, "tree_leaves")
    s.w.fill(x - 1, y + h + 1, z - 1, x + 1, y + h + 1, z + 1, "tree_leaves")
    for (dx, dz) in ((-2, -2), (2, 2), (-2, 2), (2, -2)):
        s.w.set(x + dx, y + h, z + dz, None)


def lamp_post(s, x, z, h=6, on=True, col=(1.0, 0.62, 0.3)):
    s.w.box(x - 0.12, 0, z - 0.12, x + 0.12, h, z + 0.12, "metal_dark")
    s.w.box(x - 0.5, h, z - 0.3, x + 0.5, h + 0.25, z + 0.3, "metal_dark")
    s.w.box(x - 0.4, h - 0.1, z - 0.22, x + 0.4, h, z + 0.22, "lamp_warm" if on else "lamp_off")
    if on:
        s.light((x, h - 0.6, z), (col[0] * 1.6, col[1] * 1.6, col[2] * 1.6), 11)


def car(s, x, z, col="red", yaw_x=True):
    L, Wd = (4.2, 2.0) if yaw_x else (2.0, 4.2)
    s.w.box(x, 0.35, z, x + L, 1.2, z + Wd, col)
    if yaw_x:
        s.w.box(x + 1.0, 1.2, z + 0.15, x + 3.0, 1.95, z + Wd - 0.15, "glass", transparent=True)
        s.w.box(x + 1.0, 1.95, z + 0.15, x + 3.0, 2.05, z + Wd - 0.15, col)
    for (dx, dz) in ((0.5, -0.05), (L - 1.3, -0.05), (0.5, Wd - 0.15), (L - 1.3, Wd - 0.15)):
        s.w.box(x + dx, 0, z + dz, x + dx + 0.8, 0.7, z + dz + 0.2, "rubber")


def sky_img(top, bottom, stars=True, h=256):
    a = np.zeros((h, 8, 3))
    t = np.linspace(0, 1, h)[:, None, None]
    a[:] = np.array(top) * (1 - t) + np.array(bottom) * t
    im = Image.fromarray(a.astype(np.uint8)).resize((128, h), Image.NEAREST)
    if stars:
        d = ImageDraw.Draw(im)
        r = np.random.default_rng(2)
        for _ in range(70):
            x, y = r.integers(0, 128), r.integers(0, int(h * 0.6))
            d.point((int(x), int(y)), fill=(200, 210, 230))
    return im


# =====================================================================
#  SETS
# =====================================================================
def build_exterior(atlas, dawn=False):
    s = Set("exterior" + ("_dawn" if dawn else ""), atlas, (110, 30, 110), offset=(50, 2, 70))
    w = s.w
    w.fill(-45, -1, -60, 55, -1, 35, "asphalt")
    for x in range(-30, 50, 5):
        w.fill(x, -1, 4, x, -1, 10, "asphalt_line")
        w.fill(x, -1, -6, x, -1, 0, "asphalt_line")
    w.fill(-45, -1, 18, 55, -1, 35, "grass")
    # Gebäude
    w.fill(-26, 0, -40, 30, 15, -12, "concrete")
    w.fill(-26, 15, -40, 30, 15, -12, "concrete_dark")
    for x in list(range(-24, -14, 4)) + list(range(14, 30, 4)):
        for y in (8, 12):
            lit = (x == 18 and y == 12)
            w.fill(x, y, -12, x + 1, y + 1, -12, "window_lit" if lit else "black")
    # Eingang
    w.fill(-5, 0, -12, 5, 5, -12, "glass_clear")
    w.fill(-5, 0, -13, 5, 5, -13, "floor")
    w.fill(-6, 6, -12, 6, 6, -9, "metal_dark")            # Vordach
    w.fill(-6, 0, -12, -6, 5, -12, "metal")
    w.fill(6, 0, -12, 6, 5, -12, "metal")
    s.light((0, 4.5, -10.5), (0.45, 0.7, 0.65), 9)
    # Leuchtschrift
    w.fill(-17, 8, -12, 16, 22, -12, "concrete_dark")
    neon_text(s, "LINDEN", -15, 16, -11, off=(4,) if not dawn else tuple(range(6)))
    neon_text(s, "MALL", -10, 9, -11, off=() if not dawn else tuple(range(4)))
    if not dawn:
        s.light((-6, 17, -8), (1.3, 0.22, 0.28), 14)
        s.light((6, 17, -8), (1.3, 0.22, 0.28), 14)
        s.light((0, 10, -8), (1.2, 0.2, 0.25), 12)
    # Laternen, Bäume, Autos
    for x in (-18, 0, 18, 36):
        lamp_post(s, x, 2, on=not dawn)
    for x in (-36, -30, 40, 46):
        tree(s, x, 0, 22, 6)
        tree(s, x + 3, 0, 26, 5)
    car(s, -14, 5, "red")
    car(s, 9, -5, "navy")
    car(s, 26, 6, "grey")
    # Pfützen
    for (x, z, r) in ((-6, 6, 2), (4, 12, 3), (14, 2, 2)):
        w.fill(x - r, -1, z - 1, x + r, -1, z + 1, "water")
    # Himmel
    if dawn:
        sk = sky_img((60, 90, 150), (240, 150, 100), stars=False)
        s.env = dict(amb_sky=(0.55, 0.52, 0.55), amb_ground=(0.3, 0.26, 0.24), fog=(0.85, 0.6, 0.45), fog_dens=0.012, clear=(0.85, 0.6, 0.45), emit_gain=0.6)
    else:
        sk = sky_img((4, 6, 14), (24, 30, 52))
        s.env = dict(amb_sky=(0.30, 0.34, 0.55), amb_ground=(0.12, 0.12, 0.18), fog=(0.08, 0.09, 0.16), fog_dens=0.012, clear=(0.08, 0.09, 0.16))
    s.decal("sky", sk, [(-120, -10, -90), (140, -10, -90), (140, 80, -90), (-120, 80, -90)], emit=1.0, transparent=False)
    if not dawn:
        moon = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        ImageDraw.Draw(moon).rectangle([1, 1, 6, 6], fill=(230, 236, 255, 255))
        s.decal("moon", moon, [(40, 50, -88), (48, 50, -88), (48, 58, -88), (40, 58, -88)], emit=1.0)
    else:
        sun = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        ImageDraw.Draw(sun).rectangle([0, 0, 7, 7], fill=(255, 230, 160, 255))
        s.decal("sun", sun, [(20, 6, -88), (32, 6, -88), (32, 18, -88), (20, 18, -88)], emit=1.4)
    s.anchors.update(entrance=(0, 0, -11), jonas_start=(2, 0, 14))
    return s


def build_corridor(atlas, lit=False):
    s = Set("corridor" + ("_lit" if lit else ""), atlas, (24, 12, 104), offset=(0, 1, 0))
    w = s.w
    L = 100
    for z in range(L):
        for x in range(1, 22):
            w.set(x, -1, z, "floor" if (x // 2 + z // 2) % 2 == 0 else "floor_dark")
    w.fill(0, 0, 0, 0, 10, L - 1, "plaster")
    w.fill(22, 0, 0, 22, 10, L - 1, "plaster")
    w.fill(0, 10, 0, 22, 10, L - 1, "ceiling")
    w.fill(0, 0, 0, 22, 10, 0, "plaster")
    # Läden
    neons = ["neon_red", "neon_blue", "neon_pink", "neon_green"]
    for i, z0 in enumerate(range(4, L - 10, 13)):
        for side, x in ((0, 1), (1, 21)):
            w.fill(x, 0, z0, x, 4, z0 + 9, "shutter")
            w.fill(x, 5, z0, x, 5, z0 + 9, "metal_dark")
            if (i + side) % 3 != 2:
                nb = neons[(i * 2 + side) % 4]
                w.fill(x, 6, z0 + 2, x, 6, z0 + 7, nb)
                s.light(((2.5 if side == 0 else 20.5), 6.5, z0 + 5), _col(nb, 0.5), 7)
            w.fill(x, 0, z0 + 10, x, 9, z0 + 12, "concrete")
            w.fill(x + (1 if side == 0 else -1), 0, z0 + 10, x + (1 if side == 0 else -1), 9, z0 + 11, "concrete")
    # Deckenlampen
    for i, z in enumerate(range(6, L, 10)):
        on = lit or i % 3 != 1
        w.fill(10, 10, z, 12, 10, z + 1, "lamp" if on else "lamp_off")
        if on:
            s.light((11, 9.0, z + 1), (0.75, 0.8, 0.9) if not lit else (1.1, 1.1, 1.15), 11)
    # Bänke + Pflanzen
    for z in range(15, L - 5, 22):
        w.box(9, 0.45, z, 13, 0.75, z + 1.2, "planks")
        w.box(9.2, 0, z + 0.1, 9.6, 0.45, z + 1.1, "metal_dark")
        w.box(12.4, 0, z + 0.1, 12.8, 0.45, z + 1.1, "metal_dark")
        w.fill(4, 0, z + 6, 4, 0, z + 6, "bricks")
        w.fill(4, 1, z + 6, 4, 2, z + 6, "tree_leaves")
        w.fill(18, 0, z + 6, 18, 0, z + 6, "bricks")
        w.fill(18, 1, z + 6, 18, 2, z + 6, "tree_leaves")
    # Notausgang hinten
    w.fill(10, 7, 1, 12, 7, 1, "exit")
    s.light((11, 7, 3), (0.1, 0.8, 0.35), 8)
    w.fill(9, 0, 1, 13, 4, 1, "door")
    s.env = dict(amb_sky=(0.20, 0.21, 0.28) if not lit else (0.5, 0.5, 0.52), amb_ground=(0.09, 0.09, 0.12) if not lit else (0.25, 0.25, 0.26),
                 fog=(0.02, 0.025, 0.04), fog_dens=0.028 if not lit else 0.01)
    return s


def _col(tile, f):
    c = {"neon_red": (1.0, 0.25, 0.3), "neon_blue": (0.25, 0.6, 1.0), "neon_pink": (1.0, 0.35, 0.8), "neon_green": (0.25, 1.0, 0.5)}[tile]
    return tuple(v * f for v in c)


def cctv_img(label, seed=0, h=60):
    r = np.random.default_rng(seed)
    a = (r.normal(0, 1, (h // 2, 48)) * 22 + 70).clip(0, 255)
    g = Image.fromarray(a.astype(np.uint8)).resize((96, h), Image.NEAREST)
    im = Image.merge("RGB", [g.point(lambda v: int(v * 0.6)), g, g.point(lambda v: int(v * 0.7))])
    d = ImageDraw.Draw(im)
    d.text((3, 2), label, font=ImageFont.truetype(MONO, 9), fill=(220, 255, 220))
    return im.resize((192, h * 2), Image.NEAREST)


def build_office(atlas):
    s = Set("office", atlas, (14, 10, 14), offset=(0, 1, 0))
    w = s.w
    w.fill(0, -1, 0, 13, -1, 13, "carpet")
    w.fill(0, 0, 0, 0, 8, 13, "plaster_green")
    w.fill(13, 0, 0, 13, 8, 13, "plaster_green")
    w.fill(0, 0, 0, 13, 8, 0, "plaster_green")
    w.fill(0, 8, 0, 13, 8, 13, "ceiling")
    w.fill(6, 8, 6, 7, 8, 7, "lamp_warm")
    s.light((6.5, 7, 6.5), (0.9, 0.7, 0.45), 11)
    # Monitorwand
    for r in range(2):
        for c in range(3):
            x0, y0 = 2.6 + c * 3.0, 3.0 + r * 1.9
            w.box(x0 - 0.1, y0 - 0.1, 1.0, x0 + 2.7, y0 + 1.7, 1.4, "black")
            s.wall_decal(f"mon{r}{c}", cctv_img(f"CAM 0{r * 3 + c + 1}", r * 3 + c), x0, y0, x0 + 2.6, y0 + 1.6, 1.42, emit=0.9)
    s.light((6.5, 4, 2.5), (0.15, 0.35, 0.2), 7)
    # Schreibtisch
    w.box(1.5, 1.05, 4.6, 11.5, 1.25, 6.4, "wood_desk")
    w.box(1.6, 0, 4.7, 2.0, 1.05, 6.3, "planks_dark")
    w.box(11.0, 0, 4.7, 11.4, 1.05, 6.3, "planks_dark")
    w.box(2.0, 0.2, 6.2, 11.0, 1.05, 6.3, "planks_dark")
    # Radio
    w.box(2.2, 1.25, 4.9, 4.4, 2.35, 5.8, "brown")
    grill = Image.new("RGBA", (22, 11), (60, 40, 26, 255))
    d = ImageDraw.Draw(grill)
    for x in range(1, 11, 2):
        for y in range(1, 10, 2):
            d.point((x, y), fill=(20, 14, 10, 255))
    d.rectangle([12, 2, 20, 5], fill=(255, 170, 60, 255))
    d.line([(16, 2), (16, 5)], fill=(160, 20, 10, 255))
    d.rectangle([13, 7, 15, 9], fill=(200, 190, 170, 255))
    d.rectangle([17, 7, 19, 9], fill=(200, 190, 170, 255))
    s.wall_decal("radio", grill.resize((176, 88), Image.NEAREST), 2.25, 1.3, 4.35, 2.3, 5.81, emit=0.15)
    w.box(4.0, 2.35, 5.3, 4.08, 3.6, 5.38, "metal")    # Antenne
    s.anchors["radio_dial"] = (3.9, 2.0, 5.85)
    # Telefon
    w.box(8.6, 1.25, 5.0, 10.0, 1.6, 5.9, "red")
    w.box(8.5, 1.6, 5.0, 10.1, 1.85, 5.35, "red_dark")
    s.anchors["phone"] = (9.3, 1.6, 5.4)
    # Thermoskanne, Papiere, Lampe
    w.box(1.55, 1.25, 4.8, 1.95, 2.1, 5.2, "plaster_green")
    w.box(5.0, 1.26, 5.2, 6.4, 1.28, 6.1, "white")
    w.box(10.4, 1.25, 4.8, 10.8, 2.6, 5.2, "metal_dark")
    w.box(10.0, 2.5, 4.8, 11.0, 2.8, 5.6, "metal_dark")
    s.light((10.5, 2.3, 5.6), (1.0, 0.75, 0.4), 6)
    # Stuhl hinter dem Tisch
    w.box(5.7, 0.9, 2.3, 7.3, 1.05, 3.6, "black")
    w.box(5.7, 1.05, 2.1, 7.3, 2.8, 2.3, "black")
    w.box(6.4, 0, 2.8, 6.6, 0.9, 3.1, "metal")
    # Regal + Tür
    w.fill(12, 0, 3, 12, 3, 6, "planks")
    for y in (1, 2):
        for z in range(3, 7):
            w.box(11.6, y + 0.05, z + 0.1, 11.95, y + 0.75, z + 0.8, "cardboard" if (y + z) % 2 else "navy")
    w.fill(0, 0, 9, 0, 2, 10, "door")
    s.env = dict(amb_sky=(0.38, 0.36, 0.33), amb_ground=(0.18, 0.17, 0.16), fog=(0.03, 0.03, 0.035), fog_dens=0.01)
    s.anchors.update(walter_seat=(6.5, 0.0, 3.0), desk_top=1.25)
    return s


def build_service(atlas):
    s = Set("service", atlas, (12, 10, 32), offset=(0, 1, 0))
    w = s.w
    w.fill(0, -1, 0, 11, -1, 31, "concrete_dark")
    w.fill(0, 0, 0, 0, 8, 31, "concrete")
    w.fill(11, 0, 0, 11, 8, 31, "concrete")
    w.fill(0, 8, 0, 11, 8, 31, "concrete_dark")
    w.fill(0, 0, 1, 11, 8, 1, "concrete")
    # Tür Lager 3
    w.fill(4, 0, 1, 6, 3, 1, "door")
    w.box(4.0, 0.0, 1.0, 7.0, 0.1, 1.1, "black")
    sign = pixel_text("STORAGE 3", (20, 20, 20, 255), (226, 222, 210, 255), h=11, up=10)
    s.wall_decal("sign", sign, 3.6, 4.3, 7.4, 5.2, 2.02, emit=0.1)
    # Riegel + Vorhängeschloss (außen!)
    w.box(5.2, 2.6, 2.0, 7.4, 2.8, 2.15, "metal")
    w.box(6.9, 2.2, 2.05, 7.3, 2.6, 2.25, "yellow")
    # Lichtspalt unter der Tür
    w.box(4.05, 0.0, 2.0, 6.95, 0.07, 2.04, "light_strip")
    s.light((5.5, 0.3, 2.6), (1.0, 0.55, 0.25), 3.5)
    # Käfiglampe
    w.box(5.2, 6.6, 1.95, 5.8, 7.1, 2.4, "lamp_warm")
    for x in (5.15, 5.45, 5.75):
        w.box(x, 6.55, 2.38, x + 0.06, 7.15, 2.45, "metal_dark")
    s.light((5.5, 6.3, 3.0), (0.8, 0.62, 0.4), 9)
    # Rohre + Kisten
    w.box(1, 7.2, 0, 1.5, 7.7, 31, "metal")
    w.box(2, 7.3, 0, 2.3, 7.6, 31, "metal_dark")
    w.box(9.3, 7.2, 0, 9.8, 7.7, 31, "red_dark")
    for (x, z, h) in ((1, 6, 2), (2, 6, 1), (9, 9, 3), (1, 12, 1)):
        w.fill(x, 0, z, x, h - 1, z, "cardboard")
    s.light((5.5, 6, 18), (0.25, 0.28, 0.35), 10)
    s.env = dict(amb_sky=(0.22, 0.21, 0.2), amb_ground=(0.1, 0.1, 0.1), fog=(0.015, 0.015, 0.02), fog_dens=0.03)
    s.anchors.update(door=(5.5, 0, 2.0))
    return s


def build_atrium(atlas):
    s = Set("atrium", atlas, (30, 20, 44), offset=(0, 1, 0))
    w = s.w
    for z in range(44):
        for x in range(30):
            w.set(x, -1, z, "floor" if (x + z) % 2 else "floor_dark")
    w.fill(0, 0, 0, 0, 18, 43, "plaster")
    w.fill(29, 0, 0, 29, 18, 43, "plaster")
    w.fill(0, 0, 0, 29, 18, 0, "plaster")
    w.fill(0, 18, 0, 29, 18, 43, "ceiling")
    w.fill(10, 18, 8, 19, 18, 20, "glass")
    # Galerie oben
    w.fill(1, 7, 1, 28, 7, 12, "floor")
    for x in range(2, 28, 7):
        w.fill(x, 8, 1, x + 5, 12, 1, "shutter")
        w.fill(x, 13, 1, x + 5, 13, 1, "metal_dark")
    w.fill(1, 8, 12, 28, 8, 12, "glass_clear")
    w.box(1, 9.0, 11.8, 28, 9.15, 12.2, "metal")
    for x in (3, 10, 20, 26):
        w.fill(x, 0, 12, x, 6, 12, "concrete")
    # Läden unten
    for z in range(16, 42, 9):
        w.fill(1, 0, z, 1, 4, z + 6, "shutter")
        w.fill(28, 0, z, 28, 4, z + 6, "shutter")
        w.fill(1, 5, z, 1, 5, z + 6, "metal_dark")
        w.fill(28, 5, z, 28, 5, z + 6, "metal_dark")
    # Rolltreppe (von z=30 unten nach z=13 oben, x 12..14.5)
    steps = 16
    x0, x1 = 12.0, 14.6
    for i in range(steps):
        z = 30 - i
        y = i * 0.5
        w.box(x0, 0, z - 1, x1, y + 0.5, z, "step", tiles={"py": "step", "pz": "metal_dark"})
    for i in range(16, 18):
        w.box(x0, 0, 30 - i - 1, x1, 8.0, 30 - i, "step")
    # Balustraden als schräge Quader (Steigung 0.5)
    ang = math.atan2(8.0, 16.0)
    L = math.hypot(16.0, 8.0)
    for xx in (x0 - 0.15, x1 + 0.15):
        cz, cy = 30 - 8.0, 4.0
        s.rot_box((xx, cy + 0.9, cz), (0.25, 1.6, L), ang, "glass_clear", transparent=True)
        s.rot_box((xx, cy + 1.8, cz), (0.4, 0.22, L + 0.4), ang, "rubber")
        s.rot_box((xx, cy + 0.05, cz), (0.32, 0.5, L), ang, "metal")
    w.box(x0 - 0.35, 0, 30, x1 + 0.35, 0.6, 31.5, "metal")
    s.anchors.update(mia_step=(13.3, 3.5, 23.5), bunny_step=(13.0, 3.0, 24.5))
    # Licht
    s.light((14, 16, 14), (0.25, 0.3, 0.4), 22)
    s.light((14, 6, 30), (0.4, 0.42, 0.5), 10)
    s.light((25, 13, 4), (0.15, 0.7, 0.35), 8)
    w.fill(24, 15, 1, 26, 15, 1, "exit")
    for z in (20, 34):
        w.fill(4, 0, z, 4, 0, z, "bricks"); w.fill(4, 1, z, 4, 2, z, "tree_leaves")
        w.fill(25, 0, z, 25, 0, z, "bricks"); w.fill(25, 1, z, 25, 2, z, "tree_leaves")
    s.env = dict(amb_sky=(0.26, 0.28, 0.36), amb_ground=(0.11, 0.11, 0.14), fog=(0.03, 0.035, 0.05), fog_dens=0.018)
    return s


def build_entrance(atlas, dawn=False):
    s = Set("entrance" + ("_dawn" if dawn else ""), atlas, (80, 30, 80), offset=(40, 2, 50))
    w = s.w
    # innen
    for z in range(0, 14):
        for x in range(-12, 13):
            w.set(x, -1, z, "floor" if (x + z) % 2 else "floor_dark")
    w.fill(-12, 0, 0, -12, 9, 13, "plaster")
    w.fill(12, 0, 0, 12, 9, 13, "plaster")
    w.fill(-12, 9, 0, 12, 9, 13, "ceiling")
    # Glasfront z=0
    w.fill(-12, 0, 0, 12, 9, 0, "concrete")
    w.fill(-7, 0, 0, 7, 6, 0, "glass_clear")
    w.fill(-8, 0, 0, -8, 6, 0, "metal")
    w.fill(8, 0, 0, 8, 6, 0, "metal")
    w.fill(-8, 7, 0, 8, 7, 0, "metal")
    w.box(-1.4, 2.4, 0.4, -1.2, 4.0, 0.6, "metal")
    w.box(1.2, 2.4, 0.4, 1.4, 4.0, 0.6, "metal")
    sign = pixel_text("MAIN ENTRANCE", (230, 236, 255, 255), (30, 34, 44, 255), h=11, up=10)
    s.wall_decal("sign", sign, -4.5, 7.5, 4.5, 8.6, 0.52, emit=0.4)
    # außen
    w.fill(-40, -1, -30, 40, -1, -1, "asphalt")
    for x in range(-30, 31, 5):
        w.fill(x, -1, -14, x, -1, -8, "asphalt_line")
    for x in (-14, 6, 22):
        lamp_post(s, x, -10, on=not dawn)
    car(s, -6, -18, "red")
    tree(s, -24, 0, -24, 6)
    tree(s, 26, 0, -22, 5)
    for x in range(-40, 41, 2):
        w.fill(x, 0, -30, x, 1 + (abs(x * 7) % 3), -30, "tree_leaves")
    if dawn:
        sk = sky_img((60, 100, 170), (250, 170, 110), stars=False)
        s.env = dict(amb_sky=(0.6, 0.58, 0.6), amb_ground=(0.32, 0.28, 0.26), fog=(0.9, 0.66, 0.5), fog_dens=0.012, clear=(0.9, 0.66, 0.5), emit_gain=0.7)
        sun = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        ImageDraw.Draw(sun).rectangle([0, 0, 7, 7], fill=(255, 236, 170, 255))
        s.decal("sun", sun, [(10, 2, -60), (18, 2, -60), (18, 10, -60), (10, 10, -60)], emit=1.5)
        s.light((0, 6, 6), (0.6, 0.5, 0.4), 14)
    else:
        sk = sky_img((4, 6, 14), (22, 28, 50))
        s.env = dict(amb_sky=(0.26, 0.29, 0.42), amb_ground=(0.11, 0.11, 0.15), fog=(0.07, 0.08, 0.14), fog_dens=0.016, clear=(0.07, 0.08, 0.14))
        s.light((0, 7.5, 5), (0.35, 0.37, 0.45), 12)
        s.light((0, 2.2, 1.5), (0.35, 0.3, 0.25), 5)
    s.decal("sky", sk, [(-120, -10, -62), (120, -10, -62), (120, 70, -62), (-120, 70, -62)], emit=1.0, transparent=False)
    if not dawn:
        s.light((0, 4.0, -3.5), (0.55, 0.6, 0.8), 7)
    s.anchors.update(outside=(0, 0, -0.9))
    return s


def card_img(rules, reveal, hl, scale=1):
    """Walters Karteikarte (hochauflösend)."""
    from PIL import ImageFilter
    W, H = 900, 1100
    im = Image.new("RGBA", (W, H), (236, 226, 196, 255))
    a = np.asarray(im).astype(np.int16)
    a[..., :3] += np.random.default_rng(5).integers(-8, 9, (H, W))[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for y in range(220, H - 30, 60):
        d.line([(30, y), (W - 30, y)], fill=(150, 175, 205, 255), width=3)
    d.line([(30, 180), (W - 30, 180)], fill=(200, 80, 80, 255), width=4)
    fh = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf", 84)
    fr = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf", 50)
    fb = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf", 56)
    ink = (26, 32, 78, 255)
    d.text((60, 60), "THE RULES", font=fh, fill=ink)
    d.text((W - 260, 110), "– Walter", font=fr, fill=ink)
    y = 228
    for i, r in enumerate(rules):
        words, lines, cur = r.split(), [], ""
        for wd in words:
            t = (cur + " " + wd).strip()
            if d.textlength(t, font=fr) < W - 200:
                cur = t
            else:
                lines.append(cur)
                cur = wd
        lines.append(cur)
        hgt = len(lines) * 60
        if i < reveal:
            al = 255 if (hl is None or hl == i) else 110
            if hl == i:
                hlim = Image.new("RGBA", im.size, 0)
                ImageDraw.Draw(hlim).rectangle([110, y + 4, W - 40, y + hgt + 6], fill=(255, 226, 40, 150))
                im = Image.alpha_composite(im, hlim)
                d = ImageDraw.Draw(im)
                d.ellipse([32, y - 4, 104, y + 64], outline=(200, 25, 25, 255), width=6)
            d.text((50, y - 4), f"{i + 1}.", font=fb, fill=ink[:3] + (al,))
            for j, ln in enumerate(lines):
                d.text((120, y + j * 60), ln, font=fr, fill=ink[:3] + (al,))
        y += hgt + 60
    return im
