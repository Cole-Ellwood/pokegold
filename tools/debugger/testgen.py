from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog import ROOT, keyword_matches, triage_request
from .provenance import build_provenance_report
from .reporting import load_reports


@dataclass(frozen=True)
class TestGeneratorRule:
    id: str
    title: str
    path_prefixes: tuple[str, ...]
    symbols: tuple[str, ...]
    symptom_keywords: tuple[str, ...]
    commands: tuple[str, ...]
    counterexample_commands: tuple[str, ...]
    notes: tuple[str, ...] = ()


GENERATOR_RULES = (
    TestGeneratorRule(
        id="damage_counterexamples",
        title="Damage-chain ROM-vs-oracle counterexamples",
        path_prefixes=(
            "engine/battle/effect_commands.asm",
            "engine/battle/late_gen_held_items.asm",
            "engine/battle/type_passive_damage_mods.asm",
            "data/moves/",
            "data/pokemon/base_stats/",
        ),
        symbols=(
            "wCurDamage",
            "BattleCommand_DamageCalc",
            "BattleCommand_DamageStats",
            "BattleCommand_Stab",
            "BattleCheckTypeMatchup",
            "CheckTypeMatchup",
            "wTypeMatchup",
            "TypeMatchups",
        ),
        symptom_keywords=(
            "damage",
            "clobber",
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
        ),
        commands=(
            "python -m tools.damage_debugger.oracle",
            "python -m tools.damage_debugger.fuzz --self-check-workers=2",
            "python -m tools.damage_debugger.fuzz --max-examples=500 --workers=2",
            "python -m tools.damage_debugger.coverage --write",
        ),
        counterexample_commands=(
            "python -m tools.damage_debugger.find <scenario>",
            "python -m tools.damage_debugger.minimize --bug <bug_id>",
            "python -m tools.damage_debugger.replay --scenario <scenario> --watch wCurDamage --json",
        ),
        notes=(
            "Use the fuzz seed and worker budget from a failure report to reproduce a generated counterexample.",
        ),
    ),
    TestGeneratorRule(
        id="boss_ai_counterexamples",
        title="Boss AI generated policy counterexamples",
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
        commands=(
            "python -m tools.boss_ai_debugger generate --family all --count 500 --seed 1 --out .local\\tmp\\debugger_all_scenarios.jsonl",
            "python -m tools.boss_ai_debugger batch-simulate --scenarios .local\\tmp\\debugger_all_scenarios.jsonl --json-out .local\\tmp\\debugger_all_batch.json --quiet",
            "python -m tools.boss_ai_debugger review-queue --report .local\\tmp\\debugger_all_batch.json --limit 50",
            "python -m tools.boss_ai_debugger metamorphic --generated 100 --seed 1 --fail-on-mismatch",
        ),
        counterexample_commands=(
            "python -m tools.boss_ai_debugger counterfactual --scenario <scenarios.jsonl> --scenario-id <id>",
            "python -m tools.boss_ai_debugger minimize --scenario <scenarios.jsonl> --scenario-id <id>",
            "python -m tools.boss_ai_debugger localize --report <batch_report.json>",
        ),
        notes=(
            "Use ROM materialization for selected generated cases before treating Python policy output as ROM behavior.",
        ),
    ),
    TestGeneratorRule(
        id="banking_abi_counterexamples",
        title="Banking and ABI hazard checks",
        path_prefixes=("home/", "macros/", "engine/"),
        symbols=("hROMBank", "FarCall", "Bankswitch"),
        symptom_keywords=("bank", "farcall", "register", "stack", "crash", "hang"),
        commands=(
            "python tools\\audit\\check_farcall_a_clobber.py",
            "python tools\\audit\\check_farcall_hl_clobber.py",
            "python tools\\audit\\check_cross_bank_call.py",
            "python tools\\audit\\check_release_smoke.py",
        ),
        counterexample_commands=(
            "python -m tools.debugger watch --watch-symbol hROMBank --execute --frames 120",
            "python -m tools.debugger provenance --symbol hROMBank --symbol FarCall",
        ),
    ),
    TestGeneratorRule(
        id="content_static_counterexamples",
        title="Content, map, graphics, and audio static checks",
        path_prefixes=("data/", "maps/", "gfx/", "audio/"),
        symbols=(),
        symptom_keywords=("map", "warp", "graphics", "palette", "audio", "text", "sprite"),
        commands=(
            "python tools\\audit\\check_release_smoke.py",
            "python tools\\audit\\check_layout_orgs.py",
            "python tools\\audit\\check_pic_bank_pressure.py",
            "python -m tools.debugger content-mirror --changed-file <changed_file>",
            "python -m tools.debugger content-scenarios --changed-file <changed_file> --out-scenarios .local\\tmp\\debugger_content_scenarios.jsonl",
            "python -m tools.debugger expect --source-file <changed_file>",
        ),
        counterexample_commands=(
            "python -m tools.debugger provenance --source-file <changed_file>",
            "python -m tools.debugger ingest --changed-file <changed_file>",
            "python -m tools.debugger content-mirror --source-file <changed_file>",
            "python -m tools.debugger content-scenarios --source-file <changed_file> --out-scenarios .local\\tmp\\debugger_content_scenarios.jsonl",
            "python -m tools.debugger expect --source-file <changed_file> --expect contains=<expected_text>",
        ),
        notes=(
            "This surface can use semantic content mirrors, source-derived scenarios, and static expectations now, but still needs dedicated dynamic ROM replay/fuzz generators.",
        ),
    ),
)


