from __future__ import annotations

from pathlib import Path
from typing import Any

from .catalog import ROOT, keyword_matches, triage_request
from .mirrors import build_compare_plan
from .provenance import parse_symbol_table, resolve_path
from .reporting import load_reports
from .slicing import build_slice_report
from .testgen import suggest_tests
from .workflow import build_gate_plan, command_address_arg, command_is_runnable


PHASE_TITLES = {
    "reproduce": "Reproduce the symptom",
    "observe": "Observe the suspected state",
    "slice": "Map likely code/data contributors",
    "compare": "Compare ROM behavior to expectations",
    "minimize": "Minimize to a counterexample",
    "verify": "Verify the fix",
}
SYMPTOM_HINTS = {
    "damage": (("symbol", "wCurDamage", 55),),
    "hp": (("symbol", "wCurDamage", 45),),
    "type": (
        ("symbol", "BattleCheckTypeMatchup", 68),
        ("symbol", "wTypeMatchup", 64),
        ("symbol", "TypeMatchups", 56),
        ("file", "engine/battle/effect_commands.asm", 62),
        ("file", "data/types/type_matchups.asm", 54),
    ),
    "type matchup": (
        ("symbol", "BattleCheckTypeMatchup", 78),
        ("symbol", "CheckTypeMatchup", 70),
        ("symbol", "wTypeMatchup", 74),
        ("symbol", "TypeMatchups", 64),
        ("file", "engine/battle/effect_commands.asm", 72),
        ("file", "data/types/type_matchups.asm", 64),
    ),
    "type effectiveness": (
        ("symbol", "BattleCheckTypeMatchup", 74),
        ("symbol", "wTypeMatchup", 70),
        ("file", "engine/battle/effect_commands.asm", 68),
        ("file", "data/types/type_matchups.asm", 60),
    ),
    "matchup": (
        ("symbol", "BattleCheckTypeMatchup", 66),
        ("symbol", "wTypeMatchup", 62),
        ("file", "engine/battle/effect_commands.asm", 58),
    ),
    "immune": (
        ("symbol", "BattleCheckTypeMatchup", 64),
        ("symbol", "wTypeMatchup", 62),
        ("file", "engine/battle/effect_commands.asm", 58),
    ),
    "immunity": (
        ("symbol", "BattleCheckTypeMatchup", 66),
        ("symbol", "wTypeMatchup", 64),
        ("file", "engine/battle/effect_commands.asm", 60),
    ),
    "ground": (
        ("symbol", "BattleCheckTypeMatchup", 58),
        ("symbol", "wTypeMatchup", 56),
        ("file", "data/types/type_matchups.asm", 54),
    ),
    "air balloon": (
        ("symbol", "BattleCheckTypeMatchup", 74),
        ("symbol", "wTypeMatchup", 70),
        ("file", "engine/battle/late_gen_held_items.asm", 82),
        ("file", "engine/battle/effect_commands.asm", 64),
    ),
    "balloon": (
        ("symbol", "BattleCheckTypeMatchup", 60),
        ("symbol", "wTypeMatchup", 58),
        ("file", "engine/battle/late_gen_held_items.asm", 72),
    ),
    "held item": (
        ("file", "engine/battle/late_gen_held_items.asm", 64),
        ("symbol", "wTypeMatchup", 42),
    ),
    "item": (
        ("file", "engine/battle/late_gen_held_items.asm", 48),
    ),
    "passive": (
        ("file", "engine/battle/type_passive_damage_mods.asm", 62),
        ("symbol", "wTypeMatchup", 48),
    ),
    "ability": (
        ("file", "engine/battle/type_passive_damage_mods.asm", 58),
        ("symbol", "wTypeMatchup", 44),
    ),
    "boss": (
        ("symbol", "BossAI_SelectMove", 45),
        ("file", "engine/battle/ai/boss_policy_move.asm", 40),
    ),
    "ai": (
        ("symbol", "BossAI_SelectMove", 45),
        ("file", "engine/battle/ai/boss_policy_move.asm", 40),
    ),
    "score": (("symbol", "wEnemyAIMoveScores", 45),),
    "switch": (("symbol", "BossAI_SwitchOrTryItem", 45),),
    "bank": (("symbol", "hROMBank", 45),),
    "farcall": (("symbol", "FarCall", 45),),
}


