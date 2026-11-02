"""`retro` のコマンドライン。すべて非対話。Kaggle へのアップロードや提出はしない。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, kaggle
from . import index as idx
from . import own as ownmod
from .diff import write as write_diff
from .frontmatter import dump, parse
from .lint import lint_dir
from .lt import DEFAULT_AUDIENCE
from .lt import write as write_lt
from .medal import cutoffs
from .scaffold import new as scaffold_new
from .video import render as render_video


def root_dir() -> Path:
    """リポジトリの根 = `retro.py` のあるフォルダ（無ければカレント）。"""
    here = Path(__file__).resolve().parent.parent
    return here if (here / "templates").exists() else Path.cwd()


def comp_dir(root: Path, slug: str) -> Path:
    """`slug` は competitions/ 直下の名前か、任意の競合フォルダへのパス（例 examples/sample-competition）。"""
    d = root / "competitions" / slug
    if d.exists():
        return d
    alt = Path(slug)
    if alt.is_dir() and (alt / "own").exists():
        return alt.resolve()
    raise SystemExit(f"[ERROR] {d} が無い — 先に `retro new {slug}`")


def _deadline_from_status(d: Path) -> str | None:
    """status.md の「- 締切: …」から締切を拾う。"""
    p = d / "status.md"
    if not p.exists():
        return None
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith(("- 締切:", "- deadline:")):
            v = line.split(":", 1)[1].strip()
            return v if v and not v.startswith(("(", "（")) else None
    return None


# ---------------------------------------------------------------- 各コマンド

def cmd_new(a: argparse.Namespace) -> int:
    dest = scaffold_new(root_dir(), a.slug, a.name, a.deadline)
    print(f"作成: {dest}")
    for p in sorted(dest.rglob("*")):
        if p.is_file():
            print("  ", p.relative_to(dest))
    print(f"次: retro fetch {a.slug} --team \"<チーム名>\"")
    return 0


def cmd_fetch(a: argparse.Namespace) -> int:
    root = root_dir()
    d = comp_dir(root, a.slug)
    tmp = root / "tmp" / a.slug
    tmp.mkdir(parents=True, exist_ok=True)
    print("[fetch] コンペの行")
    try:
        kaggle.competition_row(a.slug, tmp / "competition_row.csv")
    except RuntimeError as e:
        print(f"  （飛ばす）{e}")
    print("[fetch] LB")
    lb_file = kaggle.leaderboard(a.slug, tmp / "lb")
    print("[fetch] 自分の提出一覧")
    kaggle.submissions(a.slug, tmp / "submissions.csv")
    (tmp / "fetched_at.txt").write_text(idx.now_iso(), encoding="utf-8")
    subs = ownmod.read_submissions(tmp / "submissions.csv")
    lb = ownmod.read_lb(lb_file) if lb_file else None
    s = ownmod.summarize(subs, lb, a.team, not a.lower_is_better)
    print(s.text())
    # 分かったことを own/final.md の front matter に書く。本文は触らない
    final = d / "own" / "final.md"
    fm, body = parse(final.read_text(encoding="utf-8")) if final.exists() else ({}, "")
    fm.update({
        "teams": s.teams or fm.get("teams", ""),
        "rank": s.rank if s.rank is not None else fm.get("rank", ""),
        "private_best": (s.best_private or {}).get("privateScore", fm.get("private_best", "")),
        "public_best": (s.best_public or {}).get("publicScore", fm.get("public_best", "")),
        "n_submissions": s.n_submissions,
        "higher_is_better": "no" if a.lower_is_better else "yes",
        "lb_columns": " ".join(s.lb_columns),
        "fetched_at": idx.now_iso(),
    })
    fm.setdefault("private_final", fm.get("private_best", ""))        # 選んだ提出が分からないので最良で代用
    fm.setdefault("single_model_private", "")
    if s.teams and s.rank is not None:
        fm["medal"] = cutoffs(s.teams).band(s.rank)                   # 推定の圏
    final.parent.mkdir(parents=True, exist_ok=True)
    final.write_text(dump(fm) + body, encoding="utf-8")
    print(f"{final} の front matter を書いた（private_final は private 最良で仮置き。別の提出を選んでいたら直す）")
    return 0


def cmd_collect(a: argparse.Namespace) -> int:
    root = root_dir()
    d = comp_dir(root, a.slug)
    tmp = root / "tmp" / a.slug
    topics_dir = tmp / "topics"
    print(f"[collect] 討論の一覧（最大 {a.max_pages} ページ）")
    pages = []
    for p in range(1, a.max_pages + 1):
        f = topics_dir / f"list_p{p}.csv"
        if not kaggle.topics_page(a.slug, p, f):
            break
        pages.append(f)
    if not pages:
        print("[ERROR] 討論の一覧が 1 ページも取れない（slug か Kaggle の認証を確かめる）")
        return 1
    cands = idx.detect(pages, a.slug)
    print(f"[collect] {len(pages)} ページから解法記事らしい題名 {len(cands)} 件")
    wdir = tmp / "writeups"
    wdir.mkdir(parents=True, exist_ok=True)
    new_text = 0
    for c in cands:                                                    # 本文はまだ無い分だけ取る
        dst = wdir / f"{c['topic_id']}.txt"
        if dst.exists() and dst.stat().st_size > 0:
            continue
        if kaggle.topic_show(c["topic_id"], dst):
            new_text += 1
        else:
            print(f"  取れない: topic {c['topic_id']}")
    index_path = d / "writeups_index.csv"
    rows, new_rows = idx.update(idx.read_index(index_path), cands)
    idx.write_index(index_path, rows)
    print(f"[collect] 索引: +{new_rows} 行、本文 +{new_text} 件 → {wdir}")
    print()
    print(idx.status(rows, _deadline_from_status(d), a.top))
    print("\n未分析:")
    for r in rows:
        if (r.get("analyzed") or "") == "":
            print(f"  {r['rank'] or '?':>4}  {r['title'][:70]}  （票 {r['votes']}）  topic {r['topic_id']}")
    return 0


def cmd_status(a: argparse.Namespace) -> int:
    root = root_dir()
    d = comp_dir(root, a.slug)
    print(idx.status(idx.read_index(d / "writeups_index.csv"), _deadline_from_status(d), a.top))
    return 0


def cmd_diff(a: argparse.Namespace) -> int:
    root = root_dir()
    d = comp_dir(root, a.slug)
    md, data = write_diff(d, a.top)
    print(f"書いた: {md}\n書いた: {data}")
    print(f"次: retro video {a.slug}")
    return 0


def cmd_video(a: argparse.Namespace) -> int:
    root = root_dir()
    d = comp_dir(root, a.slug)
    return render_video(root, d, a.page, a.name, a.fps, a.gif, a.sheet)


def cmd_lt(a: argparse.Namespace) -> int:
    d = comp_dir(root_dir(), a.slug)
    try:
        deck = write_lt(d, minutes=a.minutes, audience=a.audience, output=a.output, force=a.force, top_n=a.top)
    except (OSError, ValueError) as e:
        print(f"[ERROR] {e}")
        return 1
    print(f"書いた: {deck}")
    print("次: retro-lt スキルで原稿を整え、資料作成スキルで PowerPoint を制作する（lt-studio にも取り込めます）")
    return 0


def cmd_lint(a: argparse.Namespace) -> int:
    root = root_dir()
    rc = 0
    for slug in a.slugs:
        d = comp_dir(root, slug)
        errs, warns = lint_dir(d)
        for w in warns:
            print(f"[warn] {w}")
        for e in errs:
            print(f"[ERROR] {e}")
        print(f"[{'FAIL' if errs else 'ok'}] {slug}")
        rc = rc or (1 if errs else 0)
    return rc


def cmd_medal(a: argparse.Namespace) -> int:
    c = cutoffs(a.teams)
    print(f"チーム数 {c.teams}: 金 ≤ {c.gold} 位、銀 ≤ {c.silver} 位、銅 ≤ {c.bronze} 位（推定。同点と丸めで 1 位ずれることがある）")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="retro", description="終わった Kaggle コンペの振り返り: 自陣の確定 → 解法の収集 → 差分 → 動画 / LT")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new", help="competitions/<slug>/ を雛形から作る")
    p.add_argument("slug")
    p.add_argument("--name", help="コンペ名")
    p.add_argument("--deadline", help="締切（UTC ISO。例 2026-10-22T23:59:00Z）")
    p.set_defaults(fn=cmd_new)

    p = sub.add_parser("fetch", help="LB と自分の提出一覧 → own/final.md（Kaggle CLI、読み取りのみ）")
    p.add_argument("slug")
    p.add_argument("--team", help="LB に出るチーム名")
    p.add_argument("--lower-is-better", action="store_true", help="指標が小さいほど良いコンペ")
    p.set_defaults(fn=cmd_fetch)

    p = sub.add_parser("collect", help="討論の解法記事 → tmp/<slug>/writeups/ と writeups_index.csv（何度でも）")
    p.add_argument("slug")
    p.add_argument("--max-pages", type=int, default=30)
    p.add_argument("--top", type=int, default=20)
    p.set_defaults(fn=cmd_collect)

    p = sub.add_parser("status", help="解法記事の集まり具合")
    p.add_argument("slug")
    p.add_argument("--top", type=int, default=20)
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser("diff", help="カード × 自陣 → diff.md と video/data.json")
    p.add_argument("slug")
    p.add_argument("--top", type=int, default=20, help="「上位 N 件」の N")
    p.set_defaults(fn=cmd_diff)

    p = sub.add_parser("video", help="data.json → MP4（+GIF、ポスター）。video/tools/render.mjs を呼ぶ")
    p.add_argument("slug")
    p.add_argument("--page", help="自作のページ（既定は video/pages/explainer.html）")
    p.add_argument("--name", help="出力ファイルの名前（既定は slug）")
    p.add_argument("--fps", type=int)
    p.add_argument("--gif", action="store_true", help="GIF も書く")
    p.add_argument("--sheet", action="store_true", help="一覧画像だけ（動画は書かない。確認用）")
    p.set_defaults(fn=cmd_video)

    p = sub.add_parser("lt", help="分析から出典付き LT 原稿と資料を生成（lt-studio 互換）")
    p.add_argument("slug")
    p.add_argument("--minutes", type=int, default=5, help="持ち時間（分、既定 5）")
    p.add_argument("--audience", default=DEFAULT_AUDIENCE, help="想定する聴衆")
    p.add_argument("--top", type=int, default=20, help="比較する上位順位の範囲")
    p.add_argument("--output", type=Path, help="出力フォルダ（既定 competitions/<slug>/lt）")
    p.add_argument("--force", action="store_true", help="生成対象のみ上書き（手書きの原稿やノートは保持）")
    p.set_defaults(fn=cmd_lt)

    p = sub.add_parser("lint", help="カード・自陣・レポートの形を検査")
    p.add_argument("slugs", nargs="+")
    p.set_defaults(fn=cmd_lint)

    p = sub.add_parser("medal", help="チーム数からメダル圏の境目を推定")
    p.add_argument("teams", type=int)
    p.set_defaults(fn=cmd_medal)

    a = ap.parse_args(argv)
    try:
        return a.fn(a)
    except kaggle.KaggleMissing as e:
        print(f"[ERROR] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
