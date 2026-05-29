from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .content_scenarios import (
    attach_behavioral_probes,
    content_scenario_records,
    content_state_instruction_trace_command,
)
from .dynamic_taint import discover_dynamic_taint_inputs_from_report
from .impact import build_impact_report
from .localize import normalize_path
from .minimize import (
    build_minimization_plan,
    load_scenario_files,
    scenario_id_for,
    unique_list,
)
from .mirrors import build_compare_plan
from .provenance import display_path, resolve_path
from .reporting import load_reports
from .testgen import suggest_tests
from .workflow import command_is_runnable, execute_step


SURFACE_RULES = {
    "damage": {
        "title": "Damage chain",
        "path_prefixes": (
            "engine/battle/effect_commands.asm",
            "engine/battle/late_gen_held_items.asm",
            "engine/battle/type_passive_damage_mods.asm",
            "data/moves/",
            "data/pokemon/base_stats/",
        ),
        "symbols": (
            "wCurDamage",
            "BattleCommand_Damage",
            "BattleCommand_DamageCalc",
            "BattleCommand_DamageStats",
            "BattleCommand_Stab",
        ),
        "keywords": ("damage", "hp", "stab", "type chart", "type matchup", "type effectiveness", "weather", "held item", "badge"),
    },
    "boss_ai": {
        "title": "Boss AI policy",
        "path_prefixes": (
            "engine/battle/ai/",
            "tools/boss_ai_debugger/",
            "tools/boss_ai_preference/",
            "audit/boss_ai_trace/",
            "audit/boss_ai_debugger/",
        ),
        "symbols": (
            "BossAI_",
            "wEnemyAIMoveScores",
            "wBossAI",
        ),
        "keywords": ("boss", "ai", "selector", "score", "switch", "policy"),
    },
    "banking_abi": {
        "title": "Banking and ABI",
        "path_prefixes": ("home/", "macros/", "engine/"),
        "symbols": ("hROMBank", "hLoadedROMBank", "FarCall", "Bankswitch"),
        "keywords": ("bank", "farcall", "register", "stack", "crash", "hang", "clobber"),
    },
    "content_static": {
        "title": "Maps, scripts, graphics, audio, and data",
        "path_prefixes": (
            "maps/",
            "scripts/",
            "text/",
            "gfx/",
            "audio/",
            "data/",
        ),
        "symbols": (),
        "keywords": (
            "map",
            "warp",
            "script",
            "graphics",
            "palette",
            "audio",
            "song",
            "text",
            "sprite",
            "ui",
        ),
    },
}
SURFACE_ALIASES = {
    "battle_damage": "damage",
    "boss": "boss_ai",
    "ai": "boss_ai",
    "banking": "banking_abi",
    "abi": "banking_abi",
    "content": "content_static",
    "maps": "content_static",
    "graphics": "content_static",
    "audio": "content_static",
}
SURFACE_ORDER = ("damage", "boss_ai", "banking_abi", "content_static", "general")
SURFACE_NAMES = frozenset(SURFACE_ORDER)
GENERATOR_PROOF_LEVELS = {
    "damage": "dynamic",
    "boss_ai": "dynamic",
    "banking_abi": "dynamic_state_probe_planned",
    "content_static": "positioned_state_dynamic_planned",
    "general": "planning",
}
BANKING_WATCH_SYMBOLS = ("hROMBank", "wFarCallBC")
BANKING_TRACE_SYMBOLS = ("FarCall", "FarCall_hl", "Bankswitch")
BANKING_PATCH_PROFILES = (
    ("active_bank_shadow", ("hROMBank=1",)),
    ("farcall_param_pair", ("wFarCallBC=0,0",)),
    ("bank_shadow_and_farcall_params", ("hROMBank=1", "wFarCallBC=0,0")),
)


