from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.boss_ai_preference.long_battle_review import (
    REQUIRED_CHECKLIST_FIELDS,
    build_long_battle_review_report,
    constructed_long_battle_review,
    validate_long_battle_review,
    write_long_battle_review_report,
)


class LongBattleReviewTests(unittest.TestCase):
    def test_constructed_review_has_full_ledger_and_earliest_error(self) -> None:
        report = build_long_battle_review_report()
        review = report["reviews"][0]

        self.assertTrue(report["reviews_valid"])
        self.assertEqual(report["turn_count"], 32)
        self.assertEqual(len(review["ledger_entries"]), 32)
        self.assertEqual(report["earliest_meaningful_error"]["turn"], 9)
        self.assertEqual(
            report["earliest_meaningful_error"]["error_class"],
            "OVERFITTED_SCRIPT_ERROR",
        )
        self.assertGreaterEqual(report["benchmark_extraction_count"], 3)
        self.assertEqual(
            report["damage_context_evidence"][0]["id"],
            "romhack_spinblock_damage_context_001",
        )
        self.assertIn(
            "romhack source stats",
            report["damage_context_evidence"][0]["transfer_warning"],
        )
        for entry in review["ledger_entries"]:
            self.assertLessEqual(REQUIRED_CHECKLIST_FIELDS, set(entry["checklist"]))

    def test_validator_rejects_short_review(self) -> None:
        review = constructed_long_battle_review()
        review["turn_count"] = 29

        errors = validate_long_battle_review(review)

        self.assertIn("review must cover at least 30 turns", errors)
        self.assertIn("ledger_entries count must match turn_count", errors)

    def test_write_long_battle_review_report_writes_markdown_and_json(self) -> None:
        with TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "long_battle.md"
            json_out_path = Path(tmpdir) / "long_battle.json"

            report = write_long_battle_review_report(
                out_path=out_path,
                json_out_path=json_out_path,
            )

            self.assertTrue(report["reviews_valid"])
            self.assertIn(
                "Long Battle Review Report",
                out_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                '"turn_count": 32',
                json_out_path.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
