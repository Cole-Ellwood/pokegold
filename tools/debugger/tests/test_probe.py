from __future__ import annotations

import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.debugger.probe import (
    build_probe_list_report,
    build_probe_stats_report,
    declare_probe,
    main,
    reset_probes,
)


def write_symbol_table(root: Path) -> None:
    (root / "pokegold.sym").write_text(
        "01:5A00 BattleCommand_DamageCalc\n"
        "02:4100 BossAI_Choose\n",
        encoding="utf-8",
    )


def write_trace(path: Path) -> None:
    events = [
        {"pc_bank_address": "01:5A00", "pc_label": "BattleCommand_DamageCalc", "frame": 2, "seq": 0},
        {"pc_bank_address": "02:4100", "pc_label": "BossAI_Choose", "frame": 4, "seq": 1},
        {"pc_bank_address": "01:5A00", "pc_label": "BattleCommand_DamageCalc+3", "frame": 8, "seq": 2},
    ]
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")


class ProbeTests(unittest.TestCase):
    def test_probe_declare_dedupes_by_name(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_symbol_table(root)
            declare_probe(name="damage_calc_entry", pc="BattleCommand_DamageCalc", root=root)
            declare_probe(name="damage_calc_entry", pc="02:4100", root=root)

            report = build_probe_list_report(root=root)

        self.assertTrue(report["valid"], report)
        self.assertEqual(report["row_count"], 2)
        self.assertEqual(report["active_probe_count"], 1)
        self.assertEqual(report["probes"][0]["target"]["bank_address"], "02:4100")

    def test_probe_stats_against_golden_trace(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_symbol_table(root)
            trace = root / "trace.jsonl"
            write_trace(trace)
            declare_probe(name="damage_calc_entry", pc="BattleCommand_DamageCalc", root=root)

            report = build_probe_stats_report(traces=("trace.jsonl",), root=root)

        self.assertTrue(report["valid"], report)
        stats = report["stats"][0]
        self.assertEqual(stats["name"], "damage_calc_entry")
        self.assertEqual(stats["fire_count"], 2)
        self.assertEqual(stats["first_frame"], 2)
        self.assertEqual(stats["last_frame"], 8)
        self.assertEqual(stats["average_inter_fire_interval"], 6)

    def test_probe_stats_match_bank_address(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "trace.jsonl"
            write_trace(trace)
            declare_probe(name="boss_ai_choose", pc="02:4100", root=root)

            report = build_probe_stats_report(traces=(trace,), root=root)

        stats = report["stats"][0]
        self.assertEqual(stats["fire_count"], 1)
        self.assertEqual(stats["sample_matches"][0]["pc_label"], "BossAI_Choose")

    def test_probe_stats_accepts_single_json_event_object(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_symbol_table(root)
            trace = root / "single.json"
            trace.write_text(
                json.dumps(
                    {
                        "pc_bank_address": "01:5A00",
                        "pc_label": "BattleCommand_DamageCalc",
                        "frame": 2,
                        "seq": 0,
                    }
                ),
                encoding="utf-8",
            )
            declare_probe(name="damage_calc_entry", pc="BattleCommand_DamageCalc", root=root)

            report = build_probe_stats_report(traces=("single.json",), root=root)

        self.assertTrue(report["valid"], report)
        self.assertEqual(report["event_count"], 1)
        self.assertEqual(report["stats"][0]["fire_count"], 1)

    def test_probe_cli_declares_and_stats_json(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_symbol_table(root)
            trace = root / "trace.jsonl"
            store = root / "probes.jsonl"
            write_trace(trace)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                declare_code = main(
                    [
                        "declare",
                        "--name",
                        "damage_calc_entry",
                        "--pc",
                        "BattleCommand_DamageCalc",
                        "--store",
                        str(store),
                        "--symbols",
                        str(root / "pokegold.sym"),
                        "--json",
                    ]
                )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                stats_code = main(["stats", "--trace", str(trace), "--store", str(store), "--json"])
            payload = json.loads(stdout.getvalue())

        self.assertEqual(declare_code, 0)
        self.assertEqual(stats_code, 0)
        self.assertEqual(payload["stats"][0]["fire_count"], 2)

    def test_probe_reset_clears_store(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_symbol_table(root)
            declare_probe(name="damage_calc_entry", pc="BattleCommand_DamageCalc", root=root)

            reset = reset_probes(root=root)
            listed = build_probe_list_report(root=root)

        self.assertTrue(reset["valid"])
        self.assertEqual(reset["cleared_row_count"], 1)
        self.assertEqual(listed["active_probe_count"], 0)

    def test_probe_stats_missing_trace_fails_closed(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_symbol_table(root)
            declare_probe(name="damage_calc_entry", pc="BattleCommand_DamageCalc", root=root)

            report = build_probe_stats_report(traces=("missing.jsonl",), root=root)

        self.assertFalse(report["valid"])
        self.assertIn("missing trace", report["errors"][0])

    def test_probe_stats_requires_a_trace(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_symbol_table(root)
            declare_probe(name="damage_calc_entry", pc="BattleCommand_DamageCalc", root=root)

            report = build_probe_stats_report(traces=(), root=root)

        self.assertFalse(report["valid"])
        self.assertIn("at least one --trace is required", report["errors"])

    def test_probe_stats_malformed_trace_fails_closed(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_symbol_table(root)
            trace = root / "trace.jsonl"
            trace.write_text('{"pc_bank_address":"01:5A00"\n', encoding="utf-8")
            declare_probe(name="damage_calc_entry", pc="BattleCommand_DamageCalc", root=root)

            report = build_probe_stats_report(traces=("trace.jsonl",), root=root)

        self.assertFalse(report["valid"])
        self.assertIn("invalid JSON", report["errors"][0])


if __name__ == "__main__":
    unittest.main()
