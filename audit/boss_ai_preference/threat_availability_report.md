# Boss AI Player Threat Availability Report

Generated from ROM source tables for the Boss AI preference lab.

## Likelihood Buckets

- `99%`: revealed or forced by public fixture evidence.
- `75%`: natural STAB/core level-up move.
- `50%`: natural non-STAB level-up move, pre-evo move, or direct TM access.
- `25%`: legal but optional or low-confidence.
- `0%`: unavailable or blocked by a four-revealed-move set.

## Known Limits

- Route reachability is a conservative checkpoint list, not a pathfinder.
- Wild grass, Surf-gated water, fishing tables, givepoke gifts/prizes, listed static encounters, direct TM scripts, and mart TM tables are parsed; breeding, trades, roaming RNG, and prerequisite-heavy statics are not fully route-modeled yet.
- Likelihood buckets are review buckets, not measured player behavior.

## Checkpoints

- `falkner` (Falkner): cap 14, badges before 0, rods ['none'], surf not usable, 34 available/current-public species, 1 direct TM move(s).
- `bugsy` (Bugsy): cap 17, badges before 1, rods ['old'], surf not usable, 50 available/current-public species, 2 direct TM move(s).
- `whitney` (Whitney): cap 21, badges before 2, rods ['old'], surf not usable, 74 available/current-public species, 13 direct TM move(s).
- `morty` (Morty): cap 26, badges before 3, rods ['old'], surf not usable, 88 available/current-public species, 13 direct TM move(s).
- `chuck` (Chuck): cap 34, badges before 4, rods ['old', 'good'], surf available, 139 available/current-public species, 17 direct TM move(s).
- `jasmine` (Jasmine): cap 34, badges before 4, rods ['old', 'good'], surf available, 139 available/current-public species, 17 direct TM move(s).
- `pryce` (Pryce): cap 34, badges before 4, rods ['old', 'good'], surf available, 139 available/current-public species, 17 direct TM move(s).
- `clair` (Clair): cap 39, badges before 7, rods ['old', 'good'], surf available, 173 available/current-public species, 17 direct TM move(s).
- `champion_lance` (Champion Lance): cap 50, badges before 8, rods ['old', 'good'], surf available, 204 available/current-public species, 20 direct TM move(s).
- `koga` (Koga): cap 50, badges before 8, rods ['old', 'good'], surf available, 198 available/current-public species, 20 direct TM move(s).
- `brock` (Brock): cap 60, badges before 8, rods ['old', 'good', 'super'], surf available, 207 available/current-public species, 38 direct TM move(s).
- `misty` (Misty): cap 63, badges before 8, rods ['old', 'good', 'super'], surf available, 207 available/current-public species, 38 direct TM move(s).
- `lt_surge` (Lt. Surge): cap 65, badges before 8, rods ['old', 'good', 'super'], surf available, 207 available/current-public species, 38 direct TM move(s).
- `erika` (Erika): cap 64, badges before 8, rods ['old', 'good', 'super'], surf available, 208 available/current-public species, 38 direct TM move(s).
- `janine` (Janine): cap 64, badges before 8, rods ['old', 'good', 'super'], surf available, 207 available/current-public species, 38 direct TM move(s).
- `sabrina` (Sabrina): cap 67, badges before 8, rods ['old', 'good', 'super'], surf available, 207 available/current-public species, 38 direct TM move(s).
- `blaine` (Blaine): cap 65, badges before 8, rods ['old', 'good', 'super'], surf available, 207 available/current-public species, 38 direct TM move(s).
- `blue` (Blue): cap 69, badges before 16, rods ['old', 'good', 'super'], surf available, 209 available/current-public species, 38 direct TM move(s).

## Fixture Threat Samples

### `falkner_pidgeotto_vs_geodude_rock_risk`

- Geodude `Tackle`: 99%, chip, active; about 12-18% vs Pidgeotto. revealed in the public fixture state
- Geodude `Defense Curl`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Geodude `Rock Throw`: 75%, meaningful, active; about 55-65% vs Pidgeotto. natural level-up STAB/core move by this checkpoint

### `bugsy_scyther_vs_quilava_fire_pressure`

- Quilava `Ember`: 99%, meaningful, active; about 45-54% vs Scyther. revealed in the public fixture state
- Quilava `Quick Attack`: 99%, chip, active; about 9-12% vs Scyther. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Geodude `Rock Throw`: 75%, lethal, switch; about 86-102% vs Scyther; switch fit risky vs Wing Attack (about 23-28% into Geodude). natural level-up STAB/core move by this checkpoint

### `whitney_miltank_vs_geodude_rollout_temptation`

