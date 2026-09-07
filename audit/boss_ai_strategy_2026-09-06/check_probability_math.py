"""Check ROM probability decoding, scaling and final global division."""
import json
from pathlib import Path
from tools.boss_ai_fixtures.harness import open_harness
from tools.boss_ai_fixtures.layout import JC_SIZE, JC_TOTAL, JC_MASS, JC_OWN_ACCURACY, JC_REPLY_ACCURACY


def main():
    rows = []
    with open_harness() as h:
        pointer = h.syms["wTilemap"].address
        rf = h.pb.register_file
        def invoke(label, regs=None):
            sp = int(rf.SP)
            returned = h.invoke("BossAI_ComparePublicActions." + label,
                dict(regs or {}, D=pointer >> 8, E=pointer & 255))
            return returned and int(rf.SP) == sp and (int(rf.D) << 8 | int(rf.E)) == pointer
        for raw in (0, 1, 2, 127, 128, 254, 255):
            p = 256 if raw == 255 else raw
            for side, offset, bit in (("Own", JC_OWN_ACCURACY, 0), ("Reply", JC_REPLY_ACCURACY, 1)):
                h.wr("wTilemap", raw, offset)
                for miss in (0, 1):
                    h.wr("wTilemap", miss << bit, 80)
                    ok = invoke(side + "Probability")
                    expected = 256 - p if miss else p
                    observed = h.outcome()["bc"]
                    rows.append(dict(path="probability", raw=raw, side=side, miss=miss,
                        expected=expected, observed=observed, passed=ok and observed == expected))
        for value in (0, 1, 255, 32767, 0x7fffff):
            for probability in (0, 1, 2, 128, 254, 255, 256):
                for i, byte in enumerate(value.to_bytes(4, "big")):
                    h.wr("hProduct", byte, i)
                ok = invoke("ScaleProbability", {"B":probability >> 8, "C":probability & 255})
                observed = int.from_bytes(bytes(h.rd("hProduct", i) for i in range(4)), "big")
                rows.append(dict(path="product", value=value, probability=probability,
                    expected=value*probability, observed=observed, passed=ok and observed == value*probability))
        for mass in (0, 1, 2, 16, 65, 282, 4064):
            totals = {0}
            if mass:
                for quotient in (1, 1024, 1983):
                    boundary = quotient * mass * 65536
                    totals.update((boundary-1, boundary, boundary+1,
                        (quotient*mass+mass-1)*65536+65535))
            for total in sorted(totals):
                for i, byte in enumerate(total.to_bytes(5, "big")):
                    h.wr("wTilemap", byte, JC_TOTAL+i)
                for i, byte in enumerate(mass.to_bytes(2, "big")):
                    h.wr("wTilemap", byte, JC_MASS+i)
                before = bytes(h.rd("wTilemap", i) for i in range(JC_SIZE))
                ok = invoke("Mean")
                expected = total // (mass*65536) if mass else 0
                observed = h.outcome()["bc"]
                unchanged = before == bytes(h.rd("wTilemap", i) for i in range(JC_SIZE))
                rows.append(dict(path="mean", total=total, mass=mass, expected=expected,
                    observed=observed, passed=ok and unchanged and observed == expected))
    Path(__file__).with_name("probability_math.json").write_text(json.dumps(rows, indent=2)+"\n")
    failures = [row for row in rows if not row["passed"]]
    print(f"{len(rows)-len(failures)}/{len(rows)} probability arithmetic checks passed")
    for row in failures:
        print(row)
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
