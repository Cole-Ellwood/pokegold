## 1. Diagnosis

The agent’s biggest blind spot is probably **decision compression**: turning a messy board state into one ranked move, with a reason that survives the next two turns. A large cookbook, boss sheets, route maps, and mechanics notes can create the appearance of competence while still failing at the only thing that matters live: “Given this exact position, what move has the best worst-case path to winning?”

Its second blind spot is likely **resource identity**. It may know phrases like “preserve your win condition,” but not reliably identify which piece is actually irreplaceable right now. In GSC-like singles, the irreplaceable piece may be the only sleep absorber, the only defensive answer to a remaining sweeper, the only fast revenge killer, the only phazer, the only spinner, the only wallbreaker, or the only Pokémon that can safely eat a known Explosion. That changes turn by turn.

The third blind spot is **branch pricing**. It probably evaluates “my move works if it hits” or “this switch is safe if they attack normally,” but not: what if the boss uses its best plausible move, gets a high roll, reveals coverage, wakes, crits, switches, spins, Explodes, or forces a Rest cycle? The move choice has to price the worst plausible branch, not just the average branch.

The fourth blind spot is **format-transfer error**. Smogon GSC is an excellent training ground, but this is a GSC-based romhack, not vanilla GSC. For example, vanilla GSC sources treat Spikes as one layer, while your local evidence points toward three-layer Spikes behavior in the romhack; that means hazard policy can transfer, but exact hazard math cannot be imported blindly. Smogon’s GSC resources are still the right backbone for studying Spikes, status, Explosion, priority, and old-gen pacing, but every local mechanical claim needs a validation tag. ([Smogon][1])

It is probably overdoing **notebook growth, route-map polish, and tooling**. A note is valuable only if it changes a move choice under pressure. A simulator is valuable only if it prevents a wrong line, exposes a branch, or verifies a mechanic. A boss sheet is valuable only if it says, before the battle, “these are the three things we cannot lose; these are the two ways we win; this is what changes after a crit/miss/reveal.”

It should stop, reduce, or quarantine the following:

Stop claiming mastery. Do not talk about the 80%-over-50 gate as if it is close until the simulator, boss AI, mechanics, and battle-review process are validated.

Reduce new cookbook recipes. Most future improvement should come from studying expert games, pausing turns, predicting lines, reviewing misses, and rewriting policies.

Quarantine all unverified mechanics. The live advisor should say “vanilla GSC expectation,” “romhack verified,” or “unknown; choose robust line.” Mechanics hallucination is worse than silence.

Quarantine Snorlax-centric conclusions. GSC Snorlax material is useful for anchor play, Rest cycles, defensive compression, and over-preservation mistakes. But “Snorlax is central” should become “identify the central anchor,” not “act like Snorlax exists in every route.” Smogon’s own GSC introduction warns against over-conserving Snorlax as if it were always worth warping the whole game around, which is exactly the kind of lesson that should be abstracted rather than copied species-first. ([Smogon][2])

Reduce local-example dominance. Your sparse Gym Leader Lab examples are precious as eval prompts, but they should not become the curriculum. The curriculum should mostly be expert play plus local validation.

Evidence that it is improving would look like this:

The agent’s top move or top two moves match a strong review process more often over time.

It catches missing state before giving advice, but does not stall with endless questions.

Its recommendations name the current win condition and irreplaceable pieces before choosing the move.

It predicts the next two turns more accurately: “If they do X, we do Y; if they reveal Z, plan changes.”

Mechanics errors drop to zero in reviewed advice.

In battle reviews, the earliest meaningful mistake moves later in the game.

It produces fewer generic phrases and more policies with triggers: “Use Rest here because this mon only needs to survive two more hits and no longer needs immediate tempo,” not “Rest to stay healthy.”

## 2. Next 20 Hours

Spend the next 20 hours mostly on expert source study and replay review. Tooling and notebook work should be capped. The agent does not need more impressive structure; it needs more trained judgment.

### Expert source study — 6 hours

Read first from Smogon’s Gold/Silver competitive resources: GSC metagame guide, Explosion, move priority, status, Spikes, OU speed tiers, sample teams, and selected Pokémon analyses by role. Smogon’s G/S resource page explicitly groups these as mechanics/guides, tier-specific OU guides, and sample teams, which makes it a good syllabus spine. ([Smogon][1])

