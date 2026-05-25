from __future__ import annotations

import argparse
from pathlib import Path

from tools.boss_ai_preference.data import (
    ALLOWED_LABELS,
    DEFAULT_FIXTURES_PATH,
    DEFAULT_JSON_REPORT_PATH,
    DEFAULT_LABELS_PATH,
    DEFAULT_PREFERENCES_PATH,
    DEFAULT_REPORT_PATH,
)

from .commands import (
    cmd_batch_simulate,
    cmd_coach_plan_templates,
    cmd_confidence_report,
    cmd_counterfactual,
    cmd_coverage_report,
    cmd_coverage_search,
    cmd_damage_ai_report,
    cmd_decision_trace,
    cmd_diff,
    cmd_generate,
    cmd_haki_coverage,
    cmd_inspect,
    cmd_invariants_mine,
    cmd_judge,
    cmd_list,
    cmd_localize,
    cmd_mastery_index_build,
    cmd_metamorphic,
    cmd_minimize,
    cmd_move_score_probe,
    cmd_mutate,
    cmd_python_contribution_trace,
    cmd_regress,
    cmd_replay_import,
    cmd_report,
    cmd_review_queue,
    cmd_role_packages,
    cmd_rom_contribution_trace,
    cmd_rom_score_materialize,
    cmd_rom_selector_materialize,
    cmd_rom_switch_materialize,
    cmd_route_eval,
    cmd_rule_map_build,
    cmd_rule_map_check,
    cmd_run_suite,
    cmd_simulate,
    cmd_state_schema_validate,
    cmd_trace_replay,
)
from .coverage_report import DEFAULT_COVERAGE_PATH
from .coverage_search import (
    DEFAULT_COVERAGE_SEARCH_REPORT,
    DEFAULT_COVERAGE_SEARCH_SCENARIOS,
)
from .generators import FAMILIES as GENERATOR_FAMILIES
from .invariants import (
    DEFAULT_INVARIANTS_JSON_PATH,
    DEFAULT_INVARIANTS_MD_PATH,
)
from .mastery_index import DEFAULT_MASTERY_INDEX_PATH
from .move_score_probe import DEFAULT_SCORE_BASE_ROUTE
from .replay_import import DEFAULT_REPLAY_IMPORT_REPORT
from .rom_score_materialize import (
    DEFAULT_BASE_ROUTE as DEFAULT_SCORE_MATERIALIZE_ROUTE,
    DEFAULT_WATCH_FRAMES as DEFAULT_SCORE_MATERIALIZE_WATCH_FRAMES,
)
from .rom_selector_materialize import (
    DEFAULT_BASE_ROUTE as DEFAULT_SELECTOR_MATERIALIZE_ROUTE,
    DEFAULT_MANIFEST_PATH as DEFAULT_SELECTOR_MATERIALIZE_MANIFEST,
)
from .rom_switch_materialize import (
    DEFAULT_BASE_ROUTE as DEFAULT_SWITCH_MATERIALIZE_ROUTE,
    DEFAULT_WATCH_FRAMES as DEFAULT_SWITCH_MATERIALIZE_WATCH_FRAMES,
)
from .rule_map import DEFAULT_RULE_MAP_PATH
from .run_store import DEFAULT_RUNS_DIR
from .state_schema import (
    DEFAULT_TRACE_DIR,
    DEFAULT_TRACE_GLOB,
)


def path_arg(value: str) -> Path:
    return Path(value)


