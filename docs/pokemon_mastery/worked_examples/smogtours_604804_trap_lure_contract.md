# Worked Example: Trap-Lure Contract

Source review: `../reviews/2026-05-13_smogtours-gen2ou-604804.md`

Source replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-604804

Supporting source:
https://www.smogon.com/forums/threads/gsc-ou-gengar.3696769/

Format: vanilla GSC OU. This is a strategic example, not romhack mechanics
proof.

## Position Pattern

```text
Our side:
A trap, lure, Destiny Bond, Perish Song, or one-time tech can remove a target.
A later converter exists, but it is currently blocked.

Opponent side:
One specific wall, cleric, phazer, spinner, revenge killer, or anchor is what
keeps the route contained.
```

In the replay, Gengar traps Blissey with Mean Look and Perish Song. Blissey is
valuable because it is the special wall and cleric. Once it is gone, Espeon and
Raikou become much harder for Garay oak to contain.

## Candidate Move Classes

Best / acceptable:

- Use the trap or lure when the target is the actual blocker and the beneficiary
  can still convert after the trade.
- Spend another one-time resource after the trap only if the new target is now
  the blocker to the opened route.

Wrong:

- Trapping a strong but replaceable Pokemon while the real blocker remains.
- Using Destiny Bond or Perish Song without enough turns, HP, or switch control
  for the sequence to finish.
- Calling the trap successful before checking the next blocker.

## Rule

A trap or lure is a blocker-removal contract:

```text
target named:
beneficiary named:
route opened:
role lost by trapper:
next blocker named:
=> trap/lure can be strong
```

If any field is blank, the move is probably a trade idea rather than a strong
route decision.

## Boundary Flip

Same trap, different answer:

```text
If Blissey is the only thing keeping Raikou and Espeon contained, trapping it
can open the route.
If another healthy wall, faster revenge route, or phazer still covers those
converters, the trap may need a follow-up trade before it is real progress.
```

Another flip:

```text
If Gengar can survive the Perish turns, Mean Look into Perish Song can remove
the blocker.
If the target can KO Gengar, escape, force Destiny Bond timing, or make the
trapper faint before the count resolves, the trap is only a risk branch.
```

## Boss-Battle Transfer

Use this when advising around Mean Look, Spider Web, Pursuit, Destiny Bond,
Perish Song, lure coverage, one-time items, Explosion, or baited AI switches.

Before recommending the move:

1. Name the target.
2. Name the beneficiary.
3. Name the route opened.
4. Name the role lost if the trapper or lure user is spent.
5. Name the next blocker after the target is removed.

Failure pattern:

```text
"This removes a strong Pokemon."
```

Better:

```text
"This removes the wall that blocks our special-route converter; after it falls,
we still need to preserve the converter and stop the opponent's remaining
physical setup route."
```
