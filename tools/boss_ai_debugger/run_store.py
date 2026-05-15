from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import load_fixtures, load_preferences

from .differential import build_differential_report
from .invariants import mine_invariants
from .generators import generate_scenarios, write_jsonl
from .metamorphic import run_metamorphic_suite
from .mutation import run_scorer_mutations
from .review_queue import build_review_queue, write_review_queue
from .rom_contribution_trace import (
    resolve_rom_contribution_trace_paths,
    run_rom_contribution_trace_for_route,
    summarize_rom_contribution_trace_paths,
    write_rom_contribution_trace_json,
)
from .rom_scenarios import evaluate_batch
from .rom_score_materialize import (
    run_rom_score_materialization,
    write_rom_score_materialization_json,
)
from .route_eval import evaluate_route_batch
from .rule_map import DEFAULT_RULE_MAP_PATH, build_rule_map, compare_rule_maps
from .state_schema import DEFAULT_TRACE_DIR, validate_scenario_file
from .trace_replay import replay_trace_paths


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUNS_DIR = ROOT / "audit" / "boss_ai_debugger" / "runs"
RUN_STORE_VERSION = "boss-ai-debugger-run-v1"
SELF_REFERENTIAL_DIFF_ARTIFACTS = {"previous_run_diff"}


def run_generated_smoke_suite(
    *,
    count: int,
    seed: int,
    run_id: str | None = None,
    runs_dir: Path = DEFAULT_RUNS_DIR,
) -> dict[str, Any]:
    if count < 0:
        raise ValueError("count must be non-negative")
    resolved_run_id = run_id or default_run_id("generated_smoke")
    run_dir = runs_dir / resolved_run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    scenarios = generate_scenarios(family="all", count=count, seed=seed)
    scenarios_path = run_dir / "scenarios.jsonl"
    batch_path = run_dir / "batch_report.json"
    queue_path = run_dir / "review_queue.json"
    metadata_path = run_dir / "metadata.json"
    summary_path = run_dir / "summary.md"

    write_jsonl(scenarios, scenarios_path)
    validation = validate_scenario_file(scenarios_path)
    batch = evaluate_batch(scenarios)
    queue = build_review_queue(batch, limit=50, source=str(batch_path))

    write_json(batch, batch_path)
    write_review_queue(queue, queue_path)

    metadata = {
        "schema_version": 1,
        "tool_version": RUN_STORE_VERSION,
        "run_id": resolved_run_id,
        "profile": "generated-smoke",
        "created_at": datetime.now(UTC).isoformat(),
        "git_commit": git_stdout(["git", "rev-parse", "HEAD"]),
        "git_status_short": git_stdout(["git", "status", "--short"]),
        "parameters": {"count": count, "seed": seed},
        "artifacts": {
            "scenarios": relative_path(scenarios_path),
            "batch_report": relative_path(batch_path),
            "review_queue": relative_path(queue_path),
            "summary": relative_path(summary_path),
        },
        "artifact_hashes": {
            "scenarios": sha256_file(scenarios_path),
            "batch_report": sha256_file(batch_path),
            "review_queue": sha256_file(queue_path),
        },
        "validation": validation,
        "batch_summary": {
            "scenario_count": batch["scenario_count"],
            "reviewable_count": batch["reviewable_count"],
            "scenarios_per_minute": batch["scenarios_per_minute"],
            "verdict_counts": batch["verdict_counts"],
        },
        "review_queue_summary": {
            "returned_count": queue["returned_count"],
            "input_reviewable_count": queue["input_reviewable_count"],
        },
    }
    write_json(metadata, metadata_path)
    summary_path.write_text(format_run_summary(metadata, queue), encoding="utf-8", newline="\n")
    return metadata


