from pathlib import Path

from retrokit.index import detect, detect_title, read_index, status, update, write_index


def test_detect_title_rank_and_medal():
    assert detect_title("7th place solution")[0] == 7
    assert detect_title("#228 silver writeup")[:2] == (228, "silver")
    assert detect_title("Deadline 22nd or 23rd?")[2] is False
    assert detect_title("gold-58 labels: what are they?")[1] == ""  # "gold-58" はメダルではない


def test_detect_and_update_preserve_hand_edits(tmp_path: Path):
    topics = tmp_path / "list_p1.csv"
    csv = ("Warning: outdated\nid,title,authorName,commentCount,votes,postDate\n"
           "11,1st place solution,a,3,50,2026-10-01\n12,Thanks!,b,0,2,2026-10-01\n")
    topics.write_text(csv, encoding="utf-8")
    cands = detect([topics], "comp")
    assert [c["topic_id"] for c in cands] == ["11"]
    rows, new = update([], cands)
    assert new == 1
    rows[0]["team"] = "hand"
    rows[0]["analyzed"] = "yes"
    rows[0]["card"] = "solutions/001-hand.md"
    rows2, new2 = update(rows, cands)
    assert new2 == 0 and rows2[0]["team"] == "hand" and rows2[0]["analyzed"] == "yes"
    idx = tmp_path / "idx.csv"
    write_index(idx, rows2)
    assert read_index(idx)[0]["card"] == "solutions/001-hand.md"
    assert "上位 20 位以内: 1 件が索引にあり、1 件が分析済み" in status(rows2)
