from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.content_scenarios import build_content_scenario_report
from tools.debugger.coverage import build_coverage_report
from tools.debugger.localize import build_localization_plan
from tools.debugger.replay import build_replay_plan


class ContentScenarioTests(unittest.TestCase):
    def test_content_scenarios_generate_script_command_stream_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "scripts" / "unit_script.asm").write_text(
                "\n".join(
                    [
                        "UnitScript:",
                        "\topentext",
                        "\twritetext UnitText",
                        "\twaitbutton",
                        "\tclosetext",
                        "\tend",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            out_scenarios = root / "content_scenarios.jsonl"

            report = build_content_scenario_report(
                source_files=("scripts/unit_script.asm",),
                out_scenarios="content_scenarios.jsonl",
                max_cases=4,
                seed=7,
                root=root,
            )
            rows = [
                json.loads(line)
                for line in out_scenarios.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        scenario = report["scenarios"][0]
        probe_ids = {probe["id"] for probe in scenario["behavioral_probes"]}
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["scenario_count"], 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(scenario["scenario_type"], "script_command_stream")
        self.assertEqual(scenario["trigger"]["script"], "UnitScript")
        self.assertEqual(scenario["state_preconditions"][0]["kind"], "script_entry")
        self.assertEqual(scenario["state_preconditions"][0]["values"]["script_label"], "UnitScript")
        self.assertIn("wScriptPos", scenario["state_preconditions"][0]["watch_symbols"])
        self.assertIn("UnitScript", scenario["runtime_targets"]["script_symbols"])
        self.assertIn("RunScriptCommand", scenario["runtime_targets"]["trace_symbols"])
        self.assertIn("content_runtime_setup_route", probe_ids)
        self.assertIn("content_state_materialization_route", probe_ids)
        self.assertIn("content_positioned_instruction_trace_route", probe_ids)
        self.assertIn("content_script_provenance", probe_ids)
        self.assertIn("--symbol RunScriptCommand", commands)
        self.assertIn("trace-instructions --report .local\\tmp\\debugger_content_state_content_scenario_7_0000.json", commands)
        self.assertIn("tools.debugger expect --source-file scripts/unit_script.asm --expect contains=opentext", commands)

    def test_content_scenarios_generate_text_block_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "text").mkdir()
            (root / "text" / "unit_text.asm").write_text(
                "\n".join(
                    [
                        "UnitText:",
                        "\ttext \"HELLO\"",
                        "\tline \"THERE\"",
                        "\tdone",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            out_scenarios = root / "content_scenarios.jsonl"

            report = build_content_scenario_report(
                source_files=("text/unit_text.asm",),
                out_scenarios="content_scenarios.jsonl",
                max_cases=4,
                seed=9,
                root=root,
            )
            rows = [
                json.loads(line)
                for line in out_scenarios.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        scenario = report["scenarios"][0]
        probe_ids = {probe["id"] for probe in scenario["behavioral_probes"]}
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["scenario_count"], 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(scenario["scenario_type"], "text_block")
        self.assertEqual(scenario["trigger"]["text"], "UnitText")
        self.assertIn("UnitText", scenario["runtime_targets"]["script_symbols"])
        self.assertIn("PrintText", scenario["runtime_targets"]["trace_symbols"])
        self.assertIn("content_runtime_setup_route", probe_ids)
        self.assertIn("content_script_provenance", probe_ids)
        self.assertIn("--symbol PrintText", commands)
        self.assertIn("tools.debugger expect --source-file text/unit_text.asm --expect contains=text", commands)

    def test_content_scenarios_generate_movement_data_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
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
            out_scenarios = root / "content_scenarios.jsonl"

            report = build_content_scenario_report(
                source_files=("scripts/unit_movement.asm",),
                out_scenarios="content_scenarios.jsonl",
                max_cases=4,
                seed=11,
                root=root,
            )
            rows = [
                json.loads(line)
                for line in out_scenarios.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        scenario = report["scenarios"][0]
        probe_ids = {probe["id"] for probe in scenario["behavioral_probes"]}
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["scenario_count"], 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(scenario["scenario_type"], "movement_data")
        self.assertEqual(scenario["trigger"]["movement"], "UnitMovement")
        self.assertEqual(scenario["state_preconditions"][0]["kind"], "movement_entry")
        self.assertEqual(scenario["state_preconditions"][0]["values"]["movement_label"], "UnitMovement")
        self.assertEqual(scenario["state_preconditions"][0]["values"]["object_id"], 0)
        self.assertIn("wMovementPointer", scenario["state_preconditions"][0]["watch_symbols"])
        self.assertIn("UnitMovement", scenario["runtime_targets"]["script_symbols"])
        self.assertIn("ApplyMovement", scenario["runtime_targets"]["trace_symbols"])
        self.assertIn("HandleMovementData", scenario["runtime_targets"]["trace_symbols"])
        self.assertIn("wMovementDataAddress", scenario["runtime_targets"]["watch_symbols"])
        self.assertEqual(scenario["runtime_targets"]["runtime_route"], "movement_engine")
        self.assertIn("content_runtime_setup_route", probe_ids)
        self.assertIn("content_script_provenance", probe_ids)
        self.assertIn("content_positioned_instruction_trace_route", probe_ids)
        self.assertIn("--symbol ApplyMovement", commands)
        self.assertIn("trace-instructions --report .local\\tmp\\debugger_content_state_content_scenario_11_0000.json", commands)
        self.assertIn("tools.debugger expect --source-file scripts/unit_movement.asm --expect contains=movement", commands)

    def test_content_scenarios_generates_map_event_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "maps" / "UnitMap.asm").write_text(
                "\n".join(
                    [
                        "UnitMap_MapEvents:",
                        "\tdef_warp_events",
                        "\twarp_event 1, 2, ROUTE_29, 1",
                        "\tdef_coord_events",
                        "\tcoord_event 2, 3, SCENE_UNITMAP, UnitMapScene",
                        "\tdef_bg_events",
                        "\tbg_event 4, 5, BGEVENT_READ, UnitMapSign",
                        "\tdef_object_events",
                        "\tobject_event 6, 7, SPRITE_CHRIS, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, -1, 0, OBJECTTYPE_SCRIPT, 0, UnitMapNPCScript, -1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            out_scenarios = root / "content_scenarios.jsonl"

            report = build_content_scenario_report(
                source_files=("maps/UnitMap.asm",),
                out_scenarios="content_scenarios.jsonl",
                max_cases=8,
                seed=5,
                root=root,
            )
            rows = [
                json.loads(line)
                for line in out_scenarios.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        scenario_types = {item["scenario_type"] for item in report["scenarios"]}
        commands = "\n".join(report["commands"])
        bg_scenario = next(item for item in report["scenarios"] if item["scenario_type"] == "map_bg_event")
        object_scenario = next(item for item in report["scenarios"] if item["scenario_type"] == "map_object_event")
        bg_probe_ids = {probe["id"] for probe in bg_scenario["behavioral_probes"]}

        self.assertTrue(report["valid"])
        self.assertEqual(report["scenario_count"], 4)
        self.assertGreaterEqual(report["runtime_probe_count"], 4)
        self.assertEqual(len(rows), 4)
        self.assertEqual(report["scenario_manifest"]["record_count"], 4)
        self.assertIn("map_warp", scenario_types)
        self.assertIn("map_coord_event", scenario_types)
        self.assertIn("map_bg_event", scenario_types)
        self.assertIn("map_object_event", scenario_types)
        self.assertIn("tools.debugger replay --changed-file maps/UnitMap.asm --scenario-id", commands)
        self.assertGreater(report["behavioral_probe_count"], 0)
        self.assertEqual(report["scenarios"][0]["behavioral_probe_count"], len(report["scenarios"][0]["behavioral_probes"]))
        self.assertIn(
            "content_replay_route",
            {probe["id"] for probe in report["scenarios"][0]["behavioral_probes"]},
        )
        self.assertIn(
            "--scenario content_scenarios.jsonl --scenario-id content_scenario_5_0000",
            commands,
        )
        self.assertIn("content_runtime_setup_route", bg_probe_ids)
        self.assertIn("content_runtime_trace_route", bg_probe_ids)
        self.assertIn("content_runtime_watch_route", bg_probe_ids)
        self.assertIn("content_state_materialization_route", bg_probe_ids)
        self.assertIn("content_state_execution_route", bg_probe_ids)
        self.assertIn("content_positioned_replay_route", bg_probe_ids)
        self.assertIn("content_positioned_instruction_trace_route", bg_probe_ids)
        self.assertIn("content_script_provenance", bg_probe_ids)
        self.assertIn("CheckFacingBGEvent", bg_scenario["runtime_targets"]["trace_symbols"])
        self.assertIn("UnitMapSign", bg_scenario["runtime_targets"]["script_symbols"])
        self.assertIn("wMapGroup", bg_scenario["runtime_targets"]["watch_symbols"])
        self.assertIn("UnitMapNPCScript", object_scenario["related_symbols"])
        self.assertIn("--symbol CheckFacingBGEvent", commands)
        self.assertIn("--watch-symbol wMapGroup", commands)
        self.assertIn("tools.debugger content-state", commands)
        self.assertIn("tools.debugger trace-instructions --report .local\\tmp\\debugger_content_state_content_scenario_5_0002.json", commands)
        self.assertIn("tools.debugger expect --source-file maps/UnitMap.asm --expect contains=warp_event", commands)

    def test_content_scenarios_feed_replay_localize_and_coverage_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "home").mkdir()
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
            (root / "home" / "map.asm").write_text(
                "\n".join(
                    [
                        "CheckFacingBGEvent:",
                        "\tcall CheckBGEventFlag",
                        "\tret",
                        "CheckBGEventFlag:",
                        "\tret",
                        "CallScript:",
                        "\tret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "01:4000 UnitMap_MapEvents",
                        "01:4010 UnitMapSign",
                        "00:5000 CheckFacingBGEvent",
                        "00:5010 CheckBGEventFlag",
                        "00:5020 CallScript",
                        "01:D000 wMapGroup",
                        "01:D001 wMapNumber",
                        "01:D002 wXCoord",
                        "01:D003 wYCoord",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            scenario_report = build_content_scenario_report(
                source_files=("maps/UnitMap.asm",),
                out_scenarios="content_scenarios.jsonl",
                root=root,
            )
            (root / "content_scenarios.json").write_text(json.dumps(scenario_report), encoding="utf-8")

            replay = build_replay_plan(reports=("content_scenarios.json",), root=root)
            localized = build_localization_plan(reports=("content_scenarios.json",), root=root)
            coverage = build_coverage_report(reports=("content_scenarios.json",), root=root)

        localized_ids = {candidate["id"] for candidate in localized["candidates"]}
        covered = {target["id"]: target for target in coverage["targets"]}

        self.assertTrue(replay["valid"])
        self.assertTrue(localized["valid"])
        self.assertTrue(coverage["valid"])
        self.assertIn("CheckFacingBGEvent", replay["replay_targets"]["symbols"])
        self.assertIn("wMapGroup", replay["replay_targets"]["watch_symbols"])
        self.assertNotIn("wMapGroup", replay["replay_targets"]["symbols"])
        self.assertIn("UnitMapSign", localized_ids)
        self.assertIn("CheckFacingBGEvent", localized_ids)
        self.assertEqual(covered["maps/UnitMap.asm"]["status"], "covered")
        self.assertEqual(covered["CheckFacingBGEvent"]["status"], "covered")
        self.assertIn("wMapGroup", covered)

    def test_cli_content_scenarios_writes_json_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "audio").mkdir()
            source = root / "audio" / "unit.asm"
            source.write_text(
                "Music_Unit:\n\tchannel_count 2\n\tchannel 1, Music_Unit_Ch1\n\tchannel 2, Music_Unit_Ch2\n",
                encoding="utf-8",
            )
            out = root / "content_scenarios.json"
            manifest = root / "content_scenarios.jsonl"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "content-scenarios",
                        "--source-file",
                        str(source),
                        "--out-scenarios",
                        str(manifest),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))
            rows = [
                json.loads(line)
                for line in manifest.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_content_scenarios")
        audio_rows = [row for row in rows if row["scenario_type"] == "audio_channel_block"]
        self.assertEqual(len(audio_rows), 1)
        self.assertEqual(data["scenario_count"], len(rows))
        self.assertEqual(audio_rows[0]["behavioral_probe_count"], len(audio_rows[0]["behavioral_probes"]))
        self.assertIn("content_replay_route", {probe["id"] for probe in audio_rows[0]["behavioral_probes"]})
        self.assertIn("content_runtime_watch_route", {probe["id"] for probe in audio_rows[0]["behavioral_probes"]})
        self.assertIn("content_state_materialization_route", {probe["id"] for probe in audio_rows[0]["behavioral_probes"]})
        self.assertIn("wMusicID", audio_rows[0]["state_preconditions"][0]["watch_symbols"])
        self.assertIn("wMusicID", audio_rows[0]["runtime_targets"]["watch_symbols"])
        self.assertIn("--watch-symbol wMusicID", "\n".join(data["commands"]))
        self.assertIn("contains=channel_count", "\n".join(data["commands"]))