def run_changed_ai_suite(
    *,
    count: int,
    seed: int,
    run_id: str | None = None,
    runs_dir: Path = DEFAULT_RUNS_DIR,
    trace_dir: Path | None = DEFAULT_TRACE_DIR,
    rom_contribution_trace_paths: list[Path] | None = None,
    refresh_rom_contribution_trace: bool = False,
    rom_contribution_boss_route: str = "clair",
    refresh_rom_score_materialization: bool = False,
) -> dict[str, Any]:
    if count < 0:
        raise ValueError("count must be non-negative")
    resolved_run_id = run_id or default_run_id("changed_ai")
    run_dir = runs_dir / resolved_run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    scenarios = generate_scenarios(family="all", count=count, seed=seed)
    scenarios_path = run_dir / "scenarios.jsonl"
    batch_path = run_dir / "batch_report.json"
    queue_path = run_dir / "review_queue.json"
    route_eval_path = run_dir / "route_eval.json"
    differential_path = run_dir / "differential.json"
    metamorphic_path = run_dir / "metamorphic.json"
    mutation_path = run_dir / "mutation.json"
    invariants_path = run_dir / "invariants.json"
    trace_replay_path = run_dir / "trace_replay.json"
    rom_contribution_summary_path = run_dir / "rom_contribution_trace_summary.json"
    rom_score_materialization_path = run_dir / "rom_score_materialization.json"
    previous_run_diff_path = run_dir / "previous_run_diff.json"
    metadata_path = run_dir / "metadata.json"
    summary_path = run_dir / "summary.md"
    copied_rom_contribution_paths = materialize_rom_contribution_traces(
        run_dir=run_dir,
        input_paths=resolve_rom_contribution_trace_paths(rom_contribution_trace_paths),
        refresh=refresh_rom_contribution_trace,
        boss_route=rom_contribution_boss_route,
    )

    write_jsonl(scenarios, scenarios_path)
    validation = validate_scenario_file(scenarios_path)
    batch = evaluate_batch(scenarios)
    queue = build_review_queue(batch, limit=50, source=str(batch_path))
    route_eval = evaluate_route_batch(scenarios, source=str(scenarios_path))
    rom_score_materialization = materialize_rom_score_scenarios(
        scenarios=scenarios,
        refresh=refresh_rom_score_materialization,
    )
    metamorphic = run_metamorphic_suite(generated=min(count, 100), seed=seed)
    fixtures = load_fixtures()
    labels = load_preferences(fixtures=fixtures)
    mutation = run_scorer_mutations(fixtures, labels)
    trace_paths = sorted(trace_dir.glob("*_live.txt")) if trace_dir and trace_dir.exists() else []
    differential = build_differential_report(
        scenarios=scenarios,
        trace_paths=trace_paths,
        rom_contribution_trace_paths=copied_rom_contribution_paths,
        rom_contribution_reports=rom_score_materialization.get("traces", []),
        source="changed-ai",
    )
    rom_contribution_summary = summarize_rom_contribution_trace_paths(
        copied_rom_contribution_paths
    )
    trace_replay = replay_trace_paths(trace_paths) if trace_paths else skipped_trace_report(trace_dir)
    invariants = mine_invariants(
        scenarios=scenarios,
        runs_dir=runs_dir,
        trace_paths=trace_paths,
    )
    rule_map = build_rule_map()
    rule_errors = compare_rule_maps(rule_map, DEFAULT_RULE_MAP_PATH)

    write_json(batch, batch_path)
    write_review_queue(queue, queue_path)
    write_json(route_eval, route_eval_path)
    write_json(differential, differential_path)
    write_json(metamorphic, metamorphic_path)
    write_json(mutation, mutation_path)
    write_json(invariants, invariants_path)
    write_json(trace_replay, trace_replay_path)
    write_json(rom_contribution_summary, rom_contribution_summary_path)
    write_rom_score_materialization_json(
        rom_score_materialization,
        rom_score_materialization_path,
    )

    metadata = {
        "schema_version": 1,
        "tool_version": RUN_STORE_VERSION,
        "run_id": resolved_run_id,
        "profile": "changed-ai",
        "created_at": datetime.now(UTC).isoformat(),
        "git_commit": git_stdout(["git", "rev-parse", "HEAD"]),
        "git_status_short": git_stdout(["git", "status", "--short"]),
        "changed_files": changed_files(),
        "parameters": {
            "count": count,
            "seed": seed,
            "trace_dir": str(trace_dir or ""),
            "refresh_rom_contribution_trace": refresh_rom_contribution_trace,
            "rom_contribution_boss_route": rom_contribution_boss_route,
            "refresh_rom_score_materialization": refresh_rom_score_materialization,
        },
        "artifacts": {
            "scenarios": relative_path(scenarios_path),
            "batch_report": relative_path(batch_path),
            "review_queue": relative_path(queue_path),
            "route_eval": relative_path(route_eval_path),
            "differential": relative_path(differential_path),
            "metamorphic": relative_path(metamorphic_path),
            "mutation": relative_path(mutation_path),
            "invariants": relative_path(invariants_path),
            "trace_replay": relative_path(trace_replay_path),
            "rom_contribution_trace_summary": relative_path(
                rom_contribution_summary_path,
            ),
            "rom_score_materialization": relative_path(rom_score_materialization_path),
            "previous_run_diff": relative_path(previous_run_diff_path),
            "rom_contribution_traces": [
                relative_path(path) for path in copied_rom_contribution_paths
            ],
            "summary": relative_path(summary_path),
        },
        "artifact_hashes": {
            "scenarios": sha256_file(scenarios_path),
            "batch_report": sha256_file(batch_path),
            "review_queue": sha256_file(queue_path),
            "route_eval": sha256_file(route_eval_path),
            "differential": sha256_file(differential_path),
            "metamorphic": sha256_file(metamorphic_path),
            "mutation": sha256_file(mutation_path),
            "invariants": sha256_file(invariants_path),
            "trace_replay": sha256_file(trace_replay_path),
            "rom_contribution_trace_summary": sha256_file(
                rom_contribution_summary_path,
            ),
            "rom_score_materialization": sha256_file(rom_score_materialization_path),
            "rom_contribution_traces": {
                relative_path(path): sha256_file(path)
                for path in copied_rom_contribution_paths
            },
        },
        "validation": validation,
        "batch_summary": {
            "scenario_count": batch["scenario_count"],
            "reviewable_count": batch["reviewable_count"],
            "scenarios_per_minute": batch["scenarios_per_minute"],
            "verdict_counts": batch["verdict_counts"],
        },
        "review_queue_summary": {
            "returned_count": queue["returned_count"],
            "input_reviewable_count": queue["input_reviewable_count"],
        },
        "route_eval_summary": route_eval["classification_counts"],
        "differential_summary": {
            "mismatch_count": differential["mismatch_count"],
            "mismatch_class_counts": differential["mismatch_class_counts"],
            "contribution_comparison": {
                "matched_trace_count": differential["contribution_comparison"][
                    "matched_trace_count"
                ],
                "mismatch_count": differential["contribution_comparison"][
                    "mismatch_count"
                ],
                "mismatch_class_counts": differential["contribution_comparison"][
                    "mismatch_class_counts"
                ],
            },
        },
        "metamorphic_summary": {
            "passed": metamorphic["passed"],
            "pass_count": metamorphic["pass_count"],
            "relation_count": metamorphic["relation_count"],
        },
        "mutation_summary": {
            "killed_count": mutation["killed_count"],
            "survived_count": mutation["survived_count"],
            "not_exercised_count": mutation["not_exercised_count"],
            "mutation_score": mutation["mutation_score"],
        },
        "invariant_summary": {
            "candidate_count": invariants["candidate_count"],
            "violation_count": invariants["violation_count"],
        },
        "trace_replay_summary": {
            "trace_count": trace_replay.get("trace_count", 0),
            "checked_count": trace_replay.get("checked_count", 0),
            "failure_count": trace_replay.get("failure_count", 0),
            "agreement_rate": trace_replay.get("agreement_rate", 0.0),
        },
        "rom_contribution_summary": {
            "available": rom_contribution_summary["available"],
            "artifact_count": rom_contribution_summary["artifact_count"],
            "event_count": rom_contribution_summary["event_count"],
            "changed_event_count": rom_contribution_summary["changed_event_count"],
            "covered_rule_count": rom_contribution_summary["covered_rule_count"],
            "changed_rule_count": rom_contribution_summary["changed_rule_count"],
            "unmapped_event_count": rom_contribution_summary["unmapped_event_count"],
        },
        "rom_score_materialization_summary": {
            "checked_count": rom_score_materialization.get("checked_count", 0),
            "error_count": rom_score_materialization.get("error_count", 0),
            "contribution_matched_count": rom_score_materialization.get(
                "contribution_matched_count", 0
            ),
            "contribution_mismatch_count": rom_score_materialization.get(
                "contribution_mismatch_count", 0
            ),
            "hook_equivalence_checked_count": rom_score_materialization.get(
                "hook_equivalence_checked_count", 0
            ),
            "hook_equivalence_mismatch_count": rom_score_materialization.get(
                "hook_equivalence_mismatch_count", 0
            ),
            "skipped_reason": rom_score_materialization.get("skipped_reason", ""),
        },
        "rule_map_summary": {
            "rule_count": rule_map["rule_count"],
            "stored_rule_map_errors": rule_errors,
        },
        "known_gaps": changed_ai_known_gaps(
            refresh_rom_contribution_trace=refresh_rom_contribution_trace,
            refresh_rom_score_materialization=refresh_rom_score_materialization,
        ),
    }
    previous_run_diff = build_previous_run_diff(
        runs_dir=runs_dir,
        current_run_id=resolved_run_id,
        current_metadata=metadata,
    )
    write_json(previous_run_diff, previous_run_diff_path)
    metadata["artifact_hashes"]["previous_run_diff"] = sha256_file(
        previous_run_diff_path
    )
    metadata["previous_run_diff_summary"] = previous_run_diff["summary"]
    write_json(metadata, metadata_path)
    summary_path.write_text(
        format_changed_ai_summary(metadata, queue),
        encoding="utf-8",
        newline="\n",
    )
    return metadata


