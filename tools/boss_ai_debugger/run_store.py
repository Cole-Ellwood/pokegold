from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .generators import generate_scenarios, write_jsonl
from .review_queue import build_review_queue, write_review_queue
from .rom_scenarios import evaluate_batch
from .state_schema import validate_scenario_file


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUNS_DIR = ROOT / "audit" / "boss_ai_debugger" / "runs"
RUN_STORE_VERSION = "boss-ai-debugger-run-v1"


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


def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("/", "\\")
    except ValueError:
        return str(path)
