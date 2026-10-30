"""差分の分析: カード × 自陣 → 構成要素の行列・圏ごとの使用率・差分の順位・段の階段。

コードに焼き込んだ約束（疲れていると破りがちなもの）:
  * 「本文に無い」（unknown）を「使っていない」に倒さない
  * 別々の解法の申告を足さない（並べるだけ）
  * 「境目の候補」は、上の圏での使用率の差 **と** 同じ解法の中の 1 変更の申告の両方が要る。頻度だけなら「頻度だけ」
  * 自陣の数値だけが実測。他はすべて本人の申告
"""

from __future__ import annotations

import json
import statistics
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .cards import DIMENSIONS, Card, Own, load_cards, load_own
from .medal import BAND_LABEL, BAND_ORDER, Cutoffs, cutoffs


@dataclass
class ElementRow:
    """行列の 1 行（構成要素 1 つ）。"""

    name: str
    dimension: str
    cells: dict[str, str]                 # カードの label → yes / no / unknown
    own: str                              # 自陣 yes / no / unknown
    used_top: int                         # 上位 N 位以内のカードで yes の数
    known_top: int                        # 上位 N 位以内で yes か no が書いてある数
    band_usage: dict[str, dict[str, int]] # 圏 → {used, known, unknown}
    effects: list[dict[str, str]]         # [{label, effect}] 解法ごとの申告（足さない）
    own_effect: str = ""                  # 自陣の実測の注記
    verdict: str = ""                     # candidate / frequency only / not a boundary / n/a
    gap_score: float = 0.0


@dataclass
class Ladder:
    """段の階段（圏ごとの private）。"""

    bands: dict[str, list[dict[str, object]]]  # 圏 → [{label, rank, private, single, team}]
    medians: dict[str, float | None]
    own_final: float | None
    own_best: float | None
    own_single: float | None
    own_band: str


@dataclass
class Diff:
    slug: str
    name: str
    own_rank: int | None
    teams: int | None
    cutoffs: dict[str, int] | None
    own_band: str
    top_n: int
    cards: list[dict[str, object]]
    elements: list[ElementRow]
    gaps: list[ElementRow]
    shared: list[str]
    split: list[str]
    ladder: Ladder
    higher_is_better: bool
    notes: list[str] = field(default_factory=list)


def _band(c: Card, cut: Cutoffs | None) -> str:
    """カードの圏: medal の欄が優先、無ければ順位とチーム数から推定。"""
    if c.medal in BAND_ORDER:
        return c.medal
    if cut is not None and c.rank is not None:
        return cut.band(c.rank)
    return "unknown"


def _own_band(own: Own, cut: Cutoffs | None) -> str:
    if own.medal in BAND_ORDER:
        return own.medal
    if cut is not None and own.rank is not None:
        return cut.band(own.rank)
    return "unknown"


def _upper_bands(own_band: str) -> list[str]:
    """自陣より上の圏の一覧。自陣の圏が不明なら圏外以外の全部。"""
    if own_band not in BAND_ORDER:
        return list(BAND_ORDER[:-1])
    return list(BAND_ORDER[: BAND_ORDER.index(own_band)])


def _rate(u: dict[str, int]) -> float | None:
    return (u["used"] / u["known"]) if u["known"] else None


