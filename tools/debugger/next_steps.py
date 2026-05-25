from __future__ import annotations

from pathlib import Path
from typing import Any

from .catalog import ROOT, keyword_matches, triage_request


NEXT_STEP_ROWS = [
    {
        "symptom_class": "script_vm_impossible_state",
        "matched_lane": "runtime_state",
        "title": "Frozen overworld or impossible script VM state",
        "keywords": [
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
            "evolved flaffy",
        ],
        "first_command": "python -m tools.debugger state-inspect --save-state <crash-state.sgm> --rom pokegold.gbc --symbols pokegold.sym --json-out .local\\tmp\\debugger_runtime_state.json",
        "required_inputs": ["crash-state save-state, preferably from the frozen screen"],
        "proof_limit": "Snapshot invariant proof: detects impossible script/PC/stack state in the supplied state; it does not prove which prior write caused it without a pre-trigger watch or instruction trace.",
        "escalation_command": "python -m tools.debugger repro-recipe --id trainer-battle-evolution-resume",
        "repro_recipes": ["trainer-battle-evolution-resume"],
    },
    {
        "symptom_class": "vram_request_contract",
        "matched_lane": "graphics_vram",
        "title": "Evolution, palette, tile, or VRAM graphics corruption",
        "keywords": [
            "vram",
            "evolution reset",
            "quilava",
            "inverted colors",
            "colors inverted",
            "palette",
            "garbled graphics",
            "tile corruption",
        ],
        "first_command": "python tools\\audit\\check_vram_request_contract.py",
        "required_inputs": ["none; audit reads the committed VRAM request and VBlank service routines"],
        "proof_limit": "Static contract proof: verifies queued tile requests wait for VBlank acknowledgement; it does not prove a supplied save-state no longer resets.",
        "escalation_command": "python -m tools.debugger watch --reset-sentinel --rom pokegold.gbc --symbols pokegold.sym --save-state <state-before-trigger> --watch-symbol wRequested2bppSize --watch-symbol wRequested1bppSize --frames 2200 --context-frames 20 --json-out .local\\tmp\\debugger_vram_reset_watch.json",
    },
    {
        "symptom_class": "crash_reset",
        "matched_lane": "runtime_crash",
        "title": "Crash, reset, intro jump, or black screen",
        "keywords": [
            "crash",
            "reset",
            "reboot",
            "black screen",
            "intro",
            "title screen",
            "hang",
            "locked up",
            "first wild",
            "wild encounter reset",
        ],
        "first_command": "python -m tools.debugger watch --reset-sentinel --rom pokegold.gbc --symbols pokegold.sym --save-state <state-before-trigger> --frames 1200 --context-frames 20 --json-out .local\\tmp\\debugger_reset_watch.json",
        "required_inputs": ["save-state before the trigger, or a reproducible input route that can create one"],
        "proof_limit": "Runtime sentinel proof: catches jumps through reset/start vectors in the supplied replay window and preserves recent PC/register/WRAM context; it does not synthesize the save by itself.",
        "escalation_command": "python -m tools.debugger repro-recipe --id first-wild-route29",
        "repro_recipes": ["first-wild-route29"],
    },
    {
        "symptom_class": "overworld_poison_cure",
        "matched_lane": "overworld_status",
        "title": "Walking poison cure or 1 HP overworld poison behavior",
        "keywords": ["walking poison", "overworld poison", "poison cure", "1 hp", "0 hp", "poisoned mon"],
        "first_command": "python tools\\audit\\check_overworld_poison_cure.py",
        "required_inputs": ["none; audit builds/runs the committed poison-step repro"],
        "proof_limit": "Runtime audit proof for the poison-step fixture; it does not prove unrelated status or battle poison behavior.",
        "escalation_command": "python -m tools.debugger investigate --changed-file engine/events/poisonstep.asm",
    },
    {
        "symptom_class": "base_ai_move_legality",
        "matched_lane": "base_ai_mechanics",
        "title": "Base non-boss AI picked a held-item-illegal move",
        "keywords": ["assault vest", "choice locked", "choice lock", "regular trainer", "non-boss", "base ai", "illegal status"],
        "first_command": "python tools\\audit\\check_base_ai_mechanics_correctness.py",
        "required_inputs": ["none; audit reads the shared base AI move scoring path"],
        "proof_limit": "Static contract proof for base AI legality gates; it does not prove a specific trainer battle without an emulator scenario.",
        "escalation_command": "python -m tools.debugger investigate --changed-file engine/battle/ai/move.asm",
    },
    {
        "symptom_class": "boss_ai_sleep_clause_move_legality",
        "matched_lane": "boss_ai",
        "title": "Boss AI selected sleep while Sleep Clause was active",
        "keywords": ["sleep clause", "hypnosis", "sleep active", "already asleep", "sleep already active"],
        "first_command": "python -m tools.boss_ai_debugger damage-ai-report --trainer <TRAINER> --enemy <ENEMY> --player-save <save.sav> --player-slot <slot> --sleep-clause both",
        "required_inputs": ["trainer id, enemy mon selector, player save, and active party slot"],
        "proof_limit": "Exact damage plus move-score report for the supplied state; use trace mode or ROM materialization before claiming the live fight is fully reproduced.",
        "escalation_command": "python -m tools.boss_ai_debugger move-score-probe --trainer <TRAINER> --enemy <ENEMY> --player-save <save.sav> --player-slot <slot> --sleep-clause both --trace",
    },
    {
        "symptom_class": "boss_ai_type_immunity_move_choice",
        "matched_lane": "boss_ai",
        "title": "Boss AI selected a move blocked by type immunity",
        "keywords": ["doesn't affect", "doesnt affect", "normal move", "normal-type", "ghost", "type immunity"],
        "first_command": "python -m tools.boss_ai_debugger damage-ai-report --trainer <TRAINER> --enemy <ENEMY> --player-save <save.sav> --player-slot <slot> --sleep-clause both",
        "required_inputs": ["trainer id, enemy mon selector, player save, and active party slot"],
        "proof_limit": "Exact damage plus selector-score report for the supplied state; it does not prove an arbitrary screenshot unless the save matches that battle.",
        "escalation_command": "python -m tools.boss_ai_debugger move-score-probe --trainer <TRAINER> --enemy <ENEMY> --player-save <save.sav> --player-slot <slot> --trace",
    },
    {
        "symptom_class": "boss_ai_hidden_power_type",
        "matched_lane": "boss_ai",
        "title": "Boss AI Hidden Power type or immunity handling",
        "keywords": ["hidden power", "hiddenpower", "dv-derived", "dv derived", "normal immunity", "stale normal"],
        "first_command": "python -m tools.boss_ai_debugger move-score-probe --trainer <TRAINER> --enemy <ENEMY> --player-save <save.sav> --player-slot <slot> --trace",
        "required_inputs": ["trainer id, enemy mon selector, player save, and active party slot"],
        "proof_limit": "Move-score probe can expose score changes and callsites, but Hidden Power's live type still needs ROM trace/materialization proof.",
        "escalation_command": "python -m tools.debugger investigate --symbol BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem --symbol HiddenPowerDamage",
    },
    {
        "symptom_class": "early_boss_debuff_spam",
        "matched_lane": "boss_ai",
        "title": "Early boss repeated debuffs instead of attacking",
        "keywords": ["leer", "growl", "tail whip", "stat drop", "debuff", "spam", "never attacked"],
        "first_command": "python -m tools.boss_ai_debugger damage-ai-report --trainer <TRAINER> --enemy <ENEMY> --player-save <save.sav> --player-slot <slot> --sleep-clause both",
        "required_inputs": ["trainer id, enemy mon selector, player save, and active party slot"],
        "proof_limit": "Single-turn score proof; multi-turn spam still needs repeated state probes or a generated scenario sequence.",
        "escalation_command": "python -m tools.boss_ai_debugger generate --family all --count 100 --seed 1 --out .local\\tmp\\early_boss_debuff_scenarios.jsonl",
    },
    {
        "symptom_class": "learnset_semantics",
        "matched_lane": "pokemon_semantics",
        "title": "Species learnset or save-party move question",
        "keywords": ["learnset", "learns", "level 14", "confusion", "spite", "move set", "moveset"],
        "first_command": "python -m tools.debugger learnset-inspect --species <SPECIES> --level <LEVEL>",
        "required_inputs": ["species and level; add party-inspect when checking a specific save"],
        "proof_limit": "Source learnset projection only; existing saves need party-inspect and any edit needs a separate save patcher.",
        "escalation_command": "python -m tools.debugger party-inspect --save <save.sav> --slot <slot>",
    },
    {
        "symptom_class": "grass_regrowth_balance",
        "matched_lane": "pokemon_semantics",
        "title": "Grass passive regrowth rate or cutoff question",
        "keywords": ["grass heal", "grass healing", "grass regrowth", "hoppip", "passive heal", "heal cutoff"],
        "first_command": "python -m tools.debugger grass-regrowth --max-total-hp 300",
        "required_inputs": ["none unless a different max HP cap is wanted"],
        "proof_limit": "Formula/cutoff mirror for current source; it does not prove a battle state is eligible to heal.",
        "escalation_command": "python -m tools.debugger content-mirror --source-file engine/battle/type_passive_damage_mods.asm",
    },
    {
        "symptom_class": "base_data_mutation_hazard",
        "matched_lane": "static_audits",
        "title": "Base-data or wCurSpecies mutation hazard",
        "keywords": ["wcurSpecies", "wcur species", "base data", "getbasedata", "candidate species"],
        "first_command": "python tools\\audit\\bug_hunt_triage.py --max-leads 12",
        "required_inputs": ["none; triage scans current source for prior bug-family hazards"],
        "proof_limit": "Static lead finder; each lead still needs source proof or a targeted runtime trace before patching.",
        "escalation_command": "python -m tools.debugger provenance --symbol wCurSpecies --symbol GetBaseData",
    },
    {
        "symptom_class": "move_search_unbounded",
        "matched_lane": "static_audits",
        "title": "Move-search corruption from copied or missing last move",
        "keywords": ["mirror move", "sketch", "mimic", "disable", "encore", "spite", "last move"],
        "first_command": "python tools\\audit\\bug_hunt_triage.py --max-leads 12",
        "required_inputs": ["none; triage scans current source for prior bug-family hazards"],
        "proof_limit": "Static lead finder; it does not execute a battle repro for Mirror Move, Mimic, Disable, Encore, or Spite.",
        "escalation_command": "python -m tools.debugger investigate --changed-file engine/battle/move_effects/sketch.asm --changed-file engine/battle/effect_commands.asm",
    },
    {
        "symptom_class": "pgoal_audit_internals",
        "matched_lane": "static_audits",
        "title": "Pgoal, proof-artifact, and release-smoke audit wiring",
        "keywords": ["pgoal", "gap_actions", "gap actions", "proof artifact", "durable proof", ".local/tmp", "audit count", "release-smoke audit", "release smoke audit", "new release-smoke", "new release smoke"],
        "first_command": "python -m tools.debugger audit --json-out .local\\tmp\\q_audit.json",
        "required_inputs": ["the audit or release-gate question being answered"],
        "proof_limit": "Static/audit-surface proof: explains what current gates inspect and which artifacts are durable; it does not decrement gap_actions unless the audit code itself consumes that evidence.",
        "escalation_command": "python tools\\audit\\check_release_smoke.py",
    },
    {
        "symptom_class": "asm_gotcha_reference",
        "matched_lane": "static_audits",
        "title": "ASM bank/call/stat-stage gotcha reference",
        "keywords": ["farcall", "clobber", "cross-bank", "cross bank", "call someLabel", "call somelabel", "silent garbage", "stat stage", "wEnemySpdLevel", "base_stat_level", "multiplier"],
        "first_command": "python tools\\audit\\check_farcall_hl_clobber.py",
        "required_inputs": ["the suspicious ASM call/stat-stage source path when available"],
        "proof_limit": "Static contract proof: explains known RGBDS/farcall/stat encoding traps and points to focused audits; it does not prove a live crash without a repro trace.",
        "escalation_command": "python tools\\audit\\check_cross_bank_call.py",
    },
    {
        "symptom_class": "repo_navigation",
        "matched_lane": "static_audits",
        "title": "Repo navigation for feature/data edit surfaces",
        "keywords": ["hm replacement", "field tools", "sky_pass", "lantern", "farfetch", "stick", "yanma", "ariados", "showcase", "free space", "rom bank", "tight banks"],
        "first_command": "python tools\\audit\\check_release_smoke.py",
        "required_inputs": ["feature/data area or Pokemon/species being located"],
        "proof_limit": "Source/navigation proof: points to the owned source/data docs and audits; edits still need the domain-specific smoke/regenerator after changes.",
        "escalation_command": "python scripts\\generate_balance_audit.py",
    },
    {
        "symptom_class": "save_format_change",
        "matched_lane": "static_audits",
        "title": "Save format version and migration impact",
        "keywords": ["save format", "save_format_version", "existing saves", "migration", "old saves", "save layout"],
        "first_command": "python tools\\audit\\check_save_format_version.py",
        "required_inputs": ["none unless inspecting a proposed save-layout diff"],
        "proof_limit": "Static layout/fingerprint proof: verifies the current save layout against SAVE_FORMAT_VERSION; it does not migrate existing saves.",
        "escalation_command": "python tools\\audit\\check_save_format_version.py --update",
    },
    {
        "symptom_class": "trace_rom_divergence",
        "matched_lane": "trace_runtime",
        "title": "Trace ROM versus release ROM identity",
        "keywords": ["trace rom", "pokegold_trace", "release rom", "roms.sha1", "sha1-pinned", "sha1 pinned", "distribute"],
        "first_command": "python tools\\verify_sha1.py pokegold.gbc",
        "required_inputs": ["none; release ROM identity is pinned by roms.sha1"],
        "proof_limit": "Release identity proof: distinguishes trace-instrumented ROMs from the SHA1-pinned release ROM; it does not validate a changed trace manifest.",
        "escalation_command": "python tools\\trace\\boss_ai_trace_batch.py --execute",
    },
    {
        "symptom_class": "content_mirror_state",
        "matched_lane": "runtime_state",
        "title": "Content mirror and script-entry state materialization",
        "keywords": ["content-mirror", "content mirror", "map script", "event macro", "built rom bytes", "script-entry", "script entry", "movement-entry", "movement entry", "state space", "materialize"],
        "first_command": "python -m tools.debugger content-mirror --source-file maps\\NewBarkTown.asm",
        "required_inputs": ["source file or content-scenario report for the map/script/movement surface"],
        "proof_limit": "Source-to-ROM mirror or planned state materialization proof; runtime execution requires content-state with a base save-state and --execute.",
        "escalation_command": "python -m tools.debugger content-state --report <content-scenarios.json> --scenario-id <id> --base-save-state <base.state> --out-state .local\\tmp\\patched.state --execute",
    },
    {
        "symptom_class": "qol_gate_design",
        "matched_lane": "static_audits",
        "title": "QoL release gates, Repel renewal, and manual feel checks",
        "keywords": ["repel", "bug-catching contest", "bug catching contest", "wrong item", "qol", "release gate", "map script", "player-communication", "communication text", "manual feel"],
        "first_command": "python tools\\audit\\check_release_smoke.py",
        "required_inputs": ["none for committed smoke checks; emulator route when the change affects feel or UI rendering"],
        "proof_limit": "Static release-smoke proof plus manual-proof routing; it does not prove an unexercised emulator flow.",
        "escalation_command": "python tools\\audit\\check_navigation_floor.py",
    },
    {
        "symptom_class": "damage_math_hazard",
        "matched_lane": "damage",
        "title": "Damage-chain math, ABI, or type-passive refactor hazard",
        "keywords": ["5x damage", "5x", "physical damage", "damage-stat", "damage stat", "type passive", "register preservation", "wCurDamage"],
        "first_command": "python -m tools.damage_debugger.clobber_smoke",
        "required_inputs": ["changed damage-chain file or scenario when available"],
        "proof_limit": "Damage oracle/smoke proof for current source; live battle claims need a matching save or generated scenario.",
        "escalation_command": "python tools\\audit\\check_battle_math_safety.py",
    },
    {
        "symptom_class": "damage_matchup_cli",
        "matched_lane": "damage",
        "title": "Damage and matchup query CLI",
        "keywords": ["damage matchup", "matchup behavior", "exact damage", "instead of guessing", "damage debugger matchup"],
        "first_command": "python -m tools.damage_debugger.matchup CHARIZARD:50 LAPRAS:50 FLAMETHROWER --json",
        "required_inputs": ["attacker species/level, defender species/level, and move"],
        "proof_limit": "Current source-backed matchup output; full battle damage still needs the damage oracle or ROM-backed scenario.",
        "escalation_command": "python -m tools.damage_debugger.clobber_smoke",
    },
    {
        "symptom_class": "headless_battle_simulation",
        "matched_lane": "headless_battle",
        "title": "Headless text/JSON battle simulation",
        "keywords": [
            "headless battle",
            "battle simulator",
            "simulate a battle",
            "text-only battle",
            "text only battle",
            "turn-by-turn battle",
            "battle turn by turn",
            "walk a battle",
            "no gui",
            "fixed rng",
            "exhaustive rng",
            "battle with switches",
            "replacement after ko",
            "potion",
            "full restore",
            "item action",
            "stat stage",
            "speed stage",
            "dragon dance",
            "calm mind",
            "quiver dance",
            "recover",
            "softboiled",
            "milk drink",
            "self heal",
            "poisonpowder",
            "poison gas",
            "toxic",
            "poison status",
            "thunder wave",
            "stun spore",
            "glare",
            "paralysis",
            "paralyze",
            "secondary status",
            "burn hit",
            "poison hit",
            "paralyze hit",
            "ember burn",
            "body slam paralysis",
            "giga drain",
            "mega drain",
            "absorb",
            "leech life",
            "drain move",
            "sleep powder",
            "spore",
            "hypnosis",
            "sing",
            "sleep status",
            "fast asleep",
            "rest",
            "status berry",
            "miracleberry",
            "mint berry",
            "psncureberry",
            "przcureberry",
            "ice berry",
            "safeguard",
            "substitute",
        ],
        "first_command": "python -m tools.headless_battle --template",
        "required_inputs": ["scenario JSON with active mons, optional bench[], selected actions/turns[] or repeat max_turns, and fixed/sample/exhaustive RNG for supported branch points"],
        "proof_limit": "Current headless slice: selected move-vs-move turns, selected BP=0 single-stat stage moves, selected Dragon Dance/Calm Mind/Quiver Dance setup moves, selected Recover/Softboiled/Milk Drink self-heal moves, selected PoisonPowder/Poison Gas/Toxic poison-status moves, selected Thunder Wave/Stun Spore/Glare paralysis-status moves with paralyzed speed/full-paralysis checks including Fighting/Electric type-passive paralysis modifiers, selected EFFECT_BURN_HIT/EFFECT_POISON_HIT/EFFECT_PARALYZE_HIT damaging status secondaries, selected Absorb/Mega Drain/Leech Life/Giga Drain drain moves, selected EFFECT_SLEEP moves plus Rest and sleep action denial/wake handling, selected held PSNCUREBERRY/PRZCUREBERRY/ICE_BERRY/MINT_BERRY/MIRACLEBERRY status cures after supported status applications, selected caller-supplied Safeguard/Substitute status blockers, selected Substitute move creation and Substitute HP routing for selected damaging hits, repeat/max_turns action maps, auto_replace_or KO/send-out loops, wild_random_move, selected switch actions, caller-supplied replace actions after KO, explicit enemy auto_replace choice using the basic source type chart, scenario-supplied or rom-switch-materialize-bridged Boss AI switch-roll branching with exact probabilities only (plus a non-branching report_only mode that summarizes ranged materialized switch probabilities without executing a branch, a fixture-match-or-reject headless-to-switch_sack scenario exporter for the canonical Starmie/Qwilfish/Gengar materialization fixture, and an accept_overrides=True mode that emits species/types/HP overrides for arbitrary boards consumed by the parameterized switch_materialization_patches, and a Phase-1 headless batch switch-materialize runner tools/headless_battle/batch_switch.py that wraps run_rom_switch_materialization_from_path with a per-scenario table plus an N-scenarios/M-observed-switches/K-probability-exact/errors summary so downstream batch validation flows can consume the materializer in one PyBoy session, and a Phase-2 expectations comparator tools/headless_battle/switch_expectations.py that loads a JSON schema of {scenario_id, expected.action, optional switch_probability_max/min, rationale} and emits per-scenario pass/fail/error/no_expectation verdicts plus a focused violation report carrying the rationale, the expected vs observed action, and the bound-formatted reason), explicit active Potion/Super Potion/Hyper Potion/Max Potion/Full Restore actions, explicit attack/defense/speed/sp_attack/sp_defense stat-stage state, PP decrement, supported Rocky Helmet/Shell Bell/Life Orb after-hit HP effects, modified-speed turn order, non-link equal-speed tie RNG, basic critical-hit checks, basic move accuracy hit/miss, damage variation with fixed/sample/exhaustive RNG, selected damaging status secondary chance RNG, selected sleep duration RNG, initial poison/burn/toxic residual after selected moves and supported item actions, multi-turn turns[] progression with HP/RNG carryover, pre-variation damage delegated to the existing ROM-backed damage oracle, one fixed-RNG NormalHit ROM differential, one EffectChance-plus-target-status-command ROM component differential for selected burn/poison/paralysis secondaries, one DrainTarget ROM component differential for selected drain healing, one GetHealingItemAmount-plus-RestoreHealth ROM component differential for selected active HP items, one HealStatus ROM component differential proving Full Restore clears wBattleMonStatus plus the TOXIC / NIGHTMARE / CONFUSED sub-status bits, and post-score Boss AI selector replay/execution from known score bytes. Strategic full-battle action choice, automatic trainer item usage, player trainer-battle Pack availability, inventory accounting, implicit replacement without auto_replace_or or auto_replace, Pursuit/Spikes/switch-in effects, accuracy/evasion stage moves/modifiers, damaging secondary stat effects outside selected burn/poison/paralysis status secondaries, multi-stat chains outside Dragon Dance/Calm Mind/Quiver Dance, Baton Pass/Psych Up, Substitute/Mist blockers outside selected status blockers, badge boosts, passive stat/speed/accuracy bonuses outside the listed paralysis path, status application outside selected poison/paralysis/sleep-status moves and selected damaging status secondaries, sleep mechanics outside selected sleep moves/Rest/action denial, freeze, burn application outside selected damaging burn secondaries, Safeguard duration/expiration, Substitute Baton Pass/multi-hit continuation details, held status prevent items, freeze/confusion held cures, Sleep Clause clearing from held sleep cures, non-paralyzed Electric speed passives, weather/time healing, drain effects outside selected EFFECT_LEECH_HIT moves, Heal Bell, RNG-consuming mechanics outside the listed supported branch points, live Boss AI scoring, Boss AI switch candidate/confidence generation, AI_TryItem, and scripts remain out of scope until separately implemented and proven.",
        "escalation_command": "python tools\\audit\\check_headless_battle_simulator.py",
    },
    {
        "symptom_class": "type_chart_navigation",
        "matched_lane": "pokemon_semantics",
        "title": "Type matchup table and runtime reader",
        "keywords": ["type matchup", "type matchups", "type chart", "dragon vs water", "specific matchup"],
        "first_command": "python -c \"import os; assert os.path.exists('data/types/type_matchups.asm'), 'type_matchups.asm missing'; print('ok')\"",
        "required_inputs": ["type matchup being inspected or edited"],
        "proof_limit": "Source locator proof for the matchup table and runtime reader; changed type semantics still need release smoke and mechanics-doc regeneration.",
        "escalation_command": "python tools\\audit\\check_release_smoke.py",
    },
    {
        "symptom_class": "add_new_move_navigation",
        "matched_lane": "static_audits",
        "title": "Add a brand-new move end to end",
        "keywords": ["add a new move", "brand-new move", "new move end-to-end", "move-name string", "move name string", "effect pointer", "animation slot"],
        "first_command": "python -m tools.debugger next --symptom \"where do I add a new move end-to-end\" --json-out .local\\tmp\\q_add_move.json",
        "required_inputs": ["move design and effect/animation/scoring intent"],
        "proof_limit": "Source locator proof: names the required tables and engine surfaces; it does not validate a new move until release smoke/build gates run.",
        "escalation_command": "python tools\\audit\\check_release_smoke.py",
    },
    {
        "symptom_class": "boss_ai_navigation",
        "matched_lane": "boss_ai",
        "title": "Boss AI public-info, gating, and WRAM navigation",
        "keywords": ["current-turn", "current turn", "hidden party", "public-info", "public information", "no cheat", "boss ai wram", "wramx reserve", "byte budget", "boss ai reserve"],
        "first_command": "python tools\\audit\\check_boss_ai_no_cheat.py",
        "required_inputs": ["none for public-info gates; dev_index when answering current byte-budget questions"],
        "proof_limit": "Static invariant proof for public-info and WRAM budget surfaces; live decision claims still need save-backed Boss AI probes.",
        "escalation_command": "python scripts\\generate_dev_index.py --rom pokegold",
    },
    {
        "symptom_class": "wram_bank_ret_crash",
        "matched_lane": "runtime_crash",
        "title": "WRAM bank switching with stack/call/ret hazards",
        "keywords": ["wram bank", "wramx stack", "setwrambank", "svbk", "return address", "ret crash", "bank ret"],
        "first_command": "python tools\\audit\\check_observation_log_invariants.py",
        "required_inputs": ["source file or trace that switches WRAM banks near a call/ret"],
        "proof_limit": "Static hazard proof for known WRAMX bank-switch call/ret patterns; exact crash proof needs a trace or replay around the bank switch.",
        "escalation_command": "python -m tools.debugger wram-bank-hazards --source-file engine\\battle\\ai\\observation_log.asm",
    },
    {
        "symptom_class": "haki_taunt_read",
        "matched_lane": "boss_ai",
        "title": "Haki taunt or oracle-read behavior",
        "keywords": ["haki", "taunt", "oracle", "red says", "eyes narrow", "read my move"],
        "first_command": "python tools\\audit\\check_haki_oracle_uniform.py",
        "required_inputs": ["none; audit reads committed Haki source tables"],
        "proof_limit": "Static contract proof: verifies uniform oracle shape, taunt coverage, exclusion list, and flush sequencing; it does not prove an emulator-live textbox render.",
        "escalation_command": "python -m tools.boss_ai_debugger haki-coverage --json",
    },
    {
        "symptom_class": "ko_band_pressure",
        "matched_lane": "boss_ai",
        "title": "KO-band pressure or deny-KO decision",
        "keywords": ["ko-band", "ko band", "ko pressure", "deny ko", "damage band", "matchup table"],
        "first_command": "python tools\\audit\\check_ko_band_oracle_self_test.py",
        "required_inputs": ["none; audit uses committed matchup-table scenarios"],
        "proof_limit": "Static plus materialized-control proof for known scenarios; use a scenario file before claiming an arbitrary live battle decision.",
        "escalation_command": "python tools\\audit\\check_ko_band_oracle_materialized.py",
    },
    {
        "symptom_class": "revealed_effect_response",
        "matched_lane": "boss_ai",
        "title": "Revealed-effect matrix response",
        "keywords": ["revealed effect", "protect", "encore", "destiny bond", "counter", "mirror coat", "disable", "perish", "phaze", "roar"],
        "first_command": "python tools\\audit\\check_revealed_effect_matrix_coverage.py",
        "required_inputs": ["none; audit reads committed matrix dispatch and coverage rows"],
        "proof_limit": "Static matrix coverage proof: confirms dispatch and key effects; does not prove every battle-state branch without a scenario.",
        "escalation_command": "python -m tools.debugger investigate --symbol BossAI_ApplyRevealedEffectMatrixBias",
    },
    {
        "symptom_class": "observation_tendency_behavior",
        "matched_lane": "boss_ai",
        "title": "Observation log, tendency, or calibration behavior",
        "keywords": ["observation", "tendency", "calibration", "learned", "memory", "recent turns", "wramx"],
        "first_command": "python tools\\audit\\check_observation_log_invariants.py",
        "required_inputs": ["none; audit uses committed golden tendency/calibration cases"],
        "proof_limit": "Golden invariant proof for the observation substrate; it does not reconstruct a fresh player save or arbitrary six-turn fight.",
        "escalation_command": "python -m tools.debugger investigate --symbol BossAI_ObservationLogAppend",
    },
    {
        "symptom_class": "role_package",
        "matched_lane": "boss_ai",
        "title": "Role/package classifier behavior",
        "keywords": ["role package", "role-package", "classifier", "spinner", "phazer", "wallbreaker", "setup sweeper", "recovery wall"],
        "first_command": "python -m tools.boss_ai_debugger role-packages --species <SPECIES> --json",
        "required_inputs": ["species name or species list to classify"],
        "proof_limit": "Debugger-table proof for public package bits; does not prove a switch-confidence threshold unless paired with a scenario/control case.",
        "escalation_command": "python tools\\audit\\check_role_package_classifier.py",
    },
    {
        "symptom_class": "coach_template",
        "matched_lane": "boss_ai",
        "title": "Coach-plan template behavior",
        "keywords": ["coach", "template", "plan template", "lance", "koga", "dragon dance", "curse rest", "outrage"],
        "first_command": "python -m tools.boss_ai_debugger coach-plan-templates --json",
        "required_inputs": ["none; debugger emits committed template golden scenarios"],
        "proof_limit": "Template golden-scenario proof: shows changed decisions for shipped templates only; it does not justify adding speculative templates.",
        "escalation_command": "python tools\\audit\\check_coach_plan_templates.py",
    },
    {
        "symptom_class": "wrong_switch",
        "matched_lane": "boss_ai",
        "title": "Boss selected the wrong switch",
        "keywords": ["wrong switch", "bad switch", "selected switch", "boss switch", "boss switched", "propose a switch", "proposed switch", "switch_sack", "expected staying", "expected to stay", "stay in", "staying in", "should stay", "switched when expected", "policy expected", "switch confidence", "switch target", "preserve"],
        "first_command": "python -m tools.boss_ai_debugger rom-switch-materialize --scenarios <scenarios.jsonl> --fail-on-mismatch",
        "required_inputs": ["scenario JSONL with the disputed switch case", "base route or manifest if the default materializer cannot position the battle"],
        "proof_limit": "ROM materialization proof for supplied switch scenarios, with switch_roll frequency exact only when the final threshold is supplied or the threshold-bias range collapses to one probability; without a scenario this remains only routing guidance.",
        "escalation_command": "python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 24 --seed 1",
    },
    {
        "symptom_class": "wrong_move_score",
        "matched_lane": "boss_ai",
        "title": "Boss selected the wrong move or score",
        "keywords": ["wrong move", "bad move", "move score", "scoring", "selected move", "score mismatch", "ai move"],
        "first_command": "python -m tools.boss_ai_debugger decision-trace --scenario <scenarios.jsonl> --scenario-id <id>",
        "required_inputs": ["scenario JSONL with the disputed move-score case", "scenario id when the file contains multiple cases"],
        "proof_limit": "Python decision-trace proof for a supplied scenario; use ROM score materialization before claiming emulator-equivalent scoring.",
        "escalation_command": "python -m tools.boss_ai_debugger rom-score-materialize --scenarios <scenarios.jsonl> --fail-on-mismatch",
    },
    {
        "symptom_class": "general",
        "matched_lane": "general",
        "title": "General debugger starting point",
        "keywords": [],
        "first_command": "python -m tools.debugger triage --symptom \"<symptom>\"",
        "required_inputs": ["specific symptom text or changed file path"],
        "proof_limit": "Routing only: triage chooses a subsystem and commands, but does not prove runtime behavior by itself.",
        "escalation_command": "python -m tools.debugger investigate --symptom \"<symptom>\"",
    },
]

