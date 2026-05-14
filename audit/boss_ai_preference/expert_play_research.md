# Expert Play Research

Generated: 2026-05-13T11:25:10+00:00

Purpose: source-backed play principles that feed benchmark design. This is an artifact index, not a strategy essay.

- Principles: 19
- Source scopes: cross_generation_play_patterns, cross_generation_strategy, vanilla_gsc_mechanics, vanilla_gsc_mechanics_and_strategy, vanilla_gsc_play_patterns, vanilla_gsc_strategy

## Principles

### `gsc_foresight_over_one_turn_prediction`

- Source: https://www.smogon.com/gs/articles/gsc_guide_part1
- Scope: `vanilla_gsc_strategy`
- Claim: Borat's guide emphasizes improving position over many turns, not choosing the highest-power attack or only predicting the next click.
- Policy implication: Every nontrivial answer should name the route improved by the move and the next-turn plan, not just immediate damage.
- Benchmark hooks: long_battle_rest_tempo_unforced_001, romhack_spinblock_damage_context_001, fixture_whitney_miltank_vs_geodude_rollout_lock_001, fixture_misty_starmie_vs_meganium_recover_tempo_001

### `gsc_bad_matchup_switching_preserves_future_routes`

- Source: https://www.smogon.com/gs/articles/gsc_guide_part1
- Scope: `vanilla_gsc_play_patterns`
- Claim: Borat's guide frames switching out of mismatches and knowing when to back off as core play, because GSC kills are earned through position rather than immediate revenge kills.
- Policy implication: When public speed and damage say the active faints before progress, a preserving pivot should beat direct damage or sacrifice unless the sacrifice opens a named route.
- Benchmark hooks: fixture_pryce_cloyster_vs_quilava_fire_pivot_001, fixture_koga_ariados_vs_typhlosion_fire_spikes_001, fixture_will_slowbro_vs_houndoom_fast_dark_001

### `gsc_spikes_need_conversion_support`

- Source: https://www.smogon.com/gs/articles/gsc_spikes
- Scope: `vanilla_gsc_strategy`
- Claim: The Spikes guide treats hazards as pressure that must be converted through status, attacks, phazing, spin pressure, or Rest-cycle pressure.
- Policy implication: A hazard move is only a policy move when it changes switch costs, KO bands, removal incentives, or a named route.
- Benchmark hooks: romhack_spikes_third_layer_janine_001, romhack_spikes_fourth_click_janine_001, romhack_spinblock_damage_context_001, external_gsc_golem_late_rapid_spin_001

### `gsc_explosion_is_route_trade`

- Source: https://www.smogon.com/gs/articles/guide_to_explosion
- Scope: `vanilla_gsc_strategy`
- Claim: The Explosion guide presents Explosion as wallbreaking, emergency defense, free-turn creation, bluffing, or simplification depending on context.
- Policy implication: Explosion answers must name both the route opened and the role lost; low HP alone is not evidence.
- Benchmark hooks: romhack_explosion_route_trade_brock_001, fixture_brock_golem_vs_vaporeon_explosion_question_001, external_gsc_forretress_explosion_on_quagsire_001, fixture_morty_gengar_vs_kadabra_destiny_bond_001

### `gsc_sleep_is_temporary_and_resttalk_aware`

- Source: https://www.smogon.com/gs/articles/status
- Scope: `vanilla_gsc_mechanics_and_strategy`
- Claim: The status guide notes sleep lasts 1-6 turns, waking Pokemon can act that turn, and Sleep Talk plus Rest changes sleep value.
- Policy implication: Sleep/setup cards must branch on miss, wake, Sleep Talk, target status, and sleep-clause state instead of continuing scripts.
- Benchmark hooks: vanilla_gsc_sleep_setup_disruption_001, long_battle_sleep_disruption_after_miss_001, external_gsc_sleeping_lax_curse_window_001, external_gsc_vaporeon_vs_restdtalk_snorlax_001, fixture_chuck_poliwrath_vs_alakazam_psychic_pivot_001, fixture_morty_haunter_vs_noctowl_sleep_line_001

### `gsc_toxic_clock_needs_survivable_transition`

- Source: https://www.smogon.com/resources/competitive/gs/status
- Scope: `vanilla_gsc_play_patterns`
- Claim: Smogon's GSC status guide treats Toxic as long-term pressure that matters when it forces recovery, switching, or endgame timing rather than as generic chip.
- Policy implication: A Toxic-clock benchmark should require the target to be unstatused, the status user to survive or justify the trade, and the follow-up pivot or attack route to be named.
- Benchmark hooks: fixture_karen_crobat_vs_dragonite_toxic_clock_001, fixture_koga_ariados_vs_typhlosion_fire_spikes_001, fixture_whitney_miltank_vs_geodude_rollout_lock_001, fixture_bugsy_ariados_vs_pidgey_status_clock_001

