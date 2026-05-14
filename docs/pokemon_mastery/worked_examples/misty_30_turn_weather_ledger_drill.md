# Worked Example: Misty 30-Turn Weather Ledger Drill

Purpose: practice a full long-game ledger against a constructed Misty battle
where the central question is who owns the weather clock. This drill trains
adaptive lead planning, rain-turn accounting, sleep branch pricing, Recover and
Rest punishment, Curse denial, paralysis budgeting, and separate-answer
preservation.

Local evidence:

- Misty route map: `../boss_route_maps/misty_turn1_route_sheet.md`.
- Misty pre-battle route sheet: `misty_pre_battle_route_sheet.md`.
- Weather clock worked example: `weather_clock_boss_examples.md`.
- Mechanics overview and generated mechanics reference:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.
- Local weather sources named in the route sheet:
  `engine/battle/move_effects/rain_dance.asm`,
  `engine/battle/move_effects/thunder.asm`, and
  `engine/battle/effect_commands.asm`.

Expert study anchors:

- Smogon Rain Offense material: manual rain is a finite offensive timer, so
  every switch, miss, recovery turn, and sacrifice must be judged by whether it
  converts before rain expires:
  <https://www.smogon.com/dp/articles/rain_offense>.
- Smogon battle conditions material: weather is a field condition that changes
  damage, accuracy, recovery, and move value:
  <https://www.smogon.com/resources/beginner/battle_conditions>.
- Smogon long-term thinking material: do not solve only the active Pokemon;
  identify the route the rest of the team is trying to open:
  <https://www.smogon.com/rs/articles/long_term_thinking>.
- Smogon risk/reward material: a rain turn can be worth accepting risk if safe
  play only lets the opponent convert the weather window:
  <https://www.smogon.com/resources/beginner/bw_risk_reward>.

## Starting Position

Use Misty's known roster:

```text
Politoed:
  Rain Dance / Hypnosis / Surf / Ice Beam

Starmie:
  Recover / Hydro Pump / Psychic / Thunder

Quagsire:
  Curse / Earthquake / Surf / Rest

Lapras:
  Rain Dance / Surf / Ice Beam / Thunder

Lanturn:
  Thunder Wave / Surf / Thunder / Ice Beam
```

Misty has an adaptive first-three opening:

```text
possible openers:
  Politoed / Starmie / Quagsire
```

Assume the user has six team jobs, not exact species:

```text
adaptive lead:
  can take a useful first turn into Politoed, Starmie, or Quagsire

rain buffer:
  can spend rain turns without losing the long-game route

Starmie answer:
  can handle speed, Recover, Wise Glasses damage, and rain Thunder pressure

Quagsire answer:
  can deny or punish Curse / Earthquake / Surf / Rest

status plan:
  can absorb or mitigate Hypnosis and Thunder Wave without losing the route

converter:
  can punish a rain setup turn, forced Recover, Rest sleep, or a paralyzed
  Misty piece
```

The drill begins before turn 1. Write three opening plans: one if Misty opens
Politoed, one if Misty opens Starmie, and one if Misty opens Quagsire.

## Ledger Fields

At every checkpoint, write these fields:

```text
turn window:
our route:
Misty route:
Misty opener or active route:
rain turns:
our irreplaceable pieces:
Misty irreplaceable pieces:
Sleep Clause and sleeping Pokemon:
Thunder Wave state:
Starmie Recover pressure:
Quagsire Curse / Rest state:
Lapras rain reset state:
Lanturn paralysis route:
current worst plausible branch:
what would change the plan:
next move class:
```

The ledger should answer one question repeatedly:

```text
Did this turn make rain convert, expire, or fail to matter?
```

## Drill

### Turns 1-3: Adaptive Opener Test

Question:

- Does the first move work into Politoed, Starmie, and Quagsire, or is it only
  good against one expected lead?

Serious candidate classes:

- attack Politoed if the damage denies rain, prices Hypnosis, or forces an
  early trade;
- pressure Starmie if the move crosses a threshold before Recover matters;
- deny Quagsire Curse if the special or phazing answer is not yet established;
- pivot only if the pivot preserves the separate Starmie and Quagsire answers.

Branch injectors:

- Misty opens Politoed and threatens Rain Dance or Hypnosis.
- Misty opens Starmie and the recovery-pressure route is immediate.
- Misty opens Quagsire and Curse is the first route.

