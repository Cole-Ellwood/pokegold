from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError

from .rom_scenarios import select_from_score_bytes


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MOVE_CONSTANTS_PATH = ROOT / "constants" / "move_constants.asm"
CAPTURE_SEPARATOR = "---"
TOP_MOVE_RE = re.compile(r"^(?P<name>[^:]+):(?P<score>\d+)$")


@dataclass(frozen=True)
class TraceReplayVerdict:
    capture_id: str
    path: str
    mode: str
    verdict: str
    match: bool
    reason: str
    chosen_id: int
    expected_move_ids: list[int]
    selector: dict[str, Any]


def load_move_names(path: Path = DEFAULT_MOVE_CONSTANTS_PATH) -> dict[int, str]:
    if not path.exists():
        return {}
    names: dict[int, str] = {}
    index = 0
    in_table = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split(";", 1)[0].strip()
        if line == "const_def":
            in_table = True
            index = 0
            continue
        if not in_table:
            continue
        if line.startswith("DEF NUM_ATTACKS"):
            break
        if not line.startswith("const "):
            continue
        parts = line.split()
        if len(parts) >= 2:
            names[index] = parts[1]
            index += 1
    return names


def parse_trace_file(path: Path) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line == CAPTURE_SEPARATOR:
            if current:
                blocks.append(current)
                current = {}
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        current[key.strip()] = value.strip()
    if current:
        blocks.append(current)
    return blocks


def collect_trace_paths(
    *,
    traces: list[Path] | None = None,
    trace_dir: Path | None = None,
    pattern: str = "*_live.txt",
) -> list[Path]:
    paths: list[Path] = []
    if traces:
        paths.extend(traces)
    if trace_dir is not None:
        paths.extend(sorted(trace_dir.glob(pattern)))
    if not paths:
        raise PreferenceDataError("provide --trace or --trace-dir")
    missing = [path for path in paths if not path.exists()]
    if missing:
        raise PreferenceDataError(
            "missing trace file(s): " + ", ".join(str(path) for path in missing)
        )
    return paths


