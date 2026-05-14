# Worked Example: Surprise Function Reclassification

Purpose: practice changing the route map after a nonstandard move is publicly
revealed. The mistake is keeping the old species label after the battle has
shown a different function.

Source:

- Replay review: `../reviews/2026-05-13_smogtours-gen2ou-891177.md`
- Replay log: https://replay.pokemonshowdown.com/smogtours-gen2ou-891177.log
- Expert basis: Smogon GSC Mechanics,
  https://www.smogon.com/forums/threads/gsc-mechanics.3542417/

Format: vanilla GSC OU strategic review. Transfer to Gym Leader Lab only after
local mechanics validation.

## Public State

This prompt pauses after turn 107 of `smogtours-gen2ou-891177`.

```text
underlying:
  Vaporeon is active and very low after Leftovers.
  Revealed moves: Growth / Rest / Sleep Talk / Surf.
  Its route was to use Blissey as setup bait and convert with boosted Surf.

MrSoup:
  Blissey is active.
  Revealed moves: Present / Light Screen / Heal Bell / Soft-Boiled.
  Present has already dealt large damage to Cloyster earlier.
  Light Screen is part of the current answer map.

Information boundary:
  There is no Team Preview. We know these moves because they have been shown
  in the log, not because a preview told either player the full sets.
```

## Live-Turn Question

What should the advisor prioritize now?

Candidate classes:

1. Keep using Growth because Blissey is a special wall.
2. Surf immediately.
3. Rest and re-score the route.
4. Switch out and preserve Vaporeon.
5. Treat Blissey as passive setup bait until a KO happens.

## Answer

Recommendation: Rest and re-score the route. If Rest cannot create a clean
conversion through Sleep Talk, screen timing, and Present variance, prepare a
handoff instead of continuing to invest in the old setup plan.

Why:

- Blissey has publicly shown damage, screen, cleric, and recovery functions.
- The original route depended on Blissey being unable to punish Growth turns.
- Present damage has already changed Vaporeon's HP thresholds, so additional
  Growth is not free progress.
- Surf is useful only if it forces a recovery, removes Blissey, or changes the
  next blocker. Into Light Screen and Soft-Boiled, it may just spend a turn.
- The advisor should now call Blissey "damage plus screen plus recovery," not
  "passive special wall."

In the replay, Vaporeon uses Rest on turn 108 and continues trying to force the
route, but eventually faints to Present on turn 127.

## Second Public State

Later, before turn 297:

```text
MrSoup's Snorlax has shown Toxic, Rest, and repeated Defense Curl.
Rollout has not yet been shown.
underlying still has Steelix with Roar and Zapdos as the main pressure piece.
Spikes are on underlying's side.
```

Expected policy: do not claim the full Snorlax set is known. Do treat Defense
Curl as a public warning that a delayed lock route may exist, and preserve the
Haze/phaze/damage answer that would punish it if Rollout appears.

After Rollout is revealed, the policy changes again: count the lock turn,
preserve or spend phazing before the high-power hit, and price whether a
sacrifice or direct KO is safer than waiting.

## Boss Transfer

Use this for local boss advice:

```text
1. Name the old species-role assumption.
2. Name the newly revealed function.
3. Ask which route the new function blocks or opens.
4. Replace the old plan if the function changes HP, PP, status, or turn order.
5. For boss AI, use only public player information and locally allowed memory.
```

Local cautions:

- Do not transfer Pokemon Showdown Present damage. Check
  `engine/battle/move_effects/present.asm`, `data/moves/present_power.asm`,
  and local damage evidence.
- Rollout advice must use local `engine/battle/move_effects/rollout.asm`,
  local accuracy, miss behavior, Defense Curl state, Haze/phazing, and current
  HP.
- Boss AI may reclassify a player Pokemon after a move is revealed or after
  observed damage proves a threshold. It may not use hidden player bench,
  hidden moves, or hidden items to do the same.

## Lesson

Public reveal changes the route map. Do not keep treating a Pokemon as setup
bait, harmless support, or a standard anchor after the battle has shown a
different function.
