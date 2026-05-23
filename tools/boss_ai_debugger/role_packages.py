from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
OUT_PATH = ROOT / "data" / "boss_ai" / "role_package_classifier.asm"

PACKAGE_ORDER: tuple[tuple[str, str, int], ...] = (
    ("spinner", "BOSS_AI_ROLEPKG_SPINNER_MASK", 1 << 0),
    ("phazer", "BOSS_AI_ROLEPKG_PHAZER_MASK", 1 << 1),
    ("setup-sweeper", "BOSS_AI_ROLEPKG_SETUP_SWEEPER_MASK", 1 << 2),
    ("recovery-wall", "BOSS_AI_ROLEPKG_RECOVERY_WALL_MASK", 1 << 3),
    ("priority-revenge", "BOSS_AI_ROLEPKG_PRIORITY_REVENGE_MASK", 1 << 4),
    ("sleep/status-pressure", "BOSS_AI_ROLEPKG_STATUS_PRESSURE_MASK", 1 << 5),
    ("trap/perish-line", "BOSS_AI_ROLEPKG_TRAP_PERISH_MASK", 1 << 6),
    ("physical/special-wallbreaker", "BOSS_AI_ROLEPKG_WALLBREAKER_MASK", 1 << 7),
)

PACKAGE_BY_NAME = {name: (symbol, mask) for name, symbol, mask in PACKAGE_ORDER}
PACKAGE_BY_SYMBOL = {symbol: (name, mask) for name, symbol, mask in PACKAGE_ORDER}

PHYSICAL_TYPES = {
    "NORMAL",
    "FIGHTING",
    "FLYING",
    "POISON",
    "GROUND",
    "ROCK",
    "BUG",
    "GHOST",
    "STEEL",
}
SPECIAL_TYPES = {
    "FIRE",
    "WATER",
    "GRASS",
    "ELECTRIC",
    "PSYCHIC_TYPE",
    "ICE",
    "DRAGON",
    "DARK",
}

SETUP_EFFECTS = {
    "EFFECT_DRAGON_DANCE",
    "EFFECT_CALM_MIND",
    "EFFECT_QUIVER_DANCE",
    "EFFECT_ATTACK_UP",
    "EFFECT_DEFENSE_UP",
    "EFFECT_SPEED_UP",
    "EFFECT_SP_ATK_UP",
    "EFFECT_SP_DEF_UP",
    "EFFECT_ATTACK_UP_2",
    "EFFECT_DEFENSE_UP_2",
    "EFFECT_SPEED_UP_2",
    "EFFECT_SP_ATK_UP_2",
    "EFFECT_SP_DEF_UP_2",
}
RELIABLE_RECOVERY_MOVES = {
    "RECOVER",
    "SOFTBOILED",
    "MILK_DRINK",
    "MORNING_SUN",
    "SYNTHESIS",
    "MOONLIGHT",
}
STATUS_PRESSURE_MOVES = {
    "SLEEP_POWDER",
    "HYPNOSIS",
    "SPORE",
    "LOVELY_KISS",
    "SING",
    "STUN_SPORE",
    "THUNDER_WAVE",
    "GLARE",
    "CONFUSE_RAY",
}
TRAP_PERISH_MOVES = {"MEAN_LOOK", "PERISH_SONG"}
PRIORITY_EFFECTS = {"EFFECT_PRIORITY_HIT"}


@dataclass(frozen=True)
class BaseStats:
    hp: int
    attack: int
    defense: int
    speed: int
    sp_attack: int
    sp_defense: int
    types: tuple[str, str]
    tmhm: frozenset[str]


@dataclass(frozen=True)
class MoveData:
    effect: str
    power: int
    type_name: str


@dataclass(frozen=True)
class RolePackageEntry:
    species: str
    mask: int
    packages: tuple[str, ...]
    public_moves: tuple[str, ...]


def _strip_comment(line: str) -> str:
    return line.split(";", 1)[0].strip()


def parse_species_order(root: Path = ROOT) -> list[str]:
    species: list[str] = []
    in_species = False
    for raw in (root / "constants" / "pokemon_constants.asm").read_text(encoding="utf-8").splitlines():
        line = _strip_comment(raw)
        if line == "const_def 1":
            in_species = True
            continue
        if in_species and line.startswith("DEF NUM_POKEMON"):
            break
        if not in_species:
            continue
        match = re.match(r"^const\s+([A-Z0-9_]+)\b", line)
        if match:
            species.append(match.group(1))
    if len(species) != 251:
        raise ValueError(f"expected 251 species constants, got {len(species)}")
    return species


def parse_moves(root: Path = ROOT) -> dict[str, MoveData]:
    moves: dict[str, MoveData] = {}
    for raw in (root / "data" / "moves" / "moves.asm").read_text(encoding="utf-8").splitlines():
        line = _strip_comment(raw)
        match = re.match(
            r"^move\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*,\s*(-?\d+)\s*,\s*([A-Z0-9_]+)\s*,",
            line,
        )
        if match:
            moves[match.group(1)] = MoveData(
                effect=match.group(2),
                power=int(match.group(3)),
                type_name=match.group(4),
            )
    return moves


