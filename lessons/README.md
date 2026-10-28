# YouTube dərsləri — Meta Ads + Google Ads (ingiliscə)

Khalil Baghirov YouTube kanalı üçün gündəlik pulsuz dərs seriyası.
**Hər gün 2 video:** Meta Ads dərsi **18:00**, Google Ads dərsi **19:00** (Asia/Baku). Hər kurs 30 dərs (`curriculum.json`).
Format: 16:9 uzun video (YouTube "video", Short deyil), 2.5–4 dəqiqə, ingiliscə, sadə və praktik.

## Fayllar
- `curriculum.json` — 30 Meta + 30 Google dərs başlığı (sıra dəyişməz).
- `progress.json` — növbəti dərs nömrələri və paylaşılanların siyahısı.
- `<course>-<NN>/script.json` — ssenari (format aşağıda); render sonrası `lesson.mp4`, `thumb.jpg`, `frame-title.png`.
- `render_lesson.py` — slaydlar (PIL, brend stili) + lokal Piper TTS səsi (hər slayd ayrıca, tam sinxron) + ffmpeg.

## Gündəlik iş qaydası (scheduled task bunu edir)
1. `git pull`. `progress.json`-dan növbəti `meta` və `google` nömrəsini götür (30-dan böyükdürsə həmin kurs bitib — keç).
2. Hər kurs üçün `lessons/<course>-<NN>/script.json` yaz:
   - `title` = curriculum-dakı başlıq (qısaldıla bilər), `subtitle` 1 sətir, `thumb` 3–5 söz, bir sözü `*ulduz*` ilə vurğula.
   - 8–10 slayd: `title` → `big` → 4–6 məzmun slaydı (`points`/`steps`/`compare`/`formula`) → `summary` (homework) → `outro`.
   - Bütün narration cəmi 450–650 söz. Birinci slayd: "Hi, I'm Khalil Baghirov, and welcome to lesson N of this free … course."
   - `outro.next` = curriculum-da növbəti dərsin başlığı (30-cu dərsdə: "Course complete — what to learn next").
   - Bəndlər qısa (≤ 8 söz), `points`/`steps` ≤ 4–5 bənd, `compare` hər tərəfdə 3 bənd.
   - Faktlar dəqiq olsun: platformaların rəsmi sənədlərinə uyğun yaz, uydurma rəqəm/statistika yazma. Əmin deyilsənsə WebSearch et.
   - Əvvəlki dərsə qısa istinad et ("In lesson 4 we…") ki, seriya kimi hiss olunsun.
3. Render: `python3 lessons/render_lesson.py lessons/<id>/script.json` (Piper yoxdursa: `pip install --break-system-packages piper-tts`; səs modeli avtomatik GitHub-dan yüklənir).
   `frame-title.png`, `thumb.jpg` və videodan 2 kadra (`ffmpeg -ss 60 -i lesson.mp4 -frames:v 1 x.jpg`) Read ilə bax: mətn kəsilməsin, üst-üstə düşməsin.
4. Commit (`script.json`, `lesson.mp4`, `thumb.jpg`, `frame-title.png`) + push `main`.
5. Metricool (brand `7685976`, timezone `Asia/Baku`): əvvəlcə `getScheduledPosts` ilə həmin saata artıq dərs qoyulubmu yoxla — dublikat yaratma. Sonra `createScheduledPost`:
   - providers `[{"network":"youtube"}]`, media `https://raw.githubusercontent.com/baghirovkhalil-ai/Sosial-post/main/lessons/<id>/lesson.mp4`
   - `youtubeData`: `{"title": youtube_title (≤100 simvol), "type":"video", "privacy":"public", "madeForKids":false, "category":"EDUCATION", "tags":[...], "isAiGeneratedContent":true}`
   - `videoThumbnailUrl` = `.../thumb.jpg` (xəta versə, thumbnail-siz yenidən göndər).
   - `text` (YouTube təsviri): description + boş sətir + "In this lesson:" və slayd başlıqları siyahısı + boş sətir +
     "Free lessons every day: Meta Ads at 18:00 and Google Ads at 19:00 (Baku time)." + "Instagram: @khalil.marketingone" +
     "Narration is AI-generated; content written by Khalil Baghirov." + 4–6 hashtag (#metaads #facebookads … / #googleads #ppc …).
   - Tarix: `progress.json`-dakı `next_date` (həmişə 1 gün qabaqcadan hazırlanır). Meta → həmin tarix 18:00, Google → 19:00. `next_date` keçmişdədirsə, sabahkı tarixi götür. Həmin slotda artıq dərs varsa, o dərs artıq planlanıb — `next_date`-i 1 gün irəli at və təkrar planlama.
6. `progress.json`-u yenilə (nömrələr +1, `next_date` +1 gün, `posted`-ə `{id, date, time}` əlavə et), `content/log.md`-yə sətir yaz, push.

## Playlist
Metricool playlist yarada bilmir. Kanalda iki playlist bir dəfə əl ilə yaradılır: **"Meta Ads Course (Free)"** və **"Google Ads Course (Free)"**, videolar ora əlavə olunur.
