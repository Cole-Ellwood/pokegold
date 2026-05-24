# ROM line-read bug audit — 2026-05-23

**Auditor:** Claude (Opus 4.7, 1M context), invoked via `/pgoal` for a
read-only line-by-line walk of the actual cartridge source.

**Scope:** `engine/`, `home/`, `data/`, `macros/`, `ram/`, `constants/`,
`maps/`, `gfx/`, `audio/` — the ROM. Excludes `tools/`, `scripts/`,
`.claude/`, `audit/` (those are dev-side, not shipped in the ROM).

**Method:** prioritized walk — recently-modified files first, then
boss AI, then battle engine, then home bank, then the rest. Web search
used for SM83 / RGBDS idioms when uncertain. Findings catalogued with
the prior-audit ID format (`BUG-2026-05-23-NNN`).

**Status legend:**
- `OPEN` — bug believed real, not yet fixed in this branch.
- `OPEN_LOW_CONF` — pattern flagged, would need playtest or trace to
  confirm; recorded so the user can decide.
- `RESOLVED_IN_CURRENT_SOURCE` — flag in older code, but current
  source already fixes it.
- `NON_BUG` — looked suspicious but is correct on careful read; kept
  so future audits don't re-flag the same code.

**Cross-model review (Codex / GPT-5.5):** spot-checked against the
`claude/boss-ai-rom-expansion` branch tip the audit was written on.
Final verdicts:

| Finding | Codex verdict | Notes |
| --- | --- | --- |
| BUG-001 | NEEDS_MORE_INFO | Contract is fragile, but no reproduced hang. Codex: "instrument or reproduce a real late-VBlank starvation path before changing contract; do not add a timeout blindly." |
| BUG-002 | CONFIRMED | PyBoy audit fails: start HP 1 → got HP 0. P1 confirmed. |
| BUG-003 | CONFIRMED (narrowed) | Codex narrowing: `engine/battle/core.asm` later calls `EnforceEnemyHeldMoveRestrictions_Far`, so impact is bad AI scoring/selection, not illegal final execution. |
| BUG-004 | CONFIRMED | After re-check: `ClearLastMove` only clears user-side vars; doesn't block Mirror Move → Sketch trigger. |
| BUG-005 | CONFIRMED | Same Mirror Move → Mimic structure. |
| BUG-006 | CONFIRMED | Metronome / Mirror Move triggers proven. Codex correction: the Sleep-Talk-charging-move evidence path was wrong — `sleep_talk.asm:117-141` excludes two-turn moves explicitly. Dropped from the trigger list; Metronome / Mirror Move are still enough. |
| BUG-007 | CONFIRMED | Link-only P3. Release smoke covers the copy-bound, not the preamble-search bound. |

Codex also flagged two **NEEDS_MORE_INFO candidates** I missed; see
"Future-authoring guardrails" near the end of this doc.

Scratchpad (working notes): `journal/2026-05-23_rom_lineread_scratchpad.md`.

**Recommended user actions (in priority order):**

1. **Fix BUG-2026-05-23-002 (overworld poison cure at 1 HP).** This is
   the most playthrough-impactful finding — affects any poisoned mon
   walking on the overworld. Its audit is already written
   (`tools/audit/check_overworld_poison_cure.py`) and currently red;
   landing the fix in `engine/events/poisonstep.asm` will turn it
   green and let `check_release_smoke.py` adopt it.
2. **Decide on BUG-2026-05-23-003 (base AI held-item legality)** —
   either ship the `.ApplyHeldItemMoveLegality` block its audit demands
   in `engine/battle/ai/move.asm`, or mark the audit XFAIL while the
   design settles.
3. **Triage BUG-004..006 (vanilla unbounded move-search loops).**
   These are pre-existing pret/pokegold defects, but they're real and
   reachable in this hack's encounter set (wild Smeargle, wild Clefairy
   line, common Mimic-learners). A shared helper that returns "move not
   found → fail" would patch all five sites at once. Consider whether
   "fix this latent vanilla class" is worth the budget.
4. **BUG-001 (gfx wait_request hang risk) and BUG-007 (link-trade
   mail-preamble walk)** are low-priority documentation entries; no
   action needed unless behavior changes upstream.

---

## Summary

**Count by status** (post Codex cross-check; original audit status):

| Status | Count |
| --- | --- |
| `CONFIRMED` (CONFIRMED by both auditors) | 6 |
| `NEEDS_MORE_INFO` (BUG-001 only) | 1 |
| `RESOLVED_IN_CURRENT_SOURCE` | 0 |
| `NON_BUG` | 0 |

Of the 6 CONFIRMED: 2 are project-introduced gaps (BUG-002 poison cure,
BUG-003 base AI legality); 4 are vanilla Gen-2 inheritances reachable
in this hack's encounter set (BUG-004..007).

**Resolution status (updated 2026-05-24 during worktree cleanup):**

| Finding | Status as of 2026-05-24 | Resolved by |
| --- | --- | --- |
| BUG-2026-05-23-001 | `OPEN_LOW_CONF` (documentary; no audit fail) | — |
| BUG-2026-05-23-002 | `RESOLVED` | `3fc5f944` (engine: cure overworld poison at 1-HP floor instead of fainting) |
| BUG-2026-05-23-003 | `RESOLVED` | `c129c3b8` (engine: fix queued rom bug regressions) |
| BUG-2026-05-23-004 | `RESOLVED` | `c129c3b8` (sketch `.find_sketch` bounded by `NUM_MOVES`) |
| BUG-2026-05-23-005 | `RESOLVED` | `c129c3b8` (mimic `.find_mimic` bounded by `NUM_MOVES`) |
| BUG-2026-05-23-006 | `RESOLVED` | `c129c3b8` (disable / encore / spite bounded by `NUM_MOVES`) |
| BUG-2026-05-23-007 | `RESOLVED` | `c129c3b8` (link `.loop2` / `.loop3` bounded by `wLinkOTMailEnd - wLinkOTMail`) |

