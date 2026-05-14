# State-Transition Benchmark Report

Generated: 2026-05-14T03:34:49+00:00

## Summary

- Benchmarks: 44
- Required initial benchmarks present: `True`
- Policy evaluated: `True`
- Policy passes evaluated benchmarks: `True`
- Mechanics profiles: `{'romhack_gym_leader_lab': 32, 'vanilla_gsc': 12}`
- Splits: `{'fixture_harvest': 24, 'holdout': 15, 'seed': 5}`
- Outcomes: `{'best': 44}`
- Outcomes by split: `{'fixture_harvest': {'best': 24}, 'holdout': {'best': 15}, 'seed': {'best': 5}}`
- Split passes: `{'fixture_harvest': True, 'holdout': True, 'seed': True}`

## Move Targets

| Benchmark | Split | Profile | Best | Acceptable | Catastrophic | Chosen | Outcome |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `vanilla_gsc_sleep_setup_disruption_001` | `seed` | `vanilla_gsc` | `move_sleep_powder` | `move_sludge_bomb` | `move_swords_dance` | `move_sleep_powder` | `best` |
| `romhack_spikes_third_layer_janine_001` | `seed` | `romhack_gym_leader_lab` | `move_spikes` | `move_explosion` | `switch_tentacruel` | `move_spikes` | `best` |
| `romhack_spikes_fourth_click_janine_001` | `seed` | `romhack_gym_leader_lab` | `move_sludge_bomb` | `move_explosion` | `move_spikes` | `move_sludge_bomb` | `best` |
| `romhack_explosion_route_trade_brock_001` | `seed` | `romhack_gym_leader_lab` | `move_explosion` | `switch_omastar` | `move_curse` | `move_explosion` | `best` |
| `romhack_defensive_answer_preservation_pryce_001` | `seed` | `romhack_gym_leader_lab` | `switch_piloswine` | `move_thunder_wave` | `move_rest` | `switch_piloswine` | `best` |
| `vanilla_gsc_sleep_clause_blocked_holdout_001` | `holdout` | `vanilla_gsc` | `move_sludge_bomb` | `move_swords_dance` | `move_sleep_powder` | `move_sludge_bomb` | `best` |
| `romhack_spikes_public_spinner_holdout_001` | `holdout` | `romhack_gym_leader_lab` | `move_explosion` | `move_sludge_bomb` | `move_spikes` | `move_explosion` | `best` |
| `romhack_spikes_maxed_explosion_conversion_holdout_001` | `holdout` | `romhack_gym_leader_lab` | `move_explosion` | `move_sludge_bomb` | `move_spikes` | `move_explosion` | `best` |
| `romhack_explosion_blocked_by_protect_holdout_001` | `holdout` | `romhack_gym_leader_lab` | `switch_omastar` | `move_earthquake` | `move_explosion` | `switch_omastar` | `best` |
| `romhack_defensive_answer_unavailable_holdout_001` | `holdout` | `romhack_gym_leader_lab` | `move_thunder_wave` | `move_surf` | `switch_piloswine` | `move_thunder_wave` | `best` |
| `fixture_chuck_poliwrath_vs_pidgeotto_ice_punch_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `switch_sudowoodo` | `move_ice_punch` | `move_focus_punch` | `switch_sudowoodo` | `best` |
| `fixture_janine_qwilfish_third_spikes_layer_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `move_spikes` | `move_explosion` | `move_sludge_bomb`, `move_surf`, `switch_tentacruel` | `move_spikes` | `best` |
| `fixture_mechanics_snorlax_full_hp_rest_status_fail_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `move_body_slam` | `move_curse` | `move_rest`, `move_sleep_talk` | `move_body_slam` | `best` |
| `fixture_brock_golem_vs_vaporeon_explosion_question_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `move_explosion` | `switch_omastar` | `move_earthquake` | `move_explosion` | `best` |
| `long_battle_sleep_disruption_after_miss_001` | `holdout` | `vanilla_gsc` | `move_sleep_powder` | `switch_skarmory`, `move_sludge_bomb` | `move_swords_dance` | `move_sleep_powder` | `best` |
| `long_battle_rest_tempo_unforced_001` | `holdout` | `vanilla_gsc` | `move_body_slam` | `switch_skarmory` | `move_rest` | `move_body_slam` | `best` |
| `romhack_spinblock_damage_context_001` | `holdout` | `romhack_gym_leader_lab` | `move_thunderbolt` | `switch_raikou` | `move_destiny_bond` | `move_thunderbolt` | `best` |
| `vanilla_gsc_phazing_timing_mirror_001` | `holdout` | `vanilla_gsc` | `move_rock_slide` | `switch_suicune` | `move_roar` | `move_rock_slide` | `best` |
| `vanilla_gsc_pp_phaze_loop_save_final_whirlwind_001` | `holdout` | `vanilla_gsc` | `move_rest` | `move_toxic` | `move_whirlwind` | `move_rest` | `best` |
| `external_gsc_sleeping_lax_curse_window_001` | `holdout` | `vanilla_gsc` | `move_curse` | `move_earthquake` | `switch_zapdos` | `move_curse` | `best` |
| `vanilla_gsc_opening_electric_double_switch_spikes_001` | `holdout` | `vanilla_gsc` | `switch_cloyster` | `move_thunder`, `move_roar` | `move_rest` | `switch_cloyster` | `best` |
| `external_gsc_forretress_explosion_on_quagsire_001` | `holdout` | `vanilla_gsc` | `move_explosion` | `switch_snorlax`, `move_toxic` | `move_spikes` | `move_explosion` | `best` |
| `external_gsc_vaporeon_vs_restdtalk_snorlax_001` | `holdout` | `vanilla_gsc` | `move_surf` | `move_rest`, `switch_raikou` | `move_growth` | `move_surf` | `best` |
| `external_gsc_golem_late_rapid_spin_001` | `holdout` | `vanilla_gsc` | `move_rapid_spin` | `move_earthquake`, `move_roar` | `move_explosion` | `move_rapid_spin` | `best` |
| `fixture_will_slowbro_vs_houndoom_fast_dark_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `switch_houndoom` | `move_surf` | `move_amnesia`, `move_psychic` | `switch_houndoom` | `best` |
| `fixture_koga_ariados_vs_typhlosion_fire_spikes_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `switch_tentacruel` | `switch_umbreon` | `move_spikes`, `move_toxic`, `move_leech_life` | `switch_tentacruel` | `best` |
| `fixture_bugsy_scyther_vs_geodude_safe_swords_dance_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `move_swords_dance` | `move_wing_attack` | `switch_ariados`, `move_quick_attack` | `move_swords_dance` | `best` |
| `fixture_chuck_poliwrath_vs_alakazam_psychic_pivot_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `switch_umbreon` | `move_hypnosis`, `move_surf` | `move_ice_punch` | `switch_umbreon` | `best` |
| `fixture_morty_haunter_vs_noctowl_sleep_line_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `move_hypnosis` | `move_night_shade` | `move_curse`, `switch_gengar` | `move_hypnosis` | `best` |
| `fixture_falkner_pidgeotto_vs_geodude_scout_probe_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `move_sand_attack` | `move_gust` | `switch_noctowl` | `move_sand_attack` | `best` |
| `fixture_pryce_cloyster_vs_quilava_fire_pivot_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `switch_slowking` | `move_protect` | `move_surf`, `move_explosion` | `switch_slowking` | `best` |
| `fixture_bugsy_scyther_vs_quilava_fire_setup_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `move_swords_dance` | `move_wing_attack` | `move_quick_attack`, `switch_ledian` | `move_swords_dance` | `best` |
| `fixture_whitney_miltank_vs_geodude_rollout_lock_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `move_body_slam` | `move_milk_drink` | `move_rollout`, `switch_girafarig` | `move_body_slam` | `best` |
| `fixture_karen_crobat_vs_dragonite_toxic_clock_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `move_toxic` | `switch_tyranitar` | `move_wing_attack`, `move_confuse_ray` | `move_toxic` | `best` |
| `fixture_koga_crobat_vs_alakazam_immediate_ko_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `move_wing_attack` | `switch_umbreon` | `move_toxic`, `move_confuse_ray` | `move_wing_attack` | `best` |
| `fixture_jasmine_skarmory_vs_machoke_focus_energy_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `move_toxic` | `move_whirlwind` | `move_steel_wing`, `switch_forretress` | `move_toxic` | `best` |
| `fixture_morty_misdreavus_vs_typhlosion_perish_route_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `move_perish_song` | `switch_gengar` | `move_confuse_ray`, `move_psywave` | `move_perish_song` | `best` |
| `fixture_whitney_clefairy_vs_bayleef_encore_reflect_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `move_encore` | `move_double_team` | `move_doubleslap` | `move_encore` | `best` |
| `fixture_jasmine_magneton_vs_quilava_speed_control_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `move_thunder_wave` | `move_thunderbolt` | `move_lock_on`, `switch_steelix` | `move_thunder_wave` | `best` |
| `fixture_misty_starmie_vs_meganium_recover_tempo_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `move_psychic` | `switch_lapras` | `move_recover`, `move_hydro_pump` | `move_psychic` | `best` |
| `fixture_clair_dragonair_vs_suicune_hidden_ice_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `switch_kingdra` | `switch_mantine` | `move_thunder`, `move_outrage` | `switch_kingdra` | `best` |
| `fixture_bugsy_ariados_vs_pidgey_status_clock_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `move_toxic` | `switch_scyther` | `move_poison_sting`, `move_giga_drain`, `move_leech_life` | `move_toxic` | `best` |
| `external_gsc_forretress_vs_curselax_status_before_hazards_001` | `fixture_harvest` | `vanilla_gsc` | `move_toxic` | `move_rapid_spin`, `move_spikes` | `move_explosion`, `switch_gengar` | `move_toxic` | `best` |
| `fixture_morty_gengar_vs_kadabra_destiny_bond_001` | `fixture_harvest` | `romhack_gym_leader_lab` | `move_shadow_ball` | `switch_misdreavus` | `move_destiny_bond`, `move_spikes` | `move_shadow_ball` | `best` |