Artifact: a **source-to-policy ledger**, not a summary. Every useful idea must become one of these:

“Trigger: ___”

“Default move/policy: ___”

“Do not apply when: ___”

“Local mechanics status: verified / vanilla-only / unknown”

“Example turn: ___”

Target: 25 policies, no longer than 90 words each.

The first 6 hours should be divided roughly like this:

1.5h on Spikes, Rapid Spin, forced switches, and residual damage. Smogon’s GSC Spikes article emphasizes that Spikes persist until Rapid Spin and cannot simply be Rested off like Toxic, while also noting the team-cost of fitting Spikes and Spin support. That should become hazard timing policy, not just “hazards good.” ([Smogon][3])

1.5h on status, sleep, RestTalk, and status-slot discipline. Smogon’s GSC status article is especially useful because it distinguishes primary status from pseudo-status and explains why Sleep Talk changes the value of sleep in GSC. ([Smogon][4])

1h on Explosion/Self-Destruct trade logic. Smogon’s Explosion guide is valuable because it frames Explosion as offensive, defensive, and tactical, while also warning that it is not an automatic win button. ([Smogon][5])

1h on sample teams and analyses: do not copy teams; extract role maps. For each team, identify the anchor, hazard plan, status plan, wallbreaker, emergency button, and endgame converter.

1h on cross-generation concepts from ADV/DPP/later gens: extract only abstract decision skills such as preserving defensive answers, forcing progress, sequencing status before setup, and not over-predicting. Ignore generation-specific mechanics unless locally validated.

### Battle-log / replay review — 5 hours

Use high-quality GSC OU tournament replays as the main corpus. There is now a large public replay/statistics resource for Gen 2 OU with 19,194 public Smogtours replays and 38,388 teams through April 4, 2026, and it can search by user, opponent, date, Pokémon, moves, and result. Treat that as a replay-finding tool, not as proof of strategic truth. ([Smogon][6])

Artifact: a **paused-turn atlas** of 40 decision points.

Each entry:

Turn number.

Known board state.

Hidden information.

Candidate moves.

Expert’s chosen move.

Why it may have been chosen.

What branch it protects against.

What lesson transfers to Gym Leader Lab.

Review 8 to 12 games, but do not watch them passively. Pause before meaningful turns: lead turns, first hazard turn, first sleep/status decision, first double/switch, first Rest, first Explosion threat, first revealed coverage move, first irreversible sacrifice, first endgame commitment.

### Live-turn drills — 3 hours

Artifact: a **scored live-advice prompt set**.

Create 60 one-turn prompts from three sources:

20 expert replay pauses.

20 Gym Leader Lab / boss-sheet states.

20 synthetic disaster states: miss, crit, unexpected coverage, early wake, bad damage roll, wrong AI assumption.

For each prompt, the agent has 90 seconds to answer using the live protocol in section 4. Score it on:

Did it choose a move?

Did it name the win condition?

Did it identify irreplaceable pieces?

Did it price the worst plausible branch?

Did it avoid mechanics hallucination?

Did it give a next-turn contingency?

Target after 3 hours: at least 45/60 answers have a usable ranked recommendation. Not perfect. Usable.

### Boss-route planning — 2 hours

Artifact: two **one-page boss route cards**, not long route maps.

Each boss card should contain:

Expected enemy order or switch behavior if known.

Our two main win conditions.

Our one emergency win condition.

Irreplaceable pieces and why.

Known dangerous turns.

Required calcs.

Sleep/status target priority.

Hazard plan.

Sacrifice permissions.

Explosion permissions.

Plan revision rules after miss/crit/reveal.

This should be compact enough to use during a live battle. If it cannot be read in 30 seconds, it is too long.

### Simulator / calculator grounding — 2 hours

Use the Pokémon Showdown calculator and local romhack tools for grounding, not decision outsourcing. The Showdown calculator supports RBY through modern generations, and the official Smogon damage-calc repository says it implements damage calculation mechanics across generations; that is useful for vanilla reference, but the romhack still needs local verification. ([Pokémon Damage Calculator][7])

Artifact: a **mechanics-and-calc truth table**.

