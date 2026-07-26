#!/usr/bin/env python3
"""ROM-backed audit: a Haki'd boss never spends its once-per-battle read on a
move the defender is immune to, whatever the incoming score array holds.

Both Haki entry points end in BossAI_ChooseBestOracleMove, which simply takes the
first move scoring under 80. The type-immunity hard block that pushes an immune
move to 80 lives in BossAI_ApplyMoveModel, so the choice is only safe if the
score array was rebuilt for the CURRENT defender first.

BossAI_OracleHakiAfterPlayerAction (player moved/switched first) always rebuilt.
BossAI_OracleHakiRead (boss moves first) did not -- it trusted whatever the
upstream pass left behind. That shipped as a Haki'd Gengar using Shadow Ball into
a Magnemite, which is a guaranteed no-op because Steel is Ghost-immune in this
hack: with the array unpopulated the choice collapsed to move slot 1.

This audit drives the real routine with adversarial starting arrays. Every one
must still produce a move the defender is not immune to. A regression that
removes the rebuild fails the all-zero and ascending rows immediately.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

GHOST, PSYCHIC_TYPE, ELECTRIC, STEEL = 8, 24, 23, 9
GENGAR_ID, MAGNEMITE_ID = 94, 81
SHADOW_BALL, THUNDERBOLT, DESTINY_BOND, PSYCHIC_M, SWIFT = 247, 85, 194, 94, 129
AI_TIER_MID = 2
SENTINEL_ADDR = 0xFFFD
HAKI_ELIGIBLE = 1 << 2
BOOT_FRAMES = 600
RUN_BUDGET = 3000

# Gengar's moveset, in slot order. Shadow Ball is the immune no-op vs Magnemite
# and sits in slot 1, which is exactly what a non-rebuilt array collapses to.
MOVES = [SHADOW_BALL, THUNDERBOLT, DESTINY_BOND, PSYCHIC_M]
MOVE_NAMES = {SHADOW_BALL: "SHADOW_BALL", THUNDERBOLT: "THUNDERBOLT",
              DESTINY_BOND: "DESTINY_BOND", PSYCHIC_M: "PSYCHIC", 0: "(none)"}
FORBIDDEN = SHADOW_BALL  # 0x vs ELECTRIC/STEEL

# Adversarial incoming score arrays. "rebuilt" is the realistic one; the rest
# stand in for an array that does not describe the current defender.
START_ARRAYS = [
    ("rebuilt for matchup", None),
    ("all zero", [0, 0, 0, 0]),
    ("all neutral 20", [20, 20, 20, 20]),
    ("ascending (slot 1 best)", [1, 2, 3, 4]),
    ("descending (slot 4 best)", [4, 3, 2, 1]),
    ("slot 1 strongly favoured", [0, 60, 60, 60]),
]

GENGAR = dict(hp=69, atk=74, deff=38, spe=59, spa=74, spd=46)
MAGNE = dict(hp=52, atk=42, deff=40, spe=28, spa=52, spd=33)


def skip(reason: str) -> int:
    print(f"SKIP: haki move choice audit ({reason})")
    return 0


def run_case(DebugSession, write_byte_banked, start):
    with DebugSession.open("pokegold") as sess:
        pb, syms = sess.pyboy, sess.symbols
        for n in ("BossAI_OracleHakiRead", "BossAI_ApplyMoveModel",
                  "wEnemyAIMoveScores", "wCurEnemyMove"):
            if syms.get(n) is None:
                return f"symbol {n} missing from pokegold.sym"
        sess.tick(BOOT_FRAMES)

        def wr(name, val, off=0):
            s = syms[name]
            write_byte_banked(pb, s.address + off, val, s.bank)

        def wr16(name, val):
            wr(name, (val >> 8) & 0xFF, 0)
            wr(name, val & 0xFF, 1)

        def rd(name, off=0):
            s = syms[name]
            old = int(pb.memory[0xFF70])
            if 0xD000 <= s.address <= 0xDFFF and s.bank:
                pb.memory[0xFF70] = s.bank
            try:
                return int(pb.memory[s.address + off])
            finally:
                pb.memory[0xFF70] = old

        def invoke(func):
            pb.memory[0xFFFF] = 0
            pb.memory[0xFF0F] = 0
            pb.memory[SENTINEL_ADDR] = 0x18
            pb.memory[SENTINEL_ADDR + 1] = 0xFE
            rf = pb.register_file
            new_sp = (int(rf.SP) - 2) & 0xFFFF
            pb.memory[new_sp] = SENTINEL_ADDR & 0xFF
            pb.memory[new_sp + 1] = SENTINEL_ADDR >> 8
            rf.SP = new_sp
            e = syms[func]
            wr("hROMBank", e.bank)
            pb.memory[0x2000] = e.bank
            rf.PC = e.address
            t = 0
            while t < RUN_BUDGET:
                pb.tick(2, False, False)
                t += 2
                if int(rf.PC) in (SENTINEL_ADDR, SENTINEL_ADDR + 2):
                    return True
            return False

        # boss side: Morty's ace Gengar (GHOST/PSYCHIC in this hack)
        wr("wBossAITier", AI_TIER_MID)
        wr("wEnemyMonSpecies", GENGAR_ID)
        wr("wEnemyMonType1", GHOST)
        wr("wEnemyMonType1", PSYCHIC_TYPE, 1)
        wr("wEnemyMonLevel", 26)
        wr16("wEnemyMonMaxHP", GENGAR["hp"])
        wr16("wEnemyMonHP", GENGAR["hp"])
        wr16("wEnemyMonAttack", GENGAR["atk"])
        wr16("wEnemyMonDefense", GENGAR["deff"])
        wr16("wEnemyMonSpeed", GENGAR["spe"])
        wr16("wEnemyMonSpclAtk", GENGAR["spa"])
        wr16("wEnemyMonSpclDef", GENGAR["spd"])
        wr("wEnemyMonStatus", 0)
        for i, mv in enumerate(MOVES):
            wr("wEnemyMonMoves", mv, i)
            wr("wEnemyMonPP", 30, i)
        wr("wEnemyDisabledMove", 0)

        # player side: ELECTRIC/STEEL wall, immune to the boss's Ghost STAB
        wr("wBattleMonSpecies", MAGNEMITE_ID)
        wr("wBattleMonType1", ELECTRIC)
        wr("wBattleMonType1", STEEL, 1)
        wr("wBattleMonLevel", 24)
        wr16("wBattleMonMaxHP", MAGNE["hp"])
        wr16("wBattleMonHP", MAGNE["hp"])
        wr16("wBattleMonAttack", MAGNE["atk"])
        wr16("wBattleMonDefense", MAGNE["deff"])
        wr16("wBattleMonSpeed", MAGNE["spe"])
        wr16("wBattleMonSpclAtk", MAGNE["spa"])
        wr16("wBattleMonSpclDef", MAGNE["spd"])
        wr("wBattleMonStatus", 0)
        for i, mv in enumerate([THUNDERBOLT, SWIFT, 0, 0]):
            wr("wBattleMonMoves", mv, i)
            wr("wBattleMonPP", 30 if mv else 0, i)

        if start is None:
            for i in range(4):
                wr("wEnemyAIMoveScores", 20, i)
            wr("hBattleTurn", 1)
            invoke("BossAI_ApplyMoveModel")
        else:
            for i, v in enumerate(start):
                wr("wEnemyAIMoveScores", v, i)

        entering = [rd("wEnemyAIMoveScores", i) for i in range(4)]

        # boss moves first, player is locked into a move (did not switch)
        wr("wBossAIRevealedMovesBitmapSpare", HAKI_ELIGIBLE, 1)
        wr("wEnemyGoesFirst", 1)
        wr("wBattlePlayerAction", 0)   # BATTLEPLAYERACTION_USEMOVE
        wr("wCurPlayerMove", THUNDERBOLT)
        wr("wEnemySubStatus5", 0)
        wr("wOTPartyCount", 1)         # no bench, so no immunity pivot
        wr("wCurEnemyMove", 0)
        wr("wBossAIMoveChoiceReady", 0)

        ok = invoke("BossAI_OracleHakiRead")
        return {"returned": ok, "entering": entering,
                "chosen": rd("wCurEnemyMove"),
                "ready": rd("wBossAIMoveChoiceReady")}


def main() -> int:
    try:
        from tools.damage_debugger.emulator import DebugSession
        from tools.damage_debugger.safe_call import write_byte_banked
    except Exception as exc:  # pragma: no cover - environment guard
        return skip(f"debugger harness unavailable: {exc}")

    rows, failures = [], []
    for label, start in START_ARRAYS:
        try:
            r = run_case(DebugSession, write_byte_banked, start)
        except Exception as exc:
            return skip(f"pokegold ROM/symbols unavailable: {exc}")
        if isinstance(r, str):
            return skip(r)

        chosen, status = r["chosen"], "OK"
        if not r["returned"]:
            status = "FAIL(no-return)"
            failures.append(f"{label}: BossAI_OracleHakiRead never returned")
        elif not r["ready"]:
            status = "FAIL(no-choice)"
            failures.append(
                f"{label}: Haki fired but committed no move choice "
                "(wBossAIMoveChoiceReady = 0)"
            )
        elif chosen == FORBIDDEN:
            status = "FAIL(immune)"
            failures.append(
                f"{label}: Haki chose {MOVE_NAMES[FORBIDDEN]}, which the defender "
                "is IMMUNE to — a guaranteed no-op. The score array was almost "
                "certainly not rebuilt for the current defender before choosing."
            )
        rows.append((label, r["entering"], MOVE_NAMES.get(chosen, str(chosen)), status))

    w = max(len(r[0]) for r in rows)
    print(f"{'incoming score array'.ljust(w)}  entering            chose         status")
    print("-" * (w + 44))
    for label, entering, name, status in rows:
        print(f"{label.ljust(w)}  {str(entering):18s}  {name:12s}  {status}")
    print()

    if failures:
        print(f"FAIL: {len(failures)} Haki move-choice violation(s).")
        for f in failures:
            print(f"  - {f}")
        print()
        print("Source: engine/battle/ai/boss_policy_switch.asm BossAI_OracleHakiRead")
        return 1

    print(f"PASS: all {len(rows)} incoming score arrays still yield a non-immune move")
    print("      (Haki rebuilds scores for the current defender before choosing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
