# Post-Spin Branch Repair Transfer 001 - 2026-05-15

Source:
- Replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-930694
- Log: https://replay.pokemonshowdown.com/smogtours-gen2ou-930694.log

Mode: spectator public.

Contamination control: selected from current Showdown search metadata after
local `rg` found no prior use of `930694`. Raw log turns were revealed through
the helper one turn at a time. Stopped after turn 12 at 24 scored side
decisions.

Pre-freeze packet:
- `active_context.md`
- `live_core.md`
- `replay_turn_pause_protocol.md`
- `heuristic_core/role_package_ledger.md`
- `heuristic_core/reset_loop_denial.md`
- `heuristic_core/public_info_tiers.md`
- `heuristic_core/name_next_board_owner.md`
- `heuristic_core/branch_punish_ranking.md`

Post-score sources:
- Smogon GSC Spikes article: Cloyster supplies Spikes, Surf, and Explosion;
  the Spikes game depends on pressure and denial maps, not just Spin.
- Smogon GSC threatlist/introduction material: Steelix gives Roar and
  Explosion support while checking Electric routes, and Machamp can pressure
  with Cross Chop plus coverage such as Fire Blast.

## Score Summary

Decisions: 24.

Top-match: 13/24.

Acceptable-match: 23/24.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 23/24.

Route-converting move chosen: 20/24.

Branch-punish chosen: 17/24.

Role-package update obeyed: 18/21 relevant package decisions.

Earliest meaningful error: turn 1 p1. I ranked Spikes above Toxic in the
Cloyster mirror; Toxic was acceptable but not the actual first converter.

Repeated-error check:
- Blind Rapid Spin ranking: 0.
- Voluntary-entry hidden-coverage overread: 0.
- Boom-before-phaze survival miss: 0.

This is sample 1 after the Spikes/Spin repair. It is a limited positive
transfer, not progress proof.

## Turn Notes

| Turn | Side | Frozen route | Actual | Grade |
| --- | --- | --- | --- | --- |
| 1 | p1 | Spikes; Toxic; Surf/coverage | Toxic | acceptable |
| 1 | p2 | Spikes; Toxic; Surf/coverage | Spikes | top |
| 2 | p1 | Spikes | Spikes | top |
| 2 | p2 | Toxic | Toxic | top |
| 3 | p1 | switch pressure owner; Surf; Explosion/Spin if side-known | Surf | acceptable |
| 3 | p2 | switch Electric/special owner | Raikou | top by class |
| 4 | p1 | switch Electric absorber | Steelix | top by class |
| 4 | p2 | Thunder | Thunder | top |
| 5 | p1 | Roar with Spikes; Earthquake; Explosion | Roar | top |
| 5 | p2 | switch owner out of Steelix | Heracross | top by class |
| 6 | p1 | Roar; Earthquake; Explosion | Earthquake | acceptable |
| 6 | p2 | switch pressure owner out of Steelix | Machamp | acceptable |
| 7 | p1 | switch off Machamp while preserving Steelix | Cloyster | acceptable |
| 7 | p2 | Cross Chop / coverage into Steelix branch | Fire Blast | acceptable |
| 8 | p1 | Explosion with spent poisoned Cloyster | Explosion | top |
| 8 | p2 | attack; switch boom absorber branch | Cloyster | acceptable |
| 9 | p1 | Cross Chop | Cross Chop | top |
| 9 | p2 | switch absorber; Cross Chop | Cross Chop | acceptable |
| 10 | p1 | Cross Chop | Cross Chop | top |
| 10 | p2 | switch or attack if sacking Machamp | Cross Chop | acceptable |
| 11 | p1 | switch Electric absorber | Steelix | top by class |
| 11 | p2 | switch punish; Thunder if Machamp stays | Thunder | acceptable |
| 12 | p1 | Earthquake; Roar; Explosion | Roar | acceptable |
| 12 | p2 | switch out of Steelix | Heracross | top by class |

## Reusable Lesson

The Spikes/Spin repair held because no Rapid Spin line was ranked without first
naming denial. In Cloyster mirror and Forretress-style positions, the live
question should stay:

```text
What wins the next owner map: Toxic, Spikes, Surf, Explosion, Spin, or handoff?
```

The Steelix sequence was better than prior samples because Roar and Earthquake
were both evaluated as route converters rather than scripts. Roar converted
when the switch branch was broad; Earthquake was acceptable when the incoming
owner was grounded and needed chip.

Do not overclaim: the packet is short and exact top-match is still just below
the primary proof target.
