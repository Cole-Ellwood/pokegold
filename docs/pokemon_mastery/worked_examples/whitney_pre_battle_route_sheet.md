# Worked Example: Whitney Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Whitney as a support-disruption
into bulky-anchor fight. This is a team-agnostic planning artifact, not final
turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `WhitneyGroup`.
- Boss route map: `../boss_route_maps/whitney_turn1_route_sheet.md`.
- Type chart, stat changes, item behavior, recovery, Attract, Rollout, and move
  category references:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.
- Move data: `data/moves/moves.asm`.
- Rollout source: `engine/battle/move_effects/rollout.asm`.
- Attract source: `engine/battle/move_effects/attract.asm` and
  `engine/battle/core.asm`.
- AI tendency evidence, not a strategic law: `engine/battle/ai/scoring.asm`.

Expert study anchors:

- GSC status material: paralysis is most valuable when it enables a later
  route, so identify which target the paralysis is meant to disable and how
  quickly the boss can convert it.
- GSC Miltank material: Milk Drink plus Body Slam paralysis makes Miltank a
  durable support/anchor Pokemon in competitive GSC, but Whitney's local
  Miltank is not vanilla OU Miltank because its stats, item, and movepool are
  different.
- Move-restriction material: Rollout-style momentum moves are selected once,
  then commit the user to a sequence that can be punished if the opponent has a
  safe pivot, status, accuracy control, Haze/phazing, or revenge route.
- Long-term thinking and risk/reward material: compare the likely boss action
  to the worst plausible branch before spending the one piece needed for the
  Miltank phase.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Whitney

Known boss roster:
  Clefairy / Girafarig / Miltank

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include a way to stop Miltank after Body Slam / Attract / Milk Drink
  pressure, a way to avoid or ignore Clefairy's Thunder Wave + Double Team
  support route, and a Girafarig damage plan that does not expose the Miltank
  answer too early; exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  no Fairy type, local type chart edits, Poison hitting Normal for 2x, Normal
  hitting Psychic for 0.5x, Ghost hitting Normal for 0x, local type categories
  such as Ghost physical and Dark special, Miltank's local HP / Attack /
  Defense boost with Speed and Special Defense drop, Clefairy's Eviolite
  defense and Special Defense boost, Miltank's Mint Berry sleep cure, Milk
  Drink healing 50% max HP, Moonlight depending on time/weather, Rollout being
  30 BP / 90% accurate with a five-hit ramp, and Attract requiring opposite
  gender

Missing evidence:
  exact player team, HP, levels, moves, items, genders, speed relations, damage
  ranges, accuracy/evasion state, whether Thunder Wave misses or fails into the
  current lead, whether the Miltank answer survives Body Slam plus first
  Rollout, whether a Poison or Fighting route actually KOs under the local type
  chart, and whether a special attacker can exploit local Miltank's low Special
  Defense without losing to Body Slam / Attract disruption
```

## Output Shape

Primary route:

- Deny the support-to-anchor sequence. Clefairy wants to spend turns on Thunder
  Wave, Double Team, and Moonlight so that Girafarig and Miltank face a slower,
  less accurate, or chipped team. The opening should pressure Clefairy without
  spending the only Miltank answer.

Backup route:

- If Clefairy cripples the opener, stop trying to sweep through the mess. Pivot
  into the piece that still keeps Miltank contained, then rebuild around either
  direct pressure into Miltank's low Special Defense, a locally verified Poison
  or Fighting damage route, or a sequence that punishes Rollout before it ramps.

Boss route priority:

```text
immediate:
  Clefairy Thunder Wave or Double Team if it hits the piece needed later;
  Miltank Attract on the first turn of a new active Pokemon;
  Body Slam paralysis if it makes Miltank's Milk Drink loop or Rollout lock
  hard to punish.

accumulating:
  Clefairy Moonlight plus evasion, repeated Girafarig chip into the Miltank
  answer, and Miltank using Milk Drink to reset damage that did not cross a
  concrete threshold.

