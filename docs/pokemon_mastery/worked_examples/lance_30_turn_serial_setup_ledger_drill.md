# Worked Example: Lance 30-Turn Serial Setup Ledger Drill

Purpose: practice a full long-game ledger against a constructed Lance battle
where the central problem is serial setup denial. This drill trains answer
budgeting across repeated Dragon Dance / Quiver Dance waves, local Outrage
category checks, speed-order updates, Focus Band branches, recharge punishment,
and final-answer preservation.

Local evidence:

- Lance route map: `../boss_route_maps/lance_turn1_route_sheet.md`.
- Lance pre-battle route sheet: `lance_pre_battle_route_sheet.md`.
- Mechanics overview and generated mechanics reference:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.
- Outrage effective-category and type-passive source:
  `engine/battle/type_passive_damage_mods.asm`.
- Local roster source: `data/trainers/parties.asm`, `ChampionGroup` /
  `LANCE`.

Expert study anchors:

- Smogon setup-move material: Dragon Dance is dangerous because it improves
  both offensive pressure and Speed, so a free turn can decide the whole route:
  <https://www.smogon.com/smog/issue26/setting_up>.
- Smogon setup-sweeper material: setup users become strongest after their
  checks have been removed or weakened:
  <https://www.smogon.com/articles/ou-setup-sweepers>.
- Smogon long-term thinking material: preserve the piece that makes the future
  route possible, even when an earlier trade looks attractive:
  <https://www.smogon.com/rs/articles/long_term_thinking>.
- Smogon risk/reward material: when a boosted sweeper threatens an irreversible
  route, the worst plausible branch can dominate average value:
  <https://www.smogon.com/resources/beginner/bw_risk_reward>.

## Starting Position

Use Lance's known roster:

```text
Steelix:
  Earthquake / Iron Tail / Outrage / Dragon Dance

Gyarados:
  Dragon Dance / Outrage / Hydro Pump / Hyper Beam

Ampharos:
  Thunder / Outrage / Fire Punch / Dragon Dance

Yanma:
  Quiver Dance / Outrage / Giga Drain / Sleep Powder

Kingdra:
  Surf / Outrage / Blizzard / Dragon Dance

Dragonite:
  Dragon Dance / Outrage / Earthquake / Hyper Beam
```

Assume the user has six team jobs, not exact species:

```text
lead pressure:
  can deny or punish Steelix's first Dragon Dance

anti-setup control:
  phaze, Haze, status, Encore, strong immediate damage, or forced trade

speed control:
  revenge, priority, paralysis, or a pivot that still works after +1 Speed

mixed Dragon answer:
  survives the relevant Outrage category and coverage from Gyarados or Kingdra

Yanma safety plan:
  handles Sleep Powder, Quiver Dance, Giga Drain, and Focus Band survival

final Dragonite route:
  must remain live after Steelix, Gyarados, Ampharos, Yanma, and Kingdra
```

The drill begins before turn 1. Write a threat-answer graph for all six Lance
Pokemon, then mark which player piece is allowed to be spent before Dragonite
appears.

## Ledger Fields

At every checkpoint, write these fields:

```text
turn window:
our route:
Lance route:
active Lance setup threat:
boost state and speed relation:
Outrage category evidence:
Outrage rampage turns:
Hyper Beam recharge state:
Yanma Focus Band / sleep state:
our irreplaceable pieces:
Lance irreplaceable pieces:
anti-setup tools remaining:
final Dragonite route:
current worst plausible branch:
what would change the plan:
next move class:
```

The ledger should answer one question repeatedly:

```text
Did this move stop the current setup wave without spending the answer needed
for the next one?
```

## Drill

### Turns 1-3: Steelix First Setup Test

Question:

- Can the opener pressure Steelix without spending the final anti-Dragon route?

Serious candidate classes:

- attack if damage denies Dragon Dance, forces Steelix out, or creates a later
  revenge threshold;
- status only if accuracy, immunity, and future Dragonite value are priced;
- phaze/Haze only if the control tool is not needed more urgently later;
- pivot only if Steelix cannot boost into an unanswerable Speed or damage state.

