"""YouTube dərs videosu (16:9) — @khalil.marketingone brend stili.
Usage: python3 lessons/render_lesson.py lessons/<id>/script.json
Output: lessons/<id>/lesson.mp4 + thumb.jpg  (səs: lokal Piper TTS, hər slayd ayrıca -> tam sinxron)
"""
import json, os, re, subprocess, sys, wave, tarfile, urllib.request, shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "engine", "assets")
FONT = lambda w, s: ImageFont.truetype(os.path.join(ASSETS, "fonts", f"Inter-{w}.otf"), s)
W, H = 1920, 1080
INK, BLUE, BLUE2, RED, MUTED, LINE, CARD = (12, 14, 20), (28, 78, 255), (74, 123, 255), (235, 60, 70), (107, 113, 134), (227, 230, 238), (255, 255, 255)
COURSE = {"meta": "META ADS COURSE", "google": "GOOGLE ADS COURSE"}
VOICE_DIR = os.path.expanduser("~/.cache/piper")
VOICE = os.path.join(VOICE_DIR, "en-us-ryan-high.onnx")
VOICE_URL = "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-ryan-high.tar.gz"

def ensure_voice():
    if os.path.exists(VOICE): return
    os.makedirs(VOICE_DIR, exist_ok=True)
    tgz = os.path.join(VOICE_DIR, "v.tgz")
    subprocess.run(["curl", "-sSL", "--max-time", "600", "-o", tgz, VOICE_URL], check=True)
    with tarfile.open(tgz) as t: t.extractall(VOICE_DIR)
    os.remove(tgz)

def tts(text, out):
    text = re.sub(r"[*_~]", "", text)
    subprocess.run([sys.executable, "-m", "piper", "-m", VOICE, "-f", out, "--sentence-silence", "0.35", "--length-scale", "1.04"],
                   input=text.encode(), check=True, capture_output=True)
    with wave.open(out) as w: return w.getnframes() / w.getframerate()

# ---------- drawing helpers ----------
def background():
    im = Image.new("RGB", (W, H), (246, 247, 250)); d = ImageDraw.Draw(im)
    for y in range(H):  # vertical gradient f6f7fa -> eceff4
        t = y / H; d.line([(0, y), (W, y)], fill=(int(246 - 10 * t), int(247 - 8 * t), int(250 - 6 * t)))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
    g.ellipse((W - 760, -420, W + 260, 520), fill=(74, 123, 255, 60)); g.ellipse((-420, H - 380, 420, H + 380), fill=(74, 123, 255, 40))
    glow = glow.filter(ImageFilter.GaussianBlur(140)); im.paste(glow, (0, 0), glow)
    dots = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(dots)
    for x in range(30, W, 44):
        for y in range(30, H, 44): dd.ellipse((x, y, x + 3, y + 3), fill=(12, 14, 20, 22))
    im.paste(dots, (0, 0), dots)
    return im

def rich(d, xy, text, font, fill=INK, hl=BLUE, max_w=None, lh=1.12):
    """Draw text with *word* highlighted; wraps to max_w. Returns bottom y."""
    x0, y = xy; tokens = []
    for part in re.split(r"(\*[^*]+\*)", text):
        if not part: continue
        hi = part.startswith("*")
        for w in part.strip("*").split(" "):
            if w: tokens.append((w, hi))
    lines, cur, cw = [], [], 0
    sp = d.textlength(" ", font=font)
    for w, hi in tokens:
        tw = d.textlength(w, font=font)
        if max_w and cur and cw + sp + tw > max_w: lines.append(cur); cur, cw = [], 0
        cw += (sp if cur else 0) + tw; cur.append((w, hi))
    if cur: lines.append(cur)
    size = font.size
    for ln in lines:
        x = x0
        for w, hi in ln:
            d.text((x, y), w, font=font, fill=hl if hi else fill); x += d.textlength(w, font=font) + sp
        y += int(size * lh)
    return y

