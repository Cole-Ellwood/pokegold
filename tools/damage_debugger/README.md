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
| `python -m tools.damage_debugger.full_chain_v2` | Focused single-scenario investigation. Pidgey-Tackle-vs-Cyndaquil chain with per-step damage logging. |
| `python -m tools.damage_debugger.trace_chain` | Deep register-state trace at every key hook in the chain. Use when `clobber_smoke` flags a regression and you want the full per-hook snapshot. |
| `python -m tools.damage_debugger.repro_pidgey` | Original repro driver for the May 2026 c-clobber bug. Kept as a known-good reference scenario. |

## Scenario format (clobber_smoke.py)

Each `Scenario` is a `(name, seed_callable, expected_low, expected_high,
note, [xfail])` record. The runner:

1. Boots a fresh PyBoy on `pokegold_debug.gbc` (240 frames -- enough to
   pass init/RAM-clear).
2. Installs hooks at every entry/exit in `HOOK_TARGETS` (key points
   along the damage chain). Hooks capture register snapshots into a
   per-scenario list.
3. Calls the seed callable: writes WRAM/HRAM to populate the scenario
   (mons, stats, move, item, turn).
4. Calls `BattleCommand_DamageStats`, `BattleCommand_DamageCalc`,
   `BattleCommand_Stab` in sequence via `safe_call.call_function_safe`.
5. Reads `wCurDamage` and asserts `expected_low <= damage <=
   expected_high`.

On FAIL, the captured register snapshots from every hook are dumped to
the log so the clobber's location is visible without re-tracing. On
XFAIL (scenario tagged `xfail=True` because of a discovered-but-not-
fixed bug), the same diagnostic is emitted but the harness still exits
0.

To add a new scenario: write a `seed_*` function and append a
`Scenario(...)` to `SCENARIOS`. Pick `expected_low/high` loose enough to
absorb integer-floor noise but tight enough to catch a 4-10x clobber-
class spike.

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
- `full_chain_v2.py` -- single-scenario chain runner with step-by-step damage
- `trace_chain.py` -- deep per-hook register snapshot
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