Branch injectors:

- Steelix uses Dragon Dance immediately.
- Steelix attacks the expected answer.
- Steelix uses Outrage and starts a rampage lock.
- The lead wins the Steelix exchange but becomes too low for its later job.

Ledger test:

- If Steelix boosts, update the local higher-offense boost plus Speed relation.
- If Outrage starts, record category evidence and rampage turn count.
- If the anti-setup piece is used, mark whether it can still answer Dragonite.

Failure signs:

- Treating Steelix like vanilla Steel/Ground without local typing evidence.
- Spending the only phazer/Haze/status route on Steelix when another line
  preserves it.
- Winning turn 1 while losing the final Dragonite map.

### Turns 4-7: Gyarados And Ampharos Fork

Question:

- Which midgame Dragon Dance user changes the answer map first?

Serious candidate classes:

- preserve the Gyarados answer if Hyper Beam or physical Outrage can break
  through the usual Water pivot;
- preserve the Ampharos answer if Magnet Thunder or Fire Punch breaks the
  physical-wall plan;
- force a boosted user into Outrage or Hyper Beam only when the follow-up
  punishment is concrete;
- sacrifice only if the next entry removes the boosted route.

Branch injectors:

- Gyarados Dragon Dances.
- Gyarados uses Hyper Beam and either KOs or enters recharge.
- Ampharos Dragon Dances and becomes a special-plus-Speed route.
- Ampharos reveals Fire Punch or Thunder damage that invalidates the planned
  pivot.

Ledger test:

- Do not group Gyarados and Ampharos under one "Dragon Dance answer."
- Record whether the boost changed Attack or Special Attack under local rules.
- If Hyper Beam recharges, name the exact punish before relying on it.

Failure signs:

- Pivoting a physical wall into boosted Ampharos by move-name memory.
- Assuming Hyper Beam is safe to bait when the hit removes the punish piece.
- Treating the first Dragon Dance user as the only setup wave.

### Turns 8-12: Yanma Tempo Disruption

Question:

- Does Yanma steal the anti-setup turn with sleep, speed, or Focus Band?

Serious candidate classes:

- remove Yanma immediately if the Focus Band branch remains survivable;
- use sleep absorption only if the target's later job is replaceable;
- prevent Quiver Dance if special bulk and Speed would make Yanma self-sufficient;
- avoid status or setup lines that lose if Sleep Powder lands first.

Branch injectors:

- Yanma uses Sleep Powder.
- Yanma Quiver Dances.
- Yanma survives through Focus Band at 1 HP.
- Yanma attacks into the expected sleep pivot and changes its threshold.

Ledger test:

- If Focus Band triggers, discard the KO script and rebuild from live Yanma.
- If Sleep Powder lands, relabel the sleeping Pokemon by remaining job.
- If Yanma boosts, update both special bulk and Speed, not just damage.

Failure signs:

- Treating Focus Band as too unlikely to mention when the branch is severe.
- Calling a sleeping anti-setup piece expendable without proving replacement.
- Forgetting that Quiver Dance also changes Yanma's ability to survive special
  counterplay.

### Turns 13-17: Kingdra Mixed Anchor

Question:

- Is Kingdra forcing the player to spend the Dragonite answer before Dragonite?

Serious candidate classes:

- deny Dragon Dance before Surf, Blizzard, or Outrage crosses thresholds;
- use the Kingdra-specific answer if it is distinct from the Dragonite answer;
- force Rest-like or lock-like downtime only if the player can convert;
- trade only if the remaining roster still covers Dragonite.

Branch injectors:

- Kingdra Dragon Dances.
- Kingdra attacks with Surf or Blizzard instead of setting up.
- Kingdra uses Outrage and reveals effective category evidence.
- The intended Kingdra answer is also the only Dragonite answer.

Ledger test:

- Write whether Kingdra is attacking the physical, special, or mixed side after
  each reveal.
- If one piece answers both Kingdra and Dragonite, decide which threat must be
  solved by a different route.
- Do not spend the final route unless the remaining Lance pieces are already
  covered.

Failure signs:

