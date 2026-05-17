from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .content_mirror import build_content_mirror_report
from .content_scenarios import build_content_scenario_report
from .coverage import build_coverage_report
from .expect import build_expectation_report
from .explain import build_explanation_report
from .fuzz import build_fuzz_plan
from .generate import build_generation_plan
from .impact import build_impact_report
from .ingest import ingest_artifacts
from .localize import build_localization_plan
from .minimize import build_minimization_plan
from .mirrors import build_compare_plan
from .ranking import rank_findings
from .replay import build_replay_plan
from .reporting import build_static_report, write_static_report
from .taint import build_taint_report
from .trace_index import build_trace_index_report, unique_list
from .visualization import build_visualization_report, write_visualization
from .workflow import command_is_runnable


DEFAULT_OUT_DIR = ".local\\tmp\\debugger_investigation"


def build_investigation_run(
    *,
    rom_path: str = "",
    symbols_path: str = "pokegold.sym",
    save_state: str = "",
    traces: tuple[str, ...] = (),
    scenarios: tuple[str, ...] = (),
    reports: tuple[str, ...] = (),
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
    report_paths = list(reports)

    ingest = ingest_artifacts(
        roms=(rom_path,) if rom_path else (),
        symbols=(symbols_path,) if symbols_path else (),
        traces=traces,
        save_states=(save_state,) if save_state else (),
        scenarios=scenarios,
        changed_files=changed_files,
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

    trace_index = build_trace_index_report(
        traces=traces,
        reports=tuple(report_paths),
        symbols=symbols,
        watch_symbols=watch_symbols,
        addresses=addresses,
        rules=rules,
        source_files=changed_files,
        symptom=symptom,
        symbols_path=symbols_path,
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

    content_files = content_mirror_files(changed_files, root=root)
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
        rom_path=rom_path,
        symbols_path=symbols_path,
        save_state=save_state,
        traces=traces,
        scenarios=scenarios,
        reports=tuple(report_paths),
        watch_symbols=watch_symbols,
        symbols=symbols,
        changed_files=changed_files,
        symptom=symptom,
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

    localize = build_localization_plan(
        changed_files=changed_files,
        symbols=symbols,
        symptom=symptom,
        reports=tuple(report_paths),
        symbols_path=symbols_path,
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
        traces=traces,
        reports=tuple(report_paths),
        symbols=tuple(unique_list([*symbols, *watch_symbols])),
        rules=rules,
        changed_files=changed_files,
        symbols_path=symbols_path,
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
        traces=traces,
        symbols=symbols,
        watch_symbols=watch_symbols,
        changed_files=changed_files,
        symptom=symptom,
        symbols_path=symbols_path,
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
        unique_list([*watch_symbols, *state_symbols_from_trace_index(trace_index), *state_like_symbols(symbols)])[:max_targets]
    )
    if taint_symbols:
        taint_source_files = tuple(
            path
            for path in changed_files
            if Path(path).suffix.lower() == ".asm"
        )
        taint = build_taint_report(
            symbols_path=symbols_path,
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
        changed_files=changed_files,
        symbols=symbols,
        symptom=symptom,
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
            traces=traces,
            expectation_files=expectation_files,
            expectations=expectations,
            symptom=symptom,
            symbols_path=symbols_path,
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
        scenarios=scenarios,
        families=families,
        symbols=symbols,
        changed_files=changed_files,
        symptom=symptom,
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
        scenarios=scenarios,
        families=families,
        symbols=symbols,
        changed_files=changed_files,
        symptom=symptom,
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
        traces=traces,
        scenarios=scenarios,
        symbols=symbols,
        rules=rules,
        addresses=addresses,
        expectations=expectations,
        expectation_files=expectation_files,
        changed_files=changed_files,
        symptom=symptom,
        out_trace=display_output_path(output_dir / "minimized_trace.json", root=root) if output_dir else "",
        symbols_path=symbols_path,
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
        changed_files=changed_files,
        symbols=symbols,
        symptom=symptom,
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
            traces=traces,
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
        "input_traces": list(traces),
        "changed_files": list(changed_files),
        "symbols": list(symbols),
        "watch_symbols": list(watch_symbols),
        "rules": list(rules),
        "addresses": list(addresses),
        "symptom": symptom,
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
            "commands": collect_report_commands(data)[:24],
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
        "command_count",
        "timeline_event_count",
        "graph_node_count",
    )
    return {key: data[key] for key in keys if key in data}


def collect_report_commands(data: dict[str, Any]) -> list[str]:
    commands: list[str] = []
    add_strings(commands, data.get("commands"))
    add_strings(commands, data.get("runnable_commands"))
    add_strings(commands, data.get("blocked_commands"))
    add_strings(commands, data.get("materialization_commands"))
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
