# Morty State Needed - 2026-04-26

Purpose: unblock `MEGAURGENT-001` without mistaking stale scratch RAM for live
Boss AI proof.

This file is not evidence that Morty is proven. It names the exact runtime
artifact still missing.

## Current Search Result

This command found no PyBoy `.state` files under the usual trace/audit/scratch
areas during this free-roam cycle:

```powershell
rg --files .local audit outbox | rg "(?i)\.state$"
```

Many `.gbc.ram` sidecars exist under `.local/`, especially
`.local/do_now_morty_current/` and `.local/boss_ai_trace_probe/`. Those are route
and failure clues, not accepted proof. Existing notes show they either miss a
usable Morty context or carry invalid copied player data such as impossible
active HP.

## Required Artifact

Provide or create a PyBoy-compatible save-state made against the current
`pokegold_trace.gbc` / `pokegold_trace.sym` basis pinned in
`audit/boss_ai_trace/live_capture_manifest.json`.

The state should be at a Morty battle decision point, not merely:

- Ecruteak Gym coordinates;
- a loaded Morty map object before battle;
- the battle intro;
- a sidecar `.gbc.ram` file copied beside a ROM.

Minimum requirements:

- `wBattleMode` is in trainer battle context for Morty, or the strict probe can
  otherwise prove the expected Morty context.
- The active player Pokemon has sane species, level, HP, and max HP.
- The state can advance far enough for Boss AI trace fields to become nonzero
  during capture.
- The trace ROM and symbol hashes match the manifest.

Probe before trusting it:

```powershell
python tools\trace\boss_ai_trace_state_probe.py --save-state path\to\before_morty_decision.state --expect-morty --strict
```

A `morty_candidate=PASS` result is necessary, but still not sufficient. The
capture must also produce nonzero Boss AI trace fields.

## Capture Path

1. Add the accepted save-state path to the `morty` entry in
   `audit/boss_ai_trace/live_capture_manifest.json`.
2. Confirm the batch runner reaches `READY`:

```powershell
python tools\trace\boss_ai_trace_batch.py --only morty
```

3. Capture Morty only:

```powershell
python tools\trace\boss_ai_trace_batch.py --execute --only morty
```

4. Validate the ledger:

```powershell
python tools\audit\check_boss_ai_live_capture_ledger.py
```

5. Update `audit/boss_ai_trace/live_capture_ledger.md` and
   `docs/project_roadmap.md` only after `audit/boss_ai_trace/morty_live.txt`
   exists and the ledger audit accepts it.

## Do Not Repeat

- Do not point `save_state` at a `.gbc.ram` sidecar.
- Do not remove `preflight.expect = morty` from the manifest to make dry-run
  output prettier.
- Do not count `audit/boss_ai_trace/morty.txt` as live proof; it is source-path
  evidence, not a boss-position capture.
- Do not accept a state that stalls in send-out or shows broken player HP such
  as `00/0` or `64000/64000`.
