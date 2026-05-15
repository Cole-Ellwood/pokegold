from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.metamorphic import (
    relation_ghost_spinblock_softens_revealed_spin_panic,
    relation_revealed_spin_discourages_extra_spikes,
    relation_unrevealed_spin_keeps_spikes_live,
    run_metamorphic_suite,
)


class MetamorphicTests(unittest.TestCase):
    def test_core_metamorphic_suite_passes(self) -> None:
        report = run_metamorphic_suite()

        self.assertTrue(report["passed"])
        self.assertEqual(report["failure_count"], 0)

    def test_spikes_spin_boundary_relations_pass(self) -> None:
        self.assertTrue(relation_revealed_spin_discourages_extra_spikes().passed)
        self.assertTrue(relation_unrevealed_spin_keeps_spikes_live().passed)
        self.assertTrue(relation_ghost_spinblock_softens_revealed_spin_panic().passed)

    def test_cli_metamorphic_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "metamorphic.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "metamorphic",
                        "--generated",
                        "4",
                        "--seed",
                        "1",
                        "--json-out",
                        str(out),
                        "--fail-on-mismatch",
                    ]
                )
            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertTrue(data["passed"])
        self.assertIn("metamorphic suite passed", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
