# Non-debugger codebase — structural code review (2026-05-26)

## Scope and method

Read-only review of everything OUTSIDE the three debugger trees
(`tools/debugger/`, `tools/damage_debugger/`, `tools/boss_ai_debugger/`).
Concrete scope:

- Python tooling: `tools/audit/`, `tools/boss_ai_preference/`,
  `tools/headless_battle/`, `tools/pokemon_mastery/`, `tools/trace/`,
  `tools/perf/`, plus loose `tools/*.py` and the `scripts/` tree.
- ROM source: `engine/`, `home/`, `data/`, `constants/`, `macros/`, `ram/`.
- ROM content: `maps/`, `gfx/`, `audio/`, `tilesets/`.
- Docs: `docs/`.

Method: file-size triage, function-shape sampling, cross-tree import map,
test-coverage shape, existing-audit inventory. No correctness audit; no
runtime behavior was tested. Companion to
[audit/debugger_code_review_2026-05-25.md](audit/debugger_code_review_2026-05-25.md),
which covered the three debugger trees with the same methodology.

The asm side is structurally different from Python: file size matters
less because banking dominates, and the existing `tools/audit/check_*.py`
floor (65 audits) already enforces many of the patterns CLAUDE.md flags.
For asm the relevant question is "what structural patterns aren't yet
covered by audits" rather than "which files are too long."

## Direct assessment

**Python tooling has the same shape problems the debugger trees had** —
god-routers, oversized hand-written test harnesses, repeated helpers,
weak test coverage on load-bearing modules. Six concrete smells, ordered
by how much they hurt readability:

1. **`tools/headless_battle/simulator.py` is 5,072 lines of battle logic
   in one file.** Single biggest Python file outside the debugger trees.
   Not declarative data — explicit `apply_*` move handlers, status
   effects, item interactions, weather, substitutes, spikes. One
   `apply_move_after_action_check` is 239 lines. (§3)
2. **`tools/boss_ai_preference/__main__.py` is the next god-router.**
   935 lines, 24 `cmd_*` handlers + 24 `subparsers.add_parser` blocks
   inlined into a 431-line `build_parser()`. Same shape as the debugger's
   pre-refactor `__main__.py`, single-axis (formatters already live in
   subsystem modules, like the post-refactor boss_ai_debugger). (§1)
3. **Two individual audit checks are 2,287 and 2,789 lines.**
   `check_headless_battle_simulator.py` is a 2,260-line `main()`;
   `check_boss_ai_trace_invariants.py` has three functions over 200 lines
   each. Both are policy bundles where individual concerns could split
   cleanly. (§2)
4. **`tools/audit/` and `scripts/` reimplement the same helpers ~50 times.**
   `def fail`, `def load`, `def code_lines`, `def strip_comment` appear
   50 times across 34 audit files; only `asm_scan.py` (84 lines) and
   `trainer_parties.py` (144 lines) are shared. (§4)
5. **`tools/headless_battle/simulator.py:12` imports backwards from
   `tools/boss_ai_preference/data`.** Low-level battle harness depending
   on the high-level labeling system. Trivial to invert. (§5)
6. **`tools/trace/` is 7 driver scripts at 2,775 lines with zero tests** —
   the boss-AI live-capture pipeline. Same liability shape as
   pre-refactor `damage_debugger/` flagged in §5 of the debugger doc. (§7)

Two more findings are observation-only:

- **Asm side: the audit floor is dense, but one hazard class isn't covered.**
  Frame-boundary register liveness across same-bank `call` sites — the AG-08
  cascade documented at `engine/battle/late_gen_held_items.asm:13-30` is
  the most recent example. No audit yet catches the pattern, only the
  individual hand-fixed call sites. (§8)
- **Docs are healthy.** Generated-doc discipline holds; the "shipped on
  DATE" rot pattern was already retired in CLAUDE.md and an audit guards
  against backslide. One minor risk: 31 `boss_ai_*.md` files compete for
  the same intro slot. (§9)

Two of these (§1 and §4) are mechanical refactors in a single pass each.
§3 is mechanical too. §2, §5, §6, §7 are pure extractions. §8 needs
thought but is doc-first.

## Surface area in numbers

Python tooling (excluding the three debugger trees):

| Tree | Files | Lines | >400 | >700 | >1000 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `tools/audit/` | 71 | 25,121 | 14 | 7 | 5 |
| `tools/boss_ai_preference/` | 30 | 18,007 | 16 | 7 | 4 |
| `tools/headless_battle/` | 14 | 13,076 | 7 | 3 | 3 |
| `scripts/` | 12 | 5,938 | 6 | 4 | 2 |
| `tools/pokemon_mastery/` | 18 | 3,157 | 1 | 0 | 0 |
| `tools/trace/` | 7 | 2,775 | 4 | 1 | 0 |
| `tools/perf/` | 2 | 631 | 1 | 0 | 0 |
| **Total** | 154 | 68,705 | 49 (32%) | 22 (14%) | 14 (9%) |

