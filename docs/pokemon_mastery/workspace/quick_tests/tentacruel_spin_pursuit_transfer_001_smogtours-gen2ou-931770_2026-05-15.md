# Tentacruel Spin/Pursuit Transfer 001 - smogtours-gen2ou-931770 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-931770`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-931770.log`

Replay search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&page=4`

Players: bored sukuna vs tahat squared.

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
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/branch_action_after_naming.md`
- `reviews/rest_spin_phaze_review_001_2026-05-15.md`

Local docs after scoring, before any further replay:

- `policy_cards/support_handoff_after_job.md`

Web/current sources used after scoring, before any further replay:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums, GSC OU sample teams breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon Forums, Tentacruel revamp:
  `https://www.smogon.com/forums/threads/tentacruel-revamp-qc-3-3.3474651/`
- Smogon Forums, Golem OU revamp:
  `https://www.smogon.com/forums/threads/golem-ou-revamp-qc-2-2-gp-2-2.3647044/`
- Smogon, Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`

## Contamination Control

- Local `rg` found no prior `smogtours-gen2ou-931770` use before selection.
- Candidate screening used only current Showdown search metadata, local
  prior-use checks, and raw-log turn counts.
- I checked unused candidates from current search pages only for local prior
  use and turn count; no move keywords or later turns were inspected during
  selection.
- The selected raw log was stored at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-931770.log`.
- No future turn was inspected before freezing each turn's top-three
  candidates.
- Web and broad local study happened only after the 49 scored side decisions
  were complete.

## Score Summary

Scored turns: 1-25.

Scorable decisions: 49.

Unscored: turn 17 p2, because Dynamic Punch KOed Tyranitar before the selected
p2 move was recoverable.

Top-match: 18 / 49.

Acceptable-match: 35 / 49.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0. Rest wake and switch-out counters were manually tracked
instead of relying only on helper status labels.

Positive-selection: 36 / 49.

Route-converting move chosen: 35 / 49.

Branch-punish chosen: 16 / 41 applicable branch decisions.

Earliest meaningful error: turn 2 p2, where I treated Forretress's hazard job
as immediate and missed Snorlax as the route reset into Nidoking.

Interpretation:
Mixed but not progress. Acceptable-match cleared the local gate and severe,
hidden, state, and mechanics errors stayed clean. This is still not broad
progress because top-match fell, positive-selection fell slightly, and branch
obedience remained weak.

## Turn Table

