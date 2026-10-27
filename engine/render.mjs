// Usage: node engine/render.mjs posts/<id>/spec.json
// Reel spec  -> posts/<id>/reel.mp4 + cover.jpg
// Carousel   -> posts/<id>/slide-1.png ...
import { createRequire } from 'module';
import { readFileSync } from 'fs';
const { chromium } = createRequire(import.meta.url)('playwright');
import { spawn, execFileSync } from 'child_process';
import path from 'path';
import { fileURLToPath, pathToFileURL } from 'url';

const ENGINE = path.dirname(fileURLToPath(import.meta.url));
const specPath = path.resolve(process.argv[2]);
const outDir = path.dirname(specPath);
const spec = JSON.parse(readFileSync(specPath, 'utf8'));
const FPS = 30;

const browser = await chromium.launch();
async function open(mode) {
  const H = mode === 'reel' ? 1920 : 1350;
  const page = await browser.newPage({ viewport: { width: 1080, height: H } });
  await page.addInitScript(([s, m]) => { window.SPEC = s; window.MODE = m; }, [spec, mode]);
  await page.goto(pathToFileURL(path.join(ENGINE, 'template.html')).href);
  await page.evaluate(() => window.ready);
  return page;
}

if (spec.type === 'carousel') {
  const page = await open('slide');
  let t = 0;
  for (let i = 0; i < spec.scenes.length; i++) {
    const d = spec.scenes[i].dur || 4;
    await page.evaluate((x) => window.renderAt(x), t + d - 0.3);
    await page.screenshot({ path: path.join(outDir, `slide-${i + 1}.png`) });
    t += d;
  }
  console.log(`carousel: ${spec.scenes.length} slides`);
} else {
  const page = await open('reel');
  const total = await page.evaluate(() => window.TOTAL);
  const frames = Math.ceil(total * FPS);
  const wav = path.join(outDir, 'music.wav');
  execFileSync('python3', [path.join(ENGINE, 'music.py'), wav, String(total + 0.5), String(spec.musicSeed ?? Math.floor(Math.random() * 1000))], { stdio: 'inherit' });
  const out = path.join(outDir, 'reel.mp4');
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = 0; f < frames; f++) {
    await page.evaluate((x) => window.renderAt(x), f / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if (f % 150 === 0) console.log(`frame ${f}/${frames}`);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
  // cover = end of first (hook) scene
  const hookEnd = (spec.scenes[0].dur || 4) - 0.3;
  await page.evaluate((x) => window.renderAt(x), hookEnd);
  await page.screenshot({ path: path.join(outDir, 'cover.jpg'), type: 'jpeg', quality: 92 });
  console.log(`reel: ${total}s, ${frames} frames -> ${out}`);
}
await browser.close();
