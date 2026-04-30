# Source And Output Ownership

Use this before editing a path or trusting an artifact. It combines path class,
edit policy, and generated/output ownership so future sessions do not have to
open two classifiers for the same decision.

## Path Classifier

| Path or pattern | Class | Edit policy | Truth role |
| --- | --- | --- | --- |
| `engine/`, `home/`, `macros/` | ROM behavior source | Edit only for requested gameplay/system work. | Primary implementation truth. |
| `data/`, `constants/` | ROM data source | Edit only for requested data, balance, trainer, item, move, or pointer work. | Primary data truth. |
| `maps/` | ROM map/script source | Edit only for requested map, event, text, NPC, or progression work. | Primary map-script truth. |
| `ram/` | Memory layout source | High caution; check `docs/generated/dev_index.md` before edits. | Primary memory truth. |
| `audio/`, `gfx/` | Asset/source data | Edit for requested media work only. | Primary asset truth. |
| `tools/` | Local tooling | Edit for audits, generators, trace helpers, and build support. | Tooling truth. |
| `scripts/` | Local generators | Edit when generated docs/audits need new source-derived facts. | Generator truth. |
| `docs/`, except `docs/generated/` | Hand-authored docs | Safe for organization passes. | Intent and routing truth below source/linker outputs. |
| `docs/generated/` | Generated docs | Do not hand-edit; regenerate. | Generated mirror of source/linker truth. |
| `docs/agent_navigation/` | Agent routing layer | Safe for organization passes. | Routing only; never overrides source or generated truth. |
| `audit/` | Evidence and audit artifacts | Edit when documenting real evidence or blocked attempts. | Evidence, not implementation truth. |
| `decisions/`, `journal/` | Durable judgment calls and session diaries | Edit when recording reversible architecture choices or per-session observations. | Tracked durable communication. |
| `.claude_handoffs/` | Per-session handoff prompts (gitignored) | Write when ending a long task; not tracked. | Local communication only. |
| `.local/`, `workspace/` | Scratch, local deps, probes, temporary outputs | Do not treat as canonical without an explicit task. | Scratch/archive only. |
| `dist/`, `*.gbc`, `*.o`, `*.map`, `*.sym` | Build/release outputs | Do not edit by hand. | Outputs; `.map`/`.sym` are read-only linker truth. |

## Generator And Output Owners

| Path or pattern | Owner | Edit directly? | Refresh or verify with |
| --- | --- | --- | --- |
| `engine/`, `data/`, `maps/`, `constants/`, `home/`, `ram/`, `macros/` | ROM source | Yes, only for requested behavior/data work. | Build both ROMs and run relevant audits. |
| `tools/audit/`, `tools/trace/` | Local verification/capture tooling | Yes, for tooling tasks. | Run the tool itself plus `python tools\audit\check_docs_navigation.py`. |
| `scripts/generate_dev_index.py` | Dev-index generator | Yes, for generated index format/content changes. | `python scripts\generate_dev_index.py --rom pokegold` |
| `scripts/generate_balance_audit.py` | Balance-audit generator | Yes, for generated balance audit changes. | `python scripts\generate_balance_audit.py` |
| `docs/generated/dev_index.md` | Generated navigation mirror | No. | Regenerate with `scripts/generate_dev_index.py`. |
| `docs/generated/balance_audit.md` | Generated balance mirror | No. | Regenerate with `scripts/generate_balance_audit.py`. |
| `docs/`, except `docs/generated/` | Agent/human docs | Yes. | `python tools\audit\check_docs_navigation.py`, `git diff --check`. |
| `audit/` | Evidence and audit artifacts | Yes, when documenting real evidence or blocked attempts. | Matching audit tool if one exists. |
| `decisions/`, `journal/` | Durable judgment/observation logs | Yes, sparingly. | Manual review; usually docs navigation if paths are referenced elsewhere. |
| `Makefile`, `layout.link` | Build/link ownership | Yes, only for build/layout tasks. | Build both ROMs; regenerate dev index if linker outputs change. |
| `pokegold.gbc`, `pokesilver.gbc`, debug/trace `.gbc` | Built ROM outputs | No. | Build commands in `docs/build.md`. |
| `*.o` | Build object outputs | No. | Rebuild. |
| `*.map`, `*.sym` | Linker outputs and address truth | No. | Rebuild; read as current address/source truth. |
| `roms.sha1` | Checksum target metadata | Only during release/checksum tasks. | Full compare/release workflow. |
| `dist/` | Release artifacts | No ordinary source edits. | Release artifact workflow in `docs/build.md`. |
| `.local/`, `workspace/` | Scratch, local deps, probes, temporary outputs | No canonical edits. | Treat as disposable unless a task explicitly names it. |

## Decision Rule

If a file is generated, edit the generator or source. If a file is output, run
the build or release process. If a file is scratch, copy only the durable fact
into `docs/`, `audit/`, `decisions/`, or `journal/` and say where it came from.

