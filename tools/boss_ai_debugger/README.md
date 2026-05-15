# Boss AI Debugger

Phase-1 debugger for BOSSAI-003.

This is fixture-backed today. It uses the BOSSAI-004 public-info fixtures and
labels as the decision corpus, then gives every legal action a readable scoring
breakdown. It does not execute the ROM scorer yet.

List fixtures:

```powershell
python -m tools.boss_ai_debugger list
```

Inspect a decision:

```powershell
python -m tools.boss_ai_debugger inspect --fixture-id clair_dragonite_vs_suicune_hidden_ice_beam
```

Record a judgment:

```powershell
python -m tools.boss_ai_debugger judge --fixture-id clair_dragonite_vs_suicune_hidden_ice_beam --action-id switch_kingdra --label best --rank 1
```

The scoring rules are deliberately small and readable. They are a review aid,
not a model checkpoint and not a source of automatic ROM edits.

Run the pairwise preference regression:

```powershell
python -m tools.boss_ai_debugger regress
```

Write a structured regression report:

```powershell
python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json
```

The regression command compares strict pairwise labels from
`tools/boss_ai_preference/labels/boss_ai_pairwise_preferences.jsonl` against
`score_action`. Non-strict labels such as `both_good`, `both_bad`,
`other_better`, and `needs_context` are counted as skipped.

Run a ROM-score scenario:

```powershell
python -m tools.boss_ai_debugger simulate --builtin all_equal_late
```

This simulator is for source review, not player-facing UX. It models the real
ROM direction: lower scores are better, scores 80+ are blocked, negative
lookahead deltas encourage, and `BossAI_SelectMove` rolls only between the best
and second-best slots.

Batch-check scenarios against policy expectations:

```powershell
python -m tools.boss_ai_debugger batch-simulate --scenarios scenarios.jsonl --limit 20
```

Each scenario may include an `expectation` or `expected_policy` object with
`best_action_ids`, `acceptable_action_ids`, `bad_action_ids`,
`catastrophic_action_ids`, `policy_tags`, `condition_tags`, `confidence`, and
`evidence_refs`. It also preserves `lesson_type`, `why`, and
`answer_changing_information` in the ranked output so policy checks stay tied to
the mastery notes instead of relying on memory. The batch report ranks
reviewable disagreements first so human/agent attention goes to the
highest-value checks.

Replay captured ROM selector traces:

```powershell
python -m tools.boss_ai_debugger trace-replay --trace-dir audit\boss_ai_trace --glob "*_live.txt"
```

`trace-replay` validates captured `wEnemyMonMoves`, `wEnemyAIMoveScores`,
`wBossAITier`, and chosen move bytes against the Python
`BossAI_SelectMove` replay. The exact replay gate is:

```powershell
python tools\audit\check_boss_ai_selector_replay.py
```

That gate requires exact score-byte captures, not just older top-three trace
summaries.

The full pre-choice ROM replay gate is:

```powershell
python tools\audit\check_boss_ai_pre_choice_replay.py
```

That gate reloads each real-trainer `pre_choice_state`, advances the trace ROM
through the move-choice input, compares the replayed trace fields against the
baseline `audit/boss_ai_trace/*_live.txt` file, and requires at least 99.99%
selector agreement.
