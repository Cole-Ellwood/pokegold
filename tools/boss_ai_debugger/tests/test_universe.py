from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.universe import (
    EXHAUSTIVE_WITNESS_CATALOG_EVIDENCE_ID,
    add_witness_evidence_from_counterfactual_materialization,
    add_witness_evidence_from_score_materialization,
    add_witness_evidence_from_deity_packets,
    build_boss_ai_universe_report,
    build_exhaustive_class_witness_catalog,
    build_exhaustive_class_witness_inventory,
    build_witness_evidence_from_contribution_summary,
    contribution_reports_from_score_materializations,
    scan_boss_ai_label_rows,
)


def switch_roll_boundary_packet() -> dict[str, object]:
    return {
        "proof_status": {
            "present_ids": [
                "observed_rom_decision",
                "switch_path",
                "switch_materialization",
            ],
        },
        "source_anchors": [
            {
                "anchor_status": "mapped",
                "rule_id": "switch.compute_switch_confidence",
                "source_label": "BossAI_ComputeSwitchConfidence",
            },
            {
                "anchor_status": "mapped",
                "rule_id": "switch.try_switch",
                "source_label": "BossAI_TrySwitch",
                "parent_label": "BossAI_TrySwitch",
            },
            {
                "anchor_status": "mapped",
                "rule_id": "switch.get_switch_threshold",
                "source_label": "BossAI_GetSwitchThreshold",
            },
        ],
        "rom_evidence": [
            {
                "kind": "rom_switch_materialization",
                "checked_count": 12,
                "error_count": 0,
                "skipped_count": 0,
                "policy_disagreement_count": 0,
                "verdicts": [
                    {
                        "scenario_id": "generated_switch_sack_1_00006_preserve_wincon_over_comfort_damage",
                        "status": "pass",
                        "family": "switch_sack",
                        "expected_switch": True,
                        "rom": {
                            "source": "trace_rom_pyboy_switch",
                            "switch_gate_evaluated": True,
                            "observation_status": "switch_proposal_observed",
                            "observed_decision": True,
                            "observed_switch_path": True,
                            "proposed_switch": True,
                            "actual_switch": False,
                            "chosen_move": 0,
                            "switch_confidence": 99,
                            "switch_param": 49,
                            "switch_index": 0,
                        },
                        "switch_roll": {
                            "available": True,
                            "proof_status": "source_mirrored_final_switch_roll_from_observed_confidence",
                            "confidence": 99,
                            "probability_exact": True,
                            "switch_chance_threshold": 230,
                            "switch_probability": 230 / 256,
                            "possible_switch_probabilities": [
                                {
                                    "effective_threshold": 60,
                                    "switch_chance_threshold": 230,
                                    "switch_probability": 230 / 256,
                                },
                                {
                                    "effective_threshold": 78,
                                    "switch_chance_threshold": 230,
                                    "switch_probability": 230 / 256,
                                },
                            ],
                        },
                    }
                ],
            }
        ],
    }


def enemy_under_pressure_boundary_packet() -> dict[str, object]:
    observed_rom_decision = {
        "available": True,
        "kind": "rom_score_materialization",
        "scenario_id": "generated_spikes_spin_1_00000",
        "status": "pass",
        "policy": {
            "verdict": "pass",
            "rom_best_action_id": "move_spikes",
        },
        "python_agreement": {
            "contribution_mismatches": 0,
            "score_bytes_match": True,
            "selector_top_match": True,
            "hook_equivalence": {
                "checked": True,
                "match": True,
                "chosen_match": True,
                "score_bytes_match": True,
            },
        },
        "decision": {
            "selector_path": {
                "source": "rom_score_materialization_final_scores",
                "best_action_id": "move_spikes",
                "best_score": 37,
                "second_action_id": "move_sludge_bomb",
                "second_score": 38,
                "score_gap": 1,
            }
        },
    }
    return {
        "scenario_id": "generated_spikes_spin_1_00000",
        "family": "spikes_spin",
        "deity_evidence_marker": "BOSS_AI_DEITY_PROOF_COMPLETE",
        "proof_blockers": [],
        "proof_status": {
            "status": "explained",
            "blockers": [],
            "missing_ids": [],
            "present_ids": [
                "observed_rom_decision",
                "candidate_scores",
                "score_bytes",
                "selector_path",
                "rom_contribution_deltas",
                "score_rule.rom_delta_observed",
                "python_contribution.normalized",
                "rom_python_agreement.reported",
            ],
        },
        "candidate_scores": [
            {
                "action_id": "move_spikes",
                "contributions": [
                    {
                        "rule_id": "move.apply_move_model.enemy_under_pressure",
                        "before": 20,
                        "after": 19,
                        "delta": -1,
                    }
                ],
            }
        ],
        "python_mirror": {
            "rom_comparison": {
                "contribution_mismatches": 0,
                "score_bytes_match": True,
                "selector_top_match": True,
            }
        },
        "source_anchors": [
            {
                "anchor_status": "mapped",
                "rule_id": "move.apply_move_model.enemy_under_pressure",
                "source_label": ".EnemyUnderPressure",
                "parent_label": "BossAI_ApplyMoveModel",
            },
            {
                "anchor_status": "mapped",
                "rule_id": "move.apply_lookahead_to_top_move_candidates",
                "source_label": "BossAI_ApplyLookaheadToTopMoveCandidates",
            },
        ],
        "observed_rom_decision": observed_rom_decision,
        "rom_evidence": [observed_rom_decision],
        "rom_contributions": {
            "available": True,
            "matched_trace_count": 1,
            "unmatched_trace_ids": [],
            "events": [
                {
                    "trace_id": "generated_spikes_spin_1_00000",
                    "rule_id": "move.apply_move_model.enemy_under_pressure",
                    "before": 20,
                    "after": 19,
                    "delta": -1,
                    "operation": "encourage_tier_weight",
                    "candidate": {
                        "kind": "move",
                        "move_id": 191,
                        "move_name": "SPIKES",
                        "slot_index": 0,
                    },
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "move.apply_move_model.enemy_under_pressure",
                        "source_label": ".EnemyUnderPressure",
                        "parent_label": "BossAI_ApplyMoveModel",
                    },
                }
            ],
        },
    }


def apply_spikes_layer_bias_negative_packet() -> dict[str, object]:
    observed_rom_decision = enemy_under_pressure_boundary_packet()["observed_rom_decision"]
    return {
        "scenario_id": "generated_spikes_spin_1_00000",
        "family": "spikes_spin",
        "deity_evidence_marker": "BOSS_AI_DEITY_PROOF_COMPLETE",
        "proof_blockers": [],
        "proof_status": {
            "status": "explained",
            "blockers": [],
            "missing_ids": [],
            "present_ids": [
                "observed_rom_decision",
                "candidate_scores",
                "score_bytes",
                "selector_path",
                "rom_contribution_deltas",
                "score_rule.rom_delta_observed",
                "public_info_inputs",
                "public_reads.snapshotted",
                "python_contribution.normalized",
                "rom_python_agreement.reported",
            ],
        },
        "candidate_scores": [
            {
                "action_id": "move_sludge_bomb",
                "blocked": False,
                "contributions": [
                    {
                        "after": 38,
                        "before": 20,
                        "delta": 18,
                        "rule": "lookahead",
                        "rule_id": "move.apply_lookahead_to_top_move_candidates",
                    }
                ],
                "final_score": 38,
                "initial_score": 20,
                "kind": "move",
                "name": "Sludge Bomb",
                "pre_lookahead_score": 20,
                "slot": 2,
            }
        ],
        "observed_rom_decision": observed_rom_decision,
        "python_mirror": {
            "rom_comparison": {
                "contribution_mismatches": 0,
                "score_bytes_match": True,
                "selector_top_match": True,
            }
        },
        "public_info_inputs": {
            "predicate_branches": [
                {
                    "predicate_id": "spikes_existing_layer_count",
                    "outcome": "zero_existing_layers",
                    "snapshot": {
                        "wPlayerScreens": {
                            "available": True,
                            "kind": "byte_range",
                            "values": [0],
                        }
                    },
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "classification": "public_info",
                        "coverage_mode": "rom_score_execution_hook",
                        "line": 2121,
                        "parent_label": "BossAI_ApplyMoveModel",
                        "public_reads": ["wBossAITurnsElapsed", "wPlayerScreens"],
                        "rule_id": "move.apply_move_model.apply_spikes_layer_bias",
                        "source_file": "engine\\battle\\ai\\boss_policy_move.asm",
                        "source_label": ".ApplySpikesLayerBias",
                    },
                    "trace_id": "generated_spikes_spin_1_00000",
                }
            ]
        },
        "rom_contributions": {
            "available": True,
            "matched_trace_count": 1,
            "unmatched_trace_ids": [],
            "events": [
                {
                    "trace_id": "generated_spikes_spin_1_00000",
                    "rule_id": "move.apply_lookahead_to_top_move_candidates",
                    "before": 20,
                    "after": 38,
                    "delta": 18,
                    "operation": "apply_signed_lookahead_delta",
                    "candidate": {
                        "kind": "move",
                        "move_id": 188,
                        "move_name": "SLUDGE_BOMB",
                        "slot_index": 1,
                    },
                }
            ],
        },
    }


