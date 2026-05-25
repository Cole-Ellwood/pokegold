# Boss AI Logic Micro-Index

Use this when the task asks about *what the Boss AI does or where it lives in
source*: scoring, switching, item use, memory, plausible-move inference,
plan/role logic, lookahead, tier ramping, or any "where in the split Boss AI source is the
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
- Line numbers in this index are generated from the split Boss AI source.
  After a non-trivial Boss AI source edit, run
  `scripts/generate_boss_ai_index.py` and
  `tools/audit/check_boss_ai_index_lines.py`.
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
  was lifted to its own `AI Scoring` SECTION; the split Boss AI source reaches
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
| `BossAI_HasAnyKOMove` | `engine/battle/ai/boss_policy_switch.asm:632` | up to 16 (3-4 per Evaluate × 4) | scans 4 enemy moves, each → `BossAI_CheckTypeMatchupNoItem` (full type-chart walk in far bank) | one `SelectMove` tick |
| `BossAI_PlayerHasPublicThreatVsEnemy` | `engine/battle/ai/boss_policy_move.asm:413` | ~20+ (`.EnemyUnderPressure` callers + Spikes layers + `PredictPlayerSwitch`) | walks 4 used-moves + type chart + revealed mask | one `ApplyMoveModel` pass |
| `BossAI_PlayerHasRevealedPriorityThreat` | `engine/battle/ai/boss_policy_move.asm:504` | ~20+ (same shape) | walks 4 used-moves + type chart per priority hit | one `ApplyMoveModel` pass |
| `BossAI_PredictPlayerSwitch` | `engine/battle/ai/boss_policy_switch.asm:474` | ~7 (Mercy refusal, Choice regret, 3× Spikes layers, Switch confidence, MultiTurn projection) | calls 2 of the above | one `SelectMove` tick |
| `BossAI_GetPrimaryThreatType` | `engine/battle/ai/boss_policy_move.asm:4591` | ~8 (Evaluate `.check_reply` 4365 + MultiTurn `.check_threat` 4452, x4) | walks revealed mask + per-type severity | one `SelectMove` tick |

Specific `HasAnyKOMove` call sites inside `BossAI_EvaluateActionLookahead`:
`BossAI_EvaluateActionLookahead` local `.check_setup` at
`engine/battle/ai/boss_policy_move.asm:4319` (gated), `.check_reply` at
`engine/battle/ai/boss_policy_move.asm:4365` (always at MID+),
`.late_reply` at `engine/battle/ai/boss_policy_move.asm:4382` (always at LATE),
plus `BossAI_ApplyMultiTurnProjection` local `.check_threat` at
`engine/battle/ai/boss_policy_move.asm:4452`. None of these inputs change between move-1 and move-4 of the same
evaluation pass — same answer, computed up to 4× per turn.

Two trivial dead trampolines were removed in the same pass:

- `.ApplyLegacyRoleBiasIfNeeded` — 2-line `jr` to `.ApplyRoleBias`,
  refactor leftover.
- `.IsSetupMove` — 1-line `jp` to `BossAI_IsCurrentEnemySetupMove`, no
  callers benefit from the wrapper.

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

- Per-class role branches `.falkner` through `.champion` live in
  `engine/battle/ai/boss_policy_move.asm:1697-1775`; their effect tables live
  in `engine/battle/ai/boss_policy_move.asm:5066-5133`. Type-only
  encouragements (Chuck → Fighting, Bruno → Fighting, Koga → Poison/Bug)
  may shadow the engine's regular STAB/type-pressure path. Effect-table
  pushes (Pryce → Whirlwind, etc.) are doing distinct work. Don't touch
  without a trace dump on a known LATE battle.
- `MaybePickAdaptiveEnemyLead` (`engine/battle/ai/boss_policy_move.asm:17`) not yet audited for dead branches.

## Source Files At A Glance

