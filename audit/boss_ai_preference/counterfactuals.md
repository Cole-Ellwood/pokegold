# Boss AI Counterfactual Fixture Families

Generated: 2026-05-12T10:56:58+00:00
Dry run: true

Generated 60 fixture variant(s).

## falkner_pidgeotto_vs_geodude_rock_risk__cf_coverage_plausible

- Parent: `falkner_pidgeotto_vs_geodude_rock_risk`
- Template: `hidden_coverage`
- Group: `falkner_pidgeotto_vs_geodude_rock_risk__hidden_coverage`
- Rationale: Tests whether scouting beats greedy setup when a coverage threat is plausible.
- Changed fields: `{"state.player.active.public_priors": "hidden coverage plausible from public learnset"}`

## falkner_pidgeotto_vs_geodude_rock_risk__cf_coverage_revealed

- Parent: `falkner_pidgeotto_vs_geodude_rock_risk`
- Template: `hidden_coverage`
- Group: `falkner_pidgeotto_vs_geodude_rock_risk__hidden_coverage`
- Rationale: Tests hard respect for a now-public coverage threat.
- Changed fields: `{"state.player.active.public_priors": "coverage threat revealed"}`

## falkner_pidgeotto_vs_geodude_rock_risk__cf_coverage_blocked

- Parent: `falkner_pidgeotto_vs_geodude_rock_risk`
- Template: `hidden_coverage`
- Group: `falkner_pidgeotto_vs_geodude_rock_risk__hidden_coverage`
- Rationale: Tests that the AI stops respecting impossible hidden coverage.
- Changed fields: `{"state.player.active.public_priors": "coverage blocked by four revealed non-coverage moves"}`

## falkner_pidgeotto_vs_geodude_rock_risk__cf_safe_switch

- Parent: `falkner_pidgeotto_vs_geodude_rock_risk`
- Template: `switch_fit`
- Group: `falkner_pidgeotto_vs_geodude_rock_risk__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "safe switch-in absorbs the public hit"}`

## falkner_pidgeotto_vs_geodude_rock_risk__cf_risky_switch

- Parent: `falkner_pidgeotto_vs_geodude_rock_risk`
- Template: `switch_fit`
- Group: `falkner_pidgeotto_vs_geodude_rock_risk__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "risky switch-in takes meaningful chip"}`

## falkner_pidgeotto_vs_geodude_rock_risk__cf_bad_switch

- Parent: `falkner_pidgeotto_vs_geodude_rock_risk`
- Template: `switch_fit`
- Group: `falkner_pidgeotto_vs_geodude_rock_risk__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "bad switch-in loses to the same public threat"}`

## bugsy_scyther_vs_quilava_fire_pressure__cf_hp_ko_range

- Parent: `bugsy_scyther_vs_quilava_fire_pressure`
- Template: `hp_threshold`
- Group: `bugsy_scyther_vs_quilava_fire_pressure__hp_threshold`
- Rationale: Tests whether immediate KO pressure should dominate setup or status.
- Changed fields: `{"state.player.active.hp": "18%"}`

## bugsy_scyther_vs_quilava_fire_pressure__cf_hp_2hko_range

- Parent: `bugsy_scyther_vs_quilava_fire_pressure`
- Template: `hp_threshold`
- Group: `bugsy_scyther_vs_quilava_fire_pressure__hp_threshold`
- Rationale: Tests the boundary where chip may set up a teammate but not end the turn.
- Changed fields: `{"state.player.active.hp": "54%"}`

## bugsy_scyther_vs_quilava_fire_pressure__cf_hp_comfortable

- Parent: `bugsy_scyther_vs_quilava_fire_pressure`
- Template: `hp_threshold`
- Group: `bugsy_scyther_vs_quilava_fire_pressure__hp_threshold`
- Rationale: Tests whether slow plans are acceptable when the target is healthy.
- Changed fields: `{"state.player.active.hp": "88%"}`

## bugsy_scyther_vs_quilava_fire_pressure__cf_boss_faster

