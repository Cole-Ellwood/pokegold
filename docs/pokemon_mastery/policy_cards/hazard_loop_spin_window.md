# Policy Card: Hazard Loop Spin Window

Status: active boundary card.

Use when: Spikes, Rapid Spin, spinblocking, or post-support handoff determines
whether hazard progress is real.

Trigger:

- Spikes can be set, retained, removed, or converted.
- Rapid Spin or a spinner entry path is live.
- The current move looks like generic progress but may create a Spin window.

Default:

Treat Spikes as a route subgame. Ask whether the line sets, retains, removes,
punishes Spin, or converts the entry map. Hazard progress is not real if the
opponent can remove it without giving up a route-relevant cost.

Hazard job ordering: before choosing Rapid Spin, ask whether the hazard piece
can set missing Spikes on the opponent's side right now. If one side is
unspiked and the setter is already active, setting the missing Spikes may beat
clearing owned-side Spikes.

Setup-threat boundary: if a boosted or immediately boosting Pokemon is already
converting, status, phazing, or cash-out may outrank both setting missing
Spikes and clearing owned-side Spikes.

Post-Spin reset check: after a successful Rapid Spin, immediately ask whether
the opposing setter is active, alive, and free to reset Spikes. Clearing hazards
is not stable progress if the setter can restore them before paying a real
route cost.

Opposite boundary:

Do not overprotect Spikes when the route has shifted. If the opponent must spin
through a losing trade, or if direct cash-out opens the converter now, take the
conversion.

Exceptions:

- A spinner without an entry path is not an immediate Spin threat.
- A spinblocker without a safe entry is not real coverage.
- If the spinner is already status-controlled and the setter still has a
  future entry/job, hand off to pressure before resetting or spending by habit.
- If the setter is already active after Spin, resetting Spikes may be the best
  immediate job even while status-controlled.
- If the setter is already active before Spin and the opponent's side is
  unspiked, setting Spikes may be the best immediate job before any clear.
- If a setup threat is already live, stop the route first; hazard work is only
  top if the threat cannot convert through it.
- If a support piece has just done its job, identify the counter-pivot before
  assuming the hazard loop is stable.

Worst branch:

You call setting Spikes progress, give the opponent a free spinner sequence,
and lose both hazard pressure and tempo.

Local status:

Vanilla GSC has one Spikes layer. In this romhack, Spikes layer count and the
successful Rapid Spin hazard-clear command clearing all layers are
`runtime_verified` in the local mechanics index. Exact text, PP, full switch-in
damage timing, Rapid Spin failure boundaries, and same-turn interactions remain
`unknown` unless the current answer cites a fixture or trace.

Evidence:

- `quick_tests/replay_turn_pause_054_hazard_loop_spin_window_smogtours-gen2ou-922676_2026-05-14.md`
- `quick_tests/hazard_loop_spin_window_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_059_rest_phaze_status_smogtours-gen2ou-888483_2026-05-14.md`
- `quick_tests/phaze_loop_rest_timing_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_060_fixed_helper_phaze_transfer_smogtours-gen2ou-912658_2026-05-14.md`
- `quick_tests/replay_turn_pause_064_branch_action_restatement_smogtours-gen2ou-907834_2026-05-14.md`
- `quick_tests/preservation_boundary_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_065_preservation_transfer_smogtours-gen2ou-920439_2026-05-14.md`
- `quick_tests/replay_turn_pause_066_branch_action_transfer_smogtours-gen2ou-920441_2026-05-14.md`
- `quick_tests/hidden_role_branch_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_067_hidden_role_transfer_smogtours-gen2ou-912841_2026-05-14.md`
- `quick_tests/support_action_branch_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_068_support_action_transfer_smogtours-gen2ou-913236_2026-05-14.md`
- `quick_tests/setup_phaze_support_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_069_support_action_transfer_smogtours-gen2ou-917918_2026-05-14.md`
- `quick_tests/sleeper_spinner_immunity_branch_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_070_sleeper_spinner_immunity_transfer_gen2ou-2568188099_2026-05-14.md`
- `quick_tests/replay_turn_pause_076_one_time_trade_transfer_smogtours-gen2ou-924513_2026-05-14.md`
- `quick_tests/spinner_removed_hazard_cashout_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_077_spinner_control_transfer_smogtours-gen2ou-925730_2026-05-14.md`
- `quick_tests/three_check_transfer_001_gen2ou-2544443857_2026-05-14.md`
- `reviews/hazard_ownership_review_001_gen2ou-2544443857_2026-05-14.md`
- `quick_tests/hazard_ownership_transfer_001_smogtours-gen2ou-906382_2026-05-14.md`
- `quick_tests/cloyster_hazard_job_transfer_001_smogtours-gen2ou-916513_2026-05-14.md`
- `romhack_deltas/spikes_and_rapid_spin.md`
- `mechanics_fixtures/spikes_rapid_spin/README.md`

Drill:

Give one turn where setting Spikes is correct, one where blocking Spin is
correct, one where cashing out beats the spinner, and one where the spinner has
no entry path.
