# State-Transition Mutation Report

Generated: 2026-05-14T03:34:44+00:00

## Summary

- Mutations: 36
- Passed mutations: 36
- Policy flips: 36
- All mutations pass: `True`
- All mutations flip: `True`
- Families: `['damage_threshold_flip', 'defensive_answer_unavailable', 'direct_removal_absent_sacrifice_trade', 'encore_trap_absent', 'explosion_blocked', 'fast_public_punish_preservation_unavailable', 'fast_public_punish_removed', 'hazard_removal_absent', 'hidden_coverage_absent', 'immediate_ko_threshold_removed', 'lock_move_safe_after_status', 'max_spikes_noop', 'opening_incentive_flip', 'perish_route_survival_removed', 'phazing_order_flip', 'pp_route_pressure_flip', 'preservation_switch_unavailable', 'recovery_window_opens', 'rest_forced_range', 'scout_probe_removed', 'setup_window_removed', 'sleep_clause_occupied', 'sleep_talk_branch_removed', 'sleep_window_removed', 'speed_control_to_direct_ko', 'spinner_revealed', 'status_clock_already_started', 'status_clock_survival_removed', 'target_already_statused', 'weak_setup_signal_to_real_boost']`

## Boundary Mutations

| Mutation | Base | Delta | Expected Flip | Actual Flip | Pass |
| --- | --- | --- | --- | --- | --- |
| `mut_sleep_clause_occupied_blocks_sleep_001` | `vanilla_gsc_sleep_setup_disruption_001` | position_snapshot.field.sleep_clause: free -> occupied | `move_sleep_powder` -> `move_sludge_bomb` | `move_sleep_powder` -> `move_sludge_bomb` | `True` |
| `mut_target_already_statused_blocks_sleep_001` | `vanilla_gsc_sleep_setup_disruption_001` | position_snapshot.opponent_active.status: none -> par | `move_sleep_powder` -> `move_sludge_bomb` | `move_sleep_powder` -> `move_sludge_bomb` | `True` |
| `mut_long_battle_sleep_clause_blocks_rescore_001` | `long_battle_sleep_disruption_after_miss_001` | position_snapshot.field.sleep_clause: free -> occupied | `move_sleep_powder` -> `move_sludge_bomb` | `move_sleep_powder` -> `move_sludge_bomb` | `True` |
| `mut_spikes_layer_2_to_max_001` | `romhack_spikes_third_layer_janine_001` | position_snapshot.field.player_side_spikes_layers: 2 -> 3 | `move_spikes` -> `move_explosion` | `move_spikes` -> `move_explosion` | `True` |
| `mut_spinner_public_lowers_spikes_001` | `fixture_janine_qwilfish_third_spikes_layer_001` | position_snapshot.field.player_rapid_spin_seen: false -> true | `move_spikes` -> `move_explosion` | `move_spikes` -> `move_explosion` | `True` |
| `mut_explosion_blocked_by_protect_001` | `romhack_explosion_route_trade_brock_001` | position_snapshot.opponent_active.revealed_moves: [Surf] -> [Surf, Protect] | `move_explosion` -> `switch_omastar` | `move_explosion` -> `switch_omastar` | `True` |
| `mut_defensive_pivot_unavailable_001` | `romhack_defensive_answer_preservation_pryce_001` | position_snapshot.boss_bench: remove Piloswine | `switch_piloswine` -> `move_thunder_wave` | `switch_piloswine` -> `move_thunder_wave` | `True` |
| `mut_preservation_switch_unavailable_001` | `fixture_chuck_poliwrath_vs_pidgeotto_ice_punch_001` | position_snapshot.boss_bench: remove Sudowoodo | `switch_sudowoodo` -> `move_ice_punch` | `switch_sudowoodo` -> `move_ice_punch` | `True` |
| `mut_long_battle_rest_becomes_forced_001` | `long_battle_rest_tempo_unforced_001` | Snorlax HP 72% -> 32%; immediate punish becomes KO if no Rest | `move_body_slam` -> `move_rest` | `move_body_slam` -> `move_rest` | `True` |
| `mut_spinblock_damage_survival_to_ko_001` | `romhack_spinblock_damage_context_001` | Gengar HP 48% / 67 HP -> 38% / 52 HP; Starmie Psychic 53-63 becomes a guaranteed KO | `move_thunderbolt` -> `switch_raikou` | `move_thunderbolt` -> `switch_raikou` | `True` |
| `mut_phazing_order_faster_to_slower_001` | `vanilla_gsc_phazing_timing_mirror_001` | boss phazer moves before opposing phazer -> boss phazer moves after opposing phazer | `move_rock_slide` -> `move_roar` | `move_rock_slide` -> `move_roar` | `True` |
| `mut_final_phaze_pp_setup_pressure_001` | `vanilla_gsc_pp_phaze_loop_save_final_whirlwind_001` | opponent setup route is contained -> immediate unanswerable setup route | `move_rest` -> `move_whirlwind` | `move_rest` -> `move_whirlwind` | `True` |
| `mut_sleep_window_target_awake_001` | `external_gsc_sleeping_lax_curse_window_001` | Snorlax asleep -> awake and able to punish setup | `move_curse` -> `move_earthquake` | `move_curse` -> `move_earthquake` | `True` |
| `mut_opening_double_switch_to_direct_pressure_001` | `vanilla_gsc_opening_electric_double_switch_spikes_001` | opponent Cloyster likely switches -> opponent Cloyster can stay and set Spikes | `switch_cloyster` -> `move_thunder` | `switch_cloyster` -> `move_thunder` | `True` |
| `mut_external_boom_blocked_by_protect_001` | `external_gsc_forretress_explosion_on_quagsire_001` | Quagsire route target has no public block -> Protect is revealed | `move_explosion` -> `switch_snorlax` | `move_explosion` -> `switch_snorlax` | `True` |
| `mut_restdtalk_branch_absent_setup_window_001` | `external_gsc_vaporeon_vs_restdtalk_snorlax_001` | Sleep Talk Rest branch public -> no Sleep Talk/Rest branch and Growth changes KO math | `move_surf` -> `move_growth` | `move_surf` -> `move_growth` | `True` |
| `mut_late_spin_no_hazards_attack_now_001` | `external_gsc_golem_late_rapid_spin_001` | own side has one Spikes layer -> no own-side hazards | `move_rapid_spin` -> `move_earthquake` | `move_rapid_spin` -> `move_earthquake` | `True` |
| `mut_fast_dark_pivot_unavailable_attack_now_001` | `fixture_will_slowbro_vs_houndoom_fast_dark_001` | position_snapshot.boss_bench: remove Houndoom | `switch_houndoom` -> `move_surf` | `switch_houndoom` -> `move_surf` | `True` |
| `mut_fire_preservation_primary_pivot_unavailable_001` | `fixture_koga_ariados_vs_typhlosion_fire_spikes_001` | position_snapshot.boss_bench: remove Tentacruel | `switch_tentacruel` -> `switch_umbreon` | `switch_tentacruel` -> `switch_umbreon` | `True` |
| `mut_safe_setup_window_removed_by_ko_range_001` | `fixture_bugsy_scyther_vs_geodude_safe_swords_dance_001` | Scyther survives Rock Throw -> Rock Throw is a guaranteed KO after the setup turn | `move_swords_dance` -> `move_wing_attack` | `move_swords_dance` -> `move_wing_attack` | `True` |
| `mut_psychic_pivot_unavailable_sleep_fallback_001` | `fixture_chuck_poliwrath_vs_alakazam_psychic_pivot_001` | position_snapshot.boss_bench: remove Umbreon | `switch_umbreon` -> `move_hypnosis` | `switch_umbreon` -> `move_hypnosis` | `True` |
| `mut_morty_sleep_clause_blocks_hypnosis_001` | `fixture_morty_haunter_vs_noctowl_sleep_line_001` | position_snapshot.field.sleep_clause: free -> occupied | `move_hypnosis` -> `move_night_shade` | `move_hypnosis` -> `move_night_shade` | `True` |
| `mut_falkner_probe_unneeded_attack_now_001` | `fixture_falkner_pidgeotto_vs_geodude_scout_probe_001` | public Rock-risk probe needed -> no meaningful Rock-risk branch | `move_sand_attack` -> `move_gust` | `move_sand_attack` -> `move_gust` | `True` |
| `mut_pryce_cloyster_survives_attack_now_001` | `fixture_pryce_cloyster_vs_quilava_fire_pivot_001` | Cloyster is KOed before progress -> Cloyster survives Flame Wheel and Surf converts | `switch_slowking` -> `move_surf` | `switch_slowking` -> `move_surf` | `True` |
| `mut_bugsy_fire_setup_window_removed_001` | `fixture_bugsy_scyther_vs_quilava_fire_setup_001` | Scyther survives one Ember -> Ember removes the setup route before +2 Wing Attack converts | `move_swords_dance` -> `move_wing_attack` | `move_swords_dance` -> `move_wing_attack` | `True` |
| `mut_whitney_rollout_after_status_001` | `fixture_whitney_miltank_vs_geodude_rollout_lock_001` | Geodude unstatused and Rollout unsafe -> Geodude paralyzed and Rollout safe | `move_body_slam` -> `move_rollout` | `move_body_slam` -> `move_rollout` | `True` |
| `mut_karen_toxic_clock_no_survival_001` | `fixture_karen_crobat_vs_dragonite_toxic_clock_001` | Crobat survives one Outrage after Toxic -> Crobat cannot keep the clock route alive | `move_toxic` -> `switch_tyranitar` | `move_toxic` -> `switch_tyranitar` | `True` |
| `mut_koga_ko_removed_preserve_umbreon_001` | `fixture_koga_crobat_vs_alakazam_immediate_ko_001` | Wing Attack KOs now -> Wing Attack no longer KOs before Psychic/Recover pressure | `move_wing_attack` -> `switch_umbreon` | `move_wing_attack` -> `switch_umbreon` | `True` |
| `mut_jasmine_real_boost_requires_whirlwind_001` | `fixture_jasmine_skarmory_vs_machoke_focus_energy_001` | Focus Energy is low-urgency setup -> Machoke has a real attack-boost route | `move_toxic` -> `move_whirlwind` | `move_toxic` -> `move_whirlwind` | `True` |
| `mut_morty_perish_route_cannot_survive_001` | `fixture_morty_misdreavus_vs_typhlosion_perish_route_001` | Misdreavus survives Flame Wheel to start Perish Song -> Misdreavus is KOed before the clock starts | `move_perish_song` -> `switch_gengar` | `move_perish_song` -> `switch_gengar` | `True` |
| `mut_whitney_encore_trap_absent_double_team_001` | `fixture_whitney_clefairy_vs_bayleef_encore_reflect_001` | Bayleef just used Reflect and Clefairy is faster -> no visible Encore trap | `move_encore` -> `move_double_team` | `move_encore` -> `move_double_team` | `True` |
| `mut_jasmine_speed_control_to_direct_ko_001` | `fixture_jasmine_magneton_vs_quilava_speed_control_001` | Thunderbolt does not KO -> Thunderbolt is public direct removal | `move_thunder_wave` -> `move_thunderbolt` | `move_thunder_wave` -> `move_thunderbolt` | `True` |
| `mut_misty_recovery_window_opens_001` | `fixture_misty_starmie_vs_meganium_recover_tempo_001` | Meganium can immediately punish -> Meganium is asleep and Psychic no longer changes cleanup math | `move_psychic` -> `move_recover` | `move_psychic` -> `move_recover` | `True` |
| `mut_clair_hidden_ice_absent_attack_now_001` | `fixture_clair_dragonair_vs_suicune_hidden_ice_001` | Suicune staying implies hidden Ice pressure -> hidden Ice pressure no longer plausible | `switch_kingdra` -> `move_thunder` | `switch_kingdra` -> `move_thunder` | `True` |
| `mut_bugsy_status_clock_already_started_001` | `fixture_bugsy_ariados_vs_pidgey_status_clock_001` | Pidgey unstatused -> Pidgey already toxic and Ariados has created the clock | `move_toxic` -> `switch_scyther` | `move_toxic` -> `switch_scyther` | `True` |
| `mut_morty_direct_removal_absent_destiny_bond_001` | `fixture_morty_gengar_vs_kadabra_destiny_bond_001` | direct_ko_available: true -> false | `move_shadow_ball` -> `move_destiny_bond` | `move_shadow_ball` -> `move_destiny_bond` | `True` |

