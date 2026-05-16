# Post-Spin Branch Repair Transfer 002 - 2026-05-15

Source:
- Replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-930575
- Log: https://replay.pokemonshowdown.com/smogtours-gen2ou-930575.log

Mode: spectator public.

Contamination control: selected from current Showdown search metadata after
local `rg` found no prior use of `930575`. Raw log turns were revealed through
the helper one turn at a time. Stopped after turn 12 at 21 scored side
decisions; p2 turns 3-5 were unscored because Cloyster was asleep and no chosen
move was logged.

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
- Smogon lead analysis: early GSC Snorlax can threaten many lines, including
  Lovely Kiss, Double-Edge + coverage, status, Curse, and Self-Destruct.
- Smogon sample teams/Zapdos notes: Zapdos/Raikou pressure with Spikes forces
  switch ownership and makes Ground/Rock answers such as Rhydon relevant.

## Score Summary

Scored decisions: 21.

Top-match: 12/21.

Acceptable-match: 19/21.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 18/21.

Route-converting move chosen: 16/21.

Branch-punish chosen: 12/18.

Role-package update obeyed: 14/17 relevant package decisions.

Side-known oracle gaps: 2. Turn 2 p1 Lovely Kiss Snorlax and turn 10 p1 exact
Raikou handoff were not public in spectator mode, but were coherent from the
player's side-known set/team.

Earliest meaningful error: turn 1 p1. I stayed on the active Zapdos pressure
script instead of pricing the double-switch owner map: Zapdos leaving for
Snorlax while Cloyster leaves for Raikou.

Repeated-error check:
- Blind Rapid Spin ranking: 0.
- Voluntary-entry hidden-coverage overread: 0. Hidden Power was treated as a
  revealed/side-known branch after it appeared, not as proof before reveal.
- Boom-before-phaze survival miss: 0.

This is sample 2 after the Spikes/Spin repair. It is not progress proof because
the sample gate requires three fresh packets or 90 decisions.

## Turn Notes

| Turn | Side | Frozen route | Actual | Grade |
| --- | --- | --- | --- | --- |
| 1 | p1 | Thunder/active pressure | Snorlax | miss |
| 1 | p2 | switch Electric/Snorlax/Ground owner | Raikou | top by class |
| 2 | p1 | Double-Edge/Body Slam; coverage/setup | Lovely Kiss | miss, oracle gap |
| 2 | p2 | switch physical/sleep absorber owner | Cloyster | top by class |
| 3 | p1 | Curse; Double-Edge; switch | Double-Edge | acceptable |
| 4 | p1 | Double-Edge | Double-Edge | top |
| 5 | p1 | switch boom absorber; Double-Edge | Double-Edge | acceptable |
| 6 | p1 | Double-Edge | Double-Edge | top |
| 6 | p2 | switch Normal resist/owner | Rhydon | top by class |
| 7 | p1 | switch Rhydon owner | Cloyster | top by class |
| 7 | p2 | Rock Slide into Zapdos/Cloyster branch | Rock Slide | top |
| 8 | p1 | Surf; Spikes; Toxic | Spikes | acceptable |
| 8 | p2 | switch owner; Rock Slide | Rock Slide | acceptable |
| 9 | p1 | Surf | Surf | top |
| 9 | p2 | switch Electric/Flying owner | Zapdos | top by class |
| 10 | p1 | switch special/Electric owner | Raikou | acceptable, oracle gap |
| 10 | p2 | Thunder | Thunder | top |
| 11 | p1 | Thunder; Hidden Power if side-known | Hidden Power | acceptable |
| 11 | p2 | switch Raikou/Rhydon owner | Raikou | top by class |
| 12 | p1 | Thunder/Hidden Power pressure | Hidden Power | acceptable |
| 12 | p2 | Thunder pressure | Thunder | top |

## Reusable Lesson

The repaired Spin branch stayed clean because no Rapid Spin choice appeared
without denial pricing. The remaining misses were exact-owner and side-known
set issues:

```text
Lead Zapdos versus Cloyster is not only active Thunder pressure. If both sides
have obvious answers, price the double-switch owner map before committing.
```

Lovely Kiss Snorlax remains a side-known oracle gap in spectator mode. It
should not become a hidden-info error unless the advice assumes it as public
fact before reveal.

## Post-Repair Sample Status

Combined post-Spikes/Spin repair sample:
- Decisions: 45
- Top-match: 25/45 = 55.6%
- Acceptable-match: 42/45 = 93.3%
- Severe/hidden/state/mechanics errors: 0

This is promising but not enough. The sample still needs a third fresh packet
or a total of 90 decisions before any progress claim.
