Here is the design I would use.

The core idea: the agent is not trying to “know Pokémon.” It is trying to build a decision policy that survives long-game pressure, uncertain information, bad luck branches, mechanic differences, and adversarial review.

Vanilla GSC should be the base language because it teaches the right habits: slow resource conversion, Rest cycles, Snorlax centrality, Spikes pressure, phazing, Explosion trades, status economy, and non-scripted re-evaluation. The romhack layer should be treated as a mechanics fork, not as a cosmetic variant.

Vanilla GSC has several mechanics that matter directly to this training design: Spikes has only one layer and deals 1/8 max HP on grounded switch-ins; Sleep Talk can call Rest and reset the Rest sleep counter; Roar and Whirlwind have Gen 2-specific priority behavior; normal sleep lasts 1–6 turns while Rest sleep lasts two turns. These mechanics are exactly why the agent must learn state tracking before it learns cleverness. ([Smogon][1])

## 1. What “Pokémon mastery” should mean operationally

For this agent, mastery means:

The agent can maintain an accurate hidden-information battle model and choose moves that preserve or improve its long-term winning routes over 30+ turn singles games, under correct mechanics, incomplete information, and bad-luck branches.

That definition needs measurable standards.

A mastered agent should be able to do all of the following.

First, it should track state with near-zero critical errors. That means HP ranges, status, sleep counters, Rest turns, PP pressure, Spikes state, revealed moves, likely unrevealed moves, Leftovers recovery, speed order, phazing interactions, Explosion availability, and which Pokémon are still required to answer opposing threats. A critical state error is any tracking error that changes the correct move class: for example, forgetting a wake turn, forgetting Spikes damage puts a defender into range, forgetting that a phazer must be preserved, or treating a sleeping target as safely disabled after the wake window has arrived.

Second, it should produce decision candidates, not single-move vibes. For every meaningful turn it should rank at least three legal options: best move, main alternative, and emergency/safety line. Each option should include immediate outcome, worst plausible opponent response, long-term resource effect, and whether it preserves the current win condition.

Third, it should distinguish decision quality from outcome quality. A good move that loses to a low-probability critical hit remains good. A bad move that wins because the opponent misses remains bad. The agent must label luck branches separately from strategic errors.

Fourth, it should play to win conditions, not to damage totals. In GSC, switching, Rest, Sleep Talk, Spikes, phazing, and Explosion can matter more than immediate damage. Smogon’s GSC Spikes guide emphasizes that Spikes are powerful because passive damage is scarce, Spikes persist until Rapid Spin, and phazing plus switching pressure can force Rest cycles and long-term loss of resources. ([Smogon][2])

Fifth, it should pass benchmark gates. Reasonable targets would be:

| Capability             | Minimum mastery standard                                                                                                               |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Mechanics              | 99%+ pass rate on source-verified GSC and romhack mechanics tests                                                                      |
| State tracking         | 0 critical errors across 500 reviewed turns; non-critical errors logged and corrected                                                  |
| Curated position play  | Best move within expert top 2 on 85–90% of benchmark positions                                                                         |
| Severe blunder control | Under 5% severe blunders on unseen 30+ turn logs                                                                                       |
| Long-game planning     | Correctly identifies own win condition, opponent win condition, and irreplaceable defensive pieces by turn 5 in 80%+ of reviewed games |
| Review quality         | Finds the earliest irreversible error within ±2 turns on most annotated losses                                                         |
| Romhack transfer       | Every romhack-specific heuristic is tagged with source evidence, fixture evidence, or “unverified” status                              |
| Notebook quality       | No core heuristic without trigger conditions, exceptions, evidence, and at least one benchmark position                                |

Win rate is useful but not enough. A Pokémon agent can win weak games while learning bad habits. Mastery needs win rate plus decision audits, hidden holdout scenarios, simulator validation, and long-form written explanations that survive adversarial review.

## 2. Curriculum from fundamentals to advanced long-game play

The curriculum should be staged. Do not let the agent skip ahead to romhack theory before it can play normal GSC positions cleanly.

