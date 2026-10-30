"""解法記事の索引（competitions/<slug>/writeups_index.csv）。

`detect` は討論の題名から解法記事らしいもの（"7th place" "#32" "gold solution" "解法"）を拾い、
`update` は候補を索引に足す（手で直した欄は守る）。`status` は集まり具合を事実だけで出す（閉じる判断はしない）。
"""

from __future__ import annotations

import csv
import io
import re
from datetime import datetime, timezone
from pathlib import Path

INDEX_FIELDS: list[str] = [                                            # 索引の列（この順）
    "topic_id", "rank", "medal", "team", "title", "url", "posted_at", "votes",
    "fetched_at", "card", "analyzed", "notes",
]
AUTO_FIELDS = ("title", "url", "posted_at", "votes", "fetched_at")    # update で必ず候補側の値に更新する欄
FILL_IF_EMPTY = ("rank", "medal")                                      # 索引側が空のときだけ埋める欄

_RANK_PATTERNS = (                                                     # 題名から順位を取る型
    re.compile(r"(?<![\d.])(\d{1,4})(?:st|nd|rd|th)\b", re.IGNORECASE),
    re.compile(r"#\s?(\d{1,4})(?![\d.])"),
    re.compile(r"(?<![\d.])(\d{1,4})\s*位"),
    re.compile(r"\b(?:rank|place)\s*[:#]?\s*(\d{1,4})(?![\d.])", re.IGNORECASE),
)
_SOLUTION_WORDS = re.compile(r"solution|write-?up|approach|解法|ソリューション", re.IGNORECASE)
_MEDALS = (                                                            # "gold-58" のように数字が続く語はメダルではない
    ("gold", re.compile(r"\bgold\b(?!\s*-?\s*\d)|金メダル|金圏", re.IGNORECASE)),
    ("silver", re.compile(r"\bsilver\b(?!\s*-?\s*\d)|銀メダル|銀圏", re.IGNORECASE)),
    ("bronze", re.compile(r"\bbronze\b(?!\s*-?\s*\d)|銅メダル|銅圏", re.IGNORECASE)),
)


def detect_title(title: str) -> tuple[int | None, str, bool]:
    """題名 → (順位, メダル, 解法記事らしいか)。"""
    rank = None
    for pat in _RANK_PATTERNS:                                         # 最初に当たった型の順位を採る
        m = pat.search(title)
        if m:
            rank = int(m.group(1))
            break
    found = [(m.start(), name) for name, pat in _MEDALS if (m := pat.search(title))]
    medal = min(found)[1] if found else ""                             # 複数あれば題名で先に出るもの
    has_word = bool(_SOLUTION_WORDS.search(title))
    is_question = title.rstrip().endswith(("?", "？"))                 # 「22nd or 23rd?」のような疑問文は除く
    return rank, medal, has_word or medal != "" or (rank is not None and not is_question)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def strip_to_header(text: str, first_col: str) -> str:
    """CSV の見出し行より前を捨てる（Kaggle CLI は先頭に版の警告を出すことがある）。"""
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.split(",")[0].strip() == first_col:
            return "".join(lines[i:])
    return text


def read_topics(paths: list[Path]) -> list[dict[str, str]]:
    """討論一覧の CSV（id,title,authorName,commentCount,votes,postDate）を束ねる。id の重複は除く。"""
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for p in paths:
        text = strip_to_header(p.read_text(encoding="utf-8"), "id")
        for row in csv.DictReader(io.StringIO(text, newline="")):
            tid = (row.get("id") or "").strip()
            if tid and tid not in seen:
                seen.add(tid)
                rows.append(row)
    return rows


def detect(topic_paths: list[Path], slug: str) -> list[dict[str, str]]:
    """討論一覧 → 解法記事の候補（索引と同じ列）。順位 → 票数の順に並べる。"""
    fetched = now_iso()
    cands: list[dict[str, str]] = []
    for row in read_topics(topic_paths):
        title = (row.get("title") or "").strip()
        rank, medal, ok = detect_title(title)
        if not ok:
            continue
        tid = row["id"].strip()
        cands.append({
            "topic_id": tid, "rank": "" if rank is None else str(rank), "medal": medal, "team": "",
            "title": title, "url": f"https://www.kaggle.com/competitions/{slug}/discussion/{tid}",
            "posted_at": (row.get("postDate") or "").strip(), "votes": (row.get("votes") or "").strip(),
            "fetched_at": fetched, "card": "", "analyzed": "", "notes": "",
        })
    cands.sort(key=lambda r: (int(r["rank"]) if r["rank"] else 10**6, -int(r["votes"] or 0)))
    return cands


def read_index(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return [dict(r) for r in csv.DictReader(f)]


def write_index(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=INDEX_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in INDEX_FIELDS})


def update(index: list[dict[str, str]], cands: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    """候補を索引に足す。(行, 新しく足した件数) を返す。手で直した欄（rank 以外の team/card/analyzed/notes 等）は守る。"""
    by_id = {r["topic_id"]: r for r in index}
    new = 0
    for c in cands:
        r = by_id.get(c["topic_id"])
        if r is None:                                                  # 新しい記事
            by_id[c["topic_id"]] = dict(c)
            new += 1
            continue
        for k in AUTO_FIELDS:                                          # 題名・票などは最新に
            r[k] = c[k]
        for k in FILL_IF_EMPTY:                                        # 順位・メダルは空のときだけ
            if not r.get(k) and c.get(k):
                r[k] = c[k]
    rows = list(by_id.values())
    rows.sort(key=lambda r: (int(r["rank"]) if (r.get("rank") or "").isdigit() else 10**6, -int(r.get("votes") or 0)))
    return rows, new


def status(rows: list[dict[str, str]], deadline: str | None = None, top: int = 20) -> str:
    """集まり具合（件数・分析済み・上位 N 位以内・締切からの日数）を事実だけで返す。"""
    analyzed = [r for r in rows if (r.get("analyzed") or "").lower() == "yes"]
    skipped = [r for r in rows if (r.get("analyzed") or "").lower() == "skip"]
    ranked = [r for r in rows if (r.get("rank") or "").isdigit() and int(r["rank"]) <= top]
    ranked_done = [r for r in ranked if (r.get("analyzed") or "").lower() == "yes"]
    lines = [
        f"索引の解法記事: {len(rows)} 件（分析済み {len(analyzed)}、対象外 {len(skipped)}）",
        f"上位 {top} 位以内: {len(ranked)} 件が索引にあり、{len(ranked_done)} 件が分析済み",
    ]
    if deadline:
        try:
            dl = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
            lines.append(f"締切からの経過日数: {(datetime.now(timezone.utc) - dl).days} 日")
        except ValueError:
            lines.append(f"締切（読めない形式）: {deadline}")
    return "\n".join(lines)
