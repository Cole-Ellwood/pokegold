"""Verify stage-separated flag exports against the public-model producers."""
import random

from tools.boss_ai_fixtures.harness import Mon, MOVES, open_harness
from tools.boss_ai_fixtures.damage import EFFECTS


def main():
    rng = random.Random(20260909)
    moves = ("TACKLE", "SNORE", "SLEEP_TALK", "FLAME_WHEEL", "SACRED_FIRE",
             "RECOVER", "REST", "GIGA_DRAIN", "FIRE_BLAST", "EXPLOSION",
             "PURSUIT", "FURY_SWIPES", "FALSE_SWIPE", "SEISMIC_TOSS")
    cases = 0
    with open_harness("pokegold_ai_reference") as h:
        boss = Mon.of("SNORLAX", 50)
        h.seed_battle(boss, Mon.of("VENUSAUR", 50))
        h.wr("wOTPartyMon1Species", boss.species)
        h.wr("wOTPartyMon1Level", 50)
        h.wr_be16("wOTPartyMon1HP", boss.hp)
        h.wr_be16("wOTPartyMon1MaxHP", boss.max_hp)
        assert h.invoke("OpenSRAM", {"A": 0})
        mem, rf = h.pb.memory, h.pb.register_file
        initial_sp = int(rf.SP)
        mem[0xa000:0xa600] = [0xa5] * 1536
        regs = {"D": 0xc9, "E": 0}

        def check_prefix(direction):
            context = bytes(mem[0xc900:0xca44])
            flags = []
            for stage in ("OwnCanAct" if direction == 0 else "PlayerCanAct",
                          "EffectUncertainty", "HitUncertainty"):
                mem[0xc948] = 0
                assert h.invoke("BossAI_ValuePublicExchange." + stage, regs)
                if not flags:
                    flags.append(int(h.outcome()["carry"]))
                flags.append(mem[0xc948])
            mem[0xc948] = context[72]
            maximum = int.from_bytes(context[49:51], "big")
            recognized, quota = False, 0
            effect, move = context[2], context[28]
            if effect == EFFECTS["EFFECT_HEAL"]:
                recognized = True
                quota = maximum if move == MOVES["REST"] else maximum // 2
            else:
                for healing, time in (("EFFECT_MORNING_SUN", 0),
                                      ("EFFECT_SYNTHESIS", 1),
                                      ("EFFECT_MOONLIGHT", 2)):
                    if effect == EFFECTS[healing]:
                        recognized = True
                        index = 2 - int(not h.rd("wLinkMode") and h.rd("wTimeOfDay") != time)
                        if context[16]:
                            index += 1 if context[16] == 2 else -1
                        quota = maximum // (8, 4, 2, 1)[index]
            if recognized and maximum:
                quota = max(1, quota)
            expected_prefix = bytearray(64)
            expected_prefix[:13] = bytes((move, effect, context[1], context[31],
                                         context[32], context[42], context[51], direction,
                                         *flags, int(recognized)))
            expected_prefix[13:15] = quota.to_bytes(2, "big")
            mem[0xa4b8:0xa4f8] = [0xa5] * 64
            before = bytes(mem[0xa000:0xa600])
            assert h.invoke("BossAI_FastExportActionPrefix", {**regs, "C": direction})
            assert h.outcome()["carry"]
            assert bytes(mem[0xa4b8:0xa4f8]) == expected_prefix, (context, expected_prefix)
            assert bytes(mem[0xc900:0xca44]) == context
            assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
            after = bytes(mem[0xa000:0xa600])
            assert before[:0x478] == after[:0x478]
            assert before[0x47c:0x4b8] == after[0x47c:0x4b8]
            assert before[0x4f8:] == after[0x4f8:]

        for i in range(1000):
            direction = i & 1
            move = MOVES[moves[i % len(moves)]]
            slot = 0xff if i % 3 else 0
            for name in ("wEnemyMonStatus", "wBattleMonStatus", "wOTPartyMon1Status",
                         "wEnemySubStatus1", "wEnemySubStatus3", "wEnemySubStatus4",
                         "wEnemySubStatus5", "wPlayerSubStatus1", "wPlayerSubStatus3",
                         "wPlayerSubStatus4", "wPlayerSubStatus5"):
                h.wr(name, rng.randrange(256) if i >= 100 else 0)
            h.wr("wEnemyMonStatus", i % 8 if i < 100 else rng.randrange(256))
            h.wr("wBattleMonStatus", i % 8 if i < 100 else rng.randrange(256))
            assert h.invoke("BossAI_BuildOwnedDamageContext", {
                **regs, "A": slot, "B": 1 - direction, "C": move})
            # Give flag producers explicit hit inputs including zero accuracy,
            # negation, survival and Substitute combinations.
            mem[0xc91f] = (0, 1, 128, 254, 255)[i % 5]
            mem[0xc90f] = rng.randrange(256)
            mem[0xc928] = i & 1
            mem[0xc929] = i >> 1 & 1
            expected = []
            for name in ("OwnCanAct" if not direction else "PlayerCanAct",
                         "EffectUncertainty", "HitUncertainty"):
                mem[0xc948] = 0
                assert h.invoke("BossAI_ValuePublicExchange." + name, regs)
                if not expected:
                    expected.append(int(h.outcome()["carry"]))
                expected.append(mem[0xc948])
            mem[0xc948] = rng.randrange(256)
            context = bytes(mem[0xc900:0xca44])
            before = bytes(mem[0xa000:0xa600])
            assert h.invoke("BossAI_FastExportActionFlags", {**regs, "C": direction})
            assert h.outcome()["carry"]
            assert bytes(mem[0xa478:0xa47c]) == bytes(expected), (i, expected)
            assert bytes(mem[0xc900:0xca44]) == context
            assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
            after = bytes(mem[0xa000:0xa600])
            assert before[:0x478] == after[:0x478] and before[0x47c:] == after[0x47c:]
            mem[0xc948] = 0
            assert h.invoke("BossAI_ValuePublicExchange.ItemUncertainty", regs)
            assert h.invoke("BossAI_ValuePublicExchange.VolatileUncertainty", regs)
            expected_setup = mem[0xc948]
            mem[0xc948] = context[72]
            before = bytes(mem[0xa000:0xa600])
            assert h.invoke("BossAI_FastExportSetupFlags", regs)
            assert mem[0xa47c] == expected_setup
            assert bytes(mem[0xc900:0xca44]) == context
            assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
            after = bytes(mem[0xa000:0xa600])
            assert before[:0x47c] == after[:0x47c] and before[0x47d:] == after[0x47d:]
            if i % 4 == 0:
                mem[0xc90d:0xc90f] = [0, 1] # capped overkill can hide raw ranges
            context = bytes(mem[0xc900:0xca44])
            mem[0xc948] = 0
            assert h.invoke("BossAI_ValuePublicExchange.MoveReplyPursuit", regs)
            assert h.invoke("BossAI_PublicDamageRange", regs)
            minimum, supported = h.outcome()["bc"], h.outcome()["carry"]
            maximum = int(rf.D) << 8 | int(rf.E)
            assert h.invoke("BossAI_ValuePublicExchange.RangeUncertainty", {
                **regs, "B": minimum >> 8, "C": minimum & 255, "HL": maximum})
            expected_range = (bytes((mem[0xc948], int(supported))) +
                              minimum.to_bytes(2, "big") + maximum.to_bytes(2, "big") +
                              bytes(mem[0xc92b:0xc92f]))
            mem[0xc948] = context[72]
            expected_context = bytes(mem[0xc900:0xca44])
            mem[0xc900:0xca44] = list(context)
            before = bytes(mem[0xa000:0xa600])
            assert h.invoke("BossAI_FastExportDamageRange", regs)
            assert bytes(mem[0xa47d:0xa487]) == expected_range, i
            assert bytes(mem[0xc900:0xca44]) == expected_context, i
            assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
            after = bytes(mem[0xa000:0xa600])
            assert before[:0x47d] == after[:0x47d] and before[0x487:] == after[0x487:]
            check_prefix(direction)
            cases += 1
        quota_cases = 0
        for move_name in ("RECOVER", "REST", "MORNING_SUN", "SYNTHESIS", "MOONLIGHT"):
            assert h.invoke("BossAI_BuildOwnedDamageContext", {
                **regs, "A": 0xff, "B": 1, "C": MOVES[move_name]})
            for weather in range(4):
                mem[0xc910] = weather
                for time in range(3):
                    h.wr("wTimeOfDay", time)
                    for link in (0, 1):
                        h.wr("wLinkMode", link)
                        for maximum in (0, 1, 999, 65535):
                            mem[0xc931:0xc933] = list(maximum.to_bytes(2, "big"))
                            for hp in (0, maximum):
                                mem[0xc92f:0xc931] = list(hp.to_bytes(2, "big"))
                                check_prefix(quota_cases & 1)
                                quota_cases += 1
        for direction in (2, 15, 255):
            before = bytes(mem[0xa000:0xa600])
            context = bytes(mem[0xc900:0xca44])
            assert h.invoke("BossAI_FastExportActionFlags", {**regs, "C": direction})
            assert not h.outcome()["carry"]
            assert bytes(mem[0xa000:0xa600]) == before
            assert bytes(mem[0xc900:0xca44]) == context
            assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
            assert h.invoke("BossAI_FastExportActionPrefix", {**regs, "C": direction})
            assert not h.outcome()["carry"]
            assert bytes(mem[0xa000:0xa600]) == before
            assert bytes(mem[0xc900:0xca44]) == context
            assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
        assert h.invoke("CloseSRAM")
    print(f"PASS: {cases} action/setup/range/prefix exports, {quota_cases} recovery prefixes and 6 rejections; "
          "context, DE/SP and SRAM footprints preserved")


if __name__ == "__main__":
    main()
