"""competitions/<slug>/ を雛形から作る。既にあれば止まる（上書きしない）。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .index import write_index

FILES = {                                                              # 作るファイル → 雛形
    "status.md": "status.md",
    "own/final.md": "own_final.md",
    "own/pipeline.md": "own_pipeline.md",
    "report.md": "report.md",
    "lessons.md": "lessons.md",
    "video/README.md": "video_README.md",
}


def render(src: Path, dst: Path, subs: dict[str, str]) -> None:
    """雛形の {{KEY}} を置き換えて写す。置き換えない {{…}} は記入欄として残る。"""
    text = src.read_text(encoding="utf-8")
    for k, v in subs.items():
        text = text.replace("{{" + k + "}}", v)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")


def new(root: Path, slug: str, name: str | None, deadline: str | None) -> Path:
    dest = root / "competitions" / slug
    if dest.exists():
        raise SystemExit(f"[ERROR] 既にある: {dest}（続きはこのフォルダで。何も変えていない）")
    templates = root / "templates"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    subs = {"SLUG": slug, "NAME": name or slug, "DEADLINE": deadline or "（未記入）", "TODAY": today}
    for rel, tpl in FILES.items():
        render(templates / tpl, dest / rel, subs)
    (dest / "solutions").mkdir(parents=True)
    (dest / "solutions" / ".gitkeep").touch()
    (dest / "video" / "out").mkdir(parents=True)
    (dest / "video" / "out" / ".gitkeep").touch()
    write_index(dest / "writeups_index.csv", [])                       # 見出しだけの索引
    (root / "tmp" / slug).mkdir(parents=True, exist_ok=True)           # 取得物の置き場（管理外）
    listing = root / "competitions" / "README.md"
    if listing.exists() and f"| {slug} |" not in listing.read_text(encoding="utf-8"):
        with listing.open("a", encoding="utf-8") as f:
            f.write(f"| {slug} | {subs['NAME']} | {subs['DEADLINE']} | 進行中 | [status]({slug}/status.md) |\n")
    return dest
