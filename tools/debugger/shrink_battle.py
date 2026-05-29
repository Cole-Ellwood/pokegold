from __future__ import annotations

import copy
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .input_log import resolve_path
from .provenance import display_path


SCHEMA_VERSION = 1
Predicate = Callable[[dict[str, Any]], bool]
PathPart = str | int

PARTY_KEYS = ("player_party", "enemy_party", "party", "opponent_party")
TOP_LEVEL_LIST_KEYS = (
    "player_party",
    "enemy_party",
    "party",
    "opponent_party",
    "moves",
    "modifiers",
    "conditions",
    "field_effects",
)


def shrink_battle_scenario_path(
    scenario_path: str | Path,
    *,
    predicate: Predicate,
    scenario_id: str = "",
    out_scenario: str = "",
    root: Path = ROOT,
) -> dict[str, Any]:
    path = resolve_path(str(scenario_path), root=root)
    if not path.exists():
        return empty_report(
            scenario_path=scenario_path,
            path=path,
            root=root,
            errors=[f"missing battle scenario: {scenario_path}"],
        )
    try:
        scenario = load_battle_scenario(path, scenario_id=scenario_id)
    except (json.JSONDecodeError, ValueError) as exc:
        return empty_report(
            scenario_path=scenario_path,
            path=path,
            root=root,
            errors=[f"{scenario_path}: {exc}"],
        )
    return shrink_battle_scenario(
        scenario,
        predicate=predicate,
        scenario_path=scenario_path,
        out_scenario=out_scenario,
        root=root,
    )


def shrink_battle_scenario(
    scenario: dict[str, Any],
    *,
    predicate: Predicate,
    scenario_path: str | Path = "",
    out_scenario: str = "",
    root: Path = ROOT,
) -> dict[str, Any]:
    original = copy.deepcopy(scenario)
    errors: list[str] = []
    if not predicate_passes(original, predicate=predicate, errors=errors):
        return {
            **base_report(scenario_path=scenario_path, path=None, root=root),
            "valid": False,
            "preserved": False,
            "errors": errors or ["baseline battle scenario does not reproduce the predicate"],
            "original_counts": battle_counts(original),
            "shrunk_counts": battle_counts(original),
            "removed_counts": removed_counts(original, original),
            "shrunk_scenario": original,
            "reduction_trace": [],
            "reduction_step_count": 0,
            "out_scenario": write_output(original, out_scenario=out_scenario, root=root),
        }

    current = copy.deepcopy(original)
    trace: list[dict[str, Any]] = []
    trial_counter = [0]
    for path in top_level_list_paths(current):
        current = shrink_list_at_path(current, path, predicate=predicate, trace=trace, trial_counter=trial_counter)
    for path in nested_move_paths(current):
        current = shrink_list_at_path(current, path, predicate=predicate, trace=trace, trial_counter=trial_counter)

    preserved = predicate_passes(current, predicate=predicate, errors=None)
    return {
        **base_report(scenario_path=scenario_path, path=None, root=root),
        "valid": preserved,
        "preserved": preserved,
        "errors": [] if preserved else ["shrunk battle scenario no longer reproduces the predicate"],
        "original_counts": battle_counts(original),
        "shrunk_counts": battle_counts(current),
        "removed_counts": removed_counts(original, current),
        "shrunk_scenario": current,
        "reduction_trace": trace,
        "reduction_step_count": len(trace),
        "out_scenario": write_output(current, out_scenario=out_scenario, root=root),
    }


