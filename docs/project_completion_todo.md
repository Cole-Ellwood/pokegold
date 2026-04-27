# Project Completion Todo

Purpose: execution checklist for the current "get it all done" sweep. This is
not source truth and not a replacement for `docs/project_roadmap.md`; it is the
working list future sessions should update while closing the remaining proof and
feel gaps.

## Status Rules

Use these exact status values:

- `TODO`: not started.
- `DOING`: actively being worked.
- `DONE_NEEDS_DOUBLE_CHECK`: implementation or evidence exists, but a second
  verification pass is still required.
- `DOUBLE_CHECKED`: done and independently checked by the command/manual proof
  named in the row.
- `BLOCKED`: cannot continue without missing state, missing tooling, unclear
  source truth, or user input.

Rule: when a task looks finished, mark it `DONE_NEEDS_DOUBLE_CHECK` first. Only
promote it to `DOUBLE_CHECKED` after the listed double-check has actually run
and the evidence path has been updated.

## Sweep Checklist

| ID | Task | Status | What done means | Double-check required before `DOUBLE_CHECKED` | Evidence / files to update |
| --- | --- | --- | --- | --- | --- |
| TODO-001 | Correct stale Opus recommendation note | `DOUBLE_CHECKED` | `audit/opus_review_recommendations_2026-04-26.md` matches current repo truth: clean tracked source, all listed boss first-decision captures finished except `shared_switch_loop`, and no stale "Morty/Jasmine only" claim remains. | `python tools\audit\check_navigation_floor.py` passed after the edit; `audit/boss_ai_trace/live_capture_ledger.md` and `git status --short --branch` were re-read. | `audit/opus_review_recommendations_2026-04-26.md`; this file. |
| TODO-002 | Build shared switch-loop live trace fixture | `DOUBLE_CHECKED` | A dedicated scenario proves the A->B->A switch-loop penalty and public emergency exceptions without pretending it is a normal trainer-route state factory case. | `python tools\audit\check_boss_ai_live_capture_ledger.py`, Boss AI invariants/no-cheat/memory, release smoke, docs navigation, normal Gold/Silver build, trace rebuild, and full manifest recapture passed. `audit/boss_ai_trace/shared_switch_loop_live.txt` was inspected for matching hashes and `switch_context=param=31,index=00,last_out=02,cooldown=02,cur_ot=00`. | `engine/battle/ai/boss.asm`; `tools/trace/boss_ai_shared_switch_loop_fixture.py`; `tools/trace/boss_ai_trace_capture.py`; `audit/boss_ai_trace/shared_switch_loop_live.txt`; `audit/boss_ai_trace/live_capture_ledger.md`; `audit/boss_ai_trace/live_capture_manifest.json`; `docs/project_roadmap.md`. |
| TODO-003 | Run focused manual emulator feel checks | `DOUBLE_CHECKED` | A short manual pass records Repel renewal accept/decline feel, HM-tool acquisition/use/backfill feel, Earl/early-rule communication text rendering, and one real boss/trainer loss fairness note. | Re-run relevant source audits after any source fix caused by the manual pass; otherwise have a second read of the audit note confirm each claimed check says what was actually tested and what was not. | New `audit/manual_feel_checks_2026-04-27.md`; `docs/project_roadmap.md` rows `VERIFY-001`, `DIFFICULTY-001`, `QOL-001`, and `COMM-001` if their proof gaps change. |
| TODO-004 | Choose exactly one forward improvement lane | `DOUBLE_CHECKED` | After proof/feel gaps above are stable, choose one: `FARFETCH_D`, `ARIADOS`, `YANMA`, or Morty-only gym scout dossier prototype. Record why that lane is the best next move before editing source. | Confirm the choice against `docs/project_roadmap.md`, `docs/balance_intent.md`, `docs/buff_backlog.md`, and/or `docs/boss_ai_spec.md` so the lane is not solving a stale problem. | `docs/project_roadmap.md`; lane-specific doc or audit note. |
| TODO-005 | Prototype Morty-only gym scout dossier if selected | `TODO` | Ecruteak-only prototype records coarse public facts from gym-trainer battles, shows the player an inspectable dossier before Morty, and lets Morty's AI use only those public facts. No all-gym rollout. | Run source-relevant audits, build Gold/Silver, and do a manual fairness read: the player must be able to understand what Morty knows before the fight. Mark `DONE_NEEDS_DOUBLE_CHECK` until both audit/build and manual fairness review are recorded. | Likely `docs/project_roadmap.md` row `BOSSAI-002`; source files chosen during implementation; new audit/handoff note. |

## Final Verification Floor

Before this sweep can be called closed:

- `python tools\audit\check_release_smoke.py`
- `python tools\audit\check_docs_navigation.py`
- `python tools\audit\check_boss_ai_live_capture_ledger.py`
- `git diff --check`
- WSL Gold/Silver build if any source file changed:

```powershell
bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
```

Record any manual emulator gap plainly. Do not convert source/audit evidence
into a claim of playtest proof.
