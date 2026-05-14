# Worked Example: Koga 30-Turn Attrition Trap Ledger Drill

Purpose: practice a full long-game ledger against a constructed Koga battle
where the central problem is poison, trapping, hazard attrition, Haze, recovery,
coverage punishment, and fast cleanup. This drill trains switch-freedom
preservation and clock arbitration: deciding when poison/trap damage is real
progress, when it is fake progress, and when the only correct move is to
preserve the answer that stops the later breaker.

Local evidence:

- Koga route map: `../boss_route_maps/koga_turn1_route_sheet.md`.
- Koga pre-battle route sheet: `koga_pre_battle_route_sheet.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Mechanics overview and generated mechanics reference:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.
- Local source paths named in the route sheet: `data/trainers/parties.asm`,
  `data/moves/moves.asm`, `engine/battle/effect_commands.asm`,
  `engine/battle/move_effects/rapid_spin.asm`,
  `engine/battle/move_effects/spikes.asm`, and
  `engine/battle/late_gen_held_items.asm`.

Expert study anchors:

- Smogon GSC status material: poison and Toxic are clocks, but in GSC Toxic
  counter behavior and switching change how the clock converts:
  <https://www.smogon.com/resources/competitive/gs/status>.
- Smogon GSC Spikes material: poison plus Spikes becomes progress when it
  changes Rest timing, switching, KO thresholds, or PP pressure:
  <https://www.smogon.com/gs/articles/gsc_spikes>.
- Smogon trapping material: trapping is valuable only when the trapped target
  is removed, exploited, or forced into a worse route:
  <https://www.smogon.com/dp/articles/dpp_trapping_guide>.
- Borat's GSC guide: do not confuse a long game with a good plan; the player
  still needs a route that actually makes progress:
  <https://www.smogon.com/gs/articles/gsc_guide_part1>.

## Starting Position

Use Koga's known roster:

```text
Ariados:
  Spikes / Toxic / Leech Life / Spider Web

Tentacruel:
  Rapid Spin / Surf / Sludge Bomb / Haze

Muk:
  Curse / Sludge Bomb / Toxic / Rest

Nidoking:
  Earthquake / Sludge Bomb / Ice Beam / Thunderbolt

Umbreon:
  Pursuit / Confuse Ray / Moonlight / Toxic

Crobat:
  Wing Attack / Toxic / Sludge Bomb / Hyper Beam
```

Assume the user has six team jobs, not exact species:

```text
lead pressure:
  can stop Ariados from freely combining Spikes, Toxic, and Spider Web

switch-freedom buffer:
  can absorb poison or trap without losing a unique future role

hazard / setup route:
  useful only if Tentacruel cannot erase it for free with Rapid Spin or Haze

Nidoking answer:
  checked against local type, passive, Expert Belt, and final damage evidence

Muk / Umbreon progress route:
  can break, phaze, Haze, status, pressure PP, or punish Rest / Moonlight

Crobat answer:
  survives prior poison, Spikes, coverage chip, and Hyper Beam / priority-like
  endgame pressure
