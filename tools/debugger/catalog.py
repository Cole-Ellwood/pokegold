from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Subsystem:
    id: str
    title: str
    scope: str
    entrypoints: tuple[str, ...]
    evidence_paths: tuple[str, ...]


@dataclass(frozen=True)
class Capability:
    id: str
    title: str
    status: str
    scope: str
    evidence: tuple[str, ...]
    gaps: tuple[str, ...]
    commands: tuple[str, ...] = ()


@dataclass(frozen=True)
class TriageRule:
    id: str
    title: str
    path_prefixes: tuple[str, ...]
    symptom_keywords: tuple[str, ...]
    reason: str
    commands: tuple[str, ...]
    excluded_path_prefixes: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()


SUBSYSTEMS = (
    Subsystem(
        id="boss_ai",
        title="Boss AI debugger",
        scope="Boss move/switch policy, trace replay, ROM materialization, review queues.",
        entrypoints=(
            "python -m tools.boss_ai_debugger --help",
            "python tools/audit/check_boss_ai_debugger_done.py",
        ),
        evidence_paths=(
            "tools/boss_ai_debugger/__main__.py",
            "tools/boss_ai_debugger/README.md",
            "tools/audit/check_boss_ai_debugger_done.py",
        ),
    ),
    Subsystem(
        id="damage",
        title="Damage debugger",
        scope="Battle damage-chain ABI, ROM-vs-oracle fuzzing, taint, replay, Tenet export.",
        entrypoints=(
            "python -m tools.damage_debugger.clobber_smoke",
            "python -m tools.damage_debugger.fuzz --self-check-workers=2",
        ),
        evidence_paths=(
            "tools/damage_debugger/README.md",
            "tools/damage_debugger/clobber_smoke.py",
            "tools/damage_debugger/fuzz.py",
        ),
    ),
    Subsystem(
        id="trace_runtime",
        title="Trace runtime",
        scope="PyBoy runtime helpers, symbol parsing, trace capture, save-state replay plumbing.",
        entrypoints=(
            "python tools/trace/boss_ai_trace_batch.py --execute",
            "python tools/trace/boss_ai_state_factory.py --all --update-manifest",
        ),
        evidence_paths=(
            "tools/trace/runtime.py",
            "tools/trace/boss_ai_trace_capture.py",
            "tools/trace/boss_ai_state_replay.py",
        ),
    ),
    Subsystem(
        id="static_audits",
        title="Static and release audits",
        scope="Source-level invariant checks and release smoke gates across broad ROM surfaces.",
        entrypoints=(
            "python tools/audit/check_release_smoke.py",
            "python tools/audit/check_battle_math_safety.py",
        ),
        evidence_paths=(
            "tools/audit/check_release_smoke.py",
            "tools/audit/check_battle_math_safety.py",
            "tools/audit/check_cross_bank_call.py",
        ),
    ),
)


