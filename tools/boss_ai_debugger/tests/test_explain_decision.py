from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools.boss_ai_preference.data import PreferenceDataError
from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.explain_decision import (
    explain_decision_from_path,
    explain_decision_from_trace_paths,
    format_explain_decision,
)
from tools.boss_ai_debugger.generators import write_jsonl


class ExplainDecisionTests(unittest.TestCase):
    def test_explanation_packet_combines_scores_rom_contributions_and_next_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            scenarios_path = root / "scenarios.jsonl"
            score_path = root / "rom_score.json"
            contribution_path = root / "rom_contribution.json"
            write_jsonl([explain_scenario()], scenarios_path)
            score_path.write_text(
                json.dumps(score_materialization_report(), indent=2),
                encoding="utf-8",
            )
            contribution_path.write_text(
                json.dumps(rom_contribution_report(), indent=2),
                encoding="utf-8",
            )

            report = explain_decision_from_path(
                scenarios_path,
                scenario_id="explain_case",
                focus_action_id="b",
                rom_score_materialization_paths=[score_path],
                rom_contribution_trace_paths=[contribution_path],
                decision_input={
                    "target": {
                        "score_rule": "move.apply_lookahead_to_top_move_candidates",
                    },
                    "resolution": {
                        "source": "generated_scenario",
                    },
                },
            )
            text = format_explain_decision(report)

        self.assertEqual(report["observed_rom_decision"]["kind"], "rom_score_materialization")
        self.assertTrue(report["python_mirror"]["rom_comparison"]["score_bytes_match"])
        self.assertEqual(report["rom_contributions"]["event_count"], 1)
        self.assertEqual(
            report["rom_contributions"]["events"][0]["source_anchor"]["anchor_status"],
            "mapped",
        )
        selector_path = report["observed_rom_decision"]["decision"]["selector_path"]
        self.assertEqual(selector_path["source"], "rom_score_materialization_final_scores")
        self.assertEqual(selector_path["best_action_id"], "a")
        self.assertEqual(selector_path["second_action_id"], "b")
        self.assertEqual(selector_path["possible_action_ids"], ["a", "b"])
        self.assertEqual(report["counterfactual"]["focus_score_flip"]["action_id"], "b")
        self.assertEqual(report["proof_status"]["missing_ids"], [])
        self.assertIn("score_rule.rom_delta_observed", report["proof_status"]["present_ids"])
        self.assertIn("public_reads.snapshotted", report["proof_status"]["present_ids"])
        self.assertIn("python_contribution.normalized", report["proof_status"]["present_ids"])
        self.assertIn("rom_python_agreement.reported", report["proof_status"]["present_ids"])
        self.assertEqual(report["decision_summary"]["status"], "explained")
        self.assertIn("ROM score bytes make a best", report["decision_summary"]["observed"])
        self.assertIn("selector best=a", report["decision_summary"]["path"])
        selector_choice = report["decision_summary"]["selector_choice_explanation"]
        self.assertEqual(selector_choice["chosen_rank"], "unknown")
        self.assertEqual(selector_choice["best_action_id"], "a")
        policy = report["decision_summary"]["policy_expectation"]
        self.assertTrue(policy["available"])
        self.assertEqual(policy["policy_verdict"], "pass")
        self.assertEqual(policy["expected_best_action_ids"], ["a"])
        self.assertEqual(policy["why"], "unit explanation")
        focus = report["decision_summary"]["focus_action_comparison"]
        self.assertTrue(focus["found"])
        self.assertEqual(focus["action_id"], "b")
        self.assertEqual(focus["chosen_action_id"], "a")
        self.assertEqual(focus["score_delta_vs_chosen"], 2)
        self.assertFalse(focus["is_observed_choice"])
        self.assertIn("scored worse", focus["score_reason"])
        self.assertEqual(
            focus["focus_rule_deltas"][0]["rule_id"],
            "move.apply_lookahead_to_top_move_candidates",
        )
        self.assertEqual(focus["focus_rule_deltas"][0]["delta"], 0)
        self.assertEqual(
            focus["chosen_rule_deltas"][0]["rule_id"],
            "move.apply_lookahead_to_top_move_candidates",
        )
        self.assertEqual(
            focus["chosen_rule_deltas"][0]["source"],
            "rom_contribution_trace",
        )
        self.assertEqual(focus["chosen_rule_deltas"][0]["delta"], -2)
        self.assertEqual(focus["selector_explanation"]["rank"], "second")
        evidence = report["decision_summary"]["evidence_highlights"]
        self.assertEqual(evidence["candidate_scores"][0]["action_id"], "a")
        self.assertEqual(evidence["rule_deltas"][0]["source"], "rom_contribution_trace")
        self.assertEqual(
            evidence["rule_deltas"][0]["rule_id"],
            "move.apply_lookahead_to_top_move_candidates",
        )
        self.assertTrue(
            any("condition_tags=" in item for item in evidence["public_inputs"])
        )
        self.assertEqual(
            report["proof_status"]["next_proof_command"]["purpose"],
            "Python score waterfall and selector surface",
        )
        self.assertIn("decision-trace", report["next_proof_commands"][0]["command"])
        self.assertIn("Answer: status=explained", text)
        self.assertIn("policy=verdict=pass; expected_best=a", text)
        self.assertIn("why=unit explanation", text)
        self.assertIn("focus=b score=20", text)
        self.assertIn("delta_vs_chosen=2", text)
        self.assertIn("focus_reason=focused action scored worse", text)
        self.assertIn("focus_selector=selector switch hedge", text)
        self.assertIn("focus_rules=b move.apply_lookahead_to_top_move_candidates", text)
        self.assertIn("chosen_rules=a move.apply_lookahead_to_top_move_candidates", text)
        self.assertIn("selector=no sampled chosen action", text)
        self.assertIn("scores=a=18", text)
        self.assertIn("rules=A move.apply_lookahead_to_top_move_candidates", text)
        self.assertIn("public=condition_tags=", text)
        self.assertIn("Observed ROM", text)
        self.assertIn("Proof status", text)
        self.assertIn("selector best=a", text)
        self.assertIn("Next proof commands", text)

    def test_explanation_rejects_wrong_rom_materialization_artifact_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            scenarios_path = root / "scenarios.jsonl"
            score_path = root / "not_rom_score.json"
            write_jsonl([explain_scenario()], scenarios_path)
            score_path.write_text(
                json.dumps(
                    {
                        "changed_ai_run": {
                            "artifacts": {
                                "rom_score_materialization": "real_report.json",
                            },
                        },
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                PreferenceDataError,
                "expected rom_score_materialization report",
            ):
                explain_decision_from_path(
                    scenarios_path,
                    scenario_id="explain_case",
                    rom_score_materialization_paths=[score_path],
                )

    def test_cli_explain_decision_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            scenarios_path = root / "scenarios.jsonl"
            out = root / "explain.json"
            write_jsonl([explain_scenario()], scenarios_path)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "explain-decision",
                        "--scenario",
                        str(scenarios_path),
                        "--scenario-id",
                        "explain_case",
                        "--focus-action-id",
                        "b",
                        "--json-out",
                        str(out),
                    ]
                )
            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["scenario_id"], "explain_case")
        self.assertIn("observed_rom_decision", data["proof_status"]["missing_ids"])
        self.assertEqual(data["decision_summary"]["status"], "needs_rom_proof")
        self.assertIn(
            "pending ROM proof; Python mirror best=a score=18",
            data["decision_summary"]["why"],
        )
        self.assertIn(
            "--run-rom-proof auto",
            data["decision_summary"]["next_proof_command"]["command"],
        )
        self.assertIn("--run-rom-proof auto", data["proof_status"]["next_proof_command"]["command"])
        self.assertIn("--focus-action-id b", data["proof_status"]["next_proof_command"]["command"])
        self.assertEqual(
            data["proof_status"]["next_proof_command"]["closes_evidence_ids"],
            ["observed_rom_decision", "score_bytes", "selector_path"],
        )
        self.assertEqual(
            data["proof_status"]["next_proof_command"]["expected_output_paths"],
            [".local\\tmp\\boss_ai_debugger\\explain_case_rom_proof.json"],
        )
        self.assertIn("Boss AI decision explanation", stdout.getvalue())
        self.assertIn("Answer: status=needs_rom_proof", stdout.getvalue())
        self.assertIn(
            "why=pending ROM proof; Python mirror best=a score=18",
            stdout.getvalue(),
        )
        self.assertIn(
            "next_meta=closes=observed_rom_decision,score_bytes,selector_path; "
            "writes=.local\\tmp\\boss_ai_debugger\\explain_case_rom_proof.json",
            stdout.getvalue(),
        )

    def test_policy_expectation_summary_names_bad_rolls(self) -> None:
        scenario = {
            "id": "bad_roll_case",
            "family": "selector_edges",
            "tier": "late",
            "selector_hedge_action_id": "bad_branch",
            "moves": [
                {"id": "safe", "name": "Safe"},
                {"id": "bad_branch", "name": "Bad Branch"},
            ],
            "expectation": {
                "best_action_ids": ["safe"],
                "bad_action_ids": ["bad_branch"],
                "policy_tags": ["selector_surface"],
                "condition_tags": ["near_tie"],
                "why": "bad branch should not receive roll odds",
            },
        }
        with tempfile.TemporaryDirectory() as temporary_dir:
            scenarios_path = Path(temporary_dir) / "scenarios.jsonl"
            write_jsonl([scenario], scenarios_path)

            report = explain_decision_from_path(
                scenarios_path,
                scenario_id="bad_roll_case",
            )
            text = format_explain_decision(report)

        policy = report["decision_summary"]["policy_expectation"]
        self.assertTrue(policy["available"])
        self.assertEqual(policy["policy_verdict"], "bad_roll")
        self.assertEqual(policy["expected_best_action_ids"], ["safe"])
        self.assertEqual(policy["expected_bad_action_ids"], ["bad_branch"])
        self.assertEqual(policy["rolled_bad_action_ids"], ["bad_branch"])
        self.assertIn(
            "policy=verdict=bad_roll; expected_best=safe; bad=bad_branch; rolled_bad=bad_branch",
            text,
        )
        self.assertIn("why=bad branch should not receive roll odds", text)

    def test_unfocused_pass_scenario_counterfactual_uses_nearest_challenger(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            scenarios_path = Path(temporary_dir) / "scenarios.jsonl"
            write_jsonl([explain_scenario()], scenarios_path)

            report = explain_decision_from_path(
                scenarios_path,
                scenario_id="explain_case",
            )
            text = format_explain_decision(report)

        self.assertEqual(report["counterfactual"]["smallest_score_flip"]["action_id"], "a")
        self.assertEqual(report["counterfactual"]["smallest_score_flip"]["required_delta"], 0)
        self.assertEqual(
            report["counterfactual"]["nearest_challenger_score_flip"]["action_id"],
            "b",
        )
        self.assertIn("counterfactual=b score 20 -> 17 delta=-3", text)
        self.assertIn("Counterfactual: b score 20 -> 17 delta=-3", text)
        self.assertNotIn("Counterfactual: a score 18 -> 18 delta=0", text)

    def test_scenario_focus_counterfactual_accepts_candidate_name_alias(self) -> None:
        scenario = {
            "id": "alias_case",
            "family": "spikes_spin",
            "tier": "late",
            "moves": [
                {
                    "id": "needle",
                    "name": "Needle Arm",
                    "deltas": [{"rule": "lookahead", "delta": -2}],
                },
                {"id": "recover_action", "name": "Recover"},
            ],
            "expectation": {
                "best_action_ids": ["needle"],
                "policy_tags": [],
                "condition_tags": [],
            },
        }
        with tempfile.TemporaryDirectory() as temporary_dir:
            scenarios_path = Path(temporary_dir) / "scenarios.jsonl"
            write_jsonl([scenario], scenarios_path)

            report = explain_decision_from_path(
                scenarios_path,
                scenario_id="alias_case",
                focus_action_id="Recover",
            )
            text = format_explain_decision(report)

        focus = report["decision_summary"]["focus_action_comparison"]
        self.assertTrue(focus["found"])
        self.assertEqual(focus["action_id"], "recover_action")
        flip = report["counterfactual"]["focus_score_flip"]
        self.assertTrue(flip["available"])
        self.assertEqual(flip["requested_action_id"], "Recover")
        self.assertEqual(flip["action_id"], "recover_action")
        self.assertEqual(flip["required_delta"], -3)
        self.assertIn("needs_delta=-3", focus["summary"])
        self.assertIn("Counterfactual: recover_action score 20 -> 17 delta=-3", text)
        self.assertNotIn("flip_unavailable", text)

    def test_scenario_focus_counterfactual_accepts_move_id_alias(self) -> None:
        scenario = {
            "id": "move_id_alias_case",
            "family": "spikes_spin",
            "tier": "late",
            "moves": [
                {
                    "id": "needle",
                    "name": "Needle Arm",
                    "move_id": 10,
                    "deltas": [{"rule": "lookahead", "delta": -2}],
                },
                {
                    "id": "recover_action",
                    "name": "Recover",
                    "move_id": 105,
                },
            ],
            "expectation": {
                "best_action_ids": ["needle"],
                "policy_tags": [],
                "condition_tags": [],
            },
        }
        with tempfile.TemporaryDirectory() as temporary_dir:
            scenarios_path = Path(temporary_dir) / "scenarios.jsonl"
            write_jsonl([scenario], scenarios_path)

            report = explain_decision_from_path(
                scenarios_path,
                scenario_id="move_id_alias_case",
                focus_action_id="105",
            )
            text = format_explain_decision(report)

        focus = report["decision_summary"]["focus_action_comparison"]
        self.assertTrue(focus["found"])
        self.assertEqual(focus["action_id"], "recover_action")
        self.assertEqual(focus["move_id"], 105)
        flip = report["counterfactual"]["focus_score_flip"]
        self.assertTrue(flip["available"])
        self.assertEqual(flip["requested_action_id"], "105")
        self.assertEqual(flip["action_id"], "recover_action")
        self.assertEqual(flip["move_id"], 105)
        self.assertEqual(flip["required_delta"], -3)
        self.assertIn("focus=recover_action score=20", text)
        self.assertIn("Counterfactual: recover_action score 20 -> 17 delta=-3", text)
        self.assertNotIn("focus=105 missing", text)

    def test_missing_scenario_focus_lists_available_candidate_aliases(self) -> None:
        scenario = {
            "id": "missing_alias_case",
            "family": "spikes_spin",
            "tier": "late",
            "moves": [
                {
                    "id": "needle",
                    "name": "Needle Arm",
                    "move_id": 10,
                    "deltas": [{"rule": "lookahead", "delta": -2}],
                },
                {
                    "id": "recover_action",
                    "name": "Recover",
                    "move_id": 105,
                },
            ],
            "expectation": {
                "best_action_ids": ["needle"],
                "policy_tags": [],
                "condition_tags": [],
            },
        }
        with tempfile.TemporaryDirectory() as temporary_dir:
            scenarios_path = Path(temporary_dir) / "scenarios.jsonl"
            write_jsonl([scenario], scenarios_path)

            report = explain_decision_from_path(
                scenarios_path,
                scenario_id="missing_alias_case",
                focus_action_id="Hydro Pump",
            )
            text = format_explain_decision(report)

        focus = report["decision_summary"]["focus_action_comparison"]
        self.assertFalse(focus["found"])
        self.assertEqual(focus["available_action_count"], 2)
        self.assertEqual(focus["available_actions"][0]["action_label"], "needle")
        self.assertIn("Needle Arm", focus["available_actions"][0]["aliases"])
        self.assertIn(
            "available=needle(Needle Arm), recover_action(Recover)",
            text,
        )
        self.assertIn("focus=Hydro Pump missing", text)
        self.assertNotIn("score None -> None", text)

    def test_scenario_rom_evidence_prioritizes_rom_contribution_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            scenarios_path = root / "scenarios.jsonl"
            score_path = root / "rom_score.json"
            write_jsonl([explain_scenario()], scenarios_path)
            score_path.write_text(
                json.dumps(score_materialization_report(), indent=2),
                encoding="utf-8",
            )

            report = explain_decision_from_path(
                scenarios_path,
                scenario_id="explain_case",
                focus_action_id="b",
                rom_score_materialization_paths=[score_path],
            )
            text = format_explain_decision(report)

        self.assertIn("rom_contribution_deltas", report["proof_status"]["missing_ids"])
        self.assertEqual(
            report["proof_status"]["next_proof_command"]["purpose"],
            "Live-route ROM contribution trace for rule/source/public-read evidence",
        )
        self.assertIn(
            "rom-contribution-trace",
            report["proof_status"]["next_proof_command"]["command"],
        )
        chain = report["proof_status"]["next_proof_chain"]
        self.assertEqual(
            chain[0]["purpose"],
            "Live-route ROM contribution trace for rule/source/public-read evidence",
        )
        self.assertEqual(
            chain[0]["closes_evidence_ids"],
            ["rom_contribution_deltas", "rom_public_read_provenance"],
        )
        self.assertEqual(
            chain[0]["expected_output_paths"],
            [".local\\tmp\\boss_ai_debugger\\explain_case_rom_contribution.json"],
        )
        self.assertEqual(
            chain[1]["purpose"],
            "Re-render this scenario packet after contribution capture",
        )
        self.assertEqual(
            chain[1]["closes_evidence_ids"],
            ["rom_contribution_deltas", "rom_public_read_provenance"],
        )
        self.assertEqual(
            chain[1]["consumes_artifact_paths"],
            [".local\\tmp\\boss_ai_debugger\\explain_case_rom_contribution.json"],
        )
        self.assertIn("--focus-action-id b", chain[1]["command"])
        self.assertIn("--run-rom-proof auto", chain[1]["command"])
        self.assertIn("--rom-contribution-trace", chain[1]["command"])
        self.assertIn(
            "next=Live-route ROM contribution trace for rule/source/public-read evidence",
            text,
        )
        self.assertIn(
            "next_meta=closes=rom_contribution_deltas,rom_public_read_provenance; "
            "writes=.local\\tmp\\boss_ai_debugger\\explain_case_rom_contribution.json",
            text,
        )
        self.assertIn("then=Re-render this scenario packet after contribution capture", text)
        self.assertIn(
            "then_meta=closes=rom_contribution_deltas,rom_public_read_provenance; "
            "uses=.local\\tmp\\boss_ai_debugger\\explain_case_rom_contribution.json",
            text,
        )

    def test_switch_scenario_marks_switch_materialization_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            scenarios_path = root / "switch_scenarios.jsonl"
            write_jsonl([switch_scenario()], scenarios_path)

            report = explain_decision_from_path(
                scenarios_path,
                scenario_id="switch_case",
                focus_action_id="preserve_switch",
            )
            text = format_explain_decision(report)

        self.assertIn("switch_materialization", report["proof_status"]["missing_ids"])
        self.assertEqual(report["candidate_scores"][1]["kind"], "switch")
        self.assertEqual(
            report["proof_status"]["next_proof_command"]["purpose"],
            "Exact one-scenario ROM proof: switch-dispatch packet",
        )
        self.assertIn("--run-rom-proof auto", report["proof_status"]["next_proof_command"]["command"])
        self.assertIn(
            "--focus-action-id preserve_switch",
            report["proof_status"]["next_proof_command"]["command"],
        )
        self.assertIn("preserve_switch[switch]=18", text)
        self.assertIn("focus=preserve_switch[switch] score=18", text)
        self.assertIn("slot=2 preserve_switch[switch]", text)

    def test_switch_materialization_is_complete_for_switch_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            scenarios_path = root / "switch_scenarios.jsonl"
            switch_path = root / "rom_switch.json"
            write_jsonl([switch_scenario()], scenarios_path)
            switch_path.write_text(
                json.dumps(switch_materialization_report(), indent=2),
                encoding="utf-8",
            )

            report = explain_decision_from_path(
                scenarios_path,
                scenario_id="switch_case",
                rom_switch_materialization_paths=[switch_path],
            )

        self.assertEqual(report["proof_status"]["missing_ids"], [])
        self.assertEqual(report["proof_status"]["status"], "explained")
        self.assertEqual(report["deity_evidence_marker"], "BOSS_AI_DEITY_PROOF_COMPLETE")
        self.assertIn("switch_materialization.proven", report["proof_status"]["present_ids"])
        self.assertIn("switch_roll.reported", report["proof_status"]["present_ids"])

    def test_selector_materialization_explanation_includes_selector_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            scenarios_path = root / "scenarios.jsonl"
            selector_path = root / "rom_selector.json"
            write_jsonl([explain_scenario()], scenarios_path)
            selector_path.write_text(
                json.dumps(selector_materialization_report(), indent=2),
                encoding="utf-8",
            )

            report = explain_decision_from_path(
                scenarios_path,
                scenario_id="explain_case",
                rom_selector_materialization_paths=[selector_path],
            )
            text = format_explain_decision(report)

        decision = report["observed_rom_decision"]["decision"]
        self.assertEqual(report["observed_rom_decision"]["kind"], "rom_selector_materialization")
        self.assertEqual(decision["selector_path"]["source"], "rom_selector_materialization_patched_score_bytes")
        self.assertEqual(decision["selector_path"]["best_action_id"], "a")
        self.assertEqual(decision["selector_path"]["second_action_id"], "b")
        self.assertEqual(decision["selector_path"]["chosen_action_id"], "a")
        self.assertTrue(decision["selector_path"]["chosen_has_nonzero_probability"])
        selector_choice = report["decision_summary"]["selector_choice_explanation"]
        self.assertEqual(selector_choice["chosen_rank"], "best")
        self.assertEqual(selector_choice["chosen_probability"], 0.625)
        self.assertIn("selector=chosen best candidate", text)
        self.assertIn("selector best=a", text)

    def test_trace_only_explanation_uses_live_score_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            trace_path = Path(temporary_dir) / "trace_live.txt"
            trace_path.write_text(
                "\n".join(
                    [
                        "boss=Trace Boss",
                        "tier=3",
                        "move_ids=1,2,3,4",
                        "move_scores=10,20,30,40",
                        "pre_model_scores=20,20,20,20",
                        "post_model_scores=10,20,30,40",
                        "model_score_deltas=-10,+0,+10,+20",
                        "chosen_slot=0",
                        "chosen_id=1",
                        "chosen=POUND",
                        "switch_confidence=0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = explain_decision_from_trace_paths(
                [trace_path],
                focus_action_id="KARATE_CHOP",
            )
            text = format_explain_decision(report)

        self.assertEqual(report["family"], "live_trace")
        self.assertEqual(report["observed_rom_decision"]["kind"], "live_trace_selector_replay")
        self.assertTrue(report["python_mirror"]["rom_comparison"]["agreement"])
        self.assertEqual(report["candidate_scores"][0]["final_score"], 10)
        selector_path = report["observed_rom_decision"]["decision"]["selector_path"]
        decision = report["observed_rom_decision"]["decision"]
        self.assertEqual(decision["chosen_slot_index"], 0)
        self.assertEqual(decision["chosen_slot_1_based"], 1)
        self.assertEqual(decision["possible_action_ids"], ["slot1:IRON_HEAD"])
        self.assertEqual(decision["possible_move_ids"], [1])
        self.assertEqual(selector_path["best_action_id"], "slot1:IRON_HEAD")
        self.assertIsNone(selector_path["second_action_id"])
        self.assertEqual(selector_path["possible_action_ids"], ["slot1:IRON_HEAD"])
        self.assertTrue(selector_path["chosen_has_nonzero_probability"])
        self.assertIn(
            "move.select_move",
            {anchor["rule_id"] for anchor in report["source_anchors"]},
        )
        self.assertIn("rom_contribution_deltas", report["proof_status"]["missing_ids"])
        self.assertIn(
            "rom-contribution-trace",
            report["proof_status"]["next_proof_command"]["command"],
        )
        self.assertEqual(report["decision_summary"]["status"], "needs_contribution_proof")
        self.assertIn("ROM live trace chose POUND", report["decision_summary"]["observed"])
        self.assertIn("slot=1", report["decision_summary"]["observed"])
        self.assertIn("selector best=slot1:IRON_HEAD", report["decision_summary"]["path"])
        selector_choice = report["decision_summary"]["selector_choice_explanation"]
        self.assertEqual(selector_choice["chosen_rank"], "best")
        self.assertEqual(selector_choice["chosen_action_id"], "slot1:IRON_HEAD")
        focus = report["decision_summary"]["focus_action_comparison"]
        self.assertTrue(focus["found"])
        self.assertEqual(focus["action_id"], "slot2:KARATE_CHOP")
        self.assertEqual(focus["chosen_action_id"], "slot1:IRON_HEAD")
        self.assertEqual(focus["score_delta_vs_chosen"], 10)
        self.assertIn("scored worse", focus["score_reason"])
        self.assertEqual(focus["selector_explanation"]["rank"], "outside_selector_roll")
        self.assertEqual(focus["focus_rule_deltas"][0]["rule_id"], "live_trace.model_score_delta")
        self.assertEqual(focus["chosen_rule_deltas"][0]["rule_id"], "live_trace.model_score_delta")
        self.assertIn(
            "rom-contribution-trace",
            report["decision_summary"]["next_proof_command"]["command"],
        )
        evidence = report["decision_summary"]["evidence_highlights"]
        self.assertEqual(evidence["candidate_scores"][0]["final_score"], 10)
        self.assertEqual(evidence["rule_deltas"][0]["source"], "python_or_live_score_delta")
        self.assertIn("trace.boss=Trace Boss", evidence["public_inputs"])
        self.assertIn("trace-replay", report["next_proof_commands"][0]["command"])
        rerender_commands = [
            item["command"]
            for item in report["next_proof_commands"]
            if item["purpose"] == "Re-render this live-trace packet after contribution capture"
        ]
        self.assertEqual(len(rerender_commands), 1)
        self.assertIn("--focus-action-id KARATE_CHOP", rerender_commands[0])
        self.assertIn("--rom-contribution-trace", rerender_commands[0])
        chain = report["proof_status"]["next_proof_chain"]
        self.assertEqual(
            chain[0]["purpose"],
            "Capture ROM score-rule contribution deltas for this route",
        )
        self.assertEqual(
            chain[0]["expected_output_paths"],
            [".local\\tmp\\boss_ai_debugger\\Trace_Boss_1_rom_contribution.json"],
        )
        self.assertEqual(
            chain[1]["purpose"],
            "Re-render this live-trace packet after contribution capture",
        )
        self.assertEqual(
            chain[1]["closes_evidence_ids"],
            ["rom_contribution_deltas", "rom_public_read_provenance"],
        )
        self.assertEqual(
            chain[1]["consumes_artifact_paths"],
            [".local\\tmp\\boss_ai_debugger\\Trace_Boss_1_rom_contribution.json"],
        )
        self.assertIn("--focus-action-id KARATE_CHOP", chain[1]["command"])
        self.assertEqual(
            report["decision_summary"]["next_proof_chain"][1]["purpose"],
            "Re-render this live-trace packet after contribution capture",
        )
        self.assertIn("chosen=POUND", text)
        self.assertIn("slot=1 slot_index=0", text)
        self.assertIn("possible_actions=['slot1:IRON_HEAD']", text)
        self.assertIn("focus=slot2:KARATE_CHOP score=20", text)
        self.assertIn("delta_vs_chosen=10", text)
        self.assertIn("focus_selector=outside nonzero selector set", text)
        self.assertIn("focus_rules=slot2:KARATE_CHOP live_trace.model_score_delta", text)
        self.assertIn("chosen_rules=slot1:IRON_HEAD live_trace.model_score_delta", text)
        self.assertIn("selector=chosen best candidate", text)
        self.assertIn("rules=slot1:IRON_HEAD live_trace.model_score_delta", text)
        self.assertIn("public=trace.boss=Trace Boss", text)
        self.assertIn(
            "then=Re-render this live-trace packet after contribution capture",
            text,
        )
        self.assertIn("Proof status", text)
        self.assertIn("selector best=slot1:IRON_HEAD", text)

    def test_trace_explanation_names_second_best_selector_roll(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            trace_path = Path(temporary_dir) / "trace_live.txt"
            trace_path.write_text(
                "\n".join(
                    [
                        "boss=Trace Boss",
                        "tier=3",
                        "move_ids=1,2,3,4",
                        "move_scores=10,10,30,40",
                        "selector_hedge_slot=1",
                        "chosen_slot=1",
                        "chosen_id=2",
                        "chosen=KARATE_CHOP",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = explain_decision_from_trace_paths([trace_path], focus_action_id="3")
            text = format_explain_decision(report)

        selector_choice = report["decision_summary"]["selector_choice_explanation"]
        self.assertEqual(selector_choice["chosen_rank"], "second")
        self.assertEqual(selector_choice["chosen_action_id"], "slot2:KARATE_CHOP")
        self.assertGreater(selector_choice["chosen_probability"], 0.0)
        self.assertIn("public switch hedge", selector_choice["reason"])
        selector_roll = report["counterfactual"]["selector_roll_counterfactual"]
        self.assertTrue(selector_roll["available"])
        self.assertTrue(selector_roll["observed_choice_due_to_random_roll"])
        self.assertEqual(selector_roll["alternate_action_id"], "slot1:IRON_HEAD")
        self.assertEqual(selector_roll["alternate_roll_range"]["min"], 0)
        self.assertIn(
            "selector roll chose second candidate",
            report["decision_summary"]["decisive_counterfactual"],
        )
        focus = report["decision_summary"]["focus_action_comparison"]
        self.assertTrue(focus["found"])
        self.assertEqual(focus["selector_explanation"]["rank"], "outside_selector_roll")
        self.assertIn("zero selector probability", focus["selector_explanation"]["reason"])
        self.assertIn("selector=chosen switch hedge via selector roll", text)
        self.assertIn("Selector roll counterfactual", text)
        self.assertIn("focus_selector=outside nonzero selector set", text)

    def test_live_trace_focus_counterfactual_accepts_slot_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            trace_path = Path(temporary_dir) / "trace_live.txt"
            trace_path.write_text(
                "\n".join(
                    [
                        "boss=Trace Boss",
                        "tier=3",
                        "move_ids=1,2,3,4",
                        "move_scores=10,20,30,40",
                        "chosen_slot=0",
                        "chosen_id=1",
                        "chosen=POUND",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = explain_decision_from_trace_paths([trace_path], focus_action_id="slot2")
            text = format_explain_decision(report)

        focus = report["decision_summary"]["focus_action_comparison"]
        self.assertTrue(focus["found"])
        self.assertEqual(focus["action_id"], "slot2:KARATE_CHOP")
        flip = report["counterfactual"]["focus_score_flip"]
        self.assertTrue(flip["available"])
        self.assertEqual(flip["action_id"], "slot2:KARATE_CHOP")
        self.assertEqual(flip["slot"], 2)
        self.assertIn("Counterfactual: slot2:KARATE_CHOP score 20 -> 9 delta=-11", text)

    def test_missing_focus_counterfactual_prints_reason_not_none_scores(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            trace_path = Path(temporary_dir) / "trace_live.txt"
            trace_path.write_text(
                "\n".join(
                    [
                        "boss=Trace Boss",
                        "tier=3",
                        "move_ids=1,2,3,4",
                        "move_scores=10,20,30,40",
                        "chosen_slot=0",
                        "chosen_id=1",
                        "chosen=POUND",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = explain_decision_from_trace_paths(
                [trace_path],
                focus_action_id="HYPER_BEAM",
            )
            text = format_explain_decision(report)

        focus = report["decision_summary"]["focus_action_comparison"]
        self.assertFalse(focus["found"])
        self.assertEqual(focus["available_action_count"], 4)
        self.assertEqual(focus["available_actions"][0]["action_id"], "slot1:IRON_HEAD")
        self.assertIn("focus=HYPER_BEAM missing", text)
        self.assertIn("available=slot1:IRON_HEAD, slot2:KARATE_CHOP", text)
        self.assertIn(
            "Counterfactual: HYPER_BEAM unavailable: focus action is not present in captured live trace slots",
            text,
        )
        self.assertNotIn("score None -> None", text)

    def test_cli_explain_decision_accepts_trace_without_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            trace_path = Path(temporary_dir) / "trace_live.txt"
            out = Path(temporary_dir) / "trace_explain.json"
            trace_path.write_text(
                "\n".join(
                    [
                        "boss=Trace Boss",
                        "tier=3",
                        "move_ids=1,2,3,4",
                        "move_scores=10,20,30,40",
                        "chosen_slot=0",
                        "chosen_id=1",
                        "chosen=POUND",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "explain-decision",
                        "--trace",
                        str(trace_path),
                        "--json-out",
                        str(out),
                    ]
                )
            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["scenario_id"], "Trace Boss#1")
        self.assertIn("Boss AI decision explanation", stdout.getvalue())

    def test_cli_explain_decision_resolves_live_boss_route_from_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            trace_path = root / "falkner_live.txt"
            manifest_path = root / "live_capture_manifest.json"
            input_manifest_out = root / "falkner_input_manifest.json"
            out = root / "trace_explain.json"
            trace_path.write_text(
                "\n".join(
                    [
                        "boss=Falkner",
                        "tier=1",
                        "move_ids=33,28,16,98",
                        "move_scores=20,23,20,20",
                        "chosen_slot=0",
                        "chosen_id=33",
                        "chosen=TACKLE",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "trace_rom": "pokegold_trace.gbc",
                        "trace_rom_sha256": "",
                        "trace_symbols": "pokegold_trace.sym",
                        "trace_symbols_sha256": "",
                        "captures": [
                            {
                                "id": "falkner",
                                "boss": "Falkner",
                                "status": "FINISHED",
                                "out": str(trace_path),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "explain-decision",
                        "--boss-route",
                        "falkner",
                        "--decision-index",
                        "1",
                        "--run-rom-proof",
                        "auto",
                        "--manifest",
                        str(manifest_path),
                        "--decision-input-manifest-out",
                        str(input_manifest_out),
                        "--json-out",
                        str(out),
                    ]
                )
            data = json.loads(out.read_text(encoding="utf-8"))
            input_manifest = json.loads(input_manifest_out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["source"]["trace_path"], str(trace_path))
        self.assertEqual(data["decision_input"]["target"]["boss_route"], "falkner")
        self.assertTrue(data["decision_input"]["replay_verification"]["verified"])
        self.assertIn("decision_input.auto_resolved", data["proof_status"]["present_ids"])
        self.assertIn("input_manifest.replay_verified", data["proof_status"]["present_ids"])
        self.assertEqual(
            data["deity_evidence_marker"],
            "BOSS_AI_DEITY_DECISION_INPUT_RESOLVED",
        )
        self.assertEqual(
            Path(input_manifest["resolution"]["trace_path"]),
            trace_path,
        )
        self.assertIn("--boss-route falkner", data["proof_status"]["next_proof_chain"][1]["command"])
        self.assertIn("input=auto source=live_capture_manifest", stdout.getvalue())
        self.assertIn("BOSS_AI_DEITY_DECISION_INPUT_RESOLVED", stdout.getvalue())

    def test_cli_explain_decision_resolves_generated_policy_question(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            input_manifest_out = root / "generated_input_manifest.json"
            out = root / "generated_explain.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "explain-decision",
                        "--policy-question",
                        "active_pressure_before_status",
                        "--decision-input-manifest-out",
                        str(input_manifest_out),
                        "--json-out",
                        str(out),
                    ]
                )
            data = json.loads(out.read_text(encoding="utf-8"))
            input_manifest = json.loads(input_manifest_out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(
            data["decision_input"]["resolution"]["source"],
            "generated_scenario",
        )
        self.assertEqual(
            data["decision_input"]["target"]["policy_question"],
            "active_pressure_before_status",
        )
        self.assertIn("decision_input.generated_auto", data["proof_status"]["present_ids"])
        self.assertIn("policy_expectation.reported", data["proof_status"]["present_ids"])
        self.assertIn("counterfactual.decisive", data["proof_status"]["present_ids"])
        self.assertEqual(
            input_manifest["resolution"]["scenario_id"],
            data["scenario_id"],
        )
        self.assertEqual(
            Path(input_manifest["resolution"]["scenario_path"]).parent,
            root,
        )
        self.assertIn("input=auto source=generated_scenario", stdout.getvalue())

    def test_trace_explanation_surfaces_switch_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            trace_path = Path(temporary_dir) / "shared_switch_loop_live.txt"
            trace_path.write_text(
                "\n".join(
                    [
                        "boss=Shared switch-loop",
                        "tier=2",
                        "move_ids=191,85,86,129",
                        "move_scores=20,1,24,28",
                        "pre_model_scores=20,20,20,20",
                        "post_model_scores=19,13,24,28",
                        "model_score_deltas=-1,-7,+4,+8",
                        "chosen_slot=0",
                        "chosen_id=191",
                        "chosen=SPIKES",
                        "switch_confidence=85",
                        "switch_context=param=31,index=01,last_out=01,cooldown=02,cur_ot=00",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = explain_decision_from_trace_paths([trace_path])
            text = format_explain_decision(report)

        switch_path = report["observed_rom_decision"]["decision"]["switch_path"]
        self.assertTrue(switch_path["observed"])
        self.assertTrue(switch_path["actual_switch"])
        self.assertEqual(switch_path["switch_param"], 0x31)
        self.assertEqual(switch_path["proposed_target_1_based"], 2)
        self.assertTrue(switch_path["switch_roll"]["available"])
        self.assertTrue(
            any("rom-switch-materialize" in item["command"] for item in report["next_proof_commands"])
        )
        self.assertIn("switch_materialization", report["proof_status"]["missing_ids"])
        self.assertEqual(
            report["proof_status"]["next_proof_command"]["purpose"],
            "Generate switch/sack probes for ROM switch-dispatch materialization",
        )
        switch_chain = report["proof_status"]["next_proof_chain"]
        self.assertEqual(
            switch_chain[0]["purpose"],
            "Generate switch/sack probes for ROM switch-dispatch materialization",
        )
        self.assertEqual(
            switch_chain[0]["expected_output_paths"],
            [".local\\tmp\\boss_ai_debugger\\Shared_switch-loop_1_switch_sack_probe.jsonl"],
        )
        self.assertEqual(
            switch_chain[1]["purpose"],
            "Materialize switch-dispatch proof against the shared switch route",
        )
        self.assertEqual(
            switch_chain[1]["closes_evidence_ids"],
            ["observed_rom_decision", "switch_path", "switch_materialization"],
        )
        self.assertEqual(
            switch_chain[1]["expected_output_paths"],
            [".local\\tmp\\boss_ai_debugger\\Shared_switch-loop_1_rom_switch.json"],
        )
        self.assertEqual(
            switch_chain[1]["consumes_artifact_paths"],
            [".local\\tmp\\boss_ai_debugger\\Shared_switch-loop_1_switch_sack_probe.jsonl"],
        )
        self.assertEqual(
            switch_chain[2]["purpose"],
            "Render switch-dispatch explanation packet after materialization",
        )
        self.assertEqual(
            switch_chain[2]["consumes_artifact_paths"],
            [
                ".local\\tmp\\boss_ai_debugger\\Shared_switch-loop_1_switch_sack_probe.jsonl",
                ".local\\tmp\\boss_ai_debugger\\Shared_switch-loop_1_rom_switch.json",
            ],
        )
        self.assertIn(
            "rom-switch-materialize",
            report["decision_summary"]["next_proof_chain"][1]["command"],
        )
        self.assertIn(
            "--rom-switch-materialization",
            report["decision_summary"]["next_proof_chain"][2]["command"],
        )
        self.assertTrue(
            {"switch.try_switch", "switch.compute_switch_confidence", "switch.get_switch_threshold"}.issubset(
                {anchor["rule_id"] for anchor in report["source_anchors"]}
            )
        )
        switch_counterfactual = report["counterfactual"]["switch_roll_counterfactual"]
        self.assertTrue(switch_counterfactual["available"])
        self.assertEqual(switch_counterfactual["confidence"], 85)
        self.assertEqual(switch_counterfactual["zero_probability_if_confidence_at_most"], 69)
        self.assertEqual(switch_counterfactual["delta_to_force_zero_probability"], -16)
        self.assertGreaterEqual(
            switch_counterfactual["nonzero_guaranteed_at_confidence"],
            switch_counterfactual["nonzero_possible_at_confidence"],
        )
        self.assertEqual(report["decision_summary"]["status"], "needs_switch_proof")
        self.assertIn("switch actual_switch_observed", report["decision_summary"]["path"])
        self.assertIn(
            "switch confidence=85",
            report["decision_summary"]["decisive_counterfactual"],
        )
        self.assertIn(
            "trace.switch_confidence=85",
            report["decision_summary"]["evidence_highlights"]["public_inputs"],
        )
        self.assertIn("switch_path=actual_switch_observed", text)
        self.assertIn(
            "next=Generate switch/sack probes for ROM switch-dispatch materialization",
            text,
        )
        self.assertIn(
            "then=Materialize switch-dispatch proof against the shared switch route",
            text,
        )
        self.assertIn(
            "then=Render switch-dispatch explanation packet after materialization",
            text,
        )
        self.assertIn("public=trace.boss=Shared switch-loop", text)
        self.assertIn("Switch counterfactual", text)

    def test_trace_auto_switch_proof_reports_hash_basis_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            trace_path = root / "shared_switch_loop_live.txt"
            trace_path.write_text(
                "\n".join(
                    [
                        "boss=Shared switch-loop",
                        "tier=2",
                        "move_ids=191,85,86,129",
                        "move_scores=20,1,24,28",
                        "pre_model_scores=20,20,20,20",
                        "post_model_scores=19,13,24,28",
                        "model_score_deltas=-1,-7,+4,+8",
                        "chosen_slot=0",
                        "chosen_id=191",
                        "chosen=SPIKES",
                        "switch_confidence=85",
                        "switch_context=param=31,index=01,last_out=01,cooldown=02,cur_ot=00",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            artifact_dir = root / "artifacts"
            with patch(
                "tools.boss_ai_debugger.explain_decision.run_rom_switch_materialization",
                side_effect=PreferenceDataError(
                    "live capture manifest trace_rom hash mismatch for pokegold_trace.gbc"
                ),
            ):
                report = explain_decision_from_trace_paths(
                    [trace_path],
                    run_rom_proof="auto",
                    auto_artifact_dir=artifact_dir,
                )
            text = format_explain_decision(report)

        self.assertIn("switch_sack_probe.jsonl", report["auto_rom_proof"][0]["scenario_path"])
        self.assertEqual(report["proof_status"]["status"], "blocked_by_hash_basis")
        self.assertIn("hash_basis.current", report["proof_status"]["missing_ids"])
        self.assertIn("switch_materialization", report["proof_status"]["missing_ids"])
        self.assertEqual(report["auto_rom_proof"][0]["status"], "blocked_by_hash_basis")
        self.assertEqual(
            report["proof_status"]["blockers"][0]["status"],
            "blocked_by_hash_basis",
        )
        self.assertIn("blocker=blocked_by_hash_basis switch", text)

    def test_trace_auto_switch_proof_counts_complete_batch_materialization(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            trace_path = root / "shared_switch_loop_live.txt"
            trace_path.write_text(
                "\n".join(
                    [
                        "boss=Shared switch-loop",
                        "tier=2",
                        "move_ids=191,85,86,129",
                        "move_scores=20,1,24,28",
                        "pre_model_scores=20,20,20,20",
                        "post_model_scores=19,13,24,28",
                        "model_score_deltas=-1,-7,+4,+8",
                        "chosen_slot=0",
                        "chosen_id=191",
                        "chosen=SPIKES",
                        "switch_confidence=85",
                        "switch_context=param=31,index=01,last_out=01,cooldown=02,cur_ot=00",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            batch_report = {
                **switch_materialization_report(),
                "checked_count": 1,
                "error_count": 0,
                "skipped_count": 0,
                "policy_disagreement_count": 0,
            }
            batch_report.pop("status", None)
            with patch(
                "tools.boss_ai_debugger.explain_decision.run_rom_switch_materialization",
                return_value=batch_report,
            ):
                report = explain_decision_from_trace_paths(
                    [trace_path],
                    run_rom_proof="auto",
                    auto_artifact_dir=root / "artifacts",
                )

        present_ids = report["proof_status"]["present_ids"]
        self.assertIn("switch_materialization", present_ids)
        self.assertIn("switch_materialization.proven", present_ids)
        self.assertIn("switch_roll.reported", present_ids)
        self.assertEqual(report["auto_rom_proof"][0]["status"], "pass")


def explain_scenario() -> dict:
    return {
        "id": "explain_case",
        "family": "spikes_spin",
        "tier": "late",
        "selector_hedge_action_id": "b",
        "moves": [
            {
                "id": "a",
                "name": "A",
                "move_id": 1,
                "deltas": [{"rule": "lookahead", "delta": -2}],
            },
            {"id": "b", "name": "B", "move_id": 2},
        ],
        "expectation": {
            "best_action_ids": ["a"],
            "policy_tags": ["unit_policy"],
            "condition_tags": ["active_revealed_rapid_spin", "spikes_layers_2"],
            "answer_changing_information": ["Rapid Spin reveal"],
            "evidence_refs": ["unit"],
            "why": "unit explanation",
        },
    }


def switch_scenario() -> dict:
    return {
        "id": "switch_case",
        "family": "switch_sack",
        "tier": "late",
        "moves": [
            {
                "id": "chip",
                "name": "Comfort Damage",
                "kind": "move",
                "deltas": [{"rule": "current active chip", "delta": -7}],
            },
            {
                "id": "preserve_switch",
                "name": "Switch Preserve Wincon",
                "kind": "switch",
                "deltas": [{"rule": "safe entry to named owner", "delta": -2}],
            },
            {"id": "status", "name": "Support Status", "kind": "move"},
        ],
        "expectation": {
            "best_action_ids": ["preserve_switch"],
            "acceptable_action_ids": ["chip"],
            "policy_tags": ["switching", "ace_preservation"],
            "condition_tags": ["safe_entry_available"],
            "answer_changing_information": ["whether the switch target enters safely"],
            "evidence_refs": ["unit"],
            "why": "unit switch explanation",
        },
    }


def score_materialization_report() -> dict:
    return {
        "schema_version": 1,
        "kind": "rom_score_materialization",
        "base_route": "koga",
        "base_state": "unit.state",
        "verdicts": [
            {
                "scenario_id": "explain_case",
                "status": "pass",
                "score_bytes_match": True,
                "selector_top_match": True,
                "contribution_comparison": {"mismatch_count": 0},
                "hook_equivalence": {"checked": False},
                "rom_policy": {
                    "verdict": "pass",
                    "severity": 0,
                    "reason": "ROM score bytes make expected-best action top",
                },
                "python": {
                    "best_action_id": "a",
                    "second_action_id": "b",
                    "final_scores": [18, 20],
                },
                "rom": {
                    "best_action_id": "a",
                    "best_score": 18,
                    "possible_action_ids": ["a", "b"],
                    "final_scores": [18, 20],
                    "selector_entry_scores": [18, 20, 80, 80],
                    "post_model_scores": [18, 20, 80, 80],
                },
            }
        ],
    }


def selector_materialization_report() -> dict:
    return {
        "schema_version": 1,
        "kind": "rom_selector_materialization",
        "base_route": "falkner",
        "base_state": "unit.state",
        "verdicts": [
            {
                "scenario_id": "explain_case",
                "status": "pass",
                "agreement": True,
                "python": {
                    "ready": True,
                    "tier": 3,
                    "best_action_id": "a",
                    "second_action_id": "b",
                    "probabilities": {"a": 0.625, "b": 0.375},
                    "final_scores": [18, 20],
                },
                "rom": {
                    "chosen_slot_index": 0,
                    "chosen_action_id": "a",
                    "chosen_action_probability": 0.625,
                    "chosen_move_id": 1,
                    "chosen_move_name": "A",
                    "move_ids": [1, 2, 0, 0],
                    "move_scores": [18, 20, 80, 80],
                    "tier": 3,
                },
                "reason": "ROM chose an action with nonzero Python selector probability",
                "known_limits": [],
            }
        ],
    }


def switch_materialization_report() -> dict:
    return {
        "schema_version": 1,
        "kind": "rom_switch_materialization",
        "base_route": "shared_switch_loop",
        "base_state": "unit.state",
        "verdicts": [
            {
                "scenario_id": "switch_case",
                "status": "pass",
                "family": "switch_sack",
                "expected_switch": True,
                "proposed_switch": True,
                "actual_switch": True,
                "rom_policy": {
                    "verdict": "pass",
                    "severity": 0,
                    "reason": "ROM proposes a switch",
                },
                "rom": {
                    "observed_decision": True,
                    "observation_status": "actual_switch_observed",
                    "proposed_switch": True,
                    "actual_switch": True,
                    "switch_confidence": 99,
                    "switch_param": 0x31,
                    "switch_index": 1,
                    "proposed_target_1_based": 2,
                    "chosen_move": 0,
                    "switch_roll": {
                        "available": True,
                        "success_probability": 0.8984375,
                    },
                },
                "switch_roll": {
                    "available": True,
                    "success_probability": 0.8984375,
                },
            }
        ],
    }


def rom_contribution_report() -> dict:
    return {
        "schema_version": 1,
        "source": "trace_rom_pyboy_hooks",
        "trace_id": "explain_case",
        "save_state": "scenario:explain_case",
        "event_count": 1,
        "changed_event_count": 1,
        "rule_entry_count": 0,
        "predicate_branch_entry_count": 1,
        "public_read_probe_entry_count": 0,
        "trace_basis": {},
        "chosen": {"move_id": 1, "move_name": "A", "slot_index": 0},
        "events": [
            {
                "event_type": "score_delta",
                "changed": True,
                "operation": "apply_signed_lookahead_delta",
                "delta": -2,
                "score_before": 20,
                "score_after": 18,
                "helper_symbol": "BossAI_ApplySignedDeltaToScore",
                "closed_by": "BossAI_ApplyLookaheadToTopMoveCandidates",
                "candidate": {
                    "kind": "move",
                    "slot": 1,
                    "slot_index": 0,
                    "move_id": 1,
                    "move_name": "A",
                },
                "source": {
                    "rule_id": "move.apply_lookahead_to_top_move_candidates",
                    "source_label": "BossAI_ApplyLookaheadToTopMoveCandidates",
                    "classification": "platform_boundary",
                    "public_reads": [],
                },
            }
        ],
        "rule_entries": [],
        "predicate_branch_entries": [
            {
                "event_type": "predicate_branch",
                "predicate": {
                    "predicate_id": "unit_public_branch",
                    "outcome": "public_fact_seen",
                    "legal_inputs": ["wPlayerUsedMoves"],
                },
                "source": {
                    "rule_id": "move.apply_lookahead_to_top_move_candidates",
                    "source_label": "BossAI_ApplyLookaheadToTopMoveCandidates",
                    "classification": "platform_boundary",
                    "public_reads": ["wPlayerUsedMoves"],
                },
                "public_input_snapshot": {
                    "wPlayerUsedMoves": {
                        "available": True,
                        "kind": "byte_range",
                        "values": [229, 0, 0, 0],
                    }
                },
            }
        ],
        "public_read_probe_entries": [],
        "known_limits": [],
    }


if __name__ == "__main__":
    unittest.main()
