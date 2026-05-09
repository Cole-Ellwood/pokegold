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
- `champion_lance` (Champion Lance): cap 50, badges before 8, rods ['old', 'good'], surf available, 205 available/current-public species, 20 direct TM move(s).
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
- Noctowl `Psychic`: 50%, meaningful, active; about 29-35% vs Haunter. natural level-up move by this checkpoint
- Quilava `Flamethrower`: 75%, lethal, switch; about 93-111% vs Haunter; switch fit risky vs Night Shade (about 29% into Quilava). natural level-up STAB/core move by this checkpoint
- Quilava `Ember`: 75%, meaningful, switch; about 51-60% vs Haunter; switch fit risky vs Night Shade (about 29% into Quilava). natural level-up STAB/core move by this checkpoint

### `chuck_poliwrath_vs_pidgeotto_ice_punch`

- Pidgeotto `Wing Attack`: 99%, chip, active; about 28-34% vs Poliwrath. revealed in the public fixture state
- Pidgeotto `Quick Attack`: 99%, chip, active; about 8-9% vs Poliwrath. revealed in the public fixture state
- Kadabra `Future Sight`: 75%, major, switch; about 61-73% vs Poliwrath; switch fit bad vs Surf (about 53-63% into Kadabra). natural level-up STAB/core move by this checkpoint

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

### `clair_dragonite_vs_suicune_hidden_ice_beam`

- Suicune `Surf`: 99%, chip, active; about 9-11% vs Dragonite. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Suicune `Blizzard`: 50%, lethal, active; about 95-113% vs Dragonite. direct TM source is available by this checkpoint
- Ampharos `Dragonbreath`: 75%, meaningful, switch; about 41-48% vs Dragonite; switch fit reasonable vs Wing Attack (about 13-16% into Ampharos). natural level-up STAB/core move by this checkpoint
- Ampharos `Twister`: 75%, chip, switch; about 28-34% vs Dragonite; switch fit reasonable vs Wing Attack (about 13-16% into Ampharos). natural level-up STAB/core move by this checkpoint
- Ampharos `Thunder`: 50%, chip, switch; about 26-31% vs Dragonite; switch fit reasonable vs Wing Attack (about 13-16% into Ampharos). legal via pre-evolution level-up path

### `clair_kingdra_vs_lapras_agility_or_attack`

- Lapras `Ice Beam`: 99%, chip, active; about 19-23% vs Kingdra. revealed in the public fixture state
- Lapras `Body Slam`: 99%, chip, active; about 10-13% vs Kingdra. revealed in the public fixture state
- Lapras `Blizzard`: 50%, chip, active; about 25-29% vs Kingdra. direct TM source is available by this checkpoint

### `koga_crobat_vs_alakazam_toxic_or_attack`

- Alakazam `Psychic`: 99%, lethal, active; about 53-62% vs Crobat. revealed in the public fixture state
- Alakazam `Recover`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Alakazam `Future Sight`: 75%, meaningful, active; about 46-55% vs Crobat. natural level-up STAB/core move by this checkpoint
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
- Meganium `Earthquake`: 50%, chip, active; about 23-28% vs Starmie. direct TM source is available by this checkpoint

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

### `falkner_pidgey_vs_charmander_mud_slap_chip`

- Charmander `Ember`: 99%, meaningful, active; about 45-55% vs Pidgey. revealed in the public fixture state
- Charmander `Scratch`: 99%, chip, active; about 21-28% vs Pidgey. revealed in the public fixture state

### `falkner_dodrio_vs_pikachu_drill_peck_or_pursuit`

- Pikachu `Thundershock`: 99%, meaningful, active; about 46-54% vs Dodrio. revealed in the public fixture state
- Pikachu `Thunder Wave`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Geodude `Rock Throw`: 75%, meaningful, switch; about 46-54% vs Dodrio; switch fit risky vs Pursuit (about 22-27% into Geodude). natural level-up STAB/core move by this checkpoint
- Bellsprout `Vine Whip`: 75%, chip, switch; about 23-27% vs Dodrio; switch fit risky vs Pursuit (about 20-25% into Bellsprout). natural level-up STAB/core move by this checkpoint

### `bugsy_scyther_vs_geodude_safe_swords_dance`

- Geodude `Tackle`: 99%, chip, active; about 9-12% vs Scyther. revealed in the public fixture state
- Geodude `Defense Curl`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Geodude `Rock Throw`: 75%, major, active; about 73-88% vs Scyther. natural level-up STAB/core move by this checkpoint

