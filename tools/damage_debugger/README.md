# damage_debugger

Python + PyBoy harness for catching CLOBBER-CLASS regressions in the
battle damage chain. Built during the May 2026 5x physical damage hunt
(commit `ac769ca5`), where an `ld c, a` mirror added inside
`TypePassive_GetEffectiveMoveCategory_Far`'s `.done` block silently
broke same-bank callers in `engine/battle/late_gen_held_items.asm` whose
`bc` was load-bearing post-dispatch. See
`docs/asm_authoring_guide.md` sec 3.13/3.14 for the recurrence pattern.

## Entry points

| Tool | Use when |
| --- | --- |
| `python -m tools.damage_debugger.clobber_smoke` | **§6 verification floor** -- runs every battle-engine ABI-touching change through. Multi-scenario regression harness. Exits 0 on pass. |
| `python -m tools.damage_debugger.clobber_smoke --self-test` | Debugger self-check for symbol-table-backed diagnostic rendering. |
| `python -m tools.damage_debugger.fuzz --max=1000 --workers=4` | Hypothesis ROM-vs-oracle fuzz. Each worker owns a PyBoy boot cache and a deterministic seed partition. |
| `python -m tools.damage_debugger.fuzz --self-check-workers=4` | Debugger self-check: runs a fixed corpus single-process and multi-process, then asserts identical ROM/oracle results. |
| `python -m tools.damage_debugger.find <scenario>` | Bucket-locates ROM-vs-oracle divergence across DamageStats / DamageCalc / Stab / TypeMatchup / TypePassive. |
| `python -m tools.damage_debugger.find --self-test` | Debugger self-check for the mid-Stab hook boundaries used by type-effectiveness diagnostics. |
| `python -m tools.damage_debugger.find --bug dm_hl_clobber --instrument-hook CheckTypeMatchup.Yup` | Focused hook instrumentation: captures registers plus `mem[HL-2..HL]` at every hook hit. |
| `python -m tools.damage_debugger.matchup CROBAT:44 ALAKAZAM:44 WING_ATTACK --user-item sharp_beak` | Quick source-table-backed damage query for one attacker, defender, move, items, grind profile, and HP percent. |
| `python -m tools.damage_debugger.taint --self-test` | SM83 byte-level taint tracker self-test for register, memory, stack, ALU, and sink propagation. |
| `python -m tools.damage_debugger.coverage --write` | Per-PC coverage report for smoke scenarios; writes `audit/damage_debugger/coverage.md`. |
| `python -m tools.damage_debugger.tenet_writer --scenario special_super_effective --target BattleCommand_Stab --output audit/damage_debugger/stab_tenet.jsonl` | Tenet-style delta trace export. JSONL records carry raw Tenet syntax plus structured events for `jq`/Python queries. |
| `python -m tools.damage_debugger.replay --scenario physical_no_items --watch wCurDamage --json` | Snapshot-ring replay: stop when a watched symbol changes, rewind to the pre-change save-state, and verify the transition replays. |
| `python tools/audit/balance_diff.py --output audit/damage_debugger/damage_heatmap.md` | Oracle-backed damage delta heatmap for learned moves and supported modifier variants. |
| `python -m tools.damage_debugger.cap_add_probe` | Regression-checks the fixed DamageCalc nonzero-`wCurDamage` accumulation path against the historical buggy model. |
| `python -m tools.damage_debugger.precommit_check --self-test` | Self-test for the Claude `PreToolUse` git-commit gate that runs `clobber_smoke` when damage-chain asm is being committed. |
| `python -m tools.damage_debugger.full_chain_v2` | Focused single-scenario investigation. Pidgey-Tackle-vs-Cyndaquil chain with per-step damage logging. |
| `python -m tools.damage_debugger.trace_chain` | Deep register-state trace at every key hook in the chain. Use when `clobber_smoke` flags a regression and you want the full per-hook snapshot. |
| `python -m tools.damage_debugger.repro_pidgey` | Original repro driver for the May 2026 c-clobber bug. Kept as a known-good reference scenario. |

## Scenario format (clobber_smoke.py)

Each `Scenario` is a `(name, seed_callable, expected_low, expected_high,
note, [chain], [post_check], [xfail])` record. The runner:

1. Boots a fresh PyBoy on `pokegold_debug.gbc` (240 frames -- enough to
   pass init/RAM-clear).
