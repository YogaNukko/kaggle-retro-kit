"""competitions/<slug>/ の記録が、後から（`retro diff`・自分・動画が）読み返せる形かを検査する。"""

from __future__ import annotations

import re
from pathlib import Path

from .cards import DIM_KEYS, load_card
from .frontmatter import parse
from .index import INDEX_FIELDS, read_index

CARD_SECTIONS: tuple[tuple[str, ...], ...] = (                         # 必須の節（日英どちらか）
    ("## 要約", "## Summary"),
    ("## 構成要素", "## Elements"),
    ("## 9 次元", "## Pipeline"),
    ("## 持ち帰り候補", "## Takeaways"),
)
_PLACEHOLDER = re.compile(r"\{\{[A-Z_]+\}\}")
_URL = re.compile(r"https?://\S+")


def lint_card(path: Path) -> list[str]:
    """カード 1 枚の問題点（空なら合格）。"""
    errs: list[str] = []
    text = path.read_text(encoding="utf-8")
    fm, body = parse(text)
    for key in ("rank", "team", "url"):
        if not fm.get(key):
            errs.append(f"{path}: front matter に `{key}` が無い")
    for alts in CARD_SECTIONS:
        if not any(re.search(rf"^{re.escape(s)}", body, re.MULTILINE) for s in alts):
            errs.append(f"{path}: 節 `{alts[0]}` が無い")
    if not _URL.search(text):
        errs.append(f"{path}: 出典の URL が無い")
    if _PLACEHOLDER.search(text):
        errs.append(f"{path}: 雛形の {{{{…}}}} が残っている")
    card = load_card(path)
    if not card.elements:
        errs.append(f"{path}: 「構成要素」の表が空（retro diff には 1 行以上要る）")
    for e in card.elements:
        if e.dimension not in DIM_KEYS:
            errs.append(f"{path}: 要素 `{e.name}` の次元 `{e.dimension}` が不明（{', '.join(DIM_KEYS)} のどれかにする）")
    return errs


def lint_dir(comp_dir: Path) -> tuple[list[str], list[str]]:
    """(エラーの一覧, 警告の一覧)。"""
    errs: list[str] = []
    warns: list[str] = []
    if not comp_dir.is_dir():
        return [f"{comp_dir}: フォルダではない"], warns
    if not (comp_dir / "status.md").exists():
        errs.append(f"{comp_dir}/status.md が無い")
    index = comp_dir / "writeups_index.csv"
    if not index.exists():
        errs.append(f"{index} が無い")
    else:
        rows = read_index(index)
        raw = index.read_text(encoding="utf-8")
        header = raw.splitlines()[0].split(",") if raw.strip() else []
        if header != INDEX_FIELDS:
            errs.append(f"{index}: 見出しが {INDEX_FIELDS} と違う")
        for r in rows:
            if (r.get("analyzed") or "").lower() == "yes":
                card = r.get("card") or ""
                if not card:
                    errs.append(f"{index}: topic {r['topic_id']} は analyzed=yes なのに card が空")
                elif not (comp_dir / card).exists():
                    errs.append(f"{index}: card {card} が無い")
    for card in sorted((comp_dir / "solutions").glob("*.md")):
        errs.extend(lint_card(card))
    for own in sorted((comp_dir / "own").glob("*.md")):
        if _PLACEHOLDER.search(own.read_text(encoding="utf-8")):
            warns.append(f"{own}: 雛形の {{{{…}}}} が残っている（終了直後は可。閉じる前に埋める）")
    final = comp_dir / "own" / "final.md"
    if final.exists():
        fm, _ = parse(final.read_text(encoding="utf-8"))
        for key in ("rank", "teams", "private_final"):
            if not fm.get(key):
                warns.append(f"{final}: front matter の `{key}` が空（階段とメダル圏が欠ける）")
    for name in ("report.md", "lessons.md"):
        p = comp_dir / name
        if p.exists() and _PLACEHOLDER.search(p.read_text(encoding="utf-8")):
            errs.append(f"{p}: 雛形の {{{{…}}}} が残っている")
    return errs, warns