## Principles

### `mut_sleep_clause_occupied_blocks_sleep_001`

- Family: `sleep_clause_occupied`
- Principle: sleep control loses when clause state blocks the transition
- Mutated state hash: `sha256:903ce9d769f04be61daa1afcfe5bd26cbec6ceb147349c2d71a9cc0ebe224db7`
- Top mutated candidates:
  - rank 1: `move_sludge_bomb` score `20` (chip is live but does not recreate the setup window)
  - rank 2: `move_sleep_powder` score `-20` (sleep is blocked by clause or existing status; sleep/setup disruption policy recreates the setup window)
  - rank 3: `move_swords_dance` score `-70` (setup follows a disrupted or threatened script; public punish can hit before setup converts)

### `mut_target_already_statused_blocks_sleep_001`

- Family: `target_already_statused`
- Principle: sleep move value collapses when the visible target is already statused
- Mutated state hash: `sha256:ccc055d655a28974d772c3e319f3f4cc9a3956732c3f81f1076e64473a9a8730`
- Top mutated candidates:
  - rank 1: `move_sludge_bomb` score `20` (chip is live but does not recreate the setup window)
  - rank 2: `move_sleep_powder` score `-20` (sleep is blocked by clause or existing status; sleep/setup disruption policy recreates the setup window)
  - rank 3: `move_swords_dance` score `-70` (setup follows a disrupted or threatened script; public punish can hit before setup converts)

