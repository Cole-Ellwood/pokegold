# Support-Set Hidden Role Transfer 001 - smogtours-gen2ou-921372 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-921372`

Mode: focused replay transfer, spectator-public, vanilla GSC. Replay actual
move is a weak pro-comparison oracle, not absolute truth.

Selected action:
Fresh no-keyword-screen transfer after
`support_set_hidden_role_probe_001`, scoring support-set hidden roles, exact
handoff identity, Rest/sleep handoff discipline, and branch action after naming.

## Sources Checked

Local docs:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/quick_tests/support_set_hidden_role_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/hidden_role_electric_transfer_002_smogtours-gen2ou-920961_2026-05-14.md`
- `docs/pokemon_mastery/policy_cards/hidden_role_voluntary_entry.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`

Web/current sources:

- Smogon, `Playing with Spikes in GSC`:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, `Introduction to Status in GSC`:
  `https://www.smogon.com/resources/competitive/gs/status`
- Smogon Forums, `Forretress (OU Revamp) Done`:
  `https://www.smogon.com/forums/threads/forretress-ou-revamp-done.3647111/`

## Contamination Control

Local search found no prior `921372` artifact before the replay was selected.
The raw log was downloaded to `tmp/pokemon_mastery_replays/` and the first
public state seen was the turn 1 prompt. No future turns were inspected before
freezing each answer.

Turn 2 p1 is unscored because freeze prevented the selected move from
appearing in the log.

## Score Summary

Turns scored: 1-16.

Scorable decisions: 31.

Top-match: 14 / 31.

Acceptable-match: 21 / 31.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful error: turn 1. I priced Lovely Kiss first and missed Jynx's
Thief support job into the Raikou switch.

## Focused Transfer Scores

Support-set hidden roles: 4 / 9 top, 5 / 9 acceptable.

- Missed turn 1: Jynx used Thief instead of immediate Lovely Kiss.
- Missed turn 3: Kingdra used Rest at 3% instead of switching out or attacking.
- Hit turn 5: Cloyster set Spikes and Snorlax used Lovely Kiss.
- Hit turn 6: sleeping Cloyster was preserved and p1 used Curse.
- Missed turn 9: p1 handed paralyzed boosted Snorlax to Skarmory.
- Missed turn 10: Skarmory used Toxic into the Zapdos handoff, not phaze.
- Hit turn 13: Toxic into Zapdos transferred after the first miss.
- Missed turn 15: I overcalled the Skarmory handoff while p1 stayed with
  Thunder.
- Partial turn 16: I found the Snorlax-answer class but named Skarmory instead
  of the actual Misdreavus.

Exact handoff identity: 5 / 11 top, 8 / 11 acceptable.

- Partial turn 1: I found a Raikou-preserving switch but not Kingdra.
- Partial turn 4: I found the handoff class but not p2's Cloyster.
- Hit turn 6 by route class: p2 preserved sleeping Cloyster into a Snorlax
  answer.
- Missed turn 9: p1 used Skarmory as the boosted-Snorlax handoff.
- Missed turns 11 and 14: p2 repeatedly handed Zapdos to Snorlax into Raikou.
- Hit turns 11 and 14: p1 handed Skarmory to Raikou.
- Hit turn 12: p1 handed Raikou back to Skarmory.
- Hit turn 13: p2 handed Snorlax to Zapdos and p1 used Toxic into it.
- Partial turn 16: p1 used Misdreavus, not Skarmory, as the Snorlax answer.

Rest/sleep handoff discipline: 3 / 5 top, 4 / 5 acceptable.

- Missed turn 3: Rest Kingdra was not priced.
- Partial turn 4: sleeping Kingdra was saved, but I overvalued possible Sleep
  Talk before a better owner was revealed.
- Hit turn 5: Snorlax used Lovely Kiss on Cloyster after Spikes.
- Hit turn 6: sleeping Cloyster was switched out and saved.
- Hit turn 16 by class: p1 used a Ghost/Snorlax-answer handoff instead of
  leaving low Raikou in.

Branch action after naming: mixed.

- Turn 10 failed: I named Zapdos/coverage pressure but missed Toxic as the move
  that covered the handoff.
- Turn 13 succeeded: after seeing the route, I used Toxic into Zapdos.
- Turn 14 failed: I named Electric pressure and missed p2's Snorlax
  counter-handoff into Raikou.
- Turn 15 failed in the opposite direction: I overcalled the double/handoff
  branch and p1/p2 stayed active.

## Turn Notes

### Turns 1-4 - Jynx Support And Rest Kingdra

Public shape:
Raikou led into Jynx. p1 switched Kingdra, Jynx used Thief, then Ice Beam
forced Kingdra to reveal Rest at 3%. Both sides then handed out: p1 to Snorlax
and p2 to Cloyster.

Frozen answer quality:
I covered the sleep threat but missed Thief, then missed Kingdra's Rest. After
Rest was revealed, I correctly widened the map to RestTalk, but overvalued
staying before p1 showed Snorlax as the better branch owner.

Lesson:
Lead Jynx is not only a sleep script. Thief and Ice Beam pressure can create
the support route before sleep appears.

### Turns 5-9 - Sleep Clause Value And Snorlax Mirror

Public shape:
Cloyster set Spikes and was put to sleep by Snorlax. p2 preserved the sleeping
Cloyster and moved to Snorlax. p1 Cursed, then Body Slammed, then overextended
to a second Curse and became paralyzed before switching to Skarmory.

Frozen answer quality:
I hit Spikes plus Lovely Kiss and the sleeping-Cloyster preservation. I also
hit Body Slam pressure on turn 7, but missed the Skarmory handoff on turn 9.

Lesson:
Once a boosted Snorlax becomes paralyzed, re-score whether it is still the
route piece. A healthy Skarmory or Ghost handoff may be the real preservation
line even when the visible Snorlax is boosted.

### Turns 10-16 - Toxic Handoff Loop And Counter-Handoff

Public shape:
Skarmory used Toxic into Zapdos, missed once and hit once. p1 repeatedly handed
Skarmory to Raikou when Zapdos appeared. p2 repeatedly counter-handed Zapdos to
Snorlax into Raikou. After Raikou stayed and missed Thunder, p1 finally used
Misdreavus as the Snorlax answer.

Frozen answer quality:
I missed the first Toxic into Zapdos but hit the repeat on turn 13. I hit the
Raikou handoffs from Skarmory, but missed p2's Snorlax counter-handoff twice.
Turn 15 was an overcorrection: I predicted handoff and p1/p2 stayed active.

Lesson:
After a support handoff loop is revealed, do not freeze it into a script. The
second-order branch is often counter-handoff, but active pressure remains live
when the opponent refuses to leave.

## Error Classes Found

- Support-set hidden roles partially transferred: the second Skarmory Toxic
  was found, but Jynx Thief, Kingdra Rest, first Skarmory Toxic, and
  paralyzed-Snorlax handoff were missed.
- Exact handoff identity remains unstable in loops: Raikou handoff was found,
  but Snorlax counter-handoff into Raikou was missed twice.
- Sleep discipline improved around preserving slept Cloyster, but I still
  missed Rest Kingdra before the set was public.
- Branch-action after naming overcorrected on turn 15: I expected another
  double instead of accepting active Thunder and Body Slam pressure.

## Next Rep

Run one small correction probe for two loop-specific boundaries: counter-handoff
after the first support handoff is revealed, and the stop condition for not
overcalling that counter-handoff when both actives can still make progress.
