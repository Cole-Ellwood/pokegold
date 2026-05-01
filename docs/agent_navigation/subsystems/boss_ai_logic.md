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

## Source Files At A Glance

| File | Lines | Role |
| --- | --- | --- |
| `engine/battle/ai/boss.asm` | ~6800 | Boss AI overlay. All `BossAI_*` routines. Where almost every behavior question lands. |
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

### Memory: per-battle state record/access

| Need | Label / line |
| --- | --- |
| Reset boss state (battle start) | `ClearBossAIState` (`engine/battle/read_trainer_attributes.asm:138`) |
| Tick turn counter | `BossAI_IncrementTurnsElapsed:1` |
| Record opponent send-out | `BossAI_RecordPlayerSwitch:26`, `BossAI_RecordPlayerSpecies:37` |
| Record opponent KO | `BossAI_RecordPlayerFaint:84` |
| Public alive bitmap (per seen species) | `BossAI_SetSeenPlayerAliveBit:114`, `BossAI_ClearSeenPlayerAliveBit:123`, `BossAI_SeenPlayerSpeciesBitFromC:133` |
| Add a revealed move to memory | `BossAI_RecordRevealedPlayerMove:290`, `BossAI_AddRevealedMoveToSpeciesMask:418`, `BossAI_SetRevealedSpeciesMaskBit:448` |
| Switch cooldown | `BossAI_DecaySwitchCooldown:2617`, `BossAI_OnSwitchExecuted:2603` |

### Memory: per-species lookup

These read the per-seen-species memory in `wBossAIRevealedMovesBitmap` and
`wBossAISpeciesUsedMoves`. Six 4-byte revealed type masks (one per seen species
slot), plus a per-species mirror of `wPlayerUsedMoves`.

| Need | Label / line |
| --- | --- |
| Slot index for active species | `BossAI_GetActiveSpeciesSeenIndex:4567`, `BossAI_GetActiveSpeciesSeenBit:5962` |
| Pointer to active species' revealed-type mask | `BossAI_GetActiveSpeciesRevealedMaskPointer:312` |
| Load per-species used-moves into vanilla `wPlayerUsedMoves` | `BossAI_LoadPlayerUsedMovesForActiveSpecies:330` |
| Mirror current `wPlayerUsedMoves` back to species slot | `BossAI_MirrorPlayerUsedMovesToSpeciesSlot:356` |
| Pointer to active species' used-moves slot | `BossAI_GetActiveSpeciesUsedMovesPointer:371` |
| Test a bit in the revealed-species mask | `BossAI_TestRevealedSpeciesMaskBit:4023` |
| Check active species has revealed any super-effective move | `BossAI_HasRevealedSuperEffectiveMove:3966` |

### Adaptive lead pick

| Need | Label / line |
| --- | --- |
| Per-trainer adaptive lead | `MaybePickAdaptiveEnemyLead:145` |
| Internal helpers | `.ShouldUseAdaptiveLeadForTrainer:203`, `.FindFirstAliveOTMon:229`, `.FindNextAliveOTMon:257` |

### Plausible / likely move-type inference

The "what does the player likely have?" engine. Builds two 4-byte type masks:
plausible (could exist) and likely (high evidence weight). Cached in WRAM
keyed on species + level.

