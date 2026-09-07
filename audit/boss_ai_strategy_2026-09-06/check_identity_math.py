"""Compare AI identity shortcuts with the original ROM Multiply/Divide path."""
import json
from pathlib import Path
from tools.boss_ai_fixtures.harness import open_harness


def main():
    rows = []
    with open_harness() as h:
        def put(value):
            for i, byte in enumerate(value.to_bytes(4, "big")):
                h.wr("hQuotient", byte, i)
        def result():
            return [h.rd("hQuotient", i) for i in range(4)] + [h.rd("hRemainder")]
        for factor in (1, 2, 100, 128, 255):
            for value in (0, 1, 65535, 65536, 0xffffff, 0xabcdef01, 0xff000000):
                put(value)
                h.wr("hMultiplier", factor)
                returned = h.invoke("Multiply")
                h.wr("hDivisor", factor)
                returned &= h.invoke("Divide", {"B":4})
                reference = result()
                put(value)
                returned &= h.invoke("BossAI_DamageKernel.ScaleQuotient", {"B":factor,"C":factor})
                observed = result()
                rows.append({"path":"quotient","factor":factor,"input":value,
                             "reference":reference,"observed":observed,
                             "pass":returned and observed == reference})
            for value in (0, 1, 255, 256, 65535):
                put(value)
                h.wr("hMultiplier", factor)
                returned = h.invoke("Multiply")
                h.wr("hDivisor", factor)
                returned &= h.invoke("Divide", {"B":4})
                reference = int.from_bytes(bytes(result()[:4]), "big")
                returned &= h.invoke("BossAI_DamageKernel.Scale",
                                     {"A":factor,"B":value >> 8,"C":value & 255,"HL":factor << 8})
                observed = h.outcome()["bc"]
                rows.append({"path":"scale","factor":factor,"input":value,
                             "reference":reference,"observed":observed,
                             "pass":returned and observed == reference})
    Path(__file__).with_name("identity_math.json").write_text(json.dumps(rows, indent=2)+"\n", encoding="utf-8")
    failed = [row for row in rows if not row["pass"]]
    print(f"{len(rows)-len(failed)}/{len(rows)} identity arithmetic comparisons passed")
    for row in failed:
        print(row)
    return bool(failed)


if __name__ == "__main__":
    raise SystemExit(main())
