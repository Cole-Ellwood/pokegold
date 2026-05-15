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

from .coverage_report import (
    DEFAULT_COVERAGE_PATH,
    build_coverage_report,
    format_coverage_report,
    write_coverage_report,
)
from .counterfactuals import (
    explain_counterfactuals_for_path,
    format_counterfactual_report,
    write_counterfactual_json,
)
from .contribution_compare import (
    format_python_contribution_report,
    python_contribution_report_from_scenarios,
    write_python_contribution_report,
)
from .differential import (
    differential_from_paths,
    format_differential_report,
    write_differential_json,
)
from .decision_trace import (
    decision_trace_from_path,
    format_decision_trace,
    write_decision_trace_json,
)
from .generators import (
    FAMILIES as GENERATOR_FAMILIES,
    format_generate_report,
    generate_scenarios,
    write_jsonl as write_scenarios_jsonl,
)
from .invariants import (
    DEFAULT_INVARIANTS_JSON_PATH,
    DEFAULT_INVARIANTS_MD_PATH,
    format_invariants_report,
    mine_invariants_from_paths,
    write_invariants_json,
    write_invariants_markdown,
)
from .metamorphic import (
    format_metamorphic_report,
    run_metamorphic_suite,
    write_metamorphic_json,
)
from .localize import (
    format_localization_report,
    localize_from_report,
    localize_from_scenarios,
    write_localization_json,
)
from .mastery_index import (
    DEFAULT_MASTERY_INDEX_PATH,
    build_mastery_index,
    format_mastery_index,
    write_mastery_index,
)
from .minimize import (
    format_minimized_report,
    minimize_scenario_path,
    write_minimized_json,
)
from .mutation import (
    format_mutation_report,
    run_scorer_mutations,
    write_mutation_json,
)
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
from .rom_contribution_trace import (
    format_rom_contribution_trace,
    parse_memory_patch,
    run_rom_contribution_trace,
    run_rom_contribution_trace_for_route,
    write_rom_contribution_trace_json,
)
from .rom_selector_materialize import (
    DEFAULT_BASE_ROUTE as DEFAULT_SELECTOR_MATERIALIZE_ROUTE,
    DEFAULT_MANIFEST_PATH as DEFAULT_SELECTOR_MATERIALIZE_MANIFEST,
    format_rom_selector_materialization,
    run_rom_selector_materialization_from_path,
    write_rom_selector_materialization_json,
)
from .rom_score_materialize import (
    DEFAULT_BASE_ROUTE as DEFAULT_SCORE_MATERIALIZE_ROUTE,
    DEFAULT_WATCH_FRAMES as DEFAULT_SCORE_MATERIALIZE_WATCH_FRAMES,
    format_rom_score_materialization,
    run_rom_score_materialization_from_path,
    write_rom_score_materialization_json,
)
from .run_store import DEFAULT_RUNS_DIR, run_changed_ai_suite, run_generated_smoke_suite
from .rule_map import (
    DEFAULT_RULE_MAP_PATH,
    build_rule_map,
    compare_rule_maps,
    format_rule_map_summary,
    write_rule_map,
)
from .review_queue import (
    build_review_queue_from_report,
    build_review_queue_from_scenarios,
    format_review_queue,
    write_review_queue,
)
from .route_eval import (
    evaluate_route_path,
    format_route_eval_report,
    write_route_eval_json,
)
from .scorer import format_inspection, inspect_fixture
from .state_schema import (
    DEFAULT_TRACE_DIR,
    DEFAULT_TRACE_GLOB,
    combine_reports,
    format_validation_report,
    validate_fixtures_file,
    validate_path,
    validate_trace_dir,
)
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


def cmd_state_schema_validate(args: argparse.Namespace) -> int:
    reports = []
    if args.fixtures:
        reports.append(validate_fixtures_file(args.fixtures_path))
    if args.trace_dir is not None:
        reports.append(validate_trace_dir(args.trace_dir, pattern=args.glob))
    for path in args.path or []:
        reports.append(validate_path(path))
    if not reports:
        reports.append(validate_fixtures_file(args.fixtures_path))
        reports.append(validate_trace_dir(DEFAULT_TRACE_DIR, pattern=DEFAULT_TRACE_GLOB))

    report = reports[0] if len(reports) == 1 else combine_reports("state_schema", reports)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_validation_report(report))
    return 0 if report["valid"] else 1


def cmd_rule_map_build(args: argparse.Namespace) -> int:
    data = build_rule_map()
    if args.json_out != "":
        write_rule_map(data, Path(args.json_out))
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(format_rule_map_summary(data))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    return 0


def cmd_rule_map_check(args: argparse.Namespace) -> int:
    data = build_rule_map()
    compare_errors = compare_rule_maps(data, args.rule_map)
    print(format_rule_map_summary(data, compare_errors=compare_errors))
    return 0 if not compare_errors else 1


