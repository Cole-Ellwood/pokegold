from __future__ import annotations

import tempfile
import unittest
import subprocess
from pathlib import Path

from tools.debugger.report_envelope import build_report_envelope, dirty_diff_hash, sha256_file


class ReportEnvelopeTests(unittest.TestCase):
    def test_envelope_contains_required_literal_anything_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = root / "unit.gbc"
            sym = root / "unit.sym"
            rom.write_bytes(b"rom")
            sym.write_bytes(b"sym")
            expected_rom_sha = sha256_file(rom)
            expected_sym_sha = sha256_file(sym)

            envelope = build_report_envelope(
                kind="unit_report",
                command="python unit",
                inputs={"x": 1},
                rom_path=rom,
                symbols_path=sym,
                proof_status="missing_evidence",
                missing_evidence=["proof"],
                blocking_gaps=["gap"],
                known_limits=["limit"],
                closed_evidence_ids=["closed"],
                repro_command="python unit",
                disproof_standard=["disprove"],
                root=root,
            )

        for key in (
            "kind",
            "schema_version",
            "command",
            "inputs",
            "rom_sha256",
            "symbols_sha256",
            "source_commit",
            "dirty_diff_hash",
            "state_basis",
            "backend",
            "proof_status",
            "missing_evidence",
            "blocking_gaps",
            "known_limits",
            "closed_evidence_ids",
            "repro_command",
            "disproof_standard",
        ):
            self.assertIn(key, envelope)
        self.assertEqual(envelope["rom_sha256"], expected_rom_sha)
        self.assertEqual(envelope["symbols_sha256"], expected_sym_sha)
        self.assertEqual(envelope["proof_status"], "missing_evidence")

    def test_relative_hash_inputs_resolve_against_passed_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "unit.gbc").write_bytes(b"rom")
            envelope = build_report_envelope(
                kind="unit_report",
                command="python unit",
                rom_path="unit.gbc",
                root=root,
            )

        self.assertNotEqual(envelope["rom_sha256"], "")

    def test_dirty_diff_hash_changes_when_untracked_content_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            untracked = root / "new_gate.py"
            untracked.write_text("one", encoding="utf-8")
            first = dirty_diff_hash(root)
            untracked.write_text("two", encoding="utf-8")
            second = dirty_diff_hash(root)

        self.assertNotEqual(first, second)

    def test_dirty_diff_hash_can_exclude_generated_artifact_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            source = root / "source.py"
            source.write_text("source", encoding="utf-8")
            artifact = root / "audit" / "boss_ai_debugger" / "god_level_benchmark" / "out.json"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("one", encoding="utf-8")
            volatile = root / "pokegold_trace.gbc.ram"
            volatile.write_text("ram one", encoding="utf-8")
            first = dirty_diff_hash(
                root,
                exclude_path_prefixes=(
                    "audit/boss_ai_debugger/god_level_benchmark",
                    "pokegold_trace.gbc.ram",
                ),
            )
            artifact.write_text("two", encoding="utf-8")
            volatile.write_text("ram two", encoding="utf-8")
            second = dirty_diff_hash(
                root,
                exclude_path_prefixes=(
                    "audit/boss_ai_debugger/god_level_benchmark",
                    "pokegold_trace.gbc.ram",
                ),
            )
            source.write_text("changed", encoding="utf-8")
            third = dirty_diff_hash(
                root,
                exclude_path_prefixes=(
                    "audit/boss_ai_debugger/god_level_benchmark",
                    "pokegold_trace.gbc.ram",
                ),
            )

        self.assertEqual(first, second)
        self.assertNotEqual(second, third)

    def test_dirty_diff_hash_changes_when_staged_content_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            tracked = root / "tracked.txt"
            tracked.write_text("one", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True, capture_output=True)
            first = dirty_diff_hash(root)
            tracked.write_text("two", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True, capture_output=True)
            second = dirty_diff_hash(root)

        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
