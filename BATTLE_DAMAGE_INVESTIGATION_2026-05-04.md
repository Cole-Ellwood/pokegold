# Battle damage 5x bug — investigation notes (2026-05-04)

**Status:** open. Bug reproduces on a fresh new game, on both `pokegold.gbc` and `pokegold_debug.gbc`. Root cause not found from static source inspection. The fixes that landed yesterday (`44ca3b29`, `5e9b785f`) are byte-confirmed in both ROMs but do not eliminate the symptom.

## Symptom

Every physical attack does roughly 5x intended damage on a fresh new game.

**Repro:** new game, level 5 Cyndaquil (20 HP, 9 Def) takes 18 damage from a level 2 wild Pidgey using Tackle. Expected damage with normal stats: ~3-4. Ratio ≈ 5x-6x.

This matches the symptom shape of the original `44ca3b29` bug ("BP=208 from `d` clobber via `ld de, wEnemyMonItem`; HIGH(`$D0F0`)=`$D0`=208"), where damage was inflated by ~`208/40 = 5.2x` for Tackle's BP=40.

The user's report originally framed this as "the BP=208 fix isn't in this rom version." Investigation showed the fix bytes ARE in the ROM, but the symptom is identical anyway.

## Branch state when bug reproduces

- Branch: `claude/romantic-meitner-314fb1` (HEAD `c60a2318`)
- Pushed to `origin/claude/romantic-meitner-314fb1`
- 13 commits ahead of `origin/codex/cleanup-gsc-rebalance-split` tip (`5e9b785f`)
- ROM build: `pokegold.gbc` SHA `20851907a83912f207d7a48408f821bdf9ed5052`, May 4 14:58 build, verifies against `roms.sha1`

## What was verified (bug is NOT this)

### Fix bytes are in the ROM at all confirmed sites

Read raw ROM bytes at three known fix sites in `pokegold.gbc`:

| Site | File offset | First bytes | Expected post-fix prefix | Match |
|---|---|---|---|---|
| `GetUserItem` | `0x37ec4` | `d5 21 fd ca 11 f0 d0 cd` | `d5` (push de) | ✓ |
| `ApplyLateGenDamageStatsItemMods_Far` | `0x3b08e` | `f5 d5 cd 28 78 fe 14 30` | `f5 d5` (push af / push de) | ✓ |
| `GetMaxHP` | `0x3cd21` | `21 0e cb d5 11 01 d1 cd` | `21 ?? ?? d5` (ld hl, …; push de) | ✓ |

Decoded `GetUserItem`:
```
push de               ; D5  ← the 44ca3b29 fix
ld hl, wBattleMonItem ; 21 FD CA
ld de, wEnemyMonItem  ; 11 F0 D0
call _GetSidedHL      ; CD 7E 3C
pop de                ; D1
ld b, [hl]            ; 46
jp GetItemHeldEffect  ; C3 E2 7E
```

This is exactly the post-fix sequence per the `44ca3b29` diff.

### Source matches binary

Source file `engine/battle/effect_commands.asm:6420-6435` has the `push de` / `pop de` lines and the `; push/pop de is load-bearing…` header comment from `44ca3b29`'s diff.

### Both ROMs have identical fix-site bytes

`pokegold.gbc` and `pokegold_debug.gbc` are byte-identical at all three fix sites. The damage path in banks `0x0d` (Effect Commands) and `0x0e` (boss/items) differs by 0-2 bytes total between the two ROMs. Big debug-vs-release diffs (~7400 bytes each) are in banks `0x01` and `0x70` — debug overlay code, not the damage chain.

This rules out "fix only worked in debug build" — the fix sites are identical.

### Bug reproduces on both ROMs

User confirmed: Cyndaquil (20 HP) one-shot from full HP by wild Pidgey Tackle on `pokegold_debug.gbc` after copying `pokegold.sav` over `pokegold_debug.sav`. Same as `pokegold.gbc`.

