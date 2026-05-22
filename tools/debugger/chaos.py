from __future__ import annotations

import json
import random
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .input_log import play_inputs_for_frame


SCHEMA_VERSION = 1
Observation = dict[str, Any]
ChaosRunner = Callable[[dict[str, Any]], Observation]
ChaosObserver = Callable[[Any, dict[str, Any]], Observation]
CHAOS_SCENARIOS = ("stable", "synthetic_flake", "synthetic-flake")

VBLANK_DELTA_CYCLES = (-1, 0, 1)
HBLANK_DELTA_CYCLES = (-1, 0, 1)
JOYPAD_LATCH_LATENCY_CYCLES = (0, 1, 2)
DMA_CPU_PHASES = (0, 1, 2, 3)
PYBOY_CYCLE_LEVEL_PERTURBATION_FIELDS = (
    "vblank_delta_cycles",
    "hblank_delta_cycles",
    "joypad_latch_latency_cycles",
    "dma_cpu_phase",
)
PYBOY_PUBLIC_API_LIMIT_REASON = (
    "pyboy_public_api_exposes_frame_ticks_and_button_events_"
    "not_cycle_level_interrupt_or_dma_timing"
)
BASELINE_OBSERVATION = {
    "status": "ok",
    "pc": "BattleCommand_DamageCalc",
    "wCurDamage": 42,
}


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
        "valid": True,
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
        "errors": [],
        "warnings": [],
        "error_count": 0,
        "warning_count": 0,
    }


def run_named_chaos_scenario(
    *,
    scenario: str,
    runs: int,
    seed: int,
    frames: int,
) -> dict[str, Any]:
    normalized = scenario.replace("-", "_")
    runners: dict[str, ChaosRunner] = {
        "stable": stable_runner,
        "synthetic_flake": synthetic_flake_runner,
    }
    if normalized not in runners:
        return {
            "schema_version": SCHEMA_VERSION,
            "kind": "unified_debugger_chaos_campaign",
            "valid": False,
            "scenario": normalized,
            "seed": int(seed),
            "runs": max(0, int(runs)),
            "frames": max(0, int(frames)),
            "baseline": BASELINE_OBSERVATION,
            "stable_count": 0,
            "divergence_count": 0,
            "diverged": False,
            "minimal_seed": None,
            "candidate_input_log": [],
            "divergences": [],
            "known_limits": [],
            "errors": [f"unknown chaos scenario: {scenario}"],
            "warnings": [],
            "error_count": 1,
            "warning_count": 0,
        }
    report = run_chaos_campaign(
        runs=runs,
        seed=seed,
        frames=frames,
        baseline=BASELINE_OBSERVATION,
        runner=runners[normalized],
    )
    report["scenario"] = normalized
    return report


def drive_pyboy_with_chaos_schedule(
    pyboy: Any,
    schedule: dict[str, Any],
    *,
    input_playback: dict[str, Any] | None = None,
    observer: ChaosObserver | None = None,
    render: bool = False,
    sound: bool = False,
    max_planned_not_applied: int = 64,
) -> dict[str, Any]:
    events = [event for event in schedule.get("events", []) if isinstance(event, dict)]
    playback = input_playback or {"valid": True, "events": []}
    played_inputs: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    planned_not_applied: list[dict[str, Any]] = []
    planned_not_applied_count = 0
    tick_count = 0
    stopped = False
    for event in events:
        frame = int(event.get("frame", tick_count) or 0)
        for field in PYBOY_CYCLE_LEVEL_PERTURBATION_FIELDS:
            if field not in event:
                continue
            planned_not_applied_count += 1
            if len(planned_not_applied) < max(0, int(max_planned_not_applied)):
                planned_not_applied.append(
                    {
                        "frame": frame,
                        "field": field,
                        "requested_value": event.get(field),
                        "status": "planned_not_applied",
                        "reason": PYBOY_PUBLIC_API_LIMIT_REASON,
                    }
                )
        played_inputs.extend(play_inputs_for_frame(pyboy, playback, frame))
        if observer is not None:
            observations.append(observer(pyboy, event))
        running = pyboy.tick(1, render, sound)
        tick_count += 1
        if running is False:
            stopped = True
            break
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "unified_debugger_chaos_pyboy_replay",
        "valid": True,
        "seed": schedule.get("seed"),
        "run_index": schedule.get("run_index"),
        "run_seed": schedule.get("run_seed"),
        "scheduled_frame_count": len(events),
        "executed_frame_count": tick_count,
        "stopped": stopped,
        "played_inputs": played_inputs,
        "played_input_count": len(played_inputs),
        "observations": observations,
        "observation_count": len(observations),
        "applied_perturbations": [],
        "applied_perturbation_count": 0,
        "planned_not_applied": planned_not_applied,
        "planned_not_applied_count": planned_not_applied_count,
        "public_api_methods_used": ["button", "tick"],
        "proof_boundary": [
            "PyBoy public API exposes frame ticks, delayed button events, memory, hooks, and save/load state.",
            "The current adapter does not claim cycle-level vblank/hblank, joypad-latch, or DMA-vs-CPU perturbation application; those schedule fields are preserved as planned_not_applied evidence.",
        ],
        "errors": [],
        "warnings": [],
        "error_count": 0,
        "warning_count": 0,
    }


def stable_runner(schedule: dict[str, Any]) -> Observation:
    return {
        **BASELINE_OBSERVATION,
        "input_log": ["A", "WAIT 1"],
        "run_seed": schedule["run_seed"],
    }


def synthetic_flake_runner(schedule: dict[str, Any]) -> Observation:
    for event in schedule["events"]:
        if (
            event["joypad_latch_latency_cycles"] == max(JOYPAD_LATCH_LATENCY_CYCLES)
            and event["dma_cpu_phase"] == max(DMA_CPU_PHASES)
        ):
            return {
                "status": "diverged",
                "pc": "BattleCommand_DamageCalc",
                "wCurDamage": 210,
                "input_log": ["A", f"WAIT {event['frame']}", "START"],
                "run_seed": schedule["run_seed"],
            }
    return stable_runner(schedule)


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
        f"scenario={report.get('scenario', 'custom')} runs={report.get('runs', 0)} "
        f"stable={report.get('stable_count', 0)} "
        f"divergences={report.get('divergence_count', 0)} minimal_seed={report.get('minimal_seed')}"
    )


def report_json(report: dict[str, Any]) -> str:
    return json.dumps(report, sort_keys=True)


def write_candidate_input_log(report: dict[str, Any], path: str | Path) -> dict[str, Any]:
    target = Path(path)
    events = [
        str(item)
        for item in report.get("candidate_input_log", [])
        if str(item).strip()
    ]
    artifact = {
        "path": str(target),
        "written": False,
        "event_count": len(events),
    }
    if not events:
        artifact["reason"] = "no_candidate_input_log"
        report["candidate_input_log_artifact"] = artifact
        return artifact
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(events) + "\n", encoding="utf-8")
    artifact["written"] = True
    report["candidate_input_log_artifact"] = artifact
    return artifact
