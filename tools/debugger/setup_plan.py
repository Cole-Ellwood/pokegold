from __future__ import annotations

from pathlib import Path
from typing import Any

from .catalog import ROOT
from .generate import SURFACE_ORDER, SURFACE_RULES, keyword_matches, normalize_surface
from .localize import normalize_path
from .minimize import load_scenario_files, scenario_id_for, unique_list
from .reporting import load_reports
from .runtime_watch import DEFAULT_ROM, DEFAULT_SYMBOLS
from .workflow import command_is_runnable


DEFAULT_SETUP_SCENARIOS = ".local\\tmp\\debugger_setup_scenarios.jsonl"
CONTENT_MAP_WATCH_SYMBOLS = ("wMapGroup", "wMapNumber", "wXCoord", "wYCoord")
CONTENT_RUNTIME_HELPERS_BY_PREFIX = (
    ("maps/", ("ReadMapEvents", "WarpCheck", "CheckCurrentMapCoordEvents", "CheckFacingBGEvent", "TryObjectEvent")),
    ("scripts/", ("CallScript", "QueueScript")),
    ("audio/", ("PlayMusic",)),
    ("gfx/", ("Request2bpp", "Get1bpp", "Decompress")),
)
NEXT_STEP_SETUP_TARGETS_BY_CLASS = {
    "wrong_switch": {
        "symbols": ("BossAI_SwitchOrTryItem",),
        "watch_symbols": ("wEnemySwitchMonIndex", "wEnemySwitchMonParam", "wEnemyAIMoveScores"),
    },
    "wrong_move_score": {
        "symbols": ("BossAI_SelectMove",),
        "watch_symbols": ("wEnemyAIMoveScores",),
    },
}
NEXT_STEP_SETUP_TARGETS_BY_LANE = {
    "boss_ai": {
        "symbols": ("BossAI_SelectMove",),
        "watch_symbols": ("wEnemyAIMoveScores",),
    },
    "damage": {
        "symbols": ("BattleCommand_DamageCalc",),
        "watch_symbols": ("wCurDamage",),
    },
    "banking_abi": {
        "symbols": ("FarCall",),
        "watch_symbols": ("hROMBank",),
    },
}
SETUP_SOURCE_EXTENSIONS = {".asm", ".inc", ".py"}


def build_setup_plan(
    *,
    rom_path: str = "",
    symbols_path: str = DEFAULT_SYMBOLS,
    save_state: str = "",
    reports: tuple[str, ...] = (),
    scenarios: tuple[str, ...] = (),
    scenario_ids: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    watch_symbols: tuple[str, ...] = (),
    symptom: str = "",
    frames: int = 300,
    out_scenarios: str = "",
    root: Path = ROOT,
) -> dict[str, Any]:
    effective_rom = rom_path or DEFAULT_ROM
    scenario_path = out_scenarios or DEFAULT_SETUP_SCENARIOS
    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    loaded_scenarios, scenario_errors = load_scenario_files(
        scenarios=scenarios,
        root=root,
    )
    discovered_save_states = discover_save_states(
        loaded_reports=loaded_reports,
        loaded_scenarios=loaded_scenarios,
        scenario_ids=scenario_ids,
        explicit_save_state=save_state,
        root=root,
    )
    selected_save_state = select_save_state(discovered_save_states)
    effective_save_state = save_state or str(selected_save_state.get("path", ""))
    signals = collect_setup_signals(
        loaded_reports=loaded_reports,
        loaded_scenarios=loaded_scenarios,
        scenario_ids=scenario_ids,
        changed_files=changed_files,
        symbols=symbols,
        watch_symbols=watch_symbols,
        symptom=symptom,
    )
    effective_symbols = tuple(unique_list([*symbols, *signal_values(signals, kind="symbol", signal_type_prefix="next_step_trace_")]))
    effective_watch_symbols = tuple(unique_list([*watch_symbols, *signal_values(signals, kind="symbol", signal_type_prefix="next_step_watch_")]))
    effective_changed_files = tuple(unique_list([*[normalize_path(path) for path in changed_files], *signal_values(signals, kind="file", signal_type_prefix="next_step_source_")]))
    surfaces = infer_setup_surfaces(signals)
    content_scenarios = collect_content_setup_scenarios(
        loaded_reports=loaded_reports,
        loaded_scenarios=loaded_scenarios,
        scenario_ids=scenario_ids,
    )
    targets = [
        build_surface_setup_target(
            surface=surface,
            effective_rom=effective_rom,
            symbols_path=symbols_path,
            save_state=effective_save_state,
            scenario_path=scenario_path,
            changed_files=effective_changed_files,
            symbols=effective_symbols,
            watch_symbols=effective_watch_symbols,
            scenario_ids=scenario_ids,
            content_scenarios=content_scenarios,
            symptom=symptom,
            frames=frames,
        )
        for surface in surfaces
    ]
    commands = unique_list(
        command
        for target in targets
        for command in target.get("commands", [])
    )
    trigger_coverage = build_trigger_coverage(
        targets=targets,
        save_state=save_state,
        selected_save_state=selected_save_state,
    )
    dynamic_targets = [
        target for target in targets if target.get("requires_positioned_state")
    ]
    warnings = []
    if dynamic_targets and not effective_save_state:
        warnings.append(
            "no save state was supplied; use the setup/materialization commands before treating runtime proof commands as final"
        )
    errors = unique_list([*report_errors, *scenario_errors])
    return {
        "schema_version": 1,
        "kind": "unified_debugger_setup_plan",
        "root": str(root),
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "rom": effective_rom,
        "symbols_path": symbols_path,
        "save_state": save_state,
        "effective_save_state": effective_save_state,
        "save_state_discovery": {
            "candidate_count": len(discovered_save_states),
            "selected": selected_save_state,
            "candidates": discovered_save_states[:40],
        },
        "frames": frames,
        "scenario_manifest": scenario_path,
        "reports": [item["source"] for item in loaded_reports],
        "scenarios": [item["source"] for item in loaded_scenarios],
        "input_scenario_ids": list(scenario_ids),
        "changed_files": [normalize_path(path) for path in changed_files],
        "symbols": list(symbols),
        "watch_symbols": list(watch_symbols),
        "effective_changed_files": list(effective_changed_files),
        "effective_symbols": list(effective_symbols),
        "effective_watch_symbols": list(effective_watch_symbols),
        "symptom": symptom,
        "signal_count": len(signals),
        "signals": signals[:160],
        "surface_count": len(surfaces),
        "surfaces": surfaces,
        "target_count": len(targets),
        "targets": targets,
        "state_requirements": {
            "save_state_supplied": bool(save_state),
            "save_state_discovered": bool(selected_save_state),
            "requires_positioned_state": bool(dynamic_targets),
            "dynamic_surface_count": len(dynamic_targets),
            "scenario_manifest": scenario_path,
            "scenario_ids": list(scenario_ids),
            "content_scenario_count": len(content_scenarios),
            "content_scenario_ids": [str(item.get("id", "")) for item in content_scenarios[:16] if item.get("id")],
        },
        "trigger_coverage": trigger_coverage,
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "This plans ROM setup, state synthesis recipes, trigger, and validation commands; it does not yet synthesize every possible save state by itself.",
            "Damage and Boss AI surfaces have dedicated state synthesis/materialization recipes; content, UI, audio, and banking surfaces still rely on scenario manifests, audits, watches, and targeted replay.",
            "Use trace-instructions with --require-hit after setup to prove the selected trigger actually reached the intended code window.",
        ],
    }