REGRESSION_GATES = {
    "script_vm_impossible_state": "python -m tools.debugger script-resume-gate --report .local\\tmp\\trainer_evo_resume_watch.json",
    "vram_request_contract": "python tools\\audit\\check_vram_request_contract.py",
    "crash_reset": "python -m tools.debugger watch --reset-sentinel --rom pokegold.gbc --symbols pokegold.sym --save-state <state-before-trigger> --frames 1200 --context-frames 20",
    "overworld_poison_cure": "python tools\\audit\\check_overworld_poison_cure.py",
    "base_ai_move_legality": "python tools\\audit\\check_base_ai_mechanics_correctness.py",
    "boss_ai_sleep_clause_move_legality": "python -m tools.boss_ai_debugger move-score-probe --trainer <TRAINER> --enemy <ENEMY> --player-save <save.sav> --player-slot <slot> --sleep-clause both --trace",
    "boss_ai_type_immunity_move_choice": "python -m tools.boss_ai_debugger move-score-probe --trainer <TRAINER> --enemy <ENEMY> --player-save <save.sav> --player-slot <slot> --trace",
    "boss_ai_hidden_power_type": "python -m tools.boss_ai_debugger move-score-probe --trainer <TRAINER> --enemy <ENEMY> --player-save <save.sav> --player-slot <slot> --trace",
    "early_boss_debuff_spam": "python -m tools.boss_ai_debugger batch-simulate --scenarios .local\\tmp\\early_boss_debuff_scenarios.jsonl --limit 20",
    "learnset_semantics": "python -m tools.debugger learnset-inspect --species <SPECIES> --level <LEVEL>",
    "grass_regrowth_balance": "python -m tools.debugger grass-regrowth --max-total-hp 300",
    "base_data_mutation_hazard": "python tools\\audit\\bug_hunt_triage.py --max-leads 12",
    "move_search_unbounded": "python tools\\audit\\bug_hunt_triage.py --max-leads 12",
    "pgoal_audit_internals": "python -m tools.debugger audit --json-out .local\\tmp\\q_audit.json",
    "asm_gotcha_reference": "python tools\\audit\\check_farcall_hl_clobber.py",
    "repo_navigation": "python tools\\audit\\check_release_smoke.py",
    "save_format_change": "python tools\\audit\\check_save_format_version.py",
    "trace_rom_divergence": "python tools\\verify_sha1.py pokegold.gbc",
    "content_mirror_state": "python -m tools.debugger compare --changed-file maps\\NewBarkTown.asm",
    "qol_gate_design": "python tools\\audit\\check_navigation_floor.py",
    "damage_math_hazard": "python tools\\audit\\check_battle_math_safety.py",
    "damage_matchup_cli": "python -m tools.damage_debugger.clobber_smoke",
    "headless_battle_simulation": "python tools\\audit\\check_headless_battle_simulator.py",
    "type_chart_navigation": "python tools\\audit\\check_release_smoke.py",
    "add_new_move_navigation": "python tools\\audit\\check_release_smoke.py",
    "boss_ai_navigation": "python tools\\audit\\check_boss_ai_no_cheat.py",
    "wram_bank_ret_crash": "python -m tools.debugger wram-bank-hazards --source-file engine\\battle\\ai\\observation_log.asm",
    "haki_taunt_read": "python tools\\audit\\check_haki_oracle_uniform.py",
    "ko_band_pressure": "python tools\\audit\\check_ko_band_oracle_materialized.py",
    "revealed_effect_response": "python tools\\audit\\check_revealed_effect_matrix_coverage.py",
    "observation_tendency_behavior": "python tools\\audit\\check_observation_log_invariants.py",
    "role_package": "python tools\\audit\\check_role_package_classifier.py",
    "coach_template": "python tools\\audit\\check_coach_plan_templates.py",
    "wrong_switch": "python -m tools.boss_ai_debugger rom-switch-materialize --scenarios <scenarios.jsonl> --fail-on-mismatch",
    "wrong_move_score": "python -m tools.boss_ai_debugger rom-score-materialize --scenarios <scenarios.jsonl> --fail-on-mismatch",
    "general": "python -m tools.debugger audit",
}


