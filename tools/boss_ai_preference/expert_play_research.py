from __future__ import annotations

from datetime import UTC, datetime
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from .data import ROOT


DEFAULT_EXPERT_PLAY_RESEARCH_REPORT_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "expert_play_research.md"
)
DEFAULT_EXPERT_PLAY_RESEARCH_JSON_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "expert_play_research.json"
)


EXPERT_PLAY_PRINCIPLES: list[dict[str, Any]] = [
    {
        "id": "gsc_foresight_over_one_turn_prediction",
        "source": "https://www.smogon.com/gs/articles/gsc_guide_part1",
        "source_scope": "vanilla_gsc_strategy",
        "source_claim": "Borat's guide emphasizes improving position over many turns, not choosing the highest-power attack or only predicting the next click.",
        "policy_implication": "Every nontrivial answer should name the route improved by the move and the next-turn plan, not just immediate damage.",
        "benchmark_hooks": [
            "long_battle_rest_tempo_unforced_001",
            "romhack_spinblock_damage_context_001",
            "fixture_whitney_miltank_vs_geodude_rollout_lock_001",
            "fixture_misty_starmie_vs_meganium_recover_tempo_001",
        ],
    },
    {
        "id": "gsc_bad_matchup_switching_preserves_future_routes",
        "source": "https://www.smogon.com/gs/articles/gsc_guide_part1",
        "source_scope": "vanilla_gsc_play_patterns",
        "source_claim": "Borat's guide frames switching out of mismatches and knowing when to back off as core play, because GSC kills are earned through position rather than immediate revenge kills.",
        "policy_implication": "When public speed and damage say the active faints before progress, a preserving pivot should beat direct damage or sacrifice unless the sacrifice opens a named route.",
        "benchmark_hooks": [
            "fixture_pryce_cloyster_vs_quilava_fire_pivot_001",
            "fixture_koga_ariados_vs_typhlosion_fire_spikes_001",
            "fixture_will_slowbro_vs_houndoom_fast_dark_001",
        ],
    },
    {
        "id": "gsc_spikes_need_conversion_support",
        "source": "https://www.smogon.com/gs/articles/gsc_spikes",
        "source_scope": "vanilla_gsc_strategy",
        "source_claim": "The Spikes guide treats hazards as pressure that must be converted through status, attacks, phazing, spin pressure, or Rest-cycle pressure.",
        "policy_implication": "A hazard move is only a policy move when it changes switch costs, KO bands, removal incentives, or a named route.",
        "benchmark_hooks": [
            "romhack_spikes_third_layer_janine_001",
            "romhack_spikes_fourth_click_janine_001",
            "romhack_spinblock_damage_context_001",
            "external_gsc_golem_late_rapid_spin_001",
        ],
    },
    {
        "id": "gsc_explosion_is_route_trade",
        "source": "https://www.smogon.com/gs/articles/guide_to_explosion",
        "source_scope": "vanilla_gsc_strategy",
        "source_claim": "The Explosion guide presents Explosion as wallbreaking, emergency defense, free-turn creation, bluffing, or simplification depending on context.",
        "policy_implication": "Explosion answers must name both the route opened and the role lost; low HP alone is not evidence.",
        "benchmark_hooks": [
            "romhack_explosion_route_trade_brock_001",
            "fixture_brock_golem_vs_vaporeon_explosion_question_001",
            "external_gsc_forretress_explosion_on_quagsire_001",
            "fixture_morty_gengar_vs_kadabra_destiny_bond_001",
        ],
    },
    {
        "id": "gsc_sleep_is_temporary_and_resttalk_aware",
        "source": "https://www.smogon.com/gs/articles/status",
        "source_scope": "vanilla_gsc_mechanics_and_strategy",
        "source_claim": "The status guide treats sleep as temporary, notes waking Pokemon can act that turn, and covers Sleep Talk plus Rest value.",
        "policy_implication": "Sleep/setup cards must branch on miss, wake, Sleep Talk, target status, sleep-clause state, and this hack's 2-4 denied-action sleep window instead of continuing scripts.",
        "benchmark_hooks": [
            "vanilla_gsc_sleep_setup_disruption_001",
            "long_battle_sleep_disruption_after_miss_001",
            "external_gsc_sleeping_lax_curse_window_001",
            "external_gsc_vaporeon_vs_restdtalk_snorlax_001",
            "fixture_chuck_poliwrath_vs_alakazam_psychic_pivot_001",
            "fixture_morty_haunter_vs_noctowl_sleep_line_001",
        ],
    },
    {
        "id": "gsc_toxic_clock_needs_survivable_transition",
        "source": "https://www.smogon.com/resources/competitive/gs/status",
        "source_scope": "vanilla_gsc_play_patterns",
        "source_claim": "Smogon's GSC status guide treats Toxic as long-term pressure that matters when it forces recovery, switching, or endgame timing rather than as generic chip.",
        "policy_implication": "A Toxic-clock benchmark should require the target to be unstatused, the status user to survive or justify the trade, and the follow-up pivot or attack route to be named.",
        "benchmark_hooks": [
            "fixture_karen_crobat_vs_dragonite_toxic_clock_001",
            "fixture_koga_ariados_vs_typhlosion_fire_spikes_001",
            "fixture_whitney_miltank_vs_geodude_rollout_lock_001",
            "fixture_bugsy_ariados_vs_pidgey_status_clock_001",
        ],
    },
    {
        "id": "risk_reward_direct_removal_beats_slow_clock",
        "source": "https://www.smogon.com/resources/beginner/bw_risk_reward",
        "source_scope": "cross_generation_play_patterns",
        "source_claim": "Smogon's risk/reward guide frames turn choice around immediate opposing punish branches and the move that best advances the overall route.",
        "policy_implication": "If public damage removes the active threat now, slow status or swingy disruption should lose unless the KO opens a worse forced route.",
        "benchmark_hooks": [
            "fixture_koga_crobat_vs_alakazam_immediate_ko_001",
            "fixture_karen_crobat_vs_dragonite_toxic_clock_001",
            "long_battle_rest_tempo_unforced_001",
            "fixture_misty_starmie_vs_meganium_recover_tempo_001",
        ],
    },
    {
        "id": "risk_reward_utility_needs_public_branch",
        "source": "https://www.smogon.com/resources/beginner/bw_risk_reward",
        "source_scope": "cross_generation_play_patterns",
        "source_claim": "Smogon's risk/reward guide emphasizes choosing moves by the opponent's immediate and worst-case branches rather than generic style preferences.",
        "policy_implication": "Utility moves like Encore should need a visible branch they punish; without that branch, safer setup or direct progress can dominate.",
        "benchmark_hooks": [
            "fixture_whitney_clefairy_vs_bayleef_encore_reflect_001",
            "fixture_falkner_pidgeotto_vs_geodude_scout_probe_001",
            "fixture_jasmine_skarmory_vs_machoke_focus_energy_001",
        ],
    },
    {
        "id": "prediction_requires_public_information",
        "source": "https://www.smogon.com/smog/issue1/introduction_to_prediction",
        "source_scope": "cross_generation_play_patterns",
        "source_claim": "Smogon's prediction guide frames prediction as an information problem: each opponent action should update what future choices are likely and what risks are acceptable.",
        "policy_implication": "Status, pivots, and direct attacks should be chosen from public speed, HP, move, and damage evidence; if a threshold changes, the policy must flip instead of repeating the same slogan.",
        "benchmark_hooks": [
            "fixture_jasmine_magneton_vs_quilava_speed_control_001",
            "fixture_whitney_clefairy_vs_bayleef_encore_reflect_001",
            "vanilla_gsc_opening_electric_double_switch_spikes_001",
            "fixture_clair_dragonair_vs_suicune_hidden_ice_001",
        ],
    },
    {
        "id": "gsc_phazing_is_timing_sensitive",
        "source": "https://www.smogon.com/gs/articles/move_priority",
        "source_scope": "vanilla_gsc_mechanics",
        "source_claim": "The priority guide documents that Roar and Whirlwind must go last to work in GSC.",
        "policy_implication": "Phazing benchmarks need speed relation and move-order evidence before labeling Roar or Whirlwind as setup control.",
        "benchmark_hooks": [
            "vanilla_gsc_phazing_timing_mirror_001",
            "fixture_jasmine_skarmory_vs_machoke_focus_energy_001",
        ],
    },
    {
        "id": "gsc_phazing_needs_live_setup_route",
        "source": "https://www.smogon.com/gs/articles/gsc_spikes",
        "source_scope": "vanilla_gsc_play_patterns",
        "source_claim": "The GSC Spikes guide frames phazing as route pressure that shuts down offense and forces switches, but also says to evaluate the whole position rather than autopilot passive tools.",
        "policy_implication": "Whirlwind or Roar should dominate when a real setup route must be denied now; low-urgency setup signals can lose to status, attack, or preservation.",
        "benchmark_hooks": [
            "fixture_jasmine_skarmory_vs_machoke_focus_energy_001",
            "vanilla_gsc_phazing_timing_mirror_001",
            "vanilla_gsc_pp_phaze_loop_save_final_whirlwind_001",
        ],
    },
    {
        "id": "gsc_perish_song_is_forced_clock_route",
        "source": "https://www.smogon.com/forums/threads/misdreavus-ou-revamp-done.3643258/",
        "source_scope": "vanilla_gsc_play_patterns",
        "source_claim": "The GSC Misdreavus analysis frames Perish Song as a forced-clock tool that can force out setup routes, but warns that Misdreavus must survive the opposing damage long enough to execute it.",
        "policy_implication": "Perish Song should be scored as route control only when the user survives the public punish and the countdown changes the opponent's route.",
        "benchmark_hooks": [
            "fixture_morty_misdreavus_vs_typhlosion_perish_route_001",
            "constructed_gsc_sleep_spikes_route_review_001",
        ],
    },
    {
        "id": "gsc_damage_thresholds_not_type_slogans",
        "source": "https://www.smogon.com/gs/articles/gsc_guide_part1",
        "source_scope": "vanilla_gsc_play_patterns",
        "source_claim": "Borat's GSC guide warns against treating super-effective text or raw power as the decision; strong play asks whether the damage changes the position and future route.",
        "policy_implication": "Type-effectiveness words in benchmark or policy explanations must be backed by mechanics-profile-specific evidence and tied to damage, KO, Rest, preservation, or route thresholds.",
        "benchmark_hooks": [
            "romhack_defensive_answer_preservation_pryce_001",
            "romhack_spinblock_damage_context_001",
            "fixture_brock_golem_vs_vaporeon_explosion_question_001",
            "fixture_will_slowbro_vs_houndoom_fast_dark_001",
            "fixture_chuck_poliwrath_vs_alakazam_psychic_pivot_001",
        ],
    },
    {
        "id": "long_term_thinking_is_skill_axis",
        "source": "https://www.smogon.com/rs/articles/long_term_thinking",
        "source_scope": "cross_generation_strategy",
        "source_claim": "The long-term thinking article frames skill as in-battle planning beyond team matchup and luck, explicitly relevant to RBY/GSC/RSE styles.",
        "policy_implication": "Battle review should grade pre-turn decision quality and earliest route loss separately from the final outcome.",
        "benchmark_hooks": [
            "constructed_gsc_sleep_spikes_route_review_001",
            "vanilla_gsc_pp_phaze_loop_save_final_whirlwind_001",
            "external_gsc_sleeping_lax_curse_window_001",
        ],
    },
    {
        "id": "gsc_opening_moves_are_information_and_resource_bids",
        "source": "https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/",
        "source_scope": "vanilla_gsc_play_patterns",
        "source_claim": "The GSC lead analysis describes strong openings as forcing switches, revealing early team structure, double-switching into Spikes chances, or landing status/Leftovers disruption.",
        "policy_implication": "Opening-turn benchmarks should value the information and resource transition created by a move, not only whether it deals immediate damage.",
        "benchmark_hooks": [
            "romhack_spikes_third_layer_janine_001",
            "vanilla_gsc_phazing_timing_mirror_001",
            "external_gsc_sleeping_lax_curse_window_001",
        ],
    },
    {
        "id": "gsc_tournament_replays_are_real_state_corpus",
        "source": "https://www.smogon.com/forums/threads/gsc-tournament-replays.3689138/",
        "source_scope": "vanilla_gsc_play_patterns",
        "source_claim": "The GSC tournament replay archive collects official tournament games, giving concrete examples of how strong players convert resources across full battles.",
        "policy_implication": "New long-game benchmark cards should be mined from real replay states when possible, with hidden future information sealed from the policy answer.",
        "benchmark_hooks": [
            "external_gsc_sleeping_lax_curse_window_001",
            "external_gsc_forretress_explosion_on_quagsire_001",
            "external_gsc_vaporeon_vs_restdtalk_snorlax_001",
            "external_gsc_golem_late_rapid_spin_001",
            "constructed_gsc_sleep_spikes_route_review_001",
        ],
    },
    {
        "id": "gsc_spikes_offense_uses_direct_pressure_and_booms",
        "source": "https://www.smogon.com/forums/threads/gsc-ou-discussion-thread.3688141/",
        "source_scope": "vanilla_gsc_play_patterns",
        "source_claim": "Current GSC discussion frames robust Spikes play with direct offensive pressure, Thunder users, Nidoking-style progress, and limited Explosion resources rather than passive hazard-only plans.",
        "policy_implication": "Spikes benchmarks need arbitration against direct attack, double-switch, and Explosion conversion lines instead of treating hazards as default progress.",
        "benchmark_hooks": [
            "vanilla_gsc_opening_electric_double_switch_spikes_001",
            "external_gsc_forretress_explosion_on_quagsire_001",
            "romhack_explosion_route_trade_brock_001",
            "romhack_spikes_third_layer_janine_001",
        ],
    },
    {
        "id": "gsc_spikes_are_not_free_passivity",
        "source": "https://www.smogon.com/gs/articles/gsc_spikes",
        "source_scope": "vanilla_gsc_play_patterns",
        "source_claim": "The Spikes guide warns that Spikes alone is not a win condition in most games and that passive Spikes play gives opposing offense time to execute its plan.",
        "policy_implication": "Hazard/status plans must lose to a revealed lethal punish unless the move creates immediate route progress or the active piece is expendable.",
        "benchmark_hooks": [
            "fixture_koga_ariados_vs_typhlosion_fire_spikes_001",
            "romhack_spikes_public_spinner_holdout_001",
            "external_gsc_golem_late_rapid_spin_001",
        ],
    },
    {
        "id": "gsc_setup_requires_opening_and_route",
        "source": "https://www.smogon.com/gs/articles/gsc_guide_part1",
        "source_scope": "vanilla_gsc_play_patterns",
        "source_claim": "Borat's GSC guide frames strong offense as improving position until there is an opening to go for the route, rather than clicking the strongest immediate attack.",
        "policy_implication": "Setup is a policy move only when the public punish is survivable and the boost changes a named route; otherwise direct attack or preservation should dominate.",
        "benchmark_hooks": [
            "fixture_bugsy_scyther_vs_geodude_safe_swords_dance_001",
            "fixture_bugsy_scyther_vs_quilava_fire_setup_001",
            "external_gsc_sleeping_lax_curse_window_001",
            "external_gsc_vaporeon_vs_restdtalk_snorlax_001",
        ],
    },
]


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def build_expert_play_research_report() -> dict[str, Any]:
    scopes = sorted({row["source_scope"] for row in EXPERT_PLAY_PRINCIPLES})
    hooks = sorted(
        {
            hook
            for row in EXPERT_PLAY_PRINCIPLES
            for hook in row["benchmark_hooks"]
        }
    )
    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "principle_count": len(EXPERT_PLAY_PRINCIPLES),
        "source_scopes": scopes,
        "benchmark_hooks": hooks,
        "principles": deepcopy(EXPERT_PLAY_PRINCIPLES),
    }


