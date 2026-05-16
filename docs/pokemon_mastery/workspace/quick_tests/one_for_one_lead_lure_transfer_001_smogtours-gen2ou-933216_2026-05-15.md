# One-For-One Lead Lure Transfer 001 - 2026-05-15

Source:
- Replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-933216
- Log: https://replay.pokemonshowdown.com/smogtours-gen2ou-933216.log

Mode: spectator public.

Contamination control: current Showdown search metadata was used only to pick
an unused replay. Raw log turns were revealed through the helper one turn at a
time. The replay ended after turn 7.

Pre-freeze packet:
- `active_context.md`
- `live_core.md`
- `replay_turn_pause_protocol.md`
- `heuristic_core/role_package_ledger.md`
- `heuristic_core/public_info_tiers.md`
- `heuristic_core/name_next_board_owner.md`
- `heuristic_core/branch_punish_ranking.md`

Post-score sources:
- Smogon GSC Jynx analysis: Jynx's OU value is Lovely Kiss plus strong Ice/Psychic pressure.
- Smogon Exeggutor overview: Exeggutor's GSC identity includes sleep, status,
  and Explosion.
- Smogon Forretress revamp: Toxic and Giga Drain are real Forretress tools in
  the Cloyster/Forretress hazard fight.

## Score Summary

Decisions: 13.

Top-match: 5/13.

Acceptable-match: 10/13.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 12/13.

Route-converting move chosen: 10/13.

Branch-punish chosen: 8/13.

Role-package update obeyed: 7/9 relevant package decisions.

Earliest meaningful error: turn 1 p1. I protected Exeggutor from Jynx's sleep
route, but the replay converted the lead immediately with Explosion after
Lovely Kiss missed. That is a high-risk one-for-one route, not a default line.

## Turn Notes

| Turn | Side | Frozen route | Actual | Grade |
| --- | --- | --- | --- | --- |
| 1 | p1 | switch sleep absorber; Sleep Powder; pressure | Explosion | miss |
| 1 | p2 | Lovely Kiss; Ice Beam; Thief | Lovely Kiss | top |
| 2 | p1 | Thunder in Zapdos mirror | Thunder | top |
| 2 | p2 | Thunder in Zapdos mirror | Thunder | top |
| 3 | p1 | Thunder; Hidden Power; switch | Hidden Power | acceptable |
| 3 | p2 | Rest if RestTalk; fallback Snorlax/Raikou switch | Snorlax | acceptable |
| 4 | p1 | Normal-answer switch | Cloyster | top by class |
| 4 | p2 | attack/Curse with Snorlax | Forretress | miss |
| 5 | p1 | Spikes; Surf; Explosion | Surf | acceptable |
| 5 | p2 | Rapid Spin; Spikes; Toxic/Explosion | Toxic | acceptable |
| 6 | p1 | Surf to pressure Forretress | Surf | top |
| 6 | p2 | Spikes; switch; Explosion | Giga Drain | miss |
| 7 | p1 | Explosion; Surf; switch | Surf | acceptable |

## Reusable Lesson

One-for-one lead trades are a real route only when explicitly priced as a
high-risk branch. Jynx's Lovely Kiss route remains the public default, but if a
slower support lead stays in, Explosion can be the route-converting punish only
when the miss or immediate trade is acceptable.

Forretress is not only Spikes/Spin. After Toxic or Giga Drain appears, update
the package to `lure + hazard control`; Surf pressure from Cloyster can be a
route-converting move before generic Spikes.
