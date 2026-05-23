# Developer ROM Index

Boss AI cognition note: if you are here for the Boss AI loop, think wildly in the journal before changing source; this index is the hard memory/bank reality check for those ideas.

Generated: 2026-05-23
ROM target: `pokegold`

Generated from `layout.link`, assembly sources, `pokegold.map`, and `pokegold.sym`.

Bank numbers are hexadecimal unless noted otherwise.

Read `docs/README.md` first for helper-doc routing, then `docs/project_context.md` for design intent. This file is for navigation and memory planning only; it does not add anything to the ROM.

## How To Use This Index

1. Start with Quick Lookup for the subsystem you are changing.
2. Use the anchor labels to jump from behavior to current bank/address and source line.
3. Check Memory Summary and Tight Banks before adding code or data.
4. Use Largest ROMX Free Ranges when moving optional code out of crowded banks.
5. Refresh this file after a successful build changes linker outputs.

## Quick Lookup

### Developer docs and review workflow
- Intent: Project intent, review order, bug-hunt checklist, and generated lookup.
- Start here: `docs/README.md`, `docs/project_context.md`, `docs/review_playbook.md`, `docs/project_map.md`, `docs/boss_ai_spec.md`, `docs/generated/dev_index.md`, `scripts/generate_dev_index.py`

### Boss AI and trainer difficulty
- Intent: Human-like major fights, no hidden-information cheating outside authored Haki.
- Start here: `engine/battle/ai/boss_platform.asm`, `engine/battle/ai/boss_policy_move.asm`, `engine/battle/ai/boss_policy_switch.asm`, `engine/battle/ai/boss_thunks.asm`, `engine/battle/ai/move.asm`, `engine/battle/ai/scoring.asm`, `engine/battle/ai/items.asm`, `engine/battle/ai/switch.asm`, `engine/battle/core.asm`, `engine/battle/used_move_text.asm`, `engine/battle/read_trainer_attributes.asm`, `data/trainers/ai_tiers.asm`
- Anchors: `BossAI_IncrementTurnsElapsed` (0e:454d, `engine/battle/ai/boss_platform.asm:24`); `BossAI_RecordPlayerSwitch` (0e:45db, `engine/battle/ai/boss_platform.asm:126`); `BossAI_SelectMove` (0e:57bf, `engine/battle/ai/boss_policy_move.asm:2677`); `BossAI_SwitchOrTryItem` (0e:58b1, `engine/battle/ai/boss_policy_switch.asm:17`); `BossAI_ComputeSwitchConfidence` (0e:6540, `engine/battle/ai/boss_policy_switch.asm:751`); `BossAI_PredictPlayerSwitch` (0e:65c3, `engine/battle/ai/boss_policy_move.asm:3605`); `BossAI_RecordRevealedPlayerMove` (0e:4717, `engine/battle/ai/boss_platform.asm:260`); `BossAI_CurrentEnemyMoveHasKOPressure` (0e:6025, `engine/battle/ai/boss_policy_move.asm:3043`); `BossAI_CurrentEnemyMovePressureScore` (0e:604d, `engine/battle/ai/boss_policy_move.asm:3077`); `BossAI_PlayerHasPublicThreatVsEnemy` (0e:5e8e, `engine/battle/ai/boss_policy_move.asm:2885`); `BossAI_PublicEnemyFaster` (0e:62e9, `engine/battle/ai/boss_policy_move.asm:3530`); `BossAI_CheckAbleToSwitchSafe` (0e:5a4e, `engine/battle/ai/boss_policy_switch.asm:298`); `BossAI_RefineSwitchCandidateForPlausibleRisk` (0e:748d, `engine/battle/ai/boss_policy_switch.asm:833`); `BossAI_ApplyPlausibleRiskToSwitchConfidence` (0e:76c1, `engine/battle/ai/boss_policy_switch.asm:1216`)

