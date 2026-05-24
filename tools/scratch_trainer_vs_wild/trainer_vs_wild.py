"""One-shot analysis: trainers whose avg party level < avg wild level on their map.

Joins:
  - parties.asm                         -> (class, const) -> [levels]
  - trainer_constants.asm               -> class -> ordered consts
  - johto/kanto_grass/water.asm         -> map_const -> [wild_levels]
  - maps/*.asm + map_constants.asm      -> map_const -> [(class, const)]
"""

from __future__ import annotations

import re
from pathlib import Path
from statistics import mean

REPO = Path(__file__).resolve().parents[2]


def camel_to_snake_upper(s: str) -> str:
    out = []
    for i, ch in enumerate(s):
        if i > 0 and ch.isupper() and not s[i - 1].isupper():
            out.append("_")
        out.append(ch.upper())
    return "".join(out)


def file_to_map_const(stem: str) -> str:
    """Convert map filename stem (e.g. MountMortar1FOutside) to UPPER_SNAKE
    constant (MOUNT_MORTAR_1F_OUTSIDE). Keeps 'floor codes' like 1F/2F/B1F
    glued — a digit followed by an uppercase letter only splits if that
    uppercase letter is followed by lowercase (i.e. it starts a real word)."""
    s = stem
    # A) lower→upper (Mount + Mortar)
    s = re.sub(r"([a-z])([A-Z])", r"\1_\2", s)
    # B) upper-upper-lower (FOutside → F_Outside; handles acronym-then-word)
    s = re.sub(r"([A-Z])([A-Z][a-z])", r"\1_\2", s)
    # C) lower→digit (Mortar + 1)
    s = re.sub(r"([a-z])(\d)", r"\1_\2", s)
    # D) digit → uppercase-followed-by-lowercase (10 + North); but NOT 1F where F
    #    isn't followed by lowercase — leave floor codes glued.
    s = re.sub(r"(\d)([A-Z][a-z])", r"\1_\2", s)
    return s.upper()


# ---------- parse trainer_constants.asm ----------

def parse_trainer_consts() -> tuple[dict[str, list[str]], list[str]]:
    """Returns (class -> ordered consts, ordered list of classes that have ≥1 const)."""
    path = REPO / "constants" / "trainer_constants.asm"
    text = path.read_text()
    by_class: dict[str, list[str]] = {}
    order: list[str] = []
    cur_class: str | None = None
    for line in text.splitlines():
        line = line.split(";", 1)[0].strip()
        if not line:
            continue
        m = re.match(r"trainerclass\s+(\w+)", line)
        if m:
            cur_class = m.group(1)
            if cur_class != "TRAINER_NONE":
                by_class[cur_class] = []
                order.append(cur_class)
            continue
        m = re.match(r"const\s+(\w+)", line)
        if m and cur_class and cur_class != "TRAINER_NONE":
            by_class[cur_class].append(m.group(1))
    # Keep ALL classes (including 0-const ones like POKEMON_PROF) — they still
    # have an empty `<Foo>Group:` label in parties.asm, and positional alignment
    # would break if we skipped them. Only TRAINER_NONE has no group at all.
    return by_class, order


# ---------- parse parties.asm ----------

def parse_parties(class_to_consts: dict[str, list[str]], class_order: list[str]) -> dict[tuple[str, str], list[int]]:
    path = REPO / "data" / "trainers" / "parties.asm"
    text = path.read_text()
    result: dict[tuple[str, str], list[int]] = {}
    cur_class: str | None = None
    party_idx_within_class = 0  # zero-based
    in_party = False
    cur_const: str | None = None
    cur_levels: list[int] = []
    group_idx = 0  # index into class_order

    for raw in text.splitlines():
        line = raw.split(";", 1)[0].rstrip()
        if not line.strip():
            continue
        m = re.match(r"^(\w+)Group:", line)
        if m:
            # flush prior party
            if in_party and cur_const is not None:
                result[(cur_class, cur_const)] = cur_levels
            if group_idx < len(class_order):
                cur_class = class_order[group_idx]
            else:
                cur_class = None
            group_idx += 1
            party_idx_within_class = 0
            in_party = False
            cur_const = None
            cur_levels = []
            continue
        # start of new party
        if re.search(r'db\s+"[^"]+@",\s*TRAINERTYPE_', line):
            if in_party and cur_const is not None:
                result[(cur_class, cur_const)] = cur_levels
            consts = class_to_consts.get(cur_class, [])
            if party_idx_within_class < len(consts):
                cur_const = consts[party_idx_within_class]
            else:
                cur_const = None
            party_idx_within_class += 1
            in_party = True
            cur_levels = []
            continue
        if in_party:
            # end of party
            if re.match(r"\s*db\s+-1\b", line):
                if cur_const is not None:
                    result[(cur_class, cur_const)] = cur_levels
                in_party = False
                cur_const = None
                cur_levels = []
                continue
            # a pokemon: db <level>, <species>, ...
            m = re.match(r"\s*db\s+(\d+)\s*,\s*\w+", line)
            if m:
                cur_levels.append(int(m.group(1)))
    if in_party and cur_const is not None:
        result[(cur_class, cur_const)] = cur_levels
    return result


