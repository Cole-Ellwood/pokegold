# Worked Example: Sabrina 30-Turn Ledger Drill

Purpose: practice a full long-game ledger against a constructed Sabrina battle
where the main problem is not hazards. This drill trains clock ownership,
move-lock exploitation, sleep planning, forced-switch sequencing, recovery
punishment, and plan revision.

Local evidence:

- Sabrina route map: `../boss_route_maps/sabrina_turn1_route_sheet.md`.
- Sabrina pre-battle route sheet: `sabrina_pre_battle_route_sheet.md`.
- Mechanics overview and generated mechanics reference:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.
- Relevant local sources named in the route sheet: `data/trainers/parties.asm`,
  `data/moves/moves.asm`, `engine/battle/effect_commands.asm`,
  `engine/battle/move_effects/encore.asm`,
  `engine/battle/move_effects/baton_pass.asm`,
  and `engine/battle/late_gen_held_items.asm`.

Expert study anchors:

- Smogon GSC status material: sleep is still powerful, but GSC sleep is not
  permanent ownership because wake turns, Sleep Talk, and role loss must be
  priced: <https://www.smogon.com/resources/competitive/gs/status>.
- Smogon GSC Jynx material: Lovely Kiss is a tempo tool that forces switches,
  but Jynx's limited bulk makes the cash-out turn matter:
  <https://www.smogon.com/forums/threads/jynx-gsc-ou-qc-2-2-gp-2-2.3667481/>.
- Smogon GSC Espeon material: Morning Sun, Speed, and coverage make repeated
  shallow chip unreliable unless it reaches a route threshold:
  <https://www.smogon.com/forums/threads/gsc-ou-espeon-qc-1-1-gp-1-1.3667456/>.
- Smogon Baton Pass material: screens, Taunt, phazing, Perish Song, and Encore
  all matter because they decide whether a position handoff survives:
  <https://www.smogon.com/dp/articles/baton_pass_chains>.
- Smogon move-restriction material: after a Choice or Encore lock, the correct
  decision is about exploiting or escaping the lock:
  <https://www.smogon.com/dp/articles/move_restrictions>.

## Starting Position

Use Sabrina's known roster:

```text
Mr. Mime:
  Light Screen / Reflect / Encore / Psychic

Jynx:
  Lovely Kiss / Ice Beam / Psychic / Perish Song

Espeon:
  Hidden Power / Psychic / Morning Sun / Baton Pass

Alakazam:
  Psychic / Ice Punch / ThunderPunch / Fire Punch
  item: Choice Specs

Hypno:
  Seismic Toss / Rest / Thunder Wave / Psychic
```

Assume the user has six team jobs, not exact species:

```text
lead pressure:
  can hit Mr. Mime without giving Encore a decisive support move

sleep plan:
  can absorb, deny, or punish Jynx's Lovely Kiss without losing the battle map

special anchor:
  can survive at least one unknown Alakazam Choice Specs attack until the lock
  is revealed

physical or mixed pressure:
  can attack through Light Screen or force damage while Reflect is absent

Hypno breaker:
  can punish Rest turns or prevent Thunder Wave from collapsing the endgame

flex piece:
  one sacrifice, pivot, status absorber, lock exploiter, or Perish Song reset
```

The drill begins before turn 1. Write a plan for all five Sabrina Pokemon before
choosing the lead. Then spend the next 30 turns updating the plan whenever a
clock, lock, sleep state, or coverage reveal changes the board.

## Ledger Fields

At every checkpoint, write these fields:

```text
turn window:
our route:
Sabrina route:
our irreplaceable pieces:
Sabrina irreplaceable pieces:
Light Screen turns:
Reflect turns:
Encore target and turns:
Sleep Clause and sleeping Pokemon:
Perish count:
Alakazam Choice Specs lock:
Espeon Hidden Power evidence:
Morning Sun recovery context:
Hypno Thunder Wave / Rest state:
current worst plausible branch:
what would change the plan:
next move class:
```

The ledger should make two distinctions clear:

- A clock is useful only if it changes future move value before it expires.
- A lock is useful only if the player has a safe route to exploit it.

## Drill

### Turns 1-3: Mr. Mime Screen And Encore Test

Question:

- Can the opener pressure Mr. Mime without donating a passive move to Encore or
  letting the wrong screen invalidate the route?

Serious candidate classes:

- attack immediately if damage denies a screen, forces Mr. Mime out, or
  shortens the screen window;