class BossAiUniverseTests(unittest.TestCase):
    def test_universe_report_counts_unmapped_labels_and_missing_classes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "boss_policy_unit.asm"
            rom = root / "unit.gbc"
            symbols = root / "unit.sym"
            map_path = root / "unit.map"
            rom.write_bytes(b"rom")
            symbols.write_text("01:4000 BossAI_SelectMove\n", encoding="utf-8")
            map_path.write_text("map", encoding="utf-8")
            source.write_text("BossAI_SelectMove::\n.NewBranch:\n\tret\n", encoding="utf-8")
            rule_map = {
                "schema_version": 1,
                "source_hashes": {"boss_policy_unit.asm": "HASH"},
                "rules": [
                    {
                        "rule_id": "move.select_move",
                        "source_file": "boss_policy_unit.asm",
                        "source_label": "BossAI_SelectMove",
                        "line": 1,
                        "parent_label": "BossAI_SelectMove",
                        "classification": "platform_boundary",
                        "public_reads": [],
                        "expected_public_inputs": [],
                        "executable": True,
                        "dynamic_coverage_target": True,
                        "score_trace_target": True,
                        "requires_public_read_provenance": False,
                        "coverage_mode": "rom_score_execution_hook",
                    }
                ],
            }

            report = build_boss_ai_universe_report(
                source_paths=(source,),
                rule_map_data=rule_map,
                rom_contribution_trace_paths=[],
                rom_path=rom,
                symbols_path=symbols,
                root=root,
            )

        self.assertEqual(report["kind"], "boss_ai_debugger_universe")
        self.assertEqual(report["proof_status"], "missing_evidence")
        self.assertEqual(report["counters"]["missing_reachable_label_count"], 0)
        self.assertEqual(report["counters"]["missing_rule_count"], 0)
        self.assertEqual(report["counters"]["missing_class_id_count"], 0)
        self.assertEqual(report["counters"]["missing_branch_count"], 1)
        self.assertEqual(report["counters"]["missing_witness_role_count"], 4)
        self.assertIn("boss_ai_exhaustive_class_witness_roles_missing", report["blocking_gaps"])
        self.assertNotIn("boss_ai_universe_has_unmapped_reachable_labels", report["blocking_gaps"])
        by_label = {row["source_label"]: row for row in report["surface_rows"]}
        self.assertEqual(by_label[".NewBranch"]["reachable_status"], "reachable_parent_rule_detail")
        self.assertEqual(by_label[".NewBranch"]["rule_id"], "move.select_move")
        self.assertIn("not an independent proof target", by_label[".NewBranch"]["unsupported_reason"])
        self.assertTrue(report["canonical_class_rows"][0]["class_id"].startswith("csc_"))
        self.assertTrue(report["canonical_class_rows"][0]["class_fingerprint"])
        self.assertTrue(report["canonical_class_rows"][0]["canonical_state_class_valid"])
        self.assertIn("explain-decision", report["canonical_class_rows"][0]["materializer_command"])
        inventory = report["exhaustive_class_witness_inventory"]
        self.assertFalse(inventory["ready"])
        self.assertEqual(inventory["status_counts"]["not_applicable"], 1)
        self.assertEqual(inventory["first_missing_roles"][0]["witness_role"], "positive")
        catalog = report["exhaustive_class_witness_catalog"]
        self.assertTrue(catalog["ready"])
        self.assertEqual(catalog["proof_status"], "catalog_only")
        self.assertIn(EXHAUSTIVE_WITNESS_CATALOG_EVIDENCE_ID, catalog["closed_evidence_ids"])
        self.assertEqual(catalog["required_witness_class_count"], 4)
        self.assertEqual(catalog["cataloged_witness_class_count"], 4)
        self.assertEqual(catalog["missing_rom_proof_role_count"], 4)
        self.assertEqual(catalog["missing_witness_class_count"], 0)
        self.assertEqual(catalog["invalid_witness_class_count"], 0)
        self.assertIn("boss_ai_exhaustive_class_witness_roles_missing", catalog["does_not_close"])
        self.assertTrue(catalog["catalog_rows"][0]["witness_class_id"].startswith("csc_"))
        self.assertEqual(catalog["catalog_rows"][0]["proof_status"], "missing_proof_artifact")

    def test_new_unclassified_label_is_reachable_unmapped_until_rule_mapped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "boss_policy_unit.asm"
            source.write_text("BossAI_NewThing::\n.loop:\n.CustomBranch:\n\tret\n", encoding="utf-8")

            rows = scan_boss_ai_label_rows(
                (source,),
                rule_by_full_symbol={},
                root=root,
            )

        by_label = {row["source_label"]: row for row in rows}
        self.assertEqual(by_label["BossAI_NewThing"]["reachable_status"], "reachable_unmapped_label")
        self.assertEqual(by_label[".CustomBranch"]["reachable_status"], "reachable_unmapped_label")
        self.assertEqual(by_label[".loop"]["reachable_status"], "generic_control_flow_ignored")

    def test_current_sources_are_rom_proven_without_boundary_gaps(self) -> None:
        report = build_boss_ai_universe_report()

        self.assertEqual(report["proof_status"], "complete")
        self.assertEqual(report["counters"]["missing_reachable_label_count"], 0)
        self.assertEqual(report["counters"]["missing_rule_count"], 0)
        self.assertEqual(report["counters"]["missing_witness_role_count"], 0)
        self.assertEqual(report["blocking_gaps"], [])
        self.assertNotIn("boss_ai_universe_has_unmapped_reachable_labels", report["blocking_gaps"])
        self.assertNotIn("boss_ai_universe_has_labels_without_rule_ids", report["blocking_gaps"])
        self.assertNotIn("boss_ai_exhaustive_class_witness_roles_missing", report["blocking_gaps"])
        self.assertTrue(
            all(
                row["status"] == "rom_proven"
                for row in report["exhaustive_class_witness_catalog"]["catalog_rows"]
            )
        )

    def test_exhaustive_witness_inventory_requires_public_read_role_only_for_public_rules(self) -> None:
        rows = [
            {
                "rule_id": "move.private",
                "class_id": "csc_private",
                "requires_public_read_provenance": False,
                "family": "mastery_policy",
                "decision_surface": "move_score",
                "proof_mode": "rom_score_materialization",
            },
            {
                "rule_id": "move.public",
                "class_id": "csc_public",
                "requires_public_read_provenance": True,
                "family": "selector_edges",
                "decision_surface": "boss_ai_rule",
                "proof_mode": "rom_contribution_trace",
            },
        ]

        inventory = build_exhaustive_class_witness_inventory(rows)

        self.assertFalse(inventory["ready"])
        self.assertEqual(inventory["rule_count"], 2)
        self.assertEqual(inventory["missing_witness_role_count"], 9)
        self.assertEqual(inventory["satisfied_witness_role_count"], 0)
        self.assertEqual(inventory["status_counts"]["not_applicable"], 1)
        public_roles = [
            row["witness_role"]
            for row in inventory["first_missing_roles"]
            if row["rule_id"] == "move.public"
        ]
        self.assertIn("public_read_provenance", public_roles)

    def test_exhaustive_witness_inventory_credits_only_observed_roles(self) -> None:
        rows = [
            {
                "rule_id": "move.public",
                "class_id": "csc_public",
                "requires_public_read_provenance": True,
                "family": "selector_edges",
                "decision_surface": "boss_ai_rule",
                "proof_mode": "rom_contribution_trace",
            },
        ]
        evidence = {
            ("move.public", "positive"): [
                {
                    "artifact": "audit/boss_ai_debugger/rom_contribution_trace_unit.json",
                    "evidence_kind": "rom_rule_execution",
                }
            ],
            ("move.public", "public_read_provenance"): [
                {
                    "artifact": "audit/boss_ai_debugger/rom_contribution_trace_unit.json",
                    "evidence_kind": "public_read_probe",
                }
            ],
        }

        inventory = build_exhaustive_class_witness_inventory(
            rows,
            witness_evidence=evidence,
        )

        self.assertFalse(inventory["ready"])
        self.assertEqual(inventory["missing_witness_role_count"], 3)
        self.assertEqual(inventory["satisfied_witness_role_count"], 2)
        self.assertEqual(inventory["status_counts"]["satisfied"], 2)
        satisfied_roles = {
            row["witness_role"] for row in inventory["first_satisfied_roles"]
        }
        self.assertEqual(satisfied_roles, {"positive", "public_read_provenance"})

    def test_exhaustive_witness_catalog_generates_canonical_targets_without_closing_proofs(self) -> None:
        identity = {
            "rom_sha256": "A" * 64,
            "symbols_sha256": "B" * 64,
            "map_sha256": "C" * 64,
            "rule_map_sha256": "D" * 64,
            "source_tree_sha256": "test",
            "dirty_diff_hash": "E" * 64,
        }
        rows = [
            {
                "rule_id": "move.public",
                "class_id": "csc_public",
                "requires_public_read_provenance": True,
                "family": "selector_edges",
                "decision_surface": "boss_ai_rule",
                "proof_mode": "rom_contribution_trace",
                "source_file": "engine/battle/ai/boss_policy_move.asm",
                "line": 10,
                "source_label": "BossAI_SelectMove",
                "parent_label": "BossAI_SelectMove",
                "expected_public_inputs": ["player_hp"],
                "materializer_command": "python -m tools.boss_ai_debugger explain-decision",
            },
            {
                "rule_id": "move.private",
                "class_id": "csc_private",
                "requires_public_read_provenance": False,
                "family": "mastery_policy",
                "decision_surface": "move_score",
                "proof_mode": "rom_score_materialization",
                "source_file": "engine/battle/ai/boss_policy_move.asm",
                "line": 20,
                "source_label": ".Private",
                "parent_label": "BossAI_SelectMove",
                "expected_public_inputs": [],
                "materializer_command": "python -m tools.boss_ai_debugger explain-decision",
            },
        ]

        catalog = build_exhaustive_class_witness_catalog(rows, identity=identity)

        self.assertTrue(catalog["ready"])
        self.assertEqual(catalog["required_witness_class_count"], 9)
        self.assertEqual(catalog["cataloged_witness_class_count"], 9)
        self.assertEqual(catalog["role_counts"]["public_read_provenance"], 1)
        self.assertEqual(catalog["duplicate_class_id_count"], 0)
        class_ids = [row["witness_class_id"] for row in catalog["catalog_rows"]]
        self.assertEqual(len(class_ids), len(set(class_ids)))
        self.assertTrue(all(row["canonical_state_class_valid"] for row in catalog["catalog_rows"]))
        self.assertTrue(all(row["proof_status"] == "missing_proof_artifact" for row in catalog["catalog_rows"]))
        self.assertIn("exhaustive_class_proofs", catalog["does_not_close"])

    def test_universe_positive_witness_uses_rom_contribution_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "boss_policy_unit.asm"
            rom = root / "unit.gbc"
            symbols = root / "unit.sym"
            map_path = root / "unit.map"
            trace = root / "rom_contribution_trace_unit.json"
            rom.write_bytes(b"rom")
            symbols.write_text("01:4000 BossAI_SelectMove\n", encoding="utf-8")
            map_path.write_text("map", encoding="utf-8")
            source.write_text("BossAI_SelectMove::\n\tret\n", encoding="utf-8")
            trace.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "trace_rom_pyboy_hooks",
                        "save_state": "route:unit",
                        "trace_basis": {},
                        "chosen": {},
                        "move_ids": [],
                        "move_scores": [],
                        "pre_model_scores": [],
                        "post_model_scores": [],
                        "rule_entry_count": 1,
                        "executed_rule_count": 1,
                        "executed_rule_ids": ["move.select_move"],
                        "rule_entries": [
                            {
                                "event_type": "rule_enter",
                                "source": {
                                    "rule_id": "move.select_move",
                                    "classification": "platform_boundary",
                                },
                            }
                        ],
                        "predicate_branch_entry_count": 0,
                        "predicate_branch_entries": [],
                        "public_read_probe_entry_count": 0,
                        "public_read_probe_entries": [],
                        "event_count": 0,
                        "changed_event_count": 0,
                        "events": [],
                        "known_limits": [],
                    }
                ),
                encoding="utf-8",
            )
            rule_map = {
                "schema_version": 1,
                "source_hashes": {"boss_policy_unit.asm": "HASH"},
                "rules": [
                    {
                        "rule_id": "move.select_move",
                        "source_file": "boss_policy_unit.asm",
                        "source_label": "BossAI_SelectMove",
                        "line": 1,
                        "parent_label": "BossAI_SelectMove",
                        "classification": "platform_boundary",
                        "public_reads": [],
                        "expected_public_inputs": [],
                        "executable": True,
                        "dynamic_coverage_target": True,
                        "score_trace_target": False,
                        "requires_public_read_provenance": False,
                        "coverage_mode": "rom_contribution_trace",
                    }
                ],
            }

            report = build_boss_ai_universe_report(
                source_paths=(source,),
                rule_map_data=rule_map,
                rom_contribution_trace_paths=[trace],
                rom_path=rom,
                symbols_path=symbols,
                root=root,
            )

        inventory = report["exhaustive_class_witness_inventory"]
        self.assertEqual(report["counters"]["missing_branch_count"], 0)
        self.assertEqual(inventory["satisfied_witness_role_count"], 1)
        self.assertEqual(inventory["missing_witness_role_count"], 3)
        self.assertEqual(inventory["first_satisfied_roles"][0]["witness_role"], "positive")

    def test_universe_boundary_witness_uses_predicate_branch_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "rom_contribution_trace_unit.json"
            trace.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "trace_rom_pyboy_hooks",
                        "save_state": "route:unit",
                        "trace_basis": {},
                        "chosen": {},
                        "move_ids": [],
                        "move_scores": [],
                        "pre_model_scores": [],
                        "post_model_scores": [],
                        "rule_entry_count": 0,
                        "rule_entries": [],
                        "predicate_branch_entry_count": 1,
                        "predicate_branch_entries": [
                            {
                                "event_type": "predicate_branch",
                                "predicate": {
                                    "predicate_id": "unit_boundary",
                                    "outcome": "threshold_met",
                                },
                                "public_input_snapshot": {
                                    "wPlayerScreens": {"values": [1]},
                                },
                                "source": {
                                    "rule_id": "move.public",
                                    "classification": "public_info",
                                },
                            }
                        ],
                        "public_read_probe_entry_count": 0,
                        "public_read_probe_entries": [],
                        "event_count": 0,
                        "changed_event_count": 0,
                        "events": [],
                        "known_limits": [],
                    }
                ),
                encoding="utf-8",
            )

            evidence = build_witness_evidence_from_contribution_summary(
                {
                    "artifacts": [
                        {
                            "artifact": str(trace),
                            "executed_rule_ids": [],
                        }
                    ]
                },
                root=root,
            )

        boundary = evidence[("move.public", "boundary")][0]
        self.assertEqual(boundary["evidence_kind"], "predicate_branch_boundary_snapshot")
        self.assertEqual(boundary["predicate_id"], "unit_boundary")
        self.assertEqual(boundary["outcome"], "threshold_met")
        self.assertEqual(boundary["snapshot_keys"], ["wPlayerScreens"])
        self.assertNotIn(("move.public", "negative"), evidence)
        self.assertNotIn(("move.public", "counterfactual_flip"), evidence)

    def test_merged_contribution_summary_expands_nested_artifacts_for_boundary_credit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "rom_contribution_trace_nested.json"
            trace.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "trace_rom_pyboy_hooks",
                        "save_state": "route:unit",
                        "trace_basis": {},
                        "chosen": {},
                        "move_ids": [],
                        "move_scores": [],
                        "pre_model_scores": [],
                        "post_model_scores": [],
                        "rule_entry_count": 0,
                        "rule_entries": [],
                        "predicate_branch_entry_count": 1,
                        "predicate_branch_entries": [
                            {
                                "event_type": "predicate_branch",
                                "predicate": {
                                    "predicate_id": "nested_boundary",
                                    "outcome": "threshold_met",
                                },
                                "public_input_snapshot": {
                                    "wPlayerScreens": {"values": [1]},
                                },
                                "source": {
                                    "rule_id": "move.public",
                                    "classification": "public_info",
                                },
                            }
                        ],
                        "public_read_probe_entry_count": 0,
                        "public_read_probe_entries": [],
                        "event_count": 0,
                        "changed_event_count": 0,
                        "events": [],
                        "known_limits": [],
                    }
                ),
                encoding="utf-8",
            )

            evidence = build_witness_evidence_from_contribution_summary(
                {
                    "artifacts": [
                        {
                            "artifact_count": 1,
                            "executed_rule_ids": ["move.public"],
                            "artifacts": [
                                {
                                    "artifact": str(trace),
                                    "executed_rule_ids": ["move.public"],
                                }
                            ],
                        }
                    ]
                },
                root=root,
            )

        positive = evidence[("move.public", "positive")][0]
        boundary = evidence[("move.public", "boundary")][0]
        self.assertEqual(positive["artifact"], str(trace))
        self.assertEqual(boundary["artifact"], str(trace))
        self.assertEqual(boundary["evidence_kind"], "predicate_branch_boundary_snapshot")
        self.assertEqual(boundary["predicate_id"], "nested_boundary")

    def test_public_read_witness_uses_rule_entry_snapshot_without_boundary_credit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "rom_contribution_trace_unit.json"
            trace.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "trace_rom_pyboy_hooks",
                        "save_state": "route:unit",
                        "trace_basis": {},
                        "chosen": {},
                        "move_ids": [],
                        "move_scores": [],
                        "pre_model_scores": [],
                        "post_model_scores": [],
                        "rule_entry_count": 1,
                        "rule_entries": [
                            {
                                "event_type": "rule_enter",
                                "public_input_snapshot": {
                                    "wPlayerUsedMoves": {"values": [1, 2, 3, 4]},
                                },
                                "source": {
                                    "rule_id": "move.public",
                                    "classification": "public_info",
                                    "public_reads": ["wPlayerUsedMoves"],
                                },
                            }
                        ],
                        "predicate_branch_entry_count": 0,
                        "predicate_branch_entries": [],
                        "public_read_probe_entry_count": 0,
                        "public_read_probe_entries": [],
                        "event_count": 0,
                        "changed_event_count": 0,
                        "events": [],
                        "known_limits": [],
                    }
                ),
                encoding="utf-8",
            )

            evidence = build_witness_evidence_from_contribution_summary(
                {
                    "artifacts": [
                        {
                            "artifact": str(trace),
                            "executed_rule_ids": ["move.public"],
                        }
                    ]
                },
                root=root,
            )

        public_read = evidence[("move.public", "public_read_provenance")][0]
        self.assertEqual(public_read["evidence_kind"], "rule_enter")
        self.assertEqual(public_read["snapshot_keys"], ["wPlayerUsedMoves"])
        self.assertIn(("move.public", "positive"), evidence)
        self.assertNotIn(("move.public", "boundary"), evidence)
        self.assertNotIn(("move.public", "negative"), evidence)
        self.assertNotIn(("move.public", "counterfactual_flip"), evidence)

    def test_platform_boundary_rule_entry_credits_boundary_witness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "rom_contribution_trace_unit.json"
            trace.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "trace_rom_pyboy_hooks",
                        "save_state": "route:unit",
                        "trace_basis": {},
                        "chosen": {},
                        "move_ids": [],
                        "move_scores": [],
                        "pre_model_scores": [],
                        "post_model_scores": [],
                        "rule_entry_count": 1,
                        "rule_entries": [
                            {
                                "event_type": "rule_enter",
                                "index": 7,
                                "source": {
                                    "rule_id": "switch.try_switch",
                                    "classification": "platform_boundary",
                                    "full_symbol": "BossAI_TrySwitch",
                                    "hook_bank": "0e",
                                    "hook_address": "4000",
                                    "source_label": "BossAI_TrySwitch",
                                },
                            }
                        ],
                        "predicate_branch_entry_count": 0,
                        "predicate_branch_entries": [],
                        "public_read_probe_entry_count": 0,
                        "public_read_probe_entries": [],
                        "event_count": 0,
                        "changed_event_count": 0,
                        "events": [],
                        "known_limits": [],
                    }
                ),
                encoding="utf-8",
            )

            evidence = build_witness_evidence_from_contribution_summary(
                {
                    "artifacts": [
                        {
                            "artifact": str(trace),
                            "executed_rule_ids": [],
                        }
                    ]
                },
                root=root,
            )

        boundary = evidence[("switch.try_switch", "boundary")][0]
        self.assertEqual(boundary["evidence_kind"], "rom_platform_rule_entry_boundary")
        self.assertEqual(boundary["status"], "platform_boundary_entry_observed")
        self.assertEqual(boundary["rule_entry_index"], 7)
        self.assertEqual(boundary["full_symbol"], "BossAI_TrySwitch")
        self.assertEqual(boundary["hook_bank"], "0e")
        self.assertEqual(boundary["hook_address"], "4000")
        self.assertNotIn(("switch.try_switch", "negative"), evidence)
        self.assertNotIn(("switch.try_switch", "counterfactual_flip"), evidence)

    def test_platform_boundary_rule_entry_fails_closed_without_hook_metadata(self) -> None:
        base_source = {
            "rule_id": "switch.try_switch",
            "classification": "platform_boundary",
            "full_symbol": "BossAI_TrySwitch",
            "hook_bank": "0e",
            "hook_address": "4000",
            "source_label": "BossAI_TrySwitch",
        }
        weak_sources = [
            {**base_source, "classification": "internal"},
            {key: value for key, value in base_source.items() if key != "full_symbol"},
            {key: value for key, value in base_source.items() if key != "hook_bank"},
            {key: value for key, value in base_source.items() if key != "hook_address"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifacts = []
            for index, source in enumerate(weak_sources):
                trace = root / f"rom_contribution_trace_unit_{index}.json"
                trace.write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "source": "trace_rom_pyboy_hooks",
                            "save_state": "route:unit",
                            "trace_basis": {},
                            "chosen": {},
                            "move_ids": [],
                            "move_scores": [],
                            "pre_model_scores": [],
                            "post_model_scores": [],
                            "rule_entry_count": 1,
                            "rule_entries": [
                                {
                                    "event_type": "rule_enter",
                                    "source": source,
                                }
                            ],
                            "predicate_branch_entry_count": 0,
                            "predicate_branch_entries": [],
                            "public_read_probe_entry_count": 0,
                            "public_read_probe_entries": [],
                            "event_count": 0,
                            "changed_event_count": 0,
                            "events": [],
                            "known_limits": [],
                        }
                    ),
                    encoding="utf-8",
                )
                artifacts.append({"artifact": str(trace), "executed_rule_ids": []})

            evidence = build_witness_evidence_from_contribution_summary(
                {"artifacts": artifacts},
                root=root,
            )

        self.assertEqual(evidence, {})

    def test_haki_exception_rule_entry_credits_boundary_witness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "rom_contribution_trace_haki.json"
            trace.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "trace_rom_pyboy_hooks",
                        "save_state": "route:haki_after_player",
                        "trace_basis": {},
                        "chosen": {},
                        "move_ids": [],
                        "move_scores": [],
                        "pre_model_scores": [],
                        "post_model_scores": [],
                        "rule_entry_count": 2,
                        "executed_rule_ids": [
                            "switch.oracle_haki_after_player_action",
                            "switch.commit_haki_oracle_choice",
                        ],
                        "rule_entries": [
                            {
                                "event_type": "rule_enter",
                                "index": 11,
                                "source": {
                                    "rule_id": "switch.oracle_haki_after_player_action",
                                    "classification": "haki_exception",
                                    "full_symbol": "BossAI_OracleHakiAfterPlayerAction",
                                    "hook_bank": "0e",
                                    "hook_address": "5734",
                                    "source_label": "BossAI_OracleHakiAfterPlayerAction",
                                },
                            },
                            {
                                "event_type": "rule_enter",
                                "index": 12,
                                "source": {
                                    "rule_id": "switch.commit_haki_oracle_choice",
                                    "classification": "haki_exception",
                                    "full_symbol": "BossAI_CommitHakiOracleChoice",
                                    "hook_bank": "0e",
                                    "hook_address": "57e5",
                                    "source_label": "BossAI_CommitHakiOracleChoice",
                                },
                            },
                        ],
                        "predicate_branch_entry_count": 0,
                        "predicate_branch_entries": [],
                        "public_read_probe_entry_count": 0,
                        "public_read_probe_entries": [],
                        "event_count": 0,
                        "changed_event_count": 0,
                        "events": [],
                        "known_limits": [],
                    }
                ),
                encoding="utf-8",
            )

            evidence = build_witness_evidence_from_contribution_summary(
                {
                    "artifacts": [
                        {
                            "artifact": str(trace),
                            "executed_rule_ids": [],
                        }
                    ]
                },
                root=root,
            )

        boundary = evidence[("switch.oracle_haki_after_player_action", "boundary")][0]
        self.assertEqual(boundary["evidence_kind"], "rom_haki_exception_rule_entry_boundary")
        self.assertEqual(boundary["status"], "haki_exception_boundary_entry_observed")
        self.assertEqual(boundary["rule_entry_index"], 11)
        self.assertEqual(boundary["full_symbol"], "BossAI_OracleHakiAfterPlayerAction")
        self.assertEqual(boundary["hook_bank"], "0e")
        self.assertEqual(boundary["hook_address"], "5734")
        self.assertEqual(boundary["save_state"], "route:haki_after_player")
        self.assertIn(("switch.commit_haki_oracle_choice", "boundary"), evidence)
        self.assertNotIn(("switch.oracle_haki_after_player_action", "counterfactual_flip"), evidence)

    def test_haki_exception_rule_entry_boundary_fails_closed_on_weak_traces(self) -> None:
        base_trace = {
            "schema_version": 1,
            "source": "trace_rom_pyboy_hooks",
            "save_state": "route:haki_after_player",
            "trace_basis": {},
            "chosen": {},
            "move_ids": [],
            "move_scores": [],
            "pre_model_scores": [],
            "post_model_scores": [],
            "rule_entry_count": 1,
            "executed_rule_ids": ["switch.oracle_haki_after_player_action"],
            "rule_entries": [
                {
                    "event_type": "rule_enter",
                    "source": {
                        "rule_id": "switch.oracle_haki_after_player_action",
                        "classification": "haki_exception",
                        "full_symbol": "BossAI_OracleHakiAfterPlayerAction",
                        "hook_bank": "0e",
                        "hook_address": "5734",
                    },
                }
            ],
            "predicate_branch_entry_count": 0,
            "predicate_branch_entries": [],
            "public_read_probe_entry_count": 0,
            "public_read_probe_entries": [],
            "event_count": 0,
            "changed_event_count": 0,
            "events": [],
            "known_limits": [],
        }

        def mutated(mutator: Any) -> dict[str, object]:
            trace = json.loads(json.dumps(base_trace))
            mutator(trace)
            return trace

        weak_traces = [
            mutated(lambda trace: trace.__setitem__("source", "python_model")),
            mutated(lambda trace: trace.__setitem__("save_state", "")),
            mutated(lambda trace: trace.__setitem__("executed_rule_ids", [])),
            mutated(lambda trace: trace["rule_entries"][0].__setitem__("event_type", "rule_exit")),
            mutated(lambda trace: trace["rule_entries"][0]["source"].__setitem__("classification", "internal")),
            mutated(lambda trace: trace["rule_entries"][0]["source"].__setitem__("rule_id", "move.haki_like")),
            mutated(lambda trace: trace["rule_entries"][0]["source"].__setitem__("rule_id", "switch.try_switch")),
            mutated(lambda trace: trace["rule_entries"][0]["source"].__setitem__("full_symbol", "BossAI_TrySwitch")),
            mutated(lambda trace: trace["rule_entries"][0]["source"].pop("full_symbol")),
            mutated(lambda trace: trace["rule_entries"][0]["source"].pop("hook_bank")),
            mutated(lambda trace: trace["rule_entries"][0]["source"].pop("hook_address")),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifacts = []
            for index, trace_data in enumerate(weak_traces):
                trace = root / f"rom_contribution_trace_haki_{index}.json"
                trace.write_text(json.dumps(trace_data), encoding="utf-8")
                artifacts.append({"artifact": str(trace), "executed_rule_ids": []})

            evidence = build_witness_evidence_from_contribution_summary(
                {"artifacts": artifacts},
                root=root,
            )

        self.assertEqual(evidence, {})

    def test_switch_dispatch_observation_credits_switch_boundary_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "rom_contribution_trace_switch.json"
            trace.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "trace_rom_pyboy_hooks",
                        "decision_surface": "switch_dispatch",
                        "save_state": "route:unit",
                        "trace_basis": {},
                        "switch_observation": {
                            "status": "actual_switch_observed",
                            "switch_confidence": 99,
                            "switch_param": 49,
                            "switch_index": 2,
                            "chosen_move": 0,
                        },
                        "chosen": {},
                        "move_ids": [],
                        "move_scores": [],
                        "pre_model_scores": [],
                        "post_model_scores": [],
                        "rule_entry_count": 2,
                        "rule_entries": [
                            {
                                "event_type": "rule_enter",
                                "index": 3,
                                "source": {
                                    "rule_id": "switch.haki_ready_common",
                                    "classification": "haki_exception",
                                    "full_symbol": "BossAI_HakiReadyCommon",
                                    "hook_bank": "0e",
                                    "hook_address": "5100",
                                    "source_label": "BossAI_HakiReadyCommon",
                                },
                            },
                            {
                                "event_type": "rule_enter",
                                "index": 4,
                                "source": {
                                    "rule_id": "move.not_switch",
                                    "classification": "internal",
                                    "full_symbol": "BossAI_NotSwitch",
                                    "hook_bank": "0e",
                                    "hook_address": "5200",
                                    "source_label": "BossAI_NotSwitch",
                                },
                            },
                        ],
                        "predicate_branch_entry_count": 0,
                        "predicate_branch_entries": [],
                        "public_read_probe_entry_count": 0,
                        "public_read_probe_entries": [],
                        "event_count": 0,
                        "changed_event_count": 0,
                        "events": [],
                        "known_limits": [],
                    }
                ),
                encoding="utf-8",
            )

            evidence = build_witness_evidence_from_contribution_summary(
                {
                    "artifacts": [
                        {
                            "artifact": str(trace),
                            "executed_rule_ids": [],
                        }
                    ]
                },
                root=root,
            )

        boundary = evidence[("switch.haki_ready_common", "boundary")][0]
        self.assertEqual(boundary["evidence_kind"], "rom_switch_dispatch_observation_boundary")
        self.assertEqual(boundary["status"], "switch_dispatch_observed")
        self.assertEqual(boundary["rule_entry_index"], 3)
        self.assertEqual(boundary["observation_status"], "actual_switch_observed")
        self.assertEqual(boundary["switch_confidence"], 99)
        self.assertEqual(boundary["switch_param"], 49)
        self.assertEqual(boundary["switch_index"], 2)
        self.assertNotIn(("switch.haki_ready_common", "counterfactual_flip"), evidence)
        self.assertNotIn(("move.not_switch", "boundary"), evidence)

    def test_switch_dispatch_observation_boundary_fails_closed_on_weak_traces(self) -> None:
        base_trace = {
            "schema_version": 1,
            "source": "trace_rom_pyboy_hooks",
            "decision_surface": "switch_dispatch",
            "save_state": "route:unit",
            "trace_basis": {},
            "switch_observation": {
                "status": "actual_switch_observed",
                "switch_confidence": 99,
            },
            "chosen": {},
            "move_ids": [],
            "move_scores": [],
            "pre_model_scores": [],
            "post_model_scores": [],
            "rule_entry_count": 1,
            "rule_entries": [
                {
                    "event_type": "rule_enter",
                    "source": {
                        "rule_id": "switch.haki_ready_common",
                        "classification": "haki_exception",
                        "full_symbol": "BossAI_HakiReadyCommon",
                        "hook_bank": "0e",
                        "hook_address": "5100",
                    },
                }
            ],
            "predicate_branch_entry_count": 0,
            "predicate_branch_entries": [],
            "public_read_probe_entry_count": 0,
            "public_read_probe_entries": [],
            "event_count": 0,
            "changed_event_count": 0,
            "events": [],
            "known_limits": [],
        }

        def mutated(mutator: Any) -> dict[str, object]:
            trace = json.loads(json.dumps(base_trace))
            mutator(trace)
            return trace

        weak_traces = [
            mutated(lambda trace: trace.__setitem__("source", "python_model")),
            mutated(lambda trace: trace.__setitem__("decision_surface", "rom_contribution_trace")),
            mutated(lambda trace: trace.__setitem__("switch_observation", {})),
            mutated(
                lambda trace: trace.__setitem__(
                    "switch_observation",
                    {"status": "no_switch_observation", "switch_confidence": 0},
                )
            ),
            mutated(lambda trace: trace["rule_entries"][0]["source"].__setitem__("rule_id", "move.not_switch")),
            mutated(lambda trace: trace["rule_entries"][0]["source"].pop("full_symbol")),
            mutated(lambda trace: trace["rule_entries"][0]["source"].pop("hook_bank")),
            mutated(lambda trace: trace["rule_entries"][0]["source"].pop("hook_address")),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifacts = []
            for index, trace_data in enumerate(weak_traces):
                trace = root / f"rom_contribution_trace_switch_{index}.json"
                trace.write_text(json.dumps(trace_data), encoding="utf-8")
                artifacts.append({"artifact": str(trace), "executed_rule_ids": []})

            evidence = build_witness_evidence_from_contribution_summary(
                {"artifacts": artifacts},
                root=root,
            )

        self.assertEqual(evidence, {})

    def test_score_materialization_nested_trace_credits_contribution_witnesses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialization = root / "rom_score_materialization.json"
            materialization.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "rom_score_materialization",
                        "score_replay_mode": "contribution_trace",
                        "traces": [
                            {
                                "schema_version": 1,
                                "source": "trace_rom_pyboy_hooks",
                                "trace_id": "generated_unit_margin",
                                "chosen": {"slot_index": 0},
                                "move_ids": [33, 44],
                                "move_scores": [18, 19],
                                "selector_entry_scores": [18, 19],
                                "executed_rule_ids": ["move.margin", "move.public"],
                                "rule_entries": [
                                    {
                                        "event_type": "rule_enter",
                                        "public_input_snapshot": {
                                            "wPlayerUsedMoves": {"values": [1, 2, 3, 4]},
                                        },
                                        "source": {
                                            "rule_id": "move.public",
                                            "classification": "public_info",
                                            "public_reads": ["wPlayerUsedMoves"],
                                        },
                                    }
                                ],
                                "predicate_branch_entries": [
                                    {
                                        "event_type": "predicate_branch",
                                        "predicate": {
                                            "predicate_id": "unit_boundary",
                                            "outcome": "threshold_met",
                                        },
                                        "public_input_snapshot": {
                                            "wPlayerScreens": {"values": [1]},
                                        },
                                        "source": {
                                            "rule_id": "move.public",
                                            "classification": "public_info",
                                        },
                                    }
                                ],
                                "public_read_probe_entries": [],
                                "events": [
                                    {
                                        "event_type": "score_delta",
                                        "changed": True,
                                        "candidate": {
                                            "kind": "move",
                                            "move_id": 33,
                                            "move_name": "TACKLE",
                                            "slot_index": 0,
                                        },
                                        "score_before": 21,
                                        "score_after": 18,
                                        "delta": -3,
                                        "source": {
                                            "rule_id": "move.margin",
                                            "source_label": ".Margin",
                                            "parent_label": "BossAI_ApplyMoveModel",
                                        },
                                    }
                                ],
                            }
                        ],
                        "verdicts": [],
                    }
                ),
                encoding="utf-8",
            )
            evidence: dict[tuple[str, str], list[dict[str, object]]] = {}

            add_witness_evidence_from_score_materialization(
                evidence,
                artifact_path=str(materialization),
                root=root,
            )

        self.assertIn(("move.public", "positive"), evidence)
        self.assertIn(("move.margin", "positive"), evidence)
        public_read = evidence[("move.public", "public_read_provenance")][0]
        self.assertEqual(public_read["artifact"], f"{materialization}#generated_unit_margin")
        self.assertEqual(public_read["snapshot_keys"], ["wPlayerUsedMoves"])
        self.assertIn(("move.public", "boundary"), evidence)
        boundary = evidence[("move.margin", "boundary")][0]
        self.assertEqual(boundary["evidence_kind"], "rom_score_delta_selector_margin_boundary")
        self.assertEqual(boundary["score_without_rule"], 21)
        counterfactual = evidence[("move.margin", "counterfactual_flip")][0]
        self.assertEqual(
            counterfactual["evidence_kind"],
            "rom_score_delta_selector_margin_counterfactual",
        )

    def test_score_materialization_nested_traces_feed_contribution_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialization = root / "rom_score_materialization.json"
            materialization.write_text(
                json.dumps(
                    {
                        "kind": "rom_score_materialization",
                        "traces": [
                            {
                                "source": "trace_rom_pyboy_hooks",
                                "trace_id": "trace:kept",
                                "public_read_probe_entries": [
                                    {
                                        "event_type": "public_read_probe",
                                        "probe": {
                                            "probe_id": "unit_probe",
                                            "outcome": "observed",
                                        },
                                        "public_input_snapshot": {
                                            "wPlayerScreens": {"values": [1]},
                                        },
                                        "source": {"rule_id": "move.public"},
                                    }
                                ],
                                "predicate_branch_entries": [],
                                "rule_entries": [],
                                "events": [],
                            },
                            {
                                "source": "fast_score_only",
                                "trace_id": "trace:ignored",
                                "public_read_probe_entries": [
                                    {
                                        "event_type": "public_read_probe",
                                        "probe": {
                                            "probe_id": "unit_probe",
                                            "outcome": "ignored",
                                        },
                                        "public_input_snapshot": {
                                            "wPlayerScreens": {"values": [2]},
                                        },
                                        "source": {"rule_id": "move.public"},
                                    }
                                ],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            reports = contribution_reports_from_score_materializations(
                [materialization],
                root=root,
            )

        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0]["trace_id"], "trace:kept")

    def test_score_materialization_verdict_only_credits_no_witnesses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialization = root / "rom_score_materialization.json"
            materialization.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "rom_score_materialization",
                        "score_replay_mode": "fast_score_only",
                        "traces": [],
                        "verdicts": [
                            {
                                "scenario_id": "generated_fast_only",
                                "status": "pass",
                                "rom": {"selector_entry_scores": [18, 19]},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            evidence: dict[tuple[str, str], list[dict[str, object]]] = {}

            add_witness_evidence_from_score_materialization(
                evidence,
                artifact_path=str(materialization),
                root=root,
            )

        self.assertEqual(evidence, {})

    def test_negative_witness_uses_explicit_negative_predicate_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "rom_contribution_trace_unit.json"
            trace.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "trace_rom_pyboy_hooks",
                        "save_state": "route:unit",
                        "trace_basis": {},
                        "chosen": {},
                        "move_ids": [],
                        "move_scores": [],
                        "pre_model_scores": [],
                        "post_model_scores": [],
                        "rule_entry_count": 0,
                        "rule_entries": [],
                        "predicate_branch_entry_count": 2,
                        "predicate_branch_entries": [
                            {
                                "event_type": "predicate_branch",
                                "predicate": {
                                    "predicate_id": "unit_negative",
                                    "outcome": "not_found",
                                },
                                "public_input_snapshot": {
                                    "wPlayerUsedMoves": {"values": [0, 0, 0, 0]},
                                },
                                "source": {
                                    "rule_id": "move.public",
                                    "classification": "public_info",
                                },
                            },
                            {
                                "event_type": "predicate_branch",
                                "predicate": {
                                    "predicate_id": "unit_boundary",
                                    "outcome": "threshold_met",
                                },
                                "public_input_snapshot": {
                                    "wPlayerScreens": {"values": [1]},
                                },
                                "source": {
                                    "rule_id": "move.boundary_only",
                                    "classification": "public_info",
                                },
                            },
                        ],
                        "public_read_probe_entry_count": 0,
                        "public_read_probe_entries": [],
                        "event_count": 0,
                        "changed_event_count": 0,
                        "events": [],
                        "known_limits": [],
                    }
                ),
                encoding="utf-8",
            )

            evidence = build_witness_evidence_from_contribution_summary(
                {
                    "artifacts": [
                        {
                            "artifact": str(trace),
                            "executed_rule_ids": [],
                        }
                    ]
                },
                root=root,
            )

        negative = evidence[("move.public", "negative")][0]
        self.assertEqual(negative["evidence_kind"], "predicate_branch_negative_snapshot")
        self.assertEqual(negative["status"], "negative_predicate_outcome_observed")
        self.assertEqual(negative["predicate_id"], "unit_negative")
        self.assertEqual(negative["outcome"], "not_found")
        self.assertEqual(negative["snapshot_keys"], ["wPlayerUsedMoves"])
        self.assertIn(("move.public", "boundary"), evidence)
        self.assertIn(("move.boundary_only", "boundary"), evidence)
        self.assertNotIn(("move.boundary_only", "negative"), evidence)

    def test_adaptive_lead_disabled_child_predicate_credits_parent_negative_and_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "rom_contribution_trace_unit.json"
            trace.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "trace_rom_pyboy_hooks",
                        "save_state": "route:unit",
                        "trace_basis": {},
                        "chosen": {},
                        "move_ids": [],
                        "move_scores": [],
                        "pre_model_scores": [],
                        "post_model_scores": [],
                        "rule_entry_count": 2,
                        "rule_entries": [],
                        "executed_rule_ids": [
                            "move.maybe_pick_adaptive_enemy_lead",
                            (
                                "move.maybe_pick_adaptive_enemy_lead."
                                "should_use_adaptive_lead_for_trainer"
                            ),
                        ],
                        "predicate_branch_entry_count": 1,
                        "predicate_branch_entries": [
                            {
                                "event_type": "predicate_branch",
                                "predicate": {
                                    "predicate_id": "adaptive_lead_trainer_match",
                                    "outcome": "disabled",
                                },
                                "public_input_snapshot": {
                                    "wOtherTrainerClass": {"values": [3]},
                                    "wOtherTrainerID": {"values": [1]},
                                    "AdaptiveLeadMap": {
                                        "kind": "static_table_reference",
                                    },
                                },
                                "source": {
                                    "rule_id": (
                                        "move.maybe_pick_adaptive_enemy_lead."
                                        "should_use_adaptive_lead_for_trainer"
                                    ),
                                    "classification": "public_info",
                                },
                            }
                        ],
                        "public_read_probe_entry_count": 0,
                        "public_read_probe_entries": [],
                        "event_count": 0,
                        "changed_event_count": 0,
                        "events": [],
                        "known_limits": [],
                    }
                ),
                encoding="utf-8",
            )

            evidence = build_witness_evidence_from_contribution_summary(
                {
                    "artifacts": [
                        {
                            "artifact": str(trace),
                            "executed_rule_ids": [
                                "move.maybe_pick_adaptive_enemy_lead",
                                (
                                    "move.maybe_pick_adaptive_enemy_lead."
                                    "should_use_adaptive_lead_for_trainer"
                                ),
                            ],
                        }
                    ]
                },
                root=root,
            )

        parent_negative = evidence[("move.maybe_pick_adaptive_enemy_lead", "negative")][0]
        self.assertEqual(
            parent_negative["evidence_kind"],
            "adaptive_lead_disabled_terminal_predicate",
        )
        self.assertEqual(
            parent_negative["status"],
            "negative_child_predicate_stopped_parent_observed",
        )
        self.assertEqual(parent_negative["outcome"], "disabled")
        parent_boundary = evidence[("move.maybe_pick_adaptive_enemy_lead", "boundary")][0]
        self.assertEqual(
            parent_boundary["evidence_kind"],
            "adaptive_lead_disabled_terminal_boundary",
        )
        self.assertEqual(
            parent_boundary["status"],
            "parent_boundary_child_predicate_observed",
        )
        self.assertEqual(parent_boundary["outcome"], "disabled")
        child_negative = evidence[
            (
                (
                    "move.maybe_pick_adaptive_enemy_lead."
                    "should_use_adaptive_lead_for_trainer"
                ),
                "negative",
            )
        ][0]
        self.assertEqual(child_negative["evidence_kind"], "predicate_branch_negative_snapshot")

    def test_negative_witness_uses_rule_entry_without_candidate_score_delta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "rom_contribution_trace_unit.json"
            trace.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "trace_rom_pyboy_hooks",
                        "save_state": "route:unit",
                        "trace_basis": {},
                        "chosen": {},
                        "move_ids": [],
                        "move_scores": [],
                        "pre_model_scores": [],
                        "post_model_scores": [],
                        "rule_entry_count": 3,
                        "rule_entries": [
                            {
                                "event_type": "rule_enter",
                                "index": 1,
                                "candidate": {
                                    "kind": "move",
                                    "slot_index": 0,
                                    "move_id": 33,
                                    "move_name": "TACKLE",
                                },
                                "source": {"rule_id": "move.score_rule"},
                            },
                            {
                                "event_type": "rule_enter",
                                "index": 2,
                                "candidate": {
                                    "kind": "move",
                                    "slot_index": 1,
                                    "move_id": 45,
                                    "move_name": "GROWL",
                                },
                                "source": {"rule_id": "move.score_rule"},
                            },
                            {
                                "event_type": "rule_enter",
                                "index": 3,
                                "candidate": {
                                    "kind": "unknown_score_pointer",
                                    "slot_index": -1,
                                    "move_id": 0,
                                },
                                "source": {"rule_id": "move.unknown_candidate"},
                            },
                        ],
                        "predicate_branch_entry_count": 0,
                        "predicate_branch_entries": [],
                        "public_read_probe_entry_count": 0,
                        "public_read_probe_entries": [],
                        "event_count": 1,
                        "changed_event_count": 1,
                        "events": [
                            {
                                "event_type": "score_delta",
                                "changed": True,
                                "delta": -2,
                                "candidate": {
                                    "kind": "move",
                                    "slot_index": 0,
                                    "move_id": 33,
                                    "move_name": "TACKLE",
                                },
                                "source": {"rule_id": "move.score_rule"},
                            }
                        ],
                        "known_limits": [],
                    }
                ),
                encoding="utf-8",
            )

            evidence = build_witness_evidence_from_contribution_summary(
                {
                    "artifacts": [
                        {
                            "artifact": str(trace),
                            "executed_rule_ids": [],
                        }
                    ]
                },
                root=root,
            )

        negative = evidence[("move.score_rule", "negative")][0]
        self.assertEqual(negative["evidence_kind"], "rom_rule_entry_without_score_delta")
        self.assertEqual(negative["status"], "negative_no_score_delta_observed")
        self.assertEqual(negative["candidate_move"], "GROWL")
        self.assertEqual(negative["candidate_move_id"], 45)
        self.assertEqual(negative["slot_index"], 1)
        self.assertEqual(negative["rule_entry_index"], 2)
        self.assertEqual(len(evidence[("move.score_rule", "negative")]), 1)
        self.assertNotIn(("move.unknown_candidate", "negative"), evidence)

    def test_boundary_witness_uses_score_delta_selector_margin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "rom_contribution_trace_unit.json"
            trace.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "trace_rom_pyboy_hooks",
                        "save_state": "route:unit",
                        "trace_basis": {},
                        "chosen": {"slot_index": 0, "move_id": 33, "move_name": "TACKLE"},
                        "move_ids": [33, 45, 52, 63],
                        "move_scores": [18, 19, 50, 60],
                        "pre_model_scores": [20, 20, 20, 20],
                        "post_model_scores": [18, 19, 50, 60],
                        "selector_entry_scores": [18, 19, 50, 60],
                        "rule_entry_count": 0,
                        "rule_entries": [],
                        "predicate_branch_entry_count": 0,
                        "predicate_branch_entries": [],
                        "public_read_probe_entry_count": 0,
                        "public_read_probe_entries": [],
                        "event_count": 2,
                        "changed_event_count": 2,
                        "events": [
                            {
                                "event_type": "score_delta",
                                "changed": True,
                                "score_before": 21,
                                "score_after": 18,
                                "delta": -3,
                                "candidate": {
                                    "kind": "move",
                                    "slot_index": 0,
                                    "move_id": 33,
                                    "move_name": "TACKLE",
                                },
                                "source": {
                                    "rule_id": "move.margin",
                                    "source_label": "BossAI_Margin",
                                    "parent_label": "BossAI_ApplyMoveModel",
                                },
                            },
                            {
                                "event_type": "score_delta",
                                "changed": True,
                                "score_before": 20,
                                "score_after": 19,
                                "delta": -1,
                                "candidate": {
                                    "kind": "move",
                                    "slot_index": 1,
                                    "move_id": 45,
                                    "move_name": "GROWL",
                                },
                                "source": {"rule_id": "move.not_decisive"},
                            },
                        ],
                        "known_limits": [],
                    }
                ),
                encoding="utf-8",
            )

            evidence = build_witness_evidence_from_contribution_summary(
                {
                    "artifacts": [
                        {
                            "artifact": str(trace),
                            "executed_rule_ids": [],
                        }
                    ]
                },
                root=root,
            )

        boundary = evidence[("move.margin", "boundary")][0]
        self.assertEqual(boundary["evidence_kind"], "rom_score_delta_selector_margin_boundary")
        self.assertEqual(boundary["status"], "score_margin_boundary_observed")
        self.assertEqual(boundary["candidate_move"], "TACKLE")
        self.assertEqual(boundary["slot_index"], 0)
        self.assertEqual(boundary["compared_slot_index"], 1)
        self.assertEqual(boundary["selector_score"], 18)
        self.assertEqual(boundary["compared_selector_score"], 19)
        self.assertEqual(boundary["observed_delta"], -3)
        self.assertEqual(boundary["score_without_rule"], 21)
        self.assertEqual(
            boundary["boundary_relation"],
            "best_candidate_would_reach_runner_up_score",
        )
        counterfactual = evidence[("move.margin", "counterfactual_flip")][0]
        self.assertEqual(
            counterfactual["evidence_kind"],
            "rom_score_delta_selector_margin_counterfactual",
        )
        self.assertEqual(
            counterfactual["status"],
            "score_margin_counterfactual_flip_observed",
        )
        self.assertEqual(counterfactual["candidate_move"], "TACKLE")
        self.assertEqual(counterfactual["slot_index"], 0)
        self.assertEqual(counterfactual["compared_slot_index"], 1)
        self.assertEqual(counterfactual["selector_score"], 18)
        self.assertEqual(counterfactual["compared_selector_score"], 19)
        self.assertEqual(counterfactual["observed_delta"], -3)
        self.assertEqual(counterfactual["score_without_rule"], 21)
        self.assertEqual(
            counterfactual["counterfactual_relation"],
            "best_candidate_would_lose_to_runner_up",
        )
        self.assertNotIn(("move.not_decisive", "boundary"), evidence)
        self.assertNotIn(("move.not_decisive", "counterfactual_flip"), evidence)

    def test_score_margin_counterfactual_requires_strict_selector_flip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "rom_contribution_trace_unit.json"
            trace.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "trace_rom_pyboy_hooks",
                        "save_state": "route:unit",
                        "trace_basis": {},
                        "chosen": {"slot_index": 0, "move_id": 33, "move_name": "TACKLE"},
                        "move_ids": [33, 45],
                        "move_scores": [18, 19],
                        "pre_model_scores": [20, 20],
                        "post_model_scores": [18, 19],
                        "selector_entry_scores": [18, 19],
                        "rule_entry_count": 0,
                        "rule_entries": [],
                        "predicate_branch_entry_count": 0,
                        "predicate_branch_entries": [],
                        "public_read_probe_entry_count": 0,
                        "public_read_probe_entries": [],
                        "event_count": 1,
                        "changed_event_count": 1,
                        "events": [
                            {
                                "event_type": "score_delta",
                                "changed": True,
                                "score_before": 19,
                                "score_after": 18,
                                "delta": -1,
                                "candidate": {
                                    "kind": "move",
                                    "slot_index": 0,
                                    "move_id": 33,
                                    "move_name": "TACKLE",
                                },
                                "source": {"rule_id": "move.margin_tie"},
                            }
                        ],
                        "known_limits": [],
                    }
                ),
                encoding="utf-8",
            )

            evidence = build_witness_evidence_from_contribution_summary(
                {
                    "artifacts": [
                        {
                            "artifact": str(trace),
                            "executed_rule_ids": [],
                        }
                    ]
                },
                root=root,
            )

        boundary = evidence[("move.margin_tie", "boundary")][0]
        self.assertEqual(boundary["score_without_rule"], 19)
        self.assertNotIn(("move.margin_tie", "counterfactual_flip"), evidence)

    def test_boundary_witness_score_delta_selector_margin_fails_closed(self) -> None:
        base_trace = {
            "schema_version": 1,
            "source": "trace_rom_pyboy_hooks",
            "save_state": "route:unit",
            "trace_basis": {},
            "chosen": {"slot_index": 0, "move_id": 33, "move_name": "TACKLE"},
            "move_ids": [33, 45],
            "move_scores": [18, 19],
            "pre_model_scores": [20, 20],
            "post_model_scores": [18, 19],
            "selector_entry_scores": [18, 19],
            "rule_entry_count": 0,
            "rule_entries": [],
            "predicate_branch_entry_count": 0,
            "predicate_branch_entries": [],
            "public_read_probe_entry_count": 0,
            "public_read_probe_entries": [],
            "event_count": 1,
            "changed_event_count": 1,
            "events": [
                {
                    "event_type": "score_delta",
                    "changed": True,
                    "score_before": 21,
                    "score_after": 18,
                    "delta": -3,
                    "candidate": {
                        "kind": "move",
                        "slot_index": 0,
                        "move_id": 33,
                        "move_name": "TACKLE",
                    },
                    "source": {"rule_id": "move.margin"},
                }
            ],
            "known_limits": [],
        }

        def mutated(mutator: Any) -> dict[str, object]:
            trace = json.loads(json.dumps(base_trace))
            mutator(trace)
            return trace

        weak_traces = [
            mutated(lambda trace: trace.__setitem__("source", "python_model")),
            mutated(lambda trace: trace.__setitem__("selector_entry_scores", [18])),
            mutated(lambda trace: trace.__setitem__("chosen", {"slot_index": 1})),
            mutated(lambda trace: trace.__setitem__("move_ids", [34, 45])),
            mutated(lambda trace: trace["events"][0].__setitem__("changed", False)),
            mutated(lambda trace: trace["events"][0].__setitem__("delta", -2)),
            mutated(lambda trace: trace["events"][0].__setitem__("source", {})),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifacts = []
            for index, trace_data in enumerate(weak_traces):
                trace = root / f"rom_contribution_trace_unit_{index}.json"
                trace.write_text(json.dumps(trace_data), encoding="utf-8")
                artifacts.append({"artifact": str(trace), "executed_rule_ids": []})

            evidence = build_witness_evidence_from_contribution_summary(
                {"artifacts": artifacts},
                root=root,
            )

        self.assertNotIn(("move.margin", "boundary"), evidence)

    def test_boundary_witness_requires_nonempty_snapshot_and_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "rom_contribution_trace_unit.json"
            trace.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "trace_rom_pyboy_hooks",
                        "save_state": "route:unit",
                        "trace_basis": {},
                        "chosen": {},
                        "move_ids": [],
                        "move_scores": [],
                        "pre_model_scores": [],
                        "post_model_scores": [],
                        "rule_entry_count": 1,
                        "rule_entries": [
                            {
                                "event_type": "rule_enter",
                                "source": {"rule_id": "move.public"},
                            }
                        ],
                        "predicate_branch_entry_count": 3,
                        "predicate_branch_entries": [
                            {
                                "event_type": "predicate_branch",
                                "predicate": {"predicate_id": "missing_snapshot", "outcome": "yes"},
                                "public_input_snapshot": {},
                                "source": {"rule_id": "move.public"},
                            },
                            {
                                "event_type": "predicate_branch",
                                "predicate": {"predicate_id": "missing_outcome"},
                                "public_input_snapshot": {"wPlayerScreens": {"values": [1]}},
                                "source": {"rule_id": "move.public"},
                            },
                            {
                                "event_type": "predicate_branch",
                                "predicate": {"predicate_id": "missing_rule", "outcome": "yes"},
                                "public_input_snapshot": {"wPlayerScreens": {"values": [1]}},
                                "source": {},
                            },
                        ],
                        "public_read_probe_entry_count": 0,
                        "public_read_probe_entries": [],
                        "event_count": 0,
                        "changed_event_count": 0,
                        "events": [],
                        "known_limits": [],
                    }
                ),
                encoding="utf-8",
            )

            evidence = build_witness_evidence_from_contribution_summary(
                {
                    "artifacts": [
                        {
                            "artifact": str(trace),
                            "executed_rule_ids": ["move.public"],
                        }
                    ]
                },
                root=root,
            )

        self.assertIn(("move.public", "positive"), evidence)
        self.assertNotIn(("move.public", "boundary"), evidence)
        self.assertNotIn(("move.public", "negative"), evidence)
        self.assertNotIn(("move.public", "counterfactual_flip"), evidence)

    def test_paired_rom_counterfactual_artifact_credits_switch_flip(self) -> None:
        identity = {
            "rom_sha256": "rom",
            "symbols_sha256": "symbols",
            "map_sha256": "map",
            "rule_map_sha256": "rules",
            "source_tree_sha256": "commit",
            "dirty_diff_hash": "diff",
        }
        report = {
            "schema_version": 1,
            "kind": "rom_counterfactual_witness_materialization",
            "proof_scope": "boss_ai.counterfactual_flip",
            "source": "generated_missing_witness_worklist",
            "generator": "tools.boss_ai_debugger.rom_counterfactual_materialize",
            "basis": dict(identity),
            "checked_count": 2,
            "skipped_count": 0,
            "error_count": 0,
            "policy_disagreement_count": 0,
            "witnesses": [
                {
                    "status": "pass",
                    "witness_role": "counterfactual_flip",
                    "rule_id": "switch.try_switch",
                    "decision_surface": "switch_dispatch",
                    "family": "switch_sack",
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "switch.try_switch",
                        "source_label": "BossAI_TrySwitch",
                        "parent_label": "BossAI_TrySwitch",
                    },
                    "mutation": {
                        "allowlist": "boss_ai_public_or_boss_owned_counterfactual_v1",
                        "changed_keys": ["wBossAISwitchConfidence"],
                    },
                    "baseline_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "baseline",
                        "executed_rule_ids": ["switch.try_switch"],
                        "switch_observation": {
                            "status": "actual_switch_observed",
                            "switch_confidence": 99,
                            "switch_param": 49,
                            "switch_index": 2,
                        },
                    },
                    "counterfactual_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "counterfactual",
                        "executed_rule_ids": ["switch.try_switch"],
                        "switch_observation": {
                            "status": "switch_proposal_observed",
                            "switch_confidence": 57,
                            "switch_param": 57,
                            "switch_index": 0,
                        },
                    },
                    "baseline_observable": {
                        "kind": "switch_dispatch",
                        "status": "actual_switch_observed",
                        "switch_confidence": 99,
                        "switch_param": 49,
                        "switch_index": 2,
                    },
                    "counterfactual_observable": {
                        "kind": "switch_dispatch",
                        "status": "switch_proposal_observed",
                        "switch_confidence": 57,
                        "switch_param": 57,
                        "switch_index": 0,
                    },
                }
            ],
        }

        evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}
        add_witness_evidence_from_counterfactual_materialization(
            evidence,
            report=report,
            artifact_path="counterfactuals/switch.json",
            rule_surfaces={"switch.try_switch": "switch_dispatch"},
            identity=identity,
        )

        counterfactual = evidence[("switch.try_switch", "counterfactual_flip")][0]
        self.assertEqual(counterfactual["evidence_kind"], "rom_paired_counterfactual_decision_flip")
        self.assertEqual(counterfactual["status"], "paired_counterfactual_flip_observed")
        self.assertEqual(counterfactual["mutation_key"], "wBossAISwitchConfidence")
        self.assertEqual(counterfactual["baseline_trace_id"], "baseline")
        self.assertEqual(counterfactual["counterfactual_trace_id"], "counterfactual")

    def test_paired_rom_counterfactual_artifact_credits_upstream_switch_helper_flip(self) -> None:
        identity = {
            "rom_sha256": "rom",
            "symbols_sha256": "symbols",
            "map_sha256": "map",
            "rule_map_sha256": "rules",
            "source_tree_sha256": "commit",
            "dirty_diff_hash": "diff",
        }
        report = {
            "schema_version": 1,
            "kind": "rom_counterfactual_witness_materialization",
            "proof_scope": "boss_ai.counterfactual_flip",
            "source": "generated_missing_witness_worklist",
            "generator": "tools.boss_ai_debugger.rom_counterfactual_materialize",
            "basis": dict(identity),
            "checked_count": 1,
            "skipped_count": 0,
            "error_count": 0,
            "policy_disagreement_count": 0,
            "witnesses": [
                {
                    "status": "pass",
                    "witness_role": "counterfactual_flip",
                    "rule_id": "switch.apply_role_package_switch_bias",
                    "decision_surface": "switch_dispatch",
                    "family": "switch_sack",
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "switch.apply_role_package_switch_bias",
                        "source_label": "BossAI_ApplyRolePackageSwitchBias",
                    },
                    "mutation": {
                        "allowlist": "boss_ai_public_or_boss_owned_counterfactual_v1",
                        "changed_keys": ["wBattleMonType1"],
                    },
                    "baseline_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "baseline",
                        "executed_rule_ids": ["switch.apply_role_package_switch_bias"],
                        "switch_observation": {
                            "status": "actual_switch_observed",
                            "switch_confidence": 99,
                            "switch_param": 49,
                            "switch_index": 2,
                        },
                    },
                    "counterfactual_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "counterfactual",
                        "executed_rule_ids": ["switch.apply_role_package_switch_bias"],
                        "switch_observation": {
                            "status": "no_switch_observation",
                            "switch_confidence": 0,
                            "switch_param": 0,
                            "switch_index": 0,
                        },
                    },
                    "baseline_observable": {
                        "kind": "switch_dispatch",
                        "status": "actual_switch_observed",
                        "switch_confidence": 99,
                        "switch_param": 49,
                        "switch_index": 2,
                    },
                    "counterfactual_observable": {
                        "kind": "switch_dispatch",
                        "status": "no_switch_observation",
                        "switch_confidence": 0,
                        "switch_param": 0,
                        "switch_index": 0,
                    },
                }
            ],
        }

        evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}
        add_witness_evidence_from_counterfactual_materialization(
            evidence,
            report=report,
            artifact_path="counterfactuals/switch-helper.json",
            rule_surfaces={"switch.apply_role_package_switch_bias": "switch_dispatch"},
            identity=identity,
        )

        counterfactual = evidence[
            ("switch.apply_role_package_switch_bias", "counterfactual_flip")
        ][0]
        self.assertEqual(
            counterfactual["evidence_kind"],
            "rom_paired_counterfactual_decision_flip",
        )
        self.assertEqual(counterfactual["mutation_key"], "wBattleMonType1")

    def test_paired_rom_counterfactual_credits_shared_switch_path_rule(self) -> None:
        identity = {
            "rom_sha256": "rom",
            "symbols_sha256": "symbols",
            "map_sha256": "map",
            "rule_map_sha256": "rules",
            "source_tree_sha256": "commit",
            "dirty_diff_hash": "diff",
        }
        report = {
            "schema_version": 1,
            "kind": "rom_counterfactual_witness_materialization",
            "proof_scope": "boss_ai.counterfactual_flip",
            "source": "generated_missing_witness_worklist",
            "generator": "tools.boss_ai_debugger.rom_counterfactual_materialize",
            "basis": dict(identity),
            "checked_count": 1,
            "skipped_count": 0,
            "error_count": 0,
            "policy_disagreement_count": 0,
            "witnesses": [
                {
                    "status": "pass",
                    "witness_role": "counterfactual_flip",
                    "rule_id": "move.get_tier_plausible_risk_weight",
                    "decision_surface": "boss_ai_rule",
                    "family": "mastery_policy",
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "move.get_tier_plausible_risk_weight",
                        "source_label": "BossAI_GetTierPlausibleRiskWeight",
                    },
                    "mutation": {
                        "allowlist": "boss_ai_public_or_boss_owned_counterfactual_v1",
                        "changed_keys": ["wBattleMonType1"],
                    },
                    "baseline_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "baseline",
                        "executed_rule_ids": ["move.get_tier_plausible_risk_weight"],
                        "switch_observation": {
                            "status": "actual_switch_observed",
                            "switch_confidence": 99,
                            "switch_param": 49,
                            "switch_index": 2,
                        },
                    },
                    "counterfactual_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "counterfactual",
                        "executed_rule_ids": ["move.get_tier_plausible_risk_weight"],
                        "switch_observation": {
                            "status": "no_switch_observation",
                            "switch_confidence": 0,
                            "switch_param": 0,
                            "switch_index": 0,
                        },
                    },
                    "baseline_observable": {
                        "kind": "switch_dispatch",
                        "status": "actual_switch_observed",
                        "switch_confidence": 99,
                        "switch_param": 49,
                        "switch_index": 2,
                    },
                    "counterfactual_observable": {
                        "kind": "switch_dispatch",
                        "status": "no_switch_observation",
                        "switch_confidence": 0,
                        "switch_param": 0,
                        "switch_index": 0,
                    },
                }
            ],
        }

        evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}
        add_witness_evidence_from_counterfactual_materialization(
            evidence,
            report=report,
            artifact_path="counterfactuals/shared-switch-path-rule.json",
            rule_surfaces={"move.get_tier_plausible_risk_weight": "boss_ai_rule"},
            identity=identity,
        )

        counterfactual = evidence[
            ("move.get_tier_plausible_risk_weight", "counterfactual_flip")
        ][0]
        self.assertEqual(
            counterfactual["evidence_kind"],
            "rom_paired_counterfactual_decision_flip",
        )
        self.assertEqual(counterfactual["mutation_key"], "wBattleMonType1")

    def test_paired_rom_counterfactual_rejects_switch_flip_for_regular_move_rule(self) -> None:
        identity = {
            "rom_sha256": "rom",
            "symbols_sha256": "symbols",
            "map_sha256": "map",
            "rule_map_sha256": "rules",
            "source_tree_sha256": "commit",
            "dirty_diff_hash": "diff",
        }
        report = {
            "schema_version": 1,
            "kind": "rom_counterfactual_witness_materialization",
            "proof_scope": "boss_ai.counterfactual_flip",
            "source": "generated_missing_witness_worklist",
            "generator": "tools.boss_ai_debugger.rom_counterfactual_materialize",
            "basis": dict(identity),
            "checked_count": 1,
            "skipped_count": 0,
            "error_count": 0,
            "policy_disagreement_count": 0,
            "witnesses": [
                {
                    "status": "pass",
                    "witness_role": "counterfactual_flip",
                    "rule_id": "move.hedge_matchup",
                    "decision_surface": "boss_ai_rule",
                    "family": "mastery_policy",
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "move.hedge_matchup",
                        "source_label": "BossAI_HedgeMatchup",
                    },
                    "mutation": {
                        "allowlist": "boss_ai_public_or_boss_owned_counterfactual_v1",
                        "changed_keys": ["wBattleMonType1"],
                    },
                    "baseline_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "baseline",
                        "executed_rule_ids": ["move.hedge_matchup"],
                        "switch_observation": {
                            "status": "actual_switch_observed",
                            "switch_confidence": 99,
                            "switch_param": 49,
                            "switch_index": 2,
                        },
                    },
                    "counterfactual_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "counterfactual",
                        "executed_rule_ids": ["move.hedge_matchup"],
                        "switch_observation": {
                            "status": "no_switch_observation",
                            "switch_confidence": 0,
                            "switch_param": 0,
                            "switch_index": 0,
                        },
                    },
                    "baseline_observable": {
                        "kind": "switch_dispatch",
                        "status": "actual_switch_observed",
                        "switch_confidence": 99,
                        "switch_param": 49,
                        "switch_index": 2,
                    },
                    "counterfactual_observable": {
                        "kind": "switch_dispatch",
                        "status": "no_switch_observation",
                        "switch_confidence": 0,
                        "switch_param": 0,
                        "switch_index": 0,
                    },
                }
            ],
        }

        evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}
        add_witness_evidence_from_counterfactual_materialization(
            evidence,
            report=report,
            artifact_path="counterfactuals/regular-move-rule-switch-flip.json",
            rule_surfaces={"move.hedge_matchup": "boss_ai_rule"},
            identity=identity,
        )

        self.assertNotIn(("move.hedge_matchup", "counterfactual_flip"), evidence)

    def test_paired_rom_counterfactual_credits_switch_bookkeeping_move_observable(self) -> None:
        identity = {
            "rom_sha256": "rom",
            "symbols_sha256": "symbols",
            "map_sha256": "map",
            "rule_map_sha256": "rules",
            "source_tree_sha256": "commit",
            "dirty_diff_hash": "diff",
        }
        report = {
            "schema_version": 1,
            "kind": "rom_counterfactual_witness_materialization",
            "proof_scope": "boss_ai.counterfactual_flip",
            "source": "generated_missing_witness_worklist",
            "generator": "tools.boss_ai_debugger.rom_counterfactual_materialize",
            "basis": dict(identity),
            "checked_count": 2,
            "skipped_count": 0,
            "error_count": 0,
            "policy_disagreement_count": 0,
            "witnesses": [
                {
                    "status": "pass",
                    "witness_role": "counterfactual_flip",
                    "rule_id": "switch.decay_switch_cooldown",
                    "decision_surface": "switch_dispatch",
                    "family": "switch_sack",
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "switch.decay_switch_cooldown",
                        "source_label": "BossAI_DecaySwitchCooldown",
                    },
                    "mutation": {
                        "allowlist": "boss_ai_public_or_boss_owned_counterfactual_v1",
                        "changed_keys": ["wBattleMonType1"],
                    },
                    "baseline_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "baseline",
                        "executed_rule_ids": ["switch.decay_switch_cooldown"],
                        "chosen": {"move_id": 92, "slot_index": 2},
                    },
                    "counterfactual_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "counterfactual",
                        "executed_rule_ids": ["switch.decay_switch_cooldown"],
                        "chosen": {"move_id": 191, "slot_index": 0},
                    },
                    "baseline_observable": {
                        "kind": "move_choice",
                        "move_id": 92,
                        "slot_index": 2,
                    },
                    "counterfactual_observable": {
                        "kind": "move_choice",
                        "move_id": 191,
                        "slot_index": 0,
                    },
                },
                {
                    "status": "pass",
                    "witness_role": "counterfactual_flip",
                    "rule_id": "switch.commit_haki_oracle_choice",
                    "decision_surface": "switch_dispatch",
                    "family": "switch_sack",
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "switch.commit_haki_oracle_choice",
                        "source_label": "BossAI_CommitHakiOracleChoice",
                    },
                    "mutation": {
                        "allowlist": "boss_ai_public_or_boss_owned_counterfactual_v1",
                        "changed_keys": ["wBattleMonType1"],
                    },
                    "baseline_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "haki-baseline",
                        "executed_rule_ids": ["switch.commit_haki_oracle_choice"],
                        "chosen": {"move_id": 188, "slot_index": 1},
                    },
                    "counterfactual_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "haki-counterfactual",
                        "executed_rule_ids": ["switch.commit_haki_oracle_choice"],
                        "chosen": {"move_id": 174, "slot_index": 0},
                    },
                    "baseline_observable": {
                        "kind": "move_choice",
                        "move_id": 188,
                        "slot_index": 1,
                    },
                    "counterfactual_observable": {
                        "kind": "move_choice",
                        "move_id": 174,
                        "slot_index": 0,
                    },
                },
            ],
        }

        evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}
        add_witness_evidence_from_counterfactual_materialization(
            evidence,
            report=report,
            artifact_path="counterfactuals/switch-bookkeeping-move.json",
            rule_surfaces={
                "switch.commit_haki_oracle_choice": "switch_dispatch",
                "switch.decay_switch_cooldown": "switch_dispatch",
            },
            identity=identity,
        )

        self.assertIn(("switch.decay_switch_cooldown", "counterfactual_flip"), evidence)
        self.assertIn(("switch.commit_haki_oracle_choice", "counterfactual_flip"), evidence)

    def test_paired_rom_counterfactual_rejects_move_observable_for_regular_switch_rule(self) -> None:
        identity = {
            "rom_sha256": "rom",
            "symbols_sha256": "symbols",
            "map_sha256": "map",
            "rule_map_sha256": "rules",
            "source_tree_sha256": "commit",
            "dirty_diff_hash": "diff",
        }
        report = {
            "schema_version": 1,
            "kind": "rom_counterfactual_witness_materialization",
            "proof_scope": "boss_ai.counterfactual_flip",
            "source": "generated_missing_witness_worklist",
            "generator": "tools.boss_ai_debugger.rom_counterfactual_materialize",
            "basis": dict(identity),
            "checked_count": 1,
            "skipped_count": 0,
            "error_count": 0,
            "policy_disagreement_count": 0,
            "witnesses": [
                {
                    "status": "pass",
                    "witness_role": "counterfactual_flip",
                    "rule_id": "switch.try_switch",
                    "decision_surface": "switch_dispatch",
                    "family": "switch_sack",
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "switch.try_switch",
                        "source_label": "BossAI_TrySwitch",
                    },
                    "mutation": {
                        "allowlist": "boss_ai_public_or_boss_owned_counterfactual_v1",
                        "changed_keys": ["wBattleMonType1"],
                    },
                    "baseline_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "baseline",
                        "executed_rule_ids": ["switch.try_switch"],
                        "chosen": {"move_id": 92, "slot_index": 2},
                    },
                    "counterfactual_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "counterfactual",
                        "executed_rule_ids": ["switch.try_switch"],
                        "chosen": {"move_id": 191, "slot_index": 0},
                    },
                    "baseline_observable": {
                        "kind": "move_choice",
                        "move_id": 92,
                        "slot_index": 2,
                    },
                    "counterfactual_observable": {
                        "kind": "move_choice",
                        "move_id": 191,
                        "slot_index": 0,
                    },
                }
            ],
        }

        evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}
        add_witness_evidence_from_counterfactual_materialization(
            evidence,
            report=report,
            artifact_path="counterfactuals/regular-switch-move.json",
            rule_surfaces={"switch.try_switch": "switch_dispatch"},
            identity=identity,
        )

        self.assertNotIn(("switch.try_switch", "counterfactual_flip"), evidence)

    def test_paired_rom_counterfactual_credits_adaptive_trainer_identity_flip(self) -> None:
        identity = {
            "rom_sha256": "rom",
            "symbols_sha256": "symbols",
            "map_sha256": "map",
            "rule_map_sha256": "rules",
            "source_tree_sha256": "commit",
            "dirty_diff_hash": "diff",
        }
        report = {
            "schema_version": 1,
            "kind": "rom_counterfactual_witness_materialization",
            "proof_scope": "boss_ai.counterfactual_flip",
            "source": "generated_missing_witness_worklist",
            "generator": "tools.boss_ai_debugger.rom_counterfactual_materialize",
            "basis": dict(identity),
            "checked_count": 1,
            "skipped_count": 0,
            "error_count": 0,
            "policy_disagreement_count": 0,
            "witnesses": [
                {
                    "status": "pass",
                    "witness_role": "counterfactual_flip",
                    "rule_id": "move.maybe_pick_adaptive_enemy_lead.should_use_adaptive_lead_for_trainer",
                    "decision_surface": "boss_ai_rule",
                    "family": "mastery_policy",
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "move.maybe_pick_adaptive_enemy_lead.should_use_adaptive_lead_for_trainer",
                        "source_label": ".ShouldUseAdaptiveLeadForTrainer",
                    },
                    "mutation": {
                        "allowlist": "boss_ai_public_or_boss_owned_counterfactual_v1",
                        "changed_keys": ["wOtherTrainerClass"],
                    },
                    "baseline_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "baseline",
                        "executed_rule_ids": [
                            "move.maybe_pick_adaptive_enemy_lead.should_use_adaptive_lead_for_trainer"
                        ],
                        "chosen": {"move_id": 92, "slot_index": 2},
                        "predicate_branch_entries": [
                            {
                                "source": {
                                    "rule_id": "move.maybe_pick_adaptive_enemy_lead.should_use_adaptive_lead_for_trainer"
                                },
                                "predicate": {
                                    "predicate_id": "adaptive_lead_trainer_match",
                                    "outcome": "enabled",
                                },
                            }
                        ],
                    },
                    "counterfactual_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "counterfactual",
                        "executed_rule_ids": [
                            "move.maybe_pick_adaptive_enemy_lead.should_use_adaptive_lead_for_trainer"
                        ],
                        "chosen": {"move_id": 104, "slot_index": 2},
                        "predicate_branch_entries": [
                            {
                                "source": {
                                    "rule_id": "move.maybe_pick_adaptive_enemy_lead.should_use_adaptive_lead_for_trainer"
                                },
                                "predicate": {
                                    "predicate_id": "adaptive_lead_trainer_match",
                                    "outcome": "disabled",
                                },
                            }
                        ],
                    },
                    "baseline_observable": {
                        "kind": "move_choice",
                        "move_id": 92,
                        "slot_index": 2,
                    },
                    "counterfactual_observable": {
                        "kind": "move_choice",
                        "move_id": 104,
                        "slot_index": 2,
                    },
                }
            ],
        }

        evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}
        add_witness_evidence_from_counterfactual_materialization(
            evidence,
            report=report,
            artifact_path="counterfactuals/adaptive-trainer.json",
            rule_surfaces={
                "move.maybe_pick_adaptive_enemy_lead.should_use_adaptive_lead_for_trainer": "boss_ai_rule"
            },
            identity=identity,
        )

        self.assertIn(
            (
                "move.maybe_pick_adaptive_enemy_lead.should_use_adaptive_lead_for_trainer",
                "counterfactual_flip",
            ),
            evidence,
        )

    def test_paired_rom_counterfactual_move_choice_credits_targeted_rules_without_branch_metadata(self) -> None:
        identity = {
            "rom_sha256": "rom",
            "symbols_sha256": "symbols",
            "map_sha256": "map",
            "rule_map_sha256": "rules",
            "source_tree_sha256": "commit",
            "dirty_diff_hash": "diff",
        }
        base_witness = {
            "status": "pass",
            "witness_role": "counterfactual_flip",
            "mutation": {
                "allowlist": "boss_ai_public_or_boss_owned_counterfactual_v1",
                "changed_keys": ["wBattleMonType1"],
            },
            "baseline_trace": {
                "source": "trace_rom_pyboy_hooks",
                "trace_id": "baseline",
                "executed_rule_ids": [
                    "move.apply_move_model.apply_setup_discipline_bias",
                    "move.hedge_matchup",
                ],
                "chosen": {"move_id": 89, "slot_index": 0},
            },
            "counterfactual_trace": {
                "source": "trace_rom_pyboy_hooks",
                "trace_id": "counterfactual",
                "executed_rule_ids": [
                    "move.apply_move_model.apply_setup_discipline_bias",
                    "move.hedge_matchup",
                ],
                "chosen": {"move_id": 126, "slot_index": 2},
            },
            "baseline_observable": {
                "kind": "move_choice",
                "move_id": 89,
                "slot_index": 0,
            },
            "counterfactual_observable": {
                "kind": "move_choice",
                "move_id": 126,
                "slot_index": 2,
            },
        }
        report = {
            "schema_version": 1,
            "kind": "rom_counterfactual_witness_materialization",
            "proof_scope": "boss_ai.counterfactual_flip",
            "source": "generated_missing_witness_worklist",
            "generator": "tools.boss_ai_debugger.rom_counterfactual_materialize",
            "basis": dict(identity),
            "checked_count": 2,
            "skipped_count": 0,
            "error_count": 0,
            "policy_disagreement_count": 0,
            "witnesses": [
                {
                    **base_witness,
                    "rule_id": "move.apply_move_model.apply_setup_discipline_bias",
                    "decision_surface": "move_score",
                    "family": "setup_heal",
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "move.apply_move_model.apply_setup_discipline_bias",
                        "source_label": ".ApplySetupDisciplineBias",
                    },
                },
                {
                    **base_witness,
                    "rule_id": "move.hedge_matchup",
                    "decision_surface": "boss_ai_rule",
                    "family": "mastery_policy",
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "move.hedge_matchup",
                        "source_label": "BossAI_HedgeMatchup",
                    },
                },
            ],
        }

        evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}
        add_witness_evidence_from_counterfactual_materialization(
            evidence,
            report=report,
            artifact_path="counterfactuals/move-choice.json",
            rule_surfaces={
                "move.apply_move_model.apply_setup_discipline_bias": "move_score",
                "move.hedge_matchup": "boss_ai_rule",
            },
            identity=identity,
        )

        score_counterfactual = evidence[
            ("move.apply_move_model.apply_setup_discipline_bias", "counterfactual_flip")
        ][0]
        self.assertEqual(
            score_counterfactual["evidence_kind"],
            "rom_paired_counterfactual_decision_flip",
        )
        rule_counterfactual = evidence[("move.hedge_matchup", "counterfactual_flip")][0]
        self.assertEqual(
            rule_counterfactual["evidence_kind"],
            "rom_paired_counterfactual_decision_flip",
        )

    def test_paired_rom_counterfactual_credits_rule_branch_outcome_flip(self) -> None:
        identity = {
            "rom_sha256": "rom",
            "symbols_sha256": "symbols",
            "map_sha256": "map",
            "rule_map_sha256": "rules",
            "source_tree_sha256": "commit",
            "dirty_diff_hash": "diff",
        }
        report = {
            "schema_version": 1,
            "kind": "rom_counterfactual_witness_materialization",
            "proof_scope": "boss_ai.counterfactual_flip",
            "source": "generated_missing_witness_worklist",
            "generator": "tools.boss_ai_debugger.rom_counterfactual_materialize",
            "basis": dict(identity),
            "checked_count": 1,
            "skipped_count": 0,
            "error_count": 0,
            "policy_disagreement_count": 0,
            "witnesses": [
                {
                    "status": "pass",
                    "witness_role": "counterfactual_flip",
                    "rule_id": "move.public_enemy_faster_uncached",
                    "decision_surface": "boss_ai_rule",
                    "family": "mastery_policy",
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "move.public_enemy_faster_uncached",
                        "source_label": "BossAI_PublicEnemyFaster_Uncached",
                    },
                    "mutation": {
                        "allowlist": "boss_ai_public_or_boss_owned_counterfactual_v1",
                        "changed_keys": ["wBattleMonType1"],
                    },
                    "baseline_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "baseline",
                        "executed_rule_ids": ["move.public_enemy_faster_uncached"],
                        "chosen": {"move_id": 89, "slot_index": 0},
                        "predicate_branch_entries": [
                            {
                                "source": {"rule_id": "move.public_enemy_faster_uncached"},
                                "predicate": {
                                    "predicate_id": "public_enemy_faster_uncached",
                                    "outcome": "enemy_faster",
                                },
                                "public_input_snapshot": {"wEnemyMonSpeed": {"value": 50}},
                            }
                        ],
                    },
                    "counterfactual_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "counterfactual",
                        "executed_rule_ids": ["move.public_enemy_faster_uncached"],
                        "chosen": {"move_id": 126, "slot_index": 2},
                        "predicate_branch_entries": [
                            {
                                "source": {"rule_id": "move.public_enemy_faster_uncached"},
                                "predicate": {
                                    "predicate_id": "public_enemy_faster_uncached",
                                    "outcome": "not_enemy_faster",
                                },
                                "public_input_snapshot": {"wEnemyMonSpeed": {"value": 40}},
                            }
                        ],
                    },
                    "baseline_observable": {
                        "kind": "move_choice",
                        "move_id": 89,
                        "slot_index": 0,
                    },
                    "counterfactual_observable": {
                        "kind": "move_choice",
                        "move_id": 126,
                        "slot_index": 2,
                    },
                },
                {
                    "status": "pass",
                    "witness_role": "counterfactual_flip",
                    "rule_id": "move.apply_move_model.enemy_can_be_poisoned_by_retaliation",
                    "decision_surface": "move_score",
                    "family": "setup_heal",
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "move.apply_move_model.enemy_can_be_poisoned_by_retaliation",
                        "source_label": ".EnemyCanBePoisonedByRetaliation",
                    },
                    "mutation": {
                        "allowlist": "boss_ai_public_or_boss_owned_counterfactual_v1",
                        "changed_keys": ["wBattleMonType1"],
                    },
                    "baseline_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "baseline",
                        "executed_rule_ids": [
                            "move.apply_move_model.enemy_can_be_poisoned_by_retaliation"
                        ],
                        "chosen": {"move_id": 89, "slot_index": 0},
                        "predicate_branch_entries": [
                            {
                                "source": {
                                    "rule_id": "move.apply_move_model.enemy_can_be_poisoned_by_retaliation"
                                },
                                "predicate": {
                                    "predicate_id": "enemy_poison_retaliation_vulnerability",
                                    "outcome": "vulnerable",
                                },
                            }
                        ],
                    },
                    "counterfactual_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "counterfactual",
                        "executed_rule_ids": [
                            "move.apply_move_model.enemy_can_be_poisoned_by_retaliation"
                        ],
                        "chosen": {"move_id": 126, "slot_index": 2},
                        "predicate_branch_entries": [
                            {
                                "source": {
                                    "rule_id": "move.apply_move_model.enemy_can_be_poisoned_by_retaliation"
                                },
                                "predicate": {
                                    "predicate_id": "enemy_poison_retaliation_vulnerability",
                                    "outcome": "not_vulnerable",
                                },
                            }
                        ],
                    },
                    "baseline_observable": {
                        "kind": "move_choice",
                        "move_id": 89,
                        "slot_index": 0,
                    },
                    "counterfactual_observable": {
                        "kind": "move_choice",
                        "move_id": 126,
                        "slot_index": 2,
                    },
                },
            ],
        }

        evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}
        add_witness_evidence_from_counterfactual_materialization(
            evidence,
            report=report,
            artifact_path="counterfactuals/branch.json",
            rule_surfaces={
                "move.public_enemy_faster_uncached": "boss_ai_rule",
                "move.apply_move_model.enemy_can_be_poisoned_by_retaliation": "move_score",
            },
            identity=identity,
        )

        counterfactual = evidence[
            ("move.public_enemy_faster_uncached", "counterfactual_flip")
        ][0]
        self.assertEqual(
            counterfactual["evidence_kind"],
            "rom_paired_counterfactual_predicate_branch_flip",
        )
        self.assertEqual(counterfactual["status"], "paired_counterfactual_branch_flip_observed")
        move_counterfactual = evidence[
            (
                "move.apply_move_model.enemy_can_be_poisoned_by_retaliation",
                "counterfactual_flip",
            )
        ][0]
        self.assertEqual(
            move_counterfactual["evidence_kind"],
            "rom_paired_counterfactual_predicate_branch_flip",
        )

    def test_paired_rom_counterfactual_credits_rule_branch_application_flip(self) -> None:
        identity = {
            "rom_sha256": "rom",
            "symbols_sha256": "symbols",
            "map_sha256": "map",
            "rule_map_sha256": "rules",
            "source_tree_sha256": "commit",
            "dirty_diff_hash": "diff",
        }
        report = {
            "schema_version": 1,
            "kind": "rom_counterfactual_witness_materialization",
            "proof_scope": "boss_ai.counterfactual_flip",
            "source": "generated_missing_witness_worklist",
            "generator": "tools.boss_ai_debugger.rom_counterfactual_materialize",
            "basis": dict(identity),
            "checked_count": 1,
            "skipped_count": 0,
            "error_count": 0,
            "policy_disagreement_count": 0,
            "witnesses": [
                {
                    "status": "pass",
                    "witness_role": "counterfactual_flip",
                    "rule_id": "move.apply_move_model.apply_charge_move_bias",
                    "decision_surface": "move_score",
                    "family": "mastery_policy",
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "move.apply_move_model.apply_charge_move_bias",
                        "source_label": ".ApplyChargeMoveBias",
                    },
                    "mutation": {
                        "allowlist": "boss_ai_public_or_boss_owned_counterfactual_v1",
                        "changed_keys": ["wBattleMonType1"],
                    },
                    "baseline_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "baseline",
                        "executed_rule_ids": [
                            "move.apply_move_model.apply_charge_move_bias"
                        ],
                        "chosen": {"move_id": 34, "slot_index": 1},
                        "predicate_branch_entries": [
                            {
                                "source": {
                                    "rule_id": "move.apply_move_model.apply_charge_move_bias"
                                },
                                "candidate": {
                                    "kind": "move",
                                    "move_id": 34,
                                    "slot_index": 1,
                                },
                                "predicate": {
                                    "predicate_id": "charge_move_bias",
                                    "outcome": "entered",
                                },
                            }
                        ],
                    },
                    "counterfactual_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "counterfactual",
                        "executed_rule_ids": [
                            "move.apply_move_model.apply_charge_move_bias"
                        ],
                        "chosen": {"move_id": 126, "slot_index": 2},
                        "predicate_branch_entries": [
                            {
                                "source": {
                                    "rule_id": "move.apply_move_model.apply_charge_move_bias"
                                },
                                "candidate": {
                                    "kind": "move",
                                    "move_id": 126,
                                    "slot_index": 2,
                                },
                                "predicate": {
                                    "predicate_id": "charge_move_bias",
                                    "outcome": "entered",
                                },
                            }
                        ],
                    },
                    "baseline_observable": {
                        "kind": "move_choice",
                        "move_id": 34,
                        "slot_index": 1,
                    },
                    "counterfactual_observable": {
                        "kind": "move_choice",
                        "move_id": 126,
                        "slot_index": 2,
                    },
                }
            ],
        }

        evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}
        add_witness_evidence_from_counterfactual_materialization(
            evidence,
            report=report,
            artifact_path="counterfactuals/application.json",
            rule_surfaces={
                "move.apply_move_model.apply_charge_move_bias": "move_score"
            },
            identity=identity,
        )

        counterfactual = evidence[
            ("move.apply_move_model.apply_charge_move_bias", "counterfactual_flip")
        ][0]
        self.assertEqual(
            counterfactual["evidence_kind"],
            "rom_paired_counterfactual_predicate_application_flip",
        )
        self.assertEqual(
            counterfactual["status"],
            "paired_counterfactual_branch_application_flip_observed",
        )

    def test_paired_rom_counterfactual_entry_marker_falls_back_to_decision_flip(self) -> None:
        identity = {
            "rom_sha256": "rom",
            "symbols_sha256": "symbols",
            "map_sha256": "map",
            "rule_map_sha256": "rules",
            "source_tree_sha256": "commit",
            "dirty_diff_hash": "diff",
        }
        report = {
            "schema_version": 1,
            "kind": "rom_counterfactual_witness_materialization",
            "proof_scope": "boss_ai.counterfactual_flip",
            "source": "generated_missing_witness_worklist",
            "generator": "tools.boss_ai_debugger.rom_counterfactual_materialize",
            "basis": dict(identity),
            "checked_count": 1,
            "skipped_count": 0,
            "error_count": 0,
            "policy_disagreement_count": 0,
            "witnesses": [
                {
                    "status": "pass",
                    "witness_role": "counterfactual_flip",
                    "rule_id": "move.apply_move_model.player_has_revealed_anti_setup",
                    "decision_surface": "move_score",
                    "family": "setup_heal",
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "move.apply_move_model.player_has_revealed_anti_setup",
                        "source_label": ".PlayerHasRevealedAntiSetup",
                    },
                    "mutation": {
                        "allowlist": "boss_ai_public_or_boss_owned_counterfactual_v1",
                        "changed_keys": ["wBattleMonType1"],
                    },
                    "baseline_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "baseline",
                        "executed_rule_ids": [
                            "move.apply_move_model.player_has_revealed_anti_setup"
                        ],
                        "chosen": {"move_id": 34, "slot_index": 1},
                        "predicate_branch_entries": [
                            {
                                "source": {
                                    "rule_id": "move.apply_move_model.player_has_revealed_anti_setup"
                                },
                                "candidate": {
                                    "kind": "move",
                                    "move_id": 174,
                                    "slot_index": 0,
                                },
                                "predicate": {
                                    "predicate_id": "revealed_anti_setup_scan",
                                    "outcome": "entered",
                                },
                            }
                        ],
                    },
                    "counterfactual_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "counterfactual",
                        "executed_rule_ids": [
                            "move.apply_move_model.player_has_revealed_anti_setup"
                        ],
                        "chosen": {"move_id": 174, "slot_index": 0},
                        "predicate_branch_entries": [
                            {
                                "source": {
                                    "rule_id": "move.apply_move_model.player_has_revealed_anti_setup"
                                },
                                "candidate": {
                                    "kind": "move",
                                    "move_id": 174,
                                    "slot_index": 0,
                                },
                                "predicate": {
                                    "predicate_id": "revealed_anti_setup_scan",
                                    "outcome": "entered",
                                },
                            }
                        ],
                    },
                    "baseline_observable": {
                        "kind": "move_choice",
                        "move_id": 34,
                        "slot_index": 1,
                    },
                    "counterfactual_observable": {
                        "kind": "move_choice",
                        "move_id": 174,
                        "slot_index": 0,
                    },
                }
            ],
        }

        evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}
        add_witness_evidence_from_counterfactual_materialization(
            evidence,
            report=report,
            artifact_path="counterfactuals/entry-marker.json",
            rule_surfaces={
                "move.apply_move_model.player_has_revealed_anti_setup": "move_score"
            },
            identity=identity,
        )

        counterfactual = evidence[
            ("move.apply_move_model.player_has_revealed_anti_setup", "counterfactual_flip")
        ][0]
        self.assertEqual(
            counterfactual["evidence_kind"],
            "rom_paired_counterfactual_decision_flip",
        )

    def test_paired_rom_counterfactual_branch_flip_can_keep_same_final_move(self) -> None:
        identity = {
            "rom_sha256": "rom",
            "symbols_sha256": "symbols",
            "map_sha256": "map",
            "rule_map_sha256": "rules",
            "source_tree_sha256": "commit",
            "dirty_diff_hash": "diff",
        }
        report = {
            "schema_version": 1,
            "kind": "rom_counterfactual_witness_materialization",
            "proof_scope": "boss_ai.counterfactual_flip",
            "source": "generated_missing_witness_worklist",
            "generator": "tools.boss_ai_debugger.rom_counterfactual_materialize",
            "basis": dict(identity),
            "checked_count": 1,
            "skipped_count": 0,
            "error_count": 0,
            "policy_disagreement_count": 0,
            "witnesses": [
                {
                    "status": "pass",
                    "witness_role": "counterfactual_flip",
                    "rule_id": "move.apply_move_model.player_cant_act_this_turn_publicly",
                    "decision_surface": "move_score",
                    "family": "mastery_policy",
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "move.apply_move_model.player_cant_act_this_turn_publicly",
                        "source_label": ".PlayerCantActThisTurnPublicly",
                    },
                    "mutation": {
                        "allowlist": "boss_ai_public_or_boss_owned_counterfactual_v1",
                        "changed_keys": ["wBattleMonStatus"],
                    },
                    "baseline_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "baseline",
                        "executed_rule_ids": [
                            "move.apply_move_model.player_cant_act_this_turn_publicly"
                        ],
                        "chosen": {"move_id": 57, "slot_index": 2},
                        "predicate_branch_entries": [
                            {
                                "source": {
                                    "rule_id": "move.apply_move_model.player_cant_act_this_turn_publicly"
                                },
                                "predicate": {
                                    "predicate_id": "player_can_act_status_gate",
                                    "outcome": "not_status_prevents_action",
                                },
                            }
                        ],
                    },
                    "counterfactual_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "counterfactual",
                        "executed_rule_ids": [
                            "move.apply_move_model.player_cant_act_this_turn_publicly"
                        ],
                        "chosen": {"move_id": 57, "slot_index": 2},
                        "predicate_branch_entries": [
                            {
                                "source": {
                                    "rule_id": "move.apply_move_model.player_cant_act_this_turn_publicly"
                                },
                                "predicate": {
                                    "predicate_id": "player_can_act_status_gate",
                                    "outcome": "status_prevents_action",
                                },
                            }
                        ],
                    },
                    "baseline_observable": {
                        "kind": "move_choice",
                        "move_id": 57,
                        "slot_index": 2,
                    },
                    "counterfactual_observable": {
                        "kind": "move_choice",
                        "move_id": 57,
                        "slot_index": 2,
                    },
                }
            ],
        }

        evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}
        add_witness_evidence_from_counterfactual_materialization(
            evidence,
            report=report,
            artifact_path="counterfactuals/same-final-move-branch.json",
            rule_surfaces={
                "move.apply_move_model.player_cant_act_this_turn_publicly": "move_score"
            },
            identity=identity,
        )

        counterfactual = evidence[
            ("move.apply_move_model.player_cant_act_this_turn_publicly", "counterfactual_flip")
        ][0]
        self.assertEqual(
            counterfactual["evidence_kind"],
            "rom_paired_counterfactual_predicate_branch_flip",
        )

    def test_paired_rom_counterfactual_branch_flip_rejects_snapshot_only_change(self) -> None:
        identity = {
            "rom_sha256": "rom",
            "symbols_sha256": "symbols",
            "map_sha256": "map",
            "rule_map_sha256": "rules",
            "source_tree_sha256": "commit",
            "dirty_diff_hash": "diff",
        }
        report = {
            "schema_version": 1,
            "kind": "rom_counterfactual_witness_materialization",
            "proof_scope": "boss_ai.counterfactual_flip",
            "source": "generated_missing_witness_worklist",
            "generator": "tools.boss_ai_debugger.rom_counterfactual_materialize",
            "basis": dict(identity),
            "checked_count": 1,
            "skipped_count": 0,
            "error_count": 0,
            "policy_disagreement_count": 0,
            "witnesses": [
                {
                    "status": "pass",
                    "witness_role": "counterfactual_flip",
                    "rule_id": "move.public_enemy_faster_uncached",
                    "decision_surface": "boss_ai_rule",
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "move.public_enemy_faster_uncached",
                        "source_label": "BossAI_PublicEnemyFaster_Uncached",
                    },
                    "mutation": {
                        "allowlist": "boss_ai_public_or_boss_owned_counterfactual_v1",
                        "changed_keys": ["wBattleMonType1"],
                    },
                    "baseline_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "baseline",
                        "executed_rule_ids": ["move.public_enemy_faster_uncached"],
                        "chosen": {"move_id": 89, "slot_index": 0},
                        "predicate_branch_entries": [
                            {
                                "source": {"rule_id": "move.public_enemy_faster_uncached"},
                                "predicate": {
                                    "predicate_id": "public_enemy_faster_uncached",
                                    "outcome": "enemy_faster",
                                },
                                "public_input_snapshot": {"wEnemyMonSpeed": {"value": 50}},
                            }
                        ],
                    },
                    "counterfactual_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "counterfactual",
                        "executed_rule_ids": ["move.public_enemy_faster_uncached"],
                        "chosen": {"move_id": 126, "slot_index": 2},
                        "predicate_branch_entries": [
                            {
                                "source": {"rule_id": "move.public_enemy_faster_uncached"},
                                "predicate": {
                                    "predicate_id": "public_enemy_faster_uncached",
                                    "outcome": "enemy_faster",
                                },
                                "public_input_snapshot": {"wEnemyMonSpeed": {"value": 40}},
                            }
                        ],
                    },
                    "baseline_observable": {
                        "kind": "move_choice",
                        "move_id": 89,
                        "slot_index": 0,
                    },
                    "counterfactual_observable": {
                        "kind": "move_choice",
                        "move_id": 126,
                        "slot_index": 2,
                    },
                }
            ],
        }

        evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}
        add_witness_evidence_from_counterfactual_materialization(
            evidence,
            report=report,
            artifact_path="counterfactuals/snapshot-only.json",
            rule_surfaces={"move.public_enemy_faster_uncached": "boss_ai_rule"},
            identity=identity,
        )

        self.assertNotIn(("move.public_enemy_faster_uncached", "counterfactual_flip"), evidence)

    def test_paired_rom_counterfactual_artifact_fails_closed_on_weak_reports(self) -> None:
        identity = {
            "rom_sha256": "rom",
            "symbols_sha256": "symbols",
            "map_sha256": "map",
            "rule_map_sha256": "rules",
            "source_tree_sha256": "commit",
            "dirty_diff_hash": "diff",
        }
        base_report = {
            "schema_version": 1,
            "kind": "rom_counterfactual_witness_materialization",
            "proof_scope": "boss_ai.counterfactual_flip",
            "source": "generated_missing_witness_worklist",
            "generator": "tools.boss_ai_debugger.rom_counterfactual_materialize",
            "basis": dict(identity),
            "checked_count": 1,
            "skipped_count": 0,
            "error_count": 0,
            "policy_disagreement_count": 0,
            "witnesses": [
                {
                    "status": "pass",
                    "witness_role": "counterfactual_flip",
                    "rule_id": "switch.try_switch",
                    "decision_surface": "switch_dispatch",
                    "source_anchor": {
                        "anchor_status": "mapped",
                        "rule_id": "switch.try_switch",
                        "source_label": "BossAI_TrySwitch",
                    },
                    "mutation": {
                        "allowlist": "boss_ai_public_or_boss_owned_counterfactual_v1",
                        "changed_keys": ["wBossAISwitchConfidence"],
                    },
                    "baseline_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "baseline",
                        "executed_rule_ids": ["switch.try_switch"],
                        "switch_observation": {
                            "status": "actual_switch_observed",
                            "switch_confidence": 99,
                            "switch_param": 49,
                            "switch_index": 2,
                        },
                    },
                    "counterfactual_trace": {
                        "source": "trace_rom_pyboy_hooks",
                        "trace_id": "counterfactual",
                        "executed_rule_ids": ["switch.try_switch"],
                        "switch_observation": {
                            "status": "switch_proposal_observed",
                            "switch_confidence": 57,
                            "switch_param": 57,
                            "switch_index": 0,
                        },
                    },
                    "baseline_observable": {
                        "kind": "switch_dispatch",
                        "status": "actual_switch_observed",
                        "switch_confidence": 99,
                        "switch_param": 49,
                        "switch_index": 2,
                    },
                    "counterfactual_observable": {
                        "kind": "switch_dispatch",
                        "status": "switch_proposal_observed",
                        "switch_confidence": 57,
                        "switch_param": 57,
                        "switch_index": 0,
                    },
                }
            ],
        }

        def mutated(mutator: Any) -> dict[str, Any]:
            report = json.loads(json.dumps(base_report))
            mutator(report)
            return report

        weak_reports = [
            mutated(lambda report: report.__setitem__("kind", "handwritten_counterfactual")),
            mutated(lambda report: report.__setitem__("proof_scope", "boss_ai.generic")),
            mutated(lambda report: report.__setitem__("skipped_count", 1)),
            mutated(lambda report: report["basis"].__setitem__("dirty_diff_hash", "stale")),
            mutated(lambda report: report["witnesses"][0]["baseline_trace"].__setitem__("source", "python")),
            mutated(lambda report: report["witnesses"][0]["baseline_trace"].__setitem__("executed_rule_ids", [])),
            mutated(lambda report: report["witnesses"][0]["mutation"].__setitem__("changed_keys", ["wBossAISwitchConfidence", "wPlayerScreens"])),
            mutated(lambda report: report["witnesses"][0]["mutation"].__setitem__("changed_keys", ["wCurPlayerMove"])),
            mutated(lambda report: report["witnesses"][0].__setitem__("counterfactual_observable", report["witnesses"][0]["baseline_observable"])),
            mutated(lambda report: report["witnesses"][0].__setitem__("decision_surface", "move_score")),
            mutated(
                lambda report: (
                    report["witnesses"][0].__setitem__(
                        "rule_id",
                        "switch.apply_role_package_switch_bias",
                    ),
                    report["witnesses"][0]["source_anchor"].__setitem__(
                        "rule_id",
                        "switch.apply_role_package_switch_bias",
                    ),
                    report["witnesses"][0]["baseline_trace"].__setitem__(
                        "executed_rule_ids",
                        ["switch.apply_role_package_switch_bias"],
                    ),
                )
            ),
        ]
        for report in weak_reports:
            evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}
            add_witness_evidence_from_counterfactual_materialization(
                evidence,
                report=report,
                artifact_path="counterfactuals/weak.json",
                rule_surfaces={
                    "switch.try_switch": "switch_dispatch",
                    "switch.apply_role_package_switch_bias": "switch_dispatch",
                },
                identity=identity,
            )
            self.assertNotIn(("switch.try_switch", "counterfactual_flip"), evidence)
            self.assertNotIn(
                ("switch.apply_role_package_switch_bias", "counterfactual_flip"),
                evidence,
            )

    def test_deity_packet_counterfactual_witness_requires_decisive_rom_observation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "packet.json"
            packet.write_text(
                json.dumps(
                    {
                        "proof_status": {
                            "present_ids": [
                                "observed_rom_decision",
                                "counterfactual.decisive",
                            ],
                        },
                        "source_anchors": [
                            {
                                "anchor_status": "mapped",
                                "rule_id": "move.select_move",
                                "source_label": "BossAI_SelectMove",
                                "parent_label": "BossAI_SelectMove",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            evidence: dict[tuple[str, str], list[dict[str, object]]] = {}

            add_witness_evidence_from_deity_packets(evidence, [packet], root=root)

        counterfactual = evidence[("move.select_move", "counterfactual_flip")][0]
        self.assertEqual(counterfactual["evidence_kind"], "deity_explain_decision_counterfactual")
        self.assertEqual(counterfactual["status"], "counterfactual_flip_observed")
        self.assertNotIn(("move.select_move", "positive"), evidence)

    def test_deity_packet_switch_no_proposal_credits_only_try_switch_negative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "packet.json"
            packet.write_text(
                json.dumps(
                    {
                        "proof_status": {
                            "present_ids": [
                                "observed_rom_decision",
                                "switch_path",
                                "switch_materialization",
                            ],
                        },
                        "source_anchors": [
                            {
                                "anchor_status": "mapped",
                                "rule_id": "switch.compute_switch_confidence",
                            },
                            {
                                "anchor_status": "mapped",
                                "rule_id": "switch.try_switch",
                                "source_label": "BossAI_TrySwitch",
                                "parent_label": "BossAI_TrySwitch",
                            },
                        ],
                        "rom_evidence": [
                            {
                                "kind": "rom_switch_materialization",
                                "error_count": 0,
                                "verdicts": [
                                    {
                                        "scenario_id": "no_switch_proposal",
                                        "rom": {
                                            "source": "trace_rom_pyboy_switch",
                                            "switch_gate_evaluated": True,
                                            "observation_status": "switch_gate_evaluated_no_proposal",
                                            "observed_decision": True,
                                            "observed_switch_path": False,
                                            "proposed_switch": False,
                                            "actual_switch": False,
                                            "switch_confidence": 0,
                                        },
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            evidence: dict[tuple[str, str], list[dict[str, object]]] = {}

            add_witness_evidence_from_deity_packets(evidence, [packet], root=root)

        negative = evidence[("switch.try_switch", "negative")][0]
        self.assertEqual(negative["evidence_kind"], "deity_switch_materialization_no_proposal_negative")
        self.assertEqual(negative["status"], "negative_no_switch_proposal_observed")
        self.assertEqual(negative["scenario_id"], "no_switch_proposal")
        self.assertNotIn(("switch.compute_switch_confidence", "negative"), evidence)
        self.assertNotIn(("switch.try_switch", "counterfactual_flip"), evidence)

    def test_deity_packet_switch_no_proposal_negative_fails_closed_on_weak_packets(self) -> None:
        base_packet = {
            "proof_status": {
                "present_ids": [
                    "observed_rom_decision",
                    "switch_path",
                    "switch_materialization",
                ],
            },
            "source_anchors": [
                {
                    "anchor_status": "mapped",
                    "rule_id": "switch.try_switch",
                }
            ],
            "rom_evidence": [
                {
                    "kind": "rom_switch_materialization",
                    "error_count": 0,
                    "verdicts": [
                        {
                            "scenario_id": "no_switch_proposal",
                            "rom": {
                                "source": "trace_rom_pyboy_switch",
                                "switch_gate_evaluated": True,
                                "observation_status": "switch_gate_evaluated_no_proposal",
                                "observed_decision": True,
                                "observed_switch_path": False,
                                "proposed_switch": False,
                                "actual_switch": False,
                                "switch_confidence": 0,
                            },
                        }
                    ],
                }
            ],
        }
        weak_packets = [
            {
                **base_packet,
                "proof_status": {"present_ids": ["observed_rom_decision", "switch_path"]},
            },
            {
                **base_packet,
                "source_anchors": [{"anchor_status": "mapped", "rule_id": "switch.compute_switch_confidence"}],
            },
            {
                **base_packet,
                "rom_evidence": [{**base_packet["rom_evidence"][0], "error_count": 1}],
            },
            {
                **base_packet,
                "rom_evidence": [
                    {
                        **base_packet["rom_evidence"][0],
                        "verdicts": [
                            {
                                "scenario_id": "wrong_backend",
                                "rom": {
                                    **base_packet["rom_evidence"][0]["verdicts"][0]["rom"],
                                    "source": "python_model",
                                },
                            }
                        ],
                    }
                ],
            },
            {
                **base_packet,
                "rom_evidence": [
                    {
                        **base_packet["rom_evidence"][0],
                        "verdicts": [
                            {
                                "scenario_id": "proposal_not_taken",
                                "rom": {
                                    **base_packet["rom_evidence"][0]["verdicts"][0]["rom"],
                                    "observation_status": "switch_proposal_observed",
                                    "observed_switch_path": True,
                                    "proposed_switch": True,
                                },
                            }
                        ],
                    }
                ],
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = []
            for index, packet in enumerate(weak_packets):
                path = root / f"packet_{index}.json"
                path.write_text(json.dumps(packet), encoding="utf-8")
                paths.append(path)
            evidence: dict[tuple[str, str], list[dict[str, object]]] = {}

            add_witness_evidence_from_deity_packets(evidence, paths, root=root)

        self.assertEqual(evidence, {})

    def test_deity_packet_switch_roll_credits_only_try_switch_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "packet.json"
            packet.write_text(json.dumps(switch_roll_boundary_packet()), encoding="utf-8")
            evidence: dict[tuple[str, str], list[dict[str, object]]] = {}

            add_witness_evidence_from_deity_packets(evidence, [packet], root=root)

        self.assertEqual(set(evidence), {("switch.try_switch", "boundary")})
        boundary = evidence[("switch.try_switch", "boundary")][0]
        self.assertEqual(boundary["evidence_kind"], "deity_switch_materialization_roll_boundary")
        self.assertEqual(boundary["status"], "switch_roll_boundary_observed")
        self.assertEqual(
            boundary["scenario_id"],
            "generated_switch_sack_1_00006_preserve_wincon_over_comfort_damage",
        )
        self.assertEqual(boundary["switch_confidence"], 99)
        self.assertEqual(boundary["switch_param"], 49)
        self.assertEqual(boundary["switch_index"], 0)
        self.assertEqual(boundary["switch_chance_threshold"], 230)
        self.assertAlmostEqual(boundary["switch_probability"], 230 / 256)
        self.assertNotIn(("switch.compute_switch_confidence", "boundary"), evidence)
        self.assertNotIn(("switch.get_switch_threshold", "boundary"), evidence)
        self.assertNotIn(("switch.try_switch", "positive"), evidence)
        self.assertNotIn(("switch.try_switch", "negative"), evidence)
        self.assertNotIn(("switch.try_switch", "counterfactual_flip"), evidence)

    def test_deity_packet_switch_roll_boundary_fails_closed_on_weak_packets(self) -> None:
        base_packet = switch_roll_boundary_packet()

        def verdict(packet: dict[str, object]) -> dict[str, object]:
            rom_evidence = packet["rom_evidence"]  # type: ignore[index]
            return rom_evidence[0]["verdicts"][0]  # type: ignore[index]

        def rom(packet: dict[str, object]) -> dict[str, object]:
            return verdict(packet)["rom"]  # type: ignore[index]

        def switch_roll(packet: dict[str, object]) -> dict[str, object]:
            return verdict(packet)["switch_roll"]  # type: ignore[index]

        def mutated(mutator: Any) -> dict[str, object]:
            packet = json.loads(json.dumps(base_packet))
            mutator(packet)
            return packet

        weak_packets = [
            mutated(
                lambda packet: packet["proof_status"].__setitem__(  # type: ignore[index]
                    "present_ids", ["observed_rom_decision", "switch_path"]
                )
            ),
            mutated(
                lambda packet: packet["source_anchors"][1].__setitem__(  # type: ignore[index]
                    "anchor_status", "unmapped"
                )
            ),
            mutated(
                lambda packet: packet["source_anchors"][1].__setitem__(  # type: ignore[index]
                    "source_label", "BossAI_GetSwitchThreshold"
                )
            ),
            mutated(lambda packet: packet["rom_evidence"][0].__setitem__("kind", "rom_score_trace")),  # type: ignore[index]
            mutated(lambda packet: packet["rom_evidence"][0].__setitem__("checked_count", 0)),  # type: ignore[index]
            mutated(lambda packet: packet["rom_evidence"][0].__setitem__("error_count", 1)),  # type: ignore[index]
            mutated(lambda packet: packet["rom_evidence"][0].__setitem__("skipped_count", 1)),  # type: ignore[index]
            mutated(
                lambda packet: packet["rom_evidence"][0].__setitem__(  # type: ignore[index]
                    "policy_disagreement_count", 1
                )
            ),
            mutated(lambda packet: verdict(packet).__setitem__("status", "skip")),
            mutated(lambda packet: rom(packet).__setitem__("source", "python_model")),
            mutated(
                lambda packet: rom(packet).__setitem__(
                    "observation_status", "switch_gate_evaluated_no_proposal"
                )
            ),
            mutated(lambda packet: rom(packet).__setitem__("proposed_switch", False)),
            mutated(lambda packet: rom(packet).__setitem__("actual_switch", True)),
            mutated(lambda packet: verdict(packet).pop("switch_roll")),
            mutated(lambda packet: switch_roll(packet).__setitem__("confidence", 98)),
            mutated(lambda packet: switch_roll(packet).__setitem__("probability_exact", False)),
            mutated(
                lambda packet: switch_roll(packet)["possible_switch_probabilities"][0].__setitem__(  # type: ignore[index]
                    "switch_chance_threshold", 229
                )
            ),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = []
            for index, packet in enumerate(weak_packets):
                path = root / f"packet_{index}.json"
                path.write_text(json.dumps(packet), encoding="utf-8")
                paths.append(path)
            evidence: dict[tuple[str, str], list[dict[str, object]]] = {}

            add_witness_evidence_from_deity_packets(evidence, paths, root=root)

        self.assertEqual(evidence, {})

    def test_deity_packet_enemy_under_pressure_credits_only_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "packet.json"
            packet.write_text(json.dumps(enemy_under_pressure_boundary_packet()), encoding="utf-8")
            evidence: dict[tuple[str, str], list[dict[str, object]]] = {}

            add_witness_evidence_from_deity_packets(evidence, [packet], root=root)

        self.assertEqual(set(evidence), {("move.apply_move_model.enemy_under_pressure", "boundary")})
        boundary = evidence[("move.apply_move_model.enemy_under_pressure", "boundary")][0]
        self.assertEqual(
            boundary["evidence_kind"],
            "deity_score_materialization_enemy_under_pressure_boundary",
        )
        self.assertEqual(boundary["status"], "score_boundary_observed")
        self.assertEqual(boundary["scenario_id"], "generated_spikes_spin_1_00000")
        self.assertEqual(boundary["candidate_move"], "SPIKES")
        self.assertEqual(boundary["candidate_move_id"], 191)
        self.assertEqual(boundary["slot_index"], 0)
        self.assertEqual(boundary["before"], 20)
        self.assertEqual(boundary["after"], 19)
        self.assertEqual(boundary["delta"], -1)
        self.assertEqual(boundary["operation"], "encourage_tier_weight")
        self.assertEqual(boundary["best_action_id"], "move_spikes")
        self.assertEqual(boundary["second_action_id"], "move_sludge_bomb")
        self.assertEqual(boundary["score_gap"], 1)
        self.assertNotIn(("move.apply_lookahead_to_top_move_candidates", "boundary"), evidence)
        self.assertNotIn(("move.apply_move_model.enemy_under_pressure", "positive"), evidence)
        self.assertNotIn(("move.apply_move_model.enemy_under_pressure", "negative"), evidence)
        self.assertNotIn(("move.apply_move_model.enemy_under_pressure", "counterfactual_flip"), evidence)

    def test_deity_packet_enemy_under_pressure_boundary_fails_closed_on_weak_packets(self) -> None:
        base_packet = enemy_under_pressure_boundary_packet()

        def observed(packet: dict[str, object]) -> dict[str, object]:
            return packet["observed_rom_decision"]  # type: ignore[index]

        def agreement(packet: dict[str, object]) -> dict[str, object]:
            return observed(packet)["python_agreement"]  # type: ignore[index]

        def selector_path(packet: dict[str, object]) -> dict[str, object]:
            decision = observed(packet)["decision"]  # type: ignore[index]
            return decision["selector_path"]  # type: ignore[index]

        def contribution_event(packet: dict[str, object]) -> dict[str, object]:
            rom_contributions = packet["rom_contributions"]  # type: ignore[index]
            return rom_contributions["events"][0]  # type: ignore[index]

        def mutated(mutator: Any) -> dict[str, object]:
            packet = json.loads(json.dumps(base_packet))
            mutator(packet)
            return packet

        weak_packets = [
            mutated(lambda packet: packet.__setitem__("family", "switch_sack")),
            mutated(lambda packet: packet.__setitem__("deity_evidence_marker", "")),
            mutated(lambda packet: packet.__setitem__("proof_blockers", ["missing"])),
            mutated(
                lambda packet: packet["proof_status"].__setitem__(  # type: ignore[index]
                    "present_ids",
                    [
                        "observed_rom_decision",
                        "score_bytes",
                        "selector_path",
                        "rom_contribution_deltas",
                        "score_rule.rom_delta_observed",
                    ],
                )
            ),
            mutated(lambda packet: agreement(packet).__setitem__("contribution_mismatches", 1)),
            mutated(
                lambda packet: packet["source_anchors"][0].__setitem__(  # type: ignore[index]
                    "rule_id", "move.apply_lookahead_to_top_move_candidates"
                )
            ),
            mutated(lambda packet: contribution_event(packet).__setitem__("delta", 1)),
            mutated(lambda packet: selector_path(packet).__setitem__("source", "python_model")),
            mutated(lambda packet: selector_path(packet).__setitem__("score_gap", 2)),
            mutated(
                lambda packet: packet["candidate_scores"][0]["contributions"][0].__setitem__(  # type: ignore[index]
                    "delta", 0
                )
            ),
            mutated(lambda packet: observed(packet).__setitem__("status", "skip")),
            mutated(lambda packet: contribution_event(packet).__setitem__("rule_id", "move.select_move")),
            mutated(
                lambda packet: contribution_event(packet)["source_anchor"].__setitem__(  # type: ignore[index]
                    "anchor_status", "unmapped"
                )
            ),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = []
            for index, packet in enumerate(weak_packets):
                path = root / f"packet_{index}.json"
                path.write_text(json.dumps(packet), encoding="utf-8")
                paths.append(path)
            evidence: dict[tuple[str, str], list[dict[str, object]]] = {}

            add_witness_evidence_from_deity_packets(evidence, paths, root=root)

        self.assertEqual(evidence, {})

    def test_deity_packet_apply_spikes_layer_bias_credits_non_spikes_negative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "packet.json"
            packet.write_text(json.dumps(apply_spikes_layer_bias_negative_packet()), encoding="utf-8")
            evidence: dict[tuple[str, str], list[dict[str, object]]] = {}

            add_witness_evidence_from_deity_packets(evidence, [packet], root=root)

        self.assertEqual(
            set(evidence),
            {("move.apply_move_model.apply_spikes_layer_bias", "negative")},
        )
        negative = evidence[("move.apply_move_model.apply_spikes_layer_bias", "negative")][0]
        self.assertEqual(
            negative["evidence_kind"],
            "deity_score_materialization_apply_spikes_layer_bias_non_spikes_negative",
        )
        self.assertEqual(negative["status"], "negative_non_spikes_candidate_observed")
        self.assertEqual(negative["source_label"], ".ApplySpikesLayerBias")
        self.assertEqual(negative["scenario_id"], "generated_spikes_spin_1_00000")
        self.assertEqual(negative["candidate_action_id"], "move_sludge_bomb")
        self.assertEqual(negative["candidate_move"], "SLUDGE_BOMB")
        self.assertEqual(negative["candidate_move_id"], 188)
        self.assertEqual(negative["slot_index"], 1)
        self.assertEqual(negative["initial_score"], 20)
        self.assertEqual(negative["pre_lookahead_score"], 20)
        self.assertEqual(negative["final_score"], 38)
        self.assertEqual(
            negative["only_contribution_rule_id"],
            "move.apply_lookahead_to_top_move_candidates",
        )
        self.assertEqual(negative["lookahead_delta"], 18)
        self.assertEqual(negative["best_action_id"], "move_spikes")
        self.assertEqual(negative["second_action_id"], "move_sludge_bomb")
        self.assertEqual(negative["score_gap"], 1)
        self.assertEqual(negative["input_id"], "spikes_existing_layer_count")
        self.assertEqual(negative["outcome"], "zero_existing_layers")
        self.assertEqual(negative["snapshot_keys"], ["wPlayerScreens"])
        self.assertNotIn(("move.apply_move_model.apply_spikes_layer_bias", "positive"), evidence)
        self.assertNotIn(("move.apply_move_model.apply_spikes_layer_bias", "boundary"), evidence)
        self.assertNotIn(("move.apply_move_model.apply_spikes_layer_bias", "counterfactual_flip"), evidence)

    def test_deity_packet_apply_spikes_layer_bias_negative_fails_closed_on_weak_packets(self) -> None:
        base_packet = apply_spikes_layer_bias_negative_packet()

        def observed(packet: dict[str, object]) -> dict[str, object]:
            return packet["observed_rom_decision"]  # type: ignore[index]

        def agreement(packet: dict[str, object]) -> dict[str, object]:
            return observed(packet)["python_agreement"]  # type: ignore[index]

        def selector_path(packet: dict[str, object]) -> dict[str, object]:
            decision = observed(packet)["decision"]  # type: ignore[index]
            return decision["selector_path"]  # type: ignore[index]

        def public_branch(packet: dict[str, object]) -> dict[str, object]:
            public_info = packet["public_info_inputs"]  # type: ignore[index]
            return public_info["predicate_branches"][0]  # type: ignore[index]

        def public_anchor(packet: dict[str, object]) -> dict[str, object]:
            return public_branch(packet)["source_anchor"]  # type: ignore[index]

        def candidate_score(packet: dict[str, object]) -> dict[str, object]:
            return packet["candidate_scores"][0]  # type: ignore[index]

        def candidate_contribution(packet: dict[str, object]) -> dict[str, object]:
            return candidate_score(packet)["contributions"][0]  # type: ignore[index]

        def contribution_event(packet: dict[str, object]) -> dict[str, object]:
            rom_contributions = packet["rom_contributions"]  # type: ignore[index]
            return rom_contributions["events"][0]  # type: ignore[index]

        def event_candidate(packet: dict[str, object]) -> dict[str, object]:
            return contribution_event(packet)["candidate"]  # type: ignore[index]

        def mutated(mutator: Any) -> dict[str, object]:
            packet = json.loads(json.dumps(base_packet))
            mutator(packet)
            return packet

        weak_packets = [
            mutated(lambda packet: packet.__setitem__("family", "switch_sack")),
            mutated(lambda packet: packet.__setitem__("proof_blockers", ["missing"])),
            mutated(lambda packet: packet["proof_status"].__setitem__("missing_ids", ["missing"])),  # type: ignore[index]
            mutated(
                lambda packet: packet["proof_status"].__setitem__(  # type: ignore[index]
                    "present_ids",
                    [
                        "observed_rom_decision",
                        "candidate_scores",
                        "score_bytes",
                        "selector_path",
                        "rom_contribution_deltas",
                    ],
                )
            ),
            mutated(lambda packet: public_anchor(packet).__setitem__("source_label", ".EnemyUnderPressure")),
            mutated(lambda packet: public_anchor(packet).__setitem__("public_reads", ["wPlayerScreens"])),
            mutated(lambda packet: public_branch(packet).__setitem__("outcome", "one_existing_layer")),
            mutated(
                lambda packet: public_branch(packet)["snapshot"]["wPlayerScreens"].__setitem__(  # type: ignore[index]
                    "values",
                    [1],
                )
            ),
            mutated(lambda packet: agreement(packet).__setitem__("score_bytes_match", False)),
            mutated(lambda packet: selector_path(packet).__setitem__("second_action_id", "move_surf")),
            mutated(lambda packet: candidate_score(packet).__setitem__("name", "Spikes")),
            mutated(lambda packet: candidate_score(packet).__setitem__("pre_lookahead_score", 19)),
            mutated(lambda packet: candidate_contribution(packet).__setitem__("rule_id", "move.apply_move_model.apply_spikes_layer_bias")),
            mutated(lambda packet: contribution_event(packet).__setitem__("operation", "discourage_tier_weight")),
            mutated(lambda packet: event_candidate(packet).__setitem__("move_id", 191)),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = []
            for index, packet in enumerate(weak_packets):
                path = root / f"packet_{index}.json"
                path.write_text(json.dumps(packet), encoding="utf-8")
                paths.append(path)
            evidence: dict[tuple[str, str], list[dict[str, object]]] = {}

            add_witness_evidence_from_deity_packets(evidence, paths, root=root)

        self.assertEqual(evidence, {})

    def test_deity_packet_nested_public_info_anchor_credits_counterfactual_witness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "packet.json"
            packet.write_text(
                json.dumps(
                    {
                        "proof_status": {
                            "present_ids": [
                                "observed_rom_decision",
                                "counterfactual.decisive",
                            ],
                        },
                        "public_info_inputs": {
                            "predicate_branches": [
                                {
                                    "predicate_id": "spikes_existing_layer_count",
                                    "outcome": "zero_existing_layers",
                                    "snapshot": {"wPlayerScreens": {"values": [0]}},
                                    "source_anchor": {
                                        "anchor_status": "mapped",
                                        "rule_id": "move.apply_move_model.apply_spikes_layer_bias",
                                        "source_label": ".ApplySpikesLayerBias",
                                        "parent_label": "BossAI_ApplyMoveModel",
                                    },
                                }
                            ],
                            "public_read_probes": [
                                {
                                    "probe_id": "spikes_existing_layer_count",
                                    "outcome": "zero_existing_layers",
                                    "snapshot": {"wPlayerScreens": {"values": [0]}},
                                    "source_anchor": {
                                        "anchor_status": "mapped",
                                        "rule_id": "move.apply_move_model.apply_spikes_layer_bias",
                                        "source_label": ".ApplySpikesLayerBias",
                                        "parent_label": "BossAI_ApplyMoveModel",
                                    },
                                }
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )
            evidence: dict[tuple[str, str], list[dict[str, object]]] = {}

            add_witness_evidence_from_deity_packets(evidence, [packet], root=root)

        counterfactual = evidence[
            ("move.apply_move_model.apply_spikes_layer_bias", "counterfactual_flip")
        ]
        self.assertEqual(
            {
                item["evidence_kind"]
                for item in counterfactual
            },
            {"deity_explain_decision_public_info_counterfactual"},
        )
        self.assertEqual(
            {item["input_kind"] for item in counterfactual},
            {"predicate_branch", "public_read_probe"},
        )
        self.assertTrue(all(item["snapshot_keys"] == ["wPlayerScreens"] for item in counterfactual))

    def test_deity_packet_nested_public_info_anchor_requires_decisive_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "packet.json"
            packet.write_text(
                json.dumps(
                    {
                        "proof_status": {"present_ids": ["observed_rom_decision"]},
                        "public_info_inputs": {
                            "predicate_branches": [
                                {
                                    "predicate_id": "spikes_existing_layer_count",
                                    "outcome": "zero_existing_layers",
                                    "snapshot": {"wPlayerScreens": {"values": [0]}},
                                    "source_anchor": {
                                        "anchor_status": "mapped",
                                        "rule_id": "move.apply_move_model.apply_spikes_layer_bias",
                                    },
                                }
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )
            evidence: dict[tuple[str, str], list[dict[str, object]]] = {}

            add_witness_evidence_from_deity_packets(evidence, [packet], root=root)

        self.assertEqual(evidence, {})

    def test_deity_packet_ignores_nested_score_contribution_source_anchors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "packet.json"
            packet.write_text(
                json.dumps(
                    {
                        "proof_status": {
                            "present_ids": [
                                "observed_rom_decision",
                                "counterfactual.decisive",
                            ],
                        },
                        "candidate_scores": [
                            {
                                "contributions": [
                                    {
                                        "source_anchor": {
                                            "anchor_status": "mapped",
                                            "rule_id": "move.score_contribution_only",
                                        }
                                    }
                                ]
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            evidence: dict[tuple[str, str], list[dict[str, object]]] = {}

            add_witness_evidence_from_deity_packets(evidence, [packet], root=root)

        self.assertEqual(evidence, {})

    def test_deity_packet_counterfactual_witness_fails_closed_on_weak_packets(self) -> None:
        weak_packets = [
            {
                "proof_status": {"present_ids": ["observed_rom_decision"]},
                "source_anchors": [
                    {"anchor_status": "mapped", "rule_id": "move.no_decisive"}
                ],
            },
            {
                "proof_status": {"present_ids": ["counterfactual.decisive"]},
                "source_anchors": [
                    {"anchor_status": "mapped", "rule_id": "move.no_rom"}
                ],
            },
            {
                "proof_status": {
                    "present_ids": ["observed_rom_decision", "counterfactual.decisive"]
                },
                "source_anchors": [{"anchor_status": "mapped"}],
            },
            {
                "proof_status": {
                    "present_ids": ["observed_rom_decision", "counterfactual.decisive"]
                },
                "source_anchors": [
                    {"anchor_status": "unmapped", "rule_id": "move.unmapped"}
                ],
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = []
            for index, packet in enumerate(weak_packets):
                path = root / f"packet_{index}.json"
                path.write_text(json.dumps(packet), encoding="utf-8")
                paths.append(path)
            evidence: dict[tuple[str, str], list[dict[str, object]]] = {}

            add_witness_evidence_from_deity_packets(evidence, paths, root=root)

        self.assertEqual(evidence, {})

    def test_cli_universe_writes_json_and_passes_green(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "universe.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(["universe", "--json-out", str(out)])

            report = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(report["kind"], "boss_ai_debugger_universe")
        self.assertEqual(report["proof_status"], "complete")
        self.assertEqual(report["counters"]["missing_class_id_count"], 0)
        self.assertEqual(report["counters"]["missing_witness_role_count"], 0)
        self.assertTrue(report["canonical_class_rows"][0]["class_id"].startswith("csc_"))


if __name__ == "__main__":
    unittest.main()
