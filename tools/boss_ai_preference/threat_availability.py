from __future__ import annotations

import copy
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .damage_estimates import display_move_name, estimate_move_damage, move_data, pokemon_data


ROOT = Path(__file__).resolve().parents[2]
BASE_STATS_DIR = ROOT / "data" / "pokemon" / "base_stats"
EVOS_ATTACKS_PATH = ROOT / "data" / "pokemon" / "evos_attacks.asm"
EVOS_POINTERS_PATH = ROOT / "data" / "pokemon" / "evos_attacks_pointers.asm"
ITEM_CONSTANTS_PATH = ROOT / "constants" / "item_constants.asm"
MART_CONSTANTS_PATH = ROOT / "constants" / "mart_constants.asm"
POKEMON_CONSTANTS_PATH = ROOT / "constants" / "pokemon_constants.asm"
EXPERIENCE_PATH = ROOT / "engine" / "pokemon" / "experience.asm"
MAP_METADATA_PATH = ROOT / "data" / "maps" / "maps.asm"
MAPS_DIR = ROOT / "maps"
WILD_DIR = ROOT / "data" / "wild"
MARTS_PATH = ROOT / "data" / "items" / "marts.asm"
DEFAULT_THREAT_REPORT_PATH = ROOT / "audit" / "boss_ai_preference" / "threat_availability_report.md"
DEFAULT_THREAT_JSON_PATH = ROOT / "audit" / "boss_ai_preference" / "threat_availability_report.json"

LIKELIHOOD_BUCKETS = (0, 25, 50, 75, 99)
STAB_FLOOR_BY_SOURCE = {
    "revealed": 99,
    "level_up": 75,
    "pre_evo_level_up": 50,
    "tm_available": 50,
}


@dataclass(frozen=True)
class Checkpoint:
    id: str
    leader: str
    level_cap: int
    badges_before: int
    wild_maps: tuple[str, ...]
    direct_tm_files: tuple[str, ...]
    rod_tiers: tuple[str, ...] = ()
    event_files: tuple[str, ...] = ()
    static_files: tuple[str, ...] = ()
    surf_available: bool = False
    notes: tuple[str, ...] = ()


PRE_FALKNER_MAPS = (
    "ROUTE_29",
    "ROUTE_30",
    "ROUTE_31",
    "ROUTE_46",
    "DARK_CAVE_VIOLET_ENTRANCE",
    "SPROUT_TOWER_2F",
    "SPROUT_TOWER_3F",
    "RUINS_OF_ALPH_INNER_CHAMBER",
)
PRE_BUGSY_MAPS = PRE_FALKNER_MAPS + (
    "ROUTE_32",
    "ROUTE_33",
    "UNION_CAVE_1F",
    "UNION_CAVE_B1F",
    "SLOWPOKE_WELL_B1F",
)
PRE_WHITNEY_MAPS = PRE_BUGSY_MAPS + (
    "ILEX_FOREST",
    "ROUTE_34",
    "ROUTE_35",
    "NATIONAL_PARK",
    "ROUTE_36",
)
PRE_MORTY_MAPS = PRE_WHITNEY_MAPS + (
    "ROUTE_37",
    "BURNED_TOWER_1F",
    "BURNED_TOWER_B1F",
)
MID_JOHTO_MAPS = PRE_MORTY_MAPS + (
    "ROUTE_38",
    "ROUTE_39",
    "ROUTE_40",
    "ROUTE_41",
    "ROUTE_42",
    "ROUTE_43",
    "LAKE_OF_RAGE",
    "MOUNT_MORTAR_1F_OUTSIDE",
    "MOUNT_MORTAR_1F_INSIDE",
    "MOUNT_MORTAR_B1F",
    "CIANWOOD_CITY",
    "OLIVINE_CITY",
    "ECRUTEAK_CITY",
)
PRE_CLAIR_MAPS = MID_JOHTO_MAPS + (
    "ROUTE_44",
    "ROUTE_45",
    "ICE_PATH_1F",
    "ICE_PATH_B1F",
    "ICE_PATH_B2F_MAHOGANY_SIDE",
    "ICE_PATH_B2F_BLACKTHORN_SIDE",
    "ICE_PATH_B3F",
    "DARK_CAVE_BLACKTHORN_ENTRANCE",
    "BLACKTHORN_CITY",
)

EARLY_TM_FILES = (
    "Route31.asm",
)
PRE_BUGSY_TM_FILES = EARLY_TM_FILES + (
    "Route32.asm",
)
PRE_WHITNEY_TM_FILES = PRE_BUGSY_TM_FILES + (
    "IlexForest.asm",
    "GoldenrodGameCorner.asm",
    "GoldenrodDeptStore5F.asm",
    "Route34IlexForestGate.asm",
    "Route36.asm",
)
PRE_MORTY_TM_FILES = PRE_WHITNEY_TM_FILES
MID_JOHTO_TM_FILES = PRE_MORTY_TM_FILES + (
    "LakeOfRageHiddenPowerHouse.asm",
    "RadioTower3F.asm",
    "Route39Farmhouse.asm",
    "Route43Gate.asm",
)
PRE_CLAIR_TM_FILES = MID_JOHTO_TM_FILES
PRE_CHAMPION_TM_FILES = PRE_CLAIR_TM_FILES + (
    "Route27.asm",
    "Route27SandstormHouse.asm",
    "VictoryRoad.asm",
)

NO_RODS: tuple[str, ...] = ()
OLD_ROD = ("old",)
GOOD_ROD = ("old", "good")
SUPER_ROD = ("old", "good", "super")

PRE_FALKNER_EVENT_FILES = ("ElmsLab.asm",)
PRE_BUGSY_EVENT_FILES = PRE_FALKNER_EVENT_FILES
PRE_WHITNEY_EVENT_FILES = PRE_BUGSY_EVENT_FILES + (
    "GoldenrodGameCorner.asm",
    "Route35GoldenrodGate.asm",
)
PRE_MORTY_EVENT_FILES = PRE_WHITNEY_EVENT_FILES
MID_JOHTO_EVENT_FILES = PRE_MORTY_EVENT_FILES + (
    "MountMortarB1F.asm",
)
PRE_CLAIR_EVENT_FILES = MID_JOHTO_EVENT_FILES
PRE_CHAMPION_EVENT_FILES = PRE_CLAIR_EVENT_FILES
POSTGAME_EVENT_FILES = PRE_CHAMPION_EVENT_FILES + (
    "BillsFamilysHouse.asm",
    "CeladonGameCornerPrizeRoom.asm",
)

PRE_MORTY_STATIC_FILES = (
    "Route36.asm",
)
MID_JOHTO_STATIC_FILES = PRE_MORTY_STATIC_FILES + (
    "LakeOfRage.asm",
    "UnionCaveB2F.asm",
    "TeamRocketBaseB1F.asm",
    "TeamRocketBaseB2F.asm",
)
PRE_CLAIR_STATIC_FILES = MID_JOHTO_STATIC_FILES
PRE_CHAMPION_STATIC_FILES = PRE_CLAIR_STATIC_FILES
POSTGAME_STATIC_FILES = PRE_CHAMPION_STATIC_FILES + (
    "VermilionCity.asm",
)

CHECKPOINTS = (
    Checkpoint(
        "falkner",
        "Falkner",
        14,
        0,
        PRE_FALKNER_MAPS,
        EARLY_TM_FILES,
        event_files=PRE_FALKNER_EVENT_FILES,
    ),
    Checkpoint(
        "bugsy",
        "Bugsy",
        17,
        1,
        PRE_BUGSY_MAPS,
        PRE_BUGSY_TM_FILES,
        rod_tiers=OLD_ROD,
        event_files=PRE_BUGSY_EVENT_FILES,
    ),
    Checkpoint(
        "whitney",
        "Whitney",
        21,
        2,
        PRE_WHITNEY_MAPS,
        PRE_WHITNEY_TM_FILES,
        rod_tiers=OLD_ROD,
        event_files=PRE_WHITNEY_EVENT_FILES,
    ),
    Checkpoint(
        "morty",
        "Morty",
        26,
        3,
        PRE_MORTY_MAPS,
        PRE_MORTY_TM_FILES,
        rod_tiers=OLD_ROD,
        event_files=PRE_MORTY_EVENT_FILES,
        static_files=PRE_MORTY_STATIC_FILES,
    ),
    Checkpoint(
        "chuck",
        "Chuck",
        34,
        4,
        MID_JOHTO_MAPS,
        MID_JOHTO_TM_FILES,
        rod_tiers=GOOD_ROD,
        event_files=MID_JOHTO_EVENT_FILES,
        static_files=MID_JOHTO_STATIC_FILES,
        surf_available=True,
        notes=(
            "Mid-Johto order is flexible; checkpoint assumes four prior badges.",
        ),
    ),
    Checkpoint(
        "jasmine",
        "Jasmine",
        34,
        4,
        MID_JOHTO_MAPS,
        MID_JOHTO_TM_FILES,
        rod_tiers=GOOD_ROD,
        event_files=MID_JOHTO_EVENT_FILES,
        static_files=MID_JOHTO_STATIC_FILES,
        surf_available=True,
        notes=(
            "Mid-Johto order is flexible; checkpoint assumes four prior badges.",
        ),
    ),
    Checkpoint(
        "pryce",
        "Pryce",
        34,
        4,
        MID_JOHTO_MAPS,
        MID_JOHTO_TM_FILES,
        rod_tiers=GOOD_ROD,
        event_files=MID_JOHTO_EVENT_FILES,
        static_files=MID_JOHTO_STATIC_FILES,
        surf_available=True,
        notes=(
            "Mid-Johto order is flexible; checkpoint assumes four prior badges.",
        ),
    ),
    Checkpoint(
        "clair",
        "Clair",
        39,
        7,
        PRE_CLAIR_MAPS,
        PRE_CLAIR_TM_FILES,
        rod_tiers=GOOD_ROD,
        event_files=PRE_CLAIR_EVENT_FILES,
        static_files=PRE_CLAIR_STATIC_FILES,
        surf_available=True,
    ),
    Checkpoint(
        "champion_lance",
        "Champion Lance",
        50,
        8,
        ("ALL_NON_SILVER",),
        PRE_CHAMPION_TM_FILES,
        rod_tiers=GOOD_ROD,
        event_files=PRE_CHAMPION_EVENT_FILES,
        static_files=PRE_CHAMPION_STATIC_FILES,
        surf_available=True,
    ),
    Checkpoint(
        "koga",
        "Koga",
        50,
        8,
        ("ALL_NON_SILVER",),
        PRE_CHAMPION_TM_FILES,
        rod_tiers=GOOD_ROD,
        event_files=PRE_CHAMPION_EVENT_FILES,
        static_files=PRE_CHAMPION_STATIC_FILES,
        surf_available=True,
    ),
    Checkpoint(
        "brock",
        "Brock",
        60,
        8,
        ("ALL_NON_SILVER",),
        ("ALL",),
        rod_tiers=SUPER_ROD,
        event_files=POSTGAME_EVENT_FILES,
        static_files=POSTGAME_STATIC_FILES,
        surf_available=True,
    ),
    Checkpoint(
        "misty",
        "Misty",
        63,
        8,
        ("ALL_NON_SILVER",),
        ("ALL",),
        rod_tiers=SUPER_ROD,
        event_files=POSTGAME_EVENT_FILES,
        static_files=POSTGAME_STATIC_FILES,
        surf_available=True,
    ),
    Checkpoint(
        "lt_surge",
        "Lt. Surge",
        65,
        8,
        ("ALL_NON_SILVER",),
        ("ALL",),
        rod_tiers=SUPER_ROD,
        event_files=POSTGAME_EVENT_FILES,
        static_files=POSTGAME_STATIC_FILES,
        surf_available=True,
    ),
    Checkpoint(
        "erika",
        "Erika",
        64,
        8,
        ("ALL_NON_SILVER",),
        ("ALL",),
        rod_tiers=SUPER_ROD,
        event_files=POSTGAME_EVENT_FILES,
        static_files=POSTGAME_STATIC_FILES,
        surf_available=True,
    ),
    Checkpoint(
        "janine",
        "Janine",
        64,
        8,
        ("ALL_NON_SILVER",),
        ("ALL",),
        rod_tiers=SUPER_ROD,
        event_files=POSTGAME_EVENT_FILES,
        static_files=POSTGAME_STATIC_FILES,
        surf_available=True,
    ),
    Checkpoint(
        "sabrina",
        "Sabrina",
        67,
        8,
        ("ALL_NON_SILVER",),
        ("ALL",),
        rod_tiers=SUPER_ROD,
        event_files=POSTGAME_EVENT_FILES,
        static_files=POSTGAME_STATIC_FILES,
        surf_available=True,
    ),
    Checkpoint(
        "blaine",
        "Blaine",
        65,
        8,
        ("ALL_NON_SILVER",),
        ("ALL",),
        rod_tiers=SUPER_ROD,
        event_files=POSTGAME_EVENT_FILES,
        static_files=POSTGAME_STATIC_FILES,
        surf_available=True,
    ),
    Checkpoint(
        "blue",
        "Blue",
        69,
        16,
        ("ALL_NON_SILVER",),
        ("ALL",),
        rod_tiers=SUPER_ROD,
        event_files=POSTGAME_EVENT_FILES,
        static_files=POSTGAME_STATIC_FILES,
        surf_available=True,
    ),
)

