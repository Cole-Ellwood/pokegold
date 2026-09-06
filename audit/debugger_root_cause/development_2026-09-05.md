# Root-cause oracle: first development fixture

Status: Phase 0 partial. This records a confirmed historical bug and initial
scoring infrastructure, not a blind diagnosis result or roadmap completion.

## Confirmed failure

Historical correction: `77e3e77c881d8dc6d363bbf0cc8c7dacfa46ffe3`.
Broken parent: `495b78ff15f4e3790c53648345f4dbec19cdd7da`.

`HandleTypePassiveRegrowth_Far.do_it` loaded the Grass type contribution into
`d`, then called `TypePassive_GetUserHPPointers_Far`, which legitimately returns
an HP pointer in `de`. The caller later used the overwritten `d` to choose the
healing denominator. The correction moves contribution calculation after the
pointer helper, preserving the value until its consumer.

Both revisions were exported into isolated build directories and freshly built
with WSL make and RGBDS 1.0.1. Production source, ROMs, and saves were not changed.
The existing ROM audit's staged between-turns setup was reused. This establishes
routine behavior under the fixture; it does not establish fresh-game reachability.

| Case | Expected heal | Broken ROM | Corrected ROM |
| --- | --- | --- | --- |
| Mono-Grass, max HP 54 | 2 | 1 | 2 |
| Mono-Grass, max HP 80 | 3 | 1 | 3 |
| Mono-Grass, max HP 112 | 4 | 2 | 4 |
| Grass/Poison, max HP 54 | 1 | 1 | 1 |

At denominator selection, the broken ROM has `d=203` (`$CB`, pointer high
byte); the corrected ROM has `d=2` for mono-Grass and `d=1` for dual-Grass.
The dual case demonstrates why matching one output number is insufficient.

Broken ROM SHA256:
`F577606E32313B9718CC756703BBB3F993DF0A4CCF55FE6D4B24865C87AA1CAE`.
Corrected ROM SHA256:
`AFDCC3C8DABD5364A519029DFD683A03A3E6F1B72965F0FD331E2A8FB8C5CBC8`.

## Implemented infrastructure

- `tools/audit/root_cause_fixtures.py` exports pinned tracked ROM/build inputs,
  excluding git history, documentation, audit answers, and debugger routing
  tables. It refuses existing destinations and does not read dirty source as the
  historical revision. Export identities belong to the evaluator, outside the
  diagnostic input directory. This is input separation, not an OS sandbox.
- The same module captures the max-HP-54 staged case before execution and writes
  a state and a 30-frame empty-button schedule. Observed results are returned to
  the evaluator separately from these inputs.
- `tools/audit/root_cause_evaluator.py` rejects absent/nonexecuted causal claims,
  wrong source locations, missing/stale identities, missing evidence, and failed
  independent replay checks. A submission's `passed` flag or success text cannot
  satisfy those checks. An unconfirmed report without an invented cause passes
  only the control check; it is never counted as a solved bug.
- The scorer's replay verifier is an evaluator-owned callable, not a command or
  set of validation flags supplied by the diagnostic report. The full verifier
  that replays causal chains, interventions, and generated regression artifacts
  is still outstanding. Unit-test verifiers do not establish runtime capability.

The initial claim convention reuses `EvidenceAtom` and the report envelope:
`claim_type=diagnosis.root_cause`; `precision` carries `source_file`,
`source_symbol`, and `source_line`; `detail` carries the invariant, causal-chain
event references, reproducer, regression, scope, and uncertainty. The envelope
pins ROM, symbols, source content, backend, and initial state/input/RNG basis.
No existing CLI signature or report field was removed or redefined. No current
investigation output is promoted into a causal claim merely because it passed.
The scorer currently accepts one initiating cause per case; multi-cause scoring
remains a required later slice.

## Runtime defects encountered and corrected

1. Selecting both a function and a local label made `trace-instructions` install
   duplicate hooks and abort with "Hook already registered for this bank and
   address." Capture now registers each bank/PC once and credits all overlapping
   target windows from the observed PCs.
2. `wBattleMonHP`, `wBattleMonMaxHP`, `wEnemyMonHP`, and `wEnemyMonMaxHP` were
   watched as one-byte values. Small HP changes affected only the unobserved low
   byte. These watches now read both bytes; status-byte watches remain one byte.

Real-ROM replay after the fixes captured 163 instruction records on the broken
fixture and 164 on the corrected fixture, without capture errors. The HP watch
observed `$002C -> $002D` (44 -> 45) versus `$002C -> $002E` (44 -> 46), and the
denominator helper was included in both traces. This is capture verification,
not an autonomous root-cause proof.

The first capture attempt also exposed differing global and repo-local PyBoy
installations. The fixture producer selects the existing trace runtime backend
before seeding. The saved fixture and successful replay used PyBoy 2.7.0. General
cross-process backend selection/identity remains work to verify beyond this path.

## Initial diagnostic baseline

The existing `build_investigation_run` entry point was run against the exported
broken revision, not the current corrected ROM. One real failure was supplied
in two tracks; these are not two independent bugs.

| Input | Outcome | Packet time |
| --- | --- | --- |
| Symptom only: mono-Grass max HP 54 heals 1 instead of 2 | No causal claim; keyword `1 hp` selected the unrelated overworld-poison route. Its audit anchor was absent from the isolated input. | 13.757 s |
| Same symptom plus pre-trigger state and ROM | Valid investigation packet, no causal claim | 9.313 s |
| Invented PC/nickname report, with no confirmed failure | No invented causal claim; unconfirmed-report control passed | Not used as a latency measurement |

These timings are individual development observations, not p50/p95 figures.
The developer knows the historical cause, so this case cannot count toward
unseen-family acceptance or an autonomous success percentage.

Local artifacts:

- `.local/tmp/root_cause_oracle/development/fixture.json`: full source/ROM/symbol,
  backend, state, and input identities plus independent observations.
- `.local/tmp/root_cause_oracle/development/baseline.json`: per-track scorer output.
- `.local/tmp/root_cause_oracle/grass_broken/capture_report.json` and
  `execution.jsonl`, with corresponding files under `grass_fixed/`: executed
  instruction traces, target coverage, and HP observations.
- `.local/tmp/root_cause_oracle/grass_broken.build.log` and
  `grass_fixed.build.log`: historical build output.

## Reproduction and verification

Fixture preparation is currently a Python API, not an unattended corpus runner:
call `export_revision(repo, commit, fresh_directory)`, build `pokegold.gbc` there
with the project's WSL/RGBDS command and `branch_currency_banner=`, then call
`capture_grass_regrowth(fixture_root, fresh_recording_directory)`. The banner
override applies only to a deliberately pinned historical export; it does not
disable release currency checks. The exporter intentionally excludes that audit.

Focused checks:

Result: 80 tests passed in 41.423 seconds. Python compilation and scoped
`git diff --check` also passed. The broader release and deity gates were not
rerun for this development slice; this is not a release-readiness claim.

```text
python -m unittest tools.debugger.tests.test_root_cause_fixtures tools.debugger.tests.test_root_cause_evaluator tools.debugger.tests.test_instruction_trace tools.debugger.tests.test_runtime_watch tools.debugger.tests.test_dynamic_taint tools.debugger.tests.test_effect_trace tools.debugger.tests.test_investigate tools.debugger.tests.test_explain
```

