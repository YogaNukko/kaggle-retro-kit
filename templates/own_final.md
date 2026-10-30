---
name: {{NAME}}
rank:
teams:
medal:
private_final:
private_best:
single_model_private:
public_final:
higher_is_better: yes
---
# 自陣の確定 — {{NAME}}

`retro fetch` が LB と提出一覧から上の front matter を埋める。
人が書くのは `private_final`（実際に選んだ提出の private。CLI は選んだ 2 本を返さない）と、
階段に出したいなら `single_model_private`（自前の単一モデルの最良）だけ。このファイルの数値はすべて **実測**（自陣の値）。

## 何を提出したか

- 最終構成（実験番号・fold・合成の中身）:
- 選んだ根拠（CV と public LB のどちらを信じたか）:
- 終盤に試して間に合わなかったもの:

## 取得の記録

- 取得日時: `tmp/{{SLUG}}/fetched_at.txt`
- LB の列名（Private かどうかの判断材料）:
