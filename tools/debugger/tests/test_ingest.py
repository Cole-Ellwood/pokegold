from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.ingest import ingest_artifacts


class IngestTests(unittest.TestCase):
    def test_ingest_manifest_accepts_core_artifact_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = root / "test.gbc"
            rom_bytes = bytearray(0x8000)
            rom_bytes[0x134:0x13C] = b"DBGTEST\0"
            rom.write_bytes(rom_bytes)
            symbols = root / "test.sym"
            symbols.write_text(
                "; generated\n00:0000 NULL\n01:4000 ExampleLabel\n",
                encoding="utf-8",
            )
            trace = root / "trace.txt"
            trace.write_text(
                "trace_rom_sha256=ABC\nchosen=TACKLE\nmove_scores=1,2,3,4\n",
                encoding="utf-8",
            )
            save_state = root / "state.sgm"
            save_state.write_bytes(b"opaque-state")
            scenario = root / "scenarios.jsonl"
            scenario.write_text(
                json.dumps(
                    {
                        "id": "scenario_1",
                        "family": "test_family",
                        "moves": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            changed = root / "engine" / "battle" / "effect_commands.asm"
            changed.parent.mkdir(parents=True)
            changed.write_text("BattleCommand_Test:\n\tret\n", encoding="utf-8")

            report = ingest_artifacts(
                roms=("test.gbc",),
                symbols=("test.sym",),
                traces=("trace.txt",),
                save_states=("state.sgm",),
                scenarios=("scenarios.jsonl",),
                changed_files=("engine/battle/effect_commands.asm",),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["artifact_count"], 6)
        by_kind = {artifact["kind"]: artifact for artifact in report["artifacts"]}
        self.assertEqual(by_kind["rom"]["metadata"]["title"], "DBGTEST")
        self.assertEqual(by_kind["symbols"]["metadata"]["label_count"], 2)
        self.assertEqual(by_kind["scenario"]["metadata"]["record_count"], 1)
        self.assertIn(
            "damage_chain",
            by_kind["source_change"]["metadata"]["triage_match_ids"],
        )

    def test_ingest_manifest_reports_invalid_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenario = root / "bad.jsonl"
            scenario.write_text("{bad json}\n", encoding="utf-8")

            report = ingest_artifacts(scenarios=("bad.jsonl",), root=root)

        self.assertFalse(report["valid"])
        self.assertEqual(report["error_count"], 1)

    def test_ingest_manifest_accepts_json_trace_without_key_value_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "events": [
                            {
                                "full_symbol": "BattleCommand_Test",
                                "source_file": "engine/battle/effect_commands.asm",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            report = ingest_artifacts(traces=("trace.json",), root=root)

        artifact = report["artifacts"][0]

        self.assertTrue(report["valid"])
        self.assertEqual(artifact["metadata"]["format"], "json")
        self.assertIn("BattleCommand_Test", artifact["metadata"]["symbol_sample"])
        self.assertFalse(artifact["warnings"])

    def test_cli_ingest_writes_json_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenario = root / "scenario.json"
            scenario.write_text(
                json.dumps({"id": "one", "family": "cli"}),
                encoding="utf-8",
            )
            out = root / "manifest.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "ingest",
                        "--scenario",
                        str(scenario),
                        "--json-out",
                        str(out),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "unified_debugger_ingest_manifest")
            self.assertTrue(data["valid"])
