# -*- coding: utf-8 -*-
"""Verwaltet GPU-Ressourcen der Sets und Figuren und baut Draw-Listen."""
import numpy as np
from PIL import Image
import engine, tiles, sets, chars

I4 = np.eye(4, dtype="f4")


class Stage:
    def __init__(self, W, H, msaa=4):
        self.r = engine.Renderer(W, H, msaa=msaa)
        self.atlas = engine.Atlas()
        tiles.register(self.atlas)
        self.r.texture("atlas", self.atlas.img)
        self.sets = {}
        self.chars = {}

    # ---------------------------------------------------------------- Sets
    def get_set(self, name):
        if name in self.sets:
            return self.sets[name]
        b = {
            "exterior": lambda: sets.build_exterior(self.atlas),
            "exterior_dawn": lambda: sets.build_exterior(self.atlas, dawn=True),
            "corridor": lambda: sets.build_corridor(self.atlas),
            "corridor_lit": lambda: sets.build_corridor(self.atlas, lit=True),
            "office": lambda: sets.build_office(self.atlas),
            "service": lambda: sets.build_service(self.atlas),
            "atrium": lambda: sets.build_atrium(self.atlas),
            "entrance": lambda: sets.build_entrance(self.atlas),
            "entrance_dawn": lambda: sets.build_entrance(self.atlas, dawn=True),
        }[name]
        s = b()
        op, tr = s.w.build_mesh()
        self.r.vao(f"{name}:op", op.array())
        self.r.vao(f"{name}:tr", tr.array())
        self.r.vao(f"{name}:pr", s.w.props.array())
        self.r.vao(f"{name}:prt", s.w.props_t.array())
        s.decal_draws = []
        for key, img, corners, emit, transparent in s.decals:
            m = engine.Mesh()
            n = np.cross(np.subtract(corners[1], corners[0]), np.subtract(corners[3], corners[0]))
            n = n / (np.linalg.norm(n) + 1e-9)
            m.add_quad(corners, tuple(n), [(0, 1), (1, 1), (1, 0), (0, 0)], (1, 1, 1, 1), emit)
            self.r.vao(key, m.array())
            self.r.texture(key, img)
            s.decal_draws.append((key, key, I4, {"transparent": transparent}))
        self.sets[name] = s
        return s

    def set_draws(self, name):
        s = self.get_set(name)
        d = [(f"{name}:op", "atlas", I4, {}), (f"{name}:pr", "atlas", I4, {})]
        d += s.decal_draws
        d += [(f"{name}:tr", "atlas", I4, {"transparent": True}), (f"{name}:prt", "atlas", I4, {"transparent": True})]
        return d

    # ---------------------------------------------------------------- Figuren
    def get_char(self, name):
        if name not in self.chars:
            c = chars.get(name)
            self.r.texture(f"skin:{name}", c.skin)
            for pname, arr in c.meshes.items():
                self.r.vao(f"char:{name}:{pname}", arr)
            self.chars[name] = c
            c._face_key = None
        return self.chars[name]

    def char_draws(self, name, pose, eyes="open", mouth="0", tint=(1, 1, 1), no_shadow=False):
        c = self.get_char(name)
        key = (eyes, mouth)
        if c._face_key != key:
            img = c.face_image(eyes, mouth)
            x, y, w, h = c.face_rect()
            self.r.textures[f"skin:{name}"].write(img.tobytes(), viewport=(x, y, w, h))
            c._face_key = key
        mats = c.matrices(pose)
        hidden = pose.get("hide", ())
        return [(f"char:{name}:{p}", f"skin:{name}", m, {"tint": tint, "no_shadow": no_shadow})
                for p, m in mats.items() if p not in hidden]

    # ---------------------------------------------------------------- Requisiten (dynamisch)
    def prop(self, key, boxes):
        """boxes: [(x0,y0,z0,x1,y1,z1,tile)] in lokalen Koordinaten -> einmalig hochladen."""
        if f"prop:{key}" not in self.r.vaos:
            w = engine.World(self.atlas, (1, 1, 1))
            for b in boxes:
                w.box(*b[:6], b[6])
            self.r.vao(f"prop:{key}", w.props.array())
        return f"prop:{key}"

    def decal(self, key, img, corners, emit=0.0, update=False):
        k = f"dyn:{key}"
        if k not in self.r.vaos:
            m = engine.Mesh()
            m.add_quad(corners, (0, 0, 1), [(0, 1), (1, 1), (1, 0), (0, 0)], (1, 1, 1, 1), emit)
            self.r.vao(k, m.array())
        if update or k not in self.r.textures:
            self.r.update_texture(k, img)
        return k

    def render(self, frame):
        return self.r.render(frame)
