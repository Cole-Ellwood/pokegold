# Policy Card: Support Handoff After Job

Status: active boundary card.

Use when: a support move, phaze, status, hazard, scout, or lure has just landed
and the next turn decides whether the route converts.

Trigger:

- A support action succeeded.
- The original plan assumed that success was enough.
- The opponent has a counter-pivot, Spin, Rest, Explosion, setup, phaze, or
  double-switch branch that can erase the progress.

Default:

After support lands, immediately name the next board. Identify the converter,
the opponent's best counter-pivot, and the resource that must be preserved for
the handoff.

Opposite boundary:

Sometimes the correct handoff is not preservation. If the support piece has
completed its unique job and the converter window is open, spend or switch it
according to the route instead of taking another safe-looking support action.

Exceptions:

- If the support move revealed new set information, re-solve before following
  the old handoff.
- If the converter has no entry path, the handoff is not live.
- If the opponent's worst branch is immediate setup, recovery, Spin, or
  Explosion, cover that branch before polishing the route.
- If the support piece is likely to be removed this turn, take the unique
  support action first when it changes the route.

Worst branch:

You celebrate the support action, miss the counter-pivot, and let the opponent
erase the route before the converter enters.

Local status:

Vanilla GSC policy source. Local boss AI information limits and mechanics
interactions require the public-information policy and local evidence.

Evidence:

- `quick_tests/replay_turn_pause_053_curselax_phaze_cashout_smogtours-gen2ou-922830_2026-05-14.md`
- `quick_tests/replay_turn_pause_054_hazard_loop_spin_window_smogtours-gen2ou-922676_2026-05-14.md`
- `quick_tests/replay_turn_pause_057_sleep_absorber_trade_handoff_smogtours-gen2ou-922568_2026-05-14.md`
- `quick_tests/replay_turn_pause_058_rest_sleeper_handoff_gen2ou-2595967411_2026-05-14.md`
- `quick_tests/rest_sleeper_handoff_probe_001_2026-05-14.md`
- `quick_tests/statused_spinner_handoff_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_077_spinner_control_transfer_smogtours-gen2ou-925730_2026-05-14.md`
- `quick_tests/paired_handoff_transfer_001_smogtours-gen2ou-920763_2026-05-14.md`
- `quick_tests/rest_sleeper_cleric_trade_probe_001_2026-05-14.md`
- `quick_tests/rest_sleeper_cleric_trade_transfer_001_smogtours-gen2ou-920770_2026-05-14.md`
- `quick_tests/screen_phaze_third_owner_probe_001_2026-05-14.md`

Drill:

Pause after a successful support turn and write: current route, converter,
opponent counter-pivot, worst branch, and next move if the opponent takes the
counter-pivot.
