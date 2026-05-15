# Boss AI Debugger

Phase-1 debugger for BOSSAI-003.

Long-term implementation plan:
`docs/boss_ai_debugger_state_of_art_implementation_plan_2026-05-15.md`.

This started as a fixture-backed review aid. It still uses the BOSSAI-004
public-info fixtures and labels as the decision corpus, but it can now also
run the trace ROM through PyBoy hooks to capture score-helper contribution
events from live boss-route execution.

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

Run the current differential report:

```powershell
python -m tools.boss_ai_debugger diff --scenarios audit\boss_ai_debugger\generated\spikes_spin.jsonl --trace-dir audit\boss_ai_trace
```

`diff` combines generated policy mismatches and exact selector trace replay
mismatches into one mismatch schema. ROM score-helper deltas are available from
`rom-contribution-trace`; `diff` summarizes those artifacts and, when matching
Python contribution traces are supplied or generated from scenarios, emits
`rule_delta_mismatch`, `missing_python_rule`, and `missing_rom_rule`.

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

The rule map gives source labels stable semantic ids for ROM contribution
traces. `rule-map check` compares the stored artifact with current source labels,
classifications, public-read hints, and source hashes.

Generate high-throughput scenario corpora:

```powershell
python -m tools.boss_ai_debugger generate --family spikes_spin --count 10000 --seed 1 --out audit\boss_ai_debugger\generated\spikes_spin.jsonl
python -m tools.boss_ai_debugger generate --family mastery_policy --count 800 --seed 1 --out audit\boss_ai_debugger\generated\mastery_policy.jsonl
python -m tools.boss_ai_debugger batch-simulate --scenarios audit\boss_ai_debugger\generated\spikes_spin.jsonl --limit 50
```

Generated scenarios are deterministic by seed and include policy expectations,
condition tags, evidence refs, answer-changing information, trace ROM/symbol
hashes, and a stable `state_hash` so batch output can be used as a review queue
rather than raw simulation spam. The
`mastery_policy` family keeps at least one generated scenario tied to every
active policy card so coverage reports expose decision-review blind spots.

Build a compact review queue from generated scenarios or a saved batch report:

```powershell
python -m tools.boss_ai_debugger review-queue --scenarios audit\boss_ai_debugger\generated\spikes_spin.jsonl --limit 50
python -m tools.boss_ai_debugger review-queue --report audit\boss_ai_debugger\runs\spikes_spin_batch.json --json-out audit\boss_ai_debugger\runs\spikes_spin_queue.json
```

The queue re-ranks reviewable mismatches by severity, bad-roll risk, policy
tags, condition novelty, and answer-changing information. It also attaches a
compact mastery policy digest and a `next_action` hint to each item, and
`--max-per-lesson` diversifies the first pass before filling any remaining
slots with duplicates.

Record a reproducible generated smoke run:

```powershell
python -m tools.boss_ai_debugger run-suite --profile generated-smoke --count 200 --seed 1
```

