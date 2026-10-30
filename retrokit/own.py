"""自陣の結果: 全提出の public / private 最良、LB からの順位とチーム数。"""

from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from .frontmatter import as_float
from .index import strip_to_header


def read_submissions(path: Path) -> list[dict[str, str]]:
    """`kaggle competitions submissions --csv` の出力（先頭に警告行が混ざることがある）。"""
    text = strip_to_header(path.read_text(encoding="utf-8"), "fileName")
    return [dict(r) for r in csv.DictReader(io.StringIO(text, newline=""))]


def read_lb(path: Path) -> list[dict[str, str]]:
    """LB の CSV か、`leaderboard -d` が落とした zip（中に CSV が 1 つ）。"""
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if n.lower().endswith(".csv")]
            if not names:
                raise SystemExit(f"[ERROR] zip に CSV が無い: {path}")
            data = z.read(names[0]).decode("utf-8")
        return [dict(r) for r in csv.DictReader(io.StringIO(data))]
    with path.open(newline="", encoding="utf-8") as f:
        return [dict(r) for r in csv.DictReader(f)]


def best(rows: list[dict[str, str]], col: str, higher_is_better: bool) -> dict[str, str] | None:
    """列 col が最良の行。"""
    scored = [(v, r) for r in rows if (v := as_float(r.get(col))) is not None]
    if not scored:
        return None
    return (max if higher_is_better else min)(scored, key=lambda x: x[0])[1]


def lb_rank(lb: list[dict[str, str]], team: str, higher_is_better: bool) -> tuple[int | None, int, str | None]:
    """(チームの順位, チーム数, 使った点数の列名)。同点は同順位にしない。"""
    if not lb:
        return None, 0, None
    score_col = next((c for c in ("Score", "score", "PrivateScore", "PublicScore") if c in lb[0]), None)
    if score_col is None:
        return None, len(lb), None
    ordered = sorted(lb, key=lambda r: (as_float(r.get(score_col)) or float("-inf")), reverse=higher_is_better)
    for i, r in enumerate(ordered, start=1):
        if (r.get("TeamName") or r.get("teamName") or "").strip() == team:
            return i, len(ordered), score_col
    return None, len(ordered), score_col


@dataclass
class OwnSummary:
    n_submissions: int = 0
    best_public: dict[str, str] | None = None
    best_private: dict[str, str] | None = None
    rank: int | None = None
    teams: int = 0
    lb_columns: list[str] = field(default_factory=list)
    score_col: str | None = None

    def text(self) -> str:
        """画面に出す要約。"""
        lines = [f"提出の件数: {self.n_submissions}"]
        for label, r, col in (("public 最良", self.best_public, "publicScore"), ("private 最良", self.best_private, "privateScore")):
            if r is None:
                lines.append(f"{label}: 値が無い（{col} 列が空。終了前か列名が違う）")
            else:
                lines.append(f"{label}: {r.get(col)} | {r.get('fileName', '')} | {r.get('date', '')} | "
                             f"public {r.get('publicScore', '')} / private {r.get('privateScore', '')} | {r.get('description', '')[:60]}")
        lines.append("選んだ 2 本: CLI では分からない。Web の My Submissions で確かめて own/final.md の private_final に書く（任意）")
        if self.lb_columns:
            lines.append(f"LB: {self.teams} チーム、列 {self.lb_columns}"
                         "（Private かどうかは取得時期と列名による。レポートでは「推定」と書く）")
            lines.append(f"順位: {self.rank if self.rank is not None else 'チームが見つからない（--team を渡す）'} / {self.teams}")
        return "\n".join(lines)


def summarize(subs: list[dict[str, str]], lb: list[dict[str, str]] | None, team: str | None, higher_is_better: bool) -> OwnSummary:
    s = OwnSummary(n_submissions=len(subs))
    s.best_public = best(subs, "publicScore", higher_is_better)
    s.best_private = best(subs, "privateScore", higher_is_better)
    if lb:
        s.lb_columns = list(lb[0].keys())
        rank, n, col = lb_rank(lb, team or "", higher_is_better)
        s.rank, s.teams, s.score_col = rank, n, col
    return s
