from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from .data import PACKAGE_DIR, ROOT, PreferenceDataError


DEFAULT_LEGACY_BENCHMARKS_PATH = (
    PACKAGE_DIR / "benchmarks" / "state_transition_benchmarks.json"
)
DEFAULT_PUBLIC_BENCHMARKS_PATH = (
    PACKAGE_DIR / "benchmarks" / "state_transition_public_cards.json"
)
DEFAULT_BENCHMARK_ORACLES_PATH = (
    PACKAGE_DIR / "benchmarks" / "state_transition_oracles.json"
)
DEFAULT_BENCHMARKS_PATH = DEFAULT_PUBLIC_BENCHMARKS_PATH
DEFAULT_BENCHMARK_REPORT_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "state_transition_benchmarks.md"
)
DEFAULT_BENCHMARK_JSON_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "state_transition_benchmarks.json"
)
DEFAULT_BENCHMARK_POLICY_ANSWERS_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "state_transition_policy_answers.json"
)
DEFAULT_BENCHMARK_MUTATION_REPORT_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "state_transition_mutations.md"
)
DEFAULT_BENCHMARK_MUTATION_JSON_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "state_transition_mutations.json"
)
DEFAULT_POLICY_ANSWER_SCHEMA_PATH = (
    PACKAGE_DIR / "schemas" / "policy_answer.schema.json"
)

