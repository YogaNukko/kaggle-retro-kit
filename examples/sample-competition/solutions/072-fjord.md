---
rank: 72
team: fjord
medal: bronze
private: 0.9481
single_model_private: 0.9455
url: https://www.kaggle.com/competitions/sample-competition/discussion/1072
topic_id: 1072
---
# 72 位 — fjord（合成）

数値はすべて **本人の申告**。

## 要約

- 何を入力し何を出すか: 3D の検査 → 12 所見の確率
- 点を取った中心: 素直な土台と合成
- 自陣と最も違う構造: 構造の差はない

## 構成要素

| 要素 | 次元 | 使用 | 効果 | 根拠 |
|---|---|---|---|---|
| 2.5D のスライス積み | features | yes | | 本文に明記 |
| 関節中心の切り出し | preprocessing | yes | | 本文に明記 |
| 画像を読む教師ラベル | training | no | | 本文に明記 |
| 施設ごとのラベル補正 | training | no | | 本文に明記 |
| 反転 TTA | inference | yes | | 本文に明記 |
| 公開 Notebook との合成 | ensemble | yes | | 本文に明記 |

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