- Treating Kingdra as a smaller Dragonite.
- Ignoring Blizzard/Surf while overfocusing on Outrage.
- Using the final Dragonite answer as a generic midgame pivot.

### Turns 18-22: Final-Answer Budget Audit

Question:

- Before Dragonite appears, which answer must still be alive, and which tools
  are already gone?

Serious candidate classes:

- heal or preserve the final answer if it is still the only live route;
- spend a narrowed piece only if it creates clean Dragonite entry control;
- force Lance's current active to reveal or lock a move before committing the
  final answer;
- accept risk if every safe line reaches Dragonite with no answer.

Branch injectors:

- The final answer is chipped below +1 Outrage, Earthquake, or Hyper Beam range.
- The phazer/Haze/status tool has already been used.
- The speed-control route is asleep or too low.
- A Lance piece remains alive to soften the final answer before Dragonite.

Ledger test:

- Mark each anti-setup tool as `unused`, `spent`, `narrowed`, or `still live`.
- Write the Dragonite route with exact dependencies: HP, Speed, status, move
  accuracy, lock/recharge punish, or sacrifice entry.
- If the route depends on a roll, crit avoidance, or miss, label the variance.

Failure signs:

- Reaching Dragonite with a vague "we still have Ice coverage" plan.
- Preserving a piece with no live job while the final answer gets chipped.
- Ignoring that a midgame Lance piece can soften the Dragonite answer first.

### Turns 23-27: Dragonite Conversion

Question:

- Can the player deny Dragonite's first boost or punish its commitment?

Serious candidate classes:

- remove or cripple Dragonite before Dragon Dance if possible;
- phaze/Haze/status if it remains fast and reliable enough after local mechanics;
- force Outrage or Hyper Beam only if the receiving piece survives and the
  follow-up converts;
- sacrifice only when the next entry creates a guaranteed or strongly favored
  punish.

Branch injectors:

- Dragonite uses Dragon Dance.
- Dragonite locks into Outrage.
- Dragonite uses Hyper Beam and either KOs or recharges.
- Dragonite uses Earthquake into the expected pivot.

Ledger test:

- After Dragon Dance, update Speed before choosing revenge or status.
- After Outrage, count rampage turns and confusion possibility, but do not rely
  on confusion without a backup.
- After Hyper Beam, check whether the recharge turn actually occurs in a state
  the player can exploit.

Failure signs:

- Treating Outrage lock as safe when the first hit removes the answer.
- Assuming Hyper Beam is punishable after letting it KO the only punisher.
- Continuing a slow damage plan after Dragonite gains Speed.

### Turns 28-30: Serial Setup Review

Question:

- Which setup wave created the earliest irreversible route loss?

Review output:

```text
earliest route loss:
first setup turn denied correctly:
first setup turn mishandled:
anti-setup tool spent too early:
final answer preserved or lost:
Outrage category claim checked:
variance branch that mattered:
one answer-changing information item:
```

Endgame rule:

- A move is correct only if it handles the current boosted route while leaving a
  real answer to the next known Lance route. If the next route is already
  uncovered, choose the line that creates the highest real comeback chance and
  label it as forced risk.

## Pass Conditions

- The ledger tracks each Dragon Dance / Quiver Dance user separately.
- The plan updates Speed order and boosted attacking category after every boost.
- Outrage category claims are tied to local evidence, not generic Dragon memory.
- Hyper Beam recharge is used only when the user can actually exploit it.
- Yanma Focus Band and Sleep Powder branches are priced before a one-hit plan is
  called safe.
- The final Dragonite route remains named throughout the midgame.
- The review identifies the earliest setup wave that damaged the final route.

## Extracted Lesson

Lance is serial setup denial, not "use Ice against Dragons." The player must
beat the active threat while preserving the tools needed for the next one.
Every Dragon Dance, Quiver Dance, Outrage lock, Hyper Beam recharge, Focus Band
survival, and sleep branch changes which answer is still real. The mastery
skill is answer budgeting: knowing when to spend a control tool now, when to
hold it for Dragonite, and when the old plan died because Speed or damage
crossed a route threshold.
