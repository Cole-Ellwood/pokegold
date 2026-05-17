from __future__ import annotations

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
    gaps: tuple[str, ...] = ()


SUBSYSTEMS = (
    Subsystem(
        id="boss_ai",
        title="Boss AI debugger",
        scope="Boss move/switch policy, trace replay, ROM materialization, review queues.",
        entrypoints=(
            "python -m tools.boss_ai_debugger --help",
            "python tools\\audit\\check_boss_ai_debugger_done.py",
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
            "python tools\\trace\\boss_ai_trace_batch.py --execute",
            "python tools\\trace\\boss_ai_state_factory.py --all --update-manifest",
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
            "python tools\\audit\\check_release_smoke.py",
            "python tools\\audit\\check_battle_math_safety.py",
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
            "stab",
            "badge",
            "weather",
            "held item",
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
            "python tools\\audit\\check_boss_ai_debugger_done.py",
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
            "python tools\\audit\\check_farcall_a_clobber.py",
            "python tools\\audit\\check_farcall_hl_clobber.py",
            "python tools\\audit\\check_cross_bank_call.py",
            "python tools\\audit\\check_release_smoke.py",
        ),
        gaps=(
            "There is no generic whole-ROM dataflow/provenance debugger for arbitrary register symptoms yet.",
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
            "python tools\\audit\\check_release_smoke.py",
            "python tools\\audit\\check_layout_orgs.py",
            "python tools\\audit\\check_pic_bank_pressure.py",
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
            commands=("python tools\\audit\\check_boss_ai_debugger_done.py",),
        ),
        _capability(
            id="whole_rom_ingest",
            title="Whole-ROM input ingestion",
            status=_complete_if_paths(root, "tools/debugger/ingest.py"),
            scope="Ingest ROMs, symbols, traces, save states, generated scenarios, and source changes.",
            evidence=(
                "tools/debugger/ingest.py",
                "tools/trace/runtime.py",
                "tools/boss_ai_debugger/state_schema.py",
                "tools/damage_debugger/scenario.py",
            ),
            gaps=() if (root / "tools/debugger/ingest.py").exists() else (
                "No ROM-wide artifact manifest command exists.",
            ),
            commands=(
                "python -m tools.debugger ingest --rom pokegold.gbc --symbols pokegold.sym",
            ),
        ),
        _capability(
            id="whole_rom_replay_localization",
            title="Whole-ROM replay and localization",
            status="partial",
            scope="Reproduce and localize behavior across arbitrary ROM code and data surfaces.",
            evidence=(
                "tools/debugger/replay.py",
                "tools/debugger/setup_plan.py",
                "tools/debugger/content_state.py",
                "tools/debugger/localize.py",
                "tools/debugger/runtime_watch.py",
                "tools/debugger/ingest.py",
                "tools/damage_debugger/replay.py",
                "tools/boss_ai_debugger/localize.py",
                "tools/trace/boss_ai_state_replay.py",
            ),
            gaps=(
                "Unified replay planning, setup/trigger materialization routing with explicit state synthesis recipes, content trigger precondition records, precondition-aware content scenario subset extraction, content positioned-state trigger coverage, content map-position, script-entry, and movement-entry WRAM patch materialization, content-state plus explicit generic state-space WRAM patch-set minimization against explicit expectations, scenario/report save-state discovery, instruction-trace reuse of executed content-state output states, generic watch execution, bounded dynamic watch-context windows, source-cause watch candidates, content scenario runtime helper/watch probes, content positioned-state instruction-trace proof routes, and expectation-preserving trace/report/context minimization exist, but executed semantic state-space minimization still needs emulator-backed reducers beyond the materialized surfaces.",
                "Replay/localization now consumes setup save-state discovery, reverse attribution, expectation failures, minimized evidence artifacts, watch-hit context frames, content ROM mirrors, and content scenario runtime targets, but exact dynamic replay is still deepest for damage and Boss AI.",
                "Watch replay reports changes, preceding frame context, PC/register snapshots, bounded static source-cause candidates, and dynamic-taint sink-write attribution can now name exact sink-writing SM83 instructions and source operands, but full reverse execution across every CPU side effect is still not implemented.",
            ),
            commands=(
                "python -m tools.debugger setup --symbol wCurDamage",
                "python -m tools.debugger replay --symbol wCurDamage",
                "python -m tools.debugger localize --symbol wCurDamage",
            ),
        ),
        _capability(
            id="causal_provenance",
            title="Causal path and provenance",
            status="partial",
            scope="Explain exact paths from symptom to code, data, state, and source labels.",
            evidence=(
                "tools/debugger/explain.py",
                "tools/debugger/trace_index.py",
                "tools/debugger/taint.py",
                "tools/debugger/dynamic_taint.py",
                "tools/debugger/instruction_trace.py",
                "tools/debugger/setup_plan.py",
                "tools/debugger/slicing.py",
                "tools/debugger/provenance.py",
                "tools/damage_debugger/taint.py",
                "tools/damage_debugger/tenet_writer.py",
                "tools/boss_ai_debugger/rom_contribution_trace.py",
                "tools/boss_ai_debugger/rule_map.py",
            ),
            gaps=(
                "Unified causal explanation now bridges watch/replay/trace-index evidence, bounded reverse-attribution windows, setup/trigger planning with explicit state synthesis recipes, coverage blockers, discovered save states, content scenario runtime trigger/source/helper/watch paths, content-state materialization helper/watch paths, report/source/symptom-selected instruction trace capture with executed content-state save reuse and execution-hit validation, source-level SM83 taint slices, report-discovered instruction-trace dynamic taint, exact sink-write attribution without source seeds, and static source slices, but arbitrary-output taint still needs automatic save-state synthesis across every ROM surface.",
                "Boss AI provenance is branch/probe based; damage provenance is trace/taint based; the new source-level taint bridge helps connect them but does not replace subsystem dynamic proof.",
            ),
            commands=(
                "python -m tools.debugger trace-index --symbol wCurDamage",
                "python -m tools.debugger taint --symbol wCurDamage",
                "python -m tools.debugger trace-instructions --symbol BattleCommand_DamageCalc --watch-symbol wCurDamage",
                "python -m tools.debugger dynamic-taint --report <instruction-trace-report.json>",
                "python -m tools.debugger explain --symbol wCurDamage",
                "python -m tools.debugger provenance --symbol wCurDamage",
            ),
        ),
        _capability(
            id="generation_fuzzing_counterexamples",
            title="Focused generation, fuzzing, and counterexamples",
            status="partial",
            scope="Generate focused tests and counterexamples for any ROM behavior.",
            evidence=(
                "tools/debugger/generate.py",
                "tools/debugger/fuzz.py",
                "tools/debugger/content_state.py",
                "tools/debugger/testgen.py",
                "tools/debugger/minimize.py",
                "tools/damage_debugger/fuzz.py",
                "tools/boss_ai_debugger/generators.py",
                "tools/boss_ai_debugger/coverage_search.py",
            ),
            gaps=(
                "Unified generation and fuzz coordinators now write deterministic seed/case manifests, route to focused generators, preserve content scenario state preconditions, generate map positioned-state, script-entry, and movement-entry materialization/replay/instruction-trace routes, include script command-stream, text-block, and movement-data scenarios, route ready instruction-trace reports into dynamic-taint handoff campaigns/cases, and hand expectation-preserving evidence to downstream tools, but semantic generator execution remains subsystem-specific outside the materialized surfaces.",
                "Fuzzing is mature for damage and generated Boss AI policy cases; map content scenarios now get positioned-state WRAM patch generation plus replay/instruction-trace routes, script command streams get script-entry WRAM patch generation plus RunScriptCommand trace/watch routes, movement data gets movement-entry WRAM patch generation plus ApplyMovement/HandleMovementData trace/watch routes, audio and asset content get explicit runtime watch/trace proof routes, and text blocks get replay/provenance/trace helper routes, while graphics/audio/UI semantic playback, banking, full script VM behavior under arbitrary event-engine context, and arbitrary event-engine states still need dedicated dynamic ROM generators.",
            ),
            commands=(
                "python -m tools.debugger generate --symbol wCurDamage",
                "python -m tools.debugger fuzz --symbol wCurDamage",
                "python -m tools.debugger generate --report <instruction-trace-report.json>",
                "python -m tools.debugger fuzz --report <instruction-trace-report.json>",
                "python -m tools.debugger suggest-tests --symbol wCurDamage",
                "python -m tools.debugger minimize --symbol wCurDamage",
            ),
        ),
        _capability(
            id="differential_mirrors",
            title="ROM-vs-expectation and mirror comparison",
            status="partial",
            scope="Compare ROM behavior against high-level expectations and Python mirrors.",
            evidence=(
                "tools/debugger/mirrors.py",
                "tools/debugger/content_mirror.py",
                "tools/debugger/content_scenarios.py",
                "tools/debugger/expect.py",
                "tools/damage_debugger/oracle.py",
                "tools/boss_ai_debugger/differential.py",
                "tools/boss_ai_debugger/rom_score_materialize.py",
            ),
            gaps=(
                "Mirror/oracle routing, generic trace expectations, scenario/precondition expectation gates, romhack-aware static content mirrors, source-derived content scenarios, and content-state behavioral mirror checks exist, but exact dynamic semantic mirrors are deep for damage and Boss AI only.",
                "Maps can now byte-compare source-derived _MapEvents tables against the built ROM, common script-command bytecode including map-action, battle setup, trainer record, mart/shop, random branch, command queue/stone-table, banked callasm/autoinput, music fade, catch tutorial, local doorstate macro, and local-label script/text bytes can be byte-compared against script labels, text macro blocks and RGBDS decimal interpolations can be charmap-encoded and byte-compared against text labels, movement data streams can be byte-compared against movement labels, audio channel headers can be byte-compared against ROM payloads, labeled db/dw/dn RGBDS data/string blocks and labeled/aggregate INCBIN assets can be byte-compared against ROM payloads, map/script/movement content-state reports can be compared through state-patch expectations plus replay/watch proof routes, and audio/asset content-state reports now expose helper watch/trace proof routes; full script VM behavior under arbitrary surrounding event-engine state, graphics/UI behavior, full audio playback, and arbitrary map interactions still need dedicated emulator-backed behavioral ROM mirrors.",
            ),
            commands=(
                "python -m tools.debugger compare --symbol wCurDamage",
                "python -m tools.debugger content-mirror --changed-file maps\\NewBarkTown.asm",
                "python -m tools.debugger content-scenarios --changed-file maps\\NewBarkTown.asm --out-scenarios .local\\tmp\\debugger_content_scenarios.jsonl",
                "python -m tools.debugger expect --expect no-errors --report <report.json>",
            ),
        ),
        _capability(
            id="impact_ranking_workflow",
            title="Bug impact ranking and workflow automation",
            status="partial",
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
            gaps=(
                "A unified investigation packet now coordinates ingest, replay, trace indexing, expectations, generation, ranking, reporting, and visualization; content-state materializations, instruction-trace validation, and ROM-surface severity calibration now feed rank/impact directly, but per-subsystem semantic severity models still need deeper ROM behavior calibration outside damage and Boss AI.",
                "Whole-ROM gate failures, watch hits, dynamic sink-write attributions, instruction-trace hook misses/limits/dynamic-taint readiness, mirror gaps, content-state ready/blocked/executed state patches, ingest errors, investigation failures, explicit suspect inputs, and banking/event/map/movement/text/audio/graphics/UI/data surface risk hints are normalized; learned semantic impact still needs expansion.",
            ),
            commands=(
                "python -m tools.debugger investigate --symbol wCurDamage",
                "python -m tools.debugger impact --report <report.json>",
            ),
        ),
        _capability(
            id="visualization_reports",
            title="Visualization and reports",
            status="partial",
            scope="Render trace timelines, waterfalls, coverage, counterfactuals, and review artifacts.",
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
            gaps=(
                "Unified visualizations now render timelines, workflow waterfalls, causal graphs, coverage lanes, impact lanes, content-state materialization/state-patch lanes, instruction-trace validation lanes, ready/miss/limit trace waterfall states, and a self-contained HTML evidence inspector with search and lane/source/severity filters; emulator-coupled TUI/canvas inspectors remain subsystem-specific.",
            ),
            commands=(
                "python -m tools.debugger visualize --report <report.json>",
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
            for path in normalized_paths
        )
        symptom_hit = bool(symptom_text) and any(
            keyword in symptom_text for keyword in rule.symptom_keywords
        )
        if not path_hit and not symptom_hit:
            continue
        seen.add(rule.id)
        matches.append(_triage_match(rule, path_hit=path_hit, symptom_hit=symptom_hit))

    if not matches:
        matches.append(
            {
                "id": "general",
                "title": "General ROM debugging baseline",
                "matched_by": ["fallback"],
                "reason": "No focused subsystem matched; start with broad static and release checks.",
                "commands": [
                    "python -m tools.debugger audit",
                    "python tools\\audit\\check_release_smoke.py",
                    "python tools\\audit\\check_workspace_hygiene.py",
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
        matches.append(_triage_match(rule, path_hit=True, symptom_hit=False))

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


def _triage_match(
    rule: TriageRule,
    *,
    path_hit: bool,
    symptom_hit: bool,
) -> dict[str, Any]:
    matched_by = []
    if path_hit:
        matched_by.append("changed_file")
    if symptom_hit:
        matched_by.append("symptom")
    return {
        "id": rule.id,
        "title": rule.title,
        "matched_by": matched_by,
        "reason": rule.reason,
        "commands": list(rule.commands),
        "gaps": list(rule.gaps),
    }


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
