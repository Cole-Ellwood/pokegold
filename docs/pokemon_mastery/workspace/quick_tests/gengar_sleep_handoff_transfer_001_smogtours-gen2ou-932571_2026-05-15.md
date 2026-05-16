# Gengar Sleep Handoff Transfer 001 - 2026-05-15

Source:
- Replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-932571
- Log: https://replay.pokemonshowdown.com/smogtours-gen2ou-932571.log

Mode: spectator public.

Contamination control: current Showdown search metadata was used only to pick
an unused replay. Raw log turns were revealed through the helper one turn at a
time. Stopped after turn 12 at 24 scored side decisions and a repeated
voluntary-entry/hidden-coverage overread.

Pre-freeze packet:
- `active_context.md`
- `live_core.md`
- `replay_turn_pause_protocol.md`
- `heuristic_core/role_package_ledger.md`
- `heuristic_core/public_info_tiers.md`
- `heuristic_core/name_next_board_owner.md`
- `heuristic_core/branch_punish_ranking.md`

Post-score sources:
- Smogon GSC Spikes article: Cloyster, Forretress, Rapid Spin, Pursuit, and
  Electric handoffs form recurring route loops.
- Smogon GSC Cloyster analysis: Cloyster's Spikes, Surf, Rapid Spin, and
  Explosion create offense-enabling pressure.

## Score Summary

Decisions: 24.

Top-match: 10/24.

Acceptable-match: 19/24.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 2.

Mechanics errors: 0.

Positive-selection: 21/24.

Route-converting move chosen: 18/24.

Branch-punish chosen: 15/24.

Role-package update obeyed: 14/18 relevant package decisions.

Earliest meaningful error: turn 1 p2. I named Ghost as a self-destruct branch
but did not promote Gengar as the Snorlax-mirror counter-handoff.

## Turn Notes

| Turn | Side | Frozen route | Actual | Grade |
| --- | --- | --- | --- | --- |
| 1 | p1 | Double-Edge; Curse; high-risk Lovely Kiss | Double-Edge | top, branch miss |
| 1 | p2 | Double-Edge; Curse; high-risk Lovely Kiss | Gengar | miss |
| 2 | p1 | switch to Gengar owner | Umbreon | top by class |
| 2 | p2 | Hypnosis/Explosion/coverage with Gengar | Exeggutor | miss |
| 3 | p1 | Toxic; sleep absorber; Pursuit | Pursuit | acceptable |
| 3 | p2 | Sleep Powder | Sleep Powder | top |
| 4 | p1 | switch after Umbreon takes sleep | Snorlax | top |
| 4 | p2 | switch/Explosion; active coverage | Hidden Power | acceptable |
| 5 | p1 | switch Explosion absorber | Forretress | top by class |
| 5 | p2 | Explosion after sleep job | Explosion | top |
| 6 | p1 | switch Golem owner; Giga Drain; Spikes | Toxic | miss |
| 6 | p2 | Fire Blast if carried; Earthquake fallback | Earthquake | acceptable |
| 7 | p1 | Spikes; Explosion; switch | Dragonite | acceptable, not top |
| 7 | p2 | Earthquake | Earthquake | top |
| 8 | p1 | Dragonite coverage into Golem | Forretress | miss, hidden-info error |
| 8 | p2 | switch to special/Normal owner | Gengar | acceptable |
| 9 | p1 | switch Gengar owner; Spikes as last job | Spikes | acceptable |
| 9 | p2 | Thunderbolt/Fire Punch pressure | Thunderbolt | top |
| 10 | p1 | switch Gengar owner | Umbreon | top |
| 10 | p2 | Thunderbolt | Thunderbolt | top |
| 11 | p1 | stay/burn sleep as Gengar owner | Dragonite | acceptable |
| 11 | p2 | switch out of Umbreon | Cloyster | acceptable |
| 12 | p1 | Dragonite coverage if side-known; fallback switch | Raikou | acceptable, hidden-info error |
| 12 | p2 | Ice Beam; switch; Rapid Spin | Spikes | miss |

## Reusable Lesson

The repaired role ledger works when the package is public: Gengar's Normal
immunity led to Umbreon, Umbreon taking sleep led to a Snorlax handoff, and
Forretress correctly absorbed Exeggutor's Explosion.

The remaining failure is voluntary-entry overread. Dragonite entering Golem and
then Cloyster did not prove hidden coverage. It could be:

```text
direct coverage owner / absorber / bait-handoff into the real owner
```

Do not let "it entered, so it must have coverage" outrank the public handoff
unless the move is revealed, side-known, or explicitly marked as a read with a
fallback.
