---
name: retro-card
description: '解法記事 1 件を solutions/<順位>-<チーム>.md のカードにする: front matter の点数、retro diff が読む「構成要素」の表、9 次元、本人申告の効果、構造を変える持ち帰り候補。索引を analyzed=yes にする。複数件は並行できる。Use when asked to "N 位を読んで", "カード", "この解法を分析", or given a discussion URL.'
---

# 段 3 — 解法 1 件 = カード 1 枚

何のためか: 記事は文章で、差分の分析には全解法と自陣が同じ形で要る。カードがその形。

## 手順（記事ごと。複数件はサブエージェントに 1 記事ずつ分けて並行）

1. 本文: `tmp/<slug>/writeups/<topic_id>.txt`（無ければ `kaggle competitions topics show <topic_id>`）。コメント欄も読む
   （ablation の数値はコメントにあることが多い）。コードへのリンクがあれば Notebook は `kaggle kernels pull`、GitHub は
   `tmp/<slug>/repos/` へ clone（確認が出る）。流用の前にライセンスを見る
2. `templates/solution_card.md` を `solutions/<順位 3 桁>-<チーム名の英小文字>.md` に写して埋める:
   - front matter: `rank` `team` `medal`（題名か `diff.md` の圏の表から）`private` `public`
     `single_model_private`（本人が単一モデルの private を書いているときだけ）`url` `topic_id` `code` `license`
   - 「構成要素」の表: **他のカードと `own/pipeline.md` で既に使った要素名を再利用する**
     （`grep -h "^| " solutions/*.md own/pipeline.md | cut -d'|' -f2 | sort -u`）。同じものは同じ綴りで。
     「使用」= yes / no / unknown。「効果」= その要素について本人が書いた数値をそのまま。「根拠」= 本文に明記 / 推定。
     本人が「使わなかった」と明記したものは `no` で書く（それも情報）
   - 9 次元、点を動かしたもの（足さない）、構造を変える持ち帰り候補だけ
3. 索引: `writeups_index.csv` の行に `card` `analyzed = yes` `team` `rank`
4. `python retro.py lint <slug>`、commit

数値: 本人のものはすべて ⚠️ 申告。自陣で測り直した値だけ ✅。
本文に無いことを推測で埋めない（`unknown`）。採否を決めない（候補と試し方まで）。