### Battle mechanics
- Intent: Shared damage, status, switching, item, and turn-flow rules.
- Start here: `engine/battle/core.asm`, `engine/battle/effect_commands.asm`, `engine/battle/type_passive_damage_mods.asm`, `engine/battle/late_gen_held_items.asm`, `engine/battle/move_effects`, `constants/battle_constants.asm`
- Anchors: `TypePassive_ApplyDamageModifiers_Far` (11:69c9, `engine/battle/type_passive_damage_mods.asm:44`); `TypePassive_TryDarkStatusShield_Far` (11:6f4e, `engine/battle/type_passive_damage_mods.asm:1069`); `TypePassive_MaybePoisonRetaliation_Far` (11:6fab, `engine/battle/type_passive_damage_mods.asm:1135`); `ApplyLateGenDamageMultipliers_Far` (11:655f, `engine/battle/late_gen_held_items.asm:183`); `HandleLateGenAfterHitEffects_Far` (11:6618, `engine/battle/late_gen_held_items.asm:301`); `TryActivateDittoImposter` (01:799b, `engine/battle/ditto_imposter.asm:1`)

### Moves
- Intent: Move stats, effects, descriptions, contact flags, and animations.
- Start here: `data/moves/moves.asm`, `data/moves/effects.asm`, `data/moves/effects_pointers.asm`, `data/moves/contact_flags.asm`, `data/moves/descriptions.asm`, `constants/move_constants.asm`
- Anchors: `Moves` (10:5aaa, `data/moves/moves.asm:14`); `MoveEffects` (09:7489, `data/moves/effects.asm:3`); `MoveContactFlags` (11:712c, `data/moves/contact_flags.asm:4`); `Spikes` (09:79a5, `data/moves/effects.asm:1525`); `RapidSpin` (09:7a7a, `data/moves/effects.asm:1772`)

### Items and held items
- Intent: Item data, descriptions, pockets, marts, and battle held effects.
- Start here: `data/items/attributes.asm`, `data/items/descriptions.asm`, `data/items/names.asm`, `data/items/marts.asm`, `engine/items`, `engine/battle/late_gen_held_items.asm`
- Anchors: `ItemAttributes` (01:68ba, `data/items/attributes.asm:8`); `ItemDescriptions` (6e:4000, `data/items/descriptions.asm:1`); `ItemNames` (6c:4000, `data/items/names.asm:1`); `IsChoiceHeldEffect_Far` (11:6910, `engine/battle/late_gen_held_items.asm:819`); `IsMoveBlockedByAssaultVest_Far` (11:6919, `engine/battle/late_gen_held_items.asm:827`)

### Pokemon data and weak-Pokemon buffs
- Intent: Base stats, types, level-up moves, evolutions, egg moves, and names.
- Start here: `data/pokemon/base_stats.asm`, `data/pokemon/base_stats`, `data/pokemon/evos_attacks.asm`, `data/pokemon/evos_attacks_pointers.asm`, `data/pokemon/egg_moves.asm`, `constants/pokemon_constants.asm`
- Anchors: `BaseData` (14:5ab9, `data/pokemon/base_stats.asm:21`); `EvosAttacksPointers` (10:685c, `data/pokemon/evos_attacks_pointers.asm:3`); `EggMovePointers` (08:79f0, `data/pokemon/egg_move_pointers.asm:1`)

### Maps, events, and QoL scripts
- Intent: Map scripts, specials, NPC events, progression, and reminders.
- Start here: `maps`, `data/maps`, `data/events/special_pointers.asm`, `engine/events/move_reminder.asm`, `engine/overworld`
- Anchors: `Special` (03:422b, `engine/events/specials.asm:1`); `SpecialsPointers` (03:4239, `data/events/special_pointers.asm:14`); `MoveReminder` (0b:444e, `engine/events/move_reminder.asm:8`)