## Arbitration Targets

### `vanilla_gsc_sleep_setup_disruption_001`

- Dominant policy: Re-score after sleep disruption; use Sleep Powder only because the recomputed state still says sleep is the route creator.
- Catastrophe trigger: Victreebel uses Swords Dance after the prior Sleep Powder miss.
- Answer-changing information:
  - Sleep Clause is already occupied.
  - Snorlax is already statused.
  - Victreebel is slower due to paralysis or speed control.
  - Snorlax is in guaranteed Sludge Bomb KO range.

### `romhack_spikes_third_layer_janine_001`

- Dominant policy: Finish the third layer when the stack is nearly complete, the target cannot immediately stop it, and hazard control is not public.
- Catastrophe trigger: Qwilfish switches instead of placing the third layer.
- Answer-changing information:
  - A player Rapid Spin user is revealed and can enter cheaply.
  - The player team is mostly Flying or otherwise ignores Spikes.
  - Snorlax has an immediate KO on Qwilfish.
  - Explosion removes the only defensive answer to a confirmed endgame route.

### `romhack_spikes_fourth_click_janine_001`

- Dominant policy: State legality dominates strategic slogans: once Spikes are maxed, use a live conversion move.
- Catastrophe trigger: Qwilfish attempts Spikes at three existing layers.
- Answer-changing information:
  - The local source changes to support a fourth layer.
  - The recorded hazard state was wrong and only two layers are up.
  - Explosion creates an immediate forced win.