Both project-tracking audits (`check_overworld_poison_cure.py`,
`check_base_ai_mechanics_correctness.py`) now PASS. BUG-001 remains
`OPEN_LOW_CONF` as a design-journal entry; no audit script tracks it.

The original "Recommended user actions" list, audit-floor table, and
per-finding sections below preserve the audit-authoring-time view for
historical reference. Per-finding Status lines have been updated in
place to reflect resolution; "Resolution" sub-lines mark the change.

**Top-priority findings (in user-action order):**

1. **BUG-2026-05-23-002 — overworld poison takes mons from 1 HP → 0 HP.**
   P1 (game-correctness, player-visible). The new
   `tools/audit/check_overworld_poison_cure.py` (untracked) is failing
   against the built ROM. Fix lives in
   `engine/events/poisonstep.asm:59-99` (`DoPoisonStep.DamageMonIfPoisoned`).
   See finding for fix sketch.

2. **BUG-2026-05-23-003 — base (non-boss) AI lacks held-item move legality.**
   P2 (AI quality gap; sub-boss trainers inconsistent vs bosses). The
   new `tools/audit/check_base_ai_mechanics_correctness.py` (untracked)
   is failing. Fix needs a new `.ApplyHeldItemMoveLegality:` block in
   `engine/battle/ai/move.asm` and a call site in `.ApplyLayers:`.

3. **BUG-2026-05-23-004 — Mirror Move → Sketch on a non-Smeargle corrupts memory.**
   P2, vanilla Gen-2 inheritance. The `.find_sketch` loop in
   `engine/battle/move_effects/sketch.asm:54-64` is unbounded and only
   exits when `[hl] == SKETCH` ($A6). If a Mirror-Move user (Pidgeot,
   Fearow, etc.) mirrors a Smeargle's Sketch, the loop walks backward
   through WRAM and lands the resulting move/PP write at an unintended
   address. Real, reachable in this hack (Smeargle is in
   `data/wild/johto_grass.asm`). Documented as low confidence pending
   an actual emulator repro.

4. **BUG-2026-05-23-005 — same `.find_mimic` unbounded walk on
   Mirror Move → Mimic.** P2, vanilla inheritance, analogue of BUG-004.
   At least as reachable: Mimic users are common (Mr. Mime, Cubone,
   many others).

