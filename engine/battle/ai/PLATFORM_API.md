# Boss AI Platform API

Status: current BOSSAI-003 platform/policy split, documented 2026-05-08.

The rebuild decision is to keep the current platform and formalize the simpler
public-info policy already present in `boss.asm`. Policy code may call the
functions below. New policy code should not read hidden player party, moves,
items, input, or menu state directly; `tools/audit/check_boss_ai_no_cheat.py`
guards that boundary.

## Entry Gates

Every public Boss AI entrypoint starts with:

```asm
ld a, [wBossAITier]
and a
ret z
```

`tools/audit/check_boss_ai_gating.py` enforces the guarded entrypoint list.

## Platform State Tracking

- `BossAI_IncrementTurnsElapsed`
- `BossAI_RecordPlayerSwitch`
- `BossAI_RecordPlayerSpecies`
- `BossAI_RecordPlayerFaint`
- `BossAI_RecordRevealedPlayerMove`
- `BossAI_LoadPlayerUsedMovesForActiveSpecies`
- `BossAI_MirrorPlayerUsedMovesToSpeciesSlot`

These functions maintain only public battle memory: seen species, alive seen
slots, revealed moves, per-species revealed-move bitmaps, turn count, and switch
count.

## Public Move And Type Helpers

- `BossAI_GetActiveSpeciesRevealedMaskPointer`
- `BossAI_GetActiveSpeciesUsedMovesPointer`
- `BossAI_GetMoveAttr`
- `BossAI_GetMoveByte`
- `BossAI_AddRevealedMoveToSpeciesMask`
- `BossAI_CheckTypeMatchupNoItem`
- `BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem`
- `BossAI_CheckPlayerMoveTypeMatchupVsBaseNoItem`
- `BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem`

These helpers read move tables and public type data. They are the allowed route
for policy code that needs type matchup information.

## Public Threat Model

- `BossAI_ComputePlayerPlausibleTypeMask`
- `BossAI_AddPublicSTABThreatsToMask`
- `BossAI_AddRevealedDamagingTypesToMask`
- `BossAI_AddSpeciesAndPreEvolutionMovesToMask`
- `BossAI_GetPrimaryThreatType`
- `BossAI_PlayerHasPublicThreatVsEnemy`
- `BossAI_HasRevealedSuperEffectiveMove`

This is the current implementation of public probabilistic threat reasoning.
It uses visible species, revealed moves, level-up/TM/HM/egg public learnability,
and known type data. It must not inspect private moveslots.

## Policy Surface

These functions are policy decisions, not platform:

- `BossAI_ApplyMoveModel`
- `BossAI_SelectMove`
- `BossAI_TrySwitch`
- `BossAI_SelectPlanIfNeeded`
- `BossAI_ApplyLookaheadToTopMoveCandidates`
- `BossAI_EvaluateActionLookahead`
- `BossAI_PredictPlayerSwitch`
- `BossAI_RefineSwitchCandidateForPlausibleRisk`
- `BossAI_ApplyPlanMoveBias`
- `BossAI_ApplyScoutMoveBias`
- `BossAI_ApplyRepeatPenalty`

Changes here require the Boss AI audit set:

```powershell
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_boss_ai_index_lines.py
```

## Trace Surface

The trace build records top moves, chosen move, plan id, plan confidence,
plausible threat masks, risk flags, lookahead bonuses, and switch context.
Trace code is diagnostic only; it must not become policy input.
