from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.damage_debugger import state as damage_state
from tools.damage_debugger import tables


def build_learnset_inspection_report(*, species: str, level: int) -> dict[str, Any]:
    base_stats = tables.load_base_stats()
    resolved_species = tables.resolve_name(species, base_stats, "species")
    learned = damage_state.load_level_up_moves().get(resolved_species, ())
    available = [
        {"level": move_level, "move": move}
        for move_level, move in learned
        if move_level <= level
    ]
    future = [
        {"level": move_level, "move": move}
        for move_level, move in learned
        if move_level > level
    ]
    current_moves = list(damage_state.level_up_moves_for_species(resolved_species, level))
    return {
        "schema_version": 1,
        "kind": "unified_debugger_learnset_inspection",
        "valid": True,
        "species": resolved_species,
        "level": level,
        "current_moves": current_moves,
        "available_level_up_moves": available,
        "future_level_up_moves": future,
        "commands": [
            f"python -m tools.debugger learnset-inspect --species {resolved_species} --level {level}",
            f"python -m tools.debugger content-mirror --source-file data/pokemon/evos_attacks.asm --json-out .local\\tmp\\evos_attacks_mirror.json",
        ],
        "known_limits": [
            "This inspects source learnset semantics and the four-move level-up projection; it does not patch an existing save by itself.",
            "Use party-inspect against a save when the question is what a specific party Pokemon currently knows.",
        ],
    }


def build_party_inspection_report(
    *,
    save: str | Path,
    slots: tuple[int, ...],
    rom: str | Path = damage_state.DEFAULT_ROM,
    symbols: str | Path = damage_state.DEFAULT_SYMBOLS,
) -> dict[str, Any]:
    requested_slots = slots or (1,)
    entries = []
    errors = []
    for slot in requested_slots:
        try:
            mon = damage_state.party_state_from_save(
                Path(save),
                slot,
                rom=Path(rom),
                symbols_path=Path(symbols),
            )
        except damage_state.StateInputError as exc:
            errors.append({"slot": slot, "error": str(exc)})
            continue
        entries.append(damage_state.state_to_json(mon))
    return {
        "schema_version": 1,
        "kind": "unified_debugger_party_inspection",
        "valid": not errors,
        "save": str(save),
        "slots": list(requested_slots),
        "party": entries,
        "errors": errors,
        "commands": [
            f"python -m tools.debugger party-inspect --save {save} "
            + " ".join(f"--slot {slot}" for slot in requested_slots)
        ],
        "known_limits": [
            "Battery-save inspection boots through Continue and reads the resulting party state.",
            "This is a read-only inspection; use an explicit save patcher for edits.",
        ],
    }


def build_grass_regrowth_report(*, max_total_hp: int = 300) -> dict[str, Any]:
    max_hp = max(1, max_total_hp)
    return {
        "schema_version": 1,
        "kind": "unified_debugger_grass_regrowth_report",
        "valid": True,
        "max_total_hp": max_hp,
        "formula": {
            "full_grass": "max(1, floor((maxHP + 16) / 32))",
            "half_grass": "max(1, floor((maxHP + 32) / 64))",
        },
        "cutoffs": {
            "full_grass": _healing_ranges(max_hp=max_hp, divisor=32, bias=16),
            "half_grass": _healing_ranges(max_hp=max_hp, divisor=64, bias=32),
        },
        "commands": [
            f"python -m tools.debugger grass-regrowth --max-total-hp {max_hp}",
            "python -m tools.debugger content-mirror --source-file engine/battle/type_passive_damage_mods.asm",
        ],
        "known_limits": [
            "This mirrors the current source formula in HandleTypePassiveRegrowth_Far.",
            "It reports healing from max HP only; battle eligibility still depends on Grass contribution, no status, and not already full HP.",
        ],
    }


def _healing_ranges(*, max_hp: int, divisor: int, bias: int) -> list[dict[str, int]]:
    ranges: list[dict[str, int]] = []
    start = 1
    current = _rounded_heal(1, divisor=divisor, bias=bias)
    for hp in range(2, max_hp + 1):
        value = _rounded_heal(hp, divisor=divisor, bias=bias)
        if value == current:
            continue
        ranges.append({"min_hp": start, "max_hp": hp - 1, "heals": current})
        start = hp
        current = value
    ranges.append({"min_hp": start, "max_hp": max_hp, "heals": current})
    return ranges


def _rounded_heal(max_hp: int, *, divisor: int, bias: int) -> int:
    return max(1, (max_hp + bias) // divisor)
