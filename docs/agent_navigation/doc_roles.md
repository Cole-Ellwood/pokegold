# Documentation Roles

Use this to decide which doc owns which kind of statement. The aim is to prevent
future sessions from adding the same routing fact in five places.

## Role Matrix

| Doc | Owns | Does not own |
| --- | --- | --- |
| `docs/README.md` | Required read order, truth precedence, global routing contract. | Detailed subsystem routes or current workstream status. |
| `docs/codex_context.md` | Project intent, fair-hard promise, design rules, done criteria. | Current file locations beyond first-read routing. |
| `docs/project_map.md` | Canonical source areas and broad task-to-source map. | Workstream status, blockers, or detailed subsystem checklists. |
| `docs/project_roadmap.md` | Current workstreams, urgency, status, evidence, blockers, next moves. | Exact source facts that must come from source/generated outputs. |
| `docs/agent_navigation/` | Fast routing, source-zone classification, verification floors, artifact lookup, glossary, micro-indexes. | Gameplay truth, balance decisions, exact addresses, or generated facts. |
| `docs/generated/dev_index.md` | Generated labels, banks, memory pressure, source anchors. | Human intent or task priority. |
| `docs/generated/balance_audit.md` | Generated Pokemon balance hints from source. | Final species design intent. |
| `docs/boss_ai_spec.md` | Boss AI fairness/design contract and implementation checklist. | Live proof status. |
| `audit/boss_ai_trace/live_capture_ledger.md` | Live capture status and trace artifact ledger. | Static AI correctness. |
| `docs/balance_intent.md` | Species-level design intent and locked/provisional roles. | Generated source audit facts. |
| `docs/buff_backlog.md` | Durable weak-Pokemon review queue. | Final source implementation. |
| `docs/qol_handoff.md` | QoL current/remaining state and low-risk implementation notes. | General map/event routing outside QoL. |
| `docs/build.md` | Build environment and command patterns. | Current workstream urgency or release decision. |
| `docs/validation_report.md` | Snapshot of validation status. | A guarantee that current dirty source still matches the snapshot. |

## Where To Put New Information

| New information | Put it in |
| --- | --- |
| "A future helper should start here for this kind of task." | `docs/agent_navigation/task_router.md` or a micro-index. |
| "This exact path is source/generated/output/scratch." | `docs/agent_navigation/source_output_ownership.md`. |
| "This workstream is blocked or complete." | `docs/project_roadmap.md`. |
| "This species has an intended role." | `docs/balance_intent.md`. |
| "This species needs review." | `docs/buff_backlog.md`. |
| "This live trace exists or is missing." | `audit/boss_ai_trace/live_capture_ledger.md`. |
| "This address, bank, label, or free-space fact changed." | Regenerate `docs/generated/dev_index.md`. |
| "This Pokemon audit row changed." | Regenerate `docs/generated/balance_audit.md`. |
| "A session is ending and needs a durable handoff." | `outbox/` plus roadmap updates. |

## Duplication Rule

A routing fact may appear in multiple entrypoints only as a pointer. The owning
doc should contain the detail. For example, `docs/README.md` can say "use
`docs/agent_navigation/README.md` for fast routing," but the route table belongs
inside `docs/agent_navigation/`.
