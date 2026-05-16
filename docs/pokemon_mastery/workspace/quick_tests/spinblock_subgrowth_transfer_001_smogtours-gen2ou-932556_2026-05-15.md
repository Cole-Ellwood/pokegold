# Spinblock/SubGrowth Transfer 001 - smogtours-gen2ou-932556 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-932556`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-932556.log`

Replay search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&page=4`

Players: cyberacc vs Bohrier.

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
- `policy_cards/hazard_loop_spin_window.md`
- `reviews/leech_resttalk_phaze_review_001_2026-05-15.md`

Local docs after scoring, before any further replay:

- `policy_cards/support_handoff_after_job.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/hidden_role_voluntary_entry.md`

Web/current sources used after scoring, before any further replay:

- Smogon Dex, Forretress GSC:
  `https://www.smogon.com/dex/gs/pokemon/forretress/`
- Smogon Dex, Gengar GSC:
  `https://www.smogon.com/dex/gs/pokemon/gengar/`
- Smogon Dex, Jolteon GSC:
  `https://www.smogon.com/dex/gs/pokemon/jolteon/`
- Smogon Dex, Starmie GSC:
  `https://www.smogon.com/dex/gs/pokemon/starmie/`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums, GSC OU sample teams breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Pikalytics current GSC Forretress, Gengar, Jolteon, and Starmie snapshots:
  `https://www.pikalytics.com/pokedex/gsc/Forretress`
  `https://www.pikalytics.com/pokedex/gsc/Gengar`
  `https://www.pikalytics.com/pokedex/gsc/Jolteon`
  `https://www.pikalytics.com/pokedex/gsc/Starmie`

## Contamination Control

- Local `rg` found no prior `smogtours-gen2ou-932556` use before selection.
- Candidate screening used only current Showdown search metadata, local
  prior-use checks, and raw-log turn counts.
- I downloaded page-4 smogtours candidates only to count turns: `932564`,
  `932554`, `932556`, `932548`, `931794`, `931770`, `931755`, and `931745`.
  No move keywords or later turns were inspected during selection.
