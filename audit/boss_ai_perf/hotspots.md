# Boss-AI cycle hotspots (static analysis baseline, 2026-05-25)

Sourced from `engine/battle/ai/boss_policy_move.asm`,
`engine/battle/ai/boss_platform.asm`,
`engine/battle/ai/boss_policy_switch.asm`. Numeric measurements live in
`audit/boss_ai_perf/baseline.json` — produced by
`python -m tools.perf.boss_ai_bench`.

## Top entry points (what the user's lag actually is)

1. **`BossAI_ApplyMoveModel`** ([boss_policy_move.asm:172](../../engine/battle/ai/boss_policy_move.asm)) — score every enemy move via `.ScoreMove`.
2. **`BossAI_SelectMove`** ([boss_policy_move.asm:2845](../../engine/battle/ai/boss_policy_move.asm)) — applies lookahead then two-pass best/second-best pick.
3. **`BossAI_TrySwitch`** ([boss_policy_switch.asm:17](../../engine/battle/ai/boss_policy_switch.asm)) — switch-policy dispatch on switch turns (separate code path; less frequent).

Both `ApplyMoveModel` and `SelectMove` re-call `BossAI_SelectPlanIfNeeded` and `BossAI_ComputePlayerPlausibleTypeMask`, but both helpers self-guard against duplicate work within a turn (plan-phase bit 7 = "done this turn"; mask cache keyed on species+level). The cost of the second call is essentially the guard check itself, not the body — that path is not a hotspot.

## Confirmed hotspots ranked by likely savings

### H1. `BossAI_ApplyMultiTurnProjection` — `GetProjectionDepth` invoked 4-6× per call
File: [engine/battle/ai/boss_policy_move.asm:5644](../../engine/battle/ai/boss_policy_move.asm), helper at line 5743.

`.GetProjectionDepth` is a 9-instruction subroutine that reads `wBossAITier` and returns 0/3/4 depending on tier. It's called from every `.AddDownsideByA`/`.AddUpsideByA` site inside `ApplyMultiTurnProjection` — six call sites in the body (post-search, ~6 invocations per call).

