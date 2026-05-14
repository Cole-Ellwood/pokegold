# Worked Example: Pryce 30-Turn Ledger Drill

Purpose: practice a full long-game ledger against a constructed Pryce battle
without needing a simulator. This is a drill for planning, re-scoring, and
resource tracking, not a solved script.

Local evidence:

- Pryce route map: `../boss_route_maps/pryce_turn1_route_sheet.md`.
- Pryce pre-battle route sheet: `pryce_pre_battle_route_sheet.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Mechanics overview and generated mechanics reference:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert study anchors:

- Smogon GSC Spikes material: hazards become real progress only when they are
  kept, exploited, or converted through forced switches, Rest pressure, phazing,
  or thresholds: <https://www.smogon.com/gs/articles/gsc_spikes>.
- Smogon long-term thinking material: form the route first, then preserve the
  pieces that make that route possible:
  <https://www.smogon.com/rs/articles/long_term_thinking>.
- Smogon risk/reward material: compare the likely branch with the worst
  plausible branch before spending an irreplaceable resource:
  <https://www.smogon.com/resources/beginner/bw_risk_reward>.

## Starting Position

Use Pryce's known roster:

```text
Cloyster:
  Spikes / Surf / Ice Beam / Explosion

Dewgong:
  Rapid Spin / Surf / Ice Beam / Encore

Sneasel:
  Faint Attack / Ice Punch / Shadow Ball / Quick Attack

Piloswine:
  Earthquake / Blizzard / Rock Slide / Roar

Slowking:
  Surf / Psychic / Thunder Wave / Rest
```

Assume the user has a normal in-game team with six roles, not exact species:

```text
lead pressure:
  can threaten Cloyster or deny a free layer

hazard/removal piece:
  can set hazards, remove hazards, or punish Dewgong's Rapid Spin

Sneasel answer:
  survives priority cleanup after chip

Piloswine answer:
  checked against local type/passive/damage evidence

Slowking breaker:
  can punish Rest, avoid paralysis collapse, or force progress through bulk

flex piece:
  one pivot, sacrifice entry, status absorber, or emergency revenge hit
