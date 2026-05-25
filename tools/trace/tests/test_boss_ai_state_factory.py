from __future__ import annotations

import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from tools.trace import boss_ai_state_factory as factory
from tools.trace.boss_ai_state_factory import (
    BASE_REQUIRED_SYMBOLS,
    ROUTES,
    BossRoute,
    TrainerConstant,
    expected_trainer,
    parse_map_consts,
    parse_rgb_int,
    parse_simple_consts,
    parse_trainer_consts,
    route_ids_from_manifest,
    selected_routes,
    strip_asm_comment,
    trace_summary,
)


class ParseRgbIntTests(unittest.TestCase):
    def test_dollar_prefix_is_hex(self) -> None:
        self.assertEqual(parse_rgb_int("$ff"), 0xFF)
        self.assertEqual(parse_rgb_int("$0a"), 0x0A)

    def test_zero_x_prefix_is_hex_via_int_base_0(self) -> None:
        self.assertEqual(parse_rgb_int("0xff"), 0xFF)

    def test_decimal_is_decimal(self) -> None:
        self.assertEqual(parse_rgb_int("255"), 255)
        self.assertEqual(parse_rgb_int("0"), 0)

    def test_trailing_comma_is_stripped(self) -> None:
        self.assertEqual(parse_rgb_int("$ff,"), 0xFF)
        self.assertEqual(parse_rgb_int("12,"), 12)

    def test_surrounding_whitespace_is_stripped(self) -> None:
        self.assertEqual(parse_rgb_int("  $4a  "), 0x4A)


class StripAsmCommentTests(unittest.TestCase):
    def test_strips_after_semicolon(self) -> None:
        self.assertEqual(strip_asm_comment("const FOO ; comment"), "const FOO")

    def test_returns_empty_for_pure_comment(self) -> None:
        self.assertEqual(strip_asm_comment("; only comment"), "")

    def test_preserves_lines_without_comments(self) -> None:
        self.assertEqual(strip_asm_comment("    const BAR"), "const BAR")


class ParseSimpleConstsTests(unittest.TestCase):
    def test_event_flags_const_block_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "event_flags.asm"
            path.write_text(
                "; comment header\n"
                "const_def\n"
                "    const EVENT_ZERO   ; 0\n"
                "    const EVENT_ONE    ; 1\n"
                "    const_skip 2\n"
                "    const EVENT_FOUR   ; 4\n"
                "    const EVENT_FIVE   ; 5\n"
                "    const_next $10\n"
                "    const EVENT_HEX10  ; 16\n",
                encoding="utf-8",
            )
            consts = parse_simple_consts(path)
        self.assertEqual(consts["EVENT_ZERO"], 0)
        self.assertEqual(consts["EVENT_ONE"], 1)
        self.assertEqual(consts["EVENT_FOUR"], 4)
        self.assertEqual(consts["EVENT_FIVE"], 5)
        self.assertEqual(consts["EVENT_HEX10"], 0x10)

    def test_lines_before_const_def_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "x.asm"
            path.write_text(
                "    const BEFORE_BLOCK\n"
                "const_def 5\n"
                "    const FIRST\n",
                encoding="utf-8",
            )
            consts = parse_simple_consts(path)
        self.assertNotIn("BEFORE_BLOCK", consts)
        self.assertEqual(consts["FIRST"], 5)


class ParseMapConstsTests(unittest.TestCase):
    def test_newgroup_increments_group_and_resets_map(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "map_constants.asm"
            path.write_text(
                "newgroup JOHTO\n"
                "map_const VIOLET_GYM, 5, 4\n"
                "map_const AZALEA_GYM, 6, 4\n"
                "newgroup KANTO\n"
                "map_const PEWTER_GYM, 7, 4\n",
                encoding="utf-8",
            )
            maps = parse_map_consts(path)
        self.assertEqual(maps["VIOLET_GYM"], (1, 1))
        self.assertEqual(maps["AZALEA_GYM"], (1, 2))
        self.assertEqual(maps["PEWTER_GYM"], (2, 1))


class ParseTrainerConstsTests(unittest.TestCase):
    def test_parses_trainerclass_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "trainer_constants.asm"
            path.write_text(
                "trainerclass FALKNER\n"
                "    const FALKNER1\n"
                "trainerclass BUGSY\n"
                "    const BUGSY1\n"
                "    const BUGSY2\n",
                encoding="utf-8",
            )
            trainers = parse_trainer_consts(path)
        self.assertEqual(trainers[("FALKNER", "FALKNER1")], TrainerConstant(0, 1))
        self.assertEqual(trainers[("BUGSY", "BUGSY1")], TrainerConstant(1, 1))
        self.assertEqual(trainers[("BUGSY", "BUGSY2")], TrainerConstant(1, 2))


class RouteIdsFromManifestTests(unittest.TestCase):
    def test_missing_manifest_returns_all_route_ids(self) -> None:
        ids = route_ids_from_manifest(Path("absent.json"))
        self.assertEqual(set(ids), set(ROUTES))

    def test_manifest_filters_to_known_routes_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            manifest = Path(tempdir) / "live_capture_manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "captures": [
                            {"id": "morty"},
                            {"id": "not_a_real_route"},
                            {"id": "jasmine"},
                            "garbage-non-dict",
                        ]
                    }
                ),
                encoding="utf-8",
            )
            ids = route_ids_from_manifest(manifest)
        self.assertEqual(ids, ["morty", "jasmine"])


