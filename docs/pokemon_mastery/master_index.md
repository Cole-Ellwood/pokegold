# Pokemon Mastery Master Index

Purpose: route future study and live-advice work to the right artifact quickly.
Fresh unseen move choice starts from `live_core.md`, not the archive. This is
the table of contents for the Pokemon mastery docs, not a replacement for the
cookbook or the detailed subfolder indexes.

## Start Here

| Need | Open |
| --- | --- |
| Fresh unseen move-choice core | `live_core.md` |
| Playbook/workspace load contract | `playbook_manifest.md` |
| Tiny live heuristic cards | `heuristic_core/README.md` |
| Compact GSC topic facts | `canon/README.md` |
| Current compact status packet | `active_context.md` |
| Context-management plan and vote record | `context_management_plan.md` |
| Expanded reference policy cards | `policy_cards/README.md` |
| Current learning continuation prompt | `continue_learning_1500_elo_prompt.md` |
| Goal recreation prompt | `goal_restart_prompt.md` |
| Study measurement loop | `measurement_minigoal_2026-05.md` |
| Live boss turn answer shape | `boss_turn_advice_template.md` |
| Pre-battle boss planning worksheet | `pre_battle_route_sheet.md` |
| Main decision cookbook | `cookbook.md` |
| This docs audit and cleanup policy | `doc_cleanup_audit_2026-05-14.md` |
| Forward study roadmap | `study_roadmap_2026-05-14.md` |
| Unseen replay practice loop | `replay_turn_pause_protocol.md` |
| Full-autonomy transfer study | `cross_domain_autonomy_policy.md` |

## Default Context Contract

Do not glob-load this directory. Fresh decisions use `live_core.md`, the public
state, and the smallest decision-relevant set of `heuristic_core/`, `canon/`,
and `romhack_deltas/` files. `workspace/` is provenance for post-score review,
not pre-freeze move choice.

## Task Routing

| Task | First file | Then check |
| --- | --- | --- |
| Fresh unseen replay move choice | `live_core.md`, current prompt | decision-relevant `heuristic_core/*.md`, `canon/*.md`, or `romhack_deltas/*.md`; scoring rules only after answers are frozen |
| Give live turn advice | `live_core.md`, then `boss_turn_advice_template.md` | matching `boss_route_maps/*_turn1_route_sheet.md`, relevant tiny heuristics, local mechanics docs |
| Plan a boss before turn 1 | `pre_battle_route_sheet.md` | `boss_route_maps/README.md`, matching `worked_examples/*_pre_battle_route_sheet.md` |
| Study a reusable decision recipe | `heuristic_core/migration_map.md`, then `policy_cards/README.md` | `cookbook.md`, `source_to_policy_ledger.md`, `worked_examples/README.md` |
| Practice exact move choice | `live_core.md`, then `replay_turn_pause_protocol.md` | choose prompts from `paused_turn_atlas.md` or `worked_examples/live_turn_drills.md` before answering, not during answer selection |
| Review a long expert battle | `active_context.md`, then `replay_turn_pause_protocol.md` | `reviews/`; add/update `source_to_policy_ledger.md`, `paused_turn_atlas.md`, `worked_examples/` only if the lesson is reusable |
| Take an adjacent-domain tangent | `cross_domain_autonomy_policy.md` | create STP/PTA/helper/fixture/reject note, then test against a Pokemon score |
| Validate romhack mechanics | `romhack_deltas/` | `mechanics_fixtures/`, local source/debugger/emulator evidence |
| Review cheap boss-AI policy fixes | `boss_ai_re_solve_trigger_audit_2026-05-14.md` | `tools/boss_ai_preference/benchmarks/`, `engine/battle/ai/boss_policy_move.asm`, `engine/battle/ai/boss_policy_switch.asm` |
| Prepare a measurable study block | `training_cycle.md` | `measurement_progress_ledger.csv`, `measurement_minigoal_2026-05.md` |
| Decide if boss-sim results count | `boss_sim_readiness_audit_2026-05-13.md` | `boss_sim_validation_protocol.md`, `workspace/battle_captures/README.md` |
| Use external research returns | `workspace/external_research_returns/` | `external_research_context_packet_2026-05-14.md`, local verification before adoption |

## Artifact Map

| Area | Role | Keep Policy |
| --- | --- | --- |
| `live_core.md` | Tiny pre-freeze move-choice entrypoint. | Keep under 80 lines. Do not turn it into an archive. |
| `playbook_manifest.md` | Load contract for core, topic retrieval, and workspace. | Keep short and update whenever the default context path changes. |
| `heuristic_core/` | Tiny live heuristics plus migration map. | Keep as small cards. Map old lessons instead of copying long notes. |
| `canon/` | Compact GSC mechanics and matchup lookup pages. | Add only source-linked facts that directly improve move choice. |
| `active_context.md` | Compact status and routing packet for future work blocks. | Preserve cap. Move decision details into `heuristic_core/` or archive evidence. |
| `context_management_plan.md` | Approved context-management plan and granular vote record. | Preserve as process source; update only after another declared audit. |
| `policy_cards/` | Expanded decision-boundary reference and evidence index. | Preserve. Do not load before fresh answer freeze by default. |
| `cookbook.md` | Canonical concise recipes for battle advice. | Preserve. Edit only to clarify, de-duplicate, or add a battle-tested recipe. |
| `source_to_policy_ledger.md` | Source lessons compressed into trigger/default/exception/worst-branch entries. | Preserve. It is the trace from expert source to policy. |
| `paused_turn_atlas.md` | Reviewed positions turned into move-choice prompts. | Preserve. It is practice material, not prose. |
| `worked_examples/` | Concrete applications, live drills, stress tests, boss worksheets. | Preserve. Use `worked_examples/README.md` as the detailed index. |
| `reviews/` | Individual battle reviews and extracted lessons. | Preserve. Do not merge into the cookbook unless the lesson has become reusable. |
| `boss_route_maps/` | Boss-specific no-preview route maps. | Preserve. They are local roster planning artifacts. |
| `romhack_deltas/` | Mechanics forks and local transfer rules. | Preserve. These outrank vanilla memory for romhack claims. |
| `romhack_deltas/mechanics_pending_index.md` | Current routing index for decision-relevant mechanics that still need local proof. | Update row status when local evidence changes. |
| `mechanics_fixtures/` | Runtime evidence for mechanics that affect advice. | Preserve and expand. |
| `measurement_*` | Progress measurement and score history. | Preserve. This is the anti-wheel-spinning layer. |
| `workspace/` | Scored quick tests, raw research, process notes, measurement reports, and battle captures. | Preserve. Exclude from default playbook context. |
| `replay_turn_pause_protocol.md` | Procedure for turn-by-turn unseen replay reps. | Preserve. It is the default expert-play measurement loop. |
| `cross_domain_autonomy_policy.md` | Bounded incentive to study adjacent domains and build odd helpers when they target a Pokemon failure. | Preserve. It prevents underusing autonomy without rewarding fluff. |
| `external_research_*` | Prompts and context for outside research. | Preserve as source material; raw returns live under `workspace/`. |
| `boss_ai_re_solve_trigger_audit_2026-05-14.md` | Public-information source audit for cheap ROM boss-AI re-score/reveal fixes. | Preserve until the identified spinner-retention fixture is implemented or rejected. |

## Current Coverage Counts

Live snapshot from 2026-05-16:

| Artifact | Count |
| --- | ---: |
| Boss turn-1 route sheets | 22 |
| Matching pre-battle worked route sheets | 22 |
| Battle reviews and retrospectives | 121 |
| Source-to-policy entries | 58 |
| Paused-turn atlas prompts | 60 |
| Live-turn drills | 52 |
| Workspace quick-test artifacts | 316 |
| Canon lookup pages | 7 |
| Romhack delta docs | 9 |