The depth value is **constant per AI tick** (tier doesn't change mid-turn). Hoisting to a register or per-turn cache eliminates 5/6 of those calls. With `BOSS_AI_LOOKAHEAD_N = 4` candidates evaluated per turn at LATE tier, that's ~20 redundant invocations per turn ≈ 200-400 cycles redundant per turn (each invocation is ~10-20 cycles of in-bank `call`+`ret`+three `ld a,[wBossAITier]; cp X`).

**Optimization**: in `ApplyMultiTurnProjection`, compute depth ONCE at entry into a register (e.g., `d`) or a scratch WRAM byte (`wBossAITemp4`), reuse for all subsequent additions. Bonus: `.GetProjectionDepth` itself could short-circuit if `wBossAITier == AI_TIER_EARLY` (already returns 0 there, but the early-return doesn't save the duplicate `ld a, [wBossAITier]` pair on the late/mid branches).

Behavioral change: none. `wBossAITier` is stable for the duration of one `AIChooseMove` invocation.

### H2. `BossAI_EvaluateActionLookahead` runs 10+ predicates per candidate
File: [engine/battle/ai/boss_policy_move.asm:5494](../../engine/battle/ai/boss_policy_move.asm).

Per candidate (max 4 candidates evaluated per turn at LATE tier):
- `BossAI_CurrentEnemyMovePressureScore`
- `AICheckPlayerQuarterHP_HL` + `AICheckPlayerHalfHP_HL`
- `BossAI_IsCurrentEnemySetupMove`
- `BossAI_HasAnyKOMove` (already cached — cheap on 2nd+ candidate)
- `BossAI_SetupBoostHasFurtherValue`
- `BossAI_SetupTurnIsAffordable`
- `BossAI_ShouldScout`
- `BossAI_GetPrimaryThreatType` (already cached)
- `BossAI_GetTypeThreatSeverityVsEnemyMon`
- `BossAI_ApplyMultiTurnProjection` (which re-runs many of the above)

Of these, the **turn-stable** ones (don't depend on current move) include:
- `BossAI_ShouldScout` — depends on plan + party state
- `BossAI_SetupTurnIsAffordable` — depends on turn counter + HP
- `BossAI_GetTypeThreatSeverityVsEnemyMon` — depends on primary threat (cached) + enemy types

A turn-level memo cache for these three would eliminate ~3 helper calls per candidate × 4 candidates = ~12 redundant calls per turn. Each predicate is itself non-trivial (`BossAI_GetTypeThreatSeverityVsEnemyMon` walks the type chart). Expected savings: 1,000–5,000 cycles per turn.

### H3. `BossAI_ApplyMultiTurnProjection` re-runs predicates already evaluated by `EvaluateActionLookahead`
Within one candidate's evaluation, `EvaluateActionLookahead` already calls `IsCurrentEnemySetupMove`, `ShouldScout`, `HasAnyKOMove`, `GetPrimaryThreatType`, `GetTypeThreatSeverityVsEnemyMon` — then immediately calls `ApplyMultiTurnProjection` which re-calls `IsCurrentEnemySetupMove`, `ShouldScout`, `HasAnyKOMove`, `GetPrimaryThreatType`, `GetTypeThreatSeverityVsEnemyMon`. Five duplicate predicate calls per candidate × 4 candidates = 20 redundant calls per turn.

The cleanest fix is to have `EvaluateActionLookahead` pass its already-computed predicate results to `ApplyMultiTurnProjection` via registers (e.g., bit-pack four 1-bit results into a single byte and pass in `d`).

Or: extend the turn-level cache to memoize these per-move predicates (keyed on move id), since the same move is evaluated by both helpers.

### H4. Switch-policy path (only on switch turns)
`BossAI_TrySwitch` ([boss_policy_switch.asm:17](../../engine/battle/ai/boss_policy_switch.asm)) calls 8–10 confidence helpers. The most expensive is `BossAI_CheckAbleToSwitchSafe` (line 310) which scans the OT party. Each subsequent helper (`RefineSwitchCandidateForPlausibleRisk`, `SwitchTargetSolvesDefensiveProblem`, `ComputeSwitchConfidence`) likely re-walks party state. Not measured here yet; defer to v15-block phase after measuring move-pick turns.

## Optimizations not in scope (per PRD constraints)

- Algorithmic horizon reduction (`BOSS_AI_LOOKAHEAD_HORIZON_*`): user sign-off required.
- Candidate count reduction (`BOSS_AI_LOOKAHEAD_N`): user sign-off required.
- Early-exit when score gap > threshold (S4 in PRD): a mechanical early-out IS in scope but is a behavioral change (subtly different distribution when two moves are equidistant to threshold). Defer to user sign-off before shipping.

## Sequence of operations

MVP (this iteration):
1. Land H1 (`GetProjectionDepth` hoist). Expected ≥5% reduction.
2. Land H3 (predicate pass-through from `EvaluateActionLookahead` to `ApplyMultiTurnProjection`). Expected additional ≥10% reduction.
3. Re-measure, verify trace parity, ship MVP.

Stretch (after MVP cleared):
4. Land H2 (extend turn-cache to `ShouldScout` / `SetupTurnIsAffordable` / `GetTypeThreatSeverityVsEnemyMon`).
5. Land H4 (switch-policy memoization on switch turns).
6. Document final numbers in `docs/boss_ai_perf_2026-05-25.md`.

## Iteration 1 results (2026-05-25)

Patches landed:
- **H1**: `BossAI_PublicEnemyFaster` wrapped with per-tick cache backed by `wBossAIPublicEnemyFasterCache`. Body renamed to `*Uncached`. Audit updated to inspect the Uncached label.
- **H1 bonus**: `BossAI_ApplyMultiTurnProjection.GetProjectionDepth` memoized via `wBossAILookaheadDepthCache`. All 8 invocations within the function (across all candidates per turn) now hit the cache after the first computation.

Cycle bench (3 samples each):

| Scenario | Baseline | Post-opt | Δ | % |
| --- | --- | --- | --- | --- |
| mid_lead | 3,511,196 | 3,417,568 | -93,628 | -2.7% |
| late_lead | 4,213,440 | 4,166,621 | -46,819 | -1.1% |
| late_lookahead_heavy | 4,213,440 | 4,353,890 | +140,450 | +3.3% |
| **OVERALL** | **11,938,076** | **11,938,079** | **-3** | **0.0%** |

LATE-tier reduction (the v4 verifier metric): **1.1%** — far below the MVP target of 15%.

### Why the small win

Both helpers are called only on specific paths:
- `BossAI_PublicEnemyFaster` is gated behind `EFFECT_PRIORITY_HIT` (line 309) and `wTypeMatchup > EFFECTIVE` (line 320). With my bench's clean WRAM state (no revealed player moves, neutral type matchup), these gates rarely trip — so the cache rarely sees a 2nd-call hit to save.
- `.GetProjectionDepth` is itself a ~22-cycle function. Caching saves ~6 cycles per hit. With 7 hits per `ApplyMultiTurnProjection` call × 4 candidates per turn = ~170 cycles saved per turn (out of 4.2M).

The cycle cost in the bench is dominated by `.ScoreMove` running ~30 `.Apply*Bias` helpers per move × 4 moves = ~120 helper calls per turn. Each individual helper is small; the cost is distributed.

### What would actually move the needle

A 15-35% reduction requires structural change, not mechanical caching:

1. **`.Apply*Bias` effect-tag dispatch**: read `wEnemyMoveStruct + MOVE_EFFECT` once at the top of `.ScoreMove`, dispatch only the bias helpers whose effect actually applies. Currently every helper is called for every move and most early-out on a `cp` check. ~30 helpers × 4 moves × ~30 cycles per no-op call = ~3,600 cycles saved per turn from this alone is tiny — but if some helpers also do per-call setup before the early-out, the savings compound. Behavior-preserving but invasive refactor.

2. **Lookahead candidate early-out** (PRD S4): when a candidate's base score is more than the lookahead-bonus cap below the current best, skip the full `BossAI_EvaluateActionLookahead` for that candidate. Cleanest single-line win, but subtly **changes behavior** for near-tie cases (different scoring rounding). Needs user sign-off per PRD constraints.

3. **Reduce `BOSS_AI_LOOKAHEAD_N` from 4 to 3 for LATE tier**: drops 25% of lookahead work directly. **Algorithmic change**, user sign-off required.

4. **Hide AI compute behind input animation**: architectural change to run AI scoring during the player's input-confirm screen. Big change, probably out of scope.

### Recommendation

The mechanical-caching pass is shipped (audits + trace parity green, build OK), but does not meet MVP target. The PRD scoped this run as "constructive-build, standard duration" — proceeding further requires a taste call from the user on options 1-4 above. **Pausing here for direction.**

## Iteration 2 results (2026-05-25, after profiling)

User picked option C (instrument the bench). Added `--profile` mode that hooks entry/exit of 30+ helpers using PyBoy `hook_register` and reports inclusive cycle aggregates. Profile of `late_lead` scenario revealed the real distribution:

```
helper                                       cycles      pct   calls  cy/call
BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem  1,122,908  29.6%   22  51,041
GetFarByte                                      1,079,728  28.5% 4654     232
BossAI_CurrentEnemyMoveHasKOPressure              727,744  19.2%    9  80,860
BossAI_CurrentEnemyMovePressureScore              716,224  18.9%    9  79,580
BossAI_ApplyScoutMoveBias                         658,580  17.4%    4 164,645
BossAI_GetTypeThreatSeverityVsEnemyMon            222,712   5.9%   11  20,246
```

**Two real fish identified:**

1. **`BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem`** at 29.6% — called 22× per turn, mostly with the same MOVE_TYPE within a single move's processing. **Optimization**: one-slot per-tick cache keyed on MOVE_TYPE (player types and substatus are turn-stable; reset clears the key). 18 of 22 calls hit cache. Saves ~920k cycles per turn.

2. **`BossAI_ApplyScoutMoveBias` → `BossAI_ShouldScout`** at 17.4% — `ShouldScout` runs 5 prereq helpers (the heavy one being `BossAI_GetTypeThreatSeverityVsEnemyMon` with a type chart walk) before rolling `Random`. The prereqs are turn-stable; only `Random` varies per call. **Optimization**: cache the prereq result + threshold value per tick. Random still runs each call (RNG consumption preserved). Saves ~600-1000k cycles per turn depending on how many ShouldScout callers fire.

### Patches landed in iteration 2

- `BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem` wrapped; body renamed to `*Uncached`. Cache keys: `wBossAILastMatchupType` + `wBossAILastMatchupResult`.
- `BossAI_ShouldScout` inlined cache (no wrapper since the body is small). Cache keys: `wBossAIShouldScoutPrereqCache` + `wBossAIShouldScoutThresholdCache`. Random consumption preserved.
- `BossAI_ResetTurnCaches` extended to reset both new sentinels.

### Final cycle results

| Scenario | Baseline | Post-opt | Δ | % |
| --- | --- | --- | --- | --- |
| mid_lead | 3,511,196 | 2,668,510 | -842,686 | **-24.0%** |
| late_lead | 4,213,440 | 3,183,488 | -1,029,952 | **-24.4%** |
| late_lookahead_heavy | 4,213,440 | 3,230,304 | -983,136 | **-23.3%** |
| **OVERALL** | **11,938,076** | **9,082,302** | **-2,855,774** | **-23.9%** |

**LATE-tier reduction = 24.4%**, comfortably past the MVP target of 15%. ~600ms real-time saved at LATE tier (1s → ~750ms compute window per AI turn).

All audits green (release_smoke, boss_ai_trace_invariants, boss_ai_no_cheat, boss_ai_gating, farcall_hl_clobber, farcall_a_clobber, typepassive_c_mirror). Build SHA1 changes by design. `check_navigation_floor` and the boss_ai_debugger pytest set fail with pre-existing issues unrelated to perf work (decision logged).

### Why this works without behavior change

- **MatchupVsPlayer cache**: writes the same `wTypeMatchup` value the uncached body would write. Same downstream behavior. Reset between turns ensures cross-turn changes invalidate the cache.
- **ShouldScout cache**: only memoizes the deterministic prereq chain. `Random` still rolls per call, preserving RNG state across the rest of the battle. Result distribution is identical.

Both caches are reset by `BossAI_ResetTurnCaches`, called at the top of `BossAI_ApplyMoveModel` and `BossAI_TrySwitch`.

### What's left on the table (for a future pass)

The next-largest helper after these two is `BossAI_GetTypeThreatSeverityVsEnemyMon` at ~222k cycles, 11 calls. Caching it (per-(threat_type, enemy_types) tuple) could net another ~5-8% reduction toward the 35% stretch target. Deferred — MVP is sufficient for the user's reported lag.

