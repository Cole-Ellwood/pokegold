# Boss AI Preference Regression Runner — implementation plan

> Status: spec, not yet implemented. Targets `tools/boss_ai_debugger/`.
> Author: Claude (planning), 2026-05-09. Implementer: Codex.

## Purpose

Close the loop on the BOSSAI-003 / BOSSAI-004 corpus. The user labels boss-AI
candidate actions in `tools/boss_ai_preference/labels/`. The existing
`tools/boss_ai_debugger/scorer.py` is a Python heuristic that scores those
actions against the fixture's textual public-info state. Today there is no
single command that reports "scorer agreed with user on N of M labels and
disagreed on these specific pairs." That command is what this runner adds.

It is **not** an asm scorer test. It does not run `engine/battle/ai/boss.asm`.
It validates the Python heuristic in `scorer.py` against the user's labels.
The heuristic is the design proxy: when it converges with the user's taste,
its rules become the spec for any later asm tweaks.

## Inputs (existing — do not change schemas)

- `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`
  ```
  { "schema_version": 1, "fixtures": [ { id, leader, tags,
        training_focus, baseline_action_id, state, actions: [...] } ] }
  ```
  See `tools/boss_ai_preference/SCHEMA.md` §Fixtures.
- `tools/boss_ai_preference/labels/boss_ai_pairwise_preferences.jsonl` —
  one JSONL row per pairwise label:
  ```
  { fixture_id, action_a_id, action_b_id, choice, preferred_action_id,
    reason_tags, action_tags, note, ... }
  ```
  `choice` ∈ `{a_better, b_better, both_good, both_bad, other_better,
  needs_context}`. See `SCHEMA.md` §Pairwise.
- `tools/boss_ai_preference/labels/boss_ai_labels.jsonl` (single-action,
  optional second pass): `{fixture_id, action_id, label, rank, ...}`
  with `label` ∈ `{best, good, bad, cheap, scary_good, needs_context}`.

Reuse `tools/boss_ai_preference/data.py` loaders (`load_fixtures`,
`fixture_map`) — already in the package, no need to reinvent.

## Output

### Stdout summary (default)

```
Boss AI preference regression: 47 / 50 strict pairwise labels agree (94.0%)
  PASS threshold: 0.80
  Skipped 12 non-strict labels (both_good=4 both_bad=2 needs_context=3 other_better=3)

Disagreements:
  bugsy_scyther_vs_quilava_fire_pressure
    label: a_better (move_swords_dance > move_wing_attack)
    scorer: move_wing_attack=62 move_swords_dance=44 → b_better
    note: "swords dancing first still kills quilava in 2 turns…"
  …
```

### `--json-out path/to/report.json`

```
{
  "schema_version": 1,
  "generated_at": "...",
  "threshold": 0.80,
  "strict_label_count": 50,
  "strict_agreement_count": 47,
  "agreement_rate": 0.94,
  "skipped": { "both_good": 4, "both_bad": 2, "needs_context": 3,
               "other_better": 3 },
  "disagreements": [
    { "fixture_id": "...", "action_a_id": "...", "action_b_id": "...",
      "label_choice": "a_better", "scorer_choice": "b_better",
      "scorer_scores": { "move_swords_dance": 44, "move_wing_attack": 62 },
      "label_note": "..." }
  ]
}
```

The JSON shape follows the "structured artifact for AI hand-off" pattern
from `docs/agent_navigation/` — easy to consume by another agent.

### Exit code

- `0` if `agreement_rate >= threshold` AND no errors.
- `1` if below threshold.
- `2` on schema or IO errors (mirrors `data.PreferenceDataError` handling
  in the existing CLI).

## Algorithm

```
load fixtures, build fixture_map by id
load pairwise labels
for each label:
  if label.choice not in {a_better, b_better}:
    bucket as skipped (non-strict ordering)
    continue
  fixture = fixture_map[label.fixture_id]   # error if missing
  action_a = find by id in fixture.actions  # error if missing
  action_b = find by id in fixture.actions
  score_a = score_action(fixture, action_a).score
  score_b = score_action(fixture, action_b).score
  if score_a == score_b:
    bucket as indeterminate (count as disagreement)
  scorer_choice = "a_better" if score_a > score_b else "b_better"
  if scorer_choice == label.choice:
    pass count++
  else:
    record disagreement
agreement_rate = pass_count / strict_label_count
emit summary + (optional) json
exit per threshold
```

The single-action labels file (`boss_ai_labels.jsonl`) is optional second-
phase scope. If supported now: rank correlation per fixture between
`label.rank` and the scorer's score-sorted ranking. Spearman or simple
position-mismatch count is fine — write it as a separate metric, not
mixed into the pairwise rate. Default off; opt-in via `--include-rank-labels`.

