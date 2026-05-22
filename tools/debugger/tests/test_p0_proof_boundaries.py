from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.debugger.address import address_spec_requires_exact_key, parse_address_spec
from tools.debugger.causal_graph import build_causal_graph_report
from tools.debugger.impact import build_impact_report
from tools.debugger.ranking import rank_findings
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
