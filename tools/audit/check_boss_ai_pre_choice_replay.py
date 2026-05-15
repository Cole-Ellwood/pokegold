#!/usr/bin/env python3
"""Replay manifest pre-choice states through the ROM boss move-choice path."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_debugger.trace_replay import parse_trace_file, replay_trace_paths
from tools.trace.runtime import sha256_file


MANIFEST = ROOT / "audit" / "boss_ai_trace" / "live_capture_manifest.json"
STATE_REPLAY = ROOT / "tools" / "trace" / "boss_ai_state_replay.py"
MIN_EXACT_CAPTURES = 18
MIN_AGREEMENT = 0.9999
BASELINE_FIELD_KEYS = (
    "trace_rom",
    "trace_rom_sha256",
    "trace_symbols",
    "trace_symbols_sha256",
    "boss",
    "tier",
    "move_ids",
    "move_scores",
    "chosen_slot",
    "cur_enemy_move_id",
    "top_moves",
    "chosen",
    "chosen_id",
    "switch_confidence",
    "plan_id",
    "plan_phase",
    "plan_confidence",
    "plausible_mask",
    "risk_flags",
    "lookahead_bonus_top",
    "revealed_masks",
    "switch_context",
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def rel_or_abs(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail("manifest root must be an object")
    if not isinstance(data.get("captures"), list):
        fail("manifest must contain captures list")
    return data


def validate_hashes(manifest: dict[str, Any]) -> tuple[Path, Path]:
    trace_rom = manifest.get("trace_rom")
    trace_symbols = manifest.get("trace_symbols")
    rom_hash = manifest.get("trace_rom_sha256")
    symbols_hash = manifest.get("trace_symbols_sha256")
    if not all(isinstance(value, str) and value for value in (trace_rom, trace_symbols)):
        fail("manifest must pin trace_rom and trace_symbols")
    if not all(isinstance(value, str) and value for value in (rom_hash, symbols_hash)):
        fail("manifest must pin trace_rom_sha256 and trace_symbols_sha256")

    rom_path = rel_or_abs(str(trace_rom))
    symbols_path = rel_or_abs(str(trace_symbols))
    actual_rom_hash = sha256_file(rom_path)
    actual_symbols_hash = sha256_file(symbols_path)
    if actual_rom_hash.upper() != str(rom_hash).upper():
        fail(
            "manifest trace_rom hash mismatch: "
            f"expected {str(rom_hash).upper()}, found {actual_rom_hash}"
        )
    if actual_symbols_hash.upper() != str(symbols_hash).upper():
        fail(
            "manifest trace_symbols hash mismatch: "
            f"expected {str(symbols_hash).upper()}, found {actual_symbols_hash}"
        )
    return rom_path, symbols_path


def move_choice_entries(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    entries = []
    for raw in manifest["captures"]:
        if not isinstance(raw, dict):
            continue
        if raw.get("id") == "shared_switch_loop":
            continue
        entries.append(raw)
    return entries


def replay_entry(
    entry: dict[str, Any],
    rom_path: Path,
    symbols_path: Path,
    out_dir: Path,
) -> Path:
    capture_id = entry.get("id")
    if not isinstance(capture_id, str) or not capture_id:
        fail("capture entry missing id")
    pre_choice_state = entry.get("pre_choice_state")
    if not isinstance(pre_choice_state, str) or not pre_choice_state:
        fail(f"{capture_id}: missing pre_choice_state")
    choice_button = entry.get("choice_button", "a")
    if not isinstance(choice_button, str) or not choice_button:
        fail(f"{capture_id}: choice_button must be a string")
    choice_wait_frames = entry.get("choice_wait_frames")
    if not isinstance(choice_wait_frames, int) or choice_wait_frames < 0:
        fail(f"{capture_id}: missing non-negative choice_wait_frames")

    state_path = rel_or_abs(pre_choice_state)
    if not state_path.exists():
        fail(f"{capture_id}: missing pre-choice state {state_path}")
    out_path = out_dir / f"{capture_id}_pre_choice_replay.txt"
    cmd = [
        sys.executable,
        str(STATE_REPLAY),
        "--save-state",
        str(state_path),
        "--button",
        choice_button,
        "--watch-frames",
        str(choice_wait_frames),
        "--boss",
        str(entry.get("boss", capture_id)),
        "--notes",
        "pre-choice replay audit",
        "--out",
        str(out_path),
        "--rom",
        str(rom_path),
        "--symbols",
        str(symbols_path),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)
    return out_path


def read_single_trace(path: Path, capture_id: str) -> dict[str, str]:
    if not path.exists():
        fail(f"{capture_id}: missing baseline trace {path}")
    blocks = parse_trace_file(path)
    if len(blocks) != 1:
        fail(f"{capture_id}: expected exactly one trace block in {path}, found {len(blocks)}")
    return blocks[0]


def compare_replay_to_baseline(entry: dict[str, Any], replay_path: Path) -> None:
    capture_id = str(entry["id"])
    baseline_path_text = entry.get("out")
    if not isinstance(baseline_path_text, str) or not baseline_path_text:
        fail(f"{capture_id}: missing baseline trace path")

    baseline = read_single_trace(rel_or_abs(baseline_path_text), capture_id)
    replay = read_single_trace(replay_path, capture_id)
    mismatches: list[str] = []
    for key in BASELINE_FIELD_KEYS:
        baseline_value = baseline.get(key, "")
        replay_value = replay.get(key, "")
        if baseline_value != replay_value:
            mismatches.append(f"{key}: baseline {baseline_value!r}, replay {replay_value!r}")

    if mismatches:
        detail = "; ".join(mismatches[:5])
        remaining = len(mismatches) - 5
        if remaining > 0:
            detail += f"; ... {remaining} more"
        fail(f"{capture_id}: pre-choice replay differs from baseline trace: {detail}")


def main() -> int:
    manifest = load_manifest(MANIFEST)
    rom_path, symbols_path = validate_hashes(manifest)
    entries = move_choice_entries(manifest)
    if len(entries) < MIN_EXACT_CAPTURES:
        fail(f"only {len(entries)} move-choice entries; expected at least {MIN_EXACT_CAPTURES}")

    with tempfile.TemporaryDirectory(prefix="boss_pre_choice_replay_") as tmp:
        out_dir = Path(tmp)
        trace_paths = [
            replay_entry(entry, rom_path, symbols_path, out_dir)
            for entry in entries
        ]
        for entry, trace_path in zip(entries, trace_paths, strict=True):
            compare_replay_to_baseline(entry, trace_path)
        report = replay_trace_paths(trace_paths)

    if report["capture_count"] != len(entries):
        fail(
            f"expected one replay capture for each manifest entry; "
            f"got {report['capture_count']} captures for {len(entries)} entries"
        )
    if report["checked_count"] != report["capture_count"]:
        missing = report["capture_count"] - report["checked_count"]
        fail(f"{missing} pre-choice replay capture(s) had no replayable decision")
    if report["failure_count"]:
        fail(f"{report['failure_count']} pre-choice replay mismatch(es)")
    if report["partial_count"]:
        fail(f"{report['partial_count']} pre-choice replay capture(s) were partial")
    if report["exact_count"] != len(entries):
        fail(
            f"only {report['exact_count']} of {len(entries)} pre-choice captures "
            "had exact score-byte evidence"
        )
    if report["exact_count"] < MIN_EXACT_CAPTURES:
        fail(
            f"only {report['exact_count']} exact pre-choice captures; "
            f"expected at least {MIN_EXACT_CAPTURES}"
        )
    if report["exact_agreement_rate"] < MIN_AGREEMENT:
        fail(
            f"pre-choice replay agreement {report['exact_agreement_rate']:.4%} "
            f"is below {MIN_AGREEMENT:.4%}"
        )

    print(
        "Boss AI pre-choice replay audit passed: "
        f"{report['exact_match_count']} / {report['exact_count']} exact captures "
        f"matched ({report['exact_agreement_rate']:.4%})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
