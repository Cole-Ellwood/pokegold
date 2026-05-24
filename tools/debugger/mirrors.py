from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog import ROOT, keyword_matches, triage_request
from .provenance import build_provenance_report
from .reporting import load_reports


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
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    matches = content_state_mirror_matches(loaded_reports)
    matches.extend(next_step_mirror_matches(loaded_reports))
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


def next_step_mirror_matches(loaded_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches = []
    for loaded in loaded_reports:
        source = str(loaded.get("source", ""))
        data = loaded.get("data", {})
        if not isinstance(data, dict):
            continue
        for next_step in embedded_next_step_reports(data):
            recommendation = next_step.get("recommendation")
            if not isinstance(recommendation, dict):
                continue
            lane = str(recommendation.get("matched_lane") or next_step.get("matched_lane") or "")
            rule = mirror_rule_for_lane(lane)
            if not rule:
                continue
            commands = unique_list(
                [
                    str(recommendation.get("first_command") or ""),
                    str(recommendation.get("regression_gate") or ""),
                    *rule.commands,
                ]
            )
            materialization_commands = unique_list(
                [
                    str(recommendation.get("first_command") or ""),
                    str(recommendation.get("regression_gate") or ""),
                    str(recommendation.get("escalation_command") or ""),
                    *route_specific_materialization_commands(recommendation, rule=rule),
                ]
            )
            matches.append(
                {
                    "id": rule.id,
                    "title": rule.title,
                    "scope": rule.scope,
                    "confidence": rule.confidence,
                    "matched_by": ["report", "next_step", str(recommendation.get("symptom_class") or "")],
                    "evidence": unique_list(
                        [
                            f"next-step route from {source}",
                            f"symptom_class={recommendation.get('symptom_class', '')}",
                            f"proof limit: {recommendation.get('proof_limit', '')}",
                            *[f"source_ref={item}" for item in string_items(recommendation.get("source_refs"))],
                            *[f"evidence standard: {item}" for item in string_items(recommendation.get("evidence_standard"))],
                            *[f"disproof standard: {item}" for item in string_items(recommendation.get("disproof_standard"))],
                        ]
                    ),
                    "commands": commands,
                    "materialization_commands": materialization_commands,
                    "gaps": unique_list(
                        [
                            *rule.gaps,
                            "A next-step mirror route is still a proof plan until the named materialization command runs against a matching scenario.",
                        ]
                    ),
                }
            )
    return matches


def embedded_next_step_reports(data: dict[str, Any]) -> list[dict[str, Any]]:
    if data.get("kind") == "unified_debugger_next_step":
        return [data]
    next_step = data.get("symptom_only_next_step")
    if isinstance(next_step, dict) and next_step.get("kind") == "unified_debugger_next_step":
        return [next_step]
    return []


def mirror_rule_for_lane(lane: str) -> MirrorRule | None:
    normalized = lane.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in {"boss_ai", "boss"}:
        return mirror_rule_by_id("boss_ai_policy_mirror")
    if normalized in {"damage", "battle_damage"}:
        return mirror_rule_by_id("damage_oracle")
    if normalized in {
        "banking_abi",
        "graphics_vram",
        "runtime_crash",
        "runtime_state",
        "base_ai_mechanics",
        "pokemon_semantics",
        "static_audits",
        "overworld_status",
    }:
        return mirror_rule_by_id("static_invariant_mirror")
    return None


def mirror_rule_by_id(rule_id: str) -> MirrorRule | None:
    for rule in MIRROR_RULES:
        if rule.id == rule_id:
            return rule
    return None


def route_specific_materialization_commands(recommendation: dict[str, Any], *, rule: MirrorRule) -> list[str]:
    commands = list(rule.materialization_commands)
    first_command = str(recommendation.get("first_command") or "")
    if "rom-switch-materialize" in first_command:
        return [first_command, str(recommendation.get("escalation_command") or "")]
    return commands


def content_state_mirror_matches(loaded_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
        gaps = []
        if not executed:
            gaps.append(
                "Content-state patches are planned but no patched save state was executed; run the content-state --execute command before treating this as final emulator behavior."
            )
        evidence = [
            f"report={source}",
            f"scenarios={len(scenario_ids)}",
            f"patches={sum(len(item.get('patches', [])) for item in materializations)}",
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
            }
        )
    return matches


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


def string_items(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list | tuple):
        return [str(item) for item in value if isinstance(item, (str, int))]
    return []
