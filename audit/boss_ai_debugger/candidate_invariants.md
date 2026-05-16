# Boss AI Debugger Candidate Invariants

Status: candidate hypotheses. Promote a rule to a blocking audit only after review.

- candidates: `13`
- violations: `1`
- scenarios: `200`
- trace files: `19`
- runs: `2`

## Candidates

### `scenario.score_delta_direction`

- source: `scenario`
- support: `1478`
- violations: `0`
- description: Score deltas keep the ROM direction: negative encourages, positive discourages.
- examples: `generated_selector_edges_20260515_00000_blocked_best`, `generated_selector_edges_20260515_00000_blocked_best`, `generated_selector_edges_20260515_00000_blocked_best`, `generated_selector_edges_20260515_00000_blocked_best`, `generated_mastery_policy_20260515_00000_active_pressure_before_status`

### `scenario.selectable_score_bounds`

- source: `scenario`
- support: `800`
- violations: `0`
- description: Selectable scores stay in 1..79, and blocked scores stay at 80 or above.
- examples: `generated_selector_edges_20260515_00000_blocked_best`, `generated_selector_edges_20260515_00000_blocked_best`, `generated_selector_edges_20260515_00000_blocked_best`, `generated_selector_edges_20260515_00000_blocked_best`, `generated_mastery_policy_20260515_00000_active_pressure_before_status`

### `scenario.blocked_probability_zero`

- source: `scenario`
- support: `2`
- violations: `0`
- description: Actions with final score 80 or above have zero selector probability.
- examples: `generated_selector_edges_20260515_00000_blocked_best`, `generated_selector_edges_20260515_00008_blocked_best`

### `scenario.selector_probability_surface`

- source: `scenario`
- support: `200`
- violations: `0`
- description: The selector gives nonzero probability only to the best and first second-best actions.
- examples: `generated_selector_edges_20260515_00000_blocked_best`, `generated_mastery_policy_20260515_00000_active_pressure_before_status`, `generated_spikes_spin_20260515_00000`, `generated_mastery_policy_20260515_00001_branch_action_after_naming`, `generated_switch_sack_20260515_00000_preserve_wincon_over_comfort_damage`

### `scenario.pass_expected_probability_floor`

- source: `scenario`
- support: `145`
- violations: `0`
- description: Pass verdicts with expected best ids satisfy the configured probability floor.
- examples: `generated_selector_edges_20260515_00000_blocked_best`, `generated_mastery_policy_20260515_00000_active_pressure_before_status`, `generated_spikes_spin_20260515_00000`, `generated_mastery_policy_20260515_00001_branch_action_after_naming`, `generated_mastery_policy_20260515_00002_cashout_boundary`

### `scenario.pass_has_no_catastrophic_roll`

- source: `scenario`
- support: `145`
- violations: `0`
- description: Passing scenarios do not roll catastrophic actions.
- examples: `generated_selector_edges_20260515_00000_blocked_best`, `generated_mastery_policy_20260515_00000_active_pressure_before_status`, `generated_spikes_spin_20260515_00000`, `generated_mastery_policy_20260515_00001_branch_action_after_naming`, `generated_mastery_policy_20260515_00002_cashout_boundary`

### `trace.exact_selector_byte_shape`

- source: `trace`
- support: `19`
- violations: `0`
- description: Exact trace captures carry four move ids and four move score bytes.
- examples: `blaine_live#1`, `blue_live#1`, `brock_live#1`, `bugsy_live#1`, `champion_lance_live#1`

### `trace.chosen_slot_is_possible`

- source: `trace`
- support: `19`
- violations: `0`
- description: Exact matched captures choose a slot or move with nonzero selector probability.
- examples: `Blaine#1`, `Blue#1`, `Brock#1`, `Bugsy#1`, `Champion Lance#1`

### `trace.score_80_probability_zero`

- source: `trace`
- support: `0`
- violations: `0`
- description: Trace selector slots with score 80 or above have zero probability.

### `trace.possible_slots_limited_to_best_second`

- source: `trace`
- support: `19`
- violations: `0`
- description: Exact selector replay exposes at most two possible slots.
- examples: `Blaine#1`, `Blue#1`, `Brock#1`, `Bugsy#1`, `Champion Lance#1`

### `run_store.artifact_hashes_match`

- source: `run_store`
- support: `15`
- violations: `1`
- description: Run metadata artifact hashes match the written artifact files.
- examples: `20260515_121426_changed_ai:batch_report`, `20260515_121426_changed_ai:differential`, `20260515_121426_changed_ai:invariants`, `20260515_121426_changed_ai:live_trace_refresh`, `20260515_121426_changed_ai:metamorphic`

Violations:
- `20260515_121426_changed_ai:rom_contribution_traces`: artifact missing

### `run_store.batch_summary_matches_report`

- source: `run_store`
- support: `1`
- violations: `0`
- description: Run metadata batch summary agrees with batch_report.json.
- examples: `20260515_121426_changed_ai`

### `run_store.review_queue_matches_batch`

- source: `run_store`
- support: `1`
- violations: `0`
- description: Review queue input count agrees with batch reviewable count.
- examples: `20260515_121426_changed_ai`

## Known Limits

- Current traces expose selector bytes, not full scoring rule events.
- Candidate invariants are hypotheses until promoted to a dedicated audit.
