# Pokemon Mastery Compounding Loop — Operator Runbook

Status: canonical. This is the entry doc for any Claude or Codex session
that wants to run one iteration of the Pokemon Mastery training loop.

## What the loop is

A durable, retrieval-augmented training cycle that drives validation
top-move agreement with strong GSC OU players from the current ~30-50%
plateau to the user-selected stretch gate. The diagnosis: the existing
mastery system has full measurement infrastructure but no position-keyed
retrieval at decision time — heuristic cards are abstract rules, not
pattern instances. The Compounding Loop adds a retrievable case library
that fires the right past lesson at every fresh prediction.

The loop is biased toward improvement (not mathematically guaranteed) by
four properties: monotone case-library growth, anti-regression battery,
held-out validation to prevent overfitting illusion, and stagnation
detection that triggers approach change.

## Gate (stretch)

Pass requires the latest validation-tier metrics row to satisfy ALL of:

| Metric | Target |
| --- | --- |
| top_match | >= 60% |
| acceptable_match | >= 75% |
| severe_blunder_rate | == 0 |
| positive_selection_converter | >= 65% |
| decision_count in window | >= 30 |

Plus case library breadth >= 150 distinct fingerprints, regression battery
100% pass, and a user sign-off on a final-exam packet (3 fresh sealed_exam
replays predicted cold).

The gate values live in [tools/pokemon_mastery/case_library/loop_state.json](../../tools/pokemon_mastery/case_library/loop_state.json)
under `gate_target` — that file is the source of truth, not this doc.

## Files

| Path | Role |
| --- | --- |
| [tools/pokemon_mastery/case_library/loop_state.json](../../tools/pokemon_mastery/case_library/loop_state.json) | Durable loop state: iteration count, phase rotation hints, gate target, EMA params. |
| [tools/pokemon_mastery/case_library/cases.jsonl](../../tools/pokemon_mastery/case_library/cases.jsonl) | Append-only extracted case rows (state fingerprint + pro action + lesson). |
| [tools/pokemon_mastery/case_library/replay_index.jsonl](../../tools/pokemon_mastery/case_library/replay_index.jsonl) | Append-only tier partition: every replay tagged study / validation / sealed_exam at fetch time. |
| [tools/pokemon_mastery/case_library/metrics.jsonl](../../tools/pokemon_mastery/case_library/metrics.jsonl) | Rolling-window aggregate metrics; the validation-tier row is the headline. |
| [tools/pokemon_mastery/case_library/regression/](../../tools/pokemon_mastery/case_library/regression/) | Constructed probes — one per recurring (failure_mode, reasoning_class). |
| [tools/pokemon_mastery/case_library/schema.json](../../tools/pokemon_mastery/case_library/schema.json) | Schema for cases, replay rows, metrics rows; reasoning_class and failure_mode enums. |
| [tools/pokemon_mastery/fetch_replay.py](../../tools/pokemon_mastery/fetch_replay.py) | Showdown API client + tier-assignment policy. |
| [tools/pokemon_mastery/fingerprint.py](../../tools/pokemon_mastery/fingerprint.py) | Public-state fingerprint extractor; canonical fingerprint_hash. |
| [tools/pokemon_mastery/replay_turn_pause.py](../../tools/pokemon_mastery/replay_turn_pause.py) | Existing turn-pause helper for prompt/reveal at turn N. |
| [tools/pokemon_mastery/verify_loop_state.py](../../tools/pokemon_mastery/verify_loop_state.py) | Schema valid + no tier contamination. (Verifier v2.) |
| [tools/pokemon_mastery/verify_regression_battery.py](../../tools/pokemon_mastery/verify_regression_battery.py) | Every probe finds a matching case. (Verifier v3.) |
| [tools/pokemon_mastery/verify_progress_gate.py](../../tools/pokemon_mastery/verify_progress_gate.py) | Latest validation metrics row meets every threshold. (Verifier v4.) |
| [tools/pokemon_mastery/verify_case_breadth.py](../../tools/pokemon_mastery/verify_case_breadth.py) | Distinct fingerprint count meets target. (Verifier v5.) |

