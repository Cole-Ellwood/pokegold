# Pokemon Mastery Measurement Mini-Goal - 2026-05

Status: active measurement overlay. This does not replace or resume the paused
long-running Pokemon mastery goal.

## Objective

Build a repeatable measurement loop that can answer:

```text
Are Pokemon battle recommendations getting measurably better over time, or are
we just creating more notes?
```

The mini-goal succeeds when progress is tracked through dated tests, trend
summaries, and occasional sealed exams. It fails if improvement is supported
only by notebook volume, known-practice examples, or unreviewed win rates.

## Source Basis

Local basis:

- `active_goal.md` already defines the desired evidence: move quality,
  mechanics errors, state-completeness errors, live-turn drill scores,
  branch-prediction accuracy, severe blunder rate, and later boss-battle
  results.
- `boss_sim_validation_protocol.md` defines the later 50-battle / 80% proof
  target.
- `boss_sim_readiness_audit_2026-05-13.md` says that target is not countable
  yet because no declared team/ruleset, trusted non-self sim run, or filled
  real boss-attempt review exists.
- `audit/boss_ai_preference/state_transition_benchmarks.md` and
  `audit/boss_ai_preference/final_report.md` provide useful proxy metrics, but
  not a sealed final exam.

External basis:

- Pokemon Showdown is usable as a simulator/library and has command-line tools,
  but it is vanilla mechanics unless customized, so it cannot validate this
  romhack by default.
- `poke-env` provides Python battle-agent interfaces and baseline players on
  top of Pokemon Showdown, useful for vanilla GSC or transfer tests, with the
  caveat that its docs say it was primarily developed for later generations.
- Recent Pokemon battle-agent papers use win rate, Elo, held-out battle
  benchmarks, and partial-observability stress tests. Those are useful models,
  but this project still needs local romhack-specific mechanics validation.

References:

- https://github.com/smogon/pokemon-showdown
- https://poke-env.readthedocs.io/en/stable/
- https://arxiv.org/abs/2402.01118
- https://arxiv.org/abs/2503.04094
- https://arxiv.org/abs/2603.15563

## Measurement Pools

Keep these separate. Do not collapse them into one score until each is stable.

| Pool | Purpose | Can Be Studied? | Counts For Trend? |
| --- | --- | --- | --- |
| Public practice | Learning, drills, known mistakes | Yes | No |
| Regression | Prevent old catastrophic errors from returning | Partly | Yes, separately |
| Quick probe | Frequent semi-blind trend checks | No before answering | Yes |
| Replay turn-pause | Repeated decisions from unseen high-level GSC games | No before answering | Yes, separately |
| Cross-domain transfer | Check whether an outside idea improves a Pokemon failure class | Yes before transfer; no before scored Pokemon check | Only if followed by a Pokemon artifact and score |
| Private final exam | Rare sealed milestone | No | Yes |
| Generated holdout | Fresh positions made near exam time | No | Yes |
| Simulation/emulator run | Outcome and adaptation check | No before run | Only after readiness gates |

If I create the questions myself, the result is at best semi-blind. A true
final exam needs prompts, seeds, teams, and answer keys kept outside my visible
study materials until after scoring.

## Quick Test Cadence

Run after every substantial study block, or every 1-3 days during active work.

Default quick test:

```text
10 scenarios total
3 vanilla GSC decisions
3 romhack boss decisions
2 mechanics/edge-case decisions
1 long-route or multi-turn branch decision
1 adversarial contamination check
```

Rules:

- Freeze the public prompt before answering.
- Answer without opening notes, source, calculators, or prior expected policy
  unless the test explicitly permits that aid.
- Prefer anonymized public prompts: no source IDs, tags, lesson labels, or
  category names that reveal the intended heuristic. Candidate actions should
  be real move classes or moves, not policy labels.
- Record the answer before checking any oracle.
- Score the answer in `measurement_progress_ledger.csv`.
- Do not add exact failed hidden-exam answers to the cookbook. Add only the
  aggregate error class and next study target.

## Replay Turn-Pause Cadence

Run after substantial study blocks or whenever the next useful action would
otherwise be generic note-taking.

Rules:

- Use `replay_turn_pause_protocol.md`.
- Prefer Smogon tournament GSC replays not already present in `reviews/`,
  `worked_examples/`, or `workspace/quick_tests/`.
- Freeze predictions for both players before revealing the turn.
- Score the replay separately from quick probes because actual player choices
  are a strong comparison point, not a perfect oracle.
- Do not count turns where the log cannot recover the intended move, such as
  no-action sleep turns.
- If the prompt omits a side's known private team/moves, mark the run as
  spectator-public and do not compare it directly to player-side tests.

## Cross-Domain Transfer Cadence

Run a small transfer sprint when a repeated error class appears or when two
Pokemon-only blocks produce no new measured error or score.

Rules:

- Use `cross_domain_autonomy_policy.md`.
- Start from a concrete Pokemon miss, not curiosity alone.
- Study one outside source or tool enough to extract one decision rule.
- Translate the rule into a Pokemon prompt, drill, source-to-policy entry,
  fixture, helper, or boss-AI audit.
- Count it for trend only after a later replay, quick probe, fixture, or audit
  tests the targeted failure class.

## Final Exam Cadence

Run every 4 weeks of active study, before any claim of major improvement, or
after a major mechanics/tooling change.

Default final exam:

```text
100 scenarios
40 vanilla GSC
40 local romhack
20 unfamiliar/generated transfer states
at least 5 multi-turn sequences
at least 1 simulation or emulator-backed batch if readiness gates allow it
```

Final exam outputs:

- total score and score by pool;
- mechanics errors by category;
- severe blunder rate;
- hidden-information or illegal-action errors;
- top-move and acceptable-move agreement;
- earliest meaningful error in multi-turn sequences;
- comparison to the previous final exam and the 3-run quick-test average.

Do not count a final exam if the answer key, exact scenarios, teams, or seeds
were visible during the preceding study period.

## Scoring Rubric

Each scenario gets five 0-4 scores:

| Dimension | Weight | Meaning |
| --- | ---: | --- |
| Action quality | 35 | Chooses the best move/switch/setup/recovery/sack, or a high-EV acceptable line |
| Mechanics accuracy | 20 | Uses correct vanilla or romhack mechanics for the declared profile |
| Reasoning quality | 20 | Names the route, alternatives, and why the top line wins |
| Risk management | 15 | Prices misses, crits, ranges, speed, status, opponent branches, and variance |
| Calibration | 10 | Marks uncertainty honestly and avoids hidden-information certainty |

Formula:

```text
weighted_score =
  (action_quality * 35
 + mechanics_accuracy * 20
 + reasoning_quality * 20
 + risk_management * 15
 + calibration * 10) / 4
```

Caps:

- illegal move or impossible switch: max 40;
- hidden-information abuse: max 50;
- severe blunder that loses a required route: max 60;
- romhack-facing answer with decision-relevant unverified mechanic: max 70;
- no single recommended move or ranked move class: max 75.

Error tags are non-exclusive. If one answer both assumes an unrevealed fact and
loses a central route, count both `hidden_info_error` and `severe_blunder` and
apply the most restrictive cap. Do not relabel a severe error as hidden-info to
make severe-blunder rate look better.

Hidden-information tiering:

- `revealed`: public move, item, status, role, or teammate evidence. It can be
  used as fact.
- `strong prior`: common set, voluntary-entry clue, or source-backed tendency.
  It can affect risk pricing, but the answer must state the fallback if wrong.
- `possible only`: legal or plausible but not public. It can be listed as a
  branch, not used as the main reason for the move unless the line is explicitly
  marked as a high-risk read and slow play loses.

## Trend Rules

Track:

- 3-run moving average for quick tests;
- final-exam score by date;
- vanilla vs. romhack split;
- known/regression vs. hidden split;
- severe blunder rate;
- mechanics error rate;
- hidden-information error rate;
- replay turn-pause top-match and acceptable-match rates;
- positive-selection rate in fresh replay or focused-transfer artifacts;
- role-package update obedience after public reveals;
- transfer-sprint target error rate before and after the Pokemon check;
- simulation/emulator win rate only after readiness gates pass.

Call progress real only when:

- the 3-run quick-test average improves by at least 5 points, or severe blunder
  rate falls materially;
