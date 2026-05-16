# Replay Turn-Pause Protocol - 2026-05-14

Purpose: use unseen high-level GSC tournament replays as frequent, measurable
practice for live move choice.

This is now the default Pokemon study loop when no romhack mechanics fixture or
real boss capture is waiting.

## Why This Counts

Smogon tournament replays are not perfect answer keys: strong players can
misplay, choose lower-variance lines for tournament reasons, or know private
team details that are absent from a public replay log. They are still valuable
because they force repeated decisions from real long-form battle states, and
their actual choices provide a strong comparison point.

Treat the replay move as a pro-comparison oracle, not absolute truth.

## Required Workflow

1. Find a GSC tournament replay that is not already reviewed or tested locally.
   Prefer material that reflects current legality when measuring current GSC
   advice. If a historical replay uses a now-banned route, quarantine it as a
   mechanics drill and do not count it toward the fresh progress sample.
2. Download the raw `.log`; do not watch the replay UI.
3. Reveal the log only up to the next decision turn. Prefer the local helper:
   `python tools\pokemon_mastery\replay_turn_pause.py path\to\replay.log prompt --turn N`.
   The helper carries common decision-relevant volatiles such as Substitute and
   confusion, plus Baton Pass boosts and tracked volatiles. It is not a full
   battle engine; manually carry unsupported state such as trapping, Encore,
   Nightmare, Perish count, Leech Seed details, or protection.
4. For each side, freeze an answer before revealing that turn:
   - recommended move or switch;
   - confidence;
   - route reason;
   - route transaction before ranked candidates:
     `their package -> our absorber/converter -> their next owner -> our punish`;
   - critical state ledger before ranked candidates: sleep/wake counter, passed
     boosts/speed, self-KO or cash-out branch, and immediate lethal/miss/crit
     risk;
   - candidate comparison before final top action:
     active target value, next-owner value, and counter-owner-after-handoff
     value;
   - public role/package update when a revealed move, voluntary entry, or
     repeated switch changes a Pokemon's job;
   - ranked top three candidates when the board is nontrivial;
   - serious alternatives;
   - rejected tempting safe/default line;
   - worst plausible branch;
   - information that would change the answer.
5. Reveal the actual turn.
   Use `python tools\pokemon_mastery\replay_turn_pause.py path\to\replay.log reveal --turn N`.
6. Score top-move agreement, acceptable-move agreement, reasoning quality,
   route tracking, hidden-information discipline, and severe blunders.
7. Continue until the replay stops producing useful decisions or fatigue makes
   answers sloppy.
8. Keep one-off misses in `workspace/quick_tests/` or `reviews/`. Promote a
   new live heuristic, policy card, or canon lookup only after the same miss
   class repeats across at least two fresh unseen decisions, or after a
   verified mechanics fact directly changes legal advice.

## Information Model

Use one of these modes and record it in the artifact.

| Mode | What I Know | Counts For |
| --- | --- | --- |
| Spectator public | Only public replay state so far. | Practice and calibration, not strict player-side scoring. |
| Side-known reconstructed | Public state plus that side's known team/moves, reconstructed from a source or provided team sheet. | Better player-advice practice when the reconstruction is credible. |
| Boss-side romhack | Boss own team and public player reveals only. | Boss AI policy review. |

Do not mix these modes inside a score without saying so.

Replay-log side-known is partial side-known: unused own moves and hidden move
types may be missing. Label any recommendation that depends on an unlisted own
move as an own-move reconstruction gap; prefer full team sheets when exact move
choice depends on private own moves.
If the frozen top move is conditional on an unlisted own move, record the
fallback before reveal and score the turn separately or unscored as an
own-move gap when the legal move list was decision-critical.

Before counting a side-known packet toward structural proof, inspect the
helper's turn-1 own-side reconstruction. Prefer sides with six own Pokemon and
at least two or three eventual moves on the pieces likely to make early
decisions. If the reconstruction has fewer than six own Pokemon, one-move core
pieces, or missing recovery, self-KO, or coverage on central jobs, label the
packet `partial_side_known_sparse`. Sparse packets can be practice and method
evidence, but exact top-match is not clean proof.

When exact move choice depends on the advised player's own unrevealed moves or
team slots, prefer one-side side-known packets over two-sided spectator-public
exact scoring. The helper supports this:

```text
python tools\pokemon_mastery\replay_turn_pause.py path\to\replay.log side-prompt --turn N --side p1
```

Use one advised side per replay or isolate runs. If one prompt reveals p1's
side-known roster, the same session is contaminated for p2 advice because p1 is
p2's opponent.

Showdown logs do not print Hidden Power type in the move name. If the helper
only shows `Hidden Power`, label type-dependent exact misses as side-known
helper gaps unless the type has already become public from damage or
effectiveness.

## Scoring

Before scoring, classify decision-relevant set information:

- `revealed`: public from the log so far.
- `strong prior`: common set or board clue, but not public fact.
- `possible only`: legal or plausible but not enough to anchor the main line.

An answer may price strong priors, but it must say what happens if the prior is
wrong. A possible-only move, item, or role cannot be the main reason for the
recommendation unless the answer explicitly marks the line as a read.