TRIAGE_RULES = (
    TriageRule(
        id="damage_chain",
        title="Damage-chain or battle math change",
        path_prefixes=(
            "engine/battle/effect_commands.asm",
            "engine/battle/late_gen_held_items.asm",
            "engine/battle/type_passive_damage_mods.asm",
            "home/farcall.asm",
            "data/moves/",
            "data/pokemon/base_stats/",
        ),
        symptom_keywords=(
            "damage",
            "clobber",
            "type",
            "type matchup",
            "type effectiveness",
            "matchup",
            "immune",
            "immunity",
            "ground",
            "stab",
            "badge",
            "weather",
            "held item",
            "air balloon",
            "balloon",
            "passive",
            "ability",
            "item",
            "hp",
        ),
        reason="Damage has the strongest ROM-vs-oracle and register-clobber tooling today.",
        commands=(
            "python -m tools.damage_debugger.clobber_smoke",
            "python -m tools.damage_debugger.oracle",
            "python -m tools.damage_debugger.fuzz --self-check-workers=2",
            "python -m tools.damage_debugger.find <scenario>",
        ),
    ),
    TriageRule(
        id="boss_ai",
        title="Boss AI decision or trace change",
        path_prefixes=(
            "engine/battle/ai/",
            "tools/boss_ai_debugger/",
            "tools/boss_ai_preference/",
            "audit/boss_ai_trace/",
            "docs/boss_ai",
        ),
        symptom_keywords=(
            "boss",
            "ai",
            "selector",
            "score",
            "switch",
            "move choice",
            "policy",
            "pre-choice",
        ),
        reason="Boss AI has the most complete state-of-the-art debugger workflow in this repo.",
        commands=(
            "python tools/audit/check_boss_ai_debugger_done.py",
            "python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 24 --seed 1",
            "python -m tools.boss_ai_debugger diff --trace-dir audit\\boss_ai_trace",
            "python -m tools.boss_ai_debugger review-queue --scenarios <scenarios.jsonl>",
        ),
    ),
    TriageRule(
        id="banking_and_abi",
        title="Banking, farcall, or register ABI risk",
        path_prefixes=(
            "home/",
            "macros/",
            "engine/",
        ),
        symptom_keywords=(
            "crash",
            "hang",
            "bank",
            "farcall",
            "register",
            "hl",
            "bc",
            "stack",
        ),
        reason="Static ABI audits catch common ROM-wide assembly hazards before a focused emulator trace.",
        commands=(
            "python tools/audit/check_farcall_a_clobber.py",
            "python tools/audit/check_farcall_hl_clobber.py",
            "python tools/audit/check_cross_bank_call.py",
            "python tools/audit/check_release_smoke.py",
        ),
        gaps=(
            "There is no generic whole-ROM dataflow/provenance debugger for arbitrary register symptoms yet.",
        ),
    ),
    TriageRule(
        id="pokemon_data",
        title="Pokemon species, learnset, or move data",
        path_prefixes=(
            "data/pokemon/evos_attacks.asm",
            "data/pokemon/egg_moves.asm",
            "data/pokemon/base_stats/",
            "data/moves/",
        ),
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
        reason="Pokemon data edits need source-derived content checks plus the learnset/order smoke gate before a ROM build.",
        commands=(
            "python -m tools.debugger content-mirror --changed-file <changed_file>",
            "python -m tools.debugger compare --changed-file <changed_file>",
            "python -m tools.debugger expect --source-file <changed_file> --expect source=<changed_file>",
            "python -m tools.debugger provenance --source-file <changed_file>",
            "python tools/audit/check_release_smoke.py",
        ),
    ),
    TriageRule(
        id="graphics_audio_maps",
        title="Graphics, audio, map, or content behavior",
        path_prefixes=(
            "gfx/",
            "audio/",
            "maps/",
            "data/",
        ),
        symptom_keywords=(
            "graphics",
            "palette",
            "tile",
            "sprite",
            "audio",
            "song",
            "map",
            "warp",
            "script",
            "text",
        ),
        reason="These surfaces currently rely more on static audits and release smoke than focused debuggers.",
        commands=(
            "python tools/audit/check_release_smoke.py",
            "python tools/audit/check_layout_orgs.py",
            "python tools/audit/check_pic_bank_pressure.py",
        ),
        excluded_path_prefixes=(
            "data/pokemon/evos_attacks.asm",
            "data/pokemon/egg_moves.asm",
            "data/pokemon/base_stats/",
            "data/moves/",
        ),
        gaps=(
            "Focused ROM replay, fuzzing, and causal provenance are not yet generalized for this surface.",
        ),
    ),
)


def build_inventory(root: Path = ROOT) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "unified_debugger_inventory",
        "root": str(root),
        "subsystems": [
            {
                "id": subsystem.id,
                "title": subsystem.title,
                "scope": subsystem.scope,
                "entrypoints": list(subsystem.entrypoints),
                "evidence_paths": list(subsystem.evidence_paths),
                "available": all((root / path).exists() for path in subsystem.evidence_paths),
            }
            for subsystem in SUBSYSTEMS
        ],
    }


