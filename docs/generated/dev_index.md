# Developer ROM Index

Boss AI cognition note: if you are here for the Boss AI loop, think wildly in the journal before changing source; this index is the hard memory/bank reality check for those ideas.

Generated: 2026-05-02
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
- Start here: `engine/battle/ai/boss.asm`, `engine/battle/ai/move.asm`, `engine/battle/ai/scoring.asm`, `engine/battle/ai/items.asm`, `engine/battle/ai/switch.asm`, `engine/battle/core.asm`, `engine/battle/used_move_text.asm`, `engine/battle/read_trainer_attributes.asm`, `data/trainers/ai_tiers.asm`, `data/trainers/parties.asm`, `data/trainers/attributes.asm`, `constants/battle_constants.asm`
- Anchors: `BossAI_IncrementTurnsElapsed` (0e:45b5, `engine/battle/ai/boss.asm:1`); `BossAI_RecordPlayerSwitch` (0e:45de, `engine/battle/ai/boss.asm:26`); `BossAI_SelectMove` (0e:53ce, `engine/battle/ai/boss.asm:2331`); `BossAI_SwitchOrTryItem` (0e:54b9, `engine/battle/ai/boss.asm:2523`); `BossAI_ComputeSwitchConfidence` (0e:5c1d, `engine/battle/ai/boss.asm:3882`); `BossAI_PredictPlayerSwitch` (0e:5c9d, `engine/battle/ai/boss.asm:3955`); `BossAI_RecordRevealedPlayerMove` (0e:471a, `engine/battle/ai/boss.asm:290`); `BossAI_CurrentEnemyMoveHasKOPressure` (0e:5774, `engine/battle/ai/boss.asm:3009`); `BossAI_CurrentEnemyMovePressureScore` (0e:579c, `engine/battle/ai/boss.asm:3042`); `BossAI_PlayerHasPublicThreatVsEnemy` (0e:55b1, `engine/battle/ai/boss.asm:2692`); `BossAI_PublicEnemyFaster` (0e:59c6, `engine/battle/ai/boss.asm:3465`); `BossAI_CheckAbleToSwitchSafe` (0e:5567, `engine/battle/ai/boss.asm:2636`); `BossAI_RefineSwitchCandidateForPlausibleRisk` (0e:6977, `engine/battle/ai/boss.asm:6353`); `BossAI_ApplyPlausibleRiskToSwitchConfidence` (0e:6bab, `engine/battle/ai/boss.asm:6725`)

### Battle mechanics
- Intent: Shared damage, status, switching, item, and turn-flow rules.
- Start here: `engine/battle/core.asm`, `engine/battle/effect_commands.asm`, `engine/battle/type_passive_damage_mods.asm`, `engine/battle/late_gen_held_items.asm`, `engine/battle/move_effects`, `constants/battle_constants.asm`
- Anchors: `TypePassive_ApplyDamageModifiers_Far` (0e:75a5, `engine/battle/type_passive_damage_mods.asm:44`); `TypePassive_TryDarkStatusShield_Far` (0e:7b32, `engine/battle/type_passive_damage_mods.asm:1057`); `TypePassive_MaybePoisonRetaliation_Far` (0e:7b81, `engine/battle/type_passive_damage_mods.asm:1118`); `ApplyLateGenDamageMultipliers_Far` (0e:714a, `engine/battle/late_gen_held_items.asm:170`); `HandleLateGenAfterHitEffects_Far` (0e:7205, `engine/battle/late_gen_held_items.asm:291`); `TryActivateDittoImposter` (01:7a13, `engine/battle/ditto_imposter.asm:1`)

