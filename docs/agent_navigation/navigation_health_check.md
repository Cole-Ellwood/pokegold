# Navigation Health Check

Use this before expanding or changing the agent navigation layer. The goal is to
keep routing fast without turning docs into a second codebase.

## Acceptance Criteria

A navigation change is healthy when all of these are true:

| Check | Pass condition |
| --- | --- |
| Source boundary | No ROM behavior, trainer data, Pokemon data, maps, RAM, generated docs, or build outputs changed during a docs-only pass. |
| Ownership | New information lives in the owning doc from `docs/agent_navigation/doc_roles.md`. |
| Search cost | A future helper can route the task through `docs/agent_navigation/start_card.md`, `docs/agent_navigation/task_router.md`, or a subsystem micro-index before broad source search. |
| Truth level | The doc says whether evidence is source, generated, audit, build, live emulator, or scratch. |
| Duplication | Entry docs point to detailed docs instead of copying their tables. |
| Verification | `python tools\audit\check_docs_navigation.py` and `git diff --check` pass. |
| Roadmap | `docs/project_roadmap.md` is updated if a workstream changes status, blocker, evidence, or next move. |

`python tools\audit\check_docs_navigation.py` validates this navigation tree,
including required files, auto-discovered
`docs/agent_navigation/**/*.md` files, path references, Python command paths,
and the core contract snippets that keep the start card, smoke routes, doc
roles, health check, and `NAV-001` roadmap row load-bearing.

## Expansion Rules

Add a new navigation file only when at least one is true:

- future sessions repeatedly search the same subsystem;
- a task has multiple plausible first files and picking wrong is costly;
- a source/generated/output boundary is easy to mistake;
- a custom term has multiple spellings or symbols;
- a handoff would otherwise require chat memory.

Do not add a new file just to make the tree look symmetrical.
New markdown files under `docs/agent_navigation/` are automatically included in
`python tools\audit\check_docs_navigation.py`; if they contain backtick path
references, those references must resolve or be explicitly modeled as planned
missing artifacts in the audit.

## Pruning Rules

Prune or consolidate when:

- two docs contain the same detailed table;
- an entrypoint explains a subsystem instead of pointing at the subsystem
  micro-index;
- a generated/source fact was copied into routing docs and can drift;
- a scratch fact from `.local/` is presented as durable evidence.

## Smoke Route Table

After a navigation pass, test at least three prompt shapes against this table.
The goal is to prove common prompts still route without broad source search:

| Prompt shape | First route | Next files | Expected answer shape |
| --- | --- | --- | --- |
| "continue making it beautiful" | `docs/agent_navigation/start_card.md` | `docs/agent_navigation/navigation_health_check.md`, `docs/agent_navigation/doc_roles.md`, `docs/project_roadmap.md`, `docs/agent_navigation/verification_matrix.md` | Stay docs-only, change roadmap only if a workstream changes, run `python tools\audit\check_navigation_floor.py`. |
| "make the project easier for future AI to jump around" | `docs/agent_navigation/start_card.md` | `docs/agent_navigation/README.md`, `docs/agent_navigation/subsystems/checkpoint_handoff.md`, `docs/project_roadmap.md` | Use docs-only organization mode, preserve dirty source files, improve routing surfaces instead of gameplay, and report what stayed untouched. |
| "is Morty boss AI proven?" | `docs/agent_navigation/subsystems/boss_ai_trace.md` | `audit/boss_ai_trace/live_capture_ledger.md`, `audit/boss_ai_trace/live_capture_manifest.json`, `audit/boss_ai_trace/morty_state_needed_2026-04-26.md` | Answer yes: current trace-ROM proof has nonzero `chosen_id=101`; all real trainer manifest rows are now captured, while `shared_switch_loop` still needs a scenario fixture. |
| "what owns pokegold.sym?" | `docs/agent_navigation/source_output_ownership.md` | `docs/build.md`, `docs/generated/dev_index.md` | Read `.sym` as linker truth; never hand-edit it. |

If any route requires broad source search as the first action, either fix the
route or record the gap in this file.
