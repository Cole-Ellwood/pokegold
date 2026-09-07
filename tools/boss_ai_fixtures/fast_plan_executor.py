"""Differential one-action execution with the producer prefix poisoned."""
from tools.boss_ai_fixtures.harness import Mon, MOVES, TYPES, open_harness
from tools.boss_ai_fixtures.cases import ITEMS


def main():
    count = 0
    with open_harness("pokegold_ai_reference") as h:
        h.seed_battle(Mon.of("CHARIZARD", 50), Mon.of("DEWGONG", 50))
        mem, rf = h.pb.memory, h.pb.register_file
        regs = {"D": 0xc9, "E": 0}
        initial_sp = int(rf.SP)
        assert h.invoke("OpenSRAM", {"A": 0})
        for move_name in ("TACKLE", "FIRE_BLAST", "GIGA_DRAIN", "DOUBLE_EDGE",
                          "STRUGGLE", "SEISMIC_TOSS", "DRAGON_RAGE", "RECOVER",
                          "REST", "SYNTHESIS", "PURSUIT", "SPLASH", "SNORE",
                          "DREAM_EATER", "FURY_SWIPES", "BONEMERANG", "SUPER_FANG",
                          "FALSE_SWIPE", "EXPLOSION"):
            for item in (0, ITEMS["LIFE_ORB"], ITEMS["SHELL_BELL"]):
                h.wr("wEnemyMonItem", item)
                for maximum in (9, 999, 65535):
                    for denied in ("clear", "sleep", "accuracy0"):
                        h.wr("wEnemyMonStatus", 1 if denied == "sleep" else 0)
                        assert h.invoke("BossAI_BuildOwnedDamageContext", {
                            **regs, "A": 0xff, "B": 1, "C": MOVES[move_name]})
                        context = bytearray(324)
                        context[:51] = bytes(mem[0xc900:0xc933])
                        context[9:13] = bytes((TYPES["FIRE"], TYPES["STEEL"], TYPES["ICE"], TYPES["ICE"]))
                        context[25:27] = maximum.to_bytes(2, "big")
                        context[49:51] = maximum.to_bytes(2, "big")
                        if denied == "accuracy0":
                            context[31] = 0
                        context[52:54] = bytes((0xff, MOVES[move_name]))
                        context[59:61] = maximum.to_bytes(2, "big")
                        context[65:67] = maximum.to_bytes(2, "big")
                        context[89:140] = context[:51]
                        mem[0xc900:0xca44] = list(context)
                        plan_slot = count // 16 % 4
                        assert h.invoke("BossAI_FastCompileOwnedPlan", {**regs, "C": plan_slot})
                        assert h.outcome()["carry"]
                        plan = bytes(mem[0xa2f8 + 64 * plan_slot:0xa338 + 64 * plan_slot])
                        for own, player in ((0, maximum), (maximum, 0), (1, 1),
                                            (maximum, maximum), (maximum // 3, maximum // 2),
                                            (maximum // 3 + 1, maximum // 2 + 1),
                                            (maximum - 1, 1), (1, maximum)):
                            for event in (0, 1):
                                # Use the immutable outgoing template only;
                                # the reference still refreshes HP flags and
                                # computes each amount at the actual successor.
                                mem[0xc900:0xca44] = list(context)
                                mem[0xc939:0xc93b] = list(own.to_bytes(2, "big"))
                                mem[0xc93f:0xc941] = list(player.to_bytes(2, "big"))
                                mem[0xc950] = 0x80 | event
                                mem[0xc948] = 0x40
                                assert h.invoke("BossAI_ValuePublicExchange.OwnMove", regs)
                                expected = (bytes(mem[0xc939:0xc93b]) +
                                            bytes(mem[0xc93f:0xc941]), mem[0xc948])
                                # No execution-time producer facts may be read.
                                mem[0xc900:0xca44] = [0xa5] * 324
                                mem[0xa3fa:0xa3fc] = list(maximum.to_bytes(2, "big"))
                                mem[0xa422:0xa424] = list(maximum.to_bytes(2, "big"))
                                continuation = 0xa448 if count & 1 else 0xa460
                                state = bytearray([0x5a] * 24)
                                state[:4] = own.to_bytes(2, "big") + player.to_bytes(2, "big")
                                state[4:12] = bytes(8)
                                state[16] = 0x40
                                mem[continuation:continuation + 24] = list(state)
                                before = bytes(mem[0xa000:0xa600])
                                assert h.invoke("BossAI_FastExecuteOwnedPlan.FlagsOnly", {
                                    **regs, "C": plan_slot, "A": event, "HL": continuation})
                                assert h.outcome()["carry"]
                                expected_flag_state = bytearray(state)
                                expected_flag_state[16] = expected[1]
                                assert bytes(mem[continuation:continuation + 24]) == expected_flag_state
                                flag_after = bytes(mem[0xa000:0xa600])
                                flag_mutable = {continuation - 0xa000 + 16, *range(0x530, 0x560)}
                                assert all(a == b for i, (a, b) in enumerate(zip(before, flag_after)) if i not in flag_mutable)
                                mem[continuation:continuation + 24] = list(state)
                                assert h.invoke("BossAI_FastExecuteOwnedPlan", {
                                    **regs, "C": plan_slot, "A": event, "HL": continuation})
                                assert h.outcome()["carry"]
                                actual = (bytes(mem[continuation:continuation + 4]), mem[continuation + 16])
                                assert actual == expected, (move_name, item, maximum, denied, own, player, event, actual, expected)
                                after = bytes(mem[0xa000:0xa600])
                                mutable = {*range(continuation - 0xa000, continuation - 0xa000 + 4),
                                           continuation - 0xa000 + 16, *range(0x530, 0x560)}
                                assert all(a == b for i, (a, b) in enumerate(zip(before, after)) if i not in mutable)
                                assert bytes(mem[0xc900:0xca44]) == bytes([0xa5] * 324)
                                assert bytes(mem[0xa2f8 + 64 * plan_slot:0xa338 + 64 * plan_slot]) == plan
                                assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
                                count += 1
        for slot, event in ((4, 0), (255, 1), (0, 2), (3, 255)):
            before = bytes(mem[0xa000:0xa600])
            assert h.invoke("BossAI_FastExecuteOwnedPlan", {**regs, "C": slot, "A": event, "HL": 0xa448})
            assert not h.outcome()["carry"]
            assert bytes(mem[0xa000:0xa600]) == before
            assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
        # A rejected fallback plan must not leak speculative reached flags.
        mem[0xa2fc] = 0
        before = bytes(mem[0xa448:0xa478])
        assert h.invoke("BossAI_FastExecuteOwnedPlan", {**regs, "C": 0, "A": 0, "HL": 0xa448})
        assert not h.outcome()["carry"]
        assert bytes(mem[0xa448:0xa478]) == before
        assert h.invoke("CloseSRAM")
    print(f"PASS: {count} native owned action/reference comparisons, producer poisoning, 4 invalid entries and fallback rejection")


if __name__ == "__main__":
    main()