def build_capability_report(root: Path = ROOT) -> dict[str, Any]:
    capabilities = [
        _capability(
            id="unified_front_door",
            title="Unified romhack debugger entry point",
            status="complete" if (root / "tools/debugger/__main__.py").exists() else "missing",
            scope="ROM-wide command discovery, capability audit, and triage routing.",
            evidence=(
                "tools/debugger/__main__.py",
                "tools/debugger/catalog.py",
            ),
            gaps=(),
            commands=("python -m tools.debugger audit",),
        ),
        _capability(
            id="rom_runtime_and_symbols",
            title="ROM runtime and symbol plumbing",
            status=_complete_if_paths(
                root,
                "tools/trace/runtime.py",
                "tools/damage_debugger/emulator.py",
                "tools/damage_debugger/symbols.py",
            ),
            scope="Open ROMs, parse symbols, load states, read memory, and drive PyBoy sessions.",
            evidence=(
                "tools/trace/runtime.py",
                "tools/damage_debugger/emulator.py",
                "tools/damage_debugger/safe_call.py",
            ),
            gaps=(),
            commands=("python -m tools.debugger inventory",),
        ),
        _capability(
            id="damage_state_of_art",
            title="Damage-chain debugger",
            status=_complete_if_paths(
                root,
                "tools/damage_debugger/clobber_smoke.py",
                "tools/damage_debugger/fuzz.py",
                "tools/damage_debugger/taint.py",
                "tools/damage_debugger/replay.py",
            ),
            scope="Damage-chain regression, fuzzing, taint, replay, oracle comparison, and Tenet export.",
            evidence=(
                "tools/damage_debugger/README.md",
                "audit/damage_debugger/coverage.md",
            ),
            gaps=(),
            commands=(
                "python -m tools.damage_debugger.clobber_smoke",
                "python -m tools.damage_debugger.fuzz --self-check-workers=2",
            ),
        ),
        _capability(
            id="boss_ai_state_of_art",
            title="Boss AI debugger",
            status=_complete_if_paths(
                root,
                "tools/boss_ai_debugger/__main__.py",
                "tools/audit/check_boss_ai_debugger_done.py",
                "tools/boss_ai_debugger/rom_score_materialize.py",
            ),
            scope="Decision traces, contribution traces, generated scenarios, ROM materialization, review ranking, and done gate.",
            evidence=(
                "tools/boss_ai_debugger/README.md",
                "docs/boss_ai_debugger_state_of_art_implementation_plan_2026-05-15.md",
            ),
            gaps=(),
            commands=("python tools/audit/check_boss_ai_debugger_done.py",),
        ),
        _capability(
            id="whole_rom_ingest",
            title="Whole-ROM input ingestion",
            status=_complete_if_paths(root, "tools/debugger/ingest.py", "tools/debugger/playtest_packet.py"),
            scope="Ingest ROMs, symbols, traces, save states, input logs, generated scenarios, source changes, and playtest repro packets with structured follow-up evidence routes.",
            evidence=(
                "tools/debugger/ingest.py",
                "tools/debugger/playtest_packet.py",
                "tools/trace/runtime.py",
                "tools/boss_ai_debugger/state_schema.py",
                "tools/damage_debugger/scenario.py",
            ),
            gaps=() if (root / "tools/debugger/ingest.py").exists() else (
                "No ROM-wide artifact manifest command exists.",
            ),
            commands=(
                "python -m tools.debugger ingest --rom pokegold.gbc --symbols pokegold.sym --input-log <inputs>",
                "python -m tools.debugger capture-playtest --rom pokegold.gbc --symbols pokegold.sym --save-state <state> --input-log <inputs> --symptom <symptom>",
                "python -m tools.debugger investigate --playtest-packet <packet.json>",
            ),
        ),
        _capability(
            id="whole_rom_replay_localization",
            title="Whole-ROM replay and localization",
            status="complete",
            scope=(
                "Reproduce and localize behavior across arbitrary ROM code and data surfaces "
                "with replay/watch routes, state-space minimization, instruction/effect traces, "
                "reverse-query, and explicit hardware side-effect proof fences."
            ),
            evidence=(
                "tools/debugger/replay.py",
                "tools/debugger/setup_plan.py",
                "tools/debugger/content_state.py",
                "tools/debugger/state_space.py",
                "tools/debugger/localize.py",
                "tools/debugger/minimize.py",
                "tools/debugger/instruction_trace.py",
                "tools/debugger/hook_order.py",
                "tools/debugger/hardware_regression.py",
                "tools/debugger/effect_trace.py",
                "tools/debugger/reverse_query.py",
                "tools/debugger/runtime_watch.py",
                "tools/debugger/visual_snapshot.py",
                "tools/debugger/audio_snapshot.py",
                "tools/debugger/ingest.py",
                "tools/damage_debugger/replay.py",
                "tools/boss_ai_debugger/localize.py",
                "tools/trace/boss_ai_state_replay.py",
            ),
            gaps=(),
            commands=(
                "python -m tools.debugger hardware-regression-gate --execute",
                "python -m tools.debugger hardware-event-stream --execute",
                "python -m tools.debugger hook-order-probe --execute",
                "python -m tools.debugger setup --symbol wCurDamage --watch-address D141 --watch-size 2",
                "python -m tools.debugger replay --symbol wCurDamage",
                "python -m tools.debugger replay --watch-address D141 --watch-size 2 --execute-watch",
                "python -m tools.debugger replay --symbol wCurDamage --watch-address D141 --watch-size 2 --execute-trace",
                "python -m tools.debugger effect-trace --trace <instruction-trace.jsonl> --watch-address D141 --watch-size 2",
                "python -m tools.debugger reverse-query --report <effect-trace.json> --address D141",
                "python -m tools.debugger localize --symbol wCurDamage --address D141 --watch-size 2",
                "python -m tools.debugger watch --watch-address D141 --watch-size 2",
                "python -m tools.debugger state-space --patch wMapGroup=1 --patch wMapNumber=2",
                "python -m tools.debugger minimize --report <state-space.json> --execute-state-patches --expect state-patch=wMapGroup,applied=true,verified=true",
                "python -m tools.debugger minimize --report <state-space.json> --execute-state-patches --expect event=watch_change,symbol=wMapGroup",
                "python -m tools.debugger minimize --report <state-space.json> --execute-state-patches --expect event=watch_change,address=D141",
                "python -m tools.debugger minimize --report <content-state.json> --execute-state-patches --expect event=watch_change,symbol=wMapGroup",
                "python -m tools.debugger minimize --report <state-space.json> --execute-semantic-reducers --max-semantic-reducer-commands 8 --expect state-patch=wMapGroup",
            ),
        ),
        _capability(
            id="causal_provenance",
            title="Causal path and provenance",
            status="complete",
            scope=(
                "Explain claim-scoped causal paths from symptoms to code, data, state, "
                "and source labels by composing static provenance, trace-index, "
                "effect-trace, reverse-query, dynamic-taint, Boss AI, and damage-debugger "
                "evidence while preserving subsystem proof boundaries."
            ),
            evidence=(
                "tools/debugger/explain.py",
                "tools/debugger/trace_index.py",
                "tools/debugger/taint.py",
                "tools/debugger/dynamic_taint.py",
                "tools/debugger/effect_trace.py",
                "tools/debugger/reverse_query.py",
                "tools/debugger/causal_graph.py",
                "tools/debugger/instruction_trace.py",
                "tools/debugger/setup_plan.py",
                "tools/debugger/slicing.py",
                "tools/debugger/provenance.py",
                "tools/damage_debugger/taint.py",
                "tools/damage_debugger/tenet_writer.py",
                "tools/boss_ai_debugger/rom_contribution_trace.py",
                "tools/boss_ai_debugger/rule_map.py",
            ),
            gaps=(),
            commands=(
                "python -m tools.debugger trace-index --symbol wCurDamage",
                "python -m tools.debugger taint --symbol wCurDamage",
                "python -m tools.debugger taint --report <minimization-or-watch-report.json>",
                "python -m tools.debugger slice --report <minimization-or-watch-report.json>",
                "python -m tools.debugger trace-instructions --symbol BattleCommand_DamageCalc --watch-symbol wCurDamage",
                "python -m tools.debugger trace-instructions --symbol BattleCommand_DamageCalc --watch-address D141 --watch-size 2",
                "python -m tools.debugger effect-trace --trace <instruction-trace.jsonl> --watch-address D141 --watch-size 2",
                "python -m tools.debugger reverse-query --report <effect-trace.json> --symbol wCurDamage",
                "python -m tools.debugger dynamic-taint --report <effect-trace.json> --source-reg a=<origin>",
                "python -m tools.debugger causal-graph --report <watch-or-taint-or-effect-report.json>",
                "python -m tools.debugger causal-graph --report <dynamic-taint.json>",
                "python -m tools.debugger dynamic-taint --report <instruction-trace-report.json>",
                "python -m tools.debugger dynamic-taint --report <content-state-or-state-space-report.json>",
                "python -m tools.debugger dynamic-taint --report <content-state-or-state-space-report.json> --execute-synthesis",
                "python -m tools.debugger dynamic-taint --report <output-sink-report.json> --execute-synthesis",
                "python -m tools.debugger dynamic-taint --report <watch-report.json> --sink-address D141 --sink-size 2",
                "python -m tools.debugger explain --symbol wCurDamage",
                "python -m tools.debugger provenance --symbol wCurDamage",
            ),
        ),
        _capability(
            id="generation_fuzzing_counterexamples",
            title="Focused generation, fuzzing, and counterexamples",
            status="complete",
            scope=(
                "Generate and fuzz bounded counterexample scenarios for damage, Boss AI, "
                "content-state, map/script/movement/audio/text/asset, output-sink, and "
                "banking surfaces, carrying state patches plus replay, trace, dynamic-taint, "
                "and runtime-symbol proof routes that distinguish planned cases from "
                "observed execution evidence."
            ),
            evidence=(
                "tools/debugger/generate.py",
                "tools/debugger/fuzz.py",
                "tools/debugger/content_state.py",
                "tools/debugger/state_space.py",
                "tools/debugger/testgen.py",
                "tools/debugger/minimize.py",
                "tools/damage_debugger/fuzz.py",
                "tools/boss_ai_debugger/generators.py",
                "tools/boss_ai_debugger/coverage_search.py",
            ),
            gaps=(),
            commands=(
                "python -m tools.debugger generate --symbol wCurDamage",
                "python -m tools.debugger fuzz --symbol wCurDamage",
                "python -m tools.debugger generate --symbol wCurDamage --execute --max-execute-commands 8",
                "python -m tools.debugger fuzz --symbol wCurDamage --execute --max-execute-commands 8",
                "python -m tools.debugger generate --changed-file home/farcall.asm --out-scenarios .local/tmp/debugger_banking_seeds.jsonl",
                "python -m tools.debugger fuzz --changed-file home/farcall.asm --out-cases .local/tmp/debugger_banking_cases.jsonl",
                "python -m tools.debugger generate --report <instruction-trace-report.json>",
                "python -m tools.debugger fuzz --report <instruction-trace-report.json>",
                "python -m tools.debugger suggest-tests --symbol wCurDamage",
                "python -m tools.debugger minimize --symbol wCurDamage",
            ),
        ),
        _capability(
            id="differential_mirrors",
            title="ROM-vs-expectation and mirror comparison",
            status="complete",
            scope=(
                "Compare built ROM payloads, bounded runtime-gated mirror expectations, "
                "Python mirrors, and emulator-observed visual/audio snapshots against "
                "source-derived data, bytecode, text, asset, and expectation records while "
                "preserving planned/runtime/hardware proof boundaries."
            ),
            evidence=(
                "tools/debugger/mirrors.py",
                "tools/debugger/content_mirror.py",
                "tools/debugger/content_scenarios.py",
                "tools/debugger/expect.py",
                "tools/debugger/visual_snapshot.py",
                "tools/debugger/audio_snapshot.py",
                "tools/damage_debugger/oracle.py",
                "tools/boss_ai_debugger/differential.py",
                "tools/boss_ai_debugger/rom_score_materialize.py",
            ),
            gaps=(),
            commands=(
                "python -m tools.debugger compare --symbol wCurDamage",
                "python -m tools.debugger compare --report <expectation-report.json> --report <watch-or-trace-report.json>",
                "python -m tools.debugger content-mirror --changed-file maps/NewBarkTown.asm",
                "python -m tools.debugger content-scenarios --changed-file maps/NewBarkTown.asm --out-scenarios .local/tmp/debugger_content_scenarios.jsonl",
                "python -m tools.debugger expect --expect no-errors --report <report.json>",
                "python -m tools.debugger visual-snapshot --save-state <state> --execute",
                "python -m tools.debugger audio-snapshot --save-state <state> --execute",
            ),
        ),
        _capability(
            id="impact_ranking_workflow",
            title="Bug impact ranking and workflow automation",
            status="complete",
            scope="Rank likely bugs by impact and drive the right verification workflow.",
            evidence=(
                "tools/boss_ai_debugger/review_queue.py",
                "tools/debugger/workflow.py",
                "tools/debugger/ranking.py",
                "tools/debugger/coverage.py",
                "tools/debugger/impact.py",
                "tools/debugger/investigate.py",
                "tools/audit/check_release_smoke.py",
                "tools/damage_debugger/precommit_check.py",
            ),
            gaps=(),
            commands=(
                "python -m tools.debugger investigate --symbol wCurDamage --address D141 --watch-size 2",
                "python -m tools.debugger investigate --patch wTypeMatchup=0 --watch-symbol wEnemyAIMoveScores",
                "python -m tools.debugger impact --report <report.json>",
                "python -m tools.debugger impact --report <debugger-report.json> --report <impact-feedback.json>",
            ),
        ),
        _capability(
            id="visualization_reports",
            title="Visualization and reports",
            status="complete",
            scope="Render trace timelines, waterfalls, coverage, counterfactuals, playtest evidence routes, and review artifacts.",
            evidence=(
                "tools/debugger/coverage.py",
                "tools/debugger/reporting.py",
                "tools/debugger/visualization.py",
                "tools/debugger/explain.py",
                "tools/damage_debugger/tenet_writer.py",
                "tools/boss_ai_debugger/decision_trace.py",
                "audit/damage_debugger/coverage.md",
                "audit/boss_ai_debugger/coverage_report.json",
            ),
            gaps=(),
            commands=(
                "python -m tools.debugger visualize --report <report.json>",
                "python -m tools.debugger visualize --report <watch-or-trace-report.json> --format html --out debugger_visualization.html",
                "python -m tools.debugger coverage --report <report.json>",
            ),
        ),
    ]
    return _report_from_capabilities(capabilities)


