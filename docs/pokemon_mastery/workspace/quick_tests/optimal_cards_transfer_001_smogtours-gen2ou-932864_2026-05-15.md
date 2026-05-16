# Optimal Cards Transfer 001 - smogtours-gen2ou-932864 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-932864`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-932864.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&server=smogtours&page=3`

Mode: spectator-public no-Team-Preview turn pause. Smogtours replay, selected
from current metadata and turn count only. I did not inspect move content or
future turns before freezing answers.

Context condition:

- This run followed the corrected compressed-core protocol: no fixed card cap.
- Pre-freeze live docs: `active_context.md`, `live_core.md`,
  `replay_turn_pause_protocol.md`, and all tiny `heuristic_core/*.md` cards.
- The same thread already contained earlier postmortem study and web snippets,
  so this is a practical learned-knowledge replay test, not a sterile final
  exam.
- No scored quick tests, future turns, raw answer labels, or external research
  returns were opened after this replay was selected and before answers were
  frozen.

Contamination control:

- Local `rg` found no prior `smogtours-gen2ou-932864` use before selection.
- The log was saved locally at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-932864.log`.
- Turn count was checked mechanically without printing move content.
- Prompts used
  `python tools/pokemon_mastery/replay_turn_pause.py ... prompt --turn N`.
- Reveals used
  `python tools/pokemon_mastery/replay_turn_pause.py ... reveal --turn N`.
- Fresh reveals stopped at turn 20 for 40 side decisions. No turn 21 or later
  move content was inspected.

Players: p1 `Seanobiwan`, p2 `isnialan`.

## Score Summary

Decisions: 40 scored, 0 unscored.

Top-match: 16/40.
Acceptable-match: 29/40.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 35/40.
Route-converting move chosen: 30/40.
Branch-punish chosen: 20/31.
Earliest meaningful error: turn 1.

Result: mixed but not progress proof. Removing the one-card cap helped
support-loop decisions: Forretress/Starmie Spikes and Rapid Spin sequencing was
much better than the strict converter-only packet. Top-match still missed the
gate because I under-ranked second-order owner changes: Steelix into expected
Raikou, Zapdos into expected Starmie, Tyranitar Roar after Snorlax Rest, and
Cloyster as the repeated Skarmory/Snorlax support handoff.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Thunder pressure; Reflect if side-known; switch Steel/Ground/Snorlax owner | Skarmory | acceptable | P/R | Snorlax lead can make immediate owner handoff better than raw Electric pressure. |
| 1 | p2 | Body Slam/Double-Edge pressure; Curse; EQ/coverage if side-known | Curse | acceptable | P | Setup was ranked, but active damage was overvalued before seeing p1's owner. |
| 2 | p1 | Whirlwind; Toxic; attack or switch only if phaze absent | Toxic | acceptable | P/R/B | Toxic hit the Cloyster branch, but Whirlwind was the generic Curselax answer. |
| 2 | p2 | Fire/coverage if side-known; switch Electric/Skarm answer; active chip | Cloyster | miss | P/B | Missed Cloyster as Skarmory support owner and Spikes reset piece. |
| 3 | p1 | Raikou handoff; Whirlwind; Starmie/spinner if preserving hazard control | Starmie | acceptable | P/B | Spinner handoff was present but under-ranked. |
| 3 | p2 | Spikes; Surf/Ice coverage; Explosion if exact route opens | Spikes | top | P/R | Correct support conversion. |
| 4 | p1 | Rapid Spin; pressure/coverage if side-known; Recover | Substitute | miss | P/R | Missed revealed SubStarmie as the safer scout before Spin. |
| 4 | p2 | Toxic Starmie; Ghost/Pursuit branch; Surf/Explosion | Zapdos | miss | P/B | Missed Zapdos as the immediate anti-spinner pressure owner. |
| 5 | p1 | Rapid Spin behind Substitute; Recover; support/status if side-known | Rapid Spin | top | P/R | Correct SubSpin conversion. |
| 5 | p2 | Thunderbolt; Snorlax/Raikou switch; coverage/status | Thunderbolt | top | P/R | Correct active pressure. |
| 6 | p1 | Raikou switch; Recover; Substitute scout | Raikou | top | P/B | Correct Electric owner handoff. |
| 6 | p2 | Thunderbolt; Snorlax if Raikou enters; coverage/status | Snorlax | acceptable | P/B | Correct branch class, under-ranked. |
| 7 | p1 | Skarmory/Normal-resist owner; Thunder pressure; Reflect/Roar if side-known | Forretress | acceptable | P/B | Hidden Forretress fit the Normal-resist support class. |
| 7 | p2 | Body Slam/Double-Edge; switch Cloyster/Zapdos into Skarm; Curse | Zapdos | acceptable | P/B | Correct expected-owner punish class, not top. |
| 8 | p1 | Spikes before forced; Raikou handoff; Toxic/Explosion branch | Raikou | acceptable | P/R | Preserving Forretress beat first-layer greed. |
| 8 | p2 | Thunderbolt; switch if Raikou branch dominates; HP Fire only if side-known | Thunderbolt | top | P/R | Correct active pressure. |
| 9 | p1 | Thunder; Roar if side-known; handoff if Snorlax/Ground branch dominates | Thunder | top | P/R | Correct active pressure into Snorlax branch. |
| 9 | p2 | Snorlax; Thunderbolt chip; Rest/status/coverage | Snorlax | top | P/B | Correct special wall handoff. |
| 10 | p1 | Thunder; Skarmory/Forretress preserve switch; Roar/Reflect if side-known | Skarmory | acceptable | P | Correct preserve branch, under-ranked. |
| 10 | p2 | Body Slam/Double-Edge; Curse; Rest if fearing Thunder | Cloyster | miss | P | Missed repeated Cloyster handoff as Skarmory/Snorlax support reset. |
| 11 | p1 | Starmie spinner; Raikou pressure; Whirlwind/Drill Peck | Forretress | miss | P | Missed Forretress as the better Toxic-immune hazard owner. |
| 11 | p2 | Spikes; Explosion; Surf/Ice/Toxic if side-known | Spikes | top | P/R | Correct Spikes reset. |
| 12 | p1 | Spikes before clearing; Rapid Spin; Raikou/Starmie handoff | Spikes | top | P/R | Correct missing-layer priority. |
| 12 | p2 | Zapdos; Surf/Explosion; Snorlax/Steelix preserve | Zapdos | top | P/B | Correct anti-Forretress pressure handoff. |
| 13 | p1 | Rapid Spin; Raikou switch; Explosion/Toxic branch | Rapid Spin | top | P/R | Correct clear while Forretress still survives. |
| 13 | p2 | Thunderbolt; HP Fire/Thunder if side-known; Snorlax if Raikou branch | Thunderbolt | top | P/R | Correct active pressure. |
| 14 | p1 | Raikou switch; sack/stay only if job complete; Explosion branch | Raikou | top | P/B | Correct preserve and handoff. |
| 14 | p2 | Thunderbolt; Snorlax if Raikou branch; HP Fire if side-known | Steelix | miss | P | Missed second-order Steelix owner into the obvious Raikou handoff. |
| 15 | p1 | Starmie; Skarmory; Forretress/sack | Starmie | top | P/B | Correct Ground owner handoff. |
| 15 | p2 | Roar; Earthquake; Explosion/Curse | Zapdos | miss | P/R | Missed Zapdos as the owner after p1's obvious Starmie handoff. |
| 16 | p1 | Substitute scout; Raikou; Recover/Surf branch | Raikou | acceptable | P/B | Correct owner was ranked but Sub overfit to the double-switch branch. |
| 16 | p2 | Thunderbolt; Steelix double; Snorlax | Thunderbolt | top | P/R | Correct active pressure. |
| 17 | p1 | Hidden Power if available, fallback Starmie; Thunder; Raikou/Skarm handoff | Hidden Power | top | P/R/B | Correct revealed-branch punish without hidden certainty. |
| 17 | p2 | Steelix; Snorlax; Thunderbolt/status | Snorlax | acceptable | P/B | Correct special wall branch, Steelix over-ranked. |
| 18 | p1 | Thunder; Skarmory/Forretress preserve; Roar/Reflect if side-known | Skarmory | acceptable | P/R | Preservation was ranked below pressure. |
| 18 | p2 | Rest; Body Slam/Double-Edge; Curse | Earthquake | miss | P/R | Missed revealed EQ as the active coverage into Raikou/Tyranitar. |
| 19 | p1 | Whirlwind; Toxic; Forretress/Starmie handoff | Tyranitar | miss | P/R | Missed Tyranitar as the Spikes phazer/offensive owner. |
| 19 | p2 | Zapdos; Curse/coverage; Rest | Rest | acceptable | P/R | Rest was correctly recognized but under-ranked. |
| 20 | p1 | Rock Slide/physical pressure; Curse; Skarmory if Sleep Talk EQ branch | Roar | miss | P/B | Missed Roar as the Spikes converter after Snorlax rested. |
| 20 | p2 | Sleep Talk if side-known; Steelix; Zapdos | Cloyster | miss | P | Missed low poisoned Cloyster as the route piece to absorb and reset. |

## Reusable Lessons

- The optimal-card protocol fixed the artificial retrieval failure. The live
  core plus tiny cards were enough to handle Spikes, Spin, missing-layer order,
  Forretress preservation, and SubSpin once the set was revealed.
- The remaining wall is second-order owner mapping. I often named our correct
  owner, then failed to name the opponent's owner into that owner.
- With Spikes down, phazing is not a fallback script. Tyranitar or Steelix Roar
  can be the route-converting move after a Rest, expected switch, or sleeping
  target.
- Cloyster kept reappearing as the support route piece, not merely a Spikes
  button. When Skarmory or Snorlax forces a passive-looking board, name
  Cloyster/Zapdos/Steelix as the next owner triangle before picking.