# ---------- parse wild encounter files ----------

def parse_wild(file_path: Path, kind: str) -> dict[str, list[int]]:
    """kind: 'grass' or 'water'. Returns {MAP_CONST: [levels]}.
    Honors `IF DEF(_GOLD)` / `ELIF DEF(_SILVER)` / `ENDC` and only collects
    levels in branches active for the Gold build (the primary ROM here)."""
    text = file_path.read_text()
    result: dict[str, list[int]] = {}
    cur_map: str | None = None
    skip_lines = 0
    # IF stack: True = inside an active branch we want to collect from
    if_active: list[bool] = []
    if_was_active: list[bool] = []  # was any prior branch in this IF taken?

    skip_per_block = 1  # both grass and water have one rate line

    for raw in text.splitlines():
        line = raw.split(";", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()

        # conditional handling
        m_if = re.match(r"IF\s+DEF\((\w+)\)", stripped)
        m_elif = re.match(r"ELIF\s+DEF\((\w+)\)", stripped)
        m_else = re.match(r"ELSE\b", stripped)
        m_endc = re.match(r"ENDC\b", stripped)
        if m_if:
            active = m_if.group(1) == "_GOLD"
            if_active.append(active)
            if_was_active.append(active)
            continue
        if m_elif:
            if not if_active:
                continue
            if if_was_active[-1]:
                if_active[-1] = False
            else:
                active = m_elif.group(1) == "_GOLD"
                if_active[-1] = active
                if active:
                    if_was_active[-1] = True
            continue
        if m_else:
            if not if_active:
                continue
            if_active[-1] = not if_was_active[-1]
            continue
        if m_endc:
            if if_active:
                if_active.pop()
                if_was_active.pop()
            continue

        # outside of any IF block, treat as active
        in_active_branch = all(if_active) if if_active else True

        m = re.match(rf"\s*def_{kind}_wildmons\s+(\w+)", line)
        if m:
            cur_map = m.group(1)
            result.setdefault(cur_map, [])
            skip_lines = skip_per_block
            continue
        if re.match(rf"\s*end_{kind}_wildmons", line):
            cur_map = None
            continue
        if cur_map is None:
            continue
        if skip_lines > 0:
            skip_lines -= 1
            continue
        if not in_active_branch:
            continue
        m = re.match(r"\s*db\s+(\d+)\s*,\s*\w+", line)
        if m:
            result[cur_map].append(int(m.group(1)))
    return result


def parse_all_wilds() -> tuple[dict[str, list[int]], dict[str, list[int]]]:
    """Returns (grass_by_map, water_by_map)."""
    grass: dict[str, list[int]] = {}
    water: dict[str, list[int]] = {}
    for fname, target in [
        ("johto_grass.asm", grass),
        ("kanto_grass.asm", grass),
    ]:
        path = REPO / "data" / "wild" / fname
        if path.exists():
            for k, v in parse_wild(path, "grass").items():
                target.setdefault(k, []).extend(v)
    for fname, target in [
        ("johto_water.asm", water),
        ("kanto_water.asm", water),
    ]:
        path = REPO / "data" / "wild" / fname
        if path.exists():
            for k, v in parse_wild(path, "water").items():
                target.setdefault(k, []).extend(v)
    return grass, water


# ---------- parse map files for trainer placements ----------

def parse_map_trainers() -> dict[str, list[tuple[str, str]]]:
    """{MAP_CONST: [(CLASS, NAME), ...]}"""
    map_dir = REPO / "maps"
    map_constants = set()
    mc_text = (REPO / "constants" / "map_constants.asm").read_text()
    for line in mc_text.splitlines():
        m = re.match(r"\s*map_const\s+(\w+)\s*,", line)
        if m:
            map_constants.add(m.group(1))

    result: dict[str, list[tuple[str, str]]] = {}
    for path in map_dir.glob("*.asm"):
        const = file_to_map_const(path.stem)
        if const not in map_constants:
            # try fallback: maybe an odd case; warn silently
            continue
        text = path.read_text()
        trainers = []
        for raw in text.splitlines():
            line = raw.split(";", 1)[0]
            m = re.match(r"\s*trainer\s+(\w+)\s*,\s*(\w+)\s*,", line)
            if m:
                trainers.append((m.group(1), m.group(2)))
                continue
            # boss-style invocation (gym leaders, rivals, Sage Li)
            m = re.match(r"\s*loadtrainer\s+(\w+)\s*,\s*(\w+)", line)
            if m:
                trainers.append((m.group(1), m.group(2)))
        # de-dup (a loadtrainer block can appear in multiple branches)
        seen = set()
        uniq = []
        for t in trainers:
            if t not in seen:
                seen.add(t)
                uniq.append(t)
        if uniq:
            result[const] = uniq
    return result


# ---------- join ----------

WATER_TRAINER_CLASSES = {"SWIMMERM", "SWIMMERF", "SAILOR", "FISHER"}


def report(rows, label):
    print(f"\n=== {label}: {len(rows)} trainers ===")
    print(f"{'MAP':<28} {'CLASS':<14} {'NAME':<14} {'PARTY':<22} {'T_AVG':>6} {'W_AVG':>6} {'W_RANGE':>9} {'DELTA':>6}")
    print("-" * 110)
    for r in rows:
        plevels = ",".join(str(x) for x in r["party_levels"])
        wrange = f"{r['wild_min']}-{r['wild_max']}"
        print(f"{r['map']:<28} {r['class']:<14} {r['name']:<14} {plevels:<22} {r['t_avg']:>6.2f} {r['wild_avg']:>6.2f} {wrange:>9} {r['delta']:>6.2f}")


def main():
    class_to_consts, class_order = parse_trainer_consts()
    parties = parse_parties(class_to_consts, class_order)
    grass_wilds, water_wilds = parse_all_wilds()
    map_trainers = parse_map_trainers()

    grass_rows = []   # land trainer vs grass wilds
    water_rows = []   # water trainer vs water wilds
    combined_rows = []  # any trainer vs grass+water (broader test)
    skipped_no_pool = set()

    for map_const, trainer_list in sorted(map_trainers.items()):
        glist = grass_wilds.get(map_const, [])
        wlist = water_wilds.get(map_const, [])
        combined = glist + wlist
        if not combined:
            skipped_no_pool.add(map_const)
            continue

        for cls, name in trainer_list:
            levels = parties.get((cls, name))
            if not levels:
                continue
            t_avg = mean(levels)
            is_water_class = cls in WATER_TRAINER_CLASSES

            # pick the natural comparison pool: water class → water; else grass
            if is_water_class and wlist:
                pool, pool_label = wlist, "water"
            elif not is_water_class and glist:
                pool, pool_label = glist, "grass"
            else:
                pool, pool_label = combined, "combined"
            w_avg = mean(pool)
            row = {
                "map": map_const,
                "class": cls,
                "name": name,
                "party_levels": levels,
                "t_avg": t_avg,
                "wild_avg": w_avg,
                "wild_min": min(pool),
                "wild_max": max(pool),
                "delta": w_avg - t_avg,
                "pool": pool_label,
            }
            if t_avg < w_avg:
                if pool_label == "grass":
                    grass_rows.append(row)
                elif pool_label == "water":
                    water_rows.append(row)
                else:
                    combined_rows.append(row)

    for rs in (grass_rows, water_rows, combined_rows):
        rs.sort(key=lambda r: (-r["delta"], r["map"], r["class"], r["name"]))

    print(f"Trainers vs wilds on their map (Gold ROM, IF DEF(_GOLD) branches only).")
    print(f"Land trainer classes compared against grass; water classes "
          f"({sorted(WATER_TRAINER_CLASSES)}) against water; rest fall back to combined.\n")

    report(grass_rows, "LAND TRAINER vs GRASS WILDS")
    report(water_rows, "WATER TRAINER vs WATER WILDS")
    if combined_rows:
        report(combined_rows, "MIXED FALLBACK (map lacks the natural pool)")

    if skipped_no_pool:
        print(f"\n[diag] {len(skipped_no_pool)} maps with trainers but no wild encounters "
              f"(gyms/buildings): {sorted(skipped_no_pool)[:6]}...")


if __name__ == "__main__":
    main()
