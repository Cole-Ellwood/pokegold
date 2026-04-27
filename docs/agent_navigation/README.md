# Agent Navigation Spine

Purpose: make future Codex/helper sessions find the right project surface fast
without changing ROM behavior. This folder is a routing layer only. It is not
source truth for mechanics, addresses, stats, trainer data, or build outputs.

Global project hook: preserve the First-Playthrough Promise. The hack is Pokemon
Gold made unknown and scary again for a veteran player, not generic hard mode,
competitive Gen 2, or pure modernization.

Read this after `docs/project_roadmap.md` when a session needs to decide where
to work next, or when the prompt is broad enough that a helper might otherwise
start with a full-repo search.

## Cold Jump Packet

For a fresh AI session, the useful packet is small:

1. `docs/README.md` for precedence and fast jump modes.
2. `docs/codex_context.md` for the project promise.
3. `docs/project_roadmap.md` for live workstreams.
4. `docs/agent_navigation/start_card.md` for lane choice.
5. One matching row in `docs/agent_navigation/task_router.md` or one matching
   micro-index under `docs/agent_navigation/subsystems/`.

For vague improvement prompts like "make the app better in an important way",
use `docs/agent_navigation/important_improvement_menu.md` before choosing the
one lane to execute.

Do not read every helper doc just to prove diligence. The point of this folder
is to stop the session from turning orientation into work.

## Complexity Budget

Use the smallest lookup that answers the current question:

| Cost | Use when | Lookup surface |
| --- | --- | --- |
| `O(1)` | A new session needs one screen to pick a lane. | `docs/agent_navigation/start_card.md` |
| `O(1)` | The user request names a task class, subsystem, or risk. | `docs/agent_navigation/task_router.md` |
| `O(1)` | The session needs to know which doc owns which kind of statement. | `docs/agent_navigation/doc_roles.md` |
| `O(1)` | The session is about to expand, prune, or finish navigation work. | `docs/agent_navigation/navigation_health_check.md` |
| `O(1)` | The session needs path class, edit policy, or generated/output ownership. | `docs/agent_navigation/source_output_ownership.md` |
| `O(1)` | The session needs checks for a known change kind. | `docs/agent_navigation/verification_matrix.md` |
| `O(1)` | The session remembers a custom mechanic but not its exact file/symbol. | `docs/agent_navigation/custom_terms.md` |
| `O(k)` | The session needs artifacts for one active workstream. | `docs/agent_navigation/artifact_catalog.md` |
| `O(k)` | The task is in a high-friction subsystem and the broad router is still too loose. | `docs/agent_navigation/subsystems/` |
| `O(log n)` by section jump | The session needs current labels, banks, memory pressure, or source anchors. | `docs/generated/dev_index.md` |
| `O(n)` | The routing docs fail to identify the surface. | Focused `rg` over source, after recording the doc gap. |

`O(n)` search is not forbidden. It is the fallback after the indexed route fails,
not the first move.

## Navigation Contract

1. Use `docs/agent_navigation/start_card.md` to pick a lane when the prompt is
   broad.
2. Identify the task class in `docs/agent_navigation/task_router.md`.
3. Use `docs/agent_navigation/doc_roles.md` before adding new routing or
   ownership facts.
4. Confirm the target path class in
   `docs/agent_navigation/source_output_ownership.md`.
5. Use `docs/agent_navigation/subsystems/` when the task is Boss AI trace,
   Pokemon balance, QoL/map scripts, or checkpoint/handoff work.
6. Use `docs/generated/dev_index.md` for current labels, banks, and memory.
7. Run the minimum relevant checks in
   `docs/agent_navigation/verification_matrix.md`.
8. Update `docs/project_roadmap.md` when a workstream changes state, gains a
   useful blocker, or gets a new next move.

## Nonfunctional Boundary

This folder may be edited freely for project organization. It must not be used
to smuggle gameplay changes into a documentation pass.

Allowed in this track:

- helper-doc routing;
- source-area maps;
- doc responsibility maps;
- verification command matrices;
- artifact indexes;
- subsystem micro-indexes;
- handoff structure;
- comments about stale or missing navigation.

Not allowed in this track:

- changing ROM logic;
- changing trainer parties, Pokemon data, move data, maps, RAM layout, or build
  products;
- hand-editing generated files;
- declaring gameplay confidence from docs alone.

## Maintenance Rules

- Keep entries path-heavy and grep-friendly.
- Prefer tables for routing, not prose essays.
- If a path moves, update this folder in the same session.
- If a generated truth changes, regenerate the generated truth instead of
  editing it by hand.
- If this folder conflicts with source/linker truth, fix this folder.

## Subsystem Micro-Indexes

Read these only when the router points at the matching area:

| File | Use for |
| --- | --- |
| `docs/agent_navigation/subsystems/boss_ai_trace.md` | Boss AI live proof, trace states, capture ledger, and proof standards. |
| `docs/agent_navigation/subsystems/trainer_boss_roster.md` | Trainer/boss AI tier lookup, party labels, and live trace priority overlay. |
| `docs/agent_navigation/subsystems/pokemon_balance.md` | Weak-Pokemon triage, generated balance audit use, and intent registry updates. |
| `docs/agent_navigation/subsystems/qol_map_scripts.md` | QoL, map scripts, events, specials, and text/service routing. |
| `docs/agent_navigation/subsystems/checkpoint_handoff.md` | Dirty worktree checkpoints, handoffs, commit boundaries, and stopping-point reports. |

## Core Cards

| File | Use for |
| --- | --- |
| `docs/agent_navigation/start_card.md` | One-screen lane picker and minimum safe stop. |
| `docs/agent_navigation/important_improvement_menu.md` | Broad "make it better" inspiration map and note discipline before choosing one lane. |
| `docs/agent_navigation/doc_roles.md` | Ownership rules for where new documentation facts belong. |
| `docs/agent_navigation/navigation_health_check.md` | Acceptance criteria and smoke routes for expanding, pruning, or completing navigation work. |
