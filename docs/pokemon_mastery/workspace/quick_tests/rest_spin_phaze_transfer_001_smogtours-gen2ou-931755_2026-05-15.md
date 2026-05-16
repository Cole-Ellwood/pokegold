# Rest/Spin/Phaze Transfer 001 - smogtours-gen2ou-931755 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-931755`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-931755.log`

Replay search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&page=4`

Players: s.islands vs betathunder.

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
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/hidden_role_voluntary_entry.md`
- `policy_cards/support_handoff_after_job.md`
- `reviews/spinblock_subgrowth_review_001_2026-05-15.md`

Local docs after scoring, before any further replay:

- `policy_cards/sleep_absorber_and_set_ambiguity.md`

Web/current sources used after scoring, before any further replay:

- Smogon Forums, Golem OU revamp:
  `https://www.smogon.com/forums/threads/golem-ou-revamp-qc-2-2-gp-2-2.3647044/`
- Smogon Forums, GSC OU Heracross:
  `https://www.smogon.com/forums/threads/gsc-ou-heracross.3699588/`
- Smogon Forums, Exeggutor revamp:
  `https://www.smogon.com/forums/threads/exeggutor-revamp-gp-2-2.3646119/`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon, Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Bulbapedia, Rest:
  `https://bulbapedia.bulbagarden.net/wiki/Rest_(move)`
- PokemonDB, Rest:
  `https://pokemondb.net/move/rest`

## Contamination Control

- Local `rg` found no prior `smogtours-gen2ou-931755` use before selection.
- Candidate screening used only current Showdown search metadata, local
  prior-use checks, and raw-log turn counts.
- I checked unused page-4 smogtours candidates `931755`, `931745`, `931770`,
  and `931794` only for local prior use and turn count.
