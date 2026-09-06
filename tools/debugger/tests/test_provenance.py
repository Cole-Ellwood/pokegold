from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.provenance import build_provenance_report


class ProvenanceTests(unittest.TestCase):
    def test_provenance_maps_symbols_to_source_hits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            symbols = root / "test.sym"
            symbols.write_text(
                "01:4000 BattleCommand_Test\n02:5abc wCurDamage\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tld hl, wCurDamage\n\tret\n",
                encoding="utf-8",
            )

            report = build_provenance_report(
                symbols_path="test.sym",
                symbols=("wCurDamage", "BattleCommand_Test"),
                source_files=("engine/battle.asm",),
                root=root,
            )

        self.assertTrue(report["valid"])
        by_query = {item["query"]: item for item in report["symbols"]}
        self.assertEqual(by_query["wCurDamage"]["address"]["bank_address"], "02:5ABC")
        self.assertGreaterEqual(by_query["wCurDamage"]["source_hit_count"], 2)
        self.assertEqual(by_query["wCurDamage"]["source_hits"][0]["kind"], "definition")
        self.assertEqual(report["source_files"][0]["symbols_matched_count"], 1)

    def test_cli_provenance_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            symbols = root / "test.sym"
            symbols.write_text("01:4000 LabelOne\n", encoding="utf-8")
            out = root / "provenance.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "provenance",
                        "--symbols",
                        str(symbols),
                        "--symbol",
                        "LabelOne",
                        "--json-out",
                        str(out),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "unified_debugger_provenance_report")
            self.assertTrue(data["valid"])


