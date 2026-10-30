#!/usr/bin/env node
// ============================================================
// render.mjs — 時刻 t だけで絵が決まるページ（window.ARCH の約束。lib/arch.js）を MP4 / GIF / ポスター PNG にする。
//
//   node tools/render.mjs info   --page <page.html>                    長さ・fps・字幕の時刻
//   node tools/render.mjs sheet  [N] --page <page.html>                 N コマの一覧画像（既定 24）
//   node tools/render.mjs frames <秒> [<秒> ...] --page <page.html>     指定した秒の原寸コマ
//   node tools/render.mjs video  --page <page.html> --name <名前> [--fps 24] [--gif] [--width 1600 --height 900]
//
// データ: ページは window.RETRO_DATA を読む。この道具が --data か $RETRO_DATA の JSON を注入する。
// 出力先: --out か $RETRO_OUT（既定 ./out）。Chromium: $RETRO_CHROME（任意）か Playwright 同梱のもの。
// 必要: playwright-core（video/ で npm install）か全体の playwright、PATH 上の ffmpeg。
// ============================================================
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const require = createRequire(import.meta.url);

function loadPlaywright() {
  const candidates = ['playwright-core', 'playwright', path.join(process.cwd(), 'node_modules/playwright-core'), path.join(process.cwd(), 'node_modules/playwright')];
  for (const c of candidates) {
    try { return require(c); } catch { /* 次の候補へ */ }
  }
  throw new Error('playwright-core が見つからない。video/ で `npm install`（か NODE_PATH に全体のインストール先を設定）');
}

function parseArgs(argv) {
  const opts = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith('--')) opts[key] = true; else { opts[key] = next; i++; }
    } else opts._.push(a);
  }
  return opts;
}

const opts = parseArgs(process.argv.slice(2));
const cmd = opts._[0];
if (!cmd || !opts.page) {
  console.error('使い方: node tools/render.mjs <info|sheet|frames|video> --page <page.html> [--name 名前] [--fps N] [--gif] [--data data.json] [--out 出力先]');
  process.exit(2);
}
const pageFile = path.resolve(opts.page);
const outDir = path.resolve(opts.out || process.env.RETRO_OUT || 'out');
const dataFile = opts.data || process.env.RETRO_DATA;
const width = +(opts.width || 1600), height = +(opts.height || 900);
fs.mkdirSync(outDir, { recursive: true });

async function openPage(browserFactory) {
  const browser = await browserFactory();
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
  if (dataFile) {
    const json = fs.readFileSync(dataFile, 'utf8');
    await page.addInitScript(`window.RETRO_DATA = ${json};`);
  }
  page.on('pageerror', (e) => console.error('[page error]', e.message));
  await page.goto('file://' + pageFile + '?render');
  await page.waitForFunction(() => window.ARCH && window.ARCH.ready, null, { timeout: 60000 });
  const arch = await page.evaluate(() => ({ duration: window.ARCH.duration, fps: window.ARCH.fps, posterTime: window.ARCH.posterTime, phases: window.ARCH.phases }));
  return { browser, page, arch };
}

function ffmpeg(args) {
  const r = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', ...args], { stdio: 'inherit' });
  if (r.status !== 0) throw new Error('ffmpeg が失敗（ffmpeg は PATH にあるか）');
}

// Chromium の実行ファイルを決める: $RETRO_CHROME → Playwright 同梱 → ~/.cache/ms-playwright にある他の版（新しい順）
function findChrome(chromium) {
  if (process.env.RETRO_CHROME) return process.env.RETRO_CHROME;
  try { const p = chromium.executablePath(); if (p && fs.existsSync(p)) return p; } catch { /* 同梱の版が無い */ }
  const cache = path.join(process.env.HOME || '', '.cache', 'ms-playwright');
  if (!fs.existsSync(cache)) return undefined;
  const cands = [];
  for (const d of fs.readdirSync(cache)) {
    for (const rel of ['chrome-linux/chrome', 'chrome-headless-shell-linux64/chrome-headless-shell', 'chrome-mac/Chromium.app/Contents/MacOS/Chromium']) {
      const f = path.join(cache, d, rel);
      if (fs.existsSync(f)) cands.push({ f, n: +(d.match(/(\d+)$/) || [0, 0])[1] });
    }
  }
  cands.sort((a, b) => b.n - a.n);
  if (cands.length) { console.error(`[render] 同梱の Chromium が無いので ${cands[0].f} を使う`); return cands[0].f; }
  return undefined;
}

