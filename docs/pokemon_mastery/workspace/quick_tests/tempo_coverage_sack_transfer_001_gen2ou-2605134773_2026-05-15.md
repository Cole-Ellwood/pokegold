# Tempo Coverage/Sack Transfer 001 - gen2ou-2605134773 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/gen2ou-2605134773`

Raw log:
`https://replay.pokemonshowdown.com/gen2ou-2605134773.log`

Replay search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&page=2`

Mode: spectator public, vanilla GSC. Replay actual move is a pro-comparison
oracle, not an absolute answer key. No Team Preview: hidden teammates, moves,
items, and roles stayed in revealed / strong-prior / possible-only tiers.

Source-quality caveat: public ladder/search replay, not confirmed tournament.
Selected because it was unused locally, rated 1336 in the current search feed,
from a different player pair than the prior replay, and long enough for a
30-decision sample.

## Sources Checked

Local docs before/during study:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/hidden_role_voluntary_entry.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/hazard_loop_spin_window.md`
- `reviews/low_cloyster_cashout_review_001_2026-05-15.md`

Web/current sources used after scoring, before any further replay:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, Cloyster OU Revamp:
  `https://www.smogon.com/forums/threads/cloyster-ou-revamp-qc-2-2-gp-2-2.3652352/`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, Gengar WIP:
  `https://www.smogon.com/forums/threads/gengar-wip.3703761/`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon, Introduction to Status Moves in GSC:
  `https://www.smogon.com/forums/threads/introduction-to-status-moves-in-gsc.3448819/`

## Contamination Control

- Local `rg` found no prior `2605134773` artifact before selection.
- Candidate screening used only search-feed metadata, local prior-use checks,
  and turn count.
- The raw log was downloaded to `tmp/pokemon_mastery_replays/`.
- No future turns were inspected before freezing each turn's top-three
  candidates.
- Web and local study review happened only after the 32 scored side decisions
  were complete.
- No keyword screening for Icy Wind, Gengar, Dynamic Punch, Earthquake,
  Tyranitar, Zapdos, Rest, or sack sequences.

## Score Summary

Scored turns: 1-17.

Scorable decisions: 32.

Unscored: turn 3 p2 and turn 8 p1 because the selected action was hidden by
pre-move KO or forced faint resolution.

Top-match: 14 / 32.

Acceptable-match: 24 / 32.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 25 / 32.

Route-converting move chosen: 21 / 32.

Branch-punish chosen: 13 / 23 applicable branch decisions.

Earliest meaningful error: turn 1 p1, where I kept Gengar active in the frozen
ranking and missed Cloyster as the Earthquake/sleep-routing owner.

Interpretation:
Not progress. Severe, hidden-info, state, and mechanics gates held, but the
top rate fell below gate after the prior limited positive transfer. The main
positive-selection misses were tempo coverage before Spikes, Gengar finishing
the Dynamic Punch route without dying to Earthquake, Zapdos Rest reset, and
low-Tyranitar defensive sack into boosted Snorlax.

## Turn Table

