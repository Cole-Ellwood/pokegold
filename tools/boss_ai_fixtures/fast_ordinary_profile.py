"""Ordinary-decision timing: frozen oracle versus native prototype, with phases.

Whole-decision cycles run from the bank-qualified entry to the final CloseSRAM
return. Native cycles are also split into disjoint phases: every hooked entry
closes the previous phase, so each cycle belongs to exactly one bucket. Buckets
are inclusive of the callees of the hooked routine until the next hooked entry.
"""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from tools.boss_ai_fixtures.cases import CASES
from tools.boss_ai_fixtures.fast_reference import ORACLE
from tools.boss_ai_fixtures.harness import open_harness
from tools.boss_ai_fixtures.joint import seed_joint_case

PROTOTYPE = "BossAI_ComparePublicActionsFastPrototype"
PHASES = {
    PROTOTYPE: "entry_inputs",
    PROTOTYPE + ".ReplyMass": "orchestration",
    PROTOTYPE + ".ActiveDefender": "orchestration",
    PROTOTYPE + ".SwitchDefender": "orchestration",
    PROTOTYPE + ".ApplyEntry": "orchestration",
    PROTOTYPE + ".InitMovePlan": "orchestration",
    PROTOTYPE + ".InitUnaryRecord": "orchestration",
    PROTOTYPE + ".PrepareReply": "orchestration",
    PROTOTYPE + ".AccumulateIncoming": "orchestration",
    PROTOTYPE + ".reply_plans": "orchestration",
    PROTOTYPE + ".plan_skip": "orchestration",
    PROTOTYPE + ".reply_next": "orchestration",
    PROTOTYPE + ".AddPairTotal": "orchestration",
    PROTOTYPE + ".CommitIncoming": "orchestration",
    "BossAI_FastPrepareOwnedCandidate": "owned_prepare",
    "BossAI_FastPrepareActiveFacts": "owned_prepare",
    "BossAI_FastPrepareReplacementFacts": "owned_prepare",
    "BossAI_PreparePublicAction": "owned_prepare",
    "BossAI_FastImportActorHP": "hp_tables",
    "BossAI_FastBuildOwnedStandalone": "owned_standalone",
    "BossAI_FastPrepareReply": "reply_prepare",
    "BossAI_FastCompileReplyNative": "reply_compile_native",
    "BossAI_FastPrepareReplyFacts": "reply_facts",
    "BossAI_FastBuildReplyStandalone": "reply_standalone",
    "BossAI_FastNormalizedPair.CorrectionOnly": "native_pair",
    "BossAI_FastScalarPair": "scalar_pair",
    "BossAI_FastScalarReplyStandalone": "scalar_standalone",
    "BossAI_FastFallbackPair.CorrectionOnly": "fallback_pair",
    "BossAI_FastUnaryFallback": "unary_fallback",
    "BossAI_FastFinalizeResults": "finalize",
}
COUNTED = ("BossAI_PublicDamageRange", "BossAI_ValuePublicExchange", "BossAI_FastBuildHPTable",
           "BossAI_FastExecuteOwnedPlan", "BossAI_FastExecuteReplyPlan")


def ordinary_cases():
    return [c for c in CASES if c.joint_check is not None and c.joint_check.get("kind", 0) == 0]


def run(h, case, scan, entry, kind):
    h.invoke("BossAI_ResetTurnCaches")
    h.seed_battle(case.boss, case.player, tier=case.tier, scores=case.scores, extra=case.extra)
    seed_joint_case(h, case)
    base = h.syms["wBattleAnimTileDict"].address
    h.pb.memory[base:base + 472] = [0xa5] * 472
    assert h.invoke(entry, {"A": kind, "B": scan, "D": base >> 8, "E": base & 255}, frame_budget=60000)
    return base


