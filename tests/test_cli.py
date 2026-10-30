import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_new_and_lint(tmp_path: Path):
    """`retro new` がリポジトリの根の写し（templates + competitions/README.md）で動く。"""
    (tmp_path / "templates").mkdir()
    for t in (ROOT / "templates").glob("*.md"):
        (tmp_path / "templates" / t.name).write_text(t.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "competitions").mkdir()
    header = "| slug | name | deadline | state | status |\n|---|---|---|---|---|\n"
    (tmp_path / "competitions" / "README.md").write_text(header, encoding="utf-8")
    from retrokit.scaffold import new

    dest = new(tmp_path, "demo-comp", "Demo", "2026-01-01T00:00:00Z")
    assert (dest / "own" / "final.md").exists() and (dest / "writeups_index.csv").exists()
    assert "| demo-comp |" in (tmp_path / "competitions" / "README.md").read_text(encoding="utf-8")


def test_cli_medal():
    out = subprocess.run([sys.executable, str(ROOT / "retro.py"), "medal", "1250"], capture_output=True, text=True, check=True).stdout
    assert "金 ≤ 12 位" in out
