"""Bank-qualified HP construction/lookup cycle sweep; no host timing claims."""
import hashlib
import json
from pathlib import Path

from tools.boss_ai_fixtures.harness import open_harness


def main():
    rows = []
    with open_harness("pokegold_ai_reference") as h:
        assert h.invoke("OpenSRAM", {"A": 0})
        stamps = []
        entry = h.syms["BossAI_FastBuildHPTable"]
        done = h.syms["BossAI_FastBuildHPTable.done"]
        h.pb.hook_register(entry.bank, entry.address, lambda _: stamps.append([h.pb._cycles()]), None)
        # done: ld a,[mode]; pop de; scf; ret = 48 T-cycles.
        h.pb.hook_register(done.bank, done.address, lambda _: stamps[-1].append(h.pb._cycles() + 48), None)
        for base, weight in ((0xa000, 128), (0xa000, 192), (0xa180, 128)):
            worst = (0, 0)
            for maximum in range(1, 1000):
                assert h.invoke("BossAI_FastBuildHPTable", {"A": weight, "B": maximum >> 8,
                                "C": maximum & 255, "HL": base})
                assert h.outcome()["carry"]
                cycles = stamps[-1][1] - stamps[-1][0]
                worst = max(worst, (cycles, maximum))
            rows.append(dict(table=hex(base), weight=weight, worst_cycles=worst[0], maximum=worst[1]))
        h.pb.hook_deregister(entry.bank, entry.address)
        h.pb.hook_deregister(done.bank, done.address)
        lookup_cycles = []
        entry = h.syms["BossAI_FastHPRank8"]
        end_address = h.syms["BossAI_FastHPRank8.masks"].address - 1
        assert h.pb.memory[entry.bank, end_address] == 0xc9
        stamps.clear()
        h.pb.hook_register(entry.bank, entry.address, lambda _: stamps.append([h.pb._cycles()]), None)
        h.pb.hook_register(entry.bank, end_address, lambda _: stamps[-1].append(h.pb._cycles() + 16), None)
        for hp in range(1000):
            assert h.invoke("BossAI_FastHPRank8", {"B": hp >> 8, "C": hp & 255, "HL": 0xa180})
            assert h.outcome()["a"] == 128 * hp // 999
            lookup_cycles.append(stamps[-1][1] - stamps[-1][0])
        h.pb.hook_deregister(entry.bank, entry.address)
        h.pb.hook_deregister(entry.bank, end_address)
        assert h.invoke("CloseSRAM")
    result = {
        "rom_sha256": hashlib.sha256(Path("pokegold_ai_reference.gbc").read_bytes()).hexdigest(),
        "domain": "HP maxima 1..999, every maximum for each actor/weight class",
        "cycles": "DMG T-cycles, bank-qualified entry to return; excludes caller argument loading",
        "construction": rows,
        "seven_tables_with_calls": 5 * rows[0]["worst_cycles"] + rows[1]["worst_cycles"]
                                  + rows[2]["worst_cycles"] + 7 * 24,
        "rank_lookup_body": [min(lookup_cycles), max(lookup_cycles)],
        "rank_lookup_with_call": [min(lookup_cycles) + 24, max(lookup_cycles) + 24],
        "limitation": "Helper phase only; complete selector and integration timing remain unmeasured",
    }
    output = Path("audit/boss_ai_strategy_2026-09-06/selector_implementation/fast_hp_profile.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
