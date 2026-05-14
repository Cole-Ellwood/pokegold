# Worked Example: Red 30-Turn Final-Boss Ledger Drill

Purpose: practice a full-route final boss ledger against a constructed Red
battle. This drill trains turn-1 game planning, answer reservation, route
handoff, screen/setup denial, RestTalk anchor control, sun-window management,
priority range, Mirror Coat punishment, and plan revision after the lead
exchange changes the rest of the fight.

Local evidence:

- Red route map: `../boss_route_maps/red_turn1_route_sheet.md`.
- Red pre-battle route sheet: `red_pre_battle_route_sheet.md`.
- Snorlax context: `../romhack_deltas/snorlax_context.md`.
- Mechanics overview and generated mechanics reference:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.
- Local source paths named in the route sheet: `data/trainers/parties.asm`,
  `data/moves/moves.asm`, `data/moves/critical_hit_moves.asm`,
  `data/battle/critical_hit_chances.asm`,
  `engine/battle/effect_commands.asm`,
  `engine/battle/move_effects/sunny_day.asm`, and
  `engine/battle/move_effects/mirror_coat.asm`.

Expert study anchors:

- Smogon win-condition material: choose lines by the endgame they make
  possible, not by the active matchup alone:
  <https://www.smogon.com/forums/threads/knowing-how-to-find-your-win-condition.3474271/>.
- Smogon risk/reward material: when a later route can become irreversible,
  worst plausible branches matter more than shallow expected value:
  <https://www.smogon.com/resources/beginner/bw_risk_reward>.
- Smogon battle-conditions material: screens and weather are temporary battle
  conditions that change move value for both sides:
  <https://www.smogon.com/dp/articles/battle_conditions>.
- Smogon long-term thinking material: the lead exchange is good only if it
  preserves the pieces needed for the planned win route:
  <https://www.smogon.com/rs/articles/long_term_thinking>.

## Starting Position

Use Red's known roster:

```text
Pikachu:
  ExtremeSpeed / Thunderbolt / Razor Leaf / Surf

Espeon:
  Reflect / Morning Sun / Calm Mind / Psychic

Snorlax:
  Curse / Sleep Talk / Rest / Body Slam

Venusaur:
  Sunny Day / Sludge Bomb / Synthesis / SolarBeam

Charizard:
  Flamethrower / Wing Attack / Sunny Day / SolarBeam

Blastoise:
  Earthquake / Surf / Blizzard / Mirror Coat
```

Assume the user has six team jobs, not exact species:

```text
Pikachu lead answer:
  survives or punishes Light Ball special coverage and ExtremeSpeed range

Espeon denial:
  stops Reflect / Calm Mind / Morning Sun from becoming a protected setup route

Snorlax anchor answer:
  phaze, Haze, strong pressure, Fighting-style pressure, PP plan, status-before-
  Rest, or a concrete sacrifice route

sun plan:
  handles Venusaur and Charizard after Sunny Day changes Fire, Water,
  SolarBeam, and recovery math

Blastoise plan:
  avoids or exploits Mirror Coat while covering Earthquake / Surf / Blizzard

flex resource:
  one sacrifice, priority/revenge line, status absorber, weather stall, or safe
  entry creator
```

The drill begins before turn 1. Write one full route map before choosing a
lead. The first answer must name which piece is *not* allowed to take Pikachu
chip because it is needed later.

## Ledger Fields

At every checkpoint, write these fields:

```text
turn window:
our route:
Red route:
Pikachu priority / coverage state:
Reflect turns:
Espeon Calm Mind state:
Snorlax Curse / Rest / Sleep Talk state:
sun turns:
Venusaur recovery / SolarBeam state:
Charizard sun pressure:
Blastoise Mirror Coat risk:
our irreplaceable pieces:
piece now expendable:
current worst plausible branch:
what would change the plan:
next move class:
```

The ledger should answer one question repeatedly:

```text
Did this move solve the active threat without damaging the answer to Red's next
known route?
```

## Drill

### Turns 1-3: Pikachu Lead Exchange

Question:

- Can the user beat or force Pikachu without spending the Snorlax, Espeon, sun,
  or Blastoise answer?

Serious candidate classes:

