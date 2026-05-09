# Boss AI Logic Micro-Index

Use this when the task asks about *what the Boss AI does or where it lives in
source*: scoring, switching, item use, memory, plausible-move inference,
plan/role logic, lookahead, tier ramping, or any "where in `boss.asm` is the
X behavior" question.

This is a routing table over the AI source. It is not the design spec. For
*intent and rules*, read `docs/boss_ai_spec.md`. For *current implemented
behavior*, read `docs/boss_ai_post_patch_notes.md`. For *live capture / trace
proof*, use `docs/agent_navigation/subsystems/boss_ai_trace.md`. For *which
trainers run boss AI at all*, use
`docs/agent_navigation/subsystems/trainer_boss_roster.md`.

Avoid grepping `engine/` cold. Pick the right row below first.

## Pitfalls (read before editing boss AI source)

- `callfar` / `farcall` destroys caller's `hl` before the target runs. If a
  Boss AI helper takes `hl` as input, it must be called via a ROM0 homecall
  thunk (precedent: `SpeciesItemBoost_Far`,
  `ApplyLateGenDamageStatsItemMods_Far` in `home/battle.asm`).
- Boss AI is gated by `wBossAITier != 0`. When tier is 0, the overlay must
  do nothing — vanilla AI behavior must remain bit-identical. Anything that
  fires unconditionally is a bug.
- No private-info reads outside the spent Haki branch. The AI may only read
  what the player has revealed: sent out, used a move, KO'd, or what the
  public type chart implies. `tools/audit/check_boss_ai_no_cheat.py` is the
  verification floor.
- WRAM reserve is **140 bytes hard** (`ram/wram.asm:2582`). Adding fields
  requires checking `Boss AI WRAM Reserve` in `docs/generated/dev_index.md`
  AND running `tools/audit/check_boss_ai_memory_budget.py`.
- Score saturation: scores ≥79 are treated as "blocked" by `SelectMove`
  (saturated by `BossAI_DiscourageScoreHL`). Adding a further "discourage"
  pass expecting it to push a move below other already-discouraged moves
  will be a no-op. See commit `542ef2e2` for the saturation patch.
- Line numbers in this index are hand-maintained. After a non-trivial
  `boss.asm` edit, re-grep the labels you're using before trusting them,
  or run `tools/audit/check_boss_ai_index_lines.py`.
- LATE-tier visible per-turn lag was a known issue: not bloat in any one
  heuristic, but the same yes/no questions answered many times per turn from
  inside the lookahead loop. **Phase 1 shipped (commit `476b8087`)** —
  per-tick
  memoization of `HasAnyKOMove`, `PlayerHasPublicThreatVsEnemy`,
  `PlayerHasRevealedPriorityThreat`, `GetPrimaryThreatType` (4 cache bytes
  inside the existing WRAM reserve, reset at `ApplyMoveModel` and
  `SwitchOrTryItem` entry). Two dead trampolines deleted at the same time
  (`.ApplyLegacyRoleBiasIfNeeded`, `.IsSetupMove`). To make room in the
  bank for the wrappers, `BossAI_TraceTopMoves` was lifted to its own
  SECTION (`engine/battle/ai/boss_trace_topmoves.asm`) and `scoring.asm`
  was lifted to its own `AI Scoring` SECTION; `boss.asm` reaches
  `AICompareSpeed` via `farcall` now.

## Performance hot path (audited 2026-05-02)

`BossAI_SelectMove` calls `BossAI_ApplyLookaheadToTopMoveCandidates`, which
calls `BossAI_EvaluateActionLookahead` up to `BOSS_AI_LOOKAHEAD_N = 4` times
per turn. Each Evaluate calls `BossAI_ApplyMultiTurnProjection` once. Several
heavy helpers are called repeatedly across this fan-out with stable answers
inside one move-pick tick — they should be memoized once per
`BossAI_SelectMove` entry, not removed.