def load_battle_scenario(path: Path, *, scenario_id: str = "") -> dict[str, Any]:
    if path.suffix.lower() == ".jsonl":
        records = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if isinstance(item, dict):
                records.append(item)
        if scenario_id:
            for record in records:
                if str(record.get("id") or record.get("scenario_id") or "") == scenario_id:
                    return record
            raise ValueError(f"scenario id not found: {scenario_id}")
        if records:
            return records[0]
        raise ValueError("scenario file contains no scenario records")
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        if scenario_id:
            for record in data:
                if isinstance(record, dict) and str(record.get("id") or record.get("scenario_id") or "") == scenario_id:
                    return record
            raise ValueError(f"scenario id not found: {scenario_id}")
        for record in data:
            if isinstance(record, dict):
                return record
    raise ValueError("scenario file does not contain a battle scenario object")


def top_level_list_paths(scenario: dict[str, Any]) -> list[tuple[PathPart, ...]]:
    return [(key,) for key in TOP_LEVEL_LIST_KEYS if isinstance(scenario.get(key), list)]


def nested_move_paths(scenario: dict[str, Any]) -> list[tuple[PathPart, ...]]:
    paths: list[tuple[PathPart, ...]] = []
    for party_key in PARTY_KEYS:
        party = scenario.get(party_key)
        if not isinstance(party, list):
            continue
        for index, mon in enumerate(party):
            if isinstance(mon, dict) and isinstance(mon.get("moves"), list):
                paths.append((party_key, index, "moves"))
    return paths