### `mut_long_battle_sleep_clause_blocks_rescore_001`

- Family: `sleep_clause_occupied`
- Principle: long-game sleep re-score must abandon sleep if clause state blocks it
- Mutated state hash: `sha256:c5cbe6b9d5e382e4a8aab94757610f7d2179351ae31b75f88e4bd371a495d1a5`
- Top mutated candidates:
  - rank 1: `move_sludge_bomb` score `20` (chip is live but does not recreate the setup window)
  - rank 2: `switch_skarmory` score `0` (no state-transition trigger matched)
  - rank 3: `move_sleep_powder` score `-20` (sleep is blocked by clause or existing status; sleep/setup disruption policy recreates the setup window)

### `mut_spikes_layer_2_to_max_001`

- Family: `max_spikes_noop`
- Principle: max hazard layer no-op dominates the set-Spikes heuristic
- Mutated state hash: `sha256:797de3b8c001940926f3a1f6c8cae8e2f4bb353c57d3d73bff2ee1bcf2445da8`
- Top mutated candidates:
  - rank 1: `move_explosion` score `35` (Explosion remains live after the hazard stack is complete)
  - rank 2: `switch_tentacruel` score `0` (no state-transition trigger matched)
  - rank 3: `move_spikes` score `-100` (local Spikes are already maxed)

