# -*- coding: utf-8 -*-
"""Eigene 16x16-Pixeltexturen (prozedural) für den Blocklook."""
import numpy as np
from PIL import Image, ImageDraw

T = 16


def _rng(name):
    return np.random.default_rng(abs(hash(name)) % (2 ** 32))


def noise_tile(base, var=14, seed=0, spots=None):
    r = np.random.default_rng(seed)
    a = np.zeros((T, T, 3), np.int16)
    for c in range(3):
        a[..., c] = base[c]
    n = r.integers(-var, var + 1, (T, T))
    a += n[..., None]
    if spots:
        col, k = spots
        for _ in range(k):
            x, y = r.integers(0, T, 2)
            a[y, x] = col
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def tile_floor(c1=(178, 176, 168), c2=(150, 148, 142), grout=(96, 94, 90), seed=1):
    im = noise_tile(c1, 6, seed)
    d = ImageDraw.Draw(im)
    d.rectangle([8, 0, 15, 7], fill=c2)
    d.rectangle([0, 8, 7, 15], fill=c2)
    a = np.asarray(im).astype(np.int16)
    a += np.random.default_rng(seed + 9).integers(-6, 7, (T, T))[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.line([(0, 0), (15, 0)], fill=grout)
    d.line([(0, 0), (0, 15)], fill=grout)
    return im


def tile_bricks(c=(120, 116, 110), mortar=(70, 68, 66), seed=2):
    im = noise_tile(c, 10, seed)
    d = ImageDraw.Draw(im)
    for y in (0, 4, 8, 12):
        d.line([(0, y), (15, y)], fill=mortar)
        off = 0 if (y // 4) % 2 == 0 else 4
        for x in range(off, 16, 8):
            d.line([(x, y), (x, y + 3)], fill=mortar)
    return im


def tile_planks(c=(132, 96, 58), seed=3):
    im = noise_tile(c, 8, seed)
    d = ImageDraw.Draw(im)
    dark = tuple(int(v * 0.65) for v in c)
    for y in (3, 7, 11, 15):
        d.line([(0, y), (15, y)], fill=dark)
    r = np.random.default_rng(seed)
    for y in (0, 4, 8, 12):
        x = int(r.integers(2, 14))
        d.line([(x, y), (x, y + 2)], fill=dark)
    return im


def tile_metal(c=(118, 122, 128), seed=4, rivets=True):
    im = noise_tile(c, 5, seed)
    d = ImageDraw.Draw(im)
    lt = tuple(min(255, v + 25) for v in c)
    dk = tuple(int(v * 0.6) for v in c)
    d.line([(0, 0), (15, 0)], fill=lt)
    d.line([(0, 15), (15, 15)], fill=dk)
    if rivets:
        for p in ((2, 2), (13, 2), (2, 13), (13, 13)):
            d.point(p, fill=dk)
    return im


def tile_shutter(c=(92, 96, 104), seed=5):
    im = noise_tile(c, 4, seed)
    d = ImageDraw.Draw(im)
    for y in range(0, 16, 3):
        d.line([(0, y), (15, y)], fill=tuple(int(v * 0.6) for v in c))
        d.line([(0, y + 1), (15, y + 1)], fill=tuple(min(255, v + 18) for v in c))
    return im


def tile_glass(seed=6):
    im = Image.new("RGBA", (T, T), (150, 200, 230, 55))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 15, 15], outline=(200, 230, 250, 140))
    d.line([(3, 12), (12, 3)], fill=(255, 255, 255, 90))
    d.line([(5, 13), (13, 5)], fill=(255, 255, 255, 60))
    return im


def tile_glass_clear():
    im = Image.new("RGBA", (T, T), (170, 210, 235, 30))
    d = ImageDraw.Draw(im)
    d.line([(2, 13), (7, 8)], fill=(255, 255, 255, 70))
    return im


def tile_solid(c, var=4, seed=7):
    return noise_tile(c, var, seed)


def tile_grass_top(seed=8):
    return noise_tile((70, 120, 50), 16, seed, spots=((90, 150, 60), 20))


def tile_grass_side(seed=9):
    im = noise_tile((110, 80, 56), 12, seed)
    a = np.asarray(im).copy()
    r = np.random.default_rng(seed)
    for x in range(T):
        h = 3 + int(r.integers(0, 3))
        a[:h, x] = (70 + r.integers(-10, 10), 120 + r.integers(-10, 10), 50)
    return Image.fromarray(a.astype(np.uint8))


def tile_leaves(seed=10):
    im = noise_tile((40, 86, 36), 18, seed, spots=((22, 50, 20), 30))
    return im


def tile_log(seed=11):
    im = noise_tile((96, 74, 48), 8, seed)
    d = ImageDraw.Draw(im)
    for x in (2, 6, 10, 13):
        d.line([(x, 0), (x, 15)], fill=(70, 52, 32))
    return im


def tile_asphalt(seed=12, line=False):
    im = noise_tile((46, 48, 52), 10, seed, spots=((70, 72, 76), 14))
    if line:
        d = ImageDraw.Draw(im)
        d.rectangle([6, 0, 9, 15], fill=(200, 196, 170))
    return im


def tile_emissive(c, pattern=None, seed=13):
    im = noise_tile(c, 6, seed)
    d = ImageDraw.Draw(im)
    if pattern == "lamp":
        d.rectangle([0, 0, 15, 15], outline=tuple(int(v * 0.7) for v in c))
        d.rectangle([2, 2, 13, 13], fill=tuple(min(255, v + 20) for v in c))
    elif pattern == "screen":
        r = np.random.default_rng(seed)
        a = np.asarray(im).astype(np.int16)
        a = a + r.integers(-40, 40, (T, T))[..., None]
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 15, 15], outline=(20, 30, 20))
    return im