class TraceSummaryTests(unittest.TestCase):
    def test_emits_chosen_plan_top_and_scores_lowercase_hex(self) -> None:
        values = {
            "wBossAITraceChosenMove": [0x05],
            "wBossAITracePlanId": [0x02],
            "wBossAITraceTopMoves": [0xAA, 0x10, 0x00],
            "wBossAITraceTopScores": [0x14, 0x0F, 0x00],
        }
        summary = trace_summary(values)
        self.assertEqual(
            summary,
            "chosen=05 plan=02 top=aa 10 00 scores=14 0f 00",
        )


class ExpectedTrainerTests(unittest.TestCase):
    def test_returns_constant_when_class_and_id_are_present(self) -> None:
        route = ROUTES["falkner"]
        trainers = {
            ("FALKNER", "FALKNER1"): TrainerConstant(0, 1),
        }
        self.assertEqual(expected_trainer(route, trainers), TrainerConstant(0, 1))

    def test_missing_entry_fails_with_named_message(self) -> None:
        route = ROUTES["falkner"]
        stderr_buffer = io.StringIO()
        with redirect_stderr(stderr_buffer):
            with self.assertRaises(SystemExit):
                expected_trainer(route, {})
        self.assertIn("missing trainer constant: FALKNER, FALKNER1", stderr_buffer.getvalue())


class SelectedRoutesTests(unittest.TestCase):
    def _ns(self, **kwargs) -> argparse.Namespace:
        return argparse.Namespace(**kwargs)

    def test_boss_flag_selects_single_route(self) -> None:
        args = self._ns(boss="morty", all=False, manifest=Path("absent.json"))
        routes = selected_routes(args)
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0].capture_id, "morty")

    def test_all_flag_returns_routes_in_manifest_order(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            manifest = Path(tempdir) / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {"captures": [{"id": "jasmine"}, {"id": "clair"}]}
                ),
                encoding="utf-8",
            )
            args = self._ns(boss="falkner", all=True, manifest=manifest)
            routes = selected_routes(args)
        self.assertEqual([r.capture_id for r in routes], ["jasmine", "clair"])

    def test_all_flag_with_missing_manifest_yields_every_route(self) -> None:
        args = self._ns(boss="falkner", all=True, manifest=Path("absent.json"))
        routes = selected_routes(args)
        self.assertEqual({r.capture_id for r in routes}, set(ROUTES))


class RoutesDataIntegrityTests(unittest.TestCase):
    def test_route_key_matches_capture_id(self) -> None:
        for key, route in ROUTES.items():
            self.assertEqual(key, route.capture_id, f"key/capture_id drift: {key}")

    def test_all_routes_have_nonempty_trainer_identity(self) -> None:
        for key, route in ROUTES.items():
            with self.subTest(key=key):
                self.assertTrue(route.trainer_class)
                self.assertTrue(route.trainer_id)
                self.assertTrue(route.map_name)
                self.assertTrue(route.clear_events)

    def test_base_required_symbols_is_sorted(self) -> None:
        # Defends against silent reordering that would change the failure-message
        # column ordering when symbols are missing.
        self.assertEqual(list(BASE_REQUIRED_SYMBOLS), sorted(BASE_REQUIRED_SYMBOLS))


class BossRouteDataclassTests(unittest.TestCase):
    def test_defaults_match_documented_baseline(self) -> None:
        route = BossRoute(
            capture_id="x",
            map_name="MAP",
            player_x=1,
            player_y=2,
            trainer_class="CLS",
            trainer_id="CLS1",
            clear_events=(),
        )
        self.assertEqual(route.set_events, ())
        self.assertEqual(route.scene_values, ())
        self.assertEqual(route.prime_buttons, ("up", "a"))
        self.assertEqual(route.input_wait_frames, 45)
        self.assertEqual(route.max_a_presses, 120)
        self.assertTrue(route.clear_badges)

    def test_route_is_frozen(self) -> None:
        route = ROUTES["morty"]
        with self.assertRaises(Exception):
            route.player_x = 99  # type: ignore[misc]


class ModuleConstantsTests(unittest.TestCase):
    def test_event_flags_path_points_at_constants_dir(self) -> None:
        self.assertTrue(factory.EVENT_FLAGS.name.endswith("event_flags.asm"))
        self.assertEqual(factory.EVENT_FLAGS.parent.name, "constants")


if __name__ == "__main__":
    unittest.main()
