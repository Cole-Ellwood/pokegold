#!/usr/bin/env python3
"""Oracle-backed damage delta heatmap.

This is a gameplay-facing audit helper built on the damage debugger's Python
oracle. It enumerates learned damaging moves for selected Pokemon, compares a
neutral baseline against supported modifier variants, and renders the largest
damage deltas plus type-level summaries.
"""

from __future__ import annotations

import argparse
import heapq
import json
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.generate_balance_audit import (
    ROOT,
    BaseStats,
    Move,
    parse_base_stats,
    parse_evos_attacks,
    parse_evos_pointer_labels,
    parse_moves,
    parse_species_order,
    parse_type_categories,
    repo_text,
)
from tools.damage_debugger.oracle import (
    BUG,
    DARK,
    DRAGON,
    ELECTRIC,
    FIRE,
    FIGHTING,
    FLYING,
    GHOST,
    GRASS,
    GROUND,
    HELD_ASSAULT_VEST,
    HELD_CHOICE_BAND,
    HELD_CHOICE_SPECS,
    HELD_EVOLITE,
    HELD_NONE,
    ICE,
    NORMAL,
    POISON,
    PSYCHIC_TYPE,
    ROCK,
    STEEL,
    WATER,
    BattleInputs,
    WEATHER_RAIN,
    WEATHER_SUN,
    predict_damage,
)


SCHEMA = "damage-delta-heatmap.v1"
STAT_NAMES = ("HP", "Atk", "Def", "Spe", "SpA", "SpD")
DEFAULT_OUTPUT = ROOT / "audit" / "damage_debugger" / "damage_heatmap.md"

TYPE_IDS = {
    "NORMAL": NORMAL,
    "FIGHTING": FIGHTING,
    "FLYING": FLYING,
    "POISON": POISON,
    "GROUND": GROUND,
    "ROCK": ROCK,
    "BUG": BUG,
    "GHOST": GHOST,
    "STEEL": STEEL,
    "FIRE": FIRE,
    "WATER": WATER,
    "GRASS": GRASS,
    "ELECTRIC": ELECTRIC,
    "PSYCHIC_TYPE": PSYCHIC_TYPE,
    "ICE": ICE,
    "DRAGON": DRAGON,
    "DARK": DARK,
}

BADGE_TYPE_BOOSTS = (
    FLYING,
    BUG,
    NORMAL,
    GHOST,
    STEEL,
    FIGHTING,
    ICE,
    DRAGON,
    ROCK,
    WATER,
    ELECTRIC,
    GRASS,
    POISON,
    PSYCHIC_TYPE,
    FIRE,
    GROUND,
)


@dataclass(frozen=True)
class DataSet:
    base_stats: dict[str, BaseStats]
    moves: dict[str, Move]
    physical_types: set[str]
    special_types: set[str]
    evolutions: dict[str, tuple[str, ...]]
    level_moves: dict[str, tuple[tuple[int, str], ...]]


@dataclass(frozen=True)
class DeltaRow:
    attacker: str
    defender: str
    move: str
    level: int
    move_type: str
    category: str
    variant: str
    baseline: int
    damage: int
    delta: int
    pct: float


@dataclass(frozen=True)
class TypeSummary:
    move_type: str
    rows: int
    avg_abs_delta: float
    max_abs_delta: int


@dataclass(frozen=True)
class HeatmapReport:
    schema: str
    combo_count: int
    variant_rows: int
    truncated: bool
    levels: list[int]
    top_deltas: list[DeltaRow]
    type_summary: list[TypeSummary]

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "combo_count": self.combo_count,
            "variant_rows": self.variant_rows,
            "truncated": self.truncated,
            "levels": self.levels,
            "top_deltas": [asdict(row) for row in self.top_deltas],
            "type_summary": [asdict(row) for row in self.type_summary],
        }


def load_dataset() -> DataSet:
    base_stats = parse_base_stats()
    moves = parse_moves(repo_text("data/moves/moves.asm"))
    physical, special = parse_type_categories(repo_text("constants/type_constants.asm"))
    species_order = parse_species_order(repo_text("constants/pokemon_constants.asm"))
    labels = parse_evos_pointer_labels(repo_text("data/pokemon/evos_attacks_pointers.asm"))
    label_to_species = dict(zip(labels, species_order, strict=False))
    evolutions, level_moves = parse_evos_attacks(
        repo_text("data/pokemon/evos_attacks.asm"),
        label_to_species,
    )
    return DataSet(
        base_stats=base_stats,
        moves=moves,
        physical_types=physical,
        special_types=special,
        evolutions=evolutions,
        level_moves=level_moves,
    )


