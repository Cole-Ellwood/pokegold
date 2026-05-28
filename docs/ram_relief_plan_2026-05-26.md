# RAM Relief Plan — 2026-05-26

**Status:** investigation complete; ready for Cole's review of top-3 before any implementation slice.
**Author:** Claude (under /pgoal, read-only iteration).
**Approver:** Cole.
**Working log:** [ram_relief_scratchpad_2026-05-26.md](ram_relief_scratchpad_2026-05-26.md).

## Goal

Use the 14 excess ROM banks (largest: 13 / 22 / 27 each with 16384
free per `docs/generated/dev_index.md`) to relocate RAM-resident data
out of the tightest RAM regions. Target: **20% reduction in used
bytes** across the pool of HRAM (127 used, 0 free) + WRAM0 (4049
used, 47 free) = **~835 bytes savable** at full target.

Read-only iteration. Deliverable is this plan. Implementation
happens in a follow-up slice after Cole sign-off on top candidates.

## Targets

| Region | Used | Free | 20% target |
|---|---:|---:|---:|
| HRAM | 127 | 0 | 25 B |
| WRAM0 | 4049 | 47 | 810 B |
| **Pool** | **4176** | **47** | **835 B** |

## Method

Two batches of 5 parallel Explore subagents (10 total), each
read-only. Batch 1 inventoried WRAM0/HRAM/WRAMX and surfaced
candidate fields. Batch 2 verified the top-5 Batch-1 candidates by
independent re-grep. Batch 3 (5 more agents) repaired the candidate
set after Batch 2 falsified most Batch-1 claims. The verification
pattern caught false positives that would otherwise have shipped as
"relief opportunities" with 0 actual relief.

Findings below are graded by **confidence after double-check** plus
**effective relief after UNION accounting** — *not* by the byte size
of the symbol itself. A 1024-byte symbol that sits inside a UNION
whose largest other peer is also large frees zero bytes when removed
alone; the plan lists effective relief, not gross symbol size.

## Ranked opportunities

Each opportunity lists: byte cost, risk class, relocation target,
file:line. Confidence is double-checked unless noted.

### Opportunity 1: Remove `wUnusedMapBuffer`

- **Bytes:** 24 (effective: 24, not in UNION)
- **File:line:** [ram/wram.asm:394-400](../ram/wram.asm)
- **Risk class:** Low
- **Relocation target:** Removal (not relocation)
- **Status:** dead code. Comment explicitly notes "retained for WRAM
  layout" — legacy holdover from a removed prototype map pointer
  buffer; no readers / writers in `engine/` or `home/`.
- **Confidence:** High.

### Opportunity 2: New UNION — `wLYOverrides` + `wMovementBuffer`

- **Bytes:** 55 (effective: 55 if timing audit passes)
- **File:line:** [ram/wram.asm:558](../ram/wram.asm) +
  [ram/wram.asm:1389](../ram/wram.asm)
- **Risk class:** Medium (timing audit needed)
- **Relocation target:** new WRAM0 UNION
- **Why mutually exclusive:** wLYOverrides is the scanline-effect
  buffer touched during battle transitions / battle animations. wMovementBuffer is the NPC/trainer movement script
  queue touched during overworld script execution. The player is
  in *either* a battle or the overworld, never both — so the bytes
  can share an address slot.
- **Required pre-merge verification:** confirm wLYOverrides is cleared
  before exiting battle, wMovementBuffer is cleared before entering
  battle, and the scanline IRQ doesn't latch a stale wLYOverrides
  read post-battle.
- **Confidence:** High on the concept; medium on the timing audit.

### Opportunity 3: ~~WRAMX-spill `wBGMapBuffer`~~ — REFUTED by Batch 4

- **Bytes:** 80 (effective: 0 — DO NOT SHIP)
- **File:line:** [ram/wram.asm:987-991](../ram/wram.asm)
- **Verdict (Batch 4 / agent 3):** `UpdateBGMapBuffer` is called
  **every vblank** from
  [home/vblank.asm:99](../home/vblank.asm:99) and
  [home/vblank.asm:364](../home/vblank.asm:364). The function reads
  `wBGMapBuffer` directly via tight VRAM-copy loops
  ([home/video.asm:21, 45-50](../home/video.asm)). Estimated
  per-vblank reads ≈ 20 × 16-cycle bank-switch tax = ~320 cycles =
  ~28% of the per-vblank budget. Unacceptable lag.
- **Status:** DROP from the implementation slice. Earlier Batch 1
  / Batch 3 agents misclassified this as cold; Batch 4's deeper
  read of the vblank ISR caught it.

