# Historical mail-removal fixture

Status: reproduced development case, excluded from blind acceptance results.
The 20-failure pilot is still incomplete. This is a confirmed SRAM corruption
regression, separate from the unconfirmed PC deposit/nickname/withdrawal report.

The historical correction is `11b8679bba912b4ecde8a908e7dac8be971c9ade`; its
broken parent is `4ed6e72eab4a486abd9eeebf6ebb5da090bd488a`. The caller loaded the
party slot into A, but `farcall ClearPartyMonMail` replaced A with the callee's
ROM bank, 17. The callee used that value to index mail storage. The correction
passes the slot in E and loads it into A inside the callee.

Both revisions were exported to new directories with the existing sanitized
source exporter (4,029 tracked build inputs each). Git history, docs, audits, and
debugger answers were excluded. WSL make and RGBDS 1.0.1 built both Gold ROMs
successfully in about 68 seconds each. The production source, ROMs, and saves
were not modified.

`capture_mail_removal` seeds distinct nonzero bytes in six party-mail records
and ten mailbox records, selects party slot 2 (the third member), and saves
immediately before the real caller loads the slot. It saves before registering
the read-only return observation hook. The unmodified caller and callee run for
one frame. The contract is that the selected 47-byte party record is cleared,
other party records remain intact, and every stored mailbox byte is preserved.

| Observation at return | Broken | Corrected |
| --- | --- | --- |
| Changed party-mail offsets | None | 94–140 (the selected record) |
| Changed mailbox offsets | 234–280 | None |
| First byte of selected party mail | `5F` | `00` |
| Mailbox 5 type byte | `00` | `EB` (preserved) |
| First byte of mailbox 6 | `00` | `EC` (preserved) |

The broken interval spans the last byte of mailbox 5 and the first 46 bytes of
mailbox 6. All 47 changed bytes become zero. The corrected run clears exactly
the selected party record. These comparisons use whole recorded mail regions,
not only the three displayed sample bytes.

The fixture exposed a debugger defect: SRAM symbol watches read the CPU bus and
returned `FF` after RAM was disabled, hiding the difference. Symbol watches now
read the named physical SRAM bank through the backend without changing mapper
registers. Public watch tests distinguish banks 0 and 1 at the same address,
reject unavailable bank access instead of substituting bus bytes, and fail on
any attempted mapper/memory mutation.

Both new recordings were replayed through `run_runtime_experiment`, then
independently rerun with `replay_experiment_report`. All four runs passed their
execution/identity checks and reproduced the displayed values. Source hashes
and ROM hashes remained unchanged. This exercises public replay, not an
autonomous symptom-to-root-cause investigation.

Artifacts are under `.local/tmp/root_cause_oracle/`: `mail_source_identity.json`,
`mail_broken_build.log`, `mail_fixed_build.log`, and
`development/mail_fixture_identity.json`. The two `development/mail_*/recording`
directories contain only `initial.state` and `inputs.json`; evaluator observations
and fix identity stay outside them. Adjacent `public_replay.json` and
`revalidated_replay.json` record the public checks. Earlier probe recordings and
`mail_*_public_before.json` document the original all-FF watch failure and are not
the final fixtures.

Broken ROM SHA256:
`B451FE8703E196371187C7586E9E31C60860F46D187891C6F9FB8751A739CE0E`.
Corrected ROM SHA256:
`05E9BE98DCE0CB5EEE6E3AAC73C4733E3F391A1B19501D2D2D8FB2586E0D088A`.

Limits: the state is staged after menu confirmation and bag transfer; neither
navigation nor bag behavior is tested. The historical cause was read during
fixture construction, so this is assisted development evidence. A pilot still
needs independently reviewed cases, sealed inputs, and scores from the public
investigation entry point. No root-cause success percentage is claimed.

