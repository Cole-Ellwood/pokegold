# Replay Turn-Pause 050 Lead Trade Support Coverage - smogtours-gen2ou-924499 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-924499`.

Mode: spectator-public vanilla GSC replay practice.

Selected measurable action: fresh transfer after
`coverage_reveal_absorber_probe_001_2026-05-14.md`. The intended target was
clean-answer plus coverage-reveal branches. The replay instead exposed a
different support-routing miss, so the run stopped after turn 4 and was
recorded as its own artifact.

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs and contaminated `934420`.
- Screening printed only replay ID, selected start turn, total turns, route
  move count, and file size.
- The selected replay was `smogtours-gen2ou-924499`.
- The selected start was turn 1. Turns 1-4 were answered before reveal.
- Species for nicknamed leads were read only from the public initial switch
  lines: p1 Exeggutor and p2 Jynx.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_049_coverage_reveal_absorber_smogtours-gen2ou-924921_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/coverage_reveal_absorber_probe_001_2026-05-14.md`

Web sources checked:

- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, GSC OU Moltres:
  `https://www.smogon.com/forums/threads/gsc-ou-moltres.3671998/`
- Smogon Forums, Explosion in GSC:
  `https://www.smogon.com/forums/threads/explosion-in-gsc-qc-2-2-gp-2-2.3484961/`
- Smogon Forums, Jynx GSC OU:
  `https://www.smogon.com/forums/threads/jynx-gsc-ou-qc-2-2-gp-2-2.3667481/`

Source note: the Cloyster source keeps the support order explicit: Spikes
enables offensive progress, Toxic pressures Snorlax/Starmie/Cloyster, and
Explosion trades after the layer. The Explosion source reinforces that
self-KO moves are route trades, not generic damage. The replay added the
support-mirror branch I missed: after hazards are established, the support
move can be coverage damage into the opposing support Pokemon rather than more
status or a switch.

## Score Summary

Scored decisions: 8 side decisions.

Top-match: 2 / 8.

Acceptable-match: 4 / 8.

Classification hits: 3 / 8.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 1. I expected the Exeggutor/Jynx lead to play
a sleep or sleep-absorber branch, but the expert line traded Exeggutor
immediately with Explosion after Jynx used Thief.

Main improvement:

- Turn 3 p1 kept the support order clean: Forretress set Spikes when it had
  the free support seat.

Main errors:

- Turn 1: over-centered sleep from the lead matchup and missed the immediate
  Explosion trade into Jynx.
- Turn 2: missed both sides' double-switching into support seats: Zapdos did
  not stay to Thunder, and Cloyster did not stay to set Spikes.
- Turn 4 p1: expected passive Toxic or a switch from Forretress, but the
  actual line used Giga Drain to damage opposing Cloyster after both hazard
  setters were in the route map.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Classification |
|---|---|---|---|---|---|
| 1 | Exeggutor lead vs Jynx lead | p1 switch to sleep absorber if available / Sleep Powder fallback; p2 Lovely Kiss | p2 Thief; p1 Explosion, both faint | p1 miss, p2 acceptable | Lead route trade over sleep script. |
| 2 | Zapdos 100 vs Cloyster 100 after lead trade | p1 Thunder; p2 Spikes | both switched: p1 Forretress, p2 Steelix | both miss | Double-switch into support / Ground-Steel seats. |
| 3 | Forretress 100 vs Steelix 100 | p1 Spikes; p2 stay with Earthquake/Roar | p2 switched Cloyster; p1 Spikes | p1 top, p2 miss | Hazard progress; p2 support mirror. |
| 4 | Forretress 100 vs Cloyster 100 with Spikes on p2 | p1 Toxic or pivot; p2 Spikes | p2 Spikes; p1 Giga Drain into Cloyster | p1 acceptable, p2 top | Coverage damage in support mirror. |

## Reusable Lessons

Lead sleep threat does not force a sleep script. If the immediate trade removes
the opposing lead's route job and the traded piece is not needed for a later
route, Explosion can be correct even before any slow positioning.

Support mirrors are not only Spikes, Toxic, Spin, or Explosion. If both support
seats are established, a coverage move that damages the opposing support piece
can be the route move. Forretress using Giga Drain into Cloyster served the
hazard/support subgame better than my passive Toxic default.

## Next Rep

Fresh replay transfer with the clean-answer plus coverage-reveal branches
again, but add one support-mirror classification:

```text
coverage damage into support piece
```
