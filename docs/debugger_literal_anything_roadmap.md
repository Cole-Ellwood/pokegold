# Debugger Literal-Anything Roadmap

**Status:** phases 0-6 built and verified; the gate is fail-closed by design,
so its verdict is a property of the *current working state*, not of this doc.
Run the gate for live truth — any ROM rebuild, source edit, or behavior change
voids evidence until the refresh pipeline below is re-run. Last full refresh:
2026-06-09 (after the trace-ROM rebuild and the boss-matchup branch's AI
changes; see "Refresh pipeline" and "Known residuals" below).
**Gate:** `python tools\audit\check_debugger_literal_anything.py --read-only --json`
**Baseline family:** `audit/debugger_literal_anything/`
**Predecessors:** [`debugger_godmode_spec.md`](debugger_godmode_spec.md),
[`debugger_unification_plan.md`](debugger_unification_plan.md), and
[`debugger_deity_mode_roadmap.md`](debugger_deity_mode_roadmap.md).

This roadmap is the next tier after the existing God and Deity debugger work.
Those earlier gates prove that the debugger can answer repo questions and can
self-drive selected runtime proofs. This roadmap is stricter: every reachable
ROM surface must be owned by a proof lane, stale evidence must fail closed, and
the final literal-anything gate must have no partial passes.

## Scope

Literal-anything means the debugger can start from an ordinary ROM question and
route it to a current proof surface for any reachable subsystem:

- source bytes, symbols, maps, scripts, text, movement, assets, and content
  mirrors
- battle damage, full-turn battle state, promoted mechanics, and Boss AI
- save format, SRAM banking, RTC, MBC transitions, and link/serial boundaries
- interrupts, DMA, timers, LCD/PPU state, VRAM/OAM/framebuffer, and audio/APU
- debugger front-door routing, report envelopes, command metadata, and artifact
  staleness

This is not permission for the debugger to edit ROM behavior. The debugger is a
read/index/replay/prove tool. It may write generated artifacts under `audit/`
or `.local/`; it must not change `engine/`, `data/`, `ram/`, `home/`, `maps/`,
`gfx/`, `audio/`, or other ROM source to make a proof pass.

## Current State

The gate reached `literal_anything_ready=True` with `blocking_gaps=[]` on
2026-06-04. That state was point-in-time: the 2026-06-04 trace-ROM rebuild,
the 2026-06-06 `pokegold.gbc` rebuild, and the boss-matchup branch's AI
changes voided evidence (fail-closed working as designed). The 2026-06-09
refresh pass re-proved every surface against the current build except the
named residuals below.

The literal-anything audit consumes the live Boss AI God report instead of
the older baseline bridge. Boss AI proof artifacts remain hash-basis checked:
stale counterfactual witness artifacts fail closed. Proof identity is
content-scoped (`source_tree_sha256` + artifact-dir-excluded dirty diff), so
committing already-validated evidence no longer voids it; any real source
change still does.

## Refresh pipeline (run after any ROM-affecting change)

1. Rebuild ROMs (gold/silver/debug + the trace variant; `run-suite
   --rebuild-roms` now builds the trace ROM explicitly).
2. `python tools\trace\boss_ai_state_factory.py --all
   --refresh-score-materialization-states --update-manifest`, then
   `python tools\trace\boss_ai_shared_switch_loop_fixture.py --update-manifest`.
   States must be regenerated BEFORE captures or the pre-choice replay audit
   diverges.
3. `python tools\trace\boss_ai_trace_batch.py --update-manifest-hashes --execute`.
4. `python -m tools.boss_ai_debugger run-suite --profile changed-ai
   --refresh-live-traces --refresh-rom-contribution-trace
   --refresh-rom-score-materialization`, then per-route contribution traces +
   the scope envelope and the pre-choice replay artifact (see
   `check_boss_ai_debugger_god` next_commands).
5. Re-run the gate's prescribed `next_command` for every stale surface
   (rom-index, replay surface family, damage fuzz/mutation, headless
   differentials) — the gate self-prescribes; harvest and execute.