For comparison the debugger trees were 78,338 lines / 129 files with 50%
of files past the 400-line bar. Non-debugger Python is half as concentrated
in oversized files (32% vs 50%) but the absolute totals are similar.

Top 10 individual Python offenders:

| Lines | File |
| ---: | --- |
| 5,072 | [tools/headless_battle/simulator.py](tools/headless_battle/simulator.py) |
| 2,789 | [tools/audit/check_boss_ai_trace_invariants.py](tools/audit/check_boss_ai_trace_invariants.py) |
| 2,694 | [tools/headless_battle/tests/test_simulator.py](tools/headless_battle/tests/test_simulator.py) |
| 2,681 | [tools/boss_ai_preference/benchmark_positions.py](tools/boss_ai_preference/benchmark_positions.py) |
| 2,361 | [tools/boss_ai_preference/app.py](tools/boss_ai_preference/app.py) |
| 2,287 | [tools/audit/check_headless_battle_simulator.py](tools/audit/check_headless_battle_simulator.py) |
| 1,600 | [tools/headless_battle/rom_differential.py](tools/headless_battle/rom_differential.py) |
| 1,601 | [tools/audit/check_release_smoke.py](tools/audit/check_release_smoke.py) |
| 1,565 | [tools/audit/check_gym_leader_wiring.py](tools/audit/check_gym_leader_wiring.py) |
| 1,384 | [scripts/generate_move_progression_audit_html.py](scripts/generate_move_progression_audit_html.py) |
| 1,329 | [tools/boss_ai_preference/threat_availability.py](tools/boss_ai_preference/threat_availability.py) |
| 1,175 | [scripts/generate_trainer_dossier_pdf.py](scripts/generate_trainer_dossier_pdf.py) |
| 1,175 | [tools/audit/check_boss_ai_debugger_roadmap.py](tools/audit/check_boss_ai_debugger_roadmap.py) |

ROM source (line counts are descriptive, not a flag — large asm files are
mostly data tables or banked engine code, both of which CLAUDE.md exempts):

| Tree | Files | Lines | Nature |
| --- | ---: | ---: | --- |
| `engine/` | 283 | ~136,460 | Battle, AI, events, overworld, audio, items |
| `home/` | 56 | ~12,142 | ROM0 helper library (farcall, thunks, utilities) |
| `data/` (incl. subdirs) | 968 | (data tables) | 251 per-species `base_stats/` files etc. |
| `constants/` | 43 | ~9,212 | Enums, flags, hardware registers |
| `macros/` | 19 | ~4,004 | RAM struct macros, SECTION helpers, table builders |
| `ram/` | 4 | ~3,131 | WRAM, SRAM, HRAM, VRAM layouts |

Memory state from
[docs/generated/dev_index.md](docs/generated/dev_index.md) Memory Summary
(2026-05-25 regen):

- ROM0: 15,721 used / **663 free** (99.6% full)
- ROMX: 1,149,336 used / 931,432 free across 127 banks
- WRAM0: 4,049 used / **47 free** (99.0% full)
- WRAMX: 3,711 used / 4,481 free across 2 banks
- HRAM: 127 used / **0 free**
- Tight banks: 0x12, 0x15, 0x17, 0x1b, 0x1e at 0 free; 0x0e at 12; 0x1c, 0x1f at 1

Docs:

- 762 `.md` files in `docs/` (24,439 lines in the 71 hand-written top-level docs)
- 3 generated docs in `docs/generated/` (`dev_index.md`, `balance_audit.md`,
  `boss_ai_teaching_heuristics_snapshot_*.md`)
- 8 generator scripts in `scripts/generate_*.py`

## §1 — `boss_ai_preference/__main__.py` is the next god-router

[tools/boss_ai_preference/__main__.py](tools/boss_ai_preference/__main__.py) shape:

- 935 lines, **24 `cmd_*` handlers** + **24 `subparsers.add_parser` blocks**
  (48 total hits matched by `grep -c '^def cmd_\|subparsers\.add_parser'`)
- `build_parser()` spans 431 lines (sampled around lines 128–558)
- Top of file: 60 import lines pulling in 20+ subsystem modules

Notable difference from the debugger's pre-refactor `__main__.py`: **zero
`def format_*` functions in this file** (`grep -c '^def format_'` → 0).
The formatters already live in their subsystem modules — same shape as
post-refactor `boss_ai_debugger/__main__.py`. So this is a single-axis
god-router (parsers + dispatchers inlined), not the three-axis variant
the debugger had.

