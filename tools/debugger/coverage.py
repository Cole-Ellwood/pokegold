from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .localize import is_watchable_symbol
from .provenance import derive_report_provenance_inputs, display_path, parse_symbol_table, resolve_path
from .reporting import load_reports
from .slicing import build_slice_report
from .workflow import command_address_arg


SYMBOL_KEYS = {
    "callsite_rule_symbol",
    "callsite_symbol",
    "closed_by",
    "full_symbol",
    "helper_symbol",
    "label",
    "parent_label",
    "pc_label",
    "query",
    "resolved",
    "source",
    "source_label",
    "target",
    "watch",
}
SOURCE_FILE_KEYS = {"source_file"}
SOURCE_FILE_LIST_KEYS = {"changed_files", "related_files", "source_files"}
SYMBOL_LIST_KEYS = {"related_symbols", "sink_symbols", "source_symbols", "symbols_to_investigate", "watch_symbols"}
ADDRESS_KEYS = {"address", "bank_address", "sink_address", "watch_address"}
ADDRESS_LIST_KEYS = {"addresses", "related_addresses", "sink_addresses", "watch_addresses"}
SOURCE_MEM_LIST_KEYS = {"source_mems"}
RULE_KEYS = {"rule_id"}
RULE_LIST_KEYS = {
    "changed_rule_ids",
    "covered_rule_ids",
    "executed_rule_ids",
    "rule_ids",
    "uncovered_rule_ids",
}