### `bugsy_butterfree_vs_pidgey_sleep_powder_or_psybeam`

- Pidgey `Quick Attack`: 99%, chip, active; about 16-19% vs Butterfree. revealed in the public fixture state
- Pidgey `Gust`: 75%, meaningful, active; about 32-39% vs Butterfree. natural level-up STAB/core move by this checkpoint

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

### `chuck_primeape_vs_machoke_intimidate_psych_up`

- Machoke `Karate Chop`: 99%, chip, active; about 25-31% vs Primeape. revealed in the public fixture state
- Machoke `Bulk Up`: 99%, support, active; support/no rough damage. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Machoke `Seismic Toss`: 75%, chip, active; about 30% vs Primeape. natural level-up STAB/core move by this checkpoint
- Machoke `Vital Throw`: 75%, chip, active; about 23-27% vs Primeape. natural level-up STAB/core move by this checkpoint
- Machoke `Fire Blast`: 50%, meaningful, active; about 41-48% vs Primeape. direct TM source is available by this checkpoint

### `chuck_machamp_vs_alakazam_rock_slide_or_low_kick`

- Alakazam `Psychic`: 99%, major, active; about 83-98% vs Machamp. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Alakazam `Recover`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Alakazam `Future Sight`: 75%, major, active; about 73-87% vs Machamp. natural level-up STAB/core move by this checkpoint
- Alakazam `Psybeam`: 75%, major, active; about 61-73% vs Machamp. natural level-up STAB/core move by this checkpoint
- Alakazam `Confusion`: 75%, meaningful, active; about 46-55% vs Machamp. natural level-up STAB/core move by this checkpoint

### `jasmine_magneton_vs_quilava_thunder_wave_or_bolt`

- Quilava `Flame Wheel`: 99%, lethal, active; about 87-103% vs Magneton. revealed in the public fixture state
- Quilava `Quick Attack`: 99%, chip, active; about 4-5% vs Magneton. revealed in the public fixture state
- Quilava `Flamethrower`: 75%, lethal, active; about 136-160% vs Magneton. natural level-up STAB/core move by this checkpoint
- Quilava `Ember`: 75%, major, active; about 72-84% vs Magneton. natural level-up STAB/core move by this checkpoint
- Quilava `Fire Blast`: 50%, lethal, active; about 198-234% vs Magneton. direct TM source is available by this checkpoint

### `pryce_piloswine_vs_typhlosion_amnesia_or_attack`

- Typhlosion `Flamethrower`: 99%, lethal, active; about 72-85% vs Piloswine. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Typhlosion `Swift`: 99%, chip, active; about 12-15% vs Piloswine. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Typhlosion `Flame Wheel`: 75%, meaningful, active; about 46-54% vs Piloswine. natural level-up STAB/core move by this checkpoint
- Typhlosion `Ember`: 75%, meaningful, active; about 38-46% vs Piloswine. natural level-up STAB/core move by this checkpoint
- Typhlosion `Fire Blast`: 50%, lethal, active; about 107-126% vs Piloswine. direct TM source is available by this checkpoint

### `clair_kingdra_vs_dragonair_dragon_dance_mirror`

- Dragonair `Outrage`: 99%, major, active; about 71-84% vs Kingdra. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Dragonair `Dragonbreath`: 75%, meaningful, active; about 44-52% vs Kingdra. natural level-up STAB/core move by this checkpoint
- Dragonair `Twister`: 75%, chip, active; about 29-34% vs Kingdra. natural level-up STAB/core move by this checkpoint
- Dragonair `Dragon Rage`: 75%, chip, active; about 30% vs Kingdra. natural level-up STAB/core move by this checkpoint
- Ampharos `Dragonbreath`: 75%, meaningful, switch; about 44-52% vs Kingdra; switch fit reasonable vs Surf (about 12-14% into Ampharos). natural level-up STAB/core move by this checkpoint

### `clair_gyarados_vs_ampharos_rest_or_attack`

- Ampharos `Thunderpunch`: 99%, chip, active; about 19-23% vs Gyarados. revealed in the public fixture state
- Ampharos `Dragonbreath`: 75%, lethal, active; about 47-56% vs Gyarados. natural level-up STAB/core move by this checkpoint
- Ampharos `Twister`: 75%, lethal, active; about 32-38% vs Gyarados. natural level-up STAB/core move by this checkpoint
- Ampharos `Thunder`: 50%, lethal, active; about 29-35% vs Gyarados. legal via pre-evolution level-up path

