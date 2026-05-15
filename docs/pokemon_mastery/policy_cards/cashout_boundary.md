# Policy Card: Cash-Out Boundary

Status: active boundary card.

Use when: a low or one-time support piece can either preserve a future job or
spend itself now through Explosion, sacrifice, aggressive status, or a damaging
trade.

Trigger:

- A support piece is low, statused, or hard to re-enter.
- The active move can open a concrete converter, not just create damage.
- Preserving the piece may retain Spikes, phazing, sleep absorption, pivoting,
  boom pressure, or a needed check.

Default:

Name the support job before spending the piece. Preserve if the job is still
route-defining and no immediate converter appears. If you explicitly name an
Explosion or Self-Destruct branch, the recommendation must also name the
absorber, sack, immunity, or reason staying still preserves the route.

Defending mirror: before attacking a low self-KO candidate with a valuable
active, name speed/order, whether the active survives with its route job, and
the lower-value owner that absorbs or resists the trade. If the self-KO moves
first or the active does not survive usefully, prefer the owner unless active
pressure or coverage wins a concrete route immediately.

Route-defining gate: self-KO leads only when the prior support job is delivered
or irrelevant, the target and post-trade converter are named, delay lets that
target reset or escape, and no revealed or cheap absorber covers the trade. If
support is not delivered yet, the target is not exact, or active pressure /
coverage improves the branch without spending the piece, treat self-KO as a
branch rather than the main line.

Full-health active-pressure boundary: do not promote Explosion or Self-Destruct
from possible to primary just because the species can cash out. If the user is
healthy and still has coverage, status, or pivot pressure that improves the
route, price that active pressure before spending it.

Low-HP Rest race: before spending a low route piece with recoil, Explosion,
Self-Destruct, or a likely last attack into a low bulky target, price whether
the target can Rest before the hit. If the faster target can heal first, the
attack may become a self-KO or bad cash-out into a preserved route piece.

Opposite boundary:

Cash out immediately when the trade opens a named converter or removes the
blocker that slow play cannot beat. Do not overcorrect from "do not auto-boom"
into refusing the one trade that creates the route.

Exceptions:

- If the piece has no realistic entry path, its future job may be imaginary.
- If the opponent's worst branch turns the preserved piece into a free setup or
  Spin window, preservation may be worse than spending.
- If the current position is losing slowly, accept a concrete high-variance
  converter over passive preservation.

Worst branch:

You preserve a famous or sentimental piece, lose the current converter window,
and later discover the preserved piece had no safe entry or no remaining job.
The opposite severe branch is naming the boom, leaving the route piece in by
habit, and losing the route on the forced revenge turn.

Local status:

Vanilla GSC policy source. Romhack Explosion, type passives, Ghost immunity,
items, and AI behavior require local status before live boss claims.

Evidence:

- `quick_tests/replay_turn_pause_055_low_cloyster_preserve_ghost_pivot_smogtours-gen2ou-922579_2026-05-14.md`
- `quick_tests/low_support_preserve_before_cashout_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_056_immediate_route_trade_converter_smogtours-gen2ou-922569_2026-05-14.md`
- `quick_tests/cashout_boundary_converter_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_058_rest_sleeper_handoff_gen2ou-2595967411_2026-05-14.md`
- `quick_tests/rest_sleeper_handoff_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_060_fixed_helper_phaze_transfer_smogtours-gen2ou-912658_2026-05-14.md`
- `quick_tests/replay_turn_pause_061_active_pressure_transfer_smogtours-gen2ou-911263_2026-05-14.md`
- `quick_tests/active_damage_persistence_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_062_active_damage_branch_action_smogtours-gen2ou-911268_2026-05-14.md`
- `quick_tests/branch_action_after_naming_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_063_branch_action_transfer_smogtours-gen2ou-907828_2026-05-14.md`
- `quick_tests/branch_action_mixed_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_064_branch_action_restatement_smogtours-gen2ou-907834_2026-05-14.md`
- `quick_tests/preservation_boundary_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_065_preservation_transfer_smogtours-gen2ou-920439_2026-05-14.md`
- `quick_tests/replay_turn_pause_068_support_action_transfer_smogtours-gen2ou-913236_2026-05-14.md`
- `quick_tests/setup_phaze_support_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_070_sleeper_spinner_immunity_transfer_gen2ou-2568188099_2026-05-14.md`
- `quick_tests/self_ko_absorber_transfer_001_smogtours-gen2ou-921984_2026-05-14.md`
- `quick_tests/replay_turn_pause_071_cashout_branch_transfer_smogtours-gen2ou-921983_2026-05-14.md`
- `quick_tests/replay_turn_pause_074_mixed_punish_transfer_gen2ou-2595957046_2026-05-14.md`
- `quick_tests/cashout_before_status_script_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_075_cashout_before_status_transfer_gen2ou-2595963523_2026-05-14.md`
- `quick_tests/one_time_trade_taxonomy_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_076_one_time_trade_transfer_smogtours-gen2ou-924513_2026-05-14.md`
- `quick_tests/spinner_removed_hazard_cashout_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_077_spinner_control_transfer_smogtours-gen2ou-925730_2026-05-14.md`
- `quick_tests/replay_turn_pause_078_branch_counter_switch_transfer_smogtours-gen2ou-925823_2026-05-14.md`
- `quick_tests/branch_action_focus_002_gen2ou-2595974016_2026-05-14.md`
- `quick_tests/branch_handoff_transfer_001_smogtours-gen2ou-914170_2026-05-14.md`
- `quick_tests/branch_cashout_coverage_sleeptalk_probe_001_2026-05-14.md`
- `quick_tests/branch_cashout_coverage_sleeptalk_transfer_001_smogtours-gen2ou-914172_2026-05-14.md`
- `quick_tests/setup_coverage_sleeptalk_handoff_probe_001_2026-05-14.md`
- `quick_tests/paired_handoff_transfer_001_smogtours-gen2ou-920763_2026-05-14.md`
- `quick_tests/rest_sleeper_cleric_trade_transfer_001_smogtours-gen2ou-920770_2026-05-14.md`
- `quick_tests/ghost_electric_trap_phaze_transfer_001_smogtours-gen2ou-920777_2026-05-14.md`
- `quick_tests/low_self_ko_defensive_owner_probe_001_2026-05-14.md`
- `quick_tests/low_self_ko_transfer_001_smogtours-gen2ou-831843_2026-05-14.md`
- `reviews/low_self_ko_review_001_smogtours-gen2ou-831843_2026-05-14.md`
- `quick_tests/low_self_ko_transfer_002_smogtours-gen2ou-831951_2026-05-14.md`
- `quick_tests/low_rest_race_cashout_probe_001_2026-05-14.md`
- `quick_tests/low_rest_race_transfer_001_gen2ou-2544449982_2026-05-14.md`
- `reviews/low_rest_race_review_001_gen2ou-2544449982_2026-05-14.md`

Drill:

Give two positions with the same low support piece: one where it must preserve
its route job, and one where it must cash out because a concrete converter is
ready.