## High-Value Entry Points By Skill

| Skill | Best entry points |
| --- | --- |
| Hidden-information discipline | `goal_restart_prompt.md`, `workspace/external_research_returns/2026-05-14_deep_research_hidden_info_turn_atlas.md`, `paused_turn_atlas.md` |
| Spikes / Rapid Spin / spinblock reasoning | `romhack_deltas/spikes_and_rapid_spin.md`, `mechanics_fixtures/spikes_rapid_spin/README.md`, `worked_examples/will_hazard_retention_stress_test.md`, `worked_examples/janine_qwilfish_spikes_arbitration.md` |
| Route planning and blocker maps | `cookbook.md`, `worked_examples/smogtours_604744_support_delivery_cascade.md`, `worked_examples/smogtours_604804_trap_lure_contract.md`, `worked_examples/smogtours_531497_converter_support_ladder.md` |
| Rest, sleep, status, and PP | `worked_examples/resttalk_branch_pricing_boss_examples.md`, `worked_examples/status_absorber_assignment_boss_examples.md`, `worked_examples/status_reset_map_boss_examples.md`, `worked_examples/pp_budget_ledger_boss_examples.md` |
| Explosion and one-time trades | `worked_examples/smogtours_451060_delayed_explosion_contract.md`, `worked_examples/smogtours_902742_staged_one_time_trades.md`, `worked_examples/brock_golem_explosion_turn_order_quarantine.md` |
| Romhack type/passive discipline | `romhack_deltas/type_passive_fixture_priorities.md`, `romhack_deltas/type_passive_route_impacts.md`, `workspace/pro_notes/04_type_effectiveness_evidence_firewall.md` |
| Whole-battle ledgers | `worked_examples/pryce_30_turn_ledger_drill.md`, `worked_examples/koga_30_turn_attrition_trap_ledger_drill.md`, `worked_examples/lance_30_turn_serial_setup_ledger_drill.md`, `worked_examples/red_30_turn_final_boss_ledger_drill.md` |
| Progress measurement | `measurement_minigoal_2026-05.md`, `measurement_progress_ledger.csv`, `replay_turn_pause_protocol.md`, `boss_sim_readiness_audit_2026-05-13.md` |

## Topic Lookup

Use this when the problem is "what knowledge applies to this board?" Load only
the rows the public state demands.

| Topic | Open first | Then check |
| --- | --- | --- |
| Hazards, Rapid Spin, spinblocking | `canon/gsc_spikes_spin.md` | `heuristic_core/reset_loop_denial.md`, `policy_cards/hazard_loop_spin_window.md`, `romhack_deltas/spikes_and_rapid_spin.md` |
| Sleep, Rest, Sleep Talk, status clocks | `canon/gsc_sleep_status.md` | `heuristic_core/rest_curse_tempo_window.md`, `policy_cards/sleep_absorber_and_set_ambiguity.md` |
| Phazing, Roar, Whirlwind, slow-phazer timing | `canon/gsc_phazing_priority.md` | `heuristic_core/reset_loop_denial.md`, `heuristic_core/rest_curse_tempo_window.md` |
| Pursuit, trapper, spinblock chain | `canon/gsc_pursuit_spinblock.md` | `heuristic_core/branch_punish_ranking.md`, `policy_cards/hidden_role_voluntary_entry.md` |
| Explosion, Self-Destruct, one-time trade | `canon/gsc_explosion.md` | `heuristic_core/spend_or_save_piece.md`, `policy_cards/cashout_boundary.md` |
| Lead matchup and opening RPS | `canon/gsc_lead_rps.md` | `heuristic_core/name_current_owner.md`, `heuristic_core/public_info_tiers.md` |
| Critical-hit math and variance | `canon/gsc_critical_hits.md` | `heuristic_core/public_info_tiers.md`; local mechanics if romhack damage thresholds matter |
| Snorlax route, CurseLax, Lovely Kiss branch | `romhack_deltas/snorlax_context.md` | `heuristic_core/rest_curse_tempo_window.md`, `policy_cards/sleep_absorber_and_set_ambiguity.md` |
| Branch named but not punished | `heuristic_core/branch_punish_ranking.md` | matching canon topic for the named branch |
| Revealed support/package changed a role | `heuristic_core/role_package_ledger.md` | `heuristic_core/rescore_after_reveal.md`, `heuristic_core/spend_or_save_piece.md` |
| No-Team-Preview or hidden-set uncertainty | `heuristic_core/public_info_tiers.md` | `playbook_manifest.md` |
| Romhack type/passive/mechanics transfer | `romhack_deltas/mechanics_pending_index.md` | local source, fixtures, debugger, or emulator evidence |

