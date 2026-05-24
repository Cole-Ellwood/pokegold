# Hack Mechanics Reference

Audience: future Codex/helper agents working in this repo.

This is the fast, source-derived mechanics reference. Use it before making
any claim about type matchups, move category, move data, held items, or
Pokemon stats in this hack. If this doc disagrees with source, source wins
and this doc must be regenerated or corrected in the same change.

**Maintenance rule:** whenever a mechanics change touches a table or rule
covered here, update this reference in the same commit. Prefer rerunning
`python scripts/generate_hack_mechanics_reference.py` so the big tables
come from source instead of memory.

## Table Of Contents

- [Fast Rules That Prevent Bad Guesses](#fast-rules-that-prevent-bad-guesses)
- [Source Files To Trust](#source-files-to-trust)
- [Physical/Special Split](#physicalspecial-split)
- [Stat Math And Boosts](#stat-math-and-boosts)
- [Type Matchup Chart](#type-matchup-chart)
- [Dragon Type Passives](#dragon-type-passives)
- [Move Effects To Check First](#move-effects-to-check-first)
- [All Move Data](#all-move-data)
- [Held Items And Item Attributes](#held-items-and-item-attributes)
- [Pokemon Base Stats And Types](#pokemon-base-stats-and-types)
- [Learnsets, TMs, Trainers, And Boss AI Data](#learnsets-tms-trainers-and-boss-ai-data)
- [Fixture And Helper-Note Audit Rules](#fixture-and-helper-note-audit-rules)

## Fast Rules That Prevent Bad Guesses

- Dark is special. Crunch, Pursuit, Bite, Thief, Faint Attack, and Beat Up
  use Special Attack unless a move has a fixed/special-case effect.
- Ghost, Poison, Bug, Rock, Ground, Steel, Flying, Fighting, and Normal are
  physical types.
- Fire, Water, Grass, Electric, Psychic, Ice, Dragon, and Dark are special
  types.
- This hack keeps the Gen 2 type-based category split. Do not use modern
  per-move physical/special memory.
- Outrage is the special Dragon exception: Dragon-typed users run Outrage
  physically only when current Attack is greater than current Special
  Attack. Ties and non-Dragon users keep it special.
- Dragon Dance is not plain +Atk here. Its script uses `bestattackup`, which
  raises the user's current higher offensive stat, then raises Speed.
  Ties raise Attack.
- Stat stages multiply the already-calculated battle stat, not the base
  stat. A base 100 Attack Pokemon at +2 is stronger than a base 200 Attack
  Pokemon at +0 because +2 doubles the computed stat after level, DV, Stat
  Exp, and the +5 floor.
- Steel/Dragon Steelix does not resist Ground. Ground is super-effective on
  Steel and neutral on Dragon, so Ground is 2x into Steelix.
- Grass is neutral into Flying in this hack. Do not call Giga Drain resisted
  into Pidgey solely because of Flying.
- Fire is 2x into Ice/Ground Piloswine, not 4x.
- Dark hits Steel neutrally in this hack; Ghost does no damage to Steel.
- Dragon's Majesty is offensive: Dragon attackers convert type-chart
  immunities to resistances for damaging non-fixed-damage moves.
- Dragon's defensive passive is Imperial Scales: Dragon defenders reduce
  non-super-effective hits, half Dragon by 2/3 and full Dragon by 1/2.

## Source Files To Trust

| Question | Source |
| --- | --- |
| Type constants and physical/special threshold | `constants/type_constants.asm` |
| Type matchups | `data/types/type_matchups.asm` |
| Move power/type/accuracy/PP/effect | `data/moves/moves.asm` |
| Move effect scripts | `data/moves/effects.asm` and `engine/battle/effect_commands.asm` |
| Move priority | `data/moves/effects_priorities.asm` plus `constants/battle_constants.asm` |
| Contact flags | `data/moves/contact_flags.asm` |
| Held item constants | `constants/item_constants.asm` |
| Item attributes | `data/items/attributes.asm` |
| Late-gen held item behavior | `engine/battle/late_gen_held_items.asm` |
| Type passive behavior | `engine/battle/type_passive_damage_mods.asm` |
| Base stats/types/wild items/TM learnsets | `data/pokemon/base_stats/*.asm` |
| Level-up moves/evolutions | `data/pokemon/evos_attacks.asm` |
| Trainer rosters | `data/trainers/parties.asm` |
| Boss AI preference fixtures | `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json` |

## Physical/Special Split

The category is decided by the move type constant. Types with constants
below `SPECIAL` (20) are physical; types at or above it are special.

| Category | Types |
| --- | --- |
| Physical | Normal, Fighting, Flying, Poison, Ground, Rock, Bug, Ghost, Steel |
| Special | Fire, Water, Grass, Electric, Psychic, Ice, Dragon, Dark |

Outrage exception source: `TypePassive_GetEffectiveMoveCategory_Far` in
`engine/battle/type_passive_damage_mods.asm`.

## Stat Math And Boosts

Source: `engine/pokemon/move_mon.asm`, `engine/battle/effect_commands.asm`,
and `data/battle/stat_multipliers.asm`.

Computed stats use Gen 2 DVs and Stat Exp:

```text
Non-HP = floor(((2 * (base + DV)) + floor(sqrt(StatExp) / 4)) * level / 100) + 5
HP     = floor(((2 * (base + HP_DV)) + floor(sqrt(HPStatExp) / 4)) * level / 100) + level + 10
```

Battle stat stages then multiply the computed battle stat:

| Stage | Multiplier | Stage | Multiplier |
| --- | --- | --- | --- |
| +1 | 1.5x | -1 | 0.66x |
| +2 | 2.0x | -2 | 0.5x |
| +3 | 2.5x | -3 | 0.4x |
| +4 | 3.0x | -4 | 0.33x |
| +5 | 3.5x | -5 | 0.28x |
| +6 | 4.0x | -6 | 0.25x |

The stored level is base-7 encoded: `BASE_STAT_LEVEL = 7` means +0,
`MAX_STAT_LEVEL = 13` means +6.

## Type Matchup Chart

Single-type matchup values below come directly from `data/types/type_matchups.asm`.
For dual types, multiply both defender columns. Foresight only removes the
Normal/Fighting into Ghost immunities listed after the `db -2` sentinel.

| Attack \ Defend | Normal | Fighting | Flying | Poison | Ground | Rock | Bug | Ghost | Steel | Fire | Water | Grass | Electric | Psychic | Ice | Dragon | Dark |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Normal | 1 | 1 | 1 | 1 | 1 | 1/2 | 1 | 0 | 1/2 | 1 | 1 | 1 | 1 | 1/2 | 1 | 1 | 1 |
| Fighting | 2 | 1 | 1/2 | 1 | 1 | 2 | 1 | 0 | 2 | 1 | 1 | 1 | 1 | 1/2 | 2 | 1 | 2 |
| Flying | 1 | 2 | 1 | 1 | 1 | 1/2 | 2 | 1 | 1/2 | 1 | 1 | 2 | 1/2 | 1 | 1 | 1 | 1 |
| Poison | 2 | 1 | 1 | 1/2 | 1/2 | 1/2 | 1 | 1/2 | 0 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | 1 |
| Ground | 1 | 1 | 0 | 2 | 1 | 2 | 1/2 | 0 | 2 | 1 | 1 | 1/2 | 2 | 1 | 1 | 1 | 1 |
| Rock | 1 | 1/2 | 2 | 1 | 1/2 | 1 | 2 | 1 | 1/2 | 2 | 1 | 1 | 1 | 1/2 | 2 | 1 | 1 |
| Bug | 1 | 1/2 | 1/2 | 1/2 | 1 | 1 | 1 | 1/2 | 1/2 | 1/2 | 1 | 2 | 1 | 2 | 1 | 1 | 2 |
| Ghost | 0 | 2 | 1 | 1 | 1 | 1 | 1 | 2 | 0 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1/2 |
| Steel | 1 | 1/2 | 1 | 1 | 1 | 2 | 1 | 1 | 1/2 | 1/2 | 1/2 | 1 | 1 | 1 | 2 | 1 | 1 |
| Fire | 1 | 1 | 1 | 1 | 1 | 1/2 | 2 | 1 | 2 | 1/2 | 1/2 | 2 | 1 | 1 | 2 | 1/2 | 1 |
| Water | 1 | 1 | 1 | 1 | 2 | 2 | 1 | 1 | 1 | 2 | 1/2 | 1/2 | 1 | 1 | 1/2 | 1/2 | 1 |
| Grass | 1 | 1 | 1 | 1/2 | 2 | 2 | 1/2 | 1 | 1/2 | 1/2 | 2 | 1/2 | 1 | 1 | 1 | 1/2 | 1 |
| Electric | 1 | 1 | 2 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 2 | 1/2 | 1/2 | 1 | 1 | 1/2 | 1 |
| Psychic | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1/2 | 1 | 1 | 1 | 1 | 1/2 | 1 | 1 | 0 |
| Ice | 1 | 1 | 2 | 1 | 2 | 1 | 1 | 1 | 1/2 | 1/2 | 1/2 | 2 | 1 | 1 | 1/2 | 2 | 1 |
| Dragon | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1/2 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 1 |
| Dark | 1 | 1/2 | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1/2 |

Foresight-specific no-effect rows:

| Attack | Defend | Normal Rule | With Foresight |
| --- | --- | --- | --- |
| Fighting | Ghost | 0 | 1 |
| Normal | Ghost | 0 | 1 |

## Dragon Type Passives

Source: `engine/battle/type_passive_damage_mods.asm`,
`engine/battle/effect_commands.asm`, and
`engine/battle/ai/boss_platform.asm`.

- Dragon's Majesty is an offensive damage rule. If a damaging
  non-fixed-damage move would hit a type-chart immunity and the attacker
  has Dragon type contribution, the immunity is converted from 0x to
  0.5x. Fixed-damage and special-case effects such as Super Fang,
  Psywave, Counter, Mirror Coat, Bide, and Future Sight are excluded.
- The boss-AI no-item type-matchup helpers mirror Dragon's Majesty for
  type-only scoring: `BossAI_ApplyDragonsMajestyNoItem` converts a
  Dragon attacker's immunity result to not-very-effective. Use this
  when judging whether a switch is truly immune to a public Dragon-side
  threat.
- Imperial Scales is the Dragon defensive damage rule. If the defender has
  Dragon type contribution and the final matchup is not
  super-effective, damage is reduced by 2/3 for half Dragon and by
  1/2 for full Dragon.

## Move Effects To Check First

- `DragonDance` script: `bestattackup`, then Speed up. Source:
  `data/moves/effects.asm`.
- `BattleCommand_BestAttackUp`: compares current Attack and Special Attack;
  if SpA is greater it raises SpA, otherwise Attack. Source:
  `engine/battle/effect_commands.asm`.
- `CalmMind`: Special Attack +1 and Special Defense +1.
- `QuiverDance`: Special Attack +1, Special Defense +1, and Speed +1.
- Priority table: Protect/Endure use priority value 3; shared
  `EFFECT_PRIORITY_HIT` moves use priority value 2; base priority is 1.
  That means Quick Attack, Mach Punch, and ExtremeSpeed share the same
  priority tier in this hack.
- Thunder in rain skips the accuracy check in `BattleCommand_CheckHit`.
- Sleep, freeze, burn, paralysis, Substitute, weather, hazards, and type
  passives are summarized in `docs/agent_navigation/gen2_vs_modern_mechanics.md`,
  but source files above are authoritative.

## All Move Data

`special*` means Outrage: special by Dragon type unless the Outrage
exception makes it physical for a Dragon user with current Atk > SpA.
`fixed` means the move's main damage is fixed/special-case and should not
be reasoned about as ordinary Atk/SpA damage.

| ID | Move | Const | Type | Category | Power | Acc | PP | Effect | Chance | Contact |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | IRON HEAD | `IRON_HEAD` | Steel | physical | 80 | 100 | 25 | `EFFECT_FLINCH_HIT` | 20 | yes |
| 02 | KARATE CHOP | `KARATE_CHOP` | Fighting | physical | 80 | 100 | 25 | `EFFECT_NORMAL_HIT` | 0 | yes |
| 03 | DOUBLESLAP | `DOUBLESLAP` | Normal | physical | 25 | 100 | 10 | `EFFECT_MULTI_HIT` | 0 | yes |
| 04 | COMET PUNCH | `COMET_PUNCH` | Normal | physical | 25 | 100 | 15 | `EFFECT_MULTI_HIT` | 0 | yes |
| 05 | MEGA PUNCH | `MEGA_PUNCH` | Normal | physical | 100 | 85 | 20 | `EFFECT_NORMAL_HIT` | 0 | yes |
| 06 | PAY DAY | `PAY_DAY` | Normal | physical | 40 | 100 | 20 | `EFFECT_PAY_DAY` | 0 | no |
| 07 | FIRE PUNCH | `FIRE_PUNCH` | Fire | special | 75 | 100 | 15 | `EFFECT_BURN_HIT` | 10 | yes |
| 08 | ICE PUNCH | `ICE_PUNCH` | Ice | special | 75 | 100 | 15 | `EFFECT_FREEZE_HIT` | 10 | yes |
| 09 | THUNDERPUNCH | `THUNDERPUNCH` | Electric | special | 75 | 100 | 15 | `EFFECT_PARALYZE_HIT` | 10 | yes |
| 0A | SCRATCH | `SCRATCH` | Normal | physical | 40 | 100 | 35 | `EFFECT_NORMAL_HIT` | 0 | yes |
| 0B | VICEGRIP | `VICEGRIP` | Normal | physical | 55 | 100 | 30 | `EFFECT_NORMAL_HIT` | 0 | yes |
| 0C | GUILLOTINE | `GUILLOTINE` | Normal | status | 0 | 30 | 5 | `EFFECT_OHKO` | 0 | yes |
| 0D | RAZOR WIND | `RAZOR_WIND` | Normal | physical | 140 | 100 | 15 | `EFFECT_RAZOR_WIND` | 0 | no |
| 0E | SWORDS DANCE | `SWORDS_DANCE` | Normal | status | 0 | 100 | 30 | `EFFECT_ATTACK_UP_2` | 0 | no |
| 0F | CUT | `CUT` | Normal | physical | 70 | 100 | 30 | `EFFECT_NORMAL_HIT` | 0 | yes |
| 10 | GUST | `GUST` | Flying | physical | 40 | 100 | 35 | `EFFECT_GUST` | 0 | no |
| 11 | WING ATTACK | `WING_ATTACK` | Flying | physical | 80 | 100 | 25 | `EFFECT_NORMAL_HIT` | 0 | yes |
| 12 | WHIRLWIND | `WHIRLWIND` | Normal | status | 0 | 100 | 20 | `EFFECT_FORCE_SWITCH` | 0 | no |
| 13 | FLY | `FLY` | Flying | physical | 70 | 100 | 15 | `EFFECT_FLY` | 0 | yes |
| 14 | BIND | `BIND` | Normal | physical | 15 | 100 | 20 | `EFFECT_TRAP_TARGET` | 0 | yes |
| 15 | SLAM | `SLAM` | Normal | physical | 120 | 80 | 20 | `EFFECT_NORMAL_HIT` | 0 | yes |
| 16 | VINE WHIP | `VINE_WHIP` | Grass | special | 50 | 100 | 35 | `EFFECT_NORMAL_HIT` | 0 | yes |
| 17 | STOMP | `STOMP` | Normal | physical | 65 | 100 | 20 | `EFFECT_STOMP` | 30 | yes |
| 18 | DOUBLE KICK | `DOUBLE_KICK` | Fighting | physical | 40 | 100 | 30 | `EFFECT_DOUBLE_HIT` | 0 | yes |
| 19 | MEGA KICK | `MEGA_KICK` | Normal | physical | 130 | 75 | 10 | `EFFECT_NORMAL_HIT` | 0 | yes |
| 1A | JUMP KICK | `JUMP_KICK` | Fighting | physical | 70 | 100 | 25 | `EFFECT_JUMP_KICK` | 0 | yes |
| 1B | ROLLING KICK | `ROLLING_KICK` | Fighting | physical | 60 | 85 | 15 | `EFFECT_FLINCH_HIT` | 30 | yes |
| 1C | SAND-ATTACK | `SAND_ATTACK` | Ground | status | 0 | 100 | 15 | `EFFECT_ACCURACY_DOWN` | 0 | no |
| 1D | HEADBUTT | `HEADBUTT` | Normal | physical | 70 | 100 | 15 | `EFFECT_FLINCH_HIT` | 30 | yes |
| 1E | HORN ATTACK | `HORN_ATTACK` | Normal | physical | 65 | 100 | 25 | `EFFECT_NORMAL_HIT` | 0 | yes |
| 1F | FURY ATTACK | `FURY_ATTACK` | Normal | physical | 25 | 100 | 20 | `EFFECT_MULTI_HIT` | 0 | yes |
| 20 | HORN DRILL | `HORN_DRILL` | Normal | fixed | 1 | 30 | 5 | `EFFECT_OHKO` | 0 | yes |
| 21 | TACKLE | `TACKLE` | Normal | physical | 40 | 100 | 35 | `EFFECT_NORMAL_HIT` | 0 | yes |
| 22 | BODY SLAM | `BODY_SLAM` | Normal | physical | 75 | 100 | 20 | `EFFECT_PARALYZE_HIT` | 30 | yes |
| 23 | WRAP | `WRAP` | Normal | physical | 15 | 100 | 20 | `EFFECT_TRAP_TARGET` | 0 | yes |
| 24 | TAKE DOWN | `TAKE_DOWN` | Normal | physical | 120 | 85 | 20 | `EFFECT_RECOIL_HIT` | 0 | yes |
| 25 | THRASH | `THRASH` | Normal | physical | 120 | 100 | 20 | `EFFECT_RAMPAGE` | 0 | yes |
| 26 | DOUBLE-EDGE | `DOUBLE_EDGE` | Normal | physical | 130 | 100 | 15 | `EFFECT_RECOIL_HIT` | 0 | yes |
| 27 | TAIL WHIP | `TAIL_WHIP` | Normal | status | 0 | 100 | 30 | `EFFECT_DEFENSE_DOWN` | 0 | no |
| 28 | POISON STING | `POISON_STING` | Poison | physical | 40 | 100 | 35 | `EFFECT_POISON_HIT` | 30 | no |
| 29 | TWINEEDLE | `TWINEEDLE` | Bug | physical | 45 | 100 | 20 | `EFFECT_POISON_MULTI_HIT` | 20 | no |
| 2A | PIN MISSILE | `PIN_MISSILE` | Bug | physical | 25 | 100 | 20 | `EFFECT_MULTI_HIT` | 0 | no |
| 2B | LEER | `LEER` | Normal | status | 0 | 100 | 30 | `EFFECT_DEFENSE_DOWN` | 0 | no |
| 2C | BITE | `BITE` | Dark | special | 60 | 100 | 25 | `EFFECT_FLINCH_HIT` | 30 | yes |
| 2D | GROWL | `GROWL` | Normal | status | 0 | 100 | 40 | `EFFECT_ATTACK_DOWN` | 0 | no |
| 2E | ROAR | `ROAR` | Normal | status | 0 | 100 | 20 | `EFFECT_FORCE_SWITCH` | 0 | no |
| 2F | SING | `SING` | Normal | status | 0 | 55 | 15 | `EFFECT_SLEEP` | 0 | no |
| 30 | SUPERSONIC | `SUPERSONIC` | Normal | status | 0 | 90 | 20 | `EFFECT_CONFUSE` | 0 | no |
| 31 | SONICBOOM | `SONICBOOM` | Normal | fixed | 20 | 90 | 20 | `EFFECT_STATIC_DAMAGE` | 0 | no |
| 32 | DISABLE | `DISABLE` | Normal | status | 0 | 100 | 20 | `EFFECT_DISABLE` | 0 | no |
| 33 | ACID | `ACID` | Poison | physical | 40 | 100 | 30 | `EFFECT_DEFENSE_DOWN_HIT` | 10 | no |
| 34 | EMBER | `EMBER` | Fire | special | 50 | 100 | 25 | `EFFECT_BURN_HIT` | 10 | no |
| 35 | FLAMETHROWER | `FLAMETHROWER` | Fire | special | 95 | 100 | 15 | `EFFECT_BURN_HIT` | 10 | no |
| 36 | MIST | `MIST` | Ice | status | 0 | 100 | 30 | `EFFECT_MIST` | 0 | no |
| 37 | WATER GUN | `WATER_GUN` | Water | special | 50 | 100 | 25 | `EFFECT_NORMAL_HIT` | 0 | no |
| 38 | HYDRO PUMP | `HYDRO_PUMP` | Water | special | 120 | 80 | 10 | `EFFECT_NORMAL_HIT` | 0 | no |
| 39 | SURF | `SURF` | Water | special | 95 | 100 | 15 | `EFFECT_NORMAL_HIT` | 0 | no |
| 3A | ICE BEAM | `ICE_BEAM` | Ice | special | 95 | 100 | 15 | `EFFECT_FREEZE_HIT` | 10 | no |
| 3B | BLIZZARD | `BLIZZARD` | Ice | special | 120 | 85 | 10 | `EFFECT_FREEZE_HIT` | 10 | no |
| 3C | PSYBEAM | `PSYBEAM` | Psychic | special | 65 | 100 | 20 | `EFFECT_CONFUSE_HIT` | 10 | no |
| 3D | BUBBLEBEAM | `BUBBLEBEAM` | Water | special | 65 | 100 | 20 | `EFFECT_SPEED_DOWN_HIT` | 10 | no |
| 3E | AURORA BEAM | `AURORA_BEAM` | Ice | special | 65 | 100 | 20 | `EFFECT_ATTACK_DOWN_HIT` | 10 | no |
| 3F | HYPER BEAM | `HYPER_BEAM` | Normal | physical | 180 | 90 | 5 | `EFFECT_HYPER_BEAM` | 0 | no |
| 40 | PECK | `PECK` | Flying | physical | 50 | 100 | 35 | `EFFECT_NORMAL_HIT` | 0 | yes |
| 41 | DRILL PECK | `DRILL_PECK` | Flying | physical | 110 | 100 | 15 | `EFFECT_NORMAL_HIT` | 0 | yes |
| 42 | SUBMISSION | `SUBMISSION` | Fighting | physical | 110 | 100 | 25 | `EFFECT_RECOIL_HIT` | 0 | yes |
| 43 | LOW KICK | `LOW_KICK` | Fighting | physical | 50 | 100 | 30 | `EFFECT_FLINCH_HIT` | 30 | yes |
| 44 | COUNTER | `COUNTER` | Fighting | fixed | 1 | 100 | 20 | `EFFECT_COUNTER` | 0 | yes |
| 45 | SEISMIC TOSS | `SEISMIC_TOSS` | Fighting | fixed | 1 | 100 | 20 | `EFFECT_LEVEL_DAMAGE` | 0 | yes |
| 46 | STRENGTH | `STRENGTH` | Normal | physical | 80 | 100 | 25 | `EFFECT_NORMAL_HIT` | 0 | yes |
| 47 | ABSORB | `ABSORB` | Grass | special | 30 | 100 | 35 | `EFFECT_LEECH_HIT` | 0 | no |
| 48 | MEGA DRAIN | `MEGA_DRAIN` | Grass | special | 50 | 100 | 20 | `EFFECT_LEECH_HIT` | 0 | no |
| 49 | LEECH SEED | `LEECH_SEED` | Grass | status | 0 | 90 | 20 | `EFFECT_LEECH_SEED` | 0 | no |
| 4A | GROWTH | `GROWTH` | Normal | status | 0 | 100 | 40 | `EFFECT_SP_ATK_UP` | 0 | no |
| 4B | RAZOR LEAF | `RAZOR_LEAF` | Grass | special | 70 | 100 | 25 | `EFFECT_NORMAL_HIT` | 0 | no |
| 4C | SOLARBEAM | `SOLARBEAM` | Grass | special | 180 | 100 | 10 | `EFFECT_SOLARBEAM` | 0 | no |
| 4D | POISONPOWDER | `POISONPOWDER` | Poison | status | 0 | 75 | 35 | `EFFECT_POISON` | 0 | no |
| 4E | STUN SPORE | `STUN_SPORE` | Grass | status | 0 | 75 | 30 | `EFFECT_PARALYZE` | 0 | no |
| 4F | SLEEP POWDER | `SLEEP_POWDER` | Grass | status | 0 | 75 | 15 | `EFFECT_SLEEP` | 0 | no |
| 50 | PETAL DANCE | `PETAL_DANCE` | Grass | special | 120 | 100 | 10 | `EFFECT_RAMPAGE` | 0 | yes |
| 51 | STRING SHOT | `STRING_SHOT` | Bug | status | 0 | 95 | 40 | `EFFECT_SPEED_DOWN` | 0 | no |
| 52 | DRAGON RAGE | `DRAGON_RAGE` | Dragon | fixed | 40 | 100 | 10 | `EFFECT_STATIC_DAMAGE` | 0 | no |
| 53 | FIRE SPIN | `FIRE_SPIN` | Fire | special | 25 | 85 | 10 | `EFFECT_TRAP_TARGET` | 0 | no |
| 54 | THUNDERSHOCK | `THUNDERSHOCK` | Electric | special | 40 | 100 | 30 | `EFFECT_PARALYZE_HIT` | 10 | no |
| 55 | THUNDERBOLT | `THUNDERBOLT` | Electric | special | 95 | 100 | 15 | `EFFECT_PARALYZE_HIT` | 10 | no |
| 56 | THUNDER WAVE | `THUNDER_WAVE` | Electric | status | 0 | 100 | 20 | `EFFECT_PARALYZE` | 0 | no |
| 57 | THUNDER | `THUNDER` | Electric | special | 120 | 70 | 10 | `EFFECT_THUNDER` | 30 | no |
| 58 | ROCK THROW | `ROCK_THROW` | Rock | physical | 50 | 90 | 15 | `EFFECT_NORMAL_HIT` | 0 | no |
| 59 | EARTHQUAKE | `EARTHQUAKE` | Ground | physical | 100 | 100 | 10 | `EFFECT_EARTHQUAKE` | 0 | no |
| 5A | FISSURE | `FISSURE` | Ground | fixed | 1 | 30 | 5 | `EFFECT_OHKO` | 0 | no |
| 5B | DIG | `DIG` | Ground | physical | 60 | 100 | 10 | `EFFECT_FLY` | 0 | yes |
| 5C | TOXIC | `TOXIC` | Poison | status | 0 | 85 | 10 | `EFFECT_TOXIC` | 0 | no |
| 5D | CONFUSION | `CONFUSION` | Psychic | special | 50 | 100 | 25 | `EFFECT_CONFUSE_HIT` | 10 | no |
| 5E | PSYCHIC | `PSYCHIC_M` | Psychic | special | 90 | 100 | 10 | `EFFECT_SP_DEF_DOWN_HIT` | 10 | no |
| 5F | HYPNOSIS | `HYPNOSIS` | Psychic | status | 0 | 60 | 20 | `EFFECT_SLEEP` | 0 | no |
| 60 | MEDITATE | `MEDITATE` | Psychic | status | 0 | 100 | 40 | `EFFECT_ATTACK_UP` | 0 | no |
| 61 | AGILITY | `AGILITY` | Psychic | status | 0 | 100 | 30 | `EFFECT_SPEED_UP_2` | 0 | no |
| 62 | QUICK ATTACK | `QUICK_ATTACK` | Normal | physical | 40 | 100 | 30 | `EFFECT_PRIORITY_HIT` | 0 | yes |
| 63 | RAGE | `RAGE` | Normal | physical | 20 | 100 | 20 | `EFFECT_RAGE` | 0 | yes |
| 64 | TELEPORT | `TELEPORT` | Psychic | status | 0 | 100 | 20 | `EFFECT_TELEPORT` | 0 | no |
| 65 | NIGHT SHADE | `NIGHT_SHADE` | Ghost | fixed | 1 | 100 | 15 | `EFFECT_LEVEL_DAMAGE` | 0 | no |
| 66 | MIMIC | `MIMIC` | Normal | status | 0 | 100 | 10 | `EFFECT_MIMIC` | 0 | no |
| 67 | SCREECH | `SCREECH` | Normal | status | 0 | 85 | 40 | `EFFECT_DEFENSE_DOWN_2` | 0 | no |
| 68 | DOUBLE TEAM | `DOUBLE_TEAM` | Normal | status | 0 | 100 | 15 | `EFFECT_EVASION_UP` | 0 | no |
| 69 | RECOVER | `RECOVER` | Normal | status | 0 | 100 | 20 | `EFFECT_HEAL` | 0 | no |
| 6A | HARDEN | `HARDEN` | Normal | status | 0 | 100 | 30 | `EFFECT_DEFENSE_UP` | 0 | no |
| 6B | MINIMIZE | `MINIMIZE` | Normal | status | 0 | 100 | 20 | `EFFECT_EVASION_UP` | 0 | no |
| 6C | SMOKESCREEN | `SMOKESCREEN` | Normal | status | 0 | 100 | 20 | `EFFECT_ACCURACY_DOWN` | 0 | no |
| 6D | CONFUSE RAY | `CONFUSE_RAY` | Ghost | status | 0 | 100 | 10 | `EFFECT_CONFUSE` | 0 | no |
| 6E | WITHDRAW | `WITHDRAW` | Water | status | 0 | 100 | 40 | `EFFECT_DEFENSE_UP` | 0 | no |
| 6F | DEFENSE CURL | `DEFENSE_CURL` | Normal | status | 0 | 100 | 40 | `EFFECT_DEFENSE_CURL` | 0 | no |
| 70 | BARRIER | `BARRIER` | Psychic | status | 0 | 100 | 30 | `EFFECT_DEFENSE_UP_2` | 0 | no |
| 71 | LIGHT SCREEN | `LIGHT_SCREEN` | Psychic | status | 0 | 100 | 30 | `EFFECT_LIGHT_SCREEN` | 0 | no |
| 72 | HAZE | `HAZE` | Ice | status | 0 | 100 | 30 | `EFFECT_RESET_STATS` | 0 | no |
| 73 | REFLECT | `REFLECT` | Psychic | status | 0 | 100 | 20 | `EFFECT_REFLECT` | 0 | no |
| 74 | FOCUS ENERGY | `FOCUS_ENERGY` | Normal | status | 0 | 100 | 30 | `EFFECT_FOCUS_ENERGY` | 0 | no |
| 75 | BIDE | `BIDE` | Normal | status | 0 | 100 | 10 | `EFFECT_BIDE` | 0 | yes |
| 76 | METRONOME | `METRONOME` | Normal | status | 0 | 100 | 10 | `EFFECT_METRONOME` | 0 | no |
| 77 | MIRROR MOVE | `MIRROR_MOVE` | Flying | status | 0 | 100 | 20 | `EFFECT_MIRROR_MOVE` | 0 | no |
| 78 | SELFDESTRUCT | `SELFDESTRUCT` | Normal | physical | 200 | 100 | 5 | `EFFECT_SELFDESTRUCT` | 0 | no |
| 79 | EGG BOMB | `EGG_BOMB` | Normal | physical | 100 | 75 | 10 | `EFFECT_NORMAL_HIT` | 0 | no |
| 7A | LICK | `LICK` | Ghost | physical | 50 | 100 | 30 | `EFFECT_PARALYZE_HIT` | 30 | yes |
| 7B | SMOG | `SMOG` | Poison | physical | 20 | 70 | 20 | `EFFECT_POISON_HIT` | 40 | no |
| 7C | SLUDGE | `SLUDGE` | Poison | physical | 65 | 100 | 25 | `EFFECT_POISON_HIT` | 30 | no |
| 7D | BONE CLUB | `BONE_CLUB` | Ground | physical | 65 | 85 | 20 | `EFFECT_FLINCH_HIT` | 10 | no |
| 7E | FIRE BLAST | `FIRE_BLAST` | Fire | special | 140 | 85 | 10 | `EFFECT_BURN_HIT` | 10 | no |
| 7F | WATERFALL | `WATERFALL` | Water | special | 80 | 100 | 15 | `EFFECT_NORMAL_HIT` | 0 | yes |
| 80 | CLAMP | `CLAMP` | Water | special | 35 | 75 | 10 | `EFFECT_TRAP_TARGET` | 0 | yes |
| 81 | SWIFT | `SWIFT` | Normal | physical | 60 | 100 | 20 | `EFFECT_ALWAYS_HIT` | 0 | no |
| 82 | SKULL BASH | `SKULL_BASH` | Normal | physical | 100 | 100 | 15 | `EFFECT_SKULL_BASH` | 0 | yes |
| 83 | SPIKE CANNON | `SPIKE_CANNON` | Normal | physical | 25 | 100 | 15 | `EFFECT_MULTI_HIT` | 0 | no |
| 84 | CONSTRICT | `CONSTRICT` | Normal | physical | 10 | 100 | 35 | `EFFECT_SPEED_DOWN_HIT` | 10 | yes |
| 85 | AMNESIA | `AMNESIA` | Psychic | status | 0 | 100 | 20 | `EFFECT_SP_DEF_UP_2` | 0 | no |
| 86 | FOCUS PUNCH | `FOCUS_PUNCH` | Fighting | physical | 150 | 100 | 20 | `EFFECT_FOCUS_PUNCH` | 0 | yes |
| 87 | SOFTBOILED | `SOFTBOILED` | Normal | status | 0 | 100 | 10 | `EFFECT_HEAL` | 0 | no |
| 88 | HI JUMP KICK | `HI_JUMP_KICK` | Fighting | physical | 130 | 90 | 20 | `EFFECT_JUMP_KICK` | 0 | yes |
| 89 | GLARE | `GLARE` | Normal | status | 0 | 75 | 30 | `EFFECT_PARALYZE` | 0 | no |
| 8A | DREAM EATER | `DREAM_EATER` | Psychic | special | 100 | 100 | 15 | `EFFECT_DREAM_EATER` | 0 | no |
| 8B | POISON GAS | `POISON_GAS` | Poison | status | 0 | 55 | 40 | `EFFECT_POISON` | 0 | no |
| 8C | BARRAGE | `BARRAGE` | Normal | physical | 25 | 100 | 20 | `EFFECT_MULTI_HIT` | 0 | no |
| 8D | LEECH LIFE | `LEECH_LIFE` | Bug | physical | 80 | 100 | 20 | `EFFECT_LEECH_HIT` | 0 | yes |
| 8E | LOVELY KISS | `LOVELY_KISS` | Normal | status | 0 | 75 | 10 | `EFFECT_SLEEP` | 0 | no |
| 8F | SKY ATTACK | `SKY_ATTACK` | Flying | physical | 140 | 90 | 5 | `EFFECT_SKY_ATTACK` | 0 | no |
| 90 | TRANSFORM | `TRANSFORM` | Normal | status | 0 | 100 | 10 | `EFFECT_TRANSFORM` | 0 | no |
| 91 | BUBBLE | `BUBBLE` | Water | special | 20 | 100 | 30 | `EFFECT_SPEED_DOWN_HIT` | 10 | no |
| 92 | DIZZY PUNCH | `DIZZY_PUNCH` | Normal | physical | 95 | 100 | 20 | `EFFECT_CONFUSE_HIT` | 20 | yes |
| 93 | SPORE | `SPORE` | Grass | status | 0 | 100 | 15 | `EFFECT_SLEEP` | 0 | no |
| 94 | FLASH | `FLASH` | Normal | status | 0 | 70 | 20 | `EFFECT_ACCURACY_DOWN` | 0 | no |
| 95 | PSYWAVE | `PSYWAVE` | Psychic | fixed | 1 | 80 | 15 | `EFFECT_PSYWAVE` | 0 | no |
| 96 | SPLASH | `SPLASH` | Normal | status | 0 | 100 | 40 | `EFFECT_SPLASH` | 0 | no |
| 97 | ACID ARMOR | `ACID_ARMOR` | Poison | status | 0 | 100 | 40 | `EFFECT_DEFENSE_UP_2` | 0 | no |
| 98 | CRABHAMMER | `CRABHAMMER` | Water | special | 90 | 85 | 10 | `EFFECT_NORMAL_HIT` | 0 | yes |
| 99 | EXPLOSION | `EXPLOSION` | Normal | physical | 250 | 100 | 5 | `EFFECT_SELFDESTRUCT` | 0 | no |
| 9A | FURY SWIPES | `FURY_SWIPES` | Normal | physical | 25 | 100 | 15 | `EFFECT_MULTI_HIT` | 0 | yes |
| 9B | BONEMERANG | `BONEMERANG` | Ground | physical | 50 | 100 | 10 | `EFFECT_DOUBLE_HIT` | 0 | no |
| 9C | REST | `REST` | Psychic | status | 0 | 100 | 10 | `EFFECT_HEAL` | 0 | no |
| 9D | ROCK SLIDE | `ROCK_SLIDE` | Rock | physical | 75 | 90 | 10 | `EFFECT_FLINCH_HIT` | 30 | no |
| 9E | HYPER FANG | `HYPER_FANG` | Normal | physical | 80 | 90 | 15 | `EFFECT_FLINCH_HIT` | 10 | yes |
| 9F | SHARPEN | `SHARPEN` | Normal | status | 0 | 100 | 30 | `EFFECT_ATTACK_UP` | 0 | no |
| A0 | CONVERSION | `CONVERSION` | Normal | status | 0 | 100 | 30 | `EFFECT_CONVERSION` | 0 | no |
| A1 | TRI ATTACK | `TRI_ATTACK` | Normal | physical | 80 | 100 | 10 | `EFFECT_TRI_ATTACK` | 20 | no |
| A2 | SUPER FANG | `SUPER_FANG` | Normal | fixed | 1 | 90 | 10 | `EFFECT_SUPER_FANG` | 0 | yes |
| A3 | SLASH | `SLASH` | Normal | physical | 70 | 100 | 20 | `EFFECT_NORMAL_HIT` | 0 | yes |
| A4 | SUBSTITUTE | `SUBSTITUTE` | Normal | status | 0 | 100 | 10 | `EFFECT_SUBSTITUTE` | 0 | no |
| A5 | STRUGGLE | `STRUGGLE` | Normal | physical | 50 | 100 | 1 | `EFFECT_RECOIL_HIT` | 0 | yes |
| A6 | SKETCH | `SKETCH` | Normal | status | 0 | 100 | 1 | `EFFECT_SKETCH` | 0 | no |
| A7 | TRIPLE KICK | `TRIPLE_KICK` | Fighting | physical | 10 | 100 | 10 | `EFFECT_TRIPLE_KICK` | 0 | yes |
| A8 | THIEF | `THIEF` | Dark | special | 40 | 100 | 10 | `EFFECT_THIEF` | 100 | yes |
| A9 | SPIDER WEB | `SPIDER_WEB` | Bug | status | 0 | 100 | 10 | `EFFECT_MEAN_LOOK` | 0 | no |
| AA | MIND READER | `MIND_READER` | Normal | status | 0 | 100 | 5 | `EFFECT_LOCK_ON` | 0 | no |
| AB | NIGHTMARE | `NIGHTMARE` | Ghost | status | 0 | 100 | 15 | `EFFECT_NIGHTMARE` | 0 | no |
| AC | FLAME WHEEL | `FLAME_WHEEL` | Fire | special | 60 | 100 | 25 | `EFFECT_FLAME_WHEEL` | 10 | yes |
| AD | SNORE | `SNORE` | Normal | physical | 40 | 100 | 15 | `EFFECT_SNORE` | 30 | no |
| AE | CURSE | `CURSE` | Curse | status | 0 | 100 | 10 | `EFFECT_CURSE` | 0 | no |
| AF | FLAIL | `FLAIL` | Normal | physical | 1 | 100 | 15 | `EFFECT_REVERSAL` | 0 | yes |
| B0 | CONVERSION2 | `CONVERSION2` | Normal | status | 0 | 100 | 30 | `EFFECT_CONVERSION2` | 0 | no |
| B1 | AEROBLAST | `AEROBLAST` | Flying | physical | 100 | 95 | 5 | `EFFECT_NORMAL_HIT` | 0 | no |
| B2 | COTTON SPORE | `COTTON_SPORE` | Grass | status | 0 | 85 | 40 | `EFFECT_SPEED_DOWN_2` | 0 | no |
| B3 | REVERSAL | `REVERSAL` | Fighting | physical | 1 | 100 | 15 | `EFFECT_REVERSAL` | 0 | yes |
| B4 | SPITE | `SPITE` | Ghost | status | 0 | 100 | 10 | `EFFECT_SPITE` | 0 | no |
| B5 | POWDER SNOW | `POWDER_SNOW` | Ice | special | 40 | 100 | 25 | `EFFECT_FREEZE_HIT` | 10 | no |
| B6 | PROTECT | `PROTECT` | Normal | status | 0 | 100 | 10 | `EFFECT_PROTECT` | 0 | no |
| B7 | MACH PUNCH | `MACH_PUNCH` | Fighting | physical | 40 | 100 | 30 | `EFFECT_PRIORITY_HIT` | 0 | yes |
| B8 | SCARY FACE | `SCARY_FACE` | Normal | status | 0 | 90 | 10 | `EFFECT_SPEED_DOWN_2` | 0 | no |
| B9 | FAINT ATTACK | `FAINT_ATTACK` | Dark | special | 60 | 100 | 20 | `EFFECT_ALWAYS_HIT` | 0 | yes |
| BA | SWEET KISS | `SWEET_KISS` | Normal | status | 0 | 75 | 10 | `EFFECT_CONFUSE` | 0 | no |
| BB | BELLY DRUM | `BELLY_DRUM` | Normal | status | 0 | 100 | 10 | `EFFECT_BELLY_DRUM` | 0 | no |
| BC | SLUDGE BOMB | `SLUDGE_BOMB` | Poison | physical | 90 | 100 | 15 | `EFFECT_POISON_HIT` | 30 | no |
| BD | MUD-SLAP | `MUD_SLAP` | Ground | physical | 30 | 100 | 10 | `EFFECT_ACCURACY_DOWN_HIT` | 100 | no |
| BE | OCTAZOOKA | `OCTAZOOKA` | Water | special | 100 | 90 | 20 | `EFFECT_ACCURACY_DOWN_HIT` | 50 | no |
| BF | SPIKES | `SPIKES` | Ground | status | 0 | 100 | 20 | `EFFECT_SPIKES` | 0 | no |
| C0 | ZAP CANNON | `ZAP_CANNON` | Electric | special | 100 | 50 | 5 | `EFFECT_PARALYZE_HIT` | 100 | no |
| C1 | FORESIGHT | `FORESIGHT` | Normal | status | 0 | 100 | 40 | `EFFECT_FORESIGHT` | 0 | no |
| C2 | DESTINY BOND | `DESTINY_BOND` | Ghost | status | 0 | 100 | 5 | `EFFECT_DESTINY_BOND` | 0 | no |
| C3 | PERISH SONG | `PERISH_SONG` | Normal | status | 0 | 100 | 5 | `EFFECT_PERISH_SONG` | 0 | no |
| C4 | ICY WIND | `ICY_WIND` | Ice | special | 55 | 95 | 15 | `EFFECT_SPEED_DOWN_HIT` | 100 | no |
| C5 | DETECT | `DETECT` | Fighting | status | 0 | 100 | 5 | `EFFECT_PROTECT` | 0 | no |
| C6 | BONE RUSH | `BONE_RUSH` | Ground | physical | 25 | 100 | 10 | `EFFECT_MULTI_HIT` | 0 | no |
| C7 | LOCK-ON | `LOCK_ON` | Normal | status | 0 | 100 | 5 | `EFFECT_LOCK_ON` | 0 | no |
| C8 | OUTRAGE | `OUTRAGE` | Dragon | special* | 100 | 100 | 15 | `EFFECT_RAMPAGE` | 0 | yes |
| C9 | SANDSTORM | `SANDSTORM` | Rock | status | 0 | 100 | 10 | `EFFECT_SANDSTORM` | 0 | no |
| CA | GIGA DRAIN | `GIGA_DRAIN` | Grass | special | 75 | 100 | 25 | `EFFECT_LEECH_HIT` | 0 | no |
| CB | ENDURE | `ENDURE` | Normal | status | 0 | 100 | 10 | `EFFECT_ENDURE` | 0 | no |
| CC | CHARM | `CHARM` | Normal | status | 0 | 100 | 20 | `EFFECT_ATTACK_DOWN_2` | 0 | no |
| CD | ROLLOUT | `ROLLOUT` | Rock | physical | 30 | 90 | 20 | `EFFECT_ROLLOUT` | 0 | yes |
| CE | FALSE SWIPE | `FALSE_SWIPE` | Normal | physical | 40 | 100 | 40 | `EFFECT_FALSE_SWIPE` | 0 | yes |
| CF | SWAGGER | `SWAGGER` | Normal | status | 0 | 90 | 15 | `EFFECT_SWAGGER` | 100 | no |
| D0 | MILK DRINK | `MILK_DRINK` | Normal | status | 0 | 100 | 10 | `EFFECT_HEAL` | 0 | no |
| D1 | SPARK | `SPARK` | Electric | special | 65 | 100 | 20 | `EFFECT_PARALYZE_HIT` | 30 | yes |
| D2 | FURY CUTTER | `FURY_CUTTER` | Bug | physical | 10 | 95 | 20 | `EFFECT_FURY_CUTTER` | 0 | yes |
| D3 | STEEL WING | `STEEL_WING` | Steel | physical | 70 | 90 | 25 | `EFFECT_DEFENSE_UP_HIT` | 10 | yes |
| D4 | MEAN LOOK | `MEAN_LOOK` | Normal | status | 0 | 100 | 5 | `EFFECT_MEAN_LOOK` | 0 | no |
| D5 | ATTRACT | `ATTRACT` | Normal | status | 0 | 100 | 15 | `EFFECT_ATTRACT` | 0 | no |
| D6 | SLEEP TALK | `SLEEP_TALK` | Normal | status | 0 | 100 | 10 | `EFFECT_SLEEP_TALK` | 0 | no |
| D7 | HEAL BELL | `HEAL_BELL` | Normal | status | 0 | 100 | 5 | `EFFECT_HEAL_BELL` | 0 | no |
| D8 | RETURN | `RETURN` | Normal | physical | 1 | 100 | 20 | `EFFECT_RETURN` | 0 | yes |
| D9 | PRESENT | `PRESENT` | Normal | fixed | 1 | 90 | 15 | `EFFECT_PRESENT` | 0 | no |
| DA | FRUSTRATION | `FRUSTRATION` | Normal | physical | 1 | 100 | 20 | `EFFECT_FRUSTRATION` | 0 | yes |
| DB | SAFEGUARD | `SAFEGUARD` | Normal | status | 0 | 100 | 25 | `EFFECT_SAFEGUARD` | 0 | no |
| DC | PAIN SPLIT | `PAIN_SPLIT` | Normal | status | 0 | 100 | 20 | `EFFECT_PAIN_SPLIT` | 0 | no |
| DD | SACRED FIRE | `SACRED_FIRE` | Fire | special | 100 | 95 | 5 | `EFFECT_SACRED_FIRE` | 50 | no |
| DE | MAGNITUDE | `MAGNITUDE` | Ground | physical | 1 | 100 | 30 | `EFFECT_MAGNITUDE` | 0 | no |
| DF | DYNAMICPUNCH | `DYNAMICPUNCH` | Fighting | physical | 100 | 50 | 5 | `EFFECT_CONFUSE_HIT` | 100 | yes |
| E0 | MEGAHORN | `MEGAHORN` | Bug | physical | 120 | 85 | 10 | `EFFECT_NORMAL_HIT` | 0 | yes |
| E1 | DRAGONBREATH | `DRAGONBREATH` | Dragon | special | 60 | 100 | 20 | `EFFECT_PARALYZE_HIT` | 30 | no |
| E2 | BATON PASS | `BATON_PASS` | Normal | status | 0 | 100 | 40 | `EFFECT_BATON_PASS` | 0 | no |
| E3 | ENCORE | `ENCORE` | Normal | status | 0 | 100 | 5 | `EFFECT_ENCORE` | 0 | no |
| E4 | PURSUIT | `PURSUIT` | Dark | special | 40 | 100 | 20 | `EFFECT_PURSUIT` | 0 | yes |
| E5 | RAPID SPIN | `RAPID_SPIN` | Normal | physical | 50 | 100 | 40 | `EFFECT_RAPID_SPIN` | 0 | yes |
| E6 | SWEET SCENT | `SWEET_SCENT` | Normal | status | 0 | 100 | 20 | `EFFECT_EVASION_DOWN` | 0 | no |
| E7 | IRON TAIL | `IRON_TAIL` | Steel | physical | 130 | 75 | 15 | `EFFECT_DEFENSE_DOWN_HIT` | 30 | yes |
| E8 | METAL CLAW | `METAL_CLAW` | Steel | physical | 50 | 95 | 35 | `EFFECT_ATTACK_UP_HIT` | 10 | yes |
| E9 | VITAL THROW | `VITAL_THROW` | Fighting | physical | 70 | 100 | 10 | `EFFECT_ALWAYS_HIT` | 0 | yes |
| EA | MORNING SUN | `MORNING_SUN` | Normal | status | 0 | 100 | 5 | `EFFECT_MORNING_SUN` | 0 | no |
| EB | SYNTHESIS | `SYNTHESIS` | Grass | status | 0 | 100 | 5 | `EFFECT_SYNTHESIS` | 0 | no |
| EC | MOONLIGHT | `MOONLIGHT` | Normal | status | 0 | 100 | 5 | `EFFECT_MOONLIGHT` | 0 | no |
| ED | HIDDEN POWER | `HIDDEN_POWER` | Normal | physical | 1 | 100 | 15 | `EFFECT_HIDDEN_POWER` | 0 | no |
| EE | CROSS CHOP | `CROSS_CHOP` | Fighting | physical | 120 | 80 | 20 | `EFFECT_NORMAL_HIT` | 0 | yes |
| EF | TWISTER | `TWISTER` | Dragon | special | 40 | 100 | 20 | `EFFECT_TWISTER` | 20 | no |
| F0 | RAIN DANCE | `RAIN_DANCE` | Water | status | 0 | 100 | 5 | `EFFECT_RAIN_DANCE` | 0 | no |
| F1 | SUNNY DAY | `SUNNY_DAY` | Fire | status | 0 | 100 | 5 | `EFFECT_SUNNY_DAY` | 0 | no |
| F2 | CRUNCH | `CRUNCH` | Dark | special | 90 | 100 | 15 | `EFFECT_SP_DEF_DOWN_HIT` | 20 | yes |
| F3 | MIRROR COAT | `MIRROR_COAT` | Psychic | fixed | 1 | 100 | 20 | `EFFECT_MIRROR_COAT` | 0 | no |
| F4 | PSYCH UP | `PSYCH_UP` | Normal | status | 0 | 100 | 10 | `EFFECT_PSYCH_UP` | 0 | no |
| F5 | EXTREMESPEED | `EXTREMESPEED` | Normal | physical | 80 | 100 | 5 | `EFFECT_PRIORITY_HIT` | 0 | yes |
| F6 | ANCIENTPOWER | `ANCIENTPOWER` | Rock | physical | 60 | 100 | 5 | `EFFECT_ALL_UP_HIT` | 10 | no |
| F7 | SHADOW BALL | `SHADOW_BALL` | Ghost | physical | 80 | 100 | 15 | `EFFECT_SP_DEF_DOWN_HIT` | 20 | no |
| F8 | FUTURE SIGHT | `FUTURE_SIGHT` | Psychic | special | 120 | 90 | 15 | `EFFECT_FUTURE_SIGHT` | 0 | no |
| F9 | ROCK SMASH | `ROCK_SMASH` | Fighting | physical | 20 | 100 | 15 | `EFFECT_DEFENSE_DOWN_HIT` | 50 | yes |
| FA | WHIRLPOOL | `WHIRLPOOL` | Water | special | 15 | 70 | 15 | `EFFECT_TRAP_TARGET` | 0 | no |
| FB | BEAT UP | `BEAT_UP` | Dark | special | 10 | 100 | 10 | `EFFECT_BEAT_UP` | 0 | no |
| FC | DRAGON DANCE | `DRAGON_DANCE` | Dragon | status | 0 | 100 | 20 | `EFFECT_DRAGON_DANCE` | 0 | no |
| FD | CALM MIND | `CALM_MIND` | Psychic | status | 0 | 100 | 20 | `EFFECT_CALM_MIND` | 0 | no |
| FE | QUIVER DANCE | `QUIVER_DANCE` | Bug | status | 0 | 100 | 20 | `EFFECT_QUIVER_DANCE` | 0 | no |

## Held Items And Item Attributes

This table is the item attribute table, not a full prose description of every
engine effect. For behavior, check `engine/battle/late_gen_held_items.asm`,
`engine/items/item_effects.asm`, and `engine/battle/effect_commands.asm`.

| ID | Item | Const/Slot | Held Effect | Param | Pocket | Field | Battle |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | MASTER BALL | `MASTER_BALL` | `HELD_NONE` | 0 | `BALL` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| 02 | ULTRA BALL | `ULTRA_BALL` | `HELD_NONE` | 0 | `BALL` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| 03 | BRIGHTPOWDER | `BRIGHTPOWDER` | `HELD_BRIGHTPOWDER` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 04 | GREAT BALL | `GREAT_BALL` | `HELD_NONE` | 0 | `BALL` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| 05 | # BALL | `POKE_BALL` | `HELD_NONE` | 0 | `BALL` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| 06 | TERU-SAMA | `TOWN_MAP` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 07 | BICYCLE | `BICYCLE` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_CLOSE` | `ITEMMENU_NOUSE` |
| 08 | MOON STONE | `MOON_STONE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| 09 | ANTIDOTE | `ANTIDOTE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 0A | BURN HEAL | `BURN_HEAL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 0B | ICE HEAL | `ICE_HEAL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 0C | AWAKENING | `AWAKENING` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 0D | PARLYZ HEAL | `PARLYZ_HEAL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 0E | FULL RESTORE | `FULL_RESTORE` | `HELD_NONE` | -1 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 0F | MAX POTION | `MAX_POTION` | `HELD_NONE` | -1 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 10 | HYPER POTION | `HYPER_POTION` | `HELD_NONE` | 200 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 11 | SUPER POTION | `SUPER_POTION` | `HELD_NONE` | 50 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 12 | POTION | `POTION` | `HELD_NONE` | 20 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 13 | ESCAPE ROPE | `ESCAPE_ROPE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_CLOSE` | `ITEMMENU_NOUSE` |
| 14 | REPEL | `REPEL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_CURRENT` | `ITEMMENU_NOUSE` |
| 15 | MAX ELIXER | `MAX_ELIXER` | `HELD_NONE` | -1 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 16 | FIRE STONE | `FIRE_STONE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| 17 | THUNDERSTONE | `THUNDERSTONE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| 18 | WATER STONE | `WATER_STONE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| 19 | TERU-SAMA | `ITEM_19` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 1A | HP UP | `HP_UP` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| 1B | PROTEIN | `PROTEIN` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| 1C | IRON | `IRON` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| 1D | CARBOS | `CARBOS` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| 1E | LUCKY PUNCH | `LUCKY_PUNCH` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 1F | CALCIUM | `CALCIUM` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| 20 | RARE CANDY | `RARE_CANDY` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| 21 | X ACCURACY | `X_ACCURACY` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| 22 | LEAF STONE | `LEAF_STONE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| 23 | METAL POWDER | `METAL_POWDER` | `HELD_METAL_POWDER` | 10 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 24 | NUGGET | `NUGGET` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 25 | # DOLL | `POKE_DOLL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| 26 | FULL HEAL | `FULL_HEAL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 27 | REVIVE | `REVIVE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 28 | MAX REVIVE | `MAX_REVIVE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 29 | GUARD SPEC. | `GUARD_SPEC` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| 2A | SUPER REPEL | `SUPER_REPEL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_CURRENT` | `ITEMMENU_NOUSE` |
| 2B | MAX REPEL | `MAX_REPEL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_CURRENT` | `ITEMMENU_NOUSE` |
| 2C | DIRE HIT | `DIRE_HIT` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| 2D | TERU-SAMA | `ITEM_2D` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 2E | FRESH WATER | `FRESH_WATER` | `HELD_NONE` | 50 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 2F | SODA POP | `SODA_POP` | `HELD_NONE` | 60 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 30 | LEMONADE | `LEMONADE` | `HELD_NONE` | 80 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 31 | X ATTACK | `X_ATTACK` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| 32 | TERU-SAMA | `ITEM_32` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 33 | X DEFEND | `X_DEFEND` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| 34 | X SPEED | `X_SPEED` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| 35 | X SPECIAL | `X_SPECIAL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| 36 | COIN CASE | `COIN_CASE` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_CURRENT` | `ITEMMENU_NOUSE` |
| 37 | ITEMFINDER | `ITEMFINDER` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_CLOSE` | `ITEMMENU_NOUSE` |
| 38 | TERU-SAMA | `POKE_FLUTE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 39 | EXP.SHARE | `EXP_SHARE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 3A | OLD ROD | `OLD_ROD` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_CLOSE` | `ITEMMENU_NOUSE` |
| 3B | GOOD ROD | `GOOD_ROD` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_CLOSE` | `ITEMMENU_NOUSE` |
| 3C | SILVER LEAF | `SILVER_LEAF` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 3D | SUPER ROD | `SUPER_ROD` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_CLOSE` | `ITEMMENU_NOUSE` |
| 3E | PP UP | `PP_UP` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| 3F | ETHER | `ETHER` | `HELD_NONE` | 10 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 40 | MAX ETHER | `MAX_ETHER` | `HELD_NONE` | -1 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 41 | ELIXER | `ELIXER` | `HELD_NONE` | 10 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 42 | RED SCALE | `RED_SCALE` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 43 | SECRETPOTION | `SECRETPOTION` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 44 | S.S.TICKET | `S_S_TICKET` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 45 | MYSTERY EGG | `MYSTERY_EGG` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 46 | LIFE ORB | `LIFE_ORB` | `HELD_LIFE_ORB` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 47 | SILVER WING | `SILVER_WING` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 48 | MOOMOO MILK | `MOOMOO_MILK` | `HELD_NONE` | 100 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 49 | QUICK CLAW | `QUICK_CLAW` | `HELD_QUICK_CLAW` | 60 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 4A | PSNCUREBERRY | `PSNCUREBERRY` | `HELD_HEAL_POISON` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 4B | GOLD LEAF | `GOLD_LEAF` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 4C | SOFT SAND | `SOFT_SAND` | `HELD_GROUND_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 4D | SHARP BEAK | `SHARP_BEAK` | `HELD_FLYING_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 4E | PRZCUREBERRY | `PRZCUREBERRY` | `HELD_HEAL_PARALYZE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 4F | BURNT BERRY | `BURNT_BERRY` | `HELD_HEAL_FREEZE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 50 | ICE BERRY | `ICE_BERRY` | `HELD_HEAL_BURN` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 51 | POISON BARB | `POISON_BARB` | `HELD_POISON_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 52 | KING'S ROCK | `KINGS_ROCK` | `HELD_FLINCH` | 30 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 53 | BITTER BERRY | `BITTER_BERRY` | `HELD_HEAL_CONFUSION` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_PARTY` |
| 54 | MINT BERRY | `MINT_BERRY` | `HELD_HEAL_SLEEP` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 55 | RED APRICORN | `RED_APRICORN` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 56 | TINYMUSHROOM | `TINYMUSHROOM` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 57 | BIG MUSHROOM | `BIG_MUSHROOM` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 58 | SILVERPOWDER | `SILVERPOWDER` | `HELD_BUG_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 59 | BLU APRICORN | `BLU_APRICORN` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 5A | TERU-SAMA | `ITEM_5A` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 5B | AMULET COIN | `AMULET_COIN` | `HELD_AMULET_COIN` | 10 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 5C | YLW APRICORN | `YLW_APRICORN` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 5D | GRN APRICORN | `GRN_APRICORN` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 5E | CLEANSE TAG | `CLEANSE_TAG` | `HELD_CLEANSE_TAG` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 5F | MYSTIC WATER | `MYSTIC_WATER` | `HELD_WATER_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 60 | TWISTEDSPOON | `TWISTEDSPOON` | `HELD_PSYCHIC_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 61 | WHT APRICORN | `WHT_APRICORN` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 62 | BLACKBELT | `BLACKBELT_I` | `HELD_FIGHTING_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 63 | BLK APRICORN | `BLK_APRICORN` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 64 | TERU-SAMA | `ITEM_64` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 65 | PNK APRICORN | `PNK_APRICORN` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 66 | BLACKGLASSES | `BLACKGLASSES` | `HELD_DARK_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 67 | SLOWPOKETAIL | `SLOWPOKETAIL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 68 | PINK BOW | `PINK_BOW` | `HELD_NORMAL_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 69 | STICK | `STICK` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 6A | SMOKE BALL | `SMOKE_BALL` | `HELD_ESCAPE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 6B | NEVERMELTICE | `NEVERMELTICE` | `HELD_ICE_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 6C | MAGNET | `MAGNET` | `HELD_ELECTRIC_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 6D | MIRACLEBERRY | `MIRACLEBERRY` | `HELD_HEAL_STATUS` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 6E | PEARL | `PEARL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 6F | BIG PEARL | `BIG_PEARL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 70 | EVERSTONE | `EVERSTONE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 71 | SPELL TAG | `SPELL_TAG` | `HELD_GHOST_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 72 | RAGECANDYBAR | `RAGECANDYBAR` | `HELD_NONE` | 20 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 73 | ? | `ITEM_73` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 74 | CHOICE BAND | `CHOICE_BAND` | `HELD_CHOICE_BAND` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 75 | MIRACLE SEED | `MIRACLE_SEED` | `HELD_GRASS_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 76 | THICK CLUB | `THICK_CLUB` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 77 | FOCUS BAND | `FOCUS_BAND` | `HELD_FOCUS_BAND` | 30 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 78 | PRUNERS | `PRUNERS` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_CLOSE` | `ITEMMENU_NOUSE` |
| 79 | ENERGYPOWDER | `ENERGYPOWDER` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 7A | ENERGY ROOT | `ENERGY_ROOT` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 7B | HEAL POWDER | `HEAL_POWDER` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 7C | REVIVAL HERB | `REVIVAL_HERB` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 7D | HARD STONE | `HARD_STONE` | `HELD_ROCK_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 7E | LUCKY EGG | `LUCKY_EGG` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 7F | CARD KEY | `CARD_KEY` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_CLOSE` | `ITEMMENU_NOUSE` |
| 80 | MACHINE PART | `MACHINE_PART` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 81 | CHOICE SPECS | `CHOICE_SPECS` | `HELD_CHOICE_SPECS` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 82 | LOST ITEM | `LOST_ITEM` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 83 | STARDUST | `STARDUST` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 84 | STAR PIECE | `STAR_PIECE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 85 | BASEMENT KEY | `BASEMENT_KEY` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_CLOSE` | `ITEMMENU_NOUSE` |
| 86 | PASS | `PASS` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 87 | SURFBOARD | `SURFBOARD` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_CLOSE` | `ITEMMENU_NOUSE` |
| 88 | CHOICE SCARF | `CHOICE_SCARF` | `HELD_CHOICE_SCARF` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 89 | ASSAULT VEST | `ASSAULT_VEST` | `HELD_ASSAULT_VEST` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 8A | CHARCOAL | `CHARCOAL` | `HELD_FIRE_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 8B | BERRY JUICE | `BERRY_JUICE` | `HELD_BERRY` | 20 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 8C | SCOPE LENS | `SCOPE_LENS` | `HELD_CRITICAL_UP` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 8D | EXPERT BELT | `EXPERT_BELT` | `HELD_EXPERT_BELT` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 8E | MUSCLE BAND | `MUSCLE_BAND` | `HELD_MUSCLE_BAND` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 8F | METAL COAT | `METAL_COAT` | `HELD_STEEL_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 90 | DRAGON FANG | `DRAGON_FANG` | `HELD_DRAGON_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 91 | WISE GLASSES | `WISE_GLASSES` | `HELD_WISE_GLASSES` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 92 | LEFTOVERS | `LEFTOVERS` | `HELD_LEFTOVERS` | 10 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 93 | EVOLITE | `EVOLITE` | `HELD_EVOLITE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 94 | AIR BALLOON | `AIR_BALLOON` | `HELD_AIR_BALLOON` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 95 | SHELL BELL | `SHELL_BELL` | `HELD_SHELL_BELL` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 96 | MYSTERYBERRY | `MYSTERYBERRY` | `HELD_RESTORE_PP` | -1 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| 97 | DRAGON SCALE | `DRAGON_SCALE` | `HELD_DRAGON_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 98 | BERSERK GENE | `BERSERK_GENE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 99 | ROCKY HELMET | `ROCKY_HELMET` | `HELD_ROCKY_HELMET` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 9A | METRONOME | `METRONOME_ITEM` | `HELD_METRONOME` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 9B | WHIRL KIT | `WHIRL_KIT` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_CLOSE` | `ITEMMENU_NOUSE` |
| 9C | SACRED ASH | `SACRED_ASH` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_CLOSE` | `ITEMMENU_NOUSE` |
| 9D | HEAVY BALL | `HEAVY_BALL` | `HELD_NONE` | 0 | `BALL` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| 9E | FLOWER MAIL | `FLOWER_MAIL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 9F | LEVEL BALL | `LEVEL_BALL` | `HELD_NONE` | 0 | `BALL` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| A0 | LURE BALL | `LURE_BALL` | `HELD_NONE` | 0 | `BALL` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| A1 | FAST BALL | `FAST_BALL` | `HELD_NONE` | 0 | `BALL` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| A2 | SKY PASS | `SKY_PASS` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_CLOSE` | `ITEMMENU_NOUSE` |
| A3 | LIGHT BALL | `LIGHT_BALL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| A4 | FRIEND BALL | `FRIEND_BALL` | `HELD_NONE` | 0 | `BALL` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| A5 | MOON BALL | `MOON_BALL` | `HELD_NONE` | 0 | `BALL` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| A6 | LOVE BALL | `LOVE_BALL` | `HELD_NONE` | 0 | `BALL` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| A7 | NORMAL BOX | `NORMAL_BOX` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_CURRENT` | `ITEMMENU_NOUSE` |
| A8 | GORGEOUS BOX | `GORGEOUS_BOX` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_CURRENT` | `ITEMMENU_NOUSE` |
| A9 | SUN STONE | `SUN_STONE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| AA | POLKADOT BOW | `POLKADOT_BOW` | `HELD_NORMAL_BOOST` | 20 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| AB | LANTERN | `LANTERN` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_CLOSE` | `ITEMMENU_NOUSE` |
| AC | UP-GRADE | `UP_GRADE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| AD | BERRY | `BERRY` | `HELD_BERRY` | 10 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| AE | GOLD BERRY | `GOLD_BERRY` | `HELD_BERRY` | 30 | `ITEM` | `ITEMMENU_PARTY` | `ITEMMENU_PARTY` |
| AF | SQUIRTBOTTLE | `SQUIRTBOTTLE` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_CLOSE` | `ITEMMENU_NOUSE` |
| B0 | POWER GLOVE | `POWER_GLOVE` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_CLOSE` | `ITEMMENU_NOUSE` |
| B1 | PARK BALL | `PARK_BALL` | `HELD_NONE` | 0 | `BALL` | `ITEMMENU_NOUSE` | `ITEMMENU_CLOSE` |
| B2 | RAINBOW WING | `RAINBOW_WING` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| B3 | CLIMB GEAR | `CLIMB_GEAR` | `HELD_NONE` | 0 | `KEY_ITEM` | `ITEMMENU_CLOSE` | `ITEMMENU_NOUSE` |
| B4 | BRICK PIECE | `BRICK_PIECE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| B5 | SURF MAIL | `SURF_MAIL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| B6 | LITEBLUEMAIL | `LITEBLUEMAIL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| B7 | PORTRAITMAIL | `PORTRAITMAIL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| B8 | LOVELY MAIL | `LOVELY_MAIL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| B9 | EON MAIL | `EON_MAIL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| BA | MORPH MAIL | `MORPH_MAIL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| BB | BLUESKY MAIL | `BLUESKY_MAIL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| BC | MUSIC MAIL | `MUSIC_MAIL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| BD | MIRAGE MAIL | `MIRAGE_MAIL` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| BE | TERU-SAMA | `ITEM_BE` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| BF | TM01 | `TM01` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| C0 | TM02 | `TM02` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| C1 | TM03 | `TM03` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| C2 | TM04 | `TM04` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| C3 | TERU-SAMA | `ITEM_C3` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| C4 | TM05 | `TM05` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| C5 | TM06 | `TM06` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| C6 | TM07 | `TM07` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| C7 | TM08 | `TM08` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| C8 | TM09 | `TM09` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| C9 | TM10 | `TM10` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| CA | TM11 | `TM11` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| CB | TM12 | `TM12` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| CC | TM13 | `TM13` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| CD | TM14 | `TM14` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| CE | TM15 | `TM15` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| CF | TM16 | `TM16` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| D0 | TM17 | `TM17` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| D1 | TM18 | `TM18` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| D2 | TM19 | `TM19` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| D3 | TM20 | `TM20` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| D4 | TM21 | `TM21` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| D5 | TM22 | `TM22` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| D6 | TM23 | `TM23` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| D7 | TM24 | `TM24` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| D8 | TM25 | `TM25` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| D9 | TM26 | `TM26` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| DA | TM27 | `TM27` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| DB | TM28 | `TM28` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| DC | TERU-SAMA | `ITEM_DC` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| DD | TM29 | `TM29` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| DE | TM30 | `TM30` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| DF | TM31 | `TM31` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| E0 | TM32 | `TM32` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| E1 | TM33 | `TM33` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| E2 | TM34 | `TM34` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| E3 | TM35 | `TM35` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| E4 | TM36 | `TM36` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| E5 | TM37 | `TM37` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| E6 | TM38 | `TM38` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| E7 | TM39 | `TM39` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| E8 | TM40 | `TM40` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| E9 | TM41 | `TM41` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| EA | TM42 | `TM42` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| EB | TM43 | `TM43` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| EC | TM44 | `TM44` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| ED | TM45 | `TM45` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| EE | TM46 | `TM46` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| EF | TM47 | `TM47` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| F0 | TM48 | `TM48` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| F1 | TM49 | `TM49` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| F2 | TM50 | `TM50` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| F3 | TM51 | `TM51 (CUT)` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| F4 | TM52 | `TM52 (FLY)` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| F5 | TM53 | `TM53 (SURF)` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| F6 | TM54 | `TM54 (STRENGTH)` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| F7 | TM55 | `TM55 (FLASH)` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| F8 | TM56 | `TM56 (WHIRLPOOL)` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| F9 | TM57 | `TM57 (WATERFALL)` | `HELD_NONE` | 0 | `TM_HM` | `ITEMMENU_PARTY` | `ITEMMENU_NOUSE` |
| FA | TERU-SAMA | `ITEM_FA` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| FB | TERU-SAMA | `$` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| FC | TERU-SAMA | `$` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| FD | TERU-SAMA | `$` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| FE | TERU-SAMA | `$` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| FF | TERU-SAMA | `$` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |
| 100 | ? | `$00` | `HELD_NONE` | 0 | `ITEM` | `ITEMMENU_NOUSE` | `ITEMMENU_NOUSE` |

## Pokemon Base Stats And Types

This table comes from `data/pokemon/base_stats/*.asm`. TM/HM compatibility
lives in each same file after the stat/type/item rows.

| ID | Species | Types | HP | Atk | Def | Spe | SpA | SpD | BST | Wild Items |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 001 | Bulbasaur | Grass/Poison | 45 | 49 | 49 | 45 | 65 | 65 | 318 | `NO_ITEM`, `NO_ITEM` |
| 002 | Ivysaur | Grass/Poison | 60 | 62 | 63 | 60 | 80 | 80 | 405 | `NO_ITEM`, `NO_ITEM` |
| 003 | Venusaur | Grass/Poison | 95 | 97 | 98 | 95 | 115 | 115 | 615 | `NO_ITEM`, `NO_ITEM` |
| 004 | Charmander | Fire | 39 | 52 | 43 | 65 | 60 | 50 | 309 | `NO_ITEM`, `NO_ITEM` |
| 005 | Charmeleon | Fire | 58 | 64 | 58 | 80 | 80 | 65 | 405 | `NO_ITEM`, `NO_ITEM` |
| 006 | Charizard | Fire/Flying | 93 | 99 | 93 | 115 | 124 | 100 | 624 | `NO_ITEM`, `NO_ITEM` |
| 007 | Squirtle | Water | 44 | 48 | 65 | 43 | 50 | 64 | 314 | `NO_ITEM`, `NO_ITEM` |
| 008 | Wartortle | Water | 59 | 63 | 80 | 58 | 65 | 80 | 405 | `NO_ITEM`, `NO_ITEM` |
| 009 | Blastoise | Water | 94 | 98 | 115 | 93 | 100 | 120 | 620 | `NO_ITEM`, `NO_ITEM` |
| 010 | Caterpie | Bug | 45 | 30 | 35 | 45 | 20 | 20 | 195 | `NO_ITEM`, `NO_ITEM` |
| 011 | Metapod | Bug | 60 | 30 | 55 | 30 | 25 | 25 | 225 | `NO_ITEM`, `NO_ITEM` |
| 012 | Butterfree | Bug/Flying | 90 | 45 | 50 | 110 | 95 | 110 | 500 | `NO_ITEM`, `SILVERPOWDER` |
| 013 | Weedle | Bug/Poison | 40 | 35 | 30 | 50 | 20 | 20 | 195 | `NO_ITEM`, `NO_ITEM` |
| 014 | Kakuna | Bug/Poison | 45 | 40 | 50 | 35 | 25 | 25 | 220 | `NO_ITEM`, `NO_ITEM` |
| 015 | Beedrill | Bug/Poison | 75 | 120 | 40 | 120 | 45 | 80 | 480 | `NO_ITEM`, `POISON_BARB` |
| 016 | Pidgey | Normal/Flying | 50 | 45 | 40 | 56 | 35 | 35 | 261 | `NO_ITEM`, `NO_ITEM` |
| 017 | Pidgeotto | Normal/Flying | 70 | 60 | 60 | 71 | 50 | 60 | 371 | `NO_ITEM`, `NO_ITEM` |
| 018 | Pidgeot | Normal/Flying | 113 | 80 | 95 | 91 | 70 | 110 | 559 | `NO_ITEM`, `NO_ITEM` |
| 019 | Rattata | Normal | 30 | 70 | 35 | 72 | 25 | 35 | 267 | `NO_ITEM`, `NO_ITEM` |
| 020 | Raticate | Normal | 55 | 120 | 60 | 97 | 50 | 70 | 452 | `NO_ITEM`, `NO_ITEM` |
| 021 | Spearow | Normal/Flying | 40 | 70 | 30 | 70 | 31 | 31 | 272 | `NO_ITEM`, `NO_ITEM` |
| 022 | Fearow | Normal/Flying | 110 | 130 | 65 | 100 | 50 | 50 | 505 | `NO_ITEM`, `SHARP_BEAK` |
| 023 | Ekans | Poison | 45 | 60 | 44 | 55 | 40 | 54 | 298 | `NO_ITEM`, `NO_ITEM` |
| 024 | Arbok | Poison/Dark | 100 | 85 | 99 | 80 | 80 | 79 | 523 | `NO_ITEM`, `NO_ITEM` |
| 025 | Pikachu | Electric | 60 | 100 | 30 | 90 | 100 | 40 | 420 | `NO_ITEM`, `BERRY` |
| 026 | Raichu | Electric/Fighting | 80 | 110 | 55 | 110 | 125 | 110 | 590 | `NO_ITEM`, `BERRY` |
| 027 | Sandshrew | Ground | 70 | 75 | 85 | 40 | 20 | 30 | 320 | `NO_ITEM`, `NO_ITEM` |
| 028 | Sandslash | Ground | 105 | 110 | 130 | 65 | 45 | 55 | 510 | `NO_ITEM`, `NO_ITEM` |
| 029 | Nidoran F | Poison | 55 | 47 | 52 | 41 | 40 | 40 | 275 | `NO_ITEM`, `NO_ITEM` |
| 030 | Nidorina | Poison | 90 | 62 | 77 | 56 | 55 | 65 | 405 | `NO_ITEM`, `NO_ITEM` |
| 031 | Nidoqueen | Poison/Ground | 130 | 85 | 100 | 75 | 75 | 100 | 565 | `NO_ITEM`, `NO_ITEM` |
| 032 | Nidoran M | Poison | 46 | 57 | 40 | 50 | 40 | 40 | 273 | `NO_ITEM`, `NO_ITEM` |
| 033 | Nidorino | Poison | 61 | 102 | 57 | 75 | 55 | 55 | 405 | `NO_ITEM`, `NO_ITEM` |
| 034 | Nidoking | Poison/Ground | 95 | 115 | 77 | 100 | 100 | 78 | 565 | `NO_ITEM`, `NO_ITEM` |
| 035 | Clefairy | Normal | 70 | 45 | 48 | 35 | 60 | 65 | 323 | `MYSTERYBERRY`, `MOON_STONE` |
| 036 | Clefable | Normal | 120 | 50 | 90 | 45 | 85 | 100 | 490 | `MYSTERYBERRY`, `MOON_STONE` |
| 037 | Vulpix | Fire | 55 | 41 | 40 | 65 | 70 | 65 | 336 | `BURNT_BERRY`, `BURNT_BERRY` |
| 038 | Ninetales | Fire | 80 | 76 | 75 | 100 | 100 | 100 | 531 | `BURNT_BERRY`, `BURNT_BERRY` |
| 039 | Jigglypuff | Normal | 115 | 45 | 20 | 20 | 45 | 25 | 270 | `NO_ITEM`, `NO_ITEM` |
| 040 | Wigglytuff | Normal | 160 | 100 | 55 | 45 | 75 | 80 | 515 | `NO_ITEM`, `NO_ITEM` |
| 041 | Zubat | Poison/Flying | 40 | 45 | 35 | 70 | 30 | 40 | 260 | `NO_ITEM`, `NO_ITEM` |
| 042 | Golbat | Poison/Flying | 80 | 80 | 80 | 90 | 65 | 75 | 470 | `NO_ITEM`, `NO_ITEM` |
| 043 | Oddish | Grass/Poison | 45 | 50 | 55 | 30 | 75 | 65 | 320 | `NO_ITEM`, `NO_ITEM` |
| 044 | Gloom | Grass/Poison | 60 | 65 | 70 | 40 | 85 | 75 | 395 | `NO_ITEM`, `NO_ITEM` |
| 045 | Vileplume | Grass/Poison | 120 | 80 | 85 | 50 | 100 | 90 | 525 | `NO_ITEM`, `NO_ITEM` |
| 046 | Paras | Bug/Grass | 35 | 70 | 55 | 25 | 45 | 55 | 285 | `TINYMUSHROOM`, `BIG_MUSHROOM` |
| 047 | Parasect | Bug/Grass | 90 | 130 | 80 | 30 | 80 | 80 | 490 | `TINYMUSHROOM`, `BIG_MUSHROOM` |
| 048 | Venonat | Bug/Poison | 60 | 55 | 50 | 45 | 40 | 55 | 305 | `NO_ITEM`, `NO_ITEM` |
| 049 | Venomoth | Bug/Poison | 110 | 80 | 60 | 100 | 100 | 150 | 600 | `NO_ITEM`, `NO_ITEM` |
| 050 | Diglett | Ground | 10 | 70 | 25 | 95 | 35 | 45 | 280 | `NO_ITEM`, `NO_ITEM` |
| 051 | Dugtrio | Ground | 35 | 110 | 50 | 130 | 50 | 70 | 445 | `NO_ITEM`, `NO_ITEM` |
| 052 | Meowth | Normal | 40 | 45 | 35 | 90 | 40 | 40 | 290 | `NO_ITEM`, `NO_ITEM` |
| 053 | Persian | Normal | 65 | 110 | 60 | 115 | 70 | 65 | 485 | `NO_ITEM`, `NO_ITEM` |
| 054 | Psyduck | Water | 50 | 52 | 48 | 55 | 90 | 50 | 345 | `NO_ITEM`, `NO_ITEM` |
| 055 | Golduck | Water | 80 | 82 | 78 | 85 | 120 | 80 | 525 | `NO_ITEM`, `NO_ITEM` |
| 056 | Mankey | Fighting | 60 | 80 | 35 | 70 | 35 | 45 | 325 | `NO_ITEM`, `NO_ITEM` |
| 057 | Primeape | Fighting | 100 | 120 | 120 | 95 | 60 | 40 | 535 | `NO_ITEM`, `NO_ITEM` |
| 058 | Growlithe | Fire | 55 | 70 | 45 | 60 | 70 | 50 | 350 | `BURNT_BERRY`, `BURNT_BERRY` |
| 059 | Arcanine | Fire | 120 | 115 | 80 | 90 | 130 | 80 | 615 | `BURNT_BERRY`, `BURNT_BERRY` |
| 060 | Poliwag | Water | 40 | 50 | 40 | 90 | 40 | 40 | 300 | `NO_ITEM`, `NO_ITEM` |
| 061 | Poliwhirl | Water | 75 | 65 | 75 | 90 | 70 | 50 | 425 | `NO_ITEM`, `KINGS_ROCK` |
| 062 | Poliwrath | Water/Fighting | 120 | 85 | 110 | 70 | 70 | 90 | 545 | `NO_ITEM`, `KINGS_ROCK` |
| 063 | Abra | Psychic | 25 | 20 | 15 | 90 | 105 | 55 | 310 | `NO_ITEM`, `NO_ITEM` |
| 064 | Kadabra | Psychic | 50 | 35 | 30 | 105 | 120 | 70 | 410 | `NO_ITEM`, `NO_ITEM` |
| 065 | Alakazam | Psychic | 60 | 50 | 45 | 120 | 150 | 130 | 555 | `NO_ITEM`, `NO_ITEM` |
| 066 | Machop | Fighting | 80 | 80 | 50 | 35 | 35 | 35 | 315 | `NO_ITEM`, `NO_ITEM` |
| 067 | Machoke | Fighting | 100 | 100 | 70 | 45 | 50 | 60 | 425 | `NO_ITEM`, `NO_ITEM` |
| 068 | Machamp | Fighting | 110 | 150 | 130 | 55 | 65 | 85 | 595 | `NO_ITEM`, `NO_ITEM` |
| 069 | Bellsprout | Grass/Poison | 50 | 75 | 35 | 40 | 70 | 30 | 300 | `NO_ITEM`, `NO_ITEM` |
| 070 | Weepinbell | Grass/Poison | 75 | 90 | 60 | 55 | 85 | 60 | 425 | `NO_ITEM`, `NO_ITEM` |
| 071 | Victreebel | Grass/Poison | 95 | 120 | 65 | 92 | 120 | 60 | 552 | `NO_ITEM`, `NO_ITEM` |
| 072 | Tentacool | Water/Poison | 40 | 40 | 35 | 70 | 50 | 100 | 335 | `NO_ITEM`, `NO_ITEM` |
| 073 | Tentacruel | Water/Poison | 80 | 80 | 65 | 100 | 100 | 120 | 545 | `NO_ITEM`, `NO_ITEM` |
| 074 | Geodude | Rock/Ground | 40 | 80 | 100 | 20 | 30 | 30 | 300 | `NO_ITEM`, `EVERSTONE` |
| 075 | Graveler | Rock/Ground | 70 | 95 | 115 | 35 | 45 | 45 | 405 | `NO_ITEM`, `EVERSTONE` |
| 076 | Golem | Rock/Ground | 100 | 110 | 150 | 45 | 55 | 100 | 560 | `NO_ITEM`, `EVERSTONE` |
| 077 | Ponyta | Fire | 50 | 85 | 55 | 90 | 65 | 65 | 410 | `NO_ITEM`, `NO_ITEM` |
| 078 | Rapidash | Fire | 65 | 100 | 70 | 105 | 120 | 80 | 540 | `NO_ITEM`, `NO_ITEM` |
| 079 | Slowpoke | Water/Psychic | 90 | 65 | 65 | 15 | 40 | 40 | 315 | `NO_ITEM`, `KINGS_ROCK` |
| 080 | Slowbro | Water/Psychic | 115 | 75 | 110 | 30 | 100 | 80 | 510 | `NO_ITEM`, `KINGS_ROCK` |
| 081 | Magnemite | Electric/Steel | 35 | 75 | 70 | 45 | 95 | 55 | 375 | `NO_ITEM`, `METAL_COAT` |
| 082 | Magneton | Electric/Steel | 70 | 85 | 110 | 80 | 120 | 50 | 515 | `NO_ITEM`, `METAL_COAT` |
| 083 | Farfetch D | Normal/Flying | 60 | 130 | 55 | 60 | 58 | 62 | 425 | `STICK`, `STICK` |
| 084 | Doduo | Normal/Flying | 35 | 85 | 45 | 75 | 35 | 35 | 310 | `NO_ITEM`, `NO_ITEM` |
| 085 | Dodrio | Normal/Flying | 80 | 110 | 70 | 120 | 60 | 60 | 500 | `NO_ITEM`, `SHARP_BEAK` |
| 086 | Seel | Water | 65 | 45 | 55 | 45 | 45 | 70 | 325 | `NO_ITEM`, `NO_ITEM` |
| 087 | Dewgong | Water/Ice | 110 | 70 | 95 | 50 | 95 | 105 | 525 | `NO_ITEM`, `NO_ITEM` |
| 088 | Grimer | Poison | 80 | 80 | 50 | 25 | 40 | 50 | 325 | `NO_ITEM`, `NUGGET` |
| 089 | Muk | Poison | 120 | 85 | 120 | 50 | 65 | 100 | 540 | `NO_ITEM`, `NUGGET` |
| 090 | Shellder | Water | 30 | 65 | 100 | 40 | 45 | 25 | 305 | `PEARL`, `BIG_PEARL` |
| 091 | Cloyster | Water/Ice | 80 | 95 | 180 | 70 | 85 | 45 | 555 | `PEARL`, `BIG_PEARL` |
| 092 | Gastly | Ghost/Psychic | 30 | 35 | 30 | 80 | 100 | 35 | 310 | `NO_ITEM`, `NO_ITEM` |
| 093 | Haunter | Ghost/Psychic | 45 | 70 | 45 | 95 | 115 | 55 | 425 | `NO_ITEM`, `NO_ITEM` |
| 094 | Gengar | Ghost/Psychic | 60 | 130 | 60 | 100 | 130 | 75 | 555 | `NO_ITEM`, `NO_ITEM` |
| 095 | Onix | Rock/Ground | 70 | 80 | 160 | 120 | 30 | 45 | 505 | `NO_ITEM`, `NO_ITEM` |
| 096 | Drowzee | Psychic | 90 | 48 | 65 | 42 | 43 | 90 | 378 | `NO_ITEM`, `NO_ITEM` |
| 097 | Hypno | Psychic | 115 | 85 | 120 | 57 | 73 | 115 | 565 | `NO_ITEM`, `NO_ITEM` |
| 098 | Krabby | Water | 30 | 105 | 90 | 50 | 25 | 25 | 325 | `NO_ITEM`, `NO_ITEM` |
| 099 | Kingler | Water | 55 | 130 | 115 | 75 | 80 | 50 | 505 | `NO_ITEM`, `NO_ITEM` |
| 100 | Voltorb | Electric | 40 | 30 | 50 | 100 | 65 | 55 | 340 | `NO_ITEM`, `NO_ITEM` |
| 101 | Electrode | Electric | 60 | 50 | 70 | 170 | 100 | 80 | 530 | `NO_ITEM`, `NO_ITEM` |
| 102 | Exeggcute | Grass/Psychic | 60 | 40 | 80 | 40 | 60 | 45 | 325 | `NO_ITEM`, `NO_ITEM` |
| 103 | Exeggutor | Grass/Psychic | 105 | 95 | 85 | 55 | 125 | 80 | 545 | `NO_ITEM`, `NO_ITEM` |
| 104 | Cubone | Ground | 50 | 50 | 95 | 35 | 40 | 50 | 320 | `NO_ITEM`, `THICK_CLUB` |
| 105 | Marowak | Ground | 100 | 120 | 110 | 45 | 50 | 80 | 505 | `NO_ITEM`, `THICK_CLUB` |
| 106 | Hitmonlee | Fighting | 80 | 120 | 53 | 102 | 35 | 110 | 500 | `NO_ITEM`, `NO_ITEM` |
| 107 | Hitmonchan | Fighting | 50 | 80 | 79 | 75 | 120 | 110 | 514 | `NO_ITEM`, `NO_ITEM` |
| 108 | Lickitung | Normal | 125 | 55 | 80 | 30 | 60 | 105 | 455 | `NO_ITEM`, `NO_ITEM` |
| 109 | Koffing | Poison/Dark | 40 | 65 | 95 | 35 | 60 | 45 | 340 | `NO_ITEM`, `NO_ITEM` |
| 110 | Weezing | Poison/Dark | 110 | 90 | 120 | 60 | 85 | 70 | 535 | `NO_ITEM`, `NO_ITEM` |
| 111 | Rhyhorn | Ground/Rock | 100 | 85 | 95 | 25 | 30 | 30 | 365 | `NO_ITEM`, `NO_ITEM` |
| 112 | Rhydon | Ground/Rock | 130 | 130 | 120 | 40 | 45 | 45 | 510 | `NO_ITEM`, `NO_ITEM` |
| 113 | Chansey | Normal | 250 | 5 | 5 | 50 | 105 | 105 | 520 | `NO_ITEM`, `LUCKY_EGG` |
| 114 | Tangela | Grass | 130 | 55 | 115 | 50 | 100 | 50 | 500 | `NO_ITEM`, `NO_ITEM` |
| 115 | Kangaskhan | Normal | 105 | 125 | 80 | 90 | 40 | 80 | 520 | `NO_ITEM`, `NO_ITEM` |
| 116 | Horsea | Water | 50 | 40 | 70 | 60 | 70 | 25 | 315 | `NO_ITEM`, `DRAGON_SCALE` |
| 117 | Seadra | Water | 70 | 65 | 95 | 85 | 95 | 45 | 455 | `NO_ITEM`, `DRAGON_SCALE` |
| 118 | Goldeen | Water | 45 | 67 | 60 | 63 | 35 | 50 | 320 | `NO_ITEM`, `NO_ITEM` |
| 119 | Seaking | Water | 80 | 92 | 65 | 68 | 80 | 80 | 465 | `NO_ITEM`, `NO_ITEM` |
| 120 | Staryu | Water | 30 | 45 | 55 | 85 | 70 | 55 | 340 | `STARDUST`, `STAR_PIECE` |
| 121 | Starmie | Water/Psychic | 80 | 75 | 85 | 115 | 125 | 85 | 565 | `STARDUST`, `STAR_PIECE` |
| 122 | Mr. Mime | Psychic | 40 | 45 | 65 | 90 | 100 | 180 | 520 | `NO_ITEM`, `MYSTERYBERRY` |
| 123 | Scyther | Bug/Flying | 80 | 110 | 80 | 105 | 55 | 80 | 510 | `NO_ITEM`, `NO_ITEM` |
| 124 | Jynx | Ice/Psychic | 75 | 50 | 55 | 115 | 135 | 95 | 525 | `ICE_BERRY`, `ICE_BERRY` |
| 125 | Electabuzz | Electric/Fighting | 65 | 105 | 57 | 105 | 95 | 85 | 512 | `NO_ITEM`, `NO_ITEM` |
| 126 | Magmar | Fire | 120 | 95 | 60 | 82 | 125 | 85 | 567 | `BURNT_BERRY`, `BURNT_BERRY` |
| 127 | Pinsir | Bug | 80 | 140 | 100 | 85 | 55 | 70 | 530 | `NO_ITEM`, `NO_ITEM` |
| 128 | Tauros | Normal | 75 | 120 | 95 | 110 | 40 | 70 | 510 | `NO_ITEM`, `NO_ITEM` |
| 129 | Magikarp | Water | 20 | 10 | 55 | 80 | 15 | 20 | 200 | `NO_ITEM`, `NO_ITEM` |
| 130 | Gyarados | Water/Dragon | 100 | 125 | 79 | 81 | 90 | 100 | 575 | `NO_ITEM`, `NO_ITEM` |
| 131 | Lapras | Water/Ice | 130 | 85 | 110 | 60 | 85 | 110 | 580 | `NO_ITEM`, `NO_ITEM` |
| 132 | Ditto | Normal | 100 | 48 | 48 | 48 | 48 | 48 | 340 | `NO_ITEM`, `NO_ITEM` |
| 133 | Eevee | Normal | 55 | 55 | 50 | 55 | 45 | 65 | 325 | `NO_ITEM`, `NO_ITEM` |
| 134 | Vaporeon | Water | 130 | 65 | 60 | 65 | 110 | 110 | 540 | `NO_ITEM`, `NO_ITEM` |
| 135 | Jolteon | Electric | 65 | 65 | 60 | 145 | 110 | 95 | 540 | `NO_ITEM`, `NO_ITEM` |
| 136 | Flareon | Fire | 65 | 145 | 60 | 65 | 95 | 110 | 540 | `NO_ITEM`, `NO_ITEM` |
| 137 | Porygon | Normal | 65 | 60 | 70 | 40 | 85 | 75 | 395 | `NO_ITEM`, `NO_ITEM` |
| 138 | Omanyte | Rock/Water | 35 | 40 | 100 | 35 | 90 | 55 | 355 | `NO_ITEM`, `NO_ITEM` |
| 139 | Omastar | Rock/Water | 80 | 80 | 125 | 55 | 115 | 70 | 525 | `NO_ITEM`, `NO_ITEM` |
| 140 | Kabuto | Rock/Water | 30 | 80 | 90 | 55 | 55 | 45 | 355 | `NO_ITEM`, `NO_ITEM` |
| 141 | Kabutops | Rock/Water | 60 | 125 | 115 | 90 | 65 | 70 | 525 | `NO_ITEM`, `NO_ITEM` |
| 142 | Aerodactyl | Rock/Flying | 100 | 105 | 80 | 130 | 60 | 75 | 550 | `NO_ITEM`, `NO_ITEM` |
| 143 | Snorlax | Normal | 160 | 110 | 65 | 30 | 65 | 110 | 540 | `LEFTOVERS`, `LEFTOVERS` |
| 144 | Articuno | Ice/Flying | 100 | 95 | 100 | 85 | 105 | 125 | 610 | `NO_ITEM`, `NO_ITEM` |
| 145 | Zapdos | Electric/Flying | 100 | 100 | 85 | 100 | 135 | 90 | 610 | `NO_ITEM`, `NO_ITEM` |
| 146 | Moltres | Fire/Flying | 100 | 110 | 90 | 90 | 135 | 85 | 610 | `NO_ITEM`, `NO_ITEM` |
| 147 | Dratini | Dragon | 41 | 64 | 45 | 50 | 50 | 50 | 300 | `NO_ITEM`, `DRAGON_SCALE` |
| 148 | Dragonair | Dragon | 90 | 84 | 65 | 70 | 110 | 70 | 489 | `NO_ITEM`, `DRAGON_SCALE` |
| 149 | Dragonite | Dragon/Flying | 121 | 134 | 95 | 70 | 110 | 100 | 630 | `NO_ITEM`, `DRAGON_SCALE` |
| 150 | Mewtwo | Psychic | 106 | 110 | 90 | 130 | 154 | 90 | 680 | `NO_ITEM`, `BERSERK_GENE` |
| 151 | Mew | Psychic | 100 | 100 | 100 | 100 | 100 | 100 | 600 | `NO_ITEM`, `MIRACLEBERRY` |
| 152 | Chikorita | Grass | 55 | 49 | 65 | 45 | 49 | 65 | 328 | `NO_ITEM`, `NO_ITEM` |
| 153 | Bayleef | Grass | 70 | 72 | 80 | 60 | 73 | 80 | 435 | `NO_ITEM`, `NO_ITEM` |
| 154 | Meganium | Grass | 130 | 75 | 107 | 60 | 83 | 100 | 555 | `NO_ITEM`, `NO_ITEM` |
| 155 | Cyndaquil | Fire | 45 | 52 | 43 | 65 | 60 | 50 | 315 | `NO_ITEM`, `NO_ITEM` |
| 156 | Quilava | Fire | 68 | 74 | 58 | 80 | 90 | 65 | 435 | `NO_ITEM`, `NO_ITEM` |
| 157 | Typhlosion | Fire/Normal | 78 | 99 | 78 | 100 | 130 | 70 | 555 | `NO_ITEM`, `NO_ITEM` |
| 158 | Totodile | Water | 50 | 65 | 64 | 43 | 44 | 48 | 314 | `NO_ITEM`, `NO_ITEM` |
| 159 | Croconaw | Water | 75 | 90 | 90 | 58 | 59 | 63 | 435 | `NO_ITEM`, `NO_ITEM` |
| 160 | Feraligatr | Water/Fighting | 85 | 105 | 100 | 87 | 95 | 83 | 555 | `NO_ITEM`, `NO_ITEM` |
| 161 | Sentret | Normal | 35 | 60 | 34 | 20 | 35 | 45 | 229 | `NO_ITEM`, `BERRY` |
| 162 | Furret | Normal | 85 | 100 | 64 | 90 | 100 | 55 | 494 | `BERRY`, `GOLD_BERRY` |
| 163 | Hoothoot | Normal/Flying | 60 | 50 | 30 | 50 | 36 | 56 | 282 | `NO_ITEM`, `NO_ITEM` |
| 164 | Noctowl | Normal/Flying | 100 | 50 | 50 | 70 | 110 | 120 | 500 | `NO_ITEM`, `NO_ITEM` |
| 165 | Ledyba | Bug/Flying | 40 | 40 | 30 | 55 | 40 | 80 | 285 | `NO_ITEM`, `NO_ITEM` |
| 166 | Ledian | Bug/Flying | 80 | 100 | 50 | 105 | 45 | 120 | 500 | `NO_ITEM`, `NO_ITEM` |
| 167 | Spinarak | Bug/Poison | 40 | 60 | 40 | 30 | 40 | 40 | 250 | `NO_ITEM`, `NO_ITEM` |
| 168 | Ariados | Bug/Poison | 110 | 90 | 100 | 40 | 60 | 60 | 460 | `NO_ITEM`, `NO_ITEM` |
| 169 | Crobat | Poison/Flying | 100 | 120 | 105 | 130 | 70 | 80 | 605 | `NO_ITEM`, `NO_ITEM` |
| 170 | Chinchou | Water/Electric | 75 | 38 | 38 | 67 | 56 | 56 | 330 | `NO_ITEM`, `NO_ITEM` |
| 171 | Lanturn | Water/Electric | 125 | 58 | 76 | 75 | 105 | 105 | 544 | `NO_ITEM`, `NO_ITEM` |
| 172 | Pichu | Electric | 20 | 40 | 15 | 60 | 35 | 35 | 205 | `NO_ITEM`, `BERRY` |
| 173 | Cleffa | Normal | 50 | 25 | 28 | 15 | 45 | 55 | 218 | `MYSTERYBERRY`, `MOON_STONE` |
| 174 | Igglybuff | Normal | 90 | 30 | 15 | 15 | 40 | 20 | 210 | `NO_ITEM`, `NO_ITEM` |
| 175 | Togepi | Normal | 35 | 20 | 65 | 20 | 40 | 65 | 245 | `NO_ITEM`, `NO_ITEM` |
| 176 | Togetic | Normal/Flying | 55 | 40 | 85 | 40 | 140 | 105 | 465 | `NO_ITEM`, `NO_ITEM` |
| 177 | Natu | Psychic/Flying | 40 | 50 | 45 | 70 | 70 | 45 | 320 | `NO_ITEM`, `NO_ITEM` |
| 178 | Xatu | Psychic/Flying | 110 | 75 | 70 | 150 | 115 | 90 | 610 | `NO_ITEM`, `NO_ITEM` |
| 179 | Mareep | Electric | 55 | 40 | 40 | 35 | 65 | 45 | 280 | `NO_ITEM`, `NO_ITEM` |
| 180 | Flaaffy | Electric | 70 | 55 | 55 | 45 | 80 | 60 | 365 | `NO_ITEM`, `NO_ITEM` |
| 181 | Ampharos | Electric/Dragon | 112 | 75 | 75 | 55 | 115 | 90 | 522 | `NO_ITEM`, `NO_ITEM` |
| 182 | Bellossom | Grass | 85 | 60 | 85 | 80 | 115 | 100 | 525 | `NO_ITEM`, `NO_ITEM` |
| 183 | Marill | Water | 70 | 60 | 50 | 40 | 20 | 50 | 290 | `NO_ITEM`, `NO_ITEM` |
| 184 | Azumarill | Water | 100 | 150 | 80 | 50 | 50 | 80 | 510 | `NO_ITEM`, `NO_ITEM` |
| 185 | Sudowoodo | Rock | 90 | 105 | 125 | 45 | 30 | 60 | 455 | `NO_ITEM`, `NO_ITEM` |
| 186 | Politoed | Water | 100 | 70 | 80 | 85 | 115 | 105 | 555 | `NO_ITEM`, `KINGS_ROCK` |
| 187 | Hoppip | Grass/Flying | 35 | 35 | 40 | 50 | 35 | 55 | 250 | `NO_ITEM`, `NO_ITEM` |
| 188 | Skiploom | Grass/Steel | 55 | 45 | 50 | 80 | 45 | 65 | 340 | `NO_ITEM`, `NO_ITEM` |
| 189 | Jumpluff | Grass/Flying | 110 | 55 | 70 | 135 | 55 | 85 | 510 | `NO_ITEM`, `NO_ITEM` |
| 190 | Aipom | Normal | 90 | 100 | 55 | 110 | 40 | 55 | 450 | `NO_ITEM`, `NO_ITEM` |
| 191 | Sunkern | Grass | 30 | 30 | 30 | 30 | 30 | 30 | 180 | `NO_ITEM`, `NO_ITEM` |
| 192 | Sunflora | Grass | 75 | 75 | 55 | 30 | 150 | 85 | 470 | `NO_ITEM`, `NO_ITEM` |
| 193 | Yanma | Bug/Dragon | 70 | 80 | 60 | 85 | 85 | 75 | 455 | `NO_ITEM`, `NO_ITEM` |
| 194 | Wooper | Water/Ground | 55 | 45 | 45 | 15 | 25 | 25 | 210 | `NO_ITEM`, `NO_ITEM` |
| 195 | Quagsire | Water/Ground | 120 | 100 | 85 | 35 | 70 | 65 | 475 | `NO_ITEM`, `NO_ITEM` |
| 196 | Espeon | Psychic | 65 | 65 | 60 | 125 | 140 | 95 | 550 | `NO_ITEM`, `NO_ITEM` |
| 197 | Umbreon | Dark | 100 | 65 | 110 | 65 | 60 | 130 | 530 | `NO_ITEM`, `NO_ITEM` |
| 198 | Murkrow | Dark/Flying | 110 | 100 | 80 | 91 | 100 | 80 | 561 | `NO_ITEM`, `NO_ITEM` |
| 199 | Slowking | Water/Psychic | 95 | 75 | 80 | 30 | 120 | 110 | 510 | `NO_ITEM`, `KINGS_ROCK` |
| 200 | Misdreavus | Ghost | 80 | 120 | 80 | 85 | 70 | 85 | 520 | `NO_ITEM`, `SPELL_TAG` |
| 201 | Unown | Psychic | 148 | 102 | 48 | 48 | 102 | 48 | 496 | `NO_ITEM`, `NO_ITEM` |
| 202 | Wobbuffet | Psychic | 220 | 33 | 65 | 33 | 33 | 65 | 449 | `NO_ITEM`, `NO_ITEM` |
| 203 | Girafarig | Normal/Psychic | 70 | 80 | 65 | 112 | 90 | 65 | 482 | `NO_ITEM`, `NO_ITEM` |
| 204 | Pineco | Bug | 80 | 65 | 90 | 15 | 35 | 35 | 320 | `NO_ITEM`, `NO_ITEM` |
| 205 | Forretress | Bug/Steel | 90 | 90 | 140 | 40 | 60 | 80 | 500 | `NO_ITEM`, `NO_ITEM` |
| 206 | Dunsparce | Normal | 120 | 120 | 120 | 20 | 20 | 20 | 420 | `NO_ITEM`, `NO_ITEM` |
| 207 | Gligar | Ground/Flying | 85 | 95 | 125 | 85 | 35 | 65 | 490 | `NO_ITEM`, `NO_ITEM` |
| 208 | Steelix | Steel/Dragon | 100 | 100 | 200 | 30 | 55 | 40 | 525 | `NO_ITEM`, `METAL_COAT` |
| 209 | Snubbull | Normal | 60 | 80 | 50 | 30 | 40 | 40 | 300 | `NO_ITEM`, `NO_ITEM` |
| 210 | Granbull | Normal | 90 | 120 | 120 | 45 | 60 | 60 | 495 | `NO_ITEM`, `NO_ITEM` |
| 211 | Qwilfish | Water/Poison | 85 | 105 | 130 | 95 | 65 | 65 | 545 | `NO_ITEM`, `NO_ITEM` |
| 212 | Scizor | Bug/Steel | 70 | 130 | 120 | 65 | 55 | 80 | 520 | `NO_ITEM`, `NO_ITEM` |
| 213 | Shuckle | Bug/Rock | 60 | 10 | 230 | 5 | 10 | 230 | 545 | `BERRY`, `BERRY` |
| 214 | Heracross | Bug/Fighting | 80 | 125 | 75 | 105 | 40 | 95 | 520 | `NO_ITEM`, `NO_ITEM` |
| 215 | Sneasel | Dark/Ice | 95 | 115 | 55 | 120 | 100 | 75 | 560 | `NO_ITEM`, `QUICK_CLAW` |
| 216 | Teddiursa | Normal | 80 | 80 | 50 | 40 | 50 | 50 | 350 | `NO_ITEM`, `NO_ITEM` |
| 217 | Ursaring | Normal | 120 | 145 | 75 | 55 | 75 | 75 | 545 | `NO_ITEM`, `NO_ITEM` |
| 218 | Slugma | Fire | 40 | 40 | 40 | 20 | 90 | 40 | 270 | `NO_ITEM`, `NO_ITEM` |
| 219 | Magcargo | Fire/Rock | 80 | 100 | 120 | 30 | 100 | 80 | 510 | `NO_ITEM`, `NO_ITEM` |
| 220 | Swinub | Ice/Ground | 50 | 50 | 40 | 50 | 30 | 30 | 250 | `NO_ITEM`, `NO_ITEM` |
| 221 | Piloswine | Ice/Ground | 140 | 100 | 120 | 50 | 60 | 90 | 560 | `NO_ITEM`, `NO_ITEM` |
| 222 | Corsola | Water/Rock | 65 | 80 | 90 | 45 | 75 | 90 | 445 | `NO_ITEM`, `NO_ITEM` |
| 223 | Remoraid | Water | 35 | 65 | 35 | 65 | 65 | 35 | 300 | `NO_ITEM`, `NO_ITEM` |
| 224 | Octillery | Water | 75 | 105 | 75 | 80 | 105 | 75 | 515 | `NO_ITEM`, `NO_ITEM` |
| 225 | Delibird | Ice/Flying | 100 | 55 | 45 | 75 | 65 | 150 | 490 | `NO_ITEM`, `NO_ITEM` |
| 226 | Mantine | Water/Flying | 95 | 40 | 85 | 90 | 105 | 140 | 555 | `NO_ITEM`, `NO_ITEM` |
| 227 | Skarmory | Steel/Flying | 75 | 80 | 140 | 70 | 40 | 70 | 475 | `NO_ITEM`, `NO_ITEM` |
| 228 | Houndour | Dark/Fire | 45 | 60 | 30 | 65 | 80 | 50 | 330 | `NO_ITEM`, `NO_ITEM` |
| 229 | Houndoom | Dark/Fire | 100 | 90 | 50 | 115 | 130 | 80 | 565 | `NO_ITEM`, `NO_ITEM` |
| 230 | Kingdra | Water/Dragon | 95 | 95 | 95 | 85 | 105 | 95 | 570 | `NO_ITEM`, `DRAGON_SCALE` |
| 231 | Phanpy | Ground | 90 | 60 | 60 | 40 | 40 | 40 | 330 | `NO_ITEM`, `NO_ITEM` |
| 232 | Donphan | Ground | 110 | 120 | 120 | 50 | 60 | 60 | 520 | `NO_ITEM`, `NO_ITEM` |
| 233 | Porygon2 | Normal | 115 | 80 | 100 | 60 | 105 | 105 | 565 | `NO_ITEM`, `NO_ITEM` |
| 234 | Stantler | Normal | 73 | 115 | 62 | 85 | 85 | 65 | 485 | `NO_ITEM`, `NO_ITEM` |
| 235 | Smeargle | Normal | 90 | 45 | 75 | 110 | 45 | 75 | 440 | `NO_ITEM`, `NO_ITEM` |
| 236 | Tyrogue | Fighting | 35 | 35 | 35 | 35 | 35 | 35 | 210 | `NO_ITEM`, `NO_ITEM` |
| 237 | Hitmontop | Fighting | 110 | 85 | 95 | 70 | 35 | 110 | 505 | `NO_ITEM`, `NO_ITEM` |
| 238 | Smoochum | Ice/Psychic | 45 | 30 | 15 | 65 | 85 | 65 | 305 | `ICE_BERRY`, `ICE_BERRY` |
| 239 | Elekid | Electric | 45 | 63 | 37 | 95 | 65 | 55 | 360 | `NO_ITEM`, `NO_ITEM` |
| 240 | Magby | Fire | 45 | 75 | 37 | 83 | 70 | 55 | 365 | `BURNT_BERRY`, `BURNT_BERRY` |
| 241 | Miltank | Normal | 105 | 80 | 105 | 100 | 40 | 70 | 500 | `MOOMOO_MILK`, `MOOMOO_MILK` |
| 242 | Blissey | Normal | 255 | 10 | 10 | 55 | 135 | 135 | 600 | `NO_ITEM`, `LUCKY_EGG` |
| 243 | Raikou | Electric | 90 | 85 | 75 | 115 | 135 | 100 | 600 | `NO_ITEM`, `NO_ITEM` |
| 244 | Entei | Fire | 115 | 135 | 85 | 100 | 90 | 75 | 600 | `NO_ITEM`, `NO_ITEM` |
| 245 | Suicune | Water | 120 | 75 | 115 | 85 | 90 | 115 | 600 | `NO_ITEM`, `NO_ITEM` |
| 246 | Larvitar | Rock/Ground | 50 | 64 | 50 | 41 | 45 | 50 | 300 | `NO_ITEM`, `NO_ITEM` |
| 247 | Pupitar | Rock/Ground | 70 | 84 | 70 | 51 | 65 | 70 | 410 | `NO_ITEM`, `NO_ITEM` |
| 248 | Tyranitar | Rock/Dark | 100 | 134 | 110 | 61 | 95 | 140 | 640 | `NO_ITEM`, `NO_ITEM` |
| 249 | Lugia | Psychic/Flying | 116 | 100 | 140 | 120 | 100 | 164 | 740 | `NO_ITEM`, `NO_ITEM` |
| 250 | Ho Oh | Fire/Flying | 116 | 140 | 100 | 100 | 120 | 164 | 740 | `SACRED_ASH`, `SACRED_ASH` |
| 251 | Celebi | Psychic/Grass | 100 | 100 | 100 | 100 | 100 | 100 | 600 | `NO_ITEM`, `MIRACLEBERRY` |

## Learnsets, TMs, Trainers, And Boss AI Data

- Level-up moves and evolutions: `data/pokemon/evos_attacks.asm`.
- TM/HM move list: `data/moves/tmhm_moves.asm` and
  `constants/item_constants.asm`.
- Per-species TM/HM compatibility: each `data/pokemon/base_stats/*.asm` file.
- Trainer parties: `data/trainers/parties.asm`.
- Boss AI preference fixtures: `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`.
- Boss AI labels and teaching notes must use this reference when they mention
  weakness, resistance, immunity, physical/special category, stat stages, or
  move/item behavior.

## Fixture And Helper-Note Audit Rules

When editing fixtures, labels, or helper notes:

1. Never write `super-effective`, `resisted`, `immune`, `physical`, or
   `special` from memory. Check the tables above or the source files.
2. If a fixture is about battle judgment rather than mechanics, word the
   note that way. Example: Magnitude into Miltank is meaningful neutral
   damage, not super-effective Ground damage.
3. If a setup move changes a stat stage, describe the stage and the affected
   computed battle stat. Do not describe it as doubling base stats.
4. If a mechanics change touches any source listed in [Source Files To Trust]
   rerun this generator and update any helper note that paraphrases the rule.
5. Run `python tools/audit/check_mechanics_docs_and_fixtures.py` after fixture
   or helper-doc changes that mention mechanics.
