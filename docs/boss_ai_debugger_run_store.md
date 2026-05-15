# Boss AI Debugger Run Store

Status: Phase-1 experiment-lineage foundation.

`tools/boss_ai_debugger/run_store.py` records reproducible debugger runs under
`audit/boss_ai_debugger/runs/`.

## Commands

```powershell
python -m tools.boss_ai_debugger run-suite --profile generated-smoke --count 200 --seed 1
```

The generated-smoke profile writes:

- `metadata.json`
- `scenarios.jsonl`
- `batch_report.json`
- `review_queue.json`
- `summary.md`

`metadata.json` records:

- run id
- profile
- created timestamp
- git commit
- dirty status
- parameters
- artifact paths
- artifact hashes
- schema validation report
- batch summary
- review queue summary

## Scope

This is not the final changed-AI suite. The changed-AI profile still depends on
full ROM scoring contribution traces. The current run store gives generated
scenario searches reproducible lineage now, so later ROM-backed suites can use
the same artifact shape.
