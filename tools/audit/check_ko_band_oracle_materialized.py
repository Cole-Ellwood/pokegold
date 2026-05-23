#!/usr/bin/env python3
"""Materialized P2b KO-band oracle smoke.

This is intentionally narrower than a full route replay. It executes the
new ROM helper `BossAI_ApplyKOBandOraclePressure` in `pokegold_trace.gbc`
through PyBoy with a concrete public-info scenario:

  Koga slot 2 (Muk) has Sludge Bomb coverage into a Grass active.

The incoming exact pressure score is 3, which is one below the full-HP KO
threshold used by `BossAI_CurrentEnemyMoveHasKOPressure`. A valid matchup-table
row must raise it to 4; a table-missing trainer id must leave it at 3.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_debugger.rom_contribution_trace import MemoryPatch
from tools.boss_ai_debugger.rom_contribution_trace import apply_memory_patches
from tools.trace import boss_ai_trace_capture as capture
from tools.trace import runtime as trace_runtime


TRACE_ROM = ROOT / "pokegold_trace.gbc"
TRACE_SYM = ROOT / "pokegold_trace.sym"
RETURN_LOOP = 0xC000
STACK_TOP = 0xCFFE
INPUT_PRESSURE_SCORE = 3
FULL_HP_KO_THRESHOLD = 4
MISSING_TRAINER_ID = 99


def check_static_integration() -> list[str]:
    problems: list[str] = []
    oracle_source = ROOT / "engine" / "battle" / "ai" / "ko_band_oracle.asm"
    move_policy = ROOT / "engine" / "battle" / "ai" / "boss_policy_move.asm"
    main_source = ROOT / "main.asm"
    if "BossAI_ApplyKOBandOraclePressure::" not in oracle_source.read_text(
        encoding="utf-8"
    ):
        problems.append("missing BossAI_ApplyKOBandOraclePressure export")
    policy_text = move_policy.read_text(encoding="utf-8")
    if "farcall BossAI_ApplyKOBandOraclePressure" not in policy_text:
        problems.append("boss_policy_move.asm does not farcall the KO-band oracle")
    if re.search(r"(?m)^\s*call\s+BossAI_ApplyKOBandOraclePressure\b", policy_text):
        problems.append("boss_policy_move.asm has unsafe in-bank call to ROMX oracle")
    main_text = main_source.read_text(encoding="utf-8")
    if 'INCLUDE "engine/battle/ai/ko_band_oracle.asm"' not in main_text:
        problems.append("main.asm does not include ko_band_oracle.asm")
    return problems


def parse_constants(path: Path, names: set[str]) -> dict[str, int]:
    values: dict[str, int] = {}
    current = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip().startswith("const_def"):
            parts = raw.split()
            current = int(parts[1], 0) if len(parts) > 1 else 0
            continue
        if raw.strip().startswith("const_next"):
            parts = raw.split()
            if len(parts) != 2:
                raise AssertionError(f"malformed const_next in {path}: {raw}")
            current = int(parts[1], 0)
            continue
        match = re.match(r"\s*const\s+(\w+)", raw)
        if not match:
            continue
        name = match.group(1)
        if name in names:
            values[name] = current
        current += 1
    missing = sorted(names - set(values))
    if missing:
        raise AssertionError(f"{path.relative_to(ROOT)} missing constants: {missing}")
    return values


def parse_trainer_constants() -> tuple[dict[str, int], dict[str, int]]:
    classes: dict[str, int] = {}
    ids: dict[str, int] = {}
    class_value = 0
    trainer_id_value = 1
    current_class = ""
    for raw in (ROOT / "constants" / "trainer_constants.asm").read_text(
        encoding="utf-8"
    ).splitlines():
        class_match = re.match(r"\s*trainerclass\s+(\w+)", raw)
        if class_match:
            trainer_id_value = 1
            current_class = class_match.group(1)
            classes[current_class] = class_value
            class_value += 1
            continue
        id_match = re.match(r"\s*const\s+(\w+)", raw)
        if id_match and current_class:
            ids[id_match.group(1)] = trainer_id_value
            trainer_id_value += 1
    for required in ("KOGA",):
        if required not in classes:
            raise AssertionError(f"missing trainer class constant {required}")
    for required in ("KOGA1",):
        if required not in ids:
            raise AssertionError(f"missing trainer id constant {required}")
    return classes, ids


def run_oracle_helper(*, trainer_id: int) -> dict[str, int | bool]:
    types = parse_constants(ROOT / "constants" / "type_constants.asm", {"GRASS"})
    trainer_classes, trainer_ids = parse_trainer_constants()
    symbols = capture.parse_symbols(TRACE_SYM)
    target = symbols["BossAI_ApplyKOBandOraclePressure"]

    pyboy = trace_runtime.open_pyboy(
        TRACE_ROM,
        "PyBoy is required for materialized KO-band oracle smoke",
    )
    trace_runtime.disable_realtime(pyboy)
    try:
        pyboy.memory[0xFF70] = 1
        pyboy.memory[0x2000] = target.bank
        pyboy.memory[symbols["hROMBank"].address] = target.bank
        apply_memory_patches(
            pyboy,
            symbols,
            [
                MemoryPatch("wTrainerClass", 0, trainer_classes["KOGA"]),
                MemoryPatch("wOtherTrainerID", 0, trainer_id),
                # Koga slot 2 is Muk in data/trainers/parties.asm.
                MemoryPatch("wCurOTMon", 0, 2),
                # Exact current move is already known super-effective.
                MemoryPatch("wTypeMatchup", 0, 20),
                MemoryPatch("wBattleMonType1", 0, types["GRASS"]),
                MemoryPatch("wBattleMonType2", 0, types["GRASS"]),
            ],
        )

        # Return into a WRAM `jr .` loop so one PyBoy frame cannot run onward
        # into unrelated ROM code and overwrite the helper's output registers.
        pyboy.memory[RETURN_LOOP] = 0x18
        pyboy.memory[RETURN_LOOP + 1] = 0xFE
        pyboy.register_file.SP = STACK_TOP
        pyboy.memory[STACK_TOP] = RETURN_LOOP & 0xFF
        pyboy.memory[STACK_TOP + 1] = RETURN_LOOP >> 8
        pyboy.register_file.B = INPUT_PRESSURE_SCORE
        pyboy.register_file.PC = target.address
        pyboy.tick(1, False, False)
        return {
            "pc": int(pyboy.register_file.PC),
            "a": int(pyboy.register_file.A),
            "f": int(pyboy.register_file.F),
            "b": int(pyboy.register_file.B),
            "carry": bool(int(pyboy.register_file.F) & 0x10),
            "trainer_id": trainer_id,
            "expected_trainer_id": trainer_ids["KOGA1"],
        }
    finally:
        pyboy.stop(save=False)


def main() -> int:
    static_problems = check_static_integration()
    if static_problems:
        for problem in static_problems:
            print(f"FAIL: {problem}")
        return 1
    if not TRACE_ROM.exists() or not TRACE_SYM.exists():
        print("FAIL: pokegold_trace.gbc/pokegold_trace.sym are required")
        return 1
    _trainer_classes, trainer_ids = parse_trainer_constants()
    valid = run_oracle_helper(trainer_id=trainer_ids["KOGA1"])
    missing = run_oracle_helper(trainer_id=MISSING_TRAINER_ID)

    problems: list[str] = []
    if valid["pc"] != RETURN_LOOP:
        problems.append(f"valid case did not return to sentinel: pc={valid['pc']:04x}")
    if missing["pc"] != RETURN_LOOP:
        problems.append(
            f"missing-table case did not return to sentinel: pc={missing['pc']:04x}"
        )
    if valid["b"] != FULL_HP_KO_THRESHOLD:
        problems.append(
            f"valid table row should raise b to {FULL_HP_KO_THRESHOLD}, got {valid['b']}"
        )
    if missing["b"] != INPUT_PRESSURE_SCORE:
        problems.append(
            f"missing table row should leave b at {INPUT_PRESSURE_SCORE}, got {missing['b']}"
        )
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1

    print(
        "PASS: KO-band oracle integration and materialized threshold flip: "
        f"KOGA1 slot 2 Grass target {INPUT_PRESSURE_SCORE}->{valid['b']}; "
        f"missing trainer id remains {missing['b']}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