| Need | Label / line |
| --- | --- |
| Build mask for current player active | `BossAI_ComputePlayerPlausibleTypeMask:4611` |
| Public STAB seed | `BossAI_AddPublicSTABThreatsToMask:4651` |
| Wipe cache | `BossAI_ClearPlausibleMask:4663` |
| Add revealed damaging types | `BossAI_AddRevealedDamagingTypesToMask:4677` |
| Add a single move id (plausible / likely) | `BossAI_AddMoveIdToPlausibleMask:4704`, `BossAI_AddMoveIdToLikelyMask:4733` |
| Set bit by type id | `BossAI_SetPlausibleAndLikelyMaskBit:4762`, `BossAI_SetPlausibleMaskBit:4769`, `BossAI_SetLikelyMaskBit:4796` |
| Walk species + pre-evolutions | `BossAI_AddSpeciesAndPreEvolutionMovesToMask:4823`, `BossAI_LoadPublicThreatSourceSpecies:4852`, `BossAI_AdvanceToPreEvolutionThreatSource:4874` |
| Per-source contribution | `BossAI_AddCurrentSpeciesSpeculativeMoveThreats:4858`, `BossAI_AddCurrentSpeciesLikelyMoveThreats:4866` |
| Move-source pools | `BossAI_AddBaseTMHMMovesToMask:4882`, `BossAI_AddSpeciesLevelUpMovesToMask:4915`, `BossAI_AddSpeciesLevelUpMovesToLikelyMask:4971`, `BossAI_AddSpeciesEggMovesToMask:5027` |
| Test bits | `BossAI_TestPlausibleMaskBit:5050`, `BossAI_TestLikelyMaskBit:5081` |
| Risk weight per tier | `BossAI_GetTierPlausibleRiskWeight:5931`, `BossAI_GetSpeculativePlausibleRiskWeight:5943` |
| Static type tables | `BossAI_PlausibleThreatTypes:6581`, `BossAIHiddenPowerThreatTypes:6601` |

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
| Outer entry | `BossAI_ApplyMoveModel:480` |
| Score read/write helpers | `BossAI_LoadScorePointer:5207`, `BossAI_SetScoreHL:5216`, `BossAI_EncourageScoreHL:5221`, `BossAI_DiscourageScoreHL:5235` |
| Apply signed delta | `BossAI_ApplySignedDeltaToScore:5345` |
| Plan-driven move bias | `BossAI_ApplyPlanMoveBias:5112` |
| Scout-pivot move bias | `BossAI_ApplyScoutMoveBias:5168` |
| Repeat-move penalty | `BossAI_ApplyRepeatPenalty:5187` |
| Save / restore enemy move struct (so scoring can probe other moves non-destructively) | `BossAI_SaveEnemyMoveStruct:4133`, `BossAI_RestoreEnemyMoveStruct:4146` |

Public-failure gates inside `ApplyMoveModel` (search by local label):

- `.UtilityMoveWouldFailPublicly:723` — Substitute, Light Screen, Reflect, Protect, Disable, Encore, Mean Look, Dream Eater, Nightmare, Rain/Sunny Day with weather already up.
- `.StatusMoveWouldFailPublicly:703` — already-statused target, Safeguard, etc.
- `.DarkShieldBlocksStatusEffect:863`, `.DarkShieldBlocksUtilityEffect:879` — full-Dark player passive shield gating.
- `.EnemyStatusMoveTypeMissesPlayer:948` — Thunder Wave into Ground, Glare into Ghost, Toxic into Poison/Steel.
- `.HeldItemMoveBlocked:646`, `.AssaultVestBlocksCurrentMove:673` — own held-item legality.

For the full current behavior list (one-line each, with rationale), read
`docs/boss_ai_post_patch_notes.md` § *Implemented Patch Summary*.

### Move pick (`BossAI_SelectMove`)

| Need | Label / line |
| --- | --- |
| Pick best vs. second-best, weighted dice on score gap | `BossAI_SelectMove:2321` |
| Trace top-3 moves and scores | `BossAI_TraceTopMoves:6609` |

Dice contract (comment at `boss.asm:2424-2428`): gap ≥6 → 90% best, gap ≥3 →
75% best, else 60% best. 79+ scores are treated as "blocked" (saturated by
`DiscourageScoreHL`).

### Pressure / KO scoring of own moves

| Need | Label / line |
| --- | --- |
| Does current move have KO pressure? | `BossAI_CurrentEnemyMoveHasKOPressure:2966` |
| Pressure score (0-N) | `BossAI_CurrentEnemyMovePressureScore:2999` |
| Public scored power | `BossAI_CurrentEnemyMoveScoredPower:3088` |
| Apply known modifiers | `BossAI_ApplyEnemyKnownPressureModifiers:3125`, `BossAI_ApplyEnemyHeldItemPressure:3131`, `BossAI_ApplyEnemyOffensivePassivePressure:3192`, `BossAI_ApplyPlayerDefensivePassivePressure:3225` |
| Has any KO move at all | `BossAI_HasAnyKOMove:4057` |

### Type matchup (no-item)

Used in places where item-modified type chart would leak hidden info.