The first public `build_investigation_run` received the symptom "Taking mail off
a party Pokemon corrupts messages stored in the PC mailbox", the broken
recording, and three supplied final-byte expectations (`00`, `EB`, `EC` for the
symbols above). No function or source anchors were supplied. In 70.935 seconds
it returned a valid report with failing expectations, no errors, and no
hypothesis evidence. Its expanding capture reached the mail caller, callee,
far-call dispatcher, and byte-fill helpers. The current hypothesis detector
handles register changes across direct calls but misses input overwritten by
far-call setup. This is an unsolved development baseline, recorded in
`development/mail_investigation_baseline/` and adjacent summary/full JSON files.

The trial gate also required the wrong control to produce the exact same final
watches as baseline. It now permits a different failing outcome, provided both
outcomes differ from restoration. Source mapping and separate expectation
checks still gate hypothesis evidence: baseline and control must fail, and
restoration must pass. A public investigation regression covers a distinct
failing control, plus rejection when control matches restoration. This changes
trial selection only; it does not resolve the missing far-call hypothesis.
All 32 investigation and effect-trace tests passed after this change (49.144
seconds); the distinct-control regression failed before the gate was changed.

The next implementation recognizes an observed `ld a, bank / ld hl, target /
rst $08` setup following a freshly written A value, an observed `jp hl` into
the target, and consumption of A before a callee write replaces it. It proposes
restoring the prior input at callee entry. Generic regression cases cover zero
and memory-loaded inputs, missing input, contradictory writes, wrong bank or
target, sequence gaps, wrong dispatch, rewritten input, and missing consumption.
No mail routine names or expected slot values appear in this detector.

On the real capture it proposes A=`02` at `ClearPartyMonMail`, citing setup
`04:70F5`, callee entry sequence 15, and first consumer sequence 18. The matching
source candidate is line 533 in `engine/pokemon/mon_menu.asm`. Public replay
then confirms baseline fails, restoration passes all three supplied byte
expectations, and control A=`03` fails by leaving the selected party record
intact while preserving the mailbox. The initial end-to-end run (128.871
seconds) stopped with a source-mapping error because that verifier supported
only direct CALL instructions. Its artifacts remain at
`development/mail_investigation_farcall/`.

Source mapping now also accepts the six emitted far-call bytes, checking the
source callee's bank and address before copying or building. The label-only
rebuild must still preserve the complete ROM and all original symbols. Tests
reject a changed byte at each of the six positions before copy/build, then
verify the accepted mapping. Input transport remains explicitly unverified in
the saved hypothesis; controlled restoration alone does not prove the earliest
causal error or independently establish the complete mail-storage contract.

The complete rerun finished in 158.769 seconds with a valid report, no errors,
and one controlled-runtime hypothesis mapped to the source line above. The
label-only build passed with identical ROM bytes and unchanged original
symbols. Overall `passed` remains false because baseline violates the supplied
expectations; no `diagnosis.root_cause` is emitted. Artifacts are in
`development/mail_investigation_farcall_mapped/`, with the full report adjacent.
The earlier three trials were also independently replayed successfully with
`replay_experiment_report`. Both source exports and both ROMs retain their
recorded hashes.

Validation for these additions: 33 investigation/effect-trace tests passed;
after the report-plumbing extension, its 18-test focused suite passed; all seven
provenance tests passed. The new positive hypothesis and far-call mapping tests
failed before implementation. Scoped whitespace checks passed.

Input transport now uses the existing instruction/taint checker for A as well
as other byte registers, including consumption at the entry instruction itself.
Far-call observations name this dependency `depends_on_entry`; existing direct
call reports retain `depends_on_return`. A modeled overwrite kills the
dependency even when the resulting byte equals the prior value, suppressing
source mapping and hypothesis promotion. Missing trace frames leave the proof
incomplete. An unexplained observed register change across an instruction that
does not write it also leaves the proof incomplete.

