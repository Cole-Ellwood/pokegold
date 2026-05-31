from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError

from .contribution_compare import (
    python_rule_id,
    rom_trace_id,
)
from .counterfactuals import (
    explain_counterfactuals,
    score_flip_for_action,
    smallest_score_flip,
)
from .decision_trace import choose_scenario, decision_trace_for_scenario
from .generators import generate_scenarios, write_jsonl
from .rom_contribution_trace import load_rom_contribution_trace
from .rom_scenarios import (
    BLOCKED_SCORE,
    adjusted_best_roll_threshold,
    evaluate_scenario,
    load_scenario_batch,
    normalize_tier,
    scenario_expectation,
    select_move,
    string_list,
)
from .rom_score_materialize import (
    DEFAULT_BASE_ROUTE as DEFAULT_SCORE_MATERIALIZE_ROUTE,
    DEFAULT_WATCH_FRAMES as DEFAULT_SCORE_MATERIALIZE_WATCH_FRAMES,
    SUPPORTED_FAMILIES as SCORE_MATERIALIZE_FAMILIES,
    run_rom_score_materialization,
)
from .rom_selector_materialize import (
    DEFAULT_BASE_ROUTE as DEFAULT_SELECTOR_MATERIALIZE_ROUTE,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_WATCH_FRAMES as DEFAULT_SELECTOR_MATERIALIZE_WATCH_FRAMES,
    run_rom_selector_materialization,
)
from .rom_switch_materialize import (
    AI_SWITCH_SACK_BIAS,
    AI_SWITCH_THRESHOLD_EARLY,
    AI_SWITCH_THRESHOLD_LATE,
    AI_SWITCH_THRESHOLD_MID,
    AI_SWITCH_WINCON_BIAS,
    DEFAULT_BASE_ROUTE as DEFAULT_SWITCH_MATERIALIZE_ROUTE,
    DEFAULT_WATCH_FRAMES as DEFAULT_SWITCH_MATERIALIZE_WATCH_FRAMES,
    SUPPORTED_FAMILIES as SWITCH_MATERIALIZE_FAMILIES,
    run_rom_switch_materialization,
    write_rom_switch_materialization_json,
)
from tools.headless_battle.simulator import (
    BOSS_AI_SWITCH_ROLL_HIGH_MARGIN,
    BOSS_AI_SWITCH_ROLL_MID_MARGIN,
    boss_ai_switch_roll_threshold,
)
from .rule_map import build_rule_map
from .trace_replay import (
    capture_id_for,
    load_move_names,
    parse_trace_file,
    replay_capture_fields,
    replay_trace_paths,
)


ROM_PROOF_CHOICES = ("none", "auto", "selector", "score", "switch")


def explain_decision_from_path(
    scenarios_path: Path,
    *,
    scenario_id: str | None = None,
    focus_action_id: str | None = None,
    rom_score_materialization_paths: list[Path] | None = None,
    rom_selector_materialization_paths: list[Path] | None = None,
    rom_switch_materialization_paths: list[Path] | None = None,
    rom_contribution_trace_paths: list[Path] | None = None,
    trace_paths: list[Path] | None = None,
    trace_capture_id: str | None = None,
    run_rom_proof: str = "none",
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    rom: Path = Path("pokegold_trace.gbc"),
    symbols_path: Path = Path("pokegold_trace.sym"),
    score_base_route: str = DEFAULT_SCORE_MATERIALIZE_ROUTE,
    selector_base_route: str = DEFAULT_SELECTOR_MATERIALIZE_ROUTE,
    switch_base_route: str = DEFAULT_SWITCH_MATERIALIZE_ROUTE,
    decision_input: dict[str, Any] | None = None,
    limit: int = 12,
) -> dict[str, Any]:
    scenarios = load_scenario_batch(scenarios_path)
    scenario = choose_scenario(scenarios, scenario_id)
    scenario_key = str(scenario.get("id") or scenario.get("scenario_id") or "unnamed")
    selected_id = str(scenario_id or scenario_key)
    selector = select_move(scenario)
    verdict = evaluate_scenario(scenario)
    decision_trace = decision_trace_for_scenario(scenario)
    counterfactual = explain_counterfactuals(scenario)
    if focus_action_id:
        counterfactual["focus_score_flip"] = focus_score_flip(
            selector,
            focus_action_id,
            scenario=scenario,
        )

    rule_index = build_rule_index()
    auto_rom_proof: list[dict[str, Any]] = []
    proof_blockers: list[dict[str, Any]] = []
    try:
        run_reports = run_requested_rom_proof(
            scenario,
            run_rom_proof=run_rom_proof,
            manifest_path=manifest_path,
            rom=rom,
            symbols_path=symbols_path,
            score_base_route=score_base_route,
            selector_base_route=selector_base_route,
            switch_base_route=switch_base_route,
        )
    except PreferenceDataError as exc:
        if not live_rom_proof_error_is_hash_basis(str(exc)):
            raise
        proof_kind = auto_rom_proof_kind(scenario) if run_rom_proof == "auto" else run_rom_proof
        attempt = live_rom_proof_attempt(
            proof_kind=proof_kind,
            status="blocked_by_hash_basis",
            reason=str(exc),
            base_route=(
                switch_base_route
                if proof_kind == "switch"
                else score_base_route if proof_kind == "score" else selector_base_route
            ),
        )
        auto_rom_proof.append(attempt)
        proof_blockers.append(attempt)
        run_reports = {"score": [], "selector": [], "switch": []}
    score_reports = [
        *run_reports["score"],
        *load_json_reports(rom_score_materialization_paths or []),
    ]
    selector_reports = [
        *run_reports["selector"],
        *load_json_reports(rom_selector_materialization_paths or []),
    ]
    switch_reports = [
        *run_reports["switch"],
        *load_json_reports(rom_switch_materialization_paths or []),
    ]

    trace_replay = replay_trace_artifacts(trace_paths or [], trace_capture_id)
    rom_contribution_reports = collect_rom_contribution_reports(
        rom_contribution_trace_paths or [],
        score_reports=score_reports,
    )
    rom_contributions = explain_rom_contributions(
        rom_contribution_reports,
        selected_id,
        scenario_key,
        rule_index,
        limit=limit,
    )
    python_candidates = candidate_packet(selector, rule_index, scenario=scenario)
    rom_evidence = collect_rom_evidence(
        selected_id,
        scenario_key,
        scenario=scenario,
        score_reports=score_reports,
        selector_reports=selector_reports,
        switch_reports=switch_reports,
        trace_replay=trace_replay,
    )
    primary_rom = primary_rom_evidence(rom_evidence, scenario)

    source_anchors = source_anchor_packet(
        rule_index,
        python_candidates=python_candidates,
        rom_contributions=rom_contributions,
        extra_rule_ids=static_rule_ids_for_scenario(scenario),
    )
    public_inputs = public_input_packet(
        scenario,
        verdict,
        rom_contribution_reports,
        selected_id,
        scenario_key,
        rule_index,
        limit=limit,
    )
    next_commands = next_proof_commands(
        scenarios_path,
        selected_id,
        scenario,
        focus_action_id=focus_action_id,
        has_rom_evidence=bool(primary_rom.get("available")),
        has_rom_contributions=bool(rom_contributions["events"]),
        existing_rom_contribution_paths=rom_contribution_trace_paths or [],
    )

    return finalize_explanation_report(
        {
        "schema_version": 1,
        "source": {
            "scenario_path": str(scenarios_path),
            "scenario_id": selected_id,
        },
        "decision_input": decision_input or {},
        "scenario_id": str(verdict.scenario_id),
        "family": str(scenario.get("family", "")),
        "tier": selector.get("tier"),
        "question": question_packet(
            scenario,
            verdict,
            selector,
            focus_action_id=focus_action_id,
        ),
        "observed_rom_decision": primary_rom,
        "rom_evidence": rom_evidence,
        "auto_rom_proof": auto_rom_proof,
        "proof_blockers": proof_blockers,
        "python_mirror": python_mirror_packet(selector, verdict, primary_rom),
        "candidate_scores": python_candidates,
        "rom_contributions": rom_contributions,
        "public_info_inputs": public_inputs,
        "source_anchors": source_anchors,
        "counterfactual": counterfactual_packet(counterfactual),
        "decision_trace_summary": decision_trace_summary(decision_trace),
        "next_proof_commands": next_commands,
        "known_limits": known_limits(primary_rom, rom_contributions),
        }
    )


def question_packet(
    scenario: dict[str, Any],
    verdict: Any,
    selector: dict[str, Any],
    *,
    focus_action_id: str | None,
) -> dict[str, Any]:
    expectation = scenario_expectation(scenario)
    return {
        "focus_action_id": focus_action_id or "",
        "rom_best_action_id": selector.get("best_action_id"),
        "expected_best_action_ids": verdict.expected_best_action_ids,
        "expected_acceptable_action_ids": verdict.expected_acceptable_action_ids,
        "expected_bad_action_ids": string_list(expectation.get("bad_action_ids")),
        "expected_catastrophic_action_ids": string_list(
            expectation.get("catastrophic_action_ids")
        ),
        "rolled_bad_action_ids": verdict.rolled_bad_action_ids,
        "rolled_catastrophic_action_ids": verdict.rolled_catastrophic_action_ids,
        "zero_probability_best_action_ids": verdict.zero_probability_best_action_ids,
        "policy_verdict": verdict.verdict,
        "policy_reason": verdict.reason,
        "policy_why": verdict.why,
        "lesson_type": verdict.lesson_type,
        "confidence": verdict.confidence,
        "evidence_refs": verdict.evidence_refs,
    }


def explain_decision_from_trace_paths(
    trace_paths: list[Path],
    *,
    trace_capture_id: str | None = None,
    focus_action_id: str | None = None,
    rom_contribution_trace_paths: list[Path] | None = None,
    decision_input: dict[str, Any] | None = None,
    run_rom_proof: str = "none",
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    rom: Path = Path("pokegold_trace.gbc"),
    symbols_path: Path = Path("pokegold_trace.sym"),
    switch_base_route: str = DEFAULT_SWITCH_MATERIALIZE_ROUTE,
    auto_artifact_dir: Path = Path(".local") / "tmp" / "boss_ai_debugger",
    limit: int = 12,
) -> dict[str, Any]:
    capture = choose_trace_capture(trace_paths, trace_capture_id)
    rule_index = build_rule_index()
    selected_id = str(capture["capture_id"])
    trace_key = trace_scenario_key(capture)
    rom_contribution_reports = collect_rom_contribution_reports(
        rom_contribution_trace_paths or [],
        score_reports=[],
    )
    rom_contributions = explain_rom_contributions(
        rom_contribution_reports,
        selected_id,
        trace_key,
        rule_index,
        limit=limit,
    )
    primary_rom = live_trace_primary_rom_evidence(capture)
    live_run_reports = run_requested_live_rom_proof(
        capture,
        run_rom_proof=run_rom_proof,
        manifest_path=manifest_path,
        rom=rom,
        symbols_path=symbols_path,
        switch_base_route=switch_base_route,
        auto_artifact_dir=auto_artifact_dir,
    )
    candidates = live_trace_candidate_packet(capture)
    public_inputs = live_trace_public_input_packet(
        capture,
        rom_contribution_reports,
        selected_id,
        trace_key,
        rule_index,
        limit=limit,
    )
    source_anchors = source_anchor_packet(
        rule_index,
        python_candidates=candidates,
        rom_contributions=rom_contributions,
        extra_rule_ids=live_trace_static_rule_ids(capture),
    )
    counterfactual = live_trace_counterfactual_packet(capture, focus_action_id)
    next_commands = next_trace_proof_commands(
        capture,
        focus_action_id=focus_action_id,
        has_rom_contributions=bool(rom_contributions["events"]),
        existing_rom_contribution_paths=rom_contribution_trace_paths or [],
        decision_input=decision_input,
    )

    return finalize_explanation_report(
        {
        "schema_version": 1,
        "source": {
            "trace_path": capture["path"],
            "capture_id": selected_id,
        },
        "decision_input": decision_input or {},
        "scenario_id": selected_id,
        "family": "live_trace",
        "tier": capture["selector"].get("tier"),
        "question": {
            "focus_action_id": focus_action_id or "",
            "rom_best_action_id": live_trace_best_action_id(capture),
            "expected_best_action_ids": [],
            "expected_acceptable_action_ids": [],
        },
        "observed_rom_decision": primary_rom,
        "rom_evidence": [primary_rom, *live_run_reports["switch"]],
        "auto_rom_proof": live_run_reports["attempts"],
        "proof_blockers": live_run_reports["blockers"],
        "python_mirror": live_trace_python_mirror_packet(capture),
        "candidate_scores": candidates,
        "rom_contributions": rom_contributions,
        "public_info_inputs": public_inputs,
        "source_anchors": source_anchors,
        "counterfactual": counterfactual,
        "decision_trace_summary": {
            "event_count": 0,
            "event_type_counts": {},
            "source": "live_trace_selector_replay",
        },
        "next_proof_commands": next_commands,
        "known_limits": live_trace_known_limits(primary_rom, rom_contributions),
        }
    )


def choose_trace_capture(
    trace_paths: list[Path],
    trace_capture_id: str | None,
) -> dict[str, Any]:
    if not trace_paths:
        raise PreferenceDataError("provide --scenario or at least one --trace")
    move_names = load_move_names()
    captures = []
    for path in trace_paths:
        if not path.exists():
            raise PreferenceDataError(f"missing trace file: {path}")
        for index, fields in enumerate(parse_trace_file(path), start=1):
            capture_id = capture_id_for(path, fields, index)
            if trace_capture_id and capture_id != trace_capture_id:
                continue
            verdict = replay_capture_fields(fields, capture_id, path, move_names)
            captures.append(
                {
                    "capture_id": capture_id,
                    "path": str(path),
                    "fields": fields,
                    "verdict": {
                        "capture_id": verdict.capture_id,
                        "path": verdict.path,
                        "mode": verdict.mode,
                        "verdict": verdict.verdict,
                        "match": verdict.match,
                        "reason": verdict.reason,
                        "chosen_id": verdict.chosen_id,
                        "expected_move_ids": verdict.expected_move_ids,
                    },
                    "selector": verdict.selector,
                }
            )
    if not captures:
        if trace_capture_id:
            raise PreferenceDataError(f"trace capture id {trace_capture_id!r} not found")
        raise PreferenceDataError("no captures found in trace file(s)")
    if len(captures) > 1 and trace_capture_id is None:
        # Live trace files normally contain one capture, but multi-capture files
        # need an explicit id so the explanation packet has one decision owner.
        ids = ", ".join(item["capture_id"] for item in captures)
        raise PreferenceDataError(f"multiple trace captures found; pass --capture-id ({ids})")
    return captures[0]


def trace_scenario_key(capture: dict[str, Any]) -> str:
    fields = capture.get("fields", {})
    boss = str(fields.get("boss", "")).strip()
    if boss:
        return boss.lower().replace(" ", "_").replace(".", "")
    return str(capture.get("capture_id", ""))


def live_trace_primary_rom_evidence(capture: dict[str, Any]) -> dict[str, Any]:
    fields = capture.get("fields", {})
    selector = capture.get("selector", {})
    chosen_id = int(capture.get("verdict", {}).get("chosen_id", 0))
    chosen_slot = optional_trace_int(fields.get("chosen_slot"))
    chosen_slot_entry = slot_for_index(selector, chosen_slot)
    selector_path = live_trace_selector_path(capture)
    return {
        "available": True,
        "kind": "live_trace_selector_replay",
        "artifact": capture.get("path", ""),
        "status": capture.get("verdict", {}).get("verdict", "unknown"),
        "capture_id": capture.get("capture_id", ""),
        "decision": {
            "chosen_id": chosen_id,
            "chosen_move_name": fields.get("chosen", chosen_slot_entry.get("name", "")),
            "chosen_slot": chosen_slot,
            "chosen_slot_index": chosen_slot,
            "chosen_slot_1_based": live_trace_human_slot(
                chosen_slot_entry,
                chosen_slot,
            ),
            "chosen_score": chosen_slot_entry.get("score"),
            "expected_move_ids": capture.get("verdict", {}).get("expected_move_ids", []),
            "possible_action_ids": selector_path.get("possible_action_ids", []),
            "possible_move_ids": selector_path.get("possible_move_ids", []),
            "move_ids": trace_int_list(fields.get("move_ids", "")),
            "move_scores": trace_int_list(fields.get("move_scores", "")),
            "pre_model_scores": trace_int_list(fields.get("pre_model_scores", "")),
            "post_model_scores": trace_int_list(fields.get("post_model_scores", "")),
            "model_score_deltas": trace_signed_int_list(fields.get("model_score_deltas", "")),
            "selector": selector,
            "selector_path": selector_path,
            "switch_confidence": optional_trace_int(fields.get("switch_confidence")),
            "switch_context": fields.get("switch_context", ""),
            "switch_path": live_trace_switch_path(capture),
        },
        "python_agreement": {
            "agreement": bool(capture.get("verdict", {}).get("match", False)),
            "reason": capture.get("verdict", {}).get("reason", ""),
            "mirror_scope": "BossAI_SelectMove replay from captured ROM score bytes",
        },
        "reason": capture.get("verdict", {}).get("reason", ""),
    }


def live_trace_candidate_packet(capture: dict[str, Any]) -> list[dict[str, Any]]:
    selector = capture.get("selector", {})
    probabilities = selector.get("probabilities_by_slot", {})
    model_deltas = trace_signed_int_list(
        capture.get("fields", {}).get("model_score_deltas", "")
    )
    pre_scores = trace_int_list(capture.get("fields", {}).get("pre_model_scores", ""))
    post_scores = trace_int_list(capture.get("fields", {}).get("post_model_scores", ""))
    candidates = []
    for slot in selector.get("slots", []):
        slot_index = int(slot.get("slot_index", -1))
        action_id = live_trace_action_id(slot)
        candidates.append(
            {
                "slot": slot.get("slot"),
                "slot_index": slot_index,
                "action_id": action_id,
                "name": slot.get("name", action_id),
                "move_id": slot.get("move_id"),
                "initial_score": pre_scores[slot_index] if 0 <= slot_index < len(pre_scores) else None,
                "pre_lookahead_score": post_scores[slot_index] if 0 <= slot_index < len(post_scores) else None,
                "final_score": slot.get("score"),
                "blocked": bool(slot.get("blocked", False)),
                "selector_probability": float(probabilities.get(slot_index, 0.0)),
                "contributions": live_trace_score_contributions(
                    slot,
                    model_deltas=model_deltas,
                    pre_scores=pre_scores,
                    post_scores=post_scores,
                ),
            }
        )
    return candidates


def live_trace_human_slot(slot: dict[str, Any], slot_index: Any) -> int | None:
    raw_slot = optional_trace_int(slot.get("slot")) if slot else None
    if raw_slot is not None:
        return raw_slot
    raw_index = optional_trace_int(slot_index)
    return raw_index + 1 if raw_index is not None else None


def live_trace_score_contributions(
    slot: dict[str, Any],
    *,
    model_deltas: list[int],
    pre_scores: list[int],
    post_scores: list[int],
) -> list[dict[str, Any]]:
    slot_index = int(slot.get("slot_index", -1))
    if not 0 <= slot_index < len(model_deltas):
        return []
    delta = model_deltas[slot_index]
    before = pre_scores[slot_index] if slot_index < len(pre_scores) else None
    after = post_scores[slot_index] if slot_index < len(post_scores) else slot.get("score")
    return [
        {
            "rule": "captured_model_score_delta",
            "rule_id": "live_trace.model_score_delta",
            "before": before,
            "delta": delta,
            "after": after,
            "note": "Captured pre/post model score byte delta from live trace.",
            "source_anchor": None,
        }
    ]


