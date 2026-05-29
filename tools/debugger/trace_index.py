from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .coverage import load_traces
from .explain import SYMPTOM_SYMBOLS, base_label, looks_like_source_path, runtime_symbol_items
from .localize import normalize_path
from .provenance import parse_symbol_table, resolve_path
from .reporting import load_reports
from .slicing import build_slice_report
from .workflow import command_address_arg, command_is_runnable


WRITE_EVENT_TYPES = {"memory_write", "score_delta", "watch_change", "memory_patch"}
READ_EVENT_TYPES = {"memory_read", "public_read"}
FLOW_EVENT_TYPES = {"control_flow", "rule_hit", "source_hint"}
REVERSE_ATTRIBUTION_RELATIONS = {
    "last_writer",
    "overwrites",
    "prior_read",
    "value_source",
    "source_context",
}
SYMBOL_KEYS = (
    "watch",
    "watch_symbol",
    "symbol",
    "state_symbol",
    "source_symbol",
    "pc_symbol",
    "full_symbol",
    "pc_label",
    "source_label",
    "callsite_symbol",
    "callsite_rule_symbol",
    "helper_symbol",
    "closed_by",
    "resolved",
    "query",
)
SOURCE_FILE_KEYS = ("source_file", "path")
RULE_KEYS = ("rule_id",)
ADDRESS_KEYS = (
    "address",
    "addr",
    "score_pointer",
    "hook_address",
    "return_address",
    "pc",
)
BANK_KEYS = (
    "bank",
    "hook_bank",
    "pc_bank",
)
VALUE_BEFORE_KEYS = ("old_hex", "old_value", "score_before", "before")
VALUE_AFTER_KEYS = ("new_hex", "new_value", "score_after", "after", "value")
REGISTER_KEYS = (
    "amount_register_a",
    "register_a",
    "register_b",
    "register_c",
    "register_d",
    "register_e",
    "register_h",
    "register_l",
    "register_sp",
    "register_pc",
    "a",
    "b",
    "c",
    "d",
    "e",
    "h",
    "l",
)


def build_trace_index_report(
    *,
    traces: tuple[str, ...] = (),
    reports: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    watch_symbols: tuple[str, ...] = (),
    addresses: tuple[str, ...] = (),
    rules: tuple[str, ...] = (),
    source_files: tuple[str, ...] = (),
    symptom: str = "",
    symbols_path: str = "pokegold.sym",
    max_events: int = 120,
    max_links: int = 160,
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_traces, trace_errors = load_traces(traces=traces, root=root)
    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    sym_path = resolve_path(symbols_path, root=root)
    symbol_table = parse_symbol_table(sym_path) if sym_path.exists() else {}
    symbol_by_address = build_symbol_address_index(symbol_table)
    warnings = [] if sym_path.exists() else [f"symbol file not found; address annotation disabled: {symbols_path}"]

    events: list[dict[str, Any]] = []
    for loaded in loaded_traces:
        events.extend(
            extract_trace_events(
                loaded["data"],
                source=loaded["source"],
                symbol_by_address=symbol_by_address,
            )
        )
    for loaded in loaded_reports:
        events.extend(
            extract_trace_events(
                loaded["data"],
                source=loaded["source"],
                symbol_by_address=symbol_by_address,
            )
        )
    events = finalize_events(events)

    queried_symbols = tuple(unique_list([*symbols, *watch_symbols, *symbols_from_symptom(symptom)]))
    query = build_query(
        symbols=queried_symbols,
        addresses=addresses,
        rules=rules,
        source_files=source_files,
        symptom=symptom,
        symbol_table=symbol_table,
    )
    enriched_events = enrich_events_with_sources(
        events,
        symbols_path=symbols_path,
        symbol_table=symbol_table,
        root=root,
        max_links=max_links,
    )
    matched_events = [
        event
        for event in enriched_events
        if event_matches_query(event, query)
    ]
    if not query["active"]:
        matched_events = enriched_events

    links = build_causal_links(enriched_events, matched_events, max_links=max_links)
    reverse_attributions = build_reverse_attributions(
        matched_events,
        links,
        max_items=min(max_events, 40),
    )
    paths = build_causal_paths(matched_events, links, max_paths=min(max_events, 40))
    commands = build_commands(
        symbols=queried_symbols,
        addresses=addresses,
        rules=rules,
        source_files=source_files,
        traces=traces,
        reports=reports,
        paths=paths,
    )
    errors = unique_list([*trace_errors, *report_errors])
    returned_events = matched_events[:max_events]

    return {
        "schema_version": 1,
        "kind": "unified_debugger_trace_index",
        "root": str(root),
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "symbols_path": symbols_path,
        "input_traces": [item["source"] for item in loaded_traces],
        "input_reports": [item["source"] for item in loaded_reports],
        "query": query,
        "all_event_count": len(enriched_events),
        "event_count": len(returned_events),
        "matched_event_count": len(matched_events),
        "write_event_count": sum(1 for event in matched_events if event["event_type"] in WRITE_EVENT_TYPES),
        "read_event_count": sum(1 for event in matched_events if event["event_type"] in READ_EVENT_TYPES),
        "flow_event_count": sum(1 for event in matched_events if event["event_type"] in FLOW_EVENT_TYPES),
        "events": returned_events,
        "address_index": build_address_index(matched_events),
        "symbol_index": build_symbol_index(matched_events),
        "rule_index": build_rule_index(matched_events),
        "causal_link_count": len(links),
        "causal_links": links[:max_links],
        "reverse_attribution_count": len(reverse_attributions),
        "reverse_attributions": reverse_attributions,
        "path_count": len(paths),
        "causal_paths": paths,
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "This normalizes trace evidence into event, causal-link, and bounded reverse-attribution indexes; use dynamic-taint when a dense opcode/register trace is available.",
            "Arbitrary trace schemas are inferred from common field names, so ambiguous address/value fields should be confirmed with replay or focused subsystem materialization.",
            "Writer-to-reader and prior-read attribution links are exact only when traces expose shared addresses, symbols, values, or rule/source context; otherwise they are provenance links from runtime events to source labels/rules.",
        ],
    }