- Parent: `bugsy_scyther_vs_quilava_fire_pressure`
- Template: `speed_boundary`
- Group: `bugsy_scyther_vs_quilava_fire_pressure__speed_boundary`
- Rationale: Tests setup and revenge-kill judgments around known turn order.
- Changed fields: `{"state.public_notes": "boss is publicly observed faster"}`

## bugsy_scyther_vs_quilava_fire_pressure__cf_player_faster

- Parent: `bugsy_scyther_vs_quilava_fire_pressure`
- Template: `speed_boundary`
- Group: `bugsy_scyther_vs_quilava_fire_pressure__speed_boundary`
- Rationale: Tests setup and revenge-kill judgments around known turn order.
- Changed fields: `{"state.public_notes": "player is publicly observed faster"}`

## bugsy_scyther_vs_quilava_fire_pressure__cf_speed_unknown

- Parent: `bugsy_scyther_vs_quilava_fire_pressure`
- Template: `speed_boundary`
- Group: `bugsy_scyther_vs_quilava_fire_pressure__speed_boundary`
- Rationale: Tests setup and revenge-kill judgments around known turn order.
- Changed fields: `{"state.public_notes": "turn order is not yet observed"}`

## whitney_miltank_vs_geodude_rollout_temptation__cf_hp_ko_range

- Parent: `whitney_miltank_vs_geodude_rollout_temptation`
- Template: `hp_threshold`
- Group: `whitney_miltank_vs_geodude_rollout_temptation__hp_threshold`
- Rationale: Tests whether immediate KO pressure should dominate setup or status.
- Changed fields: `{"state.player.active.hp": "18%"}`

## whitney_miltank_vs_geodude_rollout_temptation__cf_hp_2hko_range

- Parent: `whitney_miltank_vs_geodude_rollout_temptation`
- Template: `hp_threshold`
- Group: `whitney_miltank_vs_geodude_rollout_temptation__hp_threshold`
- Rationale: Tests the boundary where chip may set up a teammate but not end the turn.
- Changed fields: `{"state.player.active.hp": "54%"}`

## whitney_miltank_vs_geodude_rollout_temptation__cf_hp_comfortable

- Parent: `whitney_miltank_vs_geodude_rollout_temptation`
- Template: `hp_threshold`
- Group: `whitney_miltank_vs_geodude_rollout_temptation__hp_threshold`
- Rationale: Tests whether slow plans are acceptable when the target is healthy.
- Changed fields: `{"state.player.active.hp": "88%"}`

## whitney_miltank_vs_geodude_rollout_temptation__cf_boss_faster

- Parent: `whitney_miltank_vs_geodude_rollout_temptation`
- Template: `speed_boundary`
- Group: `whitney_miltank_vs_geodude_rollout_temptation__speed_boundary`
- Rationale: Tests setup and revenge-kill judgments around known turn order.
- Changed fields: `{"state.public_notes": "boss is publicly observed faster"}`

## whitney_miltank_vs_geodude_rollout_temptation__cf_player_faster

- Parent: `whitney_miltank_vs_geodude_rollout_temptation`
- Template: `speed_boundary`
- Group: `whitney_miltank_vs_geodude_rollout_temptation__speed_boundary`
- Rationale: Tests setup and revenge-kill judgments around known turn order.
- Changed fields: `{"state.public_notes": "player is publicly observed faster"}`

## whitney_miltank_vs_geodude_rollout_temptation__cf_speed_unknown

- Parent: `whitney_miltank_vs_geodude_rollout_temptation`
- Template: `speed_boundary`
- Group: `whitney_miltank_vs_geodude_rollout_temptation__speed_boundary`
- Rationale: Tests setup and revenge-kill judgments around known turn order.
- Changed fields: `{"state.public_notes": "turn order is not yet observed"}`

## whitney_miltank_vs_geodude_rollout_temptation__cf_safe_switch

- Parent: `whitney_miltank_vs_geodude_rollout_temptation`
- Template: `switch_fit`
- Group: `whitney_miltank_vs_geodude_rollout_temptation__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "safe switch-in absorbs the public hit"}`