The run suite writes scenarios, batch report, review queue, metadata, artifact
hashes, and a Markdown summary under `audit\boss_ai_debugger\runs\`.

Run the local changed-AI adaptation suite:

```powershell
python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 200 --seed 1
python -m tools.boss_ai_debugger run-suite --profile changed-ai --refresh-rom-contribution-trace
python -m tools.boss_ai_debugger run-suite --profile changed-ai --refresh-rom-score-materialization
python -m tools.boss_ai_debugger run-suite --profile changed-ai --rebuild-roms --refresh-live-traces
```

This profile records generated stress results, review queue, route evaluation,
metamorphic checks, scorer mutation results, candidate invariants, selector
trace replay when traces are available, rule-map drift, artifact hashes, and
known gaps. It also writes `previous_run_diff.json` to compare changed-AI
metrics, artifact hashes, and changed-file sets against the latest older
changed-AI run in the same run store. It does not rebuild ROMs or refresh
`rom-contribution-trace` output itself, but it ingests the existing
`audit\boss_ai_debugger\rom_contribution_trace_smoke.json` artifact when it is
present and records a summary plus copied artifact hashes in the run directory.
With `--refresh-rom-contribution-trace`, it drives one boss route and stores a
fresh ROM contribution artifact in that run instead of copying the existing
smoke artifact. With `--refresh-rom-score-materialization`, it also
materializes a targeted generated Spikes/Rapid Spin score batch before ROM
scoring and stores the matched ROM/Python contribution comparison.
With `--rebuild-roms` and `--refresh-live-traces`, it also records command
artifacts for the ROM rebuild and live trace refresh steps; without those flags
the artifacts are present as explicit skipped reports.

Run the foundation audit:

```powershell
python tools\audit\check_boss_ai_debugger_foundations.py
python tools\audit\check_boss_ai_debugger_performance.py
python tools\audit\check_boss_ai_debugger_roadmap.py --allow-incomplete
```

This checks current fixture/trace schema validity, stored rule-map freshness,
generated scenario evaluation, and review-queue accounting. The performance
audit makes the simulation/review bottleneck explicit: generated scenario
evaluation must stay above `10000/min`, reviewable checks above `1000/min`, and
the top review queue must stay below 10% avoidable duplicate lesson spam.
The roadmap audit is the readiness gate for the full state-of-the-art plan. It
is expected to report `ready=False` until ROM-materialized generated scenarios,
full predicate/read provenance, reachable rule coverage, and the final
performance targets are proven.

Run the combined definition-of-done gate:

```powershell
python tools\audit\check_boss_ai_debugger_done.py
```

The done gate runs debugger tests, no-cheat/gating/trace invariants, live
capture ledger, exact selector replay, pre-choice replay, foundation and
performance audits, changed-AI rebuild/live-trace suite, docs navigation, and
the roadmap audit with ROM selector and score materialization enabled. It writes
`.local\tmp\boss_ai_debugger\done_gate.json` and exits nonzero until every
roadmap blocker is actually closed.

Use `--skip-changed-ai-suite` only when intentionally avoiding the expensive
ROM rebuild and live trace refresh pass.

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
python -m tools.boss_ai_debugger coverage-report --changed-file engine\battle\ai\boss_policy_move.asm
```

The mastery index parses policy cards, quick tests, reviews, and the
source-to-policy ledger. The coverage report shows mapped Boss AI rules,
generated scenario tag coverage, policy-card evidence coverage, and explicitly
aggregates score-helper rule ids from available ROM contribution trace
artifacts. It distinguishes executable hook targets from static data labels,
tracks score-trace target coverage separately from score-delta coverage, and
emits grouped coverage-target worklists with suggested generator families and
trace modes for targeted Boss AI edits.

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

Render a Python scenario decision trace:

```powershell
python -m tools.boss_ai_debugger decision-trace --scenario audit\boss_ai_debugger\generated\spikes_spin.jsonl --scenario-id generated_spikes_spin_1_00001
```

`decision-trace` emits structured events for state load, candidates, score-rule
contributions, selector output, and policy check. It is the Python scenario
waterfall format.

Write a normalized Python contribution stream for ROM/Python comparison:

```powershell
python -m tools.boss_ai_debugger python-contribution-trace --scenarios scenarios.jsonl --json-out audit\boss_ai_debugger\python_contribution_trace.json
```

`python-contribution-trace` adapts scenario score events into the same
candidate/rule/delta shape as ROM contribution traces. Only explicitly mapped
ROM-mirror rules, such as lookahead, should be treated as ROM-accuracy claims.

Capture a ROM contribution trace from an existing boss route:

```powershell
python -m tools.boss_ai_debugger rom-contribution-trace --boss-route clair --json-out audit\boss_ai_debugger\rom_contribution_trace_smoke.json
python -m tools.boss_ai_debugger rom-contribution-trace --boss-route koga --patch-symbol wPlayerScreens=0x01 --patch-symbol wPlayerUsedMoves=0xe5 --json-out audit\boss_ai_debugger\rom_contribution_trace_spikes_spin_probe.json
```

