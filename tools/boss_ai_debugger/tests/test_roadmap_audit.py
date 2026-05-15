from __future__ import annotations

import unittest

from tools.audit.check_boss_ai_debugger_roadmap import (
    build_roadmap_audit,
    coverage_guided_status,
    differential_status,
    score_materialization_scenarios,
)


class RoadmapAuditTests(unittest.TestCase):
    def test_current_roadmap_audit_keeps_goal_incomplete(self) -> None:
        report = build_roadmap_audit(generated_count=24, seed=1)

        items = {item["id"]: item for item in report["items"]}

        self.assertFalse(report["ready"])
        self.assertEqual(items["canonical_state_schema"]["status"], "complete")
        self.assertEqual(items["rule_id_source_map"]["status"], "complete")
        self.assertEqual(
            items["rom_selector_materialized_generated_scenarios"]["status"],
            "partial",
        )
        self.assertEqual(
            items["rom_score_materialized_generated_scenarios"]["status"],
            "partial",
        )
        self.assertEqual(items["dynamic_public_read_provenance"]["status"], "partial")
        self.assertGreater(report["blocking_gap_count"], 0)

    def test_differential_without_matched_contributions_is_partial(self) -> None:
        differential = {
            "trace_summary": {
                "checked_count": 19,
                "failure_count": 0,
            },
            "contribution_comparison": {
                "matched_trace_count": 0,
                "mismatch_count": 0,
            },
        }

        self.assertEqual(differential_status(differential), "partial")

    def test_coverage_guided_status_tracks_uncovered_rules(self) -> None:
        coverage = {
            "rule_map": {"mapped_rule_count": 10},
            "uncovered_rules": {"uncovered_rule_count": 3},
        }

        self.assertEqual(coverage_guided_status(coverage), "partial")

    def test_score_materialization_prefers_active_revealed_spin_layers(self) -> None:
        scenarios = [
            {
                "id": "ordinary",
                "family": "spikes_spin",
                "expectation": {"condition_tags": ["spikes_layers_0"]},
            },
            {
                "id": "target",
                "family": "spikes_spin",
                "expectation": {
                    "condition_tags": [
                        "spikes_layers_2",
                        "active_revealed_rapid_spin",
                    ]
                },
            },
        ]

        selected = score_materialization_scenarios(scenarios, limit=1)

        self.assertEqual(selected[0]["id"], "target")


if __name__ == "__main__":
    unittest.main()
