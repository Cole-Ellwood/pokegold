# Replay Turn-Pause 046 Special-Wall Pivot Ladder - smogtours-gen2ou-925777 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-925777`.

Mode: spectator-public vanilla GSC replay practice.

Selected measurable action: fresh transfer after
`replay_turn_pause_045_sleep_clause_clamp_explosion_growth_smogtours-gen2ou-927169_2026-05-14.md`.
The target was a short segment around special attackers, special-wall pivots,
coverage, setup/status, and doubles.

Forced classification:

```text
direct damage / coverage into pivot / setup-status progress / double /
route denial / side-known answer / cash-out
```

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs and contaminated `934420`.
- Screening printed only replay ID, selected start turn, total turns, route
  move count, and file size.
- The selected replay was `smogtours-gen2ou-925777`.
- The selected start was turn 3. Turns 3-12 were answered before reveal.
- The helper prompt does not expose unrevealed own-team members, so
  side-known player switches are graded as side-known answers when the
  spectator-public prompt could not prove them.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_045_sleep_clause_clamp_explosion_growth_smogtours-gen2ou-927169_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/pivot_progress_after_gate_probe_001_2026-05-14.md`

Web sources checked:

- Smogon Forums, GSC OU Espeon:
  `https://www.smogon.com/forums/threads/gsc-ou-espeon-qc-1-1-gp-1-1.3667456/`
- Smogon Forums, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon Forums, GSC Teambuilding Compendium:
  `https://www.smogon.com/forums/threads/gsc-teambuilding-compendium.3547538/`
- Smogon Forums, GSC Mechanics:
  `https://www.smogon.com/forums/threads/gsc-mechanics.3542417/`

Source note: the Espeon source supports Growth as a real special-attacker
progress move, the compendium lists Growthers and special-wall classes, and
the Snorlax source reinforces Snorlax as a central offensive and defensive
presence rather than a passive wall. The local replay added the missing ladder:
direct damage, coverage into the pivot, setup/status into the pivot, double,
then route denial or cash-out if the active route has already become urgent.

## Score Summary

Scored decisions: 20 side decisions.

Top-match: 7 / 20.

Acceptable-match: 10 / 20.

Classification hits: 10 / 20.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 4 p1. I identified the sleeping Raikou absorber
branch but did not make the Snorlax double the top line.

Main improvement:

- Turn 10 transferred the active-progress lesson: Cloyster used Spikes into a
  +1 Snorlax rather than immediately exploding or attacking, and the layer
  changed the following switch/route map.

Main errors:

- Turn 4 p1: active Raikou's Thunder was easy to cover with the already
  sleeping Raikou absorber, so the player doubled to Snorlax. I left that as a
  fallback instead of the top line.
- Turn 5 p1: missed that Snorlax's revealed coverage slot could be Thunder to
  punish the obvious Skarmory wall pivot.
- Turns 6-8: under-followed the double chain. Both players kept moving between
  special attackers, special walls, and the sleeping Raikou absorber instead
  of taking the most visible active-target exchange.
- Turns 11-12: overcalled Explosion after Spikes were delivered. The actual
  line preserved Cloyster, used Golem as the side-known answer, then Roared
  rather than cashing out.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Classification |
|---|---|---|---|---|---|
| 3 | Exeggutor 88 vs Skarmory 84; p2 Raikou asleep | p1 Psychic or side-known Electric switch; p2 Toxic | p1 switched Raikou; p2 Toxic | p1 acceptable, p2 top | Side-known answer plus setup-status progress. |
| 4 | poisoned p1 Raikou 100 vs Skarmory 90 | p1 Roar if available / Thunder fallback; double Snorlax as alt; p2 switch sleeping Raikou | both switched: p1 Snorlax, p2 sleeping Raikou | p1 acceptable, p2 top | Active attack was covered; double should have been top. |
| 5 | Snorlax 100 vs sleeping Raikou 100 | p1 Curse; p2 switch Skarmory | p2 switched Skarmory; p1 Thunder missed | p1 miss, p2 top | Coverage into pivot beat generic active progress. |
| 6 | Snorlax 100 with Thunder vs Skarmory 96 | p1 Thunder; p2 stay and Toxic/Whirlwind | both switched: p1 Raikou, p2 Tyranitar | both miss | Double-chain branch missed. |
| 7 | poisoned p1 Raikou 94 vs Tyranitar 100 | p1 switch Snorlax; p2 stay and punish | p2 switched sleeping Raikou; p1 Thunder | both miss | Sleeping absorber branch re-entered immediately. |
| 8 | poisoned p1 Raikou 88 vs sleeping p2 Raikou 87 | p1 switch Snorlax; p2 switch Tyranitar | both switched Snorlax | p1 top, p2 acceptable | Special-wall double, wrong p2 identity. |
| 9 | Snorlax mirror | p1 Curse/attack; p2 Lovely Kiss if available | p1 switched Cloyster; p2 Curse | both miss | Side-known answer and setup progress missed. |
| 10 | Cloyster 100 vs +1 Snorlax 100 | p1 Spikes; p2 switch Skarmory | p1 Spikes; p2 Double-Edge | p1 top, p2 miss | Active progress through pressure. |
| 11 | Cloyster 56 vs +1 Snorlax 99 with Spikes up | p1 Explosion; p2 Double-Edge | p1 switched Golem; p2 Double-Edge | p1 miss, p2 top | Side-known recurring answer beat cash-out. |
| 12 | Golem 80 vs +1 Snorlax 100 | p1 Explosion; p2 Double-Edge | p2 Double-Edge; p1 Roar to Forretress | p1 miss, p2 top | Route denial beat cash-out. |

## Reusable Lesson

Use a ladder after a special attacker or special wall enters:

1. Is direct damage only hitting the current target, and is the response
   already revealed? If yes, consider the double.
2. Does the active Pokemon have coverage that punishes the expected pivot? If
   yes, coverage can beat generic setup.
3. Does setup or status make the expected pivot worse next turn? If yes, use
   active progress rather than doubling by habit.
4. If a route is already active, ask whether a recurring answer can deny it
   before spending Explosion or another one-time cash-out.
5. When a sleeping absorber is already established, keep pricing its re-entry
   as an active branch, not just as a passive sleep-clause fact.

## Next Rep

Construct a compact regression from this segment:

- Electric into known sleeping Electric absorber: double to wall.
- Snorlax with coverage into Skarmory: use coverage, not generic Curse.
- Cloyster after Spikes into +1 Snorlax: preserve if a recurring phazer exists.
- Golem into +1 Snorlax: Roar before Explosion when phazing is reliable.
