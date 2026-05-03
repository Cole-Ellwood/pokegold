# Tech Debt Report — IMMUTABLE

**Compiled:** 2026-05-02
**Author:** Opus 4.6 audit pass (5 parallel explore agents over the
codebase, build system, docs, engine code, and ROM/RAM layout).
**Status:** This document is the **10 commandments**. Do not edit. Future
agents check their work against this baseline. New findings discovered
later go in `TECH_DEBT_REPORT_ADDENDUM.md`, never here.

If a finding turns out to be wrong, log it in `AGENT_LOG.md` as `disputed:`
with evidence — the human reconciles, this file does not change.

---

## Severity scale

- **CRITICAL** — actively constrains development OR risks silent breakage of
  shipped saves/ROMs.
- **HIGH** — significant maintenance burden; large code volume affected;
  blocking refactor of related areas.
- **MEDIUM** — measurable cost (bytes, readability, build time) but no
  active risk.
- **LOW** — cosmetic, contained, low-impact.

---

## CRITICAL

### TD-001 — ROM bank exhaustion (11 banks at 0-6 bytes free)

Multiple ROM banks have effectively zero free space. Any growth in the
related code or data has nowhere to go without a bank-layout change.

| Bank | Free bytes | Contents (summary) |
|------|------------|--------------------|
| HRAM | 0 | Hardware temp variables — completely full |
| ROMX 12 | 0 | Picture data — immovable |
| ROMX 15 | 0 | Picture data |
| ROMX 17 | 0 | Picture data |
| ROMX 1b | 0 | Picture data |
| ROMX 1e | 0 | Picture data |
| WRAMX 01 | 0 | Boss AI state — reserve only 36 bytes (17 with `BOSS_AI_TRACE`) |
| ROMX 1c | 1 | Picture data |
| ROMX 1f | 1 | Unown picture pointers |
| ROMX 1a | 4 | Picture data |
| ROMX 0d | 6 | Battle engine code |
| ROMX 0e | 6 | Boss AI + Late-Gen Held Items + Type Passives co-located |

The most dangerous of these is bank 0x0e — it co-locates three large
battle subsystems (`engine/battle/ai/boss.asm`, `late_gen_held_items.asm`,
`type_passive_damage_mods.asm`) in 6 free bytes. Any non-trivial edit to
boss AI risks link failure with no obvious migration path.

This is a **strategic constraint**, not a single localized fix. It is
addressed indirectly by TD-005 (recover bytes via dedup), TD-007 (prune
dead labels in tight banks), and possibly bank-layout reorganization.

### TD-002 — Legacy save format v1→v2 cleanup deferred

Three locations accept `$FF` as "legacy save predating the version marker."
All are explicitly marked "v2+ must remove this." The next
`SAVE_FORMAT_VERSION` bump must strip these accept paths or shipped saves
will silently re-corrupt.

Locations:
- `constants/misc_constants.asm:34-37`
- `engine/menus/save.asm:640`
- `engine/menus/save.asm:668`
- `ram/sram.asm:105`
- `ram/sram.asm:175` (related comments)

Currently harmless. The risk is that the cleanup gets forgotten when the
version finally bumps — this finding exists to prevent that.

### TD-003 — Hard-coded `org` addresses in `layout.link`

Multiple banks pin sections to specific addresses, leaving no slack for
ROM growth.

- Bank 0x12: `org $4000` for "Pic Pointers" + "Pics 1"
- Bank 0x1f: `org $4000` for "Unown Pic Pointers" + "Pics 12"
- Bank 0x2e: `org $6300` for "bank2E" after "Pics 14"
- Bank 0x31: `org $7a40` for "bank31" after "Sprites 2"
- Bank 0x7f: `org $7df8` for "Stadium 2 Checksums" + `ds $208`

The Stadium 2 checksum pin at `$7df8` is the most fragile — ROM growth in
bank 0x7f past that point silently corrupts checksum data with no
build-time warning. Any layout reshuffle that affects these banks must
verify checksum integrity post-build.

---

## HIGH

### TD-004 — `engine/battle/ai/boss.asm` is 7,006 lines, monolithic

Single file containing 152 routines and 560 local labels. Type-inference,
move-selection, stat-prediction, score evaluation, and setup-boost
heuristics are all interleaved. No individual component can be tested,
read, or modified in isolation.

This is the single largest maintenance burden in the project. Splits along
concern boundaries (e.g. `boss_typing.asm`, `boss_scoring.asm`,
`boss_setup.asm`, `boss_state.asm`) are feasible but require care for
local-label scope and bank co-location.

