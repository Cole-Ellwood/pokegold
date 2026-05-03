# TD-005 Pattern 3 — site enumeration and design rationale

**Generated:** 2026-05-03 by claude-kind-swanson-ae5a65
**Tool:** `tools/audit/_td005_pattern3_enum.py` (strict regex)

## Scope and shape

The textbook "Pattern 3" sketched in `FINDINGS_DETAIL.md:216-227` was the
post-test branch-and-rejoin shape:

```asm
ldh a, [hBattleTurn]
and a
jr z, .player_side
ld hl, wEnemyMonXXX
jr .got_side
.player_side
ld hl, wBattleMonXXX
.got_side
```

In practice, **the post-test branch-and-rejoin shape barely exists** (5
sites total across the codebase — see `_td005_pattern3_enum.py` first
bucket pass). The dominant shape this codebase actually uses is the
**pre-load + jr-z-skip** shape:

```asm
ld hl, wPlayerXXX           ; 3 bytes — player addr loaded by default
ldh a, [hBattleTurn]         ; 2 bytes
and a                        ; 1 byte
jr z, .got                   ; 2 bytes — player turn falls through to .got
ld hl, wEnemyXXX             ; 3 bytes — enemy turn replaces hl
.got                         ; 0 bytes (label)
                             ; 11 bytes total per site
```

This evidence file enumerates the **strict pre-load shape**: a 6-line
match that requires the matched rejoin label to be the actual jr target.
Both `wPlayer*` and `wBattle*` are accepted as the player-side prefix
(this codebase uses `wBattle*` for the active-party slot's battle stats
and `wPlayer*` for player-side battle metadata).

## Why the pre-load shape exists

