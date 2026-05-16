#!/usr/bin/env python3
"""Loop runner for the Compounding Loop.

Orchestrates one iteration: picks the next phase from loop_state.json,
exposes the operations the predictor needs (append case row, append
replay row, append metrics row, bump iteration counter), validates
against case_library/schema.json, and produces the commit message
shape the runbook requires.

Most of the per-turn work (read prompt, freeze prediction, reveal,
score) is interactive and runs in the predictor session (Claude or
Codex). loop_runner.py is the thin coordination layer that keeps the
durable files consistent.

CLI:
  python tools/pokemon_mastery/loop_runner.py status
  python tools/pokemon_mastery/loop_runner.py suggest-phase
  python tools/pokemon_mastery/loop_runner.py append-case --from-stdin
  python tools/pokemon_mastery/loop_runner.py append-replay --from-stdin
  python tools/pokemon_mastery/loop_runner.py append-metrics --from-stdin
  python tools/pokemon_mastery/loop_runner.py bump-iteration --phase INGEST --replay-id gen2ou-NNN
  python tools/pokemon_mastery/loop_runner.py commit-message --phase INGEST --replay-id gen2ou-NNN
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LIB = HERE / "case_library"
STATE_PATH = LIB / "loop_state.json"
CASES_PATH = LIB / "cases.jsonl"
REPLAY_INDEX_PATH = LIB / "replay_index.jsonl"
METRICS_PATH = LIB / "metrics.jsonl"

VALID_PHASES = {
    "INGEST",
    "DIAGNOSE",
    "REGRESSION_PROTECT",
    "VALIDATE",
    "STAGNATION_CHECK",
    "CONSOLIDATE",
    "INFRA",
    "DEEP_STUDY",
    "CROSS_DOMAIN",
    "BOOTSTRAP",
}

REQUIRED_CASE_FIELDS = (
    "case_id",
    "replay_id",
    "turn",
    "side",
    "tier",
    "fingerprint",
    "pro_action",
    "pro_reasoning_class",
    "created_at",
)
REQUIRED_REPLAY_FIELDS = ("replay_id", "tier", "rating", "uploadtime", "fetched_at")
REQUIRED_METRICS_FIELDS = ("window_id", "computed_at", "tier", "decision_count")


def load_state() -> dict:
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def suggest_next_phase(state: dict) -> str:
    """Heuristic phase picker.

    Order of priority:
    - If no replays at all, INGEST.
    - If we just INGESTed and need to extract: DIAGNOSE+EXTRACT happens
      inside the INGEST turn itself, so the next phase is normally a
      fresh INGEST OR a VALIDATE if the cadence triggers.
    - Every N study INGESTs trigger a VALIDATE.
    - Every M iterations trigger CONSOLIDATE.
    - When stagnation is detected, the predictor escalates manually.
    """
    iter_count = state.get("iteration_count", 0)
    last_phase = (state.get("last_iteration_phase") or "").upper()
    cadence_validate = int(state.get("ingest_cadence_validate", 5))
    cadence_consolidate = int(state.get("consolidate_cadence_iterations", 20))
    replays = count_lines(REPLAY_INDEX_PATH)
    cases = count_lines(CASES_PATH)

    if replays == 0:
        return "INGEST"
    if iter_count > 0 and iter_count % cadence_consolidate == 0 and last_phase != "CONSOLIDATE":
        return "CONSOLIDATE"
    # Count study replays since last VALIDATE; for now, every cadence_validate INGESTs.
    study_ingests = 0
    last_validate_at = None
    if REPLAY_INDEX_PATH.exists():
        for line in REPLAY_INDEX_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("tier") == "study":
                study_ingests += 1
            elif row.get("tier") == "validation":
                last_validate_at = study_ingests
    if last_validate_at is None:
        ingests_since_validate = study_ingests
    else:
        ingests_since_validate = study_ingests - last_validate_at
    if ingests_since_validate >= cadence_validate:
        return "VALIDATE"
    return "INGEST"


def validate_case_row(row: dict) -> None:
    for f in REQUIRED_CASE_FIELDS:
        if f not in row:
            raise ValueError(f"case row missing required field: {f}")
    if row["tier"] != "study":
        raise ValueError(
            f"case row tier must be 'study' (got {row['tier']!r}); "
            "validation and sealed_exam replays are NEVER mined for cases"
        )
    fp = row.get("fingerprint", {})
    if not fp.get("active_user") or not fp.get("active_opp"):
        raise ValueError("fingerprint must include active_user and active_opp")
    if not fp.get("turn_bucket"):
        raise ValueError("fingerprint must include turn_bucket")


def validate_replay_row(row: dict) -> None:
    for f in REQUIRED_REPLAY_FIELDS:
        if f not in row:
            raise ValueError(f"replay row missing required field: {f}")
    if row["tier"] not in {"study", "validation", "sealed_exam"}:
        raise ValueError(f"invalid tier: {row['tier']!r}")


def validate_metrics_row(row: dict) -> None:
    for f in REQUIRED_METRICS_FIELDS:
        if f not in row:
            raise ValueError(f"metrics row missing required field: {f}")
    if row["tier"] not in {"study", "validation", "sealed_exam"}:
        raise ValueError(f"invalid tier: {row['tier']!r}")


def append_jsonl(row: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


def append_case(row: dict) -> None:
    validate_case_row(row)
    if row.get("replay_id"):
        seen = set()
        if REPLAY_INDEX_PATH.exists():
            for line in REPLAY_INDEX_PATH.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if r.get("replay_id"):
                    seen.add((r["replay_id"], r.get("tier")))
        if (row["replay_id"], row["tier"]) not in seen:
            raise ValueError(
                f"case row references replay_id={row['replay_id']!r} tier={row['tier']!r} "
                f"that is not in replay_index.jsonl (or has a different tier). "
                "Add the replay to the index before extracting cases from it."
            )
    append_jsonl(row, CASES_PATH)


def append_replay(row: dict) -> None:
    validate_replay_row(row)
    seen = set()
    if REPLAY_INDEX_PATH.exists():
        for line in REPLAY_INDEX_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("replay_id"):
                seen.add(r["replay_id"])
    if row["replay_id"] in seen:
        raise ValueError(f"replay_id {row['replay_id']!r} already in replay_index.jsonl")
    append_jsonl(row, REPLAY_INDEX_PATH)


def append_metrics(row: dict) -> None:
    validate_metrics_row(row)
    append_jsonl(row, METRICS_PATH)


def bump_iteration(phase: str, replay_id: str | None) -> dict:
    phase_upper = phase.upper()
    if phase_upper not in VALID_PHASES:
        raise ValueError(f"unknown phase {phase!r}; valid: {sorted(VALID_PHASES)}")
    state = load_state()
    state["iteration_count"] = int(state.get("iteration_count", 0)) + 1
    state["last_iteration_phase"] = phase_upper
    state["last_iteration_replay_id"] = replay_id
    state["last_iteration_at"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    save_state(state)
    return state


def commit_message(phase: str, replay_id: str | None) -> str:
    state = load_state()
    iter_n = state.get("iteration_count", 0)
    rid = replay_id or "na"
    return f"pokemon-mastery-loop: iter {iter_n} {phase.upper()} {rid}"


def status_report() -> dict:
    state = load_state()
    return {
        "iteration_count": state.get("iteration_count", 0),
        "last_iteration_phase": state.get("last_iteration_phase"),
        "last_iteration_replay_id": state.get("last_iteration_replay_id"),
        "replays_indexed": count_lines(REPLAY_INDEX_PATH),
        "cases_stored": count_lines(CASES_PATH),
        "metrics_rows": count_lines(METRICS_PATH),
        "suggested_next_phase": suggest_next_phase(state),
        "gate_target": state.get("gate_target"),
    }


def _read_stdin_json() -> dict:
    body = sys.stdin.read().strip()
    if not body:
        raise ValueError("expected JSON on stdin; got empty input")
    return json.loads(body)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="print loop status")
    sub.add_parser("suggest-phase", help="print suggested next phase")

    p_case = sub.add_parser("append-case", help="append a validated case row to cases.jsonl")
    p_case.add_argument("--from-stdin", action="store_true")
    p_case.add_argument("--file", type=Path)

    p_replay = sub.add_parser("append-replay", help="append a validated replay row to replay_index.jsonl")
    p_replay.add_argument("--from-stdin", action="store_true")
    p_replay.add_argument("--file", type=Path)

    p_metrics = sub.add_parser("append-metrics", help="append a validated metrics row to metrics.jsonl")
    p_metrics.add_argument("--from-stdin", action="store_true")
    p_metrics.add_argument("--file", type=Path)

    p_bump = sub.add_parser("bump-iteration", help="increment iteration_count and set last_phase")
    p_bump.add_argument("--phase", required=True)
    p_bump.add_argument("--replay-id", default=None)

    p_msg = sub.add_parser("commit-message", help="print the canonical commit message for this iteration")
    p_msg.add_argument("--phase", required=True)
    p_msg.add_argument("--replay-id", default=None)

    args = parser.parse_args(argv)

    if args.command == "status":
        print(json.dumps(status_report(), indent=2))
        return 0
    if args.command == "suggest-phase":
        print(suggest_next_phase(load_state()))
        return 0
    if args.command in ("append-case", "append-replay", "append-metrics"):
        if args.from_stdin:
            row = _read_stdin_json()
        elif args.file:
            row = json.loads(args.file.read_text(encoding="utf-8"))
        else:
            print("FAIL: pass --from-stdin or --file", file=sys.stderr)
            return 1
        try:
            if args.command == "append-case":
                append_case(row)
            elif args.command == "append-replay":
                append_replay(row)
            else:
                append_metrics(row)
        except ValueError as e:
            print(f"FAIL: {e}", file=sys.stderr)
            return 1
        print(f"appended to {args.command.split('-')[1]}")
        return 0
    if args.command == "bump-iteration":
        state = bump_iteration(args.phase, args.replay_id)
        print(json.dumps({"iteration_count": state["iteration_count"], "phase": state["last_iteration_phase"]}))
        return 0
    if args.command == "commit-message":
        print(commit_message(args.phase, args.replay_id))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
