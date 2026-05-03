# TD-004 — boss.asm split implementation plan

**Author:** Opus 4.7 (1M context) / branch `claude/nice-lamarr-f8a7e2`
**Drafted:** 2026-05-03
**Status:** PLAN ONLY. NOT claimed in AGENT_LOG. Execution requires user OK.
**Source recipe:** [tech_debt/FIX_PROPOSALS.md TD-004](../FIX_PROPOSALS.md) §242–323
**Bank-pressure baseline:** [tech_debt/TECH_DEBT_REPORT_ADDENDUM.md 2026-05-03](../TECH_DEBT_REPORT_ADDENDUM.md) (TD-001 re-eval)

---

## TL;DR

- `engine/battle/ai/boss.asm` is **7,006 lines, 152 top-level routines, 560 local labels**, all `:` (single colon, no `::` exports). It lives inside `SECTION "Enemy Trainers", ROMX` ([main.asm:168](../../main.asm:168)) alongside `engine/battle/ai/items.asm` and `engine/battle/read_trainer_attributes.asm`. Bank 0x0e.
- Plan: split into **6 thematic files + 1 retained dispatch file** (recipe proposed 5; this plan adds `boss_switch.asm`). All 7 files are INCLUDEd in the same `SECTION "Enemy Trainers"`. No `::` promotions are required because main.asm is one translation unit and `:` labels are visible to every other file in the unit.
- **Local-label scope is safe.** Zero cross-routine references via the explicit `OtherRoutine.localname` form (verified by grep). All 560 `.foo` labels are bound to their parent global label; moving a routine carries its locals intact.
- **Bank pressure is non-blocking.** Bank 0x0e has **568 free** post-TD-005 P1 + TD-007 (was 6 → 568 across the two recoveries). All split files stay in 0x0e. No relocation needed.
- **SHA1 will change** if files are thematically organised. The thematic-vs-slice trade-off is escalation #2 below.
- Effort: ~5-7 commits over 2-3 sessions (1 prep + 6 extract). Each step is verifiable in isolation.

## ESCALATIONS (taste calls — need user OK before execution)

1. **6 split files vs. 5.** Recipe proposed `boss_state / boss_typing / boss_scoring / boss_setup / boss_moves`. Switching logic (~27 routines, ~2 KB) has no clear home in those 5 — it would either bloat `boss_moves` or smear across several. Recommend adding `boss_switch.asm` as a 6th split file. Alternative: lump switch routines into `boss_moves.asm` (file gets ~7 KB, ~50 routines).
   - **Default if no answer: 6 split files.**

2. **SHA1: change once vs. preserve.** Thematic grouping requires reordering routines (their current line-order in boss.asm is not thematically clean — `BossAI_ApplyMoveModel` at line 495 is moves, then state/setup/typing/switch are interleaved). Two options:
   - **(2a) Thematic split** — routines moved into thematic files in any order. SHA1 changes once. Needs user playtest + `roms.sha1` / `dist/checksums.txt` refresh, same escalation pattern as TD-007.
   - **(2b) Pure-slice split** — split boss.asm by contiguous line ranges into files with names like `boss_lines_0001_0494.asm`. SHA1 unchanged. Defeats the refactor's purpose (no thematic grouping).
   - **Default if no answer: 2a (thematic).** Option 2b is offered only because the original recipe says "ROM SHA1 must be **identical** post-split" — that constraint is achievable only by surrendering thematic structure. The recipe's implicit assumption that thematic-and-byte-identical is simultaneously achievable is wrong.

3. **File-name prefix.** Recommend `boss_state.asm`, `boss_typing.asm`, etc. Keeps the `boss_` prefix that signals the subsystem in directory listings (matches existing `boss_trace_topmoves.asm`). Alternative: drop the prefix (`state.asm`, `typing.asm`) since they live in `engine/battle/ai/`. Recommend keeping the prefix.
   - **Default if no answer: keep `boss_` prefix.**

If you accept the three defaults, the next agent can execute the plan as written. If any default is overridden, the agent may need to revisit Mini-task 2 (file groupings) or Mini-task 5 (extraction order).

---

## Mini-task 1 — Inventory