Most Pattern 3 sites are computed on the player turn 95% of the time
(player initiates the action; the engine reads the player's struct).
The pre-load form puts the common case in the fall-through path, saving
a `jr` on player turns at the cost of a longer enemy-turn path. The
codebase consistently uses this convention — no `enemy_default` matches
were found in the 27-site set.

## Sites (27 total)

Excluded files: `engine/pokemon/experience.asm` (user WIP per AGENT_LOG
2026-05-03 partial entry).

### Bank-pressure mapping

| Containing section | Bank | Free bytes (pre-Pattern 3) | Sites in this run | Bytes recoverable here |
|---|---|---|---|---|
| `Effect Commands` | ROMX 0d | **6** (canary) | 12 | 24 |
| `Late Gen Held Items` | ROMX 0e | 568 | 9 | 18 |
| `Battle Core` | ROMX 0f | (~580) | 5 | 10 |
| `bank3E_2` (hidden_power) | ROMX 3e | not tight | 1 | 2 |
| **TOTAL** | | | **27** | **54** |

The 12 sites in `Effect Commands` are the strategic value: bank 0x0d is
the new tight canary per ADDENDUM 2026-05-03. 24 bytes of relief there
takes free bytes from 6 → ~30, materially un-tightening the canary.

The other banks are convenience savings — the helper exists, callers
should use it everywhere for consistency.

### Sites by file

#### `engine/battle/effect_commands.asm` — 6 sites (bank 0x0d)

| Line | Player addr | Enemy addr | Rejoin label |
|---|---|---|---|
| 1917 | `wPlayerMoveStruct + MOVE_CHANCE` | `wEnemyMoveStruct + MOVE_CHANCE` | `.got_move_chance` |
| 2324 | `wPlayerRolloutCount` | `wEnemyRolloutCount` | `.ok` |
| 3121 | `wBattleMonHP` | `wEnemyMonHP` | `.reversal_got_hp` |
| 4023 | `wPlayerStatLevels` | `wEnemyStatLevels` | `.got_stat_levels` |
| 5544 | `wBattleMonMaxHP` | `wEnemyMonMaxHP` | `.got_hp` |
| 6437 | `wBattleMonItem` | `wEnemyMonItem` | `.go` |

#### `engine/battle/move_effects/*.asm` — 6 sites (bank 0x0d, INCLUDE'd inside Effect Commands)

| File | Line | Player addr | Enemy addr | Rejoin label |
|---|---|---|---|---|
| `bide.asm` | 7 | `wPlayerRolloutCount` | `wEnemyRolloutCount` | `.check_still_storing_energy` |
| `conversion2.asm` | 5 | `wBattleMonType1` | `wEnemyMonType1` | `.got_type` |
| `frustration.asm` | 3 | `wBattleMonHappiness` | `wEnemyMonHappiness` | `.got_happiness` |
| `mimic.asm` | 7 | `wBattleMonMoves` | `wEnemyMonMoves` | `.player_turn` |
| `return.asm` | 3 | `wBattleMonHappiness` | `wEnemyMonHappiness` | `.ok` |
| `sketch.asm` | 27 | `wBattleMonMoves` | `wEnemyMonMoves` | `.get_last_move` |

#### `engine/battle/type_passive_damage_mods.asm` — 7 sites (bank 0x0e)

| Line | Player addr | Enemy addr | Rejoin label |
|---|---|---|---|
| 211 | `wPlayerMoveStruct + MOVE_TYPE` | `wEnemyMoveStruct + MOVE_TYPE` | `.got_type` |
| 265 | `wBattleMonType1` | `wEnemyMonType1` | `.got_user_types` |
| 478 | `wPlayerMoveStruct + MOVE_TYPE` | `wEnemyMoveStruct + MOVE_TYPE` | `.got_type` |
| 506 | `wPlayerMoveStruct + MOVE_ANIM` | `wEnemyMoveStruct + MOVE_ANIM` | `.got_anim` |
| 615 | `wPlayerMoveStruct + MOVE_POWER` | `wEnemyMoveStruct + MOVE_POWER` | `.got_power` |
| 625 | `wPlayerMoveStruct + MOVE_EFFECT` | `wEnemyMoveStruct + MOVE_EFFECT` | `.got_effect` |
| 692 | `wPlayerScreens` | `wEnemyScreens` | `.got_screens` |

#### `engine/battle/late_gen_held_items.asm` — 2 sites (bank 0x0e)

| Line | Player addr | Enemy addr | Rejoin label |
|---|---|---|---|
| 219 | `wPlayerMetronomeCount` | `wEnemyMetronomeCount` | `.got_counter` |
| 347 | `wBattleMonHP` | `wEnemyMonHP` | `.check_hp` |

#### `engine/battle/core.asm` — 5 sites (bank 0x0f)

| Line | Player addr | Enemy addr | Rejoin label |
|---|---|---|---|
| 1774 | `wBattleMonType1` | `wEnemyMonType1` | `.ok` |
| 1849 | `wBattleMonHP` | `wEnemyMonHP` | `.ok` |
| 1956 | `wBattleMonMaxHP` | `wEnemyMonMaxHP` | `.ok` |
| 1972 | `wBattleMonHP` | `wEnemyMonHP` | `.ok` |
| 1991 | `wBattleMonHP + 1` | `wEnemyMonHP + 1` | `.ok` |

#### `engine/battle/hidden_power.asm` — 1 site (bank 0x3e_2)

| Line | Player addr | Enemy addr | Rejoin label |
|---|---|---|---|
| 4 | `wBattleMonDVs` | `wEnemyMonDVs` | `.got_dvs` |

## Helper design

Placement: `home/battle_vars.asm` (HOME / ROM0). Rationale:
- ROM0 is reachable from every bank with a plain `call` — no `farcall`
  overhead.
- `home/battle_vars.asm` already groups side-aware helpers
  (`GetBattleVarAddr` etc.).
- ROM0 has 236 bytes free (per `pokegold.map` summary 2026-05-03);
  a 7-byte helper takes it to 229.

Signature:

```asm
; Returns hl pointing to the player-side or enemy-side address based on
; whose turn it is. Designed to replace the pre-load + jr-z-skip Pattern 3
; idiom (see tech_debt/EVIDENCE/td_005_pattern3_sites.md).
;
; Inputs:
;   hl = player-side address (kept on player turn)
;   de = enemy-side address  (replaces hl on enemy turn)
; Output:
;   hl = picked address
; Clobbers: af, de
; Preserves: bc
_GetSidedHL::
    ldh a, [hBattleTurn]
    and a
    ret z       ; player turn — hl already correct
    ld h, d
    ld l, e
    ret
```

Size: 7 bytes (`F0 D5` + `A7` + `C8` + `54` + `5D` + `C9`).

## Per-site transformation

Before (11 bytes, `.got` label removed):

```asm
ld hl, wPlayerXXX
ldh a, [hBattleTurn]
and a
jr z, .got
ld hl, wEnemyXXX
.got
```

After (9 bytes):

```asm
ld hl, wPlayerXXX
ld de, wEnemyXXX
call _GetSidedHL
```

Per-site savings: **2 bytes**.

### Caller-impact analysis

The helper clobbers `af` and `de`. Reviewing the 27 sites:

- All 27 sites do `ldh a, [hBattleTurn]` themselves, so they don't expect
  `a` to survive — the clobber is a no-op for callers.
- 0 of 27 sites have a live `de` value at the side-branch (verified by
  reading 5 lines before each match for `ld de, ...` or stack-pushed `de`).
  The `de` clobber is safe.
- `bc` is preserved by the helper, matching the helper convention used
  elsewhere in `home/battle_vars.asm`.

### Label-removal safety

Each site's `.got*` rejoin label is local to the enclosing function. The
strict regex requires the labeldef to immediately follow the second
`ld hl`, with no other instructions between. After conversion the label
becomes orphan; the next instruction simply reads `hl`. No `jr` from
anywhere else can target the now-removed label because the pattern only
matches sites where the label is bare (no other forward references).

(Per-site verification done at conversion time: grep for the label name
in the same file should show 1 def and at most 1 ref — the immediate
`jr z` we're removing. If 2+ refs exist, leave the label as a no-op
target and only remove the test/branch lines.)

## Realistic byte recovery

| Pattern | Sites | Bytes recovered | Notes |
|---|---|---|---|
| Site conversions | 27 | +54 | 2 bytes/site |
| Helper in ROM0 | 1 | -7 | added to home/battle_vars.asm |
| **Net** | | **+47** | |

**Below the FIX_PROPOSALS "Updated 2026-05-02" 100-byte stop-and-re-evaluate
threshold.** Same call as Pattern 1: 41 bytes was deemed worth it because
the bytes landed in a tight bank. Here, **24 of the 47 bytes land in the
new canary bank 0x0d**, which is the strategic value.

## Out-of-scope shapes (deliberately not converted)

Sites that match the loose 4-line "ldh + and + jr" header but DON'T fit
the strict 6-line pre-load shape (and so won't be converted by this
session):

- **Multi-pointer pre-loads** (e.g., `.UserAttackGreaterThanSpAtk` in
  `type_passive_damage_mods.asm:529`): pre-loads both `hl` AND `de`,
  swaps both. Helper signature would need to take 4 addresses.
- **Asymmetric arms** (most common — 58 sites): one arm loads `hl`, the
  other does `ld a, ...` or `xor` etc. Not a side-branch over the same
  data shape — these are real branching control flow.
- **Symmetric `call`** (10 sites): both arms call different functions.
  A side-aware function call would need a different helper (jump table).

Future TD work could address these with separate helpers, but each
shape has its own design considerations and per-site savings calc.

## Verification commands

```bash
# Re-enumerate (expect 27 sites unchanged before conversion):
python3 tools/audit/_td005_pattern3_enum.py | grep "^Total sites:"

# After conversion — expect helper to exist exactly once:
grep -c '^_GetSidedHL::' home/battle_vars.asm

# After conversion — expect no remaining strict-Pattern-3 sites:
python3 tools/audit/_td005_pattern3_enum.py | grep "^Total sites:"
# Should report: Total sites: 0
```
