# -*- coding: utf-8 -*-
"""Kleiner Voxel-Renderer (moderngl + Mesa llvmpipe, headless).

- Blockwelt (numpy-Gitter) mit Pixel-Texturatlas, Flächen-Culling und Ecken-AO
- Requisiten: beliebige achsparallele Quader mit Atlas-Kacheln
- Decals: Quads mit eigener Textur (Schilder, Bildschirme, Karte …)
- Blockfiguren aus Quadern mit eigener Skin-Textur + Gesichtstextur
- Licht: Ambient (Himmel/Boden), Punktlichter, Spot (Taschenlampe) mit Schatten, Emission, Nebel
"""
import math
import numpy as np
import moderngl
from PIL import Image

# ---------------------------------------------------------------- Mathe
def perspective(fov, aspect, near, far):
    t = 1 / math.tan(math.radians(fov) / 2)
    return np.array([[t / aspect, 0, 0, 0], [0, t, 0, 0],
                     [0, 0, (far + near) / (near - far), 2 * far * near / (near - far)], [0, 0, -1, 0]], "f4")


def look_at(eye, target, up=(0, 1, 0)):
    e, c, u = (np.asarray(v, "f8") for v in (eye, target, up))
    f = c - e
    f /= np.linalg.norm(f)
    s = np.cross(f, u)
    if np.linalg.norm(s) < 1e-6:
        s = np.cross(f, (0, 0, 1))
    s /= np.linalg.norm(s)
    uu = np.cross(s, f)
    m = np.eye(4)
    m[0, :3], m[1, :3], m[2, :3] = s, uu, -f
    m[:3, 3] = -m[:3, :3] @ e
    return m.astype("f4")


def translate(x, y, z):
    m = np.eye(4, dtype="f4")
    m[:3, 3] = (x, y, z)
    return m


def scale(x, y, z):
    return np.diag([x, y, z, 1]).astype("f4")


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]], "f4")


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]], "f4")


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], "f4")


# ---------------------------------------------------------------- Shader
VS = """#version 330
uniform mat4 vp; uniform mat4 model; uniform mat4 lvp;
in vec3 pos; in vec3 nrm; in vec2 uv; in float ao; in float emit;
out vec3 wp; out vec3 wn; out vec2 vuv; out float vao; out float vem; out vec4 lpos;
void main(){
  vec4 w = model * vec4(pos, 1.0);
  wp = w.xyz; wn = normalize(mat3(model) * nrm); vuv = uv; vao = ao; vem = emit;
  lpos = lvp * w;
  gl_Position = vp * w;
}"""

FS = """#version 330
uniform sampler2D tex; uniform sampler2D shadow;
uniform vec3 cam; uniform vec3 amb_sky; uniform vec3 amb_ground;
uniform vec3 fog_col; uniform float fog_dens;
uniform int npl; uniform vec3 pl_pos[12]; uniform vec3 pl_col[12]; uniform float pl_rad[12];
uniform int spot_on; uniform vec3 sp_pos; uniform vec3 sp_dir; uniform vec3 sp_col; uniform float sp_cos; uniform float sp_soft; uniform float sp_range;
uniform int sh_on; uniform float emit_gain; uniform float alpha_mul; uniform vec3 tint;
uniform int pass_transparent; uniform float exposure;
in vec3 wp; in vec3 wn; in vec2 vuv; in float vao; in float vem; in vec4 lpos;
out vec4 frag;
float shadowf(){
  if (sh_on == 0) return 1.0;
  vec3 p = lpos.xyz / lpos.w * 0.5 + 0.5;
  if (p.x < 0.0 || p.x > 1.0 || p.y < 0.0 || p.y > 1.0 || p.z > 1.0) return 1.0;
  float s = 0.0; vec2 ts = 1.0 / vec2(textureSize(shadow, 0));
  for (int x = -1; x <= 1; x++) for (int y = -1; y <= 1; y++) {
    float d = texture(shadow, p.xy + vec2(x, y) * ts).r;
    s += (p.z - 0.0015 > d) ? 0.0 : 1.0;
  }
  return s / 9.0;
}
void main(){
  vec4 t = texture(tex, vuv);
  if (pass_transparent == 0 && t.a < 0.5) discard;
  vec3 base = t.rgb * tint;
  vec3 n = normalize(wn);
  float hemi = n.y * 0.5 + 0.5;
  vec3 light = mix(amb_ground, amb_sky, hemi) * vao;
  for (int i = 0; i < npl; i++) {
    vec3 d = pl_pos[i] - wp; float L = length(d);
    float att = clamp(1.0 - L / pl_rad[i], 0.0, 1.0); att *= att;
    float nd = max(dot(n, d / max(L, 1e-4)), 0.0) * 0.8 + 0.2;
    light += pl_col[i] * att * nd * (0.55 + 0.45 * vao);
  }
  if (spot_on == 1) {
    vec3 d = wp - sp_pos; float L = length(d); vec3 dn = d / max(L, 1e-4);
    float c = dot(dn, normalize(sp_dir));
    float cone = smoothstep(sp_cos, sp_cos + sp_soft, c);
    float att = clamp(1.0 - L / sp_range, 0.0, 1.0);
    float nd = max(dot(n, -dn), 0.0) * 0.85 + 0.15;
    light += sp_col * cone * att * att * nd * shadowf();
  }
  vec3 col = base * light + base * vem * emit_gain;
  float dist = length(cam - wp);
  float f = exp(-fog_dens * dist);
  col = mix(fog_col, col, f);
  col = vec3(1.0) - exp(-col * exposure);
  col = pow(col, vec3(0.92));
  frag = vec4(col, (pass_transparent == 1 ? t.a : 1.0) * alpha_mul);
}"""

