"""Validate a codex-pgoal handoff log JSONL file.

Checks each row for:
- JSON parsability
- Required fields (ts, phase, event, status, signed_by, summary)
- Type correctness (signed_by list, summary string, etc.)
- Enum membership (event, status, confidence_label)
- ts ISO-UTC format

Reports invalid rows with line number + reason. Warns on rows whose
ts is earlier than a prior row (chronological drift from concurrent
appends - the skill documents that consumers sort by ts, but the
warning surfaces frequency for the user).

Exit codes:
    0 = clean (warnings allowed)
    1 = at least one validation error

Usage:
    python tools/codex_pgoal_handoff_validate.py [path]
    python tools/codex_pgoal_handoff_validate.py --strict  # warnings -> errors
    python tools/codex_pgoal_handoff_validate.py --json    # machine output
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

# Reuse the helper's canonical enum sets so the validator and writer
# stay locked together; if the helper adds an event, the validator
# accepts it automatically.
from codex_pgoal_handoff_append import (  # noqa: E402
    CANONICAL_CONFIDENCE,
    CANONICAL_EVENTS,
    CANONICAL_STATUSES,
)


DEFAULT_LOG_PATH = "audit/codex_pgoal_handoff_log.jsonl"
ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
REQUIRED_FIELDS = ("ts", "phase", "event", "status", "signed_by", "summary")
OPTIONAL_LIST_FIELDS = (
    "evidence",
    "write_set",
    "safe_set_for_claude",
    "collision_risk",
    "files_read",
    "tests_running",
    "planned_validation",
    "validation",
    "not_run",
)
OPTIONAL_STRING_FIELDS = (
    "confidence_label",
    "reviews",
    "intended_commit_message",
)


def validate_row(row: Any, line_no: int) -> list[str]:
    errors: list[str] = []
    if not isinstance(row, dict):
        return [f"line {line_no}: row is not a JSON object"]

    for field in REQUIRED_FIELDS:
        if field not in row:
            errors.append(f"line {line_no}: missing required field '{field}'")

    ts = row.get("ts")
    if isinstance(ts, str) and not ISO_UTC_RE.match(ts):
        errors.append(f"line {line_no}: ts '{ts}' is not ISO UTC (YYYY-MM-DDTHH:MM:SSZ)")
    elif "ts" in row and not isinstance(ts, str):
        errors.append(f"line {line_no}: ts must be a string, got {type(ts).__name__}")

    phase = row.get("phase")
    if "phase" in row and (not isinstance(phase, str) or not phase.strip()):
        errors.append(f"line {line_no}: phase must be a non-empty string")

    event = row.get("event")
    if "event" in row:
        if not isinstance(event, str):
            errors.append(f"line {line_no}: event must be a string")
        elif event not in CANONICAL_EVENTS:
            errors.append(
                f"line {line_no}: event '{event}' not in {sorted(CANONICAL_EVENTS)}"
            )

    status = row.get("status")
    if "status" in row:
        if not isinstance(status, str):
            errors.append(f"line {line_no}: status must be a string")
        elif status not in CANONICAL_STATUSES:
            errors.append(
                f"line {line_no}: status '{status}' not in {sorted(CANONICAL_STATUSES)}"
            )

    signed_by = row.get("signed_by")
    if "signed_by" in row:
        if not isinstance(signed_by, list) or not signed_by:
            errors.append(f"line {line_no}: signed_by must be a non-empty list")
        elif not all(isinstance(s, str) and s.strip() for s in signed_by):
            errors.append(f"line {line_no}: signed_by entries must be non-empty strings")

    summary = row.get("summary")
    if "summary" in row and (not isinstance(summary, str) or not summary.strip()):
        errors.append(f"line {line_no}: summary must be a non-empty string")

    if "confidence_label" in row:
        cl = row["confidence_label"]
        if cl not in CANONICAL_CONFIDENCE:
            errors.append(
                f"line {line_no}: confidence_label '{cl}' not in {sorted(CANONICAL_CONFIDENCE)}"
            )

    for field in OPTIONAL_LIST_FIELDS:
        if field in row and not isinstance(row[field], list):
            errors.append(f"line {line_no}: optional field '{field}' must be a list when present")

    for field in OPTIONAL_STRING_FIELDS:
        if field in row and not isinstance(row[field], str):
            errors.append(f"line {line_no}: optional field '{field}' must be a string when present")

    return errors


def validate_file(path: str) -> tuple[list[str], list[str], dict[str, Any]]:
    """Return (errors, warnings, stats)."""
    errors: list[str] = []
    warnings: list[str] = []
    stats: dict[str, Any] = {
        "rows": 0,
        "events": {},
        "signers": {},
        "phases": {},
    }

    p = Path(path)
    if not p.exists():
        return ([f"log file not found: {path}"], [], stats)

    last_ts: str | None = None
    last_ts_line: int = 0
    with p.open(encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            stats["rows"] += 1
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: invalid JSON: {exc}")
                continue

            errors.extend(validate_row(row, line_no))

            ev = row.get("event")
            if isinstance(ev, str):
                stats["events"][ev] = stats["events"].get(ev, 0) + 1
            phase = row.get("phase")
            if isinstance(phase, str):
                stats["phases"][phase] = stats["phases"].get(phase, 0) + 1
            signers = row.get("signed_by")
            if isinstance(signers, list):
                for s in signers:
                    if isinstance(s, str):
                        stats["signers"][s] = stats["signers"].get(s, 0) + 1

            ts = row.get("ts")
            if isinstance(ts, str) and ISO_UTC_RE.match(ts):
                if last_ts is not None and ts < last_ts:
                    warnings.append(
                        f"line {line_no}: ts {ts} earlier than line {last_ts_line} ts {last_ts} "
                        f"(append order drift; consumers should sort by ts)"
                    )
                last_ts = ts
                last_ts_line = line_no

    return errors, warnings, stats


def render_text(path: str, errors: list[str], warnings: list[str], stats: dict[str, Any]) -> str:
    lines = [f"validating {path}"]
    lines.append(f"  rows: {stats['rows']}")
    if stats["events"]:
        events_summary = ", ".join(f"{k}={v}" for k, v in sorted(stats["events"].items()))
        lines.append(f"  events: {events_summary}")
    if stats["signers"]:
        signers_summary = ", ".join(f"{k}={v}" for k, v in sorted(stats["signers"].items()))
        lines.append(f"  signers: {signers_summary}")
    if stats["phases"]:
        phases_summary = ", ".join(f"{k}={v}" for k, v in sorted(stats["phases"].items()))
        lines.append(f"  phases: {phases_summary}")
    if warnings:
        lines.append(f"warnings ({len(warnings)}):")
        for w in warnings:
            lines.append(f"  - {w}")
    if errors:
        lines.append(f"errors ({len(errors)}):")
        for e in errors:
            lines.append(f"  - {e}")
    else:
        lines.append("errors: 0 -- CLEAN")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a codex-pgoal handoff log JSONL file.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=DEFAULT_LOG_PATH,
        help=f"path to JSONL log (default: {DEFAULT_LOG_PATH})",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat warnings as errors (e.g. ts-order drift)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of human-readable text",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    errors, warnings, stats = validate_file(args.path)
    effective_errors = list(errors)
    if args.strict:
        effective_errors.extend(warnings)
    if args.json:
        print(
            json.dumps(
                {
                    "path": args.path,
                    "ok": not effective_errors,
                    "errors": errors,
                    "warnings": warnings,
                    "stats": stats,
                },
                indent=2,
            )
        )
    else:
        print(render_text(args.path, errors, warnings, stats))
    return 0 if not effective_errors else 1


if __name__ == "__main__":
    sys.exit(main())
