# Branch Action Gate 001 - smogtours-gen2ou-909834 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-909834`.

Context source:
`https://www.smogon.com/forums/threads/gsc-trios-won-by-les-mehbouls.3776135/page-4`.

Mode: focused spectator-public vanilla GSC replay transfer. No team sheet was
supplied, no Team Preview was assumed, and only the public state revealed so
far was used.

Selected measurable action: run the branch-action gate from `active_context.md`.
Before every scored answer, force the line:

`named branch -> action that beats it -> why active pressure is still enough, if it is.`

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/workspace/quick_tests/branch_action_focus_002_gen2ou-2595974016_2026-05-14.md`

Web sources checked:

- Smogon GSC Trios final page.
- Replay source `smogtours-gen2ou-909834`.

Contamination control:

- Local docs were searched for `909834`; no prior local use was found.
- Raw `.log` was downloaded to `tmp/pokemon_mastery_replays/`.
- The replay UI was not watched.
- The replay was selected from a current-archive Smogon GSC tournament page
  before content screening for branch positions.

## Score Summary

Focused branch-scored decisions: 8 from turns 1-5.

Top-match: 2 / 8.

Acceptable-match: 4 / 8.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Earliest focused error: turn 1. I overcalled the Lovely Kiss branch from
Nidoking and the sleep-absorber switch from Snorlax; the replay used Thief and
Double-Edge first.

Repeated error: by turn 5, I had both overread a branch when active pressure
was enough and underfound the counter-switch after naming a likely switch. The
gate failed before continuing deeper into the replay.

## Focused Decisions

### Turn 1 - Nidoking Lead Into Snorlax

Public state: p1 Nidoking 100% vs p2 Snorlax 100%.

Named branch -> action:

- p1: Snorlax may switch to a Nidoking answer -> Lovely Kiss still beats many
  stay and switch lines -> active sleep pressure is enough if sleep lands.
- p2: Nidoking may use Lovely Kiss -> switch to a sleep absorber or sack.

Actual choices: p1 used Thief; p2 used Double-Edge.

Grade: both miss.

Lesson: do not force the sleep branch before the replay shows that the players
value sleep more than immediate item removal and damage. Active pressure was
the correct opener on both sides.

### Turn 3 - Sleeping Snorlax Switch-Out

Public state: p1 Nidoking 66% with Lovely Kiss / Thief vs p2 Snorlax 87%
asleep.

Named branch -> action:

- p1: sleeping Snorlax likely switches out -> Earthquake into the receiver.
- p2: save sleeping Snorlax for Sleep Clause value -> switch to a Nidoking
  answer.

Actual choices: p1 switched Forretress; p2 switched Victreebel.

Grade: p1 miss, p2 acceptable by switch-out class.

Lesson: Earthquake named the switch but did not solve the next board. The
better branch action was a counter-switch that met the actual Victreebel route.

### Turn 4 - Victreebel Sleep Branch

Public state: p1 Forretress 100% vs p2 Victreebel 100%.

Named branch -> action:

- p1: Victreebel can use Sleep Powder -> switch a sleep absorber.
- p2: Forretress or a sleep absorber may enter -> Sleep Powder still changes
  the route because p2 has not slept anything yet.

Actual choices: p1 switched Snorlax; p2 used Sleep Powder.

Grade: p1 acceptable, p2 top.

Lesson: this was the gate doing its job. The named branch produced the correct
class for both sides.

### Turn 5 - After Sleep Lands

Public state: p1 Snorlax 100% asleep vs p2 Victreebel 100% with Sleep Powder
revealed.

Named branch -> action:

- p1: sleeping Snorlax should usually be saved if a Victreebel answer exists
  -> switch Forretress.
- p2: Forretress is the likely counter-switch -> use a move that pressures
  Forretress, such as paralysis, setup, or coverage, if available.

Actual choices: p1 switched Forretress; p2 switched Cloyster.

Grade: p1 top, p2 miss.

Lesson: p2's better branch action was counter-switching to the support mirror.
I named the Forretress receiver, but I did not ask which teammate met it best.

## Error Classes

- Overcalled branch: turn 1 treated sleep lines as forced when active pressure
  was the replay route.
- Underfound counter-switch: turns 3 and 5 named the switch, but the better
  answer was a counter-switch to the next board rather than a simple attack or
  in-place support move.
- No mechanics, hidden-info, state, or severe-blunder errors were scored.

## Next Rep

Do not broaden yet. Run one more branch-action gate with the same forced line,
but add a fourth field:

`best counter-switch if my named branch happens`

Pass condition: at least 6 branch decisions, at least 70% acceptable, and no
repeated miss where the branch was named but the counter-switch was not priced.
