# Usage: python3 engine/voice.py posts/<id>/spec.json
# Needs posts/<id>/voice.mp3 — ONE take of the whole script with a [long pause] between scenes
# (one line of `vo` per scene, in order). Splits it on the N-1 longest silences, then writes:
#   voice_timing.json  {durs:[...], capT:[[a,b],...]}  -> render.mjs patches scene dur + caption timing
#   voice_aligned.wav  voice placed on the final video timeline (mono 44.1k)
import json, os, re, subprocess, sys
import numpy as np

spec_path = sys.argv[1]
d = os.path.dirname(spec_path)
spec = json.load(open(spec_path))
n = len(spec['scenes'])
SR = 44100
LEAD = 0.30          # voice starts this long after the scene cut (after the transition)
TAIL = 0.45          # breathing room after the line before the next cut
LAST_TAIL = 1.6      # CTA stays on screen a bit longer

raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(d, 'voice.mp3'), '-ac', '1', '-ar', str(SR),
                      '-f', 'f32le', '-'], capture_output=True, check=True).stdout
x = np.frombuffer(raw, dtype=np.float32).copy()

# frame energy (20 ms)
hop = int(SR * 0.02)
fr = len(x) // hop
e = np.sqrt((x[:fr * hop].reshape(fr, hop) ** 2).mean(1) + 1e-12)
db = 20 * np.log10(e)
thr = max(db.max() - 38, -50)
speech = db > thr
# silence runs
runs, i = [], 0
while i < fr:
    if not speech[i]:
        j = i
        while j < fr and not speech[j]:
            j += 1
        runs.append((i, j))
        i = j
    else:
        i += 1
first = int(np.argmax(speech)); last = fr - int(np.argmax(speech[::-1]))
inner = [r for r in runs if r[0] > first and r[1] < last]
cuts = sorted(sorted(inner, key=lambda r: r[1] - r[0], reverse=True)[:n - 1])
if len(cuts) != n - 1:
    sys.exit(f'voice.py: found {len(cuts)} pauses, need {n-1}')
bounds = [first] + [c for r in cuts for c in r] + [last]
segs = [(bounds[2 * k] * hop / SR, bounds[2 * k + 1] * hop / SR) for k in range(n)]

durs, capT, t, starts = [], [], 0.0, []
for k, (a, b) in enumerate(segs):
    L = b - a
    dur = round(max(2.6, LEAD + L + (LAST_TAIL if k == n - 1 else TAIL)), 2)
    starts.append(t)
    durs.append(dur)
    capT.append([LEAD, round(LEAD + L, 2)])
    t += dur
out = np.zeros(int((t + 1) * SR), dtype=np.float32)
fade = int(0.01 * SR)
for k, (a, b) in enumerate(segs):
    s = x[int((a - 0.04) * SR): int((b + 0.08) * SR)].copy()
    s[:fade] *= np.linspace(0, 1, fade); s[-fade:] *= np.linspace(1, 0, fade)
    o = int((starts[k] + LEAD - 0.04) * SR)
    out[o:o + len(s)] += s
pk = np.abs(out).max() or 1
out = out / pk * 0.89
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-',
                os.path.join(d, 'voice_aligned.wav')], input=out.tobytes(), check=True)
json.dump({'durs': durs, 'capT': capT, 'segs': segs}, open(os.path.join(d, 'voice_timing.json'), 'w'))
print('voice: scenes', durs, 'total', round(t, 2))
