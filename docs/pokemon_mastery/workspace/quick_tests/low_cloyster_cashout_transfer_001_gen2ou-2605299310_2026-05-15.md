# Low Cloyster Cash-Out Transfer 001 - gen2ou-2605299310 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/gen2ou-2605299310`

Raw log:
`https://replay.pokemonshowdown.com/gen2ou-2605299310.log`

Replay search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&page=2`

Mode: spectator public, vanilla GSC. Replay actual move is a pro-comparison
oracle, not an absolute answer key. No Team Preview: hidden teammates, moves,
items, and roles stayed in revealed / strong-prior / possible-only tiers.

Source-quality caveat: public ladder/search replay, not confirmed tournament.
Selected because it was unused locally, rated 1362 in the current search feed,
from a different player pair than the prior replay, and long enough for a
30-decision sample.

## Sources Checked

Local docs before/during study:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/hidden_role_voluntary_entry.md`
- `reviews/spinner_side_recover_review_001_2026-05-15.md`
- `workspace/quick_tests/spinner_side_recover_transfer_001_gen2ou-2605980867_2026-05-15.md`

Web/current sources used after scoring, before any further replay:

- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, Cloyster OU Revamp:
  `https://www.smogon.com/forums/threads/cloyster-ou-revamp-qc-2-2-gp-2-2.3652352/`

## Contamination Control

- Local `rg` found no prior `2605299310` artifact before selection.
- Candidate screening used only search-feed metadata, local prior-use checks,
  and turn count.
- The raw log was downloaded to `tmp/pokemon_mastery_replays/`.
- No future turns were inspected before freezing each turn's top-three
  candidates.
- Web and local study review happened only after the 31 side decisions were
  complete.
- No keyword screening for Vaporeon, Ice Beam, Cloyster, Explosion, Charizard,
  Nidoking, Skarmory, or Pursuit.

## Score Summary

Scored turns: 1-17.

Scorable decisions: 31.

Unscored: turn 7 p1, turn 10 p2, and turn 16 p2 because the selected action was
hidden by pre-move KO or forced faint resolution.

Top-match: 19 / 31.

Acceptable-match: 29 / 31.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 29 / 31.

Route-converting move chosen: 26 / 31.

Branch-punish chosen: 17 / 23 applicable branch decisions.

Earliest meaningful error: turn 7 p2, where I did not rank Vaporeon's hidden
Ice Beam coverage into Exeggutor.

Interpretation:
Limited positive transfer, not mastery. This clears the provisional top,
acceptable, severe, state, hidden-info, and mechanics gates and repairs the
previous wrong-side Spin error. It is still one public ladder replay, not a
trend, and the main misses were positive-selection misses around hidden
coverage and low-Cloyster cash-out timing.

## Turn Table