Include:

10 important damage ranges for current bosses.

5 speed-order checks.

5 status/sleep/Rest interactions.

5 hazard/Spin checks.

5 AI behavior checks.

5 “known unknown” entries.

Every entry gets one label: verified in romhack, vanilla reference only, contradicted by romhack, unknown.

### Notebook maintenance — 2 hours

Artifact: a **live cookbook v2** capped at roughly 30 active entries.

Each entry must be short enough to use mid-battle. Anything not used in live advice, drills, or reviews gets archived. The notebook should become less impressive and more useful.

## 3. Study Method

The agent should read Smogon and expert games with one question in mind: **what would this change on a turn?** If the answer is “nothing,” it is flavor, not training.

Read first in this order:

Smogon G/S competitive resources overview.

GSC Spikes.

GSC Status.

GSC Explosion.

GSC mechanics / priority / speed tiers.

GSC sample teams.

GSC Pokémon analyses by role.

Then tournament replays.

Then ADV/DPP/later-gen material for abstract decision concepts only.

The reason to start with GSC is not that Gym Leader Lab equals vanilla GSC. It does not. The reason is that GSC teaches old-gen singles resource management: limited recovery, Rest cycles, sleep/status slots, hazard persistence, phazing, Explosion trades, imperfect damage information, and long endgames. Those are transferable.

When annotating expert games, the agent should not write “good switch” or “nice prediction.” Those are useless. It should write:

“Turn 8: player declines immediate damage to keep Zapdos/Raikou check healthy.”

“Turn 13: Explosion is threatened, so opponent moves to Pokémon that can survive or makes the Exploder’s trade low-value.”

“Turn 22: Rest is chosen not because HP is low, but because the opponent cannot punish two sleep turns.”

“Turn 31: Spikes value has exceeded direct attack value because opponent must switch three more times.”

“Turn 40: player stops preserving the anchor because it has completed its defensive job.”

That is decision skill.

To convert a concept into a turn policy, use this template:

Concept: “Spikes creates durable progress.”

Policy: “Use Spikes when the opponent is likely to switch, when the spiker is not needed as an immediate defensive answer, and when future forced switches are expected. Do not use Spikes when the active threat can 2HKO something irreplaceable, when the spiker must remain healthy for a later check, or when the battle can be won immediately by attacking.”

Concept: “Explosion trades can unlock endgames.”

Policy: “Use Explosion only when removing this target unlocks a named route, prevents a worse loss, or trades a replaceable piece for an irreplaceable enemy piece. Do not Boom merely for momentum.”

Concept: “Sleep is powerful but can be wasted.”

Policy: “Use sleep on a target that loses a role while asleep and is not an intended sleep absorber. Do not spend sleep into a Sleep Talk user or a target whose sleep does not advance a named route.”

To avoid overfitting to one format or one Pokémon, every lesson must be rewritten without species names. “Preserve Snorlax” becomes “preserve the central defensive anchor while it still answers unrevealed threats.” “Don’t overpreserve Snorlax” becomes “once the anchor’s unique jobs are done, it can be traded for progress.” “Cloyster sets Spikes” becomes “hazard setter creates durable progress only when it can survive the tempo loss.”

When abstracting ADV/DPP/later-gen lessons back into GSC-like boss battles, strip the lesson down to this chain:

Role → resource → trigger → branch → exception.

For example, a later-gen replay about preserving a Choice Scarf revenge killer becomes: “Preserve the only speed-control piece until all faster sweepers are gone or in guaranteed KO range.” The fact that Choice Scarf may not exist in the romhack is irrelevant. The resource is speed control.

A DPP hazard-stack lesson becomes: “Hazards matter when they convert forced switches into KO thresholds.” The exact Stealth Rock mechanics do not transfer. The threshold logic does.

An ADV sand/status lesson becomes: “Passive damage is strongest when paired with denial of recovery or forced cycling.” The exact weather mechanics do not transfer. The residual-pressure concept does.

## 4. Live Battle Advice Protocol

When the user asks, “What do I do now?”, the agent should use this exact format.

**Recommended move: [move/switch] — confidence [high/medium/low].**

One sentence explaining the route:

“We choose [move] because our win condition is [X], and this line preserves [Y] while covering the worst plausible [Z].”

Then:

**State read**

Active matchup:

Our HP/status/boosts:

Enemy HP/status/boosts:

Hazards/screens/weather:

Known enemy moves:

Important unknowns:

**Win condition**

Primary:

Backup:

What must not die yet:

**Candidate ranking**

1. [Best move] — What it gains. What it loses to. Worst plausible branch. Next-turn plan.

2. [Second move] — Why it is worse or more conditional.

3. [Emergency move] — Use only if [specific condition].

Do not choose: [move] because [specific punishment].

**Next turn**

If they [attack/switch/reveal/wake/Rest/Explode], do [next action].

**Missing info**

Need: [only the 1–3 missing facts that could change the move].

Required state inputs, ideally:

Current active Pokémon on both sides.

Exact HP or approximate HP bands.

Status, boosts, screens, weather, terrain if any.

Hazards and layers, with romhack validation status.

Our full remaining team: HP/status/items/moves/PP if relevant.

Opponent remaining team: revealed and unrevealed.

Known enemy moves and likely hidden moves.

Speed order if known.

Previous turn action and damage.

Boss AI pattern if known.

Ruleset: set/switch mode, items allowed, level caps, reset/death constraints.

Relevant romhack mechanics flags.

If state is missing, the agent should not ask twelve questions. It should ask for the minimum needed to avoid fake precision:

“Send the battle screenshot plus our party HP/moves. The facts that could change this move are: enemy HP, our active’s moves, and whether [enemy move] has been revealed.”

If enough state exists to act, it should still recommend a move:

“Assuming enemy [coverage move] is not revealed, I’d [move]. If it has [coverage], switch to [answer] instead.”

Candidate moves should be ranked by:

Does it preserve the primary win condition?

Does it protect irreplaceable pieces?

Does it avoid immediate loss?

Does it make progress against the boss route?

Does it survive the worst plausible branch?

Does it reduce hidden information risk?

Does it rely on low-probability RNG?

Does it keep a recoverable position after miss/crit/wake/reveal?

Irreplaceable pieces should be named explicitly:

“[Pokémon A] is irreplaceable because it is the only answer to [enemy B].”

“[Pokémon C] is no longer irreplaceable because [enemy D] is dead.”

“[Pokémon E] can be sacrificed only if it gets [enemy F] into [move] range.”

Worst plausible branch does not mean “they crit every turn forever.” It means the strongest realistic punishment: high roll, likely coverage, obvious switch, early wake, miss on an inaccurate move, boss AI choosing its best damaging move, Explosion, Rapid Spin, forced Rest, or an unrevealed set consistent with known data.

Uncertainty should be expressed like this:

“Medium confidence. The recommendation changes only if [specific hidden move] exists or if [HP] is below [threshold]. Without that, [move] is best because it keeps both routes alive.”

Not like this:

“It depends; maybe attack or switch.”

The agent must still be useful.

## 5. Drills

### Turn-1 planning drill

Input: our six, boss six, lead matchup, known mechanics flags.

Output in 90 seconds:

Primary win condition.

Backup win condition.

First three turns if no surprise.

Sleep/status target.

Hazard plan.

Irreplaceable pieces.

What reveal changes the plan.

Scoring: fail if it cannot name what must be preserved. Turn-1 plans that only say “lead with X and set up” do not count.

### 30+ turn route-tracking drill

Use an expert replay or a synthetic boss battle. Every turn, update a resource ledger:

HP.

Status.

PP.

Hazards.

Revealed moves.

Sleep turns.

Rest cycles.

Explosion users.

Known speed order.

Enemy win condition.

Our win condition.

Scoring: one point per turn for a correct ledger. Lose points for forgetting status, PP, unrevealed threats, or a Pokémon’s remaining job. The purpose is to train memory under long-game pressure.

### Plan-revision drill

Start with a planned route. Then inject one event:

Move misses.

Opponent crits.

Opponent wakes early.

Boss switches unexpectedly.

Opponent reveals coverage.

Damage is higher/lower than expected.

Our intended sacrifice survives.

Enemy uses Rest.

Enemy Spins.

Enemy Explodes.

Output in 45 seconds:

What changed?

What route died?

