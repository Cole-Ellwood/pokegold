from __future__ import annotations

import unittest

from tools.debugger.deity_runtime import apu_register_timeline_events, script_vm_stream_events
from tools.debugger.runtime_event import (
    hardware_event_required,
    inferred_trace_index_event,
    instruction_record_event,
    runtime_event_envelope,
)


class RuntimeEventTests(unittest.TestCase):
    def test_instruction_record_event_preserves_pre_instruction_precision(self) -> None:
        record = {
            "kind": "sm83_instruction_trace_frame",
            "seq": 7,
            "frame": 12,
            "bank": 1,
            "pc": 0x4000,
            "label": "UnitLabel",
            "registers": {"a": 1, "hl": 0xC000},
        }

        event = instruction_record_event(record, source_report="trace.jsonl")

        self.assertEqual(event["kind"], "runtime_event_envelope")
        self.assertEqual(event["event_kind"], "instruction")
        self.assertEqual(event["proof_status"], "instruction_observed")
        self.assertEqual(event["observation_type"], "instruction_pre_state")
        self.assertEqual(event["pc_bank_address"], "01:4000")
        self.assertEqual(event["payload"], record)
        self.assertEqual(event["evidence_atom"]["proof_status"], "instruction_observed")

    def test_hardware_event_required_stays_planned_only(self) -> None:
        event = hardware_event_required(
            event_kind="apu",
            reason="APU register stream is not implemented",
            source_report="audio_probe.json",
        )

        self.assertEqual(event["event_kind"], "hardware_event")
        self.assertEqual(event["proof_status"], "planned_only")
        self.assertTrue(event["validation"]["hardware_event_required"])
        self.assertIn("APU", event["payload"]["reason"])

    def test_inferred_trace_index_event_marks_inference(self) -> None:
        event = inferred_trace_index_event(
            {
                "event_type": "memory_write",
                "seq": "0x10",
                "pc_bank_address": "03:4567",
                "symbol": "wUnit",
            }
        )

        self.assertEqual(event["event_kind"], "memory_write")
        self.assertEqual(event["observation_type"], "inferred_from_report_fields")
        self.assertTrue(event["scope"]["inferred"])
        self.assertEqual(event["subjects"]["symbols"], ["wUnit"])

    def test_generic_envelope_normalizes_unknown_event_without_claiming_observation(self) -> None:
        event = runtime_event_envelope(
            event_kind="lcd-mode-event",
            source_kind="unit",
            payload={"raw": True},
        )

        self.assertEqual(event["event_kind"], "hardware_event")
        self.assertEqual(event["proof_status"], "planned_only")
        self.assertEqual(event["observation_type"], "planned_only")

    def test_apu_timeline_rows_emit_explicit_hardware_events_on_register_changes(self) -> None:
        events = apu_register_timeline_events(
            [
                {"frame": 0, "pc": 0x4000, "apu": {"rNR10": 1, "rNR11": 2}},
                {"frame": 1, "pc": 0x4001, "apu": {"rNR10": 1, "rNR11": 2}},
                {"frame": 2, "pc": 0x4002, "apu": {"rNR10": 3, "rNR11": 2}},
            ],
            species="TYPHLOSION",
            source_report="audio_probe.json",
        )

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["event_kind"], "hardware_event")
        self.assertEqual(events[0]["observation_type"], "explicit_hardware_event")
        self.assertEqual(events[0]["proof_status"], "runtime_observed")
        self.assertEqual(events[0]["subjects"]["changed_registers"], ["rNR10", "rNR11"])
        self.assertEqual(events[1]["frame"], 2)
        self.assertEqual(events[1]["subjects"]["changed_registers"], ["rNR10"])

    def test_script_vm_rows_emit_runtime_events_on_pointer_changes(self) -> None:
        events = script_vm_stream_events(
            [
                {
                    "frame": 0,
                    "pc": 0x4000,
                    "script_bank": 0x60,
                    "script_pos": 0x4038,
                    "script_mode": 1,
                    "script_running": 0xFF,
                    "script_stack_size": 0,
                },
                {
                    "frame": 1,
                    "pc": 0x4001,
                    "script_bank": 0x60,
                    "script_pos": 0x4038,
                    "script_mode": 1,
                    "script_running": 0xFF,
                    "script_stack_size": 0,
                },
                {
                    "frame": 2,
                    "pc": 0x4002,
                    "script_bank": 0x60,
                    "script_pos": 0x403A,
                    "script_mode": 1,
                    "script_running": 0xFF,
                    "script_stack_size": 0,
                },
            ],
            script_label="ProfElmScript",
            source_report="script_probe.json",
        )

        self.assertEqual(len(events), 3)
        self.assertEqual(events[0]["event_kind"], "script_vm")
        self.assertEqual(events[0]["observation_type"], "frame_sample")
        self.assertEqual(events[0]["proof_status"], "runtime_observed")
        self.assertEqual(events[0]["subjects"]["script_address"], "60:4038")
        self.assertIn("script_pos", events[2]["subjects"]["changed_fields"])


if __name__ == "__main__":
    unittest.main()
