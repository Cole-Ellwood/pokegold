from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.boss_ai_preference.benchmark_positions import (
    build_benchmark_policy_answers,
    load_benchmark_oracles,
    load_benchmarks,
)
from tools.boss_ai_preference.type_evidence import (
    build_type_chart_assertions,
    build_type_evidence_report,
    write_type_evidence_report,
)


class TypeEvidenceTests(unittest.TestCase):
    def test_known_romhack_type_chart_tweaks_are_source_backed(self) -> None:
        assertions = build_type_chart_assertions()
        assertions_by_id = {row["id"]: row for row in assertions}

        self.assertEqual(len(assertions), 15)
        self.assertTrue(all(row["passes"] for row in assertions))
        self.assertEqual(
            assertions_by_id["dark_steel_neutral"]["actual_hack_label"],
            "neutral",
        )
        self.assertEqual(
            assertions_by_id["ghost_steel_no_effect"]["actual_hack_label"],
            "immune",
        )

    def test_current_benchmark_and_policy_type_claims_have_evidence(self) -> None:
        benchmarks = load_benchmarks()
        oracles = load_benchmark_oracles()
        policy = build_benchmark_policy_answers(benchmarks)

        report = build_type_evidence_report(
            benchmarks,
            oracles,
            policy["answers"],
        )

        self.assertTrue(report["chart_tweaks_pass"])
        self.assertTrue(report["steel_ghost_dark_divergence_pass"])
        self.assertGreater(report["text_claim_count"], 0)
        self.assertEqual(report["unsupported_text_claim_count"], 0)
        self.assertTrue(report["all_pass"])

    def test_type_claim_without_environment_source_ref_is_rejected(self) -> None:
        benchmarks = deepcopy(load_benchmarks())
        oracles = load_benchmark_oracles()
        for benchmark in benchmarks:
            if benchmark["id"] == "romhack_defensive_answer_preservation_pryce_001":
                benchmark["source_refs"] = ["docs/boss_ai_teaching_heuristics.md"]
                break

        report = build_type_evidence_report(benchmarks, oracles, policy_answers=[])

        unsupported_locations = {
            f"{row['source_name']}:{row['benchmark_id']}"
            for row in report["unsupported_text_claims"]
        }
        self.assertIn(
            "public_card:romhack_defensive_answer_preservation_pryce_001",
            unsupported_locations,
        )
        self.assertFalse(report["all_pass"])

    def test_write_type_evidence_report_writes_markdown_and_json(self) -> None:
        with TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "type_evidence.md"
            json_out_path = Path(tmpdir) / "type_evidence.json"

            report = write_type_evidence_report(
                out_path=out_path,
                json_out_path=json_out_path,
            )

            self.assertTrue(report["all_pass"])
            self.assertIn(
                "Type-Effectiveness Evidence Report",
                out_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                '"chart_tweak_count": 15',
                json_out_path.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
