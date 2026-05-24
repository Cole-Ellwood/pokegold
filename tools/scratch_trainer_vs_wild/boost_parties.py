"""Apply integer level boosts to specific trainer parties in parties.asm.

For each (class, const) in TARGETS, computes k = ceil(w_avg - t_avg) so the
new party average lands in [w_avg, w_avg+1). Modifies only `db <level>, ...`
lines inside the target party block. Preserves column width for the level
field where possible."""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path
from statistics import mean

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from trainer_vs_wild import (
    parse_trainer_consts,
    parse_parties,
    parse_all_wilds,
    parse_map_trainers,
    WATER_TRAINER_CLASSES,
)

PARTIES_PATH = REPO / "data" / "trainers" / "parties.asm"

# (class, const) tuples to SKIP — the "unfair" Cherrygrove-style cases the
# user identified: trainers reachable before Surf vs surf-only wild pools.
UNFAIR_SKIP = {
    ("RIVAL1", "RIVAL1_1_CHIKORITA"),
    ("RIVAL1", "RIVAL1_1_CYNDAQUIL"),
    ("RIVAL1", "RIVAL1_1_TOTODILE"),
    ("FISHER", "JUSTIN"),
    ("FISHER", "HENRY"),
    ("FISHER", "RALPH1"),
}


def build_targets():
    """Re-runs the analysis and returns [(map, class, const, levels, t_avg, w_avg, k), ...]"""
    c2c, order = parse_trainer_consts()
    parties = parse_parties(c2c, order)
    grass, water = parse_all_wilds()
    map_trainers = parse_map_trainers()

    out = []
    for map_const, trainers in sorted(map_trainers.items()):
        glist = grass.get(map_const, [])
        wlist = water.get(map_const, [])
        combined = glist + wlist
        if not combined:
            continue
        for cls, name in trainers:
            if (cls, name) in UNFAIR_SKIP:
                continue
            levels = parties.get((cls, name))
            if not levels:
                continue
            t_avg = mean(levels)
            is_water = cls in WATER_TRAINER_CLASSES
            if is_water and wlist:
                pool = wlist
            elif not is_water and glist:
                pool = glist
            else:
                pool = combined
            w_avg = mean(pool)
            if t_avg >= w_avg:
                continue
            delta = w_avg - t_avg
            k = math.ceil(delta)
            if k < 1:
                continue
            out.append((map_const, cls, name, list(levels), t_avg, w_avg, k))
    return out


def find_party_line_ranges(text: str, c2c, class_order) -> dict[tuple[str, str], tuple[int, int]]:
    """{(class, const): (start_line, end_line)} — 0-indexed line numbers.
    start_line points at the `db "NAME@", ...` line; end_line is exclusive
    (one past the `db -1 ; end` line)."""
    lines = text.splitlines(keepends=False)
    result = {}
    cur_class = None
    group_idx = 0
    party_idx = 0
    party_start = None
    party_const = None

    for i, raw in enumerate(lines):
        stripped = raw.split(";", 1)[0].rstrip()
        if not stripped.strip():
            continue
        m = re.match(r"^(\w+)Group:", stripped)
        if m:
            # flush any in-progress party (shouldn't happen at group boundaries
            # since each party ends with `db -1`, but be defensive)
            party_start = None
            party_const = None
            cur_class = class_order[group_idx] if group_idx < len(class_order) else None
            group_idx += 1
            party_idx = 0
            continue
        if re.search(r'db\s+"[^"]+@",\s*TRAINERTYPE_', stripped):
            consts = c2c.get(cur_class, [])
            party_const = consts[party_idx] if party_idx < len(consts) else None
            party_start = i
            party_idx += 1
            continue
        if re.match(r"\s*db\s+-1\b", stripped) and party_start is not None and party_const is not None:
            result[(cur_class, party_const)] = (party_start, i)
            party_start = None
            party_const = None
    return result


def boost_level(line: str, k: int) -> tuple[str, int, int] | None:
    """Returns (new_line, old_level, new_level) or None if line isn't `db <num>, ...`."""
    m = re.match(r"^(.*?\bdb)(\s+)(\d+)(\s*,\s*\w+.*)$", line)
    if not m:
        return None
    prefix, spacing, num_str, rest = m.groups()
    old = int(num_str)
    new = old + k
    old_width = len(spacing) + len(num_str)
    new_str = str(new)
    new_spacing = " " * max(1, old_width - len(new_str))
    return prefix + new_spacing + new_str + rest, old, new


def main():
    targets = build_targets()
    print(f"Will boost {len(targets)} parties.\n")

    c2c, order = parse_trainer_consts()
    text = PARTIES_PATH.read_text()
    ranges = find_party_line_ranges(text, c2c, order)

    lines = text.splitlines(keepends=True)
    edits = 0

    for map_const, cls, name, levels, t_avg, w_avg, k in targets:
        rng = ranges.get((cls, name))
        if rng is None:
            print(f"  SKIP (no party range found): {cls} {name}")
            continue
        start, end = rng
        new_levels = []
        # the `db "NAME@", ...` line is at start; pokemon entries are start+1 .. end-1
        for j in range(start + 1, end):
            res = boost_level(lines[j].rstrip("\r\n"), k)
            if res is None:
                continue
            new_line, old_lvl, new_lvl = res
            new_levels.append(new_lvl)
            # preserve original line ending
            if lines[j].endswith("\r\n"):
                lines[j] = new_line + "\r\n"
            elif lines[j].endswith("\n"):
                lines[j] = new_line + "\n"
            else:
                lines[j] = new_line
            edits += 1
        new_avg = mean(new_levels) if new_levels else 0
        new_delta = new_avg - w_avg
        print(f"  {map_const:<28} {cls:<14} {name:<26} +{k}  {levels} -> {new_levels}  "
              f"avg {t_avg:.2f}->{new_avg:.2f} (wild {w_avg:.2f}, d={new_delta:+.2f})")

    if "--apply" in sys.argv:
        PARTIES_PATH.write_text("".join(lines))
        print(f"\nApplied {edits} line edits to {PARTIES_PATH.relative_to(REPO)}.")
    else:
        print(f"\nDry run — {edits} line edits computed. Re-run with --apply to write.")


if __name__ == "__main__":
    main()
