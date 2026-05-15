# Boss AI Debugger Route Evaluation

Status: foundation.

`route-eval` classifies one-turn debugger scenarios using existing structured
scenario expectations and `evaluate_scenario()` verdicts. It is not yet a
multi-turn search engine.

```powershell
python -m tools.boss_ai_debugger route-eval --scenario scenarios.jsonl
python -m tools.boss_ai_debugger route-eval --scenario scenarios.jsonl --scenario-id generated_spikes_spin_1_00001
```

The output has two levels:

- `classification`: a precise structured outcome such as `route_pass`,
  `route_bad_roll`, `route_expected_unreachable`, `route_acceptable_but_review`,
  or `route_weak_best`.
- `route_bucket`: a coarse review bucket: `pass`, `actually_bad`,
  `acceptable_near_tie`, or `needs_context`.

Route-family tags are derived only from structured policy and condition tags.
Examples include `hazard_route`, `spikes_capped`, `active_spinner_risk`,
`spinblocked`, `foresight_breaks_spinblock`, and `tempo_pressure`.

Current limits:

- No route prose parsing.
- No two-to-five turn branch search yet.
- No damage/mechanics simulation beyond the existing one-turn scenario scorer.

This gives the review queue a safer first route-context layer without pretending
the debugger has full multi-turn planning.