What route opened?

What is now irreplaceable?

What is the next move?

Scoring: fail if it tries to continue the old plan without revision.

### Hazard and Spin drill

Give 30 states involving hazard setter, spinner, spinblocker/ghost if applicable, and boss pressure.

Agent chooses: set hazard, add layer, attack, switch, spin, block spin, or ignore hazards.

Policy it must learn:

Hazards are not “free progress.” They are worth a turn only when future switches or chip thresholds justify the tempo loss.

Spin is not “always remove hazards.” Spin only matters when the hazard damage changes survival, Rest timing, sacrifice math, or an endgame threshold.

In vanilla GSC, Spikes and Rapid Spin have specific distribution and one-layer assumptions; in this romhack, the agent must use local evidence instead of importing vanilla hazard math. Smogon’s Spikes article is good for hazard value and team-cost concepts, not for unquestioned romhack mechanics. ([Smogon][3])

### Sleep/status discipline drill

Give states with one sleep move or one key status move.

Agent must answer:

Who is the best target?

Who is the worst target?

What status slot are we spending?

Does this enable a KO, setup, Rest cycle, or switch denial?

Are we wasting status into a target that does not care?

What happens if the move misses?

This drill should punish “click sleep because sleep is good.” Sleep is a route tool, not a vibes button.

### Sacrifice and Explosion route-trade drill

Give states where one Pokémon can be sacrificed or can Explode/Self-Destruct.

Agent must name:

The piece being traded.

The enemy role removed.

The route unlocked.

The route lost.

Whether the trade is mandatory, favorable, neutral, or losing.

Policy:

Do not sacrifice the weakest-looking Pokémon. Sacrifice the least necessary Pokémon after checking future defensive jobs.

Do not Explode for momentum. Explode to remove a named obstacle, stop a named threat, or convert a route.

### Defensive-answer preservation drill

Input: opponent has three remaining threats; our team has limited answers.

Agent must label each teammate:

Irreplaceable.

Replaceable.

Tradeable only for [specific target].

Dead weight.

Wincon.

Scoring: fail if it switches the only answer into avoidable chip before its job is done.

### PP/endgame conversion drill

Give 3v3 and 2v2 endgames with known PP, Rest, status, and hazards.

Agent must produce a route:

How many attacks needed?

Can enemy Rest loop?

Can we force Rest?

Can we stall PP?

When do we attack versus recover?

What crit/miss branch matters?

The output should be a concrete sequence, not “play carefully.”

### Boss AI adaptation drill

Give repeated states against a boss AI pattern. The agent predicts the boss move, then updates after each reveal.

It must keep two beliefs:

Observed AI behavior.

Still-plausible exceptions.

Scoring: fail if it overfits after one turn. A boss choosing one move once is evidence, not law.

### Anti-overprediction drill

Give states where a fancy prediction looks attractive.

Agent must choose between safe progress and hard read.

Policy:

Hard-predict only when the safe line loses or when the predicted line is still acceptable if wrong. Otherwise, take the line that preserves the route.

## 6. Battle Review Protocol

The review method must be hindsight-safe. The goal is not to say “we lost because Thunder missed” or “we won so the line was good.” The goal is to find the earliest meaningful decision error.

Use this process.

First, reconstruct the battle without judging it. Record team, rules, known mechanics, boss data, and initial plan.

Second, replay turn by turn. Before revealing each turn’s outcome, pause and write:

Known state.

Unknown state.

Current win condition.

Irreplaceable pieces.

Legal candidate moves.

Opponent’s plausible branches.

Recommended move.

Confidence.

Only then reveal what happened.

Third, grade the decision, not the result:

Good decision / good result.

Good decision / bad result.

Bad decision / good result.

Bad decision / bad result.

A miss, crit, or bad roll does not automatically make the decision bad. A risky move that worked does not automatically make it good.

Fourth, find the **earliest meaningful mistake**. This is not the first imperfect move. It is the first decision where a reasonable alternative would have materially improved the route, preserved an irreplaceable resource, avoided a forced disaster, or reduced dependence on luck.

Use mistake categories:

Missing state.

Wrong win condition.

Failed preservation.

Bad damage/calc assumption.

Mechanics hallucination.

Bad branch pricing.

