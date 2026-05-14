The blunt version: your training design is directionally good, but it can still fail by becoming a very large commentary engine. A long Markdown notebook can teach the agent to narrate GSC. It does not necessarily teach it to maintain a live threat ledger, abandon stale plans, model the opponent’s incentives, and choose the least-bad move under incomplete information.

I’d push the system away from “heuristics as prose” and toward “heuristics as tested state-transition policies.”

## 0. Source-verified mechanics baseline

These are the mechanics I would treat as verified for vanilla GSC unless your ROM or simulator fixture says otherwise.

In vanilla Generation II, Spikes has one layer. A grounded switch-in takes 12.5% max HP, rounded down, while Flying-types are immune; Rapid Spin removes Spikes from the user’s side. Smogon’s GSC mechanics resource also states that GSC Spikes originally had only one layer and always dealt 1/8 HP. ([Bulbapedia][1])

The three-layer Spikes table, 1/8, 1/6, 1/4, is not vanilla GSC. It appears in later core mechanics, documented for Generations III and IV. Your romhack can absolutely use that rule, but the agent must tag it as `fork:gll` or similar, not as `gen2:gsc`. ([Bulbapedia][1])

Rest restores HP to full, cures non-volatile status, and causes sleep. In Generation II specifically, Rest can be successfully called by Sleep Talk; it restores HP and resets the sleep duration. This matters enormously for evaluating whether “sleeping” a RestTalk user created progress or merely fed it recovery. ([Bulbapedia][2])

Sleep counting needs fixture-level precision. Smogon’s GSC status guide describes sleep as incapacitating a Pokémon for 1–6 turns and notes that GSC Pokémon can act on the turn they wake up; Bulbapedia describes Generation II sleep with a different counting convention. Do not let the agent write a sleep heuristic unless the test fixture defines exactly whether it is counting “sleep duration,” “turns unable to move,” or “wake-and-act turn.” ([Smogon][3])

Roar and Whirlwind in GSC are not generic modern phazing buttons. The Smogon GSC mechanics resource states that they need to go last to work, have -1 priority, and can fail in priority/speed interactions; Sleep Talk has priority 0 when it calls a move, which creates special cases. ([Smogon][4])

Explosion in GSC is not just “strong.” It is strategically different: Explosion is 250 base power and halves the target’s Defense, effectively making it 500 base power; if the Exploder moves first and the target survives, the target does not move that turn. The same Smogon guide emphasizes that Explosion is useful both for wallbreaking and emergency anti-sweep trades, but is not an automatic win button. ([Smogon][5])

For vanilla GSC strategic context, Snorlax is central, Cloyster is the chief Spikes user, Starmie is a premier spinner, Exeggutor and Gengar are major sleep / Explosion / utility threats, and phazers like Raikou, Skarmory, Suicune, Steelix, and Tyranitar shape long-game flow. Those are not trivia facts; they define the default threat-answer graph the agent must update during play. ([Smogon][6])

I did not find reliable public documentation for your exact “Gym Leader Lab” mechanics in the search I ran, so I would treat the romhack details you gave—three-layer Spikes, fourth click fails, Rapid Spin clears all, passive type abilities—as local truth only after ROM/simulator-backed fixtures prove them.

## 1. Where the design is most likely to fail

The biggest failure mode is heuristic accumulation without arbitration. The notebook will eventually contain “preserve defensive answers,” “make progress,” “set Spikes,” “use sleep windows,” “don’t waste Explosion,” “force Rest,” “don’t overpredict,” and “respect hidden information.” All of those can be true. The hard part is deciding which one wins on turn 27 when Cloyster is at 43%, Snorlax is asleep, Starmie may have Recover, and the opponent’s last unrevealed move changes the entire endgame.

Second, the agent may learn postgame language instead of turn-time decisions. A battle review can say “losing Skarmory was bad because Snorlax swept later,” but during the real turn the agent needs to know: “Skarmory is my only safe Normal resist; if I trade it now, I must either immediately remove Snorlax, force it to Rest, or have Explosion preserved. Otherwise this move is strategically illegal.”

Third, hidden-information leakage will poison the training. If reviews use the full replay to judge earlier decisions without reconstructing what was knowable at that time, the agent will learn clairvoyance. That looks smart in notebooks and collapses in live play.

