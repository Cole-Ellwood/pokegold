"""Private selector boundary checks: real farcalls, complete records, late rejection."""
import random

from tools.boss_ai_fixtures.cases import CASES
from tools.boss_ai_fixtures.harness import open_harness
from tools.boss_ai_fixtures.runner import run_case, check


INVALID = (0, 0, 65535, 255)


def packed(records):
    return b"".join(t.to_bytes(5, "big") + m.to_bytes(2, "big")
                    + s.to_bytes(2, "big") + bytes([u]) for t, m, s, u in records)


def check_finalizer(h, records, mask, status, reject=False):
    base = h.syms["wBattleAnimTileDict"].address
    mem, rf = h.pb.memory, h.pb.register_file
    assert h.invoke("OpenSRAM", {"A": 0})
    mem[0xa000:0xa600] = [0xa5] * 1536
    mem[0xa280:0xa2f8] = list(packed(records))
    sram = bytes(mem[0xa000:0xa620])
    mem[base:base + 472] = [0x5a] * 472
    mem[base + 467:base + 469] = list(mask.to_bytes(2, "big"))
    mem[base + 471] = status
    before = bytes(mem[base - 1:base + 480])
    sp = int(rf.SP)
    assert h.invoke("BossAI_FastFinalizeResults", {"D": base >> 8, "E": base & 255})
    out = h.outcome()
    assert int(rf.SP) == sp and (int(rf.D) << 8 | int(rf.E)) == base
    assert h.rd("hROMBank") == h.syms["BossAI_FastFinalizeResults"].bank
    assert mem[0xa000] == 255, "SRAM left open"
    if reject:
        expected = [INVALID] * 12
        mask, status = 0, 255
    else:
        expected = [(t, m, (t >> 16) // m, u) if mask & (1 << i) else INVALID
                    for i, (t, m, _, u) in enumerate(records)]
    legal = [i for i in range(12) if mask & (1 << i)]
    best = min(legal, key=lambda i: (-expected[i][2], i)) if legal else 255
    score = expected[best][2] if legal else 0
    uncertainty = expected[best][3] if legal else 255
    summary = bytes([best, uncertainty]) + score.to_bytes(2, "big") + mask.to_bytes(2, "big") + bytes([status, 1])
    assert bytes(mem[base:base + 128]) == packed(expected) + summary
    assert (out["bc"], out["carry"]) == (score, bool(legal))
    after = bytes(mem[base - 1:base + 480])
    allowed = set(range(1, 129)) | ({468, 469, 472} if reject else set())
    assert all(a == b for i, (a, b) in enumerate(zip(before, after)) if i not in allowed)
    assert h.invoke("OpenSRAM", {"A": 0})
    assert bytes(mem[0xa280:0xa2f8]) == packed(expected)
    after = bytes(mem[0xa000:0xa620])
    assert all(a == b for i, (a, b) in enumerate(zip(sram, after))
               if not (0x280 <= i < 0x2f8 or 0x510 <= i < 0x530))
    assert h.invoke("CloseSRAM")


def main():
    rng = random.Random(20260907)
    tested = 0
    with open_harness("pokegold_ai_reference") as h:
        for _ in range(1000):
            records = []
            for i in range(12):
                mass = rng.choice((1, 2, 255, 256, 564))
                total = rng.randrange(2048 * mass * 65536 + 1)
                records.append((total, mass, rng.randrange(65536), rng.randrange(256)))
            check_finalizer(h, records, rng.randrange(4096), rng.randrange(3))
            tested += 1
        for status in (0, 1, 2):
            check_finalizer(h, [INVALID] * 12, 0, status)
            tested += 1
        records = [INVALID] * 12
        records[0] = (1024 * 2 * 65536 + 1, 2, 0, 3)
        records[11] = (1024 * 2 * 65536 + 65535, 2, 0, 7)
        check_finalizer(h, records, 0x801, 1)  # larger raw T must lose integer tie
        tested += 1
        for mass, score, status, mask in ((0, 1, 0, 0x801), (565, 1, 0, 0x801),
                                         (2, 2049, 0, 0x801), (2, 2048, 3, 0x801),
                                         (2, 2048, 255, 0x801), (2, 2048, 0, 0x1801)):
            records[11] = (mass * score * 65536, mass, 0, 7)
            check_finalizer(h, records, mask, status, reject=True)
            tested += 1
        records[11] = (2048 * 564 * 65536, 564, 0, 7)
        check_finalizer(h, records, 0x801, 0)
        tested += 1

    preparations = 0
    for case in CASES:
        if case.candidate_check is None:
            continue
        with open_harness("pokegold_ai_reference") as h:
            original = h.invoke

            def invoke(name, regs=None, **kwargs):
                nonlocal preparations
                ok = original(name, regs, **kwargs)
                if name != "BossAI_EnumeratePublicActions":
                    return ok
                rf, mem = h.pb.register_file, h.pb.memory
                saved = {r: int(getattr(rf, r)) for r in ("A", "F", "B", "C", "D", "E", "HL", "SP", "PC")}
                saved_bank = h.rd("hROMBank")
                pointer = regs["D"] << 8 | regs["E"]
                expected_actions = bytes(mem[pointer:pointer + 8])
                scratch = h.syms["wAttrmap"].address
                assert original("BossAI_BuildPublicReplySet", {"D": scratch >> 8, "E": scratch & 255})
                expected_replies = bytes(mem[scratch:scratch + 67]) if regs["A"] == 0 else bytes(67)
                base = h.syms["wBattleAnimTileDict"].address
                for scan in (0, 15):
                    mem[base:base + 472] = [0xa5] * 472
                    boundary = bytes(mem[base + 472:base + 480])
                    assert original("BossAI_FastPreparePublicInputs", {"A": regs["A"], "B": scan,
                                    "D": base >> 8, "E": base & 255})
                    assert h.outcome()["carry"]
                    assert bytes(mem[base + 324:base + 332]) == expected_actions
                    assert bytes(mem[base + 332:base + 399]) == expected_replies
                    assert mem[base + 140] == 0 and mem[base + 471] == 255
                    assert mem[base + 447] == regs["A"] and mem[base + 448] == scan
                    assert int(rf.SP) == saved["SP"] and (int(rf.D) << 8 | int(rf.E)) == base
                    assert h.rd("hROMBank") == h.syms["BossAI_FastPreparePublicInputs"].bank
                    assert bytes(mem[base + 472:base + 480]) == boundary
                    preparations += 1
                for kind, scan in ((1, 0), (3, 0), (255, 0), (0, 16), (2, 255)):
                    before = bytes(mem[base:base + 472])
                    assert original("BossAI_FastPreparePublicInputs", {"A": kind, "B": scan,
                                    "D": base >> 8, "E": base & 255})
                    assert not h.outcome()["carry"] and bytes(mem[base:base + 472]) == before
                    assert int(rf.SP) == saved["SP"] and (int(rf.D) << 8 | int(rf.E)) == base
                for r, value in saved.items():
                    setattr(rf, r, value)
                h.wr("hROMBank", saved_bank)
                mem[0x2000] = saved_bank
                return ok

            h.invoke = invoke
            out = run_case(h, case)
            assert not check(case, out), (case.id, check(case, out))
    joint_vectors = 0
    for case in CASES:
        if case.joint_check is None:
            continue
        with open_harness("pokegold_ai_reference") as h:
            out = run_case(h, case)
            assert not check(case, out), (case.id, check(case, out))
            records = out["joint_records"]
            mask = sum(1 << i for i, record in enumerate(records) if record != INVALID)
            check_finalizer(h, records, mask, 1)
            joint_vectors += 1
    print(f"PASS: {tested} complete-vector finalizations and late rejections, "
          f"{preparations} real cross-bank input preparations, {joint_vectors} exhaustive "
          "joint numerator vectors; DE/SP/bank/SRAM boundaries")


if __name__ == "__main__":
    main()
