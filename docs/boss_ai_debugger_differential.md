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
- ROM contribution trace JSON files are summarized into
  `rom_contribution_summary`
- matched ROM/Python contribution traces can produce `rule_delta_mismatch`,
  `missing_python_rule`, and `missing_rom_rule`

Known limits are recorded in every report. Contribution comparison only runs
when a ROM trace id matches a Python trace id, and it currently compares changed
score-helper events by rule id and candidate slot. False predicate paths and
dynamic public-memory-read provenance are still outside this report.
