"""Emulator property checks for private selector arithmetic (reference ROM only)."""
import random

from tools.boss_ai_fixtures.harness import open_harness


def main():
    rng = random.Random(20260907)
    divisions = {(n, d) for n in (0, 1, 255, 256, 65535, 65536, 0x7fffff, 0xffffff)
                 for d in (0, 1, 2, 255, 256, 564, 0x7fff, 0x8000, 0x8001, 0xffff)}
    divisions.update((rng.randrange(1 << 24), rng.randrange(1, 65536)) for _ in range(2000))
    products = {(n, m) for n in (0, 1, -1, -245760, -1920, -(1 << 39), (1 << 39) - 1,
                                 0xffffffff, 69304320)
                for m in (0, 1, 255, 256, 65536, 72192, 144384, 0xffffff)}
    products.update((rng.randrange(-(1 << 39), 1 << 39), rng.randrange(1 << 24))
                    for _ in range(2000))
    with open_harness("pokegold_ai_reference") as h:
        assert h.invoke("OpenSRAM", {"A": 0})
        mem, rf = h.pb.memory, h.pb.register_file
        initial_sp = int(rf.SP)

        def put(address, value, size):
            mem[address:address + size] = list(value.to_bytes(size, "big"))

        def run(name, allowed):
            before = bytes(mem[0xa000:0xa600])
            assert h.invoke(name, {"D": 0xca, "E": 0xfe})
            assert int(rf.SP) == initial_sp and (int(rf.D) << 8 | int(rf.E)) == 0xcafe
            after = bytes(mem[0xa000:0xa600])
            assert all(a == b for i, (a, b) in enumerate(zip(before, after))
                       if i + 0xa000 not in allowed), name

        mem[0xa000:0xa600] = [0xa5] * 1536
        for n, d in sorted(divisions):
            put(0xa51d, n, 3)
            put(0xa520, d, 2)
            run("BossAI_FastDivide24By16", {0xa51d, 0xa51e, 0xa51f, 0xa522})
            q = int.from_bytes(bytes(mem[0xa51d:0xa520]), "big")
            if not d:
                assert q == n and h.outcome()["carry"]
            else:
                assert (q, h.outcome()["bc"]) == divmod(n, d), (n, d, q)
                assert not h.outcome()["carry"]
        for n, m in sorted(products):
            put(0xa510, n % (1 << 40), 5)
            put(0xa515, m, 3)
            run("BossAI_FastMultiply40By24", set(range(0xa510, 0xa51d)))
            actual = int.from_bytes(bytes(mem[0xa518:0xa51d]), "big")
            assert actual == n * m % (1 << 40), (n, m, actual)
        assert h.invoke("CloseSRAM")
    print(f"PASS: {len(divisions)} divisions, {len(products)} signed ring products; "
          "DE/SP and SRAM write footprints preserved")


if __name__ == "__main__":
    main()