### `romhack_explosion_route_trade_brock_001`

- Dominant policy: Explosion dominates only because the sacrifice buys a concrete next position and Golem's future defensive role is replaceable.
- Catastrophe trigger: Golem uses Curse instead of trading or switching.
- Answer-changing information:
  - Vaporeon is already in guaranteed Earthquake or Rock Slide range.
  - Golem is needed later as the only Electric immunity or Explosion user.
  - The opponent has revealed Protect or a Ghost pivot.
  - Omastar cannot safely take the forced follow-up.

### `romhack_defensive_answer_preservation_pryce_001`

- Dominant policy: Preservation through a resistant pivot dominates because it answers the immediate punish and keeps Slowking useful.
- Catastrophe trigger: Slowking uses Rest or weak chip while Ampharos keeps Electric pressure.
- Answer-changing information:
  - Piloswine is low enough that it cannot absorb ThunderPunch.
  - Ampharos has revealed coverage that KOs Piloswine on the switch.
  - Slowking has a guaranteed KO this turn.
  - Ampharos is already paralyzed or otherwise unable to pressure.

### `vanilla_gsc_sleep_clause_blocked_holdout_001`

- Dominant policy: Move legality dominates the sleep/setup heuristic; use live chip when Sleep Clause blocks the route.
- Catastrophe trigger: Victreebel clicks Sleep Powder while Sleep Clause is occupied.
- Answer-changing information:
  - Sleep Clause becomes free.
  - Snorlax is already in guaranteed Sludge Bomb KO range.
  - Victreebel is needed more as a preserved defensive piece than an attacker.

### `romhack_spikes_public_spinner_holdout_001`

- Dominant policy: Public hazard control dominates the layer-completion heuristic; remove the spinner if the trade preserves the whole hazard route.
- Catastrophe trigger: Qwilfish places a third layer while public Starmie remains active and healthy enough to spin.
- Answer-changing information:
  - Rapid Spin is not actually revealed.
  - Starmie is in guaranteed Sludge Bomb range.
  - The opponent has a Ghost that can block the Explosion route or punish it.
  - Qwilfish is needed later as the only answer to a separate threat.

### `romhack_spikes_maxed_explosion_conversion_holdout_001`