6. Re-derive counterfactual witnesses that the AI change invalidated:
   `tools/boss_ai_debugger/witness_reexec.py` re-runs old witness contexts on
   the current ROM and credits only honest flips.

## Known residuals (2026-06-09)

- **~20 boss-AI counterfactual_flip witness roles** (of 806; 786 satisfied)
  remain `cataloged_missing_rom_proof`. Their old flip contexts no longer flip
  because the boss-matchup branch genuinely changed decision behavior
  (matchup-gated switches, lookahead cap). Clusters and unblock paths:
  faint-replacement rules need a regenerated faint-replacement predispatch
  fixture (no committed producer exists); haki-oracle rules need a regenerated
  haki entry state (same); adaptive-lead rules need a pre-lead battle-start
  context; six move-model edge rules need purpose-built scenario contexts.
- **Pre-choice replay audit** fails deterministically on Erika: the replay
  samples staged scoring internals (`pre_model_scores`, `plausible_mask`) at a
  different phase than the live capture while post-model scores and the chosen
  move agree. This is the audit's named known-gap ("until trace timing is
  stable") — a trace-tooling stabilization task, not an AI regression.

## Current Surface Matrix

| Surface | Current status | Missing evidence / blocker | Next command from gate |
| --- | --- | --- | --- |
| `unified_debugger_front_door` | complete | none | `python tools\audit\check_debugger_literal_anything.py --baseline --read-only` |
| `boss_ai_debugger` | runtime proven | none | `python tools\audit\check_boss_ai_debugger_god.py --read-only --json` |
| `headless_battle` | runtime proven with named unsupported scope | none | `python tools\audit\check_headless_battle_simulator.py` |
| `damage_debugger` | runtime proven | none | `python -m tools.damage_debugger.fuzz --max-examples=100 --workers=2 --json-out audit\damage_debugger\fuzz_no_divergence.json` |
| `script_map_content` | runtime proven | none | `python -m tools.debugger replay --surface script --at "map=ELMS_LAB and script=ProfElmScript" --frames 120 --json-out audit\debugger_literal_anything\script_vm_event_log.json` |
| `graphics_ui` | runtime proven with named PyBoy backend limit | none | `python -m tools.debugger replay --surface graphics --at "map=ECRUTEAK_GYM" --json-out audit\debugger_literal_anything\graphics_vram_oam_framebuffer_digest_parity.json` |
| `audio` | runtime proven with named PyBoy backend limit | none | `python -m tools.debugger replay --surface audio --at "cry(species=TYPHLOSION)" --frames 120 --json-out audit\debugger_literal_anything\audio_apu_event_envelope.json` |
| `save_rtc_mbc` | runtime proven with named RTC halt-freeze limit | none | `python tools\audit\check_save_format_version.py` |
| `interrupts_dma_timers_lcd` | runtime proven with named timing limit | none | `python -m tools.debugger trace-instructions --symbol VBlank --frames 60` |
| `link_serial_mystery_gift` | runtime proven with named link-peer limit | none | `python -m tools.debugger triage --symptom "link serial mystery gift"` |
| `rom_byte_index` | static proven | none | `python -m tools.debugger rom-byte --address 0E:542B` |

## Acceptance Bar

The roadmap is done only when:

1. `python tools\audit\check_debugger_literal_anything.py --read-only --json`
   reports `literal_anything_ready=True`, `proof_status=complete`, and
   `blocking_gaps=[]`.
2. `partial_pass_count=0`, or every intentionally incomplete surface is
   represented as `unsupported_with_reason` rather than `partial`.
3. `unowned_reachable_surface_count=0`, `unsupported_without_reason=0`,
   `stale_artifact_count=0`, and `side_effect_unknown_command_count=0`.
4. Backend divergence is either zero or explicitly recorded as a named,
   non-authoritative backend limitation. Timing-sensitive claims must name
   their backend.
5. Every generated proof artifact carries enough identity to fail closed when
   `pokegold.gbc`, `pokegold.sym`, source commit, map/symbol/index hashes, or
   dirty diff basis changes.
