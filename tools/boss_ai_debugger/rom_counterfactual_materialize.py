from __future__ import annotations

import json
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError
from tools.trace import boss_ai_trace_capture as capture

from .canonical_classes import scenario_decision_class_fields
from .rom_contribution_trace import (
    MemoryPatch,
    RomContributionTraceSession,
    parse_memory_patch,
    stamp_rom_contribution_trace_class,
)
from .rom_scenarios import load_scenario_batch
from .rom_score_materialize import (
    DEFAULT_BASE_ROUTE,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_WATCH_FRAMES,
    materialization_for_scenario,
    normalize_name,
    replay_controls_from_manifest,
    fallback_replay_controls_from_manifest,
    run_score_materialization_attempt,
    should_fallback_to_pre_choice,
    validate_base_state_file,
)
from .rom_selector_materialize import load_manifest_entry
from .rom_switch_materialize import (
    load_manifest_save_entry,
    resolve_manifest_path,
    switch_materialization_patches,
    switch_materialization_state_field,
    validate_manifest_trace_basis,
)
from .universe import (
    ALLOWED_COUNTERFACTUAL_MUTATION_KEYS,
    COUNTERFACTUAL_MATERIALIZATION_KIND,
    COUNTERFACTUAL_MATERIALIZATION_PROOF_SCOPE,
    COUNTERFACTUAL_MUTATION_ALLOWLIST,
    SCHEMA_VERSION,
    build_boss_ai_universe_report,
)


GENERATOR_ID = "tools.boss_ai_debugger.rom_counterfactual_materialize"
SUPPORTED_DECISION_SURFACES = frozenset({"boss_ai_rule", "move_score"})


