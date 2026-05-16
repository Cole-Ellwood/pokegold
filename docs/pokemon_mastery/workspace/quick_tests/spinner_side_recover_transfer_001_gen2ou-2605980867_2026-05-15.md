# Spinner Side/Recover Transfer 001 - gen2ou-2605980867 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/gen2ou-2605980867`

Raw log:
`https://replay.pokemonshowdown.com/gen2ou-2605980867.log`

Replay search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&page=2`

Mode: spectator public, vanilla GSC. Replay actual move is a pro-comparison
oracle, not an absolute answer key. No Team Preview: hidden teammates, moves,
items, and roles stayed in revealed / strong-prior / possible-only tiers.

Source-quality caveat: public ladder/search replay, not confirmed tournament.
Selected because it was unused locally, rated 1399 in the current search feed,
from a different player pool than the prior replay, and long enough for a
30-decision sample.

## Sources Checked

Local docs before/during study:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/active_pressure_before_status.md`
- `reviews/hazard_ownership_review_001_gen2ou-2544443857_2026-05-14.md`
- `workspace/quick_tests/statused_spinner_handoff_probe_001_2026-05-14.md`
- `workspace/quick_tests/three_check_transfer_001_gen2ou-2544443857_2026-05-14.md`
- `reviews/utility_screen_screech_review_001_2026-05-15.md`

Web/current sources used after scoring, before any further replay:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Starmie:
  `https://www.smogon.com/forums/threads/gsc-ou-starmie.3692223/`
- Smogon Forums, Forretress OU Revamp:
  `https://www.smogon.com/forums/threads/forretress-ou-revamp-done.3647111/`
- Smogon Forums, GSC OU Threat List:
  `https://www.smogon.com/forums/threads/gsc-ou-threat-list-qc-2-2-gp-2.3477110/`
