"""Tests for event-runtime materialization metadata.

These tests assert that content scenarios, content-state materializations,
generic WRAM state-space reports, and compare/mirror plans all expose the
same explicit proof-status vocabulary for arbitrary-event runtime claims:

    planned_only -> ready_to_run -> state_materialized -> executed -> observed

and that compare/mirror only marks a behavioral mirror "passed" when
runtime evidence observes the requested sinks.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.debugger.content_scenarios import build_content_scenario_report
from tools.debugger.content_state import build_content_state_report
from tools.debugger.mirrors import build_compare_plan
from tools.debugger.state_space import build_state_space_report


PROOF_STATUS_PROGRESSION = (
    "planned_only",
    "ready_to_run",
    "state_materialized",
    "executed",
    "observed",
)

MIRROR_STATUS_VALUES = (
    "not_run",
    "planned_only",
    "ready_to_run",
    "state_materialized",
    "executed",
    "inconclusive",
    "passed",
    "failed",
)


def _route_for(precondition: dict) -> dict:
    route = precondition.get("event_runtime_materialization")
    if not isinstance(route, dict):
        raise AssertionError(
            f"precondition has no event_runtime_materialization route: {precondition}"
        )
    return route


class EventRuntimeMaterializationRouteTests(unittest.TestCase):
    """Content scenarios must expose explicit event-runtime materialization routes."""

    def _build_script_scenario(self, root: Path) -> dict:
        (root / "scripts").mkdir(parents=True, exist_ok=True)
        (root / "scripts" / "unit_script.asm").write_text(
            "\n".join(
                [
                    "UnitScript:",
                    "\topentext",
                    "\twritetext UnitText",
                    "\twaitbutton",
                    "\tend",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return build_content_scenario_report(
            source_files=("scripts/unit_script.asm",),
            out_scenarios="content_scenarios.jsonl",
            max_cases=4,
            seed=23,
            root=root,
        )

    def _build_movement_scenario(self, root: Path) -> dict:
        (root / "scripts").mkdir(parents=True, exist_ok=True)
        (root / "scripts" / "unit_movement.asm").write_text(
            "\n".join(
                [
                    "UnitMovement:",
                    "\tstep LEFT",
                    "\tturn_head UP",
                    "\tstep_end",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return build_content_scenario_report(
            source_files=("scripts/unit_movement.asm",),
            out_scenarios="content_scenarios.jsonl",
            max_cases=4,
            seed=29,
            root=root,
        )

    def _build_map_scenario(self, root: Path) -> dict:
        (root / "maps").mkdir(parents=True, exist_ok=True)
        (root / "maps" / "UnitMap.asm").write_text(
            "\n".join(
                [
                    "UnitMap_MapEvents:",
                    "\tdef_bg_events",
                    "\tbg_event 4, 5, BGEVENT_READ, UnitMapSign",
                    "UnitMapSign:",
                    "\tjumptext UnitMapText",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return build_content_scenario_report(
            source_files=("maps/UnitMap.asm",),
            out_scenarios="content_scenarios.jsonl",
            max_cases=4,
            seed=31,
            root=root,
        )

    def test_script_entry_precondition_emits_runtime_materialization_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self._build_script_scenario(root)

        scenario = report["scenarios"][0]
        precondition = scenario["state_preconditions"][0]
        route = _route_for(precondition)

        self.assertEqual(scenario["scenario_type"], "script_command_stream")
        self.assertEqual(precondition["kind"], "script_entry")
        self.assertEqual(route["kind"], "event_runtime_materialization")
        self.assertEqual(route["runtime_route"], "script_engine")
        self.assertIn("base_save_state", route["required_inputs"])
        self.assertIn("scenario_id", route["required_inputs"])
        self.assertIn("symbol_table", route["required_inputs"])
        self.assertGreaterEqual(len(route["state_preconditions"]), 1)
        self.assertEqual(route["state_preconditions"][0]["kind"], "script_entry")
        self.assertTrue(
            any("trace-instructions" in cmd for cmd in route["expected_proof_commands"]),
            f"expected at least one trace-instructions command, got {route['expected_proof_commands']}",
        )
        self.assertTrue(
            any("replay" in cmd for cmd in route["expected_proof_commands"]),
            f"expected at least one replay command, got {route['expected_proof_commands']}",
        )
        self.assertIn(route["actual_proof_status"], PROOF_STATUS_PROGRESSION)
        self.assertEqual(route["actual_proof_status"], "planned_only")
        self.assertEqual(route["expected_proof_status"], "instruction_observed")
        self.assertIn("wScriptPos", route["expected_sinks"])
        self.assertEqual(route["observed_sinks"], [])

    def test_movement_entry_precondition_emits_runtime_materialization_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self._build_movement_scenario(root)

        scenario = report["scenarios"][0]
        precondition = scenario["state_preconditions"][0]
        route = _route_for(precondition)

        self.assertEqual(scenario["scenario_type"], "movement_data")
        self.assertEqual(precondition["kind"], "movement_entry")
        self.assertEqual(route["kind"], "event_runtime_materialization")
        self.assertEqual(route["runtime_route"], "movement_engine")
        self.assertEqual(route["actual_proof_status"], "planned_only")
        self.assertEqual(route["expected_proof_status"], "instruction_observed")
        self.assertIn("wMovementDataAddress", route["expected_sinks"])
        self.assertIn("wMovementPointer", route["expected_sinks"])
        self.assertEqual(route["observed_sinks"], [])

    def test_map_position_precondition_emits_runtime_materialization_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self._build_map_scenario(root)

        scenario = report["scenarios"][0]
        precondition = scenario["state_preconditions"][0]
        route = _route_for(precondition)

        self.assertEqual(precondition["kind"], "map_position")
        self.assertEqual(route["kind"], "event_runtime_materialization")
        self.assertEqual(route["runtime_route"], "overworld_event_engine")
        self.assertEqual(route["actual_proof_status"], "planned_only")
        self.assertIn(route["expected_proof_status"], {"runtime_observed", "instruction_observed"})
        self.assertIn("wMapGroup", route["expected_sinks"])
        self.assertEqual(route["observed_sinks"], [])

    def test_route_fields_are_json_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self._build_script_scenario(root)
        serialized = json.dumps(report, sort_keys=True)
        decoded = json.loads(serialized)
        scenario = decoded["scenarios"][0]
        route = _route_for(scenario["state_preconditions"][0])
        self.assertIsInstance(route["expected_proof_commands"], list)
        self.assertIsInstance(route["required_inputs"], list)
        self.assertIsInstance(route["state_preconditions"], list)


class ContentStatePreservesMaterializationRouteTests(unittest.TestCase):
    """content-state must propagate the runtime route without claiming execution."""

    def _write_script_scenario_with_symbols(self, root: Path) -> None:
        (root / "test.sym").write_text(
            "\n".join(
                [
                    "02:5000 UnitScript",
                    "01:DA10 wScriptBank",
                    "01:DA11 wScriptPos",
                    "01:DA13 wScriptRunning",
                    "01:DA14 wScriptMode",
                    "01:DA15 wScriptStackSize",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        precondition = {
            "id": "script_engine_entry",
            "kind": "script_entry",
            "values": {
                "script_label": "UnitScript",
                "source_file": "scripts/unit_script.asm",
            },
            "watch_symbols": ["wScriptBank", "wScriptPos", "wScriptVar"],
            "event_runtime_materialization": {
                "kind": "event_runtime_materialization",
                "runtime_route": "script_engine",
                "required_inputs": ["base_save_state", "scenario_id", "symbol_table"],
                "state_preconditions": [
                    {
                        "id": "script_engine_entry",
                        "kind": "script_entry",
                        "watch_symbols": ["wScriptBank", "wScriptPos"],
                    }
                ],
                "expected_proof_commands": [
                    "python -m tools.debugger trace-instructions --symbol RunScriptCommand",
                    "python -m tools.debugger replay --execute-watch",
                ],
                "expected_proof_status": "instruction_observed",
                "actual_proof_status": "planned_only",
                "expected_sinks": ["wScriptPos", "wScriptVar"],
                "observed_sinks": [],
            },
        }
        (root / "content.json").write_text(
            json.dumps(
                {
                    "kind": "unified_debugger_content_scenarios",
                    "valid": True,
                    "scenarios": [
                        {
                            "id": "content_scenario_1_0000",
                            "kind": "unified_debugger_content_scenario",
                            "scenario_type": "script_command_stream",
                            "source_file": "scripts/unit_script.asm",
                            "label": "UnitScript",
                            "state_preconditions": [precondition],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def test_content_state_emits_planned_only_route_without_execute(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_script_scenario_with_symbols(root)
            report = build_content_state_report(
                reports=("content.json",),
                scenario_ids=("content_scenario_1_0000",),
                symbols_path="test.sym",
                root=root,
            )

        materialization = report["materializations"][0]
        route = materialization.get("event_runtime_materialization")
        self.assertIsInstance(route, dict)
        self.assertEqual(route["kind"], "event_runtime_materialization")
        self.assertEqual(route["runtime_route"], "script_engine")
        self.assertEqual(route["expected_proof_status"], "instruction_observed")
        self.assertEqual(route["actual_proof_status"], "ready_to_run")
        self.assertEqual(route["observed_sinks"], [])
        self.assertFalse(report["executed"])
        self.assertEqual(materialization["actual_proof_status"], "ready_to_run")

    def test_content_state_marks_blocked_route_as_planned_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("", encoding="utf-8")
            (root / "content.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "script_command_stream",
                                "source_file": "scripts/unit_script.asm",
                                "label": "MissingScript",
                                "state_preconditions": [
                                    {
                                        "id": "script_engine_entry",
                                        "kind": "script_entry",
                                        "values": {
                                            "script_label": "MissingScript",
                                            "source_file": "scripts/unit_script.asm",
                                        },
                                        "watch_symbols": ["wScriptBank", "wScriptPos"],
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            report = build_content_state_report(
                reports=("content.json",),
                scenario_ids=("content_scenario_1_0000",),
                symbols_path="test.sym",
                root=root,
            )

        materialization = report["materializations"][0]
        route = materialization["event_runtime_materialization"]
        self.assertEqual(materialization["status"], "blocked")
        self.assertEqual(materialization["actual_proof_status"], "planned_only")
        self.assertEqual(route["actual_proof_status"], "planned_only")


class StateSpaceProofStatusTests(unittest.TestCase):
    """Generic state-space patches must surface explicit proof-status fields."""

    def test_state_space_patch_records_carry_planned_only_proof_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text(
                "01:DA00 wMapGroup\n01:DA01 wMapNumber\n",
                encoding="utf-8",
            )
            report = build_state_space_report(
                patches=("wMapGroup=1", "wMapNumber=2"),
                symbols_path="test.sym",
                rom_path="pokegold.gbc",
                root=root,
            )

        space = report["state_space"]
        self.assertEqual(space["actual_proof_status"], "planned_only")
        self.assertEqual(space["expected_proof_status"], "runtime_observed")
        for patch in space["patches"]:
            self.assertEqual(patch["actual_proof_status"], "planned_only")
            self.assertEqual(patch["expected_proof_status"], "runtime_observed")
            self.assertEqual(patch.get("observed_sinks", []), [])


class CompareMirrorRuntimeEvidenceTests(unittest.TestCase):
    """Compare/mirror must not pass behavioral mirrors without runtime evidence."""

    def _write_content_state_report(
        self,
        root: Path,
        *,
        executed: bool,
        actual_proof_status: str,
        expected_sinks: list[str],
        runtime_observations: list[dict] | None = None,
    ) -> None:
        materialization = {
            "scenario_id": "content_scenario_1_0000",
            "precondition_kind": "script_entry",
            "source_file": "scripts/unit_script.asm",
            "status": "ready" if actual_proof_status != "planned_only" else "blocked",
            "actual_proof_status": actual_proof_status,
            "event_runtime_materialization": {
                "kind": "event_runtime_materialization",
                "runtime_route": "script_engine",
                "required_inputs": ["base_save_state", "scenario_id", "symbol_table"],
                "state_preconditions": [
                    {
                        "id": "script_engine_entry",
                        "kind": "script_entry",
                        "watch_symbols": expected_sinks,
                    }
                ],
                "expected_proof_commands": [
                    "python -m tools.debugger trace-instructions --symbol RunScriptCommand",
                    "python -m tools.debugger replay --execute-watch",
                ],
                "expected_proof_status": "instruction_observed",
                "actual_proof_status": actual_proof_status,
                "expected_sinks": list(expected_sinks),
                "observed_sinks": [],
            },
            "patches": [
                {
                    "symbol": "wScriptBank",
                    "value": 2,
                    "value_hex": "02",
                    "bank_address": "01:DA10",
                }
            ],
        }
        report = {
            "kind": "unified_debugger_content_state_materialization",
            "valid": True,
            "executed": executed,
            "out_state": "patched.state" if executed else "",
            "materializations": [materialization],
            "execution": {
                "executed": executed,
                "out_state": "patched.state" if executed else "",
                "applied_patches": [
                    {
                        "symbol": "wScriptBank",
                        "value": 2,
                        "value_hex": "02",
                        "observed": 2,
                        "observed_hex": "02",
                        "verified": True,
                        "bank_address": "01:DA10",
                    }
                ] if executed else [],
            },
        }
        if runtime_observations is not None:
            report["runtime_observations"] = runtime_observations
        (root / "content_state.json").write_text(
            json.dumps(report),
            encoding="utf-8",
        )

    def test_compare_marks_planned_route_not_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_content_state_report(
                root,
                executed=False,
                actual_proof_status="ready_to_run",
                expected_sinks=["wScriptPos", "wScriptVar"],
            )
            report = build_compare_plan(reports=("content_state.json",), root=root)

        match = next(m for m in report["matches"] if m["id"] == "content_state_behavioral_mirror")
        self.assertIn(match["mirror_status"], MIRROR_STATUS_VALUES)
        self.assertNotEqual(match["mirror_status"], "passed")
        self.assertEqual(match["mirror_status"], "ready_to_run")
        self.assertEqual(match["observed_sinks"], [])
        self.assertEqual(set(match["expected_sinks"]), {"wScriptPos", "wScriptVar"})
        self.assertIn(
            "runtime evidence missing",
            " ".join(match["runtime_evidence_gaps"]).lower(),
        )

    def test_compare_marks_executed_without_runtime_evidence_inconclusive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_content_state_report(
                root,
                executed=True,
                actual_proof_status="state_materialized",
                expected_sinks=["wScriptPos", "wScriptVar"],
            )
            report = build_compare_plan(reports=("content_state.json",), root=root)

        match = next(m for m in report["matches"] if m["id"] == "content_state_behavioral_mirror")
        self.assertNotEqual(match["mirror_status"], "passed")
        self.assertIn(match["mirror_status"], {"state_materialized", "inconclusive"})

    def test_compare_marks_partial_runtime_evidence_inconclusive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_content_state_report(
                root,
                executed=True,
                actual_proof_status="state_materialized",
                expected_sinks=["wScriptPos", "wScriptVar"],
                runtime_observations=[
                    {
                        "scenario_id": "content_scenario_1_0000",
                        "observed_sinks": ["wScriptPos"],
                    }
                ],
            )
            report = build_compare_plan(reports=("content_state.json",), root=root)

        match = next(m for m in report["matches"] if m["id"] == "content_state_behavioral_mirror")
        self.assertEqual(match["mirror_status"], "inconclusive")
        self.assertEqual(set(match["observed_sinks"]), {"wScriptPos"})
        self.assertEqual(set(match["expected_sinks"]), {"wScriptPos", "wScriptVar"})

    def test_compare_marks_full_runtime_evidence_passed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_content_state_report(
                root,
                executed=True,
                actual_proof_status="state_materialized",
                expected_sinks=["wScriptPos", "wScriptVar"],
                runtime_observations=[
                    {
                        "scenario_id": "content_scenario_1_0000",
                        "observed_sinks": ["wScriptPos", "wScriptVar"],
                    }
                ],
            )
            report = build_compare_plan(reports=("content_state.json",), root=root)

        match = next(m for m in report["matches"] if m["id"] == "content_state_behavioral_mirror")
        self.assertEqual(match["mirror_status"], "passed")
        self.assertEqual(set(match["observed_sinks"]), {"wScriptPos", "wScriptVar"})

    def test_compare_marks_planned_only_without_executed_state_planned_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_content_state_report(
                root,
                executed=False,
                actual_proof_status="planned_only",
                expected_sinks=["wScriptPos"],
            )
            report = build_compare_plan(reports=("content_state.json",), root=root)

        match = next(m for m in report["matches"] if m["id"] == "content_state_behavioral_mirror")
        self.assertEqual(match["mirror_status"], "planned_only")


class ExistingContentStateBehaviorPreservedTests(unittest.TestCase):
    """Adding fields must not reshape existing report payloads."""

    def test_content_state_report_still_has_legacy_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text(
                "02:5000 UnitScript\n01:DA10 wScriptBank\n01:DA11 wScriptPos\n01:DA13 wScriptRunning\n01:DA14 wScriptMode\n01:DA15 wScriptStackSize\n",
                encoding="utf-8",
            )
            (root / "content.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "script_command_stream",
                                "source_file": "scripts/unit_script.asm",
                                "label": "UnitScript",
                                "state_preconditions": [
                                    {
                                        "id": "script_engine_entry",
                                        "kind": "script_entry",
                                        "values": {
                                            "script_label": "UnitScript",
                                            "source_file": "scripts/unit_script.asm",
                                        },
                                        "watch_symbols": ["wScriptBank", "wScriptPos"],
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            report = build_content_state_report(
                reports=("content.json",),
                scenario_ids=("content_scenario_1_0000",),
                symbols_path="test.sym",
                root=root,
            )

        for key in (
            "schema_version",
            "kind",
            "valid",
            "executed",
            "materializations",
            "execution",
            "commands",
        ):
            self.assertIn(key, report, f"legacy key missing: {key}")
        materialization = report["materializations"][0]
        for key in ("scenario_id", "precondition_kind", "status", "patches"):
            self.assertIn(key, materialization, f"legacy materialization key missing: {key}")


if __name__ == "__main__":
    unittest.main()
