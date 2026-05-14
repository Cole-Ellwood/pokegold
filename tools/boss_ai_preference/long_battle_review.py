from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from .data import ROOT


DEFAULT_LONG_BATTLE_REVIEW_REPORT_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "long_battle_review.md"
)
DEFAULT_LONG_BATTLE_REVIEW_JSON_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "long_battle_review.json"
)
REQUIRED_LEDGER_FIELDS = {
    "turn",
    "phase",
    "visible_state",
    "hazards",
    "sleep_state",
    "own_win_route",
    "opp_win_route",
    "irreplaceable_pieces",
    "chosen_action",
    "expected_action",
    "decision_quality",
    "checklist",
    "review_flags",
}
REQUIRED_CHECKLIST_FIELDS = {
    "mechanics_profile_checked",
    "win_conditions_named",
    "opponent_route_named",
    "irreplaceables_named",
    "worst_branch_named",
    "answer_changing_info_named",
}


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def ledger_entry(
    turn: int,
    phase: str,
    visible_state: str,
    hazards: str,
    sleep_state: str,
    own_win_route: str,
    opp_win_route: str,
    irreplaceable_pieces: list[str],
    chosen_action: str,
    expected_action: str,
    decision_quality: str,
    review_flags: list[str],
    worst_branch_named: bool = True,
) -> dict[str, Any]:
    return {
        "turn": turn,
        "phase": phase,
        "visible_state": visible_state,
        "hazards": hazards,
        "sleep_state": sleep_state,
        "own_win_route": own_win_route,
        "opp_win_route": opp_win_route,
        "irreplaceable_pieces": irreplaceable_pieces,
        "chosen_action": chosen_action,
        "expected_action": expected_action,
        "decision_quality": decision_quality,
        "checklist": {
            "mechanics_profile_checked": True,
            "win_conditions_named": bool(own_win_route),
            "opponent_route_named": bool(opp_win_route),
            "irreplaceables_named": bool(irreplaceable_pieces),
            "worst_branch_named": worst_branch_named,
            "answer_changing_info_named": True,
        },
        "review_flags": review_flags,
    }


