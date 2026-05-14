# Worked Example: Reset Hub Leak Remains

Purpose: practice the losing side of reset-hub evaluation. A debuff, cleric,
or recovery hub can be the right immediate answer and still fail the full
route because another leak remains.

Source:

- Replay review: `../reviews/2026-05-13_smogtours-gen2ou-741084.md`
- Replay log: https://replay.pokemonshowdown.com/smogtours-gen2ou-741084.log
- Expert basis: Smogon GSC OU Threatlist,
  https://www.smogon.com/gs/articles/gsc_threats

Format: vanilla GSC OU strategic review. Transfer to Gym Leader Lab only after
local mechanics validation.

## Public State

This prompt pauses after turn 231 of `smogtours-gen2ou-741084`.

```text
Fear:
  Miltank is active at 61% after Leftovers and is paralyzed.
  Revealed moves: Growl / Heal Bell / Milk Drink / Seismic Toss.
  Starmie is the last teammate, at full HP.
  Revealed Starmie moves: Psychic / Recover / Surf / Rapid Spin.

BlazingDark:
  Rhydon is active at full HP and is paralyzed.
  Revealed moves: Curse / Earthquake / Roar / Rock Slide.
  Rhydon just switched into Miltank's Growl.
  Snorlax is still alive and has shown Body Slam / Curse / Earthquake / Rest.
  Raikou is still alive and has shown Crunch / Rest / Sleep Talk / Thunder.

Information boundary:
  There is no Team Preview. This prompt uses only moves and Pokemon revealed
  before this turn.
```

Route status:

- Miltank has stabilized several Snorlax turns with Growl and Milk Drink.
- Rhydon is a different leak: stronger immediate Ground damage, Roar, and a
  typing that asks for Starmie rather than Miltank.
- Raikou remains the special-pressure leak against Starmie and Miltank.

## Live-Turn Question

What should the advisor prioritize now?

Candidate classes:

1. Growl Rhydon again.
2. Milk Drink with Miltank.
3. Switch to Starmie.
4. Seismic Toss Rhydon.
5. Heal Bell paralysis.
6. Call the Miltank loop winning because it handled Snorlax.

## Answer

Recommendation: re-open the leak audit immediately. Rhydon is not the Snorlax
route Miltank was containing. If Starmie can be delivered without losing the
Raikou branch on the next turn, switch to Starmie; if that branch is not
covered, label the position forced risk rather than calling the Miltank loop
safe.

In the replay, Fear uses Growl again on turn 232. Rhydon still KOs Miltank
with Earthquake, and Starmie then loses to Raikou's RestTalk Thunder sequence.

Why repeated Growl fails as a policy:

- The previous Growl loop answered Snorlax's Attack boosts. It did not prove
  Miltank could survive Rhydon's damage.
- Rhydon also has Roar, so even a switch to Starmie has to account for the
  follow-up map instead of assuming a clean one-on-one.
- Raikou remains alive, so Starmie entering Rhydon is only part of the route.
  The next branch must say how Starmie avoids becoming Raikou's endpoint.
- Heal Bell or Milk Drink may improve Miltank's state, but neither removes the
  active Rhydon leak before Earthquake.

## Boss Transfer

Use this for local debuff and recovery loops:

```text
1. Name the target the hub was actually containing.
2. When a new boss piece enters, stop crediting the old containment line.
3. Re-score the new active's damage, coverage, phazing, status, and switch
   punish.
4. Deliver the correct answer if it can still enter.
5. If the correct answer loses to the next revealed boss piece, call the route
   forced risk instead of pretending the hub is winning.
```

Local cautions:

- Do not transfer exact Rhydon, Miltank, or Raikou damage to Gym Leader Lab.
- Check local stat-stage, switching, phazing, Haze, item, and type-passive
  mechanics before exact advice.
- Boss AI may use revealed player species, revealed moves, observed damage,
  status, hazards, and legal local memory. It may not use unrevealed player
  bench or hidden moves to prove that no leak remains.

## Lesson

Reset is target-specific. If the hub contains Snorlax, that does not mean it
contains Rhydon, Raikou, or the next boss route. Every new entry re-opens the
leak audit.
