from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.coverage_report import build_coverage_report
from tools.boss_ai_debugger.mastery_index import build_mastery_index


class MasteryCoverageTests(unittest.TestCase):
    def test_mastery_index_reads_policy_cards_and_quick_tests(self) -> None:
        data = build_mastery_index()
        card_ids = {card["id"] for card in data["policy_cards"]}

        self.assertIn("hazard_loop_spin_window", card_ids)
        self.assertGreaterEqual(data["quick_test_count"], 100)
        self.assertGreaterEqual(data["source_policy_count"], 3)

    def test_coverage_report_makes_full_trace_gap_explicit(self) -> None:
        data = build_coverage_report(generated_count=20, seed=1)

        self.assertFalse(data["rule_map"]["full_trace_rule_coverage_available"])
        self.assertIn("hazard_retention", data["generated"]["policy_tag_counts"])
        self.assertGreaterEqual(data["mastery"]["policy_card_count"], 1)
        self.assertGreater(data["uncovered_rules"]["uncovered_rule_count"], 0)
        self.assertIn("suggested_generator_counts", data["uncovered_rules"])

    def test_cli_mastery_index_and_coverage_report_write_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mastery_out = Path(tmp) / "mastery.json"
            coverage_out = Path(tmp) / "coverage.json"
            contribution_trace = Path(tmp) / "rom_contribution.json"
            contribution_trace.write_text(
                json.dumps(
                    {
                        "source": "trace_rom_pyboy_hooks",
                        "save_state": "route:unit",
                        "event_count": 1,
                        "changed_event_count": 1,
                        "trace_basis": {},
                        "chosen": {},
                        "events": [
                            {
                                "changed": True,
                                "operation": "encourage_score",
                                "candidate": {
                                    "kind": "move",
                                    "slot_index": 0,
                                    "move_id": 57,
                                },
                                "source": {
                                    "rule_id": "move.cli_trace_rule",
                                    "classification": "public_info",
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                mastery_code = debugger_main(
                    [
                        "mastery-index",
                        "build",
                        "--json-out",
                        str(mastery_out),
                    ]
                )
                coverage_code = debugger_main(
                    [
                        "coverage-report",
                        "--generated-count",
                        "10",
                        "--rom-contribution-trace",
                        str(contribution_trace),
                        "--changed-file",
                        "engine/battle/ai/boss_policy_move.asm",
                        "--json-out",
                        str(coverage_out),
                    ]
                )
            mastery = json.loads(mastery_out.read_text(encoding="utf-8"))
            coverage = json.loads(coverage_out.read_text(encoding="utf-8"))

        self.assertEqual(mastery_code, 0)
        self.assertEqual(coverage_code, 0)
        self.assertIn("policy_cards", mastery)
        self.assertIn("known_gaps", coverage)
        self.assertEqual(coverage["rule_map"]["trace_covered_rule_count"], 1)
        self.assertGreater(coverage["changed_rules"]["mapped_rule_count"], 0)

    def test_coverage_report_aggregates_rom_contribution_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "rom_contribution.json"
            trace.write_text(
                json.dumps(
                    {
                        "source": "trace_rom_pyboy_hooks",
                        "save_state": "route:unit",
                        "event_count": 1,
                        "changed_event_count": 1,
                        "trace_basis": {},
                        "chosen": {},
                        "events": [
                            {
                                "changed": True,
                                "operation": "encourage_score",
                                "candidate": {
                                    "kind": "move",
                                    "slot_index": 0,
                                    "move_id": 57,
                                },
                                "source": {
                                    "rule_id": "move.unit_trace_rule",
                                    "classification": "public_info",
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            data = build_coverage_report(
                generated_count=5,
                seed=1,
                rom_contribution_trace_paths=[trace],
            )

        self.assertFalse(data["rule_map"]["full_trace_rule_coverage_available"])
        self.assertEqual(data["rule_map"]["trace_covered_rule_count"], 1)
        self.assertEqual(data["rule_map"]["trace_changed_rule_count"], 1)
        self.assertEqual(
            data["rule_map"]["trace_covered_rule_ids"],
            ["move.unit_trace_rule"],
        )

    def test_coverage_report_summarizes_changed_rule_gaps(self) -> None:
        data = build_coverage_report(
            generated_count=5,
            seed=1,
            changed_files=["engine/battle/ai/boss_policy_move.asm"],
        )

        self.assertGreater(data["changed_rules"]["mapped_rule_count"], 0)
        self.assertGreater(data["changed_rules"]["uncovered_rule_count"], 0)
        self.assertIn("uncovered_rules", data["changed_rules"])


if __name__ == "__main__":
    unittest.main()