| Stage                    | Focus                                                                         | Required artifact                                                               | Pass condition                                                           |
| ------------------------ | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| 0. Mechanics truth       | Learn exact GSC mechanics and build tests                                     | `mechanics_truth.md`, mechanics test suite                                      | No critical mechanics errors                                             |
| 1. Battle-state model    | Track all battle resources turn by turn                                       | State schema, log parser, battle ledger                                         | Can reconstruct 30+ turn logs without losing sleep/HP/status/hazard info |
| 2. GSC role literacy     | Learn what common Pokémon do and why                                          | Role map: Snorlax, Cloyster, Starmie, Raikou, Skarmory, Exeggutor, Gengar, etc. | Can explain each team’s likely structure by turn 5–8                     |
| 3. Core tactical modules | Switching, status, Rest, Sleep Talk, phazing, Explosion, setup, scouting      | Separate heuristic cards per tactic                                             | Passes curated one-turn and three-turn position tests                    |
| 4. Resource management   | Preserve defensive answers, manage PP, Rest cycles, hazard costs, boom trades | Resource ledger template                                                        | Correctly identifies irreplaceable pieces in benchmark games             |
| 5. Long-game planning    | Convert small edges into endgames                                             | Win-condition tracker                                                           | Can name 2–3 plausible winning routes and update them after reveals      |
| 6. Battle review         | Analyze full games, not clips                                                 | Annotated log reports                                                           | Finds turning points and avoids result-based review                      |
| 7. Controlled simulation | Test hypotheses without overfitting                                           | Simulation reports with assumptions                                             | Can falsify or narrow heuristics                                         |
| 8. Expert comparison     | Compare to Smogon principles, expert games, high-level logs                   | Expert disagreement ledger                                                      | Explains where it disagrees and why                                      |
| 9. Romhack transfer      | Compare vanilla GSC to Gym Leader Lab mechanics                               | Romhack delta register                                                          | Every transferred heuristic is revalidated or quarantined                |
| 10. Benchmark hardening  | Maintain unseen tests and regression suite                                    | Mastery suite                                                                   | Improvements persist on holdout scenarios                                |

The order matters. The agent should not start with “how do I sweep?” It should start with “what is the real state of the game?” In long GSC-style games, most bad decisions are not calculation failures. They are state-model failures.

## 3. What the agent should study first in GSC singles

The first study priority should be mechanics that change move value.

The agent should learn these before it studies team archetypes:

1. Spikes: one layer in vanilla GSC, 1/8 HP on grounded switch-ins, persistent until Rapid Spin. This defines switching cost and long-game pressure. ([Smogon][1])
2. Rest and Sleep Talk: Rest is central to GSC durability, and Sleep Talk can call Rest, which changes how the agent should evaluate sleeping bulky Pokémon. ([Smogon][1])
3. Sleep turns and wake turns: normal sleep can last 1–6 turns; Rest is two turns. The agent’s already-learned lesson belongs here: after Sleep Powder misses, early wakes, or board changes, abandon the script and re-score the position. ([Smogon][1])
4. Roar and Whirlwind: Gen 2 phazing has unusual priority behavior; the slower phazer interaction matters. ([Smogon][1])
5. Explosion and Selfdestruct: Explosion is not merely “big damage.” In GSC it halves Defense, has enormous effective power, causes the user to faint, and if the faster exploding Pokémon moves first and the target survives, the target does not move that turn. ([Smogon][3])
6. Critical hit rules, stat caps, Belly Drum quirks, Toxic decay after switching, and PP pressure.

After mechanics, the agent should study concepts in this order:

Snorlax first. Snorlax is the central piece the agent must understand both with and against: CurseLax, DrumLax, RestTalk variants, Selfdestruct, Lovely Kiss, Fire Blast coverage, and the cost of throwing away one’s Lax too early. Smogon’s GSC introduction explicitly frames Snorlax as something a serious player must learn to play with, against, and without. ([Smogon][4])

Second: Spikes plus switching. GSC is full of switches, but switching is not free when Spikes are down. The agent needs to understand why Cloyster, Forretress, Starmie, spinblocking, Pursuit, Toxic, and phazing form a whole subsystem, not isolated tactics. ([Smogon][2])

Third: defensive answer preservation. The agent must know which piece answers which opposing route. A Skarmory, Raikou, Suicune, Starmie, Ghost, Steelix, or Miltank may be less flashy than a sweeper, but losing the wrong one can make the rest of the game unwinnable.

Fourth: status economy. Sleep, paralysis, poison, freeze odds, Body Slam paralysis, Thunder paralysis, Stun Spore, Toxic on spinners, and Heal Bell support all change which lines are real.

Fifth: Rest-cycle management. The agent should learn when Rest is forced, when Rest gives the opponent a setup turn, when Sleep Talk reduces vulnerability, and when pressuring a Rest turn is more valuable than doing chip damage.

Sixth: phazing and anti-setup. The agent must learn when Roar or Whirlwind is a win-condition tool, when it is only a stall tactic, and when the phazer itself has become the most important piece.

Seventh: Explosion trades. The right Explosion can remove the only defensive answer and open a win condition. The wrong Explosion can remove the agent’s own emergency button. Explosion should be evaluated as a trade of future routes, not as damage.