Fourth, simulations can become decorative. A toy sim that says “sleep creates setup windows” is nearly useless unless it specifies the exact sleep distribution, wake behavior, miss rate, Sleep Talk sets, switch policy, and punish line. Simulations should certify bounded claims like “under this opponent policy and this sleep-turn convention, Curse is better than switching on turn N by X,” not broad claims like “sleep enables setup.”

Fifth, the romhack fork can quietly invalidate vanilla conclusions. Three-layer Spikes changes the value of switching, Rapid Spin timing, phazing, sacrifice pivots, and how expensive “scouting” becomes. Passive type abilities may invert matchups that vanilla GSC heuristics assume are stable. If the agent imports vanilla roles without a diff layer, it will make confident false moves.

Sixth, win-rate can lie. A bot can win games against weak opponents while still making strategically rotten decisions that only strong opponents punish. You need position benchmarks, earliest-mistake reviews, and calibration tests, not just ladder outcomes.

## 2. Missing capabilities between “knows GSC facts” and “plays 30+ turns well”

The agent needs a live resource ledger. Every turn it should track HP, status, sleep counters, PP, hazards, revealed moves, likely unrevealed moves, speed relationships, Rest cycles, Explosion availability, phazers, spinners, clerics, and who still answers each win condition.

It needs a threat-answer graph. Not just “Skarmory checks Snorlax,” but “Skarmory checks this Snorlax only if not asleep, not below X HP, not forced to Rest, and not removed by Explosion; if Skarmory is gone, my backup line is phaze with Raikou or trade with my own boom.”

It needs clock modeling. Long GSC-ish games are often decided by who is winning the passive future: hazards, poison, Rest turns, PP depletion, forced switches, and which side can safely click recovery. The agent must ask, every turn: “If no one lands a big prediction for ten turns, who improves?”

It needs plan invalidation. You already encoded this for sleep. Expand it. Any miss, wake, crit, reveal, unexpected damage roll, Rest, Spin, Explosion, forced switch, or PP threshold should trigger a board re-score. No script should survive contact with a new constraint.

It needs bounded tactical search. It cannot deeply search every branch for 30 turns, but it must search forced tactical pockets: sleep/setup, Explosion threat, forced Rest, phazing, Spin turns, last-mon PP, and moments where losing one defensive answer opens a sweep.

It needs uncertainty discipline. Hidden information is not a vibe. It should maintain a posterior over sets and update it from moves used, moves not used when they would have been strong, damage rolls, speed order, switching patterns, and impossible combinations.

It needs regret control. Sometimes the best move is not the highest expected-value move; it is the move that avoids the branch where you immediately lose to a known threat. Long-game play often rewards low-regret lines until you have identified the exact winning break.

## 3. What the agent should practice next

Stop adding general lessons for a while. Give it hard positions.

Each practice item should be a snapshot, not a paragraph: full public board state, legal mechanics namespace, known moves, revealed information, possible hidden sets, HP/status/PP/hazards, side conditions, and the agent’s team plan. The task is not “explain the position.” The task is “choose a move, rank the top three alternatives, name the catastrophe branch, and say what new information would change the decision.”

The next practice priorities should be:

Sleep windows where the correct answer changes after miss/wake/reveal.

Hazard-war turns where attacking, Spiking, spinning, switching, or booming are all plausible.

Rest-cycle turns where the agent must punish a sleeping Pokémon without losing to the switch.

Explosion turns where the agent must distinguish “good trade,” “panic trade,” and “throws away unique answer.”

Defensive preservation turns where a low-HP mon is still strategically priceless.

PP/endgame turns where the immediate best-looking move loses the long clock.

Hidden-info turns where the agent must infer from absence: “They did not click Rapid Spin / Roar / Recover / Sleep Talk when strongly incentivized; update the set distribution.”

## 4. Practical opponent-model tiers

Tier 0: legal-move model. The opponent can use any legal move and switch. This catches mechanical blunders but is strategically weak.

Tier 1: immediate punishment model. The opponent chooses among moves that KO, force Rest, set up, spin, phaze, explode, or safely switch to a counter. This should be the default minimum.

