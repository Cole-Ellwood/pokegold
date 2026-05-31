# Boss AI Debugger Deity-Mode Roadmap

Status: focused implementation roadmap. Created 2026-05-30.

Purpose: define the Boss-AI-only slice of debugger deity mode. The broad
deity roadmap in `docs/debugger_deity_mode_roadmap.md` covers every runtime
surface: navigation, taint, audio, graphics, script VM, live views, and cleanup.
This file deliberately narrows the scope to one question:

> Given any reachable Boss AI decision, can the debugger drive the proof itself
> and answer "why did the boss do that?" without the human hand-supplying a save
> state, trace, scenario, materialization artifact, or contribution artifact?

Successor target: `docs/boss_ai_debugger_god_level_roadmap.md` raises this
standard from "supported Boss AI decision classes" to "every reachable Boss AI
decision class in the current commit," with speed-first canonical class proof
and a stricter failing gate for any newly discovered unsupported behavior.

The Boss AI state-of-the-art plan in
`docs/boss_ai_debugger_state_of_art_implementation_plan_2026-05-15.md` remains
the technical feature map. This file is the deity-mode execution contract for
that map: what must become self-driving, how it is measured, and what "done"
means for Boss AI only.

## Scope

In scope:

- `tools/boss_ai_debugger/*`
- Boss AI trace/proof tooling under `tools/trace/*boss_ai*`
- Boss AI audits under `tools/audit/check_boss_ai_*.py`
- Boss AI artifacts under `audit/boss_ai_debugger/*` and
  `audit/boss_ai_trace/*`
- Boss AI docs under `docs/boss_ai_debugger*.md`
- Optional read-only integration with `tools.debugger navigate` once navigation
  can reach boss-battle predicates from replayable input logs.

Out of scope for this focused roadmap:

- Audio, graphics, script VM, live TUI/canvas, and generic byte taint deity work.
- Gameplay or ROM-policy changes under `engine/`, `data/`, `ram/`, `home/`,
  `maps/`, `audio/`, or `gfx/` unless Cole explicitly approves a separate
  behavior change.
- LLM/API integration inside the debugger. Boss AI explanations must remain
  deterministic, local, replayable, and source/proof backed.
- Taste decisions. The debugger can expose behavior, mismatches, and review
  queues; it does not decide whether a policy is fun or fair.

## Deity Bar For Boss AI

God-tool Boss AI debugging is a toolbox: exact selector replay, state schema,
rule map, scenario generators, ROM materialization, contribution traces,
counterfactuals, minimization, coverage, and `explain-decision`.

Boss AI deity mode means the toolbox becomes a self-driving proof workflow:

1. The user names a boss decision question, such as:
   - "Why did Falkner choose Gust?"
   - "Why did Morty switch on turn 3?"
   - "Why did the generated active-pressure case prefer damage over status?"
   - "After this Boss AI source edit, what behavior changed and why?"
2. The debugger locates or creates a legitimate public-info decision state.
3. It captures or refreshes the needed ROM proof artifacts.
4. It renders the answer in one packet with:
   - observed ROM decision;
   - candidate scores and selector/switch probability;
   - score contribution waterfall;
   - public-read/predicate provenance;
   - source anchors;
   - ROM/Python agreement;
   - counterfactual flip;
   - policy/mastery evidence refs;
   - next proof or "proof complete" status.
5. It records reproducible artifacts and gates the result with audits.

The human boundary is reduced to "ask the Boss AI question and read the
answer." Manual save-state authoring, trace capture, scenario selection,
materialization path selection, and follow-up artifact wiring are no longer
required for supported Boss AI decision classes.

## Current Baseline

Already present or in progress:

- `explain-decision` accepts generated scenarios and live trace captures.
- It supports focus actions, attached ROM score/selector/switch materialization,
  attached ROM contribution traces, optional `--run-rom-proof`, JSON output, and
  compact text output.
