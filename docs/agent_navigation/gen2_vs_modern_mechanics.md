# Gen 2 vs Modern Mechanics — Anti-Drift Reference

Audience: future Codex/helper agents. Read this BEFORE making any
mechanics, balance, AI, moveset, item, or stat claim about this hack.

LLMs trained on internet Pokemon content carry a strong modern-Smogon-era
prior — per-move physical/special split, abilities, natures, Fairy type,
Gen 4+ moves, Choice/Focus Sash item meta, modern speed math. This hack is
Gen 2. Several of those modern assumptions silently produce wrong proposals
here. The most recent failure mode (2026-05-02): a +Atk Houndoom proposal
forgetting that in Gen 2 Dark is a Special-attacking type, so Crunch /
Pursuit / Bite all run off SpA — making +Atk dead weight on Houndoom.

This doc is the durable fix. Every numeric claim either points at the
source file/label that implements it, or is marked `(verify)` inline. If
the source says one thing and your training-data prior says another, the
source wins, and this doc must say so.

This hack is built on the pret/pokegold disassembly. It is Gen 2 plus a
hand-picked set of late-gen additions (Choice items, Assault Vest,
3-layer Spikes, contact flags, type-passive damage mods, Ditto Imposter,
15 type-chart tweaks). Every section below is laid out as
**Vanilla Gen 2** | **Modern (Gen 5+)** | **This hack**, where the
third column is what actually ships and is the one you must reason from.

The authoritative source for hack-specific deviations from vanilla Gen 2 is
`docs/mechanics_changes_from_base.md`. This doc is the *navigation*
reference — short rules with source-file pointers — not a replacement.

## 1. Physical / Special split — the single most-leaked rule

**Split is by attacking TYPE, not per-move.**

A move's offensive category is determined by the move's TYPE alone. Same
type → same offensive stat, every time, regardless of whether the move
"feels" punchy.

Source of truth: `constants/type_constants.asm`. Type constants are
ordered so that `PHYSICAL = 0` (NORMAL is 0) and `SPECIAL = 19` (FIRE is
19). The damage path classifies a move by comparing its type constant
against `SPECIAL`: type < SPECIAL → physical; type >= SPECIAL → special.
The runtime classifier is
`TypePassive_GetEffectiveMoveCategory_Far` in
`engine/battle/type_passive_damage_mods.asm`, called via the home thunk
`Battle_GetEffectiveMoveCategory` in `home/battle.asm`. The header
comment on that function calls out that the type-constant ordering is
load-bearing; reordering types silently misclassifies every move.

| Category | Types |
| --- | --- |
| Physical | NORMAL, FIGHTING, FLYING, POISON, GROUND, ROCK, BUG, GHOST, STEEL |
| Special  | FIRE, WATER, GRASS, ELECTRIC, PSYCHIC, ICE, DRAGON, DARK |

(The `BIRD` type constant exists but is unused; `CURSE_TYPE` is in the
gap between physical and special and is also unused.)

**Hack-specific exception (Outrage only).** Outrage stays Dragon-typed
but is dispatched as physical when the user's current Attack > current
Special Attack. Implemented inside the same
`TypePassive_GetEffectiveMoveCategory_Far` by returning `NORMAL` (any
physical-bucket type) instead of DRAGON when the condition fires. Ties
and non-Dragon users keep Outrage special. See
`docs/mechanics_changes_from_base.md` § 1.3 "Dragon-only Outrage
category exception".

### Concrete consequences for design (these are the failure modes)

- **DARK is special.** Crunch (DARK, BP 90), Pursuit (DARK, BP 40), Bite
  (DARK, BP 60), Faint Attack — all run off SpA. A pure-Dark mon gains
  nothing from +Atk. Houndoom (Dark/Fire) double-special STABs.
- **GHOST is physical.** Shadow Ball (GHOST, BP 80) runs off Atk. A
  Ghost ace wants Atk, not SpA, for its STAB. Same for Lick.
- **POISON is physical.** Sludge Bomb (POISON, BP 90) runs off Atk.
  Sludge, Poison Sting, Cross Poison (if present), Acid (POISON), all
  Atk-based.
- **GROUND is physical.** Earthquake, Magnitude, Mud-Slap (still SpA in
  modern, here Atk). Earth Power does not exist (Gen 4).
- **ROCK is physical.** Rock Slide, Ancient Power, Rock Throw — all Atk.
  AncientPower is one of the very few rare-typed special-feeling moves
  that is in fact physical.
- **BUG is physical.** Megahorn, Pin Missile — Atk. Bug Buzz / Signal
  Beam do not exist.
- **STEEL is physical.** Iron Tail, Steel Wing, Iron Head, Metal Claw —
  Atk. Flash Cannon does not exist.
