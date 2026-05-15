# Boss AI Debugger State-Of-The-Art Implementation Plan

Status: implementation plan. Created 2026-05-15.

Purpose: turn `tools/boss_ai_debugger/` from a useful Phase-1 review aid into
the main engineering instrument for Boss AI behavior: ROM-accurate, fast enough
to search huge state spaces, grounded in mastery notes, and able to explain
which public facts and scoring branches caused each decision.

This plan is intentionally ambitious. If fully implemented, I should not feel
like any major debugger, validation, or review capability is missing.

## Verdict

The previous roadmap had the correct core: deterministic replay, full scoring
trace, generative differential testing, counterfactual explanation, active
review ranking, multi-turn route evaluation, and a columnar results store.

The plan was not complete enough to call state of the art. It missed five
capabilities that matter for a debugger meant to survive constant AI edits:

- Dynamic invariant mining from successful and failing ROM traces.
- Mutation testing of scoring rules, fixtures, labels, and audits.
- Statistical and causal fault localization across millions of generated
  cases.
- Provenance and program-slicing views from score byte back to source label and
  public memory read.
- Experiment lineage for runs, seeds, ROM hashes, source commits, generated
  corpora, and review outcomes.

With those added, the target architecture is state of the art for this project:
it combines record/replay debugging, property/stateful testing, differential
testing, coverage-guided fuzzing, metamorphic testing, counterfactual
explanations, active learning, invariant mining, mutation testing, and
experiment tracking into one Boss AI-specific workflow.

## Current Ground Truth

Existing local capabilities:

- `tools/boss_ai_debugger/` provides fixture inspection, preference regression,
  score-byte selector replay, and ROM-score scenario simulation.
- `tools/trace/` provides PyBoy-backed trace capture, state factory, state
  probing, batch capture, and pre-choice replay plumbing.
- `audit/boss_ai_trace/` stores live captures, manifest, ledger, and selector
  replay report.
- `tools/boss_ai_preference/` stores the preference corpus, Coach Mode labels,
  feature extraction, active queue, trajectory data, reward-model reports, and
  proposal generation.
- `docs/pokemon_mastery/` stores policy cards, quick tests, reviews, route
  sheets, and the source-to-policy ledger.

Known gap: the debugger can prove selector replay from final score bytes, but
it cannot yet reconstruct full ROM scoring branch-by-branch. It also cannot
automatically rank one million generated disagreements by "worth my attention"
with enough context to prevent repeated reasoning mistakes.

## Design Principles

1. ROM behavior is the behavioral source of truth.
2. Public-info legality is a first-class data field, not prose.
3. Python mirrors are allowed only when they are continuously checked against
   ROM traces.
4. Every generated scenario must carry source, seed, ROM hash, symbol hash, and
   state hash.
5. Every mismatch should produce a minimized repro and a ranked reason to care.
6. Review time is scarcer than CPU time.
7. Outputs must be readable enough to become asm, fixture, or audit changes.
8. No opaque policy blob may become ROM behavior.

## Target User Stories

- Given a live save state, show every move and switch candidate, every score
  contribution, final score bytes, selector probability, and chosen move.
- Given a policy question such as "third-layer Spikes into revealed spinner",
  generate thousands of legal public-info variants and show the top mismatches.
- Given a mismatch, minimize it to the smallest state and smallest public fact
  change that preserves the mismatch.
- Given a Boss AI asm edit, automatically rebuild, refresh traces, compare
  rule coverage, and show which behavior changed.
- Given a mastery lesson, generate positive and negative scenarios until the
  ROM either satisfies it or produces ranked counterexamples.
- Given a suspicious score, slice back to the rule label, trace event, source
  lines, WRAM symbols read, and public-info justification.

## Architecture

### 1. Canonical State Schema

Create `tools/boss_ai_debugger/state_schema.py` and
`docs/boss_ai_debugger_state_schema.md`.

The schema must represent:

- ROM identity: `rom`, `rom_sha256`, `symbols`, `symbols_sha256`, git commit.
- Scenario identity: `scenario_id`, `seed`, `generator`, `state_hash`.
- Public boundary: `public`, `known_to_boss`, `hidden`, `haki_exception`.
- Battle state: active mons, HP bands/exact where legal, status, stat stages,
  types, abilities/passives, items if public, hazards, weather, turns elapsed,
  switch history, perish counters, revealed moves, seen species, bench memory.
- Boss candidates: moves, switches, items, legality, disabled/encored/trapped
  gates, source labels.
