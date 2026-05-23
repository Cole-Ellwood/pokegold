from __future__ import annotations

from pathlib import Path
from typing import Any

from .catalog import ROOT, keyword_matches, triage_request


NEXT_STEP_ROWS = [
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


def symptom_only_investigation_note(report: dict[str, Any]) -> str:
    symptom = str(report.get("symptom") or "").strip()
    if not symptom:
        return ""
    if _has_runtime_anchor(report):
        return ""
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
        row["matched_lane"] = str(matches[0].get("id") or row["matched_lane"])
    if symptom:
        row["first_command"] = f"python -m tools.debugger triage --symptom {symptom!r}"
        row["escalation_command"] = f"python -m tools.debugger investigate --symptom {symptom!r}"
    return row


def _public_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "symptom_class": row["symptom_class"],
        "matched_lane": row["matched_lane"],
        "title": row["title"],
        "first_command": row["first_command"],
        "required_inputs": list(row["required_inputs"]),
        "proof_limit": row["proof_limit"],
        "escalation_command": row["escalation_command"],
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
