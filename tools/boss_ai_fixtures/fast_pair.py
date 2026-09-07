"""Exact factored pair numerators/flags against original-event execution."""
import itertools
import random

from tools.boss_ai_fixtures.harness import Mon, MOVES, TYPES, open_harness
from tools.boss_ai_fixtures.cases import ITEMS
from tools.boss_ai_fixtures.fast_standalone import phi


def main():
    count = scalar = 0
    rng = random.Random(20260907)
    moves = ("TACKLE", "FIRE_BLAST", "LEECH_LIFE", "DOUBLE_EDGE", "RECOVER", "REST", "SPLASH", "DREAM_EATER",
             "FURY_SWIPES", "SUPER_FANG", "FALSE_SWIPE", "EXPLOSION")
    with open_harness("pokegold_ai_reference") as h:
        h.seed_battle(Mon.of("CHARIZARD", 50), Mon.of("DEWGONG", 50))
        mem, rf = h.pb.memory, h.pb.register_file
        regs = {"D": 0xc9, "E": 0}
        initial_sp = int(rf.SP)
        assert h.invoke("OpenSRAM", {"A": 0})
        for own_move, reply, scenario in itertools.product(moves, (*moves, None), range(8)):
            own_max, player_max = ((9, 17), (999, 703), (65535, 65535), (50000, 65535))[scenario % 4]
            own, player = ((own_max, player_max), (own_max // 3, player_max // 2),
                           (1, 1), (own_max // 3 + 1, player_max // 2 + 1),
                           (own_max, 1), (1, player_max), (0, player_max), (own_max, 0))[scenario]
            item = (0, ITEMS["LIFE_ORB"], ITEMS["SHELL_BELL"], ITEMS["ROCKY_HELMET"])[scenario % 4]
            weight = 128 if scenario & 1 else 192
            own_accuracy, reply_accuracy = ((255, 255), (128, 254), (1, 128), (254, 1),
                                            (0, 255), (255, 0), (128, 128), (0, 0))[scenario]
            h.wr("wEnemyMonItem", item)
            h.wr("wEnemyMonStatus", 2 if scenario == 4 and rng.randrange(2) else 0)
            h.wr("wBattleMonStatus", 0x40 if scenario == 5 else 0)
            templates = []
            for direction, move in ((1, own_move), (0, reply or "TACKLE")):
                assert h.invoke("BossAI_BuildOwnedDamageContext", {**regs, "A": 0xff, "B": direction, "C": MOVES[move]})
                ad = bytearray(mem[0xc900:0xc933])
                ad[9:13] = bytes((TYPES["FIRE"], TYPES["STEEL"], TYPES["ICE"], TYPES["ICE"]))
                attacker, target = (own, player) if direction else (player, own)
                attacker_max, target_max = (own_max, player_max) if direction else (player_max, own_max)
                ad[13:15] = target.to_bytes(2, "big")
                ad[25:27] = target_max.to_bytes(2, "big")
                ad[47:51] = attacker.to_bytes(2, "big") + attacker_max.to_bytes(2, "big")
                ad[31] = own_accuracy if direction else reply_accuracy
                if scenario == 4 and not direction:
                    ad[15] |= 128  # represented conservative unknown incoming
                if scenario == 5 and not direction:
                    ad[15] |= 16  # Substitute must suppress Helmet only
                templates.append(ad)
            context = bytearray(324)
            context[:51] = templates[0]
            context[51:55] = bytes((0, 255, MOVES[own_move], MOVES[reply] if reply else 0))
            context[57:61] = own.to_bytes(2, "big") + own_max.to_bytes(2, "big")
            context[63:67] = player.to_bytes(2, "big") + player_max.to_bytes(2, "big")
            context[89:140] = templates[0]
            context[140] = 2
            context[141:192] = templates[1]
            mem[0xc900:0xca44] = list(context)
            mem[0xca44:0xcad8] = [0x69] * 148
            assert h.invoke("BossAI_FastImportActorHP", {**regs, "C": weight}) and h.outcome()["carry"]
            slot = count % 4
            assert h.invoke("BossAI_FastCompileOwnedPlan", {**regs, "C": slot}) and h.outcome()["carry"]
            mem[0xc900:0xc933] = list(templates[1])
            assert h.invoke("BossAI_FastCompileReplyPlan", regs) and h.outcome()["carry"]
            assert h.invoke("BossAI_FastBuildOwnedStandalone", {**regs, "C": slot}) and h.outcome()["carry"]
            assert h.invoke("BossAI_FastBuildReplyStandalone", regs) and h.outcome()["carry"]
            mem[0xca8f + 24], mem[0xca8f + 25] = mem[0xa458], mem[0xa470]  # standalone reply flags for the scalar path
            plans = bytes(mem[0xa2f8:0xa3f8])
            reply_plan = bytes(mem[0xca8f:0xcabf])
            probabilities = [256 if a == 255 else a for a in (own_accuracy, reply_accuracy if reply else 0)]
            branches = {}
            for order, own_event, reply_event in itertools.product(range(2), range(2), range(2)):
                pa = probabilities[0] if own_event == 0 else 256 - probabilities[0]
                pr = probabilities[1] if reply_event == 0 else 256 - probabilities[1]
                if not pa * pr:
                    continue
                mem[0xc900:0xca44] = list(context)
                mem[0xc950] = 0x80 | own_event | reply_event * 2
                sequence = ("OwnMove", "Reply") if order == 0 else ("Reply", "OwnMove")
                for action in sequence:
                    assert h.invoke("BossAI_ValuePublicExchange." + action, regs)
                final_own = int.from_bytes(bytes(mem[0xc939:0xc93b]), "big")
                final_player = int.from_bytes(bytes(mem[0xc93f:0xc941]), "big")
                utility = (1024 + phi(final_own, own_max, weight) - phi(own, own_max, weight) -
                           phi(final_player, player_max, 128) + phi(player, player_max, 128))
                branches[order, own_event, reply_event] = (utility * pa * pr, mem[0xc948])
            for order in range(3):
                expected_total, expected_flags = 0, 4 if order == 2 else 0
                for (branch_order, _, _), (total, flags) in branches.items():
                    if order == 2 or branch_order == order:
                        expected_total += total * (1 if order == 2 else 2)
                        expected_flags |= flags
                mem[0xc900:0xca8f] = [0xa5] * 399
                before = bytes(mem[0xa000:0xa600])
                own_moment = int.from_bytes(plans[64 * slot + 44:64 * slot + 47], "big", signed=True)
                reply_moment = int.from_bytes(reply_plan[40:43], "big", signed=True)
                baseline = 2 * 65536 * 1024 + 512 * (own_moment + reply_moment)
                if "EXPLOSION" in (own_move, reply):
                    # A Selfdestruct miss is not identity: the factored pair rejects
                    # and the native whole pair runs every event pair.
                    assert h.invoke("BossAI_FastNormalizedPair", {**regs, "C": slot, "A": order}) and not h.outcome()["carry"]
                    assert bytes(mem[0xa000:0xa600]) == before
                    entry = "BossAI_FastFallbackPair.Native"
                else:
                    assert h.invoke("BossAI_FastNormalizedPair", {**regs, "C": slot, "A": order})
                    assert h.outcome()["carry"]
                    actual = int.from_bytes(bytes(mem[0xa578:0xa57d]), "big"), mem[0xa54e]
                    assert actual == (expected_total, expected_flags), (own_move, reply, scenario, order, actual,
                        (expected_total, expected_flags), bytes(mem[0xa550:0xa55e]).hex())
                    entry = "BossAI_FastNormalizedPair.CorrectionOnly"
                assert h.invoke(entry, {**regs, "C": slot, "A": order}) and h.outcome()["carry"]
                assert int.from_bytes(bytes(mem[0xa578:0xa57d]), "big") == (expected_total - baseline) % (1 << 40), (
                    own_move, reply, scenario, order, entry, int.from_bytes(bytes(mem[0xa578:0xa57d]), "big"), (expected_total - baseline) % (1 << 40))
                assert mem[0xa54e] == expected_flags, (own_move, reply, scenario, order, entry, mem[0xa54e], expected_flags)
                after = bytes(mem[0xa000:0xa600])
                mutable = {*range(0x448, 0x460), *range(0x4a8, 0x4b2), *range(0x510, 0x560), *range(0x56d, 0x570), *range(0x578, 0x57d)}  # regime cache, FSK_ACC
                assert all(a == b for i, (a, b) in enumerate(zip(before, after)) if i not in mutable), (
                    own_move, reply, scenario, order, [hex(0xa000 + i) for i, (a, b) in enumerate(zip(before, after)) if a != b and i not in mutable])
                # Scalar path: identical correction/flags whenever it accepts the pair.
                mem[0xa578:0xa57d] = [0x77] * 5
                mem[0xa54e] = 0x77
                before_scalar = bytes(mem[0xa000:0xa600])
                assert h.invoke("BossAI_FastScalarPair", {**regs, "C": slot, "A": order})
                if h.outcome()["carry"]:
                    scalar += 1
                    assert int.from_bytes(bytes(mem[0xa578:0xa57d]), "big") == (expected_total - baseline) % (1 << 40), (own_move, reply, scenario, order, "scalar total")
                    assert mem[0xa54e] == expected_flags, (own_move, reply, scenario, order, "scalar flags", mem[0xa54e], expected_flags)
                after_scalar = bytes(mem[0xa000:0xa600])
                scalar_mutable = {*range(0x4a8, 0x4b2), *range(0x510, 0x530), *range(0x54c, 0x578), *range(0x578, 0x57d), *range(0x5c0, 0x5d8)}
                assert all(a == b for i, (a, b) in enumerate(zip(before_scalar, after_scalar)) if i not in scalar_mutable), (
                    own_move, reply, scenario, order, [hex(0xa000 + i) for i, (a, b) in enumerate(zip(before_scalar, after_scalar)) if a != b and i not in scalar_mutable])
                assert bytes(mem[0xc900:0xca8f]) == bytes([0xa5] * 399)
                assert bytes(mem[0xca8f:0xcabf]) == reply_plan
                assert bytes(mem[0xcabf:0xcad8]) == bytes([0x69] * 25)
                assert bytes(mem[0xa2f8:0xa3f8]) == plans
                assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
                count += 1
        for slot, order, own_opcode, reply_opcode in ((4, 0, 1, 1), (255, 2, 1, 1), (0, 3, 1, 1), (0, 255, 1, 1),
                                                     (0, 0, 0, 1), (0, 0, 1, 0), (0, 0, 1, 9), (0, 0, 6, 1), (0, 0, 1, 8)):
            mem[0xa2fc], mem[0xca90] = own_opcode, reply_opcode
            before, wram = bytes(mem[0xa000:0xa600]), bytes(mem[0xc900:0xcad8])
            assert h.invoke("BossAI_FastNormalizedPair", {**regs, "C": slot, "A": order}) and not h.outcome()["carry"]
            assert bytes(mem[0xa000:0xa600]) == before and bytes(mem[0xc900:0xcad8]) == wram
        for slot, order, own_opcode, reply_opcode in ((4, 0, 1, 1), (0, 3, 1, 1), (0, 0, 0, 1), (0, 0, 1, 0), (0, 0, 7, 1), (0, 0, 1, 9)):
            mem[0xa2fc], mem[0xca90] = own_opcode, reply_opcode
            before, wram = bytes(mem[0xa000:0xa600]), bytes(mem[0xc900:0xcad8])
            assert h.invoke("BossAI_FastFallbackPair.Native", {**regs, "C": slot, "A": order}) and not h.outcome()["carry"]
            assert bytes(mem[0xa000:0xa600]) == before and bytes(mem[0xc900:0xcad8]) == wram
        assert h.invoke("CloseSRAM")
    print(f"PASS: {count} native pair numerators/flags ({scalar} also through the scalar path), producer poisoning, record guards and 15 no-write rejections")


if __name__ == "__main__":
    main()
