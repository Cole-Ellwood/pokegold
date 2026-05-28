"""Phase 1 single-trainer batch switch-materialize runner.

Per ``docs/headless_batch_validation_implementation.md`` §5 Phase 1.

The materializer in ``tools.boss_ai_debugger.rom_switch_materialize`` already
opens one PyBoy session and iterates scenarios through
``run_rom_switch_materialization_from_path``. This module is the headless-side
focus-formatted wrapper: it returns the doc-specified per-scenario table
columns (``scenario_id``, ``switch_confidence``, ``switch_roll.switch_probability``,
``switch_roll.probability_exact``, ``proof_status``, ``observation_status``)
and the summary line ``N scenarios, M observed switches, K probability_exact,
errors=E`` directly consumable by downstream tools (Phase 2 expectations
comparator, ad-hoc playtests).

This module does NOT compute live Boss AI confidence from headless boards. It
consumes ``family=switch_sack`` scenarios (produced by
``headless_to_switch_sack_scenario`` or hand-written) and reports what the ROM
actually did under those bytes. The Phase-1 deliverable is the workflow,
not new AI introspection.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from tools.boss_ai_debugger.rom_switch_materialize import (
    DEFAULT_BASE_ROUTE,
    DEFAULT_WATCH_FRAMES,
    run_rom_switch_materialization_from_path,
    write_rom_switch_materialization_json,
)
from tools.boss_ai_debugger.rom_selector_materialize import DEFAULT_MANIFEST_PATH
from tools.trace import boss_ai_trace_capture as capture


SUMMARY_TEMPLATE = (
    "Summary: {scenarios} scenarios, {observed} observed switches, "
    "{exact} probability_exact, errors={errors}"
)


def summarize_batch_switch(report: dict[str, Any]) -> dict[str, Any]:
    """Return Phase-1 summary counts on top of a materialization report.

    Counts:
    - ``scenario_count`` — total verdicts in the report (skipped/error included)
    - ``observed_switches`` — verdicts whose ROM observation reached
      ``BossAI_TrySwitch`` (i.e. ``rom.observed_switch_path`` is True)
    - ``probability_exact_count`` — verdicts where the source-mirrored final
      switch roll was reported with a single probability (no untraced bias
      range and no ranged threshold)
    - ``error_count`` — verdicts whose ``status`` is ``"error"``
    - ``skipped_count`` — verdicts whose ``status`` is ``"skipped"`` (e.g.
      unsupported scenario family)
    """
    verdicts = report.get("verdicts", [])
    observed_switch_count = 0
    probability_exact_count = 0
    error_count = 0
    skipped_count = 0
    for verdict in verdicts:
        status = verdict.get("status")
        if status == "error":
            error_count += 1
        elif status == "skipped":
            skipped_count += 1
        rom = verdict.get("rom") or {}
        if rom.get("observed_switch_path"):
            observed_switch_count += 1
        switch_roll = verdict.get("switch_roll") or {}
        if switch_roll.get("probability_exact"):
            probability_exact_count += 1
    return {
        "scenario_count": len(verdicts),
        "observed_switches": observed_switch_count,
        "probability_exact_count": probability_exact_count,
        "error_count": error_count,
        "skipped_count": skipped_count,
    }


def _confidence_text(value: Any) -> str:
    if value is None:
        return "-"
    try:
        return f"0x{int(value):02x}"
    except (TypeError, ValueError):
        return "?"


def _probability_text(switch_roll: dict[str, Any]) -> tuple[str, str]:
    if switch_roll.get("available") is False:
        reason = switch_roll.get("reason") or "unavailable"
        return f"n/a({reason})", "-"
    probability = switch_roll.get("switch_probability")
    if isinstance(probability, (int, float)):
        probability_text = f"{probability:.1%}"
    else:
        probability_text = "?"
    exact = switch_roll.get("probability_exact")
    if exact is True:
        exact_text = "yes"
    elif exact is False:
        exact_text = "no"
    else:
        exact_text = "-"
    return probability_text, exact_text


def format_batch_switch_table(
    report: dict[str, Any],
    *,
    limit: int = 50,
) -> str:
    """Render the Phase-1 per-scenario table + summary line."""
    summary = report.get("summary") or summarize_batch_switch(report)
    base_route = report.get("base_route", "?")
    base_state = report.get("base_state", "?")
    rate = report.get("materializations_per_minute", 0) or 0
    lines = [
        "Headless battle batch switch-materialize",
        f"base_route={base_route} base_state={base_state} rate={rate:.0f}/min",
        "",
        (
            f"{'scenario_id':<32} {'confidence':>10} {'switch_prob':>18} "
            f"{'exact':>5} {'proof_status':<48} {'observation_status':<40}"
        ),
    ]
    verdicts = report.get("verdicts", [])
    for verdict in verdicts[:limit]:
        scenario_id = str(verdict.get("scenario_id", "?"))[:32]
        rom = verdict.get("rom") or {}
        confidence_text = _confidence_text(rom.get("switch_confidence"))
        observation = str(rom.get("observation_status", "no_observation"))[:40]
        switch_roll = verdict.get("switch_roll") or {}
        probability_text, exact_text = _probability_text(switch_roll)
        proof = str(switch_roll.get("proof_status", "no_proof"))[:48]
        if verdict.get("status") == "error":
            reason = str(verdict.get("reason", "unknown"))
            lines.append(
                f"{scenario_id:<32} {confidence_text:>10} {probability_text:>18} "
                f"{exact_text:>5} {proof:<48} ERROR: {reason}"
            )
        elif verdict.get("status") == "skipped":
            reason = str(verdict.get("reason", "unknown"))
            lines.append(
                f"{scenario_id:<32} {confidence_text:>10} {probability_text:>18} "
                f"{exact_text:>5} {proof:<48} SKIPPED: {reason}"
            )
        else:
            lines.append(
                f"{scenario_id:<32} {confidence_text:>10} {probability_text:>18} "
                f"{exact_text:>5} {proof:<48} {observation:<40}"
            )
    if len(verdicts) > limit:
        lines.append(f"  ... ({len(verdicts) - limit} more rows truncated; raise --display-limit)")
    lines.append("")
    lines.append(
        SUMMARY_TEMPLATE.format(
            scenarios=summary["scenario_count"],
            observed=summary["observed_switches"],
            exact=summary["probability_exact_count"],
            errors=summary["error_count"],
        )
    )
    if summary.get("skipped_count"):
        lines.append(f"  ({summary['skipped_count']} scenarios skipped)")
    known_limits = report.get("known_limits") or []
    if known_limits:
        lines.append("")
        lines.append("Known limits:")
        for limit_text in known_limits:
            lines.append(f"  - {limit_text}")
    return "\n".join(lines)


def run_batch_switch_materialize(
    scenarios_path: Path,
    *,
    limit: int = 0,
    base_route: str = DEFAULT_BASE_ROUTE,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    rom: Path = capture.DEFAULT_ROM,
    symbols_path: Path = capture.DEFAULT_SYMBOLS,
    watch_frames: int = DEFAULT_WATCH_FRAMES,
    switch_threshold: Optional[int] = None,
) -> dict[str, Any]:
    """Run the batch materialization and tag the report with Phase-1 summary.

    ``limit=0`` means no cap; positive values cap the number of scenarios run.
    Delegates the heavy lifting (PyBoy session, ROM patching, observation
    sampling) to ``run_rom_switch_materialization_from_path`` which already
    opens one PyBoy session per call and iterates scenarios with cached
    base-state bytes.
    """
    report = run_rom_switch_materialization_from_path(
        scenarios_path,
        limit=limit,
        base_route=base_route,
        manifest_path=manifest_path,
        rom=rom,
        symbols_path=symbols_path,
        watch_frames=watch_frames,
        switch_threshold=switch_threshold,
    )
    report["summary"] = summarize_batch_switch(report)
    # Tag with the headless-batch kind so downstream consumers (Phase 2
    # comparator) can refuse to read a non-batch materialization report.
    report["kind"] = "headless_battle_batch_switch_materialize"
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.headless_battle.batch_switch",
        description=(
            "Run a batch of family=switch_sack scenarios through the boss-AI "
            "switch materializer in one PyBoy session. Emits per-scenario "
            "switch_confidence/switch_probability/proof_status/observation_status."
        ),
    )
    parser.add_argument(
        "--scenarios", type=Path, required=True,
        help="JSONL or JSON file with scenarios (family=switch_sack)",
    )
    parser.add_argument(
        "--limit", type=int, default=0,
        help="cap on scenarios to run (0 = no cap, default)",
    )
    parser.add_argument(
        "--base-route", default=DEFAULT_BASE_ROUTE,
        help="manifest route id for the trainer base save state",
    )
    parser.add_argument(
        "--manifest", type=Path, default=DEFAULT_MANIFEST_PATH,
        help="path to audit/boss_ai_trace/live_capture_manifest.json",
    )
    parser.add_argument("--rom", type=Path, default=Path("pokegold_trace.gbc"))
    parser.add_argument("--symbols", type=Path, default=Path("pokegold_trace.sym"))
    parser.add_argument("--watch-frames", type=int, default=DEFAULT_WATCH_FRAMES)
    parser.add_argument(
        "--switch-threshold", type=int, default=None,
        help="explicit final BossAI_TrySwitch threshold byte for exact rate",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="print full JSON report on stdout instead of the text table",
    )
    parser.add_argument(
        "--json-out", default="",
        help="write the full JSON report to a file path",
    )
    parser.add_argument(
        "--display-limit", type=int, default=50,
        help="cap on rows displayed in the text table (does not change processing)",
    )
    parser.add_argument(
        "--fail-on-error", action="store_true",
        help="exit nonzero if any scenario errored during materialization",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = run_batch_switch_materialize(
        args.scenarios,
        limit=args.limit,
        base_route=args.base_route,
        manifest_path=args.manifest,
        rom=args.rom,
        symbols_path=args.symbols,
        watch_frames=args.watch_frames,
        switch_threshold=args.switch_threshold,
    )
    if args.json_out:
        write_rom_switch_materialization_json(report, Path(args.json_out))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_batch_switch_table(report, limit=args.display_limit))
        if args.json_out:
            print(f"wrote {args.json_out}")
    if args.fail_on_error and report.get("summary", {}).get("error_count", 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
