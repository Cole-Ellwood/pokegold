#!/usr/bin/env python3
"""Build the synthetic shared switch-loop Boss AI trace state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.trace import boss_ai_state_factory as factory
from tools.trace import boss_ai_trace_capture as capture
from tools.trace import runtime as trace_runtime


DEFAULT_BASE_STATE = ROOT / ".local" / "tmp" / "boss_state_factory" / "jasmine_chosen_frame_4520.state"
DEFAULT_OUT = ROOT / ".local" / "tmp" / "boss_state_factory" / "shared_switch_loop_frame_200.state"
DEFAULT_LOG = ROOT / ".local" / "tmp" / "boss_state_factory" / "shared_switch_loop_fixture.log"
MANIFEST = ROOT / "audit" / "boss_ai_trace" / "live_capture_manifest.json"
EARTHQUAKE = 0x59
JASMINE_SWITCH_THRESHOLD_WITHOUT_LOOP = 74
ANTI_LOOP_PENALTY = 10
PARTYMON_STRUCT_LENGTH = 0x30


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def write_word(pyboy, symbols: dict[str, capture.Symbol], name: str, value: int) -> None:
    symbol = symbols[name]
    factory.write_byte(pyboy, symbol, (value >> 8) & 0xFF)
    factory.write_byte(pyboy, capture.Symbol(symbol.bank, symbol.address + 1), value & 0xFF)


def write_party_hp(
    pyboy,
    symbols: dict[str, capture.Symbol],
    zero_based_index: int,
    value: int,
) -> None:
    symbol = symbols["wOTPartyMon1HP"]
    address = symbol.address + zero_based_index * PARTYMON_STRUCT_LENGTH
    factory.write_byte(pyboy, capture.Symbol(symbol.bank, address), (value >> 8) & 0xFF)
    factory.write_byte(pyboy, capture.Symbol(symbol.bank, address + 1), value & 0xFF)


def read_word(pyboy, symbols: dict[str, capture.Symbol], name: str) -> int:
    symbol = symbols[name]
    high = capture.read_byte(pyboy, symbol)
    low = capture.read_byte(pyboy, capture.Symbol(symbol.bank, symbol.address + 1))
    return (high << 8) | low


def zero_trace(pyboy, symbols: dict[str, capture.Symbol]) -> None:
    for name, size in capture.TRACE_FIELDS:
        symbol = symbols[name]
        for offset in range(size):
            factory.write_byte(
                pyboy,
                capture.Symbol(symbol.bank, symbol.address + offset),
                0,
            )


def prepare_repeated_switch_state(pyboy, symbols: dict[str, capture.Symbol]) -> None:
    max_hp = read_word(pyboy, symbols, "wEnemyMonMaxHP")
    factory.write_one(pyboy, symbols, "wCurOTMon", 0)
    factory.write_one(pyboy, symbols, "wBossAILastSwitchedOut", 2)
    factory.write_one(pyboy, symbols, "wBossAISwitchCooldown", 2)
    factory.write_one(pyboy, symbols, "wEnemySwitchMonParam", 0)
    factory.write_one(pyboy, symbols, "wEnemySwitchMonIndex", 0)
    factory.write_one(pyboy, symbols, "wPlayerUsedMoves", EARTHQUAKE)
    factory.write_one(pyboy, symbols, "wLastPlayerCounterMove", 0)
    write_word(pyboy, symbols, "wEnemyMonHP", max_hp)
    write_word(pyboy, symbols, "wOTPartyMon2HP", 100)
    for party_index in (2, 3, 4):
        write_party_hp(pyboy, symbols, party_index, 0)
    zero_trace(pyboy, symbols)


def advance_with_a_presses(pyboy, frames: int) -> None:
    for frame in range(frames):
        if frame % 30 == 0:
            pyboy.button("a", delay=4)
        pyboy.tick(1, False, False)


def verify_fixture(pyboy, symbols: dict[str, capture.Symbol], frames: int) -> list[str]:
    lines: list[str] = []
    for frame in range(frames + 1):
        values = capture.read_trace_values(pyboy, symbols)
        confidence = values["wBossAITraceSwitchConfidence"][0]
        if confidence:
            param = values["wEnemySwitchMonParam"][0]
            target = (param & 0x0F) + 1
            last_out = values["wBossAILastSwitchedOut"][0]
            cooldown = values["wBossAISwitchCooldown"][0]
            switch_index = values["wEnemySwitchMonIndex"][0]
            threshold_with_loop = JASMINE_SWITCH_THRESHOLD_WITHOUT_LOOP + ANTI_LOOP_PENALTY
            lines.append(f"observed_frame={frame}")
            lines.append(f"switch_confidence={confidence}")
            lines.append(f"switch_param={param:02x}")
            lines.append(f"proposed_target_1_based={target}")
            lines.append(f"last_switched_out_1_based={last_out}")
            lines.append(f"switch_cooldown={cooldown}")
            lines.append(f"enemy_switch_index={switch_index}")
            lines.append(f"threshold_without_loop={JASMINE_SWITCH_THRESHOLD_WITHOUT_LOOP}")
            lines.append(f"threshold_with_loop={threshold_with_loop}")
            if target != last_out:
                fail("fixture did not propose the last switched-out target")
            if cooldown == 0:
                fail("fixture lost switch cooldown before the switch check")
            if confidence < JASMINE_SWITCH_THRESHOLD_WITHOUT_LOOP:
                fail("fixture confidence would not switch even without loop penalty")
            if confidence >= threshold_with_loop:
                fail("fixture confidence is too high to prove loop penalty suppression")
            if switch_index != 0:
                fail("fixture set a switch index despite the loop penalty")
            return lines
        pyboy.tick(1, False, False)
    fail(f"no switch confidence observed within {frames} verification frames")


def update_manifest(state_path: Path) -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for entry in data["captures"]:
        if entry.get("id") != "shared_switch_loop":
            continue
        entry["save_state"] = trace_runtime.display_path(state_path)
        entry["watch_frames"] = 180
        entry["poll_every"] = 1
        entry["stop_after_first_capture"] = True
        entry["require_chosen_move"] = False
        entry["notes"] = (
            "synthetic Jasmine battle context; public Earthquake pressure proposes "
            "returning to the last switched-out mon; confidence 80 beats Jasmine's "
            "74 threshold but loses to the 84 anti-loop threshold"
        )
        MANIFEST.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return
    fail("manifest is missing shared_switch_loop capture")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-state", type=Path, default=DEFAULT_BASE_STATE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--advance-frames", type=int, default=200)
    parser.add_argument("--verify-frames", type=int, default=120)
    parser.add_argument("--update-manifest", action="store_true")
    args = parser.parse_args()

    if not args.base_state.exists():
        fail(f"missing base state: {args.base_state}")

    symbols = capture.parse_symbols(capture.DEFAULT_SYMBOLS)
    capture.require_symbols(symbols)
    pyboy = trace_runtime.open_pyboy(capture.DEFAULT_ROM, "PyBoy is required to build the fixture")
    try:
        trace_runtime.disable_realtime(pyboy)
        with args.base_state.open("rb") as fh:
            pyboy.load_state(fh)
        prepare_repeated_switch_state(pyboy, symbols)
        advance_with_a_presses(pyboy, args.advance_frames)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("wb") as fh:
            pyboy.save_state(fh)
        observed = verify_fixture(pyboy, symbols, args.verify_frames)
    finally:
        pyboy.stop(save=False)

    log_lines = [
        "shared_switch_loop_fixture=PASS",
        f"base_state={trace_runtime.display_path(args.base_state)}",
        f"out={trace_runtime.display_path(args.out)}",
        f"advance_frames={args.advance_frames}",
        *observed,
        "setup=cur_ot=0,last_switched_out=2,cooldown=2,public_move=EARTHQUAKE,enemy_hp=full",
        "party_setup=only last-switched-out backup remains available",
    ]
    args.log.parent.mkdir(parents=True, exist_ok=True)
    args.log.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    if args.update_manifest:
        update_manifest(args.out)
    print("\n".join(log_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