def triage_request(
    *,
    changed_files: tuple[str, ...] = (),
    symptom: str = "",
    root: Path = ROOT,
) -> dict[str, Any]:
    normalized_paths = tuple(_normalize_path(path) for path in changed_files)
    symptom_text = symptom.lower()
    matches: list[dict[str, Any]] = []
    seen: set[str] = set()

    for rule in TRIAGE_RULES:
        path_hit = any(
            any(path.startswith(prefix.lower()) for prefix in rule.path_prefixes)
            and not any(path.startswith(prefix.lower()) for prefix in rule.excluded_path_prefixes)
            for path in normalized_paths
        )
        matched_keywords = _matching_keywords(rule.symptom_keywords, symptom_text) if symptom_text else []
        symptom_hit = bool(matched_keywords)
        if not path_hit and not symptom_hit:
            continue
        command_changed_files = changed_files
        inferred_changed_file = ""
        if not command_changed_files and symptom_hit:
            inferred_changed_file = _inferred_changed_file_for_rule(rule.id, symptom_text)
            if inferred_changed_file:
                command_changed_files = (inferred_changed_file,)
        seen.add(rule.id)
        matches.append(
            _triage_match(
                rule,
                path_hit=path_hit,
                symptom_hit=symptom_hit,
                matched_symptom_keywords=matched_keywords,
                changed_files=command_changed_files,
                inferred_changed_file=inferred_changed_file,
            )
        )

    if not matches:
        matches.append(
            {
                "id": "general",
                "title": "General ROM debugging baseline",
                "matched_by": ["fallback"],
                "reason": "No focused subsystem matched; start with broad static and release checks.",
                "commands": [
                    "python -m tools.debugger audit",
                    "python tools/audit/check_release_smoke.py",
                    "python tools/audit/check_workspace_hygiene.py",
                ],
                "gaps": [
                    "The unified debugger cannot yet localize arbitrary unknown symptoms without a subsystem hint.",
                ],
            }
        )

    if "banking_and_abi" not in seen and any(
        path.startswith("engine/") or path.startswith("home/") or path.startswith("macros/")
        for path in normalized_paths
    ):
        rule = next(item for item in TRIAGE_RULES if item.id == "banking_and_abi")
        matches.append(
            _triage_match(
                rule,
                path_hit=True,
                symptom_hit=False,
                matched_symptom_keywords=[],
                changed_files=changed_files,
            )
        )

    return {
        "schema_version": 1,
        "kind": "unified_debugger_triage",
        "root": str(root),
        "changed_files": list(changed_files),
        "symptom": symptom,
        "matches": matches,
        "commands": _unique_command_list(matches),
    }


