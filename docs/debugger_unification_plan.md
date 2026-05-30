# Debugger Unification Plan — one God debugger on canonical `master`

**Status:** core unification complete (Slices 1–6 landed; 20 v2 God verbs on
master + the v1 oracle + selftest 28/28). Branch `claude/debugger-unify-god` off
`master`. Remaining: 3 deferred items (below) + final merge to master.
**Next tier:** the unification is on canonical `master` (tip `04170ddf`). The
frontier above the God-tool bar — auto-navigation, runtime replay of the
static-only surfaces, one-shot taint, SM83 unification, live visualization —
and the 3 deferred items below are specced in
[`docs/debugger_deity_mode_roadmap.md`](debugger_deity_mode_roadmap.md).
**Why:** two debuggers evolved in parallel. `master` (canonical) carries the
verified **Q&A oracle** (`audit ready=True` 11/11; `check_debugger_godmode_benchmark.py`
29/29) on a clean `__main__` → `parsers` → `commands` → `formatters` architecture.
The **God-integration** (forward `consequence`, `tdb`/`reverse-query` time-travel,
`save-state-lab`, `rom-edit`, `bisect`, `vram-*`, `clobbers`, …) shipped to an
old integration branch (referred to here as the **God branch**) and never came
across to master. Goal: one debugger that is a superset of both, on canonical
master, ROM-byte-neutral. Single-owner (Claude) work — no pairing scaffolding.

## Divergence shape (measured)

- `tools/debugger/*.py` (excl. tests): **26 master-only, 45 God-branch-only, 38 shared**.
- Of the 38 shared, **32 diverged** — several massively (`dynamic_taint` 5035,
  `__main__` 4225, `visualization` 3166, `content_state` 2956, `mirrors` 2623,
  `minimize` 2490). So this is a **3-way reconciliation**, not a graft: both lines
  rewrote the shared core (master for the oracle + the package refactors, the God
  branch for the God verbs).

## Architecture decision — master is the skeleton

The God verbs are **self-contained CLIs**: each module owns its `argparse` and
exposes `main(argv) -> int`; the God branch's monolithic `__main__` delegates to them via a
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

- **Harvest (God-branch-only, additive):** the 45 God modules **except two that
  master already superseded** — the God branch's single-file `content_mirror.py`
  and `ranking.py` are OLDER than master's `content_mirror/` and `ranking/`
  **packages**. Keep master's packages; do not copy the single-file versions.
- **Keep (master-only):** the architecture files (`parsers`, `commands`,
  `formatters`, `cli_helpers`), the `content_mirror/` + `ranking/` packages,
  `proof_runner`, `runtime_state`, `save_state_format`. `save_state_inspect` is a
  reconciliation point — God's `save_state_lab` supersedes it (decide in Slice 4).
- **Shared diverged (32):** do **not** wholesale-replace. Each God module proved its
  shared-dep usage by importing + passing its tests against master's versions. When a
  God verb needs a God-branch-only ADDITION to a shared module, port that as a targeted
  addition to master's version, never a blind overwrite. `catalog.py` (capability
  registry feeding `audit ready=`) is reconciled last (Slice 6).

## Harvest order (slices) + per-slice gate

Every slice gate: cluster tests green · master benchmark **29/29** · `audit ready=True`
· `check_release_smoke.py` PASS · `git diff --check` clean · full `tools/debugger/tests`
suite green.

1. **consequence cluster** — `consequence`, `register_flow` (`clobbers`),
   `clobber_chain`, `clobber_graph`. **DONE.** 56 cluster tests + 301 suite pass.
2. **vram cluster + save_state_lab** — `vram_snapshot`, `vram_decode`, `vram_diff`,
   plus `save_state_lab` (`save-state-lab`), pulled forward because `vram_snapshot`
   imports it. **DONE.** 16 cluster tests + 317 suite pass. `save_state_lab` is added
   additively; master's `save_state_inspect` is left in place — consolidating the two
   is a deferred cleanup, not a blocker.
