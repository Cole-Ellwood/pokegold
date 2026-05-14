# Worked Example: Brock Golem Explosion Turn-Order Quarantine

Purpose: document a benchmark that should not be promoted into a normal
Explosion heuristic until turn order is resolved. This is a useful negative
example: a route trade is not real if the user is removed before the trade
move executes.

Mechanics profile: `romhack_gym_leader_lab`

Local evidence:

- Boss roster: `data/trainers/parties.asm`, `BrockGroup`
- Public card:
  `tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`,
  `fixture_brock_golem_vs_vaporeon_explosion_question_001`
- Hidden oracle:
  `tools/boss_ai_preference/benchmarks/state_transition_oracles.json`,
  `fixture_brock_golem_vs_vaporeon_explosion_question_001`
- Fixture:
  `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`,
  `brock_golem_vs_vaporeon_explosion_question`
- Explosion source: `data/moves/moves.asm`, `EXPLOSION`,
  `EFFECT_SELFDESTRUCT`
- Explosion mechanics note: `docs/agent_navigation/gen2_vs_modern_mechanics.md`
- Turn-order mechanics note: `docs/agent_navigation/gen2_vs_modern_mechanics.md`
- Damage tool self-test: `python -m tools.damage_debugger.matchup --self-test`

Expert-source framing:

- Smogon's GSC Explosion guide explains Explosion as wallbreaking, emergency
  defense, simplification, and route trade material, but also treats it as a
  committed sacrifice that must be timed:
  <https://www.smogon.com/gs/articles/guide_to_explosion>.
- Smogon's risk/reward guide applies before the sacrifice: the wrong branch
  matters most when the cost is irreversible:
  <https://www.smogon.com/resources/beginner/bw_risk_reward>.

## Public State

```text
Boss active:
  Golem Lv60 at 42%, Rocky Helmet
  Known moves: Earthquake, Rock Slide, Explosion, Curse

Player active:
  Vaporeon Lv61 at 76%
  Revealed moves: Surf, Bite
  Public priors: Ice Beam plausible, Rest plausible

Field:
  No weather or screens
```

The hidden oracle labels Explosion as best, Omastar switch as acceptable, and
Earthquake as catastrophic. The public card also says Vaporeon has revealed
Surf and outspeeds the ordinary stay-in branch.

That creates the problem: if Vaporeon is faster and chooses Surf, Golem is
removed before a normal-priority Explosion can execute.

## Damage And Turn-Order Anchors

```text
Vaporeon Surf -> Golem at 42%:
  339-399 damage.
  408-481% of Golem's current HP.
  Guaranteed KO from the shown current HP.

Golem Explosion -> Vaporeon at 76%:
  262-308 damage.
  125-147% of Vaporeon's current HP.
  Guaranteed KO if Golem gets to move.

Golem Earthquake -> Vaporeon at 76%:
  79-94 damage.
  38-45% of Vaporeon's current HP.
  Not a KO, and it does not prevent Surf from removing Golem.

Golem Rock Slide -> Vaporeon at 76%:
  59-70 damage.
  28-33% of Vaporeon's current HP.
  Not a KO, and it does not prevent Surf from removing Golem.

Vaporeon Surf -> Omastar at 100%:
  124-146 damage.
  74-87% of Omastar's max HP.
  Omastar survives one default-profile Surf, but takes heavy damage.
```

Local source lists Explosion as `EFFECT_SELFDESTRUCT`, 250 BP, 100 accuracy,
with no priority flag. The mechanics overview says Selfdestruct / Explosion
halve target Defense during damage calculation and make the user faint; it does
not give Explosion move priority. The speed section says ordinary turn order is
based on priority first, then Speed.

## Quarantine Reason

The benchmark is useful as a preference-card memory, but it is not safe as a
mechanics-grounded strategy example until one of these is proven:

```text
Golem is faster in the exact battle state;
Vaporeon is not expected to click Surf;
Vaporeon is switching, healing, or using a non-KO move;
Explosion has a romhack-specific priority or interrupt behavior not documented
in the inspected source;
the public card's "outspeeds" language is wrong or refers to something else.
```

Without one of those facts, the actual live branch is:

```text
Vaporeon uses Surf -> Golem faints -> Explosion never happens.
```

That means the route trade cannot be scored as "Explosion removes Vaporeon"
from the public state alone.

## What Still Transfers

The general Explosion lesson remains valid:

```text
Explosion is good when it removes or cripples the piece blocking a named route,
and the lost role is already discharged, replaceable, or worth spending.
```

But this card adds a prior legality gate:

```text
Can the sacrifice move actually execute before the opponent removes, blocks, or
invalidates it?
```

If the answer is no, the move is not a route trade. It is a failed plan.

## Provisional Advice For This State

Do not use this card as proof that Golem should Explode into Vaporeon from this
state. Treat it as unresolved.

From public mechanics alone:

1. Earthquake and Rock Slide are poor because Surf removes Golem and neither
   attack removes Vaporeon.
2. Explosion would be decisive only if Golem moves or Vaporeon does not attack.
3. Switching to Omastar is costly but at least executes under the Surf branch.
4. The real recommendation needs exact turn order, player likely action, and
   whether preserving Golem still matters for Machamp or another remaining
   route.

## Transfer Lesson

Before applying "Explosion converts," check the execution gate:

```text
priority / speed / Quick Claw / paralysis / sleep / full paralysis / Protect /
Ghost or other block / target switch / damage before action
```

A sacrifice heuristic that skips this gate can produce confident nonsense. The
right review response is not to make the prose sound better; it is to quarantine
the card until source, debugger trace, or a corrected public state resolves the
branch.

## Unverified Before Real Turn Advice

- Exact Golem and Vaporeon Speed in the user's battle state.
- Whether Vaporeon is actually expected to use Surf this turn.
- Whether Vaporeon has Protect, Rest, or another answer-changing fourth move.
- Whether Omastar's HP/item/current status makes the switch branch viable.
- Whether Golem is still needed for Machamp or another remaining physical route.
