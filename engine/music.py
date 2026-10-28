"""Original royalty-free ENERGETIC backing track, different per video.
Usage: python3 music.py out.wav seconds seed
The seed picks the genre (rotates), tempo, key and melody, so consecutive posts never share a track:
  0 tropical house · 1 phonk · 2 electro house · 3 future bass · 4 drum & bass · 5 afro house
"""
import sys, wave
import numpy as np
from scipy.signal import lfilter, butter

out, secs, seed = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
GENRES = ["tropical", "phonk", "electro", "future", "dnb", "afro"]
genre = GENRES[seed % len(GENRES)]
rng = np.random.default_rng(seed * 7 + 3)
SR = 44100
N = int(SR * (secs + 2)); L = np.zeros(N); R = np.zeros(N)

def midi(n): return 440 * 2 ** ((n - 69) / 12)
def add(buf, s, t, gain=1.):
    i = int(t * SR)
    if i >= N or i < 0: return
    j = min(N, i + len(s)); buf[i:j] += s[:j - i] * gain
def A(s, t, gl=1., gr=1.): add(L, s, t, gl); add(R, s, t, gr)
def env(n, a, d): t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
def lp(x, fc, o=2): b, a = butter(o, min(fc / (SR / 2), .99)); return lfilter(b, a, x)
def hp(x, fc, o=2): b, a = butter(o, fc / (SR / 2), "high"); return lfilter(b, a, x)
def bp(x, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], "band"); return lfilter(b, a, x)
def noise(n): return rng.standard_normal(n)
def saw(f, n, det=(-.1, 0, .1)):
    t = np.arange(n) / SR; s = np.zeros(n)
    for d in det: s += 2 * ((t * f * 2 ** (d / 12) + rng.random()) % 1) - 1
    return s / len(det)
def sq(f, n): return np.sign(np.sin(2 * np.pi * f * np.arange(n) / SR))
def verb(x, wet=.25):
    y = x.copy()
    for d, g in ((.029, .5), (.043, .42), (.067, .34), (.109, .26), (.151, .18)):
        k = int(d * SR); y[k:] += x[:-k] * g * wet
    return y
def kick(punch=1.0, dec=7.):
    n = int(.45 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * np.cumsum(46 + 150 * punch * np.exp(-t * 32)) / SR) * np.exp(-t * dec)
    return np.tanh(3 * s + noise(n) * np.exp(-t * 400) * .25) * .95
def clap():
    n = int(.4 * SR); x = hp(noise(n), 900); e = np.zeros(n)
    for k, o in enumerate([0, .008, .017, .026]):
        s = int(o * SR); e[s:] += np.exp(-np.arange(n - s) / SR / (.01 if k < 3 else .15))
    return x * e * .42
def snare():
    n = int(.3 * SR); t = np.arange(n) / SR
    return hp(noise(n), 1200) * env(n, .001, .08) * .5 + np.sin(2 * np.pi * 200 * t) * np.exp(-t * 28) * .4
def hat(open_=False): n = int((.2 if open_ else .05) * SR); return hp(noise(n), 7000) * env(n, .0005, .08 if open_ else .013) * (.28 if open_ else .2)
def shaker(): n = int(.07 * SR); return hp(noise(n), 6000) * env(n, .01, .02) * .17
def riser(dur):
    n = int(dur * SR); t = np.arange(n) / SR; x = noise(n); out = np.zeros(n)
    for k in range(0, n, 1024):
        fc = 400 + 7000 * (k / n) ** 2; out[k:k + 1024] = lp(hp(x[k:k + 1024], fc * .4), fc)
    return out * (t / dur) ** 2 * .35

# minor progressions (root, triad) — key shift by seed
PROGS = [[(57, [69, 72, 76]), (53, [69, 72, 77]), (48, [67, 72, 76]), (55, [67, 71, 74])],
         [(50, [69, 74, 77]), (46, [70, 74, 77]), (53, [69, 72, 77]), (48, [67, 72, 76])],
         [(52, [67, 71, 76]), (48, [67, 72, 76]), (55, [67, 71, 74]), (50, [66, 69, 74])],
         [(54, [69, 73, 78]), (50, [69, 74, 78]), (57, [69, 73, 76]), (52, [68, 71, 76])]]