## whitney_miltank_vs_geodude_rollout_temptation__cf_risky_switch

- Parent: `whitney_miltank_vs_geodude_rollout_temptation`
- Template: `switch_fit`
- Group: `whitney_miltank_vs_geodude_rollout_temptation__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "risky switch-in takes meaningful chip"}`

## whitney_miltank_vs_geodude_rollout_temptation__cf_bad_switch

- Parent: `whitney_miltank_vs_geodude_rollout_temptation`
- Template: `switch_fit`
- Group: `whitney_miltank_vs_geodude_rollout_temptation__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "bad switch-in loses to the same public threat"}`

## whitney_clefairy_vs_bayleef_encore_window__cf_target_paralyzed

- Parent: `whitney_clefairy_vs_bayleef_encore_window`
- Template: `status_aftermath`
- Group: `whitney_clefairy_vs_bayleef_encore_window__status_aftermath`
- Rationale: Tests whether status moves are legal, useful, or redundant after public status changes.
- Changed fields: `{"state.player.active.status": "paralyzed"}`

## whitney_clefairy_vs_bayleef_encore_window__cf_target_asleep

- Parent: `whitney_clefairy_vs_bayleef_encore_window`
- Template: `status_aftermath`
- Group: `whitney_clefairy_vs_bayleef_encore_window__status_aftermath`
- Rationale: Tests whether status moves are legal, useful, or redundant after public status changes.
- Changed fields: `{"state.player.active.status": "asleep"}`

## whitney_clefairy_vs_bayleef_encore_window__cf_sleep_clause_occupied

- Parent: `whitney_clefairy_vs_bayleef_encore_window`
- Template: `status_aftermath`
- Group: `whitney_clefairy_vs_bayleef_encore_window__status_aftermath`
- Rationale: Tests whether status moves are legal, useful, or redundant after public status changes.
- Changed fields: `{"state.player.active.status": "none"}`

## whitney_clefairy_vs_bayleef_encore_window__cf_safe_switch

- Parent: `whitney_clefairy_vs_bayleef_encore_window`
- Template: `switch_fit`
- Group: `whitney_clefairy_vs_bayleef_encore_window__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "safe switch-in absorbs the public hit"}`

## whitney_clefairy_vs_bayleef_encore_window__cf_risky_switch

- Parent: `whitney_clefairy_vs_bayleef_encore_window`
- Template: `switch_fit`
- Group: `whitney_clefairy_vs_bayleef_encore_window__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "risky switch-in takes meaningful chip"}`

## whitney_clefairy_vs_bayleef_encore_window__cf_bad_switch

- Parent: `whitney_clefairy_vs_bayleef_encore_window`
- Template: `switch_fit`
- Group: `whitney_clefairy_vs_bayleef_encore_window__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "bad switch-in loses to the same public threat"}`

## morty_gengar_vs_kadabra_destiny_bond__cf_target_paralyzed

- Parent: `morty_gengar_vs_kadabra_destiny_bond`
- Template: `status_aftermath`
- Group: `morty_gengar_vs_kadabra_destiny_bond__status_aftermath`
- Rationale: Tests whether status moves are legal, useful, or redundant after public status changes.
- Changed fields: `{"state.player.active.status": "paralyzed"}`

## morty_gengar_vs_kadabra_destiny_bond__cf_target_asleep

- Parent: `morty_gengar_vs_kadabra_destiny_bond`
- Template: `status_aftermath`
- Group: `morty_gengar_vs_kadabra_destiny_bond__status_aftermath`
- Rationale: Tests whether status moves are legal, useful, or redundant after public status changes.
- Changed fields: `{"state.player.active.status": "asleep"}`

## morty_gengar_vs_kadabra_destiny_bond__cf_sleep_clause_occupied

