# Boss AI Multi-Turn Plan Queue

Generated: 2026-05-13T09:40:17+00:00
Rollout mode: `deterministic_public_worst_case`

## Summary

- Showing: 20 / 55
- Existing trajectory preferences: 69
- Existing plan demonstrations: 3

## 1. whitney_miltank_vs_geodude_rollout_temptation

- Leader: Whitney
- Phase: `mid`
- Priority: 24
- Teaches: `ace_preservation`, `demo_needs_integration`, `late_resource_policy`, `scout_policy`, `sequence_policy`, `switch_policy`, `tempo`
- Reasons:
  - current scorer has modest uncertainty (margin 8)
  - generated plan cards cover several different plan shapes
  - candidate set includes move-vs-switch preservation
  - candidate set includes hidden-info scout/probe timing
  - old preference notes mention a multi-turn line
  - fixture tags point at a sequence-policy boundary
  - fixture tags point at resource preservation
  - fixture already has high-confidence trajectory feedback
  - human demonstrated a missing plan that still needs integration
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_whitney_miltank_vs_geodude_rollout_temptation_pressure_recover_then_lock_move_body_slam_move_body_slam_move_milk_drink_move_rollout`: Body Slam pressure, heal when needed, then consider Rollout (pressure_recover_then_lock; stops: `target_switches`, `boss_hp_below_35`, `target_can_punish_lock`, `lock_no_longer_changes_ko_math`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_whitney_miltank_vs_geodude_rollout_temptation_attack_now_move_body_slam_move_body_slam`: Body Slam now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_whitney_miltank_vs_geodude_rollout_temptation_scout_probe_then_commit_move_milk_drink_move_body_slam`: Probe with Milk Drink, then commit (scout_probe_then_commit; stops: `threat_revealed`, `boss_hp_below_40`, `target_switches`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_whitney_miltank_vs_geodude_rollout_temptation_switch_preserve_then_rescore_switch_girafarig_move_body_slam`: Switch to Girafarig, then re-score (switch_preserve_then_rescore; stops: `switch_in_bad_fit`, `boss_last_mon`, `plan_goal_reached`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 2. lance_dragonite_vs_suicune_champion_ace

- Leader: Champion Lance
- Phase: `late`
- Priority: 23
- Teaches: `ace_preservation`, `scout_policy`, `sequence_policy`, `switch_policy`, `tempo`
- Reasons:
  - current scorer top two actions are close (margin 0)
  - generated plan cards cover several different plan shapes
  - top candidate set includes setup/status sequencing
  - candidate set includes move-vs-switch preservation
  - old preference notes mention a multi-turn line
  - fixture tags include a hidden coverage or speed boundary
  - fixture tags point at resource preservation
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_lance_dragonite_vs_suicune_champion_ace_attack_now_move_outrage_move_outrage`: Outrage now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_lance_dragonite_vs_suicune_champion_ace_setup_once_then_attack_move_dragon_dance_move_outrage`: Dragon Dance, then Outrage (setup_once_then_attack; stops: `boss_hp_below_35`, `target_switches`, `setup_no_longer_changes_ko_math`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_lance_dragonite_vs_suicune_champion_ace_switch_preserve_then_rescore_switch_kingdra_move_outrage`: Switch to Kingdra, then re-score (switch_preserve_then_rescore; stops: `switch_in_bad_fit`, `boss_last_mon`, `plan_goal_reached`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 3. bugsy_scyther_vs_quilava_fire_pressure

- Leader: Bugsy
- Phase: `early`
- Priority: 21
- Teaches: `sequence_policy`, `switch_policy`, `tempo`, `weight_hint`
- Reasons:
  - current scorer top two actions are close (margin 2)
  - generated plan cards cover several different plan shapes
  - top candidate set includes setup/status sequencing
  - candidate set includes move-vs-switch preservation
  - old preference notes mention a multi-turn line
  - fixture tags point at a sequence-policy boundary
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_bugsy_scyther_vs_quilava_fire_pressure_attack_now_move_wing_attack_move_wing_attack`: Wing Attack now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_bugsy_scyther_vs_quilava_fire_pressure_setup_once_then_attack_move_swords_dance_move_wing_attack`: Swords Dance, then Wing Attack (setup_once_then_attack; stops: `boss_hp_below_35`, `target_switches`, `setup_no_longer_changes_ko_math`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_bugsy_scyther_vs_quilava_fire_pressure_switch_preserve_then_rescore_switch_ledian_move_wing_attack`: Switch to Ledian, then re-score (switch_preserve_then_rescore; stops: `switch_in_bad_fit`, `boss_last_mon`, `plan_goal_reached`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 4. clair_dragonair_vs_suicune_hidden_ice_beam

- Leader: Clair
- Phase: `mid`
- Priority: 21
- Teaches: `ace_preservation`, `scout_policy`, `sequence_policy`, `switch_policy`, `tempo`
- Reasons:
  - current scorer has modest uncertainty (margin 4)
  - existing preference says the compared pair omitted the best action
  - generated plan cards cover several different plan shapes
  - candidate set includes move-vs-switch preservation
  - old preference notes mention a multi-turn line
  - fixture tags include a hidden coverage or speed boundary
  - fixture tags point at resource preservation
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_clair_dragonair_vs_suicune_hidden_ice_beam_attack_now_move_thunder_move_thunder`: Thunder now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_clair_dragonair_vs_suicune_hidden_ice_beam_switch_preserve_then_rescore_switch_kingdra_move_thunder`: Switch to Kingdra, then re-score (switch_preserve_then_rescore; stops: `switch_in_bad_fit`, `boss_last_mon`, `plan_goal_reached`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_clair_dragonair_vs_suicune_hidden_ice_beam_commit_lock_only_if_safe_move_outrage_move_thunder`: Outrage, then Thunder (commit_lock_only_if_safe; stops: `target_resists_lock_move`, `target_can_switch`, `boss_hp_below_40`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 5. falkner_pidgeotto_vs_geodude_rock_risk

- Leader: Falkner
- Phase: `mid`
- Priority: 21
- Teaches: `ace_preservation`, `scout_policy`, `switch_policy`, `tempo`
- Reasons:
  - Falkner is still under-covered
  - generated plan cards cover several different plan shapes
  - candidate set includes move-vs-switch preservation
  - candidate set includes hidden-info scout/probe timing
  - old preference notes mention a multi-turn line
  - fixture tags include a hidden coverage or speed boundary
  - fixture tags point at resource preservation
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_falkner_pidgeotto_vs_geodude_rock_risk_attack_now_move_gust_move_gust`: Gust now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_falkner_pidgeotto_vs_geodude_rock_risk_scout_probe_then_commit_move_sand_attack_move_gust`: Probe with Sand Attack, then commit (scout_probe_then_commit; stops: `threat_revealed`, `boss_hp_below_40`, `target_switches`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_falkner_pidgeotto_vs_geodude_rock_risk_switch_preserve_then_rescore_switch_noctowl_move_gust`: Switch to Noctowl, then re-score (switch_preserve_then_rescore; stops: `switch_in_bad_fit`, `boss_last_mon`, `plan_goal_reached`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 6. lance_yanma_vs_lapras_sleep_powder_or_quiver_dance

- Leader: Champion Lance
- Phase: `mid`
- Priority: 21
- Teaches: `demo_needs_integration`, `hard_rule`, `sequence_policy`, `tempo`
- Reasons:
  - contains 1 rare feature(s) in the current corpus
  - generated plan cards cover several different plan shapes
  - top candidate set includes setup/status sequencing
  - old preference notes mention a multi-turn line
  - fixture tags point at a sequence-policy boundary
  - human demonstrated a missing plan that still needs integration
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_attack_now_move_giga_drain_move_giga_drain`: Giga Drain now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_sleep_then_setup_then_attack_move_sleep_powder_move_quiver_dance_move_giga_drain`: Sleep Powder, then Quiver Dance, then Giga Drain (sleep_then_setup_then_attack; stops: `status_misses`, `target_wakes`, `target_switches`, `sleep_clause_occupied`, `setup_no_longer_changes_ko_math`, `boss_hp_below_35`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_setup_once_then_attack_move_quiver_dance_move_giga_drain`: Quiver Dance, then Giga Drain (setup_once_then_attack; stops: `boss_hp_below_35`, `target_switches`, `setup_no_longer_changes_ko_math`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_lance_yanma_vs_lapras_sleep_powder_or_quiver_dance_status_once_then_attack_move_sleep_powder_move_giga_drain`: Sleep Powder, then Giga Drain (status_once_then_attack; stops: `status_landed`, `target_already_neutralized`, `target_switches`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 7. chuck_poliwrath_vs_pidgeotto_ice_punch

- Leader: Chuck
- Phase: `mid`
- Priority: 20
- Teaches: `sequence_policy`, `switch_policy`, `tempo`, `weight_hint`
- Reasons:
  - current scorer top two actions are close (margin 2)
  - existing preference says the compared pair omitted the best action
  - generated plan cards cover several different plan shapes
  - top candidate set includes setup/status sequencing
  - candidate set includes move-vs-switch preservation
  - fixture tags include a hidden coverage or speed boundary
  - fixture tags point at a sequence-policy boundary
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_chuck_poliwrath_vs_pidgeotto_ice_punch_attack_now_move_focus_punch_move_focus_punch`: Focus Punch now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_chuck_poliwrath_vs_pidgeotto_ice_punch_status_once_then_attack_move_hypnosis_move_focus_punch`: Hypnosis, then Focus Punch (status_once_then_attack; stops: `status_landed`, `target_already_neutralized`, `target_switches`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_chuck_poliwrath_vs_pidgeotto_ice_punch_switch_preserve_then_rescore_switch_sudowoodo_move_focus_punch`: Switch to Sudowoodo, then re-score (switch_preserve_then_rescore; stops: `switch_in_bad_fit`, `boss_last_mon`, `plan_goal_reached`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 8. pryce_slowking_vs_ampharos_ground_pivot

- Leader: Pryce
- Phase: `mid`
- Priority: 19
- Teaches: `late_resource_policy`, `sequence_policy`, `switch_policy`, `tempo`, `weight_hint`
- Reasons:
  - current scorer top two actions are close (margin 2)
  - existing preference says the compared pair omitted the best action
  - generated plan cards cover several different plan shapes
  - candidate set includes move-vs-switch preservation
  - old preference notes mention a multi-turn line
  - fixture tags point at a sequence-policy boundary
  - fixture tags point at resource preservation
  - fixture already has high-confidence trajectory feedback
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_pryce_slowking_vs_ampharos_ground_pivot_attack_now_move_surf_move_surf`: Surf now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_pryce_slowking_vs_ampharos_ground_pivot_speed_control_then_attack_move_thunder_wave_move_surf`: Thunder Wave, then Surf (speed_control_then_attack; stops: `status_landed`, `target_already_neutralized`, `target_switches`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_pryce_slowking_vs_ampharos_ground_pivot_switch_preserve_then_rescore_switch_piloswine_move_surf`: Switch to Piloswine, then re-score (switch_preserve_then_rescore; stops: `switch_in_bad_fit`, `boss_last_mon`, `plan_goal_reached`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_pryce_slowking_vs_ampharos_ground_pivot_recover_until_safe_move_rest_move_surf`: Rest, then Surf (recover_until_safe; stops: `not_outdamaging_player`, `boss_hp_high_enough`, `target_can_setup`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 9. erika_victreebel_vs_snorlax_sleep_or_boost

- Leader: Erika
- Phase: `mid`
- Priority: 18
- Teaches: `demo_needs_integration`, `hard_rule`, `sequence_policy`, `tempo`
- Reasons:
  - current scorer top two actions are close (margin 3)
  - existing row is already high-confidence and typed
  - generated plan cards cover several different plan shapes
  - top candidate set includes setup/status sequencing
  - old preference notes mention a multi-turn line
  - fixture tags point at a sequence-policy boundary
  - fixture already has high-confidence trajectory feedback
  - human demonstrated a missing plan that still needs integration
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_erika_victreebel_vs_snorlax_sleep_or_boost_attack_now_move_sludge_bomb_move_sludge_bomb`: Sludge Bomb now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_erika_victreebel_vs_snorlax_sleep_or_boost_sleep_then_setup_then_attack_move_sleep_powder_move_swords_dance_move_sludge_bomb`: Sleep Powder, then Swords Dance, then Sludge Bomb (sleep_then_setup_then_attack; stops: `status_misses`, `target_wakes`, `target_switches`, `sleep_clause_occupied`, `setup_no_longer_changes_ko_math`, `boss_hp_below_35`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_erika_victreebel_vs_snorlax_sleep_or_boost_setup_once_then_attack_move_swords_dance_move_sludge_bomb`: Swords Dance, then Sludge Bomb (setup_once_then_attack; stops: `boss_hp_below_35`, `target_switches`, `setup_no_longer_changes_ko_math`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_erika_victreebel_vs_snorlax_sleep_or_boost_status_once_then_attack_move_sleep_powder_move_sludge_bomb`: Sleep Powder, then Sludge Bomb (status_once_then_attack; stops: `status_landed`, `target_already_neutralized`, `target_switches`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 10. karen_crobat_vs_dragonite_toxic_or_attack

- Leader: Karen
- Phase: `mid`
- Priority: 17
- Teaches: `sequence_policy`, `switch_policy`, `tempo`, `weight_hint`
- Reasons:
  - current scorer top two actions are close (margin 1)
  - no pairwise preference has been recorded for this comparison
  - generated plan cards cover several different plan shapes
  - top candidate set includes setup/status sequencing
  - candidate set includes move-vs-switch preservation
  - fixture tags point at a sequence-policy boundary
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_karen_crobat_vs_dragonite_toxic_or_attack_attack_now_move_wing_attack_move_wing_attack`: Wing Attack now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_karen_crobat_vs_dragonite_toxic_or_attack_status_once_then_attack_move_toxic_move_wing_attack`: Toxic, then Wing Attack (status_once_then_attack; stops: `status_landed`, `target_already_neutralized`, `target_switches`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_karen_crobat_vs_dragonite_toxic_or_attack_switch_preserve_then_rescore_switch_tyranitar_move_wing_attack`: Switch to Tyranitar, then re-score (switch_preserve_then_rescore; stops: `switch_in_bad_fit`, `boss_last_mon`, `plan_goal_reached`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 11. external_gsc_rhydon_vs_sleeping_snorlax_curse_window

- Leader: External GSC
- Phase: `late`
- Priority: 15
- Teaches: `hard_rule`, `sequence_policy`, `switch_policy`, `tempo`
- Reasons:
  - current scorer has modest uncertainty (margin 5)
  - existing row is already high-confidence and typed
  - generated plan cards cover several different plan shapes
  - top candidate set includes setup/status sequencing
  - candidate set includes move-vs-switch preservation
  - old preference notes mention a multi-turn line
  - fixture tags point at a sequence-policy boundary
  - fixture already has high-confidence trajectory feedback
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_external_gsc_rhydon_vs_sleeping_snorlax_curse_window_attack_now_move_earthquake_move_earthquake`: Earthquake now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_external_gsc_rhydon_vs_sleeping_snorlax_curse_window_setup_once_then_attack_move_curse_move_earthquake`: Curse, then Earthquake (setup_once_then_attack; stops: `boss_hp_below_35`, `target_switches`, `setup_no_longer_changes_ko_math`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_external_gsc_rhydon_vs_sleeping_snorlax_curse_window_switch_preserve_then_rescore_switch_zapdos_move_earthquake`: Switch to Zapdos, then re-score (switch_preserve_then_rescore; stops: `switch_in_bad_fit`, `boss_last_mon`, `plan_goal_reached`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 12. morty_gengar_vs_kadabra_destiny_bond

- Leader: Morty
- Phase: `mid`
- Priority: 15
- Teaches: `mixed_strategy`, `switch_policy`, `tempo`
- Reasons:
  - generated plan cards cover several different plan shapes
  - candidate set includes move-vs-switch preservation
  - candidate set includes a late-game trade or sacrifice line
  - old preference notes mention a multi-turn line
  - fixture tags point at a sequence-policy boundary
  - fixture tags point at resource preservation
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_morty_gengar_vs_kadabra_destiny_bond_attack_now_move_shadow_ball_move_shadow_ball`: Shadow Ball now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_morty_gengar_vs_kadabra_destiny_bond_sacrifice_trade_for_clean_switch_move_destiny_bond_move_shadow_ball`: Destiny Bond for a clean switch (sacrifice_trade_for_clean_switch; stops: `sacrifice_no_longer_profitable`, `boss_has_no_clean_followup`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_morty_gengar_vs_kadabra_destiny_bond_switch_preserve_then_rescore_switch_misdreavus_move_shadow_ball`: Switch to Misdreavus, then re-score (switch_preserve_then_rescore; stops: `switch_in_bad_fit`, `boss_last_mon`, `plan_goal_reached`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 13. morty_misdreavus_vs_typhlosion_perish_song

- Leader: Morty
- Phase: `mid`
- Priority: 15
- Teaches: `sequence_policy`, `switch_policy`, `tempo`
- Reasons:
  - current scorer top two actions are close (margin 3)
  - no pairwise preference has been recorded for this comparison
  - generated plan cards cover several different plan shapes
  - top candidate set includes setup/status sequencing
  - candidate set includes move-vs-switch preservation
  - fixture tags point at resource preservation
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_morty_misdreavus_vs_typhlosion_perish_song_attack_now_move_psywave_move_psywave`: Psywave now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_morty_misdreavus_vs_typhlosion_perish_song_status_once_then_attack_move_confuse_ray_move_psywave`: Confuse Ray, then Psywave (status_once_then_attack; stops: `status_landed`, `target_already_neutralized`, `target_switches`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_morty_misdreavus_vs_typhlosion_perish_song_switch_preserve_then_rescore_switch_gengar_move_psywave`: Switch to Gengar, then re-score (switch_preserve_then_rescore; stops: `switch_in_bad_fit`, `boss_last_mon`, `plan_goal_reached`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 14. whitney_clefairy_vs_bayleef_encore_window

- Leader: Whitney
- Phase: `early`
- Priority: 15
- Teaches: `sequence_policy`, `tempo`, `weight_hint`
- Reasons:
  - current scorer top two actions are close (margin 2)
  - generated plan cards cover several different plan shapes
  - top candidate set includes setup/status sequencing
  - old preference notes mention a multi-turn line
  - fixture tags point at a sequence-policy boundary
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_whitney_clefairy_vs_bayleef_encore_window_attack_now_move_doubleslap_move_doubleslap`: DoubleSlap now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_whitney_clefairy_vs_bayleef_encore_window_setup_once_then_attack_move_double_team_move_doubleslap`: Double Team, then DoubleSlap (setup_once_then_attack; stops: `boss_hp_below_35`, `target_switches`, `setup_no_longer_changes_ko_math`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_whitney_clefairy_vs_bayleef_encore_window_status_once_then_attack_move_encore_move_doubleslap`: Encore, then DoubleSlap (status_once_then_attack; stops: `status_landed`, `target_already_neutralized`, `target_switches`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 15. will_slowbro_vs_houndoom_amnesia_or_surf

- Leader: Will
- Phase: `mid`
- Priority: 15
- Teaches: `ace_preservation`, `sequence_policy`, `switch_policy`, `tempo`
- Reasons:
  - current scorer has modest uncertainty (margin 5)
  - no pairwise preference has been recorded for this comparison
  - candidate set includes move-vs-switch preservation
  - old preference notes mention a multi-turn line
  - fixture tags point at a sequence-policy boundary
  - fixture tags point at resource preservation
  - fixture already has high-confidence trajectory feedback
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_will_slowbro_vs_houndoom_amnesia_or_surf_attack_now_move_surf_move_surf`: Surf now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_will_slowbro_vs_houndoom_amnesia_or_surf_switch_preserve_then_rescore_switch_houndoom_move_surf`: Switch to Houndoom, then re-score (switch_preserve_then_rescore; stops: `switch_in_bad_fit`, `boss_last_mon`, `plan_goal_reached`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 16. clair_kingdra_vs_lapras_dragon_dance_or_attack

- Leader: Clair
- Phase: `mid`
- Priority: 14
- Teaches: `sequence_policy`, `tempo`
- Reasons:
  - current scorer top two actions are close (margin 2)
  - top candidate set includes setup/status sequencing
  - old preference notes mention a multi-turn line
  - fixture tags point at a sequence-policy boundary
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_clair_kingdra_vs_lapras_dragon_dance_or_attack_attack_now_move_outrage_move_outrage`: Outrage now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_clair_kingdra_vs_lapras_dragon_dance_or_attack_setup_once_then_attack_move_dragon_dance_move_outrage`: Dragon Dance, then Outrage (setup_once_then_attack; stops: `boss_hp_below_35`, `target_switches`, `setup_no_longer_changes_ko_math`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 17. jasmine_skarmory_vs_machoke_whirlwind

- Leader: Jasmine
- Phase: `mid`
- Priority: 14
- Teaches: `sequence_policy`, `switch_policy`, `tempo`
- Reasons:
  - current scorer top two actions are close (margin 0)
  - contains 1 rare feature(s) in the current corpus
  - generated plan cards cover several different plan shapes
  - top candidate set includes setup/status sequencing
  - candidate set includes move-vs-switch preservation
  - old preference notes mention a multi-turn line
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_jasmine_skarmory_vs_machoke_whirlwind_attack_now_move_steel_wing_move_steel_wing`: Steel Wing now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_jasmine_skarmory_vs_machoke_whirlwind_status_once_then_attack_move_toxic_move_steel_wing`: Toxic, then Steel Wing (status_once_then_attack; stops: `status_landed`, `target_already_neutralized`, `target_switches`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_jasmine_skarmory_vs_machoke_whirlwind_switch_preserve_then_rescore_switch_forretress_move_steel_wing`: Switch to Forretress, then re-score (switch_preserve_then_rescore; stops: `switch_in_bad_fit`, `boss_last_mon`, `plan_goal_reached`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 18. bugsy_ariados_vs_pidgey_toxic_or_attack

- Leader: Bugsy
- Phase: `early`
- Priority: 13
- Teaches: `sequence_policy`, `switch_policy`, `tempo`, `weight_hint`
- Reasons:
  - current scorer top two actions are close (margin 1)
  - existing row is already high-confidence and typed
  - generated plan cards cover several different plan shapes
  - top candidate set includes setup/status sequencing
  - candidate set includes move-vs-switch preservation
  - fixture tags point at a sequence-policy boundary
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_bugsy_ariados_vs_pidgey_toxic_or_attack_attack_now_move_poison_sting_move_poison_sting`: Poison Sting now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_bugsy_ariados_vs_pidgey_toxic_or_attack_status_once_then_attack_move_toxic_move_poison_sting`: Toxic, then Poison Sting (status_once_then_attack; stops: `status_landed`, `target_already_neutralized`, `target_switches`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_bugsy_ariados_vs_pidgey_toxic_or_attack_switch_preserve_then_rescore_switch_scyther_move_poison_sting`: Switch to Scyther, then re-score (switch_preserve_then_rescore; stops: `switch_in_bad_fit`, `boss_last_mon`, `plan_goal_reached`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 19. bugsy_scyther_vs_geodude_safe_swords_dance

- Leader: Bugsy
- Phase: `early`
- Priority: 13
- Teaches: `sequence_policy`, `switch_policy`, `tempo`
- Reasons:
  - current scorer top two actions are close (margin 1)
  - no pairwise preference has been recorded for this comparison
  - generated plan cards cover several different plan shapes
  - top candidate set includes setup/status sequencing
  - candidate set includes move-vs-switch preservation
  - fixture tags point at a sequence-policy boundary
  - fixture already has high-confidence trajectory feedback
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_bugsy_scyther_vs_geodude_safe_swords_dance_attack_now_move_wing_attack_move_wing_attack`: Wing Attack now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_bugsy_scyther_vs_geodude_safe_swords_dance_setup_once_then_attack_move_swords_dance_move_wing_attack`: Swords Dance, then Wing Attack (setup_once_then_attack; stops: `boss_hp_below_35`, `target_switches`, `setup_no_longer_changes_ko_math`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_bugsy_scyther_vs_geodude_safe_swords_dance_switch_preserve_then_rescore_switch_ariados_move_wing_attack`: Switch to Ariados, then re-score (switch_preserve_then_rescore; stops: `switch_in_bad_fit`, `boss_last_mon`, `plan_goal_reached`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.

## 20. chuck_poliwrath_vs_alakazam_hypnosis_or_ice_punch

- Leader: Chuck
- Phase: `early`
- Priority: 13
- Teaches: `hard_rule`, `sequence_policy`, `switch_policy`, `tempo`
- Reasons:
  - current scorer top two actions are close (margin 1)
  - no pairwise preference has been recorded for this comparison
  - generated plan cards cover several different plan shapes
  - top candidate set includes setup/status sequencing
  - candidate set includes move-vs-switch preservation
  - fixture tags point at a sequence-policy boundary
  - fixture already has high-confidence trajectory feedback
  - similar plan shapes already have trajectory coverage
- Plan cards:
  - `plan_chuck_poliwrath_vs_alakazam_hypnosis_or_ice_punch_attack_now_move_surf_move_surf`: Surf now (attack_now; stops: `target_switches`, `target_faints`, `boss_hp_below_30`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_chuck_poliwrath_vs_alakazam_hypnosis_or_ice_punch_status_once_then_attack_move_hypnosis_move_surf`: Hypnosis, then Surf (status_once_then_attack; stops: `status_landed`, `target_already_neutralized`, `target_switches`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
  - `plan_chuck_poliwrath_vs_alakazam_hypnosis_or_ice_punch_switch_preserve_then_rescore_switch_umbreon_move_surf`: Switch to Umbreon, then re-score (switch_preserve_then_rescore; stops: `switch_in_bad_fit`, `boss_last_mon`, `plan_goal_reached`)
    - Rollout assumptions: Boss-side actions use the fixture's legal boss action list.; Player-side moves are separated into revealed, plausible, impossible, and unknown.; No unrevealed player move is treated as fact.