Ledger test:

- If the opener differs from the expected one, abandon the script immediately.
- Write which later Misty route the first move made easier or harder.
- Mark any lead whose job is now complete, narrowed, or still irreplaceable.

Failure signs:

- Building a Politoed-only plan and losing turn 1 to Starmie or Quagsire.
- Treating rain/sleep as the whole fight while Quagsire starts Curse.
- Attacking for chip that Recover or Rest will erase without compensation.

### Turns 4-7: Rain Ownership Window

Question:

- If rain starts, can the player make Misty spend the five turns poorly?

Serious candidate classes:

- punish Rain Dance immediately if Politoed or Lapras gave up tempo;
- pivot to burn rain turns only if the pivot remains useful afterward;
- force Recover, Rest, or a low-value coverage move during rain;
- attack if the damage creates a KO, recovery threshold, or safe entry before
  rain payoff.

Branch injectors:

- Politoed sets Rain Dance.
- Lapras resets rain after Politoed is gone.
- Starmie enters with rain active.
- Lanturn threatens rain Thunder plus Thunder Wave.

Ledger test:

- Count rain from five, and decrement it after every turn that passes.
- Mark whether each rain turn produced damage, forced a switch, caused a status
  problem, got wasted by Recover/Rest, or expired without payoff.
- Re-rank Fire damage, Water damage, and Thunder reliability under local
  mechanics.

Failure signs:

- Treating rain as just "their Water is stronger" instead of a turn budget.
- Spending every rain turn switching while the real answer gets chipped.
- Forgetting Lapras can restart the weather clock.

### Turns 8-12: Hypnosis And Status Budget

Question:

- Which status can the user afford to absorb, and which one breaks the route?

Serious candidate classes:

- use an expendable or already-narrowed piece to absorb Hypnosis only if its
  remaining job is replaceable;
- preserve the Starmie or Quagsire answer if sleep would remove its only job;
- attack after a Hypnosis miss only if the miss creates immediate route
  progress;
- keep the speed-control piece away from Lanturn if Thunder Wave makes the
  endgame unwinnable.

Branch injectors:

- Hypnosis hits the intended absorber.
- Hypnosis hits the wrong irreplaceable piece.
- Hypnosis misses and Politoed remains active.
- Lanturn paralyzes the cleaner or Starmie answer.

Ledger test:

- Mark every statused Pokemon as `still live`, `narrowed`, or `spent`.
- If Sleep Clause is now occupied, write whether that makes Jynx-style future
  sleep irrelevant in this fight or whether the sleeping piece was too costly.
- If paralysis lands, re-rank every Speed-dependent route.

Failure signs:

- Calling a sleeping Pokemon expendable because it is asleep, not because its
  job is replaceable.
- Treating a miss as a free setup turn without pricing Politoed's next move.
- Ignoring Thunder Wave because it did little immediate damage.

### Turns 13-17: Starmie Recovery Anchor

Question:

- Is the player actually making progress into Starmie, or only feeding Recover
  turns?

Serious candidate classes:

- attack if the damage forces Starmie below a threshold that Recover cannot
  safely erase;
- status if legal and if the status changes Starmie's ability to switch,
  Recover, or outpace the team;
- pivot to a stronger answer before Starmie converts rain or coverage;
- use a sacrifice only if the next entry forces a route Starmie cannot Recover
  through.

Branch injectors:

- Starmie uses Recover after weak chip.
- Starmie attacks instead of Recovering and reveals the important coverage.
- Starmie enters during rain and Thunder bypasses the accuracy check.
- Starmie is forced low enough that Recover becomes predictable.

Ledger test:

- Write whether Recover reset the exchange or gave the player a punish turn.
- Count any PP or damage threshold that makes repeated Recover worse for
  Misty.
- If the Starmie answer is also the Lapras answer, note that shared-load risk.

Failure signs:

- Repeating damage that always gets recovered.
- Treating Starmie as beaten because it was forced to Recover once.
- Spending the only Lapras answer to win a temporary Starmie exchange.

### Turns 18-22: Quagsire Curse / Rest Anchor

Question:

- Has Misty shifted from weather offense to physical-anchor pressure?

Serious candidate classes:

- deny Curse before boosted Earthquake changes the answer map;
- use special pressure, phazing, Haze, status, or a forced trade if available;
- punish Rest only if the player can convert during the sleep turns;
- preserve the Quagsire answer even if Starmie is the flashier threat.

Branch injectors:

- Quagsire gets one Curse.
- Quagsire gets a second Curse because the player chased rain turns.
- Quagsire Rests and the player has or lacks a punish.
- The Quagsire answer was spent earlier as the rain buffer.

Ledger test:

- After every Curse, rewrite the threat-answer map.
- If Rest happens, write the exact two-turn punishment plan.
- If no punishment exists, label Rest as Misty progress, not player progress.

Failure signs:

- Treating Misty as only special Water pressure.
- Calling Rest a free turn without a concrete punish.
- Losing the Quagsire answer while trying to solve Starmie and Lapras.

### Turns 23-27: Lapras And Lanturn Route Bridge

Question:

- Is the endgame being decided by rain reset, paralysis, or shared-answer
  overload?

Serious candidate classes:

- deny Lapras rain reset if the team cannot handle another five-turn weather
  window;
- preserve the piece that handles both Lapras coverage and Starmie pressure, if
  no substitute exists;
- prevent Lanturn from paralyzing the only cleaner or revenge route;
- trade only if the trade leaves enough material to beat the remaining anchor.

Branch injectors:

- Lapras uses Rain Dance after Politoed's rain expired.
- Lapras attacks under rain and forces a defensive answer below its next role.
- Lanturn uses Thunder Wave.
- The user's faster cleaner is now in range but still needs to beat one more
  Misty piece.

Ledger test:

- Mark whether Lapras is a fresh weather owner or only a bulky attacker.
- Mark whether Lanturn's value is damage, paralysis, or absorbing the user's
  converter.
- If one answer covers Starmie, Lapras, and Lanturn, decide which one must be
  handled by a different route.

Failure signs:

- Relaxing after Politoed is gone and letting Lapras restart the fight.
- Letting Lanturn paralyze the only remaining speed plan.
- Expecting one tired Water answer to cover every remaining Water.

### Turns 28-30: Weather Endgame Audit

Question:

- Which side converted the weather clock into a forced endgame?

Possible deciding resources:

- rain turns remaining;
- Sleep Clause and wake timing;
- Starmie Recover PP or threshold;
- Quagsire Curse boosts and Rest state;
- Lapras ability to reset rain;
- Lanturn Thunder Wave state;
- the next safe entry after a faint;
- whether the user still has distinct answers or only one overloaded pivot.

Review output:

```text
earliest route loss:
rain turn most wasted by Misty:
rain turn most wasted by us:
status branch that changed the route:
shared-answer overload:
best recovery punish:
one answer-changing information item:
```

Endgame rule:

- The right move is the one that either converts the remaining rain turns into a
  forced win, or prevents Misty from converting them. If weather is over, stop
  playing as though rain still decides the fight and re-rank Starmie, Quagsire,
  Lapras, and Lanturn as ordinary route pieces.

## Pass Conditions

- The ledger tracks adaptive opener, rain turns, Hypnosis, Thunder Wave,
  Starmie Recover, Quagsire Curse/Rest, Lapras rain reset, and Lanturn route
  pressure without dropping a clock.
- The plan changes when Misty opens a different first-three Pokemon than
  expected.
- Every rain turn is classified as converted, wasted, or neutral for both
  sides.
- Every recovery turn is labeled as reset, punish, or route conversion.
- Every statused player piece is relabeled by remaining job, not by HP alone.
- Every Electric, Grass, Water, Ice, or Ground claim is tied to romhack
  evidence when it drives the move choice.
- The review identifies the earliest route loss, not only the final KO.

## Extracted Lesson

Misty is the weather version of long-game route discipline. Rain is not just a
damage boost; it is a five-turn contract. Misty wins when those turns become
Starmie pressure, Lapras extension, reliable Thunder, sleep/paralysis tempo, or
Quagsire space. The player wins when rain turns are forced into Recover, Rest,
bad coverage, switches, or expired pressure while separate answers to Starmie,
Quagsire, Lapras, and Lanturn remain alive. The mastery skill is deciding
whether to punish weather now, burn its turns, or abandon the weather fight
because a different anchor has become the real route.
