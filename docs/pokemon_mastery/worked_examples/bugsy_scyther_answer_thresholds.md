# Worked Example: Bugsy Scyther Answer Thresholds

Purpose: ground the Bugsy route map in ROM-backed damage thresholds instead of
type slogans. This is a checkpoint planning aid, not a sealed benchmark.

Mechanics profile: `romhack_gym_leader_lab`

Local evidence:

- Boss roster and levels: `data/trainers/parties.asm`
- Player checkpoint constraints:
  `tools/boss_ai_preference/threat_availability.py`
- Damage tool self-test: `python -m tools.damage_debugger.matchup --self-test`
- Damage commands use default player/trainer stat assumptions unless exact
  in-battle stats are supplied.

Expert-source framing:

- Smogon's Baton Pass guides frame pass chains around whether support reaches a
  receiver that can convert, not whether the passer did much damage:
  <https://www.smogon.com/rs/articles/baton_pass> and
  <https://www.smogon.com/dp/articles/baton_pass_chains>.
- Smogon's setup overview frames setup as a route-changing turn, not a free
  damage substitute: <https://www.smogon.com/smog/issue26/setting_up>.
- Smogon's lead article treats lead choice as a team-plan fit:
  <https://www.smogon.com/smog/issue8/leads>.

## Full-HP Damage Anchors

```text
Geodude Lv17 Rock Throw -> Scyther Lv17:
  57-68 damage, 102-121% of Scyther max HP.
  Scyther is removed from full under the default calculator assumptions.

Ariados Lv15 Giga Drain -> Geodude Lv17:
  38-45 damage, 72-85% of Geodude max HP.
  Ariados can badly damage the later Scyther remover.

Scyther Lv17 Wing Attack -> Geodude Lv17:
  7-9 damage, 13-17% of Geodude max HP.

Scyther Lv17 +2 Wing Attack -> Geodude Lv17:
  15-18 damage, 28-34% of Geodude max HP.

Quilava Lv17 Ember -> Scyther Lv17:
  32-38 damage, 57-68% of Scyther max HP.

Scyther Lv17 Wing Attack -> Quilava Lv17:
  21-25 damage, 33-40% of Quilava max HP.

Scyther Lv17 +2 Wing Attack -> Quilava Lv17:
  41-49 damage, 65-78% of Quilava max HP.
```

Reflect check:

```text
Geodude Lv17 Rock Throw -> Scyther Lv17 with boss Reflect active:
  rough estimate about 50-61%.
```

## Route Interpretation

Geodude route:

- A healthy Geodude can remove unsupported Scyther immediately under the local
  damage tool's default assumptions.
- The route is fragile before Scyther appears: Ariados Giga Drain can put
  Geodude into a much narrower role, and Ledian Reflect can turn the immediate
  removal into a two-turn damage line.
- The key planning question is not "does Geodude beat Scyther?" It is "can
  Geodude reach Scyther healthy, unscreened, and with Rock Throw available?"

Quilava route:

- Ember is strong pressure, but it is not a full-HP one-hit removal line under
  the default assumptions.
- Because Scyther is faster in the public fixture family, Quilava must price the
  Swords Dance branch. If Scyther boosts and Quilava is not near full, boosted
  Wing Attack can become the converting line.
- Quilava is a pressure route, not automatically a clean Scyther answer.

Ledian support route:

- Reflect is a real answer-changing support turn because it can change Geodude
  from immediate removal into chip plus a second required action.
- If Ledian gets Reflect before Scyther enters, re-score the Scyther answer
  instead of replaying the no-screen plan.

## Decision Recipe

When planning Bugsy:

1. Name the intended Scyther remover before choosing the lead.
2. Do not spend that remover into Ariados unless the remaining HP still covers
   Scyther's current branch.
3. Treat Ledian Reflect as support that changes the later Scyther threshold.
4. Convert full-HP ranges into current-HP ranges before giving live advice.
5. If Scyther enters unsupported and Geodude is healthy, removal is the route.
6. If Scyther enters behind Reflect, with boosts, or against a chipped answer,
   abandon the old answer label and rebuild from the actual state.

## What This Teaches

The reusable lesson is answer preservation by threshold, not by species. A
piece can be the correct answer to the ace while still being a bad early lead if
the support Pokemon can damage it or change the field enough to break the later
route.

For live advice, say:

```text
Geodude removes unsupported Scyther from full under current calc assumptions,
so preserve it from Ariados and Ledian support unless you have another Scyther
route. If Reflect lands or Geodude is chipped, re-score before calling it the
answer.
```

Do not say:

```text
Lead Geodude because it beats Scyther.
```

That statement hides the actual planning problem: Bugsy's earlier Pokemon can
change whether the Scyther answer still works when it matters.

## Unverified Before Real Turn Advice

- Exact user team, current HP, moves, items, and stats.
- Exact badge/stat/grind effects if the user's in-battle stats differ from the
  default calculator assumptions.
- Whether Reflect is active, how many turns remain, and whether Scyther has
  received boosts.
- Whether the battle state has already changed a damage threshold through crits,
  status, chip, or missed moves.