def format_run_summary(metadata: dict[str, Any], queue: dict[str, Any]) -> str:
    batch = metadata["batch_summary"]
    lines = [
        f"# Boss AI Debugger Run: {metadata['run_id']}",
        "",
        f"Profile: `{metadata['profile']}`",
        f"Created: `{metadata['created_at']}`",
        f"Git commit: `{metadata['git_commit']}`",
        "",
        "## Batch",
        "",
        f"- scenarios: `{batch['scenario_count']}`",
        f"- reviewable: `{batch['reviewable_count']}`",
        f"- rate: `{batch['scenarios_per_minute']:.0f}/min`",
        f"- verdicts: `{batch['verdict_counts']}`",
        "",
        "## Top Review Items",
        "",
    ]
    if not queue["items"]:
        lines.append("None.")
    for item in queue["items"][:10]:
        probability = float(item["rom_best_probability"])
        lines.append(
            f"- `{item['verdict']}` `{item['scenario_id']}` "
            f"rom=`{item['rom_best_action_id']}` ({probability:.1%}), "
            f"best=`{','.join(item['expected_best_action_ids']) or 'none'}`"
        )
    lines.append("")
    return "\n".join(lines)


def format_changed_ai_summary(metadata: dict[str, Any], queue: dict[str, Any]) -> str:
    batch = metadata["batch_summary"]
    trace = metadata["trace_replay_summary"]
    mutation = metadata["mutation_summary"]
    contribution = metadata["rom_contribution_summary"]
    score_materialization = metadata["rom_score_materialization_summary"]
    lines = [
        f"# Boss AI Debugger Changed-AI Run: {metadata['run_id']}",
        "",
        f"Created: `{metadata['created_at']}`",
        f"Git commit: `{metadata['git_commit']}`",
        "",
        "## Gates",
        "",
        f"- scenarios: `{batch['scenario_count']}`",
        f"- reviewable: `{batch['reviewable_count']}`",
        f"- route classifications: `{metadata['route_eval_summary']}`",
        f"- differential: `{metadata['differential_summary']}`",
        f"- metamorphic: `{metadata['metamorphic_summary']}`",
        f"- mutation: `{mutation}`",
        f"- invariants: `{metadata['invariant_summary']}`",
        f"- trace replay: `{trace}`",
        f"- ROM contribution: `{contribution}`",
        f"- ROM score materialization: `{score_materialization}`",
        f"- previous run diff: `{metadata.get('previous_run_diff_summary', {})}`",
        f"- rule map errors: `{metadata['rule_map_summary']['stored_rule_map_errors']}`",
        "",
        "## Known Gaps",
        "",
    ]
    for item in metadata["known_gaps"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Top Review Items", ""])
    if not queue["items"]:
        lines.append("None.")
    for item in queue["items"][:10]:
        probability = float(item["rom_best_probability"])
        lines.append(
            f"- `{item['verdict']}` `{item['scenario_id']}` "
            f"rom=`{item['rom_best_action_id']}` ({probability:.1%}), "
            f"best=`{','.join(item['expected_best_action_ids']) or 'none'}`"
        )
    lines.append("")
    return "\n".join(lines)


def default_run_id(profile: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{profile}"


def write_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def git_stdout(args: list[str]) -> str:
    try:
        completed = subprocess.run(
            args,
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return completed.stdout.strip()


def changed_files() -> list[str]:
    output = git_stdout(["git", "diff", "--name-only", "HEAD~1..HEAD"])
    if not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def build_previous_run_diff(
    *,
    runs_dir: Path,
    current_run_id: str,
    current_metadata: dict[str, Any],
) -> dict[str, Any]:
    previous = load_previous_changed_ai_metadata(
        runs_dir=runs_dir,
        current_run_id=current_run_id,
    )
    if previous is None:
        return {
            "schema_version": 1,
            "kind": "changed_ai_previous_run_diff",
            "available": False,
            "current_run_id": current_run_id,
            "previous_run_id": "",
            "reason": "no previous changed-ai run metadata found",
            "summary": {
                "available": False,
                "changed_metric_count": 0,
                "artifact_hash_change_count": 0,
                "changed_file_added_count": 0,
                "changed_file_removed_count": 0,
            },
            "metric_deltas": {},
            "artifact_hash_changes": [],
            "changed_file_diff": {
                "previous_count": 0,
                "current_count": 0,
                "added": [],
                "removed": [],
                "shared": [],
            },
        }

    metric_deltas = changed_ai_metric_deltas(previous, current_metadata)
    artifact_hash_changes = artifact_hash_changes_for_runs(previous, current_metadata)
    changed_file_diff = changed_ai_changed_file_diff(previous, current_metadata)
    return {
        "schema_version": 1,
        "kind": "changed_ai_previous_run_diff",
        "available": True,
        "current_run_id": current_run_id,
        "previous_run_id": str(previous.get("run_id", "")),
        "previous_git_commit": str(previous.get("git_commit", "")),
        "current_git_commit": str(current_metadata.get("git_commit", "")),
        "summary": {
            "available": True,
            "changed_metric_count": len(
                [item for item in metric_deltas.values() if item["delta"] != 0]
            ),
            "artifact_hash_change_count": len(artifact_hash_changes),
            "changed_file_added_count": len(changed_file_diff["added"]),
            "changed_file_removed_count": len(changed_file_diff["removed"]),
        },
        "metric_deltas": metric_deltas,
        "artifact_hash_changes": artifact_hash_changes,
        "changed_file_diff": changed_file_diff,
    }


def load_previous_changed_ai_metadata(
    *,
    runs_dir: Path,
    current_run_id: str,
) -> dict[str, Any] | None:
    candidates = []
    for path in runs_dir.glob("*/metadata.json"):
        if path.parent.name == current_run_id:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict) or data.get("profile") != "changed-ai":
            continue
        candidates.append((str(data.get("created_at", "")), path, data))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], str(item[1])))
    return candidates[-1][2]


