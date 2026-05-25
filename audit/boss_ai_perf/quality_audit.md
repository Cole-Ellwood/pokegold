# Boss-AI perf cache: behavior-preservation audit (2026-05-25)

Systematic review of the four per-tick caches landed in `a8d095d8` +
`44aa447c`, checking each against side-effect preservation, register
clobber, RNG consumption, and trace-flag behavior. The question: do any
of these alter what a gym leader would do, even subtly?

For each cache: list (1) what the original uncached function did to
visible state, (2) what the wrapper does on hit, (3) the delta, and
(4) whether any caller relies on the changed bit.

## Cache 1: `BossAI_PublicEnemyFaster`

**Original uncached body** (`boss_policy_move.asm:3729 BossAI_PublicEnemyFasterUncached`):
- `push hl/de/bc/af` — saves all four caller regs + wCurSpecies snapshot.
- Sets wCurSpecies = player species, calls `GetBaseData` → loads
  `wBaseStats / wBaseSpeed` with PLAYER's data.
- Sets wCurSpecies = enemy species, calls `GetBaseData` → loads
  `wBaseStats / wBaseSpeed` with ENEMY's data.
- Compares speeds, possibly checks Choice Scarf via
  `BossAI_GetEnemyHeldEffect`.
- BOTH return paths (`.enemy_faster` and `.enemy_not_faster`) do:
  `pop af; ld [wCurSpecies], a; and a; call nz, GetBaseData; pop bc/de/hl`.
  The `call nz, GetBaseData` reloads `wBaseStats` with the ORIGINAL
  active species, so net side effect on `wBaseStats` is **zero**.
- Returns: `scf` (faster) or `and a` (not faster). Sets carry only.

