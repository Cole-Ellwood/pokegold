# Active Pokemon Mastery Goal

Status: active. The goal tool now uses the compact-context system from
`active_context.md` as the startup spine.

## Goal

Become a measurably stronger Pokemon singles advisor, using solid 1500-Elo play
as a training proxy rather than proof. The practical target is better unseen
move choice: plan multiple turns ahead, re-solve after new public information,
and choose moves that preserve or improve realistic win routes in GSC-style
singles and practical romhack boss turns.

## Operating Rules

- Start from `active_context.md` and only the 1-3 policy cards or local docs
  needed for the selected bottleneck. Do not load broad archives by default.
- Use current web search when selecting fresh Smogon/GSC material, checking
  current competitive sources, verifying current ladder/rating claims, or
  investigating a repeated error not explained locally.
- Use full autonomy when it improves decisions: search outside Pokemon, study
  adjacent games or AI methods, build helper programs, download materials, and
  run experiments. Use `cross_domain_autonomy_policy.md` to keep tangents tied
  to Pokemon skill instead of note volume.
- Do not default to tooling. Ask periodically whether a small helper would
  remove an annoying, repetitive, or contamination-prone part of the core study
  loop; build it only when it creates more or cleaner reps, checks, scores, or
  no-cheat AI audits.
- Spend most work time studying expert play and reviewing games, not building
  tooling.
- Make unseen GSC tournament replays the default measurement reps: reveal one
  turn at a time, freeze a prediction for each side, reveal the actual pro
  choices, then score agreement and error classes. Use
  `replay_turn_pause_protocol.md` for the exact rules.
- Optimize for live move choice. The central skill is decision compression:
  turning a messy board into one ranked recommendation, with the next-turn
  consequence and worst plausible branch named clearly.
- Treat severe-blunder avoidance as a gate, not the main training objective.
  The next phase must improve positive move selection: choosing moves that
  convert route pressure, punish named branches, or spend/preserve the correct
  route piece instead of merely choosing a safe or defensible line.
- Before serious recommendations, separate decision-relevant set facts into
  `revealed`, `strong prior`, and `possible only`. Revealed facts can anchor the
  line. Strong priors can affect risk pricing only if the recommendation says
  what happens when the prior is wrong. Possible-only facts are branches, not
  reasons to choose the main move unless slow play loses and the answer is
  explicitly marked as a read.
- Use local preference cards only as light calibration. Do not let them become
  the curriculum.
- Use GSC as the home format because the romhack is GSC-based, but study ADV,
  DPP, and other generations for transferable strategic concepts.
- Study non-Pokemon imperfect-information domains when they match a repeated
  failure mode. Poker AI, POMDPs, search/planning, chess/endgame conversion,
  RTS/fighting-game yomi, and sports analytics are valid sources when they
  produce a Pokemon drill, policy entry, fixture, helper, or measured score.
- Study Snorlax-heavy GSC material as a high-value proxy for general concepts:
  anchor preservation, Rest cycles, setup denial, Explosion trades, and route
  conversion. Do not assume Snorlax itself is central to Gym Leader Lab boss
  fights unless the local roster actually includes it.
- Abstract cross-generation concepts before transferring them. Mechanics such
  as Mega Evolution, Z-Moves, Dynamax, Terastallization, Team Preview, and
  modern item/ability ecosystems are not directly transferable without
  translation.
- Treat the Pokemon Gold romhack / Gym Leader Lab as a mechanics fork. Verify
  local mechanics with docs, source, fixtures, debugger output, or emulator
  traces before making romhack-specific claims.
- Use simulations, calculators, and local scripts as grounding. They test
  whether a learned idea survives branches and long-term consequences; they are
  not the curriculum by themselves.
- Keep the notebook as a cookbook for real turn advice. Prefer reusable
  decision recipes over broad strategy prose.
- Default to preserving existing notes. Rewrite only when a study block exposes
  a clearer recipe, a duplicate, a misleading claim, or a missing distinction
  between general, GSC, and romhack-specific play.
- Every useful source lesson should land as one of these artifacts: a
  source-to-policy ledger entry, a paused-turn decision point, a live-turn drill,
  a boss route card, a mechanics fixture, or a concise cookbook recipe.
- Reduce or quarantine work that does not improve move choice: broad notebook
  essays, speculative framework building, route-map polish before use, and
  tooling that is not tied to a real advice failure.

## Serious-Turn Checklist

Before advising a serious move, answer:

1. What is the exact public state?
2. Which decision-relevant moves, items, roles, and teammates are revealed,
   strong priors, or possible only?
3. Does my intended line require an unrevealed fact to be true? If yes, is it a
   justified read, and what happens if it is wrong?
4. What was the original game plan, and is it still live?
5. What are our current winning routes?
6. What are the opponent's current winning routes?
7. Which pieces are irreplaceable, and which are expendable?
8. What is the opponent's best immediate punish?
9. What is the worst plausible branch?
10. What happens if we attack, switch, set hazards, use status, set up, recover,
   phaze, scout, or sacrifice?
11. What resource does the move gain, and what does it spend?
12. Does the move improve a concrete route, or only feel active?
13. What is the likely next turn if this works?
14. What information would make us abandon the plan?

## Study Cadence

For each work block:

1. Study expert sources or full battle logs first.
2. For unseen replays, pause before each decision turn and freeze predictions
   before revealing the actual moves.
3. Extract practical decision lessons into the source-to-policy ledger.
4. Convert some lessons into paused-turn or live-turn drills that force a move.
5. Update the cookbook only when the lesson is useful and clear.
6. Test selected lessons with review, constructed positions, calculators, or
   simulations when that would improve future move choice.
7. If the last two blocks produced no new measured error or score, take one
   high-variance transfer tangent before doing another broad note pass.
8. Record what improved, what remains uncertain, and what should be studied
   next.

## Current Training Focus

The current phase is not about proving mastery by adding pages. It is about
building the reflexes needed for real boss advice:

- Read expert play, then compress each lesson into a trigger, default move
  class, exception, worst branch, and local-mechanics status.
- Build paused-turn atlases from replays and constructed boss states. Each
  paused turn must require a ranked move, not just commentary.
- Run turn-pause replay reps on unseen Smogon GSC tournament logs. Do not
  count the replay move as absolute truth, but do treat disagreement with a
  strong player's actual choice as evidence to investigate.
- Use cross-domain autonomy on repeated failure classes. For example, study
  poker AI when hidden-information discipline, bluff/call structure, mixed
  strategy, exploitability, or subgame re-solving is the blocker.
- Practice the live-turn answer shape until recommendations are concise:
  move, confidence, route reason, state read, candidate ranking, next turn, and
  missing information.
- Prefer concrete boss route cards over generic metagame summaries when local
  roster data is available.
- Use simulations and calculators to check breakpoints, mechanics, and branch
  claims after the strategic question is clear.

## Measurement

Track progress with move-quality evidence, not notebook volume:

- mechanics errors;
- state-completeness errors;
- hidden-information errors, counted separately and also counted alongside
  severe blunders when the same recommendation both assumes hidden facts and
  loses a route;
- live-turn drill scores;
- top-move or acceptable-move agreement in reviewed expert turns;
- turn-pause replay scores from unseen Smogon GSC tournament games;
- positive-selection rate in fresh replay artifacts: whether the chosen move
  actively improves the route, punishes the named branch, preserves or spends
  the correct route piece, or converts pressure into progress;
- transfer-study artifacts that become Pokemon drills, policy entries,
  fixtures, helpers, or scored probes;
- earliest meaningful mistake found in long reviews;
- branch-prediction accuracy;
- severe blunder rate on regression scenarios;
- boss-battle results under preregistered simulator conditions once the
  simulator is trusted.

## Proof Of Progress

The real proof is better play advice:

- coherent turn-1 plans;
- accurate plan revision after new information;
- strong win-condition tracking;
- fewer severe blunders;
- fewer total tracked errors, or a clearly labeled narrower claim such as
  "catastrophic errors improved but hidden-info errors did not";
- higher positive-selection rate, with severe blunders kept low;
- preservation of irreplaceable pieces;
- better hazard, status, Rest, PP, sacrifice, setup, phazing, and endgame
  planning;
- clear distinction between good decisions and lucky outcomes;
- romhack-specific mechanics handled separately from generic Pokemon intuition.

A later-stage validation target is to run real simulated boss battles against
the romhack AI or another non-self opponent model. A useful gate is at least an
80% win rate across 50+ battles for a declared player team and ruleset, with
losses reviewed for decision error, unavoidable variance, or simulator mismatch.
This is validation, not the curriculum, and it only counts after the simulator
is trusted for the mechanics being tested.

Do not mark this goal complete until unseen long-form battles and practical
boss-battle turn advice demonstrate those abilities. Passing tests or having a
large notebook is not enough.
