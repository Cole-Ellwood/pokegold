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

## H2 -- Claude pre-commit smoke hook

Active item: H2, pre-commit smoke hook.

Changed:
- Added `tools/damage_debugger/precommit_check.py`.
- Wired `.claude/settings.json` `PreToolUse` for Bash commands to run the
  checker before Claude executes `git commit`.
- The checker runs `clobber_smoke` only when the pending commit touches
  `engine/battle/late_gen_held_items.asm` or
  `engine/battle/type_passive_damage_mods.asm`.
- Added a temp-repo self-test that covers non-commit skip, untouched-file
  skip, touched-file smoke execution, and touched-file smoke failure blocking.

Debugger self-check:
- `python -m tools.damage_debugger.precommit_check --self-test` fails if
  the hook runs smoke for untouched files, skips smoke for touched target
  files, or fails to propagate a smoke failure.

Commands run:
- `python -m tools.damage_debugger.precommit_check --self-test`
- `python -c "import json; json.load(open('.claude/settings.json', encoding='utf-8')); print('settings json ok')"`
- `python -m compileall -q tools\damage_debugger`
- `{"tool_input":{"command":"git status"}} | python -m tools.damage_debugger.precommit_check`
- `{"tool_input":{"command":"git commit -m test"}} | python -m tools.damage_debugger.precommit_check --dry-run`
- `python3 -c "import pyboy; print('pyboy ok')"`

Bug found in debugger itself:
- None in the existing debugger. H2 adds the missing gate.

Open:
- Run final H2 verification floor and commit.

## H3 -- weather + badge oracle/fuzz axes

Active item: H3, Pass C weather + badges.

Changed:
- Added weather, move-effect, badge, link-mode, and battle-turn fields to
  `BattleInputs`.
- Modeled `DoWeatherModifiers` in `oracle.py`, including type rows taking
  precedence over the rain + SolarBeam move-effect row.
- Modeled `DoBadgeTypeBoosts` in `oracle.py`, including player-turn and
  link-mode gates, Johto/Kanto bit order, min-1 boost, and `$ffff` cap.
- Extended `fuzz.py` to generate and seed weather/badge axes.
- Added three deterministic `clobber_smoke` scenarios:
  `special_sun_fire`, `special_rain_fire`, and `special_fire_badge`.
- Registered those scenarios in `find.py` and exposed weather/badge fields
  in the human report.
- Marked the weather/badge audit gaps closed in
  `ORACLE_AUDIT_2026-05-05.md`.

Debugger self-check:
- Oracle self-test now includes exact expected values for sun, rain, and
  VolcanoBadge.
- `clobber_smoke` now fails if ROM behavior for those three reference
  scenarios diverges from the documented ranges.
- Fuzz worker self-check corpus now includes weather, SolarBeam-in-rain,
  and badge cases.

Commands run:
- `python -m tools.damage_debugger.oracle`
- `python -m tools.damage_debugger.clobber_smoke`
- `python -m tools.damage_debugger.fuzz --self-check-workers=2`
- `python -m tools.damage_debugger.fuzz --max-examples=100 --workers=1`
- `python -m tools.damage_debugger.fuzz --max-examples=100 --workers=2`
- `python -m tools.damage_debugger.find special_sun_fire`
- `python -m tools.damage_debugger.find special_fire_badge`

Bug found in debugger itself:
- The oracle audit had correctly identified weather/badges as gaps; no new
  ROM bug appeared. The debugger bug was incomplete modeling/seed coverage,
  now fixed.

Open:
- Run final H3 verification floor and commit.

## M1 -- cap-add endian investigation

Active item: M1, cap-add endian investigation.

Changed:
- Added `tools/damage_debugger/cap_add_probe.py`.
- Added `BattleInputs.initial_cur_damage`.
- Added `oracle.predict_damagecalc_only` and a model switch for current-asm
  vs intended endian-neutral accumulation.
- Extended `fuzz.py` to seed nonzero `wCurDamage` between DamageStats and
  DamageCalc for synthetic multi-hit coverage.
- Documented the finding in BUG_CHECK and ORACLE_AUDIT.

Debugger self-check:
- `cap_add_probe` fails if ROM DamageCalc output matches neither the current
  asm model nor the intended model.
- Fuzz worker self-check now includes a `$0100` initial damage case.

Commands run:
- `python -m tools.damage_debugger.oracle`
- `python -m tools.damage_debugger.cap_add_probe`
- `python -m tools.damage_debugger.fuzz --self-check-workers=2`
- `python -m tools.damage_debugger.fuzz --max-examples=100 --workers=1`
- `python -m tools.damage_debugger.fuzz --max-examples=100 --workers=2`
- `python -m tools.damage_debugger.clobber_smoke`
- `python -m compileall -q tools\damage_debugger`

Bug found in debugger/ROM:
- ROM bug confirmed: `BattleCommand_DamageCalc` adds
  `high(wCurDamage)` twice when incoming `wCurDamage >= $0100`. Example:
  incoming `$0100` gives ROM/current-asm 289 vs intended 288.