- Expectations: best/acceptable/bad/catastrophic action ids, policy tags,
  confidence, lesson ids, evidence refs, answer-changing information.

Acceptance:

- All fixture, trace, generated scenario, and mastery quick-test imports can
  round-trip through the schema.
- Schema validation rejects hidden-info fields used in public-only scoring.

### 2. Rule Id And Source Map

Create `tools/boss_ai_debugger/rule_map.py`.

Generate a stable map from asm labels and comments to rule ids:

```text
boss_policy_move.asm:.ApplyRevealedRapidSpinSpikesRisk
  rule_id=move.spikes.public_rapid_spin_risk
  source_file=engine/battle/ai/boss_policy_move.asm
  source_label=.ApplyRevealedRapidSpinSpikesRisk
  public_reads=wPlayerUsedMoves,wPlayerMonSpecies,wPlayerSubStatus...
```

Rules:

- Rule ids are semantic and stable across line shifts.
- Generated docs may include line numbers, but stored traces use rule ids.
- Rule ids must include public-info class, Haki exception class, or platform
  boundary class.

Acceptance:

- `python -m tools.boss_ai_debugger rule-map --check` fails if traced labels,
  invariant audit labels, or source labels drift without a map update.

### 3. Full ROM Scoring Contribution Trace

Extend the trace ROM to emit scoring events, not only final bytes.

Each event should capture:

- candidate kind: move/switch/item
- candidate slot
- rule id
- score before
- score after
- signed delta or tier-weight operation
- predicate outcome
- public evidence bits read
- source label id

Use a compact ring buffer in trace builds only. Normal ROM must remain
unchanged except for behavior itself.

Acceptance:

- A single traced decision can be rendered as a full contribution table.
- Existing exact selector replay remains `100%`.
- Trace WRAM budget remains inside the accepted trace-only budget or the memory
  audit is explicitly updated with a reviewed budget.

### 4. ROM/Python Differential Runner

Create `tools/boss_ai_debugger/differential.py`.

For each scenario:

1. Materialize into a trace ROM state where possible.
2. Capture full ROM scoring trace.
3. Run Python mirror scoring.
4. Compare candidate legality, rule ids, score deltas, final scores, selector
   probabilities, and chosen move surface.
5. Emit a mismatch object with severity and minimization seed.

Mismatch classes:

- `selector_mismatch`
- `score_byte_mismatch`
- `rule_delta_mismatch`
- `missing_python_rule`
- `missing_rom_rule`
- `public_boundary_violation`
- `policy_preference_mismatch`
- `trace_incomplete`

Acceptance:

- Current live trace corpus has no selector mismatches.
- Python mirror can lag ROM, but lag is explicit: every missing rule has a
  tracked owner and failing coverage case.

### 5. Scenario Generators

Create `tools/boss_ai_debugger/generators/`.

Generators:

- `boundary_matrix`: cartesian edge cases for one rule family.
- `coverage_guided`: mutates states to hit new rule ids.
- `stateful_public_info`: Hypothesis-style action sequences: reveal move,
  switch, set hazard, spin, phaze, sleep, wake, explode, recover, trap.
- `mastery_replay`: converts policy cards and quick tests into structured
  scenario families.
- `live_trace_mutator`: starts from captured pre-choice states and mutates only
  public, legal dimensions.
- `leader_personality`: preserves leader/team context while varying state.

Acceptance:

- `python -m tools.boss_ai_debugger generate --family spikes_spin --count 10000`
  writes deterministic JSONL with seeds.
- Generators can target a rule id and report coverage hit rate.

### 6. Coverage System

Create `tools/boss_ai_debugger/coverage.py`.

Track:

- rule-id coverage
- branch predicate coverage
- source label coverage
- public-info field coverage
- leader/tier/personality coverage
- mastery policy-card coverage
- scenario-generator coverage
- mutation-kill coverage

Acceptance:

- `coverage-report` shows uncovered rules and the generator most likely to hit
  each one.
- Release gate can require no regression in rule coverage for touched files.

### 7. Metamorphic Testing

Create `tools/boss_ai_debugger/metamorphic.py`.

Relations:

- Hidden player move changes must not affect public-only decisions.
- Reordering hidden bench data must not affect active public decisions.
- Revealed move transfer must stay species-scoped.
- Adding unrevealed Rapid Spin must not trigger revealed-spinner behavior.
- Revealed Rapid Spin plus no spinblock should discourage extra layers.
- Revealed Rapid Spin plus active non-Foresighted Ghost should soften panic.
- Fully blocked moves must remain unselectable regardless of deltas.
- Third and fourth selectable slots must not receive selector probability when
  best/second are present.