def constructed_long_battle_review() -> dict[str, Any]:
    ledger = [
        ledger_entry(1, "opening", "Cloyster vs Raikou", "none", "none", "establish Spikes then force Rest cycles", "Raikou pivots to Starmie for spin control", ["Cloyster as only Spiker"], "Spikes", "Spikes", "good", []),
        ledger_entry(2, "opening", "Cloyster vs Starmie", "opp side Spikes", "none", "poison or pressure spinner before it removes Spikes", "Starmie spins and resets hazard economy", ["Cloyster", "Gengar spinblocker"], "Toxic", "Toxic or switch:Gengar", "acceptable", []),
        ledger_entry(3, "opening", "Gengar vs Starmie", "opp side Spikes", "none", "block Rapid Spin and keep hazards", "Starmie forces Gengar out with Psychic", ["Gengar spinblocker"], "Thunderbolt", "Thunderbolt", "good", []),
        ledger_entry(4, "opening", "Gengar vs Tyranitar", "opp side Spikes", "none", "preserve spinblocker for later Starmie", "Tyranitar Pursuit traps Ghost", ["Gengar spinblocker"], "switch:Skarmory", "switch:Skarmory", "good", []),
        ledger_entry(5, "opening", "Skarmory vs Tyranitar", "opp side Spikes", "none", "preserve Skarmory for Snorlax while scouting", "Tyranitar chips phazer into Lax range", ["Skarmory Snorlax answer"], "Whirlwind", "Whirlwind", "good", []),
        ledger_entry(6, "opening", "Skarmory phazes Snorlax in", "opp side Spikes", "none", "keep phazing route intact", "CurseLax starts boost route", ["Skarmory Snorlax answer"], "switch:Raikou", "switch:Raikou or Whirlwind", "acceptable", []),
        ledger_entry(7, "midgame", "Raikou vs Snorlax", "opp side Spikes", "none", "force Rest or pivot to sleep user", "Snorlax Body Slam paralysis opens endgame", ["Raikou special check", "Skarmory phazer"], "Roar", "Roar", "good", []),
        ledger_entry(8, "midgame", "Victreebel vs Snorlax", "opp side Spikes", "sleep clause free", "sleep Snorlax to open Swords Dance route", "Snorlax stays and attacks if sleep misses", ["Victreebel breaker"], "Sleep Powder", "Sleep Powder", "good", []),
        ledger_entry(9, "midgame", "Victreebel vs Snorlax after Sleep Powder miss", "opp side Spikes", "sleep clause free, target awake", "re-score: preserve breaker or retry sleep only if miss branch survivable", "Body Slam or Double-Edge removes Victreebel", ["Victreebel breaker", "Skarmory phazer"], "Swords Dance", "Sleep Powder or switch:Skarmory", "bad", ["OVERFITTED_SCRIPT_ERROR", "STATE_REEVALUATION_FAILURE"], False),
        ledger_entry(10, "midgame", "Snorlax KOs Victreebel", "opp side Spikes", "sleep clause free, target awake", "fallback to Raikou pressure after losing breaker", "Snorlax no longer has to fear Grass setup", ["Skarmory phazer", "Raikou"], "send:Raikou", "send:Raikou", "forced", ["EARLIEST_IRREVERSIBLE_ERROR_MATURES"]),
        ledger_entry(11, "midgame", "Raikou vs Snorlax", "opp side Spikes", "none", "force Snorlax Rest through Thunder pressure", "Snorlax uses Curse if Raikou Rests early", ["Raikou", "Skarmory"], "Thunder", "Thunder", "good", []),
        ledger_entry(12, "midgame", "Raikou vs low Snorlax", "opp side Spikes", "none", "force Rest then go Skarmory or Gengar", "Snorlax Rest resets progress", ["Raikou PP", "Skarmory"], "Thunder", "Thunder", "good", []),
        ledger_entry(13, "midgame", "Snorlax Rests", "opp side Spikes", "Rest sleep turn 1", "use forced sleep turn to regain phaze position", "Sleep Talk can still call Body Slam or Curse", ["Skarmory"], "switch:Skarmory", "switch:Skarmory", "good", []),
        ledger_entry(14, "midgame", "Skarmory vs sleeping Snorlax", "opp side Spikes", "Rest sleep turn 2", "Whirlwind with Spikes pressure", "Sleep Talk Curse creates boost pressure", ["Skarmory Whirlwind PP"], "Whirlwind", "Whirlwind", "good", []),
        ledger_entry(15, "midgame", "Cloyster vs Starmie after phaze", "opp side Spikes", "none", "keep Starmie from spinning", "Starmie removes only hazard layer", ["Gengar spinblocker"], "switch:Gengar", "switch:Gengar", "good", []),
        ledger_entry(16, "midgame", "Gengar vs Starmie", "opp side Spikes", "none", "pressure spinner without losing spinblocker", "Psychic chips Gengar below future spinblock range", ["Gengar"], "Thunderbolt", "Thunderbolt", "good", []),
        ledger_entry(17, "conversion", "Cloyster vs Machamp", "opp side Spikes", "none", "Explode only if it opens Snorlax/Raikou route", "Machamp breaks Snorlax if left healthy", ["Cloyster Explosion", "Snorlax"], "Explosion", "Explosion", "good", []),
        ledger_entry(18, "conversion", "Cloyster traded for Machamp", "opp side Spikes", "none", "Snorlax endgame improves with Machamp gone", "Starmie still threatens spin if Gengar falls", ["Gengar spinblocker", "Snorlax"], "send:Snorlax", "send:Snorlax", "good", []),
        ledger_entry(19, "conversion", "Snorlax vs Raikou", "opp side Spikes", "none", "Curse toward endgame only while phazers are weakened", "Raikou Roar burns setup turn", ["Snorlax Rest PP"], "Body Slam", "Body Slam", "good", []),
        ledger_entry(20, "conversion", "Snorlax vs Tyranitar", "opp side Spikes", "none", "avoid unnecessary Rest before forced", "Tyranitar Rock Slide flinch and Roar pressure", ["Snorlax"], "Curse", "Body Slam or switch:Skarmory", "needs_review", ["SETUP_WITHOUT_ROUTE_PROOF"]),
        ledger_entry(21, "conversion", "Snorlax at 72% vs Tyranitar", "opp side Spikes", "none", "attack before Rest threshold", "Rest too early donates Tyranitar turns", ["Snorlax Rest PP"], "Rest", "Body Slam", "bad", ["REST_TEMPO_ERROR"]),
        ledger_entry(22, "conversion", "Sleeping Snorlax vs Tyranitar", "opp side Spikes", "Rest sleep turn 1", "survive sleep turns with Sleep Talk", "Tyranitar can phaze or crit before wake", ["Snorlax"], "Sleep Talk", "Sleep Talk", "forced", []),
        ledger_entry(23, "conversion", "Sleeping Snorlax Sleep Talk calls Curse", "opp side Spikes", "Rest sleep turn 2", "boost while asleep but track wake", "Tyranitar can Roar after boost", ["Snorlax"], "Sleep Talk", "Sleep Talk", "forced", []),
        ledger_entry(24, "conversion", "Awake Snorlax vs Skarmory", "opp side Spikes", "awake", "force Skarmory Rest or paralyze it", "Skarmory phazes Curse boosts", ["Snorlax PP", "Raikou"], "Body Slam", "Body Slam", "good", []),
        ledger_entry(25, "endgame", "Raikou vs Skarmory", "opp side Spikes", "none", "preserve Thunder PP and force Rest", "Skarmory Whirlwind stalls", ["Raikou Thunder PP"], "Thunder", "Thunder", "good", []),
        ledger_entry(26, "endgame", "Raikou vs Resting Skarmory", "opp side Spikes", "Rest sleep turn 1", "use Rest turn to double into Snorlax", "Sleep Talk Whirlwind can break route", ["Snorlax"], "switch:Snorlax", "switch:Snorlax", "good", []),
        ledger_entry(27, "endgame", "Snorlax vs sleeping Skarmory", "opp side Spikes", "Rest sleep turn 2", "Curse once if Sleep Talk phaze branch tolerable", "Sleep Talk Whirlwind resets", ["Snorlax"], "Curse", "Curse", "acceptable", []),
        ledger_entry(28, "endgame", "Snorlax at +1 vs awake Skarmory", "opp side Spikes", "awake", "Body Slam for paralysis or force Rest", "Whirlwind removes boost", ["Snorlax PP"], "Body Slam", "Body Slam", "good", []),
        ledger_entry(29, "endgame", "Gengar low vs Starmie", "opp side Spikes", "none", "block final spin only if Gengar survives Psychic", "Starmie spin frees late switches", ["Gengar spinblocker"], "Thunderbolt", "switch:Snorlax if Psychic KO is confirmed", "needs_review", ["DAMAGE_RANGE_UNVERIFIED"]),
        ledger_entry(30, "endgame", "Starmie spins after Gengar faints", "no hazards", "none", "win through Snorlax PP instead of hazards", "opponent switching is free again", ["Snorlax", "Raikou"], "send:Snorlax", "send:Snorlax", "forced", ["HAZARD_ROUTE_LOST"]),
        ledger_entry(31, "endgame", "Snorlax vs Raikou", "no hazards", "none", "PP endgame: force Rest without wasting Body Slam", "Raikou Roar and Rest cycles can outlast", ["Snorlax Rest PP", "Body Slam PP"], "Body Slam", "Body Slam", "good", []),
        ledger_entry(32, "endgame", "Snorlax low vs Resting Raikou", "no hazards", "Rest sleep turn 1", "final route depends on PP and paralysis, not damage slogans", "Raikou wakes and Roars if PP route fails", ["Snorlax Rest PP"], "Curse", "Curse or Rest depending exact PP", "needs_review", ["PP_COUNT_REQUIRED"]),
    ]
    return {
        "id": "constructed_gsc_sleep_spikes_route_review_001",
        "scenario_type": "constructed_long_game",
        "mechanics_profile": "vanilla_gsc",
        "turn_count": len(ledger),
        "source_refs": [
            "docs/boss_ai_teaching_heuristics.md",
            "tools/boss_ai_preference/benchmarks/state_transition_public_cards.json",
            "tools/boss_ai_preference/type_evidence.py",
            "https://www.smogon.com/gs/articles/gsc_spikes",
            "https://www.smogon.com/gs/articles/guide_to_explosion",
            "https://www.smogon.com/gs/articles/gsc_guide_part1",
            "https://www.smogon.com/smog/issue28/gsc",
        ],
        "phases": [
            {"name": "opening", "turns": [1, 7], "focus": "establish hazard and spinner model"},
            {"name": "midgame", "turns": [8, 18], "focus": "sleep disruption, spinblock, and Explosion trade"},
            {"name": "conversion", "turns": [19, 24], "focus": "Rest cycle and setup timing"},
            {"name": "endgame", "turns": [25, 32], "focus": "PP, hazard loss, and final route conversion"},
        ],
        "ledger_entries": ledger,
        "critical_turns": [
            {
                "turn": 9,
                "label": "earliest_irreversible_error",
                "mistake": "Swords Dance after Sleep Powder miss without re-scoring",
                "expected": "retry sleep only if the miss branch is survivable, otherwise preserve Victreebel or pivot to Skarmory",
            },
            {
                "turn": 17,
                "label": "good_route_trade",
                "mistake": "",
                "expected": "Explosion is justified because Machamp blocks Snorlax endgame and Cloyster already set the only vanilla Spikes layer",
            },
            {
                "turn": 21,
                "label": "rest_tempo_error",
                "mistake": "Rest at 72% gave Tyranitar sleep turns without preserving a required role",
                "expected": "attack or pivot until Rest is forced by range",
            },
            {
                "turn": 29,
                "label": "damage_range_gap",
                "mistake": "Gengar spinblock line needs exact Psychic survival evidence before staying in",
                "expected": "classify as needs_context unless profile-specific damage range is known; a romhack threshold card now covers the verified local damage case",
            },
        ],
        "earliest_meaningful_error": {
            "turn": 9,
            "error_class": "OVERFITTED_SCRIPT_ERROR",
            "why_irreversible": "Victreebel was the only realistic sleep/setup breaker; losing it made the remaining plan rely on Snorlax PP and Explosion trades.",
            "regression_target": "sleep_disruption_after_miss_long_game_001",
        },
        "benchmark_extractions": [
            {
                "id": "sleep_disruption_after_miss_long_game_001",
                "turn": 9,
                "best": ["move_sleep_powder", "switch_skarmory"],
                "catastrophic": ["move_swords_dance"],
                "answer_flip_field": "sleep_move_result: hit -> miss",
            },
            {
                "id": "rest_tempo_unforced_long_game_001",
                "turn": 21,
                "best": ["move_body_slam"],
                "catastrophic": ["move_rest"],
                "answer_flip_field": "snorlax_hp: forced_rest_range -> 72%",
            },
            {
                "id": "spinblock_damage_context_long_game_001",
                "turn": 29,
                "best": ["needs_context"],
                "catastrophic": ["move_thunderbolt_without_survival_range"],
                "answer_flip_field": "starmie_psychic_vs_gengar_damage_range",
            },
        ],
        "heuristics_learned": [
            "A sleep miss in a long game invalidates setup scripts more severely when the sleeper is also an irreplaceable route piece.",
            "Explosion is a good route trade only when the lost role is already discharged or replaceable.",
            "Rest timing is a route-preservation claim; high-HP Rest without a forced range can donate conversion turns.",
            "Spinblock decisions in endgames require profile-specific damage evidence; the romhack Starmie/Gengar threshold is not vanilla GSC proof.",
        ],
        "damage_context_evidence": [
            {
                "id": "romhack_spinblock_damage_context_001",
                "mechanics_profile": "romhack_gym_leader_lab",
                "source": "tools.damage_debugger.matchup",
                "queries": [
                    "STARMIE:55:player GENGAR:55:trainer PSYCHIC",
                    "GENGAR:55:trainer STARMIE:55:player THUNDERBOLT",
                ],
                "result": [
                    "Starmie Psychic deals 53-63 HP to trainer Gengar.",
                    "Gengar Thunderbolt deals 85-101 HP to player Starmie.",
                ],
                "policy_threshold": "Gengar at 67 HP survives Psychic and removes 83 HP Starmie; Gengar at 52 HP is KOed before moving.",
                "promoted_artifact": "tools/boss_ai_preference/benchmarks/state_transition_public_cards.json:romhack_spinblock_damage_context_001",
                "transfer_warning": "This evidence uses romhack source stats and typing, including Ghost/Psychic Gengar, so it must not be used as vanilla GSC truth.",
            }
        ],
        "unverified": [
            "Exact vanilla GSC Starmie Psychic versus Gengar damage for the constructed review.",
            "Exact original turn-29 Gengar HP/level if this constructed scenario is replaced with a real battle log.",
            "Exact remaining PP for Snorlax Body Slam, Rest, and opposing Raikou Roar in the final four turns.",
            "Whether an expert reviewer would prefer preserving Victreebel or retrying Sleep Powder on turn 9.",
        ],
    }


