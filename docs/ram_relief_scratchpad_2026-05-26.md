# RAM Relief Scratchpad — 2026-05-26

**Status:** active investigation. This file is the working log. Deliverable
is `docs/ram_relief_plan_2026-05-26.md`. No source edits this iteration.

## Targets

| Region | Used | Free | 20% relief = | Source |
|---|---:|---:|---:|---|
| HRAM | 127 | 0 | ~25 bytes | dev_index.md |
| WRAM0 | 4049 | 47 | ~810 bytes | dev_index.md |
| **Pool (HRAM + WRAM0)** | **4176** | **47** | **~835 bytes** | combined |

The 14 "empty ROM banks" (largest free: 13, 22, 27 at 16384 each; per
dev_index.md "Largest ROMX Free Ranges") are the relocation host pool.
WRAMX is not tight (4481 free across 2 used banks per dev_index summary;
audit will confirm whether banks 2–7 are truly empty per source).

## Iteration 1 — Batch 1 dispatch

Five subagents, parallel, all read-only investigation. Each returns a
structured candidate table.

| # | Agent | Subagent type | Scope |
|---|---|---|---|
| 1 | WRAM0 inventory | Explore | enumerate every SECTION/label in `ram/wram.asm` WRAM0 region; classify hot/cold/cache/scratch |
| 2 | HRAM inventory | Explore | enumerate every label in `ram/hram.asm`; classify by use (math UNION, IO shadow, cache, transient) |
| 3 | WRAMX free-bank audit | Explore | walk `ram/wram.asm` for BANK[02..07]; confirm which banks have zero SECTIONs (true relocation hosts) |
| 4 | Cache/scratch greps | Explore | grep WRAM0 for names matching Cache/Scratch/Temp/Buffer/Pending/Cooldown — high-relief class |
| 5 | Top-10 contiguous WRAM0 | Explore | find largest contiguous `ds N` allocations in WRAM0 — biggest single relocation wins |

After Batch 1 returns: synthesize into a candidate pool, pick top 3 by
(bytes × safety-of-move), then dispatch Batch 2 (5 deep-dive verifiers).

## Iteration 2 — Batch 1 synthesis

### WRAM0 candidate pool (combined from agents 1, 4, 5)

| Symbol | Bytes | Class | Conf | Source agent |
|---|---:|---|---|---|
| wDebugOriginalColors | 1024 | `IF DEF(_DEBUG)` — possibly **0 in prod build** | needs-verify | A5 |
| wOverworldMapBlocks | 1300 | Cold; UNION with link data | medium | A1, A5 |
| wLinkData (UNION peer) | — | already shares space with above | — | A1, A5 |
| wBoxPartialData | 480 | ROM-recompute (claimed 6 readers in save.asm) | high (claim) | A4 |
| wTempTilemap | 360 | WRAMX-move; recomputable | high (claim) | A1, A4 |
| wDecompressScratch | 320 | ROM-recompute; 2 callers in battle_transition | high (claim) | A4 |
| wLYOverridesBackup | 144 | WRAMX-move; effect code only | medium | A4 |
| wBattleAnimTileDict | 80 | ROMX precompute at startup | high (claim) | A4 |
| wTimeSetBuffer | 60 | WRAMX-move; time-set screen only | high (claim) | A4 |
| wSurfWaveBGEffect | 64 | Eliminate (claim — specific anim only) | medium | A4 |
| wBGMapBufferPointers | 40 | Eliminate (claim) | medium | A4 |
| wBattleScriptBuffer | 40 | 20+ call sites — risky | LOW | A4 |

Conservative-only pool (high-confidence rows excluding _DEBUG conditional):
480 + 360 + 320 + 80 + 60 = **1300 bytes** (157% of 810-byte WRAM0 target).
Including `wDebugOriginalColors` if it's truly _DEBUG-only adds 1024 more.

### HRAM verdict (agent 2): "Could not reach 20%"

Movable bytes found: ~8 (hUnusedByte 1, hEnemyMonSpeed 2, hUsedSpriteIndex 1,
hTilesPerCycle 1, hBlackOutBGMapThird 1, hLastTalked 1, hSerial fields 2).
Target was 25. Immovable mass: math UNION (5), IO shadows (8), bank-switch
shadows (3), hot scratch (~16). **HRAM 20% target unreachable** — plan
documents this honestly.

### WRAMX free banks (agent 3)

Banks 3, 4, 5, 6, 7 each have **zero SECTIONs declared** — 8192 free per
bank × 5 = 40960 bytes of true relief host capacity. Bank 1 boss-AI
reserve is 28 free without trace / 0 with trace (per dev_index). Agent
flagged "9 bytes" figure as not findable; need to reconcile with
`docs/boss_ai_spec.md:794-808` claim. Logging as a follow-up.

## Iteration 3 — Batch 2 dispatch (deep-dive verification)

5 subagents in parallel. Top-3 candidate trace + 2 cross-check
agents (re-grep claims independently).

| # | Agent | Subagent | Verifies |
|---|---|---|---|
| 1 | wBoxPartialData deep-trace | Explore | All readers/writers in entire repo; confirm "recomputable from ROM" |
| 2 | wDecompressScratch + wTempTilemap | Explore | Actual call sites + bytes confirmed |
| 3 | wDebugOriginalColors gate verify | Explore | `IF DEF(_DEBUG)` gating + whether prod build defines it |
| 4 | wOverworldMapBlocks UNION verify | Explore | UNION layout actually shares the 1300 bytes; cold-only proof |
| 5 | Bank-1 reserve reconciliation | Explore | 9-byte vs 28-byte figure; canonical reading from ram/wram.asm |

