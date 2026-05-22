#!/usr/bin/env python3
"""Bug-localization context packet (P5).

`debugger pack --hypothesis <id>` emits a structured packet sized for a
single LLM turn: the folded hypothesis state, citations, recent
verifications, plus a markdown rendering. First slice intentionally
ships the minimum surface (hypothesis read-back + markdown/JSON
emission); later slices add taint/slicing spans, effect-trace
neighbors, per-LLM punchline-first framing, and token-budget
enforcement.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .catalog import ROOT
from .hypothesis_tracker import detect_citation_drift, fold_history, load_events


SCHEMA_VERSION = 1
DEFAULT_MAX_TOKENS = 4000
SUPPORTED_TARGETS = ("claude", "codex")


def estimate_token_count(text: str) -> int:
    """Rough token estimate: 4 characters ≈ 1 token. Pessimistic enough
    for budget enforcement; not a substitute for a real tokenizer."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def build_context_packet(
    hypothesis_id: str,
    *,
    target: str = "claude",
    max_tokens: int = DEFAULT_MAX_TOKENS,
    root: Path = ROOT,
    store: Path | None = None,
) -> dict[str, Any]:
    target_normalized = target.lower().strip()
    if target_normalized not in SUPPORTED_TARGETS:
        target_normalized = "claude"

    errors: list[str] = []
    try:
        events = load_events(store=store, root=root)
    except FileNotFoundError as exc:
        events = []
        errors.append(f"hypothesis store unavailable: {exc}")

    folded: dict[str, Any] | None = None
    if not errors:
        try:
            folded = fold_history(events, hypothesis_id)
        except KeyError:
            errors.append(f"hypothesis {hypothesis_id!r} not found in store")

    if folded is None:
        markdown = _render_missing_markdown(hypothesis_id, errors)
        token_count = estimate_token_count(markdown)
        return {
            "kind": "unified_debugger_context_packet",
            "schema_version": SCHEMA_VERSION,
            "valid": False,
            "hypothesis_id": hypothesis_id,
            "target": target_normalized,
            "max_tokens": int(max_tokens),
            "token_count": token_count,
            "within_budget": token_count <= int(max_tokens),
            "errors": errors,
            "markdown": markdown,
            "structured": {
                "hypothesis_id": hypothesis_id,
                "errors": errors,
            },
        }

    drift_reports = detect_citation_drift(folded, root=root)
    citation_stale = bool(folded.get("citation_stale"))

    structured = _structured_payload(folded, target=target_normalized, drift_reports=drift_reports)
    markdown = _render_markdown(
        folded,
        target=target_normalized,
        drift_reports=drift_reports,
    )
    token_count = estimate_token_count(markdown)

    return {
        "kind": "unified_debugger_context_packet",
        "schema_version": SCHEMA_VERSION,
        "valid": True,
        "hypothesis_id": folded["id"],
        "target": target_normalized,
        "max_tokens": int(max_tokens),
        "token_count": token_count,
        "within_budget": token_count <= int(max_tokens),
        "citation_stale": citation_stale,
        "status": folded.get("status", "open"),
        "errors": errors,
        "markdown": markdown,
        "structured": structured,
    }


