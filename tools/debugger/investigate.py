from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .content_mirror import build_content_mirror_report
from .content_scenarios import build_content_scenario_report
from .coverage import build_coverage_report
from .audio_snapshot import build_audio_snapshot_report
from .causal_graph import build_causal_graph_report
from .expect import build_expectation_report, expectation_watch_size, load_expectation_files, parse_cli_expectation
from .explain import build_explanation_report
from .dynamic_taint import build_dynamic_taint_report
from .effect_trace import build_effect_trace_report
from .fuzz import build_fuzz_plan
from .generate import build_generation_plan
from .hook_order import build_hook_order_probe_report
from .impact import build_impact_report
from .ingest import ingest_artifacts
from .instruction_trace import build_instruction_trace_report
from .localize import build_localization_plan
from .minimize import build_minimization_plan
from .mirrors import build_compare_plan
from .ranking import rank_findings
from .replay import build_replay_plan
from .reporting import build_static_report, load_reports, write_static_report
from .reverse_query import build_reverse_query_report
from .state_space import build_state_space_report
from .taint import build_taint_report
from .trace_index import build_trace_index_report, unique_list
from .visualization import build_visualization_report, write_visualization
from .visual_snapshot import build_visual_snapshot_report
from .workflow import command_is_runnable


DEFAULT_OUT_DIR = ".local\\tmp\\debugger_investigation"