- Parent: `morty_gengar_vs_kadabra_destiny_bond`
- Template: `status_aftermath`
- Group: `morty_gengar_vs_kadabra_destiny_bond__status_aftermath`
- Rationale: Tests whether status moves are legal, useful, or redundant after public status changes.
- Changed fields: `{"state.player.active.status": "none"}`

## morty_gengar_vs_kadabra_destiny_bond__cf_safe_switch

- Parent: `morty_gengar_vs_kadabra_destiny_bond`
- Template: `switch_fit`
- Group: `morty_gengar_vs_kadabra_destiny_bond__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "safe switch-in absorbs the public hit"}`

## morty_gengar_vs_kadabra_destiny_bond__cf_risky_switch

- Parent: `morty_gengar_vs_kadabra_destiny_bond`
- Template: `switch_fit`
- Group: `morty_gengar_vs_kadabra_destiny_bond__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "risky switch-in takes meaningful chip"}`

## morty_gengar_vs_kadabra_destiny_bond__cf_bad_switch

- Parent: `morty_gengar_vs_kadabra_destiny_bond`
- Template: `switch_fit`
- Group: `morty_gengar_vs_kadabra_destiny_bond__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "bad switch-in loses to the same public threat"}`

## morty_haunter_vs_noctowl_sleep_line__cf_target_paralyzed

- Parent: `morty_haunter_vs_noctowl_sleep_line`
- Template: `status_aftermath`
- Group: `morty_haunter_vs_noctowl_sleep_line__status_aftermath`
- Rationale: Tests whether status moves are legal, useful, or redundant after public status changes.
- Changed fields: `{"state.player.active.status": "paralyzed"}`

## morty_haunter_vs_noctowl_sleep_line__cf_target_asleep

- Parent: `morty_haunter_vs_noctowl_sleep_line`
- Template: `status_aftermath`
- Group: `morty_haunter_vs_noctowl_sleep_line__status_aftermath`
- Rationale: Tests whether status moves are legal, useful, or redundant after public status changes.
- Changed fields: `{"state.player.active.status": "asleep"}`

## morty_haunter_vs_noctowl_sleep_line__cf_sleep_clause_occupied

- Parent: `morty_haunter_vs_noctowl_sleep_line`
- Template: `status_aftermath`
- Group: `morty_haunter_vs_noctowl_sleep_line__status_aftermath`
- Rationale: Tests whether status moves are legal, useful, or redundant after public status changes.
- Changed fields: `{"state.player.active.status": "none"}`

## chuck_poliwrath_vs_pidgeotto_ice_punch__cf_coverage_plausible

- Parent: `chuck_poliwrath_vs_pidgeotto_ice_punch`
- Template: `hidden_coverage`
- Group: `chuck_poliwrath_vs_pidgeotto_ice_punch__hidden_coverage`
- Rationale: Tests whether scouting beats greedy setup when a coverage threat is plausible.
- Changed fields: `{"state.player.active.public_priors": "hidden coverage plausible from public learnset"}`

## chuck_poliwrath_vs_pidgeotto_ice_punch__cf_coverage_revealed

- Parent: `chuck_poliwrath_vs_pidgeotto_ice_punch`
- Template: `hidden_coverage`
- Group: `chuck_poliwrath_vs_pidgeotto_ice_punch__hidden_coverage`
- Rationale: Tests hard respect for a now-public coverage threat.
- Changed fields: `{"state.player.active.public_priors": "coverage threat revealed"}`

## chuck_poliwrath_vs_pidgeotto_ice_punch__cf_coverage_blocked

- Parent: `chuck_poliwrath_vs_pidgeotto_ice_punch`
- Template: `hidden_coverage`
- Group: `chuck_poliwrath_vs_pidgeotto_ice_punch__hidden_coverage`
- Rationale: Tests that the AI stops respecting impossible hidden coverage.
- Changed fields: `{"state.player.active.public_priors": "coverage blocked by four revealed non-coverage moves"}`

## chuck_poliwrath_vs_pidgeotto_ice_punch__cf_target_paralyzed