| File | Lines | Role |
| --- | --- | --- |
| `engine/battle/ai/boss_platform.asm` | ~1230 | Platform-owned guarded fragments: state/public-info plumbing, passive caches, held items, type helpers, structural masks, score/scout I/O, and no-cheat tables. |
| `engine/battle/ai/boss_policy_move.asm` | ~5150 | Move-policy guarded fragments: adaptive lead, scoring overlay, move pick, plan/role, lookahead, threat/scout policy, and policy-owned tables. |
| `engine/battle/ai/boss_policy_switch.asm` | ~1190 | Switch-policy guarded fragments: dispatch, switch predicates/classifiers, confidence, candidate risk, and finalization. |
| `engine/battle/ai/boss_thunks.asm` | ~80 | HL-preserving farcall thunks into the AI Scoring bank. |
| `engine/battle/ai/scoring.asm` | ~3230 | Base Gen 2 AI scoring layers (`AI_Basic`, `AI_Setup`, `AI_Types`, `AI_Offensive`, `AI_Smart`, `AI_Cautious`, `AI_Status`, `AI_Risky`). Boss AI runs on top of these. |
| `engine/battle/ai/switch.asm` | ~660 | Base switch helpers (`CheckPlayerMoveTypeMatchups`, `CheckAbleToSwitch`, `FindAliveEnemyMons*`, `FindEnemyMons*`). Boss switch logic calls into these. |
| `engine/battle/ai/items.asm` | ~860 | `AI_SwitchOrTryItem` dispatcher (`SwitchOften` / `SwitchRarely` / `SwitchSometimes`), `AI_TryItem`, `EnemyUsed*` item routines. Vanilla path — Boss AI hooks in via `BossAI_SwitchOrTryItem`. |
| `engine/battle/ai/move.asm` | ~220 | Move-pick dispatcher. Where `BossAI_ApplyMoveModel` and `BossAI_SelectMove` are called from. |
| `engine/battle/ai/redundant.asm` | ~200 | Move-redundancy avoidance helpers. |
| `data/battle/ai/*.asm` | small | Effect lists for the **vanilla** AI scoring layer (`useful_moves`, `stall_moves`, `risky_effects`, `residual_moves`, `encore_moves`, `status_only_effects`, `constant_damage_effects`, `reckless_moves`, `rain_dance_moves`, `sunny_day_moves`). Boss AI inherits their effect because vanilla scoring runs first, but consumers are in `scoring.asm`, not the Boss AI split files. Boss AI's own effect tables live in `engine/battle/ai/boss_policy_move.asm` (`BossAIDenyKOEffects`, `BossAIStatusEffects`, `BossAIRiskyEffects`, role-effect tables). |

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

Boss AI paths are cited per split source file below.

### Data Ownership At A Glance

| Concern | Lives in |
| --- | --- |
| Vanilla AI effect lists (`useful_moves`, `risky_effects`, `stall_moves`, etc.) | `data/battle/ai/*.asm` (consumed by `engine/battle/ai/scoring.asm`) |
| Boss AI effect tables (`BossAIDenyKOEffects`, `BossAIStatusEffects`, `BossAIRiskyEffects`) | `engine/battle/ai/boss_policy_move.asm` |
| Per-boss role-effect tables (`BossAIChuckRoleEffects` etc.) | `engine/battle/ai/boss_policy_move.asm` |
| Per-trainer tier (class+id → EARLY/MID/LATE) | `BossAITierMap:1` in `data/trainers/ai_tiers.asm`; consumed by `LoadBossAITier:69` in `engine/battle/read_trainer_attributes.asm` |
| Per-class tier-weight-row override | `BossAITierRampMap:51` in `data/trainers/ai_tiers.asm` (default = `tier - 1`, set at `LoadBossAITier:97-98`) |
| Tier weight table (rows indexed by tier-weight-row) | `BossAITierWeights` (`engine/battle/ai/boss_policy_move.asm:6336`) |
| Plausible-threat type table | `BossAI_PlausibleThreatTypes` (`engine/battle/ai/boss_platform.asm:1387`) |
| Trainer attributes (base reward, AI flags) — separate concern, do not confuse with tier | `data/trainers/attributes.asm` (consumed at `engine/battle/read_trainer_attributes.asm:67`) |

### Memory: per-battle state record/access

| Need | Label / line |
| --- | --- |
| Reset boss state (battle start) | `ClearBossAIState` (`engine/battle/read_trainer_attributes.asm:138`) |
| Tick turn counter | `BossAI_IncrementTurnsElapsed` (`engine/battle/ai/boss_platform.asm:24`) |
| Record opponent send-out | `BossAI_RecordPlayerSwitch` (`engine/battle/ai/boss_platform.asm:126`), `BossAI_RecordPlayerSpecies` (`engine/battle/ai/boss_platform.asm:138`) |
| Record opponent KO | `BossAI_RecordPlayerFaint` (`engine/battle/ai/boss_platform.asm:186`) |
| Public alive bitmap (per seen species) | `BossAI_SetSeenPlayerAliveBit` (`engine/battle/ai/boss_platform.asm:217`), `BossAI_ClearSeenPlayerAliveBit` (`engine/battle/ai/boss_platform.asm:227`), `BossAI_SeenPlayerSpeciesBitFromC` (`engine/battle/ai/boss_platform.asm:238`) |
| Add a revealed move to memory | `BossAI_RecordRevealedPlayerMove` (`engine/battle/ai/boss_platform.asm:260`), `BossAI_AddRevealedMoveToSpeciesMask` (`engine/battle/ai/boss_platform.asm:467`), `BossAI_SetRevealedSpeciesMaskBit` (`engine/battle/ai/boss_platform.asm:498`) |
| Switch cooldown | `BossAI_DecaySwitchCooldown` (`engine/battle/ai/boss_policy_switch.asm:515`), `BossAI_OnSwitchExecuted` (`engine/battle/ai/boss_policy_switch.asm:500`) |