After Batch 2: any claim that fails verification gets demoted to
"needs investigation"; survivors go into the plan's Reach to 20%
section.

## Iteration 4 — Batch 2 results (verified)

### Corrections

| Field | Batch 1 claim | Verified reality | Net relief if moved alone |
|---|---|---|---:|
| wBoxPartialData | 480 B, ROM-recomputable | UNION member, write-only SRAM staging, NOT ROM-recomputable | **0 B** |
| wDecompressScratch | 320 B, 2 callers, ROM-recompute | **640 B** (40 tiles × 16), confirmed 2 callers, in 1300-B "Overworld Map" UNION | **0 B** |
| wTempTilemap | 360 B, WRAMX-movable, 4 readers in home/map.asm | 360 B confirmed; UNION peer with 480-B sized parent; 53 callers via 3 home/copy_tilemap.asm fns; WRAMX tax too high | **0 B** (UNION) |
| wDebugOriginalColors | 1024 B, `IF DEF(_DEBUG)`-gated, 0 in prod | **1024 B, NOT gated, IS in shipped ROM**; DebugColorPicker unreferenced → DEAD CODE | **0 B in this UNION** but real dead code |
| wOverworldMapBlocks | 1300 B, cold | **HOT** (per-frame in GetMapScreenCoords/GetBlockLocation); 5-8% CPU regression if WRAMX-moved | not movable |
| Bank-1 reserve | 9 free under trace | **0 free under trace, 28 free normal** (dev_index canonical; spec stale by 1 byte from P-A's wBossAILookaheadRunningBest) | n/a (status check) |

### Dominant constraint: UNION layout

Two huge WRAM0 UNIONs determine the math:

**"Overworld Map" UNION (~1300 B floor):**
- wOverworldMapBlocks: 1300 (HOT)
- wLinkData: 1300 (cold; link only)
- wDebugOriginalColors: 1024 (DEAD code, not gated)
- wBillsPCData: 819
- wDecompressScratch: 640
- wHallOfFamePokemonList: 98
- wUnusedPikachu/Jigglypuff: 24

→ UNION size = max(1300). Removing wDebugOriginalColors frees **0** because wOverworldMapBlocks/wLinkData still 1300. To free anything, the TWO 1300-B peers must both shrink/move.

**"Miscellaneous" UNION (~480 B floor):**
- wSurroundingTiles: 480
- wBoxPartialData: 480 (UNION-write only)
- wTempTilemap: 360
- wPlayerPatchLists / wOTPatchLists: 200
- wSpriteAnimData: 200
- plus several smaller peers

→ UNION size = max(480). Need wSurroundingTiles + wBoxPartialData both ≤ Nbytes for relief = (480 − N) per slot.

### Recalibrated opportunity surface

Naïve "move one field" approach: ~0 B relief from any of the Batch 1
top candidates. Real opportunities are:

1. **Non-UNION standalone WRAM0 fields** — what bytes are NOT inside a UNION? Those are direct relief targets.
2. **Shrink the largest UNION peer.** wOverworldMapBlocks is hot; can it be smaller? wSurroundingTiles 480 → smaller?
3. **Remove dead/unreferenced symbols** — wDebugOriginalColors + DebugColorPicker. Doesn't free UNION space *here*, but the line-444 SECTION may have other waste.
4. **New UNION opportunities** — find pairs of cold non-UNION WRAM0 fields with mutually-exclusive timing that could be folded into a new UNION.
5. **WRAMX-spill the bank-1 trace block (28 B)** — moving trace state to WRAMX 3-7 frees 28 normal-build bytes in WRAMX bank 1, not in WRAM0; doesn't help the target directly but reclaims bank-1 reserve for future boss-AI.

20% WRAM0 target (810 B) may not be reachable without restructuring
the overworld map block buffer or removing link functionality.
**Honest plan needs to document the actual reachable number.**

## Iteration 5 — Batch 3 dispatch

| # | Agent | Subagent | Verifies |
|---|---|---|---|
| 1 | Non-UNION WRAM0 inventory | Explore | every WRAM0 field NOT in a UNION; rank by bytes |
| 2 | wSurroundingTiles deep-dive | Explore | 480 B UNION-sizer; what is it really? Hot/cold? Shrinkable? |
| 3 | wLinkData / link-feature audit | Explore | Is link still alive in this hack? If dead, can we shed all link RAM? |
| 4 | Dead-code WRAM symbols audit | Explore | wDebugOriginalColors + DebugColorPicker dead. What else? |
| 5 | UNION-opportunity audit | Explore | find pairs of cold non-UNION WRAM0 fields whose timing is mutually exclusive |

## Double-check protocol

For any candidate that lands in the plan's "Reach to 20%" section, the
provenance trail must be:

1. Agent A: claims `X bytes savable; symbol Y in file Z`.
2. Agent B (independent): re-greps for symbol Y across `engine/`, `home/`,
   `data/`, and confirms reader/writer counts match Agent A's claim.
3. If counts diverge: candidate demoted to "needs investigation"; no
   silent acceptance.

False positives in this domain are: (a) symbol that looks like a cache
but is actually live state read by other code paths, (b) ds N
allocation that's used as a pointer base, not an array, (c) WRAMX
candidate that's actually save-formatted and would break old saves.
