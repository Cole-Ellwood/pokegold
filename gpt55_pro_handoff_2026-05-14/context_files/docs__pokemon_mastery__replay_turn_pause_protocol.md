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
2. Download the raw `.log`; do not watch the replay UI.
3. Reveal the log only up to the next decision turn. Prefer the local helper:
   `python tools\pokemon_mastery\replay_turn_pause.py path\to\replay.log prompt --turn N`.
4. For each side, freeze an answer before revealing that turn:
   - recommended move or switch;
   - confidence;
   - route reason;
   - serious alternatives;
   - worst plausible branch;
   - information that would change the answer.
5. Reveal the actual turn.
   Use `python tools\pokemon_mastery\replay_turn_pause.py path\to\replay.log reveal --turn N`.
6. Score top-move agreement, acceptable-move agreement, reasoning quality,
   route tracking, hidden-information discipline, and severe blunders.
7. Continue until the replay stops producing useful decisions or fatigue makes
   answers sloppy.
8. Extract only reusable lessons into the cookbook, source-to-policy ledger, or
   paused-turn atlas.

## Information Model

Use one of these modes and record it in the artifact.

| Mode | What I Know | Counts For |
| --- | --- | --- |
| Spectator public | Only public replay state so far. | Practice and calibration, not strict player-side scoring. |
| Side-known reconstructed | Public state plus that side's known team/moves, reconstructed from a source or provided team sheet. | Better player-advice practice when the reconstruction is credible. |
| Boss-side romhack | Boss own team and public player reveals only. | Boss AI policy review. |

Do not mix these modes inside a score without saying so.

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
`docs/pokemon_mastery/quick_tests/`:

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
Earliest meaningful error:

## Turn N

Public state:
My p1 answer:
My p2 answer:
Actual choices:
Grade:
Reusable lesson:
```

## When To Stop And Study

Stop the replay and study instead when the same error class appears twice:

- repeatedly missing preservation switches;
- repeatedly stacking hazards without retention;
- repeatedly treating unknown teams as previewed;
- repeatedly choosing damage over route progress;
- repeatedly missing Rest, Sleep Talk, Explosion, phazing, or PP implications.
