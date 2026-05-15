# Setup Hidden Role Stop Transfer 001 - smogtours-gen2ou-921412 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-921412`

Tournament source:
`https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-8.3779555/latest`

Mode: focused replay transfer, spectator-public, vanilla GSC. Replay actual
move is a weak pro-comparison oracle, not absolute truth.

Selected action:
Fresh no-keyword-screen transfer after `setup_hidden_role_stop_probe_001`,
scoring Substitute or setup stop conditions, RestTalk or sleep handoff,
phaze-support counter-handoff, and active damage over speculative loops.

## Sources Checked

Local docs:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/quick_tests/setup_hidden_role_stop_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/counter_handoff_loop_transfer_001_smogtours-gen2ou-921389_2026-05-14.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/policy_cards/active_pressure_before_status.md`

Web/current sources:

- Smogon, `Playing with Spikes in GSC`:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, `Tyranitar (OU Revamp) [Done]`:
  `https://www.smogon.com/forums/threads/tyranitar-ou-revamp-done.3658517/`
- Smogon Forums, `GSC OU Snorlax`:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon, `GSC OU Threatlist`:
  `https://www.smogon.com/gs/articles/gsc_threats`

## Contamination Control

Local search found no prior `921412` artifact before the replay was selected,
except an earlier note that `921412` had not been used. The raw log was
downloaded to `tmp/pokemon_mastery_replays/` and the first public state seen
was the turn 1 prompt. No future turns were inspected before freezing each
answer.

Turn 20 p1 is unscored because full paralysis hid the chosen action.

## Score Summary

Turns scored: 1-20.

Scorable decisions: 39.

Top-match: 16 / 39.

Acceptable-match: 25 / 39.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful error: turn 1 p2. I missed the immediate Forretress to
Raikou counter-handoff.

## Focused Transfer Scores

Setup or support stop conditions: 6 / 11 acceptable.

- Hit turn 4: Snorlax attacked and Skarmory phazed instead of letting setup
  continue.
- Missed turn 5: p1 immediately re-entered Snorlax and Skarmory used active
  Drill Peck.
- Missed turn 9: Snorlax chose Curse instead of Rest or leaving.
- Missed turn 10: Snorlax chose another Curse at low HP.
- Hit turn 11 by class: Snorlax finally left and preserved the route piece.
- Hit turn 12: Raikou revealed Roar as phaze support.
- Missed turn 14: Raikou revealed Reflect before continuing the phaze loop.
- Hit turn 15: Raikou used Roar after Reflect.
- Hit turn 16: Thunderbolt punished Forretress while Forretress set Spikes.
- Partial turn 17: I found Roar only conditionally, but expected damage first.
- Missed turn 18: Misdreavus became the third owner into the Raikou loop.

Active damage over speculative loops: 8 / 12 acceptable.

- Hit turn 1 p1, turn 2 p2, and turns 7-8: Raikou kept Electric pressure while
  the opponent handed to the special owner.
- Hit turn 4: Snorlax used Double-Edge into Skarmory.
- Missed turns 5-6: I overexpected support or continued Snorlax pressure, but
  the replay used Drill Peck and then mutual handoff.
- Hit turns 9-11 p2: Raikou kept Thunderbolt pressure into Snorlax until it
  finally left.
- Hit turn 13: Raikou used Thunderbolt into the Snorlax counter-handoff.
- Missed turn 17: I wanted Thunderbolt, but Roar caught the Raikou switch.
- Hit turn 19 p2: Raikou stayed and hit Misdreavus rather than immediately
  fleeing Toxic/trap pressure.

Phaze-support counter-handoff: 4 / 6 acceptable.

- Hit turn 4: Skarmory Whirlwind stopped boosted Snorlax.
- Hit turn 12: Raikou Roar broke the Raikou mirror.
- Hit turn 15: Raikou Roar converted after Reflect.
- Partial turn 17: I named Roar if the switch was obvious, but did not make it
  the main line.
