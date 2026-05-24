# WRAMX Bank 1 Relief Plan — 2026-05-24

**Read-only audit.** Goal: free ≥10% of WRAMX bank 1 ($d000–$dfff, 4096 bytes
total) — that is **≥410 bytes** — with at-most-minor reduction in Boss AI
battle intelligence and performance. Floor not ceiling; go bigger when free.

## Starting state (from `docs/generated/dev_index.md`)

- WRAMX bank 1 free: **0 bytes**.
- WRAMX bank 2 free: ~16,358 bytes (only 26 bytes used by
  `wBossAIWramx2Buffer`).
- Boss AI WRAM Reserve (inside bank 1, fixed-size 140 bytes
  reservation): Normal build uses 104, leaves 36; `BOSS_AI_TRACE` build
  uses 131, leaves 9.

The 140-byte reservation pad lives in `ram/wram.asm:2502`:
```
ds 140 - (wBossAIStateEnd - wBossAITier)
```
So freeing N bytes inside the Reserve does not free the same N bytes in
bank 1 — the `ds` pad just grows back to fill 140. To actually claw bank-1
bytes back from the Reserve we have to (a) shrink the Reserve cap itself,
not just the live block, and (b) make sure no future Boss AI growth needs
the slack.

## Tenant map (resolved constants)

| Constant | Value | Notes |
| --- | ---: | --- |
| `NUM_MOVES` | 4 | per-mon moveset size, not species count |
| `MOVE_LENGTH` | 7 | move struct bytes |
| `PARTY_LENGTH` | 6 | party slots |
| `BOSS_AI_OBS_ENTRY_SIZE` | 4 | bank-2 obs log entry |
| `BOSS_AI_OBS_MAX_TURNS` | 6 | bank-2 obs log capacity |
| `NUM_OBJECTS` | 16 | map object structs |
| `NUM_EVENTS` | 800 | → `wEventFlags` = **100 bytes** |
| `MAX_PC_ITEMS` | 50 | → `wPCItems` = 101 bytes |
| `NUM_BOXES` | 14 | with `BOX_NAME_LENGTH`=9 → `wBoxNames` = 126 bytes |
| `NAME_LENGTH` | 11 | |
| `MON_NAME_LENGTH` | 11 | |

## Boss AI Reserve field-by-field (104 / 131 bytes)

Pulled from `ram/wram.asm:2441-2500`. Single bytes unless noted.