SOURCE_REFS = {
    "script_vm_impossible_state": [
        "tools/debugger/next_steps.py",
        "tools/debugger/runtime_state.py",
        "tools/debugger/save_state_inspect.py",
        "tools/debugger/script_resume_gate.py",
        "tools/debugger/repro_recipes.py",
    ],
    "vram_request_contract": [
        "tools/audit/check_vram_request_contract.py",
        "home/gfx.asm",
        "home/video.asm",
    ],
    "crash_reset": [
        "tools/debugger/runtime_watch.py",
        "tools/debugger/repro_recipes.py",
        "tools/debugger/wram_bank_hazards.py",
    ],
    "overworld_poison_cure": [
        "tools/audit/check_overworld_poison_cure.py",
        "engine/events/poisonstep.asm",
    ],
    "base_ai_move_legality": [
        "tools/audit/check_base_ai_mechanics_correctness.py",
        "engine/battle/ai/move.asm",
    ],
    "boss_ai_sleep_clause_move_legality": [
        "tools/boss_ai_debugger/damage_ai_report.py",
        "tools/boss_ai_debugger/move_score_probe.py",
        "engine/battle/ai/boss_policy_move.asm",
    ],
    "boss_ai_type_immunity_move_choice": [
        "tools/boss_ai_debugger/damage_ai_report.py",
        "tools/boss_ai_debugger/move_score_probe.py",
        "engine/battle/ai/boss_policy_move.asm",
        "engine/battle/ai/boss_platform.asm",
    ],
    "boss_ai_hidden_power_type": [
        "docs/audits/rom_source_bug_audit_2026-05-24.md",
        "docs/audits/rom_bug_audit_2026-05-23.md",
        "tools/boss_ai_debugger/move_score_probe.py",
        "engine/battle/ai/boss_policy_move.asm",
        "engine/battle/ai/boss_platform.asm",
        "engine/battle/hidden_power.asm",
        "tools/audit/check_release_smoke.py",
    ],
    "early_boss_debuff_spam": [
        "tools/boss_ai_debugger/damage_ai_report.py",
        "tools/boss_ai_debugger/rom_scenarios.py",
        "engine/battle/ai/boss_policy_move.asm",
    ],
    "headless_battle_simulation": [
        "tools/headless_battle/simulator.py",
        "tools/headless_battle/README.md",
        "tools/audit/check_headless_battle_simulator.py",
    ],
    "learnset_semantics": [
        "tools/debugger/pokemon_semantics.py",
        "data/pokemon/evos_attacks.asm",
    ],
    "grass_regrowth_balance": [
        "tools/debugger/pokemon_semantics.py",
        "engine/battle/type_passive_damage_mods.asm",
    ],
    "base_data_mutation_hazard": [
        "tools/audit/bug_hunt_triage.py",
        "engine/pokemon/tempmon.asm",
        "engine/battle/ai/boss_policy_switch.asm",
        "engine/battle/ai/boss_policy_move.asm",
    ],
    "move_search_unbounded": [
        "tools/audit/bug_hunt_triage.py",
        "engine/battle/move_effects/sketch.asm",
        "engine/battle/effect_commands.asm",
    ],
    "pgoal_audit_internals": [
        "audit/omni_debugger_first_gap_action_proof_2026-05-24.md",
        "tools/debugger/__main__.py",
        "tools/debugger/catalog.py",
        "docs/debugger_godmode_codex_task.md",
        "tools/audit/check_release_smoke.py",
        "tools/audit/check_workspace_hygiene.py",
        "docs/agent_navigation/source_output_ownership.md",
        ".gitignore",
    ],
    "asm_gotcha_reference": [
        "CLAUDE.md",
        "docs/asm_authoring_guide.md",
        "home/farcall.asm",
        "tools/audit/check_farcall_hl_clobber.py",
        "tools/audit/check_cross_bank_call.py",
        "constants/battle_constants.asm",
        "engine/battle/core.asm",
        "data/battle/stat_multipliers.asm",
    ],
    "repo_navigation": [
        "tools/audit/check_release_smoke.py",
        "docs/qol_handoff.md",
        "audit/manual_feel_checks_2026-04-27.md",
        "audit/farfetchd_balance_2026-04-27.md",
        "audit/yanma_balance_2026-04-27.md",
        "audit/ariados_balance_2026-04-27.md",
        "docs/balance_intent.md",
        "docs/buff_backlog.md",
        "docs/generated/dev_index.md",
        "scripts/generate_dev_index.py",
        "maps/CianwoodCity.asm",
        "maps/SproutTower3F.asm",
        "maps/IlexForest.asm",
        "data/pokemon/base_stats/farfetch_d.asm",
        "data/pokemon/evos_attacks.asm",
        "home/hm_moves.asm",
    ],
    "save_format_change": [
        "constants/misc_constants.asm",
        "ram/sram.asm",
        "ram/wram.asm",
        "tools/audit/check_save_format_version.py",
        "CLAUDE.md",
    ],
    "trace_rom_divergence": [
        "roms.sha1",
        "Makefile",
        "tools/verify_sha1.py",
        "tools/trace/boss_ai_trace_batch.py",
        "CLAUDE.md",
    ],
    "content_mirror_state": [
        "tools/debugger/content_mirror.py",
        "tools/debugger/content_scenarios.py",
        "tools/debugger/content_state.py",
        "tools/debugger/state_space.py",
        "tools/debugger/setup_plan.py",
        "tools/debugger/README.md",
        "tools/debugger/tests/test_catalog.py",
        "maps/NewBarkTown.asm",
    ],
    "qol_gate_design": [
        "docs/agent_navigation/verification_matrix.md",
        "docs/qol_handoff.md",
        "tools/audit/check_release_smoke.py",
        "tools/audit/check_navigation_floor.py",
        "engine/events/overworld.asm",
        "audit/manual_feel_checks_2026-04-27.md",
    ],
    "damage_math_hazard": [
        "docs/asm_authoring_guide.md",
        "tools/damage_debugger/clobber_smoke.py",
        "tools/damage_debugger/fuzz.py",
        "tools/debugger/next_steps.py",
        "tools/audit/check_battle_math_safety.py",
        "engine/battle/type_passive_damage_mods.asm",
        "engine/battle/late_gen_held_items.asm",
    ],
    "damage_matchup_cli": [
        "tools/damage_debugger/README.md",
        "docs/damage_query_cli_codex_task.md",
        "tools/damage_debugger/matchup.py",
        "tools/debugger/README.md",
        "tools/audit/check_release_smoke.py",
    ],
    "type_chart_navigation": [
        "data/types/type_matchups.asm",
        "constants/type_constants.asm",
        "engine/battle/effect_commands.asm",
    ],
    "add_new_move_navigation": [
        "constants/move_constants.asm",
        "data/moves/moves.asm",
        "data/moves/effects_pointers.asm",
        "engine/battle/effect_commands.asm",
        "data/moves/names.asm",
        "data/moves/animations.asm",
        "engine/battle/ai/scoring.asm",
    ],
    "boss_ai_navigation": [
        "docs/project_context.md",
        "engine/battle/ai/PLATFORM_API.md",
        "engine/battle/ai/POLICY_DESIGN.md",
        "engine/battle/ai/boss_platform.asm",
        "tools/audit/check_boss_ai_no_cheat.py",
        "tools/audit/check_boss_ai_gating.py",
        "ram/wram.asm",
        "docs/generated/dev_index.md",
        "CLAUDE.md",
    ],
    "wram_bank_ret_crash": [
        "home/wram_bank.asm",
        "ram/wram.asm",
        "engine/battle/ai/observation_log.asm",
        "tools/audit/check_observation_log_invariants.py",
        "tools/debugger/wram_bank_hazards.py",
    ],
    "haki_taunt_read": [
        "tools/audit/check_haki_oracle_uniform.py",
        "data/trainers/ai_haki_excluded.asm",
        "engine/battle/ai/boss_policy_switch.asm",
        "docs/boss_ai_spec.md",
        "engine/battle/ai/haki_taunt_queue.asm",
        "data/boss_ai/haki_taunts.asm",
    ],
    "ko_band_pressure": [
        "tools/audit/check_ko_band_oracle_self_test.py",
        "tools/audit/check_ko_band_oracle_materialized.py",
        "engine/battle/ai/ko_band_oracle.asm",
    ],
    "revealed_effect_response": [
        "tools/audit/check_revealed_effect_matrix_coverage.py",
        "data/boss_ai/revealed_effect_matrix.asm",
        "engine/battle/ai/boss_policy_move.asm",
    ],
    "observation_tendency_behavior": [
        "tools/audit/check_observation_log_invariants.py",
        "engine/battle/ai/observation_log.asm",
        "engine/battle/ai/boss_policy_move.asm",
    ],
    "role_package": [
        "tools/boss_ai_debugger/role_packages.py",
        "tools/audit/check_role_package_classifier.py",
        "data/boss_ai/role_package_classifier.asm",
        "engine/battle/ai/boss_policy_switch.asm",
    ],
    "coach_template": [
        "tools/boss_ai_debugger/coach_plan_templates.py",
        "tools/audit/check_coach_plan_templates.py",
        "data/boss_ai/coach_plan_templates.asm",
        "engine/battle/ai/boss_policy_move.asm",
    ],
    "wrong_switch": [
        "tools/debugger/next_steps.py",
        "tools/debugger/replay.py",
        "tools/boss_ai_debugger/rom_switch_materialize.py",
        "tools/boss_ai_debugger/generators.py",
        "engine/battle/ai/boss_policy_switch.asm",
        "engine/battle/ai/switch.asm",
        "tools/boss_ai_debugger/README.md",
        "docs/project_roadmap.md",
        "docs/pokemon_mastery/policy_cards/active_pressure_before_status.md",
        "docs/pokemon_mastery/heuristic_core/converter_before_script.md",
    ],
    "wrong_move_score": [
        "tools/boss_ai_debugger/decision_trace.py",
        "tools/boss_ai_debugger/rom_score_materialize.py",
        "engine/battle/ai/boss_policy_move.asm",
        "tools/boss_ai_debugger/scorer.py",
    ],
    "general": [
        "tools/debugger/README.md",
        "docs/README.md",
        "docs/project_roadmap.md",
    ],
}


