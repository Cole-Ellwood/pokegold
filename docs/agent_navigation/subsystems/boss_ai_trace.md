# Boss AI Trace Micro-Index

Use this when the task asks for live proof, trace captures, Boss AI evidence, or
the currently blocked Morty proof capsule.

## Fast Route

| Need | Go to |
| --- | --- |
| Current live-capture status | `audit/boss_ai_trace/live_capture_ledger.md` |
| Batch capture inputs | `audit/boss_ai_trace/live_capture_manifest.json` |
| Capture command behavior | `docs/boss_ai_trace_capture.md` |
| Post-patch behavior targets | `docs/boss_ai_post_patch_notes.md` |
| Current blocker narrative | `audit/boss_ai_trace/morty_proof_capsule_attempt_2026-04-26.md` |
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

## Current Blocker

`MEGAURGENT-001` is blocked because no valid current-ROM Morty boss-position
PyBoy state is recorded. The old scratch RAM can place the player near Morty but
does not load a usable Morty object table or boss decision trace.

Do not mark Morty finished until `audit/boss_ai_trace/morty_live.txt` exists and
`python tools\audit\check_boss_ai_live_capture_ledger.py` accepts it.

## Capture Path

1. Build or identify the current trace ROM and symbols.
2. Create a boss-position save-state at a decision point.
3. Add the state path to the matching entry in
   `audit/boss_ai_trace/live_capture_manifest.json`.
4. Run a targeted capture:

```powershell
python tools\trace\boss_ai_trace_batch.py --execute --only morty
python tools\audit\check_boss_ai_live_capture_ledger.py
```

5. Update `audit/boss_ai_trace/live_capture_ledger.md`.
6. Update `docs/project_roadmap.md` only after the evidence exists.

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