def run_rom_counterfactual_materialization_from_path(
    scenarios_path: Path,
    *,
    scenario_id: str = "",
    limit: int = 1,
    mutation_patch: str,
    surface: str = "move_choice",
    base_route: str = DEFAULT_BASE_ROUTE,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    rom: Path = capture.DEFAULT_ROM,
    symbols_path: Path = capture.DEFAULT_SYMBOLS,
    button: str = "a",
    button_delay: int = 8,
    watch_frames: int = DEFAULT_WATCH_FRAMES,
) -> dict[str, Any]:
    if surface == "switch_dispatch":
        return run_switch_counterfactual_materialization_from_path(
            scenarios_path,
            scenario_id=scenario_id,
            limit=limit,
            mutation_patch=mutation_patch,
            base_route=base_route,
            manifest_path=manifest_path,
            rom=rom,
            symbols_path=symbols_path,
            watch_frames=watch_frames,
        )
    if surface != "move_choice":
        raise PreferenceDataError("surface must be 'move_choice' or 'switch_dispatch'")
    scenarios = load_scenario_batch(scenarios_path)
    if scenario_id:
        scenarios = [scenario for scenario in scenarios if str(scenario.get("id", "")) == scenario_id]
    if limit > 0:
        scenarios = scenarios[:limit]
    if len(scenarios) != 1:
        raise PreferenceDataError(
            "counterfactual materialization currently requires exactly one selected scenario"
        )
    mutation = parse_memory_patch(mutation_patch)
    mutation_key = counterfactual_mutation_changed_key(mutation)
    if mutation_key not in ALLOWED_COUNTERFACTUAL_MUTATION_KEYS:
        raise PreferenceDataError(f"counterfactual mutation is not allowlisted: {mutation_key}")

    scenario = scenarios[0]
    move_names = capture.parse_move_names(capture.MOVE_CONSTANTS)
    move_name_to_id = {normalize_name(name): move_id for move_id, name in move_names.items()}
    scenario_materialization = materialization_for_scenario(
        scenario,
        move_name_to_id=move_name_to_id,
    )
    manifest_entry = load_manifest_entry(manifest_path, base_route)
    controls = replay_controls_from_manifest(
        manifest_entry,
        button=button,
        button_delay=button_delay,
        watch_frames=watch_frames,
    )
    fallback_controls = fallback_replay_controls_from_manifest(
        manifest_entry,
        button=button,
        button_delay=button_delay,
        watch_frames=watch_frames,
    )
    started = time.perf_counter()
    with ExitStack() as stack:
        session = stack.enter_context(
            RomContributionTraceSession(rom=rom, symbols_path=symbols_path)
        )
        validate_base_state_file(session.pyboy, session.symbols, controls.base_state)
        active_controls = controls
        try:
            baseline = run_score_materialization_attempt(
                session,
                controls=controls,
                base_route=base_route,
                scenario_id=str(scenario.get("id", "")),
                memory_patches=scenario_materialization.patches,
            )
        except Exception as exc:
            if fallback_controls is None or not should_fallback_to_pre_choice(
                controls,
                fallback_controls,
                exc,
            ):
                raise
            validate_base_state_file(
                session.pyboy,
                session.symbols,
                fallback_controls.base_state,
            )
            active_controls = fallback_controls
            baseline = run_score_materialization_attempt(
                session,
                controls=fallback_controls,
                base_route=base_route,
                scenario_id=str(scenario.get("id", "")),
                memory_patches=scenario_materialization.patches,
            )
        counterfactual = run_score_materialization_attempt(
            session,
            controls=active_controls,
            base_route=base_route,
            scenario_id=f"{scenario.get('id', '')}__{mutation_key}_{mutation.value:02x}",
            memory_patches=[*scenario_materialization.patches, mutation],
        )

    stamp_trace(
        baseline,
        scenario=scenario,
        trace_id=f"{scenario.get('id', '')}__baseline",
    )
    stamp_trace(
        counterfactual,
        scenario=scenario,
        trace_id=f"{scenario.get('id', '')}__{mutation_key}_{mutation.value:02x}",
    )
    baseline_observable = move_choice_observable(baseline)
    counterfactual_observable = move_choice_observable(counterfactual)
    if baseline_observable == counterfactual_observable:
        raise PreferenceDataError(
            "counterfactual mutation did not flip the observed ROM move choice"
        )

    universe = build_boss_ai_universe_report(
        rom_path=rom,
        symbols_path=symbols_path,
    )
    witnesses = counterfactual_witnesses_for_traces(
        universe,
        baseline_trace=baseline,
        counterfactual_trace=counterfactual,
        mutation=mutation,
        mutation_key=mutation_key,
        baseline_observable=baseline_observable,
        counterfactual_observable=counterfactual_observable,
        supported_decision_surfaces=SUPPORTED_DECISION_SURFACES,
    )
    if not witnesses:
        raise PreferenceDataError("counterfactual flip produced no currently missing witnesses")

    elapsed = time.perf_counter() - started
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": COUNTERFACTUAL_MATERIALIZATION_KIND,
        "source": str(scenarios_path),
        "generator": GENERATOR_ID,
        "basis": universe["class_identity"],
        "proof_scope": COUNTERFACTUAL_MATERIALIZATION_PROOF_SCOPE,
        "base_route": base_route,
        "base_state": str(active_controls.base_state),
        "scenario_count": 1,
        "checked_count": len(witnesses),
        "skipped_count": 0,
        "error_count": 0,
        "policy_disagreement_count": 0,
        "elapsed_seconds": elapsed,
        "scenario_id": str(scenario.get("id", "")),
        "surface": surface,
        "mutation": {
            "allowlist": COUNTERFACTUAL_MUTATION_ALLOWLIST,
            "changed_keys": [mutation_key],
            "patch": {
                "symbol_name": mutation.symbol_name,
                "offset": mutation.offset,
                "value": mutation.value,
            },
        },
        "baseline_observable": baseline_observable,
        "counterfactual_observable": counterfactual_observable,
        "witnesses": witnesses,
    }


