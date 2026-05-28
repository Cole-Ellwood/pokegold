from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog import ROOT, keyword_matches, triage_request
from .content_scenarios import (
    PROOF_STATUS_PLANNED_ONLY,
    PROOF_STATUS_READY_TO_RUN,
    PROOF_STATUS_STATE_MATERIALIZED,
)
from .provenance import build_provenance_report
from .reporting import load_reports


MIRROR_STATUS_NOT_RUN = "not_run"
MIRROR_STATUS_PLANNED_ONLY = "planned_only"
MIRROR_STATUS_READY_TO_RUN = "ready_to_run"
MIRROR_STATUS_STATE_MATERIALIZED = "state_materialized"
MIRROR_STATUS_INCONCLUSIVE = "inconclusive"
MIRROR_STATUS_PASSED = "passed"
MIRROR_STATUS_FAILED = "failed"


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
    observations = _collect_runtime_observations(
        loaded_reports=loaded_reports,
        runtime_observations=runtime_observations,
    )
    matches = content_state_mirror_matches(loaded_reports, runtime_observations=observations)
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
    runtime_observations: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    observations_by_scenario = runtime_observations or {}
    matches = []
    for loaded in loaded_reports:
        data = loaded.get("data", {})
        if not isinstance(data, dict):
            continue
        if data.get("kind") != "unified_debugger_content_state_materialization":
            continue
        source = str(loaded.get("source", ""))
        materializations = [
            item
            for item in dict_items(data.get("materializations"))
            if item.get("patches")
        ]
        if not materializations:
            continue
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
        execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
        out_state = str(execution.get("out_state") or data.get("out_state") or "")
        executed = bool(data.get("executed") or execution.get("executed"))
        expected_sinks = _collect_expected_sinks(materializations)
        observed_sinks = _collect_observed_sinks_for_scenarios(
            scenario_ids,
            observations_by_scenario=observations_by_scenario,
        )
        actual_proof_status_floor = _materialization_proof_status_floor(materializations, executed=executed)
        mirror_status = _mirror_status_for(
            expected_sinks=expected_sinks,
            observed_sinks=observed_sinks,
            actual_proof_status=actual_proof_status_floor,
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
        gaps: list[str] = []
        if not executed:
            gaps.append(
                "Content-state patches are planned but no patched save state was executed; run the content-state --execute command before treating this as final emulator behavior."
            )
        runtime_evidence_gaps: list[str] = []
        if mirror_status != MIRROR_STATUS_PASSED:
            missing = sorted(set(expected_sinks) - set(observed_sinks))
            if missing:
                runtime_evidence_gaps.append(
                    "Runtime evidence missing for expected output sinks; supply replay/instruction-trace runtime_observations for "
                    + ", ".join(missing[:6])
                    + " before promoting this behavioral mirror to passed."
                )
            elif not observed_sinks:
                runtime_evidence_gaps.append(
                    "Runtime evidence missing; no observed_sinks were supplied for the content-state scenarios."
                )
        evidence = [
            f"report={source}",
            f"scenarios={len(scenario_ids)}",
            f"patches={sum(len(item.get('patches', [])) for item in materializations)}",
            f"actual_proof_status={actual_proof_status_floor}",
            f"mirror_status={mirror_status}",
        ]
        if out_state:
            evidence.append(f"state={out_state}")
        matches.append(
            {
                "id": "content_state_behavioral_mirror",
                "title": "Content WRAM patch and replay mirror",
                "scope": "Content scenarios with generated map-position, script-entry, or movement-entry WRAM state patches and replay targets.",
                "confidence": "high for selected WRAM map-position/script-entry/movement-entry state; runtime transition confidence requires replay/watch from the patched state",
                "matched_by": ["content_state_report"],
                "evidence": evidence,
                "commands": unique_list(commands),
                "materialization_commands": unique_list(materialization_commands),
                "gaps": gaps,
                "runtime_evidence_gaps": runtime_evidence_gaps,
                "mirror_status": mirror_status,
                "actual_proof_status": actual_proof_status_floor,
                "expected_proof_status": "runtime_observed",
                "expected_sinks": sorted(expected_sinks),
                "observed_sinks": sorted(observed_sinks),
                "scenario_ids": scenario_ids,
            }
        )
    return matches


def _collect_runtime_observations(
    *,
    loaded_reports: list[dict[str, Any]],
    runtime_observations: tuple[dict[str, Any], ...],
) -> dict[str, list[str]]:
    """Aggregate observed sinks per scenario from reports and explicit args.

    Observations may arrive two ways:
      - As an explicit kwarg on build_compare_plan (`runtime_observations`).
      - As a top-level `runtime_observations` list on any loaded report
        (e.g. a replay report or an instruction-trace report can append
        observed sinks per scenario_id).

    Both shapes collapse into the same per-scenario-id dictionary.
    """
    by_scenario: dict[str, set[str]] = {}
    sources: list[Any] = list(runtime_observations)
    for loaded in loaded_reports:
        data = loaded.get("data", {})
        if not isinstance(data, dict):
            continue
        report_observations = data.get("runtime_observations")
        if isinstance(report_observations, list):
            sources.extend(item for item in report_observations if isinstance(item, dict))
    for entry in sources:
        if not isinstance(entry, dict):
            continue
        scenario_id = str(entry.get("scenario_id", ""))
        if not scenario_id:
            continue
        observed = entry.get("observed_sinks") or []
        if not isinstance(observed, list):
            continue
        bucket = by_scenario.setdefault(scenario_id, set())
        for sink in observed:
            bucket.add(str(sink))
    return {scenario_id: sorted(sinks) for scenario_id, sinks in by_scenario.items()}


def _collect_expected_sinks(materializations: list[dict[str, Any]]) -> list[str]:
    """Return the union of expected_sinks across every materialization route."""
    sinks: list[str] = []
    seen: set[str] = set()
    for materialization in materializations:
        route = materialization.get("event_runtime_materialization") if isinstance(materialization, dict) else None
        if isinstance(route, dict):
            for sink in route.get("expected_sinks") or []:
                text = str(sink)
                if text and text not in seen:
                    seen.add(text)
                    sinks.append(text)
            continue
        # Fallback for reports without the explicit route: derive sinks from patch
        # symbols so older content_state JSON still aggregates the right floor.
        for patch in dict_items(materialization.get("patches")):
            base_symbol = str(patch.get("base_symbol") or patch.get("symbol") or "")
            if base_symbol and base_symbol not in seen:
                seen.add(base_symbol)
                sinks.append(base_symbol)
    return sinks


def _collect_observed_sinks_for_scenarios(
    scenario_ids: list[str],
    *,
    observations_by_scenario: dict[str, list[str]],
) -> list[str]:
    if not scenario_ids:
        flat: list[str] = []
        seen: set[str] = set()
        for sinks in observations_by_scenario.values():
            for sink in sinks:
                if sink not in seen:
                    seen.add(sink)
                    flat.append(sink)
        return flat
    seen: set[str] = set()
    out: list[str] = []
    for scenario_id in scenario_ids:
        for sink in observations_by_scenario.get(scenario_id, []):
            if sink not in seen:
                seen.add(sink)
                out.append(sink)
    return out


def _materialization_proof_status_floor(
    materializations: list[dict[str, Any]],
    *,
    executed: bool,
) -> str:
    """Return the lowest actual_proof_status across the materializations.

    The mirror's overall status is gated by the weakest link — any
    planned_only materialization keeps the floor at planned_only.
    """
    if not materializations:
        return PROOF_STATUS_PLANNED_ONLY
    statuses: set[str] = set()
    for materialization in materializations:
        status = str(
            materialization.get("actual_proof_status")
            or _infer_status_from_materialization(materialization, executed=executed)
        )
        statuses.add(status)
    if statuses == {PROOF_STATUS_STATE_MATERIALIZED}:
        return PROOF_STATUS_STATE_MATERIALIZED
    if PROOF_STATUS_PLANNED_ONLY in statuses:
        return PROOF_STATUS_PLANNED_ONLY
    if PROOF_STATUS_READY_TO_RUN in statuses:
        return PROOF_STATUS_READY_TO_RUN
    return PROOF_STATUS_STATE_MATERIALIZED


def _infer_status_from_materialization(
    materialization: dict[str, Any],
    *,
    executed: bool,
) -> str:
    """Back-fill actual_proof_status for older content_state payloads."""
    if not isinstance(materialization, dict):
        return PROOF_STATUS_PLANNED_ONLY
    status = str(materialization.get("status", ""))
    if status == "ready":
        return PROOF_STATUS_STATE_MATERIALIZED if executed else PROOF_STATUS_READY_TO_RUN
    return PROOF_STATUS_PLANNED_ONLY


def _mirror_status_for(
    *,
    expected_sinks: list[str],
    observed_sinks: list[str],
    actual_proof_status: str,
) -> str:
    """Map the collected evidence onto the mirror_status vocabulary.

    Passing requires the floor to be at least state_materialized AND every
    expected sink to be observed. Anything weaker stays at one of the
    interim statuses so consumers know exactly what evidence is missing.
    """
    expected_set = set(expected_sinks)
    observed_set = set(observed_sinks)
    if actual_proof_status == PROOF_STATUS_PLANNED_ONLY:
        if observed_set and expected_set.issubset(observed_set):
            return MIRROR_STATUS_INCONCLUSIVE
        return MIRROR_STATUS_PLANNED_ONLY
    if not expected_set:
        if observed_set:
            return MIRROR_STATUS_INCONCLUSIVE
        return MIRROR_STATUS_READY_TO_RUN if actual_proof_status == PROOF_STATUS_READY_TO_RUN else MIRROR_STATUS_STATE_MATERIALIZED
    if observed_set and expected_set.issubset(observed_set):
        return MIRROR_STATUS_PASSED
    if observed_set:
        return MIRROR_STATUS_INCONCLUSIVE
    if actual_proof_status == PROOF_STATUS_READY_TO_RUN:
        return MIRROR_STATUS_READY_TO_RUN
    return MIRROR_STATUS_STATE_MATERIALIZED


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
