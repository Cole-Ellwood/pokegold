"""Exact standalone event states/deltas/moments and actor HP imports."""
from tools.boss_ai_fixtures.harness import Mon, MOVES, TYPES, open_harness
from tools.boss_ai_fixtures.cases import ITEMS


def phi(hp, maximum, weight):
    return 0 if hp == 0 else 2 * weight + weight * hp // maximum


def main():
    count = 0
    with open_harness("pokegold_ai_reference") as h:
        h.seed_battle(Mon.of("CHARIZARD", 50), Mon.of("DEWGONG", 50))
        mem, rf = h.pb.memory, h.pb.register_file
        regs = {"D": 0xc9, "E": 0}
        initial_sp = int(rf.SP)
        assert h.invoke("OpenSRAM", {"A": 0})
        for move_name in ("TACKLE", "FIRE_BLAST", "GIGA_DRAIN", "DOUBLE_EDGE",
                          "SEISMIC_TOSS", "RECOVER", "REST", "SPLASH", "HARDEN"):
            for item in (0, ITEMS["LIFE_ORB"], ITEMS["SHELL_BELL"]):
                h.wr("wEnemyMonItem", item)
                for own_max, player_max in ((9, 127), (999, 1023), (65535, 1536)):
                    assert h.invoke("BossAI_BuildOwnedDamageContext", {
                        **regs, "A": 0xff, "B": 1, "C": MOVES[move_name]})
                    base = bytearray(324)
                    base[:51] = bytes(mem[0xc900:0xc933])
                    base[9:13] = bytes((TYPES["FIRE"], TYPES["STEEL"], TYPES["ICE"], TYPES["ICE"]))
                    base[25:27] = player_max.to_bytes(2, "big")
                    base[49:51] = own_max.to_bytes(2, "big")
                    base[52:54] = bytes((0xff, MOVES[move_name]))
                    base[59:61] = own_max.to_bytes(2, "big")
                    base[65:67] = player_max.to_bytes(2, "big")
                    for own, player in ((1, 1), (own_max, player_max), (own_max // 3, player_max // 2)):
                        for accuracy in (0, 1, 128, 254, 255):
                            context = bytearray(base)
                            context[13:15] = player.to_bytes(2, "big")
                            context[47:49] = own.to_bytes(2, "big")
                            context[31] = accuracy
                            context[57:59] = own.to_bytes(2, "big")
                            context[63:65] = player.to_bytes(2, "big")
                            context[89:140] = context[:51]
                            states = []
                            for event in (0, 1):
                                mem[0xc900:0xca44] = list(context)
                                mem[0xc950] = 0x80 | event
                                assert h.invoke("BossAI_ValuePublicExchange.OwnMove", regs)
                                states.append((bytes(mem[0xc939:0xc93b]) + bytes(mem[0xc93f:0xc941]), mem[0xc948]))
                            for weight in (128, 192):
                                mem[0xc900:0xca44] = list(context)
                                mem[0xa000:0xa600] = [0xa5] * 1536
                                assert h.invoke("BossAI_FastImportActorHP", {**regs, "C": weight})
                                assert h.outcome()["carry"]
                                assert bytes(mem[0xc900:0xca44]) == context
                                expected_actors = bytearray(80)
                                for offset, hp, maximum, w, limit in ((0, own, own_max, weight, 1536),
                                                                     (40, player, player_max, 128, 1024)):
                                    expected_actors[offset:offset + 10] = (hp.to_bytes(2, "big") + maximum.to_bytes(2, "big") +
                                        phi(hp, maximum, w).to_bytes(2, "big") + hp.to_bytes(2, "big") +
                                        phi(hp, maximum, w).to_bytes(2, "big"))
                                    expected_actors[offset + 34] = w
                                    expected_actors[offset + 37] = 0 if maximum < w else 1 if maximum < limit else 2
                                assert bytes(mem[0xa3f8:0xa448]) == expected_actors
                                after_import = bytes(mem[0xa000:0xa600])
                                assert after_import[0x280:0x3f8] == bytes([0xa5] * 0x178)
                                assert after_import[0x448:0x510] == bytes([0xa5] * 0xc8)
                                assert after_import[0x530:] == bytes([0xa5] * 0xd0)
                                assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
                                slot = count % 4
                                assert h.invoke("BossAI_FastCompileOwnedPlan", {**regs, "C": slot})
                                assert h.outcome()["carry"]
                                plan_address = 0xa2f8 + 64 * slot
                                expected = bytearray(mem[plan_address:plan_address + 64])
                                deltas = []
                                for event, (hp_pair, flags) in enumerate(states):
                                    final_own = int.from_bytes(hp_pair[:2], "big")
                                    final_player = int.from_bytes(hp_pair[2:], "big")
                                    delta = (phi(final_own, own_max, weight) - phi(own, own_max, weight) -
                                             phi(final_player, player_max, 128) + phi(player, player_max, 128))
                                    expected[32 + 4 * event:36 + 4 * event] = hp_pair
                                    expected[40 + 2 * event:42 + 2 * event] = delta.to_bytes(2, "big", signed=True)
                                    expected[47 + event] = flags
                                    deltas.append(delta)
                                probability = 256 if accuracy == 255 else accuracy
                                moment = probability * deltas[0] + (256 - probability) * deltas[1]
                                expected[44:47] = moment.to_bytes(3, "big", signed=True)
                                mem[0xc900:0xca44] = [0x5a] * 324
                                before = bytes(mem[0xa000:0xa600])
                                assert h.invoke("BossAI_FastBuildOwnedStandalone", {**regs, "C": slot})
                                assert h.outcome()["carry"]
                                actual = bytes(mem[plan_address:plan_address + 64])
                                assert actual == expected, (move_name, item, own_max, own, player, accuracy, weight,
                                    [(i, a, b) for i, (a, b) in enumerate(zip(actual, expected)) if a != b])
                                after = bytes(mem[0xa000:0xa600])
                                mutable = {*range(plan_address - 0xa000 + 32, plan_address - 0xa000 + 49),
                                           *range(0x448, 0x478), *range(0x510, 0x560)}
                                assert all(a == b for i, (a, b) in enumerate(zip(before, after)) if i not in mutable)
                                assert bytes(mem[0xc900:0xca44]) == bytes([0x5a] * 324)
                                assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
                                count += 1
        # Actor import failures must not expose a partial table/actor pair.
        for field, value, weight in ((27, 0, 128), (27, 2, 128), (27, 1, 0),
                                     (27, 1, 255), (49, 0, 128), (25, 0, 128),
                                     (47, 1000, 128), (13, 1000, 128)):
            invalid = bytearray(context)
            for at in (13, 47):
                invalid[at:at + 2] = (1).to_bytes(2, "big")
            for at in (25, 49):
                invalid[at:at + 2] = (999).to_bytes(2, "big")
            if field == 27:
                invalid[field] = value
            else:
                invalid[field:field + 2] = value.to_bytes(2, "big")
            mem[0xc900:0xca44] = list(invalid)
            before = bytes(mem[0xa000:0xa600])
            assert h.invoke("BossAI_FastImportActorHP", {**regs, "C": weight})
            assert not h.outcome()["carry"]
            assert bytes(mem[0xa000:0xa600]) == before
            assert bytes(mem[0xc900:0xca44]) == invalid
        for slot in (4, 255):
            before = bytes(mem[0xa000:0xa600])
            assert h.invoke("BossAI_FastBuildOwnedStandalone", {**regs, "C": slot})
            assert not h.outcome()["carry"]
            assert bytes(mem[0xa000:0xa600]) == before
        mem[0xa2fc] = 0
        before = bytes(mem[0xa000:0xa600])
        assert h.invoke("BossAI_FastBuildOwnedStandalone", {**regs, "C": 0})
        assert not h.outcome()["carry"]
        assert bytes(mem[0xa000:0xa600]) == before
        assert h.invoke("CloseSRAM")
    print(f"PASS: {count} actor imports and full standalone records/moments, 8 actor and 3 standalone no-write rejections")


if __name__ == "__main__":
    main()