### Opportunity 4: WRAMX-spill `wSGBPals`

- **Bytes:** 48 (effective: 48)
- **File:line:** [ram/wram.asm:1003](../ram/wram.asm)
- **Risk class:** Low (cold; SGB fallback only)
- **Relocation target:** WRAMX bank 3 (alongside Opportunity 3)
- **Confidence:** High.

### Opportunity 5: WRAMX-spill `wRadioText`

- **Bytes:** 40 (effective: 40)
- **File:line:** [ram/wram.asm:1376](../ram/wram.asm)
- **Risk class:** Low (cold; radio/phone screens only)
- **Relocation target:** WRAMX bank 3
- **Confidence:** High.

### Opportunity 6: New UNION — `wBattleScriptBuffer` + `wMovementBuffer`

- **Bytes:** 40 (effective: 40)
- **File:line:** [ram/wram.asm:759](../ram/wram.asm) +
  [ram/wram.asm:1389](../ram/wram.asm)
- **Risk class:** Low
- **Conflict:** Opportunity 2 also uses `wMovementBuffer`. Only one
  of {Opportunity 2, Opportunity 6} can ship as-is. Opportunity 2
  is preferred (more bytes), but a three-way UNION of
  `wLYOverrides` + `wBattleScriptBuffer` + `wMovementBuffer` may be
  possible if both audits pass — freeing 95 bytes.
- **Confidence:** High.

### Opportunity 7: Remove `wSafariMonAngerCount`

- **Bytes:** 1 (effective: 1)
- **File:line:** [ram/wram.asm:830](../ram/wram.asm)
- **Risk class:** Low
- **Status:** Dead — no readers/writers found in `engine/` or
  `home/`. Single-byte symbol; pure win.
- **Confidence:** High.

### Opportunity 8: WRAMX-spill `wStringBuffer5`

- **Bytes:** ~21 (effective: depends on cross-screen analysis)
- **File:line:** [ram/wram.asm:~1642-1646](../ram/wram.asm)
- **Risk class:** Medium-High (string buffers are used across screens
  including battle and menu text; cross-screen UNION blocked)
- **Relocation target:** WRAMX bank 3 IF an audit confirms string
  buffer access is not bank-switch-sensitive
- **Confidence:** Low; needs investigation before promotion.

### Opportunity 9: Move boss-AI trace block to WRAMX bank 3

- **Bytes:** 28 (frees WRAMX bank-1 reserve, NOT WRAM0)
- **File:line:** [ram/wram.asm:2482-2494](../ram/wram.asm)
- **Risk class:** Low
- **Caveat:** This does **not** count toward the WRAM0 target. It
  frees 28 bytes in the boss-AI reserve (bank 1), which is at 0
  free under `BOSS_AI_TRACE`. Includes for completeness because
  future boss-AI work (P5 / P7 from the roadmap) wants this room.
- **Confidence:** High.

### Opportunity 10: Shrink `wOverworldMapBlocks` (advisory only — not for this slice)