### Memory: per-species lookup

These read the per-seen-species memory in `wBossAIRevealedMovesBitmap` and
`wBossAISpeciesUsedMoves`. Six 4-byte revealed type masks (one per seen species
slot), plus a per-species mirror of `wPlayerUsedMoves`.

| Need | Label / line |
| --- | --- |
| Slot index for active species | `BossAI_GetActiveSpeciesSeenIndex` (`engine/battle/ai/boss_platform.asm:1042`), `BossAI_GetActiveSpeciesSeenBit` (`engine/battle/ai/boss_platform.asm:1304`) |
| Pointer to active species' revealed-type mask | `BossAI_GetActiveSpeciesRevealedMaskPointer` (`engine/battle/ai/boss_platform.asm:355`) |
| Load per-species used-moves into vanilla `wPlayerUsedMoves` | `BossAI_LoadPlayerUsedMovesForActiveSpecies` (`engine/battle/ai/boss_platform.asm:374`) |
| Mirror current `wPlayerUsedMoves` back to species slot | `BossAI_MirrorPlayerUsedMovesToSpeciesSlot` (`engine/battle/ai/boss_platform.asm:401`) |
| Pointer to active species' used-moves slot | `BossAI_GetActiveSpeciesUsedMovesPointer` (`engine/battle/ai/boss_platform.asm:417`) |
| Test a bit in the revealed-species mask | `BossAI_TestRevealedSpeciesMaskBit` (`engine/battle/ai/boss_platform.asm:864`) |
| Check active species has revealed any super-effective move | `BossAI_HasRevealedSuperEffectiveMove` (`engine/battle/ai/boss_policy_move.asm:3812`) |

### Adaptive lead pick

| Need | Label / line |
| --- | --- |
| Per-trainer adaptive lead | `MaybePickAdaptiveEnemyLead` (`engine/battle/ai/boss_policy_move.asm:17`) |
| Internal helpers | `.ShouldUseAdaptiveLeadForTrainer` (`engine/battle/ai/boss_policy_move.asm:75`), `.FindFirstAliveOTMon` (`engine/battle/ai/boss_policy_move.asm:101`), `.FindNextAliveOTMon` (`engine/battle/ai/boss_policy_move.asm:129`) |

### Plausible / likely move-type inference

The "what does the player likely have?" engine. Builds two 4-byte type masks:
plausible (could exist) and likely (high evidence weight). Cached in WRAM
keyed on species + level.

