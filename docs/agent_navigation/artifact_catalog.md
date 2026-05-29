# Artifact Catalog

Use this file to find durable evidence and handoff artifacts without searching
scratch paths first.

## Durable Artifact Zones

| Path | Contains | Trust level | Notes |
| --- | --- | --- | --- |
| `docs/agent_navigation/start_card.md` | One-screen lane picker for broad prompts. | Routing only. | Use at session start after `docs/README.md`. |
| `docs/bug_hunt_master_playbook.md` | Exhaustive bug-hunt startup, subsystem passes, search discipline, and command floor. | Review workflow. | Use for broad, release-facing, or "bug could be anywhere" prompts. |
| `docs/bug_hunt_labeled_findings_2026-04-26.md` | Labeled findings from the 2026-04-26 no-source-fix bug hunt. | Review evidence. | Source bugs remain open unless a later patch says otherwise. |
| `docs/agent_navigation/navigation_health_check.md` | Navigation acceptance criteria and smoke routes. | Routing QA. | Use before expanding, pruning, or closing navigation work. |
| `docs/agent_navigation/doc_roles.md` | Ownership rules for documentation facts. | Routing only. | Use before adding duplicate routing prose. |
| `docs/project_roadmap.md` | Workstreams, statuses, blockers, next moves. | Current planning index. | Update when a workstream changes. |
| `docs/project_completion_todo.md` | Current proof/feel sweep todo list with double-check states. | Execution checklist. | Mark finished items `DONE_NEEDS_DOUBLE_CHECK` until the named second pass is complete. |
| `docs/generated/dev_index.md` | Generated banks, labels, memory pressure, source anchors. | Generated navigation truth. | Regenerate only through `scripts/generate_dev_index.py`. |
| `docs/generated/balance_audit.md` | Generated Pokemon data audit. | Generated data mirror. | Regenerate through `scripts/generate_balance_audit.py`. |
| `audit/move_progression/move_progression_audit.html` | Generated same-type move progression issue report. | Generated audit report. | Regenerate through `scripts/generate_move_progression_audit_html.py`. |
| `docs/graphics_emulator_debugging.md` | Visual-corruption and emulator-repro triage, including VBA tile-jumble and PyBoy save sidecar notes. | Debug workflow. | Use when sprites/text/map tiles/palettes differ across emulators or a save-state repro is involved. |
| `docs/agent_navigation/source_output_ownership.md` | Source/generated/output ownership map. | Routing only. | Use before editing build artifacts or generated files. |
| `docs/agent_navigation/custom_terms.md` | Search glossary for custom mechanics and symbols. | Routing only. | Use when the feature name is remembered imprecisely. |
| `tools/audit/check_navigation_floor.py` | One-command docs/navigation readiness floor. | Audit helper. | Runs docs navigation, whitespace diff check, and dirty-state report; add `--workspace-hygiene` for clutter classification. |
| `tools/audit/check_workspace_hygiene.py` | Read-only ignored-clutter classifier. | Audit helper. | Use before proposing workspace cleanup or output relocation. |
| `tools/trace/boss_ai_trace_state_probe.py` | PyBoy state/RAM preflight for live Boss AI captures. | Probe helper. | Use before adding a candidate state to the live-capture manifest. |
| `audit/boss_ai_trace/live_capture_ledger.md` | Live Boss AI trace status ledger. | Evidence ledger. | Priority rows must not be marked finished without real capture files. |
| `audit/boss_ai_trace/live_capture_manifest.json` | Trace batch manifest. | Tool input. | Add states only when they match the current trace ROM. |
| `tools/trace/boss_ai_state_factory.py` | PyBoy state factory for real trainer live captures. | Tooling. | Use `--all --update-manifest` to regenerate trainer decision states through real map scripts. |
| `audit/boss_ai_trace/morty_live.txt` | Current Morty live chosen-move proof. | Live emulator evidence. | First proof capsule; has current trace hashes and `chosen_id=138`. |
| `audit/boss_ai_trace/morty_proof_capsule_attempt_2026-04-26.md` | Blocked Morty proof attempt and unblock recipe. | Negative evidence. | Shows why old RAM was not accepted as proof. |
| `docs/agent_navigation/subsystems/` | Micro-indexes for high-friction workstreams. | Routing only. | Use after task classification, before broad search. |
| `decisions/` | Dated reversible-judgment notes. | Tracked durable record. | Write a short file when making a project-shape call future helpers might revisit. |
| `journal/` | Per-session diary observations. | Tracked durable record. | Use for surprising findings or feel notes that don't belong in the roadmap. |
| `.claude_handoffs/` | Per-session handoff prompts. | Local only (gitignored). | Write when ending a long task and the next session needs a self-contained start. |

