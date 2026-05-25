from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.workflow import build_gate_plan, command_is_runnable


class GatePlanTests(unittest.TestCase):
    def test_gate_plan_orders_runnable_debugger_commands(self) -> None:
        report = build_gate_plan(
            changed_files=("engine/battle/late_gen_held_items.asm",),
        )
        commands = [step["command"] for step in report["steps"]]

        self.assertFalse(report["executed"])
        self.assertIn("python -m tools.damage_debugger.clobber_smoke", commands)
        self.assertIn("python tools\\audit\\check_cross_bank_call.py", commands)
        self.assertEqual(report["steps"][0]["priority"], 10)

    def test_gate_marks_placeholder_commands_not_runnable(self) -> None:
        self.assertFalse(command_is_runnable("python -m tool <scenario>"))
        self.assertTrue(command_is_runnable("python tools\\audit\\check_release_smoke.py"))

    def test_cli_gate_plan_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "gate.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "gate",
                        "--symptom",
                        "boss ai selector issue",
                        "--json-out",
                        str(out),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "unified_debugger_gate_plan")
            self.assertFalse(data["executed"])
            self.assertTrue(data["steps"])