## Decision Failure Lookup

Use this when the problem is not "what file exists?" but "what mistake am I
trying to stop making?"

| Failure mode | Open first | Drill or proof target |
| --- | --- | --- |
| Treating hazards as progress before retention/conversion | `heuristic_core/reset_loop_denial.md` | after scoring, inspect `policy_cards/hazard_loop_spin_window.md` |
| Letting Rapid Spin erase the route | `heuristic_core/reset_loop_denial.md` | finish pending fixture items; add a quick-probe scenario |
| Overclaiming hidden player moves or team slots | `heuristic_core/public_info_tiers.md` | convert public-only prompts into `paused_turn_atlas.md` after scoring |
| Following a stale plan after reveal, KO, Spin, Rest, or switch | `heuristic_core/rescore_after_reveal.md` | postmortem with old policy card or whole-battle ledger drill |
| Spending a unique answer for generic progress | `heuristic_core/spend_or_save_piece.md` | boss route maps for the relevant fight |
| Using Explosion or Destiny Bond into the wrong target | `heuristic_core/spend_or_save_piece.md` | postmortem with one-time trade examples |
| Mispricing RestTalk, sleep, or status allocation | `heuristic_core/reset_loop_denial.md` | after scoring, use sleep/status drills |
| Naming a branch but not punishing it | `heuristic_core/branch_punish_ranking.md` | next fresh replay should track branch-punish movement |
| Making type-effectiveness claims from vanilla memory | `romhack_deltas/type_passive_fixture_priorities.md`, `workspace/pro_notes/04_type_effectiveness_evidence_firewall.md` | local fixture or source check before advice |
| Calling simulation win rate proof too early | `boss_sim_readiness_audit_2026-05-13.md`, `boss_sim_validation_protocol.md` | filled real boss worksheet and readiness blockers closed |
| Producing more notes without proving improvement | `measurement_minigoal_2026-05.md`, `measurement_progress_ledger.csv` | Quick Test 001, then trend rows |
| Needing fast expert-play reps | `replay_turn_pause_protocol.md` | unseen Smogon GSC replay turn-pause run |

## Suggested Status Labels

Use these labels in future indexes and cleanup patches instead of rewriting
whole docs:

- `public_practice`: safe to study openly; not a trend score.
- `semi_blind`: usable for quick probes if answers were not reviewed first.
- `sealed`: hidden prompt/key material; do not expose before scoring.
- `source_grounded`: backed by expert source or reviewed battle.
- `runtime_verified`: checked against local romhack behavior.
- `romhack_unverified`: useful idea, but local mechanics still need proof.
- `boss_ai_public_only`: legal for ordinary boss AI under the information
  model.
- `player_advice_source_known`: legal for advisor/player planning with known
  boss rosters.

## Do Not Treat As Completion Proof

- A larger cookbook.
- More route maps without scored live-turn use.
- More reviews without decision grades or extracted drills.
- Simulation win rate before the readiness blockers are closed.
- Raw external research that has not been filtered for no-Team-Preview and
  romhack-mechanics compatibility.