2. Installs hooks at every entry/exit in `HOOK_TARGETS` (key points
   along the damage chain). Hooks capture register snapshots into a
   per-scenario list.
3. Calls the seed callable: writes WRAM/HRAM to populate the scenario
   (mons, stats, move, item, turn).
4. Calls the scenario's chain via `safe_call.call_function_safe`. The
   default chain is `BattleCommand_DamageStats`,
   `BattleCommand_DamageCalc`, `BattleCommand_Stab`; H4 scenarios also
   exercise `BattleCommand_DamageVariation` and isolated
   `HandleLateGenAfterHitEffects_Far` paths.
5. Reads `wCurDamage` and asserts `expected_low <= damage <=
   expected_high`.
6. Runs any `post_check` assertions. After-hit scenarios use this to
   verify HP side effects (Rocky Helmet, Shell Bell, Life Orb), not only
   that the handler exits.

On FAIL, the captured register snapshots from every hook are dumped to
the log so the clobber's location is visible without re-tracing. On
XFAIL (scenario tagged `xfail=True` because of a discovered-but-not-
fixed bug), the same diagnostic is emitted but the harness still exits
0.

To add a new scenario: write a `seed_*` function and append a
`Scenario(...)` to `SCENARIOS`. Pick `expected_low/high` loose enough to
absorb integer-floor or RNG noise but tight enough to catch a 4-10x
clobber-class spike. If the feature's correctness is visible outside
`wCurDamage`, add a `post_check` so the debugger fails when that state is
wrong.

## Fuzz multiprocessing

`fuzz.py` compares generated `BattleInputs` against
`oracle.predict_damage`. `--workers N` splits the example budget across
N spawned Python processes. Each process creates its own PyBoy instance
and boot cache; PyBoy is never shared across processes.

The generated axes include base stats, move type/category, crits, held
items, TypeBoostItems, late-gen post-quotient item multipliers,
TypePassive HP/status flags, weather, SolarBeam's rain modifier, matching
badge type boosts, and a synthetic nonzero `wCurDamage` entry axis for
the DamageCalc cap-add path.

The default base seed is deterministic. Worker `i` runs with
`base_seed + i`, so a failing worker report can be reproduced by rerunning
with `--workers 1 --seed <reported-seed>` and the same per-worker
`--max-examples` budget.

Before trusting worker-mode changes, run:

```powershell
python -m tools.damage_debugger.fuzz --self-check-workers=2
python -m tools.damage_debugger.fuzz --max-examples=20 --workers=1
python -m tools.damage_debugger.fuzz --max-examples=20 --workers=2
```

## Claude pre-commit gate

`.claude/settings.json` wires `tools.damage_debugger.precommit_check` into
Claude Code's `PreToolUse` hook for Bash commands. The script reads the
hook JSON from stdin and only acts on `git commit` commands.

If the pending commit touches a damage-chain ABI-sensitive file,
the hook runs `python -m tools.damage_debugger.clobber_smoke` and blocks
the commit tool call when smoke fails:

- `engine/battle/effect_commands.asm`
- `engine/battle/late_gen_held_items.asm`
- `engine/battle/type_passive_damage_mods.asm`
- `home/farcall.asm`

Run `python -m tools.damage_debugger.precommit_check --self-test` after
changing this hook. The self-test creates a temporary Git repository and
checks non-commit skip, untouched-file skip, touched-file smoke execution,
and touched-file smoke failure propagation.

## Tenet JSONL trace export

`tenet_writer.py` adapts `tracer.Tracer` frames into the public Tenet
delta-line syntax documented by Markus Gaasedelen's Tenet project
(`reg=0x...`, `mw=0xADDR:BYTES`, `pc=0x...`). The supported file format
is JSONL: each record includes the raw Tenet line under `tenet` plus
structured `events` so command-line queries do not need an IDA/Tenet
viewer or a custom SM83 architecture file.

Common checks:

```powershell
python -m tools.damage_debugger.tenet_writer --self-test
python -m tools.damage_debugger.tenet_writer --scenario special_super_effective --target BattleCommand_Stab --output audit\damage_debugger\stab_tenet.jsonl
jq -c ".events[] | select(.target == \"wCurDamage\")" audit\damage_debugger\stab_tenet.jsonl
```

The self-test is synthetic and fails if the JSONL schema, raw Tenet
syntax, memory-write event shape, target query helper, empty-trace
failure, or bad-watch failure behavior regresses. Generated `.jsonl` and
`.tenet` traces under `audit/damage_debugger/` are ignored local outputs.

