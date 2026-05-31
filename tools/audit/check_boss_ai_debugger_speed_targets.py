from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_debugger.generators import generate_scenarios, generate_scenarios_compact
from tools.boss_ai_debugger.review_queue import (
    attach_evidence_digests,
    attach_review_proof_commands,
    build_review_queue,
)
from tools.boss_ai_debugger.rom_scenarios import evaluate_batch, evaluate_batch_compact


DEFAULT_SCENARIO_COUNT = 20_000
DEFAULT_SEED = 23
DEFAULT_MIN_COMPACT_GENERATION_PER_MINUTE = 2_500_000
DEFAULT_MIN_COMPACT_SPEEDUP = 2.0
DEFAULT_MIN_COMPACT_PER_MINUTE = 5_000_000
DEFAULT_MIN_QUEUE_INPUTS_PER_MINUTE = 5_000_000
REPORT_PATH = ROOT / ".local" / "tmp" / "boss_ai_debugger" / "speed_targets_report.json"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = run_speed_targets(
        count=args.count,
        seed=args.seed,
        min_compact_generation_per_minute=args.min_compact_generation_per_minute,
        min_compact_speedup=args.min_compact_speedup,
        min_compact_per_minute=args.min_compact_per_minute,
        min_queue_inputs_per_minute=args.min_queue_inputs_per_minute,
    )
    write_json(report, args.json_out)
    errors = speed_target_errors(report)
    if errors:
        print("Boss AI debugger speed target audit failed.")
        for error in errors:
            print(f"  - {error}")
        print(f"wrote {display_path(args.json_out)}")
        return 1

    print("Boss AI debugger speed target audit passed.")
    print(
        "Compact generation: "
        f"{report['generation']['compact_per_minute']:.0f}/min vs "
        f"{report['generation']['rendered_per_minute']:.0f}/min "
        f"({report['generation']['compact_speedup']:.2f}x)."
    )
    print(
        "Compact evaluation: "
        f"{report['compact']['scenarios_per_minute']:.0f}/min vs "
        f"{report['rendered']['scenarios_per_minute']:.0f}/min "
        f"({report['compact_speedup']:.2f}x)."
    )
    print(
        "Review queue reduction: "
        f"{report['queue']['queue_inputs_per_minute']:.0f}/min from "
        f"{report['queue']['input_reviewable_count']} reviewable input(s)."
    )
    print(f"wrote {display_path(args.json_out)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=DEFAULT_SCENARIO_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--min-compact-generation-per-minute",
        type=float,
        default=DEFAULT_MIN_COMPACT_GENERATION_PER_MINUTE,
    )
    parser.add_argument(
        "--min-compact-speedup",
        type=float,
        default=DEFAULT_MIN_COMPACT_SPEEDUP,
    )
    parser.add_argument(
        "--min-compact-per-minute",
        type=float,
        default=DEFAULT_MIN_COMPACT_PER_MINUTE,
    )
    parser.add_argument(
        "--min-queue-inputs-per-minute",
        type=float,
        default=DEFAULT_MIN_QUEUE_INPUTS_PER_MINUTE,
    )
    parser.add_argument("--json-out", type=Path, default=REPORT_PATH)
    return parser


