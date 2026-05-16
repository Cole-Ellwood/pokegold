# Branch Action Gate 002 - smogtours-gen2ou-910025 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-910025`.

Context source:
`https://www.smogon.com/forums/threads/gsc-trios-won-by-les-mehbouls.3776135/page-4`.

Mode: focused spectator-public vanilla GSC replay transfer. No team sheet was
supplied, no Team Preview was assumed, and only the public state revealed so
far was used.

Selected measurable action: rerun the branch-action gate with the added fourth
field from `active_context.md`:

`named branch -> action that beats it -> why active pressure is still enough -> best counter-switch if the branch happens`

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/workspace/quick_tests/branch_action_gate_001_smogtours-gen2ou-909834_2026-05-14.md`

Web sources checked:

- Smogon GSC Trios final page.
- Replay source `smogtours-gen2ou-910025`.

Contamination control:

- Local docs were searched for `910025`; no prior local use was found.
- Raw `.log` was downloaded to `tmp/pokemon_mastery_replays/`.
- The replay UI was not watched.
- The replay was selected from the same GSC Trios source list before content
  screening.

## Score Summary

Focused branch-scored decisions: 4 from turns 2-3.

Top-match: 2 / 4.

Acceptable-match: 2 / 4.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Earliest focused error: turn 2 p2. I named Cloyster's Spikes branch and also
named Starmie as the best counter-switch, but still leaned active Double-Edge.
The replay switched Starmie.

Stop reason: the named-branch/no-counter-switch miss repeated immediately on
turn 3 p1. I named Starmie's Rapid Spin branch but did not find the Snorlax
handoff that the replay used after accepting the Spin.

## Focused Decisions

### Turn 2 - Cloyster Spikes Branch

Public state: p1 Cloyster 72% vs p2 Snorlax 100%, Double-Edge revealed.

Named branch -> action:

- p1: Snorlax can stay and pressure or switch to a hazard answer -> Spikes is
  still the route job.
- p2: Cloyster will likely set Spikes -> Starmie is the best counter-switch if
  available -> I overrode this and leaned Double-Edge as active pressure.

Actual choices: p2 switched Starmie; p1 used Spikes.

Grade: p1 top, p2 miss.

Lesson: the fourth field surfaced the answer and I still failed to obey it.
When the best counter-switch is named and public enough, it should become the
recommendation unless active pressure clearly beats it.

### Turn 3 - Starmie Rapid Spin Branch

Public state: p1 Cloyster 78% with Spikes up on p2's side vs p2 Starmie 100%.

Named branch -> action:

- p1: Starmie can Rapid Spin -> no public Ghost is revealed, so Toxic or
  Explosion can control the spinner; I did not name a concrete counter-switch.
- p2: Cloyster may Toxic, Explode, or switch -> Rapid Spin immediately clears
  the route and is still the best action.

Actual choices: p1 switched Snorlax; p2 used Rapid Spin.

Grade: p1 miss, p2 top.

Lesson: after accepting Spin, the replay route was Snorlax handoff, not another
support click. The missing field was "best handoff if Spin happens"; this is a
close cousin of the counter-switch field.

## Error Classes

- Named counter-switch ignored: turn 2 p2.
- Named utility branch without handoff: turn 3 p1.
- No mechanics, hidden-info, state, or severe-blunder errors were scored.

## Next Rep

Do not repeat a full replay yet. Make the next focused gate a micro-format:

1. Name the branch.
2. Name the best counter-switch or handoff if the branch happens.
3. Only then choose attack, support, switch, cash-out, or preserve.

The next score should separate `counter-switch_found` from
`counter-switch_obeyed`.
