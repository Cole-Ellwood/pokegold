# Worked Example: Red Sequential Converter Pressure Stress Test

Purpose: stress-test the sequential-converter lesson from
`smogtours_gen4ou_670049_sequential_converter_pressure.md` against Red's local
final-boss route. This is a narrow drill for route handoffs, not another full
30-turn ledger.

Local evidence:

- Red route map: `../boss_route_maps/red_turn1_route_sheet.md`.
- Red pre-battle route sheet: `red_pre_battle_route_sheet.md`.
- Red 30-turn drill: `red_30_turn_final_boss_ledger_drill.md`.
- Roster source: `data/trainers/parties.asm`.
- Light Ball, Rest/Sleep Talk, Sunny Day, priority, Morning Sun / Synthesis,
  Mirror Coat, and item behavior:
  `../../agent_navigation/gen2_vs_modern_mechanics.md`.
- Generated mechanics reference:
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert transfer source:

- Sequential converter review:
  `../reviews/2026-05-13_smogtours-gen4ou-670049.md`.
- Smogon setup material:
  <https://www.smogon.com/smog/issue26/setting_up>.
- Smogon Getting Started material:
  <https://www.smogon.com/articles/getting-started>.
- Smogon risk/reward material:
  <https://www.smogon.com/resources/beginner/bw_risk_reward>.

## Pattern Being Tested

Bad shortcut:

```text
We stopped the current Red Pokemon, so the route is handled.
```

Better policy:

```text
Stopping one converter only matters if the answer map still covers the next
converter that inherits the board.
```

Red's roster is built for this mistake. Pikachu can force early chip or priority
range. Espeon can turn that board into Reflect or Calm Mind. Snorlax can inherit
a weakened answer map and start Curse / Rest / Sleep Talk. Venusaur and
Charizard can inherit weather timing. Blastoise can punish special damage with
Mirror Coat. A surviving Pikachu can return as an ExtremeSpeed clock.

## Stress-Test State

Use this public-state prompt, then substitute the user's real team:

```text
Red route just stopped:
  Pikachu forced / Espeon controlled / Snorlax phazed / sun stalled /
  Blastoise pressured

Cost paid:
  HP, status, PP, item, revealed move, weather turn, screen turn, or sacrifice

Red routes still alive:
  Espeon Reflect / Calm Mind
  Snorlax Curse / Rest / Sleep Talk
  Venusaur or Charizard Sunny Day
  Blastoise Mirror Coat / mixed coverage
  Pikachu ExtremeSpeed if still alive

Question:
  Which Red Pokemon inherits the board next, and is our current answer still
  valid after the cost paid?
```

## Required Handoff Questions

After every successful denial turn, fill this:

```text
First converter stopped:
Answer used:
Cost paid by that answer:
Residual state left behind:
  screen / sun / paralysis / chip / PP loss / sleep / priority range / reveal

Next Red converter:
Our remaining answer:
Can the previous answer still perform that job:
Move that prevents a free handoff:
What information would flip the answer:
```

If the answer is "continue the old plan," prove that the next Red route does
not punish that continuation.

## Handoff Cases

### Pikachu Into Espeon Or Snorlax

Pikachu is not the whole fight. If the player beats Pikachu by spending the
only special setup answer, Espeon may inherit the board. If the player beats
Pikachu by chipping or paralyzing the only physical anchor answer, Snorlax may
inherit the board.

Failure sign:

- The advice celebrates removing Pikachu but never says which piece now handles
  Reflect / Calm Mind or Curse / RestTalk.

Correct pressure:

- Beat or force Pikachu with a piece whose later jobs are replaceable, or turn
  the Pikachu exchange into a clean entry for the Espeon or Snorlax answer.

### Espeon Into Snorlax

Stopping Espeon with the Snorlax answer can still lose if that answer is now
below the threshold required to phaze, Haze, trade, or pressure Snorlax. Reflect
turns can also protect the next route even after Espeon leaves.

Failure sign:

- The advice says "Espeon is checked" while Reflect turns remain and the
  Snorlax answer has been damaged or statused.

Correct pressure:

- Count Reflect, label the answer's remaining HP/PP/status job, and decide
  whether to shorten the route before Snorlax enters.

### Snorlax Into Sun

Forcing Snorlax to Rest is progress only if the user can cash in the sleep
turns through Sleep Talk branches. If the user spends those turns healing or
scouting, Venusaur or Charizard may inherit a cleaner weather board.

Failure sign:

- The advice treats Rest as the end of pressure without naming the Sleep Talk
  branch or the sun answer that must remain healthy afterward.

Correct pressure:

- Use Rest turns to remove Snorlax, force a decisive trade, or enter a piece
  that also keeps the sun route covered.

### Sun Into Blastoise

After Venusaur or Charizard spends sun turns, the player may reach for special
damage to stabilize. Blastoise can punish that with Mirror Coat. The sun route
may be over, but the damage-category trap can inherit the board.

Failure sign:

- The advice says "sun expired, so resume attacking" without checking Mirror
  Coat, Blizzard, Earthquake, or whether the physical answer was spent earlier.

Correct pressure:

- Re-score Blastoise as a new route, not as cleanup. Use physical or mixed
  pressure when possible, or justify the special attack by surviving the Mirror
  Coat branch.

### Any Route Into Surviving Pikachu

If Pikachu survives, ExtremeSpeed remains an endgame clock even though Light
Ball does not boost it locally. A cleaner that wins the board but ends in
priority range may not be a real cleaner.

Failure sign:

- The advice calls the endgame won without checking surviving priority.

Correct pressure:

- Preserve enough HP, remove Pikachu before the final sequence, or route the
  endgame through a piece that survives priority.

## Candidate Move Arbitration

Preserve rises when:

- the answer still uniquely covers the next Red converter;
- the current move would spend it for progress that another piece can make;
- the worst plausible handoff creates an irreversible route.

Trade or sacrifice rises when:

- the traded piece's route is complete;
- the trade removes the next converter or its only support;
- the remaining answer map covers every live Red route.

Attack rises when:

- the damage prevents the handoff by forcing a KO, Rest, recovery, weather
  expiration, screen expiration, or priority threshold;
- the attacking piece is not exposing the answer to the next route.

Setup or recovery falls when:

- Red's next converter gets a free entry;
- the move ignores an active screen, sun, RestTalk, Mirror Coat, or priority
  branch;
- the old route no longer matches the public board.

## Example Verdict Shape

```text
Recommendation:
  attack / switch / preserve / trade / recover / setup

Why:
  We stopped [first route], but it cost [resource]. Red's next likely handoff is
  [next converter], so this move protects or improves [specific answer].

Worst plausible branch:
  if we continue the old plan, Red gets [Reflect / Curse / sun / Mirror Coat /
  ExtremeSpeed] and our [answer] no longer performs its role.

What changes the answer:
  exact HP thresholds, Reflect turns, Snorlax boosts and Rest state, sun turns,
  Blastoise Mirror Coat risk, Pikachu survival, and local type/passive/damage
  evidence.
```

## Extracted Lesson

The DPP sequential-converter lesson becomes Red policy: every time one Red
route is stopped, immediately ask which route inherits the board. The best move
is not the one that proves the previous answer was correct; it is the one that
keeps the next answer alive or converts before Red's next route arrives. This
is the final-boss version of long-term Pokemon planning.
