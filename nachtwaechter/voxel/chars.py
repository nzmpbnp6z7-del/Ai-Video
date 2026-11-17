# -*- coding: utf-8 -*-
"""Blockfiguren: eigene Skins (Pixel-Art), Teile mit Gelenken, Gesichtsvarianten."""
import math, hashlib
import numpy as np
from PIL import Image, ImageDraw
from engine import Mesh, FACES, UVQ, translate, rot_x, rot_y, rot_z, scale

P = 1 / 16          # ein "Pixel" in Blockeinheiten
TX = 2              # Texel pro Pixel-Einheit


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])


def sseed(*k):
    return int(hashlib.md5(repr(k).encode()).hexdigest()[:6], 16)


def speckle(im, amount=6, seed=0):
    a = np.asarray(im).astype(np.int16)
    r = np.random.default_rng(seed)
    a[..., :3] += r.integers(-amount, amount + 1, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), im.mode)


class Part:
    def __init__(self, name, pivot, lo, hi, parent=None, skip=()):
        self.name, self.pivot, self.lo, self.hi, self.parent, self.skip = name, pivot, lo, hi, parent, skip

    def face_size(self, f):
        sx, sy, sz = (self.hi[i] - self.lo[i] for i in range(3))
        if f in ("pz", "nz"):
            return sx, sy
        if f in ("px", "nx"):
            return sz, sy
        return sx, sz


class Character:
    """Teile + Skin-Atlas. paint(part, face, img) bemalt eine Fläche."""

    def __init__(self, name, parts, painter, face_painter, size=1.0):
        self.name, self.parts, self.painter, self.face_painter, self.size = name, parts, painter, face_painter, size
        self.rects = {}
        imgs = {}
        for p in parts:
            for f in FACES:
                if f in p.skip:
                    continue
                w, h = p.face_size(f)
                im = Image.new("RGBA", (max(1, int(round(w * TX))), max(1, int(round(h * TX)))), (255, 0, 255, 255))
                painter(p.name, f, im)
                imgs[(p.name, f)] = im
        # einfaches Regal-Packing in 256er Atlas
        S = 256
        atlas = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        x = y = rowh = 0
        for k, im in sorted(imgs.items(), key=lambda kv: -kv[1].size[1]):
            w, h = im.size
            if x + w + 1 > S:
                x, y, rowh = 0, y + rowh + 1, 0
            atlas.paste(im, (x, y))
            self.rects[k] = (x, y, w, h)
            x += w + 1
            rowh = max(rowh, h)
        self.skin = atlas
        self.S = S
        self.meshes = {p.name: self._part_mesh(p) for p in parts}

    def _part_mesh(self, p):
        m = Mesh()
        lo = np.array(p.lo, float) * P
        hi = np.array(p.hi, float) * P
        size = hi - lo
        for f, (n, corners) in FACES.items():
            if f in p.skip:
                continue
            x, y, w, h = self.rects[(p.name, f)]
            e = 0.02
            u0, v0, u1, v1 = (x + e) / self.S, (y + e) / self.S, (x + w - e) / self.S, (y + h - e) / self.S
            cs = [tuple(lo + np.array(c) * size) for c in corners]
            uvs = [(u0 if q[0] == 0 else u1, v0 if q[1] == 0 else v1) for q in UVQ]
            m.add_quad(cs, n, uvs)
        return m.array()

    def face_rect(self):
        return self.rects[("head", "pz")]

    def face_image(self, eyes="open", mouth="0"):
        x, y, w, h = self.face_rect()
        im = Image.new("RGBA", (w, h), (0, 0, 0, 255))
        self.painter("head", "pz", im)
        self.face_painter(im, eyes, mouth)
        return im

    # ---- Pose -> Modellmatrizen
    def matrices(self, pose):
        root = translate(*pose.get("pos", (0, 0, 0))) @ rot_y(pose.get("yaw", 0.0)) @ scale(self.size, self.size, self.size)
        root = root @ rot_x(pose.get("lean", 0.0)) @ rot_z(pose.get("roll", 0.0))
        out = {}
        for p in self.parts:
            pv = np.array(p.pivot, float) * P
            rx, ry, rz = pose.get(p.name, (0, 0, 0))
            local = translate(*pv) @ rot_y(ry) @ rot_x(rx) @ rot_z(rz)
            parent = out[p.parent] @ translate(*(-np.array(self._pivot(p.parent)) * P)) if p.parent else root
            out[p.name] = parent @ local
        return out

    def _pivot(self, name):
        for p in self.parts:
            if p.name == name:
                return p.pivot
        return (0, 0, 0)


