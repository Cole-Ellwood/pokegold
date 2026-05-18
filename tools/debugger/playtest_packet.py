from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .evidence import evidence_atom
from .ingest import inspect_artifact
from .workflow import command_address_arg, command_is_runnable


def build_playtest_packet(
    *,
    rom_path: str = "",
    symbols_path: str = "pokegold.sym",
    save_state: str = "",
    input_log: str = "",
    screenshot: str = "",
    traces: tuple[str, ...] = (),
    reports: tuple[str, ...] = (),
    scenarios: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    watch_symbols: tuple[str, ...] = (),
    addresses: tuple[str, ...] = (),
    symptom: str = "",
    notes: tuple[str, ...] = (),
    packet_path: str = "",
    root: Path = ROOT,
) -> dict[str, Any]:
    artifacts = packet_artifacts(
        rom_path=rom_path,
        symbols_path=symbols_path,
        save_state=save_state,
        input_log=input_log,
        screenshot=screenshot,
        traces=traces,
        reports=reports,
        scenarios=scenarios,
        changed_files=changed_files,
        root=root,
    )
    errors = [
        f"{artifact['kind']} {artifact['input_path']}: {error}"
        for artifact in artifacts
        for error in artifact.get("errors", [])
    ]
    warnings = [
        f"{artifact['kind']} {artifact['input_path']}: {warning}"
        for artifact in artifacts
        for warning in artifact.get("warnings", [])
    ]
    if not save_state:
        warnings.append("no save state supplied; replay will need a state from another report or scenario")
    if not input_log:
        warnings.append("no input log supplied; exact black-box replay may require manual inputs")
    if not screenshot:
        warnings.append("no screenshot supplied; visual symptom comparison will be weaker")
    fingerprints = packet_fingerprints(artifacts)
    consistency_checks = packet_consistency_checks(artifacts, fingerprints=fingerprints)
    consistency_warnings = [
        check["message"]
        for check in consistency_checks
        if check.get("status") == "failed"
    ]
    warnings.extend(consistency_warnings)
    reproducibility = packet_reproducibility(
        artifacts=artifacts,
        consistency_checks=consistency_checks,
    )
    packet_id = packet_identity(
        symptom=symptom,
        artifacts=artifacts,
        symbols=symbols,
        watch_symbols=watch_symbols,
        addresses=addresses,
    )
    available_route_inputs = route_input_availability(
        artifacts=artifacts,
        packet_path=packet_path,
        symbols=symbols,
        watch_symbols=watch_symbols,
        addresses=addresses,
        root=root,
    )
    routes = packet_investigation_routes(
        packet_path=packet_path or "<packet.json>",
        packet_id=packet_id,
        rom_path=rom_path,
        symbols_path=symbols_path,
        save_state=save_state,
        input_log=input_log,
        symptom=symptom,
        symbols=symbols,
        watch_symbols=watch_symbols,
        addresses=addresses,
        reports=reports,
        traces=traces,
        changed_files=changed_files,
        scenarios=scenarios,
        available_inputs=available_route_inputs,
        root=root,
    )
    commands = unique_list([*packet_commands(
        packet_path=packet_path or "<packet.json>",
        rom_path=rom_path,
        symbols_path=symbols_path,
        save_state=save_state,
        input_log=input_log,
        symptom=symptom,
        symbols=symbols,
        watch_symbols=watch_symbols,
        addresses=addresses,
        reports=reports,
        traces=traces,
    ), *packet_commands_from_routes(routes)])
    route_commands = packet_commands_from_routes(routes)
    runnable_route_commands = [str(route.get("command", "")) for route in routes if route.get("runnable")]
    blocked_route_commands = [str(route.get("command", "")) for route in routes if not route.get("runnable")]
    non_route_commands = [command for command in commands if command not in route_commands]
    return {
        "schema_version": 1,
        "kind": "unified_debugger_playtest_packet",
        "root": str(root),
        "valid": not errors,
        "proof_status": "planned_only",
        "packet_id": packet_id,
        "symptom": symptom,
        "notes": list(notes),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "artifact_fingerprints": fingerprints,
        "rom_sha256": str(fingerprints.get("rom", {}).get("sha256", "")),
        "symbols_sha256": str(fingerprints.get("symbols", {}).get("sha256", "")),
        "save_state_sha256": str(fingerprints.get("save_state", {}).get("sha256", "")),
        "input_log_sha256": str(fingerprints.get("input_log", {}).get("sha256", "")),
        "screenshot_sha256": str(fingerprints.get("screenshot", {}).get("sha256", "")),
        "reproducibility": reproducibility,
        "consistency_check_count": len(consistency_checks),
        "consistency_status_counts": consistency_status_counts(consistency_checks),
        "consistency_checks": consistency_checks,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "rom": rom_path,
        "symbols": symbols_path,
        "save_state": save_state,
        "input_log": input_log,
        "screenshot": screenshot,
        "traces": list(traces),
        "reports": list(reports),
        "scenarios": list(scenarios),
        "changed_files": list(changed_files),
        "symbols_to_investigate": list(symbols),
        "watch_symbols": list(watch_symbols),
        "addresses": list(addresses),
        "evidence_route_count": len(routes),
        "evidence_routes": routes,
        "route_input_availability": available_route_inputs,
        "route_status_counts": route_status_counts(routes),
        "route_execution_status_counts": route_execution_status_counts(routes),
        "route_proof_status_counts": route_proof_status_counts(routes),
        "expected_route_proof_status_counts": expected_route_proof_status_counts(routes),
        "runnable_evidence_routes": [
            route for route in routes if route.get("runnable")
        ],
        "blocked_evidence_routes": [
            route for route in routes if not route.get("runnable")
        ],
        "executed_evidence_routes": [
            route for route in routes if route.get("execution_status") in {"executed", "observed"}
        ],
        "observed_evidence_routes": [
            route for route in routes if route.get("execution_status") == "observed"
        ],
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": unique_list([
            *runnable_route_commands,
            *[command for command in non_route_commands if command_is_runnable(command)],
        ]),
        "blocked_commands": unique_list([
            *blocked_route_commands,
            *[command for command in non_route_commands if not command_is_runnable(command)],
        ]),
        "known_limits": [
            "This packet packages playtest evidence and follow-up commands; it does not by itself prove the symptom.",
            "Exact replay still requires a compatible save state and input log or a runtime report that already contains enough state.",
            "Evidence routes are a reproducible investigation plan until the route command writes a runtime report.",
            "Screenshots are stored as artifacts for handoff; pixel/tilemap comparison still needs dedicated visual mirror execution.",
        ],
    }


