# sosial-post — @khalil.marketingone gündəlik kontent sistemi

Bu repo Khalil-in (freelance digital marketoloq, Bakı) Instagram + YouTube Shorts səhifəsi üçün
hər gün avtomatik post hazırlamaq və Metricool ilə planlaşdırmaq üçündür.
Repo **public**-dir: şəkillər/videolar Metricool-a buradan `raw.githubusercontent.com` linki ilə verilir.
Heç vaxt bura şəxsi və ya müştəri məlumatı yazma.

## Hədəf
İzləyici artımı (kəşfət) + müştəri müraciəti. Auditoriya: Bakıda kiçik/orta biznes sahibləri,
SMM-çilər, marketinq öyrənənlər. Dil: Azərbaycan dili, səmimi, sadə, "sən" müraciəti.

## Brend stili v3 "Editorial Kinetic" (2026-10-29, Khalil təsdiqlədi — dəyişmə)
- AĞ KAĞIZ FON #fafaf7 + incə qara grid (yavaş axır) + yuxarı-sağda yumşaq laym parıltı + yüngül dən (grain).
  3D kürə, mavi rəng YOXDUR.
- Rənglər: qara #0b0b0c (mətn, çərçivə), LAYM #d4ff3a (marker/vurğu), qırmızı #ff3b2f (yalnız səhv/xəbərdarlıq),
  boz #6e6e73 (kiçik mətn).
- Şrift: **Unbounded** (başlıqlar, rəqəmlər) + **Onest** (mətn, altyazı) — `engine/assets/fonts/fonts.css`.
  Hər ikisi ə/ğ/ş/İ/ı-nı tam göstərir. Başqa şrift işlətmə (Manrope/Sora/Space Grotesk-də "ə" qırılır).
- Kartlar: ağ, 4px qara çərçivə, sərt ofset kölgə (neo-brutal). Stikerlər: laym/qara/qırmızı, bir az əyik.
- Reel: yuxarıda "KHALIL BAGHIROV" + kateqoriya pill + story kimi seqmentli progress; səhnələr arası
  laym pərdə keçidi; altyazı aşağıda qutusuz, cari söz laym fonla (karaoke).
- Sonda həmişə Khalil-in şəkli laym dairədən "çıxır" (assets/khalil-cut.png — `engine/retouch.py` ilə
  rötuş edilib; orijinal khalil-cut-orig.png) + qara düymə + @khalil.marketingone.
- HƏR ŞEY VİDEO (reel) kimi gedir — şəkil/karusel post yoxdur. Cover = hook səhnəsinin son kadrı (cover.jpg).
- Musiqi: hər video üçün fərqli ENERJİLİ trek (engine/music.py seed-ə görə janr seçir:
  tropical, phonk, electro, future bass, drum&bass, afro). Ardıcıl iki reel-də eyni janr olmasın —
  `musicSeed % 6` fərqli olsun.
- Videoda emoji işlətmə (şrift göstərmir). Caption-da emoji olar.

## Səs (voiceover) — ElevenLabs
- Hər səhnədə `vo` sahəsi: diktorun deyəcəyi 1–2 cümlə (danışıq dili, rəqəmlər rəqəmlə, "AZN" yox "manat").
- ElevenLabs: model `eleven_v3`, səs **Ibrahim Mammadli** (`BQgh92MxG7QAtCA8wY7O`, az), generations_count 1.
  Mətn: `[excited] <vo1> [long pause] <vo2> [long pause] ...` — bütün video BİR take.
- mp3-ü `posts/<id>/voice.mp3` kimi qoy → `render.mjs` avtomatik: `engine/voice.py` take-i pauzalardan
  səhnələrə bölür, səhnə müddətlərini səsə uyğunlaşdırır, altyazı = `vo` (söz-söz karaoke, səslə sinxron),
  musiqi səsin altında yatır (ducking). voice.mp3 yoxdursa video səssiz (yalnız musiqi) render olunur.
- Səs faylını yükləmək üçün `storage.googleapis.com` domeni icazəli olmalıdır (claude.ai → Settings → Capabilities).
  Bloklanıbsa, səssiz render et və Khalil-ə qeyd et.

## Sütunlar (rotasiya)
AI (praktik alətlər/promptlar) · Ads (Meta/TikTok reklam) · Instagram (böyümə, Reels) ·
Psixologiya (satış/qiymət psixologiyası) · Biznes (Bakı SMB praktik məsləhət).
HƏR GÜN 2 REEL: saat **12:00** və **20:00** (karusel yoxdur — ideas.json-da "carousel" olan ideyanı reel kimi hazırla).
Ardıcıl iki slotda eyni sütun olmasın (12:00 və 20:00 fərqli sütun olsun).

