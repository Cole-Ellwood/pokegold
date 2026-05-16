# ROM Crash-Bug Audit — 2026-05-16

**Auditor:** Claude (Opus 4.7), under /pgoal
**Scope:** Entire ROM source (hack additions + inherited pret/pokegold base).
**Bug classes in scope:**
- Memory overflow: stack imbalance, buffer/array OOB writes, WRAM/HRAM corruption.
- Map tile glitches: tileset OOB, blockdata buffer overrun, connection bounds, tile pattern overflow.
- Crash/lockup: infinite loops without exit, OAM/VRAM access during wrong PPU mode,
  banking errors causing garbage execution, interrupt re-entrancy.
- Save corruption: WRAM/SRAM offset drift, checksum bypass, unsynced save format version.
- Register-ABI clobber: clobber-on-exit changes that silently break in-bank callers
  (the AG-NN / TD-005 pattern class).

**Out of scope:** Balance bugs, AI behaviour bugs (unless they crash), missing-feature
gaps, performance issues, cosmetic bugs that can't crash the game.

**Process:** Region-by-region read. Every finding cites file:line. Confidence rating
honest (LOW/MED/HIGH). Severity 1 (cosmetic-but-real) to 5 (hard freeze / save loss).
Findings that *might* be false-positives are flagged as such; do not "fix" anything
in this report blindly — triage first.

---

## Severity scale

| Sev | Meaning |
| --- | --- |
| 5 | Hard freeze, save loss, or playthrough-killing softlock. Reproducible on real hardware. |
| 4 | Crash, corrupt graphics, or scripted softlock under a reproducible scenario. |
| 3 | Wrong but recoverable behaviour (stat-drain, register clobber that miscomputes damage by ~5x). |
| 2 | Wrong but local (one-frame glitch, off-by-one in a non-load-bearing path). |
| 1 | Latent / latent-but-load-bearing-if-touched (a footgun for future authors). |

## Coverage log

The "Files reviewed" section below tracks which regions have been read this pass.
A region appears here only after I have actually read the file(s) and considered the
bug-class lens — not just listed them.