def add_common_paths(
    parser: argparse.ArgumentParser,
    *,
    labels_default: Path = DEFAULT_LABELS_PATH,
) -> None:
    parser.add_argument("--fixtures", type=path_arg, default=DEFAULT_FIXTURES_PATH)
    parser.add_argument("--labels", type=path_arg, default=labels_default)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m tools.boss_ai_debugger")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_cmd = subparsers.add_parser("list")
    add_common_paths(list_cmd)
    list_cmd.set_defaults(func=cmd_list)

    inspect_cmd = subparsers.add_parser("inspect")
    add_common_paths(inspect_cmd)
    inspect_cmd.add_argument("--fixture-id", required=True)
    inspect_cmd.add_argument("--json", action="store_true")
    inspect_cmd.set_defaults(func=cmd_inspect)

    judge_cmd = subparsers.add_parser("judge")
    add_common_paths(judge_cmd)
    judge_cmd.add_argument("--fixture-id", required=True)
    judge_cmd.add_argument("--action-id", required=True)
    judge_cmd.add_argument("--label", choices=ALLOWED_LABELS, required=True)
    judge_cmd.add_argument("--rank", type=int)
    judge_cmd.add_argument("--note", default="")
    judge_cmd.set_defaults(func=cmd_judge)

    report_cmd = subparsers.add_parser("report")
    add_common_paths(report_cmd)
    report_cmd.add_argument("--out", type=path_arg, default=DEFAULT_REPORT_PATH)
    report_cmd.add_argument("--json-out", type=path_arg, default=DEFAULT_JSON_REPORT_PATH)
    report_cmd.set_defaults(func=cmd_report)

    regress_cmd = subparsers.add_parser("regress")
    add_common_paths(regress_cmd, labels_default=DEFAULT_PREFERENCES_PATH)
    regress_cmd.add_argument("--threshold", type=float, default=0.80)
    regress_cmd.add_argument("--json-out", default="")
    regress_cmd.add_argument("--include-rank-labels", action="store_true")
    regress_cmd.add_argument("--quiet", action="store_true")
    regress_cmd.set_defaults(func=cmd_regress)

    simulate_cmd = subparsers.add_parser("simulate")
    simulate_source = simulate_cmd.add_mutually_exclusive_group(required=True)
    simulate_source.add_argument("--scenario", type=path_arg)
    simulate_source.add_argument(
        "--builtin",
        choices=["all_equal_late", "third_best_never_selected"],
    )
    simulate_cmd.add_argument("--json", action="store_true")
    simulate_cmd.add_argument("--no-events", action="store_true")
    simulate_cmd.set_defaults(func=cmd_simulate)

    batch_cmd = subparsers.add_parser("batch-simulate")
    batch_cmd.add_argument("--scenarios", type=path_arg, required=True)
    batch_cmd.add_argument("--expectations", type=path_arg)
    batch_cmd.add_argument("--json", action="store_true")
    batch_cmd.add_argument("--json-out", default="")
    batch_cmd.add_argument("--limit", type=int, default=20)
    batch_cmd.add_argument("--quiet", action="store_true")
    batch_cmd.add_argument("--benchmark-seconds", type=float, default=0.0)
    batch_cmd.add_argument("--fail-on-reviewable-mismatch", action="store_true")
    batch_cmd.set_defaults(func=cmd_batch_simulate)

    trace_cmd = subparsers.add_parser("trace-replay")
    trace_cmd.add_argument("--trace", type=path_arg, action="append")
    trace_cmd.add_argument("--trace-dir", type=path_arg)
    trace_cmd.add_argument("--glob", default="*_live.txt")
    trace_cmd.add_argument("--json", action="store_true")
    trace_cmd.add_argument("--json-out", default="")
    trace_cmd.add_argument("--limit", type=int, default=20)
    trace_cmd.add_argument("--quiet", action="store_true")
    trace_cmd.add_argument("--fail-on-mismatch", action="store_true")
    trace_cmd.set_defaults(func=cmd_trace_replay)

    state_cmd = subparsers.add_parser("state-schema")
    state_subcommands = state_cmd.add_subparsers(dest="state_command", required=True)
    state_validate = state_subcommands.add_parser("validate")
    state_validate.add_argument("--path", type=path_arg, action="append")
    state_validate.add_argument("--fixtures", action="store_true")
    state_validate.add_argument("--fixtures-path", type=path_arg, default=DEFAULT_FIXTURES_PATH)
    state_validate.add_argument("--trace-dir", type=path_arg)
    state_validate.add_argument("--glob", default=DEFAULT_TRACE_GLOB)
    state_validate.add_argument("--json", action="store_true")
    state_validate.set_defaults(func=cmd_state_schema_validate)

    rule_cmd = subparsers.add_parser("rule-map")
    rule_subcommands = rule_cmd.add_subparsers(dest="rule_command", required=True)
    rule_build = rule_subcommands.add_parser("build")
    rule_build.add_argument("--json", action="store_true")
    rule_build.add_argument("--json-out", default="")
    rule_build.set_defaults(func=cmd_rule_map_build)

    rule_check = rule_subcommands.add_parser("check")
    rule_check.add_argument("--rule-map", type=path_arg, default=DEFAULT_RULE_MAP_PATH)
    rule_check.set_defaults(func=cmd_rule_map_check)

    generate_cmd = subparsers.add_parser("generate")
    generate_cmd.add_argument("--family", choices=GENERATOR_FAMILIES, required=True)
    generate_cmd.add_argument("--count", type=int, required=True)
    generate_cmd.add_argument("--seed", type=int, default=1)
    generate_cmd.add_argument("--out", type=path_arg)
    generate_cmd.set_defaults(func=cmd_generate)

    replay_import_cmd = subparsers.add_parser("replay-import")
    replay_import_cmd.add_argument("--log", action="append", default=[])
    replay_import_cmd.add_argument("--mastery-doc", type=path_arg, action="append", default=[])
    replay_import_cmd.add_argument("--quick-tests", type=path_arg)
    replay_import_cmd.add_argument("--reviews", type=path_arg)
    replay_import_cmd.add_argument("--side", choices=["p1", "p2", "all"], default="all")
    replay_import_cmd.add_argument(
        "--mode",
        choices=["side-known", "spectator-public"],
        default="side-known",
    )
    replay_import_cmd.add_argument("--turn", type=int, action="append")
    replay_import_cmd.add_argument("--limit", type=int)
    replay_import_cmd.add_argument("--seed", type=int, default=1)
    replay_import_cmd.add_argument("--out", type=path_arg, required=True)
    replay_import_cmd.add_argument("--json", action="store_true")
    replay_import_cmd.add_argument("--json-out", default=str(DEFAULT_REPLAY_IMPORT_REPORT))
    replay_import_cmd.set_defaults(func=cmd_replay_import)

    coverage_search_cmd = subparsers.add_parser("coverage-search")
    coverage_search_cmd.add_argument("--scenarios", type=path_arg, required=True)
    coverage_search_cmd.add_argument("--rounds", type=int, default=2)
    coverage_search_cmd.add_argument("--per-seed", type=int, default=4)
    coverage_search_cmd.add_argument("--seed", type=int, default=1)
    coverage_search_cmd.add_argument("--generated-count", type=int, default=0)
    coverage_search_cmd.add_argument("--keep", type=int, default=100)
    coverage_search_cmd.add_argument("--out", type=path_arg, default=DEFAULT_COVERAGE_SEARCH_SCENARIOS)
    coverage_search_cmd.add_argument("--json", action="store_true")
    coverage_search_cmd.add_argument("--json-out", default=str(DEFAULT_COVERAGE_SEARCH_REPORT))
    coverage_search_cmd.set_defaults(func=cmd_coverage_search)

    review_cmd = subparsers.add_parser("review-queue")
    review_source = review_cmd.add_mutually_exclusive_group(required=True)
    review_source.add_argument("--report", type=path_arg)
    review_source.add_argument("--scenarios", type=path_arg)
    review_cmd.add_argument("--expectations", type=path_arg)
    review_cmd.add_argument("--limit", type=int, default=50)
    review_cmd.add_argument("--max-per-lesson", type=int, default=5)
    review_cmd.add_argument("--json", action="store_true")
    review_cmd.add_argument("--json-out", default="")
    review_cmd.set_defaults(func=cmd_review_queue)

    run_suite = subparsers.add_parser("run-suite")
    run_suite.add_argument("--profile", choices=["generated-smoke", "changed-ai"], required=True)
    run_suite.add_argument("--count", type=int, default=200)
    run_suite.add_argument("--seed", type=int, default=1)
    run_suite.add_argument("--run-id", default="")
    run_suite.add_argument("--runs-dir", type=path_arg, default=DEFAULT_RUNS_DIR)
    run_suite.add_argument("--trace-dir", type=path_arg, default=DEFAULT_TRACE_DIR)
    run_suite.add_argument("--rom-contribution-trace", type=path_arg, action="append")
    run_suite.add_argument("--refresh-rom-contribution-trace", action="store_true")
    run_suite.add_argument("--rom-contribution-boss-route", default="clair")
    run_suite.add_argument("--refresh-rom-score-materialization", action="store_true")
    run_suite.add_argument("--rebuild-roms", action="store_true")
    run_suite.add_argument("--refresh-live-traces", action="store_true")
    run_suite.add_argument("--json", action="store_true")
    run_suite.set_defaults(func=cmd_run_suite)

    metamorphic_cmd = subparsers.add_parser("metamorphic")
    metamorphic_cmd.add_argument("--generated", type=int, default=0)
    metamorphic_cmd.add_argument("--seed", type=int, default=1)
    metamorphic_cmd.add_argument("--json", action="store_true")
    metamorphic_cmd.add_argument("--json-out", default="")
    metamorphic_cmd.add_argument("--fail-on-mismatch", action="store_true")
    metamorphic_cmd.set_defaults(func=cmd_metamorphic)

    mutate_cmd = subparsers.add_parser("mutate")
    mutate_cmd.add_argument("--target", choices=["scorer"], default="scorer")
    add_common_paths(mutate_cmd, labels_default=DEFAULT_PREFERENCES_PATH)
    mutate_cmd.add_argument("--threshold", type=float, default=0.80)
    mutate_cmd.add_argument("--limit", type=int)
    mutate_cmd.add_argument("--json", action="store_true")
    mutate_cmd.add_argument("--json-out", default="")
    mutate_cmd.add_argument("--fail-on-survivor", action="store_true")
    mutate_cmd.set_defaults(func=cmd_mutate)

    mastery_cmd = subparsers.add_parser("mastery-index")
    mastery_subcommands = mastery_cmd.add_subparsers(dest="mastery_command", required=True)
    mastery_build = mastery_subcommands.add_parser("build")
    mastery_build.add_argument("--json", action="store_true")
    mastery_build.add_argument("--json-out", default=str(DEFAULT_MASTERY_INDEX_PATH))
    mastery_build.set_defaults(func=cmd_mastery_index_build)

    coverage_cmd = subparsers.add_parser("coverage-report")
    coverage_cmd.add_argument("--generated-count", type=int, default=250)
    coverage_cmd.add_argument("--seed", type=int, default=1)
    coverage_cmd.add_argument("--rom-contribution-trace", type=path_arg, action="append")
    coverage_cmd.add_argument("--changed-file", type=path_arg, action="append")
    coverage_cmd.add_argument("--json", action="store_true")
    coverage_cmd.add_argument("--json-out", default=str(DEFAULT_COVERAGE_PATH))
    coverage_cmd.set_defaults(func=cmd_coverage_report)

    confidence_cmd = subparsers.add_parser("confidence-report")
    confidence_cmd.add_argument("--batch-report", type=path_arg, required=True)
    confidence_cmd.add_argument("--materialization", type=path_arg, action="append")
    confidence_cmd.add_argument("--json", action="store_true")
    confidence_cmd.add_argument("--json-out", default="")
    confidence_cmd.add_argument("--limit", type=int, default=12)
    confidence_cmd.set_defaults(func=cmd_confidence_report)

    counterfactual_cmd = subparsers.add_parser("counterfactual")
    counterfactual_cmd.add_argument("--scenario", type=path_arg, required=True)
    counterfactual_cmd.add_argument("--scenario-id", default="")
    counterfactual_cmd.add_argument("--json", action="store_true")
    counterfactual_cmd.add_argument("--json-out", default="")
    counterfactual_cmd.set_defaults(func=cmd_counterfactual)

    minimize_cmd = subparsers.add_parser("minimize")
    minimize_cmd.add_argument("--scenario", type=path_arg, required=True)
    minimize_cmd.add_argument("--scenario-id", default="")
    minimize_cmd.add_argument("--json", action="store_true")
    minimize_cmd.add_argument("--json-out", default="")
    minimize_cmd.set_defaults(func=cmd_minimize)

    localize_cmd = subparsers.add_parser("localize")
    localize_source = localize_cmd.add_mutually_exclusive_group(required=True)
    localize_source.add_argument("--report", type=path_arg)
    localize_source.add_argument("--scenarios", type=path_arg)
    localize_cmd.add_argument("--json", action="store_true")
    localize_cmd.add_argument("--json-out", default="")
    localize_cmd.set_defaults(func=cmd_localize)

    route_eval_cmd = subparsers.add_parser("route-eval")
    route_eval_cmd.add_argument("--scenario", type=path_arg, required=True)
    route_eval_cmd.add_argument("--scenario-id", default="")
    route_eval_cmd.add_argument("--horizon", type=int, default=3)
    route_eval_cmd.add_argument("--json", action="store_true")
    route_eval_cmd.add_argument("--json-out", default="")
    route_eval_cmd.set_defaults(func=cmd_route_eval)

    diff_cmd = subparsers.add_parser("diff")
    diff_cmd.add_argument("--scenarios", type=path_arg)
    diff_cmd.add_argument("--trace-dir", type=path_arg)
    diff_cmd.add_argument("--glob", default="*_live.txt")
    diff_cmd.add_argument("--rom-contribution-trace", type=path_arg, action="append")
    diff_cmd.add_argument("--python-contribution-trace", type=path_arg, action="append")
    diff_cmd.add_argument("--json", action="store_true")
    diff_cmd.add_argument("--json-out", default="")
    diff_cmd.add_argument("--limit", type=int, default=20)
    diff_cmd.add_argument("--fail-on-mismatch", action="store_true")
    diff_cmd.set_defaults(func=cmd_diff)

    decision_trace_cmd = subparsers.add_parser("decision-trace")
    decision_trace_cmd.add_argument("--scenario", type=path_arg, required=True)
    decision_trace_cmd.add_argument("--scenario-id", default="")
    decision_trace_cmd.add_argument("--json", action="store_true")
    decision_trace_cmd.add_argument("--json-out", default="")
    decision_trace_cmd.add_argument("--limit", type=int, default=40)
    decision_trace_cmd.set_defaults(func=cmd_decision_trace)

    move_score_cmd = subparsers.add_parser("move-score-probe")
    move_score_cmd.add_argument("--trainer", required=False)
    move_score_cmd.add_argument("--enemy", required=False)
    move_score_cmd.add_argument("--player-save", type=path_arg)
    move_score_cmd.add_argument("--player-slot", type=int, default=1)
    move_score_cmd.add_argument(
        "--sleep-clause",
        choices=("inactive", "active", "both"),
        default="inactive",
    )
    move_score_cmd.add_argument("--rom", type=path_arg, default=Path("pokegold_trace.gbc"))
    move_score_cmd.add_argument("--symbols", type=path_arg, default=Path("pokegold_trace.sym"))
    move_score_cmd.add_argument(
        "--manifest",
        type=path_arg,
        default=Path("audit/boss_ai_trace/live_capture_manifest.json"),
    )
    move_score_cmd.add_argument("--score-base-route", default=DEFAULT_SCORE_BASE_ROUTE)
    move_score_cmd.add_argument("--enemy-stage", action="append", default=[])
    move_score_cmd.add_argument("--player-stage", action="append", default=[])
    move_score_cmd.add_argument("--enemy-current-hp", type=int)
    move_score_cmd.add_argument("--enemy-max-hp", type=int)
    move_score_cmd.add_argument("--player-current-hp", type=int)
    move_score_cmd.add_argument("--player-max-hp", type=int)
    move_score_cmd.add_argument("--battle-turn", type=int)
    move_score_cmd.add_argument("--boss-turns-elapsed", type=int)
    move_score_cmd.add_argument("--trace", action="store_true")
    move_score_cmd.add_argument("--json", action="store_true")
    move_score_cmd.add_argument("--self-test", action="store_true")
    move_score_cmd.set_defaults(func=cmd_move_score_probe)

    damage_ai_cmd = subparsers.add_parser("damage-ai-report")
    damage_ai_cmd.add_argument("--trainer", required=False)
    damage_ai_cmd.add_argument("--enemy", required=False)
    damage_ai_cmd.add_argument("--player-save", type=path_arg)
    damage_ai_cmd.add_argument("--player-slot", type=int, default=1)
    damage_ai_cmd.add_argument(
        "--sleep-clause",
        choices=("inactive", "active", "both"),
        default="both",
    )
    damage_ai_cmd.add_argument("--rom", type=path_arg, default=Path("pokegold_trace.gbc"))
    damage_ai_cmd.add_argument("--symbols", type=path_arg, default=Path("pokegold_trace.sym"))
    damage_ai_cmd.add_argument(
        "--manifest",
        type=path_arg,
        default=Path("audit/boss_ai_trace/live_capture_manifest.json"),
    )
    damage_ai_cmd.add_argument("--trace", action="store_true")
    damage_ai_cmd.add_argument("--json", action="store_true")
    damage_ai_cmd.add_argument("--self-test", action="store_true")
    damage_ai_cmd.set_defaults(func=cmd_damage_ai_report)

    python_trace_cmd = subparsers.add_parser("python-contribution-trace")
    python_trace_cmd.add_argument("--scenarios", type=path_arg, required=True)
    python_trace_cmd.add_argument("--json", action="store_true")
    python_trace_cmd.add_argument("--json-out", default="")
    python_trace_cmd.set_defaults(func=cmd_python_contribution_trace)

    rom_trace_cmd = subparsers.add_parser("rom-contribution-trace")
    rom_trace_source = rom_trace_cmd.add_mutually_exclusive_group(required=True)
    rom_trace_source.add_argument("--save-state", type=path_arg)
    rom_trace_source.add_argument("--boss-route")
    rom_trace_cmd.add_argument("--rom", type=path_arg, default=Path("pokegold_trace.gbc"))
    rom_trace_cmd.add_argument("--symbols", type=path_arg, default=Path("pokegold_trace.sym"))
    rom_trace_cmd.add_argument("--battery-save", type=path_arg)
    rom_trace_cmd.add_argument("--out-dir", type=path_arg)
    rom_trace_cmd.add_argument("--input-wait-frames", type=int, default=0)
    rom_trace_cmd.add_argument("--max-a-presses", type=int, default=0)
    rom_trace_cmd.add_argument("--button", default="a")
    rom_trace_cmd.add_argument("--button-delay", type=int, default=8)
    rom_trace_cmd.add_argument("--watch-frames", type=int, default=60)
    rom_trace_cmd.add_argument("--boss", default="")
    rom_trace_cmd.add_argument("--turn", default="")
    rom_trace_cmd.add_argument("--enemy", default="")
    rom_trace_cmd.add_argument("--player", default="")
    rom_trace_cmd.add_argument("--notes", default="")
    rom_trace_cmd.add_argument(
        "--patch-symbol",
        action="append",
        default=[],
        help=(
            "patch a symbol byte before replay, e.g. "
            "wPlayerScreens=0x01 or wPlayerUsedMoves+1=0xe5"
        ),
    )
    rom_trace_cmd.add_argument("--json", action="store_true")
    rom_trace_cmd.add_argument("--json-out", default="")
    rom_trace_cmd.add_argument("--limit", type=int, default=80)
    rom_trace_cmd.set_defaults(func=cmd_rom_contribution_trace)

    selector_materialize_cmd = subparsers.add_parser("rom-selector-materialize")
    selector_materialize_cmd.add_argument("--scenarios", type=path_arg, required=True)
    selector_materialize_cmd.add_argument("--limit", type=int, default=20)
    selector_materialize_cmd.add_argument(
        "--base-route",
        default=DEFAULT_SELECTOR_MATERIALIZE_ROUTE,
    )
    selector_materialize_cmd.add_argument(
        "--manifest",
        type=path_arg,
        default=DEFAULT_SELECTOR_MATERIALIZE_MANIFEST,
    )
    selector_materialize_cmd.add_argument(
        "--rom",
        type=path_arg,
        default=Path("pokegold_trace.gbc"),
    )
    selector_materialize_cmd.add_argument(
        "--symbols",
        type=path_arg,
        default=Path("pokegold_trace.sym"),
    )
    selector_materialize_cmd.add_argument("--button", default="a")
    selector_materialize_cmd.add_argument("--button-delay", type=int, default=8)
    selector_materialize_cmd.add_argument("--watch-frames", type=int, default=80)
    selector_materialize_cmd.add_argument("--json", action="store_true")
    selector_materialize_cmd.add_argument("--json-out", default="")
    selector_materialize_cmd.add_argument("--display-limit", type=int, default=20)
    selector_materialize_cmd.add_argument("--fail-on-mismatch", action="store_true")
    selector_materialize_cmd.set_defaults(func=cmd_rom_selector_materialize)

    score_materialize_cmd = subparsers.add_parser("rom-score-materialize")
    score_materialize_cmd.add_argument("--scenarios", type=path_arg, required=True)
    score_materialize_cmd.add_argument("--limit", type=int, default=4)
    score_materialize_cmd.add_argument(
        "--base-route",
        default=DEFAULT_SCORE_MATERIALIZE_ROUTE,
    )
    score_materialize_cmd.add_argument(
        "--manifest",
        type=path_arg,
        default=DEFAULT_SELECTOR_MATERIALIZE_MANIFEST,
    )
    score_materialize_cmd.add_argument(
        "--rom",
        type=path_arg,
        default=Path("pokegold_trace.gbc"),
    )
    score_materialize_cmd.add_argument(
        "--symbols",
        type=path_arg,
        default=Path("pokegold_trace.sym"),
    )
    score_materialize_cmd.add_argument("--button", default="a")
    score_materialize_cmd.add_argument("--button-delay", type=int, default=8)
    score_materialize_cmd.add_argument(
        "--watch-frames",
        type=int,
        default=DEFAULT_SCORE_MATERIALIZE_WATCH_FRAMES,
    )
    score_materialize_cmd.add_argument("--json", action="store_true")
    score_materialize_cmd.add_argument("--json-out", default="")
    score_materialize_cmd.add_argument("--display-limit", type=int, default=20)
    score_materialize_cmd.add_argument("--fast-score-only", action="store_true")
    score_materialize_cmd.add_argument("--compare-fast-score", action="store_true")
    score_materialize_cmd.add_argument("--workers", type=int, default=1)
    score_materialize_cmd.add_argument("--fail-on-mismatch", action="store_true")
    score_materialize_cmd.set_defaults(func=cmd_rom_score_materialize)

    switch_materialize_cmd = subparsers.add_parser("rom-switch-materialize")
    switch_materialize_cmd.add_argument("--scenarios", type=path_arg, required=True)
    switch_materialize_cmd.add_argument("--limit", type=int, default=20)
    switch_materialize_cmd.add_argument(
        "--base-route",
        default=DEFAULT_SWITCH_MATERIALIZE_ROUTE,
    )
    switch_materialize_cmd.add_argument(
        "--manifest",
        type=path_arg,
        default=DEFAULT_SELECTOR_MATERIALIZE_MANIFEST,
    )
    switch_materialize_cmd.add_argument(
        "--rom",
        type=path_arg,
        default=Path("pokegold_trace.gbc"),
    )
    switch_materialize_cmd.add_argument(
        "--symbols",
        type=path_arg,
        default=Path("pokegold_trace.sym"),
    )
    switch_materialize_cmd.add_argument(
        "--watch-frames",
        type=int,
        default=DEFAULT_SWITCH_MATERIALIZE_WATCH_FRAMES,
    )
    switch_materialize_cmd.add_argument("--json", action="store_true")
    switch_materialize_cmd.add_argument("--json-out", default="")
    switch_materialize_cmd.add_argument("--display-limit", type=int, default=20)
    switch_materialize_cmd.add_argument(
        "--switch-threshold",
        type=int,
        help=(
            "explicit final BossAI_SwitchOrTryItem threshold byte for exact "
            "switch-roll frequency reporting"
        ),
    )
    switch_materialize_cmd.add_argument("--fail-on-mismatch", action="store_true")
    switch_materialize_cmd.set_defaults(func=cmd_rom_switch_materialize)

    invariants_cmd = subparsers.add_parser("invariants")
    invariants_subcommands = invariants_cmd.add_subparsers(
        dest="invariants_command",
        required=True,
    )
    invariants_mine = invariants_subcommands.add_parser("mine")
    invariants_mine.add_argument("--scenarios", type=path_arg)
    invariants_mine.add_argument("--runs-dir", type=path_arg)
    invariants_mine.add_argument("--trace-dir", type=path_arg)
    invariants_mine.add_argument("--glob", default="*_live.txt")
    invariants_mine.add_argument("--json", action="store_true")
    invariants_mine.add_argument(
        "--json-out",
        default=str(DEFAULT_INVARIANTS_JSON_PATH),
    )
    invariants_mine.add_argument("--out", default=str(DEFAULT_INVARIANTS_MD_PATH))
    invariants_mine.set_defaults(func=cmd_invariants_mine)

    haki_cmd = subparsers.add_parser("haki-coverage")
    haki_cmd.add_argument("--self-test", action="store_true")
    haki_cmd.add_argument("--json", action="store_true")
    haki_cmd.set_defaults(func=cmd_haki_coverage)

    role_pkg_cmd = subparsers.add_parser("role-packages")
    role_pkg_cmd.add_argument("--species", action="append", required=True)
    role_pkg_cmd.add_argument("--json", action="store_true")
    role_pkg_cmd.set_defaults(func=cmd_role_packages)

    coach_plan_cmd = subparsers.add_parser("coach-plan-templates")
    coach_plan_cmd.add_argument("--json", action="store_true")
    coach_plan_cmd.set_defaults(func=cmd_coach_plan_templates)
    return parser