| Field | Bytes | Hot path? | Notes |
| --- | ---: | --- | --- |
| `wBossAITier` | 1 | yes | per-tick |
| `wBossAIMoveChoiceReady` | 1 | yes | latched per turn |
| `wBossAISwitchConfidence` | 1 | yes | recomputed per turn |
| `wBossAILastSwitchedOut` | 1 | medium | survives turn |
| `wBossAISwitchCooldown` | 1 | medium | survives turn |
| `wBossAIPlayerSwitchCount` | 1 | medium | match-long |
| `wBossAIPendingPlayerSwitchCount` | 1 | yes | current-turn buffer |
| `wBossAITurnsElapsed` | 1 | yes | match-long |
| `wBossAIPlanId` | 1 | yes | match-long |
| `wBossAIPlanPhase` | 1 | yes | match-long |
| `wBossAIPlanConfidence` | 1 | yes | match-long |
| `wBossAIWinconMonIdx` | 1 | yes | match-long |
| `wBossAITargetMonIdx` | 1 | yes | match-long |
| `wBossAIScoutedMask` | 1 | yes | match-long bitmap |
| `wBossAIRepeatCount` | 1 | yes | match-long |
| `wBossAILastChosenMove` | 1 | yes | match-long |
| `wBossAIPlausibleTypeMaskSpecies` | 1 | cache key | |
| `wBossAIPlausibleTypeMaskLevel` | 1 | cache key | |
| `wBossAIPlausibleTypeMaskCache` | 4 | cache value | bit per type (≤56) |
| `wBossAISeenPlayerSpeciesCount` | 1 | yes | |
| `wBossAISeenPlayerSpecies` | 6 | yes | one species per slot |
| `wBossAIRevealedMovesBitmap` | **24** | yes | 6 slots × 4-byte type mask |
| `wBossAILikelyTypeMaskCache` | 4 | cache value | |
| `wBossAISeenPlayerAliveMask` | 1 | yes | bit per seen species |
| `wBossAIRevealedMovesBitmapSpare` | 3 | unused? | adjacency-only |
| `wBossAIScorePtr` | 2 | per-tick | recompute-cheap |
| `wBossAISavedEnemyMoveStruct` | 7 | per-tick | mirrors `wEnemyMoveStruct` |
| `wBossAITemp..Temp5` | 5 | per-tick | scratch |
| `wBossAITierWeightRow` | 1 | match-long | |
| `wBossAISpeciesUsedMoves` | **24** | yes | 6 × 4-byte per-species used-move mirror |
| `wBossAIHasKOMoveCache` | 1 | per-tick | $ff/0/1 |
| `wBossAIPublicThreatCache` | 1 | per-tick | $ff/0/1 |
| `wBossAIRevealedPriorityCache` | 1 | per-tick | $ff/0/1 |
| `wBossAIPrimaryThreatCache` | 1 | per-tick | $ff/$20/type |
| **`BOSS_AI_TRACE` additions** | **27** | trace-only | |
| `wBossAITraceTopMoves` | 3 | | |
| `wBossAITraceTopScores` | 3 | | |
| `wBossAITracePreModelScores` | 4 | NUM_MOVES | |
| `wBossAITracePostModelScores` | 4 | NUM_MOVES | |
| `wBossAITraceChosenMove` | 1 | | |
| `wBossAITraceSwitchConfidence` | 1 | | |
| `wBossAITracePlanId` | 1 | | |
| `wBossAITracePlanPhase` | 1 | | |
| `wBossAITracePlanConfidence` | 1 | | |
| `wBossAITracePlausibleMask` | 4 | | |
| `wBossAITraceRiskFlags` | 1 | | |
| `wBossAITraceLookaheadBonusTop` | 3 | | |

Totals verified: 104 (Normal) / 131 (trace).

## Candidate buckets

1. **Boss AI Reserve shrink** — move bank-1 fields to WRAMX bank 2
   (already plumbed via `wBossAIWramx2Buffer`); bit-pack masks; lazy-
   recompute caches.
2. **Game Data slack** — `ds N` filler/RESERVED_UNUSED bands inside the
   Game Data section (lines 2370, 2377, 2439, 2554, 2580, 2591, 2605,
   2631, 2636, …).
3. **Big fixed structures** — `wEventFlags` (100), `wPCItems` (101),
   `wBoxNames` (126), `wObjectStructs` UNION (the 458-byte alt member),
   scene-ID block (58 bytes), `wVariableSprites` (256 - SPRITE_VARS).
4. **Top-of-bank (`WRAM 1` section)** — overworld scratch like
   `wTrainerBattleContextBackup`, `wUsedSprites`, `wMapAttributes` mirror.

## Parallel Explore audits — completed 2026-05-24

Four `Explore` subagents ran in parallel; their raw findings, claim-by-
claim verified against source/sym, are folded into the synthesis below.

## Claude checkpoint 2026-05-24 (post-audit synthesis)

### Verified facts (sym/source-checked, not just audit claims)

- Symbol addresses extracted from `pokegold.sym` so all sizes are exact:

| Symbol | Addr | Implied size to next | Source notes |
| --- | --- | ---: | --- |
| `wTrainerBattleContextBackup` | 01:d049 | 16 (to `wTrainerBattleContextBackupActive` d059) | scratch, NOT saved |
| `wUsedSprites` → `wUsedSpritesEnd` | 01:d05d → d075 | 24 + 8 pad = 32 to `wOverworldMapAnchor` d07d | NOT saved |
| `wMapPartial` → `wMapPartialEnd` | 01:d081 → d086 | 5 | one CopyBytes consumer at `home/map.asm:2381` |
| `wMapAttributes` → `wMapAttributesEnd` | 01:d086 → d092 | 12 | NOT saved |
| N/S/W/E map connections | 01:d092 → d0c2 | 48 | NOT saved |
| `wTMsHMs` | 01:d57e → d5b8 | 58 | live (player TM/HM inventory, saved) |
| `wTMTutorTMHMBackup` | 01:d6f2 → d72b | 57 | **DEAD** (zero readers in engine/home/data; only `tools/scratch_codex/wramx_bank1_audit.py` references it) |
| Boss AI Reserve block | 01:d72b → d7b7 | **140** (cap) | Live = 104 Normal / 131 trace |
| `wEventFlags` → `wBoxNames-9` | 01:d7b7 → d8b7 | **256** | `NUM_EVENTS = 2048` (the `; 800` source comment is stale; `const_next 2048` at `constants/event_flags.asm:1331` sets the actual value) |
| `wBoxNames` | 01:d8bf | 126 | already named alongside `sBox1..sBox14` in SRAM |
| `wScreenSave` | 01:da04 | 30 (6×5 metatiles per `constants/gfx_constants.asm`) | NOT in `wPlayerData*` ranges → check below |
| `wStackBottom` → `wStackTop` | 01:df03 → dfff | 252 + 1 byte cap (`ds $fc` + `db`) | NOT saved |

- `SAVE_FORMAT_VERSION = 2` (`constants/misc_constants.asm:35`).
- `pokegold.sym` boss-AI offsets reconcile to the 104/140 Normal layout
  exactly (`wBossAITier d72b … wBossAIStateEnd d793`, 0x68 = 104).
- `wBossAIRevealedMovesBitmapSpare` is **fully consumed**, not idle:
  byte 0 = reveal-taint mask (`boss_platform.asm:332,345`), byte 1 =
  quarantined Haki flags (`boss_platform.asm:53-66`,
  `boss_policy_switch.asm:116/141`), byte 2 = pending taunt id
  (`haki_taunt_queue.asm:37-55`). The earlier "3 bytes spare" framing in
  this scratchpad's own field table is **wrong**; treat all 3 bytes as
  load-bearing.

### Load-bearing structural constraint the audits collectively missed

`engine/menus/save.asm` copies five fixed ranges from WRAMX bank 1 to
SRAM (lines 451-518, 736-757):

```
sPlayerData1 = ds wPlayerData1End - wPlayerData1
sPlayerData2 = ds wPlayerData2End - wPlayerData2
sPlayerData3 = ds wPlayerData3End - wPlayerData3   ← contains the Boss AI Reserve
sCurMapData  = ds wCurMapDataEnd  - wCurMapData
sPokemonData = ds wPokemonDataEnd - wPokemonData
```

Three implications:

1. **The 140-byte Boss AI Reserve cap is a save-format-stability shim.**
   Boss AI runtime state lives inside `wPlayerData3`, so the
   `BOSS_AI_TRACE` toggle (Normal 104 vs trace 131 live bytes) can't be
   allowed to shift `wEventFlags` downstream — the `ds 140 - (live)`
   pad absorbs the difference. Shrinking *inside* the cap frees zero
   bank-1 bytes; the pad just grows. Shrinking the *cap itself* DOES
   free bank-1 bytes but changes the save-format byte offsets of every
   field after it (wEventFlags, scene IDs, decorations, daily timers,
   …) → requires `SAVE_FORMAT_VERSION` bump and user approval per
   `CLAUDE.md`.
2. **Anything inside `wPlayerData1/2/3`, `wCurMapData`, `wPokemonData`
   is save-format-touching.** That covers all the big targets the
   audits ranked highest (TMHM-backup deletion, scene-ID bit-packing,
   `wBoxNames` move, `wEventFlags` shrink, all the `ds N` filler
   bands).
