"""解法カード（competitions/<slug>/solutions/<順位>-<チーム>.md）と自陣（own/pipeline.md）の読み込み。

両方とも機械で読む部分は同じ形:

    ---                       （front matter）
    rank: 7
    team: some team
    private: 0.9574
    ---
    ## 構成要素               （1 行 = 1 つの部品。要素名はカード間で揃える。英語の見出し Elements も可）
    | 要素 | 次元 | 使用 | 効果 | 根拠 |

「使用」は yes / no / unknown。カードに無い要素は *不明*（❓）として数え、「使っていない」にはしない。
「効果」は本人の申告をそのまま（別々の解法の値を足さない）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .frontmatter import as_float, as_int, parse
from .mdtable import first_table

DIMENSIONS: tuple[tuple[str, str], ...] = (                            # (キー, 日本語の表示名)
    ("features", "埋め込み・特徴量"),
    ("preprocessing", "前処理"),
    ("augmentation", "拡張"),
    ("model", "モデル"),
    ("training", "学習戦略"),
    ("cv", "CV"),
    ("inference", "推論"),
    ("postprocessing", "後処理"),
    ("ensemble", "アンサンブル"),
)
DIM_KEYS = tuple(k for k, _ in DIMENSIONS)
DIM_LABEL = dict(DIMENSIONS)
ELEMENTS_HEADINGS = ("構成要素", "Elements")                            # 表を探す見出し（日英）
_COL = {                                                               # 表の列名（日英どちらでも）
    "name": ("要素", "Element"), "dim": ("次元", "Dimension"), "used": ("使用", "Used"),
    "effect": ("効果", "Effect", "申告の効果", "Self-reported effect"), "evidence": ("根拠", "Evidence"),
}


def _col(row: dict[str, str], key: str) -> str:
    """行の辞書から、日英どちらかの列名で値を取る。"""
    for name in _COL[key]:
        if name in row:
            return row[name]
    return ""


def norm_dim(s: str) -> str:
    """次元の表記ゆれ（日本語・略称）をキーに揃える。"""
    s = (s or "").strip().lower()
    for key, label in DIMENSIONS:
        if s == key or s == label.lower() or s.startswith(key[:4]):
            return key
    aliases = {"feature": "features", "embedding": "features", "特徴": "features", "埋め込み": "features",
               "preproc": "preprocessing", "前処理": "preprocessing", "aug": "augmentation", "拡張": "augmentation",
               "モデル": "model", "train": "training", "学習": "training", "validation": "cv", "検証": "cv",
               "infer": "inference", "tta": "inference", "推論": "inference", "post": "postprocessing", "後処理": "postprocessing",
               "ens": "ensemble", "blend": "ensemble", "stack": "ensemble", "アンサンブル": "ensemble", "合成": "ensemble"}
    for a, k in aliases.items():
        if s.startswith(a):
            return k
    return s or "other"


def norm_used(s: str) -> str:
    """使用の表記ゆれを yes / no / unknown に揃える。"""
    s = (s or "").strip().lower()
    if s in {"yes", "y", "true", "✅", "used", "1", "あり", "使った", "使用"}:
        return "yes"
    if s in {"no", "n", "false", "—", "-", "not used", "0", "なし", "使っていない", "未使用"}:
        return "no"
    return "unknown"


@dataclass
class Element:
    """構成要素の 1 行。"""

    name: str
    dimension: str
    used: str              # yes / no / unknown
    effect: str = ""       # 申告（カード）または実測（自陣）
    evidence: str = ""


@dataclass
class Card:
    """解法カード 1 枚。"""

    path: Path
    rank: int | None
    team: str
    medal: str
    private: float | None
    public: float | None
    single_model_private: float | None
    url: str
    elements: list[Element] = field(default_factory=list)
    meta: dict[str, str] = field(default_factory=dict)

    @property
    def label(self) -> str:
        """表と動画で使う短い名前（例 "#7"）。"""
        return f"#{self.rank}" if self.rank is not None else self.team or self.path.stem

    def element(self, name: str) -> Element | None:
        key = name.strip().lower()
        return next((e for e in self.elements if e.name.strip().lower() == key), None)


def _elements(body: str) -> list[Element]:
    """本文の「構成要素」の表 → Element の一覧。"""
    rows = first_table(body, ELEMENTS_HEADINGS)
    out: list[Element] = []
    for r in rows:
        name = _col(r, "name").strip()
        if not name or name.startswith(("(", "（")):                   # 空行と「（例）」の行は飛ばす
            continue
        out.append(Element(
            name=name,
            dimension=norm_dim(_col(r, "dim")),
            used=norm_used(_col(r, "used")),
            effect=_col(r, "effect").strip(),
            evidence=_col(r, "evidence").strip(),
        ))
    return out


def load_card(path: Path) -> Card:
    fm, body = parse(path.read_text(encoding="utf-8"))
    return Card(
        path=path,
        rank=as_int(fm.get("rank")),
        team=fm.get("team", "").strip(),
        medal=fm.get("medal", "").strip().lower(),
        private=as_float(fm.get("private")),
        public=as_float(fm.get("public")),
        single_model_private=as_float(fm.get("single_model_private")),
        url=fm.get("url", "").strip(),
        elements=_elements(body),
        meta=fm,
    )


def load_cards(solutions_dir: Path) -> list[Card]:
    """solutions/*.md を順位順に読む（README.md は除く）。"""
    cards = [load_card(p) for p in sorted(solutions_dir.glob("*.md")) if p.name != "README.md"]
    cards.sort(key=lambda c: (c.rank if c.rank is not None else 10**6, c.team))
    return cards


@dataclass
class Own:
    """自陣: 点数は own/final.md の front matter、構成要素は own/pipeline.md から。"""

    rank: int | None
    teams: int | None
    medal: str
    private_final: float | None
    private_best: float | None
    single_model_private: float | None
    public_final: float | None
    higher_is_better: bool
    name: str
    elements: list[Element] = field(default_factory=list)
    meta: dict[str, str] = field(default_factory=dict)

    def element(self, name: str) -> Element | None:
        key = name.strip().lower()
        return next((e for e in self.elements if e.name.strip().lower() == key), None)


def load_own(comp_dir: Path) -> Own:
    fm: dict[str, str] = {}
    final = comp_dir / "own" / "final.md"
    if final.exists():
        fm, _ = parse(final.read_text(encoding="utf-8"))
    elements: list[Element] = []
    pipeline = comp_dir / "own" / "pipeline.md"
    if pipeline.exists():
        _, body = parse(pipeline.read_text(encoding="utf-8"))
        elements = _elements(body)
    hib = (fm.get("higher_is_better", "yes").strip().lower() not in {"no", "false", "0", "いいえ"})
    return Own(
        rank=as_int(fm.get("rank")),
        teams=as_int(fm.get("teams")),
        medal=fm.get("medal", "").strip().lower(),
        private_final=as_float(fm.get("private_final")),
        private_best=as_float(fm.get("private_best")),
        single_model_private=as_float(fm.get("single_model_private")),
        public_final=as_float(fm.get("public_final")),
        higher_is_better=hib,
        name=fm.get("name", comp_dir.name),
        elements=elements,
        meta=fm,
    )