The public investigation tests cover preserved A, entry-time consumption,
same-value overwrite, missing frames, and contradictory observed values. The
positive/overwrite tests failed before input transport was connected; the
contradictory-value test exposed and then verified the fail-closed check.
All 32 investigation and dynamic-taint tests passed in 60.706 seconds.

The full public rerun with input transport finished in 179.216 seconds: valid,
no errors, and one source-mapped hypothesis whose A dependency is `taint_proven`
from entry sequence 15 through consumer sequence 18 (`depends_on_entry=true`).
Baseline and control still fail the supplied expectations, restoration passes,
and the isolated source-mapping rebuild passes. Artifacts are in
`development/mail_investigation_input_transport/`, with the full report adjacent.
The interval contains no mapper write; mapper identity remains unverified in
this report. The later loop/control and SRAM-write dependencies are not yet
proved by this hypothesis, so this remains an assisted development result and
not a verified root-cause verdict.

The next capture includes symbols from the supplied expectations ahead of
inferred watches, within the existing watch budget. Previously those symbols
were used in final replay checks but omitted from instruction capture. Input
hypotheses now select checkpoints at first use, conditional jumps/returns,
arithmetic, and the first store followed by an observed expected-watch change.
These are bounded observation choices, not additional proof claims. Public
tests reproduced both omissions before the changes; all 16 investigation tests
passed afterward (55.423 seconds).

The full rerun completed in 163.882 seconds with one valid source-mapped
hypothesis and no errors. Its automatically selected checkpoints show:

| Trial | Pointer-loop iterations | Byte-store visits | Observed HL range | Store A |
| --- | --- | --- | --- | --- |
| Baseline | 17 | 47 | `A91F`–`A94D` | `00` |
| Restore slot 2 | 2 | 47 | `A65E`–`A68C` | `00` |
| Control slot 3 | 3 | 47 | `A68D`–`A6BB` | `00` |

An additional check of the saved checkpoints verifies every loop pointer equals
`A600 + 47 * iteration`, the counter decreases to zero, the conditional loop
jump sees Z clear until its final visit, and all 47 store pointers are
consecutive with A=`00`. The record is
`development/mail_investigation_loop_observations/checked_loop_observations.json`;
the full investigation report is adjacent to that directory. The assertions
describe observed arithmetic and control sequences; they do not yet constitute
an independently replayed proof of every SRAM byte or the complete root cause.

Default-ROM ingestion is now aligned with execution: `execute_watch=True`
ingests `pokegold.gbc` when no explicit ROM path is provided. Previously replay
used that ROM while the investigation's initial artifact list contained only
symbols and state, leaving mapper identity unverified. Planning-only requests
retain their existing behavior. A public investigation regression failed with
`mapper=unverified` before the fix and now verifies MBC3 against the ingested ROM
hash; separate coverage checks execution without a saved state and planning.
The 16-test investigation suite passed in 53.487 seconds, and the additional
default-ingestion test passed separately.

The real broken ROM was ingested independently as cartridge type `0x10`; its
hash matches the recorded loop capture. That artifact is
`development/mail_rom_ingestion.json`. The prior full reports are preserved
unchanged and still show their original mapper-identity limitation.

`tools/audit/root_cause_mail_verifier.py` now independently replays the four
cases and compares all 8,192 bytes of physical SRAM bank zero at caller return.
It validates both source/ROM/symbol/state/input/backend identities before any
emulator opens, then checks loaded mail bytes and intervention preimages before
execution. The evaluator contains the known case contract and is not imported
by the diagnostic runner. Only restoration and control change A at callee
entry; ROM, source, and state files remain read-only.

The first real run passed in 9.503 seconds. Baseline changes exactly the 47
mailbox bytes, restoration exactly the selected 47-byte party record, control
exactly the next party record, and the historical correction exactly the
selected record. Every other byte in SRAM bank zero is unchanged at return.
Restoration and the correction also produce identical complete bank contents.
Artifacts are `development/mail_whole_sram_verification.json` and the subsequent
`mail_whole_sram_revalidated.json`. Source, ROM, symbols, and initial-state hashes
were rechecked unchanged.

