from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .coverage import load_traces
from .expect import (
    collect_evidence,
    evaluate_expectation,
    input_expectations,
    load_expectation_files,
    normalize_expectations,
    parse_cli_expectation,
    string_items,
)
from .localize import dict_items, normalize_path
from .provenance import display_path, parse_symbol_table, resolve_path
from .reporting import load_reports
from .testgen import suggest_tests
from .trace_index import build_symbol_address_index, extract_trace_events, finalize_events
from .workflow import command_is_runnable


BOSS_AI_SYMBOL_HINTS = (
    "BossAI_",
    "wEnemyAIMoveScores",
)
DAMAGE_SYMBOL_HINTS = (
    "wCurDamage",
    "BattleCommand_Damage",
    "BattleCommand_Stab",
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
    out_state_report: str = "",
    execute_state_patches: bool = False,
    symbols_path: str = "pokegold.sym",
    max_scenarios: int = 20,
    max_trace_records: int = 200,
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    loaded_traces, trace_errors = load_traces(traces=traces, root=root)
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
    errors = [
        *report_errors,
        *trace_errors,
        *scenario_errors,
        *subset_output.get("errors", []),
        *state_patch_minimization.get("errors", []),
        *evidence_minimization.get("errors", []),
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
        "known_limits": [
            "This command can extract scenario subsets, minimize content-state or explicit generic state-space WRAM patch sets against explicit expectations, and minimize arbitrary trace evidence; deeper semantic ddmin still runs in focused subsystem tools where they exist.",
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
    if not out_scenarios:
        return {"path": "", "written": False, "record_count": 0, "errors": []}
    path = resolve_path(out_scenarios, root=root)
    if not selected_rows:
        return {
            "path": display_path(path, root=root),
            "written": False,
            "record_count": 0,
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
        "errors": [],
    }


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

    results = [
        minimize_state_patch_view(
            view,
            expectations=all_expectations,
            execute_state_patches=execute_state_patches,
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
    commands = state_patch_minimization_commands(
        out_report=str(output.get("path", "")),
        source=str(best.get("source", "")) if best else "",
        scenario_ids=string_items(best.get("scenario_ids")) if best else [],
        expectations=all_expectations,
    )
    return {
        "attempted": True,
        "preserved": best is not None and not errors,
        "report_count": len(loaded_reports),
        "content_state_report_count": count_state_patch_views(views, "content_state"),
        "state_space_report_count": count_state_patch_views(views, "generic_state_space"),
        "expectation_count": len(all_expectations),
        "execute_state_patches": execute_state_patches,
        "execution_attempt_count": sum(int(result.get("execution_attempt_count", 0)) for result in results),
        "executed_candidate_count": sum(int(result.get("executed_candidate_count", 0)) for result in results),
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
        "scenario_ids": string_items(best.get("scenario_ids")) if best else [],
        "symbols": string_items(best.get("symbols")) if best else [],
        "source_files": string_items(best.get("source_files")) if best else [],
        "out_report": output.get("path", ""),
        "written": bool(output.get("written")),
        "result_count": len(results),
        "results": [public_state_patch_minimize_result(result) for result in results[:12]],
        "commands": commands,
        "errors": errors,
        "known_limits": [
            "Patch minimization preserves explicit expectations over content-state or generic state-space report evidence; with --execute-state-patches, explicit generic state-space candidate subsets are materialized before their expectations are evaluated.",
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
    root: Path,
) -> dict[str, Any]:
    patch_locations = list(view["patches"])
    candidate_executions: list[dict[str, Any]] = []

    def predicate(candidate_locations: list[dict[str, Any]]) -> bool:
        data, execution = state_patch_candidate_report(
            view,
            candidate_locations,
            execute_state_patches=execute_state_patches,
            candidate_index=len(candidate_executions) + 1,
            root=root,
        )
        if execution.get("attempted"):
            candidate_executions.append(execution)
            if not execution.get("executed"):
                return False
        return state_patch_expectations_pass(data, source=str(view["source"]), expectations=expectations)

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
            root=root,
        )
        if final_execution.get("attempted"):
            candidate_executions.append(final_execution)
            final_preserved = bool(final_execution.get("executed"))
        if final_preserved:
            final_preserved = state_patch_expectations_pass(
                minimized_data,
                source=str(view["source"]),
                expectations=expectations,
            )
    return {
        "source": view["source"],
        "view_kind": view.get("view_kind", "content_state"),
        "preserved": bool(final_preserved),
        "execution_mode": "emulator" if any(item.get("attempted") for item in candidate_executions) else "evidence",
        "execution_attempt_count": len([item for item in candidate_executions if item.get("attempted")]),
        "executed_candidate_count": len([item for item in candidate_executions if item.get("executed")]),
        "execution_errors": unique_list(
            error
            for item in candidate_executions
            for error in string_items(item.get("errors"))
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
        "data": minimized_data if final_preserved else None,
    }


def state_patch_expectations_pass(data: dict[str, Any], *, source: str, expectations: list[dict[str, Any]]) -> bool:
    evidence = collect_evidence(
        loaded_reports=[{"source": source, "data": data}],
        loaded_sources=[],
        trace_index={"kind": "unified_debugger_trace_index", "valid": True, "events": [], "errors": [], "warnings": []},
    )
    results = [evaluate_expectation(expectation, evidence=evidence) for expectation in expectations]
    return bool(results) and all(result["status"] == "passed" for result in results)


def state_patch_candidate_report(
    view: dict[str, Any],
    locations: list[dict[str, Any]],
    *,
    execute_state_patches: bool,
    candidate_index: int,
    root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    data = state_patch_report_with_patch_locations(view, locations)
    if not execute_state_patches or view.get("view_kind") != "generic_state_space":
        return data, {"attempted": False}
    if data.get("kind") != "unified_debugger_state_space":
        return data, {
            "attempted": False,
            "reason": "only unified_debugger_state_space reports can be execution-minimized",
        }
    return execute_generic_state_patch_candidate(
        data,
        source=str(view.get("source", "")),
        candidate_index=candidate_index,
        root=root,
    )


def execute_generic_state_patch_candidate(
    data: dict[str, Any],
    *,
    source: str,
    candidate_index: int,
    root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    from .state_space import execute_state_space

    context, context_errors = generic_state_execution_context(
        data,
        source=source,
        candidate_index=candidate_index,
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
    state_space = out.setdefault("state_space", {})
    if isinstance(state_space, dict):
        state_space["out_state"] = str(execution.get("out_state", ""))
        state_space["patches"] = list(execution.get("applied_patches") or patches)
        state_space["patch_count"] = len(state_space["patches"])
    out["patch_count"] = len(execution.get("applied_patches") or patches)
    out["minimized_evidence_view"] = True
    out["minimized_execution_view"] = True
    out.setdefault("warnings", [])
    if isinstance(out["warnings"], list):
        out["warnings"] = unique_list(
            [
                *string_items(out["warnings"]),
                "minimized generic state-space candidate was materialized before expectation evaluation",
            ]
        )
        out["warning_count"] = len(out["warnings"])
    return out, {
        "attempted": True,
        "executed": bool(execution.get("executed")),
        "candidate_index": candidate_index,
        "patch_count": len(patches),
        "out_state": str(execution.get("out_state", "")),
        "errors": list(execution.get("errors", [])),
        "warnings": list(execution.get("warnings", [])),
    }


def generic_state_execution_context(
    data: dict[str, Any],
    *,
    source: str,
    candidate_index: int,
    root: Path,
) -> tuple[dict[str, Path], list[str]]:
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
    rom_text = str(data.get("rom") or data.get("rom_path") or "pokegold.gbc")
    base_text = str(
        data.get("base_save_state")
        or state_space.get("base_save_state")
        or execution.get("base_save_state")
        or ""
    )
    rom = resolve_path(rom_text, root=root)
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
) -> list[str]:
    report = out_report or source or "<content_state.json>"
    commands = [
        f"python -m tools.debugger expect --report {report} --expect {expectation_cli(expectation)}"
        for expectation in expectations[:8]
        if expectation_cli(expectation)
    ]
    for scenario_id in scenario_ids[:4]:
        commands.append(f"python -m tools.debugger replay --report {report} --scenario-id {scenario_id} --execute-watch")
    commands.append(f"python -m tools.debugger compare --report {report}")
    return unique_list(commands)


def expectation_cli(expectation: dict[str, Any]) -> str:
    expectation_type = str(expectation.get("type", ""))
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
        return f"address={expectation['address']}"
    return str(expectation.get("description") or expectation.get("id") or "")


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
    path = str(evidence_minimization.get("out_trace", "")) or "<minimized-trace.json>"
    steps: list[dict[str, Any]] = []
    add_step(
        steps,
        "minimize",
        f"python -m tools.debugger trace-index --trace {path}",
        "Inspect the minimized generic evidence trace.",
    )
    add_step(
        steps,
        "verify",
        f"python -m tools.debugger expect --trace {path} --expect <expectation>",
        "Re-run the expectation gate on the reduced trace before using it as a repro artifact.",
    )
    return steps


def build_state_patch_minimization_steps(state_patch_minimization: dict[str, Any]) -> list[dict[str, Any]]:
    if not state_patch_minimization.get("attempted"):
        return []
    steps: list[dict[str, Any]] = []
    phase_by_command = {
        " expect ": "verify",
        " replay ": "replay",
        " compare ": "compare",
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
