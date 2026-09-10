"""Run boss-AI decision-path fixtures against the real ROM."""
from __future__ import annotations

from tools.boss_ai_fixtures.cases import CASES, Case
from tools.boss_ai_fixtures.harness import (
    HAKI_SPENT_F, MOVES, move_name, open_harness,
)

SLOT_LABELS = ("slot1", "slot2", "slot3", "slot4")


class Skip(Exception):
    """Environment cannot run ROM-backed fixtures."""


class FixtureError(Exception):
    """Selected tests do not match the supplied build or required symbols."""


def run_case(harness, case: Case) -> dict:
    harness.invoke("BossAI_ResetTurnCaches")
    harness.seed_battle(case.boss, case.player, tier=case.tier,
                        scores=case.scores, extra=case.extra)
    if case.damage_check is not None:
        from tools.boss_ai_fixtures.damage import run_damage_check
        return run_damage_check(harness, case)
    if case.action_check is not None:
        from tools.boss_ai_fixtures.action import run_action_check
        return run_action_check(harness, case)
    if case.exchange_check is not None:
        from tools.boss_ai_fixtures.action import run_exchange_check
        return run_exchange_check(harness, case)
    if case.candidate_check is not None:
        from tools.boss_ai_fixtures.action import run_candidate_check
        return run_candidate_check(harness, case)
    if case.reply_check is not None:
        from tools.boss_ai_fixtures.replies import run_reply_check
        return run_reply_check(harness, case)
    if case.joint_check is not None:
        from tools.boss_ai_fixtures.joint import run_joint_check
        return run_joint_check(harness, case)
    if case.prescore:
        # Stand in for the ordinary AIChooseMove pass having already scored this
        # matchup, so the fixture isolates the entry point under test.
        harness.invoke("BossAI_ApplyMoveModel")
        # re-apply extras the model may have disturbed
        for key, val in case.extra.items():
            if isinstance(key, tuple):
                harness.wr(key[0], val, key[1])
            else:
                harness.wr(key, val)

    returned = True
    reference = None
    if case.expect.get("exhaustive_lookahead"):
        # Evaluate each move independently from the same initial scores.
        # Compare with the production driver, including unattractive late slots.
        reference = list(case.scores)
        for slot, move in enumerate(case.boss.moves):
            if reference[slot] >= 80:
                continue
            harness.invoke("BossAI_ResetTurnCaches")
            harness.seed_battle(case.boss, case.player, tier=case.tier,
                                scores=case.scores, extra=case.extra)
            harness.invoke("BossAI_EvaluateActionLookahead", {"A": move})
            delta = harness.outcome()["a"]
            delta = delta - 256 if delta >= 128 else delta
            reference[slot] = max(1, min(79, reference[slot] + delta))
        harness.invoke("BossAI_ResetTurnCaches")
        harness.seed_battle(case.boss, case.player, tier=case.tier,
                            scores=case.scores, extra=case.extra)
    decisions = []
    # Call counters: "random_calls" pins the RNG budget; "calls" pins how many
    # times each named routine ran (a routing fixture, e.g. "the KO-band oracle
    # is consulted once for a super-effective coverage move and never for a
    # resisted one"). Both count entries into the symbol's address.
    watched = list(case.expect.get("calls", {}))
    if "random_calls" in case.expect:
        watched.append("Random")
    counts = {name: 0 for name in watched}
    hooked = []
    for name in watched:
        sym = harness.syms[name]

        def _bump(_, name=name):
            counts[name] += 1
        harness.pb.hook_register(sym.bank, sym.address, _bump, None)
        hooked.append(sym)
    # Bypass only explicitly named UI calls, returning through their real stack.
    # A stop hook parks at HRAM before state can be changed by later animation.
    for name in case.skip_calls:
        sym = harness.syms[name]
        def _return(_):
            rf, mem = harness.pb.register_file, harness.pb.memory
            sp = int(rf.SP)
            rf.PC = mem[sp] | (mem[(sp + 1) & 0xffff] << 8)
            rf.SP = (sp + 2) & 0xffff
        harness.pb.hook_register(sym.bank, sym.address, _return, None)
        hooked.append(sym)
    if case.force_random is not None:
        # Pin the RNG: Random returns this byte, so a roll-gated branch is testable.
        sym = harness.syms["Random"]

        def _fixed(_):
            rf, mem = harness.pb.register_file, harness.pb.memory
            rf.A = case.force_random
            sp = int(rf.SP)
            rf.PC = mem[sp] | (mem[(sp + 1) & 0xffff] << 8)
            rf.SP = (sp + 2) & 0xffff
        harness.pb.hook_register(sym.bank, sym.address, _fixed, None)
        hooked.append(sym)
    if case.stop_at:
        sym = harness.syms[case.stop_at]
        def _stop(_):
            harness.pb.register_file.PC = 0xfffd
        harness.pb.hook_register(sym.bank, sym.address, _stop, None)
        hooked.append(sym)
    try:
        registers = {
            key: harness.syms[value[0]].address + value[1]
            if isinstance(value, tuple) else value
            for key, value in case.registers.items()
        }
        for sym in case.entry:
            returned = harness.invoke(sym, registers) and returned
            decisions.append(harness.outcome()["carry"])
    finally:
        for sym in hooked:
            harness.pb.hook_deregister(sym.bank, sym.address)

    out = harness.outcome()
    out["returned"] = returned
    out["reference_scores"] = reference
    out["decisions"] = decisions
    out["random_calls"] = counts.get("Random", 0)
    out["calls"] = {name: counts[name] for name in case.expect.get("calls", {})}
    out["memory"] = {
        key: harness.rd(key[0], key[1]) if isinstance(key, tuple) else harness.rd(key)
        for key in case.expect.get("memory", {})
    }
    out["haki_spent"] = bool(
        harness.rd("wBossAIRevealedMovesBitmapSpare", 1) & (1 << HAKI_SPENT_F)
    )
    return out