| Need | Label / line |
| --- | --- |
| Build mask for current player active | `BossAI_ComputePlayerPlausibleTypeMask` (`engine/battle/ai/boss_policy_move.asm:4757`) |
| Public STAB seed | `BossAI_AddPublicSTABThreatsToMask` (`engine/battle/ai/boss_policy_move.asm:4800`) |
| Wipe cache | `BossAI_ClearPlausibleMask` (`engine/battle/ai/boss_platform.asm:1089`) |
| Add revealed damaging types | `BossAI_AddRevealedDamagingTypesToMask` (`engine/battle/ai/boss_policy_move.asm:4843`) |
| Add a single move id (plausible / likely) | `BossAI_AddMoveIdToPlausibleMask` (`engine/battle/ai/boss_policy_move.asm:4871`), `BossAI_AddMoveIdToLikelyMask` (`engine/battle/ai/boss_policy_move.asm:4901`) |
| Set bit by type id | `BossAI_SetPlausibleAndLikelyMaskBit` (`engine/battle/ai/boss_platform.asm:1107`), `BossAI_SetPlausibleMaskBit` (`engine/battle/ai/boss_platform.asm:1115`), `BossAI_SetLikelyMaskBit` (`engine/battle/ai/boss_platform.asm:1143`) |
| Walk species + pre-evolutions | `BossAI_AddSpeciesAndPreEvolutionMovesToMask` (`engine/battle/ai/boss_policy_move.asm:4934`), `BossAI_LoadPublicThreatSourceSpecies` (`engine/battle/ai/boss_policy_move.asm:4964`), `BossAI_AdvanceToPreEvolutionThreatSource` (`engine/battle/ai/boss_policy_move.asm:4989`) |
| Per-source contribution | `BossAI_AddCurrentSpeciesSpeculativeMoveThreats` (`engine/battle/ai/boss_policy_move.asm:4971`), `BossAI_AddCurrentSpeciesLikelyMoveThreats` (`engine/battle/ai/boss_policy_move.asm:4980`) |
| Move-source pools | `BossAI_AddBaseTMHMMovesToMask` (`engine/battle/ai/boss_policy_move.asm:4998`), `BossAI_AddSpeciesLevelUpMovesToMask` (`engine/battle/ai/boss_policy_move.asm:5032`), `BossAI_AddSpeciesLevelUpMovesToLikelyMask` (`engine/battle/ai/boss_policy_move.asm:5089`), `BossAI_AddSpeciesEggMovesToMask` (`engine/battle/ai/boss_policy_move.asm:5146`) |
| Test bits | `BossAI_TestPlausibleMaskBit` (`engine/battle/ai/boss_platform.asm:1174`), `BossAI_TestLikelyMaskBit` (`engine/battle/ai/boss_platform.asm:1206`) |
| Risk weight per tier | `BossAI_GetTierPlausibleRiskWeight` (`engine/battle/ai/boss_policy_move.asm:6188`), `BossAI_GetSpeculativePlausibleRiskWeight` (`engine/battle/ai/boss_policy_move.asm:6201`) |
| Static type tables | `BossAI_PlausibleThreatTypes` (`engine/battle/ai/boss_platform.asm:1387`), `BossAIHiddenPowerThreatTypes` (`engine/battle/ai/boss_platform.asm:1408`) |

### Move scoring overlay (`BossAI_ApplyMoveModel`)

Runs after the vanilla AI layers. Walks `wEnemyMonMoves`, scores each, writes
to `wEnemyAIMoveScores`. ~1830 lines of gates and adjustments, organized as
local labels under `BossAI_ApplyMoveModel`. To find a specific gate:

```
rg -n "^\.[A-Za-z]" engine/battle/ai/boss_*.asm | sed -n '1,200p'
```

Top-level entry and named scoring helpers:

| Need | Label / line |
| --- | --- |
| Outer entry | `BossAI_ApplyMoveModel` (`engine/battle/ai/boss_policy_move.asm:172`) |
| Score read/write helpers | `BossAI_LoadScorePointer` (`engine/battle/ai/boss_platform.asm:1248`), `BossAI_SetScoreHL` (`engine/battle/ai/boss_platform.asm:1258`), `BossAI_EncourageScoreHL` (`engine/battle/ai/boss_platform.asm:1264`), `BossAI_DiscourageScoreHL` (`engine/battle/ai/boss_platform.asm:1279`) |
| Apply signed delta | `BossAI_ApplySignedDeltaToScore` (`engine/battle/ai/boss_policy_move.asm:5422`) |
| Plan-driven move bias | `BossAI_ApplyPlanMoveBias` (`engine/battle/ai/boss_policy_move.asm:5179`) |
| Scout-pivot move bias | `BossAI_ApplyScoutMoveBias` (`engine/battle/ai/boss_policy_move.asm:5274`) |
| Repeat-move penalty | `BossAI_ApplyRepeatPenalty` (`engine/battle/ai/boss_policy_move.asm:5294`) |
| Save / restore enemy move struct (so scoring can probe other moves non-destructively) | `BossAI_SaveEnemyMoveStruct` (`engine/battle/ai/boss_platform.asm:1005`), `BossAI_RestoreEnemyMoveStruct` (`engine/battle/ai/boss_platform.asm:1019`) |

Public-failure gates inside `ApplyMoveModel` (search by local label):

- `.UtilityMoveWouldFailPublicly` (`engine/battle/ai/boss_policy_move.asm:512`) — Substitute, Light Screen, Reflect, Safeguard, Protect, Disable, Encore, Mean Look, Dream Eater, Nightmare, Rain/Sunny Day with weather already up.
- `.StatusMoveWouldFailPublicly` (`engine/battle/ai/boss_policy_move.asm:492`) — already-statused target, Safeguard, etc.
- `.DarkShieldBlocksStatusEffect` (`engine/battle/ai/boss_policy_move.asm:661`), `.DarkShieldBlocksUtilityEffect` (`engine/battle/ai/boss_policy_move.asm:677`) — full-Dark player passive shield gating.
- `.EnemyStatusMoveTypeMissesPlayer` (`engine/battle/ai/boss_policy_move.asm:756`) — Thunder Wave into Ground, Glare into Ghost, Toxic into Poison/Steel.
- `.HeldItemMoveBlocked` (`engine/battle/ai/boss_policy_move.asm:414`), `.AssaultVestBlocksCurrentMove` (`engine/battle/ai/boss_policy_move.asm:462`) — own held-item legality.

