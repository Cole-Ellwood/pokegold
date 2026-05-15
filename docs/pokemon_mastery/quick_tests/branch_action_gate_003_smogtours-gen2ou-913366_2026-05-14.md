# Branch Action Gate 003 - smogtours-gen2ou-913366 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-913366`.

Context source:
`https://www.smogon.com/forums/threads/gsc-trios-won-by-les-mehbouls.3776135/page-4`.

Mode: focused spectator-public vanilla GSC replay transfer. No team sheet was
supplied, no Team Preview was assumed, and only the public state revealed so
far was used.

Selected measurable action: rerun the branch-action gate from
`active_context.md` while splitting `counter-switch_found` from
`counter-switch_obeyed`.

Forced answer format:

1. Name the branch.
2. Name the best counter-switch or handoff if the branch happens.
3. Choose attack, support, switch, cash-out, or preserve.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/quick_tests/branch_action_gate_002_smogtours-gen2ou-910025_2026-05-14.md`

Web sources checked:

- Smogon GSC Trios final page.
- Replay source `smogtours-gen2ou-913366`.

Contamination control:

- Local docs were searched for `913366`; no prior local use was found.
- Raw `.log` was downloaded to `tmp/pokemon_mastery_replays/`.
- The replay UI was not watched.
- The replay was selected from the GSC Trios source list before content
  screening.

## Score Summary

Focused branch-scored decisions: 11 from turns 1-11.

Top-match: 4 / 11.

Acceptable-match: 5 / 11.

Counter-switch or handoff found: 5 / 11.

Counter-switch or handoff obeyed when found: 3 / 5.

Correctly obeyed handoff: 2 / 5.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Earliest focused error: turn 1 p2. I treated Forretress's first job as Spikes
and did not find the Skarmory handoff into Snorlax.

Repeated error: the failed class shifted from "found but ignored" to "wrong or
missing handoff identity." I obeyed some found branches, but too often named
the wrong receiver or kept support/active pressure when the replay used a
handoff.

## Focused Decisions

| Turn | Side | Named branch | Handoff found | Frozen action | Actual | Grade |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Forretress may switch to a physical wall or set Spikes. | No exact handoff needed; Double-Edge still hits Skarmory. | Double-Edge | Double-Edge into Skarmory | Top |
| 1 | p2 | Snorlax can pressure Forretress immediately. | Not found. | Spikes | Skarmory switch | Miss |
| 2 | p1 | Skarmory can Toxic. | Electric/pressure switch found, but it walks into Toxic. | Switch pressure piece | Double-Edge | Miss |
| 3 | p1 | Skarmory may preserve itself with Forretress. | Active Double-Edge still punishes. | Double-Edge | Double-Edge into Forretress | Top |
| 3 | p2 | Skarmory is low and can hand off to Forretress. | Forretress found and obeyed. | Switch Forretress | Switch Forretress | Top |
| 4 | p1 | Forretress can set Spikes. | Pressure switch found but not better than damage. | Switch pressure piece | Double-Edge | Miss |
| 5 | p2 | Resting Snorlax can reset the clock. | Tyranitar handoff not found. | Explosion or pressure | Switch Tyranitar | Miss |
| 7 | p1 | Tyranitar can stay and attack or switch. | Surf as active punish not obeyed; I overvalued Spikes. | Spikes | Surf | Miss |
| 8 | p1 | Tyranitar likely leaves for an Electric/special pressure piece. | Surf still punishes the receiver enough. | Surf | Surf into Jolteon | Top |
| 9 | p1 | Jolteon will attack with Electric pressure. | Handoff found, but wrong identity; Snorlax was the replay absorber. | Switch Ground/Steelix class | Switch Snorlax | Miss |
| 10 | p2 | SleepTalk Snorlax can keep clicking into Jolteon. | Skarmory receiver found and obeyed. | Switch Skarmory | Switch Skarmory | Top |
| 11 | p1 | Skarmory is low but can Rest or reset. | Cloyster handoff not found. | Sleep Talk | Switch Cloyster | Miss |

## What Changed

The explicit split helped. I no longer ignored every named handoff; turn 3 p2
and turn 10 p2 were clean obeyed counter-switches, and turn 8 p1 correctly
recognized that Surf still punished the receiver.

The remaining failure is receiver identity and handoff timing:

- I over-switch away from Snorlax when active Double-Edge is still the best
  pressure.
- I miss handoffs after a support job or Rest reset: Forretress to Tyranitar,
  Jolteon to Snorlax, and Skarmory Rest to Cloyster.
- I still treat some support moves, especially Spikes, as generically useful
  even when immediate damage or handoff solves the branch.

## Next Rep

Run one small constructed micro-probe from this gate, not another replay first.
The probe should use four scenarios:

1. Active pressure still beats the named receiver.
2. Counter-switch is found and must be obeyed.
3. Counter-switch is found but rejected because it walks into the branch.
4. Support move is tempting, but damage or handoff beats the branch.