EVIDENCE_STANDARDS = {
    "script_vm_impossible_state": [
        "A captured state report shows impossible script PC/bank/stack state, and the fix claim is rerun through script-resume-gate on a before-trigger watch. For trainer-battle evolution freezes, use python -m tools.debugger script-resume-gate --report .local\\tmp\\trainer_evo_resume_watch.json and the trainer-battle-evolution-resume recipe.",
    ],
    "vram_request_contract": [
        "The VRAM request contract audit passes on current source, and any supplied evolution/graphics trigger stays clear under a reset-sentinel watch.",
    ],
    "crash_reset": [
        "A before-trigger replay/watch either catches the reset sentinel with PC/register/WRAM context or reruns the same trigger window clean after a fix.",
    ],
    "overworld_poison_cure": [
        "The committed poison-step repro audit passes; claims beyond that fixture need an exact save/replay for the reported status path.",
    ],
    "base_ai_move_legality": [
        "The base AI mechanics audit proves the shared legality gate, and a specific trainer claim needs a scenario or emulator replay for that battle.",
    ],
    "boss_ai_sleep_clause_move_legality": [
        "A save-backed move-score probe with active Sleep Clause shows the sleep move is rejected or explains the live score delta.",
    ],
    "boss_ai_type_immunity_move_choice": [
        "A save-backed damage/move-score report shows the type-immunity score path and is paired with trace or ROM materialization before a live-fight claim.",
    ],
    "boss_ai_hidden_power_type": [
        "A trace or materialized probe shows the live Hidden Power type path and the score/legality decision that used it. The answer distinguishes the static move row type from battle-time Hidden Power type derivation and names the Boss AI stale-type decision path; release smoke remains the regression gate.",
    ],
    "early_boss_debuff_spam": [
        "Repeated generated or save-backed boss states show the debuff score pattern across turns, not just a single surprising move.",
    ],
    "learnset_semantics": [
        "Source learnset inspection proves the current table projection; save-specific claims also inspect the party slot in the supplied save.",
    ],
    "grass_regrowth_balance": [
        "The formula mirror prints the cutoff for the current source, and battle-state eligibility is proven separately when the report is live-state-specific.",
    ],
    "base_data_mutation_hazard": [
        "Static triage names a concrete lead, then provenance or a targeted trace proves whether the candidate GetBaseData path mutates the reported state.",
    ],
    "move_search_unbounded": [
        "Static triage identifies the exact move-search lead, then source proof or a runtime trace confirms the missing bound/restoration behavior.",
    ],
    "pgoal_audit_internals": [
        "The answer states that python -m tools.debugger audit inspects route definitions, not proof artifacts, so documenting a route does not decrement gap_actions. Durable proof belongs in audit/ while .local/tmp is scratch. New release-smoke gates live in tools/audit/check_release_smoke.py, and workspace hygiene checks artifact ownership with python tools/audit/check_workspace_hygiene.py.",
    ],
    "asm_gotcha_reference": [
        "The answer names farcall macro expansion order, the cross-bank plain-call locality rule, BASE_STAT_LEVEL = 7 stat-stage encoding, and points to check_farcall_hl_clobber.py, check_cross_bank_call.py, constants/battle_constants.asm, and data/battle/stat_multipliers.asm. For stat-stage byte questions, verify with python -c \"import re; c=open('constants/battle_constants.asm').read(); m=re.search(r'BASE_STAT_LEVEL\\s+EQU\\s+(\\d+)', c); assert m and m.group(1)=='7', 'BASE_STAT_LEVEL not found or != 7'; print('BASE_STAT_LEVEL=7 confirmed')\" and keep python -m tools.damage_debugger.clobber_smoke as the broad damage regression gate.",
    ],
    "repo_navigation": [
        "The debugger names the owned source/data docs for the requested surface: HM field tools and Repel/QoL use release smoke plus docs/qol_handoff.md/manual checks; Pokemon role/showcase questions cite balance audit docs and source data; ROM bank free-space questions cite docs/generated/dev_index.md and scripts/generate_dev_index.py. For free-space proof, run python -c \"c=open('docs/generated/dev_index.md').read(); assert 'Tight Banks' in c, 'expected Tight Banks section in dev_index'; print('Tight Banks section present')\" and regenerate with python scripts/generate_dev_index.py --rom pokegold.",
    ],
    "save_format_change": [
        "The answer states no migration code exists, a SAVE_FORMAT_VERSION bump invalidates old saves, and python tools/audit/check_save_format_version.py enforces constants/misc_constants.asm against the current SRAM/WRAM layout fingerprint.",
    ],
    "trace_rom_divergence": [
        "The answer names roms.sha1, Makefile trace targets, tools/verify_sha1.py, and that pokegold.gbc is the SHA1-pinned release while pokegold_trace.gbc carries trace instrumentation. Source proof can start with python -c \"c=open('roms.sha1').read(); assert 'pokegold' in c.lower() and 'pokesilver' in c.lower(), 'roms.sha1 missing pinned ROM hashes'; print('roms.sha1 pinned for both ROMs')\".",
    ],
    "content_mirror_state": [
        "The answer explains static source-to-ROM byte mirrors with python -m tools.debugger content-mirror --source-file maps\\NewBarkTown.asm and distinguishes planned state materialization from executed content-state proof using python -m tools.debugger expect --report <content-state.json> --expect state-patch=<symbol>,applied=true,verified=true.",
    ],
    "qol_gate_design": [
        "The answer chooses python tools\\audit\\check_release_smoke.py plus python tools\\audit\\check_navigation_floor.py for QoL map script, HM tool, Repel, or communication-text changes, and names manual emulator proof gaps when the change affects feel or UI rendering.",
    ],
    "damage_math_hazard": [
        "The answer identifies register preservation or dispatcher carry-through as the likely causal class, points to wCurDamage/damage-chain proof, and requires python -m tools.damage_debugger.clobber_smoke plus python tools\\audit\\check_battle_math_safety.py.",
    ],
    "damage_matchup_cli": [
        "The answer points to the damage debugger matchup/oracle tools and gives a current concrete command such as python -m tools.damage_debugger.matchup CHARIZARD:50 LAPRAS:50 FLAMETHROWER --json before relying on memory.",
    ],
    "headless_battle_simulation": [
        "The answer routes to tools.headless_battle, uses a JSON state/actions-or-turns-or-repeat/RNG scenario, and preserves proof labels: pre-variation damage is delegated to the existing ROM-backed damage oracle, one NormalHit fixed-RNG golden is ROM-differential checked by python -m tools.headless_battle.rom_differential, selected switches and caller-supplied replacements carry active/bench state with switch-volatile reset and supported incoming residual, explicit enemy auto_replace uses the source-shaped basic type-chart replacement choice, auto_replace_or plus repeat/max_turns can run simple KO/send-out loops, wild_random_move is source-mirrored, PP decrement, explicit active HP restore item actions, explicit stat-stage state, selected BP=0 single-stat stage moves, selected Dragon Dance/Calm Mind/Quiver Dance setup moves, selected Rain Dance/Sunny Day weather setup/countdown, selected Thunder weather accuracy/order, selected Spikes setup and Spikes entry damage with replacement_pending when entry damage KO leaves a live bench, selected Recover/Softboiled/Milk Drink self-heal moves, selected PoisonPowder/Poison Gas/Toxic poison-status moves, selected Thunder Wave/Stun Spore/Glare paralysis-status moves, selected damaging burn/poison/paralysis status secondaries, selected Absorb/Mega Drain/Leech Life/Giga Drain drain moves, selected EFFECT_SLEEP moves plus Rest and sleep action denial/wake handling, selected held PSNCUREBERRY/PRZCUREBERRY/ICE_BERRY/MINT_BERRY/MIRACLEBERRY status cures after supported status applications, selected caller-supplied Safeguard/Substitute status blockers, selected Substitute move creation and Substitute HP routing for selected damaging hits, scenario-supplied or rom-switch-materialize-bridged Boss AI switch-roll branching, and supported after-hit item HP effects are covered, modified-speed order, paralyzed speed/full-paralysis action denial including Fighting/Electric type-passive paralysis modifiers, non-link equal-speed ties, basic critical hits, basic move accuracy, damage variation, selected damaging status secondary chance, selected sleep duration, Boss AI switch roll, and auto-replace fallback have fixed/sample/exhaustive RNG branching where applicable, initial poison/burn/toxic residual is source-mirrored after selected moves and supported item actions, post-score Boss AI selector replay/execution starts from known score bytes, and unimplemented strategic/full-battle mechanics remain out of scope.",
    ],
    "type_chart_navigation": [
        "The answer names data/types/type_matchups.asm, constants/type_constants.asm, and the runtime reader in engine/battle/effect_commands.asm before suggesting any matchup edit.",
    ],
    "add_new_move_navigation": [
        "The answer names the move-id constant, move data row, name string, effect pointer slot, animation slot, and AI scoring entry; the proof packet is python -m tools.debugger next --symptom \"where do I add a new move end-to-end\" --json-out .local\\tmp\\q_add_move.json.",
    ],
    "boss_ai_navigation": [
        "The answer cites the public-info invariant, timing rule, observation commit boundary, no-cheat/gating audits, and for WRAM budget questions consults ram/wram.asm plus docs/generated/dev_index.md Boss AI WRAM Reserve. Use python -c \"c=open('docs/generated/dev_index.md').read(); assert 'Boss AI WRAM Reserve' in c or 'Boss AI' in c, 'expected Boss AI section in dev_index'; print('Boss AI dev_index section present')\" and python scripts/generate_dev_index.py --rom pokegold for current budget proof.",
    ],
    "wram_bank_ret_crash": [
        "The answer explains that SVBK remaps $D000-$DFFF so call/ret with SP in remapped WRAMX can pop a return address from the wrong bank, then runs check_observation_log_invariants.py or wram-bank-hazards on the source file.",
    ],
    "haki_taunt_read": [
        "The Haki oracle audit passes on current source tables and names the ai_haki_excluded exclusion table, the boss policy switch surface (BossAI_OracleHakiRead defined in boss_policy_switch.asm; BossAI_QueueHakiTaunt defined in haki_taunt_queue.asm and invoked from boss_policy_switch.asm), and the tier-and-class gate logic upstream of the oracle call. Proof can start with python -m tools.debugger next --symptom \"where is the boss AI Haki eligibility gate\" --json-out .local\\tmp\\q_haki.json; emulator-live textbox or render claims need a separate live scenario.",
    ],
    "ko_band_pressure": [
        "The KO-band oracle materialization audit passes for committed scenarios; arbitrary fight claims need a matching scenario file.",
    ],
    "revealed_effect_response": [
        "The revealed-effect matrix coverage audit proves dispatch/table coverage, while a specific battle branch needs scenario-backed state.",
    ],
    "observation_tendency_behavior": [
        "The observation invariant audit passes its golden tendency/calibration cases, and arbitrary multi-turn claims need a reconstructed fight state.",
    ],
    "role_package": [
        "The role-package debugger/table audit agrees for the species under question, and switch-confidence claims also need a scenario/control case.",
    ],
    "coach_template": [
        "The coach-template debugger emits the committed golden scenarios and the audit confirms the shipped template decision deltas.",
    ],
    "wrong_switch": [
        "A scenario JSONL matching the disputed switch case passes rom-switch-materialize on the current ROM with --fail-on-mismatch, checked_count > 0, and error_count == 0. The route names BossAI_SwitchOrTryItem, switch WRAM targets, the boss_policy_switch source anchors, and the scenario materialization command so the ordinary-language wrong-switch question is answered with a runnable proof. For switch_sack converter disagreement, rerun python -m tools.boss_ai_debugger rom-switch-materialize --scenarios <switch_sack_scenarios.jsonl> --limit 3 --fail-on-mismatch and name the scenario id, expected/proposed switch values, confidence, observation_status, switch_roll availability/frequency/probability_exact status, policy why text, ROM switch path, and stale-expectation-vs-ROM-bug status. If rom-switch-materialize reports a trace-ROM/symbol hash mismatch or says the base state is already inside/past BossAI_SwitchOrTryItem, do not treat the old shared-switch snapshot as proof; regenerate a current pre-dispatch switch_materialization_state first. Use --switch-threshold <byte> only when the final threshold is known externally and should be reported as exact; if switch_roll.available=false, say no final switch roll was observed instead of calling it a 0% switch chance.",
    ],
    "wrong_move_score": [
        "Decision trace explains the disputed score from the scenario, and rom-score-materialize passes before claiming emulator-equivalent scoring.",
    ],
    "general": [
        "Triage chooses a concrete lane and the follow-up command is rerun with the required artifacts named by that lane.",
    ],
}


