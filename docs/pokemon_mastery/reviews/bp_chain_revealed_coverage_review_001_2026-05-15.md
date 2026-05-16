# BP Chain/Revealed Coverage Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/bp_chain_revealed_coverage_transfer_001_smogtours-gen2ou-933681_2026-05-15.md`

Reason for study:
The fresh transfer was imperfect. It improved acceptable and positive-selection
metrics, but top-match and route conversion did not improve. The main lesson is
positive move selection against compound Baton Pass and revealed lure coverage:
deny the receiver, carry the boost ledger, and re-rank revealed coverage before
generic preservation.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/active_pressure_before_status.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `policy_cards/cashout_boundary.md`
- `reviews/pass_package_sleeper_handoff_review_001_2026-05-15.md`
- `reviews/status_setup_handoff_review_001_2026-05-15.md`
- `reviews/ground_receiver_triangle_review_001_2026-05-15.md`
- `reviews/curselax_forretress_timer_review_001_2026-05-15.md`
- `reviews/2026-05-13_smogtours-gen2ou-604744.md`

Current web sources:

- Smogon GSC Baton Pass:
  `https://www.smogon.com/forums/threads/gsc-bp.3541165/`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon Marowak Revamp:
  `https://www.smogon.com/forums/threads/marowak-revamp-qc-3-2-gp-2-2.3481449/`
- Smogon Snorlax Update:
  `https://www.smogon.com/forums/threads/snorlax-update-qc-2-2-gp-2-2-finished.3467216/`
- Smogon GSC OU Starmie:
  `https://www.smogon.com/forums/threads/gsc-ou-starmie.3692223/`

## Source-To-Policy Extraction

Smeargle support is receiver-first after Agility:
Smogon BP material frames Smeargle as a speed passer whose Spore threat forces
defensive waste even when Spore is not clicked. The local miss was ranking
Spore first after Agility stayed public. Once the speed pass is live, the next
question is "which receiver becomes unanswerable if this pass lands?"

Full BP in GSC is fragile but punishing:
Smogon sample-team material says GSC full BP is disruptable by phazing, but a
single misplay can decide the game. That maps directly to turns 4-11: Vaporeon
used Acid Armor/Roar/Baton Pass, Snorlax used Belly Drum, Starmie used Reflect,
and Tyranitar Roared. The answer cannot stop at "use phazer"; it must preserve
the phazer, spend damage when needed, and carry the passed boosts until they
are actually erased.

Reflect is the first half of the emergency line:
The Starmie source supports Surf as a real offensive move, not only spinner
filler. In this replay Reflect let Starmie survive one DrumLax hit, but Recover
did not improve the route enough; Surf put Snorlax into the range where
Tyranitar could take Earthquake and Roar it away. The lesson is not "always
sack Starmie," but "after the screen lands, ask which follow-up makes the next
denial turn work."

Marowak coverage is the branch map:
Smogon Marowak material emphasizes Earthquake plus Rock Slide and the need for
support because Marowak is slow and frail but extremely punishing when the
support sticks. The transfer miss repeated the old receiver-triangle problem:
after SurfLax made Marowak low, I kept Earthquake as the top Marowak action
even though Zapdos was the named preservation branch. Rock Slide had to remain
ranked as the branch-punish.

SurfLax is a reveal, not a species prior:
Snorlax sources center Curse, Belly Drum, Rest, Normal STAB, Lovely Kiss, and
coverage; Surf is not a default move to assume. The policy correction is tier
discipline on both sides. Before turn 22, SurfLax should not be used as the
main reason to stay in. After turn 22, Surf is revealed and must outrank
generic Snorlax assumptions into Marowak boards.

## Policy Updates Made

- `active_pressure_before_status.md`: tightened Smeargle support-lead wording
  so Agility makes Baton Pass and receiver denial rise beside Spore.
- `branch_action_after_naming.md`: added compound Baton Pass boost-ledger and
  revealed-lure coverage wording.
- `active_context.md`: pointed the next rep at compound Baton Pass ledgering,
  SurfLax/revealed lure discipline, and Marowak Rock Slide branch coverage.

## Measurement Note

Mixed but not progress. Compared with `curselax_forretress_timer_transfer_001`,
this run improved acceptable from 31/45 to 32/44, positive-selection from 36/45
to 38/44, hidden-info from 1 to 0, and branch percentage from 15/36 to 18/36.
Top-match fell from 16/45 to 15/44 and route conversion fell from 33/45 to
30/44. Under the active gate, this is a useful study block, not evidence of
real improvement.

## Next Rep

No new replay until the next work block starts again from `active_context.md`.
The next unseen work should force:

- Smeargle after Agility, where Spore and Baton Pass are both live;
- Vaporeon/Scizor/Jolteon pass nodes with phaze pressure;
- screen or status support followed by the concrete route-converting move;
- revealed lure coverage into Marowak, Zapdos, or Cloyster receiver branches.
