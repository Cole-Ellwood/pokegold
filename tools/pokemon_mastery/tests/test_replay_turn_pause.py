from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.pokemon_mastery.replay_turn_pause import (
    format_prompt,
    format_reveal,
    format_summary,
)


SYNTHETIC_LOG = """\
|player|p1|Alice|
|player|p2|Bob|
|gen|2
|tier|[Gen 2] OU
|start
|switch|p1a: Zapdos|Zapdos|100/100
|switch|p2a: Snorlax|Snorlax, M|100/100
|turn|1
|move|p1a: Zapdos|Thunder|p2a: Snorlax
|-damage|p2a: Snorlax|70/100
|move|p2a: Snorlax|Curse|p2a: Snorlax
|-unboost|p2a: Snorlax|spe|1
|-boost|p2a: Snorlax|atk|1
|-boost|p2a: Snorlax|def|1
|-heal|p2a: Snorlax|76/100|[from] item: Leftovers
|turn|2
|switch|p1a: Golem|Golem, M|100/100
|move|p2a: Snorlax|Rest|p2a: Snorlax
|-status|p2a: Snorlax|slp|[from] move: Rest
|-heal|p2a: Snorlax|100/100 slp|[silent]
|turn|3
|move|p1a: Golem|Earthquake|p2a: Snorlax
|cant|p2a: Snorlax|slp
"""


class ReplayTurnPauseTests(unittest.TestCase):
    def test_prompt_before_turn_includes_past_public_state_only(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "synthetic.log"
            path.write_text(SYNTHETIC_LOG, encoding="utf-8")

            prompt = format_prompt(path, 2)

        self.assertIn("p1 / Alice: active Zapdos", prompt)
        self.assertIn("p2 / Bob: active Snorlax HP 76/100 healthy", prompt)
        self.assertIn("moves: Thunder", prompt)
        self.assertIn("moves: Curse", prompt)
        self.assertIn("boosts atk+1, def+1, spe-1", prompt)
        self.assertNotIn("Golem", prompt)
        self.assertNotIn("Rest", prompt)
        self.assertNotIn("Earthquake", prompt)

    def test_reveal_includes_selected_turn_but_not_future_turn(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "synthetic.log"
            path.write_text(SYNTHETIC_LOG, encoding="utf-8")

            reveal = format_reveal(path, 2)

        self.assertIn("|turn|2", reveal)
        self.assertIn("|switch|p1a: Golem|Golem, M|100/100", reveal)
        self.assertIn("|move|p2a: Snorlax|Rest|p2a: Snorlax", reveal)
        self.assertNotIn("|turn|3", reveal)
        self.assertNotIn("Earthquake", reveal)

    def test_summary_reports_players_and_turn_count(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "synthetic.log"
            path.write_text(SYNTHETIC_LOG, encoding="utf-8")

            summary = format_summary(path)

        self.assertIn("Format: Gen 2; tier: [Gen 2] OU", summary)
        self.assertIn("Players: p1=Alice; p2=Bob", summary)
        self.assertIn("Turns: 1-3 (3 turns)", summary)


if __name__ == "__main__":
    unittest.main()
