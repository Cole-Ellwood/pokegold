# Data Rebalance Manifest (Data Layer Only)

This file tracks data-table rebalance history (move params, Pokemon base stats, Pokemon types, level-up learnsets).
It is no longer a complete release manifest for the current project state.
`docs/CHANGES.txt` is generated from this file by `scripts/export_changes_from_manifest.py`.
`docs/CHANGES_BY_CATEGORY.txt` is generated from this file by `scripts/export_changes_by_category.py`.
`docs/RELEASE_NOTES.md` is a hand-written final summary and is not generated from this file.

## Moves

- `CUT`: `power 50 -> 60`, `accuracy 95 -> 100`, `pp 30 -> 30`, `type NORMAL -> NORMAL`, `effect EFFECT_NORMAL_HIT -> EFFECT_NORMAL_HIT`
- `FIRE_SPIN`: `power 15 -> 25`, `accuracy 70 -> 85`, `pp 15 -> 10`, `type FIRE -> FIRE`, `effect EFFECT_TRAP_TARGET -> EFFECT_TRAP_TARGET`
- `MUD_SLAP`: `power 20 -> 30`, `accuracy 100 -> 100`, `pp 10 -> 10`, `type GROUND -> GROUND`, `effect EFFECT_ACCURACY_DOWN_HIT -> EFFECT_ACCURACY_DOWN_HIT`

### Batch 3

- `SOLARBEAM`: `power 120 -> 180`
- `GIGA_DRAIN`: `power 60 -> 75`, `pp 5 -> 25`
- `FIRE_BLAST`: `power 120 -> 140`, `pp 5 -> 10`
- `CROSS_CHOP`: `power 100 -> 120`, `pp 5 -> 20`

## Pokemon base stats

- `MEGANIUM`: `HP 80 -> 85`, `Atk 82 -> 88`, `Def 100 -> 105`, `Spd 80 -> 82`, `SpAtk 83 -> 90`, `SpDef 100 -> 105`
- `TYPHLOSION`: `HP 78 -> 78`, `Atk 84 -> 92`, `Def 78 -> 80`, `Spd 100 -> 103`, `SpAtk 109 -> 114`, `SpDef 85 -> 90`
- `FERALIGATR`: `HP 85 -> 88`, `Atk 105 -> 112`, `Def 100 -> 103`, `Spd 78 -> 82`, `SpAtk 79 -> 84`, `SpDef 83 -> 88`

### Batch 1

- `MEGANIUM`: `HP 85 -> 115`, `Def 105 -> 135`, `SpD 105 -> 135`
- `TYPHLOSION`: `SpA 114 -> 145`, `Spe 103 -> 123`
- `FERALIGATR`: `Atk 112 -> 127`, `SpA 84 -> 125`
- `SENTRET`: `HP 35 -> 85`, `Atk 46 -> 76`
- `FURRET`: `HP 85 -> 130`, `Atk 76 -> 126`, `Def 64 -> 80`, `SpD 55 -> 80`, `Spe 90 -> 40`
- `HOOTHOOT`: `SpA 36 -> 66`, `Spe 50 -> 90`
- `NOCTOWL`: `HP 100 -> 80`, `SpA 76 -> 116`, `Spe 70 -> 125`
- `LEDYBA`: `HP 40 -> 60`, `Def 30 -> 100`
- `LEDIAN`: `HP 55 -> 70`, `Atk 35 -> 100`, `Spe 85 -> 145`
- `ARIADOS`: `HP 70 -> 110`, `Atk 90 -> 115`, `Def 70 -> 100`
- `BELLSPROUT`: `Spe 40 -> 70`
- `WEEPINBELL`: `HP 65 -> 80`, `Spe 55 -> 85`
- `VICTREEBEL`: `HP 80 -> 90`, `Atk 105 -> 145`, `Def 65 -> 50`, `SpA 100 -> 140`, `SpD 60 -> 45`, `Spe 70 -> 110`
- `DUNSPARCE`: `HP 100 -> 180`, `Atk 70 -> 140`, `Def 70 -> 130`, `Spe 45 -> 15`


### Batch 2

