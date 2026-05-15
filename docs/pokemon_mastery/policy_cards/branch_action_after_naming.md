# Policy Card: Branch Action After Naming

Status: active boundary card.

Use when: the opponent is likely to switch, reveal coverage, use a support
piece, or punish the current active matchup.

Trigger:

- You can name a likely receiver, absorber, hard answer, or support branch.
- The tempting move only improves the visible active matchup.
- A revealed move or set detail changes which action beats the branch.
- The active KO or active trade looks obvious, but the opponent can deny it by
  moving a receiver or sack into the line.

Default:

After naming the branch, name the action that beats that branch. Choose
counter-switch, coverage, phaze, Reflect, Toxic, Screech, setup, status,
Explosion, or sacrifice only if that action beats the named receiver or punish.

Substitute/setup extension: if the expected branch is an immunity or hard
receiver, rank Substitute or setup beside coverage and counter-handoff. It can
be the positive-selection action when it keeps the active route while exposing
or punishing the receiver.

Counter-handoff extension: when the current active is likely to leave, name the
next board and our owner for that board. If that owner enters safely and
creates immediate progress, the top action is usually the handoff rather than
damage into the Pokemon that is about to leave.

Status-absorber extension: when the named branch is a sleep or status absorber,
do not keep the status move on top by habit. Re-rank cash-out, coverage,
counter-switch, setup, or Substitute into that absorber before choosing the
original status move.

Sleep-clause absorber extension: when the opponent already has a sleeping
RestTalk or otherwise useful sleeping piece, price the switch that brings it
back in to blank further sleep attempts and preserve sleep-clause value. Choose
status only if it still improves through that absorber.

Cash-out immunity guard: before Explosion, self-sacrifice, or an all-in trade,
name revealed immunities and the legal hidden immunity class that would blank
the trade in no-Team-Preview play. If the trade spends an irreplaceable piece
and loses to a plausible immunity branch, prefer pressure, setup, phaze,
coverage, or a handoff unless the line is explicitly marked as a high-risk
read.

Handoff boundary: before switching, compare active pressure, coverage/status/
phaze/setup into the expected branch, and the handoff. If the current move
already affects the next board after switch cost, Spikes damage, recoil, and
information loss are priced, it can beat the handoff.

Opposite boundary:

Do not overread every possible switch. If the active punish is still the best
branch, or if the receiver takes route-changing damage from the active move,
keep pressure instead of making a speculative double.

Exceptions:

- Spectator-public hidden bench may make the exact counter-switch unknowable;
  score by class when the route action is correct.
- Setup is correct when the expected receiver cannot reset the route or when
  the boost changes the next board more than meeting the receiver now.
- If a set reveal changes the role, re-solve instead of importing the standard
  species job.
- If the active move already improves through the expected receiver, do not
  hand off just to look predictive.

Worst branch:

You correctly say "they switch to the answer," then choose a move that only
beats the Pokemon currently on screen and hand the opponent the board.

Local status:

Vanilla GSC policy source. Romhack role, type, move, item, AI, and timing
claims need local evidence when decision-relevant.

Evidence:

- `quick_tests/replay_turn_pause_062_active_damage_branch_action_smogtours-gen2ou-911268_2026-05-14.md`
- `quick_tests/branch_action_after_naming_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_063_branch_action_transfer_smogtours-gen2ou-907828_2026-05-14.md`
- `quick_tests/branch_action_mixed_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_064_branch_action_restatement_smogtours-gen2ou-907834_2026-05-14.md`
- `quick_tests/replay_turn_pause_065_preservation_transfer_smogtours-gen2ou-920439_2026-05-14.md`
- `quick_tests/branch_action_coverage_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_066_branch_action_transfer_smogtours-gen2ou-920441_2026-05-14.md`
- `quick_tests/hidden_role_branch_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_067_hidden_role_transfer_smogtours-gen2ou-912841_2026-05-14.md`
- `quick_tests/support_action_branch_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_068_support_action_transfer_smogtours-gen2ou-913236_2026-05-14.md`
- `quick_tests/setup_phaze_support_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_069_support_action_transfer_smogtours-gen2ou-917918_2026-05-14.md`
- `quick_tests/sleeper_spinner_immunity_branch_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_070_sleeper_spinner_immunity_transfer_gen2ou-2568188099_2026-05-14.md`
- `quick_tests/replay_turn_pause_071_cashout_branch_transfer_smogtours-gen2ou-921983_2026-05-14.md`
- `quick_tests/baton_pass_receiver_branch_probe_001_2026-05-14.md`
- `quick_tests/receiver_pivot_branch_transfer_001_smogtours-gen2ou-913242_2026-05-14.md`
- `quick_tests/replay_turn_pause_072_branch_action_full_transfer_smogtours-gen2ou-917932_2026-05-14.md`
- `quick_tests/mixed_receiver_action_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_073_mixed_receiver_action_transfer_smogtours-gen2ou-917839_2026-05-14.md`
- `quick_tests/mixed_punish_class_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_074_mixed_punish_transfer_gen2ou-2595957046_2026-05-14.md`
- `quick_tests/replay_turn_pause_075_cashout_before_status_transfer_gen2ou-2595963523_2026-05-14.md`
- `quick_tests/one_time_trade_taxonomy_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_076_one_time_trade_transfer_smogtours-gen2ou-924513_2026-05-14.md`
- `quick_tests/spinner_removed_hazard_cashout_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_078_branch_counter_switch_transfer_smogtours-gen2ou-925823_2026-05-14.md`
- `quick_tests/branch_counter_switch_transfer_002_smogtours-gen2ou-914596_2026-05-14.md`
- `quick_tests/branch_absorber_punish_probe_001_2026-05-14.md`
- `quick_tests/branch_absorber_transfer_001_smogtours-gen2ou-912287_2026-05-14.md`
- `quick_tests/cashout_immunity_guard_probe_001_2026-05-14.md`
- `quick_tests/cashout_immunity_transfer_001_smogtours-gen2ou-912827_2026-05-14.md`
- `quick_tests/branch_action_focus_002_gen2ou-2595974016_2026-05-14.md`
- `quick_tests/branch_action_gate_001_smogtours-gen2ou-909834_2026-05-14.md`
- `quick_tests/branch_action_gate_002_smogtours-gen2ou-910025_2026-05-14.md`
- `quick_tests/branch_action_gate_003_smogtours-gen2ou-913366_2026-05-14.md`
- `quick_tests/branch_handoff_obedience_probe_001_2026-05-14.md`
- `quick_tests/branch_handoff_transfer_001_smogtours-gen2ou-914170_2026-05-14.md`
- `quick_tests/branch_cashout_coverage_sleeptalk_probe_001_2026-05-14.md`
- `quick_tests/branch_cashout_coverage_sleeptalk_transfer_001_smogtours-gen2ou-914172_2026-05-14.md`
- `quick_tests/setup_coverage_sleeptalk_handoff_probe_001_2026-05-14.md`
- `quick_tests/setup_coverage_sleeptalk_handoff_transfer_001_smogtours-gen2ou-914178_2026-05-14.md`
- `quick_tests/paired_handoff_probe_001_2026-05-14.md`
- `quick_tests/paired_handoff_transfer_001_smogtours-gen2ou-920763_2026-05-14.md`
- `quick_tests/rest_sleeper_cleric_trade_probe_001_2026-05-14.md`
- `quick_tests/rest_sleeper_cleric_trade_transfer_001_smogtours-gen2ou-920770_2026-05-14.md`
- `quick_tests/ghost_electric_trap_phaze_transfer_001_smogtours-gen2ou-920777_2026-05-14.md`
- `quick_tests/electric_receiver_resttalk_transfer_001_smogtours-gen2ou-920928_2026-05-14.md`
- `quick_tests/resttalk_hidden_role_correction_probe_001_2026-05-14.md`
- `quick_tests/hidden_role_electric_transfer_001_smogtours-gen2ou-920951_2026-05-14.md`
- `quick_tests/hidden_role_electric_transfer_002_smogtours-gen2ou-920961_2026-05-14.md`
- `quick_tests/support_set_hidden_role_probe_001_2026-05-14.md`
- `quick_tests/support_set_hidden_role_transfer_001_smogtours-gen2ou-921372_2026-05-14.md`
- `quick_tests/counter_handoff_loop_probe_001_2026-05-14.md`
- `quick_tests/counter_handoff_loop_transfer_001_smogtours-gen2ou-921389_2026-05-14.md`
- `quick_tests/setup_hidden_role_stop_probe_001_2026-05-14.md`
- `quick_tests/setup_hidden_role_stop_transfer_001_smogtours-gen2ou-921412_2026-05-14.md`
- `quick_tests/screen_phaze_third_owner_probe_001_2026-05-14.md`
- `reviews/counter_handoff_review_001_smogtours-gen2ou-907837_2026-05-14.md`
- `quick_tests/positive_selection_transfer_003_smogtours-gen2ou-828683_2026-05-14.md`
- `quick_tests/low_rest_race_transfer_001_gen2ou-2544449982_2026-05-14.md`
- `reviews/low_rest_race_review_001_gen2ou-2544449982_2026-05-14.md`

Drill:

Give four positions where the same visible active matchup has different correct
actions: immediate active punish, counter-switch to receiver, coverage into
receiver, and setup because the receiver cannot reset the route.
