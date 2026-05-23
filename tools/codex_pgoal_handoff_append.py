"""Append a single canonical row to a codex-pgoal handoff log.

Replaces inline `python -c "import json; ..."` heredocs in the
codex-pgoal pairing loop. Validates event/status enums, auto-timestamps
in UTC, enforces append-only, and normalizes line endings.

Examples:

    python tools/codex_pgoal_handoff_append.py \\
        --phase codex-pgoal-skill-v1-hardening \\
        --event slice_review \\
        --status approved \\
        --signed-by Claude \\
        --summary "Approved scope X with one note Y" \\
        --confidence repo-proven \\
        --reviews Codex_ack_start_2026-05-23T00:03:56Z \\
        --evidence audit/log.jsonl:23,SKILL.md:14

Extra optional fields:

    --write-set path1,path2
    --safe-set path1,path2
    --collision-risk path
    --files-read path1,path2
    --tests-running cmd1,cmd2
    --planned-validation "check1;check2"
    --validation "ran X;ran Y"
    --intended-commit-message "msg"
    --not-run "explanation of skipped check"

For complex shapes, pass `--extra-json` with a JSON object that
merges into the row before write.

Exits 0 on success printing the row index. Exits 1 on validation
failure with the specific error.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from typing import Any


CANONICAL_EVENTS = {
    "ack_start",
    "slice_update",
    "slice_review",
    "mutual_done",
    "verify_pass",
    "verify_fail",
    "blocked",
}
CANONICAL_STATUSES = {"in_progress", "complete", "approved", "rejected", "blocked"}
CANONICAL_CONFIDENCE = {"repo-proven", "memory-derived", "judgment"}
DEFAULT_LOG_PATH = "audit/codex_pgoal_handoff_log.jsonl"


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _split_semi(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def _utc_now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_row(args: argparse.Namespace) -> dict[str, Any]:
    if args.event not in CANONICAL_EVENTS:
        sys.stderr.write(
            f"event must be one of {sorted(CANONICAL_EVENTS)} (got: {args.event})\n"
        )
        sys.exit(1)
    if args.status not in CANONICAL_STATUSES:
        sys.stderr.write(
            f"status must be one of {sorted(CANONICAL_STATUSES)} (got: {args.status})\n"
        )
        sys.exit(1)
    if args.confidence and args.confidence not in CANONICAL_CONFIDENCE:
        sys.stderr.write(
            f"confidence must be one of {sorted(CANONICAL_CONFIDENCE)} or omitted "
            f"(got: {args.confidence})\n"
        )
        sys.exit(1)

    signers = _split_csv(args.signed_by)
    if not signers:
        sys.stderr.write("--signed-by requires at least one name (e.g. Claude or Claude,Codex)\n")
        sys.exit(1)

    row: dict[str, Any] = {
        "ts": _utc_now_iso(),
        "phase": args.phase,
        "event": args.event,
        "status": args.status,
        "signed_by": signers,
        "summary": args.summary,
    }
    if args.confidence:
        row["confidence_label"] = args.confidence
    if args.reviews:
        row["reviews"] = args.reviews

    optional_csv = {
        "write_set": args.write_set,
        "safe_set_for_claude": args.safe_set,
        "collision_risk": args.collision_risk,
        "files_read": args.files_read,
        "tests_running": args.tests_running,
        "evidence": args.evidence,
    }
    for key, value in optional_csv.items():
        items = _split_csv(value)
        if items:
            row[key] = items

    optional_semi = {
        "planned_validation": args.planned_validation,
        "validation": args.validation,
    }
    for key, value in optional_semi.items():
        items = _split_semi(value)
        if items:
            row[key] = items

    if args.intended_commit_message:
        row["intended_commit_message"] = args.intended_commit_message
    if args.not_run:
        row["not_run"] = [args.not_run]

    if args.extra_json:
        try:
            extra = json.loads(args.extra_json)
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"--extra-json is not valid JSON: {exc}\n")
            sys.exit(1)
        if not isinstance(extra, dict):
            sys.stderr.write("--extra-json must be a JSON object\n")
            sys.exit(1)
        row.update(extra)

    return row


def append_row(log_path: str, row: dict[str, Any]) -> int:
    os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
    with open(log_path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, separators=(",", ":")) + "\n")
    with open(log_path, "r", encoding="utf-8") as fh:
        return sum(1 for _ in fh)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append a canonical row to a codex-pgoal handoff log.",
    )
    parser.add_argument("--log-path", default=DEFAULT_LOG_PATH, help="path to JSONL log file")
    parser.add_argument("--phase", required=True, help="stable phase tag, e.g. codex-pgoal-skill-v1")
    parser.add_argument("--event", required=True, help=f"one of {sorted(CANONICAL_EVENTS)}")
    parser.add_argument("--status", required=True, help=f"one of {sorted(CANONICAL_STATUSES)}")
    parser.add_argument("--signed-by", required=True, help="comma-separated signer list")
    parser.add_argument("--summary", required=True, help="one-line decision-useful summary")
    parser.add_argument("--confidence", default=None, help=f"one of {sorted(CANONICAL_CONFIDENCE)}")
    parser.add_argument("--reviews", default=None, help="reference to the row being reviewed")
    parser.add_argument("--write-set", default=None, help="comma-separated write-set paths")
    parser.add_argument("--safe-set", default=None, help="comma-separated paths safe for the other LLM")
    parser.add_argument("--collision-risk", default=None, help="comma-separated collision-risk paths")
    parser.add_argument("--files-read", default=None, help="comma-separated files-read paths")
    parser.add_argument("--tests-running", default=None, help="comma-separated test commands")
    parser.add_argument("--evidence", default=None, help="comma-separated evidence references")
    parser.add_argument(
        "--planned-validation", default=None, help="semicolon-separated planned validation steps"
    )
    parser.add_argument(
        "--validation", default=None, help="semicolon-separated executed validation steps"
    )
    parser.add_argument("--intended-commit-message", default=None, help="intended git commit message")
    parser.add_argument("--not-run", default=None, help="explanation of any planned check skipped")
    parser.add_argument(
        "--extra-json",
        default=None,
        help="JSON object merged into the row last (for fields without dedicated flags)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    row = build_row(args)
    row_count = append_row(args.log_path, row)
    print(f"row {row_count} appended to {args.log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
