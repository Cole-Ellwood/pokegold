# Developer ROM Index

Generated: 2026-04-26
ROM target: `pokegold`

Generated from `layout.link`, assembly sources, `pokegold.map`, and `pokegold.sym`.

Bank numbers are hexadecimal unless noted otherwise.

Read `docs/README.md` first for helper-doc routing, then `docs/codex_context.md` for design intent. This file is for navigation and memory planning only; it does not add anything to the ROM.

## How To Use This Index

1. Start with Quick Lookup for the subsystem you are changing.
2. Use the anchor labels to jump from behavior to current bank/address and source line.
3. Check Memory Summary and Tight Banks before adding code or data.
4. Use Largest ROMX Free Ranges when moving optional code out of crowded banks.
5. Refresh this file after a successful build changes linker outputs.

## Quick Lookup

### Developer docs and review workflow
- Intent: Project intent, review order, bug-hunt checklist, and generated lookup.
- Start here: `docs/README.md`, `docs/codex_context.md`, `docs/codex_review_playbook.md`, `docs/project_map.md`, `docs/boss_ai_spec.md`, `docs/generated/dev_index.md`, `scripts/generate_dev_index.py`

### Boss AI and trainer difficulty
- Intent: Human-like major fights, no hidden-information cheating.
- Start here: `engine/battle/ai/boss.asm`, `engine/battle/ai/move.asm`, `engine/battle/ai/scoring.asm`, `engine/battle/ai/items.asm`, `engine/battle/ai/switch.asm`, `engine/battle/core.asm`, `engine/battle/used_move_text.asm`, `engine/battle/read_trainer_attributes.asm`, `data/trainers/ai_tiers.asm`, `data/trainers/parties.asm`, `data/trainers/attributes.asm`, `constants/battle_constants.asm`
- Anchors: `BossAI_IncrementTurnsElapsed` (0e:553b, `engine/battle/ai/boss.asm:1`); `BossAI_RecordPlayerSwitch` (0e:5564, `engine/battle/ai/boss.asm:26`); `BossAI_SelectMove` (0e:5b9f, `engine/battle/ai/boss.asm:1081`); `BossAI_SwitchOrTryItem` (0e:5c8a, `engine/battle/ai/boss.asm:1268`); `BossAI_ComputeSwitchConfidence` (0e:6110, `engine/battle/ai/boss.asm:2095`); `BossAI_PredictPlayerSwitch` (0e:617d, `engine/battle/ai/boss.asm:2158`); `BossAI_RecordRevealedPlayerMove` (0e:5650, `engine/battle/ai/boss.asm:216`); `BossAI_CurrentEnemyMoveHasKOPressure` (0e:5e9f, `engine/battle/ai/boss.asm:1639`); `BossAI_CurrentEnemyMovePressureScore` (0e:5ec7, `engine/battle/ai/boss.asm:1672`); `BossAI_PlayerHasPublicThreatVsEnemy` (0e:5d7a, `engine/battle/ai/boss.asm:1430`); `BossAI_PublicEnemyFaster` (0e:5f35, `engine/battle/ai/boss.asm:1758`); `BossAI_CheckAbleToSwitchSafe` (0e:5d30, `engine/battle/ai/boss.asm:1374`); `BossAI_RefineSwitchCandidateForPlausibleRisk` (0e:6bff, `engine/battle/ai/boss.asm:4085`); `BossAI_ApplyPlausibleRiskToSwitchConfidence` (0e:6db6, `engine/battle/ai/boss.asm:4370`)

### Battle mechanics
- Intent: Shared damage, status, switching, item, and turn-flow rules.
- Start here: `engine/battle/core.asm`, `engine/battle/effect_commands.asm`, `engine/battle/type_passive_damage_mods.asm`, `engine/battle/late_gen_held_items.asm`, `engine/battle/move_effects`, `constants/battle_constants.asm`
- Anchors: `TypePassive_ApplyDamageModifiers_Far` (0b:7389, `engine/battle/type_passive_damage_mods.asm:44`); `TypePassive_TryDarkStatusShield_Far` (0b:7916, `engine/battle/type_passive_damage_mods.asm:1057`); `TypePassive_MaybePoisonRetaliation_Far` (0b:7965, `engine/battle/type_passive_damage_mods.asm:1118`); `ApplyLateGenDamageMultipliers_Far` (0b:6fa0, `engine/battle/late_gen_held_items.asm:164`); `HandleLateGenAfterHitEffects_Far` (0b:703b, `engine/battle/late_gen_held_items.asm:261`); `TryActivateDittoImposter` (01:7588, `engine/battle/ditto_imposter.asm:1`)

