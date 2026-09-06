# Root-Cause Oracle Roadmap

Date: 2026-09-05. Status: implementation in progress; Phase 0 is partial.

Implementation record: [first development fixture and baseline](../audit/debugger_root_cause/development_2026-09-05.md).
Additional development fixture: [historical mail-removal SRAM corruption](../audit/debugger_root_cause/mail_removal_2026-09-05.md).
Additional development fixture: [historical link-mail buffer search](../audit/debugger_root_cause/link_mail_search_2026-09-06.md).
The confirmed Grass-regrowth regression has been rebuilt and reproduced against
its historical correction. The fixture exporter and initial evaluator rejection
tests exist. Two runtime-capture defects encountered during that work are fixed.
An independent causal replay verifier now checks that known case, including
intervention, negative control, trace replay, and broken/fixed regression runs.
The mail-removal development case also has an independent verifier that accepts
an assisted submission against caller, loop, fill, and whole-SRAM replay evidence.
The public investigation does not yet emit that complete diagnosis submission.
The 20-case pilot, general replay evaluation, autonomous investigation loop, and
release corpus are not complete; there is no blind success-rate claim.

## Objective

Turn the existing debugger into a system that takes an unfamiliar bug report,
obtains a reproduction, identifies the earliest causal mistake, verifies the
explanation, and returns a small evidence packet with a regression check.
The user should normally describe the symptom and read the answer. Codex may
operate the debugger, but manual source investigation and hand-built scenarios
count as assistance, not autonomous success.

"Instant" means fast verified answers when evidence is available, plus a useful
immediate response while a cold reproduction runs. It must never mean labeling
a quick guess as a proven root cause. The engineering target is 95% autonomous
diagnosis on a frozen, representative evaluation corpus, not a promise about
every possible program state. Always publish corpus size, failures, supported
scope, latency, and assistance alongside that percentage.

This is a successor to the [Godmode spec](debugger_godmode_spec.md),
[deity roadmap](debugger_deity_mode_roadmap.md), and
[literal-anything roadmap](debugger_literal_anything_roadmap.md). Their gates
remain useful prerequisites; none substitutes for the diagnosis gate below.
Do not restart their completed tooling work or rename their existing results.

## Observed baseline

Checked in this working tree on 2026-09-05:

- Session orientation: 35/35 component selftests passed.
- Godmode benchmark: 29/29 passed. Its default path scores predefined answers
  from `next_steps.py`, including anchor/command matches and word overlap.
- Capability audit: subsystem ready, deity demo not evaluated, whole-ROM
  blocked. The catalog currently hard-codes that whole-ROM blocker; it is not
  a fresh execution of the literal-anything gate.
- `next_steps.py` matches keywords, selects the first matching row, and falls
  back to general triage. Symptom-only `investigate` is explicitly a plan.
- A hypothetical PC deposit/nickname/withdrawal freeze report returned general
  documentation and triage, not PC implementation anchors or a diagnosis.
- The deity checker executes a supplied benchmark command and checks its exit
  code and evidence marker. It does not discover that command from the symptom.
- The current literal-anything and full deity runtime gates were not rerun for
  this assessment. Their historical completion claims are not current results.

Reuse the real runtime, taint, reverse-query, minimization, navigation,
state-inspection, Boss AI, damage, and content tooling already present.

## What counts as a solved bug

A successful diagnosis must contain all of the following:

1. Exact ROM, symbols, source, backend, initial state, inputs, and RNG basis.
2. A replay that exhibits the reported failure, with an observable expectation
   that distinguishes broken behavior from intended behavior.
3. The causal source location: function and source line or mapped instruction,
   plus the relevant state/value and the violated invariant. A subsystem name,
   suspicious write, last crash instruction, or changed line alone is not enough.
4. A chain from the initiating mistake through the observed symptom, naming
   evidence for each essential dependency. Include control dependencies,
   omitted operations, and timing/order where relevant, not just data writes.
5. A discriminating check: a narrow intervention, controlled comparison, or
   independent invariant proof that supports the cause and rejects plausible
   alternatives. Suppressing the final symptom alone does not establish cause.
6. A minimized reproducer and regression check that fails on the broken case
   and passes on its corrected/control case for the right reason.
