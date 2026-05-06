# Morty State Needed - 2026-04-26

Purpose: record the Morty live Boss AI trace unblock without mistaking stale
scratch RAM for live Boss AI proof.

This file began as the missing-state checklist. It is now the accepted-state
note for the first live proof capsule.

## Current Accepted Proof

Morty is `FINISHED` for `MEGAURGENT-001`. The accepted live capture is:

```text
audit/boss_ai_trace/morty_live.txt
```

The accepted PyBoy state is:

```text
.local/tmp/boss_state_factory/morty_chosen_frame_5466.state
```

Current verified evidence:

- `python tools\trace\boss_ai_trace_state_probe.py --save-state .local\tmp\boss_state_factory\morty_chosen_frame_5466.state --expect-morty --strict` passes.
- `python tools\trace\boss_ai_trace_batch.py --execute --only morty` writes
  `audit/boss_ai_trace/morty_live.txt`.
- `python tools\audit\check_boss_ai_live_capture_ledger.py` accepts Morty as
  `FINISHED`.
- The live excerpt has manifest-matching trace hashes:
  `trace_rom_sha256=ECE0411C1730CD3720D1E0DC05653949ABBA2E8375800FBBA0ED1F7A86F5B040`
  and
  `trace_symbols_sha256=C9C0469A9045C15906BAFE2A334927D8A13E7E818FF51CA11885AAE17B022F8E`.
- The decision fields are nonzero:
  `top_moves=DREAM_EATER:20,CURSE:20,NIGHT_SHADE:20`, `chosen=DREAM_EATER`,
  `chosen_id=138`, `plan_id=1`, `plan_confidence=2`, and
  `plausible_mask=33 02 20 8a`.

## What Actually Fixed It

The wrong turn was thinking the driver needed more input after top moves
appeared. The stricter proof gate was right: top moves alone were not a
completed move decision.

The live blocker was source-level cursor corruption in public-threat reads:

- `BossAI_CheckTypeMatchupNoItem` used `hl` as the `TypeMatchups` table cursor,
  then called math helpers that clobbered it before the scan loop continued.
- `BossAI_GetTypeThreatSeverityVsEnemyMon` returned through
  `BossAI_AdjustThreatSeverityForEnemyKnownDefense` without preserving the
  plausible-threat list cursor in `hl`.

`engine/battle/ai/boss.asm` now preserves those cursors, and
`tools/audit/check_boss_ai_trace_invariants.py` has static guards for both
hazards.

The later all-trainer state factory replaced the older cycle8 Morty state in
the manifest. It reaches Ecruteak Gym through real map setup, talks to Morty,
lets `loadtrainer MORTY, MORTY1` / `startbattle` create battle state, and saves
only after `wBossAITraceChosenMove != 0`.

## Historical Breadcrumbs

Ignored `.local/tmp` states are real. Plain `rg --files` respects ignore rules,
so use this when local scratch states matter:

```powershell
rg --files --no-ignore .local audit outbox | rg "(?i)\.state$"
```

Useful but non-final states:

```text
.local/tmp/free_roam_morty_cycle3/morty_battle_sane_no_trace_step_043.state
.local/tmp/morty_issue_cycle4/a_taps_trace_frame_0161.state
.local/tmp/morty_issue_cycle4/a_taps_completed_trace_delta_263.state
.local/tmp/morty_issue_cycle8/chosen_frame_3086.state
```

The first state is a sane Morty trainer battle before trace fields are written.
The frame-161 state is plan-only: `plan_id=2`, `plan_confidence=72`, and no
move choice. The delta-263 state reached top moves, but the current proof gate
requires nonzero `chosen_id`; do not use it as final proof. The cycle8 state
was the first accepted completed proof, but the manifest now uses the
regenerable real-script factory state instead.

## Capture Path

Run the current proof capsule:

```powershell
python tools\trace\boss_ai_trace_batch.py --only morty
python tools\trace\boss_ai_trace_batch.py --execute --only morty
python tools\audit\check_boss_ai_live_capture_ledger.py
```

If rebuilding trace artifacts, update
`audit/boss_ai_trace/live_capture_manifest.json` hashes before using the batch
runner or ledger audit.

## Do Not Repeat

- Do not point `save_state` at a `.gbc.ram` sidecar.
- Do not remove `preflight.expect = morty` from the manifest to make dry-run
  output prettier.
- Do not count `audit/boss_ai_trace/morty.txt` as live proof; it is source-path
  evidence, not a boss-position capture.
- Do not promote plan-only or top-move-only evidence. Morty's accepted proof has
  nonzero `chosen_id`.
- Do not accept a state that stalls in send-out or shows broken player HP such
  as `00/0` or `64000/64000`.