- Missed turn 18: p1 used Misdreavus as the third-owner answer after phazing.
- Missed turn 20 p2: I overcalled Rest or pivot while Raikou kept attacking.

RestTalk or sleep handoff: lightly tested.

- Missed turns 9-10: I overcalled Rest as likely while Snorlax kept using
  Curse at low HP.
- Hit turn 11 by class: low Snorlax finally left.
- No RestTalk was revealed in the scored segment.

Exact handoff identity: still weak.

- Missed p2 Raikou handoff on turn 1.
- Hit p1 Snorlax handoff on turns 2 and 8.
- Missed p2 exact Skarmory on turn 3 but found Snorlax-answer class.
- Missed p1 Snorlax re-entry on turn 5.
- Missed p2 Misdreavus and p1 Raikou on turn 6.
- Hit p2 Raikou handoff on turn 7 by class.
- Missed p2 Snorlax handoff on turn 13.
- Missed p2 Raikou and p1 Misdreavus handoffs on turn 18.

## Turn Notes

### Turns 1-8 - Electric Pressure And Snorlax/Skarmory Loop

Public shape:
Raikou led into Forretress. Forretress immediately handed to Raikou, p1 handed
to Snorlax, and p2 answered with Skarmory. Snorlax used Curse, then
Double-Edge; Skarmory used Whirlwind. After Umbreon was dragged, p1 returned
to Snorlax, then both sides handed into Raikou and Misdreavus/Raikou before
Snorlax again took the Electric pressure.

Frozen answer quality:
I hit the early active Electric pressure and Snorlax handoff, but missed the
initial Raikou counter-handoff, exact Skarmory identity, Umbreon-to-Snorlax
return, and the Misdreavus/Raikou mutual handoff.

Lesson:
The active-pressure correction transferred, but exact handoff identity is still
too species-template driven.

### Turns 9-15 - Low Snorlax, Roar Raikou, And Reflect

Public shape:
Snorlax kept using Curse at 55%, then 39%, while Raikou repeatedly used
Thunderbolt. At 21%, Snorlax finally left to Raikou. p1 Raikou revealed Roar,
then later Reflect, then Roar again to drag Forretress.

Frozen answer quality:
I overcalled Rest on Snorlax and did not price the no-Rest setup line well
enough. I did hit Thunderbolt pressure and the later Roar line, but missed
Reflect as the support move that made more Roar cycling safer.

Lesson:
Low setup without revealed Rest should be treated as a high-variance stay
branch, not automatically corrected into Rest. Screen plus phaze is a route
package, not two separate support moves.

### Turns 16-20 - Spikes, Third Owner, And Toxic Pressure

Public shape:
Raikou damaged Forretress while Forretress set Spikes. Raikou then Roared the
Raikou switch back into Forretress. On the next loop, p1 used Misdreavus as the
third owner while p2 used Raikou. Misdreavus Toxic poisoned Raikou while taking
Thunderbolt and paralysis. Raikou then stayed and attacked again.

Frozen answer quality:
I hit Thunderbolt plus Spikes and recognized Roar as a switch-catching option,
but missed Misdreavus as the third owner. I correctly kept active pressure live
on turn 19, but overcalled p2 Rest or pivot on turn 20.

Lesson:
Third-owner re-score still needs work. A new owner can enter not because it is
the default answer, but because it changes the loop by threatening status,
trap, immunity, or preservation.

## Error Classes Found

- Exact handoff identity remains the largest miss, especially when the handoff
  is a second or third owner rather than the first obvious species answer.
- Screen plus phaze support was underpriced until Roar was already public.
- Low Snorlax setup was overcorrected into assumed Rest; absence of Rest reveal
  matters.
- Active damage improved compared with `921389`, but the stop condition still
  oscillated: I missed Drill Peck and overcalled Rest/pivot on turn 20.

## Next Rep

Run one small correction probe for screen-plus-phaze and third-owner loop
re-score: Reflect enabling Roar, third-owner Misdreavus into Electric loops,
low setup without Rest reveal, and when active damage remains better than
Rest/pivot.
