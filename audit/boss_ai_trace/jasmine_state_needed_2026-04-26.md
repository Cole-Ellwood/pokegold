# Jasmine State Needed - 2026-04-26

Purpose: record the Jasmine live Boss AI trace attempt without mistaking a
synthetic scratch harness for live boss-position proof.

## Current Accepted Proof

Jasmine is now `FINISHED` in the live capture ledger. The accepted live capture
is:

```text
audit/boss_ai_trace/jasmine_live.txt
```

The accepted PyBoy state is:

```text
.local/tmp/boss_state_factory/jasmine_chosen_frame_4520.state
```

Current verified evidence:

- `python tools\trace\boss_ai_trace_batch.py --only jasmine` reports `READY`.
- `python tools\trace\boss_ai_trace_batch.py --execute --only jasmine` writes
  `audit/boss_ai_trace/jasmine_live.txt`.
- `python tools\trace\boss_ai_trace_state_probe.py --save-state .local\tmp\boss_state_factory\jasmine_chosen_frame_4520.state --objects 4 --object-structs 3`
  shows `battle_mode=2`, `other_trainer=class=06,id=01`, `map=01:02`, and
  Jasmine loaded as object struct 1.
- The live excerpt has manifest-matching trace hashes:
  `trace_rom_sha256=ECE0411C1730CD3720D1E0DC05653949ABBA2E8375800FBBA0ED1F7A86F5B040`
  and
  `trace_symbols_sha256=C9C0469A9045C15906BAFE2A334927D8A13E7E818FF51CA11885AAE17B022F8E`.
- The decision fields are nonzero:
  `top_moves=THUNDERBOLT:20,THUNDER_WAVE:20,LIGHT_SCREEN:20`,
  `chosen=THUNDERBOLT`, `chosen_id=85`, `plan_id=1`,
  `plan_confidence=2`, and `plausible_mask=33 02 20 8a`.

## What Was Verified

Static/source invariants still pass:

```powershell
python tools\audit\check_boss_ai_trace_invariants.py
```

The passing invariant set includes Jasmine-relevant coverage for:

- first-turn Spikes pressure gate
- public status fail gates
- Spikes plus phazing pressure response
- public +2 setup denial

The live ledger audit also passes after promotion:

```powershell
python tools\audit\check_boss_ai_live_capture_ledger.py
```

That audit correctly reports:

```text
Jasmine: FINISHED (audit/boss_ai_trace/jasmine_live.txt)
```

## Scratch Harness Attempt

A synthetic Jasmine state was created under ignored scratch space:

```text
.local/tmp/jasmine_live_probe/jasmine_injected_start.state
```

The state was made by injecting Jasmine trainer/battle RAM into a known sane
Morty in-battle state. Its probe shape is useful for debugging but not live
proof:

```text
battle_mode=2
other_trainer=class=06,id=01
map=04:07
```

The trainer fields say Jasmine, but the map/script context is still the Morty
donor battle. That mismatch is why this state must not be added to
`audit/boss_ai_trace/live_capture_manifest.json`.

A scratch direct-AI probe was also created:

```text
.local/tmp/jasmine_ai_direct_probe.py
```

It loads the injected state and jumps into the real trace ROM's `AIChooseMove`
entrypoint. It reached real Boss AI planning state (`plan_id=3`,
`plan_confidence=76`) but did not produce a completed chosen-move trace:

```text
top_moves=NO_MOVE:0,NO_MOVE:0,NO_MOVE:0
chosen=NO_MOVE
chosen_id=0
```

This is evidence that the scratch harness is not clean enough. It is not
evidence that Jasmine's real fight crashes.

## What Actually Unblocked It

`tools/trace/boss_ai_state_factory.py` created the accepted state without
stitching fake trainer battle RAM. It boots the trace ROM from copied
`pokegold.sav`, sets only the story/object flags needed for real Olivine Gym
Jasmine visibility, enters Olivine Gym through map setup, talks to Jasmine's
real script, and waits for `wBossAITraceChosenMove != 0`.

The first failed factory attempt was useful: Jasmine's map object existed but
was masked because the event parser missed `const_next` in
`constants/event_flags.asm`, so it cleared the wrong visibility flag. The fixed
factory parser resolves `EVENT_OLIVINE_GYM_JASMINE` to `$06d3`, matching the
event flag stored in the Olivine Gym map object.

The source-path Jasmine excerpt remains:

```text
audit/boss_ai_trace/jasmine.txt
```

That file supports the design checks, but it is not live proof.

## Capture Path

Run the current proof capsule:

```powershell
python tools\trace\boss_ai_state_factory.py --boss jasmine
python tools\trace\boss_ai_trace_batch.py --only jasmine
python tools\trace\boss_ai_trace_batch.py --execute --only jasmine
python tools\audit\check_boss_ai_live_capture_ledger.py
```

## Do Not Repeat

- Do not count `.local/tmp/jasmine_live_probe/jasmine_injected_start.state` as
  live proof.
- Do not count `.local/tmp/jasmine_ai_direct_probe.py` output as live proof.
- Do not point the manifest at a stitched state whose trainer fields say
  Jasmine but whose map/script context is still Morty.
- Do not simplify the state factory event parser so it ignores `const_next`;
  that exact mistake leaves Jasmine masked in Olivine Gym.
