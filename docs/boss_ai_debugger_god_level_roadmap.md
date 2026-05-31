# Boss AI Debugger God-Level Roadmap

Status: successor roadmap. Created 2026-05-31.

Purpose: raise the Boss-AI-only debugger from "deity for supported decision
classes" to "complete for every reachable Boss AI decision class in the current
commit." This is stricter than `docs/boss_ai_debugger_deity_mode_roadmap.md`.
The previous roadmap proved that the debugger can self-drive supported Boss AI
proof packets. This roadmap removes the supported-class escape hatch.

The standard here is deliberately hard:

> For the current source commit and dirty diff, every reachable Boss AI decision
> must either be explained by a ROM-backed proof chain or make the gate fail
> with the exact missing rule, public input, state class, or materialization path.

Future source changes are not "proven forever" by old artifacts. A future
change remains God-level only if the changed-AI suite auto-discovers the new
Boss AI surface, invalidates the right proof classes, refreshes the artifacts,
and returns to zero gaps.

## Non-Negotiables

- No gameplay or ROM-policy edits are required by this roadmap.
- No generic debugger deity work belongs here.
- No LLM/API-key dependency belongs in the proof loop.
- No hand-supplied traces, scenarios, save states, materialization artifacts, or
  contribution artifacts count as God-level evidence.
- No "unsupported but green" state is allowed. Unsupported reachable behavior is
  a failing gap, not a caveat.
- No hidden-info read can be silently accepted. Legal exception surfaces must be
  named, mapped, and tested.

## Current Measured Baseline

Measured locally during the 2026-05-30 Boss AI deity completion pass:

- Boss AI deity benchmark: 8/8 passed, `boss_ai_deity_ready=True`.
- Performance audit fresh run:
  - scenario evaluation: about 1.72M cases/minute;
  - reviewable checks: about 548k/minute;
  - review queue reduction: about 1.15M reviewable inputs/minute;
  - ROM-backed score materialization: about 16.4k cases/minute with 6 workers.
- Cached previous performance report in the same tree showed scenario
  evaluation up to about 2.62M/minute and review queue reduction about
  1.42M/minute.
- A generation profile for 100k scenarios showed about 465k generated
  scenarios/minute with the current stamped JSON shape.

Hotspots observed from quick profiling:

- Generation spends most time in `deepcopy`, `Path.relative_to` display-path
  work, and per-scenario JSON hashing.
- Python scenario evaluation spends most time creating per-move objects,
  score-event structures, and full JSON-ready result packets for every case.
- Review queue spends avoidable time recomputing evidence digest/compact text
  before the top queue is known.
- ROM proof is dominated by emulator/state replay mechanics; it is already much
  slower than Python triage and must stay selective.

## Speed Strategy

The speed-first design is two-tiered:

1. Exhaust every normalized public-info Boss AI decision class in a fast
   deterministic model.
2. Use ROM-backed materialization to prove class equivalence, changed surfaces,
   and minimized witnesses, not to brute-force every duplicate raw state.

Every raw reachable Boss AI state must map to a canonical proved class. If a raw
state cannot be classified, or a class lacks ROM-backed evidence, the God gate
fails. This is the only practical way to make exhaustive Boss AI proof both
honest and fast.

Expected realistic speed gains on this machine:

- Scenario generation: 5x to 15x with lazy stamping, cached paths, immutable
  templates, and delayed hashes. Target: 2.5M to 7M generated cases/minute.
- Python scoring/evaluation: 3x to 8x with compact tuple/array evaluators and
  lazy explanation materialization. Target: 5M to 15M evaluated cases/minute.
- Review queue reduction: 5x to 20x with streaming top-K selection, cached
  evidence digests, and render-on-demand explanation text. Target: 5M to 20M
  reviewable inputs/minute.
- ROM-backed materialization in PyBoy: 3x to 8x with persistent worker pools,
  base-state grouping, snapshot reuse, hook-light fast paths, and batched
  artifacts. Target: 50k to 130k materializations/minute.
- ROM-backed materialization with a dedicated headless fast core or native
  state-fork runner: 10x to 30x is plausible, but higher risk. Target: 160k to
  500k materializations/minute if this lane is built.

