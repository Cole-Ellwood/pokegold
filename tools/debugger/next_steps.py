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
        "keywords": ["wrong switch", "bad switch", "selected switch", "switch confidence", "switch target", "preserve"],
        "first_command": "python -m tools.boss_ai_debugger rom-switch-materialize --scenarios <scenarios.jsonl> --fail-on-mismatch",
        "required_inputs": ["scenario JSONL with the disputed switch case", "base route or manifest if the default materializer cannot position the battle"],
        "proof_limit": "ROM materialization proof for supplied switch scenarios; without a scenario this remains only routing guidance.",
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
    "script_vm_impossible_state": "python -m tools.debugger script-resume-gate --report .local\\tmp\\debugger_runtime_state.json",
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
        "tools/boss_ai_debugger/move_score_probe.py",
        "engine/battle/ai/boss_policy_move.asm",
        "engine/battle/ai/boss_platform.asm",
        "engine/battle/hidden_power.asm",
    ],
    "early_boss_debuff_spam": [
        "tools/boss_ai_debugger/damage_ai_report.py",
        "tools/boss_ai_debugger/rom_scenarios.py",
        "engine/battle/ai/boss_policy_move.asm",
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
    "haki_taunt_read": [
        "tools/audit/check_haki_oracle_uniform.py",
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
        "tools/boss_ai_debugger/rom_switch_materialize.py",
        "engine/battle/ai/boss_policy_switch.asm",
        "engine/battle/ai/switch.asm",
        "tools/boss_ai_debugger/README.md",
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
        "A captured state report shows impossible script PC/bank/stack state, and the fix claim is rerun through script-resume-gate on a before-trigger watch.",
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
        "A trace or materialized probe shows the live Hidden Power type path and the score/legality decision that used it.",
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
    "haki_taunt_read": [
        "The Haki oracle audit passes on current source tables and names the ai_haki_excluded exclusion table, the boss policy switch surface (BossAI_OracleHakiRead defined in boss_policy_switch.asm; BossAI_QueueHakiTaunt defined in haki_taunt_queue.asm and invoked from boss_policy_switch.asm), and the tier-and-class gate logic upstream of the oracle call. Emulator-live textbox or render claims need a separate live scenario.",
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
        "A scenario JSONL matching the disputed switch case passes rom-switch-materialize on the current ROM with --fail-on-mismatch. The route names BossAI_SwitchOrTryItem, switch WRAM targets, the boss_policy_switch source anchors, and the scenario materialization command so the ordinary-language wrong-switch question is answered with a runnable proof.",
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
        "If the same captured or before-trigger state passes script-resume-gate and no invalid script/reset event appears in the replay window, this route did not reproduce the script-VM failure.",
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
        "If trace/materialization shows the expected live Hidden Power type and the score used that type, reject a stale-type hypothesis.",
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
        "If a matching scenario JSONL passes rom-switch-materialize with the expected switch result, the wrong-switch claim is disproven for that scenario. If the returned route omits rom-switch-materialize or routes to damage/banking fallbacks instead of the boss_policy_switch surface, the oracle failed this question.",
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
