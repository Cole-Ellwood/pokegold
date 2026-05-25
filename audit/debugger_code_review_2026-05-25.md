# Debugger tools — structural code review (2026-05-25)

## Scope and method

Read-only review of the three debugger trees:
- `tools/debugger/` — the "unified omni-debugger v2"
- `tools/damage_debugger/` — PyBoy step-tracer
- `tools/boss_ai_debugger/` — boss AI inspection + ROM-trace scenarios

Method: file-size triage, function-shape sampling, cross-tree import map,
test-coverage shape. No correctness audit; no runtime behavior was tested.
Prior `audit/debugger_godmode_*` and `audit/debugger_power_*` documents
covered capability/benchmark, not structure — this review fills that gap.

## Direct assessment

**Yes, it is ugly.** Not in any single place — in pattern, repeated across
all three trees. Five concrete smells, ordered by how much they hurt
readability:

1. **The two `__main__.py` files are god-routers.** `debugger/__main__.py`
   is 3,424 lines and `boss_ai_debugger/__main__.py` is 1,482 lines.
   Every subcommand's arg parsing AND its dispatch wrapper AND its
   custom text-rendering function all live inline. (§1)
2. **`format_<thing>(report)` is the same function written 46 times.**
   In `debugger/__main__.py` alone, 46 of these (70–100 lines each)
   all do "render a stylized multi-line text block from a dict." Many
   share identical scaffolding (header, `warnings[:5]`, `errors[:5]`,
   `commands` section). (§2)
3. **`content_mirror.py` (3,665 lines) is 8 files glued into one.**
   Single file handles map events, audio channels, INCBIN assets,
   asset tables, scripts, text blocks, movement data, and labeled
   data — each as a separate concern with its own parser, invariants,
   and ROM-mirror logic. (§3)
4. **`tools/damage_debugger/legacy/` is 22 zombie files (3,576 lines).**
   Each starts with `raise SystemExit("...legacy scripts are pruned
   one-shot drivers...")` but keeps the original implementation
   underneath as unreachable dead code. Delete-then-import-not-found
   is cleaner than stub-then-unreachable-body. (§4)
5. **Test discipline is inconsistent and tests are unsplittable.**
   `damage_debugger/` has zero tests for 29 src files. `debugger/`
   has 4 substantive tests, but `tests/test_catalog.py` alone is
   **10,295 lines** — longer than the second-largest src file. (§5)

Two of these (§1, §2) are mechanically refactorable in a single pass.
The other three (§3, §4, §5) require more thought but are scoped — none
needs an architecture rewrite.

## Surface area in numbers

| Tree | Files | Lines | >400 | >700 | >1000 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `tools/debugger/` | 44 | 42,170 | 31 (70%) | 24 (55%) | 20 (45%) |
| `tools/damage_debugger/` | 29 | 11,726 | 11 (38%) | 6 (21%) | 3 (10%) |
| `tools/damage_debugger/legacy/` | 21 | 3,576 | 0 | 0 | 0 |
| `tools/boss_ai_debugger/` | 35 | 20,866 | 17 (49%) | 10 (29%) | 7 (20%) |
| **Total** | 129 | 78,338 | | | |

Per CLAUDE.md: >400 lines is a "design smell," >700 is "split unless
generated/declarative/inseparable." `tools/debugger/` has 55% of its
files past that bar. That is not "a few exception files," that is a
pattern.

Top 10 individual offenders:

| Lines | File |
| ---: | --- |
| 3,665 | [tools/debugger/content_mirror.py](tools/debugger/content_mirror.py) |
| 3,424 | [tools/debugger/__main__.py](tools/debugger/__main__.py) |
| 2,137 | [tools/debugger/ranking.py](tools/debugger/ranking.py) |
| 2,122 | [tools/boss_ai_debugger/rom_contribution_trace.py](tools/boss_ai_debugger/rom_contribution_trace.py) |
| 1,983 | [tools/debugger/minimize.py](tools/debugger/minimize.py) |
| 1,896 | [tools/debugger/setup_plan.py](tools/debugger/setup_plan.py) |
| 1,844 | [tools/debugger/impact.py](tools/debugger/impact.py) |
| 1,840 | [tools/boss_ai_debugger/generators.py](tools/boss_ai_debugger/generators.py) |
| 1,790 | [tools/debugger/visualization.py](tools/debugger/visualization.py) |
| 1,625 | [tools/boss_ai_debugger/move_score_probe.py](tools/boss_ai_debugger/move_score_probe.py) |

