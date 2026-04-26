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
| Morty proof-capsule attempt | `FINISHED` | `audit/boss_ai_trace/morty_proof_capsule_attempt_2026-04-26.md` records the earlier negative attempt and why old RAM was not accepted as proof. |
| Boss-position save-states | `IN PROGRESS` | Morty's recorded state `.local/tmp/morty_issue_cycle8/chosen_frame_3086.state` passes strict Morty preflight, and Jasmine's factory-generated state `.local/tmp/boss_state_factory/jasmine_chosen_frame_5060.state` produced a completed chosen-move excerpt; other gym-leader save-state paths plus Koga/Lance/shared-switch paths are still unrecorded. |

Any boss row promoted to `FINISHED` must point to a capture excerpt with
`trace_rom`, `trace_rom_sha256`, `trace_symbols`, and `trace_symbols_sha256`
headers matching `audit/boss_ai_trace/live_capture_manifest.json`.

Gym-leader and priority boss live captures:

| Boss | Status | Required live checks | Output path |
| --- | --- | --- | --- |
| Falkner | `UNTOUCHED` | early-tier gym leader opener; accuracy/speed pressure; no adaptive lead | `audit/boss_ai_trace/falkner_live.txt` |
| Bugsy | `UNTOUCHED` | early-tier gym leader pressure; Bug/Flying role bias; no adaptive lead | `audit/boss_ai_trace/bugsy_live.txt` |
| Whitney | `UNTOUCHED` | early-tier gym leader pressure; normal-type tempo and setup checks; no adaptive lead | `audit/boss_ai_trace/whitney_live.txt` |
| Morty | `FINISHED` | strict state preflight passes; current trace ROM excerpt has `chosen_id=95`, `top_moves=HYPNOSIS:1,CURSE:20,NIGHT_SHADE:20`, and `plan_id=2` | `audit/boss_ai_trace/morty_live.txt` |
| Chuck | `UNTOUCHED` | mid-tier adaptive-lead gym leader; Fighting role bias and setup pressure | `audit/boss_ai_trace/chuck_live.txt` |
| Jasmine | `FINISHED` | real Olivine Gym battle has `chosen_id=85`, `top_moves=THUNDERBOLT:17,THUNDER_WAVE:17,LIGHT_SCREEN:20`, and `plan_id=3` | `audit/boss_ai_trace/jasmine_live.txt` |
| Pryce | `UNTOUCHED` | late-tier adaptive-lead gym leader; Ice/Ground role bias and weather/setup planning | `audit/boss_ai_trace/pryce_live.txt` |
| Clair | `UNTOUCHED` | first-turn Spikes; Thunder Wave fail gates; Spikes+Roar; +2 setup punish | `audit/boss_ai_trace/clair_live.txt` |
| Brock | `UNTOUCHED` | late-tier adaptive-lead Kanto gym leader; Rock/Ground pressure and switch reasoning | `audit/boss_ai_trace/brock_live.txt` |
| Misty | `UNTOUCHED` | late-tier adaptive-lead Kanto gym leader; Water pressure and public threat handling | `audit/boss_ai_trace/misty_live.txt` |
| Lt. Surge | `UNTOUCHED` | late-tier adaptive-lead Kanto gym leader; Electric pressure and immunity-aware play | `audit/boss_ai_trace/lt_surge_live.txt` |
| Erika | `UNTOUCHED` | late-tier adaptive-lead Kanto gym leader; Grass status/recovery pressure | `audit/boss_ai_trace/erika_live.txt` |
| Janine | `UNTOUCHED` | late-tier adaptive-lead Kanto gym leader; Poison status fail gates and setup denial | `audit/boss_ai_trace/janine_live.txt` |
| Sabrina | `UNTOUCHED` | late-tier adaptive-lead Kanto gym leader; Psychic pressure and public threat handling | `audit/boss_ai_trace/sabrina_live.txt` |
| Blaine | `UNTOUCHED` | late-tier adaptive-lead Kanto gym leader; Fire pressure and weather/setup reasoning | `audit/boss_ai_trace/blaine_live.txt` |
| Blue | `UNTOUCHED` | late-tier adaptive-lead Kanto gym leader; mixed-team switch and public threat reasoning | `audit/boss_ai_trace/blue_live.txt` |
| Koga | `UNTOUCHED` | first-turn Spikes; Toxic fail gates; +2 setup Haze | `audit/boss_ai_trace/koga_live.txt` |
| Champion Lance | `UNTOUCHED` | non-KO Hyper Beam avoidance; Spikes+Roar; immunity pivot preference | `audit/boss_ai_trace/champion_lance_live.txt` |
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
