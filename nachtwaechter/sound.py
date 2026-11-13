# -*- coding: utf-8 -*-
"""Sounddesign: Effekte, Atmo, Spannungsmusik – alles synthetisch (numpy)."""
import hashlib
import numpy as np

SR = 44100


def seed(name):
    return int(hashlib.md5(name.encode()).hexdigest()[:8], 16)


def tsec(d):
    return np.arange(int(d * SR)) / SR


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


def reverb(x, t60=1.8, wet=0.35, s=0):
    n = int(SR * t60)
    t = np.arange(n) / SR
    ir = np.random.default_rng(s).normal(0, 1, n) * np.exp(-6.9 * t / t60)
    ir = fft_filter(ir, 120, 5000)
    ir /= np.sqrt((ir ** 2).sum())
    L = len(x) + n
    nf = 1 << (L - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, nf) * np.fft.rfft(ir, nf), nf)[:L]
    out = np.zeros(L)
    out[:len(x)] = x * (1 - wet)
    return out + y * wet


def burst(r, dur, tau):
    n = int(dur * SR)
    return r.normal(0, 1, n) * np.exp(-np.arange(n) / (tau * SR))


_CACHE = {}


def sfx(name):
    if name in _CACHE:
        return _CACHE[name]
    x = _make(name)
    _CACHE[name] = x
    return x