def _parse_csv(raw: str | None) -> list[str] | None:
    if raw is None or not raw.strip():
        return None
    return [part.strip().upper() for part in raw.split(",") if part.strip()]


def _parse_levels(raw: str) -> list[int]:
    levels: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        value = int(part)
        if value <= 0 or value > 100:
            raise ValueError(f"level {value} outside 1..100")
        levels.append(value)
    if not levels:
        raise ValueError("at least one level is required")
    return levels


def _resolve_names(kind: str, selected: list[str] | None, known: Iterable[str]) -> list[str]:
    known_set = set(known)
    if selected is None:
        return sorted(known_set)
    missing = [name for name in selected if name not in known_set]
    if missing:
        raise ValueError(f"unknown {kind}: {', '.join(missing)}")
    return selected


def _battle_stat(base: int, level: int) -> int:
    # Deterministic max-DV/no-stat-exp proxy. This is a heatmap, not a party
    # stat calculator; the report calls this out explicitly.
    return max(1, ((2 * base + 15) * level) // 100 + 5)


def _types_to_ids(types: tuple[str, str]) -> tuple[int, int]:
    return tuple(TYPE_IDS[name] for name in types)  # type: ignore[return-value]


def _move_category(move_type: str, physical_types: set[str], special_types: set[str]) -> str:
    if move_type in physical_types:
        return "physical"
    if move_type in special_types:
        return "special"
    raise ValueError(f"move type {move_type!r} is neither physical nor special")


def _learned_moves_for(
    dataset: DataSet,
    species: str,
    level: int,
    explicit_moves: set[str] | None,
) -> list[str]:
    if explicit_moves is not None:
        return sorted(explicit_moves)
    stats = dataset.base_stats[species]
    learned = {move for move_level, move in dataset.level_moves.get(species, ()) if move_level <= level}
    learned.update(stats.tms)
    return sorted(learned)


def _badge_bits_for(move_type_id: int) -> tuple[int, int]:
    if move_type_id not in BADGE_TYPE_BOOSTS:
        return 0, 0
    index = BADGE_TYPE_BOOSTS.index(move_type_id)
    if index < 8:
        return 1 << index, 0
    return 0, 1 << (index - 8)


def _base_inputs(
    *,
    attacker_stats: BaseStats,
    defender_stats: BaseStats,
    move: Move,
    level: int,
    category: str,
) -> BattleInputs:
    is_physical = category == "physical"
    atk_stat = attacker_stats.stats[1] if is_physical else attacker_stats.stats[4]
    def_stat = defender_stats.stats[2] if is_physical else defender_stats.stats[5]
    return BattleInputs(
        attacker_level=level,
        move_bp=move.power,
        move_type=TYPE_IDS[move.move_type],
        is_physical=is_physical,
        attacker_atk=_battle_stat(atk_stat, level),
        defender_def=_battle_stat(def_stat, level),
        attacker_types=_types_to_ids(attacker_stats.types),
        defender_types=_types_to_ids(defender_stats.types),
    )


def _variants(
    base: BattleInputs,
    *,
    move_type_name: str,
    category: str,
    defender_can_evolve: bool,
) -> list[tuple[str, BattleInputs]]:
    out = [("baseline", base)]
    if category == "physical":
        out.append(("choice_band", _replace(base, user_item=HELD_CHOICE_BAND)))
    else:
        out.append(("choice_specs", _replace(base, user_item=HELD_CHOICE_SPECS)))
        out.append(("assault_vest", _replace(base, opponent_item=HELD_ASSAULT_VEST)))
    if defender_can_evolve:
        out.append((
            "eviolite_defender",
            _replace(base, opponent_item=HELD_EVOLITE, can_evolve_defender=True),
        ))
    if move_type_name == "FIRE":
        out.append(("sun", _replace(base, weather=WEATHER_SUN)))
        out.append(("rain", _replace(base, weather=WEATHER_RAIN)))
    elif move_type_name == "WATER":
        out.append(("rain", _replace(base, weather=WEATHER_RAIN)))
        out.append(("sun", _replace(base, weather=WEATHER_SUN)))
    johto_badges, kanto_badges = _badge_bits_for(base.move_type)
    if johto_badges or kanto_badges:
        out.append((
            "matching_badge",
            _replace(base, johto_badges=johto_badges, kanto_badges=kanto_badges),
        ))
    return out


def _replace(inp: BattleInputs, **changes) -> BattleInputs:
    values = asdict(inp)
    values.update(changes)
    return BattleInputs(**values)


def collect_report(
    dataset: DataSet,
    *,
    attackers: list[str],
    defenders: list[str],
    moves: set[str] | None,
    levels: list[int],
    top: int,
    max_combos: int | None,
) -> HeatmapReport:
    top_heap: list[tuple[int, int, DeltaRow]] = []
    type_rows: dict[str, list[int]] = {}
    combo_count = 0
    variant_rows = 0
    truncated = False
    row_seq = 0

    for level in levels:
        for attacker in attackers:
            attacker_stats = dataset.base_stats[attacker]
            learned_moves = _learned_moves_for(dataset, attacker, level, moves)
            for move_name in learned_moves:
                move = dataset.moves.get(move_name)
                if move is None or not move.reliable_damage or move.move_type not in TYPE_IDS:
                    continue
                category = _move_category(move.move_type, dataset.physical_types, dataset.special_types)
                for defender in defenders:
                    if max_combos is not None and combo_count >= max_combos:
                        truncated = True
                        break
                    defender_stats = dataset.base_stats[defender]
                    base = _base_inputs(
                        attacker_stats=attacker_stats,
                        defender_stats=defender_stats,
                        move=move,
                        level=level,
                        category=category,
                    )
                    variant_inputs = _variants(
                        base,
                        move_type_name=move.move_type,
                        category=category,
                        defender_can_evolve=bool(dataset.evolutions.get(defender)),
                    )
                    baseline_damage = predict_damage(base)
                    combo_count += 1

                    for variant_name, inp in variant_inputs:
                        if variant_name == "baseline":
                            continue
                        damage = predict_damage(inp)
                        delta = damage - baseline_damage
                        pct = 0.0 if baseline_damage == 0 else (delta * 100.0 / baseline_damage)
                        row = DeltaRow(
                            attacker=attacker,
                            defender=defender,
                            move=move_name,
                            level=level,
                            move_type=move.move_type,
                            category=category,
                            variant=variant_name,
                            baseline=baseline_damage,
                            damage=damage,
                            delta=delta,
                            pct=round(pct, 1),
                        )
                        variant_rows += 1
                        type_rows.setdefault(move.move_type, []).append(abs(delta))
                        score = abs(delta)
                        heap_item = (score, row_seq, row)
                        row_seq += 1
                        if len(top_heap) < top:
                            heapq.heappush(top_heap, heap_item)
                        elif heap_item > top_heap[0]:
                            heapq.heapreplace(top_heap, heap_item)
                if truncated:
                    break
            if truncated:
                break
        if truncated:
            break

    top_rows = [
        item[2] for item in sorted(top_heap, key=lambda item: (item[0], item[1]), reverse=True)
    ]
    summaries = [
        TypeSummary(
            move_type=move_type,
            rows=len(deltas),
            avg_abs_delta=round(sum(deltas) / len(deltas), 2),
            max_abs_delta=max(deltas),
        )
        for move_type, deltas in sorted(type_rows.items())
        if deltas
    ]
    summaries.sort(key=lambda row: (row.max_abs_delta, row.avg_abs_delta, row.move_type), reverse=True)
    return HeatmapReport(
        schema=SCHEMA,
        combo_count=combo_count,
        variant_rows=variant_rows,
        truncated=truncated,
        levels=levels,
        top_deltas=top_rows,
        type_summary=summaries,
    )


def render_markdown(report: HeatmapReport) -> str:
    lines: list[str] = []
    lines.append("# Damage Delta Heatmap")
    lines.append("")
    lines.append("Generated from `tools/audit/balance_diff.py` using `tools.damage_debugger.oracle`.")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append(f"- Schema: `{report.schema}`")
    lines.append(f"- Levels: {', '.join(str(level) for level in report.levels)}")
    lines.append(f"- Base combinations scored: {report.combo_count}")
    lines.append(f"- Variant rows scored: {report.variant_rows}")
    lines.append(f"- Truncated by max-combo limit: {report.truncated}")
    lines.append("- Stats use a deterministic max-DV/no-stat-exp level proxy, not party data.")
    lines.append("- Variants compare against no item / no weather / no badge baseline.")
    lines.append("")
    lines.append("## Largest Deltas")
    lines.append("")
    lines.append("| Delta | Pct | Variant | Damage | Base | Level | Attacker | Defender | Move | Type | Cat |")
    lines.append("| ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- |")
    if not report.top_deltas:
        lines.append("| 0 | 0.0 | - | 0 | 0 | 0 | - | - | - | - | - |")
    for row in report.top_deltas:
        lines.append(
            f"| {row.delta:+d} | {row.pct:+.1f}% | `{row.variant}` | {row.damage} | "
            f"{row.baseline} | {row.level} | `{row.attacker}` | `{row.defender}` | "
            f"`{row.move}` | `{row.move_type}` | {row.category} |"
        )
    lines.append("")
    lines.append("## Type Summary")
    lines.append("")
    lines.append("| Move Type | Rows | Avg Abs Delta | Max Abs Delta |")
    lines.append("| --- | ---: | ---: | ---: |")
    for row in report.type_summary:
        lines.append(
            f"| `{row.move_type}` | {row.rows} | {row.avg_abs_delta:.2f} | {row.max_abs_delta} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_report(report: HeatmapReport, output: Path, json_output: Path | None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(report), encoding="utf-8")
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")


def self_test() -> int:
    dataset = load_dataset()
    report = collect_report(
        dataset,
        attackers=["CYNDAQUIL"],
        defenders=["PIDGEY"],
        moves={"EMBER", "TACKLE"},
        levels=[5],
        top=10,
        max_combos=None,
    )
    assert report.schema == SCHEMA
    assert report.combo_count >= 1
    assert report.top_deltas
    assert any(row.move_type == "FIRE" for row in report.type_summary)
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "heatmap.md"
        json_output = Path(tmp) / "heatmap.json"
        write_report(report, output, json_output)
        assert "| Delta |" in output.read_text(encoding="utf-8")
        data = json.loads(json_output.read_text(encoding="utf-8"))
        assert data["schema"] == SCHEMA
        assert data["top_deltas"]
    print("balance_diff self-test: PASS")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run parser/report self-check")
    parser.add_argument("--attackers", help="comma-separated attacker species; default all")
    parser.add_argument("--defenders", help="comma-separated defender species; default all")
    parser.add_argument("--moves", help="comma-separated moves; default attacker learnset at level")
    parser.add_argument("--levels", default="50", help="comma-separated levels, default 50")
    parser.add_argument("--top", type=int, default=40, help="largest absolute deltas to render")
    parser.add_argument("--max-combos", type=int, default=50_000,
                        help="cap base attacker/move/defender combos; use --full for no cap")
    parser.add_argument("--full", action="store_true", help="do not cap base combinations")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Markdown output path")
    parser.add_argument("--json-output", type=Path, help="optional JSON output path")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.top <= 0:
        print("--top must be positive", file=sys.stderr)
        return 2
    if args.max_combos <= 0 and not args.full:
        print("--max-combos must be positive unless --full is set", file=sys.stderr)
        return 2

    try:
        levels = _parse_levels(args.levels)
        dataset = load_dataset()
        attackers = _resolve_names("attacker", _parse_csv(args.attackers), dataset.base_stats)
        defenders = _resolve_names("defender", _parse_csv(args.defenders), dataset.base_stats)
        moves = _parse_csv(args.moves)
        move_set = set(_resolve_names("move", moves, dataset.moves)) if moves is not None else None
        report = collect_report(
            dataset,
            attackers=attackers,
            defenders=defenders,
            moves=move_set,
            levels=levels,
            top=args.top,
            max_combos=None if args.full else args.max_combos,
        )
        write_report(report, args.output, args.json_output)
    except (ValueError, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    print(
        f"wrote {args.output} "
        f"({report.combo_count} combos, {report.variant_rows} variants, "
        f"truncated={report.truncated})"
    )
    if args.json_output is not None:
        print(f"wrote {args.json_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