def validate_long_battle_review(review: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if review.get("turn_count", 0) < 30:
        errors.append("review must cover at least 30 turns")
    if review.get("mechanics_profile") not in {"vanilla_gsc", "romhack_gym_leader_lab"}:
        errors.append("review must name a supported mechanics_profile")
    ledger = review.get("ledger_entries")
    if not isinstance(ledger, list):
        return [*errors, "review must contain ledger_entries"]
    if len(ledger) != review.get("turn_count"):
        errors.append("ledger_entries count must match turn_count")
    for index, entry in enumerate(ledger):
        missing = sorted(REQUIRED_LEDGER_FIELDS - set(entry))
        if missing:
            errors.append(f"ledger_entries[{index}] missing: {', '.join(missing)}")
            continue
        checklist = entry.get("checklist")
        if not isinstance(checklist, dict):
            errors.append(f"ledger_entries[{index}].checklist must be an object")
            continue
        missing_checklist = sorted(REQUIRED_CHECKLIST_FIELDS - set(checklist))
        if missing_checklist:
            errors.append(
                f"ledger_entries[{index}].checklist missing: "
                f"{', '.join(missing_checklist)}"
            )
    if not review.get("critical_turns"):
        errors.append("review must include critical_turns")
    earliest = review.get("earliest_meaningful_error")
    if not isinstance(earliest, dict) or not earliest.get("turn"):
        errors.append("review must identify earliest_meaningful_error")
    if not review.get("benchmark_extractions"):
        errors.append("review must extract benchmark candidates")
    return errors


def build_long_battle_review_report() -> dict[str, Any]:
    review = constructed_long_battle_review()
    errors = validate_long_battle_review(review)
    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "review_count": 1,
        "reviews_valid": not errors,
        "validation_errors": errors,
        "turn_count": review["turn_count"],
        "critical_turn_count": len(review["critical_turns"]),
        "benchmark_extraction_count": len(review["benchmark_extractions"]),
        "earliest_meaningful_error": review["earliest_meaningful_error"],
        "heuristics_learned": review["heuristics_learned"],
        "damage_context_evidence": review["damage_context_evidence"],
        "unverified": review["unverified"],
        "reviews": [review],
    }


