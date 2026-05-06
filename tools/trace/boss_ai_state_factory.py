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
MAP_CONSTANTS = ROOT / "constants" / "map_constants.asm"
TRAINER_CONSTANTS = ROOT / "constants" / "trainer_constants.asm"
MANIFEST = ROOT / "audit" / "boss_ai_trace" / "live_capture_manifest.json"

MAPSTATUS_ENTER = 1
MAPSTATUS_HANDLE = 2
MAPSETUP_WARP = 0xF1
SPAWN_N_A = 0xFF

BASE_REQUIRED_SYMBOLS = (
    "hBattleTurn",
    "hMapEntryMethod",
    "wBattleHasJustStarted",
    "wBattleMode",
    "wBossAITraceChosenMove",
    "wBossAITracePlanId",
    "wBossAITraceTopMoves",
    "wDefaultSpawnpoint",
    "wEventFlags",
    "wJohtoBadges",
    "wKantoBadges",
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
class BossRoute:
    capture_id: str
    map_name: str
    player_x: int
    player_y: int
    trainer_class: str
    trainer_id: str
    clear_events: tuple[str, ...]
    set_events: tuple[str, ...] = ()
    scene_values: tuple[tuple[str, int], ...] = ()
    prime_buttons: tuple[str, ...] = ("up", "a")
    input_wait_frames: int = 45
    max_a_presses: int = 120
    clear_badges: bool = True


@dataclass(frozen=True)
class TrainerConstant:
    class_id: int
    trainer_id: int


@dataclass(frozen=True)
class RunResult:
    route: BossRoute
    state_path: Path
    frame: int


class StateFactoryError(RuntimeError):
    pass


ROUTES: dict[str, BossRoute] = {
    "falkner": BossRoute(
        capture_id="falkner",
        map_name="VIOLET_GYM",
        player_x=5,
        player_y=2,
        trainer_class="FALKNER",
        trainer_id="FALKNER1",
        clear_events=("EVENT_BEAT_FALKNER",),
    ),
    "bugsy": BossRoute(
        capture_id="bugsy",
        map_name="AZALEA_GYM",
        player_x=5,
        player_y=8,
        trainer_class="BUGSY",
        trainer_id="BUGSY1",
        clear_events=("EVENT_BEAT_BUGSY",),
    ),
    "whitney": BossRoute(
        capture_id="whitney",
        map_name="GOLDENROD_GYM",
        player_x=8,
        player_y=4,
        trainer_class="WHITNEY",
        trainer_id="WHITNEY1",
        clear_events=(
            "EVENT_BEAT_WHITNEY",
            "EVENT_MADE_WHITNEY_CRY",
            "EVENT_GOT_TM45_ATTRACT",
        ),
        scene_values=(("wGoldenrodGymSceneID", 0),),
    ),
    "morty": BossRoute(
        capture_id="morty",
        map_name="ECRUTEAK_GYM",
        player_x=5,
        player_y=2,
        trainer_class="MORTY",
        trainer_id="MORTY1",
        clear_events=("EVENT_BEAT_MORTY", "EVENT_GOT_TM30_SHADOW_BALL"),
    ),
    "chuck": BossRoute(
        capture_id="chuck",
        map_name="CIANWOOD_GYM",
        player_x=4,
        player_y=2,
        trainer_class="CHUCK",
        trainer_id="CHUCK1",
        clear_events=("EVENT_BEAT_CHUCK", "EVENT_GOT_TM01_DYNAMICPUNCH"),
        max_a_presses=160,
    ),
    "jasmine": BossRoute(
        capture_id="jasmine",
        map_name="OLIVINE_GYM",
        player_x=5,
        player_y=4,
        trainer_class="JASMINE",
        trainer_id="JASMINE1",
        clear_events=(
            "EVENT_BEAT_JASMINE",
            "EVENT_OLIVINE_GYM_JASMINE",
            "EVENT_GOT_TM23_IRON_TAIL",
        ),
        set_events=("EVENT_JASMINE_RETURNED_TO_GYM",),
        input_wait_frames=30,
    ),
    "pryce": BossRoute(
        capture_id="pryce",
        map_name="MAHOGANY_GYM",
        player_x=5,
        player_y=4,
        trainer_class="PRYCE",
        trainer_id="PRYCE1",
        clear_events=("EVENT_BEAT_PRYCE", "EVENT_GOT_TM16_ICY_WIND"),
    ),
    "clair": BossRoute(
        capture_id="clair",
        map_name="BLACKTHORN_GYM_1F",
        player_x=5,
        player_y=4,
        trainer_class="CLAIR",
        trainer_id="CLAIR1",
        clear_events=(
            "EVENT_BEAT_CLAIR",
            "EVENT_GOT_TM24_DRAGONBREATH",
        ),
    ),
    "brock": BossRoute(
        capture_id="brock",
        map_name="PEWTER_GYM",
        player_x=5,
        player_y=2,
        trainer_class="BROCK",
        trainer_id="BROCK1",
        clear_events=("EVENT_BEAT_BROCK",),
    ),
    "misty": BossRoute(
        capture_id="misty",
        map_name="CERULEAN_GYM",
        player_x=5,
        player_y=4,
        trainer_class="MISTY",
        trainer_id="MISTY1",
        clear_events=("EVENT_BEAT_MISTY", "EVENT_TRAINERS_IN_CERULEAN_GYM"),
        scene_values=(("wCeruleanGymSceneID", 0),),
    ),
    "lt_surge": BossRoute(
        capture_id="lt_surge",
        map_name="VERMILION_GYM",
        player_x=5,
        player_y=3,
        trainer_class="LT_SURGE",
        trainer_id="LT_SURGE1",
        clear_events=("EVENT_BEAT_LTSURGE", "EVENT_GOT_TM07_ZAP_CANNON"),
    ),
    "erika": BossRoute(
        capture_id="erika",
        map_name="CELADON_GYM",
        player_x=5,
        player_y=4,
        trainer_class="ERIKA",
        trainer_id="ERIKA1",
        clear_events=("EVENT_BEAT_ERIKA", "EVENT_GOT_TM19_GIGA_DRAIN"),
    ),
    "janine": BossRoute(
        capture_id="janine",
        map_name="FUCHSIA_GYM",
        player_x=1,
        player_y=11,
        trainer_class="JANINE",
        trainer_id="JANINE1",
        clear_events=("EVENT_BEAT_JANINE", "EVENT_GOT_TM06_TOXIC"),
        max_a_presses=150,
    ),
    "sabrina": BossRoute(
        capture_id="sabrina",
        map_name="SAFFRON_GYM",
        player_x=9,
        player_y=9,
        trainer_class="SABRINA",
        trainer_id="SABRINA1",
        clear_events=("EVENT_BEAT_SABRINA",),
    ),
    "blaine": BossRoute(
        capture_id="blaine",
        map_name="SEAFOAM_GYM",
        player_x=5,
        player_y=3,
        trainer_class="BLAINE",
        trainer_id="BLAINE1",
        clear_events=("EVENT_BEAT_BLAINE",),
    ),
    "blue": BossRoute(
        capture_id="blue",
        map_name="VIRIDIAN_GYM",
        player_x=5,
        player_y=4,
        trainer_class="BLUE",
        trainer_id="BLUE1",
        clear_events=("EVENT_BEAT_BLUE", "EVENT_VIRIDIAN_GYM_BLUE"),
    ),
    "koga": BossRoute(
        capture_id="koga",
        map_name="KOGAS_ROOM",
        player_x=5,
        player_y=8,
        trainer_class="KOGA",
        trainer_id="KOGA1",
        clear_events=(
            "EVENT_BEAT_ELITE_4_KOGA",
            "EVENT_KOGAS_ROOM_ENTRANCE_CLOSED",
            "EVENT_KOGAS_ROOM_EXIT_OPEN",
        ),
        scene_values=(("wKogasRoomSceneID", 1),),
    ),
    "champion_lance": BossRoute(
        capture_id="champion_lance",
        map_name="LANCES_ROOM",
        player_x=5,
        player_y=3,
        trainer_class="CHAMPION",
        trainer_id="LANCE",
        clear_events=(
            "EVENT_BEAT_CHAMPION_LANCE",
            "EVENT_LANCES_ROOM_ENTRANCE_CLOSED",
            "EVENT_LANCES_ROOM_EXIT_OPEN",
        ),
        set_events=("EVENT_LANCES_ROOM_OAK_AND_MARY",),
        scene_values=(("wLancesRoomSceneID", 1),),
        max_a_presses=150,
    ),
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_rgb_int(token: str) -> int:
    token = token.strip().rstrip(",")
    if token.startswith("$"):
        return int(token[1:], 16)
    return int(token, 0)


def strip_asm_comment(raw: str) -> str:
    return raw.split(";", 1)[0].strip()


def parse_simple_consts(path: Path) -> dict[str, int]:
    """Parse simple rgbasm const/const_skip tables."""
    constants: dict[str, int] = {}
    value = 0
    active = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = strip_asm_comment(raw)
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
    return constants


def parse_map_consts(path: Path) -> dict[str, tuple[int, int]]:
    maps: dict[str, tuple[int, int]] = {}
    group = 0
    map_value = 1
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = strip_asm_comment(raw)
        if not line:
            continue
        parts = line.replace(",", " ").split()
        if parts[0] == "newgroup" and len(parts) >= 2:
            group += 1
            map_value = 1
            continue
        if parts[0] == "map_const" and len(parts) >= 2:
            maps[parts[1]] = (group, map_value)
            map_value += 1
    return maps


def parse_trainer_consts(path: Path) -> dict[tuple[str, str], TrainerConstant]:
    trainers: dict[tuple[str, str], TrainerConstant] = {}
    class_ids: dict[str, int] = {}
    class_id = 0
    current_class = ""
    trainer_id = 1
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = strip_asm_comment(raw)
        if not line:
            continue
        parts = line.split()
        if parts[0] == "trainerclass" and len(parts) >= 2:
            current_class = parts[1]
            class_ids[current_class] = class_id
            class_id += 1
            trainer_id = 1
            continue
        if parts[0] == "const" and len(parts) >= 2 and current_class:
            trainers[(current_class, parts[1])] = TrainerConstant(
                class_ids[current_class],
                trainer_id,
            )
            trainer_id += 1
    return trainers


def route_ids_from_manifest(path: Path) -> list[str]:
    if not path.exists():
        return list(ROUTES)
    data = json.loads(path.read_text(encoding="utf-8"))
    ids: list[str] = []
    for entry in data.get("captures", []):
        if not isinstance(entry, dict):
            continue
        capture_id = entry.get("id")
        if isinstance(capture_id, str) and capture_id in ROUTES:
            ids.append(capture_id)
    return ids


def require_symbols(symbols: dict[str, capture.Symbol], routes: list[BossRoute]) -> None:
    capture.require_symbols(symbols)
    required = set(BASE_REQUIRED_SYMBOLS)
    for route in routes:
        required.update(symbol for symbol, _value in route.scene_values)
    missing = [name for name in sorted(required) if name not in symbols]
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


def clear_badges(pyboy, symbols: dict[str, capture.Symbol]) -> None:
    write_one(pyboy, symbols, "wJohtoBadges", 0)
    write_one(pyboy, symbols, "wKantoBadges", 0)


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


def write_log(out_dir: Path, route_id: str, log: list[str]) -> Path:
    log_path = out_dir / f"{route_id}_state_factory.log"
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


def setup_route_entry(
    pyboy,
    route: BossRoute,
    symbols: dict[str, capture.Symbol],
    event_constants: dict[str, int],
    map_constants: dict[str, tuple[int, int]],
    out_dir: Path,
    log: list[str],
    frame: int,
) -> int:
    validate_party(pyboy, symbols)
    if route.clear_badges:
        clear_badges(pyboy, symbols)
    for event_name in route.set_events:
        write_event(pyboy, symbols, event_constants, event_name, True)
    for event_name in route.clear_events:
        write_event(pyboy, symbols, event_constants, event_name, False)
    for symbol_name, value in route.scene_values:
        write_one(pyboy, symbols, symbol_name, value)

    if route.map_name not in map_constants:
        fail(f"missing map constant: {route.map_name}")
    map_group, map_number = map_constants[route.map_name]
    write_one(pyboy, symbols, "wMapGroup", map_group)
    write_one(pyboy, symbols, "wMapNumber", map_number)
    write_one(pyboy, symbols, "wXCoord", route.player_x)
    write_one(pyboy, symbols, "wYCoord", route.player_y)
    write_one(pyboy, symbols, "wDefaultSpawnpoint", SPAWN_N_A)
    write_one(pyboy, symbols, "hMapEntryMethod", MAPSETUP_WARP)
    write_one(pyboy, symbols, "wMapStatus", MAPSTATUS_ENTER)
    log.append(watch_line(pyboy, symbols, frame, f"{route.capture_id.upper()}_WARP_ARMED"))

    for _ in range(900):
        pyboy.tick(1, False, False)
        frame += 1
        if (
            read_one(pyboy, symbols, "wMapGroup") == map_group
            and read_one(pyboy, symbols, "wMapNumber") == map_number
            and read_one(pyboy, symbols, "wMapStatus") == MAPSTATUS_HANDLE
        ):
            log.append(watch_line(pyboy, symbols, frame, f"{route.capture_id.upper()}_MAP_READY"))
            return frame

    diagnostic = out_dir / f"{route.capture_id}_map_load_timeout.state"
    save_state(pyboy, diagnostic)
    log.append(watch_line(pyboy, symbols, frame, f"{route.capture_id.upper()}_MAP_TIMEOUT"))
    write_log(out_dir, route.capture_id, log)
    raise StateFactoryError(
        f"{route.capture_id}: map load did not settle; diagnostic state saved to {diagnostic}"
    )


def expected_trainer(
    route: BossRoute,
    trainer_constants: dict[tuple[str, str], TrainerConstant],
) -> TrainerConstant:
    key = (route.trainer_class, route.trainer_id)
    if key not in trainer_constants:
        fail(f"missing trainer constant: {route.trainer_class}, {route.trainer_id}")
    return trainer_constants[key]


def drive_to_chosen_move(
    pyboy,
    route: BossRoute,
    trainer_constant: TrainerConstant,
    symbols: dict[str, capture.Symbol],
    args: argparse.Namespace,
    log: list[str],
    frame: int,
) -> RunResult:
    input_wait_frames = (
        route.input_wait_frames
        if args.input_wait_frames == 0
        else args.input_wait_frames
    )
    for button_name in route.prime_buttons:
        press(pyboy, button_name, input_wait_frames)
        frame += input_wait_frames
        log.append(watch_line(pyboy, symbols, frame, f"PRIME_{button_name.upper()}"))

    last_signature: tuple[int, ...] | None = None
    max_presses = args.max_a_presses or route.max_a_presses
    for step in range(max_presses):
        press(pyboy, "a", input_wait_frames)
        frame += input_wait_frames
        values = capture.read_trace_values(pyboy, symbols)
        signature = capture.trace_signature(values)
        chosen = values["wBossAITraceChosenMove"][0]
        trainer_class = read_one(pyboy, symbols, "wOtherTrainerClass")
        trainer_id = read_one(pyboy, symbols, "wOtherTrainerID")
        if signature != last_signature or step % args.log_every == 0 or chosen:
            log.append(watch_line(pyboy, symbols, frame, f"DRIVE_A_{step + 1:03d}"))
            last_signature = signature
        if chosen:
            if trainer_class != trainer_constant.class_id or trainer_id != trainer_constant.trainer_id:
                diagnostic = args.out_dir / f"{route.capture_id}_wrong_trainer_{frame:04d}.state"
                save_state(pyboy, diagnostic)
                raise StateFactoryError(
                    f"{route.capture_id}: got chosen move for trainer "
                    f"{trainer_class:02x}:{trainer_id:02x}, expected "
                    f"{trainer_constant.class_id:02x}:{trainer_constant.trainer_id:02x}; "
                    f"diagnostic state saved to {diagnostic}"
                )
            state_path = args.out_dir / f"{route.capture_id}_chosen_frame_{frame:04d}.state"
            save_state(pyboy, state_path)
            return RunResult(route=route, state_path=state_path, frame=frame)

    diagnostic = args.out_dir / f"{route.capture_id}_no_chosen_after_{frame:04d}.state"
    save_state(pyboy, diagnostic)
    log.append(watch_line(pyboy, symbols, frame, f"{route.capture_id.upper()}_NO_CHOSEN"))
    write_log(args.out_dir, route.capture_id, log)
    raise StateFactoryError(
        f"{route.capture_id}: no chosen move observed; diagnostic state saved to {diagnostic}"
    )


def write_manifest_hints(args: argparse.Namespace, results: list[RunResult]) -> None:
    hints = [
        {
            "boss": result.route.capture_id,
            "save_state": str(result.state_path.relative_to(ROOT)).replace("\\", "/"),
            "frame": result.frame,
        }
        for result in results
    ]
    hint_path = args.out_dir / "manifest_hints.json"
    hint_path.write_text(json.dumps(hints, indent=2) + "\n", encoding="utf-8")


def update_manifest_paths(manifest_path: Path, results: list[RunResult]) -> None:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    state_paths = {
        result.route.capture_id: str(result.state_path.relative_to(ROOT)).replace("\\", "/")
        for result in results
    }
    for entry in data.get("captures", []):
        if not isinstance(entry, dict):
            continue
        capture_id = entry.get("id")
        if capture_id not in state_paths:
            continue
        entry["save_state"] = state_paths[capture_id]
        entry["stop_after_first_capture"] = True
        entry["require_chosen_move"] = True
    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate boss AI decision-point PyBoy states via real map scripts."
    )
    parser.add_argument("--boss", choices=tuple(ROUTES), default="jasmine")
    parser.add_argument(
        "--all",
        action="store_true",
        help="generate states for every manifest-backed trainer route in this factory",
    )
    parser.add_argument("--rom", type=Path, default=capture.DEFAULT_ROM)
    parser.add_argument("--symbols", type=Path, default=capture.DEFAULT_SYMBOLS)
    parser.add_argument("--battery-save", type=Path, default=DEFAULT_BATTERY_SAVE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument(
        "--update-manifest",
        action="store_true",
        help="write generated save-state paths into the manifest; does not promote status",
    )
    parser.add_argument(
        "--input-wait-frames",
        type=int,
        default=0,
        help="frames to wait after each input; 0 uses each route default",
    )
    parser.add_argument(
        "--max-a-presses",
        type=int,
        default=0,
        help="override the route-specific A-press limit; 0 uses each route default",
    )
    parser.add_argument("--log-every", type=int, default=8)
    return parser


def selected_routes(args: argparse.Namespace) -> list[BossRoute]:
    if args.all:
        ids = route_ids_from_manifest(args.manifest)
        return [ROUTES[capture_id] for capture_id in ids if capture_id in ROUTES]
    return [ROUTES[args.boss]]


def run_route(
    args: argparse.Namespace,
    route: BossRoute,
    symbols: dict[str, capture.Symbol],
    event_constants: dict[str, int],
    map_constants: dict[str, tuple[int, int]],
    trainer_constants: dict[tuple[str, str], TrainerConstant],
) -> tuple[RunResult, Path]:
    work_rom = prepare_work_rom(args)
    log: list[str] = [
        f"ROUTE {route.capture_id}",
        f"ROM_SOURCE {capture.display_path(args.rom)}",
        f"ROM_WORK {capture.display_path(work_rom)}",
        f"BATTERY_SAVE {capture.display_path(args.battery_save)}",
        "INPUT_WAIT_FRAMES "
        f"{route.input_wait_frames if args.input_wait_frames == 0 else args.input_wait_frames}",
    ]
    pyboy = open_pyboy(work_rom)
    try:
        frame = boot_continue(pyboy, symbols, log)
        frame = setup_route_entry(
            pyboy,
            route,
            symbols,
            event_constants,
            map_constants,
            args.out_dir,
            log,
            frame,
        )
        trainer_constant = expected_trainer(route, trainer_constants)
        result = drive_to_chosen_move(
            pyboy,
            route,
            trainer_constant,
            symbols,
            args,
            log,
            frame,
        )
        log.append(watch_line(pyboy, symbols, result.frame, f"{route.capture_id.upper()}_CHOSEN"))
    finally:
        pyboy.stop(save=False)

    log_path = write_log(args.out_dir, route.capture_id, log)
    return result, log_path


def main() -> int:
    args = build_parser().parse_args()
    if args.input_wait_frames < 0:
        fail("--input-wait-frames must be 0 or positive")
    if args.max_a_presses < 0:
        fail("--max-a-presses must be 0 or positive")
    if args.log_every <= 0:
        fail("--log-every must be positive")

    routes = selected_routes(args)
    symbols = capture.parse_symbols(args.symbols)
    require_symbols(symbols, routes)
    event_constants = parse_simple_consts(EVENT_FLAGS)
    map_constants = parse_map_consts(MAP_CONSTANTS)
    trainer_constants = parse_trainer_consts(TRAINER_CONSTANTS)

    results: list[RunResult] = []
    for route in routes:
        try:
            result, log_path = run_route(
                args,
                route,
                symbols,
                event_constants,
                map_constants,
                trainer_constants,
            )
        except StateFactoryError as exc:
            fail(str(exc))
        results.append(result)
        print(f"{route.capture_id}: state={capture.display_path(result.state_path)}")
        print(f"{route.capture_id}: frame={result.frame}")
        print(f"{route.capture_id}: log={capture.display_path(log_path)}")

    write_manifest_hints(args, results)
    if args.update_manifest:
        update_manifest_paths(args.manifest, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
