# Boss AI Trace Capture

## Boss AI Cognition Mode

Traces are how strange boss ideas earn trust. Stare at the position, imagine the
meanest fair human line, journal the branch, then use this document to capture
whether the ROM actually chose for legal reasons.

## Canonical Trace Build Command

The capture tools default to `pokegold_trace.gbc` and `pokegold_trace.sym`.
When those exact artifacts need to be refreshed, use the explicit trace rebuild:

```bash
bash -lc 'rgbds-1.0.1/rgbasm.exe -Weverything -Wtruncation=1 -Q8 -P includes.asm -D _GOLD -D BOSS_AI_TRACE -o main_gold_trace.o main.asm && rgbds-1.0.1/rgbasm.exe -Weverything -Wtruncation=1 -Q8 -P includes.asm -D _GOLD -D BOSS_AI_TRACE -o ram_gold_trace.o ram.asm && rgbds-1.0.1/rgblink.exe -Weverything -Wtruncation=1 -l layout.link -n pokegold_trace.sym -m pokegold_trace.map -o pokegold_trace.gbc audio_gold.o home_gold.o main_gold_trace.o ram_gold_trace.o data/text/common_gold.o data/maps/map_data_gold.o data/pokemon/egg_moves_gold.o data/pokemon/evos_attacks_gold.o engine/movie/credits_gold.o engine/overworld/events_gold.o gfx/misc_gold.o gfx/sprites_gold.o gfx/tilesets_gold.o data/pokemon/dex_entries_gold.o gfx/pics_gold.o && rgbds-1.0.1/rgbfix.exe -Weverything -cjsv -k 01 -l 0x33 -m MBC3+TIMER+RAM+BATTERY -r 3 -p 0 -t POKEMON_GLD -i AAUE pokegold_trace.gbc && tools/stadium pokegold_trace.gbc'
```

Build interface note:
- `Makefile` appends `DEFINES` to `RGBASMFLAGS`, but `make ... pokegold.gbc
  DEFINES="-D BOSS_AI_TRACE"` refreshes the normal-named ROM, not the
  capture-tool default `pokegold_trace.gbc`.

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

## Live State Factory Easy Path

Use this path for real trainer live proof before inventing any battle-RAM
stitching. The factory only edits overworld/story state enough to enter the
real map room, then it talks to the trainer and lets that trainer's own
`loadtrainer` / `startbattle` script create battle RAM.

Generate all supported trainer decision states and write their paths into the
manifest:

```powershell
python tools\trace\boss_ai_state_factory.py --all --update-manifest
```

Generate one trainer only:

```powershell
python tools\trace\boss_ai_state_factory.py --boss clair --update-manifest
```

The factory writes:

- decision states under `.local/tmp/boss_state_factory/*_chosen_frame_*.state`
- per-route logs under `.local/tmp/boss_state_factory/*_state_factory.log`
- `.local/tmp/boss_state_factory/manifest_hints.json`

The route table lives in `tools/trace/boss_ai_state_factory.py`. Each route is
deliberately small: manifest id, map constant, player tile in front of the
leader, trainer class/id, event flags to clear or set, and optional scene bytes
for maps that would otherwise run an entry cutscene. If a new trainer is added,
copy an existing `BossRoute` and use the map script's real `object_event` and
`loadtrainer` line as source truth.

Then dry-run the manifest:

```powershell
python tools\trace\boss_ai_trace_batch.py
```

If the target row is `READY`, run the capture:

```powershell
python tools\trace\boss_ai_trace_batch.py --execute --only clair
```

Or run every ready manifest row:

```powershell
python tools\trace\boss_ai_trace_batch.py --execute
```

Only promote a manifest/ledger row to `FINISHED` after the matching
`audit/boss_ai_trace/*_live.txt` exists and has nonzero decision evidence. Real
trainer first-decision rows should have nonzero `chosen_id`; switch-only
scenario rows like `shared_switch_loop` may instead use nonzero
`switch_confidence` plus `switch_context`. The factory's `--update-manifest`
option intentionally does not promote status; it only fills `save_state`,
`stop_after_first_capture`, and `require_chosen_move`, and it should not
downgrade an already-finished row.

As of 2026-04-26, the factory supports all real trainer rows currently in the
manifest: the 16 gym leaders, Koga, and Champion Lance. It does not generate
the `shared_switch_loop` scenario, because that needs a synthetic repeated
switch setup rather than a single map trainer.

For `shared_switch_loop`, use:

```powershell
python tools\trace\boss_ai_shared_switch_loop_fixture.py --update-manifest
python tools\trace\boss_ai_trace_batch.py --execute --only shared_switch_loop
```

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

