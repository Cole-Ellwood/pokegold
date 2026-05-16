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
- `engine/battle/core.asm` (lines 1-100 + spot reads around line 2050, 2400, 2870) — lens: unbounded loops, battle-action OOB. findings: 1 (Finding 6 — DoBattle .loop unbounded for fully-fainted OT). Player-side has explicit `CheckPlayerPartyForFitMon → jp z, LostBattle` guard; OT-side does not.
- `engine/menus/save.asm:220-540` — lens: save-corruption, partial-write windows. findings: 0 confirmed; the dual-save / Validate-then-Save-then-Checksum sequence is the standard dirty-bit pattern, correct as far as I can verify without runtime tests.
- `engine/pokemon/breeding.asm` (lines 1-150) — lens: gen-2-breeding-glitches (egg-DV inheritance, daycare gender). findings: 0; the compatibility logic at lines 1-103 reads cleanly and the data sources (`wBreedMon1DVs`, `wBreedMon2DVs`) are bounded by GetGender's CGB-safe path.
- `audio/engine.asm:1-250` + `1340-1420` — lens: audio-channel-OOB, music-command-dispatch. findings: 0 (`UpdateChannels` uses `maskbits NUM_CHANNELS`; `ParseMusicCommand` is gated by `cp FIRST_MUSIC_CMD; jr c, .readnote` at line 1149 and the command table is `assert_table_length $100 - FIRST_MUSIC_CMD` covering all command-range bytes).
- `engine/items/items.asm` (`_ReceiveItem`/`_TossItem`/`_CheckItem` dispatchers + `CheckItemPocket`) — lens: jump-table OOB on item pocket. findings: 0 confirmed (item-attribute table has only pocket values 1-4 verified by reading `data/items/attributes.asm:1-50`; latent footgun for future data errors noted).
- `engine/items/item_effects.asm:1-12` (deeper re-read, this iter) — lens: jump-table OOB on wCurItem. findings: 1 (Finding 7 — _DoItemEffect unbounded on wCurItem).
- `data/items/attributes.asm` (preamble + first 50 entries) — lens: data-integrity, pocket-value validation. findings: 0 (item_attribute macro doesn't validate pocket value range; ALL audited entries have pocket ∈ {ITEM, KEY_ITEM, BALL, TM_HM}).
- `engine/pokemon/experience.asm:1-120` — lens: div-by-zero in EXP formula, level-cap loop bound. findings: 0 (growth rate denominators all non-zero per data/growth_rates.asm; CalcLevel iteration bounded by `cp LOW(MAX_LEVEL + 1)`).
- `constants/map_setup_constants.asm` — lens: enum value validity. findings: 0 (constants $f1-$fb cover valid MapSetupScripts indices 1-11 after low-nibble mask; Finding 2 covers the misuse if hMapEntryMethod is corrupted).
- `constants/item_constants.asm:180-200` — lens: NUM_ITEMS bound. findings: 0 (NUM_ITEMS = 190, with item-effect table covering 187 of these; remaining 3 are mail items that don't reach the use-item dispatcher in normal play — Finding 7 covers the data-corruption case).
- `constants/item_data_constants.asm` (pocket enum values) — lens: dispatcher index validity. findings: 0 (data values 1-4 match the 4-entry dispatcher tables).
- `engine/link/time_capsule.asm` — lens: gen-1-trade-validation, OOB-read on incoming species. findings: 0 (ValidateOTTrademon checks species match, level <= MAX_LEVEL, type integrity; rejects mismatches via `.abnormal` with carry-set).
- `engine/link/time_capsule_2.asm` + `engine/link/init_list.asm` + `engine/link/place_waiting_text.asm` — lens: link-state-machine, buffer sizes. findings: 0 (small files; standard list-init helpers, no unguarded OOB).
- `engine/events/pokecenter_pc.asm` (lines 1-120) — lens: PCN-box-glitch, jump-table-OOB. findings: 0 (.Jumptable is 5 entries with menu-bounded indices; MenuJumptable helper inherently bounds via menu data).
- `engine/pokemon/bills_pc.asm` (lines 1-120 + jumptable helper at 2134) — lens: PC-box-corruption, jumptable OOB. findings: 0 in the part read; wJumptableIndex stays in 0..4 range across the deposit flow.
- `engine/battle/effect_commands.asm` (lines 1-100, DoMove move-effect dispatch) — lens: move-effect-table OOB. findings: 0 (MoveEffectsPointers has `assert_table_length NUM_MOVE_EFFECTS`; effect bytes come from compile-time move data).
- `engine/battle/ai/boss_platform.asm` (lines 1-200) — lens: WRAMX-budget overflow, computed-jump on corrupt state, bit-shift overflow. findings: 0 (BossAI_RecordPlayerSpecies caps at PARTY_LENGTH; counters saturate at $ff; BossAI_SeenPlayerSpeciesBitFromC bit-shift bounded by PARTY_LENGTH=6 → max bit = $20).
- `engine/overworld/scripting.asm` (Script_giveitem at 1607, Script_givepoke at 1807, Script_warp at 1945) — lens: script-data-validation, save-corruption-via-script. findings: 0 confirmed; deferred observation: these script commands don't validate item/species/map IDs before writing to wCurItem/wCurPartySpecies/wMapGroup. Authored scripts use valid macros, but a typo-bug in a script would propagate corrupt IDs to bag/party and could feed Finding 2 / 7 with a bad value. Noted in deferred for a future "script-data-integrity" audit.
- `data/moves/effects_pointers.asm` — lens: dispatcher table sizing. findings: 0 (`assert_table_length NUM_MOVE_EFFECTS` on a 159-entry table; coverage gap of 256-159 = 97 byte values which the engine never indexes because move data is authored).
- `engine/battle/move_effects/magnitude.asm` + `data/moves/magnitude_power.asm` — lens: data-table-termination OOB. findings: 0 confirmed (`100 percent` evaluates to 255 via `* $ff / 100` macro, so the last row's threshold catches BattleRandom's max value).
- `engine/battle/move_effects/metronome.asm` — lens: rejection-sampling infinite loop. findings: 0 (`cp NUM_ATTACKS + 1; jr nc, .GetMove` — bounded by RNG; NUM_ATTACKS is a compile-time constant > 0).
- `engine/battle/move_effects/counter.asm` — lens: damage-doubling overflow. findings: 0 (uses `add a + adc a` with `jr nc` to saturate at `$ff/$ff`).
- `engine/battle/move_effects/future_sight.asm` — lens: state-machine corruption, counter wraparound. findings: 0 (counter goes 4→0 monotonically, only fires when exactly 1, no wraparound path).
- `engine/battle/move_effects/pain_split.asm` — lens: HP-averaging overflow. findings: 0 (uses 16-bit ld/srl/rr to compute average; saturation handled by `.skip` branch).
- `engine/battle/move_effects/beat_up.asm` (lines 1-80) — lens: party-index wraparound, status-byte OOB. findings: 0 confirmed in the read; full file has more flows for enemy side.
- `engine/battle/move_effects/hidden_power.asm` — lens: trivially clean (one farcall to bank-local handler).
- `engine/battle/move_effects/fury_cutter.asm` — lens: counter-byte wraparound. findings: 0 crash-class; counter at wPlayerFuryCutterCount can wrap to 0 after 256 consecutive hits (a cosmetic-only Sev 0 issue — practical reachability ~zero).
- `engine/gfx/load_pics.asm` (lines 1-120) — lens: pic-bank confusion, species-OOB into PokemonPicPointers. findings: 0 (`GetFrontpic` filters species via `and a; ret z`, `cp NUM_POKEMON + 1; ret z`, `cp EGG + 1; ret nc`, and a dedicated UNOWN branch reading bounded `wUnownLetter`).
- `macros/data.asm:23` (`percent` macro definition) — lens: percent expansion correctness. findings: 0 (`* $ff / 100` confirmed; 100 percent = 255).
- `engine/menus/save.asm:540-820` — lens: save-load-version-validation, checksum-bypass. findings: 1 (Finding 8 — `cp $ff` legacy fallback still in v2 loader). Both CheckPrimarySaveFile and CheckBackupSaveFile have the issue.
- `constants/misc_constants.asm:28-35` (SAVE_FORMAT_VERSION + spec comment) — lens: spec-vs-code alignment. findings: 0 here but flagged the spec/code mismatch in save.asm (Finding 8).
- `tools/audit/check_save_format_version.py` — lens: existing audit coverage. findings: 0 (audit scope is layout fingerprint, not loader code; Finding 8 is in the gap between audits — proposed adding a strict-loader audit in the fix sketch).
- `engine/events/npc_trade.asm` (lines 1-150 — NPCTrade flow + CheckTradeGender + DoNPCTrade) — lens: trade-flag-state, jump-table-OOB on trade ID. findings: 0 (e=trade ID stored into wJumptableIndex; SmallFarFlagAction is bounded by data; trade attribute accesses use GetTradeAttr with bounded e values).
- `engine/events/fruit_trees.asm` — lens: array-OOB on wCurFruitTree. findings: 0 (wCurFruitTree is set by script just before dispatch; not in save data; `dec a` is safe for 1-based indexing because script always sets nonzero).
- `engine/events/magikarp.asm` (lines 1-100, CheckMagikarpLength + PrintMagikarpLength) — lens: party-OOB on wCurPartyMon. findings: 0 (UI bounds wCurPartyMon via SelectMonFromParty; species filter `cp MAGIKARP` exits early on non-Magikarp).
- `engine/items/tmhm.asm` (lines 1-100, TMHMPocket + TMHM_PocketLoop helpers) — lens: TM/HM array-OOB on wCurItem. findings: 0 (wCurItem set by menu; latent footgun for save-corrupted item ID covered by Finding 7).
- `engine/overworld/scripting.asm` Script_givepoke/giveegg/setevent/clearevent/checkevent/setflag/clearflag (lines 1807-1900) — lens: state-write-without-validation. findings: 0 (per-handler patterns consistent: GetScriptByte → write to WRAM → farcall worker; no inline crashes — risk is upstream script data corruption, deferred to script-integrity audit).
- `engine/movie/trade_animation.asm` (lines 1-100, opcode-table layout) — lens: animation-script dispatch OOB. findings: 0 in the preamble (opcodes are compile-time `tradeanim X` macros that resolve to (X_TradeCmd - Jumptable)/2 — bounded by definition; runtime dispatcher not fully read this iter).
- `engine/items/mart.asm` (lines 1-100, GetMart + OpenMartDialog + LoadMartPointer) — lens: mart-ID OOB. findings: 0 (GetMart's `cp NUM_MARTS` bounds the low byte of mart_id; the macro `pokemart` emits a 16-bit mart_id but valid IDs always have d=0 by convention; latent footgun for malformed scripts noted). MartTypeDialogs has `assert_table_length NUM_MART_TYPES`.
- `engine/overworld/scripting.asm` Script_pokemart (line 521), Script_random (1396), Script_loadvar (1460) — lens: script-data validity. findings: 0 (Script_random *does* explicitly handle the `range=0` case at line 1399-1400 with `ret z` — contrast with Finding 1's RandomRange which doesn't; the script-level safety net masks the engine-level footgun for the only known random caller in script-land).
- `macros/scripts/events.asm:921` (pokemart macro) — lens: macro emits expected byte layout. findings: 0 (emits `db dialog_id; dw mart_id` — confirmed call-side reads match: c=dialog_id, e=mart_id_lo, d=mart_id_hi).
- `engine/battle/ai/items.asm:1-100` (AI_SwitchOrTryItem + SwitchOften) — lens: trainer-attribute OOB, wTrainerClass bound. findings: 0 (wild-mode early-exit at line 5-6 prevents wTrainerClass=0 path; trainer mode sets wTrainerClass from compile-time data 1..NUM_TRAINER_CLASSES).
- `engine/menus/intro_menu.asm` (NewGame + ResetWRAM + ConfirmContinue + Continue_CheckRTC_RestartClock + FinishContinueFunction, lines 1-340) — lens: cold-boot init, save-continue path, RTC handling. findings: 0 (NewGame zero-fills wShadowOAM..wOptions and wGameData; -1 sentinels for RoamMon map data; ConfirmContinue properly closes window on failure path; RTC check correctly distinguishes RTC_RESET state).
- `engine/overworld/events.asm` (OverworldLoop + enable/disable helpers + StartMap + EnterMap, lines 1-130) — lens: wMapStatus jump-table OOB. findings: 0 (writers grep — all sites use named constants MAPSTATUS_START/ENTER/HANDLE/DONE = 0/1/2/3; no path writes 4+).
- `engine/battle/ai/switch.asm` (CheckPlayerMoveTypeMatchups + CheckEnemyMoveMatchups, lines 1-130) — lens: move-index OOB into Moves table. findings: 0 (wPlayerUsedMoves is null-terminated and bailed via `and a; jr z`; entries are compile-time move IDs).
- `engine/battle/ai/boss_policy_move.asm` (MaybePickAdaptiveEnemyLead + .ShouldUseAdaptiveLeadForTrainer, lines 1-100) — lens: party-slot OOB, link-mode guard. findings: 0 (early-exits on link, non-trainer, and non-AdaptiveLead trainers; `FindFirstAliveOTMon`/`FindNextAliveOTMon` are bounded by trainer party size; `inc a; ld [wEnemySwitchMonIndex], a` writes 1-based index).
- `home/map.asm:1299-1300` (LoadMapStatus) — lens: wMapStatus writer audit. findings: 0 (single-byte ld, caller controls value).

### Regions deferred
<!-- iterations append: - region (reason for deferral) -->
- `home/init.asm:60-68` WRAMX multi-bank clear — only the currently-selected WRAMX bank is cleared on cold boot. Need to inventory which WRAMX banks the hack actually reads-before-write to know if any of banks 2-7 are touched. If only WRAMX bank 1 is used (boss AI reserve), this is a non-issue. Defer to dedicated WRAMX-coverage pass.
- `home/lcd.asm` `wLYOverrides` page-alignment — the LCD STAT handler uses `ld h, HIGH(wLYOverrides); ld l, rLY` indexing, which requires wLYOverrides to be page-aligned. Verify by grepping the ram section it lives in. Defer to next iteration.
- `home/decompress.asm` `.rewrite` negative-offset arithmetic — the `cpl + add e` idiom produces `hl = de - mag - 1` in my analysis, but base pokegold ships with this exact code, so either it's correct under the LZ format definition (offsets are 1-based) or it's a long-standing latent bug that hasn't manifested. Defer until I can match against pret/pokegold and the format spec.
- Full review of `engine/menus/save.asm` (1084 lines) — large file, save corruption is the highest-blast-radius bug class; needs its own dedicated iteration.
- `engine/overworld/scripting.asm` script-data-integrity audit — `Script_giveitem`, `Script_givepoke`, `Script_giveegg`, `Script_warp`, etc. don't validate item/species/map/coord IDs before writing engine state. Authored macros use valid values today, but a typo-bug in a script source file would slip a corrupt ID through to the game engine, which then might feed Finding 2 (RunMapSetupScript OOB) or Finding 7 (item-effects OOB). Future audit: cross-reference all `Script_*` data-consumers against the call sites in maps/*.asm to ensure every value is a known constant.
- Full review of `engine/battle/effect_commands.asm` (6634 lines) — sampled DoMove dispatcher only; the 159 individual move-effect handlers each consume the battle script via the `endmove_command` terminator and have unique register-clobber patterns. Each handler is a potential bug surface (see commit `44ca3b29`'s TD-005 Pattern 3 for the historical example). Future iteration should sample handlers that touch hl as input or have a documented `_Far` suffix.
- Full review of `engine/battle/ai/boss_policy_move.asm` (5906 lines) and `boss.asm` — only spot-read the platform layer this pass. Boss AI policy code has the highest churn rate in the repo and the most documented historical bugs (May 2026 cross-bank softlock, April 2026 farcall-hl, AG-08 clobber class).

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

### Finding 6 — `DoBattle` "find first non-fainted OT mon" loop is unbounded
- **Severity:** 2
- **Confidence:** HIGH
- **Category:** oob-read (loop runs off the end of `wOTPartyMon*` if all six are HP=0)
- **File:** `engine/battle/core.asm:19-32`
- **Symptom:** If the OT party state arrives at `DoBattle` with **every** mon's HP = 0, the scan walks past `wOTPartyMon6` into adjacent WRAM (item bag, party data, save buffers — depends on `wram.asm` layout) until it happens to read a non-zero byte. At that point `d` holds an arbitrary value derived from how many slots it walked, and `wBattleAction` is set to that value. The game then "switches to OT mon #d" — indexing OOB in the OT party, computing stats from random WRAM, and almost certainly cascading into a crash or save corruption a few function calls later.
- **Trigger:** No normal play path can reach `DoBattle` with all OT mons at HP=0 — trainer parties are loaded fresh from data, and wild battles only have 1 mon. The trigger is one of: (a) save-state restore that captured the OT party mid-faint without restoring HP, (b) a future buff/scaling code path that zeros all HPs as part of a difficulty modifier, (c) memory corruption from a glitch elsewhere that nukes OT HP bytes.
- **Why:**
  ```asm
  ld hl, wOTPartyMon1HP
  ld bc, PARTYMON_STRUCT_LENGTH - 1
  ld d, BATTLEACTION_SWITCH1 - 1
  .loop
      inc d
      ld a, [hli]
      or [hl]            ; combined HP-high | HP-low; non-zero → mon is alive
      jr nz, .alive
      add hl, bc         ; skip to next mon's HP field
      jr .loop
  ```
  No `cp PARTY_LENGTH` bound on `d`. The loop simply trusts that at least one mon is alive. There's an asymmetric guard for the player at line 59-62 (`call CheckPlayerPartyForFitMon; jp z, LostBattle`), but the OT side has no equivalent.
- **Fix sketch:** Add a 4-byte bound:
  ```asm
  .loop
      inc d
      ld a, d
      cp BATTLEACTION_SWITCH1 + PARTY_LENGTH    ; bail if scanned all 6
      jr nc, .all_ot_fainted
      ld a, [hli]
      ...
  ```
  Then a `.all_ot_fainted` exit point that either declares trainer-loss (the natural semantics) or asserts. Defensible: if you got into `DoBattle` with no live OT mons, the right behaviour is "trainer immediately loses," not "wander into WRAM."
- **False-positive risk:** Mechanism is solid but reachability is purely the precondition. Vanilla pokegold has shipped with this for decades because the precondition never occurs in scripted play. A hack like this one — which adds runtime modifiers (boss AI, scaling, type passive) — increases the surface area, so the prophylactic 4-byte fix is a reasonable hardening.

### Finding 7 — `_DoItemEffect` jumps to garbage if `wCurItem` is 0 or > 187
- **Severity:** 2
- **Confidence:** HIGH
- **Category:** jump-table OOB
- **File:** `engine/items/item_effects.asm:1-12`
- **Symptom:** Reading wCurItem = 0 (no-item / cleared) or wCurItem > 187 (corrupt / out-of-range item id) takes the `dec a; rst JumpTable` path into the 187-entry `ItemEffects` table at index 255 or 187+. The fetched pointer is the two bytes living just past the table — currently whatever instruction stream follows the table in the linked ROM. `jp hl` then jumps to that arbitrary 16-bit value. Likely crash.
- **Trigger:** Pack UI bounds wCurItem to a real bag slot, so the no-corruption case is safe. Triggers if (a) save-data corruption places a >187 item id in the bag, (b) a future feature (e.g. event item delivery, debug menu) sets wCurItem then calls DoItemEffect without re-validating, (c) ITEMATTR pocket data has a bug that lets `_TossItem`/`_CheckItem` get there with a 0 — those dispatchers also `dec a; rst JumpTable` on a pocket value (separate bug, but same shape — already noted in deferred).
- **Why:**
  ```asm
  _DoItemEffect::
      ld a, [wCurItem]
      ld [wNamedObjectIndex], a
      call GetItemName
      call CopyName1
      ld a, 1
      ld [wItemEffectSucceeded], a
      ld a, [wCurItem]
      dec a                        ; 0 → $FF; 188 → 187
      ld hl, ItemEffects
      rst JumpTable                ; 2 bytes per entry, table is 187 entries
      ret
  ```
  `ItemEffects` has no `assert_table_length` (unlike the sibling tables in `data/items/attributes.asm` and `data/items/descriptions.asm`). Item ids in `constants/item_constants.asm` go up to `NUM_ITEMS = 190` (with mail items at $b5-$bd and `ITEM_BE` at $be). Mail items shouldn't reach `DoItemEffect` in normal play (mail attaches to mons, doesn't sit in bag), but the dispatcher has no defence.
- **Fix sketch:** Two layers. (a) Add `assert_table_length NUM_ITEMS - NUM_TMHM_MAIL_ETC` (or whatever the correct exclusion is) on `ItemEffects` — at minimum, hard-state the table's intended size at build time. (b) Add a runtime guard in `_DoItemEffect`: `ld a, [wCurItem]; and a; ret z; cp ItemEffects.end - ItemEffects; ret nc` before the dispatch. Costs ~6 bytes for an unambiguous bound check.
- **False-positive risk:** Mechanism is solid. Practical reachability is *low* under normal play (pack UI filters) but *non-zero* in the presence of save corruption — and mailbox/item-glitch-class bugs in the Gen 2 family historically arose from exactly this kind of "trust the caller" dispatcher. Sev 2 reflects "real but requires upstream corruption to fire."

### Finding 8 — Save loader still accepts `$ff` legacy version after the spec said v2+ must remove it
- **Severity:** 3
- **Confidence:** HIGH
- **Category:** save-format (code/spec mismatch with corruption risk on load)
- **File:** `engine/menus/save.asm:625` and `engine/menus/save.asm:653`
- **Symptom:** A v1-era save (SRAM with `sSaveFormatVersion = $ff`, the pre-marker sentinel) is loaded as if it were a current v2 save, but the WRAM layout in v2 differs from v1 by definition (the marker was added/bumped precisely because the layout drifted). The copy at lines 628-631 / 656-659 (`ld bc, wOptionsEnd - wOptions`; `call CopyBytes`) reads v2-sized blocks out of SRAM that was written with v1 sizes. Fields drift in/out of alignment: stat bytes, current-map data, party data may all read from the wrong offset. After load, the player sees garbage stats, wrong map, glitched name strings, or worse, the next save writes back v2-shaped data over v1 offsets → permanent corruption of any feature whose offset moved.
- **Trigger:** Any user with a v1-era save (anyone who saved during development before the version marker was introduced) loading this build. Per `CLAUDE.md`'s "no migration code anywhere," there is no opt-in / opt-out / conversion path — the save loads silently and the corruption is invisible until a player notices wrong stats or a wrong field name.
- **Why:**
  ```asm
  ; engine/menus/save.asm:613
  CheckPrimarySaveFile:
      ld a, BANK(sCheckValue1)
      call OpenSRAM
      ld a, [sCheckValue1]
      cp SAVE_CHECK_VALUE_1
      jr nz, .nope
      ld a, [sCheckValue2]
      cp SAVE_CHECK_VALUE_2
      jr nz, .nope
      ld a, [sSaveFormatVersion]
      cp SAVE_FORMAT_VERSION         ; current = 2
      jr z, .version_ok
      cp $ff                          ; <-- still accepting legacy
      jr nz, .nope
  .version_ok
      ...                             ; copies v2-sized blocks
  ```
  The spec lives at `constants/misc_constants.asm:29-34` and is unambiguous:
  > `$FF` means "legacy save predating this marker" and is accepted only by v1 to absorb existing dev/playtest saves on first deploy. **v2+ must NOT keep the `$FF` accept path; only the current version and explicitly-migrated previous versions are valid.**

  The version constant is `DEF SAVE_FORMAT_VERSION EQU 2` at line 35. So the loader is at v2 but still accepts the v1-only fallback. Same code-spec mismatch exists in `CheckBackupSaveFile` (line 650-654). The inline comment at the offending line itself says `v2+ must remove this`.

  The existing audit `tools/audit/check_save_format_version.py` doesn't catch this: it fingerprints WRAM/SRAM **source layout** and checks the fingerprint matches the recorded one for the current version. It does not inspect the loader for stale legacy-version branches. (Reasonable scope for that audit — it's a different concern.)

  A previous audit pass already noted this issue (`docs/codex-optimizations.html` flagged it). It remained unfixed.
- **Fix sketch:** Remove the two `cp $ff; jr nz, .nope` branches (lines 625-626 and 653-654), so a non-matching version straight-up rejects the save (`.nope` path → fall through to backup or to defaults). Also remove the comment cruft. Optional follow-up: add a new audit `tools/audit/check_save_loader_version_strict.py` that greps for `cp $ff` in save.asm and fails if found — this prevents the same drift recurring on future bumps.
- **False-positive risk:** The mechanism is concrete. The only thing that softens the impact is whether real users actually have v1-era saves out in the wild. For a hack distributed via patch + cart-flashing tools, dev/playtest saves do exist; CLAUDE.md treats save-format-version bumps as user-approval items precisely because this risk is real. Sev 3 (not 4-5) because the corruption is *silent* and *gradual* rather than a hard freeze — but the freeze could come downstream when corrupted state (e.g. an OOB species id, a >100 level byte) hits one of the unguarded dispatchers documented in Findings 2/6/7.

---

## Summary table

| # | Title | Sev | Confidence | Category | File |
| --- | --- | --- | --- | --- | --- |
| 1 | `RandomRange` hangs on `a=0` | 1 | HIGH | infinite-loop | [home/random.asm:50](home/random.asm:50) |
| 2 | `RunMapSetupScript` OOB on `hMapEntryMethod` low-nibble == 0 or > 11 | 2 | HIGH | jump-table OOB | [engine/overworld/map_setup.asm:1](engine/overworld/map_setup.asm:1) |
| 3 | `rst $30` bypasses crash trap → executes JumpTable tail | 1 | HIGH | broken crash trap | [home/header.asm:20](home/header.asm:20) |
| 4 | `DelayFrames` hangs if LCD off | 1 | HIGH | infinite-loop | [home/delay.asm:1](home/delay.asm:1) |
| 5 | `Init.wait` hangs if entered with LCD off | 1 | HIGH | infinite-loop | [home/init.asm:51](home/init.asm:51) |
| 6 | `DoBattle` "find first non-fainted OT mon" loop unbounded | 2 | HIGH | oob-read | [engine/battle/core.asm:22](engine/battle/core.asm:22) |
| 7 | `_DoItemEffect` OOB-jumps when `wCurItem` is 0 or > 187 | 2 | HIGH | jump-table OOB | [engine/items/item_effects.asm:1](engine/items/item_effects.asm:1) |
| 8 | Save loader still accepts `$ff` legacy version at v2 — code/spec mismatch, silent save corruption on load | 3 | HIGH | save-format | [engine/menus/save.asm:625](engine/menus/save.asm:625), [engine/menus/save.asm:653](engine/menus/save.asm:653) |

**Triage hint (post-iter 2):** All 7 findings remain latent — no reproducible trigger in current code. Findings 2, 6, 7 are the most operationally important: each is a missing-bound-check on a dispatcher/loop that "trusts the caller," and the cost of the fix is 4-8 bytes per site. The cheapest hardening pass would batch them: add explicit bound-check guards to `RunMapSetupScript`, `DoBattle .loop`, and `_DoItemEffect` together, plus matching `assert_table_length` directives on `MapSetupScripts` and `ItemEffects`. No Sev 3+ crashes have been observed yet across **41 review entries (~35 unique files; some re-read with different lenses)**. Deeper passes need to target high-value crash surfaces still un-audited: full `engine/battle/core.asm` (8748 lines), `engine/overworld/scripting.asm` script-cmd handlers (162 commands), `engine/battle/effect_commands.asm` (6634 lines), audio playback (notes/SFX), engine/link/, and the Gen-2 trade-cable / Time Capsule code paths.

---

## What I did NOT review

Honest list of regions skipped, with reason. So the next pass knows where to start.