3. **reverse/time-travel** — `reverse_query`, `when_wrote`, `tdb` + deps
   (`address`, `address_boundary`, `effect_trace`, `evidence`, `hardware_evidence`,
   `reporting`/`workflow` additions). Heaviest.
4. **rom_edit + bisect** — both leaf verbs (`save_state_lab` moved to Slice 2).
5. **remaining God modules** — `probe`, `auto_watch`, `hardware_event_stream`,
   `hardware_regression`, `chaos`, `heatmap`, `causal_graph`, `speedup_harness`,
   `dap_server`, `input_log`, `audio_snapshot`, `visual_snapshot`, `stat_at`,
   `type_matchup`, `hook_order`, `context_packet`, `playtest_packet`, `shrink_*`,
   `sm83_model`.
6. **catalog + selftest + session_start (final)** — reconcile `catalog.py` so
   `audit ready=True` reflects the unified surface; port `selftest` + `session_start`;
   get the God selftest green on master. Then `/shape-check` + `refactor-reviewer`,
   regen `docs/generated/dev_index.md`, merge to master.

## Final state (Slices 1–6 landed)

**20 v2 God verbs on master**, alongside the v1 Q&A oracle (`audit ready=True`
11/11, benchmark 29/29) and `selftest` (28/28 components): `auto-watch`, `bisect`,
`clobbers`, `consequence`, `crossemu`, `dap`, `heatmap`, `hypothesis`, `pack`,
`probe`, `save-state-lab`, `selftest`, `session-start`, `speedup-report`,
`stat-at`, `tdb`, `type-matchup`, `vram-diff`, `vram-snapshot`, `when-wrote`.
Whole suite green throughout (`tools/debugger/tests` 600+ passing); pure tooling,
zero ROM bytes.

De-Codex (single-owner): pairing machinery retired (`handoff_log`,
`check_two_llm_handoff_log`); codex-named spec docs renamed
(`debugger_godmode_spec.md`, `damage_query_cli_spec.md`) with refs updated;
module comments/docstrings/tests neutralized.

### Deferred (re-harvestable from the God branch; tracked follow-ups)

1. **`rom_edit`** — its core gate was "ROM edit requires a *mutual-verified* (two-LLM)
   handoff phase"; single-owner needs a new gate (e.g. audits-pass), and it edits ROM
   source, which sits in tension with the debugger's read-only-on-ROM North Star.
   A design call — left out pending that decision.
2. **`causal-graph` + `hardware-event-stream` verbs** — harvested as libs but unexposed;
   they render via a kind→formatter dispatch (no self-contained `format_text`), so a
   clean verb needs their text formatters ported into `formatters.py` (or a JSON-only
   wrapper). Modules removed from the tree to avoid orphans; re-harvest when wiring.
3. **Benchmark-internal Codex naming** — `~10 codex_*` question IDs in
   `questions.jsonl`, the `questions_codex_lane.jsonl` filename, and "Codex pair-review"
   note text remain as historical provenance. Harness reads only `questions.jsonl` and
   keys per-question scoring on the IDs; mass-renaming risks the 29/29 and isn't
   load-bearing, so left as a documented cosmetic residual.

### `sm83_model_parity` selftest component — intentionally dropped

Master's `dynamic_taint` taint engine was preserved intact (a wholesale swap of the
God branch's `dynamic_taint` regressed master's taint tests — 0 findings where master
finds 1). The frame model was grafted additively. The parity check asserted both taint
consumers *share* the SM83 model, which full taint-engine unification would require;
that unification is deferred, so the component was removed. Both consumers work
independently.

## Notes / traps

- Windows: `git`-subprocess tests (`test_bisect`, `test_rom_edit`) fail under pytest
  capture (WinError 6); run those with `pytest -s`.
- ROM-byte-neutral throughout — pure tooling. No `engine/data/ram` edits.
- `check_branch_currency.py` does NOT guard tooling drift (gameplay paths only); this
  doc + the merge-back-to-master discipline is what prevents a re-split.
