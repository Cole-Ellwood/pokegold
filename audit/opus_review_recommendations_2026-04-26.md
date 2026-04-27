# Opus Review Recommendations - 2026-04-26

Purpose: preserve the external Opus 4.6 recommendation sheet as an actionable
repo checklist. This file is an index, not source truth. If anything here
conflicts with current source, linker output, generated audit output, or
`docs/project_roadmap.md`, trust the live source truth and update this file.

Source artifact: `C:\Users\lolno\Downloads\pokemon_gold_hack_recommendation_sheet.svg`.

Current verification note: this file began as a snapshot of an older external
review sheet, then was refreshed after later proof work. Treat the tables below
as current only when they agree with `git status --short --branch`,
`audit/boss_ai_trace/live_capture_ledger.md`, and `docs/project_roadmap.md`.

## Critical Checks

| Opus item | Current repo status | Source-truth route | Next action |
| --- | --- | --- | --- |
| Commit or stage the dirty files | Old warning satisfied for tracked source before this completion sweep. The current worktree may still contain this sweep's docs/proof edits; re-run `git status --short --branch` before high-risk source work. | `git status --short --branch`; `docs/project_roadmap.md` row `VERIFY-001`; `docs/agent_navigation/subsystems/checkpoint_handoff.md` | Do not stage blindly. If the sweep grows, checkpoint logical groups after verification. |
| Live boss-fight proof beyond Morty | Satisfied for the current manifest proof floor. All listed gym leaders plus Koga and Champion Lance have current trace-ROM first-decision proof, and `shared_switch_loop` now has a dedicated live fixture. | `audit/boss_ai_trace/live_capture_ledger.md`; `audit/boss_ai_trace/live_capture_manifest.json`; `docs/boss_ai_bug_testing_plan.md`; `docs/project_roadmap.md` row `BOSSAI-001` | Keep richer scenario captures honest: do not promote static excerpts or hand-written RAM expectations to live proof. |
| Manual emulator playtesting | Still open for broad feel. Static/build audits pass, but manual feel checks were not run in the release-confidence pass. | `audit/release_confidence_2026-04-26.md`; `docs/project_roadmap.md` rows `DIFFICULTY-001`, `QOL-001`, `COMM-001` | Run focused emulator checks for boss pacing, Repel renewal accept/decline, HM-tool flow, and early communication text rendering. |
| Current save file is not a gym-leader test state | Old warning superseded for manifest proof. The live trainer state factory now creates real map/script-started boss-position states for all listed trainer rows, and `tools/trace/boss_ai_shared_switch_loop_fixture.py` owns the synthetic repeated-switch state. | `docs/project_roadmap.md` row `BOSSAI-001`; `audit/boss_ai_trace/live_capture_ledger.md`; `tools/trace/boss_ai_state_factory.py`; `tools/trace/boss_ai_shared_switch_loop_fixture.py` | Use the factory route for real trainer state regeneration. Use the shared-loop fixture script for `shared_switch_loop`. |

## Next Priority Checks

| Opus item | Current repo status | Source-truth route | Next action |
| --- | --- | --- | --- |
| Weak-Pokemon backlog: Farfetch'd, Ariados, Yanma | Open. Delibird was resolved in the latest balance lane; Farfetch'd, Ariados, and Yanma remain the explicit next queue. | `docs/project_roadmap.md` row `BALANCE-001`; `docs/buff_backlog.md`; `docs/agent_navigation/subsystems/pokemon_balance.md`; `docs/balance_intent.md` | Pick exactly one species and give it source-plus-intent treatment. Verify build, generated audit, docs navigation, and cheap-difficulty tripwires. |
| Boss AI `boss.asm` complexity risk | Real maintenance risk, not a current memory overflow. The file lives in the Enemy Trainers ROM bank and passes memory-budget audit, but it centralizes move scoring, plans, lookahead, switching, trace, and public-information guard logic. | `engine/battle/ai/boss.asm`; `tools/audit/check_boss_ai_memory_budget.py`; `docs/generated/dev_index.md`; `docs/boss_ai_spec.md`; `docs/boss_ai_bug_testing_plan.md` | Keep edits narrow and heavily verified. Do not split the file just to make it smaller; only extract a module when a natural boundary and bank/jump plan are proven. |
| Type passives interaction risk | Open as an interaction-risk lane. Static battle-math and release-smoke checks exist, but emulator/player feel and edge interactions are not fully exhausted. | `engine/battle/type_passive_damage_mods.asm`; `engine/battle/late_gen_held_items.asm`; `tools/audit/check_battle_math_safety.py`; `docs/mechanics_changes_from_base.md`; `audit/release_confidence_2026-04-26.md` | Recheck type passive interactions after battle/item edits. Prioritize passives crossing held items, contact rules, damage category, immunity/nullification, or multi-hit/secondary-effect paths. |
| HM-tool field-use flow edge cases | Mostly source/build/audit covered, still needs emulator edge proof. | `docs/project_roadmap.md` row `QOL-001`; `docs/qol_handoff.md`; `docs/agent_navigation/subsystems/qol_map_scripts.md`; `tools/audit/check_release_smoke.py` | Manually verify legacy save backfill, badge gates, key-item pocket behavior near capacity, failed-use state, and SKY_PASS/fly-style presentation. |

## Solid Automated-Check Claims

These were already documented before this note and should not be inflated into
manual play proof:

- Normal Gold/Silver builds reported up to date in the release-confidence pass.
- Boss AI no-cheat, gating, trace invariant, live-ledger, and memory-budget
  audits pass.
- Trainer/boss roster item and moveset audits pass.
- Cheap-difficulty static tripwire passes.
- Docs navigation checks pass.
- Live first-decision captures now exist for every listed gym leader, Koga, and
  Champion Lance; `shared_switch_loop` has its own live switch-confidence
  fixture.

Source-truth route: `audit/release_confidence_2026-04-26.md`,
`docs/project_roadmap.md`, and `tools/audit/`.

## Bottom Line

Opus's useful warning is not that the hack is in bad shape. It is that proof
must stay current and must not be inflated. The best next sequence is:

1. Keep this sweep's checklist current in `docs/project_completion_todo.md`.
2. Run focused emulator feel checks for Repel/HM tools and early rule
   communication.
3. Resume balance/design work only after the manual feel surface is less
   lopsided.
