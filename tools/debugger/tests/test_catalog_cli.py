from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main


class CatalogCliTests(unittest.TestCase):
    def test_cli_audit_strict_passes_when_whole_rom_goal_is_done(self) -> None:
        with redirect_stdout(io.StringIO()):
            code = debugger_main(["audit", "--strict"])

        self.assertEqual(code, 0)

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