def humanoid(extra=(), arm_w=4, leg_h=12, torso_h=12, arm_len=12, head=8, skip_head_front=False, slim=False):
    th = leg_h + torso_h
    aw = 3 if slim else arm_w
    parts = [
        Part("body", (0, leg_h, 0), (-4, 0, -2), (4, torso_h, 2)),
        Part("head", (0, th, 0), (-head / 2, 0, -head / 2), (head / 2, head, head / 2), parent="body"),
        Part("arm_r", (-4 - aw / 2, th - 2, 0), (-aw / 2, -arm_len + 2, -2), (aw / 2, 2, 2), parent="body"),
        Part("arm_l", (4 + aw / 2, th - 2, 0), (-aw / 2, -arm_len + 2, -2), (aw / 2, 2, 2), parent="body"),
        Part("leg_r", (-2, leg_h, 0), (-2, -leg_h, -2), (2, 0, 2)),
        Part("leg_l", (2, leg_h, 0), (-2, -leg_h, -2), (2, 0, 2)),
    ]
    parts += list(extra)
    return parts


# =====================================================================
#  Skins
# =====================================================================
SKIN = (226, 178, 146)


def fill(im, c):
    ImageDraw.Draw(im).rectangle([0, 0, im.size[0], im.size[1]], fill=c)


def eyes_mouth(im, eyes, mouth, skin, iris=(60, 40, 30), ey=7, big=False, mouth_y=12, lip=(150, 70, 70)):
    d = ImageDraw.Draw(im)
    w = im.size[0]
    lx, rx = (3, 10) if not big else (2, 10)
    ew = 3 if not big else 4
    eh = 2 if not big else 3
    for x in (lx, rx):
        if eyes in ("open", "wide", "serious"):
            h = eh + (1 if eyes == "wide" else 0)
            yy = ey - (1 if eyes == "wide" else 0)
            d.rectangle([x, yy, x + ew - 1, yy + h - 1], fill=(245, 245, 245))
            px = x + (1 if x == lx else 0)
            d.rectangle([px, yy, px + (1 if not big else 2) - (0 if eyes != "wide" else 1), yy + h - 1], fill=iris)
            if eyes == "serious":
                d.line([(x, yy - 1), (x + ew - 1, yy - 1)], fill=shade(skin, 0.55))
        elif eyes == "closed":
            d.line([(x, ey + 1), (x + ew - 1, ey + 1)], fill=shade(skin, 0.45))
        elif eyes == "black":
            d.rectangle([x, ey - 1, x + ew - 1, ey + eh], fill=(4, 4, 4))
            d.point((x + ew - 1, ey - 1), fill=(255, 230, 230))
    cx = w // 2
    if mouth == "0":
        d.line([(cx - 2, mouth_y), (cx + 1, mouth_y)], fill=lip)
    elif mouth == "1":
        d.rectangle([cx - 2, mouth_y, cx + 1, mouth_y + 1], fill=(50, 14, 14))
    elif mouth == "2":
        d.rectangle([cx - 2, mouth_y - 1, cx + 1, mouth_y + 2], fill=(50, 14, 14))
        d.line([(cx - 2, mouth_y - 1), (cx + 1, mouth_y - 1)], fill=(230, 226, 214))
    elif mouth == "grin":
        d.rectangle([1, mouth_y - 1, w - 2, mouth_y + 2], fill=(20, 4, 4))
        for x in range(1, w - 1, 2):
            d.point((x, mouth_y - 1), fill=(236, 232, 214))
            d.point((x + 1, mouth_y + 2), fill=(220, 214, 196))
    elif mouth == "smile":
        d.line([(cx - 3, mouth_y), (cx + 2, mouth_y)], fill=lip)
        d.point((cx - 3, mouth_y - 1), fill=lip)
        d.point((cx + 2, mouth_y - 1), fill=lip)


