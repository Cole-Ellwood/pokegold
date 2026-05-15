#!/usr/bin/env python3
"""Replay a captured PyBoy state through a boss move choice."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.trace import boss_ai_trace_capture as capture
from tools.trace import runtime as trace_runtime


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def open_pyboy(rom: Path):
    pyboy = trace_runtime.open_pyboy(
        rom,
        "PyBoy is required for state replay. Import failed",
    )
    trace_runtime.disable_realtime(pyboy)
    return pyboy


def load_state(pyboy, path: Path) -> None:
    if not path.exists():
        fail(f"missing save-state: {path}")
    with path.open("rb") as fh:
        pyboy.load_state(fh)


def has_replay_decision(values: dict[str, list[int]]) -> bool:
    return (
        values["wCurEnemyMove"][0] != 0
        or values["wBossAITraceChosenMove"][0] != 0
    )


def replay_state(args: argparse.Namespace) -> dict[str, list[int]]:
    symbols = capture.parse_symbols(args.symbols)
    capture.require_symbols(symbols)
    pyboy = open_pyboy(args.rom)
    try:
        load_state(pyboy, args.save_state)
        if args.button:
            pyboy.button(args.button, delay=args.button_delay)
        for _frame in range(args.watch_frames + 1):
            values = capture.read_trace_values(pyboy, symbols)
            if has_replay_decision(values):
                return values
            pyboy.tick(1, False, False)
        fail(f"no boss move choice observed within {args.watch_frames} frames")
    finally:
        pyboy.stop(save=False)
    raise AssertionError("unreachable")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay a saved state until a boss move choice is observed."
    )
    parser.add_argument("--rom", type=Path, default=capture.DEFAULT_ROM)
    parser.add_argument("--symbols", type=Path, default=capture.DEFAULT_SYMBOLS)
    parser.add_argument("--save-state", type=Path, required=True)
    parser.add_argument("--button", default="a")
    parser.add_argument("--button-delay", type=int, default=8)
    parser.add_argument("--watch-frames", type=int, default=60)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--boss", default="")
    parser.add_argument("--turn", default="")
    parser.add_argument("--enemy", default="")
    parser.add_argument("--player", default="")
    parser.add_argument("--notes", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.button_delay < 0:
        fail("--button-delay must be non-negative")
    if args.watch_frames < 0:
        fail("--watch-frames must be non-negative")

    values = replay_state(args)
    move_names = capture.parse_move_names(capture.MOVE_CONSTANTS)
    metadata = capture.build_trace_basis_metadata(args)
    metadata.update(
        {
            "boss": args.boss,
            "turn": args.turn,
            "enemy": args.enemy,
            "player": args.player,
            "notes": args.notes,
        }
    )
    capture.write_or_print(capture.format_capture(values, move_names, metadata), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
