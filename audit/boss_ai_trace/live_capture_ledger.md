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
| Exact selector replay audit | `FINISHED` | `python tools\audit\check_boss_ai_selector_replay.py` validates exact `wEnemyMonMoves`, `wEnemyAIMoveScores`, `wBossAITier`, and chosen move bytes for all `*_live.txt` captures. |
| Pre-choice ROM replay audit | `FINISHED` | `python tools\audit\check_boss_ai_pre_choice_replay.py` replays every real-trainer `pre_choice_state` through the trace ROM, compares the replayed trace fields to the baseline live trace, then validates exact selector fields and chosen move bytes. |
| Capture manifest | `FINISHED` | `audit/boss_ai_trace/live_capture_manifest.json` pins the current trace ROM and symbol SHA256 hashes and owns the Morty `preflight.expect` guard. |
| Batch dry-run | `FINISHED` | `python tools\trace\boss_ai_trace_batch.py` reports missing save-states and uses manifest preflights before capture. |
| Live trainer state factory | `FINISHED` | `python tools\trace\boss_ai_state_factory.py --all --update-manifest` generates real map/script-created decision states for every real trainer row in the manifest. |
| Morty proof-capsule attempt | `FINISHED` | `audit/boss_ai_trace/morty_proof_capsule_attempt_2026-04-26.md` records the earlier negative attempt and why old RAM was not accepted as proof. |
| Trainer boss-position save-states | `FINISHED` | `.local/tmp/boss_state_factory/*_chosen_frame_*.state` contains real map/script-created first-decision states for all 16 gym leaders, Koga, and Champion Lance. |
| Shared switch-loop fixture | `FINISHED` | `tools/trace/boss_ai_shared_switch_loop_fixture.py --update-manifest` writes `.local/tmp/boss_state_factory/shared_switch_loop_frame_200.state` from a real Jasmine battle state, then verifies `switch_confidence=80`, proposed target `2`, last switched-out `2`, cooldown `2`, switch index `0`, and threshold `74 -> 84`. |

Any boss row promoted to `FINISHED` must point to a capture excerpt with
`trace_rom`, `trace_rom_sha256`, `trace_symbols`, and `trace_symbols_sha256`
headers matching `audit/boss_ai_trace/live_capture_manifest.json`.

Gym-leader and priority boss live captures:

| Boss | Status | Required live checks | Output path |
| --- | --- | --- | --- |
| Falkner | `FINISHED` | exact selector replay: `tier=1`, `cur_enemy_move_id=16`, `chosen_slot=2`, `move_scores=20,19,19,19` | `audit/boss_ai_trace/falkner_live.txt` |
| Bugsy | `FINISHED` | exact selector replay: `tier=1`, `cur_enemy_move_id=141`, `chosen_slot=3`, `move_scores=20,20,19,19` | `audit/boss_ai_trace/bugsy_live.txt` |
| Whitney | `FINISHED` | exact selector replay: `tier=1`, `cur_enemy_move_id=104`, `chosen_slot=2`, `move_scores=49,19,16,19` | `audit/boss_ai_trace/whitney_live.txt` |
| Morty | `FINISHED` | strict state preflight passes; exact selector replay: `tier=2`, `cur_enemy_move_id=174`, `chosen_slot=2`, `move_scores=18,44,19,19` | `audit/boss_ai_trace/morty_live.txt` |
| Chuck | `FINISHED` | exact selector replay: `tier=2`, `cur_enemy_move_id=136`, `chosen_slot=1`, `move_scores=16,16,17,17` | `audit/boss_ai_trace/chuck_live.txt` |
| Jasmine | `FINISHED` | exact selector replay: `tier=2`, `cur_enemy_move_id=86`, `chosen_slot=2`, `move_scores=15,14,14,17` | `audit/boss_ai_trace/jasmine_live.txt` |
| Pryce | `FINISHED` | exact selector replay: `tier=2`, `cur_enemy_move_id=191`, `chosen_slot=0`, `move_scores=18,20,19,38` | `audit/boss_ai_trace/pryce_live.txt` |
| Clair | `FINISHED` | exact selector replay: `tier=3`, `cur_enemy_move_id=252`, `chosen_slot=0`, `move_scores=13,20,17,20` | `audit/boss_ai_trace/clair_live.txt` |
| Brock | `FINISHED` | exact selector replay: `tier=3`, `cur_enemy_move_id=182`, `chosen_slot=3`, `move_scores=14,20,20,17` | `audit/boss_ai_trace/brock_live.txt` |
| Misty | `FINISHED` | exact selector replay: `tier=3`, `cur_enemy_move_id=240`, `chosen_slot=0`, `move_scores=13,22,20,23` | `audit/boss_ai_trace/misty_live.txt` |
| Lt. Surge | `FINISHED` | exact selector replay: `tier=3`, `cur_enemy_move_id=86`, `chosen_slot=2`, `move_scores=17,13,12,37` | `audit/boss_ai_trace/lt_surge_live.txt` |
| Erika | `FINISHED` | exact selector replay: `tier=3`, `cur_enemy_move_id=202`, `chosen_slot=1`, `move_scores=23,16,19,23` | `audit/boss_ai_trace/erika_live.txt` |
| Janine | `FINISHED` | exact selector replay: `tier=3`, `cur_enemy_move_id=229`, `chosen_slot=0`, `move_scores=23,23,20,23` | `audit/boss_ai_trace/janine_live.txt` |
| Sabrina | `FINISHED` | exact selector replay: `tier=3`, `cur_enemy_move_id=115`, `chosen_slot=1`, `move_scores=14,14,44,17` | `audit/boss_ai_trace/sabrina_live.txt` |
| Blaine | `FINISHED` | exact selector replay: `tier=3`, `cur_enemy_move_id=191`, `chosen_slot=0`, `move_scores=18,20,14,20` | `audit/boss_ai_trace/blaine_live.txt` |
| Blue | `FINISHED` | exact selector replay: `tier=3`, `cur_enemy_move_id=161`, `chosen_slot=1`, `move_scores=50,9,12,16` | `audit/boss_ai_trace/blue_live.txt` |
| Koga | `FINISHED` | exact selector replay: `tier=3`, `cur_enemy_move_id=92`, `chosen_slot=1`, `move_scores=17,13,20,20` | `audit/boss_ai_trace/koga_live.txt` |
| Champion Lance | `FINISHED` | exact selector replay: `tier=3`, `cur_enemy_move_id=252`, `chosen_slot=3`, `move_scores=20,21,17,13` | `audit/boss_ai_trace/champion_lance_live.txt` |
| Shared switch-loop | `FINISHED` | exact selector replay: `tier=2`, `cur_enemy_move_id=191`, `chosen_slot=0`, `move_scores=20,38,38,38`; switch context remains `param=31,index=00,last_out=02,cooldown=02,cur_ot=00` | `audit/boss_ai_trace/shared_switch_loop_live.txt` |

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