def build_coverage_report(
    *,
    traces: tuple[str, ...] = (),
    reports: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    rules: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    symbols_path: str = "pokegold.sym",
    max_targets: int = 80,
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_reports, load_errors = load_reports(reports=reports, root=root)
    parsed_traces, trace_errors = load_traces(traces=traces, root=root)
    sym_path = resolve_path(symbols_path, root=root)
    symbol_table = parse_symbol_table(sym_path) if sym_path.exists() else {}
    observations = new_observations()

    for loaded in loaded_reports:
        observe_data(
            loaded["data"],
            source=loaded["source"],
            observations=observations,
        )
    for loaded in parsed_traces:
        observe_data(
            loaded["data"],
            source=loaded["source"],
            observations=observations,
        )
    add_symbol_observations_for_observed_addresses(
        observations,
        symbol_table=symbol_table,
    )

    derived_slice_inputs = derive_report_provenance_inputs(loaded_reports)
    derived_source_files = tuple(
        path
        for path in derived_slice_inputs["source_files"]
        if resolve_path(path, root=root).is_file()
    )
    slice_symbols = tuple(unique_list([*symbols, *derived_slice_inputs["symbols"]]))
    slice_source_files = tuple(unique_list([*changed_files, *derived_source_files]))
    has_symbol_file = bool(symbol_table)

    slice_report = None
    if symbols or changed_files or (has_symbol_file and (slice_symbols or slice_source_files)):
        slice_report = build_slice_report(
            symbols_path=symbols_path,
            symbols=slice_symbols,
            source_files=slice_source_files,
            max_depth=1,
            max_edges=24,
            root=root,
        )
    target_context = build_target_context(
        symbols=symbols,
        rules=rules,
        changed_files=changed_files,
        loaded_reports=loaded_reports,
        slice_report=slice_report,
        max_targets=max_targets,
    )
    targets = evaluate_targets(
        target_context=target_context,
        observations=observations,
    )
    uncovered = [target for target in targets if target["status"] == "uncovered"]
    indirect = [target for target in targets if target["status"] == "indirect"]
    covered = [target for target in targets if target["status"] == "covered"]
    errors = [*load_errors, *trace_errors]
    if slice_report:
        errors.extend(slice_report.get("errors", []))

    return {
        "schema_version": 1,
        "kind": "unified_debugger_coverage_report",
        "root": str(root),
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
        "symbols_path": symbols_path,
        "trace_count": len(parsed_traces),
        "report_count": len(loaded_reports),
        "target_count": len(targets),
        "covered_target_count": len(covered),
        "indirect_target_count": len(indirect),
        "uncovered_target_count": len(uncovered),
        "coverage_ratio": round(len(covered) / len(targets), 4) if targets else 0.0,
        "covered_symbol_count": len(observations["symbols"]),
        "covered_file_count": len(observations["files"]),
        "covered_rule_count": len(observations["rules"]),
        "covered_address_count": len(observations["addresses"]),
        "covered_symbols": summarize_seen(observations["symbols"], limit=40),
        "covered_files": summarize_seen(observations["files"], limit=40),
        "covered_rules": summarize_seen(observations["rules"], limit=40),
        "covered_addresses": summarize_seen(observations["addresses"], limit=40),
        "targets": targets,
        "uncovered_targets": uncovered,
        "known_limits": [
            "Coverage means a trace/report mentioned the symbol, file, or rule; it is not proof of semantic correctness.",
            "Indirect coverage means a related label or source file was seen, but the explicit target was not directly observed.",
        ],
    }


def load_traces(*, traces: tuple[str, ...], root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    loaded: list[dict[str, Any]] = []
    errors: list[str] = []
    for raw_path in traces:
        path = resolve_path(raw_path, root=root)
        source = display_path(path, root=root)
        if not path.exists():
            errors.append(f"missing trace: {raw_path}")
            continue
        try:
            data = parse_trace_or_json(path)
        except json.JSONDecodeError as exc:
            errors.append(f"{raw_path}: invalid JSON: {exc.msg}")
            continue
        except OSError as exc:
            errors.append(f"{raw_path}: {exc}")
            continue
        loaded.append({"path": path, "source": source, "data": data})
    return loaded, errors


def parse_trace_or_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8", errors="replace")
    stripped = text.lstrip()
    if path.suffix.lower() == ".jsonl":
        return [
            json.loads(line)
            for line in text.splitlines()
            if line.strip()
        ]
    if path.suffix.lower() == ".json" or stripped.startswith(("{", "[")):
        return json.loads(text)
    key_values: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key_values[key.strip()] = value.strip()
    return {
        "kind": "key_value_trace",
        "line_count": len(text.splitlines()),
        "keys": key_values,
    }


def new_observations() -> dict[str, dict[str, dict[str, Any]]]:
    return {"symbols": {}, "files": {}, "rules": {}, "addresses": {}}


def observe_data(data: Any, *, source: str, observations: dict[str, dict[str, dict[str, Any]]]) -> None:
    walk_data(data, source=source, observations=observations, context={})


def walk_data(
    data: Any,
    *,
    source: str,
    observations: dict[str, dict[str, dict[str, Any]]],
    context: dict[str, Any],
) -> None:
    if isinstance(data, dict):
        local_context = dict(context)
        parent_label = data.get("parent_label") or data.get("callsite_rule_symbol")
        source_file = data.get("source_file")
        if isinstance(parent_label, str):
            local_context["parent_label"] = parent_label
        if isinstance(source_file, str):
            local_context["source_file"] = source_file
        for key, value in data.items():
            observe_field(
                key,
                value,
                source=source,
                observations=observations,
                context=local_context,
            )
            walk_data(
                value,
                source=source,
                observations=observations,
                context=local_context,
            )
    elif isinstance(data, list):
        for item in data:
            walk_data(item, source=source, observations=observations, context=context)


def observe_field(
    key: str,
    value: Any,
    *,
    source: str,
    observations: dict[str, dict[str, dict[str, Any]]],
    context: dict[str, Any],
) -> None:
    if key in SOURCE_FILE_KEYS and isinstance(value, str):
        add_seen(observations["files"], normalize_path(value), source=source, role="source_file")
    elif key in SOURCE_FILE_LIST_KEYS:
        for item in string_items(value):
            if looks_like_source_path(item):
                add_seen(observations["files"], normalize_path(item), source=source, role=key)
    elif key in SYMBOL_KEYS and isinstance(value, str):
        symbol = normalize_symbol(value, context=context)
        if symbol:
            add_seen(observations["symbols"], symbol, source=source, role=key)
            if context.get("source_file"):
                add_seen(
                    observations["files"],
                    normalize_path(str(context["source_file"])),
                    source=source,
                    role=f"symbol:{symbol}",
                )
    elif key in SYMBOL_LIST_KEYS:
        for item in string_items(value):
            symbol = normalize_symbol(item, context=context)
            if symbol:
                add_seen(observations["symbols"], symbol, source=source, role=key)
                if context.get("source_file"):
                    add_seen(
                        observations["files"],
                        normalize_path(str(context["source_file"])),
                        source=source,
                        role=f"symbol:{symbol}",
                    )
    elif key in ADDRESS_KEYS:
        address = normalize_address(value)
        if address:
            add_seen(observations["addresses"], address, source=source, role=key)
    elif key in ADDRESS_LIST_KEYS:
        for item in string_items(value):
            address = normalize_address(item)
            if address:
                add_seen(observations["addresses"], address, source=source, role=key)
    elif key == "watch_values" and isinstance(value, dict):
        for raw_key in value:
            address = normalize_address(raw_key)
            if address:
                add_seen(observations["addresses"], address, source=source, role="watch_values")
                continue
            symbol = normalize_symbol(str(raw_key), context=context)
            if symbol:
                add_seen(observations["symbols"], symbol, source=source, role="watch_values")
    elif key in SOURCE_MEM_LIST_KEYS:
        for address, origin in source_mem_parts_from_value(value):
            normalized_address = normalize_address(address)
            if normalized_address:
                add_seen(observations["addresses"], normalized_address, source=source, role=key)
            symbol = normalize_symbol(origin, context=context)
            if symbol:
                add_seen(observations["symbols"], symbol, source=source, role=key)
    elif key in RULE_KEYS and isinstance(value, str):
        add_seen(observations["rules"], value, source=source, role="rule")
    elif key in RULE_LIST_KEYS:
        for item in string_items(value):
            add_seen(observations["rules"], item, source=source, role=key)


def build_target_context(
    *,
    symbols: tuple[str, ...],
    rules: tuple[str, ...],
    changed_files: tuple[str, ...],
    loaded_reports: list[dict[str, Any]],
    slice_report: dict[str, Any] | None,
    max_targets: int,
) -> dict[str, dict[str, Any]]:
    targets: dict[str, dict[str, Any]] = {}
    for symbol in symbols:
        add_target(targets, "symbol", symbol, explicit=True)
    for rule in rules:
        add_target(targets, "rule", rule, explicit=True)
    for path in changed_files:
        add_target(targets, "source_file", normalize_path(path), explicit=True)
    add_report_targets(targets, loaded_reports=loaded_reports, max_targets=max_targets)
    if not slice_report:
        return finalize_targets(targets, max_targets=max_targets)

    for target in dict_items(slice_report.get("targets")):
        symbol = target.get("resolved") or target.get("query")
        if isinstance(symbol, str) and symbol:
            entry = add_target(targets, "symbol", symbol, explicit=symbol in symbols)
            definition = target.get("definition") or {}
            if definition.get("path"):
                definition_path = normalize_path(str(definition["path"]))
                entry.setdefault("related_files", set()).add(definition_path)
                file_entry = add_target(targets, "source_file", definition_path, explicit=False)
                file_entry.setdefault("related_symbols", set()).add(symbol)
            for path in target.get("impact_files", []):
                impact_path = normalize_path(str(path))
                entry.setdefault("related_files", set()).add(impact_path)
                file_entry = add_target(targets, "source_file", impact_path, explicit=False)
                file_entry.setdefault("related_symbols", set()).add(symbol)
        for edge in target.get("incoming", [])[:max_targets]:
            if edge.get("source"):
                add_target(targets, "symbol", str(edge["source"]), explicit=False)
            if edge.get("path"):
                file_entry = add_target(targets, "source_file", normalize_path(str(edge["path"])), explicit=False)
                if edge.get("source"):
                    file_entry.setdefault("related_symbols", set()).add(str(edge["source"]))
                if edge.get("target"):
                    file_entry.setdefault("related_symbols", set()).add(str(edge["target"]))
        for edge in target.get("outgoing", [])[:max_targets]:
            if edge.get("target"):
                add_target(targets, "symbol", str(edge["target"]), explicit=False)
            if edge.get("path"):
                file_entry = add_target(targets, "source_file", normalize_path(str(edge["path"])), explicit=False)
                if edge.get("source"):
                    file_entry.setdefault("related_symbols", set()).add(str(edge["source"]))
                if edge.get("target"):
                    file_entry.setdefault("related_symbols", set()).add(str(edge["target"]))

    for source in dict_items(slice_report.get("source_files")):
        path = normalize_path(str(source.get("path", "")))
        if path:
            file_target = add_target(targets, "source_file", path, explicit=path in changed_files)
        else:
            file_target = None
        for label in source.get("labels", [])[:max_targets]:
            label_name = label.get("label")
            if isinstance(label_name, str) and label_name:
                entry = add_target(targets, "symbol", label_name, explicit=False)
                if path:
                    entry.setdefault("related_files", set()).add(path)
                    if file_target is not None:
                        file_target.setdefault("related_symbols", set()).add(label_name)

    return finalize_targets(targets, max_targets=max_targets)


def add_report_targets(
    targets: dict[str, dict[str, Any]],
    *,
    loaded_reports: list[dict[str, Any]],
    max_targets: int,
) -> None:
    for loaded in loaded_reports:
        data = loaded.get("data", {})
        if not isinstance(data, dict):
            continue
        if data.get("kind") == "unified_debugger_content_mirror":
            add_content_mirror_targets(targets, report=data, max_targets=max_targets)
        elif data.get("kind") == "unified_debugger_content_scenarios":
            add_content_scenario_targets(targets, report=data, max_targets=max_targets)
        elif data.get("kind") == "unified_debugger_fuzz_plan":
            add_content_fuzz_targets(targets, report=data, max_targets=max_targets)
        elif data.get("kind") == "unified_debugger_playtest_packet":
            add_playtest_packet_targets(targets, report=data, max_targets=max_targets)
        elif data.get("kind") == "unified_debugger_dynamic_taint_report":
            add_dynamic_taint_targets(targets, report=data, max_targets=max_targets)
        elif data.get("kind") == "unified_debugger_minimization_plan":
            add_minimization_targets(targets, report=data, source=str(loaded.get("source", "")))


def add_playtest_packet_targets(
    targets: dict[str, dict[str, Any]],
    *,
    report: dict[str, Any],
    max_targets: int,
) -> None:
    commands = string_items(report.get("commands"))
    source_files = [
        normalize_path(path)
        for path in string_items(report.get("changed_files"))[:max_targets]
        if looks_like_source_path(path)
    ]
    symbols = [
        symbol
        for symbol in unique_list(
            [
                *string_items(report.get("symbols_to_investigate")),
                *string_items(report.get("watch_symbols")),
            ]
        )[:max_targets]
        if normalize_symbol(symbol, context={})
    ]
    addresses = [
        address
        for address in (normalize_address(raw) for raw in string_items(report.get("addresses"))[:max_targets])
        if address
    ]
    for source_file in source_files:
        entry = add_target(targets, "source_file", source_file, explicit=False)
        entry.setdefault("commands", set()).update(commands)
        entry.setdefault("related_symbols", set()).update(symbols)
        entry.setdefault("related_addresses", set()).update(addresses)
    for symbol in symbols:
        entry = add_target(targets, "symbol", symbol, explicit=False)
        entry.setdefault("commands", set()).update(commands)
        entry.setdefault("related_files", set()).update(source_files)
        entry.setdefault("related_addresses", set()).update(addresses)
    for address in addresses:
        entry = add_target(targets, "address", address, explicit=False)
        entry.setdefault("commands", set()).update(commands)
        entry.setdefault("related_files", set()).update(source_files)
        entry.setdefault("related_symbols", set()).update(symbols)


def add_content_mirror_targets(
    targets: dict[str, dict[str, Any]],
    *,
    report: dict[str, Any],
    max_targets: int,
) -> None:
    for mirror in dict_items(report.get("rom_mirrors"))[:max_targets]:
        status = str(mirror.get("status", ""))
        if status not in {"passed", "failed"}:
            continue
        source_file = normalize_path(str(mirror.get("source_file", "")))
        related_files = [
            normalize_path(path)
            for path in string_items(mirror.get("related_files"))
            if looks_like_source_path(path)
        ]
        related_symbols = [
            symbol
            for symbol in string_items(mirror.get("related_symbols"))
            if symbol
        ]
        add_related_targets(
            targets,
            source_file=source_file,
            related_files=related_files,
            related_symbols=related_symbols,
        )


def add_content_scenario_targets(
    targets: dict[str, dict[str, Any]],
    *,
    report: dict[str, Any],
    max_targets: int,
) -> None:
    for scenario in dict_items(report.get("scenarios"))[:max_targets]:
        add_content_runtime_record_target(targets, record=scenario)


def add_content_fuzz_targets(
    targets: dict[str, dict[str, Any]],
    *,
    report: dict[str, Any],
    max_targets: int,
) -> None:
    for case in dict_items(report.get("fuzz_cases"))[:max_targets]:
        if case.get("counterexample_source") or case.get("related_symbols") or case.get("related_addresses"):
            add_sink_targets(
                targets,
                sink_symbols=string_items(case.get("related_symbols")),
                sink_addresses=string_items(case.get("related_addresses")),
                commands=string_items(case.get("commands")),
            )
        if not case.get("runtime_targets") and not case.get("scenario_type"):
            continue
        add_content_runtime_record_target(targets, record=case)


def add_dynamic_taint_targets(
    targets: dict[str, dict[str, Any]],
    *,
    report: dict[str, Any],
    max_targets: int,
) -> None:
    for route in trace_synthesis_routes(report)[:max_targets]:
        add_sink_targets(
            targets,
            sink_symbols=trace_synthesis_related_symbols(route),
            sink_addresses=trace_synthesis_related_addresses(route),
            commands=string_items(route.get("commands")),
        )
    for path in dict_items(report.get("paths"))[:max_targets]:
        add_sink_targets(
            targets,
            sink_symbols=string_items(path.get("related_symbols")),
            sink_addresses=string_items(path.get("related_addresses")),
            commands=string_items(path.get("commands")),
        )
    for attribution in dict_items(report.get("write_attributions"))[:max_targets]:
        add_sink_targets(
            targets,
            sink_symbols=string_items(attribution.get("related_symbols")),
            sink_addresses=string_items(attribution.get("related_addresses")),
            commands=string_items(attribution.get("commands")),
        )


def add_minimization_targets(
    targets: dict[str, dict[str, Any]],
    *,
    report: dict[str, Any],
    source: str,
) -> None:
    state_patch_minimization = report.get("state_patch_minimization")
    if not isinstance(state_patch_minimization, dict) or not state_patch_minimization.get("attempted"):
        return
    symbols = state_patch_minimization_related_symbols(state_patch_minimization)
    addresses = state_patch_minimization_related_addresses(state_patch_minimization)
    source_files = [
        normalize_path(path)
        for path in string_items(state_patch_minimization.get("source_files"))
        if looks_like_source_path(path)
    ]
    commands = state_patch_minimization_commands(state_patch_minimization, source=source)
    add_sink_targets(
        targets,
        sink_symbols=symbols,
        sink_addresses=addresses,
        commands=commands,
    )
    normalized_symbols = [symbol for symbol in (normalize_symbol(symbol, context={}) for symbol in symbols) if symbol]
    normalized_addresses = [address for address in (normalize_address(address) for address in addresses) if address]
    for source_file in source_files:
        file_entry = add_target(targets, "source_file", source_file, explicit=False)
        file_entry.setdefault("commands", set()).update(commands)
        file_entry.setdefault("related_symbols", set()).update(normalized_symbols)
        file_entry.setdefault("related_addresses", set()).update(normalized_addresses)
        for symbol in normalized_symbols:
            symbol_entry = add_target(targets, "symbol", symbol, explicit=False)
            symbol_entry.setdefault("related_files", set()).add(source_file)
            symbol_entry.setdefault("commands", set()).update(commands)
        for address in normalized_addresses:
            address_entry = add_target(targets, "address", address, explicit=False)
            address_entry.setdefault("related_files", set()).add(source_file)
            address_entry.setdefault("commands", set()).update(commands)


def state_patch_minimization_commands(item: dict[str, Any], *, source: str) -> list[str]:
    commands = []
    if source:
        commands.extend(
            [
                f"python -m tools.debugger provenance --report {source}",
                f"python -m tools.debugger taint --report {source}",
                f"python -m tools.debugger slice --report {source}",
            ]
        )
    commands.extend(string_items(item.get("commands")))
    for route in dict_items(item.get("semantic_reducer_routes")):
        commands.extend(string_items(route.get("commands")))
    return unique_list(commands)


def trace_synthesis_routes(report: dict[str, Any]) -> list[dict[str, Any]]:
    plan = report.get("trace_synthesis_plan") if isinstance(report.get("trace_synthesis_plan"), dict) else {}
    return dict_items(plan.get("routes"))


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
    return unique_list(symbols)


def state_patch_minimization_related_addresses(item: dict[str, Any]) -> list[str]:
    addresses = [
        *string_items(item.get("watch_addresses")),
        *source_mem_addresses(item),
    ]
    for result in dict_items(item.get("results")):
        addresses.extend(string_items(result.get("semantic_watch_addresses")))
        addresses.extend(string_items(result.get("semantic_replay_watch_addresses")))
        addresses.extend(source_mem_addresses(result))
    return unique_list(addresses)


def trace_synthesis_related_symbols(route: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            *string_items(route.get("sink_symbols")),
            *string_items(route.get("source_symbols")),
            *source_mem_origins(route),
        ]
    )


def trace_synthesis_related_addresses(route: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            *string_items(route.get("sink_addresses")),
            *source_mem_addresses(route),
        ]
    )