| Helper | File:line | Per-turn calls at LATE | Cost per call | Cache scope |
| --- | --- | --- | --- | --- |
| `BossAI_HasAnyKOMove` | `boss.asm:4283` | up to 16 (3-4 per Evaluate × 4) | scans 4 enemy moves, each → `BossAI_CheckTypeMatchupNoItem` (full type-chart walk in far bank) | one `SelectMove` tick |
| `BossAI_PlayerHasPublicThreatVsEnemy` | `boss.asm:2773` | ~20+ (`.EnemyUnderPressure` callers + Spikes layers + `PredictPlayerSwitch`) | walks 4 used-moves + type chart + revealed mask | one `ApplyMoveModel` pass |
| `BossAI_PlayerHasRevealedPriorityThreat` | `boss.asm:2864` | ~20+ (same shape) | walks 4 used-moves + type chart per priority hit | one `ApplyMoveModel` pass |
| `BossAI_PredictPlayerSwitch` | `boss.asm:4125` | ~7 (Mercy refusal, Choice regret, 3× Spikes layers, Switch confidence, MultiTurn projection) | calls 2 of the above | one `SelectMove` tick |
| `BossAI_GetPrimaryThreatType` | `boss.asm:6238` | ~8 (Evaluate `.check_reply` 6018 + MultiTurn `.check_threat` 6105, ×4) | walks revealed mask + per-type severity | one `SelectMove` tick |

Specific `HasAnyKOMove` call sites inside `BossAI_EvaluateActionLookahead`:
`.check_setup` 5972 (gated), `.check_reply` 6018 (always at MID+),
`.late_reply` 6035 (always at LATE), plus `MultiTurnProjection .check_threat`
6105. None of these inputs change between move-1 and move-4 of the same
evaluation pass — same answer, computed up to 4× per turn.

Two trivial dead trampolines also flagged for removal in the same pass:

- `.ApplyLegacyRoleBiasIfNeeded` at `boss.asm:2121-2122` — 2-line `jr` to
  `.ApplyRoleBias`, refactor leftover.
- `.IsSetupMove` at `boss.asm:2354-2355` — 1-line `jp` to
  `BossAI_IsCurrentEnemySetupMove`, no callers benefit from the wrapper.

Phase 1 shipped (no behavior change):

1. 4 cache bytes added inside the 140-byte `wBossAI*` reserve (post-shipping
   normal_used=104, normal_free=36; see `Boss AI WRAM Reserve` in
   `docs/generated/dev_index.md`).
2. `BossAI_ResetTurnCaches` clears all four sentinels at the top of
   `BossAI_ApplyMoveModel` and `BossAI_SwitchOrTryItem`; the four helpers
   each check their cache byte and only recompute on miss.
3. `PredictPlayerSwitch` was *not* wrapped — its two heavy internal calls
   are cached, so its per-call cost collapsed without a separate cache.
4. Same-tick correctness: every input the cached helpers read
   (`wPlayerUsedMoves`, the revealed mask, player HP bands, enemy moves,
   choice lock) is stable across one move-pick tick by construction.

Phase 2 (deferred, needs live-trace dump and gameplay-taste call):

- Per-class role branches `boss.asm:2150-2250` (`.falkner`, `.rival`,
  `.chuck`, …, `.champion`) and their effect tables `7324-7397`. Type-only
  encouragements (Chuck → Fighting, Bruno → Fighting, Koga → Poison/Bug)
  may shadow the engine's regular STAB/type-pressure path. Effect-table
  pushes (Pryce → Whirlwind, etc.) are doing distinct work. Don't touch
  without a trace dump on a known LATE battle.
- `MaybePickAdaptiveEnemyLead:165` not yet audited for dead branches.

## Source Files At A Glance

| File | Lines | Role |
| --- | --- | --- |
| `engine/battle/ai/boss.asm` | ~7500 | Boss AI overlay. All `BossAI_*` routines. Where almost every behavior question lands. |
| `engine/battle/ai/scoring.asm` | ~3230 | Base Gen 2 AI scoring layers (`AI_Basic`, `AI_Setup`, `AI_Types`, `AI_Offensive`, `AI_Smart`, `AI_Cautious`, `AI_Status`, `AI_Risky`). Boss AI runs on top of these. |
| `engine/battle/ai/switch.asm` | ~660 | Base switch helpers (`CheckPlayerMoveTypeMatchups`, `CheckAbleToSwitch`, `FindAliveEnemyMons*`, `FindEnemyMons*`). Boss switch logic calls into these. |
| `engine/battle/ai/items.asm` | ~860 | `AI_SwitchOrTryItem` dispatcher (`SwitchOften` / `SwitchRarely` / `SwitchSometimes`), `AI_TryItem`, `EnemyUsed*` item routines. Vanilla path — Boss AI hooks in via `BossAI_SwitchOrTryItem`. |
| `engine/battle/ai/move.asm` | ~220 | Move-pick dispatcher. Where `BossAI_ApplyMoveModel` and `BossAI_SelectMove` are called from. |
| `engine/battle/ai/redundant.asm` | ~200 | Move-redundancy avoidance helpers. |
| `data/battle/ai/*.asm` | small | Effect lists for the **vanilla** AI scoring layer (`useful_moves`, `stall_moves`, `risky_effects`, `residual_moves`, `encore_moves`, `status_only_effects`, `constant_damage_effects`, `reckless_moves`, `rain_dance_moves`, `sunny_day_moves`). Boss AI inherits their effect because vanilla scoring runs first, but consumers are in `scoring.asm`, not `boss.asm`. Boss AI's own effect tables are inline at the bottom of `boss.asm` (`BossAIDenyKOEffects`, `BossAIStatusEffects`, `BossAIRiskyEffects`, role-effect tables). |

