# Hidden Role Electric Transfer 001 - smogtours-gen2ou-920951 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-920951`

Tournament source:
`https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-8.3779555/latest`

Mode: focused replay transfer, spectator-public, vanilla GSC. Replay actual
move is a weak pro-comparison oracle, not absolute truth.

Selected action:
Fresh no-keyword-screen transfer after
`resttalk_hidden_role_correction_probe_001`, scoring RestTalk stay/handoff,
hidden-role voluntary entry, and active pressure into named receivers.

## Sources Checked

Local docs:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/workspace/quick_tests/electric_receiver_resttalk_transfer_001_smogtours-gen2ou-920928_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/resttalk_hidden_role_correction_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/policy_cards/hidden_role_voluntary_entry.md`

Web/current sources:

- Smogon GSC OU Winter Seasonal #8 Round 8, used for this fresh replay.
- Smogon GSC OU Winter Seasonal #8 Round 9 and GSC OU Global Championship 2026
  search results, checked for current replay-source context.

## Contamination Control

Local search found no prior `920951` artifact. The raw log was downloaded to
`tmp/pokemon_mastery_replays/` without printing the log. The first public state
seen was the turn 1 prompt. No keyword screening was used.

## Score Summary

Turns scored: 1-22.

Scorable decisions: 44.

Top-match: 14 / 44.

Acceptable-match: 19 / 44.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 1.

Earliest meaningful error: turn 1. I wanted Tyranitar to attack Raikou and
missed the Snorlax handoff into Thunder.

Hidden-info error:
Turn 6, I assigned Fire Blast to unrevealed Tyranitar instead of treating that
as a possible lure while still pricing the actual handoff map.

## Focused Transfer Scores

RestTalk stay/handoff: not tested cleanly.

Electric receiver identity: 2 / 5.

- Missed turn 1: Tyranitar handed off to Snorlax on Raikou's Thunder.
- Missed turn 9: Zapdos handed off to Snorlax as Skarmory switched to Raikou.
- Partial turn 16: I named Raikou as the receiver and kept active pressure, but
  did not choose the exact Thunderbolt.
- Missed turn 17: Zapdos stayed and kept pressuring Raikou; I over-switched.
- Partial turn 18: I found the Electric handoff class but named Snorlax instead
  of the actual Steelix.

Hidden-role voluntary entry: 0 / 3.

- Missed turn 20: Gengar entered on Starmie specifically to block Rapid Spin.
- Missed turn 21: Umbreon entered on Gengar as a receiver and Pursuit threat.
- Missed turn 22: Umbreon used Pursuit as Snorlax switched; I assigned generic
  Charm or trap support instead.

Active pressure into named receiver: 2 / 4.

- Missed turn 2: Snorlax used Double-Edge into the Skarmory receiver after I
  chose setup.
- Hit turn 16 by class: Zapdos kept active Electric pressure into named Raikou.
- Missed turn 17: Zapdos stayed into Raikou with Thunderbolt after I wanted to
  hand off.
- Hit turn 19: Steelix used Earthquake into the Starmie receiver after Raikou
  left.

Spinblock handoff: 0 / 1.

- Missed turn 20: Gengar handoff blocked Starmie's Rapid Spin.

## Turn Notes

### Turns 1-4 - Raikou And Skarmory Handoff Loop

Public shape:
Tyranitar led into Raikou. p1 handed to Snorlax on Thunder, p2 handed to
Skarmory on Snorlax, then p1 tried to bring Zapdos into Skarmory while Skarmory
kept Whirlwind pressure.

Frozen answer quality:
I missed Tyranitar to Snorlax on turn 1 and over-selected setup with Snorlax on
turn 2. I did find the Zapdos handoff into Skarmory on turn 4.

Lesson:
Electric receiver identity starts on turn 1. Do not let the lead matchup
override the immediate handoff map.

### Turns 5-11 - Whirlwind Loop And Receiver Map

Public shape:
Skarmory repeatedly Whirlwinded Zapdos attempts. Tyranitar and Cloyster were
dragged or switched in. When Zapdos finally entered, p2 switched Skarmory to
Raikou and p1 answered by going Snorlax. Later p1 used Tyranitar into Skarmory
and then Cloyster into Starmie.

Frozen answer quality:
I over-kept trying to pressure with unrevealed Tyranitar moves and missed the
Snorlax handoff on turn 9. I also missed the Starmie receiver on turn 11.

Lesson:
Repeated phaze loops punish imagined coverage. Use the public handoff map first
and treat unrevealed coverage as a contingency.

### Turns 12-16 - Starmie, Spikes, And Named Receiver Pressure

Public shape:
Cloyster handed out to Snorlax on Starmie's Psychic, later set Spikes as
Skarmory switched to Starmie. Zapdos entered on Starmie's Psychic and used
Thunderbolt into Raikou.

Frozen answer quality:
I hit Snorlax into Starmie on turn 12 and Spikes on turn 14. I missed Zapdos
into Starmie on turn 15, but did name Raikou on turn 16 and chose active
Electric pressure by class.

Lesson:
The receiver-pressure rule transferred once: active pressure is acceptable when
the receiver is named and the damage improves that receiver board.

### Turns 17-22 - Hidden Role Failures

Public shape:
Zapdos stayed in against Raikou and kept using Thunderbolt. Steelix then took
Raikou's Hidden Power and Earthquaked the Starmie receiver. Gengar entered on
Starmie's Rapid Spin, then Umbreon entered on Gengar and used Pursuit as
Snorlax switched out.

Frozen answer quality:
I over-switched away from Zapdos on turn 17, found the Electric handoff class
but not exact Steelix on turn 18, hit Earthquake into Starmie on turn 19, and
then missed three hidden-role branches in a row: Gengar spinblock, Umbreon
receiver, and Pursuit.

Lesson:
Hidden-role voluntary entry is still the live miss. When Gengar or Umbreon
enters a narrow-looking board, price spinblock, trap, Pursuit, and one-time
support before assigning a generic response.

## Error Classes Found

- Electric receiver identity improved only partially: I found some receiver
  pressure but still missed the exact Snorlax or Steelix handoff.
- Hidden-role voluntary entry failed badly in the late segment: spinblock,
  Umbreon receiver, and Pursuit were all missed.
- RestTalk boundary was not tested cleanly in this replay.
- Hidden-information discipline still needs work around unrevealed Tyranitar
  coverage.

## Next Rep

Run a fresh transfer that keeps the same hidden-role voluntary-entry target but
does not require RestTalk to appear. Score Gengar spinblock, Umbreon Pursuit or
trap, active pressure into named receiver, and exact Electric handoff identity.
