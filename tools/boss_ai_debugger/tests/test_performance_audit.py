from __future__ import annotations

import unittest

from tools.audit.check_boss_ai_debugger_performance import (
    avoidable_duplicate_lesson_rate,
    performance_errors,
)


class PerformanceAuditTests(unittest.TestCase):
    def test_avoidable_duplicate_rate_ignores_unavoidable_repeats(self) -> None:
        queue = {
            "items": [
                {"lesson_key": "hazard"},
                {"lesson_key": "hazard"},
                {"lesson_key": "hazard"},
            ]
        }

        self.assertEqual(avoidable_duplicate_lesson_rate(queue, {"hazard"}), 0.0)

    def test_avoidable_duplicate_rate_counts_skipped_available_lessons(self) -> None:
        queue = {
            "items": [
                {"lesson_key": "hazard"},
                {"lesson_key": "hazard"},
                {"lesson_key": "cashout"},
            ]
        }

        self.assertAlmostEqual(
            avoidable_duplicate_lesson_rate(queue, {"hazard", "cashout"}),
            1 / 3,
        )

    def test_performance_errors_use_thresholds(self) -> None:
        report = {
            "min_scenarios_per_minute": 10_000,
            "min_reviewable_checks_per_minute": 1_000,
            "min_queue_inputs_per_minute": 10_000,
            "min_rom_backed_replay_per_minute": 10_000,
            "max_duplicate_lesson_rate": 0.1,
            "batch": {
                "scenarios_per_minute": 9_000,
                "reviewable_count": 5,
                "reviewable_per_minute": 900,
            },
            "queue": {
                "queue_inputs_per_minute": 9_000,
                "avoidable_duplicate_lesson_rate": 0.2,
            },
            "rom_backed_replay": {
                "error_count": 2,
                "materializations_per_minute": 9_000,
            },
        }

        self.assertEqual(len(performance_errors(report)), 6)


if __name__ == "__main__":
    unittest.main()
