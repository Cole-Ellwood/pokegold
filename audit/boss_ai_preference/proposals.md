# Boss AI Preference Proposal Report

Generated: 2026-05-12T10:57:09+00:00

## Summary

- Proposals: 45
- Reward model holdout accuracy: 50.0%
- Trajectory preferences: 34
- Plan demonstrations: 3
- Blocked by trajectory conflicts: False
- Stale trajectory rows: 0

## Proposal Type Counts

- `hard_rule`: 2
- `needs_more_labels`: 21
- `schema_only`: 1
- `scoring_weight`: 1
- `scout_policy`: 2
- `sequence_policy`: 1
- `switch_policy`: 17

## Candidate: hidden_coverage_probe_before_ace_setup

- Type: `scout_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Hidden coverage suspicion can make scouting or probing better than greedy setup, especially before committing an ace.
- Evidence:
  - `clair_dragonair_vs_suicune_hidden_ice_beam:move_outrage:move_thunder`
  - `lance_dragonite_vs_suicune_champion_ace:move_dragon_dance:move_outrage`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Generate scout/probe counterfactuals and review a narrow information-value scorer change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: immediate_ko_over_slow_plan

- Type: `scoring_weight`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: A guaranteed or near-guaranteed KO should dominate slow chip, status, or recovery when the target can punish passivity.
- Evidence:
  - `brock_golem_vs_vaporeon_explosion_question:move_explosion:move_earthquake`
  - `bugsy_scyther_vs_quilava_fire_pressure:move_swords_dance:move_wing_attack`
  - `chuck_poliwrath_vs_pidgeotto_ice_punch:move_focus_punch:move_ice_punch`
  - `jasmine_steelix_vs_quilava_fire_threat:move_rock_slide:move_earthquake`
  - `koga_crobat_vs_alakazam_toxic_or_attack:move_toxic:move_wing_attack`
  - `lance_dragonite_vs_suicune_champion_ace:move_dragon_dance:move_outrage`
  - `misty_starmie_vs_meganium_recover_or_attack:move_recover:move_psychic`
  - `morty_gengar_vs_kadabra_destiny_bond:move_shadow_ball:move_destiny_bond`
- Improves:
  - `koga_crobat_vs_alakazam_toxic_or_attack:move_toxic:move_wing_attack`
- Risks / worsens:
  - `misty_starmie_vs_meganium_recover_or_attack:move_recover:move_psychic`
- Suggested implementation: Adjust an offline feature weight or produce a small scorer-diff candidate for human review.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: other_better_means_action_pool_gap

- Type: `schema_only`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Several labels say the best answer is outside the displayed pair, so V2 queries must include switch and plan actions.
- Evidence:
  - `chuck_poliwrath_vs_pidgeotto_ice_punch:move_focus_punch:move_ice_punch`
  - `clair_dragonair_vs_suicune_hidden_ice_beam:move_outrage:move_thunder`
  - `pryce_cloyster_vs_quilava_explosion_line:move_surf:move_explosion`
  - `pryce_slowking_vs_ampharos_ground_pivot:move_thunder_wave:move_surf`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Improve the preference UI/query shape; do not change ROM behavior.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: resisted_ramp_lock_opener

- Type: `hard_rule`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Do not start a resisted ramp-lock sequence when it does not KO and the target can punish or switch.
- Evidence:
  - `whitney_miltank_vs_geodude_rollout_temptation:move_rollout:move_body_slam`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Draft a narrow ASM fail/discourage rule only after reviewing the listed examples.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: sacrifice_switch_mixed_strategy

- Type: `needs_more_labels`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Sacrifice, switch, and attack can be near-tie spots where the AI should preserve variety instead of becoming deterministic.
- Evidence:
  - `brock_golem_vs_vaporeon_explosion_question:move_explosion:move_earthquake`
  - `morty_gengar_vs_kadabra_destiny_bond:move_shadow_ball:move_destiny_bond`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: setup_requires_damage_race

- Type: `needs_more_labels`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Setup is good when it keeps or improves the damage race, not merely because setup is boss-flavored.
- Evidence:
  - `bugsy_scyther_vs_quilava_fire_pressure:move_swords_dance:move_wing_attack`
  - `clair_kingdra_vs_lapras_dragon_dance_or_attack:move_dragon_dance:move_surf`
  - `lance_dragonite_vs_suicune_champion_ace:move_dragon_dance:move_outrage`
  - `whitney_clefairy_vs_bayleef_encore_window:move_double_team:move_encore`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: single_debuff_then_attack

- Type: `needs_more_labels`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: One accuracy debuff can be correct when direct chip is worthless, but repeated debuffs lose value because switching clears them.
- Evidence:
  - `falkner_pidgeotto_vs_geodude_rock_risk:move_gust:move_sand_attack`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: sleep_pressure_clause_gated

- Type: `hard_rule`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Sleep is strong legal pressure, but fail states and Sleep Clause must gate it before taste scoring runs.
- Evidence:
  - `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:move_sleep_powder:move_giga_drain`
  - `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:move_sleep_powder:move_quiver_dance`
  - `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:move_sleep_powder:switch_kingdra`
  - `morty_haunter_vs_noctowl_sleep_line:move_hypnosis:move_night_shade`
- Improves:
  - `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:move_sleep_powder:move_quiver_dance`
- Risks / worsens:
  - none in current reports
- Suggested implementation: Draft a narrow ASM fail/discourage rule only after reviewing the listed examples.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory_scout_probe_boundary

- Type: `scout_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Trajectory labels should teach when one scout/probe turn is worth more than immediate ace commitment.
- Evidence:
  - `trajectory:falkner_pidgeotto_vs_geodude_rock_risk:plan_falkner_pidgeotto_vs_geodude_rock_risk_scout_probe_then_commit_move_sand_attack_move_gust:plan_falkner_pidgeotto_vs_geodude_rock_risk_attack_now_move_gust_move_gust`
  - `trajectory:falkner_pidgeotto_vs_geodude_rock_risk:plan_falkner_pidgeotto_vs_geodude_rock_risk_scout_probe_then_commit_move_sand_attack_move_gust:plan_falkner_pidgeotto_vs_geodude_rock_risk_switch_preserve_then_rescore_switch_noctowl_move_gust`
  - `trajectory:whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_attack_now_move_body_slam_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_scout_probe_then_commit_move_milk_drink_move_body_slam`
  - `trajectory:whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_scout_probe_then_commit_move_milk_drink_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_recover_until_safe_move_milk_drink_move_body_slam`
  - `trajectory:whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_scout_probe_then_commit_move_milk_drink_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_switch_preserve_then_rescore_switch_girafarig_move_body_slam`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Generate scout/probe counterfactuals and review a narrow information-value scorer change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory_sequence_policy_boundary

