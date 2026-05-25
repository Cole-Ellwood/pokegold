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
    gap_actions: tuple["GapAction", ...] = ()


@dataclass(frozen=True)
class GapAction:
    id: str
    title: str
    gap: str
    lived_scenario: str
    commands: tuple[str, ...]
    regression_gate: str
    evidence_standard: tuple[str, ...]
    disproof_standard: tuple[str, ...]
    source_refs: tuple[str, ...] = ()


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
        id="headless_battle",
        title="Headless battle simulator",
        scope="Text/JSON no-GUI selected-turn battle simulation with explicit proof labels.",
        entrypoints=(
            "python -m tools.headless_battle --template",
            "python tools\\audit\\check_headless_battle_simulator.py",
        ),
        evidence_paths=(
            "tools/headless_battle/simulator.py",
            "tools/headless_battle/README.md",
            "tools/audit/check_headless_battle_simulator.py",
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
        id="boss_ai_live_move",
        title="Boss AI live move-choice or legality symptom",
        path_prefixes=(
            "engine/battle/ai/boss_policy_move.asm",
            "tools/boss_ai_debugger/damage_ai_report.py",
            "tools/boss_ai_debugger/move_score_probe.py",
        ),
        symptom_keywords=(
            "falkner",
            "silver",
            "hypnosis",
            "sleep clause",
            "leer",
            "normal move",
            "doesn't affect",
            "doesnt affect",
            "hidden power",
            "boss used",
        ),
        reason="Recent live boss-move bugs are fastest to inspect with exact damage plus move-score probes before generic damage debugging.",
        commands=(
            "python -m tools.boss_ai_debugger damage-ai-report --trainer <TRAINER> --enemy <ENEMY> --player-save <save.sav> --player-slot <slot> --sleep-clause both",
            "python -m tools.boss_ai_debugger move-score-probe --trainer <TRAINER> --enemy <ENEMY> --player-save <save.sav> --player-slot <slot> --trace",
            "python tools\\audit\\check_damage_ai_report.py",
            "python tools\\audit\\check_move_score_probe.py",
        ),
    ),
    TriageRule(
        id="headless_battle",
        title="Headless text/JSON selected-turn battle simulation",
        path_prefixes=(
            "tools/headless_battle/",
            "tools/audit/check_headless_battle_simulator.py",
        ),
        symptom_keywords=(
            "headless battle",
            "battle simulator",
            "simulate a battle",
            "text-only battle",
            "text only battle",
            "no gui",
            "fixed rng",
            "exhaustive rng",
        ),
        reason="The no-GUI selected-turn simulator has its own proof-labeled text/JSON path and audit gate.",
        commands=(
            "python -m tools.headless_battle --template",
            "python tools\\audit\\check_headless_battle_simulator.py",
        ),
        gaps=(
            "Full battle automation, switch flow, speed ties, RNG-consuming mechanics outside damage variation, accuracy, status, live Boss AI scoring, and scripts remain outside the headless simulator until separately proven.",
        ),
    ),
    TriageRule(
        id="overworld_status",
        title="Overworld status, poison-step, or field HP state",
        path_prefixes=(
            "engine/events/poisonstep.asm",
            "engine/overworld/",
        ),
        symptom_keywords=(
            "walking poison",
            "overworld poison",
            "poison cure",
            "1 hp",
            "0 hp",
            "poisoned mon",
        ),
        reason="The poison-step bug class has a focused runtime audit; route there before broad battle damage checks.",
        commands=(
            "python tools\\audit\\check_overworld_poison_cure.py",
            "python -m tools.debugger investigate --changed-file engine/events/poisonstep.asm",
        ),
    ),
    TriageRule(
        id="base_ai_mechanics",
        title="Base non-boss AI mechanics and move legality",
        path_prefixes=(
            "engine/battle/ai/move.asm",
            "engine/battle/ai/scoring.asm",
            "engine/battle/ai/redundant.asm",
        ),
        symptom_keywords=(
            "assault vest",
            "choice lock",
            "choice locked",
            "regular trainer",
            "non-boss",
            "base ai",
            "illegal status",
        ),
        reason="Base AI legality and shared scoring have a focused source audit separate from Boss AI policy.",
        commands=(
            "python tools\\audit\\check_base_ai_mechanics_correctness.py",
            "python tools\\audit\\check_release_smoke.py",
        ),
    ),
    TriageRule(
        id="pokemon_semantics",
        title="Pokemon data semantics, learnsets, party state, or type passives",
        path_prefixes=(
            "data/pokemon/evos_attacks.asm",
            "data/pokemon/evos_attacks_pointers.asm",
            "data/pokemon/base_stats/",
            "engine/battle/type_passive_damage_mods.asm",
        ),
        symptom_keywords=(
            "learnset",
            "moveset",
            "confusion",
            "spite",
            "grass heal",
            "grass regrowth",
            "hoppip",
            "passive heal",
        ),
        reason="Pokemon data questions need semantic source/save inspection, not only byte mirroring.",
        commands=(
            "python -m tools.debugger learnset-inspect --species <SPECIES> --level <LEVEL>",
            "python -m tools.debugger party-inspect --save <save.sav> --slot <slot>",
            "python -m tools.debugger grass-regrowth --max-total-hp 300",
        ),
    ),
    TriageRule(
        id="static_bug_hunt",
        title="Static bug-family lead finder",
        path_prefixes=(
            "engine/battle/move_effects/",
            "engine/battle/ai/boss_policy_move.asm",
        ),
        symptom_keywords=(
            "wcur species",
            "wcurspecies",
            "base data",
            "getbasedata",
            "mirror move",
            "sketch",
            "mimic",
            "disable",
            "encore",
            "spite",
        ),
        reason="Prior real bugs in this repo cluster around global base-data mutation and unbounded move searches; the lead finder routes those patterns quickly.",
        commands=(
            "python tools\\audit\\bug_hunt_triage.py --max-leads 12",
            "python -m tools.debugger provenance --symbol wCurSpecies --symbol GetBaseData",
        ),
    ),
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
            "python tools\\audit\\check_boss_ai_debugger_done.py",
            "python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 24 --seed 1",
            "python -m tools.boss_ai_debugger diff --trace-dir audit\\boss_ai_trace",
            "python -m tools.boss_ai_debugger review-queue --scenarios <scenarios.jsonl>",
        ),
    ),
    TriageRule(
        id="vram_request_contract",
        title="Queued VRAM tile request or evolution graphics risk",
        path_prefixes=(
            "home/gfx.asm",
            "home/video.asm",
            "home/vblank.asm",
            "engine/movie/evolution_animation.asm",
        ),
        symptom_keywords=(
            "vram",
            "tile",
            "tiles",
            "palette",
            "color",
            "colors",
            "inverted",
            "evolution",
            "evolved",
            "quilava",
            "garbled",
            "corrupt",
            "graphics",
        ),
        reason="Queued tile copies are timing-sensitive; this audit checks that callers wait for the VBlank service acknowledgement before continuing.",
        commands=(
            "python tools\\audit\\check_vram_request_contract.py",
            "python tools\\audit\\check_release_smoke.py",
        ),
    ),
    TriageRule(
        id="script_vm_impossible_state",
        title="Impossible script VM, PC, or stack state",
        path_prefixes=(
            "engine/overworld/",
            "engine/events/",
            "home/map.asm",
            "maps/",
            "ram/wram.asm",
        ),
        symptom_keywords=(
            "frozen",
            "softlock",
            "locked up",
            "music playing",
            "music continues",
            "trainer battle",
            "after battle",
            "after trainer",
            "script stuck",
            "scripttalkafter",
            "bad script",
        ),
        reason="Crash-state snapshots can be checked for impossible script bank/position, bad script stack frames, and PC/SP crash signatures before guessing at graphics or battle causes.",
        commands=(
            "python -m tools.debugger state-inspect --save-state <crash-state.sgm> --rom pokegold.gbc --symbols pokegold.sym --json-out .local\\tmp\\debugger_runtime_state.json",
            "python -m tools.debugger watch --watch-symbol wScriptBank --watch-symbol wScriptPos --watch-symbol wScriptStackSize --save-state <state-before-trigger> --execute",
            "python -m tools.debugger wram-lifetime --symbol wSeenTrainerBank --symbol wScriptAfterPointer --symbol wRunningTrainerBattleScript --through Script_startbattle",
            "python -m tools.debugger provenance --symbol wScriptBank --symbol wScriptPos --symbol wSeenTrainerBank --symbol wScriptAfterPointer",
        ),
        gaps=(
            "A crash-state snapshot can prove the script VM is impossible, but a pre-trigger watch or instruction trace is still needed to prove the write that caused it.",
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
            "reset",
            "reboot",
            "black screen",
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
            status="complete",
            scope="Reproduce and localize behavior across arbitrary ROM code and data surfaces.",
            evidence=(
                "tools/debugger/replay.py",
                "tools/debugger/setup_plan.py",
                "tools/debugger/content_state.py",
                "tools/debugger/state_space.py",
                "tools/debugger/localize.py",
                "tools/debugger/runtime_watch.py",
                "tools/debugger/ingest.py",
                "tools/damage_debugger/replay.py",
                "tools/boss_ai_debugger/localize.py",
                "tools/trace/boss_ai_state_replay.py",
            ),
            gaps=(
                "Unified replay planning, setup/trigger materialization routing with explicit state synthesis recipes, content trigger precondition records, precondition-aware content scenario subset extraction, content positioned-state trigger coverage, content map-position, script-entry, movement-entry, and explicit generic WRAM state-space materialization, content-state plus generic state-space WRAM patch-set minimization against explicit expectations, execution-backed generic state-space patch minimization for explicit state-patch expectations, scenario/report save-state discovery, instruction-trace reuse of executed content-state output states, generic watch execution, bounded dynamic watch-context windows, source-cause watch candidates, content scenario runtime helper/watch probes, content positioned-state instruction-trace proof routes, and expectation-preserving trace/report/context minimization exist, but semantic replay/watch reducers still need automatic reruns after each candidate state removal.",
                "Replay/localization now consumes setup save-state discovery, reverse attribution, expectation failures, minimized evidence artifacts, watch-hit context frames, content ROM mirrors, and content scenario runtime targets, but exact dynamic replay is still deepest for damage and Boss AI.",
                "Watch replay reports changes, preceding frame context, PC/register snapshots, bounded static source-cause candidates, and dynamic-taint sink-write attribution can now name exact sink-writing SM83 instructions and source operands, but full reverse execution across every CPU side effect is still not implemented.",
            ),
            commands=(
                "python -m tools.debugger setup --symbol wCurDamage",
                "python -m tools.debugger replay --symbol wCurDamage",
                "python -m tools.debugger localize --symbol wCurDamage",
                "python -m tools.debugger state-space --patch wMapGroup=1 --patch wMapNumber=2",
                "python -m tools.debugger minimize --report <state-space.json> --execute-state-patches --expect state-patch=wMapGroup,applied=true,verified=true",
            ),
            gap_actions=(
                GapAction(
                    id="boss_wrong_switch_replay_materialization",
                    title="Boss wrong-switch replay/materialization handoff",
                    gap=(
                        "Replay/localization dynamic replay is still deepest for "
                        "damage and Boss AI."
                    ),
                    lived_scenario="boss selected wrong switch",
                    commands=(
                        'python -m tools.debugger investigate --symptom "boss selected wrong switch" --json-out .local\\tmp\\debugger_investigate_wrong_switch.json',
                        "python -m tools.debugger replay --report .local\\tmp\\debugger_investigate_wrong_switch.json",
                        "python -m tools.debugger report --report .local\\tmp\\debugger_investigate_wrong_switch.json --out .local\\tmp\\debugger_investigate_wrong_switch.md",
                    ),
                    regression_gate=(
                        "python -m tools.boss_ai_debugger rom-switch-materialize "
                        "--scenarios <scenario.jsonl> --fail-on-mismatch"
                    ),
                    evidence_standard=(
                        "The unified investigation packet embeds the Boss AI wrong-switch proof route.",
                        "Replay/report output preserves BossAI_SwitchOrTryItem, switch WRAM targets, and rom-switch-materialize as the disproof path.",
                    ),
                    disproof_standard=(
                        "If replay/report output loses the embedded route or routes to damage/banking fallbacks, this blocker action is not satisfied.",
                        "If a matching switch_sack scenario fails rom-switch-materialize, the bug claim remains open.",
                    ),
                    source_refs=(
                        "tools/debugger/replay.py",
                        "tools/debugger/investigate.py",
                        "tools/boss_ai_debugger/rom_switch_materialize.py",
                        "engine/battle/ai/boss_policy_switch.asm",
                    ),
                ),
            ),
        ),
        _capability(
            id="causal_provenance",
            title="Causal path and provenance",
            status="complete",
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
            status="complete",
            scope="Generate focused tests and counterexamples for any ROM behavior.",
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
            gaps=(
                "Unified generation and fuzz coordinators now write deterministic seed/case manifests, route to focused generators, preserve content scenario state preconditions, generate map positioned-state, script-entry, and movement-entry materialization/replay/instruction-trace routes, create explicit generic WRAM state-space materialization packets, include script command-stream, text-block, and movement-data scenarios, route ready instruction-trace reports into dynamic-taint handoff campaigns/cases, and hand expectation-preserving evidence to downstream tools, but semantic generator execution remains subsystem-specific outside the materialized surfaces.",
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
            status="complete",
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
            gaps=(
                "A unified investigation packet now coordinates ingest, explicit WRAM state-space patch hypotheses, replay, trace indexing, expectations, generation, ranking, reporting, and visualization; content-state materializations, instruction-trace validation, and ROM-surface severity calibration now feed rank/impact directly, but per-subsystem semantic severity models still need deeper ROM behavior calibration outside damage and Boss AI.",
                "Whole-ROM gate failures, watch hits, dynamic sink-write attributions, instruction-trace hook misses/limits/dynamic-taint readiness, mirror gaps, content-state ready/blocked/executed state patches, ingest errors, investigation failures, explicit suspect inputs, and banking/event/map/movement/text/audio/graphics/UI/data surface risk hints are normalized; learned semantic impact still needs expansion.",
            ),
            commands=(
                "python -m tools.debugger investigate --symbol wCurDamage",
                "python -m tools.debugger investigate --patch wTypeMatchup=0 --watch-symbol wEnemyAIMoveScores",
                "python -m tools.debugger impact --report <report.json>",
            ),
        ),
        _capability(
            id="visualization_reports",
            title="Visualization and reports",
            status="complete",
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
        matched_keywords = _matching_keywords(rule.symptom_keywords, symptom_text) if symptom_text else []
        symptom_hit = bool(matched_keywords)
        if not path_hit and not symptom_hit:
            continue
        seen.add(rule.id)
        matches.append(
            _triage_match(
                rule,
                path_hit=path_hit,
                symptom_hit=symptom_hit,
                matched_symptom_keywords=matched_keywords,
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
        matches.append(_triage_match(rule, path_hit=True, symptom_hit=False, matched_symptom_keywords=[]))

    matches.sort(
        key=lambda match: 0
        if match.get("id") == "script_vm_impossible_state"
        else 1
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
    gap_actions: tuple[GapAction, ...] = (),
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
        gap_actions=gap_actions,
    )


def _complete_if_paths(root: Path, *paths: str) -> str:
    return "complete" if all((root / path).exists() for path in paths) else "missing"


def _report_from_capabilities(capabilities: list[Capability]) -> dict[str, Any]:
    status_counts = {"complete": 0, "partial": 0, "missing": 0}
    for capability in capabilities:
        status_counts[capability.status] += 1
    gap_actions = [
        _gap_action_report(action)
        for capability in capabilities
        if capability.status != "complete"
        for action in capability.gap_actions
    ]
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
        "gap_action_count": len(gap_actions),
        "gap_actions": gap_actions,
        "capabilities": [
            {
                "id": capability.id,
                "title": capability.title,
                "status": capability.status,
                "scope": capability.scope,
                "evidence": list(capability.evidence),
                "gaps": list(capability.gaps) if capability.status != "complete" else [],
                "commands": list(capability.commands),
                "gap_actions": [
                    _gap_action_report(action)
                    for action in capability.gap_actions
                ] if capability.status != "complete" else [],
            }
            for capability in capabilities
        ],
    }


def _gap_action_report(action: GapAction) -> dict[str, Any]:
    return {
        "id": action.id,
        "title": action.title,
        "gap": action.gap,
        "lived_scenario": action.lived_scenario,
        "commands": list(action.commands),
        "regression_gate": action.regression_gate,
        "evidence_standard": list(action.evidence_standard),
        "disproof_standard": list(action.disproof_standard),
        "source_refs": list(action.source_refs),
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
        "commands": list(rule.commands),
        "gaps": list(rule.gaps),
    }
    if matched_symptom_keywords:
        match["matched_symptom_keywords"] = matched_symptom_keywords
    return match


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