ALLOWED_MECHANICS_PROFILES = {"vanilla_gsc", "romhack_gym_leader_lab"}
ALLOWED_BENCHMARK_SPLITS = {"seed", "holdout", "fixture_harvest"}
REQUIRED_OUTCOME_LABELS = {"best", "acceptable", "catastrophic"}
REQUIRED_OPPONENT_TIERS = {
    "immediate_punish",
    "role_aware_preservation",
    "incentive_compatible_response",
    "hidden_info_belief_state",
}
REQUIRED_BENCHMARK_FIELDS = {
    "id",
    "split",
    "mechanics_profile",
    "source_refs",
    "tags",
    "position",
    "candidate_moves",
    "current_win_conditions",
    "irreplaceable_pieces",
    "opponent_model",
    "catastrophe_branch",
    "information_that_changes_answer",
    "arbitration",
}
REQUIRED_PUBLIC_CARD_FIELDS = {
    "id",
    "version",
    "split",
    "mechanics_profile",
    "source_refs",
    "tags",
    "position_snapshot",
    "candidate_moves_public",
    "required_answer_fields",
    "hidden_info_visible_to_policy",
    "public_opponent_model",
}
REQUIRED_ORACLE_FIELDS = {
    "best",
    "acceptable",
    "catastrophic",
    "why_best",
    "why_acceptable",
    "why_catastrophic",
    "catastrophe_branches",
    "answer_changing_information",
    "heuristic_arbitration",
    "current_win_conditions",
    "irreplaceable_pieces",
}
REQUIRED_POLICY_ANSWER_FIELDS = {
    "benchmark_id",
    "policy_version",
    "mechanics_profile_seen",
    "state_hash",
    "decision_status",
    "chosen_move_id",
    "confidence",
    "candidate_ranking",
    "current_win_conditions",
    "irreplaceable_pieces",
    "catastrophe_branches",
    "answer_changing_information",
    "rules_fired",
}
DEFAULT_REQUIRED_ANSWER_FIELDS = [
    "chosen_move_id",
    "candidate_ranking",
    "current_win_conditions",
    "irreplaceable_pieces",
    "catastrophe_branches",
    "answer_changing_information",
    "rules_fired",
]
INITIAL_REQUIRED_BENCHMARK_IDS = {
    "vanilla_gsc_sleep_setup_disruption_001",
    "romhack_spikes_third_layer_janine_001",
    "romhack_spikes_fourth_click_janine_001",
    "romhack_explosion_route_trade_brock_001",
    "romhack_defensive_answer_preservation_pryce_001",
}
SETUP_MOVE_TOKENS = {
    "amnesia",
    "belly_drum",
    "curse",
    "double_team",
    "dragon_dance",
    "growth",
    "quiver_dance",
    "swords_dance",
}
RECOVERY_MOVE_TOKENS = {"milk_drink", "recover", "rest", "softboiled"}
SLEEP_MOVE_TOKENS = {"hypnosis", "lovely_kiss", "sleep_powder", "spore"}
SLEEP_ONLY_MOVE_TOKENS = {"sleep_talk"}
STATUS_MOVE_TOKENS = {"stun_spore", "thunder_wave", "toxic"}
SCOUT_MOVE_TOKENS = {"sand_attack", "smokescreen"}
PROTECT_MOVE_TOKENS = {"protect"}
ENCORE_MOVE_TOKENS = {"encore"}
LOCK_MOVE_TOKENS = {"outrage", "rollout"}
PERISH_MOVE_TOKENS = {"perish_song"}
SACRIFICE_MOVE_TOKENS = {"destiny_bond"}
PHAZING_MOVE_TOKENS = {"roar", "whirlwind"}
HAZARD_REMOVAL_MOVE_TOKENS = {"rapid_spin"}
BENCHMARK_MUTATION_SPECS = [
    {
        "mutation_id": "mut_sleep_clause_occupied_blocks_sleep_001",
        "base_id": "vanilla_gsc_sleep_setup_disruption_001",
        "family": "sleep_clause_occupied",
        "minimal_delta": "position_snapshot.field.sleep_clause: free -> occupied",
        "changes": [
            {"path": "position_snapshot.field.sleep_clause", "value": "occupied"},
        ],
        "expected_base_move_id": "move_sleep_powder",
        "expected_mutated_move_id": "move_sludge_bomb",
        "principle": "sleep control loses when clause state blocks the transition",
    },
    {
        "mutation_id": "mut_target_already_statused_blocks_sleep_001",
        "base_id": "vanilla_gsc_sleep_setup_disruption_001",
        "family": "target_already_statused",
        "minimal_delta": "position_snapshot.opponent_active.status: none -> par",
        "changes": [
            {"path": "position_snapshot.opponent_active.status", "value": "par"},
        ],
        "expected_base_move_id": "move_sleep_powder",
        "expected_mutated_move_id": "move_sludge_bomb",
        "principle": "sleep move value collapses when the visible target is already statused",
    },
    {
        "mutation_id": "mut_long_battle_sleep_clause_blocks_rescore_001",
        "base_id": "long_battle_sleep_disruption_after_miss_001",
        "family": "sleep_clause_occupied",
        "minimal_delta": "position_snapshot.field.sleep_clause: free -> occupied",
        "changes": [
            {"path": "position_snapshot.field.sleep_clause", "value": "occupied"},
        ],
        "expected_base_move_id": "move_sleep_powder",
        "expected_mutated_move_id": "move_sludge_bomb",
        "principle": "long-game sleep re-score must abandon sleep if clause state blocks it",
    },
    {
        "mutation_id": "mut_spikes_layer_2_to_max_001",
        "base_id": "romhack_spikes_third_layer_janine_001",
        "family": "max_spikes_noop",
        "minimal_delta": "position_snapshot.field.player_side_spikes_layers: 2 -> 3",
        "changes": [
            {
                "path": "position_snapshot.field.player_side_spikes_layers",
                "value": 3,
            },
        ],
        "expected_base_move_id": "move_spikes",
        "expected_mutated_move_id": "move_explosion",
        "principle": "max hazard layer no-op dominates the set-Spikes heuristic",
    },
    {
        "mutation_id": "mut_spinner_public_lowers_spikes_001",
        "base_id": "fixture_janine_qwilfish_third_spikes_layer_001",
        "family": "spinner_revealed",
        "minimal_delta": "position_snapshot.field.player_rapid_spin_seen: false -> true",
        "changes": [
            {
                "path": "position_snapshot.field.player_rapid_spin_seen",
                "value": True,
            },
        ],
        "expected_base_move_id": "move_spikes",
        "expected_mutated_move_id": "move_explosion",
        "principle": "public removal pressure can dominate finishing the hazard stack",
    },
    {
        "mutation_id": "mut_explosion_blocked_by_protect_001",
        "base_id": "romhack_explosion_route_trade_brock_001",
        "family": "explosion_blocked",
        "minimal_delta": "position_snapshot.opponent_active.revealed_moves: [Surf] -> [Surf, Protect]",
        "changes": [
            {
                "path": "position_snapshot.opponent_active.revealed_moves",
                "value": ["Surf", "Protect"],
            },
        ],
        "expected_base_move_id": "move_explosion",
        "expected_mutated_move_id": "switch_omastar",
        "principle": "Explosion route conversion loses to a public block branch",
    },
    {
        "mutation_id": "mut_defensive_pivot_unavailable_001",
        "base_id": "romhack_defensive_answer_preservation_pryce_001",
        "family": "defensive_answer_unavailable",
        "minimal_delta": "position_snapshot.boss_bench: remove Piloswine",
        "changes": [
            {
                "path": "position_snapshot.boss_bench",
                "value": ["Cloyster", "Slowking"],
            },
        ],
        "expected_base_move_id": "switch_piloswine",
        "expected_mutated_move_id": "move_thunder_wave",
        "principle": "preservation cannot choose an unavailable defensive answer",
    },
    {
        "mutation_id": "mut_preservation_switch_unavailable_001",
        "base_id": "fixture_chuck_poliwrath_vs_pidgeotto_ice_punch_001",
        "family": "preservation_switch_unavailable",
        "minimal_delta": "position_snapshot.boss_bench: remove Sudowoodo",
        "changes": [
            {
                "path": "position_snapshot.boss_bench",
                "value": ["Hitmontop", "Hitmonlee", "Umbreon"],
            },
        ],
        "expected_base_move_id": "switch_sudowoodo",
        "expected_mutated_move_id": "move_ice_punch",
        "principle": "switch preservation only dominates when the preserving pivot exists",
    },
    {
        "mutation_id": "mut_long_battle_rest_becomes_forced_001",
        "base_id": "long_battle_rest_tempo_unforced_001",
        "family": "rest_forced_range",
        "minimal_delta": "Snorlax HP 72% -> 32%; immediate punish becomes KO if no Rest",
        "changes": [
            {"path": "position_snapshot.boss_active.hp", "value": "32%"},
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Tyranitar attack KOs if Snorlax does not Rest now.",
            },
        ],
        "expected_base_move_id": "move_body_slam",
        "expected_mutated_move_id": "move_rest",
        "principle": "Rest changes from tempo loss to forced role preservation once survival is at stake",
    },
    {
        "mutation_id": "mut_spinblock_damage_survival_to_ko_001",
        "base_id": "romhack_spinblock_damage_context_001",
        "family": "damage_threshold_flip",
        "minimal_delta": "Gengar HP 48% / 67 HP -> 38% / 52 HP; Starmie Psychic 53-63 becomes a guaranteed KO",
        "changes": [
            {"path": "position_snapshot.boss_active.hp", "value": "38%"},
            {"path": "position_snapshot.boss_active.current_hp", "value": 52},
            {
                "path": "position_snapshot.damage_bands.opponent_psychic_vs_boss_active.defender_current_hp",
                "value": 52,
            },
            {
                "path": "position_snapshot.damage_bands.opponent_psychic_vs_boss_active.ko_at_current_hp",
                "value": "guaranteed",
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Starmie is faster and Psychic is a guaranteed KO into the current Gengar HP, so staying in loses the spinblocker before Thunderbolt can fire.",
            },
        ],
        "expected_base_move_id": "move_thunderbolt",
        "expected_mutated_move_id": "switch_raikou",
        "principle": "spinblocking with an attack only dominates when exact damage evidence says the blocker survives the opponent's fastest punish",
    },
    {
        "mutation_id": "mut_phazing_order_faster_to_slower_001",
        "base_id": "vanilla_gsc_phazing_timing_mirror_001",
        "family": "phazing_order_flip",
        "minimal_delta": "boss phazer moves before opposing phazer -> boss phazer moves after opposing phazer",
        "changes": [
            {
                "path": "position_snapshot.mechanics.boss_phaze_order",
                "value": "after_opponent_phaze",
            },
            {
                "path": "position_snapshot.boss_active.speed_relation",
                "value": "slower_than_opponent_within_negative_priority",
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "If both sides click phazing, the opponent's faster Whirlwind fails first and the boss Roar acts last, so Roar can reset the setup route.",
            },
        ],
        "expected_base_move_id": "move_rock_slide",
        "expected_mutated_move_id": "move_roar",
        "principle": "Gen 2 phazing changes answer when move order flips because Roar and Whirlwind must be last to work",
    },
    {
        "mutation_id": "mut_final_phaze_pp_setup_pressure_001",
        "base_id": "vanilla_gsc_pp_phaze_loop_save_final_whirlwind_001",
        "family": "pp_route_pressure_flip",
        "minimal_delta": "opponent setup route is contained -> immediate unanswerable setup route",
        "changes": [
            {
                "path": "position_snapshot.mechanics.immediate_setup_route",
                "value": True,
            },
            {
                "path": "position_snapshot.opponent_active.boosts",
                "value": {"atk": 3, "def": 3, "spe": -3},
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Snorlax is already boosted enough that one more unchecked turn creates an unanswerable Curse route; spending the final Whirlwind PP is now justified.",
            },
        ],
        "expected_base_move_id": "move_rest",
        "expected_mutated_move_id": "move_whirlwind",
        "principle": "final phazing PP should be saved unless spending it denies an immediate setup route",
    },
    {
        "mutation_id": "mut_sleep_window_target_awake_001",
        "base_id": "external_gsc_sleeping_lax_curse_window_001",
        "family": "sleep_window_removed",
        "minimal_delta": "Snorlax asleep -> awake and able to punish setup",
        "changes": [
            {
                "path": "position_snapshot.opponent_active.status",
                "value": "none",
            },
            {
                "path": "position_snapshot.mechanics.sleep_window_available",
                "value": False,
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Snorlax is awake and can attack immediately, so Curse no longer gets the free setup window that changed the KO math.",
            },
        ],
        "expected_base_move_id": "move_curse",
        "expected_mutated_move_id": "move_earthquake",
        "principle": "setup during a sleep window loses priority once the target is awake and can punish immediately",
    },
    {
        "mutation_id": "mut_opening_double_switch_to_direct_pressure_001",
        "base_id": "vanilla_gsc_opening_electric_double_switch_spikes_001",
        "family": "opening_incentive_flip",
        "minimal_delta": "opponent Cloyster likely switches -> opponent Cloyster can stay and set Spikes",
        "changes": [
            {
                "path": "position_snapshot.mechanics.double_switch_spikes_window",
                "value": False,
            },
            {
                "path": "position_snapshot.mechanics.opening_reveal_value",
                "value": False,
            },
            {
                "path": "position_snapshot.mechanics.opening_direct_pressure_needed",
                "value": True,
            },
            {
                "path": "position_snapshot.mechanics.opponent_switch_incentive",
                "value": "low",
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Cloyster is not forced out and can stay to set Spikes; double-switching now gives the opponent the hazard turn for free.",
            },
        ],
        "expected_base_move_id": "switch_cloyster",
        "expected_mutated_move_id": "move_thunder",
        "principle": "opening double-switches are resource bids that lose to direct pressure when the opponent no longer has the switch incentive",
    },
    {
        "mutation_id": "mut_external_boom_blocked_by_protect_001",
        "base_id": "external_gsc_forretress_explosion_on_quagsire_001",
        "family": "explosion_blocked",
        "minimal_delta": "Quagsire route target has no public block -> Protect is revealed",
        "changes": [
            {
                "path": "position_snapshot.opponent_active.revealed_moves",
                "value": ["Surf", "Protect"],
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Protect is publicly revealed, so Explosion can be blanked while Forretress faints and the route trade fails.",
            },
        ],
        "expected_base_move_id": "move_explosion",
        "expected_mutated_move_id": "switch_snorlax",
        "principle": "real replay Explosion conversion loses to a public block branch even when the original route trade was correct",
    },
    {
        "mutation_id": "mut_restdtalk_branch_absent_setup_window_001",
        "base_id": "external_gsc_vaporeon_vs_restdtalk_snorlax_001",
        "family": "sleep_talk_branch_removed",
        "minimal_delta": "Sleep Talk Rest branch public -> no Sleep Talk/Rest branch and Growth changes KO math",
        "changes": [
            {
                "path": "position_snapshot.opponent_active.revealed_moves",
                "value": ["Curse", "Double-Edge"],
            },
            {
                "path": "position_snapshot.mechanics.sleep_talk_rest_branch",
                "value": False,
            },
            {
                "path": "position_snapshot.mechanics.setup_changes_ko_math",
                "value": True,
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Snorlax is asleep without public Sleep Talk or RestTalk evidence, so Growth can use the sleep window to change the Surf conversion math.",
            },
        ],
        "expected_base_move_id": "move_surf",
        "expected_mutated_move_id": "move_growth",
        "principle": "attacking a sleeping RestTalk user dominates greed, but setup can dominate when the public RestTalk catastrophe branch is absent and setup changes KO math",
    },
    {
        "mutation_id": "mut_late_spin_no_hazards_attack_now_001",
        "base_id": "external_gsc_golem_late_rapid_spin_001",
        "family": "hazard_removal_absent",
        "minimal_delta": "own side has one Spikes layer -> no own-side hazards",
        "changes": [
            {"path": "position_snapshot.field.boss_side_spikes", "value": "none"},
            {
                "path": "position_snapshot.mechanics.own_hazards_present",
                "value": False,
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "There are no own-side Spikes to remove, so Rapid Spin becomes low-value and Golem should pressure the Resting Snorlax directly.",
            },
        ],
        "expected_base_move_id": "move_rapid_spin",
        "expected_mutated_move_id": "move_earthquake",
        "principle": "late-game Rapid Spin is a route-preservation move only while hazards still tax future switches",
    },
    {
        "mutation_id": "mut_fast_dark_pivot_unavailable_attack_now_001",
        "base_id": "fixture_will_slowbro_vs_houndoom_fast_dark_001",
        "family": "fast_public_punish_preservation_unavailable",
        "minimal_delta": "position_snapshot.boss_bench: remove Houndoom",
        "changes": [
            {
                "path": "position_snapshot.boss_bench",
                "value": ["Forretress", "Starmie", "Alakazam", "Xatu"],
            },
        ],
        "expected_base_move_id": "switch_houndoom",
        "expected_mutated_move_id": "move_surf",
        "principle": "fast public punish preservation flips to the best stay-in attack only when the preserving pivot is unavailable",
    },
    {
        "mutation_id": "mut_fire_preservation_primary_pivot_unavailable_001",
        "base_id": "fixture_koga_ariados_vs_typhlosion_fire_spikes_001",
        "family": "fast_public_punish_preservation_unavailable",
        "minimal_delta": "position_snapshot.boss_bench: remove Tentacruel",
        "changes": [
            {
                "path": "position_snapshot.boss_bench",
                "value": ["Muk", "Nidoking", "Umbreon", "Crobat"],
            },
        ],
        "expected_base_move_id": "switch_tentacruel",
        "expected_mutated_move_id": "switch_umbreon",
        "principle": "lethal public Fire pressure still demands preservation, but the best preserving pivot changes when the primary answer is unavailable",
    },
    {
        "mutation_id": "mut_safe_setup_window_removed_by_ko_range_001",
        "base_id": "fixture_bugsy_scyther_vs_geodude_safe_swords_dance_001",
        "family": "setup_window_removed",
        "minimal_delta": "Scyther survives Rock Throw -> Rock Throw is a guaranteed KO after the setup turn",
        "changes": [
            {"path": "position_snapshot.boss_active.hp", "value": "70%"},
            {
                "path": "position_snapshot.mechanics.setup_survives_worst_plausible_branch",
                "value": False,
            },
            {
                "path": "position_snapshot.damage_bands.opponent_rock_throw_vs_boss_active.ko_at_current_hp",
                "value": "guaranteed",
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Geodude's plausible Rock Throw now KOs after the setup turn, so Swords Dance loses the boosted route before it can convert.",
            },
        ],
        "expected_base_move_id": "move_swords_dance",
        "expected_mutated_move_id": "move_wing_attack",
        "principle": "setup is correct only while the worst plausible punish leaves the boosted route alive",
    },
    {
        "mutation_id": "mut_psychic_pivot_unavailable_sleep_fallback_001",
        "base_id": "fixture_chuck_poliwrath_vs_alakazam_psychic_pivot_001",
        "family": "defensive_answer_unavailable",
        "minimal_delta": "position_snapshot.boss_bench: remove Umbreon",
        "changes": [
            {
                "path": "position_snapshot.boss_bench",
                "value": ["Sudowoodo", "Hitmontop", "Hitmonlee"],
            },
        ],
        "expected_base_move_id": "switch_umbreon",
        "expected_mutated_move_id": "move_hypnosis",
        "principle": "accuracy-dependent sleep becomes the fallback control line only when the clean Psychic pivot is unavailable",
    },
    {
        "mutation_id": "mut_morty_sleep_clause_blocks_hypnosis_001",
        "base_id": "fixture_morty_haunter_vs_noctowl_sleep_line_001",
        "family": "sleep_clause_occupied",
        "minimal_delta": "position_snapshot.field.sleep_clause: free -> occupied",
        "changes": [
            {"path": "position_snapshot.field.sleep_clause", "value": "occupied"},
        ],
        "expected_base_move_id": "move_hypnosis",
        "expected_mutated_move_id": "move_night_shade",
        "principle": "sleep pressure is a route only while Sleep Clause and target status make it legal",
    },
    {
        "mutation_id": "mut_falkner_probe_unneeded_attack_now_001",
        "base_id": "fixture_falkner_pidgeotto_vs_geodude_scout_probe_001",
        "family": "scout_probe_removed",
        "minimal_delta": "public Rock-risk probe needed -> no meaningful Rock-risk branch",
        "changes": [
            {"path": "position_snapshot.mechanics.public_probe_needed", "value": False},
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Geodude has no meaningful public Rock-risk branch in this mutation, so Sand Attack no longer buys enough safety to beat direct Gust progress.",
            },
        ],
        "expected_base_move_id": "move_sand_attack",
        "expected_mutated_move_id": "move_gust",
        "principle": "scout or accuracy probes need a live punish branch; otherwise the policy should take direct progress",
    },
    {
        "mutation_id": "mut_pryce_cloyster_survives_attack_now_001",
        "base_id": "fixture_pryce_cloyster_vs_quilava_fire_pivot_001",
        "family": "fast_public_punish_removed",
        "minimal_delta": "Cloyster is KOed before progress -> Cloyster survives Flame Wheel and Surf converts",
        "changes": [
            {"path": "position_snapshot.boss_active.hp", "value": "88%"},
            {
                "path": "position_snapshot.mechanics.active_faints_before_progress",
                "value": False,
            },
            {
                "path": "position_snapshot.mechanics.active_survives_public_punish",
                "value": True,
            },
            {
                "path": "position_snapshot.damage_bands.opponent_flame_wheel_vs_boss_active.ko_at_current_hp",
                "value": "never",
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Cloyster now survives the public Flame Wheel branch, so Surf can punish Quilava without spending the future Explosion/Spikes resource or needing the Slowking pivot first.",
            },
        ],
        "expected_base_move_id": "switch_slowking",
        "expected_mutated_move_id": "move_surf",
        "principle": "switching out of a bad matchup dominates while the active faints before progress, but direct attack takes over once survival evidence makes the route immediate",
    },
    {
        "mutation_id": "mut_bugsy_fire_setup_window_removed_001",
        "base_id": "fixture_bugsy_scyther_vs_quilava_fire_setup_001",
        "family": "setup_window_removed",
        "minimal_delta": "Scyther survives one Ember -> Ember removes the setup route before +2 Wing Attack converts",
        "changes": [
            {"path": "position_snapshot.boss_active.hp", "value": "45%"},
            {
                "path": "position_snapshot.mechanics.setup_survives_worst_plausible_branch",
                "value": False,
            },
            {
                "path": "position_snapshot.damage_bands.opponent_ember_vs_boss_active.ko_at_current_hp",
                "value": "guaranteed",
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Quilava's revealed Ember now removes Scyther after a setup turn, so Swords Dance loses the boosted route before it converts and Wing Attack is the best forced progress.",
            },
        ],
        "expected_base_move_id": "move_swords_dance",
        "expected_mutated_move_id": "move_wing_attack",
        "principle": "setup under public Fire pressure is correct only while speed, survival, and boosted damage preserve the two-turn route",
    },
    {
        "mutation_id": "mut_whitney_rollout_after_status_001",
        "base_id": "fixture_whitney_miltank_vs_geodude_rollout_lock_001",
        "family": "lock_move_safe_after_status",
        "minimal_delta": "Geodude unstatused and Rollout unsafe -> Geodude paralyzed and Rollout safe",
        "changes": [
            {"path": "position_snapshot.opponent_active.status", "value": "par"},
            {"path": "position_snapshot.mechanics.lock_move_safe", "value": True},
            {
                "path": "position_snapshot.mechanics.lock_after_status_or_safe_state",
                "value": True,
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Geodude is now paralyzed and Miltank remains healthy, so the taught pressure line can switch from Body Slam setup pressure to Rollout lock conversion.",
            },
        ],
        "expected_base_move_id": "move_body_slam",
        "expected_mutated_move_id": "move_rollout",
        "principle": "lock moves are route conversions only after status or safety changes the board",
    },
    {
        "mutation_id": "mut_karen_toxic_clock_no_survival_001",
        "base_id": "fixture_karen_crobat_vs_dragonite_toxic_clock_001",
        "family": "status_clock_survival_removed",
        "minimal_delta": "Crobat survives one Outrage after Toxic -> Crobat cannot keep the clock route alive",
        "changes": [
            {"path": "position_snapshot.boss_active.hp", "value": "38%"},
            {
                "path": "position_snapshot.mechanics.status_clock_survives_punish",
                "value": False,
            },
            {
                "path": "position_snapshot.damage_bands.opponent_outrage_vs_boss_active.ko_at_current_hp",
                "value": "guaranteed",
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Dragonite's revealed Outrage now removes Crobat after the status attempt, so Karen should preserve the status pivot and use Tyranitar as the anti-Dragon route.",
            },
        ],
        "expected_base_move_id": "move_toxic",
        "expected_mutated_move_id": "switch_tyranitar",
        "principle": "a Toxic clock is only the first move when the user survives the immediate route punish or the sacrifice is explicitly justified",
    },
    {
        "mutation_id": "mut_koga_ko_removed_preserve_umbreon_001",
        "base_id": "fixture_koga_crobat_vs_alakazam_immediate_ko_001",
        "family": "immediate_ko_threshold_removed",
        "minimal_delta": "Wing Attack KOs now -> Wing Attack no longer KOs before Psychic/Recover pressure",
        "changes": [
            {"path": "position_snapshot.opponent_active.hp", "value": "84%"},
            {"path": "position_snapshot.mechanics.direct_ko_available", "value": False},
            {
                "path": "position_snapshot.damage_bands.boss_wing_attack_vs_opponent_active.ko_at_current_hp",
                "value": "never",
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Wing Attack no longer removes Alakazam before Psychic or Recover pressure, so Koga should preserve Crobat and use Umbreon as the clean public answer.",
            },
        ],
        "expected_base_move_id": "move_wing_attack",
        "expected_mutated_move_id": "switch_umbreon",
        "principle": "direct KO damage dominates slow status, but preservation takes over once the KO threshold disappears",
    },
    {
        "mutation_id": "mut_jasmine_real_boost_requires_whirlwind_001",
        "base_id": "fixture_jasmine_skarmory_vs_machoke_focus_energy_001",
        "family": "weak_setup_signal_to_real_boost",
        "minimal_delta": "Focus Energy is low-urgency setup -> Machoke has a real attack-boost route",
        "changes": [
            {
                "path": "position_snapshot.opponent_active.revealed_moves",
                "value": ["Attack-boosting setup", "Karate Chop"],
            },
            {"path": "position_snapshot.mechanics.weak_setup_signal", "value": False},
            {
                "path": "position_snapshot.mechanics.phazing_required_for_boost",
                "value": True,
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Machoke now has a real attack-boost route rather than only Focus Energy, so Whirlwind should deny the boost before Toxic or Steel Wing can convert.",
            },
        ],
        "expected_base_move_id": "move_toxic",
        "expected_mutated_move_id": "move_whirlwind",
        "principle": "phazing dominates status only when the setup route is dangerous enough to deny now",
    },
    {
        "mutation_id": "mut_morty_perish_route_cannot_survive_001",
        "base_id": "fixture_morty_misdreavus_vs_typhlosion_perish_route_001",
        "family": "perish_route_survival_removed",
        "minimal_delta": "Misdreavus survives Flame Wheel to start Perish Song -> Misdreavus is KOed before the clock starts",
        "changes": [
            {"path": "position_snapshot.boss_active.hp", "value": "38%"},
            {
                "path": "position_snapshot.mechanics.perish_route_survives_punish",
                "value": False,
            },
            {
                "path": "position_snapshot.damage_bands.opponent_flame_wheel_vs_boss_active.ko_at_current_hp",
                "value": "guaranteed",
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Typhlosion's revealed Flame Wheel now removes Misdreavus before Perish Song can start, so Morty should preserve through Gengar instead of trying to create the clock.",
            },
        ],
        "expected_base_move_id": "move_perish_song",
        "expected_mutated_move_id": "switch_gengar",
        "principle": "Perish Song is a route only if the user can survive long enough to start the countdown",
    },
    {
        "mutation_id": "mut_whitney_encore_trap_absent_double_team_001",
        "base_id": "fixture_whitney_clefairy_vs_bayleef_encore_reflect_001",
        "family": "encore_trap_absent",
        "minimal_delta": "Bayleef just used Reflect and Clefairy is faster -> no visible Encore trap",
        "changes": [
            {"path": "position_snapshot.field.player_last_move", "value": "Razor Leaf"},
            {"path": "position_snapshot.mechanics.encore_trap_live", "value": False},
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Bayleef no longer has a visible low-value Reflect last move to trap, so Encore becomes speculative and Clefairy should use one Double Team setup turn while the public hit is survivable.",
            },
        ],
        "expected_base_move_id": "move_encore",
        "expected_mutated_move_id": "move_double_team",
        "principle": "Encore is a must-click only with public last-move and speed evidence; otherwise safe one-turn setup can dominate",
    },
    {
        "mutation_id": "mut_jasmine_speed_control_to_direct_ko_001",
        "base_id": "fixture_jasmine_magneton_vs_quilava_speed_control_001",
        "family": "speed_control_to_direct_ko",
        "minimal_delta": "Thunderbolt does not KO -> Thunderbolt is public direct removal",
        "changes": [
            {"path": "position_snapshot.opponent_active.hp", "value": "24%"},
            {"path": "position_snapshot.mechanics.direct_ko_available", "value": True},
            {
                "path": "position_snapshot.damage_bands.boss_thunderbolt_vs_opponent_active.ko_at_current_hp",
                "value": "guaranteed",
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Quilava is now low enough that Thunderbolt removes the active threat before speed-control status needs to buy future turns.",
            },
        ],
        "expected_base_move_id": "move_thunder_wave",
        "expected_mutated_move_id": "move_thunderbolt",
        "principle": "Speed-control status is correct only while it creates future turns; public direct removal dominates once it is available",
    },
    {
        "mutation_id": "mut_misty_recovery_window_opens_001",
        "base_id": "fixture_misty_starmie_vs_meganium_recover_tempo_001",
        "family": "recovery_window_opens",
        "minimal_delta": "Meganium can immediately punish -> Meganium is asleep and Psychic no longer changes cleanup math",
        "changes": [
            {"path": "position_snapshot.opponent_active.status", "value": "sleep"},
            {"path": "position_snapshot.mechanics.recovery_window_live", "value": True},
            {
                "path": "position_snapshot.mechanics.tempo_attack_changes_route",
                "value": False,
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Meganium is asleep this turn and Psychic no longer changes the Lapras cleanup band, so Recover preserves Starmie before the next re-score.",
            },
        ],
        "expected_base_move_id": "move_psychic",
        "expected_mutated_move_id": "move_recover",
        "principle": "Reliable recovery is correct only when a real window opens and recovery preserves a route better than immediate progress",
    },
    {
        "mutation_id": "mut_clair_hidden_ice_absent_attack_now_001",
        "base_id": "fixture_clair_dragonair_vs_suicune_hidden_ice_001",
        "family": "hidden_coverage_absent",
        "minimal_delta": "Suicune staying implies hidden Ice pressure -> hidden Ice pressure no longer plausible",
        "changes": [
            {
                "path": "position_snapshot.opponent_active.public_priors",
                "value": ["Rest plausible", "Suicune likely pivots out"],
            },
            {
                "path": "position_snapshot.mechanics.hidden_coverage_punish_plausible",
                "value": False,
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Suicune no longer has a plausible public Ice punish into Dragonair, so Thunder can claim direct pressure instead of pivoting first.",
            },
        ],
        "expected_base_move_id": "switch_kingdra",
        "expected_mutated_move_id": "move_thunder",
        "principle": "Hidden-info preservation dominates only while the punish is legal, plausible, and severe enough to change the route",
    },
    {
        "mutation_id": "mut_bugsy_status_clock_already_started_001",
        "base_id": "fixture_bugsy_ariados_vs_pidgey_status_clock_001",
        "family": "status_clock_already_started",
        "minimal_delta": "Pidgey unstatused -> Pidgey already toxic and Ariados has created the clock",
        "changes": [
            {"path": "position_snapshot.opponent_active.status", "value": "tox"},
            {
                "path": "position_snapshot.mechanics.status_clock_survives_punish",
                "value": False,
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Pidgey is already toxic, so repeating Toxic no longer creates progress; Ariados can preserve its HP and bring Scyther in after the clock exists.",
            },
        ],
        "expected_base_move_id": "move_toxic",
        "expected_mutated_move_id": "switch_scyther",
        "principle": "Status clock policy is not repeated status: once the clock exists, re-score the follow-up route",
    },
    {
        "mutation_id": "mut_morty_direct_removal_absent_destiny_bond_001",
        "base_id": "fixture_morty_gengar_vs_kadabra_destiny_bond_001",
        "family": "direct_removal_absent_sacrifice_trade",
        "minimal_delta": "direct_ko_available: true -> false",
        "changes": [
            {"path": "position_snapshot.opponent_active.hp", "value": "91%"},
            {"path": "position_snapshot.mechanics.direct_ko_available", "value": False},
            {"path": "position_snapshot.mechanics.sacrifice_trade_live", "value": True},
            {"path": "position_snapshot.mechanics.sacrifice_trade_forced", "value": True},
            {
                "path": "position_snapshot.damage_bands.boss_shadow_ball_vs_opponent_active.ko_at_current_hp",
                "value": "never",
            },
            {
                "path": "position_snapshot.damage_bands.boss_shadow_ball_vs_opponent_active.damage_low_pct",
                "value": 58,
            },
            {
                "path": "position_snapshot.damage_bands.boss_shadow_ball_vs_opponent_active.damage_high_pct",
                "value": 69,
            },
            {
                "path": "public_opponent_model.immediate_punish",
                "value": "Kadabra is now outside Shadow Ball removal range and can KO Gengar after surviving, so Destiny Bond becomes the forced route trade instead of a wasteful sacrifice.",
            },
            {
                "path": "hidden_info_visible_to_policy.damage_boundary",
                "value": "Shadow Ball no longer removes Kadabra from the public HP band.",
            },
        ],
        "oracle_overrides": {
            "best": ["move_destiny_bond"],
            "acceptable": ["switch_misdreavus"],
            "catastrophic": ["move_spikes", "move_shadow_ball"],
        },
        "expected_base_move_id": "move_shadow_ball",
        "expected_mutated_move_id": "move_destiny_bond",
        "principle": "Sacrifice trade becomes correct only after direct removal no longer converts the route",
    },
]


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PreferenceDataError(f"{path}: invalid JSON: {exc}") from exc