## Gündəlik iş qaydası (scheduled task bunu edir)
1. `git pull`. `content/ideas.json`-da ilk `"status":"todo"` ideyanı götür
   (əvvəlki slotla eyni sütundursa, növbətini). 5-dən az todo qalıbsa, WebSearch ilə
   aktual mövzulara baxıb 10 yeni ideya əlavə et.
2. `posts/<YYYY-MM-DD>-<slug>/spec.json` yaz (format aşağıda). Reel 28–40 san, 6–8 səhnə. Birinci səhnə güclü qarmaq (sual, rəqəm, ziddiyyət).
   Faktlar dəqiq olsun — əmin olmadığın rəqəmi yazma.
3. Render: `node engine/render.mjs posts/<id>/spec.json`
   (reel → reel.mp4 + cover.jpg; karusel → slide-N.png). Ən azı 3 kadra/slayda Read ilə bax:
   mətn kəsilməsin, üst-üstə düşməsin, Azərbaycan hərfləri düz olsun.
4. `music.wav`-ı commit etmə (.gitignore). Commit + push to `main`.
5. Metricool (brand id `7685976`, timezone `Asia/Baku`) ilə **boş slota** planla.
   Slotlar: hər gün 12:00 və 20:00. Sabahdan başlayaraq (maks. 3 gün irəli) boş olan ilk slotu seç.
   Bir işə salınmada **2 reel** hazırla — ən erkən iki boş slot üçün (adətən bir günün 12:00 və 20:00-ı).
   - Media URL: `https://raw.githubusercontent.com/baghirovkhalil-ai/Sosial-post/main/posts/<id>/<fayl>`
   - Reel: providers instagram + youtube; instagramData.type `REEL`, isAiGenerated true;
     youtubeData {title (≤90 simvol, sonda #shorts), type "short", privacy "public", madeForKids false,
     category "EDUCATION", isAiGeneratedContent true}; videoThumbnailUrl = cover.jpg (YouTube thumbnail
     xəta verə bilər — normaldır).
   - Caption: 1-ci sətir qarmaq, 3–6 qısa sətir dəyər, 1 CTA (yadda saxla / paylaş / "X" yaz DM-ə),
     **maks. 5 hashtag** (Instagram dekabr 2025-dən 5-dən çoxuna icazə vermir), məs. #rəqəmsalmarketinq #bakı #smm.
     Mövzunun açar sözü caption-un 1-ci sətrində olsun (Instagram axtarışı üçün).
   - Əvvəlcə getScheduledPosts ilə həmin günə artıq post qoyulubmu yoxla — dublikat yaratma.
6. `content/ideas.json`-da ideyanı `"status":"done","date":"..."` et, `content/log.md`-yə 1 sətir yaz, push.
7. Hər bazar günü əlavə olaraq son 7 günün Instagram statistikasına bax (getAnalyticsDataByMetrics),
   ən yaxşı/zəif postu `content/log.md`-yə yaz və növbəti həftənin ideyalarını ona görə prioritetləşdir.

## spec.json formatı
```json
{"id":"2026-10-28-slug","type":"reel|carousel","tag":"META ADS","musicSeed":7,
 "scenes":[ {"kind":"...","dur":3.5,"cap":"altyazı (yalnız reel)", ...} ]}
```
Mətn işarələri: `*söz*` laym marker, `_söz_` qara pill + laym mətn, `~söz~` qırmızı.
Səhnə növləri:
- `hook` {small, big, sub, stat?:{label,value,suffix}} — big qısa olsun (1–3 söz)
- `step` {num:"01", title, sub, color?: cyan(laym dolu)|yellow(qara dolu)|red(qırmızı kontur), visual?: target|bars|cross}
- `list` {title, items:[...]} (≤5 qısa bənd)
- `compare` {title, bad, good, badLabel?, goodLabel?}
- `stat` {small, value:number, suffix, label, visual?}
- `chat` {title, msgs:[{from:"user"|"ai", text}]} — AI prompt nümunələri üçün
- `cta` {small, big, sub, button} — həmişə sonuncu
`dur` saniyədir (reel üçün; karuseldə nəzərə alınmır). Mətni oxumağa vaxt ver: ~12 söz = 3.5 san.

## YouTube dərsləri (ayrı sistem)
Meta Ads + Google Ads ingiliscə uzun dərs videoları: hər gün 18:00 (Meta) və 19:00 (Google).
Bütün qaydalar `lessons/README.md`-dədir. Reels qaydaları (yuxarıdakılar) dərslərə tətbiq olunmur.