Eighth: endgames. PP, last-Rest timing, hazard state, sleep state, remaining booms, speed control, and whether the opponent can still phaze matter more than generic “play aggressively” advice.

## 4. How the agent should document heuristics

The Markdown notebook should be structured like an engineering knowledge base, not a strategy blog.

Recommended structure:

```text
pokemon-mastery-notebook/
  README.md
  00_sources_and_authority.md
  01_mechanics_truth_gsc.md
  02_mechanics_truth_romhack.md
  03_battle_state_schema.md
  04_decision_checklist.md
  05_gsc_role_map.md
  06_resource_management.md
  07_hazards_and_spinning.md
  08_sleep_status_rest.md
  09_phazing_and_setup_control.md
  10_explosion_and_sacrifice.md
  11_win_conditions_and_endgames.md
  12_matchup_gameplans.md
  13_heuristic_cards/
  14_mistake_ledger.md
  15_simulation_reports/
  16_battle_reviews/
  17_benchmark_suite.md
  18_romhack_delta_register.md
```

Each section should have a strict purpose.

`00_sources_and_authority.md` should define source hierarchy. For vanilla GSC: mechanics docs, simulator source, Smogon resources, expert logs, local tests. For the romhack: source code and local docs outrank Showdown behavior.

`01_mechanics_truth_gsc.md` should contain exact mechanics with test cases. No prose-only rules. Every mechanic should have “expected behavior,” “test fixture,” and “known implications.”

`02_mechanics_truth_romhack.md` should contain only verified romhack facts. If three-layer Spikes exist, the notebook should record exact layer damage, stacking rules, immunity rules, removal rules, and source-file references.

`03_battle_state_schema.md` should define the state object the agent tracks every turn: active Pokémon, bench, HP ranges, status, sleep counters, Rest counters, known moves, suspected moves, PP, hazards, stat stages, item state, revealed damage ranges, and current win-condition map.

`04_decision_checklist.md` should contain the pre-move checklist from section 10 below.

`05_gsc_role_map.md` should explain roles, not just species. Example: “Cloyster = Spiker / temporary physical check / possible Explosion wallbreaker / sometimes spinner, but cannot run Rapid Spin with Explosion in standard legality.” The GSC Spikes guide notes this exact Cloyster tradeoff. ([Smogon][2])

`06_resource_management.md` should define resources: HP, status, PP, sleep turns, hazard control, defensive answers, information, tempo, Explosion access, setup opportunities, and endgame material.

`13_heuristic_cards/` should be the most important folder. Every heuristic should use this template:

```markdown
# Heuristic: Re-score after sleep disruption

Status: core / provisional / rejected
Format: GSC / Romhack / Both / Needs validation
Confidence: high / medium / low
Last reviewed: YYYY-MM-DD

Trigger:
- A sleep move misses, the target wakes, Sleep Talk reveals a dangerous move, or the opponent switches into a different board state.

Rule:
- Do not continue the planned setup line automatically.
- Recompute immediate threats, wake probability or wake state, damage ranges, switch incentives, and whether the original setup target is still safe.

Why this should be true:
- Sleep creates opportunity only while the resulting position remains favorable.
- A miss, wake, or switch changes both tempo and threat map.

Exceptions:
- Continue the line only if the worst plausible branch still preserves the win condition and no irreplaceable defensive answer is exposed.

Evidence:
- Battle log IDs:
- Simulation IDs:
- Expert principle:
- Romhack fixture:

Counterexamples:
- Cases where continuing setup remains correct.

Benchmark tests:
- sleep_setup_001
- sleep_setup_004
- wake_turn_002

Failure signs:
- The agent describes the move as “still following the plan” without re-evaluating the current board.
```

A heuristic is not allowed into the core notebook unless it has trigger conditions, consequences, exceptions, and at least one concrete test.

## 5. How to use simulations without fooling itself

Simulations are useful, but only when the agent knows what question the sim is answering.

A simulation can prove or estimate:

It can prove mechanical behavior if the simulator is source-accurate and the test is narrow. For example: “Does this implementation of three-layer Spikes apply damage before or after a passive type ability?” That is a mechanics test.

It can estimate line value under stated assumptions. Example: “In this position, if the opponent switches to Raikou 60% of the time and stays in 40% of the time, does Toxic or double-switch produce better expected position?”

It can compare policies. Example: “Policy A always sets a second Spikes layer when available. Policy B attacks if the opponent has an immediate setup threat. Which policy performs better across 1,000 randomized fixtures?”

