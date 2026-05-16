# Candidate-Comparison Prompt Shape Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_012_gen2ou-2609886103_p2_2026-05-15.md`

Reason for study:
The second-ply counter-owner rule was present, but a fresh replay still failed
by turn 3. I obeyed a transaction line in form while choosing before explicitly
comparing the active target, next owner, and counter-owner.

## Sources Read

Local mastery docs:

- `live_core.md`
- `replay_turn_pause_protocol.md`
- `heuristic_core/name_next_board_owner.md`
- `heuristic_core/role_package_ledger.md`
- `heuristic_core/branch_punish_ranking.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `reviews/counter_owner_second_ply_review_001_2026-05-15.md`

Current web sources:

- Smogon Forums, An Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`
- Smogon Forums, GSC OU Jynx:
  `https://www.smogon.com/forums/threads/gsc-ou-jynx.3699576/`
- Smogon Forums, Jynx QC:
  `https://www.smogon.com/forums/threads/jynx-gsc-ou-qc-2-2-gp-2-2.3667481/`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums, GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

## Confirmed Lessons

Lead choices are not isolated move scripts. The GSC lead source emphasizes that
Cloyster has clear lead matchups and can guarantee Spikes against some leads
while being disadvantaged into others. That means turn-1 and turn-2 switches
are role signals, not noise.

Jynx's sleep threat is real, but it is conditional. The Jynx discussion
qualifies Lovely Kiss as strongest into slower Pokemon without Sleep Talk, and
the helper did not reconstruct unused Jynx moves. Future side-known scoring
must label own-move reconstruction gaps instead of treating missing own moves
as fully known.

Heracross into Starmie was not a completed route. Smogon threat material says
Skarmory is a major Heracross answer: it resists Megahorn and threatens
Heracross back. Therefore the turn after Heracross enters must solve the
Skarmory counter-owner before clicking Megahorn.

The training failure is prompt shape. A compact card saying "re-run one ply
deeper" did not force the model to do it. The replay helper now requires a
candidate comparison before final top action:

`active target -> next owner -> counter-owner after our handoff`

## Policy Correction

- `replay_turn_pause.py`: public and side-known prompts now require the
  candidate comparison before final top action.
- `test_replay_turn_pause.py`: unit test now checks that this prompt text is
  present.
- `replay_turn_pause_protocol.md`: freeze workflow now includes active/next/
  counter-owner candidate comparison.
- `live_core.md`: answer shape now says the top move comes after that
  comparison.
- `name_next_board_owner.md` and `role_package_ledger.md`: opening
  double-switches are explicitly treated as handoffs/role evidence.

## Measurement Note

Not progress. The failure happened too early for a sample claim, but it is
useful evidence that replay practice must be scaffolded by a stricter answer
shape, not just smaller docs.