def render_long_battle_review_report(report: dict[str, Any]) -> str:
    review = report["reviews"][0]
    lines = [
        "# Long Battle Review Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Reviews valid: `{report['reviews_valid']}`",
        f"- Turns reviewed: {report['turn_count']}",
        f"- Critical turns: {report['critical_turn_count']}",
        f"- Benchmark extractions: {report['benchmark_extraction_count']}",
        f"- Earliest meaningful error: turn {report['earliest_meaningful_error']['turn']} "
        f"({report['earliest_meaningful_error']['error_class']})",
        "",
        "## Critical Turns",
        "",
    ]
    for row in review["critical_turns"]:
        lines.extend(
            [
                f"### Turn {row['turn']} - `{row['label']}`",
                "",
                f"- Mistake: {row['mistake'] or 'none'}",
                f"- Expected: {row['expected']}",
                "",
            ]
        )

    lines.extend(["## Benchmark Extractions", ""])
    for row in review["benchmark_extractions"]:
        lines.extend(
            [
                f"- `{row['id']}` from turn {row['turn']}: "
                f"best `{row['best']}`, catastrophic `{row['catastrophic']}`, "
                f"flip field `{row['answer_flip_field']}`",
            ]
        )

    lines.extend(["", "## Heuristics Learned", ""])
    lines.extend(f"- {item}" for item in report["heuristics_learned"])
    lines.extend(["", "## Damage Context Evidence", ""])
    for row in report["damage_context_evidence"]:
        lines.extend(
            [
                f"- `{row['id']}` ({row['mechanics_profile']}): "
                f"{'; '.join(row['result'])}",
                f"  - Threshold: {row['policy_threshold']}",
                f"  - Transfer warning: {row['transfer_warning']}",
            ]
        )
    lines.extend(["", "## Unverified", ""])
    lines.extend(f"- {item}" for item in report["unverified"])
    return "\n".join(lines)


def write_long_battle_review_report(
    out_path: Path = DEFAULT_LONG_BATTLE_REVIEW_REPORT_PATH,
    json_out_path: Path | None = DEFAULT_LONG_BATTLE_REVIEW_JSON_PATH,
) -> dict[str, Any]:
    report = build_long_battle_review_report()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_long_battle_review_report(report),
        encoding="utf-8",
        newline="\n",
    )
    if json_out_path is not None:
        json_out_path.parent.mkdir(parents=True, exist_ok=True)
        json_out_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return report
