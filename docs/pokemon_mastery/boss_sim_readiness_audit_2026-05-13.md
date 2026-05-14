# Boss-Sim Readiness Audit - 2026-05-13

Status: not ready to count the 50-battle / 80% validation gate.

Purpose: prevent the later boss-simulation proof target from becoming a fake
metric. A win rate only means something if the simulator, opponent controller,
mechanics profile, player team, and review artifacts are strong enough to make
the result about Pokemon decisions rather than missing evidence.

## Target Being Audited

The later proof gate is:

```text
Win at least 40 of 50 recorded boss battles against the romhack AI or another
non-self opponent model, using one declared player team and ruleset, with
pre-battle route plans, turn logs, loss review, and no known mechanics mismatch
in the route that decided the result.
```

This is validation, not the curriculum. Failing this audit does not mean the
study is bad. It means the numeric proof is not yet trustworthy.

## Current Evidence

| Requirement | Current artifact | Status |
| --- | --- | --- |
| Goal and study cadence | `active_goal.md` | Present |
| 50-battle / 80% gate definition | `boss_sim_validation_protocol.md` | Present |
| Boss coverage matrix | `boss_sim_validation_protocol.md` | Present |
| Boss route coverage index | `boss_route_maps/README.md` | Present |
| Boss roster/moves/item source alignment | `boss_route_maps/source_alignment_audit_2026-05-13.md` | Source-aligned |
| Boss opening policy | `romhack_deltas/boss_opening_policy.md` and `boss_route_maps/adaptive_lead_audit_2026-05-13.md` | Source-verified, not runtime-fixture-verified |
| Pre-battle route sheets | `worked_examples/*_pre_battle_route_sheet.md` | Present for current boss route maps |
| Type-effectiveness firewall | `python -m tools.boss_ai_preference type-evidence` | Passing; 15 chart tweaks and 22 text claims covered |
| Damage-path smoke tests | `python -m tools.damage_debugger.clobber_smoke` | Passing 25 scenarios |
| Type-passive register-safety audit | `python tools/audit/check_typepassive_c_mirror.py` | Passing |
| Mechanics doc/source alignment | `python tools/audit/check_mechanics_docs_and_fixtures.py` | Passing |
| Full-Fire low-HP passive | `tools/damage_debugger/clobber_smoke.py::special_fire_low_hp` | Debugger-verified |
| Spikes / Rapid Spin runtime behavior | `mechanics_fixtures/spikes_rapid_spin/README.md` and `romhack_deltas/spikes_rapid_spin_fixture_plan.md` | Partial smoke; text, PP, grounded HP subtraction, and timing still missing |
| First real recorded boss attempt | `worked_examples/pryce_recorded_attempt_capture_protocol.md` | Protocol present, recording absent |
| Scored boss-attempt review | `worked_examples/pryce_scored_manual_worksheet.md` | Worksheet present, no filled attempt yet |
| Declared player team / ruleset for 50 battles | none | Missing |
| Non-self simulator or emulator run against boss AI | none in notebook | Missing |

## What This Means

The notebook is strong enough for pre-battle planning and turn-advice practice.
It is not yet strong enough to claim the 80% sim gate.

The best current use of simulations is still fixture-level and scenario-level:
check damage, passives, Spikes, Rapid Spin, turn order, AI opening behavior, and
constructed route branches. Do not use aggregate boss wins as mastery evidence
until the missing pieces below are closed.

## Blocking Gaps

1. No declared player team and ruleset.

   The gate requires one team, levels, moves, items, and item-use policy before
   the first counted battle. Otherwise the test can silently become easier or
   harder between runs.

2. No non-self boss run.

   The policy has not yet been tested in recorded boss battles against the
   in-game AI or a validated opponent model. Self-play or hand-picked examples
   do not satisfy the proof target.

3. Spikes and Rapid Spin are only partially runtime-fixture-verified.

   Source says the romhack has three Spikes layers, fourth-click failure, Flying
   immunity, and Rapid Spin clearing all layers. The WRAM layer transitions,
   damage fraction helpers, and Flying early-return path are now smoke-tested,
   but runtime text, PP, grounded HP subtraction, timing, failure, and
   forced-switch interactions are still not captured. This blocks
   Spikes-heavy boss-sim claims for Pryce, Jasmine, Brock, Will, Janine, Koga,
   Karen, Bruno, and Clair.

4. Type passive coverage is incomplete.

   Full-Fire below-one-third damage is debugger-verified, but many passives that
   can flip move labels remain source-only or planned: Dark status shield,
   Dragon passives, Poison contact retaliation, Psychic Mind Shield, half-Fire
   low-HP, Electric speed order, Fighting status tuning, Grass regrowth timing,
   and Ghost damage into statused defenders.

5. Boss opening policy lacks runtime traces.

   Source identifies adaptive first-three openers for many bosses and fixed
   openers for Falkner, Bugsy, Whitney, Morty, and Red. At least one adaptive
   boss and one fixed-first boss should be observed in emulator traces before
   the opening model is treated as simulator-grade.

6. No filled manual battle review exists as the bridge to automation.

   The Pryce capture protocol and scoring worksheet exist, but no real attempt
   has been captured and graded. A manual scored fight should come before a
   50-battle automated claim so the review rubric catches missing fields.

## Next Unblocking Actions

Do these before running counted 50-battle validation:

```text
1. Capture and score one real Pryce attempt.
2. Finish Spikes/Rapid Spin runtime fixtures beyond WRAM layer bits:
   full grounded switch-in HP subtraction, GLL-SPIN-003,
   GLL-SPIKES-TIMING-001, and PP/text capture for GLL-SPIKES-002 /
   GLL-SPIN-001.
3. Add one adaptive-lead trace and one fixed-first lead trace.
4. Finish the next P1A passive fixture: either half-Fire / exact-boundary Fire
   low-HP, or Electric speed turn-order.
5. Declare the first test player team, ruleset, and item policy.
6. Run a small uncounted shakedown set, then review every loss or lucky win.
```

## What Can Be Counted Now

Can count:

- cookbook recipe improvements backed by expert study or reviewed battles;
- source-grounded route-sheet improvements;
- debugger-level damage or passive fixture passes;
- mechanics audits that directly reduce future move-choice errors;
- scored manual boss attempts once a real attempt is captured.

Cannot count yet:

- aggregate boss win rate;
- Spikes-heavy sim wins as proof;
- passives-heavy route claims without the relevant fixture;
- adaptive-lead assumptions as runtime fact;
- unlogged wins;
- wins without loss/lucky-win review.

## Practical Lesson

The 80% target is useful only if it stays adversarial. The first good boss sim
should be allowed to prove that the advisor is not ready: wrong player team,
wrong opening model, wrong passive, wrong Spikes timing, or bad plan revision
are all valuable failures. Hiding those behind a win-rate number would make the
agent worse at Pokemon, not better.
