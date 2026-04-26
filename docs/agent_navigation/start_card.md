# One-Screen Start Card

Use this when a new session starts, or when the prompt is broad like
"continue making it beautiful" or "make the game perfect." This card is a
launcher, not source truth.

## First Thirty Seconds

1. Read `docs/README.md` for precedence.
2. Read `docs/codex_context.md` for the fair-hard Pokemon Gold promise.
3. Read `docs/project_roadmap.md` for current workstreams and blockers.
4. Pick a lane below.

## Pick A Lane

| If the prompt is about | Go next | Do not do |
| --- | --- | --- |
| Project organization, future-session usability, docs beauty | `docs/agent_navigation/README.md`, `docs/agent_navigation/doc_roles.md` | Touch ROM behavior or generated files. |
| Boss AI live proof, trace states, Morty/Jasmine/Clair/Koga/Lance/Red evidence | `docs/agent_navigation/subsystems/boss_ai_trace.md` | Count static audits or old `.local/` RAM as live proof. |
| Trainer parties, boss tiers, major trainer rosters | `docs/agent_navigation/subsystems/trainer_boss_roster.md` | Mix trainer-party legality with species learnset legality unless asked. |
| Weak Pokemon, stats, learnsets, evolutions, roles | `docs/agent_navigation/subsystems/pokemon_balance.md` | Trust generated audit rows as final design judgment. |
| QoL, maps, NPC text, Repel, Pokemon Center, Day-Care services | `docs/agent_navigation/subsystems/qol_map_scripts.md` | Remove preparation pressure under the name of convenience. |
| Build outputs, generated docs, checksums, release files | `docs/agent_navigation/source_output_ownership.md`, `docs/build.md` | Hand-edit `.gbc`, `.o`, `.map`, `.sym`, or generated docs. |
| Reviews or bug hunts | `docs/codex_review_playbook.md` | Start with broad source search before routing the risk. |
| Half-remembered custom mechanic | `docs/agent_navigation/custom_terms.md` | Search only one spelling. |

## Roadmap Snapshot Rule

Current workstream state lives in `docs/project_roadmap.md`. Do not copy active
status facts into this card; stale "helpful" summaries are worse than one more
roadmap lookup.

## Minimum Safe Stop

For a docs-only navigation pass:

```powershell
python tools\audit\check_docs_navigation.py
git diff --check
git status --short --branch
```

For source changes, use `docs/agent_navigation/verification_matrix.md`.
For navigation changes, also run the checklist in
`docs/agent_navigation/navigation_health_check.md`.

## Never Skip

- Name whether evidence is source, generated, build, audit, live emulator, or
  scratch.
- Update `docs/project_roadmap.md` when a workstream changes.
- Preserve unrelated dirty worktree changes.
- Say when gameplay/manual validation did not happen.
