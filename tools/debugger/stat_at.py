from __future__ import annotations

import re
from math import isqrt
from pathlib import Path
from typing import Any

from .catalog import ROOT


STAT_NAMES: tuple[str, ...] = ("hp", "atk", "def", "spd", "sat", "sdf")


STAT_INDEX: dict[str, int] = {name: index for index, name in enumerate(STAT_NAMES)}


BASE_STAT_LEVEL = 7  # in-game enum: 7 = +0 (neutral)
MAX_STAT_LEVEL = 13
MIN_STAT_LEVEL = 1
MAX_STAT_VALUE = 999
MIN_NORMAL_STAT = 5
MIN_HP_STAT = 10
MIN_MODIFIED_BATTLE_STAT = 1


DEFAULT_IV = 15  # max DV for the species (Gen 2 IV cap)
DEFAULT_EV = 65_535  # max EV for the species, the in-game grind ceiling
DEFAULT_LEVEL = 50


_STAT_LINE_PATTERN = re.compile(
    r"^\s*db\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)",
)


def build_stat_at_report(
    *,
    species: str,
    stat: str,
    level: int = DEFAULT_LEVEL,
    modifier: int = 0,
    iv: int = DEFAULT_IV,
    ev: int = DEFAULT_EV,
    root: Path = ROOT,
) -> dict[str, Any]:
    species_input = species.strip()
    stat_normalized = stat.strip().lower()
    if stat_normalized not in STAT_INDEX:
        return {
            "schema_version": 1,
            "kind": "unified_debugger_stat_at",
            "valid": False,
            "errors": [
                f"unknown stat {stat!r}; expected one of {', '.join(STAT_NAMES)}",
            ],
        }
    if not 1 <= level <= 100:
        return {
            "schema_version": 1,
            "kind": "unified_debugger_stat_at",
            "valid": False,
            "errors": [f"level {level} is outside 1..100"],
        }
    if not 0 <= iv <= 15:
        return {
            "schema_version": 1,
            "kind": "unified_debugger_stat_at",
            "valid": False,
            "errors": [f"IV {iv} is outside 0..15"],
        }
    if not 0 <= ev <= 65_535:
        return {
            "schema_version": 1,
            "kind": "unified_debugger_stat_at",
            "valid": False,
            "errors": [f"EV {ev} is outside 0..65535"],
        }
    base_file = _resolve_base_stats_file(species_input, root=root)
    if base_file is None:
        return {
            "schema_version": 1,
            "kind": "unified_debugger_stat_at",
            "valid": False,
            "errors": [f"no base_stats file for species {species_input!r}"],
        }
    bases = _read_base_stats(base_file)
    base_value = bases[STAT_INDEX[stat_normalized]]
    multipliers = _read_stat_multipliers(root)
    if not (MIN_STAT_LEVEL <= BASE_STAT_LEVEL + modifier <= MAX_STAT_LEVEL):
        return {
            "schema_version": 1,
            "kind": "unified_debugger_stat_at",
            "valid": False,
            "errors": [
                f"modifier {modifier:+d} maps to stage {BASE_STAT_LEVEL + modifier}; valid range is -6..+6",
            ],
        }
    neutral = _compute_stat(
        base=base_value,
        iv=iv,
        ev=ev,
        level=level,
        is_hp=(stat_normalized == "hp"),
    )
    if stat_normalized == "hp":
        # HP is never modified by stat-stage boosts in Gen 2.
        modified = neutral
        num, denom = (1, 1)
    else:
        if modifier not in multipliers:
            return {
                "schema_version": 1,
                "kind": "unified_debugger_stat_at",
                "valid": False,
                "errors": [f"stat multiplier table has no entry for {modifier:+d}"],
            }
        num, denom = multipliers[modifier]
        modified = min(MAX_STAT_VALUE, (neutral * num) // denom)
        modified = max(MIN_MODIFIED_BATTLE_STAT, modified)
    species_enum = _read_species_enum(base_file)
    return {
        "schema_version": 1,
        "kind": "unified_debugger_stat_at",
        "valid": True,
        "species": species_enum,
        "source_file": base_file.relative_to(root).as_posix(),
        "stat": stat_normalized,
        "base": base_value,
        "level": level,
        "iv": iv,
        "ev": ev,
        "modifier": modifier,
        "stage_multiplier": {
            "num": num,
            "denom": denom,
            "decimal": (num / denom) if stat_normalized != "hp" else 1.0,
        },
        "computed_neutral": neutral,
        "computed_modified": modified,
    }


def _resolve_base_stats_file(species: str, *, root: Path) -> Path | None:
    stem = species.lower()
    if stem.endswith(".asm"):
        stem = stem[:-4]
    candidate = root / "data" / "pokemon" / "base_stats" / f"{stem}.asm"
    return candidate if candidate.is_file() else None


def _read_base_stats(base_file: Path) -> tuple[int, ...]:
    for line in base_file.read_text(encoding="utf-8").splitlines():
        match = _STAT_LINE_PATTERN.match(line)
        if match:
            return tuple(int(value) for value in match.groups())
    raise ValueError(f"no `db hp, atk, def, spd, sat, sdf` line in {base_file}")


_ENUM_LINE_PATTERN = re.compile(r"^\s*db\s+([A-Z_][A-Z0-9_]*)\s*;")


def _read_species_enum(base_file: Path) -> str:
    for line in base_file.read_text(encoding="utf-8").splitlines():
        match = _ENUM_LINE_PATTERN.match(line)
        if match:
            return match.group(1)
    return base_file.stem.upper()


_MULT_LINE_PATTERN = re.compile(
    r"^\s*db\s+(\d+)\s*,\s*(\d+)\s*;\s*([+-]?\d+)\s*=",
)


def _read_stat_multipliers(root: Path) -> dict[int, tuple[int, int]]:
    path = root / "data" / "battle" / "stat_multipliers.asm"
    out: dict[int, tuple[int, int]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _MULT_LINE_PATTERN.match(line)
        if not match:
            continue
        num = int(match.group(1))
        denom = int(match.group(2))
        stage_label = int(match.group(3))
        out[stage_label] = (num, denom)
    return out


def _compute_stat(
    *,
    base: int,
    iv: int,
    ev: int,
    level: int,
    is_hp: bool,
) -> int:
    # Gen 2 computed-stat formula. See `engine/pokemon/move_mon.asm:1414` (CalcMonStats):
    # the in-game routine integer-square-roots StatExp before dividing by 4 (the
    # `.sqrt_loop` at 1470). Bulbapedia's Gen 2 stat formula is:
    #   floor( ((base + DV) * 2 + floor(sqrt(StatExp)) // 4) * Level / 100 ) + (5 or Level+10 for HP)
    stat_exp_sqrt = _isqrt(ev)
    inner = ((base + iv) * 2 + stat_exp_sqrt // 4) * level // 100
    if is_hp:
        return inner + level + MIN_HP_STAT
    return inner + MIN_NORMAL_STAT


def _isqrt(value: int) -> int:
    if value < 0:
        return 0
    return isqrt(value)


def format_text(report: dict[str, Any]) -> str:
    if not report.get("valid"):
        errors = report.get("errors") or ["unknown error"]
        return "Stat-at report: INVALID\n" + "\n".join(f"  {line}" for line in errors)
    lines: list[str] = []
    species = report["species"]
    stat = report["stat"].upper()
    base = report["base"]
    neutral = report["computed_neutral"]
    modified = report["computed_modified"]
    mult = report["stage_multiplier"]
    modifier = report["modifier"]
    level = report["level"]
    iv = report["iv"]
    ev = report["ev"]
    lines.append("Unified Pokemon Gold romhack debugger stat-at")
    lines.append(
        f"species={species} stat={stat} level={level} IV={iv} EV={ev} source={report['source_file']}"
    )
    lines.append("")
    lines.append(f"base {stat}: {base}")
    lines.append(f"computed at +0 (level {level}, IV={iv}, EV={ev}): {neutral}")
    if stat.lower() == "hp":
        lines.append("(HP is not affected by stat-stage modifiers in Gen 2.)")
        return "\n".join(lines)
    lines.append(
        f"stage modifier {modifier:+d} multiplier: {mult['num']}/{mult['denom']}"
        f"  (~{mult['decimal']:.2f}x)"
    )
    lines.append(f"computed at {modifier:+d}: {modified}")
    lines.append("")
    if modifier != 0:
        delta = modified - neutral
        naive_base_equivalent = int(base * mult["decimal"])
        naive_base_neutral = _compute_stat(
            base=naive_base_equivalent,
            iv=iv,
            ev=ev,
            level=level,
            is_hp=False,
        )
        lines.append(
            f"reminder: stage {modifier:+d} multiplies the COMPUTED stat ({neutral}),"
            f" not the base ({base}); the +5 floor and IV/EV term scale through."
        )
        lines.append(
            f"  base * stage_multiplier would be {naive_base_equivalent}, but the actual"
            f" computed-at-{modifier:+d} stat is {modified} (delta {delta:+d} from neutral)."
        )
        lines.append(
            f"  for reference, a base {naive_base_equivalent} mon at +0 computes to"
            f" {naive_base_neutral}; that is still not equivalent to base {base} at {modifier:+d}."
        )
    return "\n".join(lines)
