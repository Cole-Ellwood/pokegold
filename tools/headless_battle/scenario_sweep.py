"""Phase 3 board sweep generator.

Per ``docs/headless_batch_validation_implementation.md`` §5 Phase 3.

Generates a sweep of ``family=switch_sack`` scenarios for the batch
materializer by combining:

- a real trainer roster parsed from ``data/trainers/parties.asm``
- one or more caller-supplied player species
- HP fractions (e.g. 1.0 / 0.6 / 0.3 — full / mid / low)
- player and enemy statuses from the override-supported subset
- weather toggles
- optional held items

Each combination becomes one BattleState dict, fed through
``headless_to_switch_sack_scenario(state, accept_overrides=True)`` to
produce a runnable scenario. The output is a JSONL file consumable by
``python -m tools.headless_battle.batch_switch --scenarios PATH``.

Out of scope this slice: stat-stage / substitute / spike-layer
variations (those need slice C-* extensions before the exporter will
accept them); multi-trainer parallelism (Phase 4 covers that via fresh
manifest captures).
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from tools.damage_debugger import tables
from tools.headless_battle.rom_switch_scenario_export import (
    headless_to_switch_sack_scenario,
)
from tools.headless_battle.simulator import source_species_row


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PARTIES_PATH = ROOT / "data" / "trainers" / "parties.asm"
SUPPORTED_STATUSES = ("none", "burn", "poison", "paralyze", "sleep", "toxic")
WEATHER_DURATIONS = {"rain": 5, "sun": 5, "sandstorm": 5}
DEFAULT_LEVEL = 50
DEFAULT_HP_FRACTIONS = (1.0, 0.6, 0.3)
DEFAULT_STATUSES = ("none",)
DEFAULT_WEATHERS = ("none",)


class ScenarioSweepError(ValueError):
    """Raised when a sweep input is malformed or a trainer cannot be parsed."""


@dataclass(frozen=True)
class TrainerMon:
    level: int
    species: str
    item: Optional[str] = None
    moves: tuple[str, ...] = ()


@dataclass(frozen=True)
class TrainerRoster:
    name: str
    trainer_type: str
    mons: tuple[TrainerMon, ...]

    def species_names(self) -> tuple[str, ...]:
        return tuple(mon.species for mon in self.mons)


_GROUP_LINE = re.compile(r"^([A-Za-z0-9_]+)Group:\s*$")
_HEADER_LINE = re.compile(
    r'^\s*db\s+"([^"@]+)@"\s*,\s*(TRAINERTYPE_[A-Z_]+)\s*$'
)
_DB_LINE = re.compile(r"^\s*db\s+(.+?)\s*(?:;.*)?$")


def _strip_comment(text: str) -> str:
    return text.split(";", 1)[0].rstrip()


def parse_trainer_roster(
    trainer_class: str,
    *,
    parties_path: Path = DEFAULT_PARTIES_PATH,
) -> TrainerRoster:
    """Extract the first trainer roster matching ``trainer_class``.

    ``trainer_class`` is the name written in the db header (e.g. "JASMINE",
    "MORTY", "WILL"). Comparison is case-insensitive. Returns the first
    entry in the group; multi-trainer groups (e.g. shared youngster
    rosters) require explicit indexing in a future revision.
    """
    needle = trainer_class.strip().upper()
    if not parties_path.exists():
        raise ScenarioSweepError(f"missing parties file: {parties_path}")
    lines = parties_path.read_text(encoding="utf-8").splitlines()

    in_target_group = False
    in_target_trainer = False
    trainer_type: Optional[str] = None
    mons: list[TrainerMon] = []
    current_group = ""

    for raw in lines:
        group_match = _GROUP_LINE.match(raw)
        if group_match:
            current_group = group_match.group(1)
            in_target_group = current_group.upper().startswith(needle)
            in_target_trainer = False
            continue
        if not in_target_group:
            continue
        line = _strip_comment(raw)
        if not line:
            continue
        header = _HEADER_LINE.match(raw)
        if header:
            name = header.group(1).strip().upper()
            if name == needle:
                trainer_type = header.group(2)
                in_target_trainer = True
                mons = []
            else:
                in_target_trainer = False
            continue
        if not in_target_trainer:
            continue
        if line.endswith("-1") or line.endswith("-1 ;") or line == "db -1":
            return TrainerRoster(
                name=needle,
                trainer_type=trainer_type or "TRAINERTYPE_NORMAL",
                mons=tuple(mons),
            )
        match = _DB_LINE.match(raw)
        if not match:
            continue
        operands = [token.strip() for token in match.group(1).split(",")]
        if not operands or operands == ["-1"]:
            if mons:
                return TrainerRoster(
                    name=needle,
                    trainer_type=trainer_type or "TRAINERTYPE_NORMAL",
                    mons=tuple(mons),
                )
            continue
        try:
            level = int(operands[0])
        except ValueError:
            continue
        species = operands[1]
        item: Optional[str] = None
        moves: tuple[str, ...] = ()
        if trainer_type == "TRAINERTYPE_NORMAL":
            pass
        elif trainer_type == "TRAINERTYPE_MOVES":
            moves = tuple(operands[2:6])
        elif trainer_type == "TRAINERTYPE_ITEM":
            if len(operands) >= 3:
                item = operands[2]
        elif trainer_type == "TRAINERTYPE_ITEM_MOVES":
            if len(operands) >= 3:
                item = operands[2]
            moves = tuple(operands[3:7])
        mons.append(TrainerMon(level=level, species=species, item=item, moves=moves))

    raise ScenarioSweepError(
        f"trainer {trainer_class!r} not found in {parties_path} "
        "(must match the name in 'db \"NAME@\"' header)"
    )


def _resolve_status(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in SUPPORTED_STATUSES:
        raise ScenarioSweepError(
            f"status {value!r} not in override-supported subset {SUPPORTED_STATUSES}; "
            "stat-stage / substitute / nightmare / confused need future slice C-* work"
        )
    return normalized


def _resolve_weather(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in {"none", "rain", "sun", "sandstorm"}:
        raise ScenarioSweepError(
            f"weather {value!r} not in {{none, rain, sun, sandstorm}}"
        )
    return normalized


def _resolve_item(value: Optional[str]) -> int:
    if value is None or value == "" or value.upper() == "NO_ITEM":
        return 0
    return tables.canonical_item_constant(value)


def _stats_dict(species_row: "tables.BaseStatsRow", level: int) -> dict[str, int]:
    iv, ev = tables.TRAINER_IV_STATEEXP
    return {
        "attack": tables.compute_stat(species_row.atk, level, iv, ev, is_hp=False),
        "defense": tables.compute_stat(species_row.def_, level, iv, ev, is_hp=False),
        "speed": tables.compute_stat(species_row.spe, level, iv, ev, is_hp=False),
        "sp_attack": tables.compute_stat(species_row.sat, level, iv, ev, is_hp=False),
        "sp_defense": tables.compute_stat(species_row.sdf, level, iv, ev, is_hp=False),
    }


def _max_hp(species_row: "tables.BaseStatsRow", level: int) -> int:
    iv, ev = tables.TRAINER_IV_STATEEXP
    return tables.compute_hp(species_row.hp, level, iv, ev)


def _mon_dict(
    species_name: str,
    *,
    level: int = DEFAULT_LEVEL,
    hp_fraction: float = 1.0,
    status: str = "none",
    item: int = 0,
    toxic_count: int = 0,
    sleep_turns: int = 0,
) -> dict:
    species_row = source_species_row(species_name, "scenario_sweep")
    if species_row is None:
        raise ScenarioSweepError(
            f"unknown species {species_name!r} (no entry in data/pokemon/base_stats/)"
        )
    max_hp = _max_hp(species_row, level)
    hp = max(1, int(round(max_hp * hp_fraction)))
    if hp > max_hp:
        hp = max_hp
    mon: dict = {
        "species": species_row.species,
        "level": level,
        "types": [species_row.type_a, species_row.type_b],
        "hp": hp,
        "max_hp": max_hp,
        "stats": _stats_dict(species_row, level),
        "moves": [{"name": "TACKLE"}],  # placeholder; exporter doesn't read moves
        "status": status,
        "item": item,
    }
    if status == "toxic":
        mon["toxic_count"] = max(1, toxic_count or 1)
    if status == "sleep":
        # sleep_turns goes into the materializer's status byte; default to 2
        # so the byte is observable (0 would be indistinguishable from "no sleep").
        mon["sleep_turns"] = max(1, sleep_turns or 2)
    return mon


def _scenario_id(
    *,
    prefix: str,
    trainer: str,
    enemy_active: str,
    enemy_bench: str,
    player: str,
    player_hp_fraction: float,
    enemy_hp_fraction: float,
    player_status: str,
    enemy_status: str,
    weather: str,
) -> str:
    return (
        f"{prefix}_{trainer.lower()}"
        f"_act{enemy_active.lower()}_bn{enemy_bench.lower()}"
        f"_vs_{player.lower()}_phh{int(round(player_hp_fraction * 100))}"
        f"_eh{int(round(enemy_hp_fraction * 100))}"
        f"_ps{player_status}_es{enemy_status}_we{weather}"
    )


@dataclass(frozen=True)
class SweepOptions:
    trainer_class: str
    player_species: tuple[str, ...]
    enemy_active_species: tuple[str, ...] = ()
    enemy_bench_species: tuple[str, ...] = ()
    player_hp_fractions: tuple[float, ...] = DEFAULT_HP_FRACTIONS
    enemy_hp_fractions: tuple[float, ...] = DEFAULT_HP_FRACTIONS
    player_statuses: tuple[str, ...] = DEFAULT_STATUSES
    enemy_statuses: tuple[str, ...] = DEFAULT_STATUSES
    weathers: tuple[str, ...] = DEFAULT_WEATHERS
    player_items: tuple[str, ...] = ("NO_ITEM",)
    enemy_items: tuple[str, ...] = ("NO_ITEM",)
    level: int = DEFAULT_LEVEL
    tier: str = "late"
    scenario_id_prefix: str = "sweep"
    parties_path: Path = DEFAULT_PARTIES_PATH
    limit: int = 0


def sweep_against_trainer(opts: SweepOptions) -> list[dict]:
    """Return a list of ``family=switch_sack`` scenario dicts.

    The cartesian product of player species × player HP fraction × player
    status × player item × enemy_active species × enemy_bench species ×
    enemy HP fraction × enemy status × enemy item × weather is taken and
    each combo is run through the exporter. Combos rejected by the
    exporter (e.g. fainted bench) are skipped with a warning attached to
    the returned list as an ``__errors__`` entry on the first scenario;
    the function does NOT silently swallow exporter rejections.
    """
    roster = parse_trainer_roster(opts.trainer_class, parties_path=opts.parties_path)
    if not roster.mons:
        raise ScenarioSweepError(
            f"trainer {opts.trainer_class} has an empty roster"
        )
    enemy_active = opts.enemy_active_species or (roster.mons[0].species,)
    if len(roster.mons) >= 2:
        default_bench = (roster.mons[1].species,)
    else:
        default_bench = (roster.mons[0].species,)
    enemy_bench = opts.enemy_bench_species or default_bench

    statuses_player = tuple(_resolve_status(s) for s in opts.player_statuses)
    statuses_enemy = tuple(_resolve_status(s) for s in opts.enemy_statuses)
    weathers = tuple(_resolve_weather(w) for w in opts.weathers)
    player_items = tuple(_resolve_item(i) for i in opts.player_items)
    enemy_items = tuple(_resolve_item(i) for i in opts.enemy_items)

    scenarios: list[dict] = []
    errors: list[str] = []
    combos = itertools.product(
        opts.player_species,
        opts.player_hp_fractions,
        statuses_player,
        player_items,
        enemy_active,
        enemy_bench,
        opts.enemy_hp_fractions,
        statuses_enemy,
        enemy_items,
        weathers,
    )
    for (
        player_species,
        player_hp_fraction,
        player_status,
        player_item,
        enemy_active_species,
        enemy_bench_species,
        enemy_hp_fraction,
        enemy_status,
        enemy_item,
        weather,
    ) in combos:
        if enemy_active_species == enemy_bench_species:
            # Bench[0] should be a different species than the active mon
            # otherwise it cannot serve as a switch target.
            continue
        weather_count = WEATHER_DURATIONS.get(weather, 0)
        state: dict = {
            "weather": weather,
            "weather_count": weather_count,
            "turn": 1,
            "player": _mon_dict(
                player_species,
                level=opts.level,
                hp_fraction=player_hp_fraction,
                status=player_status,
                item=player_item,
            ),
            "enemy": _mon_dict(
                enemy_active_species,
                level=opts.level,
                hp_fraction=enemy_hp_fraction,
                status=enemy_status,
                item=enemy_item,
            ),
        }
        # The materializer fixes bench[0] level/HP; we still need to populate
        # something the exporter accepts. Full-HP bench mon is the cleanest
        # default — sweeping bench HP would require slice C-bench-hp future work.
        state["enemy"]["bench"] = [
            _mon_dict(enemy_bench_species, level=opts.level, hp_fraction=1.0)
        ]
        scenario_id = _scenario_id(
            prefix=opts.scenario_id_prefix,
            trainer=opts.trainer_class,
            enemy_active=enemy_active_species,
            enemy_bench=enemy_bench_species,
            player=player_species,
            player_hp_fraction=player_hp_fraction,
            enemy_hp_fraction=enemy_hp_fraction,
            player_status=player_status,
            enemy_status=enemy_status,
            weather=weather,
        )
        try:
            scenario = headless_to_switch_sack_scenario(
                state,
                scenario_id=scenario_id,
                tier=opts.tier,
                accept_overrides=True,
            )
        except Exception as exc:
            errors.append(f"{scenario_id}: {exc}")
            continue
        scenarios.append(scenario)
        if opts.limit > 0 and len(scenarios) >= opts.limit:
            break

    if not scenarios:
        if errors:
            raise ScenarioSweepError(
                "all combos rejected by the exporter; reasons: " + "; ".join(errors[:5])
            )
        raise ScenarioSweepError(
            "all combos skipped (likely enemy_active == enemy_bench for every "
            "product entry); supply distinct enemy_active and enemy_bench species"
        )
    if errors:
        # Surface rejection reasons on the result; callers can choose to
        # error-out on any rejection (CLI does so behind --strict).
        scenarios[0].setdefault("sweep_errors", []).extend(errors)
    return scenarios


def write_sweep_jsonl(scenarios: Iterable[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for scenario in scenarios:
            f.write(json.dumps(scenario, ensure_ascii=False) + "\n")


def format_sweep_summary(roster: TrainerRoster, scenarios: list[dict]) -> str:
    enemy_active_set = {s.get("overrides", {}).get("enemy_species") for s in scenarios}
    enemy_bench_set = {s.get("overrides", {}).get("enemy_bench_species") for s in scenarios}
    player_set = {s.get("overrides", {}).get("player_species") for s in scenarios}
    lines = [
        f"Headless battle scenario sweep against {roster.name} ({roster.trainer_type})",
        f"trainer roster: {', '.join(roster.species_names())}",
        f"scenarios emitted: {len(scenarios)}",
        (
            f"unique player_species={len(player_set)} "
            f"unique enemy_active={len(enemy_active_set)} "
            f"unique enemy_bench={len(enemy_bench_set)}"
        ),
    ]
    errors_first = scenarios[0].get("sweep_errors") if scenarios else None
    if errors_first:
        lines.append("")
        lines.append("Combo rejections during sweep:")
        for err in errors_first[:10]:
            lines.append(f"  - {err}")
        if len(errors_first) > 10:
            lines.append(f"  ... ({len(errors_first) - 10} more rejections truncated)")
    return "\n".join(lines)


def _split_csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _split_floats(value: str | None) -> tuple[float, ...]:
    if not value:
        return ()
    out: list[float] = []
    for part in value.split(","):
        if not part.strip():
            continue
        try:
            v = float(part.strip())
        except ValueError as exc:
            raise ScenarioSweepError(f"--hp-fractions value {part!r} not a number") from exc
        if not 0.0 < v <= 1.0:
            raise ScenarioSweepError(
                f"--hp-fractions value {v} must be in (0.0, 1.0]"
            )
        out.append(v)
    return tuple(out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.headless_battle.scenario_sweep",
        description=(
            "Generate a sweep of family=switch_sack scenarios from a real trainer "
            "roster crossed with caller-supplied player species + HP / status / "
            "weather / item variations. Output is JSONL consumable by "
            "tools.headless_battle.batch_switch."
        ),
    )
    parser.add_argument(
        "--trainer",
        required=True,
        help="trainer name as written in parties.asm (e.g. JASMINE, MORTY)",
    )
    parser.add_argument(
        "--player",
        required=True,
        help="comma-separated player species names (e.g. CYNDAQUIL,HAUNTER)",
    )
    parser.add_argument(
        "--enemy-active",
        default="",
        help="comma-separated enemy active species (default: trainer roster[0])",
    )
    parser.add_argument(
        "--enemy-bench",
        default="",
        help="comma-separated enemy bench[0] species (default: trainer roster[1])",
    )
    parser.add_argument(
        "--hp-fractions",
        default="1.0,0.6,0.3",
        help="comma-separated HP fractions applied to both sides; values in (0, 1]",
    )
    parser.add_argument(
        "--player-hp-fractions",
        default="",
        help="override player HP fractions; defaults to --hp-fractions",
    )
    parser.add_argument(
        "--enemy-hp-fractions",
        default="",
        help="override enemy HP fractions; defaults to --hp-fractions",
    )
    parser.add_argument(
        "--statuses",
        default="none",
        help=(
            "comma-separated statuses applied to both sides; subset of "
            f"{SUPPORTED_STATUSES}"
        ),
    )
    parser.add_argument("--player-statuses", default="")
    parser.add_argument("--enemy-statuses", default="")
    parser.add_argument(
        "--weathers",
        default="none",
        help="comma-separated weather toggles; subset of {none, rain, sun, sandstorm}",
    )
    parser.add_argument(
        "--player-items",
        default="NO_ITEM",
        help="comma-separated player item constants",
    )
    parser.add_argument(
        "--enemy-items",
        default="NO_ITEM",
        help="comma-separated enemy item constants",
    )
    parser.add_argument("--level", type=int, default=DEFAULT_LEVEL)
    parser.add_argument("--tier", default="late",
                        help="boss-AI tier label; one of {early, mid, late}")
    parser.add_argument("--scenario-id-prefix", default="sweep")
    parser.add_argument("--limit", type=int, default=0,
                        help="cap on scenarios emitted (0 = no cap)")
    parser.add_argument("--out", type=Path, default=None,
                        help="write scenarios as JSONL to this path")
    parser.add_argument("--json", action="store_true",
                        help="print scenarios as a JSON array on stdout")
    parser.add_argument("--strict", action="store_true",
                        help="exit nonzero on any combo rejection by the exporter")
    parser.add_argument(
        "--parties-path",
        type=Path,
        default=DEFAULT_PARTIES_PATH,
        help="path to data/trainers/parties.asm (default: repo path)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    player_species = _split_csv(args.player)
    if not player_species:
        parser.error("--player must list at least one species")
    hp_fractions = _split_floats(args.hp_fractions)
    if not hp_fractions:
        parser.error("--hp-fractions must yield at least one value")
    player_hp = _split_floats(args.player_hp_fractions) or hp_fractions
    enemy_hp = _split_floats(args.enemy_hp_fractions) or hp_fractions
    statuses = _split_csv(args.statuses) or DEFAULT_STATUSES
    player_statuses = _split_csv(args.player_statuses) or statuses
    enemy_statuses = _split_csv(args.enemy_statuses) or statuses
    weathers = _split_csv(args.weathers) or DEFAULT_WEATHERS
    opts = SweepOptions(
        trainer_class=args.trainer,
        player_species=player_species,
        enemy_active_species=_split_csv(args.enemy_active),
        enemy_bench_species=_split_csv(args.enemy_bench),
        player_hp_fractions=player_hp,
        enemy_hp_fractions=enemy_hp,
        player_statuses=player_statuses,
        enemy_statuses=enemy_statuses,
        weathers=weathers,
        player_items=_split_csv(args.player_items) or ("NO_ITEM",),
        enemy_items=_split_csv(args.enemy_items) or ("NO_ITEM",),
        level=args.level,
        tier=args.tier,
        scenario_id_prefix=args.scenario_id_prefix,
        parties_path=args.parties_path,
        limit=args.limit,
    )
    roster = parse_trainer_roster(opts.trainer_class, parties_path=opts.parties_path)
    scenarios = sweep_against_trainer(opts)
    if args.out:
        write_sweep_jsonl(scenarios, args.out)
    if args.json:
        print(json.dumps(scenarios, indent=2, sort_keys=True))
    else:
        print(format_sweep_summary(roster, scenarios))
        if args.out:
            print(f"wrote {args.out}")
    if args.strict and scenarios and scenarios[0].get("sweep_errors"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
