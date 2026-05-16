# SubSpin Named-Absorber Transfer 001 - smogtours-gen2ou-935833 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935833`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935833.log`

Replay search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou`

Web/current sources checked:

- Pokemon Showdown public replay search API for current Gen 2 OU replays.
- Pokemon Showdown raw replay log for `smogtours-gen2ou-935833`.
- Smogon, Playing with Spikes in GSC: `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, GSC OU Threatlist: `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon, Gengar Through the Ages: `https://www.smogon.com/articles/gengar-through-ages`
- Smogon, GSC OU Cloyster spotlight: `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon, GSC OU Gengar forum analysis draft: `https://www.smogon.com/forums/threads/gengar-wip.3703761/`

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/active_pressure_before_status.md`
- `docs/pokemon_mastery/policy_cards/support_handoff_after_job.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/workspace/quick_tests/subspin_named_absorber_cashout_probe_001_2026-05-15.md`

Mode: spectator public. No Team Preview. No team paste, replay UI, or future
log turns were used before freezing answers. Hidden teammates and unrevealed
moves were treated as revealed, strong-prior, or possible-only.

Contamination control:

- Local `rg` found no prior `935833` use before selection.
- Replay was selected from the current Showdown Gen 2 OU search API without
  keyword screening for Gengar, Hypnosis, Cloyster, Explosion, Steelix,
  Vaporeon, Substitute, Rapid Spin, or named-absorber trades.
- Same-pair caveat: the same player pair appears in `smogtours-gen2ou-935835`,
  but this replay ID was unseen and no future log text was opened before
  answer freezes.
- Scoring covers turns 1-17: 31 scored side decisions. Sleeping Golem no-action
  turns and forced post-faint switches were excluded.

Selected action:
Fresh transfer after the SubSpin/named-absorber regression probe. The sample
naturally tested Exeggutor's early Explosion into Zapdos, Cloyster support
sequencing, Gengar sleep/coverage branching, low support-piece spending, and
Steelix setup versus phaze.

## Score

- Scored decisions: 31
- Top match: 19/31
- Acceptable match: 26/31
- Severe blunders: 0
- State errors: 0
- Hidden-info errors: 0
- Mechanics errors: 0
- Positive-selection: 29/31
- Route-converting move chosen: 23/31 applicable
- Branch-punish chosen: 15/22 applicable
- Earliest meaningful error: turn 6

Interpretation:
Limited positive fresh transfer, not mastery. The severe/hidden/state/mechanics
gate held, and top-match, acceptable-match, route-conversion, and branch
obedience all improved versus `item_package_followup_transfer_002`. The result
is still only one replay with a same-pair caveat, and the misses are not
solved: I still under-ranked Hypnosis into a leaving poisoned target, a low
Cloyster defensive sack, and Steelix Curse as setup into the forced Water
answer.

## Turn Notes

| Turn | Side | Frozen ranked candidates | Actual | Grade | Positive-selection tags |
| --- | --- | --- | --- | --- | --- |
| 1 | p1 | 1. Hidden Power Ice/coverage; 2. switch sleep absorber; 3. Thunder | Hidden Power | top-match | positive, route |
| 1 | p2 | 1. Sleep Powder; 2. Stun Spore/Thief into absorber; 3. switch Electric answer | Sleep Powder miss | top-match | positive, route |
| 2 | p1 | 1. Hidden Power again; 2. switch sleep absorber; 3. Thunder Wave if available | Hidden Power | top-match | positive, route |
| 2 | p2 | 1. Sleep Powder; 2. switch answer; 3. Explosion as named route trade | Explosion | acceptable; Explosion under-ranked | positive only |
| 3 | p1 | 1. Spikes; 2. Toxic; 3. Surf/handoff | Spikes | top-match | positive, route |
| 3 | p2 | 1. Spikes; 2. Toxic; 3. Surf/handoff | Spikes | top-match | positive, route |
| 4 | p1 | 1. Toxic; 2. Surf; 3. pressure handoff | Toxic miss | top-match by move | positive, route |
| 4 | p2 | 1. Toxic; 2. Surf; 3. pressure handoff | Toxic | top-match | positive, route |
| 5 | p1 | 1. Toxic again; 2. Surf; 3. preserve/handoff | Toxic | top-match | positive, route |
| 5 | p2 | 1. Surf; 2. pressure handoff; 3. Explosion only after naming converter | Surf | top-match | positive, route |
| 6 | p1 | 1. pressure handoff; 2. Surf; 3. Explosion as high-risk | Surf | miss; over-preserved before taking damage | none |
| 6 | p2 | 1. pressure handoff; 2. Surf; 3. Explosion as high-risk | Surf | acceptable | positive only |
| 7 | p1 | 1. Explosion; 2. Surf; 3. switch/sack if speed or route demands | Gengar | miss; failed to use low Cloyster as defensive spend | positive only |
| 7 | p2 | 1. Surf; 2. switch if Explosion read; 3. no Explosion into Ghost branch | Surf | top-match | positive, branch |
| 8 | p1 | 1. Thunderbolt/coverage; 2. Hypnosis into switch; 3. Explosion if route opens | Hypnosis | miss; under-ranked status into the switch | positive only |
| 8 | p2 | 1. switch Gengar answer/sleep absorber; 2. Surf; 3. preserve Cloyster | Golem | acceptable by switch class | positive, branch |
| 9 | p1 | 1. Ice Punch/coverage; 2. switch if wake branch threatens; 3. Explosion only if exact | Ice Punch | top-match | positive, route |
| 10 | p1 | 1. Ice Punch KO; 2. switch if wake branch matters; 3. Explosion only if exact | Ice Punch | top-match | positive, route |
| 10 | p2 | 1. switch Gengar answer; 2. sack/burn sleep; 3. Sleep Talk if revealed | Snorlax | top by class | positive, branch |
| 11 | p1 | 1. Explosion high-risk; 2. Steelix/physical owner; 3. Thunderbolt chip | Steelix | acceptable; preserved Gengar instead of trading | positive only |
| 11 | p2 | 1. Earthquake if available; 2. switch Explosion resist/absorber; 3. Lovely Kiss if available | Golem | acceptable by absorber class | positive, branch |
| 12 | p1 | 1. Earthquake; 2. Roar if switch expected; 3. Toxic/status | Earthquake | top-match | positive, route |
| 13 | p1 | 1. Gengar to cover Explosion/Surf; 2. Earthquake; 3. Roar | Cloyster sack | miss; wrong defensive owner | none |
| 13 | p2 | 1. Surf; 2. Explosion if no Ghost branch; 3. switch/preserve | Surf | top-match | positive, branch |
| 14 | p1 | 1. Thunderbolt; 2. Explosion if needed; 3. switch preserve | Thunderbolt | top-match | positive, route |
| 15 | p1 | 1. switch Steelix; 2. Explosion high-risk; 3. Thunderbolt chip | Steelix | top-match | positive, route, branch |
| 15 | p2 | 1. Earthquake; 2. switch Explosion absorber; 3. Lovely Kiss if available | Earthquake | top-match | positive, route |
| 16 | p1 | 1. Roar; 2. Earthquake; 3. Curse/setup | Curse | miss; setup into forced Water answer was better | positive only |
| 16 | p2 | 1. Earthquake; 2. switch Water/special answer; 3. Curse/setup | Vaporeon | acceptable by switch class | positive, branch |
| 17 | p1 | 1. switch special answer; 2. Explosion if Vaporeon is exact blocker; 3. Roar | Snorlax | acceptable by switch class | positive, route |
| 17 | p2 | 1. Surf; 2. Growth if switch is free; 3. Rest | Surf | top-match | positive, route |

## Main Errors

Turn 8:
I treated Gengar's Thunderbolt as the clean route into poisoned Cloyster. The
actual Hypnosis punished the named switch instead. The correction is not
"click status with Gengar"; it is to ask whether the active target is leaving
and whether the incoming target can still be slept.

Turn 13:
I wanted to preserve Steelix with Gengar, but the actual line spent a nearly
dead, poisoned Cloyster as the lower-value defensive owner into Surf. That kept
Gengar healthier for the next forced Cloyster turn and preserved Steelix as
the Snorlax owner.

Turn 16:
I over-defaulted to phaze after getting Steelix in front of Snorlax. The actual
Curse used the forced Water answer turn as setup. This is the setup side of
branch action: phazing is not automatically conversion if the opponent's
counter-pivot is already forced and setup improves the next board.

## Post-Run Study

Because this run was imperfect, no further replay was started. The follow-up
study is recorded in:

`docs/pokemon_mastery/reviews/hypnosis_sack_setup_review_001_2026-05-15.md`

Resulting updates:

- `policy_cards/branch_action_after_naming.md` gained a status-into-switch
  reminder.
- `policy_cards/cashout_boundary.md` gained a defensive-sack-owner reminder.
- `active_context.md` and `measurement_progress_ledger.csv` were updated with
  this limited positive transfer.

## Reusable Lesson

When a poisoned or doomed active support piece is likely to leave, the positive
move may target the next board rather than the visible target. That can mean
Hypnosis into the switch, a low sack into the expected attack, or setup on the
turn the counter-pivot enters. The move is only positive if the branch and the
next owner are named before choosing.