def replay_trace_paths(
    paths: list[Path],
    *,
    move_names: dict[int, str] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    names = move_names if move_names is not None else load_move_names()
    verdicts: list[TraceReplayVerdict] = []
    for path in paths:
        for index, fields in enumerate(parse_trace_file(path), start=1):
            capture_id = capture_id_for(path, fields, index)
            verdicts.append(replay_capture_fields(fields, capture_id, path, names))

    elapsed = time.perf_counter() - started
    checked = [item for item in verdicts if item.verdict != "no_decision"]
    exact = [item for item in checked if item.mode == "exact"]
    partial = [item for item in checked if item.mode == "partial_top3"]
    matched = [item for item in checked if item.match]
    exact_matched = [item for item in exact if item.match]
    partial_matched = [item for item in partial if item.match]
    failures = [item for item in checked if not item.match]
    verdict_counts: dict[str, int] = {}
    for item in verdicts:
        verdict_counts[item.verdict] = verdict_counts.get(item.verdict, 0) + 1

    return {
        "trace_count": len(paths),
        "capture_count": len(verdicts),
        "checked_count": len(checked),
        "match_count": len(matched),
        "agreement_rate": ratio(len(matched), len(checked)),
        "exact_count": len(exact),
        "exact_match_count": len(exact_matched),
        "exact_agreement_rate": ratio(len(exact_matched), len(exact)),
        "partial_count": len(partial),
        "partial_match_count": len(partial_matched),
        "partial_agreement_rate": ratio(len(partial_matched), len(partial)),
        "failure_count": len(failures),
        "elapsed_seconds": elapsed,
        "captures_per_minute": len(verdicts) / elapsed * 60 if elapsed > 0 else 0,
        "verdict_counts": dict(sorted(verdict_counts.items())),
        "verdicts": [trace_verdict_to_json(item) for item in verdicts],
    }


def capture_id_for(path: Path, fields: dict[str, str], index: int) -> str:
    boss = fields.get("boss", path.stem)
    capture_index = fields.get("capture_index", str(index))
    return f"{boss}#{capture_index}"


def replay_capture_fields(
    fields: dict[str, str],
    capture_id: str,
    path: Path,
    move_names: dict[int, str],
) -> TraceReplayVerdict:
    chosen_id = parse_int(fields.get("chosen_id", "0"))
    current_move_id = parse_int(fields.get("cur_enemy_move_id", "0"))
    if chosen_id == 0 and current_move_id != 0 and has_exact_selector_fields(fields):
        chosen_id = current_move_id
    if chosen_id == 0:
        return TraceReplayVerdict(
            capture_id=capture_id,
            path=str(path),
            mode="none",
            verdict="no_decision",
            match=True,
            reason="trace has no chosen move",
            chosen_id=0,
            expected_move_ids=[],
            selector={},
        )

    if has_exact_selector_fields(fields):
        return replay_exact_capture(fields, capture_id, path, move_names, chosen_id)
    return replay_partial_top3_capture(fields, capture_id, path, move_names, chosen_id)


def replay_exact_capture(
    fields: dict[str, str],
    capture_id: str,
    path: Path,
    move_names: dict[int, str],
    chosen_id: int,
) -> TraceReplayVerdict:
    selector = select_from_score_bytes(
        scenario_id=capture_id,
        tier=parse_int(fields["tier"]),
        move_ids=parse_int_list(fields["move_ids"]),
        scores=parse_int_list(fields["move_scores"]),
        move_names=move_names,
    )
    if not selector.get("ready"):
        match = False
        reason = str(selector.get("reason", "selector did not choose"))
        expected = []
    else:
        expected = [int(item) for item in selector["possible_move_ids"]]
        chosen_slot = optional_int(fields.get("chosen_slot"))
        if chosen_slot is None:
            match = chosen_id in expected
            reason = (
                "chosen move id has nonzero selector probability"
                if match
                else "chosen move id is outside selector's possible best/second set"
            )
        else:
            possible_slots = [int(item) for item in selector["possible_slot_indices"]]
            slot_matches = False
            slots = selector.get("slots", [])
            if 0 <= chosen_slot < len(slots):
                slot_matches = int(slots[chosen_slot]["move_id"]) == chosen_id
            match = chosen_slot in possible_slots and slot_matches
            reason = (
                "chosen slot has nonzero selector probability"
                if match
                else "chosen slot is outside selector's possible best/second slots"
            )

    return TraceReplayVerdict(
        capture_id=capture_id,
        path=str(path),
        mode="exact",
        verdict="match" if match else "mismatch",
        match=match,
        reason=reason,
        chosen_id=chosen_id,
        expected_move_ids=expected,
        selector=selector,
    )


def replay_partial_top3_capture(
    fields: dict[str, str],
    capture_id: str,
    path: Path,
    move_names: dict[int, str],
    chosen_id: int,
) -> TraceReplayVerdict:
    top_moves = parse_top_moves(fields.get("top_moves", ""), move_names)
    expected = [move["move_id"] for move in top_moves[:2]]
    match = chosen_id in expected
    return TraceReplayVerdict(
        capture_id=capture_id,
        path=str(path),
        mode="partial_top3",
        verdict="match" if match else "mismatch",
        match=match,
        reason=(
            "chosen move id appears in top-two trace candidates"
            if match
            else "chosen move id is outside top-two trace candidates"
        ),
        chosen_id=chosen_id,
        expected_move_ids=expected,
        selector={"top_moves": top_moves},
    )


def has_exact_selector_fields(fields: dict[str, str]) -> bool:
    return all(key in fields for key in ("tier", "move_ids", "move_scores"))


def parse_top_moves(value: str, move_names: dict[int, str]) -> list[dict[str, Any]]:
    name_to_id = {name: move_id for move_id, name in move_names.items()}
    result: list[dict[str, Any]] = []
    if not value:
        return result
    for raw_part in value.split(","):
        part = raw_part.strip()
        if not part:
            continue
        match = TOP_MOVE_RE.match(part)
        if match is None:
            raise PreferenceDataError(f"invalid top_moves entry: {part!r}")
        name = match.group("name")
        move_id = name_to_id.get(name, 0)
        result.append(
            {
                "move_id": move_id,
                "name": name,
                "score": int(match.group("score")),
            }
        )
    return result


def parse_int_list(value: str) -> list[int]:
    if not value:
        return []
    return [parse_int(part.strip()) for part in value.split(",") if part.strip()]


def parse_int(value: str) -> int:
    return int(value, 0)


def optional_int(value: str | None) -> int | None:
    if value in {None, ""}:
        return None
    return parse_int(str(value))


def ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def trace_verdict_to_json(verdict: TraceReplayVerdict) -> dict[str, Any]:
    return {
        "capture_id": verdict.capture_id,
        "path": verdict.path,
        "mode": verdict.mode,
        "verdict": verdict.verdict,
        "match": verdict.match,
        "reason": verdict.reason,
        "chosen_id": verdict.chosen_id,
        "expected_move_ids": verdict.expected_move_ids,
        "selector": verdict.selector,
    }


def format_trace_replay_report(report: dict[str, Any], *, limit: int = 20) -> str:
    lines = [
        "Boss AI trace selector replay",
        (
            f"captures={report['capture_count']} checked={report['checked_count']} "
            f"matches={report['match_count']} failures={report['failure_count']} "
            f"agreement={report['agreement_rate']:.4%}"
        ),
        (
            f"exact={report['exact_match_count']}/{report['exact_count']} "
            f"({report['exact_agreement_rate']:.4%}) "
            f"partial={report['partial_match_count']}/{report['partial_count']} "
            f"({report['partial_agreement_rate']:.4%})"
        ),
    ]
    counts = " ".join(
        f"{verdict}={count}" for verdict, count in report["verdict_counts"].items()
    )
    lines.append(f"verdicts: {counts or 'none'}")

    failures = [
        item for item in report["verdicts"] if item["verdict"] == "mismatch"
    ][:limit]
    if failures:
        lines.append("")
        lines.append(f"Top {limit} mismatches:")
        for item in failures:
            lines.append(
                f"  {item['capture_id']} mode={item['mode']} "
                f"chosen={item['chosen_id']} expected={item['expected_move_ids']}"
            )
            lines.append(f"      {item['reason']}")
    return "\n".join(lines)


def write_trace_replay_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