def changed_ai_metric_deltas(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, dict[str, float]]:
    metric_paths = {
        "scenario_count": ("batch_summary", "scenario_count"),
        "reviewable_count": ("batch_summary", "reviewable_count"),
        "differential_mismatch_count": ("differential_summary", "mismatch_count"),
        "contribution_mismatch_count": (
            "differential_summary",
            "contribution_comparison",
            "mismatch_count",
        ),
        "trace_replay_failure_count": ("trace_replay_summary", "failure_count"),
        "rom_score_error_count": ("rom_score_materialization_summary", "error_count"),
        "rom_score_contribution_mismatch_count": (
            "rom_score_materialization_summary",
            "contribution_mismatch_count",
        ),
        "mutation_survived_count": ("mutation_summary", "survived_count"),
        "invariant_violation_count": ("invariant_summary", "violation_count"),
    }
    return {
        metric: metric_delta(previous, current, path)
        for metric, path in metric_paths.items()
    }


def metric_delta(
    previous: dict[str, Any],
    current: dict[str, Any],
    path: tuple[str, ...],
) -> dict[str, float]:
    previous_value = nested_number(previous, path)
    current_value = nested_number(current, path)
    return {
        "previous": previous_value,
        "current": current_value,
        "delta": current_value - previous_value,
    }


