"""チーム数から Kaggle のメダル圏の境目を推定する。

Kaggle の規則（Progression ページ、コンペのメダル）:
    チーム数 0〜99      金 上位 10%       銀 上位 20%   銅 上位 40%
    チーム数 100〜249   金 上位 10 位     銀 上位 20%   銅 上位 40%
    チーム数 250〜999   金 上位 10+0.2%   銀 上位 50 位 銅 上位 100 位
    チーム数 1000〜     金 上位 10+0.2%   銀 上位 5%    銅 上位 10%

結果は **推定** であり、Kaggle 側の丸めと同点の扱いで 1〜2 位ずれることがある。
ここから出た数字はレポートで必ず「推定」と書く。
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Cutoffs:
    """各圏の下端の順位（その順位までがその圏）。"""

    teams: int    # チーム数
    gold: int     # 金の下端の順位
    silver: int   # 銀の下端の順位
    bronze: int   # 銅の下端の順位

    def band(self, rank: int | None) -> str:
        """順位から圏の名前を返す（gold / silver / bronze / none。順位が不明なら unknown）。"""
        if rank is None:
            return "unknown"
        if rank <= self.gold:
            return "gold"
        if rank <= self.silver:
            return "silver"
        if rank <= self.bronze:
            return "bronze"
        return "none"


def cutoffs(teams: int) -> Cutoffs:
    """チーム数 → 各圏の下端の順位。"""
    if teams <= 0:
        raise ValueError("teams は正の数")
    if teams < 100:                                                   # 100 チーム未満は全部が割合
        gold = max(1, math.floor(teams * 0.10))
        silver = max(gold, math.floor(teams * 0.20))
        bronze = max(silver, math.floor(teams * 0.40))
    elif teams < 250:                                                 # 金だけ固定 10 位
        gold = 10
        silver = max(gold, math.floor(teams * 0.20))
        bronze = max(silver, math.floor(teams * 0.40))
    elif teams < 1000:                                                # 金 10 + 0.2%、銀 50 位、銅 100 位
        gold = 10 + math.floor(teams * 0.002)
        silver = max(gold, 50)
        bronze = max(silver, 100)
    else:                                                             # 1000 以上は金以外が割合
        gold = 10 + math.floor(teams * 0.002)
        silver = max(gold, math.floor(teams * 0.05))
        bronze = max(silver, math.floor(teams * 0.10))
    return Cutoffs(teams=teams, gold=gold, silver=silver, bronze=bronze)


BAND_ORDER = ("gold", "silver", "bronze", "none")                     # 上から下へ
BAND_LABEL = {"gold": "金", "silver": "銀", "bronze": "銅", "none": "圏外", "unknown": "圏 不明"}