DEPTH_VS = """#version 330
uniform mat4 lvp; uniform mat4 model; in vec3 pos; in vec2 uv;
out vec2 vuv;
void main(){ vuv = uv; gl_Position = lvp * model * vec4(pos, 1.0); }"""
DEPTH_FS = """#version 330
uniform sampler2D tex; in vec2 vuv;
void main(){ if (texture(tex, vuv).a < 0.5) discard; }"""

FMT = "3f 3f 2f 1f 1f"
ATTRS = ("pos", "nrm", "uv", "ao", "emit")

# Flächen: Normale, 4 Ecken (Einheitswürfel), Achsen für AO
FACES = {
    "px": ((1, 0, 0), [(1, 0, 1), (1, 0, 0), (1, 1, 0), (1, 1, 1)]),
    "nx": ((-1, 0, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]),
    "py": ((0, 1, 0), [(0, 1, 1), (1, 1, 1), (1, 1, 0), (0, 1, 0)]),
    "ny": ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
    "pz": ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]),
    "nz": ((0, 0, -1), [(1, 0, 0), (0, 0, 0), (0, 1, 0), (1, 1, 0)]),
}
UVQ = [(0, 1), (1, 1), (1, 0), (0, 0)]   # u,v (v nach unten)


def quad_tris(v):
    return [v[0], v[1], v[2], v[0], v[2], v[3]]


class Mesh:
    def __init__(self):
        self.data = []

    def add_quad(self, corners, normal, uvs, ao=(1, 1, 1, 1), emit=0.0):
        vs = [(*corners[i], *normal, *uvs[i], ao[i], emit) for i in range(4)]
        # AO-bewusste Diagonale (Minecraft-Trick gegen Anisotropie)
        if ao[0] + ao[2] < ao[1] + ao[3]:
            vs = vs[1:] + vs[:1]
        self.data.extend(quad_tris(vs))

    def array(self):
        return np.array(self.data, "f4") if self.data else np.zeros((0, 10), "f4")


