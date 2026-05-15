# Boss AI Debugger Decision Trace

Status: Python scenario foundation plus ROM hook trace companion.

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
used by ROM contribution traces, but it is not itself a ROM rule-event trace.
For comparison, use `python-contribution-trace` to normalize scenario score
events into candidate/rule/delta records with explicit ROM-mirror rule ids.

ROM contribution trace companion:

```powershell
python -m tools.boss_ai_debugger rom-contribution-trace `
  --boss-route clair `
  --json-out audit\boss_ai_debugger\rom_contribution_trace_smoke.json
```

`rom-contribution-trace` drives a real trace-ROM boss route with PyBoy execution
hooks on Boss AI rule labels and score mutation helpers. It records score
before/after, signed delta, candidate slot, rule id, source label, and callsite
without adding a WRAM event buffer. Current limits: false predicate paths and
dynamic public-memory-read provenance are not captured yet.