### `will_xatu_vs_typhlosion_psychic_or_confuse_ray`

- Typhlosion `Flamethrower`: 99%, meaningful, active; about 48-58% vs Xatu. revealed in the public fixture state
- Typhlosion `Quick Attack`: 99%, chip, active; about 8-10% vs Xatu. revealed in the public fixture state
- Typhlosion `Earthquake`: 99%, chip, active; about 0% vs Xatu. revealed in the public fixture state
- Typhlosion `Fire Blast`: 75%, major, active; about 71-84% vs Xatu. natural level-up STAB/core move by this checkpoint
- Typhlosion `Flame Wheel`: 75%, meaningful, active; about 30-36% vs Xatu. natural level-up STAB/core move by this checkpoint

### `will_slowbro_vs_houndoom_amnesia_or_surf`

- Houndoom `Crunch`: 99%, lethal, active; about 93-109% vs Slowbro. revealed in the public fixture state
- Houndoom `Bite`: 75%, major, active; about 64-75% vs Slowbro. natural level-up STAB/core move by this checkpoint
- Houndoom `Faint Attack`: 75%, major, active; about 64-75% vs Slowbro. natural level-up STAB/core move by this checkpoint
- Houndoom `Flamethrower`: 75%, chip, active; about 24-28% vs Slowbro. natural level-up STAB/core move by this checkpoint
- Houndoom `Solarbeam`: 50%, lethal, active; about 124-146% vs Slowbro. direct TM source is available by this checkpoint

### `will_jynx_vs_machamp_lovely_kiss_or_psychic`

- Machamp `Cross Chop`: 99%, lethal, active; about 120-142% vs Jynx. revealed in the public fixture state
- Machamp `Rock Slide`: 99%, meaningful, active; about 50-60% vs Jynx. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Machamp `Karate Chop`: 75%, major, active; about 81-96% vs Jynx. natural level-up STAB/core move by this checkpoint
- Machamp `Vital Throw`: 75%, major, active; about 71-83% vs Jynx. natural level-up STAB/core move by this checkpoint
- Machamp `Low Kick`: 75%, meaningful, active; about 50-60% vs Jynx. natural level-up STAB/core move by this checkpoint

### `koga_forretress_vs_typhlosion_spikes_or_explosion`

- Typhlosion `Flamethrower`: 99%, lethal, active; about 233-274% vs Forretress. revealed in the public fixture state
- Typhlosion `Fire Blast`: 75%, lethal, active; about 342-403% vs Forretress. natural level-up STAB/core move by this checkpoint
- Typhlosion `Flame Wheel`: 75%, lethal, active; about 149-175% vs Forretress. natural level-up STAB/core move by this checkpoint
- Typhlosion `Ember`: 75%, lethal, active; about 126-149% vs Forretress. natural level-up STAB/core move by this checkpoint
- Typhlosion `Fire Punch`: 50%, lethal, active; about 186-219% vs Forretress. direct TM source is available by this checkpoint

### `koga_ariados_vs_quilava_spider_web_or_attack`

- Quilava `Flame Wheel`: 99%, lethal, active; about 67-79% vs Ariados. revealed in the public fixture state
- Quilava `Quick Attack`: 99%, chip, active; about 7-10% vs Ariados. revealed in the public fixture state
- Quilava `Flamethrower`: 75%, lethal, active; about 104-122% vs Ariados. natural level-up STAB/core move by this checkpoint
- Quilava `Ember`: 75%, meaningful, active; about 56-67% vs Ariados. natural level-up STAB/core move by this checkpoint
- Quilava `Fire Blast`: 50%, lethal, active; about 152-180% vs Ariados. direct TM source is available by this checkpoint

### `bruno_machamp_vs_alakazam_rock_slide_or_cross_chop`

- Alakazam `Psychic`: 99%, lethal, active; about 93-110% vs Machamp. revealed in the public fixture state
- Alakazam `Recover`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Alakazam `Future Sight`: 75%, major, active; about 84-99% vs Machamp. natural level-up STAB/core move by this checkpoint
- Alakazam `Psybeam`: 75%, major, active; about 68-80% vs Machamp. natural level-up STAB/core move by this checkpoint
- Alakazam `Confusion`: 75%, meaningful, active; about 52-62% vs Machamp. natural level-up STAB/core move by this checkpoint

### `bruno_hitmonlee_vs_skarmory_high_jump_kick_or_brick_break`