- `TOGETIC`: `Atk 40 -> 110`, `Spe 40 -> 140`
- `GASTLY`: `HP 30 -> 40`, `Spe 80 -> 120`
- `HAUNTER`: `Atk 50 -> 70`, `SpA 115 -> 125`, `Spe 95 -> 135`
- `PIDGEOTTO`: `HP 63 -> 93`, `Atk 60 -> 90`
- `PIDGEOT`: `HP 83 -> 113`, `Atk 80 -> 110`
- `FLAAFFY`: `HP 70 -> 100`, `Def 55 -> 85`, `SpD 60 -> 90`
- `AMPHAROS`: `HP 90 -> 120`, `Def 75 -> 105`, `SpA 115 -> 145`, `SpD 90 -> 120`
- `HOPPIP`: `Atk 35 -> 65`, `SpA 35 -> 65`
- `SKIPLOOM`: `HP 55 -> 80`, `Def 50 -> 100`, `SpD 65 -> 115`, `Spe 80 -> 40`
- `JUMPLUFF`: `HP 75 -> 85`, `Atk 55 -> 105`, `SpA 55 -> 125`, `Spe 110 -> 150`
- `WOOPER`: `HP 55 -> 105`
- `QUAGSIRE`: `HP 95 -> 145`, `Atk 85 -> 125`, `SpA 65 -> 105`
- `QWILFISH`: `Def 75 -> 150`, `SpA 55 -> 95`
- `NATU`: `SpA 70 -> 110`
- `XATU`: `SpA 95 -> 140`, `SpD 70 -> 100`
- `UNOWN`: `HP 48 -> 148`, `Atk 72 -> 102`, `SpA 72 -> 102`
- `KOFFING`: `HP 40 -> 60`, `Atk 65 -> 85`, `SpA 60 -> 80`
- `WEEZING`: `HP 65 -> 105`, `Atk 90 -> 120`, `SpA 85 -> 125`
- `SCYTHER`: `HP 70 -> 90`, `Atk 110 -> 140`
- `ZUBAT`: `HP 40 -> 60`, `Atk 45 -> 65`
- `GOLBAT`: `HP 75 -> 95`, `Atk 80 -> 100`, `Def 70 -> 90`

### Batch 4

