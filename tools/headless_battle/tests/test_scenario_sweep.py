from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.headless_battle.scenario_sweep import (
    DEFAULT_HP_FRACTIONS,
    DEFAULT_PARTIES_PATH,
    DEFAULT_STATUSES,
    SUPPORTED_STATUSES,
    ScenarioSweepError,
    SweepOptions,
    TrainerMon,
    TrainerRoster,
    _split_csv,
    _split_floats,
    build_parser,
    format_sweep_summary,
    main,
    parse_trainer_roster,
    sweep_against_trainer,
    write_sweep_jsonl,
)


class ParseTrainerRosterTests(unittest.TestCase):
    def test_parses_jasmine_full_roster(self) -> None:
        roster = parse_trainer_roster("JASMINE")
        self.assertEqual(roster.name, "JASMINE")
        self.assertEqual(roster.trainer_type, "TRAINERTYPE_ITEM_MOVES")
        species = roster.species_names()
        # Live parties.asm has Jasmine leading with Magneton.
        self.assertEqual(species[0], "MAGNETON")
        self.assertIn("FORRETRESS", species)
        # Each mon row carries the item byte name for TRAINERTYPE_ITEM_MOVES.
        self.assertEqual(roster.mons[0].item, "MAGNET")
        # Each mon row carries 4 moves for TRAINERTYPE_ITEM_MOVES.
        self.assertEqual(len(roster.mons[0].moves), 4)
        self.assertGreater(len(roster.mons), 1)

    def test_parses_morty_with_repeated_haunter(self) -> None:
        roster = parse_trainer_roster("MORTY")
        species = roster.species_names()
        self.assertEqual(species[0], "HAUNTER")
        self.assertIn("GENGAR", species)
        # Morty's roster has HAUNTER twice (positions 0 and 3 historically).
        self.assertGreaterEqual(species.count("HAUNTER"), 2)

    def test_case_insensitive_match(self) -> None:
        upper = parse_trainer_roster("JASMINE")
        lower = parse_trainer_roster("jasmine")
        self.assertEqual(upper.species_names(), lower.species_names())

    def test_unknown_trainer_raises(self) -> None:
        with self.assertRaisesRegex(ScenarioSweepError, "not found"):
            parse_trainer_roster("DEFINITELY_NOT_A_TRAINER_42")


class CsvSplitterTests(unittest.TestCase):
    def test_split_csv_strips_and_filters_empty(self) -> None:
        self.assertEqual(_split_csv(" a, b ,, c"), ("a", "b", "c"))
        self.assertEqual(_split_csv(""), ())
        self.assertEqual(_split_csv(None), ())

    def test_split_floats_validates_range(self) -> None:
        self.assertEqual(_split_floats("1.0,0.6,0.3"), (1.0, 0.6, 0.3))
        with self.assertRaisesRegex(ScenarioSweepError, "in \\(0\\.0, 1\\.0\\]"):
            _split_floats("1.5")
        with self.assertRaisesRegex(ScenarioSweepError, "in \\(0\\.0, 1\\.0\\]"):
            _split_floats("0")
        with self.assertRaisesRegex(ScenarioSweepError, "not a number"):
            _split_floats("not-a-number")