- Type: `sequence_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Multi-turn labels should teach bounded setup/status/lock lines with explicit branch and stop conditions instead of raw move weights.
- Evidence:
  - `trajectory:brock_golem_vs_vaporeon_explosion_question:plan_brock_golem_vs_vaporeon_explosion_question_sacrifice_trade_for_clean_switch_move_explosion_move_explosion:plan_brock_golem_vs_vaporeon_explosion_question_setup_once_then_attack_move_curse_move_explosion`
  - `trajectory:brock_golem_vs_vaporeon_explosion_question:plan_brock_golem_vs_vaporeon_explosion_question_sacrifice_trade_for_clean_switch_move_explosion_move_explosion:plan_brock_golem_vs_vaporeon_explosion_question_switch_preserve_then_rescore_switch_omastar_move_explosion`
  - `trajectory:bugsy_scyther_vs_quilava_fire_pressure:plan_bugsy_scyther_vs_quilava_fire_pressure_setup_once_then_attack_move_swords_dance_move_wing_attack:plan_bugsy_scyther_vs_quilava_fire_pressure_attack_now_move_wing_attack_move_wing_attack`
  - `trajectory:bugsy_scyther_vs_quilava_fire_pressure:plan_bugsy_scyther_vs_quilava_fire_pressure_setup_once_then_attack_move_swords_dance_move_wing_attack:plan_bugsy_scyther_vs_quilava_fire_pressure_switch_preserve_then_rescore_switch_ledian_move_wing_attack`
  - `trajectory:chuck_poliwrath_vs_pidgeotto_ice_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_switch_preserve_then_rescore_switch_sudowoodo_move_focus_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_attack_now_move_focus_punch_move_focus_punch`
  - `trajectory:chuck_poliwrath_vs_pidgeotto_ice_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_switch_preserve_then_rescore_switch_sudowoodo_move_focus_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_status_once_then_attack_move_hypnosis_move_focus_punch`
  - `trajectory:clair_dragonair_vs_suicune_hidden_ice_beam:plan_clair_dragonair_vs_suicune_hidden_ice_beam_attack_now_move_thunder_move_thunder:plan_clair_dragonair_vs_suicune_hidden_ice_beam_switch_preserve_then_rescore_switch_kingdra_move_thunder`
  - `trajectory:clair_kingdra_vs_lapras_dragon_dance_or_attack:plan_clair_kingdra_vs_lapras_dragon_dance_or_attack_setup_once_then_attack_move_dragon_dance_move_outrage:plan_clair_kingdra_vs_lapras_dragon_dance_or_attack_attack_now_move_outrage_move_outrage`
  - `trajectory:erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_attack_now_move_sludge_bomb_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_setup_once_then_attack_move_swords_dance_move_sludge_bomb`
  - `trajectory:erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_attack_now_move_sludge_bomb_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_status_once_then_attack_move_sleep_powder_move_sludge_bomb`
  - `trajectory:erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_attack_now_move_sludge_bomb_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_switch_preserve_then_rescore_switch_exeggutor_move_sludge_bomb`
  - `trajectory:erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_setup_once_then_attack_move_swords_dance_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_status_once_then_attack_move_sleep_powder_move_sludge_bomb`
  - `trajectory:erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_setup_once_then_attack_move_swords_dance_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_switch_preserve_then_rescore_switch_exeggutor_move_sludge_bomb`
  - `trajectory:erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_status_once_then_attack_move_sleep_powder_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_switch_preserve_then_rescore_switch_exeggutor_move_sludge_bomb`
  - `trajectory:falkner_pidgeotto_vs_geodude_rock_risk:plan_falkner_pidgeotto_vs_geodude_rock_risk_scout_probe_then_commit_move_sand_attack_move_gust:plan_falkner_pidgeotto_vs_geodude_rock_risk_attack_now_move_gust_move_gust`
  - `trajectory:falkner_pidgeotto_vs_geodude_rock_risk:plan_falkner_pidgeotto_vs_geodude_rock_risk_scout_probe_then_commit_move_sand_attack_move_gust:plan_falkner_pidgeotto_vs_geodude_rock_risk_switch_preserve_then_rescore_switch_noctowl_move_gust`
  - `trajectory:lance_dragonite_vs_suicune_champion_ace:plan_lance_dragonite_vs_suicune_champion_ace_switch_preserve_then_rescore_switch_kingdra_move_outrage:plan_lance_dragonite_vs_suicune_champion_ace_attack_now_move_outrage_move_outrage`
  - `trajectory:lance_dragonite_vs_suicune_champion_ace:plan_lance_dragonite_vs_suicune_champion_ace_switch_preserve_then_rescore_switch_kingdra_move_outrage:plan_lance_dragonite_vs_suicune_champion_ace_setup_once_then_attack_move_dragon_dance_move_outrage`
  - `trajectory:lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_attack_now_move_giga_drain_move_giga_drain:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_status_once_then_attack_move_sleep_powder_move_giga_drain`
  - `trajectory:lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_attack_now_move_giga_drain_move_giga_drain:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_switch_preserve_then_rescore_switch_kingdra_move_giga_drain`
  - `trajectory:lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_status_once_then_attack_move_sleep_powder_move_giga_drain:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_switch_preserve_then_rescore_switch_kingdra_move_giga_drain`
  - `trajectory:morty_gengar_vs_kadabra_destiny_bond:plan_morty_gengar_vs_kadabra_destiny_bond_attack_now_move_shadow_ball_move_shadow_ball:plan_morty_gengar_vs_kadabra_destiny_bond_switch_preserve_then_rescore_switch_misdreavus_move_shadow_ball`
  - `trajectory:pryce_slowking_vs_ampharos_ground_pivot:plan_pryce_slowking_vs_ampharos_ground_pivot_switch_preserve_then_rescore_switch_piloswine_move_surf:plan_pryce_slowking_vs_ampharos_ground_pivot_attack_now_move_surf_move_surf`
  - `trajectory:pryce_slowking_vs_ampharos_ground_pivot:plan_pryce_slowking_vs_ampharos_ground_pivot_switch_preserve_then_rescore_switch_piloswine_move_surf:plan_pryce_slowking_vs_ampharos_ground_pivot_recover_until_safe_move_rest_move_surf`
  - `trajectory:pryce_slowking_vs_ampharos_ground_pivot:plan_pryce_slowking_vs_ampharos_ground_pivot_switch_preserve_then_rescore_switch_piloswine_move_surf:plan_pryce_slowking_vs_ampharos_ground_pivot_speed_control_then_attack_move_thunder_wave_move_surf`
  - `trajectory:whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_attack_now_move_body_slam_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_recover_until_safe_move_milk_drink_move_body_slam`
  - `trajectory:whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_attack_now_move_body_slam_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_scout_probe_then_commit_move_milk_drink_move_body_slam`
  - `trajectory:whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_attack_now_move_body_slam_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_switch_preserve_then_rescore_switch_girafarig_move_body_slam`
  - `trajectory:whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_scout_probe_then_commit_move_milk_drink_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_recover_until_safe_move_milk_drink_move_body_slam`
  - `trajectory:whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_scout_probe_then_commit_move_milk_drink_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_switch_preserve_then_rescore_switch_girafarig_move_body_slam`
  - `trajectory:whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_switch_preserve_then_rescore_switch_girafarig_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_recover_until_safe_move_milk_drink_move_body_slam`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Add plan/counterfactual coverage for the stop condition before any ROM change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory_switch_preserve_boundary

- Type: `switch_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Trajectory labels should distinguish useful preservation switches from passive switching that gives up the fight.
- Evidence:
  - `trajectory:brock_golem_vs_vaporeon_explosion_question:plan_brock_golem_vs_vaporeon_explosion_question_sacrifice_trade_for_clean_switch_move_explosion_move_explosion:plan_brock_golem_vs_vaporeon_explosion_question_attack_now_move_explosion_move_explosion`
  - `trajectory:brock_golem_vs_vaporeon_explosion_question:plan_brock_golem_vs_vaporeon_explosion_question_sacrifice_trade_for_clean_switch_move_explosion_move_explosion:plan_brock_golem_vs_vaporeon_explosion_question_setup_once_then_attack_move_curse_move_explosion`
  - `trajectory:brock_golem_vs_vaporeon_explosion_question:plan_brock_golem_vs_vaporeon_explosion_question_sacrifice_trade_for_clean_switch_move_explosion_move_explosion:plan_brock_golem_vs_vaporeon_explosion_question_switch_preserve_then_rescore_switch_omastar_move_explosion`
  - `trajectory:bugsy_scyther_vs_quilava_fire_pressure:plan_bugsy_scyther_vs_quilava_fire_pressure_setup_once_then_attack_move_swords_dance_move_wing_attack:plan_bugsy_scyther_vs_quilava_fire_pressure_attack_now_move_wing_attack_move_wing_attack`
  - `trajectory:bugsy_scyther_vs_quilava_fire_pressure:plan_bugsy_scyther_vs_quilava_fire_pressure_setup_once_then_attack_move_swords_dance_move_wing_attack:plan_bugsy_scyther_vs_quilava_fire_pressure_switch_preserve_then_rescore_switch_ledian_move_wing_attack`
  - `trajectory:chuck_poliwrath_vs_pidgeotto_ice_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_switch_preserve_then_rescore_switch_sudowoodo_move_focus_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_attack_now_move_focus_punch_move_focus_punch`
  - `trajectory:chuck_poliwrath_vs_pidgeotto_ice_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_switch_preserve_then_rescore_switch_sudowoodo_move_focus_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_status_once_then_attack_move_hypnosis_move_focus_punch`
  - `trajectory:clair_dragonair_vs_suicune_hidden_ice_beam:plan_clair_dragonair_vs_suicune_hidden_ice_beam_attack_now_move_thunder_move_thunder:plan_clair_dragonair_vs_suicune_hidden_ice_beam_commit_lock_only_if_safe_move_outrage_move_thunder`
  - `trajectory:clair_dragonair_vs_suicune_hidden_ice_beam:plan_clair_dragonair_vs_suicune_hidden_ice_beam_attack_now_move_thunder_move_thunder:plan_clair_dragonair_vs_suicune_hidden_ice_beam_switch_preserve_then_rescore_switch_kingdra_move_thunder`
  - `trajectory:erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_attack_now_move_sludge_bomb_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_switch_preserve_then_rescore_switch_exeggutor_move_sludge_bomb`
  - `trajectory:erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_setup_once_then_attack_move_swords_dance_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_switch_preserve_then_rescore_switch_exeggutor_move_sludge_bomb`
  - `trajectory:erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_status_once_then_attack_move_sleep_powder_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_switch_preserve_then_rescore_switch_exeggutor_move_sludge_bomb`
  - `trajectory:falkner_pidgeotto_vs_geodude_rock_risk:plan_falkner_pidgeotto_vs_geodude_rock_risk_scout_probe_then_commit_move_sand_attack_move_gust:plan_falkner_pidgeotto_vs_geodude_rock_risk_attack_now_move_gust_move_gust`
  - `trajectory:falkner_pidgeotto_vs_geodude_rock_risk:plan_falkner_pidgeotto_vs_geodude_rock_risk_scout_probe_then_commit_move_sand_attack_move_gust:plan_falkner_pidgeotto_vs_geodude_rock_risk_switch_preserve_then_rescore_switch_noctowl_move_gust`
  - `trajectory:lance_dragonite_vs_suicune_champion_ace:plan_lance_dragonite_vs_suicune_champion_ace_switch_preserve_then_rescore_switch_kingdra_move_outrage:plan_lance_dragonite_vs_suicune_champion_ace_attack_now_move_outrage_move_outrage`
  - `trajectory:lance_dragonite_vs_suicune_champion_ace:plan_lance_dragonite_vs_suicune_champion_ace_switch_preserve_then_rescore_switch_kingdra_move_outrage:plan_lance_dragonite_vs_suicune_champion_ace_setup_once_then_attack_move_dragon_dance_move_outrage`
  - `trajectory:lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_attack_now_move_giga_drain_move_giga_drain:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_switch_preserve_then_rescore_switch_kingdra_move_giga_drain`
  - `trajectory:lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_status_once_then_attack_move_sleep_powder_move_giga_drain:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_switch_preserve_then_rescore_switch_kingdra_move_giga_drain`
  - `trajectory:morty_gengar_vs_kadabra_destiny_bond:plan_morty_gengar_vs_kadabra_destiny_bond_attack_now_move_shadow_ball_move_shadow_ball:plan_morty_gengar_vs_kadabra_destiny_bond_sacrifice_trade_for_clean_switch_move_destiny_bond_move_shadow_ball`
  - `trajectory:morty_gengar_vs_kadabra_destiny_bond:plan_morty_gengar_vs_kadabra_destiny_bond_attack_now_move_shadow_ball_move_shadow_ball:plan_morty_gengar_vs_kadabra_destiny_bond_switch_preserve_then_rescore_switch_misdreavus_move_shadow_ball`
  - `trajectory:pryce_slowking_vs_ampharos_ground_pivot:plan_pryce_slowking_vs_ampharos_ground_pivot_switch_preserve_then_rescore_switch_piloswine_move_surf:plan_pryce_slowking_vs_ampharos_ground_pivot_attack_now_move_surf_move_surf`
  - `trajectory:pryce_slowking_vs_ampharos_ground_pivot:plan_pryce_slowking_vs_ampharos_ground_pivot_switch_preserve_then_rescore_switch_piloswine_move_surf:plan_pryce_slowking_vs_ampharos_ground_pivot_recover_until_safe_move_rest_move_surf`
  - `trajectory:pryce_slowking_vs_ampharos_ground_pivot:plan_pryce_slowking_vs_ampharos_ground_pivot_switch_preserve_then_rescore_switch_piloswine_move_surf:plan_pryce_slowking_vs_ampharos_ground_pivot_speed_control_then_attack_move_thunder_wave_move_surf`
  - `trajectory:whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_attack_now_move_body_slam_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_recover_until_safe_move_milk_drink_move_body_slam`
  - `trajectory:whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_attack_now_move_body_slam_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_scout_probe_then_commit_move_milk_drink_move_body_slam`
  - `trajectory:whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_attack_now_move_body_slam_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_switch_preserve_then_rescore_switch_girafarig_move_body_slam`
  - `trajectory:whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_scout_probe_then_commit_move_milk_drink_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_recover_until_safe_move_milk_drink_move_body_slam`
  - `trajectory:whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_scout_probe_then_commit_move_milk_drink_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_switch_preserve_then_rescore_switch_girafarig_move_body_slam`
  - `trajectory:whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_switch_preserve_then_rescore_switch_girafarig_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_recover_until_safe_move_milk_drink_move_body_slam`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Review move-vs-switch arbitration and add targeted switch-action fixtures first.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory:switch_policy