| Turn | Side | Frozen top-three | Actual | Grade | Positive-selection tags |
| --- | --- | --- | --- | --- | --- |
| 1 | p1 | 1. Sleep Powder; 2. status/coverage; 3. switch special owner | Tyranitar | acceptable status-absorber/trapper switch | positive, branch |
| 1 | p2 | 1. Fire/Ice coverage; 2. Thunder Wave; 3. switch sleep owner | Thunder Wave | acceptable, not top | positive, route |
| 2 | p1 | 1. Pursuit; 2. Crunch/Dark pressure; 3. Rock Slide | Pursuit, full paralysis | top | positive, route, branch |
| 2 | p2 | 1. switch Tyranitar owner; 2. DynamicPunch if available; 3. chip | Vaporeon | top by owner class | positive, route, branch |
| 3 | p1 | 1. switch Vaporeon owner, Raikou/Exeggutor class; 2. Snorlax; 3. attack | Raikou | top by class | positive, route, branch |
| 3 | p2 | 1. Surf; 2. Growth into switch; 3. coverage into Exeggutor | Growth | acceptable setup into switch | positive, route, branch |
| 4 | p1 | 1. Thunder; 2. Roar if available; 3. Rest/switch only if forced | Thunder | top | positive, route |
| 4 | p2 | 1. Surf; 2. switch owner; 3. Growth only if safe | Surf | top | positive, route |
| 5 | p1 | 1. Thunder; 2. Roar if available; 3. Rest/switch | Thunder | top | positive, route |
| 5 | p2 | 1. Surf; 2. Rest later; 3. switch if Thunder risk flips it | Surf | top | positive, route |
| 6 | p1 | 1. switch Water/Growth owner; 2. Thunder desperation; 3. Rest only if safe | Exeggutor | top | positive, route, branch |
| 6 | p2 | 1. Surf; 2. coverage if revealed; 3. switch support owner | Surf | top | positive, route |
| 7 | p1 | 1. Sleep Powder; 2. Grass/cash pressure; 3. Stun Spore into switch | pre-move KO | unscored | n/a |
| 7 | p2 | 1. switch owner or Surf; 2. Surf; 3. Growth/Rest | Ice Beam | miss; hidden coverage not ranked | none |
| 8 | p1 | 1. Lovely Kiss if available; 2. Body Slam/Double-Edge; 3. Curse | Body Slam | acceptable fallback | positive, route |
| 8 | p2 | 1. Surf; 2. Growth; 3. switch normal answer | Surf | top | positive, route |
| 9 | p1 | 1. Body Slam; 2. Rest next; 3. switch only if forced | Body Slam | top | positive, route |
| 9 | p2 | 1. Surf; 2. Rest if needed; 3. Growth only if forced switch | Surf | top | positive, route |
| 10 | p1 | 1. Body Slam before slow Rest; 2. Double-Edge if available; 3. preserve | Body Slam | top | positive, route |
| 10 | p2 | 1. switch normal resist; 2. Rest if speed permits; 3. Surf sack damage | pre-move KO | unscored | n/a |
| 11 | p1 | 1. Body Slam; 2. Tyranitar status-absorber/trapper; 3. Rest | Tyranitar | acceptable branch | positive, branch |
| 11 | p2 | 1. Thunder Wave; 2. Psychic/coverage; 3. switch normal resist | Thunder Wave | top | positive, route |
| 12 | p1 | 1. Pursuit; 2. Crunch/Dark pressure; 3. Rock Slide | Pursuit | top | positive, route, branch |
| 12 | p2 | 1. switch Tyranitar owner; 2. DynamicPunch if available; 3. chip | Skarmory | top by owner class | positive, route, branch |
| 13 | p1 | 1. Fire Blast if available; 2. Rock Slide; 3. Raikou handoff | Raikou | acceptable into Skarmory stay, punished by counter-handoff | positive only |
| 13 | p2 | 1. Toxic/phaze if staying; 2. switch Tyranitar owner; 3. Drill Peck/Curse | Tyranitar | acceptable counter-handoff | positive, route, branch |
| 14 | p1 | 1. switch Tyranitar/Nidoking owner; 2. Thunder desperation; 3. Rest if available | Cloyster | top by owner class | positive, route, branch |
| 14 | p2 | 1. Pursuit if available; 2. Rock Slide; 3. Earthquake/coverage | Earthquake | acceptable coverage into owner | positive, route |
| 15 | p1 | 1. Spikes; 2. Surf/Ice Beam chip; 3. Explosion branch | Ice Beam | miss; over-ranked field job | positive only |
| 15 | p2 | 1. Rock Slide/coverage; 2. switch Explosion absorber; 3. phaze/status | Rock Slide | top | positive, route |
| 16 | p1 | 1. Spikes before death; 2. Ice Beam; 3. Explosion if exact converter | Explosion | acceptable branch, not top | positive, route, branch |
| 16 | p2 | 1. Rock Slide; 2. switch Explosion absorber; 3. Earthquake | pre-move KO | unscored | n/a |
| 17 | p1 | 1. switch ground-immune/Nidoking owner; 2. Snorlax owner; 3. attack only as read | Charizard | top by owner class | positive, route, branch |
| 17 | p2 | 1. Lovely Kiss into likely owner; 2. Earthquake active punish; 3. coverage | Earthquake | acceptable active fallback, branch miss | positive only |

## Main Errors

Turn 7 hidden coverage:
I brought Exeggutor in correctly on Surf, but I did not rank Vaporeon's hidden
Ice Beam before choosing the follow-up. It was still possible-only before
reveal, so this is not a hidden-info error. It is a route-risk miss: once the
Water answer is in, re-check the coverage branch before treating sleep as free.

Turns 15-16 low Cloyster:
I over-ranked Spikes as Cloyster's unique job after Cloyster had already taken
Rock Slide damage. The actual sequence used Ice Beam chip and Explosion to
remove Tyranitar. Smogon sources support this boundary: Cloyster is not only a
Spiker; its Explosion and coverage are part of its offensive threat.

Turn 13 counter-handoff:
I found Raikou as the Skarmory punish but under-priced p2's Tyranitar
counter-handoff. The lesson is not "never double"; it is to name the opponent's
second owner before spending a low route piece like Raikou.

Turn 17 active fallback:
I correctly ranked Lovely Kiss into the likely owner, while the actual
Earthquake was blanked by Charizard. This is a useful reminder that replay
actuals are a weak oracle; branch-obedient advice can be better than the
observed move.

## Reusable Lesson

Low support pieces need a two-question cash-out check:

1. Is the support job still deliverable and convertible?
2. If not, is the active target the blocker whose removal opens the route?

For Cloyster specifically, Spikes is usually the first job, but Surf/Ice Beam
chip plus Explosion can be the correct positive selection when Cloyster is
low, the target is exact, and the post-trade owner is named.

Next proof should repeat this in a fresh unseen replay: hazard job versus
low-support cash-out, with hidden coverage kept as possible-only until reveal.