endgame:
  Miltank stabilizes after the user's clean answer has been paralyzed,
  attracted, chipped, or forced to enter through a bad sequence. Rollout is
  weak before it ramps and dangerous after the team has lost the ability to
  pivot or interrupt it.
```

Boss route to deny first:

- Deny Clefairy's support route if the lead cannot force progress before
  Thunder Wave / Double Team compounds. If the lead already pressures Clefairy,
  preserve the Miltank answer instead of taking low-value chip with it.

Boss route that can be delayed:

- Girafarig can often be treated as a damage-management phase rather than the
  main route, but only after checking whether Psybeam, Crunch, Shadow Ball, or
  Headbutt damages the exact piece needed for Miltank. TwistedSpoon makes
  Psybeam more relevant into some pivots, but exact damage still decides.

Best lead:

- A lead that pressures Clefairy immediately, is not the only Miltank answer,
  and does not lose the whole route if Thunder Wave lands or Double Team stacks.
  A Thunder Wave-immune or evasion-independent lead is attractive only if it
  also creates real progress; immunity without pressure lets Moonlight and
  Double Team own the clock.

First move plan:

- Use the first move to force Clefairy toward recovery, status it in a way that
  changes the Miltank phase, KO it, or pivot out before it tags the critical
  answer. "Set up" is only legal if Thunder Wave, Double Team, and Moonlight do
  not make the setup fail before Miltank arrives.

First 3 turns as intentions, not a script:

1. Establish whether Clefairy can be removed or forced to heal before it stacks
   support.
2. If Clefairy uses Thunder Wave or Double Team, re-score immediately: decide
   whether direct pressure still crosses a threshold or whether the Miltank
   answer must be preserved now.
3. When Girafarig or Miltank appears, stop evaluating by type slogans. Check
   actual damage, status, gender, speed, and whether the next action improves
   the Miltank containment route.

Piece to preserve:

- The Miltank answer above all. It may be a physical wall, a faster revenge
  route, a special breaker that exploits local Miltank's low Special Defense, a
  Poison or Fighting attacker with locally verified damage, or a control piece
  that can punish Rollout. It is not expendable just because it beats Clefairy
  on paper.

Piece that can be spent:

- A paralyzed or chipped opener can be spent only if spending it gives clean
  entry to the Miltank answer or removes Clefairy's support route. Do not spend
  it merely to trade chip that Milk Drink later erases.

Worst plausible branch:

- Clefairy paralyzes or evasion-stalls the piece meant to check Miltank,
  Girafarig chips the backup pivot, then Miltank lands Attract or Body Slam and
  uses Milk Drink to reset damage until Rollout becomes safe to start.

Abandon conditions:

- The Miltank answer becomes paralyzed, attracted, or too low to take Body Slam
  plus the first Rollout hit.
- Clefairy reaches multiple evasion boosts and the current route relies on
  ordinary accuracy.
- Girafarig reveals a damage range that makes the planned Miltank pivot unsafe.
- Miltank's Mint Berry invalidates a one-shot sleep route.
- A local type, passive, gender, or item fact contradicts the assumed answer.

What information would flip the lead or first move:

- The lead's gender relative to Miltank and whether Attract can work.
- Whether the lead is immune to Thunder Wave and still pressures Clefairy.
- Whether the team has a reliable evasion bypass, Haze/phazing, or enough direct
  damage to ignore Double Team.
- Whether a Poison or Fighting move actually KOs or forces Milk Drink under the
  local chart and current stats.
- Whether a special attacker can punish Miltank's low Special Defense before
  Body Slam paralysis or Attract removes agency.
- Whether the intended Miltank answer survives Girafarig's exact coverage.

## Extracted Lesson

Whitney is not solved by "bring Fighting" or "Miltank is scary." The real
question is whether the early support turns disable the one route that must
beat Miltank. Clefairy's weak-looking moves matter because they change later
action reliability; Girafarig matters when its coverage damages the future
answer; Miltank matters because Attract, Body Slam, Milk Drink, and Rollout can
turn a close damage race into a lost agency race. Treat Rollout as a commitment
to punish before it ramps, and treat every type-effectiveness claim as local
romhack evidence, not memory.
