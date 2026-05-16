# Hidden Role Electric Transfer 002 - smogtours-gen2ou-920961 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-920961`

Tournament source:
`https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-8.3779555/latest`

Mode: focused replay transfer, spectator-public, vanilla GSC. Replay actual
move is a weak pro-comparison oracle, not absolute truth.

Selected action:
Fresh no-keyword-screen transfer after
`hidden_role_electric_transfer_001`, scoring hidden-role voluntary entry,
RestTalk sleeper handoff, exact Electric handoff identity, and branch action
after naming a receiver.

## Sources Checked

Local docs:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/workspace/quick_tests/hidden_role_electric_transfer_001_smogtours-gen2ou-920951_2026-05-14.md`
- `docs/pokemon_mastery/policy_cards/hidden_role_voluntary_entry.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`

Web/current sources:

- Smogon GSC OU Winter Seasonal #8 Round 8, used for this fresh replay.
- Smogtours replay `smogtours-gen2ou-920961`, downloaded without printing or
  keyword-screening the log.

## Contamination Control

Local search found no prior `920961`, `921372`, `921389`, or `921412`
artifact. The raw log was downloaded to `tmp/pokemon_mastery_replays/` and the
first public state seen was the turn 1 prompt. No future turns were inspected
before freezing each answer.

## Score Summary

Turns scored: 1-22.

Scorable decisions: 44.

Top-match: 21 / 44.

Acceptable-match: 27 / 44.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful error: turn 3. I wanted Misdreavus to Protect instead of
using the actual Jolteon handoff to preserve Misdreavus after Perish Song.

## Focused Transfer Scores

RestTalk sleeper handoff: 3 / 7 top, 4 / 7 acceptable.

- Missed turn 8: Jolteon used Rest before Snorlax could take over the board.
- Hit turn 10: sleeping Jolteon returned into Electric pressure.
- Partial turn 11: I stayed with sleeping Jolteon but missed Sleep Talk as the
  actual active job.
- Missed turn 12: p1 handed from RestTalk Jolteon back to Forretress instead
  of staying to burn more sleep turns.
- Hit turns 13-14: Jolteon returned into Raikou and used Sleep Talk.
- Missed turn 15: after Growth, p1 still switched to Forretress on Snorlax's
  Earthquake instead of letting the boosted sleeper continue by habit.

Electric handoff identity: 3 / 6 exact, 4 / 6 acceptable.

- Hit turn 1: p2 handed Misdreavus to Raikou.
- Partial turn 6: I found the Electric handoff class but named Raikou instead
  of Zapdos.
- Hit turn 9: p2 used Zapdos as the Forretress/Misdreavus pressure piece.
- Missed turn 10: Zapdos handed to Raikou as p1 returned to Jolteon.
- Missed turn 12: Snorlax handed to Raikou as p1 returned to Forretress.
- Hit turn 21: p2 used Zapdos again when Misdreavus threatened Snorlax.

Hidden-role voluntary entry: 0 / 7 exact.

- Missed turn 6: Misdreavus clicked Destiny Bond instead of the expected
  trap/perish continuation.
- Missed turn 8: Jolteon revealed Rest.
- Missed turn 11: Jolteon revealed Sleep Talk as its active sleeping job.
- Missed turn 16: Forretress used Toxic before Spikes.
- Missed turn 18: p1 revealed Skarmory as the physical Snorlax answer.
- Missed turn 19: Skarmory revealed Curse instead of default phazing.
- Missed turn 22: Zapdos revealed Whirlwind to break the Misdreavus trap.

Branch action after naming: failed the key continuation.

- Turn 20: I named the likely Electric handoff and counter-switched Jolteon,
  but p2 stayed asleep while p1 used Misdreavus to threaten the Snorlax route.
- Turn 21: I named Zapdos and wanted Jolteon, but the actual route was Mean
  Look into the Zapdos switch.
- Turn 22: after the trap landed, I treated Zapdos as direct Electric pressure
  and missed Whirlwind as the route-breaking support move.

## Turn Notes

### Turns 1-8 - Trap Lead Into RestTalk Jolteon

Public shape:
Misdreavus trapped Raikou, used Perish Song, then handed to Jolteon. Zapdos
entered as the anti-Misdreavus pressure piece. Jolteon Rested as Snorlax came
in, revealing that the sleeping Electric was a future route piece rather than
only a passive sleeper to preserve.

Frozen answer quality:
The early trap line was mostly correct, but I missed the exact p1 defensive
handoff on turn 3, Misdreavus's Destiny Bond on turn 6, and Jolteon's Rest on
turn 8.

Lesson:
Rest on a fast Electric should immediately widen the set map to RestTalk and
setup support. Do not reduce the next decision to "switch sleeper out" or
"burn wake turns"; name the exact board the sleeper is buying.

### Turns 9-15 - RestTalk Handoffs And Raikou Identity

Public shape:
p1 revealed Forretress, repeatedly using it and Jolteon to manage Snorlax,
Raikou, and Zapdos. p2 used Raikou, not only Zapdos, as the exact handoff into
Jolteon/Forretress boards. Jolteon revealed Sleep Talk and Growth before p1
still handed back to Forretress on Snorlax's Earthquake.

Frozen answer quality:
I hit p1's turn-10 and turn-13 Jolteon handoffs and p2's turn-11 and turn-14
Snorlax handoffs, but I missed p2's Raikou switches on turns 10 and 12 and
over-kept boosted Jolteon in on turn 15.

Lesson:
After RestTalk plus Growth is public, staying is not automatic. If Snorlax has
Earthquake and the team has a physical sponge handoff, price the handoff before
trying to convert the boost.

### Turns 16-22 - Support-Set Reveals And Trap Breaking

Public shape:
Forretress used Toxic, then Spikes. Skarmory entered on Snorlax and revealed
Curse. Misdreavus entered as Snorlax slept, caught Zapdos with Mean Look, then
Zapdos revealed Whirlwind and dragged Snorlax.

Frozen answer quality:
I hit Spikes plus Earthquake on turn 17 and Snorlax Rest on turn 19, but missed
the important support roles: Toxic Forretress, Curse Skarmory, and Whirlwind
Zapdos. The final miss matters because I treated trap plus Perish as the whole
route and did not price phaze as the support answer to trapping.

Lesson:
When a support Pokemon enters a narrow board, hidden role does not only mean
coverage or Explosion. It can be Toxic before Spikes, Curse instead of phaze,
or phaze specifically to break a trap route.

## Error Classes Found

- Hidden-role voluntary entry is still the largest miss: the run exposed
  Destiny Bond Misdreavus, RestTalk Growth Jolteon, Toxic Forretress, Curse
  Skarmory, and Whirlwind Zapdos.
- Electric receiver identity improved at the start and end but still missed
  repeated Zapdos-to-Raikou and Snorlax-to-Raikou handoffs.
- RestTalk handling improved after reveal, but I overcorrected by wanting the
  boosted sleeper to stay when the physical sponge handoff was better.
- Branch-action after naming remains unstable when the named branch is a
  support move rather than a switch.

## Next Rep

Run one small correction probe for support-set hidden roles: RestTalk setup
handoff, Toxic-before-Spikes Forretress, Curse Skarmory, and phaze-to-break-
trap Zapdos. The probe should force a move on each board and score whether the
answer names the route that the hidden support move changes.