### Bug reproduces on a fresh new game

User started a brand new save on `pokegold.gbc`. Level 5 Cyndaquil with 20 HP, 9 Def takes 18 damage from level 2 wild Pidgey Tackle. So save-state corruption from a previously-buggy ROM is NOT the cause.

### This session's commits don't touch Tackle's path

Commits between yesterday's fix tip (`5e9b785f`) and HEAD (`c60a2318`) that touch `engine/battle/` or `home/battle*`:

- `93ff692e` (AG-04 codemod `ld a, 0` → `xor a`): 3 sites in battle code
  - `effect_commands.asm:1996` — `BattleCommand_LowerSub.rollout_rampage` (rollout/thrash, not Tackle)
  - `effect_commands.asm:3079` — `BattleCommand_ConstantDamage` PSYWAVE branch (not Tackle)
  - `core.asm:7905` — `StartBattle` setup (sprite-update flag, not damage)
- `8e93a627` (AG-06 codemod): touched `home/battle.asm` `FarCopyRadioText` only — radio text, not damage path
- All other session commits are docs-only or audit-only

None of these are on Tackle's damage code path. The bug pre-existed at `5e9b785f`.

## Audited code paths — `d` is preserved

Tackle (BP=40) goes through `EnemyAttackDamage` (Pidgey is the enemy/attacker) since `BattleCommand_DamageStats` falls through to `EnemyAttackDamage` when `hBattleTurn != 0`.

Path traced from `d = BP = 40` (line 2667-2668) through to `damagecalc`. Every function in this chain was checked for `de` preservation:

- **`Battle_GetEffectiveMoveCategory`** (HOME wrapper) → `farcall TypePassive_GetEffectiveMoveCategory_Far`. The `_Far` body pushes hl/de/bc at entry, pops them at `.done` (only one exit; checked all paths). FarCall mechanism preserves `de`. **OK.**
- **`CheckDamageStatsCritical`** (HOME wrapper) → `callfar CheckDamageStatsCritical_Far`. For non-crit attacks (typical), the `_Far` body returns early at `scf; ret z` before touching `de`. **OK.**
- **`ThickClubBoost` / `LightBallBoost`** — both push `bc`/`de` at entry, set `d` as parameter to `SpeciesItemBoost`, pop `de`/`bc` at exit. **OK.**
- **`ApplyLateGenDamageStatsItemMods`** (HOME thunk) → `homecall ApplyLateGenDamageStatsItemMods_Far`. Wrapper pushes `af`/`de` at entry (post-`5e9b785f` fix), pops at `.done`. Boost helpers (`.ApplyChoiceBandBoost` etc.) call `_CheckUserItemEquals` / `_CheckOpponentItemEquals` → `callfar GetUserItem` / `callfar GetOpponentItem`. `GetUserItem` has the `44ca3b29` push/pop de fix. `GetOpponentItem` uses inline turn-check (no `_GetSidedHL`), no `de` clobber. For an attacker holding no item, all boost helpers `ret nz` before executing `ld d, *_DEN`. **OK.**
- **`callfar DittoMetalPowder_Far`** — for physical Tackle, falls past the `cp SPECIAL; ret nc` early-return into `BattlePartyAttr` then `cp DITTO; ret nz` (Pidgey is not Ditto). `BattlePartyAttr` only push/pops `bc`. `GetPartyLocation` only manipulates `hl`/`bc`. **OK.**
- **`TruncateHL_BC`** — operates on `h`/`l`/`b`/`c` only. **OK.**
- **`GetBattleVar` / `GetBattleVarAddr`** — uses inline turn-check (not `_GetSidedHL`); push/pops only `hl`/`bc`. **OK.**

### Macro-level checks

