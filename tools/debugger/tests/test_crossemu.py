from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

from tools.debugger import crossemu


def _module_finder(*available: str):
    names = set(available)

    def inner(name: str) -> object | None:
        return object() if name in names else None

    return inner


def _command_finder(*available: str):
    names = set(available)

    def inner(name: str) -> str | None:
        return f"C:/tools/{name}.exe" if name in names else None

    return inner


class CrossemuPreflightTests(unittest.TestCase):
    def test_crossemu_preflight_reports_available_backends(self) -> None:
        report = crossemu.build_preflight_report(
            backends=("pyboy", "sameboy", "gambatte"),
            conformance_rows=({"backend": "sameboy", "status": "pass"},),
            module_finder=_module_finder("pyboy"),
            command_finder=_command_finder("sameboy-headless"),
        )

        self.assertTrue(report["valid"])
        by_name = {entry["name"]: entry for entry in report["backends"]}
        self.assertTrue(by_name["pyboy"]["available"])
        self.assertEqual(by_name["pyboy"]["availability_proof"], "python_module:pyboy")
        self.assertTrue(by_name["sameboy"]["available"])
        self.assertEqual(by_name["sameboy"]["availability_proof"], "command:sameboy-headless")
        self.assertFalse(by_name["gambatte"]["available"])
        self.assertTrue(report["ready_for_pyboy_run"])
        self.assertTrue(report["ready_for_cross_backend_diff"])

    def test_crossemu_backend_conformance_gates_results(self) -> None:
        report = crossemu.build_preflight_report(
            backends=("pyboy", "sameboy"),
            conformance_rows=({"backend": "sameboy", "status": "fail"},),
            module_finder=_module_finder("pyboy"),
            command_finder=_command_finder("sameboy-headless"),
        )

        by_name = {entry["name"]: entry for entry in report["backends"]}
        self.assertTrue(by_name["sameboy"]["available"])
        self.assertEqual(by_name["sameboy"]["conformance_status"], "fail")
        self.assertFalse(by_name["sameboy"]["trusted_for_differential"])
        self.assertFalse(report["ready_for_cross_backend_diff"])
        self.assertIn(
            "no conformance-passing cross-emulator backend is installed",
            report["blocking_reasons"],
        )

    def test_unknown_backend_fails_closed(self) -> None:
        report = crossemu.build_preflight_report(
            backends=("pyboy", "madeup"),
            conformance_rows=(),
            module_finder=_module_finder("pyboy"),
            command_finder=_command_finder(),
        )

        self.assertFalse(report["valid"])
        self.assertIn("unknown backend 'madeup'", report["errors"])

    def test_install_docs_lists_missing_backend_recipe(self) -> None:
        report = crossemu.build_install_docs_report(
            backends=("pyboy", "vba-m"),
            module_finder=_module_finder("pyboy"),
            command_finder=_command_finder(),
        )

        self.assertTrue(report["valid"])
        self.assertEqual([recipe["name"] for recipe in report["recipes"]], ["vba-m"])
        self.assertIn("VisualBoyAdvance-M", report["recipes"][0]["display_name"])
        self.assertIn("preflight --backends vba-m", report["recipes"][0]["verify_command"])

    def test_cli_preflight_json(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = crossemu.main(["preflight", "--backends", "pyboy", "--json"])

        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["kind"], "unified_debugger_crossemu_preflight")
        self.assertEqual(payload["requested_backends"], ["pyboy"])
        self.assertEqual(payload["backends"][0]["name"], "pyboy")

    def test_cli_install_docs_text(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = crossemu.main(["install-docs", "--backends", "sameboy", "--all"])

        self.assertEqual(code, 0)
        text = stdout.getvalue()
        self.assertIn("crossemu install-docs: PASS", text)
        self.assertIn("sameboy", text)


if __name__ == "__main__":
    unittest.main()