- Skarmory `Drill Peck`: 99%, lethal, active; about 156-185% vs Hitmonlee. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Skarmory `Steel Wing`: 99%, chip, active; about 25-30% vs Hitmonlee. revealed in the public fixture state
- Skarmory `Peck`: 75%, lethal, active; about 72-86% vs Hitmonlee. natural level-up STAB/core move by this checkpoint
- Skarmory `Wing Attack`: 50%, lethal, active; about 116-137% vs Hitmonlee. direct TM source is available by this checkpoint
- Skarmory `Swift`: 50%, chip, active; about 29-34% vs Hitmonlee. natural level-up move by this checkpoint

### `bruno_onix_vs_typhlosion_sandstorm_or_explosion`

- Typhlosion `Flamethrower`: 99%, lethal, active; about 71-84% vs Onix. revealed in the public fixture state
- Typhlosion `Earthquake`: 99%, lethal, active; about 44-53% vs Onix. revealed in the public fixture state
- Typhlosion `Fire Blast`: 75%, lethal, active; about 103-122% vs Onix. natural level-up STAB/core move by this checkpoint
- Typhlosion `Flame Wheel`: 75%, lethal, active; about 44-53% vs Onix. natural level-up STAB/core move by this checkpoint
- Typhlosion `Ember`: 75%, lethal, active; about 37-44% vs Onix. natural level-up STAB/core move by this checkpoint

### `karen_houndoom_vs_alakazam_pursuit_or_flamethrower`

- Alakazam `Psychic`: 99%, chip, active; about 0% vs Houndoom. revealed in the public fixture state
- Alakazam `Dynamicpunch`: 50%, meaningful, active; about 45-53% vs Houndoom. direct TM source is available by this checkpoint
- Alakazam `Hyper Beam`: 50%, meaningful, active; about 39-47% vs Houndoom. direct TM source is available by this checkpoint
- Alakazam `Zap Cannon`: 50%, meaningful, active; about 39-46% vs Houndoom. direct TM source is available by this checkpoint
- Alakazam `Thunderpunch`: 50%, chip, active; about 28-34% vs Houndoom. direct TM source is available by this checkpoint

### `karen_umbreon_vs_dragonite_curse_or_toxic`

- Dragonite `Outrage`: 99%, meaningful, active; about 39-47% vs Umbreon. revealed in the public fixture state
- Dragonite `Wing Attack`: 75%, meaningful, active; about 31-37% vs Umbreon. natural level-up STAB/core move by this checkpoint
- Dragonite `Dynamicpunch`: 50%, meaningful, active; about 53-62% vs Umbreon. direct TM source is available by this checkpoint
- Dragonite `Hyper Beam`: 50%, meaningful, active; about 47-55% vs Umbreon. legal via pre-evolution level-up path
- Dragonite `Double Edge`: 50%, meaningful, active; about 34-40% vs Umbreon. direct TM source is available by this checkpoint

### `karen_gengar_vs_snorlax_destiny_bond_or_thunderbolt`

- Snorlax `Body Slam`: 99%, chip, active; about 0% vs Gengar. revealed in the public fixture state
- Snorlax `Earthquake`: 99%, chip, active; about 0% vs Gengar. revealed in the public fixture state
- Snorlax `Shadow Ball`: 50%, lethal, active; about 172-203% vs Gengar. direct TM source is available by this checkpoint
- Snorlax `Solarbeam`: 50%, lethal, active; about 50-59% vs Gengar. direct TM source is available by this checkpoint
- Snorlax `Fire Blast`: 50%, lethal, active; about 38-46% vs Gengar. direct TM source is available by this checkpoint

### `lance_dragonite_vs_aerodactyl_thunder_or_outrage`

- Aerodactyl `Rock Slide`: 99%, meaningful, active; about 51-60% vs Dragonite. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Aerodactyl `Ancientpower`: 75%, meaningful, active; about 40-48% vs Dragonite. natural level-up STAB/core move by this checkpoint
- Aerodactyl `Hyper Beam`: 50%, chip, active; about 26-31% vs Dragonite. natural level-up move by this checkpoint
- Zapdos `Thunderbolt`: 75%, chip, switch; about 25-30% vs Dragonite. natural level-up STAB/core move by this checkpoint
- Zapdos `Drill Peck`: 75%, chip, switch; about 23-28% vs Dragonite. natural level-up STAB/core move by this checkpoint