def validate_expert_play_research_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    principles = report.get("principles")
    if not isinstance(principles, list) or not principles:
        return [*errors, "principles must be a non-empty list"]
    seen_ids: set[str] = set()
    for index, row in enumerate(principles):
        prefix = f"principles[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in (
            "id",
            "source",
            "source_scope",
            "source_claim",
            "policy_implication",
            "benchmark_hooks",
        ):
            if field not in row:
                errors.append(f"{prefix} missing {field}")
        row_id = row.get("id")
        if isinstance(row_id, str):
            if row_id in seen_ids:
                errors.append(f"{prefix} duplicate id {row_id}")
            seen_ids.add(row_id)
        if not str(row.get("source", "")).startswith("https://www.smogon.com/"):
            errors.append(f"{prefix} source must be a Smogon URL")
        if not isinstance(row.get("benchmark_hooks"), list) or not row["benchmark_hooks"]:
            errors.append(f"{prefix} benchmark_hooks must be non-empty")
    return errors


def render_expert_play_research_report(report: dict[str, Any]) -> str:
    lines = [
        "# Expert Play Research",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "Purpose: source-backed play principles that feed benchmark design. This is an artifact index, not a strategy essay.",
        "",
        f"- Principles: {report['principle_count']}",
        f"- Source scopes: {', '.join(report['source_scopes'])}",
        "",
        "## Principles",
        "",
    ]
    for row in report["principles"]:
        lines.extend(
            [
                f"### `{row['id']}`",
                "",
                f"- Source: {row['source']}",
                f"- Scope: `{row['source_scope']}`",
                f"- Claim: {row['source_claim']}",
                f"- Policy implication: {row['policy_implication']}",
                f"- Benchmark hooks: {', '.join(row['benchmark_hooks'])}",
                "",
            ]
        )
    return "\n".join(lines)


def write_expert_play_research_report(
    out_path: Path = DEFAULT_EXPERT_PLAY_RESEARCH_REPORT_PATH,
    json_out_path: Path | None = DEFAULT_EXPERT_PLAY_RESEARCH_JSON_PATH,
) -> dict[str, Any]:
    report = build_expert_play_research_report()
    errors = validate_expert_play_research_report(report)
    if errors:
        raise ValueError("\n".join(errors))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_expert_play_research_report(report),
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