Overprediction.

Underprediction.

Bad sacrifice.

Bad Rest/PP timing.

Hazard tempo error.

Boss AI assumption error.

Fifth, produce exactly one reusable lesson and one benchmark.

Reusable lesson format:

“When [trigger], prefer [policy], unless [exception].”

Benchmark format:

“In the next 20 similar states, the agent must identify [resource] before recommending a move.”

Example:

“When our only Electric resist still needs to answer the final boss mon, do not pivot it into neutral chip for tempo unless that tempo immediately wins or prevents a worse loss.”

That is a useful review. “Should have played better around crits” is not.

## 7. Simulation Use

Simulations and calculators are for grounding. They are not a substitute for strategic learning.

They are good for:

Damage ranges.

KO thresholds.

Speed order.

Move accuracy risk.

PP/endgame lines.

Testing local mechanics.

Testing boss AI scripts.

Repeating specific states.

Comparing candidate routes under controlled assumptions.

They cannot prove:

That the agent understands the battle.

That the route is robust to missing information.

That the boss AI model is correct.

That a win rate transfers to real play.

That the cookbook is good.

That an 80%-over-50 result means “mastery.”

A 40/50 result is an observed 80%, but it is still noisy; a rough Wilson 95% interval is about 67% to 89%. More importantly, if the simulator is wrong, the statistic is decorative.

Before boss-sim win rates count, validate:

Pokémon data: stats, levels, DVs/EVs/stat experience if relevant, items, moves, typings.

Damage formula.

Critical hit behavior.

Accuracy and secondary effects.

Speed and priority.

Status, sleep, wake, Rest, Sleep Talk if present.

Hazards, layers, Rapid Spin, and switching behavior.

Fire low-HP passive or any romhack-specific passive.

PP consumption.

Enemy AI move choice.

Enemy switching, if any.

RNG behavior or seed handling.

Faint replacement order.

Battle text/log equivalence against emulator observations.

Smaller gates before the 80%-over-50 target:

Gate 1: 30 representative damage calcs match emulator or trusted local data.

Gate 2: 20 mechanics fixtures pass, including hazards, spin, status, Rest, crit, and passive effects.

Gate 3: 20 boss AI states are predicted correctly or marked uncertain with a documented exception.

Gate 4: 30 live-turn drills produce a legal, state-aware recommendation with no mechanics claims beyond validation.

Gate 5: 10 full simulated boss battles complete with no illegal moves, impossible assumptions, or mid-test route edits.

Gate 6: 25-battle pilot reaches a stable win rate and every loss has an identified earliest meaningful mistake.

Gate 7: only then run 50 preregistered battles for the 80% gate.

## 8. Cookbook Design

The mastery notebook should be a practical cookbook, not an encyclopedia.

Each entry should be 60 to 140 words. Use this structure:

Name.

Trigger.

Default policy.

Exceptions.

Worst plausible branch.

Local mechanics status.

One example.

One review/drill source.

Good entry:

“Explosion trade permission. Trigger: we can remove a wall/check that blocks the named win condition. Default: Boom only if the Exploder no longer has a unique defensive job and the target’s removal immediately unlocks sweep, Rest loop, or safe endgame. Exception: do not Boom into a plausible Ghost/resist/protect-equivalent branch unless the failed trade is still recoverable. Mechanics: romhack Explosion behavior verified? [yes/no].”

Bad entry:

“Explosion is strong and can be used offensively or defensively. Watch out for Ghosts.”

What belongs:

Turn policies.

Mechanics firewall.

Boss-specific route cards.

Reviewed mistake patterns.

Damage/speed threshold cards.

Status/sleep target rules.

Hazard/Spin policies.

Sacrifice permission rules.

PP/endgame conversion rules.

AI adaptation notes.

Calibration metrics.

What should be removed:

Long prose summaries.

Generic advice.

Duplicated recipes.

Vanilla mechanics treated as local truth.

Species-specific lessons that have not been abstracted into roles.

Old routes for outdated bosses.

Sim results from unvalidated mechanics.

Any entry that never changes a live recommendation.

During live advice, the notebook should be used through a small index:

Hazards.

Sleep/status.

Setup.

Sacrifice/Explosion.

Defensive preservation.