def build_investigation_run(
    *,
    rom_path: str = "",
    symbols_path: str = "pokegold.sym",
    save_state: str = "",
    input_logs: tuple[str, ...] = (),
    traces: tuple[str, ...] = (),
    scenarios: tuple[str, ...] = (),
    reports: tuple[str, ...] = (),
    patches: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    watch_symbols: tuple[str, ...] = (),
    rules: tuple[str, ...] = (),
    addresses: tuple[str, ...] = (),
    expectations: tuple[str, ...] = (),
    expectation_files: tuple[str, ...] = (),
    families: tuple[str, ...] = (),
    symptom: str = "",
    out_dir: str = DEFAULT_OUT_DIR,
    execute_watch: bool = False,
    execute_snapshots: bool = False,
    execute_attribution: bool = False,
    watch_size: int = 1,
    frames: int = 300,
    context_frames: int = 12,
    max_targets: int = 24,
    max_events: int = 1000,
    max_cases: int = 64,
    seed: int = 1,
    root: Path = ROOT,
) -> dict[str, Any]:
    output_dir = resolve_output_dir(out_dir, root=root)
    steps: list[dict[str, Any]] = []
    produced_reports: list[dict[str, Any]] = []
    seed_input_reports, _seed_report_load_errors = load_reports(reports=reports, root=root)
    seed_playtest_inputs = derive_playtest_packet_inputs(seed_input_reports, root=root)
    effective_input_reports = tuple(unique_list([*reports, *seed_playtest_inputs["reports"]]))
    report_paths = list(effective_input_reports)
    loaded_input_reports, _report_load_errors = load_reports(reports=effective_input_reports, root=root)
    playtest_inputs = derive_playtest_packet_inputs(loaded_input_reports, root=root)
    playtest_evidence_routes = collect_playtest_evidence_routes(loaded_input_reports)
    playtest_packet_diagnostics = collect_playtest_packet_diagnostics(loaded_input_reports, root=root)
    trusted_playtest_traces = trusted_playtest_trace_paths(
        playtest_inputs["traces"],
        diagnostics=playtest_packet_diagnostics,
    )
    derived_inputs = derive_investigation_inputs(loaded_input_reports)
    input_expectation_records = load_investigation_expectations(
        expectations=expectations,
        expectation_files=expectation_files,
        root=root,
    )
    derived_expectation_inputs = derive_inputs_from_expectations(input_expectation_records)
    effective_rom_path = rom_path or first_item(playtest_inputs["roms"])
    effective_symbols_path = investigation_symbols_path(
        requested=symbols_path,
        playtest_symbols=playtest_inputs["symbols_paths"],
    )
    effective_save_state = save_state or first_item(playtest_inputs["save_states"])
    effective_input_logs = tuple(unique_list([
        *input_logs,
        *playtest_inputs["input_logs"],
        *derived_inputs["input_logs"],
    ]))
    effective_traces = tuple(unique_list([*traces, *trusted_playtest_traces]))
    effective_scenarios = tuple(unique_list([*scenarios, *playtest_inputs["scenarios"]]))
    effective_symptom = symptom or first_item(playtest_inputs["symptoms"])
    effective_changed_files = tuple(unique_list([
        *changed_files,
        *playtest_inputs["changed_files"],
        *derived_inputs["changed_files"],
        *derived_expectation_inputs["changed_files"],
    ]))
    effective_symbols = tuple(unique_list([
        *symbols,
        *playtest_inputs["symbols"],
        *derived_inputs["symbols"],
        *derived_expectation_inputs["symbols"],
    ]))
    effective_watch_symbols = tuple(unique_list([
        *watch_symbols,
        *playtest_inputs["watch_symbols"],
        *derived_inputs["watch_symbols"],
        *derived_expectation_inputs["watch_symbols"],
    ]))
    effective_addresses = tuple(unique_list([
        *addresses,
        *playtest_inputs["addresses"],
        *derived_inputs["addresses"],
        *derived_expectation_inputs["addresses"],
    ]))
    effective_watch_size = investigation_watch_size(
        requested=watch_size,
        loaded_reports=loaded_input_reports,
        expectation_records=input_expectation_records,
    )
    if effective_input_reports or _report_load_errors:
        add_input_report_step(
            steps,
            loaded_reports=loaded_input_reports,
            report_errors=_report_load_errors,
            reports=effective_input_reports,
        )
    if playtest_packet_diagnostics["packet_count"]:
        add_playtest_packet_diagnostics_step(
            steps,
            diagnostics=playtest_packet_diagnostics,
        )

    ingest = ingest_artifacts(
        roms=(effective_rom_path,) if effective_rom_path else (),
        symbols=(effective_symbols_path,) if effective_symbols_path else (),
        traces=effective_traces,
        save_states=(effective_save_state,) if effective_save_state else (),
        input_logs=effective_input_logs,
        scenarios=effective_scenarios,
        changed_files=effective_changed_files,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="01_ingest",
        phase="ingest",
        title="Ingest artifacts",
        data=ingest,
        output_dir=output_dir,
        root=root,
    )

    if patches:
        state_space_out_state = (
            display_output_path(output_dir / "state_space_patched.state", root=root)
            if output_dir and effective_save_state else ""
        )
        state_space_report_path = (
            display_output_path(output_dir / "02_state_space.json", root=root)
            if output_dir else ""
        )
        state_space = build_state_space_report(
            patches=patches,
            watch_symbols=effective_watch_symbols,
            scenario_id="investigation_state_space_1",
            source_files=effective_changed_files,
            symptom=effective_symptom,
            rom_path=effective_rom_path or "pokegold.gbc",
            symbols_path=effective_symbols_path,
            base_save_state=effective_save_state,
            out_state=state_space_out_state,
            execute=False,
            report_path=state_space_report_path,
            root=root,
        )
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="02_state_space",
            phase="observe",
            title="Build generic state-space patch report",
            data=state_space,
            output_dir=output_dir,
            root=root,
        )
        effective_watch_symbols = tuple(
            unique_list([*effective_watch_symbols, *string_items(state_space.get("watch_symbols"))])
        )

    trace_index = build_trace_index_report(
        traces=effective_traces,
        reports=tuple(report_paths),
        symbols=effective_symbols,
        watch_symbols=effective_watch_symbols,
        addresses=effective_addresses,
        rules=rules,
        source_files=effective_changed_files,
        symptom=effective_symptom,
        symbols_path=effective_symbols_path,
        max_events=max_events,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="02_trace_index",
        phase="observe",
        title="Build trace evidence index",
        data=trace_index,
        output_dir=output_dir,
        root=root,
    )

    content_files = content_mirror_files(effective_changed_files, root=root)
    if content_files:
        content_scenarios = build_content_scenario_report(
            changed_files=content_files,
            out_scenarios=display_output_path(output_dir / "content_scenarios.jsonl", root=root) if output_dir else "",
            max_cases=max_cases,
            seed=seed,
            root=root,
        )
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="02_content_scenarios",
            phase="observe",
            title="Generate content semantic scenarios",
            data=content_scenarios,
            output_dir=output_dir,
            root=root,
        )

    replay = build_replay_plan(
        rom_path=effective_rom_path,
        symbols_path=effective_symbols_path,
        save_state=effective_save_state,
        input_logs=effective_input_logs,
        traces=effective_traces,
        scenarios=effective_scenarios,
        reports=tuple(report_paths),
        watch_symbols=effective_watch_symbols,
        watch_addresses=effective_addresses,
        watch_size=effective_watch_size,
        symbols=effective_symbols,
        changed_files=effective_changed_files,
        symptom=effective_symptom,
        frames=frames,
        context_frames=context_frames,
        execute_watch=execute_watch,
        max_targets=max_targets,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="03_replay",
        phase="reproduce",
        title="Build replay plan",
        data=replay,
        output_dir=output_dir,
        root=root,
    )

    if execute_snapshots:
        if effective_save_state:
            visual_snapshot = build_visual_snapshot_report(
                rom_path=effective_rom_path or "pokegold.gbc",
                symbols_path=effective_symbols_path,
                save_state=effective_save_state,
                execute=True,
                root=root,
            )
            add_report(
                steps,
                produced_reports,
                report_paths,
                step_id="03_visual_snapshot",
                phase="observe",
                title="Capture visual/UI runtime snapshot",
                data=visual_snapshot,
                output_dir=output_dir,
                root=root,
            )
            audio_snapshot = build_audio_snapshot_report(
                rom_path=effective_rom_path or "pokegold.gbc",
                symbols_path=effective_symbols_path,
                save_state=effective_save_state,
                execute=True,
                root=root,
            )
            add_report(
                steps,
                produced_reports,
                report_paths,
                step_id="03_audio_snapshot",
                phase="observe",
                title="Capture audio runtime snapshot",
                data=audio_snapshot,
                output_dir=output_dir,
                root=root,
            )
        else:
            add_skipped_step(
                steps,
                step_id="03_runtime_snapshots",
                phase="observe",
                title="Capture visual/audio runtime snapshots",
                reason="--execute-snapshots needs a packet or input save state",
            )

    runtime_attribution = execute_runtime_attribution_chain(
        steps=steps,
        produced_reports=produced_reports,
        report_paths=report_paths,
        output_dir=output_dir,
        root=root,
        execute_attribution=execute_attribution,
        effective_rom_path=effective_rom_path,
        effective_symbols_path=effective_symbols_path,
        effective_save_state=effective_save_state,
        effective_traces=effective_traces,
        effective_input_logs=effective_input_logs,
        effective_scenarios=effective_scenarios,
        effective_symbols=effective_symbols,
        effective_watch_symbols=effective_watch_symbols,
        effective_addresses=effective_addresses,
        effective_changed_files=effective_changed_files,
        effective_symptom=effective_symptom,
        effective_watch_size=effective_watch_size,
        packet_consistency_warnings=tuple(playtest_packet_diagnostics["warnings"]),
        untrusted_trace_paths=tuple(playtest_packet_diagnostics["untrusted_trace_paths"]),
        frames=frames,
        max_targets=max_targets,
        max_events=max_events,
    )
    late_effective_traces = tuple(
        unique_list([
            *effective_traces,
            *string_items(runtime_attribution.get("trace_paths")),
        ])
    )
    trace_index_for_late_steps = trace_index
    if runtime_attribution.get("status") == "completed":
        runtime_trace_index = build_trace_index_report(
            traces=late_effective_traces,
            reports=tuple(report_paths),
            symbols=effective_symbols,
            watch_symbols=effective_watch_symbols,
            addresses=effective_addresses,
            rules=rules,
            source_files=effective_changed_files,
            symptom=effective_symptom,
            symbols_path=effective_symbols_path,
            max_events=max_events,
            root=root,
        )
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="03_runtime_trace_index",
            phase="attribute",
            title="Index executed runtime attribution evidence",
            data=runtime_trace_index,
            output_dir=output_dir,
            root=root,
        )
        trace_index_for_late_steps = runtime_trace_index

    localize = build_localization_plan(
        changed_files=effective_changed_files,
        symbols=effective_symbols,
        addresses=effective_addresses,
        watch_size=effective_watch_size,
        symptom=effective_symptom,
        reports=tuple(report_paths),
        symbols_path=effective_symbols_path,
        max_candidates=max_targets,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="04_localize",
        phase="localize",
        title="Localize suspects",
        data=localize,
        output_dir=output_dir,
        root=root,
    )

    coverage = build_coverage_report(
        traces=late_effective_traces,
        reports=tuple(report_paths),
        symbols=tuple(unique_list([*effective_symbols, *effective_watch_symbols])),
        rules=rules,
        changed_files=effective_changed_files,
        symbols_path=effective_symbols_path,
        max_targets=max_targets * 2,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="05_coverage",
        phase="coverage",
        title="Measure evidence coverage",
        data=coverage,
        output_dir=output_dir,
        root=root,
    )

    explain = build_explanation_report(
        reports=tuple(report_paths),
        traces=late_effective_traces,
        symbols=effective_symbols,
        watch_symbols=effective_watch_symbols,
        changed_files=effective_changed_files,
        symptom=effective_symptom,
        symbols_path=effective_symbols_path,
        depth=2,
        max_paths=max_targets,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="06_explain",
        phase="explain",
        title="Explain causal paths",
        data=explain,
        output_dir=output_dir,
        root=root,
    )

    taint_symbols = tuple(
        unique_list(
            [
                *effective_watch_symbols,
                *state_symbols_from_trace_index(trace_index_for_late_steps),
                *state_like_symbols(effective_symbols),
            ]
        )[:max_targets]
    )
    if taint_symbols:
        taint_source_files = tuple(
            path
            for path in effective_changed_files
            if Path(path).suffix.lower() == ".asm"
        )
        taint = build_taint_report(
            symbols_path=effective_symbols_path,
            symbols=taint_symbols,
            source_files=taint_source_files,
            max_depth=80,
            max_paths=max_targets,
            root=root,
        )
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="06_taint",
            phase="explain",
            title="Build source-level taint paths",
            data=taint,
            output_dir=output_dir,
            root=root,
        )
    else:
        add_skipped_step(
            steps,
            step_id="06_taint",
            phase="explain",
            title="Build source-level taint paths",
            reason="no --symbol or --watch-symbol inputs were supplied",
        )

    compare = build_compare_plan(
        reports=tuple(report_paths),
        changed_files=effective_changed_files,
        symbols=effective_symbols,
        symptom=effective_symptom,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="07_compare",
        phase="compare",
        title="Route mirrors and expectations",
        data=compare,
        output_dir=output_dir,
        root=root,
    )

    if content_files:
        content_mirror = build_content_mirror_report(
            changed_files=content_files,
            max_files=max_targets,
            root=root,
        )
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="07_content_mirror",
            phase="compare",
            title="Check content source mirrors",
            data=content_mirror,
            output_dir=output_dir,
            root=root,
        )

    if expectations or expectation_files:
        expect = build_expectation_report(
            reports=tuple(report_paths),
            traces=late_effective_traces,
            expectation_files=expectation_files,
            expectations=expectations,
            symptom=effective_symptom,
            symbols_path=effective_symbols_path,
            max_events=max_events,
            root=root,
        )
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="08_expect",
            phase="compare",
            title="Evaluate behavior expectations",
            data=expect,
            output_dir=output_dir,
            root=root,
        )
    else:
        add_skipped_step(
            steps,
            step_id="08_expect",
            phase="compare",
            title="Evaluate behavior expectations",
            reason="no --expect or --expect-file inputs were supplied",
        )

    seed_manifest = display_output_path(output_dir / "generated_seeds.jsonl", root=root) if output_dir else ""
    generate = build_generation_plan(
        reports=tuple(report_paths),
        scenarios=effective_scenarios,
        families=families,
        symbols=effective_symbols,
        changed_files=effective_changed_files,
        symptom=effective_symptom,
        out_scenarios=seed_manifest,
        max_cases=max_cases,
        seed=seed,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="09_generate",
        phase="generate",
        title="Plan counterexample generation",
        data=generate,
        output_dir=output_dir,
        root=root,
    )

    fuzz = build_fuzz_plan(
        reports=tuple(report_paths),
        scenarios=effective_scenarios,
        families=families,
        symbols=effective_symbols,
        changed_files=effective_changed_files,
        symptom=effective_symptom,
        out_cases=display_output_path(output_dir / "fuzz_cases.jsonl", root=root) if output_dir else "",
        max_cases=max_cases,
        seed=seed,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="09_fuzz",
        phase="generate",
        title="Plan fuzz campaigns",
        data=fuzz,
        output_dir=output_dir,
        root=root,
    )

    minimize = build_minimization_plan(
        reports=tuple(report_paths),
        traces=late_effective_traces,
        scenarios=effective_scenarios,
        symbols=effective_symbols,
        rules=rules,
        addresses=effective_addresses,
        expectations=expectations,
        expectation_files=expectation_files,
        changed_files=effective_changed_files,
        symptom=effective_symptom,
        out_trace=display_output_path(output_dir / "minimized_trace.json", root=root) if output_dir else "",
        symbols_path=effective_symbols_path,
        max_scenarios=min(max_cases, 20),
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="10_minimize",
        phase="minimize",
        title="Plan minimization",
        data=minimize,
        output_dir=output_dir,
        root=root,
    )

    rank = rank_findings(reports=tuple(report_paths), root=root)
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="11_rank",
        phase="rank",
        title="Rank findings",
        data=rank,
        output_dir=output_dir,
        root=root,
    )

    impact = build_impact_report(
        reports=tuple(report_paths),
        changed_files=effective_changed_files,
        symbols=effective_symbols,
        symptom=effective_symptom,
        max_items=max_targets * 2,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="12_impact",
        phase="rank",
        title="Rank impact",
        data=impact,
        output_dir=output_dir,
        root=root,
    )

    static_report_path = ""
    visualization_path = ""
    static_report_json = None
    visualization_json = None
    if output_dir:
        static_report_json = build_static_report(
            reports=tuple(report_paths),
            output_format="markdown",
            title="Unified Pokemon Gold Romhack Debugger Investigation",
            root=root,
        )
        static_report_file = output_dir / "investigation_report.md"
        write_static_report(static_report_json, static_report_file)
        static_report_path = display_output_path(static_report_file, root=root)
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="13_report",
            phase="report",
            title="Render static report",
            data=static_report_json,
            output_dir=output_dir,
            root=root,
        )

        visualization_json = build_visualization_report(
            reports=tuple(report_paths),
            traces=late_effective_traces,
            output_format="markdown",
            title="Unified Pokemon Gold Romhack Debugger Investigation",
            max_items=max(80, max_targets * 4),
            root=root,
        )
        visualization_file = output_dir / "investigation_visualization.md"
        write_visualization(visualization_json, visualization_file)
        visualization_path = display_output_path(visualization_file, root=root)
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="14_visualize",
            phase="report",
            title="Render visualization",
            data=visualization_json,
            output_dir=output_dir,
            root=root,
        )

    errors = unique_list(
        error
        for step in steps
        for error in step.get("errors", [])
    )
    warnings = unique_list(
        warning
        for step in steps
        for warning in step.get("warnings", [])
    )
    commands = unique_list(
        command
        for step in steps
        for command in step.get("commands", [])
    )
    failed_expectations = expectation_failures(produced_reports)
    failed_steps = [step for step in steps if step.get("status") == "failed"]
    skipped_steps = [step for step in steps if step.get("status") == "skipped"]

    return {
        "schema_version": 1,
        "kind": "unified_debugger_investigation_run",
        "root": str(root),
        "valid": not errors,
        "passed": not errors and not failed_expectations and not failed_steps,
        "out_dir": display_output_path(output_dir, root=root) if output_dir else "",
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "input_reports": list(reports),
        "effective_input_reports": list(effective_input_reports),
        "input_traces": list(traces),
        "input_logs": list(input_logs),
        "effective_input_logs": list(effective_input_logs),
        "effective_traces": list(effective_traces),
        "effective_runtime_traces": list(late_effective_traces),
        "patches": list(patches),
        "input_changed_files": list(changed_files),
        "input_symbols": list(symbols),
        "input_watch_symbols": list(watch_symbols),
        "input_addresses": list(addresses),
        "rom": effective_rom_path,
        "symbols_path": effective_symbols_path,
        "save_state": effective_save_state,
        "scenarios": list(effective_scenarios),
        "changed_files": list(effective_changed_files),
        "symbols": list(effective_symbols),
        "watch_symbols": list(effective_watch_symbols),
        "effective_watch_symbols": list(effective_watch_symbols),
        "addresses": list(effective_addresses),
        "derived_inputs": derived_inputs,
        "derived_playtest_inputs": playtest_inputs,
        "trusted_playtest_traces": trusted_playtest_traces,
        "playtest_packet_diagnostics": playtest_packet_diagnostics,
        "playtest_consistency_status_counts": playtest_packet_diagnostics["consistency_status_counts"],
        "playtest_consistency_failed_count": playtest_packet_diagnostics["consistency_failed_count"],
        "playtest_untrusted_trace_paths": playtest_packet_diagnostics["untrusted_trace_paths"],
        "derived_expectation_inputs": derived_expectation_inputs,
        "playtest_evidence_route_count": len(playtest_evidence_routes),
        "playtest_evidence_routes": playtest_evidence_routes,
        "playtest_route_status_counts": count_route_field(playtest_evidence_routes, "status", default="unknown"),
        "playtest_route_execution_status_counts": count_route_field(
            playtest_evidence_routes,
            "execution_status",
            default="planned_only",
        ),
        "playtest_route_proof_status_counts": count_route_field(playtest_evidence_routes, "proof_status", default="planned_only"),
        "playtest_expected_route_proof_status_counts": count_route_field(
            playtest_evidence_routes,
            "expected_proof_status",
            default="planned_only",
        ),
        "playtest_runnable_evidence_routes": [
            route for route in playtest_evidence_routes if route.get("runnable")
        ],
        "playtest_blocked_evidence_routes": [
            route for route in playtest_evidence_routes if not route.get("runnable")
        ],
        "rules": list(rules),
        "watch_size": effective_watch_size,
        "executed_watch": execute_watch,
        "executed_snapshots": execute_snapshots,
        "executed_attribution": execute_attribution,
        "runtime_attribution": runtime_attribution,
        "symptom": effective_symptom,
        "phase_count": len({step["phase"] for step in steps}),
        "investigation_step_count": len(steps),
        "produced_report_count": len(produced_reports),
        "failed_count": len(failed_steps) + len(failed_expectations),
        "skipped_count": len(skipped_steps),
        "steps": steps,
        "reports": produced_reports,
        "report_paths": report_paths,
        "finding_count": int(rank.get("finding_count", 0)),
        "impact_count": int(impact.get("impact_count", 0)),
        "top_findings": rank.get("findings", [])[:20],
        "top_impact": impact.get("items", [])[:20],
        "static_report": static_report_path,
        "visualization": visualization_path,
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "This command coordinates the investigation packet; expensive subsystem commands are planned unless their underlying tool explicitly executes inside a report.",
            "A complete investigation packet is only proof when the included evidence is ROM-backed and any expectation report passed.",
            "Subsystem semantic reducers and exact mirrors still own behavior-specific proof where they exist.",
        ],
    }