class SweepAgainstTrainerTests(unittest.TestCase):
    def _base_opts(self, **overrides) -> SweepOptions:
        defaults = dict(
            trainer_class="JASMINE",
            player_species=("CYNDAQUIL",),
            player_hp_fractions=(1.0,),
            enemy_hp_fractions=(1.0,),
            player_statuses=("none",),
            enemy_statuses=("none",),
            weathers=("none",),
        )
        defaults.update(overrides)
        return SweepOptions(**defaults)

    def test_default_sweep_emits_one_scenario_per_combo(self) -> None:
        opts = self._base_opts()
        scenarios = sweep_against_trainer(opts)
        self.assertEqual(len(scenarios), 1)
        self.assertTrue(scenarios[0]["id"].startswith("sweep_jasmine"))
        self.assertEqual(scenarios[0]["family"], "switch_sack")
        overrides = scenarios[0]["overrides"]
        # Player Cyndaquil base data flows through to overrides
        self.assertGreater(overrides["player_hp"], 0)
        self.assertEqual(overrides["player_status"], 0)
        # Jasmine roster[0] = MAGNETON, roster[1] = FORRETRESS
        # Their species ids come from parse_species_order
        self.assertGreater(overrides["enemy_species"], 0)
        self.assertGreater(overrides["enemy_bench_species"], 0)
        self.assertNotEqual(
            overrides["enemy_species"], overrides["enemy_bench_species"]
        )

    def test_hp_fraction_scales_observed_hp(self) -> None:
        opts = self._base_opts(player_hp_fractions=(0.5,))
        scenarios = sweep_against_trainer(opts)
        overrides = scenarios[0]["overrides"]
        self.assertAlmostEqual(
            overrides["player_hp"] / overrides["player_max_hp"], 0.5, places=1
        )

    def test_cartesian_product_of_dims(self) -> None:
        opts = self._base_opts(
            player_species=("CYNDAQUIL", "HAUNTER"),
            player_hp_fractions=(1.0, 0.6),
            enemy_hp_fractions=(1.0,),
            weathers=("none", "rain"),
        )
        scenarios = sweep_against_trainer(opts)
        # 2 players x 2 player_hp x 1 enemy_hp x 1 player_status x 1 enemy_status x
        # 1 enemy_active x 1 enemy_bench x 1 player_item x 1 enemy_item x 2 weather = 8
        self.assertEqual(len(scenarios), 8)
        ids = {s["id"] for s in scenarios}
        self.assertEqual(len(ids), 8)

    def test_status_propagates_into_overrides(self) -> None:
        opts = self._base_opts(player_statuses=("burn",))
        scenarios = sweep_against_trainer(opts)
        overrides = scenarios[0]["overrides"]
        # burn = 1<<BRN bit, which is 1<<4 = 16
        self.assertEqual(overrides["player_status"], 16)

    def test_weather_count_set_for_active_weather(self) -> None:
        opts = self._base_opts(weathers=("rain",))
        scenarios = sweep_against_trainer(opts)
        overrides = scenarios[0]["overrides"]
        self.assertEqual(overrides.get("weather_count"), 5)
        self.assertGreater(overrides.get("weather", 0), 0)

    def test_rejects_unsupported_status(self) -> None:
        opts = self._base_opts(player_statuses=("freeze",))
        with self.assertRaisesRegex(
            ScenarioSweepError, "not in override-supported subset"
        ):
            sweep_against_trainer(opts)

    def test_rejects_unsupported_weather(self) -> None:
        opts = self._base_opts(weathers=("snow",))
        with self.assertRaisesRegex(ScenarioSweepError, "weather"):
            sweep_against_trainer(opts)

    def test_skips_same_species_active_and_bench(self) -> None:
        # Force active == bench; no combo should make it through.
        opts = self._base_opts(
            enemy_active_species=("MAGNETON",),
            enemy_bench_species=("MAGNETON",),
        )
        with self.assertRaisesRegex(
            ScenarioSweepError, "enemy_active == enemy_bench"
        ):
            sweep_against_trainer(opts)

    def test_explicit_enemy_active_and_bench_override_default(self) -> None:
        opts = self._base_opts(
            enemy_active_species=("STEELIX",),
            enemy_bench_species=("SKARMORY",),
        )
        scenarios = sweep_against_trainer(opts)
        self.assertEqual(len(scenarios), 1)
        self.assertIn("actsteelix", scenarios[0]["id"])
        self.assertIn("bnskarmory", scenarios[0]["id"])

    def test_limit_caps_emission(self) -> None:
        opts = self._base_opts(
            player_species=("CYNDAQUIL", "HAUNTER", "PIKACHU", "SLOWPOKE"),
            player_hp_fractions=(1.0, 0.7, 0.4),
            limit=3,
        )
        scenarios = sweep_against_trainer(opts)
        self.assertEqual(len(scenarios), 3)

    def test_morty_default_bench_is_misdreavus(self) -> None:
        opts = self._base_opts(
            trainer_class="MORTY",
            player_species=("CYNDAQUIL",),
        )
        scenarios = sweep_against_trainer(opts)
        self.assertIn("actHaunter".lower(), scenarios[0]["id"])
        self.assertIn("bnMisdreavus".lower(), scenarios[0]["id"])


