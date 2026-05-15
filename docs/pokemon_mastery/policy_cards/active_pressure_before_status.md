# Policy Card: Active Pressure Before Status

Status: active boundary card.

Use when: a Pokemon with status, Explosion, or a pivot option also has a direct
damage, phaze, or pressure move that may already improve the route.

Trigger:

- A status-capable Pokemon can use Sleep Powder, Hypnosis, Toxic, Thunder Wave,
  or a similar move.
- A support piece can cash out with Explosion or switch to a generic answer.
- The active attack, phaze, or pressure line already threatens damage, switches,
  hazard conversion, or role preservation.
- A bulky attacker is repeatedly forcing the opponent into resist or support
  answers.

Default:

Price the active pressure line before choosing status, Explosion, or a pivot.
If direct damage, Roar/Whirlwind, or staying in already improves a named route,
do not switch to a status script just because the move exists. If the next hit
changes a support piece's future job, keep attacking until the opponent shows
the branch that flips the exchange.

Opposite boundary:

Choose status, Explosion, or the pivot when it changes a route that direct
pressure cannot: it stops setup, blocks recovery, denies a spinner, removes a
converter, creates Sleep Clause value, or preserves an irreplaceable piece.

Exceptions:

- If direct pressure only creates damage without a route, status may be the
  real converter.
- If the opponent has a clean absorber or counter-pivot, status may hand them
  the board.
- If the opponent's best branch is a switch you can name, compare one more hit
  to the counter-switch instead of attacking by inertia.
- If the support piece has no future entry or job, spending it may be correct.

Worst branch:

You see a status or Explosion button, press it automatically, and give up an
active route that was already forcing damage, switches, hazards, or recovery.

Local status:

Vanilla GSC policy source. Romhack status timing, move effects, immunities,
Explosion behavior, boss AI, and type passives require local verification when
decision-relevant.

Evidence:

- `quick_tests/replay_turn_pause_058_rest_sleeper_handoff_gen2ou-2595967411_2026-05-14.md`
- `quick_tests/replay_turn_pause_060_fixed_helper_phaze_transfer_smogtours-gen2ou-912658_2026-05-14.md`
- `quick_tests/active_pressure_status_script_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_061_active_pressure_transfer_smogtours-gen2ou-911263_2026-05-14.md`
- `quick_tests/active_damage_persistence_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_062_active_damage_branch_action_smogtours-gen2ou-911268_2026-05-14.md`
- `quick_tests/branch_action_after_naming_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_063_branch_action_transfer_smogtours-gen2ou-907828_2026-05-14.md`
- `quick_tests/branch_action_mixed_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_074_mixed_punish_transfer_gen2ou-2595957046_2026-05-14.md`
- `quick_tests/cashout_before_status_script_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_075_cashout_before_status_transfer_gen2ou-2595963523_2026-05-14.md`
- `quick_tests/one_time_trade_taxonomy_probe_001_2026-05-14.md`
- `quick_tests/counter_handoff_loop_probe_001_2026-05-14.md`
- `quick_tests/counter_handoff_loop_transfer_001_smogtours-gen2ou-921389_2026-05-14.md`
- `quick_tests/setup_hidden_role_stop_probe_001_2026-05-14.md`
- `quick_tests/setup_hidden_role_stop_transfer_001_smogtours-gen2ou-921412_2026-05-14.md`
- `quick_tests/screen_phaze_third_owner_probe_001_2026-05-14.md`

Drill:

Give four positions: attack before pivot, preserve support before Explosion,
phaze before damage, and direct damage or cash-out before sleep/status.