def parse_base_stats(root: Path = ROOT) -> dict[str, BaseStats]:
    out: dict[str, BaseStats] = {}
    for path in (root / "data" / "pokemon" / "base_stats").glob("*.asm"):
        text = path.read_text(encoding="utf-8", errors="replace")
        species_match = re.search(r"^\s*db\s+([A-Z0-9_]+)\s*;\s*\d+\s*$", text, flags=re.MULTILINE)
        stats_match = re.search(
            r"^\s*db\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$",
            text,
            flags=re.MULTILINE,
        )
        type_match = re.search(r"^\s*db\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*;\s*type", text, flags=re.MULTILINE)
        tmhm_match = re.search(r"^\s*tmhm\s+(.+)$", text, flags=re.MULTILINE)
        if not species_match or not stats_match or not type_match:
            continue
        tmhm = frozenset(
            token.strip()
            for token in (tmhm_match.group(1).split(",") if tmhm_match else [])
            if token.strip()
        )
        out[species_match.group(1)] = BaseStats(
            hp=int(stats_match.group(1)),
            attack=int(stats_match.group(2)),
            defense=int(stats_match.group(3)),
            speed=int(stats_match.group(4)),
            sp_attack=int(stats_match.group(5)),
            sp_defense=int(stats_match.group(6)),
            types=(type_match.group(1), type_match.group(2)),
            tmhm=tmhm,
        )
    return out


def _parse_pointer_labels(path: Path) -> list[str]:
    labels: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = _strip_comment(raw)
        match = re.match(r"^dw\s+([A-Za-z0-9_]+)$", line)
        if match:
            labels.append(match.group(1))
    return labels


def _parse_move_list_block(text: str, label: str, terminator: str) -> list[str]:
    match = re.search(rf"^{re.escape(label)}:\s*$", text, flags=re.MULTILINE)
    if not match:
        return []
    tail = text[match.end() :].splitlines()
    moves: list[str] = []
    in_moves = terminator != "level"
    saw_evo_end = False
    for raw in tail:
        stripped = raw.strip()
        if stripped.endswith(":") and not stripped.startswith(("db ", "\tdb ")):
            break
        line = _strip_comment(raw)
        if not line:
            continue
        if terminator == "level":
            if line == "db 0":
                if not saw_evo_end:
                    saw_evo_end = True
                    in_moves = True
                    continue
                break
            if not in_moves:
                continue
            level_match = re.match(r"^db\s+\d+\s*,\s*([A-Z0-9_]+)$", line)
            if level_match:
                moves.append(level_match.group(1))
        else:
            if line == "db -1":
                break
            move_match = re.match(r"^db\s+([A-Z0-9_]+)$", line)
            if move_match:
                moves.append(move_match.group(1))
    return moves


def parse_level_up_moves(root: Path = ROOT) -> dict[str, frozenset[str]]:
    species = parse_species_order(root)
    labels = _parse_pointer_labels(root / "data" / "pokemon" / "evos_attacks_pointers.asm")
    text = (root / "data" / "pokemon" / "evos_attacks.asm").read_text(encoding="utf-8", errors="replace")
    if len(labels) != len(species):
        raise ValueError(f"evos/attacks pointers length {len(labels)} != species length {len(species)}")
    return {
        mon: frozenset(_parse_move_list_block(text, label, "level"))
        for mon, label in zip(species, labels)
    }


def parse_egg_moves(root: Path = ROOT) -> dict[str, frozenset[str]]:
    species = parse_species_order(root)
    labels = _parse_pointer_labels(root / "data" / "pokemon" / "egg_move_pointers.asm")
    text = (root / "data" / "pokemon" / "egg_moves.asm").read_text(encoding="utf-8", errors="replace")
    if len(labels) != len(species):
        raise ValueError(f"egg pointers length {len(labels)} != species length {len(species)}")
    return {
        mon: frozenset(_parse_move_list_block(text, label, "egg"))
        for mon, label in zip(species, labels)
    }


def _has_damaging_move(
    moves: Iterable[str],
    move_data: dict[str, MoveData],
    *,
    type_family: set[str],
    min_power: int,
) -> bool:
    for move in moves:
        data = move_data.get(move)
        if not data:
            continue
        if data.power >= min_power and data.type_name in type_family:
            return True
    return False


