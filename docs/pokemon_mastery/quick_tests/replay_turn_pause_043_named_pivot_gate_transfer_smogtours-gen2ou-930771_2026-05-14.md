# Replay Turn-Pause 043 Named Pivot Gate Transfer - smogtours-gen2ou-930771 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-930771`.

Mode: spectator-public vanilla GSC replay practice.

Selected measurable action: fresh transfer after
`replay_turn_pause_042_named_pivot_transfer_smogtours-gen2ou-931095_2026-05-14.md`.
The target was four p1 decisions with the forced named-pivot gate before each
reveal:

```text
Named pivot:
Does my selected action affect it? yes/no
If no: accepting, downgrading, or wrong move?
```

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs, recent exposed candidates, and contaminated `934420`.
- Screening printed only replay ID, selected start turn, total turns, route
  move count, and file size.
- The selected start was turn 5. Turns 5-8 were answered before reveal, then
  the run stopped after four p1 decisions as specified.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/named_pivot_coverage_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_042_named_pivot_transfer_smogtours-gen2ou-931095_2026-05-14.md`

Web sources checked:

- Smogon Forums, GSC OU Tyranitar:
  `https://www.smogon.com/forums/threads/gsc-ou-tyranitar.3676727/`
- Smogon Forums, GSC OU Starmie:
  `https://www.smogon.com/forums/threads/gsc-ou-starmie.3692223/`
- Smogon Forums, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon Forums, GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

Source note: the relevant source lesson is still coverage matching. Tyranitar
compresses Pursuit / Roar / coverage, but the chosen move must match the
target being punished. This replay shows the named-pivot gate transferred, but
the next weak point is deciding whether the active target, not the pivot, is
the branch that deserves the move.

## Score Summary

Scored decisions: 8 side decisions.

Top-match: 3 / 8.

Acceptable-match: 5 / 8.

P1 named-pivot coverage checks: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 5 p1. The named-pivot gate correctly rejected
Rock Slide into a named Steelix pivot and revised to Earthquake if available,
but the actual route used Pursuit because Gengar's escape / trap branch was
more important than the Steelix pivot.

Main improvement:

- The exact turn-42 failure did not recur. Every p1 answer included a named
  pivot and either chose a move that affected it or explicitly accepted /
  downgraded it.

Main errors:

- Turn 5: overcorrected toward the named Steelix pivot and missed Pursuit's
  role into Gengar's escape branch.
- Turn 6: named the pivot gate but underpriced repeated Hypnosis from the
  active Gengar.
- Turn 7: overapplied the sleep-clause preserve default; actual play stayed in
  with sleeping Tyranitar to keep the Gengar trap seat occupied.
- Turn 8: chose the right stay-in structure but did not infer Crunch as the
  direct active-target punish.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Named pivot gate |
|---|---|---|---|---|---|
| 5 | Tyranitar 71 vs Gengar 100 | Earthquake if available after rejecting Rock Slide into named Steelix; p2 switch/attack | p2 Hypnosis miss; p1 Pursuit | p1 acceptable, p2 miss | Named Steelix; selected Earthquake affects it: yes. |
| 6 | Tyranitar 77 vs Gengar 73 | Earthquake if available; otherwise Pursuit accepts Steelix | p2 Hypnosis slept Tyranitar | p1 miss, p2 top | Named Steelix; selected Earthquake affects it: yes, but status branch was underpriced. |
| 7 | sleeping Tyranitar 83 vs Gengar 79 | switch Snorlax to preserve sleeper; p2 Thunderbolt | p2 Thunderbolt; p1 stayed asleep | p1 miss, p2 top | Named Thunderbolt / Steelix; selected switch covers Thunderbolt and accepts Steelix. |
| 8 | sleeping Tyranitar 66 vs Gengar 86 | stay and select Pursuit, accepting Steelix | p2 Thunderbolt; p1 woke and used Crunch | p1 acceptable, p2 top | Named Gengar switch / Steelix; selected Pursuit covers Gengar leaving and accepts Steelix. |

## Reusable Update

The stricter named-pivot gate worked, so do not make it more verbose yet. The
new weakness is ordering branches after the gate:

1. Active target's immediate route.
2. Named pivot route.
3. Status / sleep / trap branch.
4. Our piece's current seat or job.

In this run, the active Gengar's Hypnosis and the trapper-seat value of
sleeping Tyranitar mattered more than the Steelix pivot I kept centering. The
gate should stay, but the next replay should add one more final question:

```text
After the pivot gate, is the active target still the bigger branch?
```

## Next Rep

Fresh four-decision replay transfer with two forced checks:

```text
Named pivot:
Selected action affects pivot? yes/no
After that, is active target still the bigger branch? yes/no
```