- Geodude `Rock Throw`: 99%, chip, active; about 14-17% vs Miltank. revealed in the public fixture state
- Geodude `Defense Curl`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Geodude `Selfdestruct`: 50%, major, active; about 68-81% vs Miltank. natural level-up move by this checkpoint

### `whitney_clefairy_vs_bayleef_encore_window`

- Bayleef `Reflect`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Bayleef `Giga Drain`: 75%, chip, active; about 28-33% vs Clefairy. natural level-up STAB/core move by this checkpoint
- Bayleef `Razor Leaf`: 75%, chip, active; about 26-31% vs Clefairy. natural level-up STAB/core move by this checkpoint
- Bayleef `Headbutt`: 50%, chip, active; about 21-26% vs Clefairy. direct TM source is available by this checkpoint

### `morty_gengar_vs_kadabra_destiny_bond`

- Kadabra `Confusion`: 99%, chip, active; about 15-20% vs Gengar. revealed in the public fixture state
- Kadabra `Recover`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Kadabra `Psybeam`: 75%, chip, active; about 21-25% vs Gengar. natural level-up STAB/core move by this checkpoint
- Kadabra `Fire Punch`: 50%, lethal, active; about 32-39% vs Gengar. direct TM source is available by this checkpoint
- Kadabra `Ice Punch`: 50%, lethal, active; about 32-39% vs Gengar. direct TM source is available by this checkpoint

### `morty_haunter_vs_noctowl_sleep_line`

- Noctowl `Peck`: 99%, meaningful, active; about 31-38% vs Haunter. revealed in the public fixture state
- Noctowl `Reflect`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Quilava `Flame Wheel`: 75%, major, switch; about 60-71% vs Haunter; switch fit risky vs Night Shade (about 29% into Quilava). natural level-up STAB/core move by this checkpoint
- Quilava `Ember`: 75%, meaningful, switch; about 51-60% vs Haunter; switch fit risky vs Night Shade (about 29% into Quilava). natural level-up STAB/core move by this checkpoint
- Quilava `Fire Blast`: 50%, lethal, switch; about 135-160% vs Haunter; switch fit risky vs Night Shade (about 29% into Quilava). direct TM source is available by this checkpoint

### `chuck_poliwrath_vs_pidgeotto_ice_punch`

- Pidgeotto `Wing Attack`: 99%, chip, active; about 28-34% vs Poliwrath. revealed in the public fixture state
- Pidgeotto `Quick Attack`: 99%, chip, active; about 8-9% vs Poliwrath. revealed in the public fixture state
- Kadabra `Future Sight`: 75%, lethal, switch; about 91-107% vs Poliwrath; switch fit bad vs Surf (about 53-63% into Kadabra). natural level-up STAB/core move by this checkpoint

### `jasmine_steelix_vs_quilava_fire_threat`

- Quilava `Flame Wheel`: 99%, chip, active; about 26-31% vs Steelix. revealed in the public fixture state
- Quilava `Quick Attack`: 99%, chip, active; about 1-2% vs Steelix. revealed in the public fixture state
- Quilava `Flamethrower`: 75%, meaningful, active; about 40-48% vs Steelix. natural level-up STAB/core move by this checkpoint
- Quilava `Ember`: 75%, chip, active; about 21-25% vs Steelix. natural level-up STAB/core move by this checkpoint
- Quilava `Fire Blast`: 50%, lethal, active; about 58-69% vs Steelix. direct TM source is available by this checkpoint

### `jasmine_skarmory_vs_machoke_whirlwind`

- Machoke `Karate Chop`: 99%, chip, active; about 26-31% vs Skarmory. revealed in the public fixture state
- Machoke `Focus Energy`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Machoke `Seismic Toss`: 75%, meaningful, active; about 35% vs Skarmory. natural level-up STAB/core move by this checkpoint
- Machoke `Vital Throw`: 75%, chip, active; about 23-27% vs Skarmory. natural level-up STAB/core move by this checkpoint
- Machoke `Fire Blast`: 50%, major, active; about 61-72% vs Skarmory. direct TM source is available by this checkpoint

### `pryce_cloyster_vs_quilava_explosion_line`

- Quilava `Flame Wheel`: 99%, lethal, active; about 42-50% vs Cloyster. revealed in the public fixture state
- Quilava `Quick Attack`: 99%, chip, active; about 5-8% vs Cloyster. revealed in the public fixture state
- Quilava `Flamethrower`: 75%, lethal, active; about 67-80% vs Cloyster. natural level-up STAB/core move by this checkpoint
- Quilava `Ember`: 75%, lethal, active; about 37-43% vs Cloyster. natural level-up STAB/core move by this checkpoint
- Quilava `Fire Blast`: 50%, lethal, active; about 98-116% vs Cloyster. direct TM source is available by this checkpoint