def run_switch_counterfactual_materialization_from_path(
    scenarios_path: Path,
    *,
    scenario_id: str = "",
    limit: int = 1,
    mutation_patch: str,
    base_route: str,
    manifest_path: Path,
    rom: Path = capture.DEFAULT_ROM,
    symbols_path: Path = capture.DEFAULT_SYMBOLS,
    watch_frames: int = DEFAULT_WATCH_FRAMES,
) -> dict[str, Any]:
    scenarios = load_scenario_batch(scenarios_path)
    if scenario_id:
        scenarios = [scenario for scenario in scenarios if str(scenario.get("id", "")) == scenario_id]
    if limit > 0:
        scenarios = scenarios[:limit]
    if len(scenarios) != 1:
        raise PreferenceDataError(
            "counterfactual materialization currently requires exactly one selected scenario"
        )
    mutation = parse_memory_patch(mutation_patch)
    mutation_key = counterfactual_mutation_changed_key(mutation)
    if mutation_key not in ALLOWED_COUNTERFACTUAL_MUTATION_KEYS:
        raise PreferenceDataError(f"counterfactual mutation is not allowlisted: {mutation_key}")

    scenario = scenarios[0]
    manifest_entry = load_manifest_save_entry(manifest_path, base_route)
    validate_manifest_trace_basis(
        manifest_path,
        manifest_entry=manifest_entry,
        rom=rom,
        symbols_path=symbols_path,
    )
    base_state = resolve_manifest_path(
        str(manifest_entry[switch_materialization_state_field(manifest_entry)])
    )
    scenario_patches = switch_materialization_patches(scenario)
    started = time.perf_counter()
    with ExitStack() as stack:
        session = stack.enter_context(
            RomContributionTraceSession(rom=rom, symbols_path=symbols_path)
        )
        baseline = session.run(
            save_state=base_state,
            button="",
            watch_frames=watch_frames,
            metadata={"boss": base_route, "notes": f"switch-counterfactual:{scenario.get('id', '')}"},
            memory_patches=scenario_patches,
            finish_on="switch",
        )
        counterfactual = session.run(
            save_state=base_state,
            button="",
            watch_frames=watch_frames,
            metadata={
                "boss": base_route,
                "notes": f"switch-counterfactual:{scenario.get('id', '')}:{mutation_key}",
            },
            memory_patches=[*scenario_patches, mutation],
            finish_on="switch",
        )

    stamp_trace(
        baseline,
        scenario=scenario,
        trace_id=f"{scenario.get('id', '')}__baseline",
    )
    stamp_trace(
        counterfactual,
        scenario=scenario,
        trace_id=f"{scenario.get('id', '')}__{mutation_key}_{mutation.value:02x}",
    )
    baseline_observable = switch_dispatch_observable(baseline)
    counterfactual_observable = switch_dispatch_observable(counterfactual)
    if baseline_observable == counterfactual_observable:
        raise PreferenceDataError(
            "counterfactual mutation did not flip the observed ROM switch dispatch"
        )

    universe = build_boss_ai_universe_report(
        rom_path=rom,
        symbols_path=symbols_path,
    )
    witnesses = counterfactual_witnesses_for_traces(
        universe,
        baseline_trace=baseline,
        counterfactual_trace=counterfactual,
        mutation=mutation,
        mutation_key=mutation_key,
        baseline_observable=baseline_observable,
        counterfactual_observable=counterfactual_observable,
        supported_decision_surfaces=frozenset({"switch_dispatch"}),
    )
    if not witnesses:
        raise PreferenceDataError("counterfactual flip produced no currently missing witnesses")

    elapsed = time.perf_counter() - started
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": COUNTERFACTUAL_MATERIALIZATION_KIND,
        "source": str(scenarios_path),
        "generator": GENERATOR_ID,
        "basis": universe["class_identity"],
        "proof_scope": COUNTERFACTUAL_MATERIALIZATION_PROOF_SCOPE,
        "base_route": base_route,
        "base_state": str(base_state),
        "scenario_count": 1,
        "checked_count": len(witnesses),
        "skipped_count": 0,
        "error_count": 0,
        "policy_disagreement_count": 0,
        "elapsed_seconds": elapsed,
        "scenario_id": str(scenario.get("id", "")),
        "surface": "switch_dispatch",
        "mutation": {
            "allowlist": COUNTERFACTUAL_MUTATION_ALLOWLIST,
            "changed_keys": [mutation_key],
            "patch": {
                "symbol_name": mutation.symbol_name,
                "offset": mutation.offset,
                "value": mutation.value,
            },
        },
        "baseline_observable": baseline_observable,
        "counterfactual_observable": counterfactual_observable,
        "witnesses": witnesses,
    }


def stamp_trace(trace: dict[str, Any], *, scenario: dict[str, Any], trace_id: str) -> None:
    trace["trace_id"] = trace_id
    trace["scenario_id"] = trace_id
    stamp_rom_contribution_trace_class(trace)
    trace.update(scenario_decision_class_fields(scenario))