def packet_fingerprints(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    grouped = artifacts_by_kind(artifacts)
    return {
        "rom": first_artifact_fingerprint(grouped.get("rom", [])),
        "symbols": first_artifact_fingerprint(grouped.get("symbols", [])),
        "save_state": first_artifact_fingerprint(grouped.get("save_state", [])),
        "input_log": first_artifact_fingerprint(grouped.get("input_log", [])),
        "screenshot": first_artifact_fingerprint(grouped.get("screenshot", [])),
        "traces": [artifact_fingerprint(artifact) for artifact in grouped.get("trace", [])],
        "reports": [artifact_fingerprint(artifact) for artifact in grouped.get("report", [])],
        "scenarios": [artifact_fingerprint(artifact) for artifact in grouped.get("scenario", [])],
        "source_changes": [artifact_fingerprint(artifact) for artifact in grouped.get("source_change", [])],
    }


def artifacts_by_kind(artifacts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for artifact in artifacts:
        grouped.setdefault(str(artifact.get("kind", "")), []).append(artifact)
    return grouped


def first_artifact_fingerprint(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    return artifact_fingerprint(artifacts[0]) if artifacts else {}


def artifact_fingerprint(artifact: dict[str, Any]) -> dict[str, Any]:
    metadata = artifact.get("metadata") if isinstance(artifact.get("metadata"), dict) else {}
    return {
        "kind": str(artifact.get("kind", "")),
        "path": str(artifact.get("path", "")),
        "input_path": str(artifact.get("input_path", "")),
        "exists": bool(artifact.get("exists")),
        "size_bytes": int(artifact.get("size_bytes", 0) or 0),
        "sha256": str(artifact.get("sha256", "")),
        "metadata": fingerprint_metadata(metadata),
    }


def fingerprint_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "title",
        "cgb_flag",
        "cartridge_type",
        "rom_size_code",
        "ram_size_code",
        "header_checksum",
        "global_checksum",
        "label_count",
        "bank_count",
        "format",
        "record_count",
        "line_count",
        "input_count",
        "button_sample",
        "trace_rom_sha256",
        "trace_symbols_sha256",
        "rom_sha256_sample",
        "symbols_sha256_sample",
        "report_kind",
        "proof_status",
        "families",
        "ids_sample",
    )
    return {key: metadata[key] for key in keys if key in metadata}


def packet_reproducibility(
    *,
    artifacts: list[dict[str, Any]],
    consistency_checks: list[dict[str, Any]],
) -> dict[str, Any]:
    grouped = artifacts_by_kind(artifacts)
    has_rom = bool(first_existing(grouped.get("rom", [])))
    has_symbols = bool(first_existing(grouped.get("symbols", [])))
    has_save_state = bool(first_existing(grouped.get("save_state", [])))
    has_input_log = bool(first_existing(grouped.get("input_log", [])))
    has_screenshot = bool(first_existing(grouped.get("screenshot", [])))
    failed_checks = [check for check in consistency_checks if check.get("status") == "failed"]
    ready_for_runtime = has_rom and has_symbols and has_save_state and not failed_checks
    return {
        "has_rom": has_rom,
        "has_symbols": has_symbols,
        "has_save_state": has_save_state,
        "has_input_log": has_input_log,
        "has_screenshot": has_screenshot,
        "trace_count": len(grouped.get("trace", [])),
        "report_count": len(grouped.get("report", [])),
        "scenario_count": len(grouped.get("scenario", [])),
        "source_change_count": len(grouped.get("source_change", [])),
        "runtime_replay_ready": ready_for_runtime,
        "black_box_replay_ready": ready_for_runtime and has_input_log,
        "visual_handoff_ready": has_screenshot,
        "consistency_failed": bool(failed_checks),
        "consistency_failed_count": len(failed_checks),
    }


def first_existing(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    for artifact in artifacts:
        if artifact.get("exists"):
            return artifact
    return {}


def packet_consistency_checks(
    artifacts: list[dict[str, Any]],
    *,
    fingerprints: dict[str, Any],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    rom_sha = str(fingerprints.get("rom", {}).get("sha256", ""))
    symbols_sha = str(fingerprints.get("symbols", {}).get("sha256", ""))
    for trace in artifacts_by_kind(artifacts).get("trace", []):
        trace_path = str(trace.get("path") or trace.get("input_path") or "")
        for observed in artifact_hash_metadata(trace, "rom"):
            checks.append(hash_consistency_check(
                artifact=trace_path,
                field="trace_rom_sha256",
                observed=observed,
                expected=rom_sha,
            ))
        for observed in artifact_hash_metadata(trace, "symbols"):
            checks.append(hash_consistency_check(
                artifact=trace_path,
                field="trace_symbols_sha256",
                observed=observed,
                expected=symbols_sha,
            ))
    return checks


def artifact_hash_metadata(artifact: dict[str, Any], kind: str) -> list[str]:
    metadata = artifact.get("metadata") if isinstance(artifact.get("metadata"), dict) else {}
    if kind == "rom":
        keys = ("trace_rom_sha256", "rom_sha256_sample")
    elif kind == "symbols":
        keys = ("trace_symbols_sha256", "symbols_sha256_sample")
    else:
        keys = ()
    out: list[str] = []
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, str):
            out.append(value)
        elif isinstance(value, list | tuple):
            out.extend(str(item) for item in value if item)
    return unique_list(out)


def hash_consistency_check(
    *,
    artifact: str,
    field: str,
    observed: str,
    expected: str,
) -> dict[str, Any]:
    if not observed:
        status = "missing"
    elif not expected:
        status = "unchecked"
    elif observed.lower() == expected.lower():
        status = "passed"
    else:
        status = "failed"
    message = (
        f"{artifact} {field} matches packet artifact"
        if status == "passed"
        else f"{artifact} {field}={observed or '<missing>'} expected={expected or '<unavailable>'}"
    )
    return {
        "artifact": artifact,
        "field": field,
        "observed": observed,
        "expected": expected,
        "status": status,
        "message": message,
    }


def consistency_status_counts(checks: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for check in checks:
        status = str(check.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def packet_artifacts(
    *,
    rom_path: str,
    symbols_path: str,
    save_state: str,
    input_log: str,
    screenshot: str,
    traces: tuple[str, ...],
    reports: tuple[str, ...],
    scenarios: tuple[str, ...],
    changed_files: tuple[str, ...],
    root: Path,
) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    if rom_path:
        artifacts.append(inspect_artifact("rom", rom_path, root=root))
    if symbols_path:
        artifacts.append(inspect_artifact("symbols", symbols_path, root=root))
    if save_state:
        artifacts.append(inspect_artifact("save_state", save_state, root=root))
    if input_log:
        artifacts.append(inspect_artifact("input_log", input_log, root=root))
    if screenshot:
        artifacts.append(inspect_artifact("screenshot", screenshot, root=root))
    for trace in traces:
        artifacts.append(inspect_artifact("trace", trace, root=root))
    for report in reports:
        artifact = inspect_artifact("report", report, root=root)
        add_json_report_metadata(artifact, root=root)
        artifacts.append(artifact)
    for scenario in scenarios:
        artifacts.append(inspect_artifact("scenario", scenario, root=root))
    for changed_file in changed_files:
        artifacts.append(inspect_artifact("source_change", changed_file, require_exists=False, root=root))
    return artifacts


def add_json_report_metadata(artifact: dict[str, Any], *, root: Path) -> None:
    if not artifact.get("exists"):
        return
    path = Path(artifact["input_path"])
    if not path.is_absolute():
        path = root / path
    if path.suffix.lower() != ".json":
        return
    try:
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if isinstance(data, dict):
        artifact["metadata"]["report_kind"] = str(data.get("kind", ""))
        artifact["metadata"]["valid"] = data.get("valid")
        artifact["metadata"]["proof_status"] = data.get("proof_status", "")


def packet_investigation_routes(
    *,
    packet_path: str,
    packet_id: str,
    rom_path: str,
    symbols_path: str,
    save_state: str,
    input_log: str,
    symptom: str,
    symbols: tuple[str, ...],
    watch_symbols: tuple[str, ...],
    addresses: tuple[str, ...],
    reports: tuple[str, ...],
    traces: tuple[str, ...],
    changed_files: tuple[str, ...],
    scenarios: tuple[str, ...],
    available_inputs: dict[str, bool],
    root: Path,
) -> list[dict[str, Any]]:
    base = f".local\\tmp\\playtest_{packet_id}"
    routes: list[dict[str, Any]] = []
    add_route(
        routes,
        route_id="ingest_packet_artifacts",
        phase="ingest",
        title="Fingerprint packet artifacts",
        command=ingest_command(
            rom_path=rom_path,
            symbols_path=symbols_path,
            save_state=save_state,
            input_log=input_log,
            traces=traces,
            scenarios=scenarios,
            changed_files=changed_files,
            out_json=f"{base}_ingest.json",
        ),
        produces=f"{base}_ingest.json",
        proof_status="planned_only",
        required_inputs=ingest_required_inputs(
            rom_path=rom_path,
            symbols_path=symbols_path,
            save_state=save_state,
            input_log=input_log,
            traces=traces,
            scenarios=scenarios,
            changed_files=changed_files,
        ),
        available_inputs=available_inputs,
    )
    add_route(
        routes,
        route_id="investigate_packet",
        phase="orchestrate",
        title="Run full debugger investigation workflow",
        command=investigate_command(
            packet_path=packet_path,
            rom_path=rom_path,
            symbols_path=symbols_path,
            save_state=save_state,
            input_log=input_log,
            symptom=symptom,
            symbols=symbols,
            watch_symbols=watch_symbols,
            addresses=addresses,
            out_dir=f"{base}_investigation",
            out_json=f"{base}_investigation.json",
        ),
        produces=f"{base}_investigation.json",
        proof_status="planned_only",
        required_inputs=["packet"],
        available_inputs=available_inputs,
    )
    add_route(
        routes,
        route_id="investigate_runtime_evidence",
        phase="orchestrate",
        title="Run debugger investigation with runtime watch, visual, and audio evidence",
        command=investigate_command(
            packet_path=packet_path,
            rom_path=rom_path,
            symbols_path=symbols_path,
            save_state=save_state,
            input_log=input_log,
            symptom=symptom,
            symbols=symbols,
            watch_symbols=watch_symbols,
            addresses=addresses,
            out_dir=f"{base}_runtime_evidence",
            out_json=f"{base}_runtime_evidence.json",
            execute_runtime_evidence=True,
        ),
        produces=f"{base}_runtime_evidence.json",
        proof_status="runtime_observed",
        required_inputs=["packet", "save_state"],
        available_inputs=available_inputs,
    )
    add_route(
        routes,
        route_id="replay_plan",
        phase="reproduce",
        title="Build replay and runtime-capture plan",
        command=replay_command(
            packet_path=packet_path,
            rom_path=rom_path,
            symbols_path=symbols_path,
            save_state=save_state,
            input_log=input_log,
            symptom=symptom,
            watch_symbols=watch_symbols,
            addresses=addresses,
            execute_trace=False,
            out_json=f"{base}_replay.json",
        ),
        produces=f"{base}_replay.json",
        proof_status="planned_only",
        required_inputs=["packet"],
        available_inputs=available_inputs,
    )
    add_route(
        routes,
        route_id="runtime_watch",
        phase="observe",
        title="Observe watched state from the playtest save state",
        command=watch_command(
            rom_path=rom_path,
            symbols_path=symbols_path,
            save_state=save_state,
            watch_symbols=watch_symbols,
            addresses=addresses,
            out_json=f"{base}_watch.json",
        ),
        produces=f"{base}_watch.json",
        proof_status="runtime_observed",
        required_inputs=["save_state", "watch_target"],
        available_inputs=available_inputs,
    )
    add_route(
        routes,
        route_id="visual_snapshot",
        phase="observe",
        title="Capture visual/UI surfaces from the playtest save state",
        command=visual_snapshot_command(
            rom_path=rom_path,
            symbols_path=symbols_path,
            save_state=save_state,
            out_json=f"{base}_visual_snapshot.json",
        ),
        produces=f"{base}_visual_snapshot.json",
        proof_status="runtime_observed",
        required_inputs=["save_state"],
        available_inputs=available_inputs,
    )
    add_route(
        routes,
        route_id="audio_snapshot",
        phase="observe",
        title="Capture audio registers and music-engine state from the playtest save state",
        command=audio_snapshot_command(
            rom_path=rom_path,
            symbols_path=symbols_path,
            save_state=save_state,
            out_json=f"{base}_audio_snapshot.json",
        ),
        produces=f"{base}_audio_snapshot.json",
        proof_status="runtime_observed",
        required_inputs=["save_state"],
        available_inputs=available_inputs,
    )
    trace_output = f"{base}_instruction_trace.jsonl"
    add_route(
        routes,
        route_id="instruction_trace",
        phase="observe",
        title="Capture dense instruction trace around packet targets",
        command=trace_instruction_command(
            packet_path=packet_path,
            rom_path=rom_path,
            symbols_path=symbols_path,
            save_state=save_state,
            symptom=symptom,
            symbols=symbols,
            watch_symbols=watch_symbols,
            addresses=addresses,
            changed_files=changed_files,
            out_trace=trace_output,
            out_json=f"{base}_instruction_trace.json",
        ),
        produces=trace_output,
        proof_status="instruction_observed",
        required_inputs=["save_state", "target"],
        available_inputs=available_inputs,
    )
    effect_trace_input = traces[0] if traces else trace_output_placeholder(trace_output, save_state=save_state)
    add_route(
        routes,
        route_id="effect_trace",
        phase="attribute",
        title="Convert instruction trace into read/write effects",
        command=effect_trace_command(
            trace=effect_trace_input,
            symbols_path=symbols_path,
            watch_symbols=watch_symbols,
            addresses=addresses,
            out_json=f"{base}_effect_trace.json",
        ),
        produces=f"{base}_effect_trace.json",
        proof_status="instruction_observed",
        required_inputs=["instruction_trace", "target"],
        available_inputs=available_inputs,
    )
    effect_report = f"{base}_effect_trace.json" if (traces or save_state) else "<effect-trace.json>"
    for index, address in enumerate(addresses[:4], start=1):
        add_route(
            routes,
            route_id=f"reverse_address_{index}",
            phase="attribute",
            title=f"Find last writer for {address}",
            command=reverse_query_command(
                effect_report=effect_report,
                symbols_path=symbols_path,
                address=address,
                symbol="",
                out_json=f"{base}_reverse_address_{index}.json",
            ),
            produces=f"{base}_reverse_address_{index}.json",
            proof_status="instruction_observed",
            required_inputs=["effect_trace"],
            available_inputs=available_inputs,
        )
    for index, symbol in enumerate(unique_list([*watch_symbols, *symbols])[:4], start=1):
        add_route(
            routes,
            route_id=f"reverse_symbol_{index}",
            phase="attribute",
            title=f"Find last writer for {symbol}",
            command=reverse_query_command(
                effect_report=effect_report,
                symbols_path=symbols_path,
                address="",
                symbol=symbol,
                out_json=f"{base}_reverse_symbol_{index}.json",
            ),
            produces=f"{base}_reverse_symbol_{index}.json",
            proof_status="instruction_observed",
            required_inputs=["effect_trace"],
            available_inputs=available_inputs,
        )
    if watch_symbols or addresses:
        add_route(
            routes,
            route_id="dynamic_taint",
            phase="attribute",
            title="Propagate source hints into observed writes",
            command=dynamic_taint_command(
                effect_report=effect_report,
                symbols_path=symbols_path,
                watch_symbols=watch_symbols,
                addresses=addresses,
                out_json=f"{base}_dynamic_taint.json",
            ),
            produces=f"{base}_dynamic_taint.json",
            proof_status="taint_proven",
            required_inputs=["effect_trace", "target"],
            available_inputs=available_inputs,
        )
    add_route(
        routes,
        route_id="causal_graph",
        phase="explain",
        title="Join packet, runtime, reverse, and taint evidence",
        command=causal_graph_command(
            reports=(packet_path, effect_report, f"{base}_dynamic_taint.json"),
            symbols=symbols,
            addresses=addresses,
            out_json=f"{base}_causal_graph.json",
        ),
        produces=f"{base}_causal_graph.json",
        proof_status="planned_only",
        required_inputs=["packet", "evidence_reports"],
        available_inputs=available_inputs,
    )
    add_route(
        routes,
        route_id="visualize",
        phase="report",
        title="Render investigation visualization",
        command=visualize_command(
            reports=(packet_path, f"{base}_causal_graph.json"),
            out_path=f"{base}_visualization.md",
        ),
        produces=f"{base}_visualization.md",
        proof_status="planned_only",
        required_inputs=["packet", "causal_graph"],
        available_inputs=available_inputs,
    )
    add_route(
        routes,
        route_id="rank_impact",
        phase="rank",
        title="Rank playtest findings by likely impact",
        command=rank_command(packet_path=packet_path, out_json=f"{base}_rank.json"),
        produces=f"{base}_rank.json",
        proof_status="planned_only",
        required_inputs=["packet"],
        available_inputs=available_inputs,
    )
    attach_route_output_evidence(routes, root=root)
    return routes


def add_route(
    routes: list[dict[str, Any]],
    *,
    route_id: str,
    phase: str,
    title: str,
    command: str,
    produces: str,
    proof_status: str,
    required_inputs: list[str],
    available_inputs: dict[str, bool],
) -> None:
    command_runnable = command_is_runnable(command)
    input_status = route_input_status(required_inputs, available_inputs=available_inputs)
    runnable = command_runnable and not input_status["missing_required_inputs"]
    routes.append(
        {
            "id": route_id,
            "phase": phase,
            "title": title,
            "command": command,
            "produces": produces,
            "command_runnable": command_runnable,
            "runnable": runnable,
            "status": route_status(command_runnable=command_runnable, input_status=input_status),
            "proof_status": "planned_only",
            "expected_proof_status": proof_status,
            "evidence_atoms": [
                evidence_atom(
                    claim_type="playtest_packet.evidence_route",
                    origin="playtest_packet",
                    observation_type="planned_route",
                    proof_status="planned_only",
                    source_kind=phase,
                    scope={"route_id": route_id, "phase": phase},
                    subjects={"files": [produces]},
                    precision={
                        "expected_proof_status": proof_status,
                        "command_runnable": command_runnable,
                        "input_status": input_status["status"],
                    },
                    validation={
                        "runnable": runnable,
                        "missing_required_inputs": input_status["missing_required_inputs"],
                    },
                    detail={"title": title},
                )
            ],
            "required_inputs": required_inputs,
            "satisfied_inputs": input_status["satisfied_inputs"],
            "missing_required_inputs": input_status["missing_required_inputs"],
            "input_status": input_status["status"],
        }
    )


def ingest_required_inputs(
    *,
    rom_path: str,
    symbols_path: str,
    save_state: str,
    input_log: str,
    traces: tuple[str, ...],
    scenarios: tuple[str, ...],
    changed_files: tuple[str, ...],
) -> list[str]:
    out = []
    if rom_path:
        out.append("rom")
    if symbols_path:
        out.append("symbols")
    if save_state:
        out.append("save_state")
    if input_log:
        out.append("input_log")
    if traces:
        out.append("trace")
    if scenarios:
        out.append("scenario")
    if changed_files:
        out.append("changed_file")
    return out


def packet_commands_from_routes(routes: list[dict[str, Any]]) -> list[str]:
    return [str(route.get("command", "")) for route in routes]


def route_input_availability(
    *,
    artifacts: list[dict[str, Any]],
    packet_path: str,
    symbols: tuple[str, ...],
    watch_symbols: tuple[str, ...],
    addresses: tuple[str, ...],
    root: Path,
) -> dict[str, bool]:
    grouped = artifacts_by_kind(artifacts)
    existing_reports = [artifact for artifact in grouped.get("report", []) if artifact.get("exists")]
    report_kinds = {
        str(artifact.get("metadata", {}).get("report_kind", ""))
        for artifact in existing_reports
        if isinstance(artifact.get("metadata"), dict)
    }
    has_trace = bool(first_existing(grouped.get("trace", [])))
    has_target = bool(symbols or watch_symbols or addresses)
    has_watch_target = bool(watch_symbols or addresses)
    return {
        "packet": packet_exists(packet_path, root=root),
        "rom": bool(first_existing(grouped.get("rom", []))),
        "symbols": bool(first_existing(grouped.get("symbols", []))),
        "save_state": bool(first_existing(grouped.get("save_state", []))),
        "input_log": bool(first_existing(grouped.get("input_log", []))),
        "trace": has_trace,
        "instruction_trace": has_trace,
        "scenario": bool(first_existing(grouped.get("scenario", []))),
        "changed_file": bool(first_existing(grouped.get("source_change", []))),
        "report": bool(existing_reports),
        "evidence_reports": bool(existing_reports),
        "effect_trace": "unified_debugger_effect_trace" in report_kinds,
        "causal_graph": "unified_debugger_causal_graph" in report_kinds,
        "target": has_target,
        "watch_target": has_watch_target,
    }


def packet_exists(packet_path: str, *, root: Path) -> bool:
    if not packet_path or "<" in packet_path or ">" in packet_path:
        return False
    path = Path(packet_path)
    if not path.is_absolute():
        path = root / path
    return path.exists() and path.is_file()


def route_input_status(required_inputs: list[str], *, available_inputs: dict[str, bool]) -> dict[str, Any]:
    satisfied = [value for value in required_inputs if available_inputs.get(value, False)]
    missing = [value for value in required_inputs if not available_inputs.get(value, False)]
    return {
        "status": "ready" if not missing else "missing_required_input",
        "satisfied_inputs": satisfied,
        "missing_required_inputs": missing,
    }


def route_status(*, command_runnable: bool, input_status: dict[str, Any]) -> str:
    if not command_runnable:
        return "planned"
    if input_status["missing_required_inputs"]:
        return "blocked"
    return "ready"


def attach_route_output_evidence(routes: list[dict[str, Any]], *, root: Path) -> None:
    for route in routes:
        output = route_output_evidence(str(route.get("produces") or ""), root=root)
        route.update(output)
        execution_status = route_execution_status(route)
        route["execution_status"] = execution_status
        route["proof_status"] = route_proof_status(route, execution_status=execution_status)


def route_output_evidence(produces: str, *, root: Path) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "produced_output_path": produces,
        "produced_output_exists": False,
        "produced_output_size_bytes": 0,
        "produced_output_kind": "",
        "produced_output_valid": False,
        "produced_output_executed": False,
        "produced_output_proof_status": "",
        "produced_output_error_count": 0,
        "produced_output_errors": [],
    }
    if not produces or "<" in produces or ">" in produces:
        return evidence
    path = Path(produces)
    if not path.is_absolute():
        path = root / path
    if not path.exists() or not path.is_file():
        return evidence

    evidence["produced_output_exists"] = True
    evidence["produced_output_size_bytes"] = path.stat().st_size
    suffix = path.suffix.lower()
    if suffix == ".json":
        evidence.update(json_route_output_evidence(path))
    elif suffix == ".jsonl":
        evidence.update(jsonl_route_output_evidence(path))
    else:
        evidence["produced_output_valid"] = True
        evidence["produced_output_kind"] = suffix.removeprefix(".")
    return evidence


def json_route_output_evidence(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {
            "produced_output_kind": "json",
            "produced_output_valid": False,
            "produced_output_errors": [str(exc)],
            "produced_output_error_count": 1,
        }
    if not isinstance(data, dict):
        return {
            "produced_output_kind": "json",
            "produced_output_valid": False,
            "produced_output_errors": ["route output JSON root is not an object"],
            "produced_output_error_count": 1,
        }
    errors = data.get("errors") if isinstance(data.get("errors"), list) else []
    valid = bool(data.get("valid", not errors))
    return {
        "produced_output_kind": str(data.get("kind") or "json"),
        "produced_output_valid": valid,
        "produced_output_executed": bool(data.get("executed")),
        "produced_output_proof_status": str(data.get("proof_status") or ""),
        "produced_output_error_count": len(errors),
        "produced_output_errors": [str(error) for error in errors[:8]],
    }


def jsonl_route_output_evidence(path: Path) -> dict[str, Any]:
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError as exc:
        return {
            "produced_output_kind": "jsonl",
            "produced_output_valid": False,
            "produced_output_errors": [str(exc)],
            "produced_output_error_count": 1,
        }
    return {
        "produced_output_kind": "jsonl",
        "produced_output_valid": bool(lines),
        "produced_output_executed": bool(lines),
        "produced_output_proof_status": "instruction_observed" if lines else "",
        "produced_output_line_count": len(lines),
    }


def route_execution_status(route: dict[str, Any]) -> str:
    if not route.get("produced_output_exists"):
        return "ready_to_run" if route.get("status") == "ready" else "planned_only"
    if not route.get("produced_output_valid"):
        return "executed"
    expected = str(route.get("expected_proof_status") or "planned_only")
    observed = str(route.get("produced_output_proof_status") or "")
    if expected != "planned_only" and observed == expected:
        return "observed"
    return "executed"


def route_proof_status(route: dict[str, Any], *, execution_status: str) -> str:
    if execution_status != "observed":
        return "planned_only"
    return str(route.get("produced_output_proof_status") or "planned_only")


def route_status_counts(routes: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for route in routes:
        status = str(route.get("status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def route_execution_status_counts(routes: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for route in routes:
        status = str(route.get("execution_status") or "planned_only")
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def route_proof_status_counts(routes: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for route in routes:
        status = str(route.get("proof_status") or "planned_only")
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def expected_route_proof_status_counts(routes: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for route in routes:
        status = str(route.get("expected_proof_status") or "planned_only")
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def packet_commands(
    *,
    packet_path: str,
    rom_path: str,
    symbols_path: str,
    save_state: str,
    input_log: str,
    symptom: str,
    symbols: tuple[str, ...],
    watch_symbols: tuple[str, ...],
    addresses: tuple[str, ...],
    reports: tuple[str, ...],
    traces: tuple[str, ...],
) -> list[str]:
    commands: list[str] = []
    investigate = ["python -m tools.debugger investigate", "--playtest-packet", quote_arg(packet_path)]
    if rom_path:
        investigate.extend(["--rom", quote_arg(rom_path)])
    if symbols_path:
        investigate.extend(["--symbols", quote_arg(symbols_path)])
    if save_state:
        investigate.extend(["--save-state", quote_arg(save_state)])
    if input_log:
        investigate.extend(["--input-log", quote_arg(input_log)])
    if symptom:
        investigate.extend(["--symptom", quote_arg(symptom)])
    for symbol in symbols:
        investigate.extend(["--symbol", quote_arg(symbol)])
    for symbol in watch_symbols:
        investigate.extend(["--watch-symbol", quote_arg(symbol)])
    for address in addresses:
        investigate.extend(["--address", command_address_arg(address)])
    commands.append(" ".join(investigate))

    commands.append(f"python -m tools.debugger rank --report {quote_arg(packet_path)}")
    commands.append(f"python -m tools.debugger impact --report {quote_arg(packet_path)}")
    commands.append(f"python -m tools.debugger report --report {quote_arg(packet_path)} --out .local\\tmp\\playtest_packet_report.md")
    for report in reports[:4]:
        commands.append(f"python -m tools.debugger rank --report {quote_arg(report)}")
    for trace in traces[:2]:
        effect = ["python -m tools.debugger effect-trace", "--trace", quote_arg(trace)]
        if symbols_path:
            effect.extend(["--symbols", quote_arg(symbols_path)])
        for symbol in watch_symbols[:4]:
            effect.extend(["--watch-symbol", quote_arg(symbol)])
        for address in addresses[:4]:
            effect.extend(["--watch-address", command_address_arg(address)])
        commands.append(" ".join(effect))
    for address in addresses[:4]:
        commands.append(f"python -m tools.debugger reverse-query --report <effect-trace.json> --address {command_address_arg(address)}")
    for symbol in [*watch_symbols, *symbols][:4]:
        commands.append(f"python -m tools.debugger reverse-query --report <effect-trace.json> --symbol {quote_arg(symbol)}")
    return unique_list(commands)


def ingest_command(
    *,
    rom_path: str,
    symbols_path: str,
    save_state: str,
    input_log: str,
    traces: tuple[str, ...],
    scenarios: tuple[str, ...],
    changed_files: tuple[str, ...],
    out_json: str,
) -> str:
    args = ["python -m tools.debugger ingest", "--json-out", quote_arg(out_json)]
    if rom_path:
        args.extend(["--rom", quote_arg(rom_path)])
    if symbols_path:
        args.extend(["--symbols", quote_arg(symbols_path)])
    if save_state:
        args.extend(["--save-state", quote_arg(save_state)])
    if input_log:
        args.extend(["--input-log", quote_arg(input_log)])
    for trace in traces[:4]:
        args.extend(["--trace", quote_arg(trace)])
    for scenario in scenarios[:4]:
        args.extend(["--scenario", quote_arg(scenario)])
    for changed_file in changed_files[:8]:
        args.extend(["--changed-file", quote_arg(changed_file)])
    return " ".join(args)


def investigate_command(
    *,
    packet_path: str,
    rom_path: str,
    symbols_path: str,
    save_state: str,
    input_log: str,
    symptom: str,
    symbols: tuple[str, ...],
    watch_symbols: tuple[str, ...],
    addresses: tuple[str, ...],
    out_dir: str,
    out_json: str,
    execute_runtime_evidence: bool = False,
) -> str:
    args = [
        "python -m tools.debugger investigate",
        "--playtest-packet",
        quote_arg(packet_path),
        "--out-dir",
        quote_arg(out_dir),
        "--json-out",
        quote_arg(out_json),
    ]
    if execute_runtime_evidence:
        args.append("--execute-runtime-evidence")
        if not save_state:
            args.extend(["--save-state", "<runtime-state>"])
    if input_log:
        args.extend(["--input-log", quote_arg(input_log)])
    add_common_runtime_args(
        args,
        rom_path=rom_path,
        symbols_path=symbols_path,
        save_state=save_state,
        symptom=symptom,
        symbols=symbols,
        watch_symbols=watch_symbols,
        addresses=addresses,
    )
    return " ".join(args)


def replay_command(
    *,
    packet_path: str,
    rom_path: str,
    symbols_path: str,
    save_state: str,
    input_log: str,
    symptom: str,
    watch_symbols: tuple[str, ...],
    addresses: tuple[str, ...],
    execute_trace: bool,
    out_json: str,
) -> str:
    args = ["python -m tools.debugger replay", "--report", quote_arg(packet_path), "--json-out", quote_arg(out_json)]
    add_runtime_artifact_args(args, rom_path=rom_path, symbols_path=symbols_path, save_state=save_state)
    if input_log:
        args.extend(["--input-log", quote_arg(input_log)])
    add_symptom_arg(args, symptom=symptom)
    add_watch_args(args, watch_symbols=watch_symbols, addresses=addresses)
    if execute_trace:
        args.append("--execute-trace")
    return " ".join(args)


def watch_command(
    *,
    rom_path: str,
    symbols_path: str,
    save_state: str,
    watch_symbols: tuple[str, ...],
    addresses: tuple[str, ...],
    out_json: str,
) -> str:
    args = ["python -m tools.debugger watch", "--execute", "--json-out", quote_arg(out_json)]
    add_runtime_artifact_args(args, rom_path=rom_path, symbols_path=symbols_path, save_state=save_state)
    if not save_state:
        args.extend(["--save-state", "<runtime-state>"])
    add_watch_args(args, watch_symbols=watch_symbols, addresses=addresses)
    if not (watch_symbols or addresses):
        args.extend(["--watch-address", "<watch-address>"])
    return " ".join(args)


def visual_snapshot_command(
    *,
    rom_path: str,
    symbols_path: str,
    save_state: str,
    out_json: str,
) -> str:
    args = ["python -m tools.debugger visual-snapshot", "--execute", "--json-out", quote_arg(out_json)]
    add_runtime_artifact_args(args, rom_path=rom_path, symbols_path=symbols_path, save_state=save_state)
    if not save_state:
        args.extend(["--save-state", "<runtime-state>"])
    return " ".join(args)


def audio_snapshot_command(
    *,
    rom_path: str,
    symbols_path: str,
    save_state: str,
    out_json: str,
) -> str:
    args = ["python -m tools.debugger audio-snapshot", "--execute", "--json-out", quote_arg(out_json)]
    add_runtime_artifact_args(args, rom_path=rom_path, symbols_path=symbols_path, save_state=save_state)
    if not save_state:
        args.extend(["--save-state", "<runtime-state>"])
    return " ".join(args)


def trace_instruction_command(
    *,
    packet_path: str,
    rom_path: str,
    symbols_path: str,
    save_state: str,
    symptom: str,
    symbols: tuple[str, ...],
    watch_symbols: tuple[str, ...],
    addresses: tuple[str, ...],
    changed_files: tuple[str, ...],
    out_trace: str,
    out_json: str,
) -> str:
    args = [
        "python -m tools.debugger trace-instructions",
        "--report",
        quote_arg(packet_path),
        "--execute",
        "--out-trace",
        quote_arg(out_trace),
        "--json-out",
        quote_arg(out_json),
    ]
    add_runtime_artifact_args(args, rom_path=rom_path, symbols_path=symbols_path, save_state=save_state)
    if not save_state:
        args.extend(["--save-state", "<runtime-state>"])
    add_symptom_arg(args, symptom=symptom)
    for symbol in symbols[:6]:
        args.extend(["--symbol", quote_arg(symbol)])
    for changed_file in changed_files[:6]:
        args.extend(["--changed-file", quote_arg(changed_file)])
    add_watch_args(args, watch_symbols=watch_symbols, addresses=addresses)
    if not (symbols or watch_symbols or addresses or changed_files):
        args.extend(["--symbol", "<target-symbol>"])
    return " ".join(args)


def effect_trace_command(
    *,
    trace: str,
    symbols_path: str,
    watch_symbols: tuple[str, ...],
    addresses: tuple[str, ...],
    out_json: str,
) -> str:
    args = ["python -m tools.debugger effect-trace", "--trace", quote_arg(trace), "--symbols", quote_arg(symbols_path), "--json-out", quote_arg(out_json)]
    for symbol in watch_symbols[:6]:
        args.extend(["--watch-symbol", quote_arg(symbol)])
    for address in addresses[:6]:
        args.extend(["--watch-address", command_address_arg(address)])
    return " ".join(args)


def reverse_query_command(
    *,
    effect_report: str,
    symbols_path: str,
    address: str,
    symbol: str,
    out_json: str,
) -> str:
    args = ["python -m tools.debugger reverse-query", "--report", quote_arg(effect_report), "--symbols", quote_arg(symbols_path), "--json-out", quote_arg(out_json)]
    if address:
        args.extend(["--address", command_address_arg(address)])
    if symbol:
        args.extend(["--symbol", quote_arg(symbol)])
    return " ".join(args)


def dynamic_taint_command(
    *,
    effect_report: str,
    symbols_path: str,
    watch_symbols: tuple[str, ...],
    addresses: tuple[str, ...],
    out_json: str,
) -> str:
    args = ["python -m tools.debugger dynamic-taint", "--report", quote_arg(effect_report), "--symbols", quote_arg(symbols_path), "--json-out", quote_arg(out_json)]
    for symbol in watch_symbols[:6]:
        args.extend(["--sink-symbol", quote_arg(symbol)])
    for address in addresses[:6]:
        args.extend(["--sink-address", command_address_arg(address)])
    return " ".join(args)


def causal_graph_command(
    *,
    reports: tuple[str, ...],
    symbols: tuple[str, ...],
    addresses: tuple[str, ...],
    out_json: str,
) -> str:
    args = ["python -m tools.debugger causal-graph", "--json-out", quote_arg(out_json)]
    for report in reports:
        args.extend(["--report", quote_arg(report)])
    for symbol in symbols[:6]:
        args.extend(["--symbol", quote_arg(symbol)])
    for address in addresses[:6]:
        args.extend(["--address", command_address_arg(address)])
    return " ".join(args)


def visualize_command(*, reports: tuple[str, ...], out_path: str) -> str:
    args = ["python -m tools.debugger visualize", "--out", quote_arg(out_path)]
    for report in reports:
        args.extend(["--report", quote_arg(report)])
    return " ".join(args)


def rank_command(*, packet_path: str, out_json: str) -> str:
    return f"python -m tools.debugger rank --report {quote_arg(packet_path)} --json-out {quote_arg(out_json)}"


def add_common_runtime_args(
    args: list[str],
    *,
    rom_path: str,
    symbols_path: str,
    save_state: str,
    symptom: str,
    symbols: tuple[str, ...],
    watch_symbols: tuple[str, ...],
    addresses: tuple[str, ...],
) -> None:
    add_runtime_artifact_args(args, rom_path=rom_path, symbols_path=symbols_path, save_state=save_state)
    add_symptom_arg(args, symptom=symptom)
    for symbol in symbols[:6]:
        args.extend(["--symbol", quote_arg(symbol)])
    for symbol in watch_symbols[:6]:
        args.extend(["--watch-symbol", quote_arg(symbol)])
    for address in addresses[:6]:
        args.extend(["--address", command_address_arg(address)])


def add_runtime_artifact_args(args: list[str], *, rom_path: str, symbols_path: str, save_state: str) -> None:
    if rom_path:
        args.extend(["--rom", quote_arg(rom_path)])
    if symbols_path:
        args.extend(["--symbols", quote_arg(symbols_path)])
    if save_state:
        args.extend(["--save-state", quote_arg(save_state)])


def add_symptom_arg(args: list[str], *, symptom: str) -> None:
    if symptom:
        args.extend(["--symptom", quote_arg(symptom)])


def add_watch_args(args: list[str], *, watch_symbols: tuple[str, ...], addresses: tuple[str, ...]) -> None:
    for symbol in watch_symbols[:6]:
        args.extend(["--watch-symbol", quote_arg(symbol)])
    for address in addresses[:6]:
        args.extend(["--watch-address", command_address_arg(address)])


def trace_output_placeholder(trace_output: str, *, save_state: str) -> str:
    return trace_output if save_state else "<instruction-trace.jsonl>"


def nonempty(values: list[str]) -> list[str]:
    return [value for value in values if value]


def packet_identity(
    *,
    symptom: str,
    artifacts: list[dict[str, Any]],
    symbols: tuple[str, ...],
    watch_symbols: tuple[str, ...],
    addresses: tuple[str, ...],
) -> str:
    text = "|".join(
        [
            symptom,
            *[str(artifact.get("sha256") or artifact.get("path") or "") for artifact in artifacts],
            *symbols,
            *watch_symbols,
            *addresses,
        ]
    )
    import hashlib

    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def quote_arg(value: Any) -> str:
    text = str(value)
    if not text:
        return '""'
    if any(char.isspace() for char in text):
        return '"' + text.replace('"', '\\"') + '"'
    return text


def unique_list(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out
