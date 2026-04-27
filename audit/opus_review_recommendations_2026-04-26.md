# Opus Review Recommendations - 2026-04-26

Purpose: preserve the external Opus 4.6 recommendation sheet as an actionable
repo checklist. This file is an index, not source truth. If anything here
conflicts with current source, linker output, generated audit output, or
`docs/project_roadmap.md`, trust the live source truth and update this file.

Source artifact: `C:\Users\lolno\Downloads\pokemon_gold_hack_recommendation_sheet.svg`.

Current verification note: when this note was created, `git status --short`
reported 108 dirty entries, not the sheet's older 101 count. The sheet's
direction still holds: protect the dirty work before doing broad new work.

## Critical Checks

| Opus item | Current repo status | Source-truth route | Next action |
| --- | --- | --- | --- |
| Commit or stage the dirty files | Still open. Worktree is broadly dirty across source, docs, audit, tools, and outbox. | `git status --short --branch`; `docs/project_roadmap.md` row `VERIFY-001`; `docs/agent_navigation/subsystems/checkpoint_handoff.md` | Make a logical checkpoint before high-risk edits. Split commits by ownership instead of staging everything blindly. |
| Live boss-fight proof beyond Morty | Partly satisfied. Morty and Jasmine have current trace-ROM chosen-move proof; other gym leaders plus Koga, Champion Lance, and shared switch-loop remain unproven live. | `audit/boss_ai_trace/live_capture_ledger.md`; `audit/boss_ai_trace/live_capture_manifest.json`; `docs/boss_ai_bug_testing_plan.md`; `docs/project_roadmap.md` row `BOSSAI-001` | Capture the next real boss-position save/debugger trace, preferably Clair. Do not promote synthetic RAM stitching or static excerpts to live proof. |
| Manual emulator playtesting | Still open for broad feel. Static/build audits pass, but manual feel checks were not run in the release-confidence pass. | `audit/release_confidence_2026-04-26.md`; `docs/project_roadmap.md` rows `DIFFICULTY-001`, `QOL-001`, `COMM-001` | Run focused emulator checks for boss pacing, Repel renewal accept/decline, HM-tool flow, and early communication text rendering. |
| Current save file is not a gym-leader test state | Still open. Roadmap records `pokegold.sav` as Route 29 with one level-11 party mon, not a hidden boss-position save. | `docs/project_roadmap.md` row `BOSSAI-001`; `audit/boss_ai_trace/live_capture_ledger.md` | Create or obtain defensible PyBoy-compatible boss-position states. Keep save-state provenance attached to any trace proof. |

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

Source-truth route: `audit/release_confidence_2026-04-26.md`,
`docs/project_roadmap.md`, and `tools/audit/`.

## Bottom Line

Opus's useful warning is not that the hack is in bad shape. It is that the hack
has more static confidence than live proof. The best next sequence is:

1. Make a logical checkpoint of the dirty worktree.
2. Capture another real boss live trace, preferably Clair.
3. Run focused emulator feel checks for Repel/HM tools and early rule
   communication.
4. Resume balance/design work only after the proof surface is less lopsided.
