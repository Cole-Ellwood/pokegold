from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.replay_import import (
    ReplayImportOptions,
    import_mastery_documents,
    import_replay_sources,
)
from tools.boss_ai_debugger.rom_scenarios import evaluate_batch
from tools.boss_ai_debugger.state_schema import validate_scenario_file


SYNTHETIC_LOG = """\
|player|p1|Alice|
|player|p2|Bob|
|gen|2
|tier|[Gen 2] OU
|start
|switch|p1a: Cloyster|Cloyster, M|100/100
|switch|p2a: Starmie|Starmie|100/100
|turn|1
|move|p1a: Cloyster|Spikes|p2a: Starmie
|-sidestart|p2: Bob|Spikes
|move|p2a: Starmie|Surf|p1a: Cloyster
|-damage|p1a: Cloyster|72/100
|turn|2
|move|p2a: Starmie|Rapid Spin|p1a: Cloyster
|-sideend|p2: Bob|Spikes
|move|p1a: Cloyster|Toxic|p2a: Starmie
|-status|p2a: Starmie|psn
|turn|3
|move|p1a: Cloyster|Explosion|p2a: Starmie
|faint|p1a: Cloyster
|faint|p2a: Starmie
"""


class ReplayImportTests(unittest.TestCase):
    def test_replay_log_import_builds_public_scenarios(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "gen2ou-1.log"
            out = Path(tmp) / "scenarios.jsonl"
            log.write_text(SYNTHETIC_LOG, encoding="utf-8")

            result = import_replay_sources(
                logs=[log],
                options=ReplayImportOptions(side="p1", turns=(2,), seed=5),
            )
            rows = result["scenarios"]
            out.write_text(
                "\n".join(__import__("json").dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )

            validation = validate_scenario_file(out)
            batch = evaluate_batch(rows)

        self.assertEqual(len(rows), 1)
        self.assertTrue(validation["valid"])
        self.assertEqual(batch["scenario_count"], 1)
        self.assertEqual(rows[0]["state"]["boss"]["active"]["species"], "Cloyster")
        self.assertIn("replay_source", rows[0])
        self.assertNotIn("hidden", __import__("json").dumps(rows[0]).lower())

    def test_mastery_document_import_projects_to_debugger_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "cashout_spin_probe_gen2ou-123_p1.md"
            doc.write_text(
                "# Probe\n\nSpikes, Rapid Spin, Explosion, receiver branch, and cash-out.\n",
                encoding="utf-8",
            )

            result = import_mastery_documents([doc], seed=7)
            rows = result["scenarios"]

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["family"], "mastery_replay")
        self.assertIn("mastery_source", rows[0])
        tags = rows[0]["expectation"]["policy_tags"]
        self.assertIn("hazard_retention", tags)
        self.assertIn("cashout", tags)

    def test_mastery_document_import_tags_newest_cashout_lessons(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "resisted_explosion_board_delta_drill_001_2026-05-15.md"
            doc.write_text(
                (
                    "# Resisted Explosion Board Delta\n\n"
                    "Clean-oracle review: prefer the reversible lower-commitment "
                    "line unless resisted Explosion opens a free owner. Lovely Kiss "
                    "also creates a sleep plus cash-out role package.\n"
                ),
                encoding="utf-8",
            )

            result = import_mastery_documents([doc], seed=8)
            scenario = result["scenarios"][0]

        tags = set(scenario["expectation"]["policy_tags"])
        self.assertEqual(scenario["mastery_template_family"], "cashout_board_delta")
        self.assertIn("resisted_explosion_board_delta", tags)
        self.assertIn("reversible_before_irreversible", tags)
        self.assertIn("clean_oracle_subset", tags)
        self.assertIn("sleep_plus_cashout_package", tags)

    def test_cli_replay_import_writes_jsonl_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "gen2ou-2.log"
            out = Path(tmp) / "scenarios.jsonl"
            report = Path(tmp) / "report.json"
            log.write_text(SYNTHETIC_LOG, encoding="utf-8")
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "replay-import",
                        "--log",
                        str(log),
                        "--side",
                        "p1",
                        "--turn",
                        "2",
                        "--out",
                        str(out),
                        "--json-out",
                        str(report),
                    ]
                )

            self.assertEqual(code, 0)
            self.assertTrue(out.exists())
            self.assertTrue(report.exists())
            self.assertIn("Boss AI replay import", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