### Moves
- Intent: Move stats, effects, descriptions, contact flags, and animations.
- Start here: `data/moves/moves.asm`, `data/moves/effects.asm`, `data/moves/effects_pointers.asm`, `data/moves/contact_flags.asm`, `data/moves/descriptions.asm`, `constants/move_constants.asm`
- Anchors: `Moves` (10:5af6, `data/moves/moves.asm:14`); `MoveEffects` (09:7510, `data/moves/effects.asm:3`); `MoveContactFlags` (0b:7ad8, `data/moves/contact_flags.asm:4`); `Spikes` (09:7a19, `data/moves/effects.asm:1504`); `RapidSpin` (09:7aee, `data/moves/effects.asm:1751`)

### Items and held items
- Intent: Item data, descriptions, pockets, marts, and battle held effects.
- Start here: `data/items/attributes.asm`, `data/items/descriptions.asm`, `data/items/names.asm`, `data/items/marts.asm`, `engine/items`, `engine/battle/late_gen_held_items.asm`
- Anchors: `ItemAttributes` (01:68d5, `data/items/attributes.asm:8`); `ItemDescriptions` (6e:4000, `data/items/descriptions.asm:1`); `ItemNames` (6c:4000, `data/items/names.asm:1`); `IsChoiceHeldEffect_Far` (0b:72e9, `engine/battle/late_gen_held_items.asm:719`); `IsMoveBlockedByAssaultVest_Far` (0b:72f2, `engine/battle/late_gen_held_items.asm:727`)

### Pokemon data and weak-Pokemon buffs
- Intent: Base stats, types, level-up moves, evolutions, egg moves, and names.
- Start here: `data/pokemon/base_stats.asm`, `data/pokemon/base_stats`, `data/pokemon/evos_attacks.asm`, `data/pokemon/evos_attacks_pointers.asm`, `data/pokemon/egg_moves.asm`, `constants/pokemon_constants.asm`
- Anchors: `BaseData` (14:5bb8, `data/pokemon/base_stats.asm:21`); `EvosAttacksPointers` (10:6893, `data/pokemon/evos_attacks_pointers.asm:3`); `EggMovePointers` (08:79fe, `data/pokemon/egg_move_pointers.asm:1`)

### Maps, events, and QoL scripts
- Intent: Map scripts, specials, NPC events, progression, tutors, and reminders.
- Start here: `maps`, `data/maps`, `data/events/special_pointers.asm`, `engine/events/move_reminder.asm`, `engine/events/tm_tutor.asm`, `engine/overworld`
- Anchors: `Special` (03:422b, `engine/events/specials.asm:1`); `SpecialsPointers` (03:4239, `data/events/special_pointers.asm:14`); `MoveReminder` (0b:4451, `engine/events/move_reminder.asm:8`); `TMTutorTeachAnyTM` (0b:4c25, `engine/events/tm_tutor.asm:1`)

### RAM, saves, and temporary battle state
- Intent: WRAM, SRAM, VRAM, HRAM, save data, and low-memory pressure points.
- Start here: `ram/wram.asm`, `ram/sram.asm`, `ram/vram.asm`, `ram/hram.asm`
- Anchors: `wBattleMode` (01:d116, `ram/wram.asm:2107`); `wEnemyMon` (01:d0ef, `ram/wram.asm:2100`); `wBattleMon` (00:cafc, `ram/wram.asm:747`); `hROMBank` (00:ff9f, `ram/hram.asm:26`)

### Graphics
- Intent: Pokemon pics, trainer pics, sprites, tilesets, palettes, and UI art.
- Start here: `gfx`, `data/sprites`, `data/tilesets.asm`, `gfx/pics_gold.asm`
- Anchors: `PokemonPicPointers` (12:4000, `data/pokemon/pic_pointers.asm:3`); `TrainerPicPointers` (20:4000, `data/trainers/pic_pointers.asm:3`); `Tilesets` (05:56be, `data/tilesets.asm:13`)