## §1 — The two `__main__.py` files are god-routers

`debugger/__main__.py` shape:
- 97 top-level defs
- 89 references to `subparsers.add_parser` / `def cmd_`
- `build_parser()` alone spans lines 61–558 (497 lines) — a single
  function adds 30+ subcommands with their own `add_argument` blocks
- 44 `cmd_*` handlers + 46 `format_*` renderers + 7 utilities

`boss_ai_debugger/__main__.py` shape (1,482 lines):
- 75 references to `subparsers.add_parser` / `def cmd_`
- `build_parser()` is lines 954–1437 (484 lines)

**Smell:** orchestration files are supposed to be thin (CLAUDE.md anchor:
"scenes, controllers, routes, components, and CLIs delegate detail").
Instead each command's argparse contract is duplicated inline next to its
dispatcher next to its renderer.

**Mechanical pattern** — nearly every `cmd_*` looks like this
([tools/debugger/__main__.py:563–593](tools/debugger/__main__.py:563)):

```python
def cmd_X(args: argparse.Namespace) -> int:
    report = build_X(
        kwarg=tuple(args.kwarg),
        ...
    )
    emit_report(report, args)
    return 0 if report["valid"] else 1
```

Of 44 `cmd_*` functions, ~40 are this exact shape with different field
names. This is text repetition of policy, not different behaviors.

**Recommendation:** move each subcommand's arg-parser block and renderer
into the module that owns its report (e.g., put `format_coverage` and the
`coverage` subparser definition in `tools/debugger/coverage.py`). The
top-level `__main__.py` reduces to a discovery loop that asks each
subsystem module for its (parser, dispatcher) tuple. Expected size of
`__main__.py` after refactor: ~300–600 lines.

## §2 — `format_<thing>(report)` is the same function written 46 times

In `debugger/__main__.py`, 46 functions match `^def format_`. Each is
70–100 lines. Sampling shows they all share scaffolding:

- A header line `"Unified Pokemon Gold romhack debugger <topic>"`
- A summary line built from report counters
- A loop over `report[items]` rendering each as `"  - {title}"` + indented
  evidence
- A "Top commands" section
- A `for warning in report["warnings"][:5]: lines.append(...)` tail
- A `for error in report["errors"][:5]: lines.append(...)` tail

Compare [tools/debugger/__main__.py:3000–3066 `format_content_mirror`]
(tools/debugger/__main__.py:3000) to
[tools/debugger/__main__.py:3069–3122 `format_content_scenarios`]
(tools/debugger/__main__.py:3069): the tails are byte-for-byte identical
loops, only the section names differ.

**Smell:** "repeated policy" per CLAUDE.md — these are 46 instances of
*one* template, not 46 distinct renderers.

**Recommendation:** a single `format_report(report, *, spec)` driven by
each report kind's declarative output spec ("which fields, which
limits"). Big payoff: today the textual format drifts between
subcommands; a shared formatter pins it.

## §3 — `content_mirror.py` is 8 files glued into one

3,665 lines, 67 top-level defs. Largest functions:

| Lines | Function |
| ---: | --- |
| 341 | `encode_script_command_block` |
| 140 | `analyze_source_file` |
| 139 | `parse_rgbds_source` |
| 122 | `movement_data_rom_mirror_invariants` |
| 122 | `script_command_rom_mirror_invariants` |
| 121 | `asset_table_rom_mirror_invariants` |
| 121 | `text_block_rom_mirror_invariants` |
| 121 | `data_block_rom_mirror_invariants` |
| 117 | `asset_rom_mirror_invariants` |
| 115 | `audio_channel_rom_mirror_invariants` |
| 109 | `map_event_rom_mirror_invariants` |

