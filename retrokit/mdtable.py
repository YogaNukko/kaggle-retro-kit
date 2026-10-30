"""Markdown の表（| で区切った表）を、見出しの下から読む。

カードの機械で読む部分を普通の表にしてあるのは、人が道具なしで直せて、`retro diff` が読み返せるようにするため。
"""

from __future__ import annotations

import re


def section(text: str, headings: str | tuple[str, ...]) -> str:
    """最初に見つかった `## 見出し…` の節の本文を返す（見出しは前方一致。日本語と英語の両方を渡せる）。"""
    heads = (headings,) if isinstance(headings, str) else headings
    lines = text.splitlines()
    start = None
    level = 0
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if not m:
            continue
        if start is None:                                              # 節の開始を探す
            if any(m.group(2).strip().startswith(h) for h in heads):
                start, level = i + 1, len(m.group(1))
        elif len(m.group(1)) <= level:                                 # 同じ深さ以上の見出しで節が終わる
            return "\n".join(lines[start:i])
    return "\n".join(lines[start:]) if start is not None else ""


def tables(text: str) -> list[list[dict[str, str]]]:
    """文中のすべての表を、見出しセルをキーにした行の辞書の一覧として返す。"""
    out: list[list[dict[str, str]]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            header = _cells(lines[i])                                  # 見出し行
            i += 2                                                     # 区切り行（---）を飛ばす
            rows: list[dict[str, str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = _cells(lines[i])
                cells += [""] * (len(header) - len(cells))             # 足りないセルは空で埋める
                rows.append(dict(zip(header, cells, strict=False)))
                i += 1
            out.append(rows)
        else:
            i += 1
    return out


def first_table(text: str, headings: str | tuple[str, ...]) -> list[dict[str, str]]:
    """指定した節の最初の表。無ければ空。"""
    ts = tables(section(text, headings))
    return ts[0] if ts else []


def _cells(line: str) -> list[str]:
    """`| a | b |` → ["a", "b"]。`\\|` はセル内の | として扱う。"""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line)]