| Turn | Side | Frozen top-three | Actual | Grade | Positive-selection tags |
| --- | --- | --- | --- | --- | --- |
| 1 | p1 | 1. Double-Edge/Body Slam; 2. Earthquake if available; 3. Lovely Kiss | Double-Edge | top | positive, route |
| 1 | p2 | 1. Normal resist/special owner; 2. Thunder; 3. Roar if available | Forretress | top by class | positive, route, branch |
| 2 | p1 | 1. pressure owner; 2. Lovely Kiss; 3. coverage | Nidoking | acceptable pressure handoff | positive, route |
| 2 | p2 | 1. Spikes; 2. Toxic; 3. Explosion branch | Snorlax | miss | none |
| 3 | p1 | 1. Lovely Kiss if available; 2. Earthquake; 3. coverage | Cloyster | miss | none |
| 3 | p2 | 1. switch owner; 2. Lovely Kiss; 3. Earthquake | Curse | miss | none |
| 4 | p1 | 1. Toxic; 2. Explosion; 3. Spikes if Lax leaves | Toxic | top | positive, route, branch |
| 4 | p2 | 1. switch; 2. Double-Edge; 3. Rest/Curse | Double-Edge | acceptable, not top | positive, route |
| 5 | p1 | 1. Explosion; 2. switch owner; 3. Spikes if Lax leaves | Spikes | acceptable branch | positive, route, branch |
| 5 | p2 | 1. Rest; 2. switch; 3. Double-Edge | Tentacruel | acceptable preservation | positive, route |
| 6 | p1 | 1. Electric/Psychic owner; 2. Explosion; 3. Surf/Ice chip | Gengar | miss, missed spinner branch | none |
| 6 | p2 | 1. setup; 2. Surf; 3. Rapid Spin | Rapid Spin | acceptable, under-ranked | positive, route, branch |
| 7 | p1 | 1. Thunder/Electric coverage; 2. Hypnosis; 3. Explosion | Thunder | top | positive, route, branch |
| 7 | p2 | 1. Raikou/Snorlax switch; 2. Surf; 3. setup | Tyranitar | miss | none |
| 8 | p1 | 1. Nidoking/Ground owner; 2. Explosion; 3. Thunder | Nidoking | top | positive, route, branch |
| 8 | p2 | 1. Pursuit; 2. Rock/Dark hit; 3. switch | Pursuit | top | positive, route, branch |
| 9 | p1 | 1. Earthquake; 2. Lovely Kiss; 3. coverage | Thief | miss | none |
| 9 | p2 | 1. switch owner; 2. stay attack; 3. preserve | Snorlax | acceptable | positive, route |
| 10 | p1 | 1. Earthquake; 2. Lovely Kiss; 3. switch | Tyranitar | miss | none |
| 10 | p2 | 1. Rest; 2. switch; 3. Double-Edge/Earthquake | Rest | top | positive, route, branch |
| 11 | p1 | 1. setup/attack; 2. Rock Slide; 3. Roar | Roar | acceptable, not top | positive, route, branch |
| 11 | p2 | 1. Sleep Talk if available; 2. switch; 3. burn sleep | Skarmory | acceptable preservation | positive, route |
| 12 | p1 | 1. Gengar spinblock; 2. Roar; 3. pressure owner | Zapdos | acceptable pressure owner | positive, route |
| 12 | p2 | 1. Rapid Spin; 2. Surf; 3. switch | Surf | acceptable, not top | positive, route |
| 13 | p1 | 1. Thunder; 2. Thunder Wave; 3. Whirlwind if available | Thunder | top | positive, route |
| 13 | p2 | 1. Raikou/Tyranitar receiver; 2. Rapid Spin; 3. Surf | Raikou | top by class | positive, route, branch |
| 14 | p1 | 1. Snorlax/Nidoking owner; 2. Thunder; 3. Rest | Snorlax | top by class | positive, route, branch |
| 14 | p2 | 1. Thunder; 2. Roar if available; 3. Rest/switch | Forretress | miss | none |
| 15 | p1 | 1. Fire/active pressure; 2. Double-Edge; 3. switch pressure | Gengar | miss | none |
| 15 | p2 | 1. Rapid Spin; 2. Spikes; 3. Toxic/Explosion | Spikes | acceptable, not top | positive, route, branch |
| 16 | p1 | 1. Thunder; 2. switch; 3. Explosion | Thunder | top | positive, route |
| 16 | p2 | 1. coverage into Gengar; 2. Explosion; 3. Tyranitar/Raikou switch | Tyranitar | acceptable, not top | positive, route |
| 17 | p1 | 1. Thunder; 2. switch; 3. Explosion | Dynamic Punch | miss, correct revealed-package punish next time | positive |
| 17 | p2 | hidden by pre-move KO | hidden | unscored | n/a |
| 18 | p1 | 1. Snorlax/Nidoking owner; 2. Dynamic Punch; 3. Explosion | Nidoking | top by class | positive, route, branch |
| 18 | p2 | 1. Thunder; 2. Hidden Power; 3. Roar/Rest | Hidden Power | acceptable | positive, route |
| 19 | p1 | 1. Earthquake; 2. switch; 3. Lovely Kiss | Earthquake | top | positive, route |
| 19 | p2 | 1. switch Skarmory/Forretress; 2. Hidden Power; 3. Rest/sack | sleeping Snorlax | miss, missed RestTalk receiver | none |
| 20 | p1 | 1. Earthquake; 2. pressure; 3. switch | Tyranitar | miss, missed Sleep Talk absorber | none |
| 20 | p2 | 1. stay/Sleep Talk; 2. switch; 3. burn sleep | Sleep Talk -> Double-Edge | top | positive, route |
| 21 | p1 | 1. Roar; 2. Rock Slide/Pursuit; 3. switch | Pursuit | miss, non-converting chip | none |
| 21 | p2 | 1. Sleep Talk; 2. switch; 3. burn sleep | Sleep Talk -> Double-Edge | top | positive, route |
| 22 | p1 | 1. switch/Ghost owner; 2. Roar; 3. Rock Slide/Pursuit | Rock Slide | acceptable, not top | positive, route |
| 22 | p2 | 1. Rest on wake turn; 2. Double-Edge; 3. switch | Rest | top | positive, route, branch |
| 23 | p1 | 1. Roar; 2. Rock Slide; 3. switch | Rock Slide | acceptable, not top | positive, route |
| 23 | p2 | 1. Sleep Talk; 2. switch; 3. burn sleep | Tentacruel | acceptable spinner route | positive, route |
| 24 | p1 | 1. Gengar spinblock; 2. Rock Slide; 3. Zapdos/Nidoking | Gengar | top | positive, route, branch |
| 24 | p2 | 1. Rapid Spin; 2. Surf; 3. switch | Protect | miss | none |
| 25 | p1 | 1. Thunder; 2. Dynamic Punch; 3. switch | Thunder | top | positive, route, branch |
| 25 | p2 | 1. Surf; 2. switch; 3. Protect/Rapid Spin | Raikou | acceptable, not top | positive, route |