def tile_carpet(c=(120, 36, 40), seed=14):
    im = noise_tile(c, 8, seed)
    d = ImageDraw.Draw(im)
    for i in range(0, 16, 4):
        d.point((i, i), fill=tuple(int(v * 0.7) for v in c))
        d.point((15 - i, i), fill=tuple(int(v * 0.7) for v in c))
    return im


def tile_door(c=(96, 104, 112), seed=15):
    im = tile_metal(c, seed, rivets=False)
    d = ImageDraw.Draw(im)
    d.rectangle([2, 2, 13, 13], outline=tuple(int(v * 0.7) for v in c))
    return im


def tile_step(seed=16):
    im = noise_tile((120, 124, 130), 4, seed)
    d = ImageDraw.Draw(im)
    for x in range(0, 16, 2):
        d.line([(x, 0), (x, 15)], fill=(80, 84, 90))
    d.line([(0, 15), (15, 15)], fill=(200, 170, 40))
    return im


def tile_ceiling(seed=17):
    im = noise_tile((88, 88, 92), 5, seed, spots=((70, 70, 74), 10))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 15, 15], outline=(70, 70, 74))
    return im


def tile_cardboard(seed=18):
    im = noise_tile((160, 120, 74), 8, seed)
    d = ImageDraw.Draw(im)
    d.line([(0, 7), (15, 7)], fill=(190, 170, 120))
    return im


def tile_plaster(c=(150, 142, 128), seed=19):
    return noise_tile(c, 7, seed, spots=(tuple(int(v * 0.85) for v in c), 12))


def tile_concrete(c=(108, 108, 106), seed=20):
    im = noise_tile(c, 9, seed, spots=(tuple(int(v * 0.75) for v in c), 16))
    return im


def tile_cloud(seed=21):
    return noise_tile((235, 240, 246), 4, seed)


def tile_water(seed=22):
    im = noise_tile((36, 52, 74), 8, seed)
    d = ImageDraw.Draw(im)
    d.line([(2, 4), (8, 4)], fill=(90, 110, 140))
    d.line([(7, 11), (14, 11)], fill=(90, 110, 140))
    return im


def register(atlas):
    A = atlas.add
    A("floor", tile_floor())
    A("floor_dark", tile_floor((110, 108, 104), (92, 90, 88), (60, 58, 56), 31))
    A("floor_check", tile_floor((220, 218, 210), (40, 40, 44), (30, 30, 32), 32))
    A("bricks", tile_bricks())
    A("bricks_red", tile_bricks((140, 70, 56), (80, 60, 54), 33))
    A("planks", tile_planks())
    A("planks_dark", tile_planks((84, 58, 36), 34))
    A("metal", tile_metal())
    A("metal_dark", tile_metal((60, 64, 70), 35))
    A("shutter", tile_shutter())
    A("glass", tile_glass())
    A("glass_clear", tile_glass_clear())
    A("grass_top", tile_grass_top())
    A("grass_side", tile_grass_side())
    A("dirt", noise_tile((110, 80, 56), 12, 36))
    A("leaves", tile_leaves())
    A("log", tile_log())
    A("asphalt", tile_asphalt())
    A("asphalt_line", tile_asphalt(37, line=True))
    A("carpet", tile_carpet())
    A("door", tile_door())
    A("door_rust", tile_door((110, 74, 52), 38))
    A("step", tile_step())
    A("ceiling", tile_ceiling())
    A("cardboard", tile_cardboard())
    A("plaster", tile_plaster())
    A("plaster_green", tile_plaster((96, 112, 100), 39))
    A("concrete", tile_concrete())
    A("concrete_dark", tile_concrete((64, 66, 70), 40))
    A("water", tile_water())
    A("white", tile_solid((236, 236, 232), 3, 41))
    A("black", tile_solid((18, 18, 20), 3, 42))
    A("red", tile_solid((170, 30, 30), 6, 43))
    A("red_dark", tile_solid((110, 20, 20), 6, 44))
    A("yellow", tile_solid((230, 190, 30), 8, 45))
    A("navy", tile_solid((34, 42, 66), 5, 46))
    A("grey", tile_solid((120, 120, 124), 6, 47))
    A("rubber", tile_solid((26, 26, 28), 3, 48))
    A("wood_desk", tile_planks((96, 64, 40), 49))
    A("brown", tile_solid((92, 62, 40), 6, 50))
    A("cream", tile_solid((220, 210, 180), 5, 51))
    # leuchtende Kacheln
    A("lamp", tile_emissive((250, 248, 236), "lamp"), 1.6)
    A("lamp_warm", tile_emissive((255, 200, 120), "lamp"), 1.6)
    A("lamp_off", tile_emissive((70, 70, 72), "lamp"), 0.0)
    A("neon_red", tile_solid((255, 60, 80), 8, 52), 2.2)
    A("neon_blue", tile_solid((60, 150, 255), 8, 53), 2.0)
    A("neon_pink", tile_solid((255, 90, 200), 8, 54), 2.0)
    A("neon_green", tile_solid((60, 255, 130), 8, 55), 2.0)
    A("neon_off", tile_solid((60, 24, 28), 4, 56), 0.0)
    A("exit", tile_solid((40, 220, 110), 6, 57), 2.2)
    A("screen", tile_emissive((90, 150, 100), "screen"), 1.1)
    A("dial", tile_solid((255, 160, 50), 6, 58), 1.8)
    A("window_lit", tile_emissive((255, 196, 110), "lamp"), 1.3)
    A("window_dark", tile_glass())
    A("light_strip", tile_solid((255, 190, 110), 4, 59), 2.4)
    A("sky_moon", tile_solid((230, 236, 255), 2, 60), 2.0)
