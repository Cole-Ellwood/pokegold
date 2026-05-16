# Replay Turn-Pause 042 Named Pivot Transfer - smogtours-gen2ou-931095 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-931095`.

Mode: spectator-public vanilla GSC replay practice.

Selected measurable action: fresh transfer after
`named_pivot_coverage_probe_001_2026-05-14.md`. The target was to add a
named-pivot coverage column to the replay table:

```text
Named pivot:
Selected action affects pivot? yes/no
If no, why is accepting it correct?
```

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs, recent exposed candidates, and contaminated `934420`.
- Screening printed only replay ID, selected start turn, total turns, route
  move count, and file size.
- Turn 4 was revealed before I recorded a frozen answer, so it is context only
  and not scored. Turns 5-11 were answered before reveal.
- The run stopped after the named-pivot coverage error repeated on turns 5 and
  11.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/workspace/quick_tests/named_pivot_coverage_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_041_branch_coverage_transfer_smogtours-gen2ou-931101_2026-05-14.md`

Web sources checked:

- Smogon Forums, GSC OU Tyranitar:
  `https://www.smogon.com/forums/threads/gsc-ou-tyranitar.3676727/`
- Smogon Forums, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon Forums, GSC OU Starmie:
  `https://www.smogon.com/forums/threads/gsc-ou-starmie.3692223/`
- Smogon Forums, GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

Source note: the Tyranitar and sample-team sources reinforce that coverage is
target-specific. Tyranitar's role compression is valuable only when the move
matches the switch tree: Rock Slide for Zapdos, Fire Blast for Steels,
Earthquake for grounded Rock/Steel/Ghost targets, and Pursuit/Roar for their
own route roles.

## Score Summary

Scored decisions: 14 side decisions.

Top-match: 4 / 14.

Acceptable-match: 7 / 14.

P1 named-pivot coverage checks: 2 / 7.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Unscored context: turn 4 was not counted because I revealed it before freezing
an answer.

Earliest meaningful error: turn 5 p1. I named Zapdos as the serious pivot and
identified Rock Slide as the coverage move, then still chose Earthquake.

Repeated target error:

- Turn 5: named Zapdos pivot, selected Earthquake instead of Rock Slide.
- Turn 11: named Steelix pivot, selected Thunder instead of a move or double
  that affected Steelix.

Main improvements:

- Turn 8: preserved sleeping Tyranitar instead of burning turns, keeping it as
  Sleep Clause material and a future Rock/Pursuit/coverage piece.
- Turn 9: used Spikes as an explicit accepted-branch line. Spikes did not cover
  Thunder, but the route benefit was named and the branch was not pretended
  away.

Main errors:

- Turn 5 and turn 11 repeated the named-pivot coverage failure directly.
- Turn 10 repeated the resource-selection version: I named Forretress
  Explosion value but chose preservation instead of the cash-out that removed
  Zapdos.
- Turn 7 missed Lovely Kiss from the opposing Snorlax and did not cover the
  sleep branch.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Named pivot / coverage |
|---|---|---|---|---|---|
| 5 | Marowak vs Steelix 54 | p1 Earthquake; p2 Zapdos | p2 Zapdos; p1 Rock Slide | p1 miss, p2 top | Named Zapdos; selected Earthquake: no. |
| 6 | Marowak vs Zapdos 50 | p1 Rock Slide; p2 Steelix/coverage | both switched: p1 Tyranitar, p2 Snorlax | both miss | Named Steelix; selected Rock Slide: no. |
| 7 | Tyranitar vs Snorlax | p1 Dynamic Punch; p2 Steelix/attack | p1 Rock Slide; p2 Lovely Kiss | both miss | Named Ghost as a fail branch; selected Dynamic Punch would not cover it. |
| 8 | sleeping Tyranitar vs Snorlax 79 | p1 switch to preserve sleeper; p2 attack/Curse | p1 Forretress; p2 Zapdos | both acceptable | Named Marowak punishment; p2 Zapdos covered it. |
| 9 | Forretress vs Zapdos 56 | p1 Spikes; p2 Thunder | p2 Thunder miss; p1 Spikes | both top | Named Thunder; selected Spikes accepts rather than covers it. |
| 10 | Forretress vs Zapdos 62 | p1 switch Snorlax; p2 Thunder | p2 Hidden Power; p1 Explosion KOed both | p1 miss, p2 acceptable | Named Explosion value; selected switch: no. |
| 11 | Zapdos vs Gengar 93 | p1 Thunder; p2 attack/Explosion | p2 Steelix; p1 Thunder immune | p1 top by move, p2 miss | Named Steelix; selected Thunder: no. |

## Reusable Update

The micro-probe did not transfer yet. The new forced step for serious advice:

```text
If I name a pivot, the final action must be checked against that pivot before
the answer is frozen.
```

Use this exact final check:

```text
Named pivot:
Does my selected action affect it? yes/no
If no: am I accepting that pivot, downgrading it, or choosing the wrong move?
```

The key distinction is between an accepted branch and an uncovered branch.
Turn 9 was accepted: Spikes did not cover Thunder, but the route benefit was
worth the risk. Turns 5 and 11 were uncovered: Earthquake did not cover the
named Zapdos pivot, and Thunder did not cover the named Steelix pivot.

## Next Rep

Run one more fresh replay transfer, but stop after four p1 decisions and force
the answer format to include the named-pivot check before reveal. If the
coverage score is below 3 / 4, build a stricter answer template rather than
another prose note.