def extract_trace_events(
    data: Any,
    *,
    source: str,
    symbol_by_address: dict[str, str],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    events.extend(
        state_patch_minimization_events(
            data,
            source=source,
            symbol_by_address=symbol_by_address,
        )
    )
    walk_trace_data(
        data,
        source=source,
        path="$",
        context={},
        events=events,
        symbol_by_address=symbol_by_address,
    )
    return events


def state_patch_minimization_events(
    data: Any,
    *,
    source: str,
    symbol_by_address: dict[str, str],
) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or data.get("kind") != "unified_debugger_minimization_plan":
        return []
    minimization = data.get("state_patch_minimization")
    if not isinstance(minimization, dict) or not minimization.get("attempted"):
        return []
    source_symbols = runtime_symbol_items(minimization.get("source_symbols"))
    source_files = [
        normalize_path(path)
        for path in string_items(minimization.get("source_files"))
        if looks_like_source_path(path)
    ]
    source_mem_by_address = {
        normalize_address(address)["address"]: origin
        for address, origin in source_mem_parts(minimization)
        if normalize_address(address)["address"]
    }
    addresses = state_patch_minimization_addresses(minimization)
    out: list[dict[str, Any]] = []
    for index, address_text in enumerate(addresses):
        address = normalize_address(address_text)
        if not address["address"]:
            continue
        state_symbol = (
            source_mem_by_address.get(address["address"])
            or symbol_by_address.get(address["bank_address"])
            or symbol_by_address.get(address["address"])
            or ""
        )
        out.append(
            {
                "id": "",
                "source": source,
                "json_path": f"$.state_patch_minimization.watch_addresses[{index}]",
                "event_type": "memory_patch",
                "order": 0,
                "frame": None,
                "index": index,
                "operation": "state_patch_minimization",
                "address": address["address"],
                "bank": address["bank"],
                "bank_address": address["bank_address"],
                "state_symbol": base_label(state_symbol) or state_symbol,
                "source_symbol": source_symbols[0] if source_symbols else "",
                "pc_symbol": source_symbols[0] if source_symbols else "",
                "pc_bank_address": "",
                "rule_id": "state_patch_minimization",
                "source_file": source_files[0] if source_files else "",
                "before": "",
                "after": "",
                "delta": "",
                "value": str(minimization.get("minimized_patch_count", "")),
                "registers": {},
                "candidate": str(minimization.get("out_report", "")),
                "source_mems": string_items(minimization.get("source_mems")),
                "watch_size": positive_int(minimization.get("watch_size")) or 1,
                "confidence": 0.82 if minimization.get("preserved") else 0.62,
                "evidence": [
                    "state_patch_minimization preserved"
                    if minimization.get("preserved")
                    else "state_patch_minimization attempted",
                    f"{minimization.get('original_patch_count', 0)} -> {minimization.get('minimized_patch_count', 0)} patches",
                    "source_mems=" + ",".join(string_items(minimization.get("source_mems"))[:4]),
                    f"out_report={minimization.get('out_report', '')}",
                ],
            }
        )
    return out


def walk_trace_data(
    data: Any,
    *,
    source: str,
    path: str,
    context: dict[str, Any],
    events: list[dict[str, Any]],
    symbol_by_address: dict[str, str],
) -> None:
    if isinstance(data, dict):
        local_context = update_context(context, data)
        event = event_from_record(
            data,
            source=source,
            path=path,
            context=local_context,
            symbol_by_address=symbol_by_address,
        )
        if event:
            events.append(event)
        events.extend(
            watch_value_events(
                data,
                source=source,
                path=path,
                context=local_context,
                symbol_by_address=symbol_by_address,
            )
        )
        events.extend(public_read_events(data, source=source, path=path, context=local_context, symbol_by_address=symbol_by_address))
        for key, value in data.items():
            walk_trace_data(
                value,
                source=source,
                path=f"{path}.{key}",
                context=local_context,
                events=events,
                symbol_by_address=symbol_by_address,
            )
    elif isinstance(data, list):
        for index, item in enumerate(data):
            walk_trace_data(
                item,
                source=source,
                path=f"{path}[{index}]",
                context=context,
                events=events,
                symbol_by_address=symbol_by_address,
            )


def update_context(context: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    local = dict(context)
    for key in (*SYMBOL_KEYS, *SOURCE_FILE_KEYS, *RULE_KEYS):
        value = data.get(key)
        if isinstance(value, str) and value:
            local[key] = value
    if isinstance(data.get("source"), dict):
        nested = data["source"]
        for key in (*SYMBOL_KEYS, *SOURCE_FILE_KEYS, *RULE_KEYS):
            value = nested.get(key)
            if isinstance(value, str) and value:
                local[key] = value
    return local


def event_from_record(
    data: dict[str, Any],
    *,
    source: str,
    path: str,
    context: dict[str, Any],
    symbol_by_address: dict[str, str],
) -> dict[str, Any] | None:
    event_type = classify_event(data)
    if not event_type:
        return None
    address = event_address(data, context=context)
    source_symbol = source_symbol_for(data, context) or first_symbol(data, context)
    if event_type == "watch_change":
        source_symbol = base_label(str(data.get("pc_label") or context.get("pc_label") or source_symbol))
    state_symbol = state_symbol_for(data, address=address, symbol_by_address=symbol_by_address)
    pc_symbol = base_label(str(data.get("pc_label") or context.get("pc_label") or source_symbol))
    if event_type == "control_flow" and pc_symbol:
        state_symbol = pc_symbol
    rule_id = first_string(data, RULE_KEYS) or first_string(context, RULE_KEYS)
    source_file = first_source_file(data, context)
    before = first_string(data, VALUE_BEFORE_KEYS)
    after = first_string(data, VALUE_AFTER_KEYS)
    if event_type == "score_delta":
        before = before or stringify(data.get("score_before"))
        after = after or stringify(data.get("score_after"))
    return {
        "id": "",
        "source": source,
        "json_path": path,
        "event_type": event_type,
        "order": 0,
        "frame": data.get("frame"),
        "index": data.get("index"),
        "operation": str(data.get("operation", "")),
        "address": address["address"],
        "bank": address["bank"],
        "bank_address": address["bank_address"],
        "state_symbol": state_symbol,
        "source_symbol": source_symbol,
        "pc_symbol": pc_symbol,
        "pc_bank_address": first_string(data, ("pc_bank_address",)),
        "rule_id": rule_id,
        "source_file": normalize_path(source_file) if source_file else "",
        "before": before,
        "after": after,
        "delta": stringify(data.get("delta")),
        "value": after or stringify(data.get("value")),
        "registers": registers_from_record(data),
        "candidate": candidate_summary(data.get("candidate")),
        "confidence": confidence_for_event(event_type, has_address=bool(address["address"])),
        "evidence": event_evidence(data, event_type=event_type),
    }


def public_read_events(
    data: dict[str, Any],
    *,
    source: str,
    path: str,
    context: dict[str, Any],
    symbol_by_address: dict[str, str],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for key in ("public_reads", "static_public_read_hints"):
        value = data.get(key)
        if not isinstance(value, list):
            continue
        for index, item in enumerate(value):
            if isinstance(item, dict):
                address = event_address(item, context=context)
                symbol = state_symbol_for(item, address=address, symbol_by_address=symbol_by_address)
                read_value = first_string(item, VALUE_AFTER_KEYS) or stringify(item.get("value"))
                out.append(
                    {
                        "id": "",
                        "source": source,
                        "json_path": f"{path}.{key}[{index}]",
                        "event_type": "public_read",
                        "order": 0,
                        "frame": item.get("frame", data.get("frame")),
                        "index": item.get("index", data.get("index")),
                        "operation": key,
                        "address": address["address"],
                        "bank": address["bank"],
                        "bank_address": address["bank_address"],
                        "state_symbol": symbol or base_label(str(item.get("symbol", ""))),
                        "source_symbol": first_symbol(data, context),
                        "pc_symbol": base_label(str(context.get("pc_label") or first_symbol(data, context))),
                        "pc_bank_address": first_string(data, ("pc_bank_address",)),
                        "rule_id": first_string(context, RULE_KEYS),
                        "source_file": normalize_path(first_source_file(item, context)) if first_source_file(item, context) else "",
                        "before": "",
                        "after": read_value,
                        "delta": "",
                        "value": read_value,
                        "registers": registers_from_record(item),
                        "candidate": "",
                        "confidence": 0.72 if address["address"] or symbol else 0.58,
                        "evidence": [f"{key} entry", stringify(item)[:180]],
                    }
                )
            elif isinstance(item, str) and item:
                out.append(
                    {
                        "id": "",
                        "source": source,
                        "json_path": f"{path}.{key}[{index}]",
                        "event_type": "source_hint",
                        "order": 0,
                        "frame": data.get("frame"),
                        "index": data.get("index"),
                        "operation": key,
                        "address": "",
                        "bank": "",
                        "bank_address": "",
                        "state_symbol": base_label(item),
                        "source_symbol": first_symbol(data, context),
                        "pc_symbol": base_label(str(context.get("pc_label") or first_symbol(data, context))),
                        "pc_bank_address": first_string(data, ("pc_bank_address",)),
                        "rule_id": first_string(context, RULE_KEYS),
                        "source_file": "",
                        "before": "",
                        "after": "",
                        "delta": "",
                        "value": item,
                        "registers": {},
                        "candidate": "",
                        "confidence": 0.5,
                        "evidence": [f"{key}: {item}"],
                    }
                )
    return out


def watch_value_events(
    data: dict[str, Any],
    *,
    source: str,
    path: str,
    context: dict[str, Any],
    symbol_by_address: dict[str, str],
) -> list[dict[str, Any]]:
    watch_values = data.get("watch_values")
    if not isinstance(watch_values, dict):
        return []
    if context.get("watch"):
        return []
    pc_symbol = base_label(str(data.get("pc_label") or context.get("pc_label") or first_symbol(data, context)))
    pc_address = normalize_address(data.get("pc"), bank=data.get("bank") or context.get("bank"))
    out: list[dict[str, Any]] = []
    for index, (raw_key, raw_value) in enumerate(watch_values.items()):
        key_text = str(raw_key)
        address = normalize_address(key_text)
        state_symbol = (
            symbol_by_address.get(address["bank_address"])
            or symbol_by_address.get(address["address"])
            or (base_label(key_text) if not address["address"] else "")
            or key_text
        )
        value = stringify(raw_value)
        out.append(
            {
                "id": "",
                "source": source,
                "json_path": f"{path}.watch_values[{index}]",
                "event_type": "memory_read",
                "order": 0,
                "frame": data.get("frame"),
                "index": data.get("index", data.get("seq")),
                "operation": "watch_values_snapshot",
                "address": address["address"],
                "bank": address["bank"],
                "bank_address": address["bank_address"],
                "state_symbol": state_symbol,
                "source_symbol": pc_symbol,
                "pc_symbol": pc_symbol,
                "pc_bank_address": first_string(data, ("pc_bank_address",)) or pc_address["bank_address"],
                "rule_id": first_string(context, RULE_KEYS),
                "source_file": normalize_path(first_source_file(data, context)) if first_source_file(data, context) else "",
                "before": "",
                "after": value,
                "delta": "",
                "value": value,
                "registers": registers_from_record(data),
                "candidate": "",
                "confidence": 0.78 if address["address"] or state_symbol else 0.58,
                "evidence": [
                    "instruction trace watch_values snapshot",
                    f"watch_values[{key_text}]={value}",
                ],
            }
        )
    return out


def classify_event(data: dict[str, Any]) -> str:
    raw_type = str(data.get("event_type", "")).lower()
    if raw_type in WRITE_EVENT_TYPES or raw_type in READ_EVENT_TYPES or raw_type in FLOW_EVENT_TYPES:
        return raw_type
    if raw_type == "score_delta" or has_any(data, ("score_before", "score_after", "score_pointer")):
        return "score_delta"
    if data.get("kind") == "memory_patch" or has_any(data, ("patch_address", "patched_value")):
        return "memory_patch"
    if data.get("watch") and (has_any(data, ("old_hex", "new_hex", "old_value", "new_value"))):
        return "watch_change"
    if has_any(data, ("write", "writes")) or str(data.get("access", "")).lower() == "write":
        return "memory_write"
    if has_any(data, ("read", "reads")) or str(data.get("access", "")).lower() == "read":
        return "memory_read"
    if has_any(data, ("full_symbol", "rule_id", "hook_address", "hook_bank")):
        return "rule_hit"
    if has_any(data, ("pc_label", "pc_bank_address", "pc")):
        return "control_flow"
    return ""


def event_address(data: dict[str, Any], *, context: dict[str, Any]) -> dict[str, str]:
    bank_address = first_string(data, ("bank_address",))
    if bank_address:
        parsed = parse_bank_address(bank_address)
        if parsed["address"]:
            return parsed
    address = first_string(data, ADDRESS_KEYS) or first_string(data, ("patch_address",))
    bank = first_string(data, BANK_KEYS) or first_string(context, BANK_KEYS)
    return normalize_address(address, bank=bank)


def normalize_address(address: Any, *, bank: Any = "") -> dict[str, str]:
    address_text = hex_text(address)
    bank_text = hex_text(bank, width=2)
    if not address_text:
        return {"address": "", "bank": bank_text, "bank_address": ""}
    address_text = address_text[-4:].upper().rjust(4, "0")
    bank_address = f"{bank_text}:{address_text}" if bank_text else ""
    return {"address": address_text, "bank": bank_text, "bank_address": bank_address}


def parse_bank_address(value: str) -> dict[str, str]:
    text = value.strip().replace("$", "")
    if ":" not in text:
        return normalize_address(text)
    bank, address = text.split(":", 1)
    return normalize_address(address, bank=bank)


def hex_text(value: Any, *, width: int = 4) -> str:
    if value is None:
        return ""
    if isinstance(value, int):
        return f"{value:0{width}X}"
    text = str(value).strip()
    if not text:
        return ""
    if text.startswith(("0x", "0X")):
        text = text[2:]
    if text.startswith("$"):
        text = text[1:]
    text = "".join(char for char in text if char in "0123456789abcdefABCDEF")
    if not text:
        return ""
    return text.upper().rjust(min(width, len(text)), "0")


def state_patch_minimization_addresses(item: dict[str, Any]) -> list[str]:
    addresses = [
        *string_items(item.get("watch_addresses")),
        *source_mem_addresses(item),
    ]
    for result in dict_items(item.get("results")):
        addresses.extend(string_items(result.get("semantic_watch_addresses")))
        addresses.extend(string_items(result.get("semantic_replay_watch_addresses")))
        addresses.extend(source_mem_addresses(result))
    return unique_list(addresses)


def source_mem_addresses(route: dict[str, Any]) -> list[str]:
    return unique_list(
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


def state_symbol_for(
    data: dict[str, Any],
    *,
    address: dict[str, str],
    symbol_by_address: dict[str, str],
) -> str:
    if data.get("score_pointer"):
        return "wEnemyAIMoveScores"
    direct = first_string(data, ("watch", "state_symbol", "symbol", "target"))
    if direct:
        return base_label(direct) or direct
    if address["bank_address"] and address["bank_address"] in symbol_by_address:
        return symbol_by_address[address["bank_address"]]
    if address["address"] and address["address"] in symbol_by_address:
        return symbol_by_address[address["address"]]
    return ""


def first_symbol(data: dict[str, Any], context: dict[str, Any]) -> str:
    nested_source = data.get("source") if isinstance(data.get("source"), dict) else {}
    for source in (nested_source, data, context):
        value = first_string(source, SYMBOL_KEYS)
        if value:
            return base_label(value) or value
    return ""


def source_symbol_for(data: dict[str, Any], context: dict[str, Any]) -> str:
    nested_source = data.get("source") if isinstance(data.get("source"), dict) else {}
    source_keys = (
        "source_symbol",
        "pc_symbol",
        "pc_label",
        "source_label",
        "full_symbol",
        "callsite_symbol",
        "callsite_rule_symbol",
        "helper_symbol",
        "closed_by",
        "resolved",
        "query",
    )
    for source in (nested_source, data, context):
        value = first_string(source, source_keys)
        if value:
            return base_label(value) or value
    return ""


def first_source_file(data: dict[str, Any], context: dict[str, Any]) -> str:
    for source in (data, data.get("source") if isinstance(data.get("source"), dict) else {}, context):
        value = first_string(source, SOURCE_FILE_KEYS)
        if value and looks_like_source_path(value):
            return value
    return ""


def enrich_events_with_sources(
    events: list[dict[str, Any]],
    *,
    symbols_path: str,
    symbol_table: dict[str, dict[str, Any]],
    root: Path,
    max_links: int,
) -> list[dict[str, Any]]:
    symbol_names = unique_list(
        [
            event.get("state_symbol", "")
            for event in events
            if event.get("state_symbol")
        ]
        + [
            event.get("source_symbol", "")
            for event in events
            if event.get("source_symbol")
        ]
        + [
            event.get("pc_symbol", "")
            for event in events
            if event.get("pc_symbol")
        ]
    )[:max_links]
    sym_path = resolve_path(symbols_path, root=root)
    if not symbol_names or not sym_path.exists():
        return events
    slice_report = build_slice_report(
        symbols_path=symbols_path,
        symbols=tuple(symbol_names),
        max_depth=1,
        max_edges=max_links,
        root=root,
    )
    source_by_symbol = source_files_from_slice(slice_report)
    address_by_symbol = {
        label: data.get("bank_address", "")
        for label, data in symbol_table.items()
    }
    enriched = []
    for event in events:
        copied = dict(event)
        state_symbol = copied.get("state_symbol", "")
        if state_symbol and source_by_symbol.get(state_symbol):
            copied["state_file"] = source_by_symbol[state_symbol][0]
        if state_symbol and not copied.get("bank_address") and not copied.get("address") and address_by_symbol.get(state_symbol):
            copied["bank_address"] = address_by_symbol[state_symbol]
            copied["address"] = copied["bank_address"].split(":", 1)[1]
            copied["bank"] = copied["bank_address"].split(":", 1)[0]
        for symbol_key in ("source_symbol", "pc_symbol"):
            symbol = copied.get(symbol_key, "")
            if symbol and not copied.get("source_file") and source_by_symbol.get(symbol):
                copied["source_file"] = source_by_symbol[symbol][0]
        enriched.append(copied)
    return enriched


def source_files_from_slice(slice_report: dict[str, Any]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for target in dict_items(slice_report.get("targets")):
        symbols = unique_list([str(target.get("query", "")), str(target.get("resolved", ""))])
        files = []
        definition = target.get("definition")
        if isinstance(definition, dict) and definition.get("path"):
            files.append(str(definition["path"]))
        for edge in [*dict_items(target.get("incoming")), *dict_items(target.get("outgoing"))]:
            if edge.get("path"):
                files.append(str(edge["path"]))
        for symbol in symbols:
            if symbol:
                out[symbol] = unique_list(files)
    return out


def finalize_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, str, str, str]] = set()
    for order, event in enumerate(events):
        copied = dict(event)
        copied["order"] = order
        copied["id"] = f"ev_{order:05d}"
        key = (
            copied["source"],
            copied["json_path"],
            copied["event_type"],
            copied.get("address", ""),
            copied.get("state_symbol", ""),
            copied.get("source_symbol", ""),
            copied.get("rule_id", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(copied)
    return deduped


def build_query(
    *,
    symbols: tuple[str, ...],
    addresses: tuple[str, ...],
    rules: tuple[str, ...],
    source_files: tuple[str, ...],
    symptom: str,
    symbol_table: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    normalized_symbols = unique_list(base_label(symbol) or symbol for symbol in symbols if symbol)
    normalized_addresses = unique_list(
        normalized
        for address in addresses
        for normalized in address_query_variants(address)
    )
    for symbol in normalized_symbols:
        entry = symbol_table.get(symbol)
        if entry:
            normalized_addresses.extend([entry["address_hex"], entry["bank_address"]])
    normalized_addresses = unique_list(normalized_addresses)
    normalized_files = unique_list(normalize_path(path) for path in source_files if path)
    normalized_rules = unique_list(rules)
    return {
        "active": bool(normalized_symbols or normalized_addresses or normalized_rules or normalized_files or symptom),
        "symbols": normalized_symbols,
        "addresses": normalized_addresses,
        "rules": normalized_rules,
        "source_files": normalized_files,
        "symptom": symptom,
    }


def event_matches_query(event: dict[str, Any], query: dict[str, Any]) -> bool:
    if not query["active"]:
        return True
    event_symbols = {
        event.get("state_symbol", ""),
        event.get("source_symbol", ""),
        event.get("pc_symbol", ""),
    }
    event_addresses = {event.get("address", ""), event.get("bank_address", "")}
    if event_symbols.intersection(query["symbols"]):
        return True
    if event_addresses.intersection(query["addresses"]):
        return True
    if event.get("rule_id") in query["rules"]:
        return True
    if event.get("source_file") in query["source_files"]:
        return True
    symptom = str(query.get("symptom", "")).lower()
    if symptom:
        text = event_text(event)
        return any(word for word in symptom.split() if len(word) > 3 and word in text)
    return False


def build_causal_links(
    events: list[dict[str, Any]],
    matched_events: list[dict[str, Any]],
    *,
    max_links: int,
) -> list[dict[str, Any]]:
    matched_ids = {event["id"] for event in matched_events}
    links: list[dict[str, Any]] = []
    last_writer_by_state: dict[str, dict[str, Any]] = {}
    recent_events: list[dict[str, Any]] = []
    for event in events:
        state_key = state_key_for(event)
        if event["event_type"] in READ_EVENT_TYPES and state_key:
            writer = last_writer_by_state.get(state_key)
            if writer and (event["id"] in matched_ids or writer["id"] in matched_ids):
                links.append(
                    causal_link(
                        writer,
                        event,
                        "last_writer",
                        state_key,
                        0.9,
                    )
            )
        if event["event_type"] in WRITE_EVENT_TYPES and state_key:
            previous = last_writer_by_state.get(state_key)
            if previous and (event["id"] in matched_ids or previous["id"] in matched_ids):
                links.append(
                    causal_link(
                        previous,
                        event,
                        "overwrites",
                        state_key,
                        0.82,
                    )
                )
            if event["id"] in matched_ids:
                links.extend(
                    reverse_dependency_links(
                        recent_events,
                        event,
                        max_links=max(0, max_links - len(links)),
                    )
                )
            last_writer_by_state[state_key] = event
        if event["id"] in matched_ids and event.get("source_symbol"):
            links.append(
                {
                    "from_event": event["id"],
                    "to_event": "",
                    "relation": "source_symbol",
                    "state": event.get("source_symbol", ""),
                    "confidence": 0.72,
                    "evidence": f"{event['event_type']} attributed to {event.get('source_symbol')}",
                }
            )
        recent_events.append(event)
        if len(recent_events) > 32:
            recent_events = recent_events[-32:]
        if len(links) >= max_links:
            break
    return links


def reverse_dependency_links(
    recent_events: list[dict[str, Any]],
    event: dict[str, Any],
    *,
    max_links: int,
) -> list[dict[str, Any]]:
    if max_links <= 0:
        return []
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for prior in reversed(recent_events):
        relation = reverse_relation(prior, event)
        if not relation:
            continue
        state = display_state_for(prior)
        key = (relation, str(state))
        if key in seen:
            continue
        seen.add(key)
        confidence = reverse_relation_confidence(relation, prior, event)
        out.append(causal_link(prior, event, relation, str(state), confidence))
        if len(out) >= min(5, max_links):
            break
    return out


def reverse_relation(prior: dict[str, Any], event: dict[str, Any]) -> str:
    if prior["event_type"] in READ_EVENT_TYPES:
        if event_context_matches(prior, event) or shared_value(prior, event):
            return "prior_read"
    if shared_value(prior, event):
        return "value_source"
    if prior["event_type"] in FLOW_EVENT_TYPES and event_context_matches(prior, event):
        return "source_context"
    return ""


def reverse_relation_confidence(relation: str, prior: dict[str, Any], event: dict[str, Any]) -> float:
    if relation == "prior_read":
        return 0.88 if event_context_matches(prior, event) else 0.76
    if relation == "value_source":
        return 0.72
    if relation == "source_context":
        return 0.66
    return 0.6


def event_context_matches(left: dict[str, Any], right: dict[str, Any]) -> bool:
    for key in ("rule_id", "source_file"):
        if left.get(key) and left.get(key) == right.get(key):
            return True
    left_symbols = {left.get("source_symbol", ""), left.get("pc_symbol", "")}
    right_symbols = {right.get("source_symbol", ""), right.get("pc_symbol", "")}
    return bool(left_symbols.intersection(right_symbols) - {""})


def shared_value(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_values = trace_values(left, keys=("after", "value", "delta"))
    right_values = trace_values(right, keys=("before", "value", "delta"))
    right_values.extend(str(value) for value in right.get("registers", {}).values() if value)
    return bool(set(left_values).intersection(right_values))


def trace_values(event: dict[str, Any], *, keys: tuple[str, ...]) -> list[str]:
    out: list[str] = []
    for key in keys:
        value = str(event.get(key, "")).strip()
        if value:
            out.append(value)
            normalized = hex_text(value)
            if normalized:
                out.append(normalized)
    return unique_list(out)


def build_causal_paths(
    events: list[dict[str, Any]],
    links: list[dict[str, Any]],
    *,
    max_paths: int,
) -> list[dict[str, Any]]:
    incoming_by_event: dict[str, list[dict[str, Any]]] = {}
    for link in links:
        if link.get("to_event"):
            incoming_by_event.setdefault(str(link["to_event"]), []).append(link)
    paths = []
    for event in events:
        if len(paths) >= max_paths:
            break
        paths.append(path_from_event(event, incoming_by_event.get(event["id"], [])))
    paths.sort(key=lambda item: (-int(item["score"]), -float(item["confidence"]), item["id"]))
    return paths[:max_paths]


def build_reverse_attributions(
    events: list[dict[str, Any]],
    links: list[dict[str, Any]],
    *,
    max_items: int,
) -> list[dict[str, Any]]:
    incoming_by_event: dict[str, list[dict[str, Any]]] = {}
    for link in links:
        relation = str(link.get("relation", ""))
        if relation not in REVERSE_ATTRIBUTION_RELATIONS or not link.get("to_event"):
            continue
        incoming_by_event.setdefault(str(link["to_event"]), []).append(link)
    out = []
    for event in events:
        if len(out) >= max_items:
            break
        if event["event_type"] not in WRITE_EVENT_TYPES:
            continue
        contributors = [
            attribution_contributor(link)
            for link in incoming_by_event.get(event["id"], [])
        ]
        contributors = [item for item in contributors if item["event_id"]]
        if not contributors:
            continue
        confidence = max(float(item["confidence"]) for item in contributors)
        state = event.get("state_symbol") or event.get("bank_address") or event.get("address") or "state"
        related_symbols = unique_list(
            [
                event.get("state_symbol", ""),
                event.get("source_symbol", ""),
                event.get("pc_symbol", ""),
                *[
                    item["state"]
                    for item in contributors
                    if looks_like_symbol_state(item["state"])
                ],
            ]
        )
        related_files = unique_list([event.get("source_file", "")])
        out.append(
            {
                "event_id": event["id"],
                "title": f"{state} {event['event_type']} reverse attribution",
                "state": state,
                "event_type": event["event_type"],
                "source_symbol": event.get("source_symbol") or event.get("pc_symbol") or "",
                "confidence": round(confidence, 3),
                "contributor_count": len(contributors),
                "contributors": contributors[:8],
                "related_symbols": related_symbols,
                "related_files": related_files,
                "evidence": [
                    f"{item['relation']} via {item['state']}"
                    for item in contributors[:4]
                ],
                "commands": commands_for_event(
                    event,
                    related_symbols=related_symbols,
                    related_files=related_files,
                ),
            }
        )
    return out


def attribution_contributor(link: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": str(link.get("from_event", "")),
        "relation": str(link.get("relation", "")),
        "state": str(link.get("state", "")),
        "confidence": round(float(link.get("confidence", 0.0)), 3),
        "evidence": str(link.get("evidence", "")),
    }


def path_from_event(event: dict[str, Any], incoming: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = []
    state = event.get("state_symbol") or event.get("bank_address") or event.get("address") or event.get("rule_id") or event["event_type"]
    nodes.append(path_node("state", event["event_type"], state, event=event))
    if event.get("source_symbol") or event.get("pc_symbol"):
        nodes.append(
            path_node(
                "runtime",
                "source",
                event.get("source_symbol") or event.get("pc_symbol"),
                event=event,
            )
        )
    if event.get("rule_id"):
        nodes.append(path_node("rule", "rule_id", event["rule_id"], event=event))
    if event.get("source_file"):
        nodes.append(path_node("source", "file", event["source_file"], event=event))
    for link in incoming[:2]:
        label = f"{link['relation']}: {link['state']}"
        nodes.insert(
            0,
            {
                "id": safe_id(f"prior:{link['from_event']}"),
                "type": "runtime",
                "role": link["relation"],
                "label": label,
                "symbol": link["state"] if looks_like_symbol_state(str(link["state"])) else "",
                "file": "",
                "line": None,
                "detail": link["evidence"],
            },
        )
    score = score_for_path(event, incoming)
    confidence = min(0.98, float(event.get("confidence", 0.5)) + 0.08 * len(incoming))
    related_symbols = unique_list(
        [
            event.get("state_symbol", ""),
            event.get("source_symbol", ""),
            event.get("pc_symbol", ""),
            *[
                link.get("state", "")
                for link in incoming
                if looks_like_symbol_state(str(link.get("state", "")))
            ],
        ]
    )
    related_files = unique_list([event.get("source_file", "")])
    return {
        "id": f"path_{event['id']}",
        "title": path_title(event),
        "score": score,
        "confidence": round(confidence, 3),
        "event_id": event["id"],
        "nodes": nodes,
        "edges": path_edges(nodes),
        "evidence": event.get("evidence", [])[:4],
        "related_symbols": related_symbols,
        "related_files": related_files,
        "commands": commands_for_event(event, related_symbols=related_symbols, related_files=related_files),
    }


def path_node(node_type: str, role: str, label: str, *, event: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": safe_id(f"{node_type}:{role}:{label}:{event['id']}"),
        "type": node_type,
        "role": role,
        "label": label,
        "symbol": label if node_type in {"state", "runtime"} and label and "/" not in label else "",
        "file": event.get("source_file", "") if node_type == "source" else "",
        "line": None,
        "detail": event_detail(event),
    }


def path_edges(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "from": left["id"],
            "to": right["id"],
            "relation": relation_for(left, right),
            "evidence": right.get("detail", ""),
        }
        for left, right in zip(nodes, nodes[1:])
    ]


def relation_for(left: dict[str, Any], right: dict[str, Any]) -> str:
    if left["role"] in {"last_writer", "overwrites"}:
        return str(left["role"])
    if right["type"] == "runtime":
        return "attributed_to"
    if right["type"] == "rule":
        return "guarded_by_rule"
    if right["type"] == "source":
        return "defined_or_referenced_in"
    return "supports"


def build_address_index(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        key = event.get("bank_address") or event.get("address")
        if key:
            grouped.setdefault(str(key), []).append(event)
    return [
        {
            "address": address,
            "event_count": len(items),
            "write_count": sum(1 for item in items if item["event_type"] in WRITE_EVENT_TYPES),
            "read_count": sum(1 for item in items if item["event_type"] in READ_EVENT_TYPES),
            "symbols": unique_list(item.get("state_symbol", "") for item in items),
            "last_event": items[-1]["id"],
        }
        for address, items in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))[:80]
    ]


def build_symbol_index(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        for symbol in (event.get("state_symbol"), event.get("source_symbol"), event.get("pc_symbol")):
            if symbol:
                grouped.setdefault(str(symbol), []).append(event)
    return [
        {
            "symbol": symbol,
            "event_count": len(items),
            "event_types": unique_list(item["event_type"] for item in items),
            "sources": unique_list(item["source"] for item in items),
        }
        for symbol, items in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))[:80]
    ]


def build_rule_index(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        if event.get("rule_id"):
            grouped.setdefault(str(event["rule_id"]), []).append(event)
    return [
        {
            "rule_id": rule,
            "event_count": len(items),
            "symbols": unique_list(
                symbol
                for item in items
                for symbol in (item.get("state_symbol"), item.get("source_symbol"), item.get("pc_symbol"))
                if symbol
            ),
        }
        for rule, items in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))[:80]
    ]


def build_commands(
    *,
    symbols: tuple[str, ...],
    addresses: tuple[str, ...],
    rules: tuple[str, ...],
    source_files: tuple[str, ...],
    traces: tuple[str, ...],
    reports: tuple[str, ...],
    paths: list[dict[str, Any]],
) -> list[str]:
    commands = []
    for trace in traces[:4]:
        commands.append(f"python -m tools.debugger coverage --trace {trace}")
        commands.append(f"python -m tools.debugger explain --trace {trace}")
    for report in reports[:4]:
        commands.append(f"python -m tools.debugger explain --report {report}")
        commands.append(f"python -m tools.debugger provenance --report {report}")
        commands.append(f"python -m tools.debugger taint --report {report}")
        commands.append(f"python -m tools.debugger slice --report {report}")
        commands.append(f"python -m tools.debugger rank --report {report}")
    for symbol in symbols[:6]:
        commands.append(f"python -m tools.debugger replay --symbol {symbol}")
        commands.append(f"python -m tools.debugger taint --symbol {symbol}")
        commands.append(f"python -m tools.debugger slice --symbol {symbol}")
        commands.append(f"python -m tools.debugger provenance --symbol {symbol}")
    for address in addresses[:6]:
        commands.append(f"python -m tools.debugger trace-index --address {command_address_arg(address)}")
    for rule in rules[:6]:
        commands.append(f"python -m tools.debugger coverage --rule {rule}")
    for path in source_files[:6]:
        commands.append(f"python -m tools.debugger gate --changed-file {path}")
    for causal_path in paths[:6]:
        commands.extend(causal_path.get("commands", [])[:3])
    return unique_list(commands)[:48]


def commands_for_event(
    event: dict[str, Any],
    *,
    related_symbols: list[str],
    related_files: list[str],
) -> list[str]:
    commands = []
    for symbol in related_symbols[:4]:
        commands.append(f"python -m tools.debugger explain --symbol {symbol}")
        commands.append(f"python -m tools.debugger replay --symbol {symbol}")
        commands.append(f"python -m tools.debugger taint --symbol {symbol}")
        commands.append(f"python -m tools.debugger slice --symbol {symbol}")
    if event.get("address"):
        address = str(event.get("address"))
        watch_size = positive_int(event.get("watch_size")) or positive_int(event.get("sink_size")) or 1
        watch_size_arg = f" --watch-size {watch_size}" if watch_size != 1 else ""
        sink_size_arg = f" --sink-size {watch_size}" if watch_size != 1 else ""
        source_mem_args = " ".join(
            f"--source-mem {source_mem}"
            for source_mem in string_items(event.get("source_mems"))[:4]
        )
        command_address = command_address_arg(address)
        commands.append(f"python -m tools.debugger trace-index --address {command_address}")
        commands.append(f"python -m tools.debugger replay --watch-address {command_address}{watch_size_arg} --execute-watch")
        commands.append(f"python -m tools.debugger watch --watch-address {command_address}{watch_size_arg} --execute")
        commands.append(
            "python -m tools.debugger dynamic-taint "
            + " ".join(
                part
                for part in [
                    source_mem_args,
                    f"--sink-address {command_address_arg(address)}{sink_size_arg}",
                ]
                if part
            )
        )
    if event.get("rule_id"):
        commands.append(f"python -m tools.debugger coverage --rule {event.get('rule_id')}")
    for path in related_files[:3]:
        commands.append(f"python -m tools.debugger explain --changed-file {path}")
        commands.append(f"python -m tools.debugger gate --changed-file {path}")
    return unique_list(commands)


def build_symbol_address_index(symbol_table: dict[str, dict[str, Any]]) -> dict[str, str]:
    out = {}
    address_counts: dict[str, int] = {}
    for data in symbol_table.values():
        if data.get("address_hex"):
            address = str(data["address_hex"]).upper()
            address_counts[address] = address_counts.get(address, 0) + 1
    for label, data in symbol_table.items():
        if data.get("bank_address"):
            out.setdefault(str(data["bank_address"]).upper(), label)
        if data.get("address_hex") and address_counts.get(str(data["address_hex"]).upper(), 0) == 1:
            out.setdefault(str(data["address_hex"]).upper(), label)
    return out


def symbols_from_symptom(symptom: str) -> list[str]:
    lowered = symptom.lower()
    return unique_list(symbol for keyword, symbol in SYMPTOM_SYMBOLS.items() if keyword in lowered)


def address_query_variants(value: str) -> list[str]:
    parsed = parse_bank_address(value)
    return unique_list([parsed["address"], parsed["bank_address"]])


def has_any(data: dict[str, Any], keys: tuple[str, ...]) -> bool:
    return any(key in data for key in keys)


def first_string(data: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
        if isinstance(value, int):
            return str(value)
    return ""


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    try:
        return json.dumps(value, sort_keys=True)
    except TypeError:
        return str(value)


def positive_int(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return number if number > 0 else 0


def registers_from_record(data: dict[str, Any]) -> dict[str, str]:
    out = {}
    for key in REGISTER_KEYS:
        if key in data:
            out[key] = stringify(data[key])
    return out


def candidate_summary(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    for key in ("move_name", "species", "name", "kind"):
        if value.get(key):
            return str(value[key])
    return stringify(value)[:120]


def confidence_for_event(event_type: str, *, has_address: bool) -> float:
    base = {
        "watch_change": 0.9,
        "score_delta": 0.86,
        "memory_write": 0.78,
        "memory_patch": 0.78,
        "memory_read": 0.72,
        "public_read": 0.7,
        "rule_hit": 0.64,
        "control_flow": 0.6,
        "source_hint": 0.5,
    }.get(event_type, 0.45)
    return min(0.96, base + (0.04 if has_address else 0.0))


def event_evidence(data: dict[str, Any], *, event_type: str) -> list[str]:
    evidence = [event_type]
    for key in ("operation", "event_type", "rule_id", "delta", "old_hex", "new_hex", "score_before", "score_after"):
        if key in data:
            evidence.append(f"{key}={stringify(data[key])}")
    return evidence[:8]


def event_text(event: dict[str, Any]) -> str:
    return " ".join(
        stringify(event.get(key, ""))
        for key in (
            "event_type",
            "operation",
            "state_symbol",
            "source_symbol",
            "pc_symbol",
            "rule_id",
            "source_file",
            "candidate",
            "evidence",
        )
    ).lower()


def state_key_for(event: dict[str, Any]) -> str:
    return str(event.get("bank_address") or event.get("address") or event.get("state_symbol") or "")


def display_state_for(event: dict[str, Any]) -> str:
    return str(
        event.get("state_symbol")
        or event.get("bank_address")
        or event.get("address")
        or event.get("source_symbol")
        or event.get("rule_id")
        or event["event_type"]
    )


def looks_like_symbol_state(value: str) -> bool:
    text = str(value).strip()
    if not text or ":" in text or "/" in text or "\\" in text:
        return False
    if text.startswith(("$", "0x", "0X", ".")):
        return False
    if len(text) <= 4 and all(char in "0123456789abcdefABCDEF" for char in text):
        return False
    return text[0].isalpha() and any(char.isupper() or char == "_" for char in text)


def causal_link(
    left: dict[str, Any],
    right: dict[str, Any],
    relation: str,
    state: str,
    confidence: float,
) -> dict[str, Any]:
    return {
        "from_event": left["id"],
        "to_event": right["id"],
        "relation": relation,
        "state": state,
        "confidence": confidence,
        "evidence": f"{left['event_type']} -> {right['event_type']} via {state}",
    }


def event_detail(event: dict[str, Any]) -> str:
    pieces = []
    if event.get("bank_address") or event.get("address"):
        pieces.append(event.get("bank_address") or event.get("address"))
    if event.get("before") or event.get("after"):
        pieces.append(f"{event.get('before', '')}->{event.get('after', '')}")
    if event.get("operation"):
        pieces.append(str(event["operation"]))
    return " ".join(piece for piece in pieces if piece)


def path_title(event: dict[str, Any]) -> str:
    state = event.get("state_symbol") or event.get("bank_address") or event.get("address") or "state"
    source = event.get("source_symbol") or event.get("pc_symbol") or event.get("rule_id") or "trace"
    return f"{state} {event['event_type']} from {source}"


def score_for_path(event: dict[str, Any], incoming: list[dict[str, Any]]) -> int:
    base = {
        "watch_change": 88,
        "score_delta": 84,
        "memory_write": 78,
        "memory_patch": 76,
        "memory_read": 68,
        "public_read": 66,
        "rule_hit": 58,
        "control_flow": 52,
        "source_hint": 44,
    }.get(event["event_type"], 40)
    return min(98, base + len(incoming) * 5 + (4 if event.get("source_file") else 0))


def safe_id(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value)[:120]


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
        return [nested for item in value for nested in string_items(item)]
    if isinstance(value, dict):
        return [nested for item in value.values() for nested in string_items(item)]
    return [str(value)] if value else []


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