- **FLYING is physical.** Drill Peck, Wing Attack, Sky Attack,
  Aeroblast — Atk. (Moves that "feel airy" like Twister still run off
  the type's category — Twister is Dragon, so special.)
- **FIGHTING is physical.** Cross Chop, Hi Jump Kick, Mach Punch,
  Submission, Reversal, Vital Throw — Atk. No Aura Sphere, no Focus
  Blast.
- **NORMAL is physical.** Hyper Beam, Tri Attack, Return, Frustration,
  Body Slam, Headbutt — Atk. (Yes, Hyper Beam is physical here.)
- **FIRE is special.** Flamethrower, Fire Blast, Sacred Fire, Flame
  Wheel, Fire Punch — SpA. (Fire Punch is FIRE, so SpA, even though it
  is animated as a punch.)
- **ICE is special.** Ice Beam, Blizzard, Ice Punch — SpA.
- **PSYCHIC is special.** Psychic, Confusion, Psybeam, Psywave — SpA.
- **DRAGON is special, with the Outrage exception above.** DragonBreath
  is special; Outrage is special by default and physical only for a
  Dragon user with Atk > SpA.

**Practical rule for ace/identity proposals.** Before recommending a
stat-bump-driven role (mixed attacker, physical breaker, etc.), look up
the species's STAB *types* and apply this table. A "let's make Houndoom
mixed" proposal is wrong here unless the species's coverage moves cross
the physical/special boundary by type — which Houndoom's actually
do (Dark + Fire are both special, so it has no native physical STAB).

## 2. Type chart

- **17 types.** No Fairy. No Fairy STAB, no Fairy weakness, no "Fairy
  resists Dark". Steel still resists Dark and Ghost (vanilla Gen 2, see
  the matchup table source below).

Source of truth: `data/types/type_matchups.asm`. Read that file directly
before asserting any matchup; do not work from training-data memory of
"the Gen 2 type chart". The Foresight-only matchups are the second
block, after the `db -2` sentinel.

**Boss AI / preference-labeling caution.** Do not turn a general "threat"
word into a false type claim. Example: Geodude's Magnitude is a real public
damage threat into Miltank if Miltank locks into low-value Rollout, but Ground
is **neutral** into Normal, not super-effective. The correct lesson is
"neutral but meaningful damage while locked into a bad first Rollout hit", not
"super-effective Ground risk". Always check `data/types/type_matchups.asm`
before using `super-effective`, `resists`, or `immune` in Boss AI reasoning.

**THIS HACK has 15 deliberate matchup tweaks** committed in
`daba6006` (`balance: 15 type-chart tweaks for restored uncertainty`).
The tweaks are not telegraphed in-game. List, with vanilla-Gen-2 →
this-hack values:

Defensive shifts:
- Ground → Ghost: 1× → 0× (Ghost intangible to earth)
- Water → Ice: 1× → 0.5× (water freezes into more ice)
- Ground → Fire: 2× → 1× (fires no longer fear earthquakes)
- Steel → Fighting: 1× → 0.5× (Fighting resists Steel)
- Rock → Psychic: 1× → 0.5× (Psychic resists Rock)
- Normal → Psychic: 1× → 0.5× (Psychic resists Normal)

Offensive shifts:
- Ghost → Steel: 0.5× → 0× (cold-iron banishes spirits)
- Ghost → Fighting: 1× → 2× (Ghost SE on Fighting)
- Poison → Normal: 1× → 2× (Snorlax answer)
- Dark → Steel: 0.5× → 1× (Dark hits Steel cleanly)
- Steel → Electric: 0.5× → 1× (Steel hits Electric cleanly)
- Grass → Flying: 0.5× → 1× (Flying no longer resists Grass)
- Fighting → Poison: 0.5× → 1× (fists work on poisonous things)
- Fighting → Bug: 0.5× → 1× (chitin doesn't stop a kick)
- Psychic → Poison: 2× → 1× (poisons no longer Psychic-fodder)

Foresight (`db -2` block in `data/types/type_matchups.asm`) is unchanged:
Foresight still removes Ghost's Normal/Fighting immunities. The new
Ground → Ghost immunity from this hack is NOT inside the Foresight block,
so Foresight does not lift it.

Boss AI reads the chart at runtime via the shared damage path; matchup
scoring auto-adapts. There are no hardcoded matchup assumptions in
`engine/battle/ai/` for the 15 edits.

## 3. Stats system: DVs, Stat Exp, no natures

- **DVs**, not IVs. Range 0..15 per stat (4 bits), not 0..31. Hidden
  Power type and BP are computed from DVs (see § 9).
- **Stat Exp** ("EVs"), per-stat 0..65535. Stat Exp contributes via
  `floor(sqrt(StatExp)) / 4` into the standard Gen 2 stat formula. No
  252/252/4 spread, no 510 cap, no Hyper Training.
- **No natures.** No nature-based ±10% stat shift. No `+Atk -SpA` etc.
- **No abilities.** Don't propose ability-based identities (Intimidate,
  Levitate, Lightning Rod, Sand Stream, Drought, etc.). Don't propose
  ability-as-identity for any species; the closest hack mechanism is the
  type-passive system (§ 14).

### Stat formulas (this hack uses vanilla Gen 2 formulas)

```
ComputedStat (non-HP) = floor((2*base + IV + EV/4) * level / 100) + 5
ComputedHP            = floor((2*base + IV + EV/4) * level / 100) + level + 10
```

(`EV/4` here is `floor(sqrt(StatExp)) / 4` — the IV/EV terminology in
this doc and CLAUDE.md tracks the Gen 2-flavored simplified formula. Do
not use Gen 3+ EVs.)

### Stat-stage multipliers (Gen 2)

| Stage | Multiplier | Stage | Multiplier |
| --- | --- | --- | --- |
| +1 | ×1.5 | -1 | ×0.66 |
| +2 | ×2.0 | -2 | ×0.5 |
| +3 | ×2.5 | -3 | ×0.4 |
| +4 | ×3.0 | -4 | ×0.33 |
| +5 | ×3.5 | -5 | ×0.28 |
| +6 | ×4.0 | -6 | ×0.25 |

Note: `wEnemySpdLevel` and friends use base-7 byte encoding —
`BASE_STAT_LEVEL = 7` is `+0`, `MAX_STAT_LEVEL = 13` is `+6`. **Do not
read the byte as the multiplier directly.**

