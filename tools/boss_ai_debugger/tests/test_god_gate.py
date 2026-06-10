from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.audit.check_boss_ai_debugger_god import (
    DEFAULT_QUESTIONS,
    GENERATED_SCENARIO_CLASS_EVIDENCE_ID,
    CHANGED_AI_RUN_METADATA_EVIDENCE_ID,
    CONTRIBUTION_COMPARISON_TRACE_ID_BLOCKER,
    CONTRIBUTION_COMPARISON_TRACE_ID_EVIDENCE_ID,
    CONTRIBUTION_COMPARISON_TRACE_ID_KNOWN_GAP,
    CONTRIBUTION_REFRESH_SCOPE_EVIDENCE_ID,
    CONTRIBUTION_REFRESH_SINGLE_ROUTE_BLOCKER,
    CONTRIBUTION_REFRESH_SINGLE_ROUTE_KNOWN_GAP,
    CONTRIBUTION_TRACE_CLASS_EVIDENCE_ID,
    LIVE_TRACE_CLASS_EVIDENCE_ID,
    MATERIALIZER_VERDICT_CLASS_EVIDENCE_ID,
    MATERIALIZATION_PATH_EVIDENCE_ID,
    PRE_CHOICE_REPLAY_BLOCKER,
    PRE_CHOICE_REPLAY_EVIDENCE_ID,
    PRE_CHOICE_REPLAY_KNOWN_GAP,
    RULE_TARGET_CLASS_EVIDENCE_ID,
    SCORE_MATERIALIZATION_FULL_EVIDENCE_ID,
    SCORE_MATERIALIZATION_TARGETED_BLOCKER,
    SCORE_MATERIALIZATION_TARGETED_KNOWN_GAP,
    UNIVERSE_LABEL_EVIDENCE_ID,
    build_god_report,
    canonical_class_coverage_status,
    changed_ai_contribution_refresh_scope_status,
    changed_ai_contribution_trace_id_status,
    changed_ai_score_materialization_full_status,
    changed_ai_god_suite_status,
    generated_scenario_class_adoption_status,
    boss_ai_raw_class_adoption_status,
    pre_choice_replay_artifact_status,
)
from tools.boss_ai_debugger.universe import EXHAUSTIVE_WITNESS_CATALOG_EVIDENCE_ID