### `mut_spinner_public_lowers_spikes_001`

- Family: `spinner_revealed`
- Principle: public removal pressure can dominate finishing the hazard stack
- Mutated state hash: `sha256:01f76cabd6b661fd9d0edcfe54ac6cff9d8b5cea0cf01dbd3ef911a739cac1ff`
- Top mutated candidates:
  - rank 1: `move_explosion` score `30` (Explosion is a possible wall trade but competes with layer completion)
  - rank 2: `move_sludge_bomb` score `10` (direct damage is a live fallback)
  - rank 3: `move_spikes` score `10` (hazards have generic long-game value)

### `mut_explosion_blocked_by_protect_001`

- Family: `explosion_blocked`
- Principle: Explosion route conversion loses to a public block branch
- Mutated state hash: `sha256:a7bb233bd4a92d618984b3448e7a4f17f548bf93e7f73bbebf195747b128e6fa`
- Top mutated candidates:
  - rank 1: `switch_omastar` score `30` (switching preserves material but may miss the trade window)
  - rank 2: `move_explosion` score `-15` (public Protect or Ghost information can blank Explosion; low-future-value attacker can trade for a route)
  - rank 3: `move_curse` score `-35` (public punish can hit before setup converts)

### `mut_defensive_pivot_unavailable_001`

- Family: `defensive_answer_unavailable`
- Principle: preservation cannot choose an unavailable defensive answer
- Mutated state hash: `sha256:6ba765d5f626705d0e3952cb598c637e91c75a849e54c43fc1f5700f23c73ce5`
- Top mutated candidates:
  - rank 1: `move_thunder_wave` score `25` (status helps but does not preserve the answer as cleanly)
  - rank 2: `switch_piloswine` score `-15` (switch target is not available on the public bench; resistant pivot preserves the exposed active piece)
  - rank 3: `move_rest` score `-55` (recovery gives initiative under active pressure)

### `mut_preservation_switch_unavailable_001`

- Family: `preservation_switch_unavailable`
- Principle: switch preservation only dominates when the preserving pivot exists
- Mutated state hash: `sha256:069974325a81c9a7815662abaff8feeeec6e2bc8cd5200ed5e262efcc36b6e10`
- Top mutated candidates:
  - rank 1: `move_ice_punch` score `10` (direct damage is a live fallback)
  - rank 2: `switch_sudowoodo` score `-15` (switch target is not available on the public bench; resistant pivot preserves the exposed active piece)
  - rank 3: `move_focus_punch` score `-50` (Focus Punch is exposed to public attacking pressure; direct damage is a live fallback)

### `mut_long_battle_rest_becomes_forced_001`

- Family: `rest_forced_range`
- Principle: Rest changes from tempo loss to forced role preservation once survival is at stake
- Mutated state hash: `sha256:302f92f946c6462701b7b89ac24ac433695d8fb211d3469f700277fdb93955b3`
- Top mutated candidates:
  - rank 1: `move_rest` score `15` (Rest is forced by low HP role survival; recovery gives initiative under active pressure)
  - rank 2: `move_body_slam` score `10` (direct damage is a live fallback)
  - rank 3: `switch_skarmory` score `0` (no state-transition trigger matched)

### `mut_spinblock_damage_survival_to_ko_001`

