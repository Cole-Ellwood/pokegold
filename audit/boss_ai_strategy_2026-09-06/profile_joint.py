"""Profile the broad conditional matrix with ROM cycle counters, not host time."""
import json
import argparse
import hashlib
from pathlib import Path
from tools.boss_ai_fixtures.cases import CASES
from tools.boss_ai_fixtures.harness import open_harness
from tools.boss_ai_fixtures.runner import run_case, check


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", default="joint_broad_prior_mass")
    parser.add_argument("--rom", default="pokegold")
    parser.add_argument("--tables", action="store_true", help="use synchronous SRAM table entry")
    parser.add_argument("--no-first-state", action="store_true", help="disable first-action reuse for attribution")
    parser.add_argument("--fast-owned", action="store_true", help="broad stress variant with owned speed 999")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("joint_profile.json"))
    args = parser.parse_args()
    case = next(c for c in CASES if c.id == args.case)
    if args.fast_owned:
        from dataclasses import replace
        case = replace(case, id=case.id + "_fast_owned", boss=replace(case.boss, spe=999))
    profiles = []
    with open_harness(args.rom) as h:
        original = h.invoke
        def invoke(name, regs=None, **kwargs):
            entry = "BossAI_ComparePublicActionsWithTables" if args.tables and name == "BossAI_ComparePublicActions" else name
            if args.tables and args.no_first_state and name == "BossAI_ComparePublicActions":
                regs = dict(regs, B=regs["B"] | 16)
            if name != "BossAI_ComparePublicActions" or profiles:
                return original(entry, regs, **kwargs)
            counts, starts, elapsed, hooked = {}, {}, {}, []
            returns = {}
            labels = {
                "exchange": "BossAI_ValuePreparedPublicExchange",
                "prepare_reply": "BossAI_PreparePublicReply",
                "owned_context": "BossAI_BuildOwnedDamageContext",
                "public_context": "BossAI_BuildPublicDamageContext",
                "damage_range": "BossAI_PublicDamageRange",
                "hp_fraction": "BossAI_ValuePublicExchange.HPFraction",
                "hp_fraction_end": "BossAI_ValuePublicExchange.fraction_done",
                "mean": "BossAI_ComparePublicActions.Mean",
                "mean_end": "BossAI_ComparePublicActions.mean_done",
                "player_stat": "BossAI_EstimatePlayerDamageStat",
                "hit_facts": "BossAI_PublicHitFacts",
                "speed_facts": "BossAI_ContextSpeeds",
                "divide": "Divide",
                "multiply": "Multiply",
                "local_divide": "BossAI_Divide",
                "local_multiply": "BossAI_Multiply",
                "chart": "BossAI_DamageKernel.Chart",
                "table_offset": "AddNTimes",
                "binary_table_offset": "BossAI_AddTableOffset",
            }
            def on_label(key):
                counts[key] = counts.get(key, 0) + 1
                now = h.pb._cycles()
                if key.endswith("_end"):
                    root = key[:-4]
                    elapsed[root] = elapsed.get(root, 0) + now - starts[root]
                else:
                    starts[key] = now
                if key in ("exchange", "prepare_reply", "owned_context", "damage_range", "player_stat", "hit_facts", "speed_facts",
                           "divide", "multiply", "local_divide", "local_multiply", "chart", "table_offset", "binary_table_offset"):
                    sp = int(h.pb.register_file.SP)
                    pc = int(h.pb.memory[sp]) | int(h.pb.memory[sp + 1]) << 8
                    bank = h.rd("hROMBank") if pc >= 0x4000 else 0
                    location = (bank, pc)
                    if location not in returns:
                        returns[location] = []
                        h.pb.hook_register(bank, pc, on_return, location)
                    returns[location].append((key, sp + 2, now))
            def on_return(location):
                pending = returns[location]
                sp = int(h.pb.register_file.SP)
                for i in range(len(pending) - 1, -1, -1):
                    key, expected_sp, start_cycle = pending[i]
                    if sp == expected_sp:
                        elapsed[key] = elapsed.get(key, 0) + h.pb._cycles() - start_cycle
                        pending.pop(i)
                        break
            for key, label in labels.items():
                if label not in h.syms:
                    continue
                sym = h.syms[label]
                h.pb.hook_register(sym.bank, sym.address, on_label, key)
                hooked.append(sym)
            start = h.pb._cycles()
            try:
                returned = original(entry, regs, **kwargs)
            finally:
                for sym in hooked:
                    h.pb.hook_deregister(sym.bank, sym.address)
                for bank, pc in returns:
                    h.pb.hook_deregister(bank, pc)
            profiles.append({"scan":regs["B"], "cycles_upper_bound":h.pb._cycles()-start,
                             "calls":counts, "inclusive_loop_cycles":elapsed})
            return returned
        h.invoke = invoke
        outcome = run_case(h, case)
        errors = check(case, outcome)
    result = {"case":case.id, "rom":args.rom,
              "rom_sha256":hashlib.sha256(Path(args.rom + ".gbc").read_bytes()).hexdigest(),
              "errors":errors, "profiles":profiles,
              "limits":"Whole-call cycles include under two frames of return-trap padding; loop times exclude return epilogues."}
    path = args.output
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