def execute_runtime_attribution_chain(
    *,
    steps: list[dict[str, Any]],
    produced_reports: list[dict[str, Any]],
    report_paths: list[str],
    output_dir: Path | None,
    root: Path,
    execute_attribution: bool,
    effective_rom_path: str,
    effective_symbols_path: str,
    effective_save_state: str,
    effective_traces: tuple[str, ...],
    effective_input_logs: tuple[str, ...],
    effective_scenarios: tuple[str, ...],
    effective_symbols: tuple[str, ...],
    effective_watch_symbols: tuple[str, ...],
    effective_addresses: tuple[str, ...],
    effective_changed_files: tuple[str, ...],
    effective_symptom: str,
    effective_watch_size: int,
    frames: int,
    max_targets: int,
    max_events: int,
    packet_consistency_warnings: tuple[str, ...] = (),
    untrusted_trace_paths: tuple[str, ...] = (),
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "attempted": execute_attribution,
        "status": "not_requested",
        "trace_paths": list(effective_traces),
        "trace_record_count": 0,
        "effect_event_count": 0,
        "reverse_result_count": 0,
        "dynamic_write_attribution_count": 0,
        "causal_path_count": 0,
        "hook_order_executed": False,
        "hook_order_proof_status": "planned_only",
        "hook_order_passed": False,
        "reports": [],
        "warnings": list(packet_consistency_warnings),
        "untrusted_trace_paths": list(untrusted_trace_paths),
    }
    if not execute_attribution:
        return summary
    if not effective_symbols_path:
        add_skipped_step(
            steps,
            step_id="03_runtime_attribution",
            phase="attribute",
            title="Execute instruction/effect attribution",
            reason="runtime attribution needs a symbols file",
        )
        summary["status"] = "skipped"
        return summary

    trace_paths = list(effective_traces)
    can_capture_trace = bool(
        effective_rom_path
        and effective_save_state
        and (
            effective_symbols
            or effective_watch_symbols
            or effective_addresses
            or effective_changed_files
            or effective_symptom
            or report_paths
        )
    )
    if not trace_paths and not can_capture_trace:
        reason = "runtime attribution needs either an input trace or ROM, save state, and a traceable symbol/source target"
        if untrusted_trace_paths:
            reason = (
                "runtime attribution skipped because packet trace evidence failed consistency checks "
                "and no fresh ROM/save-state trace target could be captured"
            )
        add_skipped_step(
            steps,
            step_id="03_runtime_attribution",
            phase="attribute",
            title="Execute instruction/effect attribution",
            reason=reason,
        )
        summary["warnings"].append(reason)
        summary["status"] = "skipped"
        return summary

    hook_order_execute = can_capture_trace
    hook_order = build_hook_order_probe_report(execute=hook_order_execute, root=root)
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="03_hook_order_probe",
        phase="attribute",
        title="Validate PyBoy hook-order timing" if hook_order_execute else "Plan PyBoy hook-order validation",
        data=hook_order,
        output_dir=output_dir,
        root=root,
    )
    hook_order_report_path = investigation_report_path(output_dir, "03_hook_order_probe", root=root)
    summary["reports"].append(hook_order_report_path)
    summary["hook_order_executed"] = bool(hook_order.get("executed"))
    summary["hook_order_proof_status"] = str(hook_order.get("proof_status", "planned_only"))
    summary["hook_order_passed"] = bool(hook_order.get("passed"))

    if can_capture_trace:
        out_trace = investigation_artifact_path(
            output_dir,
            "03_instruction_trace.jsonl",
            fallback=".local\\tmp\\debugger_investigation_instruction_trace.jsonl",
            root=root,
        )
        instruction_trace = build_instruction_trace_report(
            function_symbols=effective_symbols,
            watch_symbols=effective_watch_symbols,
            watch_addresses=effective_addresses,
            watch_size=effective_watch_size,
            reports=tuple(report_paths),
            scenario_ids=effective_scenarios,
            changed_files=effective_changed_files,
            symptom=effective_symptom,
            rom_path=effective_rom_path,
            symbols_path=effective_symbols_path,
            save_state=effective_save_state,
            input_logs=effective_input_logs,
            frames=frames,
            max_functions=max(1, max_targets),
            execute=True,
            require_hit=False,
            out_trace=out_trace,
            root=root,
        )
        if not instruction_trace.get("valid") and only_no_traceable_instruction_error(instruction_trace):
            add_skipped_step(
                steps,
                step_id="03_instruction_trace",
                phase="attribute",
                title="Capture instruction trace for attribution",
                reason=str(instruction_trace.get("errors", ["no traceable function symbol was selected"])[0]),
            )
        else:
            add_report(
                steps,
                produced_reports,
                report_paths,
                step_id="03_instruction_trace",
                phase="attribute",
                title="Capture instruction trace for attribution",
                data=instruction_trace,
                output_dir=output_dir,
                root=root,
            )
            summary["reports"].append(investigation_report_path(output_dir, "03_instruction_trace", root=root))
            trace_output = instruction_trace.get("trace_output") if isinstance(instruction_trace.get("trace_output"), dict) else {}
            if trace_output.get("path") and trace_output.get("written"):
                trace_paths = unique_list([*trace_paths, str(trace_output.get("path", ""))])
                summary["trace_record_count"] = int(trace_output.get("record_count", 0) or 0)
            summary["warnings"].extend(string_items(instruction_trace.get("warnings")))

    if not trace_paths:
        add_skipped_step(
            steps,
            step_id="03_effect_trace",
            phase="attribute",
            title="Convert instruction trace into effects",
            reason="no instruction trace was available or captured",
        )
        summary["status"] = "skipped"
        return summary

    summary["trace_paths"] = trace_paths
    effect_trace = build_effect_trace_report(
        reports=(hook_order_report_path,) if hook_order_report_path else (),
        traces=tuple(trace_paths),
        symbols_path=effective_symbols_path,
        watch_symbols=effective_watch_symbols,
        watch_addresses=effective_addresses,
        watch_size=effective_watch_size,
        max_events=max_events,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="03_effect_trace",
        phase="attribute",
        title="Convert instruction trace into effects",
        data=effect_trace,
        output_dir=output_dir,
        root=root,
    )
    effect_report_path = investigation_report_path(output_dir, "03_effect_trace", root=root)
    effect_reports = (effect_report_path,) if effect_report_path else ()
    summary["reports"].append(effect_report_path)
    summary["effect_event_count"] = int(effect_trace.get("effect_event_count", 0) or 0)

    reverse_symbols = tuple(unique_list([*effective_watch_symbols, *state_like_symbols(effective_symbols)])[:max_targets])
    if reverse_symbols or effective_addresses:
        reverse_query = build_reverse_query_report(
            reports=effect_reports,
            traces=() if effect_reports else tuple(trace_paths),
            symbols=reverse_symbols,
            addresses=effective_addresses,
            symbols_path=effective_symbols_path,
            watch_size=effective_watch_size,
            root=root,
        )
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="03_reverse_query",
            phase="attribute",
            title="Query last writers for watched targets",
            data=reverse_query,
            output_dir=output_dir,
            root=root,
        )
        summary["reports"].append(investigation_report_path(output_dir, "03_reverse_query", root=root))
        summary["reverse_result_count"] = int(reverse_query.get("result_count", 0) or 0)
    else:
        add_skipped_step(
            steps,
            step_id="03_reverse_query",
            phase="attribute",
            title="Query last writers for watched targets",
            reason="no watch symbol or address target was available for reverse query",
        )

    if effective_watch_symbols or effective_addresses:
        dynamic_taint = build_dynamic_taint_report(
            reports=effect_reports,
            traces=() if effect_reports else tuple(trace_paths),
            symbols_path=effective_symbols_path,
            sink_symbols=effective_watch_symbols,
            sink_addresses=effective_addresses,
            sink_size=effective_watch_size,
            max_paths=max_targets,
            execute_synthesis=False,
            root=root,
        )
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="03_dynamic_taint",
            phase="attribute",
            title="Attribute taint and sink writes from effects",
            data=dynamic_taint,
            output_dir=output_dir,
            root=root,
        )
        summary["reports"].append(investigation_report_path(output_dir, "03_dynamic_taint", root=root))
        summary["dynamic_write_attribution_count"] = int(dynamic_taint.get("write_attribution_count", 0) or 0)
    else:
        add_skipped_step(
            steps,
            step_id="03_dynamic_taint",
            phase="attribute",
            title="Attribute taint and sink writes from effects",
            reason="no sink symbol or address target was available for dynamic taint",
        )

    causal_graph = build_causal_graph_report(
        reports=tuple(report_paths),
        traces=tuple(trace_paths),
        symbols=effective_symbols,
        addresses=effective_addresses,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="03_causal_graph",
        phase="explain",
        title="Join executed runtime attribution evidence",
        data=causal_graph,
        output_dir=output_dir,
        root=root,
    )
    summary["reports"].append(investigation_report_path(output_dir, "03_causal_graph", root=root))
    summary["causal_path_count"] = int(causal_graph.get("path_count", 0) or 0)
    summary["status"] = "completed"
    return summary