(async () => {
  const { chromium } = loadPlaywright();
  const exe = findChrome(chromium);
  const factory = async () => {
    try {
      return await chromium.launch({ executablePath: exe, args: ['--no-sandbox', '--font-render-hinting=none'] });
    } catch (e) {
      if (/executable doesn't exist|ENOENT/i.test(e.message)) {
        throw new Error('Chromium が無い。video/ で `npx playwright-core install chromium` を実行するか、RETRO_CHROME に Chrome のパスを入れる\n' + e.message.split('\n')[0]);
      }
      throw e;
    }
  };
  const { browser, page, arch } = await openPage(factory);
  const fps = +(opts.fps || arch.fps || 24);
  const name = opts.name || path.basename(pageFile, '.html');
  try {
    if (cmd === 'info') {
      console.log(`長さ ${arch.duration.toFixed(2)} 秒、fps ${fps}、コマ数 ${Math.ceil(arch.duration * fps)}、ポスター ${arch.posterTime.toFixed(2)} 秒`);
      for (const ph of arch.phases) console.log(`  ${ph.t0.toFixed(1).padStart(6)} - ${ph.t1.toFixed(1).padStart(6)}  ${ph.caption}`);
    } else if (cmd === 'sheet') {
      const n = +(opts._[1] || 24);
      const tiles = [];
      for (let i = 0; i < n; i++) {
        const t = (arch.duration * (i + 0.5)) / n;
        await page.evaluate((s) => window.ARCH.render(s, { stamp: true }), t);
        tiles.push(await page.screenshot({ type: 'png' }));
      }
      // ffmpeg の tile で並べる（列 × 行）
      const tmp = path.join(outDir, '_sheet');
      fs.mkdirSync(tmp, { recursive: true });
      tiles.forEach((b, i) => fs.writeFileSync(path.join(tmp, `s${String(i).padStart(3, '0')}.png`), b));
      const cols = Math.ceil(Math.sqrt(n)), rows = Math.ceil(n / cols);
      const out = path.join(outDir, `${name}-sheet.png`);
      ffmpeg(['-framerate', '1', '-i', path.join(tmp, 's%03d.png'), '-vf', `scale=400:-1,tile=${cols}x${rows}:padding=4:margin=4`, '-frames:v', '1', out]);
      fs.rmSync(tmp, { recursive: true, force: true });
      console.log(out);
    } else if (cmd === 'frames') {
      const times = opts._.slice(1).map(Number);
      const dir = path.join(outDir, 'frames');
      fs.mkdirSync(dir, { recursive: true });
      for (const t of times) {
        await page.evaluate((s) => window.ARCH.render(s, { stamp: true }), t);
        const f = path.join(dir, `frame-${t}.png`);
        await page.screenshot({ path: f });
        console.log(f);
      }
    } else if (cmd === 'video') {
      const total = Math.ceil(arch.duration * fps);
      const dir = path.join(outDir, 'frames', name);
      fs.rmSync(dir, { recursive: true, force: true });
      fs.mkdirSync(dir, { recursive: true });
      const t0 = Date.now();
      for (let i = 0; i < total; i++) {
        await page.evaluate((s) => window.ARCH.render(s), i / fps);
        await page.screenshot({ path: path.join(dir, `f${String(i).padStart(5, '0')}.png`), type: 'png' });
        if (i % 100 === 0) process.stdout.write(`\r  コマ ${i}/${total}（${((Date.now() - t0) / 1000).toFixed(0)} 秒）`);
      }
      process.stdout.write(`\r  コマ ${total} 枚を ${((Date.now() - t0) / 1000).toFixed(0)} 秒で撮影\n`);
      const mp4 = path.join(outDir, `${name}.mp4`);
      ffmpeg(['-framerate', String(fps), '-i', path.join(dir, 'f%05d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-movflags', '+faststart', mp4]);
      console.log(mp4);
      if (opts.gif) {
        const gif = path.join(outDir, `${name}.gif`);
        const gw = +(opts['gif-width'] || 800), gfps = +(opts['gif-fps'] || 12);
        ffmpeg(['-i', mp4, '-vf', `fps=${gfps},scale=${gw}:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5`, gif]);
        console.log(gif);
      }
      await page.evaluate((s) => window.ARCH.render(s), arch.posterTime);
      const poster = path.join(outDir, `${name}-poster.png`);
      await page.screenshot({ path: poster });
      console.log(poster);
      if (!opts['keep-frames']) fs.rmSync(dir, { recursive: true, force: true });
    } else {
      throw new Error(`不明なコマンド ${cmd}`);
    }
  } finally {
    await browser.close();
  }
})().catch((e) => { console.error('[render] ' + e.message); process.exit(1); });
