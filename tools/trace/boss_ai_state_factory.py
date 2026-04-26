#!/usr/bin/env python3
"""Generate PyBoy boss decision-point states through real map scripts."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.trace import boss_ai_trace_capture as capture


DEFAULT_OUT_DIR = ROOT / ".local" / "tmp" / "boss_state_factory"
DEFAULT_BATTERY_SAVE = ROOT / "pokegold.sav"
EVENT_FLAGS = ROOT / "constants" / "event_flags.asm"

MAPSTATUS_ENTER = 1
MAPSTATUS_HANDLE = 2
MAPSETUP_WARP = 0xF1
SPAWN_N_A = 0xFF

OLIVINE_GYM_GROUP = 1
OLIVINE_GYM_MAP = 2
JASMINE_TRAINER_CLASS = 0x06
JASMINE_TRAINER_ID = 0x01

REQUIRED_SYMBOLS = (
    "hBattleTurn",
    "hMapEntryMethod",
    "wBattleHasJustStarted",
    "wBattleMode",
    "wBossAITraceChosenMove",
    "wBossAITracePlanId",
    "wBossAITraceTopMoves",
    "wDefaultSpawnpoint",
    "wEnabledPlayerEvents",
    "wEventFlags",
    "wMapGroup",
    "wMapNumber",
    "wMapStatus",
    "wOtherTrainerClass",
    "wOtherTrainerID",
    "wPartyCount",
    "wPartyMon1HP",
    "wPartyMon1Level",
    "wPartyMon1MaxHP",
    "wPartyMon1Species",
    "wScriptMode",
    "wScriptRunning",
    "wXCoord",
    "wYCoord",
)


@dataclass(frozen=True)
class RunResult:
    state_path: Path
    frame: int


class StateFactoryError(RuntimeError):
    pass


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_rgb_int(token: str) -> int:
    token = token.strip()
    if token.startswith("$"):
        return int(token[1:], 16)
    return int(token, 0)


def parse_simple_consts(path: Path) -> dict[str, int]:
    """Parse simple rgbasm const/const_skip tables."""
    constants: dict[str, int] = {}
    value = 0
    active = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if parts[0] == "const_def":
            active = True
            value = parse_rgb_int(parts[1]) if len(parts) > 1 else 0
            continue
        if not active:
            continue
        if parts[0] == "const_next" and len(parts) >= 2:
            value = parse_rgb_int(parts[1])
            continue
        if parts[0] == "const" and len(parts) >= 2:
            constants[parts[1]] = value
            value += 1
            continue
        if parts[0] == "const_skip":
            value += parse_rgb_int(parts[1]) if len(parts) >= 2 else 1
            continue
        if parts[0] == "DEF":
            continue
    return constants


def require_symbols(symbols: dict[str, capture.Symbol]) -> None:
    capture.require_symbols(symbols)
    missing = [name for name in REQUIRED_SYMBOLS if name not in symbols]
    if missing:
        fail("missing required symbols: " + ", ".join(missing))


def write_byte(pyboy, symbol: capture.Symbol, value: int) -> None:
    value &= 0xFF
    if 0xD000 <= symbol.address <= 0xDFFF and symbol.bank:
        try:
            pyboy.memory[symbol.bank, symbol.address] = value
            return
        except Exception:
            old_bank = int(pyboy.memory[0xFF70])
            pyboy.memory[0xFF70] = symbol.bank
            try:
                pyboy.memory[symbol.address] = value
            finally:
                pyboy.memory[0xFF70] = old_bank
            return
    pyboy.memory[symbol.address] = value


def read_one(pyboy, symbols: dict[str, capture.Symbol], name: str) -> int:
    return capture.read_byte(pyboy, symbols[name])


def write_one(pyboy, symbols: dict[str, capture.Symbol], name: str, value: int) -> None:
    write_byte(pyboy, symbols[name], value)


def write_event(
    pyboy,
    symbols: dict[str, capture.Symbol],
    event_constants: dict[str, int],
    name: str,
    enabled: bool,
) -> None:
    if name not in event_constants:
        fail(f"missing event constant: {name}")
    bit_index = event_constants[name]
    base = symbols["wEventFlags"]
    byte_symbol = capture.Symbol(base.bank, base.address + bit_index // 8)
    old_value = capture.read_byte(pyboy, byte_symbol)
    mask = 1 << (bit_index & 7)
    new_value = (old_value | mask) if enabled else (old_value & ~mask)
    write_byte(pyboy, byte_symbol, new_value)


def trace_summary(values: dict[str, list[int]]) -> str:
    top = values["wBossAITraceTopMoves"]
    scores = values["wBossAITraceTopScores"]
    return (
        f"chosen={values['wBossAITraceChosenMove'][0]:02x} "
        f"plan={values['wBossAITracePlanId'][0]:02x} "
        f"top={top[0]:02x} {top[1]:02x} {top[2]:02x} "
        f"scores={scores[0]:02x} {scores[1]:02x} {scores[2]:02x}"
    )


def watch_line(pyboy, symbols: dict[str, capture.Symbol], frame: int, label: str) -> str:
    trace_values = capture.read_trace_values(pyboy, symbols)
    return (
        f"{label} frame={frame} "
        f"map={read_one(pyboy, symbols, 'wMapGroup'):02x}:"
        f"{read_one(pyboy, symbols, 'wMapNumber'):02x} "
        f"coords=x={read_one(pyboy, symbols, 'wXCoord')},"
        f"y={read_one(pyboy, symbols, 'wYCoord')} "
        f"map_status={read_one(pyboy, symbols, 'wMapStatus'):02x} "
        f"battle_mode={read_one(pyboy, symbols, 'wBattleMode'):02x} "
        f"just_started={read_one(pyboy, symbols, 'wBattleHasJustStarted'):02x} "
        f"turn={read_one(pyboy, symbols, 'hBattleTurn'):02x} "
        f"trainer={read_one(pyboy, symbols, 'wOtherTrainerClass'):02x}:"
        f"{read_one(pyboy, symbols, 'wOtherTrainerID'):02x} "
        f"script_running={read_one(pyboy, symbols, 'wScriptRunning'):02x} "
        f"script_mode={read_one(pyboy, symbols, 'wScriptMode'):02x} "
        f"{trace_summary(trace_values)}"
    )


def save_state(pyboy, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        pyboy.save_state(fh)


def write_log(out_dir: Path, log: list[str]) -> Path:
    log_path = out_dir / "boss_ai_state_factory.log"
    log_path.write_text("\n".join(log).rstrip() + "\n", encoding="utf-8")
    return log_path


def prepare_work_rom(args: argparse.Namespace) -> Path:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    work_rom = args.out_dir / args.rom.name
    shutil.copy2(args.rom, work_rom)
    if args.battery_save:
        if not args.battery_save.exists():
            fail(f"missing battery save: {args.battery_save}")
        shutil.copy2(args.battery_save, work_rom.with_suffix(work_rom.suffix + ".ram"))
    return work_rom


def open_pyboy(rom: Path):
    local_pydeps = ROOT / ".local" / "pydeps"
    if local_pydeps.exists():
        sys.path.insert(0, str(local_pydeps))
    warnings.filterwarnings("ignore", message="Using SDL2 binaries.*")
    try:
        from pyboy import PyBoy  # type: ignore
    except Exception as exc:
        fail(f"PyBoy is required for state generation. Import failed: {exc}")

    logging.disable(logging.WARNING)
    try:
        pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    except TypeError:
        pyboy = PyBoy(str(rom), window="null", sound=False)
    capture.disable_realtime(pyboy)
    return pyboy


def press(pyboy, button_name: str, wait_frames: int) -> None:
    pyboy.button(button_name, delay=8)
    pyboy.tick(wait_frames, False, False)


def boot_continue(pyboy, symbols: dict[str, capture.Symbol], log: list[str]) -> int:
    frame = 0
    pyboy.tick(1800, False, False)
    frame += 1800
    for button_name in ("start", "a", "a", "a"):
        press(pyboy, button_name, 180)
        frame += 180
        log.append(watch_line(pyboy, symbols, frame, f"BOOT_{button_name.upper()}"))
    return frame


def validate_party(pyboy, symbols: dict[str, capture.Symbol]) -> None:
    count = read_one(pyboy, symbols, "wPartyCount")
    species = read_one(pyboy, symbols, "wPartyMon1Species")
    level = read_one(pyboy, symbols, "wPartyMon1Level")
    hp = (
        read_one(pyboy, symbols, "wPartyMon1HP") << 8
    ) | capture.read_byte(
        pyboy,
        capture.Symbol(symbols["wPartyMon1HP"].bank, symbols["wPartyMon1HP"].address + 1),
    )
    max_hp = (
        read_one(pyboy, symbols, "wPartyMon1MaxHP") << 8
    ) | capture.read_byte(
        pyboy,
        capture.Symbol(
            symbols["wPartyMon1MaxHP"].bank,
            symbols["wPartyMon1MaxHP"].address + 1,
        ),
    )
    problems: list[str] = []
    if not 1 <= count <= 6:
        problems.append(f"party_count={count}")
    if species == 0:
        problems.append("species=00")
    if not 1 <= level <= 100:
        problems.append(f"level={level}")
    if hp == 0 or max_hp == 0 or hp > max_hp or hp > 999 or max_hp > 999:
        problems.append(f"hp={hp}/{max_hp}")
    if problems:
        fail("battery save did not provide a sane lead party mon: " + ", ".join(problems))


def setup_jasmine_entry(
    pyboy,
    symbols: dict[str, capture.Symbol],
    event_constants: dict[str, int],
    out_dir: Path,
    log: list[str],
    frame: int,
) -> int:
    validate_party(pyboy, symbols)
    write_event(pyboy, symbols, event_constants, "EVENT_JASMINE_RETURNED_TO_GYM", True)
    write_event(pyboy, symbols, event_constants, "EVENT_BEAT_JASMINE", False)
    write_event(pyboy, symbols, event_constants, "EVENT_OLIVINE_GYM_JASMINE", False)

    write_one(pyboy, symbols, "wMapGroup", OLIVINE_GYM_GROUP)
    write_one(pyboy, symbols, "wMapNumber", OLIVINE_GYM_MAP)
    write_one(pyboy, symbols, "wXCoord", 5)
    write_one(pyboy, symbols, "wYCoord", 4)
    write_one(pyboy, symbols, "wDefaultSpawnpoint", SPAWN_N_A)
    write_one(pyboy, symbols, "hMapEntryMethod", MAPSETUP_WARP)
    write_one(pyboy, symbols, "wMapStatus", MAPSTATUS_ENTER)
    log.append(watch_line(pyboy, symbols, frame, "JASMINE_WARP_ARMED"))

    for _ in range(900):
        pyboy.tick(1, False, False)
        frame += 1
        if (
            read_one(pyboy, symbols, "wMapGroup") == OLIVINE_GYM_GROUP
            and read_one(pyboy, symbols, "wMapNumber") == OLIVINE_GYM_MAP
            and read_one(pyboy, symbols, "wMapStatus") == MAPSTATUS_HANDLE
        ):
            log.append(watch_line(pyboy, symbols, frame, "JASMINE_MAP_READY"))
            return frame

    diagnostic = out_dir / "jasmine_map_load_timeout.state"
    save_state(pyboy, diagnostic)
    log.append(watch_line(pyboy, symbols, frame, "JASMINE_MAP_TIMEOUT"))
    write_log(out_dir, log)
    raise StateFactoryError(
        f"Jasmine map load did not settle; diagnostic state saved to {diagnostic}"
    )


def drive_to_chosen_move(
    pyboy,
    symbols: dict[str, capture.Symbol],
    args: argparse.Namespace,
    log: list[str],
    frame: int,
) -> RunResult:
    for button_name in ("up", "a"):
        press(pyboy, button_name, args.input_wait_frames)
        frame += args.input_wait_frames
        log.append(watch_line(pyboy, symbols, frame, f"PRIME_{button_name.upper()}"))

    last_signature: tuple[int, ...] | None = None
    for step in range(args.max_a_presses):
        press(pyboy, "a", args.input_wait_frames)
        frame += args.input_wait_frames
        values = capture.read_trace_values(pyboy, symbols)
        signature = capture.trace_signature(values)
        chosen = values["wBossAITraceChosenMove"][0]
        if signature != last_signature or step % args.log_every == 0 or chosen:
            log.append(watch_line(pyboy, symbols, frame, f"DRIVE_A_{step + 1:03d}"))
            last_signature = signature
        if chosen:
            state_path = args.out_dir / f"jasmine_chosen_frame_{frame:04d}.state"
            save_state(pyboy, state_path)
            return RunResult(state_path=state_path, frame=frame)

    diagnostic = args.out_dir / f"jasmine_no_chosen_after_{frame:04d}.state"
    save_state(pyboy, diagnostic)
    log.append(watch_line(pyboy, symbols, frame, "JASMINE_NO_CHOSEN"))
    write_log(args.out_dir, log)
    raise StateFactoryError(
        f"no Jasmine chosen move observed; diagnostic state saved to {diagnostic}"
    )


def write_manifest_hint(args: argparse.Namespace, result: RunResult) -> None:
    hint = {
        "boss": "jasmine",
        "save_state": str(result.state_path.relative_to(ROOT)).replace("\\", "/"),
        "frame": result.frame,
        "next": [
            "Add save_state to the jasmine manifest row.",
            "Set stop_after_first_capture=true and require_chosen_move=true.",
            "Run python tools\\trace\\boss_ai_trace_batch.py --execute --only jasmine.",
        ],
    }
    hint_path = args.out_dir / "jasmine_manifest_hint.json"
    hint_path.write_text(json.dumps(hint, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate boss AI decision-point PyBoy states via real map scripts."
    )
    parser.add_argument("--boss", choices=("jasmine",), default="jasmine")
    parser.add_argument("--rom", type=Path, default=capture.DEFAULT_ROM)
    parser.add_argument("--symbols", type=Path, default=capture.DEFAULT_SYMBOLS)
    parser.add_argument("--battery-save", type=Path, default=DEFAULT_BATTERY_SAVE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--input-wait-frames", type=int, default=45)
    parser.add_argument("--max-a-presses", type=int, default=120)
    parser.add_argument("--log-every", type=int, default=8)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.input_wait_frames <= 0:
        fail("--input-wait-frames must be positive")
    if args.max_a_presses <= 0:
        fail("--max-a-presses must be positive")
    if args.log_every <= 0:
        fail("--log-every must be positive")

    symbols = capture.parse_symbols(args.symbols)
    require_symbols(symbols)
    event_constants = parse_simple_consts(EVENT_FLAGS)
    work_rom = prepare_work_rom(args)
    log: list[str] = [
        f"ROM_SOURCE {capture.display_path(args.rom)}",
        f"ROM_WORK {capture.display_path(work_rom)}",
        f"BATTERY_SAVE {capture.display_path(args.battery_save)}",
    ]

    pyboy = open_pyboy(work_rom)
    try:
        frame = boot_continue(pyboy, symbols, log)
        frame = setup_jasmine_entry(pyboy, symbols, event_constants, args.out_dir, log, frame)
        result = drive_to_chosen_move(pyboy, symbols, args, log, frame)
        log.append(watch_line(pyboy, symbols, result.frame, "JASMINE_CHOSEN"))
    finally:
        pyboy.stop(save=False)

    log_path = write_log(args.out_dir, log)
    write_manifest_hint(args, result)
    print(f"state={capture.display_path(result.state_path)}")
    print(f"frame={result.frame}")
    print(f"log={capture.display_path(log_path)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except StateFactoryError as exc:
        fail(str(exc))
