from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog import ROOT, keyword_matches, triage_request
from .provenance import build_provenance_report
from .reporting import load_reports
from .workflow import command_address_arg


@dataclass(frozen=True)
class TestGeneratorRule:
    id: str
    title: str
    path_prefixes: tuple[str, ...]
    symbols: tuple[str, ...]
    symptom_keywords: tuple[str, ...]
    commands: tuple[str, ...]
    counterexample_commands: tuple[str, ...]
    excluded_path_prefixes: tuple[str, ...] = ()
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
            "python tools/audit/check_farcall_a_clobber.py",
            "python tools/audit/check_farcall_hl_clobber.py",
            "python tools/audit/check_cross_bank_call.py",
            "python tools/audit/check_release_smoke.py",
        ),
        counterexample_commands=(
            "python -m tools.debugger watch --watch-symbol hROMBank --execute --frames 120",
            "python -m tools.debugger provenance --symbol hROMBank --symbol FarCall",
        ),
    ),
    TestGeneratorRule(
        id="pokemon_data_counterexamples",
        title="Pokemon species, learnset, and move-data source checks",
        path_prefixes=(
            "data/pokemon/evos_attacks.asm",
            "data/pokemon/egg_moves.asm",
            "data/pokemon/base_stats/",
            "data/moves/",
        ),
        symbols=(),
        symptom_keywords=(
            "learnset",
            "level-up",
            "level up",
            "level-up move",
            "tm compatibility",
            "hm compatibility",
            "egg move",
            "evolution",
            "evolve",
            "species data",
            "pokemon data",
        ),
        commands=(
            "python -m tools.debugger content-mirror --changed-file <changed_file>",
            "python -m tools.debugger expect --source-file <changed_file> --expect source=<changed_file>",
            "python -m tools.debugger provenance --source-file <changed_file>",
            "python tools/audit/check_release_smoke.py",
        ),
        counterexample_commands=(
            "python -m tools.debugger expect --source-file <changed_file> --expect contains=<expected_text>",
            "python -m tools.debugger content-mirror --source-file <changed_file>",
            "python -m tools.debugger provenance --source-file <changed_file>",
        ),
        notes=(
            "For a concrete learnset edit, replace <expected_text> with the exact source row such as 'db 10, REFLECT'.",
        ),
    ),
    TestGeneratorRule(
        id="content_static_counterexamples",
        title="Content, map, graphics, and audio static checks",
        path_prefixes=("data/", "maps/", "gfx/", "audio/"),
        symbols=(),
        symptom_keywords=("map", "warp", "graphics", "palette", "audio", "text", "sprite"),
        commands=(
            "python tools/audit/check_release_smoke.py",
            "python tools/audit/check_layout_orgs.py",
            "python tools/audit/check_pic_bank_pressure.py",
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
        excluded_path_prefixes=(
            "data/pokemon/evos_attacks.asm",
            "data/pokemon/egg_moves.asm",
            "data/pokemon/base_stats/",
            "data/moves/",
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
    matches = report_based_suggestions(loaded_reports)
    for rule in GENERATOR_RULES:
        path_hit = any(
            any(path.startswith(prefix.lower()) for prefix in rule.path_prefixes)
            and not any(path.startswith(prefix.lower()) for prefix in rule.excluded_path_prefixes)
            for path in normalized_paths
        )
        symbol_hit = any(symbol in rule.symbols for symbol in symbols)
        symptom_hit = bool(symptom_text) and any(
            keyword_matches(keyword, symptom_text) for keyword in rule.symptom_keywords
        )
        if not path_hit and not symbol_hit and not symptom_hit:
            continue
        command_changed_files = changed_files
        inferred_changed_file = ""
        if not command_changed_files and symptom_hit:
            inferred_changed_file = inferred_changed_file_for_rule(rule.id, symptom_text)
            if inferred_changed_file:
                command_changed_files = (inferred_changed_file,)
        match = {
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
        if inferred_changed_file:
            match["inferred_changed_file"] = inferred_changed_file
        materialize_changed_file_commands(match, changed_files=command_changed_files)
        matches.append(match)

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
                reports=reports,
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


def report_based_suggestions(loaded_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches = []
    for loaded in loaded_reports:
        data = loaded.get("data", {})
        if not isinstance(data, dict):
            continue
        if data.get("kind") == "unified_debugger_fuzz_plan":
            match = content_fuzz_report_suggestion(data, source=str(loaded.get("source", "")))
            if match:
                matches.append(match)
        elif data.get("kind") == "unified_debugger_dynamic_taint_report":
            match = dynamic_taint_trace_synthesis_suggestion(data, source=str(loaded.get("source", "")))
            if match:
                matches.append(match)
        elif data.get("kind") == "unified_debugger_minimization_plan":
            match = state_patch_minimization_suggestion(data, source=str(loaded.get("source", "")))
            if match:
                matches.append(match)
    return matches


def dynamic_taint_trace_synthesis_suggestion(report: dict[str, Any], *, source: str) -> dict[str, Any] | None:
    routes = trace_synthesis_routes(report)
    if not routes:
        return None
    commands = [
        f"python -m tools.debugger coverage --report {source}",
        f"python -m tools.debugger rank --report {source}",
        f"python -m tools.debugger impact --report {source}",
        f"python -m tools.debugger visualize --report {source}",
    ]
    counterexample_commands = [
        command
        for route in routes[:6]
        for command in string_items(route.get("commands"))
    ]
    statuses = unique_list(str(route.get("state_status", "")) for route in routes if route.get("state_status"))
    sinks = unique_list(
        [
            *[
                symbol
                for route in routes
                for symbol in string_items(route.get("sink_symbols"))
            ],
            *[
                address
                for route in routes
                for address in string_items(route.get("sink_addresses"))
            ],
        ]
    )
    source_mems = unique_list(
        [
            source_mem
            for route in routes
            for source_mem in string_items(route.get("source_mems"))
        ]
    )
    sources = trace_synthesis_related_sources(routes)
    addresses = trace_synthesis_related_addresses(routes)
    return {
        "id": "dynamic_taint_trace_synthesis_counterexamples",
        "title": "Dynamic-taint trace-synthesis counterexamples",
        "matched_by": ["report"],
        "commands": unique_list(commands),
        "counterexample_commands": unique_list(counterexample_commands),
        "related_symbols": sources,
        "related_addresses": addresses,
        "notes": unique_list(
            [
                f"{len(routes)} trace-synthesis route(s) found in {source}",
                "state_status=" + ",".join(statuses) if statuses else "",
                "sources=" + ",".join(sources[:8]) if sources else "",
                "source_mems=" + ",".join(source_mems[:8]) if source_mems else "",
                "sinks=" + ",".join(sinks[:8]) if sinks else "",
                "Run setup/materialization commands before trace and dynamic-taint commands when a route requires a base save state.",
            ]
        ),
    }


def state_patch_minimization_suggestion(report: dict[str, Any], *, source: str) -> dict[str, Any] | None:
    minimization = report.get("state_patch_minimization")
    if not isinstance(minimization, dict) or not minimization.get("attempted"):
        return None
    source_symbols = state_patch_minimization_source_symbols(minimization)
    watch_symbols = state_patch_minimization_watch_symbols(minimization)
    watch_addresses = state_patch_minimization_watch_addresses(minimization)
    source_mems = state_patch_minimization_source_mems(minimization)
    out_report = str(minimization.get("out_report", ""))
    if not (source_symbols or watch_symbols or watch_addresses or source_mems or out_report):
        return None
    watch_size = positive_int(minimization.get("watch_size"))
    watch_size_arg = f" --watch-size {watch_size}" if watch_size > 1 else ""
    sink_size_arg = f" --sink-size {watch_size}" if watch_size > 1 else ""
    commands = [
        f"python -m tools.debugger provenance --report {source}",
        f"python -m tools.debugger taint --report {source}",
        f"python -m tools.debugger slice --report {source}",
        f"python -m tools.debugger dynamic-taint --report {source} --execute-synthesis",
        f"python -m tools.debugger coverage --report {source}",
        f"python -m tools.debugger rank --report {source}",
        f"python -m tools.debugger impact --report {source}",
        f"python -m tools.debugger visualize --report {source}",
    ]
    trace_args = [f"--report {out_report or source}"]
    for symbol in source_symbols[:6]:
        trace_args.append(f"--symbol {symbol}")
    for address in watch_addresses[:6]:
        trace_args.append(f"--watch-address {command_address_arg(address)}")
    if watch_size > 1:
        trace_args.append(f"--watch-size {watch_size}")
    trace_args.extend(["--execute", "--require-hit"])
    counterexample_commands = [
        *string_items(minimization.get("commands")),
        "python -m tools.debugger trace-instructions " + " ".join(trace_args),
        f"python -m tools.debugger dynamic-taint --report {source} --execute-synthesis",
    ]
    for address in watch_addresses[:4]:
        command_address = command_address_arg(address)
        counterexample_commands.append(
            f"python -m tools.debugger replay --report {out_report or source} --watch-address {command_address}{watch_size_arg} --execute-watch"
        )
        counterexample_commands.append(
            f"python -m tools.debugger dynamic-taint --report {source} --sink-address {command_address}{sink_size_arg} --execute-synthesis"
        )
    return {
        "id": "state_patch_minimization_counterexamples",
        "title": "State-patch minimization trace counterexamples",
        "matched_by": ["report"],
        "commands": unique_list(commands),
        "counterexample_commands": unique_list(counterexample_commands),
        "related_symbols": unique_list([*watch_symbols, *source_symbols]),
        "related_addresses": watch_addresses,
        "notes": unique_list(
            [
                f"state_patch_minimization found in {source}",
                "preserved=" + str(bool(minimization.get("preserved"))),
                "out_report=" + out_report if out_report else "",
                "source_symbols=" + ",".join(source_symbols[:8]) if source_symbols else "",
                "watch_symbols=" + ",".join(watch_symbols[:8]) if watch_symbols else "",
                "source_mems=" + ",".join(source_mems[:8]) if source_mems else "",
                "watch_addresses=" + ",".join(watch_addresses[:8]) if watch_addresses else "",
                "Use the minimized state report for replay/trace proof before claiming behavior.",
            ]
        ),
    }


def trace_synthesis_routes(report: dict[str, Any]) -> list[dict[str, Any]]:
    plan = report.get("trace_synthesis_plan") if isinstance(report.get("trace_synthesis_plan"), dict) else {}
    return dict_items(plan.get("routes"))


def trace_synthesis_related_sources(routes: list[dict[str, Any]]) -> list[str]:
    return unique_list(
        [
            *[
                symbol
                for route in routes
                for symbol in string_items(route.get("sink_symbols"))
            ],
            *[
                symbol
                for route in routes
                for symbol in string_items(route.get("source_symbols"))
            ],
            *[
                origin
                for route in routes
                for _, origin in source_mem_parts(route)
                if origin
            ],
        ]
    )


def trace_synthesis_related_addresses(routes: list[dict[str, Any]]) -> list[str]:
    return unique_list(
        [
            *[
                address
                for route in routes
                for address in string_items(route.get("sink_addresses"))
            ],
            *[
                address
                for route in routes
                for address, _ in source_mem_parts(route)
                if address
            ],
        ]
    )


def source_mem_parts(route: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for value in string_items(route.get("source_mems")):
        text = str(value).strip()
        if not text:
            continue
        if "=" in text:
            address, origin = text.split("=", 1)
            out.append((address.strip(), origin.strip()))
        else:
            out.append((text, ""))
    return out


def state_patch_minimization_source_symbols(item: dict[str, Any]) -> list[str]:
    symbols = string_items(item.get("source_symbols"))
    for result in dict_items(item.get("results")):
        symbols.extend(string_items(result.get("source_symbols")))
    return unique_list(symbol for symbol in symbols if symbol)


def state_patch_minimization_watch_symbols(item: dict[str, Any]) -> list[str]:
    symbols = [
        *string_items(item.get("watch_symbols")),
        *string_items(item.get("semantic_watch_symbols")),
    ]
    for _address, origin in source_mem_parts(item):
        if origin:
            symbols.append(origin)
    for result in dict_items(item.get("results")):
        symbols.extend(string_items(result.get("semantic_watch_symbols")))
        for _address, origin in source_mem_parts(result):
            if origin:
                symbols.append(origin)
    return unique_list(symbol for symbol in symbols if symbol)


def state_patch_minimization_watch_addresses(item: dict[str, Any]) -> list[str]:
    addresses = [
        *string_items(item.get("watch_addresses")),
        *[address for address, _origin in source_mem_parts(item)],
    ]
    for result in dict_items(item.get("results")):
        addresses.extend(string_items(result.get("semantic_watch_addresses")))
        addresses.extend(string_items(result.get("semantic_replay_watch_addresses")))
        addresses.extend(address for address, _origin in source_mem_parts(result))
    return unique_list(addresses)


def state_patch_minimization_source_mems(item: dict[str, Any]) -> list[str]:
    source_mems = string_items(item.get("source_mems"))
    for result in dict_items(item.get("results")):
        source_mems.extend(string_items(result.get("source_mems")))
    return unique_list(source_mems)


def positive_int(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return number if number > 0 else 0


def content_fuzz_report_suggestion(report: dict[str, Any], *, source: str) -> dict[str, Any] | None:
    cases = [
        case
        for case in dict_items(report.get("fuzz_cases"))
        if case.get("scenario_id") and (case.get("runtime_targets") or case.get("state_preconditions"))
    ]
    if not cases:
        return None
    scenario_ids = unique_list(str(case.get("scenario_id", "")) for case in cases if case.get("scenario_id"))
    commands = [
        f"python -m tools.debugger compare --report {source}",
        f"python -m tools.debugger coverage --report {source}",
        *[
            f"python -m tools.debugger expect --report {source} --expect scenario={scenario_id}"
            for scenario_id in scenario_ids[:6]
        ],
    ]
    counterexample_commands = [
        command
        for case in cases[:6]
        for command in content_fuzz_case_commands(case)
    ]
    return {
        "id": "content_fuzz_report_counterexamples",
        "title": "Content fuzz report counterexamples",
        "matched_by": ["report"],
        "commands": unique_list(commands),
        "counterexample_commands": unique_list(counterexample_commands),
        "notes": [
            f"{len(cases)} content fuzz cases found in {source}",
            "Run materialization and replay/watch commands before treating planned content behavior as emulator proof.",
        ],
    }


def content_fuzz_case_commands(case: dict[str, Any]) -> list[str]:
    commands = []
    request = case.get("materialization_request") if isinstance(case.get("materialization_request"), dict) else {}
    commands.extend(string_items(request.get("commands")))
    commands.extend(string_items(case.get("commands")))
    for probe in dict_items(case.get("behavioral_probes")):
        command = str(probe.get("command", ""))
        if command:
            commands.append(command)
    return commands


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


def materialize_changed_file_commands(match: dict[str, Any], *, changed_files: tuple[str, ...]) -> None:
    concrete_changed_file = single_changed_file_command_arg(changed_files)
    if not concrete_changed_file:
        return
    for key in ("commands", "counterexample_commands"):
        match[key] = [
            command.replace("<changed_file>", concrete_changed_file)
            for command in string_items(match.get(key))
        ]


def single_changed_file_command_arg(changed_files: tuple[str, ...]) -> str:
    if len(changed_files) != 1:
        return ""
    return changed_files[0].replace("\\", "/").strip()


def inferred_changed_file_for_rule(rule_id: str, symptom_text: str) -> str:
    if rule_id != "pokemon_data_counterexamples":
        return ""
    if keyword_matches("egg move", symptom_text):
        return "data/pokemon/egg_moves.asm"
    if keyword_matches("tm compatibility", symptom_text) or keyword_matches("hm compatibility", symptom_text):
        return "data/moves/tmhm_moves.asm"
    if (
        keyword_matches("level-up", symptom_text)
        or keyword_matches("level up", symptom_text)
        or keyword_matches("learnset", symptom_text)
        or keyword_matches("level-up move", symptom_text)
    ):
        return "data/pokemon/evos_attacks.asm"
    return ""


def dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, dict)]


def string_items(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if not isinstance(value, list | tuple):
        return []
    return [str(item) for item in value if item]


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
