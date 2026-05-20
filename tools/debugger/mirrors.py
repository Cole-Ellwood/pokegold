from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog import ROOT, keyword_matches, triage_request
from .content_scenarios import EVENT_RUNTIME_ROUTE_KEY, EVENT_RUNTIME_ROUTE_LEGACY_KEY
from .provenance import build_provenance_report
from .reporting import load_reports
from .workflow import command_address_arg


OUTPUT_RUNTIME_EVIDENCE_KINDS = {
    "watch",
    "replay_watch",
    "instruction_trace",
    "effect_trace",
    "dynamic_taint",
    "visual_snapshot",
    "audio_snapshot",
}
OUTPUT_RUNTIME_STRONG_PROOF_STATUSES = {
    "runtime_observed",
    "instruction_observed",
    "taint_proven",
    "mirror_passed",
    "observed",
}
SNAPSHOT_RUNTIME_KINDS = {"visual_snapshot", "audio_snapshot"}
SNAPSHOT_HARDWARE_DOWNGRADE_REASON = "emulator_snapshot_not_hardware_proof"


@dataclass(frozen=True)
class MirrorRule:
    id: str
    title: str
    scope: str
    confidence: str
    path_prefixes: tuple[str, ...]
    symbols: tuple[str, ...]
    symptom_keywords: tuple[str, ...]
    evidence: tuple[str, ...]
    commands: tuple[str, ...]
    materialization_commands: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()


MIRROR_RULES = (
    MirrorRule(
        id="damage_oracle",
        title="Damage ROM-vs-oracle mirror",
        scope="DamageStats/DamageCalc/Stab/type/passive/item/weather/badge damage chain.",
        confidence="high for documented damage axes; known gaps stay in damage debugger docs",
        path_prefixes=(
            "engine/battle/effect_commands.asm",
            "engine/battle/late_gen_held_items.asm",
            "engine/battle/type_passive_damage_mods.asm",
            "data/moves/",
            "data/pokemon/base_stats/",
        ),
        symbols=(
            "wCurDamage",
            "BattleCommand_DamageStats",
            "BattleCommand_DamageCalc",
            "BattleCommand_Stab",
            "BattleCheckTypeMatchup",
            "CheckTypeMatchup",
            "wTypeMatchup",
            "TypeMatchups",
        ),
        symptom_keywords=(
            "damage",
            "stab",
            "type",
            "type matchup",
            "type effectiveness",
            "matchup",
            "immune",
            "immunity",
            "ground",
            "held item",
            "air balloon",
            "balloon",
            "passive",
            "ability",
            "item",
            "weather",
            "badge",
        ),
        evidence=(
            "tools/damage_debugger/oracle.py",
            "tools/damage_debugger/fuzz.py",
            "tools/damage_debugger/find.py",
            "tools/damage_debugger/README.md",
        ),
        commands=(
            "python -m tools.damage_debugger.oracle",
            "python -m tools.damage_debugger.fuzz --self-check-workers=2",
            "python -m tools.damage_debugger.fuzz --max-examples=500 --workers=2",
        ),
        materialization_commands=(
            "python -m tools.damage_debugger.find <scenario>",
            "python -m tools.damage_debugger.replay --scenario <scenario> --watch wCurDamage --json",
        ),
        gaps=(
            "DamageVariation remains range-checked instead of exact-oracle modeled.",
            "Use current damage debugger docs for remaining special-case oracle gaps.",
        ),
    ),
    MirrorRule(
        id="boss_ai_policy_mirror",
        title="Boss AI Python policy and ROM materialization mirror",
        scope="Boss move/switch scoring, selector behavior, generated policy expectations, and trace replay.",
        confidence="high for selector and materialized supported families; Python broad-policy scenarios are review aids until materialized",
        path_prefixes=(
            "engine/battle/ai/",
            "tools/boss_ai_debugger/",
            "tools/boss_ai_preference/",
            "audit/boss_ai_trace/",
        ),
        symbols=(
            "wEnemyAIMoveScores",
            "BossAI_SelectMove",
            "BossAI_ApplyMoveModel",
            "BossAI_SwitchOrTryItem",
        ),
        symptom_keywords=("boss", "ai", "selector", "score", "switch", "policy"),
        evidence=(
            "tools/boss_ai_debugger/differential.py",
            "tools/boss_ai_debugger/rom_score_materialize.py",
            "tools/boss_ai_debugger/rom_selector_materialize.py",
            "tools/boss_ai_debugger/README.md",
        ),
        commands=(
            "python -m tools.boss_ai_debugger trace-replay --trace-dir audit\\boss_ai_trace --fail-on-mismatch",
            "python -m tools.boss_ai_debugger generate --family all --count 500 --seed 1 --out .local\\tmp\\debugger_all_scenarios.jsonl",
            "python -m tools.boss_ai_debugger batch-simulate --scenarios .local\\tmp\\debugger_all_scenarios.jsonl --json-out .local\\tmp\\debugger_all_batch.json --quiet",
            "python -m tools.boss_ai_debugger diff --scenarios .local\\tmp\\debugger_all_scenarios.jsonl --trace-dir audit\\boss_ai_trace --json-out .local\\tmp\\debugger_diff.json",
        ),
        materialization_commands=(
            "python -m tools.boss_ai_debugger rom-selector-materialize --scenarios <scenarios.jsonl> --limit 20",
            "python -m tools.boss_ai_debugger rom-score-materialize --scenarios <scenarios.jsonl> --limit 4 --compare-fast-score",
            "python -m tools.boss_ai_debugger rom-switch-materialize --scenarios <scenarios.jsonl> --limit 20",
        ),
        gaps=(
            "Broad generated mastery-policy deltas are not all exact ROM score mirrors.",
        ),
    ),
    MirrorRule(
        id="static_invariant_mirror",
        title="Content invariant and ROM-byte materialization mirror",
        scope="Project-wide source, ROM map-event, common script-command including map-action/battle setup/trainer/mart/local-label/doorstate/command-queue macros, text block, movement data, labeled data/string block, labeled/aggregate INCBIN asset, audio, and invariant checks where no dynamic mirror exists yet.",
        confidence="medium-high for map-event, common script-command, map-action/battle setup/trainer/mart/local-label/doorstate/command-queue command, text macro block with RGBDS decimal interpolation, movement data, labeled db/dw/dn data/string block, audio channel-header, and labeled/aggregate asset ROM bytes when ROM/symbols are present; medium for source-only content shapes",
        path_prefixes=("home/", "macros/", "engine/", "data/", "maps/", "gfx/", "audio/"),
        symbols=("hROMBank", "FarCall", "Bankswitch"),
        symptom_keywords=("bank", "farcall", "layout", "graphics", "audio", "map", "text"),
        evidence=(
            "tools/debugger/content_mirror.py",
            "tools/audit/check_release_smoke.py",
            "tools/audit/check_cross_bank_call.py",
            "tools/audit/check_layout_orgs.py",
        ),
        commands=(
            "python tools\\audit\\check_release_smoke.py",
            "python tools\\audit\\check_cross_bank_call.py",
            "python tools\\audit\\check_layout_orgs.py",
            "python -m tools.debugger content-mirror --changed-file <changed_file>",
            "python -m tools.debugger content-scenarios --changed-file <changed_file> --out-scenarios .local\\tmp\\debugger_content_scenarios.jsonl",
            "python -m tools.debugger expect --source-file <changed_file>",
        ),
        materialization_commands=(
            "python -m tools.debugger content-mirror --source-file <changed_file>",
            "python -m tools.debugger content-scenarios --source-file <changed_file> --out-scenarios .local\\tmp\\debugger_content_scenarios.jsonl",
            "python -m tools.debugger expect --source-file <changed_file> --expect contains=<expected_text>",
            "python -m tools.debugger watch --watch-symbol <symbol> --execute --frames 120",
            "python -m tools.debugger provenance --source-file <changed_file>",
        ),
        gaps=(
            "Map event tables, common script-command bytecode, map-action/battle setup/trainer/mart/local-label/doorstate/command-queue command bytecode, text macro blocks with RGBDS decimal interpolation, movement data streams, labeled db/dw/dn data/string blocks, audio channel headers, and labeled/aggregate INCBIN assets can be byte-compared against the built ROM, but source expectation checks for other content are not full ROM behavior mirrors.",
            "Dedicated dynamic mirrors still need to be added for full script VM behavior, graphics/UI behavior, full audio playback, and arbitrary map interactions.",
        ),
    ),
)