### Moves
- Intent: Move stats, effects, descriptions, contact flags, and animations.
- Start here: `data/moves/moves.asm`, `data/moves/effects.asm`, `data/moves/effects_pointers.asm`, `data/moves/contact_flags.asm`, `data/moves/descriptions.asm`, `constants/move_constants.asm`
- Anchors: `Moves` (10:5af6, `.claude/worktrees/optimistic-benz-e61aa2/data/moves/moves.asm:14`); `MoveEffects` (09:7510, `.claude/worktrees/optimistic-benz-e61aa2/data/moves/effects.asm:3`); `MoveContactFlags` (0e:7cdd, `data/moves/contact_flags.asm:4`); `Spikes` (09:7a2c, `.claude/worktrees/optimistic-benz-e61aa2/data/moves/effects.asm:1502`); `RapidSpin` (09:7b01, `.claude/worktrees/optimistic-benz-e61aa2/data/moves/effects.asm:1749`)

### Items and held items
- Intent: Item data, descriptions, pockets, marts, and battle held effects.
- Start here: `data/items/attributes.asm`, `data/items/descriptions.asm`, `data/items/names.asm`, `data/items/marts.asm`, `engine/items`, `engine/battle/late_gen_held_items.asm`
- Anchors: `ItemAttributes` (01:6930, `.claude/worktrees/optimistic-benz-e61aa2/data/items/attributes.asm:8`); `ItemDescriptions` (6e:4000, `.claude/worktrees/optimistic-benz-e61aa2/data/items/descriptions.asm:1`); `ItemNames` (6c:4000, `.claude/worktrees/optimistic-benz-e61aa2/data/items/names.asm:1`); `IsChoiceHeldEffect_Far` (0e:7505, `engine/battle/late_gen_held_items.asm:800`); `IsMoveBlockedByAssaultVest_Far` (0e:750e, `engine/battle/late_gen_held_items.asm:808`)

### Pokemon data and weak-Pokemon buffs
- Intent: Base stats, types, level-up moves, evolutions, egg moves, and names.
- Start here: `data/pokemon/base_stats.asm`, `data/pokemon/base_stats`, `data/pokemon/evos_attacks.asm`, `data/pokemon/evos_attacks_pointers.asm`, `data/pokemon/egg_moves.asm`, `constants/pokemon_constants.asm`
- Anchors: `BaseData` (14:5bd4, `.claude/worktrees/optimistic-benz-e61aa2/data/pokemon/base_stats.asm:21`); `EvosAttacksPointers` (10:6893, `.claude/worktrees/optimistic-benz-e61aa2/data/pokemon/evos_attacks_pointers.asm:3`); `EggMovePointers` (08:79fe, `.claude/worktrees/optimistic-benz-e61aa2/data/pokemon/egg_move_pointers.asm:1`)

### Maps, events, and QoL scripts
- Intent: Map scripts, specials, NPC events, progression, tutors, and reminders.
- Start here: `maps`, `data/maps`, `data/events/special_pointers.asm`, `engine/events/move_reminder.asm`, `engine/events/tm_tutor.asm`, `engine/overworld`
- Anchors: `Special` (03:422b, `.claude/worktrees/optimistic-benz-e61aa2/engine/events/specials.asm:1`); `SpecialsPointers` (03:4239, `.claude/worktrees/optimistic-benz-e61aa2/data/events/special_pointers.asm:14`); `MoveReminder` (0b:4451, `engine/events/move_reminder.asm:8`); `TMTutorTeachAnyTM` (0b:4bf2, `engine/events/tm_tutor.asm:1`)

### RAM, saves, and temporary battle state
- Intent: WRAM, SRAM, VRAM, HRAM, save data, and low-memory pressure points.
- Start here: `ram/wram.asm`, `ram/sram.asm`, `ram/vram.asm`, `ram/hram.asm`
- Anchors: `wBattleMode` (01:d116, `.claude/worktrees/optimistic-benz-e61aa2/ram/wram.asm:2100`); `wEnemyMon` (01:d0ef, `.claude/worktrees/optimistic-benz-e61aa2/ram/wram.asm:2093`); `wBattleMon` (00:cafc, `.claude/worktrees/optimistic-benz-e61aa2/ram/wram.asm:747`); `hROMBank` (00:ff9f, `.claude/worktrees/optimistic-benz-e61aa2/ram/hram.asm:26`)