def build(comp_dir: Path, top_n: int = 20) -> Diff:
    """競合フォルダ → Diff（計算だけ。ファイルは書かない）。"""
    own = load_own(comp_dir)
    cards = load_cards(comp_dir / "solutions")
    cut = cutoffs(own.teams) if own.teams else None
    own_band = _own_band(own, cut)
    upper = _upper_bands(own_band)
    notes: list[str] = []
    if cut is None:
        notes.append("チーム数が不明なので、圏は各カードの medal の欄だけから決めている")
    bands = {c.label: _band(c, cut) for c in cards}
    top_cards = [c for c in cards if c.rank is not None and c.rank <= top_n]

    # 要素の全体: カードと自陣の和集合。最初に出た綴りを採り、次元 → 名前の順に並べる
    order: dict[str, tuple[str, str]] = {}
    for src in [*cards, own]:
        for e in src.elements:
            key = e.name.strip().lower()
            order.setdefault(key, (e.name.strip(), e.dimension))
    dim_index = {k: i for i, (k, _) in enumerate(DIMENSIONS)}
    keys = sorted(order, key=lambda k: (dim_index.get(order[k][1], 99), order[k][0].lower()))

    rows: list[ElementRow] = []
    for key in keys:
        name, dim = order[key]
        cells: dict[str, str] = {}
        effects: list[dict[str, str]] = []
        band_usage = {b: {"used": 0, "known": 0, "unknown": 0} for b in [*BAND_ORDER, "unknown"]}
        for c in cards:
            e = c.element(name)
            used = e.used if e else "unknown"                          # カードに無い要素は不明
            cells[c.label] = used
            b = bands[c.label]
            if used == "unknown":
                band_usage[b]["unknown"] += 1
            else:
                band_usage[b]["known"] += 1
                band_usage[b]["used"] += used == "yes"
            if e and e.effect:
                effects.append({"label": c.label, "effect": e.effect})
        oe = own.element(name)
        own_used = oe.used if oe else "unknown"
        used_top = sum(1 for c in top_cards if cells[c.label] == "yes")
        known_top = sum(1 for c in top_cards if cells[c.label] != "unknown")
        rows.append(ElementRow(name=name, dimension=dim, cells=cells, own=own_used, used_top=used_top, known_top=known_top,
                               band_usage=band_usage, effects=effects, own_effect=(oe.effect if oe else "")))

    # 判定: 自陣より上の圏の使用率と、自陣の圏以下の使用率（無ければ自陣自身）を比べる
    for r in rows:
        up = {"used": 0, "known": 0}
        for b in upper:
            up["used"] += r.band_usage[b]["used"]
            up["known"] += r.band_usage[b]["known"]
        low_bands = [b for b in [*BAND_ORDER, "unknown"] if b not in upper]
        low = {"used": sum(r.band_usage[b]["used"] for b in low_bands), "known": sum(r.band_usage[b]["known"] for b in low_bands)}
        ru, rl = _rate(up), _rate(low)
        if ru is None or up["known"] < 2 or (rl is None and r.own == "unknown"):
            r.verdict = "n/a"                                          # 上の圏の記述が 2 件未満なら判定しない
        else:
            own_rate = {"yes": 1.0, "no": 0.0}.get(r.own, rl if rl is not None else 0.0)
            base = rl if rl is not None else own_rate
            if ru - base >= 0.25:                                      # 上の圏で 25 ポイント以上多く使われている
                r.verdict = "candidate" if r.effects else "frequency only"
            else:
                r.verdict = "not a boundary"
        # 差分の順位の点: 上の圏の使用率 + 申告があれば加点 + 上位での使用数（自陣が yes の行では使わない）
        r.gap_score = round((ru or 0.0) * 10 + (2 if r.effects else 0) + (r.used_top * 0.1), 2)

    gaps = sorted([r for r in rows if r.own != "yes" and any(v == "yes" for v in r.cells.values())],
                  key=lambda r: (-r.gap_score, r.name.lower()))
    shared = [r.name for r in rows
              if top_cards and r.known_top >= 2 and r.used_top == r.known_top and r.used_top >= max(2, len(top_cards) // 2)]
    split = [r.name for r in rows if r.known_top >= 3 and 0 < r.used_top < r.known_top and abs(r.used_top / r.known_top - 0.5) <= 0.25]

    # 段の階段
    lb: dict[str, list[dict[str, object]]] = {b: [] for b in [*BAND_ORDER, "unknown"]}
    for c in cards:
        if c.private is not None:
            lb[bands[c.label]].append({"label": c.label, "rank": c.rank, "private": c.private,
                                       "single": c.single_model_private, "team": c.team})
    medians = {b: (statistics.median([float(x["private"]) for x in v]) if v else None) for b, v in lb.items()}  # type: ignore[arg-type]
    ladder = Ladder(bands=lb, medians=medians, own_final=own.private_final, own_best=own.private_best,
                    own_single=own.single_model_private, own_band=own_band)

    return Diff(
        slug=comp_dir.name, name=own.name, own_rank=own.rank, teams=own.teams,
        cutoffs=({"gold": cut.gold, "silver": cut.silver, "bronze": cut.bronze} if cut else None),
        own_band=own_band, top_n=top_n,
        cards=[{"label": c.label, "rank": c.rank, "team": c.team, "band": bands[c.label], "private": c.private,
                "single": c.single_model_private, "url": c.url, "file": c.path.name} for c in cards],
        elements=rows, gaps=gaps, shared=shared, split=split, ladder=ladder, higher_is_better=own.higher_is_better, notes=notes,
    )


# ---------------------------------------------------------------- 出力

_MARK = {"yes": "✅", "no": "—", "unknown": "❓"}
_VERDICT = {"candidate": "境目の候補", "frequency only": "頻度だけ", "not a boundary": "境目でない", "n/a": "判定不能（記述が少ない）"}


def _fmt(x: float | None) -> str:
    return "" if x is None else f"{x:.4f}".rstrip("0").rstrip(".")


def _bl(b: str) -> str:
    return BAND_LABEL.get(b, b)


def to_markdown(d: Diff) -> str:
    """Diff → diff.md の本文。"""
    L: list[str] = []
    L.append(f"# {d.name} — 差分の分析（`retro diff` が生成）\n")
    L.append("約束: 自陣の数値は **実測**、他の数値はすべて **本人の申告**。別々の解法の申告は並べるだけで足さない。❓ = 本文に無い。\n")
    for n in d.notes:
        L.append(f"> 注: {n}")
    L.append("\n## 自陣の位置\n")
    L.append("| 項目 | 値 | 出典 |\n|---|---|---|")
    L.append(f"| 自陣の順位 / チーム数 | {d.own_rank if d.own_rank is not None else '?'} / {d.teams if d.teams else '?'} | own/final.md |")
    if d.cutoffs:
        cut = f"金 ≤ {d.cutoffs['gold']} 位、銀 ≤ {d.cutoffs['silver']} 位、銅 ≤ {d.cutoffs['bronze']} 位"
        L.append(f"| メダル圏の境目（チーム数からの推定 ⚠️） | {cut} | retrokit.medal |")
    L.append(f"| 自陣の圏 | {_bl(d.own_band)} | |")
    by_band = {b: [c for c in d.cards if c['band'] == b] for b in [*BAND_ORDER, 'unknown']}
    L.append("| 分析済みのカード | " + "、".join(f"{_bl(b)} {len(v)} 件" for b, v in by_band.items() if v) + " | solutions/ |")

    L.append("\n## 段の階段（圏ごとの private）\n")
    L.append("| 圏 | 解法（順位: private、単一モデル） | 中央値 | 自陣 |\n|---|---|---|---|")
    for b in [*BAND_ORDER, "unknown"]:
        items = d.ladder.bands[b]
        if not items and b != d.own_band:
            continue
        cells = "、".join(f"{x['label']}: {_fmt(x['private'])}"  # type: ignore[arg-type]
                          + (f"（単一 {_fmt(x['single'])}）" if x['single'] is not None else "") for x in items)  # type: ignore[arg-type]
        ours = ""
        if b == d.own_band:
            ours = f"最終 {_fmt(d.ladder.own_final)}" + (f"、最良 {_fmt(d.ladder.own_best)}" if d.ladder.own_best is not None else "") + \
                   (f"、単一 {_fmt(d.ladder.own_single)}" if d.ladder.own_single is not None else "")
        L.append(f"| {_bl(b)} | {cells} | {_fmt(d.ladder.medians[b])} | {ours} |")

    L.append(f"\n## 構成要素の行列（列は順位順、最後が自陣。上位 N = {d.top_n}）\n")
    labels = [c["label"] for c in d.cards]
    L.append("| 要素 | 次元 | " + " | ".join(labels) + " | 自陣 | 上位 N 件中の使用数 |")
    L.append("|---|---|" + "---|" * len(labels) + "---|---|")
    for r in d.elements:
        L.append(f"| {r.name} | {r.dimension} | " + " | ".join(_MARK[r.cells[lab]] for lab in labels) +
                 f" | {_MARK[r.own]} | {r.used_top} / {r.known_top} |")
    if d.shared:
        L.append("\n- 分析済みの上位解法に共通: " + "、".join(d.shared))
    if d.split:
        L.append("- 流派が割れた要素: " + "、".join(d.split))

    L.append("\n## 圏ごとの使用率\n")
    L.append("セル = 使った件数 / 書いてある件数（❓ は本文に無い件数）。"
             "*境目の候補* = 自陣より上の圏での使用率が高く **かつ** 同じ解法の中の 1 変更の申告が 1 件以上ある。"
             "*頻度だけ* = 申告が無い。頻度の差は因果ではない。\n")
    bands_shown = [b for b in [*BAND_ORDER, "unknown"] if any(c["band"] == b for c in d.cards)]
    L.append("| 要素 | " + " | ".join(_bl(b) for b in bands_shown) + " | 自陣 | 解法内の申告 | 判定 |")
    L.append("|---|" + "---|" * len(bands_shown) + "---|---|---|")
    for r in d.elements:
        cells = []
        for b in bands_shown:
            u = r.band_usage[b]
            cells.append(f"{u['used']} / {u['known']}" + (f"（❓{u['unknown']}）" if u["unknown"] else ""))
        claims = "；".join(f"{e['label']}: {e['effect']}" for e in r.effects) or "—"
        L.append(f"| {r.name} | " + " | ".join(cells) + f" | {_MARK[r.own]} | {claims} | {_VERDICT[r.verdict]} |")

    L.append("\n## 差分の順位（自陣が使っていない要素を、自陣より上の圏での使用率の順に）\n")
    L.append("順番は提案。採否はユーザーが決める。\n")
    L.append("| # | 要素 | 次元 | 持っていた解法 | 解法内の申告（本人の数値） | 自陣の注記 | 判定 |\n|---|---|---|---|---|---|---|")
    for i, r in enumerate(d.gaps, start=1):
        used_by = "、".join(lab for lab, v in r.cells.items() if v == "yes")
        claims = "；".join(f"{e['label']}: {e['effect']}" for e in r.effects) or "—"
        own_note = r.own_effect or ("—" if r.own == "no" else "❓ 記録なし")
        L.append(f"| {i} | {r.name} | {r.dimension} | {used_by} | {claims} | {own_note} | {_VERDICT[r.verdict]} |")
    L.append("\n## 出典\n")
    for c in d.cards:
        L.append(f"- {c['label']} {c['team']} — `solutions/{c['file']}`" + (f" — {c['url']}" if c["url"] else ""))
    L.append("- 自陣 — `own/final.md`、`own/pipeline.md`")
    return "\n".join(L) + "\n"


def to_json(d: Diff) -> dict[str, object]:
    """Diff → 動画が読む data.json の辞書。"""
    out = asdict(d)
    out["elements"] = [asdict(r) for r in d.elements]
    out["gaps"] = [asdict(r) for r in d.gaps]
    return out


def write(comp_dir: Path, top_n: int = 20) -> tuple[Path, Path]:
    """diff.md と video/data.json を書く。"""
    d = build(comp_dir, top_n)
    md = comp_dir / "diff.md"
    md.write_text(to_markdown(d), encoding="utf-8")
    data = comp_dir / "video" / "data.json"
    data.parent.mkdir(parents=True, exist_ok=True)
    data.write_text(json.dumps(to_json(d), ensure_ascii=False, indent=2), encoding="utf-8")
    return md, data
