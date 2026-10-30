---
rank: 1
team: aurora
medal: gold
private: 0.9611
single_model_private: 0.9582
url: https://www.kaggle.com/competitions/sample-competition/discussion/1001
topic_id: 1001
---
# 1 位 — aurora（合成）

数値はすべて **本人の申告**。

## 要約

- 何を入力し何を出すか: 3D の検査 → 12 所見の確率
- 点を取った中心: 画像を読む教師でラベルを作り直した
- 自陣と最も違う構造: 教師ラベル

## 構成要素

| 要素 | 次元 | 使用 | 効果 | 根拠 |
|---|---|---|---|---|
| 2.5D のスライス積み | features | yes | | 本文に明記 |
| 関節中心の切り出し | preprocessing | yes | | 本文に明記 |
| 画像を読む教師ラベル | training | yes | レポート由来より CV +0.006（単一モデル） | 本文に明記 |
| 施設ごとのラベル補正 | training | yes | private +0.002 | 本文に明記 |
| 局所切り出しの別モデル | model | yes | 局所の 2 所見で +0.003 | 本文に明記 |
| 患者で分けた 5 fold CV | cv | yes | | 本文に明記 |
| 反転 TTA | inference | yes | | 推定 |
| テストの疑似ラベル | training | no | | 本文に明記 |

## 9 次元

| # | 次元 | この解法 | 根拠 | 自陣との差分の型 |
|---|---|---|---|---|
| 1 | features | 2.5D の積み | 本文に明記 | ✅ 同じ |
| 4 | model | ConvNeXt / EfficientNet | 本文に明記 | ✅ 同じ |
| 5 | training | 構成要素を参照 | 本文に明記 | 🔄 違う |

## 持ち帰り候補

| 候補 | 次元 | 何を変えるか | 申告の効果 | 自陣での試し方 | 留保 |
|---|---|---|---|---|---|
| 構成要素を参照 | training | ラベルの作り方 | 構成要素を参照 | 1 fold で当たりを見る | 申告であり実測ではない |