def nonempty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def validate_benchmark_data(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["benchmark root must be an object"]
    if data.get("schema_version") != 1:
        errors.append("benchmark schema_version must be 1")
    benchmarks = data.get("benchmarks")
    if not isinstance(benchmarks, list):
        return [*errors, "benchmark file must contain a benchmarks list"]

    seen_ids: set[str] = set()
    for index, benchmark in enumerate(benchmarks):
        prefix = f"benchmarks[{index}]"
        if not isinstance(benchmark, dict):
            errors.append(f"{prefix}: benchmark must be an object")
            continue

        missing = sorted(REQUIRED_BENCHMARK_FIELDS - set(benchmark))
        if missing:
            errors.append(f"{prefix}: missing required field(s): {', '.join(missing)}")

        benchmark_id = benchmark.get("id")
        if not isinstance(benchmark_id, str) or not benchmark_id:
            errors.append(f"{prefix}: missing id")
        elif benchmark_id in seen_ids:
            errors.append(f"{prefix}: duplicate id {benchmark_id!r}")
        else:
            seen_ids.add(benchmark_id)

        profile = benchmark.get("mechanics_profile")
        if profile not in ALLOWED_MECHANICS_PROFILES:
            errors.append(
                f"{prefix}: mechanics_profile must be one of "
                f"{', '.join(sorted(ALLOWED_MECHANICS_PROFILES))}"
            )

        split = benchmark.get("split")
        if split not in ALLOWED_BENCHMARK_SPLITS:
            errors.append(
                f"{prefix}: split must be one of "
                f"{', '.join(sorted(ALLOWED_BENCHMARK_SPLITS))}"
            )

        if not nonempty_list(benchmark.get("source_refs")):
            errors.append(f"{prefix}: source_refs must be a non-empty list")
        if not nonempty_list(benchmark.get("tags")):
            errors.append(f"{prefix}: tags must be a non-empty list")
        if not isinstance(benchmark.get("position"), dict):
            errors.append(f"{prefix}: position must be an object")

        labels = {
            move.get("label")
            for move in benchmark.get("candidate_moves", [])
            if isinstance(move, dict)
        }
        if not nonempty_list(benchmark.get("candidate_moves")):
            errors.append(f"{prefix}: candidate_moves must be a non-empty list")
        missing_labels = sorted(REQUIRED_OUTCOME_LABELS - labels)
        if missing_labels:
            errors.append(
                f"{prefix}: candidate_moves missing label(s): "
                f"{', '.join(missing_labels)}"
            )

        for group_name in ("current_win_conditions", "irreplaceable_pieces"):
            group = benchmark.get(group_name)
            if not isinstance(group, dict):
                errors.append(f"{prefix}: {group_name} must be an object")
                continue
            for side in ("boss", "opponent"):
                if not nonempty_list(group.get(side)):
                    errors.append(f"{prefix}: {group_name}.{side} must be non-empty")

        opponent_model = benchmark.get("opponent_model")
        if not isinstance(opponent_model, dict):
            errors.append(f"{prefix}: opponent_model must be an object")
        else:
            missing_tiers = sorted(REQUIRED_OPPONENT_TIERS - set(opponent_model))
            if missing_tiers:
                errors.append(
                    f"{prefix}: opponent_model missing tier(s): "
                    f"{', '.join(missing_tiers)}"
                )

        catastrophe = benchmark.get("catastrophe_branch")
        if not isinstance(catastrophe, dict):
            errors.append(f"{prefix}: catastrophe_branch must be an object")
        else:
            for key in ("trigger", "consequence"):
                if not isinstance(catastrophe.get(key), str) or not catastrophe[key]:
                    errors.append(f"{prefix}: catastrophe_branch.{key} is required")

        if not nonempty_list(benchmark.get("information_that_changes_answer")):
            errors.append(
                f"{prefix}: information_that_changes_answer must be non-empty"
            )

        arbitration = benchmark.get("arbitration")
        if not isinstance(arbitration, dict):
            errors.append(f"{prefix}: arbitration must be an object")
        else:
            if not nonempty_list(arbitration.get("competing_heuristics")):
                errors.append(
                    f"{prefix}: arbitration.competing_heuristics must be non-empty"
                )
            if not isinstance(arbitration.get("dominant_policy"), str) or not arbitration[
                "dominant_policy"
            ]:
                errors.append(f"{prefix}: arbitration.dominant_policy is required")
    return errors


def candidate_move_id(move: Any) -> str:
    if isinstance(move, dict):
        return str(move.get("id", ""))
    return str(move)


def validate_public_card_data(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["public benchmark root must be an object"]
    if data.get("schema_version") != 1:
        errors.append("public benchmark schema_version must be 1")
    cards = data.get("cards")
    if not isinstance(cards, list):
        return [*errors, "public benchmark file must contain a cards list"]

    seen_ids: set[str] = set()
    for index, card in enumerate(cards):
        prefix = f"cards[{index}]"
        if not isinstance(card, dict):
            errors.append(f"{prefix}: public card must be an object")
            continue

        missing = sorted(REQUIRED_PUBLIC_CARD_FIELDS - set(card))
        if missing:
            errors.append(f"{prefix}: missing required field(s): {', '.join(missing)}")

        card_id = card.get("id")
        if not isinstance(card_id, str) or not card_id:
            errors.append(f"{prefix}: missing id")
        elif card_id in seen_ids:
            errors.append(f"{prefix}: duplicate id {card_id!r}")
        else:
            seen_ids.add(card_id)

        if card.get("mechanics_profile") not in ALLOWED_MECHANICS_PROFILES:
            errors.append(f"{prefix}: invalid mechanics_profile")
        if card.get("split") not in ALLOWED_BENCHMARK_SPLITS:
            errors.append(f"{prefix}: invalid split")
        if not nonempty_list(card.get("source_refs")):
            errors.append(f"{prefix}: source_refs must be a non-empty list")
        if not nonempty_list(card.get("tags")):
            errors.append(f"{prefix}: tags must be a non-empty list")
        if not isinstance(card.get("position_snapshot"), dict):
            errors.append(f"{prefix}: position_snapshot must be an object")
        if not nonempty_list(card.get("candidate_moves_public")):
            errors.append(f"{prefix}: candidate_moves_public must be non-empty")
        if not nonempty_list(card.get("required_answer_fields")):
            errors.append(f"{prefix}: required_answer_fields must be non-empty")
        if not isinstance(card.get("hidden_info_visible_to_policy"), dict):
            errors.append(f"{prefix}: hidden_info_visible_to_policy must be an object")
        if not isinstance(card.get("public_opponent_model"), dict):
            errors.append(f"{prefix}: public_opponent_model must be an object")
        else:
            missing_tiers = sorted(REQUIRED_OPPONENT_TIERS - set(card["public_opponent_model"]))
            if missing_tiers:
                errors.append(
                    f"{prefix}: public_opponent_model missing tier(s): "
                    f"{', '.join(missing_tiers)}"
                )

        forbidden = {
            "candidate_moves",
            "catastrophe_branch",
            "information_that_changes_answer",
            "arbitration",
            "current_win_conditions",
            "irreplaceable_pieces",
            "oracle",
        } & set(card)
        if forbidden:
            errors.append(
                f"{prefix}: public card contains oracle-only field(s): "
                f"{', '.join(sorted(forbidden))}"
            )

        for move_index, move in enumerate(card.get("candidate_moves_public", [])):
            if not isinstance(move, dict):
                errors.append(
                    f"{prefix}.candidate_moves_public[{move_index}]: move must be an object"
                )
                continue
            if not isinstance(move.get("id"), str) or not move["id"]:
                errors.append(
                    f"{prefix}.candidate_moves_public[{move_index}]: id is required"
                )
            leaked = {"label", "reason", "classification"} & set(move)
            if leaked:
                errors.append(
                    f"{prefix}.candidate_moves_public[{move_index}]: "
                    f"oracle label field leaked: {', '.join(sorted(leaked))}"
                )
    return errors


def validate_oracle_data(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["oracle root must be an object"]
    if data.get("schema_version") != 1:
        errors.append("oracle schema_version must be 1")
    oracles = data.get("oracles")
    if not isinstance(oracles, list):
        return [*errors, "oracle file must contain an oracles list"]

    seen_ids: set[str] = set()
    for index, row in enumerate(oracles):
        prefix = f"oracles[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix}: oracle row must be an object")
            continue
        oracle_id = row.get("id")
        if not isinstance(oracle_id, str) or not oracle_id:
            errors.append(f"{prefix}: missing id")
        elif oracle_id in seen_ids:
            errors.append(f"{prefix}: duplicate id {oracle_id!r}")
        else:
            seen_ids.add(oracle_id)

        oracle = row.get("oracle")
        if not isinstance(oracle, dict):
            errors.append(f"{prefix}: oracle must be an object")
            continue
        missing = sorted(REQUIRED_ORACLE_FIELDS - set(oracle))
        if missing:
            errors.append(f"{prefix}: missing oracle field(s): {', '.join(missing)}")
        for label in REQUIRED_OUTCOME_LABELS:
            if not nonempty_list(oracle.get(label)):
                errors.append(f"{prefix}: oracle.{label} must be non-empty")
        for group_name in ("current_win_conditions", "irreplaceable_pieces"):
            group = oracle.get(group_name)
            if not isinstance(group, dict):
                errors.append(f"{prefix}: oracle.{group_name} must be an object")
                continue
            for side in ("boss", "opponent"):
                if not nonempty_list(group.get(side)):
                    errors.append(
                        f"{prefix}: oracle.{group_name}.{side} must be non-empty"
                    )
        if not nonempty_list(oracle.get("catastrophe_branches")):
            errors.append(f"{prefix}: oracle.catastrophe_branches must be non-empty")
        if not nonempty_list(oracle.get("answer_changing_information")):
            errors.append(
                f"{prefix}: oracle.answer_changing_information must be non-empty"
            )
        if not isinstance(oracle.get("heuristic_arbitration"), dict):
            errors.append(f"{prefix}: oracle.heuristic_arbitration must be an object")
    return errors


def validate_policy_answer_data(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["policy answer root must be an object"]
    if data.get("schema_version") != 1:
        errors.append("policy answer schema_version must be 1")
    if not isinstance(data.get("policy_name"), str) or not data["policy_name"]:
        errors.append("policy answer policy_name is required")
    answers = data.get("answers")
    if not isinstance(answers, list):
        return [*errors, "policy answer file must contain an answers list"]
    for index, answer in enumerate(answers):
        prefix = f"answers[{index}]"
        if not isinstance(answer, dict):
            errors.append(f"{prefix}: answer must be an object")
            continue
        missing = sorted(REQUIRED_POLICY_ANSWER_FIELDS - set(answer))
        if missing:
            errors.append(f"{prefix}: missing field(s): {', '.join(missing)}")
        if answer.get("decision_status") not in {"action", "needs_context"}:
            errors.append(f"{prefix}: invalid decision_status")
        if not nonempty_list(answer.get("candidate_ranking")):
            errors.append(f"{prefix}: candidate_ranking must be non-empty")
        for field in (
            "current_win_conditions",
            "irreplaceable_pieces",
            "catastrophe_branches",
            "answer_changing_information",
            "rules_fired",
        ):
            if not nonempty_list(answer.get(field)):
                errors.append(f"{prefix}: {field} must be non-empty")
    return errors


def load_legacy_benchmarks(
    path: Path = DEFAULT_LEGACY_BENCHMARKS_PATH,
) -> list[dict[str, Any]]:
    data = read_json(path)
    errors = validate_benchmark_data(data)
    if errors:
        raise PreferenceDataError("\n".join(errors))
    return list(data["benchmarks"])


def load_benchmarks(path: Path = DEFAULT_PUBLIC_BENCHMARKS_PATH) -> list[dict[str, Any]]:
    data = read_json(path)
    errors = validate_public_card_data(data)
    if errors:
        raise PreferenceDataError("\n".join(errors))
    return list(data["cards"])


def load_benchmark_oracles(
    path: Path = DEFAULT_BENCHMARK_ORACLES_PATH,
) -> list[dict[str, Any]]:
    data = read_json(path)
    errors = validate_oracle_data(data)
    if errors:
        raise PreferenceDataError("\n".join(errors))
    return list(data["oracles"])


def oracle_map(oracles: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["id"]): dict(row["oracle"]) for row in oracles}


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def move_ids_by_label(oracle: dict[str, Any]) -> dict[str, list[str]]:
    labels: dict[str, list[str]] = {label: [] for label in REQUIRED_OUTCOME_LABELS}
    for label in REQUIRED_OUTCOME_LABELS:
        labels[label] = [str(move_id) for move_id in oracle.get(label, [])]
    return labels


def move_label_by_id(oracle: dict[str, Any]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for label, move_ids in move_ids_by_label(oracle).items():
        for move_id in move_ids:
            labels[move_id] = label
    return labels


def load_benchmark_answers(path: Path) -> dict[str, str]:
    data = read_json(path)
    if isinstance(data, dict) and "answers" not in data:
        return {
            str(benchmark_id): str(move_id)
            for benchmark_id, move_id in data.items()
        }
    if not isinstance(data, dict) or not isinstance(data.get("answers"), list):
        raise PreferenceDataError("benchmark answers must be an object or answers list")
    errors = validate_policy_answer_data(data)
    if errors:
        raise PreferenceDataError("\n".join(errors))

    answers: dict[str, str] = {}
    for index, answer in enumerate(data["answers"]):
        if not isinstance(answer, dict):
            raise PreferenceDataError(f"answers[{index}]: answer must be an object")
        benchmark_id = answer.get("benchmark_id")
        move_id = answer.get("chosen_move_id")
        if not isinstance(benchmark_id, str) or not benchmark_id:
            raise PreferenceDataError(f"answers[{index}]: benchmark_id is required")
        if not isinstance(move_id, str) or not move_id:
            raise PreferenceDataError(f"answers[{index}]: chosen_move_id is required")
        answers[benchmark_id] = move_id
    return answers


def parse_percent(value: Any) -> int | None:
    if isinstance(value, (int, float)):
        return int(value)
    if not isinstance(value, str):
        return None
    digits = "".join(character for character in value if character.isdigit())
    return int(digits) if digits else None


def damage_band(position: dict[str, Any], key: str) -> dict[str, Any]:
    bands = position.get("damage_bands")
    if not isinstance(bands, dict):
        return {}
    row = bands.get(key)
    return dict(row) if isinstance(row, dict) else {}


def damage_band_ko_status(row: dict[str, Any]) -> str:
    status = str(row.get("ko_at_current_hp", "")).lower()
    if status in {"guaranteed", "never", "possible"}:
        return status
    low = row.get("damage_low")
    high = row.get("damage_high")
    hp = row.get("defender_current_hp")
    if not all(isinstance(value, int) for value in (low, high, hp)):
        return "unknown"
    if low >= hp:
        return "guaranteed"
    if high < hp:
        return "never"
    return "possible"


def move_pp(position: dict[str, Any], move_id: str) -> int | None:
    pp = position.get("pp")
    if not isinstance(pp, dict):
        return None
    active_pp = pp.get("boss_active")
    if not isinstance(active_pp, dict):
        return None
    token = move_id.removeprefix("move_").replace("_", " ").lower()
    for key, value in active_pp.items():
        normalized = str(key).replace("_", " ").lower()
        if normalized == token and isinstance(value, int):
            return value
    return None


def move_class(move_id: str) -> str:
    if move_id.startswith("switch_"):
        return "switch"
    token = move_id.removeprefix("move_")
    if token in PHAZING_MOVE_TOKENS:
        return "phazing"
    if token in HAZARD_REMOVAL_MOVE_TOKENS:
        return "hazard_removal"
    if token in SLEEP_MOVE_TOKENS:
        return "sleep"
    if token in SLEEP_ONLY_MOVE_TOKENS:
        return "sleep_only"
    if token in SCOUT_MOVE_TOKENS:
        return "scout"
    if token in PROTECT_MOVE_TOKENS:
        return "protect"
    if token in ENCORE_MOVE_TOKENS:
        return "encore"
    if token in LOCK_MOVE_TOKENS:
        return "lock"
    if token in PERISH_MOVE_TOKENS:
        return "perish"
    if token in SACRIFICE_MOVE_TOKENS:
        return "sacrifice"
    if token in SETUP_MOVE_TOKENS:
        return "setup"
    if token in RECOVERY_MOVE_TOKENS:
        return "recovery"
    if token in STATUS_MOVE_TOKENS:
        return "status"
    if token in {"explosion", "selfdestruct"}:
        return "explosion"
    if token == "spikes":
        return "hazard"
    return "attack"


def text_contains_any(text: str, needles: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(needle in lower for needle in needles)


def normalized_token(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def bench_contains_target(position: dict[str, Any], switch_move_id: str) -> bool:
    bench = position.get("boss_bench")
    if not isinstance(bench, list):
        return True
    target = normalized_token(switch_move_id.removeprefix("switch_"))
    for member in bench:
        if isinstance(member, dict):
            species = str(member.get("species", ""))
        else:
            species = str(member)
        if normalized_token(species) == target:
            return True
    return False


def score_benchmark_candidate(
    benchmark: dict[str, Any],
    move_id: str,
) -> dict[str, Any]:
    tags = set(benchmark["tags"])
    profile = str(benchmark["mechanics_profile"])
    position = benchmark.get("position_snapshot") or benchmark.get("position", {})
    field = position.get("field", {}) if isinstance(position.get("field"), dict) else {}
    boss_active = (
        position.get("boss_active", {})
        if isinstance(position.get("boss_active"), dict)
        else {}
    )
    opponent_active = (
        position.get("opponent_active", {})
        if isinstance(position.get("opponent_active"), dict)
        else {}
    )
    mechanics = (
        position.get("mechanics", {})
        if isinstance(position.get("mechanics"), dict)
        else {}
    )
    immediate_setup_route = bool(mechanics.get("immediate_setup_route", False))
    sleep_window_available = bool(mechanics.get("sleep_window_available", False))
    setup_changes_ko_math = bool(mechanics.get("setup_changes_ko_math", False))
    setup_survives_worst_plausible_branch = bool(
        mechanics.get("setup_survives_worst_plausible_branch", False)
    )
    setup_changes_route = bool(mechanics.get("setup_changes_route", False))
    active_faints_before_progress = bool(
        mechanics.get("active_faints_before_progress", False)
    )
    active_survives_public_punish = bool(
        mechanics.get("active_survives_public_punish", False)
    )
    lock_move_safe = bool(mechanics.get("lock_move_safe", False))
    lock_after_status_or_safe_state = bool(
        mechanics.get("lock_after_status_or_safe_state", False)
    )
    public_probe_needed = bool(mechanics.get("public_probe_needed", False))
    single_probe_then_progress = bool(
        mechanics.get("single_probe_then_progress", False)
    )
    active_target_grounded = bool(mechanics.get("active_target_grounded", False))
    fallback_attack = str(mechanics.get("fallback_attack_if_no_pivot", ""))
    fallback_setup_attack = str(
        mechanics.get("fallback_attack_if_setup_unsafe", "")
    )
    fallback_encore_setup = str(
        mechanics.get("fallback_setup_if_encore_absent", "")
    )
    fallback_probe_attack = str(
        mechanics.get("fallback_attack_if_probe_unneeded", "")
    )
    fallback_survival_attack = str(
        mechanics.get("fallback_attack_if_active_survives", "")
    )
    status_pressure_move = str(mechanics.get("status_pressure_move", ""))
    status_clock_move = str(mechanics.get("status_clock_move", ""))
    status_clock_live = bool(mechanics.get("status_clock_live", False))
    status_clock_survives_punish = bool(
        mechanics.get("status_clock_survives_punish", False)
    )
    direct_attack_low_impact = bool(
        mechanics.get("direct_attack_low_impact", False)
    )
    fallback_status_pivot = str(
        mechanics.get("fallback_pivot_if_status_unsafe", "")
    )
    direct_ko_move = str(mechanics.get("direct_ko_move", ""))
    direct_ko_available = bool(mechanics.get("direct_ko_available", False))
    fallback_ko_pivot = str(
        mechanics.get("fallback_pivot_if_ko_unavailable", "")
    )
    tempo_attack_move = str(mechanics.get("tempo_attack_move", ""))
    tempo_attack_changes_route = bool(
        mechanics.get("tempo_attack_changes_route", False)
    )
    recovery_move = str(mechanics.get("recovery_move", ""))
    recovery_window_live = bool(mechanics.get("recovery_window_live", False))
    hidden_coverage_punish_plausible = bool(
        mechanics.get("hidden_coverage_punish_plausible", False)
    )
    primary_hidden_coverage_pivot = str(
        mechanics.get("primary_hidden_coverage_pivot", "")
    )
    fallback_hidden_coverage_pivot = str(
        mechanics.get("fallback_hidden_coverage_pivot", "")
    )
    fallback_hidden_coverage_attack = str(
        mechanics.get("fallback_attack_if_hidden_coverage_absent", "")
    )
    weak_setup_signal = bool(mechanics.get("weak_setup_signal", False))
    phazing_required_for_boost = bool(
        mechanics.get("phazing_required_for_boost", False)
    )
    perish_route_live = bool(mechanics.get("perish_route_live", False))
    perish_route_survives_punish = bool(
        mechanics.get("perish_route_survives_punish", False)
    )
    fallback_perish_pivot = str(
        mechanics.get("fallback_pivot_if_perish_unsafe", "")
    )
    sacrifice_trade_move = str(mechanics.get("sacrifice_trade_move", ""))
    sacrifice_trade_live = bool(mechanics.get("sacrifice_trade_live", False))
    sacrifice_trade_forced = bool(mechanics.get("sacrifice_trade_forced", False))
    encore_trap_live = bool(mechanics.get("encore_trap_live", False))
    encore_user_faster = bool(mechanics.get("encore_user_faster", False))
    encore_locks_low_value_move = bool(
        mechanics.get("encore_locks_low_value_move", False)
    )
    safe_one_setup_turn = bool(mechanics.get("safe_one_setup_turn", False))
    double_switch_spikes_window = bool(
        mechanics.get("double_switch_spikes_window", False)
    )
    opening_reveal_value = bool(mechanics.get("opening_reveal_value", False))
    opening_direct_pressure_needed = bool(
        mechanics.get("opening_direct_pressure_needed", False)
    )
    opponent_model = benchmark.get("public_opponent_model") or benchmark.get(
        "opponent_model",
        {},
    )
    immediate_punish = str(opponent_model.get("immediate_punish", ""))
    summary = str(position.get("summary", ""))
    opponent_attack_band = damage_band(position, "opponent_psychic_vs_boss_active")
    boss_attack_band = damage_band(position, "boss_thunderbolt_vs_opponent_active")
    opponent_attack_ko = damage_band_ko_status(opponent_attack_band)
    boss_attack_ko = damage_band_ko_status(boss_attack_band)
    cls = move_class(move_id)
    score = 0
    reasons: list[str] = []

    player_layers = field.get("player_side_spikes_layers")
    player_layers = int(player_layers) if isinstance(player_layers, int) else None
    boss_side_spikes = str(field.get("boss_side_spikes", "")).lower()
    own_hazards_present = bool(mechanics.get("own_hazards_present", False)) or (
        boss_side_spikes not in {"", "none", "0", "no"}
    )
    rapid_spin_seen = bool(field.get("player_rapid_spin_seen", False))
    grounded_seen = int(field.get("player_grounded_seen", 0) or 0)
    flying_seen = int(field.get("player_flying_seen", 0) or 0)

    if cls == "sleep":
        sleep_clause_free = field.get("sleep_clause") == "free"
        target_unstatused = opponent_active.get("status") in {None, "none"}
        if sleep_clause_free and target_unstatused:
            score += 35
            reasons.append("sleep is legal into an unstatused target")
        else:
            score -= 60
            reasons.append("sleep is blocked by clause or existing status")
        if {"sleep", "setup", "disruption"} <= tags:
            score += 40
            reasons.append("sleep/setup disruption policy recreates the setup window")

    if cls == "setup":
        if fallback_encore_setup and move_id == fallback_encore_setup:
            if encore_trap_live and encore_user_faster and encore_locks_low_value_move:
                score += 45
                reasons.append("one setup turn is acceptable but loses priority to the visible Encore trap")
            elif safe_one_setup_turn:
                score += 85
                reasons.append("one setup turn becomes best when the visible Encore trap is absent")
            else:
                score -= 40
                reasons.append("setup needs either a visible Encore trap alternative or a safe setup turn")
        if {"setup", "safe_setup_window"} <= tags:
            if setup_survives_worst_plausible_branch and setup_changes_route:
                score += 85
                reasons.append("setup is live because the worst plausible branch is survivable and the boost changes the route")
            else:
                score -= 80
                reasons.append("setup is unsafe because the worst plausible branch removes the boosted route")
        if {"sleep_window", "endgame"} <= tags:
            if sleep_window_available and setup_changes_ko_math:
                score += 85
                reasons.append("setup uses a live sleep window to change endgame KO math")
            else:
                score -= 70
                reasons.append("setup window is not live, so setup can be punished before conversion")
        if text_contains_any(summary, ("missed", "after the prior")):
            score -= 35
            reasons.append("setup follows a disrupted or threatened script")
        if (
            not setup_survives_worst_plausible_branch
            and text_contains_any(immediate_punish, ("ko", "attack", "surf", "body slam"))
        ):
            score -= 35
            reasons.append("public punish can hit before setup converts")

    if cls == "hazard":
        if profile == "romhack_gym_leader_lab" and player_layers == 3:
            score -= 100
            reasons.append("local Spikes are already maxed")
        elif (
            profile == "romhack_gym_leader_lab"
            and player_layers == 2
            and not rapid_spin_seen
            and grounded_seen > flying_seen
        ):
            score += 80
            reasons.append("third local Spikes layer is live and hard to remove")
        else:
            score += 10
            reasons.append("hazards have generic long-game value")
        if direct_ko_available and direct_ko_move:
            score -= 70
            reasons.append("hazard turn loses to an available direct-removal route")
        if sacrifice_trade_forced:
            score -= 70
            reasons.append("hazard turn loses to a forced sacrifice-trade route")

    if cls == "hazard_removal":
        if own_hazards_present:
            score += 85
            reasons.append("Rapid Spin removes own-side hazards that tax future route pivots")
            if "endgame" in tags:
                score += 20
                reasons.append("late-game hazard removal preserves remaining switch and phaze routes")
        else:
            score -= 80
            reasons.append("Rapid Spin has no hazard-removal target in the public state")

    if cls == "explosion":
        revealed_moves = [
            str(move).lower()
            for move in opponent_active.get("revealed_moves", [])
            if isinstance(move, str)
        ]
        opponent_species = str(opponent_active.get("species", "")).lower()
        if "protect" in revealed_moves or "ghost" in opponent_species:
            score -= 90
            reasons.append("public Protect or Ghost information can blank Explosion")
        if active_faints_before_progress:
            score -= 90
            reasons.append("faster public punish can KO before Explosion converts")
        elif active_survives_public_punish:
            score -= 35
            reasons.append("Explosion spends a future route resource when direct progress is available")
        if {"explosion", "route_trade"} <= tags:
            hp = parse_percent(boss_active.get("hp"))
            if hp is not None and hp <= 50:
                score += 75
                reasons.append("low-future-value attacker can trade for a route")
            else:
                score += 35
                reasons.append("Explosion may convert but needs route proof")
        elif player_layers == 2:
            score += 30
            reasons.append("Explosion is a possible wall trade but competes with layer completion")
        elif player_layers == 3:
            score += 35
            reasons.append("Explosion remains live after the hazard stack is complete")

    if cls == "switch":
        if not bench_contains_target(position, move_id):
            score -= 100
            reasons.append("switch target is not available on the public bench")
        if "opening_info_resource_bid" in tags and move_id == "switch_cloyster":
            if double_switch_spikes_window:
                score += 90
                reasons.append("double-switch can catch the expected pivot and create a Spikes window")
            else:
                score -= 70
                reasons.append("double-switch loses value when the opponent can stay and claim hazards")
        if {"spinblock", "damage_context"} <= tags:
            if opponent_attack_ko == "guaranteed":
                score += 65
                reasons.append("switch preserves material when public damage says the spinblocker is KOed")
            elif opponent_attack_ko == "never":
                score -= 35
                reasons.append("switch gives up a live spinblock attack when the active survives")
        if move_id == primary_hidden_coverage_pivot:
            if hidden_coverage_punish_plausible:
                score += 100
                reasons.append("primary pivot preserves the active from plausible severe hidden coverage")
            else:
                score -= 45
                reasons.append("primary hidden-coverage pivot loses value once the punish is absent")
        if move_id == fallback_hidden_coverage_pivot:
            if hidden_coverage_punish_plausible:
                score += 55
                reasons.append("fallback pivot is acceptable hidden-coverage preservation")
            else:
                score -= 50
                reasons.append("fallback hidden-coverage pivot is too passive once the punish is absent")
        if {"defensive_answer", "preservation"} <= tags:
            score += 85
            reasons.append("resistant pivot preserves the exposed active piece")
            if {"fast_public_punish", "preservation"} <= tags:
                if active_faints_before_progress:
                    score += 50
                    reasons.append("public speed and damage say the active faints before making progress")
                elif active_survives_public_punish:
                    score -= 75
                    reasons.append("switching loses priority once the active survives and can convert directly")
        elif player_layers == 2:
            score -= 45
            reasons.append("switching gives up the live third-layer turn")
        elif {"explosion", "route_trade"} <= tags:
            score += 30
            reasons.append("switching preserves material but may miss the trade window")
        if fallback_status_pivot and move_id == fallback_status_pivot:
            if status_clock_survives_punish:
                score += 35
                reasons.append("pivot is a real anti-route but loses priority while the status clock can be started safely")
            else:
                score += 90
                reasons.append("pivot becomes the route once the status user cannot survive the immediate punish")
        if fallback_ko_pivot and move_id == fallback_ko_pivot:
            if direct_ko_available:
                score += 25
                reasons.append("pivot preserves material but loses priority while direct KO is available")
            else:
                score += 90
                reasons.append("pivot becomes the route once direct KO damage is unavailable")
        if fallback_perish_pivot and move_id == fallback_perish_pivot:
            if perish_route_survives_punish:
                score += 30
                reasons.append("pivot preserves material but loses priority while Perish Song can start the clock")
            else:
                score += 90
                reasons.append("pivot becomes the route once Perish Song cannot survive the immediate punish")

    if cls == "recovery":
        hp = parse_percent(boss_active.get("hp"))
        if recovery_move and move_id == recovery_move:
            if recovery_window_live:
                score += 90
                reasons.append("recovery has a real public window and preserves the route")
            else:
                score -= 85
                reasons.append("recovery is a tempo trap without a real public window")
        if (
            move_id == "move_rest"
            and hp == 100
        ):
            score -= 100
            reasons.append("Rest fails at full HP in the local state model")
        elif (
            move_id == "move_rest"
            and hp is not None
            and hp <= 40
            and ("rest_cycle" in tags or "pp_endgame" in tags)
        ):
            score += 70
            reasons.append("Rest is forced by low HP role survival")
        if "pp_endgame" in tags and immediate_setup_route:
            score -= 65
            reasons.append("recovery gives the active setup route an unchecked turn")
        if text_contains_any(immediate_punish, ("pressure", "initiative", "attack", "surf")):
            score -= 55
            reasons.append("recovery gives initiative under active pressure")

    if cls == "sleep_only":
        if boss_active.get("status") in {"slp", "sleep", "asleep"}:
            score += 20
            reasons.append("Sleep Talk is live only because the user is asleep")
        else:
            score -= 100
            reasons.append("Sleep Talk is state-gated and fails while awake")

    if cls == "phazing":
        phaze_pp = move_pp(position, move_id)
        if {"phazing", "timing"} <= tags:
            phaze_order = str(mechanics.get("boss_phaze_order", "unknown"))
            if phaze_order == "before_opponent_phaze":
                score -= 100
                reasons.append("Gen 2 phazing fails if Roar or Whirlwind acts before the opposing phaze move")
            elif phaze_order == "after_opponent_phaze":
                score += 90
                reasons.append("Gen 2 phazing works because this phaze action goes last")
            else:
                score -= 35
                reasons.append("phazing order is not proven by the public state")
        else:
            score += 20
            reasons.append("phazing can deny setup when timing is valid")
        if phazing_required_for_boost:
            score += 95
            reasons.append("phazing is required because the public setup route is immediately dangerous")
        elif weak_setup_signal:
            score -= 35
            reasons.append("phazing is lower priority because the public setup signal is not yet a dangerous stat route")
        if "opening_info_resource_bid" in tags:
            if opening_reveal_value:
                score += 40
                reasons.append("opening phazing can reveal structure but may miss the Spikes-window bid")
            else:
                score -= 10
                reasons.append("opening phazing is lower value when direct pressure is required")
        if "pp_endgame" in tags and phaze_pp is not None and phaze_pp <= 1:
            if immediate_setup_route:
                score += 95
                reasons.append("final phazing PP is justified by an immediate setup route")
            else:
                score -= 85
                reasons.append("final phazing PP should be saved when it does not deny an immediate route")

    if cls == "status":
        target_unstatused = opponent_active.get("status") in {None, "none"}
        if status_clock_move and move_id == status_clock_move:
            if status_clock_live and target_unstatused and status_clock_survives_punish:
                score += 90
                reasons.append("status clock is live because the target is unstatused and the user survives the immediate punish")
            elif not target_unstatused:
                score -= 70
                reasons.append("status clock is blocked because the visible target already has status")
            else:
                score -= 70
                reasons.append("status clock is unsafe because the immediate punish breaks the route")
        elif status_clock_move:
            score -= 20
            reasons.append("secondary status is less deterministic than the named status-clock route")
        if direct_ko_available and "immediate_ko" in tags:
            score -= 80
            reasons.append("slow status loses to an immediate KO route")
        if weak_setup_signal and status_clock_move and move_id == status_clock_move:
            score += 45
            reasons.append("status clock is preferred while the visible setup signal is low urgency")
        if phazing_required_for_boost:
            score -= 65
            reasons.append("status is too slow when a real boost route must be phazed now")
        if {"defensive_answer", "preservation"} <= tags:
            score += 25
            reasons.append("status helps but does not preserve the answer as cleanly")
        else:
            score += 15
            reasons.append("status can create future turns")

    if cls == "scout":
        if public_probe_needed and single_probe_then_progress:
            score += 80
            reasons.append("one scout probe reduces a live public punish before committing")
        elif public_probe_needed:
            score += 35
            reasons.append("scout probe has value but lacks a clear conversion plan")
        else:
            score -= 60
            reasons.append("scout probe is low value without a live public punish branch")

    if cls == "protect":
        if active_faints_before_progress:
            score += 25
            reasons.append("Protect can avoid one public punish but does not improve the route like a pivot")
        elif active_survives_public_punish:
            score -= 25
            reasons.append("Protect is lower value once direct progress is safe")
        else:
            score += 5
            reasons.append("Protect is a narrow scout, not default progress")

    if cls == "encore":
        if encore_trap_live and encore_user_faster and encore_locks_low_value_move:
            score += 100
            reasons.append("Encore traps a visible low-value last move before the opponent can act")
        elif not encore_trap_live:
            score -= 75
            reasons.append("Encore lacks a visible last-move trap target")
        elif not encore_user_faster:
            score -= 70
            reasons.append("Encore loses value because the user is not proven faster")
        else:
            score -= 35
            reasons.append("Encore needs a low-value move to trap")

    if cls == "lock":
        if lock_move_safe and lock_after_status_or_safe_state:
            score += 90
            reasons.append("lock move is now safe because status or board state changed the route")
        elif hidden_coverage_punish_plausible:
            score -= 90
            reasons.append("lock move is unsafe while severe hidden coverage is plausible")
        else:
            score -= 80
            reasons.append("lock move is premature before status or a safe board changes the route")

    if cls == "perish":
        if perish_route_live and perish_route_survives_punish:
            score += 95
            reasons.append("Perish Song is live because it starts a forced clock and survives the public punish")
        elif perish_route_live:
            score -= 90
            reasons.append("Perish Song cannot start the route because the public punish removes the user first")
        else:
            score -= 35
            reasons.append("Perish Song needs a named forced-clock route")

    if cls == "sacrifice":
        if sacrifice_trade_move and move_id != sacrifice_trade_move:
            score -= 20
            reasons.append("this is not the named sacrifice-trade move")
        elif direct_ko_available:
            score -= 85
            reasons.append("sacrifice trade is wasteful while direct removal is available")
        elif sacrifice_trade_live and sacrifice_trade_forced:
            score += 100
            reasons.append("sacrifice trade is forced because direct removal no longer converts")
        elif sacrifice_trade_live:
            score += 45
            reasons.append("sacrifice trade is live but needs stronger route proof")
        else:
            score -= 65
            reasons.append("sacrifice trade lacks a named route in the public state")

    if cls == "attack":
        if tempo_attack_move:
            if move_id == tempo_attack_move and tempo_attack_changes_route:
                score += 90
                reasons.append("tempo attack changes the future cleanup route")
            elif move_id == tempo_attack_move:
                score -= 35
                reasons.append("tempo attack loses priority once it no longer changes the route")
            else:
                score -= 20
                reasons.append("non-tempo attack misses the named progress route")
        if fallback_hidden_coverage_attack and move_id == fallback_hidden_coverage_attack:
            if hidden_coverage_punish_plausible:
                score -= 70
                reasons.append("direct attack exposes the active to plausible severe hidden coverage")
            else:
                score += 85
                reasons.append("direct attack becomes best once the severe hidden-coverage branch is absent")
        if direct_ko_move:
            if move_id == direct_ko_move and direct_ko_available:
                score += 105
                reasons.append("direct attack removes the threat before slow status or preservation is needed")
            elif move_id == direct_ko_move:
                score -= 40
                reasons.append("direct attack loses priority once it no longer reaches the KO threshold")
            elif direct_ko_available:
                score -= 55
                reasons.append("non-KO action loses to the available direct KO")
        if direct_attack_low_impact and "status_clock" in tags:
            score -= 45
            reasons.append("direct attack is low-impact and does not improve the status-clock route")
        if perish_route_live and "perish_route" in tags:
            score -= 40
            reasons.append("direct or swing damage is lower value than starting the forced Perish clock")
        if status_pressure_move and move_id == status_pressure_move:
            if lock_move_safe:
                score += 10
                reasons.append("status pressure is still useful but the lock conversion is now live")
            else:
                score += 70
                reasons.append("status pressure is the opener before committing to the lock move")
        if fallback_attack and move_id == fallback_attack:
            score += 35
            reasons.append("this is the best fallback attack if the preservation pivot is unavailable")
        if fallback_setup_attack and move_id == fallback_setup_attack:
            if setup_survives_worst_plausible_branch:
                score += 15
                reasons.append("this is the primary direct attack if setup is not chosen")
            else:
                score += 55
                reasons.append("this is the best fallback attack once setup no longer survives the public punish")
        if (
            fallback_probe_attack
            and move_id == fallback_probe_attack
            and not public_probe_needed
        ):
            score += 55
            reasons.append("direct progress is preferred once the scout probe has no live punish to reduce")
        if active_faints_before_progress:
            score -= 80
            reasons.append("public speed and damage say the active can faint before direct attack converts")
        if fallback_survival_attack and move_id == fallback_survival_attack:
            if active_survives_public_punish:
                score += 80
                reasons.append("direct attack is preferred once survival evidence makes the route immediate")
            else:
                score -= 25
                reasons.append("fallback attack still needs survival evidence before it can convert")
        if "scout_probe" in tags and public_probe_needed:
            score -= 20
            reasons.append("direct damage is low value while a scout probe can reduce the public punish")
        if "opening_info_resource_bid" in tags and move_id == "move_thunder":
            if opening_direct_pressure_needed:
                score += 80
                reasons.append("direct Thunder pressure stops the Spiker from claiming the opening")
            else:
                score += 25
                reasons.append("Thunder is live pressure but may miss the expected pivot")
        if {"sleep_window", "endgame"} <= tags:
            if sleep_window_available and setup_changes_ko_math:
                score -= 20
                reasons.append("immediate attack fails to use the sleep window's setup conversion")
            else:
                score += 45
                reasons.append("immediate attack is preferred once the sleep setup window is gone")
            if active_target_grounded and move_id == "move_earthquake":
                score += 25
                reasons.append("Earthquake is the grounded active-target attack")
            elif active_target_grounded and move_id == "move_rock_slide":
                score -= 15
                reasons.append("Rock Slide mainly covers a switch read rather than the grounded active target")
        if "pp_endgame" in tags and not immediate_setup_route:
            score += 10
            reasons.append("direct progress is acceptable while preserving final phazing PP")
        if "hazard_control" in tags and not own_hazards_present:
            score += 55
            reasons.append("direct pressure dominates once there are no own-side hazards to remove")
        elif "hazard_control" in tags and own_hazards_present:
            score -= 15
            reasons.append("direct pressure is lower priority while hazards still tax future pivots")
        if {"phazing", "timing"} <= tags:
            phaze_order = str(mechanics.get("boss_phaze_order", "unknown"))
            if phaze_order == "before_opponent_phaze":
                score += 55
                reasons.append("attack is preferred when public Gen 2 phazing order would fail")
            elif phaze_order == "after_opponent_phaze":
                score -= 15
                reasons.append("attack is lower value when phazing can legally reset the setup route")
        if {"spinblock", "damage_context"} <= tags:
            if opponent_attack_ko == "guaranteed":
                score -= 95
                reasons.append("public damage band says the faster punish KOs before the attack")
            elif opponent_attack_ko == "possible":
                score -= 35
                reasons.append("public damage band says the attack can lose to the punish roll")
            elif opponent_attack_ko == "never":
                score += 70
                reasons.append("public damage band says the active survives the faster punish")
            if move_id == "move_thunderbolt" and boss_attack_ko == "guaranteed":
                score += 35
                reasons.append("public damage band says the attack removes the spinner")
            elif move_id == "move_destiny_bond":
                score -= 45
                reasons.append("Destiny Bond does not remove the spinner or block Rapid Spin here")
        if move_id == "move_focus_punch" and text_contains_any(
            f"{summary} {immediate_punish}",
            ("breaks focus punch", "faster attacking", "public fast damage"),
        ):
            score -= 60
            reasons.append("Focus Punch is exposed to public attacking pressure")
        if player_layers == 3:
            score += 55
            reasons.append("live attack converts a complete hazard state")
        elif {"sleep", "setup", "disruption"} <= tags:
            score += 20
            reasons.append("chip is live but does not recreate the setup window")
        else:
            score += 10
            reasons.append("direct damage is a live fallback")

    if not reasons:
        reasons.append("no state-transition trigger matched")
    return {
        "move_id": move_id,
        "class": cls,
        "score": score,
        "reasons": reasons,
    }


def choose_benchmark_policy_move(benchmark: dict[str, Any]) -> dict[str, Any]:
    scored = [
        score_benchmark_candidate(benchmark, str(move["id"]))
        for move in benchmark["candidate_moves_public"]
    ]
    scored.sort(key=lambda row: (-int(row["score"]), str(row["move_id"])))
    ranking = [
        {
            "action": row["move_id"],
            "rank": index,
            "move_class": row["class"],
            "score": row["score"],
            "reason": "; ".join(row["reasons"]),
        }
        for index, row in enumerate(scored, start=1)
    ]
    top_score = int(scored[0]["score"])
    second_score = int(scored[1]["score"]) if len(scored) > 1 else top_score
    return {
        "benchmark_id": benchmark["id"],
        "policy_version": "state_transition_baseline_v1",
        "mechanics_profile_seen": benchmark["mechanics_profile"],
        "state_hash": public_state_hash(benchmark),
        "decision_status": "action",
        "chosen_move_id": scored[0]["move_id"],
        "chosen_score": scored[0]["score"],
        "confidence": confidence_from_scores(top_score, second_score),
        "policy_name": "state_transition_baseline_v1",
        "candidate_ranking": ranking,
        "current_win_conditions": inferred_current_win_conditions(
            benchmark,
            scored[0]["move_id"],
        ),
        "irreplaceable_pieces": inferred_irreplaceable_pieces(benchmark),
        "catastrophe_branches": inferred_catastrophe_branches(scored),
        "answer_changing_information": inferred_answer_changing_information(benchmark),
        "rules_fired": sorted({reason for row in scored for reason in row["reasons"]}),
        "candidate_scores": scored,
    }


def public_state_hash(benchmark: dict[str, Any]) -> str:
    public_payload = {
        key: benchmark.get(key)
        for key in (
            "id",
            "version",
            "split",
            "mechanics_profile",
            "tags",
            "position_snapshot",
            "candidate_moves_public",
            "hidden_info_visible_to_policy",
            "public_opponent_model",
        )
    }
    raw = json.dumps(public_payload, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def confidence_from_scores(top_score: int, second_score: int) -> float:
    margin = max(0, top_score - second_score)
    return round(min(0.95, 0.50 + margin / 100), 2)


def inferred_catastrophe_branches(scored: list[dict[str, Any]]) -> list[dict[str, Any]]:
    branches: list[dict[str, Any]] = []
    for row in scored:
        if int(row["score"]) <= -50:
            branches.append(
                {
                    "action": row["move_id"],
                    "branch": "; ".join(row["reasons"]),
                    "avoidability": "avoidable",
                }
            )
    if not branches and scored:
        worst = scored[-1]
        branches.append(
            {
                "action": worst["move_id"],
                "branch": "lowest-ranked visible branch: " + "; ".join(worst["reasons"]),
                "avoidability": "review",
            }
        )
    return branches


def inferred_current_win_conditions(
    benchmark: dict[str, Any],
    chosen_move_id: str,
) -> list[dict[str, Any]]:
    tags = set(benchmark.get("tags", []))
    position = benchmark.get("position_snapshot") or {}
    boss_active = active_species(position, "boss_active")
    opponent_active = active_species(position, "opponent_active")
    opponent_model = benchmark.get("public_opponent_model", {})
    immediate_punish = str(opponent_model.get("immediate_punish", ""))
    route_type = "state_transition"
    if "sleep" in tags:
        route_type = "sleep_control"
    elif "spikes" in tags or "hazards" in tags:
        route_type = "hazard_conversion"
    elif "explosion" in tags or "route_trade" in tags:
        route_type = "route_trade"
    elif "defensive_answer" in tags or "preservation" in tags:
        route_type = "preservation"
    elif "mechanics" in tags:
        route_type = "mechanics_legality"

    return [
        {
            "route_id": f"{route_type}_{benchmark['id']}",
            "owner": "boss",
            "next_step": chosen_move_id,
            "primary_piece": boss_active,
            "blockers": [opponent_active],
            "source": "public_state_inference",
        },
        {
            "route_id": f"deny_opponent_{route_type}_{benchmark['id']}",
            "owner": "opponent",
            "next_step": immediate_punish or "public opponent response",
            "primary_piece": opponent_active,
            "blockers": [boss_active],
            "source": "public_opponent_model",
        },
    ]


def inferred_irreplaceable_pieces(benchmark: dict[str, Any]) -> list[dict[str, Any]]:
    tags = set(benchmark.get("tags", []))
    position = benchmark.get("position_snapshot") or {}
    boss_active = active_species(position, "boss_active")
    opponent_active = active_species(position, "opponent_active")
    pieces: list[dict[str, Any]] = [
        {
            "piece": opponent_active,
            "owner": "opponent",
            "role": "active route pressure or blocker",
            "preserve": True,
            "source": "public_active_state",
        }
    ]
    if "defensive_answer" in tags or "preservation" in tags:
        pieces.append(
            {
                "piece": boss_active,
                "owner": "boss",
                "role": "piece being preserved from the public punish branch",
                "preserve": True,
                "source": "public_preservation_tag",
            }
        )
    elif "explosion" in tags or "route_trade" in tags:
        pieces.append(
            {
                "piece": boss_active,
                "owner": "boss",
                "role": "one-time route conversion resource",
                "preserve": False,
                "source": "public_route_trade_tag",
            }
        )
    else:
        pieces.append(
            {
                "piece": boss_active,
                "owner": "boss",
                "role": "current action executor",
                "preserve": True,
                "source": "public_active_state",
            }
        )
    return pieces


def active_species(position: dict[str, Any], key: str) -> str:
    active = position.get(key, {})
    if isinstance(active, dict) and active.get("species"):
        return str(active["species"])
    return key


def inferred_answer_changing_information(
    benchmark: dict[str, Any],
) -> list[dict[str, Any]]:
    position = benchmark.get("position_snapshot") or {}
    field = position.get("field", {}) if isinstance(position.get("field"), dict) else {}
    rows: list[dict[str, Any]] = []
    if "sleep" in set(benchmark.get("tags", [])):
        rows.append(
            {
                "field": "sleep_clause_or_target_status",
                "if_true": "sleep move may become blocked or lower value",
                "needed": False,
            }
        )
    if "sleep_window" in set(benchmark.get("tags", [])):
        rows.append(
            {
                "field": "target sleep state and wake branch",
                "if_true": "setup loses priority if the target is awake or can punish before conversion",
                "needed": False,
            }
        )
    if field.get("player_side_spikes_layers") is not None:
        rows.append(
            {
                "field": "player_side_spikes_layers",
                "if_true": "different layer count can flip hazard, attack, or Explosion value",
                "needed": False,
            }
        )
    if "pp_endgame" in set(benchmark.get("tags", [])):
        rows.append(
            {
                "field": "critical phazing PP and immediate setup route",
                "if_true": "final phazing PP should be spent only when it denies an immediate route",
                "needed": False,
            }
        )
    tags = set(benchmark.get("tags", []))
    if "explosion" in tags or "sacrifice" in tags or "route_trade" in tags:
        rows.append(
            {
                "field": "public block branch or direct-removal damage threshold",
                "if_true": "sacrifice trade can become risky, unnecessary, or forced",
                "needed": False,
            }
        )
    if not rows:
        rows.append(
            {
                "field": "unrevealed move, speed, damage, or role information",
                "if_true": "candidate ordering may change if a public uncertainty becomes confirmed",
                "needed": False,
            }
        )
    return rows


def build_benchmark_policy_answers(
    benchmarks: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = [choose_benchmark_policy_move(benchmark) for benchmark in benchmarks]
    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "policy_name": "state_transition_baseline_v1",
        "answers": rows,
    }


def write_benchmark_policy_answers(
    benchmarks_path: Path = DEFAULT_BENCHMARKS_PATH,
    out_path: Path = DEFAULT_BENCHMARK_POLICY_ANSWERS_PATH,
) -> dict[str, Any]:
    report = build_benchmark_policy_answers(load_benchmarks(benchmarks_path))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def set_nested_value(data: dict[str, Any], dotted_path: str, value: Any) -> None:
    target = data
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        child = target.get(part)
        if not isinstance(child, dict):
            child = {}
            target[part] = child
        target = child
    target[parts[-1]] = value


def apply_benchmark_mutation(
    benchmark: dict[str, Any],
    spec: dict[str, Any],
) -> dict[str, Any]:
    mutated = deepcopy(benchmark)
    mutated["id"] = spec["mutation_id"]
    mutated["version"] = int(mutated.get("version", 1)) + 1
    mutated["split"] = "holdout"
    mutated["source_refs"] = [
        *list(mutated.get("source_refs", [])),
        f"mutation_of:{benchmark['id']}",
    ]
    mutated["tags"] = list(
        dict.fromkeys(
            [
                *list(mutated.get("tags", [])),
                "mutation",
                str(spec["family"]),
            ]
        )
    )
    for change in spec["changes"]:
        set_nested_value(mutated, str(change["path"]), change["value"])
    return mutated


def build_benchmark_mutation_report(
    benchmarks: list[dict[str, Any]],
    mutation_specs: list[dict[str, Any]] = BENCHMARK_MUTATION_SPECS,
) -> dict[str, Any]:
    by_id = {benchmark["id"]: benchmark for benchmark in benchmarks}
    rows: list[dict[str, Any]] = []
    for spec in mutation_specs:
        base = by_id.get(str(spec["base_id"]))
        if base is None:
            rows.append(
                {
                    "mutation_id": spec["mutation_id"],
                    "base_benchmark_id": spec["base_id"],
                    "family": spec["family"],
                    "minimal_delta": spec["minimal_delta"],
                    "principle": spec["principle"],
                    "missing_base": True,
                    "mutation_passes": False,
                    "policy_flipped": False,
                    "validation_errors": ["base benchmark not found"],
                }
            )
            continue

        mutated = apply_benchmark_mutation(base, spec)
        validation_errors = validate_public_card_data(
            {"schema_version": 1, "cards": [mutated]}
        )
        base_answer = choose_benchmark_policy_move(base)
        mutated_answer = choose_benchmark_policy_move(mutated)
        base_move = str(base_answer["chosen_move_id"])
        mutated_move = str(mutated_answer["chosen_move_id"])
        expected_base = str(spec["expected_base_move_id"])
        expected_mutated = str(spec["expected_mutated_move_id"])
        policy_flipped = base_move != mutated_move
        base_matches = base_move == expected_base
        mutated_matches = mutated_move == expected_mutated

        rows.append(
            {
                "mutation_id": spec["mutation_id"],
                "base_benchmark_id": spec["base_id"],
                "family": spec["family"],
                "minimal_delta": spec["minimal_delta"],
                "principle": spec["principle"],
                "expected_base_move_id": expected_base,
                "base_chosen_move_id": base_move,
                "base_state_hash": base_answer["state_hash"],
                "expected_mutated_move_id": expected_mutated,
                "mutated_chosen_move_id": mutated_move,
                "mutated_state_hash": public_state_hash(mutated),
                "policy_flipped": policy_flipped,
                "base_matches_expected": base_matches,
                "mutated_matches_expected": mutated_matches,
                "mutation_passes": (
                    not validation_errors
                    and policy_flipped
                    and base_matches
                    and mutated_matches
                ),
                "validation_errors": validation_errors,
                "top_mutated_candidates": mutated_answer["candidate_ranking"][:3],
            }
        )

    pass_count = sum(1 for row in rows if row["mutation_passes"])
    flip_count = sum(1 for row in rows if row["policy_flipped"])
    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "mutation_count": len(rows),
        "pass_count": pass_count,
        "policy_flip_count": flip_count,
        "all_mutations_pass": pass_count == len(rows),
        "all_mutations_flip": flip_count == len(rows),
        "families": sorted({str(row["family"]) for row in rows}),
        "mutations": rows,
    }


def render_benchmark_mutation_report(report: dict[str, Any]) -> str:
    lines = [
        "# State-Transition Mutation Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Mutations: {report['mutation_count']}",
        f"- Passed mutations: {report['pass_count']}",
        f"- Policy flips: {report['policy_flip_count']}",
        f"- All mutations pass: `{report['all_mutations_pass']}`",
        f"- All mutations flip: `{report['all_mutations_flip']}`",
        f"- Families: `{report['families']}`",
        "",
        "## Boundary Mutations",
        "",
        "| Mutation | Base | Delta | Expected Flip | Actual Flip | Pass |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["mutations"]:
        lines.append(
            "| "
            f"`{row['mutation_id']}` | "
            f"`{row['base_benchmark_id']}` | "
            f"{row['minimal_delta']} | "
            f"`{row.get('expected_base_move_id')}` -> "
            f"`{row.get('expected_mutated_move_id')}` | "
            f"`{row.get('base_chosen_move_id')}` -> "
            f"`{row.get('mutated_chosen_move_id')}` | "
            f"`{row['mutation_passes']}` |"
        )

    lines.extend(["", "## Principles", ""])
    for row in report["mutations"]:
        lines.extend(
            [
                f"### `{row['mutation_id']}`",
                "",
                f"- Family: `{row['family']}`",
                f"- Principle: {row['principle']}",
                f"- Mutated state hash: `{row.get('mutated_state_hash', '-')}`",
                "- Top mutated candidates:",
                *[
                    f"  - rank {candidate['rank']}: `{candidate['action']}` "
                    f"score `{candidate['score']}` ({candidate['reason']})"
                    for candidate in row.get("top_mutated_candidates", [])
                ],
                "",
            ]
        )
    return "\n".join(lines)


def write_benchmark_mutation_report(
    benchmarks_path: Path = DEFAULT_BENCHMARKS_PATH,
    out_path: Path = DEFAULT_BENCHMARK_MUTATION_REPORT_PATH,
    json_out_path: Path | None = DEFAULT_BENCHMARK_MUTATION_JSON_PATH,
) -> dict[str, Any]:
    report = build_benchmark_mutation_report(load_benchmarks(benchmarks_path))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_benchmark_mutation_report(report),
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


def evaluate_choice(
    benchmark: dict[str, Any],
    oracle: dict[str, Any],
    chosen_move_id: str | None,
) -> dict[str, Any]:
    labels = move_label_by_id(oracle)
    expected = move_ids_by_label(oracle)
    if chosen_move_id is None:
        outcome = "unanswered"
        chosen_label = None
    else:
        chosen_label = labels.get(chosen_move_id)
        outcome = chosen_label if chosen_label in REQUIRED_OUTCOME_LABELS else "unknown_move"

    return {
        "benchmark_id": benchmark["id"],
        "split": benchmark["split"],
        "mechanics_profile": benchmark["mechanics_profile"],
        "tags": list(benchmark["tags"]),
        "best_move_ids": expected["best"],
        "acceptable_move_ids": expected["acceptable"],
        "catastrophic_move_ids": expected["catastrophic"],
        "chosen_move_id": chosen_move_id,
        "chosen_label": chosen_label,
        "outcome": outcome,
        "dominant_policy": oracle["heuristic_arbitration"]["dominant_policy"],
        "catastrophe_trigger": oracle["catastrophe_branches"][0]["trigger"],
        "information_that_changes_answer": list(
            oracle["answer_changing_information"]
        ),
    }


def build_benchmark_report(
    benchmarks: list[dict[str, Any]],
    oracles: list[dict[str, Any]] | None = None,
    answers: dict[str, str] | None = None,
) -> dict[str, Any]:
    answers = answers or {}
    oracle_by_id = oracle_map(oracles or load_benchmark_oracles())
    rows = [
        evaluate_choice(benchmark, oracle_by_id[benchmark["id"]], answers.get(benchmark["id"]))
        for benchmark in benchmarks
    ]
    benchmark_ids = {benchmark["id"] for benchmark in benchmarks}
    unknown_answer_ids = sorted(set(answers) - benchmark_ids)
    missing_initial = sorted(INITIAL_REQUIRED_BENCHMARK_IDS - benchmark_ids)
    outcome_counts = Counter(row["outcome"] for row in rows)
    profile_counts = Counter(row["mechanics_profile"] for row in rows)
    split_counts = Counter(row["split"] for row in rows)
    outcomes_by_split: dict[str, dict[str, int]] = {}
    for split in sorted(split_counts):
        outcomes_by_split[split] = dict(
            sorted(
                Counter(row["outcome"] for row in rows if row["split"] == split).items()
            )
        )
    split_passes = {
        split: bool(answers)
        and not any(
            row["outcome"] in {"catastrophic", "unanswered", "unknown_move"}
            for row in rows
            if row["split"] == split
        )
        for split in sorted(split_counts)
    }

    return {
        "generated_at": now_iso(),
        "benchmark_count": len(benchmarks),
        "mechanics_profile_counts": dict(sorted(profile_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "required_initial_benchmark_count": len(INITIAL_REQUIRED_BENCHMARK_IDS),
        "missing_initial_benchmarks": missing_initial,
        "benchmark_contract_ready": not missing_initial,
        "answer_count": len(answers),
        "unknown_answer_ids": unknown_answer_ids,
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "outcomes_by_split": outcomes_by_split,
        "split_passes": split_passes,
        "policy_evaluated": bool(answers),
        "policy_passes": bool(answers)
        and not unknown_answer_ids
        and not outcome_counts.get("unanswered")
        and not outcome_counts.get("unknown_move")
        and not outcome_counts.get("catastrophic"),
        "benchmarks": rows,
    }


def format_list(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "-"


def render_benchmark_report(report: dict[str, Any]) -> str:
    lines = [
        "# State-Transition Benchmark Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Benchmarks: {report['benchmark_count']}",
        f"- Required initial benchmarks present: `{report['benchmark_contract_ready']}`",
        f"- Policy evaluated: `{report['policy_evaluated']}`",
        f"- Policy passes evaluated benchmarks: `{report['policy_passes']}`",
        f"- Mechanics profiles: `{report['mechanics_profile_counts']}`",
        f"- Splits: `{report['split_counts']}`",
        f"- Outcomes: `{report['outcome_counts']}`",
        f"- Outcomes by split: `{report['outcomes_by_split']}`",
        f"- Split passes: `{report['split_passes']}`",
        "",
    ]
    if report["missing_initial_benchmarks"]:
        lines.extend(
            [
                "## Missing Initial Benchmarks",
                "",
                *[f"- `{benchmark_id}`" for benchmark_id in report["missing_initial_benchmarks"]],
                "",
            ]
        )
    if report["unknown_answer_ids"]:
        lines.extend(
            [
                "## Unknown Answer IDs",
                "",
                *[f"- `{benchmark_id}`" for benchmark_id in report["unknown_answer_ids"]],
                "",
            ]
        )

    lines.extend(
        [
            "## Move Targets",
            "",
            "| Benchmark | Split | Profile | Best | Acceptable | Catastrophic | Chosen | Outcome |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report["benchmarks"]:
        lines.append(
            "| "
            f"`{row['benchmark_id']}` | "
            f"`{row['split']}` | "
            f"`{row['mechanics_profile']}` | "
            f"{format_list(row['best_move_ids'])} | "
            f"{format_list(row['acceptable_move_ids'])} | "
            f"{format_list(row['catastrophic_move_ids'])} | "
            f"{f'`{row['chosen_move_id']}`' if row['chosen_move_id'] else '-'} | "
            f"`{row['outcome']}` |"
        )

    lines.extend(["", "## Arbitration Targets", ""])
    for row in report["benchmarks"]:
        lines.extend(
            [
                f"### `{row['benchmark_id']}`",
                "",
                f"- Dominant policy: {row['dominant_policy']}",
                f"- Catastrophe trigger: {row['catastrophe_trigger']}",
                "- Answer-changing information:",
                *[
                    f"  - {item}"
                    for item in row["information_that_changes_answer"]
                ],
                "",
            ]
        )
    return "\n".join(lines)


def write_benchmark_report(
    benchmarks_path: Path = DEFAULT_BENCHMARKS_PATH,
    oracles_path: Path = DEFAULT_BENCHMARK_ORACLES_PATH,
    answers_path: Path | None = None,
    out_path: Path = DEFAULT_BENCHMARK_REPORT_PATH,
    json_out_path: Path | None = DEFAULT_BENCHMARK_JSON_PATH,
) -> dict[str, Any]:
    answers = load_benchmark_answers(answers_path) if answers_path else None
    report = build_benchmark_report(
        load_benchmarks(benchmarks_path),
        oracles=load_benchmark_oracles(oracles_path),
        answers=answers,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_benchmark_report(report), encoding="utf-8", newline="\n")
    if json_out_path is not None:
        json_out_path.parent.mkdir(parents=True, exist_ok=True)
        json_out_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return report
