# Boss AI Coach Report

Generated: 2026-05-12T10:57:09+00:00
Rollout mode: `deterministic_public_worst_case`

## Summary

- Plan questions ready: 20
- Trajectory preferences: 34
- Plan demonstrations: 3
- Suggested next review count: 10

## Phase Needs

Early, mid, and late phases all have at least one trajectory label.

## Common Generated Plan Shapes

- `attack_now`: 20
- `switch_preserve_then_rescore`: 19
- `status_once_then_attack`: 9
- `setup_once_then_attack`: 7
- `recover_until_safe`: 3
- `scout_probe_then_commit`: 2
- `sacrifice_trade_for_clean_switch`: 2
- `speed_control_then_attack`: 1
- `commit_lock_only_if_safe`: 1

## Top Coach Questions

- `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance` (Champion Lance, mid): Giga Drain now vs Sleep Powder, then Giga Drain
- `whitney_miltank_vs_geodude_rollout_temptation` (Whitney, mid): Body Slam now vs Probe with Milk Drink, then commit
- `erika_victreebel_vs_snorlax_sleep_or_boost` (Erika, mid): Sludge Bomb now vs Swords Dance, then Sludge Bomb
- `lance_dragonite_vs_suicune_champion_ace` (Champion Lance, late): Outrage now vs Dragon Dance, then Outrage
- `bugsy_scyther_vs_quilava_fire_pressure` (Bugsy, early): Wing Attack now vs Swords Dance, then Wing Attack
- `pryce_slowking_vs_ampharos_ground_pivot` (Pryce, mid): Surf now vs Thunder Wave, then Surf
- `clair_dragonair_vs_suicune_hidden_ice_beam` (Clair, mid): Thunder now vs Switch to Kingdra, then re-score
- `falkner_pidgeotto_vs_geodude_rock_risk` (Falkner, mid): Gust now vs Probe with Sand Attack, then commit
- `chuck_poliwrath_vs_pidgeotto_ice_punch` (Chuck, mid): Focus Punch now vs Hypnosis, then Focus Punch
- `bugsy_ariados_vs_pidgey_toxic_or_attack` (Bugsy, early): Poison Sting now vs Toxic, then Poison Sting

## Trajectory Details

# Boss AI Trajectory Preference Report

Generated: 2026-05-12T10:57:09+00:00

## Summary

- Fixtures: 53
- Trajectory preferences: 34
- Plan demonstrations: 3
- Conflicting duplicate trajectory rows: 0
- Stale trajectory rows: 0

## Choice Counts

- `a_better`: 19
- `neither_best_plan_missing`: 15

## Phase Coverage

- `early`: 2
- `late`: 2
- `mid`: 30

## Lesson Type Counts

- `sequence_policy`: 10
- `switch_policy`: 24

## Conflicts

No conflicting duplicate trajectory rows.

## Stale Rows

No trajectory rows have changed source hashes.

## Recent Trajectories