def source_mem_origins(route: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            origin
            for _, origin in source_mem_parts(route)
            if origin
        ]
    )


def source_mem_addresses(route: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            address
            for address, _ in source_mem_parts(route)
            if address
        ]
    )


def source_mem_parts(route: dict[str, Any]) -> list[tuple[str, str]]:
    return source_mem_parts_from_value(route.get("source_mems"))


def source_mem_parts_from_value(value: Any) -> list[tuple[str, str]]:
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


def add_sink_targets(
    targets: dict[str, dict[str, Any]],
    *,
    sink_symbols: list[str],
    sink_addresses: list[str],
    commands: list[str],
) -> None:
    symbols = [symbol for symbol in (normalize_symbol(symbol, context={}) for symbol in sink_symbols) if symbol]
    addresses = [address for address in (normalize_address(address) for address in sink_addresses) if address]
    for symbol in symbols:
        entry = add_target(targets, "symbol", symbol, explicit=False)
        entry.setdefault("commands", set()).update(commands)
        entry.setdefault("related_addresses", set()).update(addresses)
    for address in addresses:
        entry = add_target(targets, "address", address, explicit=False)
        entry.setdefault("commands", set()).update(commands)
        entry.setdefault("related_symbols", set()).update(symbols)


def add_content_runtime_record_target(
    targets: dict[str, dict[str, Any]],
    *,
    record: dict[str, Any],
) -> None:
    source_file = normalize_path(str(record.get("source_file") or record.get("changed_file") or ""))
    runtime_targets = record.get("runtime_targets") if isinstance(record.get("runtime_targets"), dict) else {}
    related_symbols = unique_list(
        [
            *string_items(record.get("related_symbols")),
            *string_items(record.get("symbols")),
            *string_items(runtime_targets.get("source_symbols")),
            *string_items(runtime_targets.get("script_symbols")),
            *string_items(runtime_targets.get("trace_symbols")),
            *string_items(runtime_targets.get("watch_symbols")),
        ]
    )
    add_related_targets(
        targets,
        source_file=source_file,
        related_files=[],
        related_symbols=related_symbols,
    )