- The selected raw log was stored at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-931755.log`.
- No future turn was inspected before freezing each turn's top-three
  candidates.
- Web and broad local study happened only after the 49 scored side decisions
  were complete.

## Score Summary

Scored turns: 1-25.

Scorable decisions: 49.

Unscored: turn 11 p2, because full paralysis hid Exeggutor's selected move.

Top-match: 22 / 49.

Acceptable-match: 30 / 49.

Severe blunders: 0.

State errors: 1. Turn 7 p1 failed to carry the exact Rest wake turn manually.

Hidden-info errors: 0.

Mechanics errors: 1. Turn 7 p1 recommended Sleep Talk on the turn Raikou woke
from Rest and could act.

Positive-selection: 37 / 49.

Route-converting move chosen: 34 / 49.

Branch-punish chosen: 12 / 39 applicable branch decisions.

Earliest meaningful error: turn 1 p1, where I over-ranked first-layer Spikes in
the Cloyster mirror and missed Raikou as the Toxic/status absorber.

Interpretation:
Not progress. Top-match recovered relative to the prior transfer, but
acceptable-match, positive-selection, route conversion, and branch-punish
obedience stayed below target, and a Rest wake-count mechanics/state error
appeared.

## Turn Table

| Turn | Side | Frozen top-three | Actual | Grade | Positive-selection tags |
| --- | --- | --- | --- | --- | --- |
| 1 | p1 | 1. Spikes; 2. Toxic; 3. pressure switch only on status read | Raikou | miss, missed Toxic absorber | none |
| 1 | p2 | 1. Spikes; 2. Toxic; 3. Surf/Explosion branch | Toxic | acceptable, not top | positive |
| 2 | p1 | 1. Thunder; 2. Hidden Power/fallback coverage; 3. switch only on Ground read | Thunder | top | positive, route |
| 2 | p2 | 1. Electric/special absorber; 2. Spikes if staying; 3. Toxic/Explosion | Raikou | top by class | positive, route, branch |
| 3 | p1 | 1. switch owner; 2. Thunder chip; 3. Rest after damage | Thunder | acceptable, not top | positive |
| 3 | p2 | 1. Thunder; 2. Hidden Power if available; 3. Toxic/switch | Thunder | top | positive, route |
| 4 | p1 | 1. Rest; 2. switch owner; 3. Thunder if no reset | Rest | top | positive, route |
| 4 | p2 | 1. Thunder; 2. Hidden Power; 3. Rest/switch | Thunder | top | positive, route |
| 5 | p1 | 1. Sleep Talk; 2. preserve sleeper; 3. burn sleep | Sleep Talk -> Hidden Power | top | positive, route |
| 5 | p2 | 1. Thunder; 2. Hidden Power if available; 3. switch | Hidden Power | acceptable coverage | positive |
| 6 | p1 | 1. Sleep Talk; 2. preserve sleeper; 3. burn sleep | Sleep Talk -> Hidden Power | top | positive, route |
| 6 | p2 | 1. Hidden Power; 2. Thunder; 3. switch | Hidden Power | top | positive, route |
| 7 | p1 | 1. Sleep Talk; 2. attack if awake; 3. switch | Thunder | miss, Rest wake-count mechanics error | state, mechanics |
| 7 | p2 | 1. Hidden Power; 2. Thunder; 3. switch | Snorlax | miss | none |
| 8 | p1 | 1. Cloyster; 2. Thunder; 3. Rest if pressured | Cloyster | top | positive, route |
| 8 | p2 | 1. Lovely Kiss; 2. Double-Edge; 3. switch | Raikou | miss | none |
| 9 | p1 | 1. Raikou; 2. Explosion read; 3. Spikes only on switch | Raikou | top | positive, route, branch |
| 9 | p2 | 1. Thunder; 2. Hidden Power; 3. switch | Thunder | top | positive, route |
| 10 | p1 | 1. Hidden Power; 2. Thunder; 3. Rest/switch | Thunder | acceptable, not top | positive, route |
| 10 | p2 | 1. Hidden Power; 2. Thunder; 3. bulky Grass/special pivot | Exeggutor | miss | none |
| 11 | p1 | 1. Hidden Power; 2. stay as sleep absorber; 3. Explosion owner if needed | Hidden Power | top | positive, route |
| 11 | p2 | hidden by full paralysis | hidden | unscored | n/a |
| 12 | p1 | 1. Explosion absorber, Ghost if available; 2. Hidden Power; 3. Cloyster fallback | Gengar | top by class | positive, route, branch |
| 12 | p2 | 1. Explosion/cash-out; 2. Sleep Powder; 3. switch | Raikou | miss | none |
| 13 | p1 | 1. Hypnosis if available; 2. Explosion read; 3. coverage | Raikou | miss | none |
| 13 | p2 | 1. Snorlax/Gengar answer; 2. Thunder; 3. Exeggutor pivot | Exeggutor | miss | none |
| 14 | p1 | 1. Gengar for Explosion/EQ; 2. Hidden Power; 3. RestTalk Raikou as sleep absorber | Gengar | top move, wrong branch | positive |
| 14 | p2 | 1. Sleep Powder; 2. switch; 3. Explosion high-risk into Ghost | Sleep Powder | top | positive, route, branch |
| 15 | p1 | 1. stay to cover Explosion; 2. Raikou on Psychic; 3. Cloyster | Exeggutor | miss, missed Psychic resist handoff | none |
| 15 | p2 | 1. Psychic; 2. Leech/status; 3. switch | Psychic | top | positive, route |
| 16 | p1 | 1. Sleep Powder; 2. Psychic; 3. Leech/Explosion branch | Psychic | acceptable, not top | positive |
| 16 | p2 | 1. special/status receiver switch; 2. Psychic; 3. Explosion | Heracross | miss, poor receiver map | none |
| 17 | p1 | 1. Gengar/Bug owner; 2. Cloyster; 3. Psychic only on switch | Cloyster | miss, wrong reset branch | none |
| 17 | p2 | 1. Megahorn; 2. switch reset; 3. Rest if available | Cloyster | miss | none |
| 18 | p1 | 1. Spikes; 2. Toxic; 3. Surf/Spin later | Toxic | acceptable, not top | positive |
| 18 | p2 | 1. Spikes; 2. Toxic; 3. switch Raikou | Spikes | top | positive, route |
| 19 | p1 | 1. Spikes before Spin; 2. Rapid Spin if available; 3. Toxic/Surf | Spikes | top | positive, route |
| 19 | p2 | 1. Toxic; 2. Raikou switch; 3. Surf | Raikou | acceptable, not top | positive |
| 20 | p1 | 1. Raikou; 2. Snorlax; 3. Explosion read | Raikou | top | positive, route, branch |
| 20 | p2 | 1. Thunder; 2. Hidden Power; 3. switch on Explosion | Thunder | top | positive, route |
| 21 | p1 | 1. Rest; 2. Snorlax/Ground owner; 3. Hidden Power | Snorlax | acceptable, not top | positive |
| 21 | p2 | 1. Hidden Power; 2. Thunder; 3. Roar/switch if available | Golem | miss, missed Ground spin/phaze package | none |
| 22 | p1 | 1. Gengar for Explosion/EQ; 2. coverage if available; 3. Lovely Kiss | Lovely Kiss | miss, missed sleep route | none |
| 22 | p2 | 1. Earthquake/Rock pressure; 2. Explosion read; 3. switch | Rapid Spin | miss, missed Golem spinner role | none |
| 23 | p1 | 1. Lovely Kiss; 2. Gengar on Explosion; 3. Earthquake/coverage | Double-Edge | miss, wrong way to stop Golem | none |
| 23 | p2 | 1. Earthquake/Rock Slide; 2. Explosion; 3. switch | Roar | miss, missed Spin + Roar package | none |
| 24 | p1 | 1. Surf into Golem; 2. Spikes reset on switch; 3. Rapid Spin later | Spikes | miss, under-ranked post-Spin reset | none |
| 24 | p2 | 1. Raikou/Cloyster switch; 2. Explosion; 3. Roar | Raikou | top by class | positive, route, branch |
| 25 | p1 | 1. Explosion into no-Ghost Raikou; 2. Snorlax/Exeggutor absorber; 3. Surf/Toxic | Exeggutor | miss, over-ranked cash-out | none |
| 25 | p2 | 1. Thunder; 2. switch into Explosion resist; 3. Hidden Power | Thunder | top | positive, route |

## Main Errors

Rest wake-count:
Turn 7 was a concrete mechanics/state failure. Raikou used Rest on turn 4,
spent turns 5 and 6 asleep using Sleep Talk, then woke and attacked on turn 7.
The helper still displayed `slp` before the turn, so the answer needed manual
Rest timing instead of a blind Sleep Talk recommendation.

Golem's full utility package:
I treated Golem mostly as Earthquake, Rock Slide, or Explosion. The replay
revealed the source-backed package: Rapid Spin, Roar, Explosion pressure, and
Normal resistance. Turn 22's Spin and turn 23's Roar were exactly the kind of
route moves that convert hazards and phaze after the spin.

Post-Spin reset:
After Golem cleared p2's Spikes, p1 Cloyster was active against a likely Golem
switch. I over-ranked Surf into the visible Golem and under-ranked resetting
Spikes before Raikou entered. This was the hazard card in direct form.

Sleep and Explosion branch conflict:
Against Exeggutor, I over-focused on Explosion absorption and did not always
cover Sleep Powder or Psychic. Gengar can be the Explosion owner, but if the
opponent's top branch is sleep or Psychic, the correct absorber may be a
RestTalk Electric, Exeggutor, or another status/typing owner.

## Reusable Lesson

Before choosing the visible-board move, identify whether the public package has
changed the role:

1. Rest wake count is manual evidence. After two Rest sleep turns, expect the
   wake-and-act turn even if a helper prompt still says asleep.
2. Golem in GSC can be Rapid Spin plus Roar plus Explosion, not just a boom
   button or Electric immunity.
3. After a spin removes the opponent's Spikes and the setter is active, reset
   Spikes before chasing damage unless the active threat converts immediately.
4. When Exeggutor is low, rank Sleep Powder, Psychic, Explosion, and switch
   preservation as separate branches; do not solve only one of them.

Next proof should be a fresh transfer only after the review: exact Rest wake
counts, Golem/Rock spinner packages, and post-Spin Spikes reset.