- It now renders structured proof guidance: dependent proof chains, expected
  output paths, consumed artifact paths, and evidence ids each command closes.
- Live captures exist for 16 gym leaders plus Koga, Champion Lance, and the
  shared switch-loop fixture under `audit/boss_ai_trace/*_live.txt`.
- Exact selector replay over current live trace files reports 19/19 matches.
- `state-schema validate`, `rule-map check`, `trace-replay`, `coverage-report`,
  `confidence-report`, `metamorphic`, `mutate`, `invariants`, `route-eval`,
  `diff`, `run-suite`, and the foundation/performance/roadmap audits exist.
- Scenario families cover spikes/spin, mastery policy, prediction mix,
  support handoff, setup/heal, switch/sack, and cash-out board delta surfaces.
- ROM score materialization exists for exact/mirrorable families and diagnostic
  broad families; ROM switch materialization exists for switch-dispatch proof.
- `tools.debugger navigate` has early-game checkpoint replay/search progress,
  but not boss-battle-depth arbitrary navigation.

Known gaps that prevent Boss AI deity mode:

- Many Boss AI proofs still begin from prebuilt live traces, state-factory
  states, generated scenarios, or manually selected materialization artifacts.
- The debugger cannot yet start from "boss X turn Y / policy question Z" and
  autonomously reach, capture, materialize, explain, and verify the decision.
- Full score-rule/public-read provenance is not proven for every reachable Boss
  AI rule and switch branch.
- Broad generated families are not all exact ROM score mirrors; some remain
  policy review surfaces until localized into precise ROM-backed rules.
- Current local `pokegold_trace.gbc` may not match the manifest-pinned trace
  basis, so selector/pre-choice/performance/roadmap gates can be hash-gated.
- Red is not part of the current live capture manifest.
- Manual boss-feel playtesting remains separate from deterministic proof.

## Measurement

Add a Boss-AI-only deity gate instead of redefining the broad debugger deity
gate.

### New Benchmark

Create `audit/boss_ai_debugger/deity_benchmark/questions.jsonl`.

Each record must include:

- `id`
- `question`
- `decision_surface`: `live_boss`, `generated_policy`, `switch_dispatch`,
  `score_rule`, `changed_ai`, or `coverage_gap`
- `driver`: must be `auto`
- `proof_command`
- `evidence_marker`
- `expected_closed_evidence_ids`
- `required_artifacts`
- `source_anchor_expectation`
- `public_info_standard`
- `disproof_standard`
- `phase`

A question passes only when the proof command exits 0, emits the evidence
marker, writes its declared artifacts, and closes the declared evidence ids
without hand-supplied state/trace/scenario/proof artifacts beyond the question
itself.

### New Audit

Create `tools/audit/check_boss_ai_debugger_deity.py`.

It should report:

- `boss_ai_deity_ready=<bool>`
- `pass_rate=<0..1>`
- `gap_actions=<n>`
- per-question pass/fail with command, artifact, evidence-id, and hash-basis
  diagnostics
- current trace ROM/symbol hashes vs manifest-pinned hashes

It should support:

- `--self-test` for scorer logic without PyBoy
- `--baseline` to record an honest red baseline
- `--allow-hash-mismatch-skip` only for local development where the trace ROM
  basis is knowingly stale

### Done Gate

Extend `tools/audit/check_boss_ai_debugger_done.py` only after the new Boss AI
deity gate exists. The normal done gate should keep reporting current
state-of-art readiness; the deity gate remains explicitly red until this
roadmap is complete.

## Phase 0 - Boss AI Deity Harness

Goal: make the Boss AI deity target measurable before implementing more
capability.

Tasks:

1. Add the benchmark schema and seed questions.
2. Add `check_boss_ai_debugger_deity.py --self-test`.
3. Add baseline report under `audit/boss_ai_debugger/deity_benchmark/`.
4. Add README/docs pointers without changing gameplay source.

Seed benchmark questions should include:

- live first-decision explanation from a known trace route;
- live switch-dispatch explanation from `shared_switch_loop_live.txt`;
- generated policy explanation with auto ROM proof;
- generated score-rule case requiring contribution/public-read provenance;
- generated switch/sack case requiring switch materialization;
- changed-AI adaptation dry run over existing artifacts;
- coverage-gap worklist question for an uncovered reachable rule;
- hash-basis diagnostic question proving stale trace ROMs skip honestly.

Acceptance:

- `python tools\audit\check_boss_ai_debugger_deity.py --self-test` passes.
- `python tools\audit\check_boss_ai_debugger_deity.py --baseline` writes an
  honest baseline with explicit gap actions.
- Existing focused Boss AI verification still passes.

## Phase 1 - Self-Driving Boss Decision Inputs

Goal: remove the manual "find or make the decision state" step for supported
Boss AI questions.

Tasks:

1. Define a Boss AI decision target schema:
   - `boss_route`
   - `decision_index` or `turn`
   - optional `focus_action_id`
   - optional public-state predicate
   - optional policy tags / expected lesson id
2. Add a resolver that maps a target to the best available proof source:
   - current live trace capture if sufficient;
   - trace state factory route if a first-decision proof can be refreshed;
   - `tools.debugger navigate` manifest once it can reach that boss battle;
   - generated scenario family if the question is policy-space rather than
     route-space.
3. Add a manifest format that records how the decision input was obtained:
   checkpoint/input log, state factory route, generated seed, trace ROM hash,
   symbol hash, source commit, dirty diff hash, and replay verification result.
4. Add fail-closed diagnostics when a target is unsupported:
   "route exists but no replayable input path," "trace ROM hash mismatch,"
   "switch state is after dispatch," "scenario family cannot materialize score
   bytes," etc.
5. Add Red only if a real route/state target is available; do not fabricate Red
   coverage to satisfy a list.

Acceptance:

- A command can explain a supported route decision from a target like
  `--boss-route falkner --decision-index 1` without the user naming
  `audit\boss_ai_trace\falkner_live.txt`.
- The packet includes the input manifest path and whether it was replay-verified.
- Unsupported boss/turn targets fail closed with a next-action command.

## Phase 2 - `explain-decision` As The Boss AI Front Door

Goal: make one command orchestrate all existing proof tools for one decision.

Tasks:

1. Add a route/target entrypoint, for example:
   `python -m tools.boss_ai_debugger explain-decision --boss-route falkner`
   and, later, `--at "<boss_ai_predicate>"`.
2. Teach `--run-rom-proof auto` to choose and chain the necessary proof tools:
   selector replay, score materialization, switch materialization,
   contribution trace, Python contribution normalization, counterfactual, and
   rule-map/source checks.
3. Stop after the strongest proof the current input supports, and label weaker
   evidence honestly.
4. Preserve `--focus-action-id` across every generated command and every
   re-render.
5. Add `proof_status` states:
   - `explained`
   - `partial`
   - `needs_rom_proof`
   - `needs_contribution_proof`
   - `needs_switch_proof`
   - `blocked_by_hash_basis`
   - `unsupported_target`
6. Ensure every proof command has:
   - evidence ids it closes;
   - output paths it writes;
   - artifact paths it consumes;
   - exact re-render command;
   - verification command.

Acceptance:

- The user can ask "why did boss X choose/avoid Y?" using one command for every
  supported live route and generated family.
- The answer packet requires no hand inspection of materialization JSON.
- Missing proof is reported as a concrete, copy-paste-safe next chain, not prose.

## Phase 3 - Full Score And Public-Read Provenance

Goal: every reachable Boss AI score/switch explanation can slice from final
decision back to source labels and legal public inputs.

Tasks:

1. Expand rule-map coverage until every reachable Boss AI scoring/switch label
   has a stable semantic rule id, classification, source anchor, and public-read
   declaration or explicit no-public-read reason.