The biggest effective gain is architectural: run millions of Python/model cases
per minute, then ROM-prove unique equivalence classes and changed branches. That
can produce 10x to 100x more coverage per minute than ROM-running every raw
case.

## Phase 0 - Freeze The God Target

Goal: define the new stricter measurement before expanding implementation.

Tasks:

1. Add `audit/boss_ai_debugger/god_level_benchmark/questions.jsonl`.
2. Add `tools/audit/check_boss_ai_debugger_god.py`.
3. Seed it from the current deity benchmark, then add rows that intentionally
   fail until every reachable class is covered.
4. Require every row to declare:
   - target decision surface;
   - auto driver;
   - expected public-state class id or class-discovery query;
   - required ROM proof mode;
   - required source/rule anchors;
   - required branch-signature coverage;
   - exact artifact outputs;
   - allowed skip reasons, if any.
5. Make allowed skips count as blockers unless they are impossible because the
   Boss AI surface is provably unreachable.

Acceptance:

- `python tools\audit\check_boss_ai_debugger_god.py --self-test` passes.
- `python tools\audit\check_boss_ai_debugger_god.py --baseline` records a red,
  honest baseline with explicit missing class/rule/materialization actions.
- Existing Boss AI deity gate stays green.

## Phase 1 - Performance Core First

Goal: make exhaustive search cheap enough before adding broader coverage.

Tasks:

1. Split scenario generation into:
   - compact internal scenario IR;
   - lazy JSON stamping;
   - lazy state hash;
   - render-only explanation payload.
2. Replace hot-loop `deepcopy` templates with immutable tuples or copy-on-write
   dict construction.
3. Cache trace ROM path text, symbol path text, and SHA-256 basis once per run.
4. Add a compact evaluator that can score four-move Boss AI cases without
   constructing `ScoreEvent`, `ScoredMove`, and JSON result objects unless a case
   is selected for explanation.
5. Make `evaluate_batch` optionally stream verdict summaries instead of
   returning all rendered verdict JSON.
6. Make review queue selection streaming top-K with render-on-demand evidence
   digests after the queue is selected.
7. Add `tools/audit/check_boss_ai_debugger_speed_targets.py` with explicit
   targets and a local machine report.

Acceptance targets:

- Generate at least 2.5M compact cases/minute.
- Evaluate at least 5M compact cases/minute.
- Reduce at least 5M reviewable inputs/minute to a top queue.
- Preserve exact current rendered packet output for selected cases.
- Existing unit tests and deity gate pass.

Stretch targets:

- 7M generated cases/minute.
- 15M evaluated cases/minute.
- 20M reviewable inputs/minute.

## Phase 2 - Boss AI Universe Extractor

Goal: stop relying on a human-maintained list of Boss AI behavior.

Tasks:

1. Build a static extractor over Boss AI assembly and symbols that enumerates:
   - Boss AI entrypoints;
   - score mutators;
   - switch proposal/dispatch paths;
   - public predicate branches;
   - hidden-info reads;
   - rule labels without semantic ids;
   - branch labels without dynamic evidence.
2. Connect the extractor to `rule-map build` so newly discovered labels fail
   closed until classified.
3. Add source-range ownership so every extracted Boss AI label points to an
   exact source file and line.
4. Distinguish unreachable/dead labels from reachable unproven labels using
   explicit evidence, not omission.

Acceptance:

- `check_boss_ai_debugger_god.py` reports zero unowned reachable Boss AI labels
  before any benchmark row can pass.
- Adding a new Boss AI branch without a rule id makes the God gate fail.

## Phase 3 - Canonical Public-State Classes

Goal: map every raw reachable Boss AI decision input to a normalized public-info
class.

Tasks:

1. Define canonical class fields for move scoring:
   - boss tier;
   - move ids/effects/types/power/accuracy/public PP facts where relevant;
   - public HP bands and KO bands;
   - known statuses/substatuses;
   - public hazards/screens/weather;
   - revealed moves and known role memory;
   - public species/type information;
   - switch cooldown/lockout facts;
   - route plan/confidence facts;
   - legal Haki/exception facts, if any.