### Audio
- Intent: Music, cries, sound effects, engine data, and song banks.
- Start here: `audio`, `audio.asm`, `constants/music_constants.asm`, `constants/sfx_constants.asm`
- Anchors: `Music` (3a:506e, `audio/music_pointers.asm:3`); `SFX` (3a:525e, `audio/sfx_pointers.asm:1`); `Cries` (3a:5192, `audio/cry_pointers.asm:1`)

## Memory Summary

| Region | Used | Free | Banks |
| --- | ---: | ---: | ---: |
| ROM0 | 16166 | 218 |  |
| ROMX | 1153717 | 927051 | 127 |
| SRAM | 31697 | 1071 | 4 |
| WRAM0 | 4047 | 49 |  |
| WRAMX | 4096 | 0 |  |
| HRAM | 127 | 0 |  |

### Boss AI WRAM Reserve

Boss AI state is carved out of full WRAMX bank 1 but has its own reserved block. Add Boss AI bytes here only after checking this budget.

| Build | Used bytes | Reserved free bytes |
| --- | ---: | ---: |
| Normal | 75 | 65 |
| With `BOSS_AI_TRACE` fields | 94 | 46 |

| Label | Address | Use |
| --- | --- | --- |
| `wBossAITier` | 01:d72b | Boss AI state start |
| `wBossAIPendingPlayerSwitchCount` | 01:d731 | Current-turn switch input buffer |
| `wBossAITurnsElapsed` | 01:d732 | Next-turn commit point for pending observations |
| `wBossAIStateEnd` | 01:d776 | Logical end before reserve padding |
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
| ROMX | 0d | 1 |
| ROMX | 1c | 1 |
| ROMX | 1f | 1 |
| ROMX | 1a | 4 |
| ROMX | 16 | 48 |
| WRAM0 | 00 | 49 |
| ROMX | 0f | 53 |
| ROMX | 20 | 64 |
| ROMX | 30 | 64 |
| ROMX | 07 | 67 |
| ROMX | 3a | 73 |

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
| `Home` | ROM0 | 00:0150-3ffd | 16046 | ROM0 00 | `home.asm`, `home/array.asm`, `home/audio.asm`, `home/battle.asm`, +49 more |
| `bankB` | ROMX | 0b:4000-4d9f | 3488 | ROMX 0b | `engine/battle/ai/redundant.asm`, `engine/battle/trainer_huds.asm`, `engine/events/move_deleter.asm`, `engine/events/move_reminder.asm`, +7 more |
| `Late Gen Held Items` | ROMX | 0b:6ea9-7bd5 | 3373 |  | `engine/battle/late_gen_held_items.asm`, `engine/battle/type_passive_damage_mods.asm`, `main.asm` |
| `Effect Commands` | ROMX | 0d:4000-7ffe | 16383 | ROMX 0d | `engine/battle/effect_commands.asm`, `engine/battle/used_move_text.asm`, `main.asm` |
| `Enemy Trainers` | ROMX | 0e:4000-71f7 | 12792 | ROMX 0e | `engine/battle/ai/boss.asm`, `engine/battle/ai/items.asm`, `engine/battle/ai/scoring.asm`, `engine/battle/read_trainer_attributes.asm`, +1 more |
| `Battle Core` | ROMX | 0f:4000-7fca | 16331 | ROMX 0f | `data/battle/effect_command_pointers.asm`, `engine/battle/core.asm`, `main.asm` |
| `Evolutions and Attacks` | ROMX | 10:6893-7f6c | 5850 | ROMX 10 | `data/pokemon/evos_attacks.asm`, `data/pokemon/evos_attacks_pointers.asm` |
| `Maps` | ROMX | 25:4000-65f8 | 9721 | ROMX 25 | `data/maps/attributes.asm`, `data/maps/blocks.asm`, `data/maps/map_data.asm`, `data/maps/maps.asm`, +2 more |
| `Events` | ROMX | 25:65f9-7d99 | 6049 | ROMX 25 | `data/wild/bug_contest_mons.asm`, `engine/events/trainer_scripts.asm`, `engine/overworld/cmd_queue.asm`, `engine/overworld/events.asm`, +1 more |
| `Audio` | ROMX | 3a:4000-5491 | 5266 | ROMX 3a | `audio.asm`, `audio/cry_pointers.asm`, `audio/engine.asm`, `audio/music/nothing.asm`, +3 more |
| `Songs 1` | ROMX | 3a:5492-7fb6 | 11045 | ROMX 3a | `audio.asm`, `audio/music/championbattle.asm`, `audio/music/darkcave.asm`, `audio/music/elmslab.asm`, +12 more |
| `Songs 2` | ROMX | 3b:4000-7ef4 | 16117 | ROMX 3b | `audio.asm`, `audio/music/bicycle.asm`, `audio/music/contestresults.asm`, `audio/music/dancinghall.asm`, +29 more |
| `Songs 3` | ROMX | 3c:4000-4940 | 2369 | ROMX 3c | `audio.asm`, `audio/music/evolution.asm`, `audio/music/halloffame.asm`, `audio/music/healpokemon.asm`, +3 more |
| `Sound Effects` | ROMX | 3c:4941-6746 | 7686 | ROMX 3c | `audio.asm`, `audio/sfx.asm` |
| `Cries` | ROMX | 3c:6747-7f75 | 6191 | ROMX 3c | `audio.asm`, `audio/cries.asm`, `data/pokemon/cries.asm` |
| `Songs 4` | ROMX | 3d:4000-7ef2 | 16115 | ROMX 3d | `audio.asm`, `audio/music/aftertherivalfight.asm`, `audio/music/azaleatown.asm`, `audio/music/bugcatchingcontest.asm`, +34 more |
| `Standard Scripts` | ROMX | 40:4000-62c4 | 8901 | ROMX 40 | `data/text/battle.asm`, `engine/events/std_scripts.asm`, `main.asm` |
| `Phone Scripts` | ROMX | 41:4000-614c | 8525 | ROMX 41 | `data/phone/text/bike_shop.asm`, `data/phone/text/bill.asm`, `data/phone/text/elm.asm`, `data/phone/text/mom.asm`, +9 more |
| `Map Scripts 1` | ROMX | 42:4000-5dc9 | 7626 | ROMX 42 | `data/maps/scripts.asm`, `maps/BurnedTower1F.asm`, `maps/BurnedTowerB1F.asm`, `maps/DiglettsCave.asm`, +19 more |
| `Map Scripts 2` | ROMX | 43:4000-7197 | 12696 | ROMX 43 | `data/maps/scripts.asm`, `maps/NationalPark.asm`, `maps/NationalParkBugContest.asm`, `maps/RadioTower1F.asm`, +4 more |
| `Map Scripts 3` | ROMX | 44:4000-70ca | 12491 | ROMX 44 | `data/maps/scripts.asm`, `maps/OlivineLighthouse1F.asm`, `maps/OlivineLighthouse2F.asm`, `maps/OlivineLighthouse3F.asm`, +15 more |
| `Map Scripts 4` | ROMX | 45:4000-6f30 | 12081 | ROMX 45 | `data/maps/scripts.asm`, `maps/IlexForest.asm`, `maps/MahoganyMart1F.asm`, `maps/TeamRocketBaseB1F.asm`, +2 more |
| `Map Scripts 5` | ROMX | 46:4000-6357 | 9048 | ROMX 46 | `data/maps/scripts.asm`, `maps/GoldenrodDeptStoreB1F.asm`, `maps/GoldenrodUnderground.asm`, `maps/GoldenrodUndergroundSwitchRoomEntrances.asm`, +10 more |
| `Map Scripts 6` | ROMX | 47:4000-49fd | 2558 | ROMX 47 | `data/maps/scripts.asm`, `maps/DarkCaveBlackthornEntrance.asm`, `maps/DarkCaveVioletEntrance.asm`, `maps/DragonsDen1F.asm`, +14 more |
| `Map Scripts 7` | ROMX | 48:4000-659e | 9631 | ROMX 48 | `data/maps/scripts.asm`, `maps/AzaleaTown.asm`, `maps/CherrygroveCity.asm`, `maps/CianwoodCity.asm`, +3 more |
| `Map Scripts 8` | ROMX | 49:4000-5f50 | 8017 | ROMX 49 | `data/maps/scripts.asm`, `maps/BlackthornCity.asm`, `maps/EcruteakCity.asm`, `maps/LakeOfRage.asm`, +3 more |
| `Map Scripts 9` | ROMX | 4a:4000-6017 | 8216 | ROMX 4a | `data/maps/scripts.asm`, `maps/Route26.asm`, `maps/Route27.asm`, `maps/Route28.asm`, +3 more |
| `Map Scripts 10` | ROMX | 4b:4000-69ba | 10683 | ROMX 4b | `data/maps/scripts.asm`, `maps/Route32.asm`, `maps/Route33.asm`, `maps/Route34.asm`, +2 more |
| `Map Scripts 11` | ROMX | 4c:4000-5f25 | 7974 | ROMX 4c | `data/maps/scripts.asm`, `maps/Route37.asm`, `maps/Route38.asm`, `maps/Route39.asm`, +3 more |
| `Map Scripts 12` | ROMX | 4d:4000-5e59 | 7770 | ROMX 4d | `data/maps/scripts.asm`, `maps/PewterCity.asm`, `maps/Route2.asm`, `maps/Route43.asm`, +3 more |
| `Map Scripts 13` | ROMX | 4e:4000-6175 | 8566 | ROMX 4e | `data/maps/scripts.asm`, `maps/CeladonCity.asm`, `maps/CinnabarIsland.asm`, `maps/FuchsiaCity.asm`, +11 more |
| `Map Scripts 14` | ROMX | 4f:4000-64c3 | 9412 | ROMX 4f | `data/maps/scripts.asm`, `maps/CeruleanCity.asm`, `maps/LavenderTown.asm`, `maps/Route11.asm`, +8 more |
| `Map Scripts 15` | ROMX | 50:4000-58ec | 6381 | ROMX 50 | `data/maps/scripts.asm`, `maps/Route10North.asm`, `maps/Route10South.asm`, `maps/Route23.asm`, +6 more |
| `Map Scripts 16` | ROMX | 51:4000-5e25 | 7718 | ROMX 51 | `data/maps/scripts.asm`, `maps/MahoganyGym.asm`, `maps/MahoganyPokecenter1F.asm`, `maps/MahoganyRedGyaradosSpeechHouse.asm`, +12 more |
| `Map Scripts 17` | ROMX | 52:4000-5cbb | 7356 | ROMX 52 | `data/maps/scripts.asm`, `maps/DanceTheater.asm`, `maps/EcruteakGym.asm`, `maps/EcruteakItemfinderHouse.asm`, +5 more |
| `Map Scripts 18` | ROMX | 53:4000-5e73 | 7796 | ROMX 53 | `data/maps/scripts.asm`, `maps/BlackthornDragonSpeechHouse.asm`, `maps/BlackthornEmysHouse.asm`, `maps/BlackthornGym1F.asm`, +12 more |
| `Map Scripts 19` | ROMX | 54:4000-5aa2 | 6819 | ROMX 54 | `data/maps/scripts.asm`, `maps/BillsHouse.asm`, `maps/CeruleanGym.asm`, `maps/CeruleanGymBadgeSpeechHouse.asm`, +8 more |
| `Map Scripts 20` | ROMX | 55:4000-55a8 | 5545 | ROMX 55 | `data/maps/scripts.asm`, `maps/AzaleaGym.asm`, `maps/AzaleaMart.asm`, `maps/AzaleaPokecenter1F.asm`, +2 more |
| `Map Scripts 21` | ROMX | 56:4000-75f0 | 13809 | ROMX 56 | `data/maps/scripts.asm`, `maps/EarlsPokemonAcademy.asm`, `maps/Route32Pokecenter1F.asm`, `maps/Route32RuinsOfAlphGate.asm`, +9 more |
| `Map Scripts 22` | ROMX | 57:4000-7646 | 13895 | ROMX 57 | `data/maps/scripts.asm`, `maps/BillsFamilysHouse.asm`, `maps/DayCare.asm`, `maps/GoldenrodBikeShop.asm`, +17 more |
| `Map Scripts 23` | ROMX | 59:4000-5fc6 | 8135 | ROMX 59 | `data/maps/scripts.asm`, `maps/BluesHouse.asm`, `maps/OaksLab.asm`, `maps/PokemonFanClub.asm`, +11 more |
| `Map Scripts 24` | ROMX | 5a:4000-5f84 | 8069 | ROMX 5a | `data/maps/scripts.asm`, `maps/BrunosRoom.asm`, `maps/HallOfFame.asm`, `maps/IndigoPlateauPokecenter1F.asm`, +10 more |
| `Map Scripts 25` | ROMX | 5b:4000-695c | 10589 | ROMX 5b | `data/maps/scripts.asm`, `maps/FastShip1F.asm`, `maps/FastShipB1F.asm`, `maps/FastShipCabins_NNW_NNE_NE.asm`, +9 more |
| `Map Scripts 26` | ROMX | 5c:4000-5608 | 5641 | ROMX 5c | `data/maps/scripts.asm`, `maps/BillsOlderSistersHouse.asm`, `maps/Colosseum.asm`, `maps/FuchsiaGym.asm`, +11 more |
| `Map Scripts 27` | ROMX | 5d:4000-5e41 | 7746 | ROMX 5d | `data/maps/scripts.asm`, `maps/CianwoodGym.asm`, `maps/CianwoodLugiaSpeechHouse.asm`, `maps/CianwoodPharmacy.asm`, +13 more |
| `Map Scripts 28` | ROMX | 5e:4000-6aca | 10955 | ROMX 5e | `data/maps/scripts.asm`, `maps/CeladonCafe.asm`, `maps/CeladonDeptStore1F.asm`, `maps/CeladonDeptStore2F.asm`, +19 more |
| `Map Scripts 29` | ROMX | 5f:4000-51d6 | 4567 | ROMX 5f | `data/maps/scripts.asm`, `maps/Route2Gate.asm`, `maps/Route2NuggetHouse.asm`, `maps/TrainerHouse1F.asm`, +7 more |
| `Map Scripts 30` | ROMX | 60:4000-6665 | 9830 | ROMX 60 | `data/maps/scripts.asm`, `maps/DayOfWeekSiblingsHouse.asm`, `maps/ElmsHouse.asm`, `maps/ElmsLab.asm`, +6 more |
| `Map Scripts 31` | ROMX | 61:4000-5921 | 6434 | ROMX 61 | `data/maps/scripts.asm`, `maps/CopycatsHouse1F.asm`, `maps/CopycatsHouse2F.asm`, `maps/FightingDojo.asm`, +10 more |
| `Map Scripts 32` | ROMX | 62:4000-4ead | 3758 | ROMX 62 | `data/maps/scripts.asm`, `maps/CherrygroveEvolutionSpeechHouse.asm`, `maps/CherrygroveGymSpeechHouse.asm`, `maps/CherrygroveMart.asm`, +5 more |

