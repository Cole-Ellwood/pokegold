# Mechanics Pending Index

Date: 2026-05-14

Purpose: prevent vanilla GSC knowledge from being used as local romhack truth
when a move recommendation depends on mechanics. This is a routing index, not a
fixture result.

Status labels:

- `runtime_verified`: confirmed by local fixture, debugger, emulator trace, or
  equivalent runtime evidence.
- `source_verified`: confirmed in local source or local docs, but not yet
  traced at runtime.
- `supplied_unverified`: stated in project notes or user prompt, but not yet
  checked locally.
- `unknown`: no usable local evidence found yet.
- `not_decision_relevant`: named for awareness, but not needed for the current
  recommendation.

## Live Advice Rule

If a live romhack recommendation depends on a mechanic below, include its
status or cap confidence. Do not settle these with web search.

## Pending Mechanics

| Mechanic | Current status | Check first | Why it matters |
| --- | --- | --- | --- |
| Spikes layer count | runtime_verified | `romhack_deltas/spikes_and_rapid_spin.md`, `mechanics_fixtures/spikes_rapid_spin/README.md` | Changes hazard route value. |
| Successful Rapid Spin hazard-clear command clears all layers | runtime_verified | `romhack_deltas/spikes_and_rapid_spin.md`, `mechanics_fixtures/spikes_rapid_spin/README.md` | Changes Spin windows and hazard retention. |
| Spikes/Rapid Spin timing | unknown | `mechanics_fixtures/spikes_rapid_spin/README.md` | Affects same-turn route claims. |
| Sleep duration and wake timing | unknown | local source or emulator trace | Affects absorber and Sleep Clause planning. |
| Sleep Talk and Rest behavior | unknown | local source or emulator trace | Affects sleeper stay/switch choices. |
| Explosion timing and damage | unknown | local source or emulator trace | Affects one-time trade valuation. |
| Ghost immunity and Explosion interactions | unknown | local source or emulator trace | Affects cash-out and blocker routes. |
| Phazing timing and failure cases | unknown | local source or emulator trace | Affects setup denial and support handoff. |
| Type passives | source_verified | `romhack_deltas/type_passive_fixture_priorities.md`, `romhack_deltas/type_passive_route_impacts.md` | Affects damage, immunities, and route maps. |
| Focus Band and Quick Claw behavior | unknown | local source or emulator trace | Affects worst plausible branches. |
| Counter/Mirror Coat behavior | unknown | local source or emulator trace | Affects attack/switch branch pricing. |
| Ordinary boss AI information limits | source_verified | `boss_ai_re_solve_trigger_audit_2026-05-14.md` | Prevents hidden-info boss policy. |
| Haki/oracle behavior | supplied_unverified | dedicated Haki docs or source when relevant | Must stay quarantined from ordinary AI. |

## Fixture Promotion Rule

When a mechanic is verified, update only this row and the fixture or delta doc
that contains the evidence. Do not rewrite live policy cards unless the
mechanic changes a move recommendation.