For the full current behavior list (one-line each, with rationale), read
`docs/boss_ai_post_patch_notes.md` § *Implemented Patch Summary*.

### Move pick (`BossAI_SelectMove`)

| Need | Label / line |
| --- | --- |
| Pick best vs. second-best, weighted dice on score gap | `BossAI_SelectMove` (`engine/battle/ai/boss_policy_move.asm:2786`) |
| Trace top-3 moves and scores | `BossAI_TraceTopMoves` in `engine/battle/ai/boss_trace_topmoves.asm` (own SECTION; called via `farcall` from `BossAI_SelectMove`) |

Dice contract (comment at `engine/battle/ai/boss_policy_move.asm:137-141`): gap ≥6 → 90% best, gap ≥3 →
75% best, else 60% best. 79+ scores are treated as "blocked" (saturated by
`DiscourageScoreHL`).

### Pressure / KO scoring of own moves

| Need | Label / line |
| --- | --- |
| Does current move have KO pressure? | `BossAI_CurrentEnemyMoveHasKOPressure` (`engine/battle/ai/boss_policy_move.asm:3152`) |
| Pressure score (0-N) | `BossAI_CurrentEnemyMovePressureScore` (`engine/battle/ai/boss_policy_move.asm:3186`) |
| Public scored power | `BossAI_CurrentEnemyMoveScoredPower` (`engine/battle/ai/boss_policy_move.asm:3284`) |
| Apply known modifiers | `BossAI_ApplyEnemyKnownPressureModifiers` (`engine/battle/ai/boss_policy_move.asm:3411`), `BossAI_ApplyEnemyHeldItemPressure` (`engine/battle/ai/boss_policy_move.asm:3418`), `BossAI_ApplyEnemyOffensivePassivePressure` (`engine/battle/ai/boss_policy_move.asm:3483`), `BossAI_ApplyPlayerDefensivePassivePressure` (`engine/battle/ai/boss_policy_move.asm:3517`) |
| Has any KO move at all | `BossAI_HasAnyKOMove` (`engine/battle/ai/boss_platform.asm:899`) |

### Type matchup (no-item)

Used in places where item-modified type chart would leak hidden info.
Before calling a target immune/resisted/weak, sanity-check
`docs/agent_navigation/hack_mechanics_reference.md`; these helpers include
Dragon's Majesty, so a Dragon attacker's type-chart immunity can become a
resistance in no-item Boss AI scoring.

| Need | Label / line |
| --- | --- |
| Player move vs. enemy active | `BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem` (`engine/battle/ai/boss_platform.asm:577`) |
| Player move vs. enemy bench (base) | `BossAI_CheckPlayerMoveTypeMatchupVsBaseNoItem` (`engine/battle/ai/boss_platform.asm:593`) |
| Enemy move vs. player active | `BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem` (`engine/battle/ai/boss_platform.asm:609`) |
| Generic | `BossAI_CheckTypeMatchupNoItem` (`engine/battle/ai/boss_platform.asm:650`) |
| Dragon's Majesty overlay | `BossAI_ApplyDragonsMajestyNoItem` (`engine/battle/ai/boss_platform.asm:726`) |
| Type contribution (per-type damage component) | `BossAI_PlayerTypeContribution` (`engine/battle/ai/boss_platform.asm:809`), `BossAI_EnemyTypeContribution` (`engine/battle/ai/boss_platform.asm:814`), `BossAI_TypeContributionAtHL` (`engine/battle/ai/boss_platform.asm:818`) |

### Switch decision