def nested_number(data: dict[str, Any], path: tuple[str, ...]) -> float:
    value: Any = data
    for key in path:
        if not isinstance(value, dict):
            return 0.0
        value = value.get(key)
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def artifact_hash_changes_for_runs(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> list[dict[str, str]]:
    previous_hashes = flatten_hashes(previous.get("artifact_hashes", {}))
    current_hashes = flatten_hashes(current.get("artifact_hashes", {}))
    changes = []
    for key in sorted(set(previous_hashes) | set(current_hashes)):
        if key in SELF_REFERENTIAL_DIFF_ARTIFACTS:
            continue
        previous_hash = previous_hashes.get(key, "")
        current_hash = current_hashes.get(key, "")
        if previous_hash == current_hash:
            continue
        changes.append(
            {
                "artifact": key,
                "previous": previous_hash,
                "current": current_hash,
            }
        )
    return changes


def changed_ai_changed_file_diff(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, Any]:
    previous_files = string_set(previous.get("changed_files", []))
    current_files = string_set(current.get("changed_files", []))
    return {
        "previous_count": len(previous_files),
        "current_count": len(current_files),
        "added": sorted(current_files - previous_files),
        "removed": sorted(previous_files - current_files),
        "shared": sorted(previous_files & current_files),
    }


def string_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}