Tier 2: role-aware model. The opponent preserves their spinner, phazer, sleep absorber, Snorlax answer, Electric answer, Explosion user, and win condition. At this tier, the agent stops assuming the opponent will trade away key pieces for chip damage.

Tier 3: incentive model. The opponent asks the same strategic questions you do: “Who wins the hazard clock? What do I need alive? What can I reveal? What can I force?” This is the first tier that starts to resemble competent long-game play.

Tier 4: belief-state model. The opponent has uncertainty about your set too. They may scout, double, avoid obvious Explosion, or make a line that is robust to two or three of your possible sets.

Tier 5: style-conditioned model. After observing five to ten turns, classify the opponent’s risk tolerance: conservative preservation, aggressive doubling, hazard obsessive, Explosion-happy, setup-greedy, or PP/endgame patient. Use this only after evidence. Do not hallucinate personality from one move.

Tier 6: bounded adversarial search. At tactical inflection points, search the opponent’s best three responses, not all responses. The opponent should not be modeled as omniscient, but it should be modeled as unwilling to walk into known immediate loss.

The key: opponent modeling should be board-incentive first, psychology second.

## 5. How to evaluate candidate moves every turn

Use a two-stage evaluator: hard filters first, then scoring.

Hard filters:

A move is suspect if it allows an immediate known sweep, loses the only answer to an unrevealed but likely threat, lets the opponent remove your only progress engine for free, spends Explosion without opening a named win condition, Rests a required defender while the opponent has a free setup path, or ignores a forced PP/hazard endpoint.

Then score the survivors with a vector, not a single vague “goodness” number:

`MoveScore = immediate safety + wincon progress + opponent wincon denial + hazard/status clock + Rest/PP clock + defensive preservation + information gain - catastrophe risk - variance exposure`

For each legal move, evaluate against the top three opponent responses under the current opponent-model tier. Use shallow search by default: one player move, one opponent response, one follow-up. Extend to four to six plies only when a trigger appears: sleep, Explosion, phazing, Rapid Spin, Rest, low PP, possible sweep, or sacrifice.

The output should be:

“Best move: X. Acceptable alternatives: Y/Z. Losing-looking move: W. Main reason: preserves A while advancing B. Catastrophe branch avoided: C. Assumption that would change this: opponent has move D.”

That is much better than a pretty paragraph.

## 6. Core heuristic cards to encode first

### Card 1: Sleep script reset

Trigger: A sleep move misses, the target wakes, the opponent switches, Sleep Talk reveals Rest or coverage, or a new defensive answer is revealed.

Rule: Discard the planned setup script and re-score the whole board before choosing the next move.

Why it should be true: Sleep is a temporary and stochastic constraint, not a permanent permission slip. GSC also has Sleep Talk and wake-and-act behavior, so a sleeping target may still deny progress. ([Smogon][3])

Exceptions: If the opponent remains unable to stop the same forced line under all plausible wake/switch branches, continue.

Failure signs: The agent clicks a second setup move because “we slept them” while the opponent now has a live phazer, Explosion user, spinner, or Sleep Talk line.

Benchmark positions needed: At least 30 sleep positions: miss branch, one-turn wake branch, Sleep Talk Rest branch, sleep-absorber switch branch, and “sleep succeeded but wrong target” branch.

### Card 2: Unique defensive answer preservation

Trigger: A candidate move risks a Pokémon that is the only remaining answer to a known or high-probability win condition.

Rule: Do not trade or expose that Pokémon unless the move either removes the threat, creates an immediate winning line, or transfers the answer role to another resource.

Why it should be true: Long games are often lost before the sweep starts. The irreversible mistake is usually the earlier loss of the only answer.

Exceptions: Preserve nothing if the passive clock is already losing and only a risky trade creates a win path.

Failure signs: The agent sacrifices a low-HP Skarmory/Raikou/Starmie-equivalent because “it is weakened,” then later loses to the exact threat it still checked.

Benchmark positions needed: 40 positions where the endangered mon is low HP but strategically essential; include decoys where sacrificing it is actually correct because the win path is immediate.

### Card 3: Fork-aware Spikes value

Trigger: The agent can set, add, preserve, or remove Spikes.

Rule: Evaluate Spikes by expected future grounded switch-ins before removal, not by the abstract statement “Spikes are good.”