def add_report(
    steps: list[dict[str, Any]],
    produced_reports: list[dict[str, Any]],
    report_paths: list[str],
    *,
    step_id: str,
    phase: str,
    title: str,
    data: dict[str, Any],
    output_dir: Path | None,
    root: Path,
) -> None:
    path = ""
    if output_dir:
        path_obj = output_dir / f"{step_id}.json"
        write_json(data, path_obj)
        path = display_output_path(path_obj, root=root)
        report_paths.append(path)
    report_ref = {
        "id": step_id,
        "kind": str(data.get("kind", "")),
        "path": path,
        "valid": bool(data.get("valid", True)),
        "passed": data.get("passed"),
        "error_count": int(data.get("error_count", 0)),
        "warning_count": int(data.get("warning_count", 0)),
    }
    produced_reports.append(report_ref)
    status = "completed" if report_ref["valid"] else "failed"
    steps.append(
        {
            "id": step_id,
            "phase": phase,
            "title": title,
            "status": status,
            "report_kind": report_ref["kind"],
            "report_path": path,
            "valid": report_ref["valid"],
            "summary": summarize_report(data),
            "errors": list(data.get("errors", []))[:8],
            "warnings": list(data.get("warnings", []))[:8],
            "commands": collect_report_commands(data, source=path)[:24],
        }
    )