6. The existing floors still pass:
   - `python tools\audit\check_debugger_deity_mode.py --timeout 90`
   - `python tools\audit\check_boss_ai_debugger_god.py --read-only --json`
   - `python tools\audit\check_boss_ai_debugger_done.py`
   - `python -m tools.debugger selftest`
   - `python tools\audit\check_debugger_godmode_benchmark.py`
   - `python tools\audit\check_release_smoke.py`

## Phase 0 - Make The Gate Read Current Truth

Goal: remove false red from stale status plumbing before building new proof
surfaces.

Tasks:

1. Make `check_debugger_literal_anything.py` consume the current Boss AI God
   proof basis or refresh `audit/boss_ai_debugger/god_level_benchmark` through
   an explicit baseline command.
2. Collapse duplicate gate blockers:
   `no-partial-pass literal-anything gate is intentionally red` and
   `no_partial_pass_literal_anything_gate` should not count as two independent
   problems.
3. For each surface, distinguish:
   - missing proof
   - stale proof
   - proof exists but surface is still classified partial
   - unsupported with named reason
4. Add a tiny self-test for the scorer so a green Boss AI God report cannot be
   scored as stale/incomplete by the literal-anything gate.

Exit check:

```powershell
python tools\audit\check_debugger_literal_anything.py --read-only --json
```

Expected result: Boss AI is no longer a literal-anything blocker, unless the
current God gate itself is red.

## Phase 1 - Refresh Existing Runtime Artifacts

Goal: turn stale or old proof artifacts into current, hash-basis-stamped
artifacts before expanding scope.

Refresh these first:

- `audio_apu_event_envelope.json`
- `graphics_vram_oam_framebuffer_digest_parity.json`
- `script_vm_event_log.json`
- `script_map_content_materializers.json`
- `script_map_content_runtime_replays.json`
- `rtc_register_edge_runtime_replay.json`
- `mbc_runtime_transition_replay_corpus.json`
- `interrupt_entry_exit_runtime_event_stream.json`
- `dma_oam_vram_runtime_event_stream.json`
- `timer_lcd_mode_runtime_event_stream.json`
- `serial_transfer_runtime_event_stream.json`

Requirements:

- Every refreshed artifact records ROM hash, symbol hash, source commit, command
  line, backend, surface id, and input manifest or scenario id.
- If a replay cannot run, the artifact must be absent or explicitly failed; no
  placeholder success.
- The literal-anything audit must identify nested stale artifacts as blocking
  stale evidence, not hide them behind a top-level zero stale count.

Exit check:

```powershell
python tools\audit\check_debugger_literal_anything.py --baseline
python tools\audit\check_debugger_literal_anything.py --read-only --json
```

Expected result: no stale nested runtime artifacts remain.

## Phase 2 - Close Runtime Event Streams

Goal: every hardware/runtime surface has at least one replayed event stream with
source anchors and backend identity.

Work items:

1. Script VM: replay Elm script and at least one callback/object/warp case from
   the content materializer corpus.
2. Graphics: replay Ecruteak Gym or equivalent and capture framebuffer, VRAM,
   OAM, LCD mode/timing metadata, and digest parity.
3. Audio: replay cry, music, and SFX paths; capture APU register timelines and
   static-runtime match evidence.
4. RTC/MBC: replay day carry overflow, halt-bit control, RAM enable, ROM bank,
   SRAM/RTC select, and latch transitions.
5. Interrupt/DMA/timer/LCD: replay VBlank entry/exit, OAM DMA transfer, TIMA
   overflow/reload, and LCD STAT mode sequence.
6. Serial/link: replay internal-clock serial transfer and record why external
   two-process link or Mystery Gift flow is supported, unsupported, or
   deferred.

Exit check:

```powershell
python tools\audit\check_debugger_literal_anything.py --read-only --json
```

Expected result: none of these blockers remain: `script_vm_event_log`,
`vram_oam_framebuffer_digest_parity`, `apu_register_event_stream`,
`rtc_halt_carry_day_overflow_runtime_replays`,
`mbc_runtime_transition_replay_corpus`, `interrupt_entry_exit_runtime_event_stream`,
`dma_oam_vram_runtime_event_stream`, `timer_lcd_mode_runtime_event_stream`, and
`serial_transfer_runtime_event_stream`.

