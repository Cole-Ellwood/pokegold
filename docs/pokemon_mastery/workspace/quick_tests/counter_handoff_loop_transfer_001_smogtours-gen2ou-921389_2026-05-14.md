# Counter-Handoff Loop Transfer 001 - smogtours-gen2ou-921389 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-921389`

Tournament source:
`https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-8.3779555/latest`

Mode: focused replay transfer, spectator-public, vanilla GSC. Replay actual
move is a weak pro-comparison oracle, not absolute truth.

Selected action:
Fresh no-keyword-screen transfer after `counter_handoff_loop_probe_001`,
scoring first handoff, counter-handoff, obeyed counter-handoff, active-pressure
stop condition, and third-owner re-score.

## Sources Checked

Local docs:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/workspace/quick_tests/counter_handoff_loop_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/active_pressure_before_status.md`

Web/current sources:

- Smogon GSC forum index and current GSC resource context.
- Smogon GSC OU Winter Seasonal #8 Round 8, used as the replay source context.
- Smogtours replay `smogtours-gen2ou-921389`, downloaded without printing or
  keyword-screening the log before turn 1.

## Contamination Control

Local search found no prior `921389` artifact before the replay was selected.
The raw log was downloaded to `tmp/pokemon_mastery_replays/` and the first
public state seen was the turn 1 prompt. Turns 1-20 were frozen before reveal.

After stopping the scored segment, a raw-log check for Substitute state exposed
later events. This replay is quarantined for any future fresh use beyond turn
20. The leakage happened after the frozen turn-1-through-20 score was complete.

## Score Summary

Turns scored: 1-20.

Scorable decisions: 40.

Top-match: 12 / 40.

Acceptable-match: 16 / 40.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 1.

Hidden-info errors: 0.

Earliest meaningful error: turn 1. I priced Snorlax lead sleep first and missed
both players using immediate Double-Edge pressure.

State error:
Turn 12 branch pricing around Rhydon's Substitute was uncertain. Surf had
broken the substitute on turn 11, and the turn-12 decision should have more
cleanly priced Starmie's Recover versus Surf rather than treating the position
as mostly forced.

## Focused Transfer Scores

First handoff found: 4 / 8 acceptable.

- Missed turn 2: p2 handed Snorlax to Tyranitar while I expected p2 to keep
  Double-Edge pressure.
- Hit turn 4 by class: p1 used Steelix as the Tyranitar answer.
- Missed turn 5: both sides left to Cloyster and Forretress.
- Missed turn 6: p1 handed Cloyster to Zapdos while Forretress used Toxic.
- Hit turn 8 by class: p1 used a Ground owner, Rhydon, into Raikou.
- Hit turn 13 by class: p1 handed Rhydon to Zapdos after the Starmie exchange.
- Missed turn 14: both sides reset to Snorlax.
- Hit turn 17: p1 used Steelix as the Rock-resist owner.

Counter-handoff found: 4 / 10 acceptable.

- Missed turn 4: p2 counter-handed Tyranitar to Snorlax into Steelix.
- Partial turn 7: I found a counter-handoff idea but named Tyranitar instead
  of Raikou.
- Missed turn 8: p2 answered the Ground owner by returning to Forretress.
- Hit turn 10 by class: Starmie answered the Substitute Rhydon route.
- Missed turn 14: p2 used Snorlax, not Raikou, as the Zapdos answer.
- Missed turn 15: p2 used Tyranitar into Resting Snorlax.
- Missed turn 17: p2 used Snorlax into Steelix again.
- Missed turn 18: p2 stayed active with Double-Edge instead of handing out.
- Hit turn 19 by class: p2 handed Snorlax to Forretress.
- Missed turn 20: p2 handed Forretress to Tyranitar while p1 left Steelix.

Counter-handoff obeyed: 3 / 7 acceptable.

- Hit turn 8 by class: p1 used a Ground owner into Raikou.
- Hit turn 13 by class: p1 preserved Rhydon from the Starmie board.
- Missed turn 14: I wanted Zapdos to attack instead of accepting the Snorlax
  reset.
- Missed turn 15: I wanted a Steelix handoff and missed Snorlax Rest.
- Missed turn 16: I wanted to preserve Snorlax and missed revealed Sleep Talk.
- Hit turn 17: p1 obeyed the Tyranitar pressure by using Steelix.
- Missed turn 20: p1 handed Steelix to poisoned Zapdos as p2 went Tyranitar.

Active-pressure stop condition: 3 / 8.

- Missed turns 1-2: overcalled sleep or handoff and underpriced lead
  Double-Edge.
- Missed turn 7: wanted Zapdos to attack, but both sides handed out.
- Hit turn 11: Starmie used Surf into Substitute and Rhydon attacked.
- Missed turn 12: expected Rhydon to leave, but it kept Earthquake pressure
  while Starmie recovered.
- Missed turn 15: expected a handoff and missed Snorlax's Rest.
- Hit turn 18: Steelix used Earthquake and Snorlax used Double-Edge.
- Hit turn 19: Steelix kept Earthquake pressure into the Forretress handoff.

Third-owner re-score: 2 / 4 acceptable.

- Missed turn 5: p1 used Cloyster, not Steelix, as the next owner.
- Hit turn 8 by class: p1 used Rhydon instead of Steelix as the Ground owner.
- Hit turn 13 by class: p1 used Zapdos to preserve Rhydon.
- Missed turn 20: p1 used poisoned Zapdos as the handoff from Steelix.

## Turn Notes

### Turns 1-6 - Lead Pressure Into Support Handoffs

Public shape:
Both Snorlax used Double-Edge instead of sleep. p2 then used Tyranitar as the
Normal resist, p1 used Zapdos into Rock Slide, then Steelix into Tyranitar.
The board moved through Cloyster and Forretress, and Forretress used Toxic into
Zapdos before setting or clearing anything else.

Frozen answer quality:
I overcalled sleep on turn 1 and handoff on turn 2. I found Tyranitar's Rock
Slide and p1's Steelix handoff, but missed the Cloyster/Forretress double
handoff and Forretress Toxic.

Lesson:
Do not let the support-loop lesson suppress simple active pressure. Lead
Double-Edge and Toxic-before-Spikes are both live route moves.

### Turns 7-13 - Rhydon Setup Versus Starmie

Public shape:
Zapdos and Forretress both left: p1 to Cloyster, p2 to Raikou. p1 then used
Rhydon as the Ground owner while p2 returned to Forretress. Rhydon revealed
Substitute and Curse. Starmie came in, broke the Substitute with Surf, recovered
once, then p1 finally handed Rhydon to Zapdos as Starmie recovered again.

Frozen answer quality:
I found the Ground-owner class but not exact Rhydon. I missed Substitute and
Curse, then overcorrected by assuming Rhydon was forced out too early. Starmie
Recover on turn 12 was correct, but p1's continued Earthquake pressure was a
real miss.

Lesson:
Setup under apparent counter-handoff changes the branch. If Substitute or a
boost makes the counter answer barely stable, do not call the forced switch
until the current sub, HP, speed order, and recovery clock are explicit.

### Turns 14-20 - Snorlax RestTalk And Phaze Loop

Public shape:
Both sides reset to Snorlax. p1 revealed Rest, then Sleep Talk, while p2 used
Tyranitar with Roar to drag poisoned Zapdos. p1 used Steelix as the Tyranitar
owner, p2 used Snorlax into Steelix, and Steelix kept Earthquake pressure until
p2 moved to Forretress. On turn 20 both sides handed again: p1 to poisoned
Zapdos, p2 to Tyranitar.

Frozen answer quality:
I missed RestTalk Snorlax and Roar Tyranitar. I did hit the later Steelix
Earthquake pressure and Forretress handoff, but failed the final third-owner
re-score when poisoned Zapdos entered as the Steelix handoff.

Lesson:
Counter-handoff is not only a species switch. RestTalk and Roar are also
counter-handoff tools because they change whether the active route can keep its
board.

## Error Classes Found

- Active-pressure underpricing returned: lead Double-Edge and Snorlax
  Double-Edge into Steelix were both missed after studying handoff loops.
- Support-set hidden roles remain live: Forretress Toxic, Rhydon Substitute
  plus Curse, RestTalk Snorlax, and Roar Tyranitar all changed the route.
- Exact handoff identity is still unstable, especially Snorlax/Tyranitar/
  Forretress counter-handoffs.
- Substitute state tracking needs a tighter explicit check before pricing
  forced switches.

## Next Rep

Run one small correction probe for setup-hidden-role stop conditions: when
Substitute or RestTalk lets the active stay through an apparent counter-handoff,
when phaze support is the counter-handoff, and when plain active damage should
still be preferred over a speculative loop.