def run_speed_targets(
    *,
    count: int,
    seed: int,
    min_compact_generation_per_minute: float,
    min_compact_speedup: float,
    min_compact_per_minute: float,
    min_queue_inputs_per_minute: float,
) -> dict[str, Any]:
    if count <= 0:
        raise SystemExit("--count must be positive")
    compact_generation_started = time.perf_counter()
    scenarios = generate_scenarios_compact(family="all", count=count, seed=seed)
    compact_generation_elapsed = time.perf_counter() - compact_generation_started

    rendered_generation_started = time.perf_counter()
    rendered_scenarios = generate_scenarios(family="all", count=count, seed=seed)
    rendered_generation_elapsed = time.perf_counter() - rendered_generation_started

    assert_compact_generation_matches_rendered(scenarios, rendered_scenarios)

    rendered_started = time.perf_counter()
    rendered = evaluate_batch(scenarios)
    rendered_elapsed = time.perf_counter() - rendered_started

    compact_started = time.perf_counter()
    compact = evaluate_batch_compact(scenarios)
    compact_elapsed = time.perf_counter() - compact_started

    assert_compact_matches_rendered(rendered, compact)

    queue_started = time.perf_counter()
    queue = build_review_queue(
        compact,
        limit=50,
        max_per_lesson=2,
        include_followups=False,
    )
    queue_elapsed = time.perf_counter() - queue_started
    queue_inputs_per_minute = (
        compact["reviewable_count"] / queue_elapsed * 60 if queue_elapsed > 0 else 0.0
    )

    followup_started = time.perf_counter()
    attach_evidence_digests(queue["items"])
    attach_review_proof_commands(queue["items"], scenario_source="")
    followup_elapsed = time.perf_counter() - followup_started

    return {
        "schema_version": 1,
        "scenario_count": count,
        "seed": seed,
        "min_compact_generation_per_minute": min_compact_generation_per_minute,
        "min_compact_speedup": min_compact_speedup,
        "min_compact_per_minute": min_compact_per_minute,
        "min_queue_inputs_per_minute": min_queue_inputs_per_minute,
        "generation": {
            "compact_elapsed_seconds": compact_generation_elapsed,
            "compact_per_minute": count / compact_generation_elapsed * 60,
            "rendered_elapsed_seconds": rendered_generation_elapsed,
            "rendered_per_minute": count / rendered_generation_elapsed * 60,
            "compact_speedup": rendered_generation_elapsed / compact_generation_elapsed
            if compact_generation_elapsed > 0
            else 0.0,
        },
        "rendered": {
            "elapsed_seconds": rendered_elapsed,
            "scenarios_per_minute": count / rendered_elapsed * 60,
            "reviewable_count": rendered["reviewable_count"],
            "verdict_counts": rendered["verdict_counts"],
        },
        "compact": {
            "elapsed_seconds": compact_elapsed,
            "scenarios_per_minute": count / compact_elapsed * 60,
            "reviewable_count": compact["reviewable_count"],
            "verdict_counts": compact["verdict_counts"],
        },
        "compact_speedup": rendered_elapsed / compact_elapsed
        if compact_elapsed > 0
        else 0.0,
        "queue": {
            "input_reviewable_count": compact["reviewable_count"],
            "returned_count": queue["returned_count"],
            "queue_elapsed_seconds": queue_elapsed,
            "queue_inputs_per_minute": queue_inputs_per_minute,
            "selected_followup_elapsed_seconds": followup_elapsed,
        },
    }


def assert_compact_generation_matches_rendered(
    compact: list[dict[str, Any]],
    rendered: list[dict[str, Any]],
) -> None:
    if len(compact) != len(rendered):
        raise SystemExit("compact generated count differs from rendered count")
    stamp_keys = {"generator_source", "rom", "rom_sha256", "symbols", "symbols_sha256", "state_hash"}
    for index, (compact_scenario, rendered_scenario) in enumerate(zip(compact, rendered)):
        stripped = {
            key: value
            for key, value in rendered_scenario.items()
            if key not in stamp_keys
        }
        if compact_scenario != stripped:
            raise SystemExit(
                f"compact generated scenario differs from rendered scenario at index {index}"
            )


def assert_compact_matches_rendered(rendered: dict[str, Any], compact: dict[str, Any]) -> None:
    if compact["scenario_count"] != rendered["scenario_count"]:
        raise SystemExit("compact scenario count differs from rendered count")
    if compact["reviewable_count"] != rendered["reviewable_count"]:
        raise SystemExit("compact reviewable count differs from rendered count")
    if compact["verdict_counts"] != rendered["verdict_counts"]:
        raise SystemExit("compact verdict counts differ from rendered counts")
    if compact["policy_tag_counts"] != rendered["policy_tag_counts"]:
        raise SystemExit("compact policy tag counts differ from rendered counts")


def speed_target_errors(report: dict[str, Any]) -> list[str]:
    errors = []
    if (
        report["generation"]["compact_per_minute"]
        < report["min_compact_generation_per_minute"]
    ):
        errors.append(
            "compact generation below throughput target: "
            f"{report['generation']['compact_per_minute']:.0f}/min"
        )
    if report["compact_speedup"] < report["min_compact_speedup"]:
        errors.append(
            "compact evaluator below speedup target: "
            f"{report['compact_speedup']:.2f}x"
        )
    if report["compact"]["scenarios_per_minute"] < report["min_compact_per_minute"]:
        errors.append(
            "compact evaluator below throughput target: "
            f"{report['compact']['scenarios_per_minute']:.0f}/min"
        )
    if report["queue"]["queue_inputs_per_minute"] < report["min_queue_inputs_per_minute"]:
        errors.append(
            "review queue reduction below throughput target: "
            f"{report['queue']['queue_inputs_per_minute']:.0f}/min"
        )
    return errors


def write_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("/", "\\")
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