All 22 mail-verifier, fixture, and Grass-verifier tests passed. Coverage includes
stale identities on either fixture before emulator startup, changed input
schedule despite a matching hash, wrong actual backend, unexpected initial
bytes, wrong intervention preimage, missing intervention, missing/duplicate
return, and an extra SRAM write outside the mail regions. Cleanup closes without
saving; tests reject verifier memory/mapper writes. This verifies the complete
SRAM regression and intervention contrast, not a submitted causal explanation
or autonomous benchmark result.

The effect tracer now checks the observed nonzero counted-loop pattern
`and a / ret z / add hl, bc / dec a / jr nz` from the input consumer. It requires
each modeled arithmetic result and flags update to match the following frame,
constant stride, the expected counter and pointer at every step, verified
branch targets/successors, and unchanged flags across the guard and jumps.
Incomplete or contradictory traces omit the loop proof while retaining the
underlying trial hypothesis. The investigation preserves this evidence in the
hypothesis observation details; it adds no root-cause verdict.

The checker validates the real recorded 17-iteration loop: stride 47, pointer
`A600` to `A91F`, input sequence 18 and exit sequence 71, with all iteration
sequence references saved in `development/mail_counted_loop_effects.json`.
This reuses the previously captured trace rather than repeating runtime and
build work. Tests cover 16-bit pointer wrap, wrong pointer/counter/stride/flags,
unexplained flag changes, wrong jump/bank, missing registers, sequence gaps, and
truncation. The combined effect/investigation suite passed 35 tests; after the
final flag-consistency checks, all 18 effect tests passed. The new positive and
rejection tests failed before their corresponding implementation changes.

Register transport now handles known MBC3 SRAM-enable, SRAM-select, and RTC-latch
writes as mapper-register operations that do not replace CPU registers or
WRAM/HRAM. Unknown mapper identity still leaves those operations unverified;
this allowance does not establish SRAM contents or access validity. Three
public investigation regressions failed before the change, and the unknown
mapper control remains incomplete. All 33 investigation/dynamic-taint tests
passed afterward (53.183 seconds).

The real trace now verifies both H and L dependencies from the pointer base at
CALL sequence 17 through the first store at sequence 90, across the counted loop
and SRAM setup. The probe's trace hash and MBC3 ROM identity match the captured
basis; its artifact is `development/mail_pointer_transport_probe.json`. Starting
at the loop-return instruction alone (sequence 71) remains unverified because
that narrower interval lacks the selected ROM-bank context. The probe therefore
explicitly identifies its seed as the pre-loop pointer base. Automatic selection
and integration of this pointer proof into the complete causal chain remain
unfinished.

The investigation now selects that pointer context automatically and retains
both byte-dependency checks with the first matching HL-based SRAM store. It
requires identified MBC3, an observed pre-loop ROMX frame with the loop's base
pointer, the loop's final pointer at the store, a RAM-bank selection, and modeled
SRAM enable state. Unknown context, disabled SRAM, absolute-address stores, and
pointer mismatches omit this link. An overwrite or missing trace frame retains
the negative or incomplete dependency result without claiming a complete cause.

The new complete public run finished in 173.865 seconds, valid with no errors
and one source-mapped hypothesis. It contains input transport, the 17-iteration
loop, H/L dependencies from sequence 17 to 90, and the modeled zero store at
SRAM bank 0:`A91F`. Baseline/control fail and restoration passes the supplied
expectations; the label-only source rebuild passes. Artifacts are in
`development/mail_investigation_pointer_link/` and its adjacent full JSON report.
All 51 investigation, taint, and effect tests passed (72.069 seconds). This
integrates the diagnostic evidence; acceptance of a submitted causal explanation
against the independent whole-SRAM verifier remains a separate unfinished step.

