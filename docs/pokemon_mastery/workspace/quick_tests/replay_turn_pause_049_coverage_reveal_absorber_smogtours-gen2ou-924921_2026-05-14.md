# Replay Turn-Pause 049 Coverage Reveal Absorber - smogtours-gen2ou-924921 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-924921`.

Mode: spectator-public vanilla GSC replay practice.

Selected measurable action: fresh transfer after
`hard_answer_before_status_probe_001_2026-05-14.md`. The target was the
clean-answer exception and the re-solve after coverage appears.

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs and contaminated `934420`.
- Screening printed only replay ID, selected start turn, total turns, route
  move count, and file size.
- The selected replay was `smogtours-gen2ou-924921`.
- The selected start was turn 5. Turns 5-6 were answered before reveal.
- The run stopped after turn 6 because the two-turn segment exposed the target
  miss cleanly.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_048_hard_answer_before_status_smogtours-gen2ou-924922_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/hard_answer_before_status_probe_001_2026-05-14.md`

Web sources checked:

- Smogon Forums, GSC OU Skarmory:
  `https://www.smogon.com/forums/threads/gsc-ou-skarmory.3709334/`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, GSC Zapdos:
  `https://www.smogon.com/forums/threads/gsc-zapdos.3674240/`
- Smogon Forums, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`

Source note: the Skarmory source supports counter-setup and phazing as part of
its Snorlax answer, but the replay tested the exception: if Snorlax reveals
Fire Blast, the old clean-answer model is no longer enough. The Cloyster
source frames Spikes and Explosion as a support/trade package; after Fire Blast
hit Cloyster, the Snorlax side protected Snorlax from that trade by pivoting
sleeping Moltres.

## Score Summary

Scored decisions: 4 side decisions.

Top-match: 1 / 4.

Acceptable-match: 2 / 4.

Classification hits: 2 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 5. I did not price Snorlax's Fire Blast
coverage into the expected Cloyster answer.

Main improvement:

- Turn 6 p1 transferred the support order: damaged Cloyster still set Spikes
  before considering Explosion.

Main errors:

- Turn 5 p1: expected Roar or Snorlax from the Electric side, but the actual
  side-known answer was Cloyster.
- Turn 5 p2: underpriced Fire Blast as a coverage reveal into that answer.
- Turn 6 p2: after revealing Fire Blast, I expected Snorlax to keep attacking,
  but the actual line pivoted sleeping Moltres into Cloyster to preserve
  Snorlax from Explosion while accepting Spikes.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Classification |
|---|---|---|---|---|---|
| 5 | Electric with Thunderbolt vs Snorlax 84; p2 Moltres asleep | p1 Roar if available or switch Snorlax; p2 Curse / Double-Edge | p1 switched Cloyster; p2 Fire Blast | both miss | Coverage reveal into side-known answer. |
| 6 | Cloyster 47 vs Snorlax 90 with Fire Blast revealed | p1 Spikes; p2 Fire Blast | p2 switched sleeping Moltres; p1 Spikes | p1 top, p2 acceptable | Hazard progress plus sleeping absorber to preserve Snorlax. |

## Reusable Lessons

Coverage reveal is not only an attack; it changes the whole answer map. Once
Snorlax showed Fire Blast into Cloyster, Cloyster was no longer a clean hard
answer, but it could still deliver Spikes before being removed.

After coverage is revealed, the coverage user may need protection from the
support piece's cash-out. Snorlax did not simply keep clicking Fire Blast into
Cloyster. It pivoted to sleeping Moltres, accepting the Spikes layer while
protecting Snorlax from Explosion.

## Next Rep

Build a small regression:

- Snorlax reveals Fire Blast into Cloyster: old hard-answer map is invalid.
- Cloyster survives at mid HP: set Spikes before Explosion if the layer changes
  the route.
- Snorlax after revealing Fire Blast: pivot to a lower-value sleeping absorber
  if Cloyster's Explosion would remove the Snorlax route.