**Wrapper hit path** (`boss_policy_move.asm:3709`):
- Reads `wBossAIPublicEnemyFasterCache` (0 = not faster, 1 = faster).
- Skips the whole body — no GetBaseData calls.
- `wBaseStats` unchanged (matches original's net effect of zero).
- `wCurSpecies` unchanged (matches original).
- Returns: carry derived from cached bit. ✓

**Delta:** none of consequence. The original temporarily clobbered
`wBaseStats` mid-call but restored it; the cache skips the temporary
clobber entirely.

**Callers:** `boss_policy_move.asm` `.ScoreMove .check_type_tempo` and
the `EFFECT_PRIORITY_HIT` branch. Both read carry only (`jr c/nc`),
ignore `a` and `wBaseStats` after the call. Verified. ✓

**Verdict:** behavior identical. No fix needed.

## Cache 2: `.GetProjectionDepth`

**Original body** (`boss_policy_move.asm:5763`):
- Reads `wBossAITier`. Returns `a` = 0 (early) / `HORIZON_MID-1` (mid) /
  `HORIZON_LATE-1` (late).
- No memory writes. No flag-state contract for callers (all callers
  immediately do `and a` or pass `a` to `.AddDownsideByA` / `.AddUpsideByA`
  which both start with `and a`).

**Wrapper hit path:**
- Reads `wBossAILookaheadDepthCache`. Returns `a` = cached depth.
- Identical return value. No memory writes other than the cache (which
  was already populated on first call).

**Delta:** none.

**Callers:** `BossAI_ApplyMultiTurnProjection`, 8 invocations. All
consume `a` immediately; none depend on exit flags. ✓

**Verdict:** behavior identical. No fix needed.

## Cache 3: `BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem`

**Original body** (`boss_platform.asm:628 *Uncached`):
- `push bc` and `push af` (hBattleTurn snapshot).
- Temporarily sets `hBattleTurn = 1` for the matchup walk.
- Calls `BossAI_CheckTypeMatchupNoItem` which:
  - Writes `wTypeMatchup` (the primary output).
  - Reads `BATTLE_VARS_SUBSTATUS1_OPP` (for SUBSTATUS_IDENTIFIED on Ghost
    type immunity).
  - Uses the HRAM math UNION (Multiply / Divide) — clobbers
    `hMultiplicand / hMultiplier / hDividend / hQuotient` as scratch.
- Restores hBattleTurn, pops bc, returns.
- Net side effect: `wTypeMatchup` written (primary output). HRAM math
  UNION clobbered (scratch).

**Wrapper hit path** (`boss_platform.asm:602`):
- Reads `wEnemyMoveStruct + MOVE_TYPE` as cache key.
- On match: writes cached value to `wTypeMatchup`, returns. HRAM math
  UNION NOT clobbered.

**Delta:** HRAM math UNION is left alone on hit. Original clobbered it.

**Is this a problem?** No. The HRAM math UNION is general-purpose scratch
(documented in `macros/ram.asm:35`). Callers that use it set their own
values before reading (the `hMultiplicand=x; hMultiplier=y; call Multiply;
read hQuotient` idiom). No caller of `BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem`
relies on it being clobbered as a side effect. The cache preserves MORE
state than the uncached — safer direction.

**Callers** (all read `wTypeMatchup` after the call, never trust `a`):
- `.ScoreMove .check_type_tempo` (line 315)
- `.ScoreMove` before `BossAI_ApplyDamageDominanceBias` (line 389)
- `.DamagingMoveBlockedByTypeImmunity` (line 444)
- `BossAI_CurrentEnemyMovePressureScore .type_matchup` (line 3395)

Verified each: reads `wTypeMatchup` then branches. ✓

**Sub-key correctness:** key is MOVE_TYPE only. Player types
(wBattleMonType1/2) and SUBSTATUS_IDENTIFIED are turn-stable; reset
clears the cache at every AI tick. Two moves with the same type get the
same (correct) matchup. ✓

**Verdict:** behavior identical. No fix needed.

## Cache 4: `BossAI_ShouldScout`

**Original body** (`boss_policy_move.asm:6259`):
- Calls 5 prereqs in order: IsActiveSpeciesScouted /
  GetPrimaryThreatType / GetTypeThreatSeverityVsEnemyMon / HasAnyKOMove /
  GetScoutRollThreshold.
- `GetTypeThreatSeverityVsEnemyMon` has a side-effect write to
  `wTypeMatchup` (it calls `BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem`
  internally).
- `HasAnyKOMove` is itself cached; on its first call this turn it may
  write `wTypeMatchup` as a sub-side-effect too.
- Calls `Random` for the scout-probability roll.
- Returns: carry set (scout) or clear (no scout). Trace block writes
  `wBossAITraceRiskFlags` bit 0 on the yes path when `BOSS_AI_TRACE`.

**Wrapper compute path:**
- Same prereqs, same Random call (RNG consumed identically).
- Captures `wTypeMatchup` after prereqs into
  `wBossAIShouldScoutMatchupValue`.
- Stores `wBossAIShouldScoutPrereqCache = 1` (passed).

**Wrapper hit path:**
- Writes cached `wBossAIShouldScoutMatchupValue` back to `wTypeMatchup`
  (PRESERVES the side effect — added in `44aa447c`).
- Calls `Random` (RNG consumed identically).
- Compares against cached threshold, returns same yes/no.
- Trace block fires identically (shared `.yes` path between compute and
  hit).

**Delta:** None on the visible state. RNG consumption preserved. Trace
flag preserved. `wTypeMatchup` preserved. Carry-flag return value
preserved.

**Failed-prereqs path:**
- Original: returns carry-clear immediately at any failed prereq.
- Wrapper: same, but stores `wBossAIShouldScoutPrereqCache = 0` first.
  Subsequent calls hit the "failed" cache and return carry-clear without
  re-running prereqs. RNG NOT consumed (matches original — Random only
  runs after prereqs pass).

**Sub-side-effect verification:** when prereqs fail in cache, does any
caller need the side effect of the helpers that DIDN'T run?
- `IsActiveSpeciesScouted`: read-only, no side effects.
- `GetPrimaryThreatType`: cached, no new side effects on miss path that
  the wrapper hides (helper writes its own cache; if that cache was
  $ff at first ShouldScout call, the helper has already populated it
  before ShouldScout's wrapper short-circuits subsequent calls).
- `GetTypeThreatSeverityVsEnemyMon`: writes `wTypeMatchup`. On
  failed-prereqs hit, wTypeMatchup is NOT written.
  - Is this a problem? Only if some caller relies on
    `BossAI_ShouldScout` having always-written-wTypeMatchup-on-the-fail-path
    behavior. Originally, on the fail path, wTypeMatchup MIGHT or might
    not have been written depending on WHICH prereq failed:
    - Fail at IsActiveSpeciesScouted (index 1): no wTypeMatchup write.
    - Fail at GetPrimaryThreatType (index 2): no wTypeMatchup write.
    - Fail at GetTypeThreatSeverityVsEnemyMon (index 3): wTypeMatchup
      WAS written, then severity check failed.
  - So even in the ORIGINAL, callers couldn't reliably assume
    wTypeMatchup was written after a fail. They don't (verified all 3
    callers above use only the carry flag).
  - Wrapper's "no wTypeMatchup write on cached-fail" matches the
    "fail at index 1 or 2" branch of the original. Indistinguishable to
    callers. ✓

**Callers:**
- `BossAI_ApplyScoutMoveBias` (line 5502): reads carry only.
- `BossAI_MaybeMarkScoutPivot` (line 6495): reads carry only.
- `BossAI_EvaluateActionLookahead .check_scout` (line 5590): reads
  carry only.

Verified each. ✓

**Verdict:** behavior identical. The matchup-preservation fix
(`44aa447c`) addresses the only side-effect divergence.

## Cross-cutting checks

### RNG state
Only `ShouldScout` consumes RNG. Wrapper rolls `Random` exactly once
per call (same as original). Failed prereqs don't roll (same as
original). Late-binding into the cache: the FIRST call this turn (compute
path) rolls one byte; SUBSEQUENT cached calls (hit path) ALSO roll one
byte. Same total RNG bytes consumed = same `Random` advances = same
downstream RNG-dependent decisions.