### `pryce_slowking_vs_ampharos_ground_pivot`

- Ampharos `Thunderpunch`: 99%, lethal, active; about 58-69% vs Slowking. revealed in the public fixture state
- Ampharos `Thunder Wave`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Ampharos `Thundershock`: 75%, meaningful, active; about 31-36% vs Slowking. natural level-up STAB/core move by this checkpoint
- Ampharos `Dragonbreath`: 75%, chip, active; about 23-27% vs Slowking. natural level-up STAB/core move by this checkpoint
- Ampharos `Thunder`: 50%, lethal, active; about 90-106% vs Slowking. direct TM source is available by this checkpoint

### `clair_dragonair_vs_suicune_hidden_ice_beam`

- Suicune `Surf`: 99%, chip, active; about 11-14% vs Dragonair. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Suicune `Blizzard`: 50%, lethal, active; about 80-95% vs Dragonair. direct TM source is available by this checkpoint
- Ampharos `Dragonbreath`: 75%, lethal, switch; about 68-80% vs Dragonair; switch fit bad vs Outrage (about 86-101% into Ampharos). natural level-up STAB/core move by this checkpoint

### `clair_kingdra_vs_lapras_dragon_dance_or_attack`

- Lapras `Ice Beam`: 99%, chip, active; about 19-22% vs Kingdra. revealed in the public fixture state
- Lapras `Body Slam`: 99%, chip, active; about 10-12% vs Kingdra. revealed in the public fixture state
- Lapras `Blizzard`: 50%, chip, active; about 23-28% vs Kingdra. direct TM source is available by this checkpoint

### `koga_crobat_vs_alakazam_toxic_or_attack`

- Alakazam `Psychic`: 99%, lethal, active; about 53-62% vs Crobat. revealed in the public fixture state
- Alakazam `Recover`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Alakazam `Future Sight`: 75%, lethal, active; about 70-83% vs Crobat. natural level-up STAB/core move by this checkpoint
- Alakazam `Psybeam`: 75%, meaningful, active; about 38-45% vs Crobat. natural level-up STAB/core move by this checkpoint
- Alakazam `Confusion`: 75%, meaningful, active; about 30-35% vs Crobat. natural level-up STAB/core move by this checkpoint

### `lance_dragonite_vs_suicune_champion_ace`

- Suicune `Surf`: 99%, chip, active; about 9-11% vs Dragonite. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Suicune `Rest`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Suicune `Blizzard`: 50%, lethal, active; about 92-108% vs Dragonite. direct TM source is available by this checkpoint
- Snorlax `Blizzard`: 50%, major, switch; about 68-80% vs Dragonite; switch fit bad vs Outrage (about 47-55% into Snorlax). direct TM source is available by this checkpoint

### `brock_golem_vs_vaporeon_explosion_question`

- Vaporeon `Surf`: 99%, lethal, active; about 136-160% vs Golem. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Vaporeon `Bite`: 99%, chip, active; about 15-18% vs Golem. revealed in the public fixture state
- Vaporeon `Hydro Pump`: 75%, lethal, active; about 170-201% vs Golem. natural level-up STAB/core move by this checkpoint
- Vaporeon `Water Gun`: 75%, lethal, active; about 73-86% vs Golem. natural level-up STAB/core move by this checkpoint
- Vaporeon `Blizzard`: 50%, lethal, active; about 57-67% vs Golem. direct TM source is available by this checkpoint

### `misty_starmie_vs_meganium_recover_or_attack`

- Meganium `Razor Leaf`: 99%, lethal, active; about 49-57% vs Starmie. revealed in the public fixture state
- Meganium `Reflect`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Meganium `Solarbeam`: 75%, lethal, active; about 60-71% vs Starmie. natural level-up STAB/core move by this checkpoint
- Meganium `Giga Drain`: 50%, lethal, active; about 52-62% vs Starmie. legal via pre-evolution level-up path
- Meganium `Earthquake`: 50%, chip, active; about 21-26% vs Starmie. direct TM source is available by this checkpoint

### `erika_victreebel_vs_snorlax_sleep_or_boost`

- Snorlax `Body Slam`: 99%, meaningful, active; about 45-53% vs Victreebel. revealed in the public fixture state
- Snorlax `Rest`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Snorlax `Hyper Beam`: 75%, lethal, active; about 108-128% vs Victreebel. natural level-up STAB/core move by this checkpoint
- Snorlax `Headbutt`: 75%, meaningful, active; about 42-50% vs Victreebel. natural level-up STAB/core move by this checkpoint
- Snorlax `Tackle`: 75%, chip, active; about 25-29% vs Victreebel. natural level-up STAB/core move by this checkpoint

