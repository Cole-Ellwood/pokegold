# Boss AI Trace Capture

## Canonical Trace Build Command

Use this command for Boss AI trace builds:

```bash
make -j4 RGBDS=rgbds-1.0.1/ pokegold.gbc DEFINES="-D BOSS_AI_TRACE"
```

Build interface note:
- `Makefile` now appends `DEFINES` to `RGBASMFLAGS`, so the command above is the canonical trace entrypoint.

## Where Trace Output Appears (Actual Behavior)

`BOSS_AI_TRACE` does not print to stdout, file logs, serial, or in-game text.
It writes trace fields into WRAM symbols only:
- `wBossAITraceTopMoves`
- `wBossAITraceTopScores`
- `wBossAITraceChosenMove`
- `wBossAITraceSwitchConfidence`
- `wBossAITracePlanId`
- `wBossAITracePlanPhase`
- `wBossAITracePlanConfidence`
- `wBossAITracePlausibleMask`
- `wBossAITraceRiskFlags`
- `wBossAITraceLookaheadBonusTop`

`wBossAITraceRiskFlags` bit meanings:
- bit 0: plausible-risk / scout trigger logic fired
- bit 1: scout move was chosen (Protect/Substitute branch)
- bit 2: scout pivot switch branch fired

Practical capture method:
- run a trace ROM in an emulator with memory/debugger access;
- read these WRAM symbols at decision points;
- export/save the observed values as text excerpts.

Helper script:

```powershell
python tools\trace\boss_ai_trace_capture.py --symbols-only
```

Use `--symbols-only` for debugger addresses. If a PyBoy save-state is available
at a boss AI decision point, pass it with `--save-state` and write the formatted
WRAM excerpt with `--out`.

Before treating a save-state or battery-RAM sidecar as boss-position proof,
probe it:

```powershell
python tools\trace\boss_ai_trace_state_probe.py --save-state path\to\before_morty_decision.state --expect-morty --strict
```

For old scratch ROM folders that rely on a `.gbc.ram` sidecar, use:

```powershell
python tools\trace\boss_ai_trace_state_probe.py --rom .local\path\to\pokegold_trace.gbc --boot-continue --expect-morty --strict
```

Do not accept a Morty candidate unless the probe prints `morty_candidate=PASS`.
`map=04:07` and `coords=x=5,y=2` are not enough by themselves; a failed
`morty_map_object_missing` verdict means the state has Ecruteak Gym coordinates
but no usable Morty object/battle context.

The probe also prints `player_active`. Treat impossible active-player values as
fatal. A current-ROM debugger warp using copied stale SRAM reached Morty's map
object, but the copied party had `hp=64000/64000`, collapsed to `00/0` in the
battle intro, and was rejected as `player_party_invalid`. A boss-position state
must have both the boss context and a sane active player Pokemon.

The manifest owns this requirement with `preflight.expect = morty`. The batch
runner turns that manifest field into the same strict probe before printing
`READY` or running capture. A bad Morty state is `INVALID_STATE`, not live
proof.

Formatted live excerpts include `trace_rom`, `trace_rom_sha256`,
`trace_symbols`, and `trace_symbols_sha256` header fields. The ledger audit
checks those fields for any row marked `FINISHED`, so every accepted capture is
tied back to the exact trace ROM and symbol file that produced it.

To poll for decision changes from a boss-position save-state:

```powershell
python tools\trace\boss_ai_trace_capture.py `
  --save-state path\to\before_decision.state `
  --watch-frames 600 `
  --poll-every 1 `
  --boss "Champion Lance" `
  --out audit\boss_ai_trace\champion_lance_live.txt
```

The live capture status ledger is:
- `audit/boss_ai_trace/live_capture_ledger.md`

Validate the ledger with:

```powershell
python tools\audit\check_boss_ai_live_capture_ledger.py
```

Configured batch captures live in:
- `audit/boss_ai_trace/live_capture_manifest.json`

The manifest pins the trace ROM and symbol file by SHA256. If you rebuild
`pokegold_trace.gbc` or `pokegold_trace.sym`, update those hashes before using
the batch runner or ledger audit.

The `morty` entry must keep its `preflight.expect` field set to `morty`.
Do not remove it just to make a dry-run print `READY`; that field is the guard
against stale Ecruteak Gym RAM being mistaken for boss proof.

Dry-run the configured captures:

```powershell
python tools\trace\boss_ai_trace_batch.py
```

Once save-states are filled into the manifest, run:

```powershell
python tools\trace\boss_ai_trace_batch.py --execute
```

## Boss Capture Checklist

For the post-release-safety boss AI patch, read
`docs/boss_ai_post_patch_notes.md` before capture. It lists the exact behavior
checks added by the patch and the manual RGBDS build fallback used when `make`
is unavailable.

Capture at least one full battle trace for each target:
- Falkner
- Whitney
- Morty
- Elite Four (at minimum one member; preferred all four)
- Champion (Lance)

Post-patch priority set:
- Morty
- Jasmine
- Clair
- Koga
- Champion (Lance)

Post-patch scenarios to capture:
- revealed Ice Punch or equivalent coverage does not transfer to another player
  species;
- A->B->A switch-loop penalty fires unless an emergency exception applies;
- first-turn Spikes gets lead bias only when not under immediate public
  pressure;
- status moves are discouraged into visible fail states;
- Spikes plus Roar/Whirlwind responds to repeated switching or setup pressure;
- public +2 setup is answered by denial moves when no immediate KO is available;
- immunity pivot preference beats a merely neutral pivot when the public threat
  type supports it.

## Trace Excerpt Storage

Save excerpts under:
- `audit/boss_ai_trace/<boss>.txt`

Recommended filenames:
- `audit/boss_ai_trace/falkner.txt`
- `audit/boss_ai_trace/whitney.txt`
- `audit/boss_ai_trace/morty.txt`
- `audit/boss_ai_trace/e4_will.txt` (or per-member variants)
- `audit/boss_ai_trace/champion_lance.txt`
