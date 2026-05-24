from __future__ import annotations

from pathlib import Path
from typing import Any

from .catalog import ROOT, keyword_matches


REPRO_RECIPES: tuple[dict[str, Any], ...] = (
    {
        "id": "first-wild-route29",
        "title": "First Route 29 wild encounter reset/black-screen repro",
        "bug_class": "runtime_crash",
        "keywords": (
            "first wild",
            "wild encounter",
            "route 29",
            "reset",
            "intro",
            "black screen",
        ),
        "purpose": (
            "Capture the first post-starter grass encounter as a reset/crash proof "
            "instead of routing it into static Boss AI matrix checks."
        ),
        "inputs": (
            "Current pokegold.gbc and pokegold.sym from this checkout.",
            "A PyBoy save-state immediately before stepping into Route 29 grass, or a battery save/input route that can create that state.",
            "Optional: the source file suspected by the trace, such as engine\\battle\\ai\\observation_log.asm.",
        ),
        "setup_steps": (
            "Build or freshness-check the ROM before capturing so symbol addresses match the artifact.",
            "Start from a new-game/early Route 29 state with one party Pokemon and wBattleMode=0.",
            "Save immediately before the step that can trigger the first wild encounter.",
        ),
        "commands": (
            "python -m tools.debugger next --symptom \"first wild encounter reset to intro then black screen\"",
            "python -m tools.debugger watch --reset-sentinel --rom pokegold.gbc --symbols pokegold.sym --save-state <route29-before-grass.state> --frames 1200 --context-frames 20 --json-out .local\\tmp\\first_wild_route29_reset_watch.json",
            "python -m tools.debugger trace-instructions --symbol StartBattle --symbol ClearBattleRAM --symbol BossAI_ClearObservationLog --watch-symbol hWRAMBank --watch-symbol wBattleMode --save-state <route29-before-grass.state> --frames 1200 --execute --require-hit --out-trace .local\\tmp\\first_wild_route29_trace.jsonl",
            "python -m tools.debugger wram-bank-hazards --source-file engine\\battle\\ai\\observation_log.asm",
        ),
        "expected_signals": (
            "reset_event_count stays 0 for a fixed build.",
            "If the bug is present, reset_events names Start/Reset/_Start or 00:0000/00:0100 and includes SP, hROMBank, hWRAMBank, wBattleMode, and wTempWildMonSpecies context.",
            "A WRAM bank/stack source bug should produce a wram-bank-hazards finding before a ROM-backed trace is needed.",
        ),
        "proof_limit": (
            "This recipe proves the crash class only when the supplied state/input route actually triggers the first wild encounter; "
            "without that state it is a capture recipe, not a live repro."
        ),
    },
    {
        "id": "trainer-battle-evolution-resume",
        "title": "Trainer battle plus post-battle evolution script-resume repro",
        "bug_class": "post_battle_script_resume",
        "keywords": (
            "trainer battle evolution",
            "post-battle evolution",
            "music playing frozen",
            "frozen after trainer",
            "evolved flaffy",
            "script resume",
        ),
        "purpose": (
            "Prove that trainer after-battle context survives StartBattle and "
            "EvolveAfterBattle before scripttalkafter resumes the map script."
        ),
        "inputs": (
            "Current pokegold.gbc and pokegold.sym from this checkout.",
            "Either the corrupted VBA-M .sgm crash state for diagnosis, or a PyBoy state before the trainer-battle/evolution trigger for replay.",
            "Optional battery save plus route-specific input recipe when no PyBoy state already exists.",
        ),
        "setup_steps": (
            "Inspect any supplied .sgm first; a post-crash state can diagnose the failure but is not a replayable before-trigger proof.",
            "For forward replay, start before the trainer battle ends or before the evolution prompt advances.",
            "Watch trainer resume bytes and script VM state through the return to the overworld.",
        ),
        "commands": (
            "python -m tools.debugger state-inspect --save-state <crash-state.sgm> --symbols pokegold.sym --rom pokegold.gbc --json-out .local\\tmp\\trainer_evo_state_inspect.json",
            "python -m tools.debugger script-resume-gate --report .local\\tmp\\trainer_evo_state_inspect.json",
            "python -m tools.debugger watch --reset-sentinel --rom pokegold.gbc --symbols pokegold.sym --save-state <before-trigger.state> --watch-symbol wSeenTrainerBank --watch-symbol wScriptAfterPointer --watch-symbol wRunningTrainerBattleScript --watch-symbol wScriptBank --watch-symbol wScriptPos --watch-symbol wScriptRunning --watch-symbol wScriptMode --frames 3600 --context-frames 30 --execute --json-out .local\\tmp\\trainer_evo_resume_watch.json",
            "python -m tools.debugger watch --reset-sentinel --rom pokegold.gbc --symbols pokegold.sym --battery-save pokegold.sav --out-initial-state .local\\tmp\\trainer_evo_continue.state --input <frame:button[:delay]> --watch-symbol wSeenTrainerBank --watch-symbol wScriptAfterPointer --watch-symbol wRunningTrainerBattleScript --watch-symbol wScriptBank --watch-symbol wScriptPos --watch-symbol wScriptRunning --watch-symbol wScriptMode --frames 3600 --context-frames 30 --execute --json-out .local\\tmp\\trainer_evo_resume_watch.json",
            "python -m tools.debugger script-resume-gate --report .local\\tmp\\trainer_evo_resume_watch.json",
            "python -m tools.debugger wram-ownership --symbol wSeenTrainerBank --symbol wScriptAfterPointer --symbol wRunningTrainerBattleScript",
            "python -m tools.debugger trace-instructions --symbol Script_startbattle --symbol StartBattle --symbol EvolveAfterBattle --symbol Script_scripttalkafter --watch-symbol wScriptBank --watch-symbol wScriptPos --save-state <before-trigger.state> --frames 3600 --execute --require-hit --out-trace .local\\tmp\\trainer_evo_resume_trace.jsonl",
        ),
        "expected_signals": (
            "Crash-state inspection fails old broken states with invalid_script_state, such as a banked script pointer below $4000 or a bank outside the ROM.",
            "Forward replay passes only when reset_event_count is 0 and no invalid_script_state event appears.",
            "wScriptAfterPointer and wSeenTrainerBank remain sane until scripttalkafter consumes them.",
        ),
        "proof_limit": (
            "The .sgm inspection path diagnoses an already-corrupted state. A fix proof still requires a before-trigger PyBoy replay/watch report or an equivalent emulator-live reproduction."
        ),
    },
)


