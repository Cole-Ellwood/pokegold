# Replay Turn-Pause 045 Sleep Clause Clamp Explosion Growth - smogtours-gen2ou-927169 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-927169`.

Mode: spectator-public vanilla GSC replay practice.

Selected measurable action: fresh transfer after
`pivot_progress_after_gate_probe_001_2026-05-14.md`, using the new
classification labels:

```text
active attack / active progress / double / route denial / side-known answer
```

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs, recent exposed candidates, and contaminated `934420`.
- Screening printed only replay ID, selected start turn, total turns, route
  move count, and file size.
- The selected replay was `smogtours-gen2ou-927169`.
- The selected start was turn 13. Turns 13-18 were answered before reveal.
- P1 turns where sleep prevented the selected move from being logged are marked
  unscored for top-move agreement.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_044_active_target_after_pivot_gate_smogtours-gen2ou-929268_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/pivot_progress_after_gate_probe_001_2026-05-14.md`

Web sources checked in the parent work block:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Pokemon Showdown ladder help:
  `https://pokemonshowdown.com/pages/ladderhelp`
- Smogon Forums, GSC OU Discussion Thread page 3:
  `https://www.smogon.com/forums/threads/gsc-ou-discussion-thread.3688141/page-3`
- Smogon Forums, An Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`

## Score Summary

Scored decisions: 10 side decisions.

Top-match: 6 / 10.

Acceptable-match: 7 / 10.

Classification hits: 6 / 10.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 13 p2. I treated Counter as the main Nidoking
punish into Snorlax, but Lovely Kiss was the route-changing move.

Main improvement:

- Turn 17 transferred the user's sleep-clause point cleanly. At 10% and asleep
  with Spikes up, Snorlax had no realistic re-entry action, but preserving it
  still blocked future Lovely Kiss. Sacking burned Cloyster preserved that
  sleep-clause shield and gave Espeon clean entry.

Main errors:

- Turn 13 p2: underpriced the immediate Lovely Kiss route.
- Turn 14 p2 and turn 15 p2: missed the support order of Cloyster switch, Clamp,
  then Explosion. Explosion was right, but only after Clamp locked the target.
- Turn 18 p1: failed the fresh active-progress transfer. Psychic attacked the
  active Nidoking, but Growth was the move that improved through the expected
  Snorlax pivot.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Classification |
|---|---|---|---|---|---|
| 13 | Snorlax 94 vs Nidoking 67 | p1 Curse; p2 Counter | p2 Lovely Kiss; p1 slept before moving | p1 unscored, p2 miss | I looked at Counter and missed sleep as the route-changing active move. |
| 14 | sleeping Snorlax 99 vs Nidoking 73 | p1 stay; p2 Earthquake / strongest attack | p2 switched Cloyster; p1 stayed asleep | p1 top, p2 miss | P1 correctly had no safe switch; p2 found support setup instead of damage. |
| 15 | sleeping Snorlax 100 vs Cloyster 88 | p1 stay; p2 Explosion | p2 Clamp; p1 stayed asleep | p1 top, p2 miss | Explosion target was right, but Clamp was the progress move before cash-out. |
| 16 | sleeping Snorlax 94 trapped vs Cloyster 88 | p2 Explosion | p2 Explosion into Snorlax, leaving it at 10 | p2 top | Route trade after Clamp. P1 move was unscored because sleep prevented action. |
| 17 | sleeping Snorlax 10 vs Nidoking 67 | p1 switch Cloyster as sack; p2 Earthquake | p1 switched Cloyster; p2 Earthquake crit KO | p1 top, p2 top | Sleep-clause shield preservation with a low-value spacer sack. |
| 18 | Espeon 94 vs Nidoking 73 | p1 Psychic; p2 switch Snorlax | p2 switched Snorlax; p1 Growth | p1 miss, p2 top | Active progress beat active attack: Growth improved through the expected Snorlax pivot. |

## Reusable Lessons

Sleep-clause preservation can matter even when the sleeper is too low to
re-enter. At turn 17, sleeping Snorlax at 10% with Spikes up was still a live
resource because it blocked another Lovely Kiss. The correct preservation was
not "save Snorlax to fight later"; it was "save the asleep status and spend a
lower-value spacer for Espeon entry."

Explosion may be the right route trade but still have a setup order. Cloyster
did not Explode immediately into sleeping Snorlax; it switched in, used Clamp
to trap, then Exploded. The target and trade were right, but the route needed
one preparatory move.

The active-progress probe did not transfer fully. On turn 18, Psychic was the
simple active attack into Nidoking, but Snorlax was the expected pivot and
Growth was the active progress move that improved through that pivot.

## Next Rep

Run a fresh short transfer focused only on special-attacker versus special-wall
pivots:

```text
If the active target is threatened and the wall pivot is obvious, should the
move be direct damage, setup/status, or a double?
```
