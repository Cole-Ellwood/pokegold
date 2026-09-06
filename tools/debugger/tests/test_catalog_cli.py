from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.__main__ import main as boss_ai_main


class CatalogCliTests(unittest.TestCase):
    def test_main_help_lists_standalone_commands(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout), self.assertRaises(SystemExit) as caught:
            debugger_main(["--help"])
        self.assertEqual(caught.exception.code, 0)
        for command in (
            "auto-watch", "bisect", "clobbers", "consequence", "crossemu", "dap",
            "heatmap", "hypothesis", "navigate", "operator-status", "pack", "probe",
            "save-state-lab", "selftest", "session-start", "speedup-report", "stat-at",
            "tdb", "type-matchup", "vram-diff", "vram-snapshot", "when-wrote",
        ):
            with self.subTest(command=command):
                self.assertIn(command, stdout.getvalue())

    def test_nested_command_preserves_output_and_read_only_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "memory.bin"
            state.write_bytes(bytes(0x10000))
            argv = ["save-state-lab", "inspect", str(state), "--json"]
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(debugger_main(argv), 0)
            report = json.loads(stdout.getvalue())
            self.assertTrue(report["valid"])
            self.assertEqual(report["kind"], "unified_debugger_save_state_inspect")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(debugger_main(["--read-only", *argv]), 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("read-only mode refuses debugger-v2:save-state-lab", stderr.getvalue())

    def test_read_only_refuses_standalone_output_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "heatmap.json"
            with redirect_stderr(io.StringIO()):
                code = debugger_main(["--read-only", "heatmap", "--out", str(out)])
            self.assertEqual(code, 2)
            self.assertFalse(out.exists())

    def test_cli_audit_strict_fails_until_whole_rom_tier_is_ready(self) -> None:
        with redirect_stdout(io.StringIO()):
            code = debugger_main(["audit", "--strict"])

        self.assertEqual(code, 1)

    def test_standalone_leading_separator_remains_accepted(self) -> None:
        outputs = []
        for prefix in (["type-matchup"], ["type-matchup", "--"]):
            output = io.StringIO()
            with redirect_stdout(output):
                code = debugger_main([*prefix, "--species", "MAREEP", "--json"])
            self.assertEqual(code, 0)
            outputs.append(json.loads(output.getvalue()))
        self.assertEqual(outputs[0], outputs[1])

    def test_read_only_help_preserves_existing_validation_order(self) -> None:
        with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as caught:
            debugger_main(["--read-only", "rom-index", "--help"])
        self.assertEqual(caught.exception.code, 0)
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(io.StringIO()):
            self.assertEqual(debugger_main(["--read-only", "heatmap", "--help"]), 2)
        self.assertEqual(output.getvalue(), "")

    def test_cli_writes_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "triage.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "triage",
                        "--symptom",
                        "damage spike",
                        "--json-out",
                        str(path),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "unified_debugger_triage")
            self.assertTrue(data["commands"])

    def test_global_read_only_allows_safe_debugger_command(self) -> None:
        with redirect_stdout(io.StringIO()):
            code = debugger_main(["--read-only", "inventory"])

        self.assertEqual(code, 0)

    def test_global_read_only_refuses_debugger_writes_before_dispatch(self) -> None:
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, redirect_stderr(stderr):
            out = Path(tmp) / "rom_index.json"
            code = debugger_main(["--read-only", "rom-index", "--json-out", str(out)])

            self.assertFalse(out.exists())

        self.assertEqual(code, 2)
        self.assertIn("read-only mode refuses debugger:rom-index", stderr.getvalue())

    def test_global_read_only_allows_safe_boss_ai_command(self) -> None:
        with redirect_stdout(io.StringIO()):
            code = boss_ai_main(["--read-only", "universe"])

        self.assertEqual(code, 1)

    def test_global_read_only_refuses_boss_ai_run_suite_before_dispatch(self) -> None:
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, redirect_stderr(stderr):
            runs_dir = Path(tmp) / "runs"
            with self.assertRaises(SystemExit) as caught:
                boss_ai_main(
                    ["--read-only", "run-suite", "--profile", "changed-ai", "--runs-dir", str(runs_dir)]
                )

            self.assertFalse(runs_dir.exists())

        self.assertEqual(caught.exception.code, 2)
        self.assertIn("read-only mode refuses boss-ai:run-suite", stderr.getvalue())