### `sabrina_alakazam_choice_lock_vs_houndoom`

- Houndoom `Crunch`: 99%, lethal, active; about 77-90% vs Alakazam. revealed in the public fixture state
- Houndoom `Flamethrower`: 99%, meaningful, active; about 40-48% vs Alakazam. revealed in the public fixture state
- Houndoom `Bite`: 75%, meaningful, active; about 52-62% vs Alakazam. natural level-up STAB/core move by this checkpoint
- Houndoom `Faint Attack`: 75%, meaningful, active; about 52-62% vs Alakazam. natural level-up STAB/core move by this checkpoint
- Houndoom `Ember`: 75%, chip, active; about 21-26% vs Alakazam. natural level-up STAB/core move by this checkpoint

### `blue_arcanine_vs_starmie_champion_style`

- Starmie `Surf`: 99%, lethal, active; about 85-100% vs Arcanine. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Starmie `Psychic`: 99%, meaningful, active; about 40-47% vs Arcanine. revealed in the public fixture state
- Starmie `Recover`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Starmie `Hydro Pump`: 75%, lethal, active; about 107-126% vs Arcanine. natural level-up STAB/core move by this checkpoint
- Starmie `Bubblebeam`: 75%, lethal, active; about 59-69% vs Arcanine. natural level-up STAB/core move by this checkpoint

### `falkner_pidgeotto_vs_charmander_sand_attack_or_gust`

- Charmander `Ember`: 99%, chip, active; about 20-25% vs Pidgeotto. revealed in the public fixture state
- Charmander `Scratch`: 99%, chip, active; about 12-15% vs Pidgeotto. revealed in the public fixture state

### `falkner_pidgeotto_vs_pikachu_gust_or_quick_attack`

- Pikachu `Thundershock`: 99%, major, active; about 62-75% vs Pidgeotto. revealed in the public fixture state
- Pikachu `Thunder Wave`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Pikachu `Quick Attack`: 50%, chip, active; about 20-25% vs Pidgeotto. natural level-up move by this checkpoint
- Geodude `Rock Throw`: 75%, lethal, switch; about 68-80% vs Pidgeotto; switch fit reasonable vs Quick Attack (about 5-8% into Geodude). natural level-up STAB/core move by this checkpoint
- Bellsprout `Vine Whip`: 75%, meaningful, switch; about 30-38% vs Pidgeotto; switch fit risky vs Quick Attack (about 20-25% into Bellsprout). natural level-up STAB/core move by this checkpoint

### `bugsy_scyther_vs_geodude_safe_swords_dance`

- Geodude `Tackle`: 99%, chip, active; about 9-12% vs Scyther. revealed in the public fixture state
- Geodude `Defense Curl`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Geodude `Rock Throw`: 75%, major, active; about 73-88% vs Scyther. natural level-up STAB/core move by this checkpoint

### `bugsy_ariados_vs_pidgey_toxic_or_attack`

- Pidgey `Quick Attack`: 99%, chip, active; about 8-10% vs Ariados. revealed in the public fixture state

### `whitney_miltank_vs_machop_attract_or_body_slam`

- Machop `Karate Chop`: 99%, meaningful, active; about 45-54% vs Miltank. revealed in the public fixture state
- Machop `Leer`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Machop `Low Kick`: 75%, chip, active; about 28-33% vs Miltank. natural level-up STAB/core move by this checkpoint
- Machop `Seismic Toss`: 75%, chip, active; about 26% vs Miltank. natural level-up STAB/core move by this checkpoint
- Bayleef `Giga Drain`: 75%, chip, switch; about 27-32% vs Miltank; switch fit risky vs Stomp (about 30-37% into Bayleef). natural level-up STAB/core move by this checkpoint

### `morty_misdreavus_vs_typhlosion_perish_song`

- Typhlosion `Flame Wheel`: 99%, meaningful, active; about 46-55% vs Misdreavus. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Typhlosion `Swift`: 99%, chip, active; about 0% vs Misdreavus. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Typhlosion `Ember`: 75%, meaningful, active; about 37-45% vs Misdreavus. natural level-up STAB/core move by this checkpoint
- Typhlosion `Fire Blast`: 50%, lethal, active; about 104-122% vs Misdreavus. direct TM source is available by this checkpoint
- Typhlosion `Fire Punch`: 50%, lethal, active; about 57-67% vs Misdreavus. direct TM source is available by this checkpoint

### `chuck_hitmonlee_vs_machoke_hi_jump_kick_or_rock_slide`