- `MILTANK`: `HP 95 -> 125`, `Atk 80 -> 110`, `Def 105 -> 135`, `Spe 100 -> 40`, `SpA 40 -> 40`, `SpD 70 -> 30`
- `CLEFAIRY`: `HP 70 -> 70`, `Atk 45 -> 75`, `Def 48 -> 48`, `Spe 35 -> 35`, `SpA 60 -> 60`, `SpD 65 -> 65`
- `YANMA`: `HP 65 -> 65`, `Atk 65 -> 125`, `Def 45 -> 45`, `Spe 95 -> 140`, `SpA 75 -> 75`, `SpD 45 -> 45`
- `SUDOWOODO`: `HP 70 -> 130`, `Atk 100 -> 150`, `Def 115 -> 145`, `Spe 30 -> 30`, `SpA 30 -> 30`, `SpD 65 -> 65`
- `SHUCKLE`: `HP 20 -> 100`, `Atk 10 -> 10`, `Def 230 -> 230`, `Spe 5 -> 5`, `SpA 10 -> 10`, `SpD 230 -> 230`
- `STANTLER`: `HP 73 -> 108`, `Atk 95 -> 135`, `Def 62 -> 82`, `Spe 85 -> 60`, `SpA 85 -> 85`, `SpD 65 -> 80`
- `MAGNEMITE`: `HP 25 -> 70`, `Atk 35 -> 135`, `Def 70 -> 100`, `Spe 45 -> 30`, `SpA 95 -> 125`, `SpD 55 -> 40`
- `MAGNETON`: `HP 50 -> 90`, `Atk 60 -> 160`, `Def 95 -> 135`, `Spe 70 -> 50`, `SpA 120 -> 150`, `SpD 70 -> 70`
- `GENGAR`: `HP 60 -> 110`, `Atk 65 -> 135`, `Def 60 -> 90`, `Spe 110 -> 110`, `SpA 130 -> 130`, `SpD 75 -> 75`
- `SNUBBULL`: `HP 60 -> 100`, `Atk 80 -> 130`, `Def 50 -> 80`, `Spe 30 -> 30`, `SpA 40 -> 40`, `SpD 40 -> 40`
- `CHINCHOU`: `HP 75 -> 75`, `Atk 38 -> 38`, `Def 38 -> 38`, `Spe 67 -> 67`, `SpA 56 -> 96`, `SpD 56 -> 56`
- `LANTURN`: `HP 125 -> 145`, `Atk 58 -> 58`, `Def 58 -> 108`, `Spe 67 -> 67`, `SpA 76 -> 126`, `SpD 76 -> 96`
- `MANTINE`: `HP 65 -> 105`, `Atk 40 -> 80`, `Def 70 -> 70`, `Spe 70 -> 100`, `SpA 80 -> 80`, `SpD 140 -> 140`
- `CORSOLA`: `HP 55 -> 55`, `Atk 55 -> 125`, `Def 85 -> 85`, `Spe 35 -> 35`, `SpA 65 -> 135`, `SpD 85 -> 85`
- `PRIMEAPE`: `HP 65 -> 105`, `Atk 105 -> 125`, `Def 60 -> 60`, `Spe 95 -> 145`, `SpA 60 -> 60`, `SpD 70 -> 70`
- `POLIWRATH`: `HP 90 -> 150`, `Atk 85 -> 85`, `Def 95 -> 145`, `Spe 70 -> 50`, `SpA 70 -> 70`, `SpD 90 -> 50`
- `STEELIX`: `HP 75 -> 135`, `Atk 85 -> 135`, `Def 200 -> 200`, `Spe 30 -> 30`, `SpA 55 -> 55`, `SpD 65 -> 45`
- `GIRAFARIG`: `HP 70 -> 40`, `Atk 80 -> 120`, `Def 65 -> 65`, `Spe 85 -> 85`, `SpA 90 -> 130`, `SpD 65 -> 65`
- `RATTATA`: `HP 30 -> 15`, `Atk 56 -> 96`, `Def 35 -> 35`, `Spe 72 -> 72`, `SpA 25 -> 25`, `SpD 35 -> 35`
- `RATICATE`: `HP 55 -> 25`, `Atk 81 -> 145`, `Def 60 -> 60`, `Spe 97 -> 97`, `SpA 50 -> 50`, `SpD 70 -> 70`
- `ARBOK`: `HP 60 -> 120`, `Atk 85 -> 85`, `Def 69 -> 109`, `Spe 80 -> 80`, `SpA 65 -> 65`, `SpD 79 -> 79`
- `GLOOM`: `HP 60 -> 60`, `Atk 65 -> 85`, `Def 70 -> 70`, `Spe 40 -> 40`, `SpA 85 -> 105`, `SpD 75 -> 75`
- `MURKROW`: `HP 60 -> 140`, `Atk 85 -> 135`, `Def 42 -> 42`, `Spe 91 -> 191`, `SpA 85 -> 135`, `SpD 42 -> 42`
- `SEEL`: `HP 65 -> 95`, `Atk 45 -> 85`, `Def 55 -> 55`, `Spe 45 -> 45`, `SpA 45 -> 85`, `SpD 70 -> 70`
- `DEWGONG`: `HP 90 -> 140`, `Atk 70 -> 110`, `Def 80 -> 80`, `Spe 70 -> 70`, `SpA 70 -> 110`, `SpD 95 -> 95`
- `PILOSWINE`: `HP 100 -> 180`, `Atk 100 -> 100`, `Def 80 -> 160`, `Spe 50 -> 50`, `SpA 60 -> 60`, `SpD 60 -> 140`


### Batch 5

