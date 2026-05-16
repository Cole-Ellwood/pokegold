# Steelix Curse/Roar Split Transfer 001 - smogtours-gen2ou-933317 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933317`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933317.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&server=smogtours&page=3`

Mode: spectator-public no-Team-Preview turn pause. Smogtours replay, selected
from current metadata and turn count only. I did not inspect move content or
future turns before freezing answers.

Contamination control:

- Local `rg` found no prior `smogtours-gen2ou-933317` use before selection.
- The log was saved locally at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-933317.log`.
- Prompts used
  `python tools/pokemon_mastery/replay_turn_pause.py ... prompt --turn N`.
- Reveals used
  `python tools/pokemon_mastery/replay_turn_pause.py ... reveal --turn N`.
- Fresh reveals stopped at turn 11 after repeated Steelix Curse/Roar split
  misses.
- No later replay turns were inspected after stopping.

Players: p1 `exguardian`, p2 `tylerkehne`.

## Score Summary

Decisions: 22 scored, 0 unscored.

Top-match: 10/22.
Acceptable-match: 17/22.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 16/22.
Route-converting move chosen: 14/22.
Branch-punish chosen: 10/18.
Earliest meaningful error: turn 1.

Result: mixed but not progress. The run improved over the prior early stop on
top, acceptable, positive, and route metrics, but it stopped at only 22
decisions and repeated one unresolved class: under-ranking `Curse` before or
inside a Steelix `Roar` loop when Skarmory/Raikou/Tyranitar branches let the
boost convert the next board. Severe, hidden-info, state, and mechanics gates
stayed clean.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Fire/active coverage into Forretress if available; Normal STAB; Lovely Kiss/Curse with fallback | Cloyster | miss | - | Missed the opening counter-handoff to the hazard owner. |
| 1 | p2 | Spikes; Toxic/coverage; switch if fearing immediate Fire coverage | Skarmory | acceptable | P/B | Switch branch existed but was under-ranked and exact owner was hidden. |
| 2 | p1 | Spikes; Toxic/status into Skarmory; Surf/Icy Wind/Explosion if it changes next owner | Spikes | top | P/R | Correct first support job. |
| 2 | p2 | Toxic; Whirlwind; switch to Electric/Forretress owner | Toxic | top | P/R | Correct support status, though it missed. |
| 3 | p1 | Toxic/Surf/Icy Wind into Skarmory or expected Forretress; pressure handoff if available | Steelix | miss | - | Missed Steelix as the exact handoff into the Electric pressure route. |
| 3 | p2 | Forretress to contest Spikes; Toxic retry; Whirlwind | Raikou | miss | - | Missed Raikou as the pressure owner after p1 Spikes. |
| 4 | p1 | Roar if available; Earthquake if Raikou stays; Curse | Curse | acceptable | P/R | Curse was ranked but too low; it made the next Steelix loop stronger. |
| 4 | p2 | Hidden Power coverage if present; Water/physical-answer switch; Electric pressure | Skarmory | acceptable | P/B | Correct to leave Raikou; exact Skarmory hidden. |
| 5 | p1 | Roar; handoff to Electric/Fire/special owner; Curse only if Skarmory cannot reset | Roar | top | P/R/B | Correct phaze after the first boost with Spikes up. |
| 5 | p2 | Whirlwind/phaze; Toxic; handoff | Hidden Power | miss | P | Skarmory revealed Steelix coverage. Before reveal this was possible-only, but voluntary-entry intent should have kept coverage live. |
| 6 | p1 | Earthquake into Tyranitar; Roar if receiver branch is stronger; preserve from coverage | Curse | miss | - | Repeated under-ranking: Tyranitar/Skarmory branch let Steelix boost again before phazing. |
| 6 | p2 | Fire/water coverage if present; Skarmory/Cloyster receiver; Rock Slide if staying | Skarmory | acceptable | P/B | Correct receiver class. |
| 7 | p1 | Roar; switch if Hidden Power pressure flips race; Curse | Roar | top | P/R/B | Correct to convert hazards before Skarmory coverage removed Steelix. |
| 7 | p2 | Hidden Power; phaze if available; switch | Hidden Power | top | P/R | Correct revealed coverage pressure. |
| 8 | p1 | Switch Snorlax/Starmie owner; Explosion only if revealed/survivable; Roar only if Starmie cannot punish | Zapdos | top by class | P/R/B | Correct to leave low Steelix; exact hidden owner was Zapdos. |
| 8 | p2 | Surf/active removal; Rapid Spin on switch; Recover/status | Surf | top | P/R | Correct active pressure before Spin. |
| 9 | p1 | Thunder into Starmie/spin; counter-handoff if Raikou/Tyranitar enters; status/coverage if set | Thunder | top | P/R | Correct to pressure Starmie before Spin. |
| 9 | p2 | Raikou Electric receiver; Rapid Spin if staying survives; Tyranitar | Raikou | top | P/R/B | Correct Electric receiver. |
| 10 | p1 | Snorlax/special-wall handoff; Thunder if staying; Steelix only with HP Water/Ice fallback | Steelix | acceptable | P/B | Steelix was ranked with caveat; exact use caught Rest. |
| 10 | p2 | Thunder/Electric pressure; Rest if para-clearing urgent; switch Normal/Rock owner | Rest | acceptable | P/R | Rest reset paralysis and made Raikou a sleeping route piece. |
| 11 | p1 | Roar to convert Spikes through switch or stay; Earthquake if Raikou stays; Curse | Curse | acceptable | P/R | Same under-ranking as turn 6: Curse before phaze was the route. |
| 11 | p2 | Switch Starmie/Skarmory; Sleep Talk only with fallback; burn sleep turn | Skarmory | top by class | P/R/B | Correct to leave sleeping Raikou before spending sleep turns. |

## Reusable Lessons

- Steelix with Spikes and Roar is a split package, not an autopilot phazer.
  `Curse` can be the route move before `Roar` when the expected answer is
  Skarmory, Tyranitar, Forretress, or another piece that lets Steelix boost.
- `Roar` is top while the switch loop is stable, the target cannot immediately
  remove Steelix, or the hazard chip is the main converter.
- `Earthquake` is top when the active grounded target must stay or cannot give
  Steelix a better boost turn. It falls when the opponent's best branch is the
  physical wall that lets Steelix set up.
- Skarmory voluntarily staying into Steelix can imply coverage or phaze. Before
  reveal, keep Hidden Power as a branch with fallback; after reveal, price its
  damage clock before choosing another boost or Roar.
- Sleeping Raikou after Rest is not a passive target by default. Name whether
  it uses Sleep Talk, stays to burn a turn, or switches to Skarmory/Starmie
  before spending the Steelix action.
