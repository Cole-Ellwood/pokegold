"""Focused tests for the forward consequence/impact oracle."""

from __future__ import annotations

import unittest

from tools.debugger import consequence


class ConsequenceReportTests(unittest.TestCase):
    def test_no_target_is_invalid(self) -> None:
        report = consequence.build_consequence_report()
        self.assertFalse(report["valid"])
        self.assertTrue(report["errors"])

    def test_function_symbol_reports_forward_abi_and_blind_spots(self) -> None:
        # GetUserItem is a real battle-engine function with a known clobber set.
        report = consequence.build_consequence_report(symbol="GetUserItem")
        self.assertTrue(report["valid"])
        self.assertEqual(report["target"]["kind"], "function")
        self.assertIsNotNone(report["forward_abi"])
        self.assertTrue(report["forward_abi"]["clobber_set"])
        # A consequence report must NEVER be presented as a completeness proof.
        self.assertTrue(report["blind_spots"])
        # The release floor always applies.
        gate_ids = {gate["id"] for gate in report["hazard_gates"]}
        self.assertIn("release_smoke", gate_ids)
        # Static-only answer is honestly marked, with runtime proof commands offered.
        self.assertEqual(report["proof_mode"], "source")
        self.assertTrue(report["proof_commands"])

    def test_damage_chain_file_fires_clobber_smoke_gate(self) -> None:
        report = consequence.build_consequence_report(
            file="engine/battle/late_gen_held_items.asm"
        )
        self.assertTrue(report["valid"])
        gate_ids = {gate["id"] for gate in report["hazard_gates"]}
        self.assertIn("damage_chain_abi", gate_ids)
        damage_gate = next(g for g in report["hazard_gates"] if g["id"] == "damage_chain_abi")
        self.assertTrue(
            any("clobber_smoke" in cmd for cmd in damage_gate["commands"])
        )

    def test_ram_path_fires_save_format_gate(self) -> None:
        gates = consequence._match_hazards(
            path="ram/wram.asm", body_text="", target_kind="file"
        )
        gate_ids = {gate["id"] for gate in gates}
        self.assertIn("save_format", gate_ids)

    def test_farcall_in_body_fires_farcall_gate(self) -> None:
        gates = consequence._match_hazards(
            path="engine/battle/foo.asm",
            body_text="    farcall SomeTargetInAnotherBank\n",
            target_kind="file",
        )
        gate_ids = {gate["id"] for gate in gates}
        self.assertIn("farcall_clobber", gate_ids)

    def test_balance_data_file_reports_data_delta(self) -> None:
        report = consequence.build_consequence_report(
            file="data/pokemon/base_stats/gyarados.asm"
        )
        self.assertIsNotNone(report["data_delta"])
        self.assertIn("taste call", report["data_delta"]["note"])


if __name__ == "__main__":
    unittest.main()