def write_valid_pre_choice_artifact(root: Path, *, manifest_hash: str | None = None) -> None:
    manifest_dir = root / "audit" / "boss_ai_trace"
    manifest_dir.mkdir(parents=True)
    manifest_path = manifest_dir / "live_capture_manifest.json"
    manifest = {
        "trace_rom_sha256": "A" * 64,
        "trace_symbols_sha256": "B" * 64,
    }
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    actual_manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest().upper()
    artifact_dir = root / "audit" / "boss_ai_debugger" / "god_level_benchmark" / "artifacts"
    artifact_dir.mkdir(parents=True)
    artifact = {
        "schema_version": 1,
        "kind": "boss_ai_pre_choice_replay_audit",
        "proof_status": "complete",
        "missing_evidence": [],
        "blocking_gaps": [],
        "closed_evidence_ids": [PRE_CHOICE_REPLAY_EVIDENCE_ID],
        "rom_sha256": manifest["trace_rom_sha256"],
        "symbols_sha256": manifest["trace_symbols_sha256"],
        "state_basis": {
            "manifest_path": "audit/boss_ai_trace/live_capture_manifest.json",
            "manifest_sha256": manifest_hash or actual_manifest_hash,
        },
        "capture_count": 18,
        "checked_count": 18,
        "failure_count": 0,
        "partial_count": 0,
        "exact_count": 18,
        "exact_match_count": 18,
        "minimum_exact_captures": 18,
        "minimum_agreement": 0.9999,
        "exact_agreement_rate": 1.0,
    }
    (artifact_dir / "pre_choice_replay.json").write_text(
        json.dumps(artifact, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_pre_choice_artifact_for_existing_manifest(root: Path) -> None:
    manifest_path = root / "audit" / "boss_ai_trace" / "live_capture_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual_manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest().upper()
    artifact_dir = root / "audit" / "boss_ai_debugger" / "god_level_benchmark" / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact = {
        "schema_version": 1,
        "kind": "boss_ai_pre_choice_replay_audit",
        "proof_status": "complete",
        "missing_evidence": [],
        "blocking_gaps": [],
        "closed_evidence_ids": [PRE_CHOICE_REPLAY_EVIDENCE_ID],
        "rom_sha256": manifest["trace_rom_sha256"],
        "symbols_sha256": manifest["trace_symbols_sha256"],
        "state_basis": {
            "manifest_path": "audit/boss_ai_trace/live_capture_manifest.json",
            "manifest_sha256": actual_manifest_hash,
        },
        "capture_count": 18,
        "checked_count": 18,
        "failure_count": 0,
        "partial_count": 0,
        "exact_count": 18,
        "exact_match_count": 18,
        "minimum_exact_captures": 18,
        "minimum_agreement": 0.9999,
        "exact_agreement_rate": 1.0,
    }
    (artifact_dir / "pre_choice_replay.json").write_text(
        json.dumps(artifact, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_changed_ai_scenarios(root: Path) -> Path:
    run_dir = root / "audit" / "boss_ai_debugger" / "runs" / "20260531_010000_changed_ai"
    run_dir.mkdir(parents=True, exist_ok=True)
    scenarios = [
        {"id": "generated_spikes_spin_1_00001", "family": "spikes_spin", "expectation": {}},
        {"id": "generated_spikes_spin_1_00000", "family": "spikes_spin", "expectation": {}},
        {"id": "generated_setup_heal_1_00000", "family": "setup_heal", "expectation": {}},
    ]
    path = run_dir / "scenarios.jsonl"
    path.write_text(
        "".join(json.dumps(scenario, sort_keys=True) + "\n" for scenario in scenarios),
        encoding="utf-8",
    )
    return path


def write_score_materialization_artifact(root: Path, scenario_ids: list[str]) -> None:
    artifact_dir = root / "audit" / "boss_ai_debugger" / "god_level_benchmark" / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact = {
        "schema_version": 1,
        "kind": "rom_score_materialization",
        "scenario_count": len(scenario_ids),
        "checked_count": len(scenario_ids),
        "skipped_count": 0,
        "error_count": 0,
        "score_bytes_match_count": 1,
        "selector_top_match_count": len(scenario_ids),
        "verdicts": [
            {
                "scenario_id": scenario_id,
                "family": "spikes_spin",
                "status": "pass",
                "score_bytes_match": index == 0,
                "class_id": f"csc_{index:020d}",
                "class_fingerprint": f"{index:064d}",
            }
            for index, scenario_id in enumerate(scenario_ids)
        ],
    }
    (artifact_dir / "changed_ai_score_materialization_full_fast.json").write_text(
        json.dumps(artifact, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_contribution_trace_id_artifacts(
    root: Path,
    *,
    matched_ids: list[str],
    materialized_ids: list[str],
    unmatched_rom_ids: list[str] | None = None,
    unmatched_python_ids: list[str] | None = None,
) -> tuple[Path, Path]:
    run_dir = root / "audit" / "boss_ai_debugger" / "runs" / "20260531_010000_changed_ai"
    run_dir.mkdir(parents=True, exist_ok=True)
    unmatched_rom_ids = unmatched_rom_ids or []
    unmatched_python_ids = unmatched_python_ids or []
    differential = {
        "schema_version": 1,
        "source": "changed-ai",
        "contribution_comparison": {
            "rom_trace_count": len(matched_ids) + len(unmatched_rom_ids),
            "python_trace_count": len(matched_ids) + len(unmatched_python_ids),
            "matched_trace_count": len(matched_ids),
            "matched_trace_ids": matched_ids,
            "unmatched_rom_trace_ids": unmatched_rom_ids,
            "unmatched_python_trace_ids": unmatched_python_ids,
            "mismatch_count": 3,
            "mismatch_class_counts": {"rule_delta_mismatch": 3},
            "class_id_mismatch_count": 0,
            "missing_class_id_count": 0,
        },
    }
    materialization = {
        "schema_version": 1,
        "kind": "rom_score_materialization",
        "traces": [
            {
                "trace_id": trace_id,
                "scenario_id": trace_id,
                "class_id": f"csc_{index:020d}",
                "decision_class_id": f"csc_{index:020d}",
            }
            for index, trace_id in enumerate(materialized_ids)
        ],
    }
    differential_path = run_dir / "differential.json"
    materialization_path = run_dir / "rom_score_materialization.json"
    differential_path.write_text(json.dumps(differential, sort_keys=True) + "\n", encoding="utf-8")
    materialization_path.write_text(json.dumps(materialization, sort_keys=True) + "\n", encoding="utf-8")
    return differential_path, materialization_path


def write_contribution_refresh_scope_artifact(
    root: Path,
    *,
    route_ids: list[str],
    artifact_route_ids: list[str] | None = None,
    run_id: str = "20260531_010000_changed_ai",
) -> None:
    manifest_dir = root / "audit" / "boss_ai_trace"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "trace_rom_sha256": "A" * 64,
        "trace_symbols_sha256": "B" * 64,
        "captures": [
            {
                "id": route_id,
                "status": "FINISHED",
                "out": f"audit/boss_ai_trace/{route_id}_live.txt",
            }
            for route_id in route_ids
        ],
    }
    manifest_path = manifest_dir / "live_capture_manifest.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest().upper()
    artifact_dir = root / "audit" / "boss_ai_debugger" / "god_level_benchmark" / "artifacts"
    trace_dir = artifact_dir / "changed_ai_rom_contribution_routes"
    trace_dir.mkdir(parents=True, exist_ok=True)
    artifact_route_ids = artifact_route_ids or route_ids
    trace_artifacts = []
    for index, route_id in enumerate(artifact_route_ids):
        rel_path = (
            Path("audit")
            / "boss_ai_debugger"
            / "god_level_benchmark"
            / "artifacts"
            / "changed_ai_rom_contribution_routes"
            / f"{index + 1:02d}_{route_id}.json"
        )
        trace = {
            "source": "trace_rom_pyboy_hooks",
            "boss_route": route_id,
            "class_id": f"csc_{index:020d}",
            "canonical_state_class": {"valid": True},
            "trace_basis": {
                "trace_rom_sha256": manifest["trace_rom_sha256"],
                "trace_symbols_sha256": manifest["trace_symbols_sha256"],
            },
            "event_count": index + 1,
            "changed_event_count": index,
        }
        (root / rel_path).write_text(json.dumps(trace, sort_keys=True) + "\n", encoding="utf-8")
        trace_artifacts.append({"boss_route": route_id, "artifact": str(rel_path)})
    artifact = {
        "schema_version": 1,
        "kind": "boss_ai_changed_ai_contribution_refresh_scope",
        "state_basis": {
            "manifest_path": "audit/boss_ai_trace/live_capture_manifest.json",
            "manifest_sha256": manifest_hash,
            "trace_rom_sha256": manifest["trace_rom_sha256"],
            "trace_symbols_sha256": manifest["trace_symbols_sha256"],
            "changed_ai_run_id": run_id,
        },
        "expected_route_ids": route_ids,
        "refreshed_route_ids": artifact_route_ids,
        "trace_artifacts": trace_artifacts,
    }
    (artifact_dir / "changed_ai_contribution_refresh_scope.json").write_text(
        json.dumps(artifact, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class BossAiGodGateTests(unittest.TestCase):
    def test_missing_rows_fail_closed_and_aggregate_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            questions = Path(tmp) / "questions.jsonl"
            questions.write_text(
                json.dumps(
                    {
                        "id": "missing",
                        "requirement": "missing requirement",
                        "surface": "boss_ai",
                        "status": "missing_evidence",
                        "blocking_gaps": ["gap"],
                        "next_command": "python next",
                        "disproof_standard": "standard",
                        "missing_reachable_label_count": 2,
                        "missing_materialization_path_count": 1,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_god_report(questions_path=questions, include_universe=False)

        self.assertFalse(report["boss_ai_god_ready"])
        self.assertEqual(report["questions_failed"], 1)
        self.assertIn("--read-only", report["repro_command"])
        self.assertEqual(report["counters"]["missing_reachable_label_count"], 2)
        self.assertEqual(report["counters"]["missing_materialization_path_count"], 1)
        self.assertIn("gap", report["blocking_gaps"])

    def test_default_questions_keep_current_baseline_green(self) -> None:
        report = build_god_report(questions_path=DEFAULT_QUESTIONS)
        self.assertTrue(report["boss_ai_god_ready"])
        self.assertEqual(report["questions_failed"], 0)
        self.assertTrue(report["boss_ai_universe"]["available"])
        self.assertEqual(report["boss_ai_universe"]["unmapped_label_count"], 0)
        self.assertEqual(report["blocking_gaps"], [])
        self.assertNotIn("boss_ai_universe_not_complete", report["blocking_gaps"])
        self.assertNotIn("boss_ai_universe_has_unmapped_reachable_labels", report["blocking_gaps"])
        self.assertNotIn("boss_ai_universe_has_labels_without_rule_ids", report["blocking_gaps"])
        self.assertNotIn("boss_ai_all_class_materialization_paths_not_available", report["blocking_gaps"])
        self.assertNotIn("boss_ai_exhaustive_class_generator_not_implemented", report["blocking_gaps"])
        self.assertNotIn("boss_ai_exhaustive_class_witness_roles_missing", report["blocking_gaps"])
        self.assertNotIn("boss_ai_canonical_class_schema_not_integrated", report["blocking_gaps"])
        self.assertNotIn("boss_ai_raw_decision_class_ids_not_integrated", report["blocking_gaps"])
        self.assertNotIn("boss_ai_live_trace_and_contribution_class_ids_not_integrated", report["blocking_gaps"])
        self.assertTrue(report["canonical_class_coverage"]["ready"])
        self.assertTrue(report["generated_scenario_class_adoption"]["ready"])
        self.assertTrue(report["live_trace_class_adoption"]["ready"])
        self.assertTrue(report["contribution_trace_class_adoption"]["ready"])
        self.assertIn(RULE_TARGET_CLASS_EVIDENCE_ID, report["closed_evidence_ids"])
        self.assertIn(GENERATED_SCENARIO_CLASS_EVIDENCE_ID, report["closed_evidence_ids"])
        self.assertIn(MATERIALIZER_VERDICT_CLASS_EVIDENCE_ID, report["closed_evidence_ids"])
        self.assertIn(LIVE_TRACE_CLASS_EVIDENCE_ID, report["closed_evidence_ids"])
        self.assertIn(CONTRIBUTION_TRACE_CLASS_EVIDENCE_ID, report["closed_evidence_ids"])
        self.assertIn(UNIVERSE_LABEL_EVIDENCE_ID, report["closed_evidence_ids"])
        self.assertIn(MATERIALIZATION_PATH_EVIDENCE_ID, report["closed_evidence_ids"])
        self.assertIn(EXHAUSTIVE_WITNESS_CATALOG_EVIDENCE_ID, report["closed_evidence_ids"])
        self.assertEqual(report["counters"]["missing_class_id_count"], 0)
        self.assertEqual(report["counters"]["missing_reachable_label_count"], 0)
        self.assertEqual(report["counters"]["missing_rule_count"], 0)
        self.assertEqual(report["counters"]["missing_materialization_path_count"], 0)
        self.assertEqual(report["counters"]["missing_witness_role_count"], 0)
        witness_inventory = report["boss_ai_universe"]["exhaustive_class_witness_inventory"]
        self.assertTrue(witness_inventory["available"])
        self.assertEqual(witness_inventory["missing_witness_role_count"], 0)
        witness_catalog = report["boss_ai_universe"]["exhaustive_class_witness_catalog"]
        self.assertTrue(witness_catalog["available"])
        self.assertTrue(witness_catalog["ready"])
        self.assertGreater(witness_catalog["generated_witness_class_count"], 0)
        self.assertEqual(witness_catalog["missing_rom_proof_role_count"], 0)
        self.assertIn("exhaustive_class_proofs", witness_catalog["does_not_close"])
        for question in report["questions"]:
            self.assertNotIn("<", question["next_command"])
            self.assertNotIn(">", question["next_command"])

    def test_complete_row_without_evidence_still_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            questions = Path(tmp) / "questions.jsonl"
            questions.write_text(
                json.dumps(
                    {
                        "id": "fake_complete",
                        "requirement": "fake complete",
                        "surface": "boss_ai",
                        "status": "complete",
                        "blocking_gaps": [],
                        "next_command": "python next",
                        "disproof_standard": "standard",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_god_report(questions_path=questions, include_universe=False)

        self.assertFalse(report["boss_ai_god_ready"])
        self.assertTrue(
            any(
                "complete rows must declare closed_evidence_ids" in error
                for error in report["schema_errors"]
            )
        )

    def test_synthetic_universe_packet_keeps_gate_red_even_when_question_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "evidence.json"
            evidence.write_text("{}", encoding="utf-8")
            questions = root / "questions.jsonl"
            questions.write_text(
                json.dumps(
                    {
                        "id": "question_complete",
                        "requirement": "question complete",
                        "surface": "boss_ai",
                        "status": "complete",
                        "blocking_gaps": [],
                        "next_command": "python next",
                        "disproof_standard": "standard",
                        "closed_evidence_ids": ["question.closed"],
                        "evidence_artifacts": ["evidence.json"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            universe = {
                "proof_status": "missing_evidence",
                "blocking_gaps": ["synthetic_unmapped_label"],
                "counters": {
                    "missing_reachable_label_count": 1,
                    "missing_rule_count": 1,
                },
            }

            report = build_god_report(
                questions_path=questions,
                root=root,
                include_universe=True,
                universe_report=universe,
            )

        self.assertFalse(report["boss_ai_god_ready"])
        self.assertEqual(report["questions_failed"], 0)
        self.assertEqual(report["counters"]["missing_reachable_label_count"], 1)
        self.assertIn("synthetic_unmapped_label", report["blocking_gaps"])
        self.assertIn("boss_ai_universe_not_complete", report["blocking_gaps"])
        self.assertIn("boss_ai_rule_target_canonical_class_ids_missing", report["blocking_gaps"])

    def test_exhaustive_generator_row_uses_witness_inventory_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (
                root
                / "audit/boss_ai_debugger/god_level_benchmark/artifacts/counterfactual_witness_materializations"
            ).mkdir(parents=True)
            questions = root / "questions.jsonl"
            questions.write_text(
                json.dumps(
                    {
                        "id": "boss_ai_exhaustive_class_generator",
                        "requirement": "exhaustive generator",
                        "surface": "boss_ai",
                        "status": "missing_evidence",
                        "blocking_gaps": ["boss_ai_exhaustive_class_generator_not_implemented"],
                        "next_command": "python -m tools.boss_ai_debugger generate --family all",
                        "disproof_standard": "all rules have witness classes",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            universe = {
                "proof_status": "missing_evidence",
                "blocking_gaps": ["boss_ai_exhaustive_class_witness_roles_missing"],
                "counters": {
                    "missing_witness_role_count": 2,
                },
                "canonical_class_rows": [
                    {
                        "rule_id": "move.unit",
                        "class_id": "csc_123",
                        "canonical_state_class_valid": True,
                        "canonical_state_class_errors": [],
                    }
                ],
                "exhaustive_class_witness_inventory": {
                    "ready": False,
                    "role_names": ["positive"],
                    "missing_witness_role_count": 2,
                    "status_counts": {"missing_evidence": 2},
                    "blocking_gaps": ["boss_ai_exhaustive_class_witness_roles_missing"],
                    "first_missing_roles": [
                        {
                            "rule_id": "move.unit",
                            "seed_class_id": "csc_123",
                            "witness_role": "positive",
                            "status": "missing_evidence",
                        }
                    ],
                },
            }

            report = build_god_report(
                questions_path=questions,
                root=root,
                include_universe=True,
                universe_report=universe,
            )

        question = report["questions"][0]
        self.assertFalse(report["boss_ai_god_ready"])
        self.assertEqual(question["proof_status"], "missing_evidence")
        self.assertNotIn("boss_ai_exhaustive_class_generator_not_implemented", question["blocking_gaps"])
        self.assertIn("boss_ai_exhaustive_class_witness_roles_missing", question["blocking_gaps"])
        self.assertEqual(report["counters"]["missing_witness_role_count"], 2)

    def test_exhaustive_generator_row_closes_when_witness_inventory_is_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (
                root
                / "audit/boss_ai_debugger/god_level_benchmark/artifacts/counterfactual_witness_materializations"
            ).mkdir(parents=True)
            questions = root / "questions.jsonl"
            questions.write_text(
                json.dumps(
                    {
                        "id": "boss_ai_exhaustive_class_generator",
                        "requirement": "exhaustive generator",
                        "surface": "boss_ai",
                        "status": "missing_evidence",
                        "blocking_gaps": ["boss_ai_exhaustive_class_generator_not_implemented"],
                        "next_command": "python -m tools.boss_ai_debugger generate --family all",
                        "disproof_standard": "all rules have witness classes",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            universe = {
                "proof_status": "complete",
                "blocking_gaps": [],
                "counters": {"missing_witness_role_count": 0},
                "canonical_class_rows": [],
                "exhaustive_class_witness_inventory": {
                    "ready": True,
                    "role_names": ["positive"],
                    "missing_witness_role_count": 0,
                    "satisfied_witness_role_count": 1,
                    "status_counts": {"satisfied": 1},
                    "blocking_gaps": [],
                    "first_missing_roles": [],
                },
                "exhaustive_class_witness_catalog": {
                    "kind": "boss_ai_exhaustive_class_witness_catalog",
                    "proof_status": "catalog_only",
                    "proof_complete": True,
                    "does_not_close": ["boss_ai_exhaustive_class_witness_roles_missing"],
                    "closed_evidence_ids": [EXHAUSTIVE_WITNESS_CATALOG_EVIDENCE_ID],
                    "required_witness_role_count": 1,
                    "cataloged_witness_class_count": 1,
                    "missing_witness_class_count": 0,
                    "invalid_witness_class_count": 0,
                    "duplicate_class_id_count": 0,
                    "missing_rom_proof_role_count": 0,
                    "rom_proven_witness_role_count": 1,
                    "blocking_gaps": [],
                    "catalog_rows": [
                        {
                            "rule_id": "move.unit",
                            "witness_role": "positive",
                            "witness_class_id": "csc_witness",
                            "canonical_state_class_valid": True,
                            "status": "rom_proven",
                            "observed_evidence_count": 1,
                        }
                    ],
                },
            }

            report = build_god_report(
                questions_path=questions,
                root=root,
                include_universe=True,
                universe_report=universe,
            )

        question = report["questions"][0]
        self.assertEqual(question["status"], "PASS")
        self.assertEqual(question["proof_status"], "complete")
        self.assertEqual(question["blocking_gaps"], [])
        self.assertIn(EXHAUSTIVE_WITNESS_CATALOG_EVIDENCE_ID, report["closed_evidence_ids"])

    def test_valid_rule_target_class_rows_close_narrow_canonical_evidence(self) -> None:
        universe = {
            "canonical_class_rows": [
                {
                    "rule_id": "move.unit",
                    "class_id": "csc_123",
                    "canonical_state_class_valid": True,
                    "canonical_state_class_errors": [],
                }
            ]
        }

        status = canonical_class_coverage_status(universe)

        self.assertTrue(status["ready"])
        self.assertEqual(status["class_row_count"], 1)
        self.assertEqual(status["valid_class_id_count"], 1)
        self.assertEqual(status["blocking_gaps"], [])

    def test_invalid_rule_target_class_rows_fail_closed(self) -> None:
        universe = {
            "canonical_class_rows": [
                {
                    "rule_id": "move.unit",
                    "class_id": "",
                    "canonical_state_class_valid": False,
                    "canonical_state_class_errors": ["missing class_id"],
                }
            ]
        }

        status = canonical_class_coverage_status(universe)

        self.assertFalse(status["ready"])
        self.assertEqual(status["missing_class_id_count"], 1)
        self.assertIn("boss_ai_rule_target_canonical_class_ids_missing", status["blocking_gaps"])

    def test_generated_scenario_class_adoption_probe_is_closed(self) -> None:
        status = generated_scenario_class_adoption_status()

        self.assertTrue(status["ready"])
        self.assertRegex(status["class_id"], r"^csc_[0-9A-F]{20}$")
        self.assertEqual(status["blocking_gaps"], [])

    def test_raw_class_adoption_closes_supported_trace_surfaces(self) -> None:
        status = boss_ai_raw_class_adoption_status()

        self.assertTrue(status["ready"])
        self.assertEqual(status["blocking_gaps"], [])
        self.assertIn(LIVE_TRACE_CLASS_EVIDENCE_ID, status["closed_evidence_ids"])
        self.assertIn(CONTRIBUTION_TRACE_CLASS_EVIDENCE_ID, status["closed_evidence_ids"])

    def test_changed_ai_metadata_replaces_generic_blocker_with_concrete_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "audit" / "boss_ai_debugger" / "runs" / "20260531_010000_changed_ai"
            run_dir.mkdir(parents=True)
            (run_dir / "batch_report.json").write_text("{}", encoding="utf-8")
            (run_dir / "scenarios.jsonl").write_text("{}\n", encoding="utf-8")
            (run_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "profile": "changed-ai",
                        "run_id": "20260531_010000_changed_ai",
                        "created_at": "2026-05-31T01:00:00+00:00",
                        "changed_files": ["engine/battle/ai/boss_policy_move.asm"],
                        "batch_summary": {"scenario_count": 1},
                        "validation": {"valid": True},
                        "known_gaps": [
                            "changed-ai suite records ROM rebuild as skipped unless explicitly requested.",
                            "ROM/Python contribution traces are compared only when trace ids match.",
                        ],
                        "artifacts": {
                            "batch_report": "audit\\boss_ai_debugger\\runs\\20260531_010000_changed_ai\\batch_report.json",
                            "scenarios": "audit\\boss_ai_debugger\\runs\\20260531_010000_changed_ai\\scenarios.jsonl",
                        },
                        "artifact_hashes": {"batch_report": "HASH", "scenarios": "HASH"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            questions = root / "questions.jsonl"
            questions.write_text(
                json.dumps(
                    {
                        "id": "boss_ai_changed_ai_god_suite",
                        "requirement": "changed AI proof",
                        "surface": "boss_ai",
                        "status": "missing_evidence",
                        "blocking_gaps": ["changed_ai_god_suite_not_implemented"],
                        "next_command": "python -m tools.boss_ai_debugger run-suite --profile changed-ai",
                        "disproof_standard": "changed AI cannot silently avoid proof refresh",
                        "missing_proof_artifact_count": 1,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_god_report(questions_path=questions, root=root, include_universe=False)

        question = report["questions"][0]
        self.assertFalse(report["boss_ai_god_ready"])
        self.assertEqual(question["proof_status"], "missing_evidence")
        self.assertNotIn("changed_ai_god_suite_not_implemented", question["blocking_gaps"])
        self.assertIn("changed_ai_rom_rebuild_skipped", question["blocking_gaps"])
        self.assertIn("changed_ai_contribution_comparison_trace_id_only", question["blocking_gaps"])
        self.assertTrue(report["changed_ai_god_suite"]["partial_evidence_ready"])
        self.assertIn(CHANGED_AI_RUN_METADATA_EVIDENCE_ID, report["closed_evidence_ids"])

    def test_changed_ai_pre_choice_artifact_resolves_only_that_known_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_pre_choice_artifact(root)
            run_dir = root / "audit" / "boss_ai_debugger" / "runs" / "20260531_010000_changed_ai"
            run_dir.mkdir(parents=True)
            (run_dir / "batch_report.json").write_text("{}", encoding="utf-8")
            (run_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "profile": "changed-ai",
                        "run_id": "20260531_010000_changed_ai",
                        "created_at": "2026-05-31T01:00:00+00:00",
                        "batch_summary": {"scenario_count": 1},
                        "validation": {"valid": True},
                        "known_gaps": [
                            PRE_CHOICE_REPLAY_KNOWN_GAP,
                            "ROM/Python contribution traces are compared only when trace ids match.",
                        ],
                        "artifacts": {
                            "batch_report": "audit\\boss_ai_debugger\\runs\\20260531_010000_changed_ai\\batch_report.json",
                        },
                        "artifact_hashes": {"batch_report": "HASH"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            status = changed_ai_god_suite_status(root)

        self.assertTrue(status["partial_evidence_ready"])
        self.assertTrue(status["pre_choice_replay"]["ready"])
        self.assertIn(PRE_CHOICE_REPLAY_KNOWN_GAP, status["known_gaps"])
        self.assertIn(PRE_CHOICE_REPLAY_KNOWN_GAP, status["resolved_known_gaps"])
        self.assertNotIn(PRE_CHOICE_REPLAY_BLOCKER, status["blocking_gaps"])
        self.assertIn("changed_ai_contribution_comparison_trace_id_only", status["blocking_gaps"])
        self.assertIn(PRE_CHOICE_REPLAY_EVIDENCE_ID, status["closed_evidence_ids"])

    def test_stale_pre_choice_artifact_does_not_resolve_known_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_pre_choice_artifact(root, manifest_hash="STALE")
            run_dir = root / "audit" / "boss_ai_debugger" / "runs" / "20260531_010000_changed_ai"
            run_dir.mkdir(parents=True)
            (run_dir / "batch_report.json").write_text("{}", encoding="utf-8")
            (run_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "profile": "changed-ai",
                        "run_id": "20260531_010000_changed_ai",
                        "created_at": "2026-05-31T01:00:00+00:00",
                        "batch_summary": {"scenario_count": 1},
                        "validation": {"valid": True},
                        "known_gaps": [PRE_CHOICE_REPLAY_KNOWN_GAP],
                        "artifacts": {
                            "batch_report": "audit\\boss_ai_debugger\\runs\\20260531_010000_changed_ai\\batch_report.json",
                        },
                        "artifact_hashes": {"batch_report": "HASH"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            pre_choice = pre_choice_replay_artifact_status(root)
            status = changed_ai_god_suite_status(root)

        self.assertFalse(pre_choice["ready"])
        self.assertIn("boss_ai_pre_choice_replay_manifest_hash_stale", pre_choice["blocking_gaps"])
        self.assertIn(PRE_CHOICE_REPLAY_BLOCKER, status["blocking_gaps"])
        self.assertNotIn(PRE_CHOICE_REPLAY_EVIDENCE_ID, status["closed_evidence_ids"])

    def test_changed_ai_full_score_materialization_resolves_targeted_batch_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenarios = write_changed_ai_scenarios(root)
            write_score_materialization_artifact(
                root,
                [
                    "generated_spikes_spin_1_00000",
                    "generated_spikes_spin_1_00001",
                    "generated_setup_heal_1_00000",
                ],
            )
            run_dir = root / "audit" / "boss_ai_debugger" / "runs" / "20260531_010000_changed_ai"
            (run_dir / "batch_report.json").write_text("{}", encoding="utf-8")
            metadata = {
                "profile": "changed-ai",
                "run_id": "20260531_010000_changed_ai",
                "created_at": "2026-05-31T01:00:00+00:00",
                "batch_summary": {"scenario_count": 3},
                "validation": {"valid": True},
                "known_gaps": [
                    SCORE_MATERIALIZATION_TARGETED_KNOWN_GAP,
                    "ROM/Python contribution traces are compared only when trace ids match.",
                ],
                "artifacts": {
                    "batch_report": "audit\\boss_ai_debugger\\runs\\20260531_010000_changed_ai\\batch_report.json",
                    "scenarios": str(scenarios.relative_to(root)),
                },
                "artifact_hashes": {"batch_report": "HASH", "scenarios": "HASH"},
            }
            (run_dir / "metadata.json").write_text(json.dumps(metadata) + "\n", encoding="utf-8")

            score_status = changed_ai_score_materialization_full_status(root, metadata)
            status = changed_ai_god_suite_status(root)

        self.assertTrue(score_status["coverage_ready"])
        self.assertEqual(score_status["expected_scenario_count"], 3)
        self.assertEqual(score_status["expected_checked_count"], 3)
        self.assertEqual(score_status["expected_skipped_count"], 0)
        self.assertEqual(score_status["score_bytes_mismatch_count"], 2)
        self.assertIn(SCORE_MATERIALIZATION_TARGETED_KNOWN_GAP, status["resolved_known_gaps"])
        self.assertNotIn(SCORE_MATERIALIZATION_TARGETED_BLOCKER, status["blocking_gaps"])
        self.assertIn("changed_ai_contribution_comparison_trace_id_only", status["blocking_gaps"])
        self.assertIn(SCORE_MATERIALIZATION_FULL_EVIDENCE_ID, status["closed_evidence_ids"])

    def test_incomplete_full_score_materialization_keeps_targeted_batch_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenarios = write_changed_ai_scenarios(root)
            write_score_materialization_artifact(root, ["generated_spikes_spin_1_00000"])
            run_dir = root / "audit" / "boss_ai_debugger" / "runs" / "20260531_010000_changed_ai"
            (run_dir / "batch_report.json").write_text("{}", encoding="utf-8")
            metadata = {
                "profile": "changed-ai",
                "run_id": "20260531_010000_changed_ai",
                "created_at": "2026-05-31T01:00:00+00:00",
                "batch_summary": {"scenario_count": 3},
                "validation": {"valid": True},
                "known_gaps": [SCORE_MATERIALIZATION_TARGETED_KNOWN_GAP],
                "artifacts": {
                    "batch_report": "audit\\boss_ai_debugger\\runs\\20260531_010000_changed_ai\\batch_report.json",
                    "scenarios": str(scenarios.relative_to(root)),
                },
                "artifact_hashes": {"batch_report": "HASH", "scenarios": "HASH"},
            }
            (run_dir / "metadata.json").write_text(json.dumps(metadata) + "\n", encoding="utf-8")

            score_status = changed_ai_score_materialization_full_status(root, metadata)
            status = changed_ai_god_suite_status(root)

        self.assertFalse(score_status["coverage_ready"])
        self.assertIn(
            "changed_ai_score_materialization_full_missing_scenarios",
            score_status["blocking_gaps"],
        )
        self.assertIn(SCORE_MATERIALIZATION_TARGETED_BLOCKER, status["blocking_gaps"])
        self.assertNotIn(SCORE_MATERIALIZATION_FULL_EVIDENCE_ID, status["closed_evidence_ids"])

    def test_changed_ai_generated_contribution_trace_ids_resolve_trace_id_gap_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matched_ids = [
                "generated_spikes_spin_1_00004",
                "generated_spikes_spin_1_00009",
                "generated_spikes_spin_1_00010",
            ]
            differential_path, materialization_path = write_contribution_trace_id_artifacts(
                root,
                matched_ids=matched_ids,
                materialized_ids=matched_ids,
                unmatched_rom_ids=["route:clair"],
                unmatched_python_ids=[f"generated_other_{index:05d}" for index in range(155)],
            )
            run_dir = root / "audit" / "boss_ai_debugger" / "runs" / "20260531_010000_changed_ai"
            (run_dir / "batch_report.json").write_text("{}", encoding="utf-8")
            metadata = {
                "profile": "changed-ai",
                "run_id": "20260531_010000_changed_ai",
                "created_at": "2026-05-31T01:00:00+00:00",
                "batch_summary": {"scenario_count": 200},
                "validation": {"valid": True},
                "known_gaps": [
                    CONTRIBUTION_COMPARISON_TRACE_ID_KNOWN_GAP,
                    "changed-ai suite refreshes one ROM contribution route, not the full live trace corpus.",
                ],
                "artifacts": {
                    "batch_report": "audit\\boss_ai_debugger\\runs\\20260531_010000_changed_ai\\batch_report.json",
                    "differential": str(differential_path.relative_to(root)),
                    "rom_score_materialization": str(materialization_path.relative_to(root)),
                },
                "artifact_hashes": {
                    "batch_report": "HASH",
                    "differential": "HASH",
                    "rom_score_materialization": "HASH",
                },
            }
            (run_dir / "metadata.json").write_text(json.dumps(metadata) + "\n", encoding="utf-8")

            comparison = changed_ai_contribution_trace_id_status(root, metadata)
            status = changed_ai_god_suite_status(root)

        self.assertTrue(comparison["ready"])
        self.assertEqual(comparison["matched_trace_count"], 3)
        self.assertEqual(comparison["materialized_trace_count"], 3)
        self.assertEqual(comparison["unmatched_python_trace_count"], 155)
        self.assertEqual(comparison["non_scenario_unmatched_rom_trace_ids"], ["route:clair"])
        self.assertEqual(comparison["mismatch_count"], 3)
        self.assertIn(CONTRIBUTION_COMPARISON_TRACE_ID_KNOWN_GAP, status["resolved_known_gaps"])
        self.assertNotIn(CONTRIBUTION_COMPARISON_TRACE_ID_BLOCKER, status["blocking_gaps"])
        self.assertIn("changed_ai_contribution_refresh_single_route_only", status["blocking_gaps"])
        self.assertIn(CONTRIBUTION_COMPARISON_TRACE_ID_EVIDENCE_ID, status["closed_evidence_ids"])

    def test_changed_ai_generated_contribution_unmatched_trace_keeps_trace_id_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            differential_path, materialization_path = write_contribution_trace_id_artifacts(
                root,
                matched_ids=["generated_spikes_spin_1_00004"],
                materialized_ids=[
                    "generated_spikes_spin_1_00004",
                    "generated_spikes_spin_1_00009",
                ],
            )
            run_dir = root / "audit" / "boss_ai_debugger" / "runs" / "20260531_010000_changed_ai"
            (run_dir / "batch_report.json").write_text("{}", encoding="utf-8")
            metadata = {
                "profile": "changed-ai",
                "run_id": "20260531_010000_changed_ai",
                "created_at": "2026-05-31T01:00:00+00:00",
                "batch_summary": {"scenario_count": 200},
                "validation": {"valid": True},
                "known_gaps": [CONTRIBUTION_COMPARISON_TRACE_ID_KNOWN_GAP],
                "artifacts": {
                    "batch_report": "audit\\boss_ai_debugger\\runs\\20260531_010000_changed_ai\\batch_report.json",
                    "differential": str(differential_path.relative_to(root)),
                    "rom_score_materialization": str(materialization_path.relative_to(root)),
                },
                "artifact_hashes": {"batch_report": "HASH", "differential": "HASH"},
            }
            (run_dir / "metadata.json").write_text(json.dumps(metadata) + "\n", encoding="utf-8")

            comparison = changed_ai_contribution_trace_id_status(root, metadata)
            status = changed_ai_god_suite_status(root)

        self.assertFalse(comparison["ready"])
        self.assertIn(
            "changed_ai_contribution_comparison_materialized_trace_ids_unmatched",
            comparison["blocking_gaps"],
        )
        self.assertIn(CONTRIBUTION_COMPARISON_TRACE_ID_BLOCKER, status["blocking_gaps"])
        self.assertNotIn(CONTRIBUTION_COMPARISON_TRACE_ID_EVIDENCE_ID, status["closed_evidence_ids"])

    def test_changed_ai_full_contribution_refresh_scope_resolves_single_route_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            route_ids = ["falkner", "bugsy"]
            write_contribution_refresh_scope_artifact(root, route_ids=route_ids)
            run_dir = root / "audit" / "boss_ai_debugger" / "runs" / "20260531_010000_changed_ai"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "batch_report.json").write_text("{}", encoding="utf-8")
            metadata = {
                "profile": "changed-ai",
                "run_id": "20260531_010000_changed_ai",
                "created_at": "2026-05-31T01:00:00+00:00",
                "batch_summary": {"scenario_count": 2},
                "validation": {"valid": True},
                "known_gaps": [
                    CONTRIBUTION_REFRESH_SINGLE_ROUTE_KNOWN_GAP,
                    CONTRIBUTION_COMPARISON_TRACE_ID_KNOWN_GAP,
                ],
                "artifacts": {
                    "batch_report": "audit\\boss_ai_debugger\\runs\\20260531_010000_changed_ai\\batch_report.json",
                },
                "artifact_hashes": {"batch_report": "HASH"},
            }
            (run_dir / "metadata.json").write_text(json.dumps(metadata) + "\n", encoding="utf-8")

            refresh_scope = changed_ai_contribution_refresh_scope_status(root, metadata)
            status = changed_ai_god_suite_status(root)

        self.assertTrue(refresh_scope["ready"])
        self.assertEqual(refresh_scope["expected_route_count"], 2)
        self.assertEqual(refresh_scope["refreshed_route_count"], 2)
        self.assertEqual(refresh_scope["route_trace_count"], 2)
        self.assertIn(CONTRIBUTION_REFRESH_SINGLE_ROUTE_KNOWN_GAP, status["resolved_known_gaps"])
        self.assertNotIn(CONTRIBUTION_REFRESH_SINGLE_ROUTE_BLOCKER, status["blocking_gaps"])
        self.assertIn(CONTRIBUTION_COMPARISON_TRACE_ID_BLOCKER, status["blocking_gaps"])
        self.assertIn(CONTRIBUTION_REFRESH_SCOPE_EVIDENCE_ID, status["closed_evidence_ids"])

    def test_incomplete_contribution_refresh_scope_keeps_single_route_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_contribution_refresh_scope_artifact(
                root,
                route_ids=["falkner", "bugsy"],
                artifact_route_ids=["falkner"],
            )
            run_dir = root / "audit" / "boss_ai_debugger" / "runs" / "20260531_010000_changed_ai"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "batch_report.json").write_text("{}", encoding="utf-8")
            metadata = {
                "profile": "changed-ai",
                "run_id": "20260531_010000_changed_ai",
                "created_at": "2026-05-31T01:00:00+00:00",
                "batch_summary": {"scenario_count": 2},
                "validation": {"valid": True},
                "known_gaps": [CONTRIBUTION_REFRESH_SINGLE_ROUTE_KNOWN_GAP],
                "artifacts": {
                    "batch_report": "audit\\boss_ai_debugger\\runs\\20260531_010000_changed_ai\\batch_report.json",
                },
                "artifact_hashes": {"batch_report": "HASH"},
            }
            (run_dir / "metadata.json").write_text(json.dumps(metadata) + "\n", encoding="utf-8")

            refresh_scope = changed_ai_contribution_refresh_scope_status(root, metadata)
            status = changed_ai_god_suite_status(root)

        self.assertFalse(refresh_scope["ready"])
        self.assertEqual(refresh_scope["missing_route_ids"], ["bugsy"])
        self.assertIn(
            "changed_ai_contribution_refresh_scope_missing_routes",
            refresh_scope["blocking_gaps"],
        )
        self.assertIn(CONTRIBUTION_REFRESH_SINGLE_ROUTE_BLOCKER, status["blocking_gaps"])
        self.assertNotIn(CONTRIBUTION_REFRESH_SCOPE_EVIDENCE_ID, status["closed_evidence_ids"])

    def test_changed_ai_all_resolved_known_gaps_mark_suite_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            route_ids = ["falkner", "bugsy"]
            write_contribution_refresh_scope_artifact(root, route_ids=route_ids)
            write_pre_choice_artifact_for_existing_manifest(root)
            scenarios = write_changed_ai_scenarios(root)
            write_score_materialization_artifact(
                root,
                [
                    "generated_spikes_spin_1_00000",
                    "generated_spikes_spin_1_00001",
                    "generated_setup_heal_1_00000",
                ],
            )
            differential_path, materialization_path = write_contribution_trace_id_artifacts(
                root,
                matched_ids=["generated_spikes_spin_1_00004"],
                materialized_ids=["generated_spikes_spin_1_00004"],
            )
            run_dir = root / "audit" / "boss_ai_debugger" / "runs" / "20260531_010000_changed_ai"
            (run_dir / "batch_report.json").write_text("{}", encoding="utf-8")
            metadata = {
                "profile": "changed-ai",
                "run_id": "20260531_010000_changed_ai",
                "created_at": "2026-05-31T01:00:00+00:00",
                "batch_summary": {"scenario_count": 3},
                "validation": {"valid": True},
                "known_gaps": [
                    CONTRIBUTION_REFRESH_SINGLE_ROUTE_KNOWN_GAP,
                    SCORE_MATERIALIZATION_TARGETED_KNOWN_GAP,
                    CONTRIBUTION_COMPARISON_TRACE_ID_KNOWN_GAP,
                    PRE_CHOICE_REPLAY_KNOWN_GAP,
                ],
                "artifacts": {
                    "batch_report": "audit\\boss_ai_debugger\\runs\\20260531_010000_changed_ai\\batch_report.json",
                    "scenarios": str(scenarios.relative_to(root)),
                    "differential": str(differential_path.relative_to(root)),
                    "rom_score_materialization": str(materialization_path.relative_to(root)),
                },
                "artifact_hashes": {
                    "batch_report": "HASH",
                    "scenarios": "HASH",
                    "differential": "HASH",
                    "rom_score_materialization": "HASH",
                },
            }
            (run_dir / "metadata.json").write_text(json.dumps(metadata) + "\n", encoding="utf-8")
            questions = root / "questions.jsonl"
            questions.write_text(
                json.dumps(
                    {
                        "id": "boss_ai_changed_ai_god_suite",
                        "requirement": "changed AI proof",
                        "surface": "boss_ai",
                        "status": "missing_evidence",
                        "blocking_gaps": ["changed_ai_god_suite_not_implemented"],
                        "next_command": "python -m tools.boss_ai_debugger run-suite --profile changed-ai",
                        "disproof_standard": "changed AI cannot silently avoid proof refresh",
                        "missing_proof_artifact_count": 1,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            status = changed_ai_god_suite_status(root)
            report = build_god_report(questions_path=questions, root=root, include_universe=False)

        self.assertTrue(status["ready"])
        self.assertTrue(status["completion_ready"])
        self.assertEqual(status["blocking_gaps"], [])
        self.assertTrue(report["boss_ai_god_ready"])
        self.assertEqual(report["questions"][0]["status"], "PASS")
        self.assertEqual(report["counters"]["missing_proof_artifact_count"], 0)
        self.assertIn(PRE_CHOICE_REPLAY_EVIDENCE_ID, status["closed_evidence_ids"])
        self.assertIn(SCORE_MATERIALIZATION_FULL_EVIDENCE_ID, status["closed_evidence_ids"])
        self.assertIn(CONTRIBUTION_COMPARISON_TRACE_ID_EVIDENCE_ID, status["closed_evidence_ids"])
        self.assertIn(CONTRIBUTION_REFRESH_SCOPE_EVIDENCE_ID, status["closed_evidence_ids"])

    def test_changed_ai_promoted_summary_is_preferred_over_latest_raw_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            promoted_dir = root / "audit" / "boss_ai_debugger" / "deity_benchmark" / "artifacts"
            promoted_dir.mkdir(parents=True)
            old_run = root / "audit" / "boss_ai_debugger" / "runs" / "20260531_010000_changed_ai"
            new_run = root / "audit" / "boss_ai_debugger" / "runs" / "20260531_020000_changed_ai"
            old_run.mkdir(parents=True)
            new_run.mkdir(parents=True)
            (old_run / "review_queue.json").write_text("{}", encoding="utf-8")
            (root / "audit" / "boss_ai_trace").mkdir(parents=True)
            (root / "audit" / "boss_ai_trace" / "live_capture_manifest.json").write_text("{}", encoding="utf-8")
            (new_run / "metadata.json").write_text(
                json.dumps(
                    {
                        "profile": "changed-ai",
                        "run_id": "newer_raw",
                        "created_at": "2026-05-31T02:00:00+00:00",
                        "batch_summary": {"scenario_count": 1},
                        "validation": {"valid": True},
                        "known_gaps": [],
                        "artifacts": {},
                        "artifact_hashes": {"metadata": "HASH"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (promoted_dir / "changed_ai_dry_run.json").write_text(
                json.dumps(
                    {
                        "kind": "boss_ai_deity_changed_ai_summary",
                        "status": "changed_ai_summary_ready",
                        "hash_basis": {
                            "ready": True,
                            "manifest_path": "audit\\boss_ai_trace\\live_capture_manifest.json",
                        },
                        "targeted_generators": {
                            "artifact": "audit\\boss_ai_debugger\\runs\\20260531_010000_changed_ai\\scenarios.jsonl",
                            "scenario_count": 1,
                        },
                        "review_queue": {
                            "artifact": "audit\\boss_ai_debugger\\runs\\20260531_010000_changed_ai\\review_queue.json",
                        },
                        "changed_ai_run": {
                            "profile": "changed-ai",
                            "run_id": "promoted",
                            "created_at": "2026-05-31T01:00:00+00:00",
                            "batch_summary": {"scenario_count": 1},
                            "validation": {"valid": True},
                            "known_gaps": [
                                "changed-ai suite records ROM rebuild as skipped unless explicitly requested.",
                            ],
                            "artifacts": {
                                "review_queue": "audit\\boss_ai_debugger\\runs\\20260531_010000_changed_ai\\review_queue.json",
                            },
                            "artifact_hashes": {"review_queue": "HASH"},
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            status = changed_ai_god_suite_status(root)

        self.assertEqual(status["run_id"], "promoted")
        self.assertEqual(status["evidence_source"], "promoted_deity_summary")
        self.assertEqual(
            status["metadata_path"],
            "audit/boss_ai_debugger/deity_benchmark/artifacts/changed_ai_dry_run.json",
        )

    def test_changed_ai_metadata_unmapped_known_gap_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "audit" / "boss_ai_debugger" / "runs" / "20260531_010000_changed_ai"
            run_dir.mkdir(parents=True)
            (run_dir / "batch_report.json").write_text("{}", encoding="utf-8")
            (run_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "profile": "changed-ai",
                        "run_id": "20260531_010000_changed_ai",
                        "created_at": "2026-05-31T01:00:00+00:00",
                        "batch_summary": {"scenario_count": 1},
                        "validation": {"valid": True},
                        "known_gaps": ["new exact changed-AI gap"],
                        "artifacts": {
                            "batch_report": "audit\\boss_ai_debugger\\runs\\20260531_010000_changed_ai\\batch_report.json",
                        },
                        "artifact_hashes": {"batch_report": "HASH"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            status = changed_ai_god_suite_status(root)

        self.assertFalse(status["ready"])
        self.assertTrue(status["partial_evidence_ready"])
        self.assertIn("changed_ai_known_gap_unmapped", status["blocking_gaps"])
        self.assertEqual(status["unmapped_known_gaps"], ["new exact changed-AI gap"])

    def test_changed_ai_missing_metadata_reports_concrete_missing_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            questions = root / "questions.jsonl"
            questions.write_text(
                json.dumps(
                    {
                        "id": "boss_ai_changed_ai_god_suite",
                        "requirement": "changed AI proof",
                        "surface": "boss_ai",
                        "status": "missing_evidence",
                        "blocking_gaps": ["changed_ai_god_suite_not_implemented"],
                        "next_command": "python -m tools.boss_ai_debugger run-suite --profile changed-ai",
                        "disproof_standard": "changed AI cannot silently avoid proof refresh",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_god_report(questions_path=questions, root=root, include_universe=False)

        question = report["questions"][0]
        self.assertEqual(question["proof_status"], "missing_evidence")
        self.assertNotIn("changed_ai_god_suite_not_implemented", question["blocking_gaps"])
        self.assertIn("changed_ai_run_metadata_missing", question["blocking_gaps"])


if __name__ == "__main__":
    unittest.main()
