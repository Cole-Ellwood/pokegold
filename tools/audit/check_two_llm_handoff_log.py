"""Enforce the rule-#6 mutual-agreement gate on the two-LLM handoff log.

This audit refuses to pass when any phase claiming ``phase_complete`` /
``slice_accepted`` status lacks the mutual-LLM signature contract from
``docs/llm_pairing_rules.md``:

1. The store at ``audit/masterpiece_handoff_log.jsonl`` exists and every
   row is a JSON object with the required fields (phase, event, status,
   model, confidence, claim, signed_at).
2. Confidence labels are in the allowed set
   (``repo-proven`` / ``memory-derived`` / ``judgment``) per rule #4.
3. Event kinds + statuses cross-check
   (``slice_review`` requires a ``reviewer`` field, ``ack_start`` must be
   ``in_progress``, etc.).
4. For every phase that has at least one ``slice_update`` with status
   ``ready_for_review`` from its primary model, there must be a matching
   ``slice_review`` row from the NON-primary model carrying
   ``confidence=repo-proven`` and ``status`` in {``slice_accepted``,
   ``phase_complete``} before the phase is marked verified.
5. No phase carries an unresolved ``slice_rejected`` event without a
   later corrective ``slice_update`` from primary.

Soft mode
---------

This audit is added to ``tools/audit/check_release_smoke.py`` in
**warn-only** mode initially. ``--strict`` exits 1 on any pending /
unresolved phase; without it, the audit prints findings and exits 0 so
the release-smoke floor doesn't break the moment a phase is mid-flight.

The intent is to flip ``--strict`` on permanently once P0+P4 are both
mutual-signed (the existing rows are well-formed and the gate doesn't
have a backfill problem).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.debugger.handoff_log import audit_store, DEFAULT_STORE  # noqa: E402


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python tools/audit/check_two_llm_handoff_log.py",
        description=(
            "Enforce mutual-LLM agreement on the masterpiece handoff log. "
            "Warn-only by default; --strict refuses on any pending phase."
        ),
    )
    parser.add_argument(
        "--store",
        default="",
        help=f"Override store path (default: {DEFAULT_STORE}).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero on any pending/unverified phase as well as row errors.",
    )
    args = parser.parse_args(argv)
    store = Path(args.store) if args.store else DEFAULT_STORE
    report = audit_store(store=store)
    row_errors = report["row_errors"]
    pending = [
        phase
        for phase in report["phases"]
        if not report["phase_status"][phase]["mutual_verified"]
    ]
    verified = [
        phase
        for phase in report["phases"]
        if report["phase_status"][phase]["mutual_verified"]
    ]

    print("=== two-LLM handoff log audit ===")
    print(f"store: {report['store']}")
    print(f"rows: {report['row_count']}; row_errors: {len(row_errors)}")

    if row_errors:
        print("ROW SCHEMA ERRORS:")
        for re in row_errors:
            print(f"  line {re['line']}:")
            for err in re["errors"]:
                print(f"    - {err}")

    if verified:
        print(f"PASS phases (mutual-verified): {', '.join(verified)}")

    if pending:
        print("PENDING phases (in-flight; no mutual sign-off yet):")
        for phase in pending:
            reasons = report["phase_status"][phase]["reasons"]
            print(f"  {phase}:")
            for reason in reasons:
                print(f"    - {reason}")

    if row_errors:
        print("FAIL: handoff log has row schema errors (fix before release).")
        return 1
    if args.strict and pending:
        print(
            f"FAIL: --strict and {len(pending)} pending phase(s); "
            "complete mutual sign-off before release."
        )
        return 1
    print("OK: no schema errors; pending phases are advisory only (warn-only mode).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