3. **Anything in the "WRAM 1" section ($d000-$d1a0, 417 bytes) and the
   "Stack" section is NOT saved and can be relocated to bank 2
   without save-format risk.** This is where the no-approval-needed
   relief has to come from.

The audits ranked candidates by raw byte savings without applying this
filter, so several of their "top wins" (TMHM backup, scene-ID pack,
`wBoxNames` move, `ds 22` party filler shrink) are all save-format
items. They're still good candidates, just gated on user approval.

### Save-format-safe ("Tier 1") relief from WRAM 1 + Stack

All access-count figures are grep counts of the symbol across
`engine/`, `home/`, `data/`.

| Target | Bytes | Refs | Cost | Notes |
| --- | ---: | ---: | --- | --- |
| `wTempMon` (party_struct, 48) | 48 | 7 refs / 4 files | small | `engine/pokemon/{tempmon,breedmon_level_growth,stats_screen,mon_stats}.asm`. Pure menu/breeding swap buffer; relocate to bank 2 with save/restore bank wrapper around each access region (already done idiom in `boss_ai_set_wram_bank` macro). |
| `wUsedSprites` + ds 8 pad (32) | 32 | ~15 refs / 2 files | small | overworld sprite GFX list, init-time mostly. |
| `wTrainerBattleContextBackup` (16) + `wTrainerBattleContextBackupActive` (1) = 17 | 17 | 4 refs / 3 files | tiny | pure context-switch buffer between `InitTrainerBattle` and `DoTrainerBattle`. |
| N/S/W/E map_connection_structs (4 × 12 = 48) | 48 | moderate | small | loaded once per warp; not hot-loop. |
| `wMapPartial` (5) + `wMapAttributes` (12) = 17 | 17 | 1 CopyBytes consumer + scattered single-field reads | medium | care: the partial copy is load-bearing; bank-switch wrapper at the copy site. |
| `wTileset` block (13, `TILESET_LENGTH`) | 13 | moderate | small | loaded per-map; not hot-loop. |
| `wScriptStack` (15, `ds 3 * 5`) | 15 | every script frame | medium | hot in overworld scripting. Bank-switch overhead non-trivial. Defer. |
| Stack shrink ($fc → $b0, save 76) | 76 | implicit | medium-risk | requires stack-depth audit; emulator-driven max-depth measurement. |
| **Tier-1 subtotal (without Stack/ScriptStack)** | **175** | | | hits ≈4.3% of bank 1 with zero save-format risk |
| Tier-1 subtotal (with Stack shrink, no ScriptStack) | 251 | | | ≈6.1% of bank 1; needs stack-depth proof |

Tier 1 alone falls short of the 410-byte floor. The 10% floor will
require some Tier-2 work.

### Save-format-bump ("Tier 2") candidates — needs user approval

