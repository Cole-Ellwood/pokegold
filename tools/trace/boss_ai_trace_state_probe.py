#!/usr/bin/env python3
"""Inspect a PyBoy state or battery-RAM-backed trace ROM before live capture."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.trace import runtime as trace_runtime

DEFAULT_ROM = ROOT / "pokegold_trace.gbc"
DEFAULT_SYMBOLS = ROOT / "pokegold_trace.sym"

MORTY_MAP_GROUP = 4
MORTY_MAP_NUMBER = 7
MORTY_OBJECT_INDEX = 2
SPRITE_MORTY = 0x15

MAP_OBJECT_LENGTH = 0x10
OBJECT_LENGTH = 0x28
MAP_OBJECT_SPRITE = 0x01
MAP_OBJECT_Y_COORD = 0x02
MAP_OBJECT_X_COORD = 0x03
MAP_OBJECT_TYPE = 0x08
MAP_OBJECT_SIGHT_RANGE = 0x09
OBJECT_SPRITE = 0x00
OBJECT_MAP_OBJECT_INDEX = 0x01
OBJECT_MAP_X = 0x10
OBJECT_MAP_Y = 0x11
NUM_OBJECT_STRUCTS = 13

INSPECT_SYMBOLS = (
    "wMapGroup",
    "wMapNumber",
    "wYCoord",
    "wXCoord",
    "wBattleMode",
    "wBattleType",
    "wOtherTrainerClass",
    "wOtherTrainerID",
    "wScriptMode",
    "wScriptBank",
    "wScriptPos",
    "wMapObjects",
    "wObjectStructs",
    "wPartyCount",
    "wPartyMon1Species",
    "wPartyMon1Level",
    "wPartyMon1HP",
    "wPartyMon1MaxHP",
    "wBattleMonSpecies",
    "wBattleMonLevel",
    "wBattleMonHP",
    "wBattleMonMaxHP",
    "wBossAITraceTopMoves",
    "wBossAITraceTopScores",
    "wBossAITraceChosenMove",
    "wBossAITraceSwitchConfidence",
    "wBossAITracePlanId",
    "wBossAITracePlausibleMask",
    "wBossAITraceRiskFlags",
    "wBossAIRevealedMovesBitmap",
)


Symbol = trace_runtime.Symbol


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def display_path(path: Path) -> str:
    return trace_runtime.display_path(path)


def sha256_file(path: Path) -> str:
    return trace_runtime.sha256_file(path)


def parse_symbols(path: Path) -> dict[str, Symbol]:
    return trace_runtime.parse_symbols(path)


def require_symbols(symbols: dict[str, Symbol]) -> None:
    missing = [name for name in INSPECT_SYMBOLS if name not in symbols]
    if missing:
        fail("missing required symbols: " + ", ".join(missing))


def load_pyboy():
    return trace_runtime.load_pyboy("PyBoy is required for state probing. Import failed")


def open_pyboy(rom: Path):
    return trace_runtime.open_pyboy(rom, "PyBoy is required for state probing. Import failed")


def read_byte(pyboy, symbol: Symbol) -> int:
    return trace_runtime.read_byte(pyboy, symbol)


def read_addr(pyboy, bank: int, address: int) -> int:
    return trace_runtime.read_addr(pyboy, bank, address)


def read_symbol(pyboy, symbols: dict[str, Symbol], name: str) -> int:
    return read_byte(pyboy, symbols[name])


def read_word(pyboy, symbol: Symbol) -> int:
    return trace_runtime.read_word(pyboy, symbol)


def read_symbol_word(pyboy, symbols: dict[str, Symbol], name: str) -> int:
    return read_word(pyboy, symbols[name])


def read_symbol_range(
    pyboy,
    symbols: dict[str, Symbol],
    name: str,
    size: int,
) -> list[int]:
    symbol = symbols[name]
    return [
        read_addr(pyboy, symbol.bank, symbol.address + offset)
        for offset in range(size)
    ]


def hex_bytes(values: list[int]) -> str:
    return " ".join(f"{value:02x}" for value in values)


def button(pyboy, name: str, wait_frames: int) -> None:
    pyboy.button(name, delay=8)
    pyboy.tick(wait_frames, False, False)


def boot_continue(pyboy) -> None:
    pyboy.tick(1800, False, False)
    button(pyboy, "start", 180)
    button(pyboy, "a", 180)
    button(pyboy, "a", 180)
    button(pyboy, "a", 180)


def load_state(pyboy, path: Path) -> None:
    if not path.exists():
        fail(f"missing save-state: {path}")
    with path.open("rb") as fh:
        pyboy.load_state(fh)


def map_object(
    pyboy,
    symbols: dict[str, Symbol],
    index: int,
) -> dict[str, int]:
    base = symbols["wMapObjects"]
    address = base.address + index * MAP_OBJECT_LENGTH
    return {
        "struct": read_addr(pyboy, base.bank, address),
        "sprite": read_addr(pyboy, base.bank, address + MAP_OBJECT_SPRITE),
        "y": read_addr(pyboy, base.bank, address + MAP_OBJECT_Y_COORD),
        "x": read_addr(pyboy, base.bank, address + MAP_OBJECT_X_COORD),
        "type": read_addr(pyboy, base.bank, address + MAP_OBJECT_TYPE) & 0x0F,
        "sight": read_addr(pyboy, base.bank, address + MAP_OBJECT_SIGHT_RANGE),
    }


def object_struct(
    pyboy,
    symbols: dict[str, Symbol],
    index: int,
) -> dict[str, int]:
    if not 0 <= index < NUM_OBJECT_STRUCTS:
        fail(f"object struct index out of range: {index}")
    base = symbols["wObjectStructs"]
    address = base.address + index * OBJECT_LENGTH
    return {
        "sprite": read_addr(pyboy, base.bank, address + OBJECT_SPRITE),
        "map_object": read_addr(pyboy, base.bank, address + OBJECT_MAP_OBJECT_INDEX),
        "x": read_addr(pyboy, base.bank, address + OBJECT_MAP_X),
        "y": read_addr(pyboy, base.bank, address + OBJECT_MAP_Y),
    }


def party_summary(pyboy, symbols: dict[str, Symbol], battle_mode: int) -> dict[str, int]:
    if battle_mode:
        return {
            "source": 1,
            "count": read_symbol(pyboy, symbols, "wPartyCount"),
            "species": read_symbol(pyboy, symbols, "wBattleMonSpecies"),
            "level": read_symbol(pyboy, symbols, "wBattleMonLevel"),
            "hp": read_symbol_word(pyboy, symbols, "wBattleMonHP"),
            "max_hp": read_symbol_word(pyboy, symbols, "wBattleMonMaxHP"),
        }
    return {
        "source": 0,
        "count": read_symbol(pyboy, symbols, "wPartyCount"),
        "species": read_symbol(pyboy, symbols, "wPartyMon1Species"),
        "level": read_symbol(pyboy, symbols, "wPartyMon1Level"),
        "hp": read_symbol_word(pyboy, symbols, "wPartyMon1HP"),
        "max_hp": read_symbol_word(pyboy, symbols, "wPartyMon1MaxHP"),
    }


def party_verdict(summary: dict[str, int]) -> list[str]:
    reasons: list[str] = []
    count = summary["count"]
    species = summary["species"]
    level = summary["level"]
    hp = summary["hp"]
    max_hp = summary["max_hp"]

    if not 1 <= count <= 6:
        reasons.append(f"party_count={count}")
    if species == 0:
        reasons.append("active_species=00")
    if not 1 <= level <= 100:
        reasons.append(f"active_level={level}")
    if max_hp == 0:
        reasons.append("active_max_hp=0")
    elif max_hp > 999:
        reasons.append(f"active_max_hp_implausible={max_hp}")
    if hp == 0:
        reasons.append("active_hp=0")
    elif hp > 999:
        reasons.append(f"active_hp_implausible={hp}")
    if max_hp and hp > max_hp:
        reasons.append(f"active_hp_gt_max:{hp}>{max_hp}")

    return reasons


def format_kv(key: str, value: str | int) -> str:
    return f"{key}={value}"


def morty_verdict(pyboy, symbols: dict[str, Symbol]) -> list[str]:
    reasons: list[str] = []
    map_group = read_symbol(pyboy, symbols, "wMapGroup")
    map_number = read_symbol(pyboy, symbols, "wMapNumber")
    battle_mode = read_symbol(pyboy, symbols, "wBattleMode")
    trainer_class = read_symbol(pyboy, symbols, "wOtherTrainerClass")
    trainer_id = read_symbol(pyboy, symbols, "wOtherTrainerID")
    morty_object = map_object(pyboy, symbols, MORTY_OBJECT_INDEX)
    morty_struct_index = morty_object["struct"]
    morty_struct = (
        object_struct(pyboy, symbols, morty_struct_index)
        if 0 < morty_struct_index < NUM_OBJECT_STRUCTS
        else None
    )

    if (map_group, map_number) != (MORTY_MAP_GROUP, MORTY_MAP_NUMBER):
        reasons.append(
            f"not_ecruteak_gym:{map_group:02x}:{map_number:02x}"
        )
    if battle_mode:
        if trainer_class != 0x04 or trainer_id != 0x01:
            reasons.append(
                f"battle_not_morty:class={trainer_class:02x},id={trainer_id:02x}"
            )
    elif morty_object["sprite"] != SPRITE_MORTY:
        reasons.append(
            f"morty_map_object_missing:object{MORTY_OBJECT_INDEX}_sprite={morty_object['sprite']:02x}"
        )
    elif not 0 < morty_struct_index < NUM_OBJECT_STRUCTS:
        reasons.append(f"morty_map_object_has_no_loaded_struct:struct={morty_struct_index:02x}")
    elif morty_struct is not None and morty_struct["sprite"] != SPRITE_MORTY:
        reasons.append(
            "morty_object_struct_mismatch:"
            f"struct{morty_struct_index}_sprite={morty_struct['sprite']:02x}"
        )
    party_reasons = party_verdict(party_summary(pyboy, symbols, battle_mode))
    if party_reasons:
        reasons.append("player_party_invalid:" + "|".join(party_reasons))

    if not reasons:
        return ["morty_candidate=PASS"]
    return ["morty_candidate=FAIL", "morty_candidate_reasons=" + ",".join(reasons)]


def format_probe(pyboy, symbols: dict[str, Symbol], args: argparse.Namespace) -> str:
    lines = [
        format_kv("trace_rom", display_path(args.rom)),
        format_kv("trace_rom_sha256", sha256_file(args.rom)),
        format_kv("trace_symbols", display_path(args.symbols)),
        format_kv("trace_symbols_sha256", sha256_file(args.symbols)),
    ]
    if args.save_state:
        lines.append(format_kv("save_state", display_path(args.save_state)))
    if args.boot_continue:
        lines.append("boot_continue=true")

    map_group = read_symbol(pyboy, symbols, "wMapGroup")
    map_number = read_symbol(pyboy, symbols, "wMapNumber")
    y_coord = read_symbol(pyboy, symbols, "wYCoord")
    x_coord = read_symbol(pyboy, symbols, "wXCoord")
    battle_mode = read_symbol(pyboy, symbols, "wBattleMode")
    party = party_summary(pyboy, symbols, battle_mode)
    script_pos = read_symbol(pyboy, symbols, "wScriptPos")
    script_pos |= read_addr(pyboy, symbols["wScriptPos"].bank, symbols["wScriptPos"].address + 1) << 8

    lines.extend(
        [
            format_kv("map", f"{map_group:02x}:{map_number:02x}"),
            format_kv("coords", f"x={x_coord},y={y_coord}"),
            format_kv("battle_mode", battle_mode),
            format_kv("battle_type", read_symbol(pyboy, symbols, "wBattleType")),
            format_kv(
                "other_trainer",
                (
                    f"class={read_symbol(pyboy, symbols, 'wOtherTrainerClass'):02x},"
                    f"id={read_symbol(pyboy, symbols, 'wOtherTrainerID'):02x}"
                ),
            ),
            format_kv(
                "script",
                (
                    f"mode={read_symbol(pyboy, symbols, 'wScriptMode')},"
                    f"bank={read_symbol(pyboy, symbols, 'wScriptBank'):02x},"
                    f"pos={script_pos:04x}"
                ),
            ),
            format_kv(
                "player_active",
                (
                    f"source={'battle' if party['source'] else 'party'},"
                    f"count={party['count']},"
                    f"species={party['species']:02x},"
                    f"level={party['level']},"
                    f"hp={party['hp']}/{party['max_hp']}"
                ),
            ),
        ]
    )

    for index in range(args.objects):
        obj = map_object(pyboy, symbols, index)
        lines.append(
            "map_object_{index}=struct={struct},sprite={sprite:02x},y={y},x={x},type={type},sight={sight}".format(
                index=index,
                **obj,
            )
        )

    for index in range(args.object_structs):
        obj = object_struct(pyboy, symbols, index)
        lines.append(
            "object_struct_{index}=sprite={sprite:02x},map_object={map_object},x={x},y={y}".format(
                index=index,
                **obj,
            )
        )

    lines.extend(
        [
            format_kv(
                "trace_top_moves",
                hex_bytes(read_symbol_range(pyboy, symbols, "wBossAITraceTopMoves", 3)),
            ),
            format_kv(
                "trace_top_scores",
                hex_bytes(read_symbol_range(pyboy, symbols, "wBossAITraceTopScores", 3)),
            ),
            format_kv(
                "trace_chosen",
                hex_bytes(read_symbol_range(pyboy, symbols, "wBossAITraceChosenMove", 1)),
            ),
            format_kv(
                "trace_switch_confidence",
                read_symbol(pyboy, symbols, "wBossAITraceSwitchConfidence"),
            ),
            format_kv(
                "trace_plan_id",
                read_symbol(pyboy, symbols, "wBossAITracePlanId"),
            ),
            format_kv(
                "trace_plausible_mask",
                hex_bytes(read_symbol_range(pyboy, symbols, "wBossAITracePlausibleMask", 4)),
            ),
            format_kv(
                "trace_risk_flags",
                f"{read_symbol(pyboy, symbols, 'wBossAITraceRiskFlags'):02x}",
            ),
            format_kv(
                "revealed_masks",
                hex_bytes(read_symbol_range(pyboy, symbols, "wBossAIRevealedMovesBitmap", 24)),
            ),
        ]
    )

    if args.expect_morty:
        lines.extend(morty_verdict(pyboy, symbols))

    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe whether a trace ROM state is usable before Boss AI capture."
    )
    parser.add_argument("--rom", type=Path, default=DEFAULT_ROM)
    parser.add_argument("--symbols", type=Path, default=DEFAULT_SYMBOLS)
    parser.add_argument("--save-state", type=Path)
    parser.add_argument(
        "--boot-continue",
        action="store_true",
        help="boot the ROM and press through Continue before probing battery RAM",
    )
    parser.add_argument("--frames", type=int, default=0, help="frames to tick before probing")
    parser.add_argument("--objects", type=int, default=6, help="map object slots to print")
    parser.add_argument(
        "--object-structs",
        type=int,
        default=4,
        help="loaded object structs to print",
    )
    parser.add_argument("--expect-morty", action="store_true")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit nonzero when an expected boss candidate fails validation",
    )
    parser.add_argument("--out", type=Path)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.frames < 0:
        fail("--frames must be non-negative")
    if args.objects < 0 or args.object_structs < 0:
        fail("--objects and --object-structs must be non-negative")

    symbols = parse_symbols(args.symbols)
    require_symbols(symbols)

    pyboy = open_pyboy(args.rom)
    try:
        if args.save_state:
            load_state(pyboy, args.save_state)
        if args.boot_continue:
            boot_continue(pyboy)
        if args.frames:
            pyboy.tick(args.frames, False, False)
        text = format_probe(pyboy, symbols, args)
    finally:
        pyboy.stop(save=False)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text, end="")
    if args.strict and "morty_candidate=FAIL" in text:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
