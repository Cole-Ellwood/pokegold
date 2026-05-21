from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError


AI_TIER_EARLY = 1
AI_TIER_MID = 2
AI_TIER_LATE = 3
BLOCKED_SCORE = 80
MIN_SELECTABLE_SCORE = 1
MAX_SELECTABLE_SCORE = 79
DEFAULT_BASE_SCORE = 20
DEFAULT_LOOKAHEAD_MARGIN = 18
DEFAULT_LOOKAHEAD_N = 4
DEFAULT_MIN_BEST_PROBABILITY = 0.5
NUM_MOVES = 4

TIER_NAMES = {
    "early": AI_TIER_EARLY,
    "mid": AI_TIER_MID,
    "late": AI_TIER_LATE,
}


@dataclass(frozen=True)
class ScoreEvent:
    rule: str
    before: int
    delta: int | None
    after: int
    note: str


@dataclass(frozen=True)
class ScoredMove:
    slot: int
    action_id: str
    name: str
    initial_score: int
    pre_lookahead_score: int
    final_score: int
    blocked: bool
    lookahead_delta: int
    lookahead_applied: bool
    events: list[ScoreEvent]


@dataclass(frozen=True)
class ScenarioVerdict:
    scenario_id: str
    verdict: str
    severity: int
    rom_best_action_id: str | None
    rom_best_probability: float
    expected_best_action_ids: list[str]
    expected_acceptable_action_ids: list[str]
    rolled_bad_action_ids: list[str]
    rolled_catastrophic_action_ids: list[str]
    zero_probability_best_action_ids: list[str]
    policy_tags: list[str]
    condition_tags: list[str]
    lesson_type: str
    confidence: str
    evidence_refs: list[str]
    why: str
    answer_changing_information: list[str]
    reason: str
    result: dict[str, Any]


def load_scenario(path: Path | None, builtin: str | None) -> dict[str, Any]:
    if path is not None and builtin is not None:
        raise PreferenceDataError("use either --scenario or --builtin, not both")
    if builtin is not None:
        return builtin_scenario(builtin)
    if path is None:
        raise PreferenceDataError("missing --scenario or --builtin")
    return json.loads(path.read_text(encoding="utf-8"))


def load_scenario_batch(
    path: Path,
    expectations_path: Path | None = None,
) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        scenarios = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            scenarios = data
        elif isinstance(data, dict) and isinstance(data.get("scenarios"), list):
            scenarios = data["scenarios"]
        elif isinstance(data, dict):
            scenarios = [data]
        else:
            raise PreferenceDataError(
                "batch file must be a scenario, list, object with scenarios, or JSONL"
            )
    if not all(isinstance(item, dict) for item in scenarios):
        raise PreferenceDataError("each batch scenario must be an object")
    scenarios = list(scenarios)
    if expectations_path is None:
        return scenarios

    expectations = load_expectation_map(expectations_path)
    return [merge_expectation(scenario, expectations) for scenario in scenarios]


def load_expectation_map(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict) and isinstance(data.get("expectations"), list):
        rows = data["expectations"]
    elif isinstance(data, dict):
        rows = [data]
    else:
        raise PreferenceDataError(
            "expectations file must be an expectation, list, or object with expectations"
        )

    expectations: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise PreferenceDataError("each expectation row must be an object")
        scenario_id = row.get("scenario_id")
        if not isinstance(scenario_id, str) or not scenario_id:
            raise PreferenceDataError("each expectation row needs scenario_id")
        expectations[scenario_id] = normalize_expectation(row)
    return expectations