def check(case: Case, out: dict) -> list[str]:
    """Return a list of human-readable failures for one case."""
    fails: list[str] = []
    fails.extend(out.get("damage_errors", []))
    if not out["returned"]:
        fails.append("routine never returned (budget exhausted)")
        return fails

    exp = case.expect
    chosen = out["chosen_move"]
    if exp.get("exhaustive_lookahead") and out["scores"] != out["reference_scores"]:
        fails.append(f"scores {out['scores']} != independent evaluation {out['reference_scores']}")

    if "a" in exp and out["a"] != exp["a"]:
        fails.append(f"A={out['a']}, expected {exp['a']}")
    for key in ("bc", "random_calls"):
        if key in exp and out[key] != exp[key]:
            fails.append(f"{key}={out[key]}, expected {exp[key]}")
    for name, want in exp.get("calls", {}).items():
        if out["calls"][name] != want:
            fails.append(f"{name} ran {out['calls'][name]} time(s), expected {want}")
    if exp.get("consistent_decisions") and len(set(out["decisions"])) != 1:
        fails.append(f"inconsistent decisions: {out['decisions']}")
    for key, want in exp.get("memory", {}).items():
        if out["memory"][key] != want:
            fails.append(f"{key}={out['memory'][key]}, expected {want}")

    if "chosen_move" in exp:
        want = MOVES[exp["chosen_move"]]
        if chosen != want:
            fails.append(
                f"chose {move_name(chosen)}, expected {exp['chosen_move']}")

    for bad in exp.get("chosen_move_not", []):
        if chosen == MOVES[bad]:
            fails.append(
                f"chose {bad}, which this fixture forbids "
                f"({'defender is immune' if bad == 'SHADOW_BALL' else 'wrong branch'})")

    if "carry" in exp and out["carry"] != exp["carry"]:
        fails.append(
            f"carry={out['carry']}, expected {exp['carry']} "
            f"({'predicate said yes when it should say no' if out['carry'] else 'predicate said no when it should say yes'})")

    if "choice_ready" in exp and out["choice_ready"] != exp["choice_ready"]:
        fails.append(
            f"choice_ready={out['choice_ready']}, expected {exp['choice_ready']}")

    if "haki_spent" in exp and out["haki_spent"] != exp["haki_spent"]:
        fails.append(
            f"haki_spent={out['haki_spent']}, expected {exp['haki_spent']} "
            f"({'Haki fired when it should not have' if out['haki_spent'] else 'Haki did not fire'})")

    for slot, floor in exp.get("score_ge", []):
        got = out["scores"][slot]
        if got < floor:
            fails.append(
                f"{SLOT_LABELS[slot]} score {got} < {floor} "
                "(expected it to be blocked/discouraged)")

    for a, b in exp.get("score_lt", []):
        sa, sb = out["scores"][a], out["scores"][b]
        if not sa < sb:
            fails.append(
                f"{SLOT_LABELS[a]} score {sa} is not below {SLOT_LABELS[b]} "
                f"score {sb} (expected it to be preferred)")

    return fails