## Scratch And Output Zones

| Path | Meaning | Rule |
| --- | --- | --- |
| `.local/` | Local deps, emulator RAM, scratch probes, temporary outputs. | Useful for investigation, not canonical proof by itself. |
| `workspace/` | Scratch/archive workspaces. | Search only when explicitly relevant. |
| `dist/` | (retired 2026-05-03) Was the BPS distribution channel; removed because `flips` is no longer available. | Do not recreate without a fresh BPS toolchain — see `docs/build.md` "Release artifact workflow (retired)". |
| `*.gbc`, `*.o`, `*.map`, `*.sym` | Build/linker outputs. | Read `.map`/`.sym` as truth; do not hand-edit any output. |

## Evidence Rule

Evidence should say what it proves and what it does not prove.

Good:

- "Audit X passed against current source."
- "Build reported both ROMs up to date."
- "Trace batch found one missing synthetic scenario and all real trainer states ready."
- "Manual emulator validation was not performed."

Bad:

- "Boss AI is proven fair" from static audits alone.
- "Morty proof exists" from old RAM that does not load a current boss decision.
- "The game is done" without naming build, audit, and playtest gaps.

## Orphan / Uncatalogued Docs

Real, tracked docs that no other tracked file links to — listed here so they
are discoverable without a blind search. Not part of the routing floor; consult
the relevant group only when its topic is in play.

### Boss-AI debugger module references

Component-level docs for the `tools/boss_ai_debugger` / `tools/debugger`
toolchain. Read alongside the module they describe.

- [Scenario generators](../boss_ai_debugger_generators.md)
- [Mastery and coverage indexes](../boss_ai_debugger_mastery_coverage.md)
- [Mutation and invariant tools](../boss_ai_debugger_mutation_invariants.md)
- [Metamorphic checks](../boss_ai_debugger_metamorphic.md)
- [Differential runner (ROM vs Python)](../boss_ai_debugger_differential.md)
- [Rule map](../boss_ai_debugger_rule_map.md)
- [Route evaluation (multi-turn)](../boss_ai_debugger_route_eval.md)
- [Analysis tools](../boss_ai_debugger_analysis_tools.md)
- [Run store](../boss_ai_debugger_run_store.md)

### Boss-AI plans and task specs

Planning / handoff specs (historical intent, not current state — cross-check
against `docs/project_roadmap.md` and the code before acting).

- [Preference regression runner plan](../boss_ai_regression_runner_plan.md)
- [Debugger closed-loop alignment plan (2026-05-15)](../boss_ai_debugger_closed_loop_alignment_plan_2026-05-15.md)
- [Trace-capture refresh — Codex task spec](../boss_ai_trace_refresh_codex_task.md)
- [boss.asm repartition — Codex task spec](../boss_asm_repartition_codex_task.md)
- [Sleep clause — Codex task spec](../sleep_clause_codex_task.md)
- [Voucher removal + TM swap plan](../voucher_removal_and_tm_swap_plan.md)

### Dated snapshots and reviews

Point-in-time records; the data underneath drifts.

- [Boss AI decision flowchart by tier (2026-05-27)](../boss_ai_flowchart_2026-05-27.md)
- [RAM pressure findings (2026-05-26)](../ram_pressure_findings_2026-05-26.md)
- [Codex review request — Claude session (2026-05-10)](../codex_review_2026-05-10.md)

### Reference and checklists

- [Type Passives V1 smoke tests](../type_passives_smoketests.md)
- [Boss authoring checklist](../boss_authoring_checklist.md)