- Parent: `chuck_poliwrath_vs_pidgeotto_ice_punch`
- Template: `status_aftermath`
- Group: `chuck_poliwrath_vs_pidgeotto_ice_punch__status_aftermath`
- Rationale: Tests whether status moves are legal, useful, or redundant after public status changes.
- Changed fields: `{"state.player.active.status": "paralyzed"}`

## chuck_poliwrath_vs_pidgeotto_ice_punch__cf_target_asleep

- Parent: `chuck_poliwrath_vs_pidgeotto_ice_punch`
- Template: `status_aftermath`
- Group: `chuck_poliwrath_vs_pidgeotto_ice_punch__status_aftermath`
- Rationale: Tests whether status moves are legal, useful, or redundant after public status changes.
- Changed fields: `{"state.player.active.status": "asleep"}`

## chuck_poliwrath_vs_pidgeotto_ice_punch__cf_sleep_clause_occupied

- Parent: `chuck_poliwrath_vs_pidgeotto_ice_punch`
- Template: `status_aftermath`
- Group: `chuck_poliwrath_vs_pidgeotto_ice_punch__status_aftermath`
- Rationale: Tests whether status moves are legal, useful, or redundant after public status changes.
- Changed fields: `{"state.player.active.status": "none"}`

## chuck_poliwrath_vs_pidgeotto_ice_punch__cf_safe_switch

- Parent: `chuck_poliwrath_vs_pidgeotto_ice_punch`
- Template: `switch_fit`
- Group: `chuck_poliwrath_vs_pidgeotto_ice_punch__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "safe switch-in absorbs the public hit"}`

## chuck_poliwrath_vs_pidgeotto_ice_punch__cf_risky_switch

- Parent: `chuck_poliwrath_vs_pidgeotto_ice_punch`
- Template: `switch_fit`
- Group: `chuck_poliwrath_vs_pidgeotto_ice_punch__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "risky switch-in takes meaningful chip"}`

## chuck_poliwrath_vs_pidgeotto_ice_punch__cf_bad_switch

- Parent: `chuck_poliwrath_vs_pidgeotto_ice_punch`
- Template: `switch_fit`
- Group: `chuck_poliwrath_vs_pidgeotto_ice_punch__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "bad switch-in loses to the same public threat"}`

## jasmine_steelix_vs_quilava_fire_threat__cf_hp_ko_range

- Parent: `jasmine_steelix_vs_quilava_fire_threat`
- Template: `hp_threshold`
- Group: `jasmine_steelix_vs_quilava_fire_threat__hp_threshold`
- Rationale: Tests whether immediate KO pressure should dominate setup or status.
- Changed fields: `{"state.player.active.hp": "18%"}`

## jasmine_steelix_vs_quilava_fire_threat__cf_hp_2hko_range

- Parent: `jasmine_steelix_vs_quilava_fire_threat`
- Template: `hp_threshold`
- Group: `jasmine_steelix_vs_quilava_fire_threat__hp_threshold`
- Rationale: Tests the boundary where chip may set up a teammate but not end the turn.
- Changed fields: `{"state.player.active.hp": "54%"}`

## jasmine_steelix_vs_quilava_fire_threat__cf_hp_comfortable

- Parent: `jasmine_steelix_vs_quilava_fire_threat`
- Template: `hp_threshold`
- Group: `jasmine_steelix_vs_quilava_fire_threat__hp_threshold`
- Rationale: Tests whether slow plans are acceptable when the target is healthy.
- Changed fields: `{"state.player.active.hp": "88%"}`

## jasmine_skarmory_vs_machoke_whirlwind__cf_hp_ko_range

- Parent: `jasmine_skarmory_vs_machoke_whirlwind`
- Template: `hp_threshold`
- Group: `jasmine_skarmory_vs_machoke_whirlwind__hp_threshold`
- Rationale: Tests whether immediate KO pressure should dominate setup or status.
- Changed fields: `{"state.player.active.hp": "18%"}`

## jasmine_skarmory_vs_machoke_whirlwind__cf_hp_2hko_range

