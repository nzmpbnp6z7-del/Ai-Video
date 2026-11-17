# -*- coding: utf-8 -*-
"""Nachbearbeitung: Bloom, Vignette, Korn, Farbstich."""
import numpy as np
from PIL import Image, ImageFilter

_cache = {}


def vignette(W, H, strength=0.55):
    k = (W, H, strength)
    if k not in _cache:
        y, x = np.mgrid[0:H, 0:W]
        d = np.sqrt(((x - W / 2) / (W * 0.62)) ** 2 + ((y - H / 2) / (H * 0.6)) ** 2)
        _cache[k] = np.clip(1.05 - d ** 2.2 * strength, 0.25, 1.0).astype(np.float32)
    return _cache[k]


def grain(W, H, i):
    k = ("g", W, H, i % 4)
    if k not in _cache:
        r = np.random.default_rng(i % 4)
        _cache[k] = np.repeat(np.repeat(r.normal(0, 2.2, (H // 3 + 1, W // 3 + 1)), 3, 0), 3, 1)[:H, :W].astype(np.float32)
    return _cache[k]


def bloom(arr, thresh=170, strength=0.55, radius=10):
    H, W, _ = arr.shape
    small = Image.fromarray(arr).resize((W // 4, H // 4), Image.BILINEAR)
    a = np.asarray(small).astype(np.float32)
    lum = a.max(axis=2, keepdims=True)
    b = np.clip(a * np.clip((lum - thresh) / (255 - thresh), 0, 1), 0, 255).astype(np.uint8)
    b = Image.fromarray(b).filter(ImageFilter.GaussianBlur(radius)).resize((W, H), Image.BILINEAR)
    return np.asarray(b).astype(np.float32) * strength


def finish(arr, fi=0, grade=(1, 1, 1), bloom_s=0.55, vig=0.55, flash=0.0, dark=1.0):
    H, W, _ = arr.shape
    out = arr.astype(np.float32)
    if bloom_s > 0:
        out += bloom(arr, strength=bloom_s)
    out *= np.array(grade, np.float32)[None, None, :]
    out *= (vignette(W, H, vig) * dark)[..., None]
    if flash > 0:
        out += flash * 150
    out += grain(W, H, fi // 2)[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)