shift = int(rng.integers(-2, 3))
PR = [(r + shift, [m + shift for m in ch]) for r, ch in PROGS[(seed // len(GENRES)) % len(PROGS)]]
BPM = {"tropical": 112, "phonk": 130, "electro": 126, "future": 150, "dnb": 172, "afro": 122}[genre] + int(rng.integers(-2, 3))
beat = 60 / BPM; bar = 4 * beat; nb = int(secs / bar) + 2
K = kick(1.2 if genre in ("phonk", "electro") else 1.0, 6 if genre == "phonk" else 7.5)
C, Sn = clap(), snare()
hook_rhythm = [(0, 2), (.75, 1), (1.5, 2), (2.5, 0), (3, 2), (3.5, 1)]
mel_seed = rng.permutation(6)
kicks = []

for b in range(nb):
    t0 = b * bar; root, ch = PR[b % 4]; intro = b == 0
    if genre in ("tropical", "electro", "afro", "future"):
        for q in range(4):
            if not intro or genre == "electro": A(K, t0 + q * beat); kicks.append(t0 + q * beat)
            if q in (1, 3) and not intro: A(C if genre != "future" else Sn, t0 + q * beat, .95, 1)
        for s16 in range(16):
            tt = t0 + s16 * beat / 4
            if genre == "electro":
                if s16 % 4 == 2: A(hat(True), tt, 1, .8)
            elif genre == "afro":
                if s16 in (3, 6, 10, 14): A(verb(bp(noise(int(.12 * SR)), 300, 900) * env(int(.12 * SR), .001, .04) * .5), tt, .8, 1.1)  # conga-ish
                A(shaker(), tt, .8, 1)
            else:
                A(shaker() if genre == "tropical" else hat(), tt, .7 + .3 * (s16 % 2), 1 - .3 * (s16 % 2))
    elif genre == "phonk":
        for pos in (0, 1.5, 2.75): A(K, t0 + pos * beat); kicks.append(t0 + pos * beat)
        A(Sn, t0 + beat); A(Sn, t0 + 3 * beat)
        for s16 in range(16):
            A(hat(), t0 + s16 * beat / 4, .8, 1)
            if b % 2 and s16 >= 12: A(hat() * .8, t0 + s16 * beat / 4 + beat / 8)
    else:  # dnb: two-step
        for pos in (0, 2.5): A(K, t0 + pos * beat); kicks.append(t0 + pos * beat)
        A(Sn, t0 + beat); A(Sn, t0 + 3 * beat)
        for s8 in range(8): A(hat(s8 % 4 == 2), t0 + s8 * beat / 2, .8, 1)

    # ---- bass
    if genre == "phonk":
        for pos, ln, slide in ((0, 1.4, 0), (1.5, 1.2, 3 if b % 2 else 5), (2.75, .9, 0)):
            n = int(beat * ln * SR); t = np.arange(n) / SR; f = np.full(n, midi(root - 24))
            if slide: f = midi(root - 24) + (midi(root - 24 + slide) - midi(root - 24)) * np.clip((t - .1) / .08, 0, 1)
            A(np.tanh(3.5 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * env(n, .003, .45) * .55, t0 + pos * beat)
    elif genre == "dnb":
        n = int(bar * SR); A(np.tanh(2 * lp(saw(midi(root - 24), n, (-.05, .05)), 300)) * env(n, .01, 1.2) * .5, t0)
    else:
        pat = {"tropical": [(0, 0), (1.5, 0), (2, 12), (3, 0), (3.5, 7)], "afro": [(0, 0), (.75, 0), (1.5, 7), (2.5, 0), (3.25, 12)],
               "electro": [(x / 2, 0) for x in range(8) if x % 2], "future": [(0, 0), (2, 0), (2.75, 0), (3.5, 0)]}[genre]
        for pos, oc in pat:
            n = int(beat * (.45 if genre != "future" else .7) * SR)
            if genre == "electro": s = np.tanh(2.5 * lp(saw(midi(root - 12 + oc), n, (-.04, .04)), 1100)) * env(n, .002, .12) * .45
            else: s = np.tanh(1.6 * np.sin(2 * np.pi * midi(root - 12 + oc) * np.arange(n) / SR)) * env(n, .004, .22) * .5
            A(s, t0 + pos * beat)

    # ---- harmony
    if genre in ("electro", "future", "dnb"):
        poss = (0.5, 1.5, 2.5, 3.25, 3.75) if genre != "dnb" else (0, 1.75, 2.5)
        for pos in poss:
            n = int((.22 if genre != "future" else .35) * SR); s = sum(saw(midi(m), n) for m in ch)
            s = lp(s, 4500 if genre != "future" else 3000) * env(n, .003, .08 if genre != "future" else .16) * .12
            A(s, t0 + pos * beat, .9, 1.1); A(s * .4, t0 + pos * beat + .11, 1.1, .6)
    elif genre == "phonk":
        riff = [(0, 2), (.5, 2), (.75, 1), (1.25, 2), (1.75, 2), (2.25, 1), (2.75, 0), (3.25, 1), (3.5, 0)]
        for pos, k in riff:
            n = int(.35 * SR); f0 = midi(ch[k] + 12); s = sq(f0, n) + sq(f0 * 1.48, n)
            A(verb(bp(s, 500, 3500) * np.exp(-np.arange(n) / SR * 9) * .12, .3), t0 + pos * beat, 1.1, .85)
    else:  # tropical / afro: marimba-ish arps + offbeat plucks
        seq = [0, 1, 2, 1, 0, 2, 1, 2]
        for k in range(8):
            m = ch[seq[(k + mel_seed[0]) % 8]] + (12 if k in (2, 5) else 0); n = int(.4 * SR); t = np.arange(n) / SR
            s = (np.sin(2 * np.pi * midi(m) * t) + .35 * np.sin(2 * np.pi * midi(m) * 4 * t) * np.exp(-t * 30)) * np.exp(-t * 7)
            A(s * .11, t0 + k * beat / 2, 1.1 - .3 * (k % 2), .8 + .3 * (k % 2))
        for q in range(4):
            n = int(.22 * SR); s = sum(sq(midi(m), n) for m in ch)
            A(lp(s, 2500) * env(n, .002, .06) * .045, t0 + (q + .5) * beat)

    # ---- lead hook (every 2nd bar, melody differs per seed)
    if b % 2 == 1:
        for k, (pos, idx) in enumerate(hook_rhythm):
            m = ch[(idx + mel_seed[k % 6]) % 3] + 12 + (12 if k == 3 else 0)
            n = int(beat * .5 * SR); t = np.arange(n) / SR
            if genre in ("tropical", "afro"):
                s = 2 * ((t * midi(m)) % 1) - 1; s = bp(s, 700, 1300) * 1.4 + bp(s, 2200, 3000)  # vocal-chop formant
                A(verb(s * env(n, .01, .12) * .2), t0 + pos * beat, .9, 1.1)
            elif genre != "phonk":
                s = (sq(midi(m), n) * .4 + np.sin(2 * np.pi * midi(m) * 2 * t) * .3) * env(n, .002, .12) * .09
                A(lp(s, 5000), t0 + pos * beat, 1.1, .8)
    # riser into every 4th bar
    if b % 4 == 3: A(riser(bar), t0, 1, 1)

# sidechain pump on everything except kicks
kick_only = np.zeros(N)
for kt in kicks: add(kick_only, K, kt)
pump = np.ones(N)
for kt in kicks:
    i = int(kt * SR); n = min(int(beat * SR), N - i)
    if n > 0: pump[i:i + n] = np.minimum(pump[i:i + n], 1 - .55 * np.exp(-np.arange(n) / SR / .1))
L = (L - kick_only) * pump + kick_only; R = (R - kick_only) * pump + kick_only
st = np.stack([L, R], 1)[:int(secs * SR)]
st[:int(.02 * SR)] *= np.linspace(0, 1, int(.02 * SR))[:, None]
fo = int(min(1.5, secs / 4) * SR); st[-fo:] *= (np.linspace(1, 0, fo) ** 1.5)[:, None]
st = np.tanh(st / (np.max(np.abs(st)) + 1e-9) * 1.6) * .9
w = wave.open(out, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
print(f"music: {genre} {BPM}bpm seed={seed}")