def merge_expectation(
    scenario: dict[str, Any],
    expectations: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    scenario_id = scenario.get("id")
    if not isinstance(scenario_id, str) or scenario_id not in expectations:
        return scenario
    merged = dict(scenario)
    existing = scenario_expectation(scenario)
    merged_expectation = {**expectations[scenario_id], **existing}
    merged["expectation"] = merged_expectation
    return merged


def normalize_expectation(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise PreferenceDataError("expectation must be an object")

    action_sets = raw.get("expect", raw.get("expectation", raw))
    if not isinstance(action_sets, dict):
        raise PreferenceDataError("expectation expect field must be an object")

    normalized = dict(action_sets)
    for key in (
        "policy_tags",
        "condition_tags",
        "lesson_type",
        "confidence",
        "evidence_refs",
        "branch_caveats",
        "catastrophe_branches",
        "answer_changing_information",
        "why",
        "min_best_probability",
    ):
        if key in raw:
            normalized[key] = raw[key]

    return normalized


def builtin_scenario(name: str) -> dict[str, Any]:
    if name == "all_equal_late":
        return {
            "id": "all_equal_late",
            "tier": "late",
            "notes": [
                "All four moves remain at the ROM default score.",
                "This exposes BossAI_SelectMove's best-vs-second slot bias.",
            ],
            "moves": [
                {"id": "slot1", "name": "Slot 1"},
                {"id": "slot2", "name": "Slot 2"},
                {"id": "slot3", "name": "Slot 3"},
                {"id": "slot4", "name": "Slot 4"},
            ],
        }
    if name == "third_best_never_selected":
        return {
            "id": "third_best_never_selected",
            "tier": "late",
            "notes": [
                "Slot 1 is best; slots 2 and 3 are tied for second.",
                "The selector only rolls between best and the first second-best slot.",
            ],
            "moves": [
                {
                    "id": "best",
                    "name": "Best",
                    "deltas": [{"rule": "small encourage", "delta": -1}],
                },
                {"id": "second_a", "name": "Second A"},
                {"id": "second_b", "name": "Second B"},
                {
                    "id": "worse",
                    "name": "Worse",
                    "deltas": [{"rule": "small discourage", "delta": 1}],
                },
            ],
        }
    known = ", ".join(["all_equal_late", "third_best_never_selected"])
    raise PreferenceDataError(f"unknown builtin scenario {name!r}; known: {known}")


def normalize_tier(value: Any) -> int:
    if isinstance(value, str):
        key = value.strip().lower()
        try:
            return TIER_NAMES[key]
        except KeyError as exc:
            raise PreferenceDataError(f"unknown tier {value!r}") from exc
    if isinstance(value, int) and value in {AI_TIER_EARLY, AI_TIER_MID, AI_TIER_LATE}:
        return value
    raise PreferenceDataError("tier must be early, mid, late, 1, 2, or 3")


def scenario_condition_tags(scenario: dict[str, Any]) -> set[str]:
    expectation = scenario_expectation(scenario)
    tags = set(string_list(expectation.get("condition_tags")))
    tags.update(string_list(scenario.get("condition_tags")))
    return tags


def apply_score_delta(score: int, delta: int) -> int:
    if score >= BLOCKED_SCORE:
        return score
    if delta < 0:
        return max(MIN_SELECTABLE_SCORE, score + delta)
    if delta > 0:
        return min(MAX_SELECTABLE_SCORE, score + delta)
    return score


def adjusted_best_roll_threshold(tier: int, gap: int) -> int:
    if gap >= 6:
        threshold = 230
    elif gap >= 3:
        threshold = 192
    else:
        return 154

    if tier == AI_TIER_LATE:
        return min(252, threshold + 32)
    if tier == AI_TIER_MID:
        return min(245, threshold + 20)
    return threshold


def score_moves(scenario: dict[str, Any]) -> list[ScoredMove]:
    moves = scenario.get("moves")
    if not isinstance(moves, list) or not moves:
        raise PreferenceDataError("scenario must contain a non-empty moves list")

    scored: list[ScoredMove] = []
    for slot, move in enumerate(moves, start=1):
        if not isinstance(move, dict):
            raise PreferenceDataError("each move must be an object")
        action_id = str(move.get("id") or f"slot{slot}")
        name = str(move.get("name") or action_id)
        initial = int(move.get("base_score", DEFAULT_BASE_SCORE))
        if move.get("blocked", False):
            initial = BLOCKED_SCORE
        if not 0 <= initial <= 255:
            raise PreferenceDataError(f"{action_id}: base_score must be 0..255")

        score = initial
        events: list[ScoreEvent] = []
        if score >= BLOCKED_SCORE:
            events.append(
                ScoreEvent(
                    rule="blocked",
                    before=score,
                    delta=None,
                    after=score,
                    note="scores 80+ are ignored by BossAI_SelectMove",
                )
            )
        else:
            for raw_delta in move.get("deltas", []):
                if isinstance(raw_delta, int):
                    rule = "delta"
                    delta = raw_delta
                    before = score
                    score = apply_score_delta(score, delta)
                    note = (
                        "encourage lowers score"
                        if delta < 0
                        else "discourage raises score"
                        if delta > 0
                        else "no score change"
                    )
                elif isinstance(raw_delta, dict):
                    rule = str(raw_delta.get("rule", "delta"))
                    before = score
                    if "set_score" in raw_delta:
                        score = int(raw_delta["set_score"])
                        delta = score - before
                        note = "set score"
                    else:
                        delta = int(raw_delta["delta"])
                        score = apply_score_delta(score, delta)
                        note = (
                            "encourage lowers score"
                            if delta < 0
                            else "discourage raises score"
                            if delta > 0
                            else "no score change"
                        )
                else:
                    raise PreferenceDataError(
                        f"{action_id}: deltas must be ints or objects"
                    )
                events.append(ScoreEvent(rule, before, delta, score, note))

            score, events = apply_setup_discipline_bias(
                scenario,
                action_id=action_id,
                name=name,
                score=score,
                events=events,
            )
            score, events = apply_public_status_fail_bias(
                scenario,
                action_id=action_id,
                name=name,
                score=score,
                events=events,
            )
            score, events = apply_support_handoff_bias(
                scenario,
                action_id=action_id,
                name=name,
                score=score,
                events=events,
            )
            score, events = apply_reversible_cashout_bias(
                scenario,
                action_id=action_id,
                name=name,
                score=score,
                events=events,
            )
            score, events = apply_prediction_risk_control_bias(
                scenario,
                action_id=action_id,
                name=name,
                score=score,
                events=events,
            )
            score, events = apply_prediction_branch_bias(
                scenario,
                action_id=action_id,
                name=name,
                score=score,
                events=events,
            )

        scored.append(
            ScoredMove(
                slot=slot,
                action_id=action_id,
                name=name,
                initial_score=initial,
                pre_lookahead_score=score,
                final_score=score,
                blocked=score >= BLOCKED_SCORE,
                lookahead_delta=int(move.get("lookahead_delta", 0)),
                lookahead_applied=False,
                events=events,
            )
        )
    return apply_lookahead(scenario, scored)


def apply_setup_discipline_bias(
    scenario: dict[str, Any],
    *,
    action_id: str,
    name: str,
    score: int,
    events: list[ScoreEvent],
) -> tuple[int, list[ScoreEvent]]:
    tags = scenario_condition_tags(scenario)
    if not ({"active_pressure_converts", "setup_already_bankrolled"} & tags):
        return score, events

    text = f"{action_id} {name}".lower()
    if not any(token in text for token in ("setup", "curse", "dance", "boost")):
        return score, events

    before = score
    delta = 8
    score = apply_score_delta(score, delta)
    return score, [
        *events,
        ScoreEvent(
            "move.apply_move_model.apply_setup_discipline_bias",
            before,
            delta,
            score,
            "visible KO pressure stops extra setup",
        ),
    ]


def apply_public_status_fail_bias(
    scenario: dict[str, Any],
    *,
    action_id: str,
    name: str,
    score: int,
    events: list[ScoreEvent],
) -> tuple[int, list[ScoreEvent]]:
    tags = scenario_condition_tags(scenario)
    if not ({"status_absorber_named", "worst_case_unguarded"} & tags):
        return score, events

    text = f"{action_id} {name}".lower()
    if not any(token in text for token in ("status", "toxic", "poison", "sleep", "leech")):
        return score, events

    before = score
    score = BLOCKED_SCORE
    delta = score - before
    return score, [
        *events,
        ScoreEvent(
            "move.apply_move_model.status_move_would_fail_publicly",
            before,
            delta,
            score,
            "public status absorber makes the status move fail",
        ),
    ]


def apply_support_handoff_bias(
    scenario: dict[str, Any],
    *,
    action_id: str,
    name: str,
    score: int,
    events: list[ScoreEvent],
) -> tuple[int, list[ScoreEvent]]:
    tags = scenario_condition_tags(scenario)
    text = f"{action_id} {name}".lower()
    delta = 0
    note = ""
    rule = "support_handoff_after_job"
    if "support_job_completed" in tags and "repeat_support" in text:
        delta = 8
        note = "support already landed, so repeating it misses the conversion"
    elif "phaze_loop_live" in tags and "generic_chip" in text:
        delta = 4
        note = "hazard phaze loop outranks generic chip"
        rule = "phaze_loop_over_generic_chip"

    if delta == 0:
        return score, events

    before = score
    score = apply_score_delta(score, delta)
    return score, [
        *events,
        ScoreEvent(f"debugger.policy.{rule}", before, delta, score, note),
    ]


def apply_reversible_cashout_bias(
    scenario: dict[str, Any],
    *,
    action_id: str,
    name: str,
    score: int,
    events: list[ScoreEvent],
) -> tuple[int, list[ScoreEvent]]:
    tags = scenario_condition_tags(scenario)
    if "reversible_before_irreversible" not in tags:
        return score, events

    text = f"{action_id} {name}".lower()
    if not any(token in text for token in ("boom", "explosion", "selfdestruct")):
        return score, events

    before = score
    delta = 8
    score = apply_score_delta(score, delta)
    return score, [
        *events,
        ScoreEvent(
            "debugger.policy.reversible_before_irreversible",
            before,
            delta,
            score,
            "reversible coverage preserves the one-shot converter",
        ),
    ]


def apply_prediction_risk_control_bias(
    scenario: dict[str, Any],
    *,
    action_id: str,
    name: str,
    score: int,
    events: list[ScoreEvent],
) -> tuple[int, list[ScoreEvent]]:
    tags = scenario_condition_tags(scenario)
    if "prediction_branch_possible_only" not in tags:
        return score, events

    text = f"{action_id} {name}".lower()
    if "reckless_prediction" not in text and "reckless prediction" not in text:
        return score, events

    before = score
    delta = 8
    score = apply_score_delta(score, delta)
    return score, [
        *events,
        ScoreEvent(
            "debugger.policy.prediction_risk_control",
            before,
            delta,
            score,
            "possible-only prediction stays below safe active conversion",
        ),
    ]


def apply_prediction_branch_bias(
    scenario: dict[str, Any],
    *,
    action_id: str,
    name: str,
    score: int,
    events: list[ScoreEvent],
) -> tuple[int, list[ScoreEvent]]:
    tier = normalize_tier(scenario.get("tier", "late"))
    tags = scenario_condition_tags(scenario)
    if (
        tier < AI_TIER_LATE
        or "prediction_branch_supported" not in tags
        or "prediction_ev_positive" not in tags
        or "prediction_branch_possible_only" in tags
    ):
        return score, events

    text = f"{action_id} {name}".lower()
    if "status" in text:
        delta = 8
        note = "late prediction branch discourages status into a named receiver"
    elif "receiver_coverage" in text or "receiver coverage" in text:
        delta = -7
        note = "late prediction branch prices coverage into the named receiver"
    else:
        return score, events

    before = score
    score = apply_score_delta(score, delta)
    return score, [
        *events,
        ScoreEvent(
            "move.apply_move_model.apply_prediction_branch_bias",
            before,
            delta,
            score,
            note,
        ),
    ]


def apply_lookahead(
    scenario: dict[str, Any],
    scored: list[ScoredMove],
) -> list[ScoredMove]:
    tier = normalize_tier(scenario.get("tier", "late"))
    if tier < AI_TIER_MID or scenario.get("lookahead", True) is False:
        return scored

    legal_scores = [
        item.pre_lookahead_score
        for item in scored
        if item.pre_lookahead_score < BLOCKED_SCORE
    ]
    if not legal_scores:
        return scored

    best = min(legal_scores)
    margin = int(scenario.get("lookahead_margin", DEFAULT_LOOKAHEAD_MARGIN))
    limit = int(scenario.get("lookahead_n", DEFAULT_LOOKAHEAD_N))
    threshold = best + margin
    applied = 0
    result: list[ScoredMove] = []
    for item in scored:
        should_apply = (
            item.pre_lookahead_score < BLOCKED_SCORE
            and item.pre_lookahead_score <= threshold
            and applied < limit
        )
        if not should_apply:
            result.append(item)
            continue

        delta = max(-18, min(18, item.lookahead_delta))
        final = apply_score_delta(item.pre_lookahead_score, delta)
        note = (
            "negative signed lookahead delta encourages"
            if delta < 0
            else "positive signed lookahead delta discourages"
            if delta > 0
            else "lookahead evaluated with no score change"
        )
        events = [
            *item.events,
            ScoreEvent("lookahead", item.pre_lookahead_score, delta, final, note),
        ]
        result.append(
            ScoredMove(
                slot=item.slot,
                action_id=item.action_id,
                name=item.name,
                initial_score=item.initial_score,
                pre_lookahead_score=item.pre_lookahead_score,
                final_score=final,
                blocked=final >= BLOCKED_SCORE,
                lookahead_delta=item.lookahead_delta,
                lookahead_applied=True,
                events=events,
            )
        )
        applied += 1
    return result


def select_move(scenario: dict[str, Any]) -> dict[str, Any]:
    tier = normalize_tier(scenario.get("tier", "late"))
    scored = score_moves(scenario)
    legal = [item for item in scored if item.final_score < BLOCKED_SCORE]
    legal.sort(key=lambda item: (item.final_score, item.slot))

    if not legal:
        return {
            "scenario_id": scenario.get("id", "unnamed"),
            "tier": tier,
            "moves": [move_to_json(item) for item in scored],
            "ready": False,
            "reason": "no selectable move below score 80",
        }

    best = legal[0]
    second = legal[1] if len(legal) > 1 else None
    probabilities = {item.action_id: 0.0 for item in scored}
    if second is None:
        probabilities[best.action_id] = 1.0
        roll_threshold = None
        gap = None
    else:
        gap = second.final_score - best.final_score
        roll_threshold = adjusted_best_roll_threshold(tier, gap)
        probabilities[best.action_id] = roll_threshold / 256
        probabilities[second.action_id] = 1 - probabilities[best.action_id]

    return {
        "scenario_id": scenario.get("id", "unnamed"),
        "tier": tier,
        "moves": [move_to_json(item) for item in scored],
        "ready": True,
        "best_action_id": best.action_id,
        "second_action_id": second.action_id if second else None,
        "best_score": best.final_score,
        "second_score": second.final_score if second else None,
        "gap": gap,
        "best_roll_threshold": roll_threshold,
        "probabilities": probabilities,
        "notes": scenario.get("notes", []),
        "expectation": scenario.get("expectation", {}),
    }


def select_from_score_bytes(
    *,
    scenario_id: str,
    tier: int | str,
    move_ids: list[int],
    scores: list[int],
    move_names: dict[int, str] | None = None,
) -> dict[str, Any]:
    """Replay BossAI_SelectMove from exact post-scoring ROM bytes.

    This intentionally starts after BossAI_ApplyMoveModel and lookahead have
    already written wEnemyAIMoveScores. It mirrors the selector's first blank
    move stop, score >= 80 block, strict-less tie behavior, and best-vs-second
    roll surface.
    """
    tier_value = normalize_tier(tier)
    if len(move_ids) != NUM_MOVES or len(scores) != NUM_MOVES:
        raise PreferenceDataError("selector replay needs exactly four moves and scores")

    slots = []
    for slot_index, (move_id, score) in enumerate(zip(move_ids, scores)):
        move_id = int(move_id)
        score = int(score)
        if not 0 <= move_id <= 255:
            raise PreferenceDataError("move ids must be 0..255")
        if not 0 <= score <= 255:
            raise PreferenceDataError("move scores must be 0..255")
        if move_id == 0:
            break
        name = (
            move_names.get(move_id, f"#{move_id:02x}")
            if move_names is not None
            else f"#{move_id:02x}"
        )
        slots.append(
            {
                "slot": slot_index + 1,
                "slot_index": slot_index,
                "move_id": move_id,
                "name": name,
                "score": score,
                "blocked": score >= BLOCKED_SCORE,
            }
        )

    if tier_value == 0:
        return {
            "scenario_id": scenario_id,
            "tier": tier_value,
            "slots": slots,
            "ready": False,
            "reason": "BossAI_SelectMove returns before boss tiers",
        }

    legal = [slot for slot in slots if int(slot["score"]) < BLOCKED_SCORE]
    if not legal:
        return {
            "scenario_id": scenario_id,
            "tier": tier_value,
            "slots": slots,
            "ready": False,
            "reason": "no selectable move below score 80",
        }

    best = min(legal, key=lambda item: (int(item["score"]), int(item["slot_index"])))
    second_candidates = [
        slot for slot in legal if int(slot["slot_index"]) != int(best["slot_index"])
    ]
    second = (
        min(
            second_candidates,
            key=lambda item: (int(item["score"]), int(item["slot_index"])),
        )
        if second_candidates
        else None
    )

    probabilities_by_slot = {int(slot["slot_index"]): 0.0 for slot in slots}
    if second is None:
        probabilities_by_slot[int(best["slot_index"])] = 1.0
        roll_threshold = None
        gap = None
    else:
        gap = int(second["score"]) - int(best["score"])
        roll_threshold = adjusted_best_roll_threshold(tier_value, gap)
        probabilities_by_slot[int(best["slot_index"])] = roll_threshold / 256
        probabilities_by_slot[int(second["slot_index"])] = (
            1 - probabilities_by_slot[int(best["slot_index"])]
        )

    possible_slots = [
        slot_index
        for slot_index, probability in probabilities_by_slot.items()
        if probability > 0
    ]
    possible_move_ids = sorted(
        {
            int(slot["move_id"])
            for slot in slots
            if int(slot["slot_index"]) in possible_slots
        }
    )
    return {
        "scenario_id": scenario_id,
        "tier": tier_value,
        "slots": slots,
        "ready": True,
        "best_slot_index": int(best["slot_index"]),
        "best_move_id": int(best["move_id"]),
        "best_score": int(best["score"]),
        "second_slot_index": int(second["slot_index"]) if second else None,
        "second_move_id": int(second["move_id"]) if second else None,
        "second_score": int(second["score"]) if second else None,
        "gap": gap,
        "best_roll_threshold": roll_threshold,
        "probabilities_by_slot": probabilities_by_slot,
        "possible_slot_indices": possible_slots,
        "possible_move_ids": possible_move_ids,
    }


def evaluate_scenario(scenario: dict[str, Any]) -> ScenarioVerdict:
    result = select_move(scenario)
    expectation = scenario_expectation(scenario)
    validate_expected_action_ids(scenario, expectation)

    best_ids = string_list(expectation.get("best_action_ids"))
    acceptable_ids = string_list(expectation.get("acceptable_action_ids"))
    bad_ids = string_list(expectation.get("bad_action_ids"))
    catastrophic_ids = string_list(expectation.get("catastrophic_action_ids"))
    policy_tags = string_list(expectation.get("policy_tags"))
    condition_tags = string_list(expectation.get("condition_tags"))
    lesson_type = str(expectation.get("lesson_type", ""))
    confidence = str(expectation.get("confidence", "medium"))
    evidence_refs = string_list(expectation.get("evidence_refs"))
    why = str(expectation.get("why", ""))
    answer_changing_information = string_list(
        expectation.get("answer_changing_information")
    )
    min_best_probability = float(
        expectation.get("min_best_probability", DEFAULT_MIN_BEST_PROBABILITY)
    )

    probabilities = result.get("probabilities", {})
    rom_best = result.get("best_action_id")
    rom_best_probability = float(probabilities.get(rom_best, 0.0)) if rom_best else 0.0
    rolled_bad = rolled_ids(probabilities, bad_ids)
    rolled_catastrophic = rolled_ids(probabilities, catastrophic_ids)
    zero_probability_best = [
        action_id for action_id in best_ids if probabilities.get(action_id, 0.0) == 0.0
    ]

    if not result.get("ready"):
        return ScenarioVerdict(
            scenario_id=str(result["scenario_id"]),
            verdict="no_rom_choice",
            severity=95,
            rom_best_action_id=None,
            rom_best_probability=0.0,
            expected_best_action_ids=best_ids,
            expected_acceptable_action_ids=acceptable_ids,
            rolled_bad_action_ids=rolled_bad,
            rolled_catastrophic_action_ids=rolled_catastrophic,
            zero_probability_best_action_ids=zero_probability_best,
            policy_tags=policy_tags,
            condition_tags=condition_tags,
            lesson_type=lesson_type,
            confidence=confidence,
            evidence_refs=evidence_refs,
            why=why,
            answer_changing_information=answer_changing_information,
            reason=str(result.get("reason", "no selectable ROM action")),
            result=result,
        )

    if rolled_catastrophic:
        verdict = "catastrophic_roll"
        severity = 100
        reason = "ROM gives nonzero probability to catastrophic action(s)"
    elif rolled_bad:
        verdict = "bad_roll"
        severity = 80
        reason = "ROM gives nonzero probability to bad action(s)"
    elif rom_best in best_ids:
        if rom_best_probability < min_best_probability:
            verdict = "weak_best"
            severity = 40
            reason = "ROM top action is expected-best but below probability floor"
        else:
            verdict = "pass"
            severity = 0
            reason = "ROM top action is expected-best"
    elif rom_best in acceptable_ids:
        verdict = "acceptable_top"
        severity = 30
        reason = "ROM top action is acceptable but not expected-best"
    elif best_ids and zero_probability_best == best_ids:
        verdict = "best_never_rolled"
        severity = 75
        reason = "all expected-best actions have zero ROM probability"
    elif best_ids:
        verdict = "mismatch"
        severity = 70
        reason = "ROM top action is outside expected best/acceptable sets"
    else:
        verdict = "needs_expectation"
        severity = 0
        reason = "scenario has no expected best action ids"

    if verdict in {"pass", "acceptable_top"} and zero_probability_best:
        verdict = "partial_best_unrolled"
        severity = max(severity, 45)
        reason = "some expected-best actions have zero ROM probability"

    return ScenarioVerdict(
        scenario_id=str(result["scenario_id"]),
        verdict=verdict,
        severity=severity,
        rom_best_action_id=str(rom_best),
        rom_best_probability=rom_best_probability,
        expected_best_action_ids=best_ids,
        expected_acceptable_action_ids=acceptable_ids,
        rolled_bad_action_ids=rolled_bad,
        rolled_catastrophic_action_ids=rolled_catastrophic,
        zero_probability_best_action_ids=zero_probability_best,
        policy_tags=policy_tags,
        condition_tags=condition_tags,
        lesson_type=lesson_type,
        confidence=confidence,
        evidence_refs=evidence_refs,
        why=why,
        answer_changing_information=answer_changing_information,
        reason=reason,
        result=result,
    )


def evaluate_batch(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    started = time.perf_counter()
    verdicts = [evaluate_scenario(scenario) for scenario in scenarios]
    elapsed = time.perf_counter() - started
    reviewable = [item for item in verdicts if item.severity > 0]
    verdict_counts: dict[str, int] = {}
    policy_counts: dict[str, int] = {}
    for item in verdicts:
        verdict_counts[item.verdict] = verdict_counts.get(item.verdict, 0) + 1
        if item.severity <= 0:
            continue
        for tag in item.policy_tags:
            policy_counts[tag] = policy_counts.get(tag, 0) + 1

    ranked = sorted(
        verdicts,
        key=lambda item: (
            -item.severity,
            -item.rom_best_probability,
            item.scenario_id,
        ),
    )
    per_minute = len(scenarios) / elapsed * 60 if elapsed > 0 else 0.0
    reviewable_per_minute = len(reviewable) / elapsed * 60 if elapsed > 0 else 0.0
    return {
        "scenario_count": len(scenarios),
        "elapsed_seconds": elapsed,
        "scenarios_per_minute": per_minute,
        "reviewable_count": len(reviewable),
        "reviewable_per_minute": reviewable_per_minute,
        "verdict_counts": dict(sorted(verdict_counts.items())),
        "policy_tag_counts": dict(sorted(policy_counts.items())),
        "verdicts": [verdict_to_json(item) for item in ranked],
    }


def benchmark_batch(
    scenarios: list[dict[str, Any]],
    seconds: float,
) -> dict[str, Any]:
    if seconds <= 0:
        raise PreferenceDataError("benchmark seconds must be positive")
    started = time.perf_counter()
    iterations = 0
    reviewable = 0
    while time.perf_counter() - started < seconds:
        for scenario in scenarios:
            verdict = evaluate_scenario(scenario)
            iterations += 1
            if verdict.severity > 0:
                reviewable += 1
    elapsed = time.perf_counter() - started
    return {
        "elapsed_seconds": elapsed,
        "evaluations": iterations,
        "reviewable_evaluations": reviewable,
        "evaluations_per_minute": iterations / elapsed * 60,
        "reviewable_evaluations_per_minute": reviewable / elapsed * 60,
    }


def string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    raise PreferenceDataError("expected string or list of strings")


def scenario_expectation(scenario: dict[str, Any]) -> dict[str, Any]:
    if "expectation" in scenario:
        return normalize_expectation(scenario["expectation"])
    if "expected_policy" in scenario:
        return normalize_expectation(scenario["expected_policy"])
    if "expect" in scenario:
        return normalize_expectation(scenario["expect"])
    return {}


def validate_expected_action_ids(
    scenario: dict[str, Any],
    expectation: dict[str, Any],
) -> None:
    expected_ids: set[str] = set()
    for key in (
        "best_action_ids",
        "acceptable_action_ids",
        "bad_action_ids",
        "catastrophic_action_ids",
    ):
        expected_ids.update(string_list(expectation.get(key)))
    if not expected_ids:
        return

    moves = scenario.get("moves", [])
    action_ids = {
        str(move.get("id") or f"slot{slot}")
        for slot, move in enumerate(moves, start=1)
        if isinstance(move, dict)
    }
    unknown = sorted(expected_ids - action_ids)
    if unknown:
        scenario_id = scenario.get("id", "unnamed")
        raise PreferenceDataError(
            f"{scenario_id}: expectation references unknown action id(s): "
            + ", ".join(unknown)
        )


def rolled_ids(probabilities: dict[str, float], action_ids: list[str]) -> list[str]:
    return [action_id for action_id in action_ids if probabilities.get(action_id, 0.0) > 0.0]


def verdict_to_json(verdict: ScenarioVerdict) -> dict[str, Any]:
    return {
        "scenario_id": verdict.scenario_id,
        "verdict": verdict.verdict,
        "severity": verdict.severity,
        "rom_best_action_id": verdict.rom_best_action_id,
        "rom_best_probability": verdict.rom_best_probability,
        "expected_best_action_ids": verdict.expected_best_action_ids,
        "expected_acceptable_action_ids": verdict.expected_acceptable_action_ids,
        "rolled_bad_action_ids": verdict.rolled_bad_action_ids,
        "rolled_catastrophic_action_ids": verdict.rolled_catastrophic_action_ids,
        "zero_probability_best_action_ids": verdict.zero_probability_best_action_ids,
        "policy_tags": verdict.policy_tags,
        "condition_tags": verdict.condition_tags,
        "lesson_type": verdict.lesson_type,
        "confidence": verdict.confidence,
        "evidence_refs": verdict.evidence_refs,
        "why": verdict.why,
        "answer_changing_information": verdict.answer_changing_information,
        "reason": verdict.reason,
        "result": verdict.result,
    }


def format_batch_report(report: dict[str, Any], *, limit: int = 20) -> str:
    lines = [
        "ROM boss AI batch check",
        f"scenarios={report['scenario_count']} reviewable={report['reviewable_count']} "
        f"elapsed={report['elapsed_seconds']:.4f}s "
        f"rate={report['scenarios_per_minute']:.0f}/min",
    ]
    counts = " ".join(
        f"{verdict}={count}" for verdict, count in report["verdict_counts"].items()
    )
    lines.append(f"verdicts: {counts or 'none'}")
    if report["policy_tag_counts"]:
        tags = " ".join(
            f"{tag}={count}" for tag, count in report["policy_tag_counts"].items()
        )
        lines.append(f"review tags: {tags}")

    lines.append("")
    lines.append(f"Top {limit} review items:")
    review_items = [
        item for item in report["verdicts"] if int(item["severity"]) > 0
    ][:limit]
    if not review_items:
        lines.append("  none")
        return "\n".join(lines)

    for item in review_items:
        probability = float(item["rom_best_probability"])
        tags = ",".join(item["policy_tags"]) or "untagged"
        lines.append(
            f"  {item['severity']:>3} {item['verdict']} {item['scenario_id']} "
            f"rom={item['rom_best_action_id']}({probability:.1%}) "
            f"best={','.join(item['expected_best_action_ids']) or 'none'} "
            f"tags={tags}"
        )
        lines.append(f"      {item['reason']}")
        context = []
        if item["lesson_type"]:
            context.append(f"lesson={item['lesson_type']}")
        if item["condition_tags"]:
            context.append(f"conditions={','.join(item['condition_tags'])}")
        if item["evidence_refs"]:
            context.append(f"refs={';'.join(item['evidence_refs'][:2])}")
        if context:
            lines.append(f"      {' '.join(context)}")
        if item["why"]:
            lines.append(f"      policy: {item['why']}")
        if item["answer_changing_information"]:
            info = "; ".join(item["answer_changing_information"])
            lines.append(f"      changes answer if: {info}")
    return "\n".join(lines)


def move_to_json(item: ScoredMove) -> dict[str, Any]:
    return {
        "slot": item.slot,
        "action_id": item.action_id,
        "name": item.name,
        "initial_score": item.initial_score,
        "pre_lookahead_score": item.pre_lookahead_score,
        "final_score": item.final_score,
        "blocked": item.blocked,
        "lookahead_delta": item.lookahead_delta,
        "lookahead_applied": item.lookahead_applied,
        "events": [
            {
                "rule": event.rule,
                "before": event.before,
                "delta": event.delta,
                "after": event.after,
                "note": event.note,
            }
            for event in item.events
        ],
    }


def format_simulation(result: dict[str, Any], *, show_events: bool = True) -> str:
    lines = [
        f"ROM boss AI scenario: {result['scenario_id']}",
        f"tier={result['tier']} lower_score_is_better blocked_score>=80",
    ]
    for note in result.get("notes", []):
        lines.append(f"note: {note}")
    lines.append("")
    lines.append("Moves:")
    for move in result["moves"]:
        probability = result.get("probabilities", {}).get(move["action_id"], 0.0)
        marker = ""
        if move["action_id"] == result.get("best_action_id"):
            marker = " best"
        elif move["action_id"] == result.get("second_action_id"):
            marker = " second"
        lines.append(
            f"  slot {move['slot']}: {move['name']} [{move['action_id']}] "
            f"{move['initial_score']} -> {move['pre_lookahead_score']} -> "
            f"{move['final_score']} p={probability:.1%}{marker}"
        )
        if show_events:
            for event in move["events"]:
                delta = event["delta"]
                delta_text = "set" if delta is None else f"{delta:+d}"
                lines.append(
                    f"    {event['rule']}: {event['before']} {delta_text} "
                    f"=> {event['after']} ({event['note']})"
                )
    lines.append("")

    if not result["ready"]:
        lines.append(f"No ROM boss move selected: {result['reason']}")
        return "\n".join(lines)

    if result["second_action_id"] is None:
        lines.append(f"Selected deterministically: {result['best_action_id']}")
        return "\n".join(lines)

    lines.append(
        "Selector rolls only best vs second: "
        f"{result['best_action_id']} score={result['best_score']} vs "
        f"{result['second_action_id']} score={result['second_score']} "
        f"gap={result['gap']} threshold={result['best_roll_threshold']}/256"
    )
    never = [
        move["action_id"]
        for move in result["moves"]
        if result["probabilities"].get(move["action_id"], 0.0) == 0.0
        and not move["blocked"]
    ]
    if never:
        lines.append(f"Selectable but never rolled: {', '.join(never)}")
    return "\n".join(lines)