### TD-005 — Duplicated boilerplate (~500-700 bytes recoverable)

Three boilerplate patterns repeat across the battle engine, each dozens
of times:

1. **Item-check-and-return** (`push hl` / `push bc` / `callfar GetUserItem` /
   `pop bc` / `pop hl` / `cp HELD_*` / `ret nz`) — 12 instances in
   `late_gen_held_items.asm` alone. 8 instructions × 12 = ~96 bytes
   recoverable via macro.
2. **Multiply/divide setup** (zero `hMultiplicand`, load operands, `call
   Multiply`, copy product to `hDividend`, load divisor, `call Divide`) —
   18 instances across `late_gen_held_items.asm`,
   `type_passive_damage_mods.asm`, `experience.asm`. Largest single lever.
3. **`hBattleTurn` side-branch** (`ldh a, [hBattleTurn]` / `and a` / `jr z,
   .player` / load enemy addr / `jr .got` / `.player` / load player addr /
   `.got`) — 100+ instances project-wide.

Plus localized duplication: `.copy_possible_loop` and `.copy_likely_loop`
in `boss.asm:4927-4947` are byte-identical loops; `_Far` and local copies
of type-contribution helpers in `type_passive_damage_mods.asm:230-285` vs
`445-495`.

Total estimated recovery: 500-700 bytes. This is the **primary lever** for
relieving TD-001 bank pressure.

### TD-006 — Magic numbers in balance-critical code

Balance-tuning values embedded as raw literals with no named constants.
These are exactly the values future playtest passes will want to adjust;
raw hex/decimal makes that error-prone.

- `engine/battle/type_passive_damage_mods.asm:950-955` — paralysis failure
  rates: raw `25`, `41`, `40`, `21`, `20`. No `BASELINE_PARALYSIS_FAIL_PCT`
  or similar.
- `engine/pokemon/experience.asm:56-58, 92-94` — nibble masks `$f0`, `$7f`.
- `engine/pokemon/experience.asm:198-206` — `.NextJohtoGymCaps` table:
  `db 14, 17, 21, 26, 34, 34, 34, 39` with no per-gym labels in the
  asm itself (the comment above maps them, but the data is unlabeled).

---

## MEDIUM

### TD-007 — 419 unreferenced labels across the codebase

Inherited from upstream pret/pokegold disassembly. Most are harmless
historical content, but they occupy ROM bytes in banks now at 0 free.

Categories (from explore-agent enumeration, see `FINDINGS_DETAIL.md`):
- **48** beta map block labels (`Beta*_Blocks`)
- **100+** unused map scripts/text (`Unused*Script`, `Unused*Text`)
- **10+** dead battle utilities (`GetHalfHP`, `SwapBattlerLevels`,
  `HandleSafariAngerEatingStatus`, `FillEnemyMovesFromMoveIndicesBuffer`,
  `PlayerPickedUpPayDayMoney`, etc.)
- Dead audio channel overrides (`audio/engine.asm:335,387,486`)
- Unused menu/UI utilities (`Menu_DummyFunction`,
  `PlaceGenericTwoOptionBox`, `GetNthMenuStrings`)
- Unused text commands (`GameFreakText`, `DummyChar`, `PokeFluteTerminator`,
  `TextCommand_CRY`)
- Stale reward text labels (`*ReceivedTM*`, `*ReceivedHM*`) — already
  guarded by `check_release_smoke.py`

Selective pruning is high-value for tight banks (TD-001), low-value
elsewhere.

### TD-008 — RGBDS v1.0.1 — pinned 5 years ago

Toolchain version hardcoded in `.github/workflows/main.yml:9,22,78`,
`CLAUDE.md`, and local build instructions. RGBDS has had multiple releases
since 2021. Not a correctness issue today, but the upgrade gap grows.

### TD-009 — Unused RAM fields (~30 bytes total)

Dummied-out fields from removed legacy features. Not actively harmful but
the 24-byte `wUnusedMapBuffer` is real WRAM space sitting idle.

Confirmed unused (no engine references):
- `wUnusedBCDNumber` (`ram/wram.asm:17`) — "BCD value, dummied out"
- `wUnusedScriptByte` (`ram/wram.asm:120`)
- `wUnusedMapBuffer` (`ram/wram.asm:272-273`) — 24 bytes
- `wUnusedGameboyPrinterSafeCancelFlag`
- `wUnusedPikachuFrameset`
- `wUnusedJigglypuffNoteXCoord`
- `wUnusedMysteryGiftStagedDataLength`
- `wUnusedLinkAction`
- `wUnusedPokedexByte`
- `wUnusedPokegearByte`
- `wUnusedBillsPCData` (3 bytes)
- `wUnusedMovementBufferBank`, `wUnusedMovementBufferPointer`
- `hUnusedByte` (`ram/hram.asm:31`)
- `hUnusedBackup` (`ram/hram.asm:157`)