## Main Errors

Tentacruel spinner package:
I initially read Tentacruel as setup or generic Water pressure and put Rapid
Spin too low. Once Rapid Spin was revealed, I handled the Gengar block better,
but still failed to rank Protect as part of the spin route: Protect can scout
the spinblock response and buy Leftovers recovery before choosing Surf, Spin,
or switch.

Spinblock into Pursuit trap:
Gengar blocked the first Rapid Spin, then Tyranitar entered and Pursuit trapped
it. I did answer with a switch on turn 8, but I did not treat the sequence as a
single package: spinner reveals Spin, Ghost enters, Pursuit user enters, then
Gengar must either punish with Thunder/Dynamic Punch or preserve itself with
the correct tax.

Rest switch-out counters:
The prior Rest correction held on turn 22, but the replay added the switch-out
boundary. Snorlax used Rest on turn 10, switched out on turn 11 before burning
a sleep action, returned on turn 19 still asleep, burned Sleep Talk turns on
20 and 21, and woke/rested again on turn 22. Rest counters advance on sleeping
action turns, not while the Pokemon is benched.

Dynamic Punch branch-punish:
Gengar's Dynamic Punch into Tyranitar was the exact revealed-package punish
that preserved the spinblocker against Pursuit. I kept thinking of Gengar as
Thunder plus Explosion and did not promote Dynamic Punch when Tyranitar was
paralyzed and low.

## Reusable Lesson

When a spinner route starts, solve the whole support chain:

1. Tentacruel with Rapid Spin can also Surf, Protect, and switch. Protect is a
   scouting and recovery action that can make the next Spin or switch safer.
2. A Ghost spinblocker invites Pursuit. If Gengar has revealed Dynamic Punch or
   coverage into the Pursuit user, rank that punish before a generic switch.
3. Rest sleep counters only advance on actual sleeping action turns. If the
   Rest user switches before acting asleep, carry the remaining sleep turns.
4. A sleeping RestTalk Snorlax can be the receiver into Nidoking or special
   pressure; do not flatten it into dead weight.

Next proof should be a fresh transfer only after the review: Tentacruel/other
spinner Protect lines, Pursuit-trap follow-up after spinblock, and Rest
switch-out wake counters.
