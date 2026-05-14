# Type-Effectiveness Evidence Report

Generated: 2026-05-14T03:34:37+00:00

## Summary

- Chart tweaks checked: 15
- Chart tweaks pass: `True`
- Steel/Ghost/Dark divergence pass: `True`
- Text claims scanned: 22
- Unsupported text claims: 0
- All pass: `True`

## Source Hierarchy

- General mechanics: source code is authority for general mechanics.
- Exact battle-state damage: validated debugger trace is authority for exact battle-state damage.
- Disagreement: treat disagreement as source/tooling/version mismatch and investigate.

## Required Source Paths

- `data/types/type_matchups.asm`
- `docs/agent_navigation/gen2_vs_modern_mechanics.md`
- `docs/agent_navigation/hack_mechanics_reference.md`
- `engine/battle/core.asm`
- `engine/battle/move_effects/rapid_spin.asm`
- `engine/battle/move_effects/spikes.asm`
- `engine/battle/type_passive_damage_mods.asm`

## Romhack Type-Chart Tweaks

| ID | Attack | Defend | Vanilla | Romhack | Source | Pass |
| --- | --- | --- | --- | --- | --- | --- |
| `ground_ghost_immunity` | `GROUND` | `GHOST` | `neutral` | `immune` | `data/types/type_matchups.asm` | `True` |
| `water_ice_resisted` | `WATER` | `ICE` | `neutral` | `resisted` | `data/types/type_matchups.asm` | `True` |
| `ground_fire_neutral` | `GROUND` | `FIRE` | `super_effective` | `neutral` | `data/types/type_matchups.asm` | `True` |
| `steel_fighting_resisted` | `STEEL` | `FIGHTING` | `neutral` | `resisted` | `data/types/type_matchups.asm` | `True` |
| `rock_psychic_resisted` | `ROCK` | `PSYCHIC_TYPE` | `neutral` | `resisted` | `data/types/type_matchups.asm` | `True` |
| `normal_psychic_resisted` | `NORMAL` | `PSYCHIC_TYPE` | `neutral` | `resisted` | `data/types/type_matchups.asm` | `True` |
| `ghost_steel_no_effect` | `GHOST` | `STEEL` | `resisted` | `immune` | `data/types/type_matchups.asm` | `True` |
| `ghost_fighting_super_effective` | `GHOST` | `FIGHTING` | `neutral` | `super_effective` | `data/types/type_matchups.asm` | `True` |
| `poison_normal_super_effective` | `POISON` | `NORMAL` | `neutral` | `super_effective` | `data/types/type_matchups.asm` | `True` |
| `dark_steel_neutral` | `DARK` | `STEEL` | `resisted` | `neutral` | `data/types/type_matchups.asm` | `True` |
| `steel_electric_neutral` | `STEEL` | `ELECTRIC` | `resisted` | `neutral` | `data/types/type_matchups.asm` | `True` |
| `grass_flying_neutral` | `GRASS` | `FLYING` | `resisted` | `neutral` | `data/types/type_matchups.asm` | `True` |
| `fighting_poison_neutral` | `FIGHTING` | `POISON` | `resisted` | `neutral` | `data/types/type_matchups.asm` | `True` |
| `fighting_bug_neutral` | `FIGHTING` | `BUG` | `resisted` | `neutral` | `data/types/type_matchups.asm` | `True` |
| `psychic_poison_neutral` | `PSYCHIC_TYPE` | `POISON` | `super_effective` | `neutral` | `data/types/type_matchups.asm` | `True` |

## Unsupported Text Claims

- none