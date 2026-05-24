# WRAMX Bank 1 Relief Audit - Codex Scratchpad - 2026-05-24

Status: complete read-only audit. Core plan frees an estimated 544 bytes from WRAMX bank 1, above the 410-byte floor. Stretch plan reaches 634 bytes. Boss AI battle-intelligence impact for the counted core is none.

Scope: read-only audit of WRAMX bank 1, with source edits forbidden. This file is Codex's scratchpad; do not use Claude's `journal/2026-05-24_wram_relief_scratchpad.md`.

Write set used:
- `journal/2026-05-24_wram_relief_codex_scratchpad.md`
- `tools/scratch_codex/wramx_bank1_audit.py`

No-write set respected:
- `engine/`, `ram/`, `data/`, `home/`, `audio/`, `gfx/`, `maps/`, `constants/`, `docs/`
- `tools/` except new `tools/scratch_codex/`

I did not read or write Claude's `journal/2026-05-24_wram_relief_scratchpad.md`.

## Evidence and Commands

- **repo-proven** `git status --short` shows many pre-existing dirty AI/docs/tool files and Claude's untracked scratchpad. I did not rely on or modify them.
- **repo-proven** `CLAUDE.md` says WRAM/SRAM offsets are high-caution save-format surfaces; WRAMX is bank-switched; Boss AI state lives in WRAMX bank 1 with a fixed reserve; generated docs are not hand-edited.
- **repo-proven** `docs/generated/dev_index.md` reports WRAMX bank 1 at 0 bytes free and Boss AI reserve free space at 36 bytes normal / 9 bytes with `BOSS_AI_TRACE`.
- **repo-proven** `python tools/scratch_codex/wramx_bank1_audit.py` parses `pokegold.map`, `pokegold_trace.map`, and `constants/event_flags.asm`; I separately read the relevant `ram/wram.asm` declarations field-by-field.
- **repo-proven** normal build WRAMX bank 1 sections total 4096 bytes: `WRAM 1` 417, `Game Data` 2177, `Party` 1247, `Stack` 255. `TOTAL EMPTY: $0000`.
- **repo-proven** WRAMX bank 2 contains only `Boss AI WRAMX2 Buffer` at 26 bytes, leaving 4070 bytes empty.
- **repo-proven** `ram/sram.asm` and `engine/menus/save.asm` raw-copy `wPlayerData3` and `wPokemonData` into SRAM, so moving/deleting saved fields requires save-format work.
- **repo-proven** `Makefile` uses `RGBFIXFLAGS += -cjsv`, so the current ROM is CGB-compatible plus SGB-compatible, not CGB-only.
- **repo-proven** `home/wram_bank.asm` warns callers must bracket atomic switch/access/restore themselves; `engine/battle/ai/observation_log.asm` uses inline `rSVBK/hWRAMBank` writes because `SetWRAMBank` cannot safely return after switching away from bank 1 while the stack is in WRAMX bank 1.
- **primary-reference** Pan Docs says CGB `SVBK` maps WRAM banks 1-7 into `$D000-$DFFF`, bank 0 aliases bank 1, and CGB features require an appropriate header byte. See https://gbdev.io/pandocs/CGB_Registers.html.
- **primary-reference** Pan Docs says interrupt handling pushes the current PC onto the stack before jumping to the handler. See https://gbdev.io/pandocs/Interrupts.html.

## WRAMX Bank 1 Field Audit

These are allocation fields/groups from `ram/wram.asm` verified against `pokegold.map` / `pokegold.sym`. Sizes below are bank-1 bytes unless noted.

| Area | Range | Bytes | Audit result |
| --- | ---: | ---: | --- |
| `SECTION "WRAM 1"` | `$d000-$d1a0` | 417 | Hot shared runtime. Not a good relief target without behavioral work. |
| Item/menu cursors, `wTempMon`, warp args | `$d000-$d048` | 73 | Hot helpers and temp mon struct; leave. |
| `wTrainerBattleContextBackup` + active byte | `$d049-$d059` | 17 | Battle state backup; leave. |
| `wUnusedAddOutdoorSpritesReturnValue` | `$d05a` | 1 | Tiny unused byte; not counted. |
| Map/tile connection state through `wForceEvolution` | `$d05b-$d0d2` | 120 | Overworld/map hot state; leave. |
| Overlay union at `$d0d3` (`wEnemyAIMoveScores`, HP anim, field move, link RNG, etc.) | `$d0d3-$d0ec` | 26 | Already structurally shared by `UNION`; no bank-1 win without feature-specific surgery. |
| Enemy/temp battle/base-data/script state | `$d0ed-$d198` | 172 | Battle/map hot state; leave. |
| Options/save-exists/textbox/GB printer anchor/options2 | `$d199-$d1a0` | 8 | Saved options; only 1 clear unused anchor (`wGBPrinterBrightness`), too small and save-format-bearing. |
| `SECTION "Game Data"` | `$d1a1-$da21` | 2177 | Main save/runtime data. Best bank-1 relief is here and in `Party`. |
| `wPlayerData1` identity/time/follow/object structs | `$d1a1-$d404` | 612 | Saved + overworld hot; leave. |
| `wCmdQueue` | `$d405-$d444` | 64 | Runtime queue; leave. |
| `wMapObjects` / object masks / variable sprites / palette state | `$d445-$d570` | 300 | Map hot; leave. |
| `wPlayerData3` total | `$d571-$d9ed` | 1149 | Contains the strongest bank-1 relief candidates. |
| Status/money/badges/item pockets | `$d571-$d684` | 276 | Saved and hot menus; leave, except unused backup below. |
| `wTradeFlags` through scene IDs | `$d685-$d6f1` | 109 | Scene IDs may be packable, but not counted in core plan. |
| `wTMTutorTMHMBackup` | `$d6f2-$d72a` | 57 | `RESERVED_UNUSED`; no non-declaration references found. Counted core delete/reuse. |
| Boss AI reserve (`wBossAITier` through pad before `wEventFlags`) | `$d72b-$d7b6` | 140 | Do not shrink for core. Current live state is 104 normal / 131 trace. |
| `wEventFlags` | `$d7b7-$d8b6` | 256 | Counted core compaction candidate: 2048 bits allocated, 1237 real constants. |
| Post-event misc + `wBoxNames` + timers/phone/etc. | `$d8b7-$d9ed` | 311 | `wBoxNames` is a good cold-bank candidate; rest is mixed. |
| `wBoxNames` | `$d8bf-$d93e` | 128 | Counted core move-to-bank-2 candidate; direct uses are PC/intro-menu naming. |
| `wCurMapData` | `$d9ee-$da21` | 52 | Current-map hot state; leave. |
| `SECTION "Party"` | `$da22-$df00` | 1247 | Active party hot data plus several saved cold blocks. |
| Active party species/structs/OTs/nicknames | `$da22-$dbe3` | 450 | Battle/menu hot; leave. |
| `wPokedexCaught`, `wPokedexSeen`, `wUnownDex`, `wUnlockedUnowns`, `wFirstUnownSeen` | `$dbe4-$dc3f` | 92 | Counted core move-to-bank-2 candidate; not Boss AI state. |
| Day-care and egg block | `$dc40-$dce5` | 166 | Counted core move-to-bank-2 candidate; many direct daycare/breeding users but outside Boss AI. |
| Bug Contest second party species + `wContestMon` | `$dce6-$dd16` | 49 | Stretch move-to-bank-2 candidate. |
| Swarm/roamer/Magikarp record block | `$dd17-$dd3f` | 41 | Stretch move-to-bank-2 candidate. |
| OT party/dude tutorial union | `$dd40-$df00` | 449 | Battle/link/tutorial surface; leave unless a dedicated flow audit proves coldness. |
| `SECTION "Stack"` | `$df01-$dfff` | 255 | Do not count without a stack high-water audit. |
| WRAMX bank 2 observation buffer | bank 2 `$d000-$d019` | 26 | Already outside bank 1; bank 2 has 4070 bytes empty for cold data if compatibility and rSVBK rules are solved. |

## Boss AI State Audit

Boss AI should not be the main source of relief.