### Graphics
- Intent: Pokemon pics, trainer pics, sprites, tilesets, palettes, and UI art.
- Start here: `gfx`, `data/sprites`, `data/tilesets.asm`, `gfx/pics_gold.asm`
- Anchors: `PokemonPicPointers` (12:4000, `.claude/worktrees/optimistic-benz-e61aa2/data/pokemon/pic_pointers.asm:3`); `TrainerPicPointers` (20:4000, `.claude/worktrees/optimistic-benz-e61aa2/data/trainers/pic_pointers.asm:3`); `Tilesets` (05:56de, `.claude/worktrees/optimistic-benz-e61aa2/data/tilesets.asm:13`)

### Audio
- Intent: Music, cries, sound effects, engine data, and song banks.
- Start here: `audio`, `audio.asm`, `constants/music_constants.asm`, `constants/sfx_constants.asm`
- Anchors: `Music` (3a:506e, `.claude/worktrees/optimistic-benz-e61aa2/audio/music_pointers.asm:3`); `SFX` (3a:525e, `.claude/worktrees/optimistic-benz-e61aa2/audio/sfx_pointers.asm:1`); `Cries` (3a:5192, `.claude/worktrees/optimistic-benz-e61aa2/audio/cry_pointers.asm:1`)

## Memory Summary

| Region | Used | Free | Banks |
| --- | ---: | ---: | ---: |
| ROM0 | 16162 | 222 |  |
| ROMX | 1157695 | 923073 | 127 |
| SRAM | 31699 | 1069 | 4 |
| WRAM0 | 4047 | 49 |  |
| WRAMX | 4096 | 0 |  |
| HRAM | 127 | 0 |  |

### Boss AI WRAM Reserve

Boss AI state is carved out of full WRAMX bank 1 but has its own reserved block. Add Boss AI bytes here only after checking this budget.

