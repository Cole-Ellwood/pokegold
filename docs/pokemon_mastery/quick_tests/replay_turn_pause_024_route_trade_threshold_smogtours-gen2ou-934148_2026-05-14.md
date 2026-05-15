# Replay Turn-Pause 024 Route Trade Threshold - smogtours-gen2ou-934148 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-934148`.

Mode: spectator public, semi-blind candidate-screened.

Purpose: fresh transfer test for
`route_trade_active_pressure_probe_001`: price Explosion/Self-Destruct as a
route trade without overcalling blind or premature cash-outs.

Contamination control:

- The replay was not referenced in local docs before this run.
- A local candidate screen checked only broad move and Pokemon-name presence
  across unused logs: Explosion, Self-Destruct, Snorlax, Exeggutor, Cloyster,
  Gengar, Forretress, Steelix, Zapdos, Raikou, Curse, Rest, and Sleep Talk.
- The screen did not reveal turn number, actor, target, move order, outcome, or
  later branches.
- Turns were revealed one at a time with the local helper after answers were
  frozen.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/route_trade_active_pressure_probe_001_smogtours-gen2ou-934329_2026-05-14.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- Smogon Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon GSC Zapdos:
  `https://www.smogon.com/forums/threads/gsc-zapdos.3674240/`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

Source note: the sources support Explosion/Self-Destruct as a route trade into
major blockers such as CurseLax, Zapdos, or Raikou, but this replay tested the
timing boundary: status, Spikes, absorber pivots, and target selection can
come before the final trade.

## Score Summary

Turns scored: 1-9.

Target phase: turns 3-9, where Exeggutor, Cloyster, and Snorlax each created
one-time-trade questions.

Decisions scored: 18 side-decisions.

Top-match: 7 / 18.

Acceptable-match: 13 / 18.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful context error: turn 1.

Earliest target error: turn 3.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 1 | Zapdos lead vs Exeggutor | p1 attack with Hidden Power or use a sleep-absorber switch; p2 Sleep Powder/Stun pressure | p1 Raikou switch; p2 Thief | p1 acceptable, p2 miss | Exeggutor led with item disruption, not immediate status. |
| 2 | Raikou 91 vs Exeggutor | p1 direct Electric coverage pressure; p2 status/switch/damage | p1 Hidden Power; p2 Psychic | p1 acceptable, p2 miss | Raikou attacking was right; Exeggutor chose damage before trade. |
| 3 | Raikou 59 vs Exeggutor 63 | p1 Hidden Power; p2 Explosion into active Electric | p2 Snorlax switch; p1 Hidden Power | p1 top, p2 miss | Overcall: Exeggutor did not need to trade because Snorlax could absorb Raikou. |
| 4 | Raikou 59 vs Snorlax 95 | p1 switch to a physical answer; p2 Curse or direct pressure | p1 Cloyster; p2 Curse | both top | Correctly saw the Snorlax route start and the need to answer physically. |
| 5 | Cloyster 100 vs +1 Snorlax | p1 Explosion with Toxic as alternative; p2 attack or continue Curse | p1 Toxic; p2 Curse | both acceptable | Overcall: status was the first route-changing answer to CurseLax. |
| 6 | Cloyster 100 vs +2 poisoned Snorlax | p1 Explosion with Spikes as alternative; p2 Rest or attack | p1 Spikes; p2 Double-Edge | p1 acceptable, p2 top | Overcall again: after Toxic, field state came before the cash-out. |
| 7 | Cloyster 40 vs +2 poisoned Snorlax 85 | p1 Explosion; p2 Double-Edge | p1 Tyranitar; p2 Double-Edge | p1 miss, p2 top | The correct route preserved low Cloyster and used a Normal resist while poison/recoil advanced. |
| 8 | Tyranitar 71 vs +2 poisoned Snorlax 66 | p1 switch/absorb while pricing Earthquake; p2 Earthquake | p1 Zapdos; p2 Earthquake immune | p1 acceptable, p2 top | Good branch pricing: the route was absorber cycling, not immediate trade. |
| 9 | Zapdos 100 vs +2 poisoned Snorlax 48 | p1 Thunderbolt; p2 Rest or switch | p1 Thunderbolt; p2 Self-Destruct KOed both | p1 top, p2 miss | Under-correction: the trade became correct once Zapdos was the active target and Toxic/Spikes/recoil had done their work. |

## Error Classes

- Premature trade overcall: turns 3, 5, 6, and 7 show I turned "Explosion is
  live" into "Explosion is best" too quickly.
- Delayed cash-out miss: turn 9 shows the opposite boundary. After Toxic,
  Spikes, recoil, and absorber cycling, Snorlax's Self-Destruct into Zapdos
  was the exact active-target trade.
- Status and hazard sequencing improved the route before the trade. Toxic
  changed Snorlax's clock, Spikes made future switches worse, and Tyranitar /
  Zapdos absorbed the correct attack classes.
- No severe blunder: my p1 lines usually preserved or attacked acceptably, but
  the p2 route-trade timing was weak.

## Policy Update

Add to route-trade policy: an active route threat does not automatically mean
cash out on the first legal turn. Ask whether status, Spikes, or a lower-cost
absorber can make the later trade cleaner. The cash-out threshold is reached
when the active target is exact, the user's prior jobs are delivered, and
delaying gives the opponent a reset or escape.

## Next Study Target

Run a smaller transfer probe that forces the distinction among Toxic first,
Spikes first, absorber pivot, and immediate Explosion into a boosting Snorlax
or active Electric.
