"""ROM parity and cycle crossover for the local table-offset arithmetic."""
import json
from pathlib import Path
from tools.boss_ai_fixtures.harness import open_harness


def main():
    failures, cycles = [], []
    count = 0
    with open_harness() as h:
        rf = h.pb.register_file
        active = {"start":None, "cycles":None}
        hooks = []
        def start(_):
            if active["start"] is None:
                active["start"] = h.pb._cycles()
        def linear_start(_):
            start(None)
            if int(rf.A) == 0:
                # The remaining AND A + taken RET Z execute in 24 cycles.
                active["cycles"] = h.pb._cycles() - active["start"] + 24
        def linear_last(_):
            if int(rf.A) == 1:
                # Last ADD HL,BC; DEC A; untaken JR NZ; RET = 36 cycles.
                active["cycles"] = h.pb._cycles() - active["start"] + 36
        def binary_done(_):
            # POP BC + RET = 28 cycles, included in the reported routine cost.
            active["cycles"] = h.pb._cycles() - active["start"] + 28
        for label, callback in (("AddNTimes",linear_start), ("AddNTimes.loop",linear_last),
                ("BossAI_AddTableOffset",start), ("BossAI_AddTableOffset.binary",start),
                ("BossAI_AddTableOffset.done",binary_done)):
            sym = h.syms[label]
            h.pb.hook_register(sym.bank,sym.address,callback,None)
            hooks.append(sym)
        def invoke(label, index, stride, base):
            active.update(start=None,cycles=None)
            sp = int(rf.SP)
            ok = h.invoke(label, {"A":index,"B":stride >> 8,"C":stride & 255,
                "HL":base,"D":0xa5,"E":0x5a})
            result = (int(rf.HL),int(rf.A),int(rf.B)<<8|int(rf.C),int(rf.D)<<8|int(rf.E),int(rf.SP))
            expected = ((base+index*stride)&65535,0,stride,0xa55a,sp)
            return ok and result == expected, result, active["cycles"]
        try:
            bases = sorted({0, 1, 0xfffe, h.syms["Moves"].address, h.syms["BaseData"].address})
            strides = (0,1,7,32,48,255,256,32768,65535)
            for index in range(256):
                for stride in strides:
                    for base in bases:
                        old = invoke("AddNTimes",index,stride,base)
                        new = invoke("BossAI_AddTableOffset",index,stride,base)
                        count += 1
                        if not old[0] or not new[0] or old[1] != new[1]:
                            failures.append(dict(index=index,stride=stride,base=base,old=old,new=new))
                old = invoke("AddNTimes",index,7,0x4000)
                new = invoke("BossAI_AddTableOffset",index,7,0x4000)
                binary = invoke("BossAI_AddTableOffset.binary",index,7,0x4000)
                if not binary[0]:
                    failures.append(dict(index=index,binary=binary))
                binary_cost = binary[2]+20  # CP immediate + untaken JP C
                linear_cost = old[2]+24     # CP immediate + taken JP C
                if new[2] != min(linear_cost,binary_cost):
                    failures.append(dict(index=index,selected=new[2],linear_dispatch=linear_cost,binary_dispatch=binary_cost))
                cycles.append(dict(index=index,linear=old[2],selected=new[2],
                    binary_with_dispatch=binary_cost))
        finally:
            for sym in hooks:
                h.pb.hook_deregister(sym.bank,sym.address)
    result = dict(comparisons=count,failures=failures,cycles=cycles,
        contract="HL modulo 65536, A=0, BC/DE/SP preserved; flags are not an output",
        measurement="Entry through fixed return epilogue; no frame-padding cost. Binary column includes 20-cycle dispatch.")
    Path(__file__).with_name("table_index_math.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("parity",count,"failures",len(failures))
    print("crossover",[r for r in cycles if 8 <= r["index"] <= 17])
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
