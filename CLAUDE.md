# CLAUDE.md — kaggle-retro-kit

終わった Kaggle コンペの振り返り: 自陣の結果を固定し、上位の解法記事を同じ形のカードにし、メダル圏ごとの差分を計算し、
解説動画にする。1 コンペ = 1 フォルダ `competitions/<slug>/`。

| 段 | 伝え方 | 動くもの |
|---|---|---|
| 1 自陣の確定 | 「`<slug>` の振り返りを始めて」 | skill `retro-start` → `python retro.py new` + `fetch` |
| 2 解法の収集 | 「解法を集めて」 | skill `retro-collect` → `python retro.py collect` |
| 3 カード | 「7 位と 21 位を読んで」「上位 20 位をカードに」 | skill `retro-card`（記事ごとに並行） |
| 4 差分の分析 | 「差分を出して」「どこで差がついた」 | `python retro.py diff` + skill `retro-report` |
| 5 動画 | 「動画にして」 | `python retro.py video` + skill `retro-video` |
| 6 教訓 | 「教訓」「還元」 | skill `retro-lessons` |

## 分析を正直に保つ約束

- 自陣の数値は **実測**、他人の数値は **本人の申告**。数値を書くたびにどちらかを書く
- 別々の解法の申告を足し合わせない。「本文に無い」を「使っていない」にしない
- カードは自分の言葉で書き、出典 URL を付ける。記事の本文をリポジトリに写さない（本文は `tmp/`、git 管理外）
- 持ち帰り候補は構造を変える案だけ（入力の渡し方・未使用データ・学習と評価のずれ）。ハイパラ・seed・checkpoint は載せない
- ファイルから分かることをユーザーに聞かない。CLI で分からないのは「選んだ 2 本」と「単一モデルの点」だけ。
  `own/final.md` に無ければ private 最良で進め、そう書く
- Kaggle へは読み取りだけ。提出・Notebook の push・データのダウンロードはしない
- 書き出した MP4 / GIF は git 管理外。GitHub Release などに置き、`report.md` からリンクする

## 回答の書式

結論（3 行）→ 表 → 「判断待ち」（ユーザーに決めてもらうこと）。事実に確度を付ける: ✅ 実測・確認済み / ⚠️ 申告・推定 / ❓ 不明。