- Dominant policy: After the stack is complete, Explosion can dominate live chip when it removes the piece that prevents hazard conversion.
- Catastrophe trigger: Qwilfish clicks a fourth Spikes or weak chip while Snorlax Rests.
- Answer-changing information:
  - Snorlax reveals Protect or a Ghost pivot is available.
  - Qwilfish is needed later as the only hazard setter after a likely spin.
  - Snorlax is already in guaranteed Sludge Bomb range.
  - A second opposing hazard absorber is healthier and more important.

### `romhack_explosion_blocked_by_protect_holdout_001`

- Dominant policy: Public Protect information overrides the Explosion-converts heuristic; preserve or chip until the block is no longer free.
- Catastrophe trigger: Golem Explodes into a revealed Protect branch.
- Answer-changing information:
  - Protect is out of PP or disabled.
  - The opponent is forced to attack due to a timer or guaranteed loss if it Protects.
  - Omastar cannot safely absorb Surf.
  - Earthquake puts Vaporeon into a forced follow-up KO range.

### `romhack_defensive_answer_unavailable_holdout_001`

- Dominant policy: Current availability dominates the preservation slogan; when the answer is gone, choose the best live mitigation move.
- Catastrophe trigger: Slowking tries to switch to a Piloswine that is not on the public bench.
- Answer-changing information:
  - Piloswine is actually alive and available.
  - Ampharos is immune to paralysis or already paralyzed.
  - Surf is a guaranteed KO.
  - Cloyster has a verified way to absorb or punish Ampharos.

### `fixture_chuck_poliwrath_vs_pidgeotto_ice_punch_001`

- Dominant policy: When a live defensive answer is available and the active piece matters later, preservation dominates visible coverage and speculative Focus Punch.
- Catastrophe trigger: Poliwrath clicks Focus Punch into the revealed faster attacking line.
- Answer-changing information:
  - Sudowoodo is unavailable, statused, or already in KO range.
  - Ice Punch is a guaranteed KO and Poliwrath survives every public response afterward.
  - Pidgeotto is locked into a non-attacking move or cannot break Focus Punch.
  - Kadabra is gone, making Poliwrath HP much less valuable.

### `fixture_janine_qwilfish_third_spikes_layer_001`

- Dominant policy: The romhack third layer dominates while it is live, public hazard control is absent, and the current opponent cannot immediately stop it.
- Catastrophe trigger: Qwilfish attacks or switches instead of placing the third layer while the stack is at two.
- Answer-changing information:
  - A player Rapid Spin user is revealed and can enter without cost.
  - Snorlax has an immediate KO or disabling move into Qwilfish.
  - The seen player team is not mostly grounded.
  - Explosion creates an immediate forced win that third-layer Spikes cannot match.

### `fixture_mechanics_snorlax_full_hp_rest_status_fail_001`

- Dominant policy: Mechanics legality dominates role slogans: choose a live move when Rest and Sleep Talk fail from the exact current state.
- Catastrophe trigger: Snorlax chooses Rest at full HP or Sleep Talk while awake.
- Answer-changing information:
  - Snorlax is below full HP, making Rest mechanically legal.
  - Snorlax is asleep, making Sleep Talk mechanically legal.
  - Skarmory is in guaranteed Body Slam KO range.
  - Whirlwind is disabled or out of PP, increasing Curse conversion value.

### `fixture_brock_golem_vs_vaporeon_explosion_question_001`

- Dominant policy: Explosion narrowly dominates because the saved judgment treats it and Omastar as close, and the current state lets the sacrifice buy a clean next position.
- Catastrophe trigger: Golem uses Earthquake while Vaporeon stays in and uses Surf.
- Answer-changing information:
  - Vaporeon reveals Protect or another Explosion block.
  - Golem is still required as the only answer to a confirmed remaining physical threat.
  - Omastar is too low to absorb Surf after switching.
  - Earthquake is guaranteed to KO because Vaporeon is much lower than recorded.

### `long_battle_sleep_disruption_after_miss_001`

- Dominant policy: After a sleep disruption, re-score the current board; sleep remains best only because the clause and target status still allow it.
- Catastrophe trigger: Victreebel uses Swords Dance after Sleep Powder already missed and Snorlax remains awake.
- Answer-changing information:
  - Sleep Clause is occupied.
  - Snorlax is already statused.
  - Victreebel no longer survives the revealed Body Slam branch.
  - Snorlax is in guaranteed Sludge Bomb KO range.

### `long_battle_rest_tempo_unforced_001`

- Dominant policy: Rest timing must be forced by role survival or route conversion; high-HP Rest under phaze/attack pressure is tempo loss.
- Catastrophe trigger: Snorlax chooses Rest while still healthy enough to keep pressuring Tyranitar.
- Answer-changing information:
  - Snorlax is in guaranteed KO range if it does not Rest now.
  - Tyranitar lacks Roar or meaningful attacking pressure.
  - Snorlax's Body Slam PP or Rest PP is nearly exhausted.
  - Skarmory cannot safely enter due to hazard or coverage damage.