## Important Labels

| Label | Address | Source |
| --- | --- | --- |
| `BossAI_IncrementTurnsElapsed` | 0e:553b | `engine/battle/ai/boss.asm:1` |
| `BossAI_RecordPlayerSwitch` | 0e:5564 | `engine/battle/ai/boss.asm:26` |
| `BossAI_SelectMove` | 0e:5b9f | `engine/battle/ai/boss.asm:1081` |
| `BossAI_SwitchOrTryItem` | 0e:5c8a | `engine/battle/ai/boss.asm:1268` |
| `BossAI_ComputeSwitchConfidence` | 0e:6110 | `engine/battle/ai/boss.asm:2095` |
| `BossAI_PredictPlayerSwitch` | 0e:617d | `engine/battle/ai/boss.asm:2158` |
| `BossAI_RecordRevealedPlayerMove` | 0e:5650 | `engine/battle/ai/boss.asm:216` |
| `BossAI_CurrentEnemyMoveHasKOPressure` | 0e:5e9f | `engine/battle/ai/boss.asm:1639` |
| `BossAI_CurrentEnemyMovePressureScore` | 0e:5ec7 | `engine/battle/ai/boss.asm:1672` |
| `BossAI_PlayerHasPublicThreatVsEnemy` | 0e:5d7a | `engine/battle/ai/boss.asm:1430` |
| `BossAI_PublicEnemyFaster` | 0e:5f35 | `engine/battle/ai/boss.asm:1758` |
| `BossAI_CheckAbleToSwitchSafe` | 0e:5d30 | `engine/battle/ai/boss.asm:1374` |
| `BossAI_RefineSwitchCandidateForPlausibleRisk` | 0e:6bff | `engine/battle/ai/boss.asm:4085` |
| `BossAI_ApplyPlausibleRiskToSwitchConfidence` | 0e:6db6 | `engine/battle/ai/boss.asm:4370` |
| `BossAITierMap` | 0e:7179 | `data/trainers/ai_tiers.asm:1` |
| `CheckPlayerMoveTypeMatchups` | 0d:4a79 | `engine/battle/ai/switch.asm:1` |
| `AICompareSpeed` | 0e:523a | `engine/battle/ai/scoring.asm:2657` |
| `AIDamageCalc` | 0e:53ef | `engine/battle/ai/scoring.asm:3017` |
| `TypePassive_ApplyDamageModifiers_Far` | 0b:7389 | `engine/battle/type_passive_damage_mods.asm:44` |
| `TypePassive_TryDarkStatusShield_Far` | 0b:7916 | `engine/battle/type_passive_damage_mods.asm:1057` |
| `TypePassive_MaybePoisonRetaliation_Far` | 0b:7965 | `engine/battle/type_passive_damage_mods.asm:1118` |
| `ApplyLateGenDamageMultipliers_Far` | 0b:6fa0 | `engine/battle/late_gen_held_items.asm:164` |
| `HandleLateGenAfterHitEffects_Far` | 0b:703b | `engine/battle/late_gen_held_items.asm:261` |
| `TryActivateDittoImposter` | 01:7588 | `engine/battle/ditto_imposter.asm:1` |
| `Moves` | 10:5af6 | `data/moves/moves.asm:14` |
| `MoveEffects` | 09:7510 | `data/moves/effects.asm:3` |
| `MoveContactFlags` | 0b:7ad8 | `data/moves/contact_flags.asm:4` |
| `Spikes` | 09:7a19 | `data/moves/effects.asm:1504` |
| `RapidSpin` | 09:7aee | `data/moves/effects.asm:1751` |
| `ItemAttributes` | 01:68d5 | `data/items/attributes.asm:8` |
| `ItemDescriptions` | 6e:4000 | `data/items/descriptions.asm:1` |
| `ItemNames` | 6c:4000 | `data/items/names.asm:1` |
| `IsChoiceHeldEffect_Far` | 0b:72e9 | `engine/battle/late_gen_held_items.asm:719` |
| `IsMoveBlockedByAssaultVest_Far` | 0b:72f2 | `engine/battle/late_gen_held_items.asm:727` |
| `BaseData` | 14:5bb8 | `data/pokemon/base_stats.asm:21` |
| `EvosAttacksPointers` | 10:6893 | `data/pokemon/evos_attacks_pointers.asm:3` |
| `EggMovePointers` | 08:79fe | `data/pokemon/egg_move_pointers.asm:1` |
| `Special` | 03:422b | `engine/events/specials.asm:1` |
| `SpecialsPointers` | 03:4239 | `data/events/special_pointers.asm:14` |
| `MoveReminder` | 0b:4451 | `engine/events/move_reminder.asm:8` |
| `TMTutorTeachAnyTM` | 0b:4c25 | `engine/events/tm_tutor.asm:1` |
| `wBattleMode` | 01:d116 | `ram/wram.asm:2107` |
| `wEnemyMon` | 01:d0ef | `ram/wram.asm:2100` |
| `wBattleMon` | 00:cafc | `ram/wram.asm:747` |
| `hROMBank` | 00:ff9f | `ram/hram.asm:26` |
| `PokemonPicPointers` | 12:4000 | `data/pokemon/pic_pointers.asm:3` |
| `TrainerPicPointers` | 20:4000 | `data/trainers/pic_pointers.asm:3` |
| `Tilesets` | 05:56be | `data/tilesets.asm:13` |
| `Music` | 3a:506e | `audio/music_pointers.asm:3` |
| `SFX` | 3a:525e | `audio/sfx_pointers.asm:1` |
| `Cries` | 3a:5192 | `audio/cry_pointers.asm:1` |

## Warning Zones

- ROM0, WRAM0, WRAMX, and HRAM are global pressure points. Prefer moving new optional logic into ROMX banks with room.
- Battle-sensitive sections such as `Battle Core`, `Effect Commands`, `Enemy Trainers`, and `Late Gen Held Items` should be checked in this file after every substantial mechanics change.
- Generated files should be refreshed with `python scripts/generate_dev_index.py --rom pokegold` after linker addresses change.
- If this file disagrees with source after a build, regenerate it before using addresses for planning.
