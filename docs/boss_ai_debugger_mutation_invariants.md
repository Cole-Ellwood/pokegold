# Boss AI Debugger Mutation And Invariant Tools

Status: foundation.

These tools improve trust in the debugger itself. They do not edit ROM source,
and they do not promote mined observations into blocking policy without review.

## Mutation Testing

```powershell
python -m tools.boss_ai_debugger mutate --target scorer --json-out audit\boss_ai_debugger\mutation_report.json
```

The initial mutation target is the Python preference scorer. Mutants wrap
`score_action` in memory and run the existing strict pairwise preference
regression through `evaluate_corpus`.

Report statuses:

- `killed`: the mutant reduced strict agreement or failed the regression
  threshold.
- `survived`: the mutant changed exercised strict pairs but labels still passed.
- `not_exercised`: no strict pair changed, so the corpus does not test that
  scoring rule yet.

This deliberately starts with scorer mutations because it has a clean injection
point and does not require source patching, subprocesses, or ROM rebuilds.

The changed-AI run profile includes this report:

```powershell
python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 200 --seed 1
```

## Invariant Mining

```powershell
python -m tools.boss_ai_debugger invariants mine `
  --scenarios audit\boss_ai_debugger\generated\spikes_spin.jsonl `
  --trace-dir audit\boss_ai_trace `
  --runs-dir audit\boss_ai_debugger\runs
```

The miner emits candidate invariants with support counts, examples, and
violations. Current candidates cover:

- selector probability surfaces in generated scenarios
- score-delta direction and selectable-score bounds
- exact selector trace byte shape and chosen-slot possibility
- run-store artifact hash and summary consistency

Current traces do not contain full scoring rule events or public-read
attribution, so rule-level invariants such as "rule A implies public field B"
must wait for full scoring traces.
