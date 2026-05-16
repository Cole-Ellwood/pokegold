#!/usr/bin/env python3
"""Verify all regression probes in case_library/regression/ pass.

Each probe is a JSON file with the shape:
  {
    "probe_id": "<unique>",
    "failure_mode": "<from schema enum>",
    "reasoning_class": "<from schema enum>",
    "position": {
      "active_user": {...mon_snapshot...},
      "active_opp": {...mon_snapshot...},
      ...
    },
    "corrected_action": {"type": "move"|"switch", "move"|"switch_to": "..."},
    "acceptable_actions": [optional list],
    "rationale": "...",
    "created_at": "..."
  }

A probe PASSES if the case_library/cases.jsonl contains AT LEAST ONE case
whose fingerprint substantially matches the probe's position AND whose
pro_action is the corrected_action (exact match for now). This proves the
pattern was learned and the recipe survived consolidation.

Exit 0 on PASS, 1 on FAIL. With zero probes the check trivially passes
(early in the loop, before recurrences appear).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIB = HERE / "case_library"
REG = LIB / "regression"


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def position_matches(probe_pos: dict, case_fp: dict) -> bool:
    pu = probe_pos.get("active_user", {})
    cu = case_fp.get("active_user", {})
    if pu.get("species") and pu.get("species") != cu.get("species"):
        return False
    po = probe_pos.get("active_opp", {})
    co = case_fp.get("active_opp", {})
    if po.get("species") and po.get("species") != co.get("species"):
        return False
    if "turn_bucket" in probe_pos and probe_pos["turn_bucket"] != case_fp.get("turn_bucket"):
        return False
    return True


def action_matches(expected: dict, actual: dict, acceptable: list[dict]) -> bool:
    if expected == actual:
        return True
    for alt in acceptable or []:
        if alt == actual:
            return True
    return False


def check_probe(probe: dict, cases: list[dict]) -> tuple[bool, str]:
    pid = probe.get("probe_id", "<no-id>")
    expected = probe.get("corrected_action")
    acceptable = probe.get("acceptable_actions", [])
    if not expected:
        return False, f"{pid}: probe missing corrected_action"
    position = probe.get("position", {})
    for case in cases:
        if position_matches(position, case.get("fingerprint", {})):
            if action_matches(expected, case.get("pro_action", {}), acceptable):
                return True, f"{pid}: matched case {case.get('case_id')}"
    return False, f"{pid}: no matching case proves the corrected pattern"


def main() -> int:
    cases = load_jsonl(LIB / "cases.jsonl")
    if not REG.is_dir():
        print("PASS (no regression dir yet)")
        return 0
    probes = sorted(REG.glob("*.json"))
    if not probes:
        print("PASS (0 probes; nothing to regress on yet)")
        return 0

    failed: list[str] = []
    for path in probes:
        try:
            probe = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            failed.append(f"{path.name}: bad json: {e}")
            continue
        ok, msg = check_probe(probe, cases)
        if ok:
            print(f"  [PASS] {msg}")
        else:
            print(f"  [FAIL] {msg}", file=sys.stderr)
            failed.append(msg)

    if failed:
        print(f"FAIL: {len(failed)} of {len(probes)} probes regressed", file=sys.stderr)
        return 1
    print(f"PASS: {len(probes)} probes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