## Activation And Per-Turn Hooks

The Boss AI is a strict additive layer on top of the vanilla AI. It only does
anything when `wBossAITier != 0`. Tier is set at battle start; per-turn hooks
fire from Battle Core.

| Where | What |
| --- | --- |
| `engine/battle/start_battle.asm:142` | `callfar ClearBossAIState` at battle entry. |
| `engine/battle/read_trainer_attributes.asm:70-138` | `ClearBossAIState`, sets `wBossAITier` and `wBossAITierWeightRow` from trainer attributes. |
| `engine/battle/core.asm:47` | `callfar MaybePickAdaptiveEnemyLead` — adaptive lead picker. |
| `engine/battle/core.asm:158` | `callfar BossAI_IncrementTurnsElapsed` — turn tick. |
| `engine/battle/core.asm:745` | `callfar BossAI_RecordPlayerSwitch`. |
| `engine/battle/core.asm:2668` | `callfar BossAI_RecordPlayerFaint`. |
| `engine/battle/core.asm:3954,3967` | `BossAI_LoadPlayerUsedMovesForActiveSpecies`, `BossAI_RecordPlayerSpecies`. |
| `engine/battle/ai/move.asm:115-117` | Main AI move dispatch: `callfar BossAI_ApplyMoveModel` then `callfar BossAI_SelectMove`; Boss pick is gated by `wBossAIMoveChoiceReady`. |

## Behavior → Source Map

All paths under `engine/battle/ai/boss.asm` unless noted.

### Data Ownership At A Glance

| Concern | Lives in |
| --- | --- |
| Vanilla AI effect lists (`useful_moves`, `risky_effects`, `stall_moves`, etc.) | `data/battle/ai/*.asm` (consumed by `engine/battle/ai/scoring.asm`) |
| Boss AI effect tables (`BossAIDenyKOEffects`, `BossAIStatusEffects`, `BossAIRiskyEffects`) | bottom of `engine/battle/ai/boss.asm` |
| Per-boss role-effect tables (`BossAIChuckRoleEffects` etc.) | bottom of `engine/battle/ai/boss.asm` |
| Per-trainer tier (class+id → EARLY/MID/LATE) | `BossAITierMap:1` in `data/trainers/ai_tiers.asm`; consumed by `LoadBossAITier:69` in `engine/battle/read_trainer_attributes.asm` |
| Per-class tier-weight-row override | `BossAITierRampMap:51` in `data/trainers/ai_tiers.asm` (default = `tier - 1`, set at `LoadBossAITier:97-98`) |
| Tier weight table (rows indexed by tier-weight-row) | `BossAITierWeights:7363` in `engine/battle/ai/boss.asm` |
| Plausible-threat type table | `BossAI_PlausibleThreatTypes:7330` in `engine/battle/ai/boss.asm` |
| Trainer attributes (base reward, AI flags) — separate concern, do not confuse with tier | `data/trainers/attributes.asm` (consumed at `engine/battle/read_trainer_attributes.asm:67`) |

### Memory: per-battle state record/access

| Need | Label / line |
| --- | --- |
| Reset boss state (battle start) | `ClearBossAIState` (`engine/battle/read_trainer_attributes.asm:138`) |
| Tick turn counter | `BossAI_IncrementTurnsElapsed:8` |
| Record opponent send-out | `BossAI_RecordPlayerSwitch:34`, `BossAI_RecordPlayerSpecies:46` |
| Record opponent KO | `BossAI_RecordPlayerFaint:94` |
| Public alive bitmap (per seen species) | `BossAI_SetSeenPlayerAliveBit:125`, `BossAI_ClearSeenPlayerAliveBit:135`, `BossAI_SeenPlayerSpeciesBitFromC:146` |
| Add a revealed move to memory | `BossAI_RecordRevealedPlayerMove:317`, `BossAI_AddRevealedMoveToSpeciesMask:452`, `BossAI_SetRevealedSpeciesMaskBit:483` |
| Switch cooldown | `BossAI_DecaySwitchCooldown:2700`, `BossAI_OnSwitchExecuted:2685` |