def add_skipped_step(
    steps: list[dict[str, Any]],
    *,
    step_id: str,
    phase: str,
    title: str,
    reason: str,
) -> None:
    steps.append(
        {
            "id": step_id,
            "phase": phase,
            "title": title,
            "status": "skipped",
            "report_kind": "",
            "report_path": "",
            "valid": True,
            "summary": {"reason": reason},
            "errors": [],
            "warnings": [reason],
            "commands": [],
        }
    )


def add_input_report_step(
    steps: list[dict[str, Any]],
    *,
    loaded_reports: list[dict[str, Any]],
    report_errors: list[str],
    reports: tuple[str, ...],
) -> None:
    commands = unique_list(
        command
        for loaded in loaded_reports
        for command in collect_report_commands(loaded.get("data", {}), source=str(loaded.get("source", "")))
    )
    steps.append(
        {
            "id": "00_input_reports",
            "phase": "ingest",
            "title": "Inspect input reports",
            "status": "completed" if not report_errors else "failed",
            "report_kind": "input_reports",
            "report_path": ", ".join(reports),
            "valid": not report_errors,
            "summary": {
                "input_report_count": len(loaded_reports),
                "input_report_command_count": len(commands),
            },
            "errors": list(report_errors)[:8],
            "warnings": [],
            "commands": commands[:24],
        }
    )


def add_playtest_packet_diagnostics_step(
    steps: list[dict[str, Any]],
    *,
    diagnostics: dict[str, Any],
) -> None:
    summary = {
        "packet_count": diagnostics.get("packet_count", 0),
        "consistency_failed_count": diagnostics.get("consistency_failed_count", 0),
        "untrusted_trace_count": len(diagnostics.get("untrusted_trace_paths", [])),
        "consistency_status_counts": diagnostics.get("consistency_status_counts", {}),
    }
    steps.append(
        {
            "id": "00_playtest_packet_diagnostics",
            "phase": "ingest",
            "title": "Inspect playtest packet consistency",
            "status": "completed",
            "report_kind": "playtest_packet_diagnostics",
            "report_path": "",
            "valid": True,
            "summary": summary,
            "errors": [],
            "warnings": string_items(diagnostics.get("warnings"))[:8],
            "commands": [],
        }
    )


def state_symbols_from_trace_index(report: dict[str, Any]) -> list[str]:
    symbols = []
    for event in dict_items(report.get("events")):
        symbol = str(event.get("state_symbol", ""))
        if is_state_symbol(symbol):
            symbols.append(symbol)
    for attribution in dict_items(report.get("reverse_attributions")):
        symbol = str(attribution.get("state", ""))
        if is_state_symbol(symbol):
            symbols.append(symbol)
        for related in string_items(attribution.get("related_symbols")):
            if is_state_symbol(related):
                symbols.append(related)
    return unique_list(symbols)


def state_like_symbols(symbols: tuple[str, ...]) -> list[str]:
    return [symbol for symbol in symbols if is_state_symbol(symbol)]


def is_state_symbol(symbol: str) -> bool:
    return str(symbol).startswith(("w", "h", "s", "v", "r"))


