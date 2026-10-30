---
name: retro-start
description: '終わった Kaggle コンペの振り返りを始める。competitions/<slug>/ を雛形から作り、LB と自陣の提出一覧を取って own/final.md と own/pipeline.md を埋める。Use when asked to "振り返りを始めて", "結果を確定", "retro start", or given a finished competition slug.'
---

# 段 1 — 自陣の確定

何のためか: 上位の解法を読むと自分の記憶がずれる。読む前に自陣の数字を固定する。

```bash
python retro.py new <slug> --name "<コンペ名>" --deadline "<UTC ISO>"   # 締切は `kaggle competitions list -s <slug>` の deadline 列
python retro.py fetch <slug> --team "<LB に出るチーム名>" [--lower-is-better]
```

`fetch` が順位・チーム数・public / private の最良・推定メダル圏を `own/final.md` の front matter に書く。

その後、ユーザーに聞かずに:

1. `private_final`: 既定（= private 最良）のままにする。ユーザーが選んだ提出を既に言っていればそれにする。
   「何を提出したか」にどちらにしたかを 1 行書く
2. `single_model_private`: 提出一覧の説明やファイル名から単一モデルの提出が明らかなら埋める。分からなければ空
3. `own/pipeline.md`: コンペのリポジトリが読めるなら（パスを教えてもらっているか、プロンプトにある）、config と README から 9 次元と
   「構成要素」の表を埋める。**試して落としたもの**は `使用 = no` にして実測の差を「効果」に書く。読めなければ提出の説明から分かる分だけ埋める
4. `python retro.py lint <slug>`、`status.md` の段 1 を更新、commit

報告: 順位 / チーム数 / 圏 / private（実測 ✅）と、CLI で分からなかったこと（選んだ 2 本）を 1 行。次は `retro-collect`。
