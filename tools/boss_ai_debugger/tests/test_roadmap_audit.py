from __future__ import annotations

import unittest

from tools.audit.check_boss_ai_debugger_roadmap import (
    build_roadmap_audit,
    coverage_guided_status,
    differential_status,
    score_materialization_evidence,
    score_materialization_gaps,
    score_materialization_scenarios,
    score_materialization_status,
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
        self.assertEqual(items["dynamic_public_read_provenance"]["status"], "complete")
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
            "coverage_targets": {"target_count": 3, "group_count": 2},
        }

        self.assertEqual(coverage_guided_status(coverage), "complete")

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

    def test_score_materialization_keeps_strict_sample_to_spikes_spin(self) -> None:
        scenarios = [
            {"id": "switch", "family": "switch_sack", "expectation": {}},
            {"id": "setup", "family": "setup_heal", "expectation": {}},
            {"id": "prediction", "family": "prediction_mix", "expectation": {}},
            {"id": "support", "family": "support_handoff", "expectation": {}},
        ]

        selected = score_materialization_scenarios(scenarios, limit=10)

        self.assertEqual(selected, [])

    def test_score_materialization_status_requires_exact_score_agreement(self) -> None:
        evidence = {
            "score_materialization": {
                "checked": True,
                "available": False,
                "checked_count": 3,
                "error_count": 0,
                "score_bytes_match_count": 2,
                "selector_top_match_count": 3,
                "contribution_mismatch_count": 0,
                "hook_equivalence_checked_count": 3,
                "hook_equivalence_mismatch_count": 0,
            }
        }

        self.assertEqual(score_materialization_status(evidence), "partial")
        self.assertIn("score-byte agreement", "\n".join(score_materialization_gaps(evidence)))

    def test_score_materialization_evidence_handles_checked_unavailable_schema(self) -> None:
        evidence = {
            "score_materialization": {
                "checked": True,
                "available": False,
                "reason": "base state missing",
            }
        }

        text = score_materialization_evidence(evidence)

        self.assertIn("score_checked=0", text)
        self.assertIn("errors=0", text)
        self.assertIn("reason=base state missing", text)


if __name__ == "__main__":
    unittest.main()
