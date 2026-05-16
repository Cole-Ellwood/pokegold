# Counter-Owner Second-Ply Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_011_gen2ou-2609904983_p2_2026-05-15.md`

Reason for study:
The packet stayed clean on severe/hidden/state/mechanics gates, but turns
22-24 repeated the plateau pattern. I named the current owner or support job,
then stopped solving before the counter-owner that owner invited.

## Sources Read

Local mastery docs:

- `live_core.md`
- `heuristic_core/name_next_board_owner.md`
- `heuristic_core/branch_punish_ranking.md`
- `heuristic_core/converter_before_script.md`
- `heuristic_core/role_package_ledger.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `reviews/snorlax_forretress_counter_handoff_review_001_2026-05-15.md`

Current web sources:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums, Vaporeon Update:
  `https://www.smogon.com/forums/threads/vaporeon-update-qc-2-2-gp-2-2.3470544/`
- Smogon Forums, GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

## Confirmed Lessons

Forretress is not just passive filler after it enters. Current Smogon material
still describes it as a compressed Spikes/Spin support piece that often lacks
direct offensive pressure. The right response is to name which teammate takes
the support board and which counter-handoff follows, not simply to hit the
sprite on screen.

Spikes plus paralysis and forced switches are a real conversion route in GSC.
If a status or support action does not change the next forced switch, it is
not positive selection just because it is normally useful.

Vaporeon has a specific branch map. Smogon Vaporeon material says to use the
Water STAB when predicting an Electric-type switch and Growth when expecting
Snorlax. In the failed turn 24 position, Raikou was public and already chipped;
Hydro Pump into the Electric counter-owner converted much more than Growth into
the old Snorlax board.

No-Team-Preview discipline remains intact. The fix is not "assume hidden
Raikou." The fix is: when Raikou is public or an Electric owner is a strong
prior, label that owner class and choose the move that beats it, with fallback
if the active Pokemon stays.

## Policy Correction

Patch the compact live structure, not the archive:

- `live_core.md`: next-board owner now includes the counter-owner invited after
  handoff.
- `name_next_board_owner.md`: after a support job or owner handoff succeeds,
  re-run the transaction one ply deeper.
- `branch_punish_ranking.md`: generic status/setup is not branch punish unless
  it beats the named next owner or counter-owner.
- `converter_before_script.md`: status/setup only count as converters if they
  beat both the active target and the named next owner/counter-owner.
- `role_package_ledger.md`: "counter-handoff is not automatic" now keeps the
  hidden-info gate while allowing promotion when the class is public enough and
  the active action only beats the old board.

## Measurement Note

This is a repair after a flat/regressing transfer, not a progress claim. The
next proof must be a fresh side-known packet where the second-ply transaction
is frozen before ranked candidates.

