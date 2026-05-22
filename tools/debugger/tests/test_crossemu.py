from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

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


class FakeMemory:
    def __getitem__(self, key: object) -> int:
        if isinstance(key, tuple):
            bank, address = key
            return (int(bank) * 31 + int(address)) & 0xFF
        if int(key) == 0xFF70:
            return 3
        return int(key) & 0xFF


class FakeScreen:
    def ndarray(self) -> bytes:
        return bytes(range(12))


class FakePyBoy:
    def __init__(self) -> None:
        self.memory = FakeMemory()
        self.screen = FakeScreen()
        self.loaded = False
        self.ticks = 0
        self.buttons: list[tuple[str, int]] = []
        self.stopped = False

    def load_state(self, _fh: object) -> None:
        self.loaded = True

    def button(self, name: str, delay: int = 1) -> None:
        self.buttons.append((name, delay))

    def tick(self, _count: int, _render: bool, _sound: bool) -> bool:
        self.ticks += 1
        return True

    def stop(self, save: bool = False) -> None:
        self.stopped = True


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

    def test_pyboy_run_loads_state_replays_inputs_and_captures_snapshot(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "unit.gb").write_bytes(b"rom")
            (root / "unit.state").write_bytes(b"state")
            (root / "unit.inputs").write_text("A 2\nWAIT 1\nSTART\n", encoding="utf-8")
            fake = FakePyBoy()

            report = crossemu.build_run_report(
                backends=("pyboy",),
                rom_path="unit.gb",
                save_state="unit.state",
                frames=4,
                input_logs=("unit.inputs",),
                root=root,
                module_finder=_module_finder("pyboy"),
                command_finder=_command_finder(),
                pyboy_factory=lambda _rom: fake,
            )

        self.assertTrue(report["valid"])
        self.assertTrue(report["executed"])
        self.assertEqual(report["proof_status"], "runtime_observed")
        self.assertTrue(fake.loaded)
        self.assertTrue(fake.stopped)
        self.assertEqual(fake.ticks, 4)
        self.assertIn(("a", 2), fake.buttons)
        self.assertIn(("start", 1), fake.buttons)
        result = report["backend_results"][0]
        self.assertEqual(result["backend"], "pyboy")
        snapshot = result["snapshot"]
        region_names = {region["name"] for region in snapshot["regions"]}
        self.assertIn("vram0", region_names)
        self.assertIn("vram1", region_names)
        self.assertIn("wramx", region_names)
        self.assertIn("oam", region_names)
        self.assertEqual(snapshot["screen_frame_count"], 1)

    def test_run_refuses_non_pyboy_backend_until_adapter_exists(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "unit.gb").write_bytes(b"rom")
            (root / "unit.state").write_bytes(b"state")
            report = crossemu.build_run_report(
                backends=("sameboy",),
                rom_path="unit.gb",
                save_state="unit.state",
                root=root,
                module_finder=_module_finder("pyboy"),
                command_finder=_command_finder("sameboy"),
            )

        self.assertFalse(report["valid"])
        self.assertIn("pending adapters: sameboy", "\n".join(report["errors"]))
        self.assertEqual(report["backend_results"][0]["status"], "planned_only")


if __name__ == "__main__":
    unittest.main()
