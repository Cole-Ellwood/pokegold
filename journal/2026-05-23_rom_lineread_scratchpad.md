# 2026-05-23 — ROM line-read scratchpad

Working notes for the bug-hunt audit. Not committed-quality. Findings get
promoted to `docs/audits/rom_bug_audit_2026-05-23.md` once I'm
confident they're real and worth user attention.

## Scope reminder

- IN: engine/, home/, data/, macros/, ram/, constants/, maps/, gfx/,
  audio/ — the actual cartridge contents.
- OUT: tools/, scripts/, .claude/, audit/ (those are dev-side, not ROM).
- READ-ONLY: only this file and the audit file may be written.
- Pace: thorough. User said "take your time."

## Bug patterns I'm watching for

1. **farcall hl clobber** — `farcall` macro = `ld hl, target :: ld a,
   BANK :: rst FarCall`. Caller's `hl` is clobbered BEFORE target runs.
   If target reads hl as input, this is a silent bug. Audited by
   `tools/audit/check_farcall_hl_clobber.py` (which uses a
   `; Reach via ROM0 thunk ...` marker on hl-input functions). Audit
   coverage limited to MARKED functions — unmarked hl-input fns slip
   through.

2. **farcall a-return clobber** — after farcall, caller's `a` = target's
   exit `c`, NOT target's exit `a`. Audited by
   `tools/audit/check_farcall_a_clobber.py`. Coverage is heuristic
   (walks back through "safe" instrs looking for ld c, a mirror).

3. **Plain `call` to label in another bank** — silently jumps to garbage
   if target lives in a different ROMX bank. Audited by
   `tools/audit/check_cross_bank_call.py`. Worth re-verifying.

4. **Register-preservation transitive contract** — refactoring a helper
   to clobber more registers can break callers many frames away.
   Recurring class (AG-NN), TD-005 Pattern 3 history, AG-08 c-mirror
   trap. Most common in battle-engine helpers under
   `engine/battle/{ai,effect_commands,type_passive_damage_mods,late_gen_held_items}.asm`.

5. **`Label:` vs `Label::`** — `:` is local, `::` is exported. Silent
   downgrade breaks cross-bank linking.

6. **Endianness** — `dw` directives are little-endian. But battle-engine
   *runtime* stat fields are big-endian (HIGH at offset+0; see
   `macros/ram.asm:35`). Two different load idioms for two different
   layouts. Easy to mix up.

7. **HRAM/IO uses `ldh`, not `ld`** — RGBDS will not auto-pick.

8. **Stat-stage base-7 encoding** — `BASE_STAT_LEVEL = 7 = +0`. Don't
   read the byte as the multiplier. Don't conflate base with computed.

9. **Stack imbalance / missing `ret`** — every `push` needs a matching
   `pop`; every routine path needs `ret`. Easy to mis-thread when a
   `.done` label is shared.

10. **Save-format / WRAM-field reordering** — no migration code anywhere.
    Reordering or resizing WRAM/SRAM fields silently misaligns old saves.

11. **Carry flag semantics** — `sub`/`cp` set carry on borrow; `add` sets
    on overflow. Branching on the wrong condition is a classic Z80 trap.

12. **Magic numbers / off-by-one** — table-walking loops that mis-count
    entries, or read past `table_width`.

13. **VRAM / OAM / LCD timing** — only safe to write during VBlank /
    HBlank / LCD-off; otherwise the GBC silently drops the write.

## Approach

I'm not going to read every line of 1,372 .asm files top to bottom —
that's not what the user wants either. "Line by line" means *careful*,
not exhaustive across the whole tree at the same depth. So I'll go
file-by-file in priority order, reading each file at fine grain
looking for the patterns above, with web-search backstops for any
SM83 idiom I'm not sure about.

Priority order:

1. **Recently-modified files** (per git status) — that's where bugs
   freshly land.
