from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .catalog import build_capability_report, build_inventory, triage_request
from .content_mirror import build_content_mirror_report
from .content_scenarios import build_content_scenario_report
from .content_state import build_content_state_report
from .coverage import build_coverage_report
from .dynamic_taint import build_dynamic_taint_report
from .explain import build_explanation_report
from .expect import build_expectation_report
from .fuzz import build_fuzz_plan
from .generate import build_generation_plan
from .impact import build_impact_report
from .ingest import ingest_artifacts
from .instruction_trace import build_instruction_trace_report
from .investigate import build_investigation_run
from .localize import build_localization_plan
from .minimize import build_minimization_plan
from .mirrors import build_compare_plan
from .provenance import build_provenance_report
from .ranking import rank_findings
from .replay import build_replay_plan
from .reporting import build_static_report, write_static_report
from .runtime_watch import build_watch_report
from .setup_plan import build_setup_plan
from .state_space import build_state_space_report
from .slicing import build_slice_report
from .testgen import suggest_tests
from .taint import build_taint_report
from .trace_index import build_trace_index_report
from .visualization import build_visualization_report, write_visualization
from .workflow import build_gate_plan, command_is_runnable


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger",
        description="Unified Pokemon Gold romhack debugger inventory, audit, and triage front door.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory = subparsers.add_parser("inventory")
    add_output_args(inventory)
    inventory.set_defaults(func=cmd_inventory)

    audit = subparsers.add_parser("audit")
    add_output_args(audit)
    audit.add_argument(
        "--strict",
        action="store_true",
        help="exit nonzero when the whole-ROM debugger goal still has gaps",
    )
    audit.set_defaults(func=cmd_audit)

    triage = subparsers.add_parser("triage")
    triage.add_argument("--changed-file", action="append", default=[])
    triage.add_argument("--symptom", default="")
    add_output_args(triage)
    triage.set_defaults(func=cmd_triage)

    ingest = subparsers.add_parser("ingest")
    ingest.add_argument("--rom", action="append", default=[])
    ingest.add_argument("--symbols", action="append", default=[])
    ingest.add_argument("--trace", action="append", default=[])
    ingest.add_argument("--save-state", action="append", default=[])
    ingest.add_argument("--scenario", action="append", default=[])
    ingest.add_argument("--changed-file", action="append", default=[])
    add_output_args(ingest)
    ingest.set_defaults(func=cmd_ingest)

    gate = subparsers.add_parser("gate")
    gate.add_argument("--changed-file", action="append", default=[])
    gate.add_argument("--symptom", default="")
    gate.add_argument(
        "--execute",
        action="store_true",
        help="run selected commands; default is to print the plan only",
    )
    gate.add_argument("--max-commands", type=int)
    gate.add_argument("--timeout-seconds", type=int, default=600)
    add_output_args(gate)
    gate.set_defaults(func=cmd_gate)

    investigate = subparsers.add_parser("investigate")
    investigate.add_argument("--rom", default="")
    investigate.add_argument("--symbols", default="pokegold.sym")
    investigate.add_argument("--save-state", default="")
    investigate.add_argument("--trace", action="append", default=[])
    investigate.add_argument("--scenario", action="append", default=[])
    investigate.add_argument("--report", action="append", default=[])
    investigate.add_argument("--changed-file", action="append", default=[])
    investigate.add_argument("--symbol", action="append", default=[])
    investigate.add_argument("--watch-symbol", action="append", default=[])
    investigate.add_argument("--rule", action="append", default=[])
    investigate.add_argument("--address", action="append", default=[])
    investigate.add_argument("--expect", action="append", default=[])
    investigate.add_argument("--expect-file", action="append", default=[])
    investigate.add_argument("--family", action="append", default=[])
    investigate.add_argument("--symptom", default="")
    investigate.add_argument("--out-dir", default=".local\\tmp\\debugger_investigation")
    investigate.add_argument("--execute-watch", action="store_true")
    investigate.add_argument("--frames", type=int, default=300)
    investigate.add_argument("--context-frames", type=int, default=12)
    investigate.add_argument("--max-targets", type=int, default=24)
    investigate.add_argument("--max-events", type=int, default=1000)
    investigate.add_argument("--max-cases", type=int, default=64)
    investigate.add_argument("--seed", type=int, default=1)
    add_output_args(investigate)
    investigate.set_defaults(func=cmd_investigate)

    localize = subparsers.add_parser("localize")
    localize.add_argument("--changed-file", action="append", default=[])
    localize.add_argument("--symbol", action="append", default=[])
    localize.add_argument("--symptom", default="")
    localize.add_argument("--report", action="append", default=[])
    localize.add_argument("--symbols", default="pokegold.sym")
    localize.add_argument("--max-candidates", type=int, default=20)
    add_output_args(localize)
    localize.set_defaults(func=cmd_localize)

    coverage = subparsers.add_parser("coverage")
    coverage.add_argument("--trace", action="append", default=[])
    coverage.add_argument("--report", action="append", default=[])
    coverage.add_argument("--symbol", action="append", default=[])
    coverage.add_argument("--rule", action="append", default=[])
    coverage.add_argument("--changed-file", action="append", default=[])
    coverage.add_argument("--symbols", default="pokegold.sym")
    coverage.add_argument("--max-targets", type=int, default=80)
    add_output_args(coverage)
    coverage.set_defaults(func=cmd_coverage)

    trace_index = subparsers.add_parser("trace-index")
    trace_index.add_argument("--trace", action="append", default=[])
    trace_index.add_argument("--report", action="append", default=[])
    trace_index.add_argument("--symbol", action="append", default=[])
    trace_index.add_argument("--watch-symbol", action="append", default=[])
    trace_index.add_argument("--address", action="append", default=[])
    trace_index.add_argument("--rule", action="append", default=[])
    trace_index.add_argument("--source-file", action="append", default=[])
    trace_index.add_argument("--symptom", default="")
    trace_index.add_argument("--symbols", default="pokegold.sym")
    trace_index.add_argument("--max-events", type=int, default=120)
    trace_index.add_argument("--max-links", type=int, default=160)
    add_output_args(trace_index)
    trace_index.set_defaults(func=cmd_trace_index)

    minimize = subparsers.add_parser("minimize")
    minimize.add_argument("--report", action="append", default=[])
    minimize.add_argument("--trace", action="append", default=[])
    minimize.add_argument("--scenario", action="append", default=[])
    minimize.add_argument("--scenario-id", action="append", default=[])
    minimize.add_argument("--bug-id", action="append", default=[])
    minimize.add_argument("--symbol", action="append", default=[])
    minimize.add_argument("--event", action="append", default=[])
    minimize.add_argument("--rule", action="append", default=[])
    minimize.add_argument("--address", action="append", default=[])
    minimize.add_argument("--source-file", action="append", default=[])
    minimize.add_argument("--expect", action="append", default=[])
    minimize.add_argument("--expect-file", action="append", default=[])
    minimize.add_argument("--changed-file", action="append", default=[])
    minimize.add_argument("--symptom", default="")
    minimize.add_argument("--out-scenarios", default="")
    minimize.add_argument("--out-trace", default="")
    minimize.add_argument("--out-state-report", default="")
    minimize.add_argument("--symbols", default="pokegold.sym")
    minimize.add_argument("--max-scenarios", type=int, default=20)
    minimize.add_argument("--max-trace-records", type=int, default=200)
    add_output_args(minimize)
    minimize.set_defaults(func=cmd_minimize)

    generate = subparsers.add_parser("generate")
    generate.add_argument("--report", action="append", default=[])
    generate.add_argument("--scenario", action="append", default=[])
    generate.add_argument("--family", action="append", default=[])
    generate.add_argument("--symbol", action="append", default=[])
    generate.add_argument("--changed-file", action="append", default=[])
    generate.add_argument("--symptom", default="")
    generate.add_argument("--out-scenarios", default="")
    generate.add_argument("--max-cases", type=int, default=64)
    generate.add_argument("--seed", type=int, default=1)
    add_output_args(generate)
    generate.set_defaults(func=cmd_generate)

    fuzz = subparsers.add_parser("fuzz")
    fuzz.add_argument("--report", action="append", default=[])
    fuzz.add_argument("--scenario", action="append", default=[])
    fuzz.add_argument("--family", action="append", default=[])
    fuzz.add_argument("--symbol", action="append", default=[])
    fuzz.add_argument("--changed-file", action="append", default=[])
    fuzz.add_argument("--symptom", default="")
    fuzz.add_argument("--out-cases", default="")
    fuzz.add_argument("--max-cases", type=int, default=64)
    fuzz.add_argument("--seed", type=int, default=1)
    add_output_args(fuzz)
    fuzz.set_defaults(func=cmd_fuzz)

    provenance = subparsers.add_parser("provenance")
    provenance.add_argument("--symbols", default="pokegold.sym")
    provenance.add_argument("--symbol", action="append", default=[])
    provenance.add_argument("--source-file", action="append", default=[])
    provenance.add_argument("--include-docs", action="store_true")
    provenance.add_argument("--max-hits", type=int, default=40)
    add_output_args(provenance)
    provenance.set_defaults(func=cmd_provenance)

    slice_parser = subparsers.add_parser("slice")
    slice_parser.add_argument("--symbols", default="pokegold.sym")
    slice_parser.add_argument("--symbol", action="append", default=[])
    slice_parser.add_argument("--source-file", action="append", default=[])
    slice_parser.add_argument("--depth", type=int, default=2)
    slice_parser.add_argument("--max-edges", type=int, default=80)
    add_output_args(slice_parser)
    slice_parser.set_defaults(func=cmd_slice)

    taint = subparsers.add_parser("taint")
    taint.add_argument("--symbols", default="pokegold.sym")
    taint.add_argument("--symbol", action="append", default=[])
    taint.add_argument("--source-file", action="append", default=[])
    taint.add_argument("--max-depth", type=int, default=80)
    taint.add_argument("--max-paths", type=int, default=40)
    add_output_args(taint)
    taint.set_defaults(func=cmd_taint)

    dynamic_taint = subparsers.add_parser("dynamic-taint")
    dynamic_taint.add_argument("--trace", action="append", default=[])
    dynamic_taint.add_argument("--report", action="append", default=[])
    dynamic_taint.add_argument("--symbols", default="pokegold.sym")
    dynamic_taint.add_argument("--source-reg", action="append", default=[])
    dynamic_taint.add_argument("--source-mem", action="append", default=[])
    dynamic_taint.add_argument("--source-symbol", action="append", default=[])
    dynamic_taint.add_argument("--sink-symbol", action="append", default=[])
    dynamic_taint.add_argument("--sink-address", action="append", default=[])
    dynamic_taint.add_argument("--sink-size", type=int, default=1)
    dynamic_taint.add_argument("--max-paths", type=int, default=40)
    add_output_args(dynamic_taint)
    dynamic_taint.set_defaults(func=cmd_dynamic_taint)

    trace_instructions = subparsers.add_parser("trace-instructions")
    trace_instructions.add_argument("--rom", default="pokegold.gbc")
    trace_instructions.add_argument("--symbols", default="pokegold.sym")
    trace_instructions.add_argument("--save-state", default="")
    trace_instructions.add_argument("--report", action="append", default=[])
    trace_instructions.add_argument("--scenario-id", action="append", default=[])
    trace_instructions.add_argument("--changed-file", action="append", default=[])
    trace_instructions.add_argument("--symptom", default="")
    trace_instructions.add_argument("--symbol", action="append", default=[])
    trace_instructions.add_argument("--watch-symbol", action="append", default=[])
    trace_instructions.add_argument("--sink-symbol", action="append", default=[])
    trace_instructions.add_argument("--frames", type=int, default=300)
    trace_instructions.add_argument("--max-bytes", type=lambda value: int(value, 0), default=0x800)
    trace_instructions.add_argument("--max-frames", type=int, default=50000)
    trace_instructions.add_argument("--max-functions", type=int, default=12)
    trace_instructions.add_argument("--execute", action="store_true")
    trace_instructions.add_argument("--require-hit", action="store_true")
    trace_instructions.add_argument("--out-trace", default="")
    add_output_args(trace_instructions)
    trace_instructions.set_defaults(func=cmd_trace_instructions)

    watch = subparsers.add_parser("watch")
    watch.add_argument("--rom", default="pokegold.gbc")
    watch.add_argument("--symbols", default="pokegold.sym")
    watch.add_argument("--save-state", default="")
    watch.add_argument("--watch-symbol", action="append", default=[])
    watch.add_argument("--frames", type=int, default=60)
    watch.add_argument("--context-frames", type=int, default=12)
    watch.add_argument("--execute", action="store_true")
    add_output_args(watch)
    watch.set_defaults(func=cmd_watch)

    replay = subparsers.add_parser("replay")
    replay.add_argument("--rom", default="")
    replay.add_argument("--symbols", default="")
    replay.add_argument("--save-state", default="")
    replay.add_argument("--trace", action="append", default=[])
    replay.add_argument("--scenario", action="append", default=[])
    replay.add_argument("--scenario-id", action="append", default=[])
    replay.add_argument("--report", action="append", default=[])
    replay.add_argument("--watch-symbol", action="append", default=[])
    replay.add_argument("--symbol", action="append", default=[])
    replay.add_argument("--changed-file", action="append", default=[])
    replay.add_argument("--symptom", default="")
    replay.add_argument("--frames", type=int, default=300)
    replay.add_argument("--context-frames", type=int, default=12)
    replay.add_argument("--execute-watch", action="store_true")
    replay.add_argument("--max-targets", type=int, default=12)
    add_output_args(replay)
    replay.set_defaults(func=cmd_replay)

    setup = subparsers.add_parser("setup")
    setup.add_argument("--rom", default="")
    setup.add_argument("--symbols", default="pokegold.sym")
    setup.add_argument("--save-state", default="")
    setup.add_argument("--report", action="append", default=[])
    setup.add_argument("--scenario", action="append", default=[])
    setup.add_argument("--scenario-id", action="append", default=[])
    setup.add_argument("--changed-file", action="append", default=[])
    setup.add_argument("--symbol", action="append", default=[])
    setup.add_argument("--watch-symbol", action="append", default=[])
    setup.add_argument("--symptom", default="")
    setup.add_argument("--frames", type=int, default=300)
    setup.add_argument("--out-scenarios", default="")
    add_output_args(setup)
    setup.set_defaults(func=cmd_setup)

    explain = subparsers.add_parser("explain")
    explain.add_argument("--report", action="append", default=[])
    explain.add_argument("--trace", action="append", default=[])
    explain.add_argument("--symbol", action="append", default=[])
    explain.add_argument("--watch-symbol", action="append", default=[])
    explain.add_argument("--changed-file", action="append", default=[])
    explain.add_argument("--symptom", default="")
    explain.add_argument("--symbols", default="pokegold.sym")
    explain.add_argument("--depth", type=int, default=2)
    explain.add_argument("--max-paths", type=int, default=20)
    add_output_args(explain)
    explain.set_defaults(func=cmd_explain)

    tests = subparsers.add_parser("suggest-tests")
    tests.add_argument("--changed-file", action="append", default=[])
    tests.add_argument("--symbol", action="append", default=[])
    tests.add_argument("--symptom", default="")
    add_output_args(tests)
    tests.set_defaults(func=cmd_suggest_tests)

    compare = subparsers.add_parser("compare")
    compare.add_argument("--report", action="append", default=[])
    compare.add_argument("--changed-file", action="append", default=[])
    compare.add_argument("--symbol", action="append", default=[])
    compare.add_argument("--symptom", default="")
    add_output_args(compare)
    compare.set_defaults(func=cmd_compare)

    content_mirror = subparsers.add_parser("content-mirror")
    content_mirror.add_argument("--source-file", action="append", default=[])
    content_mirror.add_argument("--changed-file", action="append", default=[])
    content_mirror.add_argument("--max-files", type=int, default=120)
    content_mirror.add_argument("--rom", default="pokegold.gbc")
    content_mirror.add_argument("--symbols", default="pokegold.sym")
    add_output_args(content_mirror)
    content_mirror.set_defaults(func=cmd_content_mirror)

    content_scenarios = subparsers.add_parser("content-scenarios")
    content_scenarios.add_argument("--source-file", action="append", default=[])
    content_scenarios.add_argument("--changed-file", action="append", default=[])
    content_scenarios.add_argument("--out-scenarios", default="")
    content_scenarios.add_argument("--max-cases", type=int, default=64)
    content_scenarios.add_argument("--seed", type=int, default=1)
    add_output_args(content_scenarios)
    content_scenarios.set_defaults(func=cmd_content_scenarios)

    content_state = subparsers.add_parser("content-state")
    content_state.add_argument("--report", action="append", default=[])
    content_state.add_argument("--scenario", action="append", default=[])
    content_state.add_argument("--scenario-id", action="append", default=[])
    content_state.add_argument("--rom", default="pokegold.gbc")
    content_state.add_argument("--symbols", default="pokegold.sym")
    content_state.add_argument("--base-save-state", default="")
    content_state.add_argument("--out-state", default="")
    content_state.add_argument("--execute", action="store_true")
    content_state.add_argument("--max-scenarios", type=int, default=8)
    add_output_args(content_state)
    content_state.set_defaults(func=cmd_content_state)

    state_space = subparsers.add_parser("state-space")
    state_space.add_argument("--patch", action="append", default=[])
    state_space.add_argument("--watch-symbol", action="append", default=[])
    state_space.add_argument("--scenario-id", default="")
    state_space.add_argument("--source-file", action="append", default=[])
    state_space.add_argument("--symptom", default="")
    state_space.add_argument("--rom", default="pokegold.gbc")
    state_space.add_argument("--symbols", default="pokegold.sym")
    state_space.add_argument("--base-save-state", default="")
    state_space.add_argument("--out-state", default="")
    state_space.add_argument("--execute", action="store_true")
    add_output_args(state_space)
    state_space.set_defaults(func=cmd_state_space)

    expect = subparsers.add_parser("expect")
    expect.add_argument("--report", action="append", default=[])
    expect.add_argument("--trace", action="append", default=[])
    expect.add_argument("--expect", action="append", default=[])
    expect.add_argument("--expect-file", action="append", default=[])
    expect.add_argument("--symbol", action="append", default=[])
    expect.add_argument("--event", action="append", default=[])
    expect.add_argument("--rule", action="append", default=[])
    expect.add_argument("--address", action="append", default=[])
    expect.add_argument("--source-file", action="append", default=[])
    expect.add_argument("--symptom", default="")
    expect.add_argument("--symbols", default="pokegold.sym")
    expect.add_argument("--max-events", type=int, default=1000)
    add_output_args(expect)
    expect.set_defaults(func=cmd_expect)

    rank = subparsers.add_parser("rank")
    rank.add_argument("--report", action="append", default=[], required=True)
    add_output_args(rank)
    rank.set_defaults(func=cmd_rank)

    impact = subparsers.add_parser("impact")
    impact.add_argument("--report", action="append", default=[])
    impact.add_argument("--changed-file", action="append", default=[])
    impact.add_argument("--symbol", action="append", default=[])
    impact.add_argument("--symptom", default="")
    impact.add_argument("--max-items", type=int, default=40)
    add_output_args(impact)
    impact.set_defaults(func=cmd_impact)

    report = subparsers.add_parser("report")
    report.add_argument("--report", action="append", default=[], required=True)
    report.add_argument("--out", default="")
    report.add_argument("--format", choices=("markdown", "html"), default="markdown")
    report.add_argument(
        "--title",
        default="Unified Pokemon Gold Romhack Debugger Report",
    )
    add_output_args(report)
    report.set_defaults(func=cmd_report)

    visualize = subparsers.add_parser("visualize")
    visualize.add_argument("--report", action="append", default=[])
    visualize.add_argument("--trace", action="append", default=[])
    visualize.add_argument("--out", default="")
    visualize.add_argument("--format", choices=("markdown", "html"), default="markdown")
    visualize.add_argument(
        "--title",
        default="Unified Pokemon Gold Romhack Debugger Visualization",
    )
    visualize.add_argument("--max-items", type=int, default=80)
    add_output_args(visualize)
    visualize.set_defaults(func=cmd_visualize)

    return parser


