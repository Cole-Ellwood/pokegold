"""Compare complete owned amount plans with direct reference producers."""
from tools.boss_ai_fixtures.harness import Mon, MOVES, TYPES, open_harness
from tools.boss_ai_fixtures.cases import ITEMS
from tools.boss_ai_fixtures.damage import EFFECTS


def main():
    moves = ("TACKLE", "FIRE_BLAST", "GIGA_DRAIN", "DOUBLE_EDGE", "STRUGGLE",
             "SEISMIC_TOSS", "DRAGON_RAGE", "RECOVER", "REST", "SYNTHESIS",
             "PURSUIT", "SPLASH", "SNORE", "DREAM_EATER", "EXPLOSION",
             "FALSE_SWIPE", "SUPER_FANG", "FURY_SWIPES", "HARDEN", "AMNESIA")
    count = 0
    with open_harness("pokegold_ai_reference") as h:
        h.seed_battle(Mon.of("CHARIZARD", 50), Mon.of("DEWGONG", 50))
        mem, rf = h.pb.memory, h.pb.register_file
        regs = {"D": 0xc9, "E": 0}
        initial_sp = int(rf.SP)
        assert h.invoke("OpenSRAM", {"A": 0})
        descriptor = h.syms["BossAI_FastOwnCommandDescriptors"].address
        for move_name in moves:
            for item in (0, ITEMS["LIFE_ORB"], ITEMS["SHELL_BELL"]):
                h.wr("wEnemyMonItem", item)
                for state in range(4):
                    h.wr("wEnemyMonStatus", (0, 1, 0x40, 0)[state])
                    h.wr("wEnemySubStatus3", (0, 0, 0, 0x80)[state])
                    assert h.invoke("BossAI_BuildOwnedDamageContext", {
                        **regs, "A": 0xff, "B": 1, "C": MOVES[move_name]})
                    mem[0xc933] = 0
                    # Cross actual own Fire/Steel and target Ice regimes. The
                    # reference compiler receives exactly the same public facts.
                    mem[0xc909:0xc90d] = [TYPES["FIRE"], TYPES["STEEL"],
                                           TYPES["ICE"], TYPES["ICE"]]
                    if state == 3:
                        mem[0xc914] = 2  # AD_HITS scratch must not classify a plan
                    if move_name == "TACKLE" and state == 2:
                        mem[0xc91d] = 2  # reject inconsistent min/max hit endpoints
                    mem[0xc91f] = (0, 128, 254, 255)[state]
                    mem[0xc948] = 0xa5
                    context = bytes(mem[0xc900:0xca44])
                    expected = bytearray(64)
                    slot = count % 4
                    expected[:4] = bytes((slot, context[51], context[42], context[28]))
                    expected[5:7] = context[31:33]
                    flags = []
                    for stage in ("OwnCanAct", "EffectUncertainty", "HitUncertainty"):
                        mem[0xc948] = 0
                        assert h.invoke("BossAI_ValuePublicExchange." + stage, regs)
                        if not flags:
                            flags.append(int(h.outcome()["carry"]))
                        flags.append(mem[0xc948])
                    expected[7:10] = bytes((flags[0], flags[1], flags[2] | flags[3]))
                    mem[0xc948] = 0
                    assert h.invoke("BossAI_ValuePublicExchange.ItemUncertainty", regs)
                    assert h.invoke("BossAI_ValuePublicExchange.VolatileUncertainty", regs)
                    expected[11] = mem[0xc948]
                    expected[58:60] = context[29:31]
                    expected[62:64] = context[33:35]
                    mem[0xc948] = context[72]
                    recovery = move_name in ("RECOVER", "REST", "SYNTHESIS")
                    represented = recovery or (move_name not in (
                        "EXPLOSION", "FALSE_SWIPE", "SUPER_FANG", "HARDEN", "AMNESIA")
                        and context[29:31] == bytes((1, 1)))
                    maximum = int.from_bytes(context[49:51], "big")
                    if recovery:
                        denominator = 1 if move_name == "REST" else 2
                        if move_name == "SYNTHESIS":
                            index = 2 - int(not h.rd("wLinkMode") and h.rd("wTimeOfDay") != 1)
                            if context[16]:
                                index += 1 if context[16] == 2 else -1
                            denominator = (8, 4, 2, 1)[index]
                        quota = max(1, maximum // denominator) if maximum else 0
                        expected[4] = 2
                        expected[53:55] = quota.to_bytes(2, "big")
                    elif represented:
                        expected[4] = 1
                        expected[12:14] = bytes((3, 15))
                        expected[57] = 1  # forced Fire/Steel above
                        effect = (1 if context[2] in (EFFECTS["EFFECT_LEECH_HIT"],
                                                      EFFECTS["EFFECT_DREAM_EATER"])
                                  else 2 if context[2] == EFFECTS["EFFECT_RECOIL_HIT"] else 0)
                        item_tag = (0, ITEMS["LIFE_ORB"], ITEMS["SHELL_BELL"]).index(item)
                        expected[60:62] = (descriptor + 2 * (3 * effect + item_tag)).to_bytes(2, "big")
                        if item_tag == 1:
                            expected[55:57] = (max(1, maximum // 10) if maximum else 0).to_bytes(2, "big")
                        for regime in range(4):
                            mem[0xc900:0xca44] = list(context)
                            mem[0xc90f] = (context[15] & ~6) | regime << 1
                            assert h.invoke("BossAI_ValuePublicExchange.MoveReplyPursuit", regs)
                            assert h.invoke("BossAI_PublicDamageRange", regs)
                            supported = h.outcome()["carry"]
                            raw_min = bytes(mem[0xc92b:0xc92d])
                            raw_max = bytes(mem[0xc92d:0xc92f])
                            expected[16 + 2 * regime:18 + 2 * regime] = raw_min
                            expected[24 + 2 * regime:26 + 2 * regime] = raw_max
                            if supported:
                                expected[15] |= 1 << regime
                            if raw_min != raw_max:
                                expected[14] |= 1 << regime
                            # Raw amounts are independent of the actual HP
                            # values once the two flags and other facts are fixed.
                            for hp in (1, 65535):
                                mem[0xc900:0xca44] = list(context)
                                mem[0xc90f] = (context[15] & ~6) | regime << 1
                                mem[0xc90d:0xc90f] = list(hp.to_bytes(2, "big"))
                                mem[0xc92f:0xc931] = list(hp.to_bytes(2, "big"))
                                assert h.invoke("BossAI_ValuePublicExchange.MoveReplyPursuit", regs)
                                assert h.invoke("BossAI_PublicDamageRange", regs)
                                assert h.outcome()["carry"] == supported
                                assert bytes(mem[0xc92b:0xc92f]) == raw_min + raw_max
                    mem[0xc900:0xca44] = list(context)
                    mem[0xa000:0xa600] = [0xa5] * 1536
                    before = bytes(mem[0xa000:0xa600])
                    assert h.invoke("BossAI_FastCompileOwnedPlan", {**regs, "C": slot})
                    assert h.outcome()["carry"] == represented, (move_name, item, state)
                    offset = 0x2f8 + 64 * slot
                    after = bytes(mem[0xa000:0xa600])
                    actual = after[offset:offset + 64]
                    assert actual == expected, (move_name, item, state,
                                                [(i, a, b) for i, (a, b) in enumerate(zip(actual, expected)) if a != b])
                    assert before[:offset] == after[:offset]
                    assert before[offset + 64:0x478] == after[offset + 64:0x478]
                    assert before[0x4f8:] == after[0x4f8:]
                    new_context = bytes(mem[0xc900:0xca44])
                    # Exact allowed damage-kernel output/roll/hit scratch.
                    mutable = {20, 21, 22, 23, 24, 35, 36, 37, 43, 44, 45, 46}
                    assert all(a == b for i, (a, b) in enumerate(zip(context, new_context)) if i not in mutable)
                    assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
                    count += 1
        for slot, direction in ((4, 1), (255, 1), (0, 0), (3, 2)):
            mem[0xc91b] = direction
            context = bytes(mem[0xc900:0xca44])
            before = bytes(mem[0xa000:0xa600])
            assert h.invoke("BossAI_FastCompileOwnedPlan", {**regs, "C": slot})
            assert not h.outcome()["carry"]
            assert bytes(mem[0xa000:0xa600]) == before
            assert bytes(mem[0xc900:0xca44]) == context
            assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
        assert h.invoke("CloseSRAM")
    print(f"PASS: {count} complete owned plans, four-regime raw HP independence and 4 no-write rejections")


if __name__ == "__main__":
    main()
