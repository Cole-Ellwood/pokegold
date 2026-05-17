from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .localize import is_watchable_symbol
from .provenance import display_path, resolve_path
from .reporting import load_reports
from .slicing import build_slice_report


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
SYMBOL_LIST_KEYS = {"related_symbols"}
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

    slice_report = None
    if symbols or changed_files:
        slice_report = build_slice_report(
            symbols_path=symbols_path,
            symbols=symbols,
            source_files=changed_files,
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
        "covered_symbols": summarize_seen(observations["symbols"], limit=40),
        "covered_files": summarize_seen(observations["files"], limit=40),
        "covered_rules": summarize_seen(observations["rules"], limit=40),
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
    return {"symbols": {}, "files": {}, "rules": {}}


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
        source_file = normalize_path(str(scenario.get("source_file", "")))
        runtime_targets = scenario.get("runtime_targets") if isinstance(scenario.get("runtime_targets"), dict) else {}
        related_symbols = unique_list(
            [
                *string_items(scenario.get("related_symbols")),
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
    return "uncovered", []


def coverage_commands(target: dict[str, Any]) -> list[str]:
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
        return commands
    if target["type"] == "rule":
        return [
            f"python -m tools.debugger localize --symptom {target['id']}",
            "python -m tools.boss_ai_debugger generate --family all --count 500 --seed 1 --out .local\\tmp\\debugger_all_scenarios.jsonl",
            "python -m tools.boss_ai_debugger rom-score-materialize --scenarios <scenarios.jsonl> --limit 4 --compare-fast-score",
        ]
    return [
        f"python -m tools.debugger localize --changed-file {target['id']}",
        f"python -m tools.debugger slice --source-file {target['id']}",
        f"python -m tools.debugger gate --changed-file {target['id']}",
    ]


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
    if symbol.startswith(".") and context.get("parent_label"):
        return str(context["parent_label"]) + symbol
    return symbol


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def looks_like_source_path(path: str) -> bool:
    normalized = normalize_path(path)
    return bool(normalized and "/" in normalized and Path(normalized).suffix.lower() == ".asm")


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