def build_localization_plan(
    *,
    changed_files: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    addresses: tuple[str, ...] = (),
    watch_size: int = 1,
    symptom: str = "",
    reports: tuple[str, ...] = (),
    symbols_path: str = "pokegold.sym",
    max_candidates: int = 20,
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_reports, load_errors = load_reports(reports=reports, root=root)
    effective_watch_size = localization_watch_size(
        requested=watch_size,
        loaded_reports=loaded_reports,
    )
    sym_path = resolve_path(symbols_path, root=root)
    symbol_table = parse_symbol_table(sym_path) if sym_path.exists() else {}
    address_symbols = symbols_for_addresses(addresses, symbol_table=symbol_table)
    signals = collect_signals(
        changed_files=changed_files,
        symbols=symbols,
        addresses=addresses,
        address_symbols=address_symbols,
        symptom=symptom,
        loaded_reports=loaded_reports,
    )
    candidate_scores = score_candidates(signals)
    candidate_symbols = top_names(candidate_scores["symbols"], max_candidates)
    candidate_files = top_names(candidate_scores["files"], max_candidates)
    candidate_addresses = top_names(candidate_scores["addresses"], max_candidates)

    if candidate_symbols or candidate_files:
        slice_report = build_slice_report(
            symbols_path=symbols_path,
            reports=reports,
            symbols=tuple(candidate_symbols),
            source_files=tuple(candidate_files),
            max_depth=2,
            max_edges=24,
            root=root,
        )
        signals.extend(signals_from_slice(slice_report))
        candidate_scores = score_candidates(signals)
        candidate_symbols = top_names(candidate_scores["symbols"], max_candidates)
        candidate_files = top_names(candidate_scores["files"], max_candidates)
        candidate_addresses = top_names(candidate_scores["addresses"], max_candidates)
    else:
        slice_report = None

    workflow_files = tuple(changed_files)
    workflow_symbols = tuple(symbols)
    if not symptom:
        workflow_files = tuple(candidate_files or changed_files)
        workflow_symbols = tuple(candidate_symbols or symbols)

    triage = triage_request(
        changed_files=workflow_files,
        symptom=symptom,
        root=root,
    )
    tests = suggest_tests(
        changed_files=workflow_files,
        symbols=workflow_symbols,
        symptom=symptom,
        root=root,
    )
    compare = build_compare_plan(
        changed_files=workflow_files,
        symbols=workflow_symbols,
        symptom=symptom,
        root=root,
    )
    gate = build_gate_plan(
        changed_files=workflow_files,
        symptom=symptom,
        root=root,
    )

    candidates = build_candidates(
        symbol_scores=candidate_scores["symbols"],
        file_scores=candidate_scores["files"],
        address_scores=candidate_scores["addresses"],
        signals=signals,
        max_candidates=max_candidates,
    )
    phase_steps = build_phase_steps(
        symbols=tuple(candidate_symbols or symbols),
        changed_files=tuple(candidate_files or changed_files),
        addresses=tuple(candidate_addresses or addresses),
        watch_size=effective_watch_size,
        reports=reports,
        triage=triage,
        tests=tests,
        compare=compare,
        gate=gate,
    )
    errors = list(load_errors)
    if slice_report:
        errors.extend(slice_report.get("errors", []))

    return {
        "schema_version": 1,
        "kind": "unified_debugger_localization_plan",
        "root": str(root),
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
        "changed_files": list(changed_files),
        "symbols": list(symbols),
        "addresses": list(addresses),
        "watch_size": effective_watch_size,
        "symptom": symptom,
        "input_reports": [item["source"] for item in loaded_reports],
        "signal_count": len(signals),
        "signals": signals[:120],
        "candidate_count": len(candidates),
        "candidates": candidates,
        "triage_match_ids": [match["id"] for match in triage["matches"]],
        "phase_steps": phase_steps,
        "commands": unique_commands(
            step["command"]
            for phase in phase_steps
            for step in phase["steps"]
        ),
        "runnable_commands": unique_commands(
            step["command"]
            for phase in phase_steps
            for step in phase["steps"]
            if step["runnable"]
        ),
        "blocked_commands": unique_commands(
            step["command"]
            for phase in phase_steps
            for step in phase["steps"]
            if not step["runnable"]
        ),
        "known_limits": [
            "This command plans localization and minimization; it does not prove dynamic causality by itself.",
            "Treat static slice candidates as suspects until confirmed by watch, replay, trace, taint, or subsystem materialization.",
        ],
    }


def localization_watch_size(*, requested: int, loaded_reports: list[dict[str, Any]]) -> int:
    sizes = [positive_int(requested)]
    for loaded in loaded_reports:
        sizes.extend(report_watch_sizes(loaded.get("data", {})))
    return max([size for size in sizes if size > 0] or [1])


def report_watch_sizes(data: Any) -> list[int]:
    sizes: list[int] = []
    if isinstance(data, dict):
        for key in ("watch_size", "sink_size"):
            size = positive_int(data.get(key))
            if size:
                sizes.append(size)
        if watch_like_record(data):
            size = positive_int(data.get("size"))
            if size:
                sizes.append(size)
        for value in data.values():
            sizes.extend(report_watch_sizes(value))
    elif isinstance(data, list):
        for item in data:
            sizes.extend(report_watch_sizes(item))
    return sizes


def watch_like_record(data: dict[str, Any]) -> bool:
    if data.get("address_watch"):
        return True
    return any(key in data for key in ("watch", "watch_address", "sink_address", "raw")) and any(
        key in data for key in ("address", "bank_address", "size")
    )


def positive_int(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return number if number > 0 else 0


def collect_signals(
    *,
    changed_files: tuple[str, ...],
    symbols: tuple[str, ...],
    addresses: tuple[str, ...],
    address_symbols: dict[str, list[str]],
    symptom: str,
    loaded_reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for path in changed_files:
        signals.append(signal("explicit_change", file=normalize_path(path), weight=80))
    for symbol in symbols:
        signals.append(signal("explicit_symbol", symbol=symbol, weight=80))
    for address in addresses:
        signals.append(signal("explicit_address", address=address, note=address, weight=78))
        for symbol_name in address_symbols.get(address, [])[:6]:
            signals.append(
                signal(
                    "address_resolved_symbol",
                    symbol=symbol_name,
                    address=address,
                    note=f"{address} resolves to {symbol_name}",
                    weight=82,
                )
            )
    if symptom:
        signals.append(signal("symptom", note=symptom, weight=35))
        signals.extend(signals_from_symptom(symptom))
    for loaded in loaded_reports:
        source = loaded["source"]
        report = loaded["data"]
        signals.extend(signals_from_report(report, source=source))
    return merge_duplicate_signals(signals)


def signals_from_report(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    kind = report.get("kind", "")
    out: list[dict[str, Any]] = []
    if kind == "unified_debugger_watch_report":
        for event in dict_items(report.get("events")):
            out.append(
                signal(
                    "watch_hit",
                    symbol=str(event.get("watch", "")),
                    routine=str(event.get("pc_label", "")),
                    note=f"{event.get('old_hex')} -> {event.get('new_hex')} at {event.get('pc_bank_address')}",
                    source=source,
                    weight=95,
                )
            )
        for watch in dict_items(report.get("watches")):
            out.append(
                signal(
                    "watch_symbol",
                    symbol=str(watch.get("name", "")),
                    source=source,
                    weight=45,
                )
            )
    elif kind == "unified_debugger_causal_slice":
        out.extend(signals_from_slice(report, source=source))
    elif kind == "unified_debugger_provenance_report":
        for symbol in dict_items(report.get("symbols")):
            out.append(
                signal(
                    "provenance_symbol",
                    symbol=str(symbol.get("query", "")),
                    source=source,
                    weight=45,
                )
            )
            for related in symbol.get("related_files", []):
                out.append(signal("provenance_file", file=related, source=source, weight=35))
        for source_file in dict_items(report.get("source_files")):
            out.append(
                signal(
                    "provenance_source",
                    file=str(source_file.get("path", "")),
                    source=source,
                    weight=40,
                )
            )
    elif kind == "unified_debugger_gate_plan":
        for step in dict_items(report.get("steps")):
            if step.get("status") == "failed":
                out.append(
                    signal(
                        "gate_failure",
                        note=str(step.get("command", "")),
                        source=source,
                        weight=90,
                    )
                )
    elif kind == "unified_debugger_ranked_findings":
        for finding in dict_items(report.get("findings")):
            severity = int(finding.get("severity", 30))
            out.append(
                signal(
                    "ranked_finding",
                    note=str(finding.get("title", "")),
                    source=source,
                    weight=min(100, severity),
                )
            )
    elif kind == "unified_debugger_trace_index":
        out.extend(signals_from_trace_index(report, source=source))
    elif kind == "unified_debugger_expectation_report":
        out.extend(signals_from_expectations(report, source=source))
    elif kind == "unified_debugger_minimization_plan":
        out.extend(signals_from_minimization(report, source=source))
    elif kind in {"unified_debugger_taint_report", "unified_debugger_dynamic_taint_report"}:
        out.extend(signals_from_taint(report, source=source))
    elif kind == "unified_debugger_instruction_trace":
        out.extend(signals_from_instruction_trace(report, source=source))
    elif kind in {"unified_debugger_compare_plan", "unified_debugger_test_suggestions"}:
        for match in dict_items(report.get("matches")):
            weight = 55 if match.get("id") != "uncovered_surface" else 35
            note = str(match.get("id", ""))
            out.append(
                signal(
                    "tool_match",
                    note=note,
                    source=source,
                    weight=weight,
                )
            )
            for path in string_items(match.get("source_files")):
                out.append(signal("tool_match_source", file=normalize_path(path), note=note, source=source, weight=weight + 10))
            for symbol in string_items(match.get("related_symbols")):
                out.append(signal("tool_match_symbol", symbol=symbol, note=note, source=source, weight=weight + 12))
            for scenario_id in string_items(match.get("scenario_ids")):
                out.append(signal("tool_match_scenario", note=scenario_id, source=source, weight=weight + 6))
    elif kind == "unified_debugger_content_mirror":
        out.extend(signals_from_content_mirror(report, source=source))
    elif kind == "unified_debugger_content_scenarios":
        out.extend(signals_from_content_scenarios(report, source=source))
    elif kind == "unified_debugger_fuzz_plan":
        out.extend(signals_from_fuzz_campaigns(report, source=source))
        out.extend(signals_from_content_fuzz_cases(report, source=source))
    elif kind == "unified_debugger_ingest_manifest":
        for artifact in dict_items(report.get("artifacts")):
            if artifact.get("kind") == "source_change":
                out.append(
                    signal(
                        "ingested_change",
                        file=str(artifact.get("path", "")),
                        source=source,
                        weight=65,
                    )
                )
            for error in artifact.get("errors", []):
                out.append(signal("artifact_error", note=str(error), source=source, weight=85))
    out.extend(raw_address_signals_from_report(report, source=source))
    return [item for item in out if item.get("symbol") or item.get("file") or item.get("address") or item.get("note")]


def raw_address_signals_from_report(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = address_signals_from_mapping(report, source=source, weight=58, signal_type="report_address")
    for key in (
        "events",
        "findings",
        "items",
        "write_attributions",
        "targets",
        "watches",
        "sample_records",
    ):
        for item in dict_items(report.get(key)):
            out.extend(
                address_signals_from_mapping(
                    item,
                    source=source,
                    weight=66,
                    signal_type=f"{key.rstrip('s')}_address",
                )
            )
    return out


def address_signals_from_mapping(
    item: dict[str, Any],
    *,
    source: str,
    weight: int,
    signal_type: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for key in ("address", "bank_address", "pc_bank_address", "score_pointer", "target"):
        value = item.get(key)
        if value is not None and address_match_key(str(value)):
            address = str(value)
            out.append(signal(signal_type, address=address, note=f"{key}={address}", source=source, weight=weight))
    for key in ("addresses", "related_addresses", "watch_addresses", "sink_addresses"):
        for address in string_items(item.get(key)):
            if address_match_key(address):
                out.append(signal(signal_type, address=address, note=f"{key}={address}", source=source, weight=weight))
    return out


def signals_from_content_mirror(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for mirror in dict_items(report.get("rom_mirrors")):
        status = str(mirror.get("status", ""))
        if status not in {"passed", "failed"}:
            continue
        weight = 94 if status == "failed" else 76
        note = str(mirror.get("title") or mirror.get("id") or "ROM mirror evidence")
        source_file = str(mirror.get("source_file", ""))
        if source_file:
            out.append(signal("content_rom_mirror_file", file=source_file, note=note, source=source, weight=weight))
        for path in string_items(mirror.get("related_files")):
            if looks_like_source_path(path):
                out.append(signal("content_rom_mirror_related_file", file=path, note=note, source=source, weight=max(40, weight - 8)))
        for symbol_name in string_items(mirror.get("related_symbols")):
            out.append(signal("content_rom_mirror_symbol", symbol=symbol_name, note=note, source=source, weight=weight))
    return out


def signals_from_content_scenarios(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for scenario in dict_items(report.get("scenarios")):
        out.extend(signals_from_content_runtime_record(scenario, source=source, prefix="content_scenario"))
    return out


def signals_from_content_fuzz_cases(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for case in dict_items(report.get("fuzz_cases")):
        if not case.get("runtime_targets") and not case.get("scenario_type"):
            continue
        out.extend(signals_from_content_runtime_record(case, source=source, prefix="content_fuzz"))
    return out


def signals_from_fuzz_campaigns(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for campaign in dict_items(report.get("campaigns")):
        note = str(campaign.get("id") or campaign.get("title") or "fuzz campaign")
        for symbol_name in string_items(campaign.get("related_symbols")):
            out.append(signal("fuzz_campaign_symbol", symbol=symbol_name, note=note, source=source, weight=74))
        for address in string_items(campaign.get("related_addresses")):
            out.append(signal("fuzz_campaign_address", address=address, note=note, source=source, weight=78))
        for path in string_items(campaign.get("changed_files")):
            if looks_like_source_path(path):
                out.append(signal("fuzz_campaign_file", file=path, note=note, source=source, weight=62))
    return out


def signals_from_content_runtime_record(record: dict[str, Any], *, source: str, prefix: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    scenario_id = str(record.get("scenario_id") or record.get("id") or "content runtime")
    source_file = str(record.get("source_file") or record.get("changed_file") or "")
    if source_file:
        out.append(signal(f"{prefix}_file", file=source_file, note=scenario_id, source=source, weight=62))
    runtime_targets = record.get("runtime_targets") if isinstance(record.get("runtime_targets"), dict) else {}
    for symbol_name in string_items(runtime_targets.get("source_symbols")):
        out.append(signal(f"{prefix}_source_symbol", symbol=symbol_name, note=scenario_id, source=source, weight=64))
    for symbol_name in string_items(runtime_targets.get("script_symbols")):
        out.append(signal(f"{prefix}_script_symbol", symbol=symbol_name, note=scenario_id, source=source, weight=70))
    for symbol_name in string_items(runtime_targets.get("trace_symbols")):
        out.append(signal(f"{prefix}_trace_symbol", symbol=symbol_name, note=scenario_id, source=source, weight=58))
    for symbol_name in string_items(runtime_targets.get("watch_symbols")):
        out.append(signal(f"{prefix}_watch_symbol", symbol=symbol_name, note=scenario_id, source=source, weight=56))
    for symbol_name in string_items(record.get("related_symbols")):
        out.append(signal(f"{prefix}_related_symbol", symbol=symbol_name, note=scenario_id, source=source, weight=52))
    return out


def signals_from_trace_index(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for attribution in dict_items(report.get("reverse_attributions")):
        state = str(attribution.get("state", ""))
        title = str(attribution.get("title", "reverse attribution"))
        out.append(signal("reverse_attribution_state", symbol=state, note=title, source=source, weight=98))
        if attribution.get("source_symbol"):
            out.append(
                signal(
                    "reverse_attribution_source",
                    symbol=str(attribution["source_symbol"]),
                    note=title,
                    source=source,
                    weight=82,
                )
            )
        for contributor in dict_items(attribution.get("contributors"))[:8]:
            contributor_state = str(contributor.get("state", ""))
            out.append(
                signal(
                    "reverse_attribution_contributor",
                    symbol=contributor_state,
                    note=f"{contributor.get('relation', 'contributor')} for {state}",
                    source=source,
                    weight=86,
                )
            )
        for symbol_name in string_items(attribution.get("related_symbols")):
            out.append(signal("reverse_attribution_related_symbol", symbol=symbol_name, source=source, weight=72))
        for path in string_items(attribution.get("related_files")):
            out.append(signal("reverse_attribution_related_file", file=path, source=source, weight=70))

    for event in dict_items(report.get("events")):
        event_type = str(event.get("event_type", "event"))
        weight = 88 if event_type in {"watch_change", "memory_write", "memory_patch", "score_delta"} else 68
        note = event_note(event)
        if event.get("state_symbol"):
            out.append(
                signal(
                    f"trace_{event_type}_state",
                    symbol=str(event["state_symbol"]),
                    note=note,
                    source=source,
                    weight=weight,
                )
            )
        for key in ("source_symbol", "pc_symbol"):
            if event.get(key):
                out.append(
                    signal(
                        f"trace_{event_type}_{key}",
                        symbol=str(event[key]),
                        note=note,
                        source=source,
                        weight=max(45, weight - 14),
                    )
                )
        if event.get("source_file"):
            out.append(
                signal(
                    f"trace_{event_type}_source_file",
                    file=str(event["source_file"]),
                    note=note,
                    source=source,
                    weight=max(45, weight - 10),
                )
            )

    for path in dict_items(report.get("causal_paths")):
        title = str(path.get("title", "causal path"))
        for symbol_name in string_items(path.get("related_symbols")):
            out.append(signal("trace_path_symbol", symbol=symbol_name, note=title, source=source, weight=72))
        for file_name in string_items(path.get("related_files")):
            out.append(signal("trace_path_file", file=file_name, note=title, source=source, weight=68))
        for node in dict_items(path.get("nodes"))[:8]:
            if node.get("symbol"):
                out.append(
                    signal(
                        "trace_path_node",
                        symbol=str(node["symbol"]),
                        note=title,
                        source=source,
                        weight=64,
                    )
                )
            if node.get("file"):
                out.append(
                    signal(
                        "trace_path_node_file",
                        file=str(node["file"]),
                        note=title,
                        source=source,
                        weight=60,
                    )
                )
    return out


def signals_from_expectations(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for result in dict_items(report.get("expectations")):
        expectation = result.get("expectation") if isinstance(result.get("expectation"), dict) else {}
        failed = result.get("status") == "failed"
        weight = 96 if failed else 42
        note = str(result.get("description") or result.get("id") or "expectation")
        symbol = str(expectation.get("symbol") or expectation.get("state_symbol") or "")
        if symbol:
            out.append(
                signal(
                    "failed_expectation_symbol" if failed else "passed_expectation_symbol",
                    symbol=symbol,
                    note=note,
                    source=source,
                    weight=weight,
                )
            )
        if expectation.get("source_file"):
            out.append(
                signal(
                    "failed_expectation_file" if failed else "passed_expectation_file",
                    file=str(expectation["source_file"]),
                    note=note,
                    source=source,
                    weight=max(35, weight - 8),
                )
            )
        if expectation.get("event_type"):
            out.append(
                signal(
                    "failed_expectation_event" if failed else "passed_expectation_event",
                    note=f"{expectation.get('event_type')}: {note}",
                    source=source,
                    weight=max(35, weight - 20),
                )
            )
        for address in expectation_addresses(expectation):
            out.append(
                signal(
                    "failed_expectation_address" if failed else "passed_expectation_address",
                    address=address,
                    note=note,
                    source=source,
                    weight=max(42, weight - 6),
                )
            )
    evidence = report.get("evidence_summary") if isinstance(report.get("evidence_summary"), dict) else {}
    for symbol_name in string_items(evidence.get("symbols")):
        out.append(signal("expectation_evidence_symbol", symbol=symbol_name, source=source, weight=54))
    for path in string_items(evidence.get("source_files")):
        out.append(signal("expectation_evidence_file", file=path, source=source, weight=50))
    for address in string_items(evidence.get("addresses")):
        if address_match_key(address):
            out.append(signal("expectation_evidence_address", address=address, source=source, weight=54))
    return out


def expectation_addresses(expectation: dict[str, Any]) -> list[str]:
    addresses: list[str] = []
    for key in ("address", "bank_address", "watch_address", "sink_address"):
        for address in string_items(expectation.get(key)):
            if address_match_key(address):
                addresses.append(address)
    for key in ("addresses", "related_addresses", "watch_addresses", "sink_addresses"):
        for address in string_items(expectation.get(key)):
            if address_match_key(address):
                addresses.append(address)
    return unique_commands(addresses)


def signals_from_minimization(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    evidence_minimization = report.get("evidence_minimization")
    if isinstance(evidence_minimization, dict) and evidence_minimization.get("preserved"):
        note = (
            f"evidence minimized {evidence_minimization.get('original_count', 0)}"
            f" -> {evidence_minimization.get('minimized_count', 0)}"
        )
        for symbol_name in string_items(report.get("symbols")):
            out.append(signal("minimized_trace_symbol", symbol=symbol_name, note=note, source=source, weight=78))
        if evidence_minimization.get("out_trace"):
            out.append(signal("minimized_trace_output", note=str(evidence_minimization["out_trace"]), source=source, weight=55))
    state_patch_minimization = report.get("state_patch_minimization")
    if isinstance(state_patch_minimization, dict) and state_patch_minimization.get("attempted"):
        preserved = bool(state_patch_minimization.get("preserved"))
        weight = 88 if preserved else 68
        note = (
            f"state patches {state_patch_minimization.get('original_patch_count', 0)}"
            f" -> {state_patch_minimization.get('minimized_patch_count', 0)}"
        )
        if state_patch_minimization.get("out_report"):
            out.append(
                signal(
                    "minimized_state_patch_report",
                    note=str(state_patch_minimization["out_report"]),
                    source=source,
                    weight=max(45, weight - 22),
                )
            )
        for symbol_name in state_patch_minimization_related_symbols(state_patch_minimization):
            out.append(signal("minimized_state_patch_symbol", symbol=symbol_name, note=note, source=source, weight=weight))
        for path in string_items(state_patch_minimization.get("source_files")):
            out.append(signal("minimized_state_patch_file", file=normalize_path(path), note=note, source=source, weight=weight))
        for address in state_patch_minimization_related_addresses(state_patch_minimization):
            if address_match_key(address):
                out.append(signal("minimized_state_patch_address", address=address, note=note, source=source, weight=weight))
    return out


def state_patch_minimization_related_symbols(item: dict[str, Any]) -> list[str]:
    symbols = [
        *string_items(item.get("symbols")),
        *string_items(item.get("source_symbols")),
        *string_items(item.get("watch_symbols")),
        *source_mem_origins(item),
    ]
    for result in dict_items(item.get("results")):
        symbols.extend(string_items(result.get("semantic_watch_symbols")))
        symbols.extend(string_items(result.get("semantic_replay_watch_symbols")))
        symbols.extend(source_mem_origins(result))
    return unique_commands(symbols)


def state_patch_minimization_related_addresses(item: dict[str, Any]) -> list[str]:
    addresses = [
        *string_items(item.get("watch_addresses")),
        *source_mem_addresses(item),
    ]
    for result in dict_items(item.get("results")):
        addresses.extend(string_items(result.get("semantic_watch_addresses")))
        addresses.extend(string_items(result.get("semantic_replay_watch_addresses")))
        addresses.extend(source_mem_addresses(result))
    return unique_commands(addresses)


def source_mem_origins(route: dict[str, Any]) -> list[str]:
    return unique_commands(
        [
            origin
            for _, origin in source_mem_parts(route)
            if origin
        ]
    )


def source_mem_addresses(route: dict[str, Any]) -> list[str]:
    return unique_commands(
        [
            address
            for address, _ in source_mem_parts(route)
            if address
        ]
    )


def source_mem_parts(route: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for value in string_items(route.get("source_mems")):
        text = str(value).strip()
        if not text:
            continue
        if "=" in text:
            address, origin = text.split("=", 1)
            out.append((address.strip(), origin.strip()))
        else:
            out.append((text, ""))
    return out


def signals_from_taint(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for target in dict_items(report.get("targets")):
        symbol_name = str(target.get("symbol", ""))
        if symbol_name:
            out.append(signal("taint_target", symbol=symbol_name, source=source, weight=84))
        for sink in dict_items(target.get("sinks"))[:12]:
            if sink.get("routine"):
                out.append(
                    signal(
                        "taint_sink_routine",
                        symbol=str(sink["routine"]),
                        file=str(sink.get("source_file", "")),
                        note=f"{sink.get('access', 'write')} {symbol_name}",
                        source=source,
                        weight=80,
                    )
                )
        for contributor in dict_items(target.get("contributors"))[:16]:
            if contributor.get("symbol"):
                out.append(
                    signal(
                        "taint_contributor",
                        symbol=str(contributor["symbol"]),
                        file=str(contributor.get("source_file", "")),
                        note=f"{contributor.get('relation', 'contributes')} -> {symbol_name}",
                        source=source,
                        weight=78,
                    )
                )
    for path in dict_items(report.get("paths"))[:16]:
        for symbol_name in string_items(path.get("related_symbols")):
            out.append(signal("taint_path_symbol", symbol=symbol_name, source=source, weight=70))
        for file_name in string_items(path.get("related_files")):
            out.append(signal("taint_path_file", file=file_name, source=source, weight=68))
    for attribution in dict_items(report.get("write_attributions"))[:16]:
        target = str(attribution.get("target", ""))
        if target:
            out.append(
                signal(
                    "dynamic_write_target",
                    symbol=target,
                    note=str(attribution.get("mnemonic", "")),
                    source=source,
                    weight=92,
                )
            )
        routine = base_pc_label(str(attribution.get("pc_label", "")))
        if routine:
            out.append(
                signal(
                    "dynamic_write_routine",
                    symbol=routine,
                    note=f"writes {target}",
                    source=source,
                    weight=86,
                )
            )
        for symbol_name in string_items(attribution.get("related_symbols")):
            out.append(signal("dynamic_write_related_symbol", symbol=symbol_name, source=source, weight=72))
    return out


def base_pc_label(label: str) -> str:
    text = str(label).strip()
    if not text or text.startswith("$"):
        return ""
    if "+" in text:
        text = text.split("+", 1)[0]
    return text


def signals_from_instruction_trace(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for function in dict_items(report.get("functions"))[:16]:
        symbol_name = str(function.get("symbol", ""))
        if symbol_name:
            out.append(signal("instruction_trace_function", symbol=symbol_name, source=source, weight=76))
    for watch in dict_items(report.get("watches"))[:16]:
        watch_name = str(watch.get("name", ""))
        if watch_name:
            out.append(signal("instruction_trace_watch", symbol=watch_name, source=source, weight=82))
    for record in dict_items(report.get("sample_records"))[:16]:
        for symbol_name in string_items([record.get("function"), record.get("pc_label")]):
            out.append(signal("instruction_trace_runtime", symbol=symbol_name, source=source, weight=70))
    return out


def event_note(event: dict[str, Any]) -> str:
    state = event.get("state_symbol") or event.get("bank_address") or event.get("address") or "state"
    source = event.get("source_symbol") or event.get("pc_symbol") or event.get("rule_id") or "trace"
    before = event.get("before", "")
    after = event.get("after", "")
    if before or after:
        return f"{event.get('event_type', 'event')} {state} {before}->{after} from {source}"
    return f"{event.get('event_type', 'event')} {state} from {source}"


def signals_from_slice(report: dict[str, Any], *, source: str = "slice") -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for target in dict_items(report.get("targets")):
        if not target.get("found"):
            continue
        symbol_name = str(target.get("resolved") or target.get("query") or "")
        out.append(signal("slice_target", symbol=symbol_name, source=source, weight=60))
        definition = target.get("definition") or {}
        if definition.get("path"):
            out.append(
                signal(
                    "slice_definition",
                    symbol=symbol_name,
                    file=str(definition["path"]),
                    source=source,
                    weight=55,
                )
            )
        for edge in target.get("incoming", [])[:24]:
            out.append(signal_from_edge(edge, "slice_incoming", source=source, weight=50))
        for edge in target.get("outgoing", [])[:24]:
            out.append(signal_from_edge(edge, "slice_outgoing", source=source, weight=35))
        for path in target.get("impact_files", []):
            out.append(signal("slice_impact_file", file=path, source=source, weight=30))
    for source_file in dict_items(report.get("source_files")):
        source_path = str(source_file.get("path") or "")
        if source_path:
            out.append(
                signal(
                    "slice_source_file",
                    file=source_path,
                    source=source,
                    weight=40,
                )
            )
        for label in dict_items(source_file.get("labels"))[:24]:
            label_name = str(label.get("label") or "")
            if label_name:
                out.append(
                    signal(
                        "slice_source_label",
                        symbol=label_name,
                        file=source_path,
                        source=source,
                        weight=52,
                    )
                )
        for edge in source_file.get("incoming", [])[:24]:
            out.append(signal_from_edge(edge, "slice_source_incoming", source=source, weight=46))
        for edge in source_file.get("outgoing", [])[:24]:
            out.append(signal_from_edge(edge, "slice_source_outgoing", source=source, weight=38))
    return out


def signal_from_edge(edge: dict[str, Any], signal_type: str, *, source: str, weight: int) -> dict[str, Any]:
    return signal(
        signal_type,
        symbol=str(edge.get("target", "")),
        routine=str(edge.get("source", "")),
        file=str(edge.get("path", "")),
        note=f"{edge.get('access', 'reference')} {edge.get('source')} -> {edge.get('target')}:{edge.get('line')}",
        source=source,
        weight=weight,
    )


def signals_from_symptom(symptom: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for keyword, hints in SYMPTOM_HINTS.items():
        if not keyword_matches(keyword, symptom):
            continue
        for hint_kind, value, weight in hints:
            if hint_kind == "symbol":
                out.append(signal("symptom_keyword", symbol=value, note=keyword, weight=weight))
            elif hint_kind == "file":
                out.append(signal("symptom_keyword_file", file=value, note=keyword, weight=weight))
    return out


def symbols_for_addresses(
    addresses: tuple[str, ...],
    *,
    symbol_table: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    if not addresses or not symbol_table:
        return out
    for raw_address in addresses:
        wanted = address_match_key(raw_address)
        if not wanted:
            continue
        matches: list[str] = []
        for symbol_name, info in symbol_table.items():
            candidate = address_match_key(str(info.get("bank_address", "")))
            if not candidate:
                continue
            bank_matches = wanted[0] == "" or wanted[0] == candidate[0]
            if bank_matches and wanted[1] == candidate[1]:
                matches.append(symbol_name)
        if matches:
            out[raw_address] = sorted(matches)
    return out


def address_match_key(value: str) -> tuple[str, str] | None:
    text = str(value).strip()
    if not text:
        return None
    bank = ""
    if ":" in text:
        raw_bank, text = text.split(":", 1)
        bank = normalize_hex_token(raw_bank, width=2)
        if not bank:
            return None
    address = normalize_hex_token(text, width=4)
    if not address:
        return None
    return (bank, address)


def normalize_hex_token(value: str, *, width: int) -> str:
    text = str(value).strip()
    if text.startswith("$"):
        text = text[1:]
    if text.lower().startswith("0x"):
        text = text[2:]
    if not text or len(text) > width:
        return ""
    try:
        number = int(text, 16)
    except ValueError:
        return ""
    if number >= 16 ** width:
        return ""
    return f"{number:0{width}X}"


def score_candidates(signals: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    symbol_scores: dict[str, int] = {}
    file_scores: dict[str, int] = {}
    address_scores: dict[str, int] = {}
    for item in signals:
        weight = int(item.get("weight", 0))
        symbol_name = item.get("symbol")
        routine = item.get("routine")
        file_name = item.get("file")
        address = item.get("address")
        if symbol_name:
            symbol_scores[str(symbol_name)] = symbol_scores.get(str(symbol_name), 0) + weight
        if routine and not routine.startswith("$"):
            symbol_scores[str(routine)] = symbol_scores.get(str(routine), 0) + max(15, weight // 2)
        if file_name:
            normalized = normalize_path(str(file_name))
            file_scores[normalized] = file_scores.get(normalized, 0) + weight
        if address:
            address_text = str(address)
            address_scores[address_text] = address_scores.get(address_text, 0) + weight
    return {"symbols": symbol_scores, "files": file_scores, "addresses": address_scores}


def build_candidates(
    *,
    symbol_scores: dict[str, int],
    file_scores: dict[str, int],
    address_scores: dict[str, int],
    signals: list[dict[str, Any]],
    max_candidates: int,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for symbol_name, score in sorted(symbol_scores.items(), key=lambda item: (-item[1], item[0])):
        candidates.append(
            {
                "type": "symbol",
                "id": symbol_name,
                "score": score,
                "evidence": evidence_for(signals, symbol=symbol_name),
            }
        )
    for file_name, score in sorted(file_scores.items(), key=lambda item: (-item[1], item[0])):
        candidates.append(
            {
                "type": "source_file",
                "id": file_name,
                "score": score,
                "evidence": evidence_for(signals, file=file_name),
            }
        )
    for address, score in sorted(address_scores.items(), key=lambda item: (-item[1], item[0])):
        candidates.append(
            {
                "type": "address",
                "id": address,
                "score": score,
                "evidence": evidence_for(signals, address=address),
            }
        )
    return sorted(candidates, key=lambda item: (-int(item["score"]), item["type"], item["id"]))[:max_candidates]


def build_phase_steps(
    *,
    symbols: tuple[str, ...],
    changed_files: tuple[str, ...],
    addresses: tuple[str, ...],
    watch_size: int,
    reports: tuple[str, ...],
    triage: dict[str, Any],
    tests: dict[str, Any],
    compare: dict[str, Any],
    gate: dict[str, Any],
) -> list[dict[str, Any]]:
    steps_by_phase: dict[str, list[dict[str, Any]]] = {
        phase: [] for phase in PHASE_TITLES
    }

    if reports:
        report_args = " ".join(f"--report {path}" for path in reports)
        add_step(
            steps_by_phase,
            "reproduce",
            f"python -m tools.debugger rank {report_args}",
            "Normalize existing report failures before rerunning expensive tools.",
        )
    if addresses:
        for address in addresses[:5]:
            command_address = command_address_arg(address)
            watch_size_arg = f" --watch-size {watch_size}" if watch_size != 1 else ""
            safe_address = safe_name(command_address)
            add_step(
                steps_by_phase,
                "reproduce",
                f"python -m tools.debugger replay --watch-address {command_address}{watch_size_arg} --execute-watch --json-out .local\\tmp\\debugger_replay_{safe_address}.json",
                f"Replay and watch raw address {address}.",
            )
            add_step(
                steps_by_phase,
                "observe",
                f"python -m tools.debugger watch --watch-address {command_address}{watch_size_arg} --execute --frames 300 --json-out .local\\tmp\\debugger_watch_{safe_address}.json",
                f"Observe raw address {address} for the first dynamic state change.",
            )
    if symbols:
        for symbol_name in symbols[:5]:
            if is_watchable_symbol(symbol_name):
                add_step(
                    steps_by_phase,
                    "observe",
                    f"python -m tools.debugger watch --watch-symbol {symbol_name} --execute --frames 300 --json-out .local\\tmp\\debugger_watch_{safe_name(symbol_name)}.json",
                    f"Replay and watch {symbol_name} for the first dynamic state change.",
                )
            add_step(
                steps_by_phase,
                "slice",
                f"python -m tools.debugger slice --symbol {symbol_name} --json-out .local\\tmp\\debugger_slice_{safe_name(symbol_name)}.json",
                f"Map static contributors for {symbol_name}.",
            )
            add_step(
                steps_by_phase,
                "slice",
                f"python -m tools.debugger provenance --symbol {symbol_name}",
                f"Find definitions, references, and subsystem routes for {symbol_name}.",
            )
    for path in changed_files[:5]:
        add_step(
            steps_by_phase,
            "slice",
            f"python -m tools.debugger slice --source-file {path}",
            f"Map callers and touched labels around {path}.",
        )
    for command in triage.get("commands", []):
        add_step(steps_by_phase, "reproduce", command, "Run the focused triage gate.")
    for command in compare.get("commands", []):
        add_step(steps_by_phase, "compare", command, "Compare against the best available mirror/oracle.")
    for command in compare.get("materialization_commands", []):
        add_step(steps_by_phase, "compare", command, "Materialize or replay before treating mirror output as ROM behavior.")
    for command in tests.get("commands", []):
        add_step(steps_by_phase, "minimize", command, "Generate focused scenarios around the suspected surface.")
    for command in tests.get("counterexample_commands", []):
        add_step(steps_by_phase, "minimize", command, "Reduce a failure to a concrete counterexample.")
    for step in gate.get("steps", []):
        add_step(steps_by_phase, "verify", step["command"], "Keep the final verification gate green.")

    return [
        {
            "phase": phase,
            "title": PHASE_TITLES[phase],
            "steps": unique_steps(steps),
        }
        for phase, steps in steps_by_phase.items()
        if steps
    ]


def add_step(
    steps_by_phase: dict[str, list[dict[str, Any]]],
    phase: str,
    command: str,
    reason: str,
) -> None:
    if not command:
        return
    steps_by_phase[phase].append(
        {
            "command": command,
            "reason": reason,
            "runnable": command_is_runnable(command),
        }
    )


def signal(
    signal_type: str,
    *,
    symbol: str = "",
    routine: str = "",
    file: str = "",
    address: str = "",
    note: str = "",
    source: str = "input",
    weight: int = 0,
) -> dict[str, Any]:
    return {
        "type": signal_type,
        "symbol": symbol,
        "routine": routine,
        "file": normalize_path(file) if file else "",
        "address": address,
        "note": note,
        "source": source,
        "weight": int(weight),
    }


def merge_duplicate_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for item in signals:
        key = (
            str(item.get("type", "")),
            str(item.get("symbol", "")),
            str(item.get("routine", "")),
            str(item.get("file", "")),
            str(item.get("address", "")),
            str(item.get("note", "")),
        )
        if key not in merged:
            merged[key] = dict(item)
            continue
        merged[key]["weight"] = max(int(merged[key]["weight"]), int(item.get("weight", 0)))
    return sorted(merged.values(), key=lambda item: (-int(item["weight"]), item["type"]))


def evidence_for(
    signals: list[dict[str, Any]],
    *,
    symbol: str = "",
    file: str = "",
    address: str = "",
) -> list[str]:
    evidence: list[str] = []
    for item in signals:
        if symbol and symbol not in {item.get("symbol"), item.get("routine")}:
            continue
        if file and normalize_path(str(item.get("file", ""))) != file:
            continue
        if address and str(item.get("address", "")) != address:
            continue
        note = item.get("note") or item.get("source") or item.get("type")
        evidence.append(f"{item['type']}: {note}")
    return unique_commands(evidence)[:6]


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


def unique_commands(commands: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for command in commands:
        if not command or command in seen:
            continue
        seen.add(command)
        out.append(str(command))
    return out


def top_names(scores: dict[str, int], limit: int) -> list[str]:
    return [
        name
        for name, _score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]
        if name
    ]


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def looks_like_source_path(path: str) -> bool:
    normalized = normalize_path(path)
    return bool(normalized and "/" in normalized and Path(normalized).suffix.lower() == ".asm")


def safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in value)


def is_watchable_symbol(symbol_name: str) -> bool:
    return symbol_name.startswith(("w", "h", "s", "v", "r"))


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