### `lance_aerodactyl_vs_porygon2_rock_slide_or_ancient_power`

- Porygon2 `Tri Attack`: 99%, chip, active; about 15-18% vs Aerodactyl. revealed in the public fixture state
- Porygon2 `Recover`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Porygon2 `Blizzard`: 50%, lethal, active; about 76-90% vs Aerodactyl. direct TM source is available by this checkpoint
- Porygon2 `Thunder`: 50%, lethal, active; about 76-90% vs Aerodactyl. direct TM source is available by this checkpoint
- Porygon2 `Zap Cannon`: 50%, lethal, active; about 65-76% vs Aerodactyl. natural level-up move by this checkpoint

### `lance_charizard_vs_milotic_fire_blast_or_solarbeam`

- Milotic `Surf`: 99%, support, active; support/no rough damage. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Snorlax `Body Slam`: 75%, meaningful, switch; about 38-45% vs Charizard; switch fit risky vs Wing Attack (about 25-29% into Snorlax). natural level-up STAB/core move by this checkpoint
- Snorlax `Headbutt`: 75%, meaningful, switch; about 36-42% vs Charizard; switch fit risky vs Wing Attack (about 25-29% into Snorlax). natural level-up STAB/core move by this checkpoint
- Snorlax `Double Edge`: 50%, major, switch; about 65-77% vs Charizard; switch fit risky vs Wing Attack (about 25-29% into Snorlax). direct TM source is available by this checkpoint
- Snorlax `Thunder`: 50%, meaningful, switch; about 45-53% vs Charizard; switch fit risky vs Wing Attack (about 25-29% into Snorlax). direct TM source is available by this checkpoint

### `red_pikachu_vs_dragonite_thunderbolt_or_quick_attack`

- Dragonite `Outrage`: 99%, lethal, active; about 152-180% vs Pikachu. revealed in the public fixture state
- Dragonite `Dragonbreath`: 75%, major, active; about 62-73% vs Pikachu. natural level-up STAB/core move by this checkpoint
- Dragonite `Wing Attack`: 75%, major, active; about 61-72% vs Pikachu. natural level-up STAB/core move by this checkpoint
- Dragonite `Twister`: 75%, meaningful, active; about 42-49% vs Pikachu. natural level-up STAB/core move by this checkpoint
- Dragonite `Hyper Beam`: 50%, lethal, active; about 183-215% vs Pikachu. legal via pre-evolution level-up path

### `red_snorlax_vs_alakazam_amnesia_or_body_slam`

- Alakazam `Psychic`: 99%, chip, active; about 28-33% vs Snorlax. revealed in the public fixture state
- Alakazam `Recover`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Alakazam `Future Sight`: 75%, chip, active; about 25-30% vs Snorlax. natural level-up STAB/core move by this checkpoint
- Alakazam `Dream Eater`: 50%, meaningful, active; about 31-37% vs Snorlax. direct TM source is available by this checkpoint
- Alakazam `Dynamicpunch`: 50%, chip, active; about 25-30% vs Snorlax. direct TM source is available by this checkpoint

### `red_charizard_vs_starmie_fire_blast_or_wing_attack`

- Starmie `Surf`: 99%, lethal, active; about 82-96% vs Charizard. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Starmie `Hydro Pump`: 75%, lethal, active; about 104-122% vs Charizard. natural level-up STAB/core move by this checkpoint
- Starmie `Bubblebeam`: 75%, meaningful, active; about 57-67% vs Charizard. natural level-up STAB/core move by this checkpoint
- Starmie `Psychic`: 75%, meaningful, active; about 39-46% vs Charizard. natural level-up STAB/core move by this checkpoint
- Starmie `Thunder`: 50%, major, active; about 69-81% vs Charizard. direct TM source is available by this checkpoint

### `lance_dragonite_vs_steelix_fire_blast_or_thunder`

- Steelix `Rock Slide`: 99%, meaningful, active; about 32-38% vs Dragonite. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Steelix `Earthquake`: 99%, chip, active; about 7-8% vs Dragonite. revealed in the public fixture state
- Steelix `Iron Tail`: 75%, chip, active; about 27-32% vs Dragonite. natural level-up STAB/core move by this checkpoint
- Steelix `Dragonbreath`: 75%, chip, active; about 22-26% vs Dragonite. natural level-up STAB/core move by this checkpoint
- Steelix `Rock Throw`: 50%, chip, active; about 22-26% vs Dragonite. natural level-up move by this checkpoint