Rest/PP/endgame.

Boss AI.

Mechanics firewall.

If the agent has to search through paragraphs, the cookbook has failed.

## 9. Bad Advice Rewrite

| Bad GPT-shaped advice                            | Actionable battle policy                                                                                                                                                                                                               |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| “Set up hazards early; hazards are always good.” | Set hazards when the setter is not needed immediately, the opponent is likely to switch or be forced out, and the chip changes future KO/survival thresholds. Attack or switch instead if the active threat can punish the tempo loss. |
| “Preserve your win condition.”                   | Name the win condition specifically: “We win by [Pokémon/move] after [target] is chipped/removed.” Preserve only the pieces required for that route; trade everything else deliberately.                                               |
| “Switch to your counter.”                        | Switch only if the counter survives the expected hit plus the worst plausible coverage/reveal and still performs its later job. A counter that becomes too chipped to answer the endgame may not be a counter anymore.                 |
| “Use the super-effective move.”                  | Use the move that best advances the route. Super-effective damage is correct only if it secures a KO, forces recovery, prevents setup, or keeps the next turn safe.                                                                    |
| “Go for sleep; sleep gives tempo.”               | Use sleep on the target whose disabled turns unlock progress. Do not spend sleep into a likely sleep absorber, RestTalk user, expendable mon, or target that the route does not care about.                                            |
| “Start setting up here.”                         | Set up only when the opponent cannot 2HKO, phaze, status, Explode, or force a bad Rest cycle, and when the boost changes the endgame. Otherwise, attack or pivot.                                                                      |
| “Sacrifice your weakest Pokémon.”                | Sacrifice the Pokémon with the fewest remaining unique jobs, not the lowest HP. Before sacking, check whether it is still needed for speed control, sleep absorption, defensive coverage, Spin, Explosion, or chip.                    |
| “Explode for momentum.”                          | Explode only when the trade removes a named obstacle, prevents an immediate loss, or opens a named win condition. If the target is replaceable or the Exploder still has a unique job, do not Boom.                                    |
| “Rapid Spin whenever hazards are up.”            | Spin when hazard damage changes survival, Rest timing, sack math, or endgame thresholds. If spinning loses tempo and hazards do not change the route, make progress instead.                                                           |
| “Rest when you’re low.”                          | Rest when the sleeping turns are survivable and the healed Pokémon still has a necessary job. Do not Rest if it gives free setup, lets the boss switch to the real threat, or strands you asleep without Sleep Talk/support.           |
| “Predict the switch.”                            | Hard-predict only if the safe move loses the route or if the prediction is still acceptable when wrong. Otherwise, take the move that covers both attack and switch.                                                                   |
| “Play safe.”                                     | Define safe as “the line whose worst plausible branch remains recoverable.” Sometimes the safest move is an attack, a sacrifice, or Explosion.                                                                                         |
| “Keep your anchor healthy.”                      | Preserve the anchor while it still answers unrevealed or remaining threats. Once those threats are gone or covered by another route, convert the anchor into progress.                                                                 |
| “Status the wall.”                               | Use status when it changes the wall’s function: denies repeated switching, forces Rest, enables setup, or creates KO thresholds. Do not spend a status slot just because the target is bulky.                                          |
| “Use the strongest move and hope.”               | Choose the move with the best route value. Damage matters, but so do accuracy, PP, recoil, contact effects, enemy recovery, future switch-ins, and whether a miss loses immediately.                                                   |

## 10. Final Goal Prompt

Here is the exact long-running goal prompt I would give the agent from scratch:

You are training to become a genuinely competent Pokémon singles battle advisor for a GSC-based Pokémon Gold romhack / Gym Leader Lab setting. Your target is practical, state-aware move advice at roughly solid 1500-ELO quality, not impressive notes or generic strategy prose.

Your highest priority is improving real move choice. Every study session, drill, note, simulation, and route map must answer: “Would this help me choose the correct move in a real battle state?”

