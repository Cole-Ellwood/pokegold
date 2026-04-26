# Artifact Catalog

Use this file to find durable evidence and handoff artifacts without searching
scratch paths first.

## Durable Artifact Zones

| Path | Contains | Trust level | Notes |
| --- | --- | --- | --- |
| `docs/agent_navigation/start_card.md` | One-screen lane picker for broad prompts. | Routing only. | Use at session start after `docs/README.md`. |
| `docs/bug_hunt_master_playbook.md` | Exhaustive bug-hunt startup, subsystem passes, search discipline, and command floor. | Review workflow. | Use for broad, release-facing, or "bug could be anywhere" prompts. |
| `docs/agent_navigation/navigation_health_check.md` | Navigation acceptance criteria and smoke routes. | Routing QA. | Use before expanding, pruning, or closing navigation work. |
| `docs/agent_navigation/doc_roles.md` | Ownership rules for documentation facts. | Routing only. | Use before adding duplicate routing prose. |
| `docs/project_roadmap.md` | Workstreams, statuses, blockers, next moves. | Current planning index. | Update when a workstream changes. |
| `docs/generated/dev_index.md` | Generated banks, labels, memory pressure, source anchors. | Generated navigation truth. | Regenerate only through `scripts/generate_dev_index.py`. |
| `docs/generated/balance_audit.md` | Generated Pokemon data audit. | Generated data mirror. | Regenerate through `scripts/generate_balance_audit.py`. |
| `docs/agent_navigation/source_output_ownership.md` | Source/generated/output ownership map. | Routing only. | Use before editing build artifacts or generated files. |
| `docs/agent_navigation/custom_terms.md` | Search glossary for custom mechanics and symbols. | Routing only. | Use when the feature name is remembered imprecisely. |
| `tools/audit/check_workspace_hygiene.py` | Read-only ignored-clutter classifier. | Audit helper. | Use before proposing workspace cleanup or output relocation. |
| `tools/trace/boss_ai_trace_state_probe.py` | PyBoy state/RAM preflight for live Boss AI captures. | Probe helper. | Use before adding a candidate state to the live-capture manifest. |
| `audit/boss_ai_trace/live_capture_ledger.md` | Live Boss AI trace status ledger. | Evidence ledger. | Priority rows must not be marked finished without real capture files. |
| `audit/boss_ai_trace/live_capture_manifest.json` | Trace batch manifest. | Tool input. | Add states only when they match the current trace ROM. |
| `audit/boss_ai_trace/morty_proof_capsule_attempt_2026-04-26.md` | Blocked Morty proof attempt and unblock recipe. | Negative evidence. | Shows why old RAM was not accepted as proof. |
| `docs/agent_navigation/subsystems/` | Micro-indexes for high-friction workstreams. | Routing only. | Use after task classification, before broad search. |
| `outbox/` | Self-contained handoff files. | Handoff only. | Use when context is tight or another session/model needs one file. |

## Scratch And Output Zones

| Path | Meaning | Rule |
| --- | --- | --- |
| `.local/` | Local deps, emulator RAM, scratch probes, temporary outputs. | Useful for investigation, not canonical proof by itself. |
| `workspace/` | Scratch/archive workspaces. | Search only when explicitly relevant. |
| `dist/` | Built/release outputs. | Do not edit by hand; tracked release artifacts can exist there. |
| `*.gbc`, `*.o`, `*.map`, `*.sym` | Build/linker outputs. | Read `.map`/`.sym` as truth; do not hand-edit any output. |

## Evidence Rule

Evidence should say what it proves and what it does not prove.

Good:

- "Audit X passed against current source."
- "Build reported both ROMs up to date."
- "Trace batch found missing states and ran zero captures."
- "Manual emulator validation was not performed."

Bad:

- "Boss AI is proven fair" from static audits alone.
- "Morty proof exists" from old RAM that does not load a current boss decision.
- "The game is done" without naming build, audit, and playtest gaps.