### RAM, saves, and temporary battle state
- Intent: WRAM, SRAM, VRAM, HRAM, save data, and low-memory pressure points.
- Start here: `ram/wram.asm`, `ram/sram.asm`, `ram/vram.asm`, `ram/hram.asm`
- Anchors: `wBattleMode` (01:d116, `ram/wram.asm:2019`); `wEnemyMon` (01:d0ef, `ram/wram.asm:2012`); `wBattleMon` (00:cafc, `ram/wram.asm:670`); `hROMBank` (00:ff9f, `ram/hram.asm:26`)

### Graphics
- Intent: Pokemon pics, trainer pics, sprites, tilesets, palettes, and UI art.
- Start here: `gfx`, `data/sprites`, `data/tilesets.asm`, `gfx/pics_gold.asm`
- Anchors: `PokemonPicPointers` (12:4000, `data/pokemon/pic_pointers.asm:3`); `TrainerPicPointers` (20:4000, `data/trainers/pic_pointers.asm:3`); `Tilesets` (05:561b, `data/tilesets.asm:13`)

### Audio
- Intent: Music, cries, sound effects, engine data, and song banks.
- Start here: `audio`, `audio.asm`, `constants/music_constants.asm`, `constants/sfx_constants.asm`
- Anchors: `Music` (3a:5069, `audio/music_pointers.asm:3`); `SFX` (3a:5259, `audio/sfx_pointers.asm:1`); `Cries` (3a:518d, `audio/cry_pointers.asm:1`)

## Memory Summary

| Region | Used | Free | Banks |
| --- | ---: | ---: | ---: |
| ROM0 | 15668 | 716 |  |
| ROMX | 1146603 | 934165 | 127 |
| SRAM | 31699 | 1069 | 4 |
| WRAM0 | 4049 | 47 |  |
| WRAMX | 4122 | 4070 | 2 |
| HRAM | 127 | 0 |  |

### Boss AI WRAM Reserve

Boss AI state is carved out of full WRAMX bank 1 but has its own reserved block. Add Boss AI bytes here only after checking this budget.

| Build | Used bytes | Reserved free bytes |
| --- | ---: | ---: |
| Normal | 104 | 36 |
| With `BOSS_AI_TRACE` fields | 131 | 9 |

| Label | Address | Use |
| --- | --- | --- |
| `wBossAITier` | 01:d72b | Boss AI state start |
| `wBossAIPendingPlayerSwitchCount` | 01:d731 | Current-turn switch input buffer |
| `wBossAITurnsElapsed` | 01:d732 | Next-turn commit point for pending observations |
| `wBossAIStateEnd` | 01:d793 | Logical end before reserve padding |
| `wEventFlags` | 01:d7b7 | First unrelated field after reserved block |

### Tight Banks And Regions

These are the first places to treat carefully when adding code or data.
Bank numbers in this table are hexadecimal.

| Region | Bank | Free bytes |
| --- | ---: | ---: |
| HRAM | 00 | 0 |
| ROMX | 12 | 0 |
| ROMX | 15 | 0 |
| ROMX | 17 | 0 |
| ROMX | 1b | 0 |
| ROMX | 1e | 0 |
| WRAMX | 01 | 0 |
| ROMX | 1c | 1 |
| ROMX | 1f | 1 |
| ROMX | 1a | 4 |
| ROMX | 3e | 43 |
| WRAM0 | 00 | 47 |
| ROMX | 16 | 48 |
| ROMX | 20 | 64 |
| ROMX | 30 | 64 |
| ROMX | 07 | 67 |
| ROMX | 19 | 77 |
| ROMX | 3a | 78 |

### Largest ROMX Free Ranges

Use these as candidates when moving optional code or data out of tight banks.

| Bank | Range | Bytes |
| ---: | --- | ---: |
| 13 | $4000-$7fff | 16384 |
| 22 | $4000-$7fff | 16384 |
| 27 | $4000-$7fff | 16384 |
| 28 | $4000-$7fff | 16384 |
| 29 | $4000-$7fff | 16384 |
| 2c | $4000-$7fff | 16384 |
| 2d | $4000-$7fff | 16384 |
| 2f | $4000-$7fff | 16384 |
| 34 | $4000-$7fff | 16384 |
| 35 | $4000-$7fff | 16384 |
| 58 | $4000-$7fff | 16384 |
| 63 | $4000-$7fff | 16384 |
| 67 | $4000-$7fff | 16384 |
| 6f | $4000-$7fff | 16384 |

