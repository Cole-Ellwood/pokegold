# Worked Example: Support Delivery Cascade

Source review: `../reviews/2026-05-13_smogtours-gen2ou-604744.md`

Source replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-604744

Supporting source:
https://www.smogon.com/forums/threads/gsc-ou-smeargle.3696816/

Format: vanilla GSC OU. This is a strategic example, not romhack mechanics
proof.

## Position Pattern

```text
Our side:
A support Pokemon can create speed, sleep, safe entry, or another temporary
advantage.
A receiver exists, but it needs the support to remove a route blocker.

Opponent side:
One or more blockers still stop the intended converter.
The opponent can deny the chain with phazing, Sleep Talk pressure, direct
damage, status, or a defensive pivot if given the right turn.
```

In the replay, Smeargle first uses Agility plus Baton Pass to deliver Marowak,
which removes Raikou. Later, after more trades, Smeargle uses Spore plus Baton
Pass to deliver Zapdos into the cleanup route.

## Candidate Move Classes

Best / acceptable:

- Use support when the receiver is named, the receiver's target matters, and
  the delivery line survives the opponent's best public punish.
- Spend a one-time trade after the support route changes the blocker map and
  the spent piece has already performed its durable job.

Wrong:

- Boosting or sleeping because support is generally good, without naming the
  receiver and blocker.
- Continuing the original support script after the board changes.
- Spending the receiver answer to remove the supporter when a safer denial line
  exists.

## Rule

Support is progress only when it delivers a route:

```text
support available:
receiver named:
blocker named:
delivery branch survives:
receiver changes the blocker map:
=> support is a real move
```

If the receiver is unavailable, the blocker is not relevant, or the opponent's
best public punish breaks the chain, direct damage, denial, pivoting, or
sacrifice may be better.

## Boundary Flip

Same support move, different answer:

```text
If Agility lets Marowak remove Raikou, Baton Pass can be route-winning.
If the opponent has a healthy phazer ready and Marowak cannot convert before
being reset, the same Agility can be a wasted turn.

If Spore creates Zapdos entry after its blockers are gone, it is conversion.
If the sleeping target wakes or Sleep Talks into immediate pressure and Zapdos
cannot convert, the support line must be abandoned.
```

## Boss-Battle Transfer

Use this when a boss or player route depends on screens, sleep, speed boosts,
setup, weather, Encore, forced switching, or safe-entry support.

Before recommending a support move:

1. Name the receiver.
2. Name the blocker the receiver will remove.
3. Check the opponent's best denial branch.
4. Check whether the support user is still needed later.
5. State what changes if the support succeeds.

Before denying a boss support move:

1. Name the receiver the boss is enabling.
2. Decide whether the supporter or receiver is the urgent target.
3. Preserve the piece that answers the supported receiver.
4. Re-score after every pass, sleep, phaze, miss, wake, or trade.
