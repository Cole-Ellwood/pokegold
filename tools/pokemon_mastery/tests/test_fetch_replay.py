from __future__ import annotations

import json
from pathlib import Path

from tools.pokemon_mastery import fetch_replay


def write_index(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_assign_tier_below_study_floor_skips():
    assert fetch_replay.assign_tier(1399, []) is None


def test_assign_tier_first_study_at_floor():
    assert fetch_replay.assign_tier(1400, []) == "study"


def test_assign_tier_validation_floor_requires_1600():
    rows = [
        {"replay_id": f"x{i}", "tier": "study", "rating": 1500}
        for i in range(4)
    ]
    # rating 1500 cannot land in validation even though the partition would allow it.
    assert fetch_replay.assign_tier(1500, rows) == "study"


def test_assign_tier_4_to_1_ratio():
    # Four studies, zero validations, candidate >=1600 should go to validation.
    rows = [
        {"replay_id": f"x{i}", "tier": "study", "rating": 1500}
        for i in range(4)
    ]
    assert fetch_replay.assign_tier(1700, rows) == "validation"


def test_assign_tier_ratio_holds_at_five_to_one():
    rows = (
        [{"replay_id": f"s{i}", "tier": "study", "rating": 1500} for i in range(5)]
        + [{"replay_id": "v0", "tier": "validation", "rating": 1700}]
    )
    # 5 study, 1 validation: 5 > 4*1, so next validation-eligible can go validation.
    assert fetch_replay.assign_tier(1700, rows) == "validation"


def test_assign_tier_ratio_blocks_extra_validation():
    rows = (
        [{"replay_id": f"s{i}", "tier": "study", "rating": 1500} for i in range(8)]
        + [{"replay_id": f"v{i}", "tier": "validation", "rating": 1700} for i in range(2)]
    )
    # 8 study, 2 validation: 8 <= 4*2, so next goes to study even at 1700.
    assert fetch_replay.assign_tier(1700, rows) == "study"


def test_assign_tier_explicit_study_overrides():
    rows = [{"replay_id": "v0", "tier": "validation", "rating": 1700}]
    assert fetch_replay.assign_tier(1700, rows, for_tier="study") == "study"


def test_assign_tier_explicit_validation_requires_floor():
    assert fetch_replay.assign_tier(1500, [], for_tier="validation") is None
    assert fetch_replay.assign_tier(1700, [], for_tier="validation") == "validation"


def test_assign_tier_sealed_exam_requires_floor():
    assert fetch_replay.assign_tier(1500, [], for_tier="sealed_exam") is None
    assert fetch_replay.assign_tier(1700, [], for_tier="sealed_exam") == "sealed_exam"


def test_pick_candidate_skips_seen():
    candidates = [
        {"id": "a", "rating": 1700, "private": 0},
        {"id": "b", "rating": 1800, "private": 0},
    ]
    assert fetch_replay.pick_candidate(candidates, {"b"}, 1400)["id"] == "a"


def test_pick_candidate_skips_below_min_rating():
    candidates = [
        {"id": "a", "rating": 1300, "private": 0},
        {"id": "b", "rating": 1500, "private": 0},
    ]
    assert fetch_replay.pick_candidate(candidates, set(), 1400)["id"] == "b"


def test_pick_candidate_skips_private():
    candidates = [
        {"id": "a", "rating": 1900, "private": 1},
        {"id": "b", "rating": 1500, "private": 0},
    ]
    assert fetch_replay.pick_candidate(candidates, set(), 1400)["id"] == "b"


def test_pick_candidate_returns_highest_rated():
    candidates = [
        {"id": "a", "rating": 1500, "private": 0},
        {"id": "b", "rating": 1800, "private": 0},
        {"id": "c", "rating": 1700, "private": 0},
    ]
    assert fetch_replay.pick_candidate(candidates, set(), 1400)["id"] == "b"


def test_pick_candidate_returns_none_when_empty():
    assert fetch_replay.pick_candidate([], set(), 1400) is None
    assert fetch_replay.pick_candidate([{"id": "a", "rating": 1300, "private": 0}], set(), 1400) is None


def test_pick_and_record_full_flow(tmp_path: Path):
    index_path = tmp_path / "replay_index.jsonl"
    download_dir = tmp_path / "replays"

    search_response = [
        {"id": "gen2ou-100", "rating": 1500, "private": 0, "uploadtime": 111, "players": ["p1", "p2"]},
        {"id": "gen2ou-200", "rating": 1800, "private": 0, "uploadtime": 222, "players": ["q1", "q2"]},
    ]
    log_text = "|gen|2\n|tier|[Gen 2] OU\n|turn|1\n"
    fetch_calls: list[str] = []

    def fake_fetch_json(url):
        fetch_calls.append(url)
        return search_response

    def fake_fetch_text(url):
        fetch_calls.append(url)
        return log_text

    row = fetch_replay.pick_and_record(
        fmt="gen2ou",
        min_rating=1400,
        for_tier="auto",
        download_dir=download_dir,
        index_path=index_path,
        fetch_json=fake_fetch_json,
        fetch_text=fake_fetch_text,
    )

    assert row["replay_id"] == "gen2ou-200"
    # First replay overall: 4:1 logic puts it in study (count starts at 0,0).
    assert row["tier"] == "study"
    assert row["rating"] == 1800
    assert (download_dir / "gen2ou-200.log").read_text(encoding="utf-8") == log_text
    rows = fetch_replay.read_replay_index(index_path)
    assert len(rows) == 1
    assert rows[0]["replay_id"] == "gen2ou-200"


def test_pick_and_record_skips_already_seen(tmp_path: Path):
    index_path = tmp_path / "replay_index.jsonl"
    download_dir = tmp_path / "replays"
    write_index(
        index_path,
        [{"replay_id": "gen2ou-200", "tier": "study", "rating": 1800, "uploadtime": 222, "fetched_at": "x", "players": []}],
    )

    search_response = [
        {"id": "gen2ou-200", "rating": 1800, "private": 0, "uploadtime": 222, "players": []},
        {"id": "gen2ou-300", "rating": 1500, "private": 0, "uploadtime": 333, "players": []},
    ]

    def fake_fetch_json(url):
        return search_response

    def fake_fetch_text(url):
        return "log text"

    row = fetch_replay.pick_and_record(
        fmt="gen2ou",
        min_rating=1400,
        for_tier="auto",
        download_dir=download_dir,
        index_path=index_path,
        fetch_json=fake_fetch_json,
        fetch_text=fake_fetch_text,
    )
    assert row["replay_id"] == "gen2ou-300"


def test_pick_and_record_raises_when_no_candidate(tmp_path: Path):
    import pytest

    index_path = tmp_path / "replay_index.jsonl"

    def fake_fetch_json(url):
        return [{"id": "a", "rating": 1200, "private": 0, "uploadtime": 1, "players": []}]

    with pytest.raises(RuntimeError):
        fetch_replay.pick_and_record(
            fmt="gen2ou",
            min_rating=1400,
            for_tier="auto",
            download_dir=tmp_path / "replays",
            index_path=index_path,
            fetch_json=fake_fetch_json,
            fetch_text=lambda url: "",
        )


def test_append_index_row_is_append_only(tmp_path: Path):
    p = tmp_path / "replay_index.jsonl"
    fetch_replay.append_index_row({"replay_id": "a", "tier": "study"}, p)
    fetch_replay.append_index_row({"replay_id": "b", "tier": "validation"}, p)
    rows = fetch_replay.read_replay_index(p)
    assert [r["replay_id"] for r in rows] == ["a", "b"]