def build_compare_plan(
    *,
    reports: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    symptom: str = "",
    runtime_observations: tuple[dict[str, Any], ...] = (),
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    runtime_observation_records = collect_runtime_observations(
        loaded_reports=loaded_reports,
        supplied=runtime_observations,
    )
    runtime_attempt_records = collect_runtime_attempts(loaded_reports=loaded_reports)
    matches = content_state_mirror_matches(
        loaded_reports,
        runtime_observations=runtime_observation_records,
        runtime_attempts=runtime_attempt_records,
    )
    matches.extend(
        content_fuzz_mirror_matches(
            loaded_reports,
            runtime_observations=runtime_observation_records,
            runtime_attempts=runtime_attempt_records,
        )
    )
    matches.extend(dynamic_expectation_mirror_matches(loaded_reports))
    matches.extend(match_mirrors(
        changed_files=changed_files,
        symbols=symbols,
        symptom=symptom,
        root=root,
    ))
    if not matches and symbols:
        provenance = build_provenance_report(symbols=symbols, root=root, max_hits=20)
        related_files = sorted(
            {
                path
                for symbol_report in provenance["symbols"]
                for path in symbol_report.get("related_files", [])
            }
        )
        if related_files:
            matches = match_mirrors(
                changed_files=tuple(related_files),
                symbols=symbols,
                symptom=symptom,
                root=root,
            )

    if not matches:
        triage = triage_request(changed_files=changed_files, symptom=symptom, root=root)
        matches = [
            {
                "id": "uncovered_surface",
                "title": "No dedicated mirror registered",
                "scope": "Fallback to general triage and static checks.",
                "confidence": "low",
                "matched_by": ["fallback"],
                "evidence": [],
                "commands": triage["commands"],
                "materialization_commands": [
                    "python -m tools.debugger provenance --source-file <changed_file>",
                    "python -m tools.debugger watch --watch-symbol <symbol>",
                ],
                "gaps": [
                    "No subsystem mirror/oracle is registered for this request.",
                ],
            }
        ]

    return {
        "schema_version": 1,
        "kind": "unified_debugger_compare_plan",
        "root": str(root),
        "valid": not report_errors,
        "error_count": len(report_errors),
        "errors": report_errors,
        "input_reports": [item["source"] for item in loaded_reports],
        "changed_files": list(changed_files),
        "symbols": list(symbols),
        "symptom": symptom,
        "match_count": len(matches),
        "matches": matches,
        "commands": unique_commands(matches, "commands"),
        "materialization_commands": unique_commands(matches, "materialization_commands"),
        "known_limits": [
            "This command plans mirror comparisons; it does not run expensive emulation by default.",
            "Content-state report mirrors prove the selected WRAM state and route to replay, but still need an executed patched save state before claiming final runtime behavior.",
            "Materialization commands are required before broad Python policy outputs become ROM behavior claims.",
        ],
    }


def content_state_mirror_matches(
    loaded_reports: list[dict[str, Any]],
    *,
    runtime_observations: list[dict[str, Any]],
    runtime_attempts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    matches = []
    runtime_evidence = [
        evidence
        for loaded in loaded_reports
        for evidence in runtime_mirror_evidence(loaded)
    ]
    for loaded in loaded_reports:
        data = loaded.get("data", {})
        if not isinstance(data, dict):
            continue
        if data.get("valid", True) is False:
            continue
        if data.get("kind") != "unified_debugger_content_state_materialization":
            continue
        source = str(loaded.get("source", ""))
        materializations = [
            item
            for item in dict_items(data.get("materializations"))
            if item.get("patches")
        ]
        output_materializations = [
            item
            for item in dict_items(data.get("materializations"))
            if item.get("outputs")
        ]
        if not materializations and not output_materializations:
            continue
        execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
        out_state = str(execution.get("out_state") or data.get("out_state") or "")
        executed = bool(data.get("executed") or execution.get("executed"))
        if materializations:
            scenario_ids = unique_list(
                str(item.get("scenario_id", ""))
                for item in materializations
                if item.get("scenario_id")
            )
            patch_symbols = unique_list(
                str(patch.get("symbol", ""))
                for materialization in materializations
                for patch in dict_items(materialization.get("patches"))
                if patch.get("symbol")
            )
            commands = [
                command
                for materialization in materializations[:6]
                for command in content_state_expect_commands(source=source, materialization=materialization)
            ]
            materialization_commands = [
                *[
                    f"python -m tools.debugger replay --report {source} --scenario-id {scenario_id} --execute-watch"
                    for scenario_id in scenario_ids[:6]
                ],
                *content_state_watch_commands(out_state=out_state, patch_symbols=patch_symbols),
            ]
            status = "state_materialized" if executed else "planned"
            proof_status = "state_materialized" if executed else "planned_only"
            route_status = content_state_runtime_route_status(
                materializations=materializations,
                executed=executed,
                runtime_observations=runtime_observations,
                runtime_attempts=runtime_attempts,
            )
            if route_status["mirror_status"] == "passed":
                status = "passed"
                proof_status = "mirror_passed"
            elif route_status["mirror_status"] == "failed":
                status = "failed"
                proof_status = "mirror_failed"
            gaps = []
            if executed:
                gaps.append(
                    "Patched content state was materialized, but replay/watch from that state is still required before claiming final runtime behavior."
                )
            else:
                gaps.append(
                    "Content-state patches are planned but no patched save state was executed; run the content-state --execute command before treating this as final emulator behavior."
                )
            evidence = [
                f"report={source}",
                f"scenarios={len(scenario_ids)}",
                f"patches={sum(len(item.get('patches', [])) for item in materializations)}",
                f"status={status}",
                f"proof_status={proof_status}",
                f"mirror_status={route_status['mirror_status']}",
                f"actual_proof_status={route_status['actual_proof_status']}",
            ]
            if out_state:
                evidence.append(f"state={out_state}")
            if route_status["runtime_attempt_kinds"]:
                evidence.append(f"runtime_attempt_kinds={','.join(route_status['runtime_attempt_kinds'])}")
            if route_status["required_runtime_symbols"]:
                evidence.append(f"required_runtime_symbols={','.join(route_status['required_runtime_symbols'])}")
            if route_status["observed_runtime_symbols"]:
                evidence.append(f"observed_runtime_symbols={','.join(route_status['observed_runtime_symbols'])}")
            matches.append(
                {
                    "id": "content_state_behavioral_mirror",
                    "title": "Content WRAM patch and replay mirror",
                    "scope": "Content scenarios with generated map-position, script-entry, or movement-entry WRAM state patches and replay targets.",
                    "confidence": "high for selected WRAM map-position/script-entry/movement-entry state; runtime transition confidence requires replay/watch from the patched state",
                    "matched_by": ["content_state_report"],
                    "status": status,
                    "proof_status": proof_status,
                    "mirror_status": route_status["mirror_status"],
                    "actual_proof_status": route_status["actual_proof_status"],
                    "expected_proof_status": route_status["expected_proof_status"],
                    "expected_sinks": route_status["expected_sinks"],
                    "attempted_sinks": route_status["attempted_sinks"],
                    "observed_sinks": route_status["observed_sinks"],
                    "required_runtime_symbols": route_status["required_runtime_symbols"],
                    "observed_runtime_symbols": route_status["observed_runtime_symbols"],
                    "runtime_attempt_reports": route_status["runtime_attempt_reports"],
                    "runtime_attempt_kinds": route_status["runtime_attempt_kinds"],
                    "evidence": evidence,
                    "commands": unique_list(commands),
                    "materialization_commands": unique_list(materialization_commands),
                    "gaps": gaps,
                    "runtime_evidence_gaps": route_status["runtime_evidence_gaps"],
                }
            )
        if output_materializations:
            scenario_ids = unique_list(
                str(item.get("scenario_id", ""))
                for item in output_materializations
                if item.get("scenario_id")
            )
            output_symbols = content_state_output_symbols(output_materializations)
            output_addresses = content_state_output_addresses(output_materializations)
            required_runtime_symbol_groups = content_state_output_required_runtime_symbol_groups(output_materializations)
            commands = content_output_expect_commands(
                source=source,
                materializations=output_materializations[:6],
            )
            mirror_status = content_output_mirror_status(
                output_symbols=output_symbols,
                output_addresses=output_addresses,
                required_runtime_symbol_groups=required_runtime_symbol_groups,
                runtime_evidence=runtime_evidence,
                runtime_attempts=runtime_attempts_for_scenarios(
                    scenario_ids=scenario_ids,
                    runtime_attempts=runtime_attempts,
                ),
            )
            gaps = []
            if mirror_status["status"] == "planned":
                gaps.append(
                    "Output-sink mirrors are planned until replay, watch, effect-trace, instruction tracing, or dynamic taint proves the selected helper writes the watched output state."
                )
            elif mirror_status["status"] == "partial":
                gaps.append(
                    f"Only {mirror_status['covered_count']} of {mirror_status['output_count']} output sink(s) have runtime evidence; add trace/watch coverage for the remaining output sinks."
                )
            elif mirror_status["status"] == "failed":
                gaps.append(
                    "A runtime watch/replay attempt covered every requested output sink but observed no requested output change."
                )
            materialization_commands = unique_list(
                [
                    *[
                        command
                        for materialization in output_materializations[:6]
                        for command in scalar_string_items(materialization.get("commands"))
                    ],
                    *[
                        f"python -m tools.debugger replay --report {source} --scenario-id {scenario_id} --execute-watch"
                        for scenario_id in scenario_ids[:6]
                    ],
                    (
                        "python -m tools.debugger dynamic-taint "
                        f"--report {source} "
                        + " ".join(f"--sink-symbol {symbol}" for symbol in output_symbols[:6])
                        + " "
                        + " ".join(f"--sink-address {command_address_arg(address)}" for address in output_addresses[:6])
                    ).strip(),
                ]
            )
            matches.append(
                {
                    "id": "content_output_behavioral_mirror",
                    "title": "Content output sink behavioral mirror",
                    "scope": "UI/graphics/audio output-sink scenarios with generated watch, replay, instruction-trace, and dynamic-taint proof routes.",
                    "confidence": content_output_mirror_confidence(mirror_status),
                    "matched_by": ["content_state_output_report"],
                    "status": mirror_status["status"],
                    "proof_status": mirror_status["proof_status"],
                    "mirror_status": mirror_status["mirror_status"],
                    "actual_proof_status": mirror_status["actual_proof_status"],
                    "covered_output_count": mirror_status["covered_count"],
                    "attempted_output_count": mirror_status["attempted_count"],
                    "output_count": mirror_status["output_count"],
                    "non_snapshot_covered_symbols": mirror_status["non_snapshot_covered_symbols"],
                    "non_snapshot_covered_addresses": mirror_status["non_snapshot_covered_addresses"],
                    "attempted_symbols": mirror_status["attempted_symbols"],
                    "attempted_addresses": mirror_status["attempted_addresses"],
                    "required_runtime_symbol_groups": mirror_status["required_runtime_symbol_groups"],
                    "observed_runtime_symbols": mirror_status["observed_runtime_symbols"],
                    "missing_runtime_symbol_groups": mirror_status["missing_runtime_symbol_groups"],
                    "runtime_reports": mirror_status["runtime_reports"],
                    "runtime_kinds": mirror_status["runtime_kinds"],
                    "runtime_attempt_reports": mirror_status["runtime_attempt_reports"],
                    "runtime_attempt_kinds": mirror_status["runtime_attempt_kinds"],
                    "weak_runtime_reports": mirror_status["weak_runtime_reports"],
                    "weak_runtime_kinds": mirror_status["weak_runtime_kinds"],
                    "hardware_behavior_proven": mirror_status.get("hardware_behavior_proven"),
                    "hardware_proof_statuses": mirror_status.get("hardware_proof_statuses", []),
                    "hardware_proof_boundaries": mirror_status.get("hardware_proof_boundaries", []),
                    "emulator_observed_runtime_kinds": mirror_status.get("emulator_observed_runtime_kinds", []),
                    "proof_downgrade_reason": mirror_status.get("proof_downgrade_reason", ""),
                    "evidence": [
                        f"report={source}",
                        f"scenarios={len(scenario_ids)}",
                        f"outputs={len(output_symbols) + len(output_addresses)}",
                        f"observed_outputs={mirror_status['covered_count']}",
                        f"status={mirror_status['status']}",
                        *mirror_status["evidence"],
                    ],
                    "scenario_ids": scenario_ids,
                    "related_symbols": output_symbols,
                    "related_addresses": output_addresses,
                    "commands": unique_list(commands),
                    "materialization_commands": materialization_commands,
                    "gaps": gaps,
                    "runtime_evidence_gaps": mirror_status["runtime_evidence_gaps"],
                }
            )
    return matches


def content_state_runtime_route_status(
    *,
    materializations: list[dict[str, Any]],
    executed: bool,
    runtime_observations: list[dict[str, Any]],
    runtime_attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    scenario_ids = unique_list(
        str(item.get("scenario_id", ""))
        for item in materializations
        if item.get("scenario_id")
    )
    expected_sinks = content_state_expected_sinks(materializations)
    observed_sinks = observed_sinks_for_scenarios(
        scenario_ids=scenario_ids,
        runtime_observations=runtime_observations,
    )
    required_runtime_symbols = content_state_required_runtime_symbols(materializations)
    observed_runtime_symbols = observed_runtime_symbols_for_scenarios(
        scenario_ids=scenario_ids,
        runtime_observations=runtime_observations,
    )
    relevant_attempts = runtime_attempts_for_scenarios(
        scenario_ids=scenario_ids,
        runtime_attempts=runtime_attempts,
    )
    attempted_sinks = attempted_sinks_for_scenarios(
        scenario_ids=scenario_ids,
        runtime_attempts=runtime_attempts,
    )
    missing_sinks = [sink for sink in expected_sinks if sink not in observed_sinks]
    missing_runtime_symbols = [
        symbol for symbol in required_runtime_symbols if symbol not in observed_runtime_symbols
    ]
    attempted_expected_sinks = [sink for sink in expected_sinks if sink in attempted_sinks]
    missing_attempted_sinks = [sink for sink in expected_sinks if sink not in attempted_sinks]
    materialization_status = aggregate_materialization_proof_status(materializations, executed=executed)
    has_executed_floor = executed or materialization_status in {"state_materialized", "executed", "observed"}
    if expected_sinks and not missing_sinks and not missing_runtime_symbols and has_executed_floor:
        mirror_status = "passed"
        actual_proof_status = "observed"
    elif observed_sinks:
        mirror_status = "inconclusive"
        actual_proof_status = "runtime_observed" if has_executed_floor else materialization_status
    elif expected_sinks and has_executed_floor and attempted_expected_sinks and not missing_attempted_sinks:
        mirror_status = "failed"
        actual_proof_status = "runtime_observed"
    elif attempted_expected_sinks:
        mirror_status = "inconclusive"
        actual_proof_status = "runtime_observed" if has_executed_floor else materialization_status
    else:
        mirror_status = materialization_status if materialization_status != "planned_only" else "planned_only"
        actual_proof_status = materialization_status
    runtime_evidence_gaps = []
    if missing_sinks:
        runtime_evidence_gaps.append("Runtime observations missing expected sink(s): " + ", ".join(missing_sinks))
    if missing_runtime_symbols:
        runtime_evidence_gaps.append(
            "Runtime observations missing required runtime symbol(s): " + ", ".join(missing_runtime_symbols)
        )
    if observed_sinks and not has_executed_floor:
        runtime_evidence_gaps.append("Runtime observations cannot pass this mirror until the content state is executed or otherwise state-materialized.")
    if attempted_expected_sinks and not has_executed_floor:
        runtime_evidence_gaps.append("Runtime attempts cannot pass or fail this mirror until the content state is executed or otherwise state-materialized.")
    if expected_sinks and not observed_sinks and not attempted_expected_sinks:
        runtime_evidence_gaps.append("No runtime observations were supplied for the expected sink set.")
    if expected_sinks and attempted_expected_sinks and not observed_sinks:
        runtime_evidence_gaps.append(
            "Runtime attempted expected sink(s) but observed no expected sink changes: "
            + ", ".join(attempted_expected_sinks)
        )
    if missing_attempted_sinks and attempted_expected_sinks:
        runtime_evidence_gaps.append(
            "Runtime attempts did not cover expected sink(s): " + ", ".join(missing_attempted_sinks)
        )
    return {
        "mirror_status": mirror_status,
        "actual_proof_status": actual_proof_status,
        "expected_proof_status": "runtime_observed",
        "expected_sinks": expected_sinks,
        "attempted_sinks": unique_list([sink for sink in attempted_sinks if sink in set(expected_sinks)]),
        "observed_sinks": observed_sinks,
        "required_runtime_symbols": required_runtime_symbols,
        "observed_runtime_symbols": observed_runtime_symbols,
        "runtime_attempt_reports": unique_list(str(item.get("source", "")) for item in relevant_attempts if item.get("source")),
        "runtime_attempt_kinds": unique_list(str(item.get("runtime_kind", "")) for item in relevant_attempts if item.get("runtime_kind")),
        "runtime_evidence_gaps": runtime_evidence_gaps,
    }


def content_state_expected_sinks(materializations: list[dict[str, Any]]) -> list[str]:
    return unique_list(
        sink
        for materialization in materializations
        for route in [
            materialization.get(EVENT_RUNTIME_ROUTE_KEY)
            if isinstance(materialization.get(EVENT_RUNTIME_ROUTE_KEY), dict)
            else materialization.get(EVENT_RUNTIME_ROUTE_LEGACY_KEY)
            if isinstance(materialization.get(EVENT_RUNTIME_ROUTE_LEGACY_KEY), dict)
            else {}
        ]
        for sink in [
            *scalar_string_items(materialization.get("expected_sinks")),
            *scalar_string_items(route.get("expected_sinks")),
            *[
                str(patch.get("symbol", ""))
                for patch in dict_items(materialization.get("patches"))
                if patch.get("symbol")
            ],
        ]
        if sink
    )


def content_state_required_runtime_symbols(materializations: list[dict[str, Any]]) -> list[str]:
    return unique_list(
        symbol
        for materialization in materializations
        for route in [
            materialization.get(EVENT_RUNTIME_ROUTE_KEY)
            if isinstance(materialization.get(EVENT_RUNTIME_ROUTE_KEY), dict)
            else materialization.get(EVENT_RUNTIME_ROUTE_LEGACY_KEY)
            if isinstance(materialization.get(EVENT_RUNTIME_ROUTE_LEGACY_KEY), dict)
            else {}
        ]
        for symbol in [
            *scalar_string_items(materialization.get("required_runtime_symbols")),
            *scalar_string_items(route.get("required_runtime_symbols")),
        ]
        if symbol
    )


def aggregate_materialization_proof_status(materializations: list[dict[str, Any]], *, executed: bool) -> str:
    if executed:
        return "state_materialized"
    statuses = {
        str(item.get("actual_proof_status") or "")
        for item in materializations
        if item.get("actual_proof_status")
    }
    if "state_materialized" in statuses:
        return "state_materialized"
    if "ready_to_run" in statuses or any(str(item.get("status", "")) == "ready" for item in materializations):
        return "ready_to_run"
    return "planned_only"


def collect_runtime_observations(
    *,
    loaded_reports: list[dict[str, Any]],
    supplied: tuple[dict[str, Any], ...],
) -> list[dict[str, Any]]:
    observations = [normalize_runtime_observation(item) for item in supplied if isinstance(item, dict)]
    for loaded in loaded_reports:
        data = loaded.get("data")
        if not isinstance(data, dict):
            continue
        if data.get("valid", True) is False:
            continue
        for item in dict_items(data.get("runtime_observations")):
            observation = normalize_runtime_observation(item)
            if loaded.get("source") and not observation.get("source"):
                observation["source"] = str(loaded.get("source", ""))
            observations.append(observation)
        observations.extend(runtime_observations_from_report(loaded))
    return observations


def collect_runtime_attempts(*, loaded_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        attempt
        for loaded in loaded_reports
        for attempt in runtime_attempts_from_report(loaded)
    ]


def runtime_observations_from_report(loaded: dict[str, Any]) -> list[dict[str, Any]]:
    observations = []
    scenario_ids = report_scenario_ids(loaded.get("data") if isinstance(loaded.get("data"), dict) else {})
    for evidence in runtime_mirror_evidence(loaded):
        if not output_runtime_evidence_is_strong(evidence):
            continue
        observed_sinks = unique_list(
            [
                *scalar_string_items(evidence.get("observed_sinks")),
                *scalar_string_items(evidence.get("symbols")),
                *scalar_string_items(evidence.get("addresses")),
            ]
        )
        if "observed_runtime_symbols" in evidence:
            observed_runtime_symbols = scalar_string_items(evidence.get("observed_runtime_symbols"))
        else:
            observed_runtime_symbols = scalar_string_items(evidence.get("symbols"))
        observation = normalize_runtime_observation(
            {
                "source": evidence.get("source", loaded.get("source", "")),
                "runtime_kind": evidence.get("kind", ""),
                "proof_status": evidence.get("proof_status", ""),
                "scenario_ids": scenario_ids,
                "observed_sinks": observed_sinks,
                "observed_runtime_symbols": observed_runtime_symbols,
            }
        )
        observations.append(observation)
    return observations


def runtime_attempts_from_report(loaded: dict[str, Any]) -> list[dict[str, Any]]:
    data = loaded.get("data")
    if not isinstance(data, dict):
        return []
    if data.get("valid", True) is False:
        return []
    source = str(loaded.get("source", ""))
    kind = str(data.get("kind", ""))
    scenario_ids = report_scenario_ids(data)
    if kind == "unified_debugger_watch_report":
        events = dict_items(data.get("events"))
        if not data.get("executed") and not events:
            return []
        return [
            normalize_runtime_attempt(
                {
                    "source": source,
                    "runtime_kind": "watch",
                    "proof_status": "runtime_observed",
                    "scenario_ids": scenario_ids,
                    "attempted_sinks": watch_attempt_sinks(data),
                }
            )
        ]
    if kind == "unified_debugger_replay_plan":
        attempts = []
        replay_targets = data.get("replay_targets") if isinstance(data.get("replay_targets"), dict) else {}
        replay_target_sinks = [
            *scalar_string_items(replay_targets.get("watch_symbols")),
            *scalar_string_items(replay_targets.get("watch_addresses")),
        ]
        watch_report = data.get("watch_report") if isinstance(data.get("watch_report"), dict) else {}
        if watch_report:
            attempts.extend(runtime_attempts_from_report({"source": source, "data": watch_report}))
            for attempt in attempts:
                attempt["runtime_kind"] = "replay_watch"
                attempt["scenario_ids"] = unique_list(
                    [*scenario_ids, *scalar_string_items(attempt.get("scenario_ids"))]
                )
                attempt["scenario_id"] = attempt["scenario_ids"][0] if len(attempt["scenario_ids"]) == 1 else ""
                attempt["attempted_sinks"] = unique_list(
                    [*scalar_string_items(attempt.get("attempted_sinks")), *replay_target_sinks]
                )
        if not attempts and data.get("executed_watch"):
            attempts.append(
                normalize_runtime_attempt(
                    {
                        "source": source,
                        "runtime_kind": "replay_watch",
                        "proof_status": "runtime_observed",
                        "scenario_ids": scenario_ids,
                        "attempted_sinks": replay_target_sinks,
                    }
                )
            )
        return attempts
    return []


def normalize_runtime_observation(item: dict[str, Any]) -> dict[str, Any]:
    scenario_ids = unique_list(
        [
            *scalar_string_items(item.get("scenario_id")),
            *scalar_string_items(item.get("scenario_ids")),
        ]
    )
    observed_sinks = unique_list(
        [
            *scalar_string_items(item.get("observed_sinks")),
            *scalar_string_items(item.get("sinks")),
            *scalar_string_items(item.get("symbols")),
            *scalar_string_items(item.get("addresses")),
        ]
    )
    observed_runtime_symbols = unique_list(
        [
            *scalar_string_items(item.get("observed_runtime_symbols")),
            *scalar_string_items(item.get("runtime_symbols")),
            *scalar_string_items(item.get("symbols")),
            *scalar_string_items(item.get("hit_function_symbols")),
        ]
    )
    return {
        **item,
        "scenario_id": scenario_ids[0] if len(scenario_ids) == 1 else str(item.get("scenario_id", "")),
        "scenario_ids": scenario_ids,
        "observed_sinks": observed_sinks,
        "observed_runtime_symbols": observed_runtime_symbols,
    }


def normalize_runtime_attempt(item: dict[str, Any]) -> dict[str, Any]:
    scenario_ids = unique_list(
        [
            *scalar_string_items(item.get("scenario_id")),
            *scalar_string_items(item.get("scenario_ids")),
        ]
    )
    attempted_sinks = unique_list(
        [
            *scalar_string_items(item.get("attempted_sinks")),
            *scalar_string_items(item.get("sinks")),
            *scalar_string_items(item.get("symbols")),
            *scalar_string_items(item.get("addresses")),
        ]
    )
    return {
        **item,
        "scenario_id": scenario_ids[0] if len(scenario_ids) == 1 else str(item.get("scenario_id", "")),
        "scenario_ids": scenario_ids,
        "attempted_sinks": attempted_sinks,
    }


def observed_sinks_for_scenarios(
    *,
    scenario_ids: list[str],
    runtime_observations: list[dict[str, Any]],
) -> list[str]:
    scenario_id_set = set(scenario_ids)
    return unique_list(
        sink
        for observation in runtime_observations
        if runtime_observation_applies_to_scenarios(observation, scenario_id_set=scenario_id_set)
        for sink in scalar_string_items(observation.get("observed_sinks"))
    )


def observed_runtime_symbols_for_scenarios(
    *,
    scenario_ids: list[str],
    runtime_observations: list[dict[str, Any]],
) -> list[str]:
    scenario_id_set = set(scenario_ids)
    return unique_list(
        symbol
        for observation in runtime_observations
        if runtime_observation_applies_to_scenarios(observation, scenario_id_set=scenario_id_set)
        for symbol in scalar_string_items(observation.get("observed_runtime_symbols"))
    )


def runtime_attempts_for_scenarios(
    *,
    scenario_ids: list[str],
    runtime_attempts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scenario_id_set = set(scenario_ids)
    return [
        attempt
        for attempt in runtime_attempts
        if runtime_observation_applies_to_scenarios(attempt, scenario_id_set=scenario_id_set)
    ]


def attempted_sinks_for_scenarios(
    *,
    scenario_ids: list[str],
    runtime_attempts: list[dict[str, Any]],
) -> list[str]:
    return unique_list(
        sink
        for attempt in runtime_attempts_for_scenarios(scenario_ids=scenario_ids, runtime_attempts=runtime_attempts)
        for sink in scalar_string_items(attempt.get("attempted_sinks"))
    )


def runtime_observation_applies_to_scenarios(
    observation: dict[str, Any],
    *,
    scenario_id_set: set[str],
) -> bool:
    if not scenario_id_set:
        return True
    observation_ids = set(scalar_string_items(observation.get("scenario_ids")))
    if not observation_ids:
        scenario_id = str(observation.get("scenario_id", ""))
        if scenario_id:
            observation_ids.add(scenario_id)
    return not observation_ids or bool(observation_ids.intersection(scenario_id_set))


def report_scenario_ids(data: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            *scalar_string_items(data.get("scenario_id")),
            *scalar_string_items(data.get("scenario_ids")),
            *scalar_string_items(data.get("input_scenario_ids")),
            *scalar_string_items(
                (data.get("replay_targets") if isinstance(data.get("replay_targets"), dict) else {}).get("scenario_ids")
            ),
        ]
    )


def content_fuzz_mirror_matches(
    loaded_reports: list[dict[str, Any]],
    *,
    runtime_observations: list[dict[str, Any]],
    runtime_attempts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    matches = []
    for loaded in loaded_reports:
        data = loaded.get("data", {})
        if not isinstance(data, dict):
            continue
        if data.get("valid", True) is False:
            continue
        if data.get("kind") != "unified_debugger_fuzz_plan":
            continue
        source = str(loaded.get("source", ""))
        cases = [
            item
            for item in dict_items(data.get("fuzz_cases"))
            if is_content_fuzz_case(item)
        ]
        if not cases:
            continue
        scenario_ids = unique_list(str(case.get("scenario_id", "")) for case in cases if case.get("scenario_id"))
        source_files = unique_list(str(case.get("source_file", "")) for case in cases if case.get("source_file"))
        related_symbols = unique_list(
            symbol
            for case in cases
            for symbol in content_fuzz_case_symbols(case)
        )
        runtime_routes = unique_list(content_case_runtime_route(case) for case in cases)
        expected_sinks = content_fuzz_expected_sinks(cases)
        observed_sinks = observed_sinks_for_scenarios(
            scenario_ids=scenario_ids,
            runtime_observations=runtime_observations,
        )
        required_runtime_symbols = content_fuzz_required_runtime_symbols(cases)
        observed_runtime_symbols = observed_runtime_symbols_for_scenarios(
            scenario_ids=scenario_ids,
            runtime_observations=runtime_observations,
        )
        relevant_attempts = runtime_attempts_for_scenarios(
            scenario_ids=scenario_ids,
            runtime_attempts=runtime_attempts,
        )
        runtime_attempt_kinds = unique_list(
            str(item.get("runtime_kind", ""))
            for item in relevant_attempts
            if item.get("runtime_kind")
        )
        attempted_sinks = attempted_sinks_for_scenarios(
            scenario_ids=scenario_ids,
            runtime_attempts=runtime_attempts,
        )
        route_status = content_fuzz_runtime_route_status(
            expected_sinks=expected_sinks,
            observed_sinks=observed_sinks,
            attempted_sinks=attempted_sinks,
            runtime_attempt_kinds=runtime_attempt_kinds,
            required_runtime_symbols=required_runtime_symbols,
            observed_runtime_symbols=observed_runtime_symbols,
        )
        commands = [
            *content_fuzz_expect_commands(source=source, cases=cases),
            *[
                f"python -m tools.debugger content-mirror --source-file {path}"
                for path in source_files[:6]
            ],
        ]
        materialization_commands = [
            command
            for case in cases[:6]
            for command in content_fuzz_materialization_commands(case)
        ]
        materialization_commands.extend(
            f"python -m tools.debugger replay --report {source} --scenario-id {scenario_id} --execute-watch"
            for scenario_id in scenario_ids[:6]
        )
        evidence = [
            f"report={source}",
            f"cases={len(cases)}",
            f"scenarios={len(scenario_ids)}",
        ]
        if runtime_routes:
            evidence.append(f"runtime_routes={','.join(runtime_routes)}")
        evidence.extend(
            [
                f"mirror_status={route_status['mirror_status']}",
                f"actual_proof_status={route_status['actual_proof_status']}",
            ]
        )
        if route_status["runtime_attempt_kinds"]:
            evidence.append(f"runtime_attempt_kinds={','.join(route_status['runtime_attempt_kinds'])}")
        if route_status["required_runtime_symbols"]:
            evidence.append(f"required_runtime_symbols={','.join(route_status['required_runtime_symbols'])}")
        if route_status["observed_runtime_symbols"]:
            evidence.append(f"observed_runtime_symbols={','.join(route_status['observed_runtime_symbols'])}")
        gaps = []
        if route_status["mirror_status"] != "passed":
            gaps.append(
                "Content fuzz reports describe planned behavioral routes; run the materialization and replay/watch commands before treating them as final emulator behavior."
            )
        matches.append(
            {
                "id": "content_fuzz_behavioral_mirror",
                "title": "Content fuzz expectation and behavioral mirror",
                "scope": "Content fuzz cases with generated scenario, state-precondition, runtime probe, and content mirror routes.",
                "confidence": "medium-high for generated content cases; runtime confidence requires state materialization plus replay/watch proof",
                "matched_by": ["content_fuzz_report"],
                "status": route_status["status"],
                "proof_status": route_status["proof_status"],
                "mirror_status": route_status["mirror_status"],
                "actual_proof_status": route_status["actual_proof_status"],
                "expected_proof_status": "runtime_observed",
                "expected_sinks": expected_sinks,
                "attempted_sinks": route_status["attempted_sinks"],
                "observed_sinks": route_status["observed_sinks"],
                "required_runtime_symbols": route_status["required_runtime_symbols"],
                "observed_runtime_symbols": route_status["observed_runtime_symbols"],
                "runtime_attempt_reports": unique_list(str(item.get("source", "")) for item in relevant_attempts if item.get("source")),
                "runtime_attempt_kinds": route_status["runtime_attempt_kinds"],
                "evidence": evidence,
                "scenario_ids": scenario_ids,
                "source_files": source_files,
                "related_symbols": related_symbols,
                "runtime_routes": runtime_routes,
                "commands": unique_list(commands),
                "materialization_commands": unique_list(materialization_commands),
                "gaps": gaps,
                "runtime_evidence_gaps": route_status["runtime_evidence_gaps"],
            }
        )
    return matches


def content_fuzz_runtime_route_status(
    *,
    expected_sinks: list[str],
    observed_sinks: list[str],
    attempted_sinks: list[str],
    runtime_attempt_kinds: list[str],
    required_runtime_symbols: list[str],
    observed_runtime_symbols: list[str],
) -> dict[str, Any]:
    covered_sinks = [sink for sink in expected_sinks if sink in observed_sinks]
    missing_sinks = [sink for sink in expected_sinks if sink not in observed_sinks]
    missing_runtime_symbols = [
        symbol for symbol in required_runtime_symbols if symbol not in observed_runtime_symbols
    ]
    attempted_expected_sinks = [sink for sink in expected_sinks if sink in attempted_sinks]
    missing_attempted_sinks = [sink for sink in expected_sinks if sink not in attempted_sinks]
    if expected_sinks and not missing_sinks and not missing_runtime_symbols:
        status = "passed"
        proof_status = "mirror_passed"
        mirror_status = "passed"
        actual_proof_status = "observed"
    elif covered_sinks:
        status = "partial"
        proof_status = "instruction_observed"
        mirror_status = "inconclusive"
        actual_proof_status = "instruction_observed"
    elif expected_sinks and not missing_attempted_sinks:
        status = "failed"
        proof_status = "mirror_failed"
        mirror_status = "failed"
        actual_proof_status = "runtime_observed"
    elif attempted_expected_sinks:
        status = "partial"
        proof_status = "instruction_observed"
        mirror_status = "inconclusive"
        actual_proof_status = "runtime_observed"
    else:
        status = "planned"
        proof_status = "planned_only"
        mirror_status = "not_run"
        actual_proof_status = "planned_only"
    runtime_evidence_gaps = []
    if missing_sinks:
        runtime_evidence_gaps.append("Runtime observations missing expected fuzz sink(s): " + ", ".join(missing_sinks))
    if missing_runtime_symbols:
        runtime_evidence_gaps.append(
            "Runtime observations missing required runtime symbol(s): " + ", ".join(missing_runtime_symbols)
        )
    if expected_sinks and not observed_sinks and not attempted_expected_sinks:
        runtime_evidence_gaps.append("No runtime observations were supplied for the expected fuzz sink set.")
    if expected_sinks and attempted_expected_sinks and not observed_sinks:
        runtime_evidence_gaps.append(
            "Runtime attempted expected fuzz sink(s) but observed no expected sink changes: "
            + ", ".join(attempted_expected_sinks)
        )
    if missing_attempted_sinks and attempted_expected_sinks:
        runtime_evidence_gaps.append(
            "Runtime attempts did not cover expected fuzz sink(s): " + ", ".join(missing_attempted_sinks)
        )
    if not expected_sinks:
        runtime_evidence_gaps.append("No expected runtime sinks were declared for these content fuzz cases.")
    return {
        "status": status,
        "proof_status": proof_status,
        "mirror_status": mirror_status,
        "actual_proof_status": actual_proof_status,
        "attempted_sinks": unique_list([sink for sink in attempted_sinks if sink in set(expected_sinks)]),
        "observed_sinks": unique_list([sink for sink in observed_sinks if sink in set(expected_sinks)]),
        "required_runtime_symbols": unique_list(required_runtime_symbols),
        "observed_runtime_symbols": unique_list(
            [symbol for symbol in observed_runtime_symbols if symbol in set(required_runtime_symbols)]
        ),
        "runtime_attempt_kinds": unique_list(runtime_attempt_kinds),
        "runtime_evidence_gaps": runtime_evidence_gaps,
    }


def dynamic_expectation_mirror_matches(loaded_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expectation_reports = [
        loaded
        for loaded in loaded_reports
        if isinstance(loaded.get("data"), dict)
        and loaded["data"].get("kind") == "unified_debugger_expectation_report"
        and loaded["data"].get("valid", True)
        and int(loaded["data"].get("expectation_count", 0)) > 0
    ]
    runtime_evidence = [
        evidence
        for loaded in loaded_reports
        for evidence in runtime_mirror_evidence(loaded)
    ]
    if not expectation_reports or not runtime_evidence:
        return []

    matches = []
    runtime_sources = unique_list(item["source"] for item in runtime_evidence)
    runtime_kinds = unique_list(item["kind"] for item in runtime_evidence)
    runtime_symbols = unique_list(
        symbol
        for item in runtime_evidence
        for symbol in scalar_string_items(item.get("symbols"))
    )
    runtime_addresses = unique_list(
        address
        for item in runtime_evidence
        for address in scalar_string_items(item.get("addresses"))
    )
    runtime_files = unique_list(
        path
        for item in runtime_evidence
        for path in scalar_string_items(item.get("source_files"))
    )
    runtime_artifacts = unique_list(
        artifact
        for item in runtime_evidence
        for artifact in scalar_string_items(item.get("artifacts"))
    )
    materialization_commands = unique_list(
        command
        for item in runtime_evidence
        for command in scalar_string_items(item.get("commands"))
    )
    for loaded in expectation_reports:
        report = loaded["data"]
        source = str(loaded.get("source", ""))
        passed = bool(report.get("passed"))
        failed_count = int(report.get("failed_count", 0))
        skipped_count = int(report.get("skipped_count", 0))
        uses_snapshot_evidence = expectation_report_uses_snapshot_evidence(report)
        hardware_summary = runtime_snapshot_hardware_summary(
            runtime_evidence,
            enabled=uses_snapshot_evidence,
        )
        proof_status = dynamic_expectation_proof_status(
            passed=passed,
            skipped_count=skipped_count,
            uses_snapshot_evidence=uses_snapshot_evidence,
            hardware_summary=hardware_summary,
        )
        mirror_status = "passed" if passed else "failed"
        runtime_proof_statuses = unique_list(
            str(item.get("proof_status", ""))
            for item in runtime_evidence
            if item.get("proof_status")
        )
        gaps = []
        if not passed:
            gaps.append(
                "Expectation mirror did not pass; this is a dynamic mirror failure to triage, not proof of correctness."
            )
        if skipped_count:
            gaps.append(
                f"{skipped_count} expectation(s) were skipped; add stronger runtime evidence or expectation syntax before treating the mirror as complete."
            )
        evidence = [
            f"expectation_report={source}",
            f"expectations={report.get('expectation_count', 0)}",
            f"passed={report.get('passed')}",
            f"mirror_status={mirror_status}",
            f"proof_status={proof_status}",
        ]
        if runtime_proof_statuses:
            evidence.append(f"runtime_proof_statuses={','.join(runtime_proof_statuses)}")
        if hardware_summary:
            evidence.extend(runtime_snapshot_hardware_evidence(hardware_summary))
        evidence.extend(
            [
                f"runtime_reports={len(runtime_sources)}",
                f"runtime_kinds={','.join(runtime_kinds)}",
            ]
        )
        summary = report.get("evidence_summary") if isinstance(report.get("evidence_summary"), dict) else {}
        scenario_ids = unique_list(scalar_string_items(summary.get("scenario_ids")))
        commands = unique_list(
            [
                *scalar_string_items(report.get("commands")),
                f"python -m tools.debugger expect --report {source}",
                f"python -m tools.debugger report --report {source}",
                f"python -m tools.debugger visualize --report {source} --format html --out .local\\tmp\\debugger_expectation_mirror.html",
            ]
        )
        matches.append(
            {
                "id": "runtime_expectation_dynamic_mirror",
                "title": "Execution-backed expectation mirror",
                "scope": "High-level expectations checked against executed ROM watch, replay, instruction-trace, dynamic-taint, visual/audio snapshot, or content-state evidence from any ROM surface.",
                "confidence": "high when passed with instruction/dynamic/write/framebuffer evidence; failure is treated as a dynamic mirror counterexample",
                "matched_by": ["expectation_report", "runtime_report"],
                "expectation_report": source,
                "expectation_status": "passed" if passed else "failed",
                "status": "passed" if passed else "failed",
                "proof_status": proof_status,
                "mirror_status": mirror_status,
                "actual_proof_status": proof_status,
                "expected_proof_status": "mirror_passed",
                "passed": passed,
                "failed_count": failed_count,
                "runtime_reports": runtime_sources,
                "runtime_kinds": runtime_kinds,
                "runtime_proof_statuses": runtime_proof_statuses,
                "scenario_ids": scenario_ids,
                "source_files": unique_list([*runtime_files, *scalar_string_items(summary.get("source_files"))]),
                "related_symbols": unique_list([*runtime_symbols, *scalar_string_items(summary.get("symbols"))]),
                "related_addresses": unique_list([*runtime_addresses, *scalar_string_items(summary.get("addresses"))]),
                "artifacts": runtime_artifacts,
                **hardware_summary,
                "evidence": evidence,
                "commands": commands,
                "materialization_commands": materialization_commands,
                "gaps": gaps,
            }
        )
    return matches


def expectation_report_uses_snapshot_evidence(report: dict[str, Any]) -> bool:
    if safe_int(report.get("evidence_framebuffer_count")) > 0:
        return True
    if safe_int(report.get("evidence_audio_snapshot_count")) > 0:
        return True
    summary = report.get("evidence_summary") if isinstance(report.get("evidence_summary"), dict) else {}
    return bool(dict_items(summary.get("framebuffers")) or dict_items(summary.get("audio_snapshots")))


def dynamic_expectation_proof_status(
    *,
    passed: bool,
    skipped_count: int,
    uses_snapshot_evidence: bool,
    hardware_summary: dict[str, Any],
) -> str:
    if not passed or skipped_count:
        return "mirror_failed"
    if (
        uses_snapshot_evidence
        and hardware_summary.get("hardware_behavior_proven") is False
        and hardware_summary.get("emulator_observed_runtime_kinds")
    ):
        return "runtime_observed"
    return "mirror_passed"


def runtime_snapshot_hardware_summary(
    runtime_evidence: list[dict[str, Any]],
    *,
    enabled: bool,
) -> dict[str, Any]:
    if not enabled:
        return {}
    records = [
        item
        for item in runtime_evidence
        if item.get("kind") in SNAPSHOT_RUNTIME_KINDS
        and "hardware_behavior_proven" in item
    ]
    if not records:
        return {}
    unproven = [item for item in records if item.get("hardware_behavior_proven") is not True]
    hardware_behavior_proven = not unproven
    summary: dict[str, Any] = {
        "hardware_behavior_proven": hardware_behavior_proven,
        "hardware_proof_statuses": unique_list(
            str(item.get("hardware_proof_status", ""))
            for item in records
            if item.get("hardware_proof_status")
        ),
        "hardware_proof_boundaries": unique_list(
            str(item.get("hardware_proof_boundary", ""))
            for item in records
            if item.get("hardware_proof_boundary")
        ),
        "emulator_observed_runtime_kinds": unique_list(
            str(item.get("kind", ""))
            for item in unproven
            if item.get("kind")
        ),
    }
    if unproven:
        summary["proof_downgrade_reason"] = SNAPSHOT_HARDWARE_DOWNGRADE_REASON
        summary["runtime_evidence_gaps"] = [
            "PyBoy visual/audio snapshot evidence proves emulator-observed digest/sample state only; hardware PPU/APU behavior remains unproven."
        ]
    return summary


def runtime_snapshot_hardware_evidence(summary: dict[str, Any]) -> list[str]:
    evidence = [f"hardware_behavior_proven={summary.get('hardware_behavior_proven')}"]
    statuses = scalar_string_items(summary.get("hardware_proof_statuses"))
    if statuses:
        evidence.append(f"hardware_proof_statuses={','.join(statuses)}")
    runtime_kinds = scalar_string_items(summary.get("emulator_observed_runtime_kinds"))
    if runtime_kinds:
        evidence.append(f"emulator_observed_runtime_kinds={','.join(runtime_kinds)}")
    if summary.get("proof_downgrade_reason"):
        evidence.append(f"proof_downgrade_reason={summary.get('proof_downgrade_reason')}")
    return evidence


def content_output_mirror_status(
    *,
    output_symbols: list[str],
    output_addresses: list[str],
    required_runtime_symbol_groups: list[list[str]],
    runtime_evidence: list[dict[str, Any]],
    runtime_attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    requested_symbols = unique_list(output_symbols)
    requested_addresses = unique_addresses(output_addresses)
    strong_evidence = [item for item in runtime_evidence if output_runtime_evidence_is_strong(item)]
    non_snapshot_evidence = [
        item
        for item in strong_evidence
        if str(item.get("kind", "")) not in SNAPSHOT_RUNTIME_KINDS
    ]
    weak_evidence = [
        item
        for item in runtime_evidence
        if not output_runtime_evidence_is_strong(item)
        and runtime_evidence_mentions_outputs(
            item,
            requested_symbols=requested_symbols,
            requested_addresses=requested_addresses,
        )
    ]
    observed_symbols = unique_list(
        symbol
        for item in strong_evidence
        for symbol in scalar_string_items(item.get("symbols"))
    )
    observed_addresses = unique_addresses(
        address
        for item in strong_evidence
        for address in scalar_string_items(item.get("addresses"))
    )
    observed_runtime_symbols = unique_list(
        symbol
        for item in strong_evidence
        for symbol in runtime_evidence_observed_runtime_symbols(item)
    )
    missing_runtime_symbol_groups = [
        group
        for group in required_runtime_symbol_groups
        if not any(symbol in observed_runtime_symbols for symbol in group)
    ]
    covered_symbols = [symbol for symbol in requested_symbols if symbol in observed_symbols]
    covered_addresses = [address for address in requested_addresses if normalized_address(address) in {normalized_address(item) for item in observed_addresses}]
    non_snapshot_symbols = unique_list(
        symbol
        for item in non_snapshot_evidence
        for symbol in scalar_string_items(item.get("symbols"))
    )
    non_snapshot_addresses = unique_addresses(
        address
        for item in non_snapshot_evidence
        for address in scalar_string_items(item.get("addresses"))
    )
    non_snapshot_covered_symbols = [symbol for symbol in requested_symbols if symbol in non_snapshot_symbols]
    non_snapshot_covered_addresses = [
        address
        for address in requested_addresses
        if normalized_address(address) in {normalized_address(item) for item in non_snapshot_addresses}
    ]
    attempted_symbols, attempted_addresses = content_output_attempted_sinks(
        requested_symbols=requested_symbols,
        requested_addresses=requested_addresses,
        runtime_attempts=runtime_attempts,
    )
    output_count = len(requested_symbols) + len(requested_addresses)
    covered_count = len(covered_symbols) + len(covered_addresses)
    non_snapshot_covered_count = len(non_snapshot_covered_symbols) + len(non_snapshot_covered_addresses)
    attempted_count = len(attempted_symbols) + len(attempted_addresses)
    hardware_summary = runtime_snapshot_hardware_summary(strong_evidence, enabled=True)
    snapshot_runtime_required = bool(
        hardware_summary
        and hardware_summary.get("hardware_behavior_proven") is False
        and covered_count == output_count
        and non_snapshot_covered_count < output_count
    )
    if output_count and covered_count == output_count and not missing_runtime_symbol_groups:
        status = "passed"
        proof_status = "runtime_observed" if snapshot_runtime_required else "mirror_passed"
        mirror_status = "passed"
        actual_proof_status = "runtime_observed" if snapshot_runtime_required else "observed"
    elif covered_count:
        status = "partial"
        proof_status = "instruction_observed"
        mirror_status = "inconclusive"
        actual_proof_status = "instruction_observed"
    elif output_count and attempted_count == output_count:
        status = "failed"
        proof_status = "mirror_failed"
        mirror_status = "failed"
        actual_proof_status = "runtime_observed"
    else:
        status = "planned"
        proof_status = "planned_only"
        mirror_status = "inconclusive" if attempted_count else "not_run"
        actual_proof_status = "runtime_observed" if attempted_count else "planned_only"
    return {
        "status": status,
        "proof_status": proof_status,
        "mirror_status": mirror_status,
        "actual_proof_status": actual_proof_status,
        "output_count": output_count,
        "covered_count": covered_count,
        "attempted_count": attempted_count,
        "covered_symbols": covered_symbols,
        "covered_addresses": covered_addresses,
        "non_snapshot_covered_symbols": non_snapshot_covered_symbols,
        "non_snapshot_covered_addresses": non_snapshot_covered_addresses,
        "attempted_symbols": attempted_symbols,
        "attempted_addresses": attempted_addresses,
        "required_runtime_symbol_groups": required_runtime_symbol_groups,
        "observed_runtime_symbols": observed_runtime_symbols,
        "missing_runtime_symbol_groups": missing_runtime_symbol_groups,
        "runtime_reports": unique_list(item["source"] for item in strong_evidence if item.get("source")),
        "runtime_kinds": unique_list(item["kind"] for item in strong_evidence if item.get("kind")),
        "runtime_attempt_reports": unique_list(str(item.get("source", "")) for item in runtime_attempts if item.get("source")),
        "runtime_attempt_kinds": unique_list(str(item.get("runtime_kind", "")) for item in runtime_attempts if item.get("runtime_kind")),
        "weak_runtime_reports": unique_list(item["source"] for item in weak_evidence if item.get("source")),
        "weak_runtime_kinds": unique_list(item["kind"] for item in weak_evidence if item.get("kind")),
        **hardware_summary,
        "evidence": unique_list(
            [
                *[f"symbol_observed={symbol}" for symbol in covered_symbols],
                *[f"address_observed={address}" for address in covered_addresses],
                *[f"runtime_symbol_observed={symbol}" for symbol in observed_runtime_symbols if any(symbol in group for group in required_runtime_symbol_groups)],
                *[f"required_runtime_symbol_group={'/'.join(group)}" for group in required_runtime_symbol_groups],
                *(runtime_snapshot_hardware_evidence(hardware_summary) if hardware_summary else []),
                *[f"symbol_attempted={symbol}" for symbol in attempted_symbols],
                *[f"address_attempted={address}" for address in attempted_addresses],
            ]
        ),
        "runtime_evidence_gaps": content_output_runtime_evidence_gaps(
            weak_evidence=weak_evidence,
            requested_symbols=requested_symbols,
            requested_addresses=requested_addresses,
            covered_symbols=covered_symbols,
            covered_addresses=covered_addresses,
            attempted_symbols=attempted_symbols,
            attempted_addresses=attempted_addresses,
            missing_runtime_symbol_groups=missing_runtime_symbol_groups,
        )
        + scalar_string_items(hardware_summary.get("runtime_evidence_gaps")),
    }


def runtime_evidence_observed_runtime_symbols(item: dict[str, Any]) -> list[str]:
    if "observed_runtime_symbols" in item:
        return scalar_string_items(item.get("observed_runtime_symbols"))
    return scalar_string_items(item.get("symbols"))


def content_output_attempted_sinks(
    *,
    requested_symbols: list[str],
    requested_addresses: list[str],
    runtime_attempts: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    attempted_symbols = unique_list(
        sink
        for attempt in runtime_attempts
        for sink in scalar_string_items(attempt.get("attempted_sinks"))
        if sink in requested_symbols
    )
    attempted_address_keys = {
        normalized_address(sink)
        for attempt in runtime_attempts
        for sink in scalar_string_items(attempt.get("attempted_sinks"))
        if looks_like_address(str(sink))
    }
    attempted_addresses = [
        address
        for address in requested_addresses
        if normalized_address(address) in attempted_address_keys
    ]
    return attempted_symbols, attempted_addresses


def content_output_runtime_evidence_gaps(
    *,
    weak_evidence: list[dict[str, Any]],
    requested_symbols: list[str],
    requested_addresses: list[str],
    covered_symbols: list[str],
    covered_addresses: list[str],
    attempted_symbols: list[str],
    attempted_addresses: list[str],
    missing_runtime_symbol_groups: list[list[str]],
) -> list[str]:
    gaps = weak_runtime_evidence_gaps(weak_evidence)
    missing_symbols = [symbol for symbol in requested_symbols if symbol not in covered_symbols]
    missing_addresses = [
        address
        for address in requested_addresses
        if normalized_address(address) not in {normalized_address(item) for item in covered_addresses}
    ]
    attempted_missing_symbols = [symbol for symbol in missing_symbols if symbol in attempted_symbols]
    attempted_missing_addresses = [
        address
        for address in missing_addresses
        if normalized_address(address) in {normalized_address(item) for item in attempted_addresses}
    ]
    if attempted_missing_symbols:
        gaps.append(
            "Runtime attempted output symbol(s) but observed no requested output change: "
            + ", ".join(attempted_missing_symbols)
        )
    if attempted_missing_addresses:
        gaps.append(
            "Runtime attempted output address(es) but observed no requested output change: "
            + ", ".join(attempted_missing_addresses)
        )
    if missing_symbols and attempted_symbols and len(attempted_symbols) < len(requested_symbols):
        gaps.append("Runtime attempts did not cover output symbol(s): " + ", ".join(missing_symbols))
    if missing_addresses and attempted_addresses and len(attempted_addresses) < len(requested_addresses):
        gaps.append("Runtime attempts did not cover output address(es): " + ", ".join(missing_addresses))
    if missing_runtime_symbol_groups:
        gaps.append(
            "Runtime observations missing required output helper symbol group(s): "
            + "; ".join("/".join(group) for group in missing_runtime_symbol_groups)
        )
    return unique_list(gaps)


def content_output_mirror_confidence(mirror_status: dict[str, Any]) -> str:
    status = str(mirror_status.get("status", "planned"))
    if status == "passed":
        if mirror_status.get("hardware_behavior_proven") is False:
            return "high for emulator-observed output sink coverage; hardware PPU/APU behavior remains unproven"
        return "high for output sink write coverage in supplied runtime evidence; semantic correctness still depends on the requested expectation"
    if status == "failed":
        return "high for the attempted runtime route not observing requested output sink changes; semantic root cause still needs localization"
    if status == "partial":
        return "medium for observed output sinks; incomplete until every requested output sink has runtime evidence"
    return "medium-high for selected output sinks; final confidence requires a runtime state or executed trace that reaches the drawing/audio/loader helper"


def output_runtime_evidence_is_strong(item: dict[str, Any]) -> bool:
    kind = str(item.get("kind", ""))
    if kind not in OUTPUT_RUNTIME_EVIDENCE_KINDS:
        return False
    proof_status = str(item.get("proof_status") or "")
    return bool(proof_status) and proof_status in OUTPUT_RUNTIME_STRONG_PROOF_STATUSES


def runtime_evidence_mentions_outputs(
    item: dict[str, Any],
    *,
    requested_symbols: list[str],
    requested_addresses: list[str],
) -> bool:
    item_symbols = set(scalar_string_items(item.get("symbols")))
    if item_symbols.intersection(requested_symbols):
        return True
    requested_address_keys = {normalized_address(address) for address in requested_addresses}
    item_address_keys = {normalized_address(address) for address in scalar_string_items(item.get("addresses"))}
    return bool(requested_address_keys.intersection(item_address_keys))


def weak_runtime_evidence_gaps(weak_evidence: list[dict[str, Any]]) -> list[str]:
    gaps = []
    for item in weak_evidence:
        kind = str(item.get("kind") or "unknown")
        source = str(item.get("source") or "<unknown>")
        proof_status = str(item.get("proof_status") or "unspecified")
        if kind not in OUTPUT_RUNTIME_EVIDENCE_KINDS:
            gaps.append(
                f"Ignored {kind} evidence from {source} for output-sink mirror coverage; it is not runtime output evidence."
            )
            continue
        reason = str(item.get("proof_downgrade_reason") or "")
        if reason:
            gaps.append(
                f"Ignored {kind} evidence from {source} for output-sink mirror coverage because proof_status={proof_status}: {reason}."
            )
            continue
        gaps.append(
            f"Ignored {kind} evidence from {source} for output-sink mirror coverage because proof_status={proof_status}."
        )
    return unique_list(gaps)


def runtime_mirror_evidence(loaded: dict[str, Any]) -> list[dict[str, Any]]:
    data = loaded.get("data")
    source = str(loaded.get("source", ""))
    if not isinstance(data, dict) or not source:
        return []
    if data.get("valid", True) is False:
        return []
    kind = str(data.get("kind", ""))
    if kind == "unified_debugger_watch_report":
        events = dict_items(data.get("events"))
        if not events:
            return []
        return [
            runtime_evidence_record(
                source=source,
                kind="watch",
                symbols=[
                    symbol
                    for event in events
                    for symbol in (str(event.get("watch", "")), str(event.get("pc_label", "")))
                    if symbol and not looks_like_address(symbol)
                ],
                addresses=[address for event in events for address in event_addresses(event)],
                commands=report_commands(data),
                proof_status="runtime_observed",
            )
        ]
    if kind == "unified_debugger_replay_plan":
        watch_report = data.get("watch_report") if isinstance(data.get("watch_report"), dict) else {}
        nested = runtime_mirror_evidence({"source": source, "data": watch_report}) if watch_report else []
        for item in nested:
            item["kind"] = "replay_watch"
            item["commands"] = unique_list([*scalar_string_items(item.get("commands")), *report_commands(data)])
        return nested
    if kind == "unified_debugger_instruction_trace":
        validation = data.get("execution_validation") if isinstance(data.get("execution_validation"), dict) else {}
        hit = bool(validation.get("hit") or validation.get("ready_for_dynamic_taint"))
        if not data.get("executed") and not hit:
            return []
        hit_function_symbols = scalar_string_items(validation.get("hit_function_symbols"))
        watch_symbols = scalar_string_items(validation.get("watch_symbols"))
        planned_function_symbols = unique_list(
            str(function.get("symbol", ""))
            for function in dict_items(data.get("functions"))
            if function.get("symbol")
        )
        symbols = unique_list(
            [
                *hit_function_symbols,
                *watch_symbols,
            ]
        )
        return [
            runtime_evidence_record(
                source=source,
                kind="instruction_trace",
                symbols=symbols,
                observed_runtime_symbols=hit_function_symbols,
                planned_function_symbols=planned_function_symbols,
                target_symbols=unique_list([*symbols, *planned_function_symbols]),
                addresses=scalar_string_items(validation.get("watch_addresses")) + scalar_string_items(data.get("watch_addresses")),
                source_files=[
                    str(function.get("source_file", ""))
                    for function in dict_items(data.get("functions"))
                    if function.get("source_file")
                ],
                commands=report_commands(data),
                proof_status="instruction_observed",
            )
        ]
    if kind == "unified_debugger_dynamic_taint_report":
        attributions = dict_items(data.get("write_attributions"))
        paths = dict_items(data.get("paths"))
        if not attributions and not paths:
            return []
        return [
            runtime_evidence_record(
                source=source,
                kind="dynamic_taint",
                symbols=[
                    *scalar_string_items(item.get("related_symbols")),
                    *(
                        []
                        if looks_like_address(str(item.get("sink", "")))
                        else [str(item.get("sink", ""))]
                    ),
                    str(item.get("sink_symbol", "")),
                ],
                addresses=[
                    address
                    for address in [
                        *event_addresses(item),
                        *scalar_string_items(item.get("related_addresses")),
                        str(item.get("sink", "")) if looks_like_address(str(item.get("sink", ""))) else "",
                        str(item.get("sink_address", "")),
                    ]
                    if address
                ],
                source_files=[
                    path
                    for path in scalar_string_items(item.get("related_files"))
                ],
                commands=report_commands(data),
                proof_status=runtime_item_proof_status(item),
            )
            for item in [*attributions, *paths]
        ]
    if kind == "unified_debugger_effect_trace":
        write_index = [
            item
            for item in dict_items(data.get("write_index"))
            if int(item.get("write_count", 0) or 0) > 0
        ]
        events = dict_items(data.get("events"))
        concrete_writes = effect_trace_concrete_writes(events)
        strong_concrete_writes = [
            item for item in concrete_writes if effect_trace_concrete_write_is_strong(item)
        ]
        weak_concrete_writes = [
            item for item in concrete_writes if not effect_trace_concrete_write_is_strong(item)
        ]
        strong_watch_hits = effect_trace_watch_hits(events, proof_status="instruction_observed")
        weak_watch_hits = effect_trace_watch_hits(events, proof_status="planned_only")
        compact_only_write_index = write_index if not concrete_writes else []
        records: list[dict[str, Any]] = []
        if not write_index and not concrete_writes and not weak_watch_hits:
            return []
        watch_sinks = split_symbol_address_values(data.get("watch_symbols"))
        watch_addresses = unique_addresses(
            [
                *watch_sinks["addresses"],
                *scalar_string_items(data.get("watch_addresses")),
                *[
                    str(watch.get("name") or watch.get("address") or "")
                    for watch in dict_items(data.get("watches"))
                    if not watch.get("symbol")
                ],
            ]
        )
        if strong_concrete_writes or strong_watch_hits:
            records.append(
                runtime_evidence_record(
                    source=source,
                    kind="effect_trace",
                    symbols=[
                        *effect_trace_strong_event_labels(events),
                        *[
                            str(hit.get("watch", ""))
                            for hit in strong_watch_hits
                            if hit.get("watch") and not looks_like_address(str(hit.get("watch", "")))
                        ],
                        *[
                            str(watch.get("symbol") or watch.get("name") or "")
                            for watch in dict_items(data.get("watches"))
                            if watch.get("symbol")
                            and any(str(hit.get("watch", "")) == str(watch.get("symbol") or watch.get("name") or "") for hit in strong_watch_hits)
                        ],
                    ],
                    addresses=[
                        *[str(hit.get("address", "")) for hit in strong_watch_hits if hit.get("address")],
                        *[str(item.get("address_hex", "")) for item in strong_concrete_writes if item.get("address_hex")],
                    ],
                    commands=report_commands(data),
                    proof_status="instruction_observed",
                )
            )
        if compact_only_write_index or weak_watch_hits or weak_concrete_writes:
            records.append(
                runtime_evidence_record(
                    source=source,
                    kind="effect_trace",
                    symbols=[
                        *watch_sinks["symbols"],
                        *[
                            str(hit.get("watch", ""))
                            for hit in weak_watch_hits
                            if hit.get("watch") and not looks_like_address(str(hit.get("watch", "")))
                        ],
                    ],
                    addresses=[
                        *watch_addresses,
                        *[str(item.get("address", "")) for item in compact_only_write_index],
                        *[str(hit.get("address", "")) for hit in weak_watch_hits if hit.get("address")],
                        *[str(item.get("address_hex", "")) for item in weak_concrete_writes if item.get("address_hex")],
                    ],
                    commands=report_commands(data),
                    proof_status="planned_only",
                    proof_downgrade_reason=effect_trace_weak_output_reason(
                        has_events=bool(events),
                        weak_watch_hits=weak_watch_hits,
                        weak_concrete_writes=weak_concrete_writes,
                    ),
                )
            )
        return records
    if kind == "unified_debugger_visual_snapshot":
        proof_status = runtime_snapshot_proof_status(data)
        if not proof_status or not visual_snapshot_has_runtime_samples(data):
            return []
        surfaces = dict_items(data.get("surfaces"))
        screen_frame = data.get("screen_frame") if isinstance(data.get("screen_frame"), dict) else {}
        hardware_behavior_proven = data.get("hardware_behavior_proven") is True
        return [
            runtime_evidence_record(
                source=source,
                kind="visual_snapshot",
                symbols=[str(surface.get("name", "")) for surface in surfaces if surface.get("name")],
                addresses=[str(surface.get("address", "")) for surface in surfaces if surface.get("address")],
                commands=report_commands(data),
                artifacts=[str(screen_frame.get("framebuffer") or data.get("framebuffer") or "")],
                proof_status=proof_status,
                proof_downgrade_reason=str(data.get("proof_downgrade_reason") or "")
                or ("" if hardware_behavior_proven else SNAPSHOT_HARDWARE_DOWNGRADE_REASON),
                evidence_class=str(data.get("evidence_class") or "pyboy_visual_snapshot"),
                hardware_behavior_proven=hardware_behavior_proven,
                hardware_proof_status=str(
                    data.get("hardware_proof_status")
                    or ("proven" if hardware_behavior_proven else "not_proven")
                ),
                hardware_proof_boundary=str(
                    data.get("hardware_proof_boundary")
                    or "PyBoy framebuffer digest is emulator-observed output, not proof of hardware PPU behavior."
                ),
            )
        ]
    if kind == "unified_debugger_audio_snapshot":
        proof_status = runtime_snapshot_proof_status(data)
        if not proof_status or not audio_snapshot_has_runtime_samples(data):
            return []
        register_details = dict_items(data.get("register_details"))
        symbol_state = dict_items(data.get("symbol_state"))
        wave_ram = data.get("wave_ram") if isinstance(data.get("wave_ram"), dict) else {}
        sound_buffer = data.get("sound_buffer") if isinstance(data.get("sound_buffer"), dict) else {}
        hardware_behavior_proven = data.get("hardware_behavior_proven") is True
        return [
            runtime_evidence_record(
                source=source,
                kind="audio_snapshot",
                symbols=[
                    *[str(register.get("name", "")) for register in register_details if register.get("name")],
                    *[str(item.get("symbol", "")) for item in symbol_state if item.get("symbol")],
                    str(sound_buffer.get("source", "")) if sound_buffer.get("source") else "",
                ],
                addresses=[
                    *[str(register.get("address", "")) for register in register_details if register.get("address")],
                    *[str(item.get("address", "")) for item in symbol_state if item.get("address")],
                    str(wave_ram.get("address", "")) if wave_ram.get("address") else "",
                ],
                commands=report_commands(data),
                artifacts=[
                    str(wave_ram.get("sha256", "")) if wave_ram.get("sha256") else "",
                    str(sound_buffer.get("source", "")) if sound_buffer.get("source") else "",
                    str(sound_buffer.get("sha256", "")) if sound_buffer.get("sha256") else "",
                    str(sound_buffer.get("buffer", "")) if sound_buffer.get("buffer") else "",
                ],
                proof_status=proof_status,
                proof_downgrade_reason=str(data.get("proof_downgrade_reason") or "")
                or ("" if hardware_behavior_proven else SNAPSHOT_HARDWARE_DOWNGRADE_REASON),
                evidence_class=str(data.get("evidence_class") or "pyboy_audio_snapshot"),
                hardware_behavior_proven=hardware_behavior_proven,
                hardware_proof_status=str(
                    data.get("hardware_proof_status")
                    or ("proven" if hardware_behavior_proven else "not_proven")
                ),
                hardware_proof_boundary=str(
                    data.get("hardware_proof_boundary")
                    or "PyBoy audio snapshot is emulator-observed output, not proof of hardware APU behavior."
                ),
            )
        ]
    if kind == "unified_debugger_content_state_materialization":
        execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
        if not data.get("executed") and not execution.get("executed"):
            return []
        patches = [
            patch
            for materialization in dict_items(data.get("materializations"))
            for patch in dict_items(materialization.get("patches"))
        ]
        return [
            runtime_evidence_record(
                source=source,
                kind="content_state",
                symbols=[
                    *[str(patch.get("symbol", "")) for patch in patches if patch.get("symbol")],
                    *[
                        str(output.get("state_symbol", ""))
                        for materialization in dict_items(data.get("materializations"))
                        for output in dict_items(materialization.get("outputs"))
                        if output.get("state_symbol")
                    ],
                ],
                addresses=[str(patch.get("bank_address", "")) for patch in patches if patch.get("bank_address")],
                source_files=[
                    str(materialization.get("source_file", ""))
                    for materialization in dict_items(data.get("materializations"))
                    if materialization.get("source_file")
                ],
                commands=report_commands(data),
                proof_status="state_materialized",
            )
        ]
    return []


def runtime_snapshot_proof_status(data: dict[str, Any]) -> str:
    if data.get("valid", True) is False or not data.get("executed"):
        return ""
    proof_status = str(data.get("proof_status") or "")
    return proof_status if proof_status in OUTPUT_RUNTIME_STRONG_PROOF_STATUSES else ""


def visual_snapshot_has_runtime_samples(data: dict[str, Any]) -> bool:
    if dict_items(data.get("surfaces")):
        return True
    screen_frame = data.get("screen_frame") if isinstance(data.get("screen_frame"), dict) else {}
    return bool(screen_frame.get("framebuffer") or screen_frame.get("sha256") or data.get("framebuffer"))


def audio_snapshot_has_runtime_samples(data: dict[str, Any]) -> bool:
    registers = data.get("registers") if isinstance(data.get("registers"), dict) else {}
    audio_state = data.get("audio_state") if isinstance(data.get("audio_state"), dict) else {}
    wave_ram = data.get("wave_ram") if isinstance(data.get("wave_ram"), dict) else {}
    sound_buffer = data.get("sound_buffer") if isinstance(data.get("sound_buffer"), dict) else {}
    return bool(
        registers
        or dict_items(data.get("register_details"))
        or dict_items(data.get("symbol_state"))
        or audio_state
        or wave_ram.get("sha256")
        or wave_ram.get("sample_hex")
        or sound_buffer.get("sha256")
        or sound_buffer.get("sample_hex")
        or sound_buffer.get("buffer")
    )


def runtime_evidence_record(
    *,
    source: str,
    kind: str,
    symbols: list[str] | None = None,
    addresses: list[str] | None = None,
    observed_runtime_symbols: list[str] | None = None,
    planned_function_symbols: list[str] | None = None,
    target_symbols: list[str] | None = None,
    source_files: list[str] | None = None,
    artifacts: list[str] | None = None,
    commands: list[str] | None = None,
    proof_status: str = "",
    proof_downgrade_reason: str = "",
    evidence_class: str = "",
    hardware_behavior_proven: bool | None = None,
    hardware_proof_status: str = "",
    hardware_proof_boundary: str = "",
) -> dict[str, Any]:
    record = {
        "source": source,
        "kind": kind,
        "symbols": unique_list(symbols or []),
        "addresses": unique_list(addresses or []),
        "source_files": unique_list(normalize_path(path) for path in source_files or [] if path),
        "artifacts": unique_list(artifacts or []),
        "commands": unique_list(commands or []),
    }
    if observed_runtime_symbols is not None:
        record["observed_runtime_symbols"] = unique_list(observed_runtime_symbols)
    if planned_function_symbols is not None:
        record["planned_function_symbols"] = unique_list(planned_function_symbols)
    if target_symbols is not None:
        record["target_symbols"] = unique_list(target_symbols)
    if proof_status:
        record["proof_status"] = proof_status
    if proof_downgrade_reason:
        record["proof_downgrade_reason"] = proof_downgrade_reason
    if evidence_class:
        record["evidence_class"] = evidence_class
    if hardware_behavior_proven is not None:
        record["hardware_behavior_proven"] = hardware_behavior_proven
    if hardware_proof_status:
        record["hardware_proof_status"] = hardware_proof_status
    if hardware_proof_boundary:
        record["hardware_proof_boundary"] = hardware_proof_boundary
    return record


def runtime_item_proof_status(item: dict[str, Any]) -> str:
    return str(item.get("proof_status") or item.get("match_proof_status") or "planned_only")


def effect_trace_concrete_writes(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item
        for event in events
        for item in dict_items(event.get("effects"))
        if item.get("access") == "write" and item.get("address_hex")
    ]


def effect_trace_concrete_write_is_strong(item: dict[str, Any]) -> bool:
    if item.get("hardware_event_required") and not item.get("hardware_runtime_event"):
        return False
    proof_status = str(item.get("proof_status") or "")
    if proof_status:
        return proof_status in OUTPUT_RUNTIME_STRONG_PROOF_STATUSES
    return True


def effect_trace_strong_event_labels(events: list[dict[str, Any]]) -> list[str]:
    return unique_list(
        str(event.get("pc_label", ""))
        for event in events
        if event.get("pc_label")
        and (
            any(effect_trace_concrete_write_is_strong(item) for item in dict_items(event.get("effects")))
            or effect_trace_watch_hits([event], proof_status="instruction_observed")
        )
    )


def effect_trace_watch_hits(events: list[dict[str, Any]], *, proof_status: str) -> list[dict[str, Any]]:
    return [
        hit
        for event in events
        for hit in dict_items(event.get("watch_hits"))
        if hit.get("access") == "write"
        and str(hit.get("target_match_proof_status") or hit.get("proof_status") or "") == proof_status
    ]


def effect_trace_weak_output_reason(
    *,
    has_events: bool,
    weak_watch_hits: list[dict[str, Any]],
    weak_concrete_writes: list[dict[str, Any]] | None = None,
) -> str:
    if weak_concrete_writes:
        return "effect-trace concrete write proof is hardware-gated or otherwise not instruction-observed; output behavior was not proven"
    if weak_watch_hits:
        return "effect-trace watch hit target match is bank-unverified; concrete output behavior was not proven"
    if not has_events:
        return "compact effect-trace write_index has no concrete effect events; output behavior was not proven"
    return "effect-trace output evidence did not include a strong concrete write match"


def report_commands(data: dict[str, Any]) -> list[str]:
    commands = scalar_string_items(data.get("commands"))
    commands.extend(scalar_string_items(data.get("runnable_commands")))
    commands.extend(scalar_string_items(data.get("materialization_commands")))
    return unique_list(commands)


def event_addresses(event: dict[str, Any]) -> list[str]:
    return unique_list(
        str(value)
        for value in (
            event.get("bank_address"),
            event.get("address"),
            event.get("sink_address"),
            event.get("target") if looks_like_address(str(event.get("target", ""))) else "",
        )
        if value
    )


def watch_attempt_sinks(data: dict[str, Any]) -> list[str]:
    events = dict_items(data.get("events"))
    watches = dict_items(data.get("watches"))
    return unique_list(
        [
            *scalar_string_items(data.get("watch_symbols")),
            *scalar_string_items(data.get("watch_addresses")),
            *scalar_string_items(data.get("effective_watch_symbols")),
            *scalar_string_items(data.get("effective_watch_addresses")),
            *[
                str(watch.get("symbol") or watch.get("name") or watch.get("address") or "")
                for watch in watches
            ],
            *[
                str(event.get("watch", ""))
                for event in events
                if event.get("watch")
            ],
            *[
                address
                for event in events
                for address in event_addresses(event)
            ],
        ]
    )


def is_content_fuzz_case(case: dict[str, Any]) -> bool:
    if not case.get("scenario_id"):
        return False
    if case.get("state_preconditions"):
        return True
    runtime_targets = case.get("runtime_targets") if isinstance(case.get("runtime_targets"), dict) else {}
    return bool(runtime_targets or case.get("scenario_type") or case.get("runtime_route"))


def content_case_runtime_route(case: dict[str, Any]) -> str:
    runtime_targets = case.get("runtime_targets") if isinstance(case.get("runtime_targets"), dict) else {}
    return str(runtime_targets.get("runtime_route") or case.get("runtime_route") or "")


def content_fuzz_case_symbols(case: dict[str, Any]) -> list[str]:
    runtime_targets = case.get("runtime_targets") if isinstance(case.get("runtime_targets"), dict) else {}
    out = [
        *string_items(case.get("symbols")),
        *string_items(case.get("related_symbols")),
        *string_items(case.get("required_runtime_symbols")),
    ]
    for key in ("source_symbols", "script_symbols", "trace_symbols", "watch_symbols", "required_runtime_symbols"):
        out.extend(string_items(runtime_targets.get(key)))
    for precondition in dict_items(case.get("state_preconditions")):
        out.extend(string_items(precondition.get("watch_symbols")))
        out.extend(string_items(precondition.get("required_runtime_symbols")))
        for route in event_runtime_routes_for_row(precondition):
            out.extend(string_items(route.get("required_runtime_symbols")))
    for output in dict_items(case.get("outputs")):
        out.extend(string_items(output.get("state_symbol")))
        out.extend(string_items(output.get("producer_symbol")))
    return unique_list(out)


def content_fuzz_required_runtime_symbols(cases: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for case in cases:
        runtime_targets = case.get("runtime_targets") if isinstance(case.get("runtime_targets"), dict) else {}
        out.extend(string_items(case.get("required_runtime_symbols")))
        out.extend(string_items(runtime_targets.get("required_runtime_symbols")))
        for precondition in dict_items(case.get("state_preconditions")):
            out.extend(string_items(precondition.get("required_runtime_symbols")))
            for route in event_runtime_routes_for_row(precondition):
                out.extend(string_items(route.get("required_runtime_symbols")))
    return unique_list(out)


def event_runtime_routes_for_row(row: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        route
        for route in (
            row.get(EVENT_RUNTIME_ROUTE_KEY),
            row.get(EVENT_RUNTIME_ROUTE_LEGACY_KEY),
        )
        if isinstance(route, dict)
    ]


def content_fuzz_expected_sinks(cases: list[dict[str, Any]]) -> list[str]:
    return unique_list(
        sink
        for case in cases
        for sink in [
            *content_fuzz_case_watch_sinks(case),
            *[
                str(output.get("state_symbol") or output.get("output_symbol") or output.get("address") or output.get("watch_address") or output.get("sink_address") or "")
                for output in dict_items(case.get("outputs"))
            ],
        ]
        if sink
    )


def content_fuzz_case_watch_sinks(case: dict[str, Any]) -> list[str]:
    runtime_targets = case.get("runtime_targets") if isinstance(case.get("runtime_targets"), dict) else {}
    return unique_list(
        [
            *string_items(runtime_targets.get("watch_symbols")),
            *string_items(runtime_targets.get("watch_addresses")),
            *[
                symbol
                for precondition in dict_items(case.get("state_preconditions"))
                for symbol in string_items(precondition.get("watch_symbols"))
            ],
        ]
    )


def content_fuzz_expect_commands(*, source: str, cases: list[dict[str, Any]]) -> list[str]:
    commands = []
    for case in cases[:6]:
        scenario_id = str(case.get("scenario_id", ""))
        if not scenario_id:
            continue
        commands.append(f"python -m tools.debugger expect --report {source} --expect scenario={scenario_id}")
        for precondition in dict_items(case.get("state_preconditions"))[:3]:
            kind = str(precondition.get("kind", ""))
            if not kind:
                continue
            watch_symbols = unique_list(string_items(precondition.get("watch_symbols")))
            if not watch_symbols:
                commands.append(
                    f"python -m tools.debugger expect --report {source} --expect precondition={kind},scenario={scenario_id}"
                )
                continue
            for symbol in watch_symbols[:3]:
                commands.append(
                    f"python -m tools.debugger expect --report {source} --expect precondition={kind},scenario={scenario_id},symbol={symbol}"
                )
    return commands


def content_fuzz_materialization_commands(case: dict[str, Any]) -> list[str]:
    commands = []
    request = case.get("materialization_request") if isinstance(case.get("materialization_request"), dict) else {}
    commands.extend(string_items(request.get("commands")))
    commands.extend(string_items(case.get("commands")))
    for probe in dict_items(case.get("behavioral_probes")):
        command = str(probe.get("command", ""))
        if command:
            commands.append(command)
    return commands


def content_state_expect_commands(*, source: str, materialization: dict[str, Any]) -> list[str]:
    scenario_id = str(materialization.get("scenario_id", ""))
    commands = []
    for patch in dict_items(materialization.get("patches"))[:6]:
        symbol = str(patch.get("symbol", ""))
        if not symbol:
            continue
        value_hex = str(patch.get("value_hex") or "")
        value = str(patch.get("value") or "")
        value_arg = f",value=0x{value_hex}" if value_hex else (f",value={value}" if value else "")
        scenario_arg = f",scenario={scenario_id}" if scenario_id else ""
        commands.append(
            f"python -m tools.debugger expect --report {source} --expect state-patch={symbol}{scenario_arg}{value_arg}"
        )
    return commands


def content_state_watch_commands(*, out_state: str, patch_symbols: list[str]) -> list[str]:
    if not out_state:
        return []
    return [
        "python -m tools.debugger watch "
        + " ".join(f"--watch-symbol {symbol}" for symbol in patch_symbols[:6])
        + f" --save-state {out_state} --execute"
    ]


def content_output_expect_commands(*, source: str, materializations: list[dict[str, Any]]) -> list[str]:
    commands = []
    for materialization in materializations:
        scenario_id = str(materialization.get("scenario_id", ""))
        kind = str(materialization.get("precondition_kind") or materialization.get("kind") or "output_sink")
        scenario_arg = f",scenario={scenario_id}" if scenario_id else ""
        output_symbols = unique_list(
            str(output.get("state_symbol") or output.get("output_symbol") or "")
            for output in dict_items(materialization.get("outputs"))
            if output.get("state_symbol") or output.get("output_symbol")
        )
        output_addresses = unique_addresses(
            str(output.get("address") or output.get("watch_address") or output.get("sink_address") or "")
            for output in dict_items(materialization.get("outputs"))
            if output.get("address") or output.get("watch_address") or output.get("sink_address")
        )
        if not output_symbols and not output_addresses:
            commands.append(
                f"python -m tools.debugger expect --report {source} --expect precondition={kind}{scenario_arg}"
            )
            continue
        for symbol in output_symbols[:3]:
            commands.append(
                f"python -m tools.debugger expect --report {source} --expect precondition={kind}{scenario_arg},symbol={symbol}"
            )
        for address in output_addresses[:3]:
            commands.append(
                f"python -m tools.debugger expect --report {source} --expect precondition={kind}{scenario_arg},address={command_address_arg(address)}"
            )
    return unique_list(commands)


def content_state_output_symbols(materializations: list[dict[str, Any]]) -> list[str]:
    return unique_list(
        str(output.get("state_symbol") or output.get("output_symbol") or "")
        for materialization in materializations
        for output in dict_items(materialization.get("outputs"))
        if output.get("state_symbol") or output.get("output_symbol")
    )


def content_state_output_addresses(materializations: list[dict[str, Any]]) -> list[str]:
    return unique_list(
        str(output.get("address") or output.get("watch_address") or output.get("sink_address") or "")
        for materialization in materializations
        for output in dict_items(materialization.get("outputs"))
        if output.get("address") or output.get("watch_address") or output.get("sink_address")
    )


def content_state_output_required_runtime_symbol_groups(materializations: list[dict[str, Any]]) -> list[list[str]]:
    groups: list[list[str]] = []
    for materialization in materializations:
        raw_groups = materialization.get("required_runtime_symbol_groups")
        if isinstance(raw_groups, list):
            for group in raw_groups:
                symbols = scalar_string_items(group)
                if symbols:
                    groups.append(symbols)
        for symbol in scalar_string_items(materialization.get("required_runtime_symbols")):
            groups.append([symbol])
        runtime_symbols = scalar_string_items(materialization.get("runtime_symbols"))
        if runtime_symbols:
            groups.append(runtime_symbols)
    unique_groups: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for group in groups:
        normalized = tuple(unique_list(group))
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique_groups.append(list(normalized))
    return unique_groups


def match_mirrors(
    *,
    changed_files: tuple[str, ...],
    symbols: tuple[str, ...],
    symptom: str,
    root: Path,
) -> list[dict[str, Any]]:
    normalized_paths = tuple(
        normalized_changed_path(path, root=root).lower()
        for path in changed_files
    )
    symptom_text = symptom.lower()
    matches: list[dict[str, Any]] = []
    for rule in MIRROR_RULES:
        path_hit = any(path_matches_prefix(path, rule.path_prefixes) for path in normalized_paths)
        symbol_hit = any(symbol in rule.symbols for symbol in symbols)
        symptom_hit = bool(symptom_text) and any(
            keyword_matches(keyword, symptom_text) for keyword in rule.symptom_keywords
        )
        if not path_hit and not symbol_hit and not symptom_hit:
            continue
        matches.append(
            {
                "id": rule.id,
                "title": rule.title,
                "scope": rule.scope,
                "confidence": rule.confidence,
                "matched_by": [
                    name
                    for name, hit in (
                        ("changed_file", path_hit),
                        ("symbol", symbol_hit),
                        ("symptom", symptom_hit),
                    )
                    if hit
                ],
                "evidence": list(rule.evidence),
                "commands": list(rule.commands),
                "materialization_commands": list(rule.materialization_commands),
                "gaps": list(rule.gaps),
            }
        )
    return matches


def normalized_changed_path(raw_path: str, *, root: Path) -> str:
    path = Path(raw_path)
    if path.is_absolute():
        try:
            return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")
    return raw_path.replace("\\", "/")


def normalize_path(raw_path: str) -> str:
    return str(raw_path).replace("\\", "/").strip()


def path_matches_prefix(path: str, prefixes: tuple[str, ...]) -> bool:
    for prefix in prefixes:
        normalized_prefix = prefix.lower()
        if path.startswith(normalized_prefix) or f"/{normalized_prefix}" in path:
            return True
    return False


def unique_commands(matches: list[dict[str, Any]], key: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for match in matches:
        for command in match.get(key, []):
            if command in seen:
                continue
            seen.add(command)
            out.append(command)
    return out


def dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, dict)]


def string_items(value: Any) -> list[str]:
    if not isinstance(value, list | tuple):
        return []
    return [str(item) for item in value if item]


def scalar_string_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list | tuple | set):
        return [
            nested
            for item in value
            for nested in scalar_string_items(item)
        ]
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


def safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def unique_addresses(values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    if values is None:
        items: list[Any] | Any = []
    elif isinstance(values, str):
        items = [values]
    else:
        try:
            items = iter(values)
        except TypeError:
            items = [values]
    for value in items:
        for item in scalar_string_items(value):
            text = str(item)
            key = normalized_address(text)
            if not text or key in seen:
                continue
            seen.add(key)
            out.append(text)
    return out


def normalized_address(value: Any) -> str:
    text = str(value).strip()
    if "=" in text:
        text = text.rsplit("=", 1)[1].strip()
    return command_address_arg(text).upper()


def split_symbol_address_values(value: Any) -> dict[str, list[str]]:
    symbols: list[str] = []
    addresses: list[str] = []
    for item in scalar_string_items(value):
        if looks_like_address(item):
            addresses.append(item)
        else:
            symbols.append(item)
    return {
        "symbols": unique_list(symbols),
        "addresses": unique_addresses(addresses),
    }


def looks_like_address(value: str) -> bool:
    text = str(value).strip()
    if "=" in text:
        text = text.rsplit("=", 1)[1].strip()
    if text.startswith("$"):
        text = text[1:]
    if ":" in text:
        bank, address = text.split(":", 1)
        return is_hex(bank, 2) and is_hex(address.lstrip("$"), 4)
    return is_hex(text, 4)


def is_hex(value: str, max_length: int) -> bool:
    text = str(value).strip()
    return bool(text) and len(text) <= max_length and all(char in "0123456789abcdefABCDEF" for char in text)
