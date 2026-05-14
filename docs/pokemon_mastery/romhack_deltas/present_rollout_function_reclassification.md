# Romhack Delta: Present, Rollout, And Function Reclassification

Status: source-verified from local assembly and damage-debugger checked for the
Whitney Rollout anchor. Not yet runtime-fixture verified in an emulator trace.

Scope: Pokemon Gold romhack / Gym Leader Lab. Do not use this as a vanilla GSC
or Pokemon Showdown Present claim.

## Source Evidence

- `data/moves/moves.asm`: `PRESENT` is Normal, 90 accuracy, 15 PP,
  `EFFECT_PRESENT`, fixed-effect data.
- `engine/battle/move_effects/present.asm`: Present checks immunity and miss
  first, then chooses damage or healing from `PresentPower`.
- `data/moves/present_power.asm`: Present has 40% 40 BP, 30% 80 BP, 10% 120
  BP, and 20% target-heal branches.
- `data/moves/moves.asm`: `ROLLOUT` is Rock, physical, 30 BP, 90 accuracy, 20
  PP, `EFFECT_ROLLOUT`.
- `engine/battle/move_effects/rollout.asm`: Rollout repeats through the
  Rollout substatus, increments its count on hit, resets the lock on miss, and
  doubles damage for each successful hit after the first.
- `engine/battle/effect_commands.asm`: `BattleCommand_Curl` sets
  `SUBSTATUS_CURLED`; Rollout checks that flag and adds one extra doubling
  step.
- `engine/battle/effect_commands.asm`: `BattleCommand_ResetStats` sets both
  players' stat stages back to base and recalculates both sides' stats.
- `engine/battle/ai/boss_policy_move.asm`: boss anti-setup avoidance checks
  the active player's public used-move effects, not the hidden player team.
- `data/trainers/parties.asm`: Whitney Miltank has Milk Drink / Body Slam /
  Rollout / Attract.
- `data/pokemon/evos_attacks.asm`: Delibird learns Present at level 1 and Haze
  at level 42.
- `data/trainers/parties.asm`: Pokefan Colin's level 32 Delibird has an item
  entry but no explicit move list.

## Verified Facts

Local Present is not safe to import from Pokemon Showdown replay damage. The
local source path selects one of three base powers or heals the target. This
source check did not find a local Present damage path that applies the
Showdown/GSC Present glitch's type-index damage variables.

Present is currently a Delibird relevance check, not a known Gym Leader Lab
boss route. The source has Delibird learn Present, but the level 32 Colin
trainer entry does not explicitly list moves. Before writing practical advice
for that fight, validate the generated four-move trainer set and runtime move
behavior.

Rollout is a confirmed Whitney boss route. It is a lock/ramp move, and Defense
Curl doubles the effective sequence by adding one doubling step. A miss ends
the Rollout lock.

Haze is a confirmed full stat-reset route. It resets both sides' stat stages,
then recalculates both sides' battle stats. It should be treated as setup
denial, not as damage progress.

Boss AI can reason from public revealed anti-setup effects for the active
player. It must not infer hidden Haze, Roar, Whirlwind, or anti-Rollout moves
from the unrevealed player bench.

## Damage Anchors

These are local damage-debugger checks for the existing Whitney drill:

```text
Miltank L21 Body Slam -> Geodude L20 at 78%:
  7-9 damage, 15-19% of current HP.

Miltank L21 first Rollout -> Geodude L20 at 78%:
  2-3 damage, 4-6% of current HP.

Miltank L21 first Defense Curl-boosted Rollout -> Geodude L20 at 78%:
  4-5 damage, 9-11% of current HP.

Geodude L20 Rock Throw -> Miltank L21 at 92%:
  15-18 damage, 21-25% of current HP.

Geodude L20 Magnitude examples -> Miltank L21 at 92%:
  70 BP: 20-24 damage, 28-34% of current HP.
  90 BP: 25-30 damage, 35-42% of current HP.
  110 BP: 30-36 damage, 42-51% of current HP.
  150 BP: 40-48 damage, 56-68% of current HP.
```

Strategic result: Whitney's first Rollout hit is too small to justify opening
the lock into healthy, unstatused Geodude. Body Slam pressure first remains the
local route unless Geodude is paralyzed, the punish branch is removed, or
current HP makes the lock immediately decisive.

## Strategic Translation

Use the expert-play lesson as a function rule, not a move import:

```text
Once a move is public, reclassify the Pokemon by the function that move gives
it. Before the move is public, preserve answers to plausible companion routes
without pretending the full set is known.
```

For Whitney:

- Miltank is not "the Rollout Pokemon" on turn 1. It is a flexible Body Slam /
  Milk Drink / Attract / Rollout ace.
- Rollout becomes a conversion move after paralysis, HP, Attract, or answer
  removal makes the forced sequence favorable.
- If the player reveals Haze, Roar, Whirlwind, or another anti-lock route, boss
  AI may account for that public active information according to local AI
  policy. It may not use hidden player-team knowledge.

For Delibird/Present:

- Present can be part of a reclassification drill only after local runtime or
  source evidence confirms the relevant trainer's actual moves and damage.
- Do not use `smogtours-gen2ou-891177` Present damage as local damage evidence.
  The replay is a strategic analogy: public damage changes the route map.

For Haze:

- Treat Haze as a reset endpoint only when it denies a real setup route or
  preserves a later answer.
- If the opponent is not using boosts, Haze may be a low-value turn even though
  it is mechanically legal.

## Before Advising

Ask:

1. Is the move actually on the local boss/trainer set, or only legal by
   learnset?
2. Has the move been publicly revealed, or is it only a plausible companion
   route?
3. Does the move change HP, PP, status, lock state, stat stages, or turn order?
4. Does the current answer beat the first hit, the full lock sequence, or only
   the non-locked state?
5. For boss AI, is the anti-lock or anti-setup answer public from the active
   player, or hidden on the bench?
6. Does the damage-debugger result cover the exact effective BP, status, item,
   type, and current HP branch?

## Remaining Verification

- Runtime-fixture Present against representative targets to confirm text,
  heal branch, PP, and damage path in the romhack.
- Validate the generated move list for Pokefan Colin's level 32 Delibird before
  treating it as a Present or Haze trainer drill.
- Runtime-fixture Rollout miss behavior, forced continuation, and interaction
  with phazing/Haze in a live battle trace.
