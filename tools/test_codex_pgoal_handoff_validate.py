"""Tests for tools/codex_pgoal_handoff_validate.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

from codex_pgoal_handoff_validate import (  # noqa: E402
    validate_file,
    validate_row,
    main,
)


VALID_ROW = {
    "ts": "2026-05-23T00:00:00Z",
    "phase": "test-phase",
    "event": "ack_start",
    "status": "in_progress",
    "signed_by": ["Claude"],
    "summary": "valid row",
}


def _write_log(tmp_path: Path, rows: list[dict]) -> Path:
    log = tmp_path / "log.jsonl"
    with log.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, separators=(",", ":")) + "\n")
    return log


def test_valid_row_passes():
    assert validate_row(VALID_ROW, 1) == []


def test_non_dict_row_fails():
    errors = validate_row("not a dict", 5)
    assert any("not a JSON object" in e for e in errors)


def test_missing_required_fields():
    bad = {"phase": "p", "event": "ack_start"}
    errors = validate_row(bad, 1)
    assert any("'ts'" in e for e in errors)
    assert any("'status'" in e for e in errors)
    assert any("'signed_by'" in e for e in errors)
    assert any("'summary'" in e for e in errors)


def test_bad_ts_format():
    bad = {**VALID_ROW, "ts": "2026-05-23 00:00:00"}  # space instead of T
    errors = validate_row(bad, 1)
    assert any("not ISO UTC" in e for e in errors)


def test_unknown_event():
    bad = {**VALID_ROW, "event": "not-real"}
    errors = validate_row(bad, 1)
    assert any("event 'not-real'" in e for e in errors)


def test_unknown_status():
    bad = {**VALID_ROW, "status": "wat"}
    errors = validate_row(bad, 1)
    assert any("status 'wat'" in e for e in errors)


def test_unknown_confidence_label():
    bad = {**VALID_ROW, "confidence_label": "guess"}
    errors = validate_row(bad, 1)
    assert any("confidence_label 'guess'" in e for e in errors)


def test_signed_by_must_be_nonempty_list():
    bad = {**VALID_ROW, "signed_by": []}
    errors = validate_row(bad, 1)
    assert any("non-empty list" in e for e in errors)


def test_signed_by_entries_must_be_strings():
    bad = {**VALID_ROW, "signed_by": [123]}
    errors = validate_row(bad, 1)
    assert any("non-empty strings" in e for e in errors)


def test_optional_list_field_must_be_list():
    bad = {**VALID_ROW, "evidence": "not a list"}
    errors = validate_row(bad, 1)
    assert any("'evidence' must be a list" in e for e in errors)


def test_optional_string_field_must_be_string():
    bad = {**VALID_ROW, "reviews": ["should be string"]}
    errors = validate_row(bad, 1)
    assert any("'reviews' must be a string" in e for e in errors)


def test_validate_file_missing_path_errors(tmp_path):
    errors, warnings, stats = validate_file(str(tmp_path / "does-not-exist.jsonl"))
    assert any("not found" in e for e in errors)


def test_validate_file_clean_log(tmp_path):
    log = _write_log(tmp_path, [VALID_ROW, VALID_ROW])
    errors, warnings, stats = validate_file(str(log))
    assert errors == []
    assert stats["rows"] == 2
    assert stats["events"] == {"ack_start": 2}
    assert stats["signers"] == {"Claude": 2}
    assert stats["phases"] == {"test-phase": 2}


def test_validate_file_ts_drift_warning(tmp_path):
    rows = [
        {**VALID_ROW, "ts": "2026-05-23T01:00:00Z"},
        {**VALID_ROW, "ts": "2026-05-23T00:30:00Z"},  # earlier than previous
    ]
    log = _write_log(tmp_path, rows)
    errors, warnings, stats = validate_file(str(log))
    assert errors == []
    assert any("earlier than line" in w for w in warnings)


def test_validate_file_skips_blank_lines(tmp_path):
    log = tmp_path / "log.jsonl"
    with log.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(VALID_ROW) + "\n")
        fh.write("\n")
        fh.write(json.dumps(VALID_ROW) + "\n")
    errors, warnings, stats = validate_file(str(log))
    assert errors == []
    assert stats["rows"] == 2


def test_validate_file_bad_json_reports_line(tmp_path):
    log = tmp_path / "log.jsonl"
    with log.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(VALID_ROW) + "\n")
        fh.write("{not json}\n")
    errors, warnings, stats = validate_file(str(log))
    assert any("line 2: invalid JSON" in e for e in errors)


def test_main_exit_zero_on_clean(tmp_path, capsys):
    log = _write_log(tmp_path, [VALID_ROW])
    rc = main([str(log)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "CLEAN" in out


def test_main_exit_one_on_error(tmp_path, capsys):
    bad = {**VALID_ROW, "event": "not-real"}
    log = _write_log(tmp_path, [bad])
    rc = main([str(log)])
    assert rc == 1
    out = capsys.readouterr().out
    assert "errors" in out.lower()


def test_main_strict_promotes_warnings(tmp_path, capsys):
    rows = [
        {**VALID_ROW, "ts": "2026-05-23T01:00:00Z"},
        {**VALID_ROW, "ts": "2026-05-23T00:30:00Z"},
    ]
    log = _write_log(tmp_path, rows)
    rc_lax = main([str(log)])
    capsys.readouterr()
    rc_strict = main([str(log), "--strict"])
    capsys.readouterr()
    assert rc_lax == 0
    assert rc_strict == 1


def test_main_json_output(tmp_path, capsys):
    log = _write_log(tmp_path, [VALID_ROW])
    rc = main([str(log), "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["ok"] is True
    assert parsed["stats"]["rows"] == 1
