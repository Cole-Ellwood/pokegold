from __future__ import annotations

import argparse
from pathlib import Path

from .catalog import build_capability_report, build_inventory, triage_request
from .cli_helpers import emit_report, load_jsonl
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
from .next_steps import build_next_step, symptom_only_investigation_note
from .pokemon_semantics import (
    build_grass_regrowth_report,
    build_learnset_inspection_report,
    build_party_inspection_report,
)
from .proof_runner import build_proof_campaign, build_proof_card
from .provenance import build_provenance_report
from .ranking import rank_findings
from .replay import build_replay_plan
from .repro_recipes import build_repro_recipe_report
from .reporting import build_static_report, write_static_report
from .runtime_state import build_runtime_state_report
from .runtime_watch import build_watch_report
from .save_state_inspect import build_save_state_inspection_report
from .script_resume_gate import build_script_resume_gate_report
from .setup_plan import build_setup_plan
from .slicing import build_slice_report
from .state_space import build_state_space_report
from .taint import build_taint_report
from .testgen import suggest_tests
from .trace_index import build_trace_index_report
from .visualization import build_visualization_report, write_visualization
from .workflow import build_gate_plan
from .wram_bank_hazards import build_wram_bank_hazard_report
from .wram_lifetime import build_wram_lifetime_report
from .wram_ownership import build_wram_ownership_report


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


def cmd_next(args: argparse.Namespace) -> int:
    report = build_next_step(
        changed_files=tuple(args.changed_file),
        symptom=args.symptom,
    )
    emit_report(report, args)
    return 0


def cmd_prove(args: argparse.Namespace) -> int:
    if args.suite or args.all_routes:
        cases = load_jsonl(args.suite) if args.suite else []
        report = build_proof_campaign(
            cases=tuple(cases),
            execute=args.execute,
            timeout_seconds=args.timeout_seconds,
            max_commands=args.max_commands,
            include_all_routes=args.all_routes,
        )
        emit_report(report, args)
        return 0 if report["valid"] else 1

    report = build_proof_card(
        changed_files=tuple(args.changed_file),
        symptom=args.symptom,
        execute=args.execute,
        timeout_seconds=args.timeout_seconds,
        prefer=args.prefer,
    )
    emit_report(report, args)
    return 0 if report["passed"] else 1


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
        patches=tuple(args.patch),
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
    if args.symptom and not investigation_args_have_anchor(args) and "symptom_only_next_step" not in report:
        next_step = build_next_step(symptom=args.symptom)
        report["symptom_only_next_step"] = next_step
        report["symptom_only_next_step_note"] = symptom_only_investigation_note(
            report,
            next_step=next_step,
        )
    emit_report(report, args)
    return 0 if report["valid"] and report["passed"] else 1


def investigation_args_have_anchor(args: argparse.Namespace) -> bool:
    return any(
        (
            args.rom,
            args.save_state,
            args.trace,
            args.scenario,
            args.report,
            args.patch,
            args.changed_file,
            args.symbol,
            args.watch_symbol,
            args.rule,
            args.address,
            args.expect,
            args.expect_file,
            args.family,
        )
    )


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
        execute_state_patches=args.execute_state_patches,
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
        battery_save=args.battery_save,
        boot_continue=args.boot_continue,
        input_events=tuple(args.input),
        out_initial_state=args.out_initial_state,
        frames=args.frames,
        context_frames=args.context_frames,
        execute=args.execute,
        reset_sentinel=args.reset_sentinel,
        sentinel_symbols=tuple(args.sentinel_symbol),
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_state_inspect(args: argparse.Namespace) -> int:
    report = build_runtime_state_report(
        rom_path=args.rom,
        symbols_path=args.symbols,
        save_state=args.save_state,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_save_state_inspect(args: argparse.Namespace) -> int:
    report = build_save_state_inspection_report(
        save_state=args.save_state,
        rom_path=args.rom,
        symbols_path=args.symbols,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_learnset_inspect(args: argparse.Namespace) -> int:
    report = build_learnset_inspection_report(
        species=args.species,
        level=args.level,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_party_inspect(args: argparse.Namespace) -> int:
    report = build_party_inspection_report(
        save=args.save,
        slots=tuple(args.slot),
        rom=args.rom,
        symbols=args.symbols,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_grass_regrowth(args: argparse.Namespace) -> int:
    report = build_grass_regrowth_report(max_total_hp=args.max_total_hp)
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_wram_bank_hazards(args: argparse.Namespace) -> int:
    report = build_wram_bank_hazard_report(
        source_files=tuple(args.source_file),
    )
    emit_report(report, args)
    return 0 if report["valid"] and report["passed"] else 1


def cmd_script_resume_gate(args: argparse.Namespace) -> int:
    report = build_script_resume_gate_report(
        reports=tuple(args.report),
    )
    emit_report(report, args)
    return 0 if report["valid"] and report["passed"] else 1


def cmd_wram_ownership(args: argparse.Namespace) -> int:
    report = build_wram_ownership_report(
        symbols=tuple(args.symbol),
        source_file=args.source_file,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


def cmd_wram_lifetime(args: argparse.Namespace) -> int:
    report = build_wram_lifetime_report(
        symbols=tuple(args.symbol),
        through=args.through,
        source_file=args.source_file,
        symbols_path=args.symbols,
    )
    emit_report(report, args)
    return 0 if report["valid"] and report["passed"] else 1


def cmd_repro_recipe(args: argparse.Namespace) -> int:
    report = build_repro_recipe_report(
        ids=tuple(args.id),
        symptom=args.symptom,
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
        reports=tuple(args.report),
        changed_files=tuple(args.changed_file),
        symbols=tuple(args.symbol),
        symptom=args.symptom,
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1


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