def _structured_payload(
    folded: dict[str, Any],
    *,
    target: str,
    drift_reports: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    drift_by_citation = {
        str(report.get("citation")): report
        for report in (drift_reports or [])
        if report.get("citation") is not None
    }
    citations: list[dict[str, Any]] = []
    for cite in folded.get("citations", []):
        raw = str(cite)
        path, _, line_text = raw.partition(":")
        line: int | None
        try:
            line = int(line_text) if line_text else None
        except ValueError:
            line = None
        report = drift_by_citation.get(raw)
        citations.append({
            "path": path,
            "line": line,
            "resolved": not report or report.get("ok", True),
            "reason": (report or {}).get("reason", ""),
        })
    verifications = [
        {
            "verdict": ev.get("verdict", ""),
            "notes": ev.get("notes", ""),
            "created_at": ev.get("created_at", ""),
        }
        for ev in folded.get("history", [])
        if ev.get("kind") == "verification"
    ]
    return {
        "hypothesis_id": folded.get("id", ""),
        "target": target,
        "status": folded.get("status", "open"),
        "symptom": folded.get("symptom", ""),
        "claim": folded.get("claim", ""),
        "confidence": folded.get("confidence", ""),
        "citations": citations,
        "citation_stale": bool(folded.get("citation_stale")),
        "verifications": verifications,
        "blocked_pass_count": int(folded.get("blocked_pass_count", 0) or 0),
        "session_id": folded.get("session_id", ""),
        "notes": folded.get("notes", ""),
    }


def _render_markdown(
    folded: dict[str, Any],
    *,
    target: str,
    drift_reports: Sequence[dict[str, Any]] = (),
) -> str:
    stale_citations = {
        str(report.get("citation"))
        for report in drift_reports
        if report.get("citation") is not None and not report.get("ok", True)
    }
    lines: list[str] = []
    lines.append(f"# Hypothesis context packet — {folded.get('id', '')}")
    lines.append("")
    lines.append(f"- Target reader: {target}")
    lines.append(f"- Status: {folded.get('status', 'open')}")
    lines.append(f"- Confidence: {folded.get('confidence', '')}")
    if folded.get("citation_stale"):
        lines.append("- Citation drift: YES — at least one cited path no longer resolves")
    blocked = int(folded.get("blocked_pass_count", 0) or 0)
    if blocked:
        lines.append(f"- Blocked passes: {blocked} (verification declined under weak grounding)")
    lines.append("")
    symptom = (folded.get("symptom") or "").strip()
    if symptom:
        lines.append("## Symptom")
        lines.append("")
        lines.append(symptom)
        lines.append("")
    claim = (folded.get("claim") or "").strip()
    if claim:
        lines.append("## Current claim")
        lines.append("")
        lines.append(claim)
        lines.append("")
    citations = folded.get("citations") or []
    if citations:
        lines.append("## Citations")
        lines.append("")
        for cite in citations:
            lines.append(
                f"- {_format_citation(cite, stale=str(cite) in stale_citations)}"
            )
        lines.append("")
    verifications = [ev for ev in folded.get("history", []) if ev.get("kind") == "verification"]
    if verifications:
        lines.append("## Verifications")
        lines.append("")
        for ev in verifications[-5:]:
            verdict = ev.get("verdict") or "?"
            notes = (ev.get("notes") or "").strip()
            stamp = ev.get("created_at") or ""
            lines.append(f"- [{verdict}] {stamp} {notes}".rstrip())
        lines.append("")
    notes = (folded.get("notes") or "").strip()
    if notes:
        lines.append("## Notes")
        lines.append("")
        lines.append(notes)
        lines.append("")
    lines.append("## Next action")
    lines.append("")
    lines.append(
        "(First-slice scaffolding: taint/slicing spans, effect-trace "
        "neighbors, and per-LLM punchline-first framing land in P5 "
        "follow-up slices.)"
    )
    return "\n".join(lines).rstrip() + "\n"


def _format_citation(cite: Any, *, stale: bool = False) -> str:
    if isinstance(cite, dict):
        path = str(cite.get("path") or "")
        line = cite.get("line")
        suffix = ":" + str(line) if line not in (None, "", 0) else ""
        marker = " (stale)" if stale or not cite.get("resolved", True) else ""
        return f"{path}{suffix}{marker}"
    marker = " (stale)" if stale else ""
    return f"{cite}{marker}"


def _render_missing_markdown(hypothesis_id: str, errors: Sequence[str]) -> str:
    lines = [f"# Hypothesis context packet — {hypothesis_id}", ""]
    lines.append("Status: NOT FOUND")
    lines.append("")
    for err in errors:
        lines.append(f"- {err}")
    if not errors:
        lines.append(
            f"- hypothesis {hypothesis_id!r} not found in the hypothesis tracker store"
        )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger.context_packet",
        description=(
            "Emit a bug-localization context packet for a single hypothesis "
            "(P5). First slice ships the folded hypothesis read-back plus "
            "markdown/JSON emission; richer integration lands in follow-ups."
        ),
    )
    parser.add_argument("--hypothesis", required=True, help="hypothesis id (claim event id)")
    parser.add_argument(
        "--target",
        choices=SUPPORTED_TARGETS,
        default="claude",
        help="reader LLM the packet is framed for (default: claude)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"token budget for the rendered packet (default: {DEFAULT_MAX_TOKENS})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit JSON instead of the markdown rendering",
    )
    parser.add_argument(
        "--store",
        type=Path,
        default=None,
        help="override hypothesis tracker store path (default: project store)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    packet = build_context_packet(
        args.hypothesis,
        target=args.target,
        max_tokens=args.max_tokens,
        store=args.store,
    )

    if args.json:
        print(json.dumps(packet, sort_keys=True))
    else:
        sys.stdout.write(packet["markdown"])

    return 0 if packet.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
