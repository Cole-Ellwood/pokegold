# Boss AI Preference Schema

Fixtures live in `fixtures/boss_ai_preference_fixtures.json`.

Top-level shape:

```json
{
  "schema_version": 1,
  "fixtures": []
}
```

Each fixture requires:

- `id`: stable unique id.
- `leader`: boss name shown in the tool.
- `state`: public battle state object.
- `actions`: legal boss actions the user can label.

The source fixture JSON does not need damage fields. The local server adds
optional `damage_estimate` display metadata to attacking actions returned by
`/api/fixtures`.

The server also adds optional `incoming_threats` metadata to each fixture. These
records are review hints derived from public fixture state plus ROM source data:

```json
{
  "species": "Quilava",
  "move": "Ember",
  "move_id": "EMBER",
  "bucket": "99%",
  "likelihood": 99,
  "sources": ["level_up", "revealed"],
  "reasons": ["revealed in the public fixture state"],
  "immediacy": "active",
  "severity": "meaningful",
  "switch_fit": null,
  "entry_risk": null,
  "damage": {
    "label": "about 45-54%",
    "low_percent": 45,
    "high_percent": 54
  }
}
```

Likelihood buckets are deliberately coarse:

- `99%`: revealed or forced by public fixture evidence.
- `75%`: natural STAB/core level-up move.
- `50%`: natural non-STAB level-up move, pre-evo move, or direct TM access.
- `25%`: legal but optional, low-confidence, or otherwise limited.
- `0%`: unavailable or blocked by a four-revealed-move set.

Common source tags include `revealed`, `level_up`, `pre_evo_level_up`,
`tm_available`, `grass_encounter`, `surf_encounter`, `old_rod_fishing`,
`good_rod_fishing`, `super_rod_fishing`, `gift_or_prize:*`, and
`static_encounter:*`.

For seen-party switch threats, `switch_fit` is separate from move likelihood.
It is `reasonable`, `risky`, `bad`, or `unknown` based on revealed boss damage
into the switch candidate. Bad switch-ins are suppressed from the default UI
unless their outgoing threat is major or lethal.

Fixture state must only contain public information:

- visible species, level, HP band, status, held item if known
- revealed moves
- public priors such as common learnable coverage
- seen party members
- field state visible to the player

Pairwise preference records are JSONL rows in
`labels/boss_ai_pairwise_preferences.jsonl` by default:

```json
{
  "fixture_id": "bugsy_scyther_vs_quilava_fire_pressure",
  "state_version": 1,
  "action_a_id": "move_swords_dance",
  "action_b_id": "move_wing_attack",
  "choice": "b_better",
  "preferred_action_id": "move_wing_attack",
  "confidence": "high",
  "public_info_scope": "public_only",
  "lesson_type": "weight_hint",
  "condition_tags": ["target_can_punish", "threat_revealed"],
  "holdout": false,
  "reason_tags": [],
  "action_tags": {
    "move_swords_dance": ["too_greedy", "misses_public_threat"],
    "move_wing_attack": ["uses_public_info", "keeps_tempo"]
  },
  "note": "Fire pressure is already public.",
  "created_at": "2026-05-08T00:00:00+00:00",
  "tool_version": "boss-ai-preference-v0"
}
```

`reason_tags` is retained for older comparison-level records. New browser
records write `action_tags` so each compared move can carry separate feedback.
Saving the same `fixture_id` + `action_a_id` + `action_b_id` again replaces the
older preference row.

V2 metadata fields are optional and old rows remain valid:

- `confidence`: `low`, `medium`, or `high`.
- `public_info_scope`: `public_only`, `public_plus_common_meta`,
  `hidden_info_rejected`, or `needs_source_check`.
- `lesson_type`: `hard_rule`, `weight_hint`, `sequence_policy`,
  `switch_policy`, `scout_policy`, `personality_style`, `schema_only`,
  `fixture_bug`, `stale_direct_action`, or `needs_context`.
- `condition_tags`: readable predicates such as `if_user_faster`,
  `survives_one_hit`, `sleep_clause_occupied`, or
  `hidden_coverage_plausible`.
- `counterfactual_group`: optional family id for generated boundary variants.
- `holdout`: optional boolean; `true` excludes the row from fitting and keeps
  it for evaluation.
- `source_team_hash`: optional hash of the relevant team/moveset source.
- `stale_reason`: optional explanation when a direct action id no longer maps
  cleanly after team changes.

Allowed pairwise choices:

- `a_better`
- `b_better`
- `both_good`
- `both_bad`
- `other_better`
- `needs_context`

Allowed reason tags:

- `uses_public_info`
- `misses_public_threat`
- `keeps_tempo`
- `too_greedy`
- `scary_pressure`
- `fits_boss_style`
- `reduces_risk`
- `too_passive`
- `calculated_risk`

Multi-turn trajectory preference rows are JSONL records in
`labels/boss_ai_trajectory_preferences.jsonl`:

```json
{
  "schema_version": 1,
  "fixture_id": "bugsy_scyther_vs_quilava_fire_pressure",
  "trajectory_a_id": "plan_bugsy_scyther_vs_quilava_fire_pressure_setup_once_then_attack_move_swords_dance_move_wing_attack",
  "trajectory_b_id": "plan_bugsy_scyther_vs_quilava_fire_pressure_attack_now_move_wing_attack_move_wing_attack",
  "choice": "a_better",
  "preferred_trajectory_id": "plan_bugsy_scyther_vs_quilava_fire_pressure_setup_once_then_attack_move_swords_dance_move_wing_attack",
  "horizon": 3,
  "confidence": "medium",
  "public_info_scope": "public_only",
  "lesson_type": "sequence_policy",
  "condition_tags": ["boss_faster", "survives_one_hit"],
  "branch_tags": ["if_player_switches_rescore"],
  "holdout": false,
  "comparison_scope": "selected_plan_over_all_shown",
  "compared_plan_ids": [
    "plan_bugsy_scyther_vs_quilava_fire_pressure_setup_once_then_attack_move_swords_dance_move_wing_attack",
    "plan_bugsy_scyther_vs_quilava_fire_pressure_attack_now_move_wing_attack_move_wing_attack"
  ],
  "source_team_hash": "current-party-hash",
  "fixture_state_hash": "current-fixture-hash",
  "note": "Setup is good only if it changes the next damage race.",
  "created_at": "2026-05-11T00:00:00+00:00",
  "tool_version": "boss-ai-preference-v0"
}
```

Allowed trajectory choices:

- `a_better`
- `b_better`
- `both_good`
- `both_bad`
- `depends`
- `neither_best_plan_missing`
- `upstream_state_issue`
- `needs_context`

Plan cards are generated review candidates, not ROM scripts. Each generated
plan must include a `shape`, `goal`, `horizon`, `steps`, `branch_rules`,
`stop_conditions`, `rationale`, and rollout assumptions. Player-side rollout
data must keep moves in `revealed`, `plausible`, `impossible`, and `unknown`
buckets; unrevealed player moves are never facts.

Coach Mode may save multiple trajectory rows from one click. Selecting a plan
card means that plan beats every other shown plan. `both_good`, `depends`,
`needs_context`, and `neither_best_plan_missing` apply to every shown pair.
`comparison_scope` and `compared_plan_ids` record that scope so later reports do
not treat one narrow pair as "best among all."

`source_team_hash` and `fixture_state_hash` are source freshness anchors. Reports
flag rows stale when current trainer-party or fixture/action state no longer
matches the hash stored with the label.

Missing-plan demonstrations are JSONL records in
`labels/boss_ai_plan_demonstrations.jsonl`:

```json
{
  "schema_version": 1,
  "fixture_id": "brock_golem_vs_vaporeon_explosion_question",
  "demonstration_id": "demo_sack_or_explode_for_clean_omastar",
  "horizon": 3,
  "steps": [
    {"turn": 1, "action_id": "move_explosion"},
    {"turn": 2, "action_id": "switch_omastar", "actor": "boss_next_mon"}
  ],
  "near_tie_with": ["plan_hard_switch_omastar"],
  "condition_tags": ["sack_for_clean_switch"],
  "human_summary": "Explosion and switching are close; vary them instead of always attacking.",
  "source_team_hash": "current-party-hash",
  "fixture_state_hash": "current-fixture-hash",
  "created_at": "2026-05-11T00:00:00+00:00",
  "tool_version": "boss-ai-preference-v0"
}
```

Single-action label records are still supported as JSONL rows in
`labels/boss_ai_labels.jsonl`:

```json
{
  "fixture_id": "clair_dragonair_vs_suicune_hidden_ice_beam",
  "state_version": 1,
  "action_id": "switch_kingdra",
  "label": "best",
  "rank": 1,
  "confidence": "medium",
  "lesson_type": "switch_policy",
  "condition_tags": ["hidden_coverage_plausible", "preserve_ace"],
  "note": "Pivots to Kingdra against public Ice Beam risk.",
  "created_at": "2026-05-08T00:00:00+00:00",
  "tool_version": "boss-ai-preference-v0"
}
```

Allowed labels:

- `best`
- `good`
- `bad`
- `cheap`
- `scary_good`
- `needs_context`

Structured lesson records are optional JSONL rows in
`labels/boss_ai_lessons.jsonl`. The lesson report also derives candidate
lessons directly from pairwise notes when this file is absent:

```json
{
  "lesson_id": "resisted_ramp_lock_opener",
  "source_preference_ids": [
    "whitney_miltank_vs_geodude_rollout_temptation:move_rollout:move_body_slam"
  ],
  "status": "candidate",
  "lesson_type": "hard_rule",
  "applies_to": {
    "move_properties": ["ramp_lock"],
    "target_properties": ["resists_move", "physically_bulky"],
    "excluded_when": ["ko_confirmed", "target_paralyzed", "already_locked"]
  },
  "expected_direction": "discourage",
  "rom_target": "engine/battle/ai/scoring.asm",
  "human_summary": "Do not start a resisted ramp-lock sequence when it does not KO and the target can punish or switch."
}
```

Allowed lesson statuses:

- `candidate`
- `accepted`
- `rejected`
- `needs_more_labels`

Allowed expected directions:

- `encourage`
- `discourage`
- `mixed`
- `review`