```

Do not name a final move from this shell. The task is to keep the ledger alive
until the real player team makes one route concrete.

## Ledger Fields

At every checkpoint, write these fields:

```text
turn window:
our route:
Pryce route:
our irreplaceable pieces:
Pryce irreplaceable pieces:
Spikes on our side:
Spikes on Pryce's side:
Rapid Spin access:
Cloyster Explosion state:
Dewgong Encore state:
Piloswine Roar state:
Slowking Thunder Wave / Rest state:
Sneasel cleanup range:
current worst plausible branch:
what would change the plan:
next move class:
```

The answer is not complete if it only says "attack," "set Spikes," or
"preserve the counter." It must say what route the move improves.

## Drill

### Turns 1-3: Cloyster Lead

Question:

- Can the lead stop Cloyster from converting both Spikes and Explosion?

Serious candidate classes:

- attack Cloyster to deny or price the first layer;
- pivot to a piece that handles Surf/Ice Beam without being the only later
  Sneasel or Piloswine answer;
- set a hazard only if Dewgong's spin turn has a punish;
- status only if it changes Cloyster's ability to layer or explode.

Branch injectors:

- Cloyster sets Spikes turn 1.
- Cloyster attacks instead of setting Spikes.
- Cloyster threatens Explosion into the only Piloswine or Sneasel answer.

Ledger test:

- If Spikes land, re-score grounded switch cost immediately.
- If Cloyster stays healthy, keep Explosion as a live one-time resource.
- If the lead is now low, decide whether it still has a future job or can be
  spent for safe entry.

Failure signs:

- Treating the first layer as harmless because it is only one layer.
- Letting the only later answer absorb Cloyster chip plus Explosion risk.
- Setting hazards without an answer to Dewgong.

### Turns 4-7: Dewgong Control Turn

Question:

- Does Dewgong remove the user's progress, lock a bad move with Encore, or give
  the user a punish window?

Serious candidate classes:

- pressure Dewgong before it spins;
- preserve the spinblock or spin-punish route if the user's hazards matter;
- avoid setup, recovery, or low-value support if Encore makes the next turns
  collapse;
- switch only if the switch does not put the grounded core on a losing Spikes
  clock.

Branch injectors:

- Dewgong Rapid Spins and clears all layers.
- Dewgong Encores the user's last support move.
- Dewgong attacks and puts the hazard/removal piece below future entry range.

Ledger test:

- If Rapid Spin succeeds, mark the hazard route as lost unless the next turn
  restores it with a concrete punish.
- If Encore lands, track the lock as a turn clock instead of continuing the old
  plan.
- If Dewgong is forced out, note whether it can spin later or has become
  expendable for Pryce.

Failure signs:

- Calling "I set hazards" progress after Dewgong removed them for free.
- Clicking a support move because it was good one turn ago.
- Forgetting Encore when planning a setup or recovery turn.

### Turns 8-12: First Route Trade

Question:

- Which one-time resource is now more valuable: preserving the current piece or
  converting it into entry, damage, spin denial, or an Explosion target?

Serious candidate classes:

- KO or force Cloyster before Explosion can remove a critical answer;
- accept a sacrifice only if the next entry creates real progress;
- trade a spent utility piece if its remaining jobs are replaceable;
- preserve a low-HP piece if it still checks Sneasel, spins, absorbs status, or
  creates one more safe entry.

Branch injectors:

- Cloyster Explodes.
- The user sacs a low-HP piece and gets a clean entry.
- The user sacs the only Sneasel answer by mistake.

Ledger test:

- Mark every piece as `converter`, `blocker`, `sack`, or `spent`.
- A sacrifice is legal only if the route after the sacrifice survives Pryce's
  next competent response.

Failure signs:

- "Low HP means expendable."
- Explosion or sacrifice described as momentum without naming the opened route.
- Preserving everything and losing tempo to hazards anyway.

### Turns 13-17: Piloswine Roar Window

Question:

- Is Piloswine creating damage with attacks, phazing with Spikes, or merely
  being delayed?

Serious candidate classes:

- attack if damage removes Piloswine or forces it out before Roar cycles;
- remove hazards before Roar if the grounded team cannot take repeated entries;
- pivot only through pieces that still survive their assigned job after entry
  damage;
- use type words only after checking romhack type chart/passives/final damage.

Branch injectors:

- Piloswine Roars through active Spikes.
- Piloswine attacks the expected pivot.
- The chosen Piloswine answer is revealed to be unsafe by local damage/type
  evidence.

Ledger test:

- Count how many grounded entries each irreplaceable piece can still make.
- Decide whether the fight is now a hazard-removal problem, a direct-KO
  problem, or a forced-sack problem.

Failure signs:

- Importing vanilla "hit Ice with Fire" logic without local evidence.
- Treating Roar as flavor instead of a switch-tax engine.
- Switching the correct species after it no longer has the HP to perform the
  role.

### Turns 18-22: Slowking Rest And Paralysis

Question:

- Can the user force Slowking's Rest and punish the sleep turns, or does
  Thunder Wave plus Leftovers reset the route in Pryce's favor?

Serious candidate classes:

- force Rest only if the next two turns produce setup, KO pressure, hazard
  progress, or safe entry;
- avoid exposing the only Sneasel/Piloswine answer to Thunder Wave if speed
  control is needed later;
- attack only when damage changes Rest timing, a KO range, or Slowking's
  ability to keep checking the route;
- pivot to the breaker only if entry damage and paralysis risk have been priced.

Branch injectors:

- Slowking Thunder Waves the cleaner.
- Slowking Rests before the user can convert damage.
- Slowking attacks instead of using utility and changes an entry threshold.

Ledger test:

- Record whether forcing Rest is progress or only damage that gets erased.
- Mark which Pokemon can still exploit two sleep turns.
- If no one can exploit Rest, the plan needs a different route.

Failure signs:

- Celebrating damage that Slowking can Rest off for free.
- Ignoring that paralysis changes the Sneasel endgame.
- Spending the breaker on a turn that does not force a threshold.

### Turns 23-27: Sneasel Cleanup Check

Question:

- Has Pryce's hazard/status/chip plan made Sneasel the actual endgame route?

Serious candidate classes:

- preserve the remaining Sneasel answer even if it is low;
- trade for Sneasel if the trade leaves enough material to beat Slowking or
  Piloswine afterward;
- heal only if the healed piece is still the blocker in the final route;
- choose a sack only if it creates safe entry for the real closer.

Branch injectors:

- Sneasel enters after a forced KO.
- Quick Attack range changes the apparent speed advantage.
- The expected answer is paralyzed, chipped by Spikes, or already spent.

Ledger test:

- Do not call the battle stable until the Sneasel answer survives entry,
  coverage, and priority.
- If Sneasel is removed, immediately re-rank Pryce's remaining route instead of
  relaxing.

Failure signs:

- Winning the Slowking exchange while leaving no Sneasel answer.
- Assuming being faster solves a priority endgame.
- Using the last healthy answer as a generic pivot earlier.

### Turns 28-30: Endgame Audit

Question:

- Which clock now decides the fight?

Possible clocks:

- Spikes entries;
- Encore turns;
- Rest turns;
- Thunder Wave speed loss;
- Roar cycles;
- priority range;
- remaining recovery PP;
- Explosion already spent or still live;
- the next safe entry after a faint.

Endgame rule:

- Choose the move that creates or preserves the forced line. If no forced line
  exists, choose the move that avoids the irreversible loss and keeps the most
  live routes.

Review output:

```text
earliest route loss:
best preserved resource:
worst avoidable branch:
old plan that had to be abandoned:
one move class that became better over time:
one move class that became worse over time:
```

## Pass Conditions

- The ledger tracks hazards, Rapid Spin, Encore, Explosion, Roar, Thunder Wave,
  Rest, and Sneasel priority without dropping a clock.
- The plan changes after each branch injector instead of continuing a stale
  script.
- Every sacrifice names the route it opens and the role it closes.
- Every type-effectiveness or resistance claim is tied to romhack evidence, not
  generic Pokemon memory.
- The review finds the earliest meaningful route loss, not only the final faint.

## Extracted Lesson

Pryce is a strong first 30-turn drill because every good slogan can become bad
on the wrong turn. Set hazards loses to free Rapid Spin. Preserve answers loses
when a spent piece can be converted into a clean entry. Attack for damage loses
when Slowking Rests it away. Switch to the counter loses when Spikes, paralysis,
or Roar made the counter unable to perform its role. The skill being trained is
not memorizing Pryce; it is maintaining the route ledger long enough to know
which normally true heuristic dominates on the exact turn.
