from __future__ import annotations

import unittest

from tools.boss_ai_debugger.rom_contribution_trace import MemoryPatch
from tools.boss_ai_debugger.rom_counterfactual_materialize import (
    counterfactual_mutation_changed_key,
    counterfactual_witnesses_for_traces,
    move_choice_observable,
    switch_dispatch_observable,
)
from tools.boss_ai_debugger.universe import ALLOWED_COUNTERFACTUAL_MUTATION_KEYS


class RomCounterfactualMaterializeTests(unittest.TestCase):
    def test_counterfactual_witnesses_only_credit_missing_executed_move_surfaces(self) -> None:
        universe = {
            "exhaustive_class_witness_catalog": {
                "catalog_rows": [
                    {
                        "status": "cataloged_missing_rom_proof",
                        "witness_role": "counterfactual_flip",
                        "rule_id": "move.covered",
                        "decision_surface": "move_score",
                        "family": "mastery_policy",
                        "source_label": ".Covered",
                        "parent_label": "BossAI_ApplyMoveModel",
                    },
                    {
                        "status": "cataloged_missing_rom_proof",
                        "witness_role": "counterfactual_flip",
                        "rule_id": "switch.covered",
                        "decision_surface": "switch_dispatch",
                    },
                    {
                        "status": "cataloged_missing_rom_proof",
                        "witness_role": "counterfactual_flip",
                        "rule_id": "move.not_executed",
                        "decision_surface": "move_score",
                    },
                ],
            },
        }
        baseline = {
            "source": "trace_rom_pyboy_hooks",
            "trace_id": "baseline",
            "executed_rule_ids": ["move.covered", "switch.covered"],
            "chosen": {"move_id": 89, "slot_index": 0},
        }
        counterfactual = {
            "source": "trace_rom_pyboy_hooks",
            "trace_id": "counterfactual",
            "executed_rule_ids": ["move.covered", "switch.covered"],
            "chosen": {"move_id": 126, "slot_index": 2},
        }

        witnesses = counterfactual_witnesses_for_traces(
            universe,
            baseline_trace=baseline,
            counterfactual_trace=counterfactual,
            mutation=MemoryPatch("wBattleMonType1", 0, 8),
            mutation_key="wBattleMonType1",
            baseline_observable=move_choice_observable(baseline),
            counterfactual_observable=move_choice_observable(counterfactual),
            supported_decision_surfaces=frozenset({"boss_ai_rule", "move_score"}),
        )

        self.assertEqual([witness["rule_id"] for witness in witnesses], ["move.covered"])
        self.assertEqual(
            witnesses[0]["mutation"]["changed_keys"],
            ["wBattleMonType1"],
        )

    def test_counterfactual_mutation_changed_key_includes_offsets(self) -> None:
        self.assertEqual(
            counterfactual_mutation_changed_key(MemoryPatch("wPlayerUsedMoves", 3, 105)),
            "wPlayerUsedMoves+3",
        )

    def test_enemy_stat_level_counterfactual_mutations_are_allowlisted(self) -> None:
        self.assertIn("wEnemyStatLevels", ALLOWED_COUNTERFACTUAL_MUTATION_KEYS)
        self.assertIn("wEnemyStatLevels+6", ALLOWED_COUNTERFACTUAL_MUTATION_KEYS)

    def test_switch_dispatch_observable_uses_switch_observation(self) -> None:
        observable = switch_dispatch_observable(
            {
                "switch_observation": {
                    "status": "actual_switch_observed",
                    "switch_confidence": 99,
                    "switch_param": 49,
                    "switch_index": 2,
                },
            }
        )

        self.assertEqual(
            observable,
            {
                "kind": "switch_dispatch",
                "status": "actual_switch_observed",
                "switch_confidence": 99,
                "switch_param": 49,
                "switch_index": 2,
            },
        )


if __name__ == "__main__":
    unittest.main()