def shrink_list_at_path(
    scenario: dict[str, Any],
    path: tuple[PathPart, ...],
    *,
    predicate: Predicate,
    trace: list[dict[str, Any]],
    trial_counter: list[int],
) -> dict[str, Any]:
    items = value_at_path(scenario, path)
    if not isinstance(items, list) or len(items) <= min_items_for_path(path):
        return scenario
    current_items = tuple(copy.deepcopy(items))
    granularity = 2
    current = scenario
    while len(current_items) > min_items_for_path(path):
        chunk_size = max(1, (len(current_items) + granularity - 1) // granularity)
        changed = False
        for start in range(0, len(current_items), chunk_size):
            end = min(len(current_items), start + chunk_size)
            candidate_items = current_items[:start] + current_items[end:]
            if len(candidate_items) < min_items_for_path(path):
                continue
            trial_counter[0] += 1
            candidate = copy.deepcopy(current)
            set_path_value(candidate, path, list(copy.deepcopy(candidate_items)))
            accepted = predicate_passes(candidate, predicate=predicate, errors=None)
            trace.append(
                {
                    "trial": trial_counter[0],
                    "path": path_label(path),
                    "removed_start": start,
                    "removed_end": end,
                    "removed_count": end - start,
                    "candidate_count": len(candidate_items),
                    "accepted": accepted,
                }
            )
            if accepted:
                current = candidate
                current_items = candidate_items
                granularity = max(2, granularity - 1)
                changed = True
                break
        if changed:
            continue
        if granularity >= len(current_items):
            break
        granularity = min(len(current_items), granularity * 2)
    return current


def min_items_for_path(path: tuple[PathPart, ...]) -> int:
    if path and path[-1] in {"modifiers", "conditions", "field_effects"}:
        return 0
    return 1


def predicate_passes(
    scenario: dict[str, Any],
    *,
    predicate: Predicate,
    errors: list[str] | None,
) -> bool:
    try:
        return bool(predicate(copy.deepcopy(scenario)))
    except Exception as exc:
        if errors is not None:
            errors.append(f"predicate raised: {exc}")
        return False


def value_at_path(data: dict[str, Any], path: Sequence[PathPart]) -> Any:
    current: Any = data
    for part in path:
        if isinstance(part, int):
            if not isinstance(current, list) or part >= len(current):
                return None
            current = current[part]
        else:
            if not isinstance(current, dict):
                return None
            current = current.get(part)
    return current


def set_path_value(data: dict[str, Any], path: Sequence[PathPart], value: Any) -> None:
    current: Any = data
    for part in path[:-1]:
        current = current[part]
    current[path[-1]] = value


def battle_counts(scenario: dict[str, Any]) -> dict[str, Any]:
    party_counts = {
        key: len(scenario.get(key, []))
        for key in PARTY_KEYS
        if isinstance(scenario.get(key), list)
    }
    top_level_move_count = len(scenario.get("moves", [])) if isinstance(scenario.get("moves"), list) else 0
    nested_move_count = 0
    for path in nested_move_paths(scenario):
        moves = value_at_path(scenario, path)
        nested_move_count += len(moves) if isinstance(moves, list) else 0
    modifier_count = sum(
        len(scenario.get(key, []))
        for key in ("modifiers", "conditions", "field_effects")
        if isinstance(scenario.get(key), list)
    )
    return {
        "party_counts": party_counts,
        "pokemon_count": sum(party_counts.values()),
        "move_count": top_level_move_count + nested_move_count,
        "modifier_count": modifier_count,
    }


def removed_counts(original: dict[str, Any], shrunk: dict[str, Any]) -> dict[str, int]:
    original_counts = battle_counts(original)
    shrunk_counts = battle_counts(shrunk)
    return {
        "pokemon_count": max(0, int(original_counts["pokemon_count"]) - int(shrunk_counts["pokemon_count"])),
        "move_count": max(0, int(original_counts["move_count"]) - int(shrunk_counts["move_count"])),
        "modifier_count": max(0, int(original_counts["modifier_count"]) - int(shrunk_counts["modifier_count"])),
    }


def write_output(scenario: dict[str, Any], *, out_scenario: str, root: Path) -> dict[str, Any]:
    if not out_scenario:
        return {"path": "", "written": False}
    path = resolve_path(out_scenario, root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(scenario, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return {"path": display_path(path, root=root), "written": True}


def base_report(*, scenario_path: str | Path, path: Path | None, root: Path) -> dict[str, Any]:
    report = {
        "schema_version": SCHEMA_VERSION,
        "kind": "unified_debugger_shrink_battle",
        "scenario_path": str(scenario_path),
    }
    if path is not None:
        report["input_path"] = display_path(path, root=root)
    return report


def empty_report(
    *,
    scenario_path: str | Path,
    path: Path,
    root: Path,
    errors: list[str],
) -> dict[str, Any]:
    return {
        **base_report(scenario_path=scenario_path, path=path, root=root),
        "valid": False,
        "preserved": False,
        "errors": errors,
        "original_counts": battle_counts({}),
        "shrunk_counts": battle_counts({}),
        "removed_counts": removed_counts({}, {}),
        "shrunk_scenario": {},
        "reduction_trace": [],
        "reduction_step_count": 0,
        "out_scenario": {"path": "", "written": False},
    }


def path_label(path: Sequence[PathPart]) -> str:
    out = ""
    for part in path:
        if isinstance(part, int):
            out += f"[{part}]"
        elif out:
            out += f".{part}"
        else:
            out = part
    return out


def format_report(report: dict[str, Any]) -> str:
    original = report.get("original_counts", {}) if isinstance(report.get("original_counts"), dict) else {}
    shrunk = report.get("shrunk_counts", {}) if isinstance(report.get("shrunk_counts"), dict) else {}
    lines = [
        "Battle-scenario shrinker",
        (
            f"valid={str(report.get('valid')).lower()} "
            f"pokemon={original.get('pokemon_count', 0)}->{shrunk.get('pokemon_count', 0)} "
            f"moves={original.get('move_count', 0)}->{shrunk.get('move_count', 0)} "
            f"steps={report.get('reduction_step_count', 0)}"
        ),
    ]
    for error in report.get("errors", []):
        lines.append(f"error: {error}")
    out_scenario = report.get("out_scenario") if isinstance(report.get("out_scenario"), dict) else {}
    if out_scenario.get("written"):
        lines.append(f"shrunk_scenario={out_scenario.get('path', '')}")
    return "\n".join(lines)


def report_json(report: dict[str, Any]) -> str:
    return json.dumps(report, sort_keys=True)
