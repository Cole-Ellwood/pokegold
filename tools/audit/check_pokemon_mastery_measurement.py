#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "pokemon_mastery" / "measurement_minigoal_2026-05.md"
LEDGER = ROOT / "docs" / "pokemon_mastery" / "measurement_progress_ledger.csv"

REQUIRED_COLUMNS = [
    "run_id",
    "date_utc",
    "test_type",
    "pool",
    "suite_version",
    "scenario_count",
    "romhack_commit",
    "rom_hash",
    "access_mode",
    "opponent_model",
    "action_quality",
    "mechanics_accuracy",
    "reasoning_quality",
    "risk_management",
    "calibration",
    "weighted_score",
    "top_move_agreement",
    "acceptable_move_agreement",
    "severe_blunders",
    "mechanics_errors",
    "state_errors",
    "hidden_info_errors",
    "illegal_action_errors",
    "earliest_error_turn",
    "wins",
    "battles",
    "sim_win_rate",
    "confidence_interval",
    "notes_artifact",
    "next_study_target",
]

REQUIRED_DOC_PHRASES = [
    "does not replace or resume the paused",
    "Quick Test Cadence",
    "Final Exam Cadence",
    "weighted_score",
    "Simulation Ladder",
    "Contamination Controls",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_float(value: str) -> float | None:
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def check_doc() -> None:
    if not DOC.exists():
        fail(f"missing measurement mini-goal doc: {DOC.relative_to(ROOT)}")
    text = DOC.read_text(encoding="utf-8", errors="replace")
    for phrase in REQUIRED_DOC_PHRASES:
        if phrase not in text:
            fail(f"measurement doc missing required phrase: {phrase}")


def check_ledger() -> list[dict[str, str]]:
    if not LEDGER.exists():
        fail(f"missing measurement ledger: {LEDGER.relative_to(ROOT)}")
    with LEDGER.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != REQUIRED_COLUMNS:
            fail("measurement ledger columns do not match required schema")
        rows = list(reader)
    seen: set[str] = set()
    for index, row in enumerate(rows, start=2):
        run_id = row["run_id"].strip()
        if not run_id:
            fail(f"ledger row {index}: missing run_id")
        if run_id in seen:
            fail(f"ledger row {index}: duplicate run_id {run_id}")
        seen.add(run_id)
        if not row["date_utc"].strip():
            fail(f"ledger row {index}: missing date_utc")
        scenario_count = parse_float(row["scenario_count"])
        if scenario_count is None or scenario_count < 0:
            fail(f"ledger row {index}: invalid scenario_count")
        dimensions = [
            parse_float(row["action_quality"]),
            parse_float(row["mechanics_accuracy"]),
            parse_float(row["reasoning_quality"]),
            parse_float(row["risk_management"]),
            parse_float(row["calibration"]),
        ]
        recorded = parse_float(row["weighted_score"])
        if all(value is not None for value in dimensions):
            expected = (
                dimensions[0] * 35
                + dimensions[1] * 20
                + dimensions[2] * 20
                + dimensions[3] * 15
                + dimensions[4] * 10
            ) / 4
            if recorded is None:
                fail(f"ledger row {index}: missing weighted_score")
            if abs(recorded - expected) > 0.05:
                fail(
                    f"ledger row {index}: weighted_score {recorded:.2f} "
                    f"does not match expected {expected:.2f}"
                )
        elif recorded is not None and row["test_type"] != "proxy_baseline":
            fail(f"ledger row {index}: weighted_score present without all dimensions")
    return rows


def main() -> int:
    check_doc()
    rows = check_ledger()
    scored = [row for row in rows if parse_float(row["weighted_score"]) is not None]
    print("Pokemon mastery measurement audit passed.")
    print(f"Ledger rows: {len(rows)}")
    print(f"Rows with numeric weighted_score: {len(scored)}")
    if scored:
        latest = scored[-1]
        print(
            "Latest scored run: "
            f"{latest['run_id']} score={latest['weighted_score']} "
            f"type={latest['test_type']} pool={latest['pool']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
