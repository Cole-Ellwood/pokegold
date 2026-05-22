"""When-wrote: omniscient last-writer query for the unified debugger.

P2 first slice. Thin wrapper over reverse_query that exposes the
single-question primitive the AG-NN-class workflow reaches for:

    python -m tools.debugger when-wrote --address D141 \
        --trace .local/tmp/golden/wild_floor.jsonl

Returns the last write to the address before optional anchors:

- ``--since-symbol X`` — anchor at first PC entry matching X.
- ``--since-frame N``  — anchor at instruction frame seq >= N.

Output carries the GPT-5.5 proof vector verbatim: writer PC + symbol
+ bank + frame + ``proof_status`` + ``match_precision``. The query
refuses bus-address fallback for banked targets per the P0 work in
reverse_query — when no exact bank-key match is found, the result
returns no writer and emits the explicit downgrade reason.

For deeper queries (predicates, between-spans, multi-target),
delegate to the ``tdb`` query language (P3) once it lands.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .catalog import ROOT
from .reverse_query import build_reverse_query_report


@dataclass(frozen=True)
class WhenWroteAnswer:
    target_label: str
    proof_status: str
    last_writer: dict[str, Any]
    match_precision: str
    proof_downgrade_reason: str
    address_key: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "unified_debugger_when_wrote_answer",
            "target_label": self.target_label,
            "proof_status": self.proof_status,
            "last_writer": dict(self.last_writer),
            "match_precision": self.match_precision,
            "proof_downgrade_reason": self.proof_downgrade_reason,
            "address_key": self.address_key,
        }


def run_when_wrote(
    *,
    addresses: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    traces: tuple[str, ...] = (),
    reports: tuple[str, ...] = (),
    symbols_path: str = "pokegold.sym",
    since_symbol: str = "",
    since_frame: int = 0,
    watch_size: int = 1,
    max_history: int = 12,
    root: Path = ROOT,
) -> dict[str, Any]:
    report = build_reverse_query_report(
        reports=reports,
        traces=traces,
        symbols=symbols,
        addresses=addresses,
        symbols_path=symbols_path,
        watch_size=watch_size,
        max_history=max_history,
        root=root,
    )
    answers = [
        _filter_to_when_wrote_answer(result, since_symbol=since_symbol, since_frame=since_frame)
        for result in report.get("results", [])
    ]
    return {
        "schema_version": 1,
        "kind": "unified_debugger_when_wrote",
        "root": str(root),
        "valid": report.get("valid", False),
        "errors": report.get("errors", []),
        "since_symbol": since_symbol,
        "since_frame": since_frame,
        "answer_count": len(answers),
        "answers": [answer.as_dict() for answer in answers],
        "known_limits": [
            "when-wrote is exact only for the supplied instruction/effect window (inherits reverse_query's bound).",
            "Banked targets require exact bank-aware key matches; no bus-address fallback (P0 proof boundary).",
            "--since-symbol / --since-frame filter the LAST writer up to the anchor; pre-anchor evidence outside the trace window is unknown.",
            "For richer between-span or predicate queries, use the tdb query language (P3) once it lands.",
        ],
    }


def _filter_to_when_wrote_answer(
    result: dict[str, Any],
    *,
    since_symbol: str,
    since_frame: int,
) -> WhenWroteAnswer:
    target_label = str(result.get("target", {}).get("label") or "")
    last_writer = result.get("last_writer") or {}
    proof_status = str(result.get("proof_status") or "planned_only")
    match_precision = str(result.get("match_precision") or "")
    downgrade_reason = str(result.get("proof_downgrade_reason") or "")
    address_key = str(
        result.get("matched_address_key")
        or result.get("target", {}).get("address_key")
        or result.get("matched_address")
        or ""
    )

    if isinstance(last_writer, dict) and (since_symbol or since_frame > 0):
        writer_pc_label = str(last_writer.get("pc_label") or "")
        writer_seq = int(last_writer.get("seq") or 0)
        if since_symbol and writer_pc_label and not writer_pc_label.startswith(since_symbol):
            last_writer = {}
            downgrade_reason = downgrade_reason or "writer_pc_does_not_match_since_symbol"
            proof_status = "planned_only"
        if since_frame > 0 and writer_seq and writer_seq < since_frame:
            last_writer = {}
            downgrade_reason = downgrade_reason or "writer_seq_before_since_frame"
            proof_status = "planned_only"

    return WhenWroteAnswer(
        target_label=target_label,
        proof_status=proof_status,
        last_writer=last_writer if isinstance(last_writer, dict) else {},
        match_precision=match_precision,
        proof_downgrade_reason=downgrade_reason,
        address_key=address_key,
    )


def _format_text(answer_report: dict[str, Any]) -> str:
    lines: list[str] = ["unified debugger when-wrote"]
    if not answer_report.get("valid"):
        lines.append("status: invalid")
        for err in answer_report.get("errors", []):
            lines.append(f"  error: {err}")
        return "\n".join(lines)
    for answer in answer_report.get("answers", []):
        lines.append("")
        lines.append(f"target: {answer.get('target_label') or '<unnamed>'}")
        lines.append(f"  address_key: {answer.get('address_key') or '?'}")
        lines.append(f"  proof_status: {answer.get('proof_status')}")
        lines.append(f"  match_precision: {answer.get('match_precision') or '-'}")
        if answer.get("proof_downgrade_reason"):
            lines.append(f"  proof_downgrade_reason: {answer['proof_downgrade_reason']}")
        writer = answer.get("last_writer") or {}
        if writer:
            lines.append("  last_writer:")
            for key in ("seq", "pc_bank_address", "pc_label", "value_hex", "operation", "trace_source"):
                value = writer.get(key)
                if value not in (None, "", 0):
                    lines.append(f"    {key}: {value}")
        else:
            lines.append("  last_writer: <none in supplied window>")
    if not answer_report.get("answers"):
        lines.append("no answer (no targets resolved)")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger.when_wrote",
        description=(
            "Omniscient last-writer query for a watched address. Wraps the "
            "reverse-query machinery with a single-question CLI; refuses "
            "bus-address fallback for banked targets per the P0 proof boundary."
        ),
    )
    parser.add_argument(
        "--address",
        action="append",
        default=[],
        help="Watched address (hex, e.g. D141 or wramx:01:D141). Repeatable.",
    )
    parser.add_argument(
        "--symbol",
        action="append",
        default=[],
        help="Watched symbol (resolved via --symbols). Repeatable.",
    )
    parser.add_argument(
        "--trace",
        action="append",
        default=[],
        help="Instruction trace JSONL to drive the synthesized effect trace.",
    )
    parser.add_argument(
        "--report",
        action="append",
        default=[],
        help="Existing effect-trace report JSON (skip trace synthesis).",
    )
    parser.add_argument("--symbols", default="pokegold.sym")
    parser.add_argument(
        "--since-symbol",
        default="",
        help="Anchor: ignore writers whose pc_label does not start with this symbol.",
    )
    parser.add_argument(
        "--since-frame",
        type=int,
        default=0,
        help="Anchor: ignore writers with seq < this frame index.",
    )
    parser.add_argument("--watch-size", type=int, default=1)
    parser.add_argument("--max-history", type=int, default=12)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args(argv)

    if not (args.address or args.symbol):
        print("error: pass --address or --symbol at least once", file=sys.stderr)
        return 2

    answer_report = run_when_wrote(
        addresses=tuple(args.address),
        symbols=tuple(args.symbol),
        traces=tuple(args.trace),
        reports=tuple(args.report),
        symbols_path=args.symbols,
        since_symbol=args.since_symbol,
        since_frame=args.since_frame,
        watch_size=args.watch_size,
        max_history=args.max_history,
    )
    if args.json:
        print(json.dumps(answer_report, indent=2))
    else:
        print(_format_text(answer_report))
    return 0 if answer_report.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
