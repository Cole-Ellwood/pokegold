from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog import ROOT, triage_request
from .provenance import build_provenance_report


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
        ),
        symptom_keywords=("damage", "clobber", "stab", "type", "held item", "weather"),
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
    changed_files: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    symptom: str = "",
    root: Path = ROOT,
) -> dict[str, Any]:
    normalized_paths = tuple(path.replace("\\", "/").lower() for path in changed_files)
    symptom_text = symptom.lower()
    matches = []
    for rule in GENERATOR_RULES:
        path_hit = any(
            any(path.startswith(prefix.lower()) for prefix in rule.path_prefixes)
            for path in normalized_paths
        )
        symbol_hit = any(symbol in rule.symbols for symbol in symbols)
        symptom_hit = bool(symptom_text) and any(
            keyword in symptom_text for keyword in rule.symptom_keywords
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
        "changed_files": list(changed_files),
        "symbols": list(symbols),
        "symptom": symptom,
        "match_count": len(matches),
        "matches": matches,
        "commands": unique_commands(matches, "commands"),
        "counterexample_commands": unique_commands(matches, "counterexample_commands"),
    }


def unique_commands(matches: list[dict[str, Any]], key: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for match in matches:
        for command in match[key]:
            if command in seen:
                continue
            seen.add(command)
            out.append(command)
    return out