def chrome(im, sc, idx, total, right_footer=True):
    d = ImageDraw.Draw(im)
    d.text((96, 64), "KHALIL BAGHIROV", font=FONT("Black", 26), fill=INK)
    d.ellipse((96 + d.textlength("KHALIL BAGHIROV", font=FONT("Black", 26)) + 12, 72, 96 + d.textlength("KHALIL BAGHIROV", font=FONT("Black", 26)) + 26, 86), fill=BLUE)
    lab = f"{COURSE[sc['course']]}  ·  LESSON {sc['num']:02d}"
    f = FONT("Bold", 22); tw = d.textlength(lab, font=f)
    d.rounded_rectangle((W - 96 - tw - 44, 56, W - 96, 100), radius=22, fill=CARD, outline=LINE, width=2)
    d.text((W - 96 - tw - 22, 66), lab, font=f, fill=INK)
    fs = FONT("SemiBold", 22)
    d.text((96, H - 78), "baghirovkhalil.com", font=fs, fill=MUTED)
    t = "Meta Ads  •  Google Ads  •  TikTok Ads"
    if right_footer: d.text((W - 96 - d.textlength(t, font=fs), H - 78), t, font=fs, fill=MUTED)
    if idx is not None:
        seg = (W - 192) / total
        for i in range(total):
            d.rounded_rectangle((96 + i * seg + 3, H - 30, 96 + (i + 1) * seg - 3, H - 26), radius=2, fill=BLUE if i <= idx else LINE)

PERSON = None
def person(h):
    global PERSON
    if PERSON is None:
        p = Image.open(os.path.join(ASSETS, "khalil-cut.png")).convert("RGBA"); PERSON = p.crop(p.getbbox())
    p = PERSON.copy(); r = h / p.height; return p.resize((int(p.width * r), h), Image.LANCZOS)

def disc(im, cx, cy, r):
    dsk = Image.new("RGBA", (r * 2, r * 2), (0, 0, 0, 0)); dd = ImageDraw.Draw(dsk)
    for i in range(r, 0, -2):  # radial gradient 6f93ff -> 1c4eff -> 0f2fb0
        t = i / r; c = (int(111 + (15 - 111) * t ** 1.4), int(147 + (47 - 147) * t ** 1.4), int(255 + (176 - 255) * t ** 1.4))
        dd.ellipse((r - i - int(r * .15 * (1 - t)), r - i - int(r * .2 * (1 - t)), r + i - int(r * .15 * (1 - t)), r + i - int(r * .2 * (1 - t))), fill=c)
    mask = Image.new("L", (r * 2, r * 2), 0); ImageDraw.Draw(mask).ellipse((0, 0, r * 2, r * 2), fill=255)
    im.paste(dsk, (cx - r, cy - r), mask)

def num_badge(d, x, y, n, color=BLUE, size=64):
    d.rounded_rectangle((x, y, x + size, y + size), radius=18, fill=color)
    f = FONT("Black", int(size * .45)); t = str(n); tw = d.textlength(t, font=f)
    d.text((x + (size - tw) / 2, y + size * .2), t, font=f, fill=CARD)

def card(d, box, fill=CARD, outline=LINE, r=28): d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=2)