def build_generation_plan(
    *,
    reports: tuple[str, ...] = (),
    scenarios: tuple[str, ...] = (),
    families: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    symptom: str = "",
    out_scenarios: str = "",
    max_cases: int = 64,
    seed: int = 1,
    execute: bool = False,
    max_execute_commands: int = 8,
    execute_timeout_seconds: int = 600,
    root: Path = ROOT,
) -> dict[str, Any]:
    case_limit = max(1, int(max_cases))
    warnings = []
    if max_cases < 1:
        warnings.append("max_cases was below 1 and was clamped to 1")

    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    loaded_scenarios, scenario_errors = load_scenario_files(
        scenarios=scenarios,
        root=root,
    )
    tests = suggest_tests(
        reports=reports,
        changed_files=changed_files,
        symbols=symbols,
        symptom=symptom,
        root=root,
    )
    compare = build_compare_plan(
        reports=reports,
        changed_files=changed_files,
        symbols=symbols,
        symptom=symptom,
        root=root,
    )
    minimization = build_minimization_plan(
        reports=reports,
        scenarios=scenarios,
        symbols=symbols,
        changed_files=changed_files,
        symptom=symptom,
        max_scenarios=min(case_limit, 20),
        root=root,
    )
    impact = build_impact_report(
        reports=reports,
        changed_files=changed_files,
        symbols=symbols,
        symptom=symptom,
        max_items=min(case_limit, 40),
        root=root,
    )

    signals = collect_generation_signals(
        loaded_reports=loaded_reports,
        loaded_scenarios=loaded_scenarios,
        families=families,
        symbols=symbols,
        changed_files=changed_files,
        symptom=symptom,
        tests=tests,
        compare=compare,
        minimization=minimization,
        impact=impact,
    )
    surfaces = infer_generation_surfaces(
        families=families,
        symbols=symbols,
        changed_files=changed_files,
        symptom=symptom,
        signals=signals,
    )
    generators = [
        build_generator(
            surface=surface,
            families=families,
            seed=seed,
            max_cases=case_limit,
        )
        for surface in surfaces
    ]
    seed_records = build_seed_records(
        surfaces=surfaces,
        generators=generators,
        families=families,
        symbols=symbols,
        changed_files=changed_files,
        symptom=symptom,
        seed=seed,
        max_cases=case_limit,
        out_scenarios=out_scenarios,
        root=root,
    )
    seed_output = write_seed_records(
        records=seed_records,
        out_scenarios=out_scenarios,
        root=root,
    )
    materialization_steps = build_materialization_steps(
        surfaces=surfaces,
        generators=generators,
        out_scenarios=seed_output.get("path", ""),
        families=families,
        reports=reports,
        symbols=symbols,
        changed_files=changed_files,
        symptom=symptom,
        seed=seed,
        max_cases=case_limit,
    )
    dynamic_taint_handoffs = build_dynamic_taint_handoffs(
        loaded_reports=loaded_reports,
        root=root,
    )
    counterexamples = collect_counterexamples(
        tests=tests,
        minimization=minimization,
        generators=generators,
        dynamic_taint_handoffs=dynamic_taint_handoffs,
    )
    commands = unique_list(
        [
            *tests.get("commands", []),
            *tests.get("counterexample_commands", []),
            *compare.get("commands", []),
            *compare.get("materialization_commands", []),
            *minimization.get("commands", []),
            *impact.get("commands", []),
            *commands_from_generators(generators),
            *commands_from_seed_records(seed_records),
            *[step["command"] for step in materialization_steps],
            *[item["command"] for item in dynamic_taint_handoffs],
            *[item["command"] for item in counterexamples],
        ]
    )
    execution = execute_command_batch(
        commands,
        execute=execute,
        max_commands=max_execute_commands,
        timeout_seconds=execute_timeout_seconds,
        root=root,
        step_prefix="generation",
    )
    errors = unique_list(
        [
            *report_errors,
            *scenario_errors,
            *seed_output.get("errors", []),
            *(execution.get("errors", []) if execute else []),
        ]
    )

    return {
        "schema_version": 1,
        "kind": "unified_debugger_generation_plan",
        "root": str(root),
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "reports": [item["source"] for item in loaded_reports],
        "scenarios": [item["source"] for item in loaded_scenarios],
        "scenario_count": sum(len(item["records"]) for item in loaded_scenarios),
        "changed_files": list(changed_files),
        "symbols": list(symbols),
        "families": list(families),
        "symptom": symptom,
        "seed": seed,
        "max_cases": case_limit,
        "surface_count": len(surfaces),
        "surfaces": surfaces,
        "signal_count": len(signals),
        "signals": signals[:160],
        "generator_count": len(generators),
        "generators": generators,
        "counterexample_count": len(counterexamples),
        "counterexamples": counterexamples,
        "dynamic_taint_handoff_count": len(dynamic_taint_handoffs),
        "dynamic_taint_handoffs": dynamic_taint_handoffs,
        "materialization_step_count": len(materialization_steps),
        "materialization_steps": materialization_steps,
        "seed_count": len(seed_records),
        "seed_manifest": seed_output,
        "test_suggestions": {
            "match_count": tests.get("match_count", 0),
            "match_ids": [match.get("id", "") for match in tests.get("matches", [])],
        },
        "mirror_plan": {
            "match_count": compare.get("match_count", 0),
            "match_ids": [match.get("id", "") for match in compare.get("matches", [])],
        },
        "minimization_plan": {
            "surfaces": minimization.get("surfaces", []),
            "step_count": len(minimization.get("steps", [])),
            "selected_scenario_ids": minimization.get("selected_scenario_ids", []),
        },
        "impact_plan": {
            "impact_count": impact.get("impact_count", 0),
            "items": [
                {
                    "surface": item.get("surface", ""),
                    "title": item.get("title", ""),
                    "impact_score": item.get("impact_score", 0),
                }
                for item in impact.get("items", [])[:10]
            ],
        },
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "executed": execute,
        "execution": execution,
        "known_limits": [
            "This is the unified generator coordinator for this Pokemon Gold romhack; it only executes commands when --execute is supplied, and semantic scenario execution is strongest where a surface has a ROM materializer.",
            "The optional JSONL seed manifest is a deterministic handoff manifest, not a guarantee that every surface can be replayed directly by the ROM today.",
            "Damage and Boss AI have mature dynamic generators; map/script/movement content, banking, object-event runtime-hour contexts, UI output sinks, and audio command/header WRAM plus rAUD hardware output sinks now have dynamic proof routes, while arbitrary event-engine states, full pixel playback, and full audio playback still need deeper dynamic generators.",
        ],
    }


def execute_command_batch(
    commands: list[str],
    *,
    execute: bool,
    max_commands: int,
    timeout_seconds: int,
    root: Path,
    step_prefix: str,
) -> dict[str, Any]:
    unique_commands = unique_list(commands)
    steps = [
        {
            "id": f"{step_prefix}:{index + 1}",
            "command": command,
            "runnable": command_is_runnable(command),
            "status": "pending",
            "returncode": None,
            "elapsed_seconds": 0.0,
            "stdout_tail": [],
            "stderr_tail": [],
        }
        for index, command in enumerate(unique_commands[: max(0, int(max_commands))])
    ]
    if execute:
        for step in steps:
            execute_step(step, root=root, timeout_seconds=timeout_seconds)
    else:
        for step in steps:
            step["status"] = "planned"
    failed = [step for step in steps if step["status"] == "failed"]
    skipped = [step for step in steps if step["status"] == "skipped"]
    passed = [step for step in steps if step["status"] == "passed"]
    return {
        "attempted": bool(unique_commands),
        "executed": execute,
        "command_count": len(unique_commands),
        "step_count": len(steps),
        "max_commands": max(0, int(max_commands)),
        "passed_count": len(passed),
        "failed_count": len(failed),
        "skipped_count": len(skipped),
        "truncated": len(unique_commands) > len(steps),
        "steps": steps,
        "errors": [
            f"{step['id']}: {step['command']}"
            for step in failed
        ],
    }