| Build | Used bytes | Reserved free bytes |
| --- | ---: | ---: |
| Normal | 104 | 36 |
| With `BOSS_AI_TRACE` fields | 123 | 17 |

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
| ROMX | 0d | 20 |
| ROMX | 16 | 48 |
| WRAM0 | 00 | 49 |
| ROMX | 20 | 64 |
| ROMX | 30 | 64 |
| ROMX | 07 | 67 |
| ROMX | 3a | 73 |
| ROMX | 19 | 77 |

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
| `Home` | ROM0 | 00:0150-3ff9 | 16042 | ROM0 00 | `.claude/worktrees/optimistic-benz-e61aa2/home.asm`, `.claude/worktrees/optimistic-benz-e61aa2/home/delay.asm`, `.claude/worktrees/optimistic-benz-e61aa2/home/fade.asm`, `.claude/worktrees/optimistic-benz-e61aa2/home/lcd.asm`, +56 more |
| `bankB` | ROMX | 0b:4000-4d69 | 3434 | ROMX 0b | `.claude/worktrees/optimistic-benz-e61aa2/engine/battle/ai/redundant.asm`, `.claude/worktrees/optimistic-benz-e61aa2/engine/battle/trainer_huds.asm`, `.claude/worktrees/optimistic-benz-e61aa2/engine/items/print_item_description.asm`, `.claude/worktrees/optimistic-benz-e61aa2/main.asm`, +11 more |
| `Effect Commands` | ROMX | 0d:4000-7feb | 16364 | ROMX 0d | `.claude/worktrees/optimistic-benz-e61aa2/engine/battle/effect_commands.asm`, `.claude/worktrees/optimistic-benz-e61aa2/engine/battle/used_move_text.asm`, `.claude/worktrees/optimistic-benz-e61aa2/main.asm`, `engine/battle/effect_commands.asm`, +2 more |
| `Enemy Trainers` | ROMX | 0e:4000-704e | 12367 | ROMX 0e | `.claude/worktrees/optimistic-benz-e61aa2/engine/battle/ai/items.asm`, `.claude/worktrees/optimistic-benz-e61aa2/main.asm`, `engine/battle/ai/boss.asm`, `engine/battle/ai/items.asm`, +4 more |
| `Late Gen Held Items` | ROMX | 0e:704f-7dda | 3468 |  | `engine/battle/late_gen_held_items.asm`, `engine/battle/type_passive_damage_mods.asm`, `main.asm` |
| `Battle Core` | ROMX | 0f:4000-7bb6 | 15287 | ROMX 0f | `.claude/worktrees/optimistic-benz-e61aa2/engine/battle/core.asm`, `.claude/worktrees/optimistic-benz-e61aa2/main.asm`, `data/battle/effect_command_pointers.asm`, `engine/battle/core.asm`, +1 more |
| `Evolutions and Attacks` | ROMX | 10:6893-7f96 | 5892 | ROMX 10 | `.claude/worktrees/optimistic-benz-e61aa2/data/pokemon/evos_attacks.asm`, `.claude/worktrees/optimistic-benz-e61aa2/data/pokemon/evos_attacks_pointers.asm`, `data/pokemon/evos_attacks.asm`, `data/pokemon/evos_attacks_pointers.asm` |
| `Maps` | ROMX | 25:4000-65f8 | 9721 | ROMX 25 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/map_data.asm`, `.claude/worktrees/optimistic-benz-e61aa2/data/maps/maps.asm`, `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scenes.asm`, `data/maps/attributes.asm`, +5 more |
| `Events` | ROMX | 25:65f9-7d99 | 6049 | ROMX 25 | `.claude/worktrees/optimistic-benz-e61aa2/engine/overworld/events.asm`, `data/wild/bug_contest_mons.asm`, `engine/events/trainer_scripts.asm`, `engine/overworld/cmd_queue.asm`, +2 more |
| `Audio` | ROMX | 3a:4000-5491 | 5266 | ROMX 3a | `.claude/worktrees/optimistic-benz-e61aa2/audio.asm`, `.claude/worktrees/optimistic-benz-e61aa2/audio/engine.asm`, `audio.asm`, `audio/cry_pointers.asm`, +5 more |
| `Songs 1` | ROMX | 3a:5492-7fb6 | 11045 | ROMX 3a | `.claude/worktrees/optimistic-benz-e61aa2/audio.asm`, `.claude/worktrees/optimistic-benz-e61aa2/audio/music/rivalbattle.asm`, `.claude/worktrees/optimistic-benz-e61aa2/audio/music/rocketbattle.asm`, `.claude/worktrees/optimistic-benz-e61aa2/audio/music/route36.asm`, +16 more |
| `Songs 2` | ROMX | 3b:4000-7ef4 | 16117 | ROMX 3b | `.claude/worktrees/optimistic-benz-e61aa2/audio.asm`, `.claude/worktrees/optimistic-benz-e61aa2/audio/music/kantogymbattle.asm`, `.claude/worktrees/optimistic-benz-e61aa2/audio/music/route1.asm`, `.claude/worktrees/optimistic-benz-e61aa2/audio/music/route12.asm`, +34 more |
| `Songs 3` | ROMX | 3c:4000-4940 | 2369 | ROMX 3c | `.claude/worktrees/optimistic-benz-e61aa2/audio.asm`, `.claude/worktrees/optimistic-benz-e61aa2/audio/music/evolution.asm`, `.claude/worktrees/optimistic-benz-e61aa2/audio/music/halloffame.asm`, `.claude/worktrees/optimistic-benz-e61aa2/audio/music/healpokemon.asm`, +10 more |
| `Sound Effects` | ROMX | 3c:4941-6746 | 7686 | ROMX 3c | `.claude/worktrees/optimistic-benz-e61aa2/audio.asm`, `.claude/worktrees/optimistic-benz-e61aa2/audio/sfx.asm`, `audio.asm`, `audio/sfx.asm` |
| `Cries` | ROMX | 3c:6747-7f75 | 6191 | ROMX 3c | `.claude/worktrees/optimistic-benz-e61aa2/audio.asm`, `.claude/worktrees/optimistic-benz-e61aa2/audio/cries.asm`, `.claude/worktrees/optimistic-benz-e61aa2/data/pokemon/cries.asm`, `audio.asm`, +2 more |
| `Songs 4` | ROMX | 3d:4000-7ef2 | 16115 | ROMX 3d | `.claude/worktrees/optimistic-benz-e61aa2/audio.asm`, `.claude/worktrees/optimistic-benz-e61aa2/audio/music/celadoncity.asm`, `.claude/worktrees/optimistic-benz-e61aa2/audio/music/gymleadervictory.asm`, `.claude/worktrees/optimistic-benz-e61aa2/audio/music/successfulcapture.asm`, +40 more |
| `Standard Scripts` | ROMX | 40:4000-62d3 | 8916 | ROMX 40 | `.claude/worktrees/optimistic-benz-e61aa2/engine/events/std_scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/main.asm`, `data/text/battle.asm`, `engine/events/std_scripts.asm`, +1 more |
| `Phone Scripts` | ROMX | 41:4000-614c | 8525 | ROMX 41 | `.claude/worktrees/optimistic-benz-e61aa2/engine/phone/scripts/bill.asm`, `.claude/worktrees/optimistic-benz-e61aa2/engine/phone/scripts/elm.asm`, `.claude/worktrees/optimistic-benz-e61aa2/engine/phone/scripts/mom.asm`, `.claude/worktrees/optimistic-benz-e61aa2/engine/phone/scripts/trainers.asm`, +15 more |
| `Map Scripts 1` | ROMX | 42:4000-5dd9 | 7642 | ROMX 42 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/SproutTower1F.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/SproutTower2F.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/SproutTower3F.asm`, +23 more |
| `Map Scripts 2` | ROMX | 43:4000-7197 | 12696 | ROMX 43 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/NationalPark.asm`, `data/maps/scripts.asm`, `maps/NationalPark.asm`, +6 more |
| `Map Scripts 3` | ROMX | 44:4000-6fb0 | 12209 | ROMX 44 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/RuinsOfAlphAerodactylChamber.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/RuinsOfAlphHoOhChamber.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/RuinsOfAlphKabutoChamber.asm`, +21 more |
| `Map Scripts 4` | ROMX | 45:4000-6f47 | 12104 | ROMX 45 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/MahoganyMart1F.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/TeamRocketBaseB1F.asm`, `data/maps/scripts.asm`, +5 more |
| `Map Scripts 5` | ROMX | 46:4000-636f | 9072 | ROMX 46 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/GoldenrodUnderground.asm`, `data/maps/scripts.asm`, `maps/GoldenrodDeptStoreB1F.asm`, +12 more |
| `Map Scripts 6` | ROMX | 47:4000-49c8 | 2505 | ROMX 47 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/DarkCaveBlackthornEntrance.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/DarkCaveVioletEntrance.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/SilverCaveItemRooms.asm`, +29 more |
| `Map Scripts 7` | ROMX | 48:4000-654d | 9550 | ROMX 48 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/CherrygroveCity.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/NewBarkTown.asm`, `data/maps/scripts.asm`, +6 more |
| `Map Scripts 8` | ROMX | 49:4000-5f50 | 8017 | ROMX 49 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/EcruteakCity.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/OlivineCity.asm`, `data/maps/scripts.asm`, +6 more |
| `Map Scripts 9` | ROMX | 4a:4000-6017 | 8216 | ROMX 4a | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/Route26.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/Route27.asm`, `data/maps/scripts.asm`, +6 more |
| `Map Scripts 10` | ROMX | 4b:4000-67be | 10175 | ROMX 4b | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/Route32.asm`, `data/maps/scripts.asm`, `maps/Route32.asm`, +4 more |
| `Map Scripts 11` | ROMX | 4c:4000-5f25 | 7974 | ROMX 4c | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/Route37.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/Route38.asm`, `data/maps/scripts.asm`, +6 more |
| `Map Scripts 12` | ROMX | 4d:4000-5e59 | 7770 | ROMX 4d | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/Route43.asm`, `data/maps/scripts.asm`, `maps/PewterCity.asm`, +5 more |
| `Map Scripts 13` | ROMX | 4e:4000-6173 | 8564 | ROMX 4e | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/PalletTown.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/Route1.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/Route21.asm`, +17 more |
| `Map Scripts 14` | ROMX | 4f:4000-64b1 | 9394 | ROMX 4f | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/Route13.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/Route14.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/Route15.asm`, +12 more |
| `Map Scripts 15` | ROMX | 50:4000-58ec | 6381 | ROMX 50 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/Route24.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/Route25.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/Route9.asm`, +10 more |
| `Map Scripts 16` | ROMX | 51:4000-5dfd | 7678 | ROMX 51 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/OlivineCafe.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/OlivineGoodRodHouse.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/OlivineGym.asm`, +20 more |
| `Map Scripts 17` | ROMX | 52:4000-5ccd | 7374 | ROMX 52 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/DanceTheater.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/EcruteakLugiaSpeechHouse.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/EcruteakPokecenter1F.asm`, +11 more |
| `Map Scripts 18` | ROMX | 53:4000-5e48 | 7753 | ROMX 53 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/BlackthornGym1F.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/BlackthornGym2F.asm`, `data/maps/scripts.asm`, +15 more |
| `Map Scripts 19` | ROMX | 54:4000-5aa2 | 6819 | ROMX 54 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/CeruleanGym.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/CeruleanGymBadgeSpeechHouse.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/CeruleanPokecenter1F.asm`, +15 more |
| `Map Scripts 20` | ROMX | 55:4000-55a3 | 5540 | ROMX 55 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/AzaleaMart.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/AzaleaPokecenter1F.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/CharcoalKiln.asm`, +7 more |
| `Map Scripts 21` | ROMX | 56:4000-75d9 | 13786 | ROMX 56 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/EarlsPokemonAcademy.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/VioletGym.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/VioletMart.asm`, +13 more |
| `Map Scripts 22` | ROMX | 57:4000-764a | 13899 | ROMX 57 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/GoldenrodBikeShop.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/GoldenrodGym.asm`, `data/maps/scripts.asm`, +20 more |
| `Map Scripts 23` | ROMX | 59:4000-5fc6 | 8135 | ROMX 59 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/PokemonFanClub.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/VermilionFishingSpeechHouse.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/VermilionMagnetTrainSpeechHouse.asm`, +18 more |
| `Map Scripts 24` | ROMX | 5a:4000-5f84 | 8069 | ROMX 5a | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/IndigoPlateauPokecenter1F.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/PewterGym.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/PewterMart.asm`, +18 more |
| `Map Scripts 25` | ROMX | 5b:4000-695c | 10589 | ROMX 5b | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/OlivinePort.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/VermilionPort.asm`, `data/maps/scripts.asm`, +12 more |
| `Map Scripts 26` | ROMX | 5c:4000-5608 | 5641 | ROMX 5c | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/BillsOlderSistersHouse.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/FuchsiaGym.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/FuchsiaMart.asm`, +17 more |
| `Map Scripts 27` | ROMX | 5d:4000-5e38 | 7737 | ROMX 5d | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/LavRadioTower1F.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/LavenderMart.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/LavenderNameRater.asm`, +22 more |
| `Map Scripts 28` | ROMX | 5e:4000-6aca | 10955 | ROMX 5e | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/CeladonDeptStore1F.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/CeladonDeptStore2F.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/CeladonDeptStore3F.asm`, +26 more |
| `Map Scripts 29` | ROMX | 5f:4000-51d6 | 4567 | ROMX 5f | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/TrainerHouse1F.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/TrainerHouseB1F.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/ViridianGym.asm`, +12 more |
| `Map Scripts 30` | ROMX | 60:4000-666a | 9835 | ROMX 60 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/ElmsLab.asm`, `data/maps/scripts.asm`, `maps/DayOfWeekSiblingsHouse.asm`, +8 more |
| `Map Scripts 31` | ROMX | 61:4000-5921 | 6434 | ROMX 61 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/FightingDojo.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/SaffronGym.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/SaffronMart.asm`, +16 more |
| `Map Scripts 32` | ROMX | 62:4000-4ead | 3758 | ROMX 62 | `.claude/worktrees/optimistic-benz-e61aa2/data/maps/scripts.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/CherrygroveEvolutionSpeechHouse.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/CherrygroveGymSpeechHouse.asm`, `.claude/worktrees/optimistic-benz-e61aa2/maps/CherrygroveMart.asm`, +13 more |

