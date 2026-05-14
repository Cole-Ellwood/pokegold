# Worked Example: Pryce Scored Manual Worksheet

Purpose: convert `pryce_30_turn_ledger_drill.md` into a fillable score sheet
for one real recorded Pryce attempt before simulator validation. This is an
audit tool, not an answer key.

Local evidence:

- Pryce 30-turn drill: `pryce_30_turn_ledger_drill.md`.
- Pryce pre-battle route sheet: `pryce_pre_battle_route_sheet.md`.
- Pryce route map: `../boss_route_maps/pryce_turn1_route_sheet.md`.
- Live advice shape: `../boss_turn_advice_template.md`.
- Benchmark grading notes:
  `../pro_notes/03_benchmark_architecture_and_policy_schema.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Mechanics overview and generated mechanics reference:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert study anchors:

- Smogon GSC Spikes material: hazards are progress only when layer state,
  removal, forced switching, status, or thresholds make them matter:
  <https://www.smogon.com/gs/articles/gsc_spikes>.
- Smogon long-term thinking material: start from the route, then preserve the
  pieces that make the route possible:
  <https://www.smogon.com/rs/articles/long_term_thinking>.
- Smogon risk/reward material: compare the likely branch with the worst
  plausible branch before spending an irreplaceable resource:
  <https://www.smogon.com/resources/beginner/bw_risk_reward>.

## Use Case

Use this worksheet after a recorded Pryce attempt exists: video, emulator log,
manual turn log, or annotated screenshots. Freeze the public state before each
scored decision. Grade advice from information available at that moment, not
from the outcome that happened later.

The worksheet is ready for simulator validation only when it can explain why a
decision was good or bad without using hidden future information.

## Required Capture

Record these before scoring:

- Player team, levels, moves, held items, HP, and status before battle.
- Item and healing policy: no items, limited items, or normal in-game bag.
- Exact turn transcript or video timestamps.
- Damage observed, preferably as HP values or fractions.
- Move order and any speed evidence.
- Spikes layers on both sides after every hazard or spin turn.
- Status, Encore, Rest, and sleep clocks.
- Cloyster Explosion availability and whether it was spent.
- Dewgong Rapid Spin and Encore opportunities.
- Piloswine Roar events and forced-entry damage.
- Slowking Thunder Wave, Rest, and wake timing.
- Sneasel entry, coverage, and priority range.
- Any type, passive, immunity, resistance, or damage claim source.
- Final outcome and remaining resources.

If a field is missing, do not invent it. Mark the answer as an assumption and
write what decision would flip if the missing field changed.

## Pre-Battle Prediction Score

Score 20 points before turn 1.

Fill:

```text
player ruleset:
primary route:
backup route:
preferred lead:
lead purpose:
irreplaceable player pieces:
expendable or narrow-job pieces:
Pryce routes to deny:
information that would flip the lead or plan:
mechanics claims that need local evidence:
```

Rubric:

```text
4 lead plan tied to Pryce's opener, not just type advantage
4 named primary and backup routes
4 irreplaceable-piece map
3 Pryce route triage: Spikes, Spin, Explosion, Roar, Rest, Sneasel cleanup
3 verification hooks for type chart, passives, hazards, or damage
2 clear abandonment conditions for the initial plan
```

## Critical Turn Scorecard

Score each critical turn out of 20 points.

Required scored turns:

- Pryce lead action and the first Cloyster hazard or Explosion decision.
- The first Dewgong Rapid Spin or Encore decision.
- The first sacrifice, Explosion, or forced-entry trade.
- The first Piloswine Roar or hazard-cycle decision.
- The first Slowking Thunder Wave or Rest decision.
- Sneasel's first entry or first priority-range decision.
- The final route decision that made the battle won, lost, or stable.

Fill one copy per scored turn:

```text
turn / timestamp:
public state:
our original plan:
is the original plan still live?:
our current best route:
Pryce current best route:
our irreplaceable pieces:
Pryce irreplaceable pieces:
candidate moves:
recommended move:
acceptable alternatives:
catastrophic moves:
likely Pryce response:
worst plausible branch:
resource gained:
resource spent:
type / passive / damage evidence used:
information that would change the answer:
actual outcome:
decision quality:
outcome quality:
mistake label, if any:
score:
```

Rubric:

```text
4 mechanics and public-state accuracy
4 route and win-condition clarity
4 candidate ranking with resource gain and cost
3 worst plausible branch identified
2 preservation or expendability reasoning
2 answer-changing information
1 concise recommendation grounded in the state
```

Caps:

- Mechanically impossible advice caps at 6/20.
- Omitting an immediate catastrophe branch caps at 12/20.
- Using hidden future information invalidates the turn score.
- Failing to name a route caps at 14/20, even if the move happened to work.
- Using type words such as `super effective`, `resisted`, `immune`, or
  `neutral` without romhack-specific evidence caps at 12/20 when the claim is
  decision-relevant.

Decision quality labels:

```text
good decision / good outcome
good decision / bad outcome
bad decision / good outcome
bad decision / bad outcome
needs_context
```

`needs_context` is valid only if the missing field is named and would plausibly
change the answer.

## Battle Exit Score

Score 20 points after the battle.

Fill:

```text
result:
remaining player resources:
remaining Pryce resources:
earliest meaningful route loss or route gain:
best preserved resource:
worst avoidable branch:
old plan that had to be abandoned:
move class that became better over time:
move class that became worse over time:
one reinforced recipe:
one revised recipe or mistake pattern:
one new benchmark or mutation card to create:
unverified mechanics or damage questions:
```

Rubric:

```text
5 earliest meaningful error or conversion point
4 decision quality separated from outcome quality
4 plan revision and route handoff
3 recipe reinforced, revised, or rejected
2 new benchmark or mutation extracted
2 unresolved evidence recorded instead of guessed
```

## Severity Tags

Use these labels so mistakes become future tests:

```text
STATE_TRACKING_ERROR
MECHANICS_ERROR
HIDDEN_INFO_ERROR
WIN_CONDITION_ERROR
PRESERVATION_FAILURE
OVERFITTED_SCRIPT_ERROR
RESULT_BASED_REVIEW
DAMAGE_RANGE_ERROR
ROMHACK_DELTA_ERROR
```

## Pass Thresholds

Use this only as a readiness signal, not as proof of mastery.

```text
80+ total: strong enough to review against another recorded attempt
65-79 total: useful, but review severe errors before simulator validation
below 65 total: not ready for simulator validation
```

Automatic severe fail:

- The advice ignores a decision-relevant local mechanics delta.
- The advice repeats a stale plan after Spin, Encore, Explosion, Roar, Rest,
  status, a miss, an unexpected switch, or unexpected damage.
- The advice sacrifices the only answer to Pryce's live route without naming a
  stronger route opened by that sacrifice.
- The advice treats the simulator, competitive memory, or type slogans as
  romhack truth without local evidence.

## Extracted Lesson

A scored worksheet is the bridge from study notes to simulator validation. It
forces the adviser to choose from the public state, name the route being
advanced, price the worst plausible branch, and record where local mechanics
evidence is still missing. For Pryce, the important proof is not "the plan won."
It is whether the plan survived Spikes, Rapid Spin, Encore, Explosion, Roar,
Rest, Thunder Wave, and Sneasel cleanup without dropping the route ledger.
