# Project Map

This is the front door for ROM work. Use it to route a task before broad
searching, then jump to the deeper doc or source area it names.

Agent-facing format rule: keep path tokens, task labels, command lines, and
source-truth rules explicit even when that makes the prose less human-friendly.

## First Reads

- `docs/README.md`: helper-doc entrypoint, read order, and source-truth
  precedence for future Codex/helper sessions.
- `docs/codex_context.md`: objective, design rules, and done criteria. If another
  helper doc conflicts with project intent, this file wins.
- `docs/project_roadmap.md`: current project work board with future-session
  statuses, blockers, evidence, and next ideas.
- `docs/agent_navigation/README.md`: optimized agent routing layer for task
  classification, source-zone ownership, verification floors, and artifact
  lookup.
- `docs/codex_review_playbook.md`: review and bug-hunt workflow.
- `docs/generated/dev_index.md`: generated bank/address/source lookup and memory
  pressure report. Do not hand-edit it.
- `scripts/generate_dev_index.py`: regenerates the dev index after linker outputs
  change.

## Objective Check

The hack exists to recreate first-playthrough fear for someone who already knows
Pokemon. Johto should feel familiar but unsolved: boss fights are the
centerpiece, AI must not cheat with hidden information, QoL must remove tedium
without removing decisions, and weak Pokemon buffs should create real team
options that make old tier-list knowledge incomplete. Read
`docs/codex_context.md` before mechanics, balance, AI, or progression changes.

For a concise change history over base Gold, read:

- `docs/mechanics_changes_from_base.md`: mechanics, AI, progression, evolution,
  and runtime-state changes.
- `docs/balance_intent.md`: species-level balance intent, unresolved role gaps,
  and review heuristics.
- `docs/evolution_policy.md`: evolution removals, standalone policy, and current
  unresolved evolution decisions.
- `docs/buff_backlog.md`: weak-Pokemon follow-up queue.
- `docs/generated/balance_audit.md`: generated source audit for stats,
  evolutions, level-up move counts, TM counts, and reliable STAB checks.
- `docs/manifest.md`: historical data-layer rebalance manifest.
- `docs/RELEASE_NOTES.md`: release-level summary.
- `docs/project_roadmap.md`: current workstreams, statuses, blockers, and
  future-session next moves.

## Bug Hunt Route

1. Read `docs/codex_context.md` for the project objective.
2. Read `docs/codex_review_playbook.md` for review stance, risk classes, and
   report format.
3. Use `docs/generated/dev_index.md` for current labels, source anchors, tight
   banks, and free ROMX ranges.
4. Run focused audits from `tools/audit/` when relevant.

High-risk bug areas:

- Boss AI fairness and timing: `docs/boss_ai_spec.md`,
  `docs/boss_ai_bug_testing_plan.md`,
  `engine/battle/ai/boss.asm`, `engine/battle/core.asm`, `ram/wram.asm`.
- Shared battle mechanics: `engine/battle/core.asm`,
  `engine/battle/effect_commands.asm`,
  `engine/battle/type_passive_damage_mods.asm`,
  `engine/battle/late_gen_held_items.asm`.
- Data/table consistency: pointer tables and data tables in `data/` plus matching
  constants in `constants/`.
- Memory pressure: `docs/generated/dev_index.md`, `layout.link`, `ram/wram.asm`,
  `ram/sram.asm`, `ram/hram.asm`.

## Gameplay Edit Route

