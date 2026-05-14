# Task Router

Use this as the first constant-time classifier after reading
`docs/README.md`, `docs/project_context.md`, and `docs/project_roadmap.md`.

The goal is not to describe the whole project. The goal is to prevent a future
helper from searching the whole project when one row already names the right
surface.

Routing invariant: every lane serves the First-Playthrough Promise. Boss AI,
balance, mechanics, and QoL should restore uncertainty for a veteran player,
not drift into generic hard mode, pure competitive tuning, or convenience that
erases the journey.

| User request clue | Read first | Primary source surface | Verify with | Avoid starting in |
| --- | --- | --- | --- | --- |
| "make the app better", "make the game better", "do what matters", "important improvement", "keep improving this" | `docs/agent_navigation/important_improvement_menu.md`, then the one matching router row or subsystem micro-index | Depends on chosen lane: Boss AI, live proof, cheap difficulty, Pokemon balance, QoL, battle correctness, release confidence, docs, or repo hygiene | Verification matrix row for the chosen lane; update `docs/project_roadmap.md` and leave audit/decision/journal notes at the right durability level | Doing a little of every lane, adding novelty before checking proof gaps, or leaving useful findings only in chat. |
| "bug could be anywhere", "exhaustive bug hunt", "release-facing review", "search every line" | `docs/bug_hunt_master_playbook.md`, `docs/review_playbook.md`, `docs/agent_navigation/verification_matrix.md` | Route from the master playbook to Boss AI, battle mechanics, Pokemon data, progression scripts, build/release, or docs after startup. | `python tools\audit\bug_hunt_triage.py`, then the broad command floor in `docs/bug_hunt_master_playbook.md`, then subsystem-specific audits from this router. | Random full-repo scrolling before choosing invariants and source owners. |
| "boss AI", "trainer AI", "leader is cheating", "switch logic", "major trainer difficulty" | `docs/agent_navigation/subsystems/boss_ai_logic.md`, `docs/agent_navigation/subsystems/trainer_boss_roster.md`, `docs/boss_ai_spec.md`, `docs/boss_ai_bug_testing_plan.md`, `docs/boss_ai_post_patch_notes.md` | `engine/battle/ai/`, `engine/battle/ai/items.asm`, `engine/battle/ai/switch.asm`, `engine/battle/ai/scoring.asm`, `engine/battle/ai/move.asm`, `engine/battle/core.asm`, `data/trainers/ai_tiers.asm`, `data/trainers/parties.asm` | `python tools\audit\check_boss_ai_no_cheat.py`, `python tools\audit\check_boss_ai_gating.py`, `python tools\audit\check_boss_ai_trace_invariants.py`, `python tools\audit\check_boss_ai_memory_budget.py` | Broad `engine/` search before reading the Boss AI docs. |
| "live proof", "trace", "gym leader/Koga/Lance/Red proof" | `docs/agent_navigation/subsystems/boss_ai_trace.md`, `docs/boss_ai_trace_capture.md`, `audit/boss_ai_trace/live_capture_ledger.md`, `audit/boss_ai_trace/live_capture_manifest.json` | `tools/trace/boss_ai_state_factory.py`, `tools/trace/boss_ai_trace_state_probe.py`, `tools/trace/boss_ai_trace_capture.py`, `tools/trace/boss_ai_trace_batch.py`, trace ROM outputs | `python tools\trace\boss_ai_trace_capture.py --symbols-only`, `python tools\trace\boss_ai_state_factory.py --all --update-manifest` for real trainers, Morty-only strict probe when the candidate is Morty, `python tools\trace\boss_ai_trace_batch.py`, `python tools\audit\check_boss_ai_live_capture_ledger.py` | Treating old `.local/` RAM as proof without matching current trace ROM state and passing any manifest-owned strict preflight. |
| "cheap difficulty", "unfair", "too grindy", "boss feels bad" | `docs/project_context.md`, `docs/review_playbook.md`, `docs/project_roadmap.md` | Depends on finding: Boss AI, trainer parties, Pokemon data, item economy, map scripts | Start with `python tools\audit\check_cheap_difficulty.py`, then audits for the touched system; build if source changed. | Cosmetic balance edits before identifying the unfair mechanism. |
| "Pokemon buff", "weak Pokemon", "stats", "typing", "learnset", "evolution" | `docs/agent_navigation/hack_mechanics_reference.md`, `docs/agent_navigation/subsystems/pokemon_balance.md`, `docs/balance_intent.md`, `docs/evolution_policy.md`, `docs/buff_backlog.md`, `docs/generated/balance_audit.md` | `data/pokemon/base_stats/`, `data/pokemon/base_stats.asm`, `data/pokemon/evos_attacks.asm`, `data/pokemon/evos_attacks_pointers.asm`, `data/pokemon/egg_moves.asm`, `constants/pokemon_constants.asm` | `python scripts\generate_balance_audit.py`, `python tools\audit\check_mechanics_docs_and_fixtures.py`, `python tools\audit\check_release_smoke.py` | Editing species data without checking evolution timing and trainer usage. |
| "move", "effect", "description", "contact", "category", "damage formula" | `docs/agent_navigation/hack_mechanics_reference.md`, `docs/mechanics_changes_from_base.md`, `docs/review_playbook.md` | `data/moves/`, `engine/battle/effect_commands.asm`, `engine/battle/core.asm`, `engine/battle/type_passive_damage_mods.asm`, `engine/battle/late_gen_held_items.asm`, `constants/move_constants.asm` | `python scripts\generate_hack_mechanics_reference.py`, `python tools\audit\check_mechanics_docs_and_fixtures.py`, `python tools\audit\check_battle_math_safety.py`, release smoke, build both ROMs | Updating one battle consumer while leaving Counter, Mirror Coat, crit stat choice, or held-item boosts stale. |
| "item", "held item", "mart", "description", "Assault Vest", "Choice" | `docs/agent_navigation/hack_mechanics_reference.md`, `docs/mechanics_changes_from_base.md`, `docs/project_map.md` | `data/items/`, `engine/items/`, `engine/battle/late_gen_held_items.asm` | `python scripts\generate_hack_mechanics_reference.py`, `python tools\audit\check_mechanics_docs_and_fixtures.py`, release smoke, relevant battle/item audit if available, build both ROMs | Editing item data without descriptions, names, pockets, and battle behavior in sync. |
| "QoL", "repel", "Pokemon Center", "move reminder", "tutor", "friction" | `docs/agent_navigation/subsystems/qol_map_scripts.md`, `docs/qol_handoff.md`, `docs/project_context.md` | `maps/`, `engine/events/`, `data/events/special_pointers.asm`, `engine/overworld/` | `python tools\audit\check_release_smoke.py`, map/script build, manual note for playtest gaps | QoL that removes preparation pressure or strategic cost. |
| "map", "NPC", "script", "event", "text on sign", "gym guide" | `docs/agent_navigation/subsystems/qol_map_scripts.md`, `docs/project_map.md`, `docs/generated/dev_index.md` | `maps/`, `data/maps/`, `engine/events/`, `data/events/special_pointers.asm` | Build both ROMs, release smoke, map-specific manual note | Editing a script without checking its map bank and special pointer. |
| "graphics", "sprite", "pic", "tileset", "palette", "scrambled tiles", "jumbled map", "VBA glitch", "PyBoy save" | `docs/graphics_emulator_debugging.md`, `docs/project_map.md`, `docs/generated/dev_index.md` | `gfx/`, `data/sprites/`, `data/tilesets.asm`, `gfx/pics_gold.asm`, `home/window.asm`, `home/text.asm`, `home/map.asm`, `home/audio.asm` | Build both ROMs; visual check if possible; for VBA-only glitches, record the emulator/manual proof gap | Assuming graphics are code-free when pointer tables, bank layout, BG map copying, or emulator timing may move. |
| "audio", "music", "cry", "sfx" | `docs/project_map.md`, `docs/generated/dev_index.md` | `audio/`, `audio.asm`, `constants/music_constants.asm`, `constants/sfx_constants.asm` | Build both ROMs; audio/manual gap note if not played | Large audio edits in tight banks without checking generated index. |
| "build", "release", "checksum", "up to date" | `docs/agent_navigation/source_output_ownership.md`, `docs/build.md`, `docs/validation_report.md`, `docs/generated/dev_index.md` | `Makefile`, `roms.sha1`, linker outputs, `tools/` | WSL `make` command in `docs/build.md`, `python tools\audit\check_docs_navigation.py` | Declaring build blocked before checking WSL and repo-local RGBDS. |
| "docs", "roadmap", "organize", "beautiful", "10/10", "workspace hygiene", "physical clutter", "future sessions" | `docs/agent_navigation/README.md`, `docs/agent_navigation/subsystems/checkpoint_handoff.md`, `docs/README.md`, `docs/project_roadmap.md` | `docs/`, `audit/`, `decisions/`, `journal/`; build layout only with explicit approval | `python tools\audit\check_workspace_hygiene.py`, `python tools\audit\check_docs_navigation.py`, `git diff --check` | Touching gameplay source, deleting ignored outputs, or relocating build products while in a docs/workspace-hygiene pass. |
| custom mechanic name, unfamiliar term, half-remembered feature | `docs/agent_navigation/hack_mechanics_reference.md`, `docs/agent_navigation/custom_terms.md`, `docs/mechanics_changes_from_base.md` | Depends on term route. | Verification matrix row for the target subsystem; `python tools\audit\check_mechanics_docs_and_fixtures.py` if the answer touches mechanics claims. | Broad source search before trying known spelling variants. |

## Search Escalation

If no row matches:

1. Search docs first:

```powershell
rg -n "keyword|related phrase" docs
```

2. Search source by likely subsystem:

```powershell
rg -n "SymbolOrPhrase" engine data maps constants ram
```

3. If the route was missing, update this file or `docs/project_map.md` before
   ending the session.