For documentation-only beauty passes, stay in `docs/`, `audit/`, `decisions/`,
and `journal/` unless the user explicitly asks for tooling support. Do not
clean, reset, or rewrite unrelated dirty worktree changes.

## Workspace Hygiene Rule

Ignored build/linker outputs can make the raw folder feel noisy. That noise is
not automatically a defect: root `.gbc`, `.map`, and `.sym` files are part of
the proven build/index workflow, and object files may be normal RGBDS byproducts.

For a 10/10 cleanliness pass, do not delete ignored files, relocate outputs,
or change `Makefile` output paths just to make the tree look tidy. First prove
which artifacts are expected, which are stale scratch, and which tools/docs
assume the current layout.

## Source-History Sediment Rule

Do not treat `unused`, `beta`, or `debug` filenames as deletion proof. This
codebase intentionally assembles some historical or unreferenced material:
examples include beta map blocks in `data/maps/blocks.asm`, beta map scripts and
attributes, unused Johto tileset data in `gfx/tilesets.asm`, debug room source,
and old text/data tables included from `main.asm` or nearby engine files.

Before proposing source deletion, check the include/table owners first:

```powershell
rg -n "unused|beta|debug" main.asm data/maps gfx engine maps
rg -n "INCLUDE|INCBIN" main.asm data/maps/scripts.asm data/maps/maps.asm data/maps/attributes.asm data/maps/blocks.asm gfx/tilesets.asm
```

Deleting assembled-but-unreferenced sediment needs a real removal plan: source
reference proof, map/symbol diff, Gold/Silver build, release smoke, and a reason
beyond making folder browsing look cleaner.

## 10/10 Workspace Criteria

Organization is 10/10 when every visible top-level family has an obvious role:
source, hand-authored docs, generated docs, build/linker output, release output,
or local scratch.

Cleanliness is 10/10 when `git status --short --branch` tells the source truth
quickly, ignored output is classified instead of scary, and no cleanup command
is needed just to understand the repo.

Future-agent navigation is 10/10 when a broad polish prompt routes here before
any destructive cleanup, and when a future helper can explain why the raw
assembly checkout is noisy without touching gameplay or build products.

## Hygiene Audit Helper

Use this read-only classifier before proposing cleanup:

```powershell
python tools\audit\check_workspace_hygiene.py
```

It wraps `git clean -ndX` into artifact families and also reports tracked source
status plus unignored untracked files. It does not delete, move, or rewrite
anything.

2026-04-26 no-churn audit result:

- tracked source was clean on branch `codex/cleanup-gsc-rebalance-split`;
- `git clean -ndX` reported 4247 ignored cleanup candidates;
- the largest families were generated graphics outputs (`.2bpp`, `.gbcpal`,
  `.2bpp.lz`, `.dimensions`, `.1bpp`) and expected RGBDS outputs;
- root normal/debug/trace `.gbc`, `.map`, and `.sym` files were present and
  should stay in place unless a user approves an output-layout plan;
- `.local/` held probe/dependency/temp outputs, `workspace/` held scratch review
  material, and `dist/` held release artifacts;
- no deletion or relocation was performed because the noise is currently
  explainable and build/index/tooling assumptions still depend on root outputs.

2026-04-26 follow-up organization result:

- the root QoL research report moved to `docs/qol_research_report.md`; it is
  durable policy research, not root/build truth;
- the old ignored sprint12 patch under workspace scratch was a 183 KB legacy
  gameplay patch snapshot; both `git apply --check` and
  `git apply --reverse --check` failed against current source, so current
  source/git history own the truth. It was deleted along with empty `workspace/`
  directories;
- `.local/` remains local scratch/dependency/probe output. Current top-level
  families include trace probes, PyBoy dependencies, ROM baselines/roundtrips,
  temporary outputs, and verification artifacts. Do not delete it without naming
  exact paths and trace/release impact;
- 2026-04-28 BPS release refresh: `dist/checksums.txt` and
  `dist/pokegold-data-rebalance.bps` match the current source-built
  `pokegold.gbc`; the local data-rebalance, data-rebalance-play, release, and
  roundtrip ROM copies under `.local/roms/` all match that same ROM.
  `roms.sha1`, debug ROM hashes, and VC patch outputs were left outside this
  scoped BPS package refresh.

## Current Build Output Families

| Family | Examples | Use |
| --- | --- | --- |
| Normal Gold/Silver | `pokegold.gbc`, `pokesilver.gbc`, matching `.map`/`.sym` | Main build artifacts and current address truth. |
| Debug | `pokegold_debug.gbc`, `pokesilver_debug.gbc`, matching `.map`/`.sym` | Debug build artifacts. |
| Trace | `pokegold_trace.gbc`, `pokesilver_trace.gbc`, matching `.map`/`.sym` | Boss AI trace and WRAM-symbol capture work. |
| Objects | `main_*.o`, `ram_*.o`, `home_*.o`, `audio_*.o` | Intermediate build outputs. |

Do not hand-edit any file in these output families.
