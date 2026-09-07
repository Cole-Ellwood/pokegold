"""Conditional action matrix vs exhaustive independent exchange aggregation.

The single-exchange ROM model has separate combat-reference tests. This driver
checks the selector's enumeration, weighting, rounding, ties and state contract;
it does not claim that the conditional model is a complete battle simulator.
"""
from tools.boss_ai_fixtures.harness import MOVES, ROOT, SPECIES, _parse_const_file
from time import perf_counter

from tools.boss_ai_fixtures.layout import AV_PREPARED_SIZE, JC_SCORES, JC_BEST_INDEX, JC_SIZE
ITEMS = _parse_const_file(ROOT / "constants/item_constants.asm")


def seed_joint_case(h, case):
    spec = case.joint_check
    for name in ("wEnemyMonItem", "wBattleMonItem", "wEnemyChoiceLockedMove",
                 "wEnemyDisabledMove", "wEnemyDisableCount", "wEnemyWrapCount", "wLinkMode",
                 "wEnemyIsSwitching", "wCurEnemyMoveNum", "wCurOTMon",
                 "wBattleWeather", "wEnemyScreens", "wPlayerScreens",
                 "wBossAIWinconMonIdx", "wBossAISeenPlayerSpeciesCount"):
        h.wr(name, 0)
    for name, size in (("wEnemySubStatus1", 5), ("wPlayerSubStatus1", 5),
                       ("wBossAIRevealedMovesBitmapSpare", 3)):
        for i in range(size):
            h.wr(name, 0, i)
    h.wr("wBattleMode", 2)
    h.wr("wCurEnemyMove", case.boss.moves[0] if case.boss.moves else 0)
    for prefix, mon in (("wEnemy", case.boss), ("wPlayer", case.player)):
        for field, value in (("Attack", mon.atk), ("Defense", mon.deff),
                             ("Speed", mon.spe), ("SpAtk", mon.spa), ("SpDef", mon.spd)):
            h.wr_be16(prefix + field, value)
    party = [case.boss] + spec.get("bench", [])
    h.wr("wOTPartyCount", len(party))
    for i, mon in enumerate(party):
        offset = i * 48
        for field, value in (("Species", mon.species), ("Level", mon.level),
                             ("Status", mon.status), ("Item", 0)):
            h.wr("wOTPartyMon1" + field, value, offset)
        for field, value in (("HP", mon.hp), ("MaxHP", mon.max_hp),
                             ("Attack", mon.atk), ("Defense", mon.deff),
                             ("Speed", mon.spe), ("SpclAtk", mon.spa), ("SpclDef", mon.spd)):
            h.wr("wOTPartyMon1" + field, value >> 8, offset)
            h.wr("wOTPartyMon1" + field, value & 255, offset + 1)
        for j in range(4):
            h.wr("wOTPartyMon1Moves", mon.moves[j] if j < len(mon.moves) else 0, offset + j)
            h.wr("wOTPartyMon1PP", mon.pp if j < len(mon.moves) else 0, offset + j)
    revealed = spec.get("revealed", ["TACKLE", "GROWL", "SAND_ATTACK", "QUICK_ATTACK"])
    for i in range(4):
        h.wr("wPlayerUsedMoves", MOVES[revealed[i]] if i < len(revealed) else 0, i)
    for key, value in case.extra.items():
        h.wr(key[0], value, key[1]) if isinstance(key, tuple) else h.wr(key, value)


