# Boss AI Debugger Decision Trace

Status: Python scenario foundation.

```powershell
python -m tools.boss_ai_debugger decision-trace `
  --scenario audit\boss_ai_debugger\generated\spikes_spin.jsonl `
  --scenario-id generated_spikes_spin_1_00001 `
  --json-out audit\boss_ai_debugger\decision_trace.json
```

The trace uses a structured event format:

- `state_load`
- `candidate`
- `score_rule`
- `selector`
- `policy_check`

This is a Python scenario score waterfall. It gives the debugger the event shape
needed for future ROM scoring contribution traces, but it is not itself a ROM
rule-event trace. ROM rule ids, score-event ring buffers, and public-read
evidence still need trace-ROM instrumentation.