- Type: `switch_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Use trajectory evidence for a plan-policy proposal.
- Evidence:
  - `bugsy_scyther_vs_quilava_fire_pressure:plan_bugsy_scyther_vs_quilava_fire_pressure_setup_once_then_attack_move_swords_dance_move_wing_attack:plan_bugsy_scyther_vs_quilava_fire_pressure_attack_now_move_wing_attack_move_wing_attack`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Review move-vs-switch arbitration and add targeted switch-action fixtures first.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory:switch_policy

- Type: `switch_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Use trajectory evidence for a plan-policy proposal.
- Evidence:
  - `bugsy_scyther_vs_quilava_fire_pressure:plan_bugsy_scyther_vs_quilava_fire_pressure_setup_once_then_attack_move_swords_dance_move_wing_attack:plan_bugsy_scyther_vs_quilava_fire_pressure_switch_preserve_then_rescore_switch_ledian_move_wing_attack`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Review move-vs-switch arbitration and add targeted switch-action fixtures first.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory:switch_policy

- Type: `switch_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Use trajectory evidence for a plan-policy proposal.
- Evidence:
  - `lance_dragonite_vs_suicune_champion_ace:plan_lance_dragonite_vs_suicune_champion_ace_switch_preserve_then_rescore_switch_kingdra_move_outrage:plan_lance_dragonite_vs_suicune_champion_ace_attack_now_move_outrage_move_outrage`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Review move-vs-switch arbitration and add targeted switch-action fixtures first.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory:switch_policy

- Type: `switch_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Use trajectory evidence for a plan-policy proposal.
- Evidence:
  - `lance_dragonite_vs_suicune_champion_ace:plan_lance_dragonite_vs_suicune_champion_ace_switch_preserve_then_rescore_switch_kingdra_move_outrage:plan_lance_dragonite_vs_suicune_champion_ace_setup_once_then_attack_move_dragon_dance_move_outrage`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Review move-vs-switch arbitration and add targeted switch-action fixtures first.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory:switch_policy

