#!/usr/bin/env python3
"""Verify whether the Compounding Loop has passed its progress gate.

Reads case_library/loop_state.json for the gate target, then reads
case_library/metrics.jsonl for the most recent VALIDATION-tier rolling
window. Passes only if the most recent metrics_row for tier=validation
satisfies ALL of:

  decision_count >= gate_target.sealed_window_decisions
  top_match >= gate_target.top_match_min
  acceptable_match >= gate_target.acceptable_match_min
  severe_blunder_rate == 0  (gate_target.severe_blunder_max)
  positive_selection_converter >= gate_target.positive_selection_converter_min

Exit 0 if the gate passes. Exit 1 otherwise. Prints the gap from each
threshold so the loop can target the largest remaining gap next iteration.

Honest stub today: with no metrics rows, this exits 1 (the gate has not
been hit). The gate becomes mechanically passable as soon as the loop
ingests enough sealed-validation decisions to fill the window.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIB = HERE / "case_library"


def latest_validation_metrics(rows: list[dict]) -> dict | None:
    for row in reversed(rows):
        if row.get("tier") == "validation":
            return row
    return None


def main() -> int:
    state_path = LIB / "loop_state.json"
    if not state_path.exists():
        print("FAIL: case_library/loop_state.json missing", file=sys.stderr)
        return 1
    state = json.loads(state_path.read_text(encoding="utf-8"))
    gate = state.get("gate_target", {})

    metrics_path = LIB / "metrics.jsonl"
    rows: list[dict] = []
    if metrics_path.exists():
        for line in metrics_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"FAIL: metrics.jsonl bad json: {e}", file=sys.stderr)
                return 1

    latest = latest_validation_metrics(rows)
    if latest is None:
        print(
            "FAIL: no validation-tier metrics row yet "
            "(loop has not produced a sealed window of decisions).",
            file=sys.stderr,
        )
        return 1

    needed_window = int(gate.get("sealed_window_decisions", 30))
    dc = int(latest.get("decision_count", 0))
    top = float(latest.get("top_match", 0))
    acc = float(latest.get("acceptable_match", 0))
    sev = float(latest.get("severe_blunder_rate", 1.0))
    pos = float(latest.get("positive_selection_converter", 0))

    top_min = float(gate.get("top_match_min", 0.6))
    acc_min = float(gate.get("acceptable_match_min", 0.75))
    sev_max = float(gate.get("severe_blunder_max", 0))
    pos_min = float(gate.get("positive_selection_converter_min", 0.65))

    checks = [
        ("decision_count", dc, needed_window, dc >= needed_window, "ge"),
        ("top_match", top, top_min, top >= top_min, "ge"),
        ("acceptable_match", acc, acc_min, acc >= acc_min, "ge"),
        ("severe_blunder_rate", sev, sev_max, sev <= sev_max, "le"),
        ("positive_selection_converter", pos, pos_min, pos >= pos_min, "ge"),
    ]

    print(f"window: {latest.get('window_id')}  tier=validation")
    all_pass = True
    for name, actual, threshold, ok, direction in checks:
        symbol = ">=" if direction == "ge" else "<="
        gap = (actual - threshold) if direction == "ge" else (threshold - actual)
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name} {actual!r} {symbol} {threshold!r}  gap={gap:+.4f}")
        if not ok:
            all_pass = False

    if all_pass:
        print("GATE: PASS")
        return 0
    print("GATE: FAIL", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
