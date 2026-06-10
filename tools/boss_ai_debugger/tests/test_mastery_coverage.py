from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.coverage_report import (
    build_coverage_report,
    build_deity_coverage_worklist,
    deity_next_action_command,
    public_read_provenance_summary,
    summarize_contribution_sources,
)
from tools.boss_ai_debugger.mastery_index import build_mastery_index
from tools.boss_ai_debugger.rom_contribution_trace import expected_public_read_probe_outcomes


class MasteryCoverageTests(unittest.TestCase):
    def test_mastery_index_reads_policy_cards_and_quick_tests(self) -> None:
        data = build_mastery_index()
        card_ids = {card["id"] for card in data["policy_cards"]}

        self.assertIn("hazard_loop_spin_window", card_ids)
        self.assertGreaterEqual(data["quick_test_count"], 100)
        self.assertGreaterEqual(data["source_policy_count"], 3)

    def test_coverage_report_records_full_trace_coverage(self) -> None:
        data = build_coverage_report(generated_count=20, seed=1)

        self.assertTrue(data["rule_map"]["full_trace_rule_coverage_available"])
        self.assertIn("hazard_retention", data["generated"]["policy_tag_counts"])
        self.assertGreaterEqual(data["mastery"]["policy_card_count"], 1)
        self.assertIn("policy_card_requirement_coverage", data["mastery"])
        self.assertEqual(data["uncovered_rules"]["uncovered_rule_count"], 0)
        self.assertIn("suggested_generator_counts", data["uncovered_rules"])
        self.assertIn("coverage_targets", data)
        self.assertEqual(data["coverage_targets"]["group_count"], 0)
        self.assertIn("public_read_provenance", data)

    def test_deity_coverage_worklist_is_complete_when_no_witness_gaps_remain(self) -> None:
        data = build_deity_coverage_worklist(generated_count=20, seed=1, limit=3)

        self.assertEqual(data["evidence_marker"], "BOSS_AI_DEITY_COVERAGE_WORKLIST")
        self.assertIn("coverage_gap.localized", data["closed_evidence_ids"])
        self.assertNotIn("next_action.command", data["closed_evidence_ids"])
        self.assertNotIn("source_anchors.present", data["closed_evidence_ids"])
        self.assertEqual(data["coverage_basis"]["target_count"], 0)
        self.assertEqual(data["reachability_model"]["reachable_status"], "complete")
        self.assertEqual(data["top_item"], {})
        self.assertEqual(data["next_action"], {})
        self.assertEqual(data["source_anchors"], [])
        self.assertEqual(data["worklist"], [])
        self.assertEqual(data["reachability_model"]["unsupported_targets"], [])

    def test_deity_next_action_uses_required_state_family_for_faint_replacement(self) -> None:
        command = deity_next_action_command(
            generator="switch_sack",
            trace_mode="rom_route_contribution_trace",
            rule_id="switch.pick_faint_replacement",
        )

        self.assertIn("--save-state .local\\tmp\\boss_state_factory\\faint_replacement_predispatch.state", command)
        self.assertIn("--finish-on switch", command)
        self.assertNotIn("--boss-route koga", command)

    def test_deity_next_action_uses_after_player_haki_entry_state(self) -> None:
        command = deity_next_action_command(
            generator="switch_sack",
            trace_mode="rom_route_contribution_trace",
            rule_id="switch.oracle_haki_after_player_action",
        )

        self.assertIn("--save-state .local\\tmp\\boss_ai_debugger\\haki_after_player_action_entry.state", command)
        self.assertIn("wBossAIRevealedMovesBitmapSpare+1=0x04", command)
        self.assertNotIn("--boss-route koga", command)

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
        self.assertIn("dynamic_target_count", coverage["changed_rules"])
        self.assertIn("policy_card_missing_positive_count", coverage["mastery"])

    def test_cli_coverage_report_deity_worklist_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "coverage_worklist.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "coverage-report",
                        "--deity-worklist",
                        "--generated-count",
                        "10",
                        "--json-out",
                        str(out),
                    ]
                )
            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["evidence_marker"], "BOSS_AI_DEITY_COVERAGE_WORKLIST")
        self.assertIn("BOSS_AI_DEITY_COVERAGE_WORKLIST", stdout.getvalue())
        self.assertIn("closed_evidence_ids=", stdout.getvalue())
        self.assertNotIn("next_action.command", data["closed_evidence_ids"])
        self.assertNotIn("source_anchors.present", data["closed_evidence_ids"])
        self.assertEqual(data["next_action"], {})

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
        self.assertIn("score_trace_target_count", data["rule_map"])
        self.assertEqual(
            data["rule_map"]["trace_covered_rule_ids"],
            ["move.unit_trace_rule"],
        )

    def test_contribution_source_summary_keeps_artifacts_when_nested_reports_exist(self) -> None:
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
                                    "rule_id": "move.path_trace_rule",
                                    "classification": "public_info",
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            nested_report = {
                "source": "trace_rom_pyboy_hooks",
                "save_state": "route:nested",
                "event_count": 1,
                "changed_event_count": 1,
                "trace_basis": {},
                "chosen": {},
                "events": [
                    {
                        "changed": True,
                        "operation": "discourage_score",
                        "candidate": {
                            "kind": "move",
                            "slot_index": 1,
                            "move_id": 45,
                        },
                        "source": {
                            "rule_id": "move.nested_trace_rule",
                            "classification": "public_info",
                        },
                    }
                ],
            }

            summary = summarize_contribution_sources(
                rom_contribution_trace_paths=[trace],
                rom_contribution_reports=[nested_report],
            )

        self.assertEqual(summary["artifact_count"], 2)
        self.assertIn("move.path_trace_rule", summary["executed_rule_ids"])
        self.assertIn("move.nested_trace_rule", summary["executed_rule_ids"])
        self.assertIn(
            "rom_contribution.json",
            {Path(str(artifact.get("artifact", ""))).name for artifact in summary["artifacts"]},
        )
    def test_public_read_provenance_requires_exact_outcomes_and_snapshots(self) -> None:
        rule_map = {
            "rules": [
                {
                    "rule_id": "move.public_probe",
                    "requires_public_read_provenance": True,
                }
            ]
        }
        expected = expected_public_read_probe_outcomes()
        target = "boss_reserve_spinblock:available"
        observed_except_target = {outcome: 1 for outcome in expected if outcome != target}
        observed_with_wrong_neighbor = {
            **observed_except_target,
            "boss_reserve_spinblock:not_the_available_branch": 1,
        }

        missing = public_read_provenance_summary(
            rule_map,
            {
                "public_read_probe_outcome_counts": observed_with_wrong_neighbor,
                "predicate_outcome_counts": {},
                "public_read_probe_snapshot_count": 1,
                "predicate_public_input_snapshot_count": 0,
            },
        )
        without_snapshot = public_read_provenance_summary(
            rule_map,
            {
                "public_read_probe_outcome_counts": {outcome: 1 for outcome in expected},
                "predicate_outcome_counts": {},
                "public_read_probe_snapshot_count": 0,
                "predicate_public_input_snapshot_count": 0,
            },
        )
        closed = public_read_provenance_summary(
            rule_map,
            {
                "public_read_probe_outcome_counts": {outcome: 1 for outcome in expected},
                "predicate_outcome_counts": {},
                "public_read_probe_snapshot_count": 1,
                "predicate_public_input_snapshot_count": 0,
            },
        )
        unreachable = "choice_lock_risk:immune_risk"
        closed_with_unreachable_unobserved = public_read_provenance_summary(
            rule_map,
            {
                "public_read_probe_outcome_counts": {
                    outcome: 1 for outcome in expected if outcome != unreachable
                },
                "predicate_outcome_counts": {},
                "public_read_probe_snapshot_count": 1,
                "predicate_public_input_snapshot_count": 0,
            },
        )

        self.assertIn(target, missing["missing_probe_outcomes"])
        self.assertEqual(missing["missing_probe_outcome_count"], 1)
        self.assertFalse(without_snapshot["available"])
        self.assertEqual(closed["missing_probe_outcome_count"], 0)
        self.assertTrue(closed["available"])
        self.assertEqual(closed_with_unreachable_unobserved["missing_probe_outcome_count"], 0)
        self.assertEqual(
            closed_with_unreachable_unobserved["statically_unreachable_probe_outcome_count"],
            1,
        )
        self.assertEqual(
            closed_with_unreachable_unobserved["statically_unreachable_probe_outcomes"][0]["outcome"],
            unreachable,
        )

    def test_coverage_report_summarizes_changed_rule_gaps(self) -> None:
        data = build_coverage_report(
            generated_count=5,
            seed=1,
            changed_files=["engine/battle/ai/boss_policy_move.asm"],
        )

        self.assertGreater(data["changed_rules"]["mapped_rule_count"], 0)
        self.assertEqual(data["changed_rules"]["uncovered_rule_count"], 0)
        self.assertIn("uncovered_rules", data["changed_rules"])

    def test_mastery_policy_generation_has_positive_and_negative_card_coverage(self) -> None:
        data = build_coverage_report(generated_count=24, seed=1)

        self.assertEqual(data["mastery"]["policy_card_missing_positive_count"], 0)
        self.assertEqual(data["mastery"]["policy_card_missing_negative_count"], 0)


if __name__ == "__main__":
    unittest.main()
