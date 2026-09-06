from __future__ import annotations

import subprocess
import json
import tempfile
import unittest
from pathlib import Path

from tools.audit.root_cause_fixtures import capture_grass_regrowth, capture_mail_removal, export_revision, verify_export
from tools.audit.check_link_mail_search_rom import check_link_mail_search
from tools.debugger.investigate import build_investigation_run


class RootCauseFixtureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Fixture test")
        for name, content in {
            "main.asm": 'INCLUDE "engine/unit.asm"\n',
            "engine/unit.asm": "Unit:\n\tret\n",
            "Makefile": "gold:\n\ttrue\n",
            "tools/Makefile": "all:\n\ttrue\n",
            "tools/common.h": "/* build dependency */\n",
            "tools/lz/encode.c": "/* build dependency */\n",
            "tools/copy_file.py": "# build dependency\n",
            "docs/fix.md": "Hidden cause and fix\n",
            "audit/answers.json": '{"cause": "Unit"}\n',
            "tools/audit/check_known_bug.py": "# Hidden regression answer\n",
            "tools/debugger/next_steps.py": "# Prewritten answer\n",
        }.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "broken revision")
        self.revision = self.git("rev-parse", "HEAD").strip()
        self.destination = Path(self.tmp.name) / "export"

    def git(self, *args):
        return subprocess.check_output(
            ["git", *args], cwd=self.root, text=True, stderr=subprocess.STDOUT,
        )

    def test_link_scan_rejects_existing_output_before_loading_backend(self):
        from unittest.mock import patch
        self.destination.mkdir()
        marker = self.destination / "keep.txt"
        marker.write_text("keep")
        with patch("tools.trace.runtime.load_pyboy") as backend:
            with self.assertRaises(FileExistsError):
                check_link_mail_search(self.root, self.root, self.destination)
        backend.assert_not_called()
        self.assertEqual(marker.read_text(), "keep")
        self.assertEqual(list(self.destination.iterdir()), [marker])

    def test_link_scan_rejects_changed_source_before_backend_or_output(self):
        from unittest.mock import patch
        export_revision(self.root, self.revision, self.destination)
        (self.destination / "engine/unit.asm").write_text("changed")
        output = self.destination.with_name("capture")
        with patch("tools.trace.runtime.load_pyboy") as backend:
            with self.assertRaisesRegex(ValueError, "source identity differs"):
                check_link_mail_search(self.destination, self.destination, output)
        backend.assert_not_called()
        self.assertFalse(output.exists())

    def test_exports_requested_revision_without_answers_or_dirty_work(self):
        (self.root / "engine/unit.asm").write_text("Unit:\n\tnop\n\tret\n")
        result = export_revision(self.root, self.revision, self.destination)
        self.assertEqual(result["source_commit"], self.revision)
        self.assertEqual(
            (self.destination / "engine/unit.asm").read_text(), "Unit:\n\tret\n",
        )
        for name in ("main.asm", "Makefile", "tools/Makefile", "tools/common.h",
                     "tools/lz/encode.c", "tools/copy_file.py"):
            self.assertTrue((self.destination / name).is_file(), name)
        for name in (".git", "docs", "audit", "tools/audit", "tools/debugger"):
            self.assertFalse((self.destination / name).exists(), name)
        manifest = json.loads((self.destination / "source_manifest.json").read_text())
        self.assertEqual(manifest, {key: result[key] for key in ("source_files", "source_tree_sha256")})
        self.assertNotIn(self.revision, json.dumps(manifest))
        self.assertIn("nop", (self.root / "engine/unit.asm").read_text())

    def test_rejects_existing_destination_without_touching_it(self):
        self.destination.mkdir()
        marker = self.destination / "keep.txt"
        marker.write_text("keep")
        with self.assertRaises(FileExistsError):
            export_revision(self.root, self.revision, self.destination)
        for capture in (capture_grass_regrowth, capture_mail_removal):
            with self.assertRaises(FileExistsError):
                capture(self.root, self.destination)
        self.assertEqual(list(self.destination.iterdir()), [marker])
        self.assertEqual(marker.read_text(), "keep")

    def test_unknown_revision_does_not_create_destination(self):
        with self.assertRaises(subprocess.CalledProcessError):
            export_revision(self.root, "unknown-revision", self.destination)
        self.assertFalse(self.destination.exists())

    def test_missing_rom_or_symbols_does_not_create_capture_destination(self):
        for name in ("pokegold.gbc", "pokegold.sym"):
            with self.subTest(missing=name):
                other = self.root / ("pokegold.sym" if name.endswith("gbc") else "pokegold.gbc")
                other.write_bytes(b"fixture")
                for capture in (capture_grass_regrowth, capture_mail_removal):
                    with self.assertRaises(FileNotFoundError):
                        capture(self.root, self.destination)
                self.assertFalse(self.destination.exists())
                other.unlink()

    def test_mail_capture_requires_one_caller_sequence_before_opening_or_writing(self):
        from unittest.mock import patch
        pattern = bytes([0xFA, 0, 0xD0, 0x3E, 2, 0x21, 0, 0x41, 0xCF])
        for mode in ("missing", "duplicate", "wrong_bank"):
            with self.subTest(mode=mode):
                rom = bytearray(32768)
                code = b"" if mode == "missing" else pattern * (2 if mode == "duplicate" else 1)
                rom[0x4000:0x4000 + len(code)] = code
                (self.root / "pokegold.gbc").write_bytes(rom)
                (self.root / "pokegold.sym").write_text(
                    "01:4000 MonMailAction.RemoveMailToBag\n" +
                    ("02" if mode == "wrong_bank" else "01") + ":4020 MonMailAction.BagIsFull\n" +
                    "02:4100 ClearPartyMonMail\n01:D000 wCurPartyMon\n")
                with patch("tools.damage_debugger.emulator.DebugSession.open") as opened:
                    with self.assertRaisesRegex(ValueError, "one observed caller"):
                        capture_mail_removal(self.root, self.destination)
                opened.assert_not_called()
                self.assertFalse(self.destination.exists())

    def test_source_identity_is_content_based_and_changes_with_source(self):
        first = export_revision(self.root, self.revision, self.destination)
        (self.root / "docs/fix.md").write_text("More hidden answers\n")
        self.git("add", ".")
        self.git("commit", "-qm", "documentation only")
        second = export_revision(self.root, "HEAD", self.destination.with_name("second"))
        self.assertEqual(first["source_tree_sha256"], second["source_tree_sha256"])
        (self.root / "engine/unit.asm").write_text("Unit:\n\tnop\n\tret\n")
        self.git("add", ".")
        self.git("commit", "-qm", "changed source")
        third = export_revision(self.root, "HEAD", self.destination.with_name("third"))
        self.assertNotEqual(first["source_tree_sha256"], third["source_tree_sha256"])

    def test_revalidation_rejects_changed_missing_or_forged_source_basis(self):
        identity = export_revision(self.root, self.revision, self.destination)
        self.assertTrue(verify_export(self.destination, identity))
        source = self.destination / "engine/unit.asm"
        original = source.read_bytes()
        source.write_bytes(b"wrong source")
        self.assertFalse(verify_export(self.destination, identity))
        source.unlink()
        self.assertFalse(verify_export(self.destination, identity))
        source.write_bytes(original)
        self.assertFalse(verify_export(self.destination, {**identity, "source_tree_sha256": "wrong"}))
        self.assertFalse(verify_export(self.destination, {**identity, "source_files": {}}))

    def test_public_investigation_verifies_exported_source_identity(self):
        identity = export_revision(self.root, self.revision, self.destination)
        (self.destination / "engine/generated.bin").write_bytes(b"build output")
        report = build_investigation_run(root=self.destination, out_dir="report",
                                         max_targets=1, max_events=1, max_cases=1)
        self.assertEqual(report["source_tree_sha256"], identity["source_tree_sha256"])
        self.assertNotIn("source_commit", report)
        (self.destination / "source_manifest.json").unlink()
        report = build_investigation_run(root=self.destination, out_dir="without_manifest",
                                         max_targets=1, max_events=1, max_cases=1)
        self.assertNotIn("source_tree_sha256", report)

    def test_source_change_during_investigation_invalidates_the_report(self):
        from unittest.mock import patch
        from tools.debugger.ingest import ingest_artifacts
        export_revision(self.root, self.revision, self.destination)
        def ingest(**kwargs):
            result = ingest_artifacts(**kwargs)
            (self.destination / "engine/unit.asm").write_text("Unit:\n\tnop\n\tret\n")
            return result
        with patch("tools.debugger.investigate.ingest_artifacts", side_effect=ingest):
            report = build_investigation_run(root=self.destination, out_dir="report",
                                             max_targets=1, max_events=1, max_cases=1)
        self.assertFalse(report["valid"])
        self.assertNotIn("source_tree_sha256", report)
        self.assertTrue(any("source manifest content differs" in error for error in report["errors"]))

    def test_invalid_source_manifest_rejects_before_investigation_outputs(self):
        from unittest.mock import patch
        identity = export_revision(self.root, self.revision, self.destination)
        manifest = {key: identity[key] for key in ("source_files", "source_tree_sha256")}
        path = self.destination / "source_manifest.json"
        for invalid in ({}, {**manifest, "source_tree_sha256": "stale"},
                        {"source_files": manifest["source_files"]},
                        {"source_tree_sha256": manifest["source_tree_sha256"]},
                        {**manifest, "source_files": {}},
                        {**manifest, "source_files": {"": "0" * 64}},
                        {**manifest, "source_files": {"engine\\unit.asm": "0" * 64}},
                        {**manifest, "source_files": {str(self.root / "main.asm"): "0" * 64}},
                        {**manifest, "source_files": {"../outside.asm": "0" * 64}},
                        {**manifest, "source_files": {"engine/../main.asm": "0" * 64}},
                        {**manifest, "source_files": {"missing.asm": "0" * 64}}):
            with self.subTest(invalid=invalid), patch("tools.debugger.investigate.ingest_artifacts") as ingest:
                path.write_text(json.dumps(invalid))
                with self.assertRaises(ValueError):
                    build_investigation_run(root=self.destination, out_dir="report")
                ingest.assert_not_called()
                self.assertFalse((self.destination / "report").exists())
        path.write_text(json.dumps(manifest))
        (self.destination / "engine/unit.asm").write_text("changed")
        with self.assertRaises(ValueError):
            build_investigation_run(root=self.destination, out_dir="report")
        self.assertFalse((self.destination / "report").exists())


if __name__ == "__main__":
    unittest.main()
