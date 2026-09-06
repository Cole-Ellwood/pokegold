"""Public regressions from the findings-first source audit."""

import contextlib
import hashlib
import importlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tools"), str(ROOT / "tools/audit")]


class ReportRegressions(unittest.TestCase):
    def test_branch_currency_missing_reference_is_skip(self):
        module = importlib.import_module("check_branch_currency")
        with (
            patch.object(module, "resolve_base", return_value=None),
            contextlib.redirect_stdout(io.StringIO()) as stream,
        ):
            self.assertEqual(module.main(["--strict"]), 0)
        self.assertTrue(stream.getvalue().startswith("SKIP:"))

    def test_checksum_literal_filenames(self):
        module = importlib.import_module("verify_sha1")
        digest = hashlib.sha1(b"content").hexdigest()
        for mode in (" ", "*"):
            for name in (" ordinary", "*literal", "embedded space", "trailing "):
                with (
                    self.subTest(mode=mode, name=name),
                    tempfile.TemporaryDirectory() as tmp,
                ):
                    manifest = Path(tmp) / "manifest"
                    manifest.write_text(f"{digest} {mode}{name}\n", encoding="utf-8")
                    # Mock only file IO to exercise POSIX filenames on Windows too.
                    with (
                        patch.object(sys, "argv", ["verify_sha1", str(manifest)]),
                        patch.object(Path, "exists", return_value=True),
                        patch.object(module, "sha1_file", return_value=digest) as read,
                    ):
                        self.assertEqual(module.main(), 0)
                        self.assertEqual(read.call_args.args[0], manifest.parent / name)

    def test_smoke_skip_and_failure_summary(self):
        module = importlib.import_module("check_release_smoke")
        for output, error, code in [
            ("PASS: delegated\n", "", 0),
            ("SKIP: unavailable\n", "", 0),
            ("PASS: part", "SKIP: unavailable", 0),
            ("broken\n", "", 1),
        ]:
            with (
                self.subTest(output=output),
                patch.object(
                    module.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess([], code, output, error),
                ),
                contextlib.redirect_stdout(io.StringIO()) as stream,
            ):
                if code:
                    with self.assertRaises(SystemExit):
                        module.main()
                    self.assertNotIn(
                        "ALL RELEASE SMOKE CHECKS PASSED", stream.getvalue()
                    )
                else:
                    self.assertEqual(module.main(), 0)
                    if output.startswith("SKIP") or error.startswith("SKIP"):
                        self.assertNotIn(
                            "ALL RELEASE SMOKE CHECKS PASSED", stream.getvalue()
                        )
                        self.assertNotIn(
                            "PASS: grass regrowth ROM rate audit", stream.getvalue()
                        )
                    else:
                        self.assertIn(
                            "ALL RELEASE SMOKE CHECKS PASSED", stream.getvalue()
                        )

    def test_external_report_outputs(self):
        for script, flag in [
            ("generate_dev_index.py", "--out"),
            ("generate_hack_mechanics_reference.py", "--output"),
        ]:
            with self.subTest(script=script), tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp) / "report.md"
                proc = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / script), flag, str(output)],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertGreater(output.stat().st_size, 100)

    def test_index_trace_budget(self):
        module = importlib.import_module("generate_dev_index")
        for trace in (False, True):
            with self.subTest(trace=trace), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / "test.map").write_text("")
                (root / "layout.link").write_text("")
                (root / "test.sym").write_text(
                    "01:d68e wBossAITier\n01:d71a wEventFlags\n"
                    + (
                        "01:d71a wBossAIStateEnd\n01:d6fe wBossAITraceTopMoves\n"
                        if trace
                        else "01:d6fe wBossAIStateEnd\n"
                    )
                )
                with (
                    patch.object(module, "ROOT", root),
                    patch.object(
                        module, "estimate_boss_ai_trace_bytes", return_value=28
                    ),
                    patch.object(sys, "argv", ["index", "--rom", "test", "--stdout"]),
                    contextlib.redirect_stdout(io.StringIO()) as stream,
                ):
                    self.assertEqual(module.main(), 0)
                self.assertIn("| Normal | 112 | 28 |", stream.getvalue())
                self.assertIn(
                    "| With `BOSS_AI_TRACE` fields | 140 | 0 |", stream.getvalue()
                )

    def test_pdf_body_template_and_table_bounds(self):
        try:
            import fitz
            import reportlab
        except ImportError:
            self.skipTest("PDF layout verification requires PyMuPDF and ReportLab")
        module = importlib.import_module("generate_boss_ai_architecture_pdf")
        with tempfile.TemporaryDirectory() as tmp:
            output = module.build(Path(tmp) / "report.pdf")
            with fitz.open(output) as doc:
                self.assertEqual(len(doc), 8)
                for number, page in enumerate(doc, 1):
                    if number > 1:
                        self.assertIn(f"page {number}", page.get_text())
                    for word in page.get_text("words"):
                        self.assertGreaterEqual(word[0], 0)
                        self.assertLessEqual(word[2], page.rect.width)
                # Table filename cells end at x=212.4; long names must wrap.
                for page in (doc[4], doc[5]):
                    for word in page.get_text("words"):
                        if word[4].startswith(
                            ("role_package", "tendency_counter", "redundant.asm")
                        ):
                            self.assertLessEqual(word[2], 212.4)


if __name__ == "__main__":
    unittest.main()