### Memory: per-species lookup

These read the per-seen-species memory in `wBossAIRevealedMovesBitmap` and
`wBossAISpeciesUsedMoves`. Six 4-byte revealed type masks (one per seen species
slot), plus a per-species mirror of `wPlayerUsedMoves`.

| Need | Label / line |
| --- | --- |
| Slot index for active species | `BossAI_GetActiveSpeciesSeenIndex:5120`, `BossAI_GetActiveSpeciesSeenBit:6668` |
| Pointer to active species' revealed-type mask | `BossAI_GetActiveSpeciesRevealedMaskPointer:340` |
| Load per-species used-moves into vanilla `wPlayerUsedMoves` | `BossAI_LoadPlayerUsedMovesForActiveSpecies:359` |
| Mirror current `wPlayerUsedMoves` back to species slot | `BossAI_MirrorPlayerUsedMovesToSpeciesSlot:386` |
| Pointer to active species' used-moves slot | `BossAI_GetActiveSpeciesUsedMovesPointer:402` |
| Test a bit in the revealed-species mask | `BossAI_TestRevealedSpeciesMaskBit:4326` |
| Check active species has revealed any super-effective move | `BossAI_HasRevealedSuperEffectiveMove:4262` |

### Adaptive lead pick

| Need | Label / line |
| --- | --- |
| Per-trainer adaptive lead | `MaybePickAdaptiveEnemyLead:165` |
| Internal helpers | `.ShouldUseAdaptiveLeadForTrainer:223`, `.FindFirstAliveOTMon:249`, `.FindNextAliveOTMon:277` |

### Plausible / likely move-type inference

The "what does the player likely have?" engine. Builds two 4-byte type masks:
plausible (could exist) and likely (high evidence weight). Cached in WRAM
keyed on species + level.

| Need | Label / line |
| --- | --- |
| Build mask for current player active | `BossAI_ComputePlayerPlausibleTypeMask:5171` |
| Public STAB seed | `BossAI_AddPublicSTABThreatsToMask:5212` |
| Wipe cache | `BossAI_ClearPlausibleMask:5225` |
| Add revealed damaging types | `BossAI_AddRevealedDamagingTypesToMask:5240` |
| Add a single move id (plausible / likely) | `BossAI_AddMoveIdToPlausibleMask:5268`, `BossAI_AddMoveIdToLikelyMask:5298` |
| Set bit by type id | `BossAI_SetPlausibleAndLikelyMaskBit:5328`, `BossAI_SetPlausibleMaskBit:5336`, `BossAI_SetLikelyMaskBit:5364` |
| Walk species + pre-evolutions | `BossAI_AddSpeciesAndPreEvolutionMovesToMask:5392`, `BossAI_LoadPublicThreatSourceSpecies:5422`, `BossAI_AdvanceToPreEvolutionThreatSource:5447` |
| Per-source contribution | `BossAI_AddCurrentSpeciesSpeculativeMoveThreats:5429`, `BossAI_AddCurrentSpeciesLikelyMoveThreats:5438` |
| Move-source pools | `BossAI_AddBaseTMHMMovesToMask:5456`, `BossAI_AddSpeciesLevelUpMovesToMask:5490`, `BossAI_AddSpeciesLevelUpMovesToLikelyMask:5547`, `BossAI_AddSpeciesEggMovesToMask:5604` |
| Test bits | `BossAI_TestPlausibleMaskBit:5628`, `BossAI_TestLikelyMaskBit:5660` |
| Risk weight per tier | `BossAI_GetTierPlausibleRiskWeight:6628`, `BossAI_GetSpeculativePlausibleRiskWeight:6641` |
| Static type tables | `BossAI_PlausibleThreatTypes:7330`, `BossAIHiddenPowerThreatTypes:7351` |

### Move scoring overlay (`BossAI_ApplyMoveModel`)

