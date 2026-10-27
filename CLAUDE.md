# sosial-post — @khalil.marketingone gündəlik kontent sistemi

Bu repo Khalil-in (freelance digital marketoloq, Bakı) Instagram + YouTube Shorts səhifəsi üçün
hər gün avtomatik post hazırlamaq və Metricool ilə planlaşdırmaq üçündür.
Repo **public**-dir: şəkillər/videolar Metricool-a buradan `raw.githubusercontent.com` linki ilə verilir.
Heç vaxt bura şəxsi və ya müştəri məlumatı yazma.

## Hədəf
İzləyici artımı (kəşfət) + müştəri müraciəti. Auditoriya: Bakıda kiçik/orta biznes sahibləri,
SMM-çilər, marketinq öyrənənlər. Dil: Azərbaycan dili, səmimi, sadə, "sən" müraciəti.

## Brend stili (dəyişmə — səhifə vahid görünməlidir)
- Fon: tünd kosmik (#05070f), grid, ulduzlar, göy/firuzəyi/qırmızı işıq ləkələri.
- Rənglər: firuzəyi #2ee6d6 (əsas), qırmızı #ff2d55 (səhv/xəbərdarlıq), sarı #ffc83d (rəqəm/nəticə).
- Şrift: Inter Black/ExtraBold. Böyük başlıqlar UPPERCASE + firuzəyi/qırmızı "glitch" kölgə.
- Yuxarıda kateqoriya etiketi (məs. "META ADS", "AI + MARKETİNQ"), reel-də progress bar.
- Sonda həmişə Khalil-in şəkli + ağ düymə + @khalil.marketingone.
- Videoda emoji işlətmə (şrift göstərmir). Caption-da emoji olar.

## Sütunlar (rotasiya)
AI (praktik alətlər/promptlar) · Ads (Meta/TikTok reklam) · Instagram (böyümə, Reels) ·
Psixologiya (satış/qiymət psixologiyası) · Biznes (Bakı SMB praktik məsləhət).
Ardıcıl iki gün eyni sütun olmasın. Həftədə ~4 reel + 3 karusel.

## Gündəlik iş qaydası (scheduled task bunu edir)
1. `git pull`. `content/ideas.json`-da ilk `"status":"todo"` ideyanı götür
   (dünən ilə eyni sütundursa, növbətini). 5-dən az todo qalıbsa, WebSearch ilə
   aktual mövzulara baxıb 10 yeni ideya əlavə et.
2. `posts/<YYYY-MM-DD>-<slug>/spec.json` yaz (format aşağıda). Reel 25–35 san, 6–8 səhnə;
   karusel 6–9 slayd. Birinci səhnə güclü qarmaq (sual, rəqəm, ziddiyyət).
   Faktlar dəqiq olsun — əmin olmadığın rəqəmi yazma.
3. Render: `node engine/render.mjs posts/<id>/spec.json`
   (reel → reel.mp4 + cover.jpg; karusel → slide-N.png). Ən azı 3 kadra/slayda Read ilə bax:
   mətn kəsilməsin, üst-üstə düşməsin, Azərbaycan hərfləri düz olsun.
4. `music.wav`-ı commit etmə (.gitignore). Commit + push to `main`.
5. Metricool (brand id `7685976`, timezone `Asia/Baku`) ilə **hədəf gün saat 10:00**-a planla
   (hədəf gün = sabahdan başlayaraq 10:00 postu olmayan ilk gün, maks. 3 gün irəli):
   - Media URL: `https://raw.githubusercontent.com/baghirovkhalil-ai/Sosial-post/main/posts/<id>/<fayl>`
   - Reel: providers instagram + youtube; instagramData.type `REEL`, isAiGenerated true;
     youtubeData {title (≤90 simvol, sonda #shorts), type "short", privacy "public", madeForKids false,
     category "EDUCATION", isAiGeneratedContent true}; videoThumbnailUrl = cover.jpg (YouTube thumbnail
     xəta verə bilər — normaldır).
   - Karusel: yalnız instagram, type `POST`, media = bütün slaydlar sırası ilə.
   - Caption: 1-ci sətir qarmaq, 3–6 qısa sətir dəyər, 1 CTA (yadda saxla / paylaş / "X" yaz DM-ə),
     8–12 hashtag (az + en qarışıq, məs. #rəqəmsalmarketinq #bakı #smm #aimarketing).
   - Əvvəlcə getScheduledPosts ilə həmin günə artıq post qoyulubmu yoxla — dublikat yaratma.
6. `content/ideas.json`-da ideyanı `"status":"done","date":"..."` et, `content/log.md`-yə 1 sətir yaz, push.
7. Hər bazar günü əlavə olaraq son 7 günün Instagram statistikasına bax (getAnalyticsDataByMetrics),
   ən yaxşı/zəif postu `content/log.md`-yə yaz və növbəti həftənin ideyalarını ona görə prioritetləşdir.

## spec.json formatı
```json
{"id":"2026-10-28-slug","type":"reel|carousel","tag":"META ADS","musicSeed":7,
 "scenes":[ {"kind":"...","dur":3.5,"cap":"altyazı (yalnız reel)", ...} ]}
```
Mətn işarələri: `*söz*` firuzəyi, `_söz_` sarı, `~söz~` qırmızı.
Səhnə növləri:
- `hook` {small, big, sub, stat?:{label,value,suffix}} — big qısa olsun (1–3 söz)
- `step` {num:"01", title, sub, color?: cyan|yellow|red, visual?: target|bars|cross}
- `list` {title, items:[...]} (≤5 qısa bənd)
- `compare` {title, bad, good, badLabel?, goodLabel?}
- `stat` {small, value:number, suffix, label, visual?}
- `chat` {title, msgs:[{from:"user"|"ai", text}]} — AI prompt nümunələri üçün
- `cta` {small, big, sub, button} — həmişə sonuncu
`dur` saniyədir (reel üçün; karuseldə nəzərə alınmır). Mətni oxumağa vaxt ver: ~12 söz = 3.5 san.
