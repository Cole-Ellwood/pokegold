import json
import tempfile
import unittest
from pathlib import Path

from tools.debugger.shrink_map_script import (
    format_report,
    report_json,
    shrink_map_script_path,
    shrink_map_script_scenario,
)


def canonical_scenario() -> dict:
    return {
        "id": "script_entry_repro",
        "scenario_type": "map_script",
        "map": "UnitHouse1F",
        "steps": [
            {"op": "load_map", "map": "UnitHouse1F"},
            {"op": "walk", "direction": "UP"},
            {"op": "face_object", "object": "UnitNpc"},
            {"op": "open_text", "text": "noise"},
            {"op": "set_flag", "flag": "EVENT_UNIT_NPC_READY"},
            {"op": "jump_script", "label": "UnitNpcScript"},
            {"op": "show_text", "text": "hello"},
            {"op": "close_text"},
            {"op": "wait", "frames": 8},
        ],
        "events": [
            {"kind": "warp", "id": "noise"},
            {"kind": "bg_event", "id": "unit_signpost"},
            {"kind": "object_event", "id": "noise_npc"},
        ],
        "state_preconditions": [
            {"kind": "map_position", "map": "UnitHouse1F"},
            {"kind": "script_entry", "symbol": "UnitNpcScript"},
            {"kind": "time_of_day", "value": "day"},
        ],
        "inputs": ["A", "WAIT", "A"],
    }


def keeps_script_bug_fact(scenario: dict) -> bool:
    steps = scenario.get("steps")
    if not isinstance(steps, list):
        return False
    ops = [step.get("op") for step in steps if isinstance(step, dict)]
    events = scenario.get("events") if isinstance(scenario.get("events"), list) else []
    preconditions = (
        scenario.get("state_preconditions")
        if isinstance(scenario.get("state_preconditions"), list)
        else []
    )
    return (
        "face_object" in ops
        and "jump_script" in ops
        and "show_text" in ops
        and any(event.get("id") == "unit_signpost" for event in events if isinstance(event, dict))
        and any(
            item.get("kind") == "script_entry" and item.get("symbol") == "UnitNpcScript"
            for item in preconditions
            if isinstance(item, dict)
        )
    )


class MapScriptShrinkerTests(unittest.TestCase):
    def test_canonical_reduces_script_steps_to_trigger_facts(self) -> None:
        report = shrink_map_script_scenario(canonical_scenario(), predicate=keeps_script_bug_fact)
        shrunk = report["shrunk_scenario"]
        ops = [step["op"] for step in shrunk["steps"]]

        self.assertTrue(report["valid"])
        self.assertTrue(report["preserved"])
        self.assertEqual(report["original_counts"]["step_count"], 9)
        self.assertEqual(report["shrunk_counts"]["step_count"], 3)
        self.assertEqual(ops, ["face_object", "jump_script", "show_text"])
        self.assertEqual(shrunk["events"], [{"kind": "bg_event", "id": "unit_signpost"}])
        self.assertEqual(
            shrunk["state_preconditions"],
            [{"kind": "script_entry", "symbol": "UnitNpcScript"}],
        )
        self.assertGreater(report["reduction_step_count"], 0)
        self.assertIn("steps", {step["path"] for step in report["reduction_trace"]})
        self.assertIn("events", {step["path"] for step in report["reduction_trace"]})
        self.assertIn("state_preconditions", {step["path"] for step in report["reduction_trace"]})

    def test_writes_minimized_scenario_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = shrink_map_script_scenario(
                canonical_scenario(),
                predicate=keeps_script_bug_fact,
                out_scenario="shrunk/script.json",
                root=root,
            )
            out_path = root / "shrunk" / "script.json"
            written = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertTrue(report["out_scenario"]["written"])
        self.assertEqual(report["out_scenario"]["path"], "shrunk/script.json")
        self.assertEqual(len(written["steps"]), 3)

    def test_loads_jsonl_by_scenario_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "scripts.jsonl"
            path.write_text(
                json.dumps({"id": "noise", "steps": [{"op": "noop"}]})
                + "\n"
                + json.dumps(canonical_scenario())
                + "\n",
                encoding="utf-8",
            )
            report = shrink_map_script_path(
                "scripts.jsonl",
                scenario_id="script_entry_repro",
                predicate=keeps_script_bug_fact,
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["shrunk_scenario"]["id"], "script_entry_repro")
        self.assertEqual(report["shrunk_counts"]["step_count"], 3)

    def test_baseline_must_reproduce(self) -> None:
        report = shrink_map_script_scenario(
            {"steps": [{"op": "noop"}]},
            predicate=keeps_script_bug_fact,
        )

        self.assertFalse(report["valid"])
        self.assertFalse(report["preserved"])
        self.assertIn("baseline map-script scenario does not reproduce", "\n".join(report["errors"]))
        self.assertEqual(report["reduction_step_count"], 0)

    def test_missing_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = shrink_map_script_path(
                "missing.json",
                predicate=keeps_script_bug_fact,
                root=Path(tmp),
            )

        self.assertFalse(report["valid"])
        self.assertIn("missing map-script scenario", "\n".join(report["errors"]))

    def test_format_and_json_helpers_expose_counts(self) -> None:
        report = shrink_map_script_scenario(canonical_scenario(), predicate=keeps_script_bug_fact)
        text = format_report(report)
        encoded = json.loads(report_json(report))

        self.assertIn("steps=9->3", text)
        self.assertEqual(encoded["kind"], "unified_debugger_shrink_map_script")


if __name__ == "__main__":
    unittest.main()