`wUnusedMusicF9Flag` has writes in `audio/engine.asm` but no reads —
write-only flag, also dead.

Confirmed actually-used (do **not** remove): `wUnusedSlotReelIconDelay`
(slot machine), `wUnusedSGB1eColorOffset` (SGB layouts),
`wUnusedNamesPointer` (link init).

### TD-010 — `.gitignore` cruft

~10 entries for paths that don't exist in the repo:
- `rgbds-1.0.1/` (vendored elsewhere; gitignored anyway)
- `rgbds-win64.zip`, `rgbds-win64*.zip`, `rgbds-*/`
- `.local/`
- `.claude_handoffs/`
- `.rebalance_chain/`
- Lines 54-56 duplicate the `.sav`/`.rtc`/`.state` patterns already on
  lines 51-53.

Cosmetic only. Signals lack of recent maintenance pass.

---

## LOW

### TD-011 — Likely-unused script

`scripts/export_changes_by_category.py` — no references in docs, audits,
CI, or the generator pipeline. Either resurrect with a clear purpose
documented or delete.

### TD-012 — Makefile shell hacks

`Makefile` uses raw shell pipes for things that could be proper rules:
- Lines 248-249: `cp -f $^ $@` for back-sprite duplication (Gold/Silver
  share identical back sprites).
- Lines 279-281: `cat $^ > $@` for binary concatenation (intro fire
  graphics).
- Lines 353-354: `tr < $< -d '\000' > $@` for SGB tilemap null-byte
  stripping.

Functional. Fragile if filenames or RGBDS behavior changes. Low priority.

### TD-013 — `engine/pokemon/experience.asm` stack gymnastics

`CalcExpAtLevel` uses 10+ push/pop pairs to manage intermediate cubic +
quadratic terms across the BCD arithmetic (lines 82-160). Correct but
hard to follow if the formula ever needs changing. A dedicated math
helper or a refactor using `hMultiplicand`/`hDividend` consistently
throughout would clarify intent.

---

## What is NOT tech debt (good news, recorded for completeness)

These were checked and found clean. Do not list them as findings.

- **Documentation is current.** All docs cross-reference correctly,
  generated files are freshly rebuilt (2026-05-02), roadmap evidence
  artifacts all exist. `docs/manual_qa_backlog.md` items pending playtest
  are intentional, not stale.
- **No circular include dependencies.** Include chain in `includes.asm` is
  clean and well-ordered.
- **No unsafe bank-switching.** All bank switches use proper macros that
  update `hROMBank`. No direct writes to `$2000-$3FFF` outside linker.
- **No orphaned constants.** Everything in `constants/` is referenced.
- **Audit tooling is comprehensive.** 19 audit scripts, none broken or
  redundant, covering AI, balance, memory, docs, release gates.
- **Only 1 active TODO** in the project (`TODO-005` Morty gym scout
  dossier prototype — tracked in `docs/project_completion_todo.md`).

---

## Index

| ID | Severity | Title |
|----|----------|-------|
| TD-001 | CRITICAL | ROM bank exhaustion (11 banks at 0-6 bytes free) |
| TD-002 | CRITICAL | Legacy save format v1→v2 cleanup deferred |
| TD-003 | CRITICAL | Hard-coded `org` addresses in `layout.link` |
| TD-004 | HIGH | `boss.asm` is 7,006 lines, monolithic |
| TD-005 | HIGH | Duplicated boilerplate (~500-700 bytes recoverable) |
| TD-006 | HIGH | Magic numbers in balance-critical code |
| TD-007 | MEDIUM | 419 unreferenced labels across the codebase |
| TD-008 | MEDIUM | RGBDS v1.0.1 pinned 5 years ago |
| TD-009 | MEDIUM | Unused RAM fields (~30 bytes total) |
| TD-010 | MEDIUM | `.gitignore` cruft |
| TD-011 | LOW | Likely-unused script `export_changes_by_category.py` |
| TD-012 | LOW | Makefile shell hacks |
| TD-013 | LOW | `experience.asm` stack gymnastics |

End of immutable report.
