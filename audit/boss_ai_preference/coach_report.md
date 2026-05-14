# Boss AI Coach Report

Generated: 2026-05-13T07:04:15+00:00
Rollout mode: `deterministic_public_worst_case`

## Summary

- Plan questions ready: 20
- Trajectory preferences: 56
- Plan demonstrations: 3
- Suggested next review count: 10

## Phase Needs

Early, mid, and late phases all have at least one trajectory label.

## Common Generated Plan Shapes

- `attack_now`: 20
- `switch_preserve_then_rescore`: 17
- `setup_once_then_attack`: 9
- `status_once_then_attack`: 9
- `scout_probe_then_commit`: 2
- `sleep_then_setup_then_attack`: 2
- `sacrifice_trade_for_clean_switch`: 2
- `pressure_recover_then_lock`: 1
- `commit_lock_only_if_safe`: 1
- `speed_control_then_attack`: 1
- `recover_until_safe`: 1

## Top Coach Questions

- `whitney_miltank_vs_geodude_rollout_temptation` (Whitney, mid): Body Slam pressure, heal when needed, then consider Rollout vs Body Slam now
- `lance_dragonite_vs_suicune_champion_ace` (Champion Lance, late): Outrage now vs Dragon Dance, then Outrage
- `bugsy_scyther_vs_quilava_fire_pressure` (Bugsy, early): Wing Attack now vs Swords Dance, then Wing Attack
- `clair_dragonair_vs_suicune_hidden_ice_beam` (Clair, mid): Thunder now vs Switch to Kingdra, then re-score
- `falkner_pidgeotto_vs_geodude_rock_risk` (Falkner, mid): Gust now vs Probe with Sand Attack, then commit
- `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance` (Champion Lance, mid): Giga Drain now vs Sleep Powder, then Quiver Dance, then Giga Drain
- `chuck_poliwrath_vs_pidgeotto_ice_punch` (Chuck, mid): Focus Punch now vs Hypnosis, then Focus Punch
- `pryce_slowking_vs_ampharos_ground_pivot` (Pryce, mid): Surf now vs Thunder Wave, then Surf
- `erika_victreebel_vs_snorlax_sleep_or_boost` (Erika, mid): Sludge Bomb now vs Sleep Powder, then Swords Dance, then Sludge Bomb
- `karen_crobat_vs_dragonite_toxic_or_attack` (Karen, mid): Wing Attack now vs Toxic, then Wing Attack

## Trajectory Details

# Boss AI Trajectory Preference Report

Generated: 2026-05-13T07:04:15+00:00

## Summary

- Fixtures: 57
- Trajectory preferences: 56
- Plan demonstrations: 3
- Conflicting duplicate trajectory rows: 0
- Stale trajectory rows: 0

## Choice Counts

- `a_better`: 29
- `b_better`: 2
- `neither_best_plan_missing`: 25

## Phase Coverage

- `early`: 3
- `late`: 5
- `mid`: 48

## Lesson Type Counts

- `hard_rule`: 1
- `scout_policy`: 1
- `sequence_policy`: 24
- `switch_policy`: 30

## Conflicts

No conflicting duplicate trajectory rows.

## Stale Rows

No trajectory rows have changed source hashes.

## Recent Trajectories

