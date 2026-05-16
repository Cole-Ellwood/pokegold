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

Screen/drop sequence extension: Reflect, Light Screen, Screech, and Dynamic
Punch are often the first half of the route, not the completion. After the
screen, Defense drop, or confusion lands, immediately rank the physical
follow-up, Pursuit/phaze, spinblock/Spin branch, or handoff that the support
move enabled.

Damage-threshold follow-up extension: Curse, Reflect, Light Screen, paralysis,
and similar support may make the next route-converting action direct damage
rather than preservation. Before switching out after support succeeds, ask
whether the enabled attack puts the receiver into revenge, phaze, Explosion, or
hazard range. If it does, damage can be the handoff.

Status-sacrifice extension: a low support piece can spend itself on Thunder
Wave, Toxic, screen, or similar utility if that action names and enables the
next converter. Do not call the sacrifice positive because status landed; call
it positive only when the receiver, the follow-up Pokemon, and the next board
are explicit.

Seed/reset handoff extension: Leech Seed, Thief, Rest, and phazing are not
complete just because they happened. After one lands, name whether the next
board is seed reset, item-denial pressure, RestTalk receiver re-entry, phaze
loop, or immediate cash-out, then rank the move that preserves or converts that
specific board.

Rest-to-counter-pivot extension: after a wall uses Rest, do not assume the
sleeping wall is the next target. First ask whether it stays to burn sleep
turns, has Sleep Talk, or leaves to a counter-pivot before spending any sleep
turn. If it can switch out and a revealed coverage move hits that pivot, rank
the pivot punish before generic damage into the Rest user.

Scout-to-conversion extension: Protect, scouting, and status cures are only
useful if they change the next action. After scouting a switch or revealing
coverage, immediately rank the active follow-up before defaulting to a handoff.

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

- `workspace/quick_tests/replay_turn_pause_053_curselax_phaze_cashout_smogtours-gen2ou-922830_2026-05-14.md`
- `workspace/quick_tests/replay_turn_pause_054_hazard_loop_spin_window_smogtours-gen2ou-922676_2026-05-14.md`
- `workspace/quick_tests/replay_turn_pause_057_sleep_absorber_trade_handoff_smogtours-gen2ou-922568_2026-05-14.md`
- `workspace/quick_tests/replay_turn_pause_058_rest_sleeper_handoff_gen2ou-2595967411_2026-05-14.md`
- `workspace/quick_tests/rest_sleeper_handoff_probe_001_2026-05-14.md`
- `workspace/quick_tests/statused_spinner_handoff_probe_001_2026-05-14.md`
- `workspace/quick_tests/replay_turn_pause_077_spinner_control_transfer_smogtours-gen2ou-925730_2026-05-14.md`
- `workspace/quick_tests/paired_handoff_transfer_001_smogtours-gen2ou-920763_2026-05-14.md`
- `workspace/quick_tests/rest_sleeper_cleric_trade_probe_001_2026-05-14.md`
- `workspace/quick_tests/rest_sleeper_cleric_trade_transfer_001_smogtours-gen2ou-920770_2026-05-14.md`
- `workspace/quick_tests/screen_phaze_third_owner_probe_001_2026-05-14.md`
- `workspace/quick_tests/utility_screen_screech_transfer_001_gen2ou-2592987202_2026-05-15.md`
- `reviews/utility_screen_screech_review_001_2026-05-15.md`
- `workspace/quick_tests/status_setup_handoff_transfer_001_smogtours-gen2ou-934420_2026-05-15.md`
- `reviews/status_setup_handoff_review_001_2026-05-15.md`
- `workspace/quick_tests/leech_resttalk_phaze_transfer_001_smogtours-gen2ou-933839_2026-05-15.md`
- `reviews/leech_resttalk_phaze_review_001_2026-05-15.md`
- `workspace/quick_tests/spinblock_subgrowth_transfer_001_smogtours-gen2ou-932556_2026-05-15.md`
- `reviews/spinblock_subgrowth_review_001_2026-05-15.md`
- `workspace/quick_tests/ground_receiver_triangle_transfer_001_gen2ou-2591556155_2026-05-15.md`
- `reviews/ground_receiver_triangle_review_001_2026-05-15.md`

Drill:

Pause after a successful support turn and write: current route, converter,
opponent counter-pivot, worst branch, and next move if the opponent takes the
counter-pivot.
