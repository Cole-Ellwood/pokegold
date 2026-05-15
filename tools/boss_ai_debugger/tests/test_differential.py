from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.differential import build_differential_report
from tools.boss_ai_debugger.generators import write_jsonl


def write_unit_contribution_trace(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "source": "trace_rom_pyboy_hooks",
                "save_state": "route:unit",
                "event_count": 1,
                "changed_event_count": 1,
                "trace_basis": {},
                "chosen": {},
                "events": [
                    {
                        "changed": True,
                        "operation": "encourage_score",
                        "candidate": {"kind": "move", "slot_index": 0, "move_id": 57},
                        "source": {
                            "rule_id": "move.unit_trace_rule",
                            "classification": "public_info",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def write_rom_contribution_trace(path: Path, events: list[dict]) -> None:
    path.write_text(
        json.dumps(
            {
                "source": "trace_rom_pyboy_hooks",
                "save_state": "scenario:unit",
                "event_count": len(events),
                "changed_event_count": len(events),
                "trace_basis": {},
                "chosen": {},
                "events": events,
            }
        ),
        encoding="utf-8",
    )


def write_python_contribution_trace(path: Path, events: list[dict]) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source": "python_scenario_contributions",
                "trace_count": 1,
                "event_count": len(events),
                "changed_event_count": len(events),
                "covered_rule_count": len({event["rule_id"] for event in events}),
                "covered_rule_ids": sorted({event["rule_id"] for event in events}),
                "traces": [
                    {
                        "trace_id": "unit",
                        "scenario_id": "unit",
                        "source": "python_scenario",
                        "event_count": len(events),
                        "changed_event_count": len(events),
                        "events": events,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def contribution_event(rule_id: str, delta: int, *, slot_index: int = 0) -> dict:
    return {
        "changed": True,
        "operation": "unit_delta",
        "delta": delta,
        "candidate": {
            "kind": "move",
            "slot_index": slot_index,
            "move_id": 57,
            "move_name": "SURF",
        },
        "source": {
            "rule_id": rule_id,
            "classification": "public_info",
        },
        "rule_id": rule_id,
    }


class DifferentialTests(unittest.TestCase):
    def test_policy_mismatch_is_reported(self) -> None:
        scenario = {
            "id": "policy_case",
            "tier": "late",
            "moves": [
                {"id": "bad_top", "name": "Bad Top", "deltas": [{"rule": "top", "delta": -4}]},
                {"id": "wanted", "name": "Wanted"},
            ],
            "expectation": {
                "best_action_ids": ["wanted"],
                "bad_action_ids": ["bad_top"],
                "policy_tags": ["unit"],
            },
        }

        report = build_differential_report(scenarios=[scenario])

        self.assertEqual(report["mismatch_count"], 1)
        self.assertEqual(
            report["mismatches"][0]["class"],
            "policy_preference_mismatch",
        )

    def test_trace_selector_mismatch_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "boss_live.txt"
            trace.write_text(
                "\n".join(
                    [
                        "boss=Exact",
                        "tier=3",
                        "move_ids=1,2,3,0",
                        "move_scores=20,20,20,80",
                        "chosen_id=3",
                        "chosen_slot=2",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_differential_report(trace_paths=[trace])

        self.assertEqual(report["mismatch_class_counts"], {"selector_mismatch": 1})
        self.assertEqual(report["mismatches"][0]["status"], "confirmed")

    def test_rom_contribution_trace_is_summarized_without_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "rom_contribution.json"
            write_unit_contribution_trace(trace)

            report = build_differential_report(
                rom_contribution_trace_paths=[trace],
            )

        self.assertEqual(report["mismatch_count"], 0)
        self.assertEqual(
            report["rom_contribution_summary"]["covered_rule_ids"],
            ["move.unit_trace_rule"],
        )

    def test_contribution_comparison_reports_rule_classes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rom_trace = Path(tmp) / "rom_contribution.json"
            python_trace = Path(tmp) / "python_contribution.json"
            write_rom_contribution_trace(
                rom_trace,
                [
                    contribution_event("move.shared_delta", 5),
                    contribution_event("move.only_rom", 3, slot_index=1),
                ],
            )
            write_python_contribution_trace(
                python_trace,
                [
                    contribution_event("move.shared_delta", 2),
                    contribution_event("move.only_python", 4, slot_index=2),
                ],
            )

            report = build_differential_report(
                rom_contribution_trace_paths=[rom_trace],
                python_contribution_trace_paths=[python_trace],
            )

        self.assertEqual(report["contribution_comparison"]["matched_trace_count"], 1)
        self.assertEqual(
            report["mismatch_class_counts"],
            {
                "missing_python_rule": 1,
                "missing_rom_rule": 1,
                "rule_delta_mismatch": 1,
            },
        )
        self.assertEqual(report["mismatch_count"], 3)

    def test_contribution_comparison_accepts_in_memory_rom_reports(self) -> None:
        rom_report = {
            "source": "trace_rom_pyboy_hooks",
            "trace_id": "unit",
            "event_count": 1,
            "changed_event_count": 1,
            "trace_basis": {},
            "chosen": {},
            "events": [contribution_event("move.shared_delta", 5)],
        }
        with tempfile.TemporaryDirectory() as tmp:
            python_trace = Path(tmp) / "python_contribution.json"
            write_python_contribution_trace(
                python_trace,
                [contribution_event("move.shared_delta", 5)],
            )

            report = build_differential_report(
                rom_contribution_reports=[rom_report],
                python_contribution_trace_paths=[python_trace],
            )

        self.assertEqual(report["contribution_comparison"]["matched_trace_count"], 1)
        self.assertEqual(report["contribution_comparison"]["mismatch_count"], 0)

    def test_scenario_policy_deltas_are_not_treated_as_rom_mirror_rules(self) -> None:
        scenario = {
            "id": "unit",
            "tier": "late",
            "moves": [
                {
                    "id": "policy_line",
                    "name": "Policy Line",
                    "deltas": [{"rule": "policy_only_delta", "delta": -4}],
                }
            ],
        }
        rom_report = {
            "source": "trace_rom_pyboy_hooks",
            "trace_id": "unit",
            "event_count": 0,
            "changed_event_count": 0,
            "trace_basis": {},
            "chosen": {},
            "events": [],
        }

        report = build_differential_report(
            scenarios=[scenario],
            rom_contribution_reports=[rom_report],
        )

        self.assertEqual(report["contribution_comparison"]["matched_trace_count"], 0)
        self.assertEqual(report["contribution_comparison"]["mismatch_count"], 0)

    def test_cli_diff_writes_json(self) -> None:
        scenario = {
            "id": "cli_policy_case",
            "tier": "late",
            "moves": [
                {"id": "bad_top", "name": "Bad Top", "deltas": [{"rule": "top", "delta": -4}]},
                {"id": "wanted", "name": "Wanted"},
            ],
            "expectation": {"best_action_ids": ["wanted"]},
        }
        with tempfile.TemporaryDirectory() as tmp:
            scenarios_path = Path(tmp) / "scenarios.jsonl"
            contribution_trace = Path(tmp) / "rom_contribution.json"
            out = Path(tmp) / "diff.json"
            write_jsonl([scenario], scenarios_path)
            write_unit_contribution_trace(contribution_trace)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "diff",
                        "--scenarios",
                        str(scenarios_path),
                        "--rom-contribution-trace",
                        str(contribution_trace),
                        "--json-out",
                        str(out),
                    ]
                )
            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["mismatch_count"], 1)
        self.assertEqual(data["rom_contribution_summary"]["covered_rule_count"], 1)
        self.assertIn("differential report", stdout.getvalue())

    def test_cli_python_contribution_trace_writes_json(self) -> None:
        scenario = {
            "id": "cli_contribution_case",
            "tier": "late",
            "moves": [
                {"id": "a", "name": "A", "lookahead_delta": 3},
                {"id": "b", "name": "B", "lookahead_delta": 0},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            scenarios_path = Path(tmp) / "scenarios.jsonl"
            out = Path(tmp) / "python_contribution.json"
            write_jsonl([scenario], scenarios_path)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "python-contribution-trace",
                        "--scenarios",
                        str(scenarios_path),
                        "--json-out",
                        str(out),
                    ]
                )
            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["source"], "python_scenario_contributions")
        self.assertIn("move.apply_lookahead_to_top_move_candidates", data["covered_rule_ids"])
        self.assertIn("Python contribution trace", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
