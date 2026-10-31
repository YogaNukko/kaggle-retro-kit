"""Kaggle の分析から、lt-studio が読める出典付き LT 原稿を作る。"""

from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from .cards import load_cards
from .diff import Diff, ElementRow, build, to_markdown
from .medal import BAND_LABEL

DEFAULT_AUDIENCE = "Kaggle の基本を知っている機械学習エンジニア"
_VERDICT = {
    "candidate": "境目の候補", "frequency only": "頻度だけ",
    "not a boundary": "境目でない", "n/a": "判定不能（記述が少ない）",
}
_USED = {"yes": "使用", "no": "不使用", "unknown": "不明（本文に記載なし）"}


def _within(path: Path, root: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve())


def _inputs(comp_dir: Path) -> list[Path]:
    files = [comp_dir / "own" / name for name in ("final.md", "pipeline.md")]
    files += sorted((comp_dir / "solutions").glob("*.md"))
    files += [comp_dir / name for name in ("report.md", "README.md")]
    result = []
    for path in files:
        if not _within(path, comp_dir):
            raise ValueError(f"入力がコンペフォルダの外を指しています: {path}")
        if path.is_file():
            result.append(path)
    if not result:
        raise ValueError("LT に使う記録がありません。自陣の記録または解法カードを先に作成してください")
    return result


def _evidence(text: str, status: str, *source_ids: str) -> dict:
    return {"text": text, "status": status, "source_ids": list(dict.fromkeys(source_ids))}


def _slide(slide_id: str, title: str, message: str, evidence: list[dict], notes: str, visual: str) -> dict:
    return {
        "id": slide_id, "title": title, "message": message, "seconds": 1,
        "bullets": [item["text"] for item in evidence[:3]], "evidence": evidence,
        "speaker_notes": notes, "visual": visual,
    }


def _number(value: float | int | None) -> str:
    return "記録なし" if value is None else f"{value:g}"


def _position(d: Diff, own_source: str, card_ids: dict[str, str], synthetic: bool) -> dict:
    measured = "実測欄（合成データ）" if synthetic else "実測"
    reported = "申告欄（合成データ）" if synthetic else "本人申告"
    rank_status = "measured" if d.own_rank is not None and d.teams is not None else "unknown"
    score_status = "measured" if d.ladder.own_final is not None else "unknown"
    evidence = [
        _evidence(f"自陣の順位: {_number(d.own_rank)} / {_number(d.teams)} チーム"
                  + (f"（{measured}）" if rank_status == "measured" else "（一部または全部が不明）"), rank_status, own_source),
        _evidence(f"自陣の最終 private: {_number(d.ladder.own_final)}"
                  + (f"（{measured}）" if score_status == "measured" else "（不明）"), score_status, own_source),
    ]
    for card in d.cards[:3]:
        if card["private"] is not None:
            evidence.append(_evidence(f"{card['label']} {card['team']}: private {_number(card['private'])}（{reported}）",
                                      "reported", card_ids[str(card["label"])]))
    direction = "大きいほど良い" if d.higher_is_better else "小さいほど良い"
    return _slide(
        "position", "自陣と分析済み解法の位置", f"評価指標は{direction}。自陣の実測と他者の申告を分けて比較する。",
        evidence,
        "全参加者の分布ではなく、分析した解法カードとの比較。自陣の最終提出が仮置きの場合は元の記録の注記も伝える。"
        "他者の値を再現実験の結果として扱わない。",
        f"順位と private の編集可能な比較表。評価指標は{direction}と明記する。",
    )


def _gap_slide(row: ElementRow, index: int, card_ids: dict[str, str], own_source: str, synthetic: bool) -> dict:
    own_status = "unknown" if row.own == "unknown" else "measured"
    own_label = "実測欄（合成データ）" if synthetic else "実測"
    evidence = [_evidence(f"自陣: {_USED[row.own]}" + (f"（{own_label}）" if row.own != "unknown" else ""),
                          own_status, own_source)]
    for band, count in row.band_usage.items():
        if count["known"] + count["unknown"]:
            evidence.append(_evidence(
                f"{BAND_LABEL.get(band, band)}: 使用 {count['used']} / 記載あり {count['known']} 件、"
                f"記載なし {count['unknown']} 件（本人申告を集計）", "inferred", "analysis"))
    for effect in row.effects[:3]:
        label = "申告欄（合成データ）" if synthetic else "本人申告"
        evidence.append(_evidence(f"{effect['label']} の{label}: {effect['effect']}",
                                  "reported", card_ids[effect["label"]]))
    if row.own_effect:
        evidence.append(_evidence(f"自陣の{own_label}: {row.own_effect}", "measured", own_source))
    verdict = _VERDICT[row.verdict]
    evidence.append(_evidence(f"分析上の判定: {verdict}", "inferred", "analysis"))
    return _slide(
        f"gap-{index}", row.name, f"判定は「{verdict}」。採用の効果は自分の条件で検証する。", evidence,
        "使用率の差は因果ではない。分母は使用・不使用が書かれた件数で、記載なしを不使用に含めない。"
        "別々の解法の効果は合算しない。自陣の記録が不明なら未実施とは断定しない。",
        "圏ごとの使用数・記載数・不明数を表で示す。本人申告の効果は解法ごとに分けて添える。",
    )