| Turn | Side | Frozen top-three | Actual | Grade | Positive-selection tags |
| --- | --- | --- | --- | --- | --- |
| 1 | p1 | 1. Hypnosis; 2. Ice Punch/coverage; 3. switch only if coverage risk dominates | Cloyster | miss; missed Cloyster owner | none |
| 1 | p2 | 1. Lovely Kiss; 2. Earthquake; 3. Ice/coverage branch | Earthquake | acceptable active pressure | positive, route |
| 2 | p1 | 1. Spikes; 2. Surf/Icy Wind; 3. Explosion branch | Icy Wind | miss; missed tempo coverage before layer | positive only |
| 2 | p2 | 1. Lovely Kiss; 2. Earthquake; 3. switch owner | Lovely Kiss | top despite miss | positive, route |
| 3 | p1 | 1. Surf; 2. Spikes; 3. switch only if sleep risk flips it | Surf | top | positive, route |
| 3 | p2 | hidden by pre-move KO | forced Zapdos | unscored | n/a |
| 4 | p1 | 1. Spikes; 2. Explosion high-risk; 3. preserve with Ground owner | Nidoking | acceptable preservation, not top | positive, branch |
| 4 | p2 | 1. Thunder; 2. Hidden Power if available; 3. switch owner | Thunder | top | positive, route |
| 5 | p1 | 1. Lovely Kiss into exit; 2. Ice Beam/coverage; 3. Earthquake | Lovely Kiss | top | positive, route, branch |
| 5 | p2 | 1. Hidden Power if available; 2. switch sleep owner; 3. Thunder fallback | Snorlax | acceptable by sleep-owner class | positive, branch |
| 6 | p1 | 1. coverage into sleeping Snorlax; 2. setup/handoff owner; 3. Spikes owner | Machamp | acceptable setup-owner handoff | positive, route |
| 6 | p2 | 1. Sleep Talk if revealed; 2. burn sleep; 3. Zapdos/Nidoking owner | Zapdos | acceptable owner handoff | positive, branch |
| 7 | p1 | 1. Rock Slide; 2. switch Nidoking/Ground owner; 3. Cross Chop if receiver | Rock Slide | top | positive, route |
| 7 | p2 | 1. Thunder; 2. Hidden Power into Nidoking; 3. switch owner | Thunder | top | positive, route |
| 8 | p1 | hidden by pre-move KO | forced Gengar | unscored | n/a |
| 8 | p2 | 1. Thunder; 2. Hidden Power branch; 3. switch/preserve | Thunder | top | positive, route |
| 9 | p1 | 1. Ice Punch/coverage; 2. Hypnosis; 3. Explosion high-risk with branches | Ice Punch | top | positive, route, branch |
| 9 | p2 | 1. switch Tyranitar/special owner; 2. Thunder; 3. preserve Zapdos | Tyranitar | top by owner class | positive, branch |
| 10 | p1 | 1. Dynamic Punch; 2. switch/preserve; 3. Explosion high-risk | Dynamic Punch | top | positive, route, branch |
| 10 | p2 | 1. Pursuit/Dark pressure; 2. Rock Slide; 3. Curse | Curse | acceptable setup, not top | positive only |
| 11 | p1 | 1. Thunder/coverage; 2. Dynamic Punch; 3. Explosion if no immunity branch | Thunder | top | positive, route |
| 11 | p2 | 1. switch/preserve; 2. Earthquake if it survives; 3. Rock Slide/Pursuit | Earthquake | acceptable but costly | positive, route |
| 12 | p1 | 1. Earthquake/KO low Tyranitar; 2. Ice Beam into Zapdos branch; 3. Lovely Kiss if owner enters | Ice Beam | acceptable branch but not top | positive, branch |
| 12 | p2 | 1. preserve with Zapdos/owner; 2. sack Tyranitar; 3. attack | Zapdos | top by owner class | positive, branch |
| 13 | p1 | 1. Ice Beam; 2. Lovely Kiss only if switch; 3. handoff if Zapdos Rests | Ice Beam | top | positive, route |
| 13 | p2 | 1. switch owner; 2. Thunder; 3. Rest only if it survives route | Rest | miss; missed Rest reset | none |
| 14 | p1 | 1. Ice Beam; 2. switch/handoff only if owner enters; 3. Lovely Kiss blocked by sleep use | Ice Beam | top | positive, route |
| 14 | p2 | 1. Sleep Talk if revealed; 2. switch Ice Beam owner; 3. burn sleep | Snorlax | acceptable owner handoff | positive, branch |
| 15 | p1 | 1. coverage pressure; 2. setup/handoff owner; 3. Cloyster hazard owner | Snorlax | acceptable setup-owner handoff | positive, route |
| 15 | p2 | 1. Sleep Talk if revealed; 2. switch Ice Beam owner; 3. burn sleep | Zapdos | miss; wrong sleeping owner for Snorlax board | none |
| 16 | p1 | 1. Curse; 2. attack; 3. switch only if Ghost branch dominates | Curse | top | positive, route |
| 16 | p2 | 1. switch Ghost/physical owner; 2. Sleep Talk if revealed; 3. burn sleep | Gengar | top by owner class | positive, branch |
| 17 | p1 | 1. Earthquake if available; 2. switch Gengar owner; 3. Body Slam/attack | Earthquake | top | positive, route, branch |
| 17 | p2 | 1. Hypnosis/Explosion/coverage with Gengar; 2. switch low Tyranitar sack; 3. preserve Gengar | Tyranitar | miss; defensive sack not found | none |

## Main Errors

Turn 2 tempo coverage before Spikes:
I over-applied "Cloyster should set Spikes first." Icy Wind was the actual
positive move because it slowed and damaged Nidoking, changed the speed map,
and let Cloyster finish with Surf while still healthy. Smogon sources support
Icy Wind as a specific anti-spinner/tempo tool even though Spikes is usually
Cloyster's core job.

Turn 11 Gengar pressure into Earthquake:
Dynamic Punch created the right route into Tyranitar, but the follow-up Thunder
let +1 Tyranitar remove Gengar with Earthquake. This was not severe because
the actual move removed most of Tyranitar's remaining route value, but it was
not clean route conversion. After Dynamic Punch, ask whether the target can
still KO the route piece before repeating coverage.

Turn 13 Zapdos Rest reset:
I under-ranked Rest from low Zapdos. The correction is not to assume Rest as
fact before reveal; it is to name Rest as the main reset branch when a damaged
RestTalk-class Electric can survive the incoming coverage and reclaim HP.

Turn 17 defensive sack owner:
I missed p2's low Tyranitar sack into boosted Snorlax. Gengar was the active
boosted-Lax owner, but the opponent used the nearly-dead Tyranitar to absorb
Earthquake and preserve Gengar for the next board. This is the defensive sack
owner rule from `cashout_boundary.md`.

## Reusable Lesson

Support-piece ordering is not "field job always before damage." The sequence is:

1. Does tempo coverage immediately remove or cripple the active threat while
   the support piece survives?
2. Does the field job convert before the support piece is forced out or killed?
3. If the field job will not convert yet, is there an exact target for cash-out
   or a defensive sack that preserves the real owner?

Next proof should be another fresh transfer only after the review: tempo
coverage before field job, Rest reset after coverage pressure, and defensive
sack owner after a correct active-route read.