Validation: 61 fixture, runtime-watch, runtime-experiment, instruction-capture, and investigation tests passed in 61.181 seconds. Compilation and scoped whitespace checks passed. Recording directories were checked to contain only state and input files.

The independent whole-SRAM verifier now also records callee entry, multiplier
entry, every pointer-loop iteration, and the fill call during each replay. It
checks the counter, stride, pointer, fill length, and zero value directly from
the emulator, without importing investigation verdicts. The broken case executes
17 iterations; restoration, wrong-slot control, and fixed source execute 2, 3,
and 2 respectively. The fixed entry additionally retains the slot in E.

All nine real replay checks pass, including the four exact whole-bank effects,
four pointer chains, and intended-contract contrast. The artifact is
`development/mail_pointer_chain_independent.json`. All 34 mail, Grass, fixture,
and evaluator tests passed (5.379 seconds). Regressions reject missing or
duplicated iterations, wrong counters, pointers, strides, fill values, and fill
lengths even when the final SRAM still matches. Hook preimage and duplicate-entry
errors are checked after ticking because PyBoy may swallow callback exceptions.
This verifies the observed arithmetic and resulting regression independently;
matching a submitted explanation and its references to this replay remains
unfinished, as does proving the initiating source mistake in that verifier.

The evaluator now observes the initiating caller state as well: A is 2 before
the bank load and 17 afterward. It verifies the six farcall instruction bytes
against the identity-checked ROM, checks checkpoint ordering across caller,
callee, loop and return, and retains their bank/PC locations. The four caller
checks pass alongside the previous nine replay checks.

`python -m tools.audit.root_cause_mail_verifier` now scores a submitted diagnosis
using the existing evaluator envelope. It checks the exact known source location,
invariant, intervention, one-frame recipe, and whole-bank regression contract.
Each of 23 cited instruction checkpoints must match fresh execution, including
registers, bank, PC, and the ROM opcode. Native first-frame-only trace identity is
supported; conflicting later identities are rejected. No submitted command or
success marker executes or substitutes for a replay check.

The assisted submission `development/mail_assisted_diagnosis.json` cites the
existing public `mail_investigation_pointer_link/capture_3.jsonl`, with the input
basis explicitly supplied by the evaluator author. The CLI result in
`development/mail_assisted_diagnosis_verification.json` reports solved=true,
autonomous=false, no problems, and all six diagnosis checks true. This is an
assisted development acceptance; the public runner has not emitted a complete
root-cause submission, and no blind evaluation gate has passed.

Rejection tests cover wrong source locations, stale identities, missing,
duplicated, reordered and forged citations, opcode mismatches, invalid sequences,
success-marker events, boolean register values, escaping artifact paths,
incomplete regression recipes, and downstream symptom-suppression interventions.
All 43 mail, Grass, fixture, and evaluator tests passed in 5.557 seconds. The
final real CLI replay passed after those checks; scoped whitespace checks passed.

The exported input now includes a source manifest containing only source paths,
content hashes, and their combined hash. The public investigation verifies it
before producing artifacts and again before returning; it does not read the
evaluator's commit metadata or accepted cause. Both existing mail exports were
revalidated before writing these manifests.

The new full public run `development/mail_investigation_source_basis_full.json`
finished in 158.419 seconds, valid with no errors. Its verified source-tree hash
matches the evaluator's independent identity and it retains the same one
source-mapped hypothesis at line 533. The failed baseline expectations remain
visible as passed=false; no complete diagnosis was emitted. This closes the
source-identity gap, not the remaining automatic submission and proof gaps.

All 63 fixture, mail, Grass, evaluator, and investigation tests passed in 60.228
seconds. The final expanded 10-test fixture suite also passed (6.906 seconds),
covering absent manifests, invalid paths and fields, changed or missing source,
changes during execution, and generated files outside the declared source set.
Compilation and scoped whitespace checks passed.

