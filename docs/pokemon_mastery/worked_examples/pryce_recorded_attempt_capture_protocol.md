# Worked Example: Pryce Recorded Attempt Capture Protocol

Purpose: define the minimum useful recording for filling
`pryce_scored_manual_worksheet.md`. This is not a battle plan or answer key; it
is the capture contract for turning one real Pryce attempt into reviewable
evidence.

Status:

- No complete local Pryce attempt recording was found in the docs/audit study
  surfaces checked on 2026-05-13.
- Existing Pryce artifacts are route maps, drills, worksheets, benchmarks, and
  Boss AI traces, not a user-perspective full battle attempt.

Local evidence:

- Pryce scored worksheet: `pryce_scored_manual_worksheet.md`.
- Pryce 30-turn drill: `pryce_30_turn_ledger_drill.md`.
- Pryce pre-battle route sheet: `pryce_pre_battle_route_sheet.md`.
- Pryce route map: `../boss_route_maps/pryce_turn1_route_sheet.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Mechanics overview and generated mechanics reference:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert study anchors:

- Smogon GSC Spikes material:
  <https://www.smogon.com/gs/articles/gsc_spikes>.
- Smogon long-term thinking material:
  <https://www.smogon.com/rs/articles/long_term_thinking>.
- Smogon risk/reward material:
  <https://www.smogon.com/resources/beginner/bw_risk_reward>.

## Why This Exists

The Pryce worksheet needs public-state evidence. A vague memory of the fight is
not enough because Pryce tests several state transitions:

```text
Cloyster Spikes or Explosion
Dewgong Rapid Spin or Encore
Piloswine Roar through hazards
Slowking Thunder Wave, Rest, and wake timing
Sneasel cleanup and Quick Attack range
```

The useful review question is not "did we win?" It is whether the advice
preserved the route ledger through those transitions.

## Minimum Useful Recording

Any one of these is enough to start:

- a video recording with visible HP bars, turns, and move text;
- an emulator log with turn transcript and HP/status snapshots;
- annotated screenshots after every turn plus manual move notes;
- a hand-written turn log if it records enough public state to reconstruct
  each critical decision.

Not enough by itself:

- final result only;
- team list only;
- a damage impression such as "Cloyster did a lot";
- a Boss AI trace that shows only Pryce's internal move choice without the
  user-facing battle state.

## Pre-Battle Capture

Record before talking to Pryce:

```text
ruleset:
  bag items allowed / limited / banned:
  battle style:
  set mode or switch mode:
  any level cap or self-imposed rules:

player team:
  species / level / item / moves:
  current HP:
  status:
  type/passive notes known from local docs:

lead plan:
  intended lead:
  lead's job:
  primary route:
  backup route:
  irreplaceable pieces:
  expendable or narrow-job pieces:
  first abandonment condition:
```

The lead plan must answer:

```text
If Cloyster sets Spikes, Surfs, Ice Beams, or Explodes, which later Pryce route
becomes harder to stop?
```

## Turn Capture

Record after each turn:

```text
turn:
our active:
Pryce active:
our move:
Pryce move:
move order:
HP before and after, preferably exact or fraction:
status changes:
Spikes layers on our side:
Spikes layers on Pryce's side:
Encore state:
Rest / sleep counters:
Roar or forced switch:
Explosion availability:
revealed damage or speed evidence:
our intended next route:
Pryce's current route:
```

If exact HP is unavailable, record the visible bar estimate and mark it as
approximate. Do not convert approximate bars into exact damage claims later.

## Mandatory Critical Turns

The recording is review-ready only if these are visible or reconstructable:

1. Cloyster's first hazard / attack / Explosion decision.
2. The first time player Spikes are set, denied, spun, or made irrelevant.
3. Dewgong's first Rapid Spin or Encore opportunity.
4. The first sacrifice, Explosion threat, or forced-entry trade.
5. Piloswine's first Roar or hazard-cycle opportunity.
6. Slowking's first Thunder Wave or Rest decision.
7. Sneasel's first entry or first Quick Attack cleanup threat.
8. The earliest turn where the original pre-battle route was abandoned.

If one of these never happens because the boss faints first, write that as a
confirmed absence, not as a missing field.

## Missing Evidence Flags

Use these labels while recording:

```text
MISSING_HP_EXACT:
  exact HP was not captured; damage thresholds may be approximate

MISSING_SPEED_EVIDENCE:
  move order did not prove who is faster in the relevant matchup

MISSING_LAYER_STATE:
  current Spikes count is uncertain after a set or spin turn

MISSING_STATUS_CLOCK:
  sleep, Rest, Encore, paralysis, or wake timing cannot be reconstructed

MISSING_EXPLOSION_STATE:
  Cloyster's Explosion availability or turn order is uncertain

MISSING_TYPE_EVIDENCE:
  a resistance, immunity, super-effective, or neutral claim was made without
  local type/passive evidence

MISSING_DAMAGE_SOURCE:
  a damage range or survival threshold was asserted without calculator,
  debugger, source, or observed roll support
```

Each missing evidence flag must include:

```text
decision affected:
what answer might flip:
how to capture it next time:
```

## Scoring Readiness Gate

Use `pryce_scored_manual_worksheet.md` only when:

- the pre-battle team and ruleset are known;
- each mandatory critical turn is visible, reconstructable, or explicitly
  absent;
- Spikes layer state can be reconstructed after every Spikes or Rapid Spin
  turn;
- status, Encore, Rest, Roar, and Explosion events are timestamped;
- at least one route-abandonment or route-confirmation point is captured;
- every type-effectiveness word is tied to romhack evidence when
  decision-relevant.

If this gate fails, do not score the battle yet. Write an evidence gap report
instead.

## Suggested File Layout

For the first real attempt, save artifacts with this shape:

```text
docs/pokemon_mastery/workspace/battle_captures/
  pryce_attempt_YYYYMMDD/
    README.md
    turn_log.md
    pre_battle_state.md
    critical_turns.md
    screenshots_or_video_links.md
    evidence_gaps.md
```

`README.md` should state whether the attempt is:

```text
capture_only
ready_for_scoring
scored
quarantined_missing_state
```

## Review Questions After Capture

Before scoring, answer:

```text
What did the turn-1 plan try to preserve?
When did Spikes change the route, if ever?
Did Rapid Spin erase a real route or only a decorative layer?
Did Encore or Roar invalidate a scripted plan?
Was Cloyster's Explosion treated as a route trade or just damage?
Was Slowking Rest forced at a punishable time?
Did Sneasel inherit a cleanup board created by earlier chip?
What was the earliest meaningful route gain or loss?
```

## Extracted Lesson

A real Pryce attempt is valuable only if it captures enough public state to
grade decisions before outcomes are known. The capture goal is to preserve the
evidence needed for route reasoning: hazard count, spin timing, Encore/Roar
state changes, Explosion availability, Rest and status clocks, and the exact
moment the original plan should be abandoned.
