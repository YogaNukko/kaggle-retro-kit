# 自陣のパイプライン — {{NAME}}

解法カードと同じ形で書く。`retro diff` はこの表を行列の最後の列（自陣）に使う。
ここの「効果」は自陣の **実測**（CV / LB の差と比較の条件）。分析全体で「申告」でない唯一の列。

## 構成要素

要素名はカード（`solutions/` と `diff.md`）と揃える。「使用」は yes / no。
**試して落としたものは `no` にして、実測の差を「効果」に書く**。それが差分の表を正直にする。

| 要素 | 次元 | 使用 | 効果 | 根拠 |
|---|---|---|---|---|
| （例）公開 Notebook の疑似ラベル | training | no | 試して CV −0.002（exp042） | 自陣の記録 |

## 9 次元

次元の名前: features / preprocessing / augmentation / model / training / cv / inference / postprocessing / ensemble

| # | 次元 | 自陣 | 出典（config のキー・ファイル） |
|---|---|---|---|
| 1 | features | | |
| 2 | preprocessing | | |
| 3 | augmentation | | |
| 4 | model | | |
| 5 | training | | |
| 6 | cv | | |
| 7 | inference | | |
| 8 | postprocessing | | |
| 9 | ensemble | | |

## 比較の水準

- CV の作り（fold 数・分割の鍵）:
- 自陣の LB の数値は何か（1 fold / 全 fold / 合成）:
- 指標の揺れ（同じ構成で seed を変えたときの差）:
