from __future__ import annotations

import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_debugger.generators import generate_scenarios
from tools.boss_ai_debugger.review_queue import build_review_queue
from tools.boss_ai_debugger.rom_scenarios import evaluate_batch


SCENARIO_COUNT = 5000
SEED = 23
MIN_SCENARIOS_PER_MINUTE = 10_000
MIN_REVIEWABLE_CHECKS_PER_MINUTE = 1_000
MIN_QUEUE_INPUTS_PER_MINUTE = 10_000
MAX_DUPLICATE_LESSON_RATE = 0.10
REPORT_PATH = ROOT / ".local" / "tmp" / "boss_ai_debugger" / "performance_report.json"


def main() -> int:
    scenarios = generate_scenarios(family="all", count=SCENARIO_COUNT, seed=SEED)
    batch = evaluate_batch(scenarios)

    queue_started = time.perf_counter()
    queue = build_review_queue(batch, limit=50, max_per_lesson=2)
    queue_elapsed = time.perf_counter() - queue_started
    queue_inputs_per_minute = (
        batch["reviewable_count"] / queue_elapsed * 60 if queue_elapsed > 0 else 0.0
    )
    duplicate_rate = duplicate_lesson_rate(queue)
    available_lesson_keys = reviewable_lesson_keys(batch)
    avoidable_duplicate_rate = avoidable_duplicate_lesson_rate(
        queue,
        available_lesson_keys,
    )

    report = {
        "schema_version": 1,
        "scenario_count": SCENARIO_COUNT,
        "seed": SEED,
        "min_scenarios_per_minute": MIN_SCENARIOS_PER_MINUTE,
        "min_reviewable_checks_per_minute": MIN_REVIEWABLE_CHECKS_PER_MINUTE,
        "min_queue_inputs_per_minute": MIN_QUEUE_INPUTS_PER_MINUTE,
        "max_duplicate_lesson_rate": MAX_DUPLICATE_LESSON_RATE,
        "batch": {
            "scenario_count": batch["scenario_count"],
            "reviewable_count": batch["reviewable_count"],
            "scenarios_per_minute": batch["scenarios_per_minute"],
            "reviewable_per_minute": batch["reviewable_per_minute"],
            "verdict_counts": batch["verdict_counts"],
        },
        "queue": {
            "input_reviewable_count": queue["input_reviewable_count"],
            "returned_count": queue["returned_count"],
            "queue_elapsed_seconds": queue_elapsed,
            "queue_inputs_per_minute": queue_inputs_per_minute,
            "duplicate_lesson_rate": duplicate_rate,
            "avoidable_duplicate_lesson_rate": avoidable_duplicate_rate,
            "available_lesson_key_count": len(available_lesson_keys),
        },
    }
    write_json(report, REPORT_PATH)

    errors = performance_errors(report)
    if errors:
        print("Boss AI debugger performance audit failed.")
        for error in errors:
            print(f"  - {error}")
        print(f"wrote {display_path(REPORT_PATH)}")
        return 1

    print("Boss AI debugger performance audit passed.")
    print(
        "Scenario evaluation: "
        f"{batch['scenario_count']} cases at "
        f"{batch['scenarios_per_minute']:.0f}/min; "
        f"reviewable checks at {batch['reviewable_per_minute']:.0f}/min."
    )
    print(
        "Review queue: "
        f"{queue['input_reviewable_count']} reviewable inputs at "
        f"{queue_inputs_per_minute:.0f}/min; "
        f"avoidable_duplicate_lesson_rate={avoidable_duplicate_rate:.1%} "
        f"({len(available_lesson_keys)} available lesson key(s))."
    )
    print(f"wrote {display_path(REPORT_PATH)}")
    return 0


def performance_errors(report: dict) -> list[str]:
    errors = []
    if report["batch"]["scenarios_per_minute"] < report["min_scenarios_per_minute"]:
        errors.append(
            "scenario evaluation below threshold: "
            f"{report['batch']['scenarios_per_minute']:.0f}/min"
        )
    if report["batch"]["reviewable_count"] > 0:
        if (
            report["batch"]["reviewable_per_minute"]
            < report["min_reviewable_checks_per_minute"]
        ):
            errors.append(
                "reviewable checks below threshold: "
                f"{report['batch']['reviewable_per_minute']:.0f}/min"
            )
        if (
            report["queue"]["queue_inputs_per_minute"]
            < report["min_queue_inputs_per_minute"]
        ):
            errors.append(
                "review queue reduction below threshold: "
                f"{report['queue']['queue_inputs_per_minute']:.0f}/min"
            )
    if (
        report["queue"]["avoidable_duplicate_lesson_rate"]
        > report["max_duplicate_lesson_rate"]
    ):
        errors.append(
            "review queue avoidable duplicate lesson rate above threshold: "
            f"{report['queue']['avoidable_duplicate_lesson_rate']:.1%}"
        )
    return errors


def duplicate_lesson_rate(queue: dict) -> float:
    items = queue["items"]
    if not items:
        return 0.0
    seen = set()
    duplicates = 0
    for item in items:
        lesson = item.get("lesson_key", "")
        if lesson in seen:
            duplicates += 1
        else:
            seen.add(lesson)
    return duplicates / len(items)


def avoidable_duplicate_lesson_rate(queue: dict, available_lesson_keys: set[str]) -> float:
    items = queue["items"]
    if not items:
        return 0.0
    seen = set()
    avoidable = 0
    for item in items:
        lesson = item.get("lesson_key", "")
        if lesson in seen and available_lesson_keys - seen:
            avoidable += 1
        seen.add(lesson)
    return avoidable / len(items)


def reviewable_lesson_keys(batch: dict) -> set[str]:
    keys = set()
    all_items = build_review_queue(
        batch,
        limit=int(batch["reviewable_count"]),
        max_per_lesson=0,
    )
    for item in all_items["items"]:
        key = str(item.get("lesson_key", ""))
        if key:
            keys.add(key)
    return keys


def write_json(data: dict, path: Path) -> None:
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
