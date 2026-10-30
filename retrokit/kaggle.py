"""Kaggle CLI（2.x）の薄い包み。読み取りだけ: 提出・Notebook の push・データのダウンロードはしない。"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class KaggleMissing(RuntimeError):
    """kaggle コマンドが無い。"""


def _run(args: list[str], out: Path | None = None) -> str:
    """`kaggle <args>` を実行して標準出力を返す。out を渡せばそのファイルにも書く。"""
    if shutil.which("kaggle") is None:
        raise KaggleMissing("`kaggle` CLI が見つからない。`pip install kaggle` の後に kaggle.json を置く（README 参照）")
    res = subprocess.run(["kaggle", *args], capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"kaggle {' '.join(args)} が失敗:\n{res.stderr.strip() or res.stdout.strip()}")
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(res.stdout, encoding="utf-8")
    return res.stdout


def competition_row(slug: str, out: Path) -> str:
    """コンペの行（締切・チーム数など）を CSV で。"""
    return _run(["competitions", "list", "-s", slug, "--csv"], out)


def leaderboard(slug: str, out_dir: Path) -> Path | None:
    """LB 全件（zip）を落とす。out_dir で最も新しいファイルを返す。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    _run(["competitions", "leaderboard", slug, "-d", "-p", str(out_dir), "-q"])
    files = sorted(out_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def submissions(slug: str, out: Path) -> str:
    """自分の提出一覧を CSV で（選んだ 2 本の印は返らない）。"""
    return _run(["competitions", "submissions", slug, "--csv"], out)


def topics_page(slug: str, page: int, out: Path) -> bool:
    """討論一覧の 1 ページを CSV で。空か失敗なら False。"""
    try:
        text = _run(["competitions", "topics", "list", slug, "-p", str(page), "--format", "csv"])
    except RuntimeError:
        return False
    if len(text.strip().splitlines()) <= 1:
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return True


def topic_show(topic_id: str, out: Path) -> bool:
    """討論 1 件の本文とコメントをファイルに。"""
    try:
        _run(["competitions", "topics", "show", topic_id], out)
        return True
    except RuntimeError:
        return False
