"""Tests that verify_loop_state.py enforces the investigation block on miss
cases (per the iter 9 user-flagged design upgrade).

These tests monkeypatch the verifier's LIB constant to point at a tmp
case_library and call the check function directly. No subprocess
(Windows handle inheritance breaks under nested subprocess.run).
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.pokemon_mastery import verify_loop_state as vls


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


def run_check(lib: Path, monkeypatch) -> list[str]:
    monkeypatch.setattr(vls, "LIB", lib)
    errors: list[str] = []
    vls.check(errors)
    return errors


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


def test_miss_case_without_investigation_fails(tmp_path, monkeypatch):
    lib = write_lib(tmp_path, [good_replay()], [base_case("c1", "missed_class")])
    errors = run_check(lib, monkeypatch)
    assert any("investigation" in e.lower() for e in errors), errors


def test_miss_case_with_investigation_passes(tmp_path, monkeypatch):
    inv = {"root_cause_hypothesis": "x", "future_turn_evidence": "turn 5: x", "confidence": "high"}
    lib = write_lib(tmp_path, [good_replay()], [base_case("c1", "missed_class", investigation=inv)])
    errors = run_check(lib, monkeypatch)
    assert errors == [], errors


def test_bootstrap_miss_grandfathered(tmp_path, monkeypatch):
    lib = write_lib(tmp_path, [good_replay()], [base_case("c1", "missed_class", bootstrap=True)])
    errors = run_check(lib, monkeypatch)
    assert errors == [], errors


def test_hit_top_case_does_not_require_investigation(tmp_path, monkeypatch):
    lib = write_lib(tmp_path, [good_replay()], [base_case("c1", "hit_top")])
    errors = run_check(lib, monkeypatch)
    assert errors == [], errors


def test_invalid_confidence_value_fails(tmp_path, monkeypatch):
    inv = {"root_cause_hypothesis": "x", "future_turn_evidence": "x", "confidence": "definitely"}
    lib = write_lib(tmp_path, [good_replay()], [base_case("c1", "missed_class", investigation=inv)])
    errors = run_check(lib, monkeypatch)
    assert any("confidence" in e.lower() for e in errors), errors


def test_partial_investigation_block_fails(tmp_path, monkeypatch):
    inv = {"root_cause_hypothesis": "x"}  # missing future_turn_evidence + confidence
    lib = write_lib(tmp_path, [good_replay()], [base_case("c1", "missed_class", investigation=inv)])
    errors = run_check(lib, monkeypatch)
    assert any("investigation" in e.lower() for e in errors), errors
