from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .catalog import ROOT


REAL_TYPES: tuple[str, ...] = (
    "NORMAL",
    "FIGHTING",
    "FLYING",
    "POISON",
    "GROUND",
    "ROCK",
    "BUG",
    "GHOST",
    "STEEL",
    "FIRE",
    "WATER",
    "GRASS",
    "ELECTRIC",
    "PSYCHIC_TYPE",
    "ICE",
    "DRAGON",
    "DARK",
)


MULTIPLIERS: dict[str, float] = {
    "SUPER_EFFECTIVE": 2.0,
    "EFFECTIVE": 1.0,
    "NOT_VERY_EFFECTIVE": 0.5,
    "NO_EFFECT": 0.0,
}


_TYPE_LINE_PATTERN = re.compile(
    r"^\s*db\s+([A-Z_]+)\s*,\s*([A-Z_]+)\s*;\s*type",
)


_MATCHUP_PATTERN = re.compile(
    r"^\s*db\s+([A-Z_]+)\s*,\s*([A-Z_]+)\s*,\s*([A-Z_]+)\s*$",
)


def build_type_matchup_report(*, species: str, root: Path = ROOT) -> dict[str, Any]:
    species_input = species.strip()
    base_file = _resolve_base_stats_file(species_input, root=root)
    if base_file is None:
        return {
            "schema_version": 1,
            "kind": "unified_debugger_type_matchup",
            "valid": False,
            "species_input": species_input,
            "errors": [f"no base_stats file for species {species_input!r}"],
        }
    type1, type2 = _read_species_types(base_file)
    species_enum = _read_species_enum(base_file)
    matchups = _read_matchup_table(root)
    defensive = _compute_defensive(type1, type2, matchups)
    offensive = _compute_offensive(type1, type2, matchups)
    types_list = [type1] if type2 == type1 else [type1, type2]
    return {
        "schema_version": 1,
        "kind": "unified_debugger_type_matchup",
        "valid": True,
        "species": species_enum,
        "source_file": base_file.relative_to(root).as_posix(),
        "types": types_list,
        "defensive_multipliers": defensive,
        "offensive_multipliers": offensive,
    }


def _resolve_base_stats_file(species: str, *, root: Path) -> Path | None:
    stem = species.lower()
    if stem.endswith(".asm"):
        stem = stem[:-4]
    candidate = root / "data" / "pokemon" / "base_stats" / f"{stem}.asm"
    return candidate if candidate.is_file() else None


def _read_species_types(base_file: Path) -> tuple[str, str]:
    for line in base_file.read_text(encoding="utf-8").splitlines():
        match = _TYPE_LINE_PATTERN.match(line)
        if match:
            return match.group(1), match.group(2)
    raise ValueError(f"no `db <T1>, <T2> ; type` line in {base_file}")


_ENUM_LINE_PATTERN = re.compile(r"^\s*db\s+([A-Z_][A-Z0-9_]*)\s*;")


def _read_species_enum(base_file: Path) -> str:
    for line in base_file.read_text(encoding="utf-8").splitlines():
        match = _ENUM_LINE_PATTERN.match(line)
        if match:
            return match.group(1)
    return base_file.stem.upper()


def _read_matchup_table(root: Path) -> dict[tuple[str, str], float]:
    path = root / "data" / "types" / "type_matchups.asm"
    out: dict[tuple[str, str], float] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _MATCHUP_PATTERN.match(line)
        if not match:
            continue
        attacker, defender, multiplier_name = match.groups()
        if multiplier_name not in MULTIPLIERS:
            continue
        out[(attacker, defender)] = MULTIPLIERS[multiplier_name]
    return out


def _compute_defensive(
    type1: str,
    type2: str,
    matchups: dict[tuple[str, str], float],
) -> dict[str, float]:
    out: dict[str, float] = {}
    for attacker in REAL_TYPES:
        m1 = matchups.get((attacker, type1), 1.0)
        m2 = matchups.get((attacker, type2), 1.0) if type2 != type1 else 1.0
        out[attacker] = m1 * m2
    return out


def _compute_offensive(
    type1: str,
    type2: str,
    matchups: dict[tuple[str, str], float],
) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    seen_types = [type1] if type2 == type1 else [type1, type2]
    for attacker in seen_types:
        per_type: dict[str, float] = {}
        for defender in REAL_TYPES:
            per_type[defender] = matchups.get((attacker, defender), 1.0)
        out[attacker] = per_type
    return out


def format_text(report: dict[str, Any]) -> str:
    if not report.get("valid"):
        errors = report.get("errors") or ["unknown error"]
        return "Type matchup report: INVALID\n" + "\n".join(f"  {line}" for line in errors)
    lines: list[str] = []
    species = report["species"]
    types = "/".join(report["types"])
    lines.append("Unified Pokemon Gold romhack debugger type matchup")
    lines.append(
        f"species={species} types={types} source={report['source_file']}"
    )
    lines.append("")
    lines.append("Defensive multipliers (incoming attack vs this species):")
    by_mult: dict[float, list[str]] = {}
    for attacker, mult in report["defensive_multipliers"].items():
        by_mult.setdefault(mult, []).append(attacker)
    for mult in sorted(by_mult.keys(), reverse=True):
        attackers = ", ".join(sorted(by_mult[mult]))
        label = "immune" if mult == 0.0 else f"{_fmt_mult(mult)}x"
        lines.append(f"  {label}: {attackers}")
    lines.append("")
    lines.append("Offensive multipliers (this species attacking):")
    for attacker, per_def in report["offensive_multipliers"].items():
        lines.append(f"  as {attacker}:")
        per_mult: dict[float, list[str]] = {}
        for defender, mult in per_def.items():
            if mult == 1.0:
                continue
            per_mult.setdefault(mult, []).append(defender)
        if not per_mult:
            lines.append("    no non-neutral matchups")
            continue
        for mult in sorted(per_mult.keys(), reverse=True):
            defs = ", ".join(sorted(per_mult[mult]))
            label = "no effect" if mult == 0.0 else f"{_fmt_mult(mult)}x"
            lines.append(f"    {label}: {defs}")
    return "\n".join(lines)


def _fmt_mult(value: float) -> str:
    rounded = round(value, 4)
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:g}"


def main(argv=None) -> int:
    """CLI: defensive type matchup for a species (this hack re-types some mons).

    Wired into the front door as ``python -m tools.debugger type-matchup`` (v2
    passthrough). Reads the in-repo type chart, not vanilla Gen 2 assumptions.
    """
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(prog="python -m tools.debugger type-matchup")
    parser.add_argument("--species", required=True)
    parser.add_argument("--json", action="store_true", help="machine-readable JSON")
    args = parser.parse_args(list(argv) if argv is not None else sys.argv[1:])
    report = build_type_matchup_report(species=args.species)
    print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else format_text(report))
    return 0 if report.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
