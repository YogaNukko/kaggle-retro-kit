"""front matter（`---` で囲んだ `key: value` の行）の最小の読み書き。PyYAML に依存しない。

カードと own/*.md の先頭はこう書く:

    ---
    rank: 7
    team: some team
    private: 0.9574
    ---

値はすべて str で返す。数値は `as_float` / `as_int` で読む。入れ子やリストはわざと扱わない
（機械で読む部分を小さく保ち、文章は Markdown 側に書く）。
"""

from __future__ import annotations

import re

_FM = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)           # 先頭の --- ... --- を切り出す


def parse(text: str) -> tuple[dict[str, str], str]:
    """(front matter の辞書, 本文) を返す。front matter が無ければ ({}, 全文)。"""
    m = _FM.match(text)
    if not m:
        return {}, text
    data: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:       # 空行・コメント・コロン無しは飛ばす
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":           # 引用符で囲まれていれば外す
            v = v[1:-1]
        data[k.strip()] = v
    return data, text[m.end():]


def dump(data: dict[str, object]) -> str:
    """辞書 → front matter の文字列。記号を含む値は引用符で囲む。"""
    lines = ["---"]
    for k, v in data.items():
        s = "" if v is None else str(v)
        if any(ch in s for ch in ":#\"'") or s != s.strip():
            s = '"' + s.replace('"', '\\"') + '"'
        lines.append(f"{k}: {s}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def as_float(v: str | None) -> float | None:
    """文字列 → float。空・不明を表す語は None。"""
    if v is None:
        return None
    v = v.strip()
    if not v or v.lower() in {"none", "null", "nan", "?", "n/a", "unknown", "不明", "未確認"}:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def as_int(v: str | None) -> int | None:
    f = as_float(v)
    return int(f) if f is not None else None
