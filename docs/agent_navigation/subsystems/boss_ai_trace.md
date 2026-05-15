# Boss AI Trace Micro-Index

Use this when the task asks for live proof, trace captures, Boss AI evidence,
Morty proof status, or remaining boss-position capture gaps.

## Fast Route

| Need | Go to |
| --- | --- |
| Current live-capture status | `audit/boss_ai_trace/live_capture_ledger.md` |
| Batch capture inputs | `audit/boss_ai_trace/live_capture_manifest.json` |
| Live trainer state factory | `tools/trace/boss_ai_state_factory.py` |
| Capture command behavior | `docs/boss_ai_trace_capture.md` |
| Candidate state preflight | `tools/trace/boss_ai_trace_state_probe.py` |
| Morty state/proof notes | `audit/boss_ai_trace/morty_state_needed_2026-04-26.md` |
| Jasmine state/proof notes | `audit/boss_ai_trace/jasmine_state_needed_2026-04-26.md` |
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
- Trace fields including chosen move, top scores, pre/post move-model scores,
  plausible masks, and revealed move bitmap when relevant.
- Matching ledger and manifest updates.

Not enough by itself:

- static no-cheat audits;
- source-path excerpts;
- old `.local/` RAM sidecars;
- a trace helper symbol printout;
- a batch dry-run that reports `MISSING_STATE`.

## Current Status

All current manifest rows are `FINISHED`. The 16 gym leaders plus Koga and
Champion Lance have first-turn live chosen-move proof on the current trace ROM.
Their accepted artifacts are the matching `audit/boss_ai_trace/*_live.txt`
files, produced from `.local/tmp/boss_state_factory/*_chosen_frame_*.state`,
and each has nonzero `chosen_id` plus manifest-matching trace ROM/symbol
hashes.

`shared_switch_loop` is covered separately by
`tools/trace/boss_ai_shared_switch_loop_fixture.py`, because it is not a single
map trainer. Red is not currently in the manifest; add a manifest row and a
factory route only if that capture becomes a real target.

## Capture Path

1. Build or identify the current trace ROM and symbols.
2. Read `docs/boss_ai_trace_capture.md` section `Morty Attempt Lessons` before
   trusting old PyBoy scratch states. The cycle4 frame-161 and delta-263 states
   are historical clues, not current proof.
3. For real trainers, use the state factory before writing scratch drivers:

```powershell
python tools\trace\boss_ai_state_factory.py --all --update-manifest
```

   For one trainer, use `--boss <manifest_id> --update-manifest`.
   The factory reaches the real map room and lets the trainer's own
   `loadtrainer` / `startbattle` script create battle RAM.
4. Create a separate boss-position/scenario save-state for unfinished
   non-trainer scenarios.
5. For Morty candidates, probe the state before trusting it:

```powershell
python tools\trace\boss_ai_trace_state_probe.py --save-state path\to\before_morty_decision.state --expect-morty --strict
```

6. Add the state path to the matching entry in
   `audit/boss_ai_trace/live_capture_manifest.json`. Keep any scenario-specific
   `preflight.expect` guard. Do not invent `--expect-morty` for non-Morty
   captures; the batch runner owns whatever preflight exists in the manifest.
7. Run a targeted capture. The batch runner preflights guarded states before
   reporting `READY` or writing live output:

```powershell
python tools\trace\boss_ai_trace_batch.py --execute --only jasmine
python tools\audit\check_boss_ai_live_capture_ledger.py
```

8. Update `audit/boss_ai_trace/live_capture_ledger.md`.
9. Update `docs/project_roadmap.md` only after the evidence exists.

## Priority IDs

Use the manifest IDs exactly:

| ID | Boss | Output |
| --- | --- | --- |
| `falkner` | Falkner | `audit/boss_ai_trace/falkner_live.txt` |
| `bugsy` | Bugsy | `audit/boss_ai_trace/bugsy_live.txt` |
| `whitney` | Whitney | `audit/boss_ai_trace/whitney_live.txt` |
| `morty` | Morty | `audit/boss_ai_trace/morty_live.txt` |
| `chuck` | Chuck | `audit/boss_ai_trace/chuck_live.txt` |
| `jasmine` | Jasmine | `audit/boss_ai_trace/jasmine_live.txt` |
| `pryce` | Pryce | `audit/boss_ai_trace/pryce_live.txt` |
| `clair` | Clair | `audit/boss_ai_trace/clair_live.txt` |
| `brock` | Brock | `audit/boss_ai_trace/brock_live.txt` |
| `misty` | Misty | `audit/boss_ai_trace/misty_live.txt` |
| `lt_surge` | Lt. Surge | `audit/boss_ai_trace/lt_surge_live.txt` |
| `erika` | Erika | `audit/boss_ai_trace/erika_live.txt` |
| `janine` | Janine | `audit/boss_ai_trace/janine_live.txt` |
| `sabrina` | Sabrina | `audit/boss_ai_trace/sabrina_live.txt` |
| `blaine` | Blaine | `audit/boss_ai_trace/blaine_live.txt` |
| `blue` | Blue | `audit/boss_ai_trace/blue_live.txt` |
| `koga` | Koga | `audit/boss_ai_trace/koga_live.txt` |
| `champion_lance` | Champion Lance | `audit/boss_ai_trace/champion_lance_live.txt` |
| `shared_switch_loop` | Shared switch-loop | `audit/boss_ai_trace/shared_switch_loop_live.txt` |

## Verification

Use `docs/agent_navigation/verification_matrix.md` row
`Boss AI live trace artifact`. If source changed, also use its `Boss AI logic`
row and build both ROMs. If only docs or trace ledger files changed, do not
claim gameplay behavior changed.

For all-gym-leader source coverage, run
`python tools\audit\check_gym_leader_wiring.py` alongside the tier/items/moves
audits. That check proves each leader's map script reaches the expected trainer
data through `TrainerGroups`, each party row uses real species/item/move
constants, and each class has the expected name, attributes, DVs, pic, palette,
and encounter music support. It also checks badge/reward aftermath, including
Clair's separate Dragon's Den RisingBadge route, and battle-resource rows for
leader species, moves, held items, and reward items. The same check verifies
gym map registration, leader object placement, and subordinate gym-trainer
sweep events; it still is not a live battle trace.