### `romhack_spinblock_damage_context_001`

- Dominant policy: Exact romhack damage evidence dominates the generic preserve-spinblocker heuristic; staying in is correct only because the public band says Gengar survives and KOs.
- Catastrophe trigger: Gengar chooses a non-damaging line while Starmie uses Rapid Spin or Psychic.
- Answer-changing information:
  - Gengar current HP is 52 or lower, making Psychic a guaranteed KO before Thunderbolt.
  - Starmie is no longer in guaranteed Thunderbolt KO range.
  - Starmie has a public Protect-like block or another move that changes the immediate punish.
  - The battle is vanilla GSC rather than the romhack, because Gengar typing and damage evidence differ.

### `vanilla_gsc_phazing_timing_mirror_001`

- Dominant policy: Mechanics truth dominates the phazing slogan: Roar is only a policy move when the public move order lets it act last.
- Catastrophe trigger: Golem clicks Roar while faster than Skarmory in a simultaneous phazing turn.
- Answer-changing information:
  - Golem is slower than Skarmory within the negative-priority phazing bracket.
  - Skarmory cannot or will not click Whirlwind this turn.
  - Rock Slide no longer forces meaningful damage or flinch pressure.
  - Explosion removes Skarmory and opens a named route while Golem's role is no longer needed.

### `vanilla_gsc_pp_phaze_loop_save_final_whirlwind_001`

- Dominant policy: PP is route material: final phazing PP should be spent only when it denies an immediate setup route or prevents an unavoidable loss.
- Catastrophe trigger: Skarmory uses its last Whirlwind PP while Snorlax is unboosted and not yet forcing a route.
- Answer-changing information:
  - Snorlax is already heavily boosted and one more turn creates an unanswerable route.
  - Skarmory cannot survive the current Double-Edge branch unless it phazes now.
  - Whirlwind has more than one PP remaining.
  - Toxic is blocked by existing status or another mechanics condition.

### `external_gsc_sleeping_lax_curse_window_001`

- Dominant policy: Setup dominates immediate damage only because the target is asleep and Curse changes the post-wake exchange.
- Catastrophe trigger: Rhydon switches instead of using the sleep window.
- Answer-changing information:
  - Snorlax is awake or guaranteed to wake before Rhydon converts.
  - Curse no longer changes the Earthquake KO math.
  - Snorlax reveals a move that KOs Rhydon after the Curse turn.
  - Zapdos is the only remaining route and must be preserved immediately.

### `vanilla_gsc_opening_electric_double_switch_spikes_001`

- Dominant policy: Opening moves are information and resource bids: double-switching dominates only when the public incentives make the opponent's pivot likely and the resulting Spikes window is concrete.
- Catastrophe trigger: Raikou uses Rest at full HP or otherwise passes the lead turn without pressure.
- Answer-changing information:
  - Opponent Cloyster is not incentivized to switch and can safely set Spikes.
  - Boss Cloyster is unavailable, statused, or too low to claim the expected Spikes turn.
  - The likely switch target blocks or is hostile to Cloyster's Spikes plan.
  - Direct Thunder damage or paralysis is needed immediately to stop Cloyster from completing its hazard role.

### `external_gsc_forretress_explosion_on_quagsire_001`

- Dominant policy: Route conversion dominates preservation because Forretress has already completed its hazard/spin jobs and Explosion removes the active blocker.
- Catastrophe trigger: Forretress repeats Spikes or takes a no-progress turn after its hazard role is discharged.
- Answer-changing information:
  - Protect or a Ghost switch is publicly revealed.
  - Forretress is still needed to remove hazards later.
  - Explosion no longer removes or cripples Quagsire enough to open the route.
  - Quagsire is no longer a relevant blocker to the remaining Snorlax route.

### `external_gsc_vaporeon_vs_restdtalk_snorlax_001`

- Dominant policy: Immediate conversion pressure dominates setup because the sleeping target has public RestTalk counterplay.
- Catastrophe trigger: Vaporeon uses Growth while Snorlax is asleep with Sleep Talk and Rest revealed.
- Answer-changing information:
  - Sleep Talk or Rest is not available on Snorlax.
  - Growth changes the Surf KO math enough to survive the RestTalk branch.
  - Vaporeon is forced to Rest immediately by poison or incoming damage.
  - Snorlax is guaranteed to stay asleep without Sleep Talk this turn.

### `external_gsc_golem_late_rapid_spin_001`