def derive_investigation_inputs(loaded_reports: list[dict[str, Any]], *, max_items: int = 24) -> dict[str, list[str]]:
    targets = {
        "changed_files": [],
        "symbols": [],
        "watch_symbols": [],
        "addresses": [],
        "input_logs": [],
    }
    for loaded in loaded_reports:
        collect_investigation_inputs(loaded.get("data"), targets)
    return {
        key: unique_list(values)[:max_items]
        for key, values in targets.items()
    }


def derive_playtest_packet_inputs(
    loaded_reports: list[dict[str, Any]],
    *,
    root: Path,
    max_items: int = 48,
) -> dict[str, list[str]]:
    targets = {
        "roms": [],
        "symbols_paths": [],
        "save_states": [],
        "input_logs": [],
        "screenshots": [],
        "traces": [],
        "reports": [],
        "scenarios": [],
        "changed_files": [],
        "symbols": [],
        "watch_symbols": [],
        "addresses": [],
        "symptoms": [],
        "notes": [],
    }
    for loaded in loaded_reports:
        data = loaded.get("data")
        if not isinstance(data, dict) or data.get("kind") != "unified_debugger_playtest_packet":
            continue
        packet_root = playtest_packet_root(data)
        add_first_string(targets["roms"], packet_path_reference(data.get("rom"), packet_root=packet_root, root=root))
        add_first_string(
            targets["symbols_paths"],
            packet_path_reference(data.get("symbols"), packet_root=packet_root, root=root),
        )
        add_first_string(
            targets["save_states"],
            packet_path_reference(data.get("save_state"), packet_root=packet_root, root=root),
        )
        add_first_string(
            targets["input_logs"],
            packet_path_reference(data.get("input_log"), packet_root=packet_root, root=root),
        )
        add_first_string(
            targets["screenshots"],
            packet_path_reference(data.get("screenshot"), packet_root=packet_root, root=root),
        )
        targets["traces"].extend(packet_path_references(data.get("traces"), packet_root=packet_root, root=root))
        targets["reports"].extend(packet_path_references(data.get("reports"), packet_root=packet_root, root=root))
        targets["scenarios"].extend(packet_path_references(data.get("scenarios"), packet_root=packet_root, root=root))
        targets["changed_files"].extend(
            item
            for item in packet_path_references(data.get("changed_files"), packet_root=packet_root, root=root)
            if looks_like_investigation_source_path(item)
        )
        targets["symbols"].extend(
            item
            for item in string_items(data.get("symbols_to_investigate"))
            if looks_like_investigation_symbol(item)
        )
        targets["watch_symbols"].extend(
            item
            for item in string_items(data.get("watch_symbols"))
            if looks_like_investigation_symbol(item)
        )
        targets["addresses"].extend(string_items(data.get("addresses")))
        add_first_string(targets["symptoms"], data.get("symptom"))
        targets["notes"].extend(string_items(data.get("notes")))
    return {
        key: unique_list(values)[:max_items]
        for key, values in targets.items()
    }


def collect_playtest_evidence_routes(
    loaded_reports: list[dict[str, Any]],
    *,
    max_items: int = 120,
) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    for loaded in loaded_reports:
        data = loaded.get("data")
        if not isinstance(data, dict) or data.get("kind") != "unified_debugger_playtest_packet":
            continue
        packet_id = str(data.get("packet_id") or loaded.get("source") or "")
        source = str(loaded.get("source") or "")
        for route in dict_items(data.get("evidence_routes")):
            command = str(route.get("command") or "")
            runnable = bool(route.get("runnable", True)) and command_is_runnable(command)
            expected_proof = str(
                route.get("expected_proof_status")
                or route.get("proof_status")
                or "planned_only"
            )
            routes.append(
                {
                    "source": source,
                    "packet_id": packet_id,
                    "id": str(route.get("id") or ""),
                    "phase": str(route.get("phase") or ""),
                    "title": str(route.get("title") or route.get("id") or ""),
                    "status": str(route.get("status") or ("ready" if runnable else "planned")),
                    "execution_status": str(
                        route.get("execution_status")
                        or ("ready_to_run" if runnable else "planned_only")
                    ),
                    "runnable": runnable,
                    "proof_status": str(route.get("proof_status") or "planned_only"),
                    "expected_proof_status": expected_proof,
                    "produces": str(route.get("produces") or ""),
                    "produced_output_exists": bool(route.get("produced_output_exists")),
                    "produced_output_kind": str(route.get("produced_output_kind") or ""),
                    "produced_output_valid": bool(route.get("produced_output_valid")),
                    "produced_output_proof_status": str(route.get("produced_output_proof_status") or ""),
                    "command": command,
                    "required_inputs": string_items(route.get("required_inputs")),
                }
            )
    return routes[:max_items]


def collect_playtest_packet_diagnostics(
    loaded_reports: list[dict[str, Any]],
    *,
    root: Path,
    max_items: int = 120,
) -> dict[str, Any]:
    packets: list[dict[str, Any]] = []
    status_counts: dict[str, int] = {}
    untrusted_trace_paths: list[str] = []
    warnings: list[str] = []
    consistency_failed_count = 0
    for loaded in loaded_reports:
        data = loaded.get("data")
        if not isinstance(data, dict) or data.get("kind") != "unified_debugger_playtest_packet":
            continue
        packet_root = playtest_packet_root(data)
        source = str(loaded.get("source") or "")
        packet_id = str(data.get("packet_id") or source or "")
        checks = [
            normalized_packet_consistency_check(check, packet_root=packet_root, root=root)
            for check in dict_items(data.get("consistency_checks"))
        ]
        packet_counts = packet_consistency_status_counts(checks)
        if not packet_counts:
            packet_counts = normalized_count_map(data.get("consistency_status_counts"))
        merge_counts(status_counts, packet_counts)
        failed_checks = [check for check in checks if check.get("status") == "failed"]
        failed_trace_paths = unique_list(
            check["path"]
            for check in failed_checks
            if str(check.get("field", "")).startswith("trace_") and check.get("path")
        )
        packet_warnings = unique_list(
            [
                str(check.get("message", ""))
                for check in failed_checks
                if check.get("message")
            ]
            + [
                f"playtest packet {packet_id} trace {path} failed consistency checks; excluded from runtime attribution inputs"
                for path in failed_trace_paths
            ]
        )
        consistency_failed_count += len(failed_checks)
        untrusted_trace_paths.extend(failed_trace_paths)
        warnings.extend(packet_warnings)
        reproducibility = data.get("reproducibility") if isinstance(data.get("reproducibility"), dict) else {}
        packets.append(
            {
                "source": source,
                "packet_id": packet_id,
                "runtime_replay_ready": bool(reproducibility.get("runtime_replay_ready")),
                "black_box_replay_ready": bool(reproducibility.get("black_box_replay_ready")),
                "visual_handoff_ready": bool(reproducibility.get("visual_handoff_ready")),
                "consistency_failed_count": len(failed_checks),
                "consistency_status_counts": packet_counts,
                "failed_consistency_checks": failed_checks[:max_items],
                "untrusted_trace_paths": failed_trace_paths,
                "warnings": packet_warnings,
            }
        )
    return {
        "packet_count": len(packets),
        "consistency_status_counts": dict(sorted(status_counts.items())),
        "consistency_failed_count": consistency_failed_count,
        "untrusted_trace_paths": unique_list(untrusted_trace_paths)[:max_items],
        "warnings": unique_list(warnings)[:max_items],
        "packets": packets[:max_items],
    }


def trusted_playtest_trace_paths(
    traces: list[str],
    *,
    diagnostics: dict[str, Any],
) -> list[str]:
    blocked = {trace_path_key(path) for path in string_items(diagnostics.get("untrusted_trace_paths"))}
    return [
        trace
        for trace in traces
        if trace_path_key(trace) not in blocked
    ]


