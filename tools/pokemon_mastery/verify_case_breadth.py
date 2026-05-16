#!/usr/bin/env python3
"""Verify case_library/cases.jsonl has the breadth gate target.

Reads gate_target.case_breadth_min from loop_state.json (default 150).
Counts distinct state-fingerprint hashes across cases.jsonl. A fingerprint
hash is a stable canonical hash over the decision-relevant fields:

  (active_user.species, active_opp.species, turn_bucket,
   sorted(side_conditions_user), sorted(side_conditions_opp))

This is the same hash the loop_state phase rotation uses for retrieval.
Two cases with the same hash collapse to one distinct fingerprint, so the
breadth metric counts unique strategic situations not raw case rows.

Exit 0 if distinct >= target. Exit 1 otherwise; prints the gap.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Single source of truth for the breadth-counting hash lives in fingerprint.py.
# Importing keeps this verifier in lockstep with what the loop actually stores.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from tools.pokemon_mastery.fingerprint import fingerprint_hash  # noqa: E402

HERE = Path(__file__).resolve().parent
LIB = HERE / "case_library"


def main() -> int:
    state_path = LIB / "loop_state.json"
    if not state_path.exists():
        print("FAIL: loop_state.json missing", file=sys.stderr)
        return 1
    state = json.loads(state_path.read_text(encoding="utf-8"))
    target = int(state.get("gate_target", {}).get("case_breadth_min", 150))

    cases_path = LIB / "cases.jsonl"
    distinct: set[str] = set()
    if cases_path.exists():
        for n, line in enumerate(cases_path.read_text(encoding="utf-8").splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"FAIL: cases.jsonl:{n}: bad json: {e}", file=sys.stderr)
                return 1
            fp = row.get("fingerprint", {})
            distinct.add(fingerprint_hash(fp))

    count = len(distinct)
    gap = count - target
    print(f"distinct_fingerprints: {count}  target: {target}  gap: {gap:+d}")
    if count >= target:
        print("PASS")
        return 0
    print("FAIL", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
