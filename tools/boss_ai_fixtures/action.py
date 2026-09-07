"""Immediate public HP facts compared with combat's HP fraction routines."""
from tools.boss_ai_fixtures.harness import MOVES, TYPES
from tools.boss_ai_fixtures.layout import AV_SIZE, AV_PREPARED_SIZE, AV_PREPARED_DAMAGE


def run_candidate_check(h, case):
    spec = case.candidate_check
    for name in ("wEnemyMonItem", "wEnemyDisabledMove", "wEnemyChoiceLockedMove",
                 "wEnemyWrapCount", "wLinkMode", "wEnemyIsSwitching", "wCurEnemyMoveNum"):
        h.wr(name, 0)
    for prefix in ("wEnemySubStatus1", "wPlayerSubStatus1"):
        for i in range(5):
            h.wr(prefix, 0, i)
    h.wr("wBattleMode", 2)
    h.wr("wCurOTMon", spec.get("active", 3))
    h.wr("wOTPartyCount", spec.get("count", 6))
    h.wr("wCurEnemyMove", case.boss.moves[0] if case.boss.moves else 0)
    for i, hp in enumerate(spec.get("party_hp", [100, 1, 0, 200, 50, 0])):
        h.wr("wOTPartyMon1HP", hp >> 8, i * 48)
        h.wr("wOTPartyMon1HP", hp & 255, i * 48 + 1)
    for i, pp in enumerate(spec.get("pp", [20] * 4)):
        h.wr("wEnemyMonPP", pp, i)
    for key, value in case.extra.items():
        h.wr(key[0], value, key[1]) if isinstance(key, tuple) else h.wr(key, value)
    spans = (("wEnemyMon", 48), ("wBattleMon", 48), ("wOTPartyMon1Species", 288),
             ("wEnemySubStatus1", 5), ("wPlayerSubStatus1", 5), ("wEnemyAIMoveScores", 4),
             ("wBossAITemp", 5), ("wEnemyChoiceLockedMove", 1), ("wCurEnemyMove", 1),
             ("wCurEnemyMoveNum", 1), ("wEnemySwitchMonIndex", 1), ("wEnemySwitchMonParam", 1))
    before = {(name, i): h.rd(name, i) for name, size in spans for i in range(size)}
    pointer = h.syms["wTilemap"].address
    rf = h.pb.register_file
    start_sp = int(rf.SP)
    random_calls = []
    symbol = h.syms["Random"]
    h.pb.hook_register(symbol.bank, symbol.address, lambda _: random_calls.append(1), None)
    registers = {"A": spec.get("kind", 0), "D": pointer >> 8, "E": pointer & 255}
    try:
        returned = h.invoke("BossAI_EnumeratePublicActions", registers)
    finally:
        h.pb.hook_deregister(symbol.bank, symbol.address)
    out = h.outcome()
    observed = [h.rd("wTilemap", i) for i in range(8)]
    expected = ([MOVES[x] if x else 0 for x in spec.get("moves", [None] * 4)]
                + [spec.get("switches", 19), spec.get("mode", 0),
                   MOVES[spec["forced"]] if spec.get("forced") else 0, spec.get("slot", 0)])
    errors = []
    if observed != expected:
        errors.append(f"candidate set {observed} != {expected}")
    if int(rf.SP) != start_sp or (int(rf.D) << 8 | int(rf.E)) != pointer:
        errors.append("candidate enumeration lost stack/context pointer")
    if any(h.rd(*key) != value for key, value in before.items()):
        errors.append("candidate enumeration mutated battle/party/selection state")
    if random_calls:
        errors.append("candidate enumeration consumed RNG")
    if spec.get("hidden_invariance"):
        h.wr("wBattleMonItem", 255)
        h.wr("wCurPlayerMove", MOVES["EXPLOSION"])
        for i in range(4):
            h.wr("wBattleMonMoves", MOVES["EXPLOSION"], i)
        returned &= h.invoke("BossAI_EnumeratePublicActions", registers)
        if observed != [h.rd("wTilemap", i) for i in range(8)]:
            errors.append("candidate enumeration depends on private player item/moves/input")
    if spec.get("reference_parse"):
        # Execute real non-link action parsing and held restrictions after the
        # pure-state assertions. This includes its actual first-slot Choice
        # synchronization, Encore precedence and Assault Vest fallback.
        returned &= h.invoke("ParseEnemyAction")
        parsed = [h.rd("wCurEnemyMove"), h.rd("wCurEnemyMoveNum")]
        if observed[6:8] != parsed:
            errors.append(f"forced action {observed[6:8]} != combat parser {parsed}")
    out.update(returned=returned, damage_errors=errors, memory={}, haki_spent=False,
               candidates=observed)
    return out