def add_related_targets(
    targets: dict[str, dict[str, Any]],
    *,
    source_file: str,
    related_files: list[str],
    related_symbols: list[str],
) -> None:
    if source_file:
        file_target = add_target(targets, "source_file", source_file, explicit=False)
    else:
        file_target = None
    for symbol in related_symbols:
        symbol_target = add_target(targets, "symbol", symbol, explicit=False)
        if source_file:
            symbol_target.setdefault("related_files", set()).add(source_file)
        for path in related_files:
            symbol_target.setdefault("related_files", set()).add(path)
        if file_target is not None:
            file_target.setdefault("related_symbols", set()).add(symbol)
    for path in related_files:
        related_file_target = add_target(targets, "source_file", path, explicit=False)
        for symbol in related_symbols:
            related_file_target.setdefault("related_symbols", set()).add(symbol)


def finalize_targets(
    targets: dict[str, dict[str, Any]],
    *,
    max_targets: int,
) -> dict[str, dict[str, Any]]:
    for item in targets.values():
        item["related_files"] = sorted(item.get("related_files", set()))
        item["related_symbols"] = sorted(item.get("related_symbols", set()))
        item["related_addresses"] = sorted(item.get("related_addresses", set()))
        item["commands"] = sorted(item.get("commands", set()))
    return dict(list(targets.items())[:max_targets])