The public investigation now emits ordered instruction citations for its
farcall/counting-loop/write hypothesis. It selects the caller's before/after
bank-load states, callee and loop entries, each loop iteration, the active call
containing the first store, and the caller-return checkpoint. Selection requires
proved input and pointer dependencies, a complete ordered trace interval, and
matching stack positions. Missing or unverified links omit these citations;
they do not become a complete root-cause claim.

Evidence formatting also now preserves `scope.state_basis` exactly. It previously
removed the explicit empty `inputs.events` list, changing the captured identity.
Empty schedules, nested empty values, and explicit unknown values now survive
evidence normalization. Other cosmetic scope compaction remains unchanged.

The full public run `development/mail_investigation_causal_citations_full.json`
finished in 176.768 seconds, valid with no errors, retaining one hypothesis and
23 generated citations. Its state basis retains the empty event schedule.
The evaluator-authored wrapper `development/mail_generated_citation_submission.json`
uses the public source mapping, runtime/source identities, intervention, and
generated citations. Its invariant and whole-SRAM regression remain supplied by
the evaluator author. `mail_generated_citation_verification.json` reports all six
checks passing, solved=true, autonomous=false, and no problems. Declared citation
hashes are also checked before replay; stale hash tests reject before emulation.

All 71 evidence, investigation, effect, taint, and mail-verifier tests passed in
63.252 seconds. The final expanded citation/evidence tests passed (5 tests,
3.178 seconds), and all 15 mail-verifier tests passed (0.745 seconds). The new
rejection cases cover trace gaps, duplicates, ordering, mismatched return/fill
stack positions, absent fill calls or iteration evidence, killed dependencies,
and dependencies still marked unverified. Compilation and whitespace checks pass.

Hypothesis packets now link `reproducer` to their existing baseline experiment
and `regression` to the existing supplied-expectation file. Valid executed trials
carry the existing `replay_runtime_experiment` command, and investigation command
collection exposes those commands. No extra recipe format or CLI flag was added.
The uncertainty text explicitly limits the regression file to supplied
expectations; corrected-source regression and independent intent are not implied.

Unexecuted baselines and hypothesis trials now invalidate their reports. An
unexecuted shorter candidate cannot establish minimization, and invalid shorter
reports do not advertise replay commands. The new packet test failed before its
links existed; the unexecuted case also failed before the execution checks.
All 42 investigation, runtime-experiment, and mail-verifier tests passed in
58.061 seconds. The final two duration tests, expanded with unexecuted candidates,
passed in 2.729 seconds.

The existing real artifacts were replayed through the advertised CLI, then
checked with the existing expectation CLI. All three replayed their recordings
exactly; the baseline and wrong-slot control fail the three supplied expectations,
while restoration passes. Outputs are `development/mail_packet_*_replay.json`
and `mail_packet_*_expectations.json`. This verifies the reused replay/check path;
the full capture pipeline was not rerun for this artifact-linking change.

The standard Markdown and HTML report now places controlled hypotheses before
generic ranked findings. The overview shows the source location, reported proof
status, candidate intervention, observed register change and loop, modeled store,
citation count, artifact links, and uncertainty. It explicitly says this is not
a complete root-cause proof. The live investigation uses the same renderer, so
its aggregate controlled evidence no longer disappears from the human-readable
report merely because it was assembled after the component reports.

All 23 reporting and investigation tests passed in 57.091 seconds. Coverage
checks ordering, source paths resolved against the investigated source root,
Markdown and HTML artifact links, escaping, absence when there is no controlled
hypothesis, and retention of uncertainty. The existing real public capture was
rendered to `development/mail_report_overview.md` and `.html`; both show source
line 533, the 17-by-47 loop, bank-zero A91F store, and 23 citations. Compilation
and scoped whitespace checks passed. This display change does not promote the
hypothesis or establish any remaining autonomous evaluation gate.
