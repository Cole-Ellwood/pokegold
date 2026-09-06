"""Evaluator-owned replay checks for the confirmed Grass-regrowth development case.

The diagnostic runner must not import this module or receive the fixed fixture.
These are ground-truth checks for one historical failure, not a diagnostic rule
or an assertion that the general oracle is complete.
"""
from __future__ import annotations

import json
import argparse
from pathlib import Path
from typing import Any

from tools.audit.root_cause_fixtures import verify_export
from tools.audit.root_cause_evaluator import BASIS_FIELDS, score_diagnosis
from tools.debugger.report_envelope import sha256_file
from tools.debugger.runtime_experiment import run_runtime_experiment


CALL = "HandleTypePassiveRegrowth_Far.do_it+14"
POINTER = "TypePassive_GetUserHPPointers_Far"
CONSUMER = "HandleTypePassiveRegrowth_Far.heal+6"
SHIFT = "HandleTypePassiveRegrowth_Far.shift"
POINTS = (CALL, POINTER, POINTER + "+3", POINTER + "+6", "GetMaxHP", CONSUMER, SHIFT, "SwitchTurnCore")
INVARIANT = {"at": CONSUMER, "register": "D", "expected": 2}
REGRESSION = {
    "watch": "wBattleMonHP", "initial": "002C", "expected": "002E",
    "at": SHIFT, "register": "D", "expected_register": 2,
}
CAUSE = {
    "source_file": "engine/battle/type_passive_damage_mods.asm",
    "source_symbol": "HandleTypePassiveRegrowth_Far.do_it", "source_line": 1256,
}


def read_artifact(root: Path, name: str) -> dict:
    if not isinstance(name, str) or not name:
        raise ValueError("evidence artifact path is missing")
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("evidence artifact is outside the submission directory")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("evidence artifact must be an object")
    return data


def event_at(report: dict, target: str) -> dict:
    return next(event for event in report["events"] if target in event["targets"])


def hp(report: dict) -> str:
    return report["final"].get("watch_values", {}).get("wBattleMonHP", "")