def _make(name):
    r = np.random.default_rng(seed(name))
    if name in ("footsteps", "footsteps_slow"):
        gap, n_steps = (0.6, 7) if name == "footsteps" else (1.0, 4)
        out = np.zeros(int(SR * (gap * n_steps + 1)))
        for i in range(n_steps):
            s = int(i * gap * SR)
            b = fft_filter(burst(r, 0.09, 0.018), 60, 1400) * (0.9 if i % 2 else 0.7)
            out[s:s + len(b)] += b
        return reverb(out, 1.8, 0.5)
    if name == "paper":
        out = np.zeros(int(SR * 1.2))
        for i in range(14):
            s = int(r.uniform(0, 1.0) * SR)
            b = burst(r, 0.05, 0.012)
            out[s:s + len(b)] += b * r.uniform(0.2, 0.6)
        return fft_filter(out, 1800, 9000) * 0.8
    if name == "sting":
        t = tsec(4.0)
        boom = np.sin(2 * np.pi * (55 * t - 6 * t ** 2)) * np.exp(-t / 1.1)
        cl = sum(np.sin(2 * np.pi * f * t + p) for f, p in ((1870, 0), (1990, 1), (2120, 2), (2390, 3)))
        cl *= np.clip(t / 0.03, 0, 1) * np.exp(-t / 1.2) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t)) * 0.14
        hit = fft_filter(r.normal(0, 1, len(t)) * np.exp(-t / 0.08), 40, 2500) * 0.6
        return reverb(boom + cl + hit, 3.0, 0.5)
    if name == "low_hit":
        t = tsec(3.5)
        x = np.sin(2 * np.pi * (42 * t - 3 * t ** 2)) * np.exp(-t / 1.4) + fft_filter(r.normal(0, 1, len(t)) * np.exp(-t / 0.2), 20, 300) * 0.5
        return reverb(x, 3.0, 0.4)
    if name == "thud":
        t = tsec(1.5)
        x = np.sin(2 * np.pi * 70 * t * (1 - 0.3 * t)) * np.exp(-t / 0.15) + fft_filter(r.normal(0, 1, len(t)) * np.exp(-t / 0.06), 30, 900) * 0.8
        return reverb(x, 2.6, 0.55)
    if name == "slam":
        t = tsec(2.5)
        x = np.sin(2 * np.pi * 60 * t * (1 - 0.2 * t)) * np.exp(-t / 0.12) * 1.2
        x += fft_filter(r.normal(0, 1, len(t)) * np.exp(-t / 0.05), 40, 2500)
        rat = np.zeros(len(t))
        for i in range(6):
            s = int((0.05 + i * 0.04) * SR)
            b = fft_filter(burst(r, 0.03, 0.006), 1500, 7000)
            rat[s:s + len(b)] += b * 0.3
        lock = np.zeros(len(t))
        s = int(0.6 * SR)
        lock[s:s + 1500] = fft_filter(burst(r, 1500 / SR, 0.002), 2000, 9000) * 0.6
        return reverb(x + rat + lock, 2.2, 0.45)
    if name == "knock":
        out = np.zeros(int(SR * 1.5))
        for i in range(3):
            s = int(i * 0.24 * SR)
            t = tsec(0.12)
            k = np.sin(2 * np.pi * 150 * t) * np.exp(-t / 0.03) + fft_filter(burst(r, 0.12, 0.012), 100, 1800) * 0.8
            out[s:s + len(k)] += k
        return reverb(out, 1.6, 0.4)
    if name == "glass_knock":
        out = np.zeros(int(SR * 1.6))
        for i in range(4):
            s = int(i * 0.2 * SR)
            t = tsec(0.25)
            k = np.sin(2 * np.pi * 110 * t) * np.exp(-t / 0.04)
            ring = (np.sin(2 * np.pi * 1350 * t) + 0.6 * np.sin(2 * np.pi * 2210 * t)) * np.exp(-t / 0.07) * 0.25
            k = k + ring + fft_filter(burst(r, 0.25, 0.01), 300, 5000) * 0.5
            out[s:s + len(k)] += k * (1.0 if i % 2 == 0 else 0.8)
        return reverb(out, 1.2, 0.3)
    if name == "drip":
        t = tsec(0.2)
        x = np.sin(2 * np.pi * (1700 * t - 2500 * t ** 2)) * np.exp(-t / 0.03) * 0.5
        return reverb(x, 1.8, 0.55)
    if name == "buzz":
        t = tsec(1.2)
        on = ((t % 0.6) < 0.4).astype(float)
        x = np.sign(np.sin(2 * np.pi * 165 * t)) * 0.3 + np.sin(2 * np.pi * 330 * t) * 0.2
        return fft_filter(x * on * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * t)), 100, 2500) * 0.5
    if name == "lock":
        out = np.zeros(int(SR * 0.8))
        for s_, a in ((0.0, 0.8), (0.12, 1.0)):
            b = fft_filter(burst(r, 0.03, 0.004), 1500, 9000) * a
            s = int(s_ * SR)
            out[s:s + len(b)] += b
        t = tsec(0.3)
        out[int(0.12 * SR):int(0.12 * SR) + len(t)] += np.sin(2 * np.pi * 2300 * t) * np.exp(-t / 0.05) * 0.2
        return reverb(out, 1.4, 0.4)
    if name == "click":
        out = np.zeros(int(SR * 0.3))
        for s_ in (0.0, 0.07):
            b = fft_filter(burst(r, 0.015, 0.002), 2000, 9000)
            out[int(s_ * SR):int(s_ * SR) + len(b)] += b
        return out
    if name == "power_down":
        t = tsec(1.6)
        f = 120 * np.exp(-t * 1.8) + 20
        ph = 2 * np.pi * np.cumsum(f) / SR
        x = (np.sin(ph) + 0.4 * np.sin(2 * ph)) * np.exp(-t / 0.9) * 0.6
        x[:2000] += fft_filter(burst(r, 2000 / SR, 0.004), 500, 8000)
        return reverb(x, 2.5, 0.4)
    if name == "keys":
        out = np.zeros(int(SR * 1.0))
        for i in range(10):
            s = int(r.uniform(0, 0.7) * SR)
            t = tsec(0.2)
            f = r.uniform(3000, 6500)
            out[s:s + len(t)] += np.sin(2 * np.pi * f * t) * np.exp(-t / 0.04) * r.uniform(0.1, 0.3)
        return reverb(out, 1.0, 0.3)
    if name == "door":
        t = tsec(2.2)
        sw = fft_filter(r.normal(0, 1, len(t)), 200, 1800) * np.sin(np.pi * t / 2.2) ** 2 * 0.25
        motor = np.sin(2 * np.pi * 110 * t) * 0.08 * np.sin(np.pi * t / 2.2)
        clunk = np.zeros(len(t))
        b = fft_filter(burst(r, 4000 / SR, 600 / SR), 80, 1500) * 0.6
        clunk[int(1.9 * SR):int(1.9 * SR) + len(b)] = b
        return reverb(sw + motor + clunk, 1.4, 0.35)
    if name == "thunder":
        t = tsec(5.0)
        crack = fft_filter(r.normal(0, 1, len(t)) * np.exp(-t / 0.25), 300, 4000) * 0.5
        rumble = fft_filter(np.cumsum(r.normal(0, 1, len(t))), 20, 160)
        rumble = rumble / (np.abs(rumble).max() + 1e-9) * np.clip(t / 0.2, 0, 1) * np.exp(-t / 1.8)
        return reverb(crack + rumble * 1.2, 3.0, 0.4)
    if name == "hum":
        # Ein Kind summt eine kleine Moll-Melodie (eigene Komposition)
        notes = [(69, .45), (72, .45), (71, .45), (69, .9), (64, .45), (67, .45), (65, .45), (64, .9), (62, .45), (64, .45), (65, .45), (64, 1.2)]
        out = []
        for m, d in notes:
            t = tsec(d)
            f = 440 * 2 ** ((m - 69) / 12) * (1 + 0.006 * np.sin(2 * np.pi * 5.5 * t))
            ph = 2 * np.pi * np.cumsum(f) / SR
            v = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)
            env = np.clip(t / 0.06, 0, 1) * np.clip((d - t) / 0.08, 0, 1)
            out.append(v * env)
        x = np.concatenate(out)
        x = fft_filter(x + np.random.default_rng(3).normal(0, 0.02, len(x)), 150, 1800) * 0.35
        return reverb(x, 3.2, 0.55)
    if name == "whoosh":
        t = tsec(0.5)
        return fft_filter(r.normal(0, 1, len(t)) * np.sin(np.pi * t / 0.5) ** 2, 300, 3000) * 0.18
    if name == "tick":
        t = tsec(0.06)
        return np.sin(2 * np.pi * 1600 * t) * np.exp(-t / 0.008) * 0.35
    if name == "heart":
        t = tsec(0.9)
        b = lambda s: np.sin(2 * np.pi * 48 * (t - s)) * np.exp(-np.clip(t - s, 0, None) / 0.07) * (t >= s)
        return (b(0) + 0.7 * b(0.28)) * 0.8
    raise ValueError(name)