def build_repro_recipe_report(
    *,
    ids: tuple[str, ...] = (),
    symptom: str = "",
    root: Path = ROOT,
) -> dict[str, Any]:
    errors: list[str] = []
    selected: list[dict[str, Any]] = []
    if ids:
        by_id = {recipe["id"]: recipe for recipe in REPRO_RECIPES}
        for recipe_id in ids:
            recipe = by_id.get(recipe_id)
            if recipe is None:
                errors.append(f"unknown repro recipe: {recipe_id}")
                continue
            selected.append(public_recipe(recipe))
    elif symptom:
        text = symptom.lower()
        selected = [
            public_recipe(recipe)
            for recipe in REPRO_RECIPES
            if any(keyword_matches(keyword, text) for keyword in recipe.get("keywords", ()))
        ]
    else:
        selected = [public_recipe(recipe) for recipe in REPRO_RECIPES]

    return {
        "schema_version": 1,
        "kind": "unified_debugger_repro_recipe_report",
        "root": str(root),
        "requested_ids": list(ids),
        "symptom": symptom,
        "valid": not errors,
        "recipe_count": len(selected),
        "recipes": selected,
        "error_count": len(errors),
        "errors": errors,
        "commands": [
            f"python -m tools.debugger repro-recipe --id {recipe['id']}"
            for recipe in selected
        ],
    }


def public_recipe(recipe: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(recipe["id"]),
        "title": str(recipe["title"]),
        "bug_class": str(recipe["bug_class"]),
        "purpose": str(recipe["purpose"]),
        "inputs": list(recipe.get("inputs", ())),
        "setup_steps": list(recipe.get("setup_steps", ())),
        "commands": list(recipe.get("commands", ())),
        "expected_signals": list(recipe.get("expected_signals", ())),
        "proof_limit": str(recipe.get("proof_limit", "")),
    }
