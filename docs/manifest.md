# Data Rebalance Manifest

This hack only edits existing data tables: move params, Pokemon base stats, Pokemon types, and level-up learnsets.

## Moves

- `CUT`: `power 50 -> 60`, `accuracy 95 -> 100`, `pp 30 -> 30`, `type NORMAL -> NORMAL`, `effect EFFECT_NORMAL_HIT -> EFFECT_NORMAL_HIT`
- `FIRE_SPIN`: `power 15 -> 25`, `accuracy 70 -> 85`, `pp 15 -> 10`, `type FIRE -> FIRE`, `effect EFFECT_TRAP_TARGET -> EFFECT_TRAP_TARGET`
- `MUD_SLAP`: `power 20 -> 30`, `accuracy 100 -> 100`, `pp 10 -> 10`, `type GROUND -> GROUND`, `effect EFFECT_ACCURACY_DOWN_HIT -> EFFECT_ACCURACY_DOWN_HIT`

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

## Pokemon types

- `TYPHLOSION`: `FIRE/FIRE -> FIRE/NORMAL`
- `FERALIGATR`: `WATER/WATER -> WATER/DARK`

### Batch 1

- `MEGANIUM`: `GRASS/GRASS -> GRASS/NORMAL`
- `FERALIGATR`: `WATER/DARK -> WATER/FIGHTING`

## Learnsets

- `MEGANIUM` level-up: `Lv51 SAFEGUARD -> Lv51 EARTHQUAKE`
- `TYPHLOSION` level-up: `Lv45 SWIFT -> Lv45 THUNDERPUNCH`
- `FERALIGATR` level-up: `Lv47 SCREECH -> Lv47 CRUNCH`

## Scope confirmation

- No new moves, no new move effects, no new mechanics, no new type IDs.
- No map/script/text changes.
- No engine code changes.
