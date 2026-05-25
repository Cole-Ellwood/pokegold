"""Two-LLM handoff log for the Claude+Codex partnership.

Append-only JSONL store at ``audit/masterpiece_handoff_log.jsonl``.
Every claim a model makes about a slice (ack, update, review, sign-off)
is one row. The audit at ``tools/audit/check_two_llm_handoff_log.py``
enforces the rule-#6 mutual-agreement gate: a phase or slice is only
``mutual_verified`` when BOTH models (claude and codex) have signed
rows that meet the gate conditions.

Why structural enforcement matters
----------------------------------

``docs/llm_pairing_rules.md`` rule #6 says neither LLM declares done
unilaterally. That's a convention until a programmatic gate refuses to
mark anything verified without both signatures. ``check_two_llm_handoff_log.py``
is the gate. ``handoff_log.py`` is the typed write surface that keeps
the JSONL well-formed so the audit can trust it.

Event kinds
-----------

- ``ack_start``    — a model declares ownership of a slice and its
                     write set.
- ``slice_update`` — mid- or end-of-slice status. Reports verification
                     commands run.
- ``slice_review`` — the OTHER model reviews a slice. Status must be
                     one of slice_accepted / slice_rejected.
- ``phase_done``   — terminal: this phase is fully complete. Requires
                     a prior slice_review with status=slice_accepted
                     from the non-primary model.

Status values (per event kind)
------------------------------

- ack_start:    in_progress
- slice_update: ready_for_review | blocked | abandoned
- slice_review: slice_accepted | slice_rejected | slice_revisions_requested
- phase_done:   phase_complete

Confidence labels
-----------------

Mirror ``docs/llm_pairing_rules.md`` rule #4:

- ``repo-proven``    — claim is verifiable against the actual source or a
                       runnable test. Only repo-proven satisfies the
                       mutual-verification gate.
- ``memory-derived`` — recalled from memory files / prior sessions.
- ``judgment``       — opinion / extrapolation.

A phase only becomes ``phase_complete`` when at least ONE slice_review row
from the non-primary model carries ``confidence=repo-proven`` AND status
``slice_accepted``.

CLI
---

``python -m tools.debugger.handoff_log add --phase P0 --event ack_start
--model claude --primary claude --status in_progress --confidence
repo-proven --claim "<claim>"``

``python -m tools.debugger.handoff_log list [--phase P0] [--status ...]``

``python -m tools.debugger.handoff_log show <phase>``

``python -m tools.debugger.handoff_log verify [--phase P0]`` — runs the
audit checks against the store.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from .catalog import ROOT


DEFAULT_STORE = Path("audit") / "masterpiece_handoff_log.jsonl"

EVENT_KINDS = ("ack_start", "slice_update", "slice_review", "phase_done")
CONFIDENCE_LABELS = ("repo-proven", "memory-derived", "judgment")
GATE_VALID_LABELS = frozenset({"repo-proven"})
KNOWN_MODELS = ("claude", "codex")
SOLO_CODEX_APPROVAL_KEY = "solo_codex_approved_by_cole"
SOLO_CLAUDE_APPROVAL_KEY = "solo_claude_approved_by_cole"

STATUS_BY_EVENT = {
    "ack_start": frozenset({"in_progress"}),
    "slice_update": frozenset({"ready_for_review", "blocked", "abandoned"}),
    "slice_review": frozenset(
        {"slice_accepted", "slice_rejected", "slice_revisions_requested"}
    ),
    "phase_done": frozenset({"phase_complete"}),
}

ACCEPT_STATUSES = frozenset({"slice_accepted", "phase_complete"})

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class HandoffRow:
    phase: str
    event: str
    status: str
    model: str
    confidence: str
    claim: str
    primary: str = ""
    reviewer: str = ""
    files_changed: tuple[str, ...] = ()
    files_read: tuple[str, ...] = ()
    write_set: tuple[str, ...] = ()
    safe_write_set_for_other: tuple[str, ...] = ()
    collision_risk_files: tuple[str, ...] = ()
    verification: tuple[str, ...] = ()
    verification_replayed: tuple[str, ...] = ()
    accepted_pushbacks: tuple[str, ...] = ()
    next_recommended_slice: str = ""
    mutual_done_status: str = ""
    citations: tuple[str, ...] = ()
    slice_id: str = ""
    signed_at: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "phase": self.phase,
            "event": self.event,
            "status": self.status,
            "model": self.model,
            "confidence": self.confidence,
            "claim": self.claim,
            "signed_at": self.signed_at or now_iso(),
        }
        if self.primary:
            out["primary"] = self.primary
        if self.reviewer:
            out["reviewer"] = self.reviewer
        if self.slice_id:
            out["slice_id"] = self.slice_id
        if self.files_changed:
            out["files_changed"] = list(self.files_changed)
        if self.files_read:
            out["files_read"] = list(self.files_read)
        if self.write_set:
            out["write_set"] = list(self.write_set)
        if self.safe_write_set_for_other:
            out["safe_write_set_for_other"] = list(self.safe_write_set_for_other)
        if self.collision_risk_files:
            out["collision_risk_files"] = list(self.collision_risk_files)
        if self.verification:
            out["verification"] = list(self.verification)
        if self.verification_replayed:
            out["verification_replayed"] = list(self.verification_replayed)
        if self.accepted_pushbacks:
            out["accepted_pushbacks"] = list(self.accepted_pushbacks)
        if self.next_recommended_slice:
            out["next_recommended_slice"] = self.next_recommended_slice
        if self.mutual_done_status:
            out["mutual_done_status"] = self.mutual_done_status
        if self.citations:
            out["citations"] = list(self.citations)
        for key, value in self.extra.items():
            if key in out:
                continue
            out[key] = value
        return out


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_row(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for required in ("phase", "event", "status", "model", "confidence", "claim"):
        if not row.get(required):
            errors.append(f"missing required field: {required}")
    event = row.get("event", "")
    if event and event not in EVENT_KINDS:
        errors.append(f"event {event!r} not in {EVENT_KINDS}")
    confidence = row.get("confidence", "")
    if confidence and confidence not in CONFIDENCE_LABELS:
        errors.append(
            f"confidence {confidence!r} not in {CONFIDENCE_LABELS}"
        )
    status = row.get("status", "")
    if event in STATUS_BY_EVENT and status not in STATUS_BY_EVENT[event]:
        errors.append(
            f"status {status!r} not valid for event {event!r}; expected one of "
            f"{sorted(STATUS_BY_EVENT[event])}"
        )
    if event == "slice_review" and not row.get("reviewer"):
        errors.append("slice_review row missing 'reviewer'")
    model = row.get("model", "")
    if model and model not in KNOWN_MODELS:
        # Not fatal — extensible — but warned.
        errors.append(
            f"model {model!r} not in known set {KNOWN_MODELS}; "
            "extend KNOWN_MODELS in handoff_log.py to silence"
        )
    return errors


LEGACY_EVENT_PREFIXES = ("claude_", "codex_")
LEGACY_MODEL_MAP = {
    "claude-opus-4-7[1m]": "claude",
    "claude-opus-4-7": "claude",
    "claude-sonnet-4-6": "claude",
    "5.5 Extra High": "codex",
}


def normalize_legacy_row(row: dict[str, Any]) -> dict[str, Any]:
    """Translate pre-schema rows so the typed gate can audit them.

    The first three rows in audit/masterpiece_handoff_log.jsonl were
    written before this module formalized the schema. They use
    model-prefixed events ("codex_ack_start") and long-form model
    strings ("claude-opus-4-7[1m]"). Append-only invariant means we
    cannot rewrite the file; instead we normalize on read.

    Idempotent: rows already carrying schema_version are returned
    unchanged.
    """

    if row.get("schema_version"):
        return row
    event = row.get("event", "")
    for prefix in LEGACY_EVENT_PREFIXES:
        if event.startswith(prefix):
            row["event"] = event[len(prefix):]
            break
    model = row.get("model", "")
    if model in LEGACY_MODEL_MAP:
        row["model"] = LEGACY_MODEL_MAP[model]
    legacy_status_map = {
        "slice_accepted_partial_P0": "slice_accepted",
        "ready_for_claude_review": "ready_for_review",
        "ready_for_codex_review": "ready_for_review",
    }
    status = row.get("status", "")
    if status in legacy_status_map:
        row["status"] = legacy_status_map[status]
    return row


def load_rows(store: Path) -> list[dict[str, Any]]:
    if not store.exists():
        return []
    rows: list[dict[str, Any]] = []
    with store.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{store}:{line_no}: invalid JSON: {exc}"
                ) from exc
            row = normalize_legacy_row(row)
            row["_line"] = line_no
            rows.append(row)
    return rows


def append_row(row: HandoffRow, *, store: Path = DEFAULT_STORE, root: Path = ROOT) -> Path:
    target = store if store.is_absolute() else (root / store)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = row.as_dict()
    errors = validate_row(payload)
    if errors:
        raise ValueError("invalid handoff row:\n  " + "\n  ".join(errors))
    with target.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, separators=(",", ":")) + "\n")
    return target


def rows_for_phase(rows: Sequence[dict[str, Any]], phase: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("phase") == phase]


def is_mutual_verified(rows: Sequence[dict[str, Any]], phase: str) -> tuple[bool, list[str]]:
    """Return (verified, reasons). reasons is non-empty when not verified."""

    phase_rows = rows_for_phase(rows, phase)
    if not phase_rows:
        return False, [f"no rows for phase {phase!r}"]
    primary_models = {row.get("primary", "") for row in phase_rows if row.get("primary")}
    if len(primary_models) > 1:
        return False, [
            f"phase {phase!r} has conflicting primary models: "
            f"{sorted(primary_models)}"
        ]
    primary = next(iter(primary_models), "")
    if not primary:
        return False, [f"phase {phase!r} has no row declaring a primary"]
    if any(row.get("status") == "slice_rejected" for row in phase_rows):
        return False, [f"phase {phase!r} has at least one slice_rejected row"]
    primary_acked = any(
        row.get("event") == "ack_start"
        and row.get("model") == primary
        and row.get("status") == "in_progress"
        for row in phase_rows
    )
    if not primary_acked:
        return False, [
            f"phase {phase!r} missing ack_start from primary={primary!r}"
        ]
    primary_finished = any(
        row.get("event") == "slice_update"
        and row.get("model") == primary
        and row.get("status") == "ready_for_review"
        for row in phase_rows
    )
    if not primary_finished:
        return False, [
            f"phase {phase!r} missing slice_update status=ready_for_review "
            f"from primary={primary!r}"
        ]
    other_signed = any(
        row.get("event") == "slice_review"
        and row.get("model") != primary
        and row.get("status") in ACCEPT_STATUSES
        and row.get("confidence") in GATE_VALID_LABELS
        for row in phase_rows
    )
    # Cole-approved solo continuations are still explicit review rows; they
    # must opt in so ordinary paired phases keep the non-primary gate.
    solo_codex_signed = (
        primary == "codex"
        and any(
            row.get("event") == "slice_review"
            and row.get("model") == "codex"
            and row.get("status") in ACCEPT_STATUSES
            and row.get("confidence") in GATE_VALID_LABELS
            and row.get(SOLO_CODEX_APPROVAL_KEY) is True
            for row in phase_rows
        )
    )
    if solo_codex_signed:
        return True, []
    solo_claude_signed = (
        primary == "claude"
        and any(
            row.get("event") == "slice_review"
            and row.get("model") == "claude"
            and row.get("status") in ACCEPT_STATUSES
            and row.get("confidence") in GATE_VALID_LABELS
            and row.get(SOLO_CLAUDE_APPROVAL_KEY) is True
            for row in phase_rows
        )
    )
    if solo_claude_signed:
        return True, []
    if not other_signed:
        return False, [
            f"phase {phase!r} missing repo-proven slice_review with "
            f"status in {sorted(ACCEPT_STATUSES)} from non-primary model"
        ]
    return True, []


def audit_store(store: Path = DEFAULT_STORE, root: Path = ROOT) -> dict[str, Any]:
    target = store if store.is_absolute() else (root / store)
    rows = load_rows(target)
    row_errors: list[dict[str, Any]] = []
    for row in rows:
        errors = validate_row(row)
        if errors:
            row_errors.append({"line": row.get("_line"), "errors": errors})
    phases = sorted({row.get("phase", "") for row in rows if row.get("phase")})
    phase_status = {}
    for phase in phases:
        verified, reasons = is_mutual_verified(rows, phase)
        phase_status[phase] = {
            "mutual_verified": verified,
            "reasons": reasons,
        }
    return {
        "kind": "two_llm_handoff_log_audit",
        "schema_version": SCHEMA_VERSION,
        "store": str(target),
        "row_count": len(rows),
        "row_errors": row_errors,
        "phases": phases,
        "phase_status": phase_status,
    }


def cmd_add(args: argparse.Namespace) -> int:
    row = HandoffRow(
        phase=args.phase,
        event=args.event,
        status=args.status,
        model=args.model,
        confidence=args.confidence,
        claim=args.claim,
        primary=args.primary or "",
        reviewer=args.reviewer or "",
        files_changed=tuple(args.files_changed or ()),
        files_read=tuple(args.files_read or ()),
        write_set=tuple(args.write_set or ()),
        safe_write_set_for_other=tuple(args.safe_write_set_for_other or ()),
        collision_risk_files=tuple(args.collision_risk_files or ()),
        verification=tuple(args.verification or ()),
        verification_replayed=tuple(args.verification_replayed or ()),
        slice_id=args.slice_id or "",
    )
    target = append_row(row, store=Path(args.store) if args.store else DEFAULT_STORE)
    print(f"[handoff_log] appended {args.event} for phase={args.phase} model={args.model} -> {target}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    store = Path(args.store) if args.store else DEFAULT_STORE
    rows = load_rows(store if store.is_absolute() else (ROOT / store))
    if args.phase:
        rows = [row for row in rows if row.get("phase") == args.phase]
    if args.status:
        rows = [row for row in rows if row.get("status") == args.status]
    if args.event:
        rows = [row for row in rows if row.get("event") == args.event]
    for row in rows:
        print(
            f"line {row.get('_line'):>3}  {row.get('phase'):<6} "
            f"{row.get('event'):<14} {row.get('status'):<24} "
            f"model={row.get('model'):<6} conf={row.get('confidence'):<14} "
            f"{row.get('claim', '')[:80]}"
        )
    print(f"[handoff_log] {len(rows)} row(s)")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    store = Path(args.store) if args.store else DEFAULT_STORE
    rows = load_rows(store if store.is_absolute() else (ROOT / store))
    phase_rows = rows_for_phase(rows, args.phase)
    if not phase_rows:
        print(f"[handoff_log] no rows for phase {args.phase}", file=sys.stderr)
        return 1
    verified, reasons = is_mutual_verified(rows, args.phase)
    print(f"=== {args.phase} ===")
    print(f"mutual_verified: {verified}")
    if reasons:
        for reason in reasons:
            print(f"  reason: {reason}")
    print()
    for row in phase_rows:
        print(
            f"[{row.get('signed_at', '?')}] {row.get('event'):<14} "
            f"status={row.get('status'):<26} model={row.get('model'):<6} "
            f"primary={row.get('primary', '-'):<6} "
            f"confidence={row.get('confidence', '?'):<14}"
        )
        print(f"  claim: {row.get('claim', '')[:200]}")
        if row.get("files_changed"):
            print(f"  files_changed: {row['files_changed']}")
        if row.get("verification"):
            for line in row["verification"]:
                print(f"  verify: {line}")
        if row.get("verification_replayed"):
            for line in row["verification_replayed"]:
                print(f"  replay: {line}")
        print()
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    report = audit_store(
        store=Path(args.store) if args.store else DEFAULT_STORE,
    )
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"=== handoff log audit ===")
        print(f"store: {report['store']}")
        print(f"rows: {report['row_count']}, row_errors: {len(report['row_errors'])}")
        for re in report["row_errors"]:
            print(f"  line {re['line']}:")
            for err in re["errors"]:
                print(f"    - {err}")
        print()
        for phase in report["phases"]:
            status = report["phase_status"][phase]
            mark = "PASS" if status["mutual_verified"] else "PENDING"
            print(f"{mark}: {phase} mutual_verified={status['mutual_verified']}")
            for reason in status["reasons"]:
                print(f"  reason: {reason}")
    has_row_errors = bool(report["row_errors"])
    return 1 if has_row_errors else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger.handoff_log",
        description="Two-LLM handoff log for Claude+Codex partnership.",
    )
    parser.add_argument("--store", default="", help="Override store path.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("add", help="Append a row.")
    add.add_argument("--phase", required=True)
    add.add_argument("--event", required=True, choices=EVENT_KINDS)
    add.add_argument("--status", required=True)
    add.add_argument("--model", required=True, choices=KNOWN_MODELS)
    add.add_argument("--primary", default="")
    add.add_argument("--reviewer", default="")
    add.add_argument("--confidence", required=True, choices=CONFIDENCE_LABELS)
    add.add_argument("--claim", required=True)
    add.add_argument("--slice-id", dest="slice_id", default="")
    add.add_argument("--files-changed", nargs="*", dest="files_changed")
    add.add_argument("--files-read", nargs="*", dest="files_read")
    add.add_argument("--write-set", nargs="*", dest="write_set")
    add.add_argument(
        "--safe-write-set-other", nargs="*", dest="safe_write_set_for_other"
    )
    add.add_argument("--collision-risk", nargs="*", dest="collision_risk_files")
    add.add_argument("--verification", nargs="*")
    add.add_argument(
        "--verification-replayed", nargs="*", dest="verification_replayed"
    )
    add.set_defaults(func=cmd_add)

    ls = sub.add_parser("list", help="List rows.")
    ls.add_argument("--phase", default="")
    ls.add_argument("--status", default="")
    ls.add_argument("--event", default="", choices=("",) + EVENT_KINDS)
    ls.set_defaults(func=cmd_list)

    show = sub.add_parser("show", help="Show a phase with mutual-verified status.")
    show.add_argument("phase")
    show.set_defaults(func=cmd_show)

    verify = sub.add_parser("verify", help="Audit the store.")
    verify.add_argument("--json", action="store_true")
    verify.set_defaults(func=cmd_verify)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