- Type: `switch_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Use trajectory evidence for a plan-policy proposal.
- Evidence:
  - `whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_attack_now_move_body_slam_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_scout_probe_then_commit_move_milk_drink_move_body_slam`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Review move-vs-switch arbitration and add targeted switch-action fixtures first.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory:switch_policy

- Type: `switch_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Use trajectory evidence for a plan-policy proposal.
- Evidence:
  - `whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_attack_now_move_body_slam_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_switch_preserve_then_rescore_switch_girafarig_move_body_slam`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Review move-vs-switch arbitration and add targeted switch-action fixtures first.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory:switch_policy

- Type: `switch_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Use trajectory evidence for a plan-policy proposal.
- Evidence:
  - `whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_attack_now_move_body_slam_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_recover_until_safe_move_milk_drink_move_body_slam`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Review move-vs-switch arbitration and add targeted switch-action fixtures first.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory:switch_policy

- Type: `switch_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Use trajectory evidence for a plan-policy proposal.
- Evidence:
  - `whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_scout_probe_then_commit_move_milk_drink_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_switch_preserve_then_rescore_switch_girafarig_move_body_slam`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Review move-vs-switch arbitration and add targeted switch-action fixtures first.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory:switch_policy

- Type: `switch_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Use trajectory evidence for a plan-policy proposal.
- Evidence:
  - `whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_scout_probe_then_commit_move_milk_drink_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_recover_until_safe_move_milk_drink_move_body_slam`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Review move-vs-switch arbitration and add targeted switch-action fixtures first.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory:switch_policy

- Type: `switch_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Use trajectory evidence for a plan-policy proposal.
- Evidence:
  - `whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_switch_preserve_then_rescore_switch_girafarig_move_body_slam:plan_whitney_miltank_vs_geodude_rollout_temptation_recover_until_safe_move_milk_drink_move_body_slam`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Review move-vs-switch arbitration and add targeted switch-action fixtures first.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory:switch_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `brock_golem_vs_vaporeon_explosion_question:plan_brock_golem_vs_vaporeon_explosion_question_sacrifice_trade_for_clean_switch_move_explosion_move_explosion:plan_brock_golem_vs_vaporeon_explosion_question_attack_now_move_explosion_move_explosion`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - strict plan preference needs condition tags
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: trajectory:switch_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `brock_golem_vs_vaporeon_explosion_question:plan_brock_golem_vs_vaporeon_explosion_question_sacrifice_trade_for_clean_switch_move_explosion_move_explosion:plan_brock_golem_vs_vaporeon_explosion_question_setup_once_then_attack_move_curse_move_explosion`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - strict plan preference needs condition tags
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: trajectory:switch_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `brock_golem_vs_vaporeon_explosion_question:plan_brock_golem_vs_vaporeon_explosion_question_sacrifice_trade_for_clean_switch_move_explosion_move_explosion:plan_brock_golem_vs_vaporeon_explosion_question_switch_preserve_then_rescore_switch_omastar_move_explosion`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - strict plan preference needs condition tags
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: trajectory:switch_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `falkner_pidgeotto_vs_geodude_rock_risk:plan_falkner_pidgeotto_vs_geodude_rock_risk_scout_probe_then_commit_move_sand_attack_move_gust:plan_falkner_pidgeotto_vs_geodude_rock_risk_attack_now_move_gust_move_gust`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - strict plan preference needs condition tags
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: trajectory:switch_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `falkner_pidgeotto_vs_geodude_rock_risk:plan_falkner_pidgeotto_vs_geodude_rock_risk_scout_probe_then_commit_move_sand_attack_move_gust:plan_falkner_pidgeotto_vs_geodude_rock_risk_switch_preserve_then_rescore_switch_noctowl_move_gust`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - strict plan preference needs condition tags
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: trajectory:switch_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `pryce_slowking_vs_ampharos_ground_pivot:plan_pryce_slowking_vs_ampharos_ground_pivot_switch_preserve_then_rescore_switch_piloswine_move_surf:plan_pryce_slowking_vs_ampharos_ground_pivot_attack_now_move_surf_move_surf`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - strict plan preference needs condition tags
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: trajectory:switch_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `pryce_slowking_vs_ampharos_ground_pivot:plan_pryce_slowking_vs_ampharos_ground_pivot_switch_preserve_then_rescore_switch_piloswine_move_surf:plan_pryce_slowking_vs_ampharos_ground_pivot_speed_control_then_attack_move_thunder_wave_move_surf`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - strict plan preference needs condition tags
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: trajectory:switch_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `pryce_slowking_vs_ampharos_ground_pivot:plan_pryce_slowking_vs_ampharos_ground_pivot_switch_preserve_then_rescore_switch_piloswine_move_surf:plan_pryce_slowking_vs_ampharos_ground_pivot_recover_until_safe_move_rest_move_surf`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - strict plan preference needs condition tags
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: trajectory:switch_policy

