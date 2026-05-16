# Post-Spin Branch Repair Transfer 003 - 2026-05-15

Source:
- Replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-928158
- Log: https://replay.pokemonshowdown.com/smogtours-gen2ou-928158.log

Mode: spectator public.

Contamination control: selected from current Showdown search metadata after
local `rg` found no prior use of `928158`. Raw log turns were revealed through
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
- Smogon GSC Spikes article: Cloyster, Forretress, Starmie, Gengar, and
  Misdreavus define much of the Spikes/Spin ownership map.
- Smogon GSC lead analysis: Electrics can pressure Cloyster but should also
  price Snorlax/Ground/Raikou/Cloyster double-switch owner maps.

## Score Summary

Decisions: 24.

Top-match: 13/24.

Acceptable-match: 23/24.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 21/24.

Route-converting move chosen: 19/24.

Branch-punish chosen: 15/22.

Role-package update obeyed: 17/21 relevant package decisions.

Earliest meaningful error: turn 3 p1. I ranked Earthquake from Steelix before
the double-switch owner map, while the replay had both sides leave for
Cloyster.

Repeated-error check:
- Blind Rapid Spin ranking: 0.
- Voluntary-entry hidden-coverage overread: 0.
- Boom-before-phaze survival miss: 0.

## Turn Notes

| Turn | Side | Frozen route | Actual | Grade |
| --- | --- | --- | --- | --- |
| 1 | p1 | Thunder; double-switch fallback | Thunder | top |
| 1 | p2 | switch Electric/Snorlax/Ground owner | Raikou | top by class |
| 2 | p1 | switch Electric absorber | Steelix | top by class |
| 2 | p2 | Thunder | Thunder | top |
| 3 | p1 | Earthquake; Roar; switch owner | Cloyster | acceptable |
| 3 | p2 | switch Cloyster/water owner | Cloyster | top by class |
| 4 | p1 | Toxic; Spikes; Surf | Spikes | acceptable |
| 4 | p2 | Toxic | Toxic | top |
| 5 | p1 | Toxic | Toxic | top |
| 5 | p2 | Spikes | Spikes | top |
| 6 | p1 | switch pressure/spinner owner | Starmie | acceptable |
| 6 | p2 | switch Electric owner | Raikou | top by class |
| 7 | p1 | switch Electric absorber/special owner | Snorlax | acceptable |
| 7 | p2 | Thunder | Thunder | top |
| 8 | p1 | Double-Edge | Double-Edge | top |
| 8 | p2 | Thunder or switch absorber | Cloyster | acceptable |
| 9 | p1 | switch boom absorber | Cloyster | acceptable |
| 9 | p2 | Explosion/Surf; avoid dead Toxic | Toxic | miss |
| 10 | p1 | Surf | Surf | top |
| 10 | p2 | switch pressure/spinblock owner | Gengar | acceptable |
| 11 | p1 | Surf; switch Pursuit/Dark owner | Tyranitar | acceptable |
| 11 | p2 | Thunderbolt/coverage; item utility | Thief | acceptable |
| 12 | p1 | Pursuit | Pursuit | top |
| 12 | p2 | switch; Thunderbolt/coverage if staying | Thunderbolt | acceptable |

## Reusable Lesson

The repaired Spikes/Spin rule held again: no Rapid Spin was recommended without
first naming spinblock and pressure-owner denial.

The remaining weakness is now first-cycle double-switch ownership. The correct
live question is not only "what beats the active target," but:

```text
If both active Pokemon have obvious answers, which owner pair appears next, and
does my move punish that owner pair or only the starting board?
```

Do not turn this into another broad note. The current structure is sufficient;
the next proof needs replication on fresh packets.