It can find counterexamples. This is one of its best uses. A single clear failure can invalidate an over-broad heuristic.

A simulation cannot prove:

It cannot prove a global strategic rule from toy positions.

It cannot prove romhack truth if it uses vanilla Showdown mechanics.

It cannot prove opponent behavior unless the opponent model is realistic.

It cannot prove that a decision was good merely because the simulated win rate rose in a narrow fixture.

It cannot replace battle review, because many Pokémon errors are hidden in the setup of the position: wrong team assumptions, wrong set inference, wrong preservation priorities, or bad earlier trades.

To avoid self-deception:

Keep training scenarios, validation scenarios, and final holdout scenarios separate.

Perturb everything: HP, revealed moves, unrevealed sets, hazard state, sleep state, opponent policy, and damage rolls.

Run adversarial branches, not just average branches. Ask: “What if the opponent makes the move that punishes this heuristic hardest?”

Report confidence intervals, sample sizes, assumptions, and failure cases.

Never write “simulation proves X” unless X is a narrow mechanical statement. Use “simulation supports X under assumptions A/B/C.”

Cross-check simulator outputs against local damage calculators, source code, and emulator or fixture logs.

Maintain a “simulator mismatch ledger” for every place where Showdown, local scripts, and romhack behavior diverge.

Use toy sims as microscopes, not as world models.

## 6. Concrete battle-review protocol for 30+ turn games

The review protocol should be deterministic enough that two runs produce similar findings.

Step 1: Parse and reconstruct.

Create a turn-by-turn ledger:

```text
Turn:
Agent active / opponent active:
HP ranges:
Status:
Sleep / Rest counters:
Hazards:
Stat stages:
Revealed moves:
Likely unrevealed moves:
PP notes:
Immediate threats:
Own win conditions:
Opponent win conditions:
Irreplaceable pieces:
```

Step 2: Segment the game.

Divide the game into phases:

Opening: information gathering, hazards, early status, initial matchup plan.

Midgame: trades, Rest cycles, hazard control, revealing sets, preserving answers.

Conversion: when one side’s route becomes favored.

Endgame: PP, last defensive answers, final setup, final boom, final phazing route, or unavoidable damage sequence.

Step 3: Identify decision points.

Do not review every turn equally. Mark turns where one of these occurred:

A switch into possible Spikes damage.

A sleep move was used, missed, landed, or the target woke.

A Rest turn was available or forced.

A setup move was possible.

A phazing move was possible.

Explosion or Selfdestruct was possible.

A defensive answer could be preserved or sacrificed.

A hazard could be set, spun, blocked, or exploited.

A revealed move changed the matchup.

A move created or destroyed a win condition.

Step 4: For each marked turn, compare candidate lines.

For each serious candidate move, write:

```text
Move:
Immediate value:
If opponent stays:
If opponent switches:
If opponent sets up:
If opponent Rests:
If opponent uses status:
If opponent booms:
Worst plausible branch:
Resource gained:
Resource lost:
Does this preserve own win condition?
Does this preserve answer to opponent win condition?
Verdict:
```

Step 5: Separate luck from decision quality.

Use labels:

`Good decision / bad outcome`

`Bad decision / good outcome`

`Mechanics error`

`State-tracking error`

`Damage-range error`

`Win-condition error`

`Sacrifice error`

`Overfitted-script error`

`Information error`

`Romhack-transfer error`

Step 6: Find the earliest irreversible error.

The losing move is often not the move that loses the game. It may be the turn 11 switch that put the only answer into range, the turn 17 unnecessary Rest that gave setup, or the turn 22 sacrifice that made the opponent’s last threat unstoppable.

Step 7: Produce a review artifact.

Every reviewed battle should output:

An annotated log.

A resource timeline.

A list of 3–7 critical turns.

The earliest irreversible error.

One confirmed good heuristic.

One revised or rejected heuristic.

One new benchmark scenario extracted from the game.

## 7. How the agent should learn from mistakes

Use a closed loop.

```text
Mistake observed
→ exact position captured
→ cause classified
→ hypothesis written
→ controlled test designed
→ simulation or replay test run
→ result recorded
→ heuristic updated
→ benchmark added
→ future games checked for recurrence
```

Example:

Mistake: The agent used Sleep Powder, missed, then continued as though the opponent were disabled.

Cause: Overfitted-script error plus state re-evaluation failure.

Hypothesis: “After any sleep disruption, the correct policy is to recompute from current board state before taking any setup move.”

Test: Build 30 positions where a sleep line is interrupted by miss, first-turn wake, switch, Sleep Talk, or new threat reveal. Compare fixed-script policy against re-score policy.