Eight `*_rom_mirror_invariants` functions sit side-by-side, each 110–125
lines, each handling a separate content type. Their `encode_*`
counterparts (`encode_map_event_table` 104 lines, `encode_labeled_data_block`
106 lines, `encode_script_command_block` 341 lines) live in the same file.

**Smell:** one file = one primary reason to change, per CLAUDE.md. This
file changes when ANY content type changes, which is at least 8
independent reasons.

**Recommendation:** `tools/debugger/content_mirror/` package with
`maps.py`, `audio.py`, `incbin.py`, `scripts.py`, `text.py`,
`movement.py`, `labeled_data.py`, `asset_tables.py`, plus a thin
`__init__.py` that registers the parsers and an `invariants.py` that
holds the dispatching logic. Same code, eight obvious homes for future
changes.

Same architecture smell, smaller scale:
- `tools/debugger/ranking.py:198–270` (`findings_from_report`) is a
  **30-case `if kind == "..."` chain** dispatching to per-kind finding
  builders. Classic registry pattern: one `FINDING_BUILDERS = {kind:
  function}` dict + one lookup line.
- `tools/boss_ai_debugger/generators.py` (1,840 lines) — each scenario
  generator is 50–127 lines, sitting next to all the others. Split by
  generator family.

## §4 — `damage_debugger/legacy/` is zombie code, not retired code

22 files, 3,576 lines. Each starts with:

```python
LEGACY_EXIT = (
    "tools.damage_debugger.legacy scripts are pruned one-shot drivers; "
    "use active tools.damage_debugger modules instead."
)
raise SystemExit(LEGACY_EXIT)

import sys
import time
from .emulator import DebugSession

def main() -> int:
    t0 = time.time()
    ...
```

The `raise SystemExit` is correct as a stop-gap. But:

- The original implementation underneath the stub is **unreachable code**.
  A reader who scrolls past the exit will read code that pretends to be
  the real implementation.
- "Pruned but not deleted" is a state that doesn't pay rent. There's
  zero `from tools.damage_debugger.legacy` anywhere in the active codebase
  (verified by grep). They aren't load-bearing.
- The file count alone — 22 files in `legacy/` — is visual noise when
  navigating `damage_debugger/`.

**Recommendation:** delete the directory. The historical implementation
lives in git history. If a reader genuinely needs to recover an old
one-shot driver, `git log -- tools/damage_debugger/legacy/<file>` is
the right tool, not a quarantined stub. If the goal is "don't break
external invocations," shrink each file to a single line:
`raise SystemExit("legacy/<name>: removed 2026-05-25; see git history")`.

**Also missing:** `tools/damage_debugger/__init__.py` is empty
(1 line). Every caller imports modules directly by name. A curated
`__all__` would document what damage_debugger's public surface actually
is. Compare with `tools/debugger/__init__.py` (26 exports listed).

## §5 — Test asymmetry + one 10k-line test file

| Tree | Src files | Test files | Ratio |
| --- | ---: | ---: | --- |
| `tools/debugger/` | 44 | 5 | 1 test file per 9 src |
| `tools/damage_debugger/` | 29 | 0 | none |
| `tools/boss_ai_debugger/` | 35 | 29 | ~1:1 |

**`damage_debugger` having zero tests is a real gap**, not just a
discipline smell. The user's memory `reference_damage_debugger.md` says
this is the harness that "found and fixed the user's 5x physical damage
bug." It's load-bearing on bug investigations and gets imported by both
other debugger trees ([dynamic_taint.py:8](tools/debugger/dynamic_taint.py:8),
[instruction_trace.py:9](tools/debugger/instruction_trace.py:9),
[pokemon_semantics.py:6](tools/debugger/pokemon_semantics.py:6),
[boss_ai_debugger/move_score_probe.py:14](tools/boss_ai_debugger/move_score_probe.py:14)).
Untested code that other tooling builds on is a liability.

