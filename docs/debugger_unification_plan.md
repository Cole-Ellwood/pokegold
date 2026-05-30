# Debugger Unification Plan — one God debugger on canonical `master`

**Status:** in progress (Slice 1 landed). Branch `claude/debugger-unify-god` off `master`.
**Why:** two debuggers evolved in parallel. `master` (canonical) carries the
verified **Q&A oracle** (`audit ready=True` 11/11; `check_debugger_godmode_benchmark.py`
29/29) on a clean `__main__` → `parsers` → `commands` → `formatters` architecture.
The **God-integration** (forward `consequence`, `tdb`/`reverse-query` time-travel,
`save-state-lab`, `rom-edit`, `bisect`, `vram-*`, `clobbers`, …) shipped to the
`codex/cleanup-gsc-rebalance-split` line and never came across. Goal: one debugger
that is a superset of both, on canonical master, ROM-byte-neutral.

## Divergence shape (measured)

- `tools/debugger/*.py` (excl. tests): **26 master-only, 45 codex-only, 38 shared**.
- Of the 38 shared, **32 diverged** — several massively (`dynamic_taint` 5035,
  `__main__` 4225, `visualization` 3166, `content_state` 2956, `mirrors` 2623,
  `minimize` 2490). So this is a **3-way reconciliation**, not a graft: both lines
  rewrote the shared core (master for the oracle + the package refactors, codex for
  the God verbs).

## Architecture decision — master is the skeleton

Codex's God verbs are **self-contained CLIs**: each module owns its `argparse` and
exposes `main(argv) -> int`; codex's monolithic `__main__` delegates to them via a
`V2_PASSTHROUGH_MODULES` dict. That pattern transplants cleanly onto master **without
touching `parsers`/`commands`/`formatters`**:

- New `tools/debugger/v2_passthrough.py` owns the verb→module dict + `delegate_to_module_main`.
- Thin `__main__.py` gains one pre-check: if `argv[0]` is a v2 verb, delegate; else
  run master's v1 parser unchanged.
- The v1 Q&A-oracle surface (and its 29/29 benchmark) stays exactly as is.

So harvesting a God verb = copy its module(s) + add one dict entry + port its tests.
The only real risk is a God module importing a **diverged shared module** whose API
changed on master; caught immediately by an import test + the module's own tests.

## Module disposition

- **Harvest (codex-only, additive):** the 45 God modules **except two that master
  already superseded** — codex's single-file `content_mirror.py` and `ranking.py`
  are OLDER than master's `content_mirror/` and `ranking/` **packages**. Keep
  master's packages; do not copy codex's single-file versions.
- **Keep (master-only):** the architecture files (`parsers`, `commands`,
  `formatters`, `cli_helpers`), the `content_mirror/` + `ranking/` packages,
  `proof_runner`, `runtime_state`, `save_state_format`. `save_state_inspect` is a
  reconciliation point — God's `save_state_lab` supersedes it (decide in Slice 4).
- **Shared diverged (32):** do **not** wholesale-replace. Each God module proved its
  shared-dep usage by importing + passing its tests against master's versions. When a
  God verb needs a codex-only ADDITION to a shared module, port that as a targeted
  addition to master's version, never a blind overwrite. `catalog.py` (capability
  registry feeding `audit ready=`) is reconciled last (Slice 6).

## Harvest order (slices) + per-slice gate

Every slice gate: cluster tests green · master benchmark **29/29** · `audit ready=True`
· `check_release_smoke.py` PASS · `git diff --check` clean · full `tools/debugger/tests`
suite green.

1. **consequence cluster** — `consequence`, `register_flow` (`clobbers`),
   `clobber_chain`, `clobber_graph`. **DONE.** 56 cluster tests + 301 suite pass.
2. **vram cluster** — `vram_snapshot`, `vram_decode`, `vram_diff`.
3. **reverse/time-travel** — `reverse_query`, `when_wrote`, `tdb` + deps
   (`address`, `address_boundary`, `effect_trace`, `evidence`, `hardware_evidence`,
   `reporting`/`workflow` additions). Heaviest.
4. **save_state_lab + rom_edit + bisect** — reconcile `save_state_lab` vs master's
   `save_state_inspect`.
5. **remaining God modules** — `probe`, `auto_watch`, `hardware_event_stream`,
   `hardware_regression`, `chaos`, `heatmap`, `causal_graph`, `speedup_harness`,
   `dap_server`, `input_log`, `audio_snapshot`, `visual_snapshot`, `stat_at`,
   `type_matchup`, `hook_order`, `context_packet`, `playtest_packet`, `shrink_*`,
   `sm83_model`.
6. **catalog + selftest + session_start (final)** — reconcile `catalog.py` so
   `audit ready=True` reflects the unified surface; port `selftest` + `session_start`;
   get the God selftest green on master. Then `/shape-check` + `refactor-reviewer`,
   regen `docs/generated/dev_index.md`, merge to master.

## Notes / traps

- Windows: `git`-subprocess tests (`test_bisect`, `test_rom_edit`) fail under pytest
  capture (WinError 6); run those with `pytest -s`.
- ROM-byte-neutral throughout — pure tooling. No `engine/data/ram` edits.
- `check_branch_currency.py` does NOT guard tooling drift (gameplay paths only); this
  doc + the merge-back-to-master discipline is what prevents a re-split.
