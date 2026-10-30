# video/ — 再現できる解説動画の描画器

```
lib/arch.js              SVG の部品と場面の進行役（window.Arch）。ページは window.ARCH を出す
tools/render.mjs         info | sheet N | frames 秒... | video（Playwright で撮影 → ffmpeg）
pages/explainer.*        data.json（`retro diff` の出力）駆動の 5 場面
pages/custom-example.*   手描きの場面の最小例
```

初回: ここで `npm install`（`playwright-core` が入る。ブラウザ本体は別）。続けて `npx playwright-core install chromium` で Chromium を取る
（`~/.cache/ms-playwright/` に入る。既に他の版があればそれを自動で探して使う）。手元の Chrome を使うなら `RETRO_CHROME` にパスを入れる。ffmpeg は PATH に要る。

`retro.py` を通さずに使う:

```bash
node tools/render.mjs info  --page pages/explainer.html --data ../competitions/<slug>/video/data.json
node tools/render.mjs sheet 24 --page pages/explainer.html --data ... --out ../competitions/<slug>/video/out
node tools/render.mjs video --page pages/explainer.html --data ... --out ... --name <slug> --fps 24 --gif
```

自作ページの約束: `window.ARCH = { ready, duration, fps, posterTime, phases, render(t) }`。`render(t)` は t だけで決まる。
`Arch.defineShow({ scenes: [{ id, title, dur, draw(p, u), caps: [[開始秒, 字幕]] }] })` がそれを組み立てる。

フォント: ページは Google Fonts の Noto Sans JP を読みに行き、読めなければ 3 秒で system フォントに落ちる。