- **Bytes:** up to 1300 (effective: up to 1300, would unlock the
  "Overworld Map" UNION's 1300-byte floor)
- **File:line:** [ram/wram.asm:406-407](../ram/wram.asm)
- **Risk class:** **High** — HOT field, read per-frame in
  overworld via `GetMapScreenCoords` (home/map.asm:1029) and
  `GetBlockLocation` (home/map.asm:2046). Moving to WRAMX adds
  ~16 cycles per read; at 20-30 reads/frame, ~5-8% CPU overhead in
  overworld. Shrinking requires re-architecting the block cache
  (smaller window + edge-streaming) which is its own design pass.
- **Why listed:** This is the ONLY path to actually hitting 20% in
  WRAM0. Listing as an advisory item — Cole's call whether to open
  it.
- **Confidence:** N/A (architectural decision, not a tactical fix).

### Opportunity 11: Remove `wDebugOriginalColors` + `DebugColorPicker`

- **Bytes:** 1024 declared (effective: **0** because the symbol
  lives in the 1300-byte "Overworld Map" UNION whose floor is set
  by `wOverworldMapBlocks` and `wLinkData`)
- **File:line:** [ram/wram.asm:444](../ram/wram.asm); function at
  `engine/debug/color_picker.asm:35`
- **Risk class:** Low to remove (dead code)
- **Why listed despite 0 effective relief:** the symbol is genuinely
  dead — NOT gated by `IF DEF(_DEBUG)` despite the name, and its
  consumer `DebugColorPicker` is never called. Removing it doesn't
  free RAM today but unblocks Opportunity 10's relief calculation
  (one fewer 1024-byte peer to worry about when re-architecting
  the UNION) and removes 1024 bytes of dead code in ROM. **Listed
  as a hygiene item, not a relief item.**
- **Confidence:** High (dead-code claim verified).

## Top-3 with Proof blocks

The three opportunities with highest (bytes × confidence × low risk)
ratio. Each has an independently-verified reader/writer trace.

### #1 — Opportunity 1: `wUnusedMapBuffer`

#### Proof

- **Declaration:** [ram/wram.asm:394-400](../ram/wram.asm). The
  comment around the declaration explicitly identifies this as a
  legacy buffer.
- **Readers/writers:** Batch 3 / Agent 4 (dead-code audit) and
  Batch 1 / Agent 5 (largest WRAM0 blocks) independently
  found zero references in `engine/`, `home/`, `data/`. The symbol
  name itself contains "Unused".
- **UNION membership:** Not in a UNION — standalone.
- **Relief math:** 24 bytes removed = 24 bytes WRAM0 freed.

### #2 — Opportunity 2: `wLYOverrides` + `wMovementBuffer` UNION

#### Proof

- **wLYOverrides declaration:** [ram/wram.asm:558](../ram/wram.asm)
  + [ram/wram.asm:570](../ram/wram.asm) (`wLYOverridesBackup`). Each
  is 144 bytes (`SCREEN_HEIGHT_PX`). The 55-byte relief refers to
  taking advantage of *min(144, 55)* = 55 when paired with a
  55-byte overworld field.
- **wMovementBuffer declaration:**
  [ram/wram.asm:1389](../ram/wram.asm). 55 bytes.
- **Mutual exclusion evidence (Batch 3 / Agent 5):** wLYOverrides
  call sites are all in `engine/battle/battle_transition.asm` and
  `engine/battle_anims/anim_commands.asm` — battle-only.
  wMovementBuffer call sites are in `engine/events/trainer_scripts.asm`
  and the overworld script dispatcher — overworld-only. Player
  cannot be in both at the same `wBattleMode` value.
- **Pre-merge gates** (must be re-verified at implementation time):
  - wLYOverrides cleared in the battle-exit sequence before
    returning to overworld
  - wMovementBuffer not still pending when a wild/trainer encounter
    triggers (typical pattern: movement script completes before
    encounter activation)
  - Scanline IRQ does not read wLYOverrides after the battle's
    final vblank
- **Relief math:** 55 bytes freed by overlaying wMovementBuffer
  onto the first 55 bytes of the wLYOverrides slot. wLYOverrides
  itself retains its full 144 bytes during battle; wMovementBuffer
  occupies the same address during overworld.

### #3 — Opportunity 4+5: WRAMX-spill cold standalone pair (Opp 3 dropped — see refutation above)

Bundled because they share the relocation target (WRAMX bank 3) and
move via the same plumbing. **wBGMapBuffer originally included but
removed after Batch 4 refutation** — see Opp 3 entry above.

#### Proof

- **wSGBPals:** 48 B at [ram/wram.asm:1003](../ram/wram.asm). Cold
  Super Game Boy palette fallback; only active when SGB hardware
  detected at boot. Confidence high.
- **wRadioText:** 40 B at [ram/wram.asm:1376](../ram/wram.asm).
  Cold; radio/phone text rendering only. Confidence high.
- **WRAMX bank 3 availability** (Batch 1 / Agent 3 + Batch 4 /
  Agent 5 re-verified): banks 3, 4, 5, 6, 7 each have zero SECTIONs
  declared in `ram/wram.asm`. Linker map confirms zero allocation
  in those banks. True relief hosts.
- **Relief math:** 48 + 40 = **88 bytes** freed from WRAM0;
  reappear as 88 bytes in WRAMX bank 3 (still has ~8100 free after).

## Could not reach 20% — honest accounting

Aggregating verified relief from Opportunities 1, 2, 4+5, 7 (Opp 3
dropped per Batch 4):

| Opportunity | Bytes |
|---|---:|
| 1 — Remove wUnusedMapBuffer (Batch 4 confirmed dead) | 24 |
| 2 — wLYOverrides + wMovementBuffer UNION (Batch 4 confirmed timing safe) | 55 |
| 4+5 — WRAMX-spill wSGBPals + wRadioText | 88 |
| 7 — Remove wSafariMonAngerCount | 1 |
| **Subtotal — conservative, post Batch-4** | **168** |
| 3 — wBGMapBuffer WRAMX (Batch 4 REFUTED — per-vblank hot) | 0 |
| 6 — wBattleScriptBuffer joining 3-way UNION (gated on second timing audit) | +40 |
| 8 — wStringBuffer5 WRAMX-spill (low confidence — needs investigation) | ~21 |
| **Subtotal — aggressive (Opp 6 three-way + Opp 8)** | **229** |

**~165–230 bytes ≈ 4.0–5.5% of WRAM0 used. Falls short of the 810-byte
20% target by ~580+ bytes. Batch-4 refutation of Opp 3 lost the
single largest WRAMX-spill candidate.**

**HRAM separately: ~8 movable bytes vs 25 target.** HRAM cannot reach
20% under any plausible move — the math UNION (5 B), IO shadows (8 B),
bank-switch shadows (3 B), and hot scratch (~16 B) are immovable by
hardware / hot-path reality (Batch 1 / Agent 2 verification).

### Why 20% isn't reachable without architectural moves

Two structural facts block the simple "move field X" approach:

1. **The 1300-byte "Overworld Map" UNION** at
   [ram/wram.asm:403-527](../ram/wram.asm) has *two* 1300-byte
   peers: `wOverworldMapBlocks` (HOT — per-frame overworld reads)
   and `wLinkData` (cold but live — link is fully functional in
   this hack per Batch 3 / Agent 3 audit; removing it corrupts
   save-state for any user who trades). UNION mechanics mean
   removing the third peer `wDebugOriginalColors` (1024 B, dead
   code) frees zero bytes because the two 1300-B peers still
   dictate the floor.

2. **The 480-byte "Miscellaneous" UNION** at
   [ram/wram.asm:162-200](../ram/wram.asm) is sized by
   `wSurroundingTiles` (480 B), the overworld metatile region
   buffer that's load-bearing for the map-blit pipeline (Batch 3 /
   Agent 2). Shrinking it requires redesigning the screen-edge
   tile streaming. Other peers (wBoxPartialData, wTempTilemap,
   wPlayerPatchLists, wSpriteAnimData, …) are all ≤ 480 B and
   gain nothing from moving since the floor is set by
   wSurroundingTiles.

