#!/usr/bin/env python3
"""Generate data/boss_ai/matchup_tables.asm — per-leader type matchup tables.

Owned by Claude (P2a lane). Consumed in asm by Codex's KO-band oracle
(engine/battle/ai/ko_band_oracle.asm) in P2b. The generated table feeds
BossAI_CurrentEnemyMoveHasKOPressure and BossAI_CurrentEnemyMovePressureScore
with compile-time type matchups so they avoid runtime type-chart loops.

## ABI Contract (P2b consumer-facing)

The output is a single label `BossAIMatchupTables::` followed by per-leader
rows in the order: Johto post-Whitney + Silver (RIVAL1/RIVAL2) + Rocket
executives + Elite Four + Champion + special (Blue, Red). Each leader row:

    db <TRAINER_CLASS>, <TRAINER_ID>   ; 2 bytes — primary key
    db <PARTY_COUNT>                   ; 1 byte — N slots (1..6)
    ; for each of N slots in party-data order:
    db <species>                       ; 1 byte — for debugger reference
    ; defensive matchup vector vs 17 types (atk_type -> multiplier byte):
    db <17 bytes: NORMAL_def, FIGHTING_def, ..., DARK_def>
    ; offensive coverage vector (def_type -> max multiplier this mon can hit):
    db <17 bytes: NORMAL_off, FIGHTING_off, ..., DARK_off>
    ; (one slot = 1 + 17 + 17 = 35 bytes; up to 6 slots = 210 bytes/leader)

After all leaders:

    db 0   ; trainer class 0 = end-of-table sentinel

## Multiplier byte encoding (raw, matches asm matchup loop)

    0  = NO_EFFECT             (×0)
    5  = NOT_VERY_EFFECTIVE    (×0.5)
    10 = NORMAL_EFFECTIVE      (×1)   — implicit default for any (atk, def) not in TypeMatchups
    20 = SUPER_EFFECTIVE       (×2)

Same encoding as `tools/damage_debugger/oracle.py:56-60` and the runtime
BattleCommand_Stab matchup loop (oracle reads `data/types/type_matchups.asm`
where missing rows default to NORMAL_EFFECTIVE).

## Canonical 17-type order (BIRD excluded)

    NORMAL, FIGHTING, FLYING, POISON, GROUND, ROCK, BUG, GHOST, STEEL,
    FIRE, WATER, GRASS, ELECTRIC, PSYCHIC_TYPE, ICE, DRAGON, DARK

The asm side must use the same order so byte N of either vector maps to
the same type. The order is documented in the generated table's header
comment AND enforced by tools/audit/check_ko_band_oracle_self_test.py.

## Sole-source-of-truth promise

The script parses:
  - data/trainers/parties.asm        (leader rosters + 4 moves per slot)
  - data/pokemon/base_stats/*.asm    (each species' type1, type2)
  - data/moves/moves.asm             (each move's type)
  - data/types/type_matchups.asm     (the matchup multipliers)

No type/matchup constants are hardcoded outside this docstring's
canonical type order list. If parties.asm changes a roster slot, this
generator picks it up on the next run.

## Regeneration

    python scripts/generate_boss_matchup_tables.py

Exits 0 on success and writes data/boss_ai/matchup_tables.asm. Exits 1
on parse error with a diagnostic to stderr.

## Audit pairing

tools/audit/check_ko_band_oracle_self_test.py runs the generator in
dry-run mode and diffs against the committed table — catches drift if
parties/types/moves/matchups change without a regeneration. Promote to
release-smoke once Codex's P2b lands and the table format is settled.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "data" / "boss_ai" / "matchup_tables.asm"


CANONICAL_TYPE_ORDER = (
    "NORMAL", "FIGHTING", "FLYING", "POISON", "GROUND", "ROCK", "BUG", "GHOST", "STEEL",
    "FIRE", "WATER", "GRASS", "ELECTRIC", "PSYCHIC_TYPE", "ICE", "DRAGON", "DARK",
)
NUM_CANONICAL_TYPES = len(CANONICAL_TYPE_ORDER)
assert NUM_CANONICAL_TYPES == 17, "Canonical type order must have 17 entries (BIRD excluded)"


# Eligible (trainer_class, party_group_label_prefix) for the 16-class Haki-eligible
# roster. Each leader's party_group_label is `<Group>:` in data/trainers/parties.asm.
# We process all rows under each group, since multi-stage leaders (RIVAL1, RIVAL2)
# have several party variants and the ko-band oracle needs each one.
ELIGIBLE_GROUPS = (
    ("MORTY", "MortyGroup"),
    ("CHUCK", "ChuckGroup"),
    ("JASMINE", "JasmineGroup"),
    ("PRYCE", "PryceGroup"),
    ("CLAIR", "ClairGroup"),
    ("RIVAL1", "Rival1Group"),
    ("RIVAL2", "Rival2Group"),
    ("EXECUTIVEM", "ExecutiveMGroup"),
    ("EXECUTIVEF", "ExecutiveFGroup"),
    ("WILL", "WillGroup"),
    ("BRUNO", "BrunoGroup"),
    ("KOGA", "KogaGroup"),
    ("KAREN", "KarenGroup"),
    ("CHAMPION", "ChampionGroup"),
    ("BLUE", "BlueGroup"),
    ("RED", "RedGroup"),
)


# trainertypes.asm constants — minimum information about each format.
# Each party row's leading bytes determine the per-slot byte layout.
TRAINERTYPE_NORMAL = 0
TRAINERTYPE_ITEM_MOVES = 3


# Multiplier encoding bytes (same shape as BattleCommand_Stab matchup loop).
M_NO_EFFECT = 0
M_NOT_VERY = 5
M_NORMAL = 10
M_SUPER = 20


MULT_FROM_NAME = {
    "NO_EFFECT": M_NO_EFFECT,
    "NOT_VERY_EFFECTIVE": M_NOT_VERY,
    "SUPER_EFFECTIVE": M_SUPER,
    # NORMAL is implicit (missing row).
}


@dataclass(frozen=True)
class PartySlot:
    species: str
    level: int
    moves: tuple[str, ...]  # 0..4 entries; varies per trainer-type


@dataclass(frozen=True)
class LeaderRoster:
    trainer_class: str
    trainer_id: str       # e.g. "MORTY1", "RIVAL1_3_CYNDAQUIL"
    slots: tuple[PartySlot, ...]


# ---------- parsers ----------

def _strip_comment(line: str) -> str:
    # Remove any ; comment but keep RGBDS strings — parties.asm uses bare
    # tokens after `db`, so a simple split works for the rows we care about.
    if ";" in line:
        line = line[: line.index(";")]
    return line.strip()


def parse_type_matchups(path: Path) -> dict[tuple[str, str], int]:
    """Returns {(attacker, defender): multiplier_byte}. Missing pairs = NORMAL."""
    out: dict[tuple[str, str], int] = {}
    in_table = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = _strip_comment(raw)
        if not line:
            continue
        if line.endswith(":"):
            in_table = line.startswith("TypeMatchups")
            continue
        if not in_table:
            continue
        # Format: `db <ATTACKER>, <DEFENDER>, <EFFECTIVENESS>`
        m = re.match(r"^db\s+(\w+)\s*,\s*(\w+)\s*,\s*(\w+)$", line)
        if not m:
            # End sentinel `db $ff` or `endc` etc.
            if line.startswith("db") and "$ff" in line:
                break
            continue
        att, deff, eff = m.group(1), m.group(2), m.group(3)
        if eff not in MULT_FROM_NAME:
            print(f"WARN: unrecognized effectiveness '{eff}' in type_matchups.asm; skipping", file=sys.stderr)
            continue
        out[(att, deff)] = MULT_FROM_NAME[eff]
    return out


def matchup(matchups: dict[tuple[str, str], int], att: str, deff: str) -> int:
    """Lookup with NORMAL_EFFECTIVE default."""
    return matchups.get((att, deff), M_NORMAL)


def parse_base_stats_types() -> dict[str, tuple[str, str]]:
    """Returns {SPECIES: (type_a, type_b)}."""
    out: dict[str, tuple[str, str]] = {}
    for path in (ROOT / "data" / "pokemon" / "base_stats").glob("*.asm"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        species_m = re.search(r"^\s*db\s+(\w+)\s*;\s*\d+\s*$", text, flags=re.MULTILINE)
        type_m = re.search(r"^\s*db\s+(\w+)\s*,\s*(\w+)\s*;\s*type", text, flags=re.MULTILINE)
        if not species_m or not type_m:
            continue
        out[species_m.group(1)] = (type_m.group(1), type_m.group(2))
    return out


def parse_move_types() -> dict[str, str]:
    """Returns {MOVE_NAME: type_name}."""
    out: dict[str, str] = {}
    path = ROOT / "data" / "moves" / "moves.asm"
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = _strip_comment(raw)
        # Format: `move NAME, EFFECT, BP, TYPE, ACC, PP, EFFECT_CHANCE`
        m = re.match(r"^move\s+(\w+)\s*,\s*\w+\s*,\s*-?\d+\s*,\s*(\w+)\s*,", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


# ---------- parties.asm parsing ----------

# Map known trainer-type names to per-slot byte layouts so we can pluck
# the move tokens deterministically.
TRAINER_TYPE_LAYOUT = {
    "TRAINERTYPE_NORMAL": ("level", "species"),
    "TRAINERTYPE_MOVES": ("level", "species", "m1", "m2", "m3", "m4"),
    "TRAINERTYPE_ITEM": ("level", "species", "item"),
    "TRAINERTYPE_ITEM_MOVES": ("level", "species", "item", "m1", "m2", "m3", "m4"),
}


RIVAL_STARTERS = ("CHIKORITA", "CYNDAQUIL", "TOTODILE")


def _synthesize_trainer_id(group_class: str, occurrence: int) -> str:
    """Canonical trainer-ID synthesis per constants/trainer_constants.asm.

    Codex's P2a slice_revisions_requested (2026-05-23) caught the previous
    naive `f"{group_class}{occurrence}"` synthesis emitting IDs that don't
    match the actual constants (e.g. EXECUTIVEM4 vs EXECUTIVEM_4, or
    RIVAL1_2_CYNDAQUIL for the first Cyndaquil variant when it should be
    RIVAL1_1_CYNDAQUIL). This function encodes the per-class rules:

      - CHAMPION → "LANCE" (singleton, no number).
      - EXECUTIVEM / EXECUTIVEF → underscored: EXECUTIVEM_1..EXECUTIVEM_4,
        EXECUTIVEF_1..EXECUTIVEF_2.
      - RIVAL1 / RIVAL2 → stage-major <CLASS>_<stage>_<STARTER>:
          stage   = (occurrence - 1) // 3 + 1   (1..5 for RIVAL1, 1..2 for RIVAL2)
          starter = (occurrence - 1) % 3        (0=CHIKORITA, 1=CYNDAQUIL, 2=TOTODILE)
        Mirrors the const order in constants/trainer_constants.asm:
          RIVAL1_1_CHIKORITA, RIVAL1_1_CYNDAQUIL, RIVAL1_1_TOTODILE,
          RIVAL1_2_CHIKORITA, ... RIVAL1_5_TOTODILE,
          RIVAL2_1_CHIKORITA, ... RIVAL2_2_TOTODILE.
      - All other classes (MORTY, CHUCK, JASMINE, PRYCE, CLAIR, WILL,
        BRUNO, KOGA, KAREN, BLUE, RED) → bare number suffix MORTY1, etc.
    """
    if group_class == "CHAMPION":
        return "LANCE"
    if group_class in ("EXECUTIVEM", "EXECUTIVEF"):
        return f"{group_class}_{occurrence}"
    if group_class in ("RIVAL1", "RIVAL2"):
        stage = (occurrence - 1) // 3 + 1
        starter = RIVAL_STARTERS[(occurrence - 1) % 3]
        return f"{group_class}_{stage}_{starter}"
    return f"{group_class}{occurrence}"


def parse_eligible_rosters() -> list[LeaderRoster]:
    """Walk parties.asm, returning a LeaderRoster per Haki-eligible entry."""
    text = (ROOT / "data" / "trainers" / "parties.asm").read_text(encoding="utf-8")
    lines = text.splitlines()
    rosters: list[LeaderRoster] = []

    group_starts: dict[str, int] = {}
    for i, raw in enumerate(lines):
        m = re.match(r"^(\w+Group):\s*$", raw)
        if m:
            group_starts[m.group(1)] = i

    eligible_label_to_class = {label: cls for cls, label in ELIGIBLE_GROUPS}

    # Process each group sequentially, ending at the next group label.
    sorted_groups = sorted(group_starts.items(), key=lambda kv: kv[1])
    for idx, (label, start) in enumerate(sorted_groups):
        if label not in eligible_label_to_class:
            continue
        end = sorted_groups[idx + 1][1] if idx + 1 < len(sorted_groups) else len(lines)
        cls = eligible_label_to_class[label]
        rosters.extend(_parse_group_entries(cls, lines[start + 1:end]))
    return rosters


def _parse_group_entries(group_class: str, group_lines: list[str]) -> Iterator[LeaderRoster]:
    """Each `db "NAME@", TRAINERTYPE_*` opens a new entry; `db -1` closes."""
    occurrence = 0
    current_entry_lines: list[str] = []
    current_header: str | None = None
    pending_comment: str | None = None
    for raw in group_lines:
        line = raw.rstrip()
        stripped = _strip_comment(line)
        # Capture comments preceding the next entry's header.
        if line.lstrip().startswith(";"):
            pending_comment = line.lstrip().lstrip(";").strip()
            continue
        if not stripped:
            continue
        if stripped.startswith("db ") and re.search(r'"[^"]+@"', stripped) and "TRAINERTYPE_" in stripped:
            if current_header is not None and current_entry_lines:
                occurrence += 1
                yield from _emit_entry(group_class, current_header, current_entry_lines, pending_comment, occurrence)
                pending_comment = None
            current_header = stripped
            current_entry_lines = []
            continue
        if stripped == "db -1":
            if current_header is not None:
                occurrence += 1
                yield from _emit_entry(group_class, current_header, current_entry_lines, pending_comment, occurrence)
                pending_comment = None
                current_header = None
                current_entry_lines = []
            continue
        if current_header is not None:
            current_entry_lines.append(stripped)
    # tail (in case last entry doesn't terminate with `db -1` before group end)
    if current_header is not None and current_entry_lines:
        occurrence += 1
        yield from _emit_entry(group_class, current_header, current_entry_lines, pending_comment, occurrence)


def _emit_entry(
    group_class: str,
    header: str,
    body: list[str],
    comment: str | None,
    occurrence: int,
) -> Iterator[LeaderRoster]:
    """Parse a single trainer entry into a LeaderRoster.

    Header format: `db "<NAME>@", <TRAINERTYPE_*>`
    Body rows: `db <level>, <species>[, <item>][, <m1>, <m2>, <m3>, <m4>]`
    """
    tt_m = re.search(r"TRAINERTYPE_\w+", header)
    if not tt_m:
        return
    tt = tt_m.group(0)
    layout = TRAINER_TYPE_LAYOUT.get(tt)
    if layout is None:
        return
    slots: list[PartySlot] = []
    for row in body:
        if not row.startswith("db "):
            continue
        tokens = [t.strip() for t in row[3:].split(",")]
        if len(tokens) != len(layout):
            continue  # malformed; skip silently
        named = dict(zip(layout, tokens))
        try:
            level = int(named["level"])
        except ValueError:
            continue
        species = named["species"]
        moves = tuple(named[k] for k in ("m1", "m2", "m3", "m4") if k in named and named[k])
        slots.append(PartySlot(species=species, level=level, moves=moves))
    if not slots:
        return
    trainer_id = _synthesize_trainer_id(group_class, occurrence)
    yield LeaderRoster(trainer_class=group_class, trainer_id=trainer_id, slots=tuple(slots))


# ---------- matchup computation ----------

def defensive_vector(types: tuple[str, str], matchups: dict[tuple[str, str], int]) -> tuple[int, ...]:
    """For each canonical attacker type T, what's T's effective multiplier vs (type_a, type_b)?

    Mirrors the asm matchup loop semantics:
      - For each (T, def_a) row that matches, multiply by mult/10.
      - For each (T, def_b) row that matches, multiply by mult/10.
      - NO_EFFECT collapses the product to 0 (the famous immunity rule).
    """
    type_a, type_b = types
    out: list[int] = []
    for attacker in CANONICAL_TYPE_ORDER:
        mults: list[int] = [matchup(matchups, attacker, type_a)]
        if type_b != type_a:
            mults.append(matchup(matchups, attacker, type_b))
        # Compose using the same convention: 0 collapses; otherwise multiply / 10.
        product = 10  # starting at NORMAL
        immune = False
        for m in mults:
            if m == M_NO_EFFECT:
                immune = True
                break
            product = (product * m) // 10
        if immune:
            out.append(M_NO_EFFECT)
        elif product == 0:
            out.append(M_NO_EFFECT)
        elif product < M_NORMAL:
            out.append(M_NOT_VERY)
        elif product == M_NORMAL:
            out.append(M_NORMAL)
        else:
            out.append(M_SUPER)
    return tuple(out)


def offensive_vector(
    move_names: tuple[str, ...],
    move_types: dict[str, str],
    matchups: dict[tuple[str, str], int],
) -> tuple[int, ...]:
    """For each canonical defender type T, what's the best multiplier this mon's moves can hit?"""
    out: list[int] = []
    move_type_set = [move_types[m] for m in move_names if m in move_types]
    for defender in CANONICAL_TYPE_ORDER:
        best = M_NO_EFFECT
        for atk_type in move_type_set:
            m = matchup(matchups, atk_type, defender)
            if m > best:
                best = m
        # Treat absence-of-info as NORMAL (a mon with unknown moves can do
        # at least neutral damage with a generic STAB). But we only consider
        # the moves we actually parsed.
        if not move_type_set:
            out.append(M_NORMAL)
        else:
            out.append(best)
    return tuple(out)


# ---------- emission ----------

HEADER = """; ============================================================
; data/boss_ai/matchup_tables.asm — Per-leader type matchup tables
;
; GENERATED by scripts/generate_boss_matchup_tables.py. Do not hand-edit;
; rerun the generator after any change to parties.asm, base_stats/*.asm,
; moves.asm, or type_matchups.asm.
;
; ABI (consumer-facing): see the script header for full byte layout.
; Brief: each leader row is `db <class>, <id>, <party_count>` followed by
; per-slot blocks. Each slot is `db <species>` + 17 defensive bytes + 17
; offensive bytes (canonical type order: NORMAL, FIGHTING, FLYING, POISON,
; GROUND, ROCK, BUG, GHOST, STEEL, FIRE, WATER, GRASS, ELECTRIC,
; PSYCHIC_TYPE, ICE, DRAGON, DARK). Multiplier bytes are raw matchup
; loop values: 0 = NO_EFFECT, 5 = NOT_VERY_EFFECTIVE, 10 = NORMAL,
; 20 = SUPER_EFFECTIVE.
;
; Table is terminated by a single `db 0` (trainer class 0 = sentinel).
; ============================================================

BossAIMatchupTables::
"""


def emit_table(rosters: list[LeaderRoster], matchups: dict[tuple[str, str], int], base_types: dict[str, tuple[str, str]], move_types: dict[str, str]) -> str:
    lines: list[str] = [HEADER.rstrip()]
    for r in rosters:
        slots_payload: list[str] = []
        valid = True
        for s in r.slots:
            if s.species not in base_types:
                valid = False
                break
            types = base_types[s.species]
            defv = defensive_vector(types, matchups)
            offv = offensive_vector(s.moves, move_types, matchups)
            slots_payload.append(_emit_slot(s.species, defv, offv))
        if not valid or not slots_payload:
            continue
        lines.append(f"\t; {r.trainer_class} : {r.trainer_id}")
        lines.append(f"\tdb {r.trainer_class}, {r.trainer_id}")
        lines.append(f"\tdb {len(r.slots)}")
        lines.extend(slots_payload)
        lines.append("")
    lines.append("\tdb 0 ; end-of-table sentinel")
    lines.append("")
    return "\n".join(lines)


def _emit_slot(species: str, defv: tuple[int, ...], offv: tuple[int, ...]) -> str:
    lines = [
        f"\tdb {species}",
        "\tdb " + ", ".join(str(b) for b in defv) + " ; defensive vector",
        "\tdb " + ", ".join(str(b) for b in offv) + " ; offensive vector",
    ]
    return "\n".join(lines)


# ---------- main ----------

def main(argv: list[str]) -> int:
    dry_run = "--dry-run" in argv
    try:
        matchups = parse_type_matchups(ROOT / "data" / "types" / "type_matchups.asm")
        base_types = parse_base_stats_types()
        move_types = parse_move_types()
        rosters = parse_eligible_rosters()
    except Exception as exc:
        print(f"FAIL: parse error: {exc}", file=sys.stderr)
        return 1

    if not rosters:
        print("FAIL: no eligible rosters found in parties.asm", file=sys.stderr)
        return 1

    table = emit_table(rosters, matchups, base_types, move_types)

    if dry_run:
        sys.stdout.write(table)
        return 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(table, encoding="utf-8", newline="\n")
    print(f"Wrote {OUT_PATH} ({len(rosters)} leader rosters, "
          f"{sum(len(r.slots) for r in rosters)} total slots).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