Study expert Pokémon play first. Use Smogon G/S resources, GSC OU articles, Pokémon analyses, tournament replays, battle logs, and high-quality old-gen discussion as your main training corpus. Start with GSC concepts: Spikes, Rapid Spin, sleep/status, Rest cycles, Explosion trades, phazing, speed tiers, defensive-answer preservation, PP, and endgames. Use ADV/DPP/later-generation material only to extract abstract decision policies such as preservation, forced progress, pivoting, hazard thresholding, setup discipline, sacrifice math, and endgame conversion. Do not import later-generation mechanics into the romhack.

This romhack is GSC-based but not vanilla GSC. Maintain a mechanics firewall. Every mechanics claim must be labeled: romhack verified, vanilla GSC reference, contradicted by local evidence, or unknown. Never present an unverified vanilla mechanic as romhack fact. Local mechanics tests are valuable only when they prevent wrong advice.

When the user asks “What do I do now?”, give a concise, decisive live-turn answer. Use this structure:

Recommended move and confidence.

One-sentence reason tied to the current win condition.

State read.

Primary and backup win condition.

Irreplaceable pieces.

Ranked candidate moves.

Worst plausible branch for the recommended move.

Do-not-click warning if relevant.

Next-turn contingency.

Only the missing facts that could change the move.

Always choose a move when enough information exists. If state is missing, ask for the minimum necessary information, usually a battle screenshot, party HP/moves, enemy HP/status, hazards, boosts, and revealed moves. Do not become useless by saying “it depends.” Say what it depends on and what to do under each branch.

Your recommendations must identify irreplaceable resources before spending them. Track unique defensive answers, speed control, sleep absorbers, hazard control, Explosion users, setup sweepers, wallbreakers, PP/endgame pieces, and boss-specific checks. A low-HP Pokémon may still be irreplaceable. A healthy Pokémon may be expendable.

Review battles with hindsight safety. Pause before each meaningful turn, reconstruct known information, rank candidate moves, then reveal the outcome. Separate decision quality from outcome quality. Find the earliest meaningful mistake: the first decision where a reasonable alternative materially improved the route. Each review must produce one reusable policy and one measurable benchmark.

Run drills every cycle: turn-1 planning, 30+ turn route tracking, plan revision after misses/crits/wakes/reveals/switches/unexpected damage, hazard and Spin timing, sleep/status discipline, sacrifice and Explosion trade math, defensive-answer preservation, PP/endgame conversion, and boss AI adaptation.

Use simulations and calculators for grounding, not as replacements for judgment. Validate damage, speed, status, hazards, passive effects, PP, AI, and local mechanics against emulator or trusted local evidence before counting boss-sim win rates. Do not attempt an 80%-over-50 validation gate until smaller proof gates pass.

Maintain the mastery notebook as a live cookbook. Keep entries short: trigger, policy, exceptions, worst plausible branch, mechanic status, and one example. Remove essays, generic advice, duplicate recipes, unverified mechanics, and species-specific claims that have not been abstracted into roles. The notebook should make live advice faster and sharper.

Measure improvement. Track mechanics errors, live-turn drill scores, top-move agreement in reviewed replays, earliest meaningful mistake turn, branch-prediction accuracy, state-completeness errors, and boss-battle results under preregistered conditions.

Your style should be direct and useful. Do not motivate. Do not pad. Do not say “hazards are good,” “preserve your wincon,” or “play safe” unless you define exactly what that means in the current state. The user wants the move that gives the best path to winning this battle. Your job is to provide that move, the reason, the branch risk, and the next-turn plan.

[1]: https://www.smogon.com/resources/competitive/gs "https://www.smogon.com/resources/competitive/gs"
[2]: https://www.smogon.com/smog/issue28/gsc "https://www.smogon.com/smog/issue28/gsc"
[3]: https://www.smogon.com/gs/articles/gsc_spikes "https://www.smogon.com/gs/articles/gsc_spikes"
[4]: https://www.smogon.com/gs/articles/status "https://www.smogon.com/gs/articles/status"
[5]: https://www.smogon.com/gs/articles/guide_to_explosion "https://www.smogon.com/gs/articles/guide_to_explosion"
[6]: https://www.smogon.com/forums/threads/your-one-stop-shop-for-gsc-ou-statistics.3780415/ "https://www.smogon.com/forums/threads/your-one-stop-shop-for-gsc-ou-statistics.3780415/"
[7]: https://calc.pokemonshowdown.com/ "https://calc.pokemonshowdown.com/"