## Important Labels

| Label | Address | Source |
| --- | --- | --- |
| `BossAI_IncrementTurnsElapsed` | 0e:45b5 | `engine/battle/ai/boss.asm:1` |
| `BossAI_RecordPlayerSwitch` | 0e:45de | `engine/battle/ai/boss.asm:26` |
| `BossAI_SelectMove` | 0e:53ce | `engine/battle/ai/boss.asm:2331` |
| `BossAI_SwitchOrTryItem` | 0e:54b9 | `engine/battle/ai/boss.asm:2523` |
| `BossAI_ComputeSwitchConfidence` | 0e:5c1d | `engine/battle/ai/boss.asm:3882` |
| `BossAI_PredictPlayerSwitch` | 0e:5c9d | `engine/battle/ai/boss.asm:3955` |
| `BossAI_RecordRevealedPlayerMove` | 0e:471a | `engine/battle/ai/boss.asm:290` |
| `BossAI_CurrentEnemyMoveHasKOPressure` | 0e:5774 | `engine/battle/ai/boss.asm:3009` |
| `BossAI_CurrentEnemyMovePressureScore` | 0e:579c | `engine/battle/ai/boss.asm:3042` |
| `BossAI_PlayerHasPublicThreatVsEnemy` | 0e:55b1 | `engine/battle/ai/boss.asm:2692` |
| `BossAI_PublicEnemyFaster` | 0e:59c6 | `engine/battle/ai/boss.asm:3465` |
| `BossAI_CheckAbleToSwitchSafe` | 0e:5567 | `engine/battle/ai/boss.asm:2636` |
| `BossAI_RefineSwitchCandidateForPlausibleRisk` | 0e:6977 | `engine/battle/ai/boss.asm:6353` |
| `BossAI_ApplyPlausibleRiskToSwitchConfidence` | 0e:6bab | `engine/battle/ai/boss.asm:6725` |
| `BossAITierMap` | 0e:6fa3 | `data/trainers/ai_tiers.asm:1` |
| `CheckPlayerMoveTypeMatchups` | 0d:4a79 | `.claude/worktrees/optimistic-benz-e61aa2/engine/battle/ai/switch.asm:1` |
| `AICompareSpeed` | 0b:7b28 | `.claude/worktrees/optimistic-benz-e61aa2/engine/battle/ai/scoring.asm:2642` |
| `AIDamageCalc` | 0b:7cdd | `.claude/worktrees/optimistic-benz-e61aa2/engine/battle/ai/scoring.asm:3002` |
| `TypePassive_ApplyDamageModifiers_Far` | 0e:75a5 | `engine/battle/type_passive_damage_mods.asm:44` |
| `TypePassive_TryDarkStatusShield_Far` | 0e:7b32 | `engine/battle/type_passive_damage_mods.asm:1057` |
| `TypePassive_MaybePoisonRetaliation_Far` | 0e:7b81 | `engine/battle/type_passive_damage_mods.asm:1118` |
| `ApplyLateGenDamageMultipliers_Far` | 0e:714a | `engine/battle/late_gen_held_items.asm:170` |
| `HandleLateGenAfterHitEffects_Far` | 0e:7205 | `engine/battle/late_gen_held_items.asm:291` |
| `TryActivateDittoImposter` | 01:7a13 | `engine/battle/ditto_imposter.asm:1` |
| `Moves` | 10:5af6 | `.claude/worktrees/optimistic-benz-e61aa2/data/moves/moves.asm:14` |
| `MoveEffects` | 09:7510 | `.claude/worktrees/optimistic-benz-e61aa2/data/moves/effects.asm:3` |
| `MoveContactFlags` | 0e:7cdd | `data/moves/contact_flags.asm:4` |
| `Spikes` | 09:7a2c | `.claude/worktrees/optimistic-benz-e61aa2/data/moves/effects.asm:1502` |
| `RapidSpin` | 09:7b01 | `.claude/worktrees/optimistic-benz-e61aa2/data/moves/effects.asm:1749` |
| `ItemAttributes` | 01:6930 | `.claude/worktrees/optimistic-benz-e61aa2/data/items/attributes.asm:8` |
| `ItemDescriptions` | 6e:4000 | `.claude/worktrees/optimistic-benz-e61aa2/data/items/descriptions.asm:1` |
| `ItemNames` | 6c:4000 | `.claude/worktrees/optimistic-benz-e61aa2/data/items/names.asm:1` |
| `IsChoiceHeldEffect_Far` | 0e:7505 | `engine/battle/late_gen_held_items.asm:800` |
| `IsMoveBlockedByAssaultVest_Far` | 0e:750e | `engine/battle/late_gen_held_items.asm:808` |
| `BaseData` | 14:5bd4 | `.claude/worktrees/optimistic-benz-e61aa2/data/pokemon/base_stats.asm:21` |
| `EvosAttacksPointers` | 10:6893 | `.claude/worktrees/optimistic-benz-e61aa2/data/pokemon/evos_attacks_pointers.asm:3` |
| `EggMovePointers` | 08:79fe | `.claude/worktrees/optimistic-benz-e61aa2/data/pokemon/egg_move_pointers.asm:1` |
| `Special` | 03:422b | `.claude/worktrees/optimistic-benz-e61aa2/engine/events/specials.asm:1` |
| `SpecialsPointers` | 03:4239 | `.claude/worktrees/optimistic-benz-e61aa2/data/events/special_pointers.asm:14` |
| `MoveReminder` | 0b:4451 | `engine/events/move_reminder.asm:8` |
| `TMTutorTeachAnyTM` | 0b:4bf2 | `engine/events/tm_tutor.asm:1` |
| `wBattleMode` | 01:d116 | `.claude/worktrees/optimistic-benz-e61aa2/ram/wram.asm:2100` |
| `wEnemyMon` | 01:d0ef | `.claude/worktrees/optimistic-benz-e61aa2/ram/wram.asm:2093` |
| `wBattleMon` | 00:cafc | `.claude/worktrees/optimistic-benz-e61aa2/ram/wram.asm:747` |
| `hROMBank` | 00:ff9f | `.claude/worktrees/optimistic-benz-e61aa2/ram/hram.asm:26` |
| `PokemonPicPointers` | 12:4000 | `.claude/worktrees/optimistic-benz-e61aa2/data/pokemon/pic_pointers.asm:3` |
| `TrainerPicPointers` | 20:4000 | `.claude/worktrees/optimistic-benz-e61aa2/data/trainers/pic_pointers.asm:3` |
| `Tilesets` | 05:56de | `.claude/worktrees/optimistic-benz-e61aa2/data/tilesets.asm:13` |
| `Music` | 3a:506e | `.claude/worktrees/optimistic-benz-e61aa2/audio/music_pointers.asm:3` |
| `SFX` | 3a:525e | `.claude/worktrees/optimistic-benz-e61aa2/audio/sfx_pointers.asm:1` |
| `Cries` | 3a:5192 | `.claude/worktrees/optimistic-benz-e61aa2/audio/cry_pointers.asm:1` |

## Warning Zones

- ROM0, WRAM0, WRAMX, and HRAM are global pressure points. Prefer moving new optional logic into ROMX banks with room.
- Battle-sensitive sections such as `Battle Core`, `Effect Commands`, `Enemy Trainers`, and `Late Gen Held Items` should be checked in this file after every substantial mechanics change.
- Generated files should be refreshed with `python scripts/generate_dev_index.py --rom pokegold` after linker addresses change.
- If this file disagrees with source after a build, regenerate it before using addresses for planning.