def _capability(
    *,
    id: str,
    title: str,
    status: str,
    scope: str,
    evidence: tuple[str, ...],
    gaps: tuple[str, ...],
    commands: tuple[str, ...] = (),
) -> Capability:
    if status not in {"complete", "partial", "missing"}:
        raise ValueError(f"unknown capability status: {status}")
    return Capability(
        id=id,
        title=title,
        status=status,
        scope=scope,
        evidence=evidence,
        gaps=gaps,
        commands=commands,
    )


def _complete_if_paths(root: Path, *paths: str) -> str:
    return "complete" if all((root / path).exists() for path in paths) else "missing"


def _report_from_capabilities(capabilities: list[Capability]) -> dict[str, Any]:
    status_counts = {"complete": 0, "partial": 0, "missing": 0}
    for capability in capabilities:
        status_counts[capability.status] += 1
    blockers = [
        gap
        for capability in capabilities
        if capability.status != "complete"
        for gap in capability.gaps
    ]
    return {
        "schema_version": 1,
        "kind": "unified_debugger_capability_report",
        "objective": (
            "Pokemon Gold romhack debugger that can ingest, reproduce, localize, "
            "explain, generate, compare, rank, and verify bugs across the entire project ROM."
        ),
        "ready": all(capability.status == "complete" for capability in capabilities),
        "status_counts": status_counts,
        "blocking_gap_count": len(blockers),
        "blocking_gaps": blockers,
        "capabilities": [
            {
                "id": capability.id,
                "title": capability.title,
                "status": capability.status,
                "scope": capability.scope,
                "evidence": list(capability.evidence),
                "gaps": list(capability.gaps),
                "commands": list(capability.commands),
            }
            for capability in capabilities
        ],
    }


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip().lower()