# ---------- slide renderers: return list of (image, reveal_fraction) ----------
def s_title(sc, s):
    im = background(); chrome(im, sc, None, 1, False); d = ImageDraw.Draw(im)
    d.rounded_rectangle((96, 250, 96 + 300, 300), radius=25, fill=BLUE)
    d.text((120, 260), f"LESSON {sc['num']:02d}  /  30", font=FONT("Black", 24), fill=CARD)
    y = rich(d, (96, 340), sc["title"], FONT("Black", 104), max_w=1000, lh=1.05)
    rich(d, (96, y + 24), sc["subtitle"], FONT("SemiBold", 40), fill=MUTED, max_w=980)
    disc(im, 1460, 600, 330)
    p = person(820); im.paste(p, (1460 - p.width // 2, H - p.height), p)
    return [(im, 0)]

def s_big(sc, s, idx, n):
    im = background(); chrome(im, sc, idx, n); d = ImageDraw.Draw(im)
    if s.get("kicker"): d.text((160, 300), s["kicker"].upper(), font=FONT("Bold", 30), fill=BLUE)
    rich(d, (160, 360), s["text"], FONT("Black", 132), max_w=1600, lh=1.05)
    return [(im, 0)]

def items_slide(sc, s, idx, n, style):
    states = []; items = s["items"]
    for k in range(len(items) + 1):
        im = background(); chrome(im, sc, idx, n); d = ImageDraw.Draw(im)
        y = rich(d, (96, 170), s["title"], FONT("Black", 76), max_w=1700) + 30
        gap = min(150, (H - 140 - y) // max(1, len(items)))
        for i, it in enumerate(items[:k]):
            yy = y + i * gap
            if style == "steps":
                card(d, (96, yy, W - 96, yy + gap - 22))
                num_badge(d, 124, yy + (gap - 22 - 64) // 2, i + 1)
                rich(d, (220, yy + (gap - 22) // 2 - 26), it, FONT("Bold", 44), max_w=1500)
                if i < len(items) - 1: d.polygon([(150, yy + gap - 20), (170, yy + gap - 20), (160, yy + gap - 6)], fill=BLUE)
            elif style == "summary":
                d.rounded_rectangle((96, yy + 6, 150, yy + 60), radius=14, fill=BLUE)
                d.line([(110, yy + 34), (120, yy + 46), (138, yy + 20)], fill=CARD, width=7, joint="curve")
                rich(d, (180, yy + 6), it, FONT("Bold", 46), max_w=1600)
            else:
                num_badge(d, 96, yy, i + 1)
                rich(d, (196, yy + 4), it, FONT("Bold", 48), max_w=1620)
        states.append((im, 0 if k == 0 else 0.12 + 0.86 * (k - 1) / len(items)))
    return states

def s_formula(sc, s, idx, n):
    out = []
    for k in range(2):
        im = background(); chrome(im, sc, idx, n); d = ImageDraw.Draw(im)
        rich(d, (96, 170), s["title"], FONT("Black", 76), max_w=1700)
        card(d, (96, 380, W - 96, 600), fill=INK, outline=INK, r=36)
        f = FONT("Black", 64); tw = d.textlength(s["formula"], font=f)
        if tw > W - 300: f = FONT("Black", int(64 * (W - 300) / tw)); tw = d.textlength(s["formula"], font=f)
        d.text(((W - tw) / 2, 490 - f.size // 2 - 6), s["formula"], font=f, fill=CARD)
        if k: rich(d, (120, 680), s["note"], FONT("Bold", 52), max_w=1680)
        out.append((im, 0 if k == 0 else 0.45))
    return out

def s_compare(sc, s, idx, n):
    out = []
    for k in range(2):
        im = background(); chrome(im, sc, idx, n); d = ImageDraw.Draw(im)
        rich(d, (96, 170), s["title"], FONT("Black", 76), max_w=1700)
        cols = [(s["badLabel"], s["bad"], RED, "×"), (s["goodLabel"], s["good"], BLUE, "✓")]
        for c, (lab, its, col, mark) in enumerate(cols[:k + 1]):
            x0 = 96 + c * 880; card(d, (x0, 320, x0 + 848, 940))
            d.rounded_rectangle((x0 + 40, 360, x0 + 40 + d.textlength(lab.upper(), font=FONT("Black", 30)) + 48, 414), radius=27, fill=col)
            d.text((x0 + 64, 370), lab.upper(), font=FONT("Black", 30), fill=CARD)
            for i, it in enumerate(its):
                yy = 470 + i * 140
                d.ellipse((x0 + 40, yy, x0 + 96, yy + 56), fill=col)
                if c == 0:
                    d.line([(x0 + 56, yy + 16), (x0 + 80, yy + 40)], fill=CARD, width=7); d.line([(x0 + 80, yy + 16), (x0 + 56, yy + 40)], fill=CARD, width=7)
                else:
                    d.line([(x0 + 54, yy + 30), (x0 + 64, yy + 40), (x0 + 82, yy + 16)], fill=CARD, width=7, joint="curve")
                rich(d, (x0 + 124, yy + 4), it, FONT("Bold", 42), max_w=690)
        out.append((im, 0 if k == 0 else 0.5))
    return out

def s_outro(sc, s, idx, n):
    im = background(); chrome(im, sc, None, 1, False); d = ImageDraw.Draw(im)
    d.text((96, 250), "NEXT LESSON", font=FONT("Black", 30), fill=BLUE)
    y = rich(d, (96, 300), s["next"], FONT("Black", 92), max_w=1000, lh=1.05)
    d.rounded_rectangle((96, y + 50, 96 + 330, y + 140), radius=45, fill=INK)
    d.text((140, y + 72), "Subscribe", font=FONT("Black", 40), fill=CARD)
    d.text((96, y + 180), "Free lessons every day  ·  baghirovkhalil.com", font=FONT("SemiBold", 34), fill=MUTED)
    disc(im, 1460, 600, 330); p = person(820); im.paste(p, (1460 - p.width // 2, H - p.height), p)
    return [(im, 0)]

def render_slide(sc, s, idx, n):
    t = s["type"]
    if t == "title": return s_title(sc, s)
    if t == "big": return s_big(sc, s, idx, n)
    if t in ("points", "steps", "summary"): return items_slide(sc, s, idx, n, t)
    if t == "formula": return s_formula(sc, s, idx, n)
    if t == "compare": return s_compare(sc, s, idx, n)
    if t == "outro": return s_outro(sc, s, idx, n)
    raise ValueError(t)

def thumbnail(sc, out):
    im = background().resize((1280, 720)); d = ImageDraw.Draw(im)
    disc(im, 1000, 400, 260); p = person(660); im.paste(p, (1000 - p.width // 2, 720 - p.height), p)
    d.rounded_rectangle((56, 60, 56 + 330, 112), radius=26, fill=BLUE)
    d.text((80, 70), f"{COURSE[sc['course']].replace(' COURSE', '')} · #{sc['num']}", font=FONT("Black", 30), fill=CARD)
    words = sc.get("thumb", sc["title"])
    rich(d, (56, 150), words, FONT("Black", 88), max_w=700, lh=1.02)
    d.text((56, 650), "KHALIL BAGHIROV", font=FONT("Black", 26), fill=INK)
    im.save(out, "JPEG", quality=90)

def main(spec_path):
    ensure_voice()
    sc = json.load(open(spec_path)); out = os.path.dirname(os.path.abspath(spec_path))
    work = os.path.join(out, "_build"); shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
    slides = sc["slides"]; n = len(slides); concat, wavs, pad = [], [], 0.7
    content_n = sum(1 for s in slides if s["type"] not in ("title", "outro"))
    ci = 0
    for i, s in enumerate(slides):
        wav = os.path.join(work, f"a{i:02d}.wav"); dur = tts(s["narration"], wav) + pad; wavs.append(wav)
        idx = None
        if s["type"] not in ("title", "outro"): idx = ci; ci += 1
        states = render_slide(sc, s, idx, content_n)
        for k, (img, frac) in enumerate(states):
            nxt = states[k + 1][1] if k + 1 < len(states) else 1.0
            p = os.path.join(work, f"s{i:02d}_{k}.png"); img.save(p)
            concat.append((p, max(0.4, (nxt - frac) * dur)))
        if i == 0: img.save(os.path.join(out, "frame-title.png"))
    lst = os.path.join(work, "frames.txt")
    with open(lst, "w") as f:
        for p, dd in concat: f.write(f"file '{p}'\nduration {dd:.3f}\n")
        f.write(f"file '{concat[-1][0]}'\n")
    # audio: each slide wav + pad of silence
    alst = os.path.join(work, "audio.txt"); sil = os.path.join(work, "sil.wav")
    with wave.open(wavs[0]) as w0: sr = w0.getframerate()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r={sr}:cl=mono", "-t", str(pad), sil], check=True)
    with open(alst, "w") as f:
        for w in wavs: f.write(f"file '{w}'\nfile '{sil}'\n")
    audio = os.path.join(work, "voice.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", alst, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", audio], check=True)
    mp4 = os.path.join(out, "lesson.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", audio, "-map", "0:v", "-map", "1:a",
                    "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-crf", "22",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4], check=True)
    thumbnail(sc, os.path.join(out, "thumb.jpg"))
    shutil.rmtree(work, ignore_errors=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4], capture_output=True, text=True).stdout)
    print(f"{sc['id']}: {dur:.0f}s, {os.path.getsize(mp4) / 1e6:.1f} MB -> {mp4}")

if __name__ == "__main__":
    main(sys.argv[1])