| Field/group | Bytes | Current use | Relief verdict |
| --- | ---: | --- | --- |
| Strategic scalar state (`tier`, switch counts, plan, wincon, scouting, repeat move) | 16 | Core persistent battle policy state. | Keep. |
| Plausible type mask key + possible mask | 6 | Cached public type inference. | Keep. |
| Seen species list/count | 7 | Species-to-slot mapping for revealed info. | Keep. |
| Revealed move/type masks | 24 | Per-seen-species public move/type memory. | Keep. |
| Likely type mask | 4 | Separate likely-vs-possible inference. | Keep. |
| Alive mask + spare bytes | 4 | Seen-slot liveness and taint/Haki/taunt subfields. | Keep. |
| Score pointer + saved enemy move struct | 9 | Score table and enemy-move scratch save/restore. | Small future refactor possible, not worth core risk. |
| Temp bytes + tier weight row | 6 | Shared policy scratch / trainer row. | Keep. |
| `wBossAISpeciesUsedMoves` | 24 | Preserves public used moves across same-fight switches; used by Rapid Spin bench logic. | Keep. |
| Per-tick memo caches | 4 | Source comments say these avoid many type-chart walks per late-tier pick. | Keep. |
| Trace-only fields | 27 trace-only | Debug capture. | Optional trace-only move to bank 2, not counted toward normal 410. |

## Concrete Relief Plan

Core counted plan:

| # | Change | Bank-1 bytes saved | AI impact | Prerequisites / notes |
| ---: | --- | ---: | --- | --- |
| 1 | Remove or repurpose `wTMTutorTMHMBackup` (`NUM_TMS + NUM_HMS`) instead of carrying it in `wPlayerData3`. | 57 | none | Save-format bump/migration or explicit compatibility discard. Update save-format fingerprint audit. It is marked `RESERVED_UNUSED`, and `rg` found no non-declaration source references. |
| 2 | Move `wBoxNames` from bank 1 to a bank-2 saved cold block. | 128 | none | Add bank-2 accessor/copy helpers; update save/load/checksum layout; migrate old saves; convert direct PC/intro-menu references. Requires CGB/SGB compatibility decision and rSVBK/interrupt discipline. |
| 3 | Move Pokédex/Unown saved state (`wPokedexCaught`, `wPokedexSeen`, `wUnownDex`, `wUnlockedUnowns`, `wFirstUnownSeen`) to bank 2. | 92 | none | Convert Pokedex/capture/debug/event-flag engine direct references to accessors or short banked copy windows. Save-format migration required. Requires CGB/SGB compatibility decision and rSVBK/interrupt discipline. |
| 4 | Move day-care/egg saved state (`wDayCareMan` through `wEggMon`) to bank 2. | 166 | none | Higher call-site count: daycare, breeding, happiness egg, overworld checks, text refs. Prefer local copy-in/copy-out around daycare/breeding flows rather than many tiny bank switches. Save-format migration required. Requires CGB/SGB compatibility decision and rSVBK/interrupt discipline. |
| 5 | Compact `wEventFlags` by removing event-number gaps and remapping saved event bits. Current allocation is 2048 bits / 256 bytes; real named events are 1237, which need 155 bytes if packed. | 101 | none | Save migration must map old event IDs to new IDs. Add an audit that emits/validates old-to-new event map and rejects accidental `const_next` holes unless explicitly justified. This changes many constants but not event semantics. |

Core estimated savings: 57 + 128 + 92 + 166 + 101 = 544 bytes.

Stretch counted candidates:

| Change | Additional bank-1 bytes saved | AI impact | Prerequisites / notes |
| --- | ---: | --- | --- |
| Move Bug Contest block (`wBugContestSecondPartySpecies` + `wContestMon`) to bank 2. | 49 | none | Bug contest capture/judging/display accessors, save migration, rSVBK discipline. |
| Move swarm/roamer/Magikarp record block to bank 2. | 41 | none | Wild encounter, roamer, phone swarm, intro-menu init, and Magikarp-record accessors; save migration; rSVBK discipline. |

Stretch total: 544 + 49 + 41 = 634 bytes.

Optional trace-only relief:

