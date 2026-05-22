from __future__ import annotations

import json
import random
from collections.abc import Callable
from typing import Any


SCHEMA_VERSION = 1
Observation = dict[str, Any]
ChaosRunner = Callable[[dict[str, Any]], Observation]

VBLANK_DELTA_CYCLES = (-1, 0, 1)
HBLANK_DELTA_CYCLES = (-1, 0, 1)
JOYPAD_LATCH_LATENCY_CYCLES = (0, 1, 2)
DMA_CPU_PHASES = (0, 1, 2, 3)


def derive_run_seed(seed: int, run_index: int) -> int:
    return (int(seed) * 1_000_003 + int(run_index) * 97_409) & 0xFFFFFFFF


def build_chaos_schedule(
    *,
    seed: int,
    run_index: int = 0,
    frames: int = 8,
) -> dict[str, Any]:
    run_seed = derive_run_seed(seed, run_index)
    rng = random.Random(run_seed)
    events = []
    for frame in range(max(0, int(frames))):
        events.append(
            {
                "frame": frame,
                "vblank_delta_cycles": rng.choice(VBLANK_DELTA_CYCLES),
                "hblank_delta_cycles": rng.choice(HBLANK_DELTA_CYCLES),
                "joypad_latch_latency_cycles": rng.choice(JOYPAD_LATCH_LATENCY_CYCLES),
                "dma_cpu_phase": rng.choice(DMA_CPU_PHASES),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "unified_debugger_chaos_schedule",
        "seed": int(seed),
        "run_index": int(run_index),
        "run_seed": run_seed,
        "frames": max(0, int(frames)),
        "events": events,
        "hardware_envelope": {
            "vblank_delta_cycles": list(VBLANK_DELTA_CYCLES),
            "hblank_delta_cycles": list(HBLANK_DELTA_CYCLES),
            "joypad_latch_latency_cycles": list(JOYPAD_LATCH_LATENCY_CYCLES),
            "dma_cpu_phase": list(DMA_CPU_PHASES),
        },
    }


def run_chaos_campaign(
    *,
    runs: int,
    seed: int,
    frames: int,
    baseline: Observation,
    runner: ChaosRunner,
) -> dict[str, Any]:
    run_count = max(0, int(runs))
    divergences = []
    stable_count = 0
    for run_index in range(run_count):
        schedule = build_chaos_schedule(seed=seed, run_index=run_index, frames=frames)
        observation = runner(schedule)
        diverged = observation_diverged(observation, baseline)
        if diverged:
            divergences.append(
                {
                    "run_index": run_index,
                    "run_seed": schedule["run_seed"],
                    "observation": observation,
                    "schedule": schedule,
                    "input_log": observation.get("input_log", []),
                }
            )
        else:
            stable_count += 1
    first = divergences[0] if divergences else {}
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "unified_debugger_chaos_campaign",
        "seed": int(seed),
        "runs": run_count,
        "frames": max(0, int(frames)),
        "baseline": baseline,
        "stable_count": stable_count,
        "divergence_count": len(divergences),
        "diverged": bool(divergences),
        "minimal_seed": first.get("run_seed") if first else None,
        "candidate_input_log": first.get("input_log", []) if first else [],
        "divergences": divergences,
        "known_limits": [
            "Chaos schedule generation is deterministic and hardware-envelope bounded; PyBoy interrupt/DMA perturbation is a follow-up adapter layer.",
            "A divergence is only as strong as the runner observation supplied by the caller.",
        ],
    }


def observation_diverged(observation: Observation, baseline: Observation) -> bool:
    comparable_observation = comparable_observation_fields(observation)
    comparable_baseline = comparable_observation_fields(baseline)
    return comparable_observation != comparable_baseline


def comparable_observation_fields(observation: Observation) -> dict[str, Any]:
    return {
        key: value
        for key, value in observation.items()
        if key not in {"input_log", "notes", "schedule", "run_seed"}
    }


def format_report(report: dict[str, Any]) -> str:
    if report.get("kind") == "unified_debugger_chaos_schedule":
        return (
            "Chaos schedule\n"
            f"seed={report.get('seed')} run_seed={report.get('run_seed')} frames={report.get('frames')}"
        )
    return (
        "Chaos campaign\n"
        f"runs={report.get('runs', 0)} stable={report.get('stable_count', 0)} "
        f"divergences={report.get('divergence_count', 0)} minimal_seed={report.get('minimal_seed')}"
    )


def report_json(report: dict[str, Any]) -> str:
    return json.dumps(report, sort_keys=True)
