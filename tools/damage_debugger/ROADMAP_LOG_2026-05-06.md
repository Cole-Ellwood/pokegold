# damage_debugger roadmap implementation log -- 2026-05-06

Append-only working log for `C:/Users/lolno/.claude/plans/linear-knitting-pizza.md`.

## Preflight and baseline

Active item: baseline before H1.

Changed:
- Created work branch `codex/damage-debugger-roadmap-20260506` from
  `claude/thirsty-jackson-893a52`.
- Rebuilt `pokegold_debug.gbc` / `pokegold_debug.sym` through WSL because
  the checked-out source had the Eviolite fix but the debug ROM was stale.
- Regenerated `docs/generated/dev_index.md` after the successful build.

Debugger self-check:
- `python -m tools.damage_debugger.oracle` passed.
- `python -m tools.damage_debugger.clobber_smoke` passed after rebuild.
- `python -m tools.damage_debugger.fuzz --max-examples=50` passed.
- `python -m tools.damage_debugger.find --bug hp_d_clobber` passed.

Commands run:
- `git fetch --all`
- `git branch --all --contains f438afae`
- `git switch -c codex/damage-debugger-roadmap-20260506 claude/thirsty-jackson-893a52`
- `wsl -e bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe gold_debug'`
- `python scripts/generate_dev_index.py --rom pokegold`
- `python -m tools.damage_debugger.oracle`
- `python -m tools.damage_debugger.clobber_smoke`
- `python -m tools.damage_debugger.fuzz --max-examples=50`
- `python -m tools.damage_debugger.find --bug hp_d_clobber`

Bug found in debugger itself:
- `fuzz.py` left the shared PyBoy cache alive at process exit. On Windows
  that produced repeated `Error in sys.excepthook` noise after a passing
  run. Fixed under H1.

Open:
- Continue H1 with multiprocessing fuzz.

## H1 -- multiprocessing fuzz

Active item: H1, multi-process fuzz parallelization.

Changed:
- Added `--workers N` to `tools.damage_debugger.fuzz`.
- Split Hypothesis budgets across worker processes, one PyBoy boot cache
  per worker.
- Added deterministic per-worker seeds.
- Added `--self-check-workers N` to compare a fixed corpus between
  single-process and multi-process execution.
- Stopped the fuzz boot cache explicitly in every worker.
- Documented the new modes in README, BUG_CHECK, and asm verification floor.

Debugger self-check:
- Fixed-corpus worker equivalence fails if worker aggregation, ordering, or
  ROM/oracle scoring differs between single and multi-process runs.

Commands run:
- `python -m tools.damage_debugger.fuzz --self-check-workers=2`
- `python -m tools.damage_debugger.fuzz --max-examples=20 --workers=1 --verbose`
- `python -m tools.damage_debugger.fuzz --max-examples=20 --workers=2 --verbose`
- `python -m tools.damage_debugger.fuzz --max-examples=40 --workers=4`
- `python -m tools.damage_debugger.fuzz --max-examples=50 --workers=1`
- `python -m tools.damage_debugger.fuzz --max-examples=50 --workers=2`
- `python -m tools.damage_debugger.oracle`
- `python -m tools.damage_debugger.clobber_smoke`
- `python -m compileall -q tools\damage_debugger`
- `python tools\audit\check_navigation_floor.py`
- `python tools\audit\check_release_smoke.py`

Bug found in debugger itself:
- The old `--seed` option did not actually seed Hypothesis. H1 now applies
  Hypothesis seeds explicitly and reports each worker seed.

Open:
- `check_release_smoke.py` fails on pre-existing stale shipped-claim
  references in `.claude_handoffs` / `docs\manual_qa_backlog.md` against
  `codex/cleanup-gsc-rebalance-split`; not edited under damage-debugger
  scope. H1-specific checks and `check_navigation_floor.py` pass.