def cmd_generate(args: argparse.Namespace) -> int:
    scenarios = generate_scenarios(family=args.family, count=args.count, seed=args.seed)
    if args.out is not None:
        write_scenarios_jsonl(scenarios, args.out)
        print(format_generate_report(family=args.family, count=len(scenarios), seed=args.seed, out=args.out))
    else:
        for scenario in scenarios:
            print(json.dumps(scenario, sort_keys=True))
    return 0


def cmd_review_queue(args: argparse.Namespace) -> int:
    if args.report is not None:
        queue = build_review_queue_from_report(
            args.report,
            limit=args.limit,
            max_per_lesson=args.max_per_lesson,
        )
    else:
        queue = build_review_queue_from_scenarios(
            args.scenarios,
            expectations_path=args.expectations,
            limit=args.limit,
            max_per_lesson=args.max_per_lesson,
        )
    if args.json_out != "":
        write_review_queue(queue, Path(args.json_out))
    if args.json:
        print(json.dumps(queue, indent=2, sort_keys=True))
    else:
        print(format_review_queue(queue))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    return 0


def cmd_run_suite(args: argparse.Namespace) -> int:
    if args.profile == "generated-smoke":
        metadata = run_generated_smoke_suite(
            count=args.count,
            seed=args.seed,
            run_id=args.run_id,
            runs_dir=args.runs_dir,
        )
    elif args.profile == "changed-ai":
        metadata = run_changed_ai_suite(
            count=args.count,
            seed=args.seed,
            run_id=args.run_id,
            runs_dir=args.runs_dir,
            trace_dir=args.trace_dir,
            rom_contribution_trace_paths=args.rom_contribution_trace,
            refresh_rom_contribution_trace=args.refresh_rom_contribution_trace,
            rom_contribution_boss_route=args.rom_contribution_boss_route,
        )
    else:
        raise PreferenceDataError(f"unknown run-suite profile {args.profile!r}")
    if args.json:
        print(json.dumps(metadata, indent=2, sort_keys=True))
    else:
        print(
            "Boss AI debugger run-suite complete: "
            f"profile={metadata['profile']} run_id={metadata['run_id']} "
            f"scenarios={metadata['batch_summary']['scenario_count']} "
            f"reviewable={metadata['batch_summary']['reviewable_count']} "
            f"summary={metadata['artifacts']['summary']}"
        )
    return 0


def cmd_metamorphic(args: argparse.Namespace) -> int:
    report = run_metamorphic_suite(generated=args.generated, seed=args.seed)
    if args.json_out != "":
        write_metamorphic_json(report, Path(args.json_out))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_metamorphic_report(report))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    if args.fail_on_mismatch and not report["passed"]:
        return 1
    return 0


def cmd_mutate(args: argparse.Namespace) -> int:
    if args.target != "scorer":
        raise PreferenceDataError("only --target scorer is implemented")
    fixtures = load_fixtures(args.fixtures)
    labels = load_preferences(fixtures=fixtures, path=args.labels)
    report = run_scorer_mutations(
        fixtures,
        labels,
        threshold=args.threshold,
        limit=args.limit,
    )
    if args.json_out != "":
        write_mutation_json(report, Path(args.json_out))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_mutation_report(report))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    if args.fail_on_survivor and report["survived_count"] > 0:
        return 1
    return 0


def cmd_mastery_index_build(args: argparse.Namespace) -> int:
    data = build_mastery_index()
    if args.json_out != "":
        write_mastery_index(data, Path(args.json_out))
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(format_mastery_index(data))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    return 0


def cmd_coverage_report(args: argparse.Namespace) -> int:
    data = build_coverage_report(
        generated_count=args.generated_count,
        seed=args.seed,
        rom_contribution_trace_paths=args.rom_contribution_trace,
        changed_files=args.changed_file,
    )
    if args.json_out != "":
        write_coverage_report(data, Path(args.json_out))
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(format_coverage_report(data))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    return 0


def cmd_counterfactual(args: argparse.Namespace) -> int:
    report = explain_counterfactuals_for_path(args.scenario, scenario_id=args.scenario_id or None)
    if args.json_out != "":
        write_counterfactual_json(report, Path(args.json_out))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_counterfactual_report(report))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    return 0


def cmd_minimize(args: argparse.Namespace) -> int:
    report = minimize_scenario_path(args.scenario, scenario_id=args.scenario_id or None)
    if args.json_out != "":
        write_minimized_json(report, Path(args.json_out))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_minimized_report(report))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    return 0


def cmd_localize(args: argparse.Namespace) -> int:
    if args.report is not None:
        report = localize_from_report(args.report)
    else:
        report = localize_from_scenarios(args.scenarios)
    if args.json_out != "":
        write_localization_json(report, Path(args.json_out))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_localization_report(report))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    return 0


