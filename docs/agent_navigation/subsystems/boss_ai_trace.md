# Boss AI Trace Micro-Index

Use this when the task asks for live proof, trace captures, Boss AI evidence,
Morty proof status, or remaining boss-position capture gaps.

## Fast Route

| Need | Go to |
| --- | --- |
| Current live-capture status | `audit/boss_ai_trace/live_capture_ledger.md` |
| Batch capture inputs | `audit/boss_ai_trace/live_capture_manifest.json` |
| Capture command behavior | `docs/boss_ai_trace_capture.md` |
| Candidate state preflight | `tools/trace/boss_ai_trace_state_probe.py` |
| Morty state/proof notes | `audit/boss_ai_trace/morty_state_needed_2026-04-26.md` |
| Post-patch behavior targets | `docs/boss_ai_post_patch_notes.md` |
| Earlier blocked proof attempt | `audit/boss_ai_trace/morty_proof_capsule_attempt_2026-04-26.md` |
| Capture helper code | `tools/trace/boss_ai_trace_capture.py`, `tools/trace/boss_ai_trace_batch.py` |
| Ledger audit | `tools/audit/check_boss_ai_live_capture_ledger.py` |

## What Counts As Proof

A live Boss AI proof needs a current trace ROM basis, a boss-position state or
manual debugger position, public battle context, nonzero trace fields at a
decision point, and a short fairness read explaining why the decision follows
public information.

Acceptable evidence:

- `*_live.txt` file under `audit/boss_ai_trace/` produced from a current trace
  ROM state or manually recorded debugger position.
- Trace fields including chosen move, top scores, plausible masks, and revealed
  move bitmap when relevant.
- Matching ledger and manifest updates.

Not enough by itself:

- static no-cheat audits;
- source-path excerpts;
- old `.local/` RAM sidecars;
- a trace helper symbol printout;
- a batch dry-run that reports `MISSING_STATE`.

## Current Status

Morty is `FINISHED` for the first live proof capsule. The accepted current-ROM
artifact is `audit/boss_ai_trace/morty_live.txt`, produced from
`.local/tmp/morty_issue_cycle8/chosen_frame_3086.state`; it has
`chosen_id=95`, `top_moves=HYPNOSIS:1,CURSE:20,NIGHT_SHADE:20`, `plan_id=2`,
and manifest-matching trace ROM/symbol hashes.

Remaining live-proof gaps are Jasmine, Clair, Koga, Champion Lance, Red if
added to the manifest later, and the shared switch-loop scenario. Do not mark
any of those finished from static audits, source excerpts, old `.local/` RAM,
or a dry-run alone.

## Capture Path

1. Build or identify the current trace ROM and symbols.
2. Read `docs/boss_ai_trace_capture.md` section `Morty Attempt Lessons` before
   trusting old PyBoy scratch states. The cycle4 frame-161 and delta-263 states
   are historical clues, not current proof.
3. Create a boss-position save-state at a decision point for the unfinished
   boss/scenario.
4. Probe the candidate state before trusting it:

```powershell
python tools\trace\boss_ai_trace_state_probe.py --save-state path\to\before_morty_decision.state --expect-morty --strict
```

5. Add the state path to the matching entry in
   `audit/boss_ai_trace/live_capture_manifest.json`. Keep any scenario-specific
   `preflight.expect` guard.
6. Run a targeted capture. The batch runner preflights guarded states before
   reporting `READY` or writing live output:

```powershell
python tools\trace\boss_ai_trace_batch.py --execute --only jasmine
python tools\audit\check_boss_ai_live_capture_ledger.py
```

7. Update `audit/boss_ai_trace/live_capture_ledger.md`.
8. Update `docs/project_roadmap.md` only after the evidence exists.

## Priority IDs

Use the manifest IDs exactly:

| ID | Boss | Output |
| --- | --- | --- |
| `morty` | Morty | `audit/boss_ai_trace/morty_live.txt` |
| `jasmine` | Jasmine | `audit/boss_ai_trace/jasmine_live.txt` |
| `clair` | Clair | `audit/boss_ai_trace/clair_live.txt` |
| `koga` | Koga | `audit/boss_ai_trace/koga_live.txt` |
| `champion_lance` | Champion Lance | `audit/boss_ai_trace/champion_lance_live.txt` |
| `shared_switch_loop` | Shared switch-loop | `audit/boss_ai_trace/shared_switch_loop_live.txt` |

## Verification

Use `docs/agent_navigation/verification_matrix.md` row
`Boss AI live trace artifact`. If source changed, also use its `Boss AI logic`
row and build both ROMs. If only docs or trace ledger files changed, do not
claim gameplay behavior changed.
