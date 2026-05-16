from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.boss_ai_preference.benchmark_harvest import (
    build_benchmark_label_queue,
    build_benchmark_harvest_report,
    load_fixtures,
    load_preferences,
    write_benchmark_label_queue,
    write_benchmark_harvest_report,
)


class BenchmarkHarvestTests(unittest.TestCase):
    def test_harvest_finds_complete_fixture_derived_candidates(self) -> None:
        fixtures = load_fixtures()
        preferences = load_preferences(fixtures=fixtures)

        report = build_benchmark_harvest_report(fixtures, preferences)
        complete_ids = {
            row["fixture_id"] for row in report["complete_candidates"]
        }

        self.assertEqual(report["fixture_count"], 59)
        self.assertEqual(report["preference_count"], 54)
        self.assertGreaterEqual(report["complete_candidate_count"], 4)
        self.assertIn("chuck_poliwrath_vs_pidgeotto_ice_punch", complete_ids)
        self.assertIn("janine_qwilfish_finish_third_spikes_layer", complete_ids)
        self.assertIn("mechanics_snorlax_full_hp_rest_status_fail", complete_ids)
        self.assertIn("brock_golem_vs_vaporeon_explosion_question", complete_ids)

    def test_harvest_tracks_missing_acceptable_labels(self) -> None:
        fixtures = load_fixtures()
        preferences = load_preferences(fixtures=fixtures)

        report = build_benchmark_harvest_report(fixtures, preferences)

        self.assertGreater(report["missing_counts"].get("acceptable", 0), 0)
        self.assertGreater(report["partial_candidate_count"], 0)

    def test_label_queue_turns_partial_candidates_into_review_requests(self) -> None:
        fixtures = load_fixtures()
        preferences = load_preferences(fixtures=fixtures)

        queue = build_benchmark_label_queue(fixtures, preferences, limit=5)

        self.assertEqual(queue["returned_count"], 5)
        self.assertGreater(queue["one_label_completion_count"], 0)
        self.assertIn("acceptable", queue["missing_counts"])
        self.assertTrue(queue["requests"][0]["question"])
        self.assertTrue(queue["requests"][0]["suggested_command_template"])

    def test_write_harvest_report_writes_markdown_and_json(self) -> None:
        with TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "harvest.md"
            json_out_path = Path(tmpdir) / "harvest.json"

            report = write_benchmark_harvest_report(
                out_path=out_path,
                json_out_path=json_out_path,
            )

            self.assertGreaterEqual(report["complete_candidate_count"], 3)
            self.assertIn(
                "Fixture-Derived Benchmark Harvest",
                out_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                '"complete_candidate_count"',
                json_out_path.read_text(encoding="utf-8"),
            )

    def test_write_label_queue_writes_markdown_and_json(self) -> None:
        with TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "label_queue.md"
            json_out_path = Path(tmpdir) / "label_queue.json"

            report = write_benchmark_label_queue(
                out_path=out_path,
                json_out_path=json_out_path,
                limit=3,
            )

            self.assertEqual(report["returned_count"], 3)
            self.assertIn(
                "Benchmark Label Queue",
                out_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                '"one_label_completion_count"',
                json_out_path.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
