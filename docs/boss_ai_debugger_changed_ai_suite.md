# Boss AI Debugger Changed-AI Suite

Status: local foundation.

```powershell
python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 200 --seed 1
python -m tools.boss_ai_debugger run-suite --profile changed-ai --refresh-rom-contribution-trace
python -m tools.boss_ai_debugger run-suite --profile changed-ai --rebuild-roms --refresh-live-traces
python tools\audit\check_boss_ai_debugger_performance.py
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
- ROM contribution trace summary from existing trace artifacts when present
- optional targeted ROM score materialization results
- optional ROM rebuild command report
- optional live trace refresh command report
- previous changed-AI run diff when an earlier run exists
- run metadata with git commit, changed files, artifact hashes, and known gaps
- Markdown summary

This is the current one-command adaptation harness for local debugger work. It
does not yet rebuild ROMs, refresh live trace captures, or regenerate scoring
contribution traces. It copies and summarizes existing
`rom-contribution-trace` JSON artifacts so score-helper rule coverage is visible
in the same run output. Each run also writes `previous_run_diff.json`, comparing
changed-AI metrics, artifact hashes, and changed-file sets against the latest
older changed-AI run in the same run store. The differential artifact compares
ROM/Python contribution events only when trace ids match. Those limitations are
recorded in each run's `known_gaps` field so the suite does not overstate ROM
accuracy.

`--rebuild-roms` runs the normal/trace ROM build command and stores
`rom_rebuild.json`. `--refresh-live-traces` runs the state factory and trace
batch commands and stores `live_trace_refresh.json`. Both are opt-in so a fast
local changed-AI run records skipped command artifacts instead of silently doing
expensive work.

The final debugger done gate invokes this profile with rebuild, live trace
refresh, contribution refresh, and score materialization enabled unless
`--skip-changed-ai-suite` is passed to the done gate.

`--refresh-rom-contribution-trace` drives one configured boss route, Clair by
default, and stores a fresh ROM contribution trace inside the run directory. It
is intentionally opt-in so the normal changed-AI suite remains fast and does not
require PyBoy for every local report.
