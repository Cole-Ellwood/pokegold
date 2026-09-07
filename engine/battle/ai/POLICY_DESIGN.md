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
- `BossAI_ApplyLookaheadToTopMoveCandidates` evaluates every selectable move before
  selection.
- `BossAI_SelectMove` commits to the best move unless a public switch-hedge
  candidate exists, then rolls weighted best versus hedge.
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


## Strategic consistency pass — 2026-09-06

A choice is useful only when it is feasible on the current board. KO scans,
damage dominance and strong-attack checks share PP/Disable/Choice/Assault Vest
availability. Public failures keep score 80 permanently; ordinary preferences
stay in 1..79. All four selectable moves receive the signed lookahead adjustment,
including potential hedge moves. This remains heuristic projection, not a
simulation of successor battle states.

Voluntary switches first pass HP and strict threat-improvement gates, then all
living bench slots compete on the same capped risk scale. Perish count 1 instead
requires a legal escape without the ordinary confidence roll; count 2 retains
preparation pressure and permits another action. The outer battle entry gates
still enforce traps and locked actions. A coarse KO estimate cannot prove an
immediate battle win against an unknown player party, so it does not override the
last safe exit.

Setup plan and projection bonuses share headroom, available-KO and board-safety
gates. A safe opportunity can arise after the first two turns. Scouting makes one
random decision per AI tick, shared by all its consumers. Four stable revealed
moves remove speculative STAB from both threat masks and fallback threat tests;
copied/transformed/tainted observations retain uncertainty. Choice-lock regret
uses only publicly seen living species.

Speed compares the boss's effective stat (plus its known Scarf) against an estimate
from public species, level, stage, status and type passives. The estimate assumes
DV 8 and omits unknown player item and badge modifiers. It uses the engine's stage
table and passive constants, including their rounding. It is not guaranteed turn
order and does not inspect private player stats.

At quarter HP, a faster boss without an available KO can consider Destiny Bond
against a revealed nonimmune damaging reply, even if neutral. Counter, Mirror
Coat and Hidden Power's placeholder type do not establish such a reply. With
incomplete observations, the public super-effective STAB prior remains a danger
estimate. This rule estimates a trade opportunity; it does not calculate lethal
damage or force the opponent to attack.

Validation uses the real-ROM cases in `tools/boss_ai_fixtures`, including paired
availability, risk, speed and Perish decisions and an independent four-move
lookahead reference. Those tests establish bounded behavior, not a win-rate gain
or globally optimal play. Joint action valuation, true successor search,
contextual outcome learning and broader natural battle comparisons remain future
work requiring evidence before another architectural change.

### Shared public damage facts

Current-move, available-moveset and lookahead KO premises use the same minimum
noncritical HP-loss estimate. Revealed-priority lethality uses the same model's
maximum incoming HP loss. Both compare with current HP; power/HP bands no longer
establish these KO premises. Known own stats/items are exact inputs; player
stats use visible species, level, stages and status with a DV8/no-unknown-item
or badge-boost prior. Outrage chooses its category from unmodified raw offenses.

The shared kernel reproduces combat's one-time joint stat truncation, screens,
item ordering/caps, per-row type rounding, deterministic type passives, fixed
damage and supported per-hit/post-roll effects. Aggregate HP loss is capped at
starting HP. Caller-owned contexts can be queried repeatedly without drift.
The earlier fixed-only helper is retired; its exact-boundary cases exercise
both surviving production consumers.

Damage amount, accuracy, priority and survival are separate facts. Accuracy zero
excludes impossible Fly/Dig hits. Psychic negation and known own Focus Band use
separate per-hit probability thresholds; Protect/Endure are future actions, not
promises inferred from transient flags. On-hit KO never means guaranteed action
success. Unknown player items are not read. Unsupported conditional effects and
copied player stats cannot fabricate outgoing KOs; incoming uncertainty remains
conservative. Multiple hits against Substitute need an explicit successor
Substitute-HP context; single hits cannot finish the real target through it.

Nonlethal pressure rewards, authored tier/style preferences, bench valuation,
continuation search and learning remain separate policy layers. Their joint
redesign and acceptance corpus follow the remaining ordered roadmap in
`audit/boss_ai_strategy_2026-09-06/next_stage_plan.md`.