def collect_generation_signals(
    *,
    loaded_reports: list[dict[str, Any]],
    loaded_scenarios: list[dict[str, Any]],
    families: tuple[str, ...],
    symbols: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
    tests: dict[str, Any],
    compare: dict[str, Any],
    minimization: dict[str, Any],
    impact: dict[str, Any],
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for family in families:
        signals.append(signal("explicit_family", "family", family, 80, "input"))
    for symbol in symbols:
        signals.append(signal("explicit_symbol", "symbol", symbol, 80, "input"))
    for path in changed_files:
        signals.append(signal("explicit_file", "file", normalize_path(path), 80, "input"))
    if symptom:
        signals.append(signal("symptom", "note", symptom, 60, "input"))

    for loaded in loaded_scenarios:
        for record in loaded["records"]:
            scenario_id = scenario_id_for(record)
            if scenario_id:
                signals.append(signal("scenario_file", "scenario", scenario_id, 45, loaded["source"]))
            family = record.get("family") or record.get("surface") or record.get("kind")
            if isinstance(family, str) and family:
                signals.append(signal("scenario_family", "family", family, 40, loaded["source"]))

    for loaded in loaded_reports:
        kind = str(loaded["data"].get("kind", "report"))
        signals.append(signal("input_report", "report", kind, 35, loaded["source"]))
        collect_report_signals(loaded["data"], source=loaded["source"], out=signals)

    for match in tests.get("matches", []):
        signals.append(signal("test_generator", "generator", str(match.get("id", "")), 55, "suggest-tests"))
        for symbol_name in match.get("related_symbols", [])[:6]:
            signals.append(signal("test_related_symbol", "symbol", str(symbol_name), 45, "suggest-tests"))
        for address in match.get("related_addresses", [])[:6]:
            signals.append(signal("test_related_address", "address", str(address), 45, "suggest-tests"))
    for match in compare.get("matches", []):
        signals.append(signal("mirror", "mirror", str(match.get("id", "")), 50, "compare"))
    for item in minimization.get("signals", []):
        value = str(item.get("value", ""))
        if value:
            signals.append(
                signal(
                    "minimization_" + str(item.get("type", "signal")),
                    str(item.get("kind", "note")),
                    value,
                    int(item.get("weight", 0)),
                    "minimize",
                )
            )
    for item in impact.get("items", [])[:20]:
        title = str(item.get("title", ""))
        if title:
            signals.append(signal("impact", "note", title, int(item.get("impact_score", 0)), "impact"))
        for symbol_name in item.get("related_symbols", [])[:6]:
            signals.append(signal("impact_symbol", "symbol", str(symbol_name), 45, "impact"))
        for path in item.get("related_files", [])[:6]:
            signals.append(signal("impact_file", "file", normalize_path(str(path)), 45, "impact"))

    return merge_signals(signals)


def collect_report_signals(data: Any, *, source: str, out: list[dict[str, Any]]) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            if key in {"symbol", "watch", "query", "resolved"} and isinstance(value, str):
                out.append(signal(f"report_{key}", "symbol", value, 35, source))
            elif key in {"path", "file", "source_file"} and isinstance(value, str):
                out.append(signal(f"report_{key}", "file", normalize_path(value), 35, source))
            elif key in {"scenario_id", "id"} and isinstance(value, str):
                out.append(signal(f"report_{key}", "scenario", value, 30, source))
            elif key in {"surface", "surface_id", "family", "kind", "type"} and isinstance(value, str):
                out.append(signal(f"report_{key}", "note", value, 25, source))
            collect_report_signals(value, source=source, out=out)
    elif isinstance(data, list):
        for item in data:
            collect_report_signals(item, source=source, out=out)


def infer_generation_surfaces(
    *,
    families: tuple[str, ...],
    symbols: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
    signals: list[dict[str, Any]],
) -> list[str]:
    surfaces: set[str] = set()
    for family in families:
        surface = normalize_surface(family)
        if surface:
            surfaces.add(surface)

    signal_paths = [
        str(item["value"])
        for item in signals
        if item.get("kind") == "file" and item.get("value")
    ]
    normalized_paths = [
        normalize_path(path).lower()
        for path in [*changed_files, *signal_paths]
    ]
    symbol_text = " ".join(symbols).lower()
    keyword_text = " ".join(
        [
            symptom,
            *symbols,
            *[
                item["value"]
                for item in signals
                if item["kind"] not in {"scenario", "file"}
            ],
        ]
    ).lower().replace("\\", "/")

    for surface, rule in SURFACE_RULES.items():
        path_hit = any(
            any(path.startswith(prefix.lower()) or f"/{prefix.lower()}" in path for prefix in rule["path_prefixes"])
            for path in normalized_paths
        )
        symbol_hit = any(hint.lower() in symbol_text for hint in rule["symbols"])
        keyword_hit = any(keyword_matches(keyword, keyword_text) for keyword in rule["keywords"])
        generator_hit = surface in keyword_text or surface.replace("_", " ") in keyword_text
        if path_hit or symbol_hit or keyword_hit or generator_hit:
            surfaces.add(surface)

    if "damage" in surfaces:
        for path in normalized_paths:
            if path.startswith(("data/moves/", "data/pokemon/base_stats/")):
                continue
            if path.startswith("data/"):
                surfaces.add("content_static")
    if not surfaces:
        surfaces.add("general")
    if len(surfaces) > 1:
        surfaces.discard("general")
    return [surface for surface in SURFACE_ORDER if surface in surfaces]


def normalize_surface(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in SURFACE_NAMES:
        return normalized
    return SURFACE_ALIASES.get(normalized, "")


def keyword_matches(keyword: str, text: str) -> bool:
    normalized = keyword.strip().lower()
    if not normalized:
        return False
    if " " in normalized:
        return normalized in text
    tokens = {
        token
        for token in "".join(char if char.isalnum() else " " for char in text).split()
    }
    return normalized in tokens


def build_generator(
    *,
    surface: str,
    families: tuple[str, ...],
    seed: int,
    max_cases: int,
) -> dict[str, Any]:
    if surface == "damage":
        commands = [
            "python -m tools.damage_debugger.oracle",
            "python -m tools.damage_debugger.fuzz --self-check-workers=2",
            f"python -m tools.damage_debugger.fuzz --max-examples={max(100, max_cases)} --workers=2",
            "python -m tools.damage_debugger.coverage --write",
        ]
        counterexample_commands = [
            "python -m tools.damage_debugger.find <scenario>",
            "python -m tools.damage_debugger.minimize --bug <bug_id>",
            "python -m tools.damage_debugger.replay --scenario <scenario> --watch wCurDamage --json",
        ]
        materialization_commands = [
            "python -m tools.damage_debugger.replay --scenario <scenario> --watch wCurDamage --json",
            "python -m tools.debugger replay --symbol wCurDamage --execute-watch",
        ]
        return generator(
            generator_id="damage_fuzz",
            surface=surface,
            title="Damage ROM-vs-oracle fuzz and counterexample generator",
            confidence=0.9,
            status="ready",
            commands=commands,
            counterexample_commands=counterexample_commands,
            materialization_commands=materialization_commands,
            gaps=[],
        )

    if surface == "boss_ai":
        family = first_boss_family(families)
        scenario_path = ".local\\tmp\\debugger_boss_ai_generated.jsonl"
        commands = [
            f"python -m tools.boss_ai_debugger generate --family {family} --count {max_cases} --seed {seed} --out {scenario_path}",
            f"python -m tools.boss_ai_debugger batch-simulate --scenarios {scenario_path} --json-out .local\\tmp\\debugger_boss_ai_batch.json --quiet",
            f"python -m tools.boss_ai_debugger review-queue --scenarios {scenario_path} --limit {min(50, max_cases)}",
            f"python -m tools.boss_ai_debugger metamorphic --generated {min(100, max_cases)} --seed {seed} --fail-on-mismatch",
        ]
        counterexample_commands = [
            "python -m tools.boss_ai_debugger counterfactual --scenario <scenarios.jsonl> --scenario-id <id>",
            "python -m tools.boss_ai_debugger minimize --scenario <scenarios.jsonl> --scenario-id <id>",
            "python -m tools.boss_ai_debugger localize --scenarios <scenarios.jsonl>",
        ]
        materialization_commands = [
            "python -m tools.boss_ai_debugger rom-selector-materialize --scenarios <scenarios.jsonl> --limit 20",
            "python -m tools.boss_ai_debugger rom-score-materialize --scenarios <scenarios.jsonl> --limit 4 --compare-fast-score",
            "python -m tools.boss_ai_debugger rom-switch-materialize --scenarios <scenarios.jsonl> --limit 20",
        ]
        return generator(
            generator_id="boss_ai_generated_policy",
            surface=surface,
            title="Boss AI generated policy counterexamples",
            confidence=0.88,
            status="ready",
            commands=commands,
            counterexample_commands=counterexample_commands,
            materialization_commands=materialization_commands,
            gaps=[
                "Broad generated policy cases must be ROM-materialized before treating Python policy deltas as ROM behavior.",
            ],
        )

    if surface == "banking_abi":
        dynamic_probe_commands = banking_dynamic_probe_commands()
        commands = [
            "python tools\\audit\\check_farcall_a_clobber.py",
            "python tools\\audit\\check_farcall_hl_clobber.py",
            "python tools\\audit\\check_cross_bank_call.py",
            "python tools\\audit\\check_release_smoke.py",
            dynamic_probe_commands[0],
        ]
        counterexample_commands = [
            "python -m tools.debugger watch --watch-symbol hROMBank --execute --frames 120",
            "python -m tools.debugger provenance --symbol hROMBank --symbol FarCall",
            "python -m tools.debugger gate --changed-file <changed_file>",
            dynamic_probe_commands[3],
            dynamic_probe_commands[4],
        ]
        materialization_commands = [
            dynamic_probe_commands[1],
            dynamic_probe_commands[2],
            dynamic_probe_commands[3],
            dynamic_probe_commands[4],
            "python -m tools.debugger explain --symbol hROMBank --changed-file <changed_file>",
        ]
        return generator(
            generator_id="banking_abi_dynamic_probe",
            surface=surface,
            title="Banking and ABI dynamic state-space probe generator",
            confidence=0.74,
            status="dynamic-probe-planned",
            commands=commands,
            counterexample_commands=counterexample_commands,
            materialization_commands=materialization_commands,
            gaps=[],
        )

    if surface == "content_static":
        commands = [
            "python tools\\audit\\check_release_smoke.py",
            "python tools\\audit\\check_layout_orgs.py",
            "python tools\\audit\\check_pic_bank_pressure.py",
            "python -m tools.debugger content-mirror --changed-file <changed_file>",
            "python -m tools.debugger content-scenarios --changed-file <changed_file> --out-scenarios .local\\tmp\\debugger_content_scenarios.jsonl",
            "python -m tools.debugger content-state --scenario .local\\tmp\\debugger_content_scenarios.jsonl --scenario-id <id> --json-out .local\\tmp\\debugger_content_state_<id>.json",
            "python -m tools.debugger expect --source-file <changed_file>",
            "python -m tools.debugger coverage --changed-file <changed_file>",
        ]
        counterexample_commands = [
            "python -m tools.debugger provenance --source-file <changed_file>",
            "python -m tools.debugger explain --changed-file <changed_file>",
            "python -m tools.debugger compare --changed-file <changed_file>",
            "python -m tools.debugger content-mirror --source-file <changed_file>",
            "python -m tools.debugger content-scenarios --source-file <changed_file> --out-scenarios .local\\tmp\\debugger_content_scenarios.jsonl",
            "python -m tools.debugger expect --source-file <changed_file> --expect contains=<expected_text>",
        ]
        materialization_commands = [
            "python -m tools.debugger ingest --changed-file <changed_file>",
            "python -m tools.debugger gate --changed-file <changed_file>",
            "python -m tools.debugger content-state --scenario .local\\tmp\\debugger_content_scenarios.jsonl --scenario-id <id> --base-save-state <base_state> --out-state .local\\tmp\\debugger_content_state_<id>.state --execute --json-out .local\\tmp\\debugger_content_state_<id>.json",
            "python -m tools.debugger replay --report .local\\tmp\\debugger_content_state_<id>.json --scenario .local\\tmp\\debugger_content_scenarios.jsonl --scenario-id <id> --execute-watch",
            "python -m tools.debugger replay --scenario .local\\tmp\\debugger_content_scenarios.jsonl --scenario-id <id>",
            "python -m tools.debugger replay --scenario .local\\tmp\\debugger_content_scenarios.jsonl --scenario-id <id> --changed-file <changed_file> --symbol <runtime_helper> --watch-symbol <state_symbol>",
            "python -m tools.debugger expect --source-file <changed_file> --expect not-contains=<forbidden_text>",
        ]
        return generator(
            generator_id="content_static_seed_manifest",
            surface=surface,
            title="Content/static positioned-state seed and replay generator",
            confidence=0.72,
            status="positioned-state-planned",
            commands=commands,
            counterexample_commands=counterexample_commands,
            materialization_commands=materialization_commands,
            gaps=[
                "Map content scenarios now route through positioned-state WRAM patch generation, object-event runtime-hour hHours/wTimeOfDay variants, and replay; audio header/command streams now expose music WRAM and rAUD hardware output-sink proof routes, while asset, UI, and arbitrary script semantic generators still need dedicated emulator-backed state builders for final behavioral proof.",
            ],
        )

    commands = [
        "python -m tools.debugger audit",
        "python -m tools.debugger triage --symptom <description>",
        "python -m tools.debugger localize --symptom <description>",
        "python -m tools.debugger coverage --symbol <symbol>",
    ]
    counterexample_commands = [
        "python -m tools.debugger suggest-tests --changed-file <changed_file>",
        "python -m tools.debugger compare --changed-file <changed_file>",
        "python -m tools.debugger minimize --report <report.json>",
    ]
    materialization_commands = [
        "python -m tools.debugger replay --report <report.json>",
        "python -m tools.debugger report --report <report.json>",
    ]
    return generator(
        generator_id="general_seed_manifest",
        surface=surface,
        title="General unified debugger seed manifest",
        confidence=0.4,
        status="needs-subsystem",
        commands=commands,
        counterexample_commands=counterexample_commands,
        materialization_commands=materialization_commands,
        gaps=[
            "No dedicated generator matched this surface; add a focused generator rule once the behavior is identified.",
        ],
    )


def first_boss_family(families: tuple[str, ...]) -> str:
    for family in families:
        if normalize_surface(family):
            continue
        if family.strip():
            return family.strip()
    return "all"


def banking_patch_profile(index: int) -> tuple[str, tuple[str, ...]]:
    return BANKING_PATCH_PROFILES[index % len(BANKING_PATCH_PROFILES)]


def banking_dynamic_probe_commands(
    *,
    report_stem: str = ".local\\tmp\\debugger_banking_probe",
    patches: tuple[str, ...] | None = None,
    source_file: str = "",
    base_state: str = "<base_state>",
) -> list[str]:
    patch_specs = tuple(patches or BANKING_PATCH_PROFILES[-1][1])
    state_report = f"{report_stem}_state_space.json"
    patched_state = f"{report_stem}.state"
    trace_report = f"{report_stem}_trace_report.json"
    trace_path = f"{report_stem}_trace.jsonl"
    patch_args = " ".join(f"--patch {patch}" for patch in patch_specs)
    watch_args = " ".join(f"--watch-symbol {symbol}" for symbol in BANKING_WATCH_SYMBOLS)
    trace_args = " ".join(f"--symbol {symbol}" for symbol in BANKING_TRACE_SYMBOLS)
    sink_args = " ".join(f"--sink-symbol {symbol}" for symbol in BANKING_WATCH_SYMBOLS)
    source_arg = f" --source-file {quote_arg(source_file)}" if source_file else ""
    return unique_list(
        [
            (
                "python -m tools.debugger state-space "
                f"{patch_args}{source_arg} {watch_args} --json-out {state_report}"
            ),
            (
                "python -m tools.debugger state-space "
                f"{patch_args}{source_arg} {watch_args} "
                f"--base-save-state {quote_arg(base_state)} --out-state {patched_state} "
                f"--execute --json-out {state_report}"
            ),
            (
                "python -m tools.debugger replay "
                f"--report {state_report} --save-state {patched_state} "
                f"{watch_args} --execute-watch"
            ),
            (
                "python -m tools.debugger trace-instructions "
                f"--report {state_report} {trace_args} {watch_args} "
                f"--save-state {patched_state} --execute --require-hit "
                f"--out-trace {trace_path} --json-out {trace_report}"
            ),
            (
                "python -m tools.debugger dynamic-taint "
                f"--report {trace_report} {sink_args}"
            ),
            f"python -m tools.debugger compare --report {state_report} --report {trace_report}",
            (
                "python -m tools.debugger minimize "
                f"--report {state_report} --expect state-patch={banking_first_patch_symbol(patch_specs)},value={banking_first_patch_value(patch_specs)} "
                "--execute-state-patches --out-state-report .local\\tmp\\debugger_banking_minimized.json"
            ),
        ]
    )


def banking_state_space_request(
    *,
    profile_id: str,
    patches: tuple[str, ...],
    report_stem: str,
    source_file: str = "",
) -> dict[str, Any]:
    commands = banking_dynamic_probe_commands(
        report_stem=report_stem,
        patches=patches,
        source_file=source_file,
    )
    return {
        "kind": "banking_abi_state_probe",
        "profile_id": profile_id,
        "patches": list(patches),
        "watch_symbols": list(BANKING_WATCH_SYMBOLS),
        "trace_symbols": list(BANKING_TRACE_SYMBOLS),
        "state_report": f"{report_stem}_state_space.json",
        "out_state": f"{report_stem}.state",
        "trace_report": f"{report_stem}_trace_report.json",
        "trace_output": f"{report_stem}_trace.jsonl",
        "commands": commands,
    }


def banking_first_patch_symbol(patches: tuple[str, ...]) -> str:
    if not patches:
        return "hROMBank"
    return patches[0].split("=", 1)[0].split("+", 1)[0]


def banking_first_patch_value(patches: tuple[str, ...]) -> str:
    if not patches or "=" not in patches[0]:
        return "0x01"
    first_value = patches[0].split("=", 1)[1].split(",", 1)[0].strip()
    try:
        return f"0x{int(first_value, 0):02X}"
    except ValueError:
        return first_value or "0x01"


def banking_patch_expectations(patches: tuple[str, ...]) -> list[str]:
    expectations = []
    for patch in patches:
        if "=" not in patch:
            continue
        symbol, value = patch.split("=", 1)
        expectations.append(f"state-patch={symbol.split('+', 1)[0]},value={banking_first_patch_value((patch,))}")
        if "," in value:
            expectations.append(f"state-patch={symbol.split('+', 1)[0]},byte-count={len(value.split(','))}")
    return unique_list(expectations)


def generator(
    *,
    generator_id: str,
    surface: str,
    title: str,
    confidence: float,
    status: str,
    commands: list[str],
    counterexample_commands: list[str],
    materialization_commands: list[str],
    gaps: list[str],
) -> dict[str, Any]:
    return {
        "id": generator_id,
        "surface": surface,
        "title": title,
        "confidence": confidence,
        "status": status,
        "proof_level": GENERATOR_PROOF_LEVELS.get(surface, "planning"),
        "commands": command_records(commands),
        "counterexample_commands": command_records(counterexample_commands),
        "materialization_commands": command_records(materialization_commands),
        "seed_ids": [],
        "gaps": gaps,
    }


def attach_content_state_materialization_request(record: dict[str, Any], *, scenario_manifest_path: str) -> None:
    scenario_id = str(record.get("id", ""))
    if not scenario_id:
        return
    state_report = f".local\\tmp\\debugger_content_state_{scenario_id}.json"
    state_path = f".local\\tmp\\debugger_content_state_{scenario_id}.state"
    record["proof_level"] = "positioned_state_dynamic_planned"
    record["materialization_request"] = {
        "kind": "content_positioned_state",
        "scenario_id": scenario_id,
        "scenario_manifest": scenario_manifest_path,
        "out_state": state_path,
        "out_report": state_report,
        "precondition_count": len(record.get("state_preconditions", [])),
        "commands": [
            (
                "python -m tools.debugger content-state "
                f"--scenario {scenario_manifest_path} --scenario-id {scenario_id} "
                f"--json-out {state_report}"
            ),
            (
                "python -m tools.debugger content-state "
                f"--scenario {scenario_manifest_path} --scenario-id {scenario_id} "
                f"--base-save-state <base_state> --out-state {state_path} "
                f"--execute --json-out {state_report}"
            ),
            (
                "python -m tools.debugger replay "
                f"--report {state_report} --scenario {scenario_manifest_path} "
                f"--scenario-id {scenario_id} --execute-watch"
            ),
            content_state_instruction_trace_command(
                state_report=state_report,
                scenario_id=scenario_id,
            ),
        ],
    }
    record["commands"] = unique_list(
        [
            *[str(command) for command in record.get("commands", [])],
            *record["materialization_request"]["commands"],
        ]
    )


def build_seed_records(
    *,
    surfaces: list[str],
    generators: list[dict[str, Any]],
    families: tuple[str, ...],
    symbols: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
    seed: int,
    max_cases: int,
    out_scenarios: str,
    root: Path,
) -> list[dict[str, Any]]:
    if not surfaces:
        return []
    content_records = []
    if "content_static" in surfaces:
        content_records = content_scenario_records(
            changed_files=changed_files,
            max_cases=max_cases,
            seed=seed,
            root=root,
        )
        content_records = attach_behavioral_probes(
            scenarios=content_records,
            scenario_manifest_path=(
                display_path(resolve_path(out_scenarios, root=root), root=root)
                if out_scenarios else "<debugger_seed_manifest.jsonl>"
            ),
        )
    records: list[dict[str, Any]] = []
    generator_by_surface = {item["surface"]: item for item in generators}
    for index in range(max_cases):
        surface = surfaces[index % len(surfaces)]
        generator_item = generator_by_surface.get(surface, {})
        if surface == "content_static" and content_records:
            source_record = dict(content_records[index % len(content_records)])
            original_id = str(source_record.get("id", ""))
            source_record["id"] = f"debugger_generated_content_static_{seed}_{index:04d}"
            source_record["case_index"] = index
            if original_id:
                source_record["commands"] = [
                    str(command).replace(original_id, source_record["id"])
                    for command in source_record.get("commands", [])
                ]
                source_record["behavioral_probes"] = [
                    {
                        **probe,
                        "command": str(probe.get("command", "")).replace(original_id, source_record["id"]),
                    }
                    for probe in source_record.get("behavioral_probes", [])
                    if isinstance(probe, dict)
                ]
            if source_record.get("state_preconditions"):
                attach_content_state_materialization_request(
                    source_record,
                    scenario_manifest_path=(
                        display_path(resolve_path(out_scenarios, root=root), root=root)
                        if out_scenarios else "<debugger_seed_manifest.jsonl>"
                    ),
                )
            source_record["requested_families"] = list(families)
            source_record["symptom"] = symptom
            source_record["symbols"] = list(symbols)
            records.append(source_record)
            if generator_item:
                generator_item.setdefault("seed_ids", []).append(source_record["id"])
            continue
        if surface == "banking_abi":
            record_id = f"debugger_generated_banking_abi_{seed}_{index:04d}"
            profile_id, patches = banking_patch_profile(index)
            source_file = normalize_path(changed_files[0]) if changed_files else ""
            request = banking_state_space_request(
                profile_id=profile_id,
                patches=patches,
                report_stem=f".local\\tmp\\debugger_banking_seed_{seed}_{index:04d}",
                source_file=source_file,
            )
            record = {
                "id": record_id,
                "family": surface,
                "source": "tools.debugger.generate",
                "seed": seed,
                "case_index": index,
                "surface": surface,
                "proof_level": "dynamic_state_probe_planned",
                "scenario_type": "banking_abi_state_probe",
                "profile_id": profile_id,
                "symbols": unique_list([*symbols, *BANKING_WATCH_SYMBOLS, *BANKING_TRACE_SYMBOLS]),
                "changed_files": [normalize_path(path) for path in changed_files],
                "symptom": symptom,
                "requested_families": list(families),
                "expected": {
                    "kind": "banking_abi_state_probe",
                    "status": generator_item.get("status", "planned"),
                    "expectations": banking_patch_expectations(patches),
                },
                "state_space_request": request,
                "runtime_targets": {
                    "runtime_route": "banking_abi",
                    "watch_symbols": list(BANKING_WATCH_SYMBOLS),
                    "trace_symbols": list(BANKING_TRACE_SYMBOLS),
                },
                "commands": request["commands"],
            }
            records.append(record)
            if generator_item:
                generator_item.setdefault("seed_ids", []).append(record_id)
            continue
        record_id = f"debugger_generated_{surface}_{seed}_{index:04d}"
        record = {
            "id": record_id,
            "family": surface,
            "source": "tools.debugger.generate",
            "seed": seed,
            "case_index": index,
            "surface": surface,
            "symbols": list(symbols),
            "changed_files": [normalize_path(path) for path in changed_files],
            "symptom": symptom,
            "requested_families": list(families),
            "expected": {
                "kind": "counterexample_seed",
                "status": generator_item.get("status", "planned"),
            },
            "commands": [
                item["command"]
                for item in generator_item.get("commands", [])[:4]
            ],
        }
        records.append(record)
        if generator_item:
            generator_item.setdefault("seed_ids", []).append(record_id)
    return records


def write_seed_records(
    *,
    records: list[dict[str, Any]],
    out_scenarios: str,
    root: Path,
) -> dict[str, Any]:
    if not out_scenarios:
        return {"path": "", "written": False, "record_count": len(records), "errors": []}
    path = resolve_path(out_scenarios, root=root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
            encoding="utf-8",
            newline="\n",
        )
    except OSError as exc:
        return {
            "path": display_path(path, root=root),
            "written": False,
            "record_count": 0,
            "errors": [str(exc)],
        }
    return {
        "path": display_path(path, root=root),
        "written": True,
        "record_count": len(records),
        "errors": [],
    }


def build_materialization_steps(
    *,
    surfaces: list[str],
    generators: list[dict[str, Any]],
    out_scenarios: str,
    families: tuple[str, ...],
    reports: tuple[str, ...],
    symbols: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
    seed: int,
    max_cases: int,
) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    seed_path = out_scenarios or "<debugger_seed_manifest.jsonl>"
    add_step(
        steps,
        "seed",
        self_generation_command(
            families=families,
            symbols=symbols,
            changed_files=changed_files,
            symptom=symptom,
            seed=seed,
            max_cases=max_cases,
            out_scenarios=seed_path,
        ),
        "Write or refresh the unified seed manifest for the inferred ROM surfaces.",
    )
    for generator_item in generators:
        for command in generator_item.get("commands", [])[:4]:
            add_step(
                steps,
                "generate",
                command["command"],
                f"Generate candidate cases for {generator_item['surface']}.",
            )
        for command in generator_item.get("materialization_commands", [])[:6]:
            scenario_path = subsystem_scenario_path(generator_item)
            concrete = command["command"].replace("<scenarios.jsonl>", scenario_path)
            add_step(
                steps,
                "materialize",
                concrete,
                f"Prove generated {generator_item['surface']} cases against ROM behavior when supported.",
            )
    for report in reports[:3]:
        add_step(
            steps,
            "rank",
            f"python -m tools.debugger rank --report {report}",
            "Fold generated evidence into the unified ranked finding queue.",
        )
    for symbol in symbols[:3]:
        add_step(
            steps,
            "explain",
            f"python -m tools.debugger explain --symbol {symbol}",
            "Connect generated or replayed behavior to source and state provenance.",
        )
    for path in changed_files[:3]:
        add_step(
            steps,
            "verify",
            f"python -m tools.debugger gate --changed-file {path}",
            "Run the ROM-aware verification gates for the touched surface.",
        )
    if symptom and not changed_files and not symbols:
        add_step(
            steps,
            "localize",
            f"python -m tools.debugger localize --symptom {quote_arg(symptom)}",
            "Localize symptom text before requesting a more specific generator.",
        )
    return unique_steps(steps)


def self_generation_command(
    *,
    families: tuple[str, ...],
    symbols: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
    seed: int,
    max_cases: int,
    out_scenarios: str,
) -> str:
    parts = ["python -m tools.debugger generate"]
    for family in families:
        parts.append(f"--family {quote_arg(family)}")
    for symbol in symbols:
        parts.append(f"--symbol {quote_arg(symbol)}")
    for path in changed_files:
        parts.append(f"--changed-file {quote_arg(path)}")
    if symptom:
        parts.append(f"--symptom {quote_arg(symptom)}")
    parts.append(f"--max-cases {max_cases}")
    parts.append(f"--seed {seed}")
    parts.append(f"--out-scenarios {quote_arg(out_scenarios)}")
    return " ".join(parts)


def build_dynamic_taint_handoffs(
    *,
    loaded_reports: list[dict[str, Any]],
    root: Path,
) -> list[dict[str, Any]]:
    handoffs: list[dict[str, Any]] = []
    seen_commands: set[str] = set()
    for loaded in loaded_reports:
        data = loaded.get("data")
        source = str(loaded.get("source", ""))
        if not isinstance(data, dict) or not source:
            continue
        if data.get("kind") != "unified_debugger_instruction_trace":
            continue
        validation = data.get("execution_validation") if isinstance(data.get("execution_validation"), dict) else {}
        if not validation.get("ready_for_dynamic_taint"):
            continue
        discovered = discover_dynamic_taint_inputs_from_report(
            data,
            source=source,
            report_path=loaded.get("path"),
            root=root,
        )
        has_sink = bool(discovered.get("sink_symbols") or discovered.get("sink_addresses"))
        if not discovered.get("traces") or not has_sink:
            continue
        command = f"python -m tools.debugger dynamic-taint --report {quote_arg(source)}"
        if command in seen_commands:
            continue
        seen_commands.add(command)
        handoffs.append(
            {
                "id": f"instruction_trace_dynamic_taint_{len(handoffs):04d}",
                "source_report": source,
                "status": "ready",
                "proof_level": "dynamic_trace",
                "trace_count": len(discovered.get("traces", [])),
                "traces": list(discovered.get("traces", [])),
                "sink_symbols": list(discovered.get("sink_symbols", [])),
                "sink_addresses": list(discovered.get("sink_addresses", [])),
                "source_regs": list(discovered.get("source_regs", [])),
                "source_mems": list(discovered.get("source_mems", [])),
                "source_symbols": list(discovered.get("source_symbols", [])),
                "related_symbols": dynamic_taint_related_symbols(discovered),
                "related_addresses": dynamic_taint_related_addresses(discovered),
                "trace_candidates": list(discovered.get("trace_candidates", [])),
                "command": command,
                "runnable": command_is_runnable(command),
                "reason": (
                    "Instruction trace validation reported an executed hook hit "
                    "and a written trace artifact with dynamic-taint sinks."
                ),
            }
        )
    return handoffs


def collect_counterexamples(
    *,
    tests: dict[str, Any],
    minimization: dict[str, Any],
    generators: list[dict[str, Any]],
    dynamic_taint_handoffs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    counterexamples: list[dict[str, Any]] = []
    matched_test_counterexamples = False
    for match in tests.get("matches", []):
        commands = string_items(match.get("counterexample_commands"))
        if not commands:
            continue
        matched_test_counterexamples = True
        reason = "; ".join(string_items(match.get("notes"))[:4])
        for command in commands:
            counterexamples.append(
                counterexample(
                    "suggest-tests",
                    "",
                    command,
                    reason=reason,
                    related_symbols=string_items(match.get("related_symbols")),
                    related_addresses=string_items(match.get("related_addresses")),
                )
            )
    if not matched_test_counterexamples:
        for command in tests.get("counterexample_commands", []):
            counterexamples.append(counterexample("suggest-tests", "", command))
    for step in minimization.get("steps", []):
        if step.get("phase") in {"find", "counterfactual", "minimize", "replay", "prove"}:
            counterexamples.append(
                counterexample(
                    "minimize",
                    "",
                    str(step.get("command", "")),
                    reason=str(step.get("reason", "")),
                )
            )
    for generator_item in generators:
        surface = str(generator_item.get("surface", ""))
        for command in generator_item.get("counterexample_commands", []):
            counterexamples.append(
                counterexample(
                    "generator",
                    surface,
                    str(command.get("command", "")),
                    reason=f"Counterexample command for {surface}.",
                )
            )
    for handoff in dynamic_taint_handoffs:
        counterexamples.append(
            counterexample(
                "dynamic-taint",
                "instruction_trace",
                str(handoff.get("command", "")),
                reason=str(handoff.get("reason", "")),
                related_symbols=dynamic_taint_related_symbols(handoff),
                related_addresses=dynamic_taint_related_addresses(handoff),
            )
        )
    return unique_counterexamples(counterexamples)


def subsystem_scenario_path(generator_item: dict[str, Any]) -> str:
    if generator_item.get("surface") == "boss_ai":
        return ".local\\tmp\\debugger_boss_ai_generated.jsonl"
    return "<scenarios.jsonl>"


def counterexample(
    source: str,
    surface: str,
    command: str,
    *,
    reason: str = "",
    related_symbols: list[str] | None = None,
    related_addresses: list[str] | None = None,
) -> dict[str, Any]:
    item = {
        "source": source,
        "surface": surface,
        "command": command,
        "reason": reason,
        "runnable": command_is_runnable(command),
    }
    if related_symbols:
        item["related_symbols"] = unique_list(related_symbols)
    if related_addresses:
        item["related_addresses"] = unique_list(related_addresses)
    return item


def command_records(commands: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "command": command,
            "runnable": command_is_runnable(command),
        }
        for command in commands
    ]


def commands_from_generators(generators: list[dict[str, Any]]) -> list[str]:
    commands: list[str] = []
    for generator_item in generators:
        for key in ("commands", "counterexample_commands", "materialization_commands"):
            commands.extend(item["command"] for item in generator_item.get(key, []))
    return commands


def commands_from_seed_records(records: list[dict[str, Any]]) -> list[str]:
    commands: list[str] = []
    for record in records:
        commands.extend(str(command) for command in record.get("commands", []))
        for probe in record.get("behavioral_probes", []):
            if isinstance(probe, dict):
                commands.append(str(probe.get("command", "")))
    return commands


def add_step(steps: list[dict[str, Any]], phase: str, command: str, reason: str) -> None:
    if not command:
        return
    steps.append(
        {
            "phase": phase,
            "command": command,
            "reason": reason,
            "runnable": command_is_runnable(command),
        }
    )


def signal(
    signal_type: str,
    kind: str,
    value: str,
    weight: int,
    source: str,
) -> dict[str, Any]:
    return {
        "type": signal_type,
        "kind": kind,
        "value": value,
        "weight": int(weight),
        "source": source,
    }


def merge_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in signals:
        value = str(item.get("value", ""))
        if not value:
            continue
        key = (str(item.get("type", "")), str(item.get("kind", "")), value)
        if key not in merged:
            merged[key] = dict(item)
            continue
        merged[key]["weight"] = max(int(merged[key]["weight"]), int(item.get("weight", 0)))
    return sorted(merged.values(), key=lambda item: (-int(item["weight"]), item["kind"], item["value"]))


def unique_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for step in steps:
        command = step["command"]
        if command in seen:
            continue
        seen.add(command)
        out.append(step)
    return out


def unique_counterexamples(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        command = item["command"]
        if not command or command in seen:
            continue
        seen.add(command)
        out.append(item)
    return out


def string_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list | tuple | set):
        return [nested for item in value for nested in string_items(item)]
    return [str(value)] if value else []


def dynamic_taint_related_symbols(data: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            *string_items(data.get("sink_symbols")),
            *string_items(data.get("source_symbols")),
            *source_mem_origins(data),
        ]
    )


def dynamic_taint_related_addresses(data: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            *string_items(data.get("sink_addresses")),
            *source_mem_addresses(data),
        ]
    )


def source_mem_origins(data: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            origin
            for _, origin in source_mem_parts(data)
            if origin
        ]
    )


def source_mem_addresses(data: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            address
            for address, _ in source_mem_parts(data)
            if address
        ]
    )


def source_mem_parts(data: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for value in string_items(data.get("source_mems")):
        text = str(value).strip()
        if not text:
            continue
        if "=" in text:
            left, right = (part.strip() for part in text.split("=", 1))
            if looks_like_address(left):
                out.append((left, right))
            elif looks_like_address(right):
                out.append((right, left))
            else:
                out.append((left, right))
        else:
            out.append((text, ""))
    return out


def looks_like_address(value: str) -> bool:
    text = str(value).strip().replace("$", "")
    if ":" in text:
        bank, address = text.split(":", 1)
        return is_hex(bank, 2) and is_hex(address, 4)
    return is_hex(text, 4)


def is_hex(value: str, length: int) -> bool:
    text = str(value).strip()
    return len(text) == length and all(char in "0123456789abcdefABCDEF" for char in text)


def quote_arg(value: str) -> str:
    if not value:
        return "\"\""
    if any(char.isspace() for char in value) or any(char in value for char in "\"'"):
        return '"' + value.replace('"', '\\"') + '"'
    return value