def _bundle(comp_dir: Path, minutes: int, audience: str, top_n: int) -> tuple[dict, dict[str, bytes]]:
    if type(minutes) is not int or minutes <= 0:
        raise ValueError("持ち時間 --minutes は 1 以上の整数にしてください")
    if not audience.strip():
        raise ValueError("聴衆 --audience を指定してください")
    if type(top_n) is not int or top_n <= 0:
        raise ValueError("--top は 1 以上の整数にしてください")
    files = _inputs(comp_dir)
    cards = load_cards(comp_dir / "solutions")
    labels = [card.label for card in cards]
    if len(labels) != len(set(labels)):
        raise ValueError("同じ順位ラベルのカードがあります。出典を一意にできないため、LT の書き出しを停止しました")
    d = build(comp_dir, top_n)
    # JSON cannot represent NaN or infinity; reject malformed input before writing anything.
    values = [d.ladder.own_final, d.ladder.own_best, d.ladder.own_single,
              *(value for card in d.cards for value in (card["private"], card["single"]))]
    if any(value is not None and not math.isfinite(value) for value in values):
        raise ValueError("スコアに有限でない値が含まれています")
    payload = {f"sources/{path.relative_to(comp_dir).as_posix()}": path.read_bytes() for path in files}
    payload["sources/analysis.md"] = to_markdown(d).encode("utf-8")
    readme = payload.get("sources/README.md", b"").decode("utf-8", errors="replace")
    synthetic = comp_dir.name == "sample-competition" or "合成データ" in readme
    sources = [{"id": "analysis", "title": "解法カードと自陣の記録から計算した差分",
                "path": "sources/analysis.md", "note": "使用頻度の差は因果を意味しない"}]
    source_by_path = {}
    for index, path in enumerate(files, start=1):
        relative = path.relative_to(comp_dir).as_posix()
        source_id = f"source-{index:03d}"
        source_by_path[relative] = source_id
        sources.append({"id": source_id, "title": relative, "path": f"sources/{relative}"})
    by_id = {source["id"]: source for source in sources}
    card_ids = {}
    for card in cards:
        source_id = source_by_path[f"solutions/{card.path.name}"]
        card_ids[card.label] = source_id
        by_id[source_id]["title"] = f"{card.label} {card.team} の解法カード"
        if card.url:
            parsed = urlsplit(card.url)
            if parsed.scheme in {"http", "https"} and parsed.netloc and not parsed.username and not parsed.password:
                by_id[source_id]["url"] = card.url
    final_id = source_by_path.get("own/final.md", "analysis")
    pipeline_id = source_by_path.get("own/pipeline.md", "analysis")
    disclosure = "チーム・点数・解法はすべて架空の合成データ。" if synthetic else ""
    intro_evidence = [_evidence(f"分析済みの解法カード: {len(cards)} 件", "inferred", "analysis")]
    if synthetic:
        intro_evidence.insert(0, _evidence(disclosure, "inferred", source_by_path.get("README.md", "analysis")))
    slides = [_slide(
        "scope", f"{d.name} のソリューション比較" + ("（合成データ例）" if synthetic else ""),
        disclosure + "自陣と分析済みの解法を比較し、次に検証する差分を探す。", intro_evidence,
        disclosure + "競技の課題・入力・評価指標の意味は元のコンペ資料を確認して補う。"
        "この原稿は比較分析の下書きで、全解法を網羅しているとは限らない。",
        "コンペ名と比較の目的を簡潔に示す。",
    ), _position(d, final_id, card_ids, synthetic)]
    if minutes >= 3:
        shared_evidence = []
        for row in d.elements:
            if row.name in d.shared:
                shared_evidence.append(_evidence(
                    f"{row.name}: 分析済み上位 {top_n} 位以内で使用 {row.used_top} / 記載あり {row.known_top} 件"
                    "（本人申告を集計）", "inferred", "analysis"))
        slides.append(_slide(
            "shared", "分析済み上位解法の共通点", "記述が確認できた解法の範囲で共通点を整理する。",
            shared_evidence[:3] or [_evidence("共通点を確定できる記述が不足している", "unknown", "analysis")],
            "記載なしの解法まで同じ手法を使ったとは扱わない。カードに未記載の情報は元の記事で確認する。",
            "要素ごとの使用数と記載数を示す短い表。",
        ))
    # Tuning choices are not structural takeaways; keep them in the full analysis.
    tuning_terms = ("seed", "シード", "checkpoint", "チェックポイント", "学習率", "learning rate", "ハイパラ")
    gaps = [row for row in d.gaps if not any(term in row.name.lower() for term in tuning_terms)][:2 if minutes >= 5 else 1]
    for index, row in enumerate(gaps, start=1):
        slides.append(_gap_slide(row, index, card_ids, pipeline_id, synthetic))
    takeaway = "分析で見つけた差分を、自分の評価条件で一つずつ検証する。"
    if not cards:
        takeaway = "解法カードを追加し、比較できる根拠を揃える。"
    next_evidence = [_evidence(f"検証候補: {row.name}（判定: {_VERDICT[row.verdict]}）", "inferred", "analysis") for row in gaps]
    slides.append(_slide(
        "next", "次に検証すること", takeaway,
        next_evidence or [_evidence("現時点の記録から検証候補を絞れない", "unknown", "analysis")],
        "採用はまだ決めない。自陣での使用や過去の実験が不明なら記録を確認し、"
        "次の実験で一度に変える要素と評価方法を決める。", "検証候補と、追加で確認する記録を短く並べる。",
    ))
    budget = minutes * 60 * 9 // 10  # Leave 10% for transitions and pauses.
    weights = [1 if slide["id"] == "scope" else 2 if slide["id"] in {"position", "shared", "next"} else 3 for slide in slides]
    total_weight = sum(weights)
    for slide, weight in zip(slides, weights, strict=True):
        slide["seconds"] = max(1, budget * weight // total_weight)
    slides[-1]["seconds"] += budget - sum(slide["seconds"] for slide in slides)
    deck = {
        "schema_version": "1.0", "kind": "kaggle", "title": f"{d.name} ソリューション分析 LT" + ("（合成データ例）" if synthetic else ""),
        "language": "ja", "audience": audience.strip(), "duration_minutes": minutes,
        "takeaway": takeaway, "sources": sources, "slides": slides,
    }
    return deck, payload


def build_deck(comp_dir: Path, minutes: int = 5, audience: str = DEFAULT_AUDIENCE, top_n: int = 20) -> dict:
    """ディスクに書かず、LT 原稿を作る。"""
    return _bundle(comp_dir.resolve(), minutes, audience, top_n)[0]


def write(comp_dir: Path, *, minutes: int = 5, audience: str = DEFAULT_AUDIENCE,
          output: Path | None = None, force: bool = False, top_n: int = 20) -> Path:
    """自己完結した bundle を書く。force でも生成対象以外のファイルは触らない。"""
    comp_dir = comp_dir.resolve()
    destination = output if output is not None else comp_dir / "lt"
    if destination.is_symlink():
        raise ValueError("出力先にシンボリックリンクは指定できません")
    destination = destination.resolve()
    if _within(comp_dir, destination) or any(_within(destination, comp_dir / folder) for folder in ("own", "solutions")):
        raise ValueError("出力先が元の記録と重なります。別のフォルダを指定してください")
    if destination.exists() and (not destination.is_dir() or (any(destination.iterdir()) and not force)):
        raise FileExistsError(f"出力先が既に存在します: {destination}。別の --output または --force を指定してください")
    deck, payload = _bundle(comp_dir, minutes, audience, top_n)
    payload["deck.json"] = (json.dumps(deck, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    # Preflight every generated target before starting to write.
    for relative in payload:
        target = destination / relative
        if not _within(target, destination):
            raise ValueError(f"出力が指定フォルダの外を指しています: {target}")
        if target.exists() and not target.is_file():
            raise ValueError(f"出力ファイルと同名のフォルダがあります: {target}")
    for relative, data in payload.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        # Replace files atomically, so an existing hard link is not modified in place.
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(data)
        try:
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    return destination / "deck.json"