## The HRAM sentinel trick (safe_call.py)

`call_function_safe` runs an arbitrary function under PyBoy by:

1. Writing a 2-byte `jr -2` (`0x18 0xFE`) trap at HRAM `$FFFD-$FFFE`.
2. Pushing `$FFFD` as the return address on the stack.
3. Setting `PC` to the function's entry, switching ROM bank.
4. Ticking until `PC == $FFFD` (the trap loops in place).

`$FFFD` was chosen specifically -- the original implementation used
`$0008`, the `FarCall` RST vector. Anything that called `farcall` from
the function-under-test would corrupt our return address by entering
the FarCall trampoline. `$FFFD` is in the high HRAM gap right before
`IE` at `$FFFF`, never executed by the game, and the `jr -2` is
self-contained.

**Never re-introduce `$0008` as a sentinel. The full chain's
`farcall`-dense paths blow up silently.**

## Toolchain

Required:
- Python 3.13+ with PyBoy 2.7.0 (system-installed; see
  `requirements.txt`).
- A built `pokegold_debug.gbc` + matching `.sym` at the project root
  (build via `make` per `CLAUDE.md`).

The harness reads the project root through `paths.find_artifact` (walks
up from the worktree to find ROM/sym), so it works the same in a
`.claude/worktrees/*` worktree as at the project root.

## Module catalog

Active:

- `clobber_smoke.py` -- multi-scenario regression harness (the §6 floor entry point)
- `fuzz.py` -- Hypothesis ROM-vs-oracle fuzz, with multiprocessing worker mode
- `oracle.py` -- Python damage oracle and oracle self-test
- `find.py` -- bucketed ROM-vs-oracle divergence diagnostic
- `minimize.py` -- single-axis ddmin for load-bearing BattleInputs fields
- `cap_add_probe.py` -- M1 DamageCalc nonzero-wCurDamage accumulation classifier
- `precommit_check.py` -- Claude PreToolUse git-commit smoke gate
- `full_chain_v2.py` -- single-scenario chain runner with step-by-step damage
- `trace_chain.py` -- deep per-hook register snapshot
- `taint.py` -- SM83 byte-level taint propagation over tracer frames
- `coverage.py` -- per-PC smoke-scenario coverage report
- `tenet_writer.py` -- Tenet-style JSONL trace export and target-event query helper
- `replay.py` -- PyBoy snapshot-ring watch replay for smoke scenarios
- `repro_pidgey.py` -- original c-clobber repro
- `safe_call.py` -- HRAM-sentinel function runner
- `synth.py` -- SynthBattle dataclass + scenario installer
- `scenario.py` -- YAML-scenario loader (`tools/damage_debugger/scenarios/*.yaml`)
- `tracer.py` -- PC-trace recorder for a single function
- `emulator.py` -- `DebugSession` context manager (PyBoy + symbols + state load)
- `paths.py` -- locate ROM/sym across worktree boundaries
- `symbols.py` -- `.sym` parser (forward + reverse indexes for `Label+0xNN` rendering)
- `disasm.py` -- minimal SM83 instruction walker used by `tracer.py`
- `__init__.py`, `requirements.txt`, `scenarios/` -- supporting

Pruned (under `legacy/`):

One-shot investigation drivers from earlier bug hunts: `boss_drive*`,
`drive_to_battle`, `force_wild_battle`, `boot_*`, `disasm*`,
`stats_*sweep`, `stab_isolation`, `live_probe`, `probe_inspect`,
`sgm_decoder` (VBA save-state parser experiment), `survey_savs`,
`full_sweep`, `validate_emulator`, `inspect_boss_state`, `full_chain`
(superseded by `full_chain_v2`). Kept on disk because future debugging
may want to crib pieces from them, but not part of the active surface.

## Wiring into §6 verification floor

`docs/asm_authoring_guide.md` sec 6 lists `clobber_smoke` as the
floor for any change to battle-code register ABI. Sister static audit:
`tools/audit/check_typepassive_c_mirror.py` -- both belong in any
release-smoke run involving `engine/battle/late_gen_held_items.asm` or
`engine/battle/type_passive_damage_mods.asm`.

For oracle/fuzz changes, run `python -m tools.damage_debugger.oracle`,
`python -m tools.damage_debugger.fuzz --self-check-workers=2`, and a
representative fuzz budget in both `--workers=1` and `--workers>1` modes.