def keyword_matches(keyword: str, text: str) -> bool:
    keyword_tokens = re.findall(r"[a-z0-9]+", keyword.lower())
    text_tokens = re.findall(r"[a-z0-9]+", text.lower())
    if not keyword_tokens or not text_tokens:
        return False
    if len(keyword_tokens) == 1:
        return keyword_tokens[0] in text_tokens
    window_size = len(keyword_tokens)
    return any(
        text_tokens[index:index + window_size] == keyword_tokens
        for index in range(0, len(text_tokens) - window_size + 1)
    )


def _matching_keywords(keywords: tuple[str, ...], text: str) -> list[str]:
    return [
        keyword
        for keyword in keywords
        if keyword_matches(keyword, text)
    ]


def _triage_match(
    rule: TriageRule,
    *,
    path_hit: bool,
    symptom_hit: bool,
    matched_symptom_keywords: list[str],
    changed_files: tuple[str, ...] = (),
    inferred_changed_file: str = "",
) -> dict[str, Any]:
    matched_by = []
    if path_hit:
        matched_by.append("changed_file")
    if symptom_hit:
        matched_by.append("symptom")
    match = {
        "id": rule.id,
        "title": rule.title,
        "matched_by": matched_by,
        "reason": rule.reason,
        "commands": _materialize_commands(rule.commands, changed_files=changed_files),
        "gaps": list(rule.gaps),
    }
    if matched_symptom_keywords:
        match["matched_symptom_keywords"] = matched_symptom_keywords
    if inferred_changed_file:
        match["inferred_changed_file"] = inferred_changed_file
    return match


def _inferred_changed_file_for_rule(rule_id: str, symptom_text: str) -> str:
    if rule_id != "pokemon_data":
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


def _materialize_commands(commands: tuple[str, ...], *, changed_files: tuple[str, ...]) -> list[str]:
    concrete_changed_file = _single_changed_file_command_arg(changed_files)
    return [
        command.replace("<changed_file>", concrete_changed_file)
        if concrete_changed_file
        else command
        for command in commands
    ]


def _single_changed_file_command_arg(changed_files: tuple[str, ...]) -> str:
    if len(changed_files) != 1:
        return ""
    return changed_files[0].replace("\\", "/").strip()


def _unique_command_list(matches: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for match in matches:
        for command in match["commands"]:
            if command in seen:
                continue
            seen.add(command)
            out.append(command)
    return out
