---
rank: {{RANK}}
team: {{TEAM}}
medal:
private:
public:
single_model_private:
url: {{URL}}
topic_id: {{TOPIC_ID}}
code:
license:
---
# {{RANK}} 位 — {{TEAM}}

数値は「自陣で測り直した」と書いたもの以外、すべて **本人の申告**。

## 要約

- 何を入力し何を出すか:
- 点を取った中心（1 行）:
- 自陣と最も違う構造（1 行）:

## 構成要素

1 行 = 1 つの部品。他のカードで使った要素名を再利用する（`grep -h "^| " solutions/*.md | sort -u`）。
「使用」= yes / no / unknown。「効果」= その要素について本人が書いた ablation の数値をそのまま（無ければ空）。

| 要素 | 次元 | 使用 | 効果 | 根拠 |
|---|---|---|---|---|
| | features / preprocessing / augmentation / model / training / cv / inference / postprocessing / ensemble | yes | | 本文に明記 / 推定 |

## 9 次元

| # | 次元 | この解法 | 根拠 | 自陣との差分の型 |
|---|---|---|---|---|
| 1 | features | | 本文に明記 / 推定 / 不明 | 🆕 無い / 🔄 違う / ⚡ 同じ系統で量が違う / ✅ 同じ |
| 2 | preprocessing | | | |
| 3 | augmentation | | | |
| 4 | model | | | |
| 5 | training | | | |
| 6 | cv | | | |
| 7 | inference | | | |
| 8 | postprocessing | | | |
| 9 | ensemble | | | |

## 点を動かしたもの（本人の申告。足し合わせない）

| 変更 | 次元 | 申告の差（CV / LB） | 条件（単一か合成か・fold・比較元） | 自陣と比較できるか |
|---|---|---|---|---|
| | | | | 同じ水準 / 違う / 不明 |

- 本人が「効かなかった」と書いたもの:
- 本文に無いこと（推測で埋めない）:

## 持ち帰り候補

構造を変える案だけ（入力の渡し方・未使用データ・学習と評価のずれ）。ハイパラ・seed・checkpoint・後処理の重みは載せない。

| 候補 | 次元 | 何を変えるか | 申告の効果 | 自陣での試し方 | 留保 |
|---|---|---|---|---|---|
| | | | | 既存成果物で測る / 1 fold で当たりを見る / 材料を揃えてから | |