Why it should be true: Vanilla GSC has one layer, while your romhack has three. The value of a layer depends on spin control, groundedness, forced-switch capacity, and whether spending the turn invites setup. In GSC, Spikes play is tied to status, spinblocking, baiting spinners, and forcing switches, not merely clicking Spikes on sight. ([Bulbapedia][1])

Exceptions: Do not add a layer if the opponent can spin immediately and you cannot punish it; do not set hazards if the turn loses your only answer; do not chase layer three when layer one plus pressure already wins.

Failure signs: The agent clicks Spikes into a losing setup turn, or spins reflexively when attacking the spinner’s switch-in would win more.

Benchmark positions needed: 60 hazard-war positions: vanilla one-layer, romhack 0/1/2/3 layers, immediate spin threat, spin punish, phazer abuse, and “hazard greed loses” cases.

### Card 4: Rest-cycle exploitation

Trigger: A Pokémon uses Rest, is forced to Rest, or is about to wake.

Rule: Treat Rest as a temporary tempo transfer. Ask what two turns of reduced agency allow: Spikes, phazing, setup, safe switch, PP pressure, status elsewhere, or Explosion positioning.

Why it should be true: Rest fully restores and cures, but it also creates predictable turns. Sleep Talk complicates this by allowing action and, in GSC, potentially calling Rest again. ([Bulbapedia][2])

Exceptions: Do not “punish Rest” by giving a free switch to the opponent’s real win condition. Do not assume a RestTalker is passive.

Failure signs: The agent attacks a sleeping wall for small damage while missing a chance to set hazards, force a key switch, or position a breaker.

Benchmark positions needed: 50 Rest-cycle positions: non-Sleep Talk Rest, RestTalk with dangerous Sleep Talk rolls, wake turn, forced Rest, and choosing whether to attack or switch.

### Card 5: Explosion as named conversion, not emotion

Trigger: Explosion or Self-Destruct is available and can trade.

Rule: Boom only if the target removed is named, the win condition opened is named, and the Exploder is no longer required as a defensive answer.

Why it should be true: Explosion is a wallbreaking and anti-sweep tool in GSC, but its cost is absolute: your Pokémon faints. Its best use is often baiting a specific counter or stopping a specific sweep, not “getting damage.” ([Smogon][5])

Exceptions: Emergency Explosion is correct if the alternative is immediate loss. Bait Explosion is correct if the target’s likely switch is the one blocking your win.

Failure signs: The agent booms into a redundant wall, booms while the opponent’s real answer remains, or refuses to boom against a boosted sweeper because it is “saving resources.”

Benchmark positions needed: 40 Explosion positions: bait boom, defensive boom, bad boom into resist/Ghost, boom that opens a sweep, boom that loses unique answer.

### Card 6: Phazing must beat the actual setup line

Trigger: Opponent boosts, passes boosts, Rests with boosts, or threatens a long setup line.

Rule: Use Roar/Whirlwind only when it actually resolves under the format’s mechanics and improves the future board.

Why it should be true: GSC Roar/Whirlwind have unusual priority and failure behavior; “phaze setup” is not enough as a heuristic. It must account for speed, priority, Sleep Talk, matchup, and what comes in after phazing. ([Smogon][4])

Exceptions: Sometimes attacking or Exploding is better if phazing merely resets the opponent into a better hazard/status clock.

Failure signs: The agent clicks phazing because “they boosted” while moving too early, failing, or letting the opponent’s switch-ins farm hazard advantage.

Benchmark positions needed: 30 phazing positions: slower phazer works, faster phazer fails, Sleep Talk phazing, phaze-versus-attack, phaze-versus-Explosion.

### Card 7: Sacrifice must buy a concrete asset

Trigger: A mon is low HP, statused, asleep, trapped, or apparently expendable.

Rule: A sacrifice is only good if it buys one of: safe entry, forced Rest, hazard removal, hazard layer, revenge KO, Explosion target, PP endpoint, or information that changes the line.

Why it should be true: In long games, a 12% mon can still be the only pivot, sleep sack, Explosion absorber, PP sink, or emergency phazer.

Exceptions: Sacrifice freely when the mon has no remaining role under any plausible hidden set and preserving it costs tempo that loses the game.