def run_joint_check(h, case):
    seed_joint_case(h, case)
    spec = case.joint_check
    base = h.syms["wBattleAnimTileDict"].address
    scratch = h.syms["wAttrmap"].address
    rf = h.pb.register_file
    errors, returned = [], True
    matrix_runs = []
    initial_sp = int(rf.SP)
    spans = (("wEnemyMon", 48), ("wBattleMon", 48), ("wOTPartyMon1Species", 288),
             ("wEnemySubStatus1", 5), ("wPlayerSubStatus1", 5),
             ("wEnemyAIMoveScores", 4), ("wBossAITemp", 5),
             ("wCurEnemyMove", 1), ("wCurEnemyMoveNum", 1),
             ("wEnemyChoiceLockedMove", 1), ("wCurSpecies", 1), ("wCurPartySpecies", 1))
    before = {(name, i): h.rd(name, i) for name, size in spans for i in range(size)}
    def invoke(name, registers, pointer=scratch):
        nonlocal returned
        start_frame, start_time = h.pb.frame_count, perf_counter()
        ok = h.invoke(name, dict(registers, D=pointer >> 8, E=pointer & 255),
                      frame_budget=30000 if name == "BossAI_ComparePublicActions" else 3000)
        if name == "BossAI_ComparePublicActions":
            matrix_runs.append({"scan": registers["B"], "host_seconds": perf_counter() - start_time,
                                "emulated_frame_upper_bound": h.pb.frame_count - start_frame})
        returned &= ok
        if not ok:
            raise RuntimeError(f"{name} failed to return")
        if int(rf.SP) != initial_sp or (int(rf.D) << 8 | int(rf.E)) != pointer:
            errors.append(f"{name} lost stack/context")
        return h.outcome()
    kind = spec.get("kind", 0)
    invoke("BossAI_EnumeratePublicActions", {"A": kind})
    candidates = [h.rd("wAttrmap", i) for i in range(8)]
    invoke("BossAI_BuildPublicReplySet", {})
    reply_bits = [h.rd("wAttrmap", i) for i in range(65)]
    replies = [m for m in range(1, 256) if reply_bits[m // 8] & 1 << (m % 8)]
    actions = {i: (255, 0, move) for i, move in enumerate(candidates[:4]) if move}
    actions.update({i + 4: (i, 2 if kind == 2 else 1, MOVES["STRUGGLE"])
                    for i in range(6) if candidates[4] & 1 << i})
    if candidates[5] == 1:
        forced = candidates[6]
        wait = forced in (0, 255) or h.rd("wEnemySubStatus4") & 32 or spec.get("forced_wait")
        actions[10] = (255, 3 if wait else 0, MOVES["STRUGGLE"] if wait else forced)
    elif candidates[5] == 2:
        actions[11] = (255, 3, MOVES["STRUGGLE"])
    expected = [(65535, 255)] * 12
    expected_records = [(0, 0, 65535, 255)] * 12
    tied_pairs = []
    event_rows = []
    rounded_early = {}
    for index, (slot, action_kind, move) in actions.items():
        if spec.get("check_ties") or spec.get("check_accuracy"):
            for offset, value in ((51, action_kind), (52, slot), (53, move), (80, 0)):
                h.wr("wBattleAnimTileDict", value, offset)
            invoke("BossAI_PreparePublicAction", {}, base)
        invoke("BossAI_BuildOwnedDamageContext", {"A": slot, "B": 1, "C": move})
        own_accuracy = h.rd("wAttrmap", 31) if action_kind == 0 else 255
        own_chance = 256 if own_accuracy == 255 else own_accuracy
        total = mass = early_total = 0
        uncertainty = 32 if action_kind != 2 and not reply_bits[64] & 1 else 0
        for reply in ([0] if action_kind == 2 else replies):
            reply_accuracy = 255
            if reply:
                invoke("BossAI_BuildOwnedDamageContext", {"A": slot, "B": 0, "C": reply})
                reply_accuracy = h.rd("wAttrmap", 31)
            reply_chance = 256 if reply_accuracy == 255 else reply_accuracy
            out = invoke("BossAI_ValuePublicExchange",
                         {"A": slot, "B": action_kind, "C": move, "HL": reply << 8})
            weight = 8 if reply and reply_bits[32 + reply // 8] & 1 << (reply % 8) else 1
            own_speed = h.rd("wAttrmap", 67) << 8 | h.rd("wAttrmap", 68)
            player_speed = h.rd("wAttrmap", 69) << 8 | h.rd("wAttrmap", 70)
            own_priority = h.rd("wAttrmap", 71)
            item = h.rd("wEnemyMonItem") if slot == 255 else h.rd("wOTPartyMon1Item", slot * 48)
            copied = bool(h.rd("wPlayerSubStatus5") & 8) or (
                slot != 255 and h.rd("wOTPartyMon1Species", slot * 48) == SPECIES["DITTO"])
            returned &= h.invoke("GetMovePriority", {"A": reply or MOVES["STRUGGLE"]})
            tied = (action_kind == 0 and reply != 0 and not copied and item != ITEMS["QUICK_CLAW"]
                    and own_speed == player_speed and own_priority == h.outcome()["a"])
            if spec.get("check_ties") or spec.get("check_accuracy"):
                h.wr("wBattleAnimTileDict", reply, 54)
                retained = bytes(h.rd("wBattleAnimTileDict", i) for i in range(51, AV_PREPARED_SIZE))
                captured = invoke("BossAI_PreparedExchangeAccuracy", {}, base)["bc"]
                if captured != own_accuracy << 8 | reply_accuracy or retained != bytes(h.rd("wBattleAnimTileDict", i) for i in range(51, AV_PREPARED_SIZE)):
                    errors.append(f"accuracy capture mismatch/mutation at {index}/{reply}")
                template = bytes(h.rd("wBattleAnimTileDict", i) for i in range(AV_PREPARED_SIZE))
                classified = invoke("BossAI_PreparedActionHasSpeedTie", {}, base)["carry"]
                if classified != tied or template != bytes(h.rd("wBattleAnimTileDict", i) for i in range(AV_PREPARED_SIZE)):
                    errors.append(f"tie classifier mismatch/mutation at {index}/{reply}")
            first_order_values = []
            reply_total = reply_mass = 0
            for hit_event in range(4):
                own_p = 256 - own_chance if hit_event & 1 else own_chance
                reply_p = 256 - reply_chance if hit_event & 2 else reply_chance
                if not own_p or not reply_p:
                    continue
                branch_values = []
                for order in ((4, 12) if tied else (0,)):
                    branch = hit_event | order
                    if branch:
                        out = invoke("BossAI_ValuePublicExchange",
                                     {"A": slot, "B": action_kind, "C": move, "HL": reply << 8 | branch})
                    # Branch zero reuses the result already obtained for order
                    # classification; it is the first feasible event when present.
                    event_weight = (weight if tied else 2 * weight) * own_p * reply_p
                    reply_total += out["bc"] * event_weight
                    reply_mass += event_weight
                    branch_values.append(out["bc"])
                    uncertainty |= h.rd("wAttrmap", 72)
                    if spec.get("check_accuracy"):
                        event_rows.append({"action":index, "reply":reply, "branch":branch,
                            "weight":event_weight, "value":out["bc"],
                            "own_hp":h.rd("wAttrmap", 57) << 8 | h.rd("wAttrmap", 58),
                            "reply_hp":h.rd("wAttrmap", 63) << 8 | h.rd("wAttrmap", 64)})
                if not first_order_values:
                    first_order_values = branch_values
            if reply_mass != 2 * weight * 65536:
                errors.append(f"incomplete event mass at {index}/{reply}")
            total += reply_total
            mass += reply_mass
            if tied:
                tied_pairs.append({"action": index, "reply": reply, "values": first_order_values, "weight": weight})
            early_total += (reply_total // reply_mass) * reply_mass
        expected[index] = (total // mass, uncertainty)
        expected_records[index] = (total, mass // 65536, total // mass, uncertainty)
        rounded_early[index] = early_total // mass
    best = min(actions, key=lambda i: (-expected[i][0], i)) if actions else 255
    for i in range(JC_SIZE, 472):
        h.wr("wBattleAnimTileDict", 0xa5, i)
    random_calls = []
    symbol = h.syms["Random"]
    h.pb.hook_register(symbol.bank, symbol.address, lambda _: random_calls.append(1), None)
    try:
        for scan in range(16 if spec.get("check_accuracy") else 8 if spec.get("check_ties") else 4):
            out = invoke("BossAI_ComparePublicActions", {"A": kind, "B": scan}, base)
            vector = [(h.rd("wBattleAnimTileDict", JC_SCORES + i * 3) << 8 | h.rd("wBattleAnimTileDict", JC_SCORES + 1 + i * 3),
                       h.rd("wBattleAnimTileDict", JC_SCORES + 2 + i * 3)) for i in range(12)]
            if vector != expected:
                errors.append(f"scan {scan} scores {vector} != exhaustive {expected}")
            if (h.rd("wBattleAnimTileDict", JC_BEST_INDEX), out["bc"], out["carry"]) != (
                    best, expected[best][0] if actions else 0, bool(actions)):
                errors.append(f"scan {scan} wrong best/carry: {h.rd('wBattleAnimTileDict', JC_BEST_INDEX)}, {out['bc']}")
            if any(h.rd(*key) != value for key, value in before.items()):
                errors.append(f"scan {scan} changed live state")
            if any(h.rd("wBattleAnimTileDict", i) != 0xa5 for i in range(JC_SIZE, 472)):
                errors.append(f"scan {scan} exceeded its {JC_SIZE}-byte context")
        if spec.get("hidden_invariance", True):
            h.wr("wBattleMonItem", 255)
            h.wr("wCurPlayerMove", MOVES["EXPLOSION"])
            for i in range(4):
                h.wr("wBattleMonMoves", MOVES["EXPLOSION"], i)
                h.wr("wBattleMonPP", 0, i)
            invoke("BossAI_ComparePublicActions", {"A": kind, "B": 0}, base)
            hidden_vector = [(h.rd("wBattleAnimTileDict", JC_SCORES + i * 3) << 8 | h.rd("wBattleAnimTileDict", JC_SCORES + 1 + i * 3),
                              h.rd("wBattleAnimTileDict", JC_SCORES + 2 + i * 3)) for i in range(12)]
            if hidden_vector != expected or h.rd("wBattleAnimTileDict", JC_BEST_INDEX) != best:
                errors.append("selection depends on hidden player move/PP/item/input")
        if spec.get("wait_hazard_invariance"):
            h.wr("wEnemyScreens", 0)
            invoke("BossAI_ComparePublicActions", {"A": kind, "B": 0}, base)
            wait_value = h.rd("wBattleAnimTileDict", JC_SCORES + 33) << 8 | h.rd("wBattleAnimTileDict", JC_SCORES + 34)
            if wait_value != expected[11][0]:
                errors.append("forced wait incorrectly takes switch-entry hazards")
    finally:
        h.pb.hook_deregister(symbol.bank, symbol.address)
    if random_calls:
        errors.append("matrix consumed RNG")
    if "best" in spec and best != spec["best"]:
        errors.append(f"behavioral best {best} != {spec['best']}")
    if "tie_count" in spec and len(tied_pairs) != spec["tie_count"]:
        errors.append(f"tied pairs {len(tied_pairs)} != {spec['tie_count']}")
    if spec.get("tie_changes_outcome") and not any(p["values"][0] != p["values"][1] for p in tied_pairs):
        errors.append("tie fixture has no order-dependent exchange")
    if spec.get("early_rounding_difference") and not any(rounded_early[i] != expected[i][0] for i in actions):
        errors.append("fixture does not distinguish premature branch rounding")
    if "own_miss_faints" in spec:
        misses = [r for r in event_rows if r["action"] == spec["own_miss_faints"] and r["branch"] & 1]
        if not misses or any(r["own_hp"] for r in misses):
            errors.append("missed Selfdestruct did not faint its user")
    if "reply_miss_faints" in spec:
        misses = [r for r in event_rows if r["reply"] == MOVES[spec["reply_miss_faints"]] and r["branch"] & 2]
        if not misses or any(r["reply_hp"] for r in misses):
            errors.append("missed replying Selfdestruct did not faint its user")
    if "interrupted_reply" in spec:
        interrupted = [r for r in event_rows if r["action"] == 0 and r["reply"] == MOVES[spec["interrupted_reply"]]]
        if len(interrupted) != 2 or any(r["reply_hp"] for r in interrupted) or len({r["value"] for r in interrupted}) != 1:
            errors.append("latent hit/miss outcomes changed an interrupted reply")
    if "only_hit_event" in spec and (not event_rows or any(r["branch"] & 3 != spec["only_hit_event"] for r in event_rows)):
        errors.append("impossible hit outcome received nonzero event mass")
    required = spec.get("required_uncertainty", 0)
    if best != 255 and expected[best][1] & required != required:
        errors.append(f"selected action omitted uncertainty mask {required}")
    out.update(returned=returned, damage_errors=errors, memory={}, haki_spent=False,
               joint_scores=expected, best_index=best, matrix_runs=matrix_runs,
               joint_records=expected_records,
               tied_pairs=tied_pairs, rounded_early_scores=rounded_early, event_rows=event_rows)
    return out
