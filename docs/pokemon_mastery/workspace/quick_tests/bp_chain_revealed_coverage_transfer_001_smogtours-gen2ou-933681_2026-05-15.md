# BP Chain/Revealed Coverage Transfer 001 - smogtours-gen2ou-933681 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933681`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933681.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&server=smogtours&page=2`

Mode: spectator-public no-Team-Preview turn pause. Smogtours replay, selected
from current metadata and turn count only. I did not inspect move content or
future turns before freezing answers.

Contamination control:

- Local `rg` found no prior `smogtours-gen2ou-933681` use before selection.
- The log was saved locally at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-933681.log`.
- Prompts used
  `python tools/pokemon_mastery/replay_turn_pause.py ... prompt --turn N`.
- Reveals used
  `python tools/pokemon_mastery/replay_turn_pause.py ... reveal --turn N`.
- Fresh reveals stopped at turn 23 after repeated positive-selection misses
  around Baton Pass route mapping and Marowak coverage.
- The helper omitted some Baton Pass boosts, so speed and defense boosts were
  manually carried from the public reveal lines.

## Score Summary

Decisions: 44 scored, 2 unscored.
Unscored:

- turn 7 p1, because sleep prevented action and the selected move was not
  logged.
- turn 15 p2, because Forretress fainted before its selected move was logged.

Top-match: 15/44.
Acceptable-match: 32/44.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 38/44.
Route-converting move chosen: 30/44.
Branch-punish chosen: 18/36.
Earliest meaningful error: turn 1.

Result: mixed but not progress. Acceptable, positive-selection, hidden-info,
state, and mechanics improved versus the previous transfer, and branch
obedience improved by percentage. Top-match fell and route conversion fell, so
this cannot be claimed as real progress under the active rules.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Spikes; Electric/special receiver; Toxic/cash-out | Raikou | acceptable | P/R | Correct receiver class was ranked but Spikes was over-defaulted. |
| 1 | p2 | Thunder; Thunder Wave; special-wall pivot | Smeargle | miss | P/R | Missed the immediate Smeargle support entry. |
| 2 | p1 | sleep absorber; Thunder pressure; Roar if available | Thunder | acceptable | P/R | Thunder pressure was live because Smeargle used Agility, not sleep. |
| 2 | p2 | Spore; Spikes; Agility/Baton Pass | Agility | acceptable | P/R | Agility was ranked but too low. |
| 3 | p1 | sleep absorber; Roar if available; Thunder | Starmie | acceptable | P/R/B | Correct to switch out of possible sleep/pass pressure. |
| 3 | p2 | Spore; Baton Pass; Spikes/Destiny Bond | Baton Pass to Vaporeon | acceptable | P/R/B | Baton Pass was ranked but still under the sleep script. |
| 4 | p1 | Raikou; Thunder Wave if Starmie has it; Electric coverage | Snorlax | acceptable | P/R | Correct bulky/special owner class, exact owner missed. |
| 4 | p2 | Growth; Surf; Rest/Sleep Talk | Acid Armor | miss | P/R | Missed that Vaporeon was a defensive pass node, not only Growth. |
| 5 | p1 | Lovely Kiss if available; phaze/receiver handoff; STAB | Tyranitar | acceptable | P/R/B | The phaze handoff was ranked but not top. |
| 5 | p2 | Baton Pass; Acid Armor again; Surf | Roar | miss | P/R | Vaporeon had Roar as chain protection and disruption. |
| 6 | p1 | Spikes; Toxic; Explosion high-risk | Spikes | top | P/R/B | Correct to set Spikes before the chain receiver entered. |
| 6 | p2 | Roar; Zapdos switch; Surf | Baton Pass to Snorlax | miss | P/R | I dropped Baton Pass after one Roar reveal. |
| 7 | p1 | unscored | slept before action | unscored | - | Chosen move hidden. |
| 7 | p2 | Lovely Kiss; Curse; STAB/coverage | Lovely Kiss | top | P/R/B | Correct to stop the support answer. |
| 8 | p1 | Tyranitar; Snorlax mirror; stay asleep | Starmie | miss | P/R/B | Missed Reflect Starmie as the emergency route piece. |
| 8 | p2 | Curse; Double-Edge; coverage/switch | Belly Drum | miss | P/R | Missed the actual DrumLax receiver plan. |
| 9 | p1 | Reflect; Thunder Wave; Surf/Thunder | Reflect | top | P/R/B | Correct emergency screen. |
| 9 | p2 | STAB damage; Earthquake; switch | Return | top | P/R | Correct to force the Reflect race. |
| 10 | p1 | Recover; Thunder Wave; Surf/Thunder | Surf | miss | - | Recover preserved the wrong thing; Surf damage made the Roar follow-up work. |
| 10 | p2 | Return; coverage; switch | Return | top | P/R | Correct continued pressure. |
| 11 | p1 | Roar; damaging coverage; sacrifice/pivot | Roar | top | P/R/B | Correct to erase the pass chain through Spikes. |
| 11 | p2 | Earthquake; Return; Rest/switch | Earthquake | top | P/R | Correct Tyranitar punish. |
| 12 | p1 | Raikou; Snorlax; Roar if setup | Zapdos | acceptable | P/R | Correct Electric pressure class, exact owner missed. |
| 12 | p2 | Surf; Acid Armor; Roar | Roar | acceptable | P/R/B | Roar was ranked but not top. |
| 13 | p1 | Electric pressure owner; Zapdos equivalent; stay to burn sleep | Zapdos | acceptable | P/R | Correct class. |
| 13 | p2 | Roar; Acid Armor; Surf | Baton Pass to Forretress | miss | P/R | Dropped dry Baton Pass to the hazard/support receiver. |
| 14 | p1 | Thunder; Hidden Power read; spinblock/handoff if public | Thunder | top | P/R | Correct pressure without hidden Fire anchoring. |
| 14 | p2 | Rapid Spin; Spikes; Explosion/Toxic | Rapid Spin | top | P/R/B | Correct side-ownership Spin. |
| 15 | p1 | Thunder; Hidden Power read; switch | Thunder | top | P/R | Correct finish. |
| 15 | p2 | unscored | fainted before move | unscored | - | Chosen move hidden. |
| 16 | p1 | Raikou; Snorlax; Thunder | Thunder | acceptable | P/R | Thunder was ranked as the risk trade, not top. |
| 16 | p2 | Thunder; Hidden Power; Thunder Wave/Roar | Thunderbolt | acceptable | P/R | Correct Electric pressure class. |
| 17 | p1 | Raikou; Snorlax; Thunder | Raikou | top | P/R/B | Correct handoff after losing the mirror. |
| 17 | p2 | Thunderbolt; Hidden Power; switch | Thunderbolt | top | P/R | Correct pressure. |
| 18 | p1 | Thunder; Roar if available; Snorlax handoff | Thunder | top | P/R | Correct pressure into Zapdos or receiver. |
| 18 | p2 | Snorlax; stay; Smeargle sack | Smeargle | acceptable | P/R/B | Sack was ranked but too low. |
| 19 | p1 | Thunder; safer Electric coverage; Roar | Hidden Power | acceptable | P/R | Accuracy/safe coverage was ranked but not top. |
| 19 | p2 | stay and Spikes; switch Snorlax/Zapdos; Baton Pass/Agility | Snorlax | acceptable | P/R | Correct receiver class, not top. |
| 20 | p1 | Thunder; Zapdos on Earthquake; Hidden Power | Snorlax | miss | P/R | Missed Snorlax as the correct Earthquake sponge. |
| 20 | p2 | Earthquake; Return; switch | Earthquake | top | P/R | Correct active punish. |
| 21 | p1 | strongest Normal STAB; Earthquake branch; Curse on passive switch | Double-Edge | top | P/R/B | Correct no-Rest Snorlax punish. |
| 21 | p2 | Return; Earthquake; switch Vaporeon/Zapdos | Smeargle | miss | P/R | Missed the low Smeargle sack as the preservation route. |
| 22 | p1 | Cloyster; Zapdos; stay Double-Edge if reading SD | Surf | miss | - | Missed SurfLax lure coverage into Marowak. |
| 22 | p2 | Swords Dance; Earthquake; Rock Slide | Earthquake | acceptable | P/R | Earthquake was ranked but SD was overcalled. |
| 23 | p1 | Surf; switch Cloyster/Zapdos if EQ roll bad; Double-Edge | Zapdos | acceptable | P/R | Switch preservation was ranked, but Surf was overcalled after reveal. |
| 23 | p2 | Earthquake; switch; Swords Dance | Rock Slide | miss | P/R | After Zapdos was a named branch, Rock Slide had to stay ranked. |

## Reusable Lessons

- Smeargle is not sleep-first after it reveals Agility. The threat of Spore can
  buy the switch that lets the pass route start; once Agility is public, Baton
  Pass and receiver denial must rise beside sleep.
- Baton Pass work needs a manual boost ledger. In this replay the helper
  dropped passed Speed, and the correct reasoning had to carry `spe+2` and
  later `def+2` through Vaporeon and Snorlax until Roar reset the receiver.
- Vaporeon with Acid Armor, Baton Pass, and Roar is a chain node. Roar is not
  generic phazing there; it can disrupt the defender's phazer or Electric
  handoff while preserving the pass route.
- Reflect Starmie did its job, but the positive follow-up was Surf damage into
  the DrumLax route, not Recover. Spending the Reflect owner can be correct if
  the damage makes the next phaze or revenge turn work.
- Once Snorlax reveals Surf, the Marowak board must be re-solved around that
  lure. Before Surf is public, do not assume it; after it is public, do not
  demote it because Snorlax is "normally" a Normal attacker.
- Marowak is not only Earthquake or Swords Dance. Rock Slide is the branch
  punish when Zapdos is the named preservation switch.
