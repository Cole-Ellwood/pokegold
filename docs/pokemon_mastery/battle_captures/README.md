# Battle Capture Evidence Gate

Purpose: keep exact move practice tied to real public battle states. Constructed
boss drills are useful, but the next competence proof needs one actual player
team or recorded attempt so advice can be scored across consecutive turns.

Status on 2026-05-13: `blocked_no_real_team`.

## Current Evidence Checked

- `docs/pokemon_mastery/worked_examples/exact_move_drill_scorecard_2026-05-13.md`
  asks for exact recommendations across at least three consecutive public
  states from one actual player team or recorded attempt.
- `docs/pokemon_mastery/worked_examples/pryce_recorded_attempt_capture_protocol.md`
  reports that no complete local Pryce attempt recording was found in the
  docs/audit study surfaces checked on 2026-05-13.
- `audit/boss_ai_trace/gym_leader_verification_2026-04-26.md` covers boss AI
  roster and chosen-move traces, but those are not user-perspective full battle
  attempts.
- The scratch save probe documented in the boss AI audit work found
  `pokegold.sav` as an early Route 29 state with one level-11 party member,
  not a usable gym-leader advice state.

Do not silently replace this with another constructed branch tree. If no real
player team or attempt exists, write the gap plainly and keep studying expert
play, boss rosters, or mechanics until a capture is available.

## Status Labels

```text
blocked_no_real_team:
  no actual player-side party, save state, video, screenshots, or turn log is
  available for a meaningful multi-turn score.

capture_only:
  a battle recording exists but is missing enough public state that it cannot
  be scored yet.

ready_for_three_turn_scoring:
  at least three consecutive public states can be reconstructed with player
  party, boss active, HP/status, move text, and route-relevant mechanics.

scored:
  the attempt has been reviewed with exact move recommendations, route deltas,
  worst plausible branches, and mistake labels.
```

## Minimum Input To Unblock

For an actual boss attempt, capture:

```text
boss:
ruleset:
turn number:
our active:
boss active:
our team:
  species / level / item / moves / HP / status / relevant PP:
boss visible team:
  species / HP / status / revealed moves:
field:
  Spikes layers, screens, weather, boosts, trapping, Encore, sleep or Rest
  counters:
last turn:
  our move, boss move, move order, damage, status, switch or faint:
current plan:
  original route, current route, opponent route, irreplaceable pieces:
evidence:
  screenshot, video timestamp, emulator log, damage debugger, source file, or
  calculator note for any threshold that affects the answer:
```

For a three-turn score, repeat the public state before each recommendation.
The review should answer:

```text
turn:
recommended exact move:
acceptable alternatives:
catastrophic moves:
route gained:
resource spent:
worst plausible branch:
what information would flip the answer:
post-turn state update:
decision quality:
outcome quality:
```

## Evidence Rules

- Boss AI traces are opponent-model evidence, not a substitute for the
  player-facing battle state.
- Type words such as `super effective`, `resisted`, `immune`, and `neutral`
  need mechanics-profile-specific evidence when they affect a recommendation.
- Damage thresholds need a source: observed roll, debugger trace, calculator,
  local source, or an explicit approximation flag.
- Hidden information must remain public-state legal. Do not use later revealed
  boss moves or post-battle outcomes to justify the pre-turn recommendation.
- If an exact field is missing but the move is still forced, mark the confidence
  cap and state what missing information could flip the answer.

## First Target

The preferred first capture is Pryce because the existing notebook already has:

- a pre-battle route sheet;
- a 30-turn ledger drill;
- a scored manual worksheet;
- a recorded-attempt capture protocol;
- local Spikes / Rapid Spin delta notes;
- boss AI trace evidence.

That makes Pryce the fastest route from current artifacts to real consecutive
turn scoring once player-side battle evidence exists.
