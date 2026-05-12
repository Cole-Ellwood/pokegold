from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from tools.audit.trainer_parties import TrainerPartyEntry, parse_parties

from .data import ROOT


PARTIES_PATH = ROOT / "data" / "trainers" / "parties.asm"
LEADER_GROUP_OVERRIDES = {
    "Champion Lance": "ChampionGroup",
}


def group_name_for_leader(leader: str) -> str:
    if leader in LEADER_GROUP_OVERRIDES:
        return LEADER_GROUP_OVERRIDES[leader]
    return f"{''.join(character for character in leader if character.isalnum())}Group"


@lru_cache(maxsize=1)
def parsed_parties(path: str = str(PARTIES_PATH)) -> tuple[TrainerPartyEntry, ...]:
    return tuple(parse_parties(Path(path)))


def parties_for_group(group: str) -> list[TrainerPartyEntry]:
    return [entry for entry in parsed_parties() if entry.group == group]


def party_for_group_index(group: str, index: int) -> TrainerPartyEntry | None:
    for entry in parties_for_group(group):
        if entry.index == index:
            return entry
    return None


def party_anchor_for_fixture(fixture: dict[str, Any]) -> tuple[str, int | None, str]:
    explicit_group = fixture.get("boss_party_group") or fixture.get("trainer_group")
    group = str(explicit_group or group_name_for_leader(str(fixture.get("leader", ""))))
    explicit_index = fixture.get("boss_party_index", fixture.get("trainer_index"))
    if explicit_index is not None:
        try:
            return group, int(explicit_index), "fixture"
        except (TypeError, ValueError):
            return group, None, "invalid_fixture_index"
    parties = parties_for_group(group)
    if len(parties) == 1:
        return group, parties[0].index, "unique_group"
    return group, None, "ambiguous_group"


def party_for_fixture(fixture: dict[str, Any]) -> TrainerPartyEntry | None:
    group, index, _anchor = party_anchor_for_fixture(fixture)
    if index is None:
        return None
    return party_for_group_index(group, index)


def display_token(value: str) -> str:
    if not value:
        return ""
    return " ".join(value.replace("_", " ").title().split())


def species_key(value: str) -> str:
    return "".join(character for character in value.upper() if character.isalnum())


def boss_bench_states(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    state = fixture.get("state", {})
    boss = state.get("boss", {}) if isinstance(state.get("boss"), dict) else {}
    bench_state = boss.get("bench_state", [])
    if not isinstance(bench_state, list):
        return []
    return [row for row in bench_state if isinstance(row, dict)]


def pop_bench_state(
    bench_states: list[dict[str, Any]],
    species: str,
) -> dict[str, Any]:
    key = species_key(species)
    for index, row in enumerate(bench_states):
        if species_key(str(row.get("species", ""))) == key:
            return bench_states.pop(index)
    return {}


def pop_source_mon(
    source_mons: list[Any],
    species: str,
) -> Any | None:
    key = species_key(species)
    for index, mon in enumerate(source_mons):
        if species_key(mon.species) == key:
            return source_mons.pop(index)
    return None


def source_moves(mon: Any | None) -> list[str]:
    if mon is None:
        return []
    return [display_token(move) for move in mon.moves if move != "NO_MOVE"]


def source_item(mon: Any | None) -> str:
    if mon is None or not mon.item:
        return "none"
    return display_token(mon.item)


def source_reference(mon: Any | None) -> str:
    if mon is None:
        return "fixture state"
    return f"data/trainers/parties.asm:{mon.line_no}"


def member_species(member: Any) -> str:
    if isinstance(member, dict):
        return str(member.get("species", ""))
    return str(member)


def party_hash(party: TrainerPartyEntry | None) -> str | None:
    if party is None:
        return None
    payload = [
        {
            "level": mon.level,
            "species": mon.species,
            "item": mon.item,
            "moves": list(mon.moves),
        }
        for mon in party.mons
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def boss_team_source_for_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    group, index, anchor = party_anchor_for_fixture(fixture)
    party = party_for_fixture(fixture)
    return {
        "group": group,
        "index": index,
        "anchor": anchor,
        "exact": party is not None and anchor in {"fixture", "unique_group"},
        "hash": party_hash(party),
        "path": "data/trainers/parties.asm",
        "line": party.line_no if party is not None else None,
    }


def boss_team_for_fixture(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    state = fixture.get("state", {})
    boss = state.get("boss", {}) if isinstance(state.get("boss"), dict) else {}
    active = boss.get("active", {}) if isinstance(boss.get("active"), dict) else {}
    party = party_for_fixture(fixture)
    source_mons = list(party.mons) if party is not None else []

    bench_states = boss_bench_states(fixture)
    rows: list[dict[str, Any]] = []

    active_species = str(active.get("species", ""))
    if active_species:
        active_mon = pop_source_mon(source_mons, active_species)
        moves = source_moves(active_mon) or list(active.get("revealed_moves", []))
        rows.append(
            {
                "species": active_species,
                "level": active.get(
                    "level",
                    active_mon.level if active_mon is not None else "not captured",
                ),
                "hp": active.get("hp", "not captured"),
                "status": active.get("status", "not captured"),
                "item": active.get("item") or source_item(active_mon),
                "moves": moves,
                "role": active.get("role", "active"),
                "active": True,
                "source": source_reference(active_mon),
            }
        )

    bench = boss.get("bench", [])
    if not isinstance(bench, list):
        return rows

    for member in bench:
        species = member_species(member)
        source_mon = pop_source_mon(source_mons, species)
        bench_state = pop_bench_state(bench_states, species)
        level = source_mon.level if source_mon is not None else "not captured"
        member_moves = member.get("moves", []) if isinstance(member, dict) else []
        moves = source_moves(source_mon) or list(member_moves)
        if isinstance(member, dict) and member.get("level") is not None:
            level = member["level"]
        rows.append(
            {
                "species": species,
                "level": level,
                "hp": bench_state.get("hp", "not captured"),
                "status": bench_state.get("status", "not captured"),
                "item": source_item(source_mon),
                "moves": moves,
                "role": "bench",
                "active": False,
                "source": source_reference(source_mon),
            }
        )
    return rows


def attach_boss_teams(fixtures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for fixture in fixtures:
        enriched = dict(fixture)
        enriched["boss_team"] = boss_team_for_fixture(fixture)
        enriched["boss_team_source"] = boss_team_source_for_fixture(fixture)
        output.append(enriched)
    return output