class SourceMappingBuildTests(unittest.TestCase):
    def setUp(self):
        import subprocess
        from unittest.mock import Mock
        from tools.debugger.report_envelope import sha256_file
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "input"
        self.root.mkdir()
        (self.root / "engine").mkdir()
        self.source = self.root / "engine/unit.asm"
        self.source.write_text("Caller:\n\tcall Callee\n\tret\nCallee:\n\tret\n")
        self.symbols = "01:4000 Caller\n01:4100 Callee\n"
        (self.root / "pokegold.sym").write_text(self.symbols)
        rom = bytearray(32768)
        rom[16384:16387] = bytes([0xCD, 0, 0x41])
        (self.root / "pokegold.gbc").write_bytes(rom)
        (self.root / "main_gold.o").write_bytes(b"stale object")
        (self.root / ".local").mkdir()
        (self.root / ".local/cache.txt").write_text("artifact")
        self.candidate = {"source_file": "engine/unit.asm", "source_symbol": "Caller", "source_line": 2,
                          "instruction": "call Callee", "source_sha256": sha256_file(self.source)}
        self.destination = self.root.parent / "mapped"
        self.before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        def build(destination):
            self.assertFalse(list(destination.rglob("*.o")))
            self.assertFalse((destination / ".local").exists())
            (destination / "pokegold.sym").write_text(self.symbols + "01:4000 Caller.__debugger_source_line_2\n")
            return subprocess.CompletedProcess(["unit-build"], 0, "linked", "")
        self.build = Mock(side_effect=build)

    def run_mapping(self, **overrides):
        from tools.debugger.provenance import build_source_mapping_report
        arguments = dict(root=self.root, destination=self.destination, candidate=self.candidate,
                         bank=1, pc=0x4000, build=self.build)
        arguments.update(overrides)
        return build_source_mapping_report(**arguments)

    def assert_reference_unchanged(self):
        self.assertEqual(self.before, {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_label_rebuild_checks_outputs_and_emits_only_address_evidence(self):
        report = self.run_mapping()
        self.assertTrue(report["valid"], report["errors"])
        self.build.assert_called_once_with(self.destination)
        atom, = report["evidence_atoms"]
        self.assertEqual(atom["claim_type"], "provenance.source_mapping")
        self.assertEqual(atom["precision"]["source_line"], 2)
        self.assertEqual(atom["precision"]["pc"], 0x4000)
        self.assertEqual(atom["proof_status"], "mirror_passed")
        self.assertNotIn("diagnosis.root_cause", str(report))
        self.assert_reference_unchanged()

    def test_invalid_basis_rejects_before_copy_or_build(self):
        cases = [{"candidate": {**self.candidate, "source_line": n}} for n in (0, -1, True, None, 99)]
        cases += [{"candidate": {**self.candidate, key: value}} for key, value in (
            ("source_file", "../outside.asm"), ("source_file", "missing.asm"),
            ("source_sha256", "stale"), ("source_sha256", ""),
            ("instruction", "nop"), ("source_symbol", "Other"))]
        cases += [{"bank": n} for n in (-1, 0, 2, True)]
        cases += [{"pc": n} for n in (-1, 0, 0x8000, True)]
        cases += [{"rom_path": "missing.gbc"}, {"symbols_path": "missing.sym"},
                  {"destination": self.root / "nested"}]
        cases += [{"candidate": value} for value in (None, [], "")]
        for key in self.candidate:
            cases.append({"candidate": {name: value for name, value in self.candidate.items() if name != key}})
        for arguments in cases:
            with self.subTest(arguments=arguments):
                with self.assertRaises(ValueError):
                    self.run_mapping(**arguments)
                self.assertFalse(self.destination.exists())
        self.build.assert_not_called()
        self.assert_reference_unchanged()

    def test_farcall_mapping_validates_emitted_target_before_build(self):
        from tools.debugger.report_envelope import sha256_file
        self.source.write_text("Caller:\n\tfarcall Callee\n\tret\nCallee:\n\tret\n")
        self.candidate.update(instruction="farcall Callee", source_sha256=sha256_file(self.source))
        rom = bytearray((self.root / "pokegold.gbc").read_bytes())
        encoded = bytes([0x3E, 1, 0x21, 0, 0x41, 0xCF])
        for index in range(len(encoded)):
            with self.subTest(changed_byte=index):
                rom[16384:16390] = encoded
                rom[16384 + index] ^= 1
                (self.root / "pokegold.gbc").write_bytes(rom)
                with self.assertRaises(ValueError):
                    self.run_mapping()
                self.assertFalse(self.destination.exists())
                self.build.assert_not_called()
        rom[16384:16390] = encoded
        (self.root / "pokegold.gbc").write_bytes(rom)
        self.before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        report = self.run_mapping()
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(report["evidence_atoms"][0]["proof_status"], "mirror_passed")
        self.assert_reference_unchanged()

    def test_existing_destination_is_not_overwritten(self):
        self.destination.mkdir()
        marker = self.destination / "keep.txt"
        marker.write_text("keep")
        with self.assertRaises(FileExistsError):
            self.run_mapping()
        self.assertEqual(list(self.destination.iterdir()), [marker])
        self.assertEqual(marker.read_text(), "keep")
        self.build.assert_not_called()

    def test_failed_or_inconsistent_build_never_emits_mapping(self):
        import subprocess
        from unittest.mock import Mock
        for mode in ("rom", "address", "bank", "symbols", "missing_marker", "source", "failure", "exception"):
            with self.subTest(mode=mode):
                def build(destination):
                    result = self.build.side_effect(destination)
                    if mode == "rom":
                        (destination / "pokegold.gbc").write_bytes(b"changed")
                    elif mode in ("address", "bank", "symbols", "missing_marker"):
                        text = (destination / "pokegold.sym").read_text()
                        if mode == "address":
                            text = text.replace("01:4000 Caller.__", "01:4001 Caller.__")
                        elif mode == "bank":
                            text = text.replace("01:4000 Caller.__", "00:4000 Caller.__")
                        elif mode == "symbols":
                            text = text.replace("01:4100 Callee", "01:4101 Callee")
                        else:
                            text = self.symbols
                        (destination / "pokegold.sym").write_text(text)
                    elif mode == "source":
                        path = destination / "engine/unit.asm"
                        path.write_text(path.read_text() + "; unexpected edit\n")
                    elif mode == "failure":
                        return subprocess.CompletedProcess(["unit-build"], 1, "", "failed")
                    elif mode == "exception":
                        raise RuntimeError("build failed")
                    return result
                report = self.run_mapping(destination=self.root.parent / mode, build=Mock(side_effect=build))
                self.assertFalse(report["valid"])
                self.assertTrue(report["errors"])
                self.assertFalse(report.get("evidence_atoms"))
                self.assert_reference_unchanged()