| Task | Start here |
| --- | --- |
| Boss AI or major-trainer difficulty | `docs/boss_ai_spec.md`, `engine/battle/ai/`, `data/trainers/ai_tiers.asm`, `data/trainers/parties.asm` |
| Battle mechanics or move effects | `engine/battle/core.asm`, `engine/battle/effect_commands.asm`, `engine/battle/move_effects`, `constants/battle_constants.asm` |
| Moves | `data/moves/moves.asm`, `data/moves/effects.asm`, `data/moves/effects_pointers.asm`, `data/moves/contact_flags.asm`, `constants/move_constants.asm` |
| Pokemon stats, types, learnsets, evolutions | `docs/balance_intent.md`, `docs/evolution_policy.md`, `docs/buff_backlog.md`, `docs/generated/balance_audit.md`, `data/pokemon/base_stats/`, `data/pokemon/base_stats.asm`, `data/pokemon/evos_attacks.asm`, `constants/pokemon_constants.asm` |
| Trainers and parties | `data/trainers/parties.asm`, `data/trainers/attributes.asm`, `data/trainers/ai_tiers.asm` |
| Maps, events, specials, QoL scripts | `maps/`, `data/maps/`, `engine/events/`, `data/events/special_pointers.asm`, `engine/overworld/` |
| Items and held items | `data/items/`, `engine/items/`, `engine/battle/late_gen_held_items.asm` |
| RAM, saves, temp state | `ram/wram.asm`, `ram/sram.asm`, `ram/hram.asm`, `docs/generated/dev_index.md` |
| Graphics or audio | `gfx/`, `data/sprites/`, `data/tilesets.asm`, `audio/`, `audio.asm` |

## Canonical Source Areas

- `main.asm`: top-level assembly entry and includes.
- `engine/`: gameplay logic and systems.
- `data/`: gameplay data tables.
- `maps/`: per-map scripts and map-specific logic.
- `constants/`: enum and constant definitions.
- `home/`: shared low-level routines.
- `ram/`: memory layout definitions.
- `audio/`, `gfx/`: audio and graphics assets/data.
- `macros/`: assembly macro helpers.
- `tools/`: build tools and helper scripts.

## Build And Verification

- `Makefile`: ROM build, cleanup, and compare targets.
- `INSTALL.md`: setup instructions.
- `docs/build.md`: build notes.
- `roms.sha1`: checksum verification targets.
- `tools/audit/`: focused validation scripts.

Useful audit commands:

```powershell
python tools\audit\check_docs_navigation.py
python tools\audit\check_release_smoke.py
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_battle_math_safety.py
python scripts\generate_balance_audit.py
```

After a successful build changes `pokegold.map` or `pokegold.sym`, refresh the
generated index with:

```powershell
python scripts\generate_dev_index.py --rom pokegold
```

## Generated, Output, And Scratch Paths

Do not use these as canonical gameplay-edit sources:

- `docs/generated/dev_index.md`: generated from linker/source outputs; refresh
  with `scripts/generate_dev_index.py`.
- `.local/`, `dist/`, `outbox/`, `workspace/`: local analysis, release outputs,
  scratch work, or copied artifacts.
- `workspace/scratch/review/`,
  `workspace/scratch/type_passives_dropin/`: archived legacy scratch trees.
- `*.gbc`, `*.o`, `*.map`, `*.sym`: build/linker outputs; do not edit by hand.

Search output or scratch paths only when the task explicitly concerns artifacts,
old analysis, or generated files.

## Source Truth Precedence

Use current source files and linker outputs (`pokegold.map`, `pokegold.sym`) as
the highest authority for exact implementation facts. Use
`docs/generated/dev_index.md` as the generated navigation mirror of those
outputs. Use hand-authored helper docs for project intent, workflow, and review
policy, and update them when they drift from source or generated truth.

## Agent Navigation Layer

`docs/agent_navigation/` is the fast routing layer for future sessions:

- `docs/agent_navigation/README.md`: navigation contract and complexity budget.
- `docs/agent_navigation/start_card.md`: one-screen lane picker for broad
  prompts.
- `docs/agent_navigation/doc_roles.md`: ownership rules for where new
  documentation facts belong.
- `docs/agent_navigation/navigation_health_check.md`: acceptance criteria for
  expanding, pruning, or completing navigation work, plus smoke routes for
  common prompt shapes.
- `docs/agent_navigation/task_router.md`: task clue to docs/source/checks route.
- `docs/agent_navigation/source_output_ownership.md`: source/generated/output
  ownership and edit policy by path class.
- `docs/agent_navigation/verification_matrix.md`: minimum checks by change kind.
- `docs/agent_navigation/artifact_catalog.md`: durable evidence and scratch
  boundary map.
- `docs/agent_navigation/custom_terms.md`: glossary for custom mechanics search
  terms and spelling traps.
- `docs/agent_navigation/subsystems/`: micro-indexes for Boss AI trace, Pokemon
  balance, trainer/boss rosters, QoL/map scripts, and checkpoint/handoff flow.
