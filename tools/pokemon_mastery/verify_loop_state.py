#!/usr/bin/env python3
"""Verify Pokemon Mastery Compounding Loop infrastructure invariants.

Checks:
- case_library/ exists with the expected files.
- loop_state.json validates against a minimal shape.
- replay_index.jsonl rows are well-formed; tiers are valid.
- cases.jsonl rows reference replays present in replay_index.jsonl.
- TIER CONTAMINATION GUARD: no case row has tier=validation or tier=sealed_exam.
  (Cases are only extracted from study-tier replays; the validation/sealed
  tiers are score-only.)
- All regression probes under case_library/regression/ load as valid JSON.
- No duplicate replay_id in replay_index.jsonl.
- ema_alpha and gate_target fields in loop_state.json are within sane ranges.

Exit code 0 on PASS, 1 on FAIL. Prints a short report either way.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIB = HERE / "case_library"
VALID_TIERS = {"study", "validation", "sealed_exam"}
CASE_TIERS_ALLOWED = {"study"}


def fail(msg: str, errors: list[str]) -> None:
    errors.append(msg)


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ValueError(f"{path.name}:{n}: bad json: {e}") from e
    return rows


def check(errors: list[str]) -> None:
    if not LIB.is_dir():
        fail(f"missing dir: {LIB}", errors)
        return

    state_path = LIB / "loop_state.json"
    if not state_path.exists():
        fail("missing loop_state.json", errors)
        return
    state = json.loads(state_path.read_text(encoding="utf-8"))

    for key in ("gate_target", "ingest_cadence_validate", "ema_alpha", "ema_window_size"):
        if key not in state:
            fail(f"loop_state.json missing key: {key}", errors)

    gate = state.get("gate_target", {})
    if not 0.0 <= gate.get("top_match_min", -1) <= 1.0:
        fail("gate_target.top_match_min out of range", errors)
    if not 0.0 <= state.get("ema_alpha", -1) <= 1.0:
        fail("ema_alpha out of range", errors)

    try:
        replay_rows = load_jsonl(LIB / "replay_index.jsonl")
    except ValueError as e:
        fail(str(e), errors)
        replay_rows = []
    try:
        case_rows = load_jsonl(LIB / "cases.jsonl")
    except ValueError as e:
        fail(str(e), errors)
        case_rows = []

    seen_replays: dict[str, str] = {}
    for row in replay_rows:
        rid = row.get("replay_id")
        tier = row.get("tier")
        if not rid:
            fail("replay_index.jsonl row missing replay_id", errors)
            continue
        if tier not in VALID_TIERS:
            fail(f"replay_index.jsonl: {rid} has invalid tier {tier!r}", errors)
        if rid in seen_replays:
            fail(f"replay_index.jsonl: duplicate replay_id {rid}", errors)
        seen_replays[rid] = tier

    for row in case_rows:
        cid = row.get("case_id", "<no-id>")
        rid = row.get("replay_id")
        tier = row.get("tier")
        if tier not in CASE_TIERS_ALLOWED:
            fail(
                f"TIER CONTAMINATION: case {cid} has tier={tier!r} "
                "(cases may only be extracted from study tier).",
                errors,
            )
        if rid not in seen_replays:
            fail(f"case {cid} references unknown replay_id {rid!r}", errors)
        elif seen_replays[rid] != tier:
            fail(
                f"case {cid} tier ({tier!r}) does not match replay tier "
                f"({seen_replays[rid]!r})",
                errors,
            )

    reg_dir = LIB / "regression"
    if reg_dir.is_dir():
        for probe in sorted(reg_dir.glob("*.json")):
            try:
                json.loads(probe.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                fail(f"regression probe {probe.name}: bad json: {e}", errors)

    print(
        f"loop_state: armed_by_pgoal={state.get('armed_by_pgoal')} "
        f"iter={state.get('iteration_count')} "
        f"replays={len(replay_rows)} cases={len(case_rows)} "
        f"gate={gate.get('label')}"
    )


def main() -> int:
    errors: list[str] = []
    try:
        check(errors)
    except Exception as e:
        errors.append(f"unexpected error: {e!r}")
    if errors:
        print("FAIL", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
