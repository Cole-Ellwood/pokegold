"""Exact compact HP representation checks, including mode and memory boundaries."""
import random

from tools.boss_ai_fixtures.harness import open_harness


def main():
    rng = random.Random(20260907)
    maxima = list(range(1, 257)) + [511, 512, 703, 704, 713, 999, 1023, 1024,
                                   1535, 1536, 2047, 32767, 65535]
    configs = [(base, w, m) for base, w in ((0xa000, 128), (0xa000, 192), (0xa180, 128))
               for m in maxima]
    # Reverse reuse is intentional: shorter tables must not depend on old tails.
    configs += list(reversed(configs))
    entries = lookups = 0
    with open_harness("pokegold_ai_reference") as h:
        assert h.invoke("OpenSRAM", {"A": 0})
        mem, rf = h.pb.memory, h.pb.register_file
        initial_sp = int(rf.SP)
        mem[0xa000:0xa600] = [0xa5] * 1536
        for base, weight, maximum in configs:
            before = bytes(mem[0xa000:0xa600])
            assert h.invoke("BossAI_FastBuildHPTable", {"A": weight, "B": maximum >> 8,
                            "C": maximum & 255, "HL": base, "D": 0xca, "E": 0xfe})
            assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xcafe
            mode = 0 if maximum < weight else (1 if maximum < (1536 if base == 0xa000 else 1024) else 2)
            assert h.outcome()["carry"] and h.outcome()["a"] == mode, (base, weight, maximum)
            if mode == 0:
                expected = bytes(weight * hp // maximum for hp in range(maximum + 1))
            elif mode == 1:
                expected = bytearray()
                for start in range(0, maximum + 1, 8):
                    mask = sum(1 << (i - 1) for i in range(1, 8) if start + i <= maximum
                               and weight * (start + i) // maximum > weight * (start + i - 1) // maximum)
                    expected.extend((weight * start // maximum, mask))
            else:
                expected = b"".join(((k * maximum + weight - 1) // weight).to_bytes(2, "big")
                                    for k in range(1, weight + 1))
            actual = bytes(mem[base:base + len(expected)])
            assert actual == expected, (base, weight, maximum, mode, actual.hex(), expected.hex())
            allowed = set(range(base, base + len(expected))) | set(range(0xa510, 0xa530))
            after = bytes(mem[0xa000:0xa600])
            assert all(a == b for i, (a, b) in enumerate(zip(before, after)) if i + 0xa000 not in allowed)
            entries += len(expected)
            hs = set(range(min(maximum, 17) + 1)) | {maximum, maximum - 1, maximum // 2}
            hs.update(rng.randrange(maximum + 1) for _ in range(12))
            name = ("BossAI_FastHPDirect", "BossAI_FastHPRank8", "BossAI_FastHPThresholds")[mode]
            for hp in sorted(hs):
                assert h.invoke(name, {"A": weight, "B": hp >> 8, "C": hp & 255,
                                      "HL": base, "D": 0xca, "E": 0xfe})
                assert h.outcome()["a"] == weight * hp // maximum, (mode, maximum, weight, hp)
                assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xcafe
                assert h.invoke("BossAI_FastHPPotential", {
                    "A": weight, "B": hp >> 8, "C": hp & 255,
                    "HL": base, "D": mode, "E": 0xfe})
                assert h.outcome()["bc"] == (2 * weight + weight * hp // maximum if hp else 0)
                assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == (mode << 8 | 0xfe)
                lookups += 1
            assert bytes(mem[0xa000:0xa600]) == after, "lookup wrote SRAM"
        for base, weight, maximum in ((0xa000, 128, 0), (0xa180, 192, 999),
                                      (0xa001, 128, 100), (0xa180, 127, 100)):
            before = bytes(mem[0xa000:0xa600])
            assert h.invoke("BossAI_FastBuildHPTable", {"A": weight, "B": maximum >> 8,
                            "C": maximum & 255, "HL": base, "D": 0xca, "E": 0xfe})
            assert not h.outcome()["carry"] and h.outcome()["a"] == 255
            assert bytes(mem[0xa000:0xa600]) == before
            assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xcafe
        assert h.invoke("CloseSRAM")
    print(f"PASS: {len(configs)} HP builds, {entries} table bytes, {lookups} lookups and potentials; "
          "mode/DE/SP/write boundaries and rejected inputs checked")


if __name__ == "__main__":
    main()