| Need | Label / line |
| --- | --- |
| Top-level switch / item dispatch | `BossAI_SwitchOrTryItem` (`engine/battle/ai/boss_policy_switch.asm:17`) |
| Confidence dice | `BossAI_ComputeSwitchConfidence` (`engine/battle/ai/boss_policy_switch.asm:898`) (margin-based 55/75/90% — comment at `:2641-2644`) |
| Threshold by tier | `BossAI_GetSwitchThreshold` (`engine/battle/ai/boss_policy_switch.asm:588`) |
| Loop-prevention penalty | `BossAI_NeedsLoopPenalty` (`engine/battle/ai/boss_policy_switch.asm:603`) |
| Predict opponent switch | `BossAI_PredictPlayerSwitch` (`engine/battle/ai/boss_policy_move.asm:3745`) |
| Safe-to-switch check | `BossAI_CheckAbleToSwitchSafe` (`engine/battle/ai/boss_policy_switch.asm:524`), `BossAI_FindFirstAliveSwitchCandidate` (`engine/battle/ai/boss_policy_switch.asm:546`) |
| Public faster check | `BossAI_PublicEnemyFaster` (`engine/battle/ai/boss_policy_move.asm:3650`) |
| Vanilla switch helpers used | `engine/battle/ai/switch.asm` (`CheckPlayerMoveTypeMatchups:1`, `CheckAbleToSwitch:176`, `FindAliveEnemyMons*`) |

### Switch predicates / heuristics

These are the named "should we consider switching for reason X?" checks.
Adding new reasons usually means adding one of these alongside.

| Need | Label / line |
| --- | --- |
| Public threat vs. current active | `BossAI_PlayerHasPublicThreatVsEnemy` (`engine/battle/ai/boss_policy_move.asm:2994`) |
| Revealed priority threat | `BossAI_PlayerHasRevealedPriorityThreat` (`engine/battle/ai/boss_policy_move.asm:3069`) |
| Imminent KO prevention | `BossAI_IsImminentKOPrevention` (`engine/battle/ai/boss_policy_switch.asm:652`) |
| Perish escape urgency | `BossAI_EnemyPerishEscapeUrgent` (`engine/battle/ai/boss_policy_switch.asm:666`) |
| Bench revenge respect | `BossAI_ShouldRespectPotentialPlayerRevenge` (`engine/battle/ai/boss_policy_switch.asm:682`) |
| Scarf-swing possible | `BossAI_IsScarfSwingPossible` (`engine/battle/ai/boss_policy_switch.asm:746`) |
| Suspicious switch-in (coverage/pivot) | `BossAI_IsSuspiciousSwitchIn` (`engine/battle/ai/boss_policy_switch.asm:752`) |
| Immunity-pivot opportunity | `BossAI_IsImmunityPivotOpportunity` (`engine/battle/ai/boss_policy_switch.asm:794`) |
| Ace-timing hook | `BossAI_AceTimingHook` (`engine/battle/ai/boss_policy_switch.asm:852`) |
| HP gating | `BossAI_EnemyBelowOneThirdHP` (`engine/battle/ai/boss_policy_move.asm:3573`) |

### Switch-candidate risk refinement

The "OK we want to switch — which mon, accounting for plausible threats?"
layer.

| Need | Label / line |
| --- | --- |
| Refine candidate set | `BossAI_RefineSwitchCandidateForPlausibleRisk` (`engine/battle/ai/boss_policy_switch.asm:979`) |
| Per-candidate risk score | `BossAI_ComputeSwitchCandidateRisk` (`engine/battle/ai/boss_policy_switch.asm:1062`) |
| Apply to confidence | `BossAI_ApplyPlausibleRiskToSwitchConfidence` (`engine/battle/ai/boss_policy_switch.asm:1362`) |
| Plan bias on switch | `BossAI_ApplyPlanSwitchBias` (`engine/battle/ai/boss_policy_switch.asm:1593`) |
| Sack-instead-of-switch | `BossAI_ShouldSackInsteadOfSwitch` (`engine/battle/ai/boss_policy_switch.asm:1657`) |
| Wincon protection | `BossAI_IsSwitchingIntoWinconRisk` (`engine/battle/ai/boss_policy_switch.asm:2228`) |
| Mark scout pivot | `BossAI_MaybeMarkScoutPivot` (`engine/battle/ai/boss_policy_move.asm:6322`) |
| Public bench threat score | `BossAI_SeenBenchThreatScore` (`engine/battle/ai/boss_policy_move.asm:3868`) |

### Held-item / Choice locking

| Need | Label / line |
| --- | --- |
| Get own held effect | `BossAI_GetEnemyHeldEffect` (`engine/battle/ai/boss_platform.asm:970`) |
| Currently Choice-locked? Which move? | `BossAI_EnemyChoiceLockedMove` (`engine/battle/ai/boss_platform.asm:980`), `BossAI_IsChoiceHeldEffect` (`engine/battle/ai/boss_platform.asm:996`) |

### Plan / role / wincon

