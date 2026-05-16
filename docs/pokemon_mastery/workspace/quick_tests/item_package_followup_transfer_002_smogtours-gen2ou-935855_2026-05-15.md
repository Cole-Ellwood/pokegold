# Item Package Followup Transfer 002 - smogtours-gen2ou-935855 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935855`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935855.log`

Replay search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou`

Web/current sources checked after scoring:

- Pokemon Showdown public replay search API for current Gen 2 OU replays.
- Pokemon Showdown raw replay log for `smogtours-gen2ou-935855`.
- Smogon, Playing with Spikes in GSC: `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, GSC OU discussion on Substitute Starmie: `https://www.smogon.com/forums/threads/gsc-ou-discussion-thread.3688141/post-8932823`
- Smogon, Explosion in GSC: `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, GSC OU Threatlist: `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon, GSC OU Cloyster spotlight: `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon, GSC OU Snorlax spotlight: `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md`
- `docs/pokemon_mastery/policy_cards/support_handoff_after_job.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/reviews/item_removal_revealed_package_review_001_2026-05-15.md`
- `docs/pokemon_mastery/reviews/hazard_ownership_review_001_gen2ou-2544443857_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_077_spinner_control_transfer_smogtours-gen2ou-925730_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/statused_spinner_handoff_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/reviews/2026-05-13_smogtours-gen2ou-917190.md`

Mode: spectator public. No Team Preview. No team paste, replay UI, or future
log turns were used before freezing answers. Hidden teammates and unrevealed
moves were treated as revealed, strong-prior, or possible-only.

Contamination control:

- Local `rg` found no prior `935855` use before selection.
- Replay was selected from the current Showdown Gen 2 OU search API without
  keyword screening for Starmie, Substitute, Rapid Spin, Exeggutor, Explosion,
  Cloyster, Toxic, or Zapdos.
- Same-pair caveat: this replay had the same players as
  `status_receiver_positive_transfer_002_smogtours-gen2ou-935859`, so the
  result is still fresh by replay ID but not independent by player pool.
- Used only the local turn-pause helper before each reveal. After the run,
  the helper was fixed because it had hidden `-start`, `-activate`,
  Substitute, and confusion state that mattered for this exact packet.
- Scoring covers turns 1-16: 31 scored side decisions. Turn 14 p1 was excluded
  from top/acceptable scoring because confusion prevented the selected move
  from appearing in the log, but the missed confusion state is still counted.

Selected action:
Fresh transfer after `one_time_trade_setup_transfer_001`, focused on positive
move selection after item/package reveals. The sample naturally tested
Forretress support sequencing, RestTalk Snorlax handoff, Starmie
Substitute/Rapid Spin protection, and Exeggutor Explosion into an active
Zapdos absorber.

## Score

- Scored decisions: 31
- Top match: 12/31
- Acceptable match: 23/31
- Severe blunders: 0
- State errors: 1
- Hidden-info errors: 0
- Mechanics errors: 0
- Positive-selection: 26/31
- Route-converting move chosen: 19/31 applicable
- Branch-punish chosen: 11/22 applicable
- Earliest meaningful error: turn 2

Interpretation:
Not progress. Acceptable-match recovered from the previous packet, severe and
hidden-info errors stayed at zero, and many answers were active rather than
purely safe. The score still fails the active gate: top-match stayed far below
55%, a state/tooling error appeared, and the largest misses were route
conversion misses around fast `Substitute` + `Rapid Spin` Starmie and
Exeggutor's named-absorber Explosion into Zapdos.

## Turn Notes

| Turn | Side | Frozen ranked candidates | Actual | Grade | Positive-selection tags |
| --- | --- | --- | --- | --- | --- |
| 1 | p1 | 1. Double-Edge/Body Slam pressure; 2. Curse; 3. switch to known Electric/Rock answer | Curse | acceptable; setup was ranked but not top | positive only |
| 1 | p2 | 1. Thunder/Thunderbolt; 2. Thunder Wave; 3. switch to Normal answer such as Forretress | Forretress | acceptable by switch class | positive only |
| 2 | p1 | 1. Double-Edge active damage; 2. coverage if known; 3. handoff if Explosion/Toxic priced | Curse | miss; under-ranked second Curse before forcing the support map | none |
| 2 | p2 | 1. Spikes; 2. Toxic; 3. Explosion only after naming converter | Toxic | acceptable; correct support, wrong order | positive, route |
| 3 | p1 | 1. Double-Edge; 2. Rest if poison clock dominates; 3. switch owner | Double-Edge | top-match | positive, route |
| 3 | p2 | 1. Spikes; 2. preserve; 3. Explosion only if Snorlax becomes immediate converter | Spikes | top-match | positive, route |
| 4 | p1 | 1. Double-Edge; 2. Rest; 3. switch/preserve | Double-Edge | top-match | positive, route |
| 4 | p2 | 1. switch normal resist/phazer; 2. Explosion if no phazer; 3. preserve Forretress | Steelix | acceptable by class | positive, branch |
| 5 | p1 | 1. Rest; 2. switch if phaze is forced; 3. more damage only if poison clock safe | Rest | top-match | positive, route |
| 5 | p2 | 1. Roar; 2. Earthquake/Rock pressure; 3. switch | Roar | top-match | positive, route, branch |
| 6 | p1 | 1. switch to Steelix punisher; 2. Hidden Power coverage if known; 3. Thunder | Thunder | miss; over-switched away from Zapdos pressure | positive but not route |
| 6 | p2 | 1. Roar to punish switch; 2. Rock Slide if available; 3. Toxic/cash-out branch | Snorlax | miss; missed Snorlax as Electric receiver | positive but not route |
| 7 | p1 | 1. Thunder; 2. Thunder Wave if available; 3. switch only if Snorlax set forces it | Thunder | top-match | positive, route |
| 7 | p2 | 1. Double-Edge/Body Slam; 2. Curse; 3. Rest if needed | Double-Edge | top-match | positive, route |
| 8 | p1 | 1. Thunder; 2. handoff to phazer/setter if Rest is forced; 3. switch special wall | Cloyster | miss; failed to convert forced Rest into Cloyster entry | none |
| 8 | p2 | 1. Rest; 2. switch Steelix; 3. Double-Edge if no Rest | Rest | top-match | positive, route |
| 9 | p1 | 1. Spikes; 2. Toxic if spinner enters; 3. Explosion only after Spikes | Spikes | top-match | positive, route |
| 9 | p2 | 1. switch pressure/hazard answer; 2. Sleep Talk if available; 3. spinner/support pivot | Starmie | acceptable by hazard-answer class | positive, branch |
| 10 | p1 | 1. Toxic Starmie; 2. Zapdos handoff; 3. Explosion only if spinner removal opens route | Toxic blocked by Substitute | top-match by move, but route was blocked | positive, route attempt |
| 10 | p2 | 1. Rapid Spin; 2. Substitute to block Toxic; 3. Recover/coverage | Substitute | acceptable; under-ranked the status shield | positive, not branch |
| 11 | p1 | 1. attack to break Substitute; 2. Zapdos handoff; 3. no blind Explosion | Snorlax | miss; failed to preserve Cloyster while accepting Spin | positive but not route |
| 11 | p2 | 1. attack from behind Substitute; 2. Spin if hazard control is urgent; 3. Recover | Rapid Spin | miss; failed to choose the actual conversion move | none |
| 12 | p1 | 1. Sleep Talk; 2. switch Zapdos; 3. attack if awake | Sleep Talk -> Double-Edge | top-match | positive, route |
| 12 | p2 | 1. Nightmare only as high-risk package read with Steelix/Tyranitar fallback; 2. maintain Sub; 3. switch phazer/rock | Tyranitar | acceptable by counter-pivot fallback; no hidden-info error because the read was labeled | positive read, not route |
| 13 | p1 | 1. switch to Tyranitar owner; 2. Sleep Talk; 3. Zapdos only on Earthquake read | Exeggutor | acceptable by owner class | positive, branch |
| 13 | p2 | 1. Roar; 2. Dynamic Punch; 3. Rock Slide | Dynamic Punch | acceptable | positive, route |
| 14 | p1 | 1. Giga Drain/Grass pressure; 2. Sleep Powder; 3. Explosion only if target exact | confusion self-hit | unscored top/acceptable; state error for missing confusion | none |
| 14 | p2 | 1. switch to Exeggutor answer; 2. Fire/Crunch coverage if available; 3. Dynamic Punch | Zapdos | acceptable by switch class | positive, branch |
| 15 | p1 | 1. switch Snorlax to preserve Exeggutor; 2. status if confusion permits; 3. Explosion only as read | Explosion | miss; missed named-absorber cash-out into Zapdos | none |
| 15 | p2 | 1. Hidden Power Ice if available; 2. Thunder; 3. switch normal resist if Explosion read | Thunder | acceptable | positive, route |
| 16 | p1 | 1. Spikes reset; 2. Toxic if no Substitute; 3. Explosion only if spinner removal opens route | Zapdos | miss; repeated support into SubSpin instead of pressure handoff | none |
| 16 | p2 | 1. Substitute; 2. Rapid Spin if forced; 3. Surf/Recover | Substitute | top-match | positive, route, branch |

## Main Errors

Turns 10-11:
The helper initially hid the `-start` and `-activate` lines, making Starmie's
Substitute look less consequential than it was. The deeper decision error was
still mine: once Starmie revealed `Substitute`, the route was no longer
"Toxic/Spikes into spinner." It was "Starmie can shield from Toxic, keep the
Substitute, then Spin or attack unless pressure enters immediately."

Turns 8 and 12:
I improved on not treating RestTalk Snorlax as dead material, but I still did
not consistently convert Rest turns. Turn 8 should have made Cloyster entry
the top line sooner; turn 12 was good on p1, but p2's counter-pivot was
under-ranked behind an overexcited possible-only `Nightmare` read.

Turn 15:
The Exeggutor position was the biggest positive-selection miss. I saw
confusion and wanted to preserve the piece, but the actual line used Explosion
to remove active Zapdos. The post-study correction is not "always boom with
Exeggutor"; it is: when Exeggutor has lured the Electric/SleepTalk absorber
onto the field and revealed normal resists are not entering this turn, rank
Explosion as a real branch-punish route before safe preservation.

## Post-Run Study

Because this run was imperfect, no new replay was started. The follow-up study
is recorded in:

`docs/pokemon_mastery/reviews/subspin_exeggutor_cashout_review_001_2026-05-15.md`

Resulting code/doc changes:

- `tools/pokemon_mastery/replay_turn_pause.py` now includes `-start`,
  `-end`, and `-activate` reveal lines and carries active `Substitute` and
  `confusion` state into prompts.
- `tools/pokemon_mastery/tests/test_replay_turn_pause.py` covers the new
  volatile prompt and reveal behavior.
- `policy_cards/hazard_loop_spin_window.md` gained a SubSpin shield extension.
- `policy_cards/cashout_boundary.md` gained a named-absorber cash-out
  extension.
- `replay_turn_pause_protocol.md` now warns that unsupported volatiles still
  need manual carry-forward.

## Reusable Lesson

Against fast `Substitute` + `Rapid Spin` Starmie, the next move must answer
whether the Substitute lets Starmie dodge status and take a protected Spin
cycle. Rank pressure handoff, breaking the Substitute, or a named spinner
cash-out before repeating Toxic or Spikes.

Against Exeggutor's Electric/SleepTalk absorber branch, safe preservation is
not automatically positive selection. If Explosion removes the active route
blocker and the revealed resist/Ghost branches are accounted for, it may be
the move that converts the route.

Completed follow-up:
The compact regression probe is
`workspace/quick_tests/subspin_named_absorber_cashout_probe_001_2026-05-15.md`. It is
not progress evidence. The next proof must be a fresh packet that keeps severe
errors low while top-match, acceptable-match, route-conversion, and
branch-punish scores improve together.