2. Define canonical class fields for switch/sack dispatch:
   - public party HP bands;
   - known roles/jobs;
   - public matchup bands;
   - known hazards and entry cost bands;
   - trapped/forced/safe-switch predicates;
   - sacrifice and converter predicates.
3. Add a canonicalizer that consumes live traces, generated scenarios, and
   materialized ROM states and emits stable class ids.
4. Add an audit proving every live Boss AI trace decision has a class id.
5. Add a raw-state classifier that fails if any decision input uses a public
   fact not present in the class schema.

Acceptance:

- Every current live trace decision maps to a canonical class id.
- Every generator emits a canonical class id before scoring.
- Every ROM materialization report records the class id it proves.

## Phase 4 - Exhaustive Class Generator

Goal: cover the full finite Boss AI behavior space, not just curated examples.

Tasks:

1. Build domain enumerators for each canonical field.
2. Use pairwise and boundary generation for huge cross products, but require
   full enumeration for small rule-local domains.
3. For each rule id, generate:
   - positive witness classes;
   - negative witness classes;
   - boundary witness classes;
   - public-read provenance witnesses;
   - counterfactual flip witnesses.
4. Record why a domain is finite, bounded, reduced, or symbolic.
5. Add minimization so every failing class reduces to the smallest equivalent
   class that still flips the decision.

Acceptance:

- Every reachable rule id has positive, negative, and boundary witnesses or an
  explicit unreachable proof.
- Every public predicate branch has both taken and not-taken witness classes
  where both are reachable.
- Coverage reports count classes, not just examples.

## Phase 5 - Exact Fast Mirror

Goal: make the fast model complete enough to exhaust classes at high speed.

Tasks:

1. Convert the current Python scoring mirror into a compact exact mirror over
   canonical classes.
2. Keep a rule-by-rule explanation ledger from compact scoring back to semantic
   rule ids.
3. Add switch-dispatch exact mirror support equal to move-score support.
4. Generate or verify mirror rule tables from rule-map/source anchors so assembly
   changes cannot silently drift from Python.
5. Make every mirror mismatch produce:
   - class id;
   - ROM evidence path;
   - Python rule ledger;
   - source label;
   - minimized counterfactual.

Acceptance:

- The compact mirror can evaluate at least 5M classes/minute.
- All current exact materialization families match ROM.
- Any missing mirror rule fails the God gate.

## Phase 6 - ROM Proof Accelerator

Goal: make ROM-backed evidence fast enough for class-level proof refresh.

Tasks:

1. Keep persistent PyBoy workers alive across batches.
2. Group materialization by base route/state and patch shape.
3. Cache loaded base save-state bytes and post-navigation snapshots.
4. Add a hook-light branch-signature mode separate from full contribution
   tracing.
5. Batch artifact writes and write full contribution JSON only for selected
   class witnesses.
6. Add worker health checks and deterministic retry-once semantics.
7. Investigate a dedicated headless fast core only after PyBoy pooling is
   exhausted.

Acceptance targets:

- PyBoy path: at least 50k ROM materializations/minute.
- Stretch PyBoy path: 130k/minute.
- Native/headless fast-core path, if built: 160k to 500k/minute.
- Hook-light and hook-heavy paths prove equivalent on sampled witnesses.

## Phase 7 - Equivalence Proof Database

Goal: avoid re-proving the same behavior after every run.

Tasks:

1. Store proof artifacts by content hash:
   - source diff hash;
   - trace ROM hash;
   - symbol hash;
   - rule map hash;
   - canonical class id;
   - mirror version;
   - materializer version.
2. Track class signatures:
   - selected action;
   - score bytes;
   - switch path;
   - branch signature;
   - public-read signature;
   - rule ledger digest.
3. Reuse proofs when all hashes match.
4. Invalidate only affected classes after Boss AI source edits.
5. Emit a reproducibility packet for every proof query.

Acceptance:

- Re-running the God gate on unchanged artifacts is mostly cache validation.
- Changing one Boss AI rule invalidates only classes that can touch that rule.
- Cache reuse never hides hash-basis mismatch.

## Phase 8 - Changed-AI God Suite

