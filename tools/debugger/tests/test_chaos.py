import json
import unittest

from tools.debugger.chaos import (
    DMA_CPU_PHASES,
    HBLANK_DELTA_CYCLES,
    JOYPAD_LATCH_LATENCY_CYCLES,
    VBLANK_DELTA_CYCLES,
    build_chaos_schedule,
    format_report,
    report_json,
    run_chaos_campaign,
)


BASELINE = {"status": "ok", "pc": "BattleCommand_DamageCalc", "wCurDamage": 42}


def stable_runner(schedule: dict) -> dict:
    return {**BASELINE, "input_log": ["A", "WAIT 1"], "run_seed": schedule["run_seed"]}


def synthetic_flake_runner(schedule: dict) -> dict:
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


class ChaosModeTests(unittest.TestCase):
    def test_chaos_determinism_given_seed(self) -> None:
        first = run_chaos_campaign(
            runs=25,
            seed=1,
            frames=8,
            baseline=BASELINE,
            runner=synthetic_flake_runner,
        )
        second = run_chaos_campaign(
            runs=25,
            seed=1,
            frames=8,
            baseline=BASELINE,
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
            baseline=BASELINE,
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
            baseline=BASELINE,
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
            baseline=BASELINE,
            runner=stable_runner,
        )
        text = format_report(report)
        encoded = json.loads(report_json(report))

        self.assertIn("Chaos campaign", text)
        self.assertEqual(encoded["kind"], "unified_debugger_chaos_campaign")


if __name__ == "__main__":
    unittest.main()
