# Worked Example: Phaze Before Conversion

Source review: `../reviews/2026-05-13_smogtours-gen2ou-935544.md`

Source replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-935544

Supporting source: https://www.smogon.com/gs/articles/move_priority

Format: vanilla GSC OU. This is a strategic example, not romhack mechanics
proof.

## Position Pattern

```text
Our side:
Zapdos is active and healthy enough to take the public punish.
Whirlwind is available.
Spikes are on the opponent side.

Opponent side:
A sleeping anchor is active or a setup attacker has just entered.
The opponent's next step is to stabilize with Sleep Talk, boost, or start a
cleaner route.
```

In the replay, Zapdos used Whirlwind on turn 37 to remove sleeping Snorlax.
Jolteon entered through Spikes, used Growth on turn 38, and Zapdos used
Whirlwind again before Jolteon became the whole game.

## Candidate Move Classes

Best / acceptable:

- Use the control move if it works mechanically, the user survives the public
  punish, and the forced switch creates route progress through hazards, sleep
  turns, poisoned pieces, or a safer answer map.

Wrong:

- Attacking only because damage is available, if the damage does not stop the
  setup or stabilization route.
- Waiting until the setup user has already converted, then treating phazing as
  a desperate fallback.

Catastrophic in a different state:

- Using Roar or Whirlwind when it fails under local timing or priority.
- Phazing into a worse threat with no answer.
- Spending finite control PP when the opponent has not created a live route.

## Rule

Use a control move at the route boundary:

```text
route forming:
control move works:
user survives:
forced target map acceptable:
external clock or answer map improves:
```

If those fields cannot be filled, the move may only be delay.

## Boundary Flip

Same Whirlwind, different answer:

```text
If the opponent has just used Growth and the phazer survives, Whirlwind can be
the best route-denial move.
If the phazer is too low, acts too early for the format, or drags in an even
more dangerous cleaner, attacking, switching, Haze, Encore, or sacrifice may be
better.
```

Another flip:

```text
With hazards up, forced switches can become progress.
Without hazards, status, sleep turns, or a favorable answer map, the same
forced switch may only reroll the active matchup.
```

## Boss-Battle Transfer

Use this when a boss has Dragon Dance, Curse, Growth, Quiver Dance, Rollout,
Encore chains, Baton Pass-style support, or a sleeping anchor trying to
stabilize.

Before recommending Roar, Whirlwind, Haze, Encore, or another control move:

1. Name the route being denied.
2. Check whether the move works in the romhack mechanics profile.
3. Check whether the user survives the public punish.
4. Name what improves after the forced reset.
