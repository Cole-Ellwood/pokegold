from __future__ import annotations

import argparse
from pathlib import Path

from .cli_helpers import add_output_args
from .commands import (
    cmd_audit,
    cmd_compare,
    cmd_content_mirror,
    cmd_content_scenarios,
    cmd_content_state,
    cmd_coverage,
    cmd_dynamic_taint,
    cmd_expect,
    cmd_explain,
    cmd_fuzz,
    cmd_gate,
    cmd_generate,
    cmd_grass_regrowth,
    cmd_impact,
    cmd_ingest,
    cmd_inventory,
    cmd_investigate,
    cmd_learnset_inspect,
    cmd_localize,
    cmd_minimize,
    cmd_next,
    cmd_party_inspect,
    cmd_provenance,
    cmd_prove,
    cmd_rank,
    cmd_replay,
    cmd_report,
    cmd_repro_recipe,
    cmd_save_state_inspect,
    cmd_script_resume_gate,
    cmd_setup,
    cmd_slice,
    cmd_state_inspect,
    cmd_state_space,
    cmd_suggest_tests,
    cmd_taint,
    cmd_trace_index,
    cmd_trace_instructions,
    cmd_triage,
    cmd_visualize,
    cmd_watch,
    cmd_wram_bank_hazards,
    cmd_wram_lifetime,
    cmd_wram_ownership,
)


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

    next_step = subparsers.add_parser("next")
    next_step.add_argument("--changed-file", action="append", default=[])
    next_step.add_argument("--symptom", default="")
    add_output_args(next_step)
    next_step.set_defaults(func=cmd_next)

    prove = subparsers.add_parser("prove")
    prove.add_argument("--changed-file", action="append", default=[])
    prove.add_argument("--symptom", default="")
    prove.add_argument("--execute", action="store_true")
    prove.add_argument("--timeout-seconds", type=int, default=120)
    prove.add_argument("--prefer", choices=["first", "gate", "escalation"], default="first")
    prove.add_argument("--suite", type=Path)
    prove.add_argument("--all-routes", action="store_true")
    prove.add_argument("--max-commands", type=int, default=50)
    add_output_args(prove)
    prove.set_defaults(func=cmd_prove)

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
    investigate.add_argument("--patch", action="append", default=[])
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
    minimize.add_argument("--execute-state-patches", action="store_true")
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
    watch.add_argument("--battery-save", default="")
    watch.add_argument("--boot-continue", action="store_true")
    watch.add_argument("--input", action="append", default=[])
    watch.add_argument("--out-initial-state", default="")
    watch.add_argument("--watch-symbol", action="append", default=[])
    watch.add_argument("--frames", type=int, default=60)
    watch.add_argument("--context-frames", type=int, default=12)
    watch.add_argument("--execute", action="store_true")
    watch.add_argument("--reset-sentinel", action="store_true")
    watch.add_argument("--sentinel-symbol", action="append", default=[])
    add_output_args(watch)
    watch.set_defaults(func=cmd_watch)

    state_inspect = subparsers.add_parser("state-inspect")
    state_inspect.add_argument("--rom", default="pokegold.gbc")
    state_inspect.add_argument("--symbols", default="pokegold.sym")
    state_inspect.add_argument("--save-state", required=True)
    add_output_args(state_inspect)
    state_inspect.set_defaults(func=cmd_state_inspect)

    inspect_state = subparsers.add_parser("inspect-state")
    inspect_state.add_argument("--rom", default="pokegold.gbc")
    inspect_state.add_argument("--symbols", default="pokegold.sym")
    inspect_state.add_argument("--save-state", required=True)
    add_output_args(inspect_state)
    inspect_state.set_defaults(func=cmd_save_state_inspect)

    save_state_inspect = subparsers.add_parser("save-state-inspect")
    save_state_inspect.add_argument("--rom", default="pokegold.gbc")
    save_state_inspect.add_argument("--symbols", default="pokegold.sym")
    save_state_inspect.add_argument("--save-state", required=True)
    add_output_args(save_state_inspect)
    save_state_inspect.set_defaults(func=cmd_save_state_inspect)

    learnset_inspect = subparsers.add_parser("learnset-inspect")
    learnset_inspect.add_argument("--species", required=True)
    learnset_inspect.add_argument("--level", type=int, required=True)
    add_output_args(learnset_inspect)
    learnset_inspect.set_defaults(func=cmd_learnset_inspect)

    party_inspect = subparsers.add_parser("party-inspect")
    party_inspect.add_argument("--save", required=True)
    party_inspect.add_argument("--slot", type=int, action="append", default=[])
    party_inspect.add_argument("--rom", default="pokegold.gbc")
    party_inspect.add_argument("--symbols", default="pokegold.sym")
    add_output_args(party_inspect)
    party_inspect.set_defaults(func=cmd_party_inspect)

    grass_regrowth = subparsers.add_parser("grass-regrowth")
    grass_regrowth.add_argument("--max-total-hp", type=int, default=300)
    add_output_args(grass_regrowth)
    grass_regrowth.set_defaults(func=cmd_grass_regrowth)

    wram_bank_hazards = subparsers.add_parser("wram-bank-hazards")
    wram_bank_hazards.add_argument("--source-file", action="append", default=[])
    add_output_args(wram_bank_hazards)
    wram_bank_hazards.set_defaults(func=cmd_wram_bank_hazards)

    script_resume_gate = subparsers.add_parser("script-resume-gate")
    script_resume_gate.add_argument("--report", action="append", default=[])
    add_output_args(script_resume_gate)
    script_resume_gate.set_defaults(func=cmd_script_resume_gate)

    wram_ownership = subparsers.add_parser("wram-ownership")
    wram_ownership.add_argument("--symbol", action="append", default=[])
    wram_ownership.add_argument("--source-file", default="ram/wram.asm")
    add_output_args(wram_ownership)
    wram_ownership.set_defaults(func=cmd_wram_ownership)

    wram_lifetime = subparsers.add_parser("wram-lifetime")
    wram_lifetime.add_argument("--symbol", action="append", default=[])
    wram_lifetime.add_argument("--through", default="Script_startbattle")
    wram_lifetime.add_argument("--source-file", default="engine/overworld/scripting.asm")
    wram_lifetime.add_argument("--symbols", default="pokegold.sym")
    add_output_args(wram_lifetime)
    wram_lifetime.set_defaults(func=cmd_wram_lifetime)

    repro_recipe = subparsers.add_parser("repro-recipe")
    repro_recipe.add_argument("--id", action="append", default=[])
    repro_recipe.add_argument("--symptom", default="")
    add_output_args(repro_recipe)
    repro_recipe.set_defaults(func=cmd_repro_recipe)

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
    tests.add_argument("--report", action="append", default=[])
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
