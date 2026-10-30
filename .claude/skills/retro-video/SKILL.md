---
name: retro-video
description: 'video/data.json から 5 場面の解説動画（MP4 / GIF / ポスター）を書き出し、コマを確かめる。必要なら video/lib/arch.js で手描きの深掘り場面を足す。Use when asked to "動画にして", "解説動画", "アニメーション", "render".'
---

# 段 5 — 解説動画

何のためか: 階段と行列が話の本体。点が圏ごとに登るのを見る方が、表より速く伝わる。

## 既定（設計の作業は要らない）

```bash
cd video && npm install && npx playwright-core install chromium && cd ..   # 初回のみ。Node 18+、ffmpeg が PATH に要る
python retro.py diff  <slug>                     # data.json を最新に
python retro.py video <slug> --sheet             # 一覧画像 video/out/<slug>-sheet.png: 重なり・はみ出しを見る
python retro.py video <slug> --gif               # MP4 + GIF + ポスター PNG → competitions/<slug>/video/out/
```

出す前に一覧画像（細かい所は `node video/tools/render.mjs frames <秒> ... --page video/pages/explainer.html --data <data.json>` の原寸コマ）を見る。
長い要素名は行列で切れる。気になればカードの要素名を短くする。

## 手描きの深掘り場面（任意）

`video/pages/custom-example.{html,js}` を `competitions/<slug>/video/` に写し、`window.Arch` の部品（`box` `arrow` `dot` `bar` `note` `pill` `wrap`）で描く。
`render(t)` は時刻 t だけで決まるようにし、数値には必ず「実測」か「申告」を添える。
`python retro.py video <slug> --page competitions/<slug>/video/<file>.html --name <名前>` で書き出す。

## 残す

- MP4 / GIF は git に入れない（管理外）。`gh release create <slug>-video-<YYYYMMDD> competitions/<slug>/video/out/*.mp4 *.gif`（確認が出る）か
  他の置き場に上げ、`report.md` と `video/README.md` からリンク。ポスター PNG は小さいので commit する
- 会話にファイルを送る道具があれば MP4 / GIF を送る（リポジトリを開かなくても見られるように）