| Need | Label / line |
| --- | --- |
| Player move vs. enemy active | `BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem:2815` |
| Player move vs. enemy bench (base) | `BossAI_CheckPlayerMoveTypeMatchupVsBaseNoItem:2830` |
| Enemy move vs. player active | `BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem:2845` |
| Generic | `BossAI_CheckTypeMatchupNoItem:2859` |
| Dragon's Majesty overlay | `BossAI_ApplyDragonsMajestyNoItem:2934` |
| Type contribution (per-type damage component) | `BossAI_PlayerTypeContribution:3379`, `BossAI_EnemyTypeContribution:3383`, `BossAI_TypeContributionAtHL:3386` |

### Switch decision

| Need | Label / line |
| --- | --- |
| Top-level switch / item dispatch | `BossAI_SwitchOrTryItem:2513` |
| Confidence dice | `BossAI_ComputeSwitchConfidence:3839` (margin-based 55/75/90% — comment at `:2571-2574`) |
| Threshold by tier | `BossAI_GetSwitchThreshold:3486` |
| Loop-prevention penalty | `BossAI_NeedsLoopPenalty:3565` |
| Predict opponent switch | `BossAI_PredictPlayerSwitch:3912` |
| Safe-to-switch check | `BossAI_CheckAbleToSwitchSafe:2625`, `BossAI_FindFirstAliveSwitchCandidate:2646` |
| Public faster check | `BossAI_PublicEnemyFaster:3422` |
| Vanilla switch helpers used | `engine/battle/ai/switch.asm` (`CheckPlayerMoveTypeMatchups:1`, `CheckAbleToSwitch:176`, `FindAliveEnemyMons*`) |

### Switch predicates / heuristics

These are the named "should we consider switching for reason X?" checks.
Adding new reasons usually means adding one of these alongside.

| Need | Label / line |
| --- | --- |
| Public threat vs. current active | `BossAI_PlayerHasPublicThreatVsEnemy:2681` |
| Revealed priority threat | `BossAI_PlayerHasRevealedPriorityThreat:2754` |
| Imminent KO prevention | `BossAI_IsImminentKOPrevention:3604` |
| Perish escape urgency | `BossAI_EnemyPerishEscapeUrgent:3617` |
| Bench revenge respect | `BossAI_ShouldRespectPotentialPlayerRevenge:3632` |
| Scarf-swing possible | `BossAI_IsScarfSwingPossible:3686` |
| Suspicious switch-in (coverage/pivot) | `BossAI_IsSuspiciousSwitchIn:3691` |
| Immunity-pivot opportunity | `BossAI_IsImmunityPivotOpportunity:3732` |
| Ace-timing hook | `BossAI_AceTimingHook:3794` |
| HP gating | `BossAI_EnemyBelowOneThirdHP:3279` |

### Switch-candidate risk refinement

The "OK we want to switch — which mon, accounting for plausible threats?"
layer.

| Need | Label / line |
| --- | --- |
| Refine candidate set | `BossAI_RefineSwitchCandidateForPlausibleRisk:6066` |
| Per-candidate risk score | `BossAI_ComputeSwitchCandidateRisk:6148` |
| Apply to confidence | `BossAI_ApplyPlausibleRiskToSwitchConfidence:6438` |
| Plan bias on switch | `BossAI_ApplyPlanSwitchBias:6490` |
| Sack-instead-of-switch | `BossAI_ShouldSackInsteadOfSwitch:6530` |
| Wincon protection | `BossAI_IsSwitchingIntoWinconRisk:6547` |
| Mark scout pivot | `BossAI_MaybeMarkScoutPivot:6570` |
| Public bench threat score | `BossAI_SeenBenchThreatScore:4159` |

### Held-item / Choice locking

| Need | Label / line |
| --- | --- |
| Get own held effect | `BossAI_GetEnemyHeldEffect:4101` |
| Currently Choice-locked? Which move? | `BossAI_EnemyChoiceLockedMove:4110`, `BossAI_IsChoiceHeldEffect:4125` |

### Plan / role / wincon

