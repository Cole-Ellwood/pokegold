from __future__ import annotations

import unittest

from tools.debugger.command_metadata import (
    READ_ONLY_FORBIDDEN_EFFECTS,
    SIDE_EFFECTS,
    all_command_metadata,
    metadata_by_id,
    read_only_refusal_for,
    taxonomy_summary,
)


class CommandMetadataTests(unittest.TestCase):
    def test_all_registered_commands_have_declared_side_effects(self) -> None:
        summary = taxonomy_summary()
        self.assertGreater(summary["command_count"], 0)
        self.assertEqual(summary["side_effect_unknown_command_count"], 0)

    def test_effect_names_are_from_closed_taxonomy(self) -> None:
        allowed = set(SIDE_EFFECTS)
        for row in all_command_metadata():
            self.assertTrue(row.side_effects, row.command_id)
            self.assertTrue(set(row.side_effects).issubset(allowed), row.command_id)

    def test_read_only_safety_refuses_writing_commands(self) -> None:
        by_id = metadata_by_id()
        self.assertTrue(by_id["debugger:inventory"].read_only_safe)
        self.assertIn("read_only", by_id["debugger:inventory"].side_effects)
        self.assertFalse(by_id["debugger:rom-byte"].read_only_safe)
        self.assertNotIn("read_only", by_id["debugger:rom-byte"].side_effects)
        self.assertIn("writes_report", by_id["debugger:rom-byte"].side_effects)
        self.assertFalse(by_id["debugger:rom-index"].read_only_safe)
        self.assertNotIn("read_only", by_id["debugger:rom-index"].side_effects)
        self.assertIn("writes_generated_artifact", by_id["debugger:rom-index"].side_effects)
        self.assertFalse(by_id["debugger:prove"].read_only_safe)
        self.assertNotIn("read_only", by_id["debugger:prove"].side_effects)
        self.assertFalse(by_id["debugger:gate"].read_only_safe)
        self.assertNotIn("read_only", by_id["debugger:gate"].side_effects)
        self.assertTrue(by_id["boss-ai:universe"].read_only_safe)
        self.assertIn("read_only", by_id["boss-ai:universe"].side_effects)
        self.assertFalse(by_id["boss-ai:run-suite"].read_only_safe)
        self.assertNotIn("read_only", by_id["boss-ai:run-suite"].side_effects)
        self.assertTrue(set(by_id["boss-ai:run-suite"].side_effects) & READ_ONLY_FORBIDDEN_EFFECTS)

    def test_read_only_refusal_reports_forbidden_effects(self) -> None:
        self.assertIsNone(read_only_refusal_for("debugger:inventory"))
        refusal = read_only_refusal_for("boss-ai:run-suite")
        self.assertIsNotNone(refusal)
        self.assertIn("boss-ai:run-suite", refusal or "")
        self.assertIn("rebuilds_rom", refusal or "")

    def test_read_only_refusal_rejects_output_flags_on_safe_commands(self) -> None:
        self.assertIsNone(
            read_only_refusal_for("debugger:triage", ["triage", "--symptom", "test"])
        )
        refusal = read_only_refusal_for(
            "debugger:triage", ["triage", "--symptom", "test", "--json-out", "out.json"]
        )
        self.assertIsNotNone(refusal)
        self.assertIn("--json-out", refusal or "")
        equals_form = read_only_refusal_for(
            "boss-ai:universe", ["universe", "--json-out=out.json"]
        )
        self.assertIsNotNone(equals_form)
        self.assertIn("--json-out", equals_form or "")


if __name__ == "__main__":
    unittest.main()