5. **BUG-2026-05-23-006 — same unbounded-search class in Disable,
   Encore, Spite when target's last move isn't in target's moveset.**
   P2, vanilla inheritance, much broader trigger than BUG-004/005:
   fires whenever the target's last move was via Metronome / Mirror
   Move / Sleep-Talk-charging-move (since those update LAST_COUNTER_MOVE
   to a move the target doesn't have). Wild Clefairy → Metronome →
   player Disable is a reachable Johto-route trigger.

6. **BUG-2026-05-23-007 — link-trade mail-preamble walk is unbounded.**
   P3 (link-play-only). The `.loop2` / `.loop3` mail-data parser in
   `engine/link/link.asm:328` walks `wLinkOTMail` looking for
   `SERIAL_MAIL_PREAMBLE_BYTE` with no buffer-length cap; a misbehaving
   link partner could push the parser into adjacent WRAM. Vanilla
   inheritance.

7. **BUG-2026-05-23-001 — Request2bpp/Request1bpp wait-loop hang risk.**
   LOW-CONF, future-proofing. The deliberate "wait until VBlank
   acknowledges" pattern can hang if VBlank prelude ever consistently
   overruns past LY=145. No reproducer; documenting for the design
   journal.

**Surface coverage map:**

| Surface | Coverage | Notes |
| --- | --- | --- |
| Recently-modified files (Pass 1) | Full read | All 12 M-listed files examined; diffs cross-checked against current source |
| `engine/battle/ai/` (Pass 2) | Partial | Read: `move.asm`, `boss_thunks.asm`, `boss_platform.asm:1-1000`, `boss_policy_switch.asm:1-130`, `ko_band_oracle.asm`, `observation_log.asm:1-100`, `switch.asm:1-220`, `items.asm:1-120`, sampled `boss_policy_move.asm` diff + key helpers. Not read: full 3227-line `scoring.asm` body (vanilla layered AI, low novelty), full 6425-line `boss_policy_move.asm`, items.asm:120-784 |
| `engine/battle/` core (Pass 3) | Sampled | Read: `type_passive_damage_mods.asm` (full), `effect_commands.asm` Sleep section + 2200-2370 (ApplyDamage + FailText), `late_gen_held_items.asm:1-260, 498-700`, `consume_held_item.asm`, `ditto_imposter.asm`, `hidden_power.asm`, move effects (`spikes.asm`, `substitute.asm`, `transform.asm`, `sleep_talk.asm`). Not read: full 8749-line `core.asm`, `effect_commands.asm` outside the sampled ranges, all other move effects |
| `home/` (Pass 4) | Partial | Read: `gfx.asm` diff + structure, `tilemap.asm` (full), `vblank.asm:1-200`, `video.asm:240-400`, `init.asm`, `joypad.asm:1-120`, `sram.asm`, `lcd.asm`, `farcall.asm`, `battle_vars.asm`. Not read: `map.asm`, `text.asm`, `menu.asm`, `audio.asm`, `serial.asm`, `decompress.asm`, `print_text.asm`, others |
| `engine/pokemon/` (Pass 5) | Sampled | Read: `experience.asm:1-355` (full), `mon_stats.asm:390-477`. Not read: `bills_pc.asm`, `breeding.asm`, `evolve.asm`, `mail*.asm`, `mon_menu.asm`, `move_mon.asm`, `party_menu.asm`, `stats_screen.asm` |
| Constants / RAM / macros (Pass 7) | Sampled | Read: `battle_constants.asm:1-100` + key bits, `type_constants.asm`, `move_effect_constants.asm` ordering, `macros/ram.asm:1-130`, `ram/hram.asm` math UNION, `ram/wram.asm` battle-relevant fields. Not read: full WRAM, full hardware.inc, full effect commands constants |
| `engine/menus, events, items` (Pass 6) | Light | `poisonstep.asm` (full, where bug-002 lives); `item_effects.asm:1-120` (table). Not read in depth |
| `data/` (Pass 8) | Spot-checked | `data/moves/moves.asm` looked up counter-class powers; `data/trainers/parties.asm` diff seen. Not read: full tables |
| `maps/`, `audio/`, `gfx/` (Pass 9) | Skipped | Low expected leverage; user can request a follow-up pass if desired |

**Audit-floor sanity (run during this walk):**

| Script | Result |
| --- | --- |
| `check_release_smoke.py` | PASS (with 2 doc-only date-anchored claim warnings, out of scope) |
| `check_farcall_hl_clobber.py` | PASS — known hl-input set: `ApplyLateGenDamageStatsItemMods_Far`, `SpeciesItemBoost_Far` |
| `check_farcall_a_clobber.py` | PASS — 16578 functions analyzed for a/c mirror safety |
| `check_typepassive_c_mirror.py` | PASS — 7 same-bank sites, 3 push/pop, 4 KNOWN_SAFE |
| `check_cross_bank_call.py` | PASS — no cross-bank plain `call` / `jp` outside HOME |
| `check_save_format_version.py` | PASS — matches SAVE_FORMAT_VERSION=2 |
| `check_navigation_floor.py` | PASS |
| `check_vram_request_contract.py` | PASS (intentional behavior; see BUG-001) |
| `check_battle_calc.py` | PASS |
| `check_damage_ai_report.py` | PASS |
| `check_move_score_probe.py` | PASS |
| `check_base_ai_mechanics_correctness.py` | **PASS** (resolved by `c129c3b8`) — was **FAIL** at audit-authoring time → BUG-003 |
| `check_overworld_poison_cure.py` | **PASS** (resolved by `3fc5f944`) — was **FAIL** at audit-authoring time → BUG-002 |

**Negative results worth recording (not bugs, but checked):**

- HRAM addressing class — no `ld [$FFxx]` / `ld a, [rXX]` violations
  found across 1877 .asm files. The codebase consistently uses `ldh`
  for IO/HRAM. ✓
- Type passive `c`-mirror trap (AG-08 class) — every call site has
  the push/pop bc protection or is in the audit's `KNOWN_SAFE` set.
  No new in-bank caller has slipped through. ✓
- The 3-layer Spikes counter math is sound; `cp 3 :: jr nc, .failed`
  correctly caps at 3. ✓
- The progression cap (`GetProgressionLevelCap`) c-mirror for farcall
  is in place at every `ret` site. ✓
- Hidden Power type derivation maps all 16 input values to distinct
  types in a fully-defined range; no skipped or duplicate type. ✓
- Substitute's "we only store the low byte of subHP" relies on
  `MAX_STAT_VALUE = 999` keeping `maxHP/4 < 256`. Consistent at the
  game's stat cap. ✓
- The boss-AI sleep-clause check in `.check_sleep` (new) reads
  `wEnemySleepClauseSlot` after `.PrimaryStatusBlocked` returns
  no-carry, and `jp .status_fail` correctly translates clause-violation
  into "would-fail-publicly" — flag flow is sound. ✓
- The new boss-AI early-stat-drop discipline indexes
  `wPlayerStatLevels` (ATK..EVA, 7 bytes) using the
  `EFFECT_ATTACK_DOWN..EFFECT_EVASION_DOWN` enum offset; the orderings
  match. ✓
- Sleep counter math: random%3 + 3 ∈ {3,4,5}; with the project's
  "counter decrements on slept mon's action; waking action not denied"
  semantic, this yields 2..4 missed actions, matching
  `SLEEP_MIN_DENIED_ACTIONS=2`, `SLEEP_MAX_DENIED_ACTIONS=4`. ✓
- The duplicated `FailText_CheckOpponentProtect` body (canonical in
  `effect_commands.asm:2310`, inlined in
  `type_passive_damage_mods.asm:1339`) is byte-equivalent in behavior;
  the inlined version uses `call` instead of `jp` only because more
  code follows. Worth keeping the cross-reference comments in sync if
  either is touched. ✓

**Provenance of the unbounded-loop class (BUG-004 through BUG-007):**

Web-fetched [pret/pokegold/engine/battle/move_effects/mirror_move.asm](https://github.com/pret/pokegold/blob/master/engine/battle/move_effects/mirror_move.asm)
and confirmed the same `CheckUserMove :: jr nz, .use` shape is in
vanilla pret/pokegold. The unbounded `.find_sketch / .find_mimic /
.loop / .got_move` patterns in `engine/battle/move_effects/{sketch,
mimic, disable, encore, spite}.asm` are all vanilla Gen-2 code that
this hack has inherited. They are real defects but not introduced by
this project's work.

**Tracking notes (not bugs, design WIP from session journal):**

- The May-19 Falkner-sack-switch fix (option-3 "veto switch into
  wincon when current is doomed non-wincon") in
  `journal/2026-05-19_falkner-sack-switch-scratchpad.md` has NOT
  landed. There is no `BossAI_VetoSwitchTargetIsWincon` (or similar)
  helper in `engine/battle/ai/boss_policy_switch.asm`. Player-visible
  behavior in early-tier boss fights (e.g., Falkner) may still allow
  the doomed-non-ace-into-wincon sack-switch the journal describes.
  Not flagged as a finding because it's already on the user's design
  queue — calling it out here so the next session can decide whether
  to ship.

---

## Findings

(Findings appended below as they are confirmed. Each takes the form:
`### BUG-2026-05-23-NNN — Px — short title` with `Status:`, `Surface:`,
`Evidence:`, optional `Fix sketch:`, and `Confidence:`.)

### BUG-2026-05-23-001 — Px-LOW — `Request2bpp` / `Request1bpp` wait-loop can hang if VBlank is consistently late

Status: `OPEN_LOW_CONF`

Surface: `home/gfx.asm:115-141, 165-186` (`Request2bpp::` /
`Request1bpp::` and their new `.wait_request` subroutines), paired with
`home/video.asm:242-326` (`Serve1bppRequest::` / `Serve2bppRequest::`
"back out if too far into VBlank" early-return).

Evidence:

The new pattern is:

```
; gfx.asm Request2bpp body (per cycle)
ld [wRequested2bppSize], a
call .wait_request          ; was: call DelayFrame
...
.wait_request
    call DelayFrame
    ld a, [wRequested2bppSize]
    and a
    jr nz, .wait_request    ; loop until VBlank handler clears size
    ret
```

`Serve2bppRequest` (called from `VBlank_Normal` in
`home/vblank.asm:107`) now early-returns when
`rLY < LY_VBLANK || rLY >= LY_VBLANK + 2` — only the first 2 lines of
VBlank (LY=144 and 145) actually service the request. If
`VBlank_Normal`'s earlier work (UpdateBGMapBuffer / UpdatePalsIfCGB /
UpdateBGMap) consistently overruns past LY=145, `Serve2bppRequest`
never decrements `wRequested2bppSize`, and `.wait_request` spins
forever.

In practice this should be benign — UpdateBGMapBuffer and
UpdatePalsIfCGB return-carry-to-skip the rest of the chain, so the
heavy path is exclusive. But if a future change adds a heavy
unconditional VBlank-prelude that pushes start-of-Serve2bpp past LY=145
every frame, this loop becomes a hang and the caller is no longer
making progress. The old behavior degraded gracefully (single
DelayFrame, then continue regardless of whether the request landed).

`VBlank_Cutscene` is safe — it calls the new `Serve2bppRequest_VBlank`
entry point which bypasses the LY gate.

Fix sketch (sketch only — READ-ONLY mode):

Add a frame-count bound to `.wait_request`. Something like:

```
.wait_request
    ld a, 30      ; ~half a second at 60 fps
    ld [.wait_request_budget], a   ; or use a HRAM byte
.wait_request_loop
    call DelayFrame
    ld a, [wRequested2bppSize]
    and a
    ret z
    ld a, [.wait_request_budget]
    dec a
    ld [.wait_request_budget], a
    jr nz, .wait_request_loop
    ; bail out — accept that the request didn't fully land this time
    xor a
    ld [wRequested2bppSize], a
    ret
```

Less elegant than the current code, but it eliminates the hang case
entirely. Alternative: keep the old single-DelayFrame and accept the
risk that some requests aren't fully serviced before the caller
proceeds.

Confidence: low. I have not reproduced an actual hang — this is
pattern-spotting against a known failure mode. The current chain
probably doesn't hit it. The pattern itself is INTENTIONAL and is
guarded by `tools/audit/check_vram_request_contract.py` (in the
release-smoke floor), which specifically requires this
wait-until-serviced shape because "a single DelayFrame is not enough,
because a late VBlank can intentionally skip the copy." So the design
trade-off is deliberate: wait forever ≫ silently drop the request. The
finding stands only as a future-proofing note — if VBlank prelude work
ever grows past the 2-line budget consistently, the loop becomes a
hang and the existing audit will not catch the regression.

**Codex verdict:** NEEDS_MORE_INFO. "The audit proves the contract is
fragile, not that current ROM flow hangs. `home/video.asm` has guarded
normal services and an explicit `Serve2bppRequest_VBlank` path."
Action gate before changing the contract: instrument or reproduce a
real late-VBlank starvation path. Don't add a blind timeout.

### BUG-2026-05-23-002 — P1 — overworld poison takes mons from 1 HP → 0 HP (no modern cure-at-1 boundary)

Status: `RESOLVED` (committed `3fc5f944` — `engine: cure overworld poison at 1-HP floor instead of fainting`)

Resolution (added 2026-05-24 cleanup): `tools/audit/check_overworld_poison_cure.py` now PASSes; original Status was `OPEN` at audit-authoring time.

Surface: `engine/events/poisonstep.asm:59-99` (`DoPoisonStep.DamageMonIfPoisoned`).

Evidence:

The current source applies the classic Gen-2 overworld-poison rule:
"decrement HP by 1 on every step tile; if HP hits 0, faint the mon."

```
.DamageMonIfPoisoned:
    ; ... read status, return if not poisoned
    ; ... read HP into bc, return if already 0
    dec bc
    ld [hl], c
    dec hl
    ld [hl], b
    ld a, b
    or c
    jr nz, .not_fainted
    ; HP is 0 → reset status, return %10 (fainted)
    ...
```

With `start_hp = 1`, this branches into the faint path: HP becomes
0, status is cleared, return flag = %10. The new untracked audit
`tools/audit/check_overworld_poison_cure.py` (in `tools/audit/`,
self-runnable via PyBoy against `pokegold.gbc`) is FAILING with:

```
ERROR: start HP 1: expected HP 1, got 0
```

The audit's expected semantics (per its three cases at lines 127–129):

- start HP 1 → HP 1, status 0 (cured, no damage, no faint)
- start HP 2 → HP 1, status 0 (one tick, then cured at the new 1-HP boundary)
- start HP 3 → HP 2, status preserved (normal tick)

This matches the modern "overworld poison stops at 1 HP and cures"
semantic, which is the design intent for this hack — but the source
hasn't been updated.

Player-visible consequence: a poisoned mon stepping with 1 HP faints
silently and triggers the post-faint script + happiness drop instead
of curing harmlessly. This is unforgiving in the early game where 1-HP
escape from a near-KO is common.

Fix sketch (sketch only — READ-ONLY mode):

After reading HP into bc and confirming not-already-0, insert a
"would-this-be-the-last-HP" check:

```
; ... read HP, return if 0
ld a, b
or c
ret z

; cure-and-stop if HP is already 1
ld a, b
or a
jr nz, .has_more_than_1
ld a, c
cp 1
jr nz, .has_more_than_1
; HP is exactly 1 — cure status, no damage, return %01
ld a, MON_STATUS
call GetPartyParamLocation
ld [hl], 0
ld c, %01
scf
ret

.has_more_than_1
; existing dec bc / store / .not_fainted path
```

Note that case 2 (start HP 2 → expected HP 1 + cured) needs the same
treatment AFTER the dec: if post-dec HP is exactly 1, also cure. So
the fix may want to move the cure-at-1 check to AFTER the decrement
and consolidate.

Confidence: high. The audit script is unambiguous about the expected
semantic; the source unambiguously fails it; PyBoy is the source of
truth and reports HP=0 from the real running ROM. This is a real,
playthrough-affecting bug.

**Codex verdict:** CONFIRMED. "PyBoy audit fails: start HP 1 expected
HP 1, got 0. This is a behavior regression against the intended P1 floor."

### BUG-2026-05-23-003 — P2 — base (non-boss) AI scoring lacks held-item move-legality gate

Status: `RESOLVED` (committed `c129c3b8` — `engine: fix queued rom bug regressions`)

Resolution (added 2026-05-24 cleanup): `tools/audit/check_base_ai_mechanics_correctness.py` now PASSes; original Status was `OPEN` at audit-authoring time.

Surface: `engine/battle/ai/move.asm:65-117` (`AIChooseMove.ApplyLayers`)
and the missing `.ApplyHeldItemMoveLegality:` block expected by the
audit at `engine/battle/ai/move.asm` adjacent to `AIScoringPointers:`.

Evidence:

The new untracked audit `tools/audit/check_base_ai_mechanics_correctness.py`
requires (lines 52–74):

1. The `.ApplyLayers:` body in `AIChooseMove` must `call
   .ApplyHeldItemMoveLegality` BEFORE the boss-tier branch (`ld a,
   [wBossAITier]`).
2. The `.ApplyHeldItemMoveLegality:` block must read `wEnemyMonItem`,
   `callfar GetItemHeldEffect`, and reference `HELD_ASSAULT_VEST`,
   `IsMoveBlockedByAssaultVestFromE_Far`,
   `IsChoiceHeldEffectFromE_Far`, `wEnemyChoiceLockedMove`, and
   `ld [hl], 80` (score-out unusable moves).

Reading the current `move.asm` (no `.ApplyHeldItemMoveLegality:` label
anywhere), this contract is not met. The audit fails with:

```
ERROR: base move scoring must run held-item legality before tier
dispatch missing `call .ApplyHeldItemMoveLegality`
```

Player-visible consequence: regular trainers (non-boss AI tier) can
still pick moves that are mechanically illegal for the holder of an
Assault Vest (a status move on an AV holder) or that fail the
Choice-locked check. The boss AI overlay handles this via
`BossAI_*` legality gates; the base AI does not. So sub-boss trainers
behave inconsistently relative to boss trainers.

This is less severe than the poison-cure bug (it affects AI quality,
not save/health state), but it's a real correctness gap.

Fix sketch (sketch only — READ-ONLY mode):

Add an `.ApplyHeldItemMoveLegality:` block before `AIScoringPointers:`
in `move.asm`. The block walks all 4 enemy moves, checks each against
the enemy's held effect (via `callfar GetItemHeldEffect`), and writes
80 into the corresponding score slot if the move is illegal under
Assault Vest / Choice. Then `call .ApplyHeldItemMoveLegality` from
`.ApplyLayers` before the `[wBossAITier]` check.

Confidence: high — the audit specifies the contract; the source
unambiguously lacks it.

**Codex verdict:** CONFIRMED with **scope narrowing**. The base AI's
chosen move is mechanically constrained later in
`engine/battle/core.asm` by `EnforceEnemyHeldMoveRestrictions_Far`, so
the actual *execution* is legal — the impact is bad AI scoring /
selection quality, not illegal final moves. Still worth fixing for AI
quality parity with the boss overlay, but downgrade the player-visible
severity from "AV holder uses status move" (impossible) to "AV holder
SCORES status moves equally and picks them more often than it should
once the runtime restriction filters them out." Player-visible signal:
sub-boss trainers waste turns on moves that get last-minute blocked.

### BUG-2026-05-23-004 — P2 — Mirror Move can copy Sketch onto a non-Smeargle, causing memory corruption via the `.find_sketch` unbounded backward walk

Status: `RESOLVED` (committed `c129c3b8` — `engine: fix queued rom bug regressions`; `.find_sketch` walk now bounded by `NUM_MOVES` counter)

Resolution (added 2026-05-24 cleanup): originally `OPEN_LOW_CONF` (vanilla Gen-2 inheritance — present in pret/pokegold too, but real in this hack and reproducible in-game).

Surface: [engine/battle/move_effects/sketch.asm:54-64](engine/battle/move_effects/sketch.asm) (`.find_sketch` loop in `BattleCommand_Sketch`) interacting with [engine/battle/move_effects/mirror_move.asm:11-24](engine/battle/move_effects/mirror_move.asm) (`BattleCommand_MirrorMove`'s `.use` path).

Evidence:

`BattleCommand_MirrorMove`:

```
ld a, BATTLE_VARS_LAST_COUNTER_MOVE_OPP
call GetBattleVar          ; a = opponent's last counter move
and a
jr z, .failed
call CheckUserMove         ; z if user has the move, nz if not
jr nz, .use                ; → use the mirrored move only if user doesn't have it
.failed
    ...
.use
    ld a, b                ; b = opp's last move
    ld [hl], a             ; store at current-move var
    ...
    jp ResetTurn           ; re-dispatch with the new move
```

So if the opponent's last move was Sketch and the user does NOT have Sketch in their moveset, Mirror Move stores Sketch as the user's current move and re-dispatches. The dispatch eventually calls `BattleCommand_Sketch`:

```
.does_user_already_know_move
    ld a, [hli]
    cp b
    jr z, .fail
    dec c
    jr nz, .does_user_already_know_move
; Find Sketch in the user's moveset.
    dec hl
    ld c, NUM_MOVES
.find_sketch
    dec c
    ld a, [hld]
    cp SKETCH
    jr nz, .find_sketch
    inc hl
```

The `.find_sketch` loop only exits when `[hld] == SKETCH` (move id 166 = `$A6`). It does NOT check `c` for termination — `dec c` decrements but the conditional is solely on the `cp SKETCH` result. Once `c` wraps from 0 to 255, the loop continues walking `hl` backwards through memory until it finds a `$A6` byte somewhere.

Trigger conditions:

1. Player has a Pokemon with `MIRROR_MOVE` (Pidgeot, Fearow, Articuno, Zapdos, Moltres, Aerodactyl, Mr. Mime — all in this hack).
2. Player's Mirror-Move-knowing Pokemon does NOT also know Sketch (almost always true outside Smeargle).
3. Opponent is Smeargle (encounterable in `data/wild/johto_grass.asm:395-411`).
4. Smeargle uses Sketch (its default move), then the player uses Mirror Move.

Memory effect:

After walking past `wBattleMonMoves[0]`, the loop reads `wBattleMonItem`, `wBattleMonSpecies`, the nicknames, and eventually `wPlayerMoveStruct` fields. The first byte equal to `$A6 = SKETCH = LOVE_BALL` halts the loop and triggers the "store sketched move at this slot" code, which:

- writes the move id at the matched address (so e.g. if the player was holding a `LOVE_BALL` ($A6), the `LOVE_BALL` byte is rewritten as the sketched move id — no-op-equivalent), then
- writes the move's PP to `address + (wBattleMonPP - wBattleMonMoves) = address + 6` — that's six bytes past the matched byte. Depending on where the match landed, this corrupts `wBattleMonDVs` / `wBattleMonHappiness` / move struct bytes.

The fail-mode is silent corruption, not a hang — the loop terminates because some byte in WRAM eventually matches `$A6`, but the post-loop store lands at the wrong address.

This is a vanilla Gen-2 inheritance (pret/pokegold has the same `.find_sketch` shape). It's never been triggered in a normal vanilla playthrough because (a) Smeargle is wild-encounter-only in vanilla Gen 2 and (b) Mirror-Move-users rarely face Smeargle in the wild. In this hack the wild Smeargle encounters in `johto_grass.asm` mean the bug is reachable.

Fix sketch (sketch only — READ-ONLY mode):

The same `.find_X` loop pattern is in [engine/battle/move_effects/mimic.asm:27-30](engine/battle/move_effects/mimic.asm) (`.find_mimic` looking for MIMIC = `$66 = BLACKGLASSES`). Same fix shape works:

```
.find_sketch
    dec c
    jr z, .fail            ; bound the loop at 4 iterations
    ld a, [hld]
    cp SKETCH
    jr nz, .find_sketch
    inc hl
```

OR — gate the `BattleCommand_Sketch` entry on "user actually has Sketch in moveset" by reusing the `CheckUserMove` helper. If the user doesn't have Sketch when `BattleCommand_Sketch` runs, fail the move (consistent with the implicit assumption the original code makes).

OR — block Mirror Move from copying Sketch / Mimic specifically. A small allow-list in `BattleCommand_MirrorMove` that fails for `SKETCH` and `MIMIC` (similar to how `MetronomeExcepts` blocks them for Metronome) preempts the dispatch entirely.

Confidence: high (promoted from medium-high after Codex cross-check).

**Codex verdict:** CONFIRMED. Quote: "Mirror Move can dispatch Sketch
when the user does not have Sketch, then Sketch reads opponent last
counter move via `_OPP` and unboundedly scans the user moveset for
`SKETCH`. `ClearLastMove` does not clear the value Sketch reads. No
intervening line between Mirror Move `ResetTurn` and Sketch's read
clears `wLastEnemyCounterMove`."

### BUG-2026-05-23-005 — P2 — same `.find_mimic` unbounded-walk bug as BUG-004 (Mirror Move → Mimic onto a non-Mimic-knowing user)

Status: `RESOLVED` (committed `c129c3b8` — `engine: fix queued rom bug regressions`; `.find_mimic` walk now bounded by `NUM_MOVES` counter)

Resolution (added 2026-05-24 cleanup): originally `OPEN_LOW_CONF` (vanilla Gen-2 inheritance).

Surface: [engine/battle/move_effects/mimic.asm:27-31](engine/battle/move_effects/mimic.asm) (`.find_mimic` in `BattleCommand_Mimic`).

Evidence: exact analogue of BUG-004. The `.find_mimic` loop:

```
.find_mimic
    ld a, [hld]
    cp MIMIC
    jr nz, .find_mimic
    inc hl
```

— has no iteration bound. If the user doesn't have MIMIC in their moveset but BattleCommand_Mimic is called (via Mirror Move → Mimic), the walk goes backwards through WRAM until it hits a byte equal to MIMIC's move id ($66 = BLACKGLASSES as an item).

Trigger: opponent uses Mimic, player uses Mirror Move with a non-Mimic-knowing Mirror-Move user. Mimic is a common learnable move (Mr. Mime, Cubone, many others), so this is at least as reachable as the Sketch case.

Fix sketch: same shape as BUG-004 — bound the loop on `c`, or gate the entry on "user has Mimic", or blacklist Mimic in Mirror Move.

Confidence: high (promoted from medium-high after Codex cross-check).

**Codex verdict:** CONFIRMED. Same structure as BUG-004: Mirror Move
dispatches Mimic onto a non-Mimic user, Mimic reads `_OPP` last
counter move, unboundedly scans for `MIMIC` ($66 = BLACKGLASSES as an
item).

### BUG-2026-05-23-006 — P2 — same unbounded-search bug class in Disable, Encore, Spite (target's last counter move not in target's moveset)

Status: `RESOLVED` (committed `c129c3b8` — `engine: fix queued rom bug regressions`; Disable / Encore / Spite move-search loops now bounded by `NUM_MOVES`)

Resolution (added 2026-05-24 cleanup): originally `OPEN_LOW_CONF` (vanilla Gen-2 inheritance).

Surface:
- [engine/battle/move_effects/disable.asm:26-32](engine/battle/move_effects/disable.asm) (`.loop` in `BattleCommand_Disable`)
- [engine/battle/move_effects/encore.asm:22-25](engine/battle/move_effects/encore.asm) (`.got_move` in `BattleCommand_Encore`)
- [engine/battle/move_effects/spite.asm:19-23](engine/battle/move_effects/spite.asm) (`.loop` in `BattleCommand_Spite`)

Evidence:

All three follow the same pattern — walk the opponent's moveset for a move id taken from `BATTLE_VARS_LAST_MOVE_OPP` / `BATTLE_VARS_LAST_COUNTER_MOVE_OPP`, with no iteration bound on the counter:

```
; Disable.asm
ld b, a
ld c, $ff
.loop
    inc c
    ld a, [hli]
    cp b
    jr nz, .loop      ; no termination check on c
```

```
; Encore.asm
ld b, a
.got_move
    ld a, [hli]
    cp b
    jr nz, .got_move  ; no termination at all (no counter)
```

```
; Spite.asm
ld b, a
ld c, -1
.loop
    inc c
    ld a, [hli]
    cp b
    jr nz, .loop
```

After the (eventual) match, each uses `c` as an offset into `wXxxMonPP` to either zero PP, set Encore count, or deplete PP. If `c` has wrapped one or more times during the walk through 64 KiB of address space, that offset lands at an arbitrary WRAM address.

Trigger conditions — much broader than BUG-004/005:

The target's last move only needs to be NOT IN the target's moveset. This happens whenever the target's last successful action was one of:

- **Metronome** (`engine/battle/move_effects/metronome.asm`) — picks a random move and re-dispatches; the new move's `usedmovetext` updates LAST_COUNTER_MOVE to the random move id, which is almost never in the user's actual moveset. Wild Clefairy / Wigglytuff / Igglybuff and trainers' Clefable/Wigglytuff with Metronome are common Johto encounters.
- **Mirror Move** — copies the opponent's move; updates LAST_COUNTER_MOVE to the copied move (almost never in the mirror-user's own moveset).
- **Sleep Talk** with a charging move (Fly/Dig/Razor Wind/Skull Bash/Solar Beam/Sky Attack/Bide) — the original Sleep Talk is in the moveset, but `BATTLE_VARS_LAST_COUNTER_MOVE_OPP` ends up reflecting whichever sub-move the dispatch ran (per UsedMoveText). Less likely but reachable.

Concretely: player encounters a wild Clefairy that uses Metronome → Clefairy's `wLastEnemyCounterMove` becomes whatever random move it rolled. Player uses Disable on Clefairy → Disable searches Clefairy's moveset for that random move → unbounded walk and arbitrary-WRAM PP corruption.

Same setup for Encore / Spite. Encore additionally has no bound counter at all (not even an inc c), but the WRAM corruption pattern matches.

Fix sketch (sketch only — READ-ONLY mode):

For each of the three (and the parallel Sketch / Mimic in BUG-004/005), wrap the search loop with a counter check:

```
; Disable example
ld b, a
ld c, NUM_MOVES        ; bound = 4, not $ff
.loop
    ld a, [hli]
    cp b
    jr z, .found
    dec c
    jr nz, .loop
    jp .failed         ; move not in moveset → fail the move
.found
    ld a, NUM_MOVES
    sub c              ; recover slot index 0..3
    ld c, a
    ; continue with existing PP-index logic
```

Alternatively (and simpler): early-return failure if `CheckUserMove` reports the target doesn't actually know the move. The same helper used by `BattleCommand_MirrorMove` would work — just inverted to check the opponent's moveset.

The cleanest patch is probably a shared `FindMoveInOppMoveset` helper that returns `(found?, slot_index)` and is called from all 5 sites.

This is the most-pervasive instance of the unbounded-search-loop bug class — 5 move handlers all assume the target move is in the moveset.

Confidence: high (promoted from medium-high after Codex cross-check).

**Codex verdict:** CONFIRMED. Metronome / Mirror Move triggers proven.
**Codex correction:** the "Sleep Talk with a charging move" trigger
listed above is WRONG — `engine/battle/move_effects/sleep_talk.asm:117-141`
explicitly excludes two-turn moves (`EFFECT_SKULL_BASH`, `EFFECT_RAZOR_WIND`,
`EFFECT_SKY_ATTACK`, `EFFECT_SOLARBEAM`, `EFFECT_FLY`, `EFFECT_BIDE`).
Drop that trigger from the evidence list. Metronome and Mirror Move
remain valid.

### BUG-2026-05-23-007 — P3 — link-trade mail-preamble search loop in `link.asm` is unbounded

Status: `RESOLVED` (committed `c129c3b8` — `engine: fix queued rom bug regressions`; `.loop2` / `.loop3` now bounded by `wLinkOTMailEnd - wLinkOTMail` length cap)

Resolution (added 2026-05-24 cleanup): originally `OPEN_LOW_CONF` (vanilla Gen-2 inheritance; link play required to trigger).

Surface: [engine/link/link.asm:328-339](engine/link/link.asm) (`.loop2` / `.loop3` after `wLinkOTMail`).

Evidence:

```
ld hl, wLinkOTMail
.loop2
    ld a, [hli]
    cp SERIAL_MAIL_PREAMBLE_BYTE
    jr nz, .loop2
.loop3
    ld a, [hli]
    cp SERIAL_NO_DATA_BYTE
    jr z, .loop3
    cp SERIAL_MAIL_PREAMBLE_BYTE
    jr z, .loop3
    dec hl
```

`.loop2` walks `wLinkOTMail` forward looking for `SERIAL_MAIL_PREAMBLE_BYTE` with no terminator and no length cap. If the link partner's transmitted mail data omits the preamble byte (corrupted link, modded partner ROM, hardware desync, or a malicious actor), `.loop2` reads off the end of `wLinkOTMail` into adjacent WRAM until it accidentally hits a `SERIAL_MAIL_PREAMBLE_BYTE` byte elsewhere in memory. Then `.loop3` is similarly unbounded.

Same vanilla-inheritance shape; not a new issue.

Trigger: link-trade with a misbehaving partner. Not reachable in solo play.

Fix sketch: bound `.loop2` and `.loop3` by the buffer length (`wLinkOTMailEnd - wLinkOTMail` bytes). If the preamble isn't found, abort the trade rather than parse garbage.

Confidence: low-to-medium. Real code defect but very narrow trigger (need a co-operating misbehaving link partner). Including for completeness; this is the link-cable analogue of the BUG-004..006 class.

**Codex verdict:** CONFIRMED. "Link-only P3 is fair. Release smoke
covers the copy bound, not this sentinel-search bound."

---

## Future-authoring guardrails (NEEDS_MORE_INFO candidates from Codex)

These are unbounded-search patterns Codex spotted that are not
currently reachable in shipped flow, but are the same class as
BUG-004..007 and would become real bugs if the surrounding gating
ever changes:

- **`engine/link/time_capsule_2.asm:11`** — `ConvertMon_2to1` has an
  unbounded species-table walk. Normal Time Capsule flow gates
  non-Gen1 species at `engine/link/link.asm:1970`, so the walk
  doesn't fire in practice. Becomes a real bug if a future change
  relaxes the species gate or a corrupt link partner bypasses it.
- **`engine/battle/effect_commands.asm:5196` and `effect_commands.asm:6585`**
  — battle-script command scans that are unbounded by structure but
  bounded in practice by the current move-script data. Becomes a real
  bug if any future move-effect script omits the expected terminator
  command.

Both are "future-authoring guardrail" entries, not action items.
Filed so the next audit doesn't re-discover them and waste a cycle.

<!-- End of findings. -->