Failure signs: The agent sacks “dead weight” that later would have absorbed sleep, blocked Explosion, forced a switch, or preserved a PP line.

Benchmark positions needed: 35 sacrifice positions with hidden utility, plus 15 where the sacrifice is correct.

### Card 8: PP/endgame clock before damage greed

Trigger: Low PP, repeated Rest cycles, last two or three Pokémon, or no reliable breaker remains.

Rule: Before choosing damage, compute whether the line wins by PP, forced recovery, hazard re-entry, or status clock.

Why it should be true: Long-form GSC-ish games often reach positions where immediate damage is less important than preserving the move that wins the final loop.

Exceptions: If a high-variance attack is the only way to avoid an unwinnable PP future, take it.

Failure signs: The agent spends limited PP into obvious recovery, reveals the wrong move, or loses a last-mon sequence it could have drawn/won by conserving PP.

Benchmark positions needed: 40 PP/endgame positions: Rest loops, phazer PP, Recover PP, attacking PP, last-mon hazardless endings, and “must attack now before PP lock” cases.

## 7. Exact benchmark suite I would trust

I would not be convinced by “the notebook is large” or “the agent wins sometimes.” I would want this:

Mechanics fixtures: 150 tests. Include vanilla GSC Spikes, romhack Spikes, Rapid Spin, Rest, Sleep Talk calling Rest, sleep duration convention, wake-and-act, Roar/Whirlwind priority/failure, Explosion turn effects, Toxic downgrade on switch, Leftovers/residual order, damage rounding, PP depletion, and hidden set legality.

Curated turn-decision set: 300 positions. Balanced across sleep, hazards, Rest cycles, phazing, Explosion, sacrifice, defensive preservation, PP/endgames, hidden-info inference, and romhack fork mechanics. Each position should have expert-labeled move tiers: best, acceptable, dubious, catastrophic. Do not require exactly one move unless the position truly has one.

Line-play suite: 80 scenarios of 4–8 turns each. The agent chooses every turn, with stochastic branches fixed by seed. Score not only final result, but whether it re-scored after reveals and avoided known catastrophe branches.

Replay review suite: 60 full battle logs. The task is to identify the earliest irreversible mistake, not the final losing turn. The answer must include the board state at that turn, the resource lost, the counterfactual move, and why later play could not fully repair it.

Hidden-info calibration suite: 100 partial-information positions. The agent must assign probabilities to likely sets or moves. Grade with Brier score / log loss, not just “did it guess right.”

Romhack transfer suite: 120 paired positions. Each pair has a vanilla version and a romhack version. The correct move should sometimes stay the same and sometimes flip. This catches lazy transfer.

Regression suite: every serious mistake becomes a frozen test. The test should fail if the agent repeats the same reasoning error, not merely the same move.

Minimum gates I’d require before calling it strategically competent:

Mechanics fixtures: 98% pass.

Curated decisions: 80% best-or-expert-acceptable, under 5% catastrophic.

Line-play: 70% of scenarios maintain or improve expert-assessed equity through the critical turn.

Replay review: earliest irreversible mistake within three turns of expert label in 75% of logs.

Hidden-info calibration: materially better than static usage priors.

Romhack transfer: 80% correct on paired positions where the fork changes the right answer.

Regression: no recurrence of previously fixed catastrophic mistakes across two evaluation runs.

## 8. Battle review protocol for earliest irreversible mistake

Review from the player’s perspective, not the omniscient replay perspective.

For every turn, reconstruct:

Public board state.

Known moves and known PP.

Unrevealed possibilities.

Current win conditions for both sides.

Threat-answer graph.

Hazard/status/Rest/PP clocks.

Candidate moves available.

Opponent’s top three incentive-compatible responses.

Then ask: “After this turn, what resource became unrecoverable?”

Classify mistakes like this:

Mechanical mistake: illegal or misunderstood mechanic.

Threat mistake: allowed a known immediate or eventual sweep.

Preservation mistake: lost the only answer to a key threat.

Clock mistake: shifted hazard/status/PP future against yourself.

Information mistake: ignored a reveal or inferred too much.

Conversion mistake: had a winning resource but failed to convert it.

Variance mistake: took a high-risk line when a robust line existed, or refused necessary risk when the passive future was lost.

