"""Absichtlich schlechter 3D-Renderer.

Flat-Shading, Maler-Algorithmus pro Fläche (mit allen Sortierfehlern),
keine Kantenglättung, harte Near-Plane (Flächen verschwinden einfach),
niedrige Auflösung, die später grob hochskaliert wird.
"""
import math
import colorsys
import numpy as np
from PIL import Image, ImageDraw

W, H = 360, 640          # interne Renderauflösung (wird 3x hochskaliert)
NEAR = 0.15


# ---------------------------------------------------------------- Matrizen
def T(x, y, z):
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def S(x, y=None, z=None):
    if y is None:
        y = z = x
    return np.diag([x, y, z, 1.0])


def Rx(a):
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4)
    m[1, 1], m[1, 2], m[2, 1], m[2, 2] = c, -s, s, c
    return m


def Ry(a):
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4)
    m[0, 0], m[0, 2], m[2, 0], m[2, 2] = c, s, -s, c
    return m


def Rz(a):
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4)
    m[0, 0], m[0, 1], m[1, 0], m[1, 1] = c, -s, s, c
    return m


def R(rx=0.0, ry=0.0, rz=0.0):
    return Ry(ry) @ Rx(rx) @ Rz(rz)


def seg(a, b, r, rz=None):
    """Matrix, die einen Einheitszylinder (y -1..1, Radius 1) von a nach b legt."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    d = b - a
    L = np.linalg.norm(d)
    if L < 1e-6:
        return T(*a) @ S(r, 1e-3, r)
    y = d / L
    helper = np.array([0, 0, 1.0]) if abs(y[2]) < 0.9 else np.array([1.0, 0, 0])
    x = np.cross(y, helper)
    x /= np.linalg.norm(x)
    z = np.cross(x, y)
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2] = x, y, z
    mid = (a + b) / 2
    rz = r if rz is None else rz
    return T(*mid) @ m @ S(r, L / 2, rz)


# ---------------------------------------------------------------- Meshes
class Mesh:
    def __init__(self, verts, faces):
        self.v = np.array(verts, float)
        self.vh = np.hstack([self.v, np.ones((len(self.v), 1))])
        groups = {}
        for f in faces:
            groups.setdefault(len(f), []).append(f)
        self.groups = {k: np.array(v, int) for k, v in groups.items()}


def sphere_mesh(nu=8, nv=6):
    verts = [(0, 1, 0)]
    for i in range(1, nv):
        phi = math.pi * i / nv
        for j in range(nu):
            th = 2 * math.pi * j / nu
            verts.append((math.sin(phi) * math.cos(th), math.cos(phi),
                          math.sin(phi) * math.sin(th)))
    verts.append((0, -1, 0))
    bot = len(verts) - 1
    faces = []
    for j in range(nu):
        faces.append((0, 1 + j, 1 + (j + 1) % nu))
    for i in range(nv - 2):
        r0 = 1 + i * nu
        r1 = r0 + nu
        for j in range(nu):
            j2 = (j + 1) % nu
            faces.append((r0 + j, r1 + j, r1 + j2, r0 + j2))
    last = 1 + (nv - 2) * nu
    for j in range(nu):
        faces.append((bot, last + (j + 1) % nu, last + j))
    return Mesh(verts, faces)


def box_mesh():
    v = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
         (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
    f = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6),
         (1, 2, 6, 5), (0, 3, 7, 4)]
    return Mesh(v, f)


def cyl_mesh(n=7):
    v = []
    for j in range(n):
        th = 2 * math.pi * j / n
        v.append((math.cos(th), 1, math.sin(th)))
    for j in range(n):
        th = 2 * math.pi * j / n
        v.append((math.cos(th), -1, math.sin(th)))
    f = [tuple(range(n)), tuple(range(n, 2 * n))]
    for j in range(n):
        j2 = (j + 1) % n
        f.append((j, j2, n + j2, n + j))
    # n-Ecke in Dreiecke zerlegen, damit alle Gruppen gleich lang sind
    out = []
    for face in f:
        if len(face) > 4:
            for k in range(1, len(face) - 1):
                out.append((face[0], face[k], face[k + 1]))
        else:
            out.append(face)
    return Mesh(v, out)


def cone_mesh(n=6):
    v = [(0, 1, 0)]
    for j in range(n):
        th = 2 * math.pi * j / n
        v.append((math.cos(th), -1, math.sin(th)))
    f = []
    for j in range(n):
        f.append((0, 1 + j, 1 + (j + 1) % n))
    for k in range(1, n - 1):
        f.append((1, 1 + k, 2 + k))
    return Mesh(v, f)


SPH = sphere_mesh(8, 6)
SPH_LO = sphere_mesh(6, 4)
SPH_HI = sphere_mesh(11, 8)
BOX = box_mesh()
CYL = cyl_mesh(7)
CYL5 = cyl_mesh(5)
CONE = cone_mesh(6)
PYR = cone_mesh(4)


# ---------------------------------------------------------------- Farben
def hsv(h, s=1.0, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


# ---------------------------------------------------------------- Szene
class Scene:
    def __init__(self):
        self.items = []

    def add(self, mesh, M, color, layer=1.0, emissive=False, cull=True,
            jitter=10):
        self.items.append(("mesh", mesh, M, color, layer, emissive, cull, jitter))

    def quad(self, corners, img, layer=1.0):
        """corners: 4 Weltpunkte (oben-links, oben-rechts, unten-rechts, unten-links)."""
        self.items.append(("tex", np.array(corners, float), img, layer))

    def render(self, eye, target, fov=60, bg=None, light=(-0.4, 0.8, 0.5),
               amb=0.38, levels=4, roll=0.0, img=None, fog=None):
        eye = np.asarray(eye, float)
        target = np.asarray(target, float)
        f = target - eye
        f /= np.linalg.norm(f)
        up = np.array([0, 1.0, 0])
        if abs(f[1]) > 0.98:
            up = np.array([0, 0, -1.0])
        r = np.cross(f, up)
        r /= np.linalg.norm(r)
        u = np.cross(r, f)
        if roll:
            c, s = math.cos(roll), math.sin(roll)
            r, u = r * c + u * s, -r * s + u * c
        Rm = np.array([r, u, f])
        foc = (H / 2) / math.tan(math.radians(fov) / 2)
        L = np.asarray(light, float)
        L /= np.linalg.norm(L)

        if img is None:
            img = Image.new("RGB", (W, H), bg if isinstance(bg, tuple) else (0, 0, 0))
            if isinstance(bg, Image.Image):
                img.paste(bg)
        draw = ImageDraw.Draw(img)
        polys = []  # (layer, depth, kind, data)

        for it in self.items:
            if it[0] == "tex":
                _, cw, timg, layer = it
                cv = (cw - eye) @ Rm.T
                if (cv[:, 2] < NEAR).any():
                    continue
                sx = W / 2 + foc * cv[:, 0] / cv[:, 2]
                sy = H / 2 - foc * cv[:, 1] / cv[:, 2]
                polys.append((layer, cv[:, 2].mean(), "tex",
                              (list(zip(sx, sy)), timg)))
                continue
            _, mesh, M, color, layer, emissive, cull, jitter = it
            wv = (M @ mesh.vh.T).T[:, :3]
            center = M[:3, 3]
            cv = (wv - eye) @ Rm.T
            z = cv[:, 2]
            zs = np.maximum(z, 1e-6)
            sx = W / 2 + foc * cv[:, 0] / zs
            sy = H / 2 - foc * cv[:, 1] / zs
            col = np.array(color, float)
            for k, F in mesh.groups.items():
                zz = z[F]
                ok = (zz >= NEAR).all(axis=1)
                if not ok.any():
                    continue
                F = F[ok]
                p0, p1, p2 = wv[F[:, 0]], wv[F[:, 1]], wv[F[:, 2]]
                n = np.cross(p1 - p0, p2 - p0)
                nl = np.linalg.norm(n, axis=1)
                good = nl > 1e-10
                F, n, nl = F[good], n[good], nl[good]
                if len(F) == 0:
                    continue
                n = n / nl[:, None]
                cen = wv[F].mean(axis=1)
                out = np.einsum("ij,ij->i", n, cen - center)
                n[out < 0] *= -1
                if cull:
                    vis = np.einsum("ij,ij->i", n, cen - eye) < 0
                    F, n, cen = F[vis], n[vis], cen[vis]
                    if len(F) == 0:
                        continue
                depth = z[F].mean(axis=1)
                if emissive:
                    shade = np.ones(len(F))
                else:
                    d = np.clip(n @ L, 0, 1)
                    shade = amb + (1 - amb) * d
                    shade = np.round(shade * levels) / levels
                for i in range(len(F)):
                    jj = 0
                    if jitter:
                        jj = ((F[i, 0] * 7919 + F[i, 1] * 104729) % (2 * jitter + 1)) - jitter
                    c = np.clip(col * shade[i] + jj, 0, 255)
                    if fog is not None:
                        fc, fd = fog
                        tt = min(1.0, depth[i] / fd)
                        c = c + (np.array(fc) - c) * tt
                    pts = list(zip(sx[F[i]], sy[F[i]]))
                    polys.append((layer, depth[i], "poly",
                                  (pts, tuple(int(x) for x in c))))

        polys.sort(key=lambda p: (p[0], -p[1]))
        for layer, depth, kind, data in polys:
            if kind == "poly":
                pts, c = data
                draw.polygon(pts, fill=c)
            else:
                pts, timg = data
                paste_persp(img, timg, pts)

        def project(p):
            p = (np.asarray(p, float) - eye) @ Rm.T
            if p[2] < NEAR:
                return None
            return (W / 2 + foc * p[0] / p[2], H / 2 - foc * p[1] / p[2])

        return img, project


def _persp_coeffs(dst, src):
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    return np.linalg.solve(np.array(A, float), np.array(b, float))


def paste_persp(img, timg, pts):
    w, h = timg.size
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    try:
        co = _persp_coeffs(pts, src)
    except np.linalg.LinAlgError:
        return
    warped = timg.convert("RGB").transform(img.size, Image.PERSPECTIVE, tuple(co),
                                           Image.NEAREST)
    mask = Image.new("L", timg.size, 255).transform(img.size, Image.PERSPECTIVE,
                                                    tuple(co), Image.NEAREST)
    img.paste(warped, (0, 0), mask)


# ---------------------------------------------------------------- Hintergründe / Post
def gradient(top, bottom, w=W, h=H):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top, float)[None, None, :]
    b = np.array(bottom, float)[None, None, :]
    arr = (a + (b - a) * t) * np.ones((1, w, 1))
    return Image.fromarray(arr.astype(np.uint8))


def hue_shift(img, amount):
    hsvimg = np.array(img.convert("HSV"), dtype=np.int16)
    hsvimg[..., 0] = (hsvimg[..., 0] + int(amount * 255)) % 256
    return Image.fromarray(hsvimg.astype(np.uint8), "HSV").convert("RGB")


_yy, _xx = np.mgrid[0:H, 0:W]
_vig = np.clip(1.0 - (((_xx - W / 2) / (W * 0.7)) ** 2 + ((_yy - H / 2) / (H * 0.6)) ** 2), 0, 1)


def vignette(img, strength=1.0):
    a = np.array(img, float)
    v = _vig[..., None] ** strength
    return Image.fromarray(np.clip(a * v, 0, 255).astype(np.uint8))


def grain(img, amount=25, seed=0):
    rng = np.random.default_rng(seed)
    a = np.array(img, float) + rng.normal(0, amount, (H, W, 1))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def tint(img, color, t):
    a = np.array(img, float)
    a = a + (np.array(color, float) - a) * t
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def desat(img, t):
    a = np.array(img, float)
    g = a.mean(axis=2, keepdims=True)
    a = a + (g - a) * t
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def glitch(img, seed):
    rng = np.random.default_rng(seed)
    a = np.array(img)
    for _ in range(rng.integers(4, 10)):
        y = rng.integers(0, H - 20)
        hgt = rng.integers(4, 40)
        a[y:y + hgt] = np.roll(a[y:y + hgt], rng.integers(-60, 60), axis=1)
    ch = rng.integers(0, 3)
    a[..., ch] = np.roll(a[..., ch], rng.integers(-8, 8), axis=1)
    return Image.fromarray(a)