def measure_reference(cases):
    rows = []
    with open_harness(ORACLE) as h:
        entry = "BossAI_ComparePublicActionsWithTables"
        stamps = {}
        s = h.syms[entry]
        h.pb.hook_register(s.bank, s.address, lambda _: stamps.__setitem__("start", h.pb._cycles()), None)
        close = h.syms["CloseSRAM"]
        h.pb.hook_register(close.bank, close.address, lambda _: stamps.__setitem__("end", h.pb._cycles() + 84), None)
        for case in cases:
            for scan in (0, 15):
                stamps.clear()
                run(h, case, scan, entry, 0)
                assert h.outcome()["carry"]
                rows.append({"case": case.id, "scan": scan, "cycles": stamps["end"] - stamps["start"]})
        h.pb.hook_deregister(s.bank, s.address)
        h.pb.hook_deregister(close.bank, close.address)
    return rows


def measure_native(cases):
    rows = []
    with open_harness("pokegold_ai_reference") as h:
        trace = []
        counts = Counter()
        for name in PHASES:
            s = h.syms[name]
            h.pb.hook_register(s.bank, s.address, (lambda n: lambda _: trace.append((n, h.pb._cycles())))(name), None)
        close = h.syms["CloseSRAM"]
        h.pb.hook_register(close.bank, close.address, lambda _: trace.append(("CloseSRAM", h.pb._cycles() + 84)), None)
        for name in COUNTED:
            s = h.syms[name]
            h.pb.hook_register(s.bank, s.address, (lambda n: lambda _: counts.__setitem__(n, counts[n] + 1))(name), None)
        for case in cases:
            for scan in (0, 15):
                trace.clear()
                counts.clear()
                base = run(h, case, scan, PROTOTYPE, 0)
                status = h.pb.memory[base + 126]
                assert status in (0, 1), (case.id, status)
                phases = defaultdict(int)
                calls = Counter()
                for (name, start), (_, end) in zip(trace, trace[1:]):
                    phases[PHASES.get(name, name)] += end - start
                    calls[name] += 1
                rows.append({"case": case.id, "scan": scan, "status": status,
                             "cycles": trace[-1][1] - trace[0][1],
                             "phases": dict(sorted(phases.items(), key=lambda kv: -kv[1])),
                             "calls": dict(sorted(calls.items())), "counts": dict(sorted(counts.items()))})
    return rows


def main():
    cases = ordinary_cases()
    reference, native = measure_reference(cases), measure_native(cases)
    rows = []
    for old, new in zip(reference, native):
        assert (old["case"], old["scan"]) == (new["case"], new["scan"])
        rows.append(dict(new, reference_cycles=old["cycles"], native_cycles=new.pop("cycles")))
    worst = max(rows, key=lambda row: row["native_cycles"])
    totals = Counter()
    for row in rows:
        totals.update(row["phases"])
    result = {
        "rom_sha256": hashlib.sha256(Path("pokegold_ai_reference.gbc").read_bytes()).hexdigest(),
        "oracle_sha256": hashlib.sha256(Path(ORACLE + ".gbc").read_bytes()).hexdigest(),
        "unit": "DMG T-cycles, bank-qualified entry through the final CloseSRAM return; caller setup excluded",
        "reference_entry": "BossAI_ComparePublicActionsWithTables on the frozen oracle",
        "scope": f"{len(cases)} ordinary joint fixtures in two scans; existing producers, no grouped arithmetic",
        "limitation": "Structural prototype timing only. The two-second target is not met and no domain bound is claimed.",
        "budget_cycles": 8388608,
        "worst_native": {k: worst[k] for k in ("case", "scan", "native_cycles", "reference_cycles", "status", "phases", "counts")},
        "phase_totals_all_rows": dict(sorted(totals.items(), key=lambda kv: -kv[1])),
        "rows": rows,
    }
    output = Path("audit/boss_ai_strategy_2026-09-06/selector_implementation/fast_ordinary_profile.json")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    summary = [{"case": r["case"], "scan": r["scan"], "native": r["native_cycles"],
                "reference": r["reference_cycles"], "status": r["status"]} for r in rows]
    print(json.dumps({"worst_native": result["worst_native"], "rows": summary}, indent=1))


if __name__ == "__main__":
    main()