def normalized_packet_consistency_check(
    check: dict[str, Any],
    *,
    packet_root: Path | None,
    root: Path,
) -> dict[str, Any]:
    artifact = str(check.get("artifact") or "")
    path = packet_path_reference(artifact, packet_root=packet_root, root=root)
    return {
        "artifact": artifact,
        "path": path,
        "field": str(check.get("field") or ""),
        "observed": str(check.get("observed") or ""),
        "expected": str(check.get("expected") or ""),
        "status": str(check.get("status") or "unknown"),
        "message": str(check.get("message") or ""),
    }


def packet_consistency_status_counts(checks: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for check in checks:
        status = str(check.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def normalized_count_map(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, int] = {}
    for key, raw_count in value.items():
        try:
            count = int(raw_count)
        except (TypeError, ValueError):
            continue
        out[str(key)] = count
    return dict(sorted(out.items()))


def merge_counts(target: dict[str, int], source: dict[str, int]) -> None:
    for key, count in source.items():
        target[key] = target.get(key, 0) + count


def trace_path_key(path: str) -> str:
    return normalize_report_path(path).lower()


def count_route_field(routes: list[dict[str, Any]], field: str, *, default: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for route in routes:
        value = str(route.get(field) or default)
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def playtest_packet_root(data: dict[str, Any]) -> Path | None:
    raw_root = str(data.get("root") or "").strip()
    if not raw_root:
        return None
    return Path(raw_root)


def packet_path_references(value: Any, *, packet_root: Path | None, root: Path) -> list[str]:
    return [
        reference
        for item in string_items(value)
        for reference in [packet_path_reference(item, packet_root=packet_root, root=root)]
        if reference
    ]


def packet_path_reference(value: Any, *, packet_root: Path | None, root: Path) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    path = Path(text)
    if path.is_absolute() or packet_root is None:
        return text
    resolved = packet_root / path
    try:
        return str(resolved.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved.resolve())


def investigation_symbols_path(*, requested: str, playtest_symbols: list[str]) -> str:
    if requested and requested != "pokegold.sym":
        return requested
    return first_item(playtest_symbols) or requested


def add_first_string(out: list[str], value: Any) -> None:
    text = str(value or "").strip()
    if text:
        out.append(text)


def first_item(values: list[str]) -> str:
    return values[0] if values else ""


def collect_investigation_inputs(data: Any, targets: dict[str, list[str]]) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            lowered = str(key).lower()
            if lowered == "route_input_availability":
                continue
            if lowered == "symbols" and isinstance(value, str) and looks_like_artifact_path(value):
                continue
            if lowered in {"input_log", "input_logs", "out_input_log"}:
                for item in string_items(value):
                    if looks_like_artifact_path(item):
                        targets["input_logs"].append(normalize_report_path(item))
            if lowered in {"changed_file", "changed_files", "source_file", "source_files", "related_files"}:
                for item in string_items(value):
                    if looks_like_investigation_source_path(item):
                        targets["changed_files"].append(normalize_report_path(item))
            elif lowered in {
                "address",
                "bank_address",
                "related_addresses",
                "watch_address",
                "watch_addresses",
                "sink_address",
                "sink_addresses",
                "semantic_watch_addresses",
                "semantic_replay_watch_addresses",
            }:
                targets["addresses"].extend(string_items(value))
            elif lowered == "source_mems":
                add_source_mem_targets(value, targets)
            elif lowered in {
                "symbol",
                "symbols",
                "source_symbol",
                "source_symbols",
                "sink_symbol",
                "sink_symbols",
                "state_symbol",
                "state_symbols",
                "related_symbols",
                "trace_symbols",
                "watch",
                "watch_symbols",
                "semantic_watch_symbols",
                "semantic_replay_watch_symbols",
            }:
                for item in string_items(value):
                    if not looks_like_investigation_symbol(item):
                        continue
                    if "watch" in lowered or is_state_symbol(item):
                        targets["watch_symbols"].append(item)
                    else:
                        targets["symbols"].append(item)
            collect_investigation_inputs(value, targets)
    elif isinstance(data, list):
        for item in data:
            collect_investigation_inputs(item, targets)


def add_source_mem_targets(value: Any, targets: dict[str, list[str]]) -> None:
    for address, origin in source_mem_parts(value):
        if address:
            targets["addresses"].append(address)
        if not origin or not looks_like_investigation_symbol(origin):
            continue
        if is_state_symbol(origin):
            targets["watch_symbols"].append(origin)
        else:
            targets["symbols"].append(origin)


def source_mem_parts(value: Any) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for item in string_items(value):
        text = str(item).strip()
        if not text:
            continue
        if "=" in text:
            address, origin = text.split("=", 1)
            out.append((address.strip(), origin.strip()))
        else:
            out.append((text, ""))
    return out


def load_investigation_expectations(
    *,
    expectations: tuple[str, ...],
    expectation_files: tuple[str, ...],
    root: Path,
) -> list[dict[str, Any]]:
    records = [parse_cli_expectation(raw) for raw in expectations]
    file_records, _errors = load_expectation_files(
        expectation_files=expectation_files,
        root=root,
    )
    records.extend(file_records)
    return records


def derive_inputs_from_expectations(
    expectation_records: list[dict[str, Any]],
    *,
    max_items: int = 24,
) -> dict[str, list[str]]:
    targets = {
        "changed_files": [],
        "symbols": [],
        "watch_symbols": [],
        "addresses": [],
    }
    for record in expectation_records:
        collect_investigation_inputs(record, targets)
    return {
        key: unique_list(values)[:max_items]
        for key, values in targets.items()
    }


def investigation_watch_size(
    *,
    requested: int,
    loaded_reports: list[dict[str, Any]],
    expectation_records: list[dict[str, Any]],
) -> int:
    sizes = [positive_int(requested)]
    for loaded in loaded_reports:
        sizes.extend(watch_sizes_from_data(loaded.get("data", {})))
    for record in expectation_records:
        sizes.extend(watch_sizes_from_data(record))
        sizes.append(expectation_watch_size(record))
        nested = record.get("expectation")
        if isinstance(nested, dict):
            sizes.append(expectation_watch_size(nested))
    return max([size for size in sizes if size > 0] or [1])


def watch_sizes_from_data(data: Any) -> list[int]:
    sizes: list[int] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if str(key).lower() in {"watch_size", "sink_size"}:
                size = positive_int(value)
                if size:
                    sizes.append(size)
            sizes.extend(watch_sizes_from_data(value))
    elif isinstance(data, list):
        for item in data:
            sizes.extend(watch_sizes_from_data(item))
    return sizes


def positive_int(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return number if number > 0 else 0


def looks_like_investigation_symbol(value: str) -> bool:
    text = str(value).strip()
    if (
        not text
        or "/" in text
        or "\\" in text
        or text.startswith(("$", "0x", "0X", ".", "<"))
        or looks_like_artifact_path(text)
    ):
        return False
    return text[0].isalpha() and all(char.isalnum() or char in {"_", "."} for char in text)


def looks_like_artifact_path(value: str) -> bool:
    suffix = Path(str(value).strip()).suffix.lower()
    return suffix in {
        ".gb",
        ".gbc",
        ".sym",
        ".json",
        ".jsonl",
        ".state",
        ".sgm",
        ".sav",
        ".png",
        ".bmp",
        ".gif",
        ".jpg",
        ".jpeg",
        ".inputs",
        ".log",
        ".txt",
    }


def looks_like_investigation_source_path(value: str) -> bool:
    normalized = normalize_report_path(value)
    if not normalized or "/" not in normalized:
        return False
    suffix = Path(normalized).suffix.lower()
    return suffix not in {".json", ".jsonl", ".state", ".sgm", ".sav", ".gbc", ".sym"}


def normalize_report_path(value: str) -> str:
    return str(value).strip().replace("\\", "/")


def summarize_report(data: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "valid",
        "passed",
        "artifact_count",
        "event_count",
        "dynamic_context_event_count",
        "matched_event_count",
        "reverse_attribution_count",
        "write_attribution_count",
        "invariant_count",
        "failed_invariant_count",
        "rom_mirror_count",
        "failed_rom_mirror_count",
        "path_count",
        "candidate_count",
        "target_count",
        "uncovered_target_count",
        "match_count",
        "expectation_count",
        "failed_count",
        "scenario_count",
        "behavioral_probe_count",
        "generator_count",
        "finding_count",
        "impact_count",
        "investigation_step_count",
        "produced_report_count",
        "playtest_evidence_route_count",
        "playtest_consistency_failed_count",
        "command_count",
        "timeline_event_count",
        "graph_node_count",
    )
    return {key: data[key] for key in keys if key in data}


def collect_report_commands(data: dict[str, Any], *, source: str = "") -> list[str]:
    commands: list[str] = []
    collect_high_signal_report_commands(data, commands, source=source)
    add_strings(commands, data.get("commands"))
    add_strings(commands, data.get("runnable_commands"))
    add_strings(commands, data.get("blocked_commands"))
    add_strings(commands, data.get("materialization_commands"))
    add_strings(commands, data.get("counterexample_commands"))
    for phase in dict_items(data.get("phase_steps")):
        for step in dict_items(phase.get("steps")):
            add_strings(commands, step.get("command"))
    for step in dict_items(data.get("steps")):
        add_strings(commands, step.get("command"))
        add_strings(commands, step.get("commands"))
    for item in dict_items(data.get("items")):
        add_strings(commands, item.get("next_actions"))
    for finding in dict_items(data.get("findings")):
        add_strings(commands, finding.get("next_actions"))
    for attribution in dict_items(data.get("reverse_attributions")):
        add_strings(commands, attribution.get("commands"))
    for attribution in dict_items(data.get("write_attributions")):
        add_strings(commands, attribution.get("commands"))
    for expectation in dict_items(data.get("expectations")):
        add_strings(commands, expectation.get("commands"))
    for invariant in dict_items(data.get("invariants")):
        add_strings(commands, invariant.get("commands"))
    for scenario in dict_items(data.get("scenarios")):
        add_strings(commands, scenario.get("commands"))
        for probe in dict_items(scenario.get("behavioral_probes")):
            add_strings(commands, probe.get("command"))
    return unique_list(commands)


def collect_high_signal_report_commands(data: dict[str, Any], commands: list[str], *, source: str = "") -> None:
    trace_synthesis_plan = data.get("trace_synthesis_plan")
    if isinstance(trace_synthesis_plan, dict):
        add_strings(commands, trace_synthesis_plan.get("commands"))
        for route in dict_items(trace_synthesis_plan.get("routes")):
            add_strings(commands, route.get("commands"))
    state_patch_minimization = data.get("state_patch_minimization")
    if isinstance(state_patch_minimization, dict):
        if source:
            add_strings(commands, f"python -m tools.debugger provenance --report {source}")
            add_strings(commands, f"python -m tools.debugger taint --report {source}")
            add_strings(commands, f"python -m tools.debugger slice --report {source}")
        add_strings(commands, state_patch_minimization.get("commands"))
    evidence_minimization = data.get("evidence_minimization")
    if isinstance(evidence_minimization, dict) and evidence_minimization.get("out_trace"):
        add_strings(commands, f"python -m tools.debugger trace-index --trace {evidence_minimization['out_trace']}")
    input_log_minimization = data.get("input_log_minimization")
    if isinstance(input_log_minimization, dict):
        add_strings(commands, input_log_minimization.get("commands"))
        out_input_log = str(input_log_minimization.get("out_input_log") or "")
        if out_input_log:
            add_strings(commands, f"python -m tools.debugger ingest --input-log {out_input_log}")
    for campaign in dict_items(data.get("campaigns")):
        add_strings(commands, campaign.get("commands"))
    for case in dict_items(data.get("fuzz_cases")):
        add_strings(commands, case.get("commands"))
        materialization_request = case.get("materialization_request")
        if isinstance(materialization_request, dict):
            add_strings(commands, materialization_request.get("commands"))
        for probe in dict_items(case.get("behavioral_probes")):
            add_strings(commands, probe.get("command"))
    for match in dict_items(data.get("matches")):
        add_strings(commands, match.get("commands"))
        add_strings(commands, match.get("materialization_commands"))
        add_strings(commands, match.get("counterexample_commands"))
    for generator in dict_items(data.get("generators")):
        for key in ("commands", "counterexample_commands", "materialization_commands"):
            for item in dict_items(generator.get(key)):
                add_strings(commands, item.get("command"))
    for counterexample in dict_items(data.get("counterexamples")):
        add_strings(commands, counterexample.get("command"))


def content_mirror_files(changed_files: tuple[str, ...], *, root: Path) -> tuple[str, ...]:
    out: list[str] = []
    for raw_path in changed_files:
        normalized = normalize_source_path(raw_path, root=root).lower()
        if any(normalized.startswith(prefix) for prefix in CONTENT_PREFIXES):
            out.append(raw_path)
    return tuple(unique_list(out))


CONTENT_PREFIXES = (
    "maps/",
    "data/",
    "gfx/",
    "audio/",
    "text/",
    "scripts/",
    "engine/events/",
    "engine/gfx/",
    "engine/menus/",
    "engine/overworld/",
)


def normalize_source_path(raw_path: str, *, root: Path) -> str:
    path = Path(raw_path)
    if path.is_absolute():
        try:
            return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")
    return raw_path.replace("\\", "/")


def expectation_failures(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        report
        for report in reports
        if report.get("kind") == "unified_debugger_expectation_report"
        and report.get("passed") is False
    ]


def write_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True),
        encoding="utf-8",
        newline="\n",
    )


def resolve_output_dir(out_dir: str, *, root: Path) -> Path | None:
    if not out_dir:
        return None
    path = Path(out_dir)
    if not path.is_absolute():
        path = root / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def display_output_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


def investigation_report_path(output_dir: Path | None, step_id: str, *, root: Path) -> str:
    if output_dir is None:
        return ""
    return display_output_path(output_dir / f"{step_id}.json", root=root)


def investigation_artifact_path(output_dir: Path | None, filename: str, *, fallback: str, root: Path) -> str:
    if output_dir is None:
        return fallback
    return display_output_path(output_dir / filename, root=root)


def only_no_traceable_instruction_error(report: dict[str, Any]) -> bool:
    errors = string_items(report.get("errors"))
    return bool(errors) and all(error.startswith("no traceable function symbol was selected") for error in errors)


def add_strings(out: list[str], value: Any) -> None:
    if value is None:
        return
    if isinstance(value, str):
        if value:
            out.append(value)
        return
    if isinstance(value, list | tuple | set):
        for item in value:
            add_strings(out, item)


def dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, dict)]


def string_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list | tuple | set):
        return [
            nested
            for item in value
            for nested in string_items(item)
        ]
    return [str(value)] if value else []
