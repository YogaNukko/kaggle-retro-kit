# 動画 — {{NAME}}

- `data.json` は `retro diff {{SLUG}}` が書き、`retro video {{SLUG}}` が `video/pages/explainer.html` で描く
- 書き出した MP4 / GIF は `out/` に置かれ git 管理外。GitHub Release（`gh release create {{SLUG}}-video-<日付> out/*.mp4`）に添付するか
  好きな場所に置く。ポスター PNG（`out/<名前>-poster.png`、小さい）だけ git に入れる
- 自動生成の場面の先を描きたいときは `video/pages/custom-example.html` をこのフォルダに写し、`retro video --page` で指す

| 日付 | ファイル | 長さ | Release / リンク | 伝えたい 1 文 |
|---|---|---|---|---|
| | | | | |
