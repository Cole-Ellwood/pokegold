"""Whole-pair fallback and subtraction against direct reference event sums."""
import itertools

from tools.boss_ai_fixtures.harness import Mon, MOVES, open_harness
from tools.boss_ai_fixtures.cases import ITEMS


def main():
    count = 0
    moves = ("TACKLE", "LEECH_LIFE", "DOUBLE_EDGE", "RECOVER", "REST", "PURSUIT",
             "EXPLOSION", "FALSE_SWIPE", "SUPER_FANG", "FURY_SWIPES", "HARDEN", "AMNESIA")
    with open_harness("pokegold_ai_reference") as h:
        mem, rf = h.pb.memory, h.pb.register_file
        regs = {"D": 0xc9, "E": 0}
        initial_sp = int(rf.SP)
        assert h.invoke("OpenSRAM", {"A": 0})
        for own_move, reply, scenario in itertools.product(moves, (*moves, None), range(4)):
            own, player = Mon.of("CHARIZARD", 50), Mon.of("DEWGONG", 50)
            own.max_hp, player.max_hp = ((9, 17), (999, 703), (65535, 50000), (999, 1023))[scenario]
            own.hp = 1 if scenario in (0, 2) else own.max_hp
            player.hp = 1 if scenario == 1 else player.max_hp
            h.seed_battle(own, player)
            h.wr("wEnemyMonItem", (ITEMS["LIFE_ORB"], ITEMS["ROCKY_HELMET"], ITEMS["SHELL_BELL"], ITEMS["QUICK_CLAW"])[scenario])
            h.wr("wBossAIWinconMonIdx", 1 if scenario & 1 else 0)
            h.wr("wCurOTMon", 0)
            mem[0xc900:0xcad8] = [0] * 472
            mem[0xc934:0xc937] = [255, MOVES[own_move], MOVES[reply] if reply else 0]
            assert h.invoke("BossAI_PreparePublicAction", regs)
            if scenario in (1, 3):
                h.wr_be16("wEnemyMonSpeed", int.from_bytes(bytes(mem[0xc945:0xc947]), "big"))
                assert h.invoke("BossAI_PreparePublicAction", regs)
            assert h.invoke("BossAI_PreparePublicReply", regs)
            assert h.invoke("BossAI_PreparedActionHasSpeedTie", regs)
            tie = h.outcome()["carry"]
            assert h.invoke("BossAI_PreparedExchangeAccuracy", regs)
            probabilities = [256 if a == 255 else a for a in (int(rf.B), int(rf.C))]
            context = bytes(mem[0xc900:0xca44])
            expected_total, expected_flags = 0, 0
            for order, own_event, reply_event in itertools.product(range(2 if tie else 1), range(2), range(2)):
                pa = probabilities[0] if own_event == 0 else 256 - probabilities[0]
                pr = probabilities[1] if reply_event == 0 else 256 - probabilities[1]
                if not pa * pr:
                    continue
                mem[0xc900:0xca44] = list(context)
                mem[0xc950] = own_event | reply_event * 2 | ((4 | (8 if order == 0 else 0)) if tie else 0)
                assert h.invoke("BossAI_ValuePublicExchangeFromContext", regs)
                expected_total += (int(rf.B) << 8 | int(rf.C)) * pa * pr * (1 if tie else 2)
                expected_flags |= mem[0xc948]
            mem[0xc900:0xca44] = list(context)
            mem[0xc900:0xc933] = list(context[89:140])
            mem[0xca44:0xcad8] = [0x69] * 148
            assert h.invoke("BossAI_FastImportActorHP", {**regs, "C": 192 if scenario & 1 else 128}) and h.outcome()["carry"]
            slot = count % 4
            assert h.invoke("BossAI_FastCompileOwnedPlan", {**regs, "C": slot})
            if h.outcome()["carry"]:
                assert h.invoke("BossAI_FastBuildOwnedStandalone", {**regs, "C": slot}) and h.outcome()["carry"]
            mem[0xc900:0xc933] = list(context[141:192])
            assert h.invoke("BossAI_FastCompileReplyPlan", regs)
            if h.outcome()["carry"]:
                assert h.invoke("BossAI_FastBuildReplyStandalone", regs) and h.outcome()["carry"]
            plans = bytes(mem[0xa2f8:0xa3f8])
            reply_plan = bytes(mem[0xca8f:0xcabf])
            own_moment = int.from_bytes(plans[64 * slot + 44:64 * slot + 47], "big", signed=True)
            reply_moment = int.from_bytes(reply_plan[40:43], "big", signed=True)
            baseline = 2 * 65536 * 1024 + 512 * (own_moment + reply_moment)
            for correction in (False, True):
                mem[0xc900:0xca44] = [0xa5] * 324
                before = bytes(mem[0xa000:0xa600])
                entry = "BossAI_FastFallbackPair" + (".CorrectionOnly" if correction else "")
                assert h.invoke(entry, {**regs, "C": slot, "A": 2 if tie else scenario & 1}) and h.outcome()["carry"]
                actual = int.from_bytes(bytes(mem[0xa578:0xa57d]), "big"), mem[0xa54e]
                wanted = (expected_total - (baseline if correction else 0)) % (1 << 40), expected_flags
                assert actual == wanted, (own_move, reply, scenario, tie, correction, actual, wanted, baseline)
                after = bytes(mem[0xa000:0xa600])
                mutable = {*range(0x510, 0x530), *range(0x54c, 0x560), *range(0x578, 0x57d)}
                assert all(a == b for i, (a, b) in enumerate(zip(before, after)) if i not in mutable)
                assert bytes(mem[0xca44:0xca8f]) == bytes([0x69] * 75)
                assert bytes(mem[0xca8f:0xcabf]) == reply_plan
                assert bytes(mem[0xcabf:0xcad8]) == bytes([0x69] * 25)
                assert bytes(mem[0xa2f8:0xa3f8]) == plans
                assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
                count += 1
        for slot, order, kind in ((4, 0, 0), (255, 2, 0), (0, 3, 0), (0, 255, 0), (0, 0, 1), (0, 0, 3)):
            mem[0xa2f9] = kind
            before, wram = bytes(mem[0xa000:0xa600]), bytes(mem[0xc900:0xcad8])
            assert h.invoke("BossAI_FastFallbackPair", {**regs, "C": slot, "A": order}) and not h.outcome()["carry"]
            assert bytes(mem[0xa000:0xa600]) == before and bytes(mem[0xc900:0xcad8]) == wram
        assert h.invoke("CloseSRAM")
    print(f"PASS: {count} full fallback numerators/flags and baseline replacements, record guards and 6 no-write rejections")


if __name__ == "__main__":
    main()