To actually hit 20%, one of the following architectural moves is
required (each is its own design pass):

- **Shrink `wOverworldMapBlocks`** by ~500–800 bytes via a smaller
  block window + edge-streaming. High risk (HOT path) — Cole's call.
- **Move `wOverworldMapBlocks` to WRAMX** with the 5–8% CPU overhead
  documented above. Probably unacceptable for overworld feel.
- **Remove link feature + bump SAVE_FORMAT_VERSION.** Frees
  `wLinkData` 1300-B peer, but the UNION floor is still set by
  `wOverworldMapBlocks` at 1300, so this alone gives 0 relief
  unless wOverworldMapBlocks also moves/shrinks. Plus link removal
  is a feature regression Cole hasn't approved.
- **Shrink `wSurroundingTiles`** by halving the metatile window.
  Saves up to 240 B from the Miscellaneous UNION. Requires
  re-architecting the map blit code.

None of these belong in a one-shot RAM-relief slice. They're
roadmap items in their own right.

## Open risks and follow-ups

1. **Opp 2 timing audit.** Before implementing the
   wLYOverrides+wMovementBuffer UNION, an audit must trace every
   reader/writer of both fields across the battle-to-overworld and
   overworld-to-battle transitions. If wLYOverrides leaks past the
   battle exit, the UNION corrupts wMovementBuffer the first time a
   movement script fires.

2. **boss_ai_spec.md staleness.** Bank-1 reserve doc claim is off
   by 1–2 bytes after P-A's `wBossAILookaheadRunningBest` landed
   (Batch 2 / Agent 5 reconciliation). The dev_index is canonical
   (28 free normal / 0 free trace); the spec needs a refresh in a
   future slice. Not load-bearing for this plan.

3. **`wDebugOriginalColors` + `DebugColorPicker` cleanup.** Real
   dead code (Batch 3 / Agent 4). Worth removing for hygiene even
   though it frees 0 WRAM0 bytes today. Removing also prevents the
   pattern recurring — the absence of `IF DEF(_DEBUG)` despite the
   name was a real bug.