7. Explicit scope, remaining uncertainty, elapsed time, and assistance used.

Expected behavior must come from a contract, confirmed regression baseline, or
user clarification. The implementation under investigation cannot be its own
only oracle. If intent is ambiguous, ask the smallest necessary question and
continue collecting independent evidence; do not invent a gameplay rule.

Preserve existing CLI signatures and report contracts. Express these semantics
using existing envelopes and evidence fields first. Review an exact schema only
if a demonstrated integration gap requires a public change; this roadmap does
not prescribe new public verdict names or a parallel report framework.

### Source identity for exported inputs

History-free source exports now carry `source_manifest.json`, containing exactly
`source_files` (a mapping of canonical relative paths to SHA-256 content hashes)
and `source_tree_sha256`. The latter hashes each sorted UTF-8 path, a NUL byte,
and the binary file digest. This is the existing evaluator source-basis algorithm.
Commit IDs, fix identities, observations, and accepted locations remain outside
the diagnostic input. The manifest adds no CLI flags or diagnosis verdicts.

This closes an observed integration gap: a public investigation could identify
the mapped source file but could not reconstruct the exported source set after
build products had been generated. The runner now rechecks every declared input
before creating output and verifies that basis again before returning. It emits
the existing evaluator field `source_tree_sha256` only for a verified basis.
An absent manifest leaves that field absent; an invalid initial manifest rejects
the run, and a source change during execution invalidates the report. The
independent evaluator still owns whether the declared source set is complete.

## Measurement and release gates

Build a frozen acceptance corpus of at least 100 distinct failures, spanning
battle/AI, scripts/maps, PC/party/inventory, saves/banking, graphics/audio, and
interrupt/timing/link behavior. Report each family separately. Include at least
30 historical real regressions and at least 30 independently authored mutations;
the remainder can be independently reproduced real issues or realistic injected
failures. Include cross-subsystem causes and rare event sequences.

Keep a separate development corpus. Hold out entire causal bug families and
locations, not just paraphrases of development questions. Add at least 30 clean
or ambiguous controls outside the failure denominator. The diagnostic runner
must not read held-out fixes, fault locations, labels, or benchmark metadata.
Historical fixes and regression descriptions can leak the answer through git,
audit files, and documentation: expose only the intended source revision and
sanitized runtime inputs to that runner. Independently review accepted causes.

| Measure | First integrated milestone | Release target |
| --- | --- | --- |
| Autonomous verified diagnosis | At least 16/20 blind pilot failures | At least 95/100 frozen failures; at least 85% in each family |
| False claims of proven cause | Zero in pilot and controls | Zero observed across acceptance failures and controls; publish sample size |
| First useful response | Report anchors or missing evidence promptly | p95 within 5 seconds on the declared reference machine |
| Warm verified diagnosis | Measure baseline before tuning | p50 within 10 seconds, p95 within 60 seconds with a compatible pre-trigger recording/state |
| Cold verified diagnosis | Measure navigation and diagnosis separately | p95 within 10 minutes on the supported corpus |
| Evidence replay | Every accepted pilot result reproduces | Every accepted result revalidates against its recorded basis |
| Manual assistance | Record every intervention | Zero for cases counted as autonomous |

These are proposed engineering targets, not measured current performance.
Publish timeouts and failures; do not compute a flattering latency using only
easy successes. Unsupported cases in the frozen scope count as unsolved. Report
out-of-scope cases separately without shrinking the denominator after a run.
Do not claim 95% of all real bugs from a 100-case score; expand and rotate sealed
holdouts as real usage accumulates. A new false proven-cause claim blocks release
until corrected and regression-tested.

## Phase 0 — Establish an honest diagnosis benchmark

Deliver a 20-failure pilot, clean/ambiguous controls, an evaluator, and a current
baseline. Feed the same public investigation entry point that users will use;
do not supply a bespoke proof command or suspect symbol in symptom-only cases.
Evaluate exact cause and evidence replay, not strings such as "proof passed."
Use separate input tracks for symptom only, symptom plus recording, and symptom
plus crash state. A crash state may be insufficient to recover earlier history.

Acceptance: the existing system gets an honest score, including unknowns and
misroutes. The evaluator rejects wrong-cause/correct-file answers, post-crash
writes presented as initiating causes, stale evidence, nonexecuted plans,
marker-only fake proofs, and a "fix" that merely bypasses the symptom. Tests of
the evaluator must demonstrate these rejection behaviors before promotion.