Earliest irreversible mistake means: the first decision after which the player’s previous stable win/draw path required opponent error, extreme RNG, or a later compensating blunder. The final KO is usually not the mistake. It is the autopsy photo.

## 9. Dangerous GPT-shaped Pokémon heuristics

“Keep momentum.” Bad. Momentum must mean a concrete next-state advantage: safe entry, forced switch, hazard turn, setup turn, information, or denial of recovery.

“Preserve your win condition.” Bad unless the win condition is named and its blockers are named.

“Set Spikes early.” Bad. Correct version: set Spikes when expected future grounded switch-ins before removal justify the turn and the turn does not expose a higher-priority threat.

“Use sleep to set up.” Bad. Correct version: sleep creates a possible setup window only against branches where the target stays asleep, lacks Sleep Talk disruption, cannot switch to a phazer/check, and the setup actually changes the matchup.

“Explosion removes walls.” Bad. Explosion removes one Pokémon if it lands into the right target. The question is whether that target is the bottleneck.

“Don’t overpredict.” Bad. Sometimes the obvious safe move loses slowly. The real rule is: choose the line with the best regret profile against the opponent’s incentive-compatible responses.

“Phaze setup sweepers.” Bad in GSC unless the phazing move resolves and the post-phaze board is better.

“Status is always progress.” Bad. Status into Rest, Heal Bell, Natural Cure in non-GSC formats, or the wrong sleep absorber may be neutral or negative.

“Scout with switches.” Bad in hazard-heavy forks. Scouting has a price. In three-layer Spikes, a scout can be a quarter of a grounded Pokémon’s HP.

“Snorlax is central.” True, but useless as a move rule. Better: “Before risking a Normal resist, name the opponent’s Snorlax set hypotheses and your remaining answers to each.”

## 10. Vanilla GSC to romhack transfer

Transfer causal concepts, not conclusions.

Good transfer: hazards tax switching; Rest creates cycles; Explosion converts resources; phazing punishes setup; PP matters; status changes clocks; defensive answers must be preserved; hidden sets must be inferred from incentives.

Bad transfer: “Spikes is one layer,” “this Pokémon is always the spinner,” “this matchup is safe,” “this Flying-type interaction still holds,” “this Rest cycle has the same punish window,” “this status target is good because it is good in GSC.”

Build a fork-diff card for every mechanic change:

Mechanic changed.

Affected move values.

Affected roles.

Affected heuristics.

New failure modes.

Required fixtures.

Required paired benchmarks.

For your local three-layer Spikes, the agent should not merely say “hazards are stronger.” It should compute layer value:

`Expected layer value = incremental damage × expected grounded switch-ins before removal - turn cost - punish risk - spin risk`

Layer two and layer three need their own break-even tests. In a fork where Rapid Spin clears all layers, the value of the third layer may be high only when spin is blocked, punished, impossible, or too slow.

Passive type abilities are even more dangerous. They may alter immunities, switch safety, damage ranges, setup permissions, and defensive-role identity. The agent should treat type passives as matchup-changing mechanics, not flavor text.

## 11. Concrete drills

Sleep/setup drill: Give 25 positions where sleep lands, misses, wakes early, or hits a Sleep Talk user. The agent must choose whether to set up, attack, switch, or abandon the plan. Regression target: no “continue script” move after a miss/wake/reveal.

Sleep target drill: Give common sleep users against teams with one obvious sleep absorber and one hidden bigger threat. The agent must decide whether to sleep now, attack the absorber, double, or hold sleep.

Hazard-war drill, vanilla: Cloyster/Starmie/Forretress-style positions with one-layer Spikes. The agent must choose between Spikes, Rapid Spin, Toxic/status, attack, switch, or Explosion. Score by future hazard control, not immediate HP only.

Hazard-war drill, romhack: Same positions with 0/1/2/3 layers. Include fourth Spikes fail. The agent must identify when the next layer is worth a turn and when it is greed.

Rest-cycle drill: Force a wall to Rest. The agent must pick the best punish: setup, Spikes, phaze, switch to breaker, PP stall, or attack. Include RestTalk variants where attacking into Sleep Talk is dangerous.

Phazing drill: Build GSC-specific Roar/Whirlwind positions with speed/priority traps. The agent must predict whether phazing resolves and whether it improves the board.

