# Boss AI Debugger Analysis Tools

Status: Phase-6 foundation.

These tools work on debugger scenario JSON/JSONL and batch reports. They are
offline analysis helpers, not full ROM scoring traces.

## Counterfactual

```powershell
python -m tools.boss_ai_debugger counterfactual --scenario scenarios.jsonl --scenario-id generated_spikes_spin_1_00001
```

Reports:

- ROM top action and probability
- expected best action ids
- final score by action
- score delta needed for an expected-best action to become top
- public fact changes likely to flip the answer
- evidence refs and policy note

## Minimize

```powershell
python -m tools.boss_ai_debugger minimize --scenario scenarios.jsonl --scenario-id generated_spikes_spin_1_00001
```

Removes nonessential metadata and unneeded actions while preserving:

- verdict class
- ROM best action
- expected best action ids

The output is a compact repro scenario for review or future fixture promotion.

## Localize

```powershell
python -m tools.boss_ai_debugger localize --scenarios scenarios.jsonl
python -m tools.boss_ai_debugger localize --report batch_report.json
```

Ranks:

- overrepresented policy tags
- overrepresented condition tags
- frequent move-delta rules
- likely causes labeled as hypotheses

The labels are intentionally cautious: `localize` can suggest likely causes, but
only ROM traces or direct interventions can confirm root cause.
