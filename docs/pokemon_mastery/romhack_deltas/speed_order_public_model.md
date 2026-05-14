# Speed Order Public Model - 2026-05-14

Status: source-checked policy note for battle advice and boss AI.

Purpose: answer when species base Speed is enough, when exact Speed is legal,
and which local turn-order exceptions must be priced before calling a Pokemon
"faster."

## Source Facts

- Actual move order checks priority first, then Quick Claw, then Speed. Speed
  ties are random. Source: `engine/battle/core.asm`, `.use_move`,
  `.equal_priority`, `.speed_check`, and `.speed_tie`.
- Quick Claw can override ordinary Speed when its held-effect threshold rolls.
  Local item data sets Quick Claw's threshold to `60`, or 60/256.
  Sources: `engine/battle/core.asm` and `data/items/attributes.asm`.
- Choice Scarf is applied inside the turn-order Speed helper by multiplying the
  holder's battle Speed by 3/2. Source: `engine/battle/core.asm`,
  `.GetSpeedForTurnOrder`, and `docs/mechanics_changes_from_base.md`.
- Computed stats use Gen 2 DVs and Stat Exp, not modern IVs/EVs/natures.
  Non-HP stats use base stat, DV, Stat Exp term, level, and the final +5.
  Source: `engine/pokemon/move_mon.asm`, `CalcMonStatC`.
- Enemy trainer DVs are class-specific. Source: `data/trainers/dvs.asm`.
- Enemy battle stats are initialized with `b = FALSE` before `CalcMonStats`, so
  trainer enemy Stat Exp is not applied on that path. Source:
  `engine/battle/core.asm`, enemy stat fill before `.OpponentParty`.
- Local speed modifiers include stat stages, paralysis, Electric type-passive
  Speed bumps, Dragon Dance, Quiver Dance, Agility, priority, Quick Claw, and
  Choice Scarf. Sources: `docs/agent_navigation/gen2_vs_modern_mechanics.md`
  and `docs/pokemon_mastery/romhack_deltas/type_passive_route_impacts.md`.

## Practical Advice Rule

Species base Speed is a good public prior, not a proof of move order.

Use exact Speed when it is genuinely available to the advised side:

- Player-side route sheets may use the player's real party stats and the
  source-visible boss species, level, held item, and trainer-class DVs.
- In a known boss fight, enemy trainer Stat Exp should not be assumed unless a
  fixture or source path contradicts the current `b = FALSE` stat-fill path.
- During a live battle, update after visible stages, paralysis, item reveals,
  priority reveals, and impossible turn-order events.

Do not reduce live advice to base Speed when any of these can flip order:

- different levels;
- DVs or player Stat Exp;
- paralysis or Fighting-type paralysis tuning;
- Electric Speed passive;
- Speed stages from Agility, Dragon Dance, or Quiver Dance;
- priority moves;
- Quick Claw;
- Choice Scarf;
- speed ties.

## Boss AI Firewall

Ordinary boss AI must not peek at the player's exact active Speed, hidden held
item, private DVs, Stat Exp, hidden moves, reserves, or current-turn input.

Current legal public model:

- `BossAI_PublicEnemyFaster` compares public active species base Speeds.
- It may include the boss's own known Choice Scarf by checking the enemy held
  effect.
- It does not infer unrevealed player Choice Scarf from private Speed.
- `BossAI_IsScarfSwingPossible` currently returns false with the explicit note
  not to infer unrevealed player Choice Scarf from private Speed values.

Approved exception:

- `BossAI_SetupBoostHasFurtherValue` may call `AICompareSpeed` only to stop
  encouraging further Speed setup once exact active battle Speed already says
  the boss outspeeds the active player. This exception must not spread to
  damage, hidden items, hidden moves, hidden reserves, or general move choice.

Cheap improvement boundary:

- A future public "observed speed anomaly" memory could be legal only if it is
  derived from resolved public turn order and rules out priority, Quick Claw,
  stages, paralysis, and other visible modifiers. It is not a tiny immediate
  change unless it also gets trace fields and audit fixtures.

## Policy Trigger

When a route says "we are faster" or "the boss is faster," prefer a move-order
ledger over a base-Speed claim, unless every exception above is known absent or
irrelevant to the current route.