**`tools/debugger/tests/test_catalog.py` is 10,295 lines.** One file
asserts on ~30 different subsystem outputs (its imports include almost
every module in `debugger/`). That's not test cohesion; that's a giant
integration test pretending to be unit tests. When it fails, finding
the relevant assertion takes scrolling.

**Recommendation:** split `test_catalog.py` by subsystem to match the
src layout (one `test_<module>.py` per `<module>.py`). Backfill
`damage_debugger/tests/` for at least the modules that other tools
import (`disasm`, `taint`, `state`, `tables`, `battle_calc`).

## §6 — Non-finding: the "unification" wasn't a duplication

Memory `reference_omni_debugger_v2_surface.md` says the v2 omni-debugger
"absorbs damage_debugger + boss_ai_debugger + audit floor under one
kernel." Reading the import graph:

| Importer | Imports from |
| --- | --- |
| `tools/debugger/` | `tools/damage_debugger/` (4 narrow edges: disasm, taint, state, tables) |
| `tools/boss_ai_debugger/` | `tools/damage_debugger/` (battle_calc, state, tables) |
| `tools/debugger/` | does NOT import from `tools/boss_ai_debugger/` |
| `tools/boss_ai_debugger/` | does NOT import from `tools/debugger/` |

So `damage_debugger` is a leaf utility used by both, and `debugger/`
and `boss_ai_debugger/` are siblings that share leaf code but have
fully separate CLIs. **The "absorption" was nominal** — there is one
unified front door (`python -m tools.debugger`), but boss-AI work
still goes through `python -m tools.boss_ai_debugger`. This is fine in
principle (no actual duplication shipped), just worth knowing: the
memory's "absorbed" framing overstates the consolidation. The two trees
still have to be navigated separately, which is part of why §1 hurts:
the user-facing entry doubles.

## Prioritized recommendations

Ordered by ratio of (reader-pain reduced) / (refactor risk):

1. **Delete `tools/damage_debugger/legacy/`.** (§4) Pure win — 22 fewer
   files in the tree, no behavior change. Highest payoff for lowest
   risk. Worth a single PR.
2. **Move `format_<thing>` and subcommand registration into the module
   that owns each report.** (§1, §2) Shrinks the two `__main__.py`
   files dramatically and gives every subsystem one obvious home. Can
   ship in slices — one subcommand at a time, behavior-preserving.
3. **Replace `findings_from_report`'s 30-case `if/elif` with a registry
   dict.** ([ranking.py:198–270](tools/debugger/ranking.py:198)) Tiny
   patch, big readability win.
4. **Split `content_mirror.py` into a package by content type.** (§3)
   Bigger move but every per-content-type author would benefit.
   Save for when someone next touches it.
5. **Backfill tests for `damage_debugger/`** at least for the four
   modules imported by other debugger trees. (§5)
6. **Split `tests/test_catalog.py` by subsystem.** (§5) Mechanical,
   read-only-on-src. Defer until someone needs to add a new test there.