SFX_GAIN = {"footsteps": 0.7, "footsteps_slow": 0.6, "paper": 0.5, "sting": 0.6, "low_hit": 0.8, "thud": 0.9, "slam": 1.0,
            "knock": 0.9, "glass_knock": 0.9, "drip": 0.5, "buzz": 0.5, "lock": 0.6, "click": 0.5, "power_down": 0.8,
            "keys": 0.6, "door": 0.7, "thunder": 0.9, "hum": 0.55, "whoosh": 0.5}


# --------------------------------------------------------------------- Atmo
def ambience(n, s):
    r = np.random.default_rng(s)
    t = np.arange(n) / SR
    drone = (0.5 * np.sin(2 * np.pi * 41.2 * t) + 0.35 * np.sin(2 * np.pi * 61.7 * t + 0.6 * np.sin(2 * np.pi * 0.07 * t)))
    drone *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t) ** 2
    room = fft_filter(r.normal(0, 1, n), 40, 400)
    hum = np.sin(2 * np.pi * 100 * t) * 0.03 + np.sin(2 * np.pi * 200 * t) * 0.012
    return drone * 0.05 + room * 0.04 + hum * 0.5


def rain(n, s):
    r = np.random.default_rng(s + 7)
    x = fft_filter(r.normal(0, 1, n), 700, 9000) * 0.18 + fft_filter(r.normal(0, 1, n), 80, 600) * 0.12
    drops = np.zeros(n)
    idx = r.integers(0, n, int(n / SR * 40))
    drops[idx] = r.normal(0, 1.2, len(idx))
    return x + fft_filter(drops, 1500, 8000) * 0.5


def static(n, s):
    r = np.random.default_rng(s + 3)
    x = fft_filter(r.normal(0, 1, n), 600, 5200) * 0.5
    cr = np.zeros(n)
    idx = r.integers(0, n, int(n / SR * 25))
    cr[idx] = r.normal(0, 3, len(idx))
    x += fft_filter(cr, 1000, 8000)
    return x * 0.22


def music(n, tension, s):
    """Dunkles Pad (Am–F–Dm–E) + Spannungsschichten, gesteuert von tension (0..1, pro Sample)."""
    t = np.arange(n) / SR
    chords = [(45, 48, 52), (41, 45, 48), (38, 41, 45), (40, 44, 47)]
    seg = 6.0
    pad = np.zeros(n)
    for ci in range(int(n / SR / seg) + 2):
        notes = chords[ci % 4]
        a, b = int(ci * seg * SR), int((ci + 1) * seg * SR + 1.5 * SR)
        a = max(a, 0)
        b = min(b, n)
        if a >= n:
            break
        tt = t[a:b] - ci * seg
        env = np.clip(tt / 1.5, 0, 1) * np.clip((seg + 1.5 - tt) / 1.5, 0, 1)
        v = np.zeros(b - a)
        for m in notes:
            f = 440 * 2 ** ((m - 69) / 12)
            for det in (-0.12, 0.12):
                for h in range(1, 6):
                    v += np.sin(2 * np.pi * (f * h + det * h) * tt + h) / h
        pad[a:b] += v * env
    pad = fft_filter(pad, 50, 700)
    pad = pad / (np.abs(pad).max() + 1e-9)
    T = tension
    high = (np.sin(2 * np.pi * 1318.5 * t) + np.sin(2 * np.pi * 1396.9 * t) + 0.7 * np.sin(2 * np.pi * 1975.5 * t))
    high *= (0.6 + 0.4 * np.sin(2 * np.pi * 7 * t)) * (T ** 2.5)
    sub = np.sin(2 * np.pi * 36.7 * t) * np.clip(T - 0.3, 0, 1)
    # Herzschlag – Tempo steigt mit Spannung
    bpm = 55 + 75 * T
    phase = np.cumsum(bpm / 60 / SR)
    beat_idx = np.nonzero(np.diff(np.floor(phase)) > 0)[0]
    hb = np.zeros(n)
    hs = sfx("heart")
    for i in beat_idx:
        g = np.clip((T[i] - 0.45) * 2, 0, 1)
        if g <= 0:
            continue
        e = min(n, i + len(hs))
        hb[i:e] += hs[:e - i] * g
    return pad * 0.038 + high * 0.007 + sub * 0.045 + hb * 0.34


def soft_limit(x, peak_ref=None):
    p = peak_ref or np.percentile(np.abs(x), 99.97)
    return np.tanh(x / max(p, 1e-6) * 1.05) * 0.88