def run_exchange_check(h, case):
    spec = case.exchange_check
    slot = spec.get("slot", 255)
    for name in ("wEnemyMonItem", "wBattleMonItem", "wBattleWeather", "wEnemyScreens",
                 "wPlayerScreens", "wBossAIWinconMonIdx", "wCurOTMon"):
        h.wr(name, 0)
    for key, value in case.extra.items():
        h.wr(key[0], value, key[1]) if isinstance(key, tuple) else h.wr(key, value)
    for side, hp, maximum in (("wEnemyMon", spec["own_hp"], spec["own_max"]),
                             ("wBattleMon", spec["player_hp"], spec["player_max"])):
        h.wr_be16(side + "HP", hp)
        h.wr_be16(side + "MaxHP", maximum)
    returned = True
    for prefix, mon in (("wEnemy", case.boss), ("wPlayer", case.player)):
        for field, value in (("Attack", mon.atk), ("Defense", mon.deff), ("Speed", mon.spe),
                             ("SpAtk", mon.spa), ("SpDef", mon.spd)):
            h.wr_be16(prefix + field, value)
    for enemy in (0, 1):
        h.wr("wApplyStatLevelMultipliersToEnemy", enemy)
        returned &= h.invoke("ApplyStatLevelMultiplierOnAllStats")
        returned &= h.invoke("ApplyStatusEffectOnEnemyStats" if enemy else "ApplyStatusEffectOnPlayerStats")
    h.wr("hBattleTurn", 1)
    expected_successor = spec.get("successor")
    expected_value = spec.get("value")
    if spec.get("reference_damage"):
        # Normal single-hit damage, either a move without a reply or a switch
        # receiving one reply. Obtain the amount from actual combat first.
        incoming = spec["reference_damage"] == "incoming"
        h.wr("wCriticalHit", 0)
        h.wr("wJohtoBadges", 0)
        h.wr("wKantoBadges", 0)
        returned &= h.invoke("AIGetEnemyMove_HL", {"A": MOVES[spec["reply"] if incoming else spec["move"]]})
        if incoming:
            for i in range(7):
                h.wr("wPlayerMoveStruct", h.rd("wEnemyMoveStruct", i), i)
            h.wr("hBattleTurn", 0)
        for command in ("BattleCommand_DamageStats", "BattleCommand_DamageCalc", "BattleCommand_Stab"):
            returned &= h.invoke(command)
        raw_max = h.rd_be16("wCurDamage")
        raw_min = max(1, raw_max * 217 // 255) if raw_max else 0
        if incoming:
            after = max(0, spec["own_hp"] - (raw_min if spec.get("branch", 0) & 32 else raw_max))
            expected_successor = [after, spec["player_hp"]]
            expected_value = (1024 - spec["own_hp"] * 128 // spec["own_max"]
                              + after * 128 // spec["own_max"] - (256 if after == 0 else 0))
        else:
            after = max(0, spec["player_hp"] - (raw_max if spec.get("branch", 0) & 16 else raw_min))
            expected_successor = [spec["own_hp"], after]
            expected_value = (1024 + spec["player_hp"] * 128 // spec["player_max"]
                              - after * 128 // spec["player_max"] + (256 if after == 0 else 0))
    if slot != 255:
        offset = slot * 48
        h.wr("wOTPartyCount", 6)
        for field, value in (("Species", case.boss.species), ("Level", case.boss.level),
                             ("Status", case.boss.status), ("Item", h.rd("wEnemyMonItem"))):
            h.wr("wOTPartyMon1" + field, value, offset)
        for field, value in (("HP", spec["own_hp"]), ("MaxHP", spec["own_max"]),
                             ("Attack", case.boss.atk), ("Defense", case.boss.deff),
                             ("Speed", case.boss.spe), ("SpclAtk", case.boss.spa),
                             ("SpclDef", case.boss.spd)):
            h.wr("wOTPartyMon1" + field, value >> 8, offset)
            h.wr("wOTPartyMon1" + field, value & 255, offset + 1)
    pointer = h.syms["wTilemap"].address
    spans = (("wEnemyMon", 48), ("wBattleMon", 48), ("wOTPartyMon1Species", 288),
             ("wEnemyMoveStruct", 14), ("wEnemyStatLevels", 7), ("wPlayerStatLevels", 7),
             ("wEnemySubStatus1", 5), ("wPlayerSubStatus1", 5), ("wCurDamage", 2), ("wBossAITemp", 5))
    before = {(name, i): h.rd(name, i) for name, size in spans for i in range(size)}
    rf = h.pb.register_file
    initial_sp = int(rf.SP)
    registers = {
        "A": slot, "B": spec.get("kind", 0), "C": MOVES[spec["move"]],
        "HL": (MOVES[spec["reply"]] << 8 if spec.get("reply") else 0) | spec.get("branch", 0),
        "D": pointer >> 8, "E": pointer & 255}
    random_calls = []
    random_symbol = h.syms["Random"]
    h.pb.hook_register(random_symbol.bank, random_symbol.address, lambda _: random_calls.append(1), None)
    try:
        returned &= h.invoke("BossAI_ValuePublicExchange", registers)
    finally:
        h.pb.hook_deregister(random_symbol.bank, random_symbol.address)
    out = h.outcome()
    errors = []
    successor = [(h.rd("wTilemap", n) << 8) | h.rd("wTilemap", n + 1) for n in (57, 63)]
    if expected_successor is not None and successor != expected_successor:
        errors.append(f"exchange successor {successor} != {expected_successor}")
    if expected_value is not None and out["bc"] != expected_value:
        errors.append(f"exchange value {out['bc']} != {expected_value}")
    uncertain = h.rd("wTilemap", 72)
    if uncertain != spec.get("uncertain", 0):
        errors.append(f"exchange uncertainty {uncertain} != {spec.get('uncertain', 0)}")
    if out["carry"] != (uncertain == 0):
        errors.append("certainty return disagrees with uncertainty flags")
    if int(rf.SP) != initial_sp or (int(rf.D) << 8 | int(rf.E)) != pointer:
        errors.append("exchange lost stack or caller context")
    if any(h.rd(*key) != value for key, value in before.items()):
        errors.append("exchange changed live battle/party/score state")
    if random_calls:
        errors.append("exchange consumed battle RNG")
    # Direct callers own only AV_SIZE bytes, even if reserved branch bits are set.
    # The optional prepared entry gets a 51-byte template and validity byte.
    baseline = (out["bc"], out["carry"], successor, uncertain,
                bytes(h.rd("wTilemap", i) for i in range(81, AV_SIZE)))
    def signature(region="wTilemap"):
        current = h.outcome()
        hp = [h.rd(region, n) << 8 | h.rd(region, n + 1) for n in (57, 63)]
        return (current["bc"], current["carry"], hp, h.rd(region, 72),
                bytes(h.rd(region, i) for i in range(81, AV_SIZE)))
    h.pb.hook_register(random_symbol.bank, random_symbol.address, lambda _: random_calls.append(1), None)
    for i in range(AV_SIZE, AV_PREPARED_SIZE + 15):
        h.wr("wTilemap", 0xa5, i)
    legacy_regs = dict(registers, HL=registers["HL"] | 0xc0)
    returned &= h.invoke("BossAI_ValuePublicExchange", legacy_regs)
    if signature() != baseline or any(h.rd("wTilemap", i) != 0xa5 for i in range(AV_SIZE, AV_PREPARED_SIZE + 15)):
        errors.append("legacy exchange violated its AV_SIZE-byte contract with reserved bits set")
    h.wr("wTilemap", spec.get("branch", 0) | 0xc0, 80)
    returned &= h.invoke("BossAI_ValuePublicExchangeFromContext", registers)
    if signature() != baseline or any(h.rd("wTilemap", i) != 0xa5 for i in range(AV_SIZE, AV_PREPARED_SIZE + 15)):
        errors.append("context wrapper violated its AV_SIZE-byte contract with reserved bits set")
    returned &= h.invoke("BossAI_PreparePublicAction", registers)
    template = [h.rd("wTilemap", i) for i in range(AV_SIZE, AV_PREPARED_SIZE)]
    if "cache_ready" in spec and bool(h.rd("wTilemap", AV_PREPARED_DAMAGE) & 1) != spec["cache_ready"]:
        errors.append("wrong outgoing raw-cache eligibility")
    cache_hits = []
    cache_symbol = h.syms["BossAI_ValuePublicExchange.use_prepared_range"]
    h.pb.hook_register(cache_symbol.bank, cache_symbol.address, lambda _: cache_hits.append(1), None)
    returned &= h.invoke("BossAI_ValuePreparedPublicExchange", registers)
    h.pb.hook_deregister(cache_symbol.bank, cache_symbol.address)
    if "cache_hits" in spec and len(cache_hits) != spec["cache_hits"]:
        errors.append(f"raw cache used {len(cache_hits)} times, expected {spec['cache_hits']}")
    if signature() != baseline:
        errors.append(f"prepared exchange {signature()} != original {baseline}")
    if template != [h.rd("wTilemap", i) for i in range(AV_SIZE, AV_PREPARED_SIZE)]:
        errors.append("prepared exchange mutated its outgoing template")
    if any(h.rd("wTilemap", i) != 0xa5 for i in range(AV_PREPARED_SIZE, AV_PREPARED_SIZE + 15)):
        errors.append("prepared exchange exceeded its AV_PREPARED_SIZE-byte context")
    if int(rf.SP) != initial_sp or (int(rf.D) << 8 | int(rf.E)) != pointer:
        errors.append("prepared exchange lost stack or caller context")
    if any(h.rd(*key) != value for key, value in before.items()):
        errors.append("prepared exchange changed live state")
    if spec.get("branch_reuse"):
        mode = h.rd("wTilemap", 80) & 0x40
        reference_pointer = h.syms["wAttrmap"].address
        for order in (4, 12):
            for endpoint in (0, 16, 32, 48):
                for misses in range(4):
                    branch = order | endpoint | misses
                    h.wr("wTilemap", mode | branch, 80)
                    returned &= h.invoke("BossAI_ValuePreparedPublicExchange", registers)
                    prepared = signature()
                    reference_regs = dict(registers, HL=(registers["HL"] & 0xff00) | branch,
                                          D=reference_pointer >> 8, E=reference_pointer & 255)
                    returned &= h.invoke("BossAI_ValuePublicExchange", reference_regs)
                    if prepared != signature("wAttrmap"):
                        errors.append(f"reused preparation differs on event branch {branch}")
        h.wr("wTilemap", mode | spec.get("branch", 0), 80)
        returned &= h.invoke("BossAI_ValuePreparedPublicExchange", registers)
        if template != [h.rd("wTilemap", i) for i in range(AV_SIZE, AV_PREPARED_SIZE)]:
            errors.append("event branches mutated prepared facts")
    h.pb.hook_deregister(random_symbol.bank, random_symbol.address)
    if random_calls:
        errors.append("prepared/legacy comparison consumed battle RNG")
    if spec.get("defense_reference"):
        # Run combat's real stat command and damage arithmetic in the specified
        # action order. Only deterministic, noncritical successful hits here.
        ref = spec["defense_reference"]
        own_boost = ref["side"] == "own"
        boost = spec["move"] if own_boost else spec["reply"]
        attack = spec["reply"] if own_boost else spec["move"]
        command = {"HARDEN":"DefenseUp", "WITHDRAW":"DefenseUp",
                   "BARRIER":"DefenseUp2", "ACID_ARMOR":"DefenseUp2",
                   "AMNESIA":"SpecialDefenseUp2"}[boost]
        axis = 4 if boost == "AMNESIA" else 1
        record = 81 if own_boost else 85
        projected = [h.rd("wTilemap", record + i) for i in range(4)]
        def raise_defense():
            h.wr("hBattleTurn", int(own_boost))
            h.wr("wAttackMissed", 0)
            h.wr("wEffectFailed", 0)
            return h.invoke("BattleCommand_" + command)
        h.wr("wJohtoBadges", 0)
        h.wr("wKantoBadges", 0)
        if ref["first"]:
            returned &= raise_defense()
        returned &= h.invoke("AIGetEnemyMove_HL", {"A":MOVES[attack]})
        if own_boost:
            for i in range(7):
                h.wr("wPlayerMoveStruct", h.rd("wEnemyMoveStruct", i), i)
        h.wr("hBattleTurn", int(not own_boost))
        h.wr("wCriticalHit", 0)
        for damage_command in ("DamageStats", "DamageCalc", "Stab"):
            returned &= h.invoke("BattleCommand_" + damage_command)
        raw = h.rd_be16("wCurDamage")
        minimum = bool(spec.get("branch", 0) & 32) if own_boost else not bool(spec.get("branch", 0) & 16)
        damage = max(1, raw * 217 // 255) if raw and minimum else raw
        hp = [spec["own_hp"], spec["player_hp"]]
        hp[0 if own_boost else 1] = max(0, hp[0 if own_boost else 1] - damage)
        if not ref["first"] and hp[0 if own_boost else 1]:
            returned &= raise_defense()
        prefix = "wEnemy" if own_boost else "wPlayer"
        stat = ("wEnemyMon" if own_boost else "wBattleMon") + ("SpclDef" if axis == 4 else "Defense")
        effective = h.rd_be16(stat)
        expected_record = [axis, h.rd(prefix + "StatLevels", axis), effective >> 8, effective & 255]
        if not hp[0 if own_boost else 1] and not ref["first"]:
            expected_record = [0] * 4
        if successor != hp or projected != expected_record:
            errors.append(f"defensive successor {successor}/{projected} != combat {hp}/{expected_record}")
        for (name, i), value in before.items():
            h.wr(name, value, i)
    if spec.get("reference_items"):
        # Execute combat's after-hit item dispatcher and subsequent move HP
        # command. Only presentation is bypassed; item gates, division, sided
        # HP arithmetic and the zero-HP drain behavior execute in the ROM.
        incoming = spec.get("kind", 0) == 1
        move = spec["reply"] if incoming else spec["move"]
        raw = h.rd("wTilemap", 73) << 8 | h.rd("wTilemap", 74)
        damage = h.rd("wTilemap", 75) << 8 | h.rd("wTilemap", 76)
        h.wr_be16("wEnemyMonHP", max(0, spec["own_hp"] - damage) if incoming else spec["own_hp"])
        h.wr_be16("wBattleMonHP", spec["player_hp"] if incoming else max(0, spec["player_hp"] - damage))
        returned &= h.invoke("AIGetEnemyMove_HL", {"A": MOVES[move]})
        if incoming:
            for i in range(7):
                h.wr("wPlayerMoveStruct", h.rd("wEnemyMoveStruct", i), i)
        h.wr("wCurPlayerMove" if incoming else "wCurEnemyMove", MOVES[move])
        h.wr("hBattleTurn", 0 if incoming else 1)
        h.wr_be16("wCurDamage", raw)
        def return_before_presentation(_):
            sp = int(rf.SP)
            rf.PC = h.pb.memory[sp] | h.pb.memory[sp + 1] << 8
            rf.SP = sp + 2
        stops = ["StdBattleTextbox", "UpdateHPBarBattleHuds", "GetItemName",
                 "SapHealth.finish", "BattleCommand_Recoil.dont_ko"]
        for name in stops:
            symbol = h.syms[name]
            h.pb.hook_register(symbol.bank, symbol.address, return_before_presentation, None)
        try:
            returned &= h.invoke("HandleLateGenAfterHitEffects_Far")
            returned &= h.invoke("SapHealth" if spec["reference_items"] == "drain" else "BattleCommand_Recoil")
        finally:
            for name in stops:
                symbol = h.syms[name]
                h.pb.hook_deregister(symbol.bank, symbol.address)
        combat_hp = [h.rd_be16("wEnemyMonHP"), h.rd_be16("wBattleMonHP")]
        if successor != combat_hp:
            errors.append(f"item/move HP sequence {successor} != combat {combat_hp} (raw {raw})")
        def material(hp, maximum):
            return (256 if hp else 0) + hp * 128 // maximum
        combat_value = (1024 + material(combat_hp[0], spec["own_max"])
                        - material(spec["own_hp"], spec["own_max"])
                        - material(combat_hp[1], spec["player_max"])
                        + material(spec["player_hp"], spec["player_max"]))
        if out["bc"] != combat_value:
            errors.append(f"item/move value {out['bc']} != combat successor value {combat_value}")
    if spec.get("hidden_invariance"):
        for field in ("Attack", "Defense", "Speed", "SpclAtk", "SpclDef"):
            h.wr_be16("wBattleMon" + field, 999)
        h.wr("wBattleMonItem", 255)
        h.wr("wBattleMonDVs", 255)
        h.wr("wBattleMonDVs", 255, 1)
        h.wr("wCurPlayerMove", MOVES["EXPLOSION"])
        for i in range(4):
            h.wr("wBattleMonMoves", MOVES["EXPLOSION"], i)
        returned &= h.invoke("BossAI_ValuePublicExchange", registers)
        repeated = h.outcome()
        second_hp = [(h.rd("wTilemap", n) << 8) | h.rd("wTilemap", n + 1) for n in (57, 63)]
        if (repeated["bc"], repeated["carry"], second_hp, h.rd("wTilemap", 72)) != (
                out["bc"], out["carry"], successor, uncertain):
            errors.append("exchange changed under hidden player stats/item/moves/input")
    out.update(returned=returned, damage_errors=errors, memory={}, haki_spent=False,
               successor=successor, uncertainty=uncertain)
    return out


def run_action_check(h, case):
    spec = case.action_check
    move = MOVES[spec.get("move", "RECOVER")]
    pointer = h.syms["wTilemap"].address
    regs = {"D": pointer >> 8, "E": pointer & 255}
    returned = h.invoke("BossAI_BuildPublicDamageContext", {**regs, "B": 1, "C": move})
    # Override projected HP: future states must not silently reread live HP.
    hp, maximum = spec["hp"], spec["max_hp"]
    for offset, value in ((47, hp), (49, maximum)):
        h.wr("wTilemap", value >> 8, offset)
        h.wr("wTilemap", value & 255, offset + 1)
    spans = (("wEnemyMon", 48), ("wBattleMon", 48), ("wOTPartyMon1Species", 288))
    before = {(name, i): h.rd(name, i) for name, size in spans for i in range(size)}
    context = [h.rd("wTilemap", i) for i in range(51)]
    start_sp = int(h.pb.register_file.SP)
    entry = ("BossAI_Context" + spec["self_effect"] if "self_effect" in spec else
             "BossAI_ContextEntryDamage" if "layers" in spec else "BossAI_ContextRecovery")
    raw = spec.get("raw", 0)
    returned &= h.invoke(entry, {**regs, "B": raw >> 8 if "self_effect" in spec else spec.get("layers", 0),
                               "C": raw & 255})
    out = h.outcome()
    observed, supported = out["bc"], out["carry"]
    errors = []
    rf = h.pb.register_file
    if int(rf.SP) != start_sp or (int(rf.D) << 8 | int(rf.E)) != pointer:
        errors.append("action fact did not preserve stack/context pointer")
    if context != [h.rd("wTilemap", i) for i in range(51)]:
        errors.append("action fact mutated projected context")
    if any(h.rd(*key) != value for key, value in before.items()):
        errors.append("action fact mutated live battle/party state")

    # Reference fractional rounding is executed by combat, not duplicated here.
    h.wr_be16("wEnemyMonMaxHP", maximum)
    h.wr("hBattleTurn", 1)
    if "self_effect" in spec:
        h.wr_be16("wEnemyMonHP", hp)
        h.wr_be16("wCurDamage", raw)
        command, stop = (("BattleCommand_Recoil", "BattleCommand_Recoil.dont_ko")
                         if spec["self_effect"] == "Recoil" else ("SapHealth", "SapHealth.finish"))
        # Stop only after real HP arithmetic, before UI animation/party writes.
        symbol = h.syms[stop]
        def stop_before_ui(_):
            rf = h.pb.register_file
            sp = int(rf.SP)
            rf.PC = h.pb.memory[sp] | h.pb.memory[sp + 1] << 8
            rf.SP = sp + 2
        h.pb.hook_register(symbol.bank, symbol.address, stop_before_ui, None)
        try:
            returned &= h.invoke(command)
        finally:
            h.pb.hook_deregister(symbol.bank, symbol.address)
        after = h.rd_be16("wEnemyMonHP")
        expected = hp - after if spec["self_effect"] == "Recoil" else after - hp
        if observed != expected:
            errors.append(f"self-effect HP amount {observed} != combat command {expected}")
        out.update(returned=returned, damage_errors=errors, memory={}, haki_spent=False,
                   combat_hp_amount=expected, public_hp_amount=observed)
        return out
    returned &= h.invoke(spec["fraction"])
    fraction = h.outcome()["bc"]
    if "layers" in spec:
        immune = TYPES["FLYING"] in (case.boss.type1, case.boss.type2)
        expected = 0 if immune or not spec["layers"] else min(hp, fraction)
    else:
        expected = min(max(0, maximum - hp), fraction) if hp else 0
        if not supported:
            errors.append("recognized recovery rejected")
    if observed != expected:
        errors.append(f"action HP amount {observed} != combat fraction/cap {expected}")
    out.update(returned=returned, damage_errors=errors, memory={}, haki_spent=False,
               combat_hp_amount=expected, public_hp_amount=observed)
    return out
