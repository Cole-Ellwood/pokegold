# Worked Example: Post-Spin Trade Audit

Source review: `../reviews/2026-05-13_smogtours-gen2ou-935507.md`

Source replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-935507

Format: vanilla GSC OU. This is a strategic example, not romhack mechanics
proof.

## Position Pattern

```text
Our side:
We have a hazard layer up.
Our spinner / sacrifice user is active.
The opposing spinner is active and can remove our layer this turn.

Opponent side:
The opposing hazard setter is still alive.
The opposing spinner may be removed by Explosion or another sacrifice.

Critical timing:
The opposing spin may happen before our sacrifice move resolves.
```

## Candidate Move Classes

Best when available:

- Deny the spin before it resolves, if the current layer is the route.
- Remove the hazard setter instead, if the setter can immediately recreate the
  hazard state after the spinner trade.
- Spin first, if preserving our own switch loop is more important than keeping
  the current layer.

Acceptable:

- Trade for the spinner after it spins only if denying future spins is enough
  and the post-trade setter map still favors us.

Wrong:

- Treating "spinner fainted" as proof that the hazard war was won.

Catastrophic in a different state:

- Spending the only spinner or defensive answer after the opponent support move
  has already resolved, then letting a surviving setter recreate the same
  problem for free.

## Rule

A sacrifice into a support piece must name which support function it denies:

```text
current action denied:
future action denied:
setter map after trade:
spinner map after trade:
route opened:
route closed:
```

If the answer is only "we KO the spinner," the policy is underspecified.

## Boundary Flip

Same Explosion, different answer:

```text
If Explosion acts before Rapid Spin, the current hazard layer may be preserved.
If Rapid Spin has already resolved, Explosion only denies future spins.
```

Another flip:

```text
If the opposing setter is gone or unable to reset hazards, removing the spinner
after it spins can still lock in future hazard advantage.
If the opposing setter survives and gets a clean turn, the trade may fail to
convert.
```

## Boss-Battle Transfer

Use this when a boss has Rapid Spin, Haze, screens, weather, or another support
move that may resolve before your sacrifice.

Before spending the Pokemon, ask:

1. Did the support move already happen?
2. Can another boss Pokemon recreate the support state?
3. Did the sacrifice open a named route, or only create a good-looking KO?
4. What defensive or removal role did the sacrificed Pokemon lose?
