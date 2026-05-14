# Worked Example: Reset Hub Leak Audit

Purpose: practice the late-game distinction between empty waiting and a reset
hub that has become the actual endpoint. Miltank-style play is not good because
it is passive; it is good when the remaining opponent routes cannot break its
debuff, cure, and recovery loop.

Source:

- Replay review: `../reviews/2026-05-13_smogtours-gen2ou-861180.md`
- Replay log: https://replay.pokemonshowdown.com/smogtours-gen2ou-861180.log
- Expert basis: Smogon GSC OU Threatlist,
  https://www.smogon.com/gs/articles/gsc_threats

Format: vanilla GSC OU strategic review. Transfer to Gym Leader Lab only after
local mechanics validation.

## Public State

This prompt pauses before turn 220 of `smogtours-gen2ou-861180`.

```text
melancholy0:
  Miltank is active at 78% after Leftovers.
  Revealed moves: Body Slam / Growl / Heal Bell / Milk Drink.
  Zapdos is alive but recently took heavy Double-Edge damage.
  Cloyster, Snorlax, and a low Marowak have been part of the long route.

underlying:
  Snorlax is active at 75%, paralyzed, and has just used Curse.
  Revealed moves: Curse / Double-Edge / Earthquake / Rest.
  Marowak is fainted.
  Raikou is fainted.
  Starmie, Skarmory, and Miltank remain as reset/support pieces.

Field:
  No decisive retained Spikes clock is currently winning the game.
  The late game is about whether Snorlax can create a leak through the reset
  structure.
```

Leak audit:

- Marowak breaker leak: gone.
- Raikou special-pressure leak: gone.
- Snorlax boost leak: active.
- Starmie spin/recover leak: still affects hazard routes, not the immediate
  Miltank-vs-Snorlax exchange.
- Skarmory phaze/status leak: still affects setup routes, not the immediate
  Growl answer.

## Live-Turn Question

What should the advisor prioritize now?

Candidate classes:

1. Growl Snorlax.
2. Milk Drink.
3. Heal Bell.
4. Body Slam for chip.
5. Pivot to Zapdos for Whirlwind.
6. Switch to another attacker.

## Answer

Recommendation: Growl.

Plan: keep Snorlax from becoming the remaining leak. The other major breakers
are gone, so Miltank no longer needs to rush damage; it needs to keep Curse
Snorlax below conversion while preserving Milk Drink and Heal Bell timing.

Why Growl is best:

- Snorlax just used Curse, so the immediate route is physical boosting.
- Miltank is healthy enough that Milk Drink is not yet forced.
- Body Slam chip does not cross a decisive threshold and can be erased by Rest,
  Miltank support, or Skarmory/Starmie cycling.
- Heal Bell is useful only when status is the active route problem. The current
  problem is Snorlax's Attack.
- Zapdos Whirlwind is available as an emergency reset, but Zapdos is lower and
  should not be spent while Miltank can answer the active route directly.

In the replay, Miltank uses Growl on turns 220 and 221. Underlying switches
Skarmory into the third Growl attempt on turn 222 and forfeits on turn 223.

## Branch Discipline

If Snorlax keeps attacking:

- Continue Growl or Milk Drink based on current HP. The goal is to keep the
  damage below recovery pressure.

If Snorlax Rests:

- Re-score whether to Heal Bell, pivot, set hazards, or pressure Starmie. Rest
  can be progress only if the sleep turns are converted.

If Skarmory enters:

- Do not keep treating Growl as the answer. Skarmory asks a different question:
  Toxic, Whirlwind, and whether the player has a useful active into it.

If Starmie enters:

- Re-score the hazard route. Starmie can spin and Recover, so chip only matters
  if it crosses a forced Recover, poison, or KO threshold.

If Miltank is lower:

- Milk Drink can overtake Growl. The reset hub must stay alive before it can
  control anything.

## Boss Transfer

Use this for local recovery, debuff, and cure loops:

```text
1. Name the reset function: recovery, debuff, cure, phaze, spin, screen, Rest.
2. List the live leaks that break it.
3. If leaks remain, attack or preserve for the leak instead of waiting.
4. If leaks are gone, low-damage reset moves can be endpoint moves.
5. Re-score when a new leak enters or the hub falls below recovery range.
```

Local examples:

- Whitney Miltank has Milk Drink / Body Slam / Rollout / Attract, not this
  vanilla Heal Bell / Growl set. The transfer is the leak audit, not the exact
  move list.
- Will Slowbro, Sabrina Hypno, Koga Muk, and Red Snorlax-style anchors need the
  same test: does the player's move break the reset function, or does it only
  create chip that recovery erases?
- Boss AI must not use hidden player-team knowledge to declare that no leak
  exists.

## Lesson

Reset is a win condition only after leak closure. Before that, it is
stabilization and still needs a plan for the breaker that can punch through.