- Debugger gap closed: oracle/fuzz previously had no nonzero incoming
  `wCurDamage` axis.

Open:
- Do not fix ROM under this roadmap item; gameplay-affecting fix needs
  explicit approval. Run final M1 verification floor and commit.

## H4 -- type-effectiveness, DamageVariation, after-hit scenarios

Active item: H4, deterministic coverage for type rows plus smoke coverage
for DamageVariation and late-gen after-hit effects.

Changed:
- Extended `clobber_smoke.Scenario` with optional per-scenario call chains,
  HP/state post-checks, call budgets, and an explicit allowance for handlers
  that apply side effects before entering battle text/HUD loops.
- Added smoke scenarios for FIRE super-effective, resisted, and NORMAL
  immune type rows.
- Added a DamageVariation range scenario after the super-effective chain.
- Added isolated after-hit scenarios for Rocky Helmet, Shell Bell, and Life
  Orb with HP post-checks.
- Added oracle self-test cases for the deterministic type rows.
- Fixed `find.py`'s Stab bucket hook to read at
  `BattleCommand_Stab.SkipStab` instead of reusing the post-matchup value.
- Added `python -m tools.damage_debugger.find --self-test`.

Debugger self-check:
- `clobber_smoke` fails on after-hit HP-state mismatches.
- `find --self-test` fails if Stab / TypeMatchup / TypePassive bucket
  boundaries are miswired.

Commands run:
- `python -m tools.damage_debugger.clobber_smoke` before H4 edits.
- `python -m tools.damage_debugger.oracle`
- `python -m compileall -q tools\damage_debugger`
- `python -m tools.damage_debugger.clobber_smoke`
- `python -m tools.damage_debugger.find special_super_effective`
- `python -m tools.damage_debugger.find special_not_very_effective`
- `python -m tools.damage_debugger.find physical_immune`
- `python -m tools.damage_debugger.find --list`
- `python -m tools.damage_debugger.find --json special_super_effective`
- `python -m tools.damage_debugger.find --self-test`
- `python -m tools.damage_debugger.fuzz --self-check-workers=2`
- `python -m tools.damage_debugger.fuzz --max-examples=100 --workers=1`
- `python -m tools.damage_debugger.fuzz --max-examples=100 --workers=2`
- `python tools\audit\check_navigation_floor.py`
- `git diff --check`

Bug found in debugger itself:
- `find.py` previously reported false Stab divergences for type-effective
  scenarios because it used the matchup-end hook as both the Stab and
  TypeMatchup bucket.

Open:
- Commit H4.

## M2 -- reusable hook instrumentation in find.py

Active item: M2, promote the "HL + memory at hook" probe pattern.

Changed:
- Added `--instrument-hook <symbol>` to `find.py`.
- Added reusable hook recording for CPU registers plus
  `mem[HL-2..HL]` on every hit.
- Added text and JSON instrumentation output.
- Added `--bug dm_hl_clobber` as the supported repro for the historical
  `CheckTypeMatchup.Yup` HL-clobber bug.
- Extended `find --self-test` with a `CheckTypeMatchup.Yup` instrumentation
  assertion.

Debugger self-check:
- The self-test fails if the DM repro does not produce exactly one real
  `GROUND -> GHOST` type-table row (`$04 $08 $00`) or if the hook window
  points into stack memory.
- Invalid hook names return exit code 2.

Commands run:
- `python -m compileall -q tools\damage_debugger`
- `python -m tools.damage_debugger.clobber_smoke`
- `python -m tools.damage_debugger.oracle`
- `python -m tools.damage_debugger.find --self-test`
- `python -m tools.damage_debugger.find --bug dm_hl_clobber --instrument-hook CheckTypeMatchup.Yup`
- `python -m tools.damage_debugger.find --bug dm_hl_clobber --instrument-hook CheckTypeMatchup.Yup --json`
- `python -m tools.damage_debugger.find special_super_effective --instrument-hook NoSuch.Symbol`
- `python tools\audit\check_navigation_floor.py`
- `git diff --check`

Bug found in debugger itself:
- None new in M2. This promotes the existing probe pattern into maintained
  tooling.

Open:
- Run final M2 verification floor and commit.

## H5 -- SM83 taint tracker

Active item: H5, byte-level taint over tracer frames.

Changed:
- Added `tools/damage_debugger/taint.py`.
- Implemented register/memory taint state, memory sink findings, and an
  `analyze_tracer(...)` bridge for populated `tracer.Tracer` streams.
- Covered common SM83 data-movement, memory, stack, ALU, rotate/shift,
  flag, and control-flow opcodes used by damage-path traces.
- Added CLI self-tests and JSON self-test output.
- Documented the new tool in README and BUG_CHECK.

Debugger self-check:
- Synthetic fixtures fail if taint propagation breaks across register
  copies, `[hl]` memory, stack push/pop, ALU combination, tracer bridging,
  or sink reporting.