- Type: `switch_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Use trajectory evidence for a plan-policy proposal.
- Evidence:
  - `clair_dragonair_vs_suicune_hidden_ice_beam:plan_clair_dragonair_vs_suicune_hidden_ice_beam_attack_now_move_thunder_move_thunder:plan_clair_dragonair_vs_suicune_hidden_ice_beam_switch_preserve_then_rescore_switch_kingdra_move_thunder`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Review move-vs-switch arbitration and add targeted switch-action fixtures first.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory:switch_policy

- Type: `switch_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Use trajectory evidence for a plan-policy proposal.
- Evidence:
  - `clair_dragonair_vs_suicune_hidden_ice_beam:plan_clair_dragonair_vs_suicune_hidden_ice_beam_attack_now_move_thunder_move_thunder:plan_clair_dragonair_vs_suicune_hidden_ice_beam_commit_lock_only_if_safe_move_outrage_move_thunder`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Review move-vs-switch arbitration and add targeted switch-action fixtures first.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory:switch_policy

- Type: `switch_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Use trajectory evidence for a plan-policy proposal.
- Evidence:
  - `morty_gengar_vs_kadabra_destiny_bond:plan_morty_gengar_vs_kadabra_destiny_bond_attack_now_move_shadow_ball_move_shadow_ball:plan_morty_gengar_vs_kadabra_destiny_bond_sacrifice_trade_for_clean_switch_move_destiny_bond_move_shadow_ball`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Review move-vs-switch arbitration and add targeted switch-action fixtures first.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory:switch_policy

- Type: `switch_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Use trajectory evidence for a plan-policy proposal.
- Evidence:
  - `morty_gengar_vs_kadabra_destiny_bond:plan_morty_gengar_vs_kadabra_destiny_bond_attack_now_move_shadow_ball_move_shadow_ball:plan_morty_gengar_vs_kadabra_destiny_bond_switch_preserve_then_rescore_switch_misdreavus_move_shadow_ball`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Review move-vs-switch arbitration and add targeted switch-action fixtures first.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory:switch_policy

