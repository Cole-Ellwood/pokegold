"""Combat differential driver within the shared declarative ROM fixture suite.

The reference is the ROM's actual combat pipeline, not a copied damage formula.
Kernel-only cases supply normalized context facts; public-adapter cases will
exercise construction of those facts independently from the live battle inputs.
"""
from __future__ import annotations

from tools.boss_ai_fixtures.harness import ROOT, MOVES, TYPES, Mon, SPECIES, _parse_const_file

EFFECTS = _parse_const_file(ROOT / "constants/move_effect_constants.asm")
FIXED = {EFFECTS[n] for n in (
    "EFFECT_STATIC_DAMAGE", "EFFECT_LEVEL_DAMAGE", "EFFECT_SUPER_FANG")}


def run_damage_check(h, case):
    spec = case.damage_check
    direction = spec.get("direction", 1)
    attacker = case.boss if direction else case.player
    defender = case.player if direction else case.boss
    user = "wEnemyMon" if direction else "wBattleMon"
    target = "wBattleMon" if direction else "wEnemyMon"
    target_side = "Player" if direction else "Enemy"
    move = MOVES[spec["move"]]
    errors = []
    returned = True

    # Establish known battle inputs. Extras can then supply public stage/screen
    # states and known own items; no implicit title-screen state is a mechanic.
    for name in ("wEnemyMonItem", "wBattleMonItem", "wCriticalHit", "wAttackMissed",
                 "wTypeModifier", "wBattleWeather", "wJohtoBadges", "wKantoBadges",
                 "wPlayerScreens", "wEnemyScreens"):
        h.wr(name, 0)
    h.wr("hBattleTurn", direction)
    h.wr("wTempEnemyMonSpecies", case.boss.species)
    for prefix, mon in (("wEnemy", case.boss), ("wPlayer", case.player)):
        for suffix, value in (("Attack", mon.atk), ("Defense", mon.deff),
                              ("Speed", mon.spe), ("SpAtk", mon.spa), ("SpDef", mon.spd)):
            h.wr_be16(prefix + suffix, value)
    for key, value in case.extra.items():
        h.wr(key[0], value, key[1]) if isinstance(key, tuple) else h.wr(key, value)
    if spec.get("adapter"):
        # Build actual battle stats through combat's own stage/status routines.
        # Status recalculation uses the inverse hBattleTurn convention internally.
        for enemy in (0, 1):
            h.wr("wApplyStatLevelMultipliersToEnemy", enemy)
            returned &= h.invoke("ApplyStatLevelMultiplierOnAllStats")
            returned &= h.invoke("ApplyStatusEffectOnEnemyStats" if enemy else "ApplyStatusEffectOnPlayerStats")
        h.wr("hBattleTurn", direction)
    returned &= h.invoke("AIGetEnemyMove_HL", {"A": move})
    if not direction:
        for i in range(7):
            h.wr("wPlayerMoveStruct", h.rd("wEnemyMoveStruct", i), i)
    struct = "wEnemyMoveStruct" if direction else "wPlayerMoveStruct"
    effect, power, move_type = (h.rd(struct, i) for i in (1, 2, 3))
    returned &= h.invoke("Battle_GetEffectiveMoveCategory")
    category = h.outcome()["a"]
    special = category >= 20
    attack = h.rd_be16(user + ("SpclAtk" if special else "Attack"))
    defense = h.rd_be16(target + ("SpclDef" if special else "Defense"))
    screens = h.rd("w" + target_side + "Screens")
    if screens & (8 if special else 16):
        defense *= 2

    flags = 0
    if h.rd("w" + target_side + "SubStatus1") & 8:
        flags |= 1
    if 3 * h.rd_be16(user + "HP") < h.rd_be16(user + "MaxHP"):
        flags |= 2
    if 2 * h.rd_be16(target + "HP") > h.rd_be16(target + "MaxHP"):
        flags |= 4
    if h.rd(target + "Status"):
        flags |= 8
    if move == MOVES["STRUGGLE"]:
        flags |= 64
    context = bytearray(51)
    context[:5] = bytes((attacker.level, power, effect, move_type, category))
    context[5:7] = attack.to_bytes(2, "big")
    context[7:9] = defense.to_bytes(2, "big")
    context[9:13] = bytes((attacker.type1, attacker.type2, defender.type1, defender.type2))
    context[13:15] = h.rd_be16(target + "HP").to_bytes(2, "big")
    context[15:22] = bytes((flags, h.rd("wBattleWeather"), 0, 1, 1, 1, 255))
    context[25:27] = h.rd_be16(target + "MaxHP").to_bytes(2, "big")
    for offset, value in spec.get("context", {}).items():
        context[offset] = value

    # Real combat supplies the per-hit noncritical maximum. Stab already calls
    # TypePassive_ApplyDamageModifiers_Far, so calling it again would be wrong.
    pipeline = ("BattleCommand_ConstantDamage", "BattleCommand_ResetTypeMatchup") if effect in FIXED else (
        "BattleCommand_DamageStats", "BattleCommand_DamageCalc", "BattleCommand_Stab")
    post_commands = {
        EFFECTS["EFFECT_EARTHQUAKE"]: "BattleCommand_DoubleUndergroundDamage",
        EFFECTS["EFFECT_GUST"]: "BattleCommand_DoubleFlyingDamage",
        EFFECTS["EFFECT_TWISTER"]: "BattleCommand_DoubleFlyingDamage",
        EFFECTS["EFFECT_STOMP"]: "BattleCommand_DoubleMinimizeDamage",
        EFFECTS["EFFECT_FALSE_SWIPE"]: "BattleCommand_FalseSwipe",
    }
    original_hp = h.rd_be16(target + "HP")
    expected = []
    expected_raw = []
    for roll, hits in ((217, spec.get("min_hits", 1)), (255, spec.get("max_hits", 1))):
        h.wr_be16(target + "HP", original_hp)
        total = 0
        for _ in range(hits):
            for entry in pipeline:
                returned &= h.invoke(entry)
            maximum = h.rd_be16("wCurDamage")
            # Only the deterministic roll endpoint is scalar math here. Every
            # damage mechanic and post-variation modifier runs on the ROM.
            amount = maximum if effect in FIXED else max(1, maximum * roll // 255) if maximum else 0
            h.wr_be16("wCurDamage", amount)
            if effect in post_commands:
                returned &= h.invoke(post_commands[effect])
            if effect == EFFECTS["EFFECT_PURSUIT"]:
                switching = "w" + target_side + "IsSwitching"
                h.wr(switching, int(roll == 255))
                returned &= h.invoke("BattleCommand_Pursuit")
                h.wr(switching, 0)
            amount = h.rd_be16("wCurDamage")
            total += amount
            remaining = max(0, h.rd_be16(target + "HP") - amount)
            h.wr_be16(target + "HP", remaining)
            if not remaining:
                break
        expected.append(min(total, original_hp))
        expected_raw.append(total)
    h.wr_be16(target + "HP", original_hp)

    expected_hit_facts = None
    if spec.get("hit_facts"):
        saved_hit = {(name, i): h.rd(name, i) for name, size in (
            ("wEnemyMoveStruct", 14), ("wCurDamage", 2), ("wAttackMissed", 1),
            ("wPlayerSubStatus5", 1), ("wEnemySubStatus5", 1)) for i in range(size)}
        h.wr("wAttackMissed", 0)
        if effect == EFFECTS["EFFECT_THUNDER"]:
            returned &= h.invoke("BattleCommand_ThunderAccuracy")
        accuracy_rolls = []
        battle_random = h.syms["BattleRandom"]
        h.pb.hook_register(battle_random.bank, battle_random.address,
                           lambda _: accuracy_rolls.append(int(h.pb.register_file.B)), None)
        try:
            returned &= h.invoke("BattleCommand_CheckHit")
        finally:
            h.pb.hook_deregister(battle_random.bank, battle_random.address)
        chance = accuracy_rolls[-1] if accuracy_rolls else 0 if h.rd("wAttackMissed") else 255
        returned &= h.invoke("GetMovePriority", {"A": move})
        expected_hit_facts = [chance, h.outcome()["a"]]
        for key, value in saved_hit.items():
            h.wr(key[0], value, key[1])

    for key, value in spec.get("hidden_noise", {}).items():
        h.wr(key[0], value, key[1]) if isinstance(key, tuple) else h.wr(key, value)

    expected_speeds = None
    if spec.get("speed_facts"):
        returned &= h.invoke("DetermineMoveOrder.GetEnemySpeedForTurnOrder")
        own_speed = h.outcome()["bc"]
        returned &= h.invoke("DetermineMoveOrder.GetPlayerSpeedForTurnOrder")
        expected_speeds = [own_speed, h.outcome()["bc"]]
    own_slot = spec.get("own_slot")
    if own_slot is not None:
        # Combat above ran with the candidate as the active battler. Now place
        # its raw computed facts in an OWN party slot and poison active context;
        # the party adapter must reconstruct the same ordinary entry state.
        from tools.boss_ai_fixtures.cases import ITEMS
        offset = own_slot * 48
        h.wr("wOTPartyCount", 6)
        h.wr("wOTPartySpecies", case.boss.species, own_slot)
        for field, value in (("Species", case.boss.species), ("Level", case.boss.level),
                             ("Status", case.boss.status), ("Item", h.rd("wEnemyMonItem"))):
            h.wr("wOTPartyMon1" + field, value, offset)
        for field, value in (("HP", case.boss.hp), ("MaxHP", case.boss.max_hp),
                             ("Attack", case.boss.atk), ("Defense", case.boss.deff),
                             ("Speed", case.boss.spe), ("SpclAtk", case.boss.spa),
                             ("SpclDef", case.boss.spd)):
            h.wr("wOTPartyMon1" + field, value >> 8, offset)
            h.wr("wOTPartyMon1" + field, value & 255, offset + 1)
        for i in range(4):
            h.wr("wOTPartyMon1Moves", case.boss.moves[i] if i < len(case.boss.moves) else 0, offset + i)
            h.wr("wOTPartyMon1PP", 30 if i < len(case.boss.moves) else 0, offset + i)
        h.seed_mon("wEnemyMon", Mon.of("SHUCKLE", 5, ["TACKLE"], status=16))
        h.wr("wEnemyMonItem", ITEMS["LIFE_ORB"])
        h.wr("wTempEnemyMonSpecies", SPECIES["PIKACHU"])
        for field in ("Attack", "Defense", "Speed", "SpAtk", "SpDef"):
            h.wr_be16("wEnemy" + field, 999)
        for field in ("Atk", "Def", "Spd", "SAtk", "SDef", "Acc", "Eva"):
            h.wr("wEnemy" + field + "Level", 13)
        for i in range(1, 6):
            h.wr("wEnemySubStatus" + str(i), 255)
        h.wr("wEnemyMinimized", 1)
        h.wr("wEnemyMetronomeCount", 5)

    # Caller-owned WRAM0 scratch stands in for the adapter's future stack context.
    # Snapshot live battle/AI fields so accidental writes fail independently of
    # whether their values happened to affect this particular damage result.
    spans = (("wEnemyMon", 48), ("wBattleMon", 48), ("wEnemyMoveStruct", 14),
             ("wBossAITemp", 5), ("wPlayerStats", 10), ("wEnemyStats", 10))
    if own_slot is not None:
        spans += (("wOTPartyMon1Species", 48 * 6), ("wOTPartyCount", 8))
    before = {(name, i): h.rd(name, i) for name, size in spans for i in range(size)}
    pointer = h.syms["wTilemap"].address
    observed = []
    observed_hit_facts = None
    random_calls = []
    random_symbol = h.syms["Random"]
    h.pb.hook_register(random_symbol.bank, random_symbol.address, lambda _: random_calls.append(1), None)
    try:
        if spec.get("adapter"):
            start_sp = int(h.pb.register_file.SP)
            estimate = "BossAI_EstimatePublicDamage" if own_slot is None else "BossAI_EstimatePartyDamage"
            returned &= h.invoke(estimate, {"B": direction, "C": move, "D": 255 if own_slot is None else own_slot, "HL": 0x9abc})
            rf = h.pb.register_file
            observed = [h.outcome()["bc"], (int(rf.D) << 8) | int(rf.E)]
            supported = h.outcome()["carry"]
            if supported != spec.get("supported", True):
                errors.append(f"public damage support={supported}, expected {spec.get('supported', True)}")
            if int(rf.HL) != 0x9abc or int(rf.SP) != start_sp:
                errors.append("public adapter caller HL or stack not preserved")
            # Compare the optimized range with two complete kernel executions
            # over the same normalized public facts, including all output scratch.
            build = "BossAI_BuildPublicDamageContext" if own_slot is None else "BossAI_BuildOwnedDamageContext"
            returned &= h.invoke(build, {"A": 255 if own_slot is None else own_slot,
                "B": direction, "C": move, "D": pointer >> 8, "E": pointer & 255})
            range_input = bytes(h.rd("wTilemap", i) for i in range(51))
            twins = []
            for entry in ("BossAI_PublicDamageRange", "BossAI_PublicDamageRange.multiple_hits"):
                for i, value in enumerate(range_input):
                    h.wr("wTilemap", value, i)
                returned &= h.invoke(entry, {"D": pointer >> 8, "E": pointer & 255})
                twins.append((h.outcome()["bc"], int(rf.D) << 8 | int(rf.E), h.outcome()["carry"],
                              bytes(h.rd("wTilemap", i) for i in range(51))))
                if int(rf.SP) != start_sp:
                    errors.append("damage range comparison lost caller stack")
            if twins[0][:3] != twins[1][:3] or (twins[0][2] and twins[0][3] != twins[1][3]):
                errors.append(f"optimized/general range differ: {twins}")
            if direction == 0:
                # The narrow accuracy builder must match complete public facts
                # even when unrelated AD scratch contains adversarial old data.
                for i in range(51):
                    h.wr("wTilemap", 0xa5, i)
                returned &= h.invoke("BossAI_IncomingAccuracy", {"A":255 if own_slot is None else own_slot,
                    "C":move, "D":pointer >> 8, "E":pointer & 255})
                if int(rf.C) != range_input[31]:
                    errors.append(f"narrow incoming accuracy {int(rf.C)} != complete context {range_input[31]}")
                if int(rf.SP) != start_sp or (int(rf.D) << 8 | int(rf.E)) != pointer:
                    errors.append("narrow accuracy builder lost caller stack/context")
            if spec.get("raw_facts"):
                build = "BossAI_BuildPublicDamageContext" if own_slot is None else "BossAI_BuildOwnedDamageContext"
                returned &= h.invoke(build, {"A": 255 if own_slot is None else own_slot,
                    "B": direction, "C": move, "D": pointer >> 8, "E": pointer & 255})
                returned &= h.invoke("BossAI_PublicDamageRange", {"D": pointer >> 8, "E": pointer & 255})
                raw = [(h.rd("wTilemap", i) << 8) | h.rd("wTilemap", i+1) for i in (43, 45)]
                if raw != expected_raw:
                    errors.append(f"raw side-effect damage {raw} != combat {expected_raw}")
            if spec.get("speed_facts"):
                build = "BossAI_BuildPublicDamageContext" if own_slot is None else "BossAI_BuildOwnedDamageContext"
                returned &= h.invoke(build, {"A": 255 if own_slot is None else own_slot,
                    "B": 1, "C": move, "D": pointer >> 8, "E": pointer & 255})
                returned &= h.invoke("BossAI_ContextSpeeds", {"D": pointer >> 8, "E": pointer & 255})
                speeds = [h.outcome()["bc"], int(rf.HL)]
                speed_known = spec.get("speed_known", True)
                if h.outcome()["carry"] != speed_known:
                    errors.append(f"speed certainty != {speed_known}")
                if speed_known and speeds != expected_speeds:
                    errors.append(f"public action speeds {speeds} != combat {expected_speeds}")
                if (int(rf.D) << 8 | int(rf.E)) != pointer:
                    errors.append("speed facts lost context pointer")
            if spec.get("repeat_context"):
                build = "BossAI_BuildPublicDamageContext" if own_slot is None else "BossAI_BuildOwnedDamageContext"
                returned &= h.invoke(build, {"A": 255 if own_slot is None else own_slot,
                    "B": direction, "C": move, "D": pointer >> 8, "E": pointer & 255})
                original_postroll = h.rd("wTilemap", 33)
                for _ in range(2):
                    returned &= h.invoke("BossAI_PublicDamageRange", {"D": pointer >> 8, "E": pointer & 255})
                    repeated = [h.outcome()["bc"], (int(rf.D) << 8) | int(rf.E)]
                    if repeated != observed or h.rd("wTilemap", 33) != original_postroll:
                        errors.append(f"reused context drifted: {repeated} vs {observed}")
            if spec.get("hit_facts") or spec.get("survival_facts"):
                build = "BossAI_BuildPublicDamageContext" if own_slot is None else "BossAI_BuildOwnedDamageContext"
                returned &= h.invoke(build, {"A": 255 if own_slot is None else own_slot,
                    "B": direction, "C": move, "D": pointer >> 8, "E": pointer & 255})
                observed_hit_facts = [h.rd("wTilemap", i) for i in (31, 32)]
                if spec.get("hit_facts") and observed_hit_facts != expected_hit_facts:
                    errors.append(f"public hit facts {observed_hit_facts} != combat {expected_hit_facts}")
                if spec.get("survival_facts"):
                    survival = [h.rd("wTilemap", i) for i in (40, 41)]
                    if survival != spec["survival_facts"]:
                        errors.append(f"public survival thresholds {survival} != {spec['survival_facts']}")
        for roll, hits in (() if spec.get("adapter") else ((217, spec.get("min_hits", 1)), (255, spec.get("max_hits", 1)))):
            context[20:22] = bytes((hits, roll))
            for i, value in enumerate(context):
                h.wr("wTilemap", value, i)
            start_sp = int(h.pb.register_file.SP)
            returned &= h.invoke("BossAI_DamageKernel", {"D": pointer >> 8, "E": pointer & 255})
            out = h.outcome()
            observed.append(out["bc"])
            if not out["carry"]:
                errors.append("supported arithmetic context rejected")
            rf = h.pb.register_file
            if ((int(rf.D) << 8) | int(rf.E)) != pointer or int(rf.SP) != start_sp:
                errors.append("context pointer or stack not preserved")
    finally:
        h.pb.hook_deregister(random_symbol.bank, random_symbol.address)
    if spec.get("supported", True) and observed != expected:
        errors.append(f"kernel {observed} != combat {list(expected)}")
    if spec.get("supported", True) and not (0 <= observed[0] <= observed[1] <= original_hp):
        errors.append(f"HP-loss envelope is invalid: {observed}, target HP {original_hp}")
    changed = [(key, old, h.rd(*key)) for key, old in before.items() if h.rd(*key) != old]
    if changed:
        errors.append(f"kernel changed caller battle state: {changed}")
    if random_calls:
        errors.append(f"kernel consumed RNG {len(random_calls)} times")
    out = h.outcome()
    out.update(returned=returned, damage_errors=errors, combat_damage=list(expected),
               kernel_damage=observed, memory={}, random_calls=len(random_calls),
               combat_hit_facts=expected_hit_facts, public_hit_facts=observed_hit_facts,
               haki_spent=bool(h.rd("wBossAIRevealedMovesBitmapSpare", 1) & 1))
    return out