Next work: extend independent replay verification and add a repeatable corpus runner,
build the 20-case pilot from confirmed failures, then integrate the first causal
investigation through the public entry point. Preserve the distinction between
the invented-report control and a reproducible bug throughout evaluation.

## Independent causal replay development slice

`runtime_experiment.py` now replays a saved state in a fresh emulator and permits
preconditioned, once-only byte-register interventions at observed instructions.
It records before/after registers and watched memory, validates intervention
inputs before opening the emulator, and closes without saving. This is an
experiment primitive; it does not infer a diagnosis. The shared register
snapshot now derives H/L from PyBoy's HL pair instead of silently omitting them.

`root_cause_grass_verifier.py` owns the known development case's expectations.
It rehashes the exported source inventory, ROM, symbols, state, and inputs;
checks the loaded backend binary; and matches submitted event references to a
fresh baseline. It executes the proposed intervention, an unrelated-register
negative control, and one-frame broken/corrected regression replays. The captured
chain shows D=2 before the pointer helper, D=203 after its DE assignment, and the
same wrong value reaching the heal selector. GetMaxHP receives the already-bad
value, so blaming that later helper does not explain the initiating mistake.

Restoring D=2 at the consumer restores both the invariant and HP 44→46.
Changing unrelated E leaves HP at 45. Forcing the heal shift changes HP to 46
while leaving D corrupt and is rejected. The one-frame regression fails on the
broken ROM and passes on the historical correction. This minimizes the replay
window only: the synthetic RAM state and legitimate gameplay reachability are
not minimized or established by this experiment.

The actual historical ROM runs accepted the assisted reference and rejected all
six adversarial submissions: symptom suppression, unrelated intervention,
omitted initiating chain, reversed chain, correct file/wrong cause, and stale ROM
identity. Additional unit checks cover forged events, each stale fixture artifact,
backend mismatch, invalid event references, artifact path escape, incomplete
regression, and broken control. These are evaluator tests, not blind diagnoses.

The reference's executable command was run successfully:

```text
python -m tools.audit.root_cause_grass_verifier .local/tmp/root_cause_oracle/development/fixture.json .local/tmp/root_cause_oracle/development/submission/reference.json
```

Local `submission/cli_verification.json` contains the score and fresh experiment
evidence; `submission/adversarial_scores.json` records the rejection matrix.
The accepted reference is explicitly assisted and contributes zero autonomous
successes. The public investigation baseline remains unsolved. This verifier
contains evaluator-owned ground truth for one development case and must never
be supplied to a held-out diagnostic runner.

Verification for this slice: 98 tests passed in 46.501 seconds across the prior
focused modules plus `test_runtime_experiment` and `test_root_cause_grass_verifier`.
No production gameplay source, live ROM, or live save was changed by this slice.

## Source retrieval through the investigation entry point

The existing localization step now scans the supplied source revision for
lexically relevant assembly blocks. It splits identifiers and folds simple
inflections, ranks matching terms with frequency and block-length weighting,
and emits the existing signal/candidate shapes with file-and-line quotations.
It reads current files on every call, excludes docs/audit history, and adds no
bug-specific keyword routes, dependencies, CLI flags, or causal verdicts.
Only colon-defined global blocks are indexed by this initial retrieval path;
local labels remain inside their enclosing block. Unexpanded macros and prose
synonyms remain limitations, and source comments are leads, not expectations.

A real public investigation against the broken development revision exposed
static graph fanout overwhelming the retrieved candidates: large files and
commonly called routines accumulated thousands of points. Static slice signals
now contribute their strongest weight per candidate rather than a fresh vote
for every reference. Other evidence retains its existing scoring behavior.

After this correction, the symptom-plus-state public run returned a valid
packet in 13.997 seconds and ranked `HandleTypePassiveRegrowth_Far` third.
`GetMaxHP` remains first because its existing comment describes a similar prior
clobber; it is a useful decoy that the independent runtime checks reject as the
initiating cause in this case. The report still makes no causal claim, and its
autonomous diagnosis score remains zero. Local outputs are
`development/retrieval_run.json`, `development/retrieval_summary.json`, and the
reports in `development/retrieval_run/` below the existing local artifact root.

Synthetic behavior tests exercise previously unknown storage, inventory, event,
and bank routines, a misleading `1 hp` phrase, inflection/order changes, excluded
documentation answers, source edits invalidating matches, and repeated static
references failing to bury the relevant routine. They measure retrieval only.
The original unconfirmed PC report also retrieved actual storage code in a
manual probe; it remains a control, not a reproduced bug or diagnosis success.

Verification: 33 tests passed in 46.427 seconds across `test_localize`,
`test_investigate`, `test_explain`, and `test_root_cause_evaluator`;
scoped `git diff --check` passed. The autonomous experiment-selection loop,
20-failure pilot, and full release corpus are still unfinished.

## Bounded capture driven by retrieved candidates

With the existing `execute_watch=True` option and a supplied state, investigation
now captures retrieved code, observes which routines execute, and widens into
those routines' local blocks and callees. It uses the existing instruction
tracer and static call graph. Each of at most three trials reloads the same
state; repeated target sets, no hits, and failed captures stop expansion.
The existing frame, target, and event limits bound each trial. Memory watches
come from references in the selected code, distributed across candidates.
Data-only source labels are not initial instruction targets. Planning mode
retains its existing execution behavior.

The public symptom-plus-state development run required no user-supplied source
symbol, watch symbol, intervention, or evaluator metadata. Trial 1 observed
GetMaxHP and the regrowth routine in 52 records. Trials 2 and 3 expanded to the
pointer helper and related code, producing 159 and 173 records. The resulting
trace contains D=2 before the pointer assignment, D=203 afterward and at the heal
selector, and HP changing from 44 to 45. This is automatic evidence collection
for a known, manually materialized development fixture; it is not autonomous
causal diagnosis or gameplay navigation.

The initial capture index incorrectly discarded all events because the old
symptom heuristic selected wCurDamage for “HP.” Newly captured execution is now
indexed without that heuristic filter, preserving all 384 events across the
three separately named traces. Coverage, explanation, expectations, and
minimization receive those trace paths. No root-cause claim is produced yet.

The final real run was valid and took 72.501 seconds. This single observation
does not establish a latency percentile or meet the warm-diagnosis target.
Artifacts: `development/capture_run.json`, `development/capture_summary.json`,
and the per-trial JSON reports/JSONL recordings in `development/capture_run/`
under the existing local artifact root. Reusing an output directory currently
reruns capture; identity-checked resumability remains unfinished.

Verification: 38 focused tests passed in 58.543 seconds across investigation,
instruction tracing, localization, and trace indexing. The two new public-path
tests also passed after the final small edit. They cover observed-call expansion,
inferred watches, data-label exclusion, indexing despite misleading HP language,
planning mode, failure/no-hit termination, repeated targets, three-trial/target/
recording limits, unchanged input state, and absence of invented causal claims.
Compilation and scoped diff checks passed. Full root-cause identity, causal
analysis, discriminating experiments, regression generation, and blind evaluation
remain necessary before the roadmap can be considered complete.

## Observed call-boundary register evidence