# ---------------------------------------------------------------- Jonas
def jonas_paint(part, face, im):
    w, h = im.size
    d = ImageDraw.Draw(im)
    hair = (52, 36, 26)
    jacket = (30, 36, 52)
    if part == "head":
        fill(im, SKIN)
        if face == "py":
            fill(im, hair)
        elif face == "nz":
            fill(im, hair)
            d.rectangle([0, h - 3, w, h], fill=SKIN)
        elif face in ("px", "nx"):
            d.rectangle([0, 0, w, 5], fill=hair)
            d.rectangle([0 if face == "nx" else w - 6, 0, 6 if face == "nx" else w, 8], fill=hair)
            d.rectangle([w // 2 - 1, 7, w // 2, 9], fill=shade(SKIN, 0.8))
        elif face == "pz":
            d.rectangle([0, 0, w, 3], fill=hair)
            for x in range(0, w, 3):
                d.rectangle([x, 4, x + 1, 4 + (x % 2)], fill=hair)
            d.rectangle([0, 0, 1, 7], fill=hair)
            d.rectangle([w - 2, 0, w, 7], fill=hair)
            d.rectangle([7, 9, 8, 10], fill=shade(SKIN, 0.85))
        elif face == "ny":
            fill(im, shade(SKIN, 0.8))
    elif part == "body":
        fill(im, jacket)
        if face == "pz":
            d.rectangle([5, 0, w - 6, 5], fill=(90, 94, 104))     # Hoodie
            d.line([(w // 2, 5), (w // 2, h)], fill=(14, 16, 24))
            d.rectangle([w - 6, 8, w - 2, 10], fill=(214, 176, 40))  # Abzeichen
            d.line([(6, 2), (6, 7)], fill=(210, 210, 214))
            d.line([(w - 7, 2), (w - 7, 7)], fill=(210, 210, 214))
        if face == "nz":
            d.rectangle([0, 6, w, 9], fill=(196, 200, 206))      # Reflexstreifen
            d.rectangle([0, 0, w, 3], fill=(90, 94, 104))
        if face in ("px", "nx", "pz", "nz"):
            d.rectangle([0, h - 3, w, h], fill=(22, 24, 30))
    elif part.startswith("arm"):
        fill(im, jacket)
        if face == "ny":
            fill(im, SKIN)
        else:
            d.rectangle([0, h - 4, w, h], fill=SKIN)
            d.rectangle([0, 9, w, 11], fill=(196, 200, 206))
    elif part.startswith("leg"):
        fill(im, (40, 44, 54))
        d.rectangle([0, h - 3, w, h], fill=(18, 18, 20))
        if face == "ny":
            fill(im, (18, 18, 20))
    elif part == "torch":
        fill(im, (60, 60, 64))
        if face == "pz":
            fill(im, (255, 250, 220))
    im.paste(speckle(im, 4, sseed(part, face)))


def jonas_face(im, eyes, mouth):
    eyes_mouth(im, eyes, mouth, SKIN, iris=(70, 46, 30))


def make_jonas():
    torch = Part("torch", (-6, 13, 1), (-1, -1.5, -1), (1, 1.5, 5), parent="arm_r")
    return Character("jonas", humanoid([torch]), jonas_paint, jonas_face)


# ---------------------------------------------------------------- Walter
W_SKIN = (206, 156, 128)


def walter_paint(part, face, im):
    w, h = im.size
    d = ImageDraw.Draw(im)
    grey = (178, 178, 176)
    navy = (34, 44, 70)
    if part == "head":
        fill(im, W_SKIN)
        if face == "py":
            fill(im, grey)
        elif face == "nz":
            fill(im, grey)
            d.rectangle([0, h - 3, w, h], fill=W_SKIN)
        elif face in ("px", "nx"):
            d.rectangle([0, 0, w, 6], fill=grey)
            d.rectangle([w // 2 - 1, 7, w // 2, 10], fill=shade(W_SKIN, 0.8))
        elif face == "pz":
            d.rectangle([0, 0, w, 2], fill=grey)
            d.rectangle([0, 0, 0, 8], fill=grey)
            d.rectangle([w - 1, 0, w, 8], fill=grey)
            d.rectangle([7, 8, 8, 10], fill=shade(W_SKIN, 0.82))
            d.line([(2, 4), (w - 3, 4)], fill=shade(W_SKIN, 0.8))   # Stirnfalte
            d.line([(3, 13), (3, 14)], fill=shade(W_SKIN, 0.78))
            d.line([(12, 13), (12, 14)], fill=shade(W_SKIN, 0.78))
    elif part == "body":
        fill(im, navy)
        if face == "pz":
            d.polygon([(5, 0), (w // 2, 6), (w - 6, 0)], fill=(150, 170, 196))
            d.line([(w // 2, 2), (w // 2, 8)], fill=(20, 20, 26))
            for y in (9, 13, 17, 21):
                d.point((w // 2 - 3, y), fill=(220, 180, 60))
            d.rectangle([w - 7, 6, w - 3, 8], fill=(214, 176, 40))
        d.rectangle([0, h - 3, w, h], fill=(18, 18, 22))
    elif part.startswith("arm"):
        fill(im, navy)
        if face == "ny":
            fill(im, W_SKIN)
        else:
            d.rectangle([0, h - 4, w, h], fill=W_SKIN)
            d.rectangle([0, h - 6, w, h - 5], fill=(214, 176, 40))
    elif part.startswith("leg"):
        fill(im, (30, 34, 46))
        d.rectangle([0, h - 3, w, h], fill=(12, 12, 14))
    elif part in ("cap", "visor"):
        fill(im, (26, 32, 50) if part == "cap" else (10, 10, 14))
        if part == "cap" and face == "pz":
            d.rectangle([w // 2 - 2, 1, w // 2 + 1, 4], fill=(222, 184, 56))
    im.paste(speckle(im, 4, sseed(part, face, 1)))


def walter_face(im, eyes, mouth):
    eyes_mouth(im, eyes, mouth, W_SKIN, iris=(60, 80, 100), mouth_y=13)
    d = ImageDraw.Draw(im)
    # Brille
    for x in (2, 9):
        d.rectangle([x, 6, x + 4, 9], outline=(30, 30, 32))
    d.line([(7, 7), (8, 7)], fill=(30, 30, 32))
    # Schnurrbart
    if mouth != "grin":
        d.rectangle([4, 11, 11, 12], fill=(206, 206, 204))
        d.point((4, 13), fill=(206, 206, 204))
        d.point((11, 13), fill=(206, 206, 204))
    else:
        d.rectangle([4, 10, 11, 10], fill=(206, 206, 204))


def make_walter():
    cap = Part("cap", (0, 0, 0), (-4.5, 6.5, -4.5), (4.5, 10, 4.5), parent="head")
    visor = Part("visor", (0, 0, 0), (-4.5, 6.5, 4.5), (4.5, 7.3, 7.5), parent="head")
    # Kappe/Schirm hängen am Kopf: Pivot des Kopfes als Bezug -> Pivot 0 relativ
    cap.pivot = (0, 24, 0)
    visor.pivot = (0, 24, 0)
    return Character("walter", humanoid([cap, visor]), walter_paint, walter_face)


# ---------------------------------------------------------------- Mia
M_SKIN = (240, 214, 200)
YEL = (236, 194, 30)


def mia_paint(part, face, im):
    w, h = im.size
    d = ImageDraw.Draw(im)
    hair = (36, 26, 22)
    if part == "head":
        fill(im, YEL)
        if face == "pz":
            fill(im, YEL)
            d.rectangle([2, 2, w - 3, h - 1], fill=M_SKIN)
            d.rectangle([2, 2, w - 3, 4], fill=hair)
            d.rectangle([2, 2, 3, 10], fill=hair)
            d.rectangle([w - 4, 2, w - 3, 10], fill=hair)
            for p in ((4, 11), (5, 12), (11, 11), (10, 12)):
                d.point(p, fill=(200, 140, 120))
        elif face == "ny":
            fill(im, M_SKIN)
        d.line([(0, 0), (w, 0)], fill=shade(YEL, 1.1))
    elif part == "body":
        fill(im, YEL)
        if face == "pz":
            d.line([(w // 2, 0), (w // 2, h)], fill=shade(YEL, 0.6))
            for y in (4, 10, 16):
                d.rectangle([w // 2 + 2, y, w // 2 + 3, y + 1], fill=(60, 44, 10))
    elif part.startswith("arm"):
        fill(im, YEL)
        d.rectangle([0, h - 3, w, h], fill=M_SKIN)
    elif part.startswith("leg"):
        fill(im, (60, 60, 70))
        d.rectangle([0, h - 8, w, h], fill=(190, 30, 30))
        d.rectangle([0, h - 2, w, h], fill=(90, 10, 10))
    elif part == "hood":
        fill(im, shade(YEL, 0.95))
    im.paste(speckle(im, 5, sseed(part, face, 2)))


def mia_face(im, eyes, mouth):
    eyes_mouth(im, eyes, mouth, M_SKIN, iris=(70, 44, 30), ey=6, big=True, mouth_y=12, lip=(170, 80, 90))
    if eyes == "black":
        d = ImageDraw.Draw(im)
        d.line([(3, 10), (3, 13)], fill=(40, 10, 10))
        d.line([(12, 10), (12, 13)], fill=(40, 10, 10))


def make_mia():
    hood = Part("hood", (0, 19, 0), (-4.8, -0.3, -4.8), (4.8, 8.8, 3.6), parent="head", skip=("pz", "ny"))
    return Character("mia", humanoid([hood], leg_h=9, torso_h=10, arm_len=10, head=8), mia_paint, mia_face, size=0.78)


# ---------------------------------------------------------------- Das Ding
C_SKIN = (170, 168, 160)


def creature_paint(part, face, im):
    w, h = im.size
    d = ImageDraw.Draw(im)
    if part == "head":
        fill(im, (180, 146, 20))
        if face == "pz":
            d.rectangle([2, 2, w - 3, h - 1], fill=(206, 202, 192))
    elif part == "body":
        fill(im, (190, 154, 22))
        r = np.random.default_rng(3)
        for x in range(0, w, 2):
            d.rectangle([x, h - int(r.integers(1, 6)), x + 1, h], fill=(0, 0, 0, 0))
        if face == "pz":
            d.line([(w // 2, 0), (w // 2, h)], fill=(110, 86, 10))
    elif part.startswith("arm"):
        fill(im, C_SKIN)
        d.rectangle([0, 0, w, h // 3], fill=(186, 150, 22))
        d.line([(0, h - 1), (w, h - 1)], fill=(120, 118, 112))
    elif part.startswith("leg"):
        fill(im, (130, 128, 122))
    im.paste(speckle(im, 8, sseed(part, face, 3)))


def creature_face(im, eyes, mouth):
    d = ImageDraw.Draw(im)
    w, h = im.size
    for x in (4, 9):
        d.rectangle([x, 5, x + 2, 9], fill=(2, 2, 2))
    d.point((6, 5), fill=(255, 255, 255))
    d.point((11, 5), fill=(255, 255, 255))
    d.rectangle([3, 12, w - 4, 14], fill=(10, 4, 4))
    for x in range(3, w - 3, 2):
        d.point((x, 12), fill=(230, 226, 210))
        d.point((x + 1, 14), fill=(220, 214, 196))


def make_creature():
    parts = [
        Part("body", (0, 30, 0), (-4, 0, -2), (4, 18, 2)),
        Part("head", (0, 48, 0), (-4, 0, -4), (4, 9, 4), parent="body"),
        Part("arm_r", (-5.5, 46, 0), (-1.5, -32, -1.5), (1.5, 2, 1.5), parent="body"),
        Part("arm_l", (5.5, 46, 0), (-1.5, -32, -1.5), (1.5, 2, 1.5), parent="body"),
        Part("leg_r", (-2, 30, 0), (-1.5, -30, -1.5), (1.5, 0, 1.5)),
        Part("leg_l", (2, 30, 0), (-1.5, -30, -1.5), (1.5, 0, 1.5)),
    ]
    return Character("creature", parts, creature_paint, creature_face, size=1.05)


# ---------------------------------------------------------------- Posen
def pose_idle(t, base=None, breathe=1.0):
    p = dict(base or {})
    b = math.sin(t * 2.0) * 0.03 * breathe
    p.setdefault("body", (0, 0, 0))
    p["arm_r"] = (p.get("arm_r", (0, 0, 0))[0] + b, 0, 0.05)
    p["arm_l"] = (p.get("arm_l", (0, 0, 0))[0] - b, 0, -0.05)
    return p


def pose_walk(t, speed=1.0, amp=0.6):
    s = math.sin(t * 6.0 * speed) * amp
    return {"leg_r": (s, 0, 0), "leg_l": (-s, 0, 0), "arm_r": (-s * 0.8, 0, 0.05), "arm_l": (s * 0.8, 0, -0.05)}


def pose_sit():
    return {"leg_r": (-1.45, 0, 0.05), "leg_l": (-1.45, 0, -0.05)}


def blink(t, seed=0.0):
    return ((t + seed * 1.7) % 3.7) < 0.12


ALL = {}


def get(name):
    if name not in ALL:
        ALL[name] = {"jonas": make_jonas, "walter": make_walter, "mia": make_mia, "creature": make_creature}[name]()
    return ALL[name]