- Family: `damage_threshold_flip`
- Principle: spinblocking with an attack only dominates when exact damage evidence says the blocker survives the opponent's fastest punish
- Mutated state hash: `sha256:24e0ee168ad036da4ac4d19131a081709f49bd1833443933bfc92e1789205c76`
- Top mutated candidates:
  - rank 1: `switch_raikou` score `65` (switch preserves material when public damage says the spinblocker is KOed)
  - rank 2: `switch_snorlax` score `65` (switch preserves material when public damage says the spinblocker is KOed)
  - rank 3: `move_thunderbolt` score `-50` (public damage band says the faster punish KOs before the attack; public damage band says the attack removes the spinner; direct damage is a live fallback)

### `mut_phazing_order_faster_to_slower_001`

- Family: `phazing_order_flip`
- Principle: Gen 2 phazing changes answer when move order flips because Roar and Whirlwind must be last to work
- Mutated state hash: `sha256:dc5f54ede5230dc8fefb03302d8e2fa2e0e9ff72e8021363c482045c5c5b6038`
- Top mutated candidates:
  - rank 1: `move_roar` score `90` (Gen 2 phazing works because this phaze action goes last)
  - rank 2: `move_explosion` score `0` (no state-transition trigger matched)
  - rank 3: `switch_suicune` score `0` (no state-transition trigger matched)

### `mut_final_phaze_pp_setup_pressure_001`

- Family: `pp_route_pressure_flip`
- Principle: final phazing PP should be saved unless spending it denies an immediate setup route
- Mutated state hash: `sha256:760ab68c256126ed7b638de0aa761c0f2942b38cbb9f5cb8da7c55f76754b67e`
- Top mutated candidates:
  - rank 1: `move_whirlwind` score `115` (phazing can deny setup when timing is valid; final phazing PP is justified by an immediate setup route)
  - rank 2: `move_toxic` score `15` (status can create future turns)
  - rank 3: `move_rest` score `5` (Rest is forced by low HP role survival; recovery gives the active setup route an unchecked turn)

### `mut_sleep_window_target_awake_001`

- Family: `sleep_window_removed`
- Principle: setup during a sleep window loses priority once the target is awake and can punish immediately
- Mutated state hash: `sha256:90f12a2221b1a564b330e69ef250887aaead9420eee9534effa19a26132ed044`
- Top mutated candidates:
  - rank 1: `move_earthquake` score `80` (immediate attack is preferred once the sleep setup window is gone; Earthquake is the grounded active-target attack; direct damage is a live fallback)
  - rank 2: `move_rock_slide` score `40` (immediate attack is preferred once the sleep setup window is gone; Rock Slide mainly covers a switch read rather than the grounded active target; direct damage is a live fallback)
  - rank 3: `switch_zapdos` score `0` (no state-transition trigger matched)

### `mut_opening_double_switch_to_direct_pressure_001`

- Family: `opening_incentive_flip`
- Principle: opening double-switches are resource bids that lose to direct pressure when the opponent no longer has the switch incentive
- Mutated state hash: `sha256:4f927477a7e28171e2f2739e3bd56f6d5532534b310e02c607c479035f23ba7a`
- Top mutated candidates:
  - rank 1: `move_thunder` score `90` (direct Thunder pressure stops the Spiker from claiming the opening; direct damage is a live fallback)
  - rank 2: `move_roar` score `10` (phazing can deny setup when timing is valid; opening phazing is lower value when direct pressure is required)
  - rank 3: `switch_cloyster` score `-70` (double-switch loses value when the opponent can stay and claim hazards)

### `mut_external_boom_blocked_by_protect_001`

- Family: `explosion_blocked`
- Principle: real replay Explosion conversion loses to a public block branch even when the original route trade was correct
- Mutated state hash: `sha256:85ab19e236aff7c92dd4d9a4f5a7e629e948a71222e32fcf48605620b8694eb6`
- Top mutated candidates:
  - rank 1: `switch_snorlax` score `30` (switching preserves material but may miss the trade window)
  - rank 2: `move_toxic` score `15` (status can create future turns)
  - rank 3: `move_hidden_power` score `10` (direct damage is a live fallback)

### `mut_restdtalk_branch_absent_setup_window_001`

