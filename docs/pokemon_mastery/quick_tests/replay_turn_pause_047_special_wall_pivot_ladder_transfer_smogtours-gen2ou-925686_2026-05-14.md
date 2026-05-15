# Replay Turn-Pause 047 Special-Wall Pivot Ladder Transfer - smogtours-gen2ou-925686 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-925686`.

Mode: spectator-public vanilla GSC replay practice.

Selected measurable action: fresh transfer after
`special_wall_pivot_ladder_probe_001_2026-05-14.md`. The target was the same
ladder as `replay_turn_pause_046`, stopping after the first two meaningful
misses:

```text
direct damage / coverage into pivot / setup-status progress / double /
route denial / side-known answer / cash-out
```

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs and contaminated `934420`.
- Screening printed only replay ID, selected start turn, total turns, route
  move count, and file size.
- The selected replay was `smogtours-gen2ou-925686`.
- The selected start was turn 2. Turns 2-7 were answered before reveal.
- The run stopped after turn 7 because turns 5 and 7 were meaningful ladder
  misses.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_046_special_wall_pivot_ladder_smogtours-gen2ou-925777_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/special_wall_pivot_ladder_probe_001_2026-05-14.md`

Web sources checked:

- Smogon Forums, GSC Zapdos:
  `https://www.smogon.com/forums/threads/gsc-zapdos.3674240/`
- Smogon Forums, An Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`
- Smogon Forums, Skarmory WIP:
  `https://www.smogon.com/forums/threads/skarmory-wip.3687627/`
- Smogon Forums, GSC OU Espeon:
  `https://www.smogon.com/forums/threads/gsc-ou-espeon-qc-1-1-gp-1-1.3667456/`

Source note: the lead analysis explicitly frames Electrics as choosing between
Thunder, phazing, and double-switches into expected Snorlax or Ground-type
responses. The Zapdos source stresses that Spikes support and Snorlax pressure
are linked, but Thunder alone does not solve Snorlax. The Skarmory source
reinforces the coverage-pivot point: physical attackers with special coverage
can flip the Skarmory check.

## Score Summary

Scored decisions: 11 side decisions.

Top-match: 5 / 11.

Acceptable-match: 8 / 11.

Classification hits: 8 / 11.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 5 p1. I chose Swords Dance on the forced
Snorlax exit, but Earthquake into the Exeggutor pivot was the player line.
The setup turn would have handed Exeggutor the next threat.

Main improvement:

- The Cloyster support ladder transferred. I did not jump straight to
  Explosion: Toxic, then Spikes, then Explosion matched the support order well
  enough to keep the route coherent.

Main errors:

- Turn 2 p1: Toxic was better than my Spikes-first answer because the active
  +1 Snorlax route needed a status clock before the hazard layer.
- Turn 5 p1: setup on a forced switch was too greedy; direct damage into the
  likely physical-wall pivot was better.
- Turn 7 p1: Thunder was the wrong active attack because Steelix was a live
  pivot. Hidden Power covered the pivot while still threatening progress.
- Turn 7 p2: I overcalled Exeggutor Explosion after Stun Spore. The actual
  branch preserved Exeggutor and moved to Steelix.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Classification |
|---|---|---|---|---|---|
| 2 | Cloyster 100 vs +1 Snorlax 100 | p1 Spikes; p2 Double-Edge | p1 Toxic; p2 Double-Edge | p1 acceptable, p2 top | Setup-status progress before hazard. |
| 3 | Cloyster 55 vs toxic +1 Snorlax 93 | p1 Spikes; p2 Double-Edge | p1 Spikes; p2 Double-Edge | both top | Hazard progress after status clock. |
| 4 | Cloyster 13 vs toxic +1 Snorlax 80 | p1 Explosion; p2 unscored | p1 Explosion; p2 no logged action | p1 top | Cash-out after support delivered. |
| 5 | Marowak 100 vs toxic +1 Snorlax 27 | p1 Swords Dance; p2 physical-wall switch | p2 switched Exeggutor; p1 Earthquake | p1 miss, p2 acceptable | Direct damage into pivot beat setup. |
| 6 | Marowak 100 vs Exeggutor 66 | p1 switch Zapdos; p2 Sleep Powder | p1 switched Zapdos; p2 Stun Spore | p1 top, p2 acceptable | Side-known answer plus status progress. |
| 7 | paralyzed Zapdos 100 vs Exeggutor 73 | p1 Thunder; p2 Explosion | p2 switched Steelix; p1 Hidden Power | both miss | Coverage into Ground/Steel pivot beat active attack. |

## Reusable Lessons

The ladder needs one extra early question:

```text
Does the active route need a status clock before hazards?
```

Against a +1 Snorlax, Toxic before Spikes was the route order. The later
Explosion was correct only because Toxic and Spikes had already been delivered.

Forced switch does not automatically mean setup. If the incoming pivot threatens
status, Explosion, recovery, or an immediate answer to the setup user, direct
damage into the pivot can be the better route-preserving move. Marowak's
Earthquake into Exeggutor was not glamorous, but it denied a free entry after
Snorlax was forced out.

Electric active attacks must price Ground and Steel pivots. Thunder into
Exeggutor looked active, but Hidden Power was the move that covered the
incoming Steelix branch.

## Next Rep

Construct a small regression:

- +1 Snorlax versus Cloyster: Toxic before Spikes.
- forced Snorlax exit into Exeggutor: damage before setup.
- Zapdos versus Exeggutor with Steelix live: coverage before Thunder.
- paralyzed status spreader after status lands: preserve or pivot before
  automatic Explosion.