**Smell:** orchestration files should be thin (CLAUDE.md anchor). Adding
a new subcommand requires touching this file in three places (import,
parser, dispatcher) plus its subsystem module. The 60-line import block
at the top is the obvious tell — when you read it you see how diffuse
the responsibility is.

**Mechanical pattern.** Every `cmd_*` follows the model docs' shape:
build a report dict via the subsystem function, emit via a shared
formatter, return 0/1 based on validity. Of 24 commands, ~22 are this
exact shape.

**Recommendation:** apply the same refactor pattern as
`boss_ai_debugger/__main__.py` from commit `d62cafec` — split into
`parsers.py` + `commands.py`, then collapse the top-level `__main__.py`
to a discovery loop. Expected post-refactor size: ~150–250 lines.
Risk-free; the boss_ai_debugger refactor preserved 211/212 tests.

## §2 — Two audit checks are 2,287 and 2,789 lines

[tools/audit/check_headless_battle_simulator.py](tools/audit/check_headless_battle_simulator.py)
is 2,287 lines. `main()` starts at line 29 and runs to end-of-file: a
single ~2,260-line function with 60+ scenario fixtures + assertion blocks
inlined sequentially. Each scenario is a 20–40 line payload dictionary
followed by an assertion block.

**Smell:** this is a parametrized test suite written as one large
function. CLAUDE.md says "if a function no longer fits on one screen or
exceeds roughly 40 lines, ask whether splitting would clarify it." 2,260
lines is 50× that. When this audit fails, finding the relevant scenario
takes scrolling.

[tools/audit/check_boss_ai_trace_invariants.py](tools/audit/check_boss_ai_trace_invariants.py)
is 2,789 lines / 46 top-level functions. Three audit functions exceed
200 lines each:

- `audit_spikes_and_status` (~lines 1100–1605, 506 lines)
- `audit_revealed_coverage` (~lines 123–353, 231 lines)
- `audit_item_and_passive_reasoning` (~lines 1923–2157, 235 lines)

**Smell:** each oversized function is a policy bundle (e.g.
`audit_spikes_and_status` mixes trainer switch logic + type coverage +
status tracking + move scoring). The file changes when any of those
policies change — multiple reasons to change, single file.

**Recommendation:**

- For `check_headless_battle_simulator.py`: convert the inlined scenario
  fixtures into a list of dicts + a small runner. Each fixture becomes
  a few lines of data + a one-line `_assert_scenario(fixture)` call.
  Expected size: ~600–900 lines, mostly data.
- For `check_boss_ai_trace_invariants.py`: split by audit family into
  three modules (`trace_rom.py`, `trace_coverage.py`, `trace_logic.py`)
  with a thin `__main__.py` that runs all three. Each module ends up
  ~700–900 lines.

## §3 — `headless_battle/simulator.py` is 5,072 lines of one battle simulator

[tools/headless_battle/simulator.py](tools/headless_battle/simulator.py)
is the single biggest Python file outside the debugger trees. Sampling
shows it handles the entire battle state machine plus every per-move
handler in one file:

| Approx lines | Function |
| ---: | --- |
| 239 | `apply_move_after_action_check` (lines 796–1034) |
| 112 | `apply_thunder_move` |
| 89 | `simulate_turn` |
| 75 | `apply_move` |
| 72 | `apply_sleep_status_move` |

It also contains move-type dispatch (lines 695–1147 are the apply_move
chain), status effects, weather, substitutes, spikes, stat-stage moves,
protection, drain, held item cures, safeguard/sleep/poison/paralysis
blocking — all sequential in one file.

**Smell:** one file = one primary reason to change, per CLAUDE.md. This
file changes when any battle mechanic changes — at least 8 independent
reasons (per-move-type, per-status, per-weather, per-item, per-side-
condition, RNG, speed ties, stat stages).

**Recommendation:** split into `tools/headless_battle/simulator/`
package with the dispatch tables (`moves.py`, `status.py`, `weather.py`,
`items.py`, `side_conditions.py`) separate from the core state machine
(`engine.py`). Test coverage stays intact because
[tests/test_simulator.py](tools/headless_battle/tests/test_simulator.py)
(2,694 lines, 50+ test methods) imports from `simulator` as a public
surface; the split is internal.

Same architecture smell, smaller scale:
[rom_differential.py](tools/headless_battle/rom_differential.py) is
1,600 lines doing ROM-vs-simulator diff. Worth splitting once
simulator.py is packaged, since rom_differential mirrors the simulator
structure.

## §4 — Audit-helper duplication: `fail`/`load`/`code_lines`/`strip_comment` written 50 times

