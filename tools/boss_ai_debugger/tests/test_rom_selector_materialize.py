from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

from tools.boss_ai_debugger.generators import generate_scenarios
from tools.boss_ai_debugger.rom_selector_materialize import (
    DEFAULT_BASE_ROUTE,
    DEFAULT_MANIFEST_PATH,
    action_id_for_slot,
    fake_move_ids_for_scenario,
    run_rom_selector_materialization,
    selector_verdict_from_values,
)
from tools.trace import boss_ai_trace_capture as capture


ROOT = Path(__file__).resolve().parents[3]


def pyboy_available() -> bool:
    local_pydeps = ROOT / ".local" / "pydeps"
    if local_pydeps.exists() and str(local_pydeps) not in sys.path:
        sys.path.insert(0, str(local_pydeps))
    return importlib.util.find_spec("pyboy") is not None


class RomSelectorMaterializeTests(unittest.TestCase):
    def test_default_fake_move_ids_preserve_slot_order(self) -> None:
        scenario = {
            "moves": [
                {"id": "slot1", "name": "A"},
                {"id": "slot2", "name": "B", "move_id": 57},
            ]
        }

        self.assertEqual(fake_move_ids_for_scenario(scenario), [1, 57, 0, 0])

    def test_verdict_accepts_nonzero_probability_rom_choice(self) -> None:
        python_result = {
            "scenario_id": "unit",
            "ready": True,
            "tier": 3,
            "best_action_id": "slot1",
            "second_action_id": "slot2",
            "probabilities": {"slot1": 0.7, "slot2": 0.3},
            "moves": [
                {"slot": 1, "action_id": "slot1", "final_score": 20},
                {"slot": 2, "action_id": "slot2", "final_score": 21},
            ],
        }
        values = {
            "wCurEnemyMoveNum": [1],
            "wBossAITraceChosenMove": [2],
            "wEnemyMonMoves": [1, 2, 0, 0],
            "wEnemyAIMoveScores": [20, 21, 80, 80],
            "wBossAITier": [3],
        }

        verdict = selector_verdict_from_values(
            {"id": "unit"},
            python_result,
            values,
            {2: "KARATE_CHOP"},
            patched_count=1,
            frame=1,
        )

        self.assertTrue(verdict["agreement"])
        self.assertEqual(verdict["rom"]["chosen_action_id"], "slot2")

    def test_verdict_rejects_zero_probability_rom_choice(self) -> None:
        python_result = {
            "scenario_id": "unit",
            "ready": True,
            "tier": 3,
            "best_action_id": "slot1",
            "second_action_id": "slot2",
            "probabilities": {"slot1": 0.7, "slot2": 0.3, "slot3": 0.0},
            "moves": [
                {"slot": 1, "action_id": "slot1", "final_score": 20},
                {"slot": 2, "action_id": "slot2", "final_score": 21},
                {"slot": 3, "action_id": "slot3", "final_score": 21},
            ],
        }
        values = {
            "wCurEnemyMoveNum": [2],
            "wBossAITraceChosenMove": [3],
            "wEnemyMonMoves": [1, 2, 3, 0],
            "wEnemyAIMoveScores": [20, 21, 21, 80],
            "wBossAITier": [3],
        }

        verdict = selector_verdict_from_values(
            {"id": "unit"},
            python_result,
            values,
            {3: "DOUBLESLAP"},
            patched_count=1,
            frame=1,
        )

        self.assertFalse(verdict["agreement"])
        self.assertIn("zero Python selector probability", verdict["reason"])

    def test_action_id_for_slot_uses_zero_based_rom_slot(self) -> None:
        python_result = {
            "moves": [
                {"slot": 1, "action_id": "slot1"},
                {"slot": 2, "action_id": "slot2"},
            ]
        }

        self.assertEqual(action_id_for_slot(python_result, 0), "slot1")
        self.assertEqual(action_id_for_slot(python_result, 1), "slot2")
        self.assertIsNone(action_id_for_slot(python_result, 3))

    @unittest.skipUnless(
        pyboy_available()
        and capture.DEFAULT_ROM.exists()
        and capture.DEFAULT_SYMBOLS.exists()
        and DEFAULT_MANIFEST_PATH.exists()
        and (ROOT / ".local/tmp/boss_state_factory/clair_pre_choice_frame_4523.state").exists(),
        "PyBoy trace ROM selector materialization fixture is unavailable",
    )
    def test_selector_materialization_smoke_matches_rom_selector(self) -> None:
        scenarios = generate_scenarios(family="selector_edges", count=2, seed=1)

        report = run_rom_selector_materialization(
            scenarios,
            base_route=DEFAULT_BASE_ROUTE,
            watch_frames=80,
            source="unit_test",
        )

        self.assertEqual(report["checked_count"], 2)
        self.assertEqual(report["mismatch_count"], 0)
        self.assertEqual(report["agreement_rate"], 1.0)

if __name__ == "__main__":
    unittest.main()