- Smogon Forums, Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`

## Contamination Control

- Local `rg` found no prior `2605980867` artifact before selection.
- Candidate screening used only search-feed metadata, local prior-use checks,
  and turn count.
- The raw log was downloaded to `tmp/pokemon_mastery_replays/`.
- No future turns were inspected before freezing each turn's top-three
  candidates.
- Web and local study review happened only after the 30 side decisions were
  complete.
- No keyword screening for Starmie, Forretress, Rapid Spin, Recover, Fire
  Blast, Nidoking, or double switches.

## Score Summary

Scored turns: 1-15.

Scorable decisions: 30.

Top-match: 12 / 30.

Acceptable-match: 27 / 30.

Severe blunders: 0.

State errors: 1.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 27 / 30.

Route-converting move chosen: 24 / 30.

Branch-punish chosen: 15 / 22 applicable branch decisions.

Earliest meaningful error: turn 5, where I kept both sides in the Forretress
mirror and missed the Starmie/Zapdos double-handoff.

Interpretation:
Mixed but not progress. Severe and hidden-info gates held, and acceptable,
positive, route, and branch scores improved over the prior transfer. But
top-match stayed far below the 55% gate and a state error appeared on turn 6:
I treated Starmie as a spinner route when Spikes were on the opponent's side,
not Starmie's side. Do not claim broad progress from this run.

## Turn Table

| Turn | Side | Frozen top-three | Actual | Grade | Positive-selection tags |
| --- | --- | --- | --- | --- | --- |
| 1 | p1 | 1. Lovely Kiss if available; 2. Ice/coverage; 3. switch special owner | Snorlax | acceptable by owner class | positive, route, branch |
| 1 | p2 | 1. Hidden Power Ice; 2. switch Nidoking owner; 3. screen/utility | Hidden Power | top | positive, route |
| 2 | p1 | 1. Lovely Kiss; 2. Normal pressure; 3. Curse into switch | Curse | acceptable setup into switch | positive, route, branch |
| 2 | p2 | 1. switch Snorlax owner/normal resist; 2. Reflect; 3. attack | Tyranitar | top by class | positive, route, branch |
| 3 | p1 | 1. coverage/fallback Double-Edge; 2. switch owner; 3. Curse | Double-Edge | acceptable active pressure | positive, route |
| 3 | p2 | 1. Roar; 2. Screech; 3. normal-resist owner if no utility | Forretress | acceptable by owner class | positive, route, branch |
| 4 | p1 | 1. Double-Edge; 2. switch Explosion/support owner; 3. Curse/Rest | Forretress | acceptable preservation handoff | positive, route, branch |
| 4 | p2 | 1. Explosion; 2. Toxic; 3. Spikes | Spikes | acceptable support | positive, route |
| 5 | p1 | 1. Spikes; 2. mirror coverage; 3. Rapid Spin | Zapdos | miss; missed Starmie handoff | positive only |
| 5 | p2 | 1. mirror coverage; 2. pressure/spinblock handoff; 3. Toxic/Explosion | Starmie | miss; missed spinner handoff | positive only |
| 6 | p1 | 1. Thunder; 2. Electric coverage; 3. screen/handoff | Thunder | top | positive, route, branch |
| 6 | p2 | 1. Rapid Spin; 2. Thunder Wave; 3. switch special owner | Snorlax | acceptable by switch rank, but state error: wrong-side Spin | none |
| 7 | p1 | 1. Thunder; 2. Reflect; 3. preserve Zapdos | Thunder | top | positive, route |
| 7 | p2 | 1. Lovely Kiss if available; 2. Double-Edge; 3. switch owner | Double-Edge | acceptable active trade | positive, route |
| 8 | p1 | 1. Thunder; 2. Reflect; 3. switch to preserve Zapdos | Forretress | acceptable, but missed Rest handoff priority | none |
| 8 | p2 | 1. Rest; 2. Double-Edge trade; 3. switch/sack | Rest | top | positive, route |
| 9 | p1 | 1. Spikes; 2. Rapid Spin later; 3. pressure handoff | Spikes | top | positive, route |
| 9 | p2 | 1. Sleep Talk if asleep; 2. switch hazard owner; 3. burn sleep | Sleep Talk | top | positive, route |
| 10 | p1 | 1. Rapid Spin; 2. pressure handoff; 3. preserve Forretress | Rapid Spin | top; job completed before Forretress fainted | positive, route |
| 10 | p2 | 1. switch Starmie; 2. Sleep Talk; 3. switch pressure owner | Sleep Talk -> Fire Blast | acceptable; Sleep Talk was ranked | positive, route, branch |
| 11 | p1 | 1. Roar; 2. Screech; 3. Rock Slide | Rock Slide | acceptable; hit Starmie branch | positive, route |
| 11 | p2 | 1. Sleep Talk if still asleep; 2. Starmie/Forretress hazard owner; 3. attack if awake | Starmie | acceptable | positive, route, branch |
| 12 | p1 | 1. Dark/Pursuit if available; 2. Zapdos handoff; 3. Rock Slide | Rock Slide | acceptable fallback | positive, route |
| 12 | p2 | 1. Rapid Spin; 2. Surf; 3. Recover/switch | Rapid Spin | top | positive, route |
| 13 | p1 | 1. Rock Slide; 2. Pursuit if fleeing; 3. Zapdos handoff | Rock Slide | top | positive, route |
| 13 | p2 | 1. Recover; 2. Surf; 3. switch owner | Recover | top | positive, route |
| 14 | p1 | 1. Zapdos handoff; 2. Rock Slide; 3. Dark/Pursuit if available | Snorlax | acceptable by pressure-handoff class | positive, route, branch |
| 14 | p2 | 1. Surf; 2. Recover; 3. switch owner | Recover | top | positive, route |
| 15 | p1 | 1. Lovely Kiss if available; 2. Curse; 3. Double-Edge | Nidoking | miss; missed double-switch punish into Forretress | none |
| 15 | p2 | 1. Thunder Wave if available; 2. Surf/Psychic; 3. switch Forretress/Tyranitar owner | Forretress | acceptable by switch class | positive, branch |

## Main Errors

Turn 5 double-handoff:
I correctly knew p1 wanted hazard control and p2 wanted spinner access, but I
kept both sides in the Forretress mirror. The actual line showed both players
converting the next board immediately: p2 moved Starmie toward Spin/Recover
control, and p1 met it with Zapdos before a Spin cycle began.

Turn 6 side-ownership error:
I recommended Rapid Spin for p2 Starmie even though Spikes were on p1's side
only. That is a pure state error. Before any Spin recommendation, name whose
side has Spikes and whether this spinner can clear them.

Turns 12-14 Starmie preservation:
After Starmie cleared Spikes and survived Rock Slide, Recover was the route.
Repeating Rock Slide stopped being a conversion once Starmie proved it could
Recover through the sequence. P1 needed a pressure handoff, trap/status, or a
move that actually removed Starmie.

Turn 15 double-switch punish:
Once Snorlax faced full Starmie with no hazards up, I over-focused on the
visible Starmie position. The actual p1 Nidoking double punished the likely
Forretress return and put mixed pressure on the support piece.

## Reusable Lesson

Before choosing Spin, say the side name out loud:

1. Are Spikes on my side, their side, both, or neither?
2. Can this active spinner remove hazards that hurt its own team this turn?
3. If Spin succeeds, can the opposing setter reset immediately?
4. If the spinner survives and has Recover, what pressure piece stops the
   Recover loop?
5. If the spinner/support owner is likely to leave, what double-switch or
   coverage punishes the receiver?

Next proof should be another fresh unseen transfer, not a constructed probe,
with the side-ownership Spin check and post-Spin Recover handoff active.