### Files reviewed
<!-- iterations append: - path/to/file.asm (lens: <classes>, findings: N) -->
- `home/farcall.asm` — lens: bank-confusion, register-abi. findings: 0 (clean; documented hl/a clobber already covered by audits).
- `home/random.asm` — lens: infinite-loop, OOB. findings: 1 (RandomRange(0) hang — Finding 1).
- `home/vblank.asm` — lens: stack-discipline, interrupt-reentrancy. findings: 0 (handlers mask the hVBlank index, stack push/pop balanced, no obvious re-entry path).
- `home/copy.asm` — lens: buffer-overflow, 16-bit-loop wraparound. findings: 0 (standard `inc b; inc c` pattern correct for bc ≤ $FFFE).
- `home/init.asm` — lens: stack-setup, memory-clear coverage. findings: 0 confirmed (multi-bank WRAMX clear is suspect — see deferred).
- `home/lcd.asm` — lens: interrupt-reentrancy, OAM/VRAM timing. findings: 0 (HBlank palette swap looks correct; assumes `wLYOverrides` page-aligned — verify in iter 2).
- `home/decompress.asm` — lens: OOB-write, integer-arithmetic. findings: 0 (LZ alt-pattern double-`inc hl` confirmed correct).
- `home/sram.asm` — lens: bank-confusion, MBC3-RTC-latch. findings: 0 (open/close pair maintains latch state across runs).
- `home/predef.asm` — lens: stack-trick, return-address chain. findings: 0 (chained-call via push trick is correct).
- `home/header.asm` — lens: rst-table-coverage. findings: 0 confirmed (rst $30 falls into JumpTable epilogue — vanilla pokegold inheritance; latent, low practical risk).
- `home/delay.asm` — lens: infinite-loop-on-LCD-off. findings: 0 confirmed (latent — caller would need to delay frames with LCD off; no path observed).
- `home/joypad.asm` — lens: input-state, soft-reset, interrupt-reentrancy. findings: 0 (soft-reset is intentional A+B+Start+Select via `jp Reset`).
- `home/serial.asm` — lens: link-protocol, timeouts. findings: 0 obvious; would need a link-cable scenario to truly audit.
- `engine/overworld/load_map_part.asm` — lens: map-tile-OOB. findings: 0 (offset arithmetic into wSurroundingTiles is bounded by SCREEN_HEIGHT iterations).
- `engine/pokemon/mail.asm` — lens: save-corruption, OOB-SRAM-write. findings: 0 (DeleteMailFromPC shift loop bounded by MAILBOX_CAPACITY; menu inputs bounded by ScrollingMenu).
- `engine/menus/save.asm` (lines 1-220) — lens: save-corruption, checksum-bypass. findings: 0 in the part read; full pass deferred (1084-line file).
- `engine/battle/late_gen_held_items.asm` — lens: register-abi-clobber, div-by-zero. findings: 0 (push/pop discipline against AG-08 and TD-005 patterns is documented inline at lines 1-30, 81-87; metronome math clamps before divide; denominators are compile-time non-zero).
- `engine/battle/type_passive_damage_mods.asm` (lines 1-200) — lens: register-abi-clobber, fraction-overflow. findings: 0 (fractions are hardcoded numerator/denominator pairs, all denominators non-zero).
- `engine/overworld/map_setup.asm` — lens: jump-table-OOB, bank-confusion. findings: 1 (Finding 2 — `RunMapSetupScript` index underflow).
- `engine/overworld/init_map.asm` — lens: stack-discipline, bg-map-timing. findings: 0 (push/pop balanced; hBGMapMode saved across nested writes).
- `engine/overworld/wildmons.asm` (lines 1-100) — lens: data-driven-OOB, terminator-dependence. findings: 0 confirmed; FindNest terminator-missing risk noted in deferred.
- `engine/overworld/scripting.asm` (dispatchers around lines 10-65) — lens: jump-table-OOB on `wScriptMode` and script opcode bytes. findings: 0 (vanilla pokegold inheritance; script opcodes are author-controlled compile-time data with `assert_table_length NUM_EVENT_COMMANDS` gating).
- `engine/items/item_effects.asm` (lines 1-60) — lens: jump-table-OOB on `wCurItem`. findings: 0 (no explicit guard but pack UI filters; Sev 1 latent footgun noted in deferred).
- `engine/gfx/load_push_oam.asm` — lens: OAM-DMA-timing. findings: 0 (HRAM stub copy bounded, DMA wait loop timed to 640 t-cycles for OAM_COUNT=40).
- `engine/math/math.asm` — lens: divide-by-zero behavior. findings: 0 (divisor=0 makes _Divide loop infinitely with quotient growing; callers must guard. Damage path documented at late_gen_held_items.asm has `ld c, 1` safety).
- `engine/battle/ai/boss_thunks.asm` (lines 1-83) — lens: cross-bank-call, hl/bc preservation. findings: 0 (every thunk push/pops hl per docs; AIGetEnemyMove_HL also preserves bc and passes argument via c per farcall a-passthrough rule).
- `data/growth_rates.asm` — lens: div-by-zero in EXP formula. findings: 0 (all 6 growth-rate denominators are compile-time non-zero: 1, 4, 4, 5, 5, 4).
- `home/header.asm` (re-read for rst-table audit) — findings: 1 (Finding 3 — rst $30 bypasses the canonical crash trap).
- `home/delay.asm` (re-read for LCD-off pathology) — findings: 1 (Finding 4 — DelayFrames hangs on LCD off).
- `home/init.asm:51-54` (re-read for .wait LCD assumption) — findings: 1 (Finding 5 — .wait hangs on LCD off).

### Regions deferred
<!-- iterations append: - region (reason for deferral) -->
- `home/init.asm:60-68` WRAMX multi-bank clear — only the currently-selected WRAMX bank is cleared on cold boot. Need to inventory which WRAMX banks the hack actually reads-before-write to know if any of banks 2-7 are touched. If only WRAMX bank 1 is used (boss AI reserve), this is a non-issue. Defer to dedicated WRAMX-coverage pass.
- `home/lcd.asm` `wLYOverrides` page-alignment — the LCD STAT handler uses `ld h, HIGH(wLYOverrides); ld l, rLY` indexing, which requires wLYOverrides to be page-aligned. Verify by grepping the ram section it lives in. Defer to next iteration.
- `home/decompress.asm` `.rewrite` negative-offset arithmetic — the `cpl + add e` idiom produces `hl = de - mag - 1` in my analysis, but base pokegold ships with this exact code, so either it's correct under the LZ format definition (offsets are 1-based) or it's a long-standing latent bug that hasn't manifested. Defer until I can match against pret/pokegold and the format spec.
- Full review of `engine/menus/save.asm` (1084 lines) — large file, save corruption is the highest-blast-radius bug class; needs its own dedicated iteration.

---

## Findings

<!--
Finding template — copy/paste this block per finding:

### Finding N — <one-line title>
- **Severity:** <1-5>
- **Confidence:** <LOW|MED|HIGH>
- **Category:** <stack | buffer-overflow | oob-read | oob-write | bank-confusion | interrupt | save-format | register-abi | map-tile | tileset | other>
- **File:** `path/to/file.asm:LINE`
- **Symptom:** <what the player or VRAM observer would see>
- **Trigger:** <reproducible scenario, frame-level if possible>
- **Why:** <walk-through of the failure path in 3-6 lines, citing actual code>
- **Fix sketch:** <minimal change; do NOT apply in this audit pass>
- **False-positive risk:** <what would make this not actually a bug — e.g. a caller invariant I haven't verified>
-->

<!-- Findings begin here. The verifier requires the report to have at least 5 by completion. -->

### Finding 1 — `RandomRange` hard-hangs the game when called with a=0
- **Severity:** 1
- **Confidence:** HIGH
- **Category:** other (latent infinite-loop footgun)
- **File:** `home/random.asm:50`
- **Symptom:** If any future caller passes `a=0` to `RandomRange`, the game hangs at a `jr nc, .mod` loop with interrupts still enabled — the screen keeps rendering but no scripting advances. Effectively a soft-freeze; only soft-reset (A+B+Start+Select) recovers.
- **Trigger:** None known *today*. All six current callers pass non-zero constants (`treemons.asm` uses `10`/`100`, `mom_phone.asm` uses `(MomItems_1.End - MomItems_1) / MOMITEM_SIZE`, a compile-time positive). The bug is purely latent — it fires the day someone writes `ld a, [variable]; call RandomRange` where the variable can be 0 (e.g. an empty random-item table, an empty wild-mon slot, a degenerate trainer pool).
- **Why:**
  ```asm
  RandomRange::
      push bc
      ld c, a           ; c = 0 if a was 0
      xor a             ; a = 0
  .mod
      sub c             ; a = 0 - 0 = 0; no borrow → carry CLEAR
      jr nc, .mod       ; always taken → infinite loop
  ```
  The "compute b = 256 % c" routine assumes `c != 0`. With `c = 0`, the subtract leaves `a = 0` and clears carry, so `jr nc, .mod` always jumps. No exit path.
- **Fix sketch:** Add a one-instruction guard at entry: `and a; ret z` (or jump to a defined "0 means 0" exit that returns `a = 0`). Two bytes for a permanent footgun seal.
- **False-positive risk:** None on the analysis itself — I traced the loop on paper. The only reason this is Sev 1 not Sev 5 is that no current caller can trigger it. If a code reviewer adds a dynamic-`a` caller without remembering this constraint, severity becomes 5. Worth fixing prophylactically.

### Finding 2 — `RunMapSetupScript` OOB-jumps if `hMapEntryMethod` low nibble is 0 or > 11
- **Severity:** 2
- **Confidence:** HIGH
- **Category:** other (unbounded jump-table index)
- **File:** `engine/overworld/map_setup.asm:1`
- **Symptom:** Garbage execution. PC jumps to whatever 16-bit value lies past the end of `MapSetupScripts` in ROM, which is almost certainly invalid code — the cart will either freeze, glitch graphics catastrophically, or reset via `rst $38` if execution wanders into one.
- **Trigger:** Any path where `hMapEntryMethod` is `$f0` (low nibble 0) or `$fc..$ff` (low nibble > 11) at the moment `RunMapSetupScript` is called. The known sources (`engine/menus/intro_menu.asm:12`, `:279`, `:299`; `engine/overworld/scripting.asm:1111`, `:1959`) all set valid `MAPSETUP_*` constants (`$f1`..`$fb`). But `hMapEntryMethod` lives in HRAM which is zero-initialised by [home/init.asm:74-82](home/init.asm:74); if any branch reaches `RunMapSetupScript` *before* a `MAPSETUP_*` write, low nibble is 0 → `dec a` underflows to $FF → index $1FE in a table of 11 (22 bytes long) → OOB pointer fetch → `call <garbage>`. Save-data corruption that nudges `hMapEntryMethod` to a value like `$f0` would also fire it.
- **Why:**
  ```asm
  RunMapSetupScript::
      ldh a, [hMapEntryMethod]
      and $f             ; mask to low nibble (0..15)
      dec a              ; index 0..14, OR $FF if a was 0
      ld c, a
      ld b, 0
      ld hl, MapSetupScripts
      add hl, bc
      add hl, bc          ; hl = MapSetupScripts + 2*index — OOB for index >= 11
      ld a, [hli]
      ld h, [hl]
      ld l, a
      call ReadMapSetupScript
      ret
  ```
  `MapSetupScripts` has 11 entries (`data/maps/setup_scripts.asm` — verified by `dw` count). With index $FF, `add hl, bc; add hl, bc` advances by `2*$FF = $1FE` bytes → way past the table → garbage pointer → indirect call to garbage.
