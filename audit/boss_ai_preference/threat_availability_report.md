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
- Wild grass, Surf-gated water, fishing tables, givepoke gifts/prizes, and listed static encounters are parsed; breeding, trades, roaming RNG, and prerequisite-heavy statics are not fully route-modeled yet.
- Likelihood buckets are review buckets, not measured player behavior.

## Checkpoints

- `falkner` (Falkner): cap 14, badges before 0, rods ['none'], surf not usable, 33 available/current-public species, 1 direct TM move(s).
- `bugsy` (Bugsy): cap 17, badges before 1, rods ['old'], surf not usable, 50 available/current-public species, 2 direct TM move(s).
- `whitney` (Whitney): cap 21, badges before 2, rods ['old'], surf not usable, 73 available/current-public species, 10 direct TM move(s).
- `morty` (Morty): cap 26, badges before 3, rods ['old'], surf not usable, 87 available/current-public species, 10 direct TM move(s).
- `chuck` (Chuck): cap 34, badges before 4, rods ['old', 'good'], surf available, 138 available/current-public species, 14 direct TM move(s).
- `jasmine` (Jasmine): cap 34, badges before 4, rods ['old', 'good'], surf available, 139 available/current-public species, 14 direct TM move(s).
- `pryce` (Pryce): cap 34, badges before 4, rods ['old', 'good'], surf available, 139 available/current-public species, 14 direct TM move(s).
- `clair` (Clair): cap 39, badges before 7, rods ['old', 'good'], surf available, 173 available/current-public species, 14 direct TM move(s).
- `champion_lance` (Champion Lance): cap 50, badges before 8, rods ['old', 'good'], surf available, 199 available/current-public species, 17 direct TM move(s).
- `koga` (Koga): cap 50, badges before 8, rods ['old', 'good'], surf available, 197 available/current-public species, 17 direct TM move(s).
- `brock` (Brock): cap 60, badges before 8, rods ['old', 'good', 'super'], surf available, 207 available/current-public species, 33 direct TM move(s).
- `misty` (Misty): cap 63, badges before 8, rods ['old', 'good', 'super'], surf available, 207 available/current-public species, 33 direct TM move(s).
- `lt_surge` (Lt. Surge): cap 65, badges before 8, rods ['old', 'good', 'super'], surf available, 207 available/current-public species, 33 direct TM move(s).
- `erika` (Erika): cap 64, badges before 8, rods ['old', 'good', 'super'], surf available, 208 available/current-public species, 33 direct TM move(s).
- `janine` (Janine): cap 64, badges before 8, rods ['old', 'good', 'super'], surf available, 207 available/current-public species, 33 direct TM move(s).
- `sabrina` (Sabrina): cap 67, badges before 8, rods ['old', 'good', 'super'], surf available, 207 available/current-public species, 33 direct TM move(s).
- `blaine` (Blaine): cap 65, badges before 8, rods ['old', 'good', 'super'], surf available, 207 available/current-public species, 33 direct TM move(s).
- `blue` (Blue): cap 69, badges before 16, rods ['old', 'good', 'super'], surf available, 209 available/current-public species, 33 direct TM move(s).

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
- Ampharos `Thunder`: 50%, lethal, active; about 90-106% vs Slowking. direct TM source is available by this checkpoint

### `clair_dragonite_vs_suicune_hidden_ice_beam`

- Suicune `Surf`: 99%, chip, active; about 9-11% vs Dragonite. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Suicune `Blizzard`: 50%, lethal, active; about 95-113% vs Dragonite. direct TM source is available by this checkpoint
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

- Starmie `Surf`: 99%, chip, active; about 28-33% vs Arcanine. revealed in the public fixture state; fixture-attested but not derivable from ROM at this checkpoint
- Starmie `Psychic`: 99%, chip, active; about 27-32% vs Arcanine. revealed in the public fixture state
- Starmie `Recover`: 99%, support, active; support/no rough damage. revealed in the public fixture state
- Starmie `Hydro Pump`: 75%, meaningful, active; about 35-42% vs Arcanine. natural level-up STAB/core move by this checkpoint
- Starmie `Dream Eater`: 50%, meaningful, active; about 29-35% vs Arcanine. direct TM source is available by this checkpoint