## Notable Sections

| Section | Region | Bank/range | Size | Layout constraint | Source hints |
| --- | --- | --- | ---: | --- | --- |
| `Home` | ROM0 | 00:0150-3e0b | 15548 | ROM0 00 | `home.asm`, `home/array.asm`, `home/audio.asm`, `home/battle.asm`, +49 more |
| `bankB` | ROMX | 0b:4000-4b64 | 2917 | ROMX 0b | `engine/battle/ai/redundant.asm`, `engine/battle/trainer_huds.asm`, `engine/events/move_deleter.asm`, `engine/events/move_reminder.asm`, +5 more |
| `Effect Commands` | ROMX | 0d:4000-7f30 | 16177 | ROMX 0d | `engine/battle/effect_commands.asm`, `engine/battle/used_move_text.asm`, `main.asm` |
| `Enemy Trainers` | ROMX | 0e:4000-7e33 | 15924 | ROMX 0e | `engine/battle/ai/boss_platform.asm`, `engine/battle/ai/boss_policy_move.asm`, `engine/battle/ai/boss_policy_switch.asm`, `engine/battle/ai/boss_thunks.asm`, +6 more |
| `Battle Core` | ROMX | 0f:4000-7acb | 15052 | ROMX 0f | `engine/battle/core.asm`, `main.asm` |
| `Evolutions and Attacks` | ROMX | 10:685c-7f97 | 5948 | ROMX 10 | `data/pokemon/evos_attacks.asm`, `data/pokemon/evos_attacks_pointers.asm` |
| `Late Gen Held Items` | ROMX | 11:648a-7229 | 3488 |  | `engine/battle/late_gen_held_items.asm`, `engine/battle/type_passive_damage_mods.asm`, `main.asm` |
| `Maps` | ROMX | 25:4000-65f8 | 9721 | ROMX 25 | `data/maps/attributes.asm`, `data/maps/blocks.asm`, `data/maps/map_data.asm`, `data/maps/maps.asm`, +2 more |
| `Events` | ROMX | 25:65f9-7d82 | 6026 | ROMX 25 | `data/wild/bug_contest_mons.asm`, `engine/events/trainer_scripts.asm`, `engine/overworld/cmd_queue.asm`, `engine/overworld/events.asm`, +1 more |
| `Audio` | ROMX | 3a:4000-548c | 5261 | ROMX 3a | `audio.asm`, `audio/cry_pointers.asm`, `audio/engine.asm`, `audio/music/nothing.asm`, +3 more |
| `Songs 1` | ROMX | 3a:548d-7fb1 | 11045 | ROMX 3a | `audio.asm`, `audio/music/championbattle.asm`, `audio/music/darkcave.asm`, `audio/music/elmslab.asm`, +12 more |
| `Songs 2` | ROMX | 3b:4000-7ef4 | 16117 | ROMX 3b | `audio.asm`, `audio/music/bicycle.asm`, `audio/music/contestresults.asm`, `audio/music/dancinghall.asm`, +29 more |
| `Songs 3` | ROMX | 3c:4000-47fc | 2045 | ROMX 3c | `audio.asm`, `audio/music/evolution.asm`, `audio/music/halloffame.asm`, `audio/music/healpokemon.asm`, +2 more |
| `Sound Effects` | ROMX | 3c:47fd-6602 | 7686 | ROMX 3c | `audio.asm`, `audio/sfx.asm` |
| `Cries` | ROMX | 3c:6603-7e31 | 6191 | ROMX 3c | `audio.asm`, `audio/cries.asm`, `data/pokemon/cries.asm` |
| `Songs 4` | ROMX | 3d:4000-7ef2 | 16115 | ROMX 3d | `audio.asm`, `audio/music/aftertherivalfight.asm`, `audio/music/azaleatown.asm`, `audio/music/bugcatchingcontest.asm`, +34 more |
| `Standard Scripts` | ROMX | 40:4000-62a3 | 8868 | ROMX 40 | `data/text/battle.asm`, `engine/events/std_scripts.asm`, `main.asm` |
| `Phone Scripts` | ROMX | 41:4000-60b0 | 8369 | ROMX 41 | `data/phone/text/bike_shop.asm`, `data/phone/text/bill.asm`, `data/phone/text/elm.asm`, `data/phone/text/mom.asm`, +9 more |
| `Map Scripts 1` | ROMX | 42:4000-5dd9 | 7642 | ROMX 42 | `data/maps/scripts.asm`, `maps/BurnedTower1F.asm`, `maps/BurnedTowerB1F.asm`, `maps/DiglettsCave.asm`, +19 more |
| `Map Scripts 2` | ROMX | 43:4000-7197 | 12696 | ROMX 43 | `data/maps/scripts.asm`, `maps/NationalPark.asm`, `maps/NationalParkBugContest.asm`, `maps/RadioTower1F.asm`, +4 more |
| `Map Scripts 3` | ROMX | 44:4000-6f80 | 12161 | ROMX 44 | `data/maps/scripts.asm`, `maps/OlivineLighthouse1F.asm`, `maps/OlivineLighthouse2F.asm`, `maps/OlivineLighthouse3F.asm`, +15 more |
| `Map Scripts 4` | ROMX | 45:4000-6f47 | 12104 | ROMX 45 | `data/maps/scripts.asm`, `maps/IlexForest.asm`, `maps/MahoganyMart1F.asm`, `maps/TeamRocketBaseB1F.asm`, +2 more |
| `Map Scripts 5` | ROMX | 46:4000-636f | 9072 | ROMX 46 | `data/maps/scripts.asm`, `maps/GoldenrodDeptStoreB1F.asm`, `maps/GoldenrodUnderground.asm`, `maps/GoldenrodUndergroundSwitchRoomEntrances.asm`, +10 more |
| `Map Scripts 6` | ROMX | 47:4000-49a3 | 2468 | ROMX 47 | `data/maps/scripts.asm`, `maps/DarkCaveBlackthornEntrance.asm`, `maps/DarkCaveVioletEntrance.asm`, `maps/DragonsDen1F.asm`, +14 more |
| `Map Scripts 7` | ROMX | 48:4000-654d | 9550 | ROMX 48 | `data/maps/scripts.asm`, `maps/AzaleaTown.asm`, `maps/CherrygroveCity.asm`, `maps/CianwoodCity.asm`, +3 more |
| `Map Scripts 8` | ROMX | 49:4000-5f50 | 8017 | ROMX 49 | `data/maps/scripts.asm`, `maps/BlackthornCity.asm`, `maps/EcruteakCity.asm`, `maps/LakeOfRage.asm`, +3 more |
| `Map Scripts 9` | ROMX | 4a:4000-5ff9 | 8186 | ROMX 4a | `data/maps/scripts.asm`, `maps/Route26.asm`, `maps/Route27.asm`, `maps/Route28.asm`, +3 more |
| `Map Scripts 10` | ROMX | 4b:4000-67bb | 10172 | ROMX 4b | `data/maps/scripts.asm`, `maps/Route32.asm`, `maps/Route33.asm`, `maps/Route34.asm`, +2 more |
| `Map Scripts 11` | ROMX | 4c:4000-5f25 | 7974 | ROMX 4c | `data/maps/scripts.asm`, `maps/Route37.asm`, `maps/Route38.asm`, `maps/Route39.asm`, +3 more |
| `Map Scripts 12` | ROMX | 4d:4000-5e59 | 7770 | ROMX 4d | `data/maps/scripts.asm`, `maps/PewterCity.asm`, `maps/Route2.asm`, `maps/Route43.asm`, +3 more |
| `Map Scripts 13` | ROMX | 4e:4000-6173 | 8564 | ROMX 4e | `data/maps/scripts.asm`, `maps/CeladonCity.asm`, `maps/CinnabarIsland.asm`, `maps/FuchsiaCity.asm`, +11 more |
| `Map Scripts 14` | ROMX | 4f:4000-64b1 | 9394 | ROMX 4f | `data/maps/scripts.asm`, `maps/CeruleanCity.asm`, `maps/LavenderTown.asm`, `maps/Route11.asm`, +8 more |
| `Map Scripts 15` | ROMX | 50:4000-58ec | 6381 | ROMX 50 | `data/maps/scripts.asm`, `maps/Route10North.asm`, `maps/Route10South.asm`, `maps/Route23.asm`, +6 more |
| `Map Scripts 16` | ROMX | 51:4000-5db7 | 7608 | ROMX 51 | `data/maps/scripts.asm`, `maps/MahoganyGym.asm`, `maps/MahoganyPokecenter1F.asm`, `maps/MahoganyRedGyaradosSpeechHouse.asm`, +12 more |
| `Map Scripts 17` | ROMX | 52:4000-5c9e | 7327 | ROMX 52 | `data/maps/scripts.asm`, `maps/DanceTheater.asm`, `maps/EcruteakGym.asm`, `maps/EcruteakItemfinderHouse.asm`, +5 more |
| `Map Scripts 18` | ROMX | 53:4000-5e29 | 7722 | ROMX 53 | `data/maps/scripts.asm`, `maps/BlackthornDragonSpeechHouse.asm`, `maps/BlackthornEmysHouse.asm`, `maps/BlackthornGym1F.asm`, +12 more |
| `Map Scripts 19` | ROMX | 54:4000-5aa2 | 6819 | ROMX 54 | `data/maps/scripts.asm`, `maps/BillsHouse.asm`, `maps/CeruleanGym.asm`, `maps/CeruleanGymBadgeSpeechHouse.asm`, +8 more |
| `Map Scripts 20` | ROMX | 55:4000-5567 | 5480 | ROMX 55 | `data/maps/scripts.asm`, `maps/AzaleaGym.asm`, `maps/AzaleaMart.asm`, `maps/AzaleaPokecenter1F.asm`, +2 more |
| `Map Scripts 21` | ROMX | 56:4000-756e | 13679 | ROMX 56 | `data/maps/scripts.asm`, `maps/EarlsPokemonAcademy.asm`, `maps/Route32Pokecenter1F.asm`, `maps/Route32RuinsOfAlphGate.asm`, +9 more |
| `Map Scripts 22` | ROMX | 57:4000-70b1 | 12466 | ROMX 57 | `data/maps/scripts.asm`, `maps/BillsFamilysHouse.asm`, `maps/DayCare.asm`, `maps/GoldenrodBikeShop.asm`, +17 more |
| `Map Scripts 23` | ROMX | 59:4000-5fc6 | 8135 | ROMX 59 | `data/maps/scripts.asm`, `maps/BluesHouse.asm`, `maps/OaksLab.asm`, `maps/PokemonFanClub.asm`, +11 more |
| `Map Scripts 24` | ROMX | 5a:4000-5f84 | 8069 | ROMX 5a | `data/maps/scripts.asm`, `maps/BrunosRoom.asm`, `maps/HallOfFame.asm`, `maps/IndigoPlateauPokecenter1F.asm`, +10 more |
| `Map Scripts 25` | ROMX | 5b:4000-695c | 10589 | ROMX 5b | `data/maps/scripts.asm`, `maps/FastShip1F.asm`, `maps/FastShipB1F.asm`, `maps/FastShipCabins_NNW_NNE_NE.asm`, +9 more |
| `Map Scripts 26` | ROMX | 5c:4000-54dc | 5341 | ROMX 5c | `data/maps/scripts.asm`, `maps/BillsOlderSistersHouse.asm`, `maps/Colosseum.asm`, `maps/FuchsiaGym.asm`, +11 more |
| `Map Scripts 27` | ROMX | 5d:4000-5e06 | 7687 | ROMX 5d | `data/maps/scripts.asm`, `maps/CianwoodGym.asm`, `maps/CianwoodLugiaSpeechHouse.asm`, `maps/CianwoodPharmacy.asm`, +13 more |
| `Map Scripts 28` | ROMX | 5e:4000-6a83 | 10884 | ROMX 5e | `data/maps/scripts.asm`, `maps/CeladonCafe.asm`, `maps/CeladonDeptStore1F.asm`, `maps/CeladonDeptStore2F.asm`, +19 more |
| `Map Scripts 29` | ROMX | 5f:4000-51b4 | 4533 | ROMX 5f | `data/maps/scripts.asm`, `maps/Route2Gate.asm`, `maps/Route2NuggetHouse.asm`, `maps/TrainerHouse1F.asm`, +7 more |
| `Map Scripts 30` | ROMX | 60:4000-666a | 9835 | ROMX 60 | `data/maps/scripts.asm`, `maps/DayOfWeekSiblingsHouse.asm`, `maps/ElmsHouse.asm`, `maps/ElmsLab.asm`, +6 more |
| `Map Scripts 31` | ROMX | 61:4000-5921 | 6434 | ROMX 61 | `data/maps/scripts.asm`, `maps/CopycatsHouse1F.asm`, `maps/CopycatsHouse2F.asm`, `maps/FightingDojo.asm`, +10 more |
| `Map Scripts 32` | ROMX | 62:4000-4ead | 3758 | ROMX 62 | `data/maps/scripts.asm`, `maps/CherrygroveEvolutionSpeechHouse.asm`, `maps/CherrygroveGymSpeechHouse.asm`, `maps/CherrygroveMart.asm`, +5 more |

