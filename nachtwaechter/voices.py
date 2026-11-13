# -*- coding: utf-8 -*-
"""Figurenstimmen mit Piper (neuronale Offline-TTS) + ffmpeg-Nachbearbeitung."""
import os, hashlib, subprocess, wave
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
VDIR = os.path.join(ROOT, "voices")
CACHE = os.path.join(ROOT, "build", "tts")
os.makedirs(CACHE, exist_ok=True)
SR = 44100

# name: (Modell, length_scale, noise_scale, noise_w, ffmpeg-Kette, Lautstärke)
PROFILES = {
    # Jonas, 19 – Erzähler
    "jonas": ("thorsten", 0.92, 0.6, 0.75,
              "highpass=f=80,lowpass=f=7800,acompressor=threshold=-18dB:ratio=3:attack=5:release=80", 1.0),
    # Walter, 68 – alter Nachtwächter
    "walter": ("karlsson", 1.0, 0.6, 0.8,
               "rubberband=pitch=0.86:tempo=1.0,highpass=f=70,lowpass=f=6500,aecho=0.8:0.4:40:0.12", 1.0),
    # Walter draußen hinter der Glastür (gedämpft, Regen)
    "walter_door": ("karlsson", 0.92, 0.7, 0.9,
                    "rubberband=pitch=0.86,highpass=f=150,lowpass=f=2600,aecho=0.8:0.6:60|140:0.3|0.2", 1.0),
    # Mama am Handy (Lautsprecher)
    "mama": ("kerstin", 0.95, 0.6, 0.8, "highpass=f=380,lowpass=f=3400", 0.85),
    # "Mama" aus Lager 3 – gedämpft durch die Tür, hallig
    "mama_door": ("kerstin", 1.05, 0.75, 0.9,
                  "highpass=f=120,lowpass=f=1900,aecho=0.8:0.85:180|420|760:0.5|0.35|0.2", 1.0),
    # Mia, ~7 Jahre
    "mia": ("ramona", 1.0, 0.6, 0.8,
            "rubberband=pitch=1.32,highpass=f=150,lowpass=f=8000,aecho=0.8:0.5:50|110:0.2|0.12", 0.95),
    # Mia, wenn die Maske fällt
    "mia_dark": ("ramona", 1.35, 0.8, 0.9,
                 "rubberband=pitch=0.62,lowpass=f=4500,aecho=0.8:0.85:120|300|600:0.5|0.4|0.3", 1.0),
}

_VOICES = {}


def _voice(name):
    if name not in _VOICES:
        from piper import PiperVoice
        _VOICES[name] = PiperVoice.load(os.path.join(VDIR, f"de-{name}-low.onnx"))
    return _VOICES[name]


def _fix(ph):
    """Piper zerlegt 'ç' (ich-Laut) per NFD in c + Cedille – wieder zusammensetzen."""
    out = []
    for p in ph:
        if p == "̧" and out and out[-1] == "c":
            out[-1] = "ç"
        else:
            out.append(p)
    return out


def _synth_raw(model, text, ls, ns, nw):
    from piper import SynthesisConfig
    v = _voice(model)
    cfg = SynthesisConfig(length_scale=ls, noise_scale=ns, noise_w_scale=nw, normalize_audio=True)
    sr = v.config.sample_rate
    parts = []
    for sent in v.phonemize(text):
        ids = v.phonemes_to_ids(_fix(sent))
        a = v.phoneme_ids_to_audio(ids, cfg)
        parts.append(np.asarray(a, dtype=np.float32).flatten())
        parts.append(np.zeros(int(0.22 * sr), np.float32))
    a = np.concatenate(parts[:-1]) if parts else np.zeros(1, np.float32)
    return a, sr


def _read(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768


def _write(path, x, sr):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def speak(text, profile="jonas"):
    """Gibt float64-Audio (44.1 kHz, mono) zurück."""
    model, ls, ns, nw, chain, gain = PROFILES[profile]
    key = hashlib.md5(repr((PROFILES[profile], text, 3)).encode()).hexdigest()[:16]
    out = os.path.join(CACHE, f"{profile}_{key}.wav")
    if not os.path.exists(out):
        a, sr = _synth_raw(model, text, ls, ns, nw)
        raw = out + ".raw.wav"
        _write(raw, a * 0.9, sr)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", f"aresample=44100,{chain}",
                        "-ar", "44100", "-ac", "1", out], check=True)
        os.remove(raw)
    x = _read(out)
    nz = np.nonzero(np.abs(x) > 0.008)[0]
    if len(nz):
        x = x[max(0, nz[0] - 400): nz[-1] + int(0.1 * SR)]
    return x / (np.abs(x).max() + 1e-9) * 0.8 * gain


def creature(text):
    """Mehrere Stimmen gleichzeitig, tief und verschoben – das Ding, das alle imitiert."""
    layers = [speak(text, p) for p in ("walter", "mama_door", "mia_dark")]
    n = max(len(l) for l in layers)
    mix = np.zeros(n + 4000)
    for i, l in enumerate(layers):
        # auf gleiche Länge strecken (grob) durch Interpolation
        xi = np.linspace(0, len(l) - 1, n)
        mix[i * 900: i * 900 + n] += np.interp(xi, np.arange(len(l)), l) * (0.8 if i else 1.0)
    return mix / (np.abs(mix).max() + 1e-9) * 0.85


if __name__ == "__main__":
    import sys
    v = _voice("thorsten")
    print(_fix(v.phonemize("Ich hab nicht nachgedacht, Mädchen.")[0]))
    for p in PROFILES:
        x = speak("Ich bin um sechs zurück. Keine Minute früher, hörst du?", p)
        print(p, round(len(x) / SR, 2), "s")
