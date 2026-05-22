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


def _backend_result(backend: str, *, vram0: str = "aaa", screen: str = "sss") -> dict[str, object]:
    return {
        "backend": backend,
        "status": "runtime_observed",
        "proof_status": "runtime_observed",
        "snapshot": {
            "regions": [
                {"name": "vram0", "sha256": vram0, "bank_read": "exact"},
                {"name": "oam", "sha256": "ooo", "bank_read": "unbanked"},
            ],
            "screen_frame": {"sha256": screen},
        },
    }


def _conformance_row(backend: str, status: str = "pass") -> dict[str, object]:
    return {
        "kind": crossemu.CONFORMANCE_KIND,
        "schema_version": crossemu.SCHEMA_VERSION,
        "backend": backend,
        "status": status,
        "suite": "unit",
        "rom": "unit.gb",
        "rom_sha256": "a" * 64,
        "command": "python -m tools.debugger crossemu conformance unit",
        "observed_at": "2026-05-22T00:00:00Z",
        "proof_status": "runtime_observed",
    }


def _run_report(*backend_results: dict[str, object]) -> dict[str, object]:
    return {
        "kind": "unified_debugger_crossemu_run",
        "schema_version": crossemu.SCHEMA_VERSION,
        "backend_results": list(backend_results),
    }


class CrossemuPreflightTests(unittest.TestCase):
    def test_crossemu_preflight_reports_available_backends(self) -> None:
        report = crossemu.build_preflight_report(
            backends=("pyboy", "sameboy", "gambatte"),
            conformance_rows=(_conformance_row("sameboy"),),
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
            conformance_rows=(_conformance_row("sameboy", "fail"),),
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

    def test_conformance_store_rejects_arbitrary_pass_row(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = root / "crossemu_conformance.jsonl"
            store.write_text(
                json.dumps({"backend": "sameboy", "status": "pass"}) + "\n",
                encoding="utf-8",
            )
            report = crossemu.build_preflight_report(
                backends=("pyboy", "sameboy"),
                conformance_store=store,
                root=root,
                module_finder=_module_finder("pyboy"),
                command_finder=_command_finder("sameboy-headless"),
            )

        by_name = {entry["name"]: entry for entry in report["backends"]}
        self.assertFalse(report["valid"])
        self.assertFalse(report["ready_for_cross_backend_diff"])
        self.assertFalse(by_name["sameboy"]["trusted_for_differential"])
        self.assertIn("kind must be", "\n".join(report["errors"]))

    def test_conformance_store_accepts_schema_row(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = root / "crossemu_conformance.jsonl"
            store.write_text(json.dumps(_conformance_row("sameboy")) + "\n", encoding="utf-8")
            report = crossemu.build_preflight_report(
                backends=("pyboy", "sameboy"),
                conformance_store=store,
                root=root,
                module_finder=_module_finder("pyboy"),
                command_finder=_command_finder("sameboy-headless"),
            )

        by_name = {entry["name"]: entry for entry in report["backends"]}
        self.assertTrue(report["valid"])
        self.assertTrue(report["ready_for_cross_backend_diff"])
        self.assertTrue(by_name["sameboy"]["trusted_for_differential"])

    def test_conformance_pass_row_requires_runtime_observed_proof(self) -> None:
        row = _conformance_row("sameboy")
        row["proof_status"] = "failed"
        errors = crossemu.validate_conformance_row(row, source="unit")

        self.assertIn("unit: pass rows must have proof_status='runtime_observed'", errors)

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

    def test_cli_preflight_json_out_writes_file_without_stdout(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "preflight.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = crossemu.main(
                    ["preflight", "--backends", "pyboy", "--json-out", str(out)]
                )

            self.assertEqual(code, 0)
            self.assertEqual(stdout.getvalue(), "")
            payload = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(payload["kind"], "unified_debugger_crossemu_preflight")

    def test_cli_run_json_out_writes_error_report(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "run.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = crossemu.main(
                    [
                        "run",
                        "--backends",
                        "sameboy",
                        "--save-state",
                        "missing.state",
                        "--json-out",
                        str(out),
                    ]
                )

            self.assertEqual(code, 1)
            self.assertEqual(stdout.getvalue(), "")
            payload = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(payload["kind"], "unified_debugger_crossemu_run")
        self.assertFalse(payload["valid"])
        self.assertIn("pending adapters: sameboy", "\n".join(payload["errors"]))

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

    def test_snapshot_diff_reports_region_and_screen_divergence(self) -> None:
        diff = crossemu.diff_backend_snapshots(
            (
                _backend_result("pyboy", vram0="aaa", screen="sss"),
                _backend_result("sameboy", vram0="bbb", screen="ttt"),
            )
        )

        self.assertTrue(diff["divergent"])
        self.assertEqual(diff["status"], "diverged")
        comparison = diff["comparisons"][0]
        self.assertEqual(comparison["left_backend"], "pyboy")
        self.assertEqual(comparison["right_backend"], "sameboy")
        self.assertEqual(comparison["region_differences"][0]["kind"], "region_sha256_mismatch")
        self.assertEqual(comparison["screen_difference"]["kind"], "screen_frame_sha256_mismatch")

    def test_snapshot_diff_single_backend_stays_planned(self) -> None:
        diff = crossemu.diff_backend_snapshots((_backend_result("pyboy"),))

        self.assertFalse(diff["divergent"])
        self.assertEqual(diff["status"], "not_enough_runtime_backends")
        self.assertEqual(diff["proof_status"], "planned_only")

    def test_report_diff_cli_compares_saved_run_reports(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            left = root / "pyboy.json"
            right = root / "sameboy.json"
            left.write_text(json.dumps(_run_report(_backend_result("pyboy"))), encoding="utf-8")
            right.write_text(
                json.dumps(_run_report(_backend_result("sameboy", vram0="bbb"))),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = crossemu.main(
                    ["diff", "--reports", str(left), str(right), "--json"]
                )

        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["kind"], "unified_debugger_crossemu_report_diff")
        self.assertTrue(payload["valid"])
        self.assertTrue(payload["divergent"])
        self.assertEqual(payload["snapshot_diff"]["comparison_count"], 1)

    def test_report_diff_requires_two_runtime_snapshots(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            left = root / "pyboy.json"
            left.write_text(json.dumps(_run_report(_backend_result("pyboy"))), encoding="utf-8")
            report = crossemu.build_report_diff_report(reports=(str(left),))

        self.assertFalse(report["valid"])
        self.assertIn("need at least two runtime backend snapshots", report["blocking_reasons"])

    def test_report_diff_rejects_non_run_report(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = root / "preflight.json"
            bad.write_text(json.dumps({"kind": "unified_debugger_crossemu_preflight"}), encoding="utf-8")
            report = crossemu.build_report_diff_report(reports=(str(bad),))

        self.assertFalse(report["valid"])
        self.assertIn("expected crossemu run report", "\n".join(report["errors"]))


if __name__ == "__main__":
    unittest.main()