## CLI surface

```
python -m tools.boss_ai_debugger regress [options]

Options:
  --fixtures PATH        default: tools/boss_ai_preference/fixtures/...
  --labels PATH          default: tools/boss_ai_preference/labels/...pairwise...
  --threshold FLOAT      default: 0.80
  --json-out PATH        write structured report; "" disables
  --include-rank-labels  also score the single-action labels file
  --quiet                summary only, no per-disagreement detail
```

Add `regress` as a new subparser in `tools/boss_ai_debugger/__main__.py`
alongside `list / inspect / judge / report`. Reuse `add_common_paths`.

## Audit hook

`tools/audit/check_boss_ai_preference_regression.py` — minimal wrapper
that calls the regress subcommand with the default threshold and exits
on its return code. Add to `tools/audit/check_release_smoke.py` only if
the user asks; the regression rate floor is a soft target, not a release
gate. Default: standalone audit, not in the release-smoke chain.

## Implementation files

- `tools/boss_ai_debugger/regression.py` — new, ~150-250 LoC. Contains:
  - `RegressionResult` dataclass.
  - `evaluate_label(fixture, label, scorer)` — single-label verdict.
  - `evaluate_corpus(fixtures, labels, threshold)` — aggregate.
  - `format_summary(result)` / `format_json(result)`.
- `tools/boss_ai_debugger/__main__.py` — add `regress` subcommand (~30 LoC
  new).
- `tools/audit/check_boss_ai_preference_regression.py` — wrapper script,
  ~30 LoC.
- `tools/boss_ai_debugger/README.md` — append a `regress` usage section.
- (no schema changes; no fixture or label edits)

Tests:
- `tools/boss_ai_debugger/tests/test_regression.py` — unit tests
  covering: strict-pair pass, strict-pair fail, score tie → disagreement,
  non-strict choices skipped, missing fixture/action → schema error,
  threshold pass/fail exit codes. Use the existing fixture file as a
  realistic input; create one tiny synthetic fixture inline for the
  edge-case tests.

## Out of scope (do not build these here)

- No PyBoy. No real ROM execution. No WRAM injection. No save state.
- No changes to the asm scorer in `engine/battle/ai/boss.asm`.
- No changes to `tools/boss_ai_preference/` schemas, fixtures, or labels.
- No changes to `tools/boss_ai_debugger/scorer.py`'s rules. (If the
  runner reveals systematic disagreements, the user reviews them and
  decides whether the rules or the labels need adjustment — that's a
  separate workstream.)
- No new label format. Build on top of the JSONL files that exist today.
- No release-smoke gating. The runner is informational by default.

## Estimate

150-250 LoC + ~50 LoC of tests. 1-2 hours given the existing
`scorer.py` and `data.py` already do all the per-action work.

## Acceptance criteria

- [ ] `python -m tools.boss_ai_debugger regress` runs against the current
      committed fixtures + 7 existing labels, prints a summary, exits 0
      or 1 per threshold.
- [ ] `python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json`
      writes a JSON report matching the schema in this doc.
- [ ] Unit tests pass: `python -m pytest tools/boss_ai_debugger/tests/`
      (or `python -m unittest tools.boss_ai_debugger.tests.test_regression`
      if pytest is not in the project's dev deps — match whatever the
      repo already uses).
- [ ] `python tools/audit/check_boss_ai_preference_regression.py` runs
      and exits cleanly when the threshold is met; non-zero when not.
- [ ] No changes to `tools/boss_ai_preference/`, no new dependencies,
      no schema changes.
- [ ] `python tools/audit/check_release_smoke.py` still PASS.
- [ ] Commit messages follow this repo's convention: lowercase prefix,
      em-dash, terse. e.g. `bossai-debugger: add preference regression
      runner — pairwise label vs scorer.score_action`.
- [ ] Co-Authored-By trailer on commits.

## Risks / things to flag

- **The lucid-bartik-93f5ff worktree currently has uncommitted deletions
  of all of `tools/boss_ai_preference/` and `tools/boss_ai_debugger/`.**
  If the user commits that rollback before the runner ships, this work
  becomes obsolete. Implementer should `git fetch` + check the dev tip
  state before starting; if the toolchains are gone, escalate before
  building.
- The existing 7 labels include several `both_good` / `other_better` /
  `needs_context` choices, which are intentionally non-strict and get
  skipped. Initial agreement rate may be measured over a small N. That's
  fine — runner still works; sample size will grow as the user labels
  more fixtures.
- Score ties in the heuristic happen often (the rules are coarse). Treat
  ties as disagreements; do not auto-credit them. If this turns out to
  be too punishing in practice, the user can adjust the threshold or
  add a tie-break rule to `scorer.py` separately.