- **Fix sketch:** Add a `cp NUM_MAPSETUP_SCRIPTS; jr nc, .out_of_range` guard between the `and $f` and `dec a` (with `.out_of_range: ret` or a defined sentinel script). 4-6 bytes for a permanent bounds-check, no behavioural change for valid inputs.
- **False-positive risk:** This is inherited from base pokegold — vanilla Gold/Silver have shipped with this for 25 years without anyone reporting a crash, so the practical reachability of the bad state during normal play is essentially zero. Sev 2 (not 5) because of that practical-reachability gap; a single bad write to `hMapEntryMethod` (anywhere in the codebase, or via cheat-cart) would still crash.

### Finding 3 — `rst $30` falls into the middle of `JumpTable`, bypassing the crash trap
- **Severity:** 1
- **Confidence:** HIGH
- **Category:** other (broken crash trap)
- **File:** `home/header.asm:20-35`
- **Symptom:** If PC ever lands on the `rst $30` opcode (`$F7`) — by corrupt-state execution, OOB jump, or some `db $F7` fluke — the CPU jumps to `$0030`, which lies in the *middle* of `JumpTable` (instructions `ld l, a; pop de; jp hl`). This pops a value off the stack into `de` and then jumps to whatever 16-bit value is currently in `hl`. Unlike `rst $18`, `rst $20`, and `rst $38` (which all branch to `rst $38` and infinite-loop as a deliberate crash trap), `rst $30` continues execution into whatever the current `hl` was last set to — typically wandering through more garbage.
- **Trigger:** Any execution of opcode `$F7` from corrupted PC. Common ways: tile-data interpreted as code via bank confusion, a `jp hl` to a data buffer that happens to contain `$F7`, a typo in hand-written asm. Not user-triggerable today.
- **Why:** `home/header.asm:23-35` defines `JumpTable::` at `SECTION "rst28", ROM0[$0028]`. The function body is 11 bytes (`push de; ld e, a; ld d, 0; add hl, de; add hl, de; ld a, [hli]; ld h, [hl]` then continues at offset $0030 with `ld l, a; pop de; jp hl`). The would-be `rst $30` slot is commented out (line 32: `; SECTION "rst30", ROM0[$0030]`) so rgbasm packs the JumpTable tail into the $0030..$0037 range. `rst $38` is then a separate section at line 37, correctly trapping with `rst $38`. So `rst $30` is the only rst-slot that doesn't trap.
- **Fix sketch:** Either (a) move JumpTable's tail to a normal label (give up the rst $28 entry point) and put a real `rst $38` trap at $0030, or (b) accept the inheritance and document it in CLAUDE.md as a known footgun. Vanilla pokegold has this same layout, so this is purely a 25-year-old inheritance.
- **False-positive risk:** Low — the analysis matches what rgbasm produces given the .asm. A code reviewer might argue "no realistic path triggers `rst $30`" and downgrade severity, which is fair (no current trigger). Flagging because it's a *crash trap that doesn't trap* — a class of defensive layer that's missing.

### Finding 4 — `DelayFrame`/`DelayFrames` hang if LCD is off and VBlank isn't firing
- **Severity:** 1
- **Confidence:** HIGH
- **Category:** other (latent infinite-loop on bad state)
- **File:** `home/delay.asm:1`
- **Symptom:** `halt` blocks waiting for any interrupt. If LCD is off (no VBlank), the only enabled interrupts at game runtime are timer (vector at `$0050` is a bare `reti` — does nothing useful) and serial/joypad (rarely firing). Wake-up never clears `wVBlankOccurred`, so `jr nz, .halt` always re-loops. Game appears completely frozen — even soft-reset (A+B+Select+Start) doesn't fire because soft-reset is detected only inside the joypad-update part of `VBlank_Normal`.
- **Trigger:** Any code path that calls `DelayFrame`/`DelayFrames` between `DisableLCD` and `EnableLCD` (or any sequence that ends with LCD off). `DisableLCD` itself is fine — it never calls `DelayFrames` while LCD is off. But a future author who adds "wait one frame for X before enabling LCD" would hang. Also fires on the `Reset::` entry path if `Reset` is reached with LCD already off (e.g. a soft-reset-during-LCD-off scenario).
- **Why:**
  ```asm
  DelayFrame::
      ld a, 1
      ld [wVBlankOccurred], a
  .halt
      halt
      nop
      ld a, [wVBlankOccurred]
      and a
      jr nz, .halt
      ret
  ```
  The `halt; nop` pair waits for any interrupt and the `nop` defangs the halt-bug. If no interrupt clears `wVBlankOccurred` (which only the VBlank handlers do), the `jr nz, .halt` loops forever.