- Machoke `Karate Chop`: 99%, meaningful, active; about 52-62% vs Hitmonlee. revealed in the public fixture state
- Machoke `Bulk Up`: 99%, support, active; support/no rough damage. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Machoke `Vital Throw`: 75%, meaningful, active; about 46-54% vs Hitmonlee. natural level-up STAB/core move by this checkpoint
- Machoke `Low Kick`: 75%, meaningful, active; about 34-40% vs Hitmonlee. natural level-up STAB/core move by this checkpoint
- Machoke `Seismic Toss`: 75%, chip, active; about 33% vs Hitmonlee. natural level-up STAB/core move by this checkpoint

### `chuck_poliwrath_vs_alakazam_hypnosis_or_ice_punch`

- Alakazam `Psychic`: 99%, major, active; about 73-86% vs Poliwrath. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Alakazam `Recover`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Alakazam `Future Sight`: 75%, lethal, active; about 98-116% vs Poliwrath. natural level-up STAB/core move by this checkpoint
- Alakazam `Psybeam`: 75%, meaningful, active; about 53-63% vs Poliwrath. natural level-up STAB/core move by this checkpoint
- Alakazam `Confusion`: 75%, meaningful, active; about 41-49% vs Poliwrath. natural level-up STAB/core move by this checkpoint

### `jasmine_magneton_vs_quilava_thunder_wave_or_bolt`

- Quilava `Flame Wheel`: 99%, lethal, active; about 93-110% vs Magneton. revealed in the public fixture state
- Quilava `Quick Attack`: 99%, chip, active; about 4-6% vs Magneton. revealed in the public fixture state
- Quilava `Flamethrower`: 75%, lethal, active; about 145-171% vs Magneton. natural level-up STAB/core move by this checkpoint
- Quilava `Ember`: 75%, major, active; about 76-90% vs Magneton. natural level-up STAB/core move by this checkpoint
- Quilava `Fire Blast`: 50%, lethal, active; about 211-249% vs Magneton. direct TM source is available by this checkpoint

### `pryce_piloswine_vs_typhlosion_amnesia_or_attack`

- Typhlosion `Flamethrower`: 99%, lethal, active; about 72-85% vs Piloswine. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Typhlosion `Swift`: 99%, chip, active; about 15-18% vs Piloswine. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Typhlosion `Flame Wheel`: 75%, meaningful, active; about 46-54% vs Piloswine. natural level-up STAB/core move by this checkpoint
- Typhlosion `Ember`: 75%, meaningful, active; about 38-46% vs Piloswine. natural level-up STAB/core move by this checkpoint
- Typhlosion `Fire Blast`: 50%, lethal, active; about 107-126% vs Piloswine. direct TM source is available by this checkpoint

### `clair_kingdra_vs_dragonair_dragon_dance_mirror`

- Dragonair `Outrage`: 99%, major, active; about 77-91% vs Kingdra. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Dragonair `Dragonbreath`: 75%, meaningful, active; about 47-56% vs Kingdra. natural level-up STAB/core move by this checkpoint
- Dragonair `Twister`: 75%, meaningful, active; about 31-37% vs Kingdra. natural level-up STAB/core move by this checkpoint
- Dragonair `Dragon Rage`: 75%, chip, active; about 31% vs Kingdra. natural level-up STAB/core move by this checkpoint
- Ampharos `Dragonbreath`: 75%, meaningful, switch; about 50-59% vs Kingdra; switch fit reasonable vs Surf (about 11-13% into Ampharos). natural level-up STAB/core move by this checkpoint

### `clair_dragonair_vs_ampharos_thunder_or_wave`

- Ampharos `Thunderpunch`: 99%, chip, active; about 11-14% vs Dragonair. revealed in the public fixture state
- Ampharos `Dragonbreath`: 75%, lethal, active; about 76-90% vs Dragonair. natural level-up STAB/core move by this checkpoint
- Ampharos `Twister`: 75%, meaningful, active; about 51-61% vs Dragonair. natural level-up STAB/core move by this checkpoint

### `will_xatu_vs_typhlosion_psychic_or_future_sight`

- Typhlosion `Flamethrower`: 99%, meaningful, active; about 47-55% vs Xatu. revealed in the public fixture state
- Typhlosion `Quick Attack`: 99%, chip, active; about 10-12% vs Xatu. revealed in the public fixture state
- Typhlosion `Earthquake`: 99%, chip, active; about 0% vs Xatu. revealed in the public fixture state
- Typhlosion `Fire Blast`: 75%, major, active; about 68-81% vs Xatu. natural level-up STAB/core move by this checkpoint
- Typhlosion `Double Edge`: 75%, meaningful, active; about 31-36% vs Xatu. natural level-up STAB/core move by this checkpoint

### `will_slowbro_vs_houndoom_amnesia_or_surf`

