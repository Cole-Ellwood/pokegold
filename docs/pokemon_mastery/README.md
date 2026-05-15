# Pokemon Mastery Notebook

Purpose: build practical move-choice skill for Pokemon singles advice in the
Pokemon Gold romhack / Gym Leader Lab setting.

The notebook is not meant to prove mastery by volume. It should help answer
real turns: what the plan is, what can still win, what can lose immediately,
which pieces matter, and which move improves a concrete route.

## Current Files

| File | Role |
| --- | --- |
| `active_goal.md` | Operating goal, study cadence, and serious-turn checklist. |
| `live_core.md` | Tiny pre-freeze entrypoint for fresh unseen move choice. |
| `heuristic_core/` | Small live heuristic cards and migration map from repeated old lessons. |
| `continue_learning_1500_elo_prompt.md` | Copy-paste prompt for continuing measured 1500-Elo Pokemon learning work with fresh web checks and local-doc grounding. |
| `master_index.md` | Top-level table of contents and task router for the mastery docs. |
| `study_roadmap_2026-05-14.md` | Forward roadmap focused on measured Pokemon decision improvement. |
| `doc_cleanup_audit_2026-05-14.md` | Redundancy, keep/merge/delete, and cleanup policy. |
| `boss_turn_advice_template.md` | Compact response shape for real Gym Leader Lab turn advice. |
| `boss_route_maps/` | Index and local boss-specific route maps for pre-battle planning. |
| `boss_sim_validation_protocol.md` | Later-stage 50-battle matrix and 80% validation gate for testing boss advice against AI/non-self opponents. |
| `boss_sim_readiness_audit_2026-05-13.md` | Current evidence and blockers before the 50-battle validation gate can count. |
| `boss_ai_re_solve_trigger_audit_2026-05-14.md` | Source-grounded audit of whether the re-solve-after-reveal lesson has cheap, public-only ROM boss-AI implementation targets. |
| `cookbook.md` | Practical battle-advice recipes distilled from expert sources and review. |
| `cross_domain_autonomy_policy.md` | Incentives and transfer filter for broad autonomous study, tools, and adjacent-domain research. |
| `external_research_context_packet_2026-05-14.md` | Compact project context to upload with external GPT-5.5 Pro / Deep Research prompts. |
| `external_research_prompts_2026-05-14.md` | Narrow GPT-5.5 Pro / Deep Research prompts for expert no-preview decisions and cheap no-cheat boss AI wins. |
| `goal_restart_prompt.md` | Copy-paste prompt for resuming or recreating the long-running goal with the current emphasis. |
| `mechanics_fixtures/` | Runtime fixture results for romhack mechanics that affect battle advice. |
| `measurement_minigoal_2026-05.md` | Separate progress-measurement overlay for quick tests, final exams, simulation gates, and contamination controls. |
| `measurement_progress_ledger.csv` | Machine-readable dated score ledger for the measurement mini-goal. |
| `paused_turn_atlas.md` | Index of reviewed positions turned into move-choice practice prompts. |
| `pre_battle_route_sheet.md` | Compact worksheet for planning a boss fight before turn 1. |
| `quick_tests/` | Scored quick-probe artifacts and post-oracle summaries. |
| `replay_turn_pause_protocol.md` | Rules for unseen Smogon GSC replay practice: freeze turn predictions before revealing pro choices. |
| `reviews/` | Short battle-review artifacts. These should focus on route planning, not full transcripts. |
| `romhack_deltas/` | Source-checked mechanics forks and boss-policy deltas that change how vanilla lessons transfer. |
| `source_to_policy_ledger.md` | Expert-source lessons compressed into trigger/default/exception/worst-branch policy entries. |
| `training_cycle.md` | Current work allocation and standards for study blocks. |
| `worked_examples/` | Concrete applications of the template to public benchmark or battle states. |
| `pro_notes/` | GPT-5.5 Pro method notes, kept as process guidance rather than curriculum. |

## Study Bias

Use expert play as the main learning signal: Smogon articles, analyses,
tournament replays, battle logs, and high-level forum discussion. Use the local
romhack docs and source as the authority for fork-specific mechanics.

Local preference cards and user examples are calibration data. They are useful
when they reveal a concrete mechanic, answer flip, or repeated reasoning
failure, but they should not dominate the curriculum.

## Source Discipline

- General strategy claims can come from expert Pokemon sources and battle
  review.
- GSC claims should be checked against GSC-specific resources when mechanics
  matter.
- Romhack claims must be checked against local docs, source, fixtures, debugger
  output, or emulator observations when the mechanic or damage threshold
  matters.
- Type-effectiveness words such as super effective, resisted, immune, and
  neutral require environment-specific evidence in romhack-facing advice.
