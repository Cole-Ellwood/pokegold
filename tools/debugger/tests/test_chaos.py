import json
import unittest

from tools.debugger.chaos import (
    BASELINE_OBSERVATION,
    DMA_CPU_PHASES,
    HBLANK_DELTA_CYCLES,
    JOYPAD_LATCH_LATENCY_CYCLES,
    PYBOY_PUBLIC_API_LIMIT_REASON,
    VBLANK_DELTA_CYCLES,
    build_chaos_schedule,
    drive_pyboy_with_chaos_schedule,
    format_report,
    report_json,
    run_chaos_campaign,
    run_named_chaos_scenario,
    stable_runner,
    synthetic_flake_runner,
)


class FakePyBoy:
    def __init__(self, *, stop_after_ticks: int | None = None) -> None:
        self.buttons: list[tuple[str, int]] = []
        self.ticks: list[tuple[int, bool, bool]] = []
        self.stop_after_ticks = stop_after_ticks

    def button(self, button: str, delay: int = 1) -> None:
        self.buttons.append((button, delay))

    def tick(self, count: int, render: bool, sound: bool) -> bool:
        self.ticks.append((count, render, sound))
        if self.stop_after_ticks is not None and len(self.ticks) >= self.stop_after_ticks:
            return False
        return True


class ChaosModeTests(unittest.TestCase):
    def test_chaos_determinism_given_seed(self) -> None:
        first = run_chaos_campaign(
            runs=25,
            seed=1,
            frames=8,
            baseline=BASELINE_OBSERVATION,
            runner=synthetic_flake_runner,
        )
        second = run_chaos_campaign(
            runs=25,
            seed=1,
            frames=8,
            baseline=BASELINE_OBSERVATION,
            runner=synthetic_flake_runner,
        )

        self.assertEqual(report_json(first), report_json(second))
        self.assertEqual(first["minimal_seed"], second["minimal_seed"])
        self.assertEqual(first["candidate_input_log"], second["candidate_input_log"])

    def test_chaos_catches_synthetic_flake(self) -> None:
        report = run_chaos_campaign(
            runs=100,
            seed=1,
            frames=8,
            baseline=BASELINE_OBSERVATION,
            runner=synthetic_flake_runner,
        )

        self.assertTrue(report["diverged"])
        self.assertGreater(report["divergence_count"], 0)
        self.assertIsInstance(report["minimal_seed"], int)
        self.assertIn("START", report["candidate_input_log"])
        self.assertEqual(report["divergences"][0]["run_seed"], report["minimal_seed"])

    def test_stable_scenario_stays_stable_for_100_runs(self) -> None:
        report = run_chaos_campaign(
            runs=100,
            seed=1,
            frames=8,
            baseline=BASELINE_OBSERVATION,
            runner=stable_runner,
        )

        self.assertFalse(report["diverged"])
        self.assertGreaterEqual(report["stable_count"], 99)
        self.assertEqual(report["divergence_count"], 0)

    def test_schedule_stays_inside_hardware_legal_envelope(self) -> None:
        schedule = build_chaos_schedule(seed=99, run_index=3, frames=50)

        self.assertEqual(len(schedule["events"]), 50)
        for event in schedule["events"]:
            self.assertIn(event["vblank_delta_cycles"], VBLANK_DELTA_CYCLES)
            self.assertIn(event["hblank_delta_cycles"], HBLANK_DELTA_CYCLES)
            self.assertIn(event["joypad_latch_latency_cycles"], JOYPAD_LATCH_LATENCY_CYCLES)
            self.assertIn(event["dma_cpu_phase"], DMA_CPU_PHASES)

    def test_format_and_json_helpers_expose_campaign_summary(self) -> None:
        report = run_chaos_campaign(
            runs=3,
            seed=4,
            frames=2,
            baseline=BASELINE_OBSERVATION,
            runner=stable_runner,
        )
        text = format_report(report)
        encoded = json.loads(report_json(report))

        self.assertIn("Chaos campaign", text)
        self.assertEqual(encoded["kind"], "unified_debugger_chaos_campaign")

    def test_named_scenarios_drive_cli_contract(self) -> None:
        stable = run_named_chaos_scenario(
            scenario="stable",
            runs=100,
            seed=1,
            frames=8,
        )
        flake = run_named_chaos_scenario(
            scenario="synthetic-flake",
            runs=100,
            seed=1,
            frames=8,
        )

        self.assertTrue(stable["valid"])
        self.assertFalse(stable["diverged"])
        self.assertGreaterEqual(stable["stable_count"], 99)
        self.assertTrue(flake["valid"])
        self.assertTrue(flake["diverged"])
        self.assertIn("START", flake["candidate_input_log"])

    def test_pyboy_adapter_drives_supported_frame_and_input_api(self) -> None:
        pyboy = FakePyBoy()
        schedule = build_chaos_schedule(seed=1, run_index=2, frames=3)
        input_playback = {
            "valid": True,
            "events": [
                {"frame": 0, "buttons": ["a"], "hold_frames": 2, "line": 1},
                {"frame": 1, "buttons": [], "hold_frames": 0, "line": 2},
                {"frame": 2, "buttons": ["start"], "hold_frames": 1, "line": 3},
            ],
        }

        report = drive_pyboy_with_chaos_schedule(
            pyboy,
            schedule,
            input_playback=input_playback,
            observer=lambda _pyboy, event: {"frame": event["frame"], "pc": "unit"},
        )

        self.assertTrue(report["valid"])
        self.assertEqual(report["kind"], "unified_debugger_chaos_pyboy_replay")
        self.assertEqual(pyboy.ticks, [(1, False, False), (1, False, False), (1, False, False)])
        self.assertEqual(pyboy.buttons, [("a", 2), ("start", 1)])
        self.assertEqual(report["played_input_count"], 3)
        self.assertEqual(report["observation_count"], 3)

    def test_pyboy_adapter_does_not_claim_cycle_level_perturbations(self) -> None:
        pyboy = FakePyBoy()
        schedule = build_chaos_schedule(seed=1, run_index=0, frames=2)

        report = drive_pyboy_with_chaos_schedule(pyboy, schedule)

        self.assertEqual(report["applied_perturbation_count"], 0)
        self.assertGreater(report["planned_not_applied_count"], 0)
        reasons = {item["reason"] for item in report["planned_not_applied"]}
        self.assertEqual(reasons, {PYBOY_PUBLIC_API_LIMIT_REASON})

    def test_pyboy_adapter_stops_when_pyboy_stops(self) -> None:
        pyboy = FakePyBoy(stop_after_ticks=2)
        schedule = build_chaos_schedule(seed=1, run_index=0, frames=5)

        report = drive_pyboy_with_chaos_schedule(pyboy, schedule)

        self.assertTrue(report["stopped"])
        self.assertEqual(report["executed_frame_count"], 2)


if __name__ == "__main__":
    unittest.main()