**Trap:** the boost multiplies the +5 floor and the IV/EV contribution.
A low-base mon at +N can outpace a high-base mon at +0. Base 50 at +2
Speed beats base 100 at +0 Speed at level 50. See
[CLAUDE.md](../../CLAUDE.md) "Stat math" section for the worked example.

## 4. Critical hits

Source: `BattleCommand_Critical` in
`engine/battle/effect_commands.asm:1129` and the chance table at
`data/battle/critical_hit_chances.asm`.

- **Crit damage = 2×.** Not 1.5× (Gen 6+). See
  `engine/battle/effect_commands.asm:3009` `.CriticalMultiplier` —
  shifts the damage left once.
- **Crit chance is stage-based, not Speed-based.** All mons start at
  stage 0 (1/15 ≈ 6.7%). Stages stack from:
  - Focus Energy: +1
  - High-crit move (`data/moves/critical_hit_moves.asm`): +2
  - Stick on Farfetch'd: +2 (`engine/battle/effect_commands.asm:1161`)
  - Lucky Punch on Chansey: +2 (`engine/battle/effect_commands.asm:1151`)
  - Scope Lens (`HELD_CRITICAL_UP`): +1
  - Stages cap at 6.

Chance table (`data/battle/critical_hit_chances.asm`):

| Stage | Chance |
| --- | --- |
| 0 | 1/15 (~6.7%) |
| +1 | 1/8  (12.5%) |
| +2 | 1/4  (25%) |
| +3 | 1/3  (~33%) |
| +4 | 1/2  (50%) |
| +5 | 1/2  (50%) |
| +6 | 1/2  (50%) |

This is *not* the vanilla Gen 1 / vanilla Gen 2 base-Speed formula
(`baseSpeed/512`). The actual Gen 2 mechanic in this codebase is the
stage table above — the disassembly shipped with the stage-based table.
Do not assert "high base Speed → high crit" here.

