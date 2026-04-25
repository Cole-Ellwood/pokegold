# Boss AI Spec

Date: 2026-02-14
Scope: Trainer AI behavior design for major encounters (leaders, rival, E4, champion)

## Core Policy

Target behavior: **"absurdly strong but non-cheating"**.

AI wins by legal inference and good risk management, not hidden knowledge.

## AI Tiers

### Early Tier (Badges 1-3)

- Uses obvious high-value lines and simple KO checks.
- Limited prediction depth.
- Conservative switching to avoid player confusion spikes.

### Mid Tier (Badges 4-6)

- Adds deny-KO and tempo-aware lines.
- Starts probabilistic prediction from observed player behavior.
- Uses role-aware switching with confidence gates.

### Late Tier (Badges 7-8, E4, Champion)

- Full weighted scoring model enabled.
- Stronger setup punishment and pivot discipline.
- Higher tolerance for advanced lines, but still bounded by no-cheating invariants.

## Move Scoring Model

Per legal move, compute total score:

`Total = KO + DenyKO + Tempo + SetupWindow + StatusValue + RoleBias - Risk`

Scoring components:

- `KO`: large bonus when projected KO chance is high.
- `DenyKO`: bonus for lines that prevent likely player KO next turn (protective/status/utility lines).
- `Tempo`: bonus for maintaining initiative, forcing unfavorable trades, or creating safe pivots.
- `SetupWindow`: bonus for setup only when board is safe enough (no high immediate punish probability).
- `StatusValue`: weighted by target role and encounter phase (sleep/paralysis/burn/poison value differs by context).
- `RoleBias`: mon-specific intended behavior (lead/pivot/wall/breaker/cleaner/ace).
- `Risk`: penalty for low-accuracy or high-self-punish lines unless upside is decisive.

## Switching Logic

### Confidence thresholds

- Evaluate stay-vs-switch confidence each turn.
- Suggested thresholds:
  - Early tier: switch only if confidence to improve board >= `0.80`.
  - Mid tier: >= `0.70`.
  - Late tier: >= `0.60`.

### Anti-loop cooldown

- Any mon that switches out gets a short switch cooldown.
- During cooldown, switching that same mon again requires +0.10 extra confidence.
- Forced exceptions: imminent KO prevention, immunity pivot opportunity, or scripted ace timing.

Goal: prevent repetitive pivot loops while preserving smart tactical switching.

## Prediction Logic

Prediction is probabilistic, never deterministic.

Allowed prediction inputs only:

- Seen player Pokemon species.
- Revealed player moves.
- Observed player switching patterns over the current encounter history.

Forbidden prediction inputs:

- Unseen party members.
- Unrevealed moves/items/stats.
- Future player button input.

Prediction method:

- Build weighted action priors from observed history.
- Sample from top predicted player lines (not single hard counterpick).
- Select AI action by expected value across predicted distribution.

### Current switch prediction formula

Current implementation: `engine/battle/ai/boss.asm`, `BossAI_PredictPlayerSwitch`.

The routine starts from a baseline of `10`, then applies only observed/public
state:

- If committed `wBossAIPlayerSwitchCount * 2 >= wBossAITurnsElapsed`, add `20`.
- Else if the player has switched at least once, add `10`.
- If the player's active Pokemon is not at quarter HP or lower, add `20`.
- If public/observed threat checks say the player plausibly pressures the enemy,
  add `15`.
- If the player has revealed a super-effective damaging move, subtract `10`.
- Cap final predicted switch chance at `80`.

This prediction is intentionally heuristic. Future changes should preserve the
rule that it is based on previous observations and public state, not current
hidden input.

`BossAI_RecordPlayerSwitch` must write current-turn switch observations to
pending state only. `BossAI_IncrementTurnsElapsed` commits that pending state on
the next turn before `BossAI_PredictPlayerSwitch` can consume it.

## Turn-Order Safety

Boss AI timing has a specific cheating hazard: move choice and switch/item
choice do not happen at the same point in the turn.

```mermaid
flowchart TD
    A["BattleTurn starts"] --> B["BossAI_IncrementTurnsElapsed"]
    B --> C["AIChooseMove"]
    C --> D["BossAI_ApplyMoveModel"]
    D --> E["BossAI_SelectMove"]
    E --> F["BattleMenu: player chooses action"]
    F --> G["ParsePlayerAction"]
    G --> H["BossAI_RecordPlayerSwitch if player switched"]
    H --> I["EnemyTriesToFlee / AI switch-item paths may run"]
    I --> J["DetermineMoveOrder"]
    J --> K["Moves/switches execute"]
    K --> L["UsedMoveText records revealed player moves when visible"]
```

Safety rules:

- `BossAI_SelectMove` is before player input, so move scoring cannot peek at the
  current player action unless another routine already stored unsafe state.
- `BossAI_RecordPlayerSwitch` runs during `ParsePlayerAction`, before some
  enemy switch/item logic can run later in the same turn.
- Any new state derived from `BossAI_RecordPlayerSwitch` must be pending-only
  until the next `BossAI_IncrementTurnsElapsed`.
- Revealed move tracking is safe only after the move is visibly used. Do not
  infer unrevealed moves from party data or exact private stats.

Key source anchors:

- `engine/battle/core.asm`: `BossAI_IncrementTurnsElapsed`, `AIChooseMove`,
  `BattleMenu`, `ParsePlayerAction`, `BossAI_RecordPlayerSwitch`,
  `DetermineMoveOrder`.