Runs after the vanilla AI layers. Walks `wEnemyMonMoves`, scores each, writes
to `wEnemyAIMoveScores`. ~1830 lines of gates and adjustments, organized as
local labels under `BossAI_ApplyMoveModel`. To find a specific gate:

```
rg -n "^\.[A-Za-z]" engine/battle/ai/boss.asm | sed -n '1,200p'
```

Top-level entry and named scoring helpers:

| Need | Label / line |
| --- | --- |
| Outer entry | `BossAI_ApplyMoveModel:544` |
| Score read/write helpers | `BossAI_LoadScorePointer:5808`, `BossAI_SetScoreHL:5818`, `BossAI_EncourageScoreHL:5824`, `BossAI_DiscourageScoreHL:5839` |
| Apply signed delta | `BossAI_ApplySignedDeltaToScore:5957` |
| Plan-driven move bias | `BossAI_ApplyPlanMoveBias:5698` |
| Scout-pivot move bias | `BossAI_ApplyScoutMoveBias:5761` |
| Repeat-move penalty | `BossAI_ApplyRepeatPenalty:5781` |
| Save / restore enemy move struct (so scoring can probe other moves non-destructively) | `BossAI_SaveEnemyMoveStruct:4464`, `BossAI_RestoreEnemyMoveStruct:4478` |

Public-failure gates inside `ApplyMoveModel` (search by local label):

- `.UtilityMoveWouldFailPublicly:788` — Substitute, Light Screen, Reflect, Protect, Disable, Encore, Mean Look, Dream Eater, Nightmare, Rain/Sunny Day with weather already up.
- `.StatusMoveWouldFailPublicly:768` — already-statused target, Safeguard, etc.
- `.DarkShieldBlocksStatusEffect:928`, `.DarkShieldBlocksUtilityEffect:944` — full-Dark player passive shield gating.
- `.EnemyStatusMoveTypeMissesPlayer:1013` — Thunder Wave into Ground, Glare into Ghost, Toxic into Poison/Steel.
- `.HeldItemMoveBlocked:711`, `.AssaultVestBlocksCurrentMove:738` — own held-item legality.

For the full current behavior list (one-line each, with rationale), read
`docs/boss_ai_post_patch_notes.md` § *Implemented Patch Summary*.

### Move pick (`BossAI_SelectMove`)

| Need | Label / line |
| --- | --- |
| Pick best vs. second-best, weighted dice on score gap | `BossAI_SelectMove:2394` |
| Trace top-3 moves and scores | `BossAI_TraceTopMoves` in `engine/battle/ai/boss_trace_topmoves.asm` (own SECTION; called via `farcall` from `BossAI_SelectMove`) |

Dice contract (comment at `boss.asm:2487-2491`): gap ≥6 → 90% best, gap ≥3 →
75% best, else 60% best. 79+ scores are treated as "blocked" (saturated by
`DiscourageScoreHL`).

### Pressure / KO scoring of own moves

| Need | Label / line |
| --- | --- |
| Does current move have KO pressure? | `BossAI_CurrentEnemyMoveHasKOPressure:3111` |
| Pressure score (0-N) | `BossAI_CurrentEnemyMovePressureScore:3145` |
| Public scored power | `BossAI_CurrentEnemyMoveScoredPower:3235` |
| Apply known modifiers | `BossAI_ApplyEnemyKnownPressureModifiers:3351`, `BossAI_ApplyEnemyHeldItemPressure:3358`, `BossAI_ApplyEnemyOffensivePassivePressure:3420`, `BossAI_ApplyPlayerDefensivePassivePressure:3454` |
| Has any KO move at all | `BossAI_HasAnyKOMove:4361` |

### Type matchup (no-item)

Used in places where item-modified type chart would leak hidden info.

| Need | Label / line |
| --- | --- |
| Player move vs. enemy active | `BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem:2949` |
| Player move vs. enemy bench (base) | `BossAI_CheckPlayerMoveTypeMatchupVsBaseNoItem:2965` |
| Enemy move vs. player active | `BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem:2981` |
| Generic | `BossAI_CheckTypeMatchupNoItem:2996` |
| Dragon's Majesty overlay | `BossAI_ApplyDragonsMajestyNoItem:3072` |
| Type contribution (per-type damage component) | `BossAI_PlayerTypeContribution:3620`, `BossAI_EnemyTypeContribution:3625`, `BossAI_TypeContributionAtHL:3629` |

### Switch decision

