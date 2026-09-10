"""Incoming compact plans versus the reference, with producer data poisoned."""
from tools.boss_ai_fixtures.harness import Mon, MOVES, TYPES, open_harness
from tools.boss_ai_fixtures.cases import ITEMS
from tools.boss_ai_fixtures.damage import EFFECTS

# Defense boosts compile to opcode 9 with (stages, axis) in the hit bytes.
BOOSTS = {MOVES["HARDEN"]: (1, 1), MOVES["WITHDRAW"]: (1, 1), MOVES["BARRIER"]: (2, 1),
          MOVES["ACID_ARMOR"]: (2, 1), MOVES["AMNESIA"]: (2, 4)}


def expected_plan(h, context, regs):
    """Independent full-record expectation using the reference's stage APIs."""
    mem = h.pb.memory
    out = bytearray(48)
    out[0] = context[28]
    out[2:4] = context[31:33]
    out[43:45] = context[29:31]
    for stage, offset in (("PlayerCanAct", 5), ("EffectUncertainty", 6), ("HitUncertainty", 6)):
        mem[0xc900:0xca44] = list(context)
        mem[0xc948] = 0
        assert h.invoke("BossAI_ValuePublicExchange." + stage, regs)
        if stage == "PlayerCanAct":
            out[4] = int(h.outcome()["carry"])
        out[offset] |= mem[0xc948]
    if context[51] == 1 and context[2] == EFFECTS["EFFECT_PURSUIT"]:
        out[1] = 3
    elif context[28] in BOOSTS:
        out[1], (out[43], out[44]) = 9, BOOSTS[context[28]]
        out[6] = 0  # check flags only: no effect or hit uncertainty
    elif context[28] in (MOVES["RECOVER"], MOVES["REST"], MOVES["SYNTHESIS"]):
        maximum = int.from_bytes(context[49:51], "big")
        denominator = 1 if context[28] == MOVES["REST"] else 2
        if context[28] == MOVES["SYNTHESIS"]:
            index = 2 - int(not h.rd("wLinkMode") and h.rd("wTimeOfDay") != 1)
            if context[16]:
                index += 1 if context[16] == 2 else -1
            denominator = (8, 4, 2, 1)[index]
        out[1] = 2
        out[12:14] = (max(1, maximum // denominator) if maximum else 0).to_bytes(2, "big")
    else:
        # Multi-hit and False Swipe compile per-hit / uncapped endpoints from a
        # patched producer context and keep max-min deltas in bytes 7, 8, 23, 26.
        patched = bytearray(context)
        effect, hits = context[2], bytes(context[29:31])
        if effect == EFFECTS["EFFECT_SELFDESTRUCT"]:
            family = 8
        elif effect == EFFECTS["EFFECT_SUPER_FANG"]:
            family = 6
        elif effect == EFFECTS["EFFECT_FALSE_SWIPE"]:
            family = 7
            patched[2] = EFFECTS["EFFECT_NORMAL_HIT"]
        elif hits != bytes((1, 1)):
            family = 5
            patched[29:31] = bytes((1, 1))
        else:
            family = 1
        deltas = family in (5, 7)
        out[1], out[8], out[9] = family, 0 if deltas else 3, 15
        out[22], out[45] = context[1], 1  # forced Fire/Steel user
        contact = h.syms["MoveContactFlags"]
        assert h.invoke("GetFarByte", {"A": contact.bank, "HL": contact.address + context[28] - 1})
        is_contact = int(h.pb.register_file.A) != 0
        own_item = h.rd("wEnemyMonItem") if context[42] == 255 else h.rd("wOTPartyMon1Item")
        helmet = own_item == ITEMS["ROCKY_HELMET"] and not context[15] & 16 and is_contact
        if helmet:
            maximum = int.from_bytes(context[49:51], "big")
            out[20:22] = (max(1, maximum // 6) if maximum else 0).to_bytes(2, "big")
        effect = (1 if context[2] in (EFFECTS["EFFECT_LEECH_HIT"], EFFECTS["EFFECT_DREAM_EATER"])
                  else 2 if context[2] == EFFECTS["EFFECT_RECOIL_HIT"] else 0)
        descriptor = h.syms["BossAI_FastOwnCommandDescriptors"].address + 2 * (effect * 3 + int(helmet))
        out[46:48] = descriptor.to_bytes(2, "big")
        for regime in range(4):
            mem[0xc900:0xca44] = list(patched)
            mem[0xc90f] = context[15] & ~6 | regime << 1
            assert h.invoke("BossAI_ValuePublicExchange.MoveReplyPursuit", regs)
            assert h.invoke("BossAI_PublicDamageRange", regs)
            if h.outcome()["carry"]:
                out[11] |= 1 << regime
            raw_min, raw_max = bytes(mem[0xc92b:0xc92d]), bytes(mem[0xc92d:0xc92f])
            out[12 + 2 * regime:14 + 2 * regime] = raw_max
            if raw_min != raw_max:
                out[10] |= 1 << regime
            if deltas:
                delta = int.from_bytes(raw_max, "big") - int.from_bytes(raw_min, "big")
                out[(7, 8, 23, 26)[regime]] = delta & 255
                if delta >= 256:
                    out[1] = 0  # wider than a byte: the reply stays with the fallback
    return out


def edge_cases(h, regs):
    mem, rf = h.pb.memory, h.pb.register_file
    initial_sp = int(rf.SP)
    # Absence overrides poisoned AD direction, move, item and status metadata.
    mem[0xc900:0xcad8] = [0xa5] * 472
    mem[0xc936] = 0
    before_wram = bytes(mem[0xc900:0xcad8])
    before_sram = bytes(mem[0xa000:0xa600])
    assert h.invoke("BossAI_FastCompileReplyPlan", regs) and h.outcome()["carry"]
    absent = bytearray(48)
    absent[1] = 4
    assert bytes(mem[0xca8f:0xcabf]) == absent
    assert bytes(mem[0xc900:0xca8f]) == before_wram[:399]
    assert bytes(mem[0xcabf:0xcad8]) == before_wram[447:]
    after_sram = bytes(mem[0xa000:0xa600])
    assert all(a == b for i, (a, b) in enumerate(zip(before_sram, after_sram)) if i not in (0x489, 0x48a))
    for event in (0, 1):
        mem[0xa448:0xa460] = [0x5a] * 24
        before = bytes(mem[0xa448:0xa460])
        assert h.invoke("BossAI_FastExecuteReplyPlan", {**regs, "A": event, "HL": 0xa448})
        assert h.outcome()["carry"] and bytes(mem[0xa448:0xa460]) == before
    for direction, move in ((1, "TACKLE"), (255, "TACKLE"), (0, "REST")):
        mem[0xc91b], mem[0xc91c], mem[0xc936] = direction, MOVES[move], MOVES["TACKLE"]
        before_wram, before_sram = bytes(mem[0xc900:0xcad8]), bytes(mem[0xa000:0xa600])
        assert h.invoke("BossAI_FastCompileReplyPlan", regs) and not h.outcome()["carry"]
        assert bytes(mem[0xc900:0xcad8]) == before_wram and bytes(mem[0xa000:0xa600]) == before_sram
    for event in (2, 255):
        before_sram = bytes(mem[0xa000:0xa600])
        assert h.invoke("BossAI_FastExecuteReplyPlan", {**regs, "A": event, "HL": 0xa448})
        assert not h.outcome()["carry"] and bytes(mem[0xa000:0xa600]) == before_sram
    # A per-hit roll range wider than a byte leaves the family to the fallback:
    # the header is written, the opcode stays 0 and the executor rejects.
    mem[0xc900:0xcad8] = [0] * 472
    assert h.invoke("BossAI_BuildOwnedDamageContext", {**regs, "A": 0xff, "B": 0, "C": MOVES["PIN_MISSILE"]})
    mem[0xc900] = 100
    mem[0xc905:0xc909] = [3, 0xe7, 0, 1]  # attack 999, defense 1
    mem[0xc909:0xc90d] = [TYPES["BUG"], TYPES["BUG"], TYPES["GRASS"], TYPES["PSYCHIC_TYPE"]]
    mem[0xc936] = MOVES["PIN_MISSILE"]
    assert h.invoke("BossAI_FastCompileReplyPlan", regs) and not h.outcome()["carry"]
    assert mem[0xca8f] == MOVES["PIN_MISSILE"] and mem[0xca90] == 0, mem[0xca90]
    before = bytes(mem[0xa448:0xa478])
    assert h.invoke("BossAI_FastExecuteReplyPlan", {**regs, "A": 0, "HL": 0xa448})
    assert not h.outcome()["carry"] and bytes(mem[0xa448:0xa478]) == before
    assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
    override_probe(h, regs)


def override_probe(h, regs):
    """A live FSV_OVERRIDE replaces the amount, but support stays the record's:
    the executor's outputs do not depend on the override's supported bit."""
    mem = h.pb.memory
    own, own_max, player, player_max = 999, 999, 703, 703
    regime = int(3 * player < player_max) | int(2 * own > own_max) << 1
    mem[0xc900:0xcad8] = [0] * 472
    assert h.invoke("BossAI_BuildOwnedDamageContext", {**regs, "A": 0xff, "B": 0, "C": MOVES["TACKLE"]})
    context = bytearray(324)
    context[:51] = bytes(mem[0xc900:0xc933])
    context[9:13] = bytes((TYPES["FIRE"], TYPES["STEEL"], TYPES["ICE"], TYPES["ICE"]))
    context[25:27] = own_max.to_bytes(2, "big")
    context[49:51] = player_max.to_bytes(2, "big")
    context[51:55] = bytes((0, 0xff, MOVES["TACKLE"], MOVES["TACKLE"]))
    context[59:61] = own_max.to_bytes(2, "big")
    context[65:67] = player_max.to_bytes(2, "big")
    context[140] = 2
    context[141:192] = context[:51]
    mem[0xc900:0xca44] = list(context)
    assert h.invoke("BossAI_FastCompileReplyPlan", regs) and h.outcome()["carry"]
    plan = bytearray(mem[0xca8f:0xcabf])
    assert plan[1] == 1 and plan[11] & 1 << regime, plan.hex()
    mem[0xa3fa:0xa3fc] = list(own_max.to_bytes(2, "big"))
    mem[0xa422:0xa424] = list(player_max.to_bytes(2, "big"))
    results = {}
    for supported in (True, False):
        for override_bits in (0, 2):
            record = bytearray(plan)
            if not supported:
                record[11] &= ~(1 << regime)
            mem[0xca8f:0xcabf] = list(record)
            mem[0xa4b4:0xa4b8] = [1, 0, 100, override_bits]
            state = bytearray(24)
            state[:4] = own.to_bytes(2, "big") + player.to_bytes(2, "big")
            state[16] = 0x40
            mem[0xa448:0xa460] = list(state)
            assert h.invoke("BossAI_FastExecuteReplyPlan", {**regs, "A": 0, "HL": 0xa448})
            assert h.outcome()["carry"]
            results[supported, override_bits] = (bytes(mem[0xa448:0xa44c]), mem[0xa458])
    mem[0xa4b4] = 0
    for supported in (True, False):
        assert results[supported, 0] == results[supported, 2], results
    assert results[True, 0][0] == (own - 100).to_bytes(2, "big") + player.to_bytes(2, "big"), results
    assert results[True, 0] != results[False, 0], results


def main():
    count = 0
    with open_harness("pokegold_ai_reference") as h:
        h.seed_battle(Mon.of("CHARIZARD", 50), Mon.of("DEWGONG", 50))
        mem, rf = h.pb.memory, h.pb.register_file
        regs = {"D": 0xc9, "E": 0}
        initial_sp = int(rf.SP)
        assert h.invoke("OpenSRAM", {"A": 0})
        for move in ("TACKLE", "FIRE_BLAST", "GIGA_DRAIN", "DOUBLE_EDGE",
                     "STRUGGLE", "SEISMIC_TOSS", "DRAGON_RAGE", "RECOVER",
                     "REST", "SYNTHESIS", "PURSUIT", "SPLASH", "SNORE", "DREAM_EATER", "LEECH_LIFE",
                     "FURY_SWIPES", "BONEMERANG", "TWINEEDLE", "SUPER_FANG", "FALSE_SWIPE", "EXPLOSION",
                     "HARDEN", "BARRIER", "AMNESIA"):
            for item in (0, ITEMS["ROCKY_HELMET"]):
                h.wr("wEnemyMonItem", item)
                for maximum, player_max in ((9, 17), (999, 703), (65535, 65535), (50000, 65535)):
                    for mode in ("normal", "sleep", "wake", "accuracy0", "substitute", "switch", "switch_denied", "unsupported", "unsupported0", "bench"):
                        h.wr("wBattleMonStatus", 2 if mode in ("sleep", "switch_denied") else int(mode == "wake"))
                        assert h.invoke("BossAI_BuildOwnedDamageContext", {
                            **regs, "A": 0xff, "B": 0, "C": MOVES[move]})
                        context = bytearray(324)
                        context[:51] = bytes(mem[0xc900:0xc933])
                        context[9:13] = bytes((TYPES["FIRE"], TYPES["STEEL"], TYPES["ICE"], TYPES["ICE"]))
                        context[25:27] = maximum.to_bytes(2, "big")
                        context[49:51] = player_max.to_bytes(2, "big")
                        if mode == "accuracy0":
                            context[31] = 0
                        if mode == "substitute":
                            context[15] |= 16  # AD_SUBSTITUTE_F
                        if mode.startswith("unsupported"):
                            context[15] |= 128
                            if mode == "unsupported0":
                                context[1] = 0
                        if mode == "bench":
                            context[42] = 0
                            h.wr("wOTPartyMon1Item", item)
                            h.wr("wEnemyMonItem", 0 if item else ITEMS["ROCKY_HELMET"])
                        else:
                            h.wr("wEnemyMonItem", item)
                        context[51:55] = bytes((int(mode.startswith("switch")), 0xff, MOVES["TACKLE"], MOVES[move]))
                        context[59:61] = maximum.to_bytes(2, "big")
                        context[65:67] = player_max.to_bytes(2, "big")
                        context[140] = 2  # incoming template exists, no cached range
                        context[141:192] = context[:51]
                        expected = expected_plan(h, context, regs)
                        mem[0xc900:0xca44] = list(context)
                        mem[0xca44:0xcad8] = [0x69] * 148
                        owned_plans = bytes(mem[0xa2f8:0xa3f8])
                        assert h.invoke("BossAI_FastCompileReplyPlan", regs)
                        assert h.outcome()["carry"], (move, mode)
                        plan = bytes(mem[0xca8f:0xcabf])
                        assert plan == expected, (move, item, maximum, mode, plan.hex(), expected.hex())
                        assert bytes(mem[0xa2f8:0xa3f8]) == owned_plans
                        assert bytes(mem[0xca44:0xca8f]) == bytes([0x69] * 75)
                        assert bytes(mem[0xcabf:0xcad8]) == bytes([0x69] * 25)
                        assert bytes(mem[0xc933:0xca44]) == bytes(context[51:])
                        assert mem[0xc90f] == context[15] and mem[0xc922] == context[34]
                        for own, player in ((0, player_max), (maximum, 0), (1, 1),
                                            (maximum, player_max), (maximum // 2, player_max // 3),
                                            (maximum // 2 + 1, player_max // 3 + 1),
                                            (maximum - 1, 1), (1, player_max)):
                            for event in (0, 1):
                                mem[0xc900:0xca44] = list(context)
                                mem[0xc939:0xc93b] = list(own.to_bytes(2, "big"))
                                mem[0xc93f:0xc941] = list(player.to_bytes(2, "big"))
                                mem[0xc950] = 0x80 | event * 2
                                mem[0xc948] = 0x40
                                assert h.invoke("BossAI_ValuePublicExchange.Reply", regs)
                                expected = (bytes(mem[0xc939:0xc93b]) + bytes(mem[0xc93f:0xc941]), mem[0xc948])
                                mem[0xc900:0xca8f] = [0xa5] * 399
                                mem[0xa3fa:0xa3fc] = list(maximum.to_bytes(2, "big"))
                                mem[0xa422:0xa424] = list(player_max.to_bytes(2, "big"))
                                cont = 0xa448 if count & 1 else 0xa460
                                state = bytearray([0x5a] * 24)
                                state[:4] = own.to_bytes(2, "big") + player.to_bytes(2, "big")
                                state[16] = 0x40
                                mem[cont:cont + 24] = list(state)
                                before = bytes(mem[0xa000:0xa600])
                                assert h.invoke("BossAI_FastExecuteReplyPlan.FlagsOnly", {**regs, "A": event, "HL": cont})
                                assert h.outcome()["carry"]
                                expected_flag_state = bytearray(state)
                                expected_flag_state[16] = expected[1]
                                assert bytes(mem[cont:cont + 24]) == expected_flag_state
                                flag_after = bytes(mem[0xa000:0xa600])
                                flag_mutable = {cont - 0xa000 + 16, *range(0x530, 0x560)}
                                assert all(a == b for i, (a, b) in enumerate(zip(before, flag_after)) if i not in flag_mutable)
                                mem[cont:cont + 24] = list(state)
                                assert h.invoke("BossAI_FastExecuteReplyPlan", {**regs, "A": event, "HL": cont})
                                assert h.outcome()["carry"]
                                actual = (bytes(mem[cont:cont + 4]), mem[cont + 16])
                                assert actual == expected, (move, item, maximum, mode, own, player, event, actual, expected, plan.hex())
                                after = bytes(mem[0xa000:0xa600])
                                mutable = {*range(cont - 0xa000, cont - 0xa000 + 4), cont - 0xa000 + 16, *range(0x530, 0x560)}
                                assert all(a == b for i, (a, b) in enumerate(zip(before, after)) if i not in mutable)
                                assert bytes(mem[0xc900:0xca8f]) == bytes([0xa5] * 399)
                                assert bytes(mem[0xca8f:0xcabf]) == plan
                                assert bytes(mem[0xcabf:0xcad8]) == bytes([0x69] * 25)
                                assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
                                count += 1
        edge_cases(h, regs)
        assert h.invoke("CloseSRAM")
    print(f"PASS: {count} incoming action/reference comparisons, {count // 16} full plans, producer poisoning, record guards, absent/rejected cases and the wide-range fallback")


if __name__ == "__main__":
    main()