DISPROOF_STANDARDS = {
    "script_vm_impossible_state": [
        "If the same captured or before-trigger report passes script-resume-gate and no invalid script/reset event appears, including the trainer evolution resume report, this route did not prove the freeze.",
    ],
    "vram_request_contract": [
        "If the contract audit passes and a reset-sentinel watch of the reported graphics trigger shows no stuck request or reset, look outside queued VRAM request acknowledgement.",
    ],
    "crash_reset": [
        "If the reported trigger replay never reaches reset/start vectors and PC/SP snapshots stay coherent, this route did not reproduce the reset; extend the trigger or reroute.",
    ],
    "overworld_poison_cure": [
        "If the poison-step audit passes and an exact save/replay does not reproduce the reported HP/status transition, reject this poison-step bug class.",
    ],
    "base_ai_move_legality": [
        "If the base AI audit passes and a matching battle scenario shows the shared legality gate rejects the reported illegal move, look outside base AI legality.",
    ],
    "boss_ai_sleep_clause_move_legality": [
        "If the save-backed probe with the same Sleep Clause state rejects the sleep move and trace/materialization agrees, the reported choice is not explained by this gate.",
    ],
    "boss_ai_type_immunity_move_choice": [
        "If the matching save/scenario scores the immune move as illegal or losing and trace/materialization agrees, reroute to state mismatch, Hidden Power typing, or scenario setup.",
    ],
    "boss_ai_hidden_power_type": [
        "If source shows Boss AI now derives Hidden Power's runtime type before immunity gating and release smoke covers it, reject a stale Normal-type hypothesis.",
    ],
    "early_boss_debuff_spam": [
        "If repeated generated or save-backed states do not keep selecting/scoring debuffs across turns, treat the report as a single-turn surprise rather than spam.",
    ],
    "learnset_semantics": [
        "If source inspection and party inspection both show the expected move set for the named species/level/save, reject a learnset-table bug.",
    ],
    "grass_regrowth_balance": [
        "If the formula mirror shows the expected cutoff and live-state eligibility is absent, reject a formula/cutoff bug and investigate battle-state gating instead.",
    ],
    "base_data_mutation_hazard": [
        "If static provenance or runtime trace shows the candidate GetBaseData path restores the reported state before reuse, reject this mutation-hazard lead.",
    ],
    "move_search_unbounded": [
        "If source proof or trace shows the move-search loop is bounded and restores the reported last-move state, reject this move-search bug class.",
    ],
    "pgoal_audit_internals": [
        "If the answer claims running materialize or storing scratch files under .local/tmp closes gap_actions, or suggests an unwired one-off release audit, it misread the audit/artifact contract.",
    ],
    "asm_gotcha_reference": [
        "If the answer says push/pop around farcall fixes target-input hl, treats exported :: labels as safe for plain call across banks, or reads stat-stage bytes as raw multipliers instead of BASE_STAT_LEVEL=7, reject this route.",
    ],
    "repo_navigation": [
        "If the answer only says to grep source and omits the owned audit/doc/source surfaces for the feature or data question, the navigation route is incomplete. If generated balance audit and release smoke disagree with claimed held item, learnset, Stick critical behavior, Yanma/Ariados move levels, or HM field-tool mappings, the route is stale.",
    ],
    "save_format_change": [
        "If the answer suggests there is a migration path or that SAVE_FORMAT_VERSION bumps are harmless to existing saves, reject the route.",
    ],
    "trace_rom_divergence": [
        "If the answer claims pokegold_trace.gbc and pokegold.gbc are the same release artifact or points to the trace ROM as distributable, reject the route.",
    ],
    "content_mirror_state": [
        "If content-mirror cannot resolve source labels or content-state cannot apply and verify the requested state patch, do not treat the map/script landing claim as proven.",
    ],
    "qol_gate_design": [
        "If release smoke or navigation floor fails, or a user-facing flow was not manually exercised when required, the QoL change is not done.",
    ],
    "damage_math_hazard": [
        "If clobber_smoke and battle-math safety pass on the current ROM and no touched damage-chain contract changed, this damage-chain bug class is disproven.",
    ],
    "damage_matchup_cli": [
        "If matchup output or clobber smoke disagrees with the claimed damage path, defer to current debugger evidence rather than memory.",
    ],
    "headless_battle_simulation": [
        "If the report claims strategic automatic full-battle action choice, automatic trainer item usage, player trainer-battle Pack availability, inventory accounting, implicit replacement without auto_replace_or or auto_replace, Pursuit/Spikes/switch-in effects, link-battle turn-order inversion, accuracy/evasion stage moves/modifiers, damaging secondary stat effects outside selected burn/poison/paralysis status secondaries, multi-stat chains outside Dragon Dance/Calm Mind/Quiver Dance, Baton Pass/Psych Up, Substitute/Mist blockers outside selected status blockers, badge boosts, passive stat/speed/accuracy bonuses outside the listed paralysis path, status application outside selected poison/paralysis/sleep-status moves and selected damaging status secondaries, sleep mechanics outside selected sleep moves/Rest/action denial, freeze, burn application outside selected damaging burn secondaries, Safeguard duration/expiration, Substitute Baton Pass/multi-hit continuation details, held status prevent items, freeze/confusion held cures, Sleep Clause clearing from held sleep cures, non-paralyzed Electric speed passives, weather/time healing, drain effects outside selected EFFECT_LEECH_HIT moves, Heal Bell, RNG-consuming mechanics outside the listed supported branch points, live Boss AI scoring, Boss AI switch candidate/confidence generation, AI_TryItem, scripts, or byte-proven turn sequencing beyond the listed coverage labels, reject the route as overclaimed.",
    ],
    "type_chart_navigation": [
        "If the answer returns engine battle code without naming data/types/type_matchups.asm, it missed the matchup data file.",
    ],
    "add_new_move_navigation": [
        "If the answer only names constants/move_constants.asm and omits data-side tables, effect pointers, animation, and AI scoring, the route failed the new-move question.",
    ],
    "boss_ai_navigation": [
        "If audits find hidden party, unrevealed moves/items, private stats, future input, current-turn input consumption, or stale WRAM budget data that does not match docs/generated/dev_index.md, the answer is invalid.",
    ],
    "wram_bank_ret_crash": [
        "If the source no longer switches WRAM banks across a call/ret with the stack in remapped WRAMX, reject this crash route for that file.",
    ],
    "haki_taunt_read": [
        "If the Haki oracle audit passes and a live scenario does not show the reported taunt/read, reject this oracle-read route. If the answer points only at the original bespoke Morty Haki path and omits the uniform oracle refactor that consolidates the exclusion table, the route is stale.",
    ],
    "ko_band_pressure": [
        "If the matching scenario passes KO-band materialization without the reported pressure/deny-KO delta, reject this KO-band hypothesis.",
    ],
    "revealed_effect_response": [
        "If matrix coverage passes and a matching scenario does not enter the reported revealed-effect branch, reject this matrix-response route.",
    ],
    "observation_tendency_behavior": [
        "If golden invariants pass and a reconstructed multi-turn state does not reproduce the tendency/calibration delta, reject this observation-log route.",
    ],
    "role_package": [
        "If debugger classification, table audit, and a scenario/control case agree on a different package or no switch-confidence effect, reject this role-package route.",
    ],
    "coach_template": [
        "If the template golden scenarios and audit do not reproduce the reported decision delta, reject this coach-template route.",
    ],
    "wrong_switch": [
        "If a matching scenario JSONL passes rom-switch-materialize with the expected switch result, the wrong-switch claim is disproven for that scenario. If rerunning the same switch_sack scenario no longer reports the disagreement, if switch_roll.available=false because no switch dispatch observation was reached, if the trace-ROM/symbol hashes mismatch, if the base state is already inside/past BossAI_SwitchOrTryItem, or the answer cannot connect the policy card to BossAI_SwitchOrTryItem behavior, this candidate should not be treated as proven. If the returned route omits rom-switch-materialize or routes to damage/banking fallbacks instead of the boss_policy_switch surface, the oracle failed this question.",
    ],
    "wrong_move_score": [
        "If decision trace and rom-score-materialize agree with the expected score on the supplied scenario, the wrong-score claim is disproven for that scenario.",
    ],
    "general": [
        "If triage cannot name a concrete lane or the lane-specific artifacts do not reproduce the symptom, do not treat the packet as evidence of a bug.",
    ],
}