The effect tracer now adds `effect.call_registers` evidence atoms to direct CALL
events when it observes the callee entry and a matching RET/continuation with
the expected stack pointers. Each atom reports changed and preserved observed
byte registers, plus references to interior register writes confirmed against
the next captured instruction. Missing registers remain unknown. Returns from
another recording, mismatched bank/PC/stack, missing entry/return observations,
and conditional returns with unknown flags cannot establish this evidence.
This initial analysis handles direct unconditional CALL instructions; it does
not infer farcall/indirect-call contracts or declare a changed register a bug.

The saved third automatic capture produced seven observed call boundaries.
At `HandleTypePassiveRegrowth_Far.do_it+0xE` (sequence 38), D changes from 02 to
CB between entry 39 and return 44; sequence 40 is the independently next-frame
confirmed `ld de, $cb0e` write. The shift-routine call records D as preserved.
These results are in `development/call_boundary_summary.json` and the refreshed
`development/capture_run/effects.json`/`effects.jsonl` artifacts. This analysis
ran on the prior live capture; it did not repeat emulator capture this slice.

Investigation now generates an effect report and JSONL from its captured traces
before coverage and explanation, using existing report/evidence structures.
The public-path test checks this integration; effect tests and the historical
trace separately check the register evidence. Observed boundary changes are
not an inferred preservation contract, a causal diagnosis, or an independent
expected-behavior oracle. The diagnosis score remains unchanged.

Verification: 37 tests passed in 34.222 seconds across effect tracing,
investigation, and dynamic taint. The added tests cover changed versus restored
registers, missing observations, incorrect bank/PC/stack matches, unknown
conditional-return flags, and cross-recording return rejection. Source/ROM/save
behavior is unchanged. Full input identity, autonomous hypothesis testing,
regression output, and the blind corpus remain incomplete.

## Inferred consumer-side intervention

Effect analysis now proposes a bounded trial when a register changed across an
observed call is later loaded into A and compared with its pre-call byte value.
The proposal requires a confirmed interior write and matching adjacent load/
comparison observations. It uses `diagnosis.hypothesis` with `planned_only`
status. The original value may still be an intentional comparison target, so
the pattern alone does not establish a preservation contract or a bug.

Restoration happens at the later consumer: in this regression DE legitimately
serves as an HP pointer immediately after the call, so restoring D at the return
could break that pointer use. The existing runtime experiment primitive validates
the proposed preimage and changes the register only inside a fresh emulator.
Investigation deduplicates proposals across capture trials and runs a baseline
before each restoration, capped at three proposals. A failed baseline prevents
its restoration run. No evaluator answers, fixed revision, keyword route, or
user-supplied suspect/intervention enters this selection.

A fresh public investigation against the historical broken fixture inferred
exactly one proposal: D=203→2 at `HandleTypePassiveRegrowth_Far.heal+0x6`.
It executed both replays successfully. The baseline ended with HP=45 and the
restoration with HP=46. The entire run was valid and took 67.085 seconds.
Artifacts are `development/experiment_run.json`,
`development/experiment_summary.json`, and `development/experiment_run/`,
including `04_trial_1_baseline.json` and `04_trial_1_restore.json`.

This is automatic hypothesis selection and testing on a known development
fixture, not a blind diagnosis success. It still emits no root-cause claim.
The independently known case remains exposed, and its materialized starting
state remains assistance. General intended-behavior extraction, negative
controls, regression generation, complete proof identity, and blind corpus
acceptance remain unfinished.

Verification: 42 tests passed in 35.403 seconds across effect tracing,
investigation, runtime experiments, and diagnosis scoring. Added tests cover
consumer placement, zero-valued restoration, rejection of a different comparison
constant or inconsistent observed load, proposal deduplication, baseline-before-
restoration ordering, and failed baselines preventing interventions. Compilation
and scoped diff checks passed. No production gameplay source, ROM, or save was
modified.

## Capture and experiment identity agreement

Instruction captures now retain capture-time ROM/symbol hashes, the initial-state
hash, a canonical frame-count/empty-input-event schedule, and the loaded emulator
class/module binary hash in their first record and report. Written traces also
receive a content hash in the report. The empty schedule means no newly
dispatched input events; it does not claim that a saved state's latched buttons
are released. RNG state remains identified through the initial-state bytes.
Planning or no-record results do not invent a captured backend/state basis.

Runtime experiments use the same state/schedule encoding. Investigation compares
ROM, symbols, state basis, backend class, and backend binary against its capture.
A mismatching baseline is invalid and prevents the restoration trial. This check
does not establish complete source identity or pin every backend dependency, and
does not yet revalidate all raw trace artifacts before every downstream consumer.
Those remain proof-gate gaps, not assumptions of completion.

A fresh historical GetMaxHP capture and baseline replay were both valid and
matched all five fields. Local `development/identity_verification.json` records
the comparison and `development/identity_trace.jsonl` contains the new capture.
This was a focused identity check, not a rerun of the full diagnosis pipeline.

Verification: 42 tests passed in 38.224 seconds across instruction tracing,
runtime experiments, investigation, and scoring. Tests pin the saved trace and
state bytes, detect changed initial states and replay durations, and check each
of the five baseline mismatches prevents restoration. Compilation and scoped
diff checks passed. The full root-cause roadmap remains in progress.

## Wrong-value control and replay-window check

Each inferred register-restoration trial now includes a third replay at the same
consumer with a different byte value. The control byte differs from both the
observed byte and proposed restoration, including at byte boundaries. It tests
whether the specific proposed value matters; it does not establish intended
gameplay behavior or reject every alternative cause. The existing proposal cap
therefore permits at most nine experiment replays after capture. Failed trials
or identity mismatches still stop that proposal's remaining experiments.

A fresh public investigation inferred D=2 restoration and D=3 control without
operator-supplied intervention details. All three trials passed identity checks:
baseline HP=45, restoration HP=46, wrong-value control HP=45. The entire run was
valid and took 84.700 seconds. Results are in `development/controlled_run.json`,
`development/controlled_summary.json`, and `development/controlled_run/`.
This single development observation does not meet the warm latency target.

A subsequent focused check reran the three generated trial descriptions for one
frame instead of thirty. All final watched values matched their corresponding
thirty-frame runs, including the 45/46/45 HP contrast. These are saved as
`controlled_run/minimal_baseline.json`, `minimal_restore.json`, and
`minimal_control.json`, with `development/minimal_controlled_summary.json`.
One frame is the smallest positive duration accepted by this replay primitive;
this check does not minimize the materialized state or establish legitimate
gameplay reachability. Automatic minimization and regression-file generation
are not yet integrated, and no root-cause claim is emitted.

Verification: 42 focused tests passed in 39.570 seconds. Public-path tests check
the third trial, distinct control values, zero/255 boundaries, and existing
failure/identity stops. Scoped diff checks passed. The first full diagnosis,
source/backend identity gaps, and blind pilot/release gates remain unfinished.

## Automatic one-frame reproduction checks

After successful baseline/restoration/control trials, investigation now tests a
one-frame window. It requires matching replay identity, initial observations,
all observed checkpoint events, and final watched values for each corresponding
trial. A mismatch stops the remaining short trials. Only three successful
comparisons set `minimal_positive_window`; missing observations cannot pass.
This proves the smallest positive replay duration for those observations, not
minimal RAM, minimal gameplay inputs, or a correct-behavior regression oracle.
If one frame fails, the original replay remains available and no broader
duration search or monotonicity assumption is made.