def discover_save_states(
    *,
    loaded_reports: list[dict[str, Any]],
    loaded_scenarios: list[dict[str, Any]],
    scenario_ids: tuple[str, ...],
    explicit_save_state: str,
    root: Path,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    if explicit_save_state:
        candidates.append(
            save_state_candidate(
                path=explicit_save_state,
                source="input",
                key="save_state",
                scenario_id="",
                explicit=True,
                root=root,
            )
        )
    selected_ids = {str(item) for item in scenario_ids if item}
    for loaded in loaded_scenarios:
        source = str(loaded.get("source", "scenario"))
        for record in loaded.get("records", []):
            if not isinstance(record, dict):
                continue
            scenario_id = setup_scenario_id_for(record)
            preferred = not selected_ids or scenario_id in selected_ids
            collect_save_state_candidates(
                record,
                source=source,
                scenario_id=scenario_id,
                preferred=preferred,
                selected_ids=selected_ids,
                root=root,
                out=candidates,
            )
    for loaded in loaded_reports:
        data = loaded.get("data", {})
        if isinstance(data, dict):
            collect_save_state_candidates(
                data,
                source=str(loaded.get("source", "report")),
                scenario_id=str(data.get("scenario_id", "")),
                preferred=True,
                selected_ids=selected_ids,
                root=root,
                out=candidates,
            )
    return sorted(
        unique_candidates(candidates),
        key=lambda item: (
            not bool(item.get("explicit")),
            not bool(item.get("preferred")),
            not bool(item.get("exists")),
            str(item.get("source", "")),
            str(item.get("path", "")),
        ),
    )


def collect_save_state_candidates(
    value: Any,
    *,
    source: str,
    scenario_id: str,
    preferred: bool,
    selected_ids: set[str],
    root: Path,
    out: list[dict[str, Any]],
) -> None:
    if isinstance(value, dict):
        local_scenario_id = setup_scenario_id_for(value) or scenario_id
        local_preferred = preferred or (local_scenario_id in selected_ids if selected_ids else False)
        for key, nested in value.items():
            lowered = str(key).lower()
            if isinstance(nested, str) and is_save_state_key(lowered) and looks_like_save_state_path(nested):
                out.append(
                    save_state_candidate(
                        path=nested,
                        source=source,
                        key=str(key),
                        scenario_id=local_scenario_id,
                        explicit=False,
                        preferred=local_preferred,
                        root=root,
                    )
                )
            collect_save_state_candidates(
                nested,
                source=source,
                scenario_id=local_scenario_id,
                preferred=local_preferred,
                selected_ids=selected_ids,
                root=root,
                out=out,
            )
    elif isinstance(value, list):
        for item in value:
            collect_save_state_candidates(
                item,
                source=source,
                scenario_id=scenario_id,
                preferred=preferred,
                selected_ids=selected_ids,
                root=root,
                out=out,
            )


def save_state_candidate(
    *,
    path: str,
    source: str,
    key: str,
    scenario_id: str,
    explicit: bool,
    root: Path,
    preferred: bool = True,
) -> dict[str, Any]:
    resolved = resolve_input_path(path, root=root)
    return {
        "path": display_input_path(resolved, root=root),
        "raw_path": str(path),
        "source": source,
        "key": key,
        "scenario_id": scenario_id,
        "explicit": explicit,
        "preferred": preferred,
        "exists": resolved.exists(),
    }


def select_save_state(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    for candidate in candidates:
        if candidate.get("explicit"):
            return candidate
    for candidate in candidates:
        if candidate.get("preferred") and candidate.get("exists"):
            return candidate
    for candidate in candidates:
        if candidate.get("exists"):
            return candidate
    return {}


def unique_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    seen: set[tuple[str, str, str]] = set()
    for candidate in candidates:
        key = (
            str(candidate.get("path", "")),
            str(candidate.get("source", "")),
            str(candidate.get("scenario_id", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(candidate)
    return out


def is_save_state_key(key: str) -> bool:
    lowered = key.lower()
    return lowered == "state" or lowered.endswith("_state") or "save_state" in lowered


def looks_like_save_state_path(value: str) -> bool:
    text = value.strip()
    if not text or text.startswith(("route:", "scenario:")):
        return False
    suffix = Path(text).suffix.lower()
    return suffix in {".state", ".sgm", ".sav"} or "/" in text or "\\" in text


def collect_setup_signals(
    *,
    loaded_reports: list[dict[str, Any]],
    loaded_scenarios: list[dict[str, Any]],
    scenario_ids: tuple[str, ...],
    changed_files: tuple[str, ...],
    symbols: tuple[str, ...],
    watch_symbols: tuple[str, ...],
    symptom: str,
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for symbol in symbols:
        signals.append(signal("input_symbol", "symbol", symbol, 90, "input"))
    for symbol in watch_symbols:
        signals.append(signal("input_watch", "symbol", symbol, 95, "input"))
    for path in changed_files:
        signals.append(signal("input_file", "file", normalize_path(path), 90, "input"))
    for scenario_id in scenario_ids:
        signals.append(signal("input_scenario_id", "scenario", scenario_id, 85, "input"))
    if symptom:
        signals.append(signal("input_symptom", "note", symptom, 70, "input"))

    for loaded in loaded_reports:
        data = loaded["data"]
        kind = str(data.get("kind", "report"))
        signals.append(signal("report_kind", "note", kind, 40, loaded["source"]))
        collect_report_setup_signals(data, source=loaded["source"], out=signals)

    for loaded in loaded_scenarios:
        for record in loaded["records"]:
            scenario_id = setup_scenario_id_for(record)
            if scenario_id:
                signals.append(signal("scenario_record", "scenario", scenario_id, 55, loaded["source"]))
            for key in ("family", "surface", "kind", "type"):
                value = record.get(key)
                if isinstance(value, str) and value:
                    signals.append(signal(f"scenario_{key}", "note", value, 45, loaded["source"]))
            for key in ("source_file", "path", "file"):
                value = record.get(key)
                if isinstance(value, str) and value:
                    signals.append(signal(f"scenario_{key}", "file", normalize_path(value), 45, loaded["source"]))
    return merge_signals(signals)


def collect_report_setup_signals(data: Any, *, source: str, out: list[dict[str, Any]]) -> None:
    if isinstance(data, dict):
        out.extend(next_step_setup_signals(data, source=source))
        for key, value in data.items():
            lowered = str(key).lower()
            if lowered in {"symbol", "watch", "state_symbol", "pc_symbol", "source_symbol", "resolved", "query"}:
                for item in string_items(value):
                    out.append(signal(f"report_{lowered}", "symbol", item, 45, source))
            elif lowered in {"path", "file", "source_file", "changed_file"}:
                for item in string_items(value):
                    out.append(signal(f"report_{lowered}", "file", normalize_path(item), 45, source))
            elif lowered in {"scenario_id", "id", "capture_id", "trace_id"}:
                for item in string_items(value):
                    out.append(signal(f"report_{lowered}", "scenario", item, 35, source))
            elif lowered in {"surface", "surface_id", "family", "kind", "type"}:
                for item in string_items(value):
                    out.append(signal(f"report_{lowered}", "note", item, 30, source))
            collect_report_setup_signals(value, source=source, out=out)
    elif isinstance(data, list):
        for item in data:
            collect_report_setup_signals(item, source=source, out=out)


def next_step_setup_signals(data: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for next_step in embedded_next_step_reports(data):
        recommendation = next_step.get("recommendation")
        if not isinstance(recommendation, dict):
            continue
        lane = str(recommendation.get("matched_lane") or next_step.get("matched_lane") or "")
        surface = normalize_surface(lane)
        if surface:
            out.append(signal("next_step_surface", "note", surface, 130, source))
        targets = next_step_setup_targets(recommendation)
        for index, symbol in enumerate(targets["symbols"]):
            if looks_like_runtime_symbol(symbol):
                out.append(signal("next_step_trace_symbol", "symbol", symbol, max(90, 120 - index), source))
        for index, symbol in enumerate(targets["watch_symbols"]):
            if looks_like_runtime_symbol(symbol):
                out.append(signal("next_step_watch_symbol", "symbol", symbol, max(90, 125 - index), source))
        for path in string_items(recommendation.get("source_refs")):
            if looks_like_setup_source_path(path):
                out.append(signal("next_step_source_ref", "file", normalize_path(path), 100, source))
    return out


def embedded_next_step_reports(data: dict[str, Any]) -> list[dict[str, Any]]:
    if data.get("kind") == "unified_debugger_next_step":
        return [data]
    next_step = data.get("symptom_only_next_step")
    if isinstance(next_step, dict) and next_step.get("kind") == "unified_debugger_next_step":
        return [next_step]
    return []


def next_step_setup_targets(recommendation: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    symptom_class = str(recommendation.get("symptom_class") or "")
    lane = str(recommendation.get("matched_lane") or "")
    targets = (
        NEXT_STEP_SETUP_TARGETS_BY_CLASS.get(symptom_class)
        or NEXT_STEP_SETUP_TARGETS_BY_LANE.get(lane)
        or {"symbols": (), "watch_symbols": ()}
    )
    return {
        "symbols": tuple(targets["symbols"]),
        "watch_symbols": tuple(targets["watch_symbols"]),
    }


def collect_content_setup_scenarios(
    *,
    loaded_reports: list[dict[str, Any]],
    loaded_scenarios: list[dict[str, Any]],
    scenario_ids: tuple[str, ...],
) -> list[dict[str, Any]]:
    selected_ids = {str(item) for item in scenario_ids if item}
    scenarios: list[dict[str, Any]] = []
    for loaded in loaded_reports:
        data = loaded.get("data", {})
        if not isinstance(data, dict):
            continue
        if data.get("kind") == "unified_debugger_content_scenarios":
            for scenario in dict_items(data.get("scenarios")):
                scenarios.append(scenario_with_setup_source(scenario, source=str(loaded.get("source", ""))))
        elif data.get("kind") == "unified_debugger_content_scenario" or data.get("scenario_type"):
            scenarios.append(scenario_with_setup_source(data, source=str(loaded.get("source", ""))))
    for loaded in loaded_scenarios:
        for record in loaded.get("records", []):
            if isinstance(record, dict) and (record.get("kind") == "unified_debugger_content_scenario" or record.get("scenario_type")):
                scenarios.append(scenario_with_setup_source(record, source=str(loaded.get("source", ""))))
    out = []
    seen: set[str] = set()
    for scenario in scenarios:
        scenario_id = setup_scenario_id_for(scenario)
        if selected_ids and scenario_id not in selected_ids:
            continue
        key = scenario_id or f"{scenario.get('source_file', '')}:{scenario.get('line', '')}:{scenario.get('scenario_type', '')}"
        if key in seen:
            continue
        seen.add(key)
        copied = dict(scenario)
        if scenario_id:
            copied["id"] = scenario_id
        out.append(copied)
    return out


def scenario_with_setup_source(scenario: dict[str, Any], *, source: str) -> dict[str, Any]:
    copied = dict(scenario)
    if source:
        copied.setdefault("_setup_source", source)
    return copied


def setup_scenario_id_for(record: dict[str, Any]) -> str:
    if record.get("kind") == "unified_debugger_fuzz_case":
        scenario_id = record.get("scenario_id")
        if isinstance(scenario_id, str) and scenario_id:
            return scenario_id
    for key in ("id", "scenario_id", "capture_id", "trace_id"):
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    return scenario_id_for(record)


def infer_setup_surfaces(signals: list[dict[str, Any]]) -> list[str]:
    routed_surfaces = unique_list(
        normalize_surface(str(item.get("value", "")))
        for item in signals
        if item.get("type") == "next_step_surface"
    )
    routed_surfaces = [surface for surface in routed_surfaces if surface]
    if routed_surfaces:
        explicit_scores = score_setup_surfaces(
            [
                item for item in signals
                if str(item.get("type", "")).startswith("input_") and item.get("type") != "input_symptom"
            ]
        )
        explicit_surfaces = [
            surface for surface in SURFACE_ORDER
            if surface != "general" and explicit_scores.get(surface, 0) > 0
        ]
        selected = [
            surface for surface in SURFACE_ORDER
            if surface != "general" and surface in {*routed_surfaces, *explicit_surfaces}
        ]
        return selected or routed_surfaces

    scores = score_setup_surfaces(signals)
    selected = [
        surface for surface in SURFACE_ORDER
        if surface != "general" and scores.get(surface, 0) > 0
    ]
    if not selected:
        selected = ["general"]
    return selected


def score_setup_surfaces(signals: list[dict[str, Any]]) -> dict[str, int]:
    scores = {surface: 0 for surface in SURFACE_ORDER}
    for item in signals:
        value = str(item.get("value", ""))
        kind = str(item.get("kind", ""))
        weight = int(item.get("weight", 0))
        surface = normalize_surface(value)
        if surface:
            scores[surface] += weight
        if kind == "file":
            for matched in surfaces_for_path(value):
                scores[matched] += weight
        elif kind == "symbol":
            for matched in surfaces_for_symbol(value):
                scores[matched] += weight
        else:
            text = value.lower().replace("\\", "/")
            for matched in surfaces_for_text(text):
                scores[matched] += weight

    if scores["damage"] and scores["content_static"]:
        scores["content_static"] = max(scores["content_static"], scores["damage"] // 2)
    return scores


def surfaces_for_path(path: str) -> list[str]:
    normalized = normalize_path(path).lower()
    matches = []
    for surface, rule in SURFACE_RULES.items():
        if any(
            normalized.startswith(prefix.lower()) or f"/{prefix.lower()}" in normalized
            for prefix in rule["path_prefixes"]
        ):
            matches.append(surface)
    if normalized.startswith("data/") and "damage" in matches and not normalized.startswith(("data/moves/", "data/pokemon/base_stats/")):
        matches.append("content_static")
    return unique_list(matches)


def surfaces_for_symbol(symbol: str) -> list[str]:
    text = str(symbol).lower()
    matches = []
    for surface, rule in SURFACE_RULES.items():
        for hint in rule["symbols"]:
            if hint.lower() in text:
                matches.append(surface)
    if text.startswith(("bossai_", "wbossai", "wenemyai")):
        matches.append("boss_ai")
    if text in {"wcurdamage", "battlecommand_damage", "battlecommand_damagecalc"}:
        matches.append("damage")
    if text in {"hrombank", "hloadedrombank"} or "farcall" in text or "bankswitch" in text:
        matches.append("banking_abi")
    return unique_list(matches)


def surfaces_for_text(text: str) -> list[str]:
    matches = []
    for surface, rule in SURFACE_RULES.items():
        if surface in text or surface.replace("_", " ") in text:
            matches.append(surface)
        elif any(keyword_matches(keyword, text) for keyword in rule["keywords"]):
            matches.append(surface)
    return unique_list(matches)


def build_surface_setup_target(
    *,
    surface: str,
    effective_rom: str,
    symbols_path: str,
    save_state: str,
    scenario_path: str,
    changed_files: tuple[str, ...],
    symbols: tuple[str, ...],
    watch_symbols: tuple[str, ...],
    scenario_ids: tuple[str, ...],
    content_scenarios: list[dict[str, Any]],
    symptom: str,
    frames: int,
) -> dict[str, Any]:
    if surface == "damage":
        watch = first_symbol(watch_symbols, default="wCurDamage")
        trace_symbol = first_matching_symbol(symbols, ("BattleCommand_",), default="BattleCommand_DamageCalc")
        state_recipes = damage_state_synthesis_recipes(
            symbols=symbols,
            changed_files=changed_files,
            symptom=symptom,
            scenario_path=scenario_path,
            watch=watch,
        )
        setup_commands = [
            generation_command(surface="damage", symbols=symbols, changed_files=changed_files, symptom=symptom, scenario_path=scenario_path),
        ]
        trigger_commands = [
            replay_command(
                effective_rom=effective_rom,
                symbols_path=symbols_path,
                save_state=save_state,
                watch=watch,
                frames=frames,
            ),
        ]
        validation_commands = [
            trace_instruction_command(
                effective_rom=effective_rom,
                symbols_path=symbols_path,
                save_state=save_state,
                trace_symbol=trace_symbol,
                watch=watch,
                frames=frames,
                out_trace=".local\\tmp\\debugger_setup_damage_trace.jsonl",
            ),
        ]
        return setup_target(
            surface=surface,
            title="Damage-chain setup and trigger plan",
            requires_positioned_state=True,
            setup_commands=setup_commands,
            state_synthesis_recipes=state_recipes,
            state_recipe_commands=commands_from_recipes(state_recipes),
            trigger_commands=trigger_commands,
            validation_commands=validation_commands,
        )

    if surface == "boss_ai":
        watch = first_symbol(watch_symbols, default="wEnemyAIMoveScores")
        trace_symbol = first_matching_symbol(symbols, ("BossAI_",), default="BossAI_SelectMove")
        state_recipes = boss_ai_state_synthesis_recipes(
            scenario_ids=scenario_ids,
            symbols=symbols,
            changed_files=changed_files,
            symptom=symptom,
            scenario_path=scenario_path,
        )
        setup_commands = [
            generation_command(surface="boss_ai", symbols=symbols, changed_files=changed_files, symptom=symptom, scenario_path=scenario_path),
        ]
        trigger_commands = [
            replay_command(
                effective_rom=effective_rom,
                symbols_path=symbols_path,
                save_state=save_state,
                watch=watch,
                frames=frames,
            ),
        ]
        validation_commands = [
            trace_instruction_command(
                effective_rom=effective_rom,
                symbols_path=symbols_path,
                save_state=save_state,
                trace_symbol=trace_symbol,
                watch=watch,
                frames=frames,
                out_trace=".local\\tmp\\debugger_setup_boss_ai_trace.jsonl",
            ),
        ]
        return setup_target(
            surface=surface,
            title="Boss AI materialization and trigger plan",
            requires_positioned_state=True,
            setup_commands=setup_commands,
            state_synthesis_recipes=state_recipes,
            state_recipe_commands=commands_from_recipes(state_recipes),
            trigger_commands=trigger_commands,
            validation_commands=validation_commands,
        )

    if surface == "banking_abi":
        state_recipes = banking_state_synthesis_recipes(watch=first_symbol(watch_symbols, default="hROMBank"))
        setup_commands = [
            "python tools\\audit\\check_farcall_a_clobber.py",
            "python tools\\audit\\check_farcall_hl_clobber.py",
            "python tools\\audit\\check_cross_bank_call.py",
        ]
        trigger_commands = [
            replay_command(
                effective_rom=effective_rom,
                symbols_path=symbols_path,
                save_state=save_state,
                watch=first_symbol(watch_symbols, default="hROMBank"),
                frames=frames,
            ),
        ]
        validation_commands = [
            trace_instruction_command(
                effective_rom=effective_rom,
                symbols_path=symbols_path,
                save_state=save_state,
                trace_symbol=first_matching_symbol(symbols, ("FarCall", "Bankswitch"), default="FarCall"),
                watch=first_symbol(watch_symbols, default="hROMBank"),
                frames=frames,
                out_trace=".local\\tmp\\debugger_setup_banking_trace.jsonl",
            ),
        ]
        return setup_target(
            surface=surface,
            title="Banking and ABI setup checks",
            requires_positioned_state=True,
            setup_commands=setup_commands,
            state_synthesis_recipes=state_recipes,
            state_recipe_commands=commands_from_recipes(state_recipes),
            trigger_commands=trigger_commands,
            validation_commands=validation_commands,
        )

    if surface == "content_static":
        files = unique_list(
            [
                *[normalize_path(path) for path in changed_files[:4]],
                *[
                    normalize_path(str(scenario.get("source_file", "")))
                    for scenario in content_scenarios[:8]
                    if scenario.get("source_file")
                ],
            ]
        )[:4]
        if not files:
            files = ["<changed_file>"]
        setup_commands = [
            f"python -m tools.debugger content-mirror --source-file {cmd_arg(path)}"
            for path in files
        ]
        setup_commands.extend(
            f"python -m tools.debugger content-scenarios --source-file {cmd_arg(path)} --out-scenarios {cmd_arg(scenario_path)}"
            for path in files
        )
        state_recipes = content_state_synthesis_recipes(
            files=files,
            scenario_path=scenario_path,
            scenarios=content_scenarios,
            effective_rom=effective_rom,
            symbols_path=symbols_path,
            save_state=save_state,
        )
        requires_positioned_state = bool(content_preconditions_for_scenarios(content_scenarios))
        trigger_commands = content_trigger_commands(
            scenarios=content_scenarios,
            effective_rom=effective_rom,
            symbols_path=symbols_path,
            save_state=save_state,
            scenario_path=scenario_path,
            files=files,
            frames=frames,
        )
        validation_commands = content_expectation_validation_commands(
            files=files,
            scenarios=content_scenarios,
        )
        validation_commands.extend(
            content_runtime_probe_commands(
                files=files,
                effective_rom=effective_rom,
                symbols_path=symbols_path,
                save_state=save_state,
                scenario_path=scenario_path,
                scenarios=content_scenarios,
                frames=frames,
            )
        )
        return setup_target(
            surface=surface,
            title="Content scenario setup and trigger plan",
            requires_positioned_state=requires_positioned_state,
            setup_commands=setup_commands,
            state_synthesis_recipes=state_recipes,
            state_recipe_commands=commands_from_recipes(state_recipes),
            trigger_commands=trigger_commands,
            validation_commands=validation_commands,
        )

    setup_commands = [
        triage_command(changed_files=changed_files, symptom=symptom),
        generation_command(surface="general", symbols=symbols, changed_files=changed_files, symptom=symptom, scenario_path=scenario_path),
    ]
    state_recipes = general_state_synthesis_recipes(
        symbols=symbols,
        changed_files=changed_files,
        symptom=symptom,
        scenario_path=scenario_path,
    )
    trigger_commands = [
        replay_general_command(
            effective_rom=effective_rom,
            symbols_path=symbols_path,
            save_state=save_state,
            symbols=symbols,
            watch_symbols=watch_symbols,
            changed_files=changed_files,
            symptom=symptom,
            frames=frames,
        )
    ]
    validation_commands = [
        "python -m tools.debugger investigate --symbol <symbol> --symptom <description>",
    ]
    return setup_target(
        surface=surface,
        title="General setup and trigger plan",
        requires_positioned_state=True,
        setup_commands=setup_commands,
        state_synthesis_recipes=state_recipes,
        state_recipe_commands=commands_from_recipes(state_recipes),
        trigger_commands=trigger_commands,
        validation_commands=validation_commands,
    )


def damage_state_synthesis_recipes(
    *,
    symbols: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
    scenario_path: str,
    watch: str,
) -> list[dict[str, Any]]:
    return [
        state_recipe(
            recipe_id="damage_snapshot_ring_runtime",
            surface="damage",
            title="Damage snapshot-ring runtime setup",
            status="ready",
            produces=("runtime_setup", "watch_change_evidence"),
            commands=(
                generation_command(
                    surface="damage",
                    symbols=symbols,
                    changed_files=changed_files,
                    symptom=symptom,
                    scenario_path=scenario_path,
                ),
                f"python -m tools.damage_debugger.replay --scenario physical_no_items --watch {cmd_arg(watch)} --json",
                "python -m tools.damage_debugger.find physical_no_items --json",
            ),
            output_candidates=("audit/damage_debugger/*.jsonl",),
            notes=(
                "Uses the active damage debugger boot-cache and snapshot-ring path to synthesize a controlled battle runtime.",
                "Produces replay evidence rather than a reusable PyBoy save-state file.",
            ),
        )
    ]


BOSS_STATE_FACTORY_ROUTES = {
    "falkner",
    "bugsy",
    "whitney",
    "morty",
    "chuck",
    "jasmine",
    "pryce",
    "clair",
    "brock",
    "misty",
    "lt_surge",
    "erika",
    "janine",
    "sabrina",
    "blaine",
    "blue",
    "koga",
    "champion_lance",
}


def boss_ai_state_synthesis_recipes(
    *,
    scenario_ids: tuple[str, ...],
    symbols: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
    scenario_path: str,
) -> list[dict[str, Any]]:
    route = first_known_boss_route(scenario_ids)
    factory_args = f"--boss {route}" if route else "--all"
    output_pattern = (
        f".local/tmp/boss_state_factory/{route}_chosen_frame_*.state"
        if route else ".local/tmp/boss_state_factory/*_chosen_frame_*.state"
    )
    return [
        state_recipe(
            recipe_id="boss_ai_route_state_factory",
            surface="boss_ai",
            title="Boss AI route save-state factory",
            status="ready",
            produces=("save_state", "pre_choice_state", "manifest_hints"),
            commands=(
                f"python tools\\trace\\boss_ai_state_factory.py {factory_args} --update-manifest --out-dir .local\\tmp\\boss_state_factory",
            ),
            output_candidates=(output_pattern, ".local/tmp/boss_state_factory/manifest_hints.json"),
            notes=(
                "Drives the romhack through real map scripts to a boss decision point and writes PyBoy state files.",
            ),
        ),
        state_recipe(
            recipe_id="boss_ai_generated_policy_materialization",
            surface="boss_ai",
            title="Boss AI generated scenario materialization",
            status="ready",
            produces=("rom_materialization_report", "score_state_evidence"),
            commands=(
                generation_command(
                    surface="boss_ai",
                    symbols=symbols,
                    changed_files=changed_files,
                    symptom=symptom,
                    scenario_path=scenario_path,
                ),
                f"python -m tools.boss_ai_debugger rom-selector-materialize --scenarios {cmd_arg(scenario_path)} --limit 20",
                f"python -m tools.boss_ai_debugger rom-score-materialize --scenarios {cmd_arg(scenario_path)} --limit 4 --compare-fast-score",
                f"python -m tools.boss_ai_debugger rom-switch-materialize --scenarios {cmd_arg(scenario_path)} --limit 20",
            ),
            output_candidates=(".local/tmp/boss_ai_debugger/*.json",),
            notes=(
                "Materializes selected generated policy cases against ROM state patches before treating Python policy output as ROM behavior.",
            ),
        ),
    ]


def banking_state_synthesis_recipes(*, watch: str) -> list[dict[str, Any]]:
    return [
        state_recipe(
            recipe_id="banking_boot_watch_probe",
            surface="banking_abi",
            title="Banking boot/watch probe",
            status="ready",
            produces=("runtime_watch_evidence",),
            commands=(
                f"python -m tools.debugger watch --watch-symbol {cmd_arg(watch)} --frames 120 --execute",
                "python tools\\audit\\check_farcall_a_clobber.py",
                "python tools\\audit\\check_farcall_hl_clobber.py",
                "python tools\\audit\\check_cross_bank_call.py",
            ),
            output_candidates=(".local/tmp/debugger_watch_*.json",),
            notes=(
                "Banking hazards usually need register/bank watch evidence around an existing route; this recipe gives the generic runtime probe and static ABI gates.",
            ),
        )
    ]


def content_state_synthesis_recipes(
    *,
    files: list[str],
    scenario_path: str,
    scenarios: list[dict[str, Any]],
    effective_rom: str,
    symbols_path: str,
    save_state: str,
) -> list[dict[str, Any]]:
    commands = [
        f"python -m tools.debugger content-scenarios --source-file {cmd_arg(path)} --out-scenarios {cmd_arg(scenario_path)}"
        for path in files
    ]
    recipes = [
        state_recipe(
            recipe_id="content_semantic_scenario_manifest",
            surface="content_static",
            title="Content semantic scenario manifest",
            status="ready" if commands else "needs-input",
            produces=("scenario_manifest", "content_trigger_manifest"),
            commands=tuple(commands),
            output_candidates=(scenario_path,),
            notes=(
                "Converts maps, scripts, assets, and audio source conventions into deterministic replay/materialization scenario records.",
            ),
        )
    ]
    preconditions = content_preconditions_for_scenarios(scenarios)
    if preconditions:
        scenario_commands = [
            content_scenario_setup_command(scenario_path=scenario_path, scenario=scenario)
            for scenario in scenarios[:8]
            if setup_scenario_id_for(scenario)
        ]
        materialization_commands = content_state_materialization_commands(
            scenarios=scenarios,
            effective_rom=effective_rom,
            symbols_path=symbols_path,
            save_state=save_state,
        )
        recipes.append(
            state_recipe(
                recipe_id="content_runtime_preconditions",
                surface="content_static",
                title="Content runtime trigger preconditions",
                status="planned",
                produces=("positioning_requirements", "runtime_probe_targets"),
                commands=tuple(scenario_commands),
                output_candidates=(scenario_path,),
                notes=(
                    "Records the concrete map/script/movement/audio/asset state that must be loaded or synthesized before emulator-backed proof.",
                    "Use the paired replay commands to verify the helper trace and watch targets once a positioned state exists.",
                ),
                preconditions=preconditions,
            )
        )
        recipes.append(
            state_recipe(
                recipe_id="content_positioned_state_materialization",
                surface="content_static",
                title="Content positioned-state materialization",
                status="ready" if save_state else "planned",
                produces=("positioned_save_state", "wram_patch_manifest", "runtime_probe_state"),
                commands=tuple(materialization_commands),
                output_candidates=(".local/tmp/debugger_content_state_*.state",),
                notes=(
                    "Patches map-position, script-entry, or movement-entry WRAM symbols on top of a base save state from the selected content scenario precondition.",
                    "Use the patched state with replay/watch/trace-instructions to prove the actual helper path.",
                ),
                preconditions=preconditions,
            )
        )
    return recipes


def content_preconditions_for_scenarios(scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for scenario in scenarios[:16]:
        scenario_id = setup_scenario_id_for(scenario)
        for item in dict_items(scenario.get("state_preconditions")):
            copied = dict(item)
            copied["scenario_id"] = scenario_id
            copied["scenario_type"] = str(scenario.get("scenario_type", ""))
            copied["source_file"] = normalize_path(str(scenario.get("source_file", "")))
            out.append(copied)
    return out


def content_state_materialization_commands(
    *,
    scenarios: list[dict[str, Any]],
    effective_rom: str,
    symbols_path: str,
    save_state: str,
) -> list[str]:
    commands = []
    for scenario in scenarios[:8]:
        scenario_id = setup_scenario_id_for(scenario)
        if not scenario_id:
            continue
        source = str(scenario.get("_setup_source", ""))
        args = [
            "--rom",
            cmd_arg(effective_rom),
            "--symbols",
            cmd_arg(symbols_path),
            "--scenario-id",
            cmd_arg(scenario_id),
            "--base-save-state",
            cmd_arg(save_state or "<base-state>"),
            "--out-state",
            cmd_arg(f".local\\tmp\\debugger_content_state_{scenario_id}.state"),
        ]
        if source.endswith(".jsonl"):
            args.extend(["--scenario", cmd_arg(source)])
        elif source:
            args.extend(["--report", cmd_arg(source)])
        else:
            args.extend(["--scenario", cmd_arg("<content-scenarios.jsonl>")])
        if save_state:
            args.append("--execute")
        commands.append("python -m tools.debugger content-state " + " ".join(args))
    return unique_list(commands)


def content_scenario_setup_command(*, scenario_path: str, scenario: dict[str, Any]) -> str:
    scenario_id = setup_scenario_id_for(scenario)
    args = [
        "--scenario",
        cmd_arg(scenario_path),
        "--scenario-id",
        cmd_arg(scenario_id),
    ]
    source_file = normalize_path(str(scenario.get("source_file", "")))
    if source_file:
        args.extend(["--changed-file", cmd_arg(source_file)])
    return "python -m tools.debugger replay " + " ".join(args)


def content_trigger_commands(
    *,
    scenarios: list[dict[str, Any]],
    effective_rom: str,
    symbols_path: str,
    save_state: str,
    scenario_path: str,
    files: list[str],
    frames: int,
) -> list[str]:
    if scenarios:
        commands = []
        for scenario in scenarios[:8]:
            scenario_id = setup_scenario_id_for(scenario)
            if not scenario_id:
                continue
            source_file = normalize_path(str(scenario.get("source_file", "")))
            args = [
                "--rom",
                cmd_arg(effective_rom),
                "--symbols",
                cmd_arg(symbols_path),
                "--scenario",
                cmd_arg(scenario_path),
                "--scenario-id",
                cmd_arg(scenario_id),
                "--frames",
                str(frames),
            ]
            if save_state:
                args.extend(["--save-state", cmd_arg(save_state)])
            if source_file:
                args.extend(["--changed-file", cmd_arg(source_file)])
            commands.append("python -m tools.debugger replay " + " ".join(args))
        if commands:
            return commands
    return [
        f"python -m tools.debugger replay --rom {cmd_arg(effective_rom)} --symbols {cmd_arg(symbols_path)} --scenario {cmd_arg(scenario_path)} --scenario-id <id>"
    ]


def content_expectation_validation_commands(
    *,
    files: list[str],
    scenarios: list[dict[str, Any]],
) -> list[str]:
    commands = []
    for scenario in scenarios[:8]:
        scenario_id = setup_scenario_id_for(scenario)
        source = str(scenario.get("_setup_source", ""))
        if not scenario_id or not source or source.endswith(".jsonl"):
            continue
        preconditions = dict_items(scenario.get("state_preconditions"))
        if not preconditions:
            commands.append(
                f"python -m tools.debugger expect --report {cmd_arg(source)} --expect scenario={cmd_arg(scenario_id)}"
            )
            continue
        for precondition in preconditions[:3]:
            kind = str(precondition.get("kind", ""))
            if not kind:
                continue
            args = [
                "--report",
                cmd_arg(source),
                "--expect",
                f"scenario={cmd_arg(scenario_id)}",
                "--expect",
                f"precondition={cmd_arg(kind)},scenario={cmd_arg(scenario_id)}",
            ]
            watch = first_symbol(string_items(precondition.get("watch_symbols")), default="")
            if watch:
                args.extend(["--expect", f"precondition={cmd_arg(kind)},scenario={cmd_arg(scenario_id)},symbol={cmd_arg(watch)}"])
            commands.append("python -m tools.debugger expect " + " ".join(args))
    if commands:
        return unique_list(commands)
    return [
        f"python -m tools.debugger expect --source-file {cmd_arg(path)} --expect contains=<expected_text>"
        for path in files
    ]


def content_runtime_probe_commands(
    *,
    files: list[str],
    effective_rom: str,
    symbols_path: str,
    save_state: str,
    scenario_path: str,
    scenarios: list[dict[str, Any]],
    frames: int,
) -> list[str]:
    commands: list[str] = []
    if scenarios:
        for scenario in scenarios[:8]:
            scenario_id = setup_scenario_id_for(scenario)
            if not scenario_id:
                continue
            helpers = content_scenario_runtime_helpers(scenario)
            watches = content_scenario_runtime_watches(scenario)
            if not helpers and not watches:
                continue
            source_file = normalize_path(str(scenario.get("source_file", "")))
            args = [
                "--rom",
                cmd_arg(effective_rom),
                "--symbols",
                cmd_arg(symbols_path),
                "--scenario",
                cmd_arg(scenario_path),
                "--scenario-id",
                cmd_arg(scenario_id),
                "--frames",
                str(frames),
            ]
            if save_state:
                args.extend(["--save-state", cmd_arg(save_state)])
            if source_file:
                args.extend(["--changed-file", cmd_arg(source_file)])
            for helper in helpers[:5]:
                args.extend(["--symbol", helper])
            for watch in watches[:5]:
                args.extend(["--watch-symbol", watch])
            commands.append("python -m tools.debugger replay " + " ".join(args))
        if commands:
            return commands
    for path in files:
        helpers = content_runtime_helpers(path)
        watches = content_runtime_watches(path)
        if not helpers and not watches:
            continue
        args = [
            "--rom",
            cmd_arg(effective_rom),
            "--symbols",
            cmd_arg(symbols_path),
            "--scenario",
            cmd_arg(scenario_path),
            "--scenario-id",
            "<id>",
            "--changed-file",
            cmd_arg(path),
            "--frames",
            str(frames),
        ]
        if save_state:
            args.extend(["--save-state", cmd_arg(save_state)])
        for helper in helpers[:5]:
            args.extend(["--symbol", helper])
        for watch in watches:
            args.extend(["--watch-symbol", watch])
        commands.append("python -m tools.debugger replay " + " ".join(args))
    return commands


def content_scenario_runtime_helpers(scenario: dict[str, Any]) -> list[str]:
    runtime_targets = scenario.get("runtime_targets") if isinstance(scenario.get("runtime_targets"), dict) else {}
    helpers = [
        *string_items(runtime_targets.get("trace_symbols")),
        *string_items(runtime_targets.get("script_symbols")),
    ]
    if not helpers and scenario.get("source_file"):
        helpers.extend(content_runtime_helpers(str(scenario.get("source_file", ""))))
    return unique_list([item for item in helpers if looks_like_runtime_symbol(item)])


def content_scenario_runtime_watches(scenario: dict[str, Any]) -> list[str]:
    runtime_targets = scenario.get("runtime_targets") if isinstance(scenario.get("runtime_targets"), dict) else {}
    watches = string_items(runtime_targets.get("watch_symbols"))
    if not watches and scenario.get("source_file"):
        watches.extend(content_runtime_watches(str(scenario.get("source_file", ""))))
    return unique_list([item for item in watches if looks_like_runtime_symbol(item)])


def content_runtime_helpers(path: str) -> list[str]:
    normalized = normalize_path(path).lower()
    helpers: list[str] = []
    for prefix, symbols in CONTENT_RUNTIME_HELPERS_BY_PREFIX:
        if normalized.startswith(prefix):
            helpers.extend(symbols)
    if not helpers and normalized.endswith(".asm"):
        helpers.extend(("ReadMapEvents", "CallScript"))
    return unique_list(helpers)


def content_runtime_watches(path: str) -> list[str]:
    normalized = normalize_path(path).lower()
    if normalized.startswith(("maps/", "scripts/")):
        return list(CONTENT_MAP_WATCH_SYMBOLS)
    return []


def general_state_synthesis_recipes(
    *,
    symbols: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
    scenario_path: str,
) -> list[dict[str, Any]]:
    return [
        state_recipe(
            recipe_id="general_seed_manifest",
            surface="general",
            title="General unified seed manifest",
            status="planned",
            produces=("scenario_manifest", "triage_plan"),
            commands=(
                generation_command(
                    surface="general",
                    symbols=symbols,
                    changed_files=changed_files,
                    symptom=symptom,
                    scenario_path=scenario_path,
                ),
                triage_command(changed_files=changed_files, symptom=symptom),
            ),
            output_candidates=(scenario_path,),
            notes=(
                "No dedicated state factory matched this surface; this records the strongest generic handoff manifest and triage route.",
            ),
        )
    ]


def state_recipe(
    *,
    recipe_id: str,
    surface: str,
    title: str,
    status: str,
    produces: tuple[str, ...],
    commands: tuple[str, ...],
    output_candidates: tuple[str, ...],
    notes: tuple[str, ...],
    preconditions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    command_items = command_records(list(commands))
    return {
        "id": recipe_id,
        "surface": surface,
        "title": title,
        "status": status,
        "produces": list(produces),
        "output_candidates": list(output_candidates),
        "notes": list(notes),
        "precondition_count": len(preconditions or []),
        "preconditions": preconditions or [],
        "command_count": len(command_items),
        "commands": command_items,
        "runnable": bool(command_items) and all(item["runnable"] for item in command_items),
    }


def commands_from_recipes(recipes: list[dict[str, Any]]) -> list[str]:
    return unique_list(
        str(command.get("command", ""))
        for recipe in recipes
        for command in recipe.get("commands", [])
        if isinstance(command, dict)
    )


def first_known_boss_route(scenario_ids: tuple[str, ...]) -> str:
    for scenario_id in scenario_ids:
        text = str(scenario_id).lower()
        if text in BOSS_STATE_FACTORY_ROUTES:
            return text
        for route in BOSS_STATE_FACTORY_ROUTES:
            if text.startswith(route + "_") or text.startswith(route + "-"):
                return route
    return ""


def setup_target(
    *,
    surface: str,
    title: str,
    requires_positioned_state: bool,
    setup_commands: list[str],
    state_synthesis_recipes: list[dict[str, Any]],
    state_recipe_commands: list[str],
    trigger_commands: list[str],
    validation_commands: list[str],
) -> dict[str, Any]:
    commands = unique_list([*setup_commands, *state_recipe_commands, *trigger_commands, *validation_commands])
    return {
        "surface": surface,
        "title": title,
        "requires_positioned_state": requires_positioned_state,
        "setup_command_count": len(setup_commands),
        "state_synthesis_recipe_count": len(state_synthesis_recipes),
        "state_recipe_command_count": len(state_recipe_commands),
        "trigger_command_count": len(trigger_commands),
        "validation_command_count": len(validation_commands),
        "setup_commands": command_records(setup_commands),
        "state_synthesis_recipes": state_synthesis_recipes,
        "state_recipe_commands": command_records(state_recipe_commands),
        "trigger_commands": command_records(trigger_commands),
        "validation_commands": command_records(validation_commands),
        "commands": commands,
    }


def build_trigger_coverage(
    *,
    targets: list[dict[str, Any]],
    save_state: str,
    selected_save_state: dict[str, Any],
) -> dict[str, Any]:
    rows = [
        trigger_coverage_row(target, save_state=save_state, selected_save_state=selected_save_state)
        for target in targets
    ]
    status_counts = count_statuses(row["status"] for row in rows)
    covered_count = status_counts.get("covered", 0)
    return {
        "target_count": len(rows),
        "covered_target_count": covered_count,
        "planned_target_count": status_counts.get("planned", 0),
        "blocked_target_count": status_counts.get("blocked", 0),
        "coverage_ratio": round(covered_count / len(rows), 4) if rows else 0.0,
        "status_counts": status_counts,
        "targets": rows,
        "blocking_reasons": unique_list(
            reason
            for row in rows
            for reason in row.get("blockers", [])
        ),
    }


def trigger_coverage_row(
    target: dict[str, Any],
    *,
    save_state: str,
    selected_save_state: dict[str, Any],
) -> dict[str, Any]:
    setup_status = command_group_status(target.get("setup_commands", []))
    recipe_status = state_recipe_group_status(
        target.get("state_synthesis_recipes", []),
        command_records=target.get("state_recipe_commands", []),
    )
    trigger_status = command_group_status(target.get("trigger_commands", []))
    validation_status = command_group_status(target.get("validation_commands", []))
    requires_state = bool(target.get("requires_positioned_state"))
    state_status = state_coverage_status(
        requires_state=requires_state,
        save_state=save_state,
        selected_save_state=selected_save_state,
        recipe_status=recipe_status,
    )
    blockers = trigger_blockers(
        requires_state=requires_state,
        state_status=state_status,
        setup_status=setup_status,
        recipe_status=recipe_status,
        trigger_status=trigger_status,
        validation_status=validation_status,
    )
    status = target_coverage_status(
        state_status=state_status,
        setup_status=setup_status,
        recipe_status=recipe_status,
        trigger_status=trigger_status,
        validation_status=validation_status,
        blockers=blockers,
    )
    return {
        "surface": str(target.get("surface", "")),
        "title": str(target.get("title", "")),
        "status": status,
        "requires_positioned_state": requires_state,
        "state_status": state_status,
        "selected_save_state": selected_save_state,
        "setup_status": setup_status,
        "state_recipe_status": recipe_status,
        "trigger_status": trigger_status,
        "validation_status": validation_status,
        "blockers": blockers,
    }


def command_group_status(records: Any) -> dict[str, Any]:
    items = records if isinstance(records, list) else []
    runnable = [
        item for item in items
        if isinstance(item, dict) and item.get("runnable")
    ]
    blocked = [
        item for item in items
        if isinstance(item, dict) and not item.get("runnable")
    ]
    if not items:
        status = "missing"
    elif len(runnable) == len(items):
        status = "ready"
    elif runnable:
        status = "partial"
    else:
        status = "blocked"
    return {
        "status": status,
        "command_count": len(items),
        "runnable_count": len(runnable),
        "blocked_count": len(blocked),
        "blocked_commands": [
            str(item.get("command", ""))
            for item in blocked[:8]
            if isinstance(item, dict)
        ],
    }


def state_recipe_group_status(recipes: Any, *, command_records: Any) -> dict[str, Any]:
    command_status = command_group_status(command_records)
    recipe_items = [item for item in recipes if isinstance(item, dict)] if isinstance(recipes, list) else []
    semantic_statuses = [str(item.get("status", "")) for item in recipe_items]
    if not recipe_items:
        status = command_status["status"]
    elif all(status == "ready" for status in semantic_statuses) and command_status["status"] == "ready":
        status = "ready"
    elif command_status["status"] == "blocked" or all(status in {"blocked", "needs-input"} for status in semantic_statuses):
        status = "blocked"
    elif any(status in {"ready", "partial", "planned"} for status in semantic_statuses) or command_status["status"] in {"ready", "partial"}:
        status = "partial"
    else:
        status = command_status["status"]
    return {
        **command_status,
        "status": status,
        "semantic_status_counts": count_statuses(semantic_statuses),
        "recipe_count": len(recipe_items),
    }


def state_coverage_status(
    *,
    requires_state: bool,
    save_state: str,
    selected_save_state: dict[str, Any],
    recipe_status: dict[str, Any],
) -> str:
    if not requires_state:
        return "not-required"
    if save_state:
        return "supplied"
    if selected_save_state:
        if selected_save_state.get("exists"):
            return "discovered"
        return "discovered-missing"
    if recipe_status["status"] == "ready":
        return "synthesizable"
    if recipe_status["status"] == "partial":
        return "partially-synthesizable"
    if recipe_status["status"] == "blocked":
        return "needs-concrete-recipe-input"
    return "missing-recipe"


def trigger_blockers(
    *,
    requires_state: bool,
    state_status: str,
    setup_status: dict[str, Any],
    recipe_status: dict[str, Any],
    trigger_status: dict[str, Any],
    validation_status: dict[str, Any],
) -> list[str]:
    blockers = []
    if requires_state and state_status not in {"supplied", "discovered", "not-required"}:
        blockers.append(f"state:{state_status}")
    if setup_status["status"] in {"missing", "blocked"}:
        blockers.append(f"setup:{setup_status['status']}")
    if recipe_status["status"] in {"blocked"}:
        blockers.append(f"state_recipe:{recipe_status['status']}")
    if trigger_status["status"] != "ready":
        blockers.append(f"trigger:{trigger_status['status']}")
    if validation_status["status"] != "ready":
        blockers.append(f"validation:{validation_status['status']}")
    return blockers


def target_coverage_status(
    *,
    state_status: str,
    setup_status: dict[str, Any],
    recipe_status: dict[str, Any],
    trigger_status: dict[str, Any],
    validation_status: dict[str, Any],
    blockers: list[str],
) -> str:
    if not blockers and state_status in {"supplied", "discovered", "not-required"}:
        return "covered"
    if (
        setup_status["status"] in {"ready", "partial"}
        or recipe_status["status"] in {"ready", "partial"}
        or trigger_status["status"] in {"ready", "partial"}
        or validation_status["status"] in {"ready", "partial"}
    ):
        return "planned"
    return "blocked"


def count_statuses(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        text = str(value)
        counts[text] = counts.get(text, 0) + 1
    return counts


def generation_command(
    *,
    surface: str,
    symbols: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
    scenario_path: str,
) -> str:
    args = ["--family", cmd_arg(surface), "--out-scenarios", cmd_arg(scenario_path)]
    for symbol in symbols[:6]:
        args.extend(["--symbol", cmd_arg(symbol)])
    for path in changed_files[:4]:
        args.extend(["--changed-file", cmd_arg(path)])
    if symptom:
        args.extend(["--symptom", cmd_arg(symptom)])
    return "python -m tools.debugger generate " + " ".join(args)


def replay_command(
    *,
    effective_rom: str,
    symbols_path: str,
    save_state: str,
    watch: str,
    frames: int,
) -> str:
    args = [
        "--rom",
        cmd_arg(effective_rom),
        "--symbols",
        cmd_arg(symbols_path),
        "--watch-symbol",
        cmd_arg(watch),
        "--frames",
        str(frames),
        "--execute-watch",
    ]
    if save_state:
        args.extend(["--save-state", cmd_arg(save_state)])
    return "python -m tools.debugger replay " + " ".join(args)


def replay_general_command(
    *,
    effective_rom: str,
    symbols_path: str,
    save_state: str,
    symbols: tuple[str, ...],
    watch_symbols: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
    frames: int,
) -> str:
    args = [
        "--rom",
        cmd_arg(effective_rom),
        "--symbols",
        cmd_arg(symbols_path),
        "--frames",
        str(frames),
    ]
    if save_state:
        args.extend(["--save-state", cmd_arg(save_state)])
    for symbol in symbols[:6]:
        args.extend(["--symbol", cmd_arg(symbol)])
    for watch in watch_symbols[:6]:
        args.extend(["--watch-symbol", cmd_arg(watch)])
    for path in changed_files[:4]:
        args.extend(["--changed-file", cmd_arg(path)])
    if symptom:
        args.extend(["--symptom", cmd_arg(symptom)])
    return "python -m tools.debugger replay " + " ".join(args)


def trace_instruction_command(
    *,
    effective_rom: str,
    symbols_path: str,
    save_state: str,
    trace_symbol: str,
    watch: str,
    frames: int,
    out_trace: str,
) -> str:
    args = [
        "--rom",
        cmd_arg(effective_rom),
        "--symbols",
        cmd_arg(symbols_path),
        "--symbol",
        cmd_arg(trace_symbol),
        "--watch-symbol",
        cmd_arg(watch),
        "--frames",
        str(frames),
        "--execute",
        "--require-hit",
        "--out-trace",
        cmd_arg(out_trace),
    ]
    if save_state:
        args.extend(["--save-state", cmd_arg(save_state)])
    return "python -m tools.debugger trace-instructions " + " ".join(args)


def triage_command(*, changed_files: tuple[str, ...], symptom: str) -> str:
    args = []
    for path in changed_files[:4]:
        args.extend(["--changed-file", cmd_arg(path)])
    if symptom:
        args.extend(["--symptom", cmd_arg(symptom)])
    if not args:
        args.extend(["--symptom", "<description>"])
    return "python -m tools.debugger triage " + " ".join(args)


def command_records(commands: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "command": command,
            "runnable": command_is_runnable(command),
        }
        for command in unique_list(commands)
    ]


def first_symbol(symbols: tuple[str, ...], *, default: str) -> str:
    for symbol in symbols:
        if symbol:
            return symbol
    return default


def first_matching_symbol(symbols: tuple[str, ...], prefixes: tuple[str, ...], *, default: str) -> str:
    lowered_prefixes = tuple(prefix.lower() for prefix in prefixes)
    for symbol in symbols:
        lowered = symbol.lower()
        if any(lowered.startswith(prefix) for prefix in lowered_prefixes):
            return symbol
    return default


def signal(signal_type: str, kind: str, value: str, weight: int, source: str) -> dict[str, Any]:
    return {
        "type": signal_type,
        "kind": kind,
        "value": str(value),
        "weight": weight,
        "source": source,
    }


def merge_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in signals:
        key = (str(item.get("type", "")), str(item.get("kind", "")), str(item.get("value", "")))
        if key not in merged:
            merged[key] = dict(item)
        else:
            merged[key]["weight"] = int(merged[key].get("weight", 0)) + int(item.get("weight", 0))
    return sorted(
        merged.values(),
        key=lambda item: (-int(item.get("weight", 0)), str(item.get("kind", "")), str(item.get("value", ""))),
    )


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


def looks_like_runtime_symbol(value: str) -> bool:
    text = str(value).strip()
    if not text or "/" in text or "\\" in text:
        return False
    if text.startswith(("$", "0x", "0X", ".", "-", "<")):
        return False
    return text[0].isalpha() and all(char.isalnum() or char in {"_", "."} for char in text)


def looks_like_setup_source_path(value: str) -> bool:
    text = normalize_path(str(value))
    if not text or " " in text:
        return False
    return "/" in text and Path(text).suffix.lower() in SETUP_SOURCE_EXTENSIONS


def signal_values(signals: list[dict[str, Any]], *, kind: str, signal_type_prefix: str) -> list[str]:
    return unique_list(
        str(item.get("value", ""))
        for item in signals
        if item.get("kind") == kind and str(item.get("type", "")).startswith(signal_type_prefix)
    )


def cmd_arg(value: str) -> str:
    text = str(value)
    if not text:
        return '""'
    if any(char.isspace() for char in text):
        import json

        return json.dumps(text)
    return text


def resolve_input_path(raw_path: str, *, root: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return root / path


def display_input_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve())