def flatten_hashes(value: Any, *, prefix: str = "") -> dict[str, str]:
    if isinstance(value, str):
        return {prefix: value} if prefix else {}
    if not isinstance(value, dict):
        return {}
    result: dict[str, str] = {}
    for key, item in value.items():
        child_prefix = f"{prefix}.{key}" if prefix else str(key)
        result.update(flatten_hashes(item, prefix=child_prefix))
    return result


def copy_rom_contribution_traces(paths: list[Path], *, run_dir: Path) -> list[Path]:
    copied = []
    if not paths:
        return copied
    target_dir = run_dir / "rom_contribution_traces"
    for index, path in enumerate(paths, start=1):
        if not path.exists():
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{index:02d}_{path.name}"
        shutil.copyfile(path, target)
        copied.append(target)
    return copied


def materialize_rom_contribution_traces(
    *,
    run_dir: Path,
    input_paths: list[Path],
    refresh: bool,
    boss_route: str,
) -> list[Path]:
    if refresh:
        path = run_dir / "rom_contribution_trace_refreshed.json"
        report = run_rom_contribution_trace_for_route(
            boss_id=boss_route,
            metadata={
                "boss": boss_route,
                "notes": "changed-ai-suite-refresh",
            },
        )
        write_rom_contribution_trace_json(report, path)
        return [path]
    return copy_rom_contribution_traces(input_paths, run_dir=run_dir)


