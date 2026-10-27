"""Generates an original royalty-free lo-fi/house beat. Usage: python3 music.py out.wav seconds seed"""
import sys, wave
import numpy as np

out, secs, seed = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
rng = np.random.default_rng(seed)
SR = 44100
bpm = int(rng.choice([96, 100, 104, 110, 118]))
beat = 60 / bpm
n = int(SR * secs)
mix = np.zeros(n)

PROGS = [[57, 53, 48, 55], [50, 46, 53, 48], [52, 48, 55, 50], [45, 41, 48, 43]]
prog = PROGS[seed % len(PROGS)]
minor = [0, 3, 7, 10]
major = [0, 4, 7, 11]

def env(length, a=0.01, r=0.3):
    t = np.arange(length) / SR
    e = np.minimum(1, t / a) * np.exp(-t / r)
    return e

def put(sig, start):
    s = int(start * SR)
    if s >= n: return
    e = min(n, s + len(sig))
    mix[s:e] += sig[: e - s]

def tone(freq, length, kind="tri"):
    t = np.arange(int(length * SR)) / SR
    if kind == "tri":
        return 2 * np.abs(2 * ((t * freq) % 1) - 1) - 1
    return np.sin(2 * np.pi * freq * t)

f = lambda m: 440 * 2 ** ((m - 69) / 12)
bar = beat * 4
t = 0.0
bi = 0
while t < secs:
    root = prog[bi % 4]
    chord = minor if bi % 4 in (0, 3) else major
    # pad
    for iv in chord:
        sig = tone(f(root + iv + 12), bar, "tri") * 0.05 * env(int(bar * SR), 0.25, bar)
        put(sig, t)
    # bass
    for q in range(4):
        sig = tone(f(root - 12), beat * 0.9, "sin") * 0.32 * env(int(beat * 0.9 * SR), 0.005, 0.35)
        put(sig, t + q * beat)
    # arp
    for q in range(8):
        note = root + 24 + chord[(q * 3 + bi) % 4]
        sig = tone(f(note), beat / 2, "sin") * 0.06 * env(int(beat / 2 * SR), 0.003, 0.12)
        put(sig, t + q * beat / 2)
    # drums
    for q in range(4):
        k = int(0.35 * SR); kt = np.arange(k) / SR
        kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-kt * 30)) * kt) * np.exp(-kt * 9) * 0.6
        put(kick, t + q * beat)
        if q in (1, 3):
            s = int(0.2 * SR)
            put(rng.standard_normal(s) * np.exp(-np.arange(s) / SR * 22) * 0.16, t + q * beat)
        for h in (0.5,):
            s = int(0.05 * SR)
            hat = np.diff(rng.standard_normal(s + 1)) * np.exp(-np.arange(s) / SR * 80) * 0.07
            put(hat, t + (q + h) * beat)
    t += bar
    bi += 1

fade = int(1.5 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)
mix[: int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))
mix = np.tanh(mix * 1.4) * 0.6
pcm = (mix * 32767).astype(np.int16)
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print(f"music {bpm}bpm {secs}s")
