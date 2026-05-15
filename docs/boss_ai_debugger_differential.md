# Boss AI Debugger Differential Runner

Status: foundation.

```powershell
python -m tools.boss_ai_debugger diff `
  --scenarios audit\boss_ai_debugger\generated\spikes_spin.jsonl `
  --trace-dir audit\boss_ai_trace `
  --json-out audit\boss_ai_debugger\differential.json
```

The current differential runner merges two data sources into one mismatch
schema:

- generated scenario expectation failures become `policy_preference_mismatch`
- exact trace selector replay failures become confirmed `selector_mismatch`
- partial or decisionless trace captures become `trace_incomplete`

Known limits are recorded in every report. Full `rule_delta_mismatch`,
`missing_python_rule`, and `missing_rom_rule` classes require ROM scoring
contribution trace events, which are not implemented yet.
