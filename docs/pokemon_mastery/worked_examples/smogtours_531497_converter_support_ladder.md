# Worked Example: Converter Support Ladder

Source review: `../reviews/2026-05-13_smogtours-gen2ou-531497.md`

Source replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-531497

Source team context:
https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/

Format: vanilla GSC OU. This is a strategic example, not romhack mechanics
proof.

## Position Pattern

```text
Our side:
We have a clear converter that can win after support.
The converter cannot safely sweep immediately.
Several teammates have narrow support jobs that make the converter real.

Opponent side:
Several blockers remain.
Some blockers are also counter-converters if we tunnel too hard.

Critical timing:
The first converter entry may only remove one blocker or force a reset. That
can still be progress if the route ladder survives.
```

## Candidate Move Classes

Best when available:

- Complete the missing support job that makes the converter safer: status,
  hazard, spin, phaze, chip, forced Rest, or safe entry.
- Use the converter when its entry removes a named blocker and the remaining
  counter-route is still covered.
- Preserve a low-health converter if one attack later still closes the route.

Acceptable:

- Handoff to a backup piece if it finishes the same route with fewer remaining
  blockers.
- Sacrifice a support piece after its job is complete and the converter entry
  is now clean.

Wrong:

- Declaring the route dead because the first setup attempt was checked.
- Sending the converter before the support jobs are done when the opponent can
  answer and counter-convert.
- Continuing to preserve the converter after all realistic support paths are
  gone and another route is cleaner.

## Rule

Before using or abandoning the planned converter, fill this out:

```text
Converter:
Required entry state:
Current blockers:
Support job 1:
Support job 2:
Support job 3:
What the first entry should accomplish:
Backup converter:
Event that proves the route is dead:
```

The move is good when it moves one line of this ledger from missing to complete.
It is weak when it only makes the visible matchup look better without changing
the converter ledger.

## Boundary Flip

Same converter, different answer:

```text
If the support jobs are incomplete, preserve the converter and build the route.
If the blocker map is solved and the converter can force the final sequence,
stop preserving and cash it out.
```

Same support move, different answer:

```text
Thunder Wave, Spikes, phazing, or a sacrifice is progress only if it changes a
blocker or entry condition for the converter. If the converter still cannot
enter or the opponent's counter-route becomes stronger, the support move may be
busywork.
```

## Boss-Battle Transfer

Use this when planning around a player Pokemon that is supposed to win the
fight later, especially setup sweepers, weather abusers, bulky Rest users,
priority cleaners, and one-time trade users.

Questions:

1. What must happen before this Pokemon can convert?
2. Is the current move completing one of those jobs?
3. If the first attempt only removes one boss piece, does that still improve
   the final route?
4. What boss route becomes live after that piece falls?
5. Which player Pokemon can inherit the route if the first converter is low?

This is the difference between "use the strong Pokemon" and "build the board
where the strong Pokemon's remaining turn actually wins."
