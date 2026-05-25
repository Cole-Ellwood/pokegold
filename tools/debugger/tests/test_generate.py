from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.fuzz import build_fuzz_plan
from tools.debugger.generate import build_generation_plan
from tools.debugger.next_steps import NEXT_STEP_ROWS, build_next_step


class GenerationTests(unittest.TestCase):
    def test_generate_routes_damage_and_writes_seed_scenarios(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_file = root / "generated.jsonl"
            report = build_generation_plan(
                symbols=("wCurDamage",),
                changed_files=("engine/battle/effect_commands.asm",),
                out_scenarios=str(seed_file),
                max_cases=4,
                seed=7,
                root=root,
            )

            rows = [
                json.loads(line)
                for line in seed_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertIn("damage", report["surfaces"])
        self.assertIn("damage_fuzz", {item["id"] for item in report["generators"]})
        self.assertTrue(report["seed_manifest"]["written"])
        self.assertEqual(report["seed_manifest"]["record_count"], 4)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["family"], "damage")
        self.assertIn("tools.damage_debugger.fuzz", commands)

    def test_generate_routes_boss_ai_to_generators(self) -> None:
        report = build_generation_plan(
            changed_files=("engine/battle/ai/boss_policy_move.asm",),
            symbols=("BossAI_SelectMove",),
            max_cases=8,
            seed=3,
        )
        commands = "\n".join(report["commands"])
        materialization = "\n".join(
            step["command"] for step in report["materialization_steps"]
        )

        self.assertTrue(report["valid"])
        self.assertIn("boss_ai", report["surfaces"])
        self.assertIn("boss_ai_generated_policy", {item["id"] for item in report["generators"]})
        self.assertIn("tools.boss_ai_debugger generate", commands)
        self.assertIn("rom-score-materialize", materialization)
        self.assertIn(".local\\tmp\\debugger_boss_ai_generated.jsonl", materialization)

    def test_generate_uses_embedded_next_step_instead_of_nested_report_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            investigation = root / "investigate.json"
            investigation.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_investigation_run",
                        "valid": True,
                        "symptom": "boss selected wrong switch",
                        "symptom_only_next_step": build_next_step(symptom="boss selected wrong switch"),
                        "reports": [
                            {"id": "09_fuzz", "kind": "unified_debugger_fuzz_plan", "surface": "ROM banking / ABI"},
                            {"id": "06_explain", "kind": "unified_debugger_causal_explanation", "surface": "Battle damage"},
                        ],
                        "top_impact": [
                            {
                                "type": "fuzz_campaign",
                                "title": "Fuzz campaign: fuzz_banking_abi_static_watch",
                                "severity": 55,
                                "confidence": 0.62,
                                "evidence": [],
                                "next_actions": [],
                                "impact_score": 100,
                                "surface_id": "banking_abi",
                            },
                            {
                                "type": "causal_path",
                                "title": "Causal path: Battle damage",
                                "severity": 50,
                                "confidence": 0.62,
                                "evidence": [],
                                "next_actions": [],
                                "impact_score": 90,
                                "surface_id": "battle_damage",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_generation_plan(
                reports=("investigate.json",),
                max_cases=8,
                seed=3,
                root=root,
            )
            fuzz = build_fuzz_plan(
                reports=("investigate.json",),
                max_cases=8,
                seed=3,
                root=root,
            )

        commands = "\n".join(report["commands"])
        materialization = "\n".join(step["command"] for step in report["materialization_steps"])
        fuzz_commands = "\n".join(fuzz["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["surfaces"], ["boss_ai"])
        self.assertEqual(report["effective_families"], ["switch_sack"])
        self.assertIn("boss_ai_generated_policy", {item["id"] for item in report["generators"]})
        self.assertIn("generate --family switch_sack", commands)
        self.assertIn("rom-switch-materialize --scenarios .local\\tmp\\debugger_boss_ai_generated.jsonl --limit 20 --fail-on-mismatch", materialization)
        self.assertNotIn("tools.damage_debugger.fuzz", commands)
        self.assertNotIn("check_farcall_a_clobber", commands)
        self.assertEqual(fuzz["surfaces"], ["boss_ai"])
        self.assertEqual({campaign["surface"] for campaign in fuzz["campaigns"]}, {"boss_ai"})
        self.assertIn("generate --family switch_sack", fuzz_commands)
        self.assertNotIn("tools.damage_debugger.fuzz", fuzz_commands)
        self.assertNotIn("hROMBank", fuzz_commands)

    def test_generate_routes_content_to_static_expectation_seeds(self) -> None:
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
                        "\tdef_bg_events",
                        "\tbg_event  4,  5, BGEVENT_READ, NewBarkTownSign",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            seed_file = root / "generated.jsonl"
            report = build_generation_plan(
                changed_files=("maps/NewBarkTown.asm",),
                out_scenarios="generated.jsonl",
                max_cases=3,
                seed=2,
                root=root,
            )
            rows = [
                json.loads(line)
                for line in seed_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        commands = "\n".join(report["commands"])
        materialization = "\n".join(
            step["command"] for step in report["materialization_steps"]
        )

        self.assertTrue(report["valid"])
        self.assertIn("content_static", report["surfaces"])
        self.assertIn("content_static_seed_manifest", {item["id"] for item in report["generators"]})
        self.assertIn("positioned-state-planned", {item["status"] for item in report["generators"]})
        self.assertIn("map_warp", {row.get("scenario_type") for row in rows})
        self.assertIn("positioned_state_dynamic_planned", {row.get("proof_level") for row in rows})
        self.assertIn("behavioral_probes", rows[0])
        self.assertIn("runtime_targets", rows[0])
        self.assertIn("materialization_request", rows[0])
        self.assertIn(
            "content_replay_route",
            {probe["id"] for probe in rows[0]["behavioral_probes"]},
        )
        self.assertIn(
            "content_runtime_trace_route",
            {probe["id"] for probe in rows[0]["behavioral_probes"]},
        )
        self.assertIn(
            "content_state_execution_route",
            {probe["id"] for probe in rows[0]["behavioral_probes"]},
        )
        self.assertIn(
            "content_positioned_replay_route",
            {probe["id"] for probe in rows[0]["behavioral_probes"]},
        )
        self.assertIn(
            "content_positioned_instruction_trace_route",
            {probe["id"] for probe in rows[0]["behavioral_probes"]},
        )
        self.assertIn("tools.debugger expect --source-file", commands)
        self.assertIn("tools.debugger content-scenarios", commands)
        self.assertIn("tools.debugger content-state", commands)
        self.assertIn("tools.debugger trace-instructions --report .local\\tmp\\debugger_content_state_debugger_generated_content_static_2_0000.json", commands)
        self.assertIn("--execute --json-out .local\\tmp\\debugger_content_state_debugger_generated_content_static_2_0000.json", commands)
        self.assertIn("--scenario generated.jsonl --scenario-id debugger_generated_content_static_2_0000", commands)
        self.assertIn("--symbol WarpCheck", commands)
        self.assertIn("not-contains=<forbidden_text>", commands)
        self.assertIn("replay --report .local\\tmp\\debugger_content_state_<id>.json", materialization)

    def test_generate_hands_ready_instruction_trace_to_dynamic_taint(self) -> None:
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

            report = build_generation_plan(
                reports=("instruction_trace_report.json",),
                max_cases=2,
                root=root,
            )

        commands = "\n".join(report["commands"])
        handoff = report["dynamic_taint_handoffs"][0]

        self.assertTrue(report["valid"])
        self.assertEqual(report["dynamic_taint_handoff_count"], 1)
        self.assertEqual(handoff["source_report"], "instruction_trace_report.json")
        self.assertEqual(handoff["traces"], ["instruction_trace.jsonl"])
        self.assertEqual(handoff["sink_symbols"], ["wCurDamage"])
        self.assertEqual(handoff["source_regs"], ["a=move_power"])
        self.assertIn("python -m tools.debugger dynamic-taint --report instruction_trace_report.json", commands)
        self.assertIn("dynamic-taint", {item["source"] for item in report["counterexamples"]})

    def test_cli_generate_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "generate.json"
            seed_file = Path(tmp) / "generated.jsonl"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "generate",
                        "--symbol",
                        "wCurDamage",
                        "--out-scenarios",
                        str(seed_file),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))
            rows = [
                json.loads(line)
                for line in seed_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_generation_plan")
        self.assertIn("damage", data["surfaces"])
        self.assertTrue(rows)
