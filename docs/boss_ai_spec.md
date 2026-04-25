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
