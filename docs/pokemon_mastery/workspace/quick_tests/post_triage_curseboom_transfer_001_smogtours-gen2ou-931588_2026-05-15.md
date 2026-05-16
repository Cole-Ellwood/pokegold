# Post-Triage CurseBoom Transfer 001 - 2026-05-15

Source:
- Replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-931588
- Log: https://replay.pokemonshowdown.com/smogtours-gen2ou-931588.log

Mode: spectator public.

Contamination control: selected from current Showdown search metadata after
local `rg` found no prior use. Raw log turns were revealed through the helper
one turn at a time. Stopped after turn 10 at 20 side decisions.

Pre-freeze packet:
- `active_context.md`
- `live_core.md`
- `replay_turn_pause_protocol.md`
- `heuristic_core/role_package_ledger.md`
- `heuristic_core/public_info_tiers.md`
- `heuristic_core/name_next_board_owner.md`
- `heuristic_core/branch_punish_ranking.md`

Post-score sources:
- Smogon GSC move priority article: Roar and Whirlwind are `-1` priority in
  GSC, and phazing must move last to work.
- Smogon/strategy notes checked after scoring for Exeggutor, Jynx, Forretress,
  and GSC Spikes context.

## Score Summary

Decisions: 20.

Top-match: 6/20.

Acceptable-match: 15/20.

Severe blunders: 1.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 1.

Positive-selection: 17/20.

Route-converting move chosen: 14/20.

Branch-punish chosen: 12/20.

Role-package update obeyed: 14/18 relevant package decisions.

Side-known oracle gaps: 1, turn 9 p1. Snorlax's Earthquake was not public, but
once revealed it explained why staying into Golem was a side-known line.

Earliest meaningful error: turn 1 p2. I defaulted to Exeggutor sleep pressure
and missed the immediate Thief item-removal route.

Severe error: turn 5 p1. I made generic phaze the top Skarmory answer into a
boosted Snorlax, but Snorlax used Self-Destruct. Because Roar/Whirlwind have
negative priority in GSC, a phaze line would eat the explosion before acting;
the actual Curse boosted Skarmory's Defense and let it survive.

## Turn Notes

| Turn | Side | Frozen route | Actual | Grade |
| --- | --- | --- | --- | --- |
| 1 | p1 | Hidden Power if carried; switch if no coverage | Hidden Power | top |
| 1 | p2 | Sleep Powder; status; Explosion/switch | Thief | miss |
| 2 | p1 | Hidden Power; switch boom absorber | Golem | acceptable |
| 2 | p2 | Sleep Powder; Explosion | Explosion | acceptable |
| 3 | p1 | Explosion; Earthquake; switch if preserving Golem | Cloyster | acceptable |
| 3 | p2 | switch absorber; coverage; Curse | Curse | acceptable |
| 4 | p1 | Explosion/Toxic/Spikes with Cloyster | Skarmory | miss |
| 4 | p2 | switch boom absorber; attack; Curse | Curse | acceptable |
| 5 | p1 | Whirlwind/phaze; Toxic; Drill Peck | Curse | severe, mechanics |
| 5 | p2 | coverage/switch; Curse/Rest | Self-Destruct | miss |
| 6 | p1 | switch Electric owner | Raikou | top by class |
| 6 | p2 | Hidden Power into Golem/Raikou branch | Hidden Power | top |
| 7 | p1 | Thunderbolt | Thunderbolt | top |
| 7 | p2 | switch Raikou owner | Espeon | acceptable |
| 8 | p1 | Thunderbolt; switch Snorlax if Psychic/setup | Snorlax | acceptable |
| 8 | p2 | Morning Sun/Growth; switch | Golem | miss |
| 9 | p1 | switch Explosion absorber; EQ if side-known | Earthquake | acceptable, oracle gap |
| 9 | p2 | Explosion; Earthquake | Earthquake | acceptable |
| 10 | p1 | switch Explosion absorber | Skarmory | top |
| 10 | p2 | Explosion | Explosion | top |

## Reusable Lesson

Phaze is not a magic reset into boosted Self-Destruct. Before ranking Roar or
Whirlwind, ask:

```text
Does the phazer survive the hit or Self-Destruct that moves before negative-
priority phaze? Would Curse, switch, Protect-style scout, or a resist/sack
preserve the route better?
```

This packet started after the voluntary-entry drill, but it is not progress:
the new triage helped on turns 6 and 10, while a different severe
mechanics/route error appeared.
