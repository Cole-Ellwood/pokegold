# Side-Known Transfer 020 - smogtours-gen2ou-935952 p1 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935952`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935952.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&page=1`

Mode: side-known reconstructed for p1 / Prachi Desai. Opponent information was
spectator-public only.

Contamination control:

- Local `rg` found no prior `smogtours-gen2ou-935952` use before selection.
- Only metadata and turn count were inspected before turn 1.
- Stopped at turn 26 after a severe branch/cash-out miss.

## Score Summary

Scored decisions: 25.
Unscored decisions: 1, turn 24 because Lovely Kiss stopped the selected move.
Top-match: 19/25.
Acceptable-match: 22/25.
Severe blunders: 1.
State errors: 0.
Hidden-info errors: 1.
Mechanics errors: 0.
Positive-selection: 20/25.
Route-converting move chosen: 18/25.
Branch-punish chosen: 13/17.
Role-package update obeyed: 22/25.
Route-transaction obeyed: 25/25.
Candidate comparison obeyed: 23/25 in form, 19/25 in promotion.
Earliest meaningful error: turn 9.
Primary severe error: turn 26.

Verdict: failed transfer. Early exact top-match was strong, but turn 26 broke
the pass/fail gate: after Snorlax revealed Lovely Kiss and Double-Edge, I kept
ranking Sleep Talk damage instead of pricing low-HP Self-Destruct and preserving
the RestTalk special wall with Skarmory.

## Frozen Answer Log

| Turn | Frozen top | Actual | Grade | Lesson |
| --- | --- | --- | --- | --- |
| 1 | Raikou Thunder | Thunder | top | Correct mirror pressure. |
| 2 | Raikou Thunder | Thunder into Raikou switch | top | Correct active pressure and paralysis route. |
| 3 | Switch Snorlax | Switch Snorlax | top | Correct special-wall handoff. |
| 4 | Double-Edge | Double-Edge into Cloyster | top | Correct active pressure into receiver. |
| 5 | Double-Edge | Double-Edge after Toxic | top | Correct damage before leaving. |
| 6 | Double-Edge | Double-Edge after Spikes | top | Correct pressure to force low Cloyster. |
| 7 | Switch Forretress | Switch Forretress | top | Correct low-Cloyster Explosion guard class. |
| 8 | Spikes | Spikes | top | Correct route conversion while Forretress survives. |
| 9 | Stay Forretress as sack | Switch Starmie into Explosion | acceptable miss | Correct boom-guard class, wrong piece; preserving Forretress mattered. |
| 10 | Raikou Hidden Power | Thunder into Tyranitar | acceptable miss | Correct active attack, wrong move; Thunder was stronger neutral pressure. |
| 11 | Switch Skarmory | Switch Skarmory through Pursuit | top | Correct Tyranitar owner despite Pursuit. |
| 12 | Toxic | Toxic into Zapdos switch | top | Correct branch status. |
| 13 | Switch Snorlax | Switch Snorlax | top | Correct Zapdos owner. |
| 14 | Rest | Rest into Tyranitar switch | top | Correct poison reset before route collapses. |
| 15 | Sleep Talk | Sleep Talk Surf, then Roar | top | Correct RestTalk pressure. |
| 16 | Tyranitar Rock Slide | Switch Skarmory as p2 switched Snorlax | miss | Failed next-owner handoff; Skarmory owned the Snorlax branch. |
| 17 | Toxic | Toxic into already poisoned Zapdos | top | Correct status script into Electric branch. |
| 18 | Switch Snorlax | Switch Snorlax as Zapdos Rests | top | Correct special-wall route. |
| 19 | Sleep Talk | Sleep Talk Surf | top | Correct active RestTalk pressure. |
| 20 | Double-Edge on wake | Double-Edge into Snorlax switch | top | Correct manual Rest wake count. |
| 21 | Double-Edge | Switch Skarmory into Lovely Kiss miss | acceptable miss | Sleep package not fully updated yet. |
| 22 | Switch Snorlax as sleep absorber | Toxic into Zapdos switch | acceptable miss | Right sleep-absorber idea, wrong branch. |
| 23 | Switch Snorlax | Switch Snorlax into Snorlax | top | Correct sleep-package absorber handoff. |
| 24 | Stay and attack/absorb sleep | Lovely Kiss put Snorlax to sleep | unscored | Route choice was absorber assignment; selected move was hidden by sleep. |
| 25 | Sleep Talk | Sleep Talk Double-Edge | top | Correct sleep absorber pressure. |
| 26 | Sleep Talk | Switch Skarmory into Self-Destruct | severe miss | Hidden-info plus severe branch error: low Lovely Kiss Snorlax cash-out was strong-prior. |

## Reusable Lesson

Lovely Kiss Snorlax is not only a sleep problem. Once it also shows Double-Edge
and is low enough to trade, Self-Destruct becomes a strong-prior cash-out
branch. If our active is a valuable RestTalker, special wall, or win piece,
rank the Normal resist, Ghost, or low-value sack before Sleep Talk damage unless
the damage gets the exact KO before Self-Destruct.

