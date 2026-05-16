# Rest/Phaze Prompt Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_017_gen2ou-2609050174_p1_2026-05-15.md`

Reason for study:
Turn 12 missed Tyranitar Roar after low Snorlax used Rest. The rule existed in
`reset_loop_denial.md`, but the live prompt did not force that comparison
before active damage.

## Sources Read

Local docs:

- `live_core.md`
- `heuristic_core/reset_loop_denial.md`
- `docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_017_gen2ou-2609050174_p1_2026-05-15.md`
- `docs/pokemon_mastery/reviews/post_typed_repair_sample_review_001_2026-05-15.md`

Current web sources:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon, Introduction to Competitive GSC:
  `https://www.smogon.com/smog/issue28/gsc`
- Smogon Forums, GSC Mechanics:
  `https://www.smogon.com/forums/threads/gsc-mechanics.3542417/`

## Confirmed Lessons

Smogon GSC mechanics material states that Roar and Whirlwind need to move last
to work in GSC. That means a slower phazer can still phaze after the target
uses Rest if it survives the turn.

Smogon Spikes material treats phazing as a way to convert forced switches and
Rest windows into progress. If a low Snorlax is likely to Rest, the live
question is not "which attack is safe," but whether phaze, pressure, Pursuit,
Toxic, setup, or a handoff converts the sleep window immediately.

## Policy Correction

- `replay_turn_pause.py`: prompts now require reset-denial comparison before
  damage when Rest, Recover, Spikes, Spin, phaze, or Sleep Talk can reset the
  route.
- `test_replay_turn_pause.py`: unit test now checks that prompt requirement.
- `reset_loop_denial.md`: added the Rest-before-negative-priority-phaze case.

## Measurement Note

This is a prompt-shape repair, not progress. The next proof must come from
fresh replay turns where reset-denial is promoted without over-phazing.