- `GRIMER`: `HP 80 -> 80`, `Atk 80 -> 100`, `Def 50 -> 50`, `Spe 25 -> 25`, `SpA 40 -> 40`, `SpD 50 -> 50`
- `MUK`: `HP 105 -> 135`, `Atk 105 -> 135`, `Def 75 -> 75`, `Spe 50 -> 50`, `SpA 65 -> 65`, `SpD 100 -> 100`
- `SNEASEL`: `HP 55 -> 25`, `Atk 95 -> 155`, `Def 55 -> 55`, `Spe 115 -> 160`, `SpA 35 -> 135`, `SpD 75 -> 75`
- `VILEPLUME`: `HP 75 -> 150`, `Atk 80 -> 130`, `Def 85 -> 115`, `Spe 50 -> 100`, `SpA 100 -> 150`, `SpD 90 -> 130`
- `HOUNDOUR`: `HP 45 -> 85`, `Atk 60 -> 60`, `Def 30 -> 30`, `Spe 65 -> 65`, `SpA 80 -> 110`, `SpD 50 -> 90`
- `HOUNDOOM`: `HP 75 -> 115`, `Atk 90 -> 90`, `Def 50 -> 50`, `Spe 95 -> 95`, `SpA 110 -> 140`, `SpD 80 -> 125`
- `DRAGONAIR`: `HP 61 -> 111`, `Atk 84 -> 84`, `Def 65 -> 95`, `Spe 70 -> 55`, `SpA 70 -> 110`, `SpD 70 -> 85`
- `KINGDRA`: `HP 75 -> 150`, `Atk 95 -> 135`, `Def 95 -> 135`, `Spe 85 -> 65`, `SpA 95 -> 125`, `SpD 95 -> 135`
- `DRATINI`: `HP 41 -> 91`, `Atk 64 -> 64`, `Def 45 -> 75`, `Spe 50 -> 50`, `SpA 50 -> 100`, `SpD 50 -> 50`
- `GLIGAR`: `HP 65 -> 125`, `Atk 75 -> 95`, `Def 105 -> 135`, `Spe 85 -> 85`, `SpA 35 -> 35`, `SpD 65 -> 115`
- `URSARING`: `HP 90 -> 130`, `Atk 130 -> 160`, `Def 75 -> 75`, `Spe 55 -> 55`, `SpA 75 -> 75`, `SpD 75 -> 75`
- `EXEGGUTOR`: `HP 95 -> 125`, `Atk 95 -> 95`, `Def 85 -> 135`, `Spe 55 -> 55`, `SpA 125 -> 175`, `SpD 65 -> 85`
- `SLOWBRO`: `HP 95 -> 135`, `Atk 75 -> 75`, `Def 110 -> 190`, `Spe 30 -> 30`, `SpA 100 -> 100`, `SpD 80 -> 160`
- `JYNX`: `HP 65 -> 65`, `Atk 50 -> 120`, `Def 35 -> 35`, `Spe 95 -> 95`, `SpA 115 -> 145`, `SpD 95 -> 155`
- `VENOMOTH`: `HP 70 -> 110`, `Atk 65 -> 65`, `Def 60 -> 60`, `Spe 90 -> 150`, `SpA 90 -> 90`, `SpD 75 -> 75`
- `FORRETRESS`: `HP 75 -> 105`, `Atk 90 -> 160`, `Def 140 -> 140`, `Spe 40 -> 40`, `SpA 60 -> 60`, `SpD 60 -> 40`
- `CROBAT`: `HP 85 -> 145`, `Atk 90 -> 60`, `Def 80 -> 80`, `Spe 130 -> 170`, `SpA 70 -> 70`, `SpD 80 -> 80`
- `HITMONTOP`: `HP 50 -> 50`, `Atk 95 -> 165`, `Def 95 -> 95`, `Spe 70 -> 70`, `SpA 35 -> 65`, `SpD 110 -> 170`
- `HITMONLEE`: `HP 50 -> 50`, `Atk 120 -> 150`, `Def 53 -> 53`, `Spe 87 -> 137`, `SpA 35 -> 35`, `SpD 110 -> 110`
- `HITMONCHAN`: `HP 50 -> 70`, `Atk 105 -> 125`, `Def 79 -> 79`, `Spe 76 -> 76`, `SpA 35 -> 135`, `SpD 110 -> 110`
- `ONIX`: `HP 35 -> 135`, `Atk 45 -> 115`, `Def 160 -> 160`, `Spe 70 -> 30`, `SpA 30 -> 30`, `SpD 45 -> 45`
- `MACHAMP`: `HP 90 -> 150`, `Atk 130 -> 130`, `Def 80 -> 110`, `Spe 55 -> 55`, `SpA 65 -> 65`, `SpD 85 -> 125`
- `UMBREON`: `HP 95 -> 115`, `Atk 65 -> 65`, `Def 110 -> 140`, `Spe 65 -> 65`, `SpA 60 -> 60`, `SpD 130 -> 170`
- `GYARADOS`: `HP 95 -> 125`, `Atk 125 -> 145`, `Def 79 -> 79`, `Spe 81 -> 81`, `SpA 60 -> 100`, `SpD 100 -> 100`
- `CHARIZARD`: `HP 78 -> 78`, `Atk 84 -> 124`, `Def 78 -> 78`, `Spe 100 -> 100`, `SpA 109 -> 149`, `SpD 85 -> 85`
- `AERODACTYL`: `HP 80 -> 80`, `Atk 105 -> 145`, `Def 65 -> 65`, `Spe 130 -> 130`, `SpA 60 -> 60`, `SpD 75 -> 75`
- `DRAGONITE`: `HP 91 -> 161`, `Atk 134 -> 154`, `Def 95 -> 125`, `Spe 80 -> 20`, `SpA 100 -> 140`, `SpD 100 -> 140`

