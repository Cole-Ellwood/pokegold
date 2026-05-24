# ROM Source Bug Audit - 2026-05-24

## Goal

**repo-proven** Read-only audit of actual ROM source/data behavior, excluding
debugger and support tooling except for repo routing docs and read-only
verification commands. Allowed writes were this audit file and
`audit/rom_source_bug_audit_2026-05-24_scratchpad.md`.

## Summary

**repo-proven** I found one confirmed ROM behavior bug in the current source:
Boss AI can hard-block Hidden Power as if it were still `NORMAL` before the
battle command rewrites Hidden Power's type from DVs.

**repo-proven** I did not edit ROM source. The only writes from this pass are
the scratchpad and this audit file.

## Finding 1 - Boss AI Misclassifies Hidden Power Immunity

**repo-proven** `engine/battle/ai/boss_policy_move.asm:276` calls
`.DamagingMoveBlockedByTypeImmunity` immediately after held-item move legality
and returns early on carry. The helper at
`engine/battle/ai/boss_policy_move.asm:425` checks `wEnemyMoveStruct +
MOVE_POWER`, calls `BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem`, sets the
score to 80 if `wTypeMatchup` is zero, and returns carry.

**repo-proven** That matchup helper reads the current static move type from
`wEnemyMoveStruct + MOVE_TYPE` (`engine/battle/ai/boss_platform.asm:597`).
For Hidden Power, the static ROM move row is:

```asm
move HIDDEN_POWER, EFFECT_HIDDEN_POWER, 60, NORMAL, 100, 15, 0
```

at `data/moves/moves.asm:253`.

**repo-proven** Actual battle execution does not keep Hidden Power as Normal:
`engine/battle/hidden_power.asm:1` computes Hidden Power's type from the user's
DVs and writes it back through `BATTLE_VARS_MOVE_TYPE` before damage stats and
type matchup are applied.

**repo-proven** Concrete source scenario:

- `data/trainers/parties.asm:179`, `:189`, and `:199` give Rival1's Magneton
  `HIDDEN_POWER`.
- `data/trainers/dvs.asm:13` gives Rival1 DVs `13,13,13,13`.
- The ROM Hidden Power formula maps those DVs to Bug.
- `data/pokemon/base_stats/gengar.asm:6` makes Gengar `GHOST, PSYCHIC_TYPE`.
- `data/types/type_matchups.asm:81-82` makes Bug vs Psychic super-effective and
  Bug vs Ghost resisted, for net neutral.
- `data/types/type_matchups.asm:115` makes Normal vs Ghost no effect.

**repo-proven** Result: if the player has an active Ghost/Psychic target such
as Gengar, the new Boss AI gate sees Hidden Power's stale `NORMAL` type,
decides the move is immune, sets the move score to 80, and exits before the
Hidden Power-specific scoring path can account for the real Bug type.

**judgment** This is a real move-selection bug, not only a trace/reporting
issue. The AI may discard a valid neutral Hidden Power line against Ghost
targets for Rival1 and can repeat the same mistake for any trainer Hidden Power
whose real DV-derived type is not Normal.

**judgment** Fix direction: the new hard-immunity gate should skip
`EFFECT_HIDDEN_POWER` or compute the same DV-derived type used by
`HiddenPowerDamage` before checking immunity. Do not use the static move-table
type for Hidden Power.

## Clean Passes And Rejected Leads

**repo-proven** `python tools\audit\check_ko_band_oracle_self_test.py` passed:
the generated Boss AI matchup table matches the dry-run generator output, with
39 leader rows and 179 slots.

**repo-proven** `python tools\audit\check_farcall_hl_clobber.py` passed and
scanned 1877 ASM files.

**repo-proven** `python tools\audit\check_battle_math_safety.py` passed and
scanned 196 ASM files.

**repo-proven** `python tools\audit\check_vram_request_contract.py` passed.

**repo-proven** `git diff --check -- engine constants data maps home ram audio
gfx macros main.asm layout.link Makefile` produced no output.

**repo-proven** Active ROM `INCLUDE`/`INCBIN` target scan found 2214 INCLUDE
targets and 3253 INCBIN targets, with 0 missing targets after excluding nested
worktrees and non-ROM support areas.

**repo-proven** ROM data consistency scan found 0 issues across move table
ordering, 256-wide item tables, 251 base-stat files, 251 evolution/learnset
sections, 3225 wild encounter rows, and 465 map trainer references.

**repo-proven** Rejected leads:

- Rival1 Gastly `SPITE -> CONFUSION` did not stale the Boss AI matchup table.
- Sleep duration stores 3..5, which matches 2..4 denied actions because sleep
  decrements before the wake check.
- Early stat-drop discipline did not lose the score pointer; the score helpers
  reload `hl` from `wBossAIScorePtr`.
- The trainer-battle context backup replaced 17 bytes of padding with a
  16-byte backup plus a 1-byte active flag, so that diff does not grow WRAM.
- The changed queued VRAM request code passes the repo's VBlank acknowledgment
  contract.

## Boundaries

**repo-proven** No ROM build or emulator/manual playtest was run in this pass.
Those would create or depend on build/runtime artifacts, so this audit stops at
source/static proof.

**repo-proven** External reference used for Game Boy VBlank timing context:
[Pan Docs - Rendering](https://gbdev.io/pandocs/Rendering.html). The confirmed
bug above does not depend on that external reference; it is source-proven from
the local ROM code.