| Target | Bytes | Cost | Notes |
| --- | ---: | --- | --- |
| Delete `wTMTutorTMHMBackup` (57) + `wTMTutorBadgesCounted` (1) + `wTMTutorCredits` (1) | 59 | tiny | All confirmed dead (zero engine/home/data readers). Shifts everything after them. |
| Bit-pack scene IDs (59 × 1 byte → 22 bytes of 3-bit fields) | 36 | medium | All scene IDs observed in 0..7 range (per audit; not exhaustively re-checked here — verify in a follow-up pass). Requires accessor macros at ~30 read/write sites. |
| Shrink Boss AI Reserve cap from 140 → live size + small headroom | up to ~90 | small (mostly bookkeeping) | After moving largest Boss-AI fields (`wBossAISpeciesUsedMoves` 24, `wBossAIRevealedMovesBitmap` 24, `wBossAISavedEnemyMoveStruct` 7, `wBossAISeenPlayerSpecies` 6, `wBossAITrace*` 27, `wBossAIPlausibleTypeMaskCache` 4 + `wBossAILikelyTypeMaskCache` 4) to a new `wBossAIWramx1RelocatableState` section in bank 2, live Reserve drops from 104 → ~32 bytes; cap can shrink correspondingly. Per Tenant-1 audit, the moved fields are between-turn or recompute-cheap; bank-switch wrapper cost is 1-2 wrappers per AI tick (≤30 cycles vs ~500-800 cycle tick budget = ≤6%). |
| Vestigial filler bands inside `wPlayerData3` | **110 verified** + up to 45 more | small | Big-three verified pure pad (zero hidden sym entries inside, zero offset-arithmetic readers found in source): `ds 33` (line 2370, between `wTradeFlags`@d685 and `wMooMooBerries`@d6a7), `ds 55` (line 2591, between `wUnusedTwoDayTimerStartDate`@d985 and `wStepCount`@d9bd), `ds 22` (line 2605, between `wPhoneList`@d9c6 and `wLuckyNumberShowFlag`@d9e7). Total **110 bytes certain**. Smaller scattered bands (`ds 12` at 2377, plus 17 single-/double-byte gaps) sum to another 45 bytes, but each needs same per-band sym+offset check before removing. |
| ~~Shrink `NUM_EVENTS` from 2048 → 1024~~ | ~~128~~ | ~~tiny~~ | **WRONG — withdrawn.** `constants/event_flags.asm` actually has **1237 named events** with `const_next` jumps to 200/600/1000/1600/1900/2048; named indices reach ~1937. Shrinking below ~1952 destroys live flags. Realistic shrink to 1952 (next 8-byte boundary above 1937) saves only 12 bytes — not worth the save-format bump. |
| Move `wEventFlags` (256) out of `wPlayerData3` into a separate WRAMX-2 section with its own SRAM save target | 256 | medium-high | the bigger lever once shrink is off the table; same engineering as the Tier-3 move below, but pulls the byte savings into Package B. Adds bank-switch wrap to `home/flag.asm` event-flag helpers. |
| Bit-pack 4 per-tick Boss AI caches (4 → 2 bytes) | 2 | small | nibble encoding with sentinel; <1% perf hit per audit. Only helps if Reserve cap is also being shrunk in same change. |
| `wBoxNames` (126) move from WRAMX bank 1 to its own SRAM section (near `sBox1..14`) | 126 | medium | 3 read sites (`engine/pokemon/bills_pc.asm` ×2, `engine/menus/intro_menu.asm` ×1). SRAM region exists naturally alongside the boxes themselves. |
| **Tier-2 subtotal** (without `wEventFlags` move; that's listed below in Tier-3) | **~435** | | already enough on its own; with `wEventFlags` move folded in, ~691 |

### Creative / Tier-3 — bigger but more invasive

| Target | Bytes | Cost | Notes |
| --- | ---: | --- | --- |
| Move `wEventFlags` (256) to bank 2 entirely | 256 | medium-high | `home/flag.asm` event-flag helpers (`EventFlagAction`) become the only readers; instrument bank switch there once. ~200+ overworld checks per minute; +6 cycles each = ~1200 cycles/min, negligible. Save format still touches it (copied from bank 2 → SRAM at save time). |
| Day-Care structures move to SRAM-only with on-demand WRAM load | 162 | high | `wDayCareMan`/`wDayCareLady`/`wBreedMon1`/`wBreedMon2`/`wEggMon` plus their OT/nicknames. Used only in Day-Care UI; load on UI entry, save on UI exit. Save-format moves them out of `sPokemonData` into their own SRAM section. |
| Use WRAMX banks 3-7 (currently undeclared) for further expansion | n/a | n/a | `layout.link` doesn't declare them but `SECTION "...", WRAMX, BANK[3]` works (Tenant-4 audit verified). No build-script change needed. |
| Stack shrink to $a0 with measured headroom | 92 | medium-risk | requires stack-depth audit via emulator break-on-overflow or instrumented build. |
| `wBoxNames` to bank 3 + bank-switched access | 126 | low if event-flag bank-switch is already in place | alternative to SRAM-only move; fewer code changes. |

### Recommended bundle — three packages at increasing scope

**Package A — No save-format change (≈175 bytes, ≈4.3%):**
Move `wTempMon` (48) + `wUsedSprites`+pad (32) +
`wTrainerBattleContextBackup` (17) + map connections (48) +
`wMapPartial`+`wMapAttributes` (17) + `wTileset` (13) to a new
`SECTION "WRAM1 Scratch Relocated", WRAMX, BANK[2]`. Wrap each access
site with the `boss_ai_set_wram_bank` inline macro (NOT
`SetWRAMBank`; `home/wram_bank.asm`'s helper is unsafe to call when
switching away from bank 1 because the stack lives there — see Tenant-4
audit). **Falls short of the 10% floor on its own.**

**Package B — Single save-format bump (Package A + Tier-2 essentials,
≈474 bytes, ≈11.6%):**
- Package A (175 bytes, no save risk)
- Bump `SAVE_FORMAT_VERSION` to 3, with new-game default for first
  load: zero the new layout, accept old saves as legacy by reading
  through a one-shot fixup table.
- Delete `wTMTutor*` (59 bytes)
- Shrink Reserve cap from 140 → 48 after moving large Boss AI fields
  (`wBossAISpeciesUsedMoves`, `wBossAIRevealedMovesBitmap`,
  `wBossAISavedEnemyMoveStruct`, `wBossAISeenPlayerSpecies`,
  `wBossAITrace*`, two type-mask caches) to a new
  `SECTION "Boss AI WRAMX2 State", WRAMX, BANK[2]` adjacent to the
  observation buffer. Reserve cap delta: 92 bytes.
- Bit-pack scene IDs 58 single bytes → 22 bytes of 3-bit fields: 36
  bytes (validated this iteration — max 7 scenes/map across all
  `maps/*.asm`).
- Remove the three big verified-empty `ds` bands inside `wPlayerData3`
  (ds 33 at line 2370, ds 55 at 2591, ds 22 at 2605): 110 bytes.
- Bit-pack 4 per-tick Boss AI caches: 2 bytes.

**474 bytes, ≈11.6% of bank 1 — 64 bytes of margin over the 10%
floor.** Notable withdrawals from earlier draft: the `NUM_EVENTS`
shrink line was invalid (1937 named events exist; only ~110 bytes
of headroom, not 128); replaced by tighter filler-band cleanup.

**Stretch validated (Package B+): 518 bytes ≈ 12.6%.** Ran the same
sym-gap + offset-arithmetic check via
`tools/scratch_wram_relief_deliverable_check.py`'s sibling script on
the smaller scattered `ds` bands. **18 of 19 smaller bands are pure
pad** (44 bytes). The one real hidden field: `ds 3` at line 2585 is
actually 1-byte hidden field + 2-byte pad — the `specialphonecall`
script command (`engine/overworld/scripting.asm:1814-1818`) reads
two script bytes and writes them to `wSpecialPhoneCallID` and
`wSpecialPhoneCallID + 1`, even though `wSpecialPhoneCallID` is
declared `db`. Fix is to relabel as `dw`, shrinking only 2 of the 3
pad bytes. False positive ruled out: `wCurMapCallbacksPointer + 1`
at `home/map.asm:855` is just the high byte of the `dw`, not the
pad. So smaller-band saving is 44 bytes, total Package B+ is
175 + 59 + 92 + 36 + 110 + 44 + 2 = **518 bytes (≈12.6%)**.

Big-ticket downside: save-format bump requires user approval and a
migration story (the hack has no existing migration code per
`CLAUDE.md`; would need a one-shot fixup in the save-load path keyed
on `sSaveFormatVersion`).

**Package C — Maximal relief (≈700+ bytes, ≈17%):**
- Package B
- Move `wBoxNames` (126) to its own SRAM section near `sBox*`
- Move `wEventFlags` (post-shrink, 128) to WRAMX bank 2 with bank-
  switch in `home/flag.asm`
- Move `wDayCare*` structures (162) to SRAM-only with on-demand
  load/save when Day-Care UI opens/closes

### Practical-path recommendation

Ship **Package A first** as a no-approval, no-save-risk PR. It only
hits ~4% but proves the bank-2 relocation idiom in the build, brings
the audit floor with it (need a new `tools/audit/check_wramx_bank2_
access_pattern.py` to lint that no relocated field is read without a
bank-switch wrapper), and unblocks the bigger Package B work without
holding up other branches.

Then escalate **Package B** to the user with a one-page migration
plan: what breaks, what the legacy-save path looks like, and what the
gameplay-visible artifacts would be (none if the migration is
correct).

Defer **Package C** until after Package B is in playtest — the bigger
moves are higher complexity per byte and only matter if Package B's
relief is still tight.

### Follow-ups validated this iteration

- **Scene-ID 3-bit packing is sound.** Counted `scene_script` lines per
  `maps/*.asm`: ElmsLab has 7 scenes (max), everything else ≤4. Scene
  IDs are 0..6 across the whole game → 3 bits each → 22 bytes total
  for 58 IDs (vs 58 bytes raw). The 36-byte saving in Package B is
  confirmed; only the accessor-macro refactor cost remains.
- **Three big `ds` bands verified pure pad.** For each, computed the
  sym-file gap between bounding labels and confirmed it matches `bound
  size + ds`, then grepped for offset-arithmetic readers (`wTradeFlags
  + N`, `wPhoneList + N`, `wMooMooBerries - N`, `wStepCount - N`):
  zero hits. `ds 33` at line 2370 (d685+1 to d6a7), `ds 55` at line
  2591 (d985+1 to d9bd), `ds 22` at line 2605 (d9c6+11 to d9e7). 110
  bytes certain. The smaller scattered bands (45 more bytes) likely
  also pad, but each still needs the same per-band check before
  removal.
- **Default bundle:** pgoal decision logged 2026-05-24 — Package B is
  the recommended bundle (≈474 bytes, 11.6%, single save-format bump).
  Package A (4.3%) misses the floor; Package C (17-21%) is invasive
  enough to deserve a separate escalation after B lands.

### Open questions / follow-ups (not blockers for this scratchpad)

- Stack-depth measurement: instrument the build to record max `sp`
  drop across a long playtest, before committing to a stack shrink.
- Confirm the 458-byte `wObjectStructs` UNION is not double-counted
  in any tool — Tenant-3 audit flagged it as "458 bytes wasted" but
  UNION semantics mean the bytes are shared, not duplicated.
- Quantify the per-frame cost of bank-switching for hot fields by
  running `tools/damage_debugger` and `boss_ai_debugger` against a
  prototype where one batch (e.g. the 4 Boss AI caches) lives in
  bank 2.
- The "Codex checkpoint" section at the top notes the current tracked
  tree is already dirty in Boss-AI-related files; final per-field byte
  counts should be re-verified once those changes land.

## Codex checkpoint 2026-05-24

- Read `CLAUDE.md`, `docs/README.md`, `docs/build.md`, and the relevant
  `docs/generated/dev_index.md` sections.
- Constraint reminder: do not write source/build outputs; only this
  scratchpad may be edited. Current tracked tree is already dirty in many
  Boss-AI-related files, so all source observations below are from the
  current checkout and should be revalidated after those changes settle.
- Hardware references checked: Pan Docs confirms CGB has WRAM0 always mapped
  at $c000-$cfff and selectable WRAMX banks 1-7 at $d000-$dfff via `rSVBK`;
  RGBLINK docs confirm WRAMX sections are placed in the banked $d000-$dfff
  region. This makes bank-2 scratch structurally plausible but requires
  explicit `rSVBK` save/restore around every access and care around
  interrupts/VBlank code that assumes bank 1 is mapped.