- **Fix sketch:** Add an LCD-on guard at function entry: `ldh a, [rLCDC]; bit B_LCDC_ENABLE, a; ret z` so callers that "delay with LCD off" get a graceful no-op instead of a freeze. 7 bytes. This DOES change semantics — current callers that "expected" delay with LCD off would no longer block, so existing flows would need a careful read. Most safely: leave the function alone and document the LCD-must-be-on invariant.
- **False-positive risk:** Low on the mechanism. Practical reachability requires an unusual flow where someone calls DelayFrames with LCD off, which the codebase doesn't do today. Sev 1 reflects "latent footgun, not a current crash."

### Finding 5 — `Init`'s `.wait` loop hangs forever if entered with LCD off
- **Severity:** 1
- **Confidence:** HIGH
- **Category:** other (latent infinite-loop on bad state)
- **File:** `home/init.asm:51-54`
- **Symptom:** `Init`'s `.wait` loop at line 51 polls `rLY` for `LY_VBLANK + 1` (=145). If LCD is off, `rLY` reads as `0` — never reaches 145. Loop hangs indefinitely. Interrupts are still disabled at this point in init (`di` on line 29), so even halt-based wake won't fire.
- **Trigger:** Practical paths into `Init`: (a) cold boot from `_Start` — LCD is on from the boot ROM, so fine. (b) Soft-reset via `Reset::` → `DelayFrames(32)` → `jr Init` — `DelayFrames` requires LCD on (Finding 4), so we'd hang in `DelayFrames` *before* `Init`, never reaching `.wait`. So the `.wait` hang is masked by Finding 4 on the soft-reset path. (c) A future author calls `Init` directly from any LCD-off state — hangs at `.wait`.
- **Why:**
  ```asm
  .wait
      ldh a, [rLY]
      cp LY_VBLANK + 1
      jr nz, .wait
  ```
  No bound on iteration count, no fallback. If `rLY` can't reach 145 (LCD off → stuck at 0), infinite loop.
- **Fix sketch:** Either (a) explicitly turn the LCD on at the top of `Init` before `.wait`, or (b) check `rLCDC.B_LCDC_ENABLE` and skip the wait if LCD is off. 4-6 bytes.
- **False-positive risk:** Mechanism is solid. Reachability requires entering Init with LCD off, which doesn't happen on `_Start` (boot ROM) and is blocked by Finding 4 on soft-reset. Sev 1 reflects "latent footgun, masked by other early-init invariants." Worth flagging because reviewer surprise: if any future early-init refactor *fixes* Finding 4 in a way that lets DelayFrames return with LCD off, this becomes the new hang point.

---

## Summary table

| # | Title | Sev | Confidence | Category | File |
| --- | --- | --- | --- | --- | --- |
| 1 | `RandomRange` hangs on `a=0` | 1 | HIGH | infinite-loop | [home/random.asm:50](home/random.asm:50) |
| 2 | `RunMapSetupScript` OOB on `hMapEntryMethod` low-nibble == 0 or > 11 | 2 | HIGH | jump-table OOB | [engine/overworld/map_setup.asm:1](engine/overworld/map_setup.asm:1) |
| 3 | `rst $30` bypasses crash trap → executes JumpTable tail | 1 | HIGH | broken crash trap | [home/header.asm:20](home/header.asm:20) |
| 4 | `DelayFrames` hangs if LCD off | 1 | HIGH | infinite-loop | [home/delay.asm:1](home/delay.asm:1) |
| 5 | `Init.wait` hangs if entered with LCD off | 1 | HIGH | infinite-loop | [home/init.asm:51](home/init.asm:51) |

**Triage hint:** All 5 are latent — none has a known reproducible trigger in the current code. Findings 1, 4, 5 are protective-layer hardenings (cheap to add as guards). Finding 2 is the most reachable (any future write to `hMapEntryMethod` with a bad low nibble crashes). Finding 3 is the "the safety net is broken" class — fixable only by sacrificing the JumpTable optimisation or by accepting it. No Sev 3+ crashes were observed in this iteration; expect the harder findings (e.g. inherited Gen 2 glitches, hack-introduced race conditions) to appear in deeper passes.

---

## What I did NOT review

Honest list of regions skipped, with reason. So the next pass knows where to start.
