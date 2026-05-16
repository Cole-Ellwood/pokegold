# Support Reveal Role Ledger Transfer 001 - smogtours-gen2ou-932807 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-932807`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-932807.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&server=smogtours&page=3`

Mode: spectator-public no-Team-Preview turn pause. Smogtours replay, selected
from current metadata and turn count only. I did not inspect move content or
future turns before freezing answers.

Context condition:

- This was the first fresh test after `plateau_diagnosis_001` and the new
  `heuristic_core/role_package_ledger.md` card.
- Pre-freeze live docs: `active_context.md`, `live_core.md`,
  `replay_turn_pause_protocol.md`, and the tiny `heuristic_core/*.md` cards.
- No scored quick tests, future turns, raw answer labels, long policy cards, or
  external research returns were opened after this replay was selected and
  before answers were frozen.
- Stopped after turn 12 because the same RestTalk package miss repeated. No
  turn 13 or later move content was inspected.

Players: p1 `Seanobiwan`, p2 `isnialan`.

## Score Summary

Decisions: 24 scored, 0 unscored.

Top-match: 11/24.
Acceptable-match: 21/24.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 22/24.
Route-converting move chosen: 18/24.
Branch-punish chosen: 14/20.
Earliest meaningful error: turn 2.

Result: partial repair, not progress proof. The role-ledger procedure improved
Snorlax Curse into Steelix Roar and kept acceptable-match high, but it exposed
a narrower package gap: revealed RestTalk can be a sleep-turn absorber even
when its attack is blanked by the active target. I over-pivoted Zapdos out of
Nidoking after RestTalk became public; the player repeatedly burned sleep turns
and used RestTalk as a damage absorber.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Thunder; switch only if Snorlax owner must enter; Thunder Wave/support if side-known | Thunder | top | P/R | Correct lead pressure. |
| 1 | p2 | Body Slam/Double-Edge; Curse; Lovely Kiss/EQ only if side-known | Curse | acceptable | P | Curse package was ranked but active damage overvalued. |
| 2 | p1 | Switch Normal-resist/phazer; Thunder chip; status/support if side-known | Thunder | acceptable | P/R | Thunder pressure beat early handoff for one more turn. |
| 2 | p2 | Body Slam/Double-Edge; Rest if forced low; Curse if phazer absent | Double-Edge | top | P/R | Correct active conversion. |
| 3 | p1 | Thunder to force Rest; switch Normal-resist/phazer; Thunder Wave/Rest if set | Steelix | acceptable | P/B | Correct owner class was ranked second. |
| 3 | p2 | Rest; Double-Edge trade; switch preserve | Double-Edge | acceptable | P/R | Active trade stayed live one more turn. |
| 4 | p1 | Roar; Earthquake; Curse/Explosion if side-known | Roar | top | P/R/B | Correct public phaze package after Steelix entry. |
| 4 | p2 | Rest; switch; attack if staying | Rest | top | P/R | Correct Rest timing into low Snorlax. |
| 5 | p1 | Earthquake; Zapdos handoff; Roar if switch is likely | Zapdos | acceptable | P/B | Correct handoff was ranked below active damage. |
| 5 | p2 | Coverage into Steelix; switch Water/support owner; status | Cloyster/Nidoking switch line | acceptable | P/B | Correct counter-handoff class, exact double-switch not top. |
| 6 | p1 | Thunder; switch only if Snorlax/Nidoking branch dominates; Rest if side-known | Forretress | miss | - | Missed Forretress as the anti-Cloyster/Nidoking support owner. |
| 6 | p2 | Switch special/Ground owner; Spikes if Cloyster survives; Explosion high-risk | Nidoking | top by class | P/B | Correct anti-Zapdos owner. |
| 7 | p1 | Spikes before forced; Zapdos scout/handoff; Explosion/coverage | Zapdos | acceptable | P/B | Correct scout branch was ranked but Spikes overvalued. |
| 7 | p2 | Fire/coverage; Earthquake/STAB; switch preserve | Thunder | top by coverage | P/R | Correct coverage pressure. |
| 8 | p1 | Thunder; Steelix handoff; Forretress sack/support | Rest | miss | - | Missed RestTalk Zapdos as a route piece before Sleep Talk was public. |
| 8 | p2 | Ice Beam/coverage; Thunder; switch if Steelix branch | Ice Beam | top | P/R | Correct revealed coverage pressure. |
| 9 | p1 | Steelix handoff; Sleep Talk if RestTalk is strong-prior; Forretress sack | Sleep Talk -> Thunder | acceptable | P | RestTalk was considered but under-ranked. |
| 9 | p2 | Ice Beam; switch Cloyster/Snorlax into Steelix; Thunder | Ice Beam | top | P/R | Correct active coverage. |
| 10 | p1 | Steelix handoff; Forretress sack; Sleep Talk if no entry path | Sleep Talk -> Thunder | acceptable | P | Still under-ranked RestTalk as absorber. |
| 10 | p2 | Ice Beam; switch counter-handoff; Thunder | Ice Beam | top | P/R | Correct repeat pressure. |
| 11 | p1 | Steelix switch; Rest if wake-and-act; Sleep Talk if still asleep | Wake -> Rest | acceptable | P | Wake Rest was named conditionally, not top. |
| 11 | p2 | Ice Beam; switch counter-handoff; Thunder | Ice Beam | top | P/R | Correct active pressure. |
| 12 | p1 | Steelix switch; Forretress sack; no-repeat Sleep Talk unless it has pressure | Sleep Talk -> Thunder | miss | - | Repeated miss: RestTalk can absorb turns even when Thunder is immune. |
| 12 | p2 | Ice Beam; switch counter-handoff; Thunder | Ice Beam | top | P/R | Correct active pressure. |

## Reusable Lessons

- The role ledger helped when the package was obvious and converting: Snorlax
  Curse/Rest into Steelix Roar was clean.
- The role ledger must not equate package with offense. RestTalk Zapdos had a
  public job as a sleep-turn and damage absorber against Nidoking, even though
  its revealed attacking move was immune.
- `role_package_ledger.md` was updated after scoring to ask whether RestTalk's
  job is pressure, absorbing, or pivoting.
- Next fresh test should keep the support reveal focus, but explicitly classify
  each public package as `pressure`, `absorber`, `reset`, `trap`, `phaze`, or
  `handoff` before choosing.
