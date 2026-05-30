"""Persistent investigation tracker for the unified debugger.

V0 scope: persist hypotheses across debugger sessions with citation
grounding on `repo-proven` claims. No autonomous hypothesis generation;
the LLM proposes and verifies, this module records and validates.

Store layout
------------

Append-only JSONL at ``audit/hypothesis_tree.jsonl``. Each row is one
event in the investigation history. Rows form a tree via ``parent_id``.

Event kinds:

- ``claim``        — a new root hypothesis or branch root.
- ``refinement``   — amend an existing hypothesis (text, confidence,
                     additional citations).
- ``verification`` — record running a command/test against a hypothesis
                     with an expected result and a verdict.
- ``rejection``    — mark a hypothesis refuted with a reason.

The latest event for an id determines current status; earlier events are
preserved so the investigation history is auditable.

Confidence labels
-----------------

- ``repo-proven``    — REQUIRES at least one ``path:line`` citation
                       pointing at a real file at the time of recording.
                       Only repo-proven claims satisfy a verification
                       gate on their own.
- ``memory-derived`` — may carry citations but does not require them.
                       Never satisfies a verification gate alone.
- ``judgment``       — opinion / extrapolation. Same gate semantics as
                       memory-derived.

Citation form
-------------

``relative/path/from/repo/root:LINE``. Forward slashes; line is
1-indexed. Validated at add-time; stale citations (file missing or line
out of range) are flagged at list/show time without mutating the stored
row (append-only invariant).

This module is import-friendly and is wired into the front door as
``python -m tools.debugger hypothesis`` (v2 passthrough); also callable
directly as ``python -m tools.debugger.hypothesis_tracker``.
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from .catalog import ROOT


DEFAULT_STORE = Path("audit") / "hypothesis_tree.jsonl"

EVENT_KINDS = ("claim", "refinement", "verification", "rejection")
CONFIDENCE_LABELS = ("repo-proven", "memory-derived", "judgment")
GATE_VALID_LABELS = frozenset({"repo-proven"})
TERMINAL_STATUSES = frozenset({"verified", "refuted"})


@dataclass(frozen=True)
class Citation:
    path: str
    line: int

    @classmethod
    def parse(cls, raw: str) -> "Citation":
        text = raw.strip()
        if ":" not in text:
            raise ValueError(
                f"citation {raw!r} must be path:line (forward-slash path, 1-indexed line)"
            )
        path_part, _, line_part = text.rpartition(":")
        if not path_part or not line_part:
            raise ValueError(f"citation {raw!r} must have both path and line")
        try:
            line = int(line_part)
        except ValueError as exc:
            raise ValueError(f"citation {raw!r} line is not an integer") from exc
        if line < 1:
            raise ValueError(f"citation {raw!r} line must be >= 1")
        # Normalize windows backslashes if the caller passed them.
        normalized = path_part.replace("\\", "/")
        return cls(path=normalized, line=line)

    def render(self) -> str:
        return f"{self.path}:{self.line}"

    def to_jsonable(self) -> str:
        return self.render()


def _now_utc_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_id(prefix: str = "h", *, clock: callable | None = None) -> str:
    """Return a sortable, human-readable id.

    Form: ``h_YYYYMMDDTHHMMSS_<8 hex>``. Random suffix makes
    same-second additions unique without coordination.
    """

    if clock is None:
        now = datetime.now(tz=timezone.utc)
    else:
        now = clock()
    moment = now.strftime("%Y%m%dT%H%M%S")
    return f"{prefix}_{moment}_{secrets.token_hex(4)}"


def validate_citation(citation: Citation, *, root: Path = ROOT) -> tuple[bool, str]:
    """Return ``(ok, reason)``. ``reason`` is empty when ok is True."""

    path = (root / citation.path).resolve()
    repo = root.resolve()
    try:
        path.relative_to(repo)
    except ValueError:
        return False, f"path {citation.path!r} resolves outside the repo root"
    if not path.exists():
        return False, f"path {citation.path!r} does not exist"
    if path.is_dir():
        return False, f"path {citation.path!r} is a directory"
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Binary file — accept if line==1 (allow citing existence) but
        # any other line is unverifiable.
        if citation.line == 1:
            return True, ""
        return False, f"path {citation.path!r} is binary; cannot resolve line {citation.line}"
    line_count = text.count("\n") + (0 if text.endswith("\n") else 1)
    if citation.line > max(1, line_count):
        return False, (
            f"path {citation.path!r} has {line_count} lines; "
            f"line {citation.line} is out of range"
        )
    return True, ""


def _coerce_citations(raw: Sequence[str] | None) -> list[Citation]:
    if not raw:
        return []
    return [Citation.parse(item) for item in raw]


def _write_event(event: dict[str, Any], *, store: Path) -> None:
    store.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(event, sort_keys=True)
    with store.open("a", encoding="utf-8") as fh:
        fh.write(serialized)
        fh.write("\n")


def _resolve_store(store: Path | None, *, root: Path) -> Path:
    if store is None:
        return root / DEFAULT_STORE
    if store.is_absolute():
        return store
    return root / store


def add_claim(
    *,
    symptom: str,
    claim: str,
    confidence: str,
    citations: Sequence[str] | None = None,
    session_id: str | None = None,
    notes: str = "",
    store: Path | None = None,
    root: Path = ROOT,
    clock: callable | None = None,
    rng_id: str | None = None,
) -> dict[str, Any]:
    """Append a new root-level claim. Returns the stored event dict."""

    if confidence not in CONFIDENCE_LABELS:
        raise ValueError(
            f"confidence {confidence!r} must be one of {CONFIDENCE_LABELS!r}"
        )
    parsed = _coerce_citations(citations)
    if confidence == "repo-proven" and not parsed:
        raise ValueError(
            "repo-proven claims require at least one path:line citation"
        )
    for cite in parsed:
        ok, reason = validate_citation(cite, root=root)
        if not ok:
            raise ValueError(f"citation {cite.render()!r} invalid: {reason}")
    event: dict[str, Any] = {
        "id": rng_id or _generate_id("h", clock=clock),
        "parent_id": None,
        "kind": "claim",
        "session_id": session_id or "",
        "symptom": symptom,
        "claim": claim,
        "confidence": confidence,
        "citations": [c.to_jsonable() for c in parsed],
        "notes": notes,
        "created_at": _now_utc_iso(),
    }
    resolved = _resolve_store(store, root=root)
    _write_event(event, store=resolved)
    return event


def add_refinement(
    *,
    parent_id: str,
    claim: str | None = None,
    confidence: str | None = None,
    citations: Sequence[str] | None = None,
    notes: str = "",
    session_id: str | None = None,
    store: Path | None = None,
    root: Path = ROOT,
    clock: callable | None = None,
    rng_id: str | None = None,
) -> dict[str, Any]:
    """Append a refinement against an existing hypothesis id."""

    if confidence is not None and confidence not in CONFIDENCE_LABELS:
        raise ValueError(
            f"confidence {confidence!r} must be one of {CONFIDENCE_LABELS!r}"
        )
    parsed = _coerce_citations(citations)
    for cite in parsed:
        ok, reason = validate_citation(cite, root=root)
        if not ok:
            raise ValueError(f"citation {cite.render()!r} invalid: {reason}")
    if confidence == "repo-proven" and not parsed:
        raise ValueError(
            "repo-proven refinements require at least one path:line citation"
        )
    event: dict[str, Any] = {
        "id": rng_id or _generate_id("h", clock=clock),
        "parent_id": parent_id,
        "kind": "refinement",
        "session_id": session_id or "",
        "claim": claim or "",
        "confidence": confidence or "",
        "citations": [c.to_jsonable() for c in parsed],
        "notes": notes,
        "created_at": _now_utc_iso(),
    }
    resolved = _resolve_store(store, root=root)
    _write_event(event, store=resolved)
    return event


def add_verification(
    *,
    parent_id: str,
    command: str,
    expected: str,
    verdict: str,
    actual: str = "",
    notes: str = "",
    session_id: str | None = None,
    store: Path | None = None,
    root: Path = ROOT,
    clock: callable | None = None,
    rng_id: str | None = None,
) -> dict[str, Any]:
    """Record a verification attempt against a hypothesis.

    ``verdict`` is one of ``pass`` | ``fail`` | ``inconclusive``. A
    ``pass`` verdict promotes the hypothesis status to ``verified``; a
    ``fail`` promotes it to ``refuted``. ``inconclusive`` leaves the
    status at ``open``.
    """

    if verdict not in {"pass", "fail", "inconclusive"}:
        raise ValueError(
            f"verdict {verdict!r} must be pass|fail|inconclusive"
        )
    event: dict[str, Any] = {
        "id": rng_id or _generate_id("v", clock=clock),
        "parent_id": parent_id,
        "kind": "verification",
        "session_id": session_id or "",
        "command": command,
        "expected": expected,
        "actual": actual,
        "verdict": verdict,
        "notes": notes,
        "created_at": _now_utc_iso(),
    }
    resolved = _resolve_store(store, root=root)
    _write_event(event, store=resolved)
    return event


def add_rejection(
    *,
    parent_id: str,
    reason: str,
    session_id: str | None = None,
    store: Path | None = None,
    root: Path = ROOT,
    clock: callable | None = None,
    rng_id: str | None = None,
) -> dict[str, Any]:
    """Mark a hypothesis refuted with an explanation."""

    if not reason.strip():
        raise ValueError("rejection requires a non-empty reason")
    event: dict[str, Any] = {
        "id": rng_id or _generate_id("x", clock=clock),
        "parent_id": parent_id,
        "kind": "rejection",
        "session_id": session_id or "",
        "reason": reason,
        "created_at": _now_utc_iso(),
    }
    resolved = _resolve_store(store, root=root)
    _write_event(event, store=resolved)
    return event


def load_events(*, store: Path | None = None, root: Path = ROOT) -> list[dict[str, Any]]:
    resolved = _resolve_store(store, root=root)
    if not resolved.exists():
        return []
    rows: list[dict[str, Any]] = []
    with resolved.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{resolved}:{line_no}: malformed JSON: {exc.msg}"
                ) from exc
    return rows


def _children_by_parent(events: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    table: dict[str, list[dict[str, Any]]] = {}
    for ev in events:
        parent = ev.get("parent_id")
        if parent is None:
            continue
        table.setdefault(parent, []).append(ev)
    for bucket in table.values():
        bucket.sort(key=lambda ev: ev.get("created_at", ""))
    return table


def fold_history(events: Sequence[dict[str, Any]], hypothesis_id: str) -> dict[str, Any]:
    """Collapse a hypothesis with all its history into a current-state dict.

    Returns a dict with:
    - ``id``, ``symptom``, ``claim``, ``confidence``, ``citations``,
      ``session_id``, ``notes``, ``created_at`` — folded current values.
    - ``status``: ``open`` | ``verified`` | ``refuted``.
    - ``history``: ordered list of events touching this hypothesis.
    - ``citation_stale``: True if any citation no longer resolves.
    - ``blocked_pass_count``: number of ``pass`` verdicts that did NOT
      promote to verified because confidence at the time of verification
      was not in ``GATE_VALID_LABELS``. Surfaces "the gate refused this"
      without polluting the status filter.

    Gate semantics are enforced at the moment of verification: a later
    refinement to repo-proven does not legitimize an earlier pass that
    ran against a memory-derived or judgment claim. V0 intentionally
    models a single investigation thread — refinements are last-write-
    wins on claim/confidence/cites, descendants are linearized in
    created_at order. Explicit branching is deferred to V1.
    """

    root_event = next((ev for ev in events if ev.get("id") == hypothesis_id and ev.get("kind") == "claim"), None)
    if root_event is None:
        raise KeyError(f"hypothesis {hypothesis_id!r} not found (must be a claim event)")

    children_table = _children_by_parent(events)
    history: list[dict[str, Any]] = [root_event]
    queue = list(children_table.get(hypothesis_id, ()))
    while queue:
        ev = queue.pop(0)
        history.append(ev)
        queue.extend(children_table.get(ev.get("id", ""), ()))
    history.sort(key=lambda ev: ev.get("created_at", ""))

    folded: dict[str, Any] = {
        "id": root_event["id"],
        "symptom": root_event.get("symptom", ""),
        "claim": root_event.get("claim", ""),
        "confidence": root_event.get("confidence", ""),
        "citations": list(root_event.get("citations", [])),
        "session_id": root_event.get("session_id", ""),
        "notes": root_event.get("notes", ""),
        "created_at": root_event.get("created_at", ""),
        "status": "open",
        "history": history,
        "citation_stale": False,
        "blocked_pass_count": 0,
    }

    # Track confidence at each step — the gate fires against the
    # confidence at the moment of verification, not retroactively. A
    # later refinement to repo-proven does NOT legitimize an earlier
    # pass that ran against a memory-derived claim.
    current_confidence = folded["confidence"]
    for ev in history[1:]:
        kind = ev.get("kind")
        if kind == "refinement":
            if ev.get("claim"):
                folded["claim"] = ev["claim"]
            if ev.get("confidence"):
                folded["confidence"] = ev["confidence"]
                current_confidence = ev["confidence"]
            extra = ev.get("citations") or []
            for cite in extra:
                if cite not in folded["citations"]:
                    folded["citations"].append(cite)
            if ev.get("notes"):
                folded["notes"] = ev["notes"]
        elif kind == "verification":
            verdict = ev.get("verdict")
            if verdict == "pass":
                if current_confidence in GATE_VALID_LABELS:
                    folded["status"] = "verified"
                else:
                    folded["blocked_pass_count"] += 1
            elif verdict == "fail":
                # Failing verifications refute regardless of grounding.
                folded["status"] = "refuted"
            # inconclusive leaves status alone
        elif kind == "rejection":
            folded["status"] = "refuted"

    return folded


def detect_citation_drift(
    folded: dict[str, Any],
    *,
    root: Path = ROOT,
) -> list[dict[str, Any]]:
    """Return a list of stale-citation reports for a folded hypothesis.

    Pure side effect: ``folded['citation_stale']`` is updated. The store
    file is NOT mutated (append-only invariant).
    """

    reports: list[dict[str, Any]] = []
    for raw in folded.get("citations", []):
        try:
            cite = Citation.parse(raw)
        except ValueError as exc:
            reports.append({"citation": raw, "ok": False, "reason": str(exc)})
            continue
        ok, reason = validate_citation(cite, root=root)
        if not ok:
            reports.append({"citation": raw, "ok": False, "reason": reason})
    folded["citation_stale"] = any(not r["ok"] for r in reports)
    return reports


def list_hypotheses(
    *,
    store: Path | None = None,
    root: Path = ROOT,
    session_id: str | None = None,
    status: str | None = None,
    confidence: str | None = None,
    symptom_contains: str | None = None,
    refresh_citations: bool = False,
) -> list[dict[str, Any]]:
    """Return folded hypotheses matching the given filters."""

    events = load_events(store=store, root=root)
    ids = [ev["id"] for ev in events if ev.get("kind") == "claim"]
    folded = [fold_history(events, hid) for hid in ids]
    if refresh_citations:
        for hyp in folded:
            detect_citation_drift(hyp, root=root)
    out: list[dict[str, Any]] = []
    for hyp in folded:
        if session_id and hyp.get("session_id") != session_id:
            continue
        if status and hyp.get("status") != status:
            continue
        if confidence and hyp.get("confidence") != confidence:
            continue
        if symptom_contains and symptom_contains.lower() not in hyp.get("symptom", "").lower():
            continue
        out.append(hyp)
    return out


def render_tree(
    events: Sequence[dict[str, Any]],
    root_id: str,
) -> str:
    """Render a single hypothesis and its descendants as an ASCII tree."""

    children_table = _children_by_parent(events)
    root_event = next((ev for ev in events if ev.get("id") == root_id), None)
    if root_event is None:
        return f"(no event with id {root_id!r})"

    lines: list[str] = []

    def label(ev: dict[str, Any]) -> str:
        kind = ev.get("kind", "?")
        if kind == "claim":
            return (
                f"[claim:{ev.get('confidence', '?')}] {ev['id']} — {ev.get('claim', '')}"
            )
        if kind == "refinement":
            return f"[refine] {ev['id']} — {ev.get('claim', '') or '(no new claim)'}"
        if kind == "verification":
            return (
                f"[verify:{ev.get('verdict', '?')}] {ev['id']} — "
                f"`{ev.get('command', '')}`"
            )
        if kind == "rejection":
            return f"[reject] {ev['id']} — {ev.get('reason', '')}"
        return f"[?] {ev['id']}"

    def walk(ev: dict[str, Any], prefix: str, is_last: bool) -> None:
        connector = "└── " if is_last else "├── "
        lines.append(prefix + connector + label(ev))
        children = children_table.get(ev.get("id", ""), [])
        next_prefix = prefix + ("    " if is_last else "│   ")
        for idx, child in enumerate(children):
            walk(child, next_prefix, idx == len(children) - 1)

    lines.append(label(root_event))
    children = children_table.get(root_id, [])
    for idx, child in enumerate(children):
        walk(child, "", idx == len(children) - 1)
    return "\n".join(lines)


def show_hypothesis(
    hypothesis_id: str,
    *,
    store: Path | None = None,
    root: Path = ROOT,
    refresh_citations: bool = True,
) -> dict[str, Any]:
    events = load_events(store=store, root=root)
    folded = fold_history(events, hypothesis_id)
    cite_reports: list[dict[str, Any]] = []
    if refresh_citations:
        cite_reports = detect_citation_drift(folded, root=root)
    return {
        "folded": folded,
        "citation_reports": cite_reports,
        "tree": render_tree(events, hypothesis_id),
    }


def _format_list(rows: Sequence[dict[str, Any]]) -> str:
    if not rows:
        return "(no hypotheses match filters)"
    out: list[str] = []
    for row in rows:
        flags: list[str] = []
        if row.get("citation_stale"):
            flags.append("STALE-CITE")
        blocked = row.get("blocked_pass_count", 0)
        if blocked:
            flags.append(f"BLOCKED-PASSES={blocked}")
        flag_str = (" [" + ", ".join(flags) + "]") if flags else ""
        out.append(
            f"{row['id']}  {row['status']:<10}  {row['confidence']:<14}  "
            f"{row['symptom']}{flag_str}"
        )
        out.append(f"  claim: {row['claim']}")
        if row.get("citations"):
            out.append(f"  cites: {', '.join(row['citations'])}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger.hypothesis_tracker",
        description=(
            "Persistent debugging-hypothesis tracker with citation grounding. "
            "Append-only JSONL at audit/hypothesis_tree.jsonl."
        ),
    )
    parser.add_argument(
        "--store",
        type=Path,
        default=None,
        help="override store path (default: audit/hypothesis_tree.jsonl)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="record a new claim")
    p_add.add_argument("--symptom", required=True)
    p_add.add_argument("--claim", required=True)
    p_add.add_argument(
        "--confidence",
        choices=CONFIDENCE_LABELS,
        required=True,
    )
    p_add.add_argument("--citation", action="append", default=[])
    p_add.add_argument("--session-id", default="")
    p_add.add_argument("--notes", default="")
    p_add.set_defaults(func=_cmd_add)

    p_refine = sub.add_parser("refine", help="amend an existing hypothesis")
    p_refine.add_argument("parent_id")
    p_refine.add_argument("--claim", default=None)
    p_refine.add_argument(
        "--confidence",
        choices=CONFIDENCE_LABELS,
        default=None,
    )
    p_refine.add_argument("--citation", action="append", default=[])
    p_refine.add_argument("--session-id", default="")
    p_refine.add_argument("--notes", default="")
    p_refine.set_defaults(func=_cmd_refine)

    p_verify = sub.add_parser("verify", help="record a verification attempt")
    p_verify.add_argument("parent_id")
    p_verify.add_argument("--command", required=True)
    p_verify.add_argument("--expected", required=True)
    p_verify.add_argument(
        "--verdict",
        choices=("pass", "fail", "inconclusive"),
        required=True,
    )
    p_verify.add_argument("--actual", default="")
    p_verify.add_argument("--session-id", default="")
    p_verify.add_argument("--notes", default="")
    p_verify.set_defaults(func=_cmd_verify)

    p_reject = sub.add_parser("reject", help="mark a hypothesis refuted")
    p_reject.add_argument("parent_id")
    p_reject.add_argument("--reason", required=True)
    p_reject.add_argument("--session-id", default="")
    p_reject.set_defaults(func=_cmd_reject)

    p_list = sub.add_parser("list", help="list hypotheses")
    p_list.add_argument("--session-id", default=None)
    p_list.add_argument("--status", choices=("open", "verified", "refuted"), default=None)
    p_list.add_argument("--confidence", choices=CONFIDENCE_LABELS, default=None)
    p_list.add_argument("--symptom-contains", default=None)
    p_list.add_argument("--refresh-citations", action="store_true")
    p_list.add_argument("--json", action="store_true")
    p_list.set_defaults(func=_cmd_list)

    p_show = sub.add_parser("show", help="show one hypothesis with history + tree")
    p_show.add_argument("hypothesis_id")
    p_show.add_argument("--json", action="store_true")
    p_show.set_defaults(func=_cmd_show)

    p_tree = sub.add_parser("tree", help="render the descendants of a hypothesis as an ASCII tree")
    p_tree.add_argument("hypothesis_id")
    p_tree.set_defaults(func=_cmd_tree)

    return parser


def _cmd_add(args: argparse.Namespace) -> int:
    event = add_claim(
        symptom=args.symptom,
        claim=args.claim,
        confidence=args.confidence,
        citations=args.citation,
        session_id=args.session_id or None,
        notes=args.notes,
        store=args.store,
    )
    print(json.dumps(event, sort_keys=True))
    return 0


def _cmd_refine(args: argparse.Namespace) -> int:
    event = add_refinement(
        parent_id=args.parent_id,
        claim=args.claim,
        confidence=args.confidence,
        citations=args.citation,
        session_id=args.session_id or None,
        notes=args.notes,
        store=args.store,
    )
    print(json.dumps(event, sort_keys=True))
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    event = add_verification(
        parent_id=args.parent_id,
        command=args.command,
        expected=args.expected,
        verdict=args.verdict,
        actual=args.actual,
        session_id=args.session_id or None,
        notes=args.notes,
        store=args.store,
    )
    print(json.dumps(event, sort_keys=True))
    return 0


def _cmd_reject(args: argparse.Namespace) -> int:
    event = add_rejection(
        parent_id=args.parent_id,
        reason=args.reason,
        session_id=args.session_id or None,
        store=args.store,
    )
    print(json.dumps(event, sort_keys=True))
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    rows = list_hypotheses(
        store=args.store,
        session_id=args.session_id,
        status=args.status,
        confidence=args.confidence,
        symptom_contains=args.symptom_contains,
        refresh_citations=args.refresh_citations,
    )
    if args.json:
        print(json.dumps(rows, sort_keys=True))
    else:
        print(_format_list(rows))
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    info = show_hypothesis(args.hypothesis_id, store=args.store)
    if args.json:
        print(json.dumps(info, sort_keys=True))
    else:
        folded = info["folded"]
        print(f"id:         {folded['id']}")
        print(f"status:     {folded['status']}")
        print(f"confidence: {folded['confidence']}")
        print(f"symptom:    {folded['symptom']}")
        print(f"claim:      {folded['claim']}")
        if folded.get("citations"):
            print(f"cites:      {', '.join(folded['citations'])}")
        if info["citation_reports"]:
            stale = [r for r in info["citation_reports"] if not r["ok"]]
            if stale:
                print("STALE CITATIONS:")
                for r in stale:
                    print(f"  - {r['citation']}: {r['reason']}")
        print("\ntree:")
        print(info["tree"])
    return 0


def _cmd_tree(args: argparse.Namespace) -> int:
    events = load_events(store=args.store)
    print(render_tree(events, args.hypothesis_id))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