- Dominant policy: Hazard removal dominates immediate damage because Snorlax is likely to Rest and own-side Spikes still tax the future route.
- Catastrophe trigger: Golem spends Explosion before clearing own-side Spikes.
- Answer-changing information:
  - Own-side Spikes are already absent.
  - Snorlax cannot Rest or is in guaranteed KO range.
  - Golem is no longer needed as a spinner or phazer.
  - Explosion immediately removes the final opponent route and no future switches are required.

### `fixture_will_slowbro_vs_houndoom_fast_dark_001`

- Dominant policy: Immediate public lethal punish and preservation dominate direct damage and setup when a healthy pivot can absorb the known route.
- Catastrophe trigger: Slowbro uses Amnesia or another non-preserving stay-in move while Houndoom clicks Crunch.
- Answer-changing information:
  - Will's Houndoom pivot is unavailable or too low to absorb the public Dark pressure.
  - Crunch is not actually available or no longer lethal by exact damage evidence.
  - Slowbro is faster due to speed control.
  - Surf is guaranteed to KO before Houndoom can act.
  - The player has revealed Pursuit and the switch punishment is worse than staying in.

### `fixture_koga_ariados_vs_typhlosion_fire_spikes_001`

- Dominant policy: Immediate public lethal punish dominates generic hazard and status progress; preserve Ariados through the cleanest available pivot, then re-score.
- Catastrophe trigger: Ariados stays in for Spikes, Toxic, or Leech Life while Typhlosion clicks revealed Flamethrower.
- Answer-changing information:
  - Tentacruel is unavailable or too low to absorb the public Fire pressure, making Umbreon the next preserving pivot.
  - Flamethrower is unavailable, out of PP, or no longer lethal by exact damage evidence.
  - Typhlosion is in guaranteed KO range before it can move.
  - Ariados is no longer needed as a hazard or poison piece and a sacrifice opens a forced route.
  - A public Earthquake branch makes Tentacruel's switch-in catastrophe worse than preserving through another pivot.

### `fixture_bugsy_scyther_vs_geodude_safe_swords_dance_001`

- Dominant policy: Setup dominates because the public punish is survivable and the boost changes the next-turn route; preservation and chip are weaker here.
- Catastrophe trigger: Scyther switches or uses low-value chip while Geodude remains unable to punish the setup turn.
- Answer-changing information:
  - Scyther is chipped low enough that Rock Throw or Magnitude removes it after the setup turn.
  - A stronger public Rock move is revealed.
  - Geodude is already in guaranteed Wing Attack KO range.
  - The player has a priority or phazing branch that stops Scyther after setup.
  - Bugsy needs Scyther only as a preserved late-game piece rather than the current route converter.

### `fixture_chuck_poliwrath_vs_alakazam_psychic_pivot_001`

- Dominant policy: Clean preservation through an environment-verified Psychic answer dominates accuracy-dependent sleep and low direct chip while the pivot is available.
- Catastrophe trigger: Poliwrath uses low-impact direct damage while Alakazam attacks or Recovers.
- Answer-changing information:
  - Umbreon is unavailable, too low, or threatened by confirmed coverage on the switch.
  - Sleep Clause is occupied or Alakazam is already statused, making Hypnosis invalid.
  - Psychic is no longer available or no longer a major punish by exact damage evidence.
  - Surf is a guaranteed KO or puts Alakazam into unavoidable KO range despite Recover.
  - Alakazam reveals a non-Psychic coverage branch that makes the Umbreon pivot worse than sleep or direct damage.

### `fixture_morty_haunter_vs_noctowl_sleep_line_001`

- Dominant policy: Legal sleep control dominates fixed damage because the public punish is survivable and the target is not already neutralized.
- Catastrophe trigger: Haunter uses Curse or switches while Noctowl remains unstatused and Sleep Clause is free.
- Answer-changing information:
  - Sleep Clause is occupied.
  - Noctowl is already statused.
  - Hypnosis PP is exhausted or accuracy risk is unacceptable because Haunter is in guaranteed KO range.
  - Noctowl reveals Sleep Talk or another sleep-absorbing route.
  - Night Shade puts Noctowl into guaranteed next-turn KO range.

### `fixture_falkner_pidgeotto_vs_geodude_scout_probe_001`

- Dominant policy: One scout probe dominates direct chip because the chip is tiny and the public punish is live; repeated probing is explicitly not the policy.
- Catastrophe trigger: Pidgeotto keeps clicking Gust or switches immediately while Geodude has a live Rock-risk branch.
- Answer-changing information:
  - Rock Throw is impossible, out of PP, or no longer meaningful by exact damage evidence.
  - Geodude is in a damage band where Gust materially changes the route.
  - Sand Attack has already landed once and the next turn should convert.
  - Noctowl has a confirmed better attack or defensive route into Geodude.
  - Pidgeotto is in guaranteed KO range even after one accuracy probe.