```

The drill begins before turn 1. Write which player Pokemon are allowed to be
poisoned, trapped, or spent before choosing the lead.

## Ledger Fields

At every checkpoint, write these fields:

```text
turn window:
our route:
Koga route:
Spikes on our side:
Spikes on Koga's side:
poison / Toxic state:
trap state:
Tentacruel Spin / Haze access:
Muk Curse / Rest state:
Umbreon Toxic / Confuse Ray / Moonlight / Pursuit state:
Nidoking coverage map:
Crobat cleanup range:
our irreplaceable pieces:
current worst plausible branch:
what would change the plan:
next move class:
```

The ledger should answer one question repeatedly:

```text
Is this clock attached to a Pokemon whose role matters later?
```

## Drill

### Turns 1-3: Ariados Switch-Freedom Test

Question:

- Can the opener stop Ariados from converting a weak-looking lead into Spikes,
  Toxic, and Spider Web control?

Serious candidate classes:

- attack if damage removes Ariados or forces it away before two clocks stack;
- status only if poison immunity, Toxic risk, and Tentacruel follow-up are
  priced;
- pivot only if the pivot is not the only Nidoking, Muk, or Crobat answer;
- set hazards only if Tentacruel's Rapid Spin turn has a punish.

Branch injectors:

- Ariados sets Spikes.
- Ariados uses Toxic on the lead.
- Ariados uses Spider Web on an irreplaceable piece.
- Ariados attacks, preserving its clocks for later.

Ledger test:

- If Spikes land, count grounded switch costs immediately.
- If Toxic lands, relabel the poisoned Pokemon by future job, not by current
  HP.
- If Spider Web lands, treat the active Pokemon as trapped and decide whether
  it wins, converts, or must be spent.

Failure signs:

- Letting the only Nidoking or Crobat answer take Toxic because Ariados is weak.
- Setting hazards without a Tentacruel spin-punish plan.
- Forgetting that normal pivot plans no longer exist after Spider Web.

### Turns 4-7: Tentacruel Progress Erasure

Question:

- Is Tentacruel erasing the user's route with Rapid Spin or Haze, or can the
  user punish the erasure turn?

Serious candidate classes:

- attack Tentacruel if it must be damaged before Spin/Haze becomes safe;
- preserve the hazard plan only if the next layer stays or forces progress;
- abandon setup if Haze is still free and the boost does not convert this turn;
- use Tentacruel's passive turn to bring in the real breaker only if entry cost
  and Sludge Bomb/Surf branches are priced.

Branch injectors:

- Tentacruel Rapid Spins away the user's layers.
- Tentacruel Hazes away setup.
- Tentacruel attacks instead of erasing progress.
- The user's spin/Haze punish fails to change a route.

Ledger test:

- If Rapid Spin succeeds, mark hazard progress as removed unless the spin turn
  gave concrete compensation.
- If Haze succeeds, decide whether the setup route is dead or merely delayed.
- If Tentacruel is forced out, note whether it can still erase progress later.

Failure signs:

- Counting "I set hazards" as progress after Tentacruel removed them for free.
- Continuing a setup line after Haze reset the board.
- Ignoring Tentacruel because it is not the strongest attacker.

### Turns 8-12: Muk Curse / Rest Anchor

Question:

- Is Muk becoming the long-game anchor while the player overreacts to poison and
  hazards?

Serious candidate classes:

- deny Curse before Sludge Bomb and Toxic force the wrong answers;
- phaze, Haze, status, or attack if the move changes Rest timing or KO range;
- force Rest only if the user can punish the sleep turns;
- preserve the Muk breaker or reset button even if Ariados or Tentacruel is
  still annoying.

Branch injectors:

- Muk uses Curse.
- Muk poisons the Muk answer.
- Muk Rests and the user can or cannot punish.
- The Muk answer was already trapped, poisoned, or spent.

Ledger test:

- After every Curse, rewrite the threat-answer map.
- If Muk Rests, write the exact two-turn punishment plan.
- If no punish exists, label Rest as Koga progress, not user progress.

Failure signs:

- Calling Rest a free turn without a concrete setup, phaze, KO, or entry plan.
- Letting a low-damage piece sit in while Muk becomes harder to move.
- Spending the Muk answer on the Ariados or Tentacruel phase without replacement.

### Turns 13-17: Umbreon Attrition Contract

Question:

- Is Umbreon actually losing resources, or is the player just letting Toxic,
  Confuse Ray, Moonlight, and Pursuit shape the next exchange?

Serious candidate classes:

- attack if damage forces Moonlight, a KO threshold, or a real switch;
- switch only if Pursuit risk and poison/hazard entry costs are acceptable;
- use status or setup only if Mint Berry, Moonlight, and Tentacruel Haze do not
  erase the progress;
- ignore Umbreon temporarily only if another Koga route is more urgent and the
  current active is not being trapped by attrition.

Branch injectors:

- Umbreon uses Toxic.
- Umbreon uses Confuse Ray and forces a risk decision.
- Umbreon uses Moonlight and resets chip.
- Umbreon Pursuits the expected switch.

Ledger test:

- Write what resource Umbreon lost, if any: HP threshold, Moonlight PP, Mint
  Berry, positioning, or a switch.
- If no resource changed, the player probably donated a turn.
- If switching is required, price Pursuit plus entry cost before calling it safe.

Failure signs:

- Fighting Umbreon with vague "wallbreaker pressure."
- Switching a special attacker through Pursuit without a route gain.
- Ignoring Moonlight time/weather context when recovery decides the line.

### Turns 18-22: Nidoking Coverage Map

Question:

- Has poison or trapping weakened the one piece that actually answers Nidoking?

Serious candidate classes:

- preserve the verified Nidoking answer until Earthquake / Sludge Bomb / Ice
  Beam / Thunderbolt damage is mapped;
- attack or trade if Nidoking can otherwise choose the coverage that breaks the
  team;
- pivot only after checking romhack type chart, passives, Expert Belt, and
  final damage evidence;
- sacrifice only if the next entry removes Nidoking or leaves Crobat/Muk
  covered.

Branch injectors:

- Nidoking reveals the coverage that beats the assumed pivot.
- Expert Belt changes a threshold.
- The Nidoking answer is poisoned or trapped from earlier.
- Nidoking is forced low enough that Crobat becomes Koga's main route instead.

Ledger test:

- Write which coverage moves are confirmed, likely, plausible, and impossible.
- If the answer is poisoned, count how many entries it still has.
- If the answer is also the Crobat answer, decide which route needs a different
  solution.

Failure signs:

- Type-slogan switching before local damage evidence.
- Treating "not revealed" as "absent."
- Removing Nidoking while leaving no Crobat answer.

### Turns 23-27: Crobat Cleanup Check

Question:

- Did Koga's clocks put Crobat into a winning endgame?

Serious candidate classes:

- preserve the remaining Crobat answer even if it is low;
- trade for Crobat if the trade still leaves material for Muk or Umbreon;
- heal only if the healed piece remains the final blocker;
- deny Hyper Beam cleanup if the recharge punish is not actually available.

Branch injectors:

- Crobat enters after poison and Spikes chip.
- Crobat uses Toxic on the final answer.
- Crobat attacks and puts the answer into Hyper Beam range.
- Crobat uses Hyper Beam and either removes the answer or creates a punish.

Ledger test:

- Do not call Crobat checked until the answer survives entry, poison clock,
  Sludge Bomb / Wing Attack, and Hyper Beam math.
- If Hyper Beam is baited, name the exact punish before relying on recharge.
- If Crobat is removed, immediately re-rank Muk, Umbreon, or Nidoking.

Failure signs:

- Winning the Nidoking exchange while leaving no Crobat route.
- Assuming recharge is punishable after Hyper Beam KOs the punisher.
- Treating a poisoned low-HP Crobat answer as healthy enough without counting
  the next turn.

### Turns 28-30: Attrition Endgame Audit

Question:

- Which clock decided the game: poison, Spikes, trap, recovery, Haze/Spin,
  coverage, or fast cleanup?

Review output:

```text
earliest route loss:
first clock Koga converted:
clock the player converted:
trap or poison target that mattered most:
progress erased by Tentacruel:
Muk/Umbreon resource actually won:
Crobat or Nidoking answer preserved or lost:
one answer-changing information item:
```

Endgame rule:

- A slow move is good only if the clock it creates belongs to the player. If the
  clock lands on an irreplaceable answer, or if Koga can reset it with Spin,
  Haze, Rest, Moonlight, or switching, the move may be fake progress.

## Pass Conditions

- The ledger tracks poison, Toxic, Spider Web, Spikes, Rapid Spin, Haze,
  Muk Curse/Rest, Umbreon Moonlight/Pursuit, Nidoking coverage, and Crobat
  cleanup without dropping a clock.
- Every poisoned or trapped Pokemon is relabeled by remaining job.
- Hazard and setup progress are not counted after Tentacruel erases them unless
  the erasure turn gave concrete compensation.
- Every Rest or Moonlight turn is labeled as reset, punish, or route
  conversion.
- Every Nidoking or Crobat pivot claim is tied to romhack type, passive, item,
  and damage evidence when it affects the move choice.
- The review identifies the earliest clock that made an answer fail.

## Extracted Lesson

Koga is the attrition version of long-game pressure. The dangerous move is not
always the strongest attack; it may be Toxic on the only answer, Spider Web on a
piece that needed to pivot later, Haze on a setup route, Rapid Spin on a hazard
route, Moonlight on shallow chip, or Pursuit on the switch that was supposed to
reset the position. The mastery skill is deciding which clocks are real,
which clocks are fake, and which answer cannot be allowed to inherit the wrong
timer.
