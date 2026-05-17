from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .localize import normalize_path
from .provenance import display_path, resolve_path
from .reporting import load_reports
from .trace_index import build_trace_index_report, unique_list
from .workflow import command_is_runnable


EVENT_MATCH_FIELDS = (
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
    "before",
    "after",
    "value",
    "delta",
    "operation",
)


def build_expectation_report(
    *,
    reports: tuple[str, ...] = (),
    traces: tuple[str, ...] = (),
    expectation_files: tuple[str, ...] = (),
    expectations: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    events: tuple[str, ...] = (),
    rules: tuple[str, ...] = (),
    addresses: tuple[str, ...] = (),
    source_files: tuple[str, ...] = (),
    symptom: str = "",
    symbols_path: str = "pokegold.sym",
    max_events: int = 1000,
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    loaded_sources, source_errors = load_source_files(
        source_files=source_files,
        root=root,
    )
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
    trace_index = build_trace_index_report(
        traces=traces,
        reports=reports,
        symbols_path=symbols_path,
        max_events=max(1, max_events),
        max_links=max(160, max_events),
        root=root,
    )
    evidence = collect_evidence(
        loaded_reports=loaded_reports,
        loaded_sources=loaded_sources,
        trace_index=trace_index,
    )
    results = [
        evaluate_expectation(expectation, evidence=evidence)
        for expectation in all_expectations
    ]
    errors = unique_list(
        [
            *report_errors,
            *source_errors,
            *expectation_errors,
            *trace_index.get("errors", []),
        ]
    )
    warnings = unique_list(
        [
            *trace_index.get("warnings", []),
            *([] if all_expectations else ["no expectations were provided"]),
        ]
    )
    failed = [item for item in results if item["status"] == "failed"]
    passed = [item for item in results if item["status"] == "passed"]
    skipped = [item for item in results if item["status"] == "skipped"]
    commands = unique_list(
        command
        for result in results
        for command in result.get("commands", [])
    )
    return {
        "schema_version": 1,
        "kind": "unified_debugger_expectation_report",
        "root": str(root),
        "valid": not errors,
        "passed": not failed and not errors and bool(all_expectations),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "input_reports": [item["source"] for item in loaded_reports],
        "input_traces": list(traces),
        "expectation_files": list(expectation_files),
        "symbols_path": symbols_path,
        "symptom": symptom,
        "expectation_count": len(results),
        "passed_count": len(passed),
        "failed_count": len(failed),
        "skipped_count": len(skipped),
        "evidence_event_count": len(evidence["events"]),
        "evidence_symbol_count": len(evidence["symbols"]),
        "evidence_rule_count": len(evidence["rules"]),
        "evidence_source_file_count": len(evidence["source_files"]),
        "evidence_scenario_count": len(evidence["scenario_ids"]),
        "evidence_state_precondition_count": len(evidence["state_preconditions"]),
        "evidence_state_patch_count": len(evidence["state_patches"]),
        "source_artifact_count": len(loaded_sources),
        "expectations": results,
        "evidence_summary": {
            "symbols": sorted(evidence["symbols"])[:80],
            "rules": sorted(evidence["rules"])[:80],
            "source_files": sorted(evidence["source_files"])[:80],
            "addresses": sorted(evidence["addresses"])[:80],
            "scenario_ids": sorted(evidence["scenario_ids"])[:80],
            "state_preconditions": evidence["state_preconditions"][:20],
            "state_patches": evidence["state_patches"][:20],
            "source_artifacts": evidence["source_artifacts"][:20],
            "report_errors": evidence["errors"][:20],
            "report_warnings": evidence["warnings"][:20],
        },
        "trace_index": {
            "event_count": trace_index.get("event_count", 0),
            "all_event_count": trace_index.get("all_event_count", 0),
            "causal_link_count": trace_index.get("causal_link_count", 0),
            "path_count": trace_index.get("path_count", 0),
        },
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "This evaluates high-level expectations against captured reports, traces, and explicitly supplied source files; it does not emulate missing behavior by itself.",
            "Expectation matches are only as strong as the supplied trace/report/source evidence. Use replay or subsystem materialization before treating an expectation pass as final ROM proof.",
            "Use subsystem mirrors for exact semantic oracles where they exist; this command gives every ROM surface a common expectation gate.",
        ],
    }