- `farcall` macro: `ld a, BANK(\1) :: ld hl, \1 :: rst FarCall`. Clobbers `a`, `hl`. Does not touch `de`.
- `callfar` macro: `ld hl, \1 :: ld a, BANK(\1) :: rst FarCall`. Same as above.
- `homecall` macro: `ldh a, [hROMBank] :: push af :: ld a, BANK(\1) :: rst Bankswitch :: call \1 :: pop af :: rst Bankswitch`. `rst Bankswitch` only touches `a`. Does not touch `de`.
- `FarCall_hl` (in `home/farcall.asm`): uses `a`, `b`, `c` for bank switching and `bc` return value passing. Does not touch `de`.

### `5e9b785f` covered all suspected `_GetSidedHL` clobber sites

The 5 fix sites in `5e9b785f` plus the 1 in `44ca3b29` = 6 sites. I enumerated all callers of `_GetSidedHL` (28 sites total). Only the ones called from the damage path during a vanilla-no-item Tackle scenario matter:

- `effect_commands.asm:6430` — inside `GetUserItem` (fixed by `44ca3b29`)
- `effect_commands.asm:2323` — `BattleCommand_StartLoop` (rollout/rampage moves only, not Tackle)
- `effect_commands.asm:1919, 3117, 4016, 5534` — other commands not on Tackle's path
- `late_gen_held_items.asm:232` — `.GetUserMetronomeCount` (Metronome holder only)
- `late_gen_held_items.asm:357` — `.UserStillAlive` (Life Orb damage only)
- `core.asm:1776, 1848, 1960, 1974, 1990` — outside damage path
- The 5 fixed sites in `5e9b785f` (GetMaxHP, ApplyLateGenDamageStatsItemMods_Far, FrustrationPower, HappinessPower, Sketch)

None of the unfixed call sites are reached during a no-item physical Tackle.

## What's NOT been verified

These are gaps in the static audit; any of them could hide the bug.

- The exact bytes flowing into `BattleCommand_DamageCalc` at runtime (no probe ROM built this session).
- Whether `wEnemyMoveStruct` data is being loaded correctly when the wild battle starts (move-data table → struct copy path).
- Whether the move script dispatcher between `damagestats` and `damagecalc` preserves `b`/`c`/`d`/`e`.
- The full body of `CheckDamageStatsCritical_Far` past the early-return (only checked the no-crit path).
- Whether `wCriticalHit` is being unexpectedly set to 1 elsewhere, routing through the crit branches.
- The `damagecalc` body itself past the `d == 0` check at line 2816.

## Hypotheses

Ranked by my current best guess:

1. **There's a 6th register-clobber site neither `44ca3b29` nor `5e9b785f` covered.** Possibly in a function called between `damagestats` exit and `damagecalc` entry that I haven't looked at — the move-script dispatcher itself, or a late-gen check I missed. Static audit didn't surface it but the symptom shape is unmistakably "BP clobbered to ~208."
2. **Yesterday's verification was on a different scenario than the user remembers.** The "Geodude takes 2 damage" verification on `pokegold_debug.gbc` may have been on a state where some confounding factor (level scaling, type effectiveness, an item) made damage appear correct even with a partial fix. The user's recollection may not match what was actually tested.
3. **`damagecalc` itself has a bug** that scales output ~5x — possibly something in the multiplier chain (STAB, type, crit) misapplying. The 5x ratio happens to match BP=208, but could also come from elsewhere.
4. **Move struct loading is corrupting `wEnemyMoveStructPower`** — the BP byte itself is wrong before `EnemyAttackDamage` even reads it.

## Diagnostics that would resolve this

In effort order:

1. **Test `pokegold-fix-hl-clobber-v2.gbc`** (Apr 29 probe ROM) on a fresh new game with the same scenario. If it shows the same 18-damage bug, the bug pre-dates `44ca3b29` and yesterday's fix never actually addressed this path. If it shows correct ~3-4 damage, the regression is between Apr 29 and `5e9b785f`.
2. **Bisect** between `5e9b785f` and the build that last showed correct damage. The `pokegold-bisect-step1.sav` through `step5.sav` files in the repo root suggest a prior bisect workflow. Slow but definitive.
3. **Build a probe ROM** that prints `d` at `damagecalc` entry. Same approach `44ca3b29` used to find the GetUserItem clobber (commit message: "Diagnosis took a probe ROM with 3 sites: Entry b/c/d/e, PostDivDef hQuotient, End wCurDamage"). Highest effort but tells us exactly which value is wrong, immediately pointing to the clobber site.