Result: If re-score policy reduces catastrophic punishments and preserves win conditions more often, promote the heuristic. If some cases favor continuing the line, document exceptions.

Heuristic update: Add trigger, rule, exceptions, evidence, and benchmark IDs.

Future benchmark: `sleep_disruption_regression_001–030`.

The mistake loop must be ruthless about language. “I should be more careful with sleep” is not a learning update. “After a miss or wake, recalculate immediate KO threat, setup threat, and defensive-answer exposure before choosing any non-forcing setup move” is a learning update.

## 8. Handling romhack-specific mechanics

The agent should treat normal GSC as the base strategic grammar and the romhack as a mechanics fork.

The transfer rule:

Transfer principles, not conclusions.

Good transferable principles:

Switching has a cost.

Hazards convert repeated switches into progress.

Sleep creates temporary tempo but does not suspend the need to re-score.

Rest changes the time horizon.

Defensive answers can be more valuable than attackers.

Explosion is a route trade, not merely damage.

Setup is only good if the post-setup board remains safe.

Bad transferred conclusions:

“Spikes are subtle chip,” if the romhack has three layers.

“This Pokémon is the Snorlax answer,” if passive type abilities or changed learnsets alter the matchup.

“This Showdown calc proves the line,” if the romhack has different damage, type abilities, items, or move behavior.

“This GSC role map still applies,” if the romhack changes availability, trainers, AI behavior, or mechanics.

The agent should maintain a romhack delta register:

```markdown
# Romhack Delta: Spikes

Vanilla GSC:
- One layer.
- 1/8 HP on grounded switch-in.
- Removed by Rapid Spin.

Romhack:
- Number of layers:
- Damage per layer:
- Affected types:
- Ability/passive interactions:
- Removal behavior:
- Source file:
- Fixture test:
- Strategic implication:
- Heuristics affected:
```

For passive type abilities, each ability should get the same treatment:

```markdown
# Passive Type Ability: [Name]

Source:
Activation condition:
Timing:
Affected Pokémon/types:
Interaction with switch-in:
Interaction with hazards:
Interaction with status:
Interaction with phazing:
Interaction with damage calc:
Known edge cases:
Test fixtures:
Strategic implications:
```

The agent should not trust Showdown-style simulation for romhack decisions until it has validated the relevant mechanic. Showdown can still be useful for vanilla GSC reasoning, generic line testing, and rough damage intuition. It cannot be treated as the oracle for a modified Gold engine.

The source-of-truth order for romhack play should be:

1. Romhack source code.
2. Romhack documentation.
3. Emulator or fixture observations.
4. Local damage calculator built from source.
5. Custom simulator validated against fixtures.
6. Vanilla GSC resources.
7. Generic Pokémon intuition.

## 9. Drills the agent should run

The agent needs drills that punish scripted thinking.

Sleep/setup drills:

Give the agent positions where Sleep Powder, Hypnosis, Lovely Kiss, or Spore can create a setup turn. Then branch the scenario: hit, miss, immediate wake, switch, Sleep Talk, Explosion threat, phazer switch, or surprise coverage. The agent passes only if it re-scores after each branch.

Hazard pressure drills:

Set up positions with no Spikes, one vanilla Spikes layer, and romhack multi-layer Spikes. Ask the agent to choose between setting hazards, attacking, spinning, spinblocking, phazing, or preserving the setter. Score by long-term resource gain, not immediate damage.

Defensive switching drills:

Give the agent an opposing threat and multiple possible switch-ins. Some are expendable; one is irreplaceable. The agent must identify which defensive answer cannot be risked and choose a line that avoids losing to the opponent’s best punish.

Sacrifice drills:

Create positions where something must die or might be sacrificed for tempo. The agent must answer: “What route does this sacrifice open, and what route does it close?” A sacrifice is correct only if the gained route is real and the lost role is replaceable or no longer needed.

Endgame drills:

Use 2v2, 3v3, and 4v4 late-game states with Rest cycles, PP pressure, hazards, sleep counters, and phazing. The agent must map forced lines, not just pick strong attacks.

Win-condition recognition drills:

At several turns from a long log, hide the future and ask the agent to name own win conditions, opponent win conditions, and the piece each side must preserve. Then compare to the actual game.

Explosion drills:

Give positions where Explosion can remove a wall, stop setup, trade down, or lose the game. The agent must value the trade by future routes.

Rest timing drills:

Ask whether to Rest now, attack once then Rest, switch, phaze, or sacrifice. Include cases where Rest gives the opponent a free setup turn and cases where not Resting loses the only answer.

Phazing drills:

Ask when Roar/Whirlwind is progress, when it is emergency defense, and when it merely burns PP without changing the game. Include hazard and no-hazard variants.

Romhack delta drills:

For each changed mechanic, create paired vanilla/romhack positions. The agent must explain why the correct move changes or does not change.

## 10. Questions before every move

This checklist should be short enough to use in real positions but concrete enough to prevent vague play.

Before choosing a move, the agent should ask:

What is the exact current state? HP ranges, status, sleep turns, Rest turns, hazards, stat boosts, speed order, revealed moves, likely unrevealed moves, PP pressure.

What can immediately lose the game or make it unwinnable? Setup, Explosion, sleep, paralysis, phazing failure, hazard damage, loss of a defensive answer.

What is my current win condition? Has it changed since last turn?

What is the opponent’s current win condition? What piece stops it?

Which of my Pokémon are irreplaceable right now?

Which opposing Pokémon are irreplaceable for them?

What happens if the opponent stays in?

What happens if the opponent switches to their best answer?

What happens if the opponent uses Rest?

What happens if the opponent sets up?

What happens if the opponent uses Explosion or a sacrifice line?

What happens if my move misses, they wake, they fully paralyze me, or the damage roll is low?

Does this move create progress, or does it only feel active?

What resource am I gaining: HP, status, hazard state, PP, information, positioning, setup, removal of an answer, or endgame simplification?

What resource am I spending?

Does this move expose an irreplaceable answer?

After this move, what is my likely next turn? If there is no coherent next turn, the move is suspect.

“So what?” If the move works, what concrete winning route becomes better?

The “So what?” question is especially valuable in GSC because a move that does some damage or lands status may still fail to change the long-term position. Borat’s GSC guide makes this point bluntly: long-term foresight matters more than shallow prediction, and sacrifice for an extra attack is usually bad unless it connects to a clear win plan. ([Smogon][5])

## 11. How to tell when a heuristic is bad or too GPT-shaped

A heuristic is bad if it sounds wise but cannot choose a move.

Bad signs:

It uses vague verbs: “pressure,” “play carefully,” “keep momentum,” “preserve resources,” “be aggressive,” “avoid risk.”

It has no trigger condition.

It has no measurable board features.

It has no exceptions.

It ignores hidden information.

It ignores bad-luck branches.

It cannot explain what changes if the opponent switches, Rests, wakes, booms, or sets up.

It works only in the example that inspired it.

It says “always” or “never” without matchup conditions.

It is species-slogan thinking: “Skarmory walls physical attackers,” “Cloyster sets Spikes,” “Snorlax wins late,” without checking the actual state.

It is result-based: “This was right because I won.”

It is simulator-overfit: “This was right because one toy sim liked it.”

Convert vague advice into testable rules.

Bad:

“Preserve defensive answers.”

Better:

“Do not sacrifice the only remaining answer to the opponent’s active or unrevealed win condition unless one of these is true: the threat is already in guaranteed KO range; another answer has been confirmed; the sacrifice creates an immediate forced win; or the answer’s role is no longer needed because the opposing threat is dead, asleep with no relevant wake line, trapped, or PP-exhausted.”

Bad:

“Use sleep to set up.”

Better:

“After sleep lands, setup is legal only if the target cannot wake and immediately stop the line this turn, the expected switch-in does not force out the setup user, and the setup does not expose an irreplaceable defensive answer. After a miss, wake, or switch, discard the prior script and re-score.”

Bad:

“Spikes are good in long games.”

Better:

“In vanilla GSC, setting Spikes is high priority when the team can either keep them up or exploit the opponent’s spin attempts, and when the expected game involves repeated grounded switching or Rest cycles. Setting Spikes is lower priority if the setter gives a dangerous setup turn, the opponent can immediately spin with little cost, or the agent must preserve the setter for a different defensive role.”

## 12. Mastery benchmark suite

The suite should combine mechanics tests, position tests, full-game reviews, simulation tasks, and romhack fixtures.

A serious suite would include:

Mechanics oracle tests.

These verify exact behavior: Spikes damage and removal, sleep duration, Rest duration, Sleep Talk behavior, Roar/Whirlwind priority, Explosion behavior, Toxic behavior, crit rules, stat caps, passive type abilities, romhack hazard layers, and source-specific edge cases.

Curated position set.

At least 300–500 positions from GSC games, expert logs, self-play, and constructed adversarial states. Each position should include legal moves, state ledger, expert-preferred move class, acceptable alternatives, severe blunders, and explanation requirements.

Long-game log set.

At least 50 full 30+ turn battles. The agent must produce reviews, identify turning points, name win conditions, and classify errors. Some logs should be losses. Some should contain misleading lucky wins.

