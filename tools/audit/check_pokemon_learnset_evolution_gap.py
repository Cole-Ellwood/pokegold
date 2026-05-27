#!/usr/bin/env python3
"""Audit Pokemon level-up learnsets for evolution-related bugs.

Three checks:

* Check 1 -- pre-evo overflow. A pre-evo species has a level-up entry at
  level >= its own evolution level. The mon evolves before it can ever
  learn that move (unless the player cancels evolution).

* Check 2 -- cross-evolution move duplication. A move appears in both a
  pre-evo's and a post-evo's level-up tables. Common and usually
  intentional (post-evo's L1 entries mirror the pre-evo so FillMoves
  generates a coherent moveset for trainer/wild post-evos), but
  copy-paste errors hide here. Flag every occurrence for human review.

* Check 3 -- post-evo sub-existence entries. A post-evo has a level-up
  entry at a level below its natural floor (the level at which its
  earliest pre-evo evolves into it). Reachable only via FillMoves on
  trainer/wild-generated mons, never via natural level-up on a player's
  mon.

Reads:
    data/pokemon/evos_attacks.asm
    data/pokemon/evos_attacks_pointers.asm
    constants/pokemon_constants.asm

Connects to engine/battle/ai/boss_policy_move.asm:4934
BossAI_AddSpeciesAndPreEvolutionMovesToMask, which walks pre-evo
level-up tables for the plausible-move mask. Fixing Check 1 and
Check 3 findings would refine the boss-AI accuracy slightly.

Exit status is 0 regardless of findings -- this script reports for
human review, not a hard gate.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVOS_ATTACKS = ROOT / "data" / "pokemon" / "evos_attacks.asm"
POINTERS = ROOT / "data" / "pokemon" / "evos_attacks_pointers.asm"
SPECIES_CONSTANTS = ROOT / "constants" / "pokemon_constants.asm"


LABEL_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_]*)EvosAttacks:\s*$")
POINTER_RE = re.compile(r"^\s*dw\s+([A-Za-z][A-Za-z0-9_]*)EvosAttacks\b")
SPECIES_CONST_RE = re.compile(r"^\s+const\s+([A-Z][A-Z0-9_]*)\s*(?:;.*)?$")
EVO_LEVEL_RE = re.compile(
    r"^\s*db\s+EVOLVE_LEVEL\s*,\s*(\d+)\s*,\s*([A-Z][A-Z0-9_]*)\b"
)
EVO_STAT_RE = re.compile(
    r"^\s*db\s+EVOLVE_STAT\s*,\s*(\d+)\s*,\s*[A-Z_]+\s*,\s*([A-Z][A-Z0-9_]*)\b"
)
EVO_ITEM_RE = re.compile(
    r"^\s*db\s+EVOLVE_ITEM\s*,\s*[A-Z_0-9-]+\s*,\s*([A-Z][A-Z0-9_]*)\b"
)
EVO_TRADE_RE = re.compile(
    r"^\s*db\s+EVOLVE_TRADE\s*,\s*\S+\s*,\s*([A-Z][A-Z0-9_]*)\b"
)
EVO_HAPPINESS_RE = re.compile(
    r"^\s*db\s+EVOLVE_HAPPINESS\s*,\s*[A-Z_]+\s*,\s*([A-Z][A-Z0-9_]*)\b"
)
LEVEL_MOVE_RE = re.compile(
    r"^\s*db\s+(\d+)\s*,\s*([A-Z][A-Z0-9_]*)\s*(?:;.*)?$"
)
TERMINATOR_RE = re.compile(r"^\s*db\s+0\b")


@dataclass
class Evolution:
    type: str                       # LEVEL, ITEM, TRADE, HAPPINESS, STAT
    level: int | None               # evo level if known, else None
    target: str                     # species key, e.g. "IVYSAUR"


@dataclass
class Species:
    key: str                        # uppercase constant, e.g. "BULBASAUR"
    dex_num: int                    # 1-based dex index
    label: str                      # asm label prefix, e.g. "Bulbasaur"
    evolutions: list[Evolution] = field(default_factory=list)
    levelups: list[tuple[int, str]] = field(default_factory=list)

    @property
    def level_evo_threshold(self) -> int | None:
        """Lowest level at which this species evolves, across all level-
        based evolution rows. None if no level-based evolution."""
        levels = [e.level for e in self.evolutions if e.level is not None]
        return min(levels) if levels else None


def parse_species_order() -> list[str]:
    """Return species keys in dex order (positions 0..250 -> dex 1..251).

    Walks constants/pokemon_constants.asm starting at the first
    ``const_def 1`` block, accumulating species constants until the next
    ``const_def`` line (which restarts the counter for Unown forms).
    Intermediate ``DEF JOHTO_POKEMON ...`` markers split Kanto/Johto but
    do not end the species block."""
    keys: list[str] = []
    in_block = False
    with open(SPECIES_CONSTANTS, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not in_block:
                if stripped.startswith("const_def 1"):
                    in_block = True
                continue
            if stripped.startswith("const_def"):
                # End of the species block (next is Unown forms).
                break
            if stripped.startswith("const_skip"):
                # const_skip after CELEBI (slot $fc, unused).
                continue
            m = SPECIES_CONST_RE.match(line.rstrip("\n"))
            if m and m.group(1) != "EGG":
                keys.append(m.group(1))
    return keys


def parse_pointer_labels() -> list[str]:
    """Return EvosAttacks label prefixes in dex order."""
    labels: list[str] = []
    with open(POINTERS, encoding="utf-8") as f:
        for line in f:
            m = POINTER_RE.match(line)
            if m:
                labels.append(m.group(1))
    return labels


def parse_evos_attacks(label_to_species: dict[str, Species]) -> None:
    """Populate evolutions and levelups for each Species, in place."""
    current: Species | None = None
    state = "outside"  # outside | evolutions | levelups
    with open(EVOS_ATTACKS, encoding="utf-8") as f:
        for line in f:
            label_match = LABEL_RE.match(line)
            if label_match:
                prefix = label_match.group(1)
                current = label_to_species.get(prefix)
                state = "evolutions" if current else "outside"
                continue
            if current is None:
                continue
            if TERMINATOR_RE.match(line):
                if state == "evolutions":
                    state = "levelups"
                elif state == "levelups":
                    state = "outside"
                    current = None
                continue
            if state == "evolutions":
                m = EVO_LEVEL_RE.match(line)
                if m:
                    current.evolutions.append(
                        Evolution("LEVEL", int(m.group(1)), m.group(2))
                    )
                    continue
                m = EVO_STAT_RE.match(line)
                if m:
                    current.evolutions.append(
                        Evolution("STAT", int(m.group(1)), m.group(2))
                    )
                    continue
                m = EVO_ITEM_RE.match(line)
                if m:
                    current.evolutions.append(
                        Evolution("ITEM", None, m.group(1))
                    )
                    continue
                m = EVO_TRADE_RE.match(line)
                if m:
                    current.evolutions.append(
                        Evolution("TRADE", None, m.group(1))
                    )
                    continue
                m = EVO_HAPPINESS_RE.match(line)
                if m:
                    current.evolutions.append(
                        Evolution("HAPPINESS", None, m.group(1))
                    )
                    continue
            elif state == "levelups":
                m = LEVEL_MOVE_RE.match(line)
                if m:
                    current.levelups.append((int(m.group(1)), m.group(2)))
                    continue


def compute_natural_floor(
    species: Species, by_key: dict[str, Species]
) -> int | None:
    """Lowest level the species can naturally be encountered at via
    evolution. None if it has no level-based pre-evo path (the species
    is a chain starter, or only reachable via item/trade/happiness, in
    which case Check 3 doesn't apply)."""
    levels: list[int] = []
    for parent in by_key.values():
        for evo in parent.evolutions:
            if evo.target != species.key:
                continue
            if evo.type in ("LEVEL", "STAT") and evo.level is not None:
                levels.append(evo.level)
    return min(levels) if levels else None


def transitive_post_evos(
    species: Species, by_key: dict[str, Species]
) -> list[Species]:
    """Return all species reachable from ``species`` via evolution,
    in BFS order. Direct post-evos first, then grandkids, etc."""
    out: list[Species] = []
    seen: set[str] = set()
    queue: list[Species] = [species]
    while queue:
        cur = queue.pop(0)
        for evo in cur.evolutions:
            child = by_key.get(evo.target)
            if child is None or child.key in seen:
                continue
            seen.add(child.key)
            out.append(child)
            queue.append(child)
    return out


def parents_of(
    species: Species, by_key: dict[str, Species]
) -> list[tuple[Species, Evolution]]:
    """Direct pre-evos of this species and the Evolution row that
    points into it."""
    out: list[tuple[Species, Evolution]] = []
    for parent in by_key.values():
        for evo in parent.evolutions:
            if evo.target == species.key:
                out.append((parent, evo))
    return out


@dataclass
class Check1Finding:
    species: Species
    level: int
    move: str
    evo_threshold: int

    @property
    def gap(self) -> int:
        return self.level - self.evo_threshold


@dataclass
class Check2Finding:
    pre: Species
    post: Species
    pre_level: int
    post_level: int
    move: str

    @property
    def kind(self) -> str:
        if self.post_level == 1:
            return "inherited-L1"
        if self.post_level == self.pre_level:
            return "same-level"
        return "different-level"


@dataclass
class Check3Finding:
    species: Species
    level: int
    move: str
    natural_floor: int

    @property
    def gap(self) -> int:
        return self.natural_floor - self.level


def run_checks(by_key: dict[str, Species]):
    check1: list[Check1Finding] = []
    check2: list[Check2Finding] = []
    check3: list[Check3Finding] = []

    for sp in by_key.values():
        # Check 1: pre-evo overflow.
        threshold = sp.level_evo_threshold
        if threshold is not None:
            for level, move in sp.levelups:
                if level >= threshold:
                    check1.append(Check1Finding(sp, level, move, threshold))

        # Check 2: cross-evolution duplication (against transitive
        # post-evos so Charmander/Charizard pairs are reported).
        for post in transitive_post_evos(sp, by_key):
            pre_moves = {move for (_lvl, move) in sp.levelups}
            for post_level, post_move in post.levelups:
                if post_move not in pre_moves:
                    continue
                # For each occurrence of the move on the pre-evo's table
                # (a move may appear multiple times on a table, e.g.
                # L1 GROWL and L4 GROWL).
                for pre_level, pre_move in sp.levelups:
                    if pre_move == post_move:
                        check2.append(
                            Check2Finding(sp, post, pre_level, post_level, post_move)
                        )

        # Check 3: post-evo sub-existence.
        floor = compute_natural_floor(sp, by_key)
        if floor is not None:
            for level, move in sp.levelups:
                if level < floor:
                    check3.append(Check3Finding(sp, level, move, floor))

    return check1, check2, check3


def format_evo_chain(sp: Species, by_key: dict[str, Species]) -> str:
    parents = parents_of(sp, by_key)
    parent_strs = []
    for parent, evo in parents:
        if evo.type == "LEVEL":
            parent_strs.append(f"{parent.key} @ L{evo.level}")
        elif evo.type == "STAT":
            parent_strs.append(f"{parent.key} @ L{evo.level} (stat)")
        else:
            parent_strs.append(f"{parent.key} ({evo.type.lower()})")
    evo_strs = []
    for evo in sp.evolutions:
        if evo.type == "LEVEL":
            evo_strs.append(f"{evo.target} @ L{evo.level}")
        elif evo.type == "STAT":
            evo_strs.append(f"{evo.target} @ L{evo.level} (stat)")
        else:
            evo_strs.append(f"{evo.target} ({evo.type.lower()})")
    parts: list[str] = []
    if parent_strs:
        parts.append("from " + ", ".join(parent_strs))
    if evo_strs:
        parts.append("-> " + ", ".join(evo_strs))
    return "  ".join(parts) if parts else "no evolutions"


def emit_report(
    by_key: dict[str, Species],
    species_in_dex_order: list[Species],
    check1: list[Check1Finding],
    check2: list[Check2Finding],
    check3: list[Check3Finding],
) -> None:
    out = sys.stdout.write

    out("Pokemon Learnset Evolution Audit\n")
    out("================================\n")
    out(f"Source: {EVOS_ATTACKS.relative_to(ROOT).as_posix()}\n")
    out(f"Species parsed: {len(species_in_dex_order)}\n")
    out("\n")
    out("Connects to engine/battle/ai/boss_policy_move.asm:4934\n")
    out("BossAI_AddSpeciesAndPreEvolutionMovesToMask walks pre-evo level-up\n")
    out("tables for the plausible-move mask; Check 1 and Check 3 findings\n")
    out("would refine boss-AI accuracy slightly if fixed.\n")
    out("\n")

    c2_diff = sum(1 for f in check2 if f.kind == "different-level")
    c2_same = sum(1 for f in check2 if f.kind == "same-level")
    c2_inh = sum(1 for f in check2 if f.kind == "inherited-L1")

    out("Summary\n")
    out("-------\n")
    out(f"  Check 1 (pre-evo overflow):           {len(check1)} entries\n")
    out(f"  Check 2 (cross-evo duplication):      {len(check2)} entries\n")
    out(f"    different-level (most suspicious):  {c2_diff}\n")
    out(f"    same-level (possibly copy-paste):   {c2_same}\n")
    out(f"    inherited-L1 (standard FillMoves):  {c2_inh}\n")
    out(f"  Check 3 (post-evo sub-existence):     {len(check3)} entries\n")
    out("\n")

    # Top offenders: Check 1 by gap (level past threshold), Check 3 by
    # gap (floor minus learn-level).
    out("Top 15 worst Check 1 offenders (largest overflow gap first)\n")
    out("-----------------------------------------------------------\n")
    top1 = sorted(check1, key=lambda f: (-f.gap, f.species.dex_num, f.level))[:15]
    if top1:
        for f in top1:
            out(
                f"  +{f.gap:>3}  {f.species.key:<11} L{f.level:<3} "
                f"{f.move:<14}  (evolves at L{f.evo_threshold})\n"
            )
    else:
        out("  (none)\n")
    out("\n")

    out("Top 15 worst Check 3 offenders (largest sub-existence gap first)\n")
    out("----------------------------------------------------------------\n")
    top3 = sorted(check3, key=lambda f: (-f.gap, f.species.dex_num, f.level))[:15]
    if top3:
        for f in top3:
            out(
                f"  -{f.gap:>3}  {f.species.key:<11} L{f.level:<3} "
                f"{f.move:<14}  (natural floor L{f.natural_floor})\n"
            )
    else:
        out("  (none)\n")
    out("\n")

    out("Per-species punch list (dex order; species with no findings omitted)\n")
    out("====================================================================\n")
    out("\n")

    # Group findings by species key.
    c1_by_species: dict[str, list[Check1Finding]] = {}
    for f in check1:
        c1_by_species.setdefault(f.species.key, []).append(f)
    c2_by_pre: dict[str, list[Check2Finding]] = {}
    for f in check2:
        c2_by_pre.setdefault(f.pre.key, []).append(f)
    c3_by_species: dict[str, list[Check3Finding]] = {}
    for f in check3:
        c3_by_species.setdefault(f.species.key, []).append(f)

    for sp in species_in_dex_order:
        has_c1 = sp.key in c1_by_species
        has_c2 = sp.key in c2_by_pre
        has_c3 = sp.key in c3_by_species
        if not (has_c1 or has_c2 or has_c3):
            continue

        header = f"{sp.key}  (#{sp.dex_num:03})"
        out(header + "\n")
        out("-" * len(header) + "\n")
        out(f"  chain: {format_evo_chain(sp, by_key)}\n")
        out("\n")

        if has_c1:
            threshold = sp.level_evo_threshold
            out(f"  [Check 1] pre-evo overflow -- entries at level >= L{threshold}\n")
            findings = sorted(
                c1_by_species[sp.key], key=lambda f: (-f.gap, f.level)
            )
            for f in findings:
                out(f"    +{f.gap:>3}  L{f.level:<3} {f.move}\n")
            out("\n")

        if has_c2:
            findings = c2_by_pre[sp.key]
            # Group by post-evo species, then by move.
            by_post: dict[str, list[Check2Finding]] = {}
            for f in findings:
                by_post.setdefault(f.post.key, []).append(f)
            out("  [Check 2] shared moves with post-evos\n")
            # Order post-evos by transitive-evo order (direct first).
            post_order = [p.key for p in transitive_post_evos(sp, by_key)]
            for post_key in post_order:
                if post_key not in by_post:
                    continue
                post_findings = by_post[post_key]
                # Sort findings: different-level > same-level > inherited-L1,
                # then by (pre_level, post_level).
                kind_rank = {"different-level": 0, "same-level": 1, "inherited-L1": 2}
                post_findings.sort(
                    key=lambda f: (
                        kind_rank[f.kind],
                        f.pre_level,
                        f.post_level,
                        f.move,
                    )
                )
                out(f"    vs {post_key}:\n")
                for f in post_findings:
                    out(
                        f"      {f.move:<14}  pre L{f.pre_level:<3} -> "
                        f"post L{f.post_level:<3}  [{f.kind}]\n"
                    )
            out("\n")

        if has_c3:
            floor = compute_natural_floor(sp, by_key)
            out(
                f"  [Check 3] sub-existence -- entries below natural floor L{floor}\n"
            )
            findings = sorted(
                c3_by_species[sp.key], key=lambda f: (-f.gap, f.level)
            )
            for f in findings:
                out(f"    -{f.gap:>3}  L{f.level:<3} {f.move}\n")
            out("\n")


def main(argv: list[str]) -> int:
    species_keys = parse_species_order()
    pointer_labels = parse_pointer_labels()
    if len(species_keys) != len(pointer_labels):
        print(
            f"ERROR: species-constant count ({len(species_keys)}) does not "
            f"match pointer-label count ({len(pointer_labels)})",
            file=sys.stderr,
        )
        return 2

    by_key: dict[str, Species] = {}
    by_label: dict[str, Species] = {}
    species_in_dex_order: list[Species] = []
    for idx, (key, label) in enumerate(zip(species_keys, pointer_labels)):
        sp = Species(key=key, dex_num=idx + 1, label=label)
        by_key[key] = sp
        by_label[label] = sp
        species_in_dex_order.append(sp)

    parse_evos_attacks(by_label)

    check1, check2, check3 = run_checks(by_key)
    emit_report(by_key, species_in_dex_order, check1, check2, check3)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