## Files of interest for the next agent

- `engine/battle/effect_commands.asm:2498-2780` — `BattleCommand_DamageStats`, `PlayerAttackDamage`, `EnemyAttackDamage`, `BattleCommand_DamageCalc`
- `engine/battle/late_gen_held_items.asm:1-30, 478-540` — `ApplyLateGenDamageStatsItemMods_Far`, `DittoMetalPowder_Far`
- `engine/battle/late_gen_held_items.asm:844-870` — `_CheckUserItemEquals` / `_CheckOpponentItemEquals` / `_CheckItemEquals_finish`
- `engine/battle/type_passive_damage_mods.asm:478-540` — `TypePassive_GetEffectiveMoveCategory_Far`
- `home/battle.asm:13-69` — `GetPartyLocation`, `BattlePartyAttr`, `OTPartyAttr`, related party helpers
- `home/farcall.asm` — `FarCall_hl` mechanism
- `home/battle_vars.asm:115-130` — `_GetSidedHL`
- `macros/farcall.asm` — `farcall` / `callfar` / `homecall` macro definitions
- `tech_debt/ASM_GUIDE_AUDIT_2026-05-03.md` — the AG-NN audit log; AG-07/AG-08 detail blocks document the recent farcall a-clobber findings
- `docs/asm_authoring_guide.md` §3.13 — silent register-clobber regressions from helper extraction (the class of bug `44ca3b29` documented)
- `docs/asm_authoring_guide.md` §5.12 — register-passing across the move-script dispatcher

## Relevant commits

| SHA | Description |
|---|---|
| `c60a2318` | HEAD when bug observed (docs-only commit) |
| `5e9b785f` | Yesterday's last fix; 4 transitive de-clobbers + ApplyLateGenDamageStatsItemMods_Far wrapper |
| `44ca3b29` | Yesterday's GetUserItem push/pop de fix (the original "BP=208" fix) |
| `a6a00ea8` | AG-08 fix in TypePassive_GetEffectiveMoveCategory_Far (mirror a→c at .done; doesn't touch d) |
| `769d6dd4` | AG-07 paralysis fail check fix (unrelated to damage scale) |
| `f2e18554` | Boss AI thunk fix (unrelated) |
| `3f00da81` | TD-005 Pattern 3 refactor that introduced the original BP=208 bug into GetUserItem |
| `80c2d5c6` | Original "add tactical AI and late-gen mechanics" commit; per `5e9b785f` body, the damage-amp bugs were latent since this commit |

## What was tried this session before this doc

- Verified ROM byte-level fix is present at GetUserItem, ApplyLateGenDamageStatsItemMods_Far, GetMaxHP
- Verified pokegold.gbc and pokegold_debug.gbc are identical at fix sites
- Compared ROM diffs between debug and release (7400+ bytes diff in banks 0x01/0x70, 0-2 bytes in damage banks)
- Audited every function called between `d = BP` (line 2668 of `EnemyAttackDamage`) and `damagecalc` entry
- Read `farcall` / `callfar` / `homecall` macro expansions; confirmed none clobber `de`
- Enumerated all 28 callers of `_GetSidedHL`; mapped which ones are on Tackle's path
- Read the `5e9b785f` and `44ca3b29` commit diffs in full to understand what was fixed
- Confirmed user's save isn't the cause: fresh new game reproduces the bug
- Set up `pokegold_debug.sav` as a clone of `pokegold.sav` (backup at `pokegold_debug.sav.bak`) so debug ROM testing uses the same save state