| Need | Label / line |
| --- | --- |
| Pick or refresh plan | `BossAI_SelectPlanIfNeeded:4244` |
| Find a party mon by role tag | `BossAI_FindPartyMonByRole:4419` |
| Per-boss role-bias dispatcher (reads `wTrainerClass`, jumps to per-boss branch) | `.ApplyRoleBias:2075` (under `BossAI_ApplyMoveModel`) |
| Per-boss scoring branches | `.falkner:2109`, `.rival:2101`, `.chuck:2123`, `.jasmine:2130`, `.pryce:2141`, `.clair:2150`, `.will:2157`, `.bruno:2164`, `.karen:2171`, `.koga:2178`, `.champion:2187` |
| Per-boss role-effect tables (consumed by the branches above) | `BossAIChuckRoleEffects:6729`, `BossAIJasmineRoleEffects:6735`, `BossAIPryceRoleEffects:6741`, `BossAIClairRoleEffects:6750`, `BossAIWillRoleEffects:6758`, `BossAIBrunoRoleEffects:6765`, `BossAIKarenRoleEffects:6771`, `BossAIKogaRoleEffects:6780`, `BossAIChampionRoleEffects:6788` |

### Effect classifiers

| Need | Label / line |
| --- | --- |
| Setup effect? | `BossAI_IsSetupEffect:4502`, `BossAI_IsCurrentEnemySetupMove:4528` |
| Status effect? | `BossAI_IsStatusEffect:4544` |
| Denial effect? | `BossAI_IsDenialEffect:4554` |
| Move category (phys/spec/status) | `BossAI_CurrentEnemyMoveCategory:3318` |
| Risky accuracy? | `BossAI_CurrentEnemyMoveAccuracyRisky:3336` |
| Dark-shield eligible? | `BossAI_CurrentMoveDarkShieldEligible:3360` |
| Ghost-type enemy? | `BossAI_EnemyIsGhostType:2308` |
| Species can evolve | `BossAI_EnemySpeciesCanEvolve:5902` |
| Known item nullifies threat type | `BossAI_EnemyKnownItemNullifiesThreatType:5882` |
| Static effect tables | `BossAIDenyKOEffects:6704`, `BossAIStatusEffects:6720`, `BossAIRiskyEffects:6795` |

### Lookahead / multi-turn projection

| Need | Label / line |
| --- | --- |
| Apply lookahead bonuses to top-N moves | `BossAI_ApplyLookaheadToTopMoveCandidates:5250` |
| Evaluate one action's lookahead | `BossAI_EvaluateActionLookahead:5368` |
| Multi-turn projection (tier-based future-discounted) | `BossAI_ApplyMultiTurnProjection:5496` |
| Clamp signed delta | `BossAI_ClampSignedLookaheadDelta:5642` |
| Threat type / severity probes | `BossAI_GetPrimaryThreatType:5661`, `BossAI_GetRevealedMoveThreatTypeAndSeverity:5794`, `BossAI_GetTypeThreatSeverityVsEnemyMon:5826`, `BossAI_AdjustThreatSeverityForEnemyKnownDefense:5853` |

### Tier ramp

| Need | Where |
| --- | --- |
| Tier value | `wBossAITier`, set in `engine/battle/read_trainer_attributes.asm:72,95` |
| Tier weight row | `wBossAITierWeightRow`, set at `read_trainer_attributes.asm:73,98,126` |
| Weight table | `BossAITierWeights:6693` (in `engine/battle/ai/boss.asm`) |
| Per-trainer tier ramp map | `BossAITierRampMap:51` in `data/trainers/ai_tiers.asm` (consumer: `read_trainer_attributes.asm:115`; design comment: `boss.asm:6696`) |
| Roll thresholds | `BossAI_GetScoutRollThreshold:5950`, `BossAI_GetTierPlausibleRiskWeight:5931` |

### Scout / repeat tracking

| Need | Label / line |
| --- | --- |
| Has active species been scouted? | `BossAI_IsActiveSpeciesScouted:5981` |
| Mark scouted | `BossAI_SetActiveSpeciesScouted:5994` |
| Decide to scout | `BossAI_ShouldScout:6003` |
| Same-move repeat counter | `BossAI_UpdateRepeatTracker:6029` |
| Mark scouted if scout move | `BossAI_MarkScoutedIfScoutMove:6047` |

### Helpers used everywhere

| Need | Label / line |
| --- | --- |
| Read move attribute / byte | `BossAI_GetMoveAttr:406`, `BossAI_GetMoveByte:414` |
| Decrement pressure / severity counters | `BossAI_DecPressureB:3272`, `BossAI_DecThreatSeverityB:5895` |

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
