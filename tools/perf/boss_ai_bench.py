"""Boss-AI per-turn cycle benchmark.

Measures cycles spent in BossAI_ApplyMoveModel + BossAI_SelectMove for
synthetic mid/late-tier scenarios. The numbers are *relative* — the
emulator and headless PyBoy timing isn't necessarily wall-clock identical
to a Game Boy, but cycle counts before vs. after an optimization are a
clean apples-to-apples comparison.

Usage:
    python -m tools.perf.boss_ai_bench                       # baseline mode
    python -m tools.perf.boss_ai_bench --out post_opt.json   # after-opt mode
    python -m tools.perf.boss_ai_bench --compare baseline.json post_opt.json

The benchmark hard-codes a small set of scenarios that exercise the
boss-AI hot path (lookahead enabled, multiple candidate moves, varied
types). It does NOT drive real gameplay — it sets WRAM directly and
PC-injects the entry points via the existing call_function_safe helper.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from damage_debugger.emulator import DebugSession  # noqa: E402
from damage_debugger.safe_call import (  # noqa: E402
    call_function_safe,
    read_byte_banked,
    write_byte_banked,
)


# Move IDs for representative late/mid-tier movesets. These are chosen to
# exercise the lookahead branch (damaging + setup mix, multi-type, KO-grade
# power) without depending on exact species moves. The benchmark only
# requires that the 4 moves are non-zero, have varied types, and trip the
# lookahead branch. We pull from common Gen-2 + late-gen additions.
MOVE_OUTRAGE = 0xC8
MOVE_HYPER_BEAM = 0x3F
MOVE_FIRE_BLAST = 0x7E
MOVE_ICE_BEAM = 0x3A
MOVE_THUNDERBOLT = 0x55
MOVE_EARTHQUAKE = 0x59
MOVE_DRAGON_DANCE = 0xFE  # Approx — actual hack uses bestattackup variant
MOVE_REST = 0x9C
MOVE_AGILITY = 0x61
MOVE_BODY_SLAM = 0x22
MOVE_THUNDER = 0x57
MOVE_BLIZZARD = 0x3B


# Boss AI tier values.
AI_TIER_EARLY = 1
AI_TIER_MID = 2
AI_TIER_LATE = 3

# Boss plan ids.
BOSS_PLAN_NONE = 0

# wBattleMode values.
TRAINER_BATTLE = 2


@dataclass
class BossScenario:
    """A boss-AI cycle-bench scenario."""
    name: str
    tier: int
    enemy_species: int
    enemy_level: int
    enemy_type1: int
    enemy_type2: int
    enemy_moves: tuple[int, int, int, int]
    enemy_attack: int = 200
    enemy_defense: int = 180
    enemy_speed: int = 160
    enemy_spatk: int = 200
    enemy_spdef: int = 180
    enemy_max_hp: int = 320
    enemy_cur_hp: int = 320
    player_species: int = 0x9D  # QUILAVA-ish
    player_level: int = 50
    player_type1: int = 0x14  # FIRE
    player_type2: int = 0x14
    player_attack: int = 150
    player_defense: int = 150
    player_speed: int = 150
    player_spatk: int = 150
    player_spdef: int = 150
    player_max_hp: int = 200
    player_cur_hp: int = 180


# Scenarios:
#   - mid_lead: MID-tier representative (Whitney's Miltank archetype).
#   - late_lead: LATE-tier representative (Lance's Dragonite archetype).
#   - late_lookahead_heavy: LATE-tier with all-damaging moveset to maximize
#     lookahead branch coverage.
SCENARIOS = [
    BossScenario(
        name="mid_lead",
        tier=AI_TIER_MID,
        enemy_species=0xF1,  # MILTANK-ish
        enemy_level=20,
        enemy_type1=0x00,  # NORMAL
        enemy_type2=0x00,
        enemy_moves=(MOVE_BODY_SLAM, MOVE_REST, MOVE_AGILITY, MOVE_THUNDERBOLT),
    ),
    BossScenario(
        name="late_lead",
        tier=AI_TIER_LATE,
        enemy_species=0x95,  # DRAGONITE-ish
        enemy_level=50,
        enemy_type1=0x1A,  # DRAGON
        enemy_type2=0x02,  # FLYING
        enemy_moves=(MOVE_OUTRAGE, MOVE_HYPER_BEAM, MOVE_FIRE_BLAST, MOVE_THUNDER),
    ),
    BossScenario(
        name="late_lookahead_heavy",
        tier=AI_TIER_LATE,
        enemy_species=0x95,
        enemy_level=55,
        enemy_type1=0x1A,
        enemy_type2=0x02,
        enemy_moves=(MOVE_OUTRAGE, MOVE_ICE_BEAM, MOVE_THUNDERBOLT, MOVE_EARTHQUAKE),
    ),
]


def write_be_u16(pyboy, bank: int, addr: int, value: int) -> None:
    """Write u16 big-endian (battle stat fields), banked when in WRAMX window."""
    hi = (value >> 8) & 0xFF
    lo = value & 0xFF
    write_byte_banked(pyboy, addr, hi, bank=bank)
    write_byte_banked(pyboy, addr + 1, lo, bank=bank)


def install_scenario(sess: DebugSession, scen: BossScenario) -> None:
    """Populate WRAM with the scenario's battle state.

    Only writes fields the boss-AI hot path reads. Anything not set falls
    back to whatever the boot sequence left there (mostly zero).
    """
    syms = sess.symbols
    pb = sess.pyboy

    def sym_addr(name: str) -> tuple[int, int] | None:
        s = syms.get(name)
        if s is None:
            return None
        return (s.bank, s.address)

    def w_byte(name: str, value: int) -> None:
        sa = sym_addr(name)
        if sa is None:
            return
        write_byte_banked(pb, sa[1], value, bank=sa[0])

    def w_u16(name: str, value: int) -> None:
        sa = sym_addr(name)
        if sa is None:
            return
        write_be_u16(pb, sa[0], sa[1], value)

    def w_moves(name: str, moves: tuple[int, int, int, int]) -> None:
        sa = sym_addr(name)
        if sa is None:
            return
        bank, base = sa
        for i, m in enumerate(moves):
            write_byte_banked(pb, base + i, m, bank=bank)

    # ---- Battle frame ----
    w_byte("wBattleMode", TRAINER_BATTLE)
    w_byte("wLinkMode", 0)
    w_byte("wEnemyDisabledMove", 0)
    w_byte("wEnemySwitchMonIndex", 0)
    w_byte("wOTPartyCount", 6)

    # ---- Enemy mon ----
    w_byte("wEnemyMonSpecies", scen.enemy_species)
    w_byte("wEnemyMonLevel", scen.enemy_level)
    w_byte("wEnemyMonType1", scen.enemy_type1)
    w_byte("wEnemyMonType2", scen.enemy_type2)
    w_byte("wEnemyMonItem", 0)
    w_byte("wEnemyMonStatus", 0)
    w_u16("wEnemyMonHP", scen.enemy_cur_hp)
    w_u16("wEnemyMonMaxHP", scen.enemy_max_hp)
    w_u16("wEnemyMonAttack", scen.enemy_attack)
    w_u16("wEnemyMonDefense", scen.enemy_defense)
    w_u16("wEnemyMonSpeed", scen.enemy_speed)
    w_u16("wEnemyMonSpclAtk", scen.enemy_spatk)
    w_u16("wEnemyMonSpclDef", scen.enemy_spdef)
    w_moves("wEnemyMonMoves", scen.enemy_moves)
    # Give every move full PP (15 is fine; high bits are PP-up counters).
    for i in range(4):
        sa = sym_addr("wEnemyMonPP")
        if sa is not None:
            write_byte_banked(pb, sa[1] + i, 15, bank=sa[0])

    # ---- Player mon ----
    w_byte("wBattleMonSpecies", scen.player_species)
    w_byte("wBattleMonLevel", scen.player_level)
    w_byte("wBattleMonType1", scen.player_type1)
    w_byte("wBattleMonType2", scen.player_type2)
    w_u16("wBattleMonHP", scen.player_cur_hp)

    # ---- Boss AI top-level state ----
    w_byte("wBossAITier", scen.tier)
    w_byte("wBossAIPlanId", BOSS_PLAN_NONE)  # force plan re-selection
    w_byte("wBossAIPlanPhase", 0)             # clear "done this turn" bit

    # Reset turn caches to sentinel ($ff) so the first measurement actually
    # exercises the cache-miss path. New caches added during the perf work
    # are listed alongside the original four.
    for cache_name in (
        "wBossAIHasKOMoveCache",
        "wBossAIPublicThreatCache",
        "wBossAIRevealedPriorityCache",
        "wBossAIPrimaryThreatCache",
        "wBossAIPublicEnemyFasterCache",
        "wBossAILookaheadDepthCache",
        "wBossAILastMatchupType",
        "wBossAIShouldScoutPrereqCache",
    ):
        w_byte(cache_name, 0xFF)

    # Invalidate the plausible-type-mask cache so it recomputes.
    sa = sym_addr("wBossAIPlausibleTypeMaskSpecies")
    if sa is not None:
        write_byte_banked(pb, sa[1], 0, bank=sa[0])


def reset_caches_only(sess: DebugSession) -> None:
    """Between sub-measurements within one scenario: clear caches + plan."""
    syms = sess.symbols
    pb = sess.pyboy

    def w_byte(name: str, value: int) -> None:
        s = syms.get(name)
        if s is None:
            return
        write_byte_banked(pb, s.address, value, bank=s.bank)

    w_byte("wBossAIPlanId", BOSS_PLAN_NONE)
    w_byte("wBossAIPlanPhase", 0)
    for n in (
        "wBossAIHasKOMoveCache",
        "wBossAIPublicThreatCache",
        "wBossAIRevealedPriorityCache",
        "wBossAIPrimaryThreatCache",
        "wBossAIPublicEnemyFasterCache",
        "wBossAILookaheadDepthCache",
    ):
        w_byte(n, 0xFF)
    s = syms.get("wBossAIPlausibleTypeMaskSpecies")
    if s is not None:
        write_byte_banked(pb, s.address, 0, bank=s.bank)


def time_call(sess: DebugSession, fn_name: str, budget: int = 200_000) -> tuple[int, bool]:
    """Call a boss-AI function via PC injection and return (ticks, returned)."""
    syms_dict = {n: (sess.symbols.get(n).bank, sess.symbols.get(n).address)
                 for n in [fn_name]
                 if sess.symbols.get(n) is not None}
    if fn_name not in syms_dict:
        return (0, False)
    return _safe_call(sess.pyboy, syms_dict, fn_name, budget=budget)


def _safe_call(pyboy, syms_dict, name, *, budget=200_000):
    """Cycle-counting variant of safe_call.call_function_safe.

    Reports PyBoy `_cycles()` delta (T-cycles). Disables interrupts before
    the call to avoid VBlank/Timer firing mid-function and corrupting the
    return path through bank-switch helpers.
    """
    SENTINEL_ADDR = 0xFFFD
    rf = pyboy.register_file
    pyboy.memory[SENTINEL_ADDR] = 0x18
    pyboy.memory[SENTINEL_ADDR + 1] = 0xFE
    sp = int(rf.SP)
    new_sp = (sp - 2) & 0xFFFF
    pyboy.memory[new_sp] = SENTINEL_ADDR & 0xFF
    pyboy.memory[new_sp + 1] = (SENTINEL_ADDR >> 8) & 0xFF
    rf.SP = new_sp
    bank, addr = syms_dict[name]
    rf.PC = addr
    # Honor the function's bank.
    pyboy.memory[0x2000] = bank
    # And hROMBank shadow ($FF9F in this build).
    try:
        pyboy.memory[0xFF9F] = bank
    except Exception:
        pass
    # Disable all interrupts (IE = 0) so VBlank/Timer doesn't fire mid-call
    # and corrupt the stack through a bank-switch helper.
    saved_ie = int(pyboy.memory[0xFFFF])
    pyboy.memory[0xFFFF] = 0

    def cycles_now() -> int:
        c = getattr(pyboy, "_cycles", None)
        if callable(c):
            try:
                return int(c())
            except Exception:
                return 0
        return 0

    start_cycles = cycles_now()
    ticked = 0
    try:
        while ticked < budget:
            pyboy.tick(2, False, False)
            ticked += 2
            pc = int(rf.PC)
            if pc == SENTINEL_ADDR or pc == SENTINEL_ADDR + 2:
                return (cycles_now() - start_cycles, True)
        return (cycles_now() - start_cycles, False)
    finally:
        pyboy.memory[0xFFFF] = saved_ie


@dataclass
class ScenarioResult:
    name: str
    tier: int
    apply_move_model_cycles: list[int] = field(default_factory=list)
    select_move_cycles: list[int] = field(default_factory=list)
    total_cycles: list[int] = field(default_factory=list)
    returned: list[bool] = field(default_factory=list)


def summarize(values: list[int]) -> dict:
    if not values:
        return {"mean": 0, "median": 0, "max": 0, "min": 0, "count": 0}
    return {
        "mean": int(statistics.mean(values)),
        "median": int(statistics.median(values)),
        "max": max(values),
        "min": min(values),
        "count": len(values),
    }


def run_bench(rom_variant: str, samples: int, boot_frames: int) -> dict:
    results: list[ScenarioResult] = []
    with DebugSession.open(rom_variant) as sess:
        sess.tick(boot_frames)  # let init/RAM-clear finish
        for scen in SCENARIOS:
            r = ScenarioResult(name=scen.name, tier=scen.tier)
            install_scenario(sess, scen)
            for _ in range(samples):
                reset_caches_only(sess)
                a_cycles, a_ret = time_call(sess, "BossAI_ApplyMoveModel")
                s_cycles, s_ret = time_call(sess, "BossAI_SelectMove")
                r.apply_move_model_cycles.append(a_cycles)
                r.select_move_cycles.append(s_cycles)
                r.total_cycles.append(a_cycles + s_cycles)
                r.returned.append(bool(a_ret and s_ret))
            results.append(r)

    out: dict = {
        "rom": rom_variant,
        "samples_per_scenario": samples,
        "boot_frames": boot_frames,
        "scenarios": {},
    }
    for r in results:
        out["scenarios"][r.name] = {
            "tier": r.tier,
            "apply": summarize(r.apply_move_model_cycles),
            "select": summarize(r.select_move_cycles),
            "total": summarize(r.total_cycles),
            "all_returned": all(r.returned),
            "raw_total": r.total_cycles,
        }
    # Convenience: LATE-tier representative is "late_lead".
    late = out["scenarios"].get("late_lead", {})
    if late and late.get("total"):
        out["late_tier_total_mean"] = late["total"]["mean"]
    return out


PROFILED_HELPERS = (
    # Top entry points (sanity baseline; these wrap everything else)
    "BossAI_ApplyMoveModel",
    "BossAI_SelectMove",
    # Per-move scoring helpers
    "BossAI_CurrentEnemyMoveHasKOPressure",
    "BossAI_CurrentEnemyMovePressureScore",
    "BossAI_CurrentEnemyMoveScoredPower",
    "BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem",
    "BossAI_CheckTypeMatchupNoItem",
    "BossAI_ApplyEnemyKnownPressureModifiers",
    "BossAI_IsCurrentEnemySetupMove",
    "BossAI_PublicEnemyFaster",
    "BossAI_PublicEnemyFasterUncached",
    # Lookahead body + projection
    "BossAI_ApplyLookaheadToTopMoveCandidates",
    "BossAI_EvaluateActionLookahead",
    "BossAI_ApplyMultiTurnProjection",
    "BossAI_ShouldScout",
    "BossAI_GetTypeThreatSeverityVsEnemyMon",
    "BossAI_HasAnyKOMove",
    "BossAI_GetPrimaryThreatType",
    "BossAI_PredictPlayerSwitch",
    # Heavy data lookups (KO band / matchup tables)
    "BossAI_GetCurrentEnemyMatchupSlot",
    "BossAI_CurrentSlotOffensiveCoverageVsPlayer",
    "BossAI_CurrentSlotOffensiveCoverageVsType",
    "BossAI_ApplyKOBandOraclePressure",
    "BossAI_ApplyDamageDominanceBias",
    "BossAI_ConsultKOBandCalibration",
    # Bias dispatch (called once per move from .ScoreMove)
    "BossAI_ApplyPlanMoveBias",
    "BossAI_ApplyScoutMoveBias",
    "BossAI_ApplyRepeatPenalty",
    # Mask + plan setup
    "BossAI_ComputePlayerPlausibleTypeMask",
    "BossAI_SelectPlanIfNeeded",
    "BossAI_ResetTurnCaches",
    # HOME helpers that get called a lot
    "GetBaseData",
    "AddNTimes",
    "GetFarByte",
)


def cmd_profile(rom_variant: str, boot_frames: int, out_path: Path) -> int:
    """Run BossAI_ApplyMoveModel + BossAI_SelectMove once with per-helper
    cycle hooks installed. Report inclusive cycle aggregates + call counts
    so we can see which helper subtree actually dominates.
    """
    from collections import defaultdict
    from damage_debugger.disasm import walk_function, is_ret

    with DebugSession.open(rom_variant) as sess:
        sess.tick(boot_frames)
        pb = sess.pyboy
        syms = sess.symbols

        scen = next(s for s in SCENARIOS if s.name == "late_lead")
        install_scenario(sess, scen)

        agg: dict[str, int] = defaultdict(int)
        counts: dict[str, int] = defaultdict(int)
        stack: list[tuple[str, int]] = []

        def cycles_now() -> int:
            c = getattr(pb, "_cycles", None)
            if callable(c):
                try:
                    return int(c())
                except Exception:
                    return 0
            return 0

        def make_entry_cb(name: str):
            def cb(_ctx):
                stack.append((name, cycles_now()))
                counts[name] += 1
            return cb

        def make_exit_cb(name: str):
            def cb(_ctx):
                # Find the most recent matching entry; unwind any orphaned
                # entries above it (would mean a helper returned via a path
                # we didn't hook, e.g. a jump out).
                for i in range(len(stack) - 1, -1, -1):
                    if stack[i][0] == name:
                        delta = cycles_now() - stack[i][1]
                        agg[name] += delta
                        del stack[i:]
                        return
            return cb

        def read_byte(b: int, a: int) -> int:
            if a < 0x4000:
                return int(pb.memory[a])
            return int(pb.memory[b, a])

        installed: list[tuple[int, int]] = []
        skipped: list[str] = []
        ret_hook_failures: list[str] = []
        for name in PROFILED_HELPERS:
            sym = syms.get(name)
            if sym is None:
                skipped.append(name)
                continue
            bank, addr = sym.bank, sym.address
            sess.hook_register(bank, addr, make_entry_cb(name), None)
            installed.append((bank, addr))
            try:
                instrs = walk_function(read_byte, syms, name, max_bytes=0x800)
            except Exception as exc:
                ret_hook_failures.append(f"{name}: {exc}")
                continue
            for ins in instrs:
                if is_ret(ins.opcode):
                    sess.hook_register(ins.bank, ins.pc, make_exit_cb(name), None)
                    installed.append((ins.bank, ins.pc))

        reset_caches_only(sess)
        a_cycles, a_ret = time_call(sess, "BossAI_ApplyMoveModel")
        s_cycles, s_ret = time_call(sess, "BossAI_SelectMove")

        for bank, addr in installed:
            try:
                sess.hook_deregister(bank, addr)
            except Exception:
                pass

    rows = sorted(
        ((name, agg[name], counts[name]) for name in (set(agg) | set(counts))),
        key=lambda r: -r[1],
    )
    total = a_cycles + s_cycles
    result = {
        "scenario": scen.name,
        "rom": rom_variant,
        "total_apply_cycles": a_cycles,
        "total_select_cycles": s_cycles,
        "total_combined_cycles": total,
        "skipped_missing_sym": skipped,
        "rows": [
            {
                "helper": n,
                "inclusive_cycles": c,
                "pct_of_total": (c / total * 100.0) if total else 0.0,
                "call_count": k,
                "cycles_per_call": (c // k) if k > 0 else 0,
            }
            for n, c, k in rows
        ],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"\ntotal: apply={a_cycles:,} + select={s_cycles:,} = {total:,} cycles\n")
    print(f"{'helper':<48} {'cycles':>14} {'pct':>6} {'calls':>8} {'cy/call':>10}")
    print("-" * 92)
    for n, c, k in rows[:25]:
        pct = (c / total * 100.0) if total else 0.0
        cpc = (c // k) if k > 0 else 0
        print(f"{n:<48} {c:>14,} {pct:>5.1f}% {k:>8} {cpc:>10,}")
    if skipped:
        print(f"\nSkipped (missing symbol): {', '.join(skipped)}")
    return 0


def cmd_compare(baseline_path: Path, post_path: Path) -> int:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    post = json.loads(post_path.read_text(encoding="utf-8"))
    print(f"{'scenario':<28} {'baseline':>12} {'post':>12} {'delta':>10} {'pct':>8}")
    print("-" * 75)
    overall_baseline = 0
    overall_post = 0
    for name in baseline.get("scenarios", {}):
        b = baseline["scenarios"][name]["total"]["mean"]
        p = post.get("scenarios", {}).get(name, {}).get("total", {}).get("mean", 0)
        delta = b - p
        pct = (delta / b * 100.0) if b else 0.0
        print(f"{name:<28} {b:>12,} {p:>12,} {delta:>10,} {pct:>7.1f}%")
        overall_baseline += b
        overall_post += p
    delta = overall_baseline - overall_post
    pct = (delta / overall_baseline * 100.0) if overall_baseline else 0.0
    print("-" * 75)
    print(f"{'OVERALL':<28} {overall_baseline:>12,} {overall_post:>12,} {delta:>10,} {pct:>7.1f}%")
    # Also emit a focused LATE-tier reduction line for the v4 verifier.
    late_b = baseline.get("scenarios", {}).get("late_lead", {}).get("total", {}).get("mean", 0)
    late_p = post.get("scenarios", {}).get("late_lead", {}).get("total", {}).get("mean", 0)
    late_pct = ((late_b - late_p) / late_b * 100.0) if late_b else 0.0
    print(f"\nLATE-tier (late_lead) reduction: {late_pct:.1f}%")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--rom", default="pokegold", help="ROM variant (default: pokegold)")
    p.add_argument("--samples", type=int, default=5, help="samples per scenario")
    p.add_argument("--boot-frames", type=int, default=240)
    p.add_argument("--out", default=str(REPO_ROOT / "audit" / "boss_ai_perf" / "baseline.json"))
    p.add_argument("--compare", nargs=2, metavar=("BASELINE", "POST"),
                   help="compare two bench JSONs and print a diff table")
    p.add_argument("--profile", action="store_true",
                   help="profile per-helper inclusive cycles for the late_lead scenario")
    args = p.parse_args(argv)

    if args.compare:
        return cmd_compare(Path(args.compare[0]), Path(args.compare[1]))

    if args.profile:
        out = Path(args.out)
        if out.name == "baseline.json":
            out = out.parent / "profile.json"
        return cmd_profile(args.rom, args.boot_frames, out)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results = run_bench(args.rom, args.samples, args.boot_frames)
    # Add a late_tier_reduction_pct field iff out path is post_opt.json AND
    # baseline.json exists.
    baseline_path = out_path.parent / "baseline.json"
    if out_path.name == "post_opt.json" and baseline_path.exists() and baseline_path != out_path:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        b_late = baseline.get("scenarios", {}).get("late_lead", {}).get("total", {}).get("mean", 0)
        p_late = results.get("scenarios", {}).get("late_lead", {}).get("total", {}).get("mean", 0)
        results["late_tier_reduction_pct"] = (
            ((b_late - p_late) / b_late * 100.0) if b_late else 0.0
        )
    out_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    # Always print a short summary table.
    print(f"{'scenario':<28} {'apply':>10} {'select':>10} {'total':>10} {'ret':>5}")
    print("-" * 70)
    for name, s in results["scenarios"].items():
        print(f"{name:<28} {s['apply']['mean']:>10,} {s['select']['mean']:>10,} "
              f"{s['total']['mean']:>10,} {'OK' if s['all_returned'] else 'NO':>5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