- Houndoom `Crunch`: 99%, lethal, active; about 93-109% vs Slowbro. revealed in the public fixture state
- Houndoom `Bite`: 75%, major, active; about 64-75% vs Slowbro. natural level-up STAB/core move by this checkpoint
- Houndoom `Faint Attack`: 75%, major, active; about 64-75% vs Slowbro. natural level-up STAB/core move by this checkpoint
- Houndoom `Flamethrower`: 75%, chip, active; about 24-28% vs Slowbro. natural level-up STAB/core move by this checkpoint
- Houndoom `Solarbeam`: 50%, lethal, active; about 124-146% vs Slowbro. direct TM source is available by this checkpoint

### `will_alakazam_vs_machamp_psychic_or_coverage`

- Machamp `Cross Chop`: 99%, major, active; about 77-91% vs Alakazam. revealed in the public fixture state
- Machamp `Rock Slide`: 99%, meaningful, active; about 31-38% vs Alakazam. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Machamp `Karate Chop`: 75%, meaningful, active; about 51-61% vs Alakazam. natural level-up STAB/core move by this checkpoint
- Machamp `Vital Throw`: 75%, meaningful, active; about 45-53% vs Alakazam. natural level-up STAB/core move by this checkpoint
- Machamp `Low Kick`: 75%, meaningful, active; about 32-39% vs Alakazam. natural level-up STAB/core move by this checkpoint

### `koga_ariados_vs_typhlosion_spikes_or_toxic`

- Typhlosion `Flamethrower`: 99%, lethal, active; about 149-176% vs Ariados. revealed in the public fixture state
- Typhlosion `Fire Blast`: 75%, lethal, active; about 219-258% vs Ariados. natural level-up STAB/core move by this checkpoint
- Typhlosion `Flame Wheel`: 75%, lethal, active; about 95-112% vs Ariados. natural level-up STAB/core move by this checkpoint
- Typhlosion `Ember`: 75%, major, active; about 78-93% vs Ariados. natural level-up STAB/core move by this checkpoint
- Typhlosion `Double Edge`: 75%, meaningful, active; about 50-59% vs Ariados. natural level-up STAB/core move by this checkpoint

### `koga_ariados_vs_quilava_spider_web_or_attack`

- Quilava `Flame Wheel`: 99%, lethal, active; about 68-81% vs Ariados. revealed in the public fixture state
- Quilava `Quick Attack`: 99%, chip, active; about 8-10% vs Ariados. revealed in the public fixture state
- Quilava `Flamethrower`: 75%, lethal, active; about 107-126% vs Ariados. natural level-up STAB/core move by this checkpoint
- Quilava `Ember`: 75%, meaningful, active; about 58-68% vs Ariados. natural level-up STAB/core move by this checkpoint
- Quilava `Fire Blast`: 50%, lethal, active; about 159-188% vs Ariados. direct TM source is available by this checkpoint

### `bruno_machamp_vs_alakazam_rock_slide_or_cross_chop`

- Alakazam `Psychic`: 99%, lethal, active; about 93-110% vs Machamp. revealed in the public fixture state
- Alakazam `Recover`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Alakazam `Future Sight`: 75%, lethal, active; about 124-146% vs Machamp. natural level-up STAB/core move by this checkpoint
- Alakazam `Psybeam`: 75%, major, active; about 68-80% vs Machamp. natural level-up STAB/core move by this checkpoint
- Alakazam `Confusion`: 75%, meaningful, active; about 52-62% vs Machamp. natural level-up STAB/core move by this checkpoint

### `bruno_hitmonlee_vs_skarmory_high_jump_kick_or_brick_break`

- Skarmory `Drill Peck`: 99%, lethal, active; about 125-148% vs Hitmonlee. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Skarmory `Steel Wing`: 99%, chip, active; about 20-24% vs Hitmonlee. revealed in the public fixture state
- Skarmory `Peck`: 75%, meaningful, active; about 58-69% vs Hitmonlee. natural level-up STAB/core move by this checkpoint
- Skarmory `Wing Attack`: 50%, lethal, active; about 93-110% vs Hitmonlee. direct TM source is available by this checkpoint
- Skarmory `Swift`: 50%, chip, active; about 23-27% vs Hitmonlee. natural level-up move by this checkpoint

### `bruno_onix_vs_typhlosion_sandstorm_or_explosion`

- Typhlosion `Flamethrower`: 99%, lethal, active; about 52-62% vs Onix. revealed in the public fixture state
- Typhlosion `Earthquake`: 99%, lethal, active; about 38-46% vs Onix. revealed in the public fixture state
- Typhlosion `Fire Blast`: 75%, lethal, active; about 77-91% vs Onix. natural level-up STAB/core move by this checkpoint
- Typhlosion `Flame Wheel`: 75%, lethal, active; about 32-39% vs Onix. natural level-up STAB/core move by this checkpoint
- Typhlosion `Ember`: 75%, lethal, active; about 28-32% vs Onix. natural level-up STAB/core move by this checkpoint

