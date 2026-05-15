from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.boss_ai_preference.data import (
    ALLOWED_LABELS,
    DEFAULT_FIXTURES_PATH,
    DEFAULT_JSON_REPORT_PATH,
    DEFAULT_LABELS_PATH,
    DEFAULT_PREFERENCES_PATH,
    DEFAULT_REPORT_PATH,
    PreferenceDataError,
    append_label,
    fixture_map,
    load_fixtures,
    load_labels,
    load_preferences,
    write_report,
)
from tools.boss_ai_preference.damage_estimates import attach_damage_estimates

from .regression import (
    evaluate_corpus,
    exit_code_for_result,
    format_summary,
    write_json_report,
)
from .rom_scenarios import (
    benchmark_batch,
    evaluate_batch,
    format_batch_report,
    format_simulation,
    load_scenario,
    load_scenario_batch,
    select_move,
)
from .scorer import format_inspection, inspect_fixture
from .trace_replay import (
    collect_trace_paths,
    format_trace_replay_report,
    replay_trace_paths,
    write_trace_replay_json,
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


def _load_fixture(fixtures_path: Path, fixture_id: str) -> dict:
    fixtures = load_fixtures(fixtures_path)
    fixtures_by_id = fixture_map(fixtures)
    try:
        return fixtures_by_id[fixture_id]
    except KeyError as exc:
        known = ", ".join(sorted(fixtures_by_id))
        raise PreferenceDataError(f"unknown fixture {fixture_id!r}; known: {known}") from exc


def cmd_list(args: argparse.Namespace) -> int:
    fixtures = load_fixtures(args.fixtures)
    for fixture in fixtures:
        print(f"{fixture['id']}\t{fixture['leader']}\t{fixture.get('training_focus', '')}")
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    fixture = _load_fixture(args.fixtures, args.fixture_id)
    fixture = attach_damage_estimates([fixture])[0]
    inspection = inspect_fixture(fixture)
    if args.json:
        print(json.dumps(inspection, indent=2, sort_keys=True))
    else:
        print(format_inspection(inspection))
    return 0


def cmd_judge(args: argparse.Namespace) -> int:
    record = append_label(
        fixture_id=args.fixture_id,
        action_id=args.action_id,
        label=args.label,
        rank=args.rank,
        note=args.note,
        fixtures_path=args.fixtures,
        labels_path=args.labels,
    )
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    report = write_report(
        fixtures_path=args.fixtures,
        labels_path=args.labels,
        out_path=args.out,
        json_out_path=None if args.json_out == "" else args.json_out,
    )
    print(
        "Debugger corpus report: "
        f"{report['label_count']} labels across "
        f"{report['labeled_fixture_count']} / {report['fixture_count']} fixtures"
    )
    return 0


def cmd_regress(args: argparse.Namespace) -> int:
    if args.threshold < 0 or args.threshold > 1:
        raise PreferenceDataError("threshold must be between 0 and 1")

    fixtures = load_fixtures(args.fixtures)
    labels = load_preferences(args.labels, fixtures=fixtures)
    rank_labels = (
        load_labels(DEFAULT_LABELS_PATH, fixtures=fixtures)
        if args.include_rank_labels
        else None
    )
    result = evaluate_corpus(
        fixtures,
        labels,
        args.threshold,
        rank_labels=rank_labels,
    )
    print(format_summary(result, quiet=args.quiet))
    if args.json_out != "":
        write_json_report(result, Path(args.json_out))
    return exit_code_for_result(result)


def cmd_simulate(args: argparse.Namespace) -> int:
    scenario = load_scenario(args.scenario, args.builtin)
    result = select_move(scenario)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_simulation(result, show_events=not args.no_events))
    return 0


def cmd_batch_simulate(args: argparse.Namespace) -> int:
    scenarios = load_scenario_batch(args.scenarios, args.expectations)
    report = evaluate_batch(scenarios)
    benchmark = None
    if args.benchmark_seconds:
        benchmark = benchmark_batch(scenarios, args.benchmark_seconds)
        report["benchmark"] = benchmark

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif not args.quiet:
        print(format_batch_report(report, limit=args.limit))
        if benchmark is not None:
            print("")
            print(
                "Benchmark: "
                f"{benchmark['evaluations_per_minute']:.0f} evaluations/min; "
                f"{benchmark['reviewable_evaluations_per_minute']:.0f} "
                "reviewable evaluations/min"
            )
    else:
        print(
            "ROM boss AI batch check: "
            f"{report['scenario_count']} scenarios, "
            f"{report['reviewable_count']} reviewable, "
            f"{report['scenarios_per_minute']:.0f}/min"
        )

    if args.json_out != "":
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_out).write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    if args.fail_on_reviewable_mismatch and report["reviewable_count"]:
        return 1
    return 0


def cmd_trace_replay(args: argparse.Namespace) -> int:
    paths = collect_trace_paths(
        traces=args.trace,
        trace_dir=args.trace_dir,
        pattern=args.glob,
    )
    report = replay_trace_paths(paths)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif not args.quiet:
        print(format_trace_replay_report(report, limit=args.limit))
    else:
        print(
            "Boss AI trace selector replay: "
            f"{report['match_count']} / {report['checked_count']} matched "
            f"({report['agreement_rate']:.4%})"
        )

    if args.json_out != "":
        write_trace_replay_json(report, Path(args.json_out))

    if args.fail_on_mismatch and report["failure_count"]:
        return 1
    return 0


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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except PreferenceDataError as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
