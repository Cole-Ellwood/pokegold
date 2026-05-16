# Side-Known Transfer 024 - smogtours-gen2ou-935947 p1 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935947`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935947.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&page=1`

Mode: side-known reconstructed for p1 / melancholy0. Opponent information was
spectator-public only.

Contamination control:

- Local `rg` found no prior `smogtours-gen2ou-935947` use before selection.
- Turns 1-6 were not scored because the log head was inspected while checking
  parser output. The sealed section begins at turn 7.
- Scored p1 turns 7-35, with no-action sleep / forfeit turns excluded.

## Score Summary

Decisions: 27 scored, 3 unscored.
Top-match: 9/27.
Acceptable-match: 20/27.
Severe blunders: 2.
State errors: 0.
Hidden-info errors: 2.
Mechanics errors: 1.
Positive-selection: 13/27.
Route-converting move chosen: 12/27.
Branch-punish chosen: 7/16.
Role-package update obeyed: 20/27.
Route-transaction obeyed: 19/27.
Candidate comparison obeyed: 27/27 in form, 13/27 in promotion.
Earliest meaningful error: turn 8.

Verdict: failed transfer and repair stop. This is stronger evidence than packet
023 because the replay was a Smogtours game, and it repeated the repaired
cash-out family twice: turn 30 Snorlax Self-Destruct into Zapdos after Lovely
Kiss + Double-Edge, and turn 34 Cloyster Explosion into sleeping Snorlax after
Surf changed the threshold. Turn 29 also exposed a missing compact tactic:
using a doomed Spikes switch-in as a controlled sack to cancel the opponent's
action and create clean entry.

## Frozen Answer Log

| Turn | Frozen top | Actual | Grade | Lesson |
| --- | --- | --- | --- | --- |
| 7 | Ice Punch | Switch Snorlax into Thunderbolt | acceptable miss | Active damage was plausible, but preserving paralyzed Gengar mattered. |
| 8 | Rest | Curse, then Whirlwind dragged Jynx | miss | Rest into phaze would have slept Snorlax for little gain. |
| 9 | Switch Nidoking | Switch Snorlax into Thunder Wave | acceptable miss | Nidoking would blank TWave; Snorlax absorbed status for Rest later. |
| 10 | Rest | Rest | top | Correct status/HP reset before phaze. |
| 11 | Thunder | Switch Nidoking into Thunder Wave | miss | Failed to punish the revealed status branch. |
| 12 | Ice Beam | Ice Beam | top | Correct Nidoking branch punish. |
| 13 | Hidden Power Ice | Switch sleeping Snorlax into Thunder Wave | acceptable miss | Exact removal ignored speed/status cost into our healthy Zapdos. |
| 14 | Switch Nidoking | Snorlax slept, Whirlwind dragged Nidoking | unscored | No-action sleep turn. |
| 15 | Ice Beam | Ice Beam KOed Zapdos | top | Correct active removal after the status branch was covered. |
| 16 | Switch Snorlax | Switch Jynx into Ice Punch | acceptable miss | Right preserve-Nidoking idea; Jynx was the better Ice absorber. |
| 17 | Psychic | Double Nidoking into Raikou | miss | Missed the next-owner punish after Jynx invited Raikou. |
| 18 | Earthquake | Earthquake | top | Correct punish into sleeping Raikou. |
| 19 | Earthquake | Earthquake after Raikou woke HP Ice | top | Hidden HP Ice was priced; Nidoking survived and converted. |
| 20 | Stay / Earthquake if able | Switch Jynx into Thief | acceptable miss | Low Nidoking was nearly fake to preserve, but Jynx was the chosen Thief/Ice absorber. |
| 21 | Psychic | Lovely Kiss | miss | Missed that Raikou fainting reopened Sleep Clause; sleep converted better than damage. |
| 22 | Psychic | Thief into Cloyster switch | acceptable miss | Active punish was playable; branch move hit the switch. |
| 23 | Psychic | Switch Gengar into Surf | miss | Failed to preserve low Jynx and deny Cloyster's support/cash-out branch. |
| 24 | Switch Zapdos | Gengar Explosion into sleeping Gengar immunity | acceptable miss | Actual boom failed; my move-order concern was coherent. |
| 25 | Psychic | Thief into Cloyster switch | acceptable miss | Missed the repeated Cloyster switch branch. |
| 26 | Psychic | Psychic into Snorlax switch | top | Correct low-piece spend. |
| 27 | Psychic | Thief into Snorlax | acceptable miss | Same spend idea; wrong exact damage move. |
| 28 | Spikes | Spikes, then Cloyster slept | top | Correct support job before sleep. |
| 29 | Switch Snorlax | Sacrifice Nidoking to Spikes for clean Zapdos | miss, mechanics | Missed hazard-death sack as a positive entry tactic. |
| 30 | Thunder | Snorlax Self-Destruct KOed Zapdos | severe hidden-info miss | Lovely Kiss + Double-Edge made Self-Destruct a strong-prior branch. |
| 31 | Switch Cloyster | Switch Cloyster into Surf | top | Correct low-value resist preserving Snorlax. |
| 32 | Stay with Cloyster | Stayed asleep into Surf | top by stay | Correctly kept Cloyster as cash-out absorber. |
| 33 | Stay with Cloyster | Switch Snorlax into Surf | acceptable miss | Overguarded Explosion one turn early. |
| 34 | Stay / Curse if awake | Cloyster Explosion KOed Snorlax | severe hidden-info miss | Failed to re-run the low-Cloyster four-way check after Surf. |
| 35 | Stay / attack if awake | Cloyster stayed asleep as Vaporeon Substituted | unscored | No-action sleep turn after route was lost. |
| 36 | Attack if awake | p1 forfeited | unscored | Forfeit. |

## Reusable Lesson

Sleep plus cash-out must be scored before damage when the revealed package has
already done its job. Lovely Kiss + Double-Edge Snorlax does not need to be low
before Self-Destruct becomes a strong-prior route trade. Cloyster likewise
becomes an Explosion problem after Spikes/Surf pressure and threshold changes.

A doomed hazard switch-in can be a positive route action. If a piece will die
to Spikes anyway and has no real future entry, switching it in can cancel the
opponent's selected action and create a clean entry for the real owner.

After any chip into a support/cash-out user, re-run the four-way check:
preserve, coverage/status, Explosion/Self-Destruct, or defensive sack. Do not
let "Surf was correct last turn" suppress the next-turn Explosion branch.

