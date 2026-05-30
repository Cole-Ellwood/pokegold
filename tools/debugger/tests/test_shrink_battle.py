import json
import tempfile
import unittest
from pathlib import Path

from tools.debugger.shrink_battle import (
    format_report,
    report_json,
    shrink_battle_scenario,
    shrink_battle_scenario_path,
)


def canonical_scenario() -> dict:
    return {
        "id": "ag_nn_battle_repro",
        "family": "battle",
        "enemy_party": [
            {"species": "PIDGEY", "moves": ["GUST", "SAND_ATTACK"]},
            {"species": "MILTANK", "moves": ["TACKLE", "ROLLOUT", "MILK_DRINK"]},
            {"species": "ZUBAT", "moves": ["LEECH_LIFE"]},
            {"species": "HAUNTER", "moves": ["LICK", "MEAN_LOOK", "CURSE"]},
            {"species": "RATTATA", "moves": ["QUICK_ATTACK"]},
            {"species": "GEODUDE", "moves": ["DEFENSE_CURL", "ROCK_THROW"]},
        ],
        "modifiers": ["rain", "critical_window", "badge_boost_noise"],
    }


def keeps_required_battle_fact(scenario: dict) -> bool:
    party = scenario.get("enemy_party")
    if not isinstance(party, list):
        return False
    by_species = {
        str(mon.get("species")): mon
        for mon in party
        if isinstance(mon, dict)
    }
    miltank = by_species.get("MILTANK")
    haunter = by_species.get("HAUNTER")
    if not miltank or not haunter:
        return False
    return (
        "ROLLOUT" in miltank.get("moves", [])
        and "MEAN_LOOK" in haunter.get("moves", [])
        and "critical_window" in scenario.get("modifiers", [])
    )


class BattleShrinkerTests(unittest.TestCase):
    def test_canonical_reduces_six_pokemon_scenario_to_two_that_still_triggers(self) -> None:
        report = shrink_battle_scenario(canonical_scenario(), predicate=keeps_required_battle_fact)
        shrunk = report["shrunk_scenario"]
        species = [mon["species"] for mon in shrunk["enemy_party"]]
        moves_by_species = {mon["species"]: mon["moves"] for mon in shrunk["enemy_party"]}

        self.assertTrue(report["valid"])
        self.assertTrue(report["preserved"])
        self.assertEqual(report["original_counts"]["pokemon_count"], 6)
        self.assertLessEqual(report["shrunk_counts"]["pokemon_count"], 2)
        self.assertEqual(set(species), {"MILTANK", "HAUNTER"})
        self.assertEqual(moves_by_species["MILTANK"], ["ROLLOUT"])
        self.assertEqual(moves_by_species["HAUNTER"], ["MEAN_LOOK"])
        self.assertEqual(shrunk["modifiers"], ["critical_window"])
        self.assertGreater(report["reduction_step_count"], 0)
        self.assertIn("enemy_party", {step["path"] for step in report["reduction_trace"]})
        self.assertIn("modifiers", {step["path"] for step in report["reduction_trace"]})
        self.assertIn("enemy_party[0].moves", {step["path"] for step in report["reduction_trace"]})

    def test_writes_minimized_scenario_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = shrink_battle_scenario(
                canonical_scenario(),
                predicate=keeps_required_battle_fact,
                out_scenario="shrunk/battle.json",
                root=root,
            )
            out_path = root / "shrunk" / "battle.json"
            written = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertTrue(report["out_scenario"]["written"])
        self.assertEqual(report["out_scenario"]["path"], "shrunk/battle.json")
        self.assertEqual(len(written["enemy_party"]), 2)

    def test_loads_jsonl_by_scenario_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "scenarios.jsonl"
            path.write_text(
                json.dumps({"id": "noise", "enemy_party": [{"species": "PIDGEY"}]})
                + "\n"
                + json.dumps(canonical_scenario())
                + "\n",
                encoding="utf-8",
            )
            report = shrink_battle_scenario_path(
                "scenarios.jsonl",
                scenario_id="ag_nn_battle_repro",
                predicate=keeps_required_battle_fact,
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["shrunk_scenario"]["id"], "ag_nn_battle_repro")
        self.assertLessEqual(report["shrunk_counts"]["pokemon_count"], 2)

    def test_baseline_must_reproduce(self) -> None:
        report = shrink_battle_scenario(
            {"enemy_party": [{"species": "PIDGEY", "moves": ["GUST"]}]},
            predicate=keeps_required_battle_fact,
        )

        self.assertFalse(report["valid"])
        self.assertFalse(report["preserved"])
        self.assertIn("baseline battle scenario does not reproduce", "\n".join(report["errors"]))
        self.assertEqual(report["reduction_step_count"], 0)

    def test_missing_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = shrink_battle_scenario_path(
                "missing.json",
                predicate=keeps_required_battle_fact,
                root=Path(tmp),
            )

        self.assertFalse(report["valid"])
        self.assertIn("missing battle scenario", "\n".join(report["errors"]))

    def test_format_and_json_helpers_expose_counts(self) -> None:
        report = shrink_battle_scenario(canonical_scenario(), predicate=keeps_required_battle_fact)
        text = format_report(report)
        encoded = json.loads(report_json(report))

        self.assertIn("pokemon=6->2", text)
        self.assertEqual(encoded["kind"], "unified_debugger_shrink_battle")


if __name__ == "__main__":
    unittest.main()
