from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.pokemon_mastery.replay_turn_pause import (
    format_prompt,
    format_reveal,
    format_side_prompt,
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


NICKNAMED_LOG = """\
|player|p1|Alice|
|player|p2|Bob|
|gen|2
|tier|[Gen 2] OU
|start
|switch|p1a: Cloyster|Cloyster, M|100/100
|switch|p2a: Bastard|Snorlax, M|100/100
|turn|1
|move|p1a: Cloyster|Spikes|p2a: Bastard
|-sidestart|p2: Bob|Spikes
"""


VOLATILE_LOG = """\
|player|p1|Alice|
|player|p2|Bob|
|gen|2
|tier|[Gen 2] OU
|start
|switch|p1a: Cloyster|Cloyster, M|100/100
|switch|p2a: Starmie|Starmie|100/100
|turn|1
|move|p2a: Starmie|Substitute|p2a: Starmie
|-start|p2a: Starmie|Substitute
|-damage|p2a: Starmie|75/100
|move|p1a: Cloyster|Toxic|p2a: Starmie
|-activate|p2a: Starmie|Substitute|[block] Toxic
|turn|2
|switch|p1a: Exeggutor|Exeggutor, M|100/100
|move|p2a: Starmie|Confuse Ray|p1a: Exeggutor
|-start|p1a: Exeggutor|confusion
|turn|3
|move|p2a: Starmie|Surf|p1a: Exeggutor
|turn|4
|switch|p2a: Snorlax|Snorlax, M|100/100
|turn|5
"""


BATON_PASS_LOG = """\
|player|p1|Alice|
|player|p2|Bob|
|gen|2
|tier|[Gen 2] OU
|start
|switch|p1a: Scizor|Scizor, M|100/100
|switch|p2a: Lapras|Lapras, M|100/100
|turn|1
|move|p1a: Scizor|Agility|p1a: Scizor
|-boost|p1a: Scizor|spe|2
|move|p2a: Lapras|Surf|p1a: Scizor
|-damage|p1a: Scizor|70/100
|turn|2
|move|p1a: Scizor|Baton Pass|p1a: Scizor
|switch|p1a: Espeon|Espeon, M|100/100|[from] Baton Pass
|move|p2a: Lapras|Surf|p1a: Espeon
|turn|3
"""


MEAN_LOOK_PASS_LOG = """\
|player|p1|Alice|
|player|p2|Bob|
|gen|2
|tier|[Gen 2] OU
|start
|switch|p1a: Snorlax|Snorlax, M|100/100
|switch|p2a: Umbreon|Umbreon, M|100/100
|turn|1
|move|p2a: Umbreon|Mean Look|p1a: Snorlax
|-activate|p1a: Snorlax|trapped
|move|p1a: Snorlax|Body Slam|p2a: Umbreon
|-damage|p2a: Umbreon|70/100
|turn|2
|move|p2a: Umbreon|Baton Pass|p2a: Umbreon
|switch|p2a: Rhydon|Rhydon, M|100/100|[from] Baton Pass
|move|p1a: Snorlax|Earthquake|p2a: Rhydon
|turn|3
"""


REST_SLEEP_LOG = """\
|player|p1|Alice|
|player|p2|Bob|
|gen|2
|tier|[Gen 2] OU
|start
|switch|p1a: Snorlax|Snorlax, M|100/100
|switch|p2a: Jolteon|Jolteon, M|100/100
|turn|1
|move|p1a: Snorlax|Rest|p1a: Snorlax
|-status|p1a: Snorlax|slp|[from] move: Rest
|-heal|p1a: Snorlax|100/100 slp|[silent]
|turn|2
|cant|p1a: Snorlax|slp
|move|p1a: Snorlax|Sleep Talk|p1a: Snorlax
|move|p1a: Snorlax|Double-Edge|p2a: Jolteon|[from] Sleep Talk
|turn|3
|cant|p1a: Snorlax|slp
|move|p1a: Snorlax|Sleep Talk|p1a: Snorlax
|move|p1a: Snorlax|Rest|p1a: Snorlax|[from] Sleep Talk
|-fail|p1a: Snorlax
|turn|4
"""


REST_WAKE_LOG = """\
|player|p1|Alice|
|player|p2|Bob|
|gen|2
|tier|[Gen 2] OU
|start
|switch|p1a: Snorlax|Snorlax, M|100/100
|switch|p2a: Jolteon|Jolteon, M|100/100
|turn|1
|move|p1a: Snorlax|Rest|p1a: Snorlax
|-status|p1a: Snorlax|slp|[from] move: Rest
|-heal|p1a: Snorlax|100/100 slp|[silent]
|turn|2
|cant|p1a: Snorlax|slp
|move|p1a: Snorlax|Sleep Talk|p1a: Snorlax
|move|p1a: Snorlax|Double-Edge|p2a: Jolteon|[from] Sleep Talk
|turn|3
|cant|p1a: Snorlax|slp
|move|p1a: Snorlax|Sleep Talk|p1a: Snorlax
|move|p1a: Snorlax|Double-Edge|p2a: Jolteon|[from] Sleep Talk
|turn|4
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

    def test_prompt_includes_public_species_for_nicknamed_pokemon(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nicknamed.log"
            path.write_text(NICKNAMED_LOG, encoding="utf-8")

            prompt = format_prompt(path, 1)

        self.assertIn("p2 / Bob: active Bastard (Snorlax) HP 100/100 healthy", prompt)
        self.assertIn("Bastard (Snorlax) 100/100 healthy; moves: no moves revealed", prompt)
        self.assertNotIn("Spikes", prompt)

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

    def test_reveal_includes_volatile_start_and_activation_lines(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "volatile.log"
            path.write_text(VOLATILE_LOG, encoding="utf-8")

            reveal = format_reveal(path, 1)

        self.assertIn("|-start|p2a: Starmie|Substitute", reveal)
        self.assertIn("|-activate|p2a: Starmie|Substitute|[block] Toxic", reveal)

    def test_prompt_carries_decision_relevant_volatiles(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "volatile.log"
            path.write_text(VOLATILE_LOG, encoding="utf-8")

            prompt = format_prompt(path, 3)

        self.assertIn("active Exeggutor HP 100/100 healthy; volatiles confusion", prompt)
        self.assertIn("active Starmie HP 75/100 healthy; volatiles Substitute", prompt)

    def test_switching_out_clears_decision_relevant_volatiles(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "volatile.log"
            path.write_text(VOLATILE_LOG, encoding="utf-8")

            prompt = format_prompt(path, 5)

        self.assertNotIn("Starmie 75/100 healthy; volatiles: Substitute", prompt)

    def test_baton_pass_carries_boosts_to_recipient(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "baton.log"
            path.write_text(BATON_PASS_LOG, encoding="utf-8")

            prompt = format_prompt(path, 3)

        self.assertIn("active Espeon HP 100/100 healthy; boosts spe+2", prompt)
        self.assertIn("Scizor 70/100 healthy; moves: Agility, Baton Pass", prompt)

    def test_prompt_carries_mean_look_trapping_through_baton_pass(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "mean_look.log"
            path.write_text(MEAN_LOOK_PASS_LOG, encoding="utf-8")

            prompt = format_prompt(path, 3)

        self.assertIn("active Snorlax HP 100/100 healthy; volatiles trapped", prompt)
        self.assertIn("active Rhydon HP 100/100 healthy", prompt)
        self.assertIn("Umbreon 70/100 healthy; moves: Baton Pass, Mean Look", prompt)

    def test_prompt_keeps_rest_counter_after_failed_sleeptalk_rest(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "rest_sleep.log"
            path.write_text(REST_SLEEP_LOG, encoding="utf-8")

            prompt = format_prompt(path, 4)

        self.assertIn("Rest sleep actions 2", prompt)
        self.assertIn("will wake and can act this prompted turn in GSC", prompt)

    def test_prompt_marks_rest_wake_action_after_two_sleep_actions(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "rest_wake.log"
            path.write_text(REST_WAKE_LOG, encoding="utf-8")

            prompt = format_prompt(path, 4)

        self.assertIn("Rest sleep actions 2", prompt)
        self.assertIn("will wake and can act this prompted turn in GSC", prompt)

    def test_summary_reports_players_and_turn_count(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "synthetic.log"
            path.write_text(SYNTHETIC_LOG, encoding="utf-8")

            summary = format_summary(path)

        self.assertIn("Format: Gen 2; tier: [Gen 2] OU", summary)
        self.assertIn("Players: p1=Alice; p2=Bob", summary)
        self.assertIn("Turns: 1-3 (3 turns)", summary)

    def test_side_prompt_includes_only_advised_side_known_roster(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "synthetic.log"
            path.write_text(SYNTHETIC_LOG, encoding="utf-8")

            prompt = format_side_prompt(path, 2, "p1")

        self.assertIn("Task: recommend only p1's move", prompt)
        self.assertIn("Golem; own shown moves: Earthquake", prompt)
        self.assertIn("Zapdos; own shown moves: Thunder", prompt)
        self.assertNotIn("Rest", prompt)

    def test_prompts_require_route_transaction_before_candidates(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "synthetic.log"
            path.write_text(SYNTHETIC_LOG, encoding="utf-8")

            public_prompt = format_prompt(path, 2)
            side_prompt = format_side_prompt(path, 2, "p1")

        expected = (
            "route transaction: their package -> our absorber/converter -> "
            "their next owner -> our punish"
        )
        self.assertIn(expected, public_prompt)
        self.assertIn(expected, side_prompt)

        comparison = (
            "compare candidates against active target -> next owner -> "
            "counter-owner after our handoff"
        )
        self.assertIn(comparison, public_prompt)
        self.assertIn(comparison, side_prompt)

        critical_ledger = (
            "critical ledger: sleep/wake counter, passed boosts/speed, "
            "self-KO or cash-out branch, and immediate lethal/miss/crit risk"
        )
        self.assertIn(critical_ledger, public_prompt)
        self.assertIn(critical_ledger, side_prompt)

        reset_denial = (
            "If recovery, hazards, removal, phazing, or sleep-turn actions can reset "
            "the route, compare reset-denial before damage."
        )
        self.assertIn(reset_denial, public_prompt)
        self.assertIn(reset_denial, side_prompt)

        top_three = "ranked top-three candidates"
        self.assertIn(top_three, public_prompt)
        self.assertIn(top_three, side_prompt)

        route_budget = (
            "Route-budget tiebreaker: state why #1 ranks above #2, what public "
            "fact would make #2 become #1, and the rejected safe/default line."
        )
        self.assertIn(route_budget, public_prompt)
        self.assertIn(route_budget, side_prompt)

        miss_tags = (
            "Score likely misses with route_budget, resource_identity, "
            "reset_loop, script_too_slow, branch_punish, and positive_selection."
        )
        self.assertIn(miss_tags, public_prompt)
        self.assertIn(miss_tags, side_prompt)


if __name__ == "__main__":
    unittest.main()
