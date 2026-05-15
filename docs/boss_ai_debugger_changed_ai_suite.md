# Boss AI Debugger Changed-AI Suite

Status: local foundation.

```powershell
python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 200 --seed 1
```

The changed-AI profile creates a reproducible run directory under
`audit\boss_ai_debugger\runs\` with:

- generated scenarios
- batch expectation report
- review queue
- route evaluation report
- metamorphic report
- scorer mutation report
- candidate invariant report
- selector trace replay report when trace files are available
- run metadata with git commit, changed files, artifact hashes, and known gaps
- Markdown summary

This is the current one-command adaptation harness for local debugger work. It
does not yet rebuild ROMs, refresh live trace captures, or emit full scoring
contribution traces. Those limitations are recorded in each run's `known_gaps`
field so the suite does not overstate ROM accuracy.