- Equivalent score deltas applied through different rule orderings must produce
  the same final selector surface when rules commute.

Acceptance:

- `python -m tools.boss_ai_debugger metamorphic --generated N` produces zero
  hidden-info leaks on the current ROM.

### 8. Mutation Testing

Create `tools/boss_ai_debugger/mutation.py`.

Mutate:

- Python scoring signs and thresholds.
- Scenario expectations.
- Rule-map public/hidden classifications.
- Trace parser fields.
- Invariant audit patterns.
- Selected asm compare constants in a sandbox build.

Goal: prove tests fail when the meaningful bug is inserted.

Acceptance:

- Mutation report lists killed/survived mutants.
- Surviving high-severity mutants create TODO fixtures or audit tasks.
- Do not run full mutation testing by default in release smoke; use targeted
  mutation tests for high-risk rule families.

### 9. Dynamic Invariant Mining

Create `tools/boss_ai_debugger/invariants.py`.

Mine likely invariants from passing traces:

- score ranges by rule family
- rule ordering constraints
- "if rule A fires, public field B must be set"
- "if score >= 80, selector probability is zero"
- public-read sets per rule id
- leader/tier-specific selector threshold patterns
- trace buffer completeness

Acceptance:

- Invariants are emitted as candidate audit rules, not auto-accepted.
- A reviewed invariant can become a static or trace audit.

### 10. Statistical And Causal Fault Localization

Create `tools/boss_ai_debugger/localize.py`.

Across large generated batches, correlate failures with:

- rule ids
- public fields
- leader/tier
- source labels
- scenario generators
- recent commits
- mastery tags

Then run interventions:

- disable one Python mirror rule
- flip one public fact
- clamp one score contribution
- remove one candidate
- replace one state transition

Acceptance:

- Mismatch reports include "most likely responsible rule ids" and supporting
  evidence.
- Causal claims must be labeled as `confirmed`, `likely`, or `hypothesis`.

### 11. Counterfactual Explainer

Create `tools/boss_ai_debugger/counterfactuals.py` or extend the existing
preference counterfactual module with debugger-native state support.

For each mismatch, compute:

- smallest score delta that flips selector top action
- smallest public fact change that flips ROM behavior
- smallest public fact change that flips preference model judgment
- nearest passing scenario
- nearest failing scenario

Acceptance:

- Every high-severity mismatch includes `answer_changing_information`.

### 12. Delta Minimizer

Create `tools/boss_ai_debugger/minimize.py`.

Minimize:

- scenario fields
- action sequences
- revealed-move histories
- bench lists
- rule-event traces
- source diffs when comparing commits

Acceptance:

- Any generated mismatch can be reduced to a compact repro JSON and optional
  `.state` file.

### 13. Active Review Queue

Create `tools/boss_ai_debugger/review_queue.py`.

Rank by:

- catastrophic bad-roll probability
- expected score or policy improvement
- novelty by rule coverage
- uncertainty / small top-two margin
- disagreement with preference model
- conflict with mastery policy card
- similarity to recent user corrections
- minimization quality
- ease of turning into asm/audit change

Acceptance:

- `python -m tools.boss_ai_debugger review-queue --from results.parquet --limit 50`
  shows only high-value cases and explains why each is worth reviewing.

### 14. Mastery Memory Integration

Create `tools/boss_ai_debugger/mastery_index.py`.

