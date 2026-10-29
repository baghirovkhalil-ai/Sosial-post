"""Animasiyalı YouTube dərs videosu (16:9) — @khalil.marketingone brend stili.
Usage: python3 lessons/render_lesson.py lessons/<id>/script.json
Output: lessons/<id>/lesson.mp4 + thumb.jpg + frame-title.png

Səs: lokal Piper TTS (hər cümlə ayrıca -> bəndlər, altyazı və animasiya səslə tam sinxron).
Görüntü: lessons/template.html (Playwright ilə kadr-kadr), 25 fps.
"""
import json, os, re, subprocess, sys, wave, tarfile, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LESSONS = os.path.join(ROOT, "lessons")
ASSETS = os.path.join(ROOT, "engine", "assets")
FONT = lambda w, s: ImageFont.truetype(os.path.join(ASSETS, "fonts", f"Inter-{w}.otf"), s)
COURSE = {"meta": "META ADS COURSE", "google": "GOOGLE ADS COURSE"}
VOICE_DIR = os.path.expanduser("~/.cache/piper")
VOICE = os.path.join(VOICE_DIR, "en-us-ryan-high.onnx")
VOICE_URL = "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-ryan-high.tar.gz"
FPS = 25
SENT_GAP, SLIDE_PAD = 0.28, 0.7
STOP = set("a an the and or of to in on for is are be it this that you your with as at by from we will do don't not can how what so if its it's one two three four first second third".split())

def ensure_voice():
    if os.path.exists(VOICE): return
    os.makedirs(VOICE_DIR, exist_ok=True)
    tgz = os.path.join(VOICE_DIR, "v.tgz")
    subprocess.run(["curl", "-sSL", "--max-time", "600", "-o", tgz, VOICE_URL], check=True)
    with tarfile.open(tgz) as t: t.extractall(VOICE_DIR)
    os.remove(tgz)

def sentences(text):
    text = re.sub(r"[*_~]", "", text).strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text)
    return [p.strip() for p in parts if p.strip()]

def toks(s): return {w for w in re.findall(r"[a-z0-9']+", s.lower()) if w not in STOP and len(w) > 2}

def best_sentence(item, sents, start):
    it = toks(item); best, bi = -1, None
    for j in range(start, len(sents)):
        sc = len(it & toks(sents[j]["text"])) / max(1, len(it))
        if sc > best + 1e-9: best, bi = sc, j
    return bi if best > 0 else None

# ---------- audio ----------
def synth_all(sc):
    from piper import PiperVoice, SynthesisConfig
    voice = PiperVoice.load(VOICE); cfg = SynthesisConfig(length_scale=1.04)
    sr = voice.config.sample_rate
    chunks, t = [], 0.0
    for s in sc["slides"]:
        s["start"] = round(t, 3); lt = 0.0; s["sentences"] = []
        for txt in sentences(s["narration"]):
            pcm = b"".join(c.audio_int16_bytes for c in voice.synthesize(txt, syn_config=cfg))
            a = np.frombuffer(pcm, dtype=np.int16)
            d = len(a) / sr
            s["sentences"].append({"t0": round(lt, 3), "t1": round(lt + d, 3), "text": txt})
            chunks += [a, np.zeros(int(SENT_GAP * sr), np.int16)]; lt += d + SENT_GAP
        pad = SLIDE_PAD + (0.6 if s["type"] in ("title", "outro") else 0)
        chunks.append(np.zeros(int(pad * sr), np.int16)); lt += pad
        s["dur"] = round(lt, 3); t += lt
    audio = np.concatenate(chunks)
    return audio, sr, round(t, 3)

