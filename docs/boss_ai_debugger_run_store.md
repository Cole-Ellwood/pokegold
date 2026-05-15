# Boss AI Debugger Run Store

Status: Phase-1 experiment-lineage foundation.

`tools/boss_ai_debugger/run_store.py` records reproducible debugger runs under
`audit/boss_ai_debugger/runs/`.

## Commands

```powershell
python -m tools.boss_ai_debugger run-suite --profile generated-smoke --count 200 --seed 1
python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 200 --seed 1
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
- changed-AI gate summaries when using `--profile changed-ai`
- copied ROM contribution trace artifacts and summary hashes when present

## Scope

This is not the final changed-AI suite. The changed-AI profile ingests existing
ROM score-helper contribution trace artifacts, but it does not rebuild ROMs,
refresh live captures, or regenerate those trace artifacts. The current run
store gives generated scenario searches and fast changed-AI gates reproducible
lineage now, so later ROM-backed suites can use the same artifact shape.