- Type: `switch_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Use trajectory evidence for a plan-policy proposal.
- Evidence:
  - `chuck_poliwrath_vs_pidgeotto_ice_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_switch_preserve_then_rescore_switch_sudowoodo_move_focus_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_attack_now_move_focus_punch_move_focus_punch`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Review move-vs-switch arbitration and add targeted switch-action fixtures first.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory:switch_policy

- Type: `switch_policy`
- Readiness: `manual_review`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Use trajectory evidence for a plan-policy proposal.
- Evidence:
  - `chuck_poliwrath_vs_pidgeotto_ice_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_switch_preserve_then_rescore_switch_sudowoodo_move_focus_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_status_once_then_attack_move_hypnosis_move_focus_punch`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Suggested implementation: Review move-vs-switch arbitration and add targeted switch-action fixtures first.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
  - `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
  - `python tools\audit\check_boss_ai_trace_invariants.py`
  - `python tools\audit\check_boss_ai_policy_contract.py`
  - `python tools\audit\check_boss_ai_no_cheat.py`
  - `python tools\audit\check_boss_ai_gating.py`
  - `python tools\audit\check_boss_ai_memory_budget.py`

## Candidate: trajectory:sequence_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `clair_kingdra_vs_lapras_dragon_dance_or_attack:plan_clair_kingdra_vs_lapras_dragon_dance_or_attack_setup_once_then_attack_move_dragon_dance_move_outrage:plan_clair_kingdra_vs_lapras_dragon_dance_or_attack_attack_now_move_outrage_move_outrage`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - strict plan preference needs condition tags
  - collect the same lesson type in at least two battle phases
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: trajectory:sequence_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_attack_now_move_sludge_bomb_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_setup_once_then_attack_move_swords_dance_move_sludge_bomb`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - collect the same lesson type in at least two battle phases
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: trajectory:sequence_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_attack_now_move_sludge_bomb_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_status_once_then_attack_move_sleep_powder_move_sludge_bomb`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - collect the same lesson type in at least two battle phases
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: trajectory:sequence_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_attack_now_move_sludge_bomb_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_switch_preserve_then_rescore_switch_exeggutor_move_sludge_bomb`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - collect the same lesson type in at least two battle phases
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: trajectory:sequence_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_setup_once_then_attack_move_swords_dance_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_status_once_then_attack_move_sleep_powder_move_sludge_bomb`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - collect the same lesson type in at least two battle phases
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: trajectory:sequence_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_setup_once_then_attack_move_swords_dance_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_switch_preserve_then_rescore_switch_exeggutor_move_sludge_bomb`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - collect the same lesson type in at least two battle phases
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: trajectory:sequence_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_status_once_then_attack_move_sleep_powder_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_switch_preserve_then_rescore_switch_exeggutor_move_sludge_bomb`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - collect the same lesson type in at least two battle phases
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: trajectory:sequence_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_attack_now_move_giga_drain_move_giga_drain:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_status_once_then_attack_move_sleep_powder_move_giga_drain`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - collect the same lesson type in at least two battle phases
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: trajectory:sequence_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_attack_now_move_giga_drain_move_giga_drain:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_switch_preserve_then_rescore_switch_kingdra_move_giga_drain`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - collect the same lesson type in at least two battle phases
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`

## Candidate: trajectory:sequence_policy

- Type: `needs_more_labels`
- Readiness: `blocked`
- ROM behavior change: `False`
- Requires human approval: `True`
- Summary: Collect more trajectory labels before changing behavior.
- Evidence:
  - `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_status_once_then_attack_move_sleep_powder_move_giga_drain:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_switch_preserve_then_rescore_switch_kingdra_move_giga_drain`
- Improves:
  - none proven yet
- Risks / worsens:
  - none in current reports
- Blocking reasons:
  - collect the same lesson type in at least two battle phases
- Suggested implementation: Ask for more boundary labels before proposing a behavior change.
- Required verification:
  - `python -m tools.boss_ai_preference validate`
  - `python tools\audit\check_boss_ai_preference.py`