STARTER_SPECIES = ("CHIKORITA", "CYNDAQUIL", "TOTODILE")


def checkpoint_for_leader(leader: str) -> Checkpoint:
    normalized = normalize_id(leader)
    for checkpoint in CHECKPOINTS:
        if normalize_id(checkpoint.leader) == normalized:
            return checkpoint
    return CHECKPOINTS[-1]


def attach_incoming_threats(fixtures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    annotated = copy.deepcopy(fixtures)
    for fixture in annotated:
        fixture["incoming_threats"] = relevant_fixture_threats(fixture)
    return annotated


def relevant_fixture_threats(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    threats: list[dict[str, Any]] = []
    checkpoint = checkpoint_for_leader(str(fixture.get("leader", "")))
    state = fixture.get("state", {})
    boss = state.get("boss", {}).get("active", {})
    player_state = state.get("player", {})
    active = player_state.get("active", {})
    field = state.get("field", {})

    active_threats = threats_for_pokemon(
        active,
        boss,
        field,
        checkpoint,
        immediacy="active",
    )
    threats.extend(active_threats)

    active_species = normalize_species_constant(active.get("species"))
    for species in player_state.get("seen_party", []):
        if normalize_species_constant(species) == active_species:
            continue
        seen = {"species": species, "level": checkpoint.level_cap, "revealed_moves": []}
        threats.extend(
            threats_for_pokemon(
                seen,
                boss,
                field,
                checkpoint,
                immediacy="switch",
            )
        )

    visible = [threat for threat in threats if should_show_threat(threat)]
    visible.sort(
        key=lambda threat: (
            immediacy_rank(threat["immediacy"]),
            switch_fit_rank(threat.get("switch_fit")),
            -int(threat["likelihood"]),
            -damage_high_percent(threat),
            threat["species"],
            threat["move"],
        )
    )
    return visible[:8]


def threats_for_pokemon(
    pokemon: dict[str, Any],
    defender: dict[str, Any],
    field: dict[str, Any],
    checkpoint: Checkpoint,
    *,
    immediacy: str,
) -> list[dict[str, Any]]:
    species = normalize_species_constant(pokemon.get("species"))
    if not species:
        return []
    attacker = dict(pokemon)
    attacker.setdefault("level", checkpoint.level_cap)
    revealed_moves = {
        normalize_move_constant(move)
        for move in pokemon.get("revealed_moves", [])
        if normalize_move_constant(move)
    }
    legal = legal_moves_for_species(species, checkpoint)
    all_moves = sorted(set(legal) | revealed_moves)
    entry_risk = None
    if immediacy == "switch":
        entry_risk = switch_entry_risk(attacker, defender, field)
    threats: list[dict[str, Any]] = []
    for move in all_moves:
        sources = list(legal.get(move, []))
        revealed = move in revealed_moves
        likelihood, reasons = likelihood_for_move(
            species=species,
            move=move,
            sources=sources,
            revealed=revealed,
            revealed_count=len(revealed_moves),
        )
        damage = estimate_move_damage(move, attacker, defender, field)
        threats.append(
            {
                "species": display_species(species),
                "move": display_move_name(move),
                "move_id": move,
                "likelihood": likelihood,
                "bucket": f"{likelihood}%",
                "sources": sorted(set(sources + (["revealed"] if revealed else []))),
                "reasons": reasons,
                "immediacy": immediacy,
                "damage": damage,
                "severity": severity_for_damage(damage, defender),
                "switch_fit": entry_risk["fit"] if entry_risk else None,
                "entry_risk": entry_risk,
            }
        )
    return threats


def legal_moves_for_species(species: str, checkpoint: Checkpoint) -> dict[str, list[str]]:
    moves: dict[str, set[str]] = defaultdict(set)
    for level, move in learnsets().get(species, []):
        if level <= checkpoint.level_cap:
            moves[move].add("level_up")
    for predecessor in legal_predecessors(species, checkpoint.level_cap):
        for level, move in learnsets().get(predecessor, []):
            if level <= checkpoint.level_cap:
                moves[move].add("pre_evo_level_up")
    direct_tms = direct_tm_moves_for_checkpoint(checkpoint)
    for move in tmhm_learnsets().get(species, set()):
        if move in direct_tms:
            moves[move].add("tm_available")
    return {move: sorted(sources) for move, sources in sorted(moves.items())}


def likelihood_for_move(
    *,
    species: str,
    move: str,
    sources: list[str],
    revealed: bool,
    revealed_count: int,
) -> tuple[int, list[str]]:
    if revealed:
        reasons = ["revealed in the public fixture state"]
        if not sources:
            reasons.append("fixture-attested but not derivable from ROM at this checkpoint")
        return 99, reasons
    if revealed_count >= 4:
        return 0, ["four revealed moves already fill the moveset"]
    if not sources:
        return 0, ["not legal from source-derived learnset/TM data at this checkpoint"]

    data = move_data().get(move)
    stab = False
    mon = pokemon_data(display_species(species))
    if data is not None and mon is not None:
        stab = data.type_name in mon.type_names

    if "level_up" in sources:
        if stab:
            return 75, ["natural level-up STAB/core move by this checkpoint"]
        return 50, ["natural level-up move by this checkpoint"]
    if "pre_evo_level_up" in sources:
        return 50, ["legal via pre-evolution level-up path"]
    if "tm_available" in sources:
        return 50, ["direct TM source is available by this checkpoint"]
    return 25, ["legal but optional or low-confidence source"]


def should_show_threat(threat: dict[str, Any]) -> bool:
    if int(threat["likelihood"]) <= 0:
        return False
    if (
        threat.get("immediacy") == "switch"
        and threat.get("switch_fit") == "bad"
        and threat.get("severity") not in {"lethal", "major"}
    ):
        return False
    if "revealed" in threat["sources"]:
        return True
    damage = threat.get("damage")
    if not damage:
        return False
    high = int(damage.get("high_percent") or 0)
    return high >= 25 or threat["severity"] in {"lethal", "major"}


def severity_for_damage(damage: dict[str, Any] | None, defender: dict[str, Any]) -> str:
    if damage is None:
        return "support"
    high = int(damage.get("high_percent") or 0)
    current_hp = parse_percent(defender.get("hp"))
    if current_hp is not None and high >= current_hp:
        return "lethal"
    if high >= 70:
        return "major"
    if high >= 35:
        return "meaningful"
    return "chip"


def damage_high_percent(threat: dict[str, Any]) -> int:
    damage = threat.get("damage")
    if not isinstance(damage, dict):
        return 0
    return int(damage.get("high_percent") or 0)


def switch_entry_risk(
    switch_candidate: dict[str, Any],
    boss_active: dict[str, Any],
    field: dict[str, Any],
) -> dict[str, Any]:
    estimates: list[dict[str, Any]] = []
    target = dict(switch_candidate)
    target.setdefault("hp", "100%")
    for move in boss_active.get("revealed_moves", []):
        move_id = normalize_move_constant(move)
        if not move_id:
            continue
        estimate = estimate_move_damage(
            move_id,
            boss_active,
            target,
            field,
            defender_side="player",
        )
        if estimate is not None:
            estimates.append({"move": display_move_name(move_id), "damage": estimate})

    if not estimates:
        return {
            "fit": "unknown",
            "reason": "no revealed damaging boss move to judge the switch-in",
        }

    worst = max(estimates, key=lambda row: int(row["damage"].get("high_percent") or 0))
    high = int(worst["damage"].get("high_percent") or 0)
    if high >= 40:
        fit = "bad"
        reason = "bad switch into revealed boss damage"
    elif high >= 25:
        fit = "risky"
        reason = "risky switch into revealed boss damage"
    else:
        fit = "reasonable"
        reason = "reasonable switch into revealed boss damage"

    return {
        "fit": fit,
        "reason": reason,
        "move": worst["move"],
        "damage": worst["damage"],
    }


def build_threat_report(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    fixture_species_by_leader: dict[str, set[str]] = defaultdict(set)
    for fixture in fixtures:
        state = fixture.get("state", {})
        leader = str(fixture.get("leader", ""))
        player = state.get("player", {})
        active_species = normalize_species_constant(player.get("active", {}).get("species"))
        if active_species:
            fixture_species_by_leader[leader].add(active_species)
        for species in player.get("seen_party", []):
            normalized = normalize_species_constant(species)
            if normalized:
                fixture_species_by_leader[leader].add(normalized)

    checkpoints = []
    for checkpoint in CHECKPOINTS:
        species_sources = available_species_for_checkpoint(
            checkpoint,
            fixture_species_by_leader.get(checkpoint.leader, set()),
        )
        direct_tms = sorted(direct_tm_moves_for_checkpoint(checkpoint))
        checkpoints.append(
            {
                "id": checkpoint.id,
                "leader": checkpoint.leader,
                "level_cap": checkpoint.level_cap,
                "badges_before": checkpoint.badges_before,
                "rod_tiers": list(checkpoint.rod_tiers),
                "surf_available": checkpoint.surf_available,
                "event_files": list(checkpoint.event_files),
                "static_files": list(checkpoint.static_files),
                "wild_map_count": len(expanded_wild_maps(checkpoint)),
                "available_species_count": len(species_sources),
                "available_species": [
                    {
                        "species": display_species(species),
                        "sources": sorted(sources),
                    }
                    for species, sources in sorted(species_sources.items())
                ],
                "direct_tm_moves": [display_move_name(move) for move in direct_tms],
                "notes": list(checkpoint.notes),
            }
        )
    sample_threats = {
        fixture["id"]: relevant_fixture_threats(fixture)
        for fixture in fixtures
    }
    return {
        "schema_version": 1,
        "likelihood_buckets": list(LIKELIHOOD_BUCKETS),
        "source_files": [
            "data/pokemon/evos_attacks.asm",
            "data/pokemon/base_stats/*.asm",
            "data/wild/*.asm",
            "data/maps/maps.asm",
            "data/items/marts.asm",
            "constants/mart_constants.asm",
            "maps/*.asm",
            "engine/pokemon/experience.asm",
        ],
        "known_limits": [
            "Route reachability is a conservative checkpoint list, not a pathfinder.",
            "Wild grass, Surf-gated water, fishing tables, givepoke gifts/prizes, listed static encounters, direct TM scripts, and mart TM tables are parsed; breeding, trades, roaming RNG, and prerequisite-heavy statics are not fully route-modeled yet.",
            "Likelihood buckets are review buckets, not measured player behavior.",
        ],
        "checkpoints": checkpoints,
        "fixture_threats": sample_threats,
    }


def render_threat_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Boss AI Player Threat Availability Report",
        "",
        "Generated from ROM source tables for the Boss AI preference lab.",
        "",
        "## Likelihood Buckets",
        "",
        "- `99%`: revealed or forced by public fixture evidence.",
        "- `75%`: natural STAB/core level-up move.",
        "- `50%`: natural non-STAB level-up move, pre-evo move, or direct TM access.",
        "- `25%`: legal but optional or low-confidence.",
        "- `0%`: unavailable or blocked by a four-revealed-move set.",
        "",
        "## Known Limits",
        "",
    ]
    lines.extend(f"- {limit}" for limit in report["known_limits"])
    lines.extend(["", "## Checkpoints", ""])
    for checkpoint in report["checkpoints"]:
        lines.append(
            f"- `{checkpoint['id']}` ({checkpoint['leader']}): cap "
            f"{checkpoint['level_cap']}, badges before {checkpoint['badges_before']}, "
            f"rods {checkpoint['rod_tiers'] or ['none']}, "
            f"surf {'available' if checkpoint['surf_available'] else 'not usable'}, "
            f"{checkpoint['available_species_count']} available/current-public species, "
            f"{len(checkpoint['direct_tm_moves'])} direct TM move(s)."
        )
    lines.extend(["", "## Fixture Threat Samples", ""])
    for fixture_id, threats in report["fixture_threats"].items():
        lines.append(f"### `{fixture_id}`")
        if not threats:
            lines.append("")
            lines.append("No relevant incoming damaging threats surfaced.")
            lines.append("")
            continue
        lines.append("")
        for threat in threats[:5]:
            damage = threat.get("damage")
            damage_label = "support/no rough damage"
            if damage:
                damage_label = f"{damage['label']} vs {damage['target']}"
            entry_label = ""
            entry = threat.get("entry_risk")
            if entry and entry.get("damage"):
                entry_label = (
                    f"; switch fit {entry['fit']} vs {entry['move']} "
                    f"({entry['damage']['label']} into {entry['damage']['target']})"
                )
            reasons = "; ".join(threat["reasons"])
            lines.append(
                f"- {threat['species']} `{threat['move']}`: {threat['bucket']}, "
                f"{threat['severity']}, {threat['immediacy']}; {damage_label}"
                f"{entry_label}. {reasons}"
            )
        lines.append("")
    return "\n".join(lines)


def write_threat_report(
    fixtures: list[dict[str, Any]],
    *,
    out_path: Path = DEFAULT_THREAT_REPORT_PATH,
    json_out_path: Path = DEFAULT_THREAT_JSON_PATH,
) -> dict[str, Any]:
    report = build_threat_report(fixtures)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_threat_markdown(report), encoding="utf-8", newline="\n")
    json_out_path.parent.mkdir(parents=True, exist_ok=True)
    json_out_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def available_species_for_checkpoint(
    checkpoint: Checkpoint,
    fixture_species: set[str] | None = None,
) -> dict[str, set[str]]:
    available: dict[str, set[str]] = defaultdict(set)
    for species in STARTER_SPECIES:
        available[species].add("starter_choice")
    for species, maps in wild_species_by_map("grass").items():
        if maps & expanded_wild_maps(checkpoint):
            available[species].add("grass_encounter")
    if checkpoint.surf_available:
        for species, maps in wild_species_by_map("water").items():
            if maps & expanded_wild_maps(checkpoint):
                available[species].add("surf_encounter")
    for species, sources in fishing_species_for_checkpoint(checkpoint).items():
        available[species].update(sources)
    for species, sources in gift_species_for_checkpoint(checkpoint).items():
        available[species].update(sources)
    for species, sources in static_species_for_checkpoint(checkpoint).items():
        available[species].update(sources)
    if fixture_species:
        for species in fixture_species:
            available[species].add("fixture_public_species")

    changed = True
    while changed:
        changed = False
        for species in list(available):
            for method, level, evolved in evolutions().get(species, []):
                if method == "EVOLVE_LEVEL" and level <= checkpoint.level_cap:
                    if evolved not in available:
                        available[evolved].add("level_evolution")
                        changed = True
    return available


@lru_cache(maxsize=None)
def wild_species_by_map(encounter_kind: str) -> dict[str, set[str]]:
    species_maps: dict[str, set[str]] = defaultdict(set)
    current_map: str | None = None
    start_pattern = re.compile(rf"^\s*def_{encounter_kind}_wildmons\s+([A-Z0-9_]+)")
    entry_pattern = re.compile(r"^\s*db\s+\d+\s*,\s*([A-Z0-9_]+)")
    for path in WILD_DIR.glob("*.asm"):
        if path.name in {"fish.asm", "probabilities.asm"}:
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            start = start_pattern.match(raw)
            if start:
                current_map = start.group(1)
                continue
            if raw.strip().startswith("end_"):
                current_map = None
                continue
            if current_map is None:
                continue
            entry = entry_pattern.match(raw)
            if entry:
                species_maps[entry.group(1)].add(current_map)
    return species_maps


@lru_cache(maxsize=1)
def all_wild_maps() -> frozenset[str]:
    maps: set[str] = set()
    for encounter_kind in ("grass", "water"):
        for map_names in wild_species_by_map(encounter_kind).values():
            maps.update(map_names)
    maps.update(map_fish_groups())
    return frozenset(maps)


def expanded_wild_maps(checkpoint: Checkpoint) -> set[str]:
    maps = set(checkpoint.wild_maps)
    if "ALL_NON_SILVER" in maps:
        maps.remove("ALL_NON_SILVER")
        maps.update(name for name in all_wild_maps() if not name.startswith("SILVER_CAVE"))
    return maps


def fishing_species_for_checkpoint(checkpoint: Checkpoint) -> dict[str, set[str]]:
    if not checkpoint.rod_tiers:
        return {}
    species_sources: dict[str, set[str]] = defaultdict(set)
    fish_groups = map_fish_groups()
    fish_rows = fish_species_by_group_and_rod()
    for map_name in expanded_wild_maps(checkpoint):
        group = fish_groups.get(map_name)
        if group is None or group == "FISHGROUP_NONE":
            continue
        for rod in checkpoint.rod_tiers:
            for species, level in fish_rows.get((group, rod), set()):
                if level <= checkpoint.level_cap:
                    species_sources[species].add(f"{rod}_rod_fishing")
    return species_sources


@lru_cache(maxsize=1)
def map_fish_groups() -> dict[str, str]:
    groups: dict[str, str] = {}
    pattern = re.compile(r"^\s*map\s+([A-Za-z0-9_]+)\s*,.*,\s*(FISHGROUP_[A-Z0-9_]+)")
    for line in MAP_METADATA_PATH.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            label, group = match.groups()
            groups[map_label_to_constant(label)] = group
    return groups


@lru_cache(maxsize=1)
def fish_lines() -> tuple[str, ...]:
    return tuple((WILD_DIR / "fish.asm").read_text(encoding="utf-8").splitlines())


@lru_cache(maxsize=1)
def fish_species_by_group_and_rod() -> dict[tuple[str, str], set[tuple[str, int]]]:
    rows: dict[tuple[str, str], set[tuple[str, int]]] = defaultdict(set)
    time_groups = time_fish_groups()
    current_labels: list[tuple[str, str]] = []
    saw_entry = False
    label_pattern = re.compile(r"^\s*\.([A-Za-z0-9_]+)_(Old|Good|Super):")
    species_pattern = re.compile(r"^\s*db\s+[^,]+,\s*([A-Z0-9_]+)\s*,\s*(\d+)")
    time_pattern = re.compile(r"^\s*db\s+[^,]+,\s*time_group\s+(\d+)")
    for line in fish_lines():
        if line.startswith("TimeFishGroups:"):
            break
        label = label_pattern.match(line)
        if label:
            if saw_entry:
                current_labels = []
                saw_entry = False
            group_label, rod_label = label.groups()
            current_labels.append((fish_label_to_group(group_label), rod_label.lower()))
            continue
        if not current_labels:
            continue
        time_match = time_pattern.match(line)
        if time_match:
            for species, level in time_groups.get(int(time_match.group(1)), set()):
                for current in current_labels:
                    rows[current].add((species, level))
            saw_entry = True
            continue
        species_match = species_pattern.match(line)
        if species_match:
            species, raw_level = species_match.groups()
            for current in current_labels:
                rows[current].add((species, int(raw_level)))
            saw_entry = True
    return rows


@lru_cache(maxsize=1)
def time_fish_groups() -> dict[int, set[tuple[str, int]]]:
    groups: dict[int, set[tuple[str, int]]] = defaultdict(set)
    pattern = re.compile(
        r"^\s*db\s+([A-Z0-9_]+)\s*,\s*(\d+)\s*,\s*([A-Z0-9_]+)\s*,\s*(\d+)\s*;\s*(\d+)"
    )
    for line in fish_lines():
        match = pattern.match(line)
        if not match:
            continue
        day_species, day_level, night_species, night_level, index = match.groups()
        groups[int(index)].add((day_species, int(day_level)))
        groups[int(index)].add((night_species, int(night_level)))
    return groups


def gift_species_for_checkpoint(checkpoint: Checkpoint) -> dict[str, set[str]]:
    species_sources: dict[str, set[str]] = defaultdict(set)
    event_files = set(checkpoint.event_files)
    for species, level, source_file in givepoke_sources():
        if source_file in event_files and level <= checkpoint.level_cap:
            species_sources[species].add(f"gift_or_prize:{source_file}")
    return species_sources


@lru_cache(maxsize=1)
def map_script_sources() -> dict[str, tuple[tuple[str, ...], ...]]:
    rows: dict[str, list[tuple[str, ...]]] = {
        "givepoke": [],
        "static": [],
        "direct_tm": [],
        "mart": [],
    }
    givepoke_pattern = re.compile(r"\bgivepoke\s+([A-Z0-9_]+)\s*,\s*(\d+)")
    static_pattern = re.compile(r"\bloadwildmon\s+([A-Z0-9_]+)\s*,\s*(\d+)")
    direct_tm_pattern = re.compile(r"\b(?:verbosegiveitem|giveitem|itemball)\s+(TM_[A-Z0-9_]+)")
    mart_pattern = re.compile(r"\bpokemart\s+MARTTYPE_[A-Z0-9_]+,\s*(MART_[A-Z0-9_]+)")
    for path in MAPS_DIR.glob("*.asm"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if match := givepoke_pattern.search(line):
                species, level = match.groups()
                rows["givepoke"].append((species, level, path.name))
            if match := static_pattern.search(line):
                species, level = match.groups()
                rows["static"].append((species, level, path.name))
            if match := direct_tm_pattern.search(line):
                rows["direct_tm"].append((match.group(1), path.name))
            if match := mart_pattern.search(line):
                rows["mart"].append((match.group(1), path.name))
    return {key: tuple(value) for key, value in rows.items()}


@lru_cache(maxsize=1)
def givepoke_sources() -> tuple[tuple[str, int, str], ...]:
    return tuple(
        (species, int(level), source_file)
        for species, level, source_file in map_script_sources()["givepoke"]
    )


def static_species_for_checkpoint(checkpoint: Checkpoint) -> dict[str, set[str]]:
    species_sources: dict[str, set[str]] = defaultdict(set)
    static_files = set(checkpoint.static_files)
    for species, level, source_file in static_encounter_sources():
        if source_file in static_files and level <= checkpoint.level_cap:
            species_sources[species].add(f"static_encounter:{source_file}")
    return species_sources


@lru_cache(maxsize=1)
def static_encounter_sources() -> tuple[tuple[str, int, str], ...]:
    return tuple(
        (species, int(level), source_file)
        for species, level, source_file in map_script_sources()["static"]
    )


@lru_cache(maxsize=1)
def direct_tm_sources() -> dict[str, list[str]]:
    tm_items = tm_item_moves()
    sources: dict[str, list[str]] = defaultdict(list)
    for tm_item, source_file in map_script_sources()["direct_tm"]:
        move = tm_items.get(tm_item)
        if move is not None:
            sources[move].append(source_file)
    for move, source_files in mart_tm_sources().items():
        sources[move].extend(source_files)
    return {move: sorted(set(files)) for move, files in sources.items()}


@lru_cache(maxsize=1)
def mart_tm_sources() -> dict[str, list[str]]:
    tm_items = tm_item_moves()
    mart_labels = mart_labels_by_constant()
    mart_tms = tm_items_by_mart_label()
    sources: dict[str, list[str]] = defaultdict(list)
    for mart_constant, source_file in map_script_sources()["mart"]:
        label = mart_labels.get(mart_constant)
        if label is None:
            continue
        for tm_item in mart_tms.get(label, set()):
            move = tm_items.get(tm_item)
            if move is not None:
                sources[move].append(source_file)
    return {move: sorted(set(files)) for move, files in sources.items()}


@lru_cache(maxsize=1)
def mart_labels_by_constant() -> dict[str, str]:
    constants = mart_constants()
    labels: list[str] = []
    in_table = False
    for line in MARTS_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("Marts:"):
            in_table = True
            continue
        if not in_table:
            continue
        if "assert_table_length NUM_MARTS" in line:
            break
        match = re.match(r"\s*dw\s+(Mart[A-Za-z0-9_]+)", line)
        if match:
            labels.append(match.group(1))
    return dict(zip(constants, labels, strict=True))


@lru_cache(maxsize=1)
def mart_constants() -> tuple[str, ...]:
    constants: list[str] = []
    pattern = re.compile(r"^\s*const\s+(MART_[A-Z0-9_]+)")
    for line in MART_CONSTANTS_PATH.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            constants.append(match.group(1))
    return tuple(constants)


@lru_cache(maxsize=1)
def tm_items_by_mart_label() -> dict[str, set[str]]:
    rows: dict[str, set[str]] = defaultdict(set)
    current_label: str | None = None
    label_pattern = re.compile(r"^(Mart[A-Za-z0-9_]+):")
    tm_pattern = re.compile(r"^\s*db\s+(TM_[A-Z0-9_]+)\b")
    for line in MARTS_PATH.read_text(encoding="utf-8").splitlines():
        label = label_pattern.match(line)
        if label:
            current_label = label.group(1)
            continue
        if current_label is None:
            continue
        tm = tm_pattern.match(line)
        if tm:
            rows[current_label].add(tm.group(1))
    return rows


def direct_tm_moves_for_checkpoint(checkpoint: Checkpoint) -> set[str]:
    files = set(checkpoint.direct_tm_files)
    if "ALL" in files:
        return set(direct_tm_sources())
    return {
        move
        for move, source_files in direct_tm_sources().items()
        if any(path in files for path in source_files)
    }


@lru_cache(maxsize=1)
def tm_item_moves() -> dict[str, str]:
    moves: dict[str, str] = {}
    pattern = re.compile(r"^\s*add_tm\s+([A-Z0-9_]+)")
    tm_number = 1
    for line in ITEM_CONSTANTS_PATH.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            move = match.group(1)
            moves[f"TM_{move}"] = move
            tm_number += 1
    return moves


@lru_cache(maxsize=1)
def tmhm_learnsets() -> dict[str, set[str]]:
    learnsets_by_species: dict[str, set[str]] = {}
    species_pattern = re.compile(r"^\s*db\s+([A-Z0-9_]+)\s*;")
    tmhm_pattern = re.compile(r"^\s*tmhm(?:\s+(.*))?$")
    for path in BASE_STATS_DIR.glob("*.asm"):
        species: str | None = None
        moves: set[str] = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            if species is None:
                match = species_pattern.match(line)
                if match:
                    species = match.group(1)
            tmhm = tmhm_pattern.match(line.strip())
            if tmhm:
                raw_moves = tmhm.group(1) or ""
                moves.update(move.strip() for move in raw_moves.split(",") if move.strip())
        if species is not None:
            learnsets_by_species[species] = moves
    return learnsets_by_species


@lru_cache(maxsize=1)
def learnsets() -> dict[str, list[tuple[int, str]]]:
    pointers = evos_pointer_species()
    result: dict[str, list[tuple[int, str]]] = defaultdict(list)
    current_species: str | None = None
    in_moves = False
    label_pattern = re.compile(r"^([A-Za-z0-9_]+)EvosAttacks:")
    move_pattern = re.compile(r"^\s*db\s+(\d+)\s*,\s*([A-Z0-9_]+)")
    for line in EVOS_ATTACKS_PATH.read_text(encoding="utf-8").splitlines():
        label = label_pattern.match(line)
        if label:
            current_species = pointers.get(label.group(1))
            in_moves = False
            continue
        if current_species is None:
            continue
        if "db 0 ; no more evolutions" in line:
            in_moves = True
            continue
        if "db 0 ; no more level-up moves" in line:
            current_species = None
            in_moves = False
            continue
        if not in_moves:
            continue
        move = move_pattern.match(line)
        if move:
            result[current_species].append((int(move.group(1)), move.group(2)))
    return {species: rows for species, rows in result.items()}


@lru_cache(maxsize=1)
def evolutions() -> dict[str, list[tuple[str, int, str]]]:
    pointers = evos_pointer_species()
    result: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    current_species: str | None = None
    label_pattern = re.compile(r"^([A-Za-z0-9_]+)EvosAttacks:")
    evo_pattern = re.compile(r"^\s*db\s+(EVOLVE_[A-Z_]+)\s*,\s*([A-Z0-9_]+|-?\d+)\s*,\s*([A-Z0-9_]+)")
    for line in EVOS_ATTACKS_PATH.read_text(encoding="utf-8").splitlines():
        label = label_pattern.match(line)
        if label:
            current_species = pointers.get(label.group(1))
            continue
        if current_species is None:
            continue
        if "db 0 ; no more evolutions" in line:
            current_species = None
            continue
        evo = evo_pattern.match(line)
        if evo:
            method, raw_level, target = evo.groups()
            level = int(raw_level) if raw_level.isdigit() else 101
            result[current_species].append((method, level, target))
    return result


def legal_predecessors(species: str, level_cap: int) -> set[str]:
    predecessors: set[str] = set()
    changed = True
    while changed:
        changed = False
        for source, rows in evolutions().items():
            for method, level, target in rows:
                if target == species or target in predecessors:
                    if method == "EVOLVE_LEVEL" and level <= level_cap and source not in predecessors:
                        predecessors.add(source)
                        changed = True
    return predecessors


@lru_cache(maxsize=1)
def evos_pointer_species() -> dict[str, str]:
    species = pokemon_constants()
    labels: list[str] = []
    pattern = re.compile(r"^\s*dw\s+([A-Za-z0-9_]+)EvosAttacks")
    for line in EVOS_POINTERS_PATH.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            labels.append(match.group(1))
    return {label: species[index] for index, label in enumerate(labels) if index < len(species)}


@lru_cache(maxsize=1)
def pokemon_constants() -> list[str]:
    constants: list[str] = []
    pattern = re.compile(r"^\s*const\s+([A-Z0-9_]+)\s*;")
    for line in POKEMON_CONSTANTS_PATH.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            name = match.group(1)
            if name in {"EGG"}:
                break
            constants.append(name)
    return constants


def normalize_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def map_label_to_constant(value: str) -> str:
    text = camel_to_constant(value)
    text = re.sub(r"_B_(\d)_F", r"_B\1F", text)
    text = re.sub(r"_(\d)_F", r"_\1F", text)
    return text


def fish_label_to_group(value: str) -> str:
    return "FISHGROUP_" + "_".join(camel_to_constant(part) for part in value.split("_"))


def camel_to_constant(value: str) -> str:
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", value)
    text = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", text)
    text = re.sub(r"(?<=[A-Za-z])(?=\d)", "_", text)
    text = re.sub(r"(?<=\d)(?=[A-Za-z])", "_", text)
    return text.upper()


def normalize_species_constant(value: object) -> str:
    if not isinstance(value, str) or not value:
        return ""
    text = value.upper().replace(".", "").replace("'", "").replace(" ", "_").replace("-", "_")
    aliases = {
        "MR_MIME": "MR__MIME",
        "FARFETCHD": "FARFETCH_D",
        "HO_OH": "HO_OH",
    }
    return aliases.get(text, text)


def normalize_move_constant(value: object) -> str:
    if not isinstance(value, str) or not value:
        return ""
    text = value.upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "PSYCHIC": "PSYCHIC_M",
        "THUNDERPUNCH": "THUNDERPUNCH",
        "DOUBLESLAP": "DOUBLESLAP",
    }
    return aliases.get(text, text)


def display_species(species: str) -> str:
    special = {
        "MR__MIME": "Mr. Mime",
        "FARFETCH_D": "Farfetch D",
        "HO_OH": "Ho Oh",
        "NIDORAN_M": "Nidoran M",
        "NIDORAN_F": "Nidoran F",
    }
    if species in special:
        return special[species]
    return species.replace("_", " ").title()


def parse_percent(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    match = re.match(r"^(\d+)%$", value.strip())
    if not match:
        return None
    return int(match.group(1))


def immediacy_rank(value: str) -> int:
    return {"active": 0, "switch": 1}.get(value, 9)


def switch_fit_rank(value: object) -> int:
    return {
        None: 0,
        "reasonable": 0,
        "unknown": 1,
        "risky": 2,
        "bad": 3,
    }.get(value, 9)