def live_trace_selector_path(capture: dict[str, Any]) -> dict[str, Any]:
    selector = capture.get("selector", {})
    fields = capture.get("fields", {})
    verdict = capture.get("verdict", {})
    if not selector.get("ready"):
        return {
            "available": False,
            "reason": selector.get("reason", "exact score-byte selector fields unavailable"),
            "agreement": bool(verdict.get("match", False)),
            "agreement_reason": verdict.get("reason", ""),
        }
    chosen_id = optional_trace_int(fields.get("chosen_id")) or int(verdict.get("chosen_id", 0))
    chosen_slot_index = optional_trace_int(fields.get("chosen_slot"))
    chosen_slot = slot_for_index(selector, chosen_slot_index)
    if not chosen_slot and chosen_id:
        chosen_slot = slot_for_move_id(selector, chosen_id)
    best = slot_for_index(selector, selector.get("best_slot_index"))
    second = slot_for_index(selector, selector.get("second_slot_index"))
    probabilities = live_trace_probabilities_by_action(selector)
    possible_action_ids = [
        live_trace_action_id(slot_for_index(selector, slot_index))
        for slot_index in selector.get("possible_slot_indices", [])
        if slot_for_index(selector, slot_index)
    ]
    chosen_action_id = live_trace_action_id(chosen_slot) if chosen_slot else ""
    return {
        "available": True,
        "source": "BossAI_SelectMove replay from captured wEnemyAIMoveScores",
        "best_action_id": live_trace_action_id(best) if best else None,
        "best_slot_index": selector.get("best_slot_index"),
        "best_move_id": selector.get("best_move_id"),
        "best_score": selector.get("best_score"),
        "second_action_id": live_trace_action_id(second) if second else None,
        "second_slot_index": selector.get("second_slot_index"),
        "second_move_id": selector.get("second_move_id"),
        "second_score": selector.get("second_score"),
        "score_gap": selector.get("gap"),
        "best_roll_threshold": selector.get("best_roll_threshold"),
        "possible_action_ids": possible_action_ids,
        "possible_move_ids": selector.get("possible_move_ids", []),
        "candidate_probabilities": probabilities,
        "chosen_action_id": chosen_action_id,
        "chosen_slot_index": chosen_slot.get("slot_index") if chosen_slot else chosen_slot_index,
        "chosen_move_id": chosen_id,
        "chosen_probability": float(probabilities.get(chosen_action_id, 0.0)),
        "chosen_has_nonzero_probability": float(probabilities.get(chosen_action_id, 0.0)) > 0.0,
        "agreement": bool(verdict.get("match", False)),
        "agreement_reason": verdict.get("reason", ""),
    }


def live_trace_probabilities_by_action(selector: dict[str, Any]) -> dict[str, float]:
    probabilities = selector.get("probabilities_by_slot", {})
    result: dict[str, float] = {}
    for slot in selector.get("slots", []):
        slot_index = int(slot.get("slot_index", -1))
        result[live_trace_action_id(slot)] = float(probabilities.get(slot_index, 0.0))
    return result


def materialized_selector_path(
    scenario: dict[str, Any],
    *,
    scores: list[Any],
    probabilities: dict[str, Any] | None = None,
    chosen_action_id: Any = None,
    chosen_move_id: Any = None,
    chosen_slot_index: Any = None,
    tier: Any = None,
    source: str,
) -> dict[str, Any]:
    candidates = materialized_selector_candidates(scenario, scores)
    if not candidates:
        return {
            "available": False,
            "source": source,
            "reason": "materialization did not include candidate score bytes",
        }
    legal = [item for item in candidates if int(item["score"]) < BLOCKED_SCORE]
    if not legal:
        return {
            "available": False,
            "source": source,
            "reason": "no selectable materialized score below 80",
            "candidates": candidates,
        }
    best = min(legal, key=lambda item: (int(item["score"]), int(item["slot_index"])))
    second_candidates = [
        item for item in legal if int(item["slot_index"]) != int(best["slot_index"])
    ]
    second = (
        min(
            second_candidates,
            key=lambda item: (int(item["score"]), int(item["slot_index"])),
        )
        if second_candidates
        else None
    )
    tier_value = materialized_selector_tier(scenario, tier)
    score_gap = int(second["score"]) - int(best["score"]) if second else None
    threshold = (
        adjusted_best_roll_threshold(tier_value, score_gap)
        if second and tier_value
        else None
    )
    computed_probabilities = materialized_probabilities(
        candidates,
        best=best,
        second=second,
        threshold=threshold,
    )
    provided_probabilities = normalize_probability_map(probabilities or {})
    candidate_probabilities = {
        action_id: float(provided_probabilities.get(action_id, probability))
        for action_id, probability in computed_probabilities.items()
    }
    chosen_id = str(chosen_action_id or "")
    if not chosen_id:
        chosen_id = materialized_chosen_action_id(
            candidates,
            chosen_slot_index=chosen_slot_index,
            chosen_move_id=chosen_move_id,
        )
    return {
        "available": True,
        "source": source,
        "best_action_id": best["action_id"],
        "best_slot_index": best["slot_index"],
        "best_move_id": best.get("move_id"),
        "best_score": best["score"],
        "second_action_id": second["action_id"] if second else None,
        "second_slot_index": second["slot_index"] if second else None,
        "second_move_id": second.get("move_id") if second else None,
        "second_score": second["score"] if second else None,
        "score_gap": score_gap,
        "best_roll_threshold": threshold,
        "possible_action_ids": [
            action_id
            for action_id, probability in candidate_probabilities.items()
            if probability > 0.0
        ],
        "candidate_probabilities": candidate_probabilities,
        "chosen_action_id": chosen_id,
        "chosen_move_id": optional_trace_int(chosen_move_id),
        "chosen_slot_index": optional_trace_int(chosen_slot_index),
        "chosen_probability": float(candidate_probabilities.get(chosen_id, 0.0)),
        "chosen_has_nonzero_probability": (
            bool(chosen_id) and float(candidate_probabilities.get(chosen_id, 0.0)) > 0.0
        ),
        "candidates": candidates,
    }


def materialized_selector_candidates(
    scenario: dict[str, Any],
    scores: list[Any],
) -> list[dict[str, Any]]:
    moves = [item for item in scenario.get("moves", []) if isinstance(item, dict)]
    candidates = []
    for slot_index, move in enumerate(moves[:4]):
        if slot_index >= len(scores):
            break
        score = optional_trace_int(scores[slot_index])
        if score is None:
            continue
        action_id = str(move.get("id") or move.get("action_id") or f"slot{slot_index + 1}")
        candidates.append(
            {
                "slot": slot_index + 1,
                "slot_index": slot_index,
                "action_id": action_id,
                "name": str(move.get("name") or action_id),
                "move_id": optional_trace_int(move.get("move_id")),
                "score": score,
                "blocked": score >= BLOCKED_SCORE,
            }
        )
    return candidates


def materialized_selector_tier(scenario: dict[str, Any], tier: Any) -> int:
    raw = tier if tier not in {None, ""} else scenario.get("tier", "late")
    try:
        return int(normalize_tier(raw))
    except PreferenceDataError:
        return 0


def materialized_probabilities(
    candidates: list[dict[str, Any]],
    *,
    best: dict[str, Any],
    second: dict[str, Any] | None,
    threshold: int | None,
) -> dict[str, float]:
    probabilities = {str(item["action_id"]): 0.0 for item in candidates}
    if second is None:
        probabilities[str(best["action_id"])] = 1.0
    elif threshold is not None:
        probabilities[str(best["action_id"])] = threshold / 256
        probabilities[str(second["action_id"])] = 1 - probabilities[str(best["action_id"])]
    return probabilities


def normalize_probability_map(probabilities: dict[str, Any]) -> dict[str, float]:
    normalized: dict[str, float] = {}
    for action_id, probability in probabilities.items():
        try:
            normalized[str(action_id)] = float(probability)
        except (TypeError, ValueError):
            continue
    return normalized


def materialized_chosen_action_id(
    candidates: list[dict[str, Any]],
    *,
    chosen_slot_index: Any,
    chosen_move_id: Any,
) -> str:
    slot_index = optional_trace_int(chosen_slot_index)
    if slot_index is not None:
        for candidate in candidates:
            if int(candidate["slot_index"]) == slot_index:
                return str(candidate["action_id"])
    move_id = optional_trace_int(chosen_move_id)
    if move_id is not None:
        for candidate in candidates:
            if candidate.get("move_id") == move_id:
                return str(candidate["action_id"])
    return ""


def live_trace_python_mirror_packet(capture: dict[str, Any]) -> dict[str, Any]:
    selector = capture.get("selector", {})
    verdict = capture.get("verdict", {})
    best = slot_for_index(selector, selector.get("best_slot_index"))
    second = slot_for_index(selector, selector.get("second_slot_index"))
    return {
        "available": True,
        "mirror_scope": "selector_from_rom_score_bytes",
        "best_action_id": live_trace_action_id(best) if best else None,
        "second_action_id": live_trace_action_id(second) if second else None,
        "best_score": selector.get("best_score"),
        "second_score": selector.get("second_score"),
        "gap": selector.get("gap"),
        "best_roll_threshold": selector.get("best_roll_threshold"),
        "probabilities": {
            live_trace_action_id(slot): float(
                selector.get("probabilities_by_slot", {}).get(
                    int(slot.get("slot_index", -1)),
                    0.0,
                )
            )
            for slot in selector.get("slots", [])
        },
        "policy_verdict": "not_applicable_without_scenario_expectation",
        "policy_reason": "live trace input has no generated scenario expectation",
        "rom_comparison": {
            "agreement": bool(verdict.get("match", False)),
            "reason": verdict.get("reason", ""),
        },
    }


def live_trace_counterfactual_packet(
    capture: dict[str, Any],
    focus_action_id: str | None,
) -> dict[str, Any]:
    selector = capture.get("selector", {})
    all_flips = live_trace_score_flips(selector, include_best=True)
    flips = live_trace_score_flips(selector, include_best=False) or all_flips
    focus_flip = None
    if focus_action_id:
        focus_flip = next(
            (
                item
                for item in all_flips
                if focus_action_matches(item, focus_action_id)
            ),
            {
                "action_id": focus_action_id,
                "available": False,
                "reason": "focus action is not present in captured live trace slots",
            },
        )
    return {
        "smallest_score_flip": smallest_score_flip(flips),
        "focus_score_flip": focus_flip,
        "public_fact_counterfactuals": [
            "Attach a ROM contribution trace for this route to identify which public branch or score rule would move the score bytes.",
        ],
        "answer_changing_information": [],
        "why": "Live trace counterfactuals are computed from captured final score bytes.",
    }


def live_trace_score_flips(
    selector: dict[str, Any],
    *,
    include_best: bool,
) -> list[dict[str, Any]]:
    best_score = int(selector.get("best_score", BLOCKED_SCORE)) if selector.get("ready") else BLOCKED_SCORE
    best_slot_index = int(selector.get("best_slot_index", 99))
    best_slot = best_slot_index + 1
    score_by_action: dict[str, int] = {}
    slot_by_action: dict[str, int] = {}
    for slot in selector.get("slots", []):
        if not include_best and int(slot.get("slot_index", -1)) == best_slot_index:
            continue
        action_id = live_trace_action_id(slot)
        score_by_action[action_id] = int(slot.get("score", BLOCKED_SCORE))
        slot_by_action[action_id] = int(slot.get("slot", 99))
    return [
        {
            **score_flip_for_action(
                action_id,
                score_by_action,
                slot_by_action,
                best_score=best_score,
                best_slot=best_slot,
            ),
            "move_id": slot.get("move_id"),
            "name": slot.get("name", ""),
            "slot": slot.get("slot"),
            "slot_index": slot.get("slot_index"),
        }
        for slot in selector.get("slots", [])
        for action_id in [live_trace_action_id(slot)]
        if action_id in score_by_action
    ]


def focus_action_matches(flip: dict[str, Any], focus_action_id: str) -> bool:
    focus = focus_action_id.strip().lower()
    return focus in {
        str(flip.get("action_id", "")).lower(),
        str(flip.get("name", "")).lower(),
        str(flip.get("move_id", "")).lower(),
        str(flip.get("slot", "")).lower(),
        f"slot{flip.get('slot')}".lower(),
    }


def live_trace_public_input_packet(
    capture: dict[str, Any],
    reports: list[dict[str, Any]],
    selected_id: str,
    trace_key: str,
    rule_index: dict[str, dict[str, Any]],
    *,
    limit: int,
) -> dict[str, Any]:
    fields = capture.get("fields", {})
    contribution_public = public_input_packet_from_reports(
        reports,
        selected_id,
        trace_key,
        rule_index,
        limit=limit,
    )
    return {
        "policy_tags": [],
        "condition_tags": [],
        "answer_changing_information": [],
        "evidence_refs": [capture.get("path", "")],
        "scenario_public_keys": [],
        "trace_fields": {
            key: fields.get(key, "")
            for key in (
                "boss",
                "notes",
                "tier",
                "plan_id",
                "plan_phase",
                "plan_confidence",
                "risk_flags",
                "plausible_mask",
                "switch_confidence",
                "switch_context",
                "revealed_masks",
            )
            if key in fields
        },
        **contribution_public,
    }


def public_input_packet_from_reports(
    reports: list[dict[str, Any]],
    selected_id: str,
    scenario_key: str,
    rule_index: dict[str, dict[str, Any]],
    *,
    limit: int,
) -> dict[str, Any]:
    empty_verdict = type(
        "TraceVerdict",
        (),
        {
            "policy_tags": [],
            "condition_tags": [],
            "answer_changing_information": [],
            "evidence_refs": [],
        },
    )()
    packet = public_input_packet(
        {},
        empty_verdict,
        reports,
        selected_id,
        scenario_key,
        rule_index,
        limit=limit,
    )
    return {
        "rom_public_reads_by_rule": packet["rom_public_reads_by_rule"],
        "predicate_branches": packet["predicate_branches"],
        "public_read_probes": packet["public_read_probes"],
    }


def proof_command(
    *,
    purpose: str,
    command: str,
    closes_evidence_ids: list[str] | tuple[str, ...] = (),
    expected_output_paths: list[Path | str] | tuple[Path | str, ...] = (),
    consumes_artifact_paths: list[Path | str] | tuple[Path | str, ...] = (),
) -> dict[str, Any]:
    return {
        "purpose": purpose,
        "command": command,
        "closes_evidence_ids": [str(item) for item in closes_evidence_ids],
        "expected_output_paths": [str(path) for path in expected_output_paths],
        "consumes_artifact_paths": [str(path) for path in consumes_artifact_paths],
    }