Runtime experiment reports now retain their existing call inputs so they can be
reexecuted directly. The new audit entry point consumes that same report shape,
checks ROM/symbol/state/schedule/backend identity before opening an emulator,
and compares the replayed initial state, events, and final observation with the
recording. This fills the prior executable-reproducer gap without changing
existing debugger CLI signatures or creating a separate recipe schema:

```text
python -m tools.audit.replay_runtime_experiment .local/tmp/root_cause_oracle/development/minimized_run/04_short_1_baseline.json
```

The fresh historical public run was valid, accepted all three one-frame trials,
and retained the 45/46/45 HP contrast. It took 131.879 seconds; latency targets
are still unmet. Reports and commands are in `development/minimized_run/`, with
`development/minimized_summary.json` and `development/minimized_run.json`.
The reports refer to the original state/ROM/symbol files; this is not yet a
self-contained distribution bundle. Replay comparison checks reproduction of
observed behavior, including broken behavior, rather than desired gameplay.

Verification: 45 focused tests passed in 50.199 seconds. Ten affected tests
passed after moving the CLI into the audit namespace to avoid eager-package
module-loading warnings. New tests cover mismatched short-window events, final
watches, identity, missing observations, stale artifact rejection before emulator
creation, and replayed observation drift. All three recorded one-frame trials
also reexecuted successfully. Automatic correct-behavior regression generation,
complete identity, the proven diagnosis gate, and the blind corpus remain open.

### Captured trace verification before intervention planning

The public investigation now checks each written capture's existing
`trace_sha256`, `executed`, and `valid` fields before indexing its trace or
deriving instruction effects. A changed, truncated, missing, unhashed,
unexecuted, or invalid capture fails the investigation and stops capture
expansion and intervention trials. A later failed capture also prevents trials
from using an earlier partial capture set. This reuses the producer's existing
hash and report fields; no CLI or recipe schema was added.

Verification: 35 tests across investigation, runtime experiment, and instruction
trace passed in 54.693 seconds. The new public-path test first failed on all six
initial rejection cases; the final seven-case version also checks failure after
a valid capture and passed separately. Tests assert that effect attribution and
runtime interventions are not called after rejection. Compilation and scoped
whitespace checks passed. This check binds consumed bytes to the capture report;
it does not establish independent correctness, source/build correspondence, or
full backend identity. No fresh historical emulator run or blind score was
claimed for this change. The complete roadmap remains in progress.

### Independent healing outcome through the existing expectation gate

Runtime experiment initial/final watched values now appear in the existing
trace index as `memory_read` observations. The operation distinguishes
`baseline.initial`, `baseline.final`, `intervention.initial`, and
`intervention.final`; the event retains its report path and snapshot location.
Only valid, executed experiment reports supply these observations. This lets
existing exact-value expectations check a baseline without borrowing a correct
value from the initial snapshot or an intervention. CLI signatures and
expectation types are unchanged.

A fresh one-frame replay of both historical source exports used the same
independent expectation: begin with 44 HP and end with 46 HP. Source-export,
ROM, symbols, and initial-state hashes were checked before execution. The broken
ROM ended at 45 and failed only the final-HP expectation; the corrected ROM
ended at 46 and passed both. The contract and fresh reports are saved under
`.local/tmp/root_cause_oracle/development/expectation_run/` as `expected.json`,
`input.json`, `control.json`, the two expectation reports, and `summary.json`.

Verification: 23 expectation, trace-index, and investigation tests passed in
58.115 seconds, including a new seven-case test for correct, broken,
initial-only, intervention-only, unexecuted, invalid, and missing-final
observations. Compilation and scoped whitespace checks passed. This verifies
an independently confirmed healing outcome, not the full causal invariant:
a symptom-bypassing change still requires the separate causal verifier to be
rejected. Automatic expectation discovery, a general causal regression packet,
full identity verification, and the blind pilot/release corpus remain open.

### Causal checkpoint expectation and symptom-bypass rejection

The same trace-index adapter now exposes pre-intervention checkpoint register
values as existing `control_flow` observations, with the exact target label,
bank/PC, register-specific operation, value, and original report JSON path.
For example, `baseline.checkpoint.register_d` can be matched with the existing
`pc_symbol` and `value` expectation fields. After-intervention register values
cannot replace the checkpoint preimage. This adds no expectation type or CLI
argument and does not infer a causal location from a final output.

The development contract now checks initial HP 44, final HP 46, and D=2 at the
regrowth shift checkpoint. Three fresh one-frame emulator runs were checked:

- Broken baseline: final HP 45, healing and contribution checks failed.
- Corrected baseline: final HP 46, all three checks passed.
- Symptom bypass: forcing the shift selector A from 6 to 5 restored final HP 46,
  but left D corrupted; initial/final HP checks passed and the contribution
  check failed. This case explicitly uses intervention observations and the
  same expected values, without relabeling the run as a baseline.

Source-export, ROM, symbols, and state hashes were rechecked before these runs.
Artifacts are in `.local/tmp/root_cause_oracle/development/invariant_expectation_run/`:
`expected.json`, `intervention_expected.json`, the three fresh experiment and
expectation reports, and `summary.json`. Checkpoint and expected values were
provided from the previously confirmed evaluator-owned development invariant;
this is assisted verification, not autonomous diagnosis or a blind score.

The seven-case expectation test covers correct value, wrong value despite
correct final output, wrong checkpoint, wrong register, after-only value,
intervention, and missing checkpoint. The positive case failed before the
adapter change. Expectation/trace-index/runtime-experiment tests passed 22/22
in 10.835 seconds. Full causal-chain generation, independent expectation
discovery, complete source/backend identity, and corpus gates remain open.

Follow-up verification: all 11 investigation tests passed in 43.108 seconds;
compilation and scoped whitespace checks passed. The checkpoint test was then
extended to nine cases to explicitly reject unexecuted and invalid reports,
and passed again in 0.024 seconds.

### Expectation-driven baseline in the public investigation

The public `investigate` path now replays supported baseline snapshot/checkpoint
expectations directly when execution and a save state are supplied. It derives
watch symbols and observation checkpoints from existing expectation files or
inline expectations and records `04_expected_baseline.json`. This works even
when corrected code produces no clobber hypothesis. The replay does not change
registers, and plan-only execution and unreadable expectation files do not run
this additional trial. No CLI arguments or expectation types were added.

An initial full public run exposed a second integration problem: trace
minimization tried to preserve desired-behavior predicates on the broken replay,
adding an operational error to an otherwise valid reproduced failure. For a
valid one-frame expectation baseline, the investigation now keeps that actual
replay at the minimization step and emits its executable replay command. One
frame is the minimum positive duration; this does not minimize materialized RAM
or claim a gameplay navigation proof. The original expected behavior remains a
separate regression check, so a broken case remains `passed: false`.

Thirty investigation, expectation, and runtime-experiment tests passed in
42.717 seconds after the change. The new public test covers an expectation file,
inline expectations, a broken baseline, plan-only execution, and a missing
contract, including exact observation targets, absence of register intervention,
retained failed behavior, and the saved one-frame reproducer. Compilation and
scoped whitespace checks passed. Longer-duration expectation baselines still
need failure-preserving runtime minimization; independent expectation discovery
and the complete diagnosis/corpus gates remain unfinished.