2. Expand ROM contribution hooks to cover all score mutators, switch confidence
   paths, proposal paths, threshold paths, and relevant public branch labels.
3. Record public-read snapshots for every declared public input class used by a
   rule: revealed moves, hazards, screens, active species, party HP bands, role
   memory, tier, plan id/confidence, plausible masks, switch cooldowns, and
   route context.
4. Add a coverage audit that distinguishes:
   - source label mapped;
   - hook target reachable;
   - rule entry observed;
   - score delta observed;
   - predicate branch observed;
   - public-read snapshot observed.
5. Treat hidden-info reads as hard failures unless the rule is explicitly marked
   as a legal Haki/exception surface.

Acceptance:

- `coverage-report` and the Boss AI deity gate expose no unexplained reachable
  Boss AI score/switch rule.
- `explain-decision` can name the decisive rule and public input for a live
  trace where score bytes differ.
- Hidden-info metamorphic checks pass on the generated and materialized samples.

## Phase 4 - ROM Materialization Breadth

Goal: generated policy cases stop being Python-only review aids unless they are
explicitly labeled as such.

Tasks:

1. Classify every generator family by proof mode:
   - exact ROM score materialization;
   - selector-only materialization;
   - switch-dispatch materialization;
   - policy-review only;
   - unsupported.
2. Expand `rom-score-materialize` for families whose state can be honestly
   patched into public WRAM before scoring.
3. Expand `rom-switch-materialize` for switch/sack families and live
   switch-dispatch questions.
4. Add hook-equivalence checks where contribution hooks may perturb timing or
   behavior.
5. Make unsupported families produce a localized work item instead of appearing
   as vague missing proof.

Acceptance:

- The deity benchmark includes at least one exact score case, one selector-only
  case, one switch-dispatch case, and one honestly unsupported case.
- Materialization artifacts include hash basis, base route/state, patched public
  facts, observed ROM bytes, Python comparison, and known limits.

## Phase 5 - Boss AI Search, Minimization, And Review Queue

Goal: when an AI edit changes behavior or a policy card is weakly covered, the
debugger finds the best next case to inspect.

Tasks:

1. Add a Boss-AI-only search profile that combines:
   - generated family expansion;
   - live-trace mutation from public facts;
   - mastery policy seeds;
   - coverage-guided rule targeting.
2. Ensure every high-severity mismatch gets:
   - minimized scenario;
   - decisive counterfactual;
   - likely source/rule cause;
   - public input delta;
   - proof chain to ROM materialization when supported.
3. Rank review queue items by:
   - bad-roll/catastrophic policy risk;
   - uncovered rule or branch novelty;
   - small selector gap;
   - recent changed file relevance;
   - mastery-card evidence importance;
   - reproducibility confidence.
4. Add duplicate-lesson suppression strong enough for million-case runs.

Acceptance:

- A generated million-case or budgeted equivalent run reduces to a top review
  queue with less than 10% avoidable duplicate lesson spam.
- Every top item has a command that renders an `explain-decision` packet.

## Phase 6 - Changed-AI Adaptation Suite

Goal: after a Boss AI edit, one command refreshes the right proof surface and
explains behavior deltas.

Tasks:

1. Teach `run-suite --profile changed-ai` or a new `deity-changed-ai` profile
   to:
   - inspect changed Boss AI files;
   - rebuild trace ROMs when required;
   - refresh live traces when source/manifest basis changed;
   - refresh rule map;
   - run targeted generators for changed rule ids;
   - materialize supported generated cases;
   - compare against the previous run;
   - produce a review queue and summary.
2. Make stale hash basis a first-class state:
   `blocked_by_hash_basis`, with exact rebuild/refresh commands.
3. Record source commit, dirty diff hash, ROM hashes, generated seeds, and
   artifact hashes in run metadata.
4. Keep broad release-smoke stale handoff claims outside this lane unless the
   user asks.

Acceptance:

- One command identifies changed Boss AI behavior, stale trace artifacts,
  missing Python mirror rules, and review-worthy policy changes.
- The command exits nonzero only for real blockers or mismatches configured as
  fatal, not for expected roadmap gaps.

## Phase 7 - Performance And Reproducibility

Goal: deity mode is usable, not just correct on tiny cases.

Targets:

- Pure selector replay: 1,000,000 decisions/minute.
- Python scenario scoring: 5,000,000 decisions/minute.
- Generated expectation checks: 1,000,000 decisions/minute.
- Review ranking: 1,000,000 generated cases/minute to a top queue when ROM
  execution is not required.
- ROM-backed score/switch materialization: as fast as PyBoy and hooks honestly
  allow, with worker pooling and fast-score-only modes where valid.

Tasks:

1. Keep hot scoring in compact data structures.
2. Reuse PyBoy sessions or worker pools for ROM materialization.
3. Cache parsed rule maps, symbols, move data, trainer teams, and mastery
   predicates by content hash.
4. Separate pure Python triage from ROM proof refresh.
5. Make every run reproducible from run metadata alone.

Acceptance:

- `check_boss_ai_debugger_performance.py` passes on the supported local basis.
- Run metadata can reproduce benchmark inputs, generated seeds, proof artifacts,
  and review queue ranking.

## Final Definition Of Done

Boss AI debugger deity mode is complete when all of these are true:

1. `check_boss_ai_debugger_deity.py` reports
   `boss_ai_deity_ready=True`.
2. Every Boss AI deity benchmark question passes with `driver=auto`.
3. `explain-decision` can answer supported live route, generated policy,
   score-rule, and switch-dispatch questions without hand-supplied traces,
   scenarios, or proof artifacts.
4. Every packet names observed ROM behavior, candidate scores, selector/switch
   path, contribution/public-read provenance, source anchors, ROM/Python
   agreement, counterfactuals, and proof status.
5. Reachable Boss AI score/switch rules have mapped source ids and either ROM
   provenance coverage or an explicit unsupported/unreachable reason.
6. Hidden-info/no-cheat metamorphic checks pass.
7. Changed-AI suite produces behavior diffs, stale-artifact diagnostics, and
   ranked review items from one command.
8. Performance gates pass on the supported hash basis.
9. Existing focused Boss AI gates still pass:
   - `python -m compileall -q tools\boss_ai_debugger tools\trace`
   - `python -m unittest discover tools\boss_ai_debugger\tests`
   - `python -m tools.boss_ai_debugger --help`
   - `python -m tools.boss_ai_debugger rule-map check`
   - `python -m tools.boss_ai_debugger state-schema validate --fixtures --trace-dir audit\boss_ai_trace`
   - `python -m tools.boss_ai_debugger trace-replay --trace-dir audit\boss_ai_trace --glob "*_live.txt"`
   - `python tools\audit\check_boss_ai_selector_replay.py`
   - `python tools\audit\check_boss_ai_pre_choice_replay.py`
   - `python tools\audit\check_boss_ai_debugger_foundations.py`
   - `python tools\audit\check_boss_ai_debugger_performance.py`
   - `python tools\audit\check_boss_ai_debugger_roadmap.py --allow-incomplete`
   - `python tools\audit\check_boss_ai_debugger_done.py --skip-changed-ai-suite`
10. Any hash-basis skip is reported as a blocker with exact refresh commands,
    not counted as a pass.

## Recommended First Goal

Do not begin by editing Boss AI gameplay source. Start by building Phase 0:
the Boss AI deity harness and baseline. That gives future sessions a scoreboard
that says exactly which Boss AI proof steps are still manual.

Once Phase 0 exists, the next implementation goal should be Phase 2 on top of
the current trace/scenario inputs: make `explain-decision` a stronger
self-orchestrating front door. Phase 1 deep navigation can proceed in parallel,
but it is a larger game-progression problem and should not block making the
Boss AI proof packet deterministic and measurable today.
