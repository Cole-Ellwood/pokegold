"""Incoming standalone event states and exact moments from the reference."""
from tools.boss_ai_fixtures.harness import Mon, MOVES, TYPES, open_harness
from tools.boss_ai_fixtures.cases import ITEMS
from tools.boss_ai_fixtures.fast_standalone import phi


def main():
    count = scalar = 0
    with open_harness("pokegold_ai_reference") as h:
        h.seed_battle(Mon.of("CHARIZARD", 50), Mon.of("DEWGONG", 50))
        mem, rf = h.pb.memory, h.pb.register_file
        regs = {"D": 0xc9, "E": 0}
        initial_sp = int(rf.SP)
        assert h.invoke("OpenSRAM", {"A": 0})
        for move in ("TACKLE", "FIRE_BLAST", "LEECH_LIFE", "DOUBLE_EDGE",
                     "SEISMIC_TOSS", "RECOVER", "REST", "SPLASH", "PURSUIT", None):
            for item in (0, ITEMS["ROCKY_HELMET"]):
                h.wr("wEnemyMonItem", item)
                for own_max, player_max in ((9, 127), (999, 1023), (50000, 65535)):
                    assert h.invoke("BossAI_BuildOwnedDamageContext", {
                        **regs, "A": 0xff, "B": 0, "C": MOVES[move or "TACKLE"]})
                    base = bytearray(324)
                    base[:51] = bytes(mem[0xc900:0xc933])
                    base[9:13] = bytes((TYPES["FIRE"], TYPES["STEEL"], TYPES["ICE"], TYPES["ICE"]))
                    base[25:27] = own_max.to_bytes(2, "big")
                    base[49:51] = player_max.to_bytes(2, "big")
                    base[51:55] = bytes((int(move == "PURSUIT"), 0xff, MOVES["TACKLE"], MOVES[move] if move else 0))
                    base[59:61] = own_max.to_bytes(2, "big")
                    base[65:67] = player_max.to_bytes(2, "big")
                    for own, player in ((0, player_max), (own_max, 0), (1, 1), (own_max, player_max), (own_max // 2, player_max // 3)):
                        for accuracy in (0, 1, 128, 254, 255):
                            context = bytearray(base)
                            context[13:15] = own.to_bytes(2, "big")
                            context[47:49] = player.to_bytes(2, "big")
                            context[31] = accuracy
                            context[57:59] = own.to_bytes(2, "big")
                            context[63:65] = player.to_bytes(2, "big")
                            context[140] = 2
                            context[141:192] = context[:51]
                            states = []
                            for event in (0, 1):
                                mem[0xc900:0xca44] = list(context)
                                mem[0xc950] = 0x80 | event * 2
                                assert h.invoke("BossAI_ValuePublicExchange.Reply", regs)
                                states.append((bytes(mem[0xc939:0xc93b]) + bytes(mem[0xc93f:0xc941]), mem[0xc948]))
                            for weight in (128, 192):
                                # Actor import has an owned AD ABI; provide only
                                # that HP view, then restore the incoming facts.
                                actor_context = bytearray(context)
                                actor_context[27] = 1
                                actor_context[47:51] = own.to_bytes(2, "big") + own_max.to_bytes(2, "big")
                                actor_context[13:15] = player.to_bytes(2, "big")
                                actor_context[25:27] = player_max.to_bytes(2, "big")
                                mem[0xc900:0xca44] = list(actor_context)
                                mem[0xa000:0xa600] = [0xa5] * 1536
                                assert h.invoke("BossAI_FastImportActorHP", {**regs, "C": weight}) and h.outcome()["carry"]
                                mem[0xc900:0xca44] = list(context)
                                mem[0xca44:0xcad8] = [0x69] * 148
                                assert h.invoke("BossAI_FastCompileReplyPlan", regs) and h.outcome()["carry"]
                                expected = bytearray(mem[0xca8f:0xcabf])
                                deltas = []
                                for event, (hp_pair, flags) in enumerate(states):
                                    final_own = int.from_bytes(hp_pair[:2], "big")
                                    final_player = int.from_bytes(hp_pair[2:], "big")
                                    delta = (phi(final_own, own_max, weight) - phi(own, own_max, weight) -
                                             phi(final_player, player_max, 128) + phi(player, player_max, 128))
                                    expected[28 + 4 * event:32 + 4 * event] = hp_pair
                                    expected[36 + 2 * event:38 + 2 * event] = delta.to_bytes(2, "big", signed=True)
                                    deltas.append(delta)
                                probability = 256 if accuracy == 255 else accuracy
                                moment = probability * deltas[0] + (256 - probability) * deltas[1]
                                expected[40:43] = moment.to_bytes(3, "big", signed=True)
                                mem[0xc900:0xca8f] = [0x5a] * 399
                                before = bytes(mem[0xa000:0xa600])
                                assert h.invoke("BossAI_FastBuildReplyStandalone", regs) and h.outcome()["carry"]
                                actual = bytes(mem[0xca8f:0xcabf])
                                assert actual == expected, (move, item, own_max, own, player, accuracy, weight,
                                    [(i, a, b) for i, (a, b) in enumerate(zip(actual, expected)) if a != b])
                                for cont, (_, flags) in zip((0xa448, 0xa460), states):
                                    assert mem[cont + 16] == flags
                                after = bytes(mem[0xa000:0xa600])
                                mutable = {*range(0x448, 0x478), *range(0x510, 0x560)}
                                assert all(a == b for i, (a, b) in enumerate(zip(before, after)) if i not in mutable)
                                # Scalar standalone: same record bytes plus flags at 24/25 when eligible.
                                mem[0xca8f + 24:0xca8f + 43] = [0x77] * 19
                                before = bytes(mem[0xa000:0xa600])
                                assert h.invoke("BossAI_FastScalarReplyStandalone", regs)
                                if h.outcome()["carry"]:
                                    scalar += 1
                                    actual = bytes(mem[0xca8f:0xcabf])
                                    assert actual[28:43] == expected[28:43], (move, item, own_max, own, player, accuracy, weight, "scalar",
                                        [(i, a, b) for i, (a, b) in enumerate(zip(actual, expected)) if a != b and 28 <= i < 43])
                                    assert (actual[24], actual[25]) == (states[0][1], states[1][1]), (move, item, own, player, accuracy, "scalar flags", actual[24], actual[25], states)
                                else:
                                    assert bytes(mem[0xca8f + 24:0xca8f + 43]) == bytes([0x77] * 19)
                                after = bytes(mem[0xa000:0xa600])
                                scalar_mutable = {*range(0x4a8, 0x4b2), *range(0x54c, 0x578), *range(0x5c0, 0x5e0)}  # regime cache, pair scratch, gate caches
                                assert all(a == b for i, (a, b) in enumerate(zip(before, after)) if i not in scalar_mutable)
                                assert bytes(mem[0xc900:0xca8f]) == bytes([0x5a] * 399)
                                assert bytes(mem[0xcabf:0xcad8]) == bytes([0x69] * 25)
                                assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
                                count += 1
        for opcode in (0, 10, 255):
            mem[0xca90] = opcode
            before, wram = bytes(mem[0xa000:0xa600]), bytes(mem[0xc900:0xcad8])
            assert h.invoke("BossAI_FastBuildReplyStandalone", regs) and not h.outcome()["carry"]
            assert bytes(mem[0xa000:0xa600]) == before and bytes(mem[0xc900:0xcad8]) == wram
        assert h.invoke("CloseSRAM")
    print(f"PASS: {count} ({scalar} also scalar) full incoming standalone records/moments and 3 no-write rejections")


if __name__ == "__main__":
    main()
