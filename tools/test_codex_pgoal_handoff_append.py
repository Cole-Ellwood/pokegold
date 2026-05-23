"""Tests for tools/codex_pgoal_handoff_append.py.

Covers row construction, enum validation, optional-field handling,
extra-JSON merge, and append-only semantics on a temp log.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest


TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

from codex_pgoal_handoff_append import build_row, append_row, parse_args  # noqa: E402


ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _minimal_args(**overrides):
    base = [
        "--phase", "test-phase-v1",
        "--event", "ack_start",
        "--status", "in_progress",
        "--signed-by", "Claude",
        "--summary", "minimal test row",
    ]
    for key, value in overrides.items():
        base.extend([f"--{key.replace('_', '-')}", value])
    return parse_args(base)


def test_minimal_row_has_required_fields():
    args = _minimal_args()
    row = build_row(args)
    assert set(row) >= {"ts", "phase", "event", "status", "signed_by", "summary"}
    assert ISO_UTC_RE.match(row["ts"]), row["ts"]
    assert row["signed_by"] == ["Claude"]


def test_signed_by_csv_splits():
    args = _minimal_args(signed_by="Claude,Codex")
    row = build_row(args)
    assert row["signed_by"] == ["Claude", "Codex"]


def test_invalid_event_exits(capsys):
    args = _minimal_args(event="ack_start")
    args.event = "not-a-real-event"
    with pytest.raises(SystemExit) as excinfo:
        build_row(args)
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "event must be one of" in captured.err


def test_invalid_status_exits(capsys):
    args = _minimal_args()
    args.status = "definitely-not-a-status"
    with pytest.raises(SystemExit) as excinfo:
        build_row(args)
    assert excinfo.value.code == 1
    assert "status must be one of" in capsys.readouterr().err


def test_invalid_confidence_exits(capsys):
    args = _minimal_args()
    args.confidence = "guess"
    with pytest.raises(SystemExit) as excinfo:
        build_row(args)
    assert excinfo.value.code == 1
    assert "confidence must be one of" in capsys.readouterr().err


def test_empty_signed_by_exits(capsys):
    args = _minimal_args()
    args.signed_by = ""
    with pytest.raises(SystemExit) as excinfo:
        build_row(args)
    assert excinfo.value.code == 1
    assert "signed-by" in capsys.readouterr().err


def test_optional_csv_fields_split_and_omit_when_empty():
    args = _minimal_args(write_set="a/b,c/d", collision_risk="x")
    row = build_row(args)
    assert row["write_set"] == ["a/b", "c/d"]
    assert row["collision_risk"] == ["x"]
    assert "evidence" not in row


def test_planned_validation_uses_semicolon_split():
    args = _minimal_args(planned_validation="check 1 with comma, allowed; check 2")
    row = build_row(args)
    assert row["planned_validation"] == ["check 1 with comma, allowed", "check 2"]


def test_extra_json_merges():
    args = _minimal_args(extra_json='{"custom_key": "value", "nested": {"k": 1}}')
    row = build_row(args)
    assert row["custom_key"] == "value"
    assert row["nested"] == {"k": 1}


def test_extra_json_invalid_exits(capsys):
    args = _minimal_args(extra_json="{not json")
    with pytest.raises(SystemExit) as excinfo:
        build_row(args)
    assert excinfo.value.code == 1
    assert "not valid JSON" in capsys.readouterr().err


def test_append_is_atomic_jsonl(tmp_path):
    log = tmp_path / "log.jsonl"
    args = _minimal_args()
    row1 = build_row(args)
    count1 = append_row(str(log), row1)
    assert count1 == 1
    row2 = build_row(args)
    count2 = append_row(str(log), row2)
    assert count2 == 2
    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    for line in lines:
        parsed = json.loads(line)
        assert parsed["phase"] == "test-phase-v1"


def test_append_uses_lf_line_endings(tmp_path):
    log = tmp_path / "log.jsonl"
    args = _minimal_args()
    append_row(str(log), build_row(args))
    raw = log.read_bytes()
    assert b"\r\n" not in raw, "CRLF leaked into JSONL"
    assert raw.endswith(b"\n")