def next_trace_proof_commands(
    capture: dict[str, Any],
    *,
    focus_action_id: str | None,
    has_rom_contributions: bool,
    existing_rom_contribution_paths: list[Path],
    decision_input: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    path = quote_cli(capture.get("path", ""))
    capture_id = str(capture.get("capture_id", ""))
    boss_route = route_id_for_trace_capture(capture)
    switch_path = live_trace_switch_path(capture)
    focus_args = (
        f" --focus-action-id {quote_cli(focus_action_id)}"
        if focus_action_id
        else ""
    )
    focus_segment = f"{focus_args.strip()} " if focus_args else ""
    rerender_target = live_trace_rerender_target_args(
        capture,
        decision_input=decision_input,
    )
    commands = [
        proof_command(
            purpose="Replay captured ROM selector bytes",
            command=(
                "python -m tools.boss_ai_debugger trace-replay "
                f"--trace {path}"
            ),
            closes_evidence_ids=[
                "observed_rom_decision",
                "score_bytes",
                "selector_path",
            ],
        )
    ]
    if not has_rom_contributions:
        contribution_path = temp_artifact_name(capture_id, "rom_contribution")
        commands.append(
            proof_command(
                purpose="Capture ROM score-rule contribution deltas for this route",
                command=(
                    "python -m tools.boss_ai_debugger rom-contribution-trace "
                    f"--boss-route {boss_route} "
                    f"--json-out {quote_cli(contribution_path)}"
                ),
                closes_evidence_ids=[
                    "rom_contribution_deltas",
                    "rom_public_read_provenance",
                ],
                expected_output_paths=[contribution_path],
            )
        )
        commands.append(
            proof_command(
                purpose="Re-render this live-trace packet after contribution capture",
                command=(
                    "python -m tools.boss_ai_debugger explain-decision "
                    f"{rerender_target}"
                    f"{focus_args} "
                    f"--rom-contribution-trace {quote_cli(contribution_path)}"
                ),
                closes_evidence_ids=[
                    "rom_contribution_deltas",
                    "rom_public_read_provenance",
                ],
                consumes_artifact_paths=[contribution_path],
            )
        )
    if existing_rom_contribution_paths:
        trace_args = " ".join(
            f"--rom-contribution-trace {quote_cli(path)}"
            for path in existing_rom_contribution_paths
        )
        commands.append(
            proof_command(
                purpose="Re-render this live-trace packet with attached rule deltas",
                command=(
                    "python -m tools.boss_ai_debugger explain-decision "
                    f"{rerender_target}"
                    f"{focus_args} {trace_args}"
                ),
                closes_evidence_ids=[
                    "rom_contribution_deltas",
                    "rom_public_read_provenance",
                ],
                consumes_artifact_paths=existing_rom_contribution_paths,
            )
        )
    if switch_path.get("observed"):
        scenarios = temp_artifact_name(capture_id, "switch_sack_probe").replace(".json", ".jsonl")
        switch_out = temp_artifact_name(capture_id, "rom_switch")
        commands.extend(
            [
                proof_command(
                    purpose="Generate switch/sack probes for ROM switch-dispatch materialization",
                    command=(
                        "python -m tools.boss_ai_debugger generate "
                        f"--family switch_sack --count 12 --seed 1 --out {quote_cli(scenarios)}"
                    ),
                    expected_output_paths=[scenarios],
                ),
                proof_command(
                    purpose="Materialize switch-dispatch proof against the shared switch route",
                    command=(
                        "python -m tools.boss_ai_debugger rom-switch-materialize "
                        f"--scenarios {quote_cli(scenarios)} --base-route {boss_route} "
                        f"--limit 12 --json-out {quote_cli(switch_out)}"
                    ),
                    closes_evidence_ids=[
                        "observed_rom_decision",
                        "switch_path",
                        "switch_materialization",
                    ],
                    expected_output_paths=[switch_out],
                    consumes_artifact_paths=[scenarios],
                ),
                proof_command(
                    purpose="Render switch-dispatch explanation packet after materialization",
                    command=(
                        "python -m tools.boss_ai_debugger explain-decision "
                        f"--scenario {quote_cli(scenarios)} "
                        f"--rom-switch-materialization {quote_cli(switch_out)}"
                    ),
                    closes_evidence_ids=[
                        "observed_rom_decision",
                        "switch_path",
                        "switch_materialization",
                    ],
                    consumes_artifact_paths=[scenarios, switch_out],
                ),
            ]
        )
    commands.append(
        proof_command(
            purpose="Verify source-rule anchors are current",
            command="python -m tools.boss_ai_debugger rule-map check",
            closes_evidence_ids=["source_anchors"],
        )
    )
    return commands


def live_trace_rerender_target_args(
    capture: dict[str, Any],
    *,
    decision_input: dict[str, Any] | None,
) -> str:
    manifest = decision_input or {}
    target = manifest.get("target", {}) if isinstance(manifest, dict) else {}
    resolution = manifest.get("resolution", {}) if isinstance(manifest, dict) else {}
    if target.get("boss_route"):
        parts = [
            f"--boss-route {quote_cli(str(target['boss_route']))}",
        ]
        if target.get("decision_index"):
            parts.append(f"--decision-index {target['decision_index']}")
        if target.get("decision_surface"):
            parts.append(f"--decision-surface {quote_cli(str(target['decision_surface']))}")
        artifact = manifest.get("artifact_path")
        if artifact:
            parts.append(f"--decision-input-manifest-out {quote_cli(str(artifact))}")
        return " ".join(parts)
    path = quote_cli(capture.get("path", ""))
    capture_id = str(capture.get("capture_id") or resolution.get("trace_capture_id") or "")
    return f"--trace {path} --capture-id {quote_cli(capture_id)}"


def live_trace_known_limits(
    primary_rom: dict[str, Any],
    rom_contributions: dict[str, Any],
) -> list[str]:
    limits = [
        "Live trace input proves selector behavior from captured ROM score bytes, not full score-model reconstruction.",
        "Counterfactual score flips are byte-level selector flips until a ROM contribution trace is attached.",
    ]
    if not rom_contributions.get("events"):
        limits.append("Attach or run rom-contribution-trace to get rule-level score deltas and public-read snapshots.")
    if rom_contributions.get("unmatched_trace_ids"):
        limits.append("Some ROM contribution traces were loaded but did not match this capture id or route.")
    if not primary_rom.get("python_agreement", {}).get("agreement", False):
        limits.append("Selector replay does not agree with the captured choice; inspect trace fields before drawing policy conclusions.")
    switch_path = primary_rom.get("decision", {}).get("switch_path", {})
    if switch_path.get("observed"):
        limits.append("Live trace switch fields prove observed dispatch bytes; use rom-switch-materialize for scenario-level switch policy proof.")
    return limits


def live_trace_switch_path(capture: dict[str, Any]) -> dict[str, Any]:
    fields = capture.get("fields", {})
    confidence = optional_trace_int(fields.get("switch_confidence")) or 0
    context = parse_switch_context(fields.get("switch_context", ""))
    param = int(context.get("param", 0))
    index = int(context.get("index", 0))
    observed = confidence != 0 or param != 0 or index != 0
    return {
        "observed": observed,
        "switch_confidence": confidence,
        "switch_context": context,
        "switch_param": param,
        "proposed_switch": param != 0,
        "proposed_target_1_based": (param & 0x0F) + 1 if param else 0,
        "switch_index": index,
        "actual_switch": index != 0,
        "last_switched_out": int(context.get("last_out", 0)),
        "cooldown": int(context.get("cooldown", 0)),
        "cur_ot": int(context.get("cur_ot", 0)),
        "observation_status": switch_observation_status(confidence, param, index),
        "switch_roll": live_trace_switch_roll_range(capture, confidence),
    }


def parse_switch_context(value: Any) -> dict[str, int]:
    if value in {None, ""}:
        return {}
    parsed: dict[str, int] = {}
    for part in str(value).split(","):
        if "=" not in part:
            continue
        key, raw = part.split("=", 1)
        raw = raw.strip()
        try:
            parsed[key.strip()] = int(raw, 16)
        except ValueError:
            continue
    return parsed


def switch_observation_status(confidence: int, param: int, index: int) -> str:
    if index:
        return "actual_switch_observed"
    if param:
        return "switch_proposal_observed"
    if confidence:
        return "switch_confidence_observed"
    return "no_switch_path_observed"


def live_trace_switch_roll_range(
    capture: dict[str, Any],
    confidence: int,
) -> dict[str, Any]:
    if confidence <= 0:
        return {
            "available": False,
            "reason": "no_switch_confidence_observed",
        }
    base = live_trace_base_switch_threshold(capture)
    possible_thresholds = sorted(
        {
            base["threshold"],
            base["threshold"] + AI_SWITCH_SACK_BIAS,
            base["threshold"] + AI_SWITCH_WINCON_BIAS,
            base["threshold"] + AI_SWITCH_SACK_BIAS + AI_SWITCH_WINCON_BIAS,
        }
    )
    possible = [
        {
            "effective_threshold": threshold,
            "switch_chance_threshold": boss_ai_switch_roll_threshold(confidence, threshold),
            "switch_probability": boss_ai_switch_roll_threshold(confidence, threshold) / 256,
        }
        for threshold in possible_thresholds
    ]
    chance_values = {item["switch_chance_threshold"] for item in possible}
    return {
        "available": True,
        "confidence": confidence,
        "threshold_source": "source_mirrored_base_threshold_with_untraced_bias_range",
        "threshold_exact": False,
        "probability_exact": len(chance_values) == 1,
        "base_threshold": base["threshold"],
        "tier": base["tier"],
        "possible_effective_thresholds": possible_thresholds,
        "possible_switch_probabilities": possible,
        "proof_status": "source_mirrored_switch_roll_range_from_live_trace_confidence",
    }


def live_trace_base_switch_threshold(capture: dict[str, Any]) -> dict[str, Any]:
    tier = optional_trace_int(capture.get("fields", {}).get("tier"))
    if tier == 1:
        return {"tier": "early", "threshold": AI_SWITCH_THRESHOLD_EARLY}
    if tier == 2:
        return {"tier": "mid", "threshold": AI_SWITCH_THRESHOLD_MID}
    return {"tier": "late", "threshold": AI_SWITCH_THRESHOLD_LATE}


def live_trace_best_action_id(capture: dict[str, Any]) -> str | None:
    selector = capture.get("selector", {})
    best = slot_for_index(selector, selector.get("best_slot_index"))
    return live_trace_action_id(best) if best else None


def live_trace_action_id(slot: dict[str, Any]) -> str:
    if not slot:
        return ""
    return f"slot{int(slot.get('slot', 0))}:{slot.get('name', '')}"


def slot_for_move_id(selector: dict[str, Any], move_id: Any) -> dict[str, Any]:
    try:
        wanted = int(move_id)
    except (TypeError, ValueError):
        return {}
    for slot in selector.get("slots", []):
        if int(slot.get("move_id", -1)) == wanted:
            return slot
    return {}


def slot_for_index(selector: dict[str, Any], slot_index: Any) -> dict[str, Any]:
    if slot_index is None:
        return {}
    try:
        wanted = int(slot_index)
    except (TypeError, ValueError):
        return {}
    for slot in selector.get("slots", []):
        if int(slot.get("slot_index", -1)) == wanted:
            return slot
    return {}


def route_id_for_trace_capture(capture: dict[str, Any]) -> str:
    fields = capture.get("fields", {})
    boss = str(fields.get("boss", "")).strip()
    if boss:
        return safe_id(boss.lower().replace(".", "")).replace("-", "_")
    capture_id = str(capture.get("capture_id", ""))
    return safe_id(capture_id.split("#", 1)[0].lower()).replace("-", "_")


def optional_trace_int(value: Any) -> int | None:
    if value in {None, ""}:
        return None
    try:
        return int(str(value), 0)
    except ValueError:
        return None


def trace_int_list(value: Any) -> list[int]:
    if value in {None, ""}:
        return []
    result = []
    for part in str(value).split(","):
        part = part.strip()
        if not part:
            continue
        try:
            result.append(int(part, 0))
        except ValueError:
            return []
    return result


def trace_signed_int_list(value: Any) -> list[int]:
    if value in {None, ""}:
        return []
    result = []
    for part in str(value).split(","):
        part = part.strip()
        if not part:
            continue
        try:
            result.append(int(part, 0))
        except ValueError:
            return []
    return result


def build_rule_index() -> dict[str, dict[str, Any]]:
    data = build_rule_map()
    return {str(rule["rule_id"]): rule for rule in data.get("rules", [])}


def run_requested_rom_proof(
    scenario: dict[str, Any],
    *,
    run_rom_proof: str,
    manifest_path: Path,
    rom: Path,
    symbols_path: Path,
    score_base_route: str,
    selector_base_route: str,
    switch_base_route: str,
) -> dict[str, list[dict[str, Any]]]:
    if run_rom_proof not in ROM_PROOF_CHOICES:
        raise PreferenceDataError(
            f"--run-rom-proof must be one of: {', '.join(ROM_PROOF_CHOICES)}"
        )
    if run_rom_proof == "none":
        return {"score": [], "selector": [], "switch": []}
    proof_kind = (
        auto_rom_proof_kind(scenario) if run_rom_proof == "auto" else run_rom_proof
    )
    if proof_kind == "score":
        return {
            "score": [
                run_rom_score_materialization(
                    [scenario],
                    base_route=score_base_route,
                    manifest_path=manifest_path,
                    rom=rom,
                    symbols_path=symbols_path,
                    watch_frames=DEFAULT_SCORE_MATERIALIZE_WATCH_FRAMES,
                    compare_fast_score=True,
                    source="explain-decision:inline",
                )
            ],
            "selector": [],
            "switch": [],
        }
    if proof_kind == "switch":
        return {
            "score": [],
            "selector": [],
            "switch": [
                run_rom_switch_materialization(
                    [scenario],
                    base_route=switch_base_route,
                    manifest_path=manifest_path,
                    rom=rom,
                    symbols_path=symbols_path,
                    watch_frames=DEFAULT_SWITCH_MATERIALIZE_WATCH_FRAMES,
                    source="explain-decision:inline",
                )
            ],
        }
    return {
        "score": [],
        "selector": [
            run_rom_selector_materialization(
                [scenario],
                base_route=selector_base_route,
                manifest_path=manifest_path,
                rom=rom,
                symbols_path=symbols_path,
                watch_frames=DEFAULT_SELECTOR_MATERIALIZE_WATCH_FRAMES,
                source="explain-decision:inline",
            )
        ],
        "switch": [],
    }


def run_requested_live_rom_proof(
    capture: dict[str, Any],
    *,
    run_rom_proof: str,
    manifest_path: Path,
    rom: Path,
    symbols_path: Path,
    switch_base_route: str,
    auto_artifact_dir: Path,
) -> dict[str, list[dict[str, Any]]]:
    if run_rom_proof not in ROM_PROOF_CHOICES:
        raise PreferenceDataError(
            f"--run-rom-proof must be one of: {', '.join(ROM_PROOF_CHOICES)}"
        )
    empty: dict[str, list[dict[str, Any]]] = {
        "switch": [],
        "attempts": [],
        "blockers": [],
    }
    if run_rom_proof == "none":
        return empty
    if run_rom_proof in {"selector", "score"}:
        raise PreferenceDataError("--run-rom-proof selector/score requires --scenario")
    switch_path = live_trace_switch_path(capture)
    if run_rom_proof == "auto" and not switch_path.get("observed"):
        return empty
    if not switch_path.get("observed"):
        return {
            "switch": [],
            "attempts": [
                live_rom_proof_attempt(
                    proof_kind="switch",
                    status="unsupported_target",
                    reason="live trace has no switch-dispatch bytes to materialize",
                )
            ],
            "blockers": [],
        }

    capture_id = str(capture.get("capture_id", "live_trace"))
    scenario_path, switch_out = auto_switch_artifact_paths(capture_id, auto_artifact_dir)
    scenario_count = 12
    scenarios = generate_scenarios(family="switch_sack", count=scenario_count, seed=1)
    write_jsonl(scenarios, scenario_path)
    base_route = switch_base_route or route_id_for_trace_capture(capture)
    if switch_base_route == DEFAULT_SWITCH_MATERIALIZE_ROUTE:
        base_route = route_id_for_trace_capture(capture)

    try:
        report = run_rom_switch_materialization(
            scenarios,
            base_route=base_route,
            manifest_path=manifest_path,
            rom=rom,
            symbols_path=symbols_path,
            watch_frames=DEFAULT_SWITCH_MATERIALIZE_WATCH_FRAMES,
            source=str(scenario_path),
        )
    except PreferenceDataError as exc:
        reason = str(exc)
        status = (
            "blocked_by_hash_basis"
            if live_rom_proof_error_is_hash_basis(reason)
            else "failed"
        )
        attempt = live_rom_proof_attempt(
            proof_kind="switch",
            status=status,
            reason=reason,
            scenario_path=scenario_path,
            output_path=switch_out,
            base_route=base_route,
        )
        blockers = [attempt] if status == "blocked_by_hash_basis" else []
        return {"switch": [], "attempts": [attempt], "blockers": blockers}

    write_rom_switch_materialization_json(report, switch_out)
    attempt = live_rom_proof_attempt(
        proof_kind="switch",
        status="pass",
        reason=(
            f"rom-switch-materialize checked {report.get('checked_count', 0)} "
            f"of {report.get('scenario_count', 0)} generated switch/sack probes"
        ),
        scenario_path=scenario_path,
        output_path=switch_out,
        base_route=base_route,
        closes_evidence_ids=[
            "observed_rom_decision",
            "switch_path",
            "switch_materialization",
        ],
    )
    return {"switch": [report], "attempts": [attempt], "blockers": []}


def live_rom_proof_attempt(
    *,
    proof_kind: str,
    status: str,
    reason: str,
    scenario_path: Path | None = None,
    output_path: Path | None = None,
    base_route: str = "",
    closes_evidence_ids: list[str] | None = None,
) -> dict[str, Any]:
    attempt: dict[str, Any] = {
        "proof_kind": proof_kind,
        "status": status,
        "reason": reason,
        "closes_evidence_ids": closes_evidence_ids or [],
    }
    if base_route:
        attempt["base_route"] = base_route
    if scenario_path is not None:
        attempt["scenario_path"] = str(scenario_path)
    if output_path is not None:
        attempt["output_path"] = str(output_path)
    return attempt


def live_rom_proof_error_is_hash_basis(reason: str) -> bool:
    lowered = reason.lower()
    return "hash mismatch" in lowered or "missing switch_materialization_trace" in lowered


def auto_switch_artifact_paths(
    capture_id: str,
    auto_artifact_dir: Path,
) -> tuple[Path, Path]:
    base = auto_artifact_dir / safe_id(capture_id)
    return (
        Path(f"{base}_switch_sack_probe.jsonl"),
        Path(f"{base}_rom_switch.json"),
    )


def auto_rom_proof_kind(scenario: dict[str, Any]) -> str:
    family = str(scenario.get("family", ""))
    if family in SWITCH_MATERIALIZE_FAMILIES or scenario_has_switch_candidate(scenario):
        return "switch"
    if family in SCORE_MATERIALIZE_FAMILIES:
        return "score"
    return "selector"


def scenario_has_switch_candidate(scenario: dict[str, Any]) -> bool:
    for move in scenario.get("moves", []):
        if isinstance(move, dict) and str(move.get("kind", "")) == "switch":
            return True
    return False


def static_rule_ids_for_scenario(scenario: dict[str, Any]) -> list[str]:
    rule_ids = ["move.select_move"]
    if scenario_has_switch_candidate(scenario) or auto_rom_proof_kind(scenario) == "switch":
        rule_ids.extend(
            [
                "switch.try_switch",
                "switch.compute_switch_confidence",
                "switch.get_switch_threshold",
            ]
        )
    return rule_ids


def live_trace_static_rule_ids(capture: dict[str, Any]) -> list[str]:
    rule_ids = ["move.select_move"]
    fields = capture.get("fields", {})
    if "model_score_deltas" in fields:
        rule_ids.append("move.apply_lookahead_to_top_move_candidates")
    if live_trace_switch_path(capture).get("observed"):
        rule_ids.extend(
            [
                "switch.try_switch",
                "switch.compute_switch_confidence",
                "switch.get_switch_threshold",
            ]
        )
    return rule_ids


def load_json_reports(paths: list[Path]) -> list[dict[str, Any]]:
    reports = []
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise PreferenceDataError(f"missing report: {path}") from exc
        if not isinstance(data, dict):
            raise PreferenceDataError(f"report is not a JSON object: {path}")
        data = dict(data)
        data.setdefault("_artifact_path", str(path))
        reports.append(data)
    return reports


def replay_trace_artifacts(
    trace_paths: list[Path],
    capture_id: str | None,
) -> dict[str, Any] | None:
    if not trace_paths:
        return None
    report = replay_trace_paths(trace_paths)
    if capture_id:
        report = dict(report)
        report["verdicts"] = [
            item
            for item in report.get("verdicts", [])
            if item.get("capture_id") == capture_id
        ]
    return report


def collect_rom_contribution_reports(
    paths: list[Path],
    *,
    score_reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    reports = [load_rom_contribution_trace(path) for path in paths]
    for score_report in score_reports:
        for trace in score_report.get("traces", []):
            if isinstance(trace, dict):
                reports.append(trace)
    return reports


def candidate_packet(
    selector: dict[str, Any],
    rule_index: dict[str, dict[str, Any]],
    *,
    scenario: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    probabilities = selector.get("probabilities", {})
    action_metadata = scenario_action_metadata(scenario or {})
    candidates = []
    for move in selector.get("moves", []):
        action_id = str(move.get("action_id", ""))
        metadata = action_metadata.get(action_id, {})
        contributions = []
        for item in move.get("events", []):
            rule = str(item.get("rule", ""))
            rule_id = python_rule_id(rule)
            contributions.append(
                {
                    "rule": rule,
                    "rule_id": rule_id,
                    "before": item.get("before"),
                    "delta": item.get("delta"),
                    "after": item.get("after"),
                    "note": item.get("note", ""),
                    "source_anchor": source_anchor(rule_id, rule_index),
                }
            )
        candidates.append(
            {
                "slot": move.get("slot"),
                "action_id": action_id,
                "kind": str(move.get("kind") or metadata.get("kind") or "move"),
                "name": move.get("name") or metadata.get("name") or action_id,
                "move_id": move.get("move_id", metadata.get("move_id")),
                "initial_score": move.get("initial_score"),
                "pre_lookahead_score": move.get("pre_lookahead_score"),
                "final_score": move.get("final_score"),
                "blocked": bool(move.get("blocked", False)),
                "selector_probability": float(probabilities.get(action_id, 0.0)),
                "contributions": contributions,
            }
        )
    return candidates


def scenario_action_kinds(scenario: dict[str, Any]) -> dict[str, str]:
    return {
        action_id: str(metadata.get("kind") or "move")
        for action_id, metadata in scenario_action_metadata(scenario).items()
    }


def scenario_action_metadata(scenario: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metadata = {}
    for slot, move in enumerate(scenario.get("moves", []), start=1):
        if not isinstance(move, dict):
            continue
        action_id = str(move.get("id") or f"slot{slot}")
        if not action_id:
            continue
        row = {
            "action_id": action_id,
            "name": move.get("name", action_id),
            "move_id": move.get("move_id"),
            "kind": str(move.get("kind") or "move"),
            "slot": slot,
        }
        metadata[action_id] = row
        explicit_action_id = move.get("action_id")
        if explicit_action_id:
            metadata[str(explicit_action_id)] = row
    return metadata


def collect_rom_evidence(
    selected_id: str,
    scenario_key: str,
    *,
    scenario: dict[str, Any],
    score_reports: list[dict[str, Any]],
    selector_reports: list[dict[str, Any]],
    switch_reports: list[dict[str, Any]],
    trace_replay: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    keys = scenario_keys(selected_id, scenario_key)
    evidence: list[dict[str, Any]] = []
    for report in score_reports:
        for verdict in matching_verdicts(report, keys):
            evidence.append(score_materialization_evidence(report, verdict, scenario))
    for report in selector_reports:
        for verdict in matching_verdicts(report, keys):
            evidence.append(selector_materialization_evidence(report, verdict, scenario))
    for report in switch_reports:
        for verdict in matching_verdicts(report, keys):
            evidence.append(switch_materialization_evidence(report, verdict))
    if trace_replay is not None:
        for verdict in trace_replay.get("verdicts", []):
            evidence.append(trace_replay_evidence(verdict))
    return evidence


def matching_verdicts(
    report: dict[str, Any],
    keys: set[str],
) -> list[dict[str, Any]]:
    verdicts = [
        verdict
        for verdict in report.get("verdicts", [])
        if str(verdict.get("scenario_id", "")) in keys
    ]
    if verdicts:
        return verdicts
    all_verdicts = [item for item in report.get("verdicts", []) if isinstance(item, dict)]
    return all_verdicts if len(all_verdicts) == 1 else []


def score_materialization_evidence(
    report: dict[str, Any],
    verdict: dict[str, Any],
    scenario: dict[str, Any],
) -> dict[str, Any]:
    rom = verdict.get("rom", {})
    policy = verdict.get("rom_policy", {})
    return {
        "available": True,
        "kind": "rom_score_materialization",
        "artifact": report.get("_artifact_path", ""),
        "base_route": report.get("base_route", ""),
        "base_state": report.get("base_state", ""),
        "status": verdict.get("status", "unknown"),
        "scenario_id": verdict.get("scenario_id", ""),
        "decision": {
            "rom_best_action_id": rom.get("best_action_id"),
            "possible_action_ids": rom.get("possible_action_ids", []),
            "best_score": rom.get("best_score"),
            "final_scores": rom.get("final_scores", []),
            "selector_entry_scores": rom.get("selector_entry_scores", []),
            "post_model_scores": rom.get("post_model_scores", []),
            "selector_path": materialized_selector_path(
                scenario,
                scores=rom.get("selector_entry_scores") or rom.get("final_scores", []),
                probabilities=policy.get("probabilities", {}),
                chosen_action_id=rom.get("chosen_action_id"),
                source="rom_score_materialization_final_scores",
            ),
        },
        "python_agreement": {
            "score_bytes_match": bool(verdict.get("score_bytes_match", False)),
            "selector_top_match": bool(verdict.get("selector_top_match", False)),
            "contribution_mismatches": int(
                verdict.get("contribution_comparison", {}).get("mismatch_count", 0)
            ),
            "hook_equivalence": verdict.get("hook_equivalence", {}),
        },
        "policy": policy,
        "reason": policy.get("reason", ""),
    }


def selector_materialization_evidence(
    report: dict[str, Any],
    verdict: dict[str, Any],
    scenario: dict[str, Any],
) -> dict[str, Any]:
    rom = verdict.get("rom", {})
    return {
        "available": True,
        "kind": "rom_selector_materialization",
        "artifact": report.get("_artifact_path", ""),
        "base_route": report.get("base_route", ""),
        "base_state": report.get("base_state", ""),
        "status": verdict.get("status", "unknown"),
        "scenario_id": verdict.get("scenario_id", ""),
        "decision": {
            "chosen_action_id": rom.get("chosen_action_id"),
            "chosen_move_id": rom.get("chosen_move_id"),
            "chosen_move_name": rom.get("chosen_move_name"),
            "chosen_action_probability": rom.get("chosen_action_probability"),
            "move_scores": rom.get("move_scores", []),
            "move_ids": rom.get("move_ids", []),
            "tier": rom.get("tier"),
            "selector_path": materialized_selector_path(
                scenario,
                scores=rom.get("move_scores", []),
                probabilities=verdict.get("python", {}).get("probabilities", {}),
                chosen_action_id=rom.get("chosen_action_id"),
                chosen_move_id=rom.get("chosen_move_id"),
                chosen_slot_index=rom.get("chosen_slot_index"),
                tier=rom.get("tier"),
                source="rom_selector_materialization_patched_score_bytes",
            ),
        },
        "python_agreement": {
            "agreement": bool(verdict.get("agreement", False)),
            "reason": verdict.get("reason", ""),
        },
        "reason": verdict.get("reason", ""),
    }


def switch_materialization_evidence(
    report: dict[str, Any],
    verdict: dict[str, Any],
) -> dict[str, Any]:
    rom = verdict.get("rom", {})
    policy = verdict.get("rom_policy", {})
    return {
        "available": True,
        "kind": "rom_switch_materialization",
        "artifact": report.get("_artifact_path", ""),
        "base_route": report.get("base_route", ""),
        "base_state": report.get("base_state", ""),
        "status": verdict.get("status", "unknown"),
        "scenario_id": verdict.get("scenario_id", ""),
        "decision": {
            "expected_switch": verdict.get("expected_switch"),
            "proposed_switch": rom.get("proposed_switch"),
            "actual_switch": rom.get("actual_switch"),
            "switch_confidence": rom.get("switch_confidence"),
            "switch_param": rom.get("switch_param"),
            "switch_index": rom.get("switch_index"),
            "chosen_move": rom.get("chosen_move"),
            "observation_status": rom.get("observation_status"),
            "switch_roll": verdict.get("switch_roll", {}),
            "diagnostics": rom.get("diagnostics", {}),
        },
        "python_agreement": {
            "policy_agreement": int(policy.get("severity", 0)) == 0,
        },
        "policy": policy,
        "reason": policy.get("reason", verdict.get("reason", "")),
    }


def trace_replay_evidence(verdict: dict[str, Any]) -> dict[str, Any]:
    selector = verdict.get("selector", {})
    return {
        "available": True,
        "kind": "live_trace_selector_replay",
        "artifact": verdict.get("path", ""),
        "status": verdict.get("verdict", "unknown"),
        "capture_id": verdict.get("capture_id", ""),
        "decision": {
            "chosen_id": verdict.get("chosen_id"),
            "expected_move_ids": verdict.get("expected_move_ids", []),
            "selector": selector,
        },
        "python_agreement": {
            "agreement": bool(verdict.get("match", False)),
            "reason": verdict.get("reason", ""),
        },
        "reason": verdict.get("reason", ""),
    }


def primary_rom_evidence(
    evidence: list[dict[str, Any]],
    scenario: dict[str, Any],
) -> dict[str, Any]:
    if not evidence:
        return {
            "available": False,
            "status": "needs_rom_proof",
            "reason": "no ROM materialization, contribution trace, or live selector replay artifact was supplied",
        }
    preferred = ["rom_score_materialization", "rom_switch_materialization"]
    if scenario_has_switch_candidate(scenario):
        preferred = ["rom_switch_materialization", "rom_score_materialization"]
    preferred.extend(["rom_selector_materialization", "live_trace_selector_replay"])
    for kind in preferred:
        for item in evidence:
            if item.get("kind") == kind:
                return item
    return evidence[0]


def python_mirror_packet(
    selector: dict[str, Any],
    verdict: Any,
    primary_rom: dict[str, Any],
) -> dict[str, Any]:
    packet = {
        "available": True,
        "best_action_id": selector.get("best_action_id"),
        "second_action_id": selector.get("second_action_id"),
        "best_score": selector.get("best_score"),
        "second_score": selector.get("second_score"),
        "gap": selector.get("gap"),
        "best_roll_threshold": selector.get("best_roll_threshold"),
        "probabilities": selector.get("probabilities", {}),
        "policy_verdict": verdict.verdict,
        "policy_reason": verdict.reason,
    }
    if primary_rom.get("available"):
        packet["rom_comparison"] = primary_rom.get("python_agreement", {})
    else:
        packet["rom_comparison"] = {"available": False, "reason": primary_rom.get("reason", "")}
    return packet


def explain_rom_contributions(
    reports: list[dict[str, Any]],
    selected_id: str,
    scenario_key: str,
    rule_index: dict[str, dict[str, Any]],
    *,
    limit: int,
) -> dict[str, Any]:
    keys = scenario_keys(selected_id, scenario_key)
    matched: list[dict[str, Any]] = []
    unmatched_ids = []
    for report in reports:
        trace_id = rom_trace_id(report)
        if trace_id in keys:
            matched.append(report)
        else:
            unmatched_ids.append(trace_id)
    if not matched and len(reports) == 1:
        matched = reports
        unmatched_ids = []

    events: list[dict[str, Any]] = []
    for report in matched:
        for item in report.get("events", []):
            if not isinstance(item, dict) or not item.get("changed"):
                continue
            source = item.get("source", {})
            candidate = item.get("candidate", {})
            rule_id = str(source.get("rule_id", ""))
            events.append(
                {
                    "trace_id": rom_trace_id(report),
                    "candidate": {
                        "kind": candidate.get("kind", ""),
                        "slot": candidate.get("slot"),
                        "slot_index": candidate.get("slot_index"),
                        "move_id": candidate.get("move_id"),
                        "move_name": candidate.get("move_name", ""),
                    },
                    "rule_id": rule_id,
                    "operation": item.get("operation", ""),
                    "before": item.get("score_before"),
                    "delta": item.get("delta"),
                    "after": item.get("score_after"),
                    "helper_symbol": item.get("helper_symbol", ""),
                    "closed_by": item.get("closed_by", ""),
                    "source_anchor": source_anchor(rule_id, rule_index, source=source),
                }
            )

    return {
        "available": bool(reports),
        "matched_trace_count": len(matched),
        "unmatched_trace_ids": unmatched_ids,
        "event_count": len(events),
        "events": events[:limit],
    }


def public_input_packet(
    scenario: dict[str, Any],
    verdict: Any,
    reports: list[dict[str, Any]],
    selected_id: str,
    scenario_key: str,
    rule_index: dict[str, dict[str, Any]],
    *,
    limit: int,
) -> dict[str, Any]:
    keys = scenario_keys(selected_id, scenario_key)
    matching_reports = [
        report
        for report in reports
        if rom_trace_id(report) in keys or len(reports) == 1
    ]
    predicate_branches = []
    public_read_probes = []
    public_reads: dict[str, list[str]] = {}
    for report in matching_reports:
        for entry in report.get("events", []):
            if not isinstance(entry, dict):
                continue
            source = entry.get("source", {})
            rule_id = str(source.get("rule_id", ""))
            if rule_id:
                public_reads.setdefault(rule_id, list(source.get("public_reads", [])))
        for entry in report.get("rule_entries", []):
            if not isinstance(entry, dict):
                continue
            source = entry.get("source", {})
            rule_id = str(source.get("rule_id", ""))
            if rule_id:
                public_reads.setdefault(rule_id, list(source.get("public_reads", [])))
        for entry in report.get("predicate_branch_entries", []):
            if not isinstance(entry, dict):
                continue
            predicate = entry.get("predicate", {})
            source = entry.get("source", {})
            rule_id = str(source.get("rule_id", ""))
            public_reads[rule_id] = list(source.get("public_reads", []))
            predicate_branches.append(
                {
                    "trace_id": rom_trace_id(report),
                    "predicate_id": predicate.get("predicate_id", ""),
                    "outcome": predicate.get("outcome", ""),
                    "legal_inputs": predicate.get("legal_inputs", []),
                    "snapshot": compact_snapshot(entry.get("public_input_snapshot", {})),
                    "source_anchor": source_anchor(rule_id, rule_index, source=source),
                }
            )
        for entry in report.get("public_read_probe_entries", []):
            if not isinstance(entry, dict):
                continue
            probe = entry.get("probe", {})
            source = entry.get("source", {})
            rule_id = str(source.get("rule_id", ""))
            public_reads[rule_id] = list(source.get("public_reads", []))
            public_read_probes.append(
                {
                    "trace_id": rom_trace_id(report),
                    "probe_id": probe.get("probe_id", ""),
                    "outcome": probe.get("outcome", ""),
                    "legal_inputs": probe.get("legal_inputs", []),
                    "snapshot": compact_snapshot(entry.get("public_input_snapshot", {})),
                    "source_anchor": source_anchor(rule_id, rule_index, source=source),
                }
            )

    return {
        "policy_tags": verdict.policy_tags,
        "condition_tags": verdict.condition_tags,
        "answer_changing_information": verdict.answer_changing_information,
        "evidence_refs": verdict.evidence_refs,
        "scenario_public_keys": scenario_public_keys(scenario),
        "rom_public_reads_by_rule": dict(sorted(public_reads.items())),
        "predicate_branches": predicate_branches[:limit],
        "public_read_probes": public_read_probes[:limit],
    }


def compact_snapshot(snapshot: Any) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        return {}
    compact: dict[str, Any] = {}
    for name, data in snapshot.items():
        if not isinstance(data, dict):
            continue
        compact[str(name)] = {
            "available": data.get("available"),
            "values": data.get("values", []),
            "kind": data.get("kind", ""),
        }
    return compact


def scenario_public_keys(scenario: dict[str, Any]) -> list[str]:
    keys = []
    for key in (
        "tier",
        "family",
        "moves",
        "expectation",
        "public",
        "known_to_boss",
        "overrides",
        "trainer_class",
        "switch_threshold_adjustments",
    ):
        if key in scenario:
            keys.append(key)
    return keys


def source_anchor_packet(
    rule_index: dict[str, dict[str, Any]],
    *,
    python_candidates: list[dict[str, Any]],
    rom_contributions: dict[str, Any],
    extra_rule_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    rule_ids = set()
    for rule_id in extra_rule_ids or []:
        rule_ids.add(str(rule_id))
    for candidate in python_candidates:
        for contribution in candidate.get("contributions", []):
            if contribution.get("rule_id"):
                rule_ids.add(str(contribution["rule_id"]))
    for contribution in rom_contributions.get("events", []):
        if contribution.get("rule_id"):
            rule_ids.add(str(contribution["rule_id"]))
    anchors = [
        source_anchor(rule_id, rule_index)
        for rule_id in sorted(rule_ids)
        if source_anchor(rule_id, rule_index) is not None
    ]
    return [anchor for anchor in anchors if anchor is not None]


def source_anchor(
    rule_id: str,
    rule_index: dict[str, dict[str, Any]],
    *,
    source: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    rule = rule_index.get(rule_id)
    if rule is None and source:
        return {
            "rule_id": rule_id,
            "source_file": "",
            "line": None,
            "source_label": source.get("source_label", ""),
            "classification": source.get("classification", ""),
            "public_reads": source.get("public_reads", []),
            "anchor_status": "runtime_source_unmapped",
        }
    if rule is None:
        return None
    return {
        "rule_id": rule_id,
        "source_file": rule.get("source_file", ""),
        "line": rule.get("line"),
        "source_label": rule.get("source_label", ""),
        "parent_label": rule.get("parent_label"),
        "classification": rule.get("classification", ""),
        "public_reads": rule.get("public_reads", []),
        "coverage_mode": rule.get("coverage_mode", ""),
        "anchor_status": "mapped",
    }


def counterfactual_packet(counterfactual: dict[str, Any]) -> dict[str, Any]:
    return {
        "smallest_score_flip": counterfactual.get("smallest_score_flip"),
        "nearest_challenger_score_flip": counterfactual.get(
            "nearest_challenger_score_flip"
        ),
        "focus_score_flip": counterfactual.get("focus_score_flip"),
        "public_fact_counterfactuals": counterfactual.get(
            "public_fact_counterfactuals",
            [],
        ),
        "answer_changing_information": counterfactual.get(
            "answer_changing_information",
            [],
        ),
        "why": counterfactual.get("why", ""),
    }


def focus_score_flip(
    selector: dict[str, Any],
    action_id: str,
    *,
    scenario: dict[str, Any] | None = None,
) -> dict[str, Any]:
    action_metadata = scenario_action_metadata(scenario or {})
    moves = [
        {
            **move,
            **{
                key: value
                for key, value in action_metadata.get(str(move.get("action_id", "")), {}).items()
                if value not in (None, "")
            },
            "action_id": move.get("action_id"),
        }
        for move in selector.get("moves", [])
    ]
    matched_move = next(
        (
            move
            for move in moves
            if action_matches_candidate(move, action_id)
        ),
        None,
    )
    resolved_action_id = (
        str(matched_move.get("action_id"))
        if matched_move and matched_move.get("action_id") is not None
        else action_id
    )
    score_by_action = {
        str(move["action_id"]): int(move["final_score"])
        for move in moves
    }
    slot_by_action = {
        str(move["action_id"]): int(move["slot"])
        for move in moves
    }
    best_score = int(selector.get("best_score", BLOCKED_SCORE)) if selector.get("ready") else BLOCKED_SCORE
    best_slot = slot_by_action.get(selector.get("best_action_id"), 99)
    flip = score_flip_for_action(
        resolved_action_id,
        score_by_action,
        slot_by_action,
        best_score=best_score,
        best_slot=best_slot,
    )
    if matched_move:
        flip = {
            **flip,
            "requested_action_id": action_id,
            "name": matched_move.get("name", ""),
            "move_id": matched_move.get("move_id"),
            "slot": matched_move.get("slot"),
            "slot_index": matched_move.get("slot_index"),
        }
    return smallest_score_flip([flip]) or flip


def decision_trace_summary(trace: dict[str, Any]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for event in trace.get("events", []):
        event_type = str(event.get("event_type", ""))
        counts[event_type] = counts.get(event_type, 0) + 1
    return {
        "event_count": trace.get("event_count", 0),
        "event_type_counts": dict(sorted(counts.items())),
    }


def finalize_explanation_report(report: dict[str, Any]) -> dict[str, Any]:
    selector_counterfactual = selector_roll_counterfactual_packet(
        report.get("observed_rom_decision", {})
    )
    if selector_counterfactual.get("available"):
        report.setdefault("counterfactual", {})[
            "selector_roll_counterfactual"
        ] = selector_counterfactual
    switch_counterfactual = switch_roll_counterfactual_packet(
        report.get("observed_rom_decision", {})
    )
    if switch_counterfactual.get("available"):
        report.setdefault("counterfactual", {})[
            "switch_roll_counterfactual"
        ] = switch_counterfactual
    report["proof_status"] = proof_status_packet(report)
    report["closed_evidence_ids"] = list(report["proof_status"].get("present_ids", []))
    report["deity_evidence_marker"] = deity_evidence_marker(report)
    report["decision_summary"] = decision_summary_packet(report)
    return report


def deity_evidence_marker(report: dict[str, Any]) -> str:
    present = set(report.get("proof_status", {}).get("present_ids", []))
    if {
        "decision_input.auto_resolved",
        "input_manifest.replay_verified",
    }.issubset(present):
        return "BOSS_AI_DEITY_DECISION_INPUT_RESOLVED"
    if not report.get("proof_status", {}).get("missing_ids"):
        return "BOSS_AI_DEITY_PROOF_COMPLETE"
    return "BOSS_AI_DEITY_PARTIAL_PROOF_PACKET"


def selector_roll_counterfactual_packet(rom: dict[str, Any]) -> dict[str, Any]:
    selector_path = rom.get("decision", {}).get("selector_path", {})
    if not selector_path.get("available"):
        return {"available": False, "reason": "no selector path evidence"}
    chosen = str(selector_path.get("chosen_action_id") or "")
    best = str(selector_path.get("best_action_id") or "")
    second = str(selector_path.get("second_action_id") or "")
    threshold = optional_trace_int(selector_path.get("best_roll_threshold"))
    if not chosen:
        return {
            "available": False,
            "reason": "selector surface has no sampled ROM chosen action",
        }
    if not best or not second or threshold is None:
        return {
            "available": False,
            "reason": "selector had no second candidate roll surface",
        }
    probabilities = selector_path.get("candidate_probabilities", {})
    best_probability = (
        optional_float(probabilities.get(best)) if isinstance(probabilities, dict) else None
    )
    second_probability = (
        optional_float(probabilities.get(second)) if isinstance(probabilities, dict) else None
    )
    best_range = selector_roll_range(0, threshold - 1)
    second_range = selector_roll_range(threshold, 255)
    if chosen == best:
        chosen_rank = "best"
        alternate = second
        chosen_range = best_range
        alternate_range = second_range
        observed_random = False
        reason = (
            "observed action was the selector best candidate; a roll in the "
            "second-candidate range would choose the alternate action"
        )
    elif chosen == second:
        chosen_rank = "second"
        alternate = best
        chosen_range = second_range
        alternate_range = best_range
        observed_random = True
        reason = (
            "observed action was the selector second candidate, so score bytes "
            "favored the best candidate but the BossAI_SelectMove roll selected "
            "the second candidate"
        )
    else:
        return {
            "available": False,
            "reason": "observed action is not the selector best or second candidate",
        }
    packet = {
        "available": True,
        "source": selector_path.get("source", ""),
        "chosen_action_id": chosen,
        "chosen_rank": chosen_rank,
        "alternate_action_id": alternate,
        "best_action_id": best,
        "second_action_id": second,
        "best_score": selector_path.get("best_score"),
        "second_score": selector_path.get("second_score"),
        "score_gap": selector_path.get("score_gap"),
        "best_roll_threshold": threshold,
        "roll_denominator": 256,
        "best_probability": best_probability,
        "second_probability": second_probability,
        "chosen_roll_range": chosen_range,
        "alternate_roll_range": alternate_range,
        "best_roll_range": best_range,
        "second_roll_range": second_range,
        "observed_choice_due_to_random_roll": observed_random,
        "reason": reason,
    }
    packet["summary"] = selector_roll_counterfactual_text(packet)
    return packet


def selector_roll_range(start: int, end: int) -> dict[str, Any]:
    if end < start:
        return {"empty": True, "count": 0}
    return {"min": start, "max": end, "count": end - start + 1}


def selector_roll_counterfactual_text(packet: dict[str, Any]) -> str:
    chosen_range = roll_range_text(packet.get("chosen_roll_range", {}))
    alternate_range = roll_range_text(packet.get("alternate_roll_range", {}))
    return (
        f"chosen={packet.get('chosen_action_id')} "
        f"roll={chosen_range}; alternate={packet.get('alternate_action_id')} "
        f"if roll={alternate_range}; threshold="
        f"{packet.get('best_roll_threshold')}/256"
    )


def roll_range_text(value: dict[str, Any]) -> str:
    if value.get("empty"):
        return "none"
    if {"min", "max", "count"}.issubset(value):
        return f"{value.get('min')}..{value.get('max')} ({value.get('count')}/256)"
    return "unknown"


def switch_roll_counterfactual_packet(rom: dict[str, Any]) -> dict[str, Any]:
    decision = rom.get("decision", {})
    switch_path = decision.get("switch_path", {})
    if switch_path.get("observed"):
        confidence = optional_trace_int(switch_path.get("switch_confidence"))
        roll = switch_path.get("switch_roll", {})
        observation_status = switch_path.get("observation_status", "")
        source = "live_trace_switch_path"
    elif rom.get("kind") == "rom_switch_materialization":
        confidence = optional_trace_int(decision.get("switch_confidence"))
        roll = decision.get("switch_roll", {})
        observation_status = decision.get("observation_status", "")
        source = "rom_switch_materialization"
    else:
        return {"available": False, "reason": "no switch roll evidence"}
    if confidence is None or confidence <= 0 or not roll.get("available"):
        return {
            "available": False,
            "reason": "switch confidence or switch-roll threshold evidence unavailable",
        }
    thresholds = switch_roll_thresholds(roll)
    if not thresholds:
        return {"available": False, "reason": "no effective switch threshold evidence"}
    min_threshold = min(thresholds)
    max_threshold = max(thresholds)
    zero_target = min_threshold - 1
    nonzero_possible_target = min_threshold
    nonzero_guaranteed_target = max_threshold
    mid_possible_target = min_threshold + BOSS_AI_SWITCH_ROLL_MID_MARGIN
    high_possible_target = min_threshold + BOSS_AI_SWITCH_ROLL_HIGH_MARGIN
    return {
        "available": True,
        "source": source,
        "observation_status": observation_status,
        "confidence": confidence,
        "threshold_exact": bool(roll.get("threshold_exact", False)),
        "probability_exact": bool(roll.get("probability_exact", False)),
        "possible_effective_thresholds": thresholds,
        "current_probability_range": switch_probability_range(roll),
        "zero_probability_if_confidence_at_most": zero_target,
        "delta_to_force_zero_probability": zero_target - confidence,
        "nonzero_possible_at_confidence": nonzero_possible_target,
        "delta_to_make_nonzero_possible": max(0, nonzero_possible_target - confidence),
        "nonzero_guaranteed_at_confidence": nonzero_guaranteed_target,
        "delta_to_guarantee_nonzero_probability": max(
            0,
            nonzero_guaranteed_target - confidence,
        ),
        "mid_roll_possible_at_confidence": mid_possible_target,
        "delta_to_make_mid_roll_possible": max(0, mid_possible_target - confidence),
        "high_roll_possible_at_confidence": high_possible_target,
        "delta_to_make_high_roll_possible": max(0, high_possible_target - confidence),
        "note": (
            "Switch counterfactuals move the source-mirrored confidence/threshold "
            "roll surface; actual switching can still depend on RNG when probability is nonzero."
        ),
    }


def switch_roll_thresholds(roll: dict[str, Any]) -> list[int]:
    thresholds = [
        optional_trace_int(item)
        for item in roll.get("possible_effective_thresholds", [])
    ]
    thresholds = [item for item in thresholds if item is not None]
    if thresholds:
        return sorted(set(thresholds))
    for key in ("assumed_effective_threshold", "base_threshold"):
        value = optional_trace_int(roll.get(key))
        if value is not None:
            return [value]
    return []


def switch_probability_range(roll: dict[str, Any]) -> dict[str, float] | dict[str, str]:
    probabilities = []
    for item in roll.get("possible_switch_probabilities", []):
        if isinstance(item, dict):
            probability = item.get("switch_probability")
            if isinstance(probability, (int, float)):
                probabilities.append(float(probability))
    if not probabilities and isinstance(roll.get("switch_probability"), (int, float)):
        probabilities.append(float(roll["switch_probability"]))
    if not probabilities:
        return {"available": "false"}
    return {
        "min": min(probabilities),
        "max": max(probabilities),
    }


def proof_status_packet(report: dict[str, Any]) -> dict[str, Any]:
    rom = report.get("observed_rom_decision", {})
    decision = rom.get("decision", {})
    selector_path = decision.get("selector_path", {})
    rom_contributions = report.get("rom_contributions", {})
    public_inputs = report.get("public_info_inputs", {})
    decision_input = report.get("decision_input", {})
    proof_blockers = report.get("proof_blockers", [])
    checks: list[dict[str, str]] = []
    is_switch_materialization = rom.get("kind") == "rom_switch_materialization"
    has_proven_switch_materialization = report_has_proven_switch_materialization(report)

    def add(check_id: str, status: str, detail: str) -> None:
        checks.append({"id": check_id, "status": status, "detail": detail})

    if decision_input:
        resolution = decision_input.get("resolution", {})
        replay = decision_input.get("replay_verification", {})
        if resolution.get("source") == "generated_scenario":
            add(
                "decision_input.generated_auto",
                "present",
                str(resolution.get("scenario_id") or "generated scenario selected"),
            )
        else:
            add(
                "decision_input.auto_resolved",
                "present" if resolution.get("source") else "missing",
                str(resolution.get("source") or "decision input resolver did not run"),
            )
            add(
                "input_manifest.replay_verified",
                "present" if replay.get("verified") else "missing",
                str(replay.get("reason") or "input manifest replay verification failed"),
            )

    hash_blocker = first_proof_blocker(proof_blockers, "blocked_by_hash_basis")
    if hash_blocker:
        add(
            "hash_basis.current",
            "missing",
            str(hash_blocker.get("reason") or "ROM proof blocked by stale trace basis"),
        )

    add(
        "observed_rom_decision",
        "present" if rom.get("available") else "missing",
        str(rom.get("kind") or rom.get("reason") or ""),
    )
    add(
        "candidate_scores",
        "present" if report.get("candidate_scores") else "missing",
        f"candidates={len(report.get('candidate_scores', []))}",
    )
    if is_switch_materialization:
        add("score_bytes", "not_applicable", "switch materialization does not prove move score bytes")
    else:
        add(
            "score_bytes",
            "present" if primary_decision_has_score_bytes(rom) else "missing",
            score_byte_detail(rom),
        )
    if is_switch_materialization:
        add("selector_path", "not_applicable", "switch materialization is not a move selector decision")
    else:
        add(
            "selector_path",
            "present" if selector_path.get("available") else "missing",
            str(selector_path.get("source") or selector_path.get("reason") or ""),
        )

    switch_path = decision.get("switch_path", {})
    has_switch_materialization = report_has_switch_materialization(report)
    if is_switch_materialization:
        add("switch_path", "present", str(decision.get("observation_status", "")))
    elif switch_path.get("observed"):
        add("switch_path", "present", str(switch_path.get("observation_status", "")))
    else:
        add("switch_path", "not_applicable", "no switch-dispatch bytes observed")
    if has_switch_materialization:
        add(
            "switch_materialization",
            "present",
            "rom-switch-materialize artifact attached",
        )
    elif report_has_switch_candidate(report):
        add(
            "switch_materialization",
            "missing",
            "switch-candidate scenario needs rom-switch-materialize proof",
        )
    elif switch_path.get("observed"):
        add(
            "switch_materialization",
            "missing",
            "live switch path observed; scenario-level switch-dispatch proof not attached",
        )
    else:
        add(
            "switch_materialization",
            "not_applicable",
            "no switch-dispatch proof needed for this packet",
        )

    add(
        "python_score_contributions",
        "present" if candidate_contributions_available(report.get("candidate_scores", [])) else "missing",
        "candidate contribution deltas from the Python/debugger model",
    )
    if is_switch_materialization and not rom_contributions.get("events"):
        add(
            "rom_contribution_deltas",
            "not_applicable",
            "switch materialization proof does not require move-score contribution deltas",
        )
    else:
        add(
            "rom_contribution_deltas",
            "present" if rom_contributions.get("events") else "missing",
            f"matched_events={len(rom_contributions.get('events', []))}",
        )
    add(
        "public_info_inputs",
        "present" if public_input_baseline_available(public_inputs) else "missing",
        public_input_detail(public_inputs),
    )
    if is_switch_materialization and not rom_public_read_provenance_available(public_inputs):
        add(
            "rom_public_read_provenance",
            "not_applicable",
            "switch proof uses patched public switch facts plus source anchors",
        )
    else:
        add(
            "rom_public_read_provenance",
            "present" if rom_public_read_provenance_available(public_inputs) else "missing",
            "predicate branches, public-read probes, or ROM public-read map",
        )
    add(
        "source_anchors",
        "present" if report.get("source_anchors") else "missing",
        f"anchors={len(report.get('source_anchors', []))}",
    )
    add(
        "counterfactual",
        "present" if counterfactual_available(report.get("counterfactual", {})) else "missing",
        "score flip or public-fact counterfactual",
    )
    summary_policy = policy_expectation_packet(report)
    add(
        "policy_expectation.reported",
        "present" if summary_policy.get("available") else "not_applicable",
        str(summary_policy.get("summary") or "no generated policy expectation"),
    )
    add(
        "counterfactual.decisive",
        "present" if counterfactual_available(report.get("counterfactual", {})) else "missing",
        "score, selector, switch, or public-fact counterfactual",
    )
    if rom.get("kind") == "rom_selector_materialization" and selector_path.get("available"):
        add(
            "selector_materialization.proven",
            "present",
            str(selector_path.get("source") or "ROM selector materialization"),
        )
    elif rom.get("kind") == "rom_selector_materialization":
        add(
            "selector_materialization.proven",
            "missing",
            str(rom.get("reason") or "selector materialization did not observe a selector path"),
        )
    else:
        add(
            "selector_materialization.proven",
            "not_applicable",
            str(rom.get("kind") or "no selector materialization requested"),
        )
    if has_proven_switch_materialization:
        add(
            "switch_materialization.proven",
            "present",
            "ROM switch materialization attached",
        )
        add(
            "switch_roll.reported",
            "present",
            "ROM switch roll packet available",
        )
    elif is_switch_materialization or report_has_switch_candidate(report) or switch_path.get("observed"):
        add(
            "switch_materialization.proven",
            "missing",
            "switch materialization not attached",
        )
        add(
            "switch_roll.reported",
            "missing",
            "switch materialization not attached",
        )

    target = decision_input.get("target", {}) if isinstance(decision_input, dict) else {}
    if target.get("score_rule"):
        add(
            "score_rule.rom_delta_observed",
            "present" if rom_contributions.get("events") else "missing",
            f"matched_rom_delta_events={len(rom_contributions.get('events', []))}",
        )
        add(
            "public_reads.snapshotted",
            "present" if rom_public_read_provenance_available(public_inputs) else "missing",
            "predicate/public-read snapshot provenance",
        )
        add(
            "python_contribution.normalized",
            "present" if candidate_contributions_available(report.get("candidate_scores", [])) else "missing",
            "Python candidate contribution waterfall normalized",
        )
        add(
            "rom_python_agreement.reported",
            "present" if rom.get("python_agreement") else "missing",
            "ROM/Python comparison packet reported",
        )

    missing_ids = [item["id"] for item in checks if item["status"] == "missing"]
    present_ids = [item["id"] for item in checks if item["status"] == "present"]
    next_commands = list(report.get("next_proof_commands", []))
    if hash_blocker:
        next_commands = [
            *hash_basis_refresh_commands(hash_blocker),
            *next_commands,
        ]
    next_command = prioritized_next_proof_command(
        next_commands,
        missing_ids,
    )
    next_chain = next_proof_chain(
        next_commands,
        missing_ids,
        next_command,
    )
    return {
        "status": proof_workflow_status(report, missing_ids),
        "checks": checks,
        "present_ids": present_ids,
        "missing_ids": missing_ids,
        "blockers": proof_blockers,
        "next_proof_command": next_command,
        "next_proof_chain": next_chain,
        "next_proof_reason": next_proof_reason(missing_ids, next_command),
    }


def first_proof_blocker(
    blockers: list[dict[str, Any]],
    status: str,
) -> dict[str, Any]:
    for blocker in blockers:
        if blocker.get("status") == status:
            return blocker
    return {}


def proof_workflow_status(report: dict[str, Any], missing_ids: list[str]) -> str:
    if first_proof_blocker(report.get("proof_blockers", []), "blocked_by_hash_basis"):
        return "blocked_by_hash_basis"
    rom = report.get("observed_rom_decision", {})
    if not rom.get("available"):
        return "needs_rom_proof"
    if not missing_ids:
        return "explained"
    if "switch_materialization" in missing_ids:
        return "needs_switch_proof"
    if (
        "rom_contribution_deltas" in missing_ids
        or "rom_public_read_provenance" in missing_ids
    ):
        return "needs_contribution_proof"
    if any(item in missing_ids for item in ("score_bytes", "selector_path")):
        return "needs_rom_proof"
    return "partial"


def hash_basis_refresh_commands(blocker: dict[str, Any]) -> list[dict[str, Any]]:
    base_route = str(blocker.get("base_route") or "")
    if base_route != "shared_switch_loop":
        return [
            proof_command(
                purpose="Refresh manifest-pinned trace ROM basis for this Boss AI proof",
                command="python tools\\trace\\boss_ai_trace_batch.py --execute",
                closes_evidence_ids=["hash_basis.current"],
            )
        ]
    return [
        proof_command(
            purpose="Refresh Jasmine base state for shared switch materialization",
            command=(
                "python tools\\trace\\boss_ai_state_factory.py --boss jasmine "
                "--battery-save .local\\tmp\\boss_state_factory\\pokegold_trace.gbc.ram "
                "--out-dir .local\\tmp\\boss_state_factory_current --update-manifest"
            ),
            expected_output_paths=[
                ".local\\tmp\\boss_state_factory_current\\jasmine.state",
            ],
        ),
        proof_command(
            purpose="Refresh shared switch pre-dispatch state and manifest hashes",
            command="python tools\\trace\\boss_ai_shared_switch_loop_fixture.py --update-manifest",
            closes_evidence_ids=["hash_basis.current"],
            expected_output_paths=[
                ".local\\tmp\\boss_state_factory\\shared_switch_loop_predispatch.state",
                "audit\\boss_ai_trace\\live_capture_manifest.json",
            ],
        ),
    ]


def decision_summary_packet(report: dict[str, Any]) -> dict[str, Any]:
    proof = report.get("proof_status", {})
    rom = report.get("observed_rom_decision", {})
    missing_ids = list(proof.get("missing_ids", []))
    return {
        "status": proof.get("status") or decision_summary_status(rom, missing_ids),
        "observed": observed_decision_text(rom),
        "why": decision_why_text(report),
        "path": decision_path_text(rom),
        "policy_expectation": policy_expectation_packet(report),
        "selector_choice_explanation": selector_choice_explanation_packet(rom),
        "python_agreement": python_agreement_text(
            report.get("python_mirror", {}),
            rom,
        ),
        "decisive_counterfactual": decisive_counterfactual_text(
            report.get("counterfactual", {})
        ),
        "focus_action_comparison": focus_action_comparison_packet(report),
        "evidence_highlights": evidence_highlights_packet(report),
        "missing_evidence": missing_ids,
        "next_proof_command": proof.get("next_proof_command") or {},
        "next_proof_chain": proof.get("next_proof_chain") or [],
    }


def policy_expectation_packet(report: dict[str, Any]) -> dict[str, Any]:
    question = report.get("question", {})
    expected = list(question.get("expected_best_action_ids", []))
    acceptable = list(question.get("expected_acceptable_action_ids", []))
    bad = list(question.get("expected_bad_action_ids", []))
    catastrophic = list(question.get("expected_catastrophic_action_ids", []))
    if not any((expected, acceptable, bad, catastrophic)):
        return {}
    packet = {
        "available": True,
        "policy_verdict": question.get("policy_verdict")
        or report.get("python_mirror", {}).get("policy_verdict"),
        "policy_reason": question.get("policy_reason")
        or report.get("python_mirror", {}).get("policy_reason", ""),
        "expected_best_action_ids": expected,
        "expected_acceptable_action_ids": acceptable,
        "expected_bad_action_ids": bad,
        "expected_catastrophic_action_ids": catastrophic,
        "rolled_bad_action_ids": list(question.get("rolled_bad_action_ids", [])),
        "rolled_catastrophic_action_ids": list(
            question.get("rolled_catastrophic_action_ids", [])
        ),
        "zero_probability_best_action_ids": list(
            question.get("zero_probability_best_action_ids", [])
        ),
        "why": question.get("policy_why", ""),
        "lesson_type": question.get("lesson_type", ""),
        "confidence": question.get("confidence", ""),
        "evidence_refs": list(question.get("evidence_refs", [])),
    }
    packet["summary"] = policy_expectation_text(packet)
    return packet


def policy_expectation_text(packet: dict[str, Any]) -> str:
    parts = []
    if packet.get("policy_verdict"):
        parts.append(f"verdict={packet.get('policy_verdict')}")
    parts.append(
        "expected_best="
        f"{compact_action_list(packet.get('expected_best_action_ids', []))}"
    )
    if packet.get("expected_acceptable_action_ids"):
        parts.append(
            "acceptable="
            f"{compact_action_list(packet.get('expected_acceptable_action_ids', []))}"
        )
    if packet.get("expected_bad_action_ids"):
        parts.append(
            "bad="
            f"{compact_action_list(packet.get('expected_bad_action_ids', []))}"
        )
    if packet.get("expected_catastrophic_action_ids"):
        parts.append(
            "catastrophic="
            f"{compact_action_list(packet.get('expected_catastrophic_action_ids', []))}"
        )
    if packet.get("rolled_bad_action_ids"):
        parts.append(
            "rolled_bad="
            f"{compact_action_list(packet.get('rolled_bad_action_ids', []))}"
        )
    if packet.get("rolled_catastrophic_action_ids"):
        parts.append(
            "rolled_catastrophic="
            f"{compact_action_list(packet.get('rolled_catastrophic_action_ids', []))}"
        )
    if packet.get("zero_probability_best_action_ids"):
        parts.append(
            "zero_p_best="
            f"{compact_action_list(packet.get('zero_probability_best_action_ids', []))}"
        )
    if packet.get("policy_reason"):
        parts.append(f"reason={packet.get('policy_reason')}")
    if packet.get("why"):
        parts.append(f"why={compact_public_value(packet.get('why'), max_length=96)}")
    return "; ".join(parts)


def compact_action_list(values: list[Any], *, limit: int = 4) -> str:
    if not values:
        return "none"
    text_values = [str(value) for value in values[:limit]]
    suffix = ",..." if len(values) > limit else ""
    return ",".join(text_values) + suffix


def selector_choice_explanation_packet(rom: dict[str, Any]) -> dict[str, Any]:
    if not rom.get("available"):
        return {}
    selector_path = rom.get("decision", {}).get("selector_path", {})
    if not selector_path.get("available"):
        return {}
    chosen = str(selector_path.get("chosen_action_id") or "")
    best = str(selector_path.get("best_action_id") or "")
    second = str(selector_path.get("second_action_id") or "")
    chosen_probability = selector_path_chosen_probability(selector_path, chosen)
    chosen_has_nonzero = (
        bool(selector_path.get("chosen_has_nonzero_probability"))
        or (chosen_probability is not None and chosen_probability > 0.0)
    )
    if not chosen:
        rank = "unknown"
        reason = (
            "no sampled ROM chosen action is attached; selector surface gives "
            "score bytes and probabilities only"
        )
    elif best and chosen == best:
        rank = "best"
        reason = "observed action was the selector best candidate"
    elif second and chosen == second:
        rank = "second"
        if chosen_has_nonzero:
            reason = (
                "observed action was the second selector candidate with nonzero "
                "BossAI_SelectMove roll probability"
            )
        else:
            reason = (
                "observed action matches the second selector candidate, but the "
                "recorded probability is zero; inspect score bytes and replay"
            )
    elif chosen_has_nonzero:
        rank = "other_nonzero"
        reason = (
            "observed action has nonzero selector probability but is not the "
            "named best or second candidate"
        )
    elif chosen_probability == 0.0:
        rank = "zero_probability"
        reason = (
            "observed action is not in the nonzero selector set; inspect score "
            "bytes and trace replay"
        )
    else:
        rank = "unknown"
        reason = "observed action could not be ranked against the selector path"
    packet = {
        "available": True,
        "chosen_action_id": chosen,
        "chosen_rank": rank,
        "chosen_probability": chosen_probability,
        "chosen_has_nonzero_probability": chosen_has_nonzero,
        "best_action_id": best,
        "best_score": selector_path.get("best_score"),
        "second_action_id": second,
        "second_score": selector_path.get("second_score"),
        "score_gap": selector_path.get("score_gap"),
        "best_roll_threshold": selector_path.get("best_roll_threshold"),
        "possible_action_ids": selector_path.get("possible_action_ids", []),
        "reason": reason,
    }
    packet["summary"] = selector_choice_explanation_text(packet)
    return packet


def selector_path_chosen_probability(
    selector_path: dict[str, Any],
    chosen_action_id: str,
) -> float | None:
    raw = selector_path.get("chosen_probability")
    if raw in (None, "") and chosen_action_id:
        probabilities = selector_path.get("candidate_probabilities", {})
        if isinstance(probabilities, dict):
            raw = probabilities.get(chosen_action_id)
    return optional_float(raw)


def selector_choice_explanation_text(packet: dict[str, Any]) -> str:
    rank = packet.get("chosen_rank")
    if rank == "best":
        label = "chosen best candidate"
    elif rank == "second":
        label = "chosen second candidate via selector roll"
    elif rank == "other_nonzero":
        label = "chosen nonzero-probability candidate"
    elif rank == "zero_probability":
        label = "chosen zero-probability candidate"
    elif packet.get("chosen_action_id"):
        label = "chosen rank unknown"
    else:
        label = "no sampled chosen action"
    parts = [label]
    if packet.get("chosen_action_id"):
        parts.append(f"chosen={packet.get('chosen_action_id')}")
        parts.append(f"p={format_probability(packet.get('chosen_probability'))}")
    if packet.get("best_action_id"):
        parts.append(f"best={packet.get('best_action_id')}")
    if packet.get("second_action_id"):
        parts.append(f"second={packet.get('second_action_id')}")
    if packet.get("score_gap") is not None:
        parts.append(f"gap={packet.get('score_gap')}")
    parts.append(
        "threshold="
        + (
            f"{packet.get('best_roll_threshold')}/256"
            if packet.get("best_roll_threshold") is not None
            else "single-candidate"
        )
    )
    return "; ".join(parts)


def focus_action_comparison_packet(report: dict[str, Any]) -> dict[str, Any]:
    focus = str(report.get("question", {}).get("focus_action_id", "")).strip()
    if not focus:
        return {}
    candidates = report.get("candidate_scores", [])
    focus_candidate = find_candidate(candidates, focus)
    if focus_candidate is None:
        return {
            "requested_action_id": focus,
            "found": False,
            "reason": "focus action is not present in candidate scores",
            "available_action_count": len(candidates),
            "available_actions": available_action_suggestions(candidates),
        }
    chosen_action_id = observed_chosen_action_id(report.get("observed_rom_decision", {}))
    chosen_candidate = find_candidate(
        report.get("candidate_scores", []),
        chosen_action_id,
    )
    if chosen_candidate is None:
        chosen_candidate = best_candidate(report.get("candidate_scores", []))
    focus_score = optional_score(focus_candidate.get("final_score"))
    chosen_score = optional_score(chosen_candidate.get("final_score")) if chosen_candidate else None
    score_delta = (
        focus_score - chosen_score
        if focus_score is not None and chosen_score is not None
        else None
    )
    flip = report.get("counterfactual", {}).get("focus_score_flip") or {}
    is_observed_choice = action_matches_candidate(focus_candidate, chosen_action_id)
    selector_explanation = focus_selector_explanation_packet(report, focus_candidate)
    return {
        "requested_action_id": focus,
        "found": True,
        "action_id": focus_candidate.get("action_id"),
        "action_label": candidate_action_text(focus_candidate),
        "name": focus_candidate.get("name", focus_candidate.get("action_id")),
        "move_id": focus_candidate.get("move_id"),
        "chosen_action_id": chosen_candidate.get("action_id") if chosen_candidate else chosen_action_id,
        "chosen_action_label": candidate_action_text(chosen_candidate) if chosen_candidate else chosen_action_id,
        "chosen_name": chosen_candidate.get("name") if chosen_candidate else "",
        "is_observed_choice": is_observed_choice,
        "focus_final_score": focus_score,
        "chosen_final_score": chosen_score,
        "score_delta_vs_chosen": score_delta,
        "focus_selector_probability": focus_candidate.get("selector_probability"),
        "chosen_selector_probability": (
            chosen_candidate.get("selector_probability") if chosen_candidate else None
        ),
        "blocked": bool(focus_candidate.get("blocked", False)),
        "score_reason": focus_score_reason(
            focus_candidate,
            chosen_candidate,
            score_delta=score_delta,
            is_observed_choice=is_observed_choice,
        ),
        "focus_rule_deltas": candidate_rule_delta_highlights(
            focus_candidate,
            rom_events=report.get("rom_contributions", {}).get("events", []),
        ),
        "chosen_rule_deltas": (
            candidate_rule_delta_highlights(
                chosen_candidate,
                rom_events=report.get("rom_contributions", {}).get("events", []),
            )
            if chosen_candidate
            else []
        ),
        "selector_explanation": selector_explanation,
        "counterfactual_required_delta": flip.get("required_delta"),
        "summary": focus_action_comparison_text_from_values(
            focus_candidate,
            chosen_candidate,
            score_delta=score_delta,
            flip=flip,
            is_observed_choice=is_observed_choice,
        ),
    }


def available_action_suggestions(
    candidates: list[dict[str, Any]],
    *,
    limit: int = 6,
) -> list[dict[str, Any]]:
    suggestions = []
    seen = set()
    for candidate in candidates:
        label = candidate_action_text(candidate)
        key = label.lower()
        if key in seen:
            continue
        seen.add(key)
        suggestions.append(
            {
                "action_id": candidate.get("action_id"),
                "action_label": label,
                "name": candidate.get("name", ""),
                "move_id": candidate.get("move_id"),
                "slot": candidate.get("slot"),
                "kind": str(candidate.get("kind") or "move"),
                "final_score": candidate.get("final_score"),
                "selector_probability": candidate.get("selector_probability"),
                "blocked": bool(candidate.get("blocked", False)),
                "aliases": candidate_aliases(candidate),
            }
        )
        if len(suggestions) >= limit:
            break
    return suggestions


def candidate_aliases(candidate: dict[str, Any]) -> list[str]:
    aliases = []
    for value in (
        candidate.get("action_id"),
        candidate.get("name"),
        candidate.get("move_id"),
        candidate.get("slot"),
    ):
        if value is None or value == "":
            continue
        text = str(value)
        if text not in aliases:
            aliases.append(text)
    slot = candidate.get("slot")
    if slot is not None:
        slot_text = f"slot{slot}"
        if slot_text not in aliases:
            aliases.append(slot_text)
    return aliases


def focus_selector_explanation_packet(
    report: dict[str, Any],
    focus_candidate: dict[str, Any],
) -> dict[str, Any]:
    selector_path = (
        report.get("observed_rom_decision", {})
        .get("decision", {})
        .get("selector_path", {})
    )
    if not selector_path.get("available"):
        return {}
    best = str(selector_path.get("best_action_id") or "")
    second = str(selector_path.get("second_action_id") or "")
    probability = optional_float(focus_candidate.get("selector_probability"))
    if focus_candidate.get("blocked"):
        rank = "blocked"
        reason = "focused action is blocked by score byte >= 80"
    elif best and action_matches_candidate(focus_candidate, best):
        rank = "best"
        reason = "focused action is the selector best candidate"
    elif second and action_matches_candidate(focus_candidate, second):
        rank = "second"
        reason = (
            "focused action is the selector second candidate and can be picked "
            "by the BossAI_SelectMove roll"
        )
    elif probability == 0.0:
        rank = "outside_selector_roll"
        reason = (
            "focused action has zero selector probability because "
            "BossAI_SelectMove rolls only between the best and second selectable "
            "candidates"
        )
    elif probability is not None and probability > 0.0:
        rank = "nonzero"
        reason = "focused action has nonzero selector probability"
    else:
        rank = "unknown"
        reason = "focused action could not be ranked against the selector path"
    packet = {
        "available": True,
        "rank": rank,
        "action_id": focus_candidate.get("action_id"),
        "selector_probability": probability,
        "best_action_id": best,
        "second_action_id": second,
        "reason": reason,
    }
    packet["summary"] = focus_selector_explanation_text(packet)
    return packet


def focus_selector_explanation_text(packet: dict[str, Any]) -> str:
    rank = packet.get("rank")
    if rank == "best":
        label = "selector best candidate"
    elif rank == "second":
        label = "selector second candidate"
    elif rank == "blocked":
        label = "blocked before selector"
    elif rank == "outside_selector_roll":
        label = "outside nonzero selector set"
    elif rank == "nonzero":
        label = "nonzero selector candidate"
    else:
        label = "selector rank unknown"
    parts = [label, f"p={format_probability(packet.get('selector_probability'))}"]
    if packet.get("best_action_id"):
        parts.append(f"best={packet.get('best_action_id')}")
    if packet.get("second_action_id"):
        parts.append(f"second={packet.get('second_action_id')}")
    return "; ".join(parts)


def focus_score_reason(
    focus_candidate: dict[str, Any],
    chosen_candidate: dict[str, Any] | None,
    *,
    score_delta: int | None,
    is_observed_choice: bool,
) -> str:
    if is_observed_choice:
        return "focused action is the observed ROM choice"
    if focus_candidate.get("blocked"):
        return "focused action is blocked by the final score byte"
    if score_delta is None:
        return "focused action could not be compared against the observed candidate score"
    if score_delta > 0:
        return (
            "focused action scored worse than the observed/chosen candidate "
            f"by {score_delta} byte(s); lower scores are preferred"
        )
    if score_delta == 0:
        return (
            "focused action tied the observed/chosen candidate; selector probability "
            "and slot order determine whether it can be picked"
        )
    return (
        "focused action scored better than the observed/chosen candidate; this usually "
        "means the observed action was selected through a nonzero selector roll"
    )


def candidate_rule_delta_highlights(
    candidate: dict[str, Any],
    *,
    rom_events: list[dict[str, Any]] | None = None,
    limit: int = 4,
) -> list[dict[str, Any]]:
    rom_highlights = [
        {
            "source": "rom_contribution_trace",
            "candidate": candidate.get("action_id"),
            "rule_id": event.get("rule_id"),
            "before": event.get("before"),
            "delta": event.get("delta"),
            "after": event.get("after"),
            "source_anchor": event.get("source_anchor"),
        }
        for event in (rom_events or [])
        if rom_event_matches_candidate(event, candidate)
    ]
    if rom_highlights:
        return rom_highlights[:limit]
    result = []
    for contribution in candidate.get("contributions", [])[:limit]:
        result.append(
            {
                "source": "candidate_score_contribution",
                "candidate": candidate.get("action_id"),
                "rule_id": contribution.get("rule_id"),
                "rule": contribution.get("rule"),
                "before": contribution.get("before"),
                "delta": contribution.get("delta"),
                "after": contribution.get("after"),
                "source_anchor": contribution.get("source_anchor"),
            }
        )
    return result


def rom_event_matches_candidate(
    event: dict[str, Any],
    candidate: dict[str, Any],
) -> bool:
    event_candidate = event.get("candidate", {})
    event_move_id = optional_score(event_candidate.get("move_id"))
    candidate_move_id = optional_score(candidate.get("move_id"))
    if event_move_id is not None and candidate_move_id is not None:
        return event_move_id == candidate_move_id
    event_name = str(event_candidate.get("move_name", "")).strip().lower()
    candidate_names = {
        str(candidate.get("name", "")).strip().lower(),
        str(candidate.get("action_id", "")).strip().lower(),
    }
    if event_name and event_name in candidate_names:
        return True
    event_slot = optional_score(event_candidate.get("slot"))
    candidate_slot = optional_score(candidate.get("slot"))
    if event_slot is not None and candidate_slot is not None:
        return event_slot == candidate_slot
    event_slot_index = optional_score(event_candidate.get("slot_index"))
    candidate_slot_index = optional_score(candidate.get("slot_index"))
    if event_slot_index is not None and candidate_slot_index is not None:
        return event_slot_index == candidate_slot_index
    return False


def find_candidate(
    candidates: list[dict[str, Any]],
    action_id: str,
) -> dict[str, Any] | None:
    if not action_id:
        return None
    for candidate in candidates:
        if action_matches_candidate(candidate, action_id):
            return candidate
    return None


def action_matches_candidate(candidate: dict[str, Any], action_id: str) -> bool:
    focus = action_id.strip().lower()
    if not focus:
        return False
    return focus in {
        str(candidate.get("action_id", "")).lower(),
        str(candidate.get("name", "")).lower(),
        str(candidate.get("move_id", "")).lower(),
        str(candidate.get("slot", "")).lower(),
        f"slot{candidate.get('slot')}".lower(),
    }


def observed_chosen_action_id(rom: dict[str, Any]) -> str:
    decision = rom.get("decision", {})
    selector_path = decision.get("selector_path", {})
    if selector_path.get("chosen_action_id"):
        return str(selector_path.get("chosen_action_id"))
    for key in ("chosen_action_id", "rom_best_action_id"):
        if decision.get(key):
            return str(decision.get(key))
    if rom.get("kind") == "live_trace_selector_replay":
        chosen_slot = optional_trace_int(decision.get("chosen_slot"))
        if chosen_slot is not None:
            return f"slot{chosen_slot + 1}:{decision.get('chosen_move_name', '')}"
    return ""


def best_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    eligible = [
        candidate
        for candidate in candidates
        if optional_score(candidate.get("final_score")) is not None
    ]
    if not eligible:
        return candidates[0] if candidates else None
    return min(
        eligible,
        key=lambda item: (
            int(item.get("final_score", BLOCKED_SCORE)),
            int(item.get("slot") or 99),
        ),
    )


def optional_score(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def optional_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def focus_action_comparison_text_from_values(
    focus_candidate: dict[str, Any],
    chosen_candidate: dict[str, Any] | None,
    *,
    score_delta: int | None,
    flip: dict[str, Any],
    is_observed_choice: bool,
) -> str:
    focus_text = (
        f"{candidate_action_text(focus_candidate)} score="
        f"{focus_candidate.get('final_score')} "
        f"p={format_probability(focus_candidate.get('selector_probability'))}"
    )
    if focus_candidate.get("blocked"):
        focus_text += " blocked=True"
    chosen_text = "unknown chosen action"
    if chosen_candidate:
        chosen_text = (
            f"{candidate_action_text(chosen_candidate)} score="
            f"{chosen_candidate.get('final_score')} "
            f"p={format_probability(chosen_candidate.get('selector_probability'))}"
        )
    delta_text = f"delta_vs_chosen={score_delta}" if score_delta is not None else "delta_vs_chosen=unknown"
    flip_text = ""
    if flip:
        if flip.get("available") is False:
            flip_text = f"; flip_unavailable={flip.get('reason', '')}"
        elif flip.get("required_delta") is not None:
            label = "top_delta" if is_observed_choice else "needs_delta"
            flip_text = f"; {label}={flip.get('required_delta')}"
    observed_text = "observed_choice=True; " if is_observed_choice else ""
    return f"{observed_text}{focus_text} vs {chosen_text}; {delta_text}{flip_text}"


def evidence_highlights_packet(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_scores": candidate_score_highlights(report, limit=4),
        "rule_deltas": rule_delta_highlights(report, limit=4),
        "source_anchors": source_anchor_highlights(report, limit=4),
        "public_inputs": public_input_highlights(report, limit=4),
    }


def candidate_score_highlights(
    report: dict[str, Any],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    highlights = []
    for candidate in report.get("candidate_scores", [])[:limit]:
        highlights.append(
            {
                "action_id": candidate.get("action_id"),
                "kind": candidate.get("kind", "move"),
                "name": candidate.get("name", candidate.get("action_id")),
                "final_score": candidate.get("final_score"),
                "selector_probability": candidate.get("selector_probability"),
                "blocked": candidate.get("blocked"),
            }
        )
    return highlights


def rule_delta_highlights(
    report: dict[str, Any],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    rom_events = report.get("rom_contributions", {}).get("events", [])
    if rom_events:
        return [
            {
                "source": "rom_contribution_trace",
                "candidate": rule_delta_candidate_name(item.get("candidate", {})),
                "rule_id": item.get("rule_id"),
                "before": item.get("before"),
                "delta": item.get("delta"),
                "after": item.get("after"),
                "source_anchor": item.get("source_anchor"),
            }
            for item in rom_events[:limit]
        ]
    highlights = []
    for candidate in report.get("candidate_scores", []):
        for contribution in candidate.get("contributions", []):
            highlights.append(
                {
                    "source": "python_or_live_score_delta",
                    "candidate": candidate.get("action_id"),
                    "rule_id": contribution.get("rule_id"),
                    "rule": contribution.get("rule"),
                    "before": contribution.get("before"),
                    "delta": contribution.get("delta"),
                    "after": contribution.get("after"),
                    "source_anchor": contribution.get("source_anchor"),
                }
            )
            if len(highlights) >= limit:
                return highlights
    return highlights


def rule_delta_candidate_name(candidate: dict[str, Any]) -> str:
    return str(
        candidate.get("move_name")
        or candidate.get("action_id")
        or candidate.get("slot")
        or candidate.get("slot_index")
        or ""
    )


def source_anchor_highlights(
    report: dict[str, Any],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    return [
        {
            "rule_id": anchor.get("rule_id"),
            "source": source_anchor_text(anchor),
            "classification": anchor.get("classification"),
            "public_reads": anchor.get("public_reads", []),
        }
        for anchor in report.get("source_anchors", [])[:limit]
    ]


def public_input_highlights(
    report: dict[str, Any],
    *,
    limit: int,
) -> list[str]:
    public_inputs = report.get("public_info_inputs", {})
    highlights = []
    for key in ("condition_tags", "policy_tags", "answer_changing_information"):
        values = public_inputs.get(key, [])
        if values:
            highlights.append(f"{key}={values[:limit]}")
    trace_fields = public_inputs.get("trace_fields", {})
    if isinstance(trace_fields, dict):
        for key, value in list(trace_fields.items())[:limit]:
            highlights.append(f"trace.{key}={compact_public_value(value)}")
    for branch in public_inputs.get("predicate_branches", [])[:limit]:
        highlights.append(
            "predicate "
            f"{branch.get('predicate_id')}={branch.get('outcome')} "
            f"inputs={branch.get('legal_inputs', [])}"
        )
    for probe in public_inputs.get("public_read_probes", [])[:limit]:
        highlights.append(
            "probe "
            f"{probe.get('probe_id')}={probe.get('outcome')} "
            f"inputs={probe.get('legal_inputs', [])}"
        )
    if not highlights and public_inputs.get("evidence_refs"):
        refs = compact_public_value(public_inputs.get("evidence_refs", [])[:limit])
        highlights.append(f"evidence_refs={refs}")
    return highlights[:limit]


def compact_public_value(value: Any, *, max_length: int = 80) -> str:
    text = str(value)
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def decision_summary_status(rom: dict[str, Any], missing_ids: list[str]) -> str:
    if not rom.get("available"):
        return "needs_rom_proof"
    if not missing_ids:
        return "explained"
    if any(item in missing_ids for item in ("score_bytes", "selector_path")):
        return "needs_selector_or_score_proof"
    return "partial"


def observed_decision_text(rom: dict[str, Any]) -> str:
    if not rom.get("available"):
        return f"ROM decision not attached: {rom.get('reason', '')}"
    decision = rom.get("decision", {})
    kind = str(rom.get("kind", ""))
    if kind == "rom_score_materialization":
        return (
            "ROM score bytes make "
            f"{decision.get('rom_best_action_id')} best "
            f"with score={decision.get('best_score')}"
        )
    if kind == "rom_selector_materialization":
        return (
            "ROM selector chose "
            f"{decision.get('chosen_action_id')} "
            f"({decision.get('chosen_move_name')}) "
            f"with p={format_probability(decision.get('chosen_action_probability'))}"
        )
    if kind == "live_trace_selector_replay":
        return (
            "ROM live trace chose "
            f"{decision.get('chosen_move_name') or decision.get('chosen_id')} "
            f"slot={decision.get('chosen_slot_1_based')} "
            f"score={decision.get('chosen_score')}"
        )
    if kind == "rom_switch_materialization":
        return (
            "ROM switch materialization proposed_switch="
            f"{decision.get('proposed_switch')} actual_switch="
            f"{decision.get('actual_switch')} confidence="
            f"{decision.get('switch_confidence')}"
        )
    return f"ROM evidence kind={kind} status={rom.get('status')} reason={rom.get('reason', '')}"


def decision_why_text(report: dict[str, Any]) -> str:
    rom = report.get("observed_rom_decision", {})
    path = decision_path_text(rom)
    if path:
        return path
    contribution_count = len(report.get("rom_contributions", {}).get("events", []))
    if contribution_count:
        return f"ROM contribution trace has {contribution_count} changed score event(s)."
    mirror = report.get("python_mirror", {})
    if not rom.get("available"):
        mirror_summary = python_mirror_pending_summary_text(mirror)
        if mirror_summary:
            return f"pending ROM proof; {mirror_summary}"
    reason = str(rom.get("reason", ""))
    if reason:
        return reason
    return str(mirror.get("policy_reason", ""))


def python_mirror_pending_summary_text(mirror: dict[str, Any]) -> str:
    if not mirror.get("available"):
        return ""
    best = mirror.get("best_action_id")
    if not best:
        return ""
    parts = [
        f"Python mirror best={best} score={mirror.get('best_score')}",
    ]
    if mirror.get("second_action_id"):
        parts.append(
            f"second={mirror.get('second_action_id')} "
            f"score={mirror.get('second_score')}"
        )
    if mirror.get("gap") is not None:
        parts.append(f"gap={mirror.get('gap')}")
    if mirror.get("best_roll_threshold") is not None:
        parts.append(f"threshold={mirror.get('best_roll_threshold')}/256")
    if mirror.get("policy_verdict"):
        parts.append(f"policy={mirror.get('policy_verdict')}")
    parts.append("lower scores are preferred")
    return "; ".join(parts)


def decision_path_text(rom: dict[str, Any]) -> str:
    if not rom.get("available"):
        return ""
    decision = rom.get("decision", {})
    parts = []
    selector_path = decision.get("selector_path", {})
    if selector_path.get("available"):
        parts.append(selector_path_summary_text(selector_path))
    switch_path = decision.get("switch_path", {})
    if switch_path.get("observed"):
        parts.append(switch_path_summary_text(switch_path))
    if rom.get("kind") == "rom_switch_materialization":
        parts.append(rom_switch_materialization_summary_text(decision))
    return "; ".join(part for part in parts if part)


def switch_path_summary_text(switch_path: dict[str, Any]) -> str:
    roll = switch_path.get("switch_roll", {})
    probability = switch_probability_range(roll)
    probability_text = probability_range_text(probability)
    return (
        f"switch {switch_path.get('observation_status')} "
        f"confidence={switch_path.get('switch_confidence')} "
        f"target={switch_path.get('proposed_target_1_based')} "
        f"switch_probability={probability_text}"
    )


def rom_switch_materialization_summary_text(decision: dict[str, Any]) -> str:
    roll = decision.get("switch_roll", {})
    probability = roll.get("switch_probability")
    if isinstance(probability, (int, float)):
        probability_text = f"{float(probability):.1%}"
    else:
        probability_text = probability_range_text(switch_probability_range(roll))
    return (
        f"switch_materialization status={decision.get('observation_status')} "
        f"confidence={decision.get('switch_confidence')} "
        f"switch_probability={probability_text}"
    )


def python_agreement_text(
    mirror: dict[str, Any],
    rom: dict[str, Any],
) -> str:
    comparison = mirror.get("rom_comparison") or rom.get("python_agreement") or {}
    if comparison.get("available") is False:
        return f"pending: {comparison.get('reason', '')}"
    if "score_bytes_match" in comparison:
        return (
            f"score_bytes_match={comparison.get('score_bytes_match')} "
            f"selector_top_match={comparison.get('selector_top_match')} "
            f"contribution_mismatches={comparison.get('contribution_mismatches')}"
        )
    if "agreement" in comparison:
        return (
            f"agreement={comparison.get('agreement')} "
            f"reason={comparison.get('reason', '')}"
        )
    if "policy_agreement" in comparison:
        return f"policy_agreement={comparison.get('policy_agreement')}"
    return "not available"


def decisive_counterfactual_text(counterfactual: dict[str, Any]) -> str:
    switch_counterfactual = counterfactual.get("switch_roll_counterfactual", {})
    if switch_counterfactual.get("available"):
        probability_text = probability_range_text(
            switch_counterfactual.get("current_probability_range", {})
        )
        return (
            "switch confidence="
            f"{switch_counterfactual.get('confidence')} "
            f"probability={probability_text}; "
            "force_zero_delta="
            f"{switch_counterfactual.get('delta_to_force_zero_probability')} "
            "guarantee_nonzero_delta="
            f"{switch_counterfactual.get('delta_to_guarantee_nonzero_probability')}"
        )
    selector_counterfactual = counterfactual.get("selector_roll_counterfactual", {})
    if selector_counterfactual.get("available"):
        if selector_counterfactual.get("observed_choice_due_to_random_roll"):
            return (
                "selector roll chose second candidate; "
                f"{selector_counterfactual.get('alternate_action_id')} would be chosen "
                "if roll="
                f"{roll_range_text(selector_counterfactual.get('alternate_roll_range', {}))}"
            )
        return (
            "selector roll chose best candidate; "
            f"{selector_counterfactual.get('alternate_action_id')} would be chosen "
            "if roll="
            f"{roll_range_text(selector_counterfactual.get('alternate_roll_range', {}))}"
        )
    flip = decisive_score_flip(counterfactual)
    if flip:
        if flip.get("available") is False:
            return f"{flip.get('action_id')}: {flip.get('reason', 'counterfactual unavailable')}"
        return (
            f"{flip.get('action_id')} score "
            f"{flip.get('current_score')} -> {flip.get('target_score')} "
            f"delta={flip.get('required_delta')}"
        )
    public_facts = counterfactual.get("public_fact_counterfactuals", [])
    if public_facts:
        return str(public_facts[0])
    answer_changing = counterfactual.get("answer_changing_information", [])
    if answer_changing:
        return str(answer_changing[0])
    return "not available"


def decisive_score_flip(counterfactual: dict[str, Any]) -> dict[str, Any] | None:
    focus = counterfactual.get("focus_score_flip")
    if focus:
        return focus
    smallest = counterfactual.get("smallest_score_flip")
    if smallest and smallest.get("available") is False:
        return smallest
    required_delta = optional_score(smallest.get("required_delta")) if smallest else None
    if smallest and required_delta != 0:
        return smallest
    challenger = counterfactual.get("nearest_challenger_score_flip")
    if challenger:
        return challenger
    return smallest


def primary_decision_has_score_bytes(rom: dict[str, Any]) -> bool:
    decision = rom.get("decision", {})
    for key in ("move_scores", "final_scores", "selector_entry_scores", "post_model_scores"):
        if decision.get(key):
            return True
    return False


def score_byte_detail(rom: dict[str, Any]) -> str:
    decision = rom.get("decision", {})
    for key in ("move_scores", "final_scores", "selector_entry_scores", "post_model_scores"):
        values = decision.get(key)
        if values:
            return f"{key}={values}"
    return "no ROM score-byte array attached"


def candidate_contributions_available(candidates: list[dict[str, Any]]) -> bool:
    return any(candidate.get("contributions") for candidate in candidates)


def public_input_baseline_available(public_inputs: dict[str, Any]) -> bool:
    for key in (
        "condition_tags",
        "policy_tags",
        "answer_changing_information",
        "evidence_refs",
        "scenario_public_keys",
    ):
        if public_inputs.get(key):
            return True
    return bool(public_inputs.get("trace_fields"))


def rom_public_read_provenance_available(public_inputs: dict[str, Any]) -> bool:
    return bool(
        public_inputs.get("predicate_branches")
        or public_inputs.get("public_read_probes")
        or public_inputs.get("rom_public_reads_by_rule")
    )


def public_input_detail(public_inputs: dict[str, Any]) -> str:
    return (
        f"policy_tags={len(public_inputs.get('policy_tags', []))} "
        f"condition_tags={len(public_inputs.get('condition_tags', []))} "
        f"evidence_refs={len(public_inputs.get('evidence_refs', []))} "
        f"trace_fields={len(public_inputs.get('trace_fields', {}))}"
    )


def counterfactual_available(counterfactual: dict[str, Any]) -> bool:
    return bool(
        counterfactual.get("focus_score_flip")
        or counterfactual.get("smallest_score_flip")
        or counterfactual.get("nearest_challenger_score_flip")
        or counterfactual.get("selector_roll_counterfactual")
        or counterfactual.get("switch_roll_counterfactual")
        or counterfactual.get("public_fact_counterfactuals")
        or counterfactual.get("answer_changing_information")
    )


def report_has_switch_materialization(report: dict[str, Any]) -> bool:
    if report.get("observed_rom_decision", {}).get("kind") == "rom_switch_materialization":
        return True
    return any(
        item.get("kind") == "rom_switch_materialization"
        for item in report.get("rom_evidence", [])
    )


def report_has_proven_switch_materialization(report: dict[str, Any]) -> bool:
    candidates = [report.get("observed_rom_decision", {})]
    candidates.extend(report.get("rom_evidence", []))
    return any(
        item.get("kind") == "rom_switch_materialization"
        and item.get("status") == "pass"
        for item in candidates
    )


def report_has_switch_candidate(report: dict[str, Any]) -> bool:
    if str(report.get("family", "")) in SWITCH_MATERIALIZE_FAMILIES:
        return True
    return any(
        str(candidate.get("kind", "")) == "switch"
        for candidate in report.get("candidate_scores", [])
    )


def prioritized_next_proof_command(
    commands: list[dict[str, Any]],
    missing_ids: list[str],
) -> dict[str, Any]:
    if not commands:
        return {}
    if "hash_basis.current" in missing_ids:
        command = first_command_matching(commands, ("refresh", "hash basis"))
        if command:
            return command
    if "observed_rom_decision" in missing_ids or "score_bytes" in missing_ids:
        command = first_command_matching(commands, ("ROM proof", "materialize", "trace-replay"))
        if command:
            return command
    if "switch_materialization" in missing_ids:
        command = first_command_matching(
            commands,
            ("generate switch/sack probes", "rom-switch-materialize", "switch-dispatch"),
        )
        if command:
            return command
    if "rom_contribution_deltas" in missing_ids or "rom_public_read_provenance" in missing_ids:
        command = first_command_matching(
            commands,
            (
                "rom-contribution-trace",
                "live-route rom contribution trace",
                "capture rom score-rule contribution",
            ),
        )
        if command:
            return command
        command = first_command_matching(commands, ("contribution",))
        if command:
            return command
    if "selector_path" in missing_ids:
        command = first_command_matching(commands, ("selector", "ROM proof", "trace-replay"))
        if command:
            return command
    if "source_anchors" in missing_ids:
        command = first_command_matching(commands, ("rule-map", "source-rule"))
        if command:
            return command
    return commands[0]


def next_proof_chain(
    commands: list[dict[str, Any]],
    missing_ids: list[str],
    next_command: dict[str, Any],
) -> list[dict[str, Any]]:
    if not next_command:
        return []
    chain = [next_command]
    if "hash_basis.current" in missing_ids and command_matches(
        next_command,
        ("refresh", "hash basis"),
    ):
        for command in commands:
            if command_matches(command, ("refresh", "hash basis")) and command not in chain:
                chain.append(command)
        materialize = first_command_matching(
            commands,
            ("rom-switch-materialize", "materialize switch-dispatch proof"),
        )
        if materialize and materialize not in chain:
            chain.append(materialize)
    if "switch_materialization" in missing_ids and command_matches(
        next_command,
        ("generate switch/sack probes", "rom-switch-materialize", "switch-dispatch"),
    ):
        materialize = first_command_matching(
            commands,
            ("rom-switch-materialize", "materialize switch-dispatch proof"),
        )
        if materialize and materialize != next_command:
            chain.append(materialize)
        render = first_command_matching(
            commands,
            ("render switch-dispatch explanation packet", "rom-switch-materialization"),
        )
        if render and render not in chain:
            chain.append(render)
    if (
        "rom_contribution_deltas" in missing_ids
        or "rom_public_read_provenance" in missing_ids
    ) and command_matches(
        next_command,
        ("rom-contribution-trace", "capture rom score-rule contribution"),
    ):
        follow_up = first_command_matching(
            commands,
            (
                "re-render this live-trace packet after contribution capture",
                "re-render this live-trace packet with attached rule deltas",
                "re-render this scenario packet after contribution capture",
            ),
        )
        if follow_up and follow_up != next_command:
            chain.append(follow_up)
    return chain


def first_command_matching(
    commands: list[dict[str, Any]],
    needles: tuple[str, ...],
) -> dict[str, Any] | None:
    for command in commands:
        if command_matches(command, needles):
            return command
    return None


def command_matches(command: dict[str, Any], needles: tuple[str, ...]) -> bool:
    lowered = tuple(needle.lower() for needle in needles)
    text = f"{command.get('purpose', '')} {command.get('command', '')}".lower()
    return any(needle in text for needle in lowered)


def next_proof_reason(
    missing_ids: list[str],
    next_command: dict[str, Any],
) -> str:
    if not next_command:
        return "no follow-up command available"
    closed = [
        item
        for item in next_command.get("closes_evidence_ids", [])
        if item in missing_ids
    ]
    if closed:
        return "next command closes missing evidence: " + ", ".join(closed)
    if missing_ids:
        return "closes first missing evidence: " + ", ".join(missing_ids[:3])
    return "all compact explanation evidence is present; rerun the first proof command to reproduce"


def next_proof_commands(
    scenarios_path: Path,
    scenario_id: str,
    scenario: dict[str, Any],
    *,
    focus_action_id: str | None,
    has_rom_evidence: bool,
    has_rom_contributions: bool,
    existing_rom_contribution_paths: list[Path],
) -> list[dict[str, Any]]:
    scenario_args = f"--scenario {quote_cli(scenarios_path)} --scenario-id {quote_cli(scenario_id)}"
    focus_args = (
        f" --focus-action-id {quote_cli(focus_action_id)}"
        if focus_action_id
        else ""
    )
    proof_kind = auto_rom_proof_kind(scenario)
    commands = [
        proof_command(
            purpose="Python score waterfall and selector surface",
            command=f"python -m tools.boss_ai_debugger decision-trace {scenario_args}",
            closes_evidence_ids=[
                "candidate_scores",
                "python_score_contributions",
            ],
        ),
        proof_command(
            purpose="Smallest score/public-fact flip",
            command=f"python -m tools.boss_ai_debugger counterfactual {scenario_args}",
            closes_evidence_ids=["counterfactual"],
        ),
    ]
    if not has_rom_contributions:
        out = temp_artifact_name(scenario_id, "python_contribution")
        commands.append(
            proof_command(
                purpose="Normalize Python contribution stream for ROM/Python delta comparison",
                command=(
                    "python -m tools.boss_ai_debugger python-contribution-trace "
                    f"--scenarios {quote_cli(scenarios_path)} --json-out {quote_cli(out)}"
                ),
                closes_evidence_ids=["python_score_contributions"],
                expected_output_paths=[out],
            )
        )
    if not has_rom_evidence:
        commands.append(
            one_scenario_rom_proof_command(
                scenarios_path,
                scenario_id,
                focus_action_id=focus_action_id,
                proof_kind=proof_kind,
            )
        )
    elif not has_rom_contributions and proof_kind == "score":
        commands.append(
            one_scenario_rom_proof_command(
                scenarios_path,
                scenario_id,
                focus_action_id=focus_action_id,
                proof_kind=proof_kind,
            )
        )
    if existing_rom_contribution_paths:
        trace_args = " ".join(
            f"--rom-contribution-trace {quote_cli(path)}"
            for path in existing_rom_contribution_paths
        )
        commands.append(
            proof_command(
                purpose="Compare scenario policy, live selector replay, and attached contribution artifacts",
                command=(
                    "python -m tools.boss_ai_debugger diff "
                    f"--scenarios {quote_cli(scenarios_path)} {trace_args}"
                ),
                consumes_artifact_paths=existing_rom_contribution_paths,
            )
        )
    else:
        contribution_out = temp_artifact_name(scenario_id, "rom_contribution")
        commands.append(
            proof_command(
                purpose="Live-route ROM contribution trace for rule/source/public-read evidence",
                command=(
                    "python -m tools.boss_ai_debugger rom-contribution-trace "
                    f"--boss-route {DEFAULT_SCORE_MATERIALIZE_ROUTE} "
                    f"--json-out {quote_cli(contribution_out)}"
                ),
                closes_evidence_ids=[
                    "rom_contribution_deltas",
                    "rom_public_read_provenance",
                ],
                expected_output_paths=[contribution_out],
            )
        )
        commands.append(
            proof_command(
                purpose="Re-render this scenario packet after contribution capture",
                command=(
                    "python -m tools.boss_ai_debugger explain-decision "
                    f"{scenario_args}{focus_args} --run-rom-proof auto "
                    f"--rom-contribution-trace {quote_cli(contribution_out)}"
                ),
                closes_evidence_ids=[
                    "rom_contribution_deltas",
                    "rom_public_read_provenance",
                ],
                consumes_artifact_paths=[contribution_out],
            )
        )
    commands.append(
        proof_command(
            purpose="Verify source-rule anchors are current",
            command="python -m tools.boss_ai_debugger rule-map check",
            closes_evidence_ids=["source_anchors"],
        )
    )
    return commands


def one_scenario_rom_proof_command(
    path: Path,
    scenario_id: str,
    *,
    focus_action_id: str | None,
    proof_kind: str,
) -> dict[str, Any]:
    focus_args = (
        f" --focus-action-id {quote_cli(focus_action_id)}"
        if focus_action_id
        else ""
    )
    focus_segment = f"{focus_args.strip()} " if focus_args else ""
    purpose = {
        "switch": "Exact one-scenario ROM proof: switch-dispatch packet",
        "score": "Exact one-scenario ROM proof: score packet",
        "selector": "Exact one-scenario ROM proof: selector packet",
    }.get(proof_kind, "Exact one-scenario ROM proof packet")
    out = temp_artifact_name(scenario_id, "rom_proof")
    closes = {
        "switch": [
            "observed_rom_decision",
            "switch_path",
            "switch_materialization",
        ],
        "score": ["observed_rom_decision", "score_bytes", "selector_path"],
        "selector": ["observed_rom_decision", "score_bytes", "selector_path"],
    }.get(proof_kind, ["observed_rom_decision"])
    return proof_command(
        purpose=purpose,
        command=(
            "python -m tools.boss_ai_debugger explain-decision "
            f"--scenario {quote_cli(path)} --scenario-id {quote_cli(scenario_id)} "
            f"{focus_segment}--run-rom-proof auto "
            f"--json-out {quote_cli(out)}"
        ),
        closes_evidence_ids=closes,
        expected_output_paths=[out],
    )


def known_limits(
    primary_rom: dict[str, Any],
    rom_contributions: dict[str, Any],
) -> list[str]:
    limits = [
        "Python candidate scores are a scenario mirror unless a ROM materialization artifact is attached or run.",
        "ROM contribution deltas are reported only for attached or generated trace artifacts with matching trace ids.",
    ]
    if not primary_rom.get("available"):
        limits.append("Observed ROM decision is pending; run the suggested materialization command for ROM-backed proof.")
    if rom_contributions.get("unmatched_trace_ids"):
        limits.append("Some ROM contribution traces were loaded but did not match this scenario id.")
    return limits


def scenario_keys(selected_id: str, scenario_key: str) -> set[str]:
    return {
        selected_id,
        scenario_key,
        f"scenario:{selected_id}",
        f"scenario:{scenario_key}",
        f"route:{scenario_key}",
    }


def quote_cli(value: Path | str) -> str:
    text = str(value)
    if not text:
        return '""'
    if re.search(r"\s", text):
        return '"' + text.replace('"', '\\"') + '"'
    return text


def temp_artifact_name(scenario_id: str, suffix: str) -> str:
    return f".local\\tmp\\boss_ai_debugger\\{safe_id(scenario_id)}_{suffix}.json"


def safe_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return cleaned or "decision"


def format_probability(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.1%}"
    return "unknown"


def probability_range_text(value: dict[str, Any]) -> str:
    if {"min", "max"}.issubset(value) and isinstance(value["min"], (int, float)):
        return f"{float(value['min']):.1%}-{float(value['max']):.1%}"
    return "unknown"


def selector_threshold_text(selector_path: dict[str, Any]) -> str:
    threshold = selector_path.get("best_roll_threshold")
    return f"{threshold}/256" if threshold is not None else "single-candidate"


def selector_probability_text(selector_path: dict[str, Any]) -> str:
    probabilities = selector_path.get("candidate_probabilities", {})
    if not isinstance(probabilities, dict):
        return "unknown"
    active = [
        (action_id, float(probability))
        for action_id, probability in probabilities.items()
        if float(probability) > 0.0
    ]
    if not active:
        return "none"
    return ", ".join(
        f"{action_id}={probability:.1%}" for action_id, probability in active
    )


def selector_path_summary_text(selector_path: dict[str, Any]) -> str:
    return (
        f"selector best={selector_path.get('best_action_id')} "
        f"score={selector_path.get('best_score')} "
        f"second={selector_path.get('second_action_id')} "
        f"score={selector_path.get('second_score')} "
        f"gap={selector_path.get('score_gap')} "
        f"threshold={selector_threshold_text(selector_path)} "
        f"prob={selector_probability_text(selector_path)}"
    )


def candidate_score_highlights_text(items: list[dict[str, Any]]) -> str:
    return ", ".join(
        f"{candidate_action_text(item)}={item.get('final_score')} "
        f"p={format_probability(item.get('selector_probability'))}"
        for item in items
    )


def available_action_suggestions_text(items: list[dict[str, Any]]) -> str:
    return ", ".join(available_action_suggestion_text(item) for item in items)


def available_action_suggestion_text(item: dict[str, Any]) -> str:
    label = str(item.get("action_label") or item.get("action_id") or "")
    name = str(item.get("name") or "")
    if name and name.lower() not in {
        label.lower(),
        str(item.get("action_id") or "").lower(),
    } and not label.lower().endswith(f":{name.lower()}"):
        label = f"{label}({name})"
    return label


def candidate_action_text(item: dict[str, Any]) -> str:
    kind = str(item.get("kind") or "move")
    action_id = str(item.get("action_id", ""))
    if kind and kind != "move":
        return f"{action_id}[{kind}]"
    return action_id


def rule_delta_highlights_text(items: list[dict[str, Any]]) -> str:
    return "; ".join(rule_delta_highlight_text(item) for item in items)


def rule_delta_highlight_text(item: dict[str, Any]) -> str:
    rule = item.get("rule_id") or item.get("rule")
    return (
        f"{item.get('candidate')} {rule}: "
        f"{item.get('before')} {format_signed_delta(item.get('delta'))} "
        f"-> {item.get('after')}"
    )


def format_signed_delta(value: Any) -> str:
    if isinstance(value, int):
        return f"{value:+d}"
    return str(value)


def source_anchor_highlights_text(items: list[dict[str, Any]]) -> str:
    return "; ".join(
        f"{item.get('rule_id')}@{item.get('source')}" for item in items
    )


def proof_command_metadata_text(
    command: dict[str, Any],
    *,
    include_empty: bool = False,
) -> str:
    chunks = []
    closes = list(command.get("closes_evidence_ids") or [])
    writes = list(command.get("expected_output_paths") or [])
    consumes = list(command.get("consumes_artifact_paths") or [])
    if closes:
        chunks.append(f"closes={compact_action_list(closes, limit=6)}")
    elif include_empty:
        chunks.append("closes=none")
    if writes:
        chunks.append(f"writes={compact_action_list(writes, limit=3)}")
    if consumes:
        chunks.append(f"uses={compact_action_list(consumes, limit=3)}")
    return "; ".join(chunks)


def format_explain_decision(report: dict[str, Any], *, limit: int = 12) -> str:
    lines = [
        "Boss AI decision explanation",
        (
            f"scenario={report['scenario_id']} family={report.get('family', '')} "
            f"tier={report.get('tier')}"
        ),
    ]
    decision_input = report.get("decision_input") or {}
    if decision_input:
        resolution = decision_input.get("resolution", {})
        replay = decision_input.get("replay_verification", {})
        lines.append(
            "input="
            f"auto source={resolution.get('source')} "
            f"route={decision_input.get('target', {}).get('boss_route')} "
            f"manifest={decision_input.get('artifact_path')} "
            f"replay_verified={replay.get('verified')}"
        )
    marker = report.get("deity_evidence_marker")
    if marker:
        closed = report.get("closed_evidence_ids", [])
        lines.append(
            f"deity_marker={marker} closed={compact_action_list(closed, limit=8)}"
        )
    summary = report.get("decision_summary", {})
    if summary:
        lines.extend(
            [
                "",
                (
                    "Answer: "
                    f"status={summary.get('status')} "
                    f"observed={summary.get('observed')}"
                ),
            ]
        )
        if summary.get("why"):
            lines.append(f"  why={summary.get('why')}")
        policy_expectation = summary.get("policy_expectation") or {}
        if policy_expectation.get("available"):
            lines.append(f"  policy={policy_expectation.get('summary')}")
        selector_choice = summary.get("selector_choice_explanation") or {}
        if selector_choice.get("available"):
            lines.append(f"  selector={selector_choice.get('summary')}")
        if summary.get("python_agreement"):
            lines.append(f"  python={summary.get('python_agreement')}")
        if summary.get("decisive_counterfactual"):
            lines.append(
                f"  counterfactual={summary.get('decisive_counterfactual')}"
            )
        focus = summary.get("focus_action_comparison") or {}
        if focus:
            if focus.get("found"):
                lines.append(f"  focus={focus.get('summary')}")
                if focus.get("score_reason"):
                    lines.append(f"  focus_reason={focus.get('score_reason')}")
                selector_explanation = focus.get("selector_explanation") or {}
                if selector_explanation.get("available"):
                    lines.append(
                        f"  focus_selector={selector_explanation.get('summary')}"
                    )
                if focus.get("focus_rule_deltas"):
                    lines.append(
                        "  "
                        "focus_rules="
                        f"{rule_delta_highlights_text(focus.get('focus_rule_deltas', []))}"
                    )
                if focus.get("chosen_rule_deltas"):
                    lines.append(
                        "  "
                        "chosen_rules="
                        f"{rule_delta_highlights_text(focus.get('chosen_rule_deltas', []))}"
                    )
            else:
                focus_line = (
                    f"focus={focus.get('requested_action_id')} "
                    f"missing: {focus.get('reason')}"
                )
                available = focus.get("available_actions") or []
                if available:
                    focus_line += (
                        f"; available={available_action_suggestions_text(available)}"
                    )
                lines.append(f"  {focus_line}")
        evidence = summary.get("evidence_highlights") or {}
        scores = evidence.get("candidate_scores") or []
        if scores:
            lines.append(f"  scores={candidate_score_highlights_text(scores)}")
        rule_deltas = evidence.get("rule_deltas") or []
        if rule_deltas:
            lines.append(f"  rules={rule_delta_highlights_text(rule_deltas)}")
        anchors = evidence.get("source_anchors") or []
        if anchors:
            lines.append(f"  anchors={source_anchor_highlights_text(anchors)}")
        public_inputs = evidence.get("public_inputs") or []
        if public_inputs:
            lines.append(f"  public={'; '.join(public_inputs)}")
        next_command = summary.get("next_proof_command") or {}
        if next_command:
            lines.append(
                "  "
                f"next={next_command.get('purpose')}: "
                f"{next_command.get('command')}"
            )
            detail = proof_command_metadata_text(next_command)
            if detail:
                lines.append(f"  next_meta={detail}")
        next_chain = summary.get("next_proof_chain") or []
        for follow_up in next_chain[1:]:
            lines.append(
                "  "
                f"then={follow_up.get('purpose')}: "
                f"{follow_up.get('command')}"
            )
            detail = proof_command_metadata_text(follow_up)
            if detail:
                lines.append(f"  then_meta={detail}")
    rom = report["observed_rom_decision"]
    lines.append("")
    if rom.get("available"):
        lines.append(
            f"Observed ROM: {rom.get('kind')} status={rom.get('status')} "
            f"reason={rom.get('reason', '')}"
        )
        decision = rom.get("decision", {})
        if rom.get("kind") == "rom_score_materialization":
            lines.append(
                "  "
                f"rom_best={decision.get('rom_best_action_id')} "
                f"possible={decision.get('possible_action_ids', [])} "
                f"scores={decision.get('final_scores', [])}"
            )
            selector_path = decision.get("selector_path", {})
            if selector_path.get("available"):
                lines.append("  " + selector_path_summary_text(selector_path))
        elif rom.get("kind") == "rom_selector_materialization":
            lines.append(
                "  "
                f"chosen={decision.get('chosen_action_id')} "
                f"move={decision.get('chosen_move_name')} "
                f"p={decision.get('chosen_action_probability')} "
                f"scores={decision.get('move_scores', [])}"
            )
            selector_path = decision.get("selector_path", {})
            if selector_path.get("available"):
                lines.append("  " + selector_path_summary_text(selector_path))
        elif rom.get("kind") == "live_trace_selector_replay":
            lines.append(
                "  "
                f"chosen={decision.get('chosen_move_name')} "
                f"id={decision.get('chosen_id')} "
                f"slot={decision.get('chosen_slot_1_based')} "
                f"slot_index={decision.get('chosen_slot_index')} "
                f"score={decision.get('chosen_score')} "
                f"possible_actions={decision.get('possible_action_ids', [])} "
                f"possible_move_ids={decision.get('possible_move_ids', [])} "
                f"scores={decision.get('move_scores', [])}"
            )
            selector_path = decision.get("selector_path", {})
            if selector_path.get("available"):
                lines.append("  " + selector_path_summary_text(selector_path))
            switch_path = decision.get("switch_path", {})
            if switch_path.get("observed"):
                roll = switch_path.get("switch_roll", {})
                possible = roll.get("possible_switch_probabilities", [])
                if possible:
                    low = min(float(item["switch_probability"]) for item in possible)
                    high = max(float(item["switch_probability"]) for item in possible)
                    probability_text = f"{low:.1%}-{high:.1%}"
                else:
                    probability_text = "unknown"
                lines.append(
                    "  "
                    f"switch_path={switch_path.get('observation_status')} "
                    f"confidence={switch_path.get('switch_confidence')} "
                    f"param={switch_path.get('switch_param')} "
                    f"index={switch_path.get('switch_index')} "
                    f"target={switch_path.get('proposed_target_1_based')} "
                    f"switch_probability={probability_text}"
                )
        elif rom.get("kind") == "rom_switch_materialization":
            roll = decision.get("switch_roll", {})
            switch_probability = roll.get("switch_probability")
            probability_text = (
                f"{switch_probability:.1%}"
                if isinstance(switch_probability, float)
                else "unknown"
            )
            lines.append(
                "  "
                f"proposed_switch={decision.get('proposed_switch')} "
                f"confidence={decision.get('switch_confidence')} "
                f"switch_probability={probability_text}"
            )
        else:
            lines.append(f"  decision={decision}")
    else:
        lines.append(f"Observed ROM: {rom.get('status')} - {rom.get('reason')}")

    mirror = report["python_mirror"]
    lines.extend(
        [
            "",
            (
                "Python mirror: "
                f"best={mirror.get('best_action_id')} "
                f"second={mirror.get('second_action_id')} "
                f"gap={mirror.get('gap')} "
                f"policy={mirror.get('policy_verdict')}"
            ),
            "",
            "Proof status:",
        ]
    )
    proof = report.get("proof_status", {})
    if proof:
        if proof.get("status"):
            lines.append(f"  status={proof.get('status')}")
        lines.append(f"  present={proof.get('present_ids', [])}")
        lines.append(f"  missing={proof.get('missing_ids', [])}")
        for blocker in proof.get("blockers", []):
            lines.append(
                "  "
                f"blocker={blocker.get('status')} "
                f"{blocker.get('proof_kind')}: {blocker.get('reason')}"
            )
        next_command = proof.get("next_proof_command") or {}
        if next_command:
            lines.append(
                "  "
                f"next={next_command.get('purpose')}: {next_command.get('command')}"
            )
            detail = proof_command_metadata_text(next_command)
            if detail:
                lines.append(f"  next_meta={detail}")
        next_chain = proof.get("next_proof_chain") or []
        for follow_up in next_chain[1:]:
            lines.append(
                "  "
                f"then={follow_up.get('purpose')}: {follow_up.get('command')}"
            )
            detail = proof_command_metadata_text(follow_up)
            if detail:
                lines.append(f"  then_meta={detail}")
        if proof.get("next_proof_reason"):
            lines.append(f"  reason={proof.get('next_proof_reason')}")
    lines.extend(
        [
            "Candidate scores:",
        ]
    )
    for candidate in report["candidate_scores"][:limit]:
        lines.append(
            "  "
            f"slot={candidate['slot']} {candidate_action_text(candidate)} "
            f"{candidate['initial_score']} -> {candidate['pre_lookahead_score']} "
            f"-> {candidate['final_score']} "
            f"p={candidate['selector_probability']:.1%} "
            f"blocked={candidate['blocked']}"
        )
        for contribution in candidate.get("contributions", [])[:3]:
            lines.append(
                "    "
                f"{contribution['rule']}: {contribution['before']} "
                f"{contribution['delta']:+d} -> {contribution['after']}"
                if isinstance(contribution.get("delta"), int)
                else f"    {contribution['rule']}: no score delta"
            )

    rom_contrib = report["rom_contributions"]
    if rom_contrib["events"]:
        lines.extend(["", f"ROM contribution deltas (first {limit}):"])
        for item in rom_contrib["events"][:limit]:
            candidate = item.get("candidate", {})
            anchor = item.get("source_anchor") or {}
            source_text = source_anchor_text(anchor)
            lines.append(
                "  "
                f"{candidate.get('move_name', '') or candidate.get('slot_index')} "
                f"{item.get('rule_id')}: {item.get('before')} "
                f"{item.get('delta'):+d} -> {item.get('after')} "
                f"{source_text}"
            )
    elif rom_contrib.get("available"):
        lines.extend(
            [
                "",
                (
                    "ROM contribution deltas: no matching changed events "
                    f"(unmatched={rom_contrib.get('unmatched_trace_ids', [])})"
                ),
            ]
        )

    counterfactual = report["counterfactual"]
    lines.append("")
    flip = decisive_score_flip(counterfactual)
    if flip:
        if flip.get("available") is False:
            lines.append(
                "Counterfactual: "
                f"{flip.get('action_id')} unavailable: "
                f"{flip.get('reason', 'score flip unavailable')}"
            )
        else:
            lines.append(
                "Counterfactual: "
                f"{flip.get('action_id')} score {flip.get('current_score')} -> "
                f"{flip.get('target_score')} delta={flip.get('required_delta')}"
            )
    selector_counterfactual = counterfactual.get("selector_roll_counterfactual", {})
    if selector_counterfactual.get("available"):
        lines.append(
            "Selector roll counterfactual: "
            f"{selector_counterfactual.get('summary')}"
        )
    switch_counterfactual = counterfactual.get("switch_roll_counterfactual", {})
    if switch_counterfactual.get("available"):
        probability = switch_counterfactual.get("current_probability_range", {})
        if isinstance(probability, dict) and {"min", "max"}.issubset(probability):
            probability_text = f"{probability['min']:.1%}-{probability['max']:.1%}"
        else:
            probability_text = "unknown"
        lines.append(
            "Switch counterfactual: "
            f"confidence={switch_counterfactual.get('confidence')} "
            f"switch_probability={probability_text}; "
            "force_zero_at_or_below="
            f"{switch_counterfactual.get('zero_probability_if_confidence_at_most')} "
            "delta="
            f"{switch_counterfactual.get('delta_to_force_zero_probability')}; "
            "guarantee_nonzero_at="
            f"{switch_counterfactual.get('nonzero_guaranteed_at_confidence')} "
            "delta="
            f"{switch_counterfactual.get('delta_to_guarantee_nonzero_probability')}"
        )
    for item in counterfactual.get("public_fact_counterfactuals", [])[:3]:
        lines.append(f"  - {item}")

    anchors = report.get("source_anchors", [])
    if anchors:
        lines.extend(["", "Source anchors:"])
        for anchor in anchors[:limit]:
            lines.append(f"  - {source_anchor_text(anchor)} {anchor.get('rule_id')}")

    public_inputs = report["public_info_inputs"]
    lines.extend(
        [
            "",
            "Public-info inputs:",
            f"  condition_tags={public_inputs.get('condition_tags', [])}",
            f"  policy_tags={public_inputs.get('policy_tags', [])}",
        ]
    )
    if public_inputs.get("predicate_branches"):
        for branch in public_inputs["predicate_branches"][:3]:
            lines.append(
                "  "
                f"predicate {branch.get('predicate_id')}={branch.get('outcome')} "
                f"inputs={branch.get('legal_inputs', [])}"
            )

    lines.extend(["", "Next proof commands:"])
    for command in report["next_proof_commands"][:limit]:
        lines.append(f"  - {command['purpose']}: {command['command']}")
        detail = proof_command_metadata_text(command, include_empty=True)
        if detail:
            lines.append(f"    {detail}")

    lines.extend(["", "Known limits:"])
    for item in report["known_limits"]:
        lines.append(f"  - {item}")
    return "\n".join(lines)


def source_anchor_text(anchor: dict[str, Any] | None) -> str:
    if not anchor:
        return "[unmapped]"
    source_file = anchor.get("source_file") or ""
    line = anchor.get("line")
    if source_file and line:
        return f"{source_file}:{line}"
    label = anchor.get("source_label") or anchor.get("rule_id", "")
    return label or "[unmapped]"


def write_explain_decision_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