def reveals(s):
    se, r = s["sentences"], []
    first_min = 0.9
    if s["type"] in ("points", "steps", "summary"):
        j = 0
        for k, item in enumerate(s["items"]):
            bi = best_sentence(item, se, j)
            if bi is None: bi = min(len(se) - 1, j + (1 if k else 0))
            t = se[bi]["t0"] + 0.15
            if r and t <= r[-1] + 0.35: t = r[-1] + 0.6
            r.append(round(max(first_min, t), 3)); j = bi
    elif s["type"] == "compare":
        bi = best_sentence(" ".join(s["good"]) + " " + s["goodLabel"], se, 1) or max(1, len(se) // 2)
        r = [round(max(2.2, se[min(bi, len(se) - 1)]["t0"] + 0.1), 3)]
    elif s["type"] == "formula":
        bi = best_sentence(s["note"], se, 1) or max(1, len(se) - 2)
        r = [round(max(2.8, se[min(bi, len(se) - 1)]["t0"] + 0.1), 3)]
    return r

# ---------- thumbnail (static) ----------
def rich(d, xy, text, font, fill=(12, 14, 20), hl=(28, 78, 255), max_w=None, lh=1.12):
    x0, y = xy; tokens = []
    for part in re.split(r"(\*[^*]+\*)", text):
        if not part: continue
        hi = part.startswith("*")
        for w in part.strip("*").split(" "):
            if w: tokens.append((w, hi))
    lines, cur, cw = [], [], 0; sp = d.textlength(" ", font=font)
    for w, hi in tokens:
        tw = d.textlength(w, font=font)
        if max_w and cur and cw + sp + tw > max_w: lines.append(cur); cur, cw = [], 0
        cw += (sp if cur else 0) + tw; cur.append((w, hi))
    if cur: lines.append(cur)
    for ln in lines:
        x = x0
        for w, hi in ln: d.text((x, y), w, font=font, fill=hl if hi else fill); x += d.textlength(w, font=font) + sp
        y += int(font.size * lh)
    return y

def thumbnail(sc, out):
    W, H = 1280, 720
    im = Image.new("RGB", (W, H), (246, 247, 250)); d = ImageDraw.Draw(im)
    for y in range(H): t = y / H; d.line([(0, y), (W, y)], fill=(int(246 - 10 * t), int(247 - 8 * t), int(250 - 6 * t)))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((W - 560, -300, W + 200, 400), fill=(74, 123, 255, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(100)); im.paste(glow, (0, 0), glow)
    r = 260; cx, cy = 1000, 400
    dsk = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0)); dd = ImageDraw.Draw(dsk)
    for i in range(r, 0, -2):
        t = i / r; dd.ellipse((r - i, r - i, r + i, r + i), fill=(int(111 + (15 - 111) * t ** 1.4), int(147 + (47 - 147) * t ** 1.4), int(255 + (176 - 255) * t ** 1.4)))
    im.paste(dsk, (cx - r, cy - r), dsk)
    p = Image.open(os.path.join(ASSETS, "khalil-cut.png")).convert("RGBA"); p = p.crop(p.getbbox())
    k = 660 / p.height; p = p.resize((int(p.width * k), 660), Image.LANCZOS); im.paste(p, (cx - p.width // 2, H - p.height), p)
    d = ImageDraw.Draw(im)
    lab = f"{COURSE[sc['course']].replace(' COURSE', '')} · #{sc['num']}"; f = FONT("Black", 30)
    d.rounded_rectangle((56, 60, 56 + d.textlength(lab, font=f) + 48, 112), radius=26, fill=(28, 78, 255)); d.text((80, 70), lab, font=f, fill="white")
    rich(d, (56, 150), sc.get("thumb", sc["title"]), FONT("Black", 88), max_w=700, lh=1.02)
    d.text((56, 650), "KHALIL BAGHIROV", font=FONT("Black", 26), fill=(12, 14, 20))
    im.save(out, "JPEG", quality=90)

# ---------- video ----------
def render_video(spec, wav, mp4, title_png):
    from playwright.sync_api import sync_playwright
    frames = int(spec["total"] * FPS)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-", "-i", wav,
                           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        pg.add_init_script(f"window.SPEC = {json.dumps(spec)};")
        pg.goto("file://" + os.path.join(LESSONS, "template.html")); pg.evaluate("window.ready")
        for f in range(frames):
            pg.evaluate(f"window.renderAt({f / FPS})")
            ff.stdin.write(pg.screenshot(type="jpeg", quality=88))
            if f % 500 == 0: print(f"frame {f}/{frames}", flush=True)
        title_t = min(spec["slides"][0]["dur"] - 0.3, 3.2)
        pg.evaluate(f"window.renderAt({title_t})"); pg.screenshot(path=title_png)
        b.close()
    ff.stdin.close(); ff.wait()

def main(spec_path):
    ensure_voice()
    sc = json.load(open(spec_path)); out = os.path.dirname(os.path.abspath(spec_path))
    audio, sr, total = synth_all(sc)
    for s in sc["slides"]: s["reveals"] = reveals(s)
    raw = os.path.join(out, "_voice_raw.wav"); wav = os.path.join(out, "_voice.wav")
    with wave.open(raw, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(audio.tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", wav], check=True)
    spec = {"course": sc["course"], "courseLabel": COURSE[sc["course"]], "num": sc["num"], "title": sc["title"], "subtitle": sc["subtitle"],
            "total": total, "slides": sc["slides"]}
    mp4 = os.path.join(out, "lesson.mp4")
    tmp = os.path.join("/tmp", f"lesson-{sc['id']}-{os.getpid()}.mp4")  # render outside the repo, then move
    render_video(spec, wav, tmp, os.path.join(out, "frame-title.png"))
    shutil.move(tmp, mp4)
    thumbnail(sc, os.path.join(out, "thumb.jpg"))
    for f in (raw, wav): os.remove(f)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4], capture_output=True, text=True).stdout)
    print(f"{sc['id']}: {dur:.0f}s, {os.path.getsize(mp4) / 1e6:.1f} MB -> {mp4}")

if __name__ == "__main__":
    main(sys.argv[1])