## Pokemon types

- `TYPHLOSION`: `FIRE/FIRE -> FIRE/NORMAL`
- `FERALIGATR`: `WATER/WATER -> WATER/DARK`

### Batch 1

- `MEGANIUM`: `GRASS/GRASS -> GRASS/NORMAL`
- `FERALIGATR`: `WATER/DARK -> WATER/FIGHTING`


### Batch 2

- `GASTLY`: `GHOST/POISON -> GHOST/PSYCHIC_TYPE`
- `HAUNTER`: `GHOST/POISON -> GHOST/PSYCHIC_TYPE`
- `GENGAR`: `GHOST/POISON -> GHOST/PSYCHIC_TYPE`
- `AMPHAROS`: `ELECTRIC/ELECTRIC -> ELECTRIC/DRAGON`
- `SKIPLOOM`: `GRASS/FLYING -> GRASS/STEEL`
- `KOFFING`: `POISON/POISON -> POISON/DARK`
- `WEEZING`: `POISON/POISON -> POISON/DARK`

### Dragon package

- `ARCANINE`: `FIRE/FIRE -> FIRE/DRAGON`
- `GYARADOS`: `WATER/FLYING -> WATER/DRAGON`

### Batch 3

- `BAYLEEF`: `GRASS/GRASS -> GRASS/NORMAL`

## Learnsets

- `MEGANIUM` level-up: `Lv51 SAFEGUARD -> Lv51 EARTHQUAKE`
- `TYPHLOSION` level-up: `Lv45 SWIFT -> Lv45 THUNDERPUNCH`
- `FERALIGATR` level-up: `Lv47 SCREECH -> Lv47 CRUNCH`

### Dragon package

- `DRATINI`: add `Lv32 DRAGONBREATH`; keeps `Lv50 OUTRAGE`
- `DRAGONAIR`: add `Lv32 DRAGONBREATH`; keeps `Lv56 OUTRAGE`
- `DRAGONITE`: add `Lv32 DRAGONBREATH`; keeps `Lv61 OUTRAGE`
- `GYARADOS`: `Lv35 TWISTER -> Lv35 DRAGONBREATH`; add `Lv50 OUTRAGE`
- `ARCANINE`: add `Lv42 DRAGONBREATH`, `Lv55 OUTRAGE`
- `AMPHAROS`: keeps `Lv42 DRAGONBREATH`; add `Lv57 OUTRAGE`
- `KINGDRA`: add `Lv40 DRAGONBREATH`, `Lv55 OUTRAGE`

### Batch 3

- `BAYLEEF` level-up: `Lv17 SUBSTITUTE absent -> present`, `Lv17 LEECH_SEED absent -> present`, `Lv17 GIGA_DRAIN absent -> present`, `Lv21 SOLARBEAM absent -> present`
- `QUILAVA` level-up: `Lv20 FLAMETHROWER absent -> present`
- `TYPHLOSION` level-up: `Lv37 FIRE_BLAST absent -> present`
- `TOTODILE` level-up: `Lv13 WATER_GUN -> Lv13 SURF`
- `CROCONAW` level-up: `Lv28 SCARY_FACE -> Lv28 CROSS_CHOP`

### Level-up order cleanup

- Reordered 24 level-up rows back into increasing-level order without changing
  any move levels or move identities. This restores the table invariant used by
  `FillMoves` when generating a Pokemon's current moves from species and level.

### Ariados utility pass

- `ARIADOS` level-up: add `Lv22 SPIKES`; `Lv43 SPIDER_WEB -> Lv37 SPIDER_WEB`.

### Yanma utility pass

- `YANMA` level-up: `Lv19 LEECH_LIFE -> Lv17 LEECH_LIFE`.

## Scope note

- This document covers only data-layer diffs.
- Current release scope includes engine, AI, and script/map behavior changes.
- See `docs/mechanics_changes_from_base.md` and `docs/RELEASE_NOTES.md` for full release scope.