| Need | Label / line |
| --- | --- |
| Pick or refresh plan | `BossAI_SelectPlanIfNeeded` (`engine/battle/ai/boss_policy_move.asm:3963`) |
| Find a party mon by role tag | `BossAI_FindPartyMonByRole` (`engine/battle/ai/boss_policy_move.asm:4403`) |
| Per-boss role-bias dispatcher (reads `wTrainerClass`, jumps to per-boss branch) | `.ApplyRoleBias` (`engine/battle/ai/boss_policy_move.asm:2397`) (under `BossAI_ApplyMoveModel`) |
| Per-boss scoring branches | `.falkner` (`engine/battle/ai/boss_policy_move.asm:2455`), `.rival` (`engine/battle/ai/boss_policy_move.asm:2447`), `.chuck` (`engine/battle/ai/boss_policy_move.asm:2490`), `.jasmine` (`engine/battle/ai/boss_policy_move.asm:2497`), `.pryce` (`engine/battle/ai/boss_policy_move.asm:2508`), `.clair` (`engine/battle/ai/boss_policy_move.asm:2517`), `.will` (`engine/battle/ai/boss_policy_move.asm:2524`), `.bruno` (`engine/battle/ai/boss_policy_move.asm:2531`), `.karen` (`engine/battle/ai/boss_policy_move.asm:2538`), `.koga` (`engine/battle/ai/boss_policy_move.asm:2545`), `.champion` (`engine/battle/ai/boss_policy_move.asm:2554`) |
| Per-boss role-effect tables (consumed by the branches above) | `BossAIChuckRoleEffects` (`engine/battle/ai/boss_policy_move.asm:6362`), `BossAIJasmineRoleEffects` (`engine/battle/ai/boss_policy_move.asm:6369`), `BossAIPryceRoleEffects` (`engine/battle/ai/boss_policy_move.asm:6376`), `BossAIClairRoleEffects` (`engine/battle/ai/boss_policy_move.asm:6386`), `BossAIWillRoleEffects` (`engine/battle/ai/boss_policy_move.asm:6395`), `BossAIBrunoRoleEffects` (`engine/battle/ai/boss_policy_move.asm:6403`), `BossAIKarenRoleEffects` (`engine/battle/ai/boss_policy_move.asm:6410`), `BossAIKogaRoleEffects` (`engine/battle/ai/boss_policy_move.asm:6420`), `BossAIChampionRoleEffects` (`engine/battle/ai/boss_policy_move.asm:6429`) |

### Effect classifiers

| Need | Label / line |
| --- | --- |
| Setup effect? | `BossAI_IsSetupEffect` (`engine/battle/ai/boss_policy_move.asm:4496`), `BossAI_IsCurrentEnemySetupMove` (`engine/battle/ai/boss_policy_move.asm:4523`) |
| Status effect? | `BossAI_IsStatusEffect` (`engine/battle/ai/boss_policy_move.asm:4723`) |
| Denial effect? | `BossAI_IsDenialEffect` (`engine/battle/ai/boss_policy_move.asm:4734`) |
| Move category (phys/spec/status) | `BossAI_CurrentEnemyMoveCategory` (`engine/battle/ai/boss_platform.asm:768`) |
| Risky accuracy? | `BossAI_CurrentEnemyMoveAccuracyRisky` (`engine/battle/ai/boss_policy_move.asm:3615`) |
| Dark-shield eligible? | `BossAI_CurrentMoveDarkShieldEligible` (`engine/battle/ai/boss_platform.asm:789`) |
| Ghost-type enemy? | `BossAI_EnemyIsGhostType` (`engine/battle/ai/boss_policy_move.asm:2763`) |
| Species can evolve | `BossAI_EnemySpeciesCanEvolve` (`engine/battle/ai/boss_policy_move.asm:6149`) |
| Known item nullifies threat type | `BossAI_EnemyKnownItemNullifiesThreatType` (`engine/battle/ai/boss_policy_move.asm:6127`) |
| Static effect tables | `BossAIDenyKOEffects` (`engine/battle/ai/boss_policy_move.asm:6348`), `BossAIStatusEffects` (`engine/battle/ai/boss_policy_move.asm:6365`), `BossAIRiskyEffects` (`engine/battle/ai/boss_policy_move.asm:6375`) |

### Lookahead / multi-turn projection

