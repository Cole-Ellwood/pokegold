from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.debugger.address import address_spec_requires_exact_key, parse_address_spec
from tools.debugger.causal_graph import build_causal_graph_report
from tools.debugger.dynamic_taint import build_dynamic_taint_report
from tools.debugger.evidence import bank_state_record, evidence_atom
from tools.debugger.impact import build_impact_report
from tools.debugger.ranking import rank_findings
from tools.debugger.reverse_query import build_reverse_query_report
from tools.debugger.visualization import build_visualization_report


class P0ProofBoundaryAcceptanceTests(unittest.TestCase):
    def test_ranking_dynamic_write_attribution_preserves_planned_proof_status(self) -> None:
        with dynamic_taint_report() as root:
            ranked = rank_findings(reports=("dynamic_taint.json",), root=root)

        attribution = next(item for item in ranked["findings"] if item["type"] == "reverse_attribution")

        self.assertEqual(attribution["proof_status"], "planned_only")
        self.assertIn("match_precision=bus_address_unverified_bank", attribution["evidence"])
        self.assertIn("proof_downgrade_reason=unexecuted_trace_synthesis_route", attribution["evidence"])

    def test_impact_dynamic_write_attribution_preserves_planned_proof_status(self) -> None:
        with dynamic_taint_report() as root:
            impact = build_impact_report(reports=("dynamic_taint.json",), root=root)

        attribution = next(item for item in impact["items"] if item["type"] == "reverse_attribution")

        self.assertEqual(attribution["proof_status"], "planned_only")
        self.assertIn("match_precision=bus_address_unverified_bank", attribution["evidence"])
        self.assertIn("planned attribution with hypothetical write", "\n".join(attribution["evidence"]))

    def test_impact_renders_typed_bank_state_records_from_evidence_atoms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "nested_impact.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_impact_report",
                        "valid": True,
                        "items": [
                            {
                                "type": "reverse_query",
                                "title": "Reverse query: sram A100",
                                "severity": 70,
                                "confidence": 0.9,
                                "impact_score": 80,
                                "proof_status": "instruction_observed",
                                "evidence": ["last_writer=WriteSram"],
                                "evidence_atoms": [
                                    evidence_atom(
                                        claim_type="reverse_query.last_writer",
                                        origin="reverse_query",
                                        observation_type="instruction",
                                        proof_status="instruction_observed",
                                        validation={
                                            "last_writer_bank_state_records": [
                                                bank_state_record(
                                                    name="sram",
                                                    value=2,
                                                    source="inferred_bank_state.sram",
                                                    valid_for_spaces=("sram",),
                                                ).as_dict()
                                            ]
                                        },
                                    )
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            impact = build_impact_report(reports=("nested_impact.json",), root=root)

        reverse_item = next(item for item in impact["items"] if item["type"] == "reverse_query")

        self.assertEqual(reverse_item["proof_status"], "instruction_observed")
        self.assertIn(
            "bank_state_record=last_writer:sram=0x02 source=inferred_bank_state.sram state=inferred_from_io_write valid_for=sram",
            reverse_item["evidence"],
        )

    def test_causal_graph_reverse_query_missing_result_proof_defaults_planned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reverse.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_reverse_query",
                        "valid": True,
                        "results": [
                            {
                                "target": {"label": "wCurDamage", "symbol": "wCurDamage"},
                                "matched_address": "D141",
                                "evidence": ["no concrete last writer in supplied effect window"],
                                "last_writer": None,
                                "write_count": 0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            graph = build_causal_graph_report(reports=("reverse.json",), root=root)

        reverse_node = next(node for node in graph["nodes"] if node["kind"] == "reverse_query")
        answer_edge = next(edge for edge in graph["edges"] if edge["relation"] == "answers_target")

        self.assertEqual(reverse_node["proof_status"], "planned_only")
        self.assertEqual(answer_edge["proof_status"], "planned_only")

    def test_visualization_shared_node_requires_mixed_proof_badge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dynamic.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_dynamic_taint_report",
                        "valid": True,
                        "write_attributions": [
                            {
                                "id": "planned_attribution",
                                "target": "wCurDamage",
                                "pc_label": "PlannedWriter",
                                "mnemonic": "planned write",
                                "seq": 3,
                                "proof_status": "planned_only",
                                "related_symbols": ["wCurDamage"],
                            }
                        ],
                        "paths": [
                            {
                                "id": "dynamic_taint_path_0001",
                                "title": "move_power -> wCurDamage",
                                "target": "wCurDamage",
                                "proof_status": "taint_proven",
                                "related_symbols": ["move_power", "wCurDamage"],
                                "evidence": ["taint=move_power"],
                                "score": 92,
                                "confidence": 0.9,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            visualization = build_visualization_report(reports=("dynamic.json",), root=root)

        node = next(item for item in visualization["graph"]["nodes"] if item["label"] == "wCurDamage")

        self.assertEqual(node["proof_badge"], "mixed")
        self.assertEqual(node["proof_min"], "planned_only")
        self.assertEqual(node["proof_max"], "taint_proven")

    def test_address_spec_rejects_impossible_bank_for_unbanked_space(self) -> None:
        exact = parse_address_spec("02:$D141")
        fixed_wram0 = parse_address_spec("00:$C000")

        self.assertTrue(address_spec_requires_exact_key(exact))
        self.assertFalse(address_spec_requires_exact_key(fixed_wram0))
        for raw in ("00:$D141", "08:$D141", "01:$C000", "01:$FF12"):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    parse_address_spec(raw)

    def test_reverse_query_synthesizes_typed_bank_state_records_from_legacy_scalar_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("01:4000 UnitFunc\n", encoding="utf-8")
            (root / "legacy_effect.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "unified_debugger_effect_trace",
                        "valid": True,
                        "write_index": [
                            {
                                "address": "A100",
                                "address_key": "sram:02:A100",
                                "space": "sram",
                                "bank": 2,
                                "write_count": 1,
                                "last_writer_seq": 2,
                                "last_writer_pc": "01:4006",
                                "last_value_hex": "22",
                            }
                        ],
                        "events": [
                            {
                                "seq": 2,
                                "trace_source": "legacy_trace.jsonl",
                                "pc_bank_address": "01:4006",
                                "pc_label": "WriteSram",
                                "pre_registers": {"A": 0x22},
                                "observed_memory": [],
                                "bank_state": {
                                    "sram": 2,
                                    "sram_inferred": 1,
                                    "sram_enabled": 0,
                                },
                                "bank_state_sources": {
                                    "sram": "inferred_bank_state.sram",
                                },
                                "effects": [
                                    {
                                        "access": "write",
                                        "kind": "memory_write",
                                        "operation": "ld [nn], a",
                                        "address_hex": "A100",
                                        "address_key": "sram:02:A100",
                                        "value_hex": "22",
                                        "value_source": "A",
                                        "bank": 2,
                                        "bank_source": "inferred_bank_state.sram",
                                        "space": "sram",
                                        "sram_enabled": 0,
                                        "sram_enabled_source": "bank_state.sram_enabled",
                                        "post_value_hex": "22",
                                        "post_value_status": "matched",
                                        "post_observed_seq": 3,
                                        "post_observed_pc": "01:4009",
                                        "proof_status": "instruction_observed",
                                    }
                                ],
                            }
                        ],
                        "trace_window": {
                            "checkpoints": [
                                {
                                    "kind": "trace_checkpoint",
                                    "checkpoint_kind": "pre_instruction_trace_frame",
                                    "checkpoint_source": "instruction_trace",
                                    "emulator_replay": False,
                                    "emulator_replay_status": "not_run",
                                    "source": "legacy_trace.jsonl",
                                    "seq": 2,
                                    "pc_bank_address": "01:4006",
                                    "pc_label": "WriteSram",
                                    "registers": {"A": 0x22},
                                    "bank_state": {
                                        "sram": 2,
                                        "sram_inferred": 1,
                                        "sram_enabled": 0,
                                    },
                                    "bank_state_sources": {
                                        "sram": "inferred_bank_state.sram",
                                    },
                                    "observed_memory": [],
                                }
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )

            reverse = build_reverse_query_report(
                reports=("legacy_effect.json",),
                addresses=("02:$A100",),
                symbols_path="test.sym",
                root=root,
            )
            (root / "reverse.json").write_text(json.dumps(reverse), encoding="utf-8")
            ranked = rank_findings(reports=("reverse.json",), root=root)
            graph = build_causal_graph_report(reports=("reverse.json",), root=root)

        result = reverse["results"][0]
        span = result["bounded_effect_span_validation"]
        ranked_reverse = next(item for item in ranked["findings"] if item["type"] == "reverse_query")
        graph_reverse_node = next(item for item in graph["nodes"] if item["kind"] == "reverse_query")
        graph_answer_edge = next(item for item in graph["edges"] if item["relation"] == "answers_target")
        last_writer_records = {item["name"]: item for item in result["last_writer"]["bank_state_records"]}
        checkpoint_records = {
            item["name"]: item
            for item in result["checkpoint_validation"]["checkpoint"]["bank_state_records"]
        }
        span_checkpoint_records = {item["name"]: item for item in span["checkpoint_bank_state_records"]}
        span_write_records = {item["name"]: item for item in span["writes"][-1]["bank_state_records"]}
        atom = next(item for item in result["evidence_atoms"] if item["claim_type"] == "reverse_query.last_writer")
        atom_records = {item["name"]: item for item in atom["validation"]["last_writer_bank_state_records"]}

        self.assertTrue(reverse["valid"])
        self.assertEqual(result["matched_address_key"], "sram:02:A100")
        self.assertEqual(span["status"], "effect_span_consistent")
        self.assertEqual(last_writer_records["sram"]["state_kind"], "inferred_from_io_write")
        self.assertTrue(last_writer_records["sram"]["inferred"])
        self.assertEqual(last_writer_records["sram_enabled"]["state_kind"], "sram_disabled")
        self.assertFalse(last_writer_records["sram_enabled"]["inferred"])
        self.assertNotIn("sram_inferred", last_writer_records)
        self.assertEqual(checkpoint_records["sram"]["source"], "inferred_bank_state.sram")
        self.assertEqual(checkpoint_records["sram_enabled"]["state_kind"], "sram_disabled")
        self.assertEqual(span_checkpoint_records["sram"]["source_kind"], "inferred_bank_state")
        self.assertEqual(span_write_records["sram_enabled"]["source"], "bank_state.sram_enabled")
        self.assertEqual(atom_records["sram_enabled"]["state_kind"], "sram_disabled")
        self.assertIn(
            "bank_state_record=last_writer:sram=0x02 source=inferred_bank_state.sram state=inferred_from_io_write valid_for=sram",
            ranked_reverse["evidence"],
        )
        self.assertIn(
            "bank_state_record=last_writer:sram_enabled=0x00 source=bank_state.sram_enabled state=sram_disabled valid_for=sram",
            ranked_reverse["evidence"],
        )
        self.assertEqual(
            graph_reverse_node["proof_status_by_source"][
                "bank_state:last_writer:sram:inferred_bank_state.sram"
            ],
            "instruction_observed",
        )
        self.assertEqual(
            graph_answer_edge["proof_status_by_source"][
                "bank_state:last_writer:sram_enabled:bank_state.sram_enabled"
            ],
            "instruction_observed",
        )

    def test_dynamic_taint_consumes_typed_bank_state_records_for_runtime_bank_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text(
                "01:D141 wCurDamage\n01:4000 UnitFunc\n",
                encoding="utf-8",
            )
            (root / "instruction_trace.jsonl").write_text(
                json.dumps(
                    {
                        "seq": 0,
                        "bank": 1,
                        "pc": 0x4000,
                        "pc_label": "UnitFunc",
                        "opcode": 0x34,
                        "regs": {"HL": 0xD141},
                        "bank_state_records": [
                            {
                                "name": "wram",
                                "value": 1,
                                "value_hex": "01",
                                "source": "inferred_bank_state.wram",
                                "source_kind": "inferred_bank_state",
                                "state_kind": "inferred_from_io_write",
                                "inferred": True,
                                "valid_for_space": "wramx",
                                "valid_for_spaces": ["wramx"],
                            }
                        ],
                        "watch_values": {"wCurDamage": "0F"},
                        "watch_value_specs": [
                            {
                                "name": "wCurDamage",
                                "value_hex": "0F",
                                "address": 0xD141,
                                "address_hex": "D141",
                                "bank": 1,
                                "bank_address": "01:D141",
                                "size": 1,
                                "address_watch": False,
                                "raw": "",
                                "symbol": "wCurDamage",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            dynamic = build_dynamic_taint_report(
                traces=("instruction_trace.jsonl",),
                symbols_path="test.sym",
                sink_symbols=("wCurDamage",),
                root=root,
            )

        attribution = dynamic["write_attributions"][0]

        self.assertTrue(dynamic["valid"])
        self.assertEqual(attribution["value_hex"], "10")
        self.assertEqual(attribution["bank_source"], "inferred_bank_state.wram")
        self.assertEqual(attribution["source_operands"][0]["value"], "0F")
        self.assertEqual(
            attribution["evidence_atoms"][0]["precision"]["bank_source"],
            "inferred_bank_state.wram",
        )


class dynamic_taint_report:
    def __enter__(self) -> Path:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "dynamic_taint.json").write_text(
            json.dumps(
                {
                    "kind": "unified_debugger_dynamic_taint_report",
                    "valid": True,
                    "write_attributions": [
                        {
                            "target": "wCurDamage",
                            "address": "D141",
                            "pc_label": "PlannedWriter",
                            "score": 82,
                            "confidence": 0.8,
                            "proof_status": "planned_only",
                            "match_precision": "bus_address_unverified_bank",
                            "proof_downgrade_reason": "unexecuted_trace_synthesis_route",
                            "evidence": ["planned attribution with hypothetical write"],
                            "related_symbols": ["wCurDamage", "PlannedWriter"],
                            "related_addresses": ["D141"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return root

    def __exit__(self, *args: object) -> None:
        self.tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