Commands run:
- `python -m compileall -q tools\damage_debugger`
- `python -m tools.damage_debugger.taint --self-test`
- `python -m tools.damage_debugger.taint --json-self-test`
- `python -m tools.damage_debugger.tracer`
- `python -m tools.damage_debugger.clobber_smoke`
- `python -m tools.damage_debugger.find --self-test`

Bug found in debugger itself:
- None new in H5. This adds the root-cause propagation layer that later
  traced failures can use.

Open:
- Run final H5 verification floor and commit.

## M3 -- coverage report

Active item: M3, per-PC smoke-scenario coverage report.

Changed:
- Added `tools/damage_debugger/coverage.py`.
- Added Markdown report generation at `audit/damage_debugger/coverage.md`.
- Added JSON summary output and `--fail-under` threshold handling.
- Added synthetic self-tests for output shape, JSON totals, missed-PC
  rendering, and threshold failure behavior.

Debugger self-check:
- `coverage --self-test` fails if report schema or threshold behavior breaks.

Commands run:
- `python -m compileall -q tools\damage_debugger`
- `python -m tools.damage_debugger.coverage --self-test`
- `python -m tools.damage_debugger.coverage --write audit\damage_debugger\coverage.md --json`
- `python -m tools.damage_debugger.coverage --fail-under 99 --target BattleCommand_DamageCalc`

Bug found in debugger itself:
- The initial default target set included `CheckTypeMatchup`; per-PC hooks in
  its long type-table loop made the full H4 scenario set exceed the command
  timeout. M3 now keeps `CheckTypeMatchup` explicitly targetable but omits it
  from the default report, relying on Stab coverage plus M2's focused hook
  instrumentation for that path.

Open:
- Run final M3 verification floor and commit.

## M4 -- Tenet-format trace export

Active item: M4, Tenet-style omniscient trace export.

Changed:
- Added `tools/damage_debugger/tenet_writer.py`.
- Wrapped existing `tracer.Tracer` frames in JSONL records that carry raw
  Tenet delta syntax plus structured register and watched-memory events.
- Added scenario-backed tracing, so a known smoke scenario can run while a
  single damage-path function is traced.
- Added optional raw `.tenet` text output.
- Ignored generated `audit/damage_debugger/*.jsonl` and `*.tenet` trace
  outputs.

Debugger self-check:
- `tenet_writer --self-test` verifies raw Tenet syntax, JSONL schema,
  memory-write event shape, target-event query helper, text output,
  empty-trace rejection, and bad-watch-size rejection.

Commands run:
- `python -m tools.damage_debugger.tracer`
- `python -m tools.damage_debugger.clobber_smoke`
- `python -m compileall -q tools\damage_debugger`
- `python -m tools.damage_debugger.tenet_writer --self-test`
- `python -m tools.damage_debugger.tenet_writer --scenario special_super_effective --target BattleCommand_Stab --output "$env:TEMP\dd_stab_tenet.jsonl" --text-output "$env:TEMP\dd_stab_tenet.tenet"`
- JSON shape check over `$env:TEMP\dd_stab_tenet.jsonl`
- Invalid target and invalid `--max-frames` failure checks

Bug found in debugger itself:
- The first M4 draft imported `clobber_smoke` at module import time, causing
  the pure `--self-test` path to emit PyBoy's SDL warning and depend on
  emulator imports. Scenario imports are now lazy, so the schema self-check is
  emulator-independent.

Open:
- Run final M4 verification floor and commit.

## M5 -- Pass D negative-control redo

Active item: M5, negative control re-do.

Changed:
- No shipped code change.
- Temporarily removed the AG-08 `push bc` / `pop bc` preservation pair in
  `ApplyLateGenDamageStatsItemMods_Far`.
- Rebuilt the deliberately broken debug ROM, captured smoke/find failure
  evidence, restored the source, rebuilt the clean debug ROM, and regenerated
  `docs/generated/dev_index.md`.
- Documented the check in `BUG_CHECK.md`.

Debugger self-check:
- Historical AG-08 fixture must fail `clobber_smoke` and bucket-locate in
  `find.py`; clean restore must return to PASS/no-divergence.

Commands run:
- Temporary `apply_patch` removing `push bc` / `pop bc`
- `wsl -e bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe gold_debug'`
- `python -m tools.damage_debugger.clobber_smoke`
- `python -m tools.damage_debugger.find physical_no_items`
- `python -m tools.damage_debugger.find --json physical_no_items`
- Temporary `apply_patch` restoring `push bc` / `pop bc`
- WSL `gold_debug` rebuild again
- `python scripts/generate_dev_index.py --rom pokegold`
- `python -m tools.damage_debugger.clobber_smoke`
- `python -m tools.damage_debugger.find physical_no_items`
- `git diff -- engine\battle\late_gen_held_items.asm`
- `git diff -- docs\generated\dev_index.md`

Bug found in debugger itself:
- None. The fixture still trips the harness. Current expanded smoke catches
  13/18 scenarios; the historical first eight all fail with the expected
  footprint.

Open:
- Run final M5 doc/navigation checks and commit.