Sleep disruption set.

Positions where sleep plans are interrupted by miss, wake, switch, Sleep Talk, phazing, or Explosion. This directly tests the known lesson.

Hazard war set.

Positions involving Spikes setting, spinning, spinblocking, Pursuit support, phazing, and multi-layer romhack hazards.

Sacrifice and Explosion set.

Positions where a sacrifice is tempting but wrong, and positions where a sacrifice is necessary. Include Explosion trades that open a win condition and Explosion trades that throw away the game.

Endgame set.

Small remaining-team states requiring PP planning, Rest timing, hazard math, phazing, and forced-line recognition.

Romhack delta set.

Paired vanilla/romhack scenarios where the correct decision may change due to three-layer Spikes, passive type abilities, altered learnsets, altered damage, or trainer-specific constraints.

Written explanation exam.

The agent must justify decisions using concrete state facts. Explanations should be graded down for vague prose, missing alternatives, missing worst-case branches, or failure to update after new information.

Regression suite.

Every major mistake becomes a future test. If the agent repeats an old mistake, the corresponding heuristic is not learned.

Performance suite.

Run the agent against fixed baselines, self-play populations, and, if available, human or expert-reviewed games. Track win rate, but also track severe blunder rate, state errors, and decision agreement. Win rate without audit is not enough.

## 13. What the agent should avoid

Avoid short-term damage obsession. In GSC-style battles, the best move is often Rest, switch, phaze, set Spikes, spin, scout, or preserve a piece.

Avoid fixed scripts. “Sleep Powder into setup” is a plan only until the board changes.

Avoid ignoring wake turns. Sleep is a temporary condition with uncertain duration, not a permanent disable.

Avoid sacrificing irreplaceable pieces. A low-HP phazer, spinner, Ghost, Electric resist, Normal resist, or Snorlax answer may still be the only thing preventing a loss.

Avoid treating all sacrifices as momentum. Many sacrifices just reduce future options.

Avoid assuming Showdown accuracy equals romhack accuracy. This is especially dangerous with three-layer Spikes and passive type abilities.

Avoid importing vanilla GSC conclusions into the romhack without delta testing.

Avoid species slogans. Roles change with sets, HP, status, hazards, and mechanics.

Avoid ignoring Explosion. Both sides may have a route that depends on boom pressure.

Avoid ignoring Rest cycles. Rest is not just healing; it changes tempo, sleep state, and setup windows.

Avoid ignoring PP. In long games, PP can be a win condition.

Avoid “super effective” thinking. Actual damage ranges and long-term effects matter more than type-chart satisfaction.

Avoid one-game heuristic updates. A single game can suggest a hypothesis; it usually should not create a core rule unless it exposes a clear logical flaw.

Avoid overfitting to toy simulations.

Avoid hidden-info certainty. The agent should mark suspected sets separately from confirmed sets.

Avoid failing to ask “So what?” after every apparently productive move.

Avoid reviewing only the losing turn. The losing position is often created 10 turns earlier.

## 14. Pasteable long-running goal prompt

