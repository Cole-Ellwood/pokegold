# Boss AI Live Capture Ledger

Purpose: track real emulator/debugger captures for the post-patch Boss AI
priority fights. Static audits and source-path excerpts are already present;
this file tracks the remaining live WRAM capture work.

Status legend:

- `FINISHED`: live capture excerpt exists for this boss/scenario.
- `IN PROGRESS`: save-state/debugger setup exists, but the excerpt is not
  complete.
- `UNTOUCHED`: no boss-position save-state or live capture has been made yet.

Tooling status:

| Item | Status | Evidence |
| --- | --- | --- |
| Trace symbol address printout | `FINISHED` | `python tools\trace\boss_ai_trace_capture.py --symbols-only` |
| One-shot WRAM reader | `FINISHED` | `audit/boss_ai_trace/trace_helper_smoke.txt` |
| Polling watch mode | `FINISHED` | `audit/boss_ai_trace/trace_watch_smoke.txt` |
| State/RAM candidate probe | `FINISHED` | `python tools\trace\boss_ai_trace_state_probe.py --rom .local\do_now_morty_current\morty_live_attempt\pokegold_trace.gbc --boot-continue --expect-morty --strict` rejects raw stale Morty scratch RAM with `morty_candidate=FAIL`; the probe also rejects current-ROM debugger-warp states when copied SRAM has impossible active-player HP such as `64000/64000`. |
| Ledger audit | `FINISHED` | `python tools\audit\check_boss_ai_live_capture_ledger.py` |
| Capture manifest | `FINISHED` | `audit/boss_ai_trace/live_capture_manifest.json` pins the current trace ROM and symbol SHA256 hashes and owns the Morty `preflight.expect` guard. |
| Batch dry-run | `FINISHED` | `python tools\trace\boss_ai_trace_batch.py` reports missing save-states and uses manifest preflights before capture. |
| Live trainer state factory | `FINISHED` | `python tools\trace\boss_ai_state_factory.py --all --update-manifest` generates real map/script-created decision states for every trainer row in the manifest except the synthetic shared switch-loop scenario. |
| Morty proof-capsule attempt | `FINISHED` | `audit/boss_ai_trace/morty_proof_capsule_attempt_2026-04-26.md` records the earlier negative attempt and why old RAM was not accepted as proof. |
| Trainer boss-position save-states | `FINISHED` | `.local/tmp/boss_state_factory/*_chosen_frame_*.state` contains real map/script-created first-decision states for all 16 gym leaders, Koga, and Champion Lance. Shared switch-loop still needs a separate scenario fixture. |

Any boss row promoted to `FINISHED` must point to a capture excerpt with
`trace_rom`, `trace_rom_sha256`, `trace_symbols`, and `trace_symbols_sha256`
headers matching `audit/boss_ai_trace/live_capture_manifest.json`.

Gym-leader and priority boss live captures:

| Boss | Status | Required live checks | Output path |
| --- | --- | --- | --- |
| Falkner | `FINISHED` | `chosen_id=17`, `top_moves=WING_ATTACK:19,QUICK_ATTACK:19,MUD_SLAP:20`, `plan_id=3` | `audit/boss_ai_trace/falkner_live.txt` |
| Bugsy | `FINISHED` | `chosen_id=40`, `top_moves=TOXIC:19,POISON_STING:20,GIGA_DRAIN:20`, `plan_id=3` | `audit/boss_ai_trace/bugsy_live.txt` |
| Whitney | `FINISHED` | `chosen_id=104`, `top_moves=DOUBLE_TEAM:17,THUNDER_WAVE:19,DOUBLESLAP:20`, `plan_id=3` | `audit/boss_ai_trace/whitney_live.txt` |
| Morty | `FINISHED` | strict state preflight passes; current trace ROM excerpt has `chosen_id=101`, `top_moves=CURSE:20,NIGHT_SHADE:20,HYPNOSIS:37`, and `plan_id=2` | `audit/boss_ai_trace/morty_live.txt` |
| Chuck | `FINISHED` | `chosen_id=136`, `top_moves=HI_JUMP_KICK:19,ROCK_SLIDE:20,FORESIGHT:20`, `plan_id=2` | `audit/boss_ai_trace/chuck_live.txt` |
| Jasmine | `FINISHED` | real Olivine Gym battle has `chosen_id=85`, `top_moves=THUNDERBOLT:17,THUNDER_WAVE:17,LIGHT_SCREEN:20`, and `plan_id=3` | `audit/boss_ai_trace/jasmine_live.txt` |
| Pryce | `FINISHED` | `chosen_id=58`, `top_moves=ICE_BEAM:17,SURF:20,EXPLOSION:21`, `plan_id=2` | `audit/boss_ai_trace/pryce_live.txt` |
| Clair | `FINISHED` | `chosen_id=92`, `top_moves=TOXIC:18,EARTHQUAKE:20,WING_ATTACK:20`, `plan_id=3` | `audit/boss_ai_trace/clair_live.txt` |
| Brock | `FINISHED` | `chosen_id=57`, `top_moves=SURF:20,ICE_BEAM:20,PROTECT:20`, `plan_id=3` | `audit/boss_ai_trace/brock_live.txt` |
| Misty | `FINISHED` | `chosen_id=57`, `top_moves=HYPNOSIS:19,SURF:20,ICE_BEAM:20`, `plan_id=3` | `audit/boss_ai_trace/misty_live.txt` |
| Lt. Surge | `FINISHED` | `chosen_id=85`, `top_moves=THUNDERBOLT:16,THUNDER_WAVE:18,EXPLOSION:21`, `plan_id=3` | `audit/boss_ai_trace/lt_surge_live.txt` |
| Erika | `FINISHED` | `chosen_id=202`, `top_moves=GIGA_DRAIN:16,STUN_SPORE:19,REFLECT:20`, `plan_id=3` | `audit/boss_ai_trace/erika_live.txt` |
| Janine | `FINISHED` | `chosen_id=57`, `top_moves=SLUDGE_BOMB:20,SURF:20,EXPLOSION:21`, `plan_id=2` | `audit/boss_ai_trace/janine_live.txt` |
| Sabrina | `FINISHED` | `chosen_id=58`, `top_moves=ICE_BEAM:20,PSYCHIC_M:20,PERISH_SONG:20`, `plan_id=3` | `audit/boss_ai_trace/sabrina_live.txt` |
| Blaine | `FINISHED` | `chosen_id=174`, `top_moves=CURSE:20,FLAMETHROWER:20,ROCK_SLIDE:20`, `plan_id=3` | `audit/boss_ai_trace/blaine_live.txt` |
| Blue | `FINISHED` | `chosen_id=85`, `top_moves=THUNDERBOLT:16,ICE_BEAM:20,TRI_ATTACK:38`, `plan_id=3` | `audit/boss_ai_trace/blue_live.txt` |
| Koga | `FINISHED` | `chosen_id=188`, `top_moves=SLUDGE_BOMB:17,CURSE:18,TOXIC:28`, `plan_id=2` | `audit/boss_ai_trace/koga_live.txt` |
| Champion Lance | `FINISHED` | `chosen_id=200`, `top_moves=OUTRAGE:17,EARTHQUAKE:20,FIRE_BLAST:20`, `plan_id=3` | `audit/boss_ai_trace/champion_lance_live.txt` |
| Shared switch-loop | `UNTOUCHED` | A->B->A loop penalty and public emergency exceptions | `audit/boss_ai_trace/shared_switch_loop_live.txt` |

Recommended command once a boss-position PyBoy state exists:

```powershell
python tools\trace\boss_ai_trace_capture.py `
  --save-state path\to\before_lance_decision.state `
  --watch-frames 600 `
  --poll-every 1 `
  --boss "Champion Lance" `
  --notes "non-KO Hyper Beam bait" `
  --out audit\boss_ai_trace\champion_lance_live.txt
```

Manual debugger fallback:

```powershell
python tools\trace\boss_ai_trace_capture.py --symbols-only
```

Read the printed WRAM addresses at each boss AI decision point, then paste the
observed values into the matching `*_live.txt` file.