- attack if damage removes Pikachu or forces it below useful priority range;
- pivot if the pivot survives Surf, Razor Leaf, Thunderbolt, and ExtremeSpeed
  while preserving later roles;
- status only if the miss/status-immunity branch does not expose a later
  irreplaceable answer;
- sacrifice only if the next entry creates a stronger route than the role lost.

Branch injectors:

- Pikachu uses Thunderbolt.
- Pikachu uses Surf into a Ground/Rock-style answer.
- Pikachu uses Razor Leaf and the high-crit branch matters.
- Pikachu uses ExtremeSpeed into a low-HP cleaner or revenge route.

Ledger test:

- Record whether Pikachu's move changed the route map, not just HP.
- If Razor Leaf is relevant, classify the line by variance budget.
- If the lead is now low, decide whether it is still an answer, a sack, or a
  one-hit converter.

Failure signs:

- Overcommitting the Snorlax or Espeon answer to win the lead exchange.
- Treating a type label as proof against Pikachu coverage.
- Forgetting ExtremeSpeed range after Pikachu survives.

### Turns 4-7: Espeon Screen / Setup Fork

Question:

- Does Espeon turn the post-lead board into a Reflect or Calm Mind route?

Serious candidate classes:

- attack through the category not blocked by the active screen;
- phaze/Haze/status if Calm Mind would make damage collapse;
- pivot only if the pivot does not give Espeon a free Morning Sun reset;
- sacrifice only if the next entry immediately denies the boosted route.

Branch injectors:

- Espeon sets Reflect.
- Espeon uses Calm Mind.
- Espeon uses Morning Sun and erases shallow chip.
- Espeon attacks and puts the planned Snorlax answer below threshold.

Ledger test:

- If Reflect appears, start a five-turn counter.
- If Calm Mind appears, update both damage taken and damage dealt by Espeon.
- If Morning Sun resets the race, mark the previous damage as fake progress
  unless it bought position, PP, status, or a forced entry.

Failure signs:

- Attacking physically through Reflect with no threshold gain.
- Letting Calm Mind sit because Espeon is not Red's ace.
- Spending the Snorlax answer as the Espeon pivot without replacement.

### Turns 8-13: Snorlax Anchor Route

Question:

- Is Red's Snorlax becoming the real endgame clock?

Serious candidate classes:

- deny Curse before Body Slam and RestTalk make the answer map collapse;
- force Rest only if the user can punish Sleep Talk branches;
- phaze/Haze if the control tool is still reliable and worth spending now;
- trade or sacrifice only if it opens a concrete route that removes or
  neutralizes Snorlax before it converts.

Branch injectors:

- Snorlax uses Curse.
- Snorlax uses Body Slam and paralyzes the answer.
- Snorlax Rests.
- Sleep Talk calls Body Slam, Curse, or Rest.

Ledger test:

- After every Curse, rewrite damage and Speed assumptions.
- If Rest happens, write the exact punishment through possible Sleep Talk calls.
- If Body Slam paralysis lands, relabel the affected Pokemon's remaining job.

Failure signs:

- Calling Rest a free turn while Sleep Talk can still act.
- Treating "we have a Snorlax answer" as true after it is paralyzed, chipped,
  or low on PP.
- Spending the phazer/Haze user earlier and noticing only after Snorlax boosts.

### Turns 14-18: Sun Route Collision

Question:

- Do Venusaur or Charizard own the next five turns?

Serious candidate classes:

- deny Sunny Day if Water damage or clear-weather recovery is part of the plan;
- burn sun turns only if each turn does not create a worse entry for Red;
- attack if damage forces Venusaur/Charizard out or prevents a recovery reset;
- pivot only through pieces that survive both the obvious STAB and SolarBeam or
  coverage under local type/passive evidence.

Branch injectors:

- Venusaur uses Sunny Day.
- Venusaur uses Synthesis under sun.
- Charizard uses Sunny Day.
- Charizard attacks through the expected Water answer with SolarBeam or Wing
  Attack / Flamethrower.

Ledger test:

- Count sun from five.
- Re-rank Water, Fire, SolarBeam, Synthesis, Morning Sun, and weather-dependent
  recovery under local mechanics.
- If sun expires, stop using the sun route as the current explanation.

Failure signs:

- Switching a Water answer into sun because it was correct in clear weather.
- Repeating chip that Synthesis erases.
- Forgetting Charizard and Venusaur can both create or exploit sun.

### Turns 19-23: Blastoise Mirror Coat Check

Question:

- Can the user pressure Blastoise without handing Mirror Coat the decisive KO?

Serious candidate classes:

- use physical or mixed pressure if it changes the route without Mirror Coat
  risk;
- use special damage only if the Mirror Coat branch is survivable, blocked, or
  less important than the route gained;
- pivot if Blastoise's coverage would remove the intended attacker;
- sacrifice only if the next entry forces Blastoise out or removes it.

Branch injectors:

- Blastoise uses Mirror Coat into a special attack.
- Blastoise attacks instead with Surf, Blizzard, or Earthquake.
- The user's physical answer is also needed for Snorlax.
- The user's special nuke is the only way to stop Blastoise in time.

Ledger test:

- Before every special attack, write the Mirror Coat branch.
- If Blastoise attacks instead of Mirror Coat, record which coverage move
  changed the pivot map.
- If a sacrifice creates entry, name the route that entry opens.

Failure signs:

- "Special damage hits harder" without pricing Mirror Coat.
- Spending the Snorlax answer to solve Blastoise after Snorlax remains live.
- Pivoting into Blastoise coverage by type memory instead of damage evidence.

### Turns 24-27: Route Handoff Audit

Question:

- Which Red route is still live, and which user answer has become overloaded?

Serious candidate classes:

- preserve an answer if it still blocks the only live Red route;
- spend an answer if its route is dead and it creates the next clean entry;
- attack if it creates a forced KO, forced recovery, or endgame simplification;
- recover or stall only if the healed piece remains a blocker or converter.

Branch injectors:

- Pikachu survives and can still ExtremeSpeed.
- Espeon or Venusaur can recover through shallow damage.
- Snorlax remains alive but the answer has been weakened.
- Blastoise or Charizard is the last route blocker.

Ledger test:

- Mark every remaining Pokemon as `converter`, `blocker`, `sack`, or `spent`.
- Write the next two turns for the best move and the safest move.
- If the safest move still loses, choose the risk that creates a real winning
  branch and label it forced risk.

Failure signs:

- Trying to preserve every Pokemon instead of converting.
- Sacrificing a piece whose last job is still live.
- Treating Red's remaining roster as isolated one-on-ones instead of route
  handoffs.

### Turns 28-30: Final-Boss Review

Question:

- Did the turn-1 plan survive contact with Red's route handoffs?

Review output:

```text
turn-1 plan:
first route that appeared:
first plan revision:
earliest route loss:
piece preserved correctly:
piece spent correctly:
worst branch priced correctly:
worst branch ignored:
final route that decided the game:
one answer-changing information item:
```

Endgame rule:

- Red is won by route sequencing. A move that beats the active Pokemon is wrong
  if it makes Snorlax, Espeon, sun, Blastoise, or surviving Pikachu priority
  unanswerable. A move that looks passive is correct if it preserves the only
  real answer and forces Red's next route to arrive on worse terms.

## Pass Conditions

- The ledger tracks Pikachu coverage/priority, Reflect, Calm Mind, Snorlax
  Curse/Rest/Sleep Talk, sun turns, recovery, Blastoise Mirror Coat, and
  priority range without dropping a route.
- The plan states a turn-1 win route and revises it after the first surprise.
- Every sacrifice names the route it opens and the route it closes.
- Every recovery or setup turn is labeled as reset, punish, or conversion.
- Every type, weather, item, or damage claim is tied to romhack evidence when
  it affects the move choice.
- The review identifies the earliest route loss, not only the final faint.

## Extracted Lesson

Red is the final-boss version of Pokemon planning. It is not enough to beat the
active Pokemon; the player must keep the future route map intact. Pikachu tests
lead discipline, Espeon tests screen/setup denial, Snorlax tests anchor
preservation, Venusaur and Charizard test weather ownership, Blastoise tests
punish-branch discipline, and surviving priority tests endgame thresholds. The
mastery skill is route handoff: knowing which threat Red is trying to pass the
game to next, and making each move preserve or improve the answer to that next
route.
