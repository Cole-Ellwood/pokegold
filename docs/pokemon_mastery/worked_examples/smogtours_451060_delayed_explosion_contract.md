# Worked Example: Delayed Explosion Contract

Source review: `../reviews/2026-05-13_smogtours-gen2ou-451060.md`

Source replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-451060

Source team context:
https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/

Format: vanilla GSC OU. This is a strategic example, not romhack mechanics
proof.

## Position Pattern

```text
Our side:
We have a Pokemon with Explosion, Self-Destruct, Destiny Bond, or another
one-time trade button.
That Pokemon is damaged or appears expendable.
It also still has a narrow live job: spin, phaze, set hazards, absorb, force
Rest, scout, attack one target, or create clean entry.

Opponent side:
There is at least one valuable target now, but the true route blocker may not
be active yet.
The opponent has a later route that may require this same piece to answer.

Critical timing:
Clicking the trade now wins material, but may lose the recurring job that keeps
the long game stable.
```

## Candidate Move Classes

Best when available:

- Preserve the trade user while its recurring job is still live.
- Use the recurring job first if it changes the route immediately: spin a layer,
  phaze a setup attempt, force Rest, reset positioning, or keep the future
  converter healthy.
- Spend the trade only when the target is a named route blocker and the
  post-trade map has a real converter.

Acceptable:

- Trade into a high-value target when the user's recurring job is already done
  or replaceable.
- Trade early if waiting allows the opponent's route to become irreversible.

Wrong:

- Exploding because the user is low HP.
- Exploding because the target is strong, without naming the route opened.
- Preserving forever after the contract target appears and the user's old job
  no longer matters.

## Rule

Before clicking the one-time trade, fill this out:

```text
Current user:
Trade move:
Target:
Target's route job:
Our route opened by removing target:
Our recurring job lost by spending user:
Replacement for lost job:
Opponent punish branch:
Next converter after the trade:
```

If the "next converter" line is blank, the trade is suspect. If the "recurring
job lost" line is still important and has no replacement, preserving is usually
better.

## Boundary Flip

Same user, different answer:

```text
If Golem is the only spinner and hazards are deciding the long game, preserve
Golem even if Explosion can trade for a useful target.
If hazards are gone, the spinner job is no longer needed, and the active target
blocks the remaining route, Explosion rises sharply.
```

Same target, different answer:

```text
If the target is valuable but replaceable, do not spend the one-time trade
unless the user's role is finished.
If the target is the only remaining answer to the cleaner or the only piece
holding the opponent's endgame together, the trade may be correct.
```

## Boss-Battle Transfer

Use this when a boss fight includes Explosion, Self-Destruct, Destiny Bond,
Perish Song, Focus Band, a low-health phazer, a low-health spinner, or another
one-time route converter.

Questions:

1. What route does the trade open?
2. What boss route does the user still answer if preserved?
3. Can the boss punish the trade with a pivot, status, setup, Protect-like
   effect, or sacrifice?
4. What remains after the trade: cleaner, wall, phazer, revenge killer,
   spinner, or nothing?
5. Would waiting one turn create a cleaner contract, or does waiting allow an
   irreversible route?

This is especially relevant for Gym Leader Lab because boss teams often have
role compression. A low-health Pokemon may still be the only piece that spins,
phazes, blocks a sweep, or creates safe entry.
