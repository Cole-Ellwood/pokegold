# Custom Mechanics Glossary

Use this when a future session remembers a concept but not the exact symbol,
file, or spelling. Terms are grouped by search surface, not by player-facing
feature category.

## Battle Mechanics Terms

| Term helpers | Meaning | Primary route |
| --- | --- | --- |
| `Type Passive V1`, type passives, Dragon's Majesty, Imperial Scales | Type-based passive damage/status/accuracy mechanics. | `docs/mechanics_changes_from_base.md`, `engine/battle/type_passive_damage_mods.asm` |
| Dragon-only Outrage category exception, effective category | Dragon users can make `OUTRAGE` use physical category under defined stat conditions. | `docs/mechanics_changes_from_base.md`, `engine/battle/core.asm`, `engine/battle/type_passive_damage_mods.asm` |
| Spikes layers, Rapid Spin rework | Three-layer Spikes and full Rapid Spin clearing. | `engine/battle/move_effects/spikes.asm`, `engine/battle/move_effects/rapid_spin.asm` |
| Contact flags, Rocky Helmet, Poison retaliation | Gen 6-style contact table used by multiple battle effects. | `data/moves/contact_flags.asm`, `engine/battle/type_passive_damage_mods.asm` |
| Ditto Imposter, auto-transform | Ditto auto-Transform on switch-in when legal. | `engine/battle/ditto_imposter.asm`, `engine/battle/core.asm` |

## Held Item Terms

| Search terms | Route |
| --- | --- |
| `CHOICE_BAND`, `CHOICE_SPECS`, `CHOICE_SCARF`, choice lock | `engine/battle/late_gen_held_items.asm`, `engine/battle/core.asm` |
| `ASSAULT_VEST`, status move block, vest legality | `engine/battle/late_gen_held_items.asm`, `engine/battle/core.asm`, `data/text/battle.asm` |
| `EVOLITE`, Eviolite, `EvioliteDesc` | `engine/battle/late_gen_held_items.asm`, `data/items/descriptions.asm` |
| `AIR_BALLOON`, Ground immunity, balloon pop | `engine/battle/late_gen_held_items.asm`, `engine/battle/core.asm` |
| `SHELL_BELL`, `ROCKY_HELMET`, `METRONOME_ITEM` | `engine/battle/late_gen_held_items.asm`, `engine/battle/used_move_text.asm` |

## AI And Trainer Terms

| Search terms | Route |
| --- | --- |
| Boss AI tier, `AI_TIER_EARLY`, `AI_TIER_MID`, `AI_TIER_LATE` | `data/trainers/ai_tiers.asm`, `constants/trainer_data_constants.asm` |
| no-cheat, hidden information, current-turn input | `docs/boss_ai_spec.md`, `engine/battle/ai/` |
| scout move, scout pivot, plausible risk | `engine/battle/ai/`, `docs/boss_ai_trace_capture.md` |
| live capture, trace ROM, `BOSS_AI_TRACE` | `docs/agent_navigation/subsystems/boss_ai_trace.md` |
| gym scout dossier | `docs/project_roadmap.md` row `BOSSAI-002` |

## Progression And QoL Terms

| Search terms | Route |
| --- | --- |
| Move Reminder, relearn flow, page size | `engine/events/move_reminder.asm`, `maps/DayCare.asm` |
| branching evolution choice menu | `engine/pokemon/evolve.asm`, `docs/evolution_policy.md` |
| FAST text speed default | `data/default_options.asm`, `docs/qol_handoff.md` |
| Bicycle auto-register | `maps/GoldenrodBikeShop.asm`, `engine/overworld/select_menu.asm` |
| Repel renewal prompt | `docs/qol_handoff.md`, `engine/overworld/events.asm`, `engine/events/repel.asm`, `engine/items/item_effects.asm` |
| Pokemon Center friction trim | `docs/qol_handoff.md`, `engine/events/std_scripts.asm` |

## Common Spelling Traps

| If searching for | Also search |
| --- | --- |
| Eviolite | `EVOLITE`, `EvioliteDesc` |
| Choice lock | `wPlayerChoiceLockedMove`, `wEnemyChoiceLockedMove`, `IsChoiceHeldEffect_Far` |
| Metronome item | `METRONOME_ITEM`, `wPlayerMetronomeMove`, `wPlayerMetronomeCount` |
| Boss trace | `BOSS_AI_TRACE`, `wBossAITrace`, `live_capture_manifest` |