| Need | Label / line |
| --- | --- |
| Apply lookahead bonuses to top-N moves | `BossAI_ApplyLookaheadToTopMoveCandidates` (`engine/battle/ai/boss_policy_move.asm:5324`) |
| Evaluate one action's lookahead | `BossAI_EvaluateActionLookahead` (`engine/battle/ai/boss_policy_move.asm:5455`) |
| Multi-turn projection (tier-based future-discounted) | `BossAI_ApplyMultiTurnProjection` (`engine/battle/ai/boss_policy_move.asm:5605`) |
| Clamp signed delta | `BossAI_ClampSignedLookaheadDelta` (`engine/battle/ai/boss_policy_move.asm:5773`) |
| Threat type / severity probes | `BossAI_GetPrimaryThreatType` (`engine/battle/ai/boss_policy_move.asm:5802`), `BossAI_GetRevealedMoveThreatTypeAndSeverity` (`engine/battle/ai/boss_policy_move.asm:5990`), `BossAI_GetTypeThreatSeverityVsEnemyMon` (`engine/battle/ai/boss_policy_move.asm:6025`), `BossAI_AdjustThreatSeverityForEnemyKnownDefense` (`engine/battle/ai/boss_policy_move.asm:6053`) |

### Tier ramp

| Need | Where |
| --- | --- |
| Tier value | `wBossAITier`, set in `engine/battle/read_trainer_attributes.asm:72,95` |
| Tier weight row | `wBossAITierWeightRow`, set at `read_trainer_attributes.asm:73,98,126` |
| Weight table | `BossAITierWeights` (`engine/battle/ai/boss_policy_move.asm:6336`) |
| Per-trainer tier ramp map | `BossAITierRampMap:51` in `data/trainers/ai_tiers.asm` (consumer: `read_trainer_attributes.asm:115`; design comment: `engine/battle/ai/boss_policy_move.asm:5029`) |
| Roll thresholds | `BossAI_GetScoutRollThreshold` (`engine/battle/ai/boss_policy_move.asm:6209`), `BossAI_GetTierPlausibleRiskWeight` (`engine/battle/ai/boss_policy_move.asm:6188`) |

### Scout / repeat tracking

| Need | Label / line |
| --- | --- |
| Has active species been scouted? | `BossAI_IsActiveSpeciesScouted` (`engine/battle/ai/boss_platform.asm:1324`) |
| Mark scouted | `BossAI_SetActiveSpeciesScouted` (`engine/battle/ai/boss_platform.asm:1338`) |
| Decide to scout | `BossAI_ShouldScout` (`engine/battle/ai/boss_policy_move.asm:6224`) |
| Same-move repeat counter | `BossAI_UpdateRepeatTracker` (`engine/battle/ai/boss_platform.asm:1358`) |
| Mark scouted if scout move | `BossAI_MarkScoutedIfScoutMove` (`engine/battle/ai/boss_policy_move.asm:6293`) |

### Helpers used everywhere

| Need | Label / line |
| --- | --- |
| Read move attribute / byte | `BossAI_GetMoveAttr` (`engine/battle/ai/boss_platform.asm:453`), `BossAI_GetMoveByte` (`engine/battle/ai/boss_platform.asm:462`) |
| Decrement pressure / severity counters | `BossAI_DecPressureB` (`engine/battle/ai/boss_policy_move.asm:3565`), `BossAI_DecThreatSeverityB` (`engine/battle/ai/boss_policy_move.asm:6141`) |

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
| `wBossAIRevealedMovesBitmapSpare` byte 0 | 1 | Bit per seen species; set after copied/temporary revealed moves, blocking four-move saturation. |
| `wBossAIRevealedMovesBitmapSpare` byte 1 | 1 | Quarantined Haki flags: spent, ace-seen, and current-turn eligibility for the Morty/Gengar prototype. |
| `wBossAIRevealedMovesBitmapSpare` byte 2 | 1 | Spare for future per-species growth. |
| `wBossAIScorePtr` | 2 | Current score-write pointer (used by `Encourage/DiscourageScoreHL`). |
| `wBossAISavedEnemyMoveStruct` | `MOVE_LENGTH` | Saved across non-destructive move probes. |
| `wBossAITemp..Temp5` | 5 | Scratch. |
| `wBossAITierWeightRow` | 1 | Row into `BossAITierWeights`; default = `wBossAITier - 1`, overridable per trainer. |
| `wBossAISpeciesUsedMoves` | `PARTY_LENGTH * NUM_MOVES` | Per-seen-species mirror of `wPlayerUsedMoves`; preserved across same-fight switches. |
| (under `BOSS_AI_TRACE`) | ~30 | Trace fields: top-3 moves/scores, pre/post move-model scores, chosen move, plan tracing, plausible mask snapshot, risk flags, lookahead bonuses. |

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