`rom-contribution-trace` installs PyBoy execution hooks on trace-ROM Boss AI
source labels and score mutation helpers, then drives the existing real
map/script boss route until the first move choice. It records candidate slot,
source rule id, score before/after, signed delta, helper operation, callsite,
dynamic rule-label entries, and the pinned trace ROM/symbol hashes. Score
events and rule entries are separate: a rule entry proves the label executed,
while a score event proves a score mutation. Selected public-info branch labels
are recorded as predicate branch entries; they explain concrete branch outcomes
such as Spikes layer count or Rapid Spin hazard-risk paths. Configured
public-read probes record compact snapshots of declared legal inputs, including
byte ranges such as `wPlayerUsedMoves`, structured party HP slots for reserve
Ghost checks, and static ROM table references for learnset/base-data
dependencies. These are PyBoy execution hooks with snapshots, not CPU
memory-read watchpoints. `--patch-symbol SYMBOL=VALUE` can apply byte patches at
replay start and before the first scored candidate, which is useful for one-off
ROM probes like `--patch-symbol wPlayerScreens=0x01`. Save-state mode also
exists, but it only captures score events if the supplied state is before
scoring; the existing `pre_choice_state` files are already after move scoring
and mainly exercise the selector.

Materialize generated final score bytes into the trace ROM selector:

```powershell
python -m tools.boss_ai_debugger rom-selector-materialize --scenarios audit\boss_ai_debugger\generated\selector_edges.jsonl --limit 20
```

`rom-selector-materialize` loads a real pre-choice trace state, hooks
`BossAI_SelectMove.first_pass`, patches the generated scenario's final
post-score move ids and score bytes into WRAM, and then lets the ROM selector
choose. This is an honest ROM-backed selector check for generated cases, but it
is not full battle-state or score-model materialization.

Materialize generated score-model state before ROM scoring:

```powershell
python -m tools.boss_ai_debugger generate --family spikes_spin --count 12 --seed 1 --out .local\tmp\boss_ai_debugger\spikes_score_materialize.jsonl
python -m tools.boss_ai_debugger rom-score-materialize --scenarios .local\tmp\boss_ai_debugger\spikes_score_materialize.jsonl --limit 4
python -m tools.boss_ai_debugger rom-score-materialize --scenarios .local\tmp\boss_ai_debugger\spikes_score_materialize.jsonl --limit 4 --compare-fast-score
python -m tools.boss_ai_debugger rom-score-materialize --scenarios .local\tmp\boss_ai_debugger\spikes_score_materialize.jsonl --limit 200 --fast-score-only --workers 4
```

`rom-score-materialize` loads Koga's real pre-choice trace state, patches a
generated Spikes/Rapid Spin scenario into public WRAM before
`BossAI_ApplyMoveModel.ScoreMove`, and captures the resulting ROM contribution
trace under the generated scenario id. It patches concrete move ids, tier/weight
row, score bytes, Spikes layers, active revealed Rapid Spin, Ghost/Foresight
spinblock state, reserve Ghost availability, bench revealed Spin memory, and
active species Spin priors. The output also compares ROM score-helper
contributions against the Python scenario contribution stream with matching
trace ids, so mismatches become review items instead of hand inspection.
`--fast-score-only` reuses the same ROM state patching path but skips
score-helper hooks; use it for high-throughput ROM answer checks, then rerun
interesting failures without that flag for rule-level contribution traces. If
the hook-heavy contribution run disagrees with the fast score-only run, treat
the fast run as the behavior check and the contribution run as diagnostic
evidence that needs localization. `--compare-fast-score` runs both paths for
the same scenarios and reports hook-equivalence mismatches explicitly. Fast mode
can shard cases across `--workers` independent PyBoy sessions for the
high-throughput ROM-backed replay gate.

Classify route context:

```powershell
python -m tools.boss_ai_debugger route-eval --scenario audit\boss_ai_debugger\generated\spikes_spin.jsonl --horizon 3
```

`route-eval` maps scenario verdicts into structured route outcomes such as
`route_bad_roll`, `route_expected_unreachable`, or
`route_acceptable_but_review`, plus coarse buckets for `actually_bad`,
`acceptable_near_tie`, and `needs_context`. It also adds a bounded 2-5 turn
route projection over candidate moves, with explicit factors for hazards, Rapid
Spin, phazing, sleep, recovery, self-KO, and ace preservation. This is an
analysis layer for review prioritization, not a claim that the ROM is doing
multi-turn tree search.