Likely integration: `tools/audit/`, existing report envelopes and debugger tests.
This is the first implementation slice; no broad refactor or new UI first.

## Phase 1 — Make one end-to-end case work

Choose a real historical cross-function corruption bug with independently
confirmed broken and fixed revisions. If available, prefer a PC/party or script
resume case outside the already strong Boss AI lanes. The hypothetical PC
symptom above is a routing probe, not an established regression fixture.

Wire existing operations into one bounded investigation: interpret expectation,
locate candidates, obtain state, replay, observe divergence, trace backward,
test explanation, minimize, and report. Keep this orchestration in the existing
investigation/proof path; initially support just enough operations for the case.
Save intermediate artifacts so an interrupted investigation can resume without
repeating an expensive capture. Reuse workflow and evidence identity machinery.

Acceptance: symptom plus an available pre-trigger recording yields a verified
cause and regression artifact without manually specifying source locations,
watch symbols, or commands. An unavailable reproduction returns a specific
missing input rather than success. This development case does not count as blind
acceptance success.

Likely integration: `investigate.py`, `proof_runner.py`, `workflow.py`,
`runtime_state.py`, `trace_index.py`, `minimize.py`.

## Phase 2 — Retrieve unfamiliar code and drive investigations

Keep known keyword routes as shortcuts; add retrieval from current source and
symbols when they are absent or insufficient. Reuse ROM indexes, source slices,
WRAM ownership, references, and map/content metadata. Cover reads and writes,
bank aliases, unions, macros, tables, indirect dispatch, and event transitions.
Return ranked cited candidates and the evidence needed to distinguish them.

For open-ended symptom interpretation, let the host agent reason over retrieved
evidence and invoke existing structured tools. Keep ROM facts and proof checking
deterministic. Do not add an embedded model dependency or hand-author a keyword
row for each held-out failure. Log model/runtime configuration and every tool
step so the measured system includes the agent's cost and behavior.

Use a bounded choose/execute/inspect loop that changes its next action when
evidence rejects a candidate. Stop repeated actions with identical inputs and
no new evidence. Missing intended behavior is distinct from missing runtime
evidence; request only the necessary clarification or artifact.

Acceptance: held-out PC, inventory, event, and banked-memory symptoms reach
relevant code without bespoke routing rows; controlled paraphrases preserve
diagnosis quality; misleading keywords do not lock the runner to the first lane.
Candidate retrieval is measured separately and never counted as a solved bug.

## Phase 3 — Reproduce and capture without expert setup

Extend existing navigation and replay incrementally using observed failed cases.
Prefer supplied recordings, then compatible checkpoints, then bounded navigation
or existing scenario factories. Verify each starting state and label synthesized
states. Do not treat a staged boss seed as a fresh-game navigation proof.

Record enough pre-trigger history to find the first divergence: inputs, RNG,
bank context, key transitions, and targeted memory writes. Start with lightweight
recording and replay a narrow instruction window; grow backward when the cause
precedes the captured window. If no usable history exists, reproduce again or
report that limitation. Add trigger detection for assertion/invariant failures,
reset loops, stalled scripts, unexpected value changes, and visual/audio mismatch
only as supported observable expectations require them.

Acceptance: deterministic replay reproduces the failure and state signature;
the capture contains its causal predecessor. Cover stale/mismatched ROMs,
truncated recordings, insufficient history, rare RNG triggers, bank switching,
and nondeterministic replay. Named failures cannot silently become proof.

Likely integration: `navigate.py`, `repro_recipes.py`, `runtime_watch.py`,
`instruction_trace.py`, `input_log.py`, and `tools/trace/`.

## Phase 4 — Establish cause rather than correlation

Join existing instruction attribution, dynamic taint, reverse queries, register
clobbers, and WRAM lifetime evidence. Start from the earliest observable invariant
divergence and work backward through actual executed data and control flow.
Handle overwritten inputs, missing writes, wrong branches, bank/union aliasing,
and event ordering. Explicitly identify gaps in instruction or hardware modeling.