### `fixture_pryce_cloyster_vs_quilava_fire_pivot_001`

- Dominant policy: Preservation dominates both direct attack and Explosion because the active faints before progress and a public Fire-resist pivot exists.
- Catastrophe trigger: Cloyster stays in to click Surf or Explosion while faster Quilava has revealed Flame Wheel.
- Answer-changing information:
  - Cloyster is healthy enough to survive Flame Wheel and Surf materially changes the route.
  - Slowking is unavailable or already too low to pivot into Fire pressure.
  - Quilava's Fire STAB is out of PP, disabled, or otherwise cannot KO before Cloyster moves.
  - Explosion is guaranteed to move first or remove the only remaining blocker to Pryce's endgame.
  - Protect has a field effect or residual-damage route that makes scouting more than a one-turn delay.

### `fixture_bugsy_scyther_vs_quilava_fire_setup_001`

- Dominant policy: Setup dominates because the public punish is survivable and the boost changes the two-turn route; attack dominates only after the survival or conversion condition fails.
- Catastrophe trigger: Scyther switches or uses weak priority while the setup route is live.
- Answer-changing information:
  - Scyther is slower than Quilava.
  - Ember or another revealed Fire move KOs Scyther after the setup turn.
  - Unboosted Wing Attack already KOs Quilava from the public HP.
  - A switch-in makes the boosted route fail or exposes a more important Scyther preservation duty.
  - A damage roll leaves Quilava outside +2 Wing Attack range and Quick Attack does not cover the remainder.

### `fixture_whitney_miltank_vs_geodude_rollout_lock_001`

- Dominant policy: Body Slam pressure dominates first-turn Rollout because lock moves need status, HP, and punish branches to be favorable before commitment.
- Catastrophe trigger: Miltank opens Rollout into healthy, unstatused Geodude.
- Answer-changing information:
  - Body Slam already paralyzed Geodude.
  - Miltank is near the damage threshold where Milk Drink is required before continuing pressure.
  - Geodude is in range where Rollout immediately forces the route without dangerous lock turns.
  - Magnitude is confirmed absent or unable to threaten the lock sequence.
  - A switch makes Body Slam pressure worse than preserving Miltank.

### `fixture_karen_crobat_vs_dragonite_toxic_clock_001`

- Dominant policy: Toxic dominates because it creates a concrete clock while Crobat survives the first punish; preservation becomes the next re-score after the clock is established.
- Catastrophe trigger: Crobat uses Wing Attack into full-HP Dragonite.
- Answer-changing information:
  - Crobat no longer survives the public Outrage branch.
  - Dragonite already has primary status.
  - Wing Attack reaches a decisive damage threshold.
  - Tyranitar is unavailable or too low to pivot into the Dragon route.
  - A revealed coverage move makes Tyranitar a bad follow-up pivot.

### `fixture_koga_crobat_vs_alakazam_immediate_ko_001`

- Dominant policy: Immediate KO damage dominates slow status and disruption when it removes the active threat before Psychic or Recover can matter.
- Catastrophe trigger: Crobat uses Toxic while Wing Attack already KOs.
- Answer-changing information:
  - Wing Attack no longer KOs from the current HP range.
  - Alakazam is already statused or cannot use Recover.
  - Crobat is slower than Alakazam in the public state.
  - Umbreon is unavailable or too low to preserve Crobat if the KO route disappears.
  - A revealed Alakazam move makes Umbreon a bad fallback pivot.

### `fixture_jasmine_skarmory_vs_machoke_focus_energy_001`

- Dominant policy: Toxic pressure slightly dominates because Focus Energy is a low-urgency setup signal and Skarmory can survive the public punish; Whirlwind takes over only when setup becomes a real boost route.
- Catastrophe trigger: Skarmory attacks with Steel Wing into healthy Machoke.
- Answer-changing information:
  - Machoke reveals a real attack-boosting setup route.
  - Machoke is already poisoned.
  - Steel Wing reaches a KO threshold.
  - Fire Blast is confirmed and makes Skarmory unable to stay.
  - Whirlwind PP is scarce enough that spending it now closes a later route.

### `fixture_morty_misdreavus_vs_typhlosion_perish_route_001`

- Dominant policy: Perish Song dominates because it changes the route by forcing the boosted attacker to leave, while Misdreavus survives the public punish.
- Catastrophe trigger: Misdreavus uses Confuse Ray instead of Perish Song.
- Answer-changing information:
  - Misdreavus no longer survives the revealed Flame Wheel branch.
  - Typhlosion is no longer boosted.
  - Typhlosion is already in a direct KO range.
  - Gengar is unavailable or too low to preserve the route.
  - A stronger Fire move is confirmed and changes whether Perish Song can start.