Final full public runs after the minimization correction: broken input was
`valid: true`, `passed: false`, with no operational errors, in 81.647 seconds;
corrected control was `valid: true`, `passed: true`, with no errors, in 56.223
seconds. Both starting-HP checks passed; the broken healing and contribution
checks failed and the corrected checks passed. Reports and summary are saved as
`development/public_expectation_v2_{input,control}/`, the corresponding full
JSON reports, and `development/public_expectation_v2_summary.json`. Both saved
baseline replay CLI commands were executed again successfully (exit 0), with
fresh outputs saved as `baseline_replayed.json` in their run directories. These
are assisted development runs with a supplied checkpoint contract; no blind
success or latency-target completion is claimed.

### Bounded duration reduction preserves the reproduced observations

Expectation-driven baselines longer than one frame now try shorter replay
windows in ascending order, up to the existing `max_cases` budget. A candidate
must preserve ROM/symbol/backend/state/input identity (apart from the requested
duration), the complete initial snapshot, checkpoint events, and final watched
values. A candidate that restores the desired value is not accepted when that
changes the reproduced failure. Ascending trials avoid a monotonicity assumption
and prove the first matching duration is the minimum positive duration for
these observations. If all shorter durations are excluded, the original can
itself be the minimum.

Each candidate and the original report are retained. A budget limit or an
unassessable replay retains the original and reports the minimum as unproven;
a changed identity invalidates the reduction. A completed shorter run that
simply never reaches a required checkpoint excludes that duration and permits
the next trial. The selected report retains the existing replay CLI command.
This replaces the one-frame-only path for expectation baselines, while keeping
the independently supplied regression expectations unchanged.

Verification: 31 investigation, expectation, and runtime-experiment tests
passed in 45.849 seconds. The new public-path test covers 13 cases, including
one- and two-frame minima, preserving a failure despite a candidate satisfying
the desired output, a zero trial budget, a capped search, an original minimum,
changed ROM/symbol/backend/state identity, missing checkpoints, changed initial
or checkpoint observations, and a runtime error. Artifact-retention assertions
passed in a separate 1.839-second run. Compilation and scoped whitespace checks
passed. This is a minimum of the recorded observations, not a reduction of all
materialized state or gameplay navigation; the full causal and corpus gates
remain open.

Real full public verification reduced the 30-frame historical failing baseline
to one frame while preserving all recorded checkpoint/initial observations and
final HP 45. The independent desired-behavior regression still failed, as it
should; the investigation was valid with no operational errors. The complete
run took 109.736 seconds. Artifacts are in
`development/public_duration_minimize/`, with the full report and summary in
`development/public_duration_minimize.json` and
`development/public_duration_minimize_summary.json`. The selected
`10_minimize.json` was replayed through the saved audit CLI successfully (exit
0), with output saved as `minimum_replayed.json`. This is one assisted historical
development case, not a blind diagnosis result or a latency-target pass.

### Source call candidates for observed register-clobber hypotheses

Effect traces now reuse the static call graph to attach matching source calls
to existing hypotheses. Matching checks the caller's symbol bank/range and the
observed callee bank/address, and requires a direct unconditional source call.
The candidate includes source file, block, line, instruction, and file hash.
Repeated matching calls remain separate candidates. These fields stay in the
hypothesis detail; they do not populate proven source precision or promote the
hypothesis to a root-cause claim. Current-source-to-built-ROM correspondence is
explicitly unverified.

Reprocessing the hash-checked historical capture files produced two hypotheses
from two capture windows, both citing the same candidate: line 1256 of
`engine/battle/type_passive_damage_mods.asm`, the call to
`TypePassive_GetUserHPPointers_Far` in `HandleTypePassiveRegrowth_Far.do_it`.
The recorded source hash matched the current exported source. Artifacts are
`development/source_candidate_effects.json`, `development/source_candidates.json`,
and `development/source_candidate_summary.json`. Two windows are evidence for
one development case, not two independently diagnosed failures.

Verification: all 44 effect-trace, investigation, and dynamic-taint tests passed
in 39.997 seconds. The new mapping test covers a single call, repeated calls,
an edited source line/hash, wrong caller bank, wrong callee bank, and wrong
callee; an added conditional-call mismatch case passed separately in 0.047
seconds. Compilation and scoped whitespace checks passed. No fresh emulator
capture or full build was needed for this source lookup check. A verified build
mapping and complete causal claim remain outstanding, along with the blind
pilot and release corpus.

### Build-backed address check for the development source candidate

An isolated copy of the historical broken build received one local label
immediately before source line 1256. WSL make reassembled `main_gold.o`, relinked
Gold, and ran the existing ROM fix/stadium steps successfully. The generated
label `HandleTypePassiveRegrowth_Far.__debugger_source_call_1256` resolves to
`11:71DC`, exactly the call address observed in both trace windows.

The rebuilt ROM SHA256 is
`F577606E32313B9718CC756703BBB3F993DF0A4CCF55FE6D4B24865C87AA1CAE`, identical to
the recorded broken ROM. Removing only the added label line reconstructs the
original source bytes exactly. Every original symbol retains the same address;
the marker is the only additional symbol. The original source export and main
working-tree source were not edited. This verifies the source-line address for
this historical case, using an actual assembly/link rather than textual call
matching. Other object files came from the existing historical build; this does
not establish full current-source provenance for every linked object.

The build directory, log, preparation manifest, and verification are saved as
`development/source_label_build/`, `development/source_label_build.log`,
`development/source_label_manifest.json`, and
`development/source_label_verification.json`. The verification records original
and instrumented source hashes, original and rebuilt symbol hashes, ROM hash,
main-object hash, build-log hash, and RGBASM/RGBLINK/RGBFIX executable hashes.
The build used the documented explicit Windows RGBDS executables through WSL
make, with `PYTHON=python3`, `branch_currency_banner=`, and target `pokegold.gbc`.

This address verification was manually orchestrated and counts as assistance.
The automatic hypothesis remains provisional until such a check is integrated
and replayed in its evidence path; no root-cause verdict was promoted. Full
causal-chain generation, independent expectations, full source/backend identity,
and the pilot/release corpus remain unfinished. No unrelated gameplay changes
or generated documentation refresh were needed.

### Reusable isolated source-mapping operation

`provenance.build_source_mapping_report` now performs the label-only mapping
operation using the existing provenance report and evidence-atom format. A
trusted caller supplies the build function; candidate/report content cannot
supply a command. Preflight checks the candidate source hash, line, instruction,
source block, CALL address, required files, and a new destination outside the
reference tree before any copy or build. Existing destinations are not changed.
The copy excludes `.git` and object caches, inserts the local marker, and runs
the configured build. Failed builds retain artifacts but emit no mapping atom.

After build success, the operation verifies unchanged reference inputs, exactly
the intended label-only source edit, identical ROM bytes, the expected marker
bank/address, and every original symbol. Success emits only a
`provenance.source_mapping` atom with `mirror_passed` status and precise source
and ROM address fields. It does not emit `diagnosis.root_cause` or assert
causal correctness. Existing CLI signatures are unchanged; automatic build
selection and investigation integration remain separate work.

Verification: 22 provenance and effect-trace tests passed in 1.286 seconds.
Tests cover stale/missing candidate fields, invalid line/address boundaries,
wrong data shape, unsafe or existing destinations, missing inputs, source/ROM/
symbol/address drift, missing markers, failed/raising builders, absence of
mapping evidence on failure, excluded object caches, and unchanged reference
files. Compilation and scoped whitespace checks passed.

