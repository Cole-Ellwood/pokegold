from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.boss_ai_debugger.move_score_probe import find_score_probe_route


class MoveScoreProbeRouteTests(unittest.TestCase):
    def test_score_probe_does_not_use_pre_choice_state_as_score_base(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pre_choice = root / "erika_pre_choice.state"
            pre_choice.write_bytes(b"state")
            rom = root / "test.gbc"
            symbols = root / "test.sym"
            rom.write_bytes(b"rom")
            symbols.write_text("", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "captures": [
                            {
                                "id": "erika",
                                "pre_choice_state": str(pre_choice),
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            route = find_score_probe_route(
                manifest,
                trainer_route_ids=("erika",),
                score_base_route=None,
                rom=rom,
                symbols=symbols,
            )

            self.assertEqual(route.route_id, "erika")
            self.assertIsNone(route.route_state)
            self.assertEqual(route.route_state_field, "")
            self.assertTrue(
                any(
                    "replaying the trainer route from the start" in warning
                    for warning in route.warnings
                )
            )

    def test_score_probe_uses_clean_score_materialization_state_when_available(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            score_state = root / "koga_score.state"
            score_state.write_bytes(b"state")
            rom = root / "test.gbc"
            symbols = root / "test.sym"
            rom.write_bytes(b"rom")
            symbols.write_text("", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "captures": [
                            {
                                "id": "koga",
                                "score_materialization_state": str(score_state),
                            },
                            {
                                "id": "erika",
                                "pre_choice_state": str(root / "erika_pre_choice.state"),
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            route = find_score_probe_route(
                manifest,
                trainer_route_ids=("erika",),
                score_base_route="koga",
                rom=rom,
                symbols=symbols,
            )

            self.assertEqual(route.route_id, "koga")
            self.assertEqual(route.route_state, score_state)
            self.assertEqual(route.route_state_field, "score_materialization_state")
            self.assertTrue(
                any(
                    "generic synthetic scoring base" in warning
                    for warning in route.warnings
                )
            )


if __name__ == "__main__":
    unittest.main()
