"""End-to-return replacement timing on frozen reference and native entry."""
import hashlib
import json
from pathlib import Path

from tools.boss_ai_fixtures.fast_reference import ORACLE, replacement_boundaries
from tools.boss_ai_fixtures.harness import open_harness
from tools.boss_ai_fixtures.joint import seed_joint_case


def measure(rom, native):
    rows = []
    with open_harness(rom) as h:
        name = "BossAI_ComparePublicActionsFastPrototype" if native else "BossAI_ComparePublicActions"
        entry = h.syms[name]
        end = h.syms["CloseSRAM" if native else "BossAI_ComparePublicActions.done"]
        stamps = []
        h.pb.hook_register(entry.bank, entry.address,
                           lambda _: stamps.__setitem__(slice(None), [h.pb._cycles()]), None)

        def finish(_):
            if len(stamps) == 1:
                # Native finalizer tail-jumps CloseSRAM (84 cycles to return).
                # Frozen .done: load best word40, address20, load8, cp8,
                # untaken jr8, scf4, ret16 =104. All fixtures have legal bench.
                stamps.append(h.pb._cycles() + (84 if native else 104))

        h.pb.hook_register(end.bank, end.address, finish, None)
        for case in replacement_boundaries():
            if case.joint_check.get("native_restart"):
                continue
            for scan in (0, 15):
                h.invoke("BossAI_ResetTurnCaches")
                h.seed_battle(case.boss, case.player, tier=case.tier,
                              scores=case.scores, extra=case.extra)
                seed_joint_case(h, case)
                base = h.syms["wBattleAnimTileDict"].address
                h.pb.memory[base:base + 472] = [0xa5] * 472
                assert h.invoke(name, {"A": 2, "B": scan, "D": base >> 8, "E": base & 255})
                assert h.outcome()["carry"] and len(stamps) == 2
                if native:
                    assert h.pb.memory[base + 126] == 0 and h.pb.memory[0xa000] == 255
                rows.append({"case": case.id, "scan": scan, "cycles": stamps[1] - stamps[0]})
        h.pb.hook_deregister(entry.bank, entry.address)
        h.pb.hook_deregister(end.bank, end.address)
    return rows


def main():
    baseline, native = measure(ORACLE, False), measure("pokegold_ai_reference", True)
    rows = []
    for old, new in zip(baseline, native):
        assert (old["case"], old["scan"]) == (new["case"], new["scan"])
        rows.append({"case": old["case"], "scan": old["scan"],
                     "reference_cycles": old["cycles"], "native_cycles": new["cycles"]})
    worst = max(rows, key=lambda row: row["native_cycles"])
    result = {
        "rom_sha256": hashlib.sha256(Path("pokegold_ai_reference.gbc").read_bytes()).hexdigest(),
        "oracle_sha256": hashlib.sha256(Path(ORACLE + ".gbc").read_bytes()).hexdigest(),
        "unit": "DMG T-cycles, bank-qualified entry through return; caller setup excluded",
        "scope": "112 five-bench replacement decisions, 56 HP/hazard/item/weight fixtures in two scans",
        "limitation": "Representative replacement decisions only; ordinary decisions still restart and whole-domain two-second target is unverified",
        "worst_native": worst,
        "rows": rows,
    }
    output = Path("audit/boss_ai_strategy_2026-09-06/selector_implementation/fast_replacement_profile.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"worst_native": worst, "samples": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