The operation also completed a real fresh-object Gold rebuild using the
prepared historical tree and the configured WSL/RGBDS command. It returned a
valid mapping of line 1256 to `11:71DC`, with the original ROM and symbols
preserved. The build tree is `development/source_mapping_operator/`; the report,
including build stdout/stderr, command, result, and caller-recorded RGBDS
executable hashes, is `development/source_mapping_operator_report.json`.
The host supplied the build configuration, so this remains assisted development
verification. Full causal diagnosis, full provenance, and corpus gates remain
unfinished.

### Automatic source mapping after a discriminating trial

The public investigation now selects source candidates from its observed
hypotheses, deduplicates them, and schedules a label-only rebuild after a valid
baseline/restoration/control comparison. The baseline and negative control must
agree and the restoration must change the final watched values. At most the
smaller of three, `max_targets`, and `max_cases` source locations are rebuilt.

Build configuration comes from the prepared tree's Makefile, numeric
`.rgbds-version`, and matching RGBDS binaries. The fixed recipe uses the existing
Gold target supplied to investigation, with a 120-second build timeout; no
candidate supplies shell commands. Missing tooling produces an explicit skipped
step. Builds use retained temporary directories outside the source tree, omit
`.local` artifacts and object caches, and leave source inputs unchanged. Rebuild
ROM/symbol identity must match the capture before address evidence enters the
packet. A failed or mismatched mapping remains an error, not a proven cause.

Verification: 36 investigation, provenance, and effect-trace tests passed in
43.618 seconds. New integration coverage checks one build for duplicate source
candidates, no build without a discriminating outcome, missing tooling, failed
builds, and mismatched mapping identity. Six provenance tests passed again in
0.855 seconds after explicitly testing `.local` exclusion. Compilation and
scoped whitespace checks passed.

A full public historical run selected and rebuilt the candidate without a
manually selected source line or build callback. It emitted one valid source
mapping at line 1256 / `11:71DC`, retained the failing gameplay expectations, and
completed without operational errors in 124.794 seconds. Reports are in
`development/public_source_mapping/`, with full JSON and summary at
`development/public_source_mapping.json` and
`development/public_source_mapping_summary.json`. The provenance report records
the retained temporary build directory. This used a prepared build tree and a
previously supplied expectation contract; it is a development integration run,
not a blind or fully autonomous diagnosis. Root-cause synthesis, independent
intent, complete provenance, latency, and corpus gates remain unfinished.

### Per-trial behavior contracts (2026-09-05)

Investigation now evaluates each valid baseline, restoration, and negative-control
trial against the supplied expectations using the existing expectation report.
Each check reads only that trial. For intervention trials the copied contract uses
`intervention.*` operations in place of `baseline.*`; values, checkpoint symbols,
counts, and other requirements remain intact. Original expectation files are not
modified. Contract-requested watches and checkpoints are included in all trials
and their shorter-window checks. This makes output restoration distinguishable
from satisfying the complete supplied contract, without issuing a root-cause claim.

The existing public investigation test now checks the independent trial reports,
retention of baseline failure, correct-output/wrong-invariant rejection, observation
of a separate contract checkpoint, and the source-mapping cases. All 45 investigation,
expectation, provenance, and effect-trace tests passed in 45.287 seconds. Compilation
and scoped whitespace checks passed. Public CLI signatures remain unchanged; the
additional artifacts use the existing expectation schema. Expected behavior still
requires an independently justified supplied contract, and causal synthesis and
acceptance-corpus gates remain open.

The first real run used shortened symptom wording and completed in 138.555 seconds.
Its three trial checks were valid: baseline/control passed initial HP but failed
healing and the checkpoint invariant; restoration passed all three. Source mapping
also succeeded. However, the overall run was invalid because the earlier replay
router returned `no watchable replay target was found`. This is a retained routing
limitation, not an accepted diagnosis. Artifacts are in
`development/public_trial_expectations/` and its adjacent summary JSON. A repeat
uses the exact established fixture wording to compare this change consistently.
All 14 investigation tests passed again in 54.868 seconds after the final change
to include contract checkpoints in shorter-window trials.

The repeat with the established symptom wording completed in 151.348 seconds,
valid with no operational errors. It retained the broken behavior (`passed: false`)
and produced the expected independent trial results: baseline/control fail healing
and type contribution; restoration passes initial HP, healing, and type contribution.
Artifacts: `development/public_trial_contracts/`, `public_trial_contracts.json`, and
`public_trial_contracts_summary.json`. This remains an assisted development run with
a supplied invariant contract and prepared historical state/build tree. It does not
prove an autonomous diagnosis or satisfy the remaining corpus/causal-chain gates.

### Route replay from supplied observation contracts (2026-09-05)

Moved the existing expectation parsing before replay planning and passed baseline
initial/final memory symbols into the existing replay watch inputs. The planner
can now use the supplied observable contract when symptom keyword routing provides
no target. Explicit watches retain order, duplicates are removed, and planning
still does not execute. The expectation baseline and individual trial checks reuse
the parsed contract. No CLI or report schema changes were introduced.

A public investigation test exercises CLI and file contracts with an unfamiliar
parcel symptom, explicit/contract duplicate watches, planning without execution,
and absence of a contract or target. It verifies the actual replay report and
watch invocation, preserves failing expected behavior, and checks the input
contract is unchanged. The focused test passed; compilation and scoped whitespace
checks passed. The exact shortened Grass symptom from the previous routing failure
is being rerun through the full public investigation for runtime verification.

Verification completed: 34 investigation, replay, and expectation tests passed in
58.897 seconds. The real public run with the exact previously failing shortened
symptom completed in 156.960 seconds, valid with no operational errors. Replay
selected `wBattleMonHP` from the contract. Baseline and control expectations still
fail, restoration passes, and source mapping is valid. Overall `passed: false`
correctly retains the broken gameplay observation. Artifacts are in
`development/public_contract_routing/`, with adjacent full and summary JSON files.
This resolves the demonstrated contract-backed routing failure, not general
symptom-only reproduction or the outstanding causal-diagnosis and corpus gates.

### Link verified trial evidence to the source hypothesis (2026-09-05)

The investigation's existing evidence-atom field now carries a combined
`diagnosis.hypothesis` when baseline/control fail the supplied expectations,
restoration passes, all checks are valid/nonempty, and the source mapping is a
verified label-only rebuild. The atom links the observed call/consumer/comparison
sequences, source precision, original contract, trial and expectation reports,
and ROM/symbol/backend/state basis. Referenced traces, reports, and source mapping
carry file hashes. The source hash is retained. It explicitly leaves the complete
initiating dependency chain, independent intent, and corrected-source regression
unverified; no root-cause atom or complete-proof claim is emitted.

Tests cover the combined atom and its references, plus withholding it for absent,
failed, stale, or unproven mappings and wrong-invariant/no-contrast trials. All 42
investigation, effect-trace, and evaluator tests passed in 47.640 seconds; the
focused integration test passed again after reference hashes were added.
Compilation and scoped whitespace checks passed. Existing real raw traces were
checked to resolve both observed windows' call/consumer/comparison sequence numbers
to the corresponding instructions. Full runtime packet verification follows.