def materialize_rom_score_scenarios(
    *,
    scenarios: list[dict[str, Any]],
    refresh: bool,
) -> dict[str, Any]:
    selected = score_materialization_scenarios(scenarios, limit=3)
    if not refresh:
        return skipped_rom_score_materialization_report(
            selected_count=len(selected),
            reason=(
                "not requested; pass --refresh-rom-score-materialization to run "
                "generated score-model materialization"
            ),
        )
    if not selected:
        return skipped_rom_score_materialization_report(
            selected_count=0,
            reason="no generated spikes_spin scenarios available for score materialization",
        )
    return run_rom_score_materialization(
        selected,
        source="changed-ai-suite",
    )


def score_materialization_scenarios(
    scenarios: list[dict[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    candidates = [
        scenario
        for scenario in scenarios
        if scenario.get("family") == "spikes_spin"
    ]

    def priority(scenario: dict[str, Any]) -> tuple[int, str]:
        expectation = scenario.get("expectation", {})
        tags = (
            set(expectation.get("condition_tags", []))
            if isinstance(expectation, dict)
            else set()
        )
        active_revealed = "active_revealed_rapid_spin" in tags
        risky_layer = "spikes_layers_1" in tags or "spikes_layers_2" in tags
        return (
            0 if active_revealed and risky_layer else 1,
            str(scenario.get("id", "")),
        )

    return sorted(candidates, key=priority)[:limit]


def skipped_rom_score_materialization_report(
    *,
    selected_count: int,
    reason: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "source": "changed-ai-suite",
        "kind": "rom_score_materialization",
        "base_route": "koga",
        "base_state": "",
        "scenario_count": selected_count,
        "checked_count": 0,
        "skipped_count": selected_count,
        "error_count": 0,
        "score_bytes_match_count": 0,
        "selector_top_match_count": 0,
        "contribution_matched_count": 0,
        "contribution_mismatch_count": 0,
        "hook_equivalence_checked_count": 0,
        "hook_equivalence_mismatch_count": 0,
        "elapsed_seconds": 0.0,
        "materializations_per_minute": 0.0,
        "skipped_reason": reason,
        "known_limits": [reason],
        "verdicts": [],
        "traces": [],
    }


def changed_ai_known_gaps(
    *,
    refresh_rom_contribution_trace: bool,
    refresh_rom_score_materialization: bool,
) -> list[str]:
    gaps = ["changed-ai suite does not rebuild ROMs yet."]
    if refresh_rom_contribution_trace:
        gaps.append(
            "changed-ai suite refreshes one ROM contribution route, not the full live trace corpus."
        )
    else:
        gaps.append(
            "changed-ai suite ingests existing ROM contribution trace artifacts but does not refresh them."
        )
    if refresh_rom_score_materialization:
        gaps.append(
            "changed-ai suite materializes a targeted generated score batch, not all touched-rule generated scenarios."
        )
    else:
        gaps.append(
            "changed-ai suite records generated score materialization as skipped unless explicitly requested."
        )
    gaps.extend(
        [
            "ROM/Python contribution traces are compared only when trace ids match.",
            "pre-choice replay remains a separate audit until trace timing is stable.",
        ]
    )
    return gaps


def skipped_trace_report(trace_dir: Path | None) -> dict[str, Any]:
    return {
        "trace_count": 0,
        "capture_count": 0,
        "checked_count": 0,
        "match_count": 0,
        "agreement_rate": 0.0,
        "failure_count": 0,
        "verdict_counts": {"skipped": 1},
        "verdicts": [],
        "skip_reason": f"trace dir not found or empty: {trace_dir}",
    }


def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("/", "\\")
    except ValueError:
        return str(path)
