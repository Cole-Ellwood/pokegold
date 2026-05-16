# Leech/RestTalk/Phaze Transfer 001 - smogtours-gen2ou-933839 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933839`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933839.log`

Replay search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&page=2`

Players: Hitmonlee Oswald vs gsc maestro.

Mode: spectator public, vanilla GSC. Replay actual move is a comparison oracle,
not an absolute answer key. No Team Preview: hidden teammates, moves, items,
and roles stayed in revealed / strong-prior / possible-only tiers.

Source-quality caveat: Smogtours replay, but not tied here to a specific
tournament round. Selected because it was unused locally, from a different
player pair than the prior transfer, and long enough for a 30-50 decision
sample.

## Sources Checked

Local docs before/during sealed work:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/active_pressure_before_status.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `policy_cards/support_handoff_after_job.md`

Local docs after scoring, before any further replay:

- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/cashout_boundary.md`
- `reviews/status_setup_handoff_review_001_2026-05-15.md`

Web/current sources used after scoring, before any further replay:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon, Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Smogon Forums, Zapdos GSC OU analysis:
  `https://www.smogon.com/forums/threads/zapdos-qc-2-2-gp-2-2.3673848/`
- Smogon Forums, Exeggutor GSC OU revamp:
  `https://www.smogon.com/forums/threads/exeggutor-revamp-gp-2-2.3646119/`
- Smogon Forums, GSC OU lead analysis:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`
- Smogon Forums, GSC OU sample teams breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Pikalytics current GSC Exeggutor, Zapdos, Cloyster, and Vaporeon snapshots:
  `https://www.pikalytics.com/pokedex/gsc/Exeggutor`
  `https://www.pikalytics.com/pokedex/gsc/Zapdos`
  `https://www.pikalytics.com/pokedex/gsc/Cloyster`
  `https://www.pikalytics.com/pokedex/gsc/Vaporeon`
- PokemonDB Leech Seed mechanics page:
  `https://pokemondb.net/move/leech-seed`

## Contamination Control

- Local `rg` found no prior `smogtours-gen2ou-933839` use before selection.
- Candidate screening used only current Showdown search metadata, local
  prior-use checks, and raw-log turn counts.
- I downloaded three unused candidates only to count turns: `935550`, `934420`,
  and `933839`. No move keywords or later turns were inspected during
  selection.