- hidden or generated-holdout scores do not lag public/regression scores by
  more than 15 points;
- mechanics errors are flat or declining;
- hidden-information, mechanics, and state errors are not merely replacing
  severe blunders. If severe blunders drop but total tracked errors rise, report
  only "catastrophic error control improved," not broad error improvement;
- severe blunders stay low and positive-selection rate rises. Do not call a
  block progress if it only avoids obvious mistakes while choosing safe,
  generic, or non-converting moves;
- the same catastrophic error class does not recur in two consecutive scored
  runs;
- improvement appears in both vanilla and romhack pools, or the reported claim
  is explicitly limited to one pool.

Occasional drops are acceptable. A one-run gain is not a trend.

Structural-repair sample gate:

- After changing the live decision system, collect three fresh replay packets
  or at least 90 scored side decisions before claiming the repair worked.
- Compare against the recent fresh-replay baseline on top-match,
  acceptable-match, positive-selection, route conversion, branch-punish, and
  role-package obedience, with severe/hidden/state/mechanics errors still low.
- If the sample is regressing or blatantly flat, pause replay review and run a
  training-method review. Reconsider prompt format, replay review as the main
  practice mode, scoring oracle quality, card structure, GSC theory gaps,
  mechanics fixtures, and retrieval/attention limits before collecting more
  replay volume.

## Simulation Ladder

Do not jump straight to the 50-battle gate.

| Stage | Name | Countable? | Requirement |
| --- | --- | --- | --- |
| 0 | Scenario benchmark | Yes | Quick/final exams with frozen prompts |
| 1 | Single-turn sim/check | Yes, narrow | Damage, speed, status, or branch oracle is trusted |
| 2 | Uncounted boss shakedown | No | Real or emulated attempts reviewed for mismatches |
| 3 | Mini sim exam | Partly | 10-15 declared battles, every loss/lucky win reviewed |
| 4 | Final boss sim gate | Yes | 40+ wins / 50, declared team/ruleset, no deciding mismatch |

Opponent options by stage:

- romhack in-game boss AI through emulator traces or recorded attempts;
- random legal baseline for sanity only;
- simple heuristic baseline that prefers KO, avoids dead moves, and switches out
  of catastrophic public matchups;
- Pokemon Showdown / `poke-env` baselines for vanilla or transfer tests only;
- frozen older advisor or external model if available;
- human-authored trap scenarios for known failure modes.

Never use self-play as the main final metric. It can improve against its own
quirks without improving real advice.

## Contamination Controls

Safeguards:

- Store private exam prompts and answer keys outside normal visible study docs
  when possible.
- Use neutral scenario IDs, not filenames that reveal the answer.
- Rotate surface forms: HP bands, wording, lead identity, revealed move order,
  and alternate but equivalent board states.
- Include canary scenarios that should fail if hidden facts leaked.
- Report public/regression and hidden/generated scores separately.
- Use paired evaluations when comparing old and new policies: same seeds,
  teams, and opponent policy.
- Sample and review wins, not just losses, so lucky bad play does not count as
  progress.

Red flags:

- quick scores rise while hidden exam scores stay flat;
- performance depends on prompt wording;
- score improves only against one weak opponent policy;
- simulated win rate rises while human/engine review finds no better decisions;
- the assistant assumes hidden moves/items/team slots before public reveal;
- romhack scores fall while aggregate score rises.

## Current Baseline

This is the starting measurement state, not proof of mastery:

- state-transition benchmark proxy: 43 / 43 evaluated positions passed;
- preference final readiness: not ready for ROM scoring review;
- pairwise holdout proxy: 83.3%;
- trajectory holdout proxy: 100.0%;
- no filled real boss-attempt review yet;
- no countable non-self 50-battle run yet;
- boss-sim readiness audit still says aggregate win rate is not countable.

## Next Concrete Actions

1. Record this baseline in `measurement_progress_ledger.csv`.
2. Run Quick Test 001 with 10 fresh or semi-blind scenarios.
3. Fill one real boss-attempt worksheet, preferably Pryce because the capture
   and scoring protocol already exists.
4. Add one generated-holdout mechanism only after the first manual quick tests
   reveal which scenario fields matter.
5. Do not run the 50-battle gate until the readiness audit blockers are closed.
