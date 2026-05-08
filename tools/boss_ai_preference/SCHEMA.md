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
- `25%`: legal but limited, optional, or voucher-gated.
- `0%`: unavailable or blocked by a four-revealed-move set.

Common source tags include `revealed`, `level_up`, `pre_evo_level_up`,
`tm_available`, `voucher_limited`, `grass_encounter`, `surf_encounter`,
`old_rod_fishing`, `good_rod_fishing`, `super_rod_fishing`, `gift_or_prize:*`,
and `static_encounter:*`.

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

Single-action label records are still supported as JSONL rows in
`labels/boss_ai_labels.jsonl`:

```json
{
  "fixture_id": "clair_dragonite_vs_suicune_hidden_ice_beam",
  "state_version": 1,
  "action_id": "switch_kingdra",
  "label": "best",
  "rank": 1,
  "note": "Preserves Dragonite against public Ice Beam risk.",
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