def cmd_invariants_mine(args: argparse.Namespace) -> int:
    report = mine_invariants_from_paths(
        scenarios_path=args.scenarios,
        runs_dir=args.runs_dir,
        trace_dir=args.trace_dir,
        trace_glob=args.glob,
    )
    if args.json_out != "":
        write_invariants_json(report, Path(args.json_out))
    if args.out != "":
        write_invariants_markdown(report, Path(args.out))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_invariants_report(report))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
        if args.out != "":
            print(f"wrote {args.out}")
    return 0


def cmd_route_eval(args: argparse.Namespace) -> int:
    report = evaluate_route_path(
        args.scenario,
        scenario_id=args.scenario_id or None,
    )
    if args.json_out != "":
        write_route_eval_json(report, Path(args.json_out))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_route_eval_report(report))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    report = differential_from_paths(
        scenarios_path=args.scenarios,
        trace_dir=args.trace_dir,
        trace_glob=args.glob,
        rom_contribution_trace_paths=args.rom_contribution_trace,
        python_contribution_trace_paths=args.python_contribution_trace,
    )
    if args.json_out != "":
        write_differential_json(report, Path(args.json_out))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_differential_report(report, limit=args.limit))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    if args.fail_on_mismatch and report["mismatch_count"] > 0:
        return 1
    return 0


def cmd_python_contribution_trace(args: argparse.Namespace) -> int:
    scenarios = load_scenario_batch(args.scenarios)
    report = python_contribution_report_from_scenarios(scenarios)
    if args.json_out != "":
        write_python_contribution_report(report, Path(args.json_out))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_python_contribution_report(report))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    return 0


def cmd_decision_trace(args: argparse.Namespace) -> int:
    trace = decision_trace_from_path(
        args.scenario,
        scenario_id=args.scenario_id or None,
    )
    if args.json_out != "":
        write_decision_trace_json(trace, Path(args.json_out))
    if args.json:
        print(json.dumps(trace, indent=2, sort_keys=True))
    else:
        print(format_decision_trace(trace, limit=args.limit))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    return 0


def cmd_rom_contribution_trace(args: argparse.Namespace) -> int:
    metadata = {
        "boss": args.boss,
        "turn": args.turn,
        "enemy": args.enemy,
        "player": args.player,
        "notes": args.notes,
    }
    memory_patches = [parse_memory_patch(item) for item in args.patch_symbol]
    if args.boss_route:
        report = run_rom_contribution_trace_for_route(
            boss_id=args.boss_route,
            rom=args.rom,
            symbols_path=args.symbols,
            battery_save=args.battery_save,
            out_dir=args.out_dir,
            input_wait_frames=args.input_wait_frames,
            max_a_presses=args.max_a_presses,
            metadata=metadata,
            memory_patches=memory_patches,
        )
    else:
        report = run_rom_contribution_trace(
            save_state=args.save_state,
            rom=args.rom,
            symbols_path=args.symbols,
            button=args.button,
            button_delay=args.button_delay,
            watch_frames=args.watch_frames,
            metadata=metadata,
            memory_patches=memory_patches,
        )
    if args.json_out != "":
        write_rom_contribution_trace_json(report, Path(args.json_out))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_rom_contribution_trace(report, limit=args.limit))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    return 0


def cmd_rom_selector_materialize(args: argparse.Namespace) -> int:
    report = run_rom_selector_materialization_from_path(
        args.scenarios,
        limit=args.limit,
        base_route=args.base_route,
        manifest_path=args.manifest,
        rom=args.rom,
        symbols_path=args.symbols,
        button=args.button,
        button_delay=args.button_delay,
        watch_frames=args.watch_frames,
    )
    if args.json_out != "":
        write_rom_selector_materialization_json(report, Path(args.json_out))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_rom_selector_materialization(report, limit=args.display_limit))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    if args.fail_on_mismatch and report["mismatch_count"] > 0:
        return 1
    return 0


def cmd_rom_score_materialize(args: argparse.Namespace) -> int:
    report = run_rom_score_materialization_from_path(
        args.scenarios,
        limit=args.limit,
        base_route=args.base_route,
        manifest_path=args.manifest,
        rom=args.rom,
        symbols_path=args.symbols,
        button=args.button,
        button_delay=args.button_delay,
        watch_frames=args.watch_frames,
    )
    if args.json_out != "":
        write_rom_score_materialization_json(report, Path(args.json_out))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_rom_score_materialization(report, limit=args.display_limit))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    if args.fail_on_mismatch and report["contribution_mismatch_count"] > 0:
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
    score_materialize_cmd.add_argument("--fail-on-mismatch", action="store_true")
    score_materialize_cmd.set_defaults(func=cmd_rom_score_materialize)

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