def _ensure_regression_gate(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("regression_gate"):
        return row
    row["regression_gate"] = REGRESSION_GATES.get(
        str(row.get("symptom_class", "")),
        str(row.get("first_command") or row.get("escalation_command") or "python -m tools.debugger audit"),
    )
    return row


def _ensure_source_refs(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("source_refs"):
        return row
    row["source_refs"] = SOURCE_REFS.get(str(row.get("symptom_class", "")), SOURCE_REFS["general"])
    return row


def _ensure_evidence_standard(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("evidence_standard"):
        return row
    row["evidence_standard"] = EVIDENCE_STANDARDS.get(str(row.get("symptom_class", "")), EVIDENCE_STANDARDS["general"])
    return row


def _ensure_disproof_standard(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("disproof_standard"):
        return row
    row["disproof_standard"] = DISPROOF_STANDARDS.get(str(row.get("symptom_class", "")), DISPROOF_STANDARDS["general"])
    return row


def _ensure_row_metadata(row: dict[str, Any]) -> dict[str, Any]:
    _ensure_regression_gate(row)
    _ensure_source_refs(row)
    _ensure_evidence_standard(row)
    _ensure_disproof_standard(row)
    return row


for _row in NEXT_STEP_ROWS:
    _ensure_row_metadata(_row)


def build_next_step(
    *,
    symptom: str = "",
    changed_files: tuple[str, ...] = (),
    root: Path = ROOT,
) -> dict[str, Any]:
    triage = triage_request(changed_files=changed_files, symptom=symptom, root=root)
    candidates = _matching_rows(symptom)
    if not candidates:
        candidates = [_fallback_row(triage, symptom)]
    recommendation = candidates[0]

    return {
        "schema_version": 1,
        "kind": "unified_debugger_next_step",
        "root": str(root),
        "symptom": symptom,
        "changed_files": list(changed_files),
        "matched_lane": recommendation["matched_lane"],
        "recommendation": _public_row(recommendation),
        "candidates": [_public_row(row) for row in candidates[:5]],
        "triage_match_ids": [match["id"] for match in triage.get("matches", [])],
        "triage_commands": list(triage.get("commands", [])),
    }


def symptom_only_investigation_note(
    report: dict[str, Any],
    *,
    next_step: dict[str, Any] | None = None,
) -> str:
    symptom = str(report.get("symptom") or "").strip()
    if not symptom:
        return ""
    if _has_runtime_anchor(report):
        return ""
    if next_step is None:
        next_step = build_next_step(symptom=symptom)
    command = next_step["recommendation"]["first_command"]
    return (
        "No runtime evidence supplied. This is a planning packet, not a repro. "
        f"Suggested shorter path: python -m tools.debugger next --symptom {symptom!r} "
        f"(first command: {command})"
    )


def _matching_rows(symptom: str) -> list[dict[str, Any]]:
    text = symptom.lower()
    if not text:
        return []
    rows = []
    for row in NEXT_STEP_ROWS:
        if row["symptom_class"] == "general":
            continue
        if any(keyword_matches(keyword, text) for keyword in row["keywords"]):
            rows.append(row)
    return rows


def _fallback_row(triage: dict[str, Any], symptom: str) -> dict[str, Any]:
    row = dict(next(item for item in NEXT_STEP_ROWS if item["symptom_class"] == "general"))
    matches = triage.get("matches", [])
    if matches:
        match_id = str(matches[0].get("id") or row["matched_lane"])
        row["matched_lane"] = match_id
        if match_id in _TRIAGE_FALLBACK_ROWS:
            row.update(_TRIAGE_FALLBACK_ROWS[match_id])
    if symptom:
        row["first_command"] = f"python -m tools.debugger triage --symptom {symptom!r}"
        row["escalation_command"] = f"python -m tools.debugger investigate --symptom {symptom!r}"
    return _ensure_row_metadata(row)


_TRIAGE_FALLBACK_ROWS = {
    "boss_ai_live_move": {
        "title": "Boss AI live move-choice or legality symptom",
        "first_command": "python -m tools.boss_ai_debugger damage-ai-report --trainer <TRAINER> --enemy <ENEMY> --player-save <save.sav> --player-slot <slot> --sleep-clause both",
        "required_inputs": ["trainer id, enemy mon selector, player save, and active party slot"],
        "proof_limit": "Exact damage plus move-score report for the supplied state; use trace mode or ROM materialization for final live proof.",
        "source_refs": [
            "tools/boss_ai_debugger/damage_ai_report.py",
            "tools/boss_ai_debugger/move_score_probe.py",
            "engine/battle/ai/boss_policy_move.asm",
        ],
        "evidence_standard": [
            "A save-backed damage/move-score report explains the live move decision, then trace or ROM materialization confirms it before a fight-wide claim.",
        ],
        "disproof_standard": [
            "If the matching save-backed report and trace/materialization agree with the expected legal move choice, reject this live move-choice route.",
        ],
        "regression_gate": "python -m tools.boss_ai_debugger move-score-probe --trainer <TRAINER> --enemy <ENEMY> --player-save <save.sav> --player-slot <slot> --trace",
        "escalation_command": "python -m tools.boss_ai_debugger move-score-probe --trainer <TRAINER> --enemy <ENEMY> --player-save <save.sav> --player-slot <slot> --trace",
    },
    "overworld_status": {
        "title": "Overworld status, poison-step, or field HP state",
        "first_command": "python tools\\audit\\check_overworld_poison_cure.py",
        "required_inputs": ["none; audit builds/runs the committed poison-step repro"],
        "proof_limit": "Runtime audit proof for the poison-step fixture; it does not prove unrelated battle poison behavior.",
        "source_refs": [
            "tools/audit/check_overworld_poison_cure.py",
            "engine/events/poisonstep.asm",
        ],
        "evidence_standard": [
            "The committed poison-step repro audit passes; other status claims need a save/replay for that exact path.",
        ],
        "disproof_standard": [
            "If the poison-step audit passes and the exact save/replay does not reproduce the reported status transition, reject this field-status route.",
        ],
        "regression_gate": "python tools\\audit\\check_overworld_poison_cure.py",
        "escalation_command": "python -m tools.debugger investigate --changed-file engine/events/poisonstep.asm",
    },
    "base_ai_mechanics": {
        "title": "Base non-boss AI mechanics and move legality",
        "first_command": "python tools\\audit\\check_base_ai_mechanics_correctness.py",
        "required_inputs": ["none; audit reads the shared base AI move scoring path"],
        "proof_limit": "Static contract proof for base AI legality gates; it does not prove a specific trainer battle without an emulator scenario.",
        "source_refs": [
            "tools/audit/check_base_ai_mechanics_correctness.py",
            "engine/battle/ai/move.asm",
        ],
        "evidence_standard": [
            "The base AI mechanics audit proves the shared legality gate; battle-specific claims need a matching scenario or replay.",
        ],
        "disproof_standard": [
            "If the audit and matching battle scenario show the legality gate rejects the reported move, reject this base-AI legality route.",
        ],
        "regression_gate": "python tools\\audit\\check_base_ai_mechanics_correctness.py",
        "escalation_command": "python -m tools.debugger investigate --changed-file engine/battle/ai/move.asm",
    },
    "pokemon_semantics": {
        "title": "Pokemon data semantics, learnsets, party state, or type passives",
        "first_command": "python -m tools.debugger learnset-inspect --species <SPECIES> --level <LEVEL>",
        "required_inputs": ["species and level; use party-inspect when checking a specific save"],
        "proof_limit": "Semantic source/save inspection only; use content mirrors or runtime probes for ROM-byte or live battle proof.",
        "source_refs": [
            "tools/debugger/pokemon_semantics.py",
            "data/pokemon/evos_attacks.asm",
            "engine/battle/type_passive_damage_mods.asm",
        ],
        "evidence_standard": [
            "Source semantic inspection answers table/formula questions; save-specific claims also inspect the supplied party slot or live state.",
        ],
        "disproof_standard": [
            "If source inspection and save/live inspection match the expected semantics, reject this data-semantics route and investigate state or UI interpretation.",
        ],
        "regression_gate": "python -m tools.debugger learnset-inspect --species <SPECIES> --level <LEVEL>",
        "escalation_command": "python -m tools.debugger party-inspect --save <save.sav> --slot <slot>",
    },
    "static_bug_hunt": {
        "title": "Static bug-family lead finder",
        "first_command": "python tools\\audit\\bug_hunt_triage.py --max-leads 12",
        "required_inputs": ["none; triage scans current source for prior bug-family hazards"],
        "proof_limit": "Static lead finder; each lead still needs source proof or a targeted runtime trace before patching.",
        "source_refs": [
            "tools/audit/bug_hunt_triage.py",
            "engine/pokemon/tempmon.asm",
            "engine/battle/effect_commands.asm",
        ],
        "evidence_standard": [
            "Static triage names a concrete bug-family lead, then provenance or runtime trace proves whether that lead reaches the reported state.",
        ],
        "disproof_standard": [
            "If provenance or trace shows the lead cannot reach the reported state, reject it instead of patching from static suspicion.",
        ],
        "regression_gate": "python tools\\audit\\bug_hunt_triage.py --max-leads 12",
        "escalation_command": "python -m tools.debugger provenance --symbol wCurSpecies --symbol GetBaseData",
    },
}


def _public_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "symptom_class": row["symptom_class"],
        "matched_lane": row["matched_lane"],
        "title": row["title"],
        "first_command": row["first_command"],
        "required_inputs": list(row["required_inputs"]),
        "proof_limit": row["proof_limit"],
        "source_refs": list(row["source_refs"]),
        "evidence_standard": list(row["evidence_standard"]),
        "disproof_standard": list(row["disproof_standard"]),
        "escalation_command": row["escalation_command"],
        "regression_gate": row["regression_gate"],
        "repro_recipes": list(row.get("repro_recipes", ())),
    }


def _has_runtime_anchor(report: dict[str, Any]) -> bool:
    if report.get("symbols") or report.get("changed_files"):
        return True
    for key in ("input_traces", "input_scenarios", "input_reports", "patches", "watch_symbols", "rules", "addresses", "expectations", "expectation_files"):
        value = report.get(key)
        if isinstance(value, list) and value:
            return True
        if isinstance(value, tuple) and value:
            return True
        if isinstance(value, str) and value:
            return True
    return False