def add_output_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--json-out", default="")


def cmd_inventory(args: argparse.Namespace) -> int:
    report = build_inventory()
    emit_report(report, args)
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    report = build_capability_report()
    emit_report(report, args)
    if args.strict and not report["ready"]:
        return 1
    return 0


def cmd_triage(args: argparse.Namespace) -> int:
    report = triage_request(
        changed_files=tuple(args.changed_file),
        symptom=args.symptom,
    )
    emit_report(report, args)
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    report = ingest_artifacts(
        roms=tuple(args.rom),
        symbols=tuple(args.symbols),
        traces=tuple(args.trace),
        save_states=tuple(args.save_state),
        scenarios=tuple(args.scenario),
        changed_files=tuple(args.changed_file),
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_gate(args: argparse.Namespace) -> int:
    report = build_gate_plan(
        changed_files=tuple(args.changed_file),
        symptom=args.symptom,
        execute=args.execute,
        max_commands=args.max_commands,
        timeout_seconds=args.timeout_seconds,
    )
    emit_report(report, args)
    if args.execute and not report["passed"]:
        return 1
    return 0


def cmd_investigate(args: argparse.Namespace) -> int:
    report = build_investigation_run(
        rom_path=args.rom,
        symbols_path=args.symbols,
        save_state=args.save_state,
        traces=tuple(args.trace),
        scenarios=tuple(args.scenario),
        reports=tuple(args.report),
        changed_files=tuple(args.changed_file),
        symbols=tuple(args.symbol),
        watch_symbols=tuple(args.watch_symbol),
        rules=tuple(args.rule),
        addresses=tuple(args.address),
        expectations=tuple(args.expect),
        expectation_files=tuple(args.expect_file),
        families=tuple(args.family),
        symptom=args.symptom,
        out_dir=args.out_dir,
        execute_watch=args.execute_watch,
        frames=args.frames,
        context_frames=args.context_frames,
        max_targets=args.max_targets,
        max_events=args.max_events,
        max_cases=args.max_cases,
        seed=args.seed,
    )
    emit_report(report, args)
    return 0 if report["valid"] and report["passed"] else 1


def cmd_localize(args: argparse.Namespace) -> int:
    report = build_localization_plan(
        changed_files=tuple(args.changed_file),
        symbols=tuple(args.symbol),
        symptom=args.symptom,
        reports=tuple(args.report),
        symbols_path=args.symbols,
        max_candidates=args.max_candidates,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_coverage(args: argparse.Namespace) -> int:
    report = build_coverage_report(
        traces=tuple(args.trace),
        reports=tuple(args.report),
        symbols=tuple(args.symbol),
        rules=tuple(args.rule),
        changed_files=tuple(args.changed_file),
        symbols_path=args.symbols,
        max_targets=args.max_targets,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_trace_index(args: argparse.Namespace) -> int:
    report = build_trace_index_report(
        traces=tuple(args.trace),
        reports=tuple(args.report),
        symbols=tuple(args.symbol),
        watch_symbols=tuple(args.watch_symbol),
        addresses=tuple(args.address),
        rules=tuple(args.rule),
        source_files=tuple(args.source_file),
        symptom=args.symptom,
        symbols_path=args.symbols,
        max_events=args.max_events,
        max_links=args.max_links,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_minimize(args: argparse.Namespace) -> int:
    report = build_minimization_plan(
        reports=tuple(args.report),
        traces=tuple(args.trace),
        scenarios=tuple(args.scenario),
        scenario_ids=tuple(args.scenario_id),
        bug_ids=tuple(args.bug_id),
        symbols=tuple(args.symbol),
        events=tuple(args.event),
        rules=tuple(args.rule),
        addresses=tuple(args.address),
        source_files=tuple(args.source_file),
        expectations=tuple(args.expect),
        expectation_files=tuple(args.expect_file),
        changed_files=tuple(args.changed_file),
        symptom=args.symptom,
        out_scenarios=args.out_scenarios,
        out_trace=args.out_trace,
        out_state_report=args.out_state_report,
        symbols_path=args.symbols,
        max_scenarios=args.max_scenarios,
        max_trace_records=args.max_trace_records,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_generate(args: argparse.Namespace) -> int:
    report = build_generation_plan(
        reports=tuple(args.report),
        scenarios=tuple(args.scenario),
        families=tuple(args.family),
        symbols=tuple(args.symbol),
        changed_files=tuple(args.changed_file),
        symptom=args.symptom,
        out_scenarios=args.out_scenarios,
        max_cases=args.max_cases,
        seed=args.seed,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_fuzz(args: argparse.Namespace) -> int:
    report = build_fuzz_plan(
        reports=tuple(args.report),
        scenarios=tuple(args.scenario),
        families=tuple(args.family),
        symbols=tuple(args.symbol),
        changed_files=tuple(args.changed_file),
        symptom=args.symptom,
        out_cases=args.out_cases,
        max_cases=args.max_cases,
        seed=args.seed,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_provenance(args: argparse.Namespace) -> int:
    report = build_provenance_report(
        symbols_path=args.symbols,
        symbols=tuple(args.symbol),
        source_files=tuple(args.source_file),
        include_docs=args.include_docs,
        max_hits=args.max_hits,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_slice(args: argparse.Namespace) -> int:
    report = build_slice_report(
        symbols_path=args.symbols,
        symbols=tuple(args.symbol),
        source_files=tuple(args.source_file),
        max_depth=args.depth,
        max_edges=args.max_edges,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_taint(args: argparse.Namespace) -> int:
    report = build_taint_report(
        symbols_path=args.symbols,
        symbols=tuple(args.symbol),
        source_files=tuple(args.source_file),
        max_depth=args.max_depth,
        max_paths=args.max_paths,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_dynamic_taint(args: argparse.Namespace) -> int:
    report = build_dynamic_taint_report(
        traces=tuple(args.trace),
        reports=tuple(args.report),
        symbols_path=args.symbols,
        source_regs=tuple(args.source_reg),
        source_mems=tuple(args.source_mem),
        source_symbols=tuple(args.source_symbol),
        sink_symbols=tuple(args.sink_symbol),
        sink_addresses=tuple(args.sink_address),
        sink_size=args.sink_size,
        max_paths=args.max_paths,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_trace_instructions(args: argparse.Namespace) -> int:
    report = build_instruction_trace_report(
        function_symbols=tuple(args.symbol),
        watch_symbols=tuple(args.watch_symbol),
        reports=tuple(args.report),
        scenario_ids=tuple(args.scenario_id),
        changed_files=tuple(args.changed_file),
        symptom=args.symptom,
        sink_symbols=tuple(args.sink_symbol),
        rom_path=args.rom,
        symbols_path=args.symbols,
        save_state=args.save_state,
        frames=args.frames,
        max_bytes=args.max_bytes,
        max_frames=args.max_frames,
        max_functions=args.max_functions,
        execute=args.execute,
        require_hit=args.require_hit,
        out_trace=args.out_trace,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_watch(args: argparse.Namespace) -> int:
    report = build_watch_report(
        watch_symbols=tuple(args.watch_symbol),
        rom_path=args.rom,
        symbols_path=args.symbols,
        save_state=args.save_state,
        frames=args.frames,
        context_frames=args.context_frames,
        execute=args.execute,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_replay(args: argparse.Namespace) -> int:
    report = build_replay_plan(
        rom_path=args.rom,
        symbols_path=args.symbols,
        save_state=args.save_state,
        traces=tuple(args.trace),
        scenarios=tuple(args.scenario),
        scenario_ids=tuple(args.scenario_id),
        reports=tuple(args.report),
        watch_symbols=tuple(args.watch_symbol),
        symbols=tuple(args.symbol),
        changed_files=tuple(args.changed_file),
        symptom=args.symptom,
        frames=args.frames,
        context_frames=args.context_frames,
        execute_watch=args.execute_watch,
        max_targets=args.max_targets,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_setup(args: argparse.Namespace) -> int:
    report = build_setup_plan(
        rom_path=args.rom,
        symbols_path=args.symbols,
        save_state=args.save_state,
        reports=tuple(args.report),
        scenarios=tuple(args.scenario),
        scenario_ids=tuple(args.scenario_id),
        changed_files=tuple(args.changed_file),
        symbols=tuple(args.symbol),
        watch_symbols=tuple(args.watch_symbol),
        symptom=args.symptom,
        frames=args.frames,
        out_scenarios=args.out_scenarios,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_explain(args: argparse.Namespace) -> int:
    report = build_explanation_report(
        reports=tuple(args.report),
        traces=tuple(args.trace),
        symbols=tuple(args.symbol),
        watch_symbols=tuple(args.watch_symbol),
        changed_files=tuple(args.changed_file),
        symptom=args.symptom,
        symbols_path=args.symbols,
        depth=args.depth,
        max_paths=args.max_paths,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_suggest_tests(args: argparse.Namespace) -> int:
    report = suggest_tests(
        changed_files=tuple(args.changed_file),
        symbols=tuple(args.symbol),
        symptom=args.symptom,
    )
    emit_report(report, args)
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    report = build_compare_plan(
        reports=tuple(args.report),
        changed_files=tuple(args.changed_file),
        symbols=tuple(args.symbol),
        symptom=args.symptom,
    )
    emit_report(report, args)
    return 0


def cmd_content_mirror(args: argparse.Namespace) -> int:
    report = build_content_mirror_report(
        source_files=tuple(args.source_file),
        changed_files=tuple(args.changed_file),
        max_files=args.max_files,
        rom_path=args.rom,
        symbols_path=args.symbols,
    )
    emit_report(report, args)
    return 0 if report["valid"] and report["passed"] else 1


def cmd_content_scenarios(args: argparse.Namespace) -> int:
    report = build_content_scenario_report(
        source_files=tuple(args.source_file),
        changed_files=tuple(args.changed_file),
        out_scenarios=args.out_scenarios,
        max_cases=args.max_cases,
        seed=args.seed,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_content_state(args: argparse.Namespace) -> int:
    report = build_content_state_report(
        reports=tuple(args.report),
        scenarios=tuple(args.scenario),
        scenario_ids=tuple(args.scenario_id),
        rom_path=args.rom,
        symbols_path=args.symbols,
        base_save_state=args.base_save_state,
        out_state=args.out_state,
        execute=args.execute,
        max_scenarios=args.max_scenarios,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_state_space(args: argparse.Namespace) -> int:
    report = build_state_space_report(
        patches=tuple(args.patch),
        watch_symbols=tuple(args.watch_symbol),
        scenario_id=args.scenario_id,
        source_files=tuple(args.source_file),
        symptom=args.symptom,
        rom_path=args.rom,
        symbols_path=args.symbols,
        base_save_state=args.base_save_state,
        out_state=args.out_state,
        execute=args.execute,
        report_path=args.json_out,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_expect(args: argparse.Namespace) -> int:
    report = build_expectation_report(
        reports=tuple(args.report),
        traces=tuple(args.trace),
        expectation_files=tuple(args.expect_file),
        expectations=tuple(args.expect),
        symbols=tuple(args.symbol),
        events=tuple(args.event),
        rules=tuple(args.rule),
        addresses=tuple(args.address),
        source_files=tuple(args.source_file),
        symptom=args.symptom,
        symbols_path=args.symbols,
        max_events=args.max_events,
    )
    emit_report(report, args)
    return 0 if report["valid"] and report["passed"] else 1


def cmd_rank(args: argparse.Namespace) -> int:
    report = rank_findings(reports=tuple(args.report))
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_impact(args: argparse.Namespace) -> int:
    report = build_impact_report(
        reports=tuple(args.report),
        changed_files=tuple(args.changed_file),
        symbols=tuple(args.symbol),
        symptom=args.symptom,
        max_items=args.max_items,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_report(args: argparse.Namespace) -> int:
    report = build_static_report(
        reports=tuple(args.report),
        output_format=args.format,
        title=args.title,
    )
    if args.out:
        out_path = Path(args.out)
        write_static_report(report, out_path)
        report["out"] = str(out_path)
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_visualize(args: argparse.Namespace) -> int:
    report = build_visualization_report(
        reports=tuple(args.report),
        traces=tuple(args.trace),
        output_format=args.format,
        title=args.title,
        max_items=args.max_items,
    )
    if args.out:
        out_path = Path(args.out)
        write_visualization(report, out_path)
        report["out"] = str(out_path)
    emit_report(report, args)
    return 0 if report["valid"] else 1


def emit_report(report: dict[str, Any], args: argparse.Namespace) -> None:
    if args.json_out:
        write_json(report, Path(args.json_out))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif report["kind"] == "unified_debugger_inventory":
        print(format_inventory(report))
    elif report["kind"] == "unified_debugger_capability_report":
        print(format_audit(report))
    elif report["kind"] == "unified_debugger_triage":
        print(format_triage(report))
    elif report["kind"] == "unified_debugger_ingest_manifest":
        print(format_ingest(report))
    elif report["kind"] == "unified_debugger_gate_plan":
        print(format_gate(report))
    elif report["kind"] == "unified_debugger_investigation_run":
        print(format_investigation_run(report))
    elif report["kind"] == "unified_debugger_localization_plan":
        print(format_localization_plan(report))
    elif report["kind"] == "unified_debugger_coverage_report":
        print(format_coverage_report(report))
    elif report["kind"] == "unified_debugger_trace_index":
        print(format_trace_index(report))
    elif report["kind"] == "unified_debugger_minimization_plan":
        print(format_minimization_plan(report))
    elif report["kind"] == "unified_debugger_generation_plan":
        print(format_generation_plan(report))
    elif report["kind"] == "unified_debugger_fuzz_plan":
        print(format_fuzz_plan(report))
    elif report["kind"] == "unified_debugger_provenance_report":
        print(format_provenance(report))
    elif report["kind"] == "unified_debugger_causal_slice":
        print(format_slice(report))
    elif report["kind"] == "unified_debugger_taint_report":
        print(format_taint(report))
    elif report["kind"] == "unified_debugger_dynamic_taint_report":
        print(format_dynamic_taint(report))
    elif report["kind"] == "unified_debugger_instruction_trace":
        print(format_instruction_trace(report))
    elif report["kind"] == "unified_debugger_watch_report":
        print(format_watch(report))
    elif report["kind"] == "unified_debugger_replay_plan":
        print(format_replay_plan(report))
    elif report["kind"] == "unified_debugger_setup_plan":
        print(format_setup_plan(report))
    elif report["kind"] == "unified_debugger_causal_explanation":
        print(format_explanation(report))
    elif report["kind"] == "unified_debugger_test_suggestions":
        print(format_test_suggestions(report))
    elif report["kind"] == "unified_debugger_compare_plan":
        print(format_compare_plan(report))
    elif report["kind"] == "unified_debugger_content_mirror":
        print(format_content_mirror(report))
    elif report["kind"] == "unified_debugger_content_scenarios":
        print(format_content_scenarios(report))
    elif report["kind"] == "unified_debugger_content_state_materialization":
        print(format_content_state(report))
    elif report["kind"] == "unified_debugger_state_space":
        print(format_state_space(report))
    elif report["kind"] == "unified_debugger_expectation_report":
        print(format_expectation_report(report))
    elif report["kind"] == "unified_debugger_ranked_findings":
        print(format_ranked_findings(report))
    elif report["kind"] == "unified_debugger_impact_report":
        print(format_impact_report(report))
    elif report["kind"] == "unified_debugger_static_report":
        print(format_static_report(report))
    elif report["kind"] == "unified_debugger_visualization":
        print(format_visualization(report))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))


def format_inventory(report: dict[str, Any]) -> str:
    lines = ["Unified Pokemon Gold romhack debugger inventory", f"root={report['root']}", ""]
    lines.append("Subsystems:")
    for subsystem in report["subsystems"]:
        availability = "available" if subsystem["available"] else "missing"
        lines.append(f"  - {availability}: {subsystem['id']} - {subsystem['title']}")
        lines.append(f"      scope: {subsystem['scope']}")
        for command in subsystem["entrypoints"][:2]:
            lines.append(f"      command: {command}")
    return "\n".join(lines)


def format_audit(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger capability audit",
        f"ready={report['ready']} status_counts={report['status_counts']}",
        f"blocking_gaps={report['blocking_gap_count']}",
        "",
        "Capabilities:",
    ]
    for capability in report["capabilities"]:
        lines.append(
            f"  - {capability['status']}: {capability['id']} - {capability['title']}"
        )
        for gap in capability["gaps"][:2]:
            lines.append(f"      gap: {gap}")
        for command in capability["commands"][:1]:
            lines.append(f"      command: {command}")
    if report["blocking_gaps"]:
        lines.extend(["", "Top gaps:"])
        for gap in report["blocking_gaps"][:8]:
            lines.append(f"  - {gap}")
    return "\n".join(lines)


def format_triage(report: dict[str, Any]) -> str:
    lines = ["Unified Pokemon Gold romhack debugger triage"]
    if report["changed_files"]:
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report["symptom"]:
        lines.append(f"symptom={report['symptom']}")
    lines.extend(["", "Matches:"])
    for match in report["matches"]:
        lines.append(
            f"  - {match['id']} - {match['title']} "
            f"({', '.join(match['matched_by'])})"
        )
        lines.append(f"      reason: {match['reason']}")
        for gap in match["gaps"]:
            lines.append(f"      gap: {gap}")
    lines.extend(["", "Suggested commands:"])
    for command in report["commands"]:
        lines.append(f"  - {command}")
    return "\n".join(lines)


def format_ingest(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger ingest manifest",
        (
            f"valid={report['valid']} artifacts={report['artifact_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
        "",
        "Artifacts:",
    ]
    for artifact in report["artifacts"]:
        status = "ok" if not artifact["errors"] else "error"
        lines.append(
            f"  - {status}: {artifact['kind']} {artifact['path']} "
            f"size={artifact['size_bytes']} sha256={artifact['sha256'][:12]}"
        )
        metadata = artifact["metadata"]
        if artifact["kind"] == "rom" and metadata.get("title"):
            lines.append(f"      title: {metadata['title']}")
        if artifact["kind"] == "symbols":
            lines.append(
                f"      labels: {metadata.get('label_count', 0)} "
                f"banks: {metadata.get('bank_count', 0)}"
            )
        if artifact["kind"] == "scenario":
            lines.append(
                f"      records: {metadata.get('record_count', 0)} "
                f"families: {', '.join(metadata.get('families', []))}"
            )
        if artifact["kind"] == "source_change":
            matches = metadata.get("triage_match_ids", [])
            lines.append(f"      triage: {', '.join(matches)}")
        for warning in artifact["warnings"]:
            lines.append(f"      warning: {warning}")
        for error in artifact["errors"]:
            lines.append(f"      error: {error}")
    return "\n".join(lines)


def format_gate(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger gate",
        (
            f"executed={report['executed']} passed={report['passed']} "
            f"steps={report['step_count']} failed={report['failed_count']} "
            f"skipped={report['skipped_count']}"
        ),
    ]
    if report["changed_files"]:
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report["symptom"]:
        lines.append(f"symptom={report['symptom']}")
    lines.extend(["", "Steps:"])
    for step in report["steps"]:
        runnable = "runnable" if step["runnable"] else "needs-input"
        lines.append(
            f"  - P{step['priority']} {step['status']}: {step['command']} ({runnable})"
        )
        for line in step["stderr_tail"][:2]:
            lines.append(f"      stderr: {line}")
    return "\n".join(lines)


def format_investigation_run(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger investigation run",
        (
            f"valid={report['valid']} passed={report['passed']} "
            f"steps={report['investigation_step_count']} reports={report['produced_report_count']} "
            f"findings={report['finding_count']} impact={report['impact_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
    ]
    if report.get("out_dir"):
        lines.append(f"out_dir={report['out_dir']}")
    if report.get("symptom"):
        lines.append(f"symptom={report['symptom']}")
    if report.get("symbols"):
        lines.append("symbols=" + ", ".join(report["symbols"]))
    if report.get("changed_files"):
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report.get("static_report"):
        lines.append(f"static_report={report['static_report']}")
    if report.get("visualization"):
        lines.append(f"visualization={report['visualization']}")
    lines.extend(["", "Steps:"])
    for step in report["steps"]:
        path = f" -> {step['report_path']}" if step.get("report_path") else ""
        lines.append(
            f"  - {step['status']} {step['id']} [{step['phase']}]: {step['title']}{path}"
        )
        summary = step.get("summary", {})
        if summary:
            lines.append(
                "      "
                + "; ".join(f"{key}={value}" for key, value in sorted(summary.items()))
            )
        for error in step.get("errors", [])[:2]:
            lines.append(f"      error: {error}")
        for warning in step.get("warnings", [])[:1]:
            lines.append(f"      warning: {warning}")
    if report["top_findings"]:
        lines.extend(["", "Top findings:"])
        for item in report["top_findings"][:10]:
            lines.append(
                f"  - S{item['severity']} C{item['confidence']:.2f} "
                f"{item['type']}: {item['title']}"
            )
    if report["top_impact"]:
        lines.extend(["", "Top impact:"])
        for item in report["top_impact"][:10]:
            lines.append(
                f"  - I{item['impact_score']} S{item['severity']} "
                f"{item['type']} [{item['surface']}]: {item['title']}"
            )
    if report["commands"]:
        lines.extend(["", "Top proof commands:"])
        for command in report["commands"][:10]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_localization_plan(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger localization plan",
        (
            f"valid={report['valid']} candidates={report['candidate_count']} "
            f"signals={report['signal_count']} errors={report['error_count']}"
        ),
    ]
    if report["symptom"]:
        lines.append(f"symptom={report['symptom']}")
    if report["changed_files"]:
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report["symbols"]:
        lines.append("symbols=" + ", ".join(report["symbols"]))
    if report["input_reports"]:
        lines.append("reports=" + ", ".join(report["input_reports"]))
    lines.extend(["", "Top candidates:"])
    for candidate in report["candidates"][:10]:
        lines.append(
            f"  - S{candidate['score']} {candidate['type']}: {candidate['id']}"
        )
        for evidence in candidate.get("evidence", [])[:2]:
            lines.append(f"      evidence: {evidence}")
    lines.extend(["", "Plan:"])
    for phase in report["phase_steps"]:
        lines.append(f"  {phase['title']}:")
        for step in phase["steps"][:6]:
            runnable = "runnable" if step["runnable"] else "needs-input"
            lines.append(f"    - {step['command']} ({runnable})")
            lines.append(f"        reason: {step['reason']}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_coverage_report(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger coverage report",
        (
            f"valid={report['valid']} targets={report['target_count']} "
            f"covered={report['covered_target_count']} indirect={report['indirect_target_count']} "
            f"uncovered={report['uncovered_target_count']} ratio={report['coverage_ratio']}"
        ),
        (
            f"observed_symbols={report['covered_symbol_count']} "
            f"observed_files={report['covered_file_count']} "
            f"observed_rules={report['covered_rule_count']}"
        ),
    ]
    if report["targets"]:
        lines.extend(["", "Targets:"])
        for target in report["targets"][:30]:
            explicit = "explicit" if target["explicit"] else "related"
            lines.append(
                f"  - {target['status']} {explicit} {target['type']}: {target['id']}"
            )
            for evidence in target.get("evidence", [])[:2]:
                lines.append(f"      evidence: {evidence}")
            if target["status"] == "uncovered":
                for command in target.get("commands", [])[:2]:
                    lines.append(f"      command: {command}")
    if report["covered_symbols"]:
        lines.extend(["", "Top observed symbols:"])
        for item in report["covered_symbols"][:10]:
            lines.append(f"  - {item['id']} count={item['count']}")
    if report["uncovered_targets"]:
        lines.extend(["", "Uncovered targets:"])
        for target in report["uncovered_targets"][:10]:
            lines.append(f"  - {target['type']}: {target['id']}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_trace_index(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger trace index",
        (
            f"valid={report['valid']} events={report['event_count']}/{report['all_event_count']} "
            f"matched={report['matched_event_count']} writes={report['write_event_count']} "
            f"reads={report['read_event_count']} links={report['causal_link_count']} "
            f"attributions={report.get('reverse_attribution_count', 0)} "
            f"paths={report['path_count']} errors={report['error_count']} warnings={report['warning_count']}"
        ),
    ]
    query = report.get("query", {})
    if query.get("symbols"):
        lines.append("symbols=" + ", ".join(query["symbols"]))
    if query.get("addresses"):
        lines.append("addresses=" + ", ".join(query["addresses"]))
    if query.get("rules"):
        lines.append("rules=" + ", ".join(query["rules"]))
    if query.get("source_files"):
        lines.append("source_files=" + ", ".join(query["source_files"]))
    if query.get("symptom"):
        lines.append(f"symptom={query['symptom']}")
    if report["events"]:
        lines.extend(["", "Events:"])
        for event in report["events"][:24]:
            state = event.get("state_symbol") or event.get("bank_address") or event.get("address") or "-"
            source = event.get("source_symbol") or event.get("pc_symbol") or event.get("rule_id") or "-"
            value = ""
            if event.get("before") or event.get("after"):
                value = f" {event.get('before', '')}->{event.get('after', '')}"
            lines.append(
                f"  - {event['id']} {event['event_type']} {state} from {source}{value}"
            )
            if event.get("source_file"):
                lines.append(f"      source: {event['source_file']}")
    if report.get("reverse_attributions"):
        lines.extend(["", "Reverse attributions:"])
        for item in report["reverse_attributions"][:12]:
            lines.append(
                f"  - C{item['confidence']:.2f} {item['event_id']}: {item['title']}"
            )
            for contributor in item.get("contributors", [])[:3]:
                lines.append(
                    f"      {contributor['relation']}: {contributor['state']} "
                    f"({contributor['event_id']})"
                )
    if report["causal_paths"]:
        lines.extend(["", "Causal paths:"])
        for path in report["causal_paths"][:12]:
            lines.append(
                f"  - S{path['score']} C{path['confidence']:.2f} {path['id']}: {path['title']}"
            )
            for node_item in path.get("nodes", [])[:4]:
                lines.append(f"      {node_item['type']}/{node_item['role']}: {node_item['label']}")
    if report["commands"]:
        lines.extend(["", "Top proof commands:"])
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_minimization_plan(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger minimization plan",
        (
            f"valid={report['valid']} scenarios={report['scenario_count']} "
            f"selected={report['selected_scenario_count']} errors={report['error_count']}"
        ),
        "surfaces=" + ", ".join(report["surfaces"]),
    ]
    if report["selected_scenario_ids"]:
        lines.append("selected_ids=" + ", ".join(report["selected_scenario_ids"][:10]))
    if report["bug_ids"]:
        lines.append("bug_ids=" + ", ".join(report["bug_ids"]))
    subset = report.get("subset_output", {})
    if subset.get("written"):
        lines.append(f"subset={subset['path']} records={subset['record_count']}")
    precondition_minimization = report.get("precondition_minimization", {})
    if precondition_minimization.get("attempted"):
        lines.append(
            "state_preconditions="
            + str(precondition_minimization.get("selected_precondition_count", 0))
            + "/"
            + str(precondition_minimization.get("precondition_count", 0))
        )
    state_patch_minimization = report.get("state_patch_minimization", {})
    if state_patch_minimization.get("attempted"):
        lines.append(
            "state_patches_minimized="
            + str(state_patch_minimization.get("preserved", False))
            + " "
            + str(state_patch_minimization.get("original_patch_count", 0))
            + "->"
            + str(state_patch_minimization.get("minimized_patch_count", 0))
        )
        if state_patch_minimization.get("out_report"):
            lines.append(f"state_patch_subset={state_patch_minimization['out_report']}")
    evidence_minimization = report.get("evidence_minimization", {})
    if evidence_minimization.get("attempted"):
        source_kind = str(evidence_minimization.get("source_kind", "trace") or "evidence")
        lines.append(
            "evidence_minimized="
            + str(evidence_minimization.get("preserved", False))
            + (
                f" {source_kind}"
                f" {evidence_minimization.get('original_count', 0)}"
                f"->{evidence_minimization.get('minimized_count', 0)}"
            )
        )
        if evidence_minimization.get("context_frame_original_count"):
            lines.append(
                "context_frames="
                + str(evidence_minimization.get("context_frame_original_count", 0))
                + "->"
                + str(evidence_minimization.get("context_frame_minimized_count", 0))
            )
        if evidence_minimization.get("out_trace"):
            lines.append(f"evidence_subset={evidence_minimization['out_trace']}")
    lines.extend(["", "Steps:"])
    for step in report["steps"][:30]:
        runnable = "runnable" if step["runnable"] else "needs-input"
        lines.append(f"  - {step['phase']}: {step['command']} ({runnable})")
        lines.append(f"      reason: {step['reason']}")
    if report["signals"]:
        lines.extend(["", "Signals:"])
        for item in report["signals"][:12]:
            lines.append(
                f"  - W{item['weight']} {item['kind']} {item['value']} ({item['type']})"
            )
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_generation_plan(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger generation plan",
        (
            f"valid={report['valid']} surfaces={report['surface_count']} "
            f"generators={report['generator_count']} counterexamples={report['counterexample_count']} "
            f"seeds={report['seed_count']} errors={report['error_count']}"
        ),
        f"seed={report['seed']} max_cases={report['max_cases']}",
        "surfaces=" + ", ".join(report["surfaces"]),
    ]
    if report["changed_files"]:
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report["symbols"]:
        lines.append("symbols=" + ", ".join(report["symbols"]))
    if report["families"]:
        lines.append("families=" + ", ".join(report["families"]))
    if report["symptom"]:
        lines.append(f"symptom={report['symptom']}")
    seed_manifest = report.get("seed_manifest", {})
    if seed_manifest.get("written"):
        lines.append(
            f"seed_manifest={seed_manifest['path']} records={seed_manifest['record_count']}"
        )
    lines.extend(["", "Generators:"])
    for generator in report["generators"]:
        lines.append(
            f"  - {generator['id']} [{generator['surface']}] "
            f"{generator['status']} C{generator['confidence']:.2f}: {generator['title']}"
        )
        for gap in generator.get("gaps", [])[:2]:
            lines.append(f"      gap: {gap}")
        for command in generator.get("commands", [])[:3]:
            runnable = "runnable" if command["runnable"] else "needs-input"
            lines.append(f"      command: {command['command']} ({runnable})")
    if report["materialization_steps"]:
        lines.extend(["", "Materialization workflow:"])
        for step in report["materialization_steps"][:24]:
            runnable = "runnable" if step["runnable"] else "needs-input"
            lines.append(f"  - {step['phase']}: {step['command']} ({runnable})")
            lines.append(f"      reason: {step['reason']}")
    if report["counterexamples"]:
        lines.extend(["", "Counterexample commands:"])
        for item in report["counterexamples"][:20]:
            runnable = "runnable" if item["runnable"] else "needs-input"
            surface = f" [{item['surface']}]" if item.get("surface") else ""
            lines.append(f"  - {item['source']}{surface}: {item['command']} ({runnable})")
    if report["signals"]:
        lines.extend(["", "Signals:"])
        for item in report["signals"][:12]:
            lines.append(
                f"  - W{item['weight']} {item['kind']} {item['value']} ({item['type']})"
            )
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_fuzz_plan(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger fuzz plan",
        (
            f"valid={report['valid']} surfaces={report['surface_count']} "
            f"campaigns={report['campaign_count']} dynamic={report['dynamic_campaign_count']} "
            f"static={report['static_campaign_count']} cases={report['fuzz_case_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
        f"seed={report['seed']} max_cases={report['max_cases']}",
        "surfaces=" + ", ".join(report["surfaces"]),
    ]
    case_manifest = report.get("case_manifest", {})
    if case_manifest.get("written"):
        lines.append(f"case_manifest={case_manifest['path']} records={case_manifest['record_count']}")
    lines.extend(["", "Campaigns:"])
    for campaign in report["campaigns"]:
        lines.append(
            f"  - {campaign['id']} [{campaign['surface']}] "
            f"{campaign['status']} {campaign['proof_level']} C{campaign['confidence']:.2f}: {campaign['title']}"
        )
        for gap in campaign.get("gaps", [])[:2]:
            lines.append(f"      gap: {gap}")
        for command in campaign.get("commands", [])[:3]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"      command: {command} ({runnable})")
    if report["fuzz_cases"]:
        lines.extend(["", "Fuzz cases:"])
        for case in report["fuzz_cases"][:16]:
            lines.append(
                f"  - {case['id']} {case['surface']} {case['fuzz_type']} "
                f"{case['proof_level']}"
            )
            for expectation in case.get("expectations", [])[:2]:
                lines.append(f"      expect: {expectation}")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_provenance(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger provenance",
        (
            f"valid={report['valid']} symbols={report['symbol_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
        f"symbol_file={report['symbols_path']} sha256={report['symbols_sha256'][:12]}",
        "",
    ]
    if report["symbols"]:
        lines.append("Symbols:")
        for symbol in report["symbols"]:
            address = symbol.get("address")
            location = address["bank_address"] if address else "not-in-symbols"
            lines.append(
                f"  - {symbol['query']} {location} "
                f"source_hits={symbol['source_hit_count']}"
            )
            for hit in symbol["source_hits"][:5]:
                lines.append(
                    f"      {hit['kind']}: {hit['path']}:{hit['line']} {hit['text']}"
                )
            for command in symbol.get("suggested_commands", [])[:3]:
                lines.append(f"      command: {command}")
    if report["source_files"]:
        lines.append("Source files:")
        for source in report["source_files"]:
            lines.append(
                f"  - {source['path']} labels={source['label_count']} "
                f"symbol_matches={source['symbols_matched_count']}"
            )
            for label in source["labels"][:5]:
                address = label.get("address", {})
                suffix = f" {address.get('bank_address', '')}" if address else ""
                lines.append(f"      label: {label['label']}:{label['line']}{suffix}")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_slice(report: dict[str, Any]) -> str:
    graph = report["graph"]
    lines = [
        "Unified Pokemon Gold romhack debugger causal slice",
        (
            f"valid={report['valid']} nodes={graph['node_count']} "
            f"edges={graph['edge_count']} source_files={graph['source_file_count']}"
        ),
        f"symbol_file={report['symbols_path']} sha256={report['symbols_sha256'][:12]}",
        "",
    ]
    if report["targets"]:
        lines.append("Targets:")
        for target in report["targets"]:
            if not target["found"]:
                lines.append(f"  - {target['query']} not-found")
                continue
            address = target.get("address") or {}
            location = address.get("bank_address", "source-only")
            definition = target.get("definition") or {}
            lines.append(
                f"  - {target['resolved']} {location} "
                f"defined={definition.get('path', '<unknown>')}:{definition.get('line', '?')}"
            )
            lines.append(
                f"      incoming={len(target['incoming'])} outgoing={len(target['outgoing'])} "
                f"impact_files={len(target['impact_files'])}"
            )
            for edge in target["incoming"][:8]:
                lines.append(
                    f"      in d{edge['depth']} {edge['access']}: "
                    f"{edge['source']} -> {edge['target']} "
                    f"{edge['path']}:{edge['line']} {edge['text']}"
                )
            for edge in target["outgoing"][:5]:
                lines.append(
                    f"      out d{edge['depth']} {edge['access']}: "
                    f"{edge['source']} -> {edge['target']} "
                    f"{edge['path']}:{edge['line']} {edge['text']}"
                )
            for command in target.get("suggested_commands", [])[:3]:
                lines.append(f"      command: {command}")
    if report["source_files"]:
        lines.append("Source files:")
        for source in report["source_files"]:
            lines.append(
                f"  - {source['path']} labels={source.get('label_count', 0)} "
                f"incoming={len(source.get('incoming', []))} "
                f"outgoing={len(source.get('outgoing', []))}"
            )
            for command in source.get("suggested_commands", [])[:3]:
                lines.append(f"      command: {command}")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_taint(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger taint report",
        (
            f"valid={report['valid']} targets={report['target_count']} "
            f"sinks={report['sink_count']} contributors={report['contributor_count']} "
            f"paths={report['path_count']} errors={report['error_count']} warnings={report['warning_count']}"
        ),
        f"symbols={report['symbols_path']} sources={report['source_file_count']} routines={report['routine_count']}",
    ]
    if report["targets"]:
        lines.extend(["", "Targets:"])
        for target in report["targets"][:12]:
            lines.append(
                f"  - {target['symbol']} found={target['found']} "
                f"sinks={target['sink_count']} contributors={target['contributor_count']}"
            )
            for contributor in target.get("contributors", [])[:4]:
                lines.append(
                    f"      {contributor['relation']}: {contributor['symbol']} "
                    f"at {contributor.get('source_file', '')}:{contributor.get('line', '')}"
                )
    if report["paths"]:
        lines.extend(["", "Taint paths:"])
        for path in report["paths"][:12]:
            lines.append(
                f"  - S{path['score']} C{path['confidence']:.2f} "
                f"{path['target']} {path['access']} {path['source_file']}:{path['line']}"
            )
            for step in path.get("steps", [])[:4]:
                lines.append(f"      {step['role']}: {step['code']}")
    if report["commands"]:
        lines.extend(["", "Top proof commands:"])
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_dynamic_taint(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger dynamic taint report",
        (
            f"valid={report['valid']} traces={report['trace_count']} "
            f"sources={report['source_count']} sinks={report['sink_count']} "
            f"findings={report['finding_count']} paths={report['path_count']} "
            f"writes={report.get('write_attribution_count', 0)} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
        f"symbols={report['symbols_path']}",
    ]
    if report.get("sources"):
        lines.extend(["", "Sources:"])
        for source in report["sources"][:12]:
            if source.get("type") == "register":
                lines.append(f"  - register {source.get('register')} -> {source.get('origin')}")
            else:
                lines.append(f"  - memory ${source.get('address')} -> {source.get('origin')}")
    if report.get("paths"):
        lines.extend(["", "Dynamic taint paths:"])
        for path in report["paths"][:12]:
            lines.append(
                f"  - S{path['score']} C{path['confidence']:.2f} "
                f"{path['title']}"
            )
            lines.append(
                f"      seq={path.get('seq')} pc=${int(path.get('pc', 0)):04X} "
                f"{path.get('mnemonic', '')}"
            )
    if report.get("write_attributions"):
        lines.extend(["", "Dynamic sink writes:"])
        for attribution in report["write_attributions"][:12]:
            lines.append(
                f"  - S{attribution.get('score', 0)} C{float(attribution.get('confidence', 0.0)):.2f} "
                f"{attribution.get('target')} at {attribution.get('pc_label')}"
            )
            lines.append(
                f"      seq={attribution.get('seq')} address=${attribution.get('address')} "
                f"{attribution.get('mnemonic', '')}"
            )
            operands = ", ".join(
                str(item)
                for item in attribution.get("evidence", [])
                if str(item).startswith("sources=")
            )
            if operands:
                lines.append(f"      {operands}")
    if report.get("trace_runs"):
        lines.extend(["", "Trace runs:"])
        for run in report["trace_runs"][:8]:
            lines.append(
                f"  - {run.get('source')} frames={run.get('frame_count', 0)} "
                f"instructions={run.get('instruction_count', 0)} "
                f"findings={run.get('finding_count', 0)} "
                f"writes={run.get('write_attribution_count', 0)} "
                f"unsupported={run.get('unsupported_count', 0)}"
            )
    if report["commands"]:
        lines.extend(["", "Top proof commands:"])
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_instruction_trace(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger instruction trace",
        (
            f"valid={report['valid']} executed={report['executed']} "
            f"functions={report['function_count']} instructions={report['instruction_count']} "
            f"captured={report['captured_frame_count']} watches={report['watch_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
        f"rom={report['rom']} sha256={report['rom_sha256'][:12]}",
        f"symbols={report['symbols']} sha256={report['symbols_sha256'][:12]}",
    ]
    input_save_state = report.get("input_save_state", "")
    effective_save_state = report.get("effective_save_state", report.get("save_state", ""))
    if input_save_state:
        lines.append(f"save_state={input_save_state}")
    if effective_save_state and effective_save_state != input_save_state:
        source = report.get("save_state_discovery", {}).get("selected", {}).get("source", "")
        lines.append(f"effective_save_state={effective_save_state} source={source}")
    if report.get("trace_output", {}).get("path"):
        trace_output = report["trace_output"]
        state = "written" if trace_output.get("written") else "planned"
        lines.append(f"trace={trace_output['path']} {state} records={trace_output.get('record_count', 0)}")
    selection = report.get("target_selection")
    if isinstance(selection, dict):
        functions = ", ".join(selection.get("function_symbols", [])[:8])
        watches = ", ".join(selection.get("watch_symbols", [])[:8])
        lines.append(f"selected_functions={functions or '<none>'}")
        lines.append(f"selected_watches={watches or '<none>'}")
    validation = report.get("execution_validation")
    if isinstance(validation, dict):
        hit_functions = ", ".join(validation.get("hit_function_symbols", [])[:8])
        missing_functions = ", ".join(validation.get("missing_function_symbols", [])[:8])
        lines.append(
            "execution_validation="
            f"attempted={validation.get('attempted')} "
            f"required={validation.get('required')} "
            f"hit={validation.get('hit')} "
            f"captured_functions={validation.get('captured_function_count', 0)} "
            f"ready_for_dynamic_taint={validation.get('ready_for_dynamic_taint')}"
        )
        if hit_functions:
            lines.append(f"hit_functions={hit_functions}")
        if missing_functions:
            lines.append(f"missing_functions={missing_functions}")
    if report.get("functions"):
        lines.extend(["", "Functions:"])
        for function in report["functions"][:12]:
            lines.append(
                f"  - {function['symbol']} {function.get('bank_address', '')} "
                f"instructions={function.get('instruction_count', 0)} hooks={function.get('hook_count', 0)}"
            )
            for instruction in function.get("instructions", [])[:4]:
                lines.append(
                    f"      {instruction['bank_address']} {instruction['mnemonic']}"
                )
    if report.get("sample_records"):
        lines.extend(["", "Captured sample:"])
        for record in report["sample_records"][:8]:
            lines.append(
                f"  - seq={record.get('seq')} {record.get('pc_bank_address')} "
                f"{record.get('mnemonic')}"
            )
    if report["commands"]:
        lines.extend(["", "Top proof commands:"])
        for command in report["commands"][:10]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_watch(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger watch replay",
        (
            f"valid={report['valid']} executed={report['executed']} "
            f"frames={report['frames']} context={report.get('context_frames', 0)} "
            f"hits={report['hit_count']} dynamic_context={report.get('dynamic_context_event_count', 0)}"
        ),
        f"rom={report['rom']} sha256={report['rom_sha256'][:12]}",
        f"symbols={report['symbols']} sha256={report['symbols_sha256'][:12]}",
        "",
        "Watches:",
    ]
    for watch in report["watches"]:
        location = watch["bank_address"] if watch["found"] else "not-found"
        lines.append(f"  - {watch['name']} {location} size={watch['size']}")
        for command in watch.get("suggested_commands", [])[:2]:
            lines.append(f"      command: {command}")
    if report["events"]:
        lines.append("Events:")
        for event in report["events"][:20]:
            lines.append(
                f"  - frame={event['frame']} {event['watch']} "
                f"{event['old_hex']}->{event['new_hex']} "
                f"pc={event['pc_bank_address']} {event['pc_label']}"
            )
            cause = event.get("source_cause") if isinstance(event.get("source_cause"), dict) else {}
            context = event.get("dynamic_context") if isinstance(event.get("dynamic_context"), dict) else {}
            if context.get("context_frame_count"):
                lines.append(
                    f"      context: {context['context_frame_count']} prior frame snapshots"
                )
            for candidate in cause.get("candidates", [])[:2]:
                lines.append(
                    f"      cause: S{candidate.get('score', 0)} "
                    f"{candidate.get('access', 'reference')} "
                    f"{candidate.get('source_file', '')}:{candidate.get('line', '')}"
                )
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_replay_plan(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger replay plan",
        (
            f"valid={report['valid']} phases={report['phase_count']} "
            f"watch_symbols={report['watch_symbol_count']} symbols={report['symbol_count']} "
            f"sources={report['source_file_count']} scenarios={report['scenario_id_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
        f"rom={report['rom']} symbols={report['symbols_path']} frames={report['frames']} context={report.get('context_frames', 0)}",
    ]
    if report.get("save_state"):
        lines.append(f"save_state={report['save_state']}")
    if report.get("effective_save_state") and report.get("effective_save_state") != report.get("save_state"):
        source = report.get("save_state_discovery", {}).get("selected", {}).get("source", "")
        lines.append(f"effective_save_state={report['effective_save_state']} source={source}")
    targets = report.get("replay_targets", {})
    if targets.get("watch_symbols"):
        lines.extend(["", "Watch targets:"])
        for symbol in targets["watch_symbols"][:12]:
            lines.append(f"  - {symbol}")
    if targets.get("source_files"):
        lines.extend(["", "Source targets:"])
        for path in targets["source_files"][:8]:
            lines.append(f"  - {path}")
    watch_report = report.get("watch_report")
    if watch_report:
        lines.extend(
            [
                "",
                (
                    f"Executed watch: valid={watch_report['valid']} "
                    f"hits={watch_report['hit_count']}"
                ),
            ]
        )
        for event in watch_report.get("events", [])[:8]:
            lines.append(
                f"  - frame={event['frame']} {event['watch']} "
                f"{event['old_hex']}->{event['new_hex']} at {event['pc_bank_address']} {event['pc_label']}"
            )
            cause = event.get("source_cause") if isinstance(event.get("source_cause"), dict) else {}
            if cause.get("candidate_count"):
                lines.append(
                    f"      source_cause_candidates={cause['candidate_count']} "
                    f"top={cause['candidates'][0].get('source_file', '')}:{cause['candidates'][0].get('line', '')}"
                )
    if report["phase_steps"]:
        lines.extend(["", "Plan:"])
        for phase in report["phase_steps"]:
            lines.append(f"  {phase['title']}:")
            for step in phase["steps"][:8]:
                runnable = "runnable" if step["runnable"] else "needs-input"
                lines.append(f"    - {step['command']} ({runnable})")
                lines.append(f"        reason: {step['reason']}")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_setup_plan(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger setup plan",
        (
            f"valid={report['valid']} surfaces={report['surface_count']} "
            f"targets={report['target_count']} commands={report['command_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
        f"rom={report['rom']} symbols={report['symbols_path']}",
        f"scenario_manifest={report['scenario_manifest']}",
    ]
    if report.get("effective_save_state"):
        source = report.get("save_state_discovery", {}).get("selected", {}).get("source", "")
        lines.append(f"effective_save_state={report['effective_save_state']} source={source}")
    state = report.get("state_requirements", {})
    lines.append(
        "state="
        f"save_state_supplied={state.get('save_state_supplied')} "
        f"save_state_discovered={state.get('save_state_discovered')} "
        f"requires_positioned_state={state.get('requires_positioned_state')}"
    )
    coverage = report.get("trigger_coverage", {})
    if isinstance(coverage, dict):
        lines.append(
            "trigger_coverage="
            f"covered={coverage.get('covered_target_count', 0)} "
            f"planned={coverage.get('planned_target_count', 0)} "
            f"blocked={coverage.get('blocked_target_count', 0)} "
            f"ratio={coverage.get('coverage_ratio', 0.0)}"
        )
    if report.get("surfaces"):
        lines.append(f"surfaces={', '.join(report['surfaces'])}")
    for target in report.get("targets", [])[:8]:
        lines.extend(["", f"{target.get('surface')}: {target.get('title')}"])
        target_coverage = next(
            (
                row for row in coverage.get("targets", [])
                if isinstance(row, dict) and row.get("surface") == target.get("surface")
            ),
            {},
        ) if isinstance(coverage, dict) else {}
        if target_coverage:
            lines.append(
                "  coverage="
                f"{target_coverage.get('status')} "
                f"state={target_coverage.get('state_status')} "
                f"trigger={target_coverage.get('trigger_status', {}).get('status')} "
                f"validation={target_coverage.get('validation_status', {}).get('status')}"
            )
            blockers = target_coverage.get("blockers", [])
            if blockers:
                lines.append("  blockers=" + ", ".join(str(item) for item in blockers[:6]))
        recipes = target.get("state_synthesis_recipes", [])
        if recipes:
            lines.append("  state_synthesis_recipes:")
            for recipe in recipes[:4]:
                produces = ", ".join(str(item) for item in recipe.get("produces", [])[:4])
                lines.append(
                    f"    - {recipe.get('id')} status={recipe.get('status')} produces={produces}"
                )
                for command in recipe.get("commands", [])[:2]:
                    runnable = "runnable" if command.get("runnable") else "needs-input"
                    lines.append(f"        {command.get('command')} ({runnable})")
                for precondition in recipe.get("preconditions", [])[:3]:
                    values = precondition.get("values", {}) if isinstance(precondition.get("values"), dict) else {}
                    value_text = ", ".join(
                        f"{key}={value}"
                        for key, value in values.items()
                        if value not in {"", None}
                    )
                    scenario_id = precondition.get("scenario_id", "")
                    lines.append(
                        f"        precondition: {scenario_id} {precondition.get('kind', '')} {value_text}".rstrip()
                    )
        for group_name in ("setup_commands", "state_recipe_commands", "trigger_commands", "validation_commands"):
            records = target.get(group_name, [])
            if not records:
                continue
            lines.append(f"  {group_name}:")
            for record in records[:4]:
                runnable = "runnable" if record.get("runnable") else "needs-input"
                lines.append(f"    - {record.get('command')} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_explanation(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger causal explanation",
        (
            f"valid={report['valid']} paths={report['path_count']} "
            f"events={report['dynamic_event_count']} traces={report['trace_observation_count']} "
            f"content_scenarios={report.get('content_scenario_count', 0)} "
            f"targets={report['target_symbol_count']} symbols/{report['target_file_count']} files "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
    ]
    if report.get("symptom"):
        lines.append(f"symptom={report['symptom']}")
    if report.get("target_symbols"):
        lines.append("symbols=" + ", ".join(report["target_symbols"][:10]))
    if report.get("target_files"):
        lines.append("source_files=" + ", ".join(report["target_files"][:8]))
    if report["paths"]:
        lines.extend(["", "Causal paths:"])
        for path in report["paths"][:12]:
            lines.append(
                f"  - S{path['score']} C{path['confidence']:.2f} {path['id']}: {path['title']}"
            )
            for item in path.get("nodes", [])[:6]:
                location = ""
                if item.get("file"):
                    location = f" {item['file']}:{item.get('line', '')}".rstrip(":")
                lines.append(f"      {item['type']}/{item['role']}: {item['label']}{location}")
            for evidence in path.get("evidence", [])[:3]:
                lines.append(f"      evidence: {evidence}")
            for command in path.get("commands", [])[:2]:
                lines.append(f"      next: {command}")
    if report["commands"]:
        lines.extend(["", "Top proof commands:"])
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_test_suggestions(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger test suggestions",
        f"matches={report['match_count']}",
    ]
    if report["changed_files"]:
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report["symbols"]:
        lines.append("symbols=" + ", ".join(report["symbols"]))
    if report["symptom"]:
        lines.append(f"symptom={report['symptom']}")
    lines.extend(["", "Matches:"])
    for match in report["matches"]:
        lines.append(
            f"  - {match['id']} - {match['title']} "
            f"({', '.join(match['matched_by'])})"
        )
        for note in match.get("notes", [])[:2]:
            lines.append(f"      note: {note}")
    lines.extend(["", "Generator/check commands:"])
    for command in report["commands"]:
        lines.append(f"  - {command}")
    lines.extend(["", "Counterexample commands:"])
    for command in report["counterexample_commands"]:
        lines.append(f"  - {command}")
    return "\n".join(lines)


def format_compare_plan(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger compare plan",
        f"matches={report['match_count']}",
    ]
    if report["changed_files"]:
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report.get("input_reports"):
        lines.append("reports=" + ", ".join(report["input_reports"]))
    if report["symbols"]:
        lines.append("symbols=" + ", ".join(report["symbols"]))
    if report["symptom"]:
        lines.append(f"symptom={report['symptom']}")
    lines.extend(["", "Mirrors:"])
    for match in report["matches"]:
        lines.append(
            f"  - {match['id']} - {match['title']} "
            f"({', '.join(match['matched_by'])})"
        )
        lines.append(f"      confidence: {match['confidence']}")
        for gap in match.get("gaps", [])[:2]:
            lines.append(f"      gap: {gap}")
    lines.extend(["", "Compare commands:"])
    for command in report["commands"]:
        lines.append(f"  - {command}")
    lines.extend(["", "Materialization/proof commands:"])
    for command in report["materialization_commands"]:
        lines.append(f"  - {command}")
    return "\n".join(lines)


def format_content_mirror(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger content mirror",
        (
            f"valid={report['valid']} passed={report['passed']} "
            f"sources={report['source_file_count']} invariants={report['invariant_count']} "
            f"rom_mirrors={report.get('rom_mirror_count', 0)} "
            f"failed={report['failed_invariant_count']} warnings={report['warning_count']} "
            f"errors={report['error_count']}"
        ),
    ]
    if report.get("rom"):
        state = "available" if report.get("rom_available") else "not-found"
        lines.append(f"rom={report.get('rom')} symbols={report.get('symbols_path')} ({state})")
    if report.get("changed_files"):
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report.get("requested_source_files"):
        lines.append("source_files=" + ", ".join(report["requested_source_files"]))
    if report["source_files"]:
        lines.extend(["", "Sources:"])
        for source in report["source_files"][:20]:
            macro_counts = source.get("macro_counts", {})
            event_counts = source.get("map_event_counts", {})
            event_summary = ", ".join(
                f"{name}={count}"
                for name, count in event_counts.items()
                if count
            )
            lines.append(
                f"  - {source['path']} labels={source.get('global_label_count', 0)} "
                f"assets={source.get('asset_count', 0)}"
            )
            if event_summary:
                lines.append(f"      map events: {event_summary}")
            if source.get("rom_mirror_count"):
                lines.append(f"      rom mirrors: {source.get('rom_mirror_count')}")
            if macro_counts.get("INCBIN"):
                lines.append(f"      incbin={macro_counts['INCBIN']}")
    if report.get("rom_mirrors"):
        lines.extend(["", "ROM mirrors:"])
        for item in report["rom_mirrors"][:12]:
            line = int(item.get("line", 0))
            location = f"{item['source_file']}:{line}" if line else str(item["source_file"])
            lines.append(f"  - {item['status']} S{item['severity']} {item['title']} ({location})")
            for evidence in item.get("evidence", [])[:3]:
                lines.append(f"      evidence: {evidence}")
    if report["failed_invariants"]:
        lines.extend(["", "Failed invariants:"])
        for item in report["failed_invariants"][:20]:
            line = int(item.get("line", 0))
            location = f"{item['source_file']}:{line}" if line else str(item["source_file"])
            lines.append(f"  - S{item['severity']} {item['type']}: {item['title']} ({location})")
            for evidence in item.get("evidence", [])[:2]:
                lines.append(f"      evidence: {evidence}")
            for command in item.get("commands", [])[:2]:
                runnable = "runnable" if command_is_runnable(command) else "needs-input"
                lines.append(f"      next: {command} ({runnable})")
    if report["commands"]:
        lines.extend(["", "Top proof commands:"])
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_content_scenarios(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger content scenarios",
        (
            f"valid={report['valid']} scenarios={report['scenario_count']} "
            f"behavioral_probes={report.get('behavioral_probe_count', 0)} "
            f"runtime_probes={report.get('runtime_probe_count', 0)} "
            f"sources={report['source_file_count']} errors={report['error_count']} "
            f"warnings={report['warning_count']}"
        ),
    ]
    manifest = report.get("scenario_manifest", {})
    if manifest.get("written"):
        lines.append(f"manifest={manifest.get('path', '')} records={manifest.get('record_count', 0)}")
    if report.get("changed_files"):
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report.get("requested_source_files"):
        lines.append("source_files=" + ", ".join(report["requested_source_files"]))
    if report["scenarios"]:
        lines.extend(["", "Scenarios:"])
        for scenario in report["scenarios"][:20]:
            trigger = scenario.get("trigger", {})
            trigger_text = ", ".join(f"{key}={value}" for key, value in trigger.items() if value)
            lines.append(
                f"  - {scenario['id']} {scenario['scenario_type']} "
                f"{scenario['source_file']}:{scenario.get('line', 0)}"
            )
            if trigger_text:
                lines.append(f"      trigger: {trigger_text}")
            runtime_targets = scenario.get("runtime_targets") if isinstance(scenario.get("runtime_targets"), dict) else {}
            trace_symbols = runtime_targets.get("trace_symbols", [])
            watch_symbols = runtime_targets.get("watch_symbols", [])
            if trace_symbols:
                lines.append("      trace: " + ", ".join(str(symbol) for symbol in trace_symbols[:5]))
            if watch_symbols:
                lines.append("      watch: " + ", ".join(str(symbol) for symbol in watch_symbols[:5]))
            for command in scenario.get("commands", [])[:2]:
                runnable = "runnable" if command_is_runnable(command) else "needs-input"
                lines.append(f"      next: {command} ({runnable})")
            for probe in scenario.get("behavioral_probes", [])[:3]:
                runnable = "runnable" if probe.get("runnable") else "needs-input"
                lines.append(
                    f"      probe: {probe.get('phase')} {probe.get('command')} ({runnable})"
                )
    if report["commands"]:
        lines.extend(["", "Top scenario commands:"])
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_content_state(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger content state materialization",
        (
            f"valid={report['valid']} executed={report['executed']} "
            f"scenarios={report['scenario_count']} materializations={report['materialization_count']} "
            f"patches={report['patch_count']} errors={report['error_count']} warnings={report['warning_count']}"
        ),
        f"rom={report.get('rom', '')} symbols={report.get('symbols', '')}",
    ]
    if report.get("base_save_state") or report.get("out_state"):
        lines.append(f"base_state={report.get('base_save_state', '')} out_state={report.get('out_state', '')}")
    for item in report.get("materializations", [])[:12]:
        lines.extend(["", f"{item.get('scenario_id')}: {item.get('precondition_kind')} status={item.get('status')}"])
        if item.get("map_name"):
            resolution = item.get("map_resolution", {}) if isinstance(item.get("map_resolution"), dict) else {}
            lines.append(
                "  map="
                f"{item.get('map_name')} group={resolution.get('map_group', 0)} "
                f"number={resolution.get('map_number', 0)}"
            )
        for patch in item.get("patches", [])[:8]:
            lines.append(
                f"  patch {patch.get('symbol')}={patch.get('value_hex')} "
                f"@{patch.get('bank_address')}"
            )
        for error in item.get("errors", [])[:4]:
            lines.append(f"  error: {error}")
    execution = report.get("execution", {})
    if execution.get("executed"):
        lines.extend(["", f"wrote={execution.get('out_state', '')} patches={execution.get('patch_count', 0)}"])
    if report.get("commands"):
        lines.extend(["", "Commands:"])
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_state_space(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger state-space materialization",
        (
            f"valid={report['valid']} executed={report['executed']} "
            f"patches={report['patch_count']} errors={report['error_count']} "
            f"warnings={report['warning_count']}"
        ),
        f"rom={report.get('rom', '')} symbols={report.get('symbols', '')}",
    ]
    if report.get("scenario_id"):
        lines.append(f"scenario={report['scenario_id']}")
    if report.get("source_files"):
        lines.append("source_files=" + ", ".join(report["source_files"]))
    if report.get("base_save_state") or report.get("out_state"):
        lines.append(f"base_state={report.get('base_save_state', '')} out_state={report.get('out_state', '')}")
    state_space = report.get("state_space") if isinstance(report.get("state_space"), dict) else {}
    patches = state_space.get("patches", [])
    if patches:
        lines.extend(["", "Patches:"])
        for patch in patches[:16]:
            status = patch.get("status") or patch.get("materialization_status") or "planned"
            lines.append(
                f"  - {status}: {patch.get('symbol')}={patch.get('value_hex')} "
                f"@{patch.get('bank_address')}"
            )
            if patch.get("observed_hex"):
                lines.append(
                    f"      observed={patch.get('observed_hex')} verified={patch.get('verified')}"
                )
            for error in patch.get("errors", [])[:3]:
                lines.append(f"      error: {error}")
    execution = report.get("execution", {}) if isinstance(report.get("execution"), dict) else {}
    if execution.get("executed"):
        lines.extend(["", f"wrote={execution.get('out_state', '')} patches={execution.get('patch_count', 0)}"])
    if report.get("commands"):
        lines.extend(["", "Commands:"])
        for command in report["commands"][:9]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_expectation_report(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger expectation report",
        (
            f"valid={report['valid']} passed={report['passed']} "
            f"expectations={report['expectation_count']} passed_count={report['passed_count']} "
            f"failed={report['failed_count']} skipped={report['skipped_count']} "
            f"events={report['evidence_event_count']} errors={report['error_count']} warnings={report['warning_count']}"
        ),
    ]
    if (
        report.get("evidence_scenario_count")
        or report.get("evidence_state_precondition_count")
        or report.get("evidence_state_patch_count")
    ):
        lines.append(
            "state_evidence="
            + f"scenarios={report.get('evidence_scenario_count', 0)} "
            + f"preconditions={report.get('evidence_state_precondition_count', 0)} "
            + f"patches={report.get('evidence_state_patch_count', 0)}"
        )
    if report.get("symptom"):
        lines.append(f"symptom={report['symptom']}")
    if report["input_reports"]:
        lines.append("reports=" + ", ".join(report["input_reports"]))
    if report["input_traces"]:
        lines.append("traces=" + ", ".join(report["input_traces"]))
    if report["expectations"]:
        lines.extend(["", "Expectations:"])
        for item in report["expectations"][:30]:
            lines.append(
                f"  - {item['status']} {item['id']} "
                f"({item['type']}) observed={item['observed_count']}"
            )
            for evidence in item.get("evidence", [])[:3]:
                lines.append(f"      evidence: {evidence}")
            for command in item.get("commands", [])[:2]:
                runnable = "runnable" if command_is_runnable(command) else "needs-input"
                lines.append(f"      next: {command} ({runnable})")
    summary = report.get("evidence_summary", {})
    if summary:
        lines.extend(["", "Evidence:"])
        for key in ("symbols", "rules", "source_files", "addresses", "scenario_ids"):
            values = summary.get(key, [])
            if values:
                lines.append(f"  - {key}: " + ", ".join(values[:8]))
    if report["commands"]:
        lines.extend(["", "Top proof commands:"])
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_ranked_findings(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger ranked findings",
        (
            f"valid={report['valid']} reports={report['report_count']} "
            f"findings={report['finding_count']} errors={report['error_count']}"
        ),
    ]
    if report["errors"]:
        lines.append("Errors:")
        for error in report["errors"][:5]:
            lines.append(f"  - {error}")
    if report["findings"]:
        lines.append("Findings:")
        for item in report["findings"][:30]:
            lines.append(
                f"  - S{item['severity']} C{item['confidence']:.2f} "
                f"{item['type']}: {item['title']}"
            )
            for evidence in item.get("evidence", [])[:2]:
                lines.append(f"      evidence: {evidence}")
            for action in item.get("next_actions", [])[:2]:
                lines.append(f"      next: {action}")
    return "\n".join(lines)


def format_impact_report(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger impact report",
        (
            f"valid={report['valid']} reports={report['loaded_report_count']}/{report['report_count']} "
            f"items={report['impact_count']} commands={report['command_count']} errors={report['error_count']}"
        ),
    ]
    if report.get("changed_files"):
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report.get("symbols"):
        lines.append("symbols=" + ", ".join(report["symbols"]))
    if report.get("symptom"):
        lines.append(f"symptom={report['symptom']}")
    if report["errors"]:
        lines.append("Errors:")
        for error in report["errors"][:5]:
            lines.append(f"  - {error}")
    if report["items"]:
        lines.append("Impact queue:")
        for item in report["items"][:30]:
            lines.append(
                f"  - I{item['impact_score']} S{item['severity']} C{item['confidence']:.2f} "
                f"{item['type']} [{item['surface']}]: {item['title']}"
            )
            for evidence in item.get("evidence", [])[:2]:
                lines.append(f"      evidence: {evidence}")
            for action in item.get("next_actions", [])[:2]:
                lines.append(f"      next: {action}")
    if report["commands"]:
        lines.append("Top proof commands:")
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    return "\n".join(lines)


def format_static_report(report: dict[str, Any]) -> str:
    if report.get("out"):
        return "\n".join(
            [
                "Unified Pokemon Gold romhack debugger static report",
                (
                    f"valid={report['valid']} format={report['format']} "
                    f"reports={report['loaded_report_count']}/{report['requested_report_count']} "
                    f"findings={report['finding_count']} errors={report['error_count']}"
                ),
                f"out={report['out']}",
            ]
        )
    return str(report["content"])


def format_visualization(report: dict[str, Any]) -> str:
    if report.get("out"):
        return "\n".join(
            [
                "Unified Pokemon Gold romhack debugger visualization",
                (
                    f"valid={report['valid']} format={report['format']} "
                    f"reports={report['loaded_report_count']}/{report['report_count']} "
                    f"traces={report['trace_count']} timeline={report['timeline_event_count']} "
                    f"waterfall={report['waterfall_step_count']} graph={report['graph_node_count']}/{report['graph_edge_count']} "
                    f"errors={report['error_count']}"
                ),
                f"out={report['out']}",
            ]
        )
    lines = [
        "Unified Pokemon Gold romhack debugger visualization",
        (
            f"valid={report['valid']} format={report['format']} "
            f"reports={report['loaded_report_count']}/{report['report_count']} "
            f"traces={report['trace_count']} timeline={report['timeline_event_count']} "
            f"waterfall={report['waterfall_step_count']} graph={report['graph_node_count']}/{report['graph_edge_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
    ]
    if report["lane_summary"]:
        lines.append("Lanes:")
        for lane in report["lane_summary"][:12]:
            lines.append(
                f"  - {lane['lane']}: count={lane['count']} max_severity={lane['max_severity']}"
            )
    if report["timeline"]:
        lines.append("Timeline:")
        for item in report["timeline"][:12]:
            lines.append(f"  - S{item['severity']} {item['lane']}/{item['type']}: {item['title']}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def write_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
