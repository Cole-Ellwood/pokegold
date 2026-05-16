# Status Setup/Handoff Transfer 001 - smogtours-gen2ou-934420 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-934420`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-934420.log`

Replay search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&page=2`

Players: Estuardo19 vs Zokuru.

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
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/support_handoff_after_job.md`

Web/current sources used after scoring, before any further replay:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums, GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon Forums, GSC Good Cores:
  `https://www.smogon.com/forums/threads/gsc-good-cores.3536015/`
- Smogon Forums, Dragonite OU Revamp:
  `https://www.smogon.com/forums/threads/dragonite-ou-revamp-done.3647144/`
- Pikalytics current GSC Smeargle usage snapshot:
  `https://pikalytics.com/pokedex/gsc/Smeargle`

## Contamination Control

- Local `rg` found no prior `smogtours-gen2ou-934420` use before selection.
- Candidate screening used only current Showdown search metadata, local
  prior-use checks, and raw-log turn counts.
- I downloaded three unused candidates only to count turns: `935550`, `934420`,
  and `933839`. No move keywords or later turns were inspected during
  selection.
- The selected raw log was stored at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-934420.log`.
- No future turn was inspected before freezing each turn's top-three
  candidates.
- Web and broad local study happened only after the 49 scored side decisions
  were complete.

## Score Summary

Scored turns: 1-25.

Scorable decisions: 49.

Unscored: turn 7 p1 because full paralysis hid the selected move.

Top-match: 23 / 49.

Acceptable-match: 40 / 49.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0. Conditional own-move recommendations such as Toxic,
Haze, or coverage were marked as "if available" with a fallback; possible-only
hidden moves did not anchor a recommendation as fact.

Mechanics errors: 0.

Positive-selection: 38 / 49.

Route-converting move chosen: 34 / 49.

Branch-punish chosen: 21 / 43 applicable branch decisions.

Earliest meaningful error: turn 1 p2, where I over-scripted Smeargle as Spore
and did not put Spikes first despite the lead support route.

Interpretation:
Mixed but not progress. Top, acceptable, and route conversion improved over the
prior fresh transfer, and the severe/hidden/state/mechanics gates held. This is
not real progress because positive-selection fell and branch-punish obedience
was poor. The repeated misses were about choosing the branch move that makes
the route better, not about avoiding obvious losses.

## Turn Table

| Turn | Side | Frozen top-three | Actual | Grade | Positive-selection tags |
| --- | --- | --- | --- | --- | --- |
| 1 | p1 | 1. sleep/status absorber; 2. attack Smeargle; 3. Spikes if no absorber | Raikou | top by absorber class | positive, route, branch |
| 1 | p2 | 1. Spore; 2. Spikes; 3. Baton Pass/setup | Spikes | acceptable, not top | positive, route |
| 2 | p1 | 1. Thunder; 2. Hidden Power into Ground; 3. phaze/switch | Hidden Power | acceptable, missed branch top | none |
| 2 | p2 | 1. Spore; 2. Ground owner; 3. preserve Smeargle | Marowak | acceptable, not top | positive |
| 3 | p1 | 1. Cloyster handoff; 2. repeat Hidden Power; 3. Raikou preserve | Cloyster | top | positive, route, branch |
| 3 | p2 | 1. Earthquake; 2. Swords Dance; 3. stay pressure | Smeargle | miss, did not expect support reset | none |
| 4 | p1 | 1. Raikou/status absorber; 2. Surf; 3. Spikes | Surf | miss, overread sleep | none |
| 4 | p2 | 1. Spore; 2. Thunder Wave; 3. switch | Thunder Wave | acceptable status route | positive, route, branch |
| 5 | p1 | 1. Surf; 2. Spikes; 3. switch | Spikes | acceptable field job, not top | positive |
| 5 | p2 | 1. Starmie/water owner; 2. status; 3. preserve | Starmie | top by class | positive, route, branch |
| 6 | p1 | 1. Toxic if available; 2. Raikou pressure; 3. Surf | Toxic | top | positive, route, branch |
| 6 | p2 | 1. Rapid Spin; 2. Surf; 3. Recover/switch | Rapid Spin | top | positive, route, branch |
| 7 | p1 | hidden by full paralysis | full paralysis | unscored | n/a |
| 7 | p2 | 1. switch/pressure; 2. Surf; 3. Recover | Surf | acceptable | positive, route |
| 8 | p1 | 1. Spikes; 2. Raikou pressure; 3. Surf | Spikes | top | positive, route, branch |
| 8 | p2 | 1. Surf; 2. Rapid Spin; 3. Recover | Surf | top | positive, route |
| 9 | p1 | 1. Spikes reset; 2. Raikou pressure; 3. Surf | Raikou | acceptable pressure handoff | positive, route, branch |
| 9 | p2 | 1. Rapid Spin; 2. Surf; 3. Recover | Rapid Spin | top | positive, route, branch |
| 10 | p1 | 1. Hidden Power into receiver; 2. Electric attack; 3. handoff | Hidden Power | top | positive, route, branch |
| 10 | p2 | 1. Ground owner; 2. Surf stay; 3. recover | Steelix | top by class | positive, route, branch |
| 11 | p1 | 1. Cloyster/anti-Ground owner; 2. Hidden Power; 3. Rest/handoff | Dragonite | acceptable owner class | positive, route, branch |
| 11 | p2 | 1. Earthquake; 2. Roar; 3. Explosion read | Zapdos | miss, missed counter-pivot | none |
| 12 | p1 | 1. Raikou; 2. Ice Beam if available; 3. Thunder Wave | Thunder Wave | acceptable but missed utility top | positive |
| 12 | p2 | 1. Hidden Power; 2. Thunder; 3. switch | Hidden Power | top | positive, route |
| 13 | p1 | 1. coverage/attack if available; 2. Raikou; 3. preserve | Raikou | acceptable fallback | positive |
| 13 | p2 | 1. Hidden Power; 2. Steelix; 3. stay | Snorlax | miss, missed special sponge | none |
| 14 | p1 | 1. Steelix/Normal resist; 2. Cloyster; 3. Thunder | Steelix | top by class | positive, route, branch |
| 14 | p2 | 1. Curse; 2. Body Slam; 3. Earthquake | Curse | top | positive, route |
| 15 | p1 | 1. Roar; 2. Explosion; 3. Earthquake/Curse | Curse | acceptable setup, not top | positive, route, branch |
| 15 | p2 | 1. Earthquake; 2. switch absorber; 3. Curse | Earthquake | top | positive, route, branch |
| 16 | p1 | 1. Roar; 2. Explosion; 3. Earthquake | Roar | top | positive, route, branch |
| 16 | p2 | 1. Earthquake; 2. switch absorber; 3. Curse | Earthquake | top | positive, route, branch |
| 17 | p1 | 1. Raikou preserve; 2. Explosion; 3. Roar | Raikou | top | positive, route, branch |
| 17 | p2 | 1. Surf; 2. switch; 3. Recover | Surf | top | positive, route |
| 18 | p1 | 1. Hidden Power into Ground; 2. Electric attack; 3. Rest/switch | Hidden Power | top move, wrong receiver read | none |
| 18 | p2 | 1. Ground owner; 2. Surf; 3. Recover | Snorlax | miss, missed sponge branch | none |
| 19 | p1 | 1. Steelix; 2. Cloyster; 3. Thunder | Dragonite | acceptable owner but wrong route | positive |
| 19 | p2 | 1. Earthquake; 2. Curse; 3. switch | Curse | acceptable, not top | positive, route |
| 20 | p1 | 1. Haze if available; 2. Steelix; 3. Thunder Wave | Thunder Wave | miss, failed status-sacrifice receiver plan | none |
| 20 | p2 | 1. Body Slam/normal hit; 2. Curse; 3. switch | Body Slam | top | positive, route |
| 21 | p1 | 1. Cross Chop; 2. Curse if switch; 3. coverage | Curse | miss, missed setup into receiver | none |
| 21 | p2 | 1. Starmie/fighting owner; 2. Zapdos; 3. stay | Starmie | top by class | positive, route, branch |
| 22 | p1 | 1. Machamp coverage; 2. Raikou; 3. stay attack | Snorlax | miss, missed status-tolerant handoff | none |
| 22 | p2 | 1. Surf/Psychic; 2. Recover; 3. switch | Thunder Wave | miss, missed support status | none |
| 23 | p1 | 1. Double-Edge/Body Slam; 2. Curse on switch; 3. Rest | Curse | acceptable, not top | positive, route |
| 23 | p2 | 1. Recover; 2. Steelix/Snorlax owner; 3. Surf | Steelix | acceptable, not top | positive, route |
| 24 | p1 | 1. Earthquake; 2. Machamp; 3. Curse/Rest | Earthquake | top | positive, route, branch |
| 24 | p2 | 1. Roar if available; 2. Explosion; 3. Earthquake/Curse | Curse | acceptable, not top | positive, route |
| 25 | p1 | 1. Earthquake; 2. switch lower-value absorber; 3. Curse/Rest | Earthquake | top | positive, route, branch |
| 25 | p2 | 1. Roar if available; 2. Earthquake; 3. Explosion | Earthquake | acceptable, not top | positive, route |

## Main Errors

Smeargle lead order:
I treated Smeargle as sleep-first. The replay used Spikes first and Thunder
Wave second. Smeargle can threaten Spore, but once it is revealed as a support
lead, active damage and field-ordering must be priced before reflexively
switching to a sleep absorber.

Special sponge and status-tolerant handoffs:
I repeatedly named Ground receivers for Raikou but missed Snorlax as the
special sponge on turns 13 and 18. I also missed p1's Snorlax into Starmie's
Thunder Wave on turn 22. The correction is to separate "Electric immunity" from
"special/status absorber." Snorlax can be the right receiver even when Ground
types are public.

Setup into expected receiver:
Turn 21 was the cleanest route miss. Machamp threatened paralyzed Snorlax, the
opponent's Starmie receiver was obvious, and the replay used Curse rather than
attacking into the leaving target. This was the branch-action card in plain
form: if the receiver is coming and setup makes the receiver worse, setup is
the positive move.

Support status sacrifice:
Dragonite's turn-20 Thunder Wave looked passive if judged only as "Dragonite
dies." It made more sense with the next board: paralyzed Snorlax into Machamp.
The lesson is not to assume hidden Haze from voluntary entry; it is to ask what
revealed status does for the next converter before switching or using generic
damage.

Steelix setup versus immediate phaze:
I over-ranked Roar as the automatic Steelix answer. Source review supports
Curse + Roar as a package: Steelix may need to boost first, then phaze or
attack. The positive question is whether the setup changes the later Roar or
Earthquake route, not whether phazing is available at all.

## Reusable Lesson

Before choosing a "safe" owner or status line, name the route receiver and ask
which move makes that receiver better:

1. If a frail support lead reveals Spikes or Thunder Wave, re-rank active
   pressure and field order before assuming sleep.
2. If a special attacker faces Starmie, Zapdos, or Raikou branches, include
   Snorlax as a status-tolerant sponge, not just Ground-type immunity owners.
3. If a physical converter forces a receiver, setup can be the branch-punish.
4. If a low support piece can paralyze or screen the exact blocker for the next
   converter, the status sacrifice can be positive only when that converter is
   named.

Next proof should be a fresh transfer only after the review: support-lead
ordering, Snorlax/status-tolerant receiver handoffs, and setup into named
Starmie/Zapdos/Snorlax receivers.
