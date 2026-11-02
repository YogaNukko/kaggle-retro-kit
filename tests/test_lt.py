import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from retrokit.cli import main
from retrokit.lt import build_deck, write

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "sample-competition"


def _copy(tmp_path: Path) -> Path:
    return Path(shutil.copytree(EXAMPLE, tmp_path / "competition"))


def test_export_is_portable_and_preserves_provenance(tmp_path: Path):
    output = tmp_path / "bundle"
    deck = json.loads(write(EXAMPLE, output=output).read_text(encoding="utf-8"))
    assert deck["schema_version"] == "1.0" and deck["kind"] == "kaggle"
    assert "合成データ" in deck["title"]
    assert 5 <= len(deck["slides"]) <= 7
    sources = {source["id"]: source for source in deck["sources"]}
    for source in sources.values():
        assert (output / source["path"]).is_file()
        assert (output / source["path"]).resolve().is_relative_to(output)
    items = [item for slide in deck["slides"] for item in slide["evidence"]]
    assert {"measured", "reported", "inferred"} <= {item["status"] for item in items}
    for item in items:
        assert item["source_ids"] and set(item["source_ids"]) <= sources.keys()
        if item["status"] == "reported":
            assert all("/solutions/" in sources[ref]["path"] for ref in item["source_ids"])
    assert not (output / "tmp").exists()
    # A bundle can move without any reference to the original checkout.
    moved = tmp_path / "moved"
    output.rename(moved)
    assert all((moved / source["path"]).is_file() for source in sources.values())


def test_unknown_is_not_untried_and_effects_are_separate(tmp_path: Path):
    comp = _copy(tmp_path)
    pipeline = comp / "own" / "pipeline.md"
    pipeline.write_text(pipeline.read_text(encoding="utf-8").replace("| model | no |", "| model | unknown |"), encoding="utf-8")
    deck = build_deck(comp)
    gap = next(slide for slide in deck["slides"] if slide["title"] == "局所切り出しの別モデル")
    own_item = gap["evidence"][0]
    assert own_item["status"] == "unknown" and "不明" in own_item["text"]
    assert "未実施" not in own_item["text"] and "不使用" not in own_item["text"]
    effects = [item for item in gap["evidence"] if item["status"] == "reported"]
    assert effects and all(len(item["source_ids"]) == 1 for item in effects)
    assert any("記載なし" in item["text"] for item in gap["evidence"])


def test_lower_is_better_and_missing_own_scores(tmp_path: Path):
    comp = _copy(tmp_path)
    final = comp / "own" / "final.md"
    text = final.read_text(encoding="utf-8").replace("higher_is_better: yes", "higher_is_better: no")
    final.write_text(text.replace("private_final: 0.9452", "private_final:"), encoding="utf-8")
    position = next(slide for slide in build_deck(comp)["slides"] if slide["id"] == "position")
    assert "小さいほど良い" in position["message"] and "小さいほど良い" in position["visual"]
    score = next(item for item in position["evidence"] if "自陣の最終 private" in item["text"])
    assert score["status"] == "unknown" and "記録なし" in score["text"]
    assert "実測" not in score["text"]


@pytest.mark.parametrize("minutes", [1, 3, 5, 10, 30])
def test_time_budget(minutes: int):
    deck = build_deck(EXAMPLE, minutes=minutes)
    seconds = [slide["seconds"] for slide in deck["slides"]]
    assert all(type(value) is int and value > 0 for value in seconds)
    assert sum(seconds) <= minutes * 60


@pytest.mark.parametrize("minutes", [0, -1, True, 2.5])
def test_invalid_minutes_do_not_write(tmp_path: Path, minutes):
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="持ち時間"):
        write(EXAMPLE, minutes=minutes, output=output)
    assert not output.exists()


def test_overwrite_requires_opt_in_and_preserves_authored_files(tmp_path: Path):
    output = tmp_path / "bundle"
    path = write(EXAMPLE, output=output)
    original = path.read_bytes()
    notes = output / "outline.md"
    notes.write_text("人が編集した原稿", encoding="utf-8")
    with pytest.raises(FileExistsError):
        write(EXAMPLE, output=output)
    assert path.read_bytes() == original
    write(EXAMPLE, output=output, minutes=10, force=True)
    assert notes.read_text(encoding="utf-8") == "人が編集した原稿"
    assert json.loads(path.read_text(encoding="utf-8"))["duration_minutes"] == 10


@pytest.mark.parametrize("relative", [".", "own", "own/export", "solutions/export", ".."])
def test_output_cannot_overlap_original_records(tmp_path: Path, relative: str):
    comp = _copy(tmp_path)
    source = comp / "own" / "final.md"
    original = source.read_bytes()
    with pytest.raises(ValueError, match="重なります"):
        write(comp, output=comp / relative, force=True)
    assert source.read_bytes() == original


def test_preflight_rejects_collision_before_writing(tmp_path: Path):
    output = tmp_path / "bundle"
    (output / "sources" / "own" / "final.md").mkdir(parents=True)
    with pytest.raises(ValueError, match="同名のフォルダ"):
        write(EXAMPLE, output=output, force=True)
    assert not (output / "deck.json").exists()
    assert not (output / "sources" / "analysis.md").exists()


def test_output_symlink_cannot_escape(tmp_path: Path):
    output = tmp_path / "bundle"
    outside = tmp_path / "outside"
    output.mkdir()
    outside.mkdir()
    try:
        (output / "sources").symlink_to(outside, target_is_directory=True)
    except OSError:
        if os.name != "nt":
            pytest.skip("Creating symlinks is not available in this environment")
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "New-Item -ItemType Junction -Path $env:LT_TEST_LINK -Target $env:LT_TEST_TARGET | Out-Null"],
            env={**os.environ, "LT_TEST_LINK": str(output / "sources"), "LT_TEST_TARGET": str(outside)},
            capture_output=True,
        )
        if result.returncode:
            pytest.skip("Creating Windows junctions is not available in this environment")
    try:
        with pytest.raises(ValueError, match="外を指しています"):
            write(EXAMPLE, output=output, force=True)
    finally:
        # Remove the link itself, never recursively traverse its target.
        if (output / "sources").is_symlink():
            (output / "sources").unlink()
        else:
            (output / "sources").rmdir()
    assert not list(outside.iterdir())


def test_cli_lt_and_clean_invalid_input(tmp_path: Path, capsys):
    output = tmp_path / "bundle"
    assert main(["lt", str(EXAMPLE), "--output", str(output), "--audience", "初学者"]) == 0
    deck = json.loads((output / "deck.json").read_text(encoding="utf-8"))
    assert deck["audience"] == "初学者"
    assert main(["lt", str(EXAMPLE), "--output", str(tmp_path / "invalid"), "--minutes", "0"]) == 1
    assert "[ERROR]" in capsys.readouterr().out


def test_frequency_only_does_not_claim_causation(tmp_path: Path):
    comp = _copy(tmp_path)
    # Drop all reported effect values without changing the usage pattern.
    for card in (comp / "solutions").glob("*.md"):
        lines = []
        for line in card.read_text(encoding="utf-8").splitlines():
            fields = line.split("|")
            if len(fields) == 7 and fields[1].strip() not in {"要素", "---", ""}:
                fields[4] = " "
                line = "|".join(fields)
            lines.append(line)
        card.write_text("\n".join(lines) + "\n", encoding="utf-8")
    gaps = [slide for slide in build_deck(comp)["slides"] if slide["id"].startswith("gap-")]
    assert any("頻度だけ" in slide["message"] for slide in gaps)
    assert all("因果ではない" in slide["speaker_notes"] for slide in gaps)
