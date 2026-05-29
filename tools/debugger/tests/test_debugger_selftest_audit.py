from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from tools.audit.check_debugger_selftest import (
    build_audit_report,
    format_audit_report,
    main,
)
from tools.debugger.selftest import CheckResult, SelftestReport


class DebuggerSelftestAuditTests(unittest.TestCase):
    def test_build_audit_report_passes_through_component_results(self) -> None:
        selftest = SelftestReport(
            ok=True,
            results=[
                CheckResult(
                    component="capability_audit",
                    ok=True,
                    next_command="python -m tools.debugger audit",
                    detail="ready",
                )
            ],
        )
        report = build_audit_report(selftest)

        self.assertTrue(report["passed"])
        self.assertEqual(report["kind"], "debugger_selftest_audit")
        self.assertEqual(report["component_count"], 1)
        self.assertEqual(report["failed_component_count"], 0)
        self.assertEqual(report["failed_components"], [])
        self.assertEqual(report["components"][0]["component"], "capability_audit")

    def test_failed_report_names_next_command(self) -> None:
        selftest = SelftestReport(
            ok=False,
            results=[
                CheckResult(
                    component="bisect",
                    ok=False,
                    next_command="python -m tools.debugger selftest --component bisect",
                    error="synthetic failure",
                )
            ],
        )
        report = build_audit_report(selftest)
        text = format_audit_report(report)

        self.assertFalse(report["passed"])
        self.assertEqual(report["failed_component_count"], 1)
        self.assertIn("Debugger selftest audit FAIL", text)
        self.assertIn("bisect", text)
        self.assertIn("next command", text)

    def test_main_json_output_is_machine_readable(self) -> None:
        selftest = SelftestReport(
            ok=True,
            results=[
                CheckResult(
                    component="inventory",
                    ok=True,
                    next_command="python -m tools.debugger inventory",
                    detail="ok",
                )
            ],
        )
        stdout = io.StringIO()
        with patch(
            "tools.audit.check_debugger_selftest.run_selftest",
            return_value=selftest,
        ), redirect_stdout(stdout):
            code = main(["--json"])

        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["passed"])
        self.assertEqual(payload["components"][0]["component"], "inventory")


if __name__ == "__main__":
    unittest.main()