- `engine/battle/ai/move.asm`: `BossAI_ApplyMoveModel`,
  `BossAI_SelectMove`.
- `engine/battle/ai/items.asm`: `AI_SwitchOrTryItem`,
  `BossAI_SwitchOrTryItem`, `BossAI_OnSwitchExecuted`.
- `engine/battle/used_move_text.asm`: `BossAI_RecordRevealedPlayerMove`.
- `engine/battle/read_trainer_attributes.asm`: `LoadBossAITier`,
  `ClearBossAIState`.
- `engine/battle/ai/switch.asm`: legacy enemy switch scoring helpers. Boss
  model code should prefer boss-safe wrappers in `engine/battle/ai/boss.asm`.

## Legacy AI Scoring Interaction

Current implementation: boss trainers skip the normal AI scoring layers in
`engine/battle/ai/move.asm` and jump directly to the boss model when
`wBossAITier != 0`.

Rules:

- Keep boss move selection on the boss model unless legacy scoring has been
  audited for hidden-information reads.
- If a legacy helper needs private player information for ordinary trainers,
  gate that helper off for boss tiers or replace it with public/observed state.
- `AI_Smart_MeanLook` defensively skips `AICheckLastPlayerMon` for boss tiers
  because that helper scans hidden player party HP.
- If normal scoring is ever re-enabled for boss tiers, re-audit
  `engine/battle/ai/scoring.asm` before relying on it.

## Boss-Safe Decision Helpers

The boss model should use wrappers that avoid exact private player stats and
hidden party information:

- `BossAI_CurrentEnemyMoveHasKOPressure`: heuristic KO pressure from move power,
  public typing, STAB, type matchup, and coarse public HP bands.
- `BossAI_CurrentEnemyMovePressureScore`: shared pressure score used by move
  scoring and lookahead.
- `BossAI_PlayerHasPublicThreatVsEnemy`: revealed player moves first, then
  current public typing as a fallback.
- `BossAI_PublicEnemyFaster`: public species base-speed estimate, not exact
  runtime speed stats.
- `BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem` and
  `BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem`: type matchup without held
  item peeking.
- `BossAI_CheckAbleToSwitchSafe`: boss switch candidate check that avoids
  player hidden-information scoring.

Treat direct boss-model calls to `AIDamageCalc`, `AICompareSpeed`, or
`CheckPlayerMoveTypeMatchups` as suspect unless the caller is clearly ordinary
AI or battle resolution rather than boss decision knowledge.

## Runtime State Budget

Boss AI runtime state lives in `ram/wram.asm`, in WRAMX bank 1, because battle
code reads and writes it directly without WRAM bank switching.

Reserved block:

- Start: `wBossAITier`.
- Normal-build logical end: `wBossAIStateEnd`.
- Reserved size: `140` bytes, enforced by
  `ds 140 - (wBossAIStateEnd - wBossAITier)`.
- Current normal build: `wBossAITier = 01:d72b`,
  `wBossAIStateEnd = 01:d776`, so normal state uses `75` bytes and leaves `65`
  reserved bytes.
- Current trace field set adds `19` bytes under `BOSS_AI_TRACE`, so trace state
  would use `94` bytes and leave `46` reserved bytes.

Adding 2-3 bytes to this block is acceptable in principle, but every change must
still be build-verified because WRAMX overall has no free unreserved space.
Never move save-compatible or unrelated WRAM fields casually to make room.
For exact current addresses and byte counts, treat `docs/generated/dev_index.md`
as the source of truth; refresh it after linker outputs change.

## Implementation Checklist For Boss AI Changes

- Confirm the new signal is legal public or previously observed information.
- Decide whether the signal is same-turn unsafe. If yes, commit it only at the
  next `BossAI_IncrementTurnsElapsed`.
- Update or inspect `ClearBossAIState` coverage if adding fields.
- Check `AIChooseMove`, `AI_SwitchOrTryItem`, and execution flow for both player
  and enemy timing.
- Verify bank `0e` size and avoid moving logic into tight `Battle Core` bank
  `0f` unless necessary.
- Refresh `docs/generated/dev_index.md` after a build changes symbols.

## Known Remaining Fairness Risk

Exact battle helpers such as `AIDamageCalc` and `AICompareSpeed` remain in the
legacy AI code and battle engine. Those helpers use exact active Pokemon stats,
including private player stat values. That is stronger than a human-like
estimate when used for boss decision knowledge.

Future fix direction:

- Add boss-safe damage and speed estimators based on public species, level,
  typing, stat stages, revealed moves, and observed damage ranges.
- Keep exact helpers for ordinary AI or internal battle resolution, but do not
  use them for boss decision knowledge unless the exact value has become public
  through observed turn order or damage.
- Treat any new direct boss-model call to those exact helpers as a review
  finding unless it is deliberately documented and justified.

## Explicit No-Cheating Invariants

- AI cannot read hidden player party slots.
- AI cannot read unrevealed moves, held items, or private stat data.
- AI cannot peek player input before action lock.
- AI cannot alter RNG outcomes after decision.
- AI cannot bypass normal PP, priority, accuracy, or legality checks.
- AI cannot execute illegal move/item combinations.
- AI and player run on the same battle ruleset and damage model.

## Logging and Tuning Hooks (Design)

- Emit per-turn debug trace in development builds:
  - top 3 move scores
  - switch confidence
  - prediction distribution
  - chosen action + reason code
- Use traces to tune weights per tier without changing no-cheating invariants.