def suggest_tests(
    *,
    reports: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    symptom: str = "",
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    normalized_paths = tuple(path.replace("\\", "/").lower() for path in changed_files)
    symptom_text = symptom.lower()
    matches = next_step_test_matches(loaded_reports)
    for rule in GENERATOR_RULES:
        path_hit = any(
            any(path.startswith(prefix.lower()) for prefix in rule.path_prefixes)
            for path in normalized_paths
        )
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
                "matched_by": [
                    name
                    for name, hit in (
                        ("changed_file", path_hit),
                        ("symbol", symbol_hit),
                        ("symptom", symptom_hit),
                    )
                    if hit
                ],
                "commands": list(rule.commands),
                "counterexample_commands": list(rule.counterexample_commands),
                "notes": list(rule.notes),
            }
        )

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
            return suggest_tests(
                changed_files=tuple(related_files),
                symbols=symbols,
                symptom=symptom,
                reports=reports,
                root=root,
            )

    if not matches:
        triage = triage_request(changed_files=changed_files, symptom=symptom, root=root)
        matches.append(
            {
                "id": "general",
                "title": "General romhack counterexample baseline",
                "matched_by": ["fallback"],
                "commands": [
                    "python -m tools.debugger audit",
                    "python tools\\audit\\check_release_smoke.py",
                ],
                "counterexample_commands": [
                    "python -m tools.debugger provenance --source-file <changed_file>",
                    "python -m tools.debugger watch --watch-symbol <symbol>",
                ],
                "notes": [
                    "No focused generator matched; use triage commands and add a dedicated generator rule for this surface.",
                ],
                "triage_match_ids": [match["id"] for match in triage["matches"]],
            }
        )

    return {
        "schema_version": 1,
        "kind": "unified_debugger_test_suggestions",
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
        "counterexample_commands": unique_commands(matches, "counterexample_commands"),
    }


def next_step_test_matches(loaded_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches = []
    for loaded in loaded_reports:
        for next_step in next_step_reports_from_loaded(loaded):
            match = next_step_test_match(source=loaded["source"], next_step=next_step)
            if match:
                matches.append(match)
    return matches


def next_step_reports_from_loaded(loaded: dict[str, Any]) -> list[dict[str, Any]]:
    data = loaded["data"]
    if not isinstance(data, dict):
        return []
    if data.get("kind") == "unified_debugger_next_step":
        return [data]
    embedded = data.get("symptom_only_next_step")
    if isinstance(embedded, dict) and embedded.get("kind") == "unified_debugger_next_step":
        return [embedded]
    return []


def next_step_test_match(*, source: str, next_step: dict[str, Any]) -> dict[str, Any] | None:
    recommendation = next_step.get("recommendation")
    if not isinstance(recommendation, dict):
        return None
    symptom_class = str(recommendation.get("symptom_class") or "unknown")
    title = str(recommendation.get("title") or symptom_class or "next proof route")
    first_command = str(recommendation.get("first_command") or "")
    regression_gate = str(recommendation.get("regression_gate") or "")
    escalation_command = str(recommendation.get("escalation_command") or "")
    return {
        "id": "next_step_regression_gate",
        "title": f"Regression gate from next proof route: {title}",
        "matched_by": ["report", "next_step"],
        "source": source,
        "symptom_class": symptom_class,
        "commands": unique_strings([first_command, regression_gate]),
        "counterexample_commands": unique_strings([escalation_command]),
        "notes": next_step_notes(source=source, recommendation=recommendation),
    }


def next_step_notes(*, source: str, recommendation: dict[str, Any]) -> list[str]:
    notes = [
        f"report: {source}",
        f"symptom_class: {recommendation.get('symptom_class', 'unknown')}",
    ]
    for label, key in (
        ("required input", "required_inputs"),
        ("source/data", "source_refs"),
        ("evidence standard", "evidence_standard"),
        ("disproof standard", "disproof_standard"),
    ):
        for item in string_items(recommendation.get(key)):
            notes.append(f"{label}: {item}")
    proof_limit = str(recommendation.get("proof_limit") or "")
    if proof_limit:
        notes.append(f"proof limit: {proof_limit}")
    return notes


def unique_commands(matches: list[dict[str, Any]], key: str) -> list[str]:
    return unique_strings(
        command
        for match in matches
        for command in match.get(key, [])
    )


def string_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list | tuple):
        return [
            item
            for raw in value
            for item in string_items(raw)
        ]
    return []


def unique_strings(items: Any) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        command = str(item)
        if not command or command in seen:
            continue
        seen.add(command)
        out.append(command)
    return out
