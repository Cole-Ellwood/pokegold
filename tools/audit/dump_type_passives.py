#!/usr/bin/env python3
"""Dump Type Passives V1 contributions per species.

Outputs:
  audit/type_passives.csv

Columns:
  species,type1,type2,effective_contributions
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path


TYPE_LINE_RE = re.compile(r"^\s*db\s+([A-Z_]+)\s*,\s*([A-Z_]+)\b")
INCLUDE_RE = re.compile(r'^\s*INCLUDE\s+"([^"]+)"\s*$')

VALID_TYPES = {
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
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def species_token(path: Path) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "_", path.stem).strip("_").upper()
    return re.sub(r"_+", "_", token)


def contribution_text(type1: str, type2: str) -> str:
    if type1 == type2:
        return f"{type1}=full"
    return f"{type1}=half;{type2}=half"


def parse_types(path: Path) -> tuple[str, str] | None:
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = TYPE_LINE_RE.match(raw)
        if not m:
            continue
        t1 = m.group(1).upper()
        t2 = m.group(2).upper()
        if t1 in VALID_TYPES and t2 in VALID_TYPES:
            return t1, t2
    return None


def ordered_base_stat_files(root: Path) -> list[Path]:
    include_root = root / "data" / "pokemon" / "base_stats.asm"
    if not include_root.exists():
        return sorted((root / "data" / "pokemon" / "base_stats").glob("*.asm"))

    files: list[Path] = []
    for raw in include_root.read_text(encoding="utf-8", errors="replace").splitlines():
        m = INCLUDE_RE.match(raw)
        if not m:
            continue
        include_path = (root / m.group(1)).resolve()
        if include_path.is_file() and include_path.suffix.lower() == ".asm":
            if "base_stats" in include_path.parts:
                files.append(include_path)
    return files


def main() -> int:
    root = repo_root()
    files = ordered_base_stat_files(root)
    if not files:
        print("ERROR: no base stats files found", file=sys.stderr)
        return 2

    rows: list[dict[str, str]] = []
    missing: list[str] = []
    for path in files:
        parsed = parse_types(path)
        if not parsed:
            missing.append(str(path))
            continue
        type1, type2 = parsed
        rows.append(
            {
                "species": species_token(path),
                "type1": type1,
                "type2": type2,
                "effective_contributions": contribution_text(type1, type2),
            }
        )

    out_dir = root / "audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "type_passives.csv"

    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["species", "type1", "type2", "effective_contributions"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {out_path} ({len(rows)} rows).")
    if missing:
        print("WARNING: could not parse types in:")
        for item in missing:
            print(f"  - {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