| Need | Label / line |
| --- | --- |
| Top-level switch / item dispatch | `BossAI_SwitchOrTryItem:2593` |
| Confidence dice | `BossAI_ComputeSwitchConfidence:4123` (margin-based 55/75/90% — comment at `:2641-2644`) |
| Threshold by tier | `BossAI_GetSwitchThreshold:3743` |
| Loop-prevention penalty | `BossAI_NeedsLoopPenalty:3823` |
| Predict opponent switch | `BossAI_PredictPlayerSwitch:4203` |
| Safe-to-switch check | `BossAI_CheckAbleToSwitchSafe:2709`, `BossAI_FindFirstAliveSwitchCandidate:2731` |
| Public faster check | `BossAI_PublicEnemyFaster:3672` |
| Vanilla switch helpers used | `engine/battle/ai/switch.asm` (`CheckPlayerMoveTypeMatchups:1`, `CheckAbleToSwitch:176`, `FindAliveEnemyMons*`) |

### Switch predicates / heuristics

These are the named "should we consider switching for reason X?" checks.
Adding new reasons usually means adding one of these alongside.

| Need | Label / line |
| --- | --- |
| Public threat vs. current active | `BossAI_PlayerHasPublicThreatVsEnemy:2773` |
| Revealed priority threat | `BossAI_PlayerHasRevealedPriorityThreat:2864` |
| Imminent KO prevention | `BossAI_IsImminentKOPrevention:3869` |
| Perish escape urgency | `BossAI_EnemyPerishEscapeUrgent:3883` |
| Bench revenge respect | `BossAI_ShouldRespectPotentialPlayerRevenge:3899` |
| Scarf-swing possible | `BossAI_IsScarfSwingPossible:3960` |
| Suspicious switch-in (coverage/pivot) | `BossAI_IsSuspiciousSwitchIn:3966` |
| Immunity-pivot opportunity | `BossAI_IsImmunityPivotOpportunity:4008` |
| Ace-timing hook | `BossAI_AceTimingHook:4077` |
| HP gating | `BossAI_EnemyBelowOneThirdHP:3510` |

### Switch-candidate risk refinement

The "OK we want to switch — which mon, accounting for plausible threats?"
layer.

| Need | Label / line |
| --- | --- |
| Refine candidate set | `BossAI_RefineSwitchCandidateForPlausibleRisk:6790` |
| Per-candidate risk score | `BossAI_ComputeSwitchCandidateRisk:6873` |
| Apply to confidence | `BossAI_ApplyPlausibleRiskToSwitchConfidence:7170` |
| Plan bias on switch | `BossAI_ApplyPlanSwitchBias:7223` |
| Sack-instead-of-switch | `BossAI_ShouldSackInsteadOfSwitch:7264` |
| Wincon protection | `BossAI_IsSwitchingIntoWinconRisk:7282` |
| Mark scout pivot | `BossAI_MaybeMarkScoutPivot:7312` |
| Public bench threat score | `BossAI_SeenBenchThreatScore:4498` |

### Held-item / Choice locking

| Need | Label / line |
| --- | --- |
| Get own held effect | `BossAI_GetEnemyHeldEffect:4429` |
| Currently Choice-locked? Which move? | `BossAI_EnemyChoiceLockedMove:4439`, `BossAI_IsChoiceHeldEffect:4455` |

### Plan / role / wincon

| Need | Label / line |
| --- | --- |
| Pick or refresh plan | `BossAI_SelectPlanIfNeeded:4590` |
| Find a party mon by role tag | `BossAI_FindPartyMonByRole:4772` |
| Per-boss role-bias dispatcher (reads `wTrainerClass`, jumps to per-boss branch) | `.ApplyRoleBias:2137` (under `BossAI_ApplyMoveModel`) |
| Per-boss scoring branches | `.falkner:2171`, `.rival:2163`, `.chuck:2185`, `.jasmine:2192`, `.pryce:2203`, `.clair:2212`, `.will:2219`, `.bruno:2226`, `.karen:2233`, `.koga:2240`, `.champion:2249` |
| Per-boss role-effect tables (consumed by the branches above) | `BossAIChuckRoleEffects:7402`, `BossAIJasmineRoleEffects:7409`, `BossAIPryceRoleEffects:7416`, `BossAIClairRoleEffects:7426`, `BossAIWillRoleEffects:7435`, `BossAIBrunoRoleEffects:7443`, `BossAIKarenRoleEffects:7450`, `BossAIKogaRoleEffects:7460`, `BossAIChampionRoleEffects:7469` |

