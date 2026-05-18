from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from tools.debugger.content_scenarios import (
    EVENT_RUNTIME_ROUTE_KIND,
    PROOF_STATUS_PLANNED_ONLY,
    PROOF_STATUS_PROGRESSION,
    build_content_scenario_report,
    event_runtime_materialization_route,
)
from tools.debugger.content_state import build_content_state_report
from tools.debugger.mirrors import build_compare_plan
from tools.debugger.state_space import build_state_space_report


class EventRuntimeMaterializationTests(unittest.TestCase):
    def test_content_scenarios_attach_map_runtime_materialization_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "maps" / "UnitMap.asm").write_text(
                "UnitMap_MapEvents:\n\tdef_warp_events\n\twarp_event 4, 5, ROUTE_29, 1\n",
                encoding="utf-8",
            )

            report = build_content_scenario_report(
                source_files=("maps/UnitMap.asm",),
                max_cases=2,
                seed=11,
                root=root,
            )

        precondition = report["scenarios"][0]["state_preconditions"][0]
        self.assertIn("event_runtime_materialization", precondition)
        route = precondition["event_runtime_materialization_route"]
        self.assertEqual(precondition["event_runtime_materialization"], route)

        self.assertEqual(PROOF_STATUS_PROGRESSION[0], PROOF_STATUS_PLANNED_ONLY)
        self.assertEqual(PROOF_STATUS_PROGRESSION[-1], "observed")
        self.assertEqual(route["kind"], EVENT_RUNTIME_ROUTE_KIND)
        self.assertEqual(route["runtime_route"], "overworld_event_engine")
        self.assertEqual(route["actual_proof_status"], "planned_only")
        self.assertEqual(route["expected_proof_status"], "runtime_observed")
        self.assertIn("base_save_state", route["required_inputs"])
        self.assertIn("wMapGroup", route["expected_sinks"])
        self.assertEqual(route["observed_sinks"], [])

    def test_content_scenarios_attach_script_runtime_materialization_route(self) -> None:
        route = event_runtime_materialization_route(
            scenario_id="content_scenario_1_0000",
            scenario_type="script_command_stream",
            precondition_kind="script_entry",
            values={"script_label": "UnitScript", "source_file": "scripts/unit.asm"},
            watch_symbols=["wScriptPos", "wScriptVar"],
            outputs=[],
        )

        self.assertEqual(route["runtime_route"], "script_engine")
        self.assertEqual(route["expected_proof_status"], "instruction_observed")
        self.assertIn("RunScriptCommand", " ".join(route["expected_proof_commands"]))
        self.assertEqual(route["state_preconditions"][0]["kind"], "script_entry")
        self.assertIn("wScriptPos", route["expected_sinks"])

    def test_route_helper_accepts_claude_contract_signature(self) -> None:
        route = event_runtime_materialization_route(
            precondition_kind="script_entry",
            precondition_id="script_entry_1",
            watch_symbols=["wScriptPos"],
            values={"script_label": "UnitScript"},
            scenario_id="content_scenario_1_0002",
            source_file="scripts/unit.asm",
            actual_proof_status="ready_to_run",
            observed_sinks=("wScriptPos",),
        )

        self.assertEqual(route["kind"], EVENT_RUNTIME_ROUTE_KIND)
        self.assertEqual(route["precondition_id"], "script_entry_1")
        self.assertEqual(route["source_file"], "scripts/unit.asm")
        self.assertEqual(route["actual_proof_status"], "ready_to_run")
        self.assertEqual(route["observed_sinks"], ["wScriptPos"])
        self.assertIn("instruction_trace", route["evidence_kinds"])

    def test_content_scenarios_output_route_lists_output_sinks(self) -> None:
        route = event_runtime_materialization_route(
            scenario_id="content_scenario_1_0001",
            scenario_type="ui_tilemap_update",
            precondition_kind="ui_output_sink",
            values={"ui_label": "UnitUI", "source_file": "engine/unit.asm"},
            watch_symbols=["wTilemap"],
            outputs=[
                {"state_symbol": "wTilemap"},
                {"address": "$9800"},
            ],
        )

        self.assertEqual(route["runtime_route"], "ui_tilemap_engine")
        self.assertIn("wTilemap", route["expected_sinks"])
        self.assertIn("$9800", route["expected_sinks"])
        self.assertEqual(route["observed_sinks"], [])

    def test_content_state_ready_materialization_promotes_route_to_ready_to_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_map_fixture(root)
            write_map_symbols(root)
            write_content_scenario(root, with_route=True)

            report = build_content_state_report(
                reports=("content.json",),
                symbols_path="test.sym",
                root=root,
            )

        materialization = report["materializations"][0]
        self.assertIn("event_runtime_materialization", materialization)
        route = materialization["event_runtime_materialization_route"]
        self.assertEqual(materialization["event_runtime_materialization"], route)

        self.assertTrue(report["valid"])
        self.assertEqual(materialization["status"], "ready")
        self.assertEqual(materialization["actual_proof_status"], "ready_to_run")
        self.assertEqual(route["actual_proof_status"], "ready_to_run")
        self.assertEqual(route["expected_proof_status"], "runtime_observed")

    def test_content_state_accepts_claude_route_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_map_fixture(root)
            write_map_symbols(root)
            write_content_scenario(root, with_route=True, route_key="event_runtime_materialization")

            report = build_content_state_report(
                reports=("content.json",),
                symbols_path="test.sym",
                root=root,
            )

        materialization = report["materializations"][0]

        self.assertEqual(materialization["actual_proof_status"], "ready_to_run")
        self.assertEqual(materialization["event_runtime_materialization"]["kind"], EVENT_RUNTIME_ROUTE_KIND)
        self.assertEqual(
            materialization["event_runtime_materialization"],
            materialization["event_runtime_materialization_route"],
        )

    def test_content_state_blocked_materialization_keeps_route_planned_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_map_symbols(root)
            write_content_scenario(root, with_route=True)

            report = build_content_state_report(
                reports=("content.json",),
                symbols_path="test.sym",
                root=root,
            )

        materialization = report["materializations"][0]
        route = materialization["event_runtime_materialization_route"]

        self.assertFalse(report["valid"])
        self.assertEqual(materialization["status"], "blocked")
        self.assertEqual(materialization["actual_proof_status"], "planned_only")
        self.assertEqual(route["actual_proof_status"], "planned_only")

    def test_content_state_execution_promotes_route_to_state_materialized(self) -> None:
        class FakeMemory:
            def __init__(self) -> None:
                self.values: dict[Any, int] = {0xFF70: 1}

            def __getitem__(self, key: Any) -> int:
                return self.values.get(key, 0)

            def __setitem__(self, key: Any, value: int) -> None:
                self.values[key] = int(value) & 0xFF

        class FakePyBoy:
            def __init__(self) -> None:
                self.memory = FakeMemory()

            def load_state(self, _fh: Any) -> None:
                return None

            def save_state(self, fh: Any) -> None:
                fh.write(b"patched-state")

            def stop(self, save: bool = False) -> None:
                return None

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_map_fixture(root)
            write_map_symbols(root)
            write_content_scenario(root, with_route=True)
            (root / "rom.gbc").write_bytes(b"rom")
            (root / "base.state").write_bytes(b"base-state")

            with patch("tools.debugger.content_state.trace_runtime.open_pyboy", return_value=FakePyBoy()):
                report = build_content_state_report(
                    reports=("content.json",),
                    symbols_path="test.sym",
                    rom_path="rom.gbc",
                    base_save_state="base.state",
                    out_state="patched.state",
                    execute=True,
                    root=root,
                )

        materialization = report["materializations"][0]
        route = materialization["event_runtime_materialization_route"]

        self.assertTrue(report["executed"])
        self.assertEqual(materialization["actual_proof_status"], "state_materialized")
        self.assertEqual(route["actual_proof_status"], "state_materialized")
        self.assertIn("wMapGroup", route["observed_sinks"])

    def test_content_state_output_materialization_keeps_route_planned_until_runtime_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("00:0000 NULL\n", encoding="utf-8")
            route = event_runtime_materialization_route(
                scenario_id="content_scenario_1_0002",
                scenario_type="asset_materialization",
                precondition_kind="asset_loader_entry",
                values={"asset": "gfx/unit.2bpp", "source_file": "gfx/unit.asm"},
                watch_symbols=["wRequested2bppSource"],
                outputs=[{"state_symbol": "wRequested2bppSource"}],
            )
            (root / "content.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0002",
                                "scenario_type": "asset_materialization",
                                "source_file": "gfx/unit.asm",
                                "state_preconditions": [
                                    {
                                        "id": "asset_loader_runtime",
                                        "kind": "asset_loader_entry",
                                        "values": {"asset": "gfx/unit.2bpp"},
                                        "event_runtime_materialization_route": route,
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_content_state_report(reports=("content.json",), symbols_path="test.sym", root=root)

        materialization = report["materializations"][0]

        self.assertEqual(materialization["status"], "planned")
        self.assertEqual(materialization["actual_proof_status"], "planned_only")
        self.assertEqual(materialization["event_runtime_materialization_route"]["actual_proof_status"], "planned_only")

    def test_state_space_ready_patch_has_runtime_proof_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_map_symbols(root)

            report = build_state_space_report(
                patches=("wMapGroup=24",),
                symbols_path="test.sym",
                scenario_id="content_scenario_1_0000",
                root=root,
            )

        patch_record = report["state_space"]["patches"][0]

        self.assertTrue(report["valid"])
        self.assertEqual(patch_record["actual_proof_status"], "ready_to_run")
        self.assertEqual(patch_record["expected_proof_status"], "runtime_observed")
        self.assertEqual(report["state_space"]["actual_proof_status"], "ready_to_run")
        self.assertIn("wMapGroup", report["state_space"]["expected_sinks"])

    def test_state_space_execution_promotes_patch_proof_fields(self) -> None:
        class FakeMemory:
            def __init__(self) -> None:
                self.values: dict[Any, int] = {0xFF70: 1}

            def __getitem__(self, key: Any) -> int:
                return self.values.get(key, 0)

            def __setitem__(self, key: Any, value: int) -> None:
                self.values[key] = int(value) & 0xFF

        class FakePyBoy:
            def __init__(self) -> None:
                self.memory = FakeMemory()

            def load_state(self, _fh: Any) -> None:
                return None

            def save_state(self, fh: Any) -> None:
                fh.write(b"patched")

            def stop(self, save: bool = False) -> None:
                return None

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_map_symbols(root)
            (root / "rom.gbc").write_bytes(b"rom")
            (root / "base.state").write_bytes(b"base")

            with patch("tools.debugger.state_space.trace_runtime.open_pyboy", return_value=FakePyBoy()):
                report = build_state_space_report(
                    patches=("wMapGroup=24",),
                    symbols_path="test.sym",
                    rom_path="rom.gbc",
                    base_save_state="base.state",
                    out_state="patched.state",
                    execute=True,
                    root=root,
                )

        patch_record = report["state_space"]["patches"][0]

        self.assertTrue(report["executed"])
        self.assertEqual(patch_record["actual_proof_status"], "state_materialized")
        self.assertEqual(report["state_space"]["actual_proof_status"], "state_materialized")
        self.assertIn("wMapGroup", report["state_space"]["observed_sinks"])

    def test_compare_marks_ready_route_as_ready_to_run_without_runtime_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_content_state_report(
                root,
                executed=False,
                materialization_status="ready",
                actual_proof_status="ready_to_run",
            )

            report = build_compare_plan(reports=("content_state.json",), root=root)

        match = next(item for item in report["matches"] if item["id"] == "content_state_behavioral_mirror")

        self.assertEqual(match["status"], "planned")
        self.assertEqual(match["proof_status"], "planned_only")
        self.assertEqual(match["mirror_status"], "ready_to_run")
        self.assertEqual(match["actual_proof_status"], "ready_to_run")
        self.assertIn("wMapGroup", match["expected_sinks"])
        self.assertEqual(match["observed_sinks"], [])
        self.assertTrue(match["runtime_evidence_gaps"])

    def test_compare_keeps_state_materialized_route_unpassed_without_runtime_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_content_state_report(
                root,
                executed=True,
                materialization_status="ready",
                actual_proof_status="state_materialized",
            )

            report = build_compare_plan(reports=("content_state.json",), root=root)

        match = next(item for item in report["matches"] if item["id"] == "content_state_behavioral_mirror")

        self.assertEqual(match["status"], "state_materialized")
        self.assertEqual(match["proof_status"], "state_materialized")
        self.assertEqual(match["mirror_status"], "state_materialized")
        self.assertEqual(match["actual_proof_status"], "state_materialized")
        self.assertEqual(match["observed_sinks"], [])
        self.assertTrue(match["runtime_evidence_gaps"])

    def test_compare_passes_executed_route_when_runtime_observations_cover_expected_sinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_content_state_report(
                root,
                executed=True,
                materialization_status="ready",
                actual_proof_status="state_materialized",
            )

            report = build_compare_plan(
                reports=("content_state.json",),
                runtime_observations=(
                    {
                        "scenario_id": "content_scenario_1_0000",
                        "observed_sinks": ["wMapGroup", "wMapNumber"],
                    },
                ),
                root=root,
            )

        match = next(item for item in report["matches"] if item["id"] == "content_state_behavioral_mirror")

        self.assertEqual(match["mirror_status"], "passed")
        self.assertEqual(match["actual_proof_status"], "observed")
        self.assertEqual(match["expected_proof_status"], "runtime_observed")
        self.assertEqual(set(match["observed_sinks"]), {"wMapGroup", "wMapNumber"})
        self.assertEqual(match["runtime_evidence_gaps"], [])

    def test_compare_harvests_runtime_observations_from_loaded_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_content_state_report(
                root,
                executed=True,
                materialization_status="ready",
                actual_proof_status="state_materialized",
            )
            (root / "runtime.json").write_text(
                json.dumps(
                    {
                        "kind": "unit_runtime_observation",
                        "runtime_observations": [
                            {
                                "scenario_id": "content_scenario_1_0000",
                                "observed_sinks": ["wMapGroup", "wMapNumber"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_compare_plan(reports=("content_state.json", "runtime.json"), root=root)

        match = next(item for item in report["matches"] if item["id"] == "content_state_behavioral_mirror")

        self.assertEqual(match["mirror_status"], "passed")
        self.assertEqual(match["actual_proof_status"], "observed")
        self.assertEqual(match["observed_sinks"], ["wMapGroup", "wMapNumber"])


def write_map_fixture(root: Path) -> None:
    (root / "data" / "maps").mkdir(parents=True)
    (root / "data" / "maps" / "maps.asm").write_text(
        "MapGroup_Unit:\n\tmap UnitMap, TILESET_JOHTO, TOWN, LANDMARK_NEW_BARK_TOWN, MUSIC_NEW_BARK_TOWN, FALSE, PALETTE_AUTO, FISHGROUP_OCEAN\n",
        encoding="utf-8",
    )


def write_map_symbols(root: Path) -> None:
    (root / "test.sym").write_text(
        "01:DA00 wMapGroup\n01:DA01 wMapNumber\n01:DA02 wYCoord\n01:DA03 wXCoord\n",
        encoding="utf-8",
    )


def write_content_scenario(
    root: Path,
    *,
    with_route: bool,
    route_key: str = "event_runtime_materialization_route",
) -> None:
    route = event_runtime_materialization_route(
        scenario_id="content_scenario_1_0000",
        scenario_type="map_warp",
        precondition_kind="map_position",
        values={"map_label": "UnitMap_MapEvents", "x": 4, "y": 5},
        watch_symbols=["wMapGroup", "wMapNumber"],
        outputs=[],
    )
    precondition: dict[str, Any] = {
        "id": "map_warp_position",
        "kind": "map_position",
        "values": {"map_label": "UnitMap_MapEvents", "x": 4, "y": 5},
        "watch_symbols": ["wMapGroup", "wMapNumber"],
    }
    if with_route:
        precondition[route_key] = route
    (root / "content.json").write_text(
        json.dumps(
            {
                "kind": "unified_debugger_content_scenarios",
                "valid": True,
                "scenarios": [
                    {
                        "id": "content_scenario_1_0000",
                        "kind": "unified_debugger_content_scenario",
                        "scenario_type": "map_warp",
                        "source_file": "maps/UnitMap.asm",
                        "state_preconditions": [precondition],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def write_content_state_report(
    root: Path,
    *,
    executed: bool,
    materialization_status: str,
    actual_proof_status: str,
) -> None:
    route = event_runtime_materialization_route(
        scenario_id="content_scenario_1_0000",
        scenario_type="map_warp",
        precondition_kind="map_position",
        values={"map_label": "UnitMap_MapEvents", "x": 4, "y": 5},
        watch_symbols=["wMapGroup", "wMapNumber"],
        outputs=[],
    )
    route["actual_proof_status"] = actual_proof_status
    materialization = {
        "scenario_id": "content_scenario_1_0000",
        "scenario_type": "map_warp",
        "precondition_kind": "map_position",
        "source_file": "maps/UnitMap.asm",
        "status": materialization_status,
        "actual_proof_status": actual_proof_status,
        "expected_proof_status": "runtime_observed",
        "expected_sinks": ["wMapGroup", "wMapNumber"],
        "observed_sinks": ["wMapGroup", "wMapNumber"] if executed else [],
        "event_runtime_materialization_route": route,
        "patches": [
            {"symbol": "wMapGroup", "value": 24, "value_hex": "18", "bank_address": "01:DA00"},
            {"symbol": "wMapNumber", "value": 4, "value_hex": "04", "bank_address": "01:DA01"},
        ],
        "errors": [],
    }
    (root / "content_state.json").write_text(
        json.dumps(
            {
                "kind": "unified_debugger_content_state_materialization",
                "valid": True,
                "executed": executed,
                "out_state": "patched.state",
                "materializations": [materialization],
                "execution": {
                    "executed": executed,
                    "out_state": "patched.state",
                    "applied_patches": materialization["patches"] if executed else [],
                },
            }
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