- `falkner_pidgeotto_vs_geodude_rock_risk:plan_falkner_pidgeotto_vs_geodude_rock_risk_scout_probe_then_commit_move_sand_attack_move_gust:plan_falkner_pidgeotto_vs_geodude_rock_risk_switch_preserve_then_rescore_switch_noctowl_move_gust`: `a_better` (switch_policy, mid)
- `pryce_slowking_vs_ampharos_ground_pivot:plan_pryce_slowking_vs_ampharos_ground_pivot_switch_preserve_then_rescore_switch_piloswine_move_surf:plan_pryce_slowking_vs_ampharos_ground_pivot_attack_now_move_surf_move_surf`: `a_better` (switch_policy, mid)
- `pryce_slowking_vs_ampharos_ground_pivot:plan_pryce_slowking_vs_ampharos_ground_pivot_switch_preserve_then_rescore_switch_piloswine_move_surf:plan_pryce_slowking_vs_ampharos_ground_pivot_speed_control_then_attack_move_thunder_wave_move_surf`: `a_better` (switch_policy, mid)
- `pryce_slowking_vs_ampharos_ground_pivot:plan_pryce_slowking_vs_ampharos_ground_pivot_switch_preserve_then_rescore_switch_piloswine_move_surf:plan_pryce_slowking_vs_ampharos_ground_pivot_recover_until_safe_move_rest_move_surf`: `a_better` (switch_policy, mid)
- `clair_dragonair_vs_suicune_hidden_ice_beam:plan_clair_dragonair_vs_suicune_hidden_ice_beam_attack_now_move_thunder_move_thunder:plan_clair_dragonair_vs_suicune_hidden_ice_beam_switch_preserve_then_rescore_switch_kingdra_move_thunder`: `a_better` (switch_policy, mid)
- `clair_dragonair_vs_suicune_hidden_ice_beam:plan_clair_dragonair_vs_suicune_hidden_ice_beam_attack_now_move_thunder_move_thunder:plan_clair_dragonair_vs_suicune_hidden_ice_beam_commit_lock_only_if_safe_move_outrage_move_thunder`: `a_better` (switch_policy, mid)
- `morty_gengar_vs_kadabra_destiny_bond:plan_morty_gengar_vs_kadabra_destiny_bond_attack_now_move_shadow_ball_move_shadow_ball:plan_morty_gengar_vs_kadabra_destiny_bond_sacrifice_trade_for_clean_switch_move_destiny_bond_move_shadow_ball`: `a_better` (switch_policy, mid)
- `morty_gengar_vs_kadabra_destiny_bond:plan_morty_gengar_vs_kadabra_destiny_bond_attack_now_move_shadow_ball_move_shadow_ball:plan_morty_gengar_vs_kadabra_destiny_bond_switch_preserve_then_rescore_switch_misdreavus_move_shadow_ball`: `a_better` (switch_policy, mid)
- `chuck_poliwrath_vs_pidgeotto_ice_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_switch_preserve_then_rescore_switch_sudowoodo_move_focus_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_attack_now_move_focus_punch_move_focus_punch`: `a_better` (switch_policy, mid)
- `chuck_poliwrath_vs_pidgeotto_ice_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_switch_preserve_then_rescore_switch_sudowoodo_move_focus_punch:plan_chuck_poliwrath_vs_pidgeotto_ice_punch_status_once_then_attack_move_hypnosis_move_focus_punch`: `a_better` (switch_policy, mid)
- `clair_kingdra_vs_lapras_dragon_dance_or_attack:plan_clair_kingdra_vs_lapras_dragon_dance_or_attack_setup_once_then_attack_move_dragon_dance_move_outrage:plan_clair_kingdra_vs_lapras_dragon_dance_or_attack_attack_now_move_outrage_move_outrage`: `a_better` (sequence_policy, mid)
- `erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_attack_now_move_sludge_bomb_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_setup_once_then_attack_move_swords_dance_move_sludge_bomb`: `neither_best_plan_missing` (sequence_policy, mid)
- `erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_attack_now_move_sludge_bomb_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_status_once_then_attack_move_sleep_powder_move_sludge_bomb`: `neither_best_plan_missing` (sequence_policy, mid)
- `erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_attack_now_move_sludge_bomb_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_switch_preserve_then_rescore_switch_exeggutor_move_sludge_bomb`: `neither_best_plan_missing` (sequence_policy, mid)
- `erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_setup_once_then_attack_move_swords_dance_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_status_once_then_attack_move_sleep_powder_move_sludge_bomb`: `neither_best_plan_missing` (sequence_policy, mid)
- `erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_setup_once_then_attack_move_swords_dance_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_switch_preserve_then_rescore_switch_exeggutor_move_sludge_bomb`: `neither_best_plan_missing` (sequence_policy, mid)
- `erika_victreebel_vs_snorlax_sleep_or_boost:plan_erika_victreebel_vs_snorlax_sleep_or_boost_status_once_then_attack_move_sleep_powder_move_sludge_bomb:plan_erika_victreebel_vs_snorlax_sleep_or_boost_switch_preserve_then_rescore_switch_exeggutor_move_sludge_bomb`: `neither_best_plan_missing` (sequence_policy, mid)
- `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_attack_now_move_giga_drain_move_giga_drain:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_status_once_then_attack_move_sleep_powder_move_giga_drain`: `neither_best_plan_missing` (sequence_policy, mid)
- `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_attack_now_move_giga_drain_move_giga_drain:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_switch_preserve_then_rescore_switch_kingdra_move_giga_drain`: `neither_best_plan_missing` (sequence_policy, mid)
- `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_status_once_then_attack_move_sleep_powder_move_giga_drain:plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_switch_preserve_then_rescore_switch_kingdra_move_giga_drain`: `neither_best_plan_missing` (sequence_policy, mid)