def load_expectation_files(
    *,
    expectation_files: tuple[str, ...],
    root: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    loaded: list[dict[str, Any]] = []
    errors: list[str] = []
    for raw_path in expectation_files:
        path = resolve_path(raw_path, root=root)
        if not path.exists():
            errors.append(f"missing expectation file: {raw_path}")
            continue
        try:
            records = load_expectation_records(path)
        except json.JSONDecodeError as exc:
            errors.append(f"{raw_path}: invalid JSON: {exc.msg}")
            continue
        except OSError as exc:
            errors.append(f"{raw_path}: {exc}")
            continue
        source = display_path(path, root=root)
        for index, record in enumerate(records, 1):
            copied = dict(record)
            copied.setdefault("source", source)
            copied.setdefault("id", f"{Path(raw_path).stem}_{index}")
            loaded.append(copied)
    return loaded, errors


def load_source_files(
    *,
    source_files: tuple[str, ...],
    root: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    loaded: list[dict[str, Any]] = []
    errors: list[str] = []
    for raw_path in source_files:
        normalized = normalize_path(raw_path)
        path = resolve_path(raw_path, root=root)
        if not path.exists():
            errors.append(f"missing source file: {raw_path}")
            continue
        if not path.is_file():
            errors.append(f"source path is not a file: {raw_path}")
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{raw_path}: {exc}")
            continue
        loaded.append(
            {
                "path": display_path(path, root=root),
                "query": normalized,
                "text": text,
                "line_count": len(text.splitlines()),
                "size_bytes": path.stat().st_size,
            }
        )
    return loaded, errors


def load_expectation_records(path: Path) -> list[dict[str, Any]]:
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
        if isinstance(data.get("expectations"), list):
            return [item for item in data["expectations"] if isinstance(item, dict)]
        return [data]
    return []


def parse_cli_expectation(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text in {"no-errors", "no_errors"}:
        return {"id": "cli_no_errors", "type": "no_errors", "source": "cli"}
    if text in {"report-valid", "report_valid"}:
        return {"id": "cli_report_valid", "type": "report_valid", "source": "cli"}
    if text.startswith("symbol:"):
        return {"id": f"cli_symbol_{safe_name(text[7:])}", "type": "symbol_observed", "symbol": text[7:], "source": "cli"}
    if text.startswith("symbol="):
        return {"id": f"cli_symbol_{safe_name(text[7:])}", "type": "symbol_observed", "symbol": text[7:], "source": "cli"}
    if text.startswith("rule:"):
        return {"id": f"cli_rule_{safe_name(text[5:])}", "type": "rule_observed", "rule_id": text[5:], "source": "cli"}
    if text.startswith("rule="):
        return {"id": f"cli_rule_{safe_name(text[5:])}", "type": "rule_observed", "rule_id": text[5:], "source": "cli"}
    if text.startswith("source:"):
        path = normalize_path(text[7:])
        return {"id": f"cli_source_{safe_name(path)}", "type": "source_observed", "source_file": path, "source": "cli"}
    if text.startswith("source="):
        path = normalize_path(text[7:])
        return {"id": f"cli_source_{safe_name(path)}", "type": "source_observed", "source_file": path, "source": "cli"}
    if text.startswith("address:"):
        return {"id": f"cli_address_{safe_name(text[8:])}", "type": "address_observed", "address": text[8:], "source": "cli"}
    if text.startswith("address="):
        return {"id": f"cli_address_{safe_name(text[8:])}", "type": "address_observed", "address": text[8:], "source": "cli"}
    if text.startswith("scenario:"):
        scenario_id = text.removeprefix("scenario:")
        return {"id": f"cli_scenario_{safe_name(scenario_id)}", "type": "scenario_observed", "scenario_id": scenario_id, "source": "cli"}
    if text.startswith("scenario="):
        scenario_id = text.removeprefix("scenario=")
        return {"id": f"cli_scenario_{safe_name(scenario_id)}", "type": "scenario_observed", "scenario_id": scenario_id, "source": "cli"}
    if text.startswith("precondition:"):
        return parse_precondition_expectation(text.removeprefix("precondition:"))
    if text.startswith("precondition="):
        return parse_precondition_expectation(text.removeprefix("precondition="))
    if text.startswith("state-precondition:"):
        return parse_precondition_expectation(text.removeprefix("state-precondition:"))
    if text.startswith("state-precondition="):
        return parse_precondition_expectation(text.removeprefix("state-precondition="))
    if text.startswith("patch:"):
        return parse_state_patch_expectation(text.removeprefix("patch:"))
    if text.startswith("patch="):
        return parse_state_patch_expectation(text.removeprefix("patch="))
    if text.startswith("state-patch:"):
        return parse_state_patch_expectation(text.removeprefix("state-patch:"))
    if text.startswith("state-patch="):
        return parse_state_patch_expectation(text.removeprefix("state-patch="))
    if text.startswith("event:"):
        event_type = text[6:]
        return {"id": f"cli_event_{safe_name(event_type)}", "type": "event_observed", "event_type": event_type, "source": "cli"}
    if text.startswith("event="):
        fields = parse_field_list(text)
        fields.setdefault("type", "event_observed")
        fields.setdefault("id", "cli_event_" + safe_name(str(fields.get("event_type", "event"))))
        fields.setdefault("source", "cli")
        return fields
    if text.startswith("no-event="):
        fields = parse_field_list("event=" + text.removeprefix("no-event="))
        fields["type"] = "event_absent"
        fields.setdefault("id", "cli_no_event_" + safe_name(str(fields.get("event_type", "event"))))
        fields.setdefault("source", "cli")
        return fields
    if text.startswith("contains="):
        value = text.removeprefix("contains=")
        return {"id": f"cli_contains_{safe_name(value)}", "type": "contains_text", "contains": value, "source": "cli"}
    if text.startswith("contains:"):
        value = text.removeprefix("contains:")
        return {"id": f"cli_contains_{safe_name(value)}", "type": "contains_text", "contains": value, "source": "cli"}
    if text.startswith("not-contains="):
        value = text.removeprefix("not-contains=")
        return {"id": f"cli_not_contains_{safe_name(value)}", "type": "text_absent", "contains": value, "source": "cli", "max_count": 0}
    if text.startswith("not-contains:"):
        value = text.removeprefix("not-contains:")
        return {"id": f"cli_not_contains_{safe_name(value)}", "type": "text_absent", "contains": value, "source": "cli", "max_count": 0}
    return {
        "id": "cli_contains_" + safe_name(text),
        "type": "contains_text",
        "contains": text,
        "source": "cli",
    }


def parse_precondition_expectation(value: str) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "type": "precondition_observed",
        "source": "cli",
    }
    for index, piece in enumerate(value.split(",")):
        piece = piece.strip()
        if not piece:
            continue
        if "=" not in piece:
            if index == 0:
                fields["precondition_kind"] = piece
            continue
        key, field_value = piece.split("=", 1)
        key = key.strip()
        field_value = field_value.strip()
        if key in {"precondition", "kind", "precondition_kind"}:
            key = "precondition_kind"
        elif key == "scenario":
            key = "scenario_id"
        elif key in {"watch", "watch_symbol"}:
            key = "symbol"
        fields[key] = field_value
    fields.setdefault("precondition_kind", value.strip())
    fields["id"] = "cli_precondition_" + safe_name(
        "_".join(
            item
            for item in (
                str(fields.get("precondition_kind", "")),
                str(fields.get("scenario_id", "")),
                str(fields.get("symbol", "")),
            )
            if item
        )
        or "state"
    )
    return fields


def parse_field_list(text: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for index, piece in enumerate(text.split(",")):
        piece = piece.strip()
        if not piece:
            continue
        if "=" in piece:
            key, value = piece.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key == "event":
                key = "event_type"
            elif key == "rule":
                key = "rule_id"
            elif key == "scenario":
                key = "scenario_id"
            elif key == "min":
                key = "min_count"
                value = int(value)
            elif key == "max":
                key = "max_count"
                value = int(value)
            fields[key] = value
        elif index == 0:
            fields["event_type"] = piece
    return fields


def parse_state_patch_expectation(value: str) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "type": "state_patch_observed",
        "source": "cli",
    }
    for index, piece in enumerate(value.split(",")):
        piece = piece.strip()
        if not piece:
            continue
        if "=" not in piece:
            if index == 0:
                fields["symbol"] = piece
            continue
        key, field_value = piece.split("=", 1)
        key = key.strip()
        field_value = field_value.strip()
        if key in {"patch", "state_patch", "watch", "watch_symbol"}:
            key = "symbol"
        elif key == "scenario":
            key = "scenario_id"
        elif key in {"expected", "after"}:
            key = "value"
        fields[key] = field_value
    fields.setdefault("symbol", value.strip())
    fields["id"] = "cli_state_patch_" + safe_name(
        "_".join(
            item
            for item in (
                str(fields.get("symbol", "")),
                str(fields.get("scenario_id", "")),
                str(fields.get("value", "")),
            )
            if item
        )
        or "patch"
    )
    return fields


def input_expectations(
    *,
    symbols: tuple[str, ...],
    events: tuple[str, ...],
    rules: tuple[str, ...],
    addresses: tuple[str, ...],
    source_files: tuple[str, ...],
) -> list[dict[str, Any]]:
    out = []
    for symbol in symbols:
        out.append({"id": f"input_symbol_{safe_name(symbol)}", "type": "symbol_observed", "symbol": symbol, "source": "input"})
    for event_type in events:
        out.append({"id": f"input_event_{safe_name(event_type)}", "type": "event_observed", "event_type": event_type, "source": "input"})
    for rule in rules:
        out.append({"id": f"input_rule_{safe_name(rule)}", "type": "rule_observed", "rule_id": rule, "source": "input"})
    for address in addresses:
        out.append({"id": f"input_address_{safe_name(address)}", "type": "address_observed", "address": address, "source": "input"})
    for path in source_files:
        normalized = normalize_path(path)
        out.append({"id": f"input_source_{safe_name(normalized)}", "type": "source_observed", "source_file": normalized, "source": "input"})
    return out


def normalize_expectations(expectations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for index, expectation in enumerate(expectations, 1):
        copied = dict(expectation)
        copied.setdefault("id", f"expectation_{index}")
        copied.setdefault("type", infer_expectation_type(copied))
        copied.setdefault("description", copied["id"])
        copied["min_count"] = int(copied.get("min_count", 1))
        if "max_count" in copied:
            copied["max_count"] = int(copied["max_count"])
        if copied.get("source_file"):
            copied["source_file"] = normalize_path(str(copied["source_file"]))
        if copied.get("rule") and not copied.get("rule_id"):
            copied["rule_id"] = copied["rule"]
        normalized.append(copied)
    return normalized


def infer_expectation_type(expectation: dict[str, Any]) -> str:
    if expectation.get("event_type"):
        return "event_observed"
    if expectation.get("precondition_kind") or expectation.get("watch_symbol"):
        return "precondition_observed"
    if expectation.get("patch_symbol") or expectation.get("state_patch"):
        return "state_patch_observed"
    if expectation.get("symbol"):
        return "symbol_observed"
    if expectation.get("rule_id") or expectation.get("rule"):
        return "rule_observed"
    if expectation.get("source_file"):
        return "source_observed"
    if expectation.get("address") or expectation.get("bank_address"):
        return "address_observed"
    if expectation.get("scenario_id"):
        return "scenario_observed"
    return "contains_text" if expectation.get("contains") else "unknown"


def collect_evidence(
    *,
    loaded_reports: list[dict[str, Any]],
    loaded_sources: list[dict[str, Any]],
    trace_index: dict[str, Any],
) -> dict[str, Any]:
    evidence = {
        "events": list(trace_index.get("events", [])),
        "symbols": set(),
        "rules": set(),
        "source_files": set(),
        "source_artifacts": [],
        "addresses": set(),
        "scenario_ids": set(),
        "state_preconditions": [],
        "state_patches": [],
        "texts": [],
        "errors": [],
        "warnings": [],
        "invalid_reports": [],
    }
    collect_report_evidence(trace_index, source="trace-index", evidence=evidence)
    for loaded in loaded_reports:
        collect_report_evidence(loaded["data"], source=loaded["source"], evidence=evidence)
    for loaded in loaded_sources:
        add_source_evidence(loaded, evidence=evidence)
    for event in evidence["events"]:
        add_event_evidence(event, evidence)
    return evidence


def add_source_evidence(source: dict[str, Any], *, evidence: dict[str, Any]) -> None:
    path = normalize_path(str(source.get("path", source.get("query", ""))))
    query = normalize_path(str(source.get("query", path)))
    if path:
        evidence["source_files"].add(path)
    if query:
        evidence["source_files"].add(query)
    text = str(source.get("text", ""))
    if text:
        evidence["texts"].append(text)
    evidence["source_artifacts"].append(
        {
            "path": path,
            "query": query,
            "line_count": int(source.get("line_count", 0)),
            "size_bytes": int(source.get("size_bytes", 0)),
        }
    )


def collect_report_evidence(data: Any, *, source: str, evidence: dict[str, Any]) -> None:
    if isinstance(data, dict):
        collect_structured_state_evidence(data, source=source, evidence=evidence)
        if data.get("valid") is False:
            evidence["invalid_reports"].append(source)
        for error in string_items(data.get("errors")):
            evidence["errors"].append(f"{source}: {error}")
        for warning in string_items(data.get("warnings")):
            evidence["warnings"].append(f"{source}: {warning}")
        for key, value in data.items():
            if key in {
                "symbol",
                "watch",
                "query",
                "resolved",
                "state_symbol",
                "source_symbol",
                "pc_symbol",
                "full_symbol",
                "pc_label",
                "watch_symbols",
                "trace_symbols",
                "script_symbols",
                "source_labels",
                "related_symbols",
            }:
                for item in string_items(value):
                    if item:
                        evidence["symbols"].add(base_label(item))
            elif key in {"rule", "rule_id"}:
                for item in string_items(value):
                    if item:
                        evidence["rules"].add(item)
            elif key in {"source_file", "path"}:
                for item in string_items(value):
                    if "/" in normalize_path(item):
                        evidence["source_files"].add(normalize_path(item))
            elif key in {"address", "bank_address", "pc_bank_address"}:
                for item in string_items(value):
                    for address in address_variants(item):
                        evidence["addresses"].add(address)
            if isinstance(value, str):
                evidence["texts"].append(value)
            collect_report_evidence(value, source=source, evidence=evidence)
    elif isinstance(data, list):
        for item in data:
            collect_report_evidence(item, source=source, evidence=evidence)
    elif isinstance(data, str):
        evidence["texts"].append(data)


def collect_structured_state_evidence(data: dict[str, Any], *, source: str, evidence: dict[str, Any]) -> None:
    if data.get("kind") == "unified_debugger_content_state_materialization":
        collect_content_state_patch_evidence(data, source=source, evidence=evidence)
    collect_generic_state_patch_evidence(data, source=source, evidence=evidence)
    scenario_id = scenario_id_from_record(data)
    if scenario_id:
        evidence["scenario_ids"].add(scenario_id)
    preconditions = data.get("state_preconditions")
    if scenario_id and isinstance(preconditions, list):
        for index, precondition in enumerate(preconditions, 1):
            if isinstance(precondition, dict):
                add_state_precondition_evidence(
                    precondition,
                    scenario=data,
                    source=source,
                    index=index,
                    evidence=evidence,
                )
    if isinstance(data.get("scenario_id"), str) and data.get("kind") and data.get("values"):
        add_state_precondition_evidence(
            data,
            scenario={},
            source=source,
            index=1,
            evidence=evidence,
        )


def collect_content_state_patch_evidence(data: dict[str, Any], *, source: str, evidence: dict[str, Any]) -> None:
    out_state = normalize_path(str(data.get("out_state", "")))
    executed = bool(data.get("executed"))
    for materialization in dict_items(data.get("materializations")):
        scenario_id = str(materialization.get("scenario_id", ""))
        source_file = normalize_path(str(materialization.get("source_file", "")))
        if scenario_id:
            evidence["scenario_ids"].add(scenario_id)
        if source_file:
            evidence["source_files"].add(source_file)
        for patch in dict_items(materialization.get("patches")):
            add_state_patch_evidence(
                patch,
                scenario_id=scenario_id,
                source_file=source_file,
                out_state=out_state,
                materialization_status=str(materialization.get("status", "")),
                executed=executed,
                applied=False,
                source=source,
                evidence=evidence,
            )
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
    for patch in dict_items(execution.get("applied_patches")):
        add_state_patch_evidence(
            patch,
            scenario_id=str(patch.get("scenario_id", "")),
            source_file="",
            out_state=normalize_path(str(execution.get("out_state") or out_state)),
            materialization_status="applied",
            executed=bool(execution.get("executed", executed)),
            applied=True,
            source=source,
            evidence=evidence,
        )


def collect_generic_state_patch_evidence(data: dict[str, Any], *, source: str, evidence: dict[str, Any]) -> None:
    for patch in explicit_state_patch_records(data):
        add_state_patch_evidence(
            patch,
            scenario_id=str(patch.get("scenario_id", "")),
            source_file=normalize_path(str(patch.get("source_file", ""))),
            out_state=normalize_path(str(patch.get("out_state", ""))),
            materialization_status=str(patch.get("status") or patch.get("materialization_status") or "generic"),
            executed=bool(patch.get("executed", False)),
            applied=bool(patch.get("applied", False)),
            source=source,
            evidence=evidence,
        )


def explicit_state_patch_records(data: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    out.extend(dict_items(data.get("state_patches")))
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    out.extend(dict_items(state_space.get("patches")))
    out.extend(dict_items(state_space.get("state_patches")))
    return [patch for patch in out if patch.get("symbol")]


def add_state_patch_evidence(
    patch: dict[str, Any],
    *,
    scenario_id: str,
    source_file: str,
    out_state: str,
    materialization_status: str,
    executed: bool,
    applied: bool,
    source: str,
    evidence: dict[str, Any],
) -> None:
    symbol = str(patch.get("symbol", ""))
    if not symbol:
        return
    record = {
        "symbol": base_label(symbol),
        "scenario_id": scenario_id,
        "source_file": source_file,
        "value": int(patch.get("value", 0)),
        "value_hex": str(patch.get("value_hex", "")),
        "observed": patch.get("observed"),
        "observed_hex": str(patch.get("observed_hex", "")),
        "verified": bool(patch.get("verified", False)),
        "bank_address": str(patch.get("bank_address", "")),
        "out_state": out_state,
        "materialization_status": materialization_status,
        "executed": executed,
        "applied": applied,
        "source": source,
    }
    if record not in evidence["state_patches"]:
        evidence["state_patches"].append(record)
    evidence["symbols"].add(record["symbol"])
    if scenario_id:
        evidence["scenario_ids"].add(scenario_id)
    if source_file:
        evidence["source_files"].add(source_file)
    for address in address_variants(record["bank_address"]):
        evidence["addresses"].add(address)


def add_state_precondition_evidence(
    precondition: dict[str, Any],
    *,
    scenario: dict[str, Any],
    source: str,
    index: int,
    evidence: dict[str, Any],
) -> None:
    values = precondition.get("values") if isinstance(precondition.get("values"), dict) else {}
    scenario_id = str(precondition.get("scenario_id") or scenario.get("id") or scenario.get("scenario_id") or "")
    kind = str(precondition.get("kind", ""))
    source_file = normalize_path(
        str(
            precondition.get("source_file")
            or scenario.get("source_file")
            or values.get("source_file")
            or ""
        )
    )
    watch_symbols = unique_list(string_items(precondition.get("watch_symbols")))
    record = {
        "id": str(precondition.get("id") or f"{scenario_id}_precondition_{index}"),
        "scenario_id": scenario_id,
        "scenario_type": str(scenario.get("scenario_type", precondition.get("scenario_type", ""))),
        "kind": kind,
        "source_file": source_file,
        "values": dict(values),
        "watch_symbols": watch_symbols,
        "source": source,
    }
    if record not in evidence["state_preconditions"]:
        evidence["state_preconditions"].append(record)
    if scenario_id:
        evidence["scenario_ids"].add(scenario_id)
    if source_file:
        evidence["source_files"].add(source_file)
    for symbol in watch_symbols:
        evidence["symbols"].add(base_label(symbol))


def scenario_id_from_record(data: dict[str, Any]) -> str:
    for key in ("scenario_id", "id"):
        value = data.get(key)
        if not isinstance(value, str) or not value:
            continue
        kind = str(data.get("kind", "")).lower()
        if "scenario" in kind:
            return value
        if data.get("scenario_type") or value.startswith(("content_scenario_", "debugger_generated_", "scenario_")):
            return value
    return ""


def add_event_evidence(event: dict[str, Any], evidence: dict[str, Any]) -> None:
    for key in ("state_symbol", "source_symbol", "pc_symbol"):
        value = event.get(key)
        if value:
            evidence["symbols"].add(base_label(str(value)))
    if event.get("rule_id"):
        evidence["rules"].add(str(event["rule_id"]))
    if event.get("source_file"):
        evidence["source_files"].add(normalize_path(str(event["source_file"])))
    for key in ("address", "bank_address", "pc_bank_address"):
        for address in address_variants(str(event.get(key, ""))):
            evidence["addresses"].add(address)
    evidence["texts"].extend(string_items(event.get("evidence")))


def evaluate_expectation(expectation: dict[str, Any], *, evidence: dict[str, Any]) -> dict[str, Any]:
    expectation_type = str(expectation.get("type", "unknown"))
    if expectation_type == "no_errors":
        observed = len(evidence["errors"])
        passed = observed == 0
        result = result_for(expectation, passed=passed, observed_count=observed, evidence=evidence["errors"][:6])
    elif expectation_type == "report_valid":
        observed = len(evidence["invalid_reports"])
        passed = observed == 0
        result = result_for(expectation, passed=passed, observed_count=observed, evidence=evidence["invalid_reports"][:6])
    elif expectation_type == "symbol_observed":
        symbol = base_label(str(expectation.get("symbol", "")))
        observed = count_symbol(symbol, evidence=evidence)
        result = count_result(expectation, observed_count=observed, evidence=[symbol])
    elif expectation_type == "rule_observed":
        rule = str(expectation.get("rule_id", ""))
        observed = 1 if rule in evidence["rules"] else 0
        result = count_result(expectation, observed_count=observed, evidence=[rule])
    elif expectation_type == "source_observed":
        source_file = normalize_path(str(expectation.get("source_file", "")))
        observed = 1 if source_file in evidence["source_files"] else 0
        result = count_result(expectation, observed_count=observed, evidence=[source_file])
    elif expectation_type == "address_observed":
        variants = set(address_variants(str(expectation.get("address") or expectation.get("bank_address") or "")))
        observed = 1 if variants.intersection(evidence["addresses"]) else 0
        result = count_result(expectation, observed_count=observed, evidence=sorted(variants))
    elif expectation_type == "scenario_observed":
        scenario_id = str(expectation.get("scenario_id", ""))
        observed = 1 if scenario_id in evidence["scenario_ids"] else 0
        result = count_result(expectation, observed_count=observed, evidence=[scenario_id])
    elif expectation_type == "precondition_observed":
        matches = matching_preconditions(expectation, evidence=evidence)
        result = count_result(expectation, observed_count=len(matches), evidence=precondition_evidence(matches))
    elif expectation_type == "state_patch_observed":
        matches = matching_state_patches(expectation, evidence=evidence)
        result = count_result(expectation, observed_count=len(matches), evidence=state_patch_evidence(matches))
    elif expectation_type == "event_observed":
        matches = matching_events(expectation, evidence=evidence)
        result = count_result(expectation, observed_count=len(matches), evidence=event_evidence(matches))
    elif expectation_type == "event_absent":
        matches = matching_events(expectation, evidence=evidence)
        max_count = int(expectation.get("max_count", 0))
        result = result_for(
            expectation,
            passed=len(matches) <= max_count,
            observed_count=len(matches),
            evidence=event_evidence(matches),
        )
    elif expectation_type == "value_equals":
        matches = matching_events(expectation, evidence=evidence)
        expected = str(expectation.get("expected", expectation.get("after", expectation.get("value", ""))))
        passed_matches = [
            event
            for event in matches
            if expected in {str(event.get("after", "")), str(event.get("value", "")), str(event.get("before", ""))}
        ]
        result = count_result(expectation, observed_count=len(passed_matches), evidence=event_evidence(passed_matches or matches))
    elif expectation_type == "contains_text":
        needle = str(expectation.get("contains", ""))
        observed = sum(1 for text in evidence["texts"] if needle and needle in text)
        result = count_result(expectation, observed_count=observed, evidence=[needle])
    elif expectation_type == "text_absent":
        needle = str(expectation.get("contains", ""))
        observed = sum(1 for text in evidence["texts"] if needle and needle in text)
        result = result_for(
            expectation,
            passed=observed <= int(expectation.get("max_count", 0)),
            observed_count=observed,
            evidence=[needle],
        )
    else:
        result = {
            **base_result(expectation),
            "status": "skipped",
            "observed_count": 0,
            "evidence": [f"unsupported expectation type: {expectation_type}"],
        }
    result["commands"] = commands_for_expectation(expectation, result)
    return result


def matching_preconditions(expectation: dict[str, Any], *, evidence: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        precondition
        for precondition in evidence["state_preconditions"]
        if precondition_matches(precondition, expectation)
    ]


def precondition_matches(precondition: dict[str, Any], expectation: dict[str, Any]) -> bool:
    expected_kind = str(expectation.get("precondition_kind", expectation.get("kind", "")))
    if expected_kind and str(precondition.get("kind", "")) != expected_kind:
        return False
    expected_scenario = str(expectation.get("scenario_id", ""))
    if expected_scenario and str(precondition.get("scenario_id", "")) != expected_scenario:
        return False
    expected_source = str(expectation.get("source_file", ""))
    if expected_source and normalize_path(str(precondition.get("source_file", ""))) != normalize_path(expected_source):
        return False
    expected_symbol = str(expectation.get("symbol") or expectation.get("watch_symbol") or "")
    if expected_symbol and base_label(expected_symbol) not in {base_label(symbol) for symbol in precondition.get("watch_symbols", [])}:
        return False
    value_key = str(expectation.get("value_key", ""))
    expected_value = str(expectation.get("value", expectation.get("expected", "")))
    values = precondition.get("values") if isinstance(precondition.get("values"), dict) else {}
    if value_key:
        if value_key not in values:
            return False
        if expected_value and str(values.get(value_key, "")) != expected_value:
            return False
    contains = expectation.get("contains")
    if contains and str(contains) not in json.dumps(precondition, sort_keys=True):
        return False
    return True


def matching_state_patches(expectation: dict[str, Any], *, evidence: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        patch
        for patch in evidence["state_patches"]
        if state_patch_matches(patch, expectation)
    ]


def state_patch_matches(patch: dict[str, Any], expectation: dict[str, Any]) -> bool:
    expected_symbol = str(
        expectation.get("patch_symbol")
        or expectation.get("state_patch")
        or expectation.get("symbol")
        or ""
    )
    if expected_symbol and base_label(expected_symbol) != base_label(str(patch.get("symbol", ""))):
        return False
    expected_scenario = str(expectation.get("scenario_id", ""))
    if expected_scenario and expected_scenario != str(patch.get("scenario_id", "")):
        return False
    expected_source = str(expectation.get("source_file", ""))
    if expected_source and normalize_path(expected_source) != normalize_path(str(patch.get("source_file", ""))):
        return False
    expected_address = str(expectation.get("address") or expectation.get("bank_address") or "")
    if expected_address:
        expected_variants = set(address_variants(expected_address))
        patch_variants = set(address_variants(str(patch.get("bank_address", ""))))
        if not expected_variants.intersection(patch_variants):
            return False
    expected_value = expectation.get("value", expectation.get("expected"))
    if expected_value not in {None, ""} and not state_patch_value_matches(patch, str(expected_value)):
        return False
    expected_out_state = str(expectation.get("out_state", ""))
    if expected_out_state and normalize_path(expected_out_state) != normalize_path(str(patch.get("out_state", ""))):
        return False
    if truthy_expectation(expectation.get("verified")) and not patch.get("verified"):
        return False
    if truthy_expectation(expectation.get("applied")) and not patch.get("applied"):
        return False
    return True


def state_patch_value_matches(patch: dict[str, Any], expected_value: str) -> bool:
    expected = expected_value.strip()
    if not expected:
        return True
    observed_values = {
        str(patch.get("value", "")),
        str(patch.get("value_hex", "")).lower(),
        str(patch.get("observed", "")),
        str(patch.get("observed_hex", "")).lower(),
    }
    numeric = parse_int_text(expected)
    if numeric is not None:
        observed_values.add(str(numeric & 0xFF))
        observed_values.add(f"{numeric & 0xFF:02x}")
    return expected.lower().removeprefix("$").removeprefix("0x") in observed_values


def parse_int_text(value: str) -> int | None:
    text = value.strip()
    if not text:
        return None
    try:
        if text.startswith("$"):
            return int(text[1:], 16)
        return int(text, 0)
    except ValueError:
        return None


def truthy_expectation(value: Any) -> bool:
    if value is None or value is False:
        return False
    text = str(value).strip().lower()
    return bool(text) and text not in {"0", "false", "no", "off"}


def matching_events(expectation: dict[str, Any], *, evidence: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        event
        for event in evidence["events"]
        if event_matches(event, expectation)
    ]


def event_matches(event: dict[str, Any], expectation: dict[str, Any]) -> bool:
    for key in EVENT_MATCH_FIELDS:
        expected = expectation.get(key)
        if expected in {None, ""}:
            continue
        if key == "symbol":
            symbols = {
                base_label(str(event.get("state_symbol", ""))),
                base_label(str(event.get("source_symbol", ""))),
                base_label(str(event.get("pc_symbol", ""))),
            }
            if base_label(str(expected)) not in symbols:
                return False
        elif key == "rule":
            if str(event.get("rule_id", "")) != str(expected):
                return False
        elif key in {"address", "bank_address"}:
            expected_variants = set(address_variants(str(expected)))
            event_variants = set(
                address
                for item in (event.get("address", ""), event.get("bank_address", ""))
                for address in address_variants(str(item))
            )
            if not expected_variants.intersection(event_variants):
                return False
        elif key == "source_file":
            if normalize_path(str(event.get("source_file", ""))) != normalize_path(str(expected)):
                return False
        else:
            if str(event.get(key, "")) != str(expected):
                return False
    contains = expectation.get("contains")
    if contains:
        return str(contains) in json.dumps(event, sort_keys=True)
    return True


def count_result(expectation: dict[str, Any], *, observed_count: int, evidence: list[str]) -> dict[str, Any]:
    min_count = int(expectation.get("min_count", 1))
    max_count = expectation.get("max_count")
    passed = observed_count >= min_count and (max_count is None or observed_count <= int(max_count))
    return result_for(expectation, passed=passed, observed_count=observed_count, evidence=evidence)


def result_for(
    expectation: dict[str, Any],
    *,
    passed: bool,
    observed_count: int,
    evidence: list[str],
) -> dict[str, Any]:
    result = base_result(expectation)
    result.update(
        {
            "status": "passed" if passed else "failed",
            "observed_count": observed_count,
            "evidence": [item for item in evidence if item][:8],
        }
    )
    return result


def base_result(expectation: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(expectation.get("id", "")),
        "type": str(expectation.get("type", "")),
        "description": str(expectation.get("description", expectation.get("id", ""))),
        "source": str(expectation.get("source", "")),
        "severity": int(expectation.get("severity", 70)),
        "min_count": int(expectation.get("min_count", 1)),
        "max_count": expectation.get("max_count"),
        "expectation": {
            key: value
            for key, value in expectation.items()
            if key not in {"description", "source"}
        },
    }


def commands_for_expectation(expectation: dict[str, Any], result: dict[str, Any]) -> list[str]:
    commands = []
    scenario_id = str(expectation.get("scenario_id", ""))
    if scenario_id:
        commands.append(f"python -m tools.debugger setup --report <content_scenarios.json> --scenario-id {scenario_id}")
        commands.append(f"python -m tools.debugger replay --report <content_scenarios.json> --scenario-id {scenario_id}")
    if expectation.get("type") == "precondition_observed" or expectation.get("precondition_kind"):
        precondition_kind = str(expectation.get("precondition_kind", "<kind>"))
        scenario_arg = f",scenario={scenario_id}" if scenario_id else ""
        commands.append(
            f"python -m tools.debugger expect --report <content_scenarios.json> --expect precondition={precondition_kind}{scenario_arg}"
        )
    if expectation.get("type") == "state_patch_observed" or expectation.get("patch_symbol") or expectation.get("state_patch"):
        patch_symbol = str(
            expectation.get("patch_symbol")
            or expectation.get("state_patch")
            or expectation.get("symbol")
            or "<symbol>"
        )
        scenario_arg = f",scenario={scenario_id}" if scenario_id else ""
        value = expectation.get("value", expectation.get("expected", ""))
        value_arg = f",value={value}" if value is not None and str(value) else ""
        commands.append(
            f"python -m tools.debugger expect --report <content_state.json> --expect state-patch={patch_symbol}{scenario_arg}{value_arg}"
        )
        if patch_symbol != "<symbol>":
            commands.append(
                f"python -m tools.debugger watch --watch-symbol {patch_symbol} --save-state <patched-state> --execute"
            )
    symbol = expectation.get("symbol") or expectation.get("state_symbol")
    if symbol:
        commands.append(f"python -m tools.debugger trace-index --symbol {symbol}")
        commands.append(f"python -m tools.debugger explain --symbol {symbol}")
        commands.append(f"python -m tools.debugger replay --symbol {symbol}")
    if expectation.get("event_type"):
        commands.append(f"python -m tools.debugger expect --expect event={expectation.get('event_type')}")
    if expectation.get("rule_id") or expectation.get("rule"):
        rule = expectation.get("rule_id") or expectation.get("rule")
        commands.append(f"python -m tools.debugger coverage --rule {rule}")
    if expectation.get("source_file"):
        commands.append(f"python -m tools.debugger gate --changed-file {expectation.get('source_file')}")
        commands.append(
            f"python -m tools.debugger expect --source-file {expectation.get('source_file')} --expect report-valid"
        )
    if expectation.get("contains"):
        commands.append("python -m tools.debugger expect --source-file <source_file> --expect contains=<text>")
    if expectation.get("address") or expectation.get("bank_address"):
        address = expectation.get("address") or expectation.get("bank_address")
        commands.append(f"python -m tools.debugger trace-index --address {address}")
    if result["status"] == "failed":
        commands.append("python -m tools.debugger compare --symptom <expected_behavior>")
        commands.append("python -m tools.debugger generate --symptom <expected_behavior>")
    return unique_list(commands)


def event_evidence(events: list[dict[str, Any]]) -> list[str]:
    out = []
    for event in events[:8]:
        state = event.get("state_symbol") or event.get("bank_address") or event.get("address") or "state"
        source = event.get("source_symbol") or event.get("pc_symbol") or event.get("rule_id") or "trace"
        out.append(f"{event.get('event_type', 'event')} {state} from {source}")
    return out


def precondition_evidence(preconditions: list[dict[str, Any]]) -> list[str]:
    out = []
    for precondition in preconditions[:8]:
        scenario_id = precondition.get("scenario_id") or "scenario"
        kind = precondition.get("kind") or "precondition"
        source_file = precondition.get("source_file") or "source"
        watches = ", ".join(precondition.get("watch_symbols", [])[:4])
        suffix = f" watches {watches}" if watches else ""
        out.append(f"{scenario_id} {kind} in {source_file}{suffix}")
    return out


def state_patch_evidence(patches: list[dict[str, Any]]) -> list[str]:
    out = []
    for patch in patches[:8]:
        scenario_id = patch.get("scenario_id") or "scenario"
        symbol = patch.get("symbol") or "symbol"
        value = patch.get("value_hex") or patch.get("value") or "value"
        source_file = patch.get("source_file") or patch.get("source") or "source"
        out.append(f"{scenario_id} patches {symbol}={value} from {source_file}")
    return out


def count_symbol(symbol: str, *, evidence: dict[str, Any]) -> int:
    if symbol in evidence["symbols"]:
        return 1
    return sum(
        1
        for event in evidence["events"]
        if symbol
        in {
            base_label(str(event.get("state_symbol", ""))),
            base_label(str(event.get("source_symbol", ""))),
            base_label(str(event.get("pc_symbol", ""))),
        }
    )


def address_variants(value: str) -> list[str]:
    text = value.strip().upper().replace("$", "")
    if not text:
        return []
    if text.startswith("0X"):
        text = text[2:]
    if ":" in text:
        bank, address = text.split(":", 1)
        address = address[-4:].rjust(4, "0")
        return unique_list([address, f"{bank[-2:].rjust(2, '0')}:{address}"])
    if all(char in "0123456789ABCDEF" for char in text):
        return [text[-4:].rjust(4, "0")]
    return [text]


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


def dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, dict)]


def base_label(value: str) -> str:
    text = str(value).strip()
    if "+" in text:
        text = text.split("+", 1)[0]
    return text


def safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in str(value))[:80]
