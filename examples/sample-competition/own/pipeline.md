# 自陣のパイプライン — サンプルコンペ（合成）

## 構成要素

| 要素 | 次元 | 使用 | 効果 | 根拠 |
|---|---|---|---|---|
| 2.5D のスライス積み | features | yes | 土台 | config |
| 関節中心の切り出し | preprocessing | yes | 全体より CV +0.003（exp041） | 自陣の記録 |
| 画像を読む教師ラベル | training | no | 画像だけの版を試して CV −0.001（exp120）、棄却 | 自陣の記録 |
| 施設ごとのラベル補正 | training | no | | 未着手 |
| 局所切り出しの別モデル | model | no | exp207 保留 | 自陣の記録 |
| 患者で分けた 5 fold CV | cv | yes | | config |
| 反転 TTA | inference | yes | CV +0.0005 | 自陣の記録 |
| 公開 Notebook との合成 | ensemble | yes | 単一より private +0.006（実測） | 提出一覧 |
| テストの疑似ラベル | training | no | | 未着手 |

## 9 次元

| # | 次元 | 自陣 | 出典 |
|---|---|---|---|
| 1 | features | 5 枚のスライスを 2.5D に積む | config |
| 2 | preprocessing | 中心 140 mm の切り出し | config |
| 3 | augmentation | 反転・小さな回転 | config |
| 4 | model | ConvNeXt-S | config |
| 5 | training | レポート由来のラベル、BCE | config |
| 6 | cv | 患者で分けた 5 fold | config |
| 7 | inference | 反転 TTA | config |
| 8 | postprocessing | なし | — |
| 9 | ensemble | 自陣 0.4 + 公開 Notebook 0.6 | 提出一覧 |