- `whitney_miltank_vs_geodude_rollout_temptation:plan_whitney_miltank_vs_geodude_rollout_temptation_pressure_recover_then_lock_move_body_slam_move_body_slam_move_milk_drink_move_rollout:plan_whitney_miltank_vs_geodude_rollout_temptation_switch_preserve_then_rescore_switch_girafarig_move_body_slam`: `a_better` (sequence_policy, mid)
- `external_gsc_rhydon_vs_sleeping_snorlax_curse_window:plan_external_gsc_rhydon_vs_sleeping_snorlax_curse_window_setup_once_then_attack_move_curse_move_earthquake:plan_external_gsc_rhydon_vs_sleeping_snorlax_curse_window_attack_now_move_earthquake_move_earthquake`: `a_better` (sequence_policy, late)
- `external_gsc_rhydon_vs_sleeping_snorlax_curse_window:plan_external_gsc_rhydon_vs_sleeping_snorlax_curse_window_setup_once_then_attack_move_curse_move_earthquake:plan_external_gsc_rhydon_vs_sleeping_snorlax_curse_window_switch_preserve_then_rescore_switch_zapdos_move_earthquake`: `a_better` (sequence_policy, late)
- `will_slowbro_vs_houndoom_amnesia_or_surf:plan_will_slowbro_vs_houndoom_amnesia_or_surf_switch_preserve_then_rescore_switch_houndoom_move_surf:plan_will_slowbro_vs_houndoom_amnesia_or_surf_attack_now_move_surf_move_surf`: `a_better` (switch_policy, mid)
- `pryce_slowking_vs_ampharos_ground_pivot:plan_pryce_slowking_vs_ampharos_ground_pivot_attack_now_move_surf_move_surf:plan_pryce_slowking_vs_ampharos_ground_pivot_speed_control_then_attack_move_thunder_wave_move_surf`: `neither_best_plan_missing` (switch_policy, mid)
- `pryce_slowking_vs_ampharos_ground_pivot:plan_pryce_slowking_vs_ampharos_ground_pivot_attack_now_move_surf_move_surf:plan_pryce_slowking_vs_ampharos_ground_pivot_recover_until_safe_move_rest_move_surf`: `neither_best_plan_missing` (switch_policy, mid)
- `pryce_slowking_vs_ampharos_ground_pivot:plan_pryce_slowking_vs_ampharos_ground_pivot_speed_control_then_attack_move_thunder_wave_move_surf:plan_pryce_slowking_vs_ampharos_ground_pivot_recover_until_safe_move_rest_move_surf`: `neither_best_plan_missing` (switch_policy, mid)
- `lance_dragonite_vs_suicune_champion_ace:plan_lance_dragonite_vs_suicune_champion_ace_attack_now_move_outrage_move_outrage:plan_lance_dragonite_vs_suicune_champion_ace_setup_once_then_attack_move_dragon_dance_move_outrage`: `neither_best_plan_missing` (switch_policy, late)
- `bugsy_scyther_vs_quilava_fire_pressure:plan_bugsy_scyther_vs_quilava_fire_pressure_attack_now_move_wing_attack_move_wing_attack:plan_bugsy_scyther_vs_quilava_fire_pressure_switch_preserve_then_rescore_switch_ledian_move_wing_attack`: `neither_best_plan_missing` (sequence_policy, early)
- `falkner_pidgeotto_vs_geodude_rock_risk:plan_falkner_pidgeotto_vs_geodude_rock_risk_attack_now_move_gust_move_gust:plan_falkner_pidgeotto_vs_geodude_rock_risk_switch_preserve_then_rescore_switch_noctowl_move_gust`: `neither_best_plan_missing` (scout_policy, mid)
- `chuck_poliwrath_vs_pidgeotto_ice_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_attack_now_move_focus_punch_move_focus_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_status_once_then_attack_move_hypnosis_move_focus_punch`: `neither_best_plan_missing` (switch_policy, mid)
- `morty_gengar_vs_kadabra_destiny_bond:plan_morty_gengar_vs_kadabra_destiny_bond_sacrifice_trade_for_clean_switch_move_destiny_bond_move_shadow_ball:plan_morty_gengar_vs_kadabra_destiny_bond_switch_preserve_then_rescore_switch_misdreavus_move_shadow_ball`: `neither_best_plan_missing` (hard_rule, mid)
- `erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_attack_now_move_sludge_bomb_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_sleep_then_setup_then_attack_move_sleep_powder_move_swords_dance_move_sludge_bomb`: `b_better` (sequence_policy, mid)
- `erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_sleep_then_setup_then_attack_move_sleep_powder_move_swords_dance_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_setup_once_then_attack_move_swords_dance_move_sludge_bomb`: `a_better` (sequence_policy, mid)
- `erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_sleep_then_setup_then_attack_move_sleep_powder_move_swords_dance_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_status_once_then_attack_move_sleep_powder_move_sludge_bomb`: `a_better` (sequence_policy, mid)
- `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_attack_now_move_giga_drain_move_giga_drain:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_setup_once_then_attack_move_quiver_dance_move_giga_drain`: `neither_best_plan_missing` (sequence_policy, mid)
- `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_attack_now_move_giga_drain_move_giga_drain:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_sleep_then_setup_then_attack_move_sleep_powder_move_quiver_dance_move_giga_drain`: `b_better` (sequence_policy, mid)
- `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_sleep_then_setup_then_attack_move_sleep_powder_move_quiver_dance_move_giga_drain:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_setup_once_then_attack_move_quiver_dance_move_giga_drain`: `a_better` (sequence_policy, mid)
- `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_sleep_then_setup_then_attack_move_sleep_powder_move_quiver_dance_move_giga_drain:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_status_once_then_attack_move_sleep_powder_move_giga_drain`: `a_better` (sequence_policy, mid)
- `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_setup_once_then_attack_move_quiver_dance_move_giga_drain:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_status_once_then_attack_move_sleep_powder_move_giga_drain`: `neither_best_plan_missing` (sequence_policy, mid)
