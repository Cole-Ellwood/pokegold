# Post-CurseBoom Repair Transfer 002 - 2026-05-15

Source:
- Replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-931584
- Log: https://replay.pokemonshowdown.com/smogtours-gen2ou-931584.log

Mode: spectator public.

Contamination control: selected from current Showdown search metadata after
local `rg` found no prior use of `931584`. Raw log turns were revealed through
the helper one turn at a time. Stopped after turn 11 because the same
Spikes/Spin branch error appeared multiple times.

Pre-freeze packet:
- `active_context.md`
- `live_core.md`
- `replay_turn_pause_protocol.md`
- `heuristic_core/role_package_ledger.md`
- `heuristic_core/reset_loop_denial.md`
- `heuristic_core/public_info_tiers.md`
- `heuristic_core/name_next_board_owner.md`
- `heuristic_core/branch_punish_ranking.md`

Post-score source:
- Smogon's GSC Spikes article: Cloyster, Forretress, and Starmie are the main
  Spikes/Rapid Spin pieces; Gengar and Misdreavus are the spinblockers. Gengar
  pairs with Forretress by blocking Spin from Cloyster and opposing Forretress.

## Score Summary

Scored decisions: 21. Turn 2 p2 was excluded because full paralysis prevented
the chosen move from being logged.

Top-match: 7/21.

Acceptable-match: 15/21.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 18/21.

Route-converting move chosen: 14/21.

Branch-punish chosen: 10/21.

Role-package update obeyed: 10/15 relevant package decisions.

Earliest meaningful error: turn 1 p2. I named the common Snorlax/Ground
handoff into Raikou but missed Exeggutor as the status/explosion owner.

Stop condition: repeated Spikes/Spin branch miss on turns 5, 6, and 10. I kept
ranking Rapid Spin as if the opponent would leave the spinner matchup static,
while the actual route used Spikes, Toxic, Zapdos pressure, and Gengar
spinblock timing.

## Turn Notes

| Turn | Side | Frozen route | Actual | Grade |
| --- | --- | --- | --- | --- |
| 1 | p1 | Thunder | Thunder | top |
| 1 | p2 | switch Snorlax/Ground owner | Exeggutor | acceptable |
| 2 | p1 | switch sleep/boom absorber | Thunder | acceptable |
| 2 | p2 | excluded, full paralysis | full paralysis | unscored |
| 3 | p1 | switch sleep/boom absorber | Thunder | acceptable |
| 3 | p2 | Explosion / Sleep Powder | Explosion | top |
| 4 | p1 | attack with Snorlax | Forretress | miss |
| 4 | p2 | Spikes; Explosion; Toxic | Toxic | acceptable |
| 5 | p1 | Rapid Spin to deny likely Spikes | Spikes | acceptable, branch miss |
| 5 | p2 | Spikes | Spikes | top |
| 6 | p1 | Rapid Spin | Toxic | miss, branch miss |
| 6 | p2 | Rapid Spin / Surf | Zapdos | miss |
| 7 | p1 | switch Zapdos owner | Snorlax | top |
| 7 | p2 | Thunder | Thunder | top |
| 8 | p1 | attack with Snorlax | Rest | acceptable |
| 8 | p2 | Thunder or switch Cloyster | Cloyster | acceptable |
| 9 | p1 | switch Forretress | Forretress | top |
| 9 | p2 | Explosion; Rapid Spin; Surf | Surf | acceptable |
| 10 | p1 | Rapid Spin | Spikes | miss, branch miss |
| 10 | p2 | Rapid Spin / Surf | Gengar | miss, spinblock branch |
| 11 | p1 | Toxic or switch Gengar owner | Tyranitar | acceptable |
| 11 | p2 | Thunderbolt / coverage | Thunderbolt | top |

## Reusable Lesson

Rapid Spin is not the default answer to a static hazard board. It is a branch
punish that must be ranked against the opponent's denial map:

```text
Can they switch to Gengar/Misdreavus, go to an Electric or Fire pressure owner,
or use Surf/Explosion before the Spin loop stabilizes?
```

If the denial branch is likely, Toxic, Spikes, Surf, Explosion, or the owner
handoff can be higher than blind Spin. The move that wins the Spikes loop is
the move that beats the next owner, not necessarily Rapid Spin itself.

## Restarted Sample Status

Combined restarted sample after CurseBoom repair:
- Decisions: 45
- Top-match: 18/45 = 40.0%
- Acceptable-match: 34/45 = 75.6%
- Severe/state/mechanics errors: 0
- Hidden-info errors: 1

This is flat/regressing by top-match and contains a repeated branch class.
Under the plateau loop, stop broad replay grinding and study the Spikes/Spin
branch before collecting more sample.