### Effect classifiers

| Need | Label / line |
| --- | --- |
| Setup effect? | `BossAI_IsSetupEffect:4862`, `BossAI_IsCurrentEnemySetupMove:4889` |
| Status effect? | `BossAI_IsStatusEffect:5089` |
| Denial effect? | `BossAI_IsDenialEffect:5100` |
| Move category (phys/spec/status) | `BossAI_CurrentEnemyMoveCategory:3556` |
| Risky accuracy? | `BossAI_CurrentEnemyMoveAccuracyRisky:3575` |
| Dark-shield eligible? | `BossAI_CurrentMoveDarkShieldEligible:3600` |
| Ghost-type enemy? | `BossAI_EnemyIsGhostType:2374` |
| Species can evolve | `BossAI_EnemySpeciesCanEvolve:6592` |
| Known item nullifies threat type | `BossAI_EnemyKnownItemNullifiesThreatType:6570` |
| Static effect tables | `BossAIDenyKOEffects:7375`, `BossAIStatusEffects:7392`, `BossAIRiskyEffects:7477` |

### Lookahead / multi-turn projection

| Need | Label / line |
| --- | --- |
| Apply lookahead bonuses to top-N moves | `BossAI_ApplyLookaheadToTopMoveCandidates:5861` |
| Evaluate one action's lookahead | `BossAI_EvaluateActionLookahead:5987` |
| Multi-turn projection (tier-based future-discounted) | `BossAI_ApplyMultiTurnProjection:6137` |
| Clamp signed delta | `BossAI_ClampSignedLookaheadDelta:6290` |
| Threat type / severity probes | `BossAI_GetPrimaryThreatType:6316`, `BossAI_GetRevealedMoveThreatTypeAndSeverity:6479`, `BossAI_GetTypeThreatSeverityVsEnemyMon:6512`, `BossAI_AdjustThreatSeverityForEnemyKnownDefense:6540` |

### Tier ramp

| Need | Where |
| --- | --- |
| Tier value | `wBossAITier`, set in `engine/battle/read_trainer_attributes.asm:72,95` |
| Tier weight row | `wBossAITierWeightRow`, set at `read_trainer_attributes.asm:73,98,126` |
| Weight table | `BossAITierWeights:7363` (in `engine/battle/ai/boss.asm`) |
| Per-trainer tier ramp map | `BossAITierRampMap:51` in `data/trainers/ai_tiers.asm` (consumer: `read_trainer_attributes.asm:115`; design comment: `boss.asm:7056`) |
| Roll thresholds | `BossAI_GetScoutRollThreshold:6649`, `BossAI_GetTierPlausibleRiskWeight:6628` |

### Scout / repeat tracking

| Need | Label / line |
| --- | --- |
| Has active species been scouted? | `BossAI_IsActiveSpeciesScouted:6688` |
| Mark scouted | `BossAI_SetActiveSpeciesScouted:6702` |
| Decide to scout | `BossAI_ShouldScout:6712` |
| Same-move repeat counter | `BossAI_UpdateRepeatTracker:6745` |
| Mark scouted if scout move | `BossAI_MarkScoutedIfScoutMove:6764` |

### Helpers used everywhere

| Need | Label / line |
| --- | --- |
| Read move attribute / byte | `BossAI_GetMoveAttr:438`, `BossAI_GetMoveByte:447` |
| Decrement pressure / severity counters | `BossAI_DecPressureB:3502`, `BossAI_DecThreatSeverityB:6584` |

## Boss AI WRAM Block

Lives in WRAMX bank 1 because Battle Core touches it without bank-switching.
Total reserve: **140 bytes** (`ds 140 - (wBossAIStateEnd - wBossAITier)` at
`ram/wram.asm:2582`). Adding fields requires checking the *Boss AI WRAM
Reserve* line in `docs/generated/dev_index.md`. Cleared by `ClearBossAIState`
at battle start.

