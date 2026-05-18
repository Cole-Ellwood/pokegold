from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .coverage import load_traces
from .expect import (
    EVENT_MATCH_FIELDS,
    base_label,
    collect_evidence,
    evaluate_expectation,
    input_expectations,
    load_expectation_files,
    normalize_expectations,
    parse_cli_expectation,
    string_items,
)
from .input_log import BUTTON_ALIASES, parse_input_log
from .localize import dict_items, normalize_path
from .provenance import display_path, parse_symbol_table, resolve_path
from .reporting import load_reports
from .testgen import suggest_tests
from .trace_index import build_symbol_address_index, extract_trace_events, finalize_events
from .workflow import command_address_arg, command_is_runnable, execute_step


BOSS_AI_SYMBOL_HINTS = (
    "BossAI_",
    "wEnemyAIMoveScores",
)
DAMAGE_SYMBOL_HINTS = (
    "wCurDamage",
    "BattleCommand_Damage",
    "BattleCommand_Stab",
)
CONTENT_SOURCE_ROOTS = (
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
SCENARIO_ID_KEYS = {"id", "scenario_id", "capture_id", "trace_id"}
BUG_ID_KEYS = {"bug", "bug_id", "known_bug"}
SURFACE_KEYWORDS = {
    "damage": ("damage", "hp", "stab", "type", "weather", "held item", "badge"),
    "boss_ai": ("boss", "ai", "selector", "score", "switch", "policy"),
}
CONTEXT_LIST_KEYS = ("prelude", "frames", "context", "events")


def build_minimization_plan(
    *,
    reports: tuple[str, ...] = (),
    traces: tuple[str, ...] = (),
    input_logs: tuple[str, ...] = (),
    scenarios: tuple[str, ...] = (),
    scenario_ids: tuple[str, ...] = (),
    bug_ids: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    events: tuple[str, ...] = (),
    rules: tuple[str, ...] = (),
    addresses: tuple[str, ...] = (),
    source_files: tuple[str, ...] = (),
    expectations: tuple[str, ...] = (),
    expectation_files: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    symptom: str = "",
    out_scenarios: str = "",
    out_trace: str = "",
    out_input_log: str = "",
    out_state_report: str = "",
    execute_state_patches: bool = False,
    execute_semantic_reducers: bool = False,
    max_semantic_reducer_commands: int = 8,
    semantic_reducer_timeout_seconds: int = 600,
    symbols_path: str = "pokegold.sym",
    max_scenarios: int = 20,
    max_trace_records: int = 200,
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    loaded_traces, trace_errors = load_traces(traces=traces, root=root)
    loaded_input_logs, input_log_errors = load_input_log_files(
        input_logs=input_logs,
        root=root,
    )
    loaded_scenarios, scenario_errors = load_scenario_files(
        scenarios=scenarios,
        root=root,
    )
    report_scenarios = scenario_sources_from_reports(loaded_reports)
    scenario_sources = [*loaded_scenarios, *report_scenarios]
    signals = collect_minimization_signals(
        loaded_reports=loaded_reports,
        loaded_scenarios=scenario_sources,
        scenario_ids=scenario_ids,
        bug_ids=bug_ids,
        symbols=symbols,
        changed_files=changed_files,
        symptom=symptom,
    )
    selected_ids = list(scenario_ids) if scenario_ids else select_scenario_ids(signals, limit=max_scenarios)
    selected_rows = select_scenarios(scenario_sources, selected_ids=selected_ids)
    selected_source_files = tuple(
        unique_list(
            [
                *source_files_from_scenarios(selected_rows),
                *sorted(ids_by_type(signals, "file")),
            ]
        )
    )
    subset_output = write_scenario_subset(
        selected_rows=selected_rows,
        out_scenarios=out_scenarios,
        root=root,
    )
    precondition_minimization = build_precondition_minimization(
        scenario_sources=scenario_sources,
        selected_ids=selected_ids,
    )
    state_patch_minimization = build_state_patch_minimization(
        loaded_reports=loaded_reports,
        reports=reports,
        expectations=expectations,
        expectation_files=expectation_files,
        symbols=symbols,
        events=events,
        rules=rules,
        addresses=addresses,
        source_files=source_files,
        out_state_report=out_state_report,
        execute_state_patches=execute_state_patches,
        execute_semantic_reducers=execute_semantic_reducers,
        max_semantic_reducer_commands=max_semantic_reducer_commands,
        semantic_reducer_timeout_seconds=semantic_reducer_timeout_seconds,
        symbols_path=symbols_path,
        root=root,
    )
    evidence_minimization = build_evidence_minimization(
        loaded_traces=loaded_traces,
        loaded_reports=loaded_reports,
        reports=reports,
        expectations=expectations,
        expectation_files=expectation_files,
        symbols=symbols,
        events=events,
        rules=rules,
        addresses=addresses,
        source_files=source_files,
        out_trace=out_trace,
        symbols_path=symbols_path,
        max_trace_records=max_trace_records,
        root=root,
    )
    input_log_minimization = build_input_log_minimization(
        loaded_input_logs=loaded_input_logs,
        reports=reports,
        expectations=expectations,
        expectation_files=expectation_files,
        events=events,
        out_input_log=out_input_log,
        root=root,
    )
    surfaces = infer_surfaces(
        symbols=symbols,
        changed_files=changed_files,
        scenario_source_files=selected_source_files,
        symptom=symptom,
        signals=signals,
    )
    steps = build_minimization_steps(
        surfaces=surfaces,
        scenario_paths=[item["source"] for item in scenario_sources],
        selected_ids=selected_ids,
        bug_ids=tuple(sorted({*bug_ids, *ids_by_type(signals, "bug")})),
        symbols=symbols,
        changed_files=changed_files,
        scenario_source_files=selected_source_files,
        symptom=symptom,
        subset_path=subset_output.get("path", ""),
    )
    steps.extend(build_precondition_minimization_steps(precondition_minimization))
    steps.extend(build_state_patch_minimization_steps(state_patch_minimization))
    steps.extend(build_evidence_minimization_steps(evidence_minimization))
    steps.extend(build_input_log_minimization_steps(input_log_minimization))
    errors = [
        *report_errors,
        *trace_errors,
        *input_log_errors,
        *scenario_errors,
        *subset_output.get("errors", []),
        *state_patch_minimization.get("errors", []),
        *evidence_minimization.get("errors", []),
        *input_log_minimization.get("errors", []),
    ]
    return {
        "schema_version": 1,
        "kind": "unified_debugger_minimization_plan",
        "root": str(root),
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
        "reports": [item["source"] for item in loaded_reports],
        "traces": [item["source"] for item in loaded_traces],
        "input_logs": [item["source"] for item in loaded_input_logs],
        "scenarios": [item["source"] for item in scenario_sources],
        "scenario_count": sum(len(item["records"]) for item in scenario_sources),
        "report_scenario_count": sum(len(item["records"]) for item in report_scenarios),
        "selected_scenario_count": len(selected_rows),
        "selected_scenario_ids": selected_ids,
        "bug_ids": sorted({*bug_ids, *ids_by_type(signals, "bug")}),
        "surfaces": surfaces,
        "signals": signals[:120],
        "steps": steps,
        "commands": unique_list(step["command"] for step in steps),
        "runnable_commands": unique_list(step["command"] for step in steps if step["runnable"]),
        "blocked_commands": unique_list(step["command"] for step in steps if not step["runnable"]),
        "subset_output": subset_output,
        "precondition_minimization": precondition_minimization,
        "state_patch_minimization": state_patch_minimization,
        "evidence_minimization": evidence_minimization,
        "input_log_minimization": input_log_minimization,
        "known_limits": [
            "This command can extract scenario subsets, minimize content-state or explicit generic state-space WRAM patch sets against explicit expectations, minimize arbitrary trace evidence, and reduce supported text input logs while preserving retained input timing; deeper semantic ddmin still runs in focused subsystem tools where they exist.",
            "Placeholder commands need a concrete generated scenario, bug id, save state, or ROM materialization artifact before execution.",
        ],
    }


def load_scenario_files(
    *,
    scenarios: tuple[str, ...],
    root: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    loaded: list[dict[str, Any]] = []
    errors: list[str] = []
    for raw_path in scenarios:
        path = resolve_path(raw_path, root=root)
        source = display_path(path, root=root)
        if not path.exists():
            errors.append(f"missing scenario file: {raw_path}")
            continue
        try:
            records = load_scenario_records(path)
        except json.JSONDecodeError as exc:
            errors.append(f"{raw_path}: invalid JSON: {exc.msg}")
            continue
        except OSError as exc:
            errors.append(f"{raw_path}: {exc}")
            continue
        loaded.append(
            {
                "path": path,
                "source": source,
                "records": records,
                "ids": [scenario_id_for(record) for record in records if scenario_id_for(record)],
            }
        )
    return loaded, errors


def load_input_log_files(
    *,
    input_logs: tuple[str, ...],
    root: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    loaded: list[dict[str, Any]] = []
    errors: list[str] = []
    next_frame = 0
    for raw_path in input_logs:
        path = resolve_path(raw_path, root=root)
        source = display_path(path, root=root)
        if not path.exists():
            errors.append(f"missing input log file: {raw_path}")
            continue
        parsed_events, parsed_errors = parse_input_log(path, start_frame=next_frame)
        errors.extend(f"{raw_path}: {error}" for error in parsed_errors)
        if parsed_events:
            next_frame = max(int(event.get("end_frame", next_frame)) for event in parsed_events)
        loaded.append(
            {
                "path": path,
                "source": source,
                "input_path": raw_path,
                "events": parsed_events,
                "errors": parsed_errors,
            }
        )
    return loaded, errors


def load_scenario_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        records = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if isinstance(item, dict):
                records.append(item)
        return records
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def scenario_sources_from_reports(loaded_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for loaded in loaded_reports:
        records = scenario_records_from_report(loaded["data"])
        if not records:
            continue
        sources.append(
            {
                "path": loaded["path"],
                "source": f"{loaded['source']}#scenarios",
                "records": records,
                "ids": [scenario_id_for(record) for record in records if scenario_id_for(record)],
            }
        )
    return sources


def scenario_records_from_report(report: Any) -> list[dict[str, Any]]:
    if not isinstance(report, dict):
        return []
    if isinstance(report.get("scenarios"), list):
        return [item for item in report["scenarios"] if is_report_scenario_record(item)]
    if is_report_scenario_record(report):
        return [report]
    return []


def is_report_scenario_record(value: Any) -> bool:
    return isinstance(value, dict) and bool(scenario_id_for(value)) and (
        "scenario" in str(value.get("kind", "")).lower()
        or bool(value.get("scenario_type"))
        or str(value.get("family", "")) in {"content_static", "damage", "boss_ai"}
    )


def collect_minimization_signals(
    *,
    loaded_reports: list[dict[str, Any]],
    loaded_scenarios: list[dict[str, Any]],
    scenario_ids: tuple[str, ...],
    bug_ids: tuple[str, ...],
    symbols: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for scenario_id in scenario_ids:
        signals.append(signal("explicit_scenario", "scenario", scenario_id, 100, "input"))
    for bug_id in bug_ids:
        signals.append(signal("explicit_bug", "bug", bug_id, 100, "input"))
    for symbol in symbols:
        signals.append(signal("explicit_symbol", "symbol", symbol, 60, "input"))
    for path in changed_files:
        signals.append(signal("explicit_file", "file", normalize_path(path), 60, "input"))
    if symptom:
        signals.append(signal("symptom", "note", symptom, 40, "input"))

    for loaded in loaded_scenarios:
        for scenario_id in loaded["ids"]:
            signals.append(signal("scenario_file", "scenario", scenario_id, 40, loaded["source"]))
    for loaded in loaded_reports:
        signals.extend(signals_from_report(loaded["data"], source=loaded["source"]))
    return merge_signals(signals)


def signals_from_report(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    walk_report_for_ids(report, source=source, out=out, context={})
    for record in scenario_records_from_report(report):
        surface = str(record.get("surface") or record.get("family") or record.get("scenario_type") or "")
        if surface:
            out.append(signal("report_scenario_surface", "surface", surface, 75, source))
    kind = report.get("kind", "")
    if kind == "unified_debugger_coverage_report":
        for target in dict_items(report.get("uncovered_targets")):
            value = str(target.get("id", ""))
            if value:
                out.append(signal("coverage_gap", str(target.get("type", "target")), value, 70, source))
    if kind == "unified_debugger_localization_plan":
        for candidate in dict_items(report.get("candidates"))[:10]:
            out.append(
                signal(
                    "localization_candidate",
                    str(candidate.get("type", "candidate")),
                    str(candidate.get("id", "")),
                    min(90, int(candidate.get("score", 0)) // 10 + 30),
                    source,
                )
            )
    if kind == "unified_debugger_ranked_findings":
        for finding in dict_items(report.get("findings"))[:20]:
            out.append(
                signal(
                    "ranked_finding",
                    "note",
                    str(finding.get("title", "")),
                    int(finding.get("severity", 40)),
                    source,
                )
            )
    if kind == "unified_debugger_content_state_materialization":
        for materialization in dict_items(report.get("materializations")):
            source_file = normalize_path(str(materialization.get("source_file", "")))
            if source_file:
                out.append(signal("content_state_source", "file", source_file, 65, source))
            for patch in dict_items(materialization.get("patches")):
                symbol = str(patch.get("symbol", ""))
                if symbol:
                    out.append(signal("content_state_patch", "symbol", symbol, 55, source))
    return [item for item in out if item["value"]]


def walk_report_for_ids(
    data: Any,
    *,
    source: str,
    out: list[dict[str, Any]],
    context: dict[str, Any],
) -> None:
    if isinstance(data, dict):
        local_context = dict(context)
        if isinstance(data.get("scenario_id"), str):
            local_context["scenario_id"] = data["scenario_id"]
        for key, value in data.items():
            if key in SCENARIO_ID_KEYS and isinstance(value, str) and (key != "id" or is_scenario_record(data, value)):
                out.append(signal(f"report_{key}", "scenario", value, 70, source))
            elif key in BUG_ID_KEYS and isinstance(value, str):
                out.append(signal(f"report_{key}", "bug", value, 80, source))
            elif key in {"watch", "symbol", "query", "resolved"} and isinstance(value, str):
                out.append(signal(f"report_{key}", "symbol", value, 35, source))
            walk_report_for_ids(value, source=source, out=out, context=local_context)
    elif isinstance(data, list):
        for item in data:
            walk_report_for_ids(item, source=source, out=out, context=context)


def select_scenario_ids(signals: list[dict[str, Any]], *, limit: int) -> list[str]:
    scores: dict[str, int] = {}
    for item in signals:
        if item["kind"] != "scenario":
            continue
        scores[item["value"]] = scores.get(item["value"], 0) + int(item["weight"])
    return [
        scenario_id
        for scenario_id, _score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def select_scenarios(
    loaded_scenarios: list[dict[str, Any]],
    *,
    selected_ids: list[str],
) -> list[dict[str, Any]]:
    if not selected_ids:
        return []
    selected = set(selected_ids)
    out = []
    for loaded in loaded_scenarios:
        for record in loaded["records"]:
            if scenario_id_for(record) in selected:
                out.append(record)
    return out


def source_files_from_scenarios(records: list[dict[str, Any]]) -> list[str]:
    return unique_list(
        normalize_path(str(record.get("source_file", "")))
        for record in records
        if record.get("source_file")
    )


def write_scenario_subset(
    *,
    selected_rows: list[dict[str, Any]],
    out_scenarios: str,
    root: Path,
) -> dict[str, Any]:
    if not out_scenarios and not selected_rows:
        return {"path": "", "written": False, "record_count": 0, "errors": []}
    auto_path = not bool(out_scenarios)
    target = out_scenarios or default_scenario_subset_path(selected_rows)
    path = resolve_path(target, root=root)
    if not selected_rows:
        return {
            "path": display_path(path, root=root),
            "written": False,
            "record_count": 0,
            "auto": auto_path,
            "errors": ["no selected scenarios available to write"],
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in selected_rows),
        encoding="utf-8",
        newline="\n",
    )
    return {
        "path": display_path(path, root=root),
        "written": True,
        "record_count": len(selected_rows),
        "auto": auto_path,
        "errors": [],
    }


def default_scenario_subset_path(selected_rows: list[dict[str, Any]]) -> str:
    scenario_id = (safe_name(scenario_id_for(selected_rows[0])) or "selected") if selected_rows else "selected"
    return f".local/tmp/debugger_minimized_candidates_{scenario_id}.jsonl"


def build_precondition_minimization(
    *,
    scenario_sources: list[dict[str, Any]],
    selected_ids: list[str],
) -> dict[str, Any]:
    selected = set(selected_ids)
    all_preconditions = [
        precondition
        for source in scenario_sources
        for record in source["records"]
        for precondition in state_preconditions_from_scenario(record, source=source["source"])
    ]
    selected_preconditions = [
        precondition
        for precondition in all_preconditions
        if not selected or precondition["scenario_id"] in selected
    ]
    selected_scenario_ids = unique_list(precondition["scenario_id"] for precondition in selected_preconditions)
    expectations = precondition_expectations(selected_preconditions)
    return {
        "attempted": bool(all_preconditions),
        "scenario_count": len(unique_list(precondition["scenario_id"] for precondition in all_preconditions)),
        "precondition_count": len(all_preconditions),
        "selected_scenario_ids": selected_scenario_ids,
        "selected_precondition_count": len(selected_preconditions),
        "selected_preconditions": selected_preconditions[:40],
        "expectations": expectations[:80],
        "known_limits": [
            "Precondition minimization preserves the smallest selected content scenario state requirements; it does not synthesize a save state by itself.",
        ],
    }


def state_preconditions_from_scenario(record: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    scenario_id = scenario_id_for(record)
    if not scenario_id:
        return []
    preconditions = []
    for index, precondition in enumerate(dict_items(record.get("state_preconditions")), 1):
        values = precondition.get("values") if isinstance(precondition.get("values"), dict) else {}
        source_file = normalize_path(
            str(
                precondition.get("source_file")
                or record.get("source_file")
                or values.get("source_file")
                or ""
            )
        )
        preconditions.append(
            {
                "id": str(precondition.get("id") or f"{scenario_id}_precondition_{index}"),
                "scenario_id": scenario_id,
                "scenario_type": str(record.get("scenario_type", precondition.get("scenario_type", ""))),
                "kind": str(precondition.get("kind", "")),
                "source_file": source_file,
                "values": dict(values),
                "watch_symbols": unique_list(string_items(precondition.get("watch_symbols"))),
                "source": source,
            }
        )
    return preconditions


def precondition_expectations(preconditions: list[dict[str, Any]]) -> list[str]:
    expectations: list[str] = []
    for precondition in preconditions:
        scenario_id = precondition["scenario_id"]
        kind = precondition["kind"]
        expectations.append(f"scenario={scenario_id}")
        if kind:
            expectations.append(f"precondition={kind},scenario={scenario_id}")
        for symbol in precondition.get("watch_symbols", [])[:4]:
            if kind:
                expectations.append(f"precondition={kind},scenario={scenario_id},symbol={symbol}")
    return unique_list(expectations)


def build_state_patch_minimization(
    *,
    loaded_reports: list[dict[str, Any]],
    reports: tuple[str, ...],
    expectations: tuple[str, ...],
    expectation_files: tuple[str, ...],
    symbols: tuple[str, ...],
    events: tuple[str, ...],
    rules: tuple[str, ...],
    addresses: tuple[str, ...],
    source_files: tuple[str, ...],
    out_state_report: str,
    execute_state_patches: bool,
    execute_semantic_reducers: bool,
    max_semantic_reducer_commands: int,
    semantic_reducer_timeout_seconds: int,
    symbols_path: str,
    root: Path,
) -> dict[str, Any]:
    views = [
        view
        for loaded in loaded_reports
        if isinstance(loaded.get("data"), dict)
        for view in state_patch_views_from_report(loaded)
    ]
    views = [view for view in views if view["patches"]]
    if not views:
        return {
            "attempted": False,
            "reason": "no content-state or explicit generic state-space reports with patches were supplied",
            "report_count": len(loaded_reports),
            "content_state_report_count": 0,
            "state_space_report_count": 0,
            "expectation_count": 0,
            "errors": [],
        }

    file_expectations, expectation_errors = load_expectation_files(
        expectation_files=expectation_files,
        root=root,
    )
    all_expectations = normalize_expectations(
        [
            *file_expectations,
            *[parse_cli_expectation(raw) for raw in expectations],
            *input_expectations(
                symbols=symbols,
                events=events,
                rules=rules,
                addresses=addresses,
                source_files=source_files,
            ),
        ]
    )
    if not all_expectations:
        return {
            "attempted": False,
            "reason": "no --expect, --expect-file, --symbol, --event, --rule, --address, or --source-file predicate was supplied",
            "report_count": len(loaded_reports),
            "content_state_report_count": count_state_patch_views(views, "content_state"),
            "state_space_report_count": count_state_patch_views(views, "generic_state_space"),
            "expectation_count": 0,
            "errors": expectation_errors,
            "suggested_expectations": state_patch_suggested_expectations(views),
        }

    semantic_reducer_budget = {"remaining": max(0, max_semantic_reducer_commands)}
    results = [
        minimize_state_patch_view(
            view,
            expectations=all_expectations,
            execute_state_patches=execute_state_patches,
            execute_semantic_reducers=execute_semantic_reducers,
            semantic_reducer_budget=semantic_reducer_budget,
            semantic_reducer_timeout_seconds=semantic_reducer_timeout_seconds,
            symbols_path=symbols_path,
            root=root,
        )
        for view in views
    ]
    preserved = [result for result in results if result.get("preserved")]
    best = min(
        preserved,
        key=lambda item: (int(item.get("minimized_patch_count", 0)), str(item.get("source", ""))),
        default=None,
    )
    output = write_minimized_state_report(
        best=best,
        out_state_report=out_state_report,
        root=root,
    )
    errors = unique_list([*expectation_errors, *output.get("errors", [])])
    if execute_state_patches and best is None:
        errors = unique_list(
            [
                *errors,
                *[
                    error
                    for result in results
                    for error in string_items(result.get("execution_errors"))
                ],
            ]
        )
    preservation_errors = list(errors)
    best_data = best.get("data") if isinstance(best, dict) and isinstance(best.get("data"), dict) else {}
    watch_symbols = candidate_watch_symbols(data=best_data, expectations=all_expectations) if best_data else expectation_watch_symbols(all_expectations)
    watch_addresses = candidate_watch_addresses(data=best_data, expectations=all_expectations) if best_data else []
    watch_size = candidate_watch_size(best_data, expectations=all_expectations) if best_data else expectation_watch_size(all_expectations)
    scenario_ids = string_items(best.get("scenario_ids")) if best else []
    symbols = string_items(best.get("symbols")) if best else []
    source_files = string_items(best.get("source_files")) if best else []
    source_symbols = known_source_symbols(
        symbols,
        symbols_path=symbols_path,
        root=root,
    )
    source_mems = string_items(best.get("source_mems")) if best else []
    semantic_reducer_routes = state_patch_semantic_reducer_routes(
        out_report=str(output.get("path", "")),
        source=str(best.get("source", "")) if best else "",
        scenario_ids=scenario_ids,
        symbols=symbols,
        source_files=source_files,
        source_symbols=source_symbols,
        source_mems=source_mems,
        watch_symbols=watch_symbols,
        watch_addresses=watch_addresses,
        watch_size=watch_size,
        expectations=all_expectations,
        symbols_path=symbols_path,
    )
    semantic_reducer_commands = unique_list(
        command
        for route in semantic_reducer_routes
        for command in string_items(route.get("commands"))
    )
    semantic_reducer_execution = execute_semantic_reducer_routes(
        semantic_reducer_routes,
        execute=execute_semantic_reducers,
        max_commands=semantic_reducer_budget["remaining"] if execute_semantic_reducers else max_semantic_reducer_commands,
        timeout_seconds=semantic_reducer_timeout_seconds,
        root=root,
    )
    if execute_semantic_reducers:
        semantic_reducer_budget["remaining"] = max(
            0,
            semantic_reducer_budget["remaining"] - int(semantic_reducer_execution.get("step_count", 0)),
        )
    if execute_semantic_reducers:
        errors = unique_list([*errors, *string_items(semantic_reducer_execution.get("errors"))])
    commands = state_patch_minimization_commands(
        out_report=str(output.get("path", "")),
        source=str(best.get("source", "")) if best else "",
        scenario_ids=scenario_ids,
        expectations=all_expectations,
        source_symbols=source_symbols,
        source_mems=source_mems,
        watch_symbols=watch_symbols,
        watch_addresses=watch_addresses,
        watch_size=watch_size,
        symbols_path=symbols_path,
    )
    commands = unique_list([*commands, *semantic_reducer_commands])
    minimized_save_state_delta = minimized_save_state_delta_for_result(best)
    return {
        "attempted": True,
        "preserved": best is not None and not preservation_errors,
        "report_count": len(loaded_reports),
        "content_state_report_count": count_state_patch_views(views, "content_state"),
        "state_space_report_count": count_state_patch_views(views, "generic_state_space"),
        "expectation_count": len(all_expectations),
        "execute_state_patches": execute_state_patches,
        "execution_attempt_count": sum(int(result.get("execution_attempt_count", 0)) for result in results),
        "executed_candidate_count": sum(int(result.get("executed_candidate_count", 0)) for result in results),
        "semantic_watch_rerun_attempt_count": sum(int(result.get("semantic_watch_rerun_attempt_count", 0)) for result in results),
        "semantic_watch_rerun_count": sum(int(result.get("semantic_watch_rerun_count", 0)) for result in results),
        "semantic_replay_rerun_attempt_count": sum(int(result.get("semantic_replay_rerun_attempt_count", 0)) for result in results),
        "semantic_replay_rerun_count": sum(int(result.get("semantic_replay_rerun_count", 0)) for result in results),
        "semantic_reducer_candidate_attempt_count": sum(int(result.get("semantic_reducer_candidate_attempt_count", 0)) for result in results),
        "semantic_reducer_candidate_execution_count": sum(int(result.get("semantic_reducer_candidate_execution_count", 0)) for result in results),
        "semantic_reducer_candidate_failed_count": sum(int(result.get("semantic_reducer_candidate_failed_count", 0)) for result in results),
        "expectations": [
            {
                "id": str(expectation.get("id", "")),
                "type": str(expectation.get("type", "")),
                "description": expectation_cli(expectation),
            }
            for expectation in all_expectations
        ],
        "source": str(best.get("source", "")) if best else "",
        "original_patch_count": int(best.get("original_patch_count", 0)) if best else 0,
        "minimized_patch_count": int(best.get("minimized_patch_count", 0)) if best else 0,
        "removed_patch_count": int(best.get("removed_patch_count", 0)) if best else 0,
        "scenario_ids": scenario_ids,
        "symbols": symbols,
        "source_files": source_files,
        "source_symbols": source_symbols,
        "source_mems": source_mems,
        "minimized_save_state_delta": minimized_save_state_delta,
        "watch_symbols": watch_symbols,
        "watch_addresses": watch_addresses,
        "watch_size": watch_size,
        "out_report": output.get("path", ""),
        "written": bool(output.get("written")),
        "semantic_reducer_surfaces": state_patch_semantic_surfaces(
            symbols=symbols,
            source_files=source_files,
            source_symbols=source_symbols,
            source_mems=source_mems,
            watch_symbols=watch_symbols,
            watch_addresses=watch_addresses,
            expectations=all_expectations,
        ),
        "semantic_reducer_route_count": len(semantic_reducer_routes),
        "semantic_reducer_routes": semantic_reducer_routes,
        "semantic_reducer_commands": semantic_reducer_commands,
        "execute_semantic_reducers": execute_semantic_reducers,
        "semantic_reducer_execution": semantic_reducer_execution,
        "semantic_reducer_command_budget": max(0, max_semantic_reducer_commands),
        "semantic_reducer_command_budget_remaining": semantic_reducer_budget["remaining"],
        "result_count": len(results),
        "results": [public_state_patch_minimize_result(result) for result in results[:12]],
        "commands": commands,
        "errors": errors,
        "known_limits": [
            "Patch minimization preserves explicit expectations over content-state or generic state-space report evidence; with --execute-state-patches, content-state and explicit generic state-space candidate subsets are materialized before their expectations are evaluated, replay is rebuilt from each candidate state, and event/value expectations rerun watch evidence from each candidate state.",
            "Without a state-patch or similarly specific predicate, a broad expectation such as no-errors can minimize away behaviorally necessary state.",
        ],
    }


def state_patch_views_from_report(loaded: dict[str, Any]) -> list[dict[str, Any]]:
    data = loaded["data"]
    source = loaded["source"]
    if not isinstance(data, dict):
        return []
    if data.get("kind") == "unified_debugger_content_state_materialization":
        return [
            {
                "source": source,
                "data": data,
                "view_kind": "content_state",
                "patches": content_state_patch_locations(data),
            }
        ]
    return [
        {
            "source": source,
            "data": data,
            "view_kind": "generic_state_space",
            "patches": generic_state_patch_locations(data),
        }
    ]


def count_state_patch_views(views: list[dict[str, Any]], view_kind: str) -> int:
    return sum(1 for view in views if view.get("view_kind") == view_kind)


def minimize_state_patch_view(
    view: dict[str, Any],
    *,
    expectations: list[dict[str, Any]],
    execute_state_patches: bool,
    execute_semantic_reducers: bool,
    semantic_reducer_budget: dict[str, int],
    semantic_reducer_timeout_seconds: int,
    symbols_path: str,
    root: Path,
) -> dict[str, Any]:
    patch_locations = list(view["patches"])
    candidate_executions: list[dict[str, Any]] = []
    candidate_semantic_reductions: list[dict[str, Any]] = []
    symbol_by_address = symbol_address_index(symbols_path=symbols_path, root=root)

    def predicate(candidate_locations: list[dict[str, Any]]) -> bool:
        data, execution = state_patch_candidate_report(
            view,
            candidate_locations,
            execute_state_patches=execute_state_patches,
            candidate_index=len(candidate_executions) + 1,
            expectations=expectations,
            symbols_path=symbols_path,
            root=root,
        )
        if execution.get("attempted"):
            candidate_executions.append(execution)
            if not execution.get("executed"):
                return False
            if execution.get("semantic_watch_required") and not execution.get("semantic_watch_executed"):
                return False
            if execution.get("semantic_replay_required") and not execution.get("semantic_replay_executed"):
                return False
        expectations_passed = state_patch_expectations_pass(
            data,
            source=str(view["source"]),
            expectations=expectations,
            symbol_by_address=symbol_by_address,
        )
        if not expectations_passed:
            return False
        semantic_reduction = execute_candidate_semantic_reducers(
            data=data,
            source=str(view["source"]),
            locations=candidate_locations,
            original_patch_count=len(patch_locations),
            candidate_index=len(candidate_semantic_reductions) + 1,
            expectations=expectations,
            execute_semantic_reducers=execute_semantic_reducers,
            semantic_reducer_budget=semantic_reducer_budget,
            timeout_seconds=semantic_reducer_timeout_seconds,
            symbols_path=symbols_path,
            root=root,
        )
        if semantic_reduction.get("attempted"):
            candidate_semantic_reductions.append(semantic_reduction)
            if int(semantic_reduction.get("failed_count", 0)):
                return False
        return True

    initial_passed = predicate(patch_locations)
    minimized = greedy_minimize_items(patch_locations, predicate=predicate, min_items=0) if initial_passed else patch_locations
    minimized_data = None
    final_preserved = initial_passed
    if initial_passed:
        minimized_data, final_execution = state_patch_candidate_report(
            view,
            minimized,
            execute_state_patches=execute_state_patches,
            candidate_index=len(candidate_executions) + 1,
            expectations=expectations,
            symbols_path=symbols_path,
            root=root,
        )
        if final_execution.get("attempted"):
            candidate_executions.append(final_execution)
            final_preserved = bool(final_execution.get("executed"))
            if final_execution.get("semantic_watch_required") and not final_execution.get("semantic_watch_executed"):
                final_preserved = False
            if final_execution.get("semantic_replay_required") and not final_execution.get("semantic_replay_executed"):
                final_preserved = False
        if final_preserved:
            final_preserved = state_patch_expectations_pass(
                minimized_data,
                source=str(view["source"]),
                expectations=expectations,
                symbol_by_address=symbol_by_address,
            )
        if final_preserved:
            final_semantic_reduction = execute_candidate_semantic_reducers(
                data=minimized_data,
                source=str(view["source"]),
                locations=minimized,
                original_patch_count=len(patch_locations),
                candidate_index=len(candidate_semantic_reductions) + 1,
                expectations=expectations,
                execute_semantic_reducers=execute_semantic_reducers,
                semantic_reducer_budget=semantic_reducer_budget,
                timeout_seconds=semantic_reducer_timeout_seconds,
                symbols_path=symbols_path,
                root=root,
            )
            if final_semantic_reduction.get("attempted"):
                candidate_semantic_reductions.append(final_semantic_reduction)
                if int(final_semantic_reduction.get("failed_count", 0)):
                    final_preserved = False
    return {
        "source": view["source"],
        "view_kind": view.get("view_kind", "content_state"),
        "preserved": bool(final_preserved),
        "execution_mode": "emulator" if any(item.get("attempted") for item in candidate_executions) else "evidence",
        "execution_attempt_count": len([item for item in candidate_executions if item.get("attempted")]),
        "executed_candidate_count": len([item for item in candidate_executions if item.get("executed")]),
        "semantic_watch_rerun_attempt_count": len([item for item in candidate_executions if item.get("semantic_watch_required")]),
        "semantic_watch_rerun_count": len([item for item in candidate_executions if item.get("semantic_watch_executed")]),
        "semantic_replay_rerun_attempt_count": len([item for item in candidate_executions if item.get("semantic_replay_required")]),
        "semantic_replay_rerun_count": len([item for item in candidate_executions if item.get("semantic_replay_executed")]),
        "semantic_reducer_candidate_attempt_count": len([item for item in candidate_semantic_reductions if item.get("attempted")]),
        "semantic_reducer_candidate_execution_count": len([item for item in candidate_semantic_reductions if item.get("executed")]),
        "semantic_reducer_candidate_failed_count": len([item for item in candidate_semantic_reductions if int(item.get("failed_count", 0))]),
        "execution_errors": unique_list(
            [
                *[
                    error
                    for item in candidate_executions
                    for error in string_items(item.get("errors"))
                ],
                *[
                    error
                    for item in candidate_semantic_reductions
                    for error in string_items(item.get("errors"))
                ],
            ]
        ),
        "original_patch_count": len(patch_locations),
        "minimized_patch_count": len(minimized) if final_preserved else 0,
        "removed_patch_count": len(patch_locations) - len(minimized) if final_preserved else 0,
        "scenario_ids": state_patch_scenario_ids(minimized_data or view["data"], minimized if final_preserved else patch_locations),
        "source_files": state_patch_source_files(minimized_data or view["data"], minimized if final_preserved else patch_locations),
        "symbols": (
            unique_list(str(location.get("symbol", "")) for location in minimized if location.get("symbol"))
            if final_preserved else []
        ),
        "source_mems": state_patch_source_mems(minimized) if final_preserved else [],
        "semantic_reducer_candidates": candidate_semantic_reductions[:12],
        "data": minimized_data if final_preserved else None,
    }


def execute_candidate_semantic_reducers(
    *,
    data: dict[str, Any],
    source: str,
    locations: list[dict[str, Any]],
    original_patch_count: int,
    candidate_index: int,
    expectations: list[dict[str, Any]],
    execute_semantic_reducers: bool,
    semantic_reducer_budget: dict[str, int],
    timeout_seconds: int,
    symbols_path: str,
    root: Path,
) -> dict[str, Any]:
    if not execute_semantic_reducers:
        return {"attempted": False, "reason": "semantic reducer execution was not requested"}
    if len(locations) >= original_patch_count:
        return {"attempted": False, "reason": "candidate did not remove any state patches"}
    remaining = max(0, int(semantic_reducer_budget.get("remaining", 0)))
    if remaining <= 0:
        return {
            "attempted": False,
            "reason": "semantic reducer command budget exhausted",
            "candidate_index": candidate_index,
            "removed_patch_count": original_patch_count - len(locations),
        }
    report_output = write_candidate_semantic_reducer_report(
        data=data,
        source=source,
        candidate_index=candidate_index,
        root=root,
    )
    if report_output.get("errors"):
        return {
            "attempted": True,
            "executed": False,
            "candidate_index": candidate_index,
            "removed_patch_count": original_patch_count - len(locations),
            "report": report_output.get("path", ""),
            "route_count": 0,
            "step_count": 0,
            "failed_count": 0,
            "errors": string_items(report_output.get("errors")),
        }
    symbols = unique_list(str(location.get("symbol", "")) for location in locations if location.get("symbol"))
    source_files = state_patch_source_files(data, locations)
    source_symbols = known_source_symbols(
        symbols,
        symbols_path=symbols_path,
        root=root,
    )
    source_mems = state_patch_source_mems(locations)
    watch_symbols = candidate_watch_symbols(data=data, expectations=expectations)
    watch_addresses = candidate_watch_addresses(data=data, expectations=expectations)
    watch_size = candidate_watch_size(data, expectations=expectations)
    routes = state_patch_semantic_reducer_routes(
        out_report=str(report_output.get("path", "")),
        source=source,
        scenario_ids=state_patch_scenario_ids(data, locations),
        symbols=symbols,
        source_files=source_files,
        source_symbols=source_symbols,
        source_mems=source_mems,
        watch_symbols=watch_symbols,
        watch_addresses=watch_addresses,
        watch_size=watch_size,
        expectations=expectations,
        symbols_path=symbols_path,
    )
    execution = execute_semantic_reducer_routes(
        routes,
        execute=True,
        max_commands=remaining,
        timeout_seconds=timeout_seconds,
        root=root,
    )
    semantic_reducer_budget["remaining"] = max(
        0,
        remaining - int(execution.get("step_count", 0)),
    )
    return {
        **execution,
        "candidate_index": candidate_index,
        "removed_patch_count": original_patch_count - len(locations),
        "report": report_output.get("path", ""),
    }


def write_candidate_semantic_reducer_report(
    *,
    data: dict[str, Any],
    source: str,
    candidate_index: int,
    root: Path,
) -> dict[str, Any]:
    source_name = safe_name(Path(source).stem or source or "state_patch")
    path = root / ".local" / "tmp" / f"debugger_semantic_reducer_candidate_{source_name}_{candidate_index:03d}.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2, sort_keys=True),
            encoding="utf-8",
            newline="\n",
        )
    except OSError as exc:
        return {"path": display_path(path, root=root), "written": False, "errors": [str(exc)]}
    return {"path": display_path(path, root=root), "written": True, "errors": []}


def state_patch_expectations_pass(
    data: dict[str, Any],
    *,
    source: str,
    expectations: list[dict[str, Any]],
    symbol_by_address: dict[str, str] | None = None,
) -> bool:
    trace_events = finalize_events(
        extract_trace_events(
            data,
            source=source,
            symbol_by_address=symbol_by_address or {},
        )
    )
    evidence = collect_evidence(
        loaded_reports=[{"source": source, "data": data}],
        loaded_sources=[],
        trace_index={
            "kind": "unified_debugger_trace_index",
            "valid": True,
            "events": trace_events,
            "errors": [],
            "warnings": [],
        },
    )
    results = [evaluate_expectation(expectation, evidence=evidence) for expectation in expectations]
    return bool(results) and all(result["status"] == "passed" for result in results)


def state_patch_candidate_report(
    view: dict[str, Any],
    locations: list[dict[str, Any]],
    *,
    execute_state_patches: bool,
    candidate_index: int,
    expectations: list[dict[str, Any]],
    symbols_path: str,
    root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    data = state_patch_report_with_patch_locations(view, locations)
    if not execute_state_patches:
        return data, {"attempted": False}
    if view.get("view_kind") not in {"content_state", "generic_state_space"}:
        return data, {"attempted": False}
    if data.get("kind") != "unified_debugger_state_space":
        if view.get("view_kind") == "content_state":
            return execute_content_state_patch_candidate(
                data,
                source=str(view.get("source", "")),
                candidate_index=candidate_index,
                expectations=expectations,
                symbols_path=symbols_path,
                root=root,
            )
        return data, {"attempted": False, "reason": "only content-state and unified_debugger_state_space reports can be execution-minimized"}
    return execute_generic_state_patch_candidate(
        data,
        source=str(view.get("source", "")),
        candidate_index=candidate_index,
        expectations=expectations,
        symbols_path=symbols_path,
        root=root,
    )


def execute_content_state_patch_candidate(
    data: dict[str, Any],
    *,
    source: str,
    candidate_index: int,
    expectations: list[dict[str, Any]],
    symbols_path: str,
    root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    from .content_state import execute_materialization
    from .replay import build_replay_plan
    from .runtime_watch import build_watch_report

    context, context_errors = content_state_execution_context(
        data,
        source=source,
        candidate_index=candidate_index,
        symbols_path=symbols_path,
        root=root,
    )
    if context_errors:
        return data, {
            "attempted": True,
            "executed": False,
            "candidate_index": candidate_index,
            "patch_count": sum(
                len(dict_items(materialization.get("patches")))
                for materialization in dict_items(data.get("materializations"))
            ),
            "errors": context_errors,
        }
    execution = execute_materialization(
        materializations=dict_items(data.get("materializations")),
        rom=context["rom"],
        base_state=context["base_state"],
        output_state=context["out_state"],
        execute=True,
        root=root,
    )
    out = copy.deepcopy(data)
    out["execution"] = execution_with_applied_patch_metadata(execution)
    out["executed"] = bool(execution.get("executed"))
    out["out_state"] = str(execution.get("out_state", ""))
    if isinstance(execution.get("save_state_delta"), dict):
        out["save_state_delta"] = copy.deepcopy(execution["save_state_delta"])
    out["minimized_evidence_view"] = True
    out["minimized_execution_view"] = True
    semantic_watch = execute_candidate_semantic_watch(
        data=out,
        context=context,
        expectations=expectations,
        build_watch_report_func=build_watch_report,
        root=root,
    )
    semantic_replay = execute_candidate_semantic_replay(
        data=out,
        context=context,
        expectations=expectations,
        build_replay_plan_func=build_replay_plan,
        root=root,
    )
    if semantic_watch["required"]:
        out["semantic_watch_reducer"] = {
            key: value
            for key, value in semantic_watch.items()
            if key != "report"
        }
        if isinstance(semantic_watch.get("report"), dict):
            out["watch_report"] = semantic_watch["report"]
    if semantic_replay["required"]:
        out["semantic_replay_reducer"] = {
            key: value
            for key, value in semantic_replay.items()
            if key != "report"
        }
        if isinstance(semantic_replay.get("report"), dict):
            out["replay_report"] = semantic_replay["report"]
    out.setdefault("warnings", [])
    if isinstance(out["warnings"], list):
        out["warnings"] = unique_list(
            [
                *string_items(out["warnings"]),
                "minimized content-state candidate was materialized before expectation evaluation",
                *string_items(semantic_watch.get("warnings")),
                *string_items(semantic_replay.get("warnings")),
            ]
        )
        out["warning_count"] = len(out["warnings"])
    combined_errors = unique_list(
        [
            *string_items(execution.get("errors")),
            *string_items(semantic_watch.get("errors")),
            *string_items(semantic_replay.get("errors")),
        ]
    )
    return out, {
        "attempted": True,
        "executed": bool(execution.get("executed")),
        "candidate_index": candidate_index,
        "patch_count": int(execution.get("patch_count", 0)),
        "out_state": str(execution.get("out_state", "")),
        "semantic_watch_required": bool(semantic_watch["required"]),
        "semantic_watch_executed": bool(semantic_watch["executed"]),
        "semantic_watch_symbols": string_items(semantic_watch.get("watch_symbols")),
        "semantic_watch_addresses": string_items(semantic_watch.get("watch_addresses")),
        "semantic_replay_required": bool(semantic_replay["required"]),
        "semantic_replay_executed": bool(semantic_replay["executed"]),
        "semantic_replay_watch_symbols": string_items(semantic_replay.get("watch_symbols")),
        "semantic_replay_watch_addresses": string_items(semantic_replay.get("watch_addresses")),
        "semantic_replay_save_state": str(semantic_replay.get("save_state", "")),
        "save_state_delta": copy.deepcopy(execution.get("save_state_delta", {})),
        "errors": combined_errors,
        "warnings": unique_list(
            [
                *string_items(execution.get("warnings")),
                *string_items(semantic_watch.get("warnings")),
                *string_items(semantic_replay.get("warnings")),
            ]
        ),
    }


def execution_with_applied_patch_metadata(execution: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(execution)
    out_state = str(out.get("out_state", ""))
    out["applied_patches"] = [
        {
            **patch,
            "executed": bool(out.get("executed")),
            "applied": True,
            "status": "applied",
            "materialization_status": "applied",
            "out_state": out_state,
        }
        for patch in dict_items(out.get("applied_patches"))
    ]
    return out


def execute_generic_state_patch_candidate(
    data: dict[str, Any],
    *,
    source: str,
    candidate_index: int,
    expectations: list[dict[str, Any]],
    symbols_path: str,
    root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    from .replay import build_replay_plan
    from .state_space import execute_state_space
    from .runtime_watch import build_watch_report

    context, context_errors = generic_state_execution_context(
        data,
        source=source,
        candidate_index=candidate_index,
        symbols_path=symbols_path,
        root=root,
    )
    patches, patch_errors = generic_state_executable_patches(data)
    errors = unique_list([*context_errors, *patch_errors])
    if errors:
        return data, {
            "attempted": True,
            "executed": False,
            "candidate_index": candidate_index,
            "patch_count": len(patches),
            "errors": errors,
        }
    execution = execute_state_space(
        patches=patches,
        rom=context["rom"],
        base_state=context["base_state"],
        output_state=context["out_state"],
        execute=True,
        root=root,
    )
    out = copy.deepcopy(data)
    out["execution"] = execution
    out["executed"] = bool(execution.get("executed"))
    out["out_state"] = str(execution.get("out_state", ""))
    if isinstance(execution.get("save_state_delta"), dict):
        out["save_state_delta"] = copy.deepcopy(execution["save_state_delta"])
    state_space = out.setdefault("state_space", {})
    if isinstance(state_space, dict):
        state_space["out_state"] = str(execution.get("out_state", ""))
        state_space["patches"] = list(execution.get("applied_patches") or patches)
        state_space["patch_count"] = len(state_space["patches"])
        if isinstance(execution.get("save_state_delta"), dict):
            state_space["save_state_delta"] = copy.deepcopy(execution["save_state_delta"])
    out["patch_count"] = len(execution.get("applied_patches") or patches)
    out["minimized_evidence_view"] = True
    out["minimized_execution_view"] = True
    semantic_watch = execute_candidate_semantic_watch(
        data=out,
        context=context,
        expectations=expectations,
        build_watch_report_func=build_watch_report,
        root=root,
    )
    semantic_replay = execute_candidate_semantic_replay(
        data=out,
        context=context,
        expectations=expectations,
        build_replay_plan_func=build_replay_plan,
        root=root,
    )
    if semantic_watch["required"]:
        out["semantic_watch_reducer"] = {
            key: value
            for key, value in semantic_watch.items()
            if key != "report"
        }
        if isinstance(semantic_watch.get("report"), dict):
            out["watch_report"] = semantic_watch["report"]
    if semantic_replay["required"]:
        out["semantic_replay_reducer"] = {
            key: value
            for key, value in semantic_replay.items()
            if key != "report"
        }
        if isinstance(semantic_replay.get("report"), dict):
            out["replay_report"] = semantic_replay["report"]
    out.setdefault("warnings", [])
    if isinstance(out["warnings"], list):
        out["warnings"] = unique_list(
            [
                *string_items(out["warnings"]),
                "minimized generic state-space candidate was materialized before expectation evaluation",
                *string_items(semantic_watch.get("warnings")),
                *string_items(semantic_replay.get("warnings")),
            ]
        )
        out["warning_count"] = len(out["warnings"])
    combined_errors = unique_list(
        [
            *string_items(execution.get("errors")),
            *string_items(semantic_watch.get("errors")),
            *string_items(semantic_replay.get("errors")),
        ]
    )
    return out, {
        "attempted": True,
        "executed": bool(execution.get("executed")),
        "candidate_index": candidate_index,
        "patch_count": len(patches),
        "out_state": str(execution.get("out_state", "")),
        "semantic_watch_required": bool(semantic_watch["required"]),
        "semantic_watch_executed": bool(semantic_watch["executed"]),
        "semantic_watch_symbols": string_items(semantic_watch.get("watch_symbols")),
        "semantic_watch_addresses": string_items(semantic_watch.get("watch_addresses")),
        "semantic_replay_required": bool(semantic_replay["required"]),
        "semantic_replay_executed": bool(semantic_replay["executed"]),
        "semantic_replay_watch_symbols": string_items(semantic_replay.get("watch_symbols")),
        "semantic_replay_watch_addresses": string_items(semantic_replay.get("watch_addresses")),
        "semantic_replay_save_state": str(semantic_replay.get("save_state", "")),
        "save_state_delta": copy.deepcopy(execution.get("save_state_delta", {})),
        "errors": combined_errors,
        "warnings": unique_list(
            [
                *string_items(execution.get("warnings")),
                *string_items(semantic_watch.get("warnings")),
                *string_items(semantic_replay.get("warnings")),
            ]
        ),
    }


def execute_candidate_semantic_watch(
    *,
    data: dict[str, Any],
    context: dict[str, Path],
    expectations: list[dict[str, Any]],
    build_watch_report_func: Any,
    root: Path,
) -> dict[str, Any]:
    required = expectations_need_runtime_watch(expectations)
    watch_symbols = candidate_watch_symbols(data=data, expectations=expectations)
    watch_addresses = candidate_watch_addresses(data=data, expectations=expectations)
    watch_size = candidate_watch_size(data, expectations=expectations)
    if not required:
        return {
            "required": False,
            "executed": False,
            "watch_symbols": watch_symbols,
            "watch_addresses": watch_addresses,
            "watch_size": watch_size,
            "errors": [],
            "warnings": [],
        }
    if not watch_symbols and not watch_addresses:
        return {
            "required": True,
            "executed": False,
            "watch_symbols": [],
            "watch_addresses": [],
            "watch_size": watch_size,
            "errors": ["semantic watch reducer requires at least one watch symbol or raw watch address"],
            "warnings": [],
        }
    try:
        report = build_watch_report_func(
            watch_symbols=tuple(watch_symbols),
            watch_addresses=tuple(watch_addresses),
            watch_size=watch_size,
            rom_path=str(context["rom"]),
            symbols_path=str(context["symbols"]),
            save_state=str(context["out_state"]),
            frames=60,
            context_frames=12,
            execute=True,
            root=root,
        )
    except Exception as exc:
        return {
            "required": True,
            "executed": False,
            "watch_symbols": watch_symbols,
            "watch_addresses": watch_addresses,
            "watch_size": watch_size,
            "errors": [f"semantic watch reducer failed: {exc}"],
            "warnings": [],
        }
    return {
        "required": True,
        "executed": bool(report.get("executed")) and not report.get("errors"),
        "watch_symbols": watch_symbols,
        "watch_addresses": watch_addresses,
        "watch_size": watch_size,
        "hit_count": int(report.get("hit_count", 0)),
        "errors": list(report.get("errors", [])),
        "warnings": list(report.get("warnings", [])),
        "report": report,
    }


def execute_candidate_semantic_replay(
    *,
    data: dict[str, Any],
    context: dict[str, Path],
    expectations: list[dict[str, Any]],
    build_replay_plan_func: Any,
    root: Path,
) -> dict[str, Any]:
    watch_symbols = candidate_watch_symbols(data=data, expectations=expectations)
    watch_addresses = candidate_watch_addresses(data=data, expectations=expectations)
    watch_size = candidate_watch_size(data, expectations=expectations)
    symbols = [] if watch_addresses else candidate_replay_symbols(data=data, watch_symbols=watch_symbols)
    scenario_ids = candidate_replay_scenario_ids(data)
    source_files = candidate_replay_source_files(data)
    save_state = str(context.get("out_state") or "")
    execute_watch = expectations_need_runtime_watch(expectations) and bool(watch_symbols or watch_addresses)
    required = bool(save_state and (watch_symbols or watch_addresses or symbols or scenario_ids))
    if not required:
        return {
            "required": False,
            "executed": False,
            "execute_watch": execute_watch,
            "watch_symbols": watch_symbols,
            "watch_addresses": watch_addresses,
            "watch_size": watch_size,
            "symbols": symbols,
            "scenario_ids": scenario_ids,
            "source_files": source_files,
            "save_state": save_state,
            "errors": [],
            "warnings": [],
        }
    try:
        report = build_replay_plan_func(
            rom_path=str(context["rom"]),
            symbols_path=str(context["symbols"]),
            save_state=save_state,
            scenario_ids=tuple(scenario_ids),
            watch_symbols=tuple(watch_symbols),
            watch_addresses=tuple(watch_addresses),
            watch_size=watch_size,
            symbols=tuple(symbols),
            changed_files=tuple(source_files),
            frames=60,
            context_frames=12,
            execute_watch=execute_watch,
            root=root,
        )
    except Exception as exc:
        return {
            "required": True,
            "executed": False,
            "execute_watch": execute_watch,
            "watch_symbols": watch_symbols,
            "watch_addresses": watch_addresses,
            "watch_size": watch_size,
            "symbols": symbols,
            "scenario_ids": scenario_ids,
            "source_files": source_files,
            "save_state": save_state,
            "errors": [f"semantic replay reducer failed: {exc}"],
            "warnings": [],
        }
    replay_valid = bool(report.get("valid"))
    watch_executed = bool(report.get("executed_watch"))
    return {
        "required": True,
        "executed": replay_valid and (not execute_watch or watch_executed),
        "execute_watch": execute_watch,
        "watch_executed": watch_executed,
        "watch_symbols": watch_symbols,
        "watch_addresses": watch_addresses,
        "watch_size": watch_size,
        "symbols": symbols,
        "scenario_ids": scenario_ids,
        "source_files": source_files,
        "save_state": save_state,
        "phase_count": int(report.get("phase_count", 0)),
        "command_count": len(report.get("commands", [])),
        "errors": list(report.get("errors", [])),
        "warnings": list(report.get("warnings", [])),
        "report": report,
    }


def expectations_need_runtime_watch(expectations: list[dict[str, Any]]) -> bool:
    for expectation in expectations:
        expectation_type = str(expectation.get("type", ""))
        if expectation_type in {"event_observed", "event_absent", "value_equals"}:
            return True
        if expectation.get("watch") or expectation.get("watch_symbol") or expectation.get("watch_address"):
            return True
    return False


def candidate_replay_symbols(*, data: dict[str, Any], watch_symbols: list[str]) -> list[str]:
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    patch_symbols = [
        str(patch.get("base_symbol") or patch.get("symbol") or "")
        for patch in dict_items(state_space.get("patches"))
    ]
    for materialization in dict_items(data.get("materializations")):
        patch_symbols.extend(
            str(patch.get("base_symbol") or patch.get("symbol") or "")
            for patch in dict_items(materialization.get("patches"))
        )
    return unique_list(
        symbol
        for symbol in [
            *watch_symbols,
            *string_items(data.get("symbols")),
            *string_items(state_space.get("symbols")),
            *patch_symbols,
        ]
        if symbol
    )


def candidate_replay_scenario_ids(data: dict[str, Any]) -> list[str]:
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    return unique_list(
        scenario_id
        for scenario_id in [
            *string_items(data.get("scenario_ids")),
            *content_state_scenario_ids(data),
            *[
                str(patch.get("scenario_id", ""))
                for patch in dict_items(state_space.get("patches"))
            ],
        ]
        if scenario_id
    )


def candidate_replay_source_files(data: dict[str, Any]) -> list[str]:
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    source_files = [
        *content_state_source_files(data),
        *[
            normalize_path(str(patch.get("source_file", "")))
            for patch in dict_items(state_space.get("patches"))
        ],
    ]
    return unique_list(path for path in source_files if path)


def candidate_watch_symbols(*, data: dict[str, Any], expectations: list[dict[str, Any]]) -> list[str]:
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    raw_watch_requested = bool(candidate_watch_addresses(data=data, expectations=expectations))
    patch_symbols = [
        str(patch.get("base_symbol") or patch.get("symbol") or "")
        for patch in dict_items(state_space.get("patches"))
    ]
    for materialization in dict_items(data.get("materializations")):
        patch_symbols.extend(
            str(patch.get("base_symbol") or patch.get("symbol") or "")
            for patch in dict_items(materialization.get("patches"))
        )
    explicit_symbols = [
        *string_items(data.get("watch_symbols")),
        *string_items(state_space.get("watch_symbols")),
        *[
            symbol
            for materialization in dict_items(data.get("materializations"))
            for symbol in string_items(materialization.get("watch_symbols"))
        ],
    ]
    expectation_symbols: list[str] = []
    for expectation in expectations:
        for key in ("watch", "watch_symbol", "state_symbol"):
            value = str(expectation.get(key, ""))
            if value:
                expectation_symbols.append(value)
        if str(expectation.get("type", "")) in {"event_observed", "event_absent", "value_equals"}:
            symbol = str(expectation.get("symbol", ""))
            if symbol and (not patch_symbols or base_label(symbol) in {base_label(patch_symbol) for patch_symbol in patch_symbols}):
                expectation_symbols.append(symbol)
    return unique_list(
        symbol
        for symbol in [
            *explicit_symbols,
            *expectation_symbols,
            *([] if raw_watch_requested else patch_symbols),
        ]
        if symbol
    )


def candidate_watch_addresses(*, data: dict[str, Any], expectations: list[dict[str, Any]]) -> list[str]:
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    explicit_addresses = [
        *string_items(data.get("watch_addresses")),
        *string_items(state_space.get("watch_addresses")),
        *report_watch_addresses(data),
        *[
            address
            for materialization in dict_items(data.get("materializations"))
            for address in string_items(materialization.get("watch_addresses"))
        ],
    ]
    expectation_addresses: list[str] = []
    for expectation in expectations:
        for key in ("watch_address", "address", "bank_address"):
            value = str(expectation.get(key, ""))
            if value:
                expectation_addresses.append(value)
    return unique_list(
        address
        for address in [*explicit_addresses, *expectation_addresses]
        if address
    )


def candidate_watch_size(data: dict[str, Any], *, expectations: list[dict[str, Any]] | None = None) -> int:
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    values = [
        data.get("watch_size"),
        state_space.get("watch_size"),
        *report_watch_sizes(data),
        *[
            materialization.get("watch_size")
            for materialization in dict_items(data.get("materializations"))
        ],
        expectation_watch_size(expectations or []),
    ]
    sizes: list[int] = []
    for value in values:
        try:
            size = int(value)
        except (TypeError, ValueError):
            continue
        if size > 0:
            sizes.append(size)
    return max(sizes, default=1)


def report_watch_addresses(data: Any) -> list[str]:
    addresses: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            lowered = str(key).lower()
            if lowered in {"watch_address", "watch_addresses", "sink_address", "sink_addresses", "related_addresses"}:
                addresses.extend(string_items(value))
            elif lowered == "target":
                addresses.extend(item for item in string_items(value) if looks_like_address(item))
            addresses.extend(report_watch_addresses(value))
    elif isinstance(data, list | tuple):
        for item in data:
            addresses.extend(report_watch_addresses(item))
    return unique_list(address for address in addresses if address)


def report_watch_sizes(data: Any) -> list[int]:
    sizes: list[int] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if str(key).lower() in {"watch_size", "sink_size"}:
                try:
                    size = int(value)
                except (TypeError, ValueError):
                    size = 0
                if size > 0:
                    sizes.append(size)
            sizes.extend(report_watch_sizes(value))
    elif isinstance(data, list | tuple):
        for item in data:
            sizes.extend(report_watch_sizes(item))
    return sizes


def looks_like_address(value: str) -> bool:
    text = str(value).strip()
    if not text:
        return False
    if "=" in text:
        _label, text = [part.strip() for part in text.rsplit("=", 1)]
    if text.startswith("$"):
        text = text[1:]
    if text.lower().startswith("0x"):
        text = text[2:]
    if ":" in text:
        bank, address = [part.strip().lstrip("$") for part in text.split(":", 1)]
        return is_hex(bank, 2) and is_hex(address, 4)
    return is_hex(text, 4)


def is_hex(value: str, max_length: int) -> bool:
    text = str(value).strip()
    return bool(text) and len(text) <= max_length and all(char in "0123456789abcdefABCDEF" for char in text)


def content_state_execution_context(
    data: dict[str, Any],
    *,
    source: str,
    candidate_index: int,
    symbols_path: str,
    root: Path,
) -> tuple[dict[str, Path], list[str]]:
    rom_text = str(data.get("rom") or data.get("rom_path") or "pokegold.gbc")
    symbols_text = str(data.get("symbols") or data.get("symbols_path") or symbols_path)
    base_text = str(data.get("base_save_state") or value_at_key_path(data, ("execution", "base_save_state")) or "")
    rom = resolve_path(rom_text, root=root)
    symbols = resolve_path(symbols_text, root=root)
    base_state = resolve_path(base_text, root=root) if base_text else None
    out_state = state_patch_candidate_out_state(
        source=source,
        candidate_index=candidate_index,
        root=root,
    )
    errors = []
    if not rom.exists():
        errors.append(f"missing ROM for content-state minimization execution: {rom_text}")
    if base_state is None:
        errors.append("content-state minimization execution requires base_save_state")
    elif not base_state.exists():
        errors.append(f"missing base save state for content-state minimization execution: {base_text}")
    return {
        "rom": rom,
        "symbols": symbols,
        "base_state": base_state or root / "<missing-base-state>",
        "out_state": out_state,
    }, errors


def generic_state_execution_context(
    data: dict[str, Any],
    *,
    source: str,
    candidate_index: int,
    symbols_path: str,
    root: Path,
) -> tuple[dict[str, Path], list[str]]:
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
    rom_text = str(data.get("rom") or data.get("rom_path") or "pokegold.gbc")
    symbols_text = str(data.get("symbols") or data.get("symbols_path") or state_space.get("symbols") or symbols_path)
    base_text = str(
        data.get("base_save_state")
        or state_space.get("base_save_state")
        or execution.get("base_save_state")
        or ""
    )
    rom = resolve_path(rom_text, root=root)
    symbols = resolve_path(symbols_text, root=root)
    base_state = resolve_path(base_text, root=root) if base_text else None
    out_state = state_patch_candidate_out_state(
        source=source,
        candidate_index=candidate_index,
        root=root,
    )
    errors = []
    if not rom.exists():
        errors.append(f"missing ROM for state-space minimization execution: {rom_text}")
    if base_state is None:
        errors.append("state-space minimization execution requires base_save_state")
    elif not base_state.exists():
        errors.append(f"missing base save state for state-space minimization execution: {base_text}")
    return {
        "rom": rom,
        "symbols": symbols,
        "base_state": base_state or root / "<missing-base-state>",
        "out_state": out_state,
    }, errors


def generic_state_executable_patches(data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    patches = []
    errors = []
    for patch in dict_items(value_at_key_path(data, ("state_space", "patches"))):
        missing = [
            key
            for key in ("bank", "address", "value")
            if patch.get(key) in {None, ""}
        ]
        if missing:
            errors.append(
                "state-space patch is missing execution fields "
                + ",".join(missing)
                + f": {patch.get('symbol', '<unknown>')}"
            )
            continue
        patches.append(patch)
    return patches, unique_list(errors)


def state_patch_candidate_out_state(*, source: str, candidate_index: int, root: Path) -> Path:
    source_name = safe_name(Path(source).stem or source or "state_space")
    return (
        root
        / ".local"
        / "tmp"
        / "debugger_state_space_minimize"
        / f"{source_name}_{candidate_index:04d}.state"
    )


def content_state_patch_locations(data: dict[str, Any]) -> list[dict[str, Any]]:
    locations = []
    for materialization_index, materialization in enumerate(dict_items(data.get("materializations"))):
        scenario_id = str(materialization.get("scenario_id", ""))
        for patch_index, patch in enumerate(dict_items(materialization.get("patches"))):
            locations.append(
                {
                    "section": "materialization",
                    "materialization_index": materialization_index,
                    "patch_index": patch_index,
                    "symbol": str(patch.get("symbol", "")),
                    "base_symbol": str(patch.get("base_symbol") or patch.get("symbol") or ""),
                    "bank_address": str(patch.get("bank_address", "")),
                    "address": patch.get("address", ""),
                    "scenario_id": scenario_id,
                    "applied": False,
                }
            )
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
    for patch_index, patch in enumerate(dict_items(execution.get("applied_patches"))):
        locations.append(
            {
                "section": "applied",
                "materialization_index": -1,
                "patch_index": patch_index,
                "symbol": str(patch.get("symbol", "")),
                "base_symbol": str(patch.get("base_symbol") or patch.get("symbol") or ""),
                "bank_address": str(patch.get("bank_address", "")),
                "address": patch.get("address", ""),
                "scenario_id": str(patch.get("scenario_id", "")),
                "applied": True,
            }
        )
    return locations


def generic_state_patch_locations(data: dict[str, Any]) -> list[dict[str, Any]]:
    locations: list[dict[str, Any]] = []
    for path in (("state_patches",), ("state_space", "patches"), ("state_space", "state_patches")):
        for patch_index, patch in enumerate(dict_items(value_at_key_path(data, path))):
            symbol = str(patch.get("symbol", ""))
            if not symbol:
                continue
            locations.append(
                {
                    "section": "generic",
                    "path": list(path),
                    "patch_index": patch_index,
                    "symbol": symbol,
                    "base_symbol": str(patch.get("base_symbol") or patch.get("symbol") or ""),
                    "bank_address": str(patch.get("bank_address", "")),
                    "address": patch.get("address", ""),
                    "scenario_id": str(patch.get("scenario_id", "")),
                    "source_file": normalize_path(str(patch.get("source_file", ""))),
                    "applied": bool(patch.get("applied", False)),
                }
            )
    return locations


def value_at_key_path(data: dict[str, Any], path: tuple[str, ...] | list[str]) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def set_value_at_key_path(data: dict[str, Any], path: tuple[str, ...] | list[str], value: Any) -> None:
    current: Any = data
    for key in path[:-1]:
        if not isinstance(current, dict):
            return
        current = current.get(key)
    if isinstance(current, dict) and path:
        current[path[-1]] = value


def state_patch_report_with_patch_locations(view: dict[str, Any], locations: list[dict[str, Any]]) -> dict[str, Any]:
    if view.get("view_kind") == "content_state":
        return content_state_report_with_patch_locations(view["data"], locations)
    return generic_state_report_with_patch_locations(view["data"], locations)


def content_state_report_with_patch_locations(data: dict[str, Any], locations: list[dict[str, Any]]) -> dict[str, Any]:
    kept = {patch_location_key(location) for location in locations}
    out = copy.deepcopy(data)
    for materialization_index, materialization in enumerate(dict_items(out.get("materializations"))):
        patches = [
            patch
            for patch_index, patch in enumerate(dict_items(materialization.get("patches")))
            if ("materialization", materialization_index, patch_index) in kept
        ]
        materialization["patches"] = patches
        materialization["patch_count"] = len(patches)
        if not patches and materialization.get("status") == "ready":
            materialization["status"] = "minimized"
    execution = out.get("execution") if isinstance(out.get("execution"), dict) else None
    if execution is not None:
        applied = [
            patch
            for patch_index, patch in enumerate(dict_items(execution.get("applied_patches")))
            if ("applied", -1, patch_index) in kept
        ]
        execution["applied_patches"] = applied
        execution["patch_count"] = len(applied)
    out["patch_count"] = sum(
        len(dict_items(materialization.get("patches")))
        for materialization in dict_items(out.get("materializations"))
    )
    out["minimized_evidence_view"] = True
    out.setdefault("warnings", [])
    if isinstance(out["warnings"], list):
        out["warnings"] = unique_list(
            [
                *string_items(out["warnings"]),
                "minimized content-state evidence view; rerun content-state execution before treating it as a physical save state",
            ]
        )
        out["warning_count"] = len(out["warnings"])
    return out


def generic_state_report_with_patch_locations(data: dict[str, Any], locations: list[dict[str, Any]]) -> dict[str, Any]:
    kept = {patch_location_key(location) for location in locations}
    out = copy.deepcopy(data)
    for path in (("state_patches",), ("state_space", "patches"), ("state_space", "state_patches")):
        patches = [
            patch
            for patch_index, patch in enumerate(dict_items(value_at_key_path(out, path)))
            if ("generic", tuple(path), patch_index) in kept
        ]
        if value_at_key_path(out, path) is not None:
            set_value_at_key_path(out, path, patches)
    out["minimized_evidence_view"] = True
    out.setdefault("warnings", [])
    if isinstance(out["warnings"], list):
        out["warnings"] = unique_list(
            [
                *string_items(out["warnings"]),
                "minimized generic state-space evidence view; rerun materialization or emulator execution before treating it as a physical save state",
            ]
        )
        out["warning_count"] = len(out["warnings"])
    return out


def patch_location_key(location: dict[str, Any]) -> tuple[Any, ...]:
    section = str(location.get("section", ""))
    if section == "generic":
        return (section, tuple(string_items(location.get("path"))), int(location.get("patch_index", -1)))
    return (
        section,
        int(location.get("materialization_index", -1)),
        int(location.get("patch_index", -1)),
    )


def write_minimized_state_report(
    *,
    best: dict[str, Any] | None,
    out_state_report: str,
    root: Path,
) -> dict[str, Any]:
    if best is None:
        return {"path": "", "written": False, "errors": []}
    if not out_state_report:
        return {"path": "", "written": False, "errors": []}
    path = resolve_path(out_state_report, root=root)
    data = best.get("data")
    if not isinstance(data, dict):
        return {"path": display_path(path, root=root), "written": False, "errors": ["no minimized state-space report was available to write"]}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True),
        encoding="utf-8",
        newline="\n",
    )
    return {"path": display_path(path, root=root), "written": True, "errors": []}


def public_state_patch_minimize_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in result.items()
        if key != "data"
    }


def minimized_save_state_delta_for_result(result: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {}
    data = result.get("data")
    if not isinstance(data, dict):
        return {}
    delta = data.get("save_state_delta")
    if isinstance(delta, dict):
        return copy.deepcopy(delta)
    execution = data.get("execution")
    if isinstance(execution, dict) and isinstance(execution.get("save_state_delta"), dict):
        return copy.deepcopy(execution["save_state_delta"])
    state_space = data.get("state_space")
    if isinstance(state_space, dict) and isinstance(state_space.get("save_state_delta"), dict):
        return copy.deepcopy(state_space["save_state_delta"])
    return {}


def content_state_scenario_ids(data: dict[str, Any]) -> list[str]:
    return unique_list(
        str(materialization.get("scenario_id", ""))
        for materialization in dict_items(data.get("materializations"))
        if materialization.get("scenario_id")
    )


def content_state_source_files(data: dict[str, Any]) -> list[str]:
    out = []
    for materialization in dict_items(data.get("materializations")):
        source_file = normalize_path(str(materialization.get("source_file", "")))
        if source_file:
            out.append(source_file)
        map_resolution = materialization.get("map_resolution") if isinstance(materialization.get("map_resolution"), dict) else {}
        map_source = normalize_path(str(map_resolution.get("source_file", "")))
        if map_source:
            out.append(map_source)
    return unique_list(out)


def state_patch_scenario_ids(data: dict[str, Any], locations: list[dict[str, Any]]) -> list[str]:
    return unique_list(
        [
            *content_state_scenario_ids(data),
            *[
                str(location.get("scenario_id", ""))
                for location in locations
                if location.get("scenario_id")
            ],
        ]
    )


def state_patch_source_files(data: dict[str, Any], locations: list[dict[str, Any]]) -> list[str]:
    return unique_list(
        [
            *content_state_source_files(data),
            *[
                normalize_path(str(location.get("source_file", "")))
                for location in locations
                if location.get("source_file")
            ],
        ]
    )


def state_patch_source_mems(locations: list[dict[str, Any]]) -> list[str]:
    sources: list[str] = []
    for location in locations:
        address = patch_location_address(location)
        if not address:
            continue
        origin = str(location.get("base_symbol") or location.get("symbol") or "").strip()
        if origin:
            sources.append(f"{address}={origin}")
        else:
            sources.append(address)
    return unique_list(sources)


def patch_location_address(location: dict[str, Any]) -> str:
    bank_address = str(location.get("bank_address", "")).strip()
    if bank_address:
        return bank_address
    address = location.get("address")
    if isinstance(address, int):
        return f"{address & 0xFFFF:04X}"
    return str(address or "").strip()


def known_source_symbols(symbols: list[str], *, symbols_path: str, root: Path) -> list[str]:
    path = resolve_path(symbols_path, root=root)
    if not path.exists():
        return []
    symbol_table = parse_symbol_table(path)
    return unique_list(symbol for symbol in symbols if symbol in symbol_table)


def state_patch_suggested_expectations(views: list[dict[str, Any]]) -> list[str]:
    suggestions = []
    for view in views[:4]:
        for location in view["patches"][:8]:
            symbol = str(location.get("symbol", ""))
            if not symbol:
                continue
            scenario = str(location.get("scenario_id", ""))
            scenario_arg = f",scenario={scenario}" if scenario else ""
            suggestions.append(f"state-patch={symbol}{scenario_arg}")
    return unique_list(suggestions)


def state_patch_minimization_commands(
    *,
    out_report: str,
    source: str,
    scenario_ids: list[str],
    expectations: list[dict[str, Any]],
    source_symbols: list[str] | None = None,
    source_mems: list[str] | None = None,
    watch_symbols: list[str] | None = None,
    watch_addresses: list[str] | None = None,
    watch_size: int = 1,
    symbols_path: str = "pokegold.sym",
) -> list[str]:
    report = out_report or source or "<content_state.json>"
    effective_watch_symbols = unique_list([*(watch_symbols or []), *expectation_watch_symbols(expectations)])
    effective_watch_addresses = unique_list([*(watch_addresses or []), *expectation_watch_addresses(expectations)])
    effective_watch_size = max(watch_size if watch_size > 0 else 1, expectation_watch_size(expectations))
    commands = [
        f"python -m tools.debugger expect --report {report} --expect {expectation_cli(expectation)}"
        for expectation in expectations[:8]
        if expectation_cli(expectation)
    ]
    for scenario_id in scenario_ids[:4]:
        commands.append(f"python -m tools.debugger replay --report {report} --scenario-id {scenario_id} --execute-watch")
    for symbol in effective_watch_symbols[:4]:
        commands.append(f"python -m tools.debugger replay --report {report} --watch-symbol {symbol} --execute-watch")
    for address in effective_watch_addresses[:4]:
        commands.append(f"python -m tools.debugger replay --report {report} --watch-address {command_address_arg(address)} --watch-size {effective_watch_size} --execute-watch")
    dynamic_taint = state_patch_dynamic_taint_command(
        report=report,
        symbols_path=symbols_path,
        source_symbols=source_symbols or [],
        source_mems=source_mems or [],
        watch_symbols=effective_watch_symbols,
        watch_addresses=effective_watch_addresses,
        watch_size=effective_watch_size,
    )
    if dynamic_taint:
        commands.append(dynamic_taint)
    commands.append(f"python -m tools.debugger compare --report {report}")
    return unique_list(commands)


def state_patch_dynamic_taint_command(
    *,
    report: str,
    symbols_path: str,
    source_symbols: list[str],
    source_mems: list[str],
    watch_symbols: list[str],
    watch_addresses: list[str],
    watch_size: int,
) -> str:
    effective_source_symbols = unique_list(symbol for symbol in source_symbols if symbol)
    effective_source_mems = unique_list(source for source in source_mems if source)
    sink_symbols = unique_list(symbol for symbol in watch_symbols if symbol)
    sink_addresses = unique_list(address for address in watch_addresses if address)
    if not sink_symbols and not sink_addresses:
        return ""
    args = [
        "python -m tools.debugger dynamic-taint",
        "--report",
        report,
        "--symbols",
        symbols_path,
    ]
    for symbol in effective_source_symbols[:6]:
        args.extend(["--source-symbol", symbol])
    for source in effective_source_mems[:6]:
        args.extend(["--source-mem", source])
    for symbol in sink_symbols[:6]:
        args.extend(["--sink-symbol", symbol])
    for address in sink_addresses[:6]:
        args.extend(["--sink-address", command_address_arg(address)])
    if sink_addresses and watch_size != 1:
        args.extend(["--sink-size", str(watch_size)])
    args.append("--execute-synthesis")
    return " ".join(args)


def state_patch_semantic_reducer_routes(
    *,
    out_report: str,
    source: str,
    scenario_ids: list[str],
    symbols: list[str],
    source_files: list[str],
    source_symbols: list[str],
    source_mems: list[str],
    watch_symbols: list[str],
    watch_addresses: list[str],
    watch_size: int,
    expectations: list[dict[str, Any]],
    symbols_path: str,
) -> list[dict[str, Any]]:
    report = out_report or source or "<content_state_or_state_space.json>"
    surfaces = state_patch_semantic_surfaces(
        symbols=symbols,
        source_files=source_files,
        source_symbols=source_symbols,
        source_mems=source_mems,
        watch_symbols=watch_symbols,
        watch_addresses=watch_addresses,
        expectations=expectations,
    )
    routes: list[dict[str, Any]] = []
    add_semantic_route(
        routes,
        route_id="unified_static_causal_reducer",
        surface="general",
        reason="Map the minimized state artifact back to source labels, taint seeds, and static slices.",
        commands=[
            f"python -m tools.debugger provenance --report {report}",
            f"python -m tools.debugger taint --report {report}",
            f"python -m tools.debugger slice --report {report}",
        ],
    )
    if "content_static" in surfaces:
        for path in source_files[:4]:
            safe_path = safe_name(path.replace("/", "_").replace("\\", "_")) or "source"
            add_semantic_route(
                routes,
                route_id=f"content_static_semantic_reducer_{len(routes)}",
                surface="content_static",
                reason="Regenerate static mirrors and source-derived runtime scenarios for the minimized content surface.",
                source_file=path,
                commands=[
                    f"python -m tools.debugger content-mirror --source-file {path}",
                    f"python -m tools.debugger content-scenarios --source-file {path} --out-scenarios .local\\tmp\\debugger_content_scenarios_{safe_path}.jsonl",
                    f"python -m tools.debugger compare --report {report}",
                ],
            )
    if "battle_mechanics" in surfaces:
        add_semantic_route(
            routes,
            route_id="battle_mechanics_semantic_gates",
            surface="battle_mechanics",
            reason="Run damage, item, passive, and hazard debugger gates against the minimized battle-state artifact.",
            commands=[
                "python -m tools.damage_debugger.oracle",
                "python -m tools.damage_debugger.clobber_smoke",
                "python -m tools.damage_debugger.hazard_smoke",
                "python -m tools.damage_debugger.fuzz --self-check-workers=2",
            ],
        )
    if "boss_ai" in surfaces:
        add_semantic_route(
            routes,
            route_id="boss_ai_semantic_suite",
            surface="boss_ai",
            reason="Run Boss AI semantic scenario generation and ROM score materialization after state minimization.",
            commands=[
                "python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 24 --seed 1 --refresh-rom-score-materialization --json",
            ],
        )
    if scenario_ids and "boss_ai" in surfaces:
        add_semantic_route(
            routes,
            route_id="boss_ai_minimized_scenarios",
            surface="boss_ai",
            reason="Feed selected scenario ids to the Boss AI semantic minimizer when the minimized artifact carries scenario identity.",
            commands=[
                f"python -m tools.boss_ai_debugger minimize --scenario {source or '<scenarios.jsonl>'} --scenario-id {scenario_id}"
                for scenario_id in scenario_ids[:4]
            ],
        )
    dynamic_taint = state_patch_dynamic_taint_command(
        report=report,
        symbols_path=symbols_path,
        source_symbols=source_symbols,
        source_mems=source_mems,
        watch_symbols=watch_symbols,
        watch_addresses=watch_addresses,
        watch_size=watch_size,
    )
    if dynamic_taint:
        add_semantic_route(
            routes,
            route_id="minimized_dynamic_taint_reducer",
            surface="runtime_taint",
            reason="Trace minimized source memory into the preserved watch sink after candidate patch removal.",
            commands=[dynamic_taint],
        )
    return routes


def add_semantic_route(
    routes: list[dict[str, Any]],
    *,
    route_id: str,
    surface: str,
    reason: str,
    commands: list[str],
    source_file: str = "",
) -> None:
    concrete_commands = unique_list(command for command in commands if command)
    if not concrete_commands:
        return
    routes.append(
        {
            "id": route_id,
            "surface": surface,
            "source_file": source_file,
            "reason": reason,
            "command_count": len(concrete_commands),
            "commands": concrete_commands,
            "runnable_commands": [command for command in concrete_commands if command_is_runnable(command)],
            "blocked_commands": [command for command in concrete_commands if not command_is_runnable(command)],
        }
    )


def execute_semantic_reducer_routes(
    routes: list[dict[str, Any]],
    *,
    execute: bool,
    max_commands: int,
    timeout_seconds: int,
    root: Path,
) -> dict[str, Any]:
    steps = semantic_reducer_execution_steps(routes, max_commands=max_commands)
    if execute:
        for step in steps:
            execute_step(step, root=root, timeout_seconds=timeout_seconds)
    else:
        for step in steps:
            step["status"] = "planned"
    failed = [step for step in steps if step["status"] == "failed"]
    skipped = [step for step in steps if step["status"] == "skipped"]
    passed = [step for step in steps if step["status"] == "passed"]
    return {
        "attempted": bool(routes),
        "executed": execute,
        "route_count": len(routes),
        "step_count": len(steps),
        "max_commands": max(0, max_commands),
        "passed_count": len(passed),
        "failed_count": len(failed),
        "skipped_count": len(skipped),
        "truncated": len(all_semantic_reducer_commands(routes)) > len(steps),
        "steps": steps,
        "errors": [
            f"semantic_reducer {step['route_id']}: {step['command']}"
            for step in failed
        ],
    }


def semantic_reducer_execution_steps(routes: list[dict[str, Any]], *, max_commands: int) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    limit = max(0, int(max_commands))
    for route in routes:
        route_id = str(route.get("id") or route.get("surface") or "semantic_reducer")
        surface = str(route.get("surface", ""))
        for command in string_items(route.get("commands")):
            if len(steps) >= limit:
                return steps
            steps.append(
                {
                    "id": f"semantic_reducer:{len(steps) + 1}",
                    "route_id": route_id,
                    "surface": surface,
                    "command": command,
                    "runnable": command_is_runnable(command),
                    "status": "pending",
                    "returncode": None,
                    "elapsed_seconds": 0.0,
                    "stdout_tail": [],
                    "stderr_tail": [],
                }
            )
    return steps


def all_semantic_reducer_commands(routes: list[dict[str, Any]]) -> list[str]:
    return unique_list(
        command
        for route in routes
        for command in string_items(route.get("commands"))
    )


def state_patch_semantic_surfaces(
    *,
    symbols: list[str],
    source_files: list[str],
    source_symbols: list[str],
    source_mems: list[str],
    watch_symbols: list[str],
    watch_addresses: list[str],
    expectations: list[dict[str, Any]],
) -> list[str]:
    text = " ".join(
        [
            *symbols,
            *source_symbols,
            *source_mems,
            *watch_symbols,
            *watch_addresses,
            *source_files,
            *[
                str(expectation.get(key, ""))
                for expectation in expectations
                for key in ("id", "type", "symbol", "state_symbol", "watch_symbol", "address", "description")
            ],
        ]
    ).lower()
    surfaces: set[str] = set()
    if any(hint.lower() in text for hint in BOSS_AI_SYMBOL_HINTS) or any(
        keyword in text for keyword in SURFACE_KEYWORDS["boss_ai"]
    ):
        surfaces.add("boss_ai")
    if (
        any(hint.lower() in text for hint in DAMAGE_SYMBOL_HINTS)
        or any(keyword in text for keyword in SURFACE_KEYWORDS["damage"])
        or "engine/battle/" in text
        or "spikes" in text
        or "rapid_spin" in text
        or "wtypematchup" in text
    ):
        surfaces.add("battle_mechanics")
    if any(normalize_path(path).lower().startswith(CONTENT_SOURCE_ROOTS) for path in source_files):
        surfaces.add("content_static")
    return sorted(surfaces or {"general"})


def expectation_watch_symbols(expectations: list[dict[str, Any]]) -> list[str]:
    symbols: list[str] = []
    for expectation in expectations:
        for key in ("watch", "watch_symbol", "state_symbol", "symbol"):
            value = str(expectation.get(key, ""))
            if value:
                symbols.append(value)
    return unique_list(symbol for symbol in symbols if symbol)


def expectation_watch_addresses(expectations: list[dict[str, Any]]) -> list[str]:
    addresses: list[str] = []
    for expectation in expectations:
        for key in ("watch_address", "address", "bank_address"):
            value = str(expectation.get(key, ""))
            if value:
                addresses.append(value)
    return unique_list(address for address in addresses if address)


def expectation_watch_size(expectations: list[dict[str, Any]]) -> int:
    sizes: list[int] = []
    for expectation in expectations:
        for key in ("watch_size", "sink_size", "size"):
            try:
                size = int(expectation.get(key, 0))
            except (TypeError, ValueError):
                continue
            if size > 0:
                sizes.append(size)
    return max(sizes, default=1)


def expectation_cli(expectation: dict[str, Any]) -> str:
    expectation_type = str(expectation.get("type", ""))
    if expectation_type in {"event_observed", "event_absent"}:
        parts = []
        event_type = str(expectation.get("event_type", ""))
        if event_type:
            parts.append(event_type)
        event_fields = [
            *[key for key in EVENT_MATCH_FIELDS if key != "event_type"],
            "watch_size",
            "sink_size",
            "size",
            "contains",
        ]
        for key in event_fields:
            value = expectation.get(key)
            if value is None or value == "":
                continue
            parts.append(f"{key}={value}")
        if expectation.get("min_count") not in {None, "", 1, "1"}:
            parts.append(f"min={expectation['min_count']}")
        if expectation.get("max_count") not in {None, ""}:
            parts.append(f"max={expectation['max_count']}")
        prefix = "no-event=" if expectation_type == "event_absent" else "event="
        return prefix + ",".join(parts)
    if expectation_type == "state_patch_observed":
        symbol = str(expectation.get("symbol") or expectation.get("patch_symbol") or expectation.get("state_patch") or "")
        parts = [symbol] if symbol else []
        if expectation.get("scenario_id"):
            parts.append(f"scenario={expectation['scenario_id']}")
        if expectation.get("value") not in {None, ""}:
            parts.append(f"value={expectation['value']}")
        if expectation.get("applied") not in {None, ""}:
            parts.append(f"applied={expectation['applied']}")
        if expectation.get("verified") not in {None, ""}:
            parts.append(f"verified={expectation['verified']}")
        return "state-patch=" + ",".join(parts)
    if expectation_type == "symbol_observed" and expectation.get("symbol"):
        return f"symbol={expectation['symbol']}"
    if expectation_type == "scenario_observed" and expectation.get("scenario_id"):
        return f"scenario={expectation['scenario_id']}"
    if expectation_type == "source_observed" and expectation.get("source_file"):
        return f"source={expectation['source_file']}"
    if expectation_type == "rule_observed" and expectation.get("rule_id"):
        return f"rule={expectation['rule_id']}"
    if expectation_type == "address_observed" and expectation.get("address"):
        return f"address={command_address_arg(expectation['address'])}"
    return str(expectation.get("description") or expectation.get("id") or "")


def build_input_log_minimization(
    *,
    loaded_input_logs: list[dict[str, Any]],
    reports: tuple[str, ...],
    expectations: tuple[str, ...],
    expectation_files: tuple[str, ...],
    events: tuple[str, ...],
    out_input_log: str,
    root: Path,
) -> dict[str, Any]:
    loaded_expectations, expectation_errors = load_expectation_files(
        expectation_files=expectation_files,
        root=root,
    )
    all_expectations = normalize_expectations(
        [
            *[parse_cli_expectation(item) for item in expectations],
            *loaded_expectations,
            *input_expectations(
                symbols=(),
                events=events,
                rules=(),
                addresses=(),
                source_files=(),
            ),
        ]
    )
    input_only_expectations = [
        expectation
        for expectation in all_expectations
        if supports_input_log_expectation(expectation)
    ]
    events_with_source = [
        event
        for loaded in loaded_input_logs
        for event in loaded.get("events", [])
        if isinstance(event, dict)
    ]
    if not loaded_input_logs:
        return {
            "attempted": False,
            "reason": "no --input-log inputs were supplied",
            "errors": expectation_errors,
            "input_log_count": 0,
            "expectation_count": len(input_only_expectations),
        }
    if not input_only_expectations:
        return {
            "attempted": False,
            "reason": "no input-log predicate was supplied",
            "errors": expectation_errors,
            "input_log_count": len(loaded_input_logs),
            "original_event_count": len(events_with_source),
            "expectation_count": 0,
        }
    minimized = minimize_input_events(events_with_source, expectations=input_only_expectations)
    output = write_minimized_input_log(
        events=minimized["events"] if minimized["preserved"] else [],
        out_input_log=out_input_log,
        root=root,
    )
    errors = [*expectation_errors, *output.get("errors", [])]
    commands = input_log_minimization_commands(
        out_input_log=output.get("path", ""),
        reports=reports,
        expectations=input_only_expectations,
    )
    return {
        "attempted": True,
        "preserved": bool(minimized["preserved"]) and not errors,
        "input_log_count": len(loaded_input_logs),
        "input_logs": [str(item.get("source", "")) for item in loaded_input_logs],
        "expectation_count": len(input_only_expectations),
        "expectations": [
            {
                "id": str(expectation.get("id", "")),
                "type": str(expectation.get("type", "")),
                "event_type": str(expectation.get("event_type", "")),
                "description": str(expectation.get("description", expectation.get("id", ""))),
            }
            for expectation in input_only_expectations
        ],
        "original_event_count": len(events_with_source),
        "minimized_event_count": len(minimized["events"]) if minimized["preserved"] else 0,
        "removed_event_count": max(0, len(events_with_source) - len(minimized["events"])) if minimized["preserved"] else 0,
        "written_line_count": int(output.get("line_count", 0) or 0),
        "out_input_log": output.get("path", ""),
        "written": bool(output.get("written")),
        "button_sample": input_button_sample(minimized["events"]) if minimized["preserved"] else [],
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "results": minimized["results"],
        "errors": errors,
        "known_limits": [
            "Input-log minimization preserves explicit input predicates and retained event timing in the text log; it does not prove the minimized log still reproduces the ROM symptom until replay/watch routes execute.",
        ],
    }


def supports_input_log_expectation(expectation: dict[str, Any]) -> bool:
    expectation_type = str(expectation.get("type", ""))
    if expectation_type in {"contains_text", "text_absent"}:
        return bool(expectation.get("contains"))
    if expectation_type not in {"event_observed", "event_absent"}:
        return False
    event_type = str(expectation.get("event_type", ""))
    if event_type in {"played_input", "input_event", "wait", "input_wait"}:
        return True
    return any(expectation.get(key) not in {None, ""} for key in ("button", "buttons", "raw", "line", "frame", "contains"))


def minimize_input_events(
    events: list[dict[str, Any]],
    *,
    expectations: list[dict[str, Any]],
) -> dict[str, Any]:
    def predicate(candidate: list[dict[str, Any]]) -> bool:
        if not candidate:
            return False
        return input_expectations_pass(candidate, expectations=expectations)

    initial_passed = predicate(events)
    minimized = greedy_minimize_items(events, predicate=predicate, min_items=1) if initial_passed else events
    return {
        "preserved": initial_passed,
        "events": minimized if initial_passed else [],
        "results": input_expectation_results(minimized if initial_passed else events, expectations=expectations),
    }


def input_expectations_pass(events: list[dict[str, Any]], *, expectations: list[dict[str, Any]]) -> bool:
    return all(result["status"] == "passed" for result in input_expectation_results(events, expectations=expectations))


def input_expectation_results(events: list[dict[str, Any]], *, expectations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for expectation in expectations:
        expectation_type = str(expectation.get("type", ""))
        matches = [event for event in events if input_event_matches(event, expectation)]
        if expectation_type in {"event_absent", "text_absent"}:
            max_count = int(expectation.get("max_count", 0) or 0)
            passed = len(matches) <= max_count
            observed = len(matches)
        else:
            min_count = int(expectation.get("min_count", 1) or 1)
            max_count = expectation.get("max_count")
            observed = len(matches)
            passed = observed >= min_count and (max_count is None or observed <= int(max_count))
        results.append(
            {
                "id": str(expectation.get("id", "")),
                "type": expectation_type,
                "event_type": str(expectation.get("event_type", "")),
                "status": "passed" if passed else "failed",
                "observed_count": observed,
                "evidence": [input_event_evidence(event) for event in matches[:8]],
            }
        )
    return results


def input_event_matches(event: dict[str, Any], expectation: dict[str, Any]) -> bool:
    expectation_type = str(expectation.get("type", ""))
    contains = str(expectation.get("contains", ""))
    if expectation_type in {"contains_text", "text_absent"}:
        return bool(contains and contains in input_event_text(event))

    event_type = str(expectation.get("event_type", ""))
    buttons = [str(button).lower() for button in event.get("buttons", []) if button]
    if event_type in {"wait", "input_wait"} and buttons:
        return False
    if event_type and event_type not in {"played_input", "input_event", "wait", "input_wait"}:
        return False
    expected_buttons = expected_input_buttons(expectation)
    if expected_buttons and not set(expected_buttons).issubset(set(buttons)):
        return False
    if expectation.get("raw") not in {None, ""} and str(event.get("raw", "")).strip() != str(expectation.get("raw", "")).strip():
        return False
    for key in ("line", "frame"):
        if expectation.get(key) not in {None, ""} and str(event.get(key, "")) != str(expectation.get(key, "")):
            return False
    if contains and contains not in input_event_text(event):
        return False
    return True


def expected_input_buttons(expectation: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("button", "buttons"):
        raw = str(expectation.get(key, ""))
        if not raw:
            continue
        pieces = raw.replace("+", ",").replace("|", ",").replace(";", ",").replace(" ", ",").split(",")
        values.extend(piece for piece in pieces if piece)
    out = []
    for value in values:
        normalized = BUTTON_ALIASES.get(value.upper(), value.lower())
        out.append(normalized)
    return unique_list(out)


def input_event_text(event: dict[str, Any]) -> str:
    return f"{event.get('raw', '')} {json.dumps(event, sort_keys=True)}"


def input_event_evidence(event: dict[str, Any]) -> str:
    buttons = "+".join(str(button).upper() for button in event.get("buttons", []) if button) or "WAIT"
    return f"frame={event.get('frame', '')} line={event.get('line', '')} input={buttons}"


def write_minimized_input_log(
    *,
    events: list[dict[str, Any]],
    out_input_log: str,
    root: Path,
) -> dict[str, Any]:
    if not out_input_log:
        return {"path": "", "written": False, "line_count": 0, "errors": []}
    if not events:
        path = resolve_path(out_input_log, root=root)
        return {
            "path": display_path(path, root=root),
            "written": False,
            "line_count": 0,
            "errors": ["no input events preserved the minimization predicate"],
        }
    path = resolve_path(out_input_log, root=root)
    lines = minimized_input_log_lines(events)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return {
        "path": display_path(path, root=root),
        "written": True,
        "line_count": len(lines),
        "errors": [],
    }


def minimized_input_log_lines(events: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    cursor = 0
    for event in sorted(events, key=lambda item: (int(item.get("frame", 0) or 0), int(item.get("line", 0) or 0))):
        frame = int(event.get("frame", cursor) or cursor)
        if frame > cursor:
            lines.append(f"WAIT {frame - cursor}")
            cursor = frame
        raw = str(event.get("raw", "")).strip()
        if not raw:
            buttons = [str(button).upper() for button in event.get("buttons", []) if button]
            raw = "+".join(buttons) if buttons else f"WAIT {max(1, int(event.get('advance_frames', 1) or 1))}"
        lines.append(raw)
        cursor = max(cursor, int(event.get("end_frame", frame + 1) or frame + 1))
    return lines


def input_button_sample(events: list[dict[str, Any]]) -> list[str]:
    return unique_list(
        str(button).upper()
        for event in events
        for button in event.get("buttons", [])
        if button
    )


def input_log_minimization_commands(
    *,
    out_input_log: str,
    reports: tuple[str, ...],
    expectations: list[dict[str, Any]],
) -> list[str]:
    artifact = out_input_log or "<minimized.inputs>"
    commands = [f"python -m tools.debugger ingest --input-log {artifact}"]
    for report in reports[:4]:
        commands.append(f"python -m tools.debugger replay --report {report} --input-log {artifact}")
        commands.append(f"python -m tools.debugger investigate --report {report} --input-log {artifact}")
    if not reports:
        commands.append(f"python -m tools.debugger replay --input-log {artifact} --save-state <state.sgm>")
        commands.append(f"python -m tools.debugger investigate --input-log {artifact} --save-state <state.sgm>")
    for expectation in expectations[:4]:
        expectation_arg = expectation_cli(expectation)
        if expectation_arg:
            commands.append(f"python -m tools.debugger minimize --input-log {artifact} --expect {expectation_arg}")
    return unique_list(commands)


def build_evidence_minimization(
    *,
    loaded_traces: list[dict[str, Any]],
    loaded_reports: list[dict[str, Any]],
    reports: tuple[str, ...],
    expectations: tuple[str, ...],
    expectation_files: tuple[str, ...],
    symbols: tuple[str, ...],
    events: tuple[str, ...],
    rules: tuple[str, ...],
    addresses: tuple[str, ...],
    source_files: tuple[str, ...],
    out_trace: str,
    symbols_path: str,
    max_trace_records: int,
    root: Path,
) -> dict[str, Any]:
    file_expectations, expectation_errors = load_expectation_files(
        expectation_files=expectation_files,
        root=root,
    )
    all_expectations = normalize_expectations(
        [
            *file_expectations,
            *[parse_cli_expectation(raw) for raw in expectations],
            *input_expectations(
                symbols=symbols,
                events=events,
                rules=rules,
                addresses=addresses,
                source_files=source_files,
            ),
        ]
    )
    candidates = [
        trace_view
        for loaded in loaded_traces
        for trace_view in trace_record_views(loaded, source_kind="trace")
    ]
    candidates.extend(
        trace_view
        for loaded in loaded_reports
        for trace_view in trace_record_views(loaded, source_kind="report")
    )
    if not candidates:
        return {
            "attempted": False,
            "reason": "no trace-like --trace or --report inputs were supplied",
            "errors": expectation_errors,
            "trace_count": len(loaded_traces),
            "report_count": len(loaded_reports),
            "expectation_count": len(all_expectations),
        }
    if not all_expectations:
        return {
            "attempted": False,
            "reason": "no --expect, --expect-file, --symbol, --event, --rule, --address, or --source-file predicate was supplied",
            "errors": expectation_errors,
            "trace_count": len(loaded_traces),
            "report_count": len(loaded_reports),
            "expectation_count": 0,
        }

    symbol_by_address = symbol_address_index(symbols_path=symbols_path, root=root)
    errors = list(expectation_errors)
    results = []
    for candidate in candidates:
        minimized = minimize_trace_view(
            candidate,
            expectations=all_expectations,
            reports=reports,
            symbol_by_address=symbol_by_address,
            max_trace_records=max_trace_records,
        )
        results.append(minimized)
    preserved = [item for item in results if item.get("preserved")]
    best = min(
        preserved,
        key=lambda item: (int(item.get("minimized_count", 0)), str(item.get("source", ""))),
        default=None,
    )
    output = write_minimized_trace(
        best=best,
        out_trace=out_trace,
        root=root,
    )
    best_data = best.get("data") if best else None
    watch_symbols = evidence_watch_symbols(best_data, expectations=all_expectations) if best_data is not None else []
    watch_addresses = evidence_watch_addresses(best_data, expectations=all_expectations) if best_data is not None else []
    watch_size = evidence_watch_size(best_data, expectations=all_expectations) if best_data is not None else expectation_watch_size(all_expectations)
    commands = evidence_minimization_commands(
        out_trace=output.get("path", ""),
        source=str(best.get("source", "")) if best else "",
        source_kind=str(best.get("source_kind", "")) if best else "",
        expectations=all_expectations,
        watch_symbols=watch_symbols,
        watch_addresses=watch_addresses,
        watch_size=watch_size,
    ) if best else []
    errors.extend(output.get("errors", []))
    return {
        "attempted": True,
        "preserved": best is not None and not errors,
        "trace_count": len(loaded_traces),
        "report_count": len(loaded_reports),
        "candidate_count": len(candidates),
        "expectation_count": len(all_expectations),
        "expectations": [
            {
                "id": str(expectation.get("id", "")),
                "type": str(expectation.get("type", "")),
                "description": str(expectation.get("description", expectation.get("id", ""))),
            }
            for expectation in all_expectations
        ],
        "source": str(best.get("source", "")) if best else "",
        "source_kind": str(best.get("source_kind", "")) if best else "",
        "record_path": str(best.get("record_path", "")) if best else "",
        "original_count": int(best.get("original_count", 0)) if best else 0,
        "candidate_count_after_filter": int(best.get("candidate_count_after_filter", 0)) if best else 0,
        "minimized_count": int(best.get("minimized_count", 0)) if best else 0,
        "removed_count": int(best.get("removed_count", 0)) if best else 0,
        "context_frame_original_count": int(best.get("context_frame_original_count", 0)) if best else 0,
        "context_frame_minimized_count": int(best.get("context_frame_minimized_count", 0)) if best else 0,
        "context_frame_removed_count": int(best.get("context_frame_removed_count", 0)) if best else 0,
        "context_minimized_event_count": int(best.get("context_minimized_event_count", 0)) if best else 0,
        "out_trace": output.get("path", ""),
        "written": bool(output.get("written")),
        "watch_symbols": watch_symbols,
        "watch_addresses": watch_addresses,
        "watch_size": watch_size,
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "result_count": len(results),
        "results": [public_minimize_result(item) for item in results[:12]],
        "errors": errors,
        "known_limits": [
            "Generic evidence minimization preserves explicit trace/report expectations and trims report context windows, not every hidden emulator state transition.",
            "For exact semantic minimization, feed the reduced evidence artifact into the owning subsystem reducer or ROM materialization command when one exists.",
        ],
    }


def public_minimize_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in result.items()
        if key != "data"
    }


def symbol_address_index(*, symbols_path: str, root: Path) -> dict[str, str]:
    path = resolve_path(symbols_path, root=root)
    if not path.exists():
        return {}
    return build_symbol_address_index(parse_symbol_table(path))


def trace_record_views(loaded: dict[str, Any], *, source_kind: str = "trace") -> list[dict[str, Any]]:
    data = loaded["data"]
    source = loaded["source"]
    if isinstance(data, list):
        records = [item for item in data if isinstance(item, dict)]
        return [
            {
                "source": source,
                "record_path": "$",
                "data": data,
                "records": records,
                "container": "root_list",
                "key": "",
                "source_kind": source_kind,
            }
        ] if records else []
    if not isinstance(data, dict):
        return []
    for key in ("events", "records", "trace", "entries"):
        value = data.get(key)
        if isinstance(value, list):
            records = [item for item in value if isinstance(item, dict)]
            if records:
                return [
                    {
                        "source": source,
                        "record_path": f"$.{key}",
                        "data": data,
                        "records": records,
                        "container": "dict_list",
                        "key": key,
                        "source_kind": source_kind,
                    }
                ]
    return []


def minimize_trace_view(
    trace_view: dict[str, Any],
    *,
    expectations: list[dict[str, Any]],
    reports: tuple[str, ...],
    symbol_by_address: dict[str, str],
    max_trace_records: int,
) -> dict[str, Any]:
    records = list(trace_view["records"])
    relevant = relevant_records(records, expectations=expectations, max_trace_records=max_trace_records)
    candidate_records = relevant or records[:max_trace_records]

    def predicate(candidate: list[dict[str, Any]]) -> bool:
        if not candidate:
            return False
        data = trace_data_with_records(trace_view, candidate)
        return expectations_pass(
            data,
            expectations=expectations,
            reports=reports,
            source=str(trace_view["source"]),
            symbol_by_address=symbol_by_address,
        )

    initial_passed = predicate(candidate_records)
    minimized = greedy_minimize_records(candidate_records, predicate=predicate) if initial_passed else candidate_records
    context_stats = empty_context_stats()
    if initial_passed:
        minimized, context_stats = minimize_dynamic_context_records(minimized, predicate=predicate)
    return {
        "source": trace_view["source"],
        "source_kind": trace_view.get("source_kind", "trace"),
        "record_path": trace_view["record_path"],
        "preserved": bool(initial_passed),
        "original_count": len(records),
        "candidate_count_after_filter": len(candidate_records),
        "minimized_count": len(minimized) if initial_passed else 0,
        "removed_count": len(records) - len(minimized) if initial_passed else 0,
        "truncated": len(records) > max_trace_records and not relevant,
        "data": trace_data_with_records(trace_view, minimized) if initial_passed else None,
        **context_stats,
    }


def relevant_records(
    records: list[dict[str, Any]],
    *,
    expectations: list[dict[str, Any]],
    max_trace_records: int,
) -> list[dict[str, Any]]:
    needles = expectation_needles(expectations)
    if not needles:
        return records[:max_trace_records]
    out = []
    for record in records:
        text = json.dumps(record, sort_keys=True).lower()
        if any(needle in text for needle in needles):
            out.append(record)
        if len(out) >= max_trace_records:
            break
    return out


def expectation_needles(expectations: list[dict[str, Any]]) -> list[str]:
    needles = []
    for expectation in expectations:
        for key in (
            "event_type",
            "symbol",
            "state_symbol",
            "source_symbol",
            "pc_symbol",
            "rule_id",
            "rule",
            "address",
            "bank_address",
            "source_file",
            "contains",
            "before",
            "after",
            "value",
            "delta",
            "operation",
        ):
            value = str(expectation.get(key, "")).strip().lower()
            if value:
                needles.append(value)
    return unique_list(needles)


def expectations_pass(
    data: Any,
    *,
    expectations: list[dict[str, Any]],
    reports: tuple[str, ...],
    source: str,
    symbol_by_address: dict[str, str],
) -> bool:
    trace_events = finalize_events(
        extract_trace_events(
            data,
            source=source,
            symbol_by_address=symbol_by_address,
        )
    )
    evidence = collect_evidence(
        loaded_reports=[],
        loaded_sources=[],
        trace_index={
            "kind": "unified_debugger_trace_index",
            "valid": True,
            "events": trace_events,
            "errors": [],
            "warnings": [],
        },
    )
    for report in reports:
        evidence["texts"].append(report)
    results = [evaluate_expectation(expectation, evidence=evidence) for expectation in expectations]
    return bool(results) and all(result["status"] == "passed" for result in results)


def evidence_watch_symbols(data: Any, *, expectations: list[dict[str, Any]]) -> list[str]:
    return unique_list(
        [
            *report_watch_symbols(data),
            *expectation_watch_symbols(expectations),
        ]
    )


def report_watch_symbols(data: Any) -> list[str]:
    symbols: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            lowered = str(key).lower()
            if lowered in {"watch", "watch_symbol", "watch_symbols", "sink_symbol", "sink_symbols", "related_symbols"}:
                symbols.extend(string_items(value))
            symbols.extend(report_watch_symbols(value))
    elif isinstance(data, list | tuple):
        for item in data:
            symbols.extend(report_watch_symbols(item))
    return unique_list(symbol for symbol in symbols if symbol)


def evidence_watch_addresses(data: Any, *, expectations: list[dict[str, Any]]) -> list[str]:
    return unique_address_targets(
        [
            *report_watch_addresses(data),
            *report_event_watch_addresses(data),
            *expectation_watch_addresses(expectations),
        ]
    )


def report_event_watch_addresses(data: Any) -> list[str]:
    addresses: list[str] = []
    if isinstance(data, dict):
        event_type = str(data.get("event_type", "")).lower()
        if event_type in {"memory_write", "memory_patch", "score_delta", "watch_change"}:
            for key in ("watch_address", "sink_address", "address", "bank_address", "score_pointer"):
                addresses.extend(item for item in string_items(data.get(key)) if looks_like_address(item))
        for value in data.values():
            addresses.extend(report_event_watch_addresses(value))
    elif isinstance(data, list | tuple):
        for item in data:
            addresses.extend(report_event_watch_addresses(item))
    return unique_list(address for address in addresses if address)


def unique_address_targets(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text:
            continue
        key = address_target_key(text)
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def address_target_key(value: str) -> str:
    text = str(value).strip().replace("$", "")
    if text.lower().startswith("0x"):
        text = text[2:]
    if ":" in text:
        bank, address = [part.strip() for part in text.split(":", 1)]
        return f"{bank.upper().rjust(2, '0')}:{address.upper().rjust(4, '0')}"
    return text.upper().rjust(4, "0")


def evidence_watch_size(data: Any, *, expectations: list[dict[str, Any]]) -> int:
    sizes = [*report_watch_sizes(data), expectation_watch_size(expectations)]
    return max((size for size in sizes if size > 0), default=1)


def evidence_minimization_commands(
    *,
    out_trace: str,
    source: str,
    source_kind: str,
    expectations: list[dict[str, Any]],
    watch_symbols: list[str],
    watch_addresses: list[str],
    watch_size: int,
) -> list[str]:
    artifact = out_trace or source or "<minimized-trace.json>"
    artifact_arg = "--report" if source_kind == "report" else "--trace"
    commands = [f"python -m tools.debugger trace-index {artifact_arg} {artifact}"]
    for expectation in expectations[:8]:
        expectation_arg = expectation_cli(expectation)
        if expectation_arg:
            commands.append(f"python -m tools.debugger expect {artifact_arg} {artifact} --expect {expectation_arg}")
    for symbol in watch_symbols[:4]:
        commands.append(f"python -m tools.debugger dynamic-taint {artifact_arg} {artifact} --sink-symbol {symbol}")
        if source_kind == "report":
            commands.append(f"python -m tools.debugger replay --report {artifact} --watch-symbol {symbol} --execute-watch")
    effective_watch_size = max(watch_size if watch_size > 0 else 1, expectation_watch_size(expectations))
    watch_size_arg = f" --watch-size {effective_watch_size}" if effective_watch_size != 1 else ""
    sink_size_arg = f" --sink-size {effective_watch_size}" if effective_watch_size != 1 else ""
    for address in unique_list([*watch_addresses, *expectation_watch_addresses(expectations)])[:4]:
        command_address = command_address_arg(address)
        commands.append(f"python -m tools.debugger trace-index {artifact_arg} {artifact} --address {command_address}")
        commands.append(f"python -m tools.debugger localize --address {command_address}{watch_size_arg}")
        commands.append(f"python -m tools.debugger setup --watch-address {command_address}{watch_size_arg}")
        if source_kind == "report":
            commands.append(f"python -m tools.debugger replay --report {artifact} --watch-address {command_address}{watch_size_arg} --execute-watch")
        commands.append(f"python -m tools.debugger watch --watch-address {command_address}{watch_size_arg} --execute")
        commands.append(f"python -m tools.debugger dynamic-taint {artifact_arg} {artifact} --sink-address {command_address}{sink_size_arg}")
    return unique_list(commands)


def greedy_minimize_records(
    records: list[dict[str, Any]],
    *,
    predicate: Any,
) -> list[dict[str, Any]]:
    return greedy_minimize_items(records, predicate=predicate, min_items=1)


def greedy_minimize_items(
    items: list[Any],
    *,
    predicate: Any,
    min_items: int = 0,
) -> list[Any]:
    kept = list(items)
    index = 0
    while index < len(kept):
        candidate = kept[:index] + kept[index + 1 :]
        if len(candidate) >= min_items and predicate(candidate):
            kept = candidate
            continue
        index += 1
    return kept


def minimize_dynamic_context_records(
    records: list[dict[str, Any]],
    *,
    predicate: Any,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    minimized = copy.deepcopy(records)
    original_context_frames = count_dynamic_context_frames(minimized)
    minimized_event_count = 0
    for context_path in dynamic_context_paths(minimized):
        changed = minimize_dynamic_context_at_path(
            minimized,
            context_path=context_path,
            predicate=predicate,
        )
        if changed:
            minimized_event_count += 1
    minimized_context_frames = count_dynamic_context_frames(minimized)
    return minimized, {
        "context_frame_original_count": original_context_frames,
        "context_frame_minimized_count": minimized_context_frames,
        "context_frame_removed_count": max(0, original_context_frames - minimized_context_frames),
        "context_minimized_event_count": minimized_event_count,
    }


def minimize_dynamic_context_at_path(
    records: list[dict[str, Any]],
    *,
    context_path: tuple[Any, ...],
    predicate: Any,
) -> bool:
    context = value_at_path(records, context_path)
    if not isinstance(context, dict):
        return False
    changed = False
    for key in CONTEXT_LIST_KEYS:
        frames = context.get(key)
        if not isinstance(frames, list) or not frames:
            continue

        def frames_predicate(candidate_frames: list[Any]) -> bool:
            candidate_records = copy.deepcopy(records)
            candidate_context = value_at_path(candidate_records, context_path)
            if not isinstance(candidate_context, dict):
                return False
            candidate_context[key] = candidate_frames
            refresh_context_counts(candidate_context)
            return predicate(candidate_records)

        min_items = 1 if key == "prelude" else 0
        kept = greedy_minimize_items(frames, predicate=frames_predicate, min_items=min_items)
        if len(kept) != len(frames):
            context[key] = kept
            refresh_context_counts(context)
            changed = True
    return changed


def dynamic_context_paths(data: Any) -> list[tuple[Any, ...]]:
    paths: list[tuple[Any, ...]] = []

    def walk(value: Any, path: tuple[Any, ...]) -> None:
        if isinstance(value, dict):
            if isinstance(value.get("dynamic_context"), dict):
                paths.append((*path, "dynamic_context"))
            for key, nested in value.items():
                walk(nested, (*path, key))
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                walk(nested, (*path, index))

    walk(data, ())
    return paths


def value_at_path(data: Any, path: tuple[Any, ...]) -> Any:
    value = data
    for part in path:
        if isinstance(part, int) and isinstance(value, list):
            value = value[part]
        elif isinstance(part, str) and isinstance(value, dict):
            value = value[part]
        else:
            return None
    return value


def count_dynamic_context_frames(records: list[dict[str, Any]]) -> int:
    total = 0
    for context_path in dynamic_context_paths(records):
        context = value_at_path(records, context_path)
        if not isinstance(context, dict):
            continue
        for key in CONTEXT_LIST_KEYS:
            frames = context.get(key)
            if isinstance(frames, list):
                total += len([frame for frame in frames if isinstance(frame, dict)])
    return total


def refresh_context_counts(context: dict[str, Any]) -> None:
    prelude = context.get("prelude")
    if isinstance(prelude, list):
        context["context_frame_count"] = len(prelude)


def empty_context_stats() -> dict[str, int]:
    return {
        "context_frame_original_count": 0,
        "context_frame_minimized_count": 0,
        "context_frame_removed_count": 0,
        "context_minimized_event_count": 0,
    }


def trace_data_with_records(trace_view: dict[str, Any], records: list[dict[str, Any]]) -> Any:
    if trace_view["container"] == "root_list":
        return list(records)
    copied = dict(trace_view["data"])
    copied[trace_view["key"]] = list(records)
    return copied


def write_minimized_trace(
    *,
    best: dict[str, Any] | None,
    out_trace: str,
    root: Path,
) -> dict[str, Any]:
    if not out_trace:
        return {"path": "", "written": False, "errors": []}
    path = resolve_path(out_trace, root=root)
    if not best or best.get("data") is None:
        return {
            "path": display_path(path, root=root),
            "written": False,
            "errors": ["no trace candidate preserved the minimization predicate"],
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    data = best["data"]
    if path.suffix.lower() == ".jsonl" and isinstance(data, list):
        path.write_text(
            "".join(json.dumps(item, sort_keys=True) + "\n" for item in data),
            encoding="utf-8",
            newline="\n",
        )
    elif path.suffix.lower() == ".jsonl" and isinstance(data, dict) and isinstance(data.get("events"), list):
        path.write_text(
            "".join(json.dumps(item, sort_keys=True) + "\n" for item in data["events"]),
            encoding="utf-8",
            newline="\n",
        )
    else:
        path.write_text(
            json.dumps(data, indent=2, sort_keys=True),
            encoding="utf-8",
            newline="\n",
        )
    return {"path": display_path(path, root=root), "written": True, "errors": []}


def build_evidence_minimization_steps(evidence_minimization: dict[str, Any]) -> list[dict[str, Any]]:
    if not evidence_minimization.get("attempted"):
        return []
    steps: list[dict[str, Any]] = []
    commands = string_items(evidence_minimization.get("commands"))
    if not commands:
        path = str(evidence_minimization.get("out_trace", "")) or "<minimized-trace.json>"
        commands = [
            f"python -m tools.debugger trace-index --trace {path}",
            f"python -m tools.debugger expect --trace {path} --expect <expectation>",
        ]
    for command in commands:
        if " dynamic-taint " in f" {command} ":
            phase = "taint"
        elif " replay " in f" {command} " or " watch " in f" {command} ":
            phase = "replay"
        elif " expect " in f" {command} ":
            phase = "verify"
        elif " localize " in f" {command} ":
            phase = "localize"
        elif " setup " in f" {command} ":
            phase = "setup"
        else:
            phase = "minimize"
        add_step(
            steps,
            phase,
            command,
            "Use the minimized evidence artifact and preserved runtime targets for follow-up proof.",
        )
    return unique_steps(steps)


def build_input_log_minimization_steps(input_log_minimization: dict[str, Any]) -> list[dict[str, Any]]:
    if not input_log_minimization.get("attempted"):
        return []
    steps: list[dict[str, Any]] = []
    for command in string_items(input_log_minimization.get("commands")):
        if " replay " in f" {command} " or " investigate " in f" {command} ":
            phase = "replay"
        elif " ingest " in f" {command} ":
            phase = "ingest"
        else:
            phase = "minimize"
        add_step(
            steps,
            phase,
            command,
            "Use the minimized input log with replay or investigation before treating it as a reduced playtest repro.",
        )
    return unique_steps(steps)


def build_state_patch_minimization_steps(state_patch_minimization: dict[str, Any]) -> list[dict[str, Any]]:
    if not state_patch_minimization.get("attempted"):
        return []
    steps: list[dict[str, Any]] = []
    phase_by_command = {
        " expect ": "verify",
        " replay ": "replay",
        " dynamic-taint ": "explain",
        " compare ": "compare",
        " content-mirror ": "compare",
        " content-scenarios ": "generate",
        " damage_debugger.": "verify",
        " boss_ai_debugger ": "prove",
        " provenance ": "explain",
        " taint ": "explain",
        " slice ": "static",
    }
    for command in string_items(state_patch_minimization.get("commands")):
        phase = next(
            (name for needle, name in phase_by_command.items() if needle in f" {command} "),
            "minimize",
        )
        add_step(
            steps,
            phase,
            command,
            "Verify the minimized state patch evidence before using it as a replay or mirror artifact.",
        )
    return unique_steps(steps)


def build_precondition_minimization_steps(precondition_minimization: dict[str, Any]) -> list[dict[str, Any]]:
    if not precondition_minimization.get("attempted"):
        return []
    steps: list[dict[str, Any]] = []
    by_scenario: dict[str, list[dict[str, Any]]] = {}
    for precondition in precondition_minimization.get("selected_preconditions", []):
        by_scenario.setdefault(str(precondition.get("scenario_id", "")), []).append(precondition)
    for scenario_id, preconditions in list(by_scenario.items())[:8]:
        if not scenario_id or not preconditions:
            continue
        source = report_source_from_scenario_source(str(preconditions[0].get("source", "")))
        first_kind = str(preconditions[0].get("kind", "<kind>"))
        add_step(
            steps,
            "verify",
            f"python -m tools.debugger expect --report {source} --expect scenario={scenario_id} --expect precondition={first_kind},scenario={scenario_id}",
            "Prove the reduced content scenario still carries its required runtime state precondition.",
        )
        add_step(
            steps,
            "setup",
            f"python -m tools.debugger setup --report {source} --scenario-id {scenario_id}",
            "Materialize the selected scenario preconditions into concrete runtime setup and watch requirements.",
        )
        add_step(
            steps,
            "replay",
            f"python -m tools.debugger replay --report {source} --scenario-id {scenario_id}",
            "Replay the selected content scenario through the same focused runtime route.",
        )
    return unique_steps(steps)


def report_source_from_scenario_source(source: str) -> str:
    return source.removesuffix("#scenarios") or "<content_scenarios.json>"


def infer_surfaces(
    *,
    symbols: tuple[str, ...],
    changed_files: tuple[str, ...],
    scenario_source_files: tuple[str, ...],
    symptom: str,
    signals: list[dict[str, Any]],
) -> list[str]:
    surfaces: set[str] = set()
    signal_text = [
        item["value"]
        for item in signals
        if item["kind"] != "scenario" or item["type"] == "explicit_scenario"
    ]
    text = " ".join([symptom, *symbols, *changed_files, *scenario_source_files, *signal_text]).lower()
    if any(hint.lower() in text for hint in DAMAGE_SYMBOL_HINTS) or any(
        keyword in text for keyword in SURFACE_KEYWORDS["damage"]
    ):
        surfaces.add("damage")
    if any(hint.lower() in text for hint in BOSS_AI_SYMBOL_HINTS) or any(
        keyword in text for keyword in SURFACE_KEYWORDS["boss_ai"]
    ):
        surfaces.add("boss_ai")
    if "content_scenario_" in text:
        surfaces.add("content_static")
    if not surfaces:
        for path in (*changed_files, *scenario_source_files):
            normalized = normalize_path(path).lower()
            if normalized.startswith(("maps/", "gfx/", "audio/", "data/")):
                surfaces.add("content_static")
    return sorted(surfaces or {"general"})


def build_minimization_steps(
    *,
    surfaces: list[str],
    scenario_paths: list[str],
    selected_ids: list[str],
    bug_ids: tuple[str, ...],
    symbols: tuple[str, ...],
    changed_files: tuple[str, ...],
    scenario_source_files: tuple[str, ...],
    symptom: str,
    subset_path: str,
) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    scenario_source = subset_path or (scenario_paths[0] if scenario_paths else "<scenarios.jsonl>")
    scenario_id = selected_ids[0] if selected_ids else "<id>"
    if "boss_ai" in surfaces:
        add_step(
            steps,
            "extract",
            f"python -m tools.debugger minimize --scenario {scenario_source} --scenario-id {scenario_id} --out-scenarios .local\\tmp\\debugger_minimized_candidates.jsonl",
            "Keep a small candidate scenario set before running expensive ROM materialization.",
        )
        add_step(
            steps,
            "counterfactual",
            f"python -m tools.boss_ai_debugger counterfactual --scenario {scenario_source} --scenario-id {scenario_id}",
            "Explain which public facts would flip the policy verdict.",
        )
        add_step(
            steps,
            "minimize",
            f"python -m tools.boss_ai_debugger minimize --scenario {scenario_source} --scenario-id {scenario_id} --json-out .local\\tmp\\boss_ai_minimized_{safe_name(scenario_id)}.json",
            "Run the Boss AI semantic scenario minimizer.",
        )
        add_step(
            steps,
            "prove",
            f"python -m tools.boss_ai_debugger rom-score-materialize --scenarios {scenario_source} --limit 4 --compare-fast-score",
            "Materialize minimized scenarios before treating Python policy behavior as ROM behavior.",
        )
    if "damage" in surfaces:
        bug_id = bug_ids[0] if bug_ids else "<bug_id>"
        add_step(
            steps,
            "find",
            "python -m tools.damage_debugger.find <scenario>",
            "Locate the concrete damage-debugger scenario that reproduces the symptom.",
        )
        add_step(
            steps,
            "minimize",
            f"python -m tools.damage_debugger.minimize --bug {bug_id}",
            "Run the damage-axis ddmin reducer for the bug id.",
        )
        add_step(
            steps,
            "replay",
            "python -m tools.damage_debugger.replay --scenario <scenario> --watch wCurDamage --json",
            "Use snapshot-ring replay to prove the minimal state transition.",
        )
    if "content_static" in surfaces or "general" in surfaces:
        static_paths = tuple(unique_list([*changed_files, *scenario_source_files]))[:3] or ("<changed_file>",)
        for path in static_paths:
            add_step(
                steps,
                "static",
                f"python -m tools.debugger slice --source-file {path}",
                "Reduce the suspect surface to touched labels and static references.",
            )
            add_step(
                steps,
                "verify",
                f"python -m tools.debugger gate --changed-file {path}",
                "Run the broad romhack gates until this surface has a dedicated reducer.",
            )
    if not steps:
        suggestions = suggest_tests(
            changed_files=changed_files,
            symbols=symbols,
            symptom=symptom,
        )
        for command in suggestions.get("counterexample_commands", []):
            add_step(steps, "minimize", command, "Fallback counterexample command from test suggestions.")
    return unique_steps(steps)


def add_step(steps: list[dict[str, Any]], phase: str, command: str, reason: str) -> None:
    steps.append(
        {
            "phase": phase,
            "command": command,
            "reason": reason,
            "runnable": command_is_runnable(command),
        }
    )


def signal(
    signal_type: str,
    kind: str,
    value: str,
    weight: int,
    source: str,
) -> dict[str, Any]:
    return {
        "type": signal_type,
        "kind": kind,
        "value": value,
        "weight": weight,
        "source": source,
    }


def merge_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in signals:
        key = (item["type"], item["kind"], item["value"])
        if key not in merged:
            merged[key] = dict(item)
            continue
        merged[key]["weight"] = max(int(merged[key]["weight"]), int(item["weight"]))
    return sorted(merged.values(), key=lambda item: (-int(item["weight"]), item["kind"], item["value"]))


def scenario_id_for(record: dict[str, Any]) -> str:
    for key in ("id", "scenario_id"):
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def is_scenario_record(data: dict[str, Any], scenario_id: str) -> bool:
    text = str(scenario_id)
    if not text:
        return False
    kind = str(data.get("kind", "")).lower()
    if "scenario" in kind:
        return True
    if data.get("scenario_type") or data.get("family") in {"content_static", "damage", "boss_ai"}:
        return True
    return text.startswith(("content_scenario_", "debugger_generated_", "scenario_"))


def ids_by_type(signals: list[dict[str, Any]], kind: str) -> set[str]:
    return {item["value"] for item in signals if item["kind"] == kind and item["value"]}


def unique_list(values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def unique_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for step in steps:
        command = step["command"]
        if command in seen:
            continue
        seen.add(command)
        out.append(step)
    return out


def safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in value)
