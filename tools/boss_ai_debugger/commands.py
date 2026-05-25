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

from . import haki_coverage
from .coverage_report import (
    DEFAULT_COVERAGE_PATH,
    build_coverage_report,
    format_coverage_report,
    write_coverage_report,
)
from .coverage_search import (
    DEFAULT_COVERAGE_SEARCH_REPORT,
    DEFAULT_COVERAGE_SEARCH_SCENARIOS,
    format_coverage_search_report,
    run_coverage_guided_search_from_path,
    write_coverage_search_report,
    write_coverage_search_scenarios,
)
from .confidence_report import (
    build_confidence_report_from_paths,
    format_confidence_report,
    write_confidence_report_json,
)
from .coach_plan_templates import (
    format_coach_plan_template_report,
    run_coach_plan_template_report,
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
from .damage_ai_report import (
    format_damage_ai_report,
    run_damage_ai_report,
    run_self_test as run_damage_ai_report_self_test,
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
from .move_score_probe import (
    DEFAULT_SCORE_BASE_ROUTE,
    format_move_score_probe,
    parse_stage_overrides,
    ProbeOverrides,
    run_move_score_probe,
    run_self_test as run_move_score_probe_self_test,
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
from .replay_import import (
    DEFAULT_REPLAY_IMPORT_REPORT,
    ReplayImportOptions,
    format_replay_import_report,
    import_replay_sources,
    write_imported_scenarios,
    write_replay_import_report,
)
from .role_packages import (
    describe_species as describe_role_package_species,
    format_role_package_rows,
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
from .rom_switch_materialize import (
    DEFAULT_BASE_ROUTE as DEFAULT_SWITCH_MATERIALIZE_ROUTE,
    DEFAULT_WATCH_FRAMES as DEFAULT_SWITCH_MATERIALIZE_WATCH_FRAMES,
    format_rom_switch_materialization,
    run_rom_switch_materialization_from_path,
    write_rom_switch_materialization_json,
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


def cmd_replay_import(args: argparse.Namespace) -> int:
    options = ReplayImportOptions(
        side=args.side,
        mode=args.mode,
        turns=tuple(args.turn or ()),
        limit=args.limit,
        seed=args.seed,
    )
    result = import_replay_sources(
        logs=args.log or (),
        mastery_docs=args.mastery_doc or (),
        quick_tests=args.quick_tests,
        reviews=args.reviews,
        options=options,
    )
    write_imported_scenarios(result["scenarios"], args.out)
    if args.json_out != "":
        write_replay_import_report(result["report"], Path(args.json_out))
    if args.json:
        print(json.dumps(result["report"], indent=2, sort_keys=True))
    else:
        print(format_replay_import_report(result["report"]))
        print(f"wrote {args.out}")
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    return 0


def cmd_coverage_search(args: argparse.Namespace) -> int:
    result = run_coverage_guided_search_from_path(
        args.scenarios,
        rounds=args.rounds,
        per_seed=args.per_seed,
        seed=args.seed,
        generated_count=args.generated_count,
        keep=args.keep,
    )
    write_coverage_search_scenarios(result["scenarios"], args.out)
    if args.json_out != "":
        write_coverage_search_report(result["report"], Path(args.json_out))
    if args.json:
        print(json.dumps(result["report"], indent=2, sort_keys=True))
    else:
        print(format_coverage_search_report(result["report"]))
        print(f"wrote {args.out}")
        if args.json_out != "":
            print(f"wrote {args.json_out}")
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
            refresh_rom_score_materialization=args.refresh_rom_score_materialization,
            rebuild_roms=args.rebuild_roms,
            refresh_live_traces=args.refresh_live_traces,
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


def cmd_confidence_report(args: argparse.Namespace) -> int:
    data = build_confidence_report_from_paths(
        batch_report_path=args.batch_report,
        materialization_paths=args.materialization,
    )
    if args.json_out != "":
        write_confidence_report_json(data, Path(args.json_out))
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(format_confidence_report(data, limit=args.limit))
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
        horizon=args.horizon,
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


def cmd_move_score_probe(args: argparse.Namespace) -> int:
    if args.self_test:
        return run_move_score_probe_self_test()
    missing = [
        name
        for name in ("trainer", "enemy", "player_save")
        if getattr(args, name) in {None, ""}
    ]
    if missing:
        raise PreferenceDataError("missing required argument(s): " + ", ".join(missing))
    report = run_move_score_probe(
        trainer=args.trainer,
        enemy=args.enemy,
        player_save=args.player_save,
        player_slot=args.player_slot,
        sleep_clause=args.sleep_clause,
        trace=args.trace,
        rom=args.rom,
        symbols=args.symbols,
        manifest=args.manifest,
        score_base_route=args.score_base_route or None,
        overrides=ProbeOverrides(
            enemy_stat_stages=parse_stage_overrides(args.enemy_stage),
            player_stat_stages=parse_stage_overrides(args.player_stage),
            enemy_current_hp=args.enemy_current_hp,
            enemy_max_hp=args.enemy_max_hp,
            player_current_hp=args.player_current_hp,
            player_max_hp=args.player_max_hp,
            battle_turn=args.battle_turn,
            boss_turns_elapsed=args.boss_turns_elapsed,
        ),
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_move_score_probe(report))
    return 0


def cmd_damage_ai_report(args: argparse.Namespace) -> int:
    if args.self_test:
        return run_damage_ai_report_self_test()
    missing = [
        name
        for name in ("trainer", "enemy", "player_save")
        if getattr(args, name) in {None, ""}
    ]
    if missing:
        raise PreferenceDataError("missing required argument(s): " + ", ".join(missing))
    report = run_damage_ai_report(
        trainer=args.trainer,
        enemy=args.enemy,
        player_save=args.player_save,
        player_slot=args.player_slot,
        sleep_clause=args.sleep_clause,
        trace=args.trace,
        rom=args.rom,
        symbols=args.symbols,
        manifest=args.manifest,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_damage_ai_report(report))
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
        collect_contribution_traces=not args.fast_score_only,
        compare_fast_score=args.compare_fast_score,
        workers=args.workers,
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


def cmd_rom_switch_materialize(args: argparse.Namespace) -> int:
    report = run_rom_switch_materialization_from_path(
        args.scenarios,
        limit=args.limit,
        base_route=args.base_route,
        manifest_path=args.manifest,
        rom=args.rom,
        symbols_path=args.symbols,
        watch_frames=args.watch_frames,
        switch_threshold=args.switch_threshold,
    )
    if args.json_out != "":
        write_rom_switch_materialization_json(report, Path(args.json_out))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_rom_switch_materialization(report, limit=args.display_limit))
        if args.json_out != "":
            print(f"wrote {args.json_out}")
    if args.fail_on_mismatch and (
        report["policy_disagreement_count"] > 0 or report["error_count"] > 0
    ):
        return 1
    return 0


def cmd_haki_coverage(args: argparse.Namespace) -> int:
    if args.self_test:
        return haki_coverage.run_self_test()
    report = haki_coverage.run_haki_coverage()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(haki_coverage.format_haki_coverage(report))
    return 0 if report.get("ok") else 1


def cmd_role_packages(args: argparse.Namespace) -> int:
    try:
        rows = describe_role_package_species(args.species)
    except ValueError as exc:
        print(str(exc))
        return 2
    ok = all(bool(row["committed_matches_source"]) for row in rows)
    if args.json:
        print(json.dumps({"ok": ok, "species": rows}, indent=2, sort_keys=True))
    else:
        print(format_role_package_rows(rows))
    return 0 if ok else 1


def cmd_coach_plan_templates(args: argparse.Namespace) -> int:
    report = run_coach_plan_template_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_coach_plan_template_report(report))
    return 0 if report.get("ok") else 1