- **Crits ignore unfavorable stat changes.** Verified: see
  `CheckDamageStatsCritical` (`engine/battle/effect_commands.asm:2619`)
  and `CheckDamageStatsCritical_Far` for the rule. The crit path uses
  unboosted stats only when the opponent's defense stage > user's
  attack stage; this is the vanilla Gen 2 rule, not the modern "ignore
  all defender's positive boosts and all attacker's negative boosts"
  rule. Match the source comment: "Unboosted stats should be used if
  the attack is a critical hit, AND the stage of the opponent's defense
  is higher than the user's attack." `(verify exact predicate when
  designing around it.)`

## 5. Status conditions

### Burn

- 1/2 Atk multiplier on physical damage. Hack-tuned by Fighting type:
  see `ApplyBrnEffectOnAttack_Far`
  (`engine/battle/type_passive_damage_mods.asm:865`):
  - Baseline: ×1/2
  - Half Fighting: ×5/8
  - Full Fighting: ×3/4
- Residual damage = `maxHP/8` per turn. See
  `ResidualDamage` and `GetEighthMaxHP` callsite in
  `engine/battle/core.asm:1085`. (Vanilla Gen 2 = 1/8; modern Gen 7+
  changed to 1/16; this hack is 1/8.)
- Burn pseudo-ignores Fire-types — see `BattleCommand_BurnTarget`
  (`engine/battle/effect_commands.asm:3798`) which calls
  `CheckMoveTypeMatchesTarget` to skip burning a Fire-type with a
  Fire-typed move. This is the standard Gen 2 STAB-status check.

### Paralysis

- 25% full-paralyze baseline. Hack-tuned by Fighting type:
  `TypePassive_GetUserParalysisFailThreshold_Far`
  (`engine/battle/type_passive_damage_mods.asm:790`):
  - Baseline: 25%
  - Half Fighting: 20%
  - Full Fighting: 15%
- Speed cut to 1/4 baseline. Hack-tuned by Fighting type:
  `ApplyPrzEffectOnSpeed_Far`
  (`engine/battle/type_passive_damage_mods.asm:803`):
  - Baseline: ×1/4
  - Half Fighting: ×3/8
  - Full Fighting: ×1/2

  (Gen 7+ uses ×1/2 baseline; this hack is ×1/4 baseline.)
- Electric type half/full bumps Speed by 41/40 or 21/20 in the same
  routine; Electric mons are slightly faster baseline.
- Cannot paralyze Electric-types (vanilla rule).

### Sleep

- Duration is rolled at apply time:
  `BattleCommand_SleepTarget` (`engine/battle/effect_commands.asm:3455`,
  loop at `:3494`) rerolls until the random byte is in `1..6` (excludes
  0 and 7), then `inc a` stores `2..7`. Counter ticks down each turn.
  In practice that's 1..6 turns asleep before the wake-up turn, which
  matches vanilla Gen 2.
- `SLP_MASK = %111` (`constants/battle_constants.asm:221`). The status
  byte's low 3 bits are the sleep counter; non-zero means asleep.
- Sleep Talk and Snore exist (Gen 2 stock). Rest sleeps for
  `REST_SLEEP_TURNS + 1` turns, then heals (see
  `engine/battle/effect_commands.asm:5933`).

### Freeze

- Frozen mon cannot move. Thaw conditions:
  - User uses `FLAME_WHEEL` or `SACRED_FIRE` — sets thaw on use, see
    `engine/battle/effect_commands.asm:209-213`.
  - Hit by a Fire-type damaging move — thaw set in
    `engine/battle/effect_commands.asm:6180-6197` (the post-damage
    freeze-clear path).
- **No 20%-per-turn random thaw chance.** Vanilla Gen 2 behavior — you
  stay frozen until something melts you.

### Confusion

- Self-hit chance: 50% per turn while confused
  (`engine/battle/effect_commands.asm:275-285`).
- Self-hit damage: 40 BP, typeless — see
  `engine/battle/effect_commands.asm:2779` (`ld d, 40`) routed through
  `ConfusionDamageCalc` with `wIsConfusionDamage` set so the type
  effectiveness branch is bypassed.
- Confusion turns: 1..4 (`(BattleRandom & 3) + 1` style; verify exact
  range in `BattleCommand_Confuse`,
  `engine/battle/effect_commands.asm:5618`). `(verify count)`

### Toxic (badly poisoned)

- Counter increments each turn; damage = `(maxHP/16) * counter`. See
  `ResidualDamage` (`engine/battle/core.asm:1093-1107`) — `GetSixteenthMaxHP`
  scaled by the toxic count.
- `wPlayerToxicCount` / `wEnemyToxicCount` reset on switch out
  (vanilla rule — this hack does not Gen 5+ "preserves on switch").

## 6. Substitute

- Sub HP = `floor(maxHP / 4)`. See
  `BattleCommand_Substitute`
  (`engine/battle/move_effects/substitute.asm:17-24`) — two right-shifts
  on the maxHP word, no `+1`. (Some references say "Gen 1 was +1, Gen 2
  is /4 floored"; this hack matches the floored variant.)
- User's HP is reduced by sub HP at creation. If `currentHP - subHP <=
  0`, sub fails ("too weak to make a substitute").
- Sub blocks status moves, indirect damage triggers,
  secondary-effect status, crits against the holder, stat drops on the
  holder, and Toxic counter advancement. Standard Gen 2 sub semantics.
- **No Gen 6+ Sound-move bypass** — verified by absence; no Sound-flag
  check on `DoSubstituteDamage` (`engine/battle/effect_commands.asm:3382`).
- **Hack-specific (commit `65c5296f`):** contact-trigger passives now
  correctly skip when the contact landed on a Substitute. The two
  affected paths are `TypePassive_MaybePoisonRetaliation_Far` (Poison
  defender's contact-poison passive) and the Rocky Helmet recoil branch
  in `HandleLateGenAfterHitEffects_Far`. Do not assume contact effects
  fire through Sub.

## 7. Held items

Three groups. Always state which group when proposing an item-based
identity.

### Group A — vanilla Gen 2 items, still functional in this hack

- **Leftovers**: 1/16 maxHP per turn.
- **Berry / Gold Berry / PSNCureBerry / PRZCureBerry / Mint Berry /
  Burnt Berry / Ice Berry / Bitter Berry / Mysteryberry / MiracleBerry
  / Berry Juice**: ONE-SHOT consumables, cleared on use. NOT Gen 4+
  residual berries. List in `constants/item_constants.asm:81-96` and
  surrounding.
- **Stick** (held by Farfetch'd): +2 crit stages.
- **Lucky Punch** (held by Chansey): +2 crit stages.
- **Light Ball** (held by Pikachu): doubles Pikachu's **SpA only**, not
  Atk. Verified via `LightBallBoost`
  (`engine/battle/effect_commands.asm:2643`), called only from the
  `.special` branch of player attack damage calc
  (`engine/battle/effect_commands.asm:2565`). The `SpeciesItemBoost_Far`
  it calls (`engine/battle/late_gen_held_items.asm:555`) doubles the
  stat at `hl`, and at the call site `hl` is `wPlayerSpAtk`. **This is
  the vanilla Gen 2 behavior, not the Gen 4+ behavior of doubling both
  Atk and SpA.** A "Light Ball Pikachu mixed attacker" frame is wrong
  here.
- **Thick Club** (held by Cubone/Marowak): doubles Atk.
- **Quick Claw**: ~23% chance to act first regardless of Speed (60/256
  threshold against `BattleRandom`, see `engine/battle/core.asm:486-503`).
- **Scope Lens**: +1 crit stage.
- **King's Rock**: hack-modified — flinch on hit now requires CONTACT
  (`docs/mechanics_changes_from_base.md` § 1.1). Vanilla had no contact
  gate.
- **Type-boost held items**: SilverPowder, Charcoal, Mystic Water,
  Miracle Seed, NeverMeltIce, Magnet, TwistedSpoon, Hard Stone, Sharp
  Beak, Poison Barb, Soft Sand, Black Belt, Blackglasses, Spell Tag,
  Polkadot Bow, Pink Bow. All shift to **×1.2 (was ×1.1)** in this hack
  via the `HELD_TYPE_BOOST` parameter bump (`docs/mechanics_changes_from_base.md`
  § 1.7). Dragon Fang and Dragon Scale both now boost Dragon
  damage (Dragon Fang was bugged in vanilla).
- **Focus Band**: 1/16 chance to survive at 1 HP (vanilla rule).
- **Berserk Gene**: +2 Attack but inflicts confusion on activation
  (vanilla Gen 2 mechanic; verify exact behavior at use site if
  designing around it).

### Group B — modern items added by THIS HACK

Source: `engine/battle/late_gen_held_items.asm` and
`docs/mechanics_changes_from_base.md` § 1.2. Constant definitions in
`constants/item_constants.asm`.

- **Life Orb** (`LIFE_ORB`): damage ×13/10 (1.3×); recoil = `maxHP/10`,
  min 1.
- **Choice Band** (`CHOICE_BAND`): physical attack ×3/2 (1.5×);
  move-locks user to first selected move until reset.
- **Choice Specs** (`CHOICE_SPECS`): special attack ×3/2; move-locks.
- **Choice Scarf** (`CHOICE_SCARF`): turn-order Speed ×3/2;
  move-locks.
- **Assault Vest** (`ASSAULT_VEST`): holder's SpDef ×3/2 vs incoming
  special damage; blocks non-damaging move selection (with explicit
  exceptions in code). If no legal move remains, forces `STRUGGLE`.
- **Expert Belt** (`EXPERT_BELT`): super-effective damage ×6/5 (1.2×).
- **Muscle Band** (`MUSCLE_BAND`): physical damage ×11/10 (1.1×).
- **Wise Glasses** (`WISE_GLASSES`): special damage ×11/10.
- **Eviolite** (constant spelled `EVOLITE`): Def and SpDef ×3/2 if
  species can evolve.
- **Air Balloon** (`AIR_BALLOON`): Ground attacks become no-effect
  against holder; pops on direct damage hit.
- **Shell Bell** (`SHELL_BELL`): heal `floor(damage/8)` per hit, min 1.
- **Rocky Helmet** (`ROCKY_HELMET`): contact attacker takes `maxHP/6`
  (min 1). Now correctly Sub-gated as of `65c5296f`.
- **Metronome** (held item, `METRONOME_ITEM`): repeated same damaging
  move stacks ×(10 + 2*count)/10, capped at ×2.0. Resets on move
  change, non-damaging move, switch, or losing the item.

Choice / Vest move-lock state lives in WRAM (`wPlayerChoice*`,
`wMetronomeCount` etc.) and is reset on battle start and on switch.
Player-side enforcement is in the move-selection menu; enemy-side
enforcement is at action-parse time.

### Group C — modern items that DO NOT exist in this hack

Verified by absence in `constants/item_constants.asm`:

- **Focus Sash** — does not exist. Don't suggest "OHKO survivor" item
  identities.
- **Toxic Orb / Flame Orb** — do not exist. No self-status pivot
  setups.
- **Heat Rock / Damp Rock / Smooth Rock / Icy Rock** — do not exist.
  Weather is fixed at 5 turns from a setup move (§ 11).
- **White Herb / Mental Herb / Power Herb** — do not exist.
- **Wide Lens / Zoom Lens** — do not exist.
- **Black Sludge** — does not exist.
- **Safety Goggles** — does not exist.
- **Big Root** — does not exist.
- **Mega Stones, Z-Crystals, Tera Shards** — entire mechanic absent
  (§ 16).

### Practical rule for item-based identity proposals

Look up the item constant in `constants/item_constants.asm`. If it's
not there, the item doesn't exist. If it is, check
`engine/battle/late_gen_held_items.asm` for the actual multiplier
shipping in this hack, and `docs/mechanics_changes_from_base.md` § 1.2
for the cross-summary.

## 8. Moves that don't exist in this hack

Verified by reading `constants/move_constants.asm` (move IDs 0..0xfe;
`NUM_ATTACKS` is `const_value - 1`). Moves a modern-trained model will
reach for and be wrong:

- **Sucker Punch** (Gen 4) — absent.
- **Knock Off** (Gen 3) — absent.
- **U-turn / Volt Switch / Flip Turn / Parting Shot** (Gen 4+) —
  absent.
- **Roost** (Gen 4) — absent.
- **Stealth Rock / Sticky Web / Toxic Spikes** (Gen 4+) — absent.
  Spikes is the only entry hazard.
- **Trick Room** (Gen 4) — absent.
- **Tailwind** (Gen 4) — absent.
- **Bulk Up / Nasty Plot / Calm Mind variations** — Calm Mind IS
  present (`CALM_MIND`, ID `fd`); Bulk Up and Nasty Plot are absent.
- **Close Combat** (Gen 4) — absent.
- **Earth Power / Flash Cannon / Dark Pulse / Aura Sphere /
  Air Slash** (Gen 4) — absent.
- **Bullet Punch / Ice Shard / Shadow Sneak / Aqua Jet** (Gen 4+
  priority) — absent. Priority moves in this hack are Quick Attack
  (+1, NORMAL), Mach Punch (+1, FIGHTING), and Extreme Speed
  (`EXTREMESPEED`, +2 Gen 2 priority, NORMAL).
- **Fairy moves** (Moonblast, Dazzling Gleam, Play Rough) — absent;
  no Fairy type.
- **Fake Out** — absent.
- **Will-O-Wisp** — absent. Burn is delivered via fire-typed damaging
  moves with burn chance, or via specific status effects.

### Moves that DO exist in this hack but are post-Gen 2 in vanilla

- **Dragon Dance** (`DRAGON_DANCE`, ID `fc`): +1 Atk / +1 Spe.
- **Calm Mind** (`CALM_MIND`, ID `fd`): +1 SpA / +1 SpD `(verify exact
  effect bytes via data/moves/moves.asm and the EFFECT_CALM_MIND
  handler)`.
- **Quiver Dance** (`QUIVER_DANCE`, ID `fe`): +1 SpA / +1 SpD / +1 Spe.
  Gen 5 in vanilla.
- **Iron Head** (`IRON_HEAD`, ID `01`): replaces vanilla Pound at
  index 01.

For any move-presence question, the authoritative file is
`constants/move_constants.asm`. The full move data table is
`data/moves/moves.asm`.

## 9. Move mechanics that differ from modern

- **Counter**: blocks PHYSICAL-typed attacks only. Implementation in
  `engine/battle/move_effects/counter.asm:33-36` calls
  `Battle_GetLastCounterMoveCategory` (`home/battle.asm:263`) and exits
  early when category is special (a >= SPECIAL).
- **Mirror Coat**: blocks SPECIAL-typed attacks only.
  `engine/battle/move_effects/mirror_coat.asm:34-36`. Symmetric to
  Counter. Both also apply the Outrage exception (Outrage will be
  Counterable when its user runs it physically).
- **Hidden Power**: type AND base power computed from DVs. Source:
  `engine/battle/hidden_power.asm`. BP range is **31..70** (the formula
  is `floor((5*N + Spc&3) / 2) + 31` where N is the 4-bit MSB-of-each-DV
  composite). Type is computed from `(Atk DV & 3) << 2 | (Def DV & 3)`,
  with Normal and Bird and unused types skipped. Modern Hidden Power is
  fixed BP 60/70; this hack uses the Gen 2 variable BP.
- **Pursuit**: doubles BP on switching target.
  `engine/battle/move_effects/pursuit.asm` — checks
  `wEnemyIsSwitching` / `wPlayerIsSwitching` and `sla` the damage word.
- **Encore**: locks target into last move for `(BattleRandom & 3) + 3`
  turns = **3..6 turns**. `engine/battle/move_effects/encore.asm:40-45`.
  (Plan referenced "3..7" — source is 3..6.)
- **Outrage**: 100 BP, DRAGON, 100% acc, 15 PP per
  `data/moves/moves.asm:216`. Always read `data/moves/moves.asm` directly
  before quoting BP. Outrage rampage is 2-3 turns then confuse, vanilla
  mechanic.

- **Earthquake / Magnitude / Fissure** all hit Dig users
  (`engine/battle/effect_commands.asm:1735-1740, 1789-1798`). Gust and
  Twister and Whirlwind and Thunder hit Fly users
  (`engine/battle/effect_commands.asm:1780-1787`). EQ damage doubles
  vs Dig users `(verify the damage doubling — confirmed only that
  EQ/Magnitude/Fissure connect; spot-check the 2x multiplier in the
  Dig effect handler if designing around it)`.
- **Recovery moves**:
  - **Recover / Soft-Boiled / Milk Drink / Slack Off**: 50% maxHP via
    `BattleCommand_Heal` (`engine/battle/effect_commands.asm:5897`).
  - **Rest**: full HP + sleep `REST_SLEEP_TURNS + 1`.
  - **Synthesis / Morning Sun / Moonlight**:
    `BattleCommand_TimeBasedHealContinue`
    (`engine/battle/effect_commands.asm:6275-6367`). Heal index is
    derived from time-of-day match AND weather:
    - Time match + clear: 1/2 maxHP
    - Time match + sun: full HP
    - Time match + rain or sandstorm: 1/4 maxHP
    - Time mismatch + clear: 1/4 maxHP
    - Time mismatch + sun: 1/2 maxHP
    - Time mismatch + rain or sandstorm: 1/8 maxHP

    Multiplier table at `engine/battle/effect_commands.asm:6363`. The
    plan's "50% / 25% / 100%" version of these is correct only for
    matching time of day; mismatched time halves it.
- **Selfdestruct / Explosion**: halve target Defense in damage calc
  (`engine/battle/effect_commands.asm:2795-2800`). User faints on use.
- **High-crit moves**: see `data/moves/critical_hit_moves.asm` for the
  list (Slash, Crabhammer, Karate Chop, Razor Leaf, etc.) — +2 crit
  stages each.

## 10. Damage formula

Damage step in this hack matches vanilla Gen 2 with the late-gen item
multiplier strip layered in. `BattleCommand_DamageCalc` is at
`engine/battle/effect_commands.asm:2786`; the multi-stage pipeline runs
through `ApplyLateGenDamageMultipliers_Far` for held items and the
type-passive system, then `.CriticalMultiplier`, then
`BattleCommand_DamageVariation`.

Conceptual formula (Gen 2 style):

```
Damage = (((2 * Level / 5 + 2) * BP * Atk / Def) / 50) + 2
       * STAB   (×1.5 if attacker shares the move's type)
       * TypeEffectiveness  (×0, ×0.5, ×1, ×2; multi-type stacks by
                             chained matchup db entries)
       * RandomFactor       (×0.85..×1.00, see below)
       * ItemBoosts         (Group A & B held items; see § 7)
       * TypePassives       (this hack; see § 14)
       * Crit               (×2 if crit, see § 4)
```

- **STAB**: ×1.5. (Gen 6+ added Adaptability ×2; absent here, no
  abilities.)
- **Type effectiveness**: 0× / 0.5× / 1× / 2×. NOT ×0.625 for "not very
  effective" or anything modern. Multi-type targets stack matchups
  multiplicatively by repeated table entries.
- **Random factor**: `~0.85 .. ~1.00` (`BattleCommand_DamageVariation`
  at `engine/battle/effect_commands.asm:1550`). The implementation
  rejects random bytes < `85 percent + 1` after `rrca`, then divides by
  `100 percent`. This is the vanilla Gen 2 distribution — biased toward
  the high end (lowest values rejected by the loop). The 217..255/255
  range commonly cited for Gen 2 corresponds to this 85%..100%
  distribution.
- **Damage cap**: `999` per hit (`MAX_DAMAGE EQU 999`,
  `engine/battle/effect_commands.asm:2927`).
- **Min damage**: `2` (`MIN_DAMAGE EQU 2`,
  `engine/battle/effect_commands.asm:2928`).

Late-gen item / type-passive insertion points relative to vanilla Gen 2:

- Item multipliers via `ApplyLateGenDamageMultipliers_Far`
  (`engine/battle/effect_commands.asm:2920`) — runs after STAB+type
  steps and before crit.
- Type passives (Outrage category swap, Bug/Water/Ground/Rock defender
  reductions, Fire-attacker-low-HP boost, Ghost-vs-statused, etc.) live
  alongside that step in
  `engine/battle/type_passive_damage_mods.asm`.
- See `docs/mechanics_changes_from_base.md` § 1.3 for the full table of
  passive multipliers.

## 11. Weather

Source: `engine/battle/move_effects/rain_dance.asm`,
`engine/battle/move_effects/sunny_day.asm`, and
`engine/battle/move_effects/sandstorm.asm`.

- **Three weather effects:** Sunny Day, Rain Dance, Sandstorm. **NO
  Hail.** **NO weather-summoning abilities** (no abilities at all).
- **Sun:** Fire damage ×1.5, Water damage ×0.5, SolarBeam no charge,
  Synthesis-family heal up (§ 9), Thunder accuracy down `(verify)`.
- **Rain:** Water ×1.5, Fire ×0.5, Thunder bypasses accuracy check
  (`engine/battle/effect_commands.asm:1800-1809` `.ThunderRain`),
  Synthesis-family heal halved.
- **Sandstorm:** chip damage to non-Rock/Ground/Steel; Rock SpD ×1.5
  `(verify exact multipliers in HandleWeather)`.
- **Duration:** all weather lasts **5 turns** flat. `wWeatherCount` is
  set to `5` by all three setup moves (e.g.
  `engine/battle/move_effects/rain_dance.asm:4-5`). No Heat Rock /
  Damp Rock / Smooth Rock — no extension items exist (§ 7C).

## 12. Entry hazards

Source: `engine/battle/core.asm:3977` `SpikesDamage` and
`engine/battle/move_effects/spikes.asm`.

- **Spikes is the ONLY hazard** in this hack.
- **3 layers** (hack feature, see `docs/mechanics_changes_from_base.md`
  § 1.4). Vanilla Gen 2 was 1 layer.
- **Damage on switch-in:**
  - 1 layer: maxHP/8
  - 2 layers: maxHP/6
  - 3 layers: maxHP/4
- **Flying-types are unaffected** (`engine/battle/core.asm:3993-4000`).
  No "Levitate ability" — only the Flying type is checked.
- **Rapid Spin** clears all Spikes layers; AI redundancy and scoring
  are layer-aware (see `docs/mechanics_changes_from_base.md` § 1.4).
- **Stealth Rock, Sticky Web, Toxic Spikes:** none exist.

## 13. Speed and turn order

Source: `engine/battle/core.asm` around `:475-540` (priority-tied
turn-order resolution).

- **Speed ties** are resolved by coin flip *after* both selections are
  visible. No "always slower / always faster" tie rules.
- **Quick Claw** is the only "ignore Speed" held effect: 60/256 ≈
  23.4% trigger chance against `BattleRandom`
  (`engine/battle/core.asm:486-503`). Both-have-Quick-Claw is
  re-rolled in a side-stable order.
- **Choice Scarf** Speed ×3/2 is hack-added (Group B above), applied
  to the turn-order Speed only.
- **Priority moves** in this hack (from `data/moves/moves.asm`):
  - Quick Attack: +1, NORMAL, BP 40
  - Mach Punch: +1, FIGHTING, BP 40
  - Extreme Speed (`EXTREMESPEED`): Gen 2 priority `+2` `(verify
    against EFFECT_PRIORITY_HIT handling — Extreme Speed in vanilla
    Gen 2 is +1; some references say +2 for Gen 5+ retconning)`. The
    move slot is in `data/moves/moves.asm`; the effect is
    `EFFECT_PRIORITY_HIT` shared with Quick Attack and Mach Punch, so
    likely +1.
- **Priority below 0** (Counter / Mirror Coat / Roar / Whirlwind):
  vanilla Gen 2 doesn't formalize these as numeric priorities; they
  are special-cased in turn-order code. Don't claim "priority -6 like
  modern Roar".

### Speed-affecting moves in this hack

- `AGILITY` (+2 Spe) is the ONLY single-stat +Speed move in this hack.
- `DRAGON_DANCE` = +1 Atk, +1 Spe combo.
- `QUIVER_DANCE` = +1 SpA, +1 SpD, +1 Spe combo.
- A "no Agility" rule is equivalent to "no single-stat +Speed move"
  here.

(Boss AI Speed-stage cap by base Speed band is a separate rule: see
[CLAUDE.md](../../CLAUDE.md) "Boss AI Speed-cap rule" and
`engine/battle/ai/boss_policy_switch.asm` `.check_speed`. ≥90 base = +1 cap, 60-89
= +2, ≤59 = +3.)

## 14. Type passive system (HACK-SPECIFIC, no vanilla analog)

This is the closest mechanic to "abilities" in this hack — but it is
NOT abilities. Effects are baked into types and apply to every member
of that type. Source: `engine/battle/type_passive_damage_mods.asm` and
`docs/mechanics_changes_from_base.md` § 1.3.

Half/Full distinction: a mon with the type as one of its two slots
gets the Half tier; a pure-type mon (both slots same) gets the Full
tier.

Damage-side passives, abridged (full table in mechanics_changes_from_base.md):

- **Normal STAB** enhancer (×31/30 half, ×16/15 full → final STAB ~1.55× / ~1.60×).
- **Fire** attacker below 1/3 HP: ×11/10 half, ×6/5 full damage.
- **Ghost** attacker vs statused defender: ×21/20 half, ×11/10 full.
- **Dragon** attacker — "Dragon's Majesty": treats type-chart immunities
  as resistances (×0 → ×0.5) for damaging non-fixed-damage moves.
- **Dragon** defender — "Imperial Scales": non-super-effective hits
  reduced ×2/3 half, ×1/2 full.
- **Ground** defender vs SE hit: ×19/20 half, ×9/10 full reduction.
- **Rock** defender vs crit: ×19/20 half, ×9/10 full reduction.
- **Bug** defender vs physical category: ×19/20 half, ×9/10 full
  reduction.
- **Water** defender vs special category: ×39/40 half, ×19/20 full
  reduction.
- **Ice** defender above half HP: ×39/40 half, ×19/20 full reduction.

Status-side / utility passives, abridged:

- **Electric** speed: ×41/40 half, ×21/20 full.
- **Fighting** tunes paralysis (less speed cut, less full-paralyze)
  and burn (less Atk cut). See § 5 for exact numbers.
- **Flying** accuracy bonus: ×26/25 half, ×27/25 full.
- **Dark** status shield: half = 50% negate first incoming status, full
  = 100%; consumes one per active mon (`wPlayerDarkShieldConsumed`,
  `wEnemyDarkShieldConsumed`).
- **Psychic** mind shield: 6/256 (half) or 13/256 (full) chance to set
  incoming damage to 0 (hit still proceeds for hit-flow).
- **Poison** retaliation: on contact damaging hit, 10% (half) or 20%
  (full) to poison the attacker. Now correctly Sub-gated (commit
  `65c5296f`).
- **Steel** recoil mitigation on recoil moves: ×1/2 (half) or ×0
  (full).
- **Grass** end-of-turn regrowth: maxHP/64 (half) or maxHP/32 (full)
  if not statused and not full HP.

This system is the design lever that gives "weak" defensive types a
distinct identity. When you find yourself reaching for an ability to
explain a buff, look at whether the type passive already provides it.

## 15. What does NOT exist at all

Reasoning from any of these is automatically wrong:

- **Abilities.** No Intimidate, Levitate, Lightning Rod, Sand Stream,
  Drought, Drizzle, Sturdy, Rough Skin, Static, Multiscale, etc.
  Closest analog: type passives (§ 14).
- **Natures.** No nature-based ±10% stat shift.
- **Fairy type.** No Fairy STAB, no Fairy weakness, no resistances
  derived from Fairy.
- **Mega Evolution, Z-Moves, Dynamax/Gigantamax, Terastallization.**
- **Hyper Training / Bottle Caps.** DVs are immutable.
- **EV training items / power items / Macho Brace.** Stat Exp is the
  Gen 2 system.
- **Per-move physical/special split.** See § 1 — by type only.
- **Per-turn random freeze thaw.** § 5.
- **Rest-talk speed boosters as items** (no Heat Rock etc., § 7C).

## 16. Hack-specific deviations summary (cross-link)

Quick reference. The authoritative table is
`docs/mechanics_changes_from_base.md`. If you need to design or argue
about a deviation, read that file.

| Area | Hack deviation | This-doc § | Source |
| --- | --- | --- | --- |
| Type chart | 15 matchup tweaks (see § 2 list) | § 2 | `data/types/type_matchups.asm` |
| Held items | Late-gen items added (Group B) | § 7 | `engine/battle/late_gen_held_items.asm` |
| Held items | Type-boost items ×1.1 → ×1.2 | § 7 | `data/items/attributes.asm` (`HELD_TYPE_BOOST` value) |
| Type passives | Whole new system (§ 14) | § 14 | `engine/battle/type_passive_damage_mods.asm` |
| Contact flags | Per-move table; Rocky Helmet / poison retaliation gated | § 6, § 7B | `data/moves/contact_flags.asm`, `engine/battle/effect_commands.asm` |
| Spikes | 3 layers (was 1); Rapid Spin clears all | § 12 | `engine/battle/move_effects/spikes.asm` |
| Ditto | Auto-Transform on switch-in | (see mechanics doc) | `engine/battle/effect_commands.asm` |
| Dragon Fang | Now actually boosts Dragon damage | § 7 | `data/types/type_boost_items.asm` |
| Outrage | DRAGON physical when user's Atk > SpA | § 1, § 9 | `engine/battle/type_passive_damage_mods.asm` |
| Burn / paralysis | Fighting-type-tuned penalties | § 5 | `engine/battle/type_passive_damage_mods.asm` |
| Trainer battles | Pack disabled; Set forced; AI bag use disabled | (see mechanics doc) | `engine/battle/menu.asm`, `engine/battle/core.asm` |
| Boss AI | Tiered, weighted, public-info-only | (see boss spec) | `engine/battle/ai/`, `docs/boss_ai_spec.md` |
| Sub vs contact | Contact passives skip when Sub absorbed (commit `65c5296f`) | § 6 | `engine/battle/type_passive_damage_mods.asm` |

For any of these, the rule is the same: **read the source**, not your
training-data memory. If you find a place where this doc disagrees with
source, update this doc; do not work around it.

## Verification protocol

Every numeric or rule claim in this doc either cites a source label
(`engine/.../foo.asm:NNN`) or is marked `(verify)` inline. When you
extend or update this doc:

1. If the claim is about a battle mechanic in this hack, find and cite
   the source label that implements it.
2. If the source disagrees with the modern-mechanics prior, the source
   wins, and the doc must say so explicitly.
3. If the claim cannot be verified within reasonable effort, mark it
   `(verify)` rather than asserting confidently.

This is the same standard the project applies to all design docs:
"trust source/linker truth and update the helper doc"
(`docs/README.md`).
