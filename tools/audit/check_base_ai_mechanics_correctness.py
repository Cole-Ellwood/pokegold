#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MOVE_AI_FILE = ROOT / "engine" / "battle" / "ai" / "move.asm"
SCORING_FILE = ROOT / "engine" / "battle" / "ai" / "scoring.asm"
REDUNDANT_FILE = ROOT / "engine" / "battle" / "ai" / "redundant.asm"
EFFECT_COMMANDS_FILE = ROOT / "engine" / "battle" / "effect_commands.asm"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read(path: Path) -> str:
    if not path.exists():
        fail(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def block(text: str, start: str, end: str) -> str:
    start_index = text.find(start)
    if start_index == -1:
        fail(f"missing block start: {start}")
    end_index = text.find(end, start_index + len(start))
    if end_index == -1:
        fail(f"missing block end after {start}: {end}")
    return text[start_index:end_index]


def require_contains(text: str, needle: str, context: str) -> None:
    require(needle in text, f"{context} missing `{needle}`")


def main() -> int:
    move_ai = read(MOVE_AI_FILE)
    scoring = read(SCORING_FILE)
    redundant = read(REDUNDANT_FILE)
    effect_commands = read(EFFECT_COMMANDS_FILE)

    apply_layers = block(move_ai, ".ApplyLayers:", ".BossModel")
    require_contains(
        apply_layers,
        "call .ApplyHeldItemMoveLegality",
        "base move scoring must run held-item legality before tier dispatch",
    )
    require(
        apply_layers.find("call .ApplyHeldItemMoveLegality")
        < apply_layers.find("ld a, [wBossAITier]"),
        "held-item legality must run before the boss-tier branch",
    )

    held_gate = block(move_ai, ".ApplyHeldItemMoveLegality:", "AIScoringPointers:")
    for needle in (
        "wEnemyMonItem",
        "callfar GetItemHeldEffect",
        "HELD_ASSAULT_VEST",
        "callfar IsMoveBlockedByAssaultVestFromE_Far",
        "callfar IsChoiceHeldEffectFromE_Far",
        "wEnemyChoiceLockedMove",
        "ld [hl], 80",
    ):
        require_contains(held_gate, needle, "shared held-item legality gate")

    ai_types = block(scoring, "AI_Types:", "AI_Offensive:")
    require_contains(ai_types, "callfar BattleCheckTypeMatchup", "AI_Types")
    require_contains(ai_types, "AIBlockMove", "AI_Types immune branch")

    ai_status = block(scoring, "AI_Status:", "AI_Risky:")
    require_contains(ai_status, "callfar BattleCheckTypeMatchup", "AI_Status")
    require_contains(ai_status, "AIBlockMove", "AI_Status immune branch")

    matchup = block(effect_commands, "BattleCheckTypeMatchup:", ".TypesLoop:")
    for needle in ("GROUND", "GetOpponentItem", "HELD_AIR_BALLOON", "wTypeMatchup"):
        require_contains(matchup, needle, "BattleCheckTypeMatchup Air Balloon gate")

    spikes_redundant = block(redundant, ".Spikes:", ".Foresight:")
    require_contains(spikes_redundant, "SCREENS_SPIKES_MASK", "Spikes redundancy")
    require_contains(spikes_redundant, "cp 3", "Spikes redundancy three-layer cap")

    rapid_spin = block(scoring, "AI_Smart_RapidSpin:", "AI_Smart_HiddenPower:")
    for needle in ("SCREENS_SPIKES_MASK", "cp 2", "cp 3"):
        require_contains(rapid_spin, needle, "Rapid Spin layer-aware scoring")

    damage_calc = block(scoring, "AIDamageCalc:", "AI_Cautious:")
    for needle in (
        "callfar EnemyAttackDamage",
        "callfar BattleCommand_DamageCalc",
        "callfar BattleCommand_Stab",
    ):
        require_contains(damage_calc, needle, "base damage estimate path")

    require(
        not re.search(r"callfar\s+BossAI_", apply_layers),
        "base mechanics gate must not call boss strategic helpers before tier dispatch",
    )

    print("Base AI mechanics correctness audit passed.")
    print("Verified shared gates: type/status matchup, Air Balloon immunity,")
    print("three-layer Spikes/Rapid Spin, held-item legality, and base damage path.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