## Phase 3 - Cross-Backend Honesty

Goal: claims that depend on graphics, audio, timing, or hardware event order are
not silently PyBoy-only.

Tasks:

1. Run or refresh `graphics_crossemu_backend_preflight.json`.
2. Add equivalent backend labels for audio and timing-sensitive event streams.
3. For each unavailable backend, record a machine-readable unsupported reason:
   missing executable, missing automation API, nondeterministic backend, or
   intentionally out of local scope.
4. If a backend is available, compare digests/events against PyBoy or record a
   named divergence with source and runtime evidence.

Exit check:

```powershell
python tools\audit\check_debugger_literal_anything.py --read-only --json
```

Expected result: `backend_divergence_count=0`, or every divergence is demoted
from blocker to documented non-authoritative limitation by explicit policy.

## Phase 4 - Finish Battle/Headless Full-Turn Coverage

Goal: close the promoted-mechanic turn-level gap without weakening the already
strong damage and Boss AI proof lanes.

Tasks:

1. Inventory the promoted mechanics that still lack ROM turn-level
   differentials.
2. Generate or promote canonical turn boards for each missing mechanic.
3. Run component and turn-level ROM differentials; store artifacts under
   `audit/headless_battle/` or the existing literal-anything artifact path.
4. Keep damage-core fuzz and mutation campaigns green.

Exit check:

```powershell
python tools\audit\check_headless_battle_simulator.py
python tools\audit\check_debugger_literal_anything.py --read-only --json
```

Expected result: `remaining_promoted_mechanic_turn_differentials` is gone.

## Phase 5 - Promote Partial Surfaces To Final Status

Goal: stop using `partial` as a success state.

Tasks:

1. Define final statuses in the literal-anything scorer:
   - `complete`
   - `runtime_proven`
   - `static_proven`
   - `unsupported_with_reason`
   - `missing_evidence`
   - `stale_evidence`
2. Convert `damage_debugger` and `rom_byte_index` from partial to complete or
   static/runtime-proven based on their current evidence.
3. Convert `unified_debugger_front_door` to complete only when all other
   reachable surfaces are non-partial.
4. Keep command side-effect taxonomy strict: no unknown or destructive commands
   are allowed into the read-only proof flow.

Exit check:

```powershell
python tools\audit\check_debugger_literal_anything.py --read-only --json
```

Expected result: `partial_pass_count=0`.

## Phase 6 - Final Literal-Anything Definition Of Done

Goal: one command proves the whole ROM debugger surface honestly.

Tasks:

1. Add a concise human report for the final gate under
   `audit/debugger_literal_anything/final_<date>.md`.
2. Make the gate write a machine-readable final report with every surface,
   evidence id, artifact path, backend, stale basis, next command, and
   unsupported reason if any.
3. Add the final roadmap pointer to `docs/project_roadmap.md` after the gate is
   green.
4. Run the full verification floor.

Final command:

```powershell
python tools\audit\check_debugger_literal_anything.py --baseline
```

Whole-roadmap done means the follow-up read-only command is also green:

```powershell
python tools\audit\check_debugger_literal_anything.py --read-only --json
```

## First Slice Recommendation

Start with Phase 0. It is small and prevents wasted work: the current literal
gate is partly red because it has not ingested the current Boss AI God proof.
Once the gate reports only real non-Boss-AI blockers, attack Phase 1 stale
runtime artifacts in this order:

1. Script VM and script/map content, because they carry the largest static-only
   gap.
2. Hardware event streams, because interrupt/DMA/timer/LCD proof unlocks
   graphics and timing claims.
3. Audio and graphics backend parity, because those are user-visible and
   emulator-sensitive.
4. Headless promoted mechanics, because it is self-contained and should not
   disturb script/audio/graphics work.

Do not declare "entire ROM" complete until the literal-anything gate is green.
The Boss AI God result is a completed slice inside this larger roadmap, not the
whole destination.
