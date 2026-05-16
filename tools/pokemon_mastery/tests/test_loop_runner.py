from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.pokemon_mastery import loop_runner as lr


@pytest.fixture
def isolated_lib(tmp_path: Path, monkeypatch):
    lib = tmp_path / "case_library"
    lib.mkdir()
    state = {
        "iteration_count": 0,
        "last_iteration_phase": None,
        "last_iteration_replay_id": None,
        "ingest_cadence_validate": 5,
        "consolidate_cadence_iterations": 20,
        "gate_target": {"label": "stretch"},
    }
    (lib / "loop_state.json").write_text(json.dumps(state), encoding="utf-8")
    (lib / "cases.jsonl").write_text("", encoding="utf-8")
    (lib / "replay_index.jsonl").write_text("", encoding="utf-8")
    (lib / "metrics.jsonl").write_text("", encoding="utf-8")
    monkeypatch.setattr(lr, "LIB", lib)
    monkeypatch.setattr(lr, "STATE_PATH", lib / "loop_state.json")
    monkeypatch.setattr(lr, "CASES_PATH", lib / "cases.jsonl")
    monkeypatch.setattr(lr, "REPLAY_INDEX_PATH", lib / "replay_index.jsonl")
    monkeypatch.setattr(lr, "METRICS_PATH", lib / "metrics.jsonl")
    return lib


def good_case(case_id="c1", tier="study", replay_id="gen2ou-1"):
    return {
        "case_id": case_id,
        "replay_id": replay_id,
        "turn": 1,
        "side": "p1",
        "tier": tier,
        "fingerprint": {
            "active_user": {"species": "Snorlax"},
            "active_opp": {"species": "Cloyster"},
            "turn_bucket": "mid",
        },
        "pro_action": {"type": "move", "move": "Body Slam"},
        "pro_reasoning_class": "converter",
        "created_at": "x",
    }


def good_replay(replay_id="gen2ou-1", tier="study"):
    return {
        "replay_id": replay_id,
        "tier": tier,
        "rating": 1500,
        "uploadtime": 111,
        "fetched_at": "x",
    }


def good_metrics(tier="validation"):
    return {
        "window_id": "w1",
        "computed_at": "x",
        "tier": tier,
        "decision_count": 5,
    }


def test_suggest_phase_empty_state_says_ingest(isolated_lib):
    assert lr.suggest_next_phase(lr.load_state()) == "INGEST"


def test_suggest_phase_after_5_study_ingests_says_validate(isolated_lib):
    for i in range(5):
        lr.append_replay(good_replay(replay_id=f"gen2ou-{i}"))
    assert lr.suggest_next_phase(lr.load_state()) == "VALIDATE"


def test_suggest_phase_resets_after_validation(isolated_lib):
    for i in range(5):
        lr.append_replay(good_replay(replay_id=f"gen2ou-s{i}"))
    lr.append_replay(good_replay(replay_id="gen2ou-v0", tier="validation"))
    assert lr.suggest_next_phase(lr.load_state()) == "INGEST"


def test_append_case_rejects_non_study_tier(isolated_lib):
    lr.append_replay(good_replay(replay_id="gen2ou-v", tier="validation"))
    with pytest.raises(ValueError, match="tier must be 'study'"):
        lr.append_case(good_case(replay_id="gen2ou-v", tier="validation"))


def test_append_case_rejects_unknown_replay_id(isolated_lib):
    with pytest.raises(ValueError, match="not in replay_index"):
        lr.append_case(good_case(replay_id="gen2ou-missing"))


def test_append_case_happy_path(isolated_lib):
    lr.append_replay(good_replay())
    lr.append_case(good_case())
    assert isolated_lib.joinpath("cases.jsonl").read_text(encoding="utf-8").count("\n") == 1


def test_append_case_missing_required_field(isolated_lib):
    lr.append_replay(good_replay())
    case = good_case()
    del case["pro_action"]
    with pytest.raises(ValueError, match="missing required field"):
        lr.append_case(case)


def test_append_replay_dedupes(isolated_lib):
    lr.append_replay(good_replay())
    with pytest.raises(ValueError, match="already in"):
        lr.append_replay(good_replay())


def test_append_replay_rejects_bad_tier(isolated_lib):
    row = good_replay()
    row["tier"] = "garbage"
    with pytest.raises(ValueError, match="invalid tier"):
        lr.append_replay(row)


def test_append_metrics_rejects_bad_tier(isolated_lib):
    row = good_metrics()
    row["tier"] = "garbage"
    with pytest.raises(ValueError, match="invalid tier"):
        lr.append_metrics(row)


def test_append_metrics_accepts_validation_row(isolated_lib):
    lr.append_metrics(good_metrics())
    assert isolated_lib.joinpath("metrics.jsonl").read_text(encoding="utf-8").strip()


def test_bump_iteration_increments(isolated_lib):
    state1 = lr.bump_iteration("INGEST", "gen2ou-1")
    assert state1["iteration_count"] == 1
    assert state1["last_iteration_phase"] == "INGEST"
    assert state1["last_iteration_replay_id"] == "gen2ou-1"
    state2 = lr.bump_iteration("DIAGNOSE", None)
    assert state2["iteration_count"] == 2
    assert state2["last_iteration_phase"] == "DIAGNOSE"


def test_bump_iteration_rejects_unknown_phase(isolated_lib):
    with pytest.raises(ValueError, match="unknown phase"):
        lr.bump_iteration("garbage", None)


def test_commit_message_format(isolated_lib):
    lr.bump_iteration("INGEST", "gen2ou-1")
    msg = lr.commit_message("INGEST", "gen2ou-1")
    assert msg == "pokemon-mastery-loop: iter 1 INGEST gen2ou-1"


def test_commit_message_na_for_no_replay(isolated_lib):
    lr.bump_iteration("CONSOLIDATE", None)
    msg = lr.commit_message("CONSOLIDATE", None)
    assert msg == "pokemon-mastery-loop: iter 1 CONSOLIDATE na"


def test_status_report_fields(isolated_lib):
    lr.append_replay(good_replay())
    lr.append_case(good_case())
    lr.bump_iteration("INGEST", "gen2ou-1")
    report = lr.status_report()
    assert report["iteration_count"] == 1
    assert report["last_iteration_phase"] == "INGEST"
    assert report["replays_indexed"] == 1
    assert report["cases_stored"] == 1
    assert report["suggested_next_phase"] in {"INGEST", "VALIDATE", "CONSOLIDATE"}