# ---------------------------------------------------------------- Atlas
class Atlas:
    """Kacheln à 16x16 Pixel in einem 512x512-Atlas."""
    T = 16
    N = 32

    def __init__(self):
        self.img = Image.new("RGBA", (self.T * self.N, self.T * self.N), (255, 0, 255, 255))
        self.names = {}
        self.emit = {}

    def add(self, name, tile_img, emissive=0.0):
        i = len(self.names)
        x, y = (i % self.N) * self.T, (i // self.N) * self.T
        self.img.paste(tile_img.convert("RGBA").resize((self.T, self.T), Image.NEAREST), (x, y))
        self.names[name] = i
        self.emit[name] = emissive

    def uv(self, name, u0=0.0, v0=0.0, u1=1.0, v1=1.0):
        i = self.names[name]
        x, y = (i % self.N), (i // self.N)
        s = 1.0 / self.N
        e = 0.0005
        return (x + u0) * s + e, (y + v0) * s + e, (x + u1) * s - e, (y + v1) * s - e


# ---------------------------------------------------------------- Welt
class World:
    def __init__(self, atlas, size):
        self.atlas = atlas
        self.vox = np.zeros(size, np.int16)
        self.blocks = [None]          # id -> (top, side, bottom, transparent)
        self.bid = {}
        self.props = Mesh()           # zusätzliche Quader (nicht im Gitter)
        self.props_t = Mesh()         # transparente Quader
        self.offset = np.zeros(3)

    def block(self, name, top=None, side=None, bottom=None, transparent=False):
        if name in self.bid:
            return self.bid[name]
        side = side or name
        self.blocks.append((top or side, side, bottom or top or side, transparent))
        self.bid[name] = len(self.blocks) - 1
        return self.bid[name]

    def fill(self, x0, y0, z0, x1, y1, z1, name):
        """Füllt inklusive Grenzen (x0..x1). name=None -> Luft."""
        b = 0 if name is None else self.bid[name]
        xs, ys, zs = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
        ox, oy, oz = self.offset.astype(int)
        self.vox[xs[0] + ox:xs[1] + ox + 1, ys[0] + oy:ys[1] + oy + 1, zs[0] + oz:zs[1] + oz + 1] = b

    def set(self, x, y, z, name):
        ox, oy, oz = self.offset.astype(int)
        self.vox[x + ox, y + oy, z + oz] = 0 if name is None else self.bid[name]

    def solid(self, x, y, z):
        X, Y, Z = self.vox.shape
        if 0 <= x < X and 0 <= y < Y and 0 <= z < Z:
            b = self.vox[x, y, z]
            return b != 0 and not self.blocks[b][3]
        return False

    def build_mesh(self):
        opaque, trans = Mesh(), Mesh()
        X, Y, Z = self.vox.shape
        idx = np.argwhere(self.vox != 0)
        occ = np.zeros((X + 2, Y + 2, Z + 2), bool)
        tr_ids = [i for i, b in enumerate(self.blocks) if b and b[3]]
        solid = (self.vox != 0) & ~np.isin(self.vox, tr_ids)
        occ[1:-1, 1:-1, 1:-1] = solid
        ox, oy, oz = self.offset
        for (x, y, z) in idx:
            b = self.vox[x, y, z]
            top, side, bottom, transparent = self.blocks[b]
            for fname, (n, corners) in FACES.items():
                nx_, ny_, nz_ = x + n[0], y + n[1], z + n[2]
                if 0 <= nx_ < X and 0 <= ny_ < Y and 0 <= nz_ < Z:
                    nb = self.vox[nx_, ny_, nz_]
                    if nb != 0 and (not self.blocks[nb][3] or transparent):
                        continue
                tile = top if fname == "py" else (bottom if fname == "ny" else side)
                u0, v0, u1, v1 = self.atlas.uv(tile)
                uvs = [(u0 if q[0] == 0 else u1, v0 if q[1] == 0 else v1) for q in UVQ]
                cs = [(x + c[0] - ox, y + c[1] - oy, z + c[2] - oz) for c in corners]
                ao = []
                if not transparent:
                    for c in corners:
                        # Nachbarn in der Ebene vor der Fläche
                        a = [i for i in range(3) if n[i] == 0]
                        d = [(1 if c[a[0]] == 1 else -1), (1 if c[a[1]] == 1 else -1)]
                        base = [x + n[0], y + n[1], z + n[2]]
                        p1 = list(base); p1[a[0]] += d[0]
                        p2 = list(base); p2[a[1]] += d[1]
                        p3 = list(base); p3[a[0]] += d[0]; p3[a[1]] += d[1]
                        s1 = occ[p1[0] + 1, p1[1] + 1, p1[2] + 1]
                        s2 = occ[p2[0] + 1, p2[1] + 1, p2[2] + 1]
                        s3 = occ[p3[0] + 1, p3[1] + 1, p3[2] + 1]
                        lvl = 0 if (s1 and s2) else 3 - (int(s1) + int(s2) + int(s3))
                        ao.append(0.45 + 0.55 * lvl / 3)
                else:
                    ao = [1, 1, 1, 1]
                (trans if transparent else opaque).add_quad(cs, n, uvs, ao, self.atlas.emit.get(tile, 0.0))
        return opaque, trans

    # ---- Requisiten (frei positionierte Quader)
    def box(self, x0, y0, z0, x1, y1, z1, tile, tiles=None, emit=None, transparent=False, uvscale=1.0):
        """Quader von (x0,y0,z0) bis (x1,y1,z1) in Weltkoordinaten. tiles: dict face->tile."""
        m = self.props_t if transparent else self.props
        lo = np.array([min(x0, x1), min(y0, y1), min(z0, z1)], float)
        hi = np.array([max(x0, x1), max(y0, y1), max(z0, z1)], float)
        size = hi - lo
        for fname, (n, corners) in FACES.items():
            t = (tiles or {}).get(fname, tile)
            if t is None:
                continue
            cs = [tuple(lo + np.array(c) * size) for c in corners]
            # Kachel-Wiederholung grob über Teilbereich (max 1 Kachel)
            a = [i for i in range(3) if n[i] == 0]
            su, sv = min(1.0, size[a[0]] * uvscale), min(1.0, size[a[1]] * uvscale)
            if fname in ("py", "ny"):
                su, sv = min(1.0, size[0] * uvscale), min(1.0, size[2] * uvscale)
            elif fname in ("px", "nx"):
                su, sv = min(1.0, size[2] * uvscale), min(1.0, size[1] * uvscale)
            else:
                su, sv = min(1.0, size[0] * uvscale), min(1.0, size[1] * uvscale)
            u0, v0, u1, v1 = self.atlas.uv(t, 0, 0, su, sv)
            uvs = [(u0 if q[0] == 0 else u1, v0 if q[1] == 0 else v1) for q in UVQ]
            e = self.atlas.emit.get(t, 0.0) if emit is None else emit
            m.add_quad(cs, n, uvs, (1, 1, 1, 1), e)


# ---------------------------------------------------------------- Renderer
class Renderer:
    def __init__(self, W, H, msaa=4, shadow_size=1024):
        self.W, self.H = W, H
        self.ctx = moderngl.create_context(standalone=True, backend="egl")
        self.prog = self.ctx.program(vertex_shader=VS, fragment_shader=FS)
        self.dprog = self.ctx.program(vertex_shader=DEPTH_VS, fragment_shader=DEPTH_FS)
        self.msaa = msaa
        self.color_ms = self.ctx.renderbuffer((W, H), 4, samples=msaa)
        self.depth_ms = self.ctx.depth_renderbuffer((W, H), samples=msaa)
        self.fbo_ms = self.ctx.framebuffer([self.color_ms], self.depth_ms)
        self.fbo_out = self.ctx.simple_framebuffer((W, H), components=4)
        self.shadow_tex = self.ctx.depth_texture((shadow_size, shadow_size))
        self.shadow_tex.compare_func = ""
        self.shadow_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.shadow_fbo = self.ctx.framebuffer(depth_attachment=self.shadow_tex)
        self.textures = {}
        self.vaos = {}

    def texture(self, key, img):
        if key in self.textures:
            return self.textures[key]
        img = img.convert("RGBA")
        t = self.ctx.texture(img.size, 4, img.tobytes())
        t.filter = (moderngl.NEAREST, moderngl.NEAREST)
        t.repeat_x = t.repeat_y = False
        self.textures[key] = t
        return t

    def update_texture(self, key, img):
        img = img.convert("RGBA")
        if key in self.textures and self.textures[key].size == img.size:
            self.textures[key].write(img.tobytes())
            return self.textures[key]
        self.textures.pop(key, None)
        return self.texture(key, img)

    def vao(self, key, arr):
        if key in self.vaos:
            return self.vaos[key]
        if len(arr) == 0:
            self.vaos[key] = None
            return None
        vbo = self.ctx.buffer(np.ascontiguousarray(arr, "f4").tobytes())
        v = self.ctx.vertex_array(self.prog, [(vbo, FMT, *ATTRS)])
        dv = self.ctx.vertex_array(self.dprog, [(vbo, "3f 12x 2f 8x", "pos", "uv")])
        self.vaos[key] = (v, dv, vbo)
        return self.vaos[key]

    def drop(self, prefix):
        for k in [k for k in self.vaos if k.startswith(prefix)]:
            v = self.vaos.pop(k)
            if v:
                v[0].release(); v[1].release(); v[2].release()

    def render(self, frame):
        """frame: dict mit cam(eye,target,fov,roll), env, lights, spot, draws[(vao_key, tex_key, model, opts)]."""
        ctx, p = self.ctx, self.prog
        eye = np.array(frame["eye"], "f4")
        V = look_at(eye, frame["target"], frame.get("up", (0, 1, 0)))
        if frame.get("roll"):
            V = rot_z(frame["roll"]) @ V
        P = perspective(frame.get("fov", 55), self.W / self.H, 0.05, 220)
        VP = P @ V
        env = frame["env"]
        sp = frame.get("spot")
        LVP = np.eye(4, dtype="f4")
        sh = 0
        if sp is not None and sp.get("shadow", True):
            sh = 1
            sp_pos = np.array(sp["pos"], "f4")
            sp_dir = np.array(sp["dir"], "f4")
            LV = look_at(sp_pos, sp_pos + sp_dir, (0, 1, 0) if abs(sp_dir[1]) < 0.95 else (0, 0, 1))
            LP = perspective(sp.get("angle", 40) * 2 + 10, 1.0, 0.1, sp.get("range", 30))
            LVP = LP @ LV
            self.shadow_fbo.use()
            self.shadow_fbo.clear(depth=1.0)
            ctx.enable(moderngl.DEPTH_TEST)
            ctx.disable(moderngl.CULL_FACE)
            self.dprog["lvp"].write(LVP.T.tobytes())
            for key, tex, model, opts in frame["draws"]:
                if opts.get("transparent") or opts.get("no_shadow"):
                    continue
                v = self.vaos.get(key)
                if not v:
                    continue
                self.textures[tex].use(0)
                self.dprog["tex"].value = 0
                self.dprog["model"].write(np.asarray(model, "f4").T.tobytes())
                v[1].render()
        self.fbo_ms.use()
        fc = env.get("clear", env["fog"])
        self.fbo_ms.clear(*fc, 1.0, depth=1.0)
        ctx.enable(moderngl.DEPTH_TEST)
        ctx.disable(moderngl.CULL_FACE)
        p["vp"].write(VP.T.tobytes())
        p["lvp"].write(LVP.T.tobytes())
        p["cam"].value = tuple(eye)
        p["amb_sky"].value = tuple(env["amb_sky"])
        p["amb_ground"].value = tuple(env["amb_ground"])
        p["fog_col"].value = tuple(env["fog"])
        p["fog_dens"].value = env.get("fog_dens", 0.03)
        pls = frame.get("lights", [])[:12]
        p["npl"].value = len(pls)
        if pls:
            pos = np.zeros((12, 3), "f4"); col = np.zeros((12, 3), "f4"); rad = np.ones(12, "f4")
            for i, (pp, cc, rr) in enumerate(pls):
                pos[i], col[i], rad[i] = pp, cc, rr
            p["pl_pos"].write(pos.tobytes()); p["pl_col"].write(col.tobytes()); p["pl_rad"].write(rad.tobytes())
        if sp is not None:
            p["spot_on"].value = 1
            p["sp_pos"].value = tuple(sp["pos"]); p["sp_dir"].value = tuple(sp["dir"]); p["sp_col"].value = tuple(sp["col"])
            p["sp_cos"].value = math.cos(math.radians(sp.get("angle", 25)))
            p["sp_soft"].value = sp.get("soft", 0.08)
            p["sp_range"].value = sp.get("range", 30)
        else:
            p["spot_on"].value = 0
        p["sh_on"].value = sh
        self.shadow_tex.use(1)
        p["shadow"].value = 1
        p["tex"].value = 0
        p["emit_gain"].value = env.get("emit_gain", 1.0)
        p["exposure"].value = frame.get("exposure", env.get("exposure", 1.9))
        for transparent_pass in (0, 1):
            if transparent_pass:
                ctx.enable(moderngl.BLEND)
                ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
                ctx.depth_mask = False
            p["pass_transparent"].value = transparent_pass
            for key, tex, model, opts in frame["draws"]:
                if bool(opts.get("transparent")) != bool(transparent_pass):
                    continue
                v = self.vaos.get(key)
                if not v:
                    continue
                self.textures[tex].use(0)
                p["model"].write(np.asarray(model, "f4").T.tobytes())
                p["alpha_mul"].value = opts.get("alpha", 1.0)
                p["tint"].value = tuple(opts.get("tint", (1, 1, 1)))
                v[0].render()
            if transparent_pass:
                ctx.disable(moderngl.BLEND)
                ctx.depth_mask = True
        ctx.copy_framebuffer(self.fbo_out, self.fbo_ms)
        data = self.fbo_out.read(components=3)
        img = np.frombuffer(data, np.uint8).reshape(self.H, self.W, 3)[::-1]
        return img