For each decision:

- `top_match`: exact same move/switch as the player, when the actual move is
  legal and meaningful.
- `acceptable_match`: different move but same defensible route or clear
  conditional match.
- `route_error`: wrong plan, wrong resource, or stale plan continuation.
- `state_error`: missed HP/status/hazards/revealed move/speed/order detail.
- `hidden_info_error`: assumes unrevealed team/moves/items/roles as fact or
  lets an unrevealed fact determine the main recommendation without labeling it
  as a read and naming the fallback.
- `mechanics_error`: wrong GSC or local-romhack mechanic.
- `severe_blunder`: line immediately loses a central route or irreplaceable
  piece without compensation.
- `positive_selection`: answer chooses a move that actively improves the route,
  punishes the named branch, preserves or spends the correct route piece, or
  converts pressure into progress. Mark 0 when the answer is merely safe,
  generic, passive, or acceptable only because it does not throw.
- `route_converting_move_chosen`: answer identifies and chooses the move that
  improves board equity when a converter exists.
- `branch_punish_chosen`: answer names the likely branch and chooses the move,
  switch, phaze, setup, coverage, or utility action that beats that branch.
- `role_package_update_obeyed`: after a public reveal or role-signaling entry,
  answer classifies the package before ranking moves. Use classes such as
  `pressure`, `absorber`, `reset`, `trap`, `phaze`, `handoff`, `lure`,
  `cleric`, or `spinner`.
- `route_transaction_obeyed`: on nontrivial turns, answer gives the package,
  absorber/converter, next owner, and punish before ranked candidates.
- `critical_state_ledger_obeyed`: on nontrivial turns, answer states
  sleep/wake counter, passed boosts/speed, self-KO or cash-out branch, and
  immediate lethal/miss/crit risk before ranked candidates.
- `actual_in_top_three`: actual move/switch appeared in the frozen ranked
  candidates. This separates candidate generation from top-rank calibration.
- `actual_branch_named`: the receiver, absorber, cash-out, setup, or reset
  branch that happened was named before reveal.
- `top_rank_failure`: post-score reason the top candidate lost when the actual
  was known or acceptable: `branch_probability`, `route_budget`,
  `oracle_style`, `own_move_gap`, `state`, `mechanics`, `hidden_info`, or
  `missing_candidate`.
- `oracle_quality`: post-score label for the actual move as an oracle:
  `clean`, `route_equivalent`, `style_or_variance`, `own_move_gap`, or
  `unscored`. This does not erase top-match misses; it decides whether to
  patch policy, mark a side-known helper gap, or avoid overfitting to style.
- `retrieval_failure`: the miss is already covered by a loaded live card, but
  the answer failed to apply it. Track this separately from missing-policy
  errors so the docs do not grow for every application miss.

When exact top-match depends on private moves or teammates absent from the
spectator-public prompt, still score it, but label the postmortem as a
side-known oracle gap rather than silently treating it as a public-route error.

Tags are non-exclusive. A line can be both `hidden_info_error` and
`severe_blunder`; count both rather than choosing the softer label.

Replay-probe score should be reported separately from quick-test and final-exam
scores.

## Exclusions

Skip or mark unscored:

- forced switches after a faint;
- no-action sleep/freeze/paralysis turns where the chosen move is not logged;
- turns where the prompt cannot include the advised side's legal choices;
- end turns after the outcome is already forced;
- turns where a timer or disconnect clearly changes incentives.

## Artifact Template

Save each run under `docs/pokemon_mastery/reviews/` or
`docs/pokemon_mastery/workspace/quick_tests/`:

```text
# Replay Turn-Pause Run - YYYY-MM-DD - replay-id

Source:
Mode:
Contamination control:

## Score Summary

Decisions:
Top-match:
Acceptable-match:
Severe blunders:
State errors:
Hidden-info errors:
Mechanics errors:
Positive-selection:
Route-converting move chosen:
Branch-punish chosen:
Role-package update obeyed:
Oracle-quality notes:
Earliest meaningful error:

## Turn N

Public state:
My p1 answer:
My p2 answer:
Actual choices:
Grade:
Positive-selection tags:
Reusable lesson:
```

## Plateau Loop

After a structural repair, gather a sizable fresh replay sample before claiming
progress. Default sample: three fresh packets or at least 90 scored side
decisions, whichever comes first, unless a repeated severe/hidden/state/
mechanics error forces an earlier stop.

If the sample regresses or is blatantly flat versus the recent baseline, stop
replay grinding and run a training-method review. Consider whether the blocker
is replay review itself, prompt shape, scoring oracle, tiny-card structure, GSC
theory, mechanics fixtures, retrieval burden, or model attention. Then update
the training structure and restart the sample loop.

## When To Stop And Study

Stop the replay and study instead when the same error class appears twice:

- repeatedly missing preservation switches;
- repeatedly stacking hazards without retention;
- repeatedly treating unknown teams as previewed;
- repeatedly choosing damage over route progress;
- repeatedly missing Rest, Sleep Talk, Explosion, phazing, or PP implications.
- repeatedly missing role/package updates after public reveals.