### `fixture_whitney_clefairy_vs_bayleef_encore_reflect_001`

- Dominant policy: Encore dominates because public last-move and speed evidence make it a concrete trap, while Double Team is only the fallback when that trap is absent.
- Catastrophe trigger: Clefairy uses DoubleSlap while Bayleef's last move is Reflect.
- Answer-changing information:
  - Bayleef's last move is not Reflect.
  - Clefairy is slower than Bayleef.
  - Bayleef already switched out after using Reflect.
  - Bayleef is already under Encore.
  - Bayleef is in direct KO range from an attack.

### `fixture_jasmine_magneton_vs_quilava_speed_control_001`

- Dominant policy: Speed-control status dominates while direct damage does not remove Quilava and Magneton survives the public punish; direct attack takes over once the damage threshold removes the active threat.
- Catastrophe trigger: Magneton uses Lock-On while Quilava remains faster.
- Answer-changing information:
  - Thunderbolt reaches a direct removal threshold.
  - Quilava is already statused.
  - Magneton no longer survives the public Flame Wheel branch.
  - Dig is confirmed as the immediate move and changes whether Magneton can stay.
  - Steelix is no longer needed as a later-route anchor.

### `fixture_misty_starmie_vs_meganium_recover_tempo_001`

- Dominant policy: Tempo attack dominates because it improves the named Lapras cleanup route while Recover lacks a public window.
- Catastrophe trigger: Starmie uses Recover while Meganium remains active and able to attack.
- Answer-changing information:
  - Meganium is asleep or otherwise cannot punish the recovery turn.
  - Psychic no longer changes the Lapras cleanup band.
  - Lapras already has guaranteed cleanup without Starmie chip.
  - Starmie is needed later and can Recover without donating tempo.
  - Meganium has Synthesis confirmed and the chip route no longer sticks.

### `fixture_clair_dragonair_vs_suicune_hidden_ice_001`

- Dominant policy: Hidden-info preservation dominates because the plausible punish is severe, the opponent is incentivized to reveal it, and Kingdra is available.
- Catastrophe trigger: Dragonair stays in with Thunder while Suicune reveals Ice coverage.
- Answer-changing information:
  - Ice Beam or equivalent Ice coverage becomes impossible or very low plausibility.
  - Kingdra is unavailable or too low to pivot.
  - Suicune is forced to switch rather than threaten coverage.
  - Thunder reaches a decisive KO or forced-Rest threshold.
  - Mantine has a stronger confirmed role than Kingdra in the remaining matchup.

### `fixture_bugsy_ariados_vs_pidgey_status_clock_001`

- Dominant policy: Toxic dominates because it changes future turns while the public punish is survivable; pivoting dominates only after the clock exists or Toxic is unsafe.
- Catastrophe trigger: Ariados uses weak chip instead of Toxic.
- Answer-changing information:
  - Pidgey is already poisoned or otherwise statused.
  - Gust or another revealed move now KOs Ariados before Toxic matters.
  - Scyther is no longer an important ace route.
  - Ariados direct damage reaches a decisive threshold.
  - The player has a confirmed status-blocking pivot.

### `external_gsc_forretress_vs_curselax_status_before_hazards_001`

- Dominant policy: When a support Pokemon survives and the opposing setup anchor is unstatused, the route-stopping status move dominates generic hazard economy.
- Catastrophe trigger: Forretress spends the turn on Explosion or a bad switch instead of starting the Toxic clock.
- Answer-changing information:
  - Snorlax is already poisoned, paralyzed, asleep, or otherwise statused.
  - Forretress no longer survives the public hit long enough to land Toxic.
  - A phazing move is available and must be used immediately to stop a more dangerous boost state.
  - Rapid Spin is needed because own-side Spikes decide an immediate forced-entry route.
  - Explosion is proven to remove Snorlax and open a cleaner route than status.

### `fixture_morty_gengar_vs_kadabra_destiny_bond_001`

- Dominant policy: Direct removal dominates sacrifice and preservation while it cleanly removes the active threat; the trade line becomes correct only after direct removal stops converting.
- Catastrophe trigger: Gengar uses Destiny Bond while Shadow Ball already removes Kadabra.
- Answer-changing information:
  - Kadabra is outside Shadow Ball removal range.
  - Gengar is slower than Kadabra.
  - Destiny Bond is blocked or cannot carry through the expected move order.
  - Misdreavus is the only remaining answer to a later threat and cannot be exposed.
  - The battle is vanilla GSC rather than this romhack benchmark, requiring separate damage evidence.
