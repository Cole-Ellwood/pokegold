"""Run boss-AI decision-path fixtures against the real ROM."""
from __future__ import annotations

from tools.boss_ai_fixtures.cases import CASES, Case
from tools.boss_ai_fixtures.harness import (
    HAKI_SPENT_F, MOVES, move_name, open_harness,
)

SLOT_LABELS = ("slot1", "slot2", "slot3", "slot4")


class Skip(Exception):
    """Environment cannot run ROM-backed fixtures."""


def run_case(harness, case: Case) -> dict:
    harness.seed_battle(case.boss, case.player, tier=case.tier,
                        scores=case.scores, extra=case.extra)
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
    for sym in case.entry:
        returned = harness.invoke(sym) and returned

    out = harness.outcome()
    out["returned"] = returned
    out["haki_spent"] = bool(
        harness.rd("wBossAIRevealedMovesBitmapSpare", 1) & (1 << HAKI_SPENT_F)
    )
    return out


def check(case: Case, out: dict) -> list[str]:
    """Return a list of human-readable failures for one case."""
    fails: list[str] = []
    if not out["returned"]:
        fails.append("routine never returned (budget exhausted)")
        return fails

    exp = case.expect
    chosen = out["chosen_move"]

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
            verbose: bool = False) -> tuple[list[tuple[Case, dict, list[str]]], int]:
    """Run every case (optionally filtered by id/path substring)."""
    selected = [c for c in CASES
                if only is None or only in c.id or only in c.path]
    if not selected:
        raise Skip(f"no fixtures matched {only!r}")

    results: list[tuple[Case, dict, list[str]]] = []
    try:
        ctx = open_harness(rom)
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
                raise Skip(f"symbol missing from pokegold.sym: {exc}") from exc
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