### `karen_houndoom_vs_alakazam_pursuit_or_flamethrower`

- Alakazam `Psychic`: 99%, chip, active; about 0% vs Houndoom. revealed in the public fixture state
- Alakazam `Dynamicpunch`: 50%, meaningful, active; about 45-53% vs Houndoom. direct TM source is available by this checkpoint
- Alakazam `Hyper Beam`: 50%, meaningful, active; about 39-47% vs Houndoom. direct TM source is available by this checkpoint
- Alakazam `Zap Cannon`: 50%, meaningful, active; about 39-46% vs Houndoom. direct TM source is available by this checkpoint
- Alakazam `Thunderpunch`: 50%, chip, active; about 28-34% vs Houndoom. direct TM source is available by this checkpoint

### `karen_crobat_vs_dragonite_toxic_or_attack`

- Dragonite `Outrage`: 99%, meaningful, active; about 47-56% vs Crobat. revealed in the public fixture state
- Dragonite `Wing Attack`: 75%, meaningful, active; about 38-45% vs Crobat. natural level-up STAB/core move by this checkpoint
- Dragonite `Dragonbreath`: 75%, meaningful, active; about 30-36% vs Crobat. natural level-up STAB/core move by this checkpoint
- Dragonite `Dragon Rage`: 75%, chip, active; about 26% vs Crobat. natural level-up STAB/core move by this checkpoint
- Dragonite `Blizzard`: 50%, lethal, active; about 80-95% vs Crobat. direct TM source is available by this checkpoint

### `karen_gengar_vs_snorlax_destiny_bond_or_thunderbolt`

- Snorlax `Body Slam`: 99%, chip, active; about 0% vs Gengar. revealed in the public fixture state
- Snorlax `Earthquake`: 99%, chip, active; about 0% vs Gengar. revealed in the public fixture state
- Snorlax `Shadow Ball`: 50%, lethal, active; about 172-203% vs Gengar. direct TM source is available by this checkpoint
- Snorlax `Solarbeam`: 50%, lethal, active; about 50-59% vs Gengar. direct TM source is available by this checkpoint
- Snorlax `Fire Blast`: 50%, lethal, active; about 38-46% vs Gengar. direct TM source is available by this checkpoint

### `lance_dragonite_vs_aerodactyl_outrage_or_dragon_dance`

- Aerodactyl `Rock Slide`: 99%, meaningful, active; about 51-60% vs Dragonite. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Aerodactyl `Ancientpower`: 75%, meaningful, active; about 40-48% vs Dragonite. natural level-up STAB/core move by this checkpoint
- Aerodactyl `Hyper Beam`: 50%, chip, active; about 26-31% vs Dragonite. natural level-up move by this checkpoint
- Zapdos `Thunderbolt`: 75%, chip, switch; about 25-30% vs Dragonite. natural level-up STAB/core move by this checkpoint
- Zapdos `Drill Peck`: 75%, chip, switch; about 23-28% vs Dragonite. natural level-up STAB/core move by this checkpoint

### `lance_ampharos_vs_porygon2_thunder_or_dragon_dance`

- Porygon2 `Tri Attack`: 99%, chip, active; about 20-24% vs Ampharos. revealed in the public fixture state
- Porygon2 `Recover`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Porygon2 `Blizzard`: 50%, major, active; about 61-72% vs Ampharos. direct TM source is available by this checkpoint
- Tyranitar `Earthquake`: 50%, lethal, switch; about 79-93% vs Ampharos; switch fit bad vs Thunder (about 35-41% into Tyranitar). direct TM source is available by this checkpoint

### `lance_kingdra_vs_starmie_dragon_dance_or_attack`

- Starmie `Surf`: 99%, chip, active; about 6-7% vs Kingdra. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Starmie `Recover`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Starmie `Psychic`: 75%, chip, active; about 25-29% vs Kingdra. natural level-up STAB/core move by this checkpoint
- Starmie `Thunder`: 50%, chip, active; about 21-26% vs Kingdra. direct TM source is available by this checkpoint
- Starmie `Blizzard`: 50%, chip, active; about 21-25% vs Kingdra. direct TM source is available by this checkpoint

### `red_pikachu_vs_dragonite_thunderbolt_or_extremespeed`