- use status only if Encore on that status is acceptable;
- set up only if the Encore branch is harmless or Mr. Mime cannot use it;
- pivot only if the pivot does not spend the Jynx sleep plan or Alakazam anchor.

Branch injectors:

- Mr. Mime sets Light Screen.
- Mr. Mime sets Reflect.
- Mr. Mime Encores a support, recovery, or setup move.
- Mr. Mime attacks and puts the lead below its next-job threshold.

Ledger test:

- If a screen goes up, set a five-turn counter and re-rank attacking categories.
- If Encore lands, write whether the locked move still improves a route.
- If the opener cannot progress through the active screen, switch plans before
  losing the screen turns for free.

Failure signs:

- "Psychic types are weak to X" without checking the screen and local damage.
- Treating Light Screen and Reflect as flavor instead of turn clocks.
- Clicking setup into a visible Encore trap.

### Turns 4-7: Jynx Sleep And Perish Test

Question:

- Does Jynx's first utility turn remove a key role, or does it create a
  manageable clock the player can exploit?

Serious candidate classes:

- attack if Jynx's bulk makes immediate pressure better than overplanning;
- switch to the assigned sleep absorber only if losing that piece's turn does
  not open Alakazam, Espeon, or Hypno;
- exploit Sleep Clause if a harmless Pokemon is already asleep;
- respond to Perish Song by planning the next entry before the count forces it.

Branch injectors:

- Lovely Kiss hits the intended absorber.
- Lovely Kiss hits the wrong irreplaceable piece.
- Lovely Kiss misses.
- Jynx uses Perish Song instead of sleep.
- Jynx attacks into the expected sleep pivot.

Ledger test:

- Mark whether sleep made the target expendable, narrowed, or still essential.
- If Perish Song starts, count the forced switch sequence and who gets the best
  entry when the count reaches zero.
- If Jynx misses, do not auto-setup; re-score Jynx's next best move.

Failure signs:

- "Sleep gives us free turns" without naming the cash-out.
- Treating a missed sleep move as permission to follow the old setup script.
- Letting Perish Song choose the next matchup for Sabrina.

### Turns 8-12: Alakazam Choice Lock Map

Question:

- Can the player survive the first unknown Choice Specs attack and turn the
  revealed lock into progress?

Serious candidate classes:

- preserve the broad special anchor until Alakazam reveals Psychic, Ice Punch,
  ThunderPunch, or Fire Punch;
- pivot after the lock only if the pivot's other future jobs survive;
- attack through the lock if Alakazam cannot safely switch or if the attack
  removes the lock threat;
- sacrifice only if the free entry creates a route that is stronger than the
  lost defensive job.

Branch injectors:

- Alakazam locks Psychic.
- Alakazam locks an elemental punch that breaks the assumed pivot.
- Alakazam switches out after revealing the lock.
- The player overuses the lock exploiter and loses the Jynx or Hypno answer.

Ledger test:

- Record the lock immediately after Alakazam attacks.
- Write who can enter that locked move and what route they improve afterward.
- If no one can exploit the lock safely, the answer is not "we know the move";
  it is "we survived but still need a new route."

Failure signs:

- Pivoting by type memory without checking romhack chart/passive/final damage.
- Spending the only Jynx or Hypno answer just because it resists the locked
  move.
- Forgetting that Alakazam can reset its lock by switching.

### Turns 13-17: Espeon Recovery And Baton Pass

Question:

- Is the player making progress against Espeon, or only producing chip that
  Morning Sun or Baton Pass converts into Sabrina's position advantage?

Serious candidate classes:

- force a threshold that Morning Sun cannot erase before the next punish;
- use status only if it survives relevant resets and changes the Baton Pass
  recipient's route;
- preserve the Hidden Power answer until type and damage evidence are known;
- punish Baton Pass by re-evaluating the incoming Pokemon, not by continuing
  to discuss Espeon.

Branch injectors:

- Espeon reveals Hidden Power damage that flips the answer map.
- Espeon uses Morning Sun and erases shallow chip.
- Espeon Baton Passes out of a bad matchup.
- The incoming Baton Pass recipient is Alakazam, Jynx, or Hypno.

Ledger test:

- Treat Hidden Power as evidence, not a generic coverage slot.
- If Morning Sun erases the plan, switch to status, threshold, PP, or forced
  entry pressure.
- If Baton Pass happens, rebuild the active matchup and preserve any passed
  stat context.

Failure signs:

- Repeating chip into Morning Sun without a threshold.
- Calling the Espeon answer safe before Hidden Power evidence exists.
- Forgetting that Baton Pass is a board transition, not just a switch.

### Turns 18-22: Hypno Paralysis And Rest Cycle

Question:

- Can the player force Hypno's Rest and convert the sleep turns, or does
  Thunder Wave make Sabrina's endgame easier?

Serious candidate classes:

- attack if damage forces Rest at a time the player can punish;
- avoid exposing the speed-control piece to Thunder Wave if Alakazam or Jynx
  still requires it;
- pivot to the Hypno breaker only if the entry does not sacrifice another
  irreplaceable job;
- recover only if the healed Pokemon remains the blocker or converter.

Branch injectors:

- Hypno Thunder Waves the cleaner or revenge route.
- Hypno Rests at the exact threshold the player failed to punish.
- Hypno uses Seismic Toss to put a pivot into fixed-damage range.
- Hypno stays awake because the player never forces enough damage.

Ledger test:

- If Rest happens, write the exact two-turn punish attempt.
- If no punish exists, Rest was not progress for the player.
- If Thunder Wave lands, re-rank every Speed-dependent route.

Failure signs:

- Counting damage that Rest deletes as progress.
- Ignoring fixed Seismic Toss thresholds.
- Preserving the wrong piece while the actual speed-control route dies.

### Turns 23-27: Clock Collision

Question:

- Which clock now dominates when screens, sleep, Perish Song, Choice lock,
  Morning Sun, Rest, and paralysis overlap?

Serious candidate classes:

- stall a screen only if the stall does not give Jynx, Alakazam, or Hypno a
  better entry;
- sacrifice a narrowed piece only if the next entry exploits a lock, sleep
  turn, or Rest turn;
- attack if it creates the next forced KO or denies recovery;
- switch if the current active is locked, slept, or paralyzed into a losing
  sequence and the switch preserves the endgame map.

Branch injectors:

- A screen has one turn left but Sabrina can use that turn to enter a stronger
  threat.
- A sleeping Pokemon wakes or remains asleep at a route-critical moment.
- Perish Song forces a switch while Alakazam's lock has reset.
- The player can choose between preserving all pieces and making a decisive
  sack.

Ledger test:

- Order clocks by route severity, not by which one appeared first.
- Write the next two turns after each serious move.
- If every safe line loses slowly, choose the risk that creates the highest real
  comeback chance and label it as forced risk.

Failure signs:

- Updating only HP while ignoring turn clocks.
- Letting an expired plan consume a live clock.
- Refusing a legal sacrifice because the piece is "still useful" in abstract.

### Turns 28-30: Endgame Audit

Question:

- What is the forced line, and which Sabrina piece still blocks it?

Possible deciding resources:

- one remaining screen turn;
- an active or expired Encore lock;
- Sleep Clause and wake timing;
- Perish count;
- Alakazam's current lock or reset;
- Espeon's Morning Sun PP/time/weather context;
- Hypno Rest state and Thunder Wave spread;
- the next free entry after a faint.

Review output:

```text
earliest route loss:
best clock exploited:
worst ignored clock:
piece preserved correctly:
piece spent correctly:
lock or clock that changed the original plan:
one answer-changing information item:
```

Endgame rule:

- A move is good if it creates or preserves a concrete forced line. If no forced
  line exists, choose the move that keeps the most live routes while avoiding
  the most severe irreversible branch.

## Pass Conditions

- The ledger tracks screens, Encore, sleep, Perish Song, Choice lock, Hidden
  Power evidence, Morning Sun, Thunder Wave, and Rest without dropping a clock.
- The plan changes after the active clock or lock changes.
- The player exploits at least one Sabrina lock or recovery turn instead of
  only reacting defensively.
- Every "safe switch" claim names the other jobs that switch target still must
  perform later.
- Every type or resistance claim is tied to romhack evidence and observed
  damage when it affects the move.
- The review identifies the earliest route loss, not only the final KO.

## Extracted Lesson

Sabrina is the non-hazard version of long-game pressure. The boss does not need
Spikes to create a losing clock; screens, Encore, sleep, Perish Song, Choice
Specs, Morning Sun, Baton Pass, Thunder Wave, and Rest all force the player to
spend turns carefully. The skill being trained is clock arbitration: knowing
when to attack through a screen, wait out a lock, switch out of Encore, cash in
sleep tempo, punish Rest, or abandon the original plan because a new clock has
made it false.