| Field | Bytes | Purpose |
| --- | --- | --- |
| `wBossAITier` | 1 | 0=off, EARLY/MID/LATE; gate for the entire overlay. |
| `wBossAIMoveChoiceReady` | 1 | Set by `SelectMove`; read in `engine/battle/ai/move.asm`. |
| `wBossAISwitchConfidence` | 1 | Output of `ComputeSwitchConfidence`. |
| `wBossAILastSwitchedOut` | 1 | Loop-prevention; checked by `NeedsLoopPenalty`. |
| `wBossAISwitchCooldown` | 1 | Decayed by `DecaySwitchCooldown`. |
| `wBossAIPlayerSwitchCount`, `wBossAIPendingPlayerSwitchCount` | 2 | Player switch tempo signal. |
| `wBossAITurnsElapsed` | 1 | Ticked at `core.asm:158`. |
| `wBossAIPlanId`, `wBossAIPlanPhase`, `wBossAIPlanConfidence` | 3 | Plan/role state. |
| `wBossAIWinconMonIdx`, `wBossAITargetMonIdx` | 2 | Wincon protection / target. |
| `wBossAIScoutedMask` | 1 | Per-slot scout bitmap. |
| `wBossAIRepeatCount`, `wBossAILastChosenMove` | 2 | Repeat-move tracker. |
| `wBossAIPlausibleTypeMaskSpecies`, `wBossAIPlausibleTypeMaskLevel` | 2 | Cache key. |
| `wBossAIPlausibleTypeMaskCache` | 4 | Plausible type bitmap (current player active). |
| `wBossAISeenPlayerSpeciesCount` | 1 | Number of seen player species (≤6). |
| `wBossAISeenPlayerSpecies` | `PARTY_LENGTH` | Seen-species ring. |
| `wBossAIRevealedMovesBitmap` | `PARTY_LENGTH * 4` | Per-seen-species revealed type masks. |
| `wBossAILikelyTypeMaskCache` | 4 | High-evidence type bitmap. |
| `wBossAISeenPlayerAliveMask` | 1 | Bit per seen species; cleared on faint. |
| `wBossAIRevealedMovesBitmapSpare` | 3 | Spare for future per-species growth. |
| `wBossAIScorePtr` | 2 | Current score-write pointer (used by `Encourage/DiscourageScoreHL`). |
| `wBossAISavedEnemyMoveStruct` | `MOVE_LENGTH` | Saved across non-destructive move probes. |
| `wBossAITemp..Temp5` | 5 | Scratch. |
| `wBossAITierWeightRow` | 1 | Row into `BossAITierWeights`; default = `wBossAITier - 1`, overridable per trainer. |
| `wBossAISpeciesUsedMoves` | `PARTY_LENGTH * NUM_MOVES` | Per-seen-species mirror of `wPlayerUsedMoves`; preserved across same-fight switches. |
| (under `BOSS_AI_TRACE`) | ~22 | Trace fields: top-3 moves/scores, chosen move, plan tracing, plausible mask snapshot, risk flags, lookahead bonuses. |

End marker: `wBossAIStateEnd::` at `ram/wram.asm:2580`.

## Audit Floor

Run before claiming Boss AI source work is done:

| Audit | Checks |
| --- | --- |
| `python tools\audit\check_boss_ai_no_cheat.py` | No private-info reads outside the spent Haki branch. |
| `python tools\audit\check_boss_ai_gating.py` | Boss AI is only active when tier > 0 and only on intended trainers. |
| `python tools\audit\check_boss_ai_memory_budget.py` | WRAM block fits its 140-byte reserve from `docs/generated/dev_index.md`. |
| `python tools\audit\check_boss_ai_trace_invariants.py` | Trace fields stay consistent with on-the-wire decision state. |
| `python tools\audit\check_boss_ai_live_capture_ledger.py` | Trace ledger / manifest cross-check (live proof side). |

If source bytes change, regenerate the dev index after a successful build:

```
python scripts/generate_dev_index.py --rom pokegold
```

## Cross-References

| Doc | When |
| --- | --- |
| `docs/boss_ai_spec.md` | Design intent, Haki contract, fairness gates. |
| `docs/boss_ai_post_patch_notes.md` | Current implemented behavior catalog (what each gate does, why). |
| `docs/boss_ai_bug_testing_plan.md` | Test scenarios and expected behaviors. |
| `docs/agent_navigation/subsystems/boss_ai_trace.md` | Live trace capture / proof workflow. |
| `docs/agent_navigation/subsystems/trainer_boss_roster.md` | Which trainers run boss AI; party labels. |
| `data/trainers/ai_tiers.asm`, `data/trainers/attributes.asm` | Tier assignment per class. |

## Verification Matrix

Use `docs/agent_navigation/verification_matrix.md` row **Boss AI logic** for
source-side changes. For docs-only changes here, use the navigation/docs row
instead — do not claim gameplay behavior changed from a doc edit.