`grep -c '^def (fail|load|code_lines|strip_comment)' tools/audit/*.py`
returns 50 occurrences across 34 files. There are two shared modules
([asm_scan.py](tools/audit/asm_scan.py), 84 lines;
[trainer_parties.py](tools/audit/trainer_parties.py), 144 lines), but
no central `audit_helpers.py` covering the generic utilities.

Sampling — each of these is its own 1–4 line definition with a slightly
different error-message prefix:

- `tools/audit/check_release_smoke.py:1` — own `def fail`
- `tools/audit/check_farcall_a_clobber.py` — own `def fail`
- `tools/audit/check_boss_ai_no_cheat.py` — own `def fail`
- … 31 more files

**Smell:** repeated policy per CLAUDE.md. The text is policy ("this is
how an audit reports failure") not coincidence. Today these can drift in
how they format the message, what exit code they return, whether they
prefix the audit name, etc.

**Recommendation:** extract a 60–80 line `tools/audit/_common.py`
exposing `fail(audit_name, message)`, `load(path)`, `code_lines(text)`,
`strip_comment(line)`. Replace 34 files' local copies with the import.
Net: ~150 lines deleted, one obvious home for "how audits report
errors." Lowest-risk item in this doc.

The same pattern shows up in `scripts/`: `manifest_changes.py` exists
as a shared utility imported by 2 scripts, but the 8 generator scripts
each reimplement `Path(__file__).resolve().parents[2]`, their own
dataclasses for Move/Pokemon/Type/Trainer, and their own ROM-parsing
helpers. A `scripts/_rom_data.py` consolidating the dataclasses + parsers
would save ~300 lines and keep the ROM model coherent across generators.

## §5 — Cross-tree backward import: simulator → preference

[tools/headless_battle/simulator.py:12](tools/headless_battle/simulator.py:12):

```python
from tools.boss_ai_preference.data import PreferenceDataError
```

`headless_battle` is a low-level battle harness used by `rom_differential`,
the switch-expectations framework, audit checks, and the trace pipeline.
`boss_ai_preference` is a high-level labeling system that imports
`headless_battle` for scenario evaluation. The current import is
backwards — `simulator` should not depend on the preference system's
exception types.

**Recommendation:** define `PreferenceDataError` (or its parent class)
in a shared location. Two options:

1. Move it into `headless_battle` if it's actually about battle-data
   contract violations.
2. Move it into a new `tools/shared/exceptions.py` if it covers more
   than headless-battle.

Trivial to fix: a single move + 2 import updates. Worth doing because
the current shape lets boss_ai_preference grow into a fat dependency on
headless_battle's behalf.

## §6 — Embedded HTML/CSS/JS in Python string literals

Two cases worth calling out:

1. [scripts/generate_move_progression_audit_html.py](scripts/generate_move_progression_audit_html.py)
   contains a `css()` function returning a 516-line CSS string literal
   (approximately lines 504–1019) and a `js()` function returning a
   62-line JS literal (1020–1081). Out of the file's 1,384 lines, 578
   are pure markup-as-Python-string.
2. [tools/boss_ai_preference/app.py](tools/boss_ai_preference/app.py)
   is 2,361 lines, of which a large block (sampled lines 47–1990, ~1,943
   lines) is embedded HTML for the local UI. The remaining ~400 lines
   are the HTTP handler.

**Smell:** no editor syntax highlighting; markup can't be reviewed or
tested independently; Python string-quoting rules complicate the HTML
(or vice versa).

**Recommendation:** move the markup into sibling files
(`scripts/move_progression_audit.css`, `tools/boss_ai_preference/app.html`)
and load via `pathlib.Path(__file__).parent / "x.css"`. Either or both
generator scripts can be patched in 15 minutes each with no behavior
change. After the move, `app.py` shrinks to ~500 lines.

## §7 — Test asymmetry: `tools/trace/` has zero tests on the boss-AI audit pipeline

| Tree | Src files | Test files | Notes |
| --- | ---: | ---: | --- |
| `tools/boss_ai_preference/` | 23 | 6 | OK |
| `tools/headless_battle/` | 8 | 5 | Good, but tests are coarse (one 2,694-line test_simulator.py) |
| `tools/pokemon_mastery/` | 11 | 6 | Good ratio + loop semantics |
| `tools/perf/` | 2 | 0 | No tests; benchmark-only tree |
| `tools/trace/` | 7 | 0 | **None.** Boss-AI live-capture pipeline. |
| `tools/audit/` | 71 | 1 (a single self-test) | Audits are run in CI; not unit-tested |

The most concerning is `tools/trace/`. Seven driver scripts (2,775 lines)
power the boss-AI trace pipeline used by `MEGAURGENT-001` and `VERIFY-001`
in [docs/project_roadmap.md](docs/project_roadmap.md). The drivers include
`boss_ai_state_factory.py` (884 lines, generates synthetic battle states)
and `boss_ai_trace_capture.py` (456 lines, reads WRAM after PyBoy
execution). Zero tests means: no regression detection if a module breaks,
no documented examples of how to use the drivers, no validation that
state factory outputs are well-formed.

Same liability shape as the debugger audit's §5 finding on
`damage_debugger/`. The mitigation suggested there ("backfill at least
the four modules that other debugger trees import") applies analogously:
test the state factory and the trace capture at minimum.

Separately: `tools/audit/`'s test coverage is by-design (audits run as
CI gates, not unit-tested) but worth flagging because the two largest
checks (§2) are exactly the kind of code that would benefit from
parametrized test fixtures.

## §8 — Asm side: dense audit floor, one uncovered hazard class

`tools/audit/check_*.py` is 65 files. Sampled the safety-critical ones:

- `check_cross_bank_call.py` — plain `call`/`jp` to a label in another
  bank (the May 2026 cross-bank-softlock class). 39 hits in
  `engine/battle/ai/boss.asm` were fixed by routing through
  [engine/battle/ai/boss_thunks.asm](engine/battle/ai/boss_thunks.asm)
  (82 lines, 7 hl-preserving thunks at lines 33–82, commit `f2e18554`).
- `check_farcall_hl_clobber.py` — caller's hl clobber pre-target
  (the April 2026 one-shot-damage class). Auto-discovers hl-input
  functions by header marker comment.
- `check_farcall_a_clobber.py` — target's `a` lost via `c`-pass-through
  (the May 2026 wild-floor no-op class). Promoted to the release-smoke
  floor 2026-05-04 after surfacing 5 latent bugs.
- `check_release_smoke.py` — 1,601-line broad-spectrum smoke audit.
- `check_layout_orgs.py`, `check_pic_bank_pressure.py`,
  `check_rsvbk_write_discipline.py`, `check_save_format_version.py` —
  ROM-layout and save-format gates.
- 12 boss-AI-specific audits (no-cheat, gating, memory budget, trace
  invariants, policy contract).

**The audit floor is dense. CLAUDE.md and `docs/asm_authoring_guide.md`
together encode most of the load-bearing patterns.** The interesting
finding is what isn't covered:

**Frame-boundary register liveness across same-bank `call` sites.** The
canonical example is documented at
[engine/battle/late_gen_held_items.asm:13-30](engine/battle/late_gen_held_items.asm:13):
the AG-08 fix (`a6a00ea8`) added `ld c, a` after `pop bc` in
`TypePassive_GetEffectiveMoveCategory_Far` to mirror move-type into `c`
for cross-bank farcallers per the farcall-a-passthrough rule. AG-08
claimed same-bank callers were unaffected because they consume `a`
immediately via `cp SPECIAL`. **That was true for `a` but wrong for `c`** —
PlayerAttackDamage / EnemyAttackDamage carry `bc` = defender def bytes
through this function into `TruncateHL_BC`, and the new `c` write
overwrote the def low byte, producing ~9× damage masked as "5× physical
damage" with STAB. The fix was push/pop bc at the same-bank call site.

This is the same hazard family as `44ca3b29` (the `GetUserItem` de-clobber
from `_GetSidedHL` extraction). Both are transitive register-preservation
failures where a local edit silently broke a caller many frames away.
`check_farcall_a_clobber.py` catches the cross-bank version; nothing
catches the same-bank version. The fix at line 32 is per-site push/pop,
which is correct but doesn't scale — the next refactor that touches a
hot battle helper can reintroduce the class.

**Recommendation:** rather than write a new linter (frame-boundary
register flow analysis is hard), make this a CLAUDE.md +
`docs/asm_authoring_guide.md` policy update:

- Add §3.15 to the asm guide describing same-bank transitive register
  clobber as a sibling of §3.13–§3.14.
- For high-risk modules (`engine/battle/`, `engine/battle/ai/`), require
  running `tools.damage_debugger.clobber_smoke` after any refactor that
  changes a function's register-write set. The verification floor
  (asm guide §6) already mentions this for ABI-changing fixes; expand
  it to cover same-bank `call` sites at minimum.
- Consider extending `check_farcall_a_clobber.py` to also walk back from
  same-bank `call` sites whose caller reads bc/de/hl post-call. The
  callee may not have a `ret`-side mirror to find, but the symmetry of
  the rule still applies: any write the callee performs to a register
  the caller subsequently reads is a hazard.

This is doc-and-tooling work, not asm work. No file in `engine/` needs
to change for this finding.

## §9 — Docs are healthy

762 `.md` files in `docs/`. Generated-doc discipline holds:

- `docs/generated/dev_index.md`, `balance_audit.md`, and
  `boss_ai_teaching_heuristics_snapshot_*.md` are the only generated
  docs. All three regenerate from `scripts/generate_*.py` (8 generators
  total). Git history shows only natural address/line diffs from
  rebuilds, never hand-authored prose insertions.
- The "shipped on DATE" pattern CLAUDE.md noted as rotted is gone from
  tracked docs; `tools/audit/check_no_stale_shipped_claims.py` exists
  as a guard.
- `.claude_handoffs/` is gitignored as expected; not visible in tracked
  state.

Minor risks worth knowing about, not urgent:

1. **31 `boss_ai_*.md` files** at the top level of `docs/`. Sample:
   `boss_ai_spec.md`, `boss_ai_bug_testing_plan.md`, `boss_ai_lessons_*.md`,
   `boss_ai_debugger_*.md`, plus the `pokemon_mastery/` coaching corpus.
   Routing through `docs/README.md` + `docs/agent_navigation/task_router.md`
   mitigates the "which is the intro?" hesitation but doesn't eliminate
   it. **Observation only** — splitting them by purpose (`spec/`, `testing/`,
   `lessons/`, `debugger/`) inside `docs/` is a possible follow-up but
   not load-bearing.

2. **Some generator scripts lack documented refresh triggers.**
   `docs/agent_navigation/source_output_ownership.md` lists the
   generators but not every regenerate-when condition. CLAUDE.md
   specifies "after **any** successful build that links" for
   `dev_index.md` and "balance/stats/evos changes" for `balance_audit.md`,
   but the boss-AI snapshot and PDF generators don't have explicit
   triggers documented. Low-risk follow-up.

3. **`docs/pokemon_mastery/` is 667 files** of hand-written training
   corpus. Intentionally separate from canonical game docs; verified by
   spot-check against artifact catalog. No action needed.

## §10 — Maps / gfx / audio: no structural smell

Quick scan only.

- 607 map `.asm` files. Beta/unused-script discipline is clean: 172
  unreferenced movement/text/script blocks carry explicit
  `; unreferenced` markers (`UnusedWoosterScript`,
  `CeladonPokecenter2FBeta_MapScripts`, etc.). These are intentional
  sediment from pret's disassembly, not leakage.
- 1,526 `.png` sources + 6,032 `.2bpp.*` intermediates. Pipeline is
  consistent: PNG sources → `.2bpp.lz` compressed → `.o` build objects.
  No stray hand-edited `.2bpp` files in tracked state.
- 101 audio files. Clean structure; `music/`, `sfx.asm`, `cries.asm`
  with pointers/engine stubs intact.
- 43 `data/tilesets/*` data definitions. Dual-track (Johto + modern)
  with explicit unused-layer markers (`UnusedTilesetJohtoMeta`,
  `UnusedTilesetJohtoColl`).

**Verdict: no structural red flags. Historical sediment and beta
variants are explicitly classified.**

## Prioritized recommendations

Ordered by ratio of (reader-pain reduced) / (refactor risk):

1. **Extract `tools/audit/_common.py`.** (§4) ~60 lines of shared
   `fail`/`load`/`code_lines`/`strip_comment` replacing 34 copies. Pure
   deletion win, zero behavior change. Lowest risk in this doc, highest
   leverage per minute. Ship in one PR.
2. **Invert the simulator → preference import.** (§5) One-line move of
   `PreferenceDataError`. Trivial. Ship as a 5-minute PR; clears the
   path for §3's split.
3. **Split `boss_ai_preference/__main__.py` into `parsers.py` +
   `commands.py`.** (§1) Mechanical, behavior-preserving, same pattern
   as `boss_ai_debugger/__main__.py` from `d62cafec`. Expected
   post-refactor size: 150–250 lines.
4. **Extract embedded HTML/CSS from `scripts/generate_move_progression_audit_html.py`
   and `tools/boss_ai_preference/app.py`.** (§6) Mechanical move to
   sibling files. ~2,500 lines of Python shrink to ~1,000 with cleaner
   markup ownership.
5. **Convert `check_headless_battle_simulator.py`'s 2,260-line `main()`
   into a fixtures list + runner.** (§2) Each fixture becomes data;
   the audit body shrinks dramatically. Same shape works for any future
   parametrized audit.
6. **Backfill `tools/trace/` tests** for at least `boss_ai_state_factory.py`
   and `boss_ai_trace_capture.py`. (§7) Different shape (real test
   writing, not refactoring); may warrant its own session like the
   debugger doc's parallel item 5.
7. **Split `tools/headless_battle/simulator.py` into a package by
   concern.** (§3) Bigger move but every battle-mechanic edit would
   benefit. Save for when someone next touches a move handler — when
   that happens, the split is then non-speculative.
8. **Split `check_boss_ai_trace_invariants.py` by audit family.** (§2)
   Mechanical, behavior-preserving. Defer unless adding a new audit
   family.
9. **Add asm guide §3.15 + verification-floor expansion for same-bank
   transitive register clobber.** (§8) Doc-and-tooling. No code changes.
   Worth doing before the next refactor of a hot battle helper.
10. **Consolidate `scripts/_rom_data.py` for the 8 generator scripts.**
    (§4) Lower priority than #1 because the duplication is less
    visible; pick up when next touching any generator.

Items 1–4 are single-pass mechanical refactors. Items 5–8 require more
thought but are scoped. Items 9–10 are doc-and-tooling work.

## Active workstreams to avoid colliding with

Before recommending big moves, checked
[docs/project_roadmap.md](docs/project_roadmap.md) and `git branch -a`:

- **TECHDEBT-001** (open): AG-NN / TD-### track has 4 open + 4 partial
  items. AG-03's 39 boss.asm cross-bank-call thunks (commit `f2e18554`)
  are gated on trace-ROM manifest refresh. **Don't recommend re-thunking
  or moving `boss_thunks.asm`** until the manifest is refreshed.
- **BOSSAI-001** (IN_PROGRESS): boss-AI live-capture validation depends
  on `tools/trace/`. The trace pipeline is what §7's test backfill
  protects; any test backfill should respect the current manifest
  shape rather than reshape it.
- **BOSSAI-003 / BOSSAI-004** (COMPLETE, V2 planned): `tools/boss_ai_preference/`
  is feature-complete at V1 but `docs/boss_ai_rlhf_v2_implementation_plan.md`
  documents a V2 (active query queue, structured lessons,
  counterfactual fixtures, offline preference model, proposal reports).
  §1's parser-split is V2-compatible; §6's HTML extraction is too.
  **Don't propose deeper refactors to `boss_ai_preference/` modules
  beyond those two without checking the V2 plan.**
- **Boss AI rebuild (shelved 2026-05-05)**: per
  `memory/project_boss_ai_rebuild_shelved.md`, BOSSAI-003 + BOSSAI-004
  paused; simpler architecture surfaced. Treat any structural smell in
  `engine/battle/ai/` as observation only.

Two pre-existing audit-violation commits sit on `master` ahead of
`origin/codex/cleanup-gsc-rebalance-split`:

- `e532da2c` — boss_ai: primary-threat register fix + curse/pain-split
  gates + haki oracle rework
- `7c1e918c` — battle: fix pinsir double-edge HP-bar overflow
  (cherry-pick `fafd3ed1`)

These were noted in the session brief; this audit does not address them.
Master is 113 commits ahead of the dev tip overall; the bulk of those
are the verified debugger refactor + balance/audit work that landed in
the last ~3 weeks.

## What I did *not* check

- Correctness of any single function. This is a structure review only.
- Whether `tools/headless_battle/simulator.py` actually simulates the
  ROM correctly (the differential exists; running it was out of scope).
- Behavior of `tools/boss_ai_preference/` end-to-end (the V2 plan
  references features I did not validate).
- Whether every generator script in `scripts/` produces the output
  it claims. CLAUDE.md and `docs/agent_navigation/source_output_ownership.md`
  document the contracts; I confirmed the contracts exist, not that
  each script honors its contract.
- ROM build correctness on Windows/WSL. `make compare` was not run.
- Audit-floor pass rate. Did not run `tools/audit/check_release_smoke.py`
  or any other audit during this review.
- Map-asm-level correctness, gfx asset correctness, or audio playback.

A correctness review would want a different methodology — running the
audit floor, running the simulator differential against a fresh ROM
build, running representative `boss_ai_preference` commands. Those are
separate tasks.

## Execution status

**Shipped (2026-05-26):**

- **Item 1 — `tools/audit/_common.py`.** New 38-line module with the
  canonical `fail` / `load` / `strip_comment` / `code_lines` and
  re-exported `ROOT`. 16 audit files migrated to sibling-style
  `from _common import …` (matching the established `import asm_scan`
  pattern in `check_vram_request_contract.py:17-20`). Net: −83 lines
  across the audit tree (115 deletions / 32 insertions in 16 audits,
  +38 in `_common.py`).

  Five files were deliberately NOT migrated for `fail`: they carry
  intentional behavior drift (write to `sys.stderr`, use the `ERROR:`
  prefix instead of `FAIL:`, or call `sys.exit(1)` instead of raising
  `SystemExit`). Local defs kept; `_common.py` header documents the
  exemption.

  Verification: `python tools/audit/check_release_smoke.py` PASS
  (all 24 sub-audits green). Spot-checked
  `check_layout_orgs.py`, `check_pic_bank_pressure.py`,
  `check_save_format_version.py`, `check_boss_ai_memory_budget.py`,
  `check_boss_ai_trace_invariants.py` individually — all PASS.
  Pre-existing FAIL on `check_wramx_bank1_relief.py` ("Boss AI reserve
  pad is 29 bytes; expected 36") reproduces against `HEAD~` without my
  changes (the audit's expected constant lagged commit `1c256cb4`'s
  WRAMX-bank-1 relief); not caused by this work.

- **Item 2 — Invert `simulator → preference` import.** (§5)
  `tools/headless_battle/simulator.py` no longer imports
  `PreferenceDataError`. The exception class is a `ValueError`
  subclass ([tools/boss_ai_preference/data.py:74](tools/boss_ai_preference/data.py:74))
  so the existing `except (KeyError, PreferenceDataError, ValueError)`
  at line 3221 already double-covered it; the explicit reference is
  redundant. 2-line diff: drop the import + drop `PreferenceDataError`
  from the catch tuple. `tools/headless_battle/` is now decoupled from
  `tools/boss_ai_preference/`.

  Verification: 135/135 simulator tests OK,
  `python tools/audit/check_headless_battle_simulator.py` PASS (27/27
  scenarios within expected damage ranges).

- **Item 4 — Extract embedded HTML/CSS/JS.** (§6) Two extractions
  in one commit.

  `scripts/generate_move_progression_audit_html.py`: the 516-line
  `css()` body and 56-line `js()` body moved to
  `scripts/assets/move_progression.css` and
  `scripts/assets/move_progression.js`. The two functions shrink to
  one-line `read_text(encoding="utf-8")` calls. Generator size:
  1,384 → 815 lines (-569).

  `tools/boss_ai_preference/app.py`: the 1,989-line `HTML = """…"""`
  constant moved to `tools/boss_ai_preference/app.html`. `app.py`
  size: 2,361 → 372 lines (-1,989, 84% reduction).

  Verification: `python scripts/generate_move_progression_audit_html.py`
  succeeds and produces 292,179 bytes of HTML output (vs the
  committed 292,181 baseline — diff is 2 bytes of whitespace inside
  the `<style>` block, semantically identical; the committed
  baseline output is not regenerated in this commit because the data
  has separately drifted since `6625a5a2` and a regen would mix
  whitespace and balance line-citation changes). `python -m unittest
  discover tools.boss_ai_preference.tests` → 32/33 (same pre-existing
  failure as item 3). `python tools/audit/check_release_smoke.py`
  → PASS.

- **Item 3 — Split `boss_ai_preference/__main__.py`.** (§1) Applied the
  d62cafec pattern that fixed `boss_ai_debugger/__main__.py`. Old
  935-line `__main__.py` (24 inlined `cmd_*` handlers + 24
  `subparsers.add_parser` blocks + a 283-line `build_parser`) is now
  three files: `__main__.py` (18 lines — just `main()` + entrypoint
  guard with `PreferenceDataError` exit-wrap), `parsers.py` (440 lines
  — `path_arg`, `add_common_paths`, `add_trajectory_paths`,
  `add_include_trajectories_arg`, `add_v2_metadata_args`, and the full
  `build_parser` body, with imports focused on the
  `DEFAULT_*`/`ALLOWED_*` constants used as argparse defaults +
  `from .commands import cmd_*`), `commands.py` (597 lines — the 24
  `cmd_*` handlers + their helpers `metric_label`,
  `v2_metadata_kwargs`, and the full subsystem import block).

  Verification: `python -m tools.boss_ai_preference --help` registers
  all 24 subcommands. `python -m unittest discover
  tools.boss_ai_preference.tests` → 32/33 OK (1 pre-existing failure
  on `test_benchmark_harvest::test_harvest_finds_complete_fixture_derived_candidates`:
  `assertEqual(report["fixture_count"], 57)` against actual 59 — A/B
  verified against `HEAD~` via `git stash`, fixture count drift, not
  caused by this refactor; same stale-fixture issue surfaces in
  `tools/audit/check_boss_ai_preference.py` independently).
  `python tools/audit/check_release_smoke.py` → PASS.

**Remaining items, ranked by leverage:**

4. **Extract embedded HTML/CSS** from
   `scripts/generate_move_progression_audit_html.py` and
   `tools/boss_ai_preference/app.py`. (§6)
5. **Convert `check_headless_battle_simulator.py`'s 2,260-line `main()`
   into a fixtures list + runner.** (§2)
6. **Backfill `tools/trace/` tests.** (§7)
7. **Split `tools/headless_battle/simulator.py` into a package.** (§3)
8. **Split `check_boss_ai_trace_invariants.py` by audit family.** (§2)
9. **Add asm guide §3.15 + verification-floor expansion for same-bank
   transitive register clobber.** (§8)
10. **Consolidate `scripts/_rom_data.py` for the 8 generator scripts.** (§4)
