from pathlib import Path

from retrokit.cards import load_card, load_cards, load_own
from retrokit.diff import build, to_markdown
from retrokit.frontmatter import dump, parse
from retrokit.lint import lint_dir
from retrokit.mdtable import first_table

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "sample-competition"


def test_frontmatter_roundtrip():
    text = dump({"rank": 7, "team": "a: b", "private": 0.95})
    fm, body = parse(text + "# title\n")
    assert fm["rank"] == "7" and fm["team"] == "a: b" and body.startswith("# title")


def test_mdtable_first_table():
    md = "## 構成要素\n\n| 要素 | 使用 |\n|---|---|\n| a \\| b | yes |\n\n## 他\n| x |\n|---|\n| 1 |\n"
    rows = first_table(md, ("構成要素", "Elements"))
    assert rows == [{"要素": "a | b", "使用": "yes"}]


def test_example_cards_load():
    cards = load_cards(EXAMPLE / "solutions")
    assert [c.rank for c in cards] == [1, 5, 21, 33, 63, 72]
    c = load_card(EXAMPLE / "solutions" / "001-aurora.md")
    assert c.medal == "gold" and c.private == 0.9611
    assert c.element("画像を読む教師ラベル").used == "yes"
    own = load_own(EXAMPLE)
    assert own.rank == 102 and own.teams == 1250 and own.element("反転 TTA").used == "yes"


def test_example_diff_rules():
    d = build(EXAMPLE)
    assert d.cutoffs == {"gold": 12, "silver": 62, "bronze": 125} and d.own_band == "none"
    by_name = {r.name: r for r in d.elements}
    # 本文に無い（unknown）を「使っていない」にしない
    assert by_name["局所切り出しの別モデル"].cells["#21"] == "unknown"
    # 差分の順位: 自陣が yes でなく、誰かが使っている
    assert d.gaps and all(r.own != "yes" for r in d.gaps)
    assert d.gaps[0].name == "局所切り出しの別モデル"
    # 境目の候補には ablation の申告が要る
    assert by_name["画像を読む教師ラベル"].verdict == "candidate"
    assert by_name["2.5D のスライス積み"].verdict == "not a boundary"
    md = to_markdown(d)
    assert "## 差分の順位" in md and "足さない" in md


def test_example_lints_clean():
    errs, _ = lint_dir(EXAMPLE)
    assert errs == []