All 152 top-level labels in `engine/battle/ai/boss.asm`. Every label is `:` (single colon, file-local-to-translation-unit); zero `::` exports. Byte size is **estimated** (lines × 2 B/line, the file's empirical density given 7,006 lines map to a ~12 KB section after items.asm). Exact byte sizes will come from `pokegold.map` post-build.

| # | Label | Lines | ~Bytes | Description |
|---|-------|------:|------:|-------------|
| 1 | `BossAI_IncrementTurnsElapsed` | 1–25 | 50 | Turn-tick: bumps elapsed-turns counter, decays switch cooldown, drains pending-switch count. |
| 2 | `BossAI_RecordPlayerSwitch` | 26–36 | 22 | Increments `wBossAIPendingPlayerSwitchCount` (saturated at 0xff). |
| 3 | `BossAI_RecordPlayerSpecies` | 37–83 | 94 | Records the active player species into `wBossAISeenPlayerSpecies`, dedup. |
| 4 | `BossAI_RecordPlayerFaint` | 84–113 | 60 | Marks the active player species as fainted in seen-species ledger. |
| 5 | `BossAI_SetSeenPlayerAliveBit` | 114–122 | 18 | Bit-helper: set "alive" bit for current seen-species index. |
| 6 | `BossAI_ClearSeenPlayerAliveBit` | 123–132 | 20 | Bit-helper: clear "alive" bit. |
| 7 | `BossAI_SeenPlayerSpeciesBitFromC` | 133–144 | 24 | Compute (seen-species byte, mask) for index in `c`. |
| 8 | `MaybePickAdaptiveEnemyLead` | 145–289 | 290 | Pre-battle: optionally swap enemy lead based on player-team threat profile. |
| 9 | `BossAI_RecordRevealedPlayerMove` | 290–311 | 44 | Per-turn: log a player move into the species-keyed revealed-moves bitmap. |
| 10 | `BossAI_GetActiveSpeciesRevealedMaskPointer` | 312–329 | 36 | Returns hl pointing at the revealed-moves mask byte for active species. |
| 11 | `BossAI_LoadPlayerUsedMovesForActiveSpecies` | 330–355 | 52 | Loads per-species used-moves bitmap into the per-turn cache. |
| 12 | `BossAI_MirrorPlayerUsedMovesToSpeciesSlot` | 356–370 | 30 | Writes per-turn used-moves cache back to species-keyed slot. |
| 13 | `BossAI_GetActiveSpeciesUsedMovesPointer` | 371–405 | 70 | Returns hl pointing at the per-species used-moves mask byte. |
| 14 | `BossAI_GetMoveAttr` | 406–413 | 16 | Reads a byte from a move's attribute table at offset `c`. (HOT — many internal callers) |
| 15 | `BossAI_GetMoveByte` | 414–417 | 8 | Get the move ID byte (offset 0). Tail of GetMoveAttr. |
| 16 | `BossAI_AddRevealedMoveToSpeciesMask` | 418–447 | 60 | Find the move's bit position and OR it into the species mask. |
| 17 | `BossAI_SetRevealedSpeciesMaskBit` | 448–479 | 64 | Set bit `b` of byte at hl in revealed-moves mask. |
| 18 | `BossAI_ResetTurnCaches` | 480–494 | 30 | Per-turn cache reset (used-moves, primary-threat, etc.). |
| 19 | `BossAI_ApplyMoveModel` | 495–2317 | 3646 | **GIANT.** Per-move scoring/risk model — the heart of the AI. ~30% of the file. |
| 20 | `BossAI_EnemyIsGhostType` | 2318–2330 | 26 | Type predicate: enemy mon has GHOST as type1 or type2. |
| 21 | `BossAI_SelectMove` | 2331–2522 | 384 | **Top-level entry.** Picks the best-scoring move; gates Boss pick via `wBossAIMoveChoiceReady`. Called from [engine/battle/ai/move.asm:116](../../engine/battle/ai/move.asm:116). |
| 22 | `BossAI_SwitchOrTryItem` | 2523–2613 | 182 | **Top-level entry.** Decides switch vs. AI_TryItem; threshold-vs-confidence with random margin. Called from items dispatcher. |
| 23 | `BossAI_OnSwitchExecuted` | 2614–2627 | 28 | Records `wBossAILastSwitchedOut` + sets cooldown. Called from [engine/battle/ai/items.asm:687](../../engine/battle/ai/items.asm:687). |
| 24 | `BossAI_DecaySwitchCooldown` | 2628–2635 | 16 | Decrement `wBossAISwitchCooldown` if non-zero. |
| 25 | `BossAI_CheckAbleToSwitchSafe` | 2636–2656 | 42 | Wrapper around `CheckAbleToSwitch` that respects cooldown + bench-alive count. |
| 26 | `BossAI_FindFirstAliveSwitchCandidate` | 2657–2691 | 70 | Find first non-fainted, non-active party member. |
| 27 | `BossAI_PlayerHasPublicThreatVsEnemy` | 2692–2707 | 32 | Cached: any revealed player move is super-effective vs. enemy. |
| 28 | `BossAI_PlayerHasPublicThreatVsEnemyUncached` | 2708–2780 | 146 | Uncached version; iterates revealed moves + checks type matchup. |
| 29 | `BossAI_PlayerHasRevealedPriorityThreat` | 2781–2796 | 32 | Cached: revealed priority move that hits enemy hard. |
| 30 | `BossAI_PlayerHasRevealedPriorityThreatUncached` | 2797–2857 | 122 | Uncached version. |
| 31 | `BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem` | 2858–2872 | 30 | Type matchup: player move vs. enemy mon, ignoring held items. |
| 32 | `BossAI_CheckPlayerMoveTypeMatchupVsBaseNoItem` | 2873–2887 | 30 | Type matchup: player move vs. enemy's base form. |
| 33 | `BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem` | 2888–2901 | 28 | Type matchup: enemy move vs. player mon. |
| 34 | `BossAI_CheckTypeMatchupNoItem` | 2902–2976 | 150 | Core type-matchup primitive: returns multiplier in `b`. |
| 35 | `BossAI_ApplyDragonsMajestyNoItem` | 2977–3008 | 64 | Special-case: Dragon's Majesty type chart override for matchup. |
| 36 | `BossAI_CurrentEnemyMoveHasKOPressure` | 3009–3041 | 66 | "Could this move plausibly KO?" predicate. |
| 37 | `BossAI_CurrentEnemyMovePressureScore` | 3042–3130 | 178 | Pressure scoring: power × matchup × modifiers → `b`. |
| 38 | `BossAI_CurrentEnemyMoveScoredPower` | 3131–3167 | 74 | Scaled effective power for the current enemy move. |
| 39 | `BossAI_ApplyEnemyKnownPressureModifiers` | 3168–3173 | 12 | Thunk that calls the three Apply*Pressure routines below. |
| 40 | `BossAI_ApplyEnemyHeldItemPressure` | 3174–3234 | 122 | Adjust pressure by enemy held item (Choice/Specs/Vest etc.). |
| 41 | `BossAI_ApplyEnemyOffensivePassivePressure` | 3235–3267 | 66 | Adjust pressure by enemy type-passive offensive mods. |
| 42 | `BossAI_ApplyPlayerDefensivePassivePressure` | 3268–3314 | 94 | Adjust pressure by player type-passive defensive mods. |
| 43 | `BossAI_DecPressureB` | 3315–3321 | 14 | Decrement `b` floored at 0. |
| 44 | `BossAI_EnemyBelowOneThirdHP` | 3322–3360 | 78 | HP threshold predicate: enemy current/max ≤ 1/3. |
| 45 | `BossAI_CurrentEnemyMoveCategory` | 3361–3378 | 36 | Returns physical/special/status for current enemy move. |
| 46 | `BossAI_CurrentEnemyMoveAccuracyRisky` | 3379–3402 | 48 | Accuracy < threshold predicate. |
| 47 | `BossAI_CurrentMoveDarkShieldEligible` | 3403–3421 | 38 | Predicate for Dark Shield held-item interactions. |
| 48 | `BossAI_PlayerTypeContribution` | 3422–3425 | 8 | Wrapper: type-contrib for player mon types. |
| 49 | `BossAI_EnemyTypeContribution` | 3426–3428 | 6 | Wrapper: type-contrib for enemy mon types. |
| 50 | `BossAI_TypeContributionAtHL` | 3429–3464 | 72 | Sum two-byte type-contribution values from a table at hl. |
| 51 | `BossAI_PublicEnemyFaster` | 3465–3528 | 128 | Public-info speed comparison: who outspeeds based on what's been seen. |
| 52 | `BossAI_GetSwitchThreshold` | 3529–3607 | 158 | Returns the confidence threshold for switching given tier + state. |
| 53 | `BossAI_NeedsLoopPenalty` | 3608–3646 | 78 | Anti-switch-loop heuristic; returns carry if penalty applies. |
| 54 | `BossAI_IsImminentKOPrevention` | 3647–3659 | 26 | Predicate: are we about to be KO'd next turn? |
| 55 | `BossAI_EnemyPerishEscapeUrgent` | 3660–3674 | 30 | Perish-song-induced switch urgency. |
| 56 | `BossAI_ShouldRespectPotentialPlayerRevenge` | 3675–3728 | 108 | Revenge-killer awareness: don't blindly stay in. |
| 57 | `BossAI_IsScarfSwingPossible` | 3729–3733 | 10 | Trivial wrapper. |
| 58 | `BossAI_IsSuspiciousSwitchIn` | 3734–3774 | 82 | Did the player just switch in something with surprising matchup? |
| 59 | `BossAI_IsImmunityPivotOpportunity` | 3775–3836 | 124 | Detect free pivot via type immunity. |
| 60 | `BossAI_AceTimingHook` | 3837–3881 | 90 | Ace-Pokémon-specific timing reveals. |
| 61 | `BossAI_ComputeSwitchConfidence` | 3882–3954 | 146 | Total confidence-to-switch score. |
| 62 | `BossAI_PredictPlayerSwitch` | 3955–4012 | 116 | Predict whether the player will switch this turn. |
| 63 | `BossAI_HasRevealedSuperEffectiveMove` | 4013–4069 | 114 | Per-species: any revealed move is super-effective vs. target. |
| 64 | `BossAI_TestRevealedSpeciesMaskBit` | 4070–4103 | 68 | Bit test on revealed-moves mask. |
| 65 | `BossAI_HasAnyKOMove` | 4104–4119 | 32 | Cached predicate: enemy has any KO move. |
| 66 | `BossAI_HasAnyKOMoveUncached` | 4120–4163 | 88 | Uncached version. |
| 67 | `BossAI_GetEnemyHeldEffect` | 4164–4172 | 18 | Read held-item effect for enemy mon. |
| 68 | `BossAI_EnemyChoiceLockedMove` | 4173–4187 | 30 | Returns currently-Choice-locked move slot. |
| 69 | `BossAI_IsChoiceHeldEffect` | 4188–4195 | 16 | Predicate on held-effect = Choice item. |
| 70 | `BossAI_SaveEnemyMoveStruct` | 4196–4208 | 26 | Save enemy current-move struct to scratch. |
| 71 | `BossAI_RestoreEnemyMoveStruct` | 4209–4221 | 26 | Restore from scratch. |
| 72 | `BossAI_SeenBenchThreatScore` | 4222–4306 | 170 | Threat score for the bench (non-active) seen species. |
| 73 | `BossAI_SelectPlanIfNeeded` | 4307–4481 | 350 | Plan-selection state machine: pivots between scout / boost / aggro / defend. |
| 74 | `BossAI_FindPartyMonByRole` | 4482–4564 | 166 | Pick party member matching a role tag (ace, scarfer, etc.). |
| 75 | `BossAI_IsSetupEffect` | 4565–4590 | 52 | Effect-id predicate: is this a setup move? |
| 76 | `BossAI_IsCurrentEnemySetupMove` | 4591–4606 | 32 | Wrapper using the current move's effect. |
| 77 | `BossAI_SetupBoostHasFurtherValue` | 4607–4761 | 310 | **Speed-cap rule (CLAUDE.md ref).** Per-stat-stage value gating for setup. |
| 78 | `BossAI_SetupTurnIsAffordable` | 4762–4787 | 52 | Affordability check (don't setup into incoming KO). |
| 79 | `BossAI_IsStatusEffect` | 4788–4797 | 20 | Effect-id predicate: is this a status move? |
| 80 | `BossAI_IsDenialEffect` | 4798–4810 | 26 | Effect-id predicate: is this a denial move (substitute, leech, protect)? |
| 81 | `BossAI_GetActiveSpeciesSeenIndex` | 4811–4854 | 88 | Index in `wBossAISeenPlayerSpecies` for the active player species. |
| 82 | `BossAI_ComputePlayerPlausibleTypeMask` | 4855–4894 | 80 | Build the plausible-types mask for the player mon. |
| 83 | `BossAI_AddPublicSTABThreatsToMask` | 4895–4906 | 24 | Add STAB types from public info to plausible mask. |
| 84 | `BossAI_ClearPlausibleMask` | 4907–4920 | 28 | Zero plausible + likely masks. |
| 85 | `BossAI_AddRevealedDamagingTypesToMask` | 4921–4947 | 54 | OR revealed damaging-move types into masks. |
| 86 | `BossAI_AddMoveIdToPlausibleMask` | 4948–4976 | 58 | Convert move-id → type → plausible bit. |
| 87 | `BossAI_AddMoveIdToLikelyMask` | 4977–5005 | 58 | Same, into likely mask. |
| 88 | `BossAI_SetPlausibleAndLikelyMaskBit` | 5006–5012 | 14 | Bit-set helper for both masks. |
| 89 | `BossAI_SetPlausibleMaskBit` | 5013–5039 | 54 | Bit-set helper. |
| 90 | `BossAI_SetLikelyMaskBit` | 5040–5066 | 54 | Bit-set helper. |
| 91 | `BossAI_AddSpeciesAndPreEvolutionMovesToMask` | 5067–5095 | 58 | Walk species + pre-evolution chain, add learnable moves. |
| 92 | `BossAI_LoadPublicThreatSourceSpecies` | 5096–5101 | 12 | Set up active species + pre-evolution iterator. |
| 93 | `BossAI_AddCurrentSpeciesSpeculativeMoveThreats` | 5102–5109 | 16 | Add current iterator species' speculative moves. |
| 94 | `BossAI_AddCurrentSpeciesLikelyMoveThreats` | 5110–5117 | 16 | Add current iterator species' likely moves. |
| 95 | `BossAI_AdvanceToPreEvolutionThreatSource` | 5118–5125 | 16 | Advance iterator to pre-evolution. |
| 96 | `BossAI_AddBaseTMHMMovesToMask` | 5126–5158 | 66 | Add the base-form's TM/HM-learnable moves. |
| 97 | `BossAI_AddSpeciesLevelUpMovesToMask` | 5159–5214 | 112 | Add level-up moves up to current level. |
| 98 | `BossAI_AddSpeciesLevelUpMovesToLikelyMask` | 5215–5270 | 112 | Same, but to likely mask only (more conservative). |
| 99 | `BossAI_AddSpeciesEggMovesToMask` | 5271–5293 | 46 | Add egg-move type bits. |
| 100 | `BossAI_TestPlausibleMaskBit` | 5294–5324 | 62 | Bit test on plausible mask. |
| 101 | `BossAI_TestLikelyMaskBit` | 5325–5355 | 62 | Bit test on likely mask. |
| 102 | `BossAI_ApplyPlanMoveBias` | 5356–5411 | 112 | Per-plan move-score bias (encourage/discourage). |
| 103 | `BossAI_ApplyScoutMoveBias` | 5412–5430 | 38 | Scout-mode-specific bias. |
| 104 | `BossAI_ApplyRepeatPenalty` | 5431–5450 | 40 | Penalty for picking the same move repeatedly. |
| 105 | `BossAI_LoadScorePointer` | 5451–5459 | 18 | Load hl = pointer to current move's score byte. |
| 106 | `BossAI_SetScoreHL` | 5460–5464 | 10 | Store `a` to score byte. |
| 107 | `BossAI_EncourageScoreHL` | 5465–5478 | 28 | Add a bias to score byte (saturating). (HOT) |
| 108 | `BossAI_DiscourageScoreHL` | 5479–5493 | 30 | Subtract a bias. (HOT) |
| 109 | `BossAI_ApplyLookaheadToTopMoveCandidates` | 5494–5588 | 190 | Multi-turn lookahead — score top-3 candidates. |
| 110 | `BossAI_ApplySignedDeltaToScore` | 5589–5611 | 46 | Apply signed delta to score with clamping. |
| 111 | `BossAI_EvaluateActionLookahead` | 5612–5760 | 298 | Single-step action lookahead (call/jump/recurse). |
| 112 | `BossAI_ApplyMultiTurnProjection` | 5761–5906 | 292 | Project N turns ahead, accumulate signed delta. |
| 113 | `BossAI_ClampSignedLookaheadDelta` | 5907–5925 | 38 | Clamp the signed lookahead delta. |
| 114 | `BossAI_GetPrimaryThreatType` | 5926–5947 | 44 | Cached: dominant threat type from public info. |
| 115 | `BossAI_GetPrimaryThreatTypeUncached` | 5948–6080 | 266 | Uncached version; walks revealed move set. |
| 116 | `BossAI_GetRevealedMoveThreatTypeAndSeverity` | 6081–6112 | 64 | Per-move (type, severity) extractor. |
| 117 | `BossAI_GetTypeThreatSeverityVsEnemyMon` | 6113–6139 | 54 | How dangerous is type-X attacking the enemy? |
| 118 | `BossAI_AdjustThreatSeverityForEnemyKnownDefense` | 6140–6168 | 58 | Adjust severity for known enemy defensive item. |
| 119 | `BossAI_EnemyKnownItemNullifiesThreatType` | 6169–6181 | 26 | Predicate: does the enemy's known item nullify type X? |
| 120 | `BossAI_DecThreatSeverityB` | 6182–6188 | 14 | Decrement `b` floored at 0. |
| 121 | `BossAI_EnemySpeciesCanEvolve` | 6189–6217 | 58 | Predicate: is the enemy mid-evolution-line? |
| 122 | `BossAI_GetTierPlausibleRiskWeight` | 6218–6229 | 24 | Per-tier risk-weight lookup. |
| 123 | `BossAI_GetSpeculativePlausibleRiskWeight` | 6230–6236 | 14 | Speculative weight (low-confidence moves). |
| 124 | `BossAI_GetScoutRollThreshold` | 6237–6248 | 24 | Scout-mode RNG threshold. |
| 125 | `BossAI_GetActiveSpeciesSeenBit` | 6249–6267 | 38 | Bit-helper for seen-species. |
| 126 | `BossAI_IsActiveSpeciesScouted` | 6268–6280 | 26 | Predicate. |
| 127 | `BossAI_SetActiveSpeciesScouted` | 6281–6289 | 18 | Bit-set. |
| 128 | `BossAI_ShouldScout` | 6290–6315 | 52 | Decision: is now a good scout opportunity? |
| 129 | `BossAI_UpdateRepeatTracker` | 6316–6333 | 36 | Update `wBossAILastMove*` family. |
| 130 | `BossAI_MarkScoutedIfScoutMove` | 6334–6352 | 38 | Mark scouted-bit if the chosen move was a scout. |
| 131 | `BossAI_RefineSwitchCandidateForPlausibleRisk` | 6353–6434 | 164 | Filter switch candidates by plausible-type risk. |
| 132 | `BossAI_ComputeSwitchCandidateRisk` | 6435–6724 | 580 | **Big.** Per-candidate risk score; main filter logic. |
| 133 | `BossAI_ApplyPlausibleRiskToSwitchConfidence` | 6725–6776 | 104 | Subtract plausible-risk from switch confidence. |
| 134 | `BossAI_ApplyPlanSwitchBias` | 6777–6816 | 80 | Plan-state-driven switch confidence bias. |
| 135 | `BossAI_ShouldSackInsteadOfSwitch` | 6817–6833 | 34 | Sack vs. switch decision. |
| 136 | `BossAI_IsSwitchingIntoWinconRisk` | 6834–6856 | 46 | Is the switch target itself a wincon-risk? |
| 137 | `BossAI_MaybeMarkScoutPivot` | 6857–6867 | 22 | Mark scouted-bit on a successful switch. |
| 138 | `BossAI_PlausibleThreatTypes` | 6868–6887 | 40 | **DATA TABLE.** All combat types in plausibility-iteration order. |
| 139 | `BossAIHiddenPowerThreatTypes` | 6888–6898 | 22 | **DATA TABLE.** Hidden-power-eligible types. |
| 140 | `BossAITierWeights` | 6899–6909 | 22 | **DATA TABLE.** 7-column weight rows per AI tier. |
| 141 | `BossAIDenyKOEffects` | 6910–6925 | 32 | **DATA TABLE.** Effects that deny KO outcomes. |
| 142 | `BossAIStatusEffects` | 6926–6934 | 18 | **DATA TABLE.** Status-class effects. |
| 143 | `BossAIChuckRoleEffects` | 6935–6940 | 12 | **DATA TABLE.** Per-role effect lists. |
| 144 | `BossAIJasmineRoleEffects` | 6941–6946 | 12 | DATA TABLE. |
| 145 | `BossAIPryceRoleEffects` | 6947–6955 | 18 | DATA TABLE. |
| 146 | `BossAIClairRoleEffects` | 6956–6963 | 16 | DATA TABLE. |
| 147 | `BossAIWillRoleEffects` | 6964–6970 | 14 | DATA TABLE. |
| 148 | `BossAIBrunoRoleEffects` | 6971–6976 | 12 | DATA TABLE. |
| 149 | `BossAIKarenRoleEffects` | 6977–6985 | 18 | DATA TABLE. |
| 150 | `BossAIKogaRoleEffects` | 6986–6993 | 16 | DATA TABLE. |
| 151 | `BossAIChampionRoleEffects` | 6994–7000 | 14 | DATA TABLE. |
| 152 | `BossAIRiskyEffects` | 7001–7006 | 12 | **DATA TABLE.** Risky/recoil/charge effects. |

**Inventory totals:** 152 entries, ~13,090 estimated bytes (slight over-count vs. observed section size because comments inflate line × 2). All `:` (single-colon, file-local). No `::` exports.

---

## Mini-task 2 — Classification

Each routine is mapped to one of seven targets:

- **`boss_state.asm`** — turn/phase tracking, seen-species, revealed-moves bookkeeping, scouted-bit ledger, switch-cooldown decay
- **`boss_typing.asm`** — type-mask inference, type-contribution helpers, type-matchup primitives, threat-type extraction
- **`boss_scoring.asm`** — score-byte mutators, plan/scout/repeat biases, lookahead, plan tables, role tables
- **`boss_setup.asm`** — setup/status/denial effect predicates + setup-boost-value (the speed-cap routine)
- **`boss_moves.asm`** — move attribute helpers, pressure scoring, KO-pressure, held-item modifiers, choice-lock, scratch save/restore, **`BossAI_ApplyMoveModel`**
- **`boss_switch.asm`** — switch eligibility, threat predicates, public-speed comparison, switch-confidence + thresholds + risk refinement, plan switch bias
- **`boss.asm`** (kept) — `BossAI_SelectMove`, `BossAI_SwitchOrTryItem` (the two top-level entries called from outside this section)

`MaybePickAdaptiveEnemyLead` is a pre-battle one-shot that mutates state — placed in **`boss_state.asm`**.

### Classification table

| Routine # | Target | Justification keywords |
|----------:|--------|------------------------|
| 1 | boss_state | turn-tick, cooldown |
| 2–4 | boss_state | record (switch/species/faint) |
| 5–7 | boss_state | seen-species bit helpers |
| 8 | boss_state | adaptive enemy lead, mutates state |
| 9–13 | boss_state | revealed-moves / used-moves bookkeeping |
| 14–15 | boss_moves | move attr/byte read |
| 16–17 | boss_state | revealed-moves mask mutators |
| 18 | boss_state | per-turn cache reset |
| 19 | boss_moves | per-move scoring (giant) |
| 20 | boss_typing | ghost-type predicate |
| 21 | **boss (kept)** | top-level move dispatch |
| 22 | **boss (kept)** | top-level switch/item dispatch |
| 23–24 | boss_state | switch ledger / cooldown |
| 25–26 | boss_switch | switch eligibility |
| 27–30 | boss_switch | threat predicates (cached/uncached) |
| 31–35 | boss_typing | type-matchup primitives |
| 36–47 | boss_moves | KO/pressure/held-item/category/accuracy/dark-shield |
| 48–50 | boss_typing | type-contribution helpers |
| 51 | boss_switch | speed comparison (used by switch decision) |
| 52–62 | boss_switch | thresholds, anti-loop, predict-switch, suspicious switch-in, etc. |
| 63–64 | boss_state | revealed mask test |
| 65–66 | boss_moves | KO move predicate (cached/uncached) |
| 67–71 | boss_moves | held-effect, choice-lock, struct save/restore |
| 72 | boss_switch | bench threat score (used in switch refinement) |
| 73 | boss_scoring | plan-selection state machine |
| 74 | boss_scoring | role-based party search |
| 75–80 | boss_setup | setup/status/denial predicates + boost-value |
| 81 | boss_state | seen-species index |
| 82–101 | boss_typing | plausible/likely mask construction + bit helpers |
| 102–113 | boss_scoring | bias + lookahead + projection + clamp |
| 114–120 | boss_typing | threat-type computation + nullifier |
| 121 | boss_typing | evolution predicate (used by mask building) |
| 122–124 | boss_scoring | tier weights + scout threshold |
| 125–130 | boss_state | scouted-bit + repeat tracker |
| 131–137 | boss_switch | switch refinement, plan bias, sack/wincon, scout pivot |
| 138–139 | boss_typing | threat-types data tables |
| 140–152 | boss_scoring | tier weights + role tables + risky effects |

### Per-file roll-up

| File | Routine count | ~Bytes | Notes |
|------|--------------:|------:|-------|
| `boss_state.asm` | 24 | ~1,330 | Turn/seen/revealed bookkeeping; small routines, many call sites |
| `boss_typing.asm` | 38 | ~2,400 | Type-mask construction is verbose; includes 2 small data tables |
| `boss_scoring.asm` | 28 | ~1,950 | Includes 12 role-effect tables (~200 B together) and lookahead routines |
| `boss_setup.asm` | 6 | ~490 | Smallest split file; the speed-cap routine dominates |
| `boss_moves.asm` | 27 | ~5,300 | **Largest** — `ApplyMoveModel` alone is ~3.6 KB |
| `boss_switch.asm` | 27 | ~2,070 | Includes `ComputeSwitchCandidateRisk` (~580 B) |
| `boss.asm` (kept) | 2 | ~570 | Two top-level entries only |
| **Total** | **152** | **~14,110** | Estimate may be high vs. ~12.4 KB observed; build will reveal exact |

The bank-0e free-byte budget post-TD-005 P1 + TD-007 is **568 bytes** ([dev_index.md:118](../../docs/generated/dev_index.md:118)), and the section currently consumes ~12.4 KB. The split is byte-neutral (refactor-only), so no bank pressure change is expected.

---

## Mini-task 3 — Local-label scope audit

**RESULT: GREEN. Zero RED flags. The split is safe with respect to local-label scoping.**

- Total `.foo` local-label declarations in boss.asm: **560**
- Cross-routine references via the explicit-form `BossAI_X.localname` syntax: **0**

Verification commands the next agent must run before extraction:

```bash
# 1. Confirm local-label count is unchanged
grep -cE '^\.[a-zA-Z_]' engine/battle/ai/boss.asm
# Expected: 560

# 2. Confirm no cross-routine local-label references
grep -E 'BossAI[A-Za-z_]+\.[a-z][a-z_]+' engine/battle/ai/boss.asm
# Expected: no output (0 matches)

# 3. (If splitting is partly done) confirm same invariant across all split files
grep -cE '^\.[a-zA-Z_]' engine/battle/ai/boss*.asm
grep -E 'BossAI[A-Za-z_]+\.[a-z][a-z_]+' engine/battle/ai/boss*.asm
```

In RGBDS, `.foo` resolves to the most-recent preceding global label's scope. Because no routine uses the explicit `BossAI_X.foo` form to reach into another routine's locals, every `.foo` is implicitly bound to its parent global label. Moving a routine to a new file carries the locals with it, and no caller needs adjustment.

If a future commit (between this plan being drafted and execution) adds a cross-routine local-label reference, command 2 above will surface it before the move executes.

---

## Mini-task 4 — Bank/section relocation analysis

**Decision: all 7 files stay in `SECTION "Enemy Trainers", ROMX` (bank 0x0e). No relocation is required or recommended.**

### Section context

- Section: `"Enemy Trainers"` ([main.asm:168–172](../../main.asm:168))
- Includes: `engine/battle/ai/items.asm`, `engine/battle/ai/boss.asm`, `engine/battle/read_trainer_attributes.asm`
- Bank: 0x0e (16,384 byte ceiling)
- Pre-TD-005-P1: 6 free bytes
- Post-TD-005-P1: 568 free (per [docs/generated/dev_index.md:118](../../docs/generated/dev_index.md:118))
- Refactor-only split is byte-neutral → 568 free expected to remain

### Why no relocation

Splitting boss.asm purely re-shuffles where the same bytes appear in source. Because all 7 split files are INCLUDEd in the same `SECTION` block, the linker concatenates them in include-order into the same bank. The byte total in 0x0e doesn't change.

Moving any individual file to a *different* SECTION (e.g., a new `SECTION "Boss AI Helpers", ROMX[$4000], BANK[$13]`) would require:
- New SECTION declaration for that file
- All same-section `call`s into that file's labels become `farcall`s
- All `:` references that need to resolve cross-section may need `::` promotion (or stay `:` since main.asm is one TU, but link-order can still bite)
- Higher cost, no benefit while 0x0e has 568 free

### Farcall in-degree (top callers from outside boss.asm)

External `farcall` / `callfar` / `BANK(...)` references targeting `BossAI_*`:

| Caller file | Target routine | Citation |
|-------------|----------------|----------|
| `engine/battle/used_move_text.asm` | `BossAI_RecordRevealedPlayerMove` | [used_move_text.asm:16](../../engine/battle/used_move_text.asm:16) |
| `engine/battle/core.asm` | `BossAI_IncrementTurnsElapsed` | [core.asm:158](../../engine/battle/core.asm:158) |
| `engine/battle/core.asm` | `BossAI_RecordPlayerSwitch` | [core.asm:745](../../engine/battle/core.asm:745) |
| `engine/battle/core.asm` | `BossAI_RecordPlayerFaint` | [core.asm:2668](../../engine/battle/core.asm:2668) |
| `engine/battle/core.asm` | `BossAI_LoadPlayerUsedMovesForActiveSpecies` | [core.asm:3954](../../engine/battle/core.asm:3954) |
| `engine/battle/core.asm` | `BossAI_RecordPlayerSpecies` | [core.asm:3967](../../engine/battle/core.asm:3967) |
| `engine/battle/ai/items.asm` | `BossAI_OnSwitchExecuted` | [items.asm:687](../../engine/battle/ai/items.asm:687) (same SECTION) |
| `engine/battle/ai/move.asm` | `BossAI_ApplyMoveModel` | [move.asm:115](../../engine/battle/ai/move.asm:115) |
| `engine/battle/ai/move.asm` | `BossAI_SelectMove` | [move.asm:116](../../engine/battle/ai/move.asm:116) |
| `engine/battle/ai/boss.asm` | `BossAI_TraceTopMoves` | [boss.asm:2346](../../engine/battle/ai/boss.asm:2346) (already farcall — different section) |

External in-degree is **9 callsites across 7 unique target routines**. All targets are `BossAI_Record*` / `BossAI_LoadPlayer*` / `BossAI_OnSwitch*` / `BossAI_ApplyMoveModel` / `BossAI_SelectMove` / `BossAI_IncrementTurnsElapsed`. None of these routines are at risk of relocating bank — they all stay in `SECTION "Enemy Trainers"`.

The plan therefore has **zero impact on existing `farcall` paths**. `tools/audit/check_farcall_hl_clobber.py` should not regress.

### Hot-path internal callers (NOT to move)

Per the internal-call grep, these are the most-called routines within boss.asm and should be considered hot-path. They are still safe to move (same-section `call` is bank-neutral) but the next agent should keep them on the early extraction list to verify nothing breaks:

- `BossAI_GetMoveAttr` (~10+ callers) → `boss_moves.asm`
- `BossAI_DiscourageScoreHL` (~13+ callers via `jp`/`call`) → `boss_scoring.asm`
- `BossAI_EncourageScoreHL` (~10+ callers) → `boss_scoring.asm`
- `BossAI_GetEnemyHeldEffect` (~6 callers) → `boss_moves.asm`
- `BossAI_PublicEnemyFaster` (~6 callers) → `boss_switch.asm`
- `BossAI_ResetTurnCaches`, `BossAI_SelectPlanIfNeeded`, `BossAI_ComputePlayerPlausibleTypeMask` (called from both `BossAI_SelectMove` AND `BossAI_SwitchOrTryItem`)

---

## Mini-task 5 — Extraction order + checkpoint plan

**Strategy: leaf-most files first.** Each step is a single commit. Build + audits run between steps. SHA1 changes once at step 1 (the routine reordering); subsequent steps preserve byte layout.

### Pre-flight (before step 1)

```bash
# Baseline build artifacts to compare against
wsl -e bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && \
    make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe \
    RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc'
sha1sum pokegold.gbc > /tmp/baseline.sha1
cp pokegold.map /tmp/baseline.map

# Snapshot baseline audit results
python3 tools/audit/check_release_smoke.py
python3 tools/audit/check_farcall_hl_clobber.py
python3 tools/audit/check_boss_ai_no_cheat.py
python3 tools/audit/check_boss_ai_trace_invariants.py
python3 tools/audit/check_boss_ai_memory_budget.py
```

### Step 0 — claim in AGENT_LOG (separate commit)

Append a `## YYYY-MM-DD HH:MM UTC — TD-004 — claimed` entry per template in [tech_debt/README.md](../README.md). Mention strategy choice (thematic split per escalation #2). No source changes in this commit.

### Step 1 — Reorder + re-export prep (1 commit, SHA1 CHANGES)

Move all 152 routines into thematic order *within the existing boss.asm* — no new files yet. The new in-file order is: `state` block, `typing` block, `scoring` block, `setup` block, `moves` block, `switch` block, then `boss` (`SelectMove` + `SwitchOrTryItem`) at the end.

Why this is a separate commit: the routine reordering is the byte-shifting event. After step 1 lands, `pokegold.gbc` SHA1 changes once. All subsequent file-extract steps preserve those bytes verbatim.

Verification:
```bash
make pokegold.gbc                          # must link
# SHA1 will differ from baseline — expected
python3 tools/audit/check_release_smoke.py
python3 tools/audit/check_boss_ai_no_cheat.py
python3 tools/audit/check_boss_ai_trace_invariants.py
python3 tools/audit/check_boss_ai_memory_budget.py
python3 tools/audit/check_farcall_hl_clobber.py
python3 tools/audit/check_battle_math_safety.py
python3 scripts/generate_dev_index.py --rom pokegold
sha1sum pokegold.gbc > /tmp/post_reorder.sha1   # capture for steps 2-7 to match
```

If any audit references specific line numbers in boss.asm (likely `check_boss_ai_trace_invariants.py`), update those references in the same commit.

**ESCALATION:** Step 1 changes SHA1. User playtest of one battle (rival 1 or first gym) at this point is recommended — if audits pass and battle plays normally, the reorder is sound. Do not refresh `roms.sha1` yet — wait until step 7 lands.

### Step 2 — Extract boss_setup.asm (1 commit, SHA1 unchanged)

Smallest extract first to validate the extract pattern. Cut routines 75–80 (effect predicates + setup-boost-value) into `engine/battle/ai/boss_setup.asm`. Add `INCLUDE "engine/battle/ai/boss_setup.asm"` in main.asm at the position those routines previously occupied within `SECTION "Enemy Trainers"`.

Verification:
```bash
make pokegold.gbc
sha1sum pokegold.gbc | diff - /tmp/post_reorder.sha1  # must match
python3 tools/audit/check_boss_ai_trace_invariants.py
python3 tools/audit/check_navigation_floor.py
```

### Step 3 — Extract boss_state.asm (1 commit, SHA1 unchanged)

Cut state routines into `boss_state.asm`. Add INCLUDE in correct position. Local-label re-grep:
```bash
grep -cE '^\.[a-zA-Z_]' engine/battle/ai/boss*.asm
# Sum across all files must equal 560
grep -E 'BossAI[A-Za-z_]+\.[a-z][a-z_]+' engine/battle/ai/boss*.asm
# Must be 0
```
SHA1 must match `/tmp/post_reorder.sha1`.

### Step 4 — Extract boss_typing.asm (1 commit, SHA1 unchanged)

Same pattern. SHA1 must match `/tmp/post_reorder.sha1`.

### Step 5 — Extract boss_scoring.asm (1 commit, SHA1 unchanged)

Same pattern. **Special caution:** `boss_scoring.asm` includes the role-effect data tables (138–152). The audit `check_boss_ai_trace_invariants.py` references `BossAI_DiscourageScoreHL` / `BossAI_EncourageScoreHL` by name — those names don't change, but if the audit script greps a specific file path, update it.

### Step 6 — Extract boss_switch.asm (1 commit, SHA1 unchanged)

Same pattern. Largest single routine here is `BossAI_ComputeSwitchCandidateRisk` (~580 B) — confirm it fits the slice cleanly.

### Step 7 — Extract boss_moves.asm (1 commit, SHA1 unchanged)

Last and largest extract. After this step, `boss.asm` retains only `BossAI_SelectMove` + `BossAI_SwitchOrTryItem` (~570 B total), down from ~14 KB. SHA1 must match `/tmp/post_reorder.sha1`.

### Step 8 — Doc updates (1 commit, no source change)

- Update [docs/agent_navigation/source_output_ownership.md](../../docs/agent_navigation/source_output_ownership.md) to map each new file to a subsystem
- Update [docs/agent_navigation/subsystems/boss_ai_logic.md](../../docs/agent_navigation/subsystems/boss_ai_logic.md) routine table with new file paths
- Append `## YYYY-MM-DD — TD-004 — done` entry to [tech_debt/AGENT_LOG.md](../AGENT_LOG.md), update [tech_debt/STATUS.md](../STATUS.md), append a CHANGELOG entry
- Re-run the freshness audit: `python3 tools/audit/check_tech_debt_freshness.py`
- Append `## TD-004 — boss.asm split` to [tech_debt/CHANGELOG.md](../CHANGELOG.md) with the SHA1-change note

### Step 9 — User playtest + SHA1 refresh (gated)

User plays through at least: starter selection + Rival 1 + Falkner + Bugsy. Confirms boss AI behavior matches pre-split. Then:
```bash
sha1sum pokegold.gbc    # capture new SHA1
# Update roms.sha1 + dist/checksums.txt with new SHA1
make compare    # must now PASS
```

This is the same SHA1-update escalation pattern as TD-007 — needs explicit user OK before touching `roms.sha1`.

### Constraints / ordering rules

- **Step 1 must precede steps 2–7.** Reordering after extraction is much harder (would require re-cutting and re-pasting across files).
- **Steps 2–7 are reorderable among themselves**, but recommend leaf-first (smallest, fewest dependencies first) to limit blast radius per commit.
- **Step 8 must follow steps 2–7** (docs reference final file layout).
- **Step 9 must follow step 8** (`STATUS.md done` should already say done before user playtest gates the SHA1).

---

## Mini-task 6 — Risk register + rollback plan

Risks ranked by probability × impact. Estimates: P (low/med/high), I (small / medium / large blast).

### R1 — Local-label collision after move (P: low, I: large) — RANK 1

Some routine's `.loop` happens to collide with a sibling's `.loop` after both move to the same new file. RGBDS scopes locals to the preceding global, so this *should* be safe — but if a routine uses the bare `.loop` form when it meant to reach into another's scope, the move silently re-binds.

- **Detection:** `tools/audit/check_boss_ai_trace_invariants.py` validates specific instruction sequences inside specific routines. A re-bound `.loop` would fail this audit.
- **Mitigation:** the explicit-form grep (Mini-task 3) already shows zero cross-routine references → low P. But re-run the grep before AND after each extract step.
- **Rollback:** `git revert` the extract commit. SHA1 returns to the post-step-1 state.

### R2 — Bank overflow at link (P: low, I: medium) — RANK 2

Step 1 reorders routines but does not change byte total → bank usage unchanged. Steps 2–7 are byte-neutral. Therefore bank 0x0e free space stays at 568 B unless an extract accidentally duplicates a routine.

- **Detection:** `make pokegold.gbc` link error if section overflows.
- **Mitigation:** after each step, regenerate dev_index and confirm bank 0x0e free count.
- **Rollback:** `git revert` the offending step.

### R3 — `farcall` hl-clobber regression introduced by reorder (P: low, I: medium) — RANK 3

[CLAUDE.md](../../CLAUDE.md) cites two prior incidents (April 2026 one-shot damage, May 2026 rival 1 softlock) where reorganizing code reintroduced an hl-clobber bug. The split itself doesn't introduce new `farcall`s, but if step 1 reorders a `homecall` thunk relative to its target, behavior could regress.

- **Detection:** `tools/audit/check_farcall_hl_clobber.py` after step 1.
- **Mitigation:** the split adds zero new `farcall`s — all internal calls remain `call` (same section). Only existing `farcall BossAI_TraceTopMoves` ([boss.asm:2346](../../engine/battle/ai/boss.asm:2346)) is at risk; verify it still resolves correctly.
- **Rollback:** `git revert` step 1, re-plan ordering to avoid the regression.

### R4 — `BANK(label)` returns wrong value after extract (P: very low, I: medium) — RANK 4

If any code uses `BANK(BossAI_X)` to construct a bank byte, the value is unchanged as long as the label stays in 0x0e. If a future change accidentally moves a file to a different section, `BANK(...)` will silently return a different value and `farcall` will jump to a wrong bank.

- **Detection:** runtime — would manifest as a wild jump in battle. Hard to detect in audit; gameplay regression.
- **Mitigation:** all 6 split files MUST be INCLUDEd in the same `SECTION "Enemy Trainers"` block in main.asm. Code review of the main.asm diff is the gate.
- **Rollback:** check main.asm diff for any new `SECTION` line introduced near the boss includes — if present, revert.

### R5 — Audit script greps the wrong file path (P: med, I: small) — RANK 5

`tools/audit/check_boss_ai_trace_invariants.py` and `tools/audit/bug_hunt_triage.py` reference `engine/battle/ai/boss.asm` directly. After extract, some routines they assert about live in different files.

- **Detection:** audit failure with "could not find routine X in boss.asm" or similar.
- **Mitigation:** audit a script change is part of step 1 (or whichever step extracts the routine the audit checks).
- **Rollback:** trivial — update the audit's file paths in the same commit as the extract.

### Rollback plan / point of no return

| After commit | Cleanly revertable? | Why |
|--------------|---------------------|-----|
| Step 0 (claim) | Yes | log-only |
| Step 1 (reorder) | Yes — revert restores original boss.asm byte-for-byte | one commit, contained |
| Step 2 (boss_setup extract) | Yes | revert restores boss.asm with reorder still in place |
| Steps 3–7 (each extract) | Yes — revert restores prior file layout | each is one commit |
| Step 8 (doc update) | Yes | docs only |
| Step 9 (`roms.sha1` refresh) | **POINT OF NO RETURN** | refreshing `roms.sha1` makes `make compare` succeed against the new SHA1; reverting requires also reverting all of 1–8 |

**Recommendation:** keep step 9 as the LAST commit. Until then every change can be cleanly `git revert`-ed without disturbing roms.sha1 / dist/checksums.txt. The point of no return aligns with user playtest sign-off.

If something goes catastrophically wrong after step 9 (e.g. user finds a regression on day 2), the recovery is: revert all of TD-004's commits as one block, then refresh `roms.sha1` back to the original baseline. This is more work than reverting one commit but still finite — every commit in the TD-004 sequence is independently reversible.

---

## Cross-references

- Recipe: [tech_debt/FIX_PROPOSALS.md TD-004](../FIX_PROPOSALS.md) §242–323
- Bank-pressure: [tech_debt/TECH_DEBT_REPORT_ADDENDUM.md](../TECH_DEBT_REPORT_ADDENDUM.md) "2026-05-03 — TD-001 snapshot refresh"
- Status entry: [tech_debt/STATUS.md](../STATUS.md) TD-004 row (currently `open`)
- Build invariants: [CLAUDE.md](../../CLAUDE.md) "RGBDS / asm gotchas", "Build & verification"
- Source of truth: [engine/battle/ai/boss.asm](../../engine/battle/ai/boss.asm)
- Inclusion: [main.asm:168–172](../../main.asm:168) — `SECTION "Enemy Trainers", ROMX`
- Per-routine audit references: [tools/audit/check_boss_ai_trace_invariants.py](../../tools/audit/check_boss_ai_trace_invariants.py), [tools/audit/bug_hunt_triage.py](../../tools/audit/bug_hunt_triage.py)
- Dev index baseline: [docs/generated/dev_index.md](../../docs/generated/dev_index.md) (Generated 2026-05-03)

---

## Open questions for the executing agent

1. The exact byte size of each routine (estimates above use lines × 2 B/line). Run `python3 scripts/generate_dev_index.py --rom pokegold` and inspect `pokegold.map` to get exact section sizes per included file after each extract. Update Mini-task 2 roll-up table with measurements.
2. Whether `tools/audit/check_boss_ai_trace_invariants.py` references file paths or only routine names. If the former, update paths inline with the relevant extract step. If the latter, no change needed.
3. Whether the user wants step 1 (reorder) to be its own commit with playtest before extracts begin. Default per this plan: yes. Alternative: bundle reorder into step 2 (boss_setup extract). Recommend keeping step 1 separate so the SHA1-change moment is isolated and bisectable.