- The selected raw log was stored at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-932556.log`.
- No future turn was inspected before freezing each turn's top-three
  candidates.
- Web and broad local study happened only after the 49 scored side decisions
  were complete.

## Score Summary

Scored turns: 1-25.

Scorable decisions: 49.

Unscored: turn 20 p2, because Starmie's Surf KOed Nidoking before the selected
p2 move was recoverable.

Top-match: 14 / 49.

Acceptable-match: 34 / 49.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 1. Turn 11 p2 let possible-only Nidoking item state anchor
a Thief recommendation. Nidoking's later Leftovers reveal showed that the item
route was not public fact.

Mechanics errors: 0.

Positive-selection: 38 / 49.

Route-converting move chosen: 35 / 49.

Branch-punish chosen: 9 / 38 applicable branch decisions.

Earliest meaningful error: turn 2 p2, where I over-priced Fire Blast/coverage
into Forretress and missed Lovely Kiss as the branch-changing move.

Interpretation:
Mixed but not progress. Positive-selection recovered from the previous bad
transfer, but top-match fell, branch-punish obedience fell again, and the
hidden-info gate failed once. This is not a mastery signal and not broad
progress.

## Turn Table

| Turn | Side | Frozen top-three | Actual | Grade | Positive-selection tags |
| --- | --- | --- | --- | --- | --- |
| 1 | p1 | 1. Electric attack; 2. Roar/scout if available; 3. double to Spikes owner on switch | Forretress | acceptable, not top | positive, route |
| 1 | p2 | 1. Snorlax/Ground receiver; 2. Spikes if staying; 3. Toxic/Surf | Snorlax | top by class | positive, route, branch |
| 2 | p1 | 1. Spikes; 2. Toxic; 3. sleep/Normal absorber switch | Misdreavus | acceptable, not top | positive, route |
| 2 | p2 | 1. Fire coverage if available; 2. Curse/attack; 3. switch | Lovely Kiss | miss | none |
| 3 | p1 | 1. Mean Look trap if available; 2. Perish/Song route; 3. Thunder/status | Toxic | miss, status into switch not ranked | none |
| 3 | p2 | 1. Earthquake if available; 2. Lovely Kiss; 3. switch to Ghost/status answer | Zapdos | acceptable switch class | positive |
| 4 | p1 | 1. Raikou receiver; 2. Forretress; 3. stay/scout | Snorlax | miss, missed Snorlax sponge | none |
| 4 | p2 | 1. Thunder/Electric pressure; 2. status/coverage; 3. Rest/scout | Snorlax | miss, missed mirror reset | none |
| 5 | p1 | 1. Lovely Kiss if available; 2. Curse; 3. Double-Edge/Body Slam | Double-Edge | acceptable, not top | positive, route |
| 5 | p2 | 1. Lovely Kiss; 2. Curse; 3. Double-Edge/switch | Lovely Kiss | top | positive, route |
| 6 | p1 | 1. Misdreavus; 2. Forretress; 3. burn sleep/Sleep Talk if available | Misdreavus | top | positive, route, branch |
| 6 | p2 | 1. Double-Edge/Body Slam; 2. Curse; 3. Cloyster/Zapdos counter-pivot | Cloyster | acceptable, not top | none |
| 7 | p1 | 1. Toxic; 2. Raikou; 3. Forretress | Toxic | top | positive, route |
| 7 | p2 | 1. Spikes; 2. Toxic; 3. Surf/switch | Spikes | top | positive, route |
| 8 | p1 | 1. Toxic repeat after cure; 2. Raikou; 3. Forretress | Toxic | top move, branch miss into Nidoking | positive, route |
| 8 | p2 | 1. Toxic Misdreavus; 2. Surf; 3. switch special/Poison owner | Nidoking | miss, Poison owner not named | none |
| 9 | p1 | 1. Forretress/physical owner; 2. stay only with coverage; 3. sleeping Snorlax | Skarmory | acceptable owner class | positive, route, branch |
| 9 | p2 | 1. coverage into Misdreavus; 2. switch; 3. Earthquake on Normal | Thief | miss, Thief utility under-ranked | none |
| 10 | p1 | 1. Drill Peck/active pressure; 2. Whirlwind; 3. switch | Snorlax | miss, missed sleeping absorber route | none |
| 10 | p2 | 1. Electric/fire coverage if available; 2. Ice Beam/coverage; 3. switch | Ice Beam | acceptable coverage | positive |
| 11 | p1 | 1. Steel/flying owner; 2. Misdreavus; 3. stay/burn sleep | Forretress | acceptable owner class | positive, route, branch |
| 11 | p2 | 1. Thief item route; 2. Ice Beam; 3. switch | Earthquake | miss, hidden-info item-state error | hidden-info error |
| 12 | p1 | 1. Spikes; 2. Rapid Spin only after side check; 3. switch owner | Spikes | top | positive, route |
| 12 | p2 | 1. Earthquake pressure; 2. fire coverage if available; 3. switch | Gengar | miss, missed spinblock handoff | none |
| 13 | p1 | 1. Raikou/Snorlax handoff; 2. Misdreavus; 3. stay only with coverage | Protect | miss, scout not ranked | none |
| 13 | p2 | 1. Fire/special coverage; 2. Explosion branch; 3. switch | Ice Punch | acceptable coverage | positive, route |
| 14 | p1 | 1. handoff to sponge; 2. Protect; 3. stay only with coverage | Hidden Power | miss, failed revealed coverage conversion | none |
| 14 | p2 | 1. special attack; 2. Explosion; 3. switch | Dynamic Punch | miss, utility sequence under-ranked | none |
| 15 | p1 | 1. Hidden Power; 2. Protect/scout; 3. switch | Protect | acceptable, not top | positive |
| 15 | p2 | 1. Dynamic Punch; 2. Ice Punch; 3. Zapdos/Nidoking switch | Zapdos | acceptable, not top | positive |
| 16 | p1 | 1. Raikou; 2. sleeping Snorlax; 3. Protect/scout | Raikou | top | positive, route, branch |
| 16 | p2 | 1. Thunder; 2. Hidden Power/coverage; 3. switch | Thunder | top | positive, route |
| 17 | p1 | 1. Roar if available; 2. Rest if needed; 3. Hidden Power/Thunder | Hidden Power | acceptable, not top | positive, route |
| 17 | p2 | 1. Snorlax/Nidoking receiver; 2. preserve Zapdos; 3. Thunder | Thunder | acceptable, not top | positive, route |
| 18 | p1 | 1. Roar if available; 2. Hidden Power; 3. Rest | Hidden Power | acceptable, not top | positive, route |
| 18 | p2 | 1. Rest if available; 2. Snorlax/Nidoking switch; 3. Thunder | Nidoking | acceptable, not top | positive, route |
| 19 | p1 | 1. Skarmory/Forretress owner; 2. Hidden Power read; 3. sleeping Snorlax | Starmie | miss, missed Water/Recover owner | positive |
| 19 | p2 | 1. Earthquake; 2. Ice Beam into flyer; 3. switch | Earthquake | top | positive, route |
| 20 | p1 | 1. Surf/Psychic KO; 2. Recover; 3. Rapid Spin only after Ghost check | Surf | top | positive, route |
| 20 | p2 | hidden by pre-move KO | hidden | unscored | n/a |
| 21 | p1 | 1. Snorlax/Raikou handoff; 2. Recover; 3. Surf only on Sub read | Surf | miss, missed active Sub denial | none |
| 21 | p2 | 1. Growth on forced switch; 2. Thunderbolt; 3. Baton/switch | Substitute | miss, Sub package under-ranked | positive, route |
| 22 | p1 | 1. Snorlax handoff; 2. Surf on repeat Sub; 3. Raikou | Surf | acceptable, not top | none |
| 22 | p2 | 1. Thunderbolt; 2. Substitute; 3. Growth/Baton | Substitute | acceptable, not top | positive, route |
| 23 | p1 | 1. Surf; 2. Snorlax absorber; 3. Recover | Snorlax | acceptable, not top | positive |
| 23 | p2 | 1. Thunderbolt; 2. Substitute; 3. Growth/Baton | Thunderbolt | top | positive, route |
| 24 | p1 | 1. stay/Sleep Talk if available; 2. Raikou; 3. Starmie | Sleep Talk -> Surf | top | positive, route, branch |
| 24 | p2 | 1. Thunderbolt; 2. Substitute; 3. Growth/Baton | Substitute | acceptable, not top | positive |
| 25 | p1 | 1. Sleep Talk; 2. switch only after Sub breaks; 3. burn sleep | Sleep Talk -> Surf | top | positive, route, branch |
| 25 | p2 | 1. Thunderbolt; 2. Growth; 3. switch/preserve | Growth | acceptable, not top | positive, route |

## Main Errors

Forretress coverage into spinblock:
After Forretress revealed Hidden Power into Gengar, the next positive move was
to keep pricing that active coverage. I instead treated Forretress as a generic
support piece that should hand off. That missed the exact "revealed package"
rule: once coverage into the spinblock is public, the support piece can become
the converter.

Gengar utility sequence:
Gengar's Dynamic Punch was not random damage. It was an attempt to confuse
Forretress and stop Hidden Power, Spikes retention, or a clean handoff. I kept
ranking generic special damage and missed the support move that changed the
receiver map.

Jolteon Substitute/Growth package:
Against Starmie, I over-switched before the package was fully revealed. Surf
was the active answer to repeated Substitute until Thunderbolt appeared. After
Thunderbolt was public, the sleeping Snorlax handoff was correct, and Sleep
Talk Surf became the route move that broke Substitute.

Item-state discipline:
Nidoking revealed Thief, but I promoted Thief into an item-removal route before
Nidoking's item state was public. Later Leftovers proved the correction: Thief
can be ranked as damage or utility, but stealing cannot be the reason for the
main line unless no-item status is public or the answer explicitly marks a
high-risk read and fallback.

## Reusable Lesson

Do not let a species role override a revealed move package:

1. If a support piece reveals coverage into the spinblock or route blocker,
   re-rank active coverage before a safe handoff.
2. If a utility move such as Dynamic Punch changes the receiver map, price the
   enabled follow-up rather than treating it as flavor damage.
3. If Substitute appears on an Electric, ask whether the current active move
   breaks it. Do not switch into a free setup line until the Electric attack or
   pass target is public.
4. If Thief is revealed, separate move access from item state. Item removal is
   public only when the user's no-item condition is public or the line is
   explicitly a read.

Next proof should be a fresh transfer only after the review: revealed coverage
into spinblock, Substitute/Growth active denial, and item-state discipline.
