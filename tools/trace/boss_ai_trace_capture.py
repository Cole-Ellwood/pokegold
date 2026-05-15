#!/usr/bin/env python3
"""Capture or print Boss AI trace WRAM fields from a trace ROM."""

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
MOVE_CONSTANTS = ROOT / "constants" / "move_constants.asm"

TRACE_FIELDS: tuple[tuple[str, int], ...] = (
    ("wBossAITraceTopMoves", 3),
    ("wBossAITraceTopScores", 3),
    ("wBossAITracePreModelScores", 4),
    ("wBossAITracePostModelScores", 4),
    ("wBossAITraceChosenMove", 1),
    ("wBossAITraceSwitchConfidence", 1),
    ("wBossAITracePlanId", 1),
    ("wBossAITracePlanPhase", 1),
    ("wBossAITracePlanConfidence", 1),
    ("wBossAITracePlausibleMask", 4),
    ("wBossAITraceRiskFlags", 1),
    ("wBossAITraceLookaheadBonusTop", 3),
    ("wBossAIRevealedMovesBitmap", 24),
)

SELECTOR_REPLAY_FIELDS: tuple[tuple[str, int], ...] = (
    ("wBossAITier", 1),
    ("wEnemyMonMoves", 4),
    ("wEnemyAIMoveScores", 4),
    ("wCurEnemyMoveNum", 1),
    ("wCurEnemyMove", 1),
)

CONTEXT_FIELDS: tuple[tuple[str, int], ...] = (
    ("wEnemySwitchMonParam", 1),
    ("wEnemySwitchMonIndex", 1),
    ("wBossAILastSwitchedOut", 1),
    ("wBossAISwitchCooldown", 1),
    ("wCurOTMon", 1),
)

RISK_FLAGS = (
    (0, "plausible-risk-or-scout-trigger"),
    (1, "scout-move-chosen"),
    (2, "scout-pivot-switch"),
    (3, "haki-oracle-fired"),
)

