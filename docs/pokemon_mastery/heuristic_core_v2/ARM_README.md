# heuristic_core_v2 — Intervention Arm

This is the **intervention arm** of the A/B counterfactual control for the
GSC mastery training-loop /pgoal (armed 2026-05-16).

## What this is

`heuristic_core/` is the **frozen baseline**. Its content matches the
state at commit `fad81f02` (the packet 045 baseline). It does not change
while the proof bar is open.

`heuristic_core_v2/` is the **intervention**. Edits during /pgoal
iterations go here. Each packet runs the same replay twice — once
loading v1, once loading v2 — and the score delta isolates whether
the intervention causes the lift.

`live_core.md` (baseline) and `live_core_v2.md` (intervention) follow
the same A/B pattern.

## Why

Proof-bar condition 4 (counterfactual): "SAME-replay control with
intervention OFF regresses to ~15/30. Without this you have correlation,
not causation."

A/B card sets implement that condition cleanly: same replay, same
freeze protocol, only the loaded-card content differs.

## Rules for editing this arm

- All intervention content goes in `heuristic_core_v2/` or
  `live_core_v2.md`. Never edit baseline `heuristic_core/` or
  `live_core.md` while the /pgoal is open.
- Each packet spec must declare which arm it loads. Default packet
  template runs both arms.
- If a single intervention is empirically validated (proof bar
  passes), the **promotion** of v2 → v1 is a separate operation
  recorded in the proof_bar_status doc, not inline.
- If multiple competing interventions are being A/B/C tested, fork
  `heuristic_core_v3/` etc. Don't squash them into v2.

## Initial state (this commit)

`heuristic_core_v2/` is byte-identical to `heuristic_core/`.
`live_core_v2.md` is byte-identical to `live_core.md`.
The first non-trivial intervention will be packet 046's artifact-format
change (audit-first ordering + Revised top slot per default plan 5b).