## Morty Attempt Lessons

These details saved the 2026-04-26 follow-up from false proof:

- Morty's map object is object index 2, not 1. `object_const_def` starts map
  object constants at 2, and `maps/EcruteakGym.asm` puts Morty in
  `map_object_2`.
- Loaded object structs are `$28` bytes wide. Using `$29` shifts later object
  reads and makes valid object data look broken.
- A candidate state can pass the Morty map/object preflight and still fail as
  live proof. For completed move-decision proof, `plan_id` alone is not enough;
  prefer `chosen_id != 0`, with nonzero top moves as the weaker useful signal.
- The original Morty route was not player move selection. From
  `.local/tmp/free_roam_morty_cycle3/morty_battle_sane_no_trace_step_043.state`,
  press `A` four times with 45-frame waits, then continue in the same PyBoy
  process. The plan-only breadcrumb is
  `.local/tmp/morty_issue_cycle4/a_taps_trace_frame_0161.state`. The later
  delta-263 state reached top moves but not an accepted chosen move on the
  current stricter proof gate.
- The first accepted Morty proof state was
  `.local/tmp/morty_issue_cycle8/chosen_frame_3086.state`. The current manifest
  uses the regenerable real-script factory state
  `.local/tmp/boss_state_factory/morty_chosen_frame_5646.state`. Both depend on
  the repaired cursor bugs in `engine/battle/ai/boss.asm`:
  `BossAI_CheckTypeMatchupNoItem` must preserve the TypeMatchups table cursor
  around multiply/divide work, and `BossAI_GetTypeThreatSeverityVsEnemyMon`
  must preserve the plausible-threat list cursor around the known-defense
  adjustment helper.
- If PyBoy driving seems to hang, check whether the script is simply running at
  real-time speed. After `load_state`, call `pyboy.set_emulation_speed(0)` in
  scratch drivers, and write progress to a file under `.local/tmp/` when the
  shell will not return buffered output until process exit.
- Do not use the frame-161 Morty state as final manifest proof. It is a
  plan-only snapshot with `plan_id=2`/`plan_confidence=72` but zero
  top-move/chosen-move fields. Use it as a diagnostic breadcrumb.
- Do not use the delta-263 state as final proof either. It was the useful wrong
  turn: top moves existed, but the accepted tooling requires a nonzero chosen
  move. The current manifest records the factory chosen state instead.
- When a battle stalls before a trace appears, save a screenshot/BMP from the
  current frame. The Morty scratch attempt looked close until the screen showed
  broken player state during send-out.

The manifest owns this requirement with `preflight.expect = morty`. The batch
runner turns that manifest field into the same strict probe before printing
`READY` or running capture. A bad Morty state is `INVALID_STATE`, not live
proof.

If the dry-run reports `INVALID_STATE` only because PyBoy cannot import from
`.local\pydeps` or those dependency folders are access-denied in a sandbox,
rerun the preflight with dependency access before judging the state. On
2026-04-26, the same Morty manifest entry reported `READY` once the batch runner
could read the local PyBoy dependency folders.

The capture helper disables PyBoy real-time pacing before state load and watch
loops. If an inline scratch driver imports `boss_ai_trace_state_probe.py` with
`importlib`, register the module in `sys.modules` before `exec_module`; otherwise
the `@dataclass` decorator can fail under Python 3.14.

Formatted live excerpts include `trace_rom`, `trace_rom_sha256`,
`trace_symbols`, and `trace_symbols_sha256` header fields. The ledger audit
checks those fields for any row marked `FINISHED`, so every accepted capture is
tied back to the exact trace ROM and symbol file that produced it.

When `--require-chosen-move` is used, a watch that never observes nonzero
`chosen_id` must exit nonzero instead of writing a `no_captures=true` file as
if the run succeeded.

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

Current first-decision live proof status:
- all 16 gym leaders: captured
- Koga: captured
- Champion Lance: captured
- shared switch-loop: captured with a dedicated switch-confidence fixture

The all-trainer captures are smoke proof that the current trace ROM reaches the
Boss AI decision path through real map scripts and records a nonzero chosen
move. They are not exhaustive proof for every behavior branch below.

Post-patch priority scenarios still worth richer targeted captures:
- Morty
- Jasmine
- Clair
- Koga
- Champion Lance

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
- `audit/boss_ai_trace/falkner_live.txt`
- `audit/boss_ai_trace/whitney_live.txt`
- `audit/boss_ai_trace/morty_live.txt`
- `audit/boss_ai_trace/koga_live.txt`
- `audit/boss_ai_trace/champion_lance_live.txt`