METADATA_KEYS = (
    "trace_rom",
    "trace_rom_sha256",
    "trace_symbols",
    "trace_symbols_sha256",
    "boss",
    "turn",
    "enemy",
    "player",
    "frame",
    "capture_index",
    "notes",
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


def parse_move_names(path: Path) -> dict[int, str]:
    if not path.exists():
        return {}
    names: dict[int, str] = {}
    index = 0
    in_table = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split(";", 1)[0].strip()
        if line == "const_def":
            in_table = True
            index = 0
            continue
        if not in_table:
            continue
        if not line.startswith("const "):
            if line.startswith("DEF NUM_ATTACKS"):
                break
            continue
        parts = line.split()
        if len(parts) >= 2:
            names[index] = parts[1]
            index += 1
    return names


def require_symbols(symbols: dict[str, Symbol]) -> None:
    missing = [
        name
        for name, _size in TRACE_FIELDS + SELECTOR_REPLAY_FIELDS + CONTEXT_FIELDS
        if name not in symbols
    ]
    if missing:
        fail("missing required trace symbols: " + ", ".join(missing))


def format_addr(symbol: Symbol) -> str:
    return f"{symbol.bank:02x}:{symbol.address:04x}"


def read_byte(pyboy, symbol: Symbol) -> int:
    return trace_runtime.read_byte(pyboy, symbol)


def read_range(pyboy, symbol: Symbol, size: int) -> list[int]:
    return trace_runtime.read_range(pyboy, symbol, size)


def decode_move(move_id: int, move_names: dict[int, str]) -> str:
    name = move_names.get(move_id)
    if not name:
        return f"#{move_id:02x}"
    return name


def hex_bytes(values: list[int]) -> str:
    return " ".join(f"{value:02x}" for value in values)


def csv_bytes(values: list[int]) -> str:
    return ",".join(str(value) for value in values)


def csv_score_deltas(before: list[int], after: list[int]) -> str:
    deltas = []
    for left, right in zip(before, after):
        if left == 0xFF or right == 0xFF:
            deltas.append("na")
        else:
            deltas.append(f"{right - left:+d}")
    return ",".join(deltas)


def decode_risk_flags(value: int) -> str:
    active = [name for bit, name in RISK_FLAGS if value & (1 << bit)]
    return ",".join(active) if active else "none"


def format_metadata_lines(metadata: dict[str, str]) -> list[str]:
    lines: list[str] = []
    for key in METADATA_KEYS:
        if metadata.get(key):
            lines.append(f"{key}={metadata[key]}")
    return lines


def format_capture(
    values: dict[str, list[int]],
    move_names: dict[int, str],
    metadata: dict[str, str],
) -> str:
    top_moves = values["wBossAITraceTopMoves"]
    top_scores = values["wBossAITraceTopScores"]
    chosen = values["wBossAITraceChosenMove"][0]
    risk_flags = values["wBossAITraceRiskFlags"][0]
    move_ids = values["wEnemyMonMoves"]
    move_scores = values["wEnemyAIMoveScores"]
    pre_model_scores = values["wBossAITracePreModelScores"]
    post_model_scores = values["wBossAITracePostModelScores"]

    top_pairs = []
    for move, score in zip(top_moves, top_scores):
        top_pairs.append(f"{decode_move(move, move_names)}:{score}")

    lines = format_metadata_lines(metadata)

    lines.extend(
        [
            f"tier={values['wBossAITier'][0]}",
            f"move_ids={csv_bytes(move_ids)}",
            f"move_scores={csv_bytes(move_scores)}",
            f"pre_model_scores={csv_bytes(pre_model_scores)}",
            f"post_model_scores={csv_bytes(post_model_scores)}",
            f"model_score_deltas={csv_score_deltas(pre_model_scores, post_model_scores)}",
            f"chosen_slot={values['wCurEnemyMoveNum'][0]}",
            f"cur_enemy_move_id={values['wCurEnemyMove'][0]}",
            f"top_moves={','.join(top_pairs)}",
            f"chosen={decode_move(chosen, move_names)}",
            f"chosen_id={chosen}",
            f"switch_confidence={values['wBossAITraceSwitchConfidence'][0]}",
            f"plan_id={values['wBossAITracePlanId'][0]}",
            f"plan_phase={values['wBossAITracePlanPhase'][0]}",
            f"plan_confidence={values['wBossAITracePlanConfidence'][0]}",
            f"plausible_mask={hex_bytes(values['wBossAITracePlausibleMask'])}",
            f"risk_flags={risk_flags:02x} ({decode_risk_flags(risk_flags)})",
            f"lookahead_bonus_top={csv_bytes(values['wBossAITraceLookaheadBonusTop'])}",
            f"revealed_masks={hex_bytes(values['wBossAIRevealedMovesBitmap'])}",
            (
                "switch_context="
                f"param={values['wEnemySwitchMonParam'][0]:02x},"
                f"index={values['wEnemySwitchMonIndex'][0]:02x},"
                f"last_out={values['wBossAILastSwitchedOut'][0]:02x},"
                f"cooldown={values['wBossAISwitchCooldown'][0]:02x},"
                f"cur_ot={values['wCurOTMon'][0]:02x}"
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def format_symbols(symbols: dict[str, Symbol]) -> str:
    lines = ["Boss AI trace symbols:"]
    for name, size in TRACE_FIELDS + SELECTOR_REPLAY_FIELDS + CONTEXT_FIELDS:
        symbol = symbols[name]
        if size == 1:
            lines.append(f"{name}={format_addr(symbol)}")
        else:
            end = symbol.address + size - 1
            lines.append(f"{name}={format_addr(symbol)}-{end:04x} ({size} bytes)")
    return "\n".join(lines) + "\n"


def trace_signature(values: dict[str, list[int]]) -> tuple[int, ...]:
    flattened: list[int] = []
    for name, _size in TRACE_FIELDS:
        flattened.extend(values[name])
    return tuple(flattened)


def has_decision_values(values: dict[str, list[int]]) -> bool:
    return (
        values["wBossAITraceChosenMove"][0] != 0
        or any(values["wBossAITraceTopMoves"])
        or values["wBossAITraceSwitchConfidence"][0] != 0
        or values["wBossAITraceRiskFlags"][0] != 0
    )


def has_completed_move_decision(values: dict[str, list[int]]) -> bool:
    return values["wBossAITraceChosenMove"][0] != 0


def read_trace_values(pyboy, symbols: dict[str, Symbol]) -> dict[str, list[int]]:
    return {
        name: read_range(pyboy, symbols[name], size)
        for name, size in TRACE_FIELDS + SELECTOR_REPLAY_FIELDS + CONTEXT_FIELDS
    }


def load_pyboy():
    return trace_runtime.load_pyboy(
        "PyBoy is required for WRAM capture. Use --symbols-only for debugger "
        "addresses, or install PyBoy. Import failed"
    )


def open_pyboy(args: argparse.Namespace):
    return trace_runtime.open_pyboy(
        args.rom,
        "PyBoy is required for WRAM capture. Use --symbols-only for debugger "
        "addresses, or install PyBoy. Import failed",
    )


def disable_realtime(pyboy) -> None:
    trace_runtime.disable_realtime(pyboy)


def load_state_if_requested(pyboy, args: argparse.Namespace) -> None:
    if args.save_state:
        if not args.save_state.exists():
            fail(f"missing save-state: {args.save_state}")
        with args.save_state.open("rb") as fh:
            pyboy.load_state(fh)


def capture_wram(args: argparse.Namespace, symbols: dict[str, Symbol]) -> dict[str, list[int]]:
    pyboy = open_pyboy(args)
    try:
        disable_realtime(pyboy)
        load_state_if_requested(pyboy, args)

        if args.frames:
            pyboy.tick(args.frames, False, False)

        return read_trace_values(pyboy, symbols)
    finally:
        pyboy.stop(save=False)


def watch_wram(
    args: argparse.Namespace,
    symbols: dict[str, Symbol],
    move_names: dict[int, str],
    metadata: dict[str, str],
) -> str:
    if args.watch_frames <= 0:
        fail("--watch-frames must be greater than 0")
    if args.poll_every <= 0:
        fail("--poll-every must be greater than 0")

    pyboy = open_pyboy(args)
    captures: list[str] = []
    last_signature: tuple[int, ...] | None = None
    frame = 0
    capture_index = 0
    try:
        disable_realtime(pyboy)
        load_state_if_requested(pyboy, args)

        while frame <= args.watch_frames:
            values = read_trace_values(pyboy, symbols)
            signature = trace_signature(values)
            has_capture_values = (
                has_completed_move_decision(values)
                if args.require_chosen_move
                else has_decision_values(values)
            )
            if (
                signature != last_signature
                and (args.include_zero_snapshots or has_capture_values)
            ):
                capture_index += 1
                capture_meta = dict(metadata)
                capture_meta["frame"] = str(frame)
                capture_meta["capture_index"] = str(capture_index)
                captures.append(format_capture(values, move_names, capture_meta).rstrip())
                last_signature = signature
                if args.stop_after_first_capture:
                    break

            if frame == args.watch_frames:
                break
            step = min(args.poll_every, args.watch_frames - frame)
            pyboy.tick(step, False, False)
            frame += step
    finally:
        pyboy.stop(save=False)

    if not captures:
        if args.require_chosen_move:
            fail(
                "no completed move-decision capture observed "
                f"within {args.watch_frames} watched frames"
            )
        lines = format_metadata_lines(metadata)
        lines.extend(
            [
                "no_captures=true",
                f"watched_frames={args.watch_frames}",
                "notes=no nonzero Boss AI trace field changes were observed",
            ]
        )
        return "\n".join(lines) + "\n"

    return "\n---\n".join(captures) + "\n"


def write_or_print(text: str, out: Path | None) -> None:
    if out is None:
        print(text, end="")
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print or capture Boss AI trace WRAM fields."
    )
    parser.add_argument("--rom", type=Path, default=DEFAULT_ROM)
    parser.add_argument("--symbols", type=Path, default=DEFAULT_SYMBOLS)
    parser.add_argument("--save-state", type=Path)
    parser.add_argument("--frames", type=int, default=0)
    parser.add_argument("--watch-frames", type=int, default=0)
    parser.add_argument("--poll-every", type=int, default=1)
    parser.add_argument("--include-zero-snapshots", action="store_true")
    parser.add_argument("--stop-after-first-capture", action="store_true")
    parser.add_argument(
        "--require-chosen-move",
        action="store_true",
        help="watch until a completed move choice is traced",
    )
    parser.add_argument("--symbols-only", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--boss", default="")
    parser.add_argument("--turn", default="")
    parser.add_argument("--enemy", default="")
    parser.add_argument("--player", default="")
    parser.add_argument("--notes", default="")
    return parser


def build_trace_basis_metadata(args: argparse.Namespace) -> dict[str, str]:
    return {
        "trace_rom": display_path(args.rom),
        "trace_rom_sha256": sha256_file(args.rom),
        "trace_symbols": display_path(args.symbols),
        "trace_symbols_sha256": sha256_file(args.symbols),
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    symbols = parse_symbols(args.symbols)
    require_symbols(symbols)

    if args.symbols_only:
        write_or_print(format_symbols(symbols), args.out)
        return 0

    move_names = parse_move_names(MOVE_CONSTANTS)
    metadata = build_trace_basis_metadata(args)
    metadata.update({
        "boss": args.boss,
        "turn": args.turn,
        "enemy": args.enemy,
        "player": args.player,
        "notes": args.notes,
    })
    if args.watch_frames:
        write_or_print(watch_wram(args, symbols, move_names, metadata), args.out)
    else:
        values = capture_wram(args, symbols)
        write_or_print(format_capture(values, move_names, metadata), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