4. **Bank 0e (boss AI ROM, 2 bytes free).** Cole's earlier question
   about fitting `BossAI_PickFaintReplacement`'s 4×-weak fix needs
   ~16 ROM bytes in bank 0e. This RAM-relief plan does NOT
   address that — it's a separate ROM-bank relocation question.
   The recommended path stays: relocate `BossAI_PickFaintReplacement`
   to bank 13/22/27 via `callfar`.

5. **20% target shortfall.** This plan reaches ~6–7%. If Cole still
   wants the full 20%, the next step is opening Opportunity 10
   (`wOverworldMapBlocks` shrink/move) as its own design pass with
   its own GPT review, not a RAM-relief slice. Until then,
   accept the realistic ~250-byte relief.

## Negative effects of this plan

Honest accounting of downsides if the recommended slice ships:

1. **Static analysis only — no runtime confirmation.** All ten
   subagents read source and grepped. None ran the ROM. Batch 4
   already caught one false-cold claim (Opp 3 / wBGMapBuffer); a
   fifth batch could catch another. The damage_debugger and
   boss_ai_debugger harnesses are NOT used in this iteration.
2. **Opp 2 UNION is fragile to future code.** wLYOverrides ↔
   wMovementBuffer safety depends on `hLCDCPointer` staying 0 in
   overworld. Any future feature that re-enables the LCD STAT IRQ
   in overworld (custom scanline effect, parallax, etc.) silently
   corrupts wMovementBuffer. Surprising-regression class.
3. **Opp 4 / Opp 5 (WRAMX-spill) adds bank-switch tax** of ~16
   cycles per read to wSGBPals and wRadioText. Acceptable for cold
   fields but real. Increases the cost of any future feature that
   wants to touch those fields more frequently.
4. **Dead-symbol removal loses the address slot.** If a future
   revival of debug color-picker / Safari rage / unused map buffer
   wants those slots back, they need new homes. Minor but real.
5. **20% target NOT reached.** Post-Batch-4, conservative reach is
   ~168 B / ~4%. Cole's stated goal needs architectural surgery
   (Opp 10 — wOverworldMapBlocks shrink/move) as a separate design
   pass; this plan does not get there.
6. **Bank 0e ROM tightness NOT addressed.** Earlier
   BossAI_PickFaintReplacement 4×-weak switch fix needed ~16 ROM
   bytes in bank 0e; this RAM-relief plan does NOT help that.
   Different memory region; different fix (`callfar` relocation).
7. **Opportunity cost.** This iteration's tool budget was spent on
   RAM analysis instead of: (a) the boss-AI switch bug, (b) P-A
   commit, (c) P2/P3 boss-AI phases per the future roadmap.
8. **Save-format risk: LOW.** None of the surviving top-2 touch
   save-formatted state. No SAVE_FORMAT_VERSION bump needed.
9. **Batch-4 reversal cost** demonstrates the value of the
   double-check protocol but also shows the limits of static
   analysis. A future "Batch 5" timing audit could surface that
   Opp 4 or Opp 5 has a per-frame reader nobody caught.

## Recommendation for next slice (post Batch-4)

If Cole signs off, implement Opportunities 1 + 2 + 4+5 + 7 in a
single ~168-byte WRAM0 relief slice:

- Remove wUnusedMapBuffer (Opp 1) — 24 B
- Remove wSafariMonAngerCount (Opp 7) — 1 B
- New UNION wLYOverrides + wMovementBuffer (Opp 2) — 55 B (Batch 4
  confirmed timing safe; ship as-is)
- WRAMX-spill wSGBPals + wRadioText to WRAMX bank 3 (Opp 4+5) —
  88 B (Batch 4 confirmed bank 3 truly empty)

DO NOT ship: Opp 3 (wBGMapBuffer — Batch 4 refuted as per-vblank hot).

Plus the hygiene removal (Opp 11): delete `wDebugOriginalColors` +
`DebugColorPicker` (0 RAM relief but cleans 1024 B of dead code).

Verification floor: build green, release_smoke, farcall audits,
boss_ai audits, save_format_version (no save format change, so
should be green), clobber_smoke (cheap to run). **Plus an
emulator-step verification:** run the implementation slice in
PyBoy or BGB, enter+exit a battle, walk into NPC trigger, save and
load — confirm no visible regression. This is the runtime check
that the static analysis cannot provide.

If Cole wants the additional ~3-5% relief, also pursue Opp 6 (the
three-way wLYOverrides + wBattleScriptBuffer + wMovementBuffer
UNION) — gated on a second timing audit for the wBattleScriptBuffer
side.

If Cole wants the full 20%, open Opportunity 10 (wOverworldMapBlocks
shrink) as its own design pass with a GPT round of review.