- Family: `sleep_talk_branch_removed`
- Principle: attacking a sleeping RestTalk user dominates greed, but setup can dominate when the public RestTalk catastrophe branch is absent and setup changes KO math
- Mutated state hash: `sha256:c332952308284c485a0655552af7bcdf03a17f9de6df80248f84bb7a0184109f`
- Top mutated candidates:
  - rank 1: `move_growth` score `50` (setup uses a live sleep window to change endgame KO math; public punish can hit before setup converts)
  - rank 2: `switch_raikou` score `0` (no state-transition trigger matched)
  - rank 3: `move_surf` score `-10` (immediate attack fails to use the sleep window's setup conversion; direct damage is a live fallback)

### `mut_late_spin_no_hazards_attack_now_001`

- Family: `hazard_removal_absent`
- Principle: late-game Rapid Spin is a route-preservation move only while hazards still tax future switches
- Mutated state hash: `sha256:bdf09b6e19f2e6851fcc23c7a72f026fee86e431f9e5de74ccb27d8f017ce353`
- Top mutated candidates:
  - rank 1: `move_earthquake` score `65` (direct pressure dominates once there are no own-side hazards to remove; direct damage is a live fallback)
  - rank 2: `move_roar` score `20` (phazing can deny setup when timing is valid)
  - rank 3: `move_explosion` score `0` (no state-transition trigger matched)

### `mut_fast_dark_pivot_unavailable_attack_now_001`

- Family: `fast_public_punish_preservation_unavailable`
- Principle: fast public punish preservation flips to the best stay-in attack only when the preserving pivot is unavailable
- Mutated state hash: `sha256:6747a9c8ed6ebd4199d4a8da6cad623d7b04cf3f146f94db6859bc6ad20e4c67`
- Top mutated candidates:
  - rank 1: `move_surf` score `45` (this is the best fallback attack if the preservation pivot is unavailable; direct damage is a live fallback)
  - rank 2: `move_psychic` score `10` (direct damage is a live fallback)
  - rank 3: `switch_houndoom` score `-15` (switch target is not available on the public bench; resistant pivot preserves the exposed active piece)

### `mut_fire_preservation_primary_pivot_unavailable_001`

- Family: `fast_public_punish_preservation_unavailable`
- Principle: lethal public Fire pressure still demands preservation, but the best preserving pivot changes when the primary answer is unavailable
- Mutated state hash: `sha256:8630d8d253fa4def4d446610746e6e19be309617558a0004d4e8c7669d9af616`
- Top mutated candidates:
  - rank 1: `switch_umbreon` score `85` (resistant pivot preserves the exposed active piece)
  - rank 2: `move_toxic` score `25` (status helps but does not preserve the answer as cleanly)
  - rank 3: `move_leech_life` score `10` (direct damage is a live fallback)

### `mut_safe_setup_window_removed_by_ko_range_001`

- Family: `setup_window_removed`
- Principle: setup is correct only while the worst plausible punish leaves the boosted route alive
- Mutated state hash: `sha256:62ef7462f0f7bb2c34fb1e4530d360af0594fd32d81746842689f451e9046a5e`
- Top mutated candidates:
  - rank 1: `move_wing_attack` score `65` (this is the best fallback attack once setup no longer survives the public punish; direct damage is a live fallback)
  - rank 2: `move_quick_attack` score `10` (direct damage is a live fallback)
  - rank 3: `switch_ariados` score `0` (no state-transition trigger matched)

### `mut_psychic_pivot_unavailable_sleep_fallback_001`

- Family: `defensive_answer_unavailable`
- Principle: accuracy-dependent sleep becomes the fallback control line only when the clean Psychic pivot is unavailable
- Mutated state hash: `sha256:920801e28e8e16196655c995ecb19d0d394a3aec46043d4401e86dd49dcb05a0`
- Top mutated candidates:
  - rank 1: `move_hypnosis` score `35` (sleep is legal into an unstatused target)
  - rank 2: `move_ice_punch` score `10` (direct damage is a live fallback)
  - rank 3: `move_surf` score `10` (direct damage is a live fallback)

### `mut_morty_sleep_clause_blocks_hypnosis_001`

- Family: `sleep_clause_occupied`
- Principle: sleep pressure is a route only while Sleep Clause and target status make it legal
- Mutated state hash: `sha256:f498b01fc5f13171af5973f77ca9f67d53d23220ddd2309e76992abc34e3fff5`
- Top mutated candidates:
  - rank 1: `move_night_shade` score `10` (direct damage is a live fallback)
  - rank 2: `move_curse` score `0` (no state-transition trigger matched)
  - rank 3: `switch_gengar` score `0` (no state-transition trigger matched)

### `mut_falkner_probe_unneeded_attack_now_001`

- Family: `scout_probe_removed`
- Principle: scout or accuracy probes need a live punish branch; otherwise the policy should take direct progress
- Mutated state hash: `sha256:842355a7812979b985e3ef92fc6a3418b07606cbf24bc8c05daf8f67fae500e8`
- Top mutated candidates:
  - rank 1: `move_gust` score `65` (direct progress is preferred once the scout probe has no live punish to reduce; direct damage is a live fallback)
  - rank 2: `switch_noctowl` score `0` (no state-transition trigger matched)
  - rank 3: `move_sand_attack` score `-60` (scout probe is low value without a live public punish branch)

### `mut_pryce_cloyster_survives_attack_now_001`

- Family: `fast_public_punish_removed`
- Principle: switching out of a bad matchup dominates while the active faints before progress, but direct attack takes over once survival evidence makes the route immediate
- Mutated state hash: `sha256:0cb69169478e2656e2f998e317a2e084c83da848ecbe17e97a665ee6a47f1a08`
- Top mutated candidates:
  - rank 1: `move_surf` score `90` (direct attack is preferred once survival evidence makes the route immediate; direct damage is a live fallback)
  - rank 2: `switch_slowking` score `10` (resistant pivot preserves the exposed active piece; switching loses priority once the active survives and can convert directly)
  - rank 3: `move_protect` score `-25` (Protect is lower value once direct progress is safe)

### `mut_bugsy_fire_setup_window_removed_001`

- Family: `setup_window_removed`
- Principle: setup under public Fire pressure is correct only while speed, survival, and boosted damage preserve the two-turn route
- Mutated state hash: `sha256:cb628e5d81e473e9d472026ab1520c1ee4d11e9cdb474c700d5493815de3156d`
- Top mutated candidates:
  - rank 1: `move_wing_attack` score `65` (this is the best fallback attack once setup no longer survives the public punish; direct damage is a live fallback)
  - rank 2: `move_quick_attack` score `10` (direct damage is a live fallback)
  - rank 3: `switch_ledian` score `0` (no state-transition trigger matched)

### `mut_whitney_rollout_after_status_001`

- Family: `lock_move_safe_after_status`
- Principle: lock moves are route conversions only after status or safety changes the board
- Mutated state hash: `sha256:7ecfd9f75f29e5e2f64d670f44f4d3c50dfba95ca365bb1f7ccaba7ddad9cfef`
- Top mutated candidates:
  - rank 1: `move_rollout` score `90` (lock move is now safe because status or board state changed the route)
  - rank 2: `move_body_slam` score `20` (status pressure is still useful but the lock conversion is now live; direct damage is a live fallback)
  - rank 3: `switch_girafarig` score `0` (no state-transition trigger matched)

### `mut_karen_toxic_clock_no_survival_001`

- Family: `status_clock_survival_removed`
- Principle: a Toxic clock is only the first move when the user survives the immediate route punish or the sacrifice is explicitly justified
- Mutated state hash: `sha256:e762e8dd6fb02046ff32ec43512cbeddcb0028304d45b06d0bfd6dd4bc793a62`
- Top mutated candidates:
  - rank 1: `switch_tyranitar` score `90` (pivot becomes the route once the status user cannot survive the immediate punish)
  - rank 2: `move_confuse_ray` score `-35` (direct attack is low-impact and does not improve the status-clock route; direct damage is a live fallback)
  - rank 3: `move_wing_attack` score `-35` (direct attack is low-impact and does not improve the status-clock route; direct damage is a live fallback)

### `mut_koga_ko_removed_preserve_umbreon_001`

- Family: `immediate_ko_threshold_removed`
- Principle: direct KO damage dominates slow status, but preservation takes over once the KO threshold disappears
- Mutated state hash: `sha256:a36942da8788ff083d3e566de166dacd7ad74a8e0b0b5070192cd5761414539d`
- Top mutated candidates:
  - rank 1: `switch_umbreon` score `90` (pivot becomes the route once direct KO damage is unavailable)
  - rank 2: `move_confuse_ray` score `10` (direct damage is a live fallback)
  - rank 3: `move_wing_attack` score `-30` (direct attack loses priority once it no longer reaches the KO threshold; direct damage is a live fallback)

### `mut_jasmine_real_boost_requires_whirlwind_001`

- Family: `weak_setup_signal_to_real_boost`
- Principle: phazing dominates status only when the setup route is dangerous enough to deny now
- Mutated state hash: `sha256:2299209921010a4dbcdab6e7834b0dcf606dbab496bf16bd4809f81b2d52726d`
- Top mutated candidates:
  - rank 1: `move_whirlwind` score `115` (phazing can deny setup when timing is valid; phazing is required because the public setup route is immediately dangerous)
  - rank 2: `move_toxic` score `40` (status clock is live because the target is unstatused and the user survives the immediate punish; status is too slow when a real boost route must be phazed now; status can create future turns)
  - rank 3: `move_steel_wing` score `10` (direct damage is a live fallback)

### `mut_morty_perish_route_cannot_survive_001`

- Family: `perish_route_survival_removed`
- Principle: Perish Song is a route only if the user can survive long enough to start the countdown
- Mutated state hash: `sha256:bf70c15ca24b7a682f2da11e69d841bad2bc6ee59fd3941bde9f1b38a0db4422`
- Top mutated candidates:
  - rank 1: `switch_gengar` score `90` (pivot becomes the route once Perish Song cannot survive the immediate punish)
  - rank 2: `move_confuse_ray` score `-30` (direct or swing damage is lower value than starting the forced Perish clock; direct damage is a live fallback)
  - rank 3: `move_psywave` score `-30` (direct or swing damage is lower value than starting the forced Perish clock; direct damage is a live fallback)

### `mut_whitney_encore_trap_absent_double_team_001`

- Family: `encore_trap_absent`
- Principle: Encore is a must-click only with public last-move and speed evidence; otherwise safe one-turn setup can dominate
- Mutated state hash: `sha256:3427a817fff01b79e267120d91b69bb004c65f28735606fb975fbf8959ad9dae`
- Top mutated candidates:
  - rank 1: `move_double_team` score `85` (one setup turn becomes best when the visible Encore trap is absent)
  - rank 2: `move_thunder_wave` score `15` (status can create future turns)
  - rank 3: `move_doubleslap` score `10` (direct damage is a live fallback)

### `mut_jasmine_speed_control_to_direct_ko_001`

- Family: `speed_control_to_direct_ko`
- Principle: Speed-control status is correct only while it creates future turns; public direct removal dominates once it is available
- Mutated state hash: `sha256:baca0ea1baa75659b0c658152af5c610ce070fa6d74e3cadffd302f5140a90eb`
- Top mutated candidates:
  - rank 1: `move_thunderbolt` score `70` (direct attack removes the threat before slow status or preservation is needed; direct attack is low-impact and does not improve the status-clock route; direct damage is a live fallback)
  - rank 2: `move_thunder_wave` score `25` (status clock is live because the target is unstatused and the user survives the immediate punish; slow status loses to an immediate KO route; status can create future turns)
  - rank 3: `switch_steelix` score `0` (no state-transition trigger matched)

### `mut_misty_recovery_window_opens_001`

- Family: `recovery_window_opens`
- Principle: Reliable recovery is correct only when a real window opens and recovery preserves a route better than immediate progress
- Mutated state hash: `sha256:f49765e11cbd5369b84898e58f2bfc81441723037843412e6e102c940b9ef7d8`
- Top mutated candidates:
  - rank 1: `move_recover` score `90` (recovery has a real public window and preserves the route)
  - rank 2: `switch_lapras` score `0` (no state-transition trigger matched)
  - rank 3: `move_hydro_pump` score `-10` (non-tempo attack misses the named progress route; direct damage is a live fallback)

### `mut_clair_hidden_ice_absent_attack_now_001`

- Family: `hidden_coverage_absent`
- Principle: Hidden-info preservation dominates only while the punish is legal, plausible, and severe enough to change the route
- Mutated state hash: `sha256:e0a5e6c079f0024a92a28ddf35444b8625b7735c36639e7e0ec8467c08b62c07`
- Top mutated candidates:
  - rank 1: `move_thunder` score `95` (direct attack becomes best once the severe hidden-coverage branch is absent; direct damage is a live fallback)
  - rank 2: `switch_kingdra` score `-45` (primary hidden-coverage pivot loses value once the punish is absent)
  - rank 3: `switch_mantine` score `-50` (fallback hidden-coverage pivot is too passive once the punish is absent)

### `mut_bugsy_status_clock_already_started_001`

- Family: `status_clock_already_started`
- Principle: Status clock policy is not repeated status: once the clock exists, re-score the follow-up route
- Mutated state hash: `sha256:c28e82720fb0f83ade766e68efa44ce7697344754053c62179cd9d913eeea9f8`
- Top mutated candidates:
  - rank 1: `switch_scyther` score `90` (pivot becomes the route once the status user cannot survive the immediate punish)
  - rank 2: `move_giga_drain` score `-35` (direct attack is low-impact and does not improve the status-clock route; direct damage is a live fallback)
  - rank 3: `move_leech_life` score `-35` (direct attack is low-impact and does not improve the status-clock route; direct damage is a live fallback)

### `mut_morty_direct_removal_absent_destiny_bond_001`

- Family: `direct_removal_absent_sacrifice_trade`
- Principle: Sacrifice trade becomes correct only after direct removal no longer converts the route
- Mutated state hash: `sha256:281f3677caa120004c4edcc2a2b67643bcf62fe286bf0ac2c8076bf3535e1718`
- Top mutated candidates:
  - rank 1: `move_destiny_bond` score `100` (sacrifice trade is forced because direct removal no longer converts)
  - rank 2: `switch_misdreavus` score `0` (no state-transition trigger matched)
  - rank 3: `move_shadow_ball` score `-30` (direct attack loses priority once it no longer reaches the KO threshold; direct damage is a live fallback)
