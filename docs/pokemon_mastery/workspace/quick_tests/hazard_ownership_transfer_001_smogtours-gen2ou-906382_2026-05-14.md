# Hazard Ownership Transfer 001 - smogtours-gen2ou-906382 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-906382`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-906382.log`

Web/current source checked:

- Smogon GSC forum index, which currently lists active GSC OU statistics,
  viability rankings, discussion, sample-team, and tournament/replay resources.
- Smogon search for GSC OU Winter Seasonal #8 material before selecting this
  unused replay.

Mode: sealed spectator-public turn-pause transfer. Future turns and answer
labels were not used before each frozen answer.

Selected action:
Run a fresh 30-side-decision transfer after the hazard ownership review from
`gen2ou-2544443857`, with special attention to Spikes, Spin, phaze loops, and
named branch punishment.

## Score

- Top match: 12/30
- Acceptable match: 26/30
- Severe blunders: 0
- Mechanics errors: 0
- State errors: 1
- Hidden-info errors: 0
- Illegal-action errors: 0
- Positive-selection hits: 20/30
- Route-converting move chosen: 11/21 applicable
- Branch-punish chosen: 7/16 applicable

Interpretation:
This is not broad improvement proof. Severe errors stayed at 0, but top-match
fell below the prior 14/30 packet. Acceptable-match was high because many
answers kept the game playable, but the main bottleneck remains choosing the
best route-converting move as top action instead of naming it as an alternative.

## Turn Notes

| Turn | Side | Frozen top | Actual | Score |
| --- | --- | --- | --- | --- |
| 1 | p1 | Spore if available | Spikes | acceptable; positive hazard route, not top |
| 1 | p2 | Lovely Kiss if available | Earthquake | acceptable; active pressure was underweighted |
| 2 | p1 | Switch to Ground-immune/special owner | Zapdos | top; support handoff |
| 2 | p2 | Earthquake, with Ice Beam branch priced | Ice Beam | acceptable; branch coverage not top |
| 3 | p1 | Switch Zapdos out | Hidden Power | acceptable; strong-prior Zapdos HP was underweighted |
| 3 | p2 | Ice Beam, with Lovely Kiss priced | Lovely Kiss | acceptable; sleep conversion not top |
| 4 | p1 | Switch sleeping Zapdos out | stayed asleep | acceptable only as burn-one-turn alternative |
| 4 | p2 | Ice Beam | Ice Beam | top |
| 5 | p1 | Switch to Nidoking owner | Snorlax | top |
| 5 | p2 | Ice Beam, with Earthquake branch priced | Earthquake | acceptable; grounded receiver punish not top |
| 6 | p1 | Immediate Snorlax attack | Double-Edge | top by class |
| 6 | p2 | Switch to Snorlax answer | Reflect | miss; support screen was not priced |
| 7 | p1 | Curse/setup if available | Double-Edge | acceptable; active chip line was lower ranked |
| 7 | p2 | Earthquake, with switch priced | Tyranitar | acceptable; preserve-to-resist not top |
| 8 | p1 | Coverage into Tyranitar | Surf | top by class |
| 8 | p2 | Roar/phaze, with Rock Slide priced | Rock Slide | acceptable |
| 9 | p1 | Surf | Surf | top |
| 9 | p2 | Switch to Snorlax owner | Misdreavus | top by class |
| 10 | p1 | Switch out of Misdreavus | Steelix | top by action class |
| 10 | p2 | Misdreavus trap route | Snorlax | miss; counter-handoff not priced |
| 11 | p1 | Roar with Spikes pressure | Earthquake | acceptable; active damage not top |
| 11 | p2 | Super-effective coverage into Steelix | Earthquake | top |
| 12 | p1 | Earthquake, with Roar into Rest priced | Roar | acceptable; route phaze not top |
| 12 | p2 | Rest | Rest | top |
| 13 | p1 | Earthquake, with Roar priced | Roar | acceptable; phaze loop not top |
| 13 | p2 | Switch out of Steelix | Cloyster | top by action class |
| 14 | p1 | Roar | Earthquake | acceptable; active punish lower ranked |
| 14 | p2 | Switch to Steelix answer | Cloyster | top by action class |
| 15 | p1 | Attack/punish Cloyster | Smeargle | miss; support handoff was not priced |
| 15 | p2 | Rapid Spin | Spikes | miss plus state error; current job was set missing Spikes |

## Main Error

Turn 15 repeated the hazard-ownership bottleneck in a sharper form. I saw
Cloyster as a low active spinner with Spikes on its own side, but I did not
properly price that p1's side had no Spikes. Because Cloyster was already in,
setting the missing Spikes on p1's side was the immediate route-converting job.

This is a state error, not a hidden-info error. I did not assume an unrevealed
move was known; I failed to convert a public hazard asymmetry into the correct
move priority.

## Useful Transfers

- Revealed coverage into named receiver improved on turn 8: Snorlax's Surf into
  Tyranitar was correctly top-ranked by class.
- Spikes plus phaze loop was recognized but still often under-ranked. Steelix
  Roar on turns 12-13 was acceptable but not top.
- Severe-blunder control held, but positive move selection did not improve
  enough because the route-converting move was too often placed as an
  alternative.

## Policy Update

When a Cloyster or other hazard piece is active, order the possible jobs before
choosing:

1. Set missing Spikes on the opponent's side.
2. Clear owned-side Spikes with Rapid Spin.
3. Cash out with Explosion or damage.
4. Pivot or preserve.

If one side is unspiked and the setter is already active, setting the missing
Spikes can beat Spin even when the setter is also a plausible spinner.

## Next Rep

Fresh transfer or focused review on Cloyster hazard job ordering:
name both sides' hazard status, then choose between Spikes, Spin, Explosion,
Surf/Ice Beam, switch, and phaze before revealing.