def run_all(rom: str = "pokegold", only: str | None = None,
            verbose: bool = False, suite: str = "all") -> tuple[list[tuple[Case, dict, list[str]]], int]:
    """Run every case (optionally filtered by id/path substring)."""
    if suite not in ("all", "production", "reference"):
        raise ValueError(f"unknown fixture suite {suite!r}")
    selected = [c for c in CASES
                if (only is None or only in c.id or only in c.path)
                and (suite == "all" or c.requires_reference == (suite == "reference"))]
    if not selected:
        raise FixtureError(f"no {suite} fixtures matched {only!r}")

    results: list[tuple[Case, dict, list[str]]] = []
    try:
        with open_harness(rom) as harness:
            if any(c.requires_reference for c in selected) and not harness.has("BossAI_ComparePublicActions"):
                raise FixtureError(
                    f"{rom} does not contain the offline AI reference evaluator. "
                    "Use --suite production for game-build tests, or build "
                    "gold_ai_reference/silver_ai_reference and select that ROM with --rom.")
    except FixtureError:
        raise
    except Exception as exc:  # pragma: no cover - environment guard
        raise Skip(f"debugger harness unavailable: {exc}") from exc

    # One session per case: these routines end in text boxes and UI paths that
    # leave synthetic state behind, and a reused session lets one fixture
    # contaminate the next.
    for case in selected:
        try:
            ctx2 = open_harness(rom)
        except Exception as exc:
            raise Skip(f"pokegold ROM/symbols unavailable: {exc}") from exc
        with ctx2 as harness:
            try:
                out = run_case(harness, case)
            except KeyError as exc:
                raise FixtureError(f"{case.id}: required symbol missing from {rom}.sym: {exc}") from exc
            fails = check(case, out)
        results.append((case, out, fails))
    return results, len(selected)


def report(results, verbose: bool = False) -> int:
    idw = max(len(c.id) for c, _, _ in results)
    pathw = max(len(c.path) for c, _, _ in results)
    print(f"{'fixture'.ljust(idw)}  {'path'.ljust(pathw)}  chose         status")
    print("-" * (idw + pathw + 30))
    failed = 0
    for case, out, fails in results:
        status = "OK" if not fails else "FAIL"
        if fails:
            failed += 1
        print(f"{case.id.ljust(idw)}  {case.path.ljust(pathw)}  "
              f"{move_name(out['chosen_move'])[:12]:12s}  {status}")
        if verbose:
            print(f"    pins   : {case.pins}")
            print(f"    boss   : {case.boss.describe()}")
            print(f"    player : {case.player.describe()}")
            print(f"    scores : {out['scores']}  haki_spent={out['haki_spent']}"
                  f"  choice_ready={out['choice_ready']}")
        for f in fails:
            print(f"    !! {f}")
            if not verbose:
                print(f"       pins: {case.pins}")
    print()
    if failed:
        print(f"FAIL: {failed} of {len(results)} boss-AI decision-path fixtures broke.")
        print("Source: engine/battle/ai/  (see each fixture's `pins` note)")
        return 1
    print(f"PASS: all {len(results)} boss-AI decision-path fixtures hold")
    paths = sorted({c.path for c, _, _ in results})
    print(f"      paths covered: {', '.join(paths)}")
    return 0
