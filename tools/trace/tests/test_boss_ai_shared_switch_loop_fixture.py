from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.trace import boss_ai_shared_switch_loop_fixture as fixture


class ManifestSwitchBaseStateTests(unittest.TestCase):
    def test_prefers_current_jasmine_state_over_recorded_shared_base(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "captures": [
                            {
                                "id": "shared_switch_loop",
                                "switch_materialization_base_state": (
                                    ".local/tmp/boss_state_factory/jasmine_old.state"
                                ),
                            },
                            {
                                "id": "jasmine",
                                "save_state": (
                                    ".local/tmp/boss_state_factory/jasmine_current.state"
                                ),
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with patch.object(fixture, "ROOT", root), patch.object(
                fixture, "MANIFEST", manifest
            ):
                self.assertEqual(
                    fixture.manifest_switch_base_state(),
                    root / ".local/tmp/boss_state_factory/jasmine_current.state",
                )

    def test_falls_back_to_recorded_shared_base_when_jasmine_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "captures": [
                            {
                                "id": "shared_switch_loop",
                                "switch_materialization_base_state": (
                                    ".local/tmp/boss_state_factory/jasmine_old.state"
                                ),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with patch.object(fixture, "ROOT", root), patch.object(
                fixture, "MANIFEST", manifest
            ):
                self.assertEqual(
                    fixture.manifest_switch_base_state(),
                    root / ".local/tmp/boss_state_factory/jasmine_old.state",
                )


if __name__ == "__main__":
    unittest.main()