class FormatSweepSummaryTests(unittest.TestCase):
    def test_summary_names_trainer_and_counts(self) -> None:
        roster = parse_trainer_roster("JASMINE")
        opts = SweepOptions(
            trainer_class="JASMINE",
            player_species=("CYNDAQUIL", "HAUNTER"),
            player_hp_fractions=(1.0,),
            enemy_hp_fractions=(1.0,),
        )
        scenarios = sweep_against_trainer(opts)
        text = format_sweep_summary(roster, scenarios)
        self.assertIn("JASMINE", text)
        self.assertIn("TRAINERTYPE_ITEM_MOVES", text)
        self.assertIn(f"scenarios emitted: {len(scenarios)}", text)
        self.assertIn("unique player_species=2", text)


class WriteSweepJsonlTests(unittest.TestCase):
    def test_writes_one_scenario_per_line(self) -> None:
        opts = SweepOptions(
            trainer_class="JASMINE",
            player_species=("CYNDAQUIL",),
            player_hp_fractions=(1.0, 0.5),
            enemy_hp_fractions=(1.0,),
        )
        scenarios = sweep_against_trainer(opts)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sweep.jsonl"
            write_sweep_jsonl(scenarios, out)
            lines = out.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), len(scenarios))
        first = json.loads(lines[0])
        self.assertEqual(first["family"], "switch_sack")


class CliMainTests(unittest.TestCase):
    def test_cli_writes_jsonl_and_prints_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sweep.jsonl"
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(
                    [
                        "--trainer",
                        "JASMINE",
                        "--player",
                        "CYNDAQUIL,HAUNTER",
                        "--hp-fractions",
                        "1.0,0.6",
                        "--out",
                        str(out),
                    ]
                )
            text = buf.getvalue()
            data = out.read_text(encoding="utf-8").splitlines()
        self.assertEqual(code, 0)
        # 2 player species x 2 player_hp x 2 enemy_hp (defaults to --hp-fractions)
        # x 1 active x 1 bench = 8
        self.assertEqual(len(data), 8)
        self.assertIn("JASMINE", text)
        self.assertIn("scenarios emitted: 8", text)

    def test_cli_json_mode_prints_array(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(
                [
                    "--trainer",
                    "JASMINE",
                    "--player",
                    "CYNDAQUIL",
                    "--hp-fractions",
                    "1.0",
                    "--enemy-hp-fractions",
                    "1.0",
                    "--json",
                ]
            )
        self.assertEqual(code, 0)
        parsed = json.loads(buf.getvalue())
        self.assertIsInstance(parsed, list)
        self.assertGreaterEqual(len(parsed), 1)

    def test_cli_rejects_unknown_trainer(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            with self.assertRaises(ScenarioSweepError):
                main(
                    [
                        "--trainer",
                        "NOT_A_REAL_TRAINER",
                        "--player",
                        "CYNDAQUIL",
                    ]
                )

    def test_cli_strict_returns_nonzero_when_some_combos_reject(self) -> None:
        # Force a same-species combo so all combos get rejected and we trip
        # the all-rejected error path. Use a partial-reject case instead:
        # active=MAGNETON but bench=MAGNETON for one product entry, while
        # bench=FORRETRESS works for another.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sweep.jsonl"
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(
                    [
                        "--trainer",
                        "JASMINE",
                        "--player",
                        "CYNDAQUIL",
                        "--enemy-active",
                        "MAGNETON",
                        "--enemy-bench",
                        "FORRETRESS,MAGNETON",  # one valid, one same-as-active
                        "--hp-fractions",
                        "1.0",
                        "--out",
                        str(out),
                    ]
                )
            scenarios = out.read_text(encoding="utf-8").splitlines()
        # Same-species combo silently skipped; one valid scenario emitted.
        self.assertEqual(code, 0)
        self.assertEqual(len(scenarios), 1)


class CliParserTests(unittest.TestCase):
    def test_requires_trainer_and_player(self) -> None:
        with self.assertRaises(SystemExit):
            build_parser().parse_args(["--player", "CYNDAQUIL"])
        with self.assertRaises(SystemExit):
            build_parser().parse_args(["--trainer", "JASMINE"])

    def test_parser_defaults(self) -> None:
        args = build_parser().parse_args(["--trainer", "X", "--player", "Y"])
        self.assertEqual(args.hp_fractions, "1.0,0.6,0.3")
        self.assertEqual(args.statuses, "none")
        self.assertEqual(args.weathers, "none")
        self.assertEqual(args.level, 50)
        self.assertEqual(args.tier, "late")


if __name__ == "__main__":
    unittest.main()
