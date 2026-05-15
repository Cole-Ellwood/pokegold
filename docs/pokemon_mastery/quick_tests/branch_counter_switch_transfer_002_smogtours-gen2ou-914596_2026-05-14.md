# Branch Counter-Switch Transfer 002 - smogtours-gen2ou-914596 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-914596`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-914596.log`

Tournament source:
`https://www.smogon.com/forums/threads/smogon-premier-league-xvii-week-8.3778512/`

Web/current source checked:

- Smogon SPL XVII Week 8 and Week 9 GSC OU replay posts.
- Smogon GSC current forum/search results before selecting an unused replay.

Contamination control:

- Local `rg` found no prior `914596` use before selection.
- No keyword screen for Cloyster, Spikes, Sleep Talk, or branch turns.
- Used only spectator-public prompts from the local replay helper before each
  reveal.
- Turn 6 p1 and turn 8 p1 are unscored because Snorlax was put to sleep before
  its selected move could be logged.

Selected action:
Fresh transfer after `cloyster_hazard_job_transfer_001`, focused on whether I
obey the branch-action card after forcing an exit.

## Score

- Scored decisions: 30
- Top match: 14/30
- Acceptable match: 25/30
- Severe blunders: 0
- State errors: 1
- Hidden-info errors: 1
- Mechanics errors: 0
- Positive-selection: 24/30
- Route-converting move chosen: 14/23 applicable
- Branch-punish chosen: 7/17 applicable
- Earliest meaningful error: turn 1

Interpretation:
This packet is not progress over the previous one. Severe errors stayed at 0,
but top-match, positive-selection, route conversion, and branch-punish all fell.
The branch-counter-switch problem did not transfer cleanly.

## Turn Notes

| Turn | Side | Frozen top | Actual | Grade |
| --- | --- | --- | --- | --- |
| 1 | p1 | Spore | Spider Web | miss; trap set not recognized |
| 1 | p2 | Switch sleep absorber | Snorlax | top by class |
| 2 | p1 | Spore | Perish Song | miss; did not continue trap route |
| 2 | p2 | Attack Smeargle | Body Slam | top by class |
| 3 | p1 | Baton Pass trap route | Destiny Bond | miss; hidden-info error |
| 3 | p2 | Attack Smeargle | Body Slam | top |
| 4 | p1 | Sleep Powder | Snorlax | acceptable sleep-absorber switch |
| 4 | p2 | Sleep Powder | Zapdos | acceptable sleep-absorber switch |
| 5 | p1 | Double-Edge | Double-Edge | top |
| 5 | p2 | Thunder | Exeggutor | acceptable counter-handoff |
| 6 | p1 | unscored | slept before move | excluded |
| 6 | p2 | Sleep Powder | Sleep Powder | top |
| 7 | p1 | Switch sleeping Snorlax | Sleep Talk | acceptable after Sleep Talk reveal |
| 7 | p2 | Explosion | Psychic | acceptable active pressure |
| 8 | p1 | unscored | slept before move | excluded |
| 8 | p2 | Explosion | Sleep Powder | state error; sleep was open again |
| 9 | p1 | Switch sleeping Snorlax | Exeggutor | top |
| 9 | p2 | Counter-switch Zapdos | Psychic | acceptable but overread |
| 10 | p1 | Sleep Powder | Explosion | acceptable, but branch punish missed |
| 10 | p2 | Switch sleep absorber | Zapdos | top by class |
| 11 | p1 | Spikes | Snorlax | acceptable preservation switch |
| 11 | p2 | Explosion | Psychic | acceptable |
| 12 | p1 | Sleep Talk | Sleep Talk -> Double-Edge | top |
| 12 | p2 | Psychic | Cloyster | miss; missed physical receiver |
| 13 | p1 | Switch sleeping Snorlax | Cloyster | top |
| 13 | p2 | Explosion | Spikes | acceptable, but over-cashed |
| 14 | p1 | Spikes | Spikes | top |
| 14 | p2 | Explosion | Explosion | top |
| 15 | p1 | Rapid Spin if available | Surf | acceptable fallback; Spin not revealed |
| 15 | p2 | Attack to KO Cloyster | Crunch | top by class |
| 16 | p1 | Earthquake | Earthquake | top |
| 16 | p2 | Switch Exeggutor | Exeggutor | top |

## Main Errors

Turn 3 hidden-info error:
After Spider Web and Perish Song, I made Baton Pass to a hidden trap owner the
top line without a fallback. The actual move was Destiny Bond, which cashed out
Smeargle immediately for Snorlax. In spectator-public mode, Baton Pass and a
recipient can be priced as strong-prior possibilities, but they cannot be the
main line without naming the fallback when the prior is wrong.

Turn 8 state error:
Snorlax had woken and the prompt showed it as healthy, not asleep. I still
treated sleep as if it were blocked and recommended Explosion for p2. Because
sleep was open again, Sleep Powder was the route-converting move.

Turn 10 branch-punish miss:
I correctly named Zapdos as the likely sleep absorber, but kept Sleep Powder as
p1's top move. The actual p1 line used Explosion into Zapdos. This is the
branch-action failure in clean form: after naming the absorber, choose the move
that beats the absorber.

## Useful Transfers

- The active-Cloyster hazard correction held on turn 14: p1 set missing Spikes
  before trying to Spin.
- The setup-threat boundary did not apply on turn 13: I overcalled Explosion
  from Cloyster, while the replay set Spikes first.
- Branch counter-switches were recognized sometimes, especially turn 16 p2
  Exeggutor into Steelix Earthquake, but not consistently.

## Policy Update

If the named branch is a status absorber, do not keep the status move on top by
habit. Re-rank:

1. cash-out or coverage that removes the absorber;
2. counter-switch to the absorber's owner;
3. setup/Substitute if it keeps the route through the absorber;
4. the original status move only if the absorber branch is unlikely or still
   favorable.

## Next Rep

Short focused branch-absorber drill or fresh transfer:
when I name the sleep/status absorber, force the top-three ranking to include
the absorber-punish action before the status move can remain top.