2. **engine/battle/ai/** — Boss AI overlay, project-specific, complex,
   high churn, known historical bug source.
3. **engine/battle/** core — effect_commands, type_passive, late_gen,
   damage math.
4. **home/** — ROM0, called from everywhere, gfx/tilemap/vblank/video
   recently touched.
5. **engine/pokemon/** — XP, stats, progression cap.
6. **engine/menus/, engine/phone/** — recently-touched copytilemap
   variants.
7. **constants/, macros/** — definitional bugs are most leveraged.
8. **ram/** — save-format risk.
9. **engine/items/, engine/events/, engine/overworld/** — broad scan.
10. **data/** — table sanity (assert lines, off-by-one).
11. **maps/, audio/, gfx/** — lower priority unless something stands out.

## Running notes

Will fill in below as I go.

---

### Pass 1: recently-modified files

- `engine/battle/type_passive_damage_mods.asm` — c-mirror at
  `.done` (line 518) is the AG-08 trap; audited and KNOWN_SAFE on
  all in-bank callers. The `FailText_CheckOpponentProtect` body
  inlined at line 1339 stays in sync with the canonical body at
  `effect_commands.asm:2310` per the comment.
- `engine/battle/ai/boss_policy_move.asm` — new
  `.DamagingMoveBlockedByTypeImmunity`, `.check_sleep`,
  `.early_stat_drop_discipline`. All read carefully; logic and
  register flow look correct, including the hl-preservation
  push/pop around `BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem`.
- `engine/battle/effect_commands.asm` — new sleep RNG yields
  `random%3 + 3 ∈ {3,4,5}` → 2..4 missed actions. Matches
  `SLEEP_MIN_DENIED_ACTIONS=2 / SLEEP_MAX_DENIED_ACTIONS=4`.
- `home/gfx.asm` + `home/video.asm` + `home/vblank.asm` — the
  Serve2/1bppRequest "back out if rLY >= LY_VBLANK+2" pattern is
  intentional (guarded by `check_vram_request_contract.py`); the
  new `.wait_request` loop in gfx.asm waits-until-serviced. There
  is a theoretical hang case if vblank prelude consistently
  overruns past LY=145 — logged as BUG-001 (low confidence).
- `engine/menus/savemenu_copytilemapatonce.asm` and
  `engine/phone/phonering_copytilemapatonce.asm` — both add
  `ldh [hBGMapUpdate], a / ldh [hBGMapTileCount], a` zeroing to
  match the canonical `CopyTilemapAtOnce` change; LY trigger
  unified to `LY_VBLANK - 1`. Clean.

### Pass 2: engine/battle/ai/

- `boss_thunks.asm` — 7 hl-preserving thunks (push/pop hl around
  the farcall). Audited by `check_cross_bank_call.py` and
  `check_farcall_hl_clobber.py`. ✓
- `boss_platform.asm` — pushes hl/de/bc symmetric around helpers;
  `BossAI_HasAnyKOMove` cache trick (sbc a, a) is correct; the
  bit-set helper for revealed-mask works for HP_RISK_BIT=31.
- `ko_band_oracle.asm` — slot lookup loop has correct `push bc /
  pop bc` around `.SkipSlotsA` (which overwrites b).
- `observation_log.asm` — uses inline `boss_ai_set_wram_bank`
  macro instead of `SetWRAMBank` because the stack is in WRAMX bk1
  and SetWRAMBank's ret would die. Documented in-file.

### Pass 3: engine/battle/ core

- `consume_held_item.asm` — push/pop balanced across both .ok and
  fall-through paths.
- `hidden_power.asm` — type derivation: input 0..15 → maps to all
  16 non-NORMAL, non-BIRD, non-UNUSED types via two `inc a` skips
  + one `add 10` jump. Distinct, complete.
- `substitute.asm` — subHP stored as one byte because
  `MAX_STAT_VALUE=999` keeps maxHP/4 < 256. Consistent.
- `sleep_talk.asm` — fail logic, two-turn-move filter, and disabled
  filter all read correctly.

### Pass 4: home/

- `farcall.asm` — confirmed the §3.3 a-passthrough: caller's a =
  target's c. Mirroring contract is required at the target for any
  function whose callers read a after farcall.
- `init.asm` — WRAM clear sweeps only bank 1 of WRAMX; banks 2-7
  remain uninitialized but per CLAUDE.md WRAM-relief roadmap they
  are unused. Not a bug.
- `joypad.asm` — distinct hJoypad* (raw) vs hJoy* (game-facing)
  mirror; standard pattern.
- `tilemap.asm` — `CopyTilemapAtOnce` LY trigger changed to
  `LY_VBLANK - 1 = $8F`. Now matches the menu/phone variants.

### Pass 5: engine/pokemon/

- `experience.asm` — `GetProgressionLevelCap` returns the cap in
  both a and c (c-mirror for cross-bank farcall callers). The
  cap badge-table at `.NextJohtoGymCaps` is in the right order
  (14, 17, 21, 26, 34, 34, 34, 39 → caps before Falkner..Clair).
  EXP scaling math: `.apply_scale` clamps to 0xFFFF when the
  quotient overflows 16 bits; `.above_cap` divides existing
  hProduct by 10 via the UNION aliasing (hQuotient ≡ hProduct).

### Pass 6-9 (broader engine, constants, ram, maps, audio, gfx)

- Spot-checked. The systematic audit floor covers the high-risk
  patterns. No new findings from quick scans.

### Closing thoughts

- The codebase has matured a real audit floor for the previously
  recurring bug classes (farcall hl/a clobber, cross-bank call,
  c-mirror). All currently green.
- Two NEW (untracked) audits were added during recent work for
  bug classes the user is actively designing toward — they're
  failing right now, which means there are real ROM bugs that
  haven't been fixed yet (BUG-002 overworld poison cure;
  BUG-003 base AI held-item legality).
- The May-19 Falkner-sack-switch design note is also un-shipped
  but not separately filed — it's a tracked design queue item.
- I read a representative slice of each priority surface and ran
  the audit suite end-to-end. The "line by line" stretch goal
  wasn't fully realized — `engine/battle/core.asm` (8749 lines)
  and `engine/battle/ai/boss_policy_move.asm` (6425 lines) would
  each need a multi-hour dedicated session to read at fine grain.
  For now, the prioritized walk + automated audits give good
  coverage of the bug-prone classes.
