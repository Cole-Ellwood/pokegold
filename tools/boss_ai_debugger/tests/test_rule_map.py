from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.rule_map import build_rule_map, validate_rule_map


class RuleMapTests(unittest.TestCase):
    def test_current_rule_map_contains_recent_spikes_spin_rules(self) -> None:
        data = build_rule_map()
        labels = {rule["source_label"] for rule in data["rules"]}

        self.assertFalse(validate_rule_map(data))
        self.assertIn(".ApplyRevealedRapidSpinSpikesRisk", labels)
        self.assertIn(".BossHasAvailableReserveGhost", labels)
        self.assertIn(".SpeciesLevelUpHasRapidSpin", labels)

    def test_public_info_rules_have_stable_rule_ids(self) -> None:
        data = build_rule_map()
        by_label = {rule["source_label"]: rule for rule in data["rules"]}
        rule = by_label[".PlayerHasSeenBenchRevealedRapidSpin"]

        self.assertEqual(rule["classification"], "public_info")
        self.assertEqual(
            rule["rule_id"],
            "move.apply_move_model.player_has_seen_bench_revealed_rapid_spin",
        )
        self.assertIn("wPlayerUsedMoves", rule["public_reads"])
        self.assertTrue(rule["executable"])
        self.assertTrue(rule["score_trace_target"])
        self.assertTrue(rule["requires_public_read_provenance"])
        self.assertIn("wPlayerUsedMoves", rule["expected_public_inputs"])

    def test_static_boss_ai_tables_are_not_dynamic_coverage_targets(self) -> None:
        data = build_rule_map()
        by_label = {rule["source_label"]: rule for rule in data["rules"]}
        table = by_label["BossAIRiskyEffects"]

        self.assertFalse(table["executable"])
        self.assertFalse(table["dynamic_coverage_target"])
        self.assertEqual(table["coverage_mode"], "static_reference")

    def test_cli_rule_map_build_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "rule_map.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(["rule-map", "build", "--json-out", str(out)])

            text = out.read_text(encoding="utf-8")

        self.assertEqual(code, 0)
        self.assertIn("Boss AI rule-map check passed", stdout.getvalue())
        self.assertIn("ApplyRevealedRapidSpinSpikesRisk", text)


if __name__ == "__main__":
    unittest.main()
