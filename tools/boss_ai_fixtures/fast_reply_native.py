"""Native reply compiler versus the producer-based compile, every move."""
from tools.boss_ai_fixtures.harness import Mon, MOVES, open_harness
from tools.boss_ai_fixtures.cases import ITEMS

NUM_ATTACKS = max(v for k, v in MOVES.items() if not k.startswith("ANIM_") and v < 255)


def scenarios():
    yield "plain", Mon.of("SNORLAX", 50, ["TACKLE"]), Mon.of("PIDGEY", 50, ["TACKLE"]), {}
    yield "ghost_helmet", Mon.of("GENGAR", 45, ["LICK"]), Mon.of("MACHAMP", 60, ["KARATE_CHOP"]), {
        "wEnemyMonItem": ITEMS["ROCKY_HELMET"], "wEnemyScreens": 3, "wBattleWeather": 1}
    yield "psychic_sub_rain", Mon.of("ALAKAZAM", 70, ["PSYCHIC_M"]), Mon.of("GYARADOS", 55, ["SURF"]), {
        "wEnemySubStatus4": 1 << 4, "wBattleWeather": 2, "wPlayerAccLevel": 9, "wEnemyEvaLevel": 5}
    yield "identified_lockon_fly", Mon.of("STEELIX", 50, ["IRON_TAIL"]), Mon.of("CHARIZARD", 50, ["FLY"]), {
        "wEnemySubStatus1": 1 << 1, "wEnemySubStatus5": 1 << 5, "wEnemySubStatus3": 1 << 1 | 1 << 7,
        "wPlayerSubStatus4": 1 << 1, "wPlayerSubStatus3": 1 << 7, "wBattleMonStatus": 0x40 | 2}
    yield "ice_low_hp_powder", Mon.of("DEWGONG", 40, ["ICE_BEAM"], hp_pct=20), Mon.of("ARCANINE", 40, ["FIRE_BLAST"], hp_pct=25), {
        "wEnemyMonItem": ITEMS["BRIGHTPOWDER"], "wBattleWeather": 1, "wEnemyMonStatus": 0x40, "wEnemyMinimized": 1}
    yield "transformed_player", Mon.of("SNORLAX", 50, ["TACKLE"]), Mon.of("DITTO", 50, ["TRANSFORM"]), {
        "wPlayerSubStatus5": 1 << 3, "wBattleMonStatus": 1}
    yield "dragon_water_outrage", Mon.of("KINGDRA", 55, ["SURF"]), Mon.of("DRAGONITE", 55, ["OUTRAGE"]), {
        "wPlayerSubStatus3": 1 << 4, "wEnemySubStatus3": 1 << 6, "wEnemyMonStatus": 1 << 3}
    yield "bug_balloon_sun", Mon.of("SCIZOR", 50, ["STEEL_WING"]), Mon.of("VENUSAUR", 50, ["SOLARBEAM"]), {
        "wEnemyMonItem": ITEMS["AIR_BALLOON"], "wBattleWeather": 1, "wPlayerSubStatus3": 1 << 4, "wTimeOfDay": 1}
    yield "focus_band_burn_para", Mon.of("SNORLAX", 50, ["BODY_SLAM"]), Mon.of("SNORLAX", 50, ["TACKLE"]), {
        "wEnemyMonItem": ITEMS["FOCUS_BAND"], "wBattleMonStatus": 1 << 4, "wEnemyMonStatus": 1 << 6, "wPlayerAccLevel": 6}
    yield "quick_claw_poison_defender", Mon.of("MUK", 50, ["SLUDGE"]), Mon.of("MACHAMP", 50, ["CROSS_CHOP"]), {
        "wEnemyMonItem": ITEMS["QUICK_CLAW"], "wPlayerSubStatus3": 1 << 6, "wEnemySubStatus4": 1 << 5}
    # Per-hit roll ranges wider than a byte (4x Bug multi-hit into a level 5 defender).
    yield "wide_roll_range", Mon.of("EXEGGCUTE", 5, ["BARRAGE"]), Mon.of("PINSIR", 100, ["PIN_MISSILE"]), {}


def compile_pair(h, mem, regs, base, move, mask):
    """Return (producer record, native record) for one reply on the current epoch."""
    h.wr("wBattleAnimTileDict", move, 54)  # AV_REPLY
    prefix = bytes(mem[base:base + 324])
    assert h.invoke("BossAI_FastPrepareReply", {**regs, "C": mask})
    producer = bytes(mem[base + 399:base + 447])
    mem[base + 399:base + 447] = [0x5a] * 48
    mem[base:base + 89] = list(prefix[:89])
    assert h.invoke("BossAI_FastCompileReplyNative", {**regs, "A": move, "C": mask})
    native = bytes(mem[base + 399:base + 447])
    return producer, native


def main():
    count = 0
    with open_harness("pokegold_ai_reference") as h:
        mem, rf = h.pb.memory, h.pb.register_file
        base = h.syms["wBattleAnimTileDict"].address
        regs = {"D": base >> 8, "E": base & 255}
        initial_sp = int(rf.SP)
        assert h.invoke("OpenSRAM", {"A": 0})
        for name, boss, player, extra in scenarios():
            h.invoke("BossAI_ResetTurnCaches")
            h.seed_battle(boss, player, extra=extra)
            h.wr("wOTPartyCount", 2)
            h.wr("wCurOTMon", 0)
            bench = Mon.of("DITTO" if name == "plain" else "SCIZOR", 48, ["TACKLE"], hp_pct=60)
            for field, value in (("Species", bench.species), ("Level", bench.level), ("Status", 0x20),
                                 ("Item", ITEMS["ROCKY_HELMET"] if name == "plain" else 0)):
                h.wr("wOTPartyMon1" + field, value, 48)
            for field, value in (("HP", bench.hp), ("MaxHP", bench.max_hp), ("Attack", bench.atk),
                                 ("Defense", bench.deff), ("Speed", bench.spe), ("SpclAtk", bench.spa), ("SpclDef", bench.spd)):
                h.wr("wOTPartyMon1" + field, value >> 8, 48)
                h.wr("wOTPartyMon1" + field, value & 255, 49)
            for slot, kind in ((255, 0), (1, 1)):
                mem[base:base + 472] = [0] * 472
                mem[base + 51:base + 55] = [kind, slot, MOVES["STRUGGLE"], MOVES["TACKLE"]]
                assert h.invoke("BossAI_PreparePublicAction", regs)
                mem[base:base + 51] = list(mem[base + 89:base + 140])  # owned context for the actor import
                assert h.invoke("BossAI_FastImportActorHP", {**regs, "C": 128}) and h.outcome()["carry"]
                assert h.invoke("BossAI_FastPrepareReplyFacts", regs)
                for move in range(1, NUM_ATTACKS + 1):
                    mask = 15 if move % 3 else (move % 16 or 1)
                    producer, native = compile_pair(h, mem, regs, base, move, mask)
                    if producer != native:
                        diff = [(i, producer[i], native[i]) for i in range(48) if producer[i] != native[i]]
                        raise AssertionError((name, slot, move, [k for k, v in MOVES.items() if v == move], mask, diff,
                                              producer.hex(), native.hex()))
                    assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == base
                    count += 1
        assert h.invoke("CloseSRAM")
    print(f"PASS: {count} native reply compiles match the producer path byte for byte")


if __name__ == "__main__":
    main()
