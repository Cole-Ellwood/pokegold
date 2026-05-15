# Boss AI Debugger

Phase-1 debugger for BOSSAI-003.

Long-term implementation plan:
`docs/boss_ai_debugger_state_of_art_implementation_plan_2026-05-15.md`.

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

Validate canonical state inputs:

```powershell
python -m tools.boss_ai_debugger state-schema validate
python -m tools.boss_ai_debugger state-schema validate --fixtures --trace-dir audit\boss_ai_trace
```

`state-schema validate` checks the current preference fixtures and live trace
captures by default. It rejects hidden/private fields in public-only scenario
data, and it verifies the trace fields needed for exact selector replay.

Build and check the Boss AI rule map:

```powershell
python -m tools.boss_ai_debugger rule-map build --json-out audit\boss_ai_debugger\rule_map.json
python -m tools.boss_ai_debugger rule-map check
```

The rule map gives source labels stable semantic ids for later full scoring
traces. `rule-map check` compares the stored artifact with current source labels,
classifications, public-read hints, and source hashes.

Generate high-throughput scenario corpora:

```powershell
python -m tools.boss_ai_debugger generate --family spikes_spin --count 10000 --seed 1 --out audit\boss_ai_debugger\generated\spikes_spin.jsonl
python -m tools.boss_ai_debugger batch-simulate --scenarios audit\boss_ai_debugger\generated\spikes_spin.jsonl --limit 50
```

Generated scenarios are deterministic by seed and include policy expectations,
condition tags, evidence refs, and answer-changing information so batch output
can be used as a review queue rather than raw simulation spam.

Build a compact review queue from generated scenarios or a saved batch report:

```powershell
python -m tools.boss_ai_debugger review-queue --scenarios audit\boss_ai_debugger\generated\spikes_spin.jsonl --limit 50
python -m tools.boss_ai_debugger review-queue --report audit\boss_ai_debugger\runs\spikes_spin_batch.json --json-out audit\boss_ai_debugger\runs\spikes_spin_queue.json
```

The queue re-ranks reviewable mismatches by severity, bad-roll risk, policy
tags, condition novelty, and answer-changing information.

Record a reproducible generated smoke run:

```powershell
python -m tools.boss_ai_debugger run-suite --profile generated-smoke --count 200 --seed 1
```

The run suite writes scenarios, batch report, review queue, metadata, artifact
hashes, and a Markdown summary under `audit\boss_ai_debugger\runs\`.

Run the foundation audit:

```powershell
python tools\audit\check_boss_ai_debugger_foundations.py
```

This checks current fixture/trace schema validity, stored rule-map freshness,
generated scenario evaluation, and review-queue accounting.

Run metamorphic checks:

```powershell
python -m tools.boss_ai_debugger metamorphic --generated 100 --seed 1 --fail-on-mismatch
```

The metamorphic suite checks selector invariants and Spikes/Rapid Spin boundary
relations that should hold without needing a hand label for every generated
state.

Build mastery and coverage indexes:

```powershell
python -m tools.boss_ai_debugger mastery-index build
python -m tools.boss_ai_debugger coverage-report --generated-count 250 --seed 1
```

The mastery index parses policy cards, quick tests, reviews, and the
source-to-policy ledger. The coverage report shows mapped Boss AI rules,
generated scenario tag coverage, policy-card evidence coverage, and explicitly
flags that full ROM scoring trace coverage is not implemented yet.

Run scorer mutation tests:

```powershell
python -m tools.boss_ai_debugger mutate --target scorer --json-out audit\boss_ai_debugger\mutation_report.json
```

The mutation runner wraps the Python scorer in memory and reuses the strict
pairwise preference regression. It reports killed, survived, and not-exercised
mutants so missing label coverage is visible instead of being mistaken for
correctness.

Mine candidate invariants:

```powershell
python -m tools.boss_ai_debugger invariants mine --scenarios audit\boss_ai_debugger\generated\spikes_spin.jsonl --trace-dir audit\boss_ai_trace --runs-dir audit\boss_ai_debugger\runs
```

`invariants mine` emits candidate selector/scenario/run-store invariants with
support counts and violations. These are hypotheses until promoted to a
dedicated audit.

Analyze a mismatch:

```powershell
python -m tools.boss_ai_debugger counterfactual --scenario audit\boss_ai_debugger\generated\spikes_spin.jsonl --scenario-id generated_spikes_spin_1_00001
python -m tools.boss_ai_debugger minimize --scenario audit\boss_ai_debugger\generated\spikes_spin.jsonl --scenario-id generated_spikes_spin_1_00001
python -m tools.boss_ai_debugger localize --scenarios audit\boss_ai_debugger\generated\spikes_spin.jsonl
```

`counterfactual` reports the smallest score movement and public fact changes
that would flip the answer, `minimize` removes nonessential fields/actions while
preserving the verdict, and `localize` ranks overrepresented tags and move-delta
rules in reviewable batches.

Classify one-turn route context:

```powershell
python -m tools.boss_ai_debugger route-eval --scenario audit\boss_ai_debugger\generated\spikes_spin.jsonl
```

`route-eval` maps scenario verdicts into structured route outcomes such as
`route_bad_roll`, `route_expected_unreachable`, or
`route_acceptable_but_review`, plus coarse buckets for `actually_bad`,
`acceptable_near_tie`, and `needs_context`. It is a foundation for route review,
not full multi-turn search yet.