def counterfactual_witnesses_for_traces(
    universe: dict[str, Any],
    *,
    baseline_trace: dict[str, Any],
    counterfactual_trace: dict[str, Any],
    mutation: MemoryPatch,
    mutation_key: str,
    baseline_observable: dict[str, Any],
    counterfactual_observable: dict[str, Any],
    supported_decision_surfaces: frozenset[str],
) -> list[dict[str, Any]]:
    executed_rule_ids = set(str(item) for item in baseline_trace.get("executed_rule_ids", []))
    rows = universe["exhaustive_class_witness_catalog"]["catalog_rows"]
    witnesses: list[dict[str, Any]] = []
    for row in rows:
        if row.get("status") != "cataloged_missing_rom_proof":
            continue
        if row.get("witness_role") != "counterfactual_flip":
            continue
        rule_id = str(row.get("rule_id", "") or "")
        if rule_id not in executed_rule_ids:
            continue
        decision_surface = str(row.get("decision_surface", "") or "")
        if decision_surface not in supported_decision_surfaces:
            continue
        witnesses.append(
            {
                "status": "pass",
                "witness_role": "counterfactual_flip",
                "rule_id": rule_id,
                "decision_surface": decision_surface,
                "family": row.get("family", ""),
                "source_anchor": {
                    "anchor_status": "mapped",
                    "rule_id": rule_id,
                    "source_label": row.get("source_label", ""),
                    "parent_label": row.get("parent_label", ""),
                },
                "mutation": {
                    "allowlist": COUNTERFACTUAL_MUTATION_ALLOWLIST,
                    "changed_keys": [mutation_key],
                    "patch": {
                        "symbol_name": mutation.symbol_name,
                        "offset": mutation.offset,
                        "value": mutation.value,
                    },
                },
                "baseline_trace": baseline_trace,
                "counterfactual_trace": counterfactual_trace,
                "baseline_observable": baseline_observable,
                "counterfactual_observable": counterfactual_observable,
            }
        )
    return witnesses


def counterfactual_mutation_changed_key(mutation: MemoryPatch) -> str:
    if mutation.offset == 0:
        return mutation.symbol_name
    return f"{mutation.symbol_name}+{mutation.offset}"


def move_choice_observable(trace: dict[str, Any]) -> dict[str, Any]:
    chosen = trace.get("chosen")
    if not isinstance(chosen, dict):
        raise PreferenceDataError("ROM trace did not record a chosen move")
    move_id = safe_int(chosen.get("move_id"), 0)
    slot_index = safe_int(chosen.get("slot_index"), -1)
    if move_id <= 0 or slot_index < 0:
        raise PreferenceDataError("ROM trace chosen move is incomplete")
    return {
        "kind": "move_choice",
        "move_id": move_id,
        "slot_index": slot_index,
    }


def switch_dispatch_observable(trace: dict[str, Any]) -> dict[str, Any]:
    observation = trace.get("switch_observation")
    if not isinstance(observation, dict):
        raise PreferenceDataError("ROM trace did not record a switch observation")
    status = str(observation.get("status", "") or "")
    if not status:
        raise PreferenceDataError("ROM switch observation is missing status")
    return {
        "kind": "switch_dispatch",
        "status": status,
        "switch_confidence": safe_int(observation.get("switch_confidence"), 0),
        "switch_param": safe_int(observation.get("switch_param"), 0),
        "switch_index": safe_int(observation.get("switch_index"), 0),
    }


def safe_int(value: Any, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def write_rom_counterfactual_materialization_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def format_rom_counterfactual_materialization(
    report: dict[str, Any],
    *,
    limit: int = 12,
) -> str:
    witnesses = report.get("witnesses") if isinstance(report.get("witnesses"), list) else []
    lines = [
        "ROM counterfactual witness materialization",
        (
            f"scenario={report.get('scenario_id', '')} checked={report.get('checked_count', 0)} "
            f"skipped={report.get('skipped_count', 0)} errors={report.get('error_count', 0)}"
        ),
        (
            f"baseline={report.get('baseline_observable', {})} "
            f"counterfactual={report.get('counterfactual_observable', {})}"
        ),
    ]
    for witness in witnesses[:limit]:
        lines.append(
            "  "
            f"{witness.get('rule_id', '')} "
            f"surface={witness.get('decision_surface', '')} "
            f"mutation={','.join(witness.get('mutation', {}).get('changed_keys', []))}"
        )
    if len(witnesses) > limit:
        lines.append(f"  ... {len(witnesses) - limit} more")
    return "\n".join(lines)


def counterfactual_materialization_failure_count(report: dict[str, Any]) -> int:
    return (
        int(report.get("skipped_count", 0) or 0)
        + int(report.get("error_count", 0) or 0)
        + int(report.get("policy_disagreement_count", 0) or 0)
    )