- The selected raw log was stored at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-933839.log`.
- No future turn was inspected before freezing each turn's top-three
  candidates.
- Web and broad local study happened only after the 47 scored side decisions
  were complete.

## Score Summary

Scored turns: 1-25.

Scorable decisions: 47.

Unscored:

- turn 10 p2, because Cloyster's Explosion KOed Exeggutor before the selected
  p2 move was recoverable;
- turn 17 p1, because sleep prevented action and the selected move was hidden;
- turn 25 p2, because full paralysis hid the selected move.

Top-match: 19 / 47.

Acceptable-match: 32 / 47.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0. Conditional own-move recommendations stayed conditional,
and possible-only hidden moves did not anchor a main recommendation.

Mechanics errors: 0. The post-score review still treats vanilla GSC Leech Seed,
Sleep Talk, Rest, and Sleep Clause as source material only for this vanilla
transfer; romhack-facing claims still require local mechanics evidence.

Positive-selection: 30 / 47.

Route-converting move chosen: 30 / 47.

Branch-punish chosen: 13 / 37 applicable branch decisions.

Earliest meaningful error: turn 1 p2, where I treated Exeggutor primarily as a
sleep lead and did not make Leech Seed the route pressure against Snorlax.

Interpretation:
Not progress. The severe/hidden/state/mechanics gate held, but top-match,
acceptable-match, positive selection, route conversion, and branch-punish
obedience all dropped from the previous fresh transfer. The packet avoided
obvious losses while repeatedly choosing safe or generic moves over route
improving moves.

## Turn Table

| Turn | Side | Frozen top-three | Actual | Grade | Positive-selection tags |
| --- | --- | --- | --- | --- | --- |
| 1 | p1 | 1. Lovely Kiss if available; 2. Double-Edge/Body Slam; 3. switch sleep absorber | Double-Edge | acceptable, not top | positive, route |
| 1 | p2 | 1. Sleep Powder; 2. status/Leech/Spikes support; 3. switch/Explosion | Leech Seed | miss, did not route-rank seed pressure | none |
| 2 | p1 | 1. switch to reset seed; 2. Double-Edge; 3. Rest/Curse | Double-Edge | acceptable, not top | positive |
| 2 | p2 | 1. Sleep Powder; 2. Explosion; 3. Psychic/Thief | Thief | miss, item removal was underpriced | none |
| 3 | p1 | 1. switch to reset seed; 2. Double-Edge; 3. Rest if available but seeded | Rest | miss, missed Rest reset under seed pressure | none |
| 3 | p2 | 1. Sleep Powder; 2. Explosion; 3. Psychic/Thief | Cloyster | miss, missed seed-to-Cloyster handoff | none |
| 4 | p1 | 1. switch to break seed; 2. Sleep Talk if revealed; 3. burn sleep | Cloyster | top | positive, route, branch |
| 4 | p2 | 1. Spikes; 2. Toxic; 3. Explosion later | Spikes | top | positive, route |
| 5 | p1 | 1. Spikes; 2. Toxic; 3. Surf/Spin if no Spikes | Spikes | top | positive, route |
| 5 | p2 | 1. Toxic opposing Cloyster; 2. Surf/Ice; 3. switch pressure | Toxic | top | positive, route |
| 6 | p1 | 1. Toxic if available; 2. Surf/Ice pressure; 3. switch Electric/Gengar owner | Surf | acceptable, not top | positive, route |
| 6 | p2 | 1. Surf pressure; 2. switch pressure; 3. Explosion branch | Raikou | miss, Electric receiver not named | none |
| 7 | p1 | 1. switch Ground/Electric owner; 2. Explosion read; 3. Surf chip | Steelix | top | positive, route, branch |
| 7 | p2 | 1. Thunder/Electric attack; 2. Rest if needed; 3. switch on Explosion read | Thunder | top | positive, route |
| 8 | p1 | 1. Earthquake active punish; 2. Roar on switch; 3. Curse/Explosion | Roar | acceptable, not top | positive, route, branch |
| 8 | p2 | 1. switch Cloyster; 2. Exeggutor; 3. Hidden Power if available | Cloyster | top | positive, route, branch |
| 9 | p1 | 1. Roar through Spikes; 2. Earthquake/coverage; 3. switch special owner | Cloyster | miss, wrong owner and seed map | none |
| 9 | p2 | 1. Leech Seed; 2. Sleep/Stun if available; 3. switch Cloyster | Leech Seed | top | positive, route, branch |
| 10 | p1 | 1. Ice/coverage if available; 2. switch to break seed; 3. Explosion read | Explosion | acceptable, not top | positive, route |
| 10 | p2 | hidden by pre-move KO | hidden | unscored | n/a |
| 11 | p1 | 1. switch Steelix/Ground unless HP coverage; 2. Hidden Power; 3. Rest/Whirlwind | Hidden Power | acceptable, not top | positive |
| 11 | p2 | 1. Rock Slide; 2. Explosion; 3. Raikou/Cloyster switch | Raikou | miss, receiver not route-ranked | none |
| 12 | p1 | 1. switch Steelix; 2. Whirlwind; 3. Hidden Power/Thunderbolt | Whirlwind | miss, phaze loop under-ranked | none |
| 12 | p2 | 1. switch Golem/Ground; 2. coverage if available; 3. Rest | Rest | miss, Rest reset underpriced | none |
| 13 | p1 | 1. Thunder/Thunderbolt; 2. switch Steelix; 3. Whirlwind | Thunderbolt | top | positive, route |
| 13 | p2 | 1. Golem Electric immunity; 2. Explosion if staying; 3. Toxic/Surf | sleeping Raikou | miss, missed sleeping special receiver | none |
| 14 | p1 | 1. Whirlwind phaze loop; 2. Thunderbolt chip; 3. Steelix if wake/coverage | Whirlwind | top | positive, route, branch |
| 14 | p2 | 1. Sleep Talk if available; 2. Golem; 3. burn sleep | Sleep Talk | top | positive, route, branch |
| 15 | p1 | 1. Whirlwind phaze loop; 2. Steelix into Normal hit; 3. Thunderbolt | Steelix | acceptable, not top | positive, route, branch |
| 15 | p2 | 1. Double-Edge/Body Slam; 2. Curse; 3. Lovely Kiss if available | Double-Edge | top | positive, route |
| 16 | p1 | 1. Roar with Spikes; 2. Earthquake; 3. Curse | Curse | acceptable, not top | positive, route |
| 16 | p2 | 1. switch Cloyster; 2. Earthquake if available; 3. Curse/Lovely Kiss | Lovely Kiss | miss, sleep branch underpriced | none |
| 17 | p1 | hidden by no-action sleep | hidden | unscored | n/a |
| 17 | p2 | 1. Curse; 2. Double-Edge; 3. switch Cloyster | Cloyster | miss, missed water pressure handoff | none |
| 18 | p1 | 1. switch water-resist pressure; 2. stay if Sleep Talk/wake; 3. sleeping Snorlax | Dragonite | acceptable by class | positive, route, branch |
| 18 | p2 | 1. Surf into Steelix; 2. Explosion on Zapdos read; 3. Toxic/Spikes | Surf | top | positive, route |
| 19 | p1 | 1. Thunder/Thunderbolt if available; 2. Zapdos; 3. Thunder Wave/status | Machamp | miss, missed physical converter handoff | none |
| 19 | p2 | 1. Toxic; 2. Ice Beam if available; 3. switch/cashout | sleeping Raikou | miss, missed sleeping receiver | none |
| 20 | p1 | 1. Fighting STAB pressure; 2. Curse on owner; 3. switch | Earthquake | acceptable, not top | positive |
| 20 | p2 | 1. bulky physical owner; 2. Sleep Talk; 3. Golem/boom route | Vaporeon | top by owner class | positive, route, branch |
| 21 | p1 | 1. Zapdos into Vaporeon; 2. Fighting STAB; 3. Earthquake chip | Zapdos | top | positive, route, branch |
| 21 | p2 | 1. Surf/Hydro pressure; 2. setup if switch; 3. Ice Beam if available | Surf | top | positive, route |
| 22 | p1 | 1. Thunderbolt; 2. Whirlwind on Ground/Raikou; 3. switch | Whirlwind | acceptable, not top | positive, route, branch |
| 22 | p2 | 1. sleeping Raikou; 2. Golem; 3. Surf | Golem | acceptable, not top | positive, branch |
| 23 | p1 | 1. Thunderbolt; 2. Whirlwind on Golem; 3. switch | Thunderbolt | top | positive, route |
| 23 | p2 | 1. Golem; 2. Raikou; 3. Surf | sleeping Raikou | acceptable, not top | positive, route |
| 24 | p1 | 1. Whirlwind; 2. Thunderbolt chip; 3. Steelix | Whirlwind | top | positive, route, branch |
| 24 | p2 | 1. Sleep Talk; 2. switch Golem/Vaporeon; 3. burn sleep | Sleep Talk -> Rest | top | positive, route, branch |
| 25 | p1 | 1. Whirlwind; 2. Steelix; 3. Thunderbolt | Thunder Wave | miss, missed status sacrifice into later route | none |
| 25 | p2 | hidden by full paralysis | hidden | unscored | n/a |

## Main Errors

Exeggutor seed and item-removal package:
I treated Exeggutor as a sleep/status script and did not re-solve after Leech
Seed. Turn 2 also missed the item route: after turn 1, Exeggutor had shown no
Leftovers recovery of its own, while Snorlax had Leftovers, making Thief a
stronger pressure candidate than generic Psychic or sleep.

Seed target and seeder replacement:
Turn 3 showed the cost of staying seeded. Snorlax Rested, but Exeggutor's side
switched to Cloyster, so the seeded Snorlax healed the current opposing active
while staying trapped in the seed clock. The answer needed to name whether the
route was seed reset, Rest reset, or immediate cash-out.

Rest reset and sleeping receiver maps:
Raikou's turn-12 Rest and later Sleep Talk made it a real route piece, not a
passive sleeping target. I repeatedly failed to price sleeping Raikou as an
Electric and special receiver that could re-enter to absorb Thunderbolt, blank
status, or roll Sleep Talk.

Revealed Whirlwind plus Spikes:
After Zapdos revealed Whirlwind into Spikes, the route was no longer "attack or
switch." The line could repeatedly convert forced switches, sleeping Raikou,
and Snorlax/Vaporeon/Golem entries. I under-committed to the loop on turn 12 and
again preferred generic damage or handoffs in later positions.

Receiver class after active pressure:
Machamp into Vaporeon, Cloyster into Raikou, and Zapdos into sleeping Raikou
were all cases where the correct action required naming the next board owner.
The misses were not about possible-only hidden teams; they were about failing
to use revealed or strong-prior receiver classes after the opponent made a
route-preserving switch.

## Reusable Lesson

Before choosing the safe visible-board move, reclassify the route after each
package reveal:

1. Leech Seed plus no-item Exeggutor means seed clock, Thief, Explosion, and
   switch-reset all need to be ranked before sleep script.
2. A RestTalk Electric that is asleep can still be the receiver, especially
   after Rest or Sleep Talk is public.
3. Revealed Whirlwind/Roar plus Spikes is a conversion route. Keep the phaze
   loop top until a public branch removes hazards, forces the phazer out, or
   opens a better converter.
4. Support status or damage is positive only when it names the later converter,
   not when it merely looks safe.

Next proof should be a fresh transfer only after the review: Exeggutor seed or
item-removal packages, RestTalk receiver re-entry, and revealed phaze-loop
commitment.
