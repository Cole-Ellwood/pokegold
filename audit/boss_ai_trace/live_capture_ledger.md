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
| Ledger audit | `FINISHED` | `python tools\audit\check_boss_ai_live_capture_ledger.py` |
| Capture manifest | `FINISHED` | `audit/boss_ai_trace/live_capture_manifest.json` |
| Batch dry-run | `FINISHED` | `python tools\trace\boss_ai_trace_batch.py` reports missing save-states. |
| Boss-position save-states | `UNTOUCHED` | No Morty/Jasmine/Clair/Koga/Lance save-state paths recorded yet. |

Priority boss live captures:

| Boss | Status | Required live checks | Output path |
| --- | --- | --- | --- |
| Morty | `UNTOUCHED` | revealed coverage species isolation; status fail gates; +2 setup Haze | `audit/boss_ai_trace/morty_live.txt` |
| Jasmine | `UNTOUCHED` | first-turn Spikes; status fail gates; Spikes+Roar; +2 setup punish | `audit/boss_ai_trace/jasmine_live.txt` |
| Clair | `UNTOUCHED` | first-turn Spikes; Thunder Wave fail gates; Spikes+Roar; +2 setup punish | `audit/boss_ai_trace/clair_live.txt` |
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
