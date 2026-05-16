"""Tests that verify_loop_state.py enforces the investigation block on miss
cases (per the iter 9 user-flagged design upgrade).

These tests build a tiny fake case_library directory and run the verifier
via subprocess, checking the actual exit code + stderr.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

VERIFIER = Path(__file__).resolve().parents[1] / "verify_loop_state.py"


def write_lib(tmp: Path, replays: list[dict], cases: list[dict]) -> Path:
    lib = tmp / "case_library"
    lib.mkdir()
    (lib / "loop_state.json").write_text(
        json.dumps({
            "gate_target": {"top_match_min": 0.6, "case_breadth_min": 150},
            "ingest_cadence_validate": 5,
            "ema_alpha": 0.3,
            "ema_window_size": 10,
        }),
        encoding="utf-8",
    )
    with (lib / "replay_index.jsonl").open("w", encoding="utf-8") as f:
        for r in replays:
            f.write(json.dumps(r) + "\n")
    with (lib / "cases.jsonl").open("w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c) + "\n")
    (lib / "metrics.jsonl").write_text("", encoding="utf-8")
    return lib


def run_verifier(lib: Path) -> subprocess.CompletedProcess:
    # The verifier resolves its own LIB path from its own __file__; copy the
    # verifier into the tmp dir so it points at our fake lib.
    copy = lib.parent / "verify_loop_state.py"
    copy.write_bytes(VERIFIER.read_bytes())
    return subprocess.run(
        [sys.executable, str(copy)],
        capture_output=True,
        text=True,
    )


def good_replay():
    return {"replay_id": "gen2ou-1", "tier": "study", "rating": 1500, "uploadtime": 1, "fetched_at": "x"}


def base_case(case_id: str, failure_mode: str, *, bootstrap: bool = False, investigation: dict | None = None):
    case = {
        "case_id": case_id,
        "replay_id": "gen2ou-1",
        "turn": 1,
        "side": "p1",
        "tier": "study",
        "fingerprint": {
            "active_user": {"species": "Snorlax", "hp_bucket": "100%"},
            "active_opp": {"species": "Blissey", "hp_bucket": "100%"},
            "turn_bucket": "t1",
        },
        "pro_action": {"type": "switch", "switch_to": "Rhydon"},
        "pro_reasoning_class": "converter",
        "failure_mode": failure_mode,
        "created_at": "x",
    }
    if bootstrap:
        case["bootstrap_iteration"] = True
    if investigation:
        case["investigation"] = investigation
    return case


def test_miss_case_without_investigation_fails(tmp_path):
    lib = write_lib(
        tmp_path,
        replays=[good_replay()],
        cases=[base_case("c1", "missed_class")],
    )
    result = run_verifier(lib)
    assert result.returncode == 1
    assert "investigation" in (result.stdout + result.stderr).lower()


def test_miss_case_with_investigation_passes(tmp_path):
    inv = {
        "root_cause_hypothesis": "test",
        "future_turn_evidence": "turn 5: x happened",
        "confidence": "high",
    }
    lib = write_lib(
        tmp_path,
        replays=[good_replay()],
        cases=[base_case("c1", "missed_class", investigation=inv)],
    )
    result = run_verifier(lib)
    assert result.returncode == 0, result.stderr


def test_bootstrap_miss_grandfathered(tmp_path):
    lib = write_lib(
        tmp_path,
        replays=[good_replay()],
        cases=[base_case("c1", "missed_class", bootstrap=True)],
    )
    result = run_verifier(lib)
    assert result.returncode == 0


def test_hit_top_case_does_not_require_investigation(tmp_path):
    lib = write_lib(
        tmp_path,
        replays=[good_replay()],
        cases=[base_case("c1", "hit_top")],
    )
    result = run_verifier(lib)
    assert result.returncode == 0


def test_invalid_confidence_value_fails(tmp_path):
    inv = {
        "root_cause_hypothesis": "x",
        "future_turn_evidence": "x",
        "confidence": "definitely",
    }
    lib = write_lib(
        tmp_path,
        replays=[good_replay()],
        cases=[base_case("c1", "missed_class", investigation=inv)],
    )
    result = run_verifier(lib)
    assert result.returncode == 1
    assert "confidence" in (result.stdout + result.stderr).lower()


def test_partial_investigation_block_fails(tmp_path):
    inv = {"root_cause_hypothesis": "x"}  # missing future_turn_evidence + confidence
    lib = write_lib(
        tmp_path,
        replays=[good_replay()],
        cases=[base_case("c1", "missed_class", investigation=inv)],
    )
    result = run_verifier(lib)
    assert result.returncode == 1
    assert "investigation" in (result.stdout + result.stderr).lower()