Explosion drill: Give bait-boom and panic-boom positions. The agent must name the target, the opened win condition, and the defensive role lost by booming.

Sacrifice drill: Present three possible sacks. One is low HP but still essential, one is healthy but strategically redundant, one buys safe entry. The agent must justify the sack by resource purchased.

Defensive preservation drill: Repeatedly tempt the agent to risk its only answer for damage or hazards. The right move is often boring. This is where many “smart-sounding” agents die.

PP/endgame drill: Last three Pokémon, limited PP, Rest/Recover loops. The agent must produce a PP plan before choosing a move.

Hidden-info set inference drill: Hide two moves. The opponent’s prior choices imply likely set constraints. The agent must update probabilities and choose a move robust to the top two sets.

Bad-luck branch drill: The agent makes a correct move, then suffers miss/crit/early wake. The task is to recover, not complain. It must re-score from the new board and choose the best salvage line.

## 12. Simulations: what they can and cannot prove

Use simulations to answer bounded questions.

Good simulation claim: “In this exact board state, if the opponent switches Starmie into Cloyster at least 45% of the time and we can punish Spin with Explosion, Spikes has higher expected value than Surf over the next four turns.”

Bad simulation claim: “Spikes is better than attacking.”

Good simulation claim: “Against this RestTalk distribution, setting up once after sleep has positive EV only if wake probability and Sleep Talk damage are below this threshold.”

Bad simulation claim: “Sleep creates setup windows.”

Good simulation claim: “If Rapid Spin clears all three local layers, layer three is worth clicking only when expected grounded switch-ins before Spin exceed N, or when Spin can be punished by KO/trade.”

Bad simulation claim: “Three-layer Spikes means always stack hazards.”

Simulations cannot prove broad strategy unless the opponent policy, hidden-set distribution, mechanics, and evaluation objective are realistic. They can falsify bad heuristics, find break-even thresholds, and generate benchmark positions. That is enough. Do not ask them to be oracles.

## 13. What requires human/expert judgment

Expert judgment is needed to label strategic move tiers, decide which risks are acceptable in a losing passive clock, identify whether a sacrifice really transfers a defensive role, judge whether a hidden set posterior is reasonable, and decide when “technically safe” play is too slow to win.

Human review is also needed for romhack transfer. A simulator can tell you the mechanics. It cannot automatically tell you which vanilla concepts survived the fork.

## 14. Operational definition of mastery

I would define mastery for this agent as follows:

It tracks the board without drift for 30+ turns.

It can name both players’ live win conditions every turn.

It preserves unique defensive answers unless it can prove compensation.

It updates hidden-set beliefs from actions and non-actions.

It recognizes when the passive clock is winning or losing.

It uses sleep, Spikes, Rest, phazing, Explosion, sacrifices, and PP as resources with costs, not slogans.

It performs well on unseen benchmark positions, not just on replays it studied.

It can explain a move as a state transition: “This move keeps A alive, threatens B, denies C, improves D clock, and loses only to E branch.”

It finds the earliest irreversible mistake in its own losses.

It improves through regression tests: once a mistake is fixed, it stays fixed.

The sharpest standard: when the agent loses, its review should usually reveal either a reasonable risk that failed, a hidden set that was genuinely hard to infer, or a known benchmark gap. If the review instead says “we followed the plan” after the board changed, the agent is still pretending to play long-form Pokémon rather than playing it.

[1]: https://bulbapedia.bulbagarden.net/wiki/Spikes_%28move%29 "Spikes (move) - Bulbapedia, the community-driven Pokémon encyclopedia"
[2]: https://bulbapedia.bulbagarden.net/wiki/Rest_%28move%29 "Rest (move) - Bulbapedia, the community-driven Pokémon encyclopedia"
[3]: https://www.smogon.com/gs/articles/status "Introduction to Status in GSC - Smogon University"
[4]: https://www.smogon.com/forums/threads/gsc-mechanics.3542417/ "Resource - Gsc Mechanics | Smogon Forums"
[5]: https://www.smogon.com/gs/articles/guide_to_explosion "Explosion in GSC - Smogon University"
[6]: https://www.smogon.com/smog/issue28/gsc "Introduction to Competitive GSC - Smogon University"
