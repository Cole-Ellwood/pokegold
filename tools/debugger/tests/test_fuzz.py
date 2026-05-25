from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.fuzz import build_fuzz_plan


class FuzzTests(unittest.TestCase):
    def test_fuzz_routes_content_to_source_expectation_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            source = root / "maps" / "NewBarkTown.asm"
            source.write_text(
                "\n".join(
                    [
                        "NewBarkTown_MapEvents:",
                        "\tdef_warp_events",
                        "\twarp_event  1,  1, ROUTE_29, 1",
                        "\tdef_object_events",
                        "\tobject_event  5,  5, SPRITE_SILVER, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, -1, 0, OBJECTTYPE_SCRIPT, 0, RivalScript, -1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            cases_file = root / "fuzz_cases.jsonl"

            report = build_fuzz_plan(
                changed_files=("maps/NewBarkTown.asm",),
                out_cases="fuzz_cases.jsonl",
                max_cases=8,
                seed=11,
                root=root,
            )
            rows = [
                json.loads(line)
                for line in cases_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        commands = "\n".join(report["commands"])
        expectations = {
            expectation
            for case in report["fuzz_cases"]
            for expectation in case["expectations"]
        }
        fuzz_types = {case["fuzz_type"] for case in report["fuzz_cases"]}
        proof_levels = {case["proof_level"] for case in report["fuzz_cases"]}

        self.assertTrue(report["valid"])
        self.assertIn("content_static", report["surfaces"])
        self.assertEqual(report["dynamic_campaign_count"], 1)
        self.assertTrue(report["case_manifest"]["written"])
        self.assertEqual(len(rows), report["fuzz_case_count"])
        self.assertIn("map_warp", fuzz_types)
        self.assertIn("map_object_event", fuzz_types)
        self.assertIn("positioned_state_dynamic_planned", proof_levels)
        self.assertIn("static_expectation", proof_levels)
        self.assertIn("materialization_request", report["fuzz_cases"][0])
        self.assertIn(
            "trace-instructions",
            "\n".join(report["fuzz_cases"][0]["materialization_request"]["commands"]),
        )
        self.assertIn("contains=warp_event", expectations)
        self.assertIn("contains=object_event", expectations)
        self.assertIn("not-contains=__DEBUGGER_FORBIDDEN_SENTINEL__", expectations)
        self.assertIn("tools.debugger expect --source-file maps/NewBarkTown.asm", commands)
        self.assertIn("tools.debugger content-scenarios", commands)
        self.assertIn("tools.debugger content-state", commands)

    def test_fuzz_turns_ready_instruction_trace_into_dynamic_taint_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "instruction_trace.jsonl").write_text(
                json.dumps({"seq": 1, "bank": 1, "pc": 0x4000, "opcode": 0xEA, "operand": [0x41, 0xD1]}) + "\n",
                encoding="utf-8",
            )
            (root / "instruction_trace_report.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_instruction_trace",
                        "valid": True,
                        "trace_output": {"path": "instruction_trace.jsonl", "written": True},
                        "execution_validation": {
                            "ready_for_dynamic_taint": True,
                            "hit_count": 1,
                            "watch_symbols": ["wCurDamage"],
                        },
                        "dynamic_taint_sources": {"source_regs": ["a=move_power"]},
                    }
                ),
                encoding="utf-8",
            )

            report = build_fuzz_plan(
                reports=("instruction_trace_report.json",),
                max_cases=4,
                root=root,
            )

        commands = "\n".join(report["commands"])
        case = next(item for item in report["fuzz_cases"] if item["fuzz_type"] == "dynamic_taint_handoff")

        self.assertTrue(report["valid"])
        self.assertEqual(report["dynamic_taint_handoff_count"], 1)
        self.assertGreaterEqual(report["dynamic_campaign_count"], 1)
        self.assertIn("instruction_trace", {campaign["surface"] for campaign in report["campaigns"]})
        self.assertEqual(case["proof_level"], "dynamic_trace")
        self.assertEqual(case["source_report"], "instruction_trace_report.json")
        self.assertEqual(case["sink_symbols"], ["wCurDamage"])
        self.assertIn("python -m tools.debugger dynamic-taint --report instruction_trace_report.json", commands)

    def test_fuzz_keeps_map_report_surfaces_content_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "maps" / "NewBarkTown.asm").write_text(
                "NewBarkTown_MapEvents:\n\tdef_warp_events\n\twarp_event 1, 1, ROUTE_29, 1\n",
                encoding="utf-8",
            )
            trace_index = root / "trace_index.json"
            trace_index.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_trace_index",
                        "valid": True,
                        "query": {
                            "active": True,
                            "source_files": ["maps/NewBarkTown.asm"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            impact = root / "impact.json"
            impact.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_impact_report",
                        "valid": True,
                        "items": [
                            {
                                "type": "coverage_gap",
                                "title": "Uncovered source_file: maps/NewBarkTown.asm",
                                "severity": 40,
                                "confidence": 0.7,
                                "evidence": [],
                                "next_actions": [],
                                "impact_score": 70,
                                "related_files": [
                                    "maps/NewBarkTown.asm",
                                    "tools/audit/check_pic_bank_pressure.py",
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_fuzz_plan(
                reports=("trace_index.json", "impact.json"),
                changed_files=("maps/NewBarkTown.asm",),
                max_cases=4,
                root=root,
            )

        self.assertEqual(report["surfaces"], ["content_static"])
        self.assertEqual({campaign["surface"] for campaign in report["campaigns"]}, {"content_static"})
        self.assertEqual(report["dynamic_campaign_count"], 1)
        self.assertIn("positioned_state_dynamic_planned", {campaign["proof_level"] for campaign in report["campaigns"]})
        self.assertIn("materialization_request", report["fuzz_cases"][0])
        self.assertIn("tools.debugger content-state", "\n".join(report["commands"]))
        self.assertIn("tools.debugger replay --report .local\\tmp\\debugger_content_state_", "\n".join(report["commands"]))

    def test_fuzz_routes_damage_to_dynamic_campaign(self) -> None:
        report = build_fuzz_plan(
            symbols=("wCurDamage",),
            changed_files=("engine/battle/effect_commands.asm",),
            max_cases=4,
            seed=5,
        )
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertIn("damage", report["surfaces"])
        self.assertEqual(report["dynamic_campaign_count"], 1)
        self.assertIn("dynamic_counterexample", {case["fuzz_type"] for case in report["fuzz_cases"]})
        self.assertIn("tools.damage_debugger.fuzz", commands)

    def test_cli_fuzz_writes_json_and_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "maps" / "NewBarkTown.asm").write_text(
                "NewBarkTown_MapEvents:\n\twarp_event 1, 1, ROUTE_29, 1\n",
                encoding="utf-8",
            )
            out = root / "fuzz.json"
            cases = root / "cases.jsonl"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "fuzz",
                        "--changed-file",
                        str(root / "maps" / "NewBarkTown.asm"),
                        "--out-cases",
                        str(cases),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))
            rows = [
                json.loads(line)
                for line in cases.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_fuzz_plan")
        self.assertTrue(rows)
