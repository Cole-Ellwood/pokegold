"""Unary wait/switch fallback against direct reference reply-event sums."""
import itertools

from tools.boss_ai_fixtures.harness import Mon, MOVES, open_harness
from tools.boss_ai_fixtures.cases import ITEMS


def main():
    count = 0
    replies = ("TACKLE", "LEECH_LIFE", "RECOVER", "REST", "PURSUIT", "EXPLOSION",
               "FALSE_SWIPE", "SUPER_FANG", "FURY_SWIPES", "HARDEN", "SPLASH")
    with open_harness("pokegold_ai_reference") as h:
        mem, rf = h.pb.memory, h.pb.register_file
        regs = {"D": 0xc9, "E": 0}
        initial_sp = int(rf.SP)
        assert h.invoke("OpenSRAM", {"A": 0})
        for reply, kind, scenario in itertools.product(replies, (1, 3), range(4)):
            own, player = Mon.of("CHARIZARD", 50), Mon.of("DEWGONG", 50)
            own.max_hp, player.max_hp = ((9, 17), (999, 703), (65535, 50000), (999, 1023))[scenario]
            own.hp = 1 if scenario in (0, 2) else own.max_hp
            player.hp = 1 if scenario == 1 else player.max_hp
            bench = Mon.of("STEELIX", 50, ["TACKLE"])
            bench.hp = 3 if scenario & 1 else bench.max_hp
            h.seed_battle(own, player)
            h.wr("wEnemyMonItem", (ITEMS["ROCKY_HELMET"], 0, ITEMS["QUICK_CLAW"], 0)[scenario])
            h.wr("wEnemyScreens", (0, 1, 3, 2)[scenario])
            h.wr("wEnemySubStatus3", 128 if scenario == 3 else 0)
            h.wr("wOTPartyCount", 2)
            h.wr("wCurOTMon", 0)
            h.wr("wBossAIWinconMonIdx", 2 if scenario & 2 else 0)
            for field, value in (("Species", bench.species), ("Level", bench.level), ("Status", 0),
                                 ("Item", ITEMS["ROCKY_HELMET"] if scenario == 1 else 0)):
                h.wr("wOTPartyMon1" + field, value, 48)
            for field, value in (("HP", bench.hp), ("MaxHP", bench.max_hp), ("Attack", bench.atk),
                                 ("Defense", bench.deff), ("Speed", bench.spe),
                                 ("SpclAtk", bench.spa), ("SpclDef", bench.spd)):
                h.wr("wOTPartyMon1" + field, value >> 8, 48)
                h.wr("wOTPartyMon1" + field, value & 255, 49)
            slot = 1 if kind == 1 else 255
            mem[0xc900:0xcad8] = [0] * 472
            mem[0xc933:0xc937] = [kind, slot, MOVES["STRUGGLE"], MOVES[reply]]
            assert h.invoke("BossAI_PreparePublicAction", regs)
            assert h.invoke("BossAI_PreparePublicReply", regs)
            reply_accuracy = mem[0xc900 + 89 + 51 + 1 + 31]
            probability = 256 if reply_accuracy == 255 else reply_accuracy
            context = bytes(mem[0xc900:0xca44])
            expected_total, expected_flags = 0, 0
            for event in range(2):
                p = probability if event == 0 else 256 - probability
                if not p:
                    continue
                mem[0xc900:0xca44] = list(context)
                mem[0xc950] = event * 2
                assert h.invoke("BossAI_ValuePublicExchangeFromContext", regs)
                expected_total += (int(rf.B) << 8 | int(rf.C)) * p * 512
                expected_flags |= mem[0xc948]
            entry_delta = 0
            if kind == 1:
                # Independent entry delta from the reference's own exchange with an absent reply.
                mem[0xc900:0xca44] = list(context)
                mem[0xc936] = 0
                assert h.invoke("BossAI_ValuePublicExchangeFromContext", regs)
                entry_delta = (int(rf.B) << 8 | int(rf.C)) - 1024
            baseline = 2 * 65536 * (1024 + entry_delta)
            mem[0xc900:0xca44] = list(context)
            mem[0xc900:0xc933] = list(context[141:192])
            assert h.invoke("BossAI_FastCompileReplyPlan", regs)
            reply_plan = bytes(mem[0xca8f:0xcabf])
            mem[0xa585:0xa58a] = list(baseline.to_bytes(5, "big"))
            mem[0xc900:0xca44] = [0xa5] * 324
            mem[0xcabf:0xcad8] = [0x69] * 25
            before = bytes(mem[0xa000:0xa600])
            assert h.invoke("BossAI_FastUnaryFallback", {**regs, "B": kind, "C": slot}) and h.outcome()["carry"]
            actual = int.from_bytes(bytes(mem[0xa578:0xa57d]), "big"), mem[0xa54e]
            wanted = (expected_total - baseline) % (1 << 40), expected_flags
            assert actual == wanted, (reply, kind, scenario, actual, wanted, baseline, reply_plan.hex())
            after = bytes(mem[0xa000:0xa600])
            mutable = {*range(0x510, 0x530), *range(0x54c, 0x560), *range(0x578, 0x57d)}
            assert all(a == b for i, (a, b) in enumerate(zip(before, after)) if i not in mutable)
            assert bytes(mem[0xca8f:0xcabf]) == reply_plan
            assert bytes(mem[0xcabf:0xcad8]) == bytes([0x69] * 25)
            assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
            count += 1
        for kind in (0, 2, 4, 255):
            before, wram = bytes(mem[0xa000:0xa600]), bytes(mem[0xc900:0xcad8])
            assert h.invoke("BossAI_FastUnaryFallback", {**regs, "B": kind, "C": 255}) and not h.outcome()["carry"]
            assert bytes(mem[0xa000:0xa600]) == before and bytes(mem[0xc900:0xcad8]) == wram
        assert h.invoke("CloseSRAM")
    print(f"PASS: {count} unary wait/switch fallback totals/flags with baseline subtraction and 4 no-write rejections")


if __name__ == "__main__":
    main()