The full public historical run completed in 145.023 seconds, valid with no
operational errors and retained gameplay failure. It emitted exactly one combined
hypothesis at `engine/battle/type_passive_damage_mods.asm:1256` / `11:71DC`, linking
two independently captured observation windows and all three trials. Verification
asserted the source location and every referenced trace/trial/expectation/mapping
hash against the actual files. Artifacts are in `development/public_linked_hypothesis/`
and adjacent full/summary JSON files. This remains an assisted development result;
the combined hypothesis is not a completed causal diagnosis or a benchmark success.

### Preserve register-change provenance and expose propagation gaps (2026-09-05)

Hypothesis observations now retain the call's entry/return sequence numbers,
register values before/after the call, and next-frame-confirmed in-call write
sequences. A direct-continuity flag distinguishes a dense unchanged register path
from gaps or intervening definitions. The combined investigation evidence retains
this detail. These remain hypotheses; equal return/consumer values do not prove
that intervening code transported the value.

An initial straight-line rejection experiment removed the historical hypotheses:
the real caller increments DE and GetMaxHP saves, reuses, and restores DE. It was
replaced with explicit propagation uncertainty rather than excluding legitimate
stack-preservation cases or assuming that equality proves dependency. Existing
byte-taint machinery is the next integration point for proving those transfers.
Tests cover continuous observations, same-value redefinition, sequence gaps,
unknown/changed return observations, and preservation of false continuity through
the combined evidence atom. The focused integration test passed in 1.560 seconds;
compilation and scoped whitespace checks passed.

Reprocessed all three prior captures only after verifying their bytes against
recorded hashes. Both historical hypotheses remain: in-call writes 27 and 40,
entry/return 26/31 and 39/44, D changing 02 to CB, direct continuity false for both.
Saved `development/continuous_register_effects.json`. This is analysis of existing
verified execution, not a fresh runtime run or a completed dependency proof.

All 31 effect-trace and investigation tests passed in 42.117 seconds.

### Observe WRAM bank identity during instruction capture (2026-09-05)

A model experiment with the existing TaintEngine carries the returned D origin
through the real increment/save/reuse/restore sequence into A at the consumer,
with no unsupported instructions. The old trace lacked WRAM bank identity, so
this was not accepted as a stack-transfer proof. Inspection of the installed
PyBoy loader established the supported state-header hardware-mode layout: v8-15
byte 4, v16-17 byte 5. Successful loading still belongs to the backend.

Instruction capture now uses that recognized loaded-state mode to record the
live FF70 selector at each hook in CGB mode or fixed WRAM bank 1 in DMG mode.
Unknown versions/mode bytes omit bank identity. No new CLI parameters or changed
signatures; existing bank-state fields and parsing normalize selector zero to 1.
Tests cover v8/v15/v16/v17, unsupported v7/v18, invalid mode, selector zero/seven,
DMG fixed bank, changing selectors between hooks, and no selector mutation by
capture. All 46 instruction-trace/effect-trace/dynamic-taint tests passed in 2.052
seconds. The 15 capture tests passed again in 1.281 seconds after adding the
per-hook selector-change test. Compilation and scoped whitespace checks passed.

Fresh historical capture: 159 instructions, every frame observes WRAM bank 1.
Compared every record against the previous capture after excluding the newly
added bank fields; all register snapshots, instruction order, watches, and input
basis are identical. Artifacts: `development/bank_observed_capture.json`,
`bank_observed_trace.jsonl`, and `bank_observed_summary.json`. Trace SHA256:
`DE6AE5EBA376397338D15998AF0D0EEAF498195EB0153C7F2C52ECE225EB3352`.
This supplies a missing prerequisite; automated stack-transport proof, complete
causal diagnosis, and acceptance corpus gates remain unfinished.

### Bank-aware register transport and capture-gap rejection (2026-09-05)

Reused the existing byte-taint engine and factored its banked-memory stepping into
one internal operation shared by dynamic taint and investigation transport checks.
Fixed stale stack taint: immediate return-address writes from CALL/RST now clear
older origins at those addresses, including taken conditional calls; untaken
calls preserve the prior bytes. Public dynamic-taint regression tests exercise
reused stack slots through a subsequent pop and observable sink write.

Investigation now checks the observed interval from call return to consumer,
preserves the result in the effect report, and includes it in the combined
hypothesis. Missing/duplicate/out-of-order sequence records, unknown registers or
memory bank, unsupported instructions, and unverified control transitions leave
transport planned-only. A supported same-value redefinition or different-bank pop
can disprove this register dependency; such candidates skip source mapping and do
not emit the combined hypothesis. The bounded operation currently supports
WRAM/HRAM transport and does not claim an initiating cause or intended behavior.

The first full historical run completed in 141.425 seconds with valid trial and
source results and modeled transport through both observed windows. Inspection
then found a missing RST bank-switch trampoline: consecutive hook sequence numbers
were not sufficient to prove complete instruction capture. Control-transition
validation was added before accepting a taint result. The earlier transport
`taint_proven` fields in `development/public_register_transport.json` are therefore
superseded by `development/register_transport_control_validation.json`. Rechecking
the same hash-verified raw traces now correctly leaves both intervals planned-only,
identifying unverified transitions after sequences 44 and 57. No root-cause claim
was emitted. The next capture must include FarCall/Bankswitch and observed return
targets rather than infer the missing instructions.

All 62 dynamic-taint, investigation, instruction-trace, and effect-trace tests
passed before the final control checks; the focused integration test passed again
in 4.561 seconds with control gaps, wrong code bank, and missing return targets.
The final full focused suite result follows. CLI signatures and existing report
kinds remain unchanged; additional transport facts use existing evidence detail.

Final verification: all 62 focused tests passed in 48.901 seconds after the
control-transition and persistence changes. Compilation and scoped whitespace
checks passed. Complete stack transport, causal diagnosis, and corpus gates remain
open; the missing trampoline is a concrete next capture target.

### Capture restart dispatch and observed stack returns (2026-09-05)

POP/RET instruction records now include bus-read stack-byte samples through the
existing `watch_value_specs` field. Reads are limited to WRAM/HRAM addresses;
normal instructions and unsuitable address ranges get no stack samples. The
public capture tests cover ordinary WRAM, bank-boundary addresses, HRAM endpoints,
unsupported memory ranges, absence on NOP, and exact read addresses.

The bounded capture loop follows restart vectors observed in hash-verified traces
and includes their source-reachable dispatch helpers within the existing target
budget. It preserves hit targets, does not expand from an unobserved RST or stale
trace, and still stops repeated target sets. A historical three-pass capture
completed in 46.258 seconds with 52/228/233 records, no record-limit hits, and
FarCall, FarCall_hl, FarCall_JumpToHL, and Bankswitch included automatically.
Artifacts are in `development/dispatch_capture/`.

Those added observations exposed missing RST 00/10 entries in the shared taint
engine's known control opcodes; they now match the other restart opcodes. Tests
assert no unsupported count for every restart. Register transport can apply the
existing MBC3 selector model only when ingested cartridge metadata identifies MBC3
and its ROM hash matches capture identity. Observed mapper writes then establish
the bank used by later control transfers; generic memory transport remains bounded
to WRAM/HRAM. Public integration tests cover known/unknown mapper, identity mismatch,
zero-bank aliasing, and wrong destination bank. No CLI signatures changed.

