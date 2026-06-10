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
    def test_cli_audit_strict_fails_until_whole_rom_tier_is_ready(self) -> None:
        with redirect_stdout(io.StringIO()):
            code = debugger_main(["audit", "--strict"])

        self.assertEqual(code, 1)

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
