#!/usr/bin/env python3
"""Replay manifest pre-choice states through the ROM boss move-choice path."""

from __future__ import annotations

import json
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = Path(__file__).resolve().parent
if str(AUDIT_DIR) not in sys.path:
    sys.path.insert(0, str(AUDIT_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _common import fail
from tools.boss_ai_debugger.trace_replay import parse_trace_file, replay_trace_paths
from tools.debugger.report_envelope import build_report_envelope
from tools.trace.runtime import sha256_file

from _trace_artifacts import require_manifest_basis


MANIFEST = ROOT / "audit" / "boss_ai_trace" / "live_capture_manifest.json"
STATE_REPLAY = ROOT / "tools" / "trace" / "boss_ai_state_replay.py"
PRE_CHOICE_REPLAY_EVIDENCE_ID = "boss_ai_pre_choice_replay.exact_match_corpus"
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
    "pre_model_scores",
    "post_model_scores",
    "model_score_deltas",
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


def repo_rel(path: Path, *, root: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def build_audit_report(
    *,
    manifest: dict[str, Any],
    entries: list[dict[str, Any]],
    replay_report: dict[str, Any],
    rom_path: Path,
    symbols_path: Path,
    manifest_path: Path = MANIFEST,
    root: Path = ROOT,
) -> dict[str, Any]:
    capture_ids = [str(entry.get("id", "")) for entry in entries]
    manifest_hash = sha256_file(manifest_path)
    report = build_report_envelope(
        kind="boss_ai_pre_choice_replay_audit",
        command="python tools\\audit\\check_boss_ai_pre_choice_replay.py",
        inputs={"manifest": repo_rel(manifest_path, root=root)},
        rom_path=rom_path,
        symbols_path=symbols_path,
        state_basis={
            "manifest_path": repo_rel(manifest_path, root=root),
            "manifest_sha256": manifest_hash,
            "capture_ids": capture_ids,
            "minimum_exact_captures": MIN_EXACT_CAPTURES,
            "minimum_agreement": MIN_AGREEMENT,
            "trace_rom": str(manifest.get("trace_rom", "")),
            "trace_symbols": str(manifest.get("trace_symbols", "")),
        },
        backend="pyboy_trace_replay",
        proof_status="complete",
        closed_evidence_ids=[PRE_CHOICE_REPLAY_EVIDENCE_ID],
        repro_command=(
            "python tools\\audit\\check_boss_ai_pre_choice_replay.py "
            "--json-out audit\\boss_ai_debugger\\god_level_benchmark\\artifacts\\pre_choice_replay.json"
        ),
        disproof_standard=[
            "Every manifest move-choice capture replays from its pre-choice state.",
            "Each replay matches the recorded baseline trace fields and exact score-byte evidence.",
            "The artifact manifest hash and trace ROM/symbol hashes match the current live capture manifest.",
        ],
        root=root,
    )
    report.update(
        {
            "manifest_path": repo_rel(manifest_path, root=root),
            "manifest_sha256": manifest_hash,
            "baseline_field_keys": list(BASELINE_FIELD_KEYS),
            "excluded_capture_ids": [
                {
                    "id": "shared_switch_loop",
                    "reason": "shared switch-loop capture does not exercise the move-choice replay path",
                }
            ],
            "minimum_exact_captures": MIN_EXACT_CAPTURES,
            "minimum_agreement": MIN_AGREEMENT,
            "capture_ids": capture_ids,
            "capture_count": int(replay_report.get("capture_count", 0) or 0),
            "checked_count": int(replay_report.get("checked_count", 0) or 0),
            "failure_count": int(replay_report.get("failure_count", 0) or 0),
            "partial_count": int(replay_report.get("partial_count", 0) or 0),
            "exact_count": int(replay_report.get("exact_count", 0) or 0),
            "exact_match_count": int(replay_report.get("exact_match_count", 0) or 0),
            "exact_agreement_rate": float(replay_report.get("exact_agreement_rate", 0.0) or 0.0),
            "verdict_counts": dict(replay_report.get("verdict_counts", {})),
            "trace_rom_sha256": str(manifest.get("trace_rom_sha256", "")),
            "trace_symbols_sha256": str(manifest.get("trace_symbols_sha256", "")),
        }
    )
    return report


def write_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, help="write a complete proof envelope when the audit passes")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    require_manifest_basis()
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

    audit_report = build_audit_report(
        manifest=manifest,
        entries=entries,
        replay_report=report,
        rom_path=rom_path,
        symbols_path=symbols_path,
    )
    if args.json_out is not None:
        write_report(audit_report, args.json_out)
    print(
        "Boss AI pre-choice replay audit passed: "
        f"{report['exact_match_count']} / {report['exact_count']} exact captures "
        f"matched ({report['exact_agreement_rate']:.4%})."
    )
    if args.json_out is not None:
        print(f"json_out={args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
