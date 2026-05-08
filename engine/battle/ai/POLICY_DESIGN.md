# Boss AI Policy Design

Status: BOSSAI-003 accepted architecture, documented 2026-05-08.

## Architecture Decision

Use the simpler unified public-info scorer. Do not implement the archived Layer
A/Layer B CFR rewrite unless future evidence proves this source cannot meet the
feel target.

Source evidence supporting this decision:

- `BossAI_ComputePlayerPlausibleTypeMask` already builds public threat priors
  from visible species, revealed moves, and public learnability.
- `BossAI_SelectPlanIfNeeded` already tracks a readable plan id and confidence.
- `BossAI_ApplyLookaheadToTopMoveCandidates` evaluates near-top actions before
  selection.
- `BossAI_SelectMove` already picks weighted best versus second-best instead of
  always taking a deterministic argmax.
- `BossAI_PredictPlayerSwitch`, `BossAI_ApplyRepeatPenalty`, scouting, and
  switch-loop penalties already cover the practical pattern-detection lane.
- `BossAI_RefineSwitchCandidateForPlausibleRisk` already uses plausible and
  likely threat masks when choosing switch candidates.

The minimal correct BOSSAI-003 completion is therefore documentation, debugger,
and audit hardening around the current scorer, not a speculative wholesale asm
rewrite.

## Policy Promise

Bosses should look prepared because they reason from public information:

- visible species
- visible HP/status/field state
- revealed moves
- public type chart
- public learnability priors
- boss roster and leader personality
- observed player switches and repeated patterns

Bosses must not read hidden party slots, hidden moves, hidden items, direct
player input, or private menu state.

## Scoring Shape

Current source is not one literal formula, but the policy should be reviewed as
this shape:

```text
score(action) =
  immediate pressure
  + plan bias
  + public coverage/denial value
  + lookahead value
  + scout/pattern value
  - public threat risk
  - repetition/loop risk
  - bad switch-in risk
```

The `tools/boss_ai_debugger` fixture scorer mirrors this shape for review. It
is not a ROM-executed model and should not auto-land changes.

## Personality Defaults

- Early leaders may make simpler, bolder choices.
- Mid leaders should respect revealed super-effective threats and obvious
  revenge lines.
- Late leaders should preserve high-value mons, respect public hidden coverage,
  and vary near-tie choices.
- Champion-tier fights should prioritize explainable adaptation over raw STAB
  habit.

## Preference Corpus

BOSSAI-004 labels are now the taste source:

- `best` and rank-1 actions are positive examples.
- `cheap` and `bad` labels are regression warnings.
- `scary_good` labels mark behavior that should be allowed but monitored.
- `needs_context` means the fixture is under-specified and should not drive a
  source change by itself.

Before changing ROM behavior for a taste issue, add or update a fixture label
and inspect it through `tools.boss_ai_debugger`.

## Review Rules

1. No source change without a public-info explanation.
2. No black-box training output lands in asm.
3. Every new heuristic must cite a policy idea in this file or add a small
   section here.
4. Every Boss AI source change reruns the audit floor in `PLATFORM_API.md`.