## The six phases

Each iteration picks the highest-value phase based on `loop_state.json`
and what's missing from the gate:

1. **INGEST** — fetch one unseen study-tier replay; for each scorable turn,
   reconstruct the public state, query the case library for K nearest past
   cases by fingerprint, freeze a prediction WITH explicit reference to
   which retrieved cases fired (or "no cases fired"), reveal, score per
   [replay_turn_pause_protocol.md](replay_turn_pause_protocol.md). Save a
   quick_tests artifact AND append a row to [measurement_progress_ledger.csv](measurement_progress_ledger.csv).
2. **DIAGNOSE+EXTRACT** — for every scored decision (miss OR hit), append a
   case row to `cases.jsonl` matching `schema.json`: fingerprint, pro_action,
   predicted_action, pro_reasoning_class (from the enum), failure_mode, lesson
   (short imperative recipe), evidence_url. Hits are kept (positive patterns
   are still retrieval-valuable).
3. **REGRESSION-PROTECT** — when a (failure_mode, reasoning_class) pair recurs
   >=3 times, generate a constructed probe under `regression/` with the
   minimal-position class + corrected action. `verify_regression_battery.py`
   enforces that every probe continues to find a matching case.
4. **VALIDATE** — every 5 ingest-iterations, fetch and score ONE validation-tier
   replay. Validation replays are NEVER mined for cases. Update the rolling-window
   row in `metrics.jsonl` with `tier=validation`.
5. **STAGNATION-CHECK** — after every 3 validation runs, compute EMA of validation
   top_match. If flat or declining 3 windows in a row, ESCALATE: deep-study →
   cross-domain transfer → block for human review.
6. **CONSOLIDATE** — every 20 iterations, aggregate cases by (failure_mode,
   reasoning_class); update [heuristic_core/](heuristic_core/) cards to reflect
   what actually pulls weight in retrieval. Never delete evidence; demote with
   `compressed_into`.

## Pre-freeze context discipline

For fresh-replay predictions, load **only**:

- [live_core.md](live_core.md)
- The replay prompt from `replay_turn_pause.py prompt --turn N`
- At most one [heuristic_core/*.md](heuristic_core/) card chosen by the question
- The K retrieved cases from the case library

Do NOT load: cookbook, source_to_policy_ledger, paused_turn_atlas, full
policy_cards, scored quick tests, reviews, or external research returns
before freezing. Do NOT use web search before freezing a fresh prediction.

After scoring, full archives are open for postmortem.

## Partition discipline

`replay_index.jsonl` is append-only. Tier policy enforced by
[fetch_replay.py:assign_tier](../../tools/pokemon_mastery/fetch_replay.py):

- rating < 1400: skip (don't add to index).
- rating >= 1400, ratio holds (validation*4 < study): study.
- rating >= 1600 AND ratio allows validation: validation.
- sealed_exam: only set explicitly at final-exam time.

`verify_loop_state.py` enforces that `cases.jsonl` rows only carry `tier=study`.
Cases mined from validation or sealed_exam replays will fail the verifier.

## Run one iteration

If you are a Claude session with the pgoal armed, the Stop hook handles
this automatically. To run a single manual iteration as either Claude or
Codex:

```bash
# 1. Pick what phase to run. Check loop state first:
cat tools/pokemon_mastery/case_library/loop_state.json | grep iteration_count

# 2. INGEST: fetch one study-tier replay.
python tools/pokemon_mastery/fetch_replay.py pick --for-tier auto

# 3. Read the prompt for turn 1:
python tools/pokemon_mastery/replay_turn_pause.py \
  tmp/pokemon_mastery_replays/<replay_id>.log prompt --turn 1

# 4. Compute the fingerprint:
python tools/pokemon_mastery/fingerprint.py \
  tmp/pokemon_mastery_replays/<replay_id>.log --turn 1 --side p1

# 5. Query the case library for matching past cases (once retrieve_cases.py
#    lands), freeze a prediction, then reveal and score:
python tools/pokemon_mastery/replay_turn_pause.py \
  tmp/pokemon_mastery_replays/<replay_id>.log reveal --turn 1

# 6. Append a case row to case_library/cases.jsonl.
# 7. Save the scored artifact under docs/pokemon_mastery/quick_tests/.
# 8. Append a row to docs/pokemon_mastery/measurement_progress_ledger.csv.
# 9. Increment loop_state.iteration_count and update last_iteration_phase.
# 10. Commit with message: pokemon-mastery-loop: iter N <phase> <replay_id>
```

`loop_runner.py` (queued infrastructure) will automate steps 1, 6-10.

## Start (or restart) the loop in a fresh Claude session

The /pgoal state is per-worktree-path (project hash). Opening Claude in a
fresh worktree where the pgoal was never armed shows no active goal even
though the loop code is present. To arm it:

```bash
python ~/.claude/skills/pgoal/scripts/pgoal.py set \
  --objective "$(cat tools/pokemon_mastery/pgoal_spec/objective.txt)" \
  --phase implementation \
  --criteria "$(cat tools/pokemon_mastery/pgoal_spec/criteria.txt)" \
  --constraints "$(cat tools/pokemon_mastery/pgoal_spec/constraints.txt)" \
  --verify "$(cat tools/pokemon_mastery/pgoal_spec/verify.txt)" \
  --long-run --continuation-style adaptive --full-prompt-every-iterations 25 \
  --assume-defaults
```

Pgoal state is in `~/.claude/goal-state/by-project/<sha256(worktree-path)>/`
and persists across sessions; the Stop hook auto-continues iterations.
The case library at `tools/pokemon_mastery/case_library/` is in-repo, so any
checkout sees the same persistent brain.

For Codex sessions, the pgoal harness isn't available — they invoke loop
work directly via `python tools/pokemon_mastery/loop_runner.py`.

## Verifiers

The five automated criteria are tied to commands that exit 0 (pass) or
nonzero (fail). Run all of them with:

```bash
python -m pytest tools/pokemon_mastery/ -q
python tools/pokemon_mastery/verify_loop_state.py
python tools/pokemon_mastery/verify_regression_battery.py
python tools/pokemon_mastery/verify_progress_gate.py
python tools/pokemon_mastery/verify_case_breadth.py
```

Or via the pgoal harness:

```bash
python ~/.claude/skills/pgoal/scripts/pgoal.py verify --run --record
```

## What gets escalated to the user

The user is gameplay-design lead and does not code. They get pulled in for:

1. **Final-exam packet sign-off** (the only required user gate): 3 fresh
   sealed_exam replays predicted cold under pre-freeze discipline. They
   confirm the improvement is real.
2. **Stagnation block**: after the 3-strike escalation chain runs out
   (deep-study → cross-domain → block).
3. **Constraint conflict**: e.g., a save-format-affecting change suggested
   by consolidation.

Everything else is delegated. Decisions go through `pgoal.py decision`.

## Honest hedge

No no-weight-update loop is provably guaranteed to improve. The loop
**cannot regress** (regression battery enforces) and **can compound
monotonically** (cases only added). Under the assumption that GSC OU has a
coverable pattern set and retrieval surfaces them, the loop is expected to
converge to the gate. That's the strongest honest claim.

## Related docs

- [active_context.md](active_context.md) — startup spine for mastery work.
- [active_goal.md](active_goal.md) — overall goal statement.
- [training_cycle.md](training_cycle.md) — broader operating plan.
- [replay_turn_pause_protocol.md](replay_turn_pause_protocol.md) — scoring rules.
- [live_core.md](live_core.md) — pre-freeze move-choice entrypoint.
- [tools/pokemon_mastery/case_library/README.md](../../tools/pokemon_mastery/case_library/README.md) — files in the library.