| Change | Bytes saved | AI impact | Notes |
| --- | ---: | --- | --- |
| Move `BOSS_AI_TRACE` fields to bank 2. | 27 trace-build-only, 0 normal | none in normal; very minor trace performance cost | Useful only to restore trace reserve headroom. Not counted toward the normal-build 410-byte goal. |

Not counted:

- Scene ID packing: the 59 scene-ID bytes at `$d6b7-$d6f1` may pack two nibbles per byte if an audit proves every scene value fits 0-15. Estimated savings about 29 bytes. Save-format work required. Not needed for the 410-byte floor.
- Stack shrink: 64+ bytes might be possible only after stack high-water instrumentation across battles, overworld, menus, link, save/load, and interrupts. Currently blocked.
- Boss AI state shrink: possible tiny wins exist, but the current fields are live policy memory. Shrinking them is the wrong first move because the bank has larger non-AI structural wins.

## Required Prerequisites Before Implementation

1. CGB/SGB compatibility decision.
   - Current build is CGB-compatible and SGB-compatible (`-cjsv`). WRAMX bank 2 is a CGB feature; on SGB/DMG compatibility hardware or mode, bank-2 assumptions are unsafe. Either make the hack CGB-only or keep bank-1/SRAM fallbacks for SGB-compatible builds.

2. rSVBK / stack / VBlank discipline.
   - The stack is in WRAMX bank 1 (`$df01-$dfff`). Do not `call SetWRAMBank` to switch away from bank 1 because its `ret` would read the return address through the newly selected WRAMX bank.
   - Bank-2 accessors need inline switch/restore, must restore bank 1 before returning to callers with bank-1 stack frames, and should use `di`/restore-IME or another audited interrupt strategy for every access window.
   - If any bank-2 window can run with interrupts enabled, VBlank/interrupt handlers must save/restore `rSVBK` and `hWRAMBank` before touching WRAMX labels. Short `di` windows are simpler; bulk save/load copies may need chunking so they do not visibly starve VBlank.

3. Save-format work.
   - User approval is required before implementing any shipping save-format change.
   - Bump `SAVE_FORMAT_VERSION`.
   - Add load-time migration from version 2 to the new layout.
   - Update SRAM sections/checksums so moved bank-2 cold blocks still persist.
   - Update `tools/audit/check_save_format_version.py` fingerprints and add explicit coverage for bank-2 saved blocks.

4. Audit scripts.
   - Promote or rewrite `tools/scratch_codex/wramx_bank1_audit.py` as a real audit that reports WRAMX bank 1 free bytes and fails below the agreed floor.
   - Add an event-flag migration audit that validates old-to-new event ID mapping and proves every old named event survives.
   - Add a direct-reference audit for moved cold labels so future code cannot access bank-2 data without wrappers.
   - Extend rSVBK hazard audits to catch new bank-2 accessors that call/return through the wrong bank or leave interrupts exposed.

5. Verification scenarios.
   - Build normal and trace ROMs and rerun memory-budget/docs-navigation/save-format/rSVBK audits.
   - Save/load migration smoke from an old version-2 save with nonempty box names, Pokedex/Unown state, daycare parents/egg state, and several event flags from each removed gap.
   - Gameplay smokes for PC box naming, capture/Pokedex update, Unown seen/unlocked state, daycare deposit/withdraw/egg generation, and event visibility/trainer flags.
   - Boss AI smoke to prove no battle-intelligence regression: at minimum one late-tier trainer with revealed moves, switch memory, Rapid Spin bench knowledge, and type-plausibility caches intact.

## Checkpoint Log

- Started audit in read-only mode; source/doc paths are inspect-only.
- Created read-only helper under `tools/scratch_codex/`.
- Verified WRAMX bank 1 is full and bank 2 is mostly empty from linker maps.
- Read Boss AI state declarations and policy uses; rejected naive Boss AI shrink as low-yield/high-risk.
- Audited saved bank-1 fields and identified core 544-byte plan with no Boss AI intelligence loss.
- Added compatibility, save-format, audit-script, and rSVBK/VBlank prerequisites.
## 2026-05-24 Implementation Checkpoint

Goal promoted from read-only plan to implementation. Current chosen package:

- Remove audited saved WRAM padding/dead fields in `wPlayerData1/2/3`, `wCurMapData`, and the 22-byte pre-Pokedex pad in `wPokemonData`.
- Move box names out of WRAMX bank 1 to SRAM-only storage, accessed through the existing `wBoxNameBuffer`.
- Leave Boss AI runtime state and the 140-byte reserve cap unchanged, so AI battle intelligence and trace behavior should be unaffected.
- Bump `SAVE_FORMAT_VERSION` and add v2 load/checksum migration because the saved WRAM layout changes.

Estimated WRAMX bank-1 savings before build: 411 bytes:

- `wPlayerData3` padding/dead fields/box names/special-phone width cleanup: 333 bytes.
- `wPokemonData` pre-Pokedex pad: 22 bytes.
- `wCurMapData` padding: 5 bytes.
- `wPlayerData2` padding: 47 bytes.
- `wPlayerData1` padding: 4 bytes.

AI impact: none. No Boss AI fields are relocated or shrunk.

## 2026-05-24 Implementation Final

Implemented package:

| Change | Bank-1 bytes saved | AI impact | Notes |
| --- | ---: | --- | --- |
| Remove saved WRAM padding/dead bands in `wPlayerData1`. | 4 | none | v2 migration copies around the removed bytes. |
| Remove saved WRAM padding/dead bands in `wPlayerData2`. | 47 | none | v2 migration copies around the removed bytes. |
| Remove saved WRAM padding/dead fields in `wPlayerData3`, including the audited-dead TM tutor backups. | 205 | none | Boss AI reserve is unchanged; `wSpecialPhoneCallID` is correctly widened to `dw` for the hidden two-byte script write. |
| Move `wBoxNames` out of WRAMX bank 1 into SRAM-only `sBoxNames`, using `wBoxNameBuffer`/`wStringBuffer2` for display and rename paths. | 128 | none | PC box rename updates `sBoxNames` and refreshes the primary checksum. Default box names initialize in SRAM. |
| Remove saved WRAM padding in `wCurMapData`. | 5 | none | v2 migration copies around the removed bytes. |
| Remove pre-Pokedex saved WRAM padding in `wPokemonData`. | 22 | none | v2 migration copies Pokemon data before moving primary old box names, because the new `sBoxNames` destination overlaps the old v2 PokemonData SRAM range. |

Total WRAMX bank-1 relief: 411 bytes.

Measured from rebuilt linker maps:

| Build | WRAMX bank 1 used | WRAMX bank 1 free | Boss AI live | Boss AI reserve pad |
| --- | ---: | ---: | ---: | ---: |
| Normal | 3685 | 411 | 104 | 36 |
| `BOSS_AI_TRACE` | 3685 | 411 | 131 | 9 |

Prerequisites resolved:

- Save-format work: `SAVE_FORMAT_VERSION` bumped from 2 to 3; v2 primary and backup load/checksum migration added; current primary keeps old external checksum/version/active-box offsets via compatibility padding; backup check values are likewise pinned.
- Audit scripts: added `tools/audit/check_wramx_bank1_relief.py`; updated save-format fingerprint for v3.
- SGB/CGB and rSVBK decision: no WRAMX bank-2 runtime relocation shipped, so there is no new `rSVBK`/VBlank/SGB compatibility risk in this implementation.
- Generated docs: refreshed `docs/generated/dev_index.md`; updated `docs/boss_ai_spec.md` Boss AI budget anchors.

Verification run:

- Forced normal build passed:
  `bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -B -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc'`
- Forced trace build passed:
  `bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -B -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe DEFINES="-D BOSS_AI_TRACE" pokegold.gbc'`
- Restored normal `pokegold.*` artifacts after copying trace artifacts to `pokegold_trace.*`.
- `python tools\audit\check_wramx_bank1_relief.py` passed.
- `python tools\audit\check_save_format_version.py` passed.
- `python tools\audit\check_boss_ai_memory_budget.py` passed.
- `python tools\audit\check_docs_navigation.py` passed.
- `python tools\audit\check_release_smoke.py` passed, with its existing two stale-shipped-claim warnings only.
- `git diff --check` passed; it printed CRLF-normalization warnings in unrelated dirty files and the updated save-format fingerprint JSON.