- Parent: `jasmine_skarmory_vs_machoke_whirlwind`
- Template: `hp_threshold`
- Group: `jasmine_skarmory_vs_machoke_whirlwind__hp_threshold`
- Rationale: Tests the boundary where chip may set up a teammate but not end the turn.
- Changed fields: `{"state.player.active.hp": "54%"}`

## jasmine_skarmory_vs_machoke_whirlwind__cf_hp_comfortable

- Parent: `jasmine_skarmory_vs_machoke_whirlwind`
- Template: `hp_threshold`
- Group: `jasmine_skarmory_vs_machoke_whirlwind__hp_threshold`
- Rationale: Tests whether slow plans are acceptable when the target is healthy.
- Changed fields: `{"state.player.active.hp": "88%"}`

## pryce_cloyster_vs_quilava_explosion_line__cf_safe_switch

- Parent: `pryce_cloyster_vs_quilava_explosion_line`
- Template: `switch_fit`
- Group: `pryce_cloyster_vs_quilava_explosion_line__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "safe switch-in absorbs the public hit"}`

## pryce_cloyster_vs_quilava_explosion_line__cf_risky_switch

- Parent: `pryce_cloyster_vs_quilava_explosion_line`
- Template: `switch_fit`
- Group: `pryce_cloyster_vs_quilava_explosion_line__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "risky switch-in takes meaningful chip"}`

## pryce_cloyster_vs_quilava_explosion_line__cf_bad_switch

- Parent: `pryce_cloyster_vs_quilava_explosion_line`
- Template: `switch_fit`
- Group: `pryce_cloyster_vs_quilava_explosion_line__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "bad switch-in loses to the same public threat"}`

## pryce_slowking_vs_ampharos_ground_pivot__cf_target_paralyzed

- Parent: `pryce_slowking_vs_ampharos_ground_pivot`
- Template: `status_aftermath`
- Group: `pryce_slowking_vs_ampharos_ground_pivot__status_aftermath`
- Rationale: Tests whether status moves are legal, useful, or redundant after public status changes.
- Changed fields: `{"state.player.active.status": "paralyzed"}`

## pryce_slowking_vs_ampharos_ground_pivot__cf_target_asleep

- Parent: `pryce_slowking_vs_ampharos_ground_pivot`
- Template: `status_aftermath`
- Group: `pryce_slowking_vs_ampharos_ground_pivot__status_aftermath`
- Rationale: Tests whether status moves are legal, useful, or redundant after public status changes.
- Changed fields: `{"state.player.active.status": "asleep"}`

## pryce_slowking_vs_ampharos_ground_pivot__cf_sleep_clause_occupied

- Parent: `pryce_slowking_vs_ampharos_ground_pivot`
- Template: `status_aftermath`
- Group: `pryce_slowking_vs_ampharos_ground_pivot__status_aftermath`
- Rationale: Tests whether status moves are legal, useful, or redundant after public status changes.
- Changed fields: `{"state.player.active.status": "none"}`

## pryce_slowking_vs_ampharos_ground_pivot__cf_safe_switch

- Parent: `pryce_slowking_vs_ampharos_ground_pivot`
- Template: `switch_fit`
- Group: `pryce_slowking_vs_ampharos_ground_pivot__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "safe switch-in absorbs the public hit"}`

## pryce_slowking_vs_ampharos_ground_pivot__cf_risky_switch

- Parent: `pryce_slowking_vs_ampharos_ground_pivot`
- Template: `switch_fit`
- Group: `pryce_slowking_vs_ampharos_ground_pivot__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "risky switch-in takes meaningful chip"}`

## pryce_slowking_vs_ampharos_ground_pivot__cf_bad_switch

- Parent: `pryce_slowking_vs_ampharos_ground_pivot`
- Template: `switch_fit`
- Group: `pryce_slowking_vs_ampharos_ground_pivot__switch_fit`
- Rationale: Tests when an other_better/switch lesson should override move scoring.
- Changed fields: `{"state.public_notes": "bad switch-in loses to the same public threat"}`