Goal: after a Boss AI edit, one command returns to zero gaps or points at the
exact new uncovered behavior.

Tasks:

1. Build `run-suite --profile boss-ai-god` or `god-suite`.
2. Source diff drives affected rule ids and class invalidation.
3. The suite refreshes:
   - rule map;
   - class schema if public reads changed;
   - affected class enumeration;
   - exact mirror checks;
   - ROM materializations for changed classes;
   - contribution/public-read evidence;
   - explain-decision packets for top deltas.
4. The suite ranks changed behavior by severity and novelty.
5. The suite exits nonzero for any unclassified new Boss AI label, class,
   public read, or materialization mismatch.

Acceptance:

- A Boss AI source edit cannot silently remain outside the proof universe.
- The suite reports "zero gaps" only when all affected classes are refreshed.

## Phase 9 - User Question Front Door

Goal: preserve the human-level experience while the backend becomes exhaustive.

Tasks:

1. Let `explain-decision` target any canonical class, live boss route, generated
   policy family, changed-rule delta, or coverage gap.
2. Add `--why "<question>"` parsing only if it stays deterministic and maps to
   explicit target fields.
3. Return:
   - observed or generated decision input;
   - class id;
   - proof status;
   - exact ROM decision;
   - compact mirror decision;
   - contribution waterfall;
   - public-read provenance;
   - counterfactual flip;
   - source anchors;
   - proof artifacts;
   - cache/proof freshness.
4. If the question maps to multiple classes, explain the class set and render
   representative/minimized witnesses.

Acceptance:

- "Why did this boss do that?" resolves to either a complete proof packet or a
  failing God-gate gap action.
- There is no path where the answer is green but missing a reachable Boss AI
  behavior class.

## Phase 10 - Final God Gate

Goal: make the stricter claim enforceable.

The final gate should run:

- `python tools\audit\check_boss_ai_debugger_god.py`
- `python tools\audit\check_boss_ai_debugger_deity.py --baseline`
- `python tools\audit\check_boss_ai_debugger_speed_targets.py`
- `python tools\audit\check_boss_ai_debugger_roadmap.py --check-rom-selector-materialization --check-rom-score-materialization`
- `python tools\audit\check_boss_ai_debugger_done.py`
- `python -m unittest discover tools\boss_ai_debugger\tests`
- `python -m unittest discover tools\trace\tests`
- `python -m tools.boss_ai_debugger rule-map check`
- `python -m tools.boss_ai_debugger state-schema validate --fixtures --trace-dir audit\boss_ai_trace`
- `python -m tools.boss_ai_debugger trace-replay --trace-dir audit\boss_ai_trace --glob "*_live.txt"`
- `python tools\audit\check_boss_ai_selector_replay.py`
- `python tools\audit\check_boss_ai_pre_choice_replay.py`
- `python tools\audit\check_boss_ai_trace_invariants.py`
- `python tools\audit\check_boss_ai_live_capture_ledger.py`

Any hash-basis mismatch is a blocker unless the command is explicitly running a
diagnostic mode that is expected to report mismatch.

Final definition of done:

1. `check_boss_ai_debugger_god.py` reports zero missing reachable Boss AI
   labels, rules, branches, public reads, class ids, proof artifacts, and
   materialization paths.
2. Every reachable raw Boss AI decision input maps to a canonical proved class.
3. Every canonical class has exact mirror output and ROM-backed evidence at the
   required proof tier.
4. Every changed Boss AI source edit invalidates and refreshes affected classes.
5. Performance targets pass.
6. Existing Boss AI deity and normal Boss AI debugger gates remain green.

## Recommended Next Implementation Order

1. Build the God gate harness red baseline.
2. Land Phase 1 performance work before expanding exhaustive coverage.
3. Add the universe extractor and canonical class schema.
4. Expand exact mirrors and ROM materialization breadth class by class.
5. Add proof-cache invalidation and changed-AI God suite.

Speed comes first because exhaustive proof without speed will collapse into a
slow curated benchmark again. The strongest next technical bet is the compact
IR/evaluator lane: it attacks the largest Python overhead, makes class
enumeration cheap, and reduces pressure on ROM materialization by shrinking the
set of cases that need emulator proof.
