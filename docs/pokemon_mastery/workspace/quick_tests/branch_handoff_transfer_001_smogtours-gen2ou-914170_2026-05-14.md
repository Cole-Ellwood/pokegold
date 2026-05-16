# Branch Handoff Transfer 001 - smogtours-gen2ou-914170 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-914170`.

Context source:
`https://www.smogon.com/forums/threads/gsc-trios-won-by-les-mehbouls.3776135/page-4`.

Mode: focused spectator-public vanilla GSC replay transfer. No team sheet was
supplied, no Team Preview was assumed, and only the public state revealed so
far was used.

Selected measurable action: transfer
`branch_handoff_obedience_probe_001` to a fresh no-keyword-screen replay. The
extra fields were scored separately: branch found, handoff or branch-beating
action found, handoff obeyed, and rejected because it walks into the branch.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/workspace/quick_tests/branch_handoff_obedience_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`

Web sources checked:

- Smogon GSC Trios final page.
- Replay source `smogtours-gen2ou-914170`.

Contamination control:

- Local docs were searched for `914170`; no prior local use was found.
- Raw `.log` was downloaded to `tmp/pokemon_mastery_replays/`.
- The replay UI was not watched.
- The replay was selected from a Smogon GSC tournament page before content
  screening.

## Score Summary

Focused branch-scored decisions: 12 from turns 1-12.

Top-match: 5 / 12.

Acceptable-match: 7 / 12.

Branch found: 10 / 12.

Handoff or branch-beating action found: 7 / 12.

Handoff obeyed when found: 5 / 7.

Correctly obeyed handoff or branch action: 4 / 7.

Valid rejection because the handoff walked into the branch: 1 / 2.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Earliest focused error: turn 1 p1. I found Zapdos's immediate Thunder branch
but over-preserved Forretress with a receiver switch. The replay used
Forretress Explosion into Zapdos.

Repeated error class: branch identity was usually found, but the best
branch-beating action was still unstable. I missed the Forretress cash-out into
Zapdos, missed Golem as the Thunder receiver, and over-assumed sleeping Raikou
would switch instead of using Sleep Talk.

## Focused Decisions

| Turn | Side | Branch found | Handoff/action found | Frozen action | Actual | Grade |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Zapdos attacks immediately. | Wrong: special receiver. | Switch receiver | Explosion into Zapdos | Miss |
| 1 | p2 | Forretress may stay, switch, or trade. | Active Thunder still covers enough. | Thunder | Thunder | Top |
| 3 | p1 | Cloyster Surf forces Flareon out. | Snorlax/special sponge handoff found. | Handoff | Switch Snorlax | Acceptable |
| 3 | p2 | Flareon must act or leave. | Surf is active punish. | Surf | Surf | Top |
| 5 | p1 | Cloyster may leave after Thunder reveal. | Not found: Golem receiver. | Thunder | Thunder into Golem | Miss |
| 6 | p1 | Golem pressures poisoned Snorlax. | Exeggutor handoff found and obeyed. | Switch Ground resist | Switch Exeggutor | Top |
| 7 | p1 | Golem likely leaves for a special receiver. | Branch action found by class. | Sleep/status or Psychic into receiver | Psychic into Raikou | Acceptable |
| 8 | p1 | Raikou can stay and Crunch. | Status beats the branch. | Sleep Powder | Sleep Powder | Top |
| 9 | p1 | Sleeping Raikou may switch or Sleep Talk. | Wrong handoff; I over-weighted switch-out. | Stay or pressure receiver | Switch Snorlax | Miss |
| 9 | p2 | Sleeping Raikou may be saved. | Wrong: switch-out over Sleep Talk. | Switch | Sleep Talk Crunch | Miss |
| 11 | p1 | Golem threatens poisoned Snorlax. | Wrong: handoff over coverage. | Switch Exeggutor | Surf | Miss |
| 12 | p1 | Low Snorlax cannot take Earthquake. | Exeggutor handoff found and obeyed. | Switch Exeggutor | Switch Exeggutor | Top |

## Reusable Lessons

- A found handoff is not automatically correct. If the active piece has a
  one-time trade that removes the route threat, cash-out may beat preservation.
- A sleeping Pokemon is often switched to preserve Sleep Clause value, but
  RestTalk changes the branch. If Sleep Talk is revealed or likely, price
  staying in before assuming the sleeper leaves.
- Coverage can be the branch action. Once Snorlax revealed Thunder, Golem was a
  live receiver; once Surf was revealed, staying into Golem became better than
  defaulting to the Grass handoff.
- Support or preservation is worse when it lets the branch keep initiative.

## Error Classes

- Handoff identity wrong: turn 1 Forretress, turn 5 Golem receiver, turn 9
  sleeping Raikou.
- Handoff found but wrong to obey: turn 11 Exeggutor handoff was worse than
  Snorlax Surf into Golem.
- No mechanics, hidden-info, state, or severe-blunder errors were scored.

## Next Rep

Make a four-scenario micro-probe from this transfer:

1. Support piece cashes out instead of preserving.
2. Revealed coverage beats a named receiver.
3. Sleeper stays with Sleep Talk instead of switching out.
4. Handoff is correct only after the active coverage or cash-out is priced.