Reanalysis of the expanded hash-verified captures passes both register-transport
windows, including observed return targets and bank changes 17 -> 15 -> 17. Results
are in `dispatch_capture/transport_after_model_fix.json`. This supports the bounded
register dependency, not a completed causal diagnosis. All 64 focused tests passed
in 61.856 seconds; compilation and scoped whitespace checks passed. Full public
integration verification follows.

Full public verification completed in 166.646 seconds: valid, no operational
errors, retained broken gameplay expectations. Exactly one combined hypothesis
maps to source line 1256 / `11:71DC`; both observed transport windows pass through
the complete captured trampoline and stack restore with MBC3 transitions 17 -> 15
-> 17. The run selected mapper semantics from its matching ingested ROM, not a
manually supplied mapper flag. Trace and mapping file hashes were rechecked.
Artifacts: `development/public_dispatch_transport/`, adjacent full JSON, and
`public_dispatch_transport_summary.json`. This is an assisted development result;
source-to-symptom causal synthesis, complete provenance/regression proof, latency,
and acceptance-corpus gates remain unfinished.


## Stack evidence reconciliation

Register transport now requires captured low/high bytes for each POP, checks any
tagged slot against its last modeled write in the same memory bank, and checks
the resulting register pair and SP against the next captured frame. POP AF applies
the hardware low-nibble mask to F. Contradictions or missing samples retain
planned-only status and omit the dependency conclusion. The change adds one local
map of written byte values; public signatures and report fields are unchanged.

Six public investigation regression cases failed before the change and pass after:
missing low/high samples, a changed tagged stack byte even when the following D
matches that changed byte, and inconsistent D/E/SP after POP. Existing same-bank
restoration and different-bank refutation remain covered. All 64 focused taint,
investigation, instruction-capture, and effect tests passed in 51.791 seconds.

Both saved public-dispatch emulator captures were rechecked against their recorded
SHA256 and reanalyzed. Their register dependency windows still pass, including the
nested stack operations. Results are saved as
`development/public_dispatch_stack_validation.json`. This was reanalysis of saved
captures, not another full emulator investigation. Full root-cause synthesis,
independent intent, corrected-regression proof, and the acceptance corpus remain
unfinished; this check does not promote the hypothesis to a root-cause claim.


## Observed comparison-to-branch dependency

The effect report now cites the first conditional jump reached with the modeled,
next-frame-validated comparison flags intact. It records comparison, branch, and
successor sequences, condition, taken status, actual target/bank, and flags in the
existing hypothesis detail. The public investigation preserves this evidence next
to its register-transport observation. This is a control dependency observation,
not proof that the branch violates independently established intent.

The check stops at overwritten/unknown flags, uncertain effects, or an intervening
control transfer. It requires sequential execution up to the branch and the actual
modeled branch successor, including bank. Tests cover taken/untaken branches,
changed/missing/rewritten flags, missing sequence/successor, and wrong target/bank;
the positive cases failed before implementation. Public investigation coverage
checks preservation of the branch citation in its combined hypothesis.

Reanalysis of both hash-verified public-dispatch captures finds comparison ->
branch -> successor sequences 87/89/90 and 91/93/94. Both execute `jr nz` with F=40
and reach 11:71FA. Artifact: `development/public_dispatch_branch_validation.json`.
The check uses the existing instruction/effect model and adds no CLI parameters,
report envelope, or gameplay patch. The remainder of the source-to-symptom chain,
independent intent and corrected-regression proof, and acceptance corpus are still
unfinished. These saved-capture observations are assisted development evidence.

All 64 focused taint, investigation, instruction-capture, and effect tests passed in 53.774 seconds. Compilation and scoped whitespace checks also passed.


## Replay observations along the downstream calculation

The public investigation now chooses additional trial checkpoints from its own
captured instructions. When a comparison/branch hypothesis precedes a change in a
requested watch, it samples the comparison, branch, successor, apparent store,
and arithmetic PCs in that interval. Repeated arithmetic PCs are observed on every
hit, exposing loop counts. These are capture selections, not dependency verdicts;
selecting a point across incomplete evidence does not certify causality.

The baseline, restoration, negative control, and short replay use the same selected
points. User-required points remain present; extra points fit the remaining
max-targets budget. No fixed-regression symbols or evaluator answers are used by
the selection. Existing CLI and report envelopes are preserved; the existing
runtime observe/events fields carry the observations. This adds one local point
selector and per-hypothesis lists, not another trace or report framework.

Public-entry-point tests cover the extra comparison/arithmetic/store checkpoints,
a three-target budget that preserves two required checkpoints, and the existing
no-downstream-evidence case. All 64 focused taint, investigation, instruction-
capture, and effect tests passed in 64.767 seconds; compilation and scoped
whitespace checks passed. Fresh public emulator verification follows.


Fresh public investigation finished in 160.548 seconds: valid, no operational
errors, one source-mapped hypothesis, and the original broken expectations remain
failed. It selected 17 common checkpoints. Baseline and negative control each
record 41 events, six right shifts, branch F=40, heal amount C=01, store A=2D, and
final HP=002D. Restoration records 36 events, five shifts, branch F=C0, C=02,
store A=2E, and final HP=002E. Raw-trace, trial, expectation-report, and source-map
hashes were checked against the combined hypothesis. Both register-transport
windows still pass. Artifacts: `development/public_downstream_observations/`,
adjacent full JSON, and `public_downstream_observations_summary.json`.

This makes the downstream arithmetic contrast replay-visible rather than merely
comparing final totals. It remains an assisted development hypothesis; a local
intervention alone does not prove source intent, earliest cause, a corrected-source
regression, or full roadmap completion.


## Cited comparison of trial checkpoints

Combined investigation hypotheses now include a checkpoint comparison in their
existing detail. Visits are grouped by bank and PC, with per-trial hit counts,
sequence references, and observed register/watch differences. Every reported value
cites its own event sequence; the adjacent trial metadata supplies the report path
and SHA256. This preserves repeated visits, missing visits, and unknown register
samples without aligning different loop iterations as if they were equivalent.
A sampled event with an unknown value retains its sequence but has no value key.

Constant values are not listed as value changes merely because hit counts differ.
Post-intervention register snapshots are omitted when they repeat pre-intervention
values. They are explicitly described as before instruction execution. Invalid
checkpoint sequences (missing, duplicate, out of order, negative, or boolean)
produce comparison errors and no comparison rows, not fabricated references.
The surrounding observation remains a hypothesis rather than a root-cause claim.
No public call signatures or report envelope changed; one local comparison helper
is used by the existing investigation path.

Public-entry-point tests cover different loop counts, same PC in different banks,
unvisited checkpoints, missing register values, differing register/watch samples,
constant repeats, redundant intervention snapshots, and invalid sequence cases.
The previously captured three emulator trials were hash-verified and compared;
all 17 checkpoint references and every emitted value were checked against the
source trial events. The comparison exposes branch F=40/C0/40, six/five/six shifts,
and HP-store A=2D/2E/2D for baseline/restoration/control. Artifact:
`development/public_downstream_checkpoint_comparison.json` (reanalysis, not a new
emulator run). Full causal synthesis, independent intent, corrected-source
regression, and the blind acceptance corpus remain incomplete.

All 64 focused investigation, effect, taint, and instruction-capture tests passed in 52.814 seconds after the final comparison changes. Compilation and scoped whitespace checks passed.