- Dragonite `Outrage`: 99%, lethal, active; about 152-180% vs Pikachu. revealed in the public fixture state
- Dragonite `Dragonbreath`: 75%, major, active; about 62-73% vs Pikachu. natural level-up STAB/core move by this checkpoint
- Dragonite `Wing Attack`: 75%, major, active; about 61-72% vs Pikachu. natural level-up STAB/core move by this checkpoint
- Dragonite `Twister`: 75%, meaningful, active; about 42-49% vs Pikachu. natural level-up STAB/core move by this checkpoint
- Dragonite `Hyper Beam`: 50%, lethal, active; about 183-215% vs Pikachu. legal via pre-evolution level-up path

### `red_snorlax_vs_alakazam_curse_or_body_slam`

- Alakazam `Psychic`: 99%, meaningful, active; about 34-39% vs Snorlax. revealed in the public fixture state
- Alakazam `Recover`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Alakazam `Future Sight`: 75%, meaningful, active; about 45-53% vs Snorlax. natural level-up STAB/core move by this checkpoint
- Alakazam `Psybeam`: 75%, chip, active; about 24-28% vs Snorlax. natural level-up STAB/core move by this checkpoint
- Alakazam `Dream Eater`: 50%, meaningful, active; about 37-44% vs Snorlax. direct TM source is available by this checkpoint

### `red_charizard_vs_starmie_sunny_day_or_switch`

- Starmie `Surf`: 99%, lethal, active; about 87-102% vs Charizard. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Starmie `Hydro Pump`: 75%, lethal, active; about 110-130% vs Charizard. natural level-up STAB/core move by this checkpoint
- Starmie `Bubblebeam`: 75%, major, active; about 61-72% vs Charizard. natural level-up STAB/core move by this checkpoint
- Starmie `Psychic`: 75%, meaningful, active; about 41-49% vs Charizard. natural level-up STAB/core move by this checkpoint
- Starmie `Thunder`: 50%, major, active; about 74-87% vs Charizard. direct TM source is available by this checkpoint

### `lance_dragonite_vs_steelix_earthquake_or_outrage`

- Steelix `Rock Slide`: 99%, meaningful, active; about 32-38% vs Dragonite. revealed in the public fixture state
- Steelix `Earthquake`: 99%, chip, active; about 7-8% vs Dragonite. revealed in the public fixture state
- Steelix `Iron Tail`: 75%, chip, active; about 27-32% vs Dragonite. natural level-up STAB/core move by this checkpoint
- Steelix `Dragonbreath`: 75%, chip, active; about 22-26% vs Dragonite. natural level-up STAB/core move by this checkpoint
- Steelix `Rock Throw`: 50%, chip, active; about 22-26% vs Dragonite. natural level-up move by this checkpoint

### `red_blastoise_vs_zapdos_mirror_coat_or_blizzard`

- Zapdos `Thunderbolt`: 99%, major, active; about 71-84% vs Blastoise. revealed in the public fixture state
- Zapdos `Drill Peck`: 75%, meaningful, active; about 34-41% vs Blastoise. natural level-up STAB/core move by this checkpoint
- Zapdos `Thundershock`: 75%, meaningful, active; about 30-36% vs Blastoise. natural level-up STAB/core move by this checkpoint
- Zapdos `Thunder`: 50%, lethal, active; about 90-106% vs Blastoise. direct TM source is available by this checkpoint
- Zapdos `Zap Cannon`: 50%, lethal, active; about 75-89% vs Blastoise. direct TM source is available by this checkpoint

### `red_blastoise_vs_tyranitar_surf_or_mirror_coat`

- Tyranitar `Rock Slide`: 99%, meaningful, active; about 30-36% vs Blastoise. revealed in the public fixture state
- Tyranitar `Crunch`: 99%, chip, active; about 25-29% vs Blastoise. revealed in the public fixture state
- Tyranitar `Hyper Beam`: 50%, meaningful, active; about 49-57% vs Blastoise. legal via pre-evolution level-up path
- Tyranitar `Focus Punch`: 50%, meaningful, active; about 41-48% vs Blastoise. direct TM source is available by this checkpoint
- Tyranitar `Double Edge`: 50%, meaningful, active; about 35-41% vs Blastoise. direct TM source is available by this checkpoint

### `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance`

- Lapras `Surf`: 99%, chip, active; about 14-17% vs Yanma. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Lapras `Ice Beam`: 75%, lethal, active; about 89-106% vs Yanma. natural level-up STAB/core move by this checkpoint
- Lapras `Blizzard`: 50%, lethal, active; about 112-132% vs Yanma. direct TM source is available by this checkpoint
- Lapras `Double Edge`: 50%, meaningful, active; about 30-35% vs Yanma. direct TM source is available by this checkpoint
- Machamp `Cross Chop`: 75%, major, switch; about 82-97% vs Yanma; switch fit reasonable vs Giga Drain (about 13-16% into Machamp). natural level-up STAB/core move by this checkpoint