def verify_grass_diagnosis(
    report: dict,
    *,
    fixtures: dict,
    artifact_root: Path,
) -> dict[str, Any]:
    """Reexecute the claimed chain, intervention, negative control and regression.

    Fixtures/identity come from the evaluator. Read-only recipes may choose the
    one-frame minimized window and a preconditioned intervention; no command from
    the report is executed. Return actual experiment reports with the check bits
    so the result is reviewable. Do not reuse submission-provided verdicts.
    """
    for side in ("input", "control"):
        fixture = fixtures[side]
        root = Path(fixture["root"])
        if not verify_export(root, fixture):
            raise ValueError(f"stale {side} source export")
        for name, expected in (
            ("pokegold.gbc", fixture["rom_sha256"]),
            ("pokegold.sym", fixture["symbols_sha256"]),
            ("recording/initial.state", fixture["state_basis"]["initial_state_sha256"]),
            ("recording/inputs.json", fixture["state_basis"]["input_log_sha256"]),
        ):
            if sha256_file(root / name) != expected:
                raise ValueError(f"stale {side} artifact: {name}")

    claim = next(atom for atom in report["evidence_atoms"]
                 if atom.get("claim_type") == "diagnosis.root_cause")
    detail = claim["detail"]
    if detail["invariant"] != INVARIANT:
        raise ValueError("claim does not identify the type-contribution invariant")
    recipe = read_artifact(artifact_root, detail["reproducer"])
    regression = read_artifact(artifact_root, detail["regression"])
    if recipe != {"state": "recording/initial.state", "frames": 1, "buttons": []}:
        raise ValueError("reproducer is not the minimal recorded one-frame trigger")
    if regression != REGRESSION:
        raise ValueError("regression must test both the heal and its type-contribution invariant")

    def run(side, *, frames, observe, interventions):
        result = run_runtime_experiment(
            rom_path="pokegold.gbc", symbols_path="pokegold.sym",
            save_state=recipe["state"], frames=frames, observe=observe,
            watch_symbols=("wBattleMonHP",), interventions=interventions,
            root=Path(fixtures[side]["root"]),
        )
        if result.get("backend_sha256") != fixtures[side]["backend_sha256"]:
            raise ValueError(f"{side} replay backend differs from its fixture")
        return result

    baseline = run("input", frames=30, observe=POINTS, interventions=())
    if not baseline["valid"]:
        raise ValueError(f"baseline did not replay: {baseline['errors']}")

    # Match submitted event references to fresh execution, preserving order and
    # requiring the entire observed clobber/use/outcome chain. A copied marker or
    # an event from the symptom-forcing trial cannot stand in for baseline facts.
    required = {
        index for index, event in enumerate(baseline["events"])
        if "SwitchTurnCore" not in event["targets"] or event["watch_values"]["wBattleMonHP"] == "002D"
    }
    matched = set()
    next_index = 0
    trace_cache = {}
    chain_valid = True
    for reference in detail["causal_chain"]:
        name = reference["trace"]
        if name not in trace_cache:
            trace_cache[name] = read_artifact(artifact_root, name)
        trace = trace_cache[name]
        for key in ("rom_sha256", "symbols_sha256", "initial_state_sha256", "backend_sha256"):
            if trace.get(key) != baseline[key]:
                raise ValueError(f"stale causal trace {key}")
        seq = reference["seq"]
        if type(seq) is not int or seq < 0:
            raise ValueError("causal trace sequence must be a nonnegative integer")
        cited = [event for event in trace["events"] if event["seq"] == seq]
        if len(cited) != 1:
            raise ValueError("causal trace sequence is missing or duplicated")
        keys = ("bank", "pc", "registers", "after_registers", "watch_values")
        found = next((i for i in range(next_index, len(baseline["events"]))
                      if all(cited[0].get(key) == baseline["events"][i].get(key) for key in keys)), None)
        if found is None:
            chain_valid = False
            break
        matched.add(found)
        next_index = found + 1
    chain_valid = chain_valid and required <= matched

    restored = run("input", frames=30, observe=POINTS, interventions=(detail["intervention"],))
    unrelated = run("input", frames=30, observe=POINTS, interventions=(
        {"at": CONSUMER, "register": "E", "expected": 15, "value": 0},
    ))
    minimal = run("input", frames=recipe["frames"], observe=(SHIFT,), interventions=())
    control = run("control", frames=recipe["frames"], observe=(SHIFT,), interventions=())

    def register(result, target, name, *, after=False):
        field = "after_registers" if after else "registers"
        return event_at(result, target)[field].get(f"register_{name.lower()}")

    failure = (
        hp(baseline) == "002D"
        and register(baseline, CALL, "D") == "02"
        and register(baseline, POINTER + "+3", "D") == "02"
        and register(baseline, POINTER + "+6", "D") == "CB"
        and register(baseline, "GetMaxHP", "D") == "CB"
        and register(baseline, CONSUMER, "D") == "CB"
        and register(baseline, SHIFT, "A") == "06"
    )
    alternatives = (
        restored["valid"] and unrelated["valid"]
        and hp(restored) == "002E" and register(restored, CONSUMER, "D", after=True) == "02"
        and register(restored, SHIFT, "D") == "02"
        and hp(unrelated) == "002D" and register(unrelated, CONSUMER, "D", after=True) == "CB"
        # GetMaxHP receives the already-bad value and returns it unchanged.
        and register(baseline, "GetMaxHP", "D") == register(baseline, CONSUMER, "D")
    )
    broken_regression = minimal["valid"] and hp(minimal) == "002D" and register(minimal, SHIFT, "D") == "CB"
    fixed_regression = control["valid"] and hp(control) == "002E" and register(control, SHIFT, "D") == "02"
    return {
        "failure_reproduced": failure,
        "causal_chain_replayed": failure and chain_valid,
        "alternatives_rejected": bool(alternatives),
        "minimized_reproducer_replayed": bool(broken_regression and minimal["initial"]["watch_values"]["wBattleMonHP"] == "002C"),
        "regression_failed_broken": bool(broken_regression),
        "regression_passed_control": bool(fixed_regression),
        "evidence": {"baseline": baseline, "intervention": restored, "negative_control": unrelated,
                     "minimal_broken": minimal, "minimal_fixed": control},
        "known_limits": ["One known development cause; one-frame input minimization, not minimization of all materialized RAM."],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixtures", type=Path, help="Evaluator-owned fixture identity JSON")
    parser.add_argument("submission", type=Path, help="Diagnosis JSON; evidence paths are relative to its directory")
    args = parser.parse_args()
    fixtures = json.loads(args.fixtures.read_text(encoding="utf-8"))
    report = json.loads(args.submission.read_text(encoding="utf-8"))
    verification = {}

    def replay(submission):
        verification.update(verify_grass_diagnosis(
            submission, fixtures=fixtures, artifact_root=args.submission.parent,
        ))
        return verification

    score = score_diagnosis(
        report, expected_basis={key: fixtures["input"][key] for key in BASIS_FIELDS},
        accepted_causes=[CAUSE], verify_replay=replay,
        assistance_events=["Evaluator author supplied known development cause and intervention"],
    )
    print(json.dumps({"score": score, "verification": verification}, indent=2))
    return 0 if score["solved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
