from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError

from .rom_scenarios import (
    BLOCKED_SCORE,
    evaluate_batch,
    load_scenario_batch,
    score_moves,
    select_move,
)
from .trace_replay import (
    parse_int_list,
    parse_trace_file,
    replay_trace_paths,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INVARIANTS_JSON_PATH = (
    ROOT / "audit" / "boss_ai_debugger" / "candidate_invariants.json"
)
DEFAULT_INVARIANTS_MD_PATH = (
    ROOT / "audit" / "boss_ai_debugger" / "candidate_invariants.md"
)


def mine_invariants_from_paths(
    *,
    scenarios_path: Path | None = None,
    runs_dir: Path | None = None,
    trace_dir: Path | None = None,
    trace_glob: str = "*_live.txt",
) -> dict[str, Any]:
    scenarios = load_scenario_batch(scenarios_path) if scenarios_path is not None else []
    traces = []
    if trace_dir is not None:
        if not trace_dir.exists():
            raise PreferenceDataError(f"trace dir not found: {trace_dir}")
        traces = sorted(trace_dir.glob(trace_glob))
    if runs_dir is not None and not runs_dir.exists():
        raise PreferenceDataError(f"runs dir not found: {runs_dir}")
    return mine_invariants(
        scenarios=scenarios,
        runs_dir=runs_dir,
        trace_paths=traces,
    )


def mine_invariants(
    *,
    scenarios: list[dict[str, Any]] | None = None,
    runs_dir: Path | None = None,
    trace_paths: list[Path] | None = None,
) -> dict[str, Any]:
    scenario_rows = scenarios or []
    trace_rows = trace_paths or []
    run_rows = list_run_dirs(runs_dir) if runs_dir is not None else []
    candidates = []
    candidates.extend(mine_scenario_invariants(scenario_rows))
    candidates.extend(mine_trace_invariants(trace_rows))
    candidates.extend(mine_run_store_invariants(run_rows))

    return {
        "schema_version": 1,
        "status": "candidate",
        "scenario_count": len(scenario_rows),
        "trace_file_count": len(trace_rows),
        "run_count": len(run_rows),
        "candidate_count": len(candidates),
        "violation_count": sum(int(item["violation_count"]) for item in candidates),
        "candidates": candidates,
        "known_limits": [
            "Current traces expose selector bytes, not full scoring rule events.",
            "Candidate invariants are hypotheses until promoted to a dedicated audit.",
        ],
    }


def mine_scenario_invariants(scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    direction = invariant(
        "scenario.score_delta_direction",
        "scenario",
        "Score deltas keep the ROM direction: negative encourages, positive discourages.",
    )
    bounds = invariant(
        "scenario.selectable_score_bounds",
        "scenario",
        "Selectable scores stay in 1..79, and blocked scores stay at 80 or above.",
    )
    blocked_zero = invariant(
        "scenario.blocked_probability_zero",
        "scenario",
        "Actions with final score 80 or above have zero selector probability.",
    )
    selector_surface = invariant(
        "scenario.selector_probability_surface",
        "scenario",
        "The selector gives nonzero probability only to the best and first second-best actions.",
    )
    pass_floor = invariant(
        "scenario.pass_expected_probability_floor",
        "scenario",
        "Pass verdicts with expected best ids satisfy the configured probability floor.",
    )
    pass_no_catastrophe = invariant(
        "scenario.pass_has_no_catastrophic_roll",
        "scenario",
        "Passing scenarios do not roll catastrophic actions.",
    )

    if not scenarios:
        return [
            direction,
            bounds,
            blocked_zero,
            selector_surface,
            pass_floor,
            pass_no_catastrophe,
        ]

    batch = evaluate_batch(scenarios)
    verdict_by_id = {item["scenario_id"]: item for item in batch["verdicts"]}
    for scenario in scenarios:
        scenario_id = str(scenario.get("id", "unnamed"))
        try:
            scored = score_moves(scenario)
            result = select_move(scenario)
        except Exception as exc:
            add_violation(bounds, scenario_id, f"scenario scoring failed: {exc}")
            continue

        for move in scored:
            for event in move.events:
                if event.delta is None:
                    continue
                add_support(direction, scenario_id)
                if event.delta < 0 and event.after > event.before:
                    add_violation(
                        direction,
                        scenario_id,
                        f"{move.action_id}:{event.rule} negative delta raised score",
                    )
                if event.delta > 0 and event.after < event.before:
                    add_violation(
                        direction,
                        scenario_id,
                        f"{move.action_id}:{event.rule} positive delta lowered score",
                    )
                if event.delta == 0 and event.after != event.before:
                    add_violation(
                        direction,
                        scenario_id,
                        f"{move.action_id}:{event.rule} zero delta changed score",
                    )

            add_support(bounds, scenario_id)
            if move.final_score < BLOCKED_SCORE:
                if not 1 <= move.final_score <= 79:
                    add_violation(
                        bounds,
                        scenario_id,
                        f"{move.action_id} selectable score {move.final_score} is outside 1..79",
                    )
            elif move.final_score < 80:
                add_violation(
                    bounds,
                    scenario_id,
                    f"{move.action_id} blocked score {move.final_score} is below 80",
                )

        probabilities = result.get("probabilities", {})
        for move in result.get("moves", []):
            if int(move["final_score"]) < BLOCKED_SCORE:
                continue
            add_support(blocked_zero, scenario_id)
            action_id = str(move["action_id"])
            if float(probabilities.get(action_id, 0.0)) != 0.0:
                add_violation(
                    blocked_zero,
                    scenario_id,
                    f"{action_id} is blocked but has probability {probabilities[action_id]}",
                )

        if result.get("ready"):
            add_support(selector_surface, scenario_id)
            allowed = {
                str(result.get("best_action_id")),
                str(result.get("second_action_id")),
            }
            rolled = {
                str(action_id)
                for action_id, probability in probabilities.items()
                if float(probability) > 0.0
            }
            extra = sorted(rolled - allowed)
            if extra:
                add_violation(
                    selector_surface,
                    scenario_id,
                    "unexpected nonzero probability actions: " + ",".join(extra),
                )

        verdict = verdict_by_id.get(scenario_id)
        if not verdict or verdict.get("verdict") != "pass":
            continue
        add_support(pass_floor, scenario_id)
        add_support(pass_no_catastrophe, scenario_id)
        if verdict.get("rolled_catastrophic_action_ids"):
            add_violation(
                pass_no_catastrophe,
                scenario_id,
                "pass verdict still rolls catastrophic action",
            )
        expectation = scenario.get("expectation", {})
        floor = float(expectation.get("min_best_probability", 0.5))
        if float(verdict.get("rom_best_probability", 0.0)) < floor:
            add_violation(
                pass_floor,
                scenario_id,
                f"ROM best probability below floor {floor}",
            )

    return [
        direction,
        bounds,
        blocked_zero,
        selector_surface,
        pass_floor,
        pass_no_catastrophe,
    ]


def mine_trace_invariants(paths: list[Path]) -> list[dict[str, Any]]:
    byte_shape = invariant(
        "trace.exact_selector_byte_shape",
        "trace",
        "Exact trace captures carry four move ids and four move score bytes.",
    )
    chosen_possible = invariant(
        "trace.chosen_slot_is_possible",
        "trace",
        "Exact matched captures choose a slot or move with nonzero selector probability.",
    )
    blocked_zero = invariant(
        "trace.score_80_probability_zero",
        "trace",
        "Trace selector slots with score 80 or above have zero probability.",
    )
    possible_slots = invariant(
        "trace.possible_slots_limited_to_best_second",
        "trace",
        "Exact selector replay exposes at most two possible slots.",
    )

    if not paths:
        return [byte_shape, chosen_possible, blocked_zero, possible_slots]

    for path in paths:
        for index, fields in enumerate(parse_trace_file(path), start=1):
            if not all(key in fields for key in ("tier", "move_ids", "move_scores")):
                continue
            capture_id = f"{path.stem}#{index}"
            add_support(byte_shape, capture_id)
            move_ids = parse_int_list(fields.get("move_ids", ""))
            scores = parse_int_list(fields.get("move_scores", ""))
            if len(move_ids) != 4 or len(scores) != 4:
                add_violation(
                    byte_shape,
                    capture_id,
                    f"move_ids={len(move_ids)} move_scores={len(scores)}",
                )

    report = replay_trace_paths(paths)
    for item in report["verdicts"]:
        if item.get("mode") != "exact":
            continue
        capture_id = str(item["capture_id"])
        add_support(chosen_possible, capture_id)
        if not item.get("match"):
            add_violation(chosen_possible, capture_id, str(item.get("reason", "")))
        selector = item.get("selector", {})
        slots = selector.get("slots", [])
        probabilities = selector.get("probabilities_by_slot", {})
        for slot in slots:
            if int(slot.get("score", 0)) < BLOCKED_SCORE:
                continue
            add_support(blocked_zero, capture_id)
            probability = float(
                probabilities.get(
                    int(slot["slot_index"]),
                    probabilities.get(str(slot["slot_index"]), 0.0),
                )
            )
            if probability != 0.0:
                add_violation(
                    blocked_zero,
                    capture_id,
                    f"slot {slot['slot_index']} score {slot['score']} probability {probability}",
                )
        if selector.get("ready"):
            add_support(possible_slots, capture_id)
            slot_count = len(selector.get("possible_slot_indices", []))
            if slot_count > 2:
                add_violation(
                    possible_slots,
                    capture_id,
                    f"possible slot count is {slot_count}",
                )

    return [byte_shape, chosen_possible, blocked_zero, possible_slots]


def mine_run_store_invariants(run_dirs: list[Path]) -> list[dict[str, Any]]:
    hashes_match = invariant(
        "run_store.artifact_hashes_match",
        "run_store",
        "Run metadata artifact hashes match the written artifact files.",
    )
    batch_summary = invariant(
        "run_store.batch_summary_matches_report",
        "run_store",
        "Run metadata batch summary agrees with batch_report.json.",
    )
    queue_count = invariant(
        "run_store.review_queue_matches_batch",
        "run_store",
        "Review queue input count agrees with batch reviewable count.",
    )

    for run_dir in run_dirs:
        metadata_path = run_dir / "metadata.json"
        if not metadata_path.exists():
            continue
        run_id = run_dir.name
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            add_violation(hashes_match, run_id, f"invalid metadata json: {exc}")
            continue

        artifacts = metadata.get("artifacts", {})
        artifact_hashes = metadata.get("artifact_hashes", {})
        for name, expected_hash in artifact_hashes.items():
            add_support(hashes_match, f"{run_id}:{name}")
            artifact_path = resolve_run_artifact(run_dir, artifacts.get(name))
            if artifact_path is None or not artifact_path.exists():
                add_violation(hashes_match, f"{run_id}:{name}", "artifact missing")
                continue
            actual_hash = sha256_file(artifact_path)
            if actual_hash != str(expected_hash).upper():
                add_violation(
                    hashes_match,
                    f"{run_id}:{name}",
                    f"expected {expected_hash}, found {actual_hash}",
                )

        batch_path = resolve_run_artifact(run_dir, artifacts.get("batch_report"))
        queue_path = resolve_run_artifact(run_dir, artifacts.get("review_queue"))
        if batch_path is None or queue_path is None:
            continue
        if not batch_path.exists() or not queue_path.exists():
            continue
        batch = json.loads(batch_path.read_text(encoding="utf-8"))
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
        add_support(batch_summary, run_id)
        summary = metadata.get("batch_summary", {})
        for key in ("scenario_count", "reviewable_count", "verdict_counts"):
            if summary.get(key) != batch.get(key):
                add_violation(
                    batch_summary,
                    run_id,
                    f"{key} metadata={summary.get(key)!r} batch={batch.get(key)!r}",
                )
        add_support(queue_count, run_id)
        if queue.get("input_reviewable_count") != batch.get("reviewable_count"):
            add_violation(
                queue_count,
                run_id,
                (
                    "queue input_reviewable_count="
                    f"{queue.get('input_reviewable_count')} batch reviewable_count="
                    f"{batch.get('reviewable_count')}"
                ),
            )

    return [hashes_match, batch_summary, queue_count]


def list_run_dirs(runs_dir: Path | None) -> list[Path]:
    if runs_dir is None or not runs_dir.exists():
        return []
    return sorted(path for path in runs_dir.iterdir() if path.is_dir())


def resolve_run_artifact(run_dir: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    root_candidate = ROOT / path
    if root_candidate.exists():
        return root_candidate
    return run_dir / path.name


def invariant(invariant_id: str, source_kind: str, description: str) -> dict[str, Any]:
    return {
        "id": invariant_id,
        "status": "candidate",
        "source_kind": source_kind,
        "description": description,
        "support_count": 0,
        "violation_count": 0,
        "examples": [],
        "violations": [],
    }


def add_support(candidate: dict[str, Any], example: str) -> None:
    candidate["support_count"] += 1
    if len(candidate["examples"]) < 5:
        candidate["examples"].append(example)


def add_violation(candidate: dict[str, Any], example: str, reason: str) -> None:
    candidate["violation_count"] += 1
    if len(candidate["violations"]) < 10:
        candidate["violations"].append({"example": example, "reason": reason})


def format_invariants_report(report: dict[str, Any]) -> str:
    lines = [
        "Boss AI debugger candidate invariants",
        (
            f"candidates={report['candidate_count']} "
            f"violations={report['violation_count']} "
            f"scenarios={report['scenario_count']} "
            f"traces={report['trace_file_count']} runs={report['run_count']}"
        ),
    ]
    for candidate in report["candidates"]:
        lines.append("")
        lines.append(
            f"- {candidate['id']} [{candidate['source_kind']}] "
            f"support={candidate['support_count']} "
            f"violations={candidate['violation_count']}"
        )
        lines.append(f"  {candidate['description']}")
        if candidate["violations"]:
            first = candidate["violations"][0]
            lines.append(f"  first violation: {first['example']}: {first['reason']}")
    if report["known_limits"]:
        lines.append("")
        lines.append("Known limits:")
        for item in report["known_limits"]:
            lines.append(f"- {item}")
    return "\n".join(lines)


def format_invariants_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Boss AI Debugger Candidate Invariants",
        "",
        "Status: candidate hypotheses. Promote a rule to a blocking audit only after review.",
        "",
        f"- candidates: `{report['candidate_count']}`",
        f"- violations: `{report['violation_count']}`",
        f"- scenarios: `{report['scenario_count']}`",
        f"- trace files: `{report['trace_file_count']}`",
        f"- runs: `{report['run_count']}`",
        "",
        "## Candidates",
        "",
    ]
    for candidate in report["candidates"]:
        lines.extend(
            [
                f"### `{candidate['id']}`",
                "",
                f"- source: `{candidate['source_kind']}`",
                f"- support: `{candidate['support_count']}`",
                f"- violations: `{candidate['violation_count']}`",
                f"- description: {candidate['description']}",
            ]
        )
        if candidate["examples"]:
            examples = ", ".join(f"`{example}`" for example in candidate["examples"])
            lines.append(f"- examples: {examples}")
        if candidate["violations"]:
            lines.append("")
            lines.append("Violations:")
            for violation in candidate["violations"]:
                lines.append(
                    f"- `{violation['example']}`: {violation['reason']}"
                )
        lines.append("")
    lines.append("## Known Limits")
    lines.append("")
    for item in report["known_limits"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def write_invariants_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_invariants_markdown(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_invariants_markdown(report), encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()
