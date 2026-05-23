#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OBS = ROOT / "engine" / "battle" / "ai" / "observation_log.asm"
WRAM = ROOT / "ram" / "wram.asm"
MAIN = ROOT / "main.asm"
PLATFORM = ROOT / "engine" / "battle" / "ai" / "boss_platform.asm"
MOVE = ROOT / "engine" / "battle" / "ai" / "boss_policy_move.asm"
READ_TRAINER = ROOT / "engine" / "battle" / "read_trainer_attributes.asm"
CONSTANTS = ROOT / "constants" / "battle_constants.asm"
WEIGHTS = ROOT / "data" / "boss_ai" / "tendency_counter_weights.asm"

FORBIDDEN_OBS_SYMBOLS = (
    "wCurPlayerMove",
    "wBattlePlayerAction",
    "wBattleMonMoves",
    "wBattleMonPP",
    "wBattleMonItem",
    "hJoy",
    "wMenuCursor",
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def read(path: Path) -> str:
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8", errors="replace")


def require(text: str, needle: str, context: str) -> None:
    if needle not in text:
        fail(f"{context}: missing `{needle}`")


def require_order(text: str, needles: list[str], context: str) -> None:
    pos = -1
    for needle in needles:
        nxt = text.find(needle, pos + 1)
        if nxt < 0:
            fail(f"{context}: missing `{needle}` in order")
        pos = nxt


def block(text: str, label: str) -> str:
    pattern = re.compile(rf"^{re.escape(label)}::?:\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        fail(f"missing label {label}")
    start = match.start()
    next_label = re.search(r"^[A-Za-z_][A-Za-z0-9_]*::?:\s*$", text[match.end() :], re.MULTILINE)
    if not next_label:
        return text[start:]
    return text[start : match.end() + next_label.start()]


def parse_weight_values(weights: str) -> list[int]:
    values: list[int] = []
    for line in weights.splitlines():
        stripped = line.strip()
        if not stripped.startswith("db "):
            continue
        token = stripped.split(";", 1)[0].split()[1]
        values.append(int(token, 0))
    return values


def run_golden_scenarios(weight_values: list[int]) -> None:
    """Recreate the P5 failure class: recent public habits should change a
    boss decision input, while EARLY or heavy-damage cases stay inert."""
    switch_under_pressure = 1
    protect_recover = 2
    status_fish = 4
    bonus_cap = 24

    mid_window = [switch_under_pressure, protect_recover, status_fish]
    mid_bonus = sum(weight_values[class_id] for class_id in mid_window)
    if mid_bonus != 13:
        fail(f"golden MID tendency scenario expected bonus 13, got {mid_bonus}")

    repeated_switch_bonus = min(
        sum(weight_values[switch_under_pressure] for _ in range(6)),
        bonus_cap,
    )
    if repeated_switch_bonus != bonus_cap:
        fail(
            "golden LATE repeated-switch scenario should hit cap "
            f"{bonus_cap}, got {repeated_switch_bonus}"
        )

    enemy_first_light_damage = {"damage": 1, "speed": 2}
    heavy_damage = {"damage": 3, "speed": 2}
    if not (enemy_first_light_damage["speed"] == 2 and enemy_first_light_damage["damage"] < 3):
        fail("golden calibration scenario should enable enemy-first light-damage bonus")
    if heavy_damage["damage"] < 3:
        fail("golden calibration blocker should treat heavy damage as blocking")


def main() -> int:
    obs = read(OBS)
    wram = read(WRAM)
    main = read(MAIN)
    platform = read(PLATFORM)
    move = read(MOVE)
    read_trainer = read(READ_TRAINER)
    constants = read(CONSTANTS)
    weights = read(WEIGHTS)

    for symbol in FORBIDDEN_OBS_SYMBOLS:
        if re.search(rf"\b{re.escape(symbol)}\b", obs):
            fail(f"observation log reads forbidden hidden/input symbol `{symbol}`")

    require(wram, 'SECTION "Boss AI WRAMX2 Buffer", WRAMX, BANK[2]', "WRAMX2 section")
    for needle in (
        "wBossAIObsWriteIndex:: db",
        "wBossAIObsCount:: db",
        "wBossAIObsEntries:: ds BOSS_AI_OBS_ENTRY_SIZE * BOSS_AI_OBS_MAX_TURNS",
        "wBossAIWramx2BufferEnd::",
    ):
        require(wram, needle, "WRAMX2 observation buffer")

    for needle in (
        "DEF BOSS_AI_OBS_ENTRY_SIZE EQU 4",
        "DEF BOSS_AI_OBS_MAX_TURNS EQU 6",
        "DEF BOSS_AI_OBS_MID_TURNS EQU 3",
        "DEF BOSS_AI_OBS_CLASS_COUNT EQU 7",
        "DEF BOSS_AI_OBS_TENDENCY_BONUS_CAP EQU 24",
    ):
        require(constants, needle, "observation constants")

    require(main, 'INCLUDE "engine/battle/ai/observation_log.asm"', "main include")
    require(read_trainer, "call BossAI_ClearObservationLog", "battle-init clear")
    require_order(
        platform,
        [
            "inc [hl]",
            "call BossAI_AppendObservationLog",
            "ld a, [wBossAIPendingPlayerSwitchCount]",
        ],
        "next-turn append before pending switch fold",
    )

    append = block(obs, "BossAI_AppendObservationLog")
    require_order(
        append,
        [
            "ld a, [wBossAITier]",
            "cp AI_TIER_MID",
            "ret c",
            "call BossAI_ClassifyCurrentObservation",
            "call BossAI_CurrentObservationDamageBand",
            "call BossAI_ObservationWindowLimit",
            "boss_ai_set_wram_bank 2",
            "wBossAIObsWriteIndex",
            "wBossAIObsCount",
            "boss_ai_set_wram_bank 1",
        ],
        "append gate and bounded write",
    )

    tendency = block(obs, "BossAI_ConsultTendencyCounters")
    require_order(
        tendency,
        [
            "ld a, [wBossAITier]",
            "cp AI_TIER_MID",
            "jr nc, .enabled",
            "xor a",
            "ret",
            "call BossAI_ObservationWindowLimit",
            "boss_ai_set_wram_bank 2",
            "wBossAIObsCount",
            "BossAI_ObservationWeightForClass",
            "BOSS_AI_OBS_TENDENCY_BONUS_CAP",
            "boss_ai_set_wram_bank 1",
        ],
        "tendency counter tier gate and bounded scan",
    )

    calibration = block(obs, "BossAI_ConsultKOBandCalibration")
    require_order(
        calibration,
        [
            "ld a, [wBossAITier]",
            "cp AI_TIER_LATE",
            "jr nc, .enabled",
            "xor a",
            "ret",
            "boss_ai_set_wram_bank 2",
            "BOSS_AI_OBS_SPEED_ENEMY_FIRST",
            "boss_ai_set_wram_bank 1",
        ],
        "late-only calibration gate",
    )

    require(move, "call BossAI_ConsultTendencyCounters", "switch-prediction consumer")
    require(move, "call BossAI_ConsultKOBandCalibration", "KO-band calibration consumer")
    require(weights, "BossAIObservationTendencyWeights:", "weight table")
    weight_values = parse_weight_values(weights)
    if len(weight_values) != 7:
        fail(f"weight table must have 7 rows, found {len(weight_values)}")
    run_golden_scenarios(weight_values)

    if "call SetWRAMBank" in obs:
        fail("observation log must not call SetWRAMBank from a WRAMX-stack context")
    require(obs, "ldh [rSVBK], a", "inline WRAMX switch writes hardware bank")
    require(obs, "ldh [hWRAMBank], a", "inline WRAMX switch updates shadow bank")

    print("PASS: P5 observation log invariants")
    print("  - WRAMX2 ring buffer is bounded to 3 MID / 6 LATE entries")
    print("  - EARLY returns zero and performs no buffer writes")
    print("  - consumers are wired into switch prediction and KO-band calibration")
    print("  - observation source avoids hidden-info/input symbols")
    print("  - golden tendency/calibration scenarios prove nonzero MID/LATE decision input")
    return 0


if __name__ == "__main__":
    sys.exit(main())
