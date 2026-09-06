# Historical link-mail scan development witness

This is evaluator-owned evidence for an exposed historical defect. It is not a
blind corpus entry or an autonomous diagnostic result. Do not supply this file,
the evaluator harness, Git identity, or observations to the diagnostic runner.

## Source and build

Both exports contain tracked build inputs and a content-only source manifest.
The main checkout's assembly was not changed for this experiment.

| Side | Commit | Source tree SHA256 |
| --- | --- | --- |
| Broken | `2dda61ae8376178c71a0f516232d4ceaf051354c` | `C3EA6BBD23261EAD1D1E6033560C0EF8009D097DD63F7940086897D45305E70C` |
| Fixed | `c129c3b8201bb4922a0dd7676fcf524fe4fdaaaf` | `0FE9CA5876F109069A8D69279B42CF2CB47E06B9387F7BA0B624BB2BC67E7763` |

Exports live under `.local/tmp/root_cause_oracle/link_broken` and `link_fixed`.
Each `pokegold.gbc` built successfully with WSL `make -j4 PYTHON=python3` and
explicit `../../../../rgbds-1.0.1/{rgbasm,rgblink,rgbfix,rgbgfx}.exe` tools.
Build logs are adjacent to the export roots. No Silver build was needed for this
Gold-only witness.

## Observable contract and results

`Gen2ToGen2LinkComms` starts at its native `ld hl, wLinkOTMail` instruction,
before either scan. The staged input occupies the complete 390-byte region
`$CA84..$CC09`; `$CC0A` is the exclusive end. Interrupts are disabled in the
recording to isolate the parser. No ROM instructions are patched.

The harness checks every native `ld a, [hli]` checkpoint until the first
out-of-bounds read checkpoint or `.skip_mail`, including its address, input byte,
and loop identity. It checks contiguous reads from the buffer start and expected
loop transitions; a read count alone is insufficient.

| Input | Broken result | Fixed result |
| --- | --- | --- |
| 390 zero bytes, no preamble | 391st read checkpoint at `$CC0A`, loop 2 | 390 reads, `.skip_mail` |
| 390 preamble bytes (`$20`) | 391st read checkpoint at `$CC0A`, loop 3 | 390 reads, `.skip_mail` |
| One preamble then 389 no-data bytes (`$FE`) | 391st read checkpoint at `$CC0A`, loop 3 | 390 reads, `.skip_mail` |
| 389 zero bytes then a final-byte preamble | 391st read checkpoint at `$CC0A`, loop 3 | 390 reads, `.skip_mail` |

All eight states were replayed twice in fresh PyBoy instances, for sixteen
matching replays. Source manifests and ROM/symbol hashes are checked around
capture. Each recording contains only `initial.state` and `inputs.json`;
evaluator observations and identities remain outside those directories.

## Reproduction

From the repository root, with the two built exports, choose a new output path:

```powershell
python -m tools.audit.check_link_mail_search_rom .local/tmp/root_cause_oracle/link_broken .local/tmp/root_cause_oracle/link_fixed .local/tmp/root_cause_oracle/development/link_search_verified
```

That path already contains this run. Existing destinations are rejected without
modification. `evaluator_observations.json` holds all read checkpoints and the
ROM, symbol, backend, state, schedule, and source hashes. Twelve fixture tests
passed, including rejection of changed source and existing output before backend
startup. `git diff --check` passed.

## Remaining gaps

This proves only the malformed-buffer search behavior under staged parser input.
It does not establish that a live peer produces these buffers, gameplay
reachability, subsequent copying/decoding safety, or normal valid-mail behavior.
In particular, the later full-buffer copy is outside this witness's bounds claim.
The four inputs are variants of one mechanism, not four independent failures.
No causal intervention, accepted diagnosis, cross-backend gameplay comparison,
or independent review has been completed for this case. The blind pilot and
release-corpus gates remain open.

## Public investigation and capture fixes

The public `build_investigation_run` entry point received the broken ROM/source
export, saved state, and symptom: "A link trade can get stuck while receiving
malformed mail data." No function name, watch symbol, evaluator report, fix,
or bespoke proof command was supplied. This is still an assisted development
run because the symptom and staged recording were authored with the cause known.

The first run took 30.2 seconds and captured no instructions. The planner's
forward-target test used `target > next_pc`, so a branch to exactly the
instruction following an unconditional back edge incorrectly ended the walk.
Changing that comparison to `>=` preserves the exit block. A public trace-plan
regression failed before the change and passed afterward, with a no-forward-exit
control that still stops at the back edge. All 17 instruction-trace tests passed.
The historical parser plan grew from 92 to 224 instructions and now includes the
saved entry at `0A:4248`.

Dense capture then exposed a separate PyBoy frame-boundary stall. Two test
processes were stopped after repeated stack observations found them inside
`tick`; no completed replay was attributed to those runs. A bounded diagnostic
captured partial records but also timed out. A Python-source probe confirmed a
hook repeating at `0A:424E`, CPU cycle 42087712, with the frame already complete.
The narrowly scoped emulator correction, native build, regression test, archive
of the original backend, and audio limitation are documented in
[the backend patch notes](../../tools/trace/patches/README.md). The corrected
workspace backend and trace changes passed 37 runtime/instruction tests.

With both corrections, the same public investigation completed in 59.137 seconds.
Both captures contain the first out-of-bounds read checkpoint at sequence 1171:
`0A:424B`, `Gen2ToGen2LinkComms.loop2`, `HL=$CC0A`. Each trace hits the 4000-record
cap; neither is a complete execution history. Outputs are under
`.local/tmp/root_cause_oracle/development/link_public_native_frame_fix`, with the
aggregate report in the adjacent `link_public_native_frame_fix_full.json`.

The aggregate remains `valid=false`, `passed=false`, with no diagnosis evidence
atoms. Its remaining error is `no watchable replay target was found`: the early
watch replay runs before localization can supply a target. The later instruction
captures are valid and executed, but the investigator does not yet infer or
verify this missing search bound. Correct those integration/reasoning gaps before
claiming an accepted diagnosis. The saved recording is unchanged; the new capture
records the corrected backend hash instead of rewriting the older fixture's hash.
