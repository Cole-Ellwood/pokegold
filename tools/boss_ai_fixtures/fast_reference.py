"""Complete restart vectors versus independent frozen-ROM aggregation."""
import argparse
from dataclasses import replace
from tools.boss_ai_fixtures.cases import CASES
from tools.boss_ai_fixtures.fast_results import INVALID, packed
from tools.boss_ai_fixtures.harness import Mon, open_harness
from tools.boss_ai_fixtures.joint import ITEMS, seed_joint_case
from tools.boss_ai_fixtures.runner import run_case, check


ORACLE = ".local/ai-two-second/preflight-2026-09-06-pro2/oracle"


def replacement_boundaries():
    template = next(c for c in CASES if c.id == "joint_replacement_hazards")
    maxima = (1, 2, 127, 128, 129, 192, 193, 255, 256, 999, 1023, 1535, 1536, 65535)
    species = ("SNORLAX", "PIDGEOT", "STEELIX", "PIKACHU", "BLASTOISE")
    for maximum in maxima:
        for layers in range(4):
            bench = []
            for i, name in enumerate(species):
                mon = Mon.of(name, 50, ["TACKLE"])
                bench.append(replace(mon, max_hp=maximum,
                                     hp=(1, maximum, max(1, maximum // 2))[i % 3]))
            extra = {"wEnemyScreens": layers, "wBossAIWinconMonIdx": layers + 2,
                     "wPlayerSubStatus1": 255 if layers & 1 else 0,
                     ("wOTPartyMon1Item", 48): ITEMS["AIR_BALLOON"],
                     ("wOTPartyMon1Item", 96): ITEMS["QUICK_CLAW"],
                     ("wOTPartyMon1Item", 144): ITEMS["KINGS_ROCK"]}
            yield replace(template, id=f"replacement_hp{maximum}_spikes{layers}",
                          extra=extra, joint_check={"kind": 2, "bench": bench})
    for maximum, hp in ((100, 101), (0, 1)):
        bench = [Mon.of(name, 50, ["TACKLE"]) for name in species]
        # Third of five bench slots: both scans finish valid native records
        # before discovering the diagnostic actor and discarding that state.
        bench[2] = replace(bench[2], max_hp=maximum, hp=hp)
        yield replace(template, id=f"replacement_restart_hp{hp}_max{maximum}",
                      extra={"wEnemyScreens": 3},
                      joint_check={"kind": 2, "bench": bench, "native_restart": True})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prototype", action="store_true")
    parser.add_argument("--replacement-boundaries", action="store_true")
    args = parser.parse_args()
    prototype = args.prototype or args.replacement_boundaries
    entry = ("BossAI_ComparePublicActionsFastPrototype" if prototype else
             "BossAI_ComparePublicActionsFastReferenceRestart")
    tested = 0
    for case in replacement_boundaries() if args.replacement_boundaries else CASES:
        if case.joint_check is None:
            continue
        with open_harness(ORACLE) as oracle:
            out = run_case(oracle, case)
            assert not check(case, out), (case.id, check(case, out))
            records = out["joint_records"]
        legal = [i for i, record in enumerate(records) if record != INVALID]
        mask = sum(1 << i for i in legal)
        best = min(legal, key=lambda i: (-records[i][2], i)) if legal else 255
        score, uncertainty = (records[best][2], records[best][3]) if legal else (0, 255)
        replacement = prototype and case.joint_check.get("kind", 0) == 2
        native = replacement and not case.joint_check.get("native_restart")
        expected = (packed(records) + bytes((best, uncertainty)) +
                    score.to_bytes(2, "big") + mask.to_bytes(2, "big") + bytes((0 if native else 2, 1)))
        with open_harness("pokegold_ai_reference") as h:
            h.invoke("BossAI_ResetTurnCaches")
            h.seed_battle(case.boss, case.player, tier=case.tier,
                          scores=case.scores, extra=case.extra)
            seed_joint_case(h, case)
            mem, rf = h.pb.memory, h.pb.register_file
            base = h.syms["wBattleAnimTileDict"].address
            sp = int(rf.SP)
            random_calls = []
            random_symbol = h.syms["Random"]
            h.pb.hook_register(random_symbol.bank, random_symbol.address,
                               lambda _: random_calls.append(1), None)
            for scan in (0, 15):
                assert h.invoke("OpenSRAM", {"A": 0})
                mem[0xa000:0xa600] = [0xa5] * 1536
                sram = bytes(mem[0xa000:0xa620])
                assert h.invoke("CloseSRAM")
                mem[base:base + 472] = [0x5a] * 472
                boundary = bytes(mem[base + 472:base + 480])
                assert h.invoke(entry, {
                    "A": case.joint_check.get("kind", 0), "B": scan,
                    "D": base >> 8, "E": base & 255}, frame_budget=30000)
                assert bytes(mem[base:base + 128]) == expected, (case.id, scan)
                assert (h.outcome()["bc"], h.outcome()["carry"]) == (score, bool(legal))
                assert int(rf.SP) == sp and (int(rf.D) << 8 | int(rf.E)) == base
                assert h.rd("hROMBank") == h.syms[entry].bank
                assert mem[0xa000] == 255
                assert bytes(mem[base + 472:base + 480]) == boundary
                assert h.invoke("OpenSRAM", {"A": 0})
                after = bytes(mem[0xa000:0xa620])
                assert all(a == b for i, (a, b) in enumerate(zip(sram, after))
                           if not (0x280 <= i < 0x2f8 or 0x510 <= i < 0x530 or
                                   replacement and (i < 0x180 or 0x3f8 <= i < 0x420 or
                                               i == 0x47c or 0x487 <= i < 0x489))), case.id
                assert h.invoke("CloseSRAM")
                tested += 1
            assert not random_calls
            h.pb.hook_deregister(random_symbol.bank, random_symbol.address)
        print(f"PASS {case.id}: full frozen T/M/score/uncertainty, forward/reverse", flush=True)
    with open_harness("pokegold_ai_reference") as h:
        mem, rf = h.pb.memory, h.pb.register_file
        sp = int(rf.SP)
        for kind, scan in ((1, 0), (3, 15), (255, 0), (0, 16), (2, 255)):
            assert h.invoke(entry, {
                "A": kind, "B": scan, "D": 0xc9, "E": 0})
            assert bytes(mem[0xc900:0xc978]) == packed([INVALID] * 12)
            assert mem[0xc97e] == 255 and not h.outcome()["carry"] and h.outcome()["bc"] == 0
            assert mem[0xa000] == 255
            assert int(rf.SP) == sp and (int(rf.D) << 8 | int(rf.E)) == 0xc900
    print(f"PASS: {tested} frozen-reference restart vectors and 5 invalid entries; "
          "DE/SP/bank/SRAM and context boundaries")


if __name__ == "__main__":
    main()