### Trace-build correctness
All four caches preserve their `BOSS_AI_TRACE` writes:
- PublicEnemyFaster: no trace block in original. ✓
- GetProjectionDepth: no trace block. ✓
- MatchupVsPlayer: no trace block. ✓
- ShouldScout: trace block fires identically on hit and compute (shared
  `.yes` path). ✓

### Cache reset coverage
`BossAI_ResetTurnCaches` (called at the top of `BossAI_ApplyMoveModel` AND
`BossAI_SwitchOrTryItem`) clears all 6 sentinels:
- `wBossAIPublicEnemyFasterCache`
- `wBossAILookaheadDepthCache`
- `wBossAILastMatchupType`
- `wBossAIShouldScoutPrereqCache` (matchup value not explicitly cleared;
  not needed since it's only read when prereq cache = 1, which only
  gets set AFTER matchup value is written; verified safe)

`BossAI_OracleHakiRead` does NOT call `BossAI_ResetTurnCaches`, but it
also doesn't invoke any of the four cached helpers — it operates on
score adjustments via `BossAI_ApplyKnownPlayerActionOracleBias` +
`BossAI_ChooseBestOracleMove`, neither of which uses type-matchup or
scout predicates. ✓

### Register clobber
Each wrapper's hit path has a STRICTER clobber profile than the
uncached body (less code → less clobbering). Where the uncached body
preserved `bc/de/hl` via push/pop, the hit path doesn't touch them at
all. Where the uncached body preserved `hBattleTurn`, the hit path
doesn't modify it. All callers' downstream behavior is preserved or
improved.

### Substatus / Foresight / dynamic-typing edge cases
The cache key for MatchupVsPlayer is MOVE_TYPE only. Substatus
(specifically SUBSTATUS_IDENTIFIED for Ghost vs Normal/Fighting) is
turn-stable during scoring (Foresight resolves in MOVE EXECUTION, not
in AI SCORING). Cache reset at each tick invalidates stale results.
Hidden Power isn't used by bosses. ✓

### Gym leader decisions
None of these caches change the decision graph:
- Same plan selection
- Same threat detection
- Same scout / KO / setup / status logic
- Same lookahead candidate set (early-out unchanged)
- Same RNG consumption → same random rolls landing the same way

A gym leader makes the IDENTICAL move on the IDENTICAL state. Just ~24%
fewer cycles to do it.

## Items not strictly needed but worth doing

### Item Q1: defensively reset `wBossAIShouldScoutMatchupValue` in `BossAI_ResetTurnCaches`

**Today:** the matchup-value byte is only READ on the hit path, which
only fires when `wBossAIShouldScoutPrereqCache = 1`. The cache is set
to 1 only AFTER the matchup byte is written. So the byte's pre-write
contents are never read. Safe today.

**Tomorrow risk:** if someone refactors and sets `prereq_cache = 1`
without first writing matchup_value, they'd read stale data. Defensive
reset costs 2 cycles per AI tick (4 in worst case across both
ApplyMoveModel + SwitchOrTryItem invocations) and 0 WRAM bytes.

**Recommend:** add it. Zero perf cost, prevents a future foot-gun.

### Item Q2: commit the regenerated `docs/generated/dev_index.md`

**Today:** my asm changes (added 7 WRAM bytes, added/changed several
functions) shift bank usage and the Tight-Banks figure. `v14` (regen)
PASSES at runtime, but the COMMITTED `dev_index.md` lags master's
source by one regen cycle.

**Risk:** anyone reading `docs/generated/dev_index.md` from master
without running the regen first sees a slightly stale picture. The
audits use the regenerated file, not the committed one, so they're
fine. Just a docs-source-of-truth thing.

**Recommend:** include the regenerated dev_index in a follow-up commit.

## Speedup-vs-quality summary

| Cache | Speed gain (per turn) | Quality impact | Fix shipped |
| --- | --- | --- | --- |
| PublicEnemyFaster | ~30k cycles | None | n/a |
| GetProjectionDepth | ~500 cycles | None | n/a |
| MatchupVsPlayer | ~900k cycles | None (HRAM math left alone, but no caller depends on its clobber) | n/a |
| ShouldScout | ~600k cycles | Side effect now preserved | `44aa447c` |

Total: ~1.5M cycles saved per LATE-tier turn (≈24%). Zero changes to
boss decision logic. All audits green.