## Important Labels

| Label | Address | Source |
| --- | --- | --- |
| `BossAI_IncrementTurnsElapsed` | 0e:454d | `engine/battle/ai/boss_platform.asm:24` |
| `BossAI_RecordPlayerSwitch` | 0e:45db | `engine/battle/ai/boss_platform.asm:126` |
| `BossAI_SelectMove` | 0e:57bf | `engine/battle/ai/boss_policy_move.asm:2677` |
| `BossAI_SwitchOrTryItem` | 0e:58b1 | `engine/battle/ai/boss_policy_switch.asm:17` |
| `BossAI_ComputeSwitchConfidence` | 0e:6540 | `engine/battle/ai/boss_policy_switch.asm:751` |
| `BossAI_PredictPlayerSwitch` | 0e:65c3 | `engine/battle/ai/boss_policy_move.asm:3605` |
| `BossAI_RecordRevealedPlayerMove` | 0e:4717 | `engine/battle/ai/boss_platform.asm:260` |
| `BossAI_CurrentEnemyMoveHasKOPressure` | 0e:6025 | `engine/battle/ai/boss_policy_move.asm:3043` |
| `BossAI_CurrentEnemyMovePressureScore` | 0e:604d | `engine/battle/ai/boss_policy_move.asm:3077` |
| `BossAI_PlayerHasPublicThreatVsEnemy` | 0e:5e8e | `engine/battle/ai/boss_policy_move.asm:2885` |
| `BossAI_PublicEnemyFaster` | 0e:62e9 | `engine/battle/ai/boss_policy_move.asm:3530` |
| `BossAI_CheckAbleToSwitchSafe` | 0e:5a4e | `engine/battle/ai/boss_policy_switch.asm:298` |
| `BossAI_RefineSwitchCandidateForPlausibleRisk` | 0e:748d | `engine/battle/ai/boss_policy_switch.asm:833` |
| `BossAI_ApplyPlausibleRiskToSwitchConfidence` | 0e:76c1 | `engine/battle/ai/boss_policy_switch.asm:1216` |
| `BossAITierMap` | 0e:7d6e | `data/trainers/ai_tiers.asm:1` |
| `CheckPlayerMoveTypeMatchups` | 0d:49e5 | `engine/battle/ai/switch.asm:1` |
| `AICompareSpeed` | 0b:78d0 | `engine/battle/ai/scoring.asm:2650` |
| `AIDamageCalc` | 0b:7a85 | `engine/battle/ai/scoring.asm:2977` |
| `TypePassive_ApplyDamageModifiers_Far` | 11:69c9 | `engine/battle/type_passive_damage_mods.asm:44` |
| `TypePassive_TryDarkStatusShield_Far` | 11:6f4e | `engine/battle/type_passive_damage_mods.asm:1069` |
| `TypePassive_MaybePoisonRetaliation_Far` | 11:6fab | `engine/battle/type_passive_damage_mods.asm:1135` |
| `ApplyLateGenDamageMultipliers_Far` | 11:655f | `engine/battle/late_gen_held_items.asm:183` |
| `HandleLateGenAfterHitEffects_Far` | 11:6618 | `engine/battle/late_gen_held_items.asm:301` |
| `TryActivateDittoImposter` | 01:799b | `engine/battle/ditto_imposter.asm:1` |
| `Moves` | 10:5aaa | `data/moves/moves.asm:14` |
| `MoveEffects` | 09:7489 | `data/moves/effects.asm:3` |
| `MoveContactFlags` | 11:712c | `data/moves/contact_flags.asm:4` |
| `Spikes` | 09:79a5 | `data/moves/effects.asm:1525` |
| `RapidSpin` | 09:7a7a | `data/moves/effects.asm:1772` |
| `ItemAttributes` | 01:68ba | `data/items/attributes.asm:8` |
| `ItemDescriptions` | 6e:4000 | `data/items/descriptions.asm:1` |
| `ItemNames` | 6c:4000 | `data/items/names.asm:1` |
| `IsChoiceHeldEffect_Far` | 11:6910 | `engine/battle/late_gen_held_items.asm:819` |
| `IsMoveBlockedByAssaultVest_Far` | 11:6919 | `engine/battle/late_gen_held_items.asm:827` |
| `BaseData` | 14:5ab9 | `data/pokemon/base_stats.asm:21` |
| `EvosAttacksPointers` | 10:685c | `data/pokemon/evos_attacks_pointers.asm:3` |
| `EggMovePointers` | 08:79f0 | `data/pokemon/egg_move_pointers.asm:1` |
| `Special` | 03:422b | `engine/events/specials.asm:1` |
| `SpecialsPointers` | 03:4239 | `data/events/special_pointers.asm:14` |
| `MoveReminder` | 0b:444e | `engine/events/move_reminder.asm:8` |
| `wBattleMode` | 01:d116 | `ram/wram.asm:2019` |
| `wEnemyMon` | 01:d0ef | `ram/wram.asm:2012` |
| `wBattleMon` | 00:cafc | `ram/wram.asm:670` |
| `hROMBank` | 00:ff9f | `ram/hram.asm:26` |
| `PokemonPicPointers` | 12:4000 | `data/pokemon/pic_pointers.asm:3` |
| `TrainerPicPointers` | 20:4000 | `data/trainers/pic_pointers.asm:3` |
| `Tilesets` | 05:561b | `data/tilesets.asm:13` |
| `Music` | 3a:5069 | `audio/music_pointers.asm:3` |
| `SFX` | 3a:5259 | `audio/sfx_pointers.asm:1` |
| `Cries` | 3a:518d | `audio/cry_pointers.asm:1` |

## Warning Zones

- ROM0, WRAM0, WRAMX, and HRAM are global pressure points. Prefer moving new optional logic into ROMX banks with room.
- Battle-sensitive sections such as `Battle Core`, `Effect Commands`, `Enemy Trainers`, and `Late Gen Held Items` should be checked in this file after every substantial mechanics change.
- Generated files should be refreshed with `python scripts/generate_dev_index.py --rom pokegold` after linker addresses change.
- If this file disagrees with source after a build, regenerate it before using addresses for planning.