### `risk_reward_direct_removal_beats_slow_clock`

- Source: https://www.smogon.com/resources/beginner/bw_risk_reward
- Scope: `cross_generation_play_patterns`
- Claim: Smogon's risk/reward guide frames turn choice around immediate opposing punish branches and the move that best advances the overall route.
- Policy implication: If public damage removes the active threat now, slow status or swingy disruption should lose unless the KO opens a worse forced route.
- Benchmark hooks: fixture_koga_crobat_vs_alakazam_immediate_ko_001, fixture_karen_crobat_vs_dragonite_toxic_clock_001, long_battle_rest_tempo_unforced_001, fixture_misty_starmie_vs_meganium_recover_tempo_001

### `risk_reward_utility_needs_public_branch`

- Source: https://www.smogon.com/resources/beginner/bw_risk_reward
- Scope: `cross_generation_play_patterns`
- Claim: Smogon's risk/reward guide emphasizes choosing moves by the opponent's immediate and worst-case branches rather than generic style preferences.
- Policy implication: Utility moves like Encore should need a visible branch they punish; without that branch, safer setup or direct progress can dominate.
- Benchmark hooks: fixture_whitney_clefairy_vs_bayleef_encore_reflect_001, fixture_falkner_pidgeotto_vs_geodude_scout_probe_001, fixture_jasmine_skarmory_vs_machoke_focus_energy_001

### `prediction_requires_public_information`

- Source: https://www.smogon.com/smog/issue1/introduction_to_prediction
- Scope: `cross_generation_play_patterns`
- Claim: Smogon's prediction guide frames prediction as an information problem: each opponent action should update what future choices are likely and what risks are acceptable.
- Policy implication: Status, pivots, and direct attacks should be chosen from public speed, HP, move, and damage evidence; if a threshold changes, the policy must flip instead of repeating the same slogan.
- Benchmark hooks: fixture_jasmine_magneton_vs_quilava_speed_control_001, fixture_whitney_clefairy_vs_bayleef_encore_reflect_001, vanilla_gsc_opening_electric_double_switch_spikes_001, fixture_clair_dragonair_vs_suicune_hidden_ice_001

### `gsc_phazing_is_timing_sensitive`

- Source: https://www.smogon.com/gs/articles/move_priority
- Scope: `vanilla_gsc_mechanics`
- Claim: The priority guide documents that Roar and Whirlwind must go last to work in GSC.
- Policy implication: Phazing benchmarks need speed relation and move-order evidence before labeling Roar or Whirlwind as setup control.
- Benchmark hooks: vanilla_gsc_phazing_timing_mirror_001, fixture_jasmine_skarmory_vs_machoke_focus_energy_001

### `gsc_phazing_needs_live_setup_route`

- Source: https://www.smogon.com/gs/articles/gsc_spikes
- Scope: `vanilla_gsc_play_patterns`
- Claim: The GSC Spikes guide frames phazing as route pressure that shuts down offense and forces switches, but also says to evaluate the whole position rather than autopilot passive tools.
- Policy implication: Whirlwind or Roar should dominate when a real setup route must be denied now; low-urgency setup signals can lose to status, attack, or preservation.
- Benchmark hooks: fixture_jasmine_skarmory_vs_machoke_focus_energy_001, vanilla_gsc_phazing_timing_mirror_001, vanilla_gsc_pp_phaze_loop_save_final_whirlwind_001

### `gsc_perish_song_is_forced_clock_route`

- Source: https://www.smogon.com/forums/threads/misdreavus-ou-revamp-done.3643258/
- Scope: `vanilla_gsc_play_patterns`
- Claim: The GSC Misdreavus analysis frames Perish Song as a forced-clock tool that can force out setup routes, but warns that Misdreavus must survive the opposing damage long enough to execute it.
- Policy implication: Perish Song should be scored as route control only when the user survives the public punish and the countdown changes the opponent's route.
- Benchmark hooks: fixture_morty_misdreavus_vs_typhlosion_perish_route_001, constructed_gsc_sleep_spikes_route_review_001

### `gsc_damage_thresholds_not_type_slogans`