def evaluate_targets(
    *,
    target_context: dict[str, dict[str, Any]],
    observations: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    targets = []
    for target in sorted(target_context.values(), key=lambda item: (not item["explicit"], item["type"], item["id"])):
        status, evidence = evaluate_target(target, observations=observations)
        item = {
            "type": target["type"],
            "id": target["id"],
            "explicit": target["explicit"],
            "status": status,
            "evidence": evidence,
            "related_files": target.get("related_files", []),
            "related_symbols": target.get("related_symbols", []),
            "related_addresses": target.get("related_addresses", []),
            "commands": coverage_commands(target),
        }
        targets.append(item)
    return targets


def evaluate_target(
    target: dict[str, Any],
    *,
    observations: dict[str, dict[str, dict[str, Any]]],
) -> tuple[str, list[str]]:
    if target["type"] == "symbol":
        direct = seen_entry(observations["symbols"], target["id"])
        if direct:
            return "covered", describe_seen(direct)
        for path in target.get("related_files", []):
            file_entry = seen_entry(observations["files"], path)
            if file_entry:
                return "indirect", [f"related file covered: {path}", *describe_seen(file_entry)[:2]]
    if target["type"] == "source_file":
        direct = seen_entry(observations["files"], target["id"])
        if direct:
            return "covered", describe_seen(direct)
        for symbol in target.get("related_symbols", []):
            symbol_entry = seen_entry(observations["symbols"], symbol)
            if symbol_entry:
                return "indirect", [f"label covered from file: {symbol}", *describe_seen(symbol_entry)[:2]]
    if target["type"] == "rule":
        direct = seen_entry(observations["rules"], target["id"])
        if direct:
            return "covered", describe_seen(direct)
    if target["type"] == "address":
        direct = seen_entry(observations["addresses"], target["id"])
        if direct:
            return "covered", describe_seen(direct)
        for symbol in target.get("related_symbols", []):
            symbol_entry = seen_entry(observations["symbols"], symbol)
            if symbol_entry:
                return "indirect", [f"related symbol covered: {symbol}", *describe_seen(symbol_entry)[:2]]
    return "uncovered", []


def coverage_commands(target: dict[str, Any]) -> list[str]:
    custom_commands = prioritized_coverage_commands(string_items(target.get("commands")))
    if target["type"] == "symbol":
        commands = [
            f"python -m tools.debugger localize --symbol {target['id']}",
            f"python -m tools.debugger slice --symbol {target['id']}",
        ]
        if is_watchable_symbol(target["id"]):
            commands.insert(
                0,
                f"python -m tools.debugger watch --watch-symbol {target['id']} --execute --frames 300",
            )
        return unique_list([*custom_commands, *commands])[:8]
    if target["type"] == "address":
        command_address = command_address_arg(target["id"])
        return unique_list(
            [
                *custom_commands,
                f"python -m tools.debugger localize --address {command_address}",
                f"python -m tools.debugger watch --watch-address {command_address} --execute --frames 300",
                f"python -m tools.debugger replay --watch-address {command_address} --execute-watch",
            ]
        )[:8]
    if target["type"] == "rule":
        return unique_list(
            [
                *custom_commands,
                f"python -m tools.debugger localize --symptom {target['id']}",
                "python -m tools.boss_ai_debugger generate --family all --count 500 --seed 1 --out .local\\tmp\\debugger_all_scenarios.jsonl",
                "python -m tools.boss_ai_debugger rom-score-materialize --scenarios <scenarios.jsonl> --limit 4 --compare-fast-score",
            ]
        )
    return unique_list(
        [
            *custom_commands,
            f"python -m tools.debugger localize --changed-file {target['id']}",
            f"python -m tools.debugger slice --source-file {target['id']}",
            f"python -m tools.debugger gate --changed-file {target['id']}",
        ]
    )


def prioritized_coverage_commands(commands: list[str]) -> list[str]:
    priorities = (
        "provenance --report",
        "taint --report",
        "slice --report",
        "dynamic-taint",
        "expect --report",
        "replay --report",
        "compare --report",
        "content-mirror",
        "content-scenarios",
        "damage_debugger",
        "boss_ai_debugger",
    )

    def priority(command: str) -> tuple[int, str]:
        for index, needle in enumerate(priorities):
            if needle in command:
                return index, command
        return len(priorities), command

    return unique_list(sorted(commands, key=priority))


def add_target(
    targets: dict[str, dict[str, Any]],
    target_type: str,
    target_id: str,
    *,
    explicit: bool,
) -> dict[str, Any]:
    key = f"{target_type}:{target_id}"
    if key not in targets:
        targets[key] = {
            "type": target_type,
            "id": target_id,
            "explicit": explicit,
            "related_files": set(),
            "related_symbols": set(),
            "related_addresses": set(),
            "commands": set(),
        }
    else:
        targets[key]["explicit"] = bool(targets[key]["explicit"] or explicit)
    return targets[key]


def add_seen(
    bucket: dict[str, dict[str, Any]],
    name: str,
    *,
    source: str,
    role: str,
) -> None:
    if not name:
        return
    entry = bucket.setdefault(name, {"id": name, "count": 0, "sources": set(), "roles": set()})
    entry["count"] += 1
    entry["sources"].add(source)
    entry["roles"].add(role)


def add_symbol_observations_for_observed_addresses(
    observations: dict[str, dict[str, dict[str, Any]]],
    *,
    symbol_table: dict[str, dict[str, Any]],
) -> None:
    aliases = symbol_address_aliases(symbol_table)
    for address, entry in list(observations["addresses"].items()):
        symbol = aliases.get(address)
        if not symbol and ":" in address:
            symbol = aliases.get(address.split(":", 1)[1])
        if not symbol:
            continue
        for source in sorted(entry["sources"]):
            add_seen(
                observations["symbols"],
                symbol,
                source=source,
                role="watch_values_address_alias",
            )


def symbol_address_aliases(symbol_table: dict[str, dict[str, Any]]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    address_counts: dict[str, int] = {}
    for data in symbol_table.values():
        address = str(data.get("address_hex") or "").upper()
        if address:
            address_counts[address] = address_counts.get(address, 0) + 1
    for label, data in symbol_table.items():
        bank_address = str(data.get("bank_address") or "").upper()
        address = str(data.get("address_hex") or "").upper()
        if bank_address:
            aliases.setdefault(bank_address, label)
        if address and address_counts.get(address, 0) == 1:
            aliases.setdefault(address, label)
    return aliases


def summarize_seen(bucket: dict[str, dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    items = sorted(bucket.values(), key=lambda item: (-int(item["count"]), item["id"]))[:limit]
    return [
        {
            "id": item["id"],
            "count": item["count"],
            "sources": sorted(item["sources"])[:8],
            "roles": sorted(item["roles"])[:8],
        }
        for item in items
    ]


def describe_seen(entry: dict[str, Any]) -> list[str]:
    sources = ", ".join(sorted(entry["sources"])[:3])
    roles = ", ".join(sorted(entry["roles"])[:3])
    return [f"seen {entry['count']} time(s)", f"sources: {sources}", f"roles: {roles}"]


def seen_entry(bucket: dict[str, dict[str, Any]], target_id: str) -> dict[str, Any] | None:
    if target_id in bucket:
        return bucket[target_id]
    normalized = normalize_path(target_id)
    address = normalize_address(target_id)
    if address and address in bucket:
        return bucket[address]
    if normalized in bucket:
        return bucket[normalized]
    for name, entry in bucket.items():
        if name.endswith("." + target_id) or target_id.endswith("." + name):
            return entry
    return None


def normalize_symbol(value: str, *, context: dict[str, Any]) -> str:
    symbol = value.strip()
    if not symbol or "\\" in symbol or "/" in symbol:
        return ""
    if symbol.startswith("$") or symbol.startswith("0x"):
        return ""
    if looks_like_artifact_path(symbol):
        return ""
    if symbol.startswith(".") and context.get("parent_label"):
        return str(context["parent_label"]) + symbol
    return symbol


def normalize_address(value: Any) -> str:
    if isinstance(value, int):
        return f"{value & 0xFFFF:04X}"
    text = str(value).strip()
    if not text:
        return ""
    if "=" in text:
        text = text.split("=", 1)[1].strip()
    if ":" in text:
        bank, address = text.split(":", 1)
        normalized_address = normalize_address(address)
        bank_text = bank.replace("$", "").strip()
        if normalized_address and bank_text:
            return f"{bank_text.upper()}:{normalized_address}"
        return normalized_address
    stripped = text.replace("$", "")
    if stripped.startswith(("0x", "0X")):
        stripped = stripped[2:]
    if len(stripped) == 4 and all(char in "0123456789abcdefABCDEF" for char in stripped):
        return stripped.upper()
    return ""


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def looks_like_source_path(path: str) -> bool:
    normalized = normalize_path(path)
    return bool(normalized and "/" in normalized and Path(normalized).suffix.lower() == ".asm")


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


def string_items(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list | tuple | set):
        return [item for nested in value for item in string_items(nested)]
    return []


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


def dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, dict)]