```text
Long-running goal: Become strategically competent at long-form Pokémon singles, using vanilla GSC singles as the base training environment and then transferring validated principles into the Pokémon Gold romhack / Gym Leader Lab setting.

Primary objective:
Develop a battle-playing policy that can make strong decisions in 30+ turn singles battles under hidden information, correct mechanics, long-term resource pressure, and romhack-specific rule changes. The goal is not to write impressive Pokémon commentary. The goal is to choose better moves, preserve winning routes, and learn from mistakes using falsifiable evidence.

Core definition of mastery:
A decision is good only if it improves or preserves the agent’s realistic winning routes from the current board state, accounting for mechanics, damage ranges, revealed and unrevealed information, hazards, status, sleep/wake states, Rest cycles, PP, phazing, Explosion, setup threats, sacrifice value, and long-term defensive requirements.

Training rules:
1. Treat vanilla GSC as the base strategic grammar.
2. Treat the romhack as a mechanics fork. Do not assume vanilla GSC or Pokémon Showdown behavior applies until verified against romhack docs, source, fixtures, or local tests.
3. Maintain a Markdown heuristics notebook. No heuristic may enter the core notebook unless it has trigger conditions, concrete board features, exceptions, evidence, counterexamples, and benchmark tests.
4. Maintain separate files for GSC mechanics truth, romhack mechanics truth, battle-state schema, decision checklist, role map, resource management, hazards, sleep/status/Rest, phazing/setup control, Explosion/sacrifice, win conditions/endgames, mistake ledger, simulation reports, battle reviews, benchmark suite, and romhack delta register.
5. Before every meaningful move, identify:
   - exact state;
   - own win condition;
   - opponent win condition;
   - irreplaceable pieces on both sides;
   - immediate losing branches;
   - likely opponent stay/switch/setup/Rest/status/Explosion lines;
   - resource gained and resource spent;
   - worst plausible branch;
   - next-turn plan;
   - answer to “So what does this move actually accomplish?”
6. Never follow a fixed script after the board changes. In particular, after a sleep move misses, a target wakes, a new move is revealed, a switch changes the matchup, or a bad-luck branch occurs, immediately re-score the position.
7. Use simulations only for bounded claims. Simulations may test mechanics, compare line assumptions, estimate policy behavior, and find counterexamples. They do not prove broad strategic truths unless validated across varied and held-out scenarios.
8. Every battle review must reconstruct the full state ledger, segment the battle into phases, identify critical turns, compare candidate lines, separate luck from decision quality, find the earliest irreversible error, and update exactly one or more heuristics or benchmark tests.
9. Every mistake must enter the loop:
   mistake → exact position → error class → hypothesis → controlled test → result → heuristic update → benchmark regression.
10. Every romhack mechanic difference must enter the delta register with source evidence, fixture evidence, strategic implications, affected heuristics, and validation status.

Initial study order:
1. GSC mechanics: Spikes, Rest, Sleep Talk, sleep duration, Roar/Whirlwind, Explosion, crit rules, stat caps, Toxic, PP.
2. Snorlax: playing with it, against it, and without it.
3. Spikes and switching: setting, keeping, removing, spinblocking, phazing, and exploiting hazard pressure.
4. Status economy: sleep, paralysis, poison, Heal Bell, and how status changes long-term routes.
5. Defensive answer preservation.
6. Rest-cycle and Sleep Talk management.
7. Phazing and anti-setup.
8. Explosion and sacrifice valuation.
9. Endgames, PP, and win-condition conversion.
10. Romhack-specific deltas: three-layer Spikes, passive type abilities, changed learnsets, changed damage, changed trainer/team context.

Required recurring drills:
- Sleep/setup disruption drills.
- Hazard pressure and spin drills.
- Defensive switching drills.
- Sacrifice valuation drills.
- Explosion trade drills.
- Rest timing drills.
- Phazing drills.
- Endgame forced-line drills.
- Win-condition recognition drills.
- Romhack delta drills comparing vanilla and modified mechanics.

Benchmark standards:
- Pass source-verified mechanics tests with no critical failures.
- Maintain accurate battle ledgers across long games.
- Achieve high agreement with expert-annotated move classes on unseen curated positions.
- Keep severe blunders below a defined threshold.
- Correctly identify win conditions and irreplaceable pieces in long games.
- Produce battle reviews that find the earliest meaningful error rather than merely the final losing turn.
- Demonstrate improvement on held-out benchmarks, not only on training scenarios.
- Preserve a regression suite so old mistakes stay fixed.

Forbidden learning habits:
- Do not optimize for sounding smart.
- Do not rely on generic advice like “keep momentum” or “play carefully.”
- Do not use win/loss alone as proof of decision quality.
- Do not confuse vanilla simulation with romhack truth.
- Do not continue plans after misses, wakes, reveals, or changed board states without re-scoring.
- Do not sacrifice irreplaceable defensive pieces without a concrete winning route.
- Do not write heuristics that cannot be tested in battle positions.

Output cadence:
After each study block, simulation block, or battle review, update the notebook with:
1. new facts learned;
2. changed heuristics;
3. rejected heuristics;
4. mistake patterns;
5. new benchmark scenarios;
6. unresolved questions;
7. next tests.

Success condition:
The agent is considered improving only when its future decisions in unseen long-game positions become measurably better: fewer state errors, fewer severe blunders, better preservation of win conditions, more accurate endgame planning, stronger romhack-specific mechanic handling, and battle explanations that are specific enough to be falsified.
```

[1]: https://www.smogon.com/forums/threads/gsc-mechanics.3542417/ "Resource - Gsc Mechanics | Smogon Forums"
[2]: https://www.smogon.com/gs/articles/gsc_spikes "Playing with Spikes in GSC - Smogon University"
[3]: https://www.smogon.com/gs/articles/guide_to_explosion "Explosion in GSC - Smogon University"
[4]: https://www.smogon.com/smog/issue28/gsc "Introduction to Competitive GSC - Smogon University"
[5]: https://www.smogon.com/gs/articles/gsc_guide_part1 "Borat's Guide to GSC — Part 1 - Smogon University"