None of these is an architectural rewrite. Each is mechanical and
behavior-preserving. The two highest-impact items (#1 and #2) can be
done by a single agent in a single sitting without touching the
surrounding logic.

## Execution status (2026-05-25)

**Shipped:**

- Item 1 (delete `tools/damage_debugger/legacy/`) — commit `3d6ae70d`.
- Item 2 (`__main__.py` god-router split) — `3d6ae70d` for
  `tools/debugger/` (3,424 → 16 lines, split into `parsers.py` +
  `commands.py` + `formatters.py` + `cli_helpers.py`); `d62cafec` for
  `tools/boss_ai_debugger/` (1,482 → 18 lines, split into `parsers.py`
  + `commands.py`; no `formatters.py` needed because boss_ai_debugger
  already kept its formatters in subsystem modules).
- Item 3 (`findings_from_report` registry dict) — `3d6ae70d`.
- `emit_report` got the same registry-dict treatment as item 3
  (the 96-line if/elif chain in the original `__main__.py` is now
  a `FORMATTERS.get(kind)` lookup against the new `formatters.py`
  registry).
- Item 4 (`content_mirror.py` package split) — shipped after
  `808ec11b`. Old single-file `tools/debugger/content_mirror.py`
  (3,665 lines) deleted; new `tools/debugger/content_mirror/`
  package replaces it with 14 files / 3,976 lines: one per content
  type (`maps.py`=451, `audio.py`=250, `incbin.py`=201,
  `asset_tables.py`=153, `scripts.py`=598, `scripts_data.py`=219,
  `text.py`=332, `movement.py`=337, `labeled_data.py`=247) plus
  `helpers.py`=241 (shared regexes/parsers/factories),
  `rom_context.py`=347 (ROM + symbol + charmap loaders),
  `charmap.py`=64 (charmap string encoding shared between text and
  labeled_data), `invariants.py`=496 (the top-level
  `build_content_mirror_report` orchestrator + `analyze_source_file`
  per-source dispatcher + `parse_rgbds_source` shared tokenizer), and
  a 40-line `__init__.py` that re-exports the public surface so the
  five downstream importers (`tools/debugger/__init__.py`,
  `tests/test_catalog.py`, `runtime_state.py`, `investigate.py`,
  `content_scenarios.py`, `commands.py`) stay unbroken.
  `scripts_data.py` was split out from `scripts.py` after the
  file-shape gate flagged the 798-line draft; the
  `SCRIPT_COMMAND_SPECS` dict is pure declarative data (1:1 mirror of
  `macros/scripts/scripts.asm`) so the split fits CLAUDE.md's
  declarative-data exemption.

**Tests passing post-refactor:**
`tools.debugger.tests.test_catalog` → 230/230 (re-verified after the
content_mirror split — every `test_content_mirror_compares_*`
integration test still passes against the package);
`tools.boss_ai_debugger.tests` → 211/212 (1 skip; 1 pre-existing
failure on `test_current_roadmap_audit_keeps_goal_incomplete` —
A/B-verified pre-existing via `git stash` against the pre-refactor
tree, concerns `audit/boss_ai_debugger/rule_map.json` data state, not
source structure). `check_no_solo_commits_omni_debugger.py` passes
for all four shipped phases.

**Remaining items, ranked by leverage:**

1. **`ranking.py` split (2,115 lines, added during execution).** The
   file-shape hook flagged this during slice 2; the split was deferred
   to keep the registry-dict change bounded. Same "homogeneous registry
   of similar functions" justification as the new `formatters.py`.
   Suggested package: `ranking/severity.py` (SEVERITY_BASE,
   ROM_SURFACE_SEVERITY_HINTS, calibrate_finding_severity),
   `ranking/builders.py` (the 30 `*_findings` functions),
   `ranking/__init__.py` (rank_findings + dispatcher + helpers).
2. **Item 6 — split `tests/test_catalog.py` (10,295 lines).**
   Mechanical; one `test_<module>.py` per `<module>.py` to mirror the
   src layout.
3. **Item 5 — backfill `damage_debugger/tests/`.** Different shape
   (real test-writing, not structural refactor); may warrant its own
   session. Priority modules are the four that other debugger trees
   import: `disasm`, `taint`, `state`, `tables`, `battle_calc`.

## What I did *not* check

- Correctness of any single function. This is a structure review only.
- Whether any of the 30+ subcommands actually work end-to-end.
- Performance or memory characteristics.
- Whether the v2 capability claims in the prior `debugger_godmode_*`
  audits still hold.
- Test quality of the boss_ai tests (only counted them).

A correctness review would want a different methodology — running
`python -m tools.debugger ...` on real artifacts, comparing outputs,
checking that the 8 `*_rom_mirror_invariants` functions actually agree
with the ROM. That is a separate task.