def classify_species(
    species: str,
    stats: BaseStats,
    public_moves: frozenset[str],
    move_data: dict[str, MoveData],
) -> int:
    effects = {move_data[move].effect for move in public_moves if move in move_data}
    mask = 0

    if "RAPID_SPIN" in public_moves:
        mask |= PACKAGE_BY_NAME["spinner"][1]
    if "ROAR" in public_moves or "WHIRLWIND" in public_moves:
        mask |= PACKAGE_BY_NAME["phazer"][1]
    if effects & SETUP_EFFECTS and (stats.speed >= 80 or max(stats.attack, stats.sp_attack) >= 95):
        mask |= PACKAGE_BY_NAME["setup-sweeper"][1]
    if public_moves & RELIABLE_RECOVERY_MOVES and stats.hp + stats.defense + stats.sp_defense >= 260:
        mask |= PACKAGE_BY_NAME["recovery-wall"][1]
    if effects & PRIORITY_EFFECTS:
        mask |= PACKAGE_BY_NAME["priority-revenge"][1]
    if public_moves & STATUS_PRESSURE_MOVES:
        mask |= PACKAGE_BY_NAME["sleep/status-pressure"][1]
    if public_moves & TRAP_PERISH_MOVES:
        mask |= PACKAGE_BY_NAME["trap/perish-line"][1]
    if stats.attack >= 105 and _has_damaging_move(public_moves, move_data, type_family=PHYSICAL_TYPES, min_power=80):
        mask |= PACKAGE_BY_NAME["physical/special-wallbreaker"][1]
    if stats.sp_attack >= 105 and _has_damaging_move(public_moves, move_data, type_family=SPECIAL_TYPES, min_power=80):
        mask |= PACKAGE_BY_NAME["physical/special-wallbreaker"][1]
    return mask


def package_names(mask: int) -> tuple[str, ...]:
    return tuple(name for name, _symbol, bit in PACKAGE_ORDER if mask & bit)


def build_role_package_table(root: Path = ROOT) -> list[RolePackageEntry]:
    species_order = parse_species_order(root)
    base_stats = parse_base_stats(root)
    moves = parse_moves(root)
    level_up = parse_level_up_moves(root)
    egg = parse_egg_moves(root)
    entries: list[RolePackageEntry] = []
    for species in species_order:
        stats = base_stats[species]
        public_moves = frozenset(level_up.get(species, frozenset()) | stats.tmhm | egg.get(species, frozenset()))
        mask = classify_species(species, stats, public_moves, moves)
        entries.append(
            RolePackageEntry(
                species=species,
                mask=mask,
                packages=package_names(mask),
                public_moves=tuple(sorted(public_moves)),
            )
        )
    return entries


def asm_mask_expr(mask: int) -> str:
    if mask == 0:
        return "0"
    return " | ".join(symbol for _name, symbol, bit in PACKAGE_ORDER if mask & bit)


def render_role_package_asm(entries: list[RolePackageEntry]) -> str:
    lines = [
        "; Generated by scripts/generate_boss_role_package_table.py.",
        "; Do not hand-edit; source truth is visible species public learnability",
        "; from data/pokemon/* plus move metadata from data/moves/moves.asm.",
        ";",
        "; Each row is one byte indexed by species id - 1: package bits 0..7.",
        "",
        "BossAIRolePackageBySpecies::",
        "\ttable_width 1, BossAIRolePackageBySpecies",
    ]
    for entry in entries:
        names = ", ".join(entry.packages) if entry.packages else "none"
        lines.append(f"\tdb {asm_mask_expr(entry.mask)} ; {entry.species}: {names}")
    lines.extend(
        [
            "\tassert_table_length NUM_POKEMON",
            "",
        ]
    )
    return "\n".join(lines)


def write_role_package_asm(root: Path = ROOT, out_path: Path = OUT_PATH) -> str:
    text = render_role_package_asm(build_role_package_table(root))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8", newline="\n")
    return text


def parse_generated_role_package_table(path: Path = OUT_PATH) -> dict[str, int]:
    text = path.read_text(encoding="utf-8")
    out: dict[str, int] = {}
    for raw in text.splitlines():
        match = re.match(r"\s*db\s+(.+?)\s*;\s*([A-Z0-9_]+):", raw)
        if not match:
            continue
        expr, species = match.group(1), match.group(2)
        out[species] = _eval_asm_mask_expr(expr)
    return out


def _eval_asm_mask_expr(expr: str) -> int:
    parts = [part.strip() for part in expr.split("|") if part.strip()]
    value = 0
    for part in parts:
        if part == "0":
            continue
        if part not in PACKAGE_BY_SYMBOL:
            raise ValueError(f"unknown package symbol in generated table: {part}")
        value |= PACKAGE_BY_SYMBOL[part][1]
    return value


def describe_species(species_names: Iterable[str], *, root: Path = ROOT) -> list[dict[str, object]]:
    generated = parse_generated_role_package_table(root / "data" / "boss_ai" / "role_package_classifier.asm")
    built = {entry.species: entry for entry in build_role_package_table(root)}
    rows: list[dict[str, object]] = []
    for raw_name in species_names:
        species = raw_name.strip().upper()
        if species not in built:
            raise ValueError(f"unknown species: {raw_name}")
        row = built[species]
        committed_mask = generated.get(species)
        rows.append(
            {
                "species": species,
                "mask": row.mask,
                "packages": list(row.packages),
                "committed_mask": committed_mask,
                "committed_packages": list(package_names(committed_mask or 0)),
                "committed_matches_source": committed_mask == row.mask,
            }
        )
    return rows


def format_role_package_rows(rows: list[dict[str, object]]) -> str:
    lines = ["Boss AI role-package classifier"]
    for row in rows:
        packages = row["committed_packages"] or ["unclassified"]
        status = "OK" if row["committed_matches_source"] else "DRIFT"
        lines.append(f"- {row['species']}: {', '.join(packages)} ({status})")
    return "\n".join(lines)