For each candidate, run the cheapest discriminating experiment. Compare broken
and trusted control executions under matched inputs/RNG where possible. A local
state intervention can test a hypothesis, but cannot alone prove a source fix or
legitimate reachability. Verify it restores the violated invariant and downstream
behavior, and distinguish alternative causes with negative controls.

Historical corrected revisions and mutation controls belong in isolated test
fixtures. Production diagnosis remains read-only on ROM source; this roadmap
does not authorize automatic gameplay patches. Never modify the user's live save
or working ROM to make a proof pass.

Acceptance: blind pilot threshold of 16/20, with all accepted cases replayable.
Reject plausible decoys, shared downstream crash sites, unrelated changed lines,
wrong ground-truth mirrors, and symptom-suppressing interventions. Describe
interacting causes when one location is insufficient; do not force a single-line
answer to a multi-cause failure.

## Phase 5 — Expand based on measured misses

Classify every unsolved case by the missing operation: expectation, retrieval,
reachability, capture, causal model, counterfactual, or backend support. Implement
the smallest reusable improvement for the dominant failure class, then rerun the
affected cases and fresh heldouts. Extend existing surface tools; do not add a
separate orchestrator or state schema per subsystem.

Prioritize PC/party/inventory and script/save corruption after the first vertical
slice, then cross-bank battle interactions, then timing/graphics/audio and link
cases according to measured frequency and impact. Use existing literal-anything
coverage to discover missing surfaces, but require actual diagnosis evidence.
Timing-sensitive emulator results must name the backend and receive the required
VBA-M comparison before a cross-backend claim is accepted. Hardware certainty
and missing link peers remain explicit limits.

Acceptance: run the full frozen corpus, meet overall and per-family targets,
and publish every unresolved case and assistance event. A large family of similar
Boss AI cases cannot compensate for a missing storage or scripting family.

## Phase 6 — Make verified answers fast

Profile the complete pipeline after the blind pilot works. Measure source/index
loading, navigation, trace capture, causal analysis, minimization, and host-agent
latency separately on a recorded reference machine/configuration.

Reuse current indexes and hash-validated checkpoints; cache by ROM/source,
symbols, backend, state, inputs, and expectation as applicable. Use compact event
recording and selective instruction replay. Reuse an earlier diagnosis only when
its cause and evidence still validate against the current basis. Unknown symptoms
must not inherit confidence from a superficially similar cached case.

Acceptance: warm/cold latency targets on the same frozen corpus without accuracy
loss. Cache invalidation tests change each relevant identity input and verify
stale evidence is rejected. No index service, database, or persistent emulator
daemon unless profiling demonstrates a need that a local change cannot address.

## Phase 7 — Regression output and operating discipline

Produce a concise answer with cause, causal chain, reproducible evidence, and
scope. Attach the minimized input/state fixture and a regression command using
existing test infrastructure. Run that check on broken and control cases. Keep
raw reports available without making the user assemble them into an explanation.

Store useful confirmed reproductions for development, but retire exposed
acceptance cases and replace them with sealed holdouts. Add previously unseen
real user bugs to ongoing evaluation. A corrected routing row is a maintenance
improvement; it is not evidence of improved generalization by itself.

Acceptance: all release metrics pass, focused regression tests and existing
applicable debugger gates pass, and no production ROM/source behavior changes.
Do not require unrelated ROM rebuilds for documentation or pure tooling edits;
use the repository build/audit workflow when an actual fixture/build change
requires it.

## Execution order and completion rule

1. Phase 0 baseline and evaluator rejection tests.
2. Phase 1 single integrated development case.
3. Phases 2–4 in small slices until blind pilot acceptance.
4. Phase 5 expansion; Phase 6 optimization only after profiling.
5. Phase 7 release against untouched holdouts.

Each implementation slice should land one observable capability, its behavioral
tests, and a before/after diagnosis score. Keep changes local; reuse existing
modules and remove redundant paths before adding another abstraction. No new
dashboard, mega-framework, exhaustive state ontology, or blanket rewrite is a
prerequisite. Estimate schedule after the pilot exposes integration cost; there
is no defensible completion date from component counts alone.

The roadmap is complete only when the runner satisfies the diagnosis contract
and release targets on unseen failures. A green God, Deity, or literal-anything
gate by itself cannot close this workstream.