- Source: https://www.smogon.com/gs/articles/gsc_guide_part1
- Scope: `vanilla_gsc_play_patterns`
- Claim: Borat's GSC guide warns against treating super-effective text or raw power as the decision; strong play asks whether the damage changes the position and future route.
- Policy implication: Type-effectiveness words in benchmark or policy explanations must be backed by mechanics-profile-specific evidence and tied to damage, KO, Rest, preservation, or route thresholds.
- Benchmark hooks: romhack_defensive_answer_preservation_pryce_001, romhack_spinblock_damage_context_001, fixture_brock_golem_vs_vaporeon_explosion_question_001, fixture_will_slowbro_vs_houndoom_fast_dark_001, fixture_chuck_poliwrath_vs_alakazam_psychic_pivot_001

### `long_term_thinking_is_skill_axis`

- Source: https://www.smogon.com/rs/articles/long_term_thinking
- Scope: `cross_generation_strategy`
- Claim: The long-term thinking article frames skill as in-battle planning beyond team matchup and luck, explicitly relevant to RBY/GSC/RSE styles.
- Policy implication: Battle review should grade pre-turn decision quality and earliest route loss separately from the final outcome.
- Benchmark hooks: constructed_gsc_sleep_spikes_route_review_001, vanilla_gsc_pp_phaze_loop_save_final_whirlwind_001, external_gsc_sleeping_lax_curse_window_001

### `gsc_opening_moves_are_information_and_resource_bids`

- Source: https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/
- Scope: `vanilla_gsc_play_patterns`
- Claim: The GSC lead analysis describes strong openings as forcing switches, revealing early team structure, double-switching into Spikes chances, or landing status/Leftovers disruption.
- Policy implication: Opening-turn benchmarks should value the information and resource transition created by a move, not only whether it deals immediate damage.
- Benchmark hooks: romhack_spikes_third_layer_janine_001, vanilla_gsc_phazing_timing_mirror_001, external_gsc_sleeping_lax_curse_window_001

### `gsc_tournament_replays_are_real_state_corpus`

- Source: https://www.smogon.com/forums/threads/gsc-tournament-replays.3689138/
- Scope: `vanilla_gsc_play_patterns`
- Claim: The GSC tournament replay archive collects official tournament games, giving concrete examples of how strong players convert resources across full battles.
- Policy implication: New long-game benchmark cards should be mined from real replay states when possible, with hidden future information sealed from the policy answer.
- Benchmark hooks: external_gsc_sleeping_lax_curse_window_001, external_gsc_forretress_explosion_on_quagsire_001, external_gsc_vaporeon_vs_restdtalk_snorlax_001, external_gsc_golem_late_rapid_spin_001, constructed_gsc_sleep_spikes_route_review_001

### `gsc_spikes_offense_uses_direct_pressure_and_booms`

- Source: https://www.smogon.com/forums/threads/gsc-ou-discussion-thread.3688141/
- Scope: `vanilla_gsc_play_patterns`
- Claim: Current GSC discussion frames robust Spikes play with direct offensive pressure, Thunder users, Nidoking-style progress, and limited Explosion resources rather than passive hazard-only plans.
- Policy implication: Spikes benchmarks need arbitration against direct attack, double-switch, and Explosion conversion lines instead of treating hazards as default progress.
- Benchmark hooks: vanilla_gsc_opening_electric_double_switch_spikes_001, external_gsc_forretress_explosion_on_quagsire_001, romhack_explosion_route_trade_brock_001, romhack_spikes_third_layer_janine_001

### `gsc_spikes_are_not_free_passivity`

- Source: https://www.smogon.com/gs/articles/gsc_spikes
- Scope: `vanilla_gsc_play_patterns`
- Claim: The Spikes guide warns that Spikes alone is not a win condition in most games and that passive Spikes play gives opposing offense time to execute its plan.
- Policy implication: Hazard/status plans must lose to a revealed lethal punish unless the move creates immediate route progress or the active piece is expendable.
- Benchmark hooks: fixture_koga_ariados_vs_typhlosion_fire_spikes_001, romhack_spikes_public_spinner_holdout_001, external_gsc_golem_late_rapid_spin_001

### `gsc_setup_requires_opening_and_route`

- Source: https://www.smogon.com/gs/articles/gsc_guide_part1
- Scope: `vanilla_gsc_play_patterns`
- Claim: Borat's GSC guide frames strong offense as improving position until there is an opening to go for the route, rather than clicking the strongest immediate attack.
- Policy implication: Setup is a policy move only when the public punish is survivable and the boost changes a named route; otherwise direct attack or preservation should dominate.
- Benchmark hooks: fixture_bugsy_scyther_vs_geodude_safe_swords_dance_001, fixture_bugsy_scyther_vs_quilava_fire_setup_001, external_gsc_sleeping_lax_curse_window_001, external_gsc_vaporeon_vs_restdtalk_snorlax_001