Index:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/policy_cards/*.md`
- `docs/pokemon_mastery/quick_tests/*.md`
- `docs/pokemon_mastery/reviews/*.md`
- route sheets and boss route maps

Convert each lesson into:

- trigger predicates
- preferred actions
- bad actions
- exceptions
- worst branch
- evidence refs
- confidence

Acceptance:

- Scenario reports cite mastery evidence by file path.
- A policy card with no generated positive and negative coverage is reported as
  missing coverage.

### 15. Multi-Turn Route Evaluator

Create `tools/boss_ai_debugger/route_eval.py`.

Evaluate 2-5 turn plans with exact local mechanics where possible:

- hazards and spin retention
- phazing and setup denial
- sleep-clause material
- self-KO trade timing
- recovery loops
- perish/trap routes
- revenge priority
- ace preservation

Use shallow search first. MCTS-style search is allowed for hard positions, but
the output must be symbolic: "plan survives these branches and loses these
branches."

Acceptance:

- One-turn ROM mismatches can be classified as actually bad, acceptable
  near-tie, or needs longer-route context.

### 16. Experiment Store

Create `audit/boss_ai_debugger/runs/` plus optional Parquet/Arrow output.

Each run records:

- run id
- command
- git commit
- dirty diff hash
- ROM hashes
- generator config
- seeds
- counts
- coverage
- mismatch summary
- review queue output
- artifacts

Use a simple local format first:

- JSON metadata
- JSONL mismatch stream
- Parquet/Arrow table when dependencies are available
- Markdown summary

Acceptance:

- Any report can be reproduced from run metadata.
- Runs can be compared by commit.

### 17. Observability Event Format

Emit structured trace events compatible with common observability concepts:

- `trace_id`: scenario/run id
- `span_id`: candidate/rule event id
- `parent_span_id`: decision id
- event type: `state_load`, `score_rule`, `selector`, `policy_check`,
  `counterfactual`, `minimize`
- attributes: rule id, source label, candidate id, public reads, score delta

Acceptance:

- A single decision can be rendered as a timeline.
- Batch failures can be grouped by trace attributes.

### 18. UI And TUI

The primary user is Codex, so CLI and JSON matter most. Still add a compact TUI
or static HTML report for dense inspection.

Views:

- decision waterfall
- rule coverage heatmap
- top mismatches
- counterfactual diff
- source slice
- mastery evidence pane
- run comparison

Acceptance:

- No required interaction for batch work.
- Static report can be opened after a long run without rerunning emulation.

## Performance Plan

Targets:

- Pure selector replay: at least 1,000,000 decisions/minute.
- Python scenario scoring: at least 5,000,000 decisions/minute.
- Generated expectation checks: at least 1,000,000 decisions/minute.
- ROM-backed full pre-choice replay: at least 10,000 decisions/minute.
- Stretch ROM-backed replay: 100,000 decisions/minute with emulator pooling,
  in-memory state loading, and trace-entry hooks.
- Review ranking: at least 1,000,000 generated cases/minute down to a top-50
  queue when ROM execution is not required.

Implementation tactics:

- Keep hot state in typed arrays or compact dataclasses.
- Avoid per-scenario subprocesses.
- Reuse PyBoy workers.
- Load save states from memory buffers where possible.
- Separate generation, scoring, capture, and review ranking stages.
- Use columnar output for batch analytics.
- Cache parsed symbols, move data, trainer teams, mastery predicates, and rule
  maps by content hash.

## CLI Surface

Add these subcommands under `python -m tools.boss_ai_debugger`:

```powershell
state-schema validate --path scenario.json
rule-map build --json-out audit/boss_ai_debugger/rule_map.json
rule-map check
capture-full --state path.state --json-out decision_trace.json
diff --scenarios scenarios.jsonl --rom --python --json-out run.json
generate --family spikes_spin --count 10000 --seed 1 --out scenarios.jsonl
coverage-report --runs audit/boss_ai_debugger/runs
metamorphic --scenarios scenarios.jsonl
mutate --target scorer --family spikes_spin --limit 100
invariants mine --runs audit/boss_ai_debugger/runs --out candidate_invariants.md
localize --run RUN_ID
counterfactual --scenario mismatch.json
minimize --mismatch mismatch.json --out minimized.json
review-queue --run RUN_ID --limit 50
mastery-index build
route-eval --scenario scenario.json --horizon 3
run-suite --profile changed-ai
```

## Implementation Phases

### Phase 0 - Document And Guard The Current Baseline

Deliverables:

- This plan.
- Add doc link from `tools/boss_ai_debugger/README.md`.
- Add a "do not start with UI" note: correctness and batch triage first.

Exit:

- Current debugger tests still pass.

### Phase 1 - Canonical State And Rule Map

Deliverables:

- `state_schema.py`
- `rule_map.py`
- schema docs
- importers for fixtures and trace captures

Exit:

- Current 59 fixtures and 19 live captures validate.

### Phase 2 - Full Scoring Trace

Deliverables:

- Trace ROM scoring-event ring buffer.
- Parser and renderer.
- Source-map check.

Exit:

- A live capture explains all final score bytes by rule event.

### Phase 3 - Differential Runner

Deliverables:

- ROM/Python comparison.
- Mismatch schema.
- JSON/Markdown reports.

Exit:

- Current live corpus has zero selector mismatches and known Python mirror gaps
  listed explicitly.

### Phase 4 - Generators And Coverage

Deliverables:

- Boundary, coverage-guided, stateful, mastery, and live mutator generators.
- Coverage reports.

Exit:

- Every current Boss AI rule id has at least one generated scenario or an
  explicit "unreachable / trace-only / Haki-only" reason.

### Phase 5 - Metamorphic And Mutation Testing

Deliverables:

- Metamorphic relation suite.
- Targeted mutation runner.

Exit:

- High-risk public-info rules have hidden-info leak tests and killed mutants.

### Phase 6 - Counterfactuals, Minimization, Localization

Deliverables:

- Counterfactual explainer.
- Delta minimizer.
- Statistical/causal localization.

Exit:

- High-severity mismatches produce compact repros and ranked likely causes.

### Phase 7 - Mastery And Active Review Queue

Deliverables:

- Mastery index.
- Review queue ranker.
- Coverage from policy cards to scenarios.

Exit:

- A 1,000,000-scenario non-ROM batch can be reduced to a top-50 review queue
  with evidence refs and no duplicate lesson spam.

### Phase 8 - Route Evaluation

Deliverables:

- 2-5 turn route evaluator.
- Branch summaries and route-value classification.

Exit:

- One-turn "disagreements" can be separated into bad, acceptable, or
  needs-context buckets.

### Phase 9 - Experiment Store And Reports

Deliverables:

- Run metadata.
- JSONL and optional Parquet outputs.
- Static HTML or Markdown reports.
- Run comparison.

Exit:

- Any result can be reproduced by run id.

### Phase 10 - Change-Adaptation Suite

Deliverables:

- `run-suite --profile changed-ai`
- Git diff-aware targeted generators.
- Trace refresh orchestration.
- Rule coverage diff.

Exit:

- After a Boss AI asm edit, one command identifies exact behavior changes,
  stale traces, missing Python mirror rules, and review-worthy policy changes.

## Validation Profiles

### Fast Local

```powershell
python -m compileall -q tools\boss_ai_debugger tools\trace
python -m unittest discover tools\boss_ai_debugger\tests
python -m tools.boss_ai_debugger trace-replay --trace-dir audit\boss_ai_trace --glob "*_live.txt" --fail-on-mismatch
python -m tools.boss_ai_debugger rule-map check
python -m tools.boss_ai_debugger state-schema validate --fixtures
```

### Changed AI

```powershell
wsl make pokegold.gbc pokesilver.gbc pokegold_trace.gbc
python tools\trace\boss_ai_state_factory.py --all --update-manifest
python tools\trace\boss_ai_trace_batch.py --execute
python tools\audit\check_boss_ai_selector_replay.py
python tools\audit\check_boss_ai_pre_choice_replay.py
python -m tools.boss_ai_debugger run-suite --profile changed-ai
```

### Deep Search

```powershell
python -m tools.boss_ai_debugger generate --all-families --count 1000000 --out audit/boss_ai_debugger/generated/deep.jsonl
python -m tools.boss_ai_debugger diff --scenarios audit/boss_ai_debugger/generated/deep.jsonl --python --json-out audit/boss_ai_debugger/runs/deep/run.json
python -m tools.boss_ai_debugger review-queue --run deep --limit 100
```

### ROM Accuracy Proof

```powershell
python -m tools.boss_ai_debugger diff --scenarios audit/boss_ai_debugger/generated/rom_sample.jsonl --rom --python --json-out audit/boss_ai_debugger/runs/rom_accuracy/run.json
python -m tools.boss_ai_debugger coverage-report --run rom_accuracy
python -m tools.boss_ai_debugger localize --run rom_accuracy
```

## Acceptance Metrics

Behavioral:

- Selector replay: 100% on live captures.
- Pre-choice replay: at least 99.99%, target 100%.
- Full score-byte agreement: at least 99.99% on ROM-backed generated sample,
  target 100% except documented trace limitations.
- Public-info leak rate: 0 known leaks.
- Rule coverage: 100% reachable rule ids covered.
- High-risk mutation score: at least 95% killed.

Review:

- Top-50 review queue has less than 10% duplicate lesson spam.
- Every high-severity item has a minimized repro.
- Every high-severity item has counterfactual answer-changing information.
- Every mastery policy card has positive and negative scenario coverage.

Performance:

- Non-ROM generated scenario triage: 1,000,000+/minute.
- Pure selector replay: 1,000,000+/minute.
- Python scoring: 5,000,000+/minute.
- ROM-backed decision replay: 10,000+/minute.

Maintainability:

- Every rule id maps to source.
- Every behavior-changing commit can produce a before/after behavior diff.
- Every trace artifact records ROM hash, symbols hash, source commit, and seed.

## Risks

- Full scoring trace may exceed trace WRAM. Mitigation: trace-only ring buffer,
  event compression, optional serial/log streaming, or staged trace builds by
  rule family.
- PyBoy replay may be too slow for ROM-backed stretch targets. Mitigation:
  persistent workers, memory state loading, trace-entry hooks, scenario sampling,
  and heavy use of Python mirror for broad triage.
- Python mirror may become fragile if it tries to duplicate asm manually.
  Mitigation: generated rule map, ROM differential checks, and explicit missing
  mirror rule reports.
- Mastery notes may contain contradictory lessons. Mitigation: confidence,
  condition tags, holdouts, conflict reports, and active review queue.
- Coverage-guided generation can produce illegal or uninteresting states.
  Mitigation: schema validation, legality checks, corpus minimization, and
  review ranking.

## Research Basis

- Record/replay debugging: GDB process record/replay and rr show the value of
  deterministic replay and reverse debugging for rare failures.
  <https://sourceware.org/gdb/current/onlinedocs/gdb.html/Process-Record-and-Replay.html>
  <https://rr-project.org/>
- Coverage-guided fuzzing: libFuzzer uses coverage feedback, corpus mutation,
  parallel workers, and corpus minimization.
  <https://llvm.org/docs/LibFuzzer.html>
- Stateful property testing: Hypothesis state machines generate sequences of
  actions, not just independent inputs.
  <https://hypothesis.readthedocs.io/en/latest/stateful.html>
- Differential testing: Csmith found compiler bugs by generating unusual but
  valid programs and comparing implementations.
  <https://users.cs.utah.edu/~regehr/papers/pldi11-preprint.pdf>
- Test-oracle problem: automated testing needs multiple oracle styles,
  including human, specification, differential, and metamorphic oracles.
  <https://discovery.ucl.ac.uk/id/eprint/1471263/>
- Counterfactual explanation: explain what minimal change would produce a
  desired or different result.
  <https://arxiv.org/abs/1711.00399>
- Additive feature attribution: SHAP frames per-prediction contribution
  accounting, useful as an analogy for rule contribution waterfalls.
  <https://arxiv.org/abs/1705.07874>
- Active learning: uncertainty, margin, entropy, and instance selection reduce
  labeling cost.
  <https://modal-python.readthedocs.io/en/latest/content/query_strategies/uncertainty_sampling.html>
  <https://link.springer.com/article/10.1007/s10115-012-0507-8>
- Probability calibration: predicted confidence must be checked against observed
  frequencies before it is trusted as review priority.
  <https://scikit-learn.org/stable/modules/calibration.html>
- Dynamic invariant mining: Daikon-style invariant discovery can turn passing
  traces into candidate guards.
  <https://plse.cs.washington.edu/daikon/pubs/invariants-tse2001-abstract.html>
- Statistical debugging: large sets of passing/failing runs can localize likely
  failure predictors.
  <https://pages.cs.wisc.edu/~liblit/icml-2006/>
- OpenTelemetry: traces, metrics, and logs provide a useful event model for
  decision timelines and batch observability.
  <https://opentelemetry.io/docs/>
- Experiment tracking: MLflow-style run metadata, metrics, params, artifacts,
  and searchable comparisons are the right pattern for long-running debugger
  experiments.
  <https://www.mlflow.org/docs/2.2.2/tracking.html>
- Columnar analytics: Apache Arrow's data locality, random access, and
  zero-copy-friendly format motivate a columnar result store for huge scenario
  batches.
  <https://arrow.apache.org/docs/format/Columnar.html>
- Self-play/search systems: AlphaZero is a reminder that search plus learned
  evaluation can be powerful, but for this repo it belongs in offline route
  evaluation and proposal tooling, not opaque ROM behavior.
  <https://arxiv.org/abs/1712.01815>

## Final Definition Of Done

The Boss AI debugger is complete when I can run one command after an AI edit and
get:

- exact ROM replay proof;
- full score contribution waterfalls;
- rule coverage diff;
- generated stress cases for touched logic;
- hidden-info leak checks;
- minimized mismatches;
- counterfactual explanations;
- mastery evidence refs;
- top-ranked review queue;
- behavior diff against the previous commit;
- reproducible run metadata.

At that point the bottleneck is only taste and design judgment, not tooling,
memory, or forgotten lessons.
