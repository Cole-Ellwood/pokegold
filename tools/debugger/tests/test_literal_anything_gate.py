from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.audit.check_debugger_literal_anything import (
    AFTER_HIT_ORDER_EVIDENCE_ID,
    AFTER_HIT_ORDER_SCENARIO,
    AUDIO_CRY_MUSIC_SFX_BACKEND_PARITY_GAP,
    AUDIO_APU_EVENT_EVIDENCE_ID,
    AUDIO_REMAINING_CRY_MUSIC_SFX_PARITY_GAP,
    AUDIO_TYPHLOSION_CRY_MATCH_EVIDENCE_ID,
    BOSS_AI_GOD_REQUIRED_EVIDENCE_IDS,
    CANONICAL_STATE_CLASS_DAMAGE_MUTATION_EVIDENCE_ID,
    CANONICAL_STATE_CLASS_CONTENT_STATE_MATERIALIZER_EVIDENCE_ID,
    CANONICAL_STATE_CLASS_GLOBAL_GAP,
    CANONICAL_STATE_CLASS_REMAINING_ADOPTION_GAP,
    CANONICAL_STATE_CLASS_SELECTED_ADOPTION_EVIDENCE_ID,
    DAMAGE_FUZZ_MIN_EXAMPLES,
    DAMAGE_FUZZ_NO_DIVERGENCE_EVIDENCE_ID,
    DAMAGE_EXPANDED_MUTATION_CAMPAIGNS_GAP,
    DAMAGE_MODIFIER_RECOIL_EVIDENCE_ID,
    DAMAGE_MODIFIER_RECOIL_SCENARIOS,
    DAMAGE_MUTATION_CAMPAIGN_EVIDENCE_IDS,
    DAMAGE_MUTATION_CAMPAIGN_EVIDENCE_ID,
    DAMAGE_MUTATION_AUTO_MINIMIZED_DIVERGENCE_EVIDENCE_ID,
    DAMAGE_MUTATION_RNG_DISTRIBUTION_EVIDENCE_ID,
    DAMAGE_MUTATION_SELECTED_STATUS_SIDE_EFFECTS_EVIDENCE_ID,
    DAMAGE_MUTATION_SPECIES_WIDE_EVIOLITE_EVIDENCE_ID,
    DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS,
    DAMAGE_MUTATION_REQUIRED_CAMPAIGNS,
    DAMAGE_MUTATION_REQUIRED_IDS,
    DAMAGE_REMAINING_EXPANDED_MUTATION_CAMPAIGNS_GAP,
    DMA_OAM_VRAM_EVENTS_GAP,
    DMA_OAM_VRAM_RUNTIME_EVENT_STREAM_GAP,
    GRAPHICS_BACKEND_LABEL_EVIDENCE_ID,
    GRAPHICS_DIGEST_EVIDENCE_ID,
    HARDWARE_DMA_MODEL_EVIDENCE_ID,
    HARDWARE_DMA_RUNTIME_EVENT_EVIDENCE_ID,
    HARDWARE_INTERRUPT_MODEL_EVIDENCE_ID,
    HARDWARE_INTERRUPT_RUNTIME_EVENT_EVIDENCE_ID,
    HARDWARE_TIMER_LCD_MODEL_EVIDENCE_ID,
    HARDWARE_TIMER_LCD_RUNTIME_EVENT_EVIDENCE_ID,
    HEADLESS_COMPONENT_ROM_DIFFERENTIALS,
    HEADLESS_COMPONENT_ROM_DIFFERENTIAL_EVIDENCE_ID,
    HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP,
    HEADLESS_PROMOTED_TURN_WORKLIST_EVIDENCE_ID,
    HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP,
    HEADLESS_SPIKES_HAZARD_CASES,
    HEADLESS_SPIKES_HAZARD_EVIDENCE_ID,
    INTERRUPT_ENTRY_EXIT_EVENTS_GAP,
    INTERRUPT_ENTRY_EXIT_RUNTIME_EVENT_STREAM_GAP,
    LINK_BOUNDARY_RUNTIME_STATE_CLASS_CORPUS_GAP,
    LINK_BOUNDARY_RUNTIME_STATE_CLASS_CORPUS_EVIDENCE_ID,
    LINK_BOUNDARY_SOURCE_ANCHOR_EVIDENCE_ID,
    LINK_BOUNDARY_SOURCE_ANCHOR_LABELS,
    LINK_BOUNDARY_STATE_CLASSES_GAP,
    MBC_BANK_TRANSITION_MODEL_EVIDENCE_ID,
    MBC_RUNTIME_TRANSITION_REPLAY_EVIDENCE_ID,
    MBC_RUNTIME_TRANSITION_REPLAY_GAP,
    MBC_STATE_TRANSITION_GAP,
    RTC_EDGE_CASE_REPLAY_GAP,
    RTC_HALT_BIT_NEGATIVE_CONTROL_EVIDENCE_ID,
    RTC_HALT_SEMANTICS_RUNTIME_GAP,
    RTC_REGISTER_EDGE_RUNTIME_REPLAY_EVIDENCE_ID,
    RTC_REMAINING_HALT_FREEZE_SEMANTICS_RUNTIME_GAP,
    RTC_RUNTIME_REPLAY_GAP,
    RTC_SOURCE_ANCHOR_EVIDENCE_ID,
    SAVE_FORMAT_SRAM_BANK_EVIDENCE_ID,
    SCRIPT_MAP_CALLBACK_CORPUS_REMAINING_GAP,
    SCRIPT_MAP_CALLBACK_CORPUS_EVIDENCE_ID,
    SCRIPT_MAP_CALLBACK_MATERIALIZER_GAP,
    SCRIPT_MAP_CALLBACK_REMAINING_GAP,
    SCRIPT_MAP_CALLBACK_SELECTED_EVIDENCE_ID,
    SCRIPT_MAP_CONTENT_MATERIALIZER_EVIDENCE_ID,
    SCRIPT_MAP_CONTENT_MATERIALIZER_SCENARIOS,
    SCRIPT_OBJECT_STRUCT_VISIBILITY_EVIDENCE_ID,
    SCRIPT_OBJECT_STRUCT_VISIBILITY_REMAINING_GAP,
    SCRIPT_WARP_OBJECT_COLLISION_REMAINING_GAP,
    SCRIPT_WARP_OBJECT_COLLISION_REPLAY_GAP,
    SCRIPT_WARP_OBJECT_COLLISION_RUNTIME_EVIDENCE_ID,
    SCRIPT_WARP_OBJECT_COLLISION_RUNTIME_REMAINING_GAP,
    SCRIPT_WARP_OBJECT_POSITION_EVIDENCE_ID,
    SERIAL_EVENT_STREAM_GAP,
    SERIAL_REGISTER_WRITE_MODEL_EVIDENCE_ID,
    SERIAL_TRANSFER_RUNTIME_EVENT_EVIDENCE_ID,
    SERIAL_TRANSFER_RUNTIME_EVENT_STREAM_GAP,
    SCRIPT_VM_EVENT_EVIDENCE_ID,
    TIMER_LCD_MODE_EVENTS_GAP,
    TIMER_LCD_MODE_RUNTIME_EVENT_STREAM_GAP,
    after_hit_item_order_status,
    audio_apu_event_envelope_status,
    build_literal_anything_report,
    canonical_state_class_schema_status,
    damage_fuzz_no_divergence_status,
    damage_modifier_recoil_smoke_status,
    damage_mutation_campaign_status,
    dma_oam_vram_runtime_event_stream_status,
    dma_oam_vram_transfer_model_status,
    graphics_backend_label_status,
    graphics_digest_parity_status,
    boss_ai_god_gate_status,
    headless_component_rom_differential_status,
    headless_promoted_turn_worklist_status,
    headless_spikes_hazard_smoke_status,
    interrupt_entry_ime_model_status,
    interrupt_entry_exit_runtime_event_stream_status,
    link_boundary_runtime_state_class_corpus_status,
    link_boundary_source_anchor_status,
    main,
    mbc_bank_transition_model_status,
    mbc_runtime_transition_replay_corpus_status,
    rom_index_artifact_status,
    rom_index_input_hashes,
    rtc_edge_case_source_anchor_status,
    rtc_register_edge_runtime_replay_status,
    save_format_sram_bank_ownership_status,
    script_map_content_materializer_status,
    script_map_content_runtime_replay_status,
    serial_register_write_model_status,
    serial_transfer_runtime_event_stream_status,
    script_vm_event_log_status,
    timer_lcd_mode_runtime_event_stream_status,
    timer_ppu_io_overflow_model_status,
)
from tools.audit.check_save_format_version import compute_fingerprint
from tools.debugger.canonical_state_class import build_canonical_state_class, stable_json_hash
from tools.debugger.runtime_event import runtime_event_envelope


class LiteralAnythingGateTests(unittest.TestCase):
    def test_literal_anything_gate_is_green_with_required_counters(self) -> None:
        report = build_literal_anything_report(read_only=True)
        self.assertTrue(report["literal_anything_ready"], report["blocking_gaps"])
        counters = report["counters"]
        self.assertEqual(counters["unowned_reachable_surface_count"], 0)
        self.assertEqual(counters["unsupported_without_reason"], 0)
        self.assertEqual(counters["partial_pass_count"], 0)
        self.assertEqual(counters["backend_divergence_count"], 0)
        self.assertEqual(counters["stale_artifact_count"], 0)
        self.assertIn("side_effect_unknown_command_count", counters)
        self.assertEqual(counters["side_effect_unknown_command_count"], 0)
        self.assertEqual(report["proof_status"], "complete")
        self.assertEqual(report["blocking_gaps"], [])

        rows = {row["surface_id"]: row for row in report["surfaces"]}
        hardware_row = rows["interrupts_dma_timers_lcd"]
        self.assertEqual(hardware_row["owner_lane"], "runtime_trace")
        self.assertTrue(hardware_row["unsupported_reason"])
        if report["interrupt_entry_ime_model"]["ready"]:
            self.assertNotIn(INTERRUPT_ENTRY_EXIT_EVENTS_GAP, hardware_row["missing_evidence"])
            if report["interrupt_entry_exit_runtime_events"]["ready"]:
                self.assertNotIn(INTERRUPT_ENTRY_EXIT_RUNTIME_EVENT_STREAM_GAP, hardware_row["missing_evidence"])
                self.assertIn(HARDWARE_INTERRUPT_RUNTIME_EVENT_EVIDENCE_ID, report["closed_evidence_ids"])
            else:
                self.assertIn(INTERRUPT_ENTRY_EXIT_RUNTIME_EVENT_STREAM_GAP, hardware_row["missing_evidence"])
        else:
            self.assertIn(INTERRUPT_ENTRY_EXIT_EVENTS_GAP, hardware_row["missing_evidence"])
        if report["dma_oam_vram_transfer_models"]["ready"]:
            self.assertNotIn(DMA_OAM_VRAM_EVENTS_GAP, hardware_row["missing_evidence"])
            if report["dma_oam_vram_runtime_events"]["ready"]:
                self.assertNotIn(DMA_OAM_VRAM_RUNTIME_EVENT_STREAM_GAP, hardware_row["missing_evidence"])
            else:
                self.assertIn(DMA_OAM_VRAM_RUNTIME_EVENT_STREAM_GAP, hardware_row["missing_evidence"])
        else:
            self.assertIn(DMA_OAM_VRAM_EVENTS_GAP, hardware_row["missing_evidence"])
        if report["timer_ppu_io_overflow_models"]["ready"]:
            self.assertNotIn(TIMER_LCD_MODE_EVENTS_GAP, hardware_row["missing_evidence"])
            if report["timer_lcd_mode_runtime_events"]["ready"]:
                self.assertNotIn(TIMER_LCD_MODE_RUNTIME_EVENT_STREAM_GAP, hardware_row["missing_evidence"])
                self.assertIn(HARDWARE_TIMER_LCD_RUNTIME_EVENT_EVIDENCE_ID, report["closed_evidence_ids"])
            else:
                self.assertIn(TIMER_LCD_MODE_RUNTIME_EVENT_STREAM_GAP, hardware_row["missing_evidence"])
        else:
            self.assertIn(TIMER_LCD_MODE_EVENTS_GAP, hardware_row["missing_evidence"])
        self.assertEqual(hardware_row["proof_status"], "runtime_proven")
        self.assertEqual(hardware_row["backend"], "pyboy_static_model_with_named_timing_limit")

        link_row = rows["link_serial_mystery_gift"]
        self.assertEqual(link_row["owner_lane"], "runtime_trace")
        self.assertTrue(link_row["unsupported_reason"])
        if report["serial_register_write_model"]["ready"]:
            self.assertNotIn(SERIAL_EVENT_STREAM_GAP, link_row["missing_evidence"])
            if report["serial_transfer_runtime_events"]["ready"]:
                self.assertIn(SERIAL_TRANSFER_RUNTIME_EVENT_EVIDENCE_ID, report["closed_evidence_ids"])
                self.assertNotIn(SERIAL_TRANSFER_RUNTIME_EVENT_STREAM_GAP, link_row["missing_evidence"])
            else:
                self.assertIn(SERIAL_TRANSFER_RUNTIME_EVENT_STREAM_GAP, link_row["missing_evidence"])
        else:
            self.assertIn(SERIAL_EVENT_STREAM_GAP, link_row["missing_evidence"])
        if report["link_boundary_source_anchors"]["ready"]:
            self.assertNotIn(LINK_BOUNDARY_STATE_CLASSES_GAP, link_row["missing_evidence"])
            if report["link_boundary_runtime_state_class_corpus"]["ready"]:
                self.assertNotIn(LINK_BOUNDARY_RUNTIME_STATE_CLASS_CORPUS_GAP, link_row["missing_evidence"])
            else:
                self.assertIn(LINK_BOUNDARY_RUNTIME_STATE_CLASS_CORPUS_GAP, link_row["missing_evidence"])
        else:
            self.assertIn(LINK_BOUNDARY_STATE_CLASSES_GAP, link_row["missing_evidence"])
        self.assertEqual(link_row["proof_status"], "runtime_proven")
        self.assertEqual(link_row["backend"], "pyboy_static_model_with_named_link_limit")
        save_row = rows["save_rtc_mbc"]
        self.assertEqual(save_row["owner_lane"], "save_rtc_mbc_state")
        if report["rtc_edge_case_source_anchors"]["ready"]:
            self.assertNotIn(RTC_EDGE_CASE_REPLAY_GAP, save_row["missing_evidence"])
            if report["rtc_register_edge_runtime_replay"]["ready"]:
                self.assertNotIn(RTC_RUNTIME_REPLAY_GAP, save_row["missing_evidence"])
                self.assertNotIn(RTC_HALT_SEMANTICS_RUNTIME_GAP, save_row["missing_evidence"])
                self.assertIn(RTC_REGISTER_EDGE_RUNTIME_REPLAY_EVIDENCE_ID, report["closed_evidence_ids"])
                self.assertIn(RTC_HALT_BIT_NEGATIVE_CONTROL_EVIDENCE_ID, report["closed_evidence_ids"])
            else:
                self.assertIn(RTC_RUNTIME_REPLAY_GAP, save_row["missing_evidence"])
        else:
            self.assertIn(RTC_EDGE_CASE_REPLAY_GAP, save_row["missing_evidence"])
        if report["mbc_bank_transition_model"]["ready"]:
            self.assertNotIn(MBC_STATE_TRANSITION_GAP, save_row["missing_evidence"])
            if report["mbc_runtime_transition_replay_corpus"]["ready"]:
                self.assertNotIn(MBC_RUNTIME_TRANSITION_REPLAY_GAP, save_row["missing_evidence"])
                self.assertIn(MBC_RUNTIME_TRANSITION_REPLAY_EVIDENCE_ID, report["closed_evidence_ids"])
            else:
                self.assertIn(MBC_RUNTIME_TRANSITION_REPLAY_GAP, save_row["missing_evidence"])
        else:
            self.assertIn(MBC_STATE_TRANSITION_GAP, save_row["missing_evidence"])
        self.assertTrue(save_row["unsupported_reason"])
        if report["save_format_sram_bank_ownership"]["ready"]:
            self.assertNotIn("sram_bank_ownership", save_row["missing_evidence"])
            self.assertIn(SAVE_FORMAT_SRAM_BANK_EVIDENCE_ID, report["closed_evidence_ids"])
        else:
            self.assertEqual(save_row["proof_status"], "unsupported")
            self.assertEqual(save_row["backend"], "none")
            self.assertIn("sram_bank_ownership", save_row["missing_evidence"])
        self.assertEqual(save_row["proof_status"], "runtime_proven")
        self.assertEqual(save_row["backend"], "pyboy_plus_static_with_named_rtc_limit")

    def test_read_only_baseline_does_not_write_outputs(self) -> None:
        captured = io.StringIO()
        with redirect_stdout(captured):
            rc = main(["--baseline", "--read-only", "--json"])
        payload = json.loads(captured.getvalue())
        self.assertEqual(rc, 0 if payload["literal_anything_ready"] else 1)
        self.assertFalse(payload["read_only_mode"]["would_write_baseline"])
        self.assertTrue(payload["read_only_mode"]["baseline_write_refused"])
        self.assertTrue(payload["read_only_mode"]["global_command_refusal_enforced"])
        self.assertIn("read_only_command_refusal.enforced", payload["closed_evidence_ids"])
        self.assertNotIn("json_out", payload)

    def test_self_test_accepts_roadmap_command_shape(self) -> None:
        captured = io.StringIO()
        with redirect_stdout(captured):
            rc = main(["--self-test", "--baseline", "--read-only"])
        self.assertEqual(rc, 0)
        self.assertIn("SELF-TEST PASS", captured.getvalue())

    def test_next_commands_are_not_placeholder_templates(self) -> None:
        report = build_literal_anything_report(read_only=True)
        commands = [row["next_command"] for row in report["surfaces"]]
        self.assertFalse([command for command in commands if "<" in command or ">" in command])

    def test_rom_byte_surface_tracks_remaining_jsonl_gap_after_lookup_command(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["rom_byte_index"]
        self.assertIn("rom-byte --address", row["next_command"])
        self.assertNotIn("confidence_scored_source_lookup", row["missing_evidence"])
        self.assertIn("rom_byte_lookup.confidence_scored_source_lookup", report["closed_evidence_ids"])
        if report["rom_index_artifacts"]["ready"]:
            self.assertNotIn("rom_surface_index_jsonl", row["missing_evidence"])
            self.assertNotIn("rom_byte_index_jsonl", row["missing_evidence"])
            self.assertIn("rom_index_jsonl.generated", report["closed_evidence_ids"])
        if report["content_mirror_span_artifact"]["ready"]:
            self.assertNotIn("content_mirror_exact_span_rows", row["missing_evidence"])
            self.assertIn("content_mirror_exact_span_rows.reported", report["closed_evidence_ids"])
        if report["rom_index_artifacts"]["ready"] and report["content_mirror_span_artifact"]["ready"]:
            self.assertEqual(row["proof_status"], "static_proven")

    def test_generated_rom_inventory_closes_only_inventory_generated_gap(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["unified_debugger_front_door"]
        if report["rom_index_artifacts"]["ready"]:
            self.assertNotIn("whole_rom_surface_inventory", row["missing_evidence"])
            self.assertNotIn("whole-ROM surface inventory is not generated", report["blocking_gaps"])
            self.assertIn("whole_rom_surface_inventory.generated", report["closed_evidence_ids"])
            if report["literal_anything_ready"]:
                self.assertEqual(row["proof_status"], "complete")
                self.assertNotIn("no_partial_pass_literal_anything_gate", row["missing_evidence"])
                self.assertNotIn("no_partial_pass_literal_anything_gate", report["blocking_gaps"])
        else:
            self.assertIn("whole_rom_surface_inventory", row["missing_evidence"])
            if report["rom_index_artifacts"]["stale_artifact_count"]:
                self.assertIn("rom_index_artifacts_stale", report["blocking_gaps"])
            else:
                self.assertIn("whole-ROM surface inventory is not generated", report["blocking_gaps"])

    def test_boss_ai_class_adoption_gap_closes_when_god_gate_probe_is_ready(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["boss_ai_debugger"]
        if report["boss_ai_class_adoption"]["ready"]:
            self.assertNotIn(
                "boss_ai_live_trace_and_contribution_class_ids_not_integrated",
                row["missing_evidence"],
            )
            self.assertNotIn(
                "boss_ai_live_trace_and_contribution_class_ids_not_integrated",
                report["blocking_gaps"],
            )
            self.assertIn("boss_ai_live_trace_class_ids.validated", report["closed_evidence_ids"])
            self.assertIn("boss_ai_contribution_trace_class_ids.validated", report["closed_evidence_ids"])
            if report["boss_ai_god_gate"]["ready"]:
                self.assertEqual(row["missing_evidence"], [])
                self.assertEqual(row["proof_status"], "runtime_proven")
            else:
                self.assertIn("boss_ai_universe_not_complete", row["missing_evidence"])
        else:
            self.assertIn(
                "boss_ai_live_trace_and_contribution_class_ids_not_integrated",
                row["missing_evidence"],
            )

    def _write_boss_ai_god_gate_fixture(
        self,
        root: Path,
        *,
        omit_closed_id: str = "",
        green_gate: bool = False,
        missing_universe_blocker: bool = False,
        artifact_name: str = "baseline_2026-05-31.json",
    ) -> Path:
        for path in (
            root / "tools" / "audit" / "check_boss_ai_debugger_god.py",
            root / "tools" / "boss_ai_debugger" / "universe.py",
            root / "audit" / "boss_ai_debugger" / "god_level_benchmark" / "questions.jsonl",
            root / "audit" / "boss_ai_debugger" / "rule_map.json",
            root / "audit" / "boss_ai_debugger" / "coverage_report.json",
            root / "audit" / "boss_ai_debugger" / "god_level_benchmark" / "artifacts" / "changed_ai.json",
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}", encoding="utf-8")
        closed = [item for item in BOSS_AI_GOD_REQUIRED_EVIDENCE_IDS if item != omit_closed_id]
        blockers = [] if green_gate else ["boss_ai_exhaustive_class_witness_roles_missing"]
        if not green_gate and not missing_universe_blocker:
            blockers.append("boss_ai_universe_not_complete")
        artifact = root / "audit" / "boss_ai_debugger" / "god_level_benchmark" / artifact_name
        artifact.write_text(
            json.dumps(
                {
                    "kind": "boss_ai_debugger_god_gate",
                    "proof_status": "complete" if green_gate else "missing_evidence",
                    "boss_ai_god_ready": green_gate,
                    "closed_evidence_ids": closed,
                    "blocking_gaps": blockers,
                    "counters": {
                        "missing_reachable_label_count": 0,
                        "missing_rule_count": 0,
                        "missing_branch_count": 0,
                        "missing_public_read_count": 0,
                        "missing_class_id_count": 0,
                        "missing_materialization_path_count": 0,
                        "missing_witness_role_count": 0 if green_gate else 575,
                    },
                    "canonical_class_coverage": {
                        "ready": True,
                        "valid_class_id_count": 195,
                    },
                    "changed_ai_god_suite": {
                        "partial_evidence_ready": True,
                        "completion_ready": True,
                        "blocking_gaps": [],
                        "evidence_artifacts": [
                            "audit/boss_ai_debugger/god_level_benchmark/artifacts/changed_ai.json"
                        ],
                    },
                }
            ),
            encoding="utf-8",
        )
        return artifact

    def test_boss_ai_god_gate_bridge_imports_precise_closed_ids_only(self) -> None:
        report = build_literal_anything_report(read_only=True)
        if report["boss_ai_god_gate"]["ready"]:
            for evidence_id in BOSS_AI_GOD_REQUIRED_EVIDENCE_IDS:
                self.assertIn(evidence_id, report["closed_evidence_ids"])
            self.assertNotIn("boss_ai_universe_not_complete", report["missing_evidence"])
            self.assertNotIn("exhaustive_class_proofs", report["missing_evidence"])

    def test_boss_ai_god_gate_status_accepts_red_partial_evidence_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_boss_ai_god_gate_fixture(root)

            status = boss_ai_god_gate_status(root=root)

        self.assertTrue(status["bridge_valid"])
        self.assertFalse(status["ready"])
        self.assertEqual(status["missing_witness_role_count"], 575)
        self.assertIn("boss_ai_universe_not_complete", status["blocking_gaps"])
        for evidence_id in BOSS_AI_GOD_REQUIRED_EVIDENCE_IDS:
            self.assertIn(evidence_id, status["closed_evidence_ids"])

    def test_boss_ai_god_gate_status_uses_newest_baseline_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = BOSS_AI_GOD_REQUIRED_EVIDENCE_IDS[0]
            self._write_boss_ai_god_gate_fixture(root, omit_closed_id=missing)
            self._write_boss_ai_god_gate_fixture(root, artifact_name="baseline_2026-06-01.json")

            status = boss_ai_god_gate_status(root=root)

        self.assertTrue(status["bridge_valid"], status["errors"])
        self.assertFalse(status["ready"])
        self.assertEqual(
            status["path"],
            "audit/boss_ai_debugger/god_level_benchmark/baseline_2026-06-01.json",
        )
        self.assertFalse(any(missing in error for error in status["errors"]))

    def test_boss_ai_god_gate_status_fails_closed_without_expected_evidence_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = BOSS_AI_GOD_REQUIRED_EVIDENCE_IDS[0]
            self._write_boss_ai_god_gate_fixture(root, omit_closed_id=missing)

            status = boss_ai_god_gate_status(root=root)

        self.assertFalse(status["ready"])
        self.assertTrue(any(missing in error for error in status["errors"]))

    def test_boss_ai_god_gate_status_accepts_complete_green_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_boss_ai_god_gate_fixture(root, green_gate=True)

            status = boss_ai_god_gate_status(root=root)

        self.assertTrue(status["bridge_valid"], status["errors"])
        self.assertTrue(status["ready"])
        self.assertEqual(status["blocking_gaps"], [])

    def test_boss_ai_god_gate_status_fails_closed_when_incomplete_blocker_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_boss_ai_god_gate_fixture(root, missing_universe_blocker=True)

            status = boss_ai_god_gate_status(root=root)

        self.assertFalse(status["bridge_valid"])
        self.assertFalse(status["ready"])
        self.assertIn("Boss God gate must leave boss_ai_universe_not_complete open while incomplete", status["errors"])

    def test_headless_battle_class_adoption_closes_only_turn_level_class_gap(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["headless_battle"]
        if report["headless_battle_class_adoption"]["ready"]:
            self.assertNotIn("turn_level_class_ids", row["missing_evidence"])
            if report["headless_component_rom_differentials"]["ready"]:
                self.assertNotIn(HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP, row["missing_evidence"])
                if report["headless_promoted_turn_worklist"]["ready"]:
                    self.assertNotIn(HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP, row["missing_evidence"])
                else:
                    self.assertIn(HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP, row["missing_evidence"])
            else:
                self.assertIn(HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP, row["missing_evidence"])
            self.assertIn(
                "headless_battle_turn_level_class_ids.validated",
                report["closed_evidence_ids"],
            )
            if report["canonical_state_class_schema"]["selected_surface_adoption_ready"]:
                self.assertNotIn(CANONICAL_STATE_CLASS_GLOBAL_GAP, report["blocking_gaps"])
                self.assertNotIn(CANONICAL_STATE_CLASS_REMAINING_ADOPTION_GAP, report["blocking_gaps"])
                self.assertIn(
                    CANONICAL_STATE_CLASS_SELECTED_ADOPTION_EVIDENCE_ID,
                    report["closed_evidence_ids"],
                )
            else:
                self.assertIn(CANONICAL_STATE_CLASS_GLOBAL_GAP, report["blocking_gaps"])
        else:
            self.assertIn("turn_level_class_ids", row["missing_evidence"])

    def test_canonical_state_class_schema_status_validates_core_schema_contract(self) -> None:
        status = canonical_state_class_schema_status()

        self.assertTrue(status["ready"])
        self.assertEqual(status["schema_version"], 1)
        self.assertIn("boss_ai", status["validated_surface_buckets"])
        self.assertIn("battle", status["validated_surface_buckets"])
        self.assertIn("runtime", status["validated_surface_buckets"])
        self.assertRegex(status["stable_class_id"], r"^csc_[0-9A-F]{20}$")
        self.assertTrue(status["hidden_fact_rejection"])

    def test_canonical_state_class_schema_status_fails_closed_without_identity_basis(self) -> None:
        status = canonical_state_class_schema_status(identity={"rom_sha256": "A" * 64})

        self.assertFalse(status["ready"])
        self.assertTrue(
            any("valid canonical class rejected" in error for error in status["errors"])
        )

    def test_canonical_state_class_selected_adoption_closes_global_gap(self) -> None:
        report = build_literal_anything_report(read_only=True)
        status = report["canonical_state_class_schema"]

        if status["selected_surface_adoption_ready"]:
            self.assertNotIn(CANONICAL_STATE_CLASS_GLOBAL_GAP, report["missing_evidence"])
            self.assertNotIn(CANONICAL_STATE_CLASS_GLOBAL_GAP, report["blocking_gaps"])
            self.assertNotIn(CANONICAL_STATE_CLASS_REMAINING_ADOPTION_GAP, report["missing_evidence"])
            self.assertNotIn(CANONICAL_STATE_CLASS_REMAINING_ADOPTION_GAP, report["blocking_gaps"])
            self.assertIn(CANONICAL_STATE_CLASS_SELECTED_ADOPTION_EVIDENCE_ID, report["closed_evidence_ids"])
            self.assertTrue(status["selected_surface_adoptions"]["boss_ai"])
            self.assertTrue(status["selected_surface_adoptions"]["headless_battle"])
            self.assertIn("content_state_materializers", status["selected_surface_adoptions"])
            self.assertTrue(status["selected_surface_adoptions"]["content_state_materializers"])
            self.assertTrue(status["selected_surface_adoptions"]["damage_mutation_campaign"])
        else:
            self.assertIn(CANONICAL_STATE_CLASS_GLOBAL_GAP, report["missing_evidence"])

    def test_headless_spikes_hazard_smoke_preserves_current_rom_differential_gap(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["headless_battle"]
        if report["headless_component_rom_differentials"]["ready"]:
            self.assertNotIn(HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP, row["missing_evidence"])
            if report["headless_promoted_turn_worklist"]["ready"]:
                self.assertNotIn(HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP, row["missing_evidence"])
            else:
                self.assertIn(HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP, row["missing_evidence"])
        else:
            self.assertIn(HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP, row["missing_evidence"])
        if report["headless_spikes_hazard_smoke"]["ready"]:
            self.assertIn(HEADLESS_SPIKES_HAZARD_EVIDENCE_ID, report["closed_evidence_ids"])
        else:
            self.assertNotIn(HEADLESS_SPIKES_HAZARD_EVIDENCE_ID, report["closed_evidence_ids"])

    def test_headless_component_rom_differentials_replace_broad_gap_with_residual_gap(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["headless_battle"]
        if report["headless_component_rom_differentials"]["ready"]:
            self.assertIn(HEADLESS_COMPONENT_ROM_DIFFERENTIAL_EVIDENCE_ID, report["closed_evidence_ids"])
            self.assertNotIn(HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP, row["missing_evidence"])
            self.assertNotIn(HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP, report["missing_evidence"])
            if report["headless_promoted_turn_worklist"]["ready"]:
                self.assertNotIn(HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP, row["missing_evidence"])
                self.assertNotIn(HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP, report["missing_evidence"])
            else:
                self.assertIn(HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP, row["missing_evidence"])
                self.assertIn(HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP, report["missing_evidence"])
        else:
            self.assertIn(HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP, row["missing_evidence"])
            self.assertNotIn(HEADLESS_COMPONENT_ROM_DIFFERENTIAL_EVIDENCE_ID, report["closed_evidence_ids"])

    def test_complete_headless_component_rom_differential_artifact_narrows_report_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_component_rom_differential_report(root)

            report = build_literal_anything_report(root=root, read_only=True)

        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["headless_battle"]
        self.assertNotIn(HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP, row["missing_evidence"])
        self.assertNotIn(HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP, report["missing_evidence"])
        self.assertNotIn(HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP, report["blocking_gaps"])
        self.assertIn(HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP, row["missing_evidence"])
        self.assertIn(HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP, report["missing_evidence"])
        self.assertIn(HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP, report["blocking_gaps"])
        self.assertIn(HEADLESS_COMPONENT_ROM_DIFFERENTIAL_EVIDENCE_ID, report["closed_evidence_ids"])

    def test_incomplete_headless_component_rom_differential_artifact_keeps_broad_report_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_component_rom_differential_report(
                root,
                scenarios=HEADLESS_COMPONENT_ROM_DIFFERENTIALS[:-1],
            )

            report = build_literal_anything_report(root=root, read_only=True)

        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["headless_battle"]
        self.assertIn(HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP, row["missing_evidence"])
        self.assertIn(HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP, report["missing_evidence"])
        self.assertIn(HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP, report["blocking_gaps"])
        self.assertNotIn(HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP, row["missing_evidence"])
        self.assertNotIn(HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP, report["missing_evidence"])
        self.assertNotIn(HEADLESS_COMPONENT_ROM_DIFFERENTIAL_EVIDENCE_ID, report["closed_evidence_ids"])

    def _write_component_rom_differential_report(
        self,
        root: Path,
        scenarios: tuple[str, ...] = HEADLESS_COMPONENT_ROM_DIFFERENTIALS,
        *,
        proof_status: str = "complete",
    ) -> Path:
        out_dir = root / "audit" / "headless_battle"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "rom_differential.json"
        results = [
            {
                "scenario_id": scenario,
                "ok": True,
                "errors": [],
                "rom": {"observed": scenario},
                "headless": {"observed": scenario},
            }
            for scenario in scenarios
        ]
        path.write_text(
            json.dumps(
                {
                    "kind": "headless_battle_component_rom_differential",
                    "proof_status": proof_status,
                    "scenario_count": len(results),
                    "pass_count": len(results),
                    "fail_count": 0 if proof_status == "complete" else 1,
                    "results": results,
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_headless_component_rom_differential_status_accepts_required_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_component_rom_differential_report(root)

            status = headless_component_rom_differential_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["scenario_count"], len(HEADLESS_COMPONENT_ROM_DIFFERENTIALS))

    def test_headless_component_rom_differential_status_fails_closed_without_named_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_component_rom_differential_report(root, scenarios=HEADLESS_COMPONENT_ROM_DIFFERENTIALS[:-1])

            status = headless_component_rom_differential_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn(HEADLESS_COMPONENT_ROM_DIFFERENTIALS[-1], status["missing_scenarios"])

    def test_headless_component_rom_differential_status_fails_closed_when_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = self._write_component_rom_differential_report(root)
            source_path = root / "tools" / "headless_battle" / "rom_differential.py"
            source_path.parent.mkdir(parents=True)
            source_path.write_text("# newer proof input\n", encoding="utf-8")
            os.utime(artifact, (100, 100))
            os.utime(source_path, (200, 200))

            status = headless_component_rom_differential_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("headless component ROM differential artifact is older than proof inputs", status["errors"])

    def _write_promoted_turn_worklist(
        self,
        root: Path,
        *,
        proof_status: str = "worklist_only",
        closed_evidence_ids: list[str] | None = None,
        omit_last_row: bool = False,
        row_proof_status: str = "source_mirrored_pending_differential",
        row_blocking_gaps: list[str] | None = None,
        row_closed_evidence_ids: list[str] | None = None,
    ) -> Path:
        from tools.headless_battle.simulator import coverage_report

        rows = coverage_report()["source_mirrored_pending_differential"]
        if omit_last_row:
            rows = rows[:-1]
        out_dir = root / "audit" / "headless_battle"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "promoted_turn_differential_worklist.json"
        blocking_gaps = (
            row_blocking_gaps
            if row_blocking_gaps is not None
            else [HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP]
        )
        payload_rows = [
            {
                "kind": "headless_battle_promoted_turn_differential_worklist_row",
                "id": row["id"],
                "source": row["source"],
                "gate": row["gate"],
                "notes": row["notes"],
                "proof_status": row_proof_status,
                "turn_differential_status": "pending_rom_turn_differential",
                "missing_evidence": ["rom_backed_turn_differential"],
                "blocking_gaps": blocking_gaps,
                "does_not_close": [HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP],
                "closed_evidence_ids": row_closed_evidence_ids or [],
            }
            for row in rows
        ]
        path.write_text(
            json.dumps(
                {
                    "kind": "headless_battle_promoted_turn_differential_worklist",
                    "proof_status": proof_status,
                    "source": "tools.headless_battle.simulator.coverage_report",
                    "source_path": "tools/headless_battle/simulator.py",
                    "missing_evidence": [HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP],
                    "blocking_gaps": [HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP],
                    "does_not_close": [HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP],
                    "closed_evidence_ids": closed_evidence_ids
                    if closed_evidence_ids is not None
                    else [HEADLESS_PROMOTED_TURN_WORKLIST_EVIDENCE_ID],
                    "row_count": len(payload_rows),
                    "pending_turn_differential_count": len(payload_rows),
                    "rows": payload_rows,
                    "component_rom_differentials": {
                        "path": "audit/headless_battle/rom_differential.json",
                        "exists": True,
                    },
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_headless_promoted_turn_worklist_closes_only_catalog_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_component_rom_differential_report(root)
            self._write_promoted_turn_worklist(root)

            report = build_literal_anything_report(root=root, read_only=True)

        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["headless_battle"]
        self.assertIn(HEADLESS_COMPONENT_ROM_DIFFERENTIAL_EVIDENCE_ID, report["closed_evidence_ids"])
        self.assertIn(HEADLESS_PROMOTED_TURN_WORKLIST_EVIDENCE_ID, report["closed_evidence_ids"])
        self.assertNotIn(HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP, row["missing_evidence"])
        self.assertNotIn(HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP, row["missing_evidence"])
        self.assertNotIn(HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP, report["blocking_gaps"])
        self.assertEqual(row["proof_status"], "runtime_proven")
        self.assertTrue(row["unsupported_reason"])

    def test_headless_promoted_turn_worklist_alone_keeps_broad_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_promoted_turn_worklist(root)

            report = build_literal_anything_report(root=root, read_only=True)

        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["headless_battle"]
        self.assertIn(HEADLESS_PROMOTED_TURN_WORKLIST_EVIDENCE_ID, report["closed_evidence_ids"])
        self.assertNotIn(HEADLESS_COMPONENT_ROM_DIFFERENTIAL_EVIDENCE_ID, report["closed_evidence_ids"])
        self.assertIn(HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP, row["missing_evidence"])
        self.assertIn(HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP, report["blocking_gaps"])
        self.assertNotIn(HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP, row["missing_evidence"])

    def test_headless_promoted_turn_worklist_status_accepts_pending_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_promoted_turn_worklist(root)

            status = headless_promoted_turn_worklist_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["row_count"], status["pending_turn_differential_count"])
        self.assertGreater(status["row_count"], 0)

    def test_headless_promoted_turn_worklist_status_fails_closed_when_closing_extra_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_promoted_turn_worklist(
                root,
                closed_evidence_ids=[
                    HEADLESS_PROMOTED_TURN_WORKLIST_EVIDENCE_ID,
                    "claimed_promoted_turn_differential",
                ],
            )

            status = headless_promoted_turn_worklist_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn(
            "worklist must close only the narrow promoted-turn worklist evidence id",
            status["errors"],
        )

    def test_headless_promoted_turn_worklist_status_fails_closed_when_row_claims_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_promoted_turn_worklist(
                root,
                row_proof_status="complete",
                row_closed_evidence_ids=["claimed_turn_differential"],
            )

            status = headless_promoted_turn_worklist_status(root=root)

        self.assertFalse(status["ready"])
        self.assertTrue(
            any("must remain source-mirrored pending differential" in error for error in status["errors"])
        )
        self.assertTrue(any("must not close evidence" in error for error in status["errors"]))

    def test_headless_promoted_turn_worklist_status_fails_closed_without_current_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_promoted_turn_worklist(root, omit_last_row=True)

            status = headless_promoted_turn_worklist_status(root=root)

        self.assertFalse(status["ready"])
        self.assertTrue(status["missing_source_ids"])

    def _write_hazard_smoke_log(self, root: Path, cases: tuple[str, ...] = HEADLESS_SPIKES_HAZARD_CASES) -> None:
        out_dir = root / "audit" / "damage_debugger"
        out_dir.mkdir(parents=True)
        (out_dir / "hazard_smoke.log").write_text(
            "\n".join([f"PASS {case} proof row" for case in cases])
            + "\nPASS: all hazard smoke cases matched expected state.\n",
            encoding="utf-8",
        )

    def test_headless_spikes_hazard_smoke_status_accepts_required_pass_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_hazard_smoke_log(root)

            status = headless_spikes_hazard_smoke_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["case_count"], len(HEADLESS_SPIKES_HAZARD_CASES))

    def test_headless_spikes_hazard_smoke_status_fails_closed_without_named_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_hazard_smoke_log(root, cases=HEADLESS_SPIKES_HAZARD_CASES[:-1])

            status = headless_spikes_hazard_smoke_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn(HEADLESS_SPIKES_HAZARD_CASES[-1], status["missing_cases"])

    def test_headless_spikes_hazard_smoke_status_fails_closed_when_log_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_hazard_smoke_log(root)
            log_path = root / "audit" / "damage_debugger" / "hazard_smoke.log"
            source_path = root / "tools" / "damage_debugger" / "hazard_smoke.py"
            source_path.parent.mkdir(parents=True)
            source_path.write_text("# newer proof input\n", encoding="utf-8")
            os.utime(log_path, (100, 100))
            os.utime(source_path, (200, 200))

            status = headless_spikes_hazard_smoke_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("hazard_smoke log is older than Spikes hazard proof inputs", status["errors"])
        self.assertTrue(any("hazard_smoke.py" in item for item in status["stale_dependencies"]))

    def test_save_format_sram_bank_ownership_closes_only_sram_gap(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["save_rtc_mbc"]
        if report["rtc_edge_case_source_anchors"]["ready"]:
            self.assertNotIn(RTC_EDGE_CASE_REPLAY_GAP, row["missing_evidence"])
            if report["rtc_register_edge_runtime_replay"]["ready"]:
                self.assertNotIn(RTC_RUNTIME_REPLAY_GAP, row["missing_evidence"])
                self.assertNotIn(RTC_HALT_SEMANTICS_RUNTIME_GAP, row["missing_evidence"])
                if report["mbc_runtime_transition_replay_corpus"]["ready"]:
                    self.assertNotIn(RTC_REMAINING_HALT_FREEZE_SEMANTICS_RUNTIME_GAP, row["missing_evidence"])
                else:
                    self.assertIn(RTC_REMAINING_HALT_FREEZE_SEMANTICS_RUNTIME_GAP, row["missing_evidence"])
                self.assertIn(RTC_REGISTER_EDGE_RUNTIME_REPLAY_EVIDENCE_ID, report["closed_evidence_ids"])
                self.assertIn(RTC_HALT_BIT_NEGATIVE_CONTROL_EVIDENCE_ID, report["closed_evidence_ids"])
            else:
                self.assertIn(RTC_RUNTIME_REPLAY_GAP, row["missing_evidence"])
            self.assertIn(RTC_SOURCE_ANCHOR_EVIDENCE_ID, report["closed_evidence_ids"])
        else:
            self.assertIn(RTC_EDGE_CASE_REPLAY_GAP, row["missing_evidence"])
        if report["mbc_bank_transition_model"]["ready"]:
            self.assertNotIn(MBC_STATE_TRANSITION_GAP, row["missing_evidence"])
            if report["mbc_runtime_transition_replay_corpus"]["ready"]:
                self.assertNotIn(MBC_RUNTIME_TRANSITION_REPLAY_GAP, row["missing_evidence"])
                self.assertIn(MBC_RUNTIME_TRANSITION_REPLAY_EVIDENCE_ID, report["closed_evidence_ids"])
            else:
                self.assertIn(MBC_RUNTIME_TRANSITION_REPLAY_GAP, row["missing_evidence"])
            self.assertIn(MBC_BANK_TRANSITION_MODEL_EVIDENCE_ID, report["closed_evidence_ids"])
        else:
            self.assertIn(MBC_STATE_TRANSITION_GAP, row["missing_evidence"])
        if report["save_format_sram_bank_ownership"]["ready"]:
            self.assertNotIn("sram_bank_ownership", row["missing_evidence"])
            self.assertIn(SAVE_FORMAT_SRAM_BANK_EVIDENCE_ID, report["closed_evidence_ids"])
        else:
            self.assertIn("sram_bank_ownership", row["missing_evidence"])

    def _write_rtc_source_anchor_fixture(self, root: Path, *, include_set_clock: bool = True) -> None:
        (root / "home").mkdir(parents=True)
        (root / "engine" / "rtc").mkdir(parents=True)
        (root / "audit" / "debugger_literal_anything").mkdir(parents=True)
        home_labels = ["LatchClock", "GetClock", "FixDays"]
        if include_set_clock:
            home_labels.append("SetClock")
        (root / "home" / "time.asm").write_text(
            "\n".join(f"{label}::" for label in home_labels) + "\n",
            encoding="utf-8",
        )
        (root / "engine" / "rtc" / "rtc.asm").write_text(
            "SaveRTC:\n_GetClock:\n_FixDays:\n",
            encoding="utf-8",
        )
        rows = [
            {"kind": "rom_surface_index_row", "surface_id": f"symbol:00:4000:{label}", "nearest_label": label}
            for label in ("LatchClock", "GetClock", "FixDays", "SetClock", "SaveRTC", "_GetClock", "_FixDays")
        ]
        (root / "audit" / "debugger_literal_anything" / "rom_surface_index.jsonl").write_text(
            "\n".join(json.dumps(row) for row in rows) + "\n",
            encoding="utf-8",
        )

    def test_rtc_edge_case_source_anchor_status_accepts_source_and_index_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_rtc_source_anchor_fixture(root)

            status = rtc_edge_case_source_anchor_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["source_anchor_count"], 7)
        self.assertEqual(status["indexed_label_count"], 7)

    def test_rtc_edge_case_source_anchor_status_fails_closed_without_source_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_rtc_source_anchor_fixture(root, include_set_clock=False)

            status = rtc_edge_case_source_anchor_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("SetClock", status["missing_source_labels"])

    def _write_rtc_register_edge_runtime_fixture(
        self,
        root: Path,
        *,
        omit_case: str = "",
        claim_halt_semantics: bool = False,
        bad_event_scope: bool = False,
        halt_seconds_advanced: bool | None = True,
    ) -> Path:
        out_dir = root / "audit" / "debugger_literal_anything"
        out_dir.mkdir(parents=True)
        case_specs = {
            "rtc_day_high_carry_register_write_readback": {
                "transition_kind": "rtc_register_write_carry_readback",
                "carry_set_readback": True,
                "carry_clear_readback": True,
            },
            "rtc_halt_bit_readback_nonsemantic_control": {
                "transition_kind": "rtc_halt_bit_readback_nonsemantic_control",
                "halt_bit_readback": True,
            },
            "rtc_seeded_day_511_no_carry_readback": {
                "transition_kind": "rtc_seeded_day_counter_readback",
                "day_low_matches": True,
                "day_high_day_bit_matches": True,
                "carry_matches": True,
                "seeded_elapsed_days": 511,
                "observed_carry": False,
            },
            "rtc_seeded_day_512_carry_overflow_readback": {
                "transition_kind": "rtc_seeded_day_counter_readback",
                "day_low_matches": True,
                "day_high_day_bit_matches": True,
                "carry_matches": True,
                "seeded_elapsed_days": 512,
                "observed_carry": True,
            },
            "rtc_seeded_day_513_carry_overflow_readback": {
                "transition_kind": "rtc_seeded_day_counter_readback",
                "day_low_matches": True,
                "day_high_day_bit_matches": True,
                "carry_matches": True,
                "seeded_elapsed_days": 513,
                "observed_carry": True,
            },
        }
        cases = []
        events = []
        for index, (case_id, spec) in enumerate(case_specs.items()):
            if case_id == omit_case:
                continue
            case = {
                "case_id": case_id,
                "transition_kind": spec["transition_kind"],
                "write_range": "$4000-$5FFF,$6000-$7FFF,$A000-$BFFF",
                "transition_observed": True,
                "halt_semantics_proven": claim_halt_semantics,
                **spec,
            }
            if case_id == "rtc_halt_bit_readback_nonsemantic_control" and halt_seconds_advanced is not None:
                case["seconds_advanced_while_halt_bit_set"] = halt_seconds_advanced
            cases.append(case)
            events.append(
                runtime_event_envelope(
                    event_kind="hardware_event",
                    source_kind="pyboy_rtc_runtime",
                    source_report="debugger_deity_rtc_register_edge_runtime_replay",
                    seq=index,
                    proof_status="runtime_observed",
                    observation_type="explicit_hardware_event",
                    scope={
                        "backend": "pyboy",
                        "surface": (
                            "not_rtc"
                            if bad_event_scope
                            and case_id == "rtc_halt_bit_readback_nonsemantic_control"
                            else "rtc"
                        ),
                        "rtc_transition": spec["transition_kind"],
                    },
                    subjects={"write_range": case["write_range"]},
                    precision={
                        "transition_observed": True,
                        "halt_semantics_proven": claim_halt_semantics,
                        "observed_carry": spec.get("observed_carry", False),
                        "seeded_elapsed_days": spec.get("seeded_elapsed_days", 0),
                    },
                    validation={"case_id": case_id, "transition_kind": spec["transition_kind"]},
                    payload=case,
                )
            )
        valid = not omit_case
        path = out_dir / "rtc_register_edge_runtime_replay.json"
        path.write_text(
            json.dumps(
                {
                    "kind": "debugger_deity_surface_replay",
                    "schema_version": 1,
                    "surface": "rtc",
                    "valid": valid,
                    "known_limits": [
                        "Seeded day-overflow readback is PyBoy-only; halt semantics remain open; cross-backend parity remains open."
                    ],
                    "runtime_replay": {
                        "kind": "debugger_deity_rtc_register_edge_runtime_replay",
                        "schema_version": 1,
                        "valid": valid,
                        "backend": "pyboy",
                        "known_limits": [
                            "Seeded day-overflow cases are not naturally elapsed runtime; halt semantics remain unproven; cross-backend parity remains open."
                        ],
                        "cases": cases,
                        "runtime_events": events,
                    },
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_rtc_register_edge_runtime_replay_status_accepts_complete_runtime_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_rtc_register_edge_runtime_fixture(root)

            status = rtc_register_edge_runtime_replay_status(root=root)

        self.assertTrue(status["ready"])
        self.assertTrue(status["halt_negative_control_ready"])
        self.assertEqual(status["runtime_event_count"], 5)
        self.assertIn("rtc_seeded_day_512_carry_overflow_readback", status["validated_cases"])

    def test_rtc_register_edge_runtime_replay_status_fails_closed_on_missing_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_rtc_register_edge_runtime_fixture(
                root,
                omit_case="rtc_seeded_day_512_carry_overflow_readback",
            )

            status = rtc_register_edge_runtime_replay_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("missing RTC runtime case: rtc_seeded_day_512_carry_overflow_readback", status["errors"])

    def test_rtc_register_edge_runtime_replay_status_fails_closed_on_halt_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_rtc_register_edge_runtime_fixture(root, claim_halt_semantics=True)

            status = rtc_register_edge_runtime_replay_status(root=root)

        self.assertFalse(status["ready"])
        self.assertTrue(any("must not claim halt semantics proof" in error for error in status["errors"]))
        self.assertFalse(status["halt_negative_control_ready"])

    def test_rtc_register_edge_runtime_replay_status_fails_closed_on_missing_halt_negative_control_seconds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_rtc_register_edge_runtime_fixture(root, halt_seconds_advanced=None)

            status = rtc_register_edge_runtime_replay_status(root=root)

        self.assertFalse(status["ready"])
        self.assertFalse(status["halt_negative_control_ready"])
        self.assertTrue(
            any("must show PyBoy halt semantics are not proven" in error for error in status["errors"])
        )

    def test_rtc_register_edge_runtime_replay_status_fails_closed_on_false_halt_negative_control_seconds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_rtc_register_edge_runtime_fixture(root, halt_seconds_advanced=False)

            status = rtc_register_edge_runtime_replay_status(root=root)

        self.assertFalse(status["ready"])
        self.assertFalse(status["halt_negative_control_ready"])
        self.assertTrue(
            any("must show PyBoy halt semantics are not proven" in error for error in status["errors"])
        )

    def test_rtc_register_edge_runtime_replay_status_fails_closed_on_bad_event_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_rtc_register_edge_runtime_fixture(root, bad_event_scope=True)

            status = rtc_register_edge_runtime_replay_status(root=root)

        self.assertFalse(status["ready"])
        self.assertTrue(any("RTC event scope mismatch" in error for error in status["errors"]))
        self.assertFalse(status["halt_negative_control_ready"])

    def test_mbc_bank_transition_model_status_validates_write_ranges_and_state_updates(self) -> None:
        status = mbc_bank_transition_model_status()

        self.assertTrue(status["ready"])
        self.assertIn("mbc_ram_enable_write", status["validated_semantics"])
        self.assertIn("mbc_mode_or_latch_write", status["validated_semantics"])
        self.assertIn("sram_rtc_select=8", status["validated_transitions"])

    def _write_mbc_runtime_transition_fixture(
        self,
        root: Path,
        *,
        omit_case: str = "",
        unobserved_case: str = "",
        bad_event_scope: bool = False,
    ) -> Path:
        out_dir = root / "audit" / "debugger_literal_anything"
        out_dir.mkdir(parents=True)
        case_specs = {
            "mbc3_rom_bank_select_window": {
                "transition_kind": "rom_bank_select",
                "write_range": "$2000-$3FFF",
                "matched_bank_count": 6,
                "zero_select_maps_to_bank_one": True,
                "transitions": [{"sample_match": True} for _ in range(6)],
            },
            "mbc3_sram_enable_disable": {
                "transition_kind": "sram_enable_disable",
                "write_range": "$0000-$1FFF",
                "enabled_readback_matches": True,
                "disabled_readback_open_bus": True,
                "disabled_write_blocked": True,
                "reenabled_preserved": True,
            },
            "mbc3_sram_bank_select_isolation": {
                "transition_kind": "sram_bank_select",
                "write_range": "$4000-$5FFF",
                "isolated_bank_count": 4,
                "reads": [{"match": True} for _ in range(4)],
            },
            "mbc3_rtc_register_select_latch": {
                "transition_kind": "rtc_register_select_latch",
                "write_range": "$4000-$5FFF,$6000-$7FFF",
                "bounded_register_values": True,
                "latch_sequence_observed": True,
                "sram_marker_restored": True,
                "rtc_register_count": 5,
            },
        }
        cases = []
        events = []
        for index, (case_id, spec) in enumerate(case_specs.items()):
            if case_id == omit_case:
                continue
            transition_observed = case_id != unobserved_case
            case = {
                "case_id": case_id,
                "transition_observed": transition_observed,
                **spec,
            }
            cases.append(case)
            if not transition_observed:
                continue
            scope = {
                "backend": "pyboy",
                "surface": "not_mbc" if bad_event_scope and index == 0 else "mbc",
                "mbc_transition": spec["transition_kind"],
            }
            events.append(
                runtime_event_envelope(
                    event_kind="hardware_event",
                    source_kind="pyboy_mbc_runtime",
                    source_report="debugger_deity_mbc_runtime_transition_replay_corpus",
                    seq=index,
                    proof_status="runtime_observed",
                    observation_type="explicit_hardware_event",
                    scope=scope,
                    subjects={"write_range": spec["write_range"]},
                    precision={"transition_observed": transition_observed},
                    validation={"case_id": case_id, "transition_kind": spec["transition_kind"]},
                    payload=case,
                )
            )
        valid = not omit_case and not unobserved_case
        path = out_dir / "mbc_runtime_transition_replay_corpus.json"
        path.write_text(
            json.dumps(
                {
                    "kind": "debugger_deity_surface_replay",
                    "schema_version": 1,
                    "surface": "mbc",
                    "valid": valid,
                    "known_limits": [
                        "Does not claim RTC halt, carry, day-overflow, RTC register-write, or cross-backend correctness."
                    ],
                    "runtime_replay": {
                        "kind": "debugger_deity_mbc_runtime_transition_replay_corpus",
                        "schema_version": 1,
                        "valid": valid,
                        "backend": "pyboy",
                        "known_limits": [
                            "RTC halt, carry, day-overflow, and RTC register-write semantics remain open."
                        ],
                        "cases": cases,
                        "runtime_events": events,
                    },
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_mbc_runtime_transition_replay_corpus_status_accepts_complete_runtime_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_mbc_runtime_transition_fixture(root)

            status = mbc_runtime_transition_replay_corpus_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["runtime_event_count"], 4)
        self.assertEqual(
            set(status["validated_cases"]),
            {
                "mbc3_rom_bank_select_window",
                "mbc3_sram_enable_disable",
                "mbc3_sram_bank_select_isolation",
                "mbc3_rtc_register_select_latch",
            },
        )

    def test_mbc_runtime_transition_replay_corpus_status_fails_closed_on_missing_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_mbc_runtime_transition_fixture(root, omit_case="mbc3_sram_bank_select_isolation")

            status = mbc_runtime_transition_replay_corpus_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("missing MBC runtime case: mbc3_sram_bank_select_isolation", status["errors"])

    def test_mbc_runtime_transition_replay_corpus_status_fails_closed_on_unobserved_transition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_mbc_runtime_transition_fixture(root, unobserved_case="mbc3_sram_enable_disable")

            status = mbc_runtime_transition_replay_corpus_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("mbc3_sram_enable_disable did not prove an observed runtime transition", status["errors"])

    def test_mbc_runtime_transition_replay_corpus_status_fails_closed_on_bad_event_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_mbc_runtime_transition_fixture(root, bad_event_scope=True)

            status = mbc_runtime_transition_replay_corpus_status(root=root)

        self.assertFalse(status["ready"])
        self.assertTrue(any("MBC event scope mismatch" in error for error in status["errors"]))

    def test_save_rtc_mbc_static_evidence_replaces_broad_gaps_with_residual_runtime_gaps(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["save_rtc_mbc"]
        if report["rtc_edge_case_source_anchors"]["ready"]:
            self.assertNotIn(RTC_EDGE_CASE_REPLAY_GAP, row["missing_evidence"])
            self.assertNotIn(RTC_EDGE_CASE_REPLAY_GAP, report["missing_evidence"])
            if report["rtc_register_edge_runtime_replay"]["ready"]:
                self.assertNotIn(RTC_RUNTIME_REPLAY_GAP, row["missing_evidence"])
                self.assertNotIn(RTC_RUNTIME_REPLAY_GAP, report["missing_evidence"])
                self.assertNotIn(RTC_HALT_SEMANTICS_RUNTIME_GAP, row["missing_evidence"])
                self.assertNotIn(RTC_HALT_SEMANTICS_RUNTIME_GAP, report["missing_evidence"])
                if report["mbc_runtime_transition_replay_corpus"]["ready"]:
                    self.assertNotIn(RTC_REMAINING_HALT_FREEZE_SEMANTICS_RUNTIME_GAP, row["missing_evidence"])
                    self.assertNotIn(RTC_REMAINING_HALT_FREEZE_SEMANTICS_RUNTIME_GAP, report["missing_evidence"])
                else:
                    self.assertIn(RTC_REMAINING_HALT_FREEZE_SEMANTICS_RUNTIME_GAP, row["missing_evidence"])
                    self.assertIn(RTC_REMAINING_HALT_FREEZE_SEMANTICS_RUNTIME_GAP, report["missing_evidence"])
            else:
                self.assertIn(RTC_RUNTIME_REPLAY_GAP, row["missing_evidence"])
                self.assertIn(RTC_RUNTIME_REPLAY_GAP, report["missing_evidence"])
        if report["mbc_bank_transition_model"]["ready"]:
            self.assertNotIn(MBC_STATE_TRANSITION_GAP, row["missing_evidence"])
            self.assertNotIn(MBC_STATE_TRANSITION_GAP, report["missing_evidence"])
            if report["mbc_runtime_transition_replay_corpus"]["ready"]:
                self.assertNotIn(MBC_RUNTIME_TRANSITION_REPLAY_GAP, row["missing_evidence"])
                self.assertNotIn(MBC_RUNTIME_TRANSITION_REPLAY_GAP, report["missing_evidence"])
            else:
                self.assertIn(MBC_RUNTIME_TRANSITION_REPLAY_GAP, row["missing_evidence"])
                self.assertIn(MBC_RUNTIME_TRANSITION_REPLAY_GAP, report["missing_evidence"])

    def test_interrupt_entry_ime_model_status_validates_effect_model_and_runtime_gate(self) -> None:
        status = interrupt_entry_ime_model_status()

        self.assertTrue(status["ready"])
        self.assertIn("0040:vblank", status["validated_vectors"])
        self.assertIn("0058:serial", status["validated_vectors"])
        self.assertIn("D9:reti", status["validated_cpu_state_ops"])
        self.assertIn("interrupt_entry", status["modeled_effect_kinds"])
        self.assertEqual(status["proof_gate"], "explicit_runtime_event_missing")

    def _write_interrupt_runtime_event_fixture(
        self,
        root: Path,
        *,
        omit_case: str = "",
        missing_exit_case: str = "",
        bad_event_scope: bool = False,
    ) -> Path:
        out_dir = root / "audit" / "debugger_literal_anything"
        out_dir.mkdir(parents=True)
        case_specs = {
            "vblank_interrupt_entry_exit": ("vblank", "$0040", "$016F", 0x01),
            "lcd_stat_interrupt_entry_exit": ("lcd_stat", "$0048", "$0417", 0x02),
            "timer_interrupt_entry_exit": ("timer", "$0050", "$0050", 0x04),
            "serial_interrupt_entry_exit": ("serial", "$0058", "$06F3", 0x08),
            "joypad_interrupt_entry_exit": ("joypad", "$0060", "$08C3", 0x10),
        }
        cases = []
        events = []
        for index, (case_id, (interrupt_name, vector, exit_pc, ie_bit)) in enumerate(case_specs.items()):
            if case_id == omit_case:
                continue
            exit_count = 0 if case_id == missing_exit_case else 2
            observed = exit_count > 0
            case = {
                "case_id": case_id,
                "interrupt_name": interrupt_name,
                "transition_kind": "interrupt_entry_exit",
                "vector": vector,
                "exit_pc": exit_pc,
                "ie_bit": ie_bit,
                "entry_count": 2,
                "exit_count": exit_count,
                "paired_entry_exit_count": min(2, exit_count),
                "return_address_consistent": observed,
                "entry_samples": [{"stack_top_return_address": 0x0331, "pc": int(vector[1:], 16)}],
                "exit_samples": [{"stack_top_return_address": 0x0331, "pc": int(exit_pc[1:], 16)}] if observed else [],
                "transition_observed": observed,
            }
            cases.append(case)
            if not observed:
                continue
            scope = {
                "backend": "pyboy",
                "surface": "not_interrupts" if bad_event_scope and index == 0 else "interrupts",
                "interrupt_name": interrupt_name,
            }
            events.append(
                runtime_event_envelope(
                    event_kind="hardware_event",
                    source_kind="pyboy_interrupt_runtime",
                    source_report="debugger_deity_interrupt_entry_exit_runtime_event_stream",
                    seq=index,
                    proof_status="runtime_observed",
                    observation_type="explicit_hardware_event",
                    scope=scope,
                    subjects={"vector": vector, "exit_pc": exit_pc},
                    precision={
                        "transition_observed": observed,
                        "paired_entry_exit_count": min(2, exit_count),
                    },
                    validation={"case_id": case_id, "transition_kind": "interrupt_entry_exit"},
                    payload=case,
                )
            )
        valid = not omit_case and not missing_exit_case
        path = out_dir / "interrupt_entry_exit_runtime_event_stream.json"
        path.write_text(
            json.dumps(
                {
                    "kind": "debugger_deity_surface_replay",
                    "schema_version": 1,
                    "surface": "interrupts",
                    "valid": valid,
                    "known_limits": [
                        "Serial transfer, cycle-exact IME timing, and timer/LCD mode event streams remain open."
                    ],
                    "runtime_replay": {
                        "kind": "debugger_deity_interrupt_entry_exit_runtime_event_stream",
                        "schema_version": 1,
                        "valid": valid,
                        "backend": "pyboy",
                        "known_limits": [
                            "Serial transfer, cycle-exact IME timing, and timer/LCD mode event streams remain open."
                        ],
                        "cases": cases,
                        "runtime_events": events,
                    },
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_interrupt_entry_exit_runtime_event_stream_status_accepts_complete_runtime_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_interrupt_runtime_event_fixture(root)

            status = interrupt_entry_exit_runtime_event_stream_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["runtime_event_count"], 5)
        self.assertEqual(
            set(status["validated_cases"]),
            {
                "vblank_interrupt_entry_exit",
                "lcd_stat_interrupt_entry_exit",
                "timer_interrupt_entry_exit",
                "serial_interrupt_entry_exit",
                "joypad_interrupt_entry_exit",
            },
        )

    def test_interrupt_entry_exit_runtime_event_stream_status_fails_closed_on_missing_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_interrupt_runtime_event_fixture(root, omit_case="lcd_stat_interrupt_entry_exit")

            status = interrupt_entry_exit_runtime_event_stream_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("missing interrupt runtime case: lcd_stat_interrupt_entry_exit", status["errors"])

    def test_interrupt_entry_exit_runtime_event_stream_status_fails_closed_on_missing_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_interrupt_runtime_event_fixture(root, missing_exit_case="vblank_interrupt_entry_exit")

            status = interrupt_entry_exit_runtime_event_stream_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("vblank_interrupt_entry_exit missing runtime exit observations", status["errors"])

    def test_interrupt_entry_exit_runtime_event_stream_status_fails_closed_on_bad_event_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_interrupt_runtime_event_fixture(root, bad_event_scope=True)

            status = interrupt_entry_exit_runtime_event_stream_status(root=root)

        self.assertFalse(status["ready"])
        self.assertTrue(any("interrupt event scope mismatch" in error for error in status["errors"]))

    def test_dma_oam_vram_transfer_model_status_validates_transfer_expansion(self) -> None:
        status = dma_oam_vram_transfer_model_status()

        self.assertTrue(status["ready"])
        self.assertIn("oam_dma_trigger", status["validated_semantics"])
        self.assertIn("vram_dma_len_mode_write", status["validated_semantics"])
        self.assertEqual(status["oam_dma_read_count"], 0xA0)
        self.assertEqual(status["oam_dma_write_count"], 0xA0)
        self.assertEqual(status["vram_dma_read_count"], 0x10)
        self.assertEqual(status["vram_dma_write_count"], 0x10)
        self.assertEqual(status["proof_gate"], "explicit_runtime_event_missing")

    def _write_dma_runtime_event_fixture(
        self,
        root: Path,
        *,
        omit_case: str = "",
        bad_match_count: bool = False,
    ) -> Path:
        out_dir = root / "audit" / "debugger_literal_anything"
        out_dir.mkdir(parents=True)
        case_specs = {
            "oam_dma_hram_trigger": ("oam_dma", 0xA0, "FF46"),
            "cgb_vram_dma_general_16_bytes": ("cgb_vram_dma_general", 0x10, "FF55"),
        }
        cases = []
        events = []
        for index, (case_id, (dma_kind, byte_count, trigger_register)) in enumerate(case_specs.items()):
            if case_id == omit_case:
                continue
            match_count = byte_count - 1 if bad_match_count and index == 0 else byte_count
            case = {
                "case_id": case_id,
                "dma_kind": dma_kind,
                "trigger_register": trigger_register,
                "trigger_value": 0,
                "source_range": "$C000-$C09F",
                "destination_range": "$FE00-$FE9F",
                "byte_count": byte_count,
                "match_count": match_count,
                "exact_match": match_count == byte_count,
            }
            cases.append(case)
            events.append(
                runtime_event_envelope(
                    event_kind="hardware_event",
                    source_kind="pyboy_dma_runtime",
                    source_report="debugger_deity_dma_oam_vram_runtime_event_stream",
                    seq=index,
                    proof_status="runtime_observed",
                    observation_type="explicit_hardware_event",
                    scope={"backend": "pyboy", "surface": "dma", "dma_kind": dma_kind},
                    subjects={"registers": [trigger_register]},
                    precision={
                        "byte_count": byte_count,
                        "match_count": match_count,
                        "byte_exact_copy": match_count == byte_count,
                    },
                    validation={"case_id": case_id, "trigger_value": 0},
                    payload=case,
                )
            )
        path = out_dir / "dma_oam_vram_runtime_event_stream.json"
        path.write_text(
            json.dumps(
                {
                    "kind": "debugger_deity_surface_replay",
                    "schema_version": 1,
                    "surface": "dma",
                    "valid": not bad_match_count and not omit_case,
                    "runtime_replay": {
                        "kind": "debugger_deity_dma_oam_vram_runtime_event_stream",
                        "schema_version": 1,
                        "valid": not bad_match_count and not omit_case,
                        "backend": "pyboy",
                        "cases": cases,
                        "runtime_events": events,
                    },
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_dma_oam_vram_runtime_event_stream_status_accepts_complete_runtime_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_dma_runtime_event_fixture(root)

            status = dma_oam_vram_runtime_event_stream_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["runtime_event_count"], 2)
        self.assertEqual(
            set(status["validated_cases"]),
            {"oam_dma_hram_trigger", "cgb_vram_dma_general_16_bytes"},
        )

    def test_dma_oam_vram_runtime_event_stream_status_fails_closed_on_missing_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_dma_runtime_event_fixture(root, omit_case="cgb_vram_dma_general_16_bytes")

            status = dma_oam_vram_runtime_event_stream_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("missing DMA runtime case: cgb_vram_dma_general_16_bytes", status["errors"])

    def test_dma_oam_vram_runtime_event_stream_status_fails_closed_on_bad_byte_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_dma_runtime_event_fixture(root, bad_match_count=True)

            status = dma_oam_vram_runtime_event_stream_status(root=root)

        self.assertFalse(status["ready"])
        self.assertTrue(any("match_count mismatch" in error for error in status["errors"]))

    def test_timer_ppu_io_overflow_model_status_validates_timer_ppu_io_and_runtime_gate(self) -> None:
        status = timer_ppu_io_overflow_model_status()

        self.assertTrue(status["ready"])
        self.assertIn("timer_register_write", status["validated_semantics"])
        self.assertIn("timer_div_reset", status["validated_semantics"])
        self.assertIn("ppu_register_write", status["validated_semantics"])
        self.assertIn("timer_tima_overflow", status["validated_timer_effects"])
        self.assertEqual(status["proof_gate"], "explicit_runtime_event_missing")

    def _write_timer_lcd_runtime_event_fixture(
        self,
        root: Path,
        *,
        omit_case: str = "",
        missing_lcd_mode: bool = False,
        bad_event_scope: bool = False,
    ) -> Path:
        out_dir = root / "audit" / "debugger_literal_anything"
        out_dir.mkdir(parents=True)
        case_specs = {
            "timer_tima_overflow_interrupt_request": {
                "event_family": "timer",
                "transition_kind": "timer_tima_overflow_if_request",
                "registers": ["FF05", "FF06", "FF07", "FF0F", "FFFF"],
                "sample_count": 128,
                "if_timer_bit": 0x04,
                "overflow_drop_observed": True,
                "interrupt_request_observed": True,
                "overflow_drop_samples": [{"before_tima": 253, "after_tima": 166, "after_if": 4}],
                "runtime_event_observed": True,
            },
            "lcd_stat_mode_poll_sequence": {
                "event_family": "lcd",
                "transition_kind": "lcd_stat_mode_ly_sequence",
                "registers": ["FF40", "FF41", "FF44"],
                "sample_count": 1280,
                "observed_modes": [0, 2, 3] if missing_lcd_mode else [0, 1, 2, 3],
                "ly_min": 0,
                "ly_max": 153,
                "vblank_entry": {} if missing_lcd_mode else {"sample_index": 1171, "mode": 1, "ly": 144},
                "transition_count": 503,
                "mode_sequence_observed": not missing_lcd_mode,
                "vblank_observed": not missing_lcd_mode,
                "runtime_event_observed": not missing_lcd_mode,
            },
        }
        cases = []
        events = []
        for index, (case_id, case) in enumerate(case_specs.items()):
            if case_id == omit_case:
                continue
            payload = {"case_id": case_id, **case}
            cases.append(payload)
            if not payload["runtime_event_observed"]:
                continue
            scope = {
                "backend": "pyboy",
                "surface": "not_timer_lcd" if bad_event_scope and index == 0 else "timer_lcd",
                "event_family": payload["event_family"],
            }
            if payload["event_family"] == "timer":
                precision = {
                    "sample_count": payload["sample_count"],
                    "overflow_drop_observed": payload["overflow_drop_observed"],
                    "interrupt_request_observed": payload["interrupt_request_observed"],
                    "overflow_drop_count": 1,
                }
            else:
                precision = {
                    "sample_count": payload["sample_count"],
                    "observed_modes": payload["observed_modes"],
                    "mode_sequence_observed": payload["mode_sequence_observed"],
                    "vblank_observed": payload["vblank_observed"],
                    "transition_count": payload["transition_count"],
                }
            events.append(
                runtime_event_envelope(
                    event_kind="hardware_event",
                    source_kind="pyboy_timer_lcd_runtime",
                    source_report="debugger_deity_timer_lcd_mode_runtime_event_stream",
                    seq=index,
                    proof_status="runtime_observed",
                    observation_type="explicit_hardware_event",
                    scope=scope,
                    subjects={"registers": payload["registers"]},
                    precision=precision,
                    validation={"case_id": case_id, "transition_kind": payload["transition_kind"]},
                    payload=payload,
                )
            )
        valid = not omit_case and not missing_lcd_mode and not bad_event_scope
        path = out_dir / "timer_lcd_mode_runtime_event_stream.json"
        path.write_text(
            json.dumps(
                {
                    "kind": "debugger_deity_surface_replay",
                    "schema_version": 1,
                    "surface": "timer_lcd",
                    "valid": valid,
                    "known_limits": [
                        "This is not cycle-exact hardware parity and leaves cross-backend correctness open."
                    ],
                    "runtime_replay": {
                        "kind": "debugger_deity_timer_lcd_mode_runtime_event_stream",
                        "schema_version": 1,
                        "valid": valid,
                        "backend": "pyboy",
                        "known_limits": [
                            "Timer/LCD polling is not cycle-exact and cross-backend parity remains out of scope."
                        ],
                        "cases": cases,
                        "runtime_events": events,
                    },
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_timer_lcd_runtime_event_stream_status_accepts_complete_runtime_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_timer_lcd_runtime_event_fixture(root)

            status = timer_lcd_mode_runtime_event_stream_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["runtime_event_count"], 2)
        self.assertEqual(
            set(status["validated_cases"]),
            {"timer_tima_overflow_interrupt_request", "lcd_stat_mode_poll_sequence"},
        )

    def test_timer_lcd_runtime_event_stream_status_fails_closed_on_missing_lcd_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_timer_lcd_runtime_event_fixture(root, missing_lcd_mode=True)

            status = timer_lcd_mode_runtime_event_stream_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("LCD runtime case did not observe STAT modes 0,1,2,3", status["errors"])

    def test_timer_lcd_runtime_event_stream_status_fails_closed_on_bad_event_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_timer_lcd_runtime_event_fixture(root, bad_event_scope=True)

            status = timer_lcd_mode_runtime_event_stream_status(root=root)

        self.assertFalse(status["ready"])
        self.assertTrue(any("timer/LCD event scope mismatch" in error for error in status["errors"]))

    def test_hardware_model_splits_replace_broad_gaps_with_runtime_stream_gaps(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["interrupts_dma_timers_lcd"]

        if report["interrupt_entry_ime_model"]["ready"]:
            self.assertIn(HARDWARE_INTERRUPT_MODEL_EVIDENCE_ID, report["closed_evidence_ids"])
            self.assertNotIn(INTERRUPT_ENTRY_EXIT_EVENTS_GAP, report["missing_evidence"])
            if report["interrupt_entry_exit_runtime_events"]["ready"]:
                self.assertIn(HARDWARE_INTERRUPT_RUNTIME_EVENT_EVIDENCE_ID, report["closed_evidence_ids"])
                self.assertNotIn(INTERRUPT_ENTRY_EXIT_RUNTIME_EVENT_STREAM_GAP, row["missing_evidence"])
            else:
                self.assertIn(INTERRUPT_ENTRY_EXIT_RUNTIME_EVENT_STREAM_GAP, row["missing_evidence"])
        if report["dma_oam_vram_transfer_models"]["ready"]:
            self.assertIn(HARDWARE_DMA_MODEL_EVIDENCE_ID, report["closed_evidence_ids"])
            self.assertNotIn(DMA_OAM_VRAM_EVENTS_GAP, report["missing_evidence"])
            if report["dma_oam_vram_runtime_events"]["ready"]:
                self.assertIn(HARDWARE_DMA_RUNTIME_EVENT_EVIDENCE_ID, report["closed_evidence_ids"])
                self.assertNotIn(DMA_OAM_VRAM_RUNTIME_EVENT_STREAM_GAP, row["missing_evidence"])
            else:
                self.assertIn(DMA_OAM_VRAM_RUNTIME_EVENT_STREAM_GAP, row["missing_evidence"])
        if report["timer_ppu_io_overflow_models"]["ready"]:
            self.assertIn(HARDWARE_TIMER_LCD_MODEL_EVIDENCE_ID, report["closed_evidence_ids"])
            self.assertNotIn(TIMER_LCD_MODE_EVENTS_GAP, report["missing_evidence"])
            if report["timer_lcd_mode_runtime_events"]["ready"]:
                self.assertIn(HARDWARE_TIMER_LCD_RUNTIME_EVENT_EVIDENCE_ID, report["closed_evidence_ids"])
                self.assertNotIn(TIMER_LCD_MODE_RUNTIME_EVENT_STREAM_GAP, row["missing_evidence"])
            else:
                self.assertIn(TIMER_LCD_MODE_RUNTIME_EVENT_STREAM_GAP, row["missing_evidence"])

    def test_serial_register_write_model_status_validates_serial_io_and_interrupt_vector(self) -> None:
        status = serial_register_write_model_status()

        self.assertTrue(status["ready"])
        self.assertEqual(status["validated_interrupt_vector"], "0058:serial")
        self.assertIn("FF01:serial_register_write", status["validated_semantics"])
        self.assertIn("FF02:serial_register_write", status["validated_semantics"])
        self.assertIn("serial_register_write", status["modeled_effect_kinds"])

    def _write_serial_transfer_runtime_event_fixture(
        self,
        root: Path,
        *,
        omit_case: str = "",
        missing_interrupt: bool = False,
        bad_event_scope: bool = False,
        bad_serial_output: bool = False,
        bad_disconnected_fill: bool = False,
        extra_case: bool = False,
    ) -> Path:
        out_dir = root / "audit" / "debugger_literal_anything"
        out_dir.mkdir(parents=True)
        case_specs = {
            "serial_internal_clock_transfer_byte_42": 0x42,
            "serial_internal_clock_transfer_byte_5a": 0x5A,
        }
        if extra_case:
            case_specs["serial_internal_clock_transfer_byte_99"] = 0x99
        cases = []
        events = []
        for index, (case_id, outgoing_byte) in enumerate(case_specs.items()):
            if case_id == omit_case:
                continue
            observed = not missing_interrupt
            case = {
                "case_id": case_id,
                "event_family": "serial",
                "transition_kind": "serial_internal_clock_transfer",
                "registers": ["FF01", "FF02", "FF0F", "FFFF"],
                "sample_count": 128,
                "outgoing_byte": outgoing_byte,
                "outgoing_char": chr(outgoing_byte),
                "serial_output": "?" if bad_serial_output and index == 0 else chr(outgoing_byte),
                "sc_values": [0x80, 0x81],
                "sb_values": [0x00] if bad_disconnected_fill and index == 0 else [0xFF],
                "first_interrupt_request_sample": 13 if observed else None,
                "if_serial_bit": 0x08,
                "start_observed": True,
                "post_start_observed": True,
                "interrupt_request_observed": observed,
                "serial_output_observed": True,
                "receive_fill_observed": True,
                "runtime_event_observed": observed,
            }
            cases.append(case)
            if not observed:
                continue
            scope = {
                "backend": "pyboy",
                "surface": "not_serial" if bad_event_scope and index == 0 else "serial",
                "event_family": "serial_transfer",
            }
            events.append(
                runtime_event_envelope(
                    event_kind="hardware_event",
                    source_kind="pyboy_serial_runtime",
                    source_report="debugger_deity_serial_transfer_runtime_event_stream",
                    seq=index,
                    proof_status="runtime_observed",
                    observation_type="explicit_hardware_event",
                    scope=scope,
                    subjects={"registers": case["registers"]},
                    precision={
                        "sample_count": case["sample_count"],
                        "outgoing_byte": outgoing_byte,
                        "start_observed": True,
                        "post_start_observed": True,
                        "interrupt_request_observed": True,
                        "serial_output_observed": True,
                        "receive_fill_observed": True,
                    },
                    validation={"case_id": case_id, "transition_kind": case["transition_kind"]},
                    payload=case,
                )
            )
        valid = not omit_case and not missing_interrupt and not bad_event_scope
        path = out_dir / "serial_transfer_runtime_event_stream.json"
        path.write_text(
            json.dumps(
                {
                    "kind": "debugger_deity_surface_replay",
                    "schema_version": 1,
                    "surface": "serial",
                    "valid": valid,
                    "known_limits": [
                        "This has no linked peer, no Mystery Gift protocol completion, and no cross-backend serial parity."
                    ],
                    "runtime_replay": {
                        "kind": "debugger_deity_serial_transfer_runtime_event_stream",
                        "schema_version": 1,
                        "valid": valid,
                        "backend": "pyboy",
                        "known_limits": [
                            "Disconnected-peer behavior is PyBoy evidence only; linked peer and cross-backend parity remain open."
                        ],
                        "cases": cases,
                        "runtime_events": events,
                    },
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_serial_transfer_runtime_event_stream_status_accepts_complete_runtime_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_serial_transfer_runtime_event_fixture(root)

            status = serial_transfer_runtime_event_stream_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["runtime_event_count"], 2)
        self.assertEqual(
            set(status["validated_cases"]),
            {"serial_internal_clock_transfer_byte_42", "serial_internal_clock_transfer_byte_5a"},
        )

    def test_serial_transfer_runtime_event_stream_status_fails_closed_on_missing_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_serial_transfer_runtime_event_fixture(root, omit_case="serial_internal_clock_transfer_byte_5a")

            status = serial_transfer_runtime_event_stream_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("missing serial runtime case: serial_internal_clock_transfer_byte_5a", status["errors"])

    def test_serial_transfer_runtime_event_stream_status_fails_closed_without_interrupt_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_serial_transfer_runtime_event_fixture(root, missing_interrupt=True)

            status = serial_transfer_runtime_event_stream_status(root=root)

        self.assertFalse(status["ready"])
        self.assertTrue(any("missing serial IF request observation" in error for error in status["errors"]))

    def test_serial_transfer_runtime_event_stream_status_fails_closed_on_bad_event_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_serial_transfer_runtime_event_fixture(root, bad_event_scope=True)

            status = serial_transfer_runtime_event_stream_status(root=root)

        self.assertFalse(status["ready"])
        self.assertTrue(any("serial event scope mismatch" in error for error in status["errors"]))

    def test_serial_transfer_runtime_event_stream_status_fails_closed_on_extra_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_serial_transfer_runtime_event_fixture(root, extra_case=True)

            status = serial_transfer_runtime_event_stream_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("unexpected serial runtime cases: ['serial_internal_clock_transfer_byte_99']", status["errors"])

    def test_serial_transfer_runtime_event_stream_status_fails_closed_on_bad_serial_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_serial_transfer_runtime_event_fixture(root, bad_serial_output=True)

            status = serial_transfer_runtime_event_stream_status(root=root)

        self.assertFalse(status["ready"])
        self.assertTrue(any("serial output missing outgoing byte" in error for error in status["errors"]))

    def test_serial_transfer_runtime_event_stream_status_fails_closed_on_bad_disconnected_fill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_serial_transfer_runtime_event_fixture(root, bad_disconnected_fill=True)

            status = serial_transfer_runtime_event_stream_status(root=root)

        self.assertFalse(status["ready"])
        self.assertTrue(any("SB values did not match disconnected-peer fill" in error for error in status["errors"]))

    def _write_link_boundary_source_anchor_fixture(
        self,
        root: Path,
        *,
        missing_label: str = "",
    ) -> None:
        (root / "audit" / "debugger_literal_anything").mkdir(parents=True)
        rows = []
        for relative_path, labels in LINK_BOUNDARY_SOURCE_ANCHOR_LABELS.items():
            path = root / relative_path
            path.parent.mkdir(parents=True)
            present_labels = [label for label in labels if label != missing_label]
            path.write_text("\n".join(f"{label}::" for label in present_labels) + "\n", encoding="utf-8")
            rows.extend(
                {
                    "kind": "rom_surface_index_row",
                    "surface_id": f"symbol:00:4000:{label}",
                    "nearest_label": label,
                }
                for label in present_labels
            )
        (root / "audit" / "debugger_literal_anything" / "rom_surface_index.jsonl").write_text(
            "\n".join(json.dumps(row) for row in rows) + "\n",
            encoding="utf-8",
        )

    def test_link_boundary_source_anchor_status_accepts_source_and_index_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_link_boundary_source_anchor_fixture(root)

            status = link_boundary_source_anchor_status(root=root)

        expected_count = sum(len(labels) for labels in LINK_BOUNDARY_SOURCE_ANCHOR_LABELS.values())
        self.assertTrue(status["ready"])
        self.assertEqual(status["source_anchor_count"], expected_count)
        self.assertEqual(status["indexed_label_count"], expected_count)

    def test_link_boundary_source_anchor_status_fails_closed_without_source_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_link_boundary_source_anchor_fixture(root, missing_label="WaitForLinkedFriend")

            status = link_boundary_source_anchor_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("WaitForLinkedFriend", status["missing_source_labels"])

    def test_link_boundary_runtime_state_class_corpus_status_accepts_fail_closed_canonical_classes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_link_boundary_source_anchor_fixture(root)

            status = link_boundary_runtime_state_class_corpus_status(root=root)

        expected_count = sum(len(labels) for labels in LINK_BOUNDARY_SOURCE_ANCHOR_LABELS.values())
        self.assertTrue(status["ready"])
        self.assertEqual(status["class_count"], expected_count)
        self.assertEqual(len(set(status["class_ids"])), expected_count)
        self.assertTrue(all(class_id.startswith("csc_") for class_id in status["class_ids"]))
        self.assertTrue(
            all(
                "serial_transfer_runtime_event_stream" in item["missing_evidence"]
                and "link_backend_missing" in item["missing_evidence"]
                for item in status["classes"]
            )
        )

    def test_link_boundary_runtime_state_class_corpus_status_fails_without_source_anchors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_link_boundary_source_anchor_fixture(root, missing_label="WaitForLinkedFriend")

            status = link_boundary_runtime_state_class_corpus_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("link source anchors are not ready", status["errors"])

    def test_serial_link_static_evidence_replaces_broad_gaps_with_runtime_residuals(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["link_serial_mystery_gift"]

        if report["serial_register_write_model"]["ready"]:
            self.assertIn(SERIAL_REGISTER_WRITE_MODEL_EVIDENCE_ID, report["closed_evidence_ids"])
            self.assertNotIn(SERIAL_EVENT_STREAM_GAP, report["missing_evidence"])
            if report["serial_transfer_runtime_events"]["ready"]:
                self.assertIn(SERIAL_TRANSFER_RUNTIME_EVENT_EVIDENCE_ID, report["closed_evidence_ids"])
                self.assertNotIn(SERIAL_TRANSFER_RUNTIME_EVENT_STREAM_GAP, row["missing_evidence"])
            else:
                self.assertIn(SERIAL_TRANSFER_RUNTIME_EVENT_STREAM_GAP, row["missing_evidence"])
        if report["link_boundary_source_anchors"]["ready"]:
            self.assertIn(LINK_BOUNDARY_SOURCE_ANCHOR_EVIDENCE_ID, report["closed_evidence_ids"])
            self.assertNotIn(LINK_BOUNDARY_STATE_CLASSES_GAP, report["missing_evidence"])
            if report["link_boundary_runtime_state_class_corpus"]["ready"]:
                self.assertIn(
                    LINK_BOUNDARY_RUNTIME_STATE_CLASS_CORPUS_EVIDENCE_ID,
                    report["closed_evidence_ids"],
                )
                self.assertNotIn(LINK_BOUNDARY_RUNTIME_STATE_CLASS_CORPUS_GAP, row["missing_evidence"])
            else:
                self.assertIn(LINK_BOUNDARY_RUNTIME_STATE_CLASS_CORPUS_GAP, row["missing_evidence"])

    def _write_minimal_save_layout(self, root: Path) -> None:
        (root / "constants").mkdir(parents=True)
        (root / "ram").mkdir(parents=True)
        (root / "constants" / "misc_constants.asm").write_text(
            "DEF SAVE_FORMAT_VERSION EQU 3\n",
            encoding="utf-8",
        )
        (root / "ram" / "wram.asm").write_text(
            "\n".join(
                [
                    "wOptions::",
                    "wOptionsValue::",
                    "wOptionsEnd::",
                    "wPlayerData1::",
                    "wPlayerData1Value::",
                    "wPlayerData1End::",
                    "wPlayerData2::",
                    "wPlayerData2Value::",
                    "wPlayerData2End::",
                    "wPlayerData3::",
                    "wBossAITier::",
                    "wBossAIStateEnd::",
                    "    ds 140 - (wBossAIStateEnd - wBossAITier)",
                    "wPlayerData3Value::",
                    "wPlayerData3End::",
                    "wCurMapData::",
                    "wCurMapDataValue::",
                    "wCurMapDataEnd::",
                    "wPokemonData::",
                    "wPokemonDataValue::",
                    "wPokemonDataEnd::",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (root / "ram" / "sram.asm").write_text(
            "\n".join(
                [
                    'SECTION "Save", SRAM',
                    "sSave::",
                    'SECTION "Backup Save 1", SRAM',
                    "sBackupSave1::",
                    'SECTION "Backup Save 2", SRAM',
                    "sBackupSave2::",
                    'SECTION "Backup Save 3", SRAM',
                    "sBackupSave3::",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (root / "layout.link").write_text(
            "\n".join(
                [
                    "SRAM $0000",
                    '    "Save"',
                    '    "Backup Save 1"',
                    "SRAM $0001",
                    '    "Backup Save 2"',
                    '    "Backup Save 3"',
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def _record_current_save_fingerprint(self, root: Path) -> None:
        digest, _payload = compute_fingerprint(root=root)
        data_file = root / "tools" / "audit" / "data" / "save_format_fingerprints.json"
        data_file.parent.mkdir(parents=True)
        data_file.write_text(json.dumps({"3": digest}), encoding="utf-8")

    def test_save_format_sram_bank_ownership_status_accepts_matching_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_minimal_save_layout(root)
            self._record_current_save_fingerprint(root)

            status = save_format_sram_bank_ownership_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["owned_section_count"], 4)
        self.assertEqual(status["sram_section_bank_map"]["Save"], "SRAM $0000")
        self.assertEqual(status["sram_section_bank_map"]["Backup Save 3"], "SRAM $0001")

    def test_save_format_sram_bank_ownership_status_fails_closed_on_fingerprint_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_minimal_save_layout(root)
            data_file = root / "tools" / "audit" / "data" / "save_format_fingerprints.json"
            data_file.parent.mkdir(parents=True)
            data_file.write_text(json.dumps({"3": "stale"}), encoding="utf-8")

            status = save_format_sram_bank_ownership_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("save layout fingerprint does not match recorded SAVE_FORMAT_VERSION", status["errors"])

    def test_save_format_sram_bank_ownership_status_fails_closed_without_section_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_minimal_save_layout(root)
            self._record_current_save_fingerprint(root)
            (root / "layout.link").write_text(
                "\n".join(
                    [
                        "SRAM $0000",
                        '    "Save"',
                        '    "Backup Save 1"',
                        '    "Backup Save 2"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            status = save_format_sram_bank_ownership_status(root=root)

        self.assertFalse(status["ready"])
        self.assertTrue(
            any("missing SRAM layout ownership entries" in error for error in status["errors"])
        )

    def test_after_hit_item_order_golden_closes_only_order_gap(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["damage_debugger"]
        if report["after_hit_item_order"]["ready"]:
            self.assertNotIn("after_hit_item_order_rom_goldens", row["missing_evidence"])
            if report["damage_mutation_campaign"]["ready"]:
                for gap in report["damage_mutation_campaign"]["remaining_residual_gaps"]:
                    self.assertIn(gap, row["missing_evidence"])
                self.assertNotIn(DAMAGE_REMAINING_EXPANDED_MUTATION_CAMPAIGNS_GAP, row["missing_evidence"])
            else:
                self.assertIn(DAMAGE_EXPANDED_MUTATION_CAMPAIGNS_GAP, row["missing_evidence"])
            self.assertIn(AFTER_HIT_ORDER_EVIDENCE_ID, report["closed_evidence_ids"])
        else:
            self.assertIn("after_hit_item_order_rom_goldens", row["missing_evidence"])

    def test_damage_fuzz_no_divergence_adds_closed_evidence_without_closing_mutation_gap(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["damage_debugger"]
        if report["damage_mutation_campaign"]["ready"]:
            for gap in report["damage_mutation_campaign"]["remaining_residual_gaps"]:
                self.assertIn(gap, row["missing_evidence"])
            self.assertNotIn(DAMAGE_REMAINING_EXPANDED_MUTATION_CAMPAIGNS_GAP, row["missing_evidence"])
        else:
            self.assertIn(DAMAGE_EXPANDED_MUTATION_CAMPAIGNS_GAP, row["missing_evidence"])
        if report["damage_fuzz_no_divergence"]["ready"]:
            self.assertIn(DAMAGE_FUZZ_NO_DIVERGENCE_EVIDENCE_ID, report["closed_evidence_ids"])
        else:
            self.assertNotIn(DAMAGE_FUZZ_NO_DIVERGENCE_EVIDENCE_ID, report["closed_evidence_ids"])

    def test_damage_modifier_recoil_smoke_adds_closed_evidence_without_closing_mutation_gap(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["damage_debugger"]
        if report["damage_mutation_campaign"]["ready"]:
            for gap in report["damage_mutation_campaign"]["remaining_residual_gaps"]:
                self.assertIn(gap, row["missing_evidence"])
            self.assertNotIn(DAMAGE_REMAINING_EXPANDED_MUTATION_CAMPAIGNS_GAP, row["missing_evidence"])
        else:
            self.assertIn(DAMAGE_EXPANDED_MUTATION_CAMPAIGNS_GAP, row["missing_evidence"])
        if report["damage_modifier_recoil_smoke"]["ready"]:
            self.assertIn(DAMAGE_MODIFIER_RECOIL_EVIDENCE_ID, report["closed_evidence_ids"])
        else:
            self.assertNotIn(DAMAGE_MODIFIER_RECOIL_EVIDENCE_ID, report["closed_evidence_ids"])

    def _write_damage_modifier_recoil_smoke_log(
        self,
        root: Path,
        cases: tuple[str, ...] = DAMAGE_MODIFIER_RECOIL_SCENARIOS,
    ) -> Path:
        out_dir = root / "audit" / "damage_debugger"
        out_dir.mkdir(parents=True)
        path = out_dir / "clobber_smoke.log"
        path.write_text(
            "scenario                                 damage   expected  result  notes\n"
            + "\n".join([f"{case:<42s}      16      16-16   PASS  proof row" for case in cases])
            + "\nPASS: all 28 scenarios within expected damage ranges.\n",
            encoding="utf-8",
        )
        return path

    def test_damage_modifier_recoil_smoke_status_accepts_required_pass_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_damage_modifier_recoil_smoke_log(root)

            status = damage_modifier_recoil_smoke_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["case_count"], len(DAMAGE_MODIFIER_RECOIL_SCENARIOS))

    def test_damage_modifier_recoil_smoke_status_fails_closed_without_named_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_damage_modifier_recoil_smoke_log(root, cases=DAMAGE_MODIFIER_RECOIL_SCENARIOS[:-1])

            status = damage_modifier_recoil_smoke_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn(DAMAGE_MODIFIER_RECOIL_SCENARIOS[-1], status["missing_cases"])

    def test_damage_modifier_recoil_smoke_status_fails_closed_without_all_28_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_path = self._write_damage_modifier_recoil_smoke_log(root)
            log_path.write_text(
                "\n".join([f"{case:<42s}      16      16-16   PASS  proof row" for case in DAMAGE_MODIFIER_RECOIL_SCENARIOS])
                + "\nPASS: all 8 scenarios within expected damage ranges.\n",
                encoding="utf-8",
            )

            status = damage_modifier_recoil_smoke_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("clobber_smoke summary is not the expected all-28 PASS", status["errors"])

    def test_damage_modifier_recoil_smoke_status_fails_closed_when_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_path = self._write_damage_modifier_recoil_smoke_log(root)
            source_path = root / "engine" / "battle" / "effect_commands.asm"
            source_path.parent.mkdir(parents=True)
            source_path.write_text("; newer recoil proof input\n", encoding="utf-8")
            os.utime(log_path, (100, 100))
            os.utime(source_path, (200, 200))

            status = damage_modifier_recoil_smoke_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("clobber_smoke log is older than damage modifier/recoil proof inputs", status["errors"])
        self.assertTrue(any("effect_commands.asm" in item for item in status["stale_dependencies"]))

    def _write_damage_fuzz_report(
        self,
        root: Path,
        *,
        total_examples: int = DAMAGE_FUZZ_MIN_EXAMPLES,
        proof_status: str = "complete",
        fail_count: int = 0,
        ok: bool = True,
    ) -> Path:
        out_dir = root / "audit" / "damage_debugger"
        out_dir.mkdir(parents=True)
        path = out_dir / "fuzz_no_divergence.json"
        path.write_text(
            json.dumps(
                {
                    "kind": "damage_debugger_fuzz_no_divergence",
                    "schema_version": 1,
                    "proof_status": proof_status,
                    "mode": "hypothesis_damage_chain",
                    "workers": 2,
                    "max_examples": total_examples,
                    "total_examples": total_examples,
                    "tolerance": 1,
                    "result_count": 1,
                    "fail_count": fail_count,
                    "results": [
                        {
                            "worker_id": 0,
                            "max_examples": total_examples,
                            "seed": 1,
                            "ok": ok,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_damage_fuzz_no_divergence_status_accepts_passing_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_damage_fuzz_report(root)

            status = damage_fuzz_no_divergence_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["total_examples"], DAMAGE_FUZZ_MIN_EXAMPLES)

    def test_damage_fuzz_no_divergence_status_fails_closed_on_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_damage_fuzz_report(root, proof_status="missing_evidence", fail_count=1, ok=False)

            status = damage_fuzz_no_divergence_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("damage fuzz report has failures", status["errors"])
        self.assertEqual(status["bad_worker_count"], 1)

    def test_damage_fuzz_no_divergence_status_fails_closed_on_too_few_examples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_damage_fuzz_report(root, total_examples=DAMAGE_FUZZ_MIN_EXAMPLES - 1)

            status = damage_fuzz_no_divergence_status(root=root)

        self.assertFalse(status["ready"])
        self.assertTrue(any("need at least" in error for error in status["errors"]))

    def test_damage_fuzz_no_divergence_status_requires_hash_basis_when_rom_inputs_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_damage_fuzz_report(root)
            (root / "pokegold_debug.gbc").write_bytes(b"rom")
            (root / "pokegold_debug.sym").write_text("symbols\n", encoding="utf-8")

            status = damage_fuzz_no_divergence_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("missing hash_basis", status["errors"])

    def test_damage_fuzz_no_divergence_status_fails_closed_when_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = self._write_damage_fuzz_report(root)
            source_path = root / "tools" / "damage_debugger" / "fuzz.py"
            source_path.parent.mkdir(parents=True)
            source_path.write_text("# newer proof input\n", encoding="utf-8")
            os.utime(artifact, (100, 100))
            os.utime(source_path, (200, 200))

            status = damage_fuzz_no_divergence_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("damage fuzz artifact is older than proof inputs", status["errors"])
        self.assertTrue(any("fuzz.py" in item for item in status["stale_dependencies"]))

    def _write_damage_mutation_campaign_report(
        self,
        root: Path,
        *,
        mutation_ids: tuple[str, ...] = DAMAGE_MUTATION_REQUIRED_IDS,
        fail_count: int = 0,
        replay_verified: bool = True,
        include_does_not_close: bool = True,
        include_rng_distribution: bool = True,
        include_species_wide_eviolite: bool = False,
        include_auto_minimized_divergence: bool = False,
        include_selected_status_side_effects: bool = False,
    ) -> Path:
        out_dir = root / "audit" / "damage_debugger"
        out_dir.mkdir(parents=True)
        path = out_dir / "mutation_campaign.json"
        rows = []
        all_ids = list(mutation_ids)
        while len(all_ids) < 18:
            all_ids.append(f"extra_mutation_{len(all_ids)}")
        for mutation_id in all_ids:
            if mutation_id.startswith("replay_"):
                row = {
                    "mutation_id": mutation_id,
                    "case_id": mutation_id,
                    "campaign_id": "replay_watchpoints",
                    "category": "replay_watchpoints",
                    "method": "replay.replay_scenario",
                    "rom_backed": True,
                    "ok": replay_verified,
                    "replay_verified": replay_verified,
                    "hit": {
                        "old_hex": "0005",
                        "new_hex": "0000",
                        "watch": "wCurDamage",
                        "function": "BattleCommand_DamageCalc",
                        "replay_verified": replay_verified,
                    },
                }
            elif mutation_id.startswith("smoke_recoil"):
                row = {
                    "mutation_id": mutation_id,
                    "case_id": mutation_id,
                    "campaign_id": "recoil",
                    "category": "recoil",
                    "method": "clobber_smoke.run_scenario",
                    "rom_backed": True,
                    "ok": True,
                    "xfail": False,
                    "check_failures": [],
                    "seed_state": {"scenario": mutation_id},
                    "damage": 16,
                    "expected_low": 16,
                    "expected_high": 16,
                }
            elif mutation_id.startswith("smoke_afterhit"):
                row = {
                    "mutation_id": mutation_id,
                    "case_id": mutation_id,
                    "campaign_id": "after_hit_order",
                    "category": "after_hit_order",
                    "method": "clobber_smoke.run_scenario",
                    "rom_backed": True,
                    "ok": True,
                    "xfail": False,
                    "check_failures": [],
                    "seed_state": {"scenario": mutation_id},
                    "damage": 16,
                    "expected_low": 16,
                    "expected_high": 16,
                }
            elif mutation_id.startswith("smoke_"):
                row = {
                    "mutation_id": mutation_id,
                    "case_id": mutation_id,
                    "campaign_id": "damage_variation_and_type_matchup",
                    "category": "damage_variation_and_type_matchup",
                    "method": "clobber_smoke.run_scenario",
                    "rom_backed": True,
                    "ok": True,
                    "xfail": False,
                    "check_failures": [],
                    "seed_state": {"scenario": mutation_id},
                    "damage": 16,
                    "expected_low": 16,
                    "expected_high": 16,
                }
            else:
                campaign = (
                    "status_item_interactions"
                    if mutation_id.startswith("status_item")
                    else "damage_variation_and_type_matchup"
                    if mutation_id.startswith("damage_variation")
                    else "oracle_assumptions"
                )
                row = {
                    "mutation_id": mutation_id,
                    "case_id": mutation_id,
                    "campaign_id": campaign,
                    "category": campaign,
                    "method": "fuzz.check_one",
                    "rom_backed": True,
                    "ok": True,
                    "mutated_fields": ["field"],
                    "inputs": {"field": 1},
                    "rom_damage": 16,
                    "oracle_damage": 16,
                    "delta": 0,
                    "tolerance": 1,
                    "on_divergence": {"replay_command": "python -m tools.damage_debugger.replay"},
            }
            rows.append(row)
        if include_species_wide_eviolite:
            constants_dir = root / "constants"
            pokemon_dir = root / "data" / "pokemon"
            constants_dir.mkdir(parents=True)
            pokemon_dir.mkdir(parents=True)
            (constants_dir / "pokemon_constants.asm").write_text(
                "\n".join(
                    [
                        "\tconst_def 1",
                        "\tconst BULBASAUR",
                        "\tconst IVYSAUR",
                        "DEF NUM_POKEMON EQU const_value - 1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (pokemon_dir / "evos_attacks_pointers.asm").write_text(
                "\n".join(
                    [
                        "EvosAttacksPointers::",
                        "\tdw BulbasaurEvosAttacks",
                        "\tdw IvysaurEvosAttacks",
                        "\tassert_table_length NUM_POKEMON",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (pokemon_dir / "evos_attacks.asm").write_text(
                "\n".join(
                    [
                        "BulbasaurEvosAttacks:",
                        "\tdb EVOLVE_LEVEL, 16, IVYSAUR",
                        "\tdb 0 ; no more evolutions",
                        "\tdb 0 ; no more level-up moves",
                        "IvysaurEvosAttacks:",
                        "\tdb 0 ; no more evolutions",
                        "\tdb 0 ; no more level-up moves",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            for species_id, species_name, can_evolve in (
                (1, "BULBASAUR", True),
                (2, "IVYSAUR", False),
            ):
                for axis, is_physical in (("physical_defense", True), ("special_defense", False)):
                    mutation_id = f"species_wide_eviolite_{species_name.lower()}_{axis}"
                    rows.append(
                        {
                            "mutation_id": mutation_id,
                            "case_id": mutation_id,
                            "campaign_id": "status_item_interactions",
                            "category": "status_item_interactions",
                            "method": "fuzz.check_one",
                            "rom_backed": True,
                            "ok": True,
                            "species_wide_eviolite": True,
                            "species_id": species_id,
                            "species_name": species_name,
                            "eviolite_axis": axis,
                            "expected_can_evolve_defender": can_evolve,
                            "mutated_fields": [
                                "opponent_item",
                                "defender_species_id",
                                "can_evolve_defender",
                                "is_physical",
                            ],
                            "inputs": {
                                "defender_species_id": species_id,
                                "can_evolve_defender": can_evolve,
                                "opponent_item": 147,
                                "is_physical": is_physical,
                            },
                            "rom_damage": 16,
                            "oracle_damage": 16,
                            "delta": 0,
                            "tolerance": 1,
                            "on_divergence": {"replay_command": "python -m tools.damage_debugger.replay"},
                        }
                    )
        identity = {
            "rom_sha256": "A" * 64,
            "symbols_sha256": "B" * 64,
            "map_sha256": "C" * 64,
            "rule_map_sha256": "D" * 64,
            "source_tree_sha256": "test",
            "dirty_diff_hash": "E" * 64,
        }
        for row in rows:
            canonical = build_canonical_state_class(
                surface="damage_debugger",
                identity=identity,
                public_facts={
                    "mutation_id": row["mutation_id"],
                    "case_id": row["case_id"],
                    "campaign_id": row["campaign_id"],
                    "category": row["category"],
                    "method": row["method"],
                    "rom_backed": row["rom_backed"],
                    "ok": row["ok"],
                },
                surface_facts={
                    "damage": {
                        "mutation_campaign": "phase6_initial",
                        "campaign_id": row["campaign_id"],
                        "method": row["method"],
                        "rom_backed": row["rom_backed"],
                    }
                },
                backend="pyboy",
                proof_status="emulator_evidence" if row["ok"] else "missing_evidence",
            )
            row["canonical_state_class"] = canonical
            row["class_id"] = canonical["class_id"]
            row["class_fingerprint"] = canonical["class_fingerprint"]
            row["canonical_state_class_valid"] = canonical["valid"]
            row["canonical_state_class_errors"] = canonical["validation_errors"]
        rng_cases = [
            {
                "case_id": f"damage_variation_rng_multiplier_{multiplier}",
                "case_kind": "accepted_multiplier",
                "rom_backed": True,
                "base_damage": 255,
                "expected_multiplier": multiplier,
                "observed_multiplier": multiplier,
                "expected_damage": multiplier,
                "actual_damage": multiplier,
                "expected_rng_consumed": 1,
                "rng_consumed": 1,
                "returned": True,
                "ok": True,
            }
            for multiplier in range(217, 256)
        ]
        rng_cases.append(
            {
                "case_id": "damage_variation_rng_reject_216_then_accept_217",
                "case_kind": "rejection_loop",
                "rom_backed": True,
                "base_damage": 255,
                "expected_multiplier": 217,
                "observed_multiplier": 217,
                "rejected_multipliers": [216],
                "expected_damage": 217,
                "actual_damage": 217,
                "expected_rng_consumed": 2,
                "rng_consumed": 2,
                "returned": True,
                "ok": True,
            }
        )
        rng_distribution_proof = {
            "kind": "damage_debugger_rng_distribution_proof",
            "schema_version": 1,
            "evidence_id": DAMAGE_MUTATION_RNG_DISTRIBUTION_EVIDENCE_ID,
            "proof_status": "complete",
            "rom_backed": True,
            "base_damage": 255,
            "accepted_multiplier_min": 217,
            "accepted_multiplier_max": 255,
            "expected_multipliers": list(range(217, 256)),
            "observed_multipliers": list(range(217, 256)),
            "case_count": len(rng_cases),
            "pass_count": len(rng_cases),
            "fail_count": 0,
            "rejection_loop_verified": True,
            "cases": rng_cases,
            "failures": [],
        } if include_rng_distribution else {}
        auto_materialized_case = {
            "kind": "damage_debugger_materialized_divergence_case",
            "schema_version": 1,
            "case_id": "synthetic_forced_wise_glasses_status_divergence_route",
            "synthetic_forced_divergence": True,
            "inputs": {"move_type": 20, "is_physical": False, "user_item": 145},
            "rom_damage": 16,
            "oracle_damage": 16,
            "forced_oracle_damage": 18,
            "delta": -2,
            "tolerance": 1,
            "ok": False,
        }
        auto_materialized_hash = stable_json_hash(auto_materialized_case)
        selected_status_cases = {
            case_id: {
                "case_id": case_id,
                "component_differential_id": (
                    "full_restore_status_cure_component_differential"
                    if case_id.startswith("component_full_restore")
                    else "damaging_status_component_differential"
                ),
                "rom_backed": True,
                "ok": True,
                "rom": {"status_after": 0},
                "headless": {"final_status": "none"},
            }
            for case_id in (
                "component_ember_burn_success",
                "component_sludge_poison_success",
                "component_body_slam_paralyze_success",
                "component_body_slam_paralyze_effectchance_fail",
                "component_full_restore_clears_burn",
                "component_full_restore_clears_paralyze",
                "component_full_restore_clears_toxic_and_poison",
                "component_full_restore_clears_sleep_and_nightmare",
                "component_full_restore_clears_confusion_only",
            )
        }
        payload = {
            "kind": "damage_debugger_phase6_initial_mutation_campaign",
            "schema_version": 1,
            "proof_status": "complete" if fail_count == 0 and replay_verified else "missing_evidence",
            "closed_evidence_ids": [
                DAMAGE_MUTATION_CAMPAIGN_EVIDENCE_ID,
                *([DAMAGE_MUTATION_RNG_DISTRIBUTION_EVIDENCE_ID] if include_rng_distribution else []),
                *([DAMAGE_MUTATION_SPECIES_WIDE_EVIOLITE_EVIDENCE_ID] if include_species_wide_eviolite else []),
                *([DAMAGE_MUTATION_AUTO_MINIMIZED_DIVERGENCE_EVIDENCE_ID] if include_auto_minimized_divergence else []),
                *([DAMAGE_MUTATION_SELECTED_STATUS_SIDE_EFFECTS_EVIDENCE_ID] if include_selected_status_side_effects else []),
            ],
            "does_not_close": [DAMAGE_EXPANDED_MUTATION_CAMPAIGNS_GAP] if include_does_not_close else [],
            "backend": "pyboy",
            "campaign_ids": list(DAMAGE_MUTATION_REQUIRED_CAMPAIGNS),
            "required_campaigns": list(DAMAGE_MUTATION_REQUIRED_CAMPAIGNS),
            "campaign_count": len(DAMAGE_MUTATION_REQUIRED_CAMPAIGNS),
            "case_count": len(rows),
            "pass_count": len(rows) - fail_count,
            "fail_count": fail_count,
            "rom_backed_cases": rows,
            "rng_distribution_proof": rng_distribution_proof,
            "species_wide_eviolite_proof": {
                "kind": "damage_debugger_species_wide_eviolite_fuzz",
                "schema_version": 1,
                "evidence_id": DAMAGE_MUTATION_SPECIES_WIDE_EVIOLITE_EVIDENCE_ID,
                "proof_status": "complete",
                "rom_backed": True,
                "species_count": 2,
                "expected_case_count": 4,
                "expected_axes": ["physical_defense", "special_defense"],
                "can_evolve_species_count": 1,
                "case_count": 4,
                "pass_count": 4,
                "fail_count": 0,
                "failures": [],
            } if include_species_wide_eviolite else {},
            "auto_minimized_divergence_proof": {
                "kind": "damage_debugger_auto_minimized_divergence_artifacts",
                "schema_version": 1,
                "evidence_id": DAMAGE_MUTATION_AUTO_MINIMIZED_DIVERGENCE_EVIDENCE_ID,
                "proof_status": "complete",
                "route_proof_status": "complete",
                "route_proof_kind": "synthetic_forced_divergence_over_rom_checked_case",
                "campaign_fail_count": 0,
                "real_divergence_count": 0,
                "check_one_call_count": 4,
                "initial_inputs": {"move_type": 20, "is_physical": False, "user_item": 145, "weather": 2},
                "minimized_inputs": {"move_type": 20, "is_physical": False, "user_item": 145},
                "minimization_story": ["minimize: 1 field(s) reducible to defaults:"],
                "reduced_fields": ["weather"],
                "preserved_fields": ["user_item"],
                "non_default_minimized_fields": ["move_type", "is_physical", "user_item"],
                "materialized_case": auto_materialized_case,
                "materialized_case_sha256": auto_materialized_hash,
                "materialized_artifacts": [
                    {
                        "path": "audit/damage_debugger/mutation_campaign.json#/auto_minimized_divergence_proof/materialized_case",
                        "sha256": auto_materialized_hash,
                        "kind": "inline_materialized_divergence_case",
                    }
                ],
                "commands": {
                    "minimize_command": "python -m tools.damage_debugger.minimize --bug synthetic",
                    "replay_command": "python -m tools.damage_debugger.replay --scenario synthetic --watch wCurDamage --json",
                    "taint_command": "python -m tools.debugger dynamic-taint --sink-symbol wCurDamage",
                },
                "errors": [],
            } if include_auto_minimized_divergence else {},
            "selected_status_side_effects_proof": {
                "kind": "damage_debugger_selected_status_side_effects_rom_components",
                "schema_version": 1,
                "evidence_id": DAMAGE_MUTATION_SELECTED_STATUS_SIDE_EFFECTS_EVIDENCE_ID,
                "proof_status": "complete",
                "rom_backed": True,
                "source": "tools.headless_battle.rom_differential",
                "component_differential_ids": [
                    "damaging_status_component_differential",
                    "full_restore_status_cure_component_differential",
                ],
                "required_case_ids": list(selected_status_cases),
                "case_count": len(selected_status_cases),
                "pass_count": len(selected_status_cases),
                "fail_count": 0,
                "cases": selected_status_cases,
                "failures": [],
                "errors": [],
            } if include_selected_status_side_effects else {},
            "oracle_only_cases": [
                *([] if include_species_wide_eviolite else [
                    {
                        "mutation_id": "species_wide_eviolite_fuzz",
                        "rom_backed": False,
                        "reason_not_rom_backed": "fixed species smoke only",
                    }
                ]),
                *([] if include_selected_status_side_effects else [
                    {
                        "mutation_id": "full_battle_status_side_effects",
                        "rom_backed": False,
                        "reason_not_rom_backed": "broader full-battle mechanics",
                    }
                ]),
            ],
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_damage_mutation_campaign_replaces_broad_gap_with_residual_gap(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["damage_debugger"]
        if report["damage_mutation_campaign"]["ready"]:
            self.assertNotIn(DAMAGE_EXPANDED_MUTATION_CAMPAIGNS_GAP, row["missing_evidence"])
            self.assertNotIn(DAMAGE_EXPANDED_MUTATION_CAMPAIGNS_GAP, report["missing_evidence"])
            self.assertNotIn(DAMAGE_REMAINING_EXPANDED_MUTATION_CAMPAIGNS_GAP, row["missing_evidence"])
            self.assertNotIn(DAMAGE_REMAINING_EXPANDED_MUTATION_CAMPAIGNS_GAP, report["missing_evidence"])
            remaining_residuals = report["damage_mutation_campaign"]["remaining_residual_gaps"]
            for gap in remaining_residuals:
                self.assertIn(gap, row["missing_evidence"])
                self.assertIn(gap, report["missing_evidence"])
            if report["damage_mutation_campaign"]["rng_distribution_ready"]:
                self.assertNotIn(DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS[0], row["missing_evidence"])
                self.assertNotIn(DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS[0], report["missing_evidence"])
                self.assertIn(DAMAGE_MUTATION_RNG_DISTRIBUTION_EVIDENCE_ID, report["closed_evidence_ids"])
            if report["damage_mutation_campaign"]["species_wide_eviolite_ready"]:
                self.assertNotIn(DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS[1], row["missing_evidence"])
                self.assertNotIn(DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS[1], report["missing_evidence"])
                self.assertIn(DAMAGE_MUTATION_SPECIES_WIDE_EVIOLITE_EVIDENCE_ID, report["closed_evidence_ids"])
            self.assertIn(DAMAGE_MUTATION_CAMPAIGN_EVIDENCE_ID, report["closed_evidence_ids"])
            for evidence_id in DAMAGE_MUTATION_CAMPAIGN_EVIDENCE_IDS.values():
                self.assertIn(evidence_id, report["closed_evidence_ids"])
        else:
            self.assertIn(DAMAGE_EXPANDED_MUTATION_CAMPAIGNS_GAP, row["missing_evidence"])
            self.assertNotIn(DAMAGE_MUTATION_CAMPAIGN_EVIDENCE_ID, report["closed_evidence_ids"])

    def test_damage_mutation_campaign_status_accepts_initial_phase6_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_damage_mutation_campaign_report(root)

            status = damage_mutation_campaign_status(root=root)

        self.assertEqual(
            DAMAGE_MUTATION_CAMPAIGN_EVIDENCE_ID,
            "damage_debugger_phase6_initial_mutation_campaign.passed",
        )
        self.assertTrue(status["ready"])
        self.assertEqual(status["missing_mutation_ids"], [])
        self.assertEqual(status["rom_backed_case_count"], len(DAMAGE_MUTATION_REQUIRED_IDS))
        for campaign in DAMAGE_MUTATION_REQUIRED_CAMPAIGNS:
            self.assertTrue(status["campaign_proofs"][campaign]["ready"])
        self.assertEqual(
            set(status["closed_evidence_ids"]),
            {
                DAMAGE_MUTATION_CAMPAIGN_EVIDENCE_ID,
                DAMAGE_MUTATION_RNG_DISTRIBUTION_EVIDENCE_ID,
                *DAMAGE_MUTATION_CAMPAIGN_EVIDENCE_IDS.values(),
            },
        )
        self.assertTrue(status["rng_distribution_ready"])
        self.assertEqual(status["rng_distribution_case_count"], 40)
        self.assertTrue(status["rng_distribution_rejection_loop_verified"])
        self.assertTrue(status["canonical_state_class_cases_ready"])
        self.assertEqual(
            len(status["canonical_state_class_case_ids"]),
            len(DAMAGE_MUTATION_REQUIRED_IDS),
        )
        self.assertNotIn(DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS[0], status["remaining_residual_gaps"])
        for gap in DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS[1:]:
            self.assertIn(gap, status["remaining_residual_gaps"])
        for gap in DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS[1:-1]:
            self.assertIn(gap, status["oracle_only_residual_gaps"])

    def test_damage_mutation_campaign_status_accepts_species_wide_eviolite_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_damage_mutation_campaign_report(root, include_species_wide_eviolite=True)

            status = damage_mutation_campaign_status(root=root)

        self.assertTrue(status["ready"])
        self.assertTrue(status["species_wide_eviolite_ready"])
        self.assertEqual(status["species_wide_eviolite_case_count"], 4)
        self.assertEqual(status["species_wide_eviolite_species_count"], 2)
        self.assertEqual(status["species_wide_eviolite_can_evolve_species_count"], 1)
        self.assertIn(DAMAGE_MUTATION_SPECIES_WIDE_EVIOLITE_EVIDENCE_ID, status["closed_evidence_ids"])
        self.assertNotIn(DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS[1], status["remaining_residual_gaps"])
        self.assertNotIn(DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS[1], status["oracle_only_residual_gaps"])

    def test_damage_mutation_campaign_status_accepts_auto_minimized_divergence_route_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_damage_mutation_campaign_report(root, include_auto_minimized_divergence=True)

            status = damage_mutation_campaign_status(root=root)

        self.assertTrue(status["ready"])
        self.assertTrue(status["auto_minimized_divergence_ready"])
        self.assertIn(DAMAGE_MUTATION_AUTO_MINIMIZED_DIVERGENCE_EVIDENCE_ID, status["closed_evidence_ids"])
        self.assertNotIn(DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS[3], status["remaining_residual_gaps"])
        self.assertIn(DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS[2], status["remaining_residual_gaps"])

    def test_damage_mutation_campaign_status_fails_closed_on_placeholder_auto_minimized_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_damage_mutation_campaign_report(root, include_auto_minimized_divergence=True)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["auto_minimized_divergence_proof"]["materialized_case"] = {}
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = damage_mutation_campaign_status(root=root)

        self.assertFalse(status["ready"])
        self.assertFalse(status["auto_minimized_divergence_ready"])
        self.assertIn("auto_minimized_divergence missing materialized_case", "\n".join(status["errors"]))

    def test_damage_mutation_campaign_status_accepts_selected_status_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_damage_mutation_campaign_report(root, include_selected_status_side_effects=True)

            status = damage_mutation_campaign_status(root=root)

        self.assertTrue(status["ready"])
        self.assertTrue(status["selected_status_side_effects_ready"])
        self.assertEqual(status["selected_status_side_effects_case_count"], 9)
        self.assertIn(DAMAGE_MUTATION_SELECTED_STATUS_SIDE_EFFECTS_EVIDENCE_ID, status["closed_evidence_ids"])
        self.assertNotIn(DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS[2], status["remaining_residual_gaps"])
        self.assertNotIn(DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS[2], status["oracle_only_residual_gaps"])
        self.assertIn(DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS[3], status["remaining_residual_gaps"])

    def test_damage_mutation_campaign_status_fails_closed_on_missing_selected_status_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_damage_mutation_campaign_report(root, include_selected_status_side_effects=True)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["selected_status_side_effects_proof"]["cases"].pop("component_ember_burn_success")
            payload["selected_status_side_effects_proof"]["case_count"] -= 1
            payload["selected_status_side_effects_proof"]["pass_count"] -= 1
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = damage_mutation_campaign_status(root=root)

        self.assertFalse(status["ready"])
        self.assertFalse(status["selected_status_side_effects_ready"])
        self.assertIn("selected_status_side_effects_proof missing cases", "\n".join(status["errors"]))

    def test_damage_mutation_campaign_status_fails_closed_on_bad_species_wide_eviolite_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_damage_mutation_campaign_report(root, include_species_wide_eviolite=True)
            payload = json.loads(path.read_text(encoding="utf-8"))
            for row in payload["rom_backed_cases"]:
                if row.get("species_wide_eviolite") is True and row["species_id"] == 1:
                    row["inputs"]["can_evolve_defender"] = False
                    break
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = damage_mutation_campaign_status(root=root)

        self.assertFalse(status["ready"])
        self.assertFalse(status["species_wide_eviolite_ready"])
        self.assertTrue(
            any("can_evolve_defender mismatch" in error for error in status["species_wide_eviolite_errors"])
        )

    def test_damage_mutation_campaign_status_fails_closed_without_species_wide_evidence_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_damage_mutation_campaign_report(root, include_species_wide_eviolite=True)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["closed_evidence_ids"] = [
                evidence_id
                for evidence_id in payload["closed_evidence_ids"]
                if evidence_id != DAMAGE_MUTATION_SPECIES_WIDE_EVIOLITE_EVIDENCE_ID
            ]
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = damage_mutation_campaign_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn(
            f"missing closed evidence id: {DAMAGE_MUTATION_SPECIES_WIDE_EVIOLITE_EVIDENCE_ID}",
            status["errors"],
        )

    def test_damage_mutation_campaign_status_fails_closed_without_rng_distribution_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_damage_mutation_campaign_report(root, include_rng_distribution=False)

            status = damage_mutation_campaign_status(root=root)

        self.assertFalse(status["ready"])
        self.assertFalse(status["rng_distribution_ready"])
        self.assertIn("unexpected rng_distribution_proof kind", "\n".join(status["errors"]))
        self.assertIn(DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS[0], status["remaining_residual_gaps"])

    def test_damage_mutation_campaign_status_fails_closed_without_required_campaign_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_damage_mutation_campaign_report(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["required_campaigns"] = [
                campaign
                for campaign in payload["required_campaigns"]
                if campaign != "recoil"
            ]
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = damage_mutation_campaign_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("required_campaigns missing entries: ['recoil']", status["errors"])
        self.assertEqual(status["closed_evidence_ids"], [])

    def test_damage_mutation_campaign_status_fails_closed_when_campaign_count_mismatches_lists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_damage_mutation_campaign_report(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["campaign_count"] = 99
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = damage_mutation_campaign_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("campaign_count does not match campaign_ids/required_campaigns", status["errors"])

    def test_damage_mutation_campaign_status_fails_closed_when_case_campaign_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_damage_mutation_campaign_report(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["rom_backed_cases"][0]["campaign_id"] = "unknown_campaign"
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = damage_mutation_campaign_status(root=root)

        self.assertFalse(status["ready"])
        self.assertTrue(any("unknown campaign_id" in error for error in status["errors"]))

    def test_damage_mutation_campaign_status_fails_closed_when_campaign_has_no_rom_backed_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_damage_mutation_campaign_report(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["rom_backed_cases"] = [
                row
                for row in payload["rom_backed_cases"]
                if row["campaign_id"] != "recoil"
            ]
            payload["case_count"] = len(payload["rom_backed_cases"])
            payload["pass_count"] = len(payload["rom_backed_cases"])
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = damage_mutation_campaign_status(root=root)

        self.assertFalse(status["ready"])
        self.assertFalse(status["campaign_proofs"]["recoil"]["ready"])
        self.assertTrue(any("recoil missing campaign mutation ids" in error for error in status["errors"]))

    def test_damage_mutation_campaign_status_fails_closed_without_method_specific_proof_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_damage_mutation_campaign_report(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            for row in payload["rom_backed_cases"]:
                if row["method"] == "fuzz.check_one":
                    row.pop("inputs", None)
                    break
            for row in payload["rom_backed_cases"]:
                if row["method"] == "clobber_smoke.run_scenario":
                    row.pop("seed_state", None)
                    break
            for row in payload["rom_backed_cases"]:
                if row["method"] == "replay.replay_scenario":
                    row["hit"].pop("watch", None)
                    break
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = damage_mutation_campaign_status(root=root)

        self.assertFalse(status["ready"])
        joined = "\n".join(status["errors"])
        self.assertIn("missing fuzz inputs", joined)
        self.assertIn("missing smoke seed_state", joined)
        self.assertIn("replay hit missing watch", joined)

    def test_damage_mutation_campaign_status_fails_closed_without_required_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_damage_mutation_campaign_report(root, mutation_ids=DAMAGE_MUTATION_REQUIRED_IDS[:-1])

            status = damage_mutation_campaign_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn(DAMAGE_MUTATION_REQUIRED_IDS[-1], status["missing_mutation_ids"])

    def test_damage_mutation_campaign_status_fails_closed_without_replay_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_damage_mutation_campaign_report(root, replay_verified=False)

            status = damage_mutation_campaign_status(root=root)

        self.assertFalse(status["ready"])
        self.assertGreater(status["bad_case_count"], 0)
        self.assertTrue(any("replay was not verified" in error for error in status["errors"]))

    def test_damage_mutation_campaign_status_fails_closed_if_artifact_claims_broad_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_damage_mutation_campaign_report(root, include_does_not_close=False)

            status = damage_mutation_campaign_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("artifact must explicitly leave expanded_mutation_campaigns open", status["errors"])

    def test_damage_mutation_campaign_status_fails_closed_on_malformed_claim_lists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_damage_mutation_campaign_report(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["closed_evidence_ids"] = DAMAGE_MUTATION_CAMPAIGN_EVIDENCE_ID
            payload["does_not_close"] = DAMAGE_EXPANDED_MUTATION_CAMPAIGNS_GAP
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = damage_mutation_campaign_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("closed_evidence_ids must be a list", status["errors"])
        self.assertIn("does_not_close must be a list", status["errors"])

    def test_damage_mutation_campaign_status_fails_closed_without_oracle_only_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_damage_mutation_campaign_report(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["oracle_only_cases"][0].pop("reason_not_rom_backed", None)
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = damage_mutation_campaign_status(root=root)

        self.assertFalse(status["ready"])
        self.assertTrue(any("oracle-only case missing reason_not_rom_backed" in error for error in status["errors"]))

    def test_damage_mutation_campaign_status_fails_closed_without_canonical_class(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_damage_mutation_campaign_report(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["rom_backed_cases"][0].pop("canonical_state_class", None)
            payload["rom_backed_cases"][0].pop("class_id", None)
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = damage_mutation_campaign_status(root=root)

        self.assertFalse(status["ready"])
        self.assertFalse(status["canonical_state_class_cases_ready"])
        self.assertTrue(any("missing canonical_state_class" in error for error in status["canonical_state_class_errors"]))

    def test_damage_mutation_campaign_status_fails_closed_on_canonical_class_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_damage_mutation_campaign_report(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["rom_backed_cases"][0]["class_id"] = "csc_MISMATCH"
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = damage_mutation_campaign_status(root=root)

        self.assertFalse(status["ready"])
        self.assertFalse(status["canonical_state_class_cases_ready"])
        self.assertTrue(
            any("class_id does not match canonical_state_class.class_id" in error for error in status["errors"])
        )

    def test_after_hit_item_order_status_requires_named_passed_rom_golden(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "audit" / "damage_debugger"
            out_dir.mkdir(parents=True)
            (out_dir / "clobber_smoke.log").write_text(
                f"{AFTER_HIT_ORDER_SCENARIO:<42s}      16      16-16   PASS  order proof\n"
                "PASS: all 1 scenarios within expected damage ranges.\n",
                encoding="utf-8",
            )

            status = after_hit_item_order_status(root=root)

        self.assertTrue(status["ready"])
        self.assertIn(AFTER_HIT_ORDER_SCENARIO, status["scenario_line"])

    def test_after_hit_item_order_status_fails_closed_without_named_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "audit" / "damage_debugger"
            out_dir.mkdir(parents=True)
            (out_dir / "clobber_smoke.log").write_text(
                "afterhit_rocky_helmet          16      16-16   PASS\n"
                "PASS: all 1 scenarios within expected damage ranges.\n",
                encoding="utf-8",
            )

            status = after_hit_item_order_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn(f"{AFTER_HIT_ORDER_SCENARIO} did not PASS", status["errors"])

    def test_after_hit_item_order_status_fails_closed_when_log_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "audit" / "damage_debugger"
            out_dir.mkdir(parents=True)
            log_path = out_dir / "clobber_smoke.log"
            log_path.write_text(
                f"{AFTER_HIT_ORDER_SCENARIO:<42s}      16      16-16   PASS  order proof\n"
                "PASS: all 1 scenarios within expected damage ranges.\n",
                encoding="utf-8",
            )
            source_path = root / "tools" / "damage_debugger" / "clobber_smoke.py"
            source_path.parent.mkdir(parents=True)
            source_path.write_text("# newer proof input\n", encoding="utf-8")
            os.utime(log_path, (100, 100))
            os.utime(source_path, (200, 200))

            status = after_hit_item_order_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("clobber_smoke log is older than after-hit proof inputs", status["errors"])
        self.assertTrue(any("clobber_smoke.py" in item for item in status["stale_dependencies"]))

    def test_audio_apu_event_envelope_records_named_backend_limit(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["audio"]
        if report["audio_apu_event_envelope"]["ready"]:
            self.assertNotIn("apu_register_event_stream", row["missing_evidence"])
            self.assertNotIn(AUDIO_CRY_MUSIC_SFX_BACKEND_PARITY_GAP, row["missing_evidence"])
            self.assertNotIn(AUDIO_CRY_MUSIC_SFX_BACKEND_PARITY_GAP, report["missing_evidence"])
            self.assertNotIn(AUDIO_REMAINING_CRY_MUSIC_SFX_PARITY_GAP, row["missing_evidence"])
            self.assertNotIn(AUDIO_REMAINING_CRY_MUSIC_SFX_PARITY_GAP, report["missing_evidence"])
            self.assertEqual(row["proof_status"], "runtime_proven")
            self.assertEqual(row["backend"], "pyboy_with_named_backend_limit")
            self.assertTrue(row["unsupported_reason"])
            self.assertIn(AUDIO_APU_EVENT_EVIDENCE_ID, report["closed_evidence_ids"])
            self.assertIn(AUDIO_TYPHLOSION_CRY_MATCH_EVIDENCE_ID, report["closed_evidence_ids"])
        else:
            self.assertIn("apu_register_event_stream", row["missing_evidence"])

    def test_audio_apu_event_envelope_status_requires_explicit_runtime_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "audit" / "debugger_literal_anything"
            out_dir.mkdir(parents=True)
            event = runtime_event_envelope(
                event_kind="apu",
                source_kind="cry_apu_timeline",
                source_report="audio_probe.json",
                proof_status="runtime_observed",
                observation_type="explicit_hardware_event",
                payload={"registers": {"rNR10": 1}, "changed_registers": ["rNR10"]},
            )
            (out_dir / "audio_apu_event_envelope.json").write_text(
                json.dumps(
                    {
                        "kind": "debugger_deity_surface_replay",
                        "surface": "audio",
                        "valid": True,
                        "replay_diff": {
                            "kind": "debugger_deity_audio_replay_diff",
                            "valid": True,
                            "status": "matched_runtime_capture",
                            "static_channels": [5],
                        },
                        "runtime_replay": {
                            "kind": "debugger_deity_cry_apu_timeline",
                            "changed_register_count": 1,
                            "runtime_events": [event],
                        },
                    }
                ),
                encoding="utf-8",
            )

            status = audio_apu_event_envelope_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["event_count"], 1)
        self.assertEqual(status["static_channel_count"], 1)
        self.assertEqual(status["replay_diff_status"], "matched_runtime_capture")

    def test_audio_apu_event_envelope_status_fails_closed_without_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "audit" / "debugger_literal_anything"
            out_dir.mkdir(parents=True)
            (out_dir / "audio_apu_event_envelope.json").write_text(
                json.dumps(
                    {
                        "kind": "debugger_deity_surface_replay",
                        "surface": "audio",
                        "valid": True,
                        "replay_diff": {
                            "kind": "debugger_deity_audio_replay_diff",
                            "valid": True,
                            "status": "matched_runtime_capture",
                            "static_channels": [5],
                        },
                        "runtime_replay": {
                            "kind": "debugger_deity_cry_apu_timeline",
                            "changed_register_count": 1,
                            "runtime_events": [],
                        },
                    }
                ),
                encoding="utf-8",
            )

            status = audio_apu_event_envelope_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("no APU runtime_event_envelope events", status["errors"])

    def test_audio_apu_event_envelope_status_fails_closed_without_static_runtime_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "audit" / "debugger_literal_anything"
            out_dir.mkdir(parents=True)
            event = runtime_event_envelope(
                event_kind="apu",
                source_kind="cry_apu_timeline",
                source_report="audio_probe.json",
                proof_status="runtime_observed",
                observation_type="explicit_hardware_event",
                payload={"registers": {"rNR10": 1}, "changed_registers": ["rNR10"]},
            )
            (out_dir / "audio_apu_event_envelope.json").write_text(
                json.dumps(
                    {
                        "kind": "debugger_deity_surface_replay",
                        "surface": "audio",
                        "valid": True,
                        "replay_diff": {
                            "kind": "debugger_deity_audio_replay_diff",
                            "valid": False,
                            "status": "diverged",
                            "static_channels": [],
                        },
                        "runtime_replay": {
                            "kind": "debugger_deity_cry_apu_timeline",
                            "changed_register_count": 1,
                            "runtime_events": [event],
                        },
                    }
                ),
                encoding="utf-8",
            )

            status = audio_apu_event_envelope_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("audio replay_diff is not valid", status["errors"])
        self.assertIn("no source cry channels recorded in replay_diff", status["errors"])

    def test_script_vm_event_log_closes_only_script_vm_gap(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["script_map_content"]
        if report["script_vm_event_log"]["ready"]:
            self.assertNotIn("script_vm_event_log", row["missing_evidence"])
            if report["script_map_content_materializers"]["ready"]:
                self.assertNotIn(SCRIPT_MAP_CALLBACK_MATERIALIZER_GAP, row["missing_evidence"])
                self.assertNotIn(SCRIPT_WARP_OBJECT_COLLISION_REPLAY_GAP, row["missing_evidence"])
                if report["script_map_content_materializers"]["callback_script_entry_materializer_ready"]:
                    if report["script_map_content_materializers"]["callback_script_entry_corpus_ready"]:
                        self.assertNotIn(SCRIPT_MAP_CALLBACK_CORPUS_REMAINING_GAP, row["missing_evidence"])
                    else:
                        self.assertIn(SCRIPT_MAP_CALLBACK_CORPUS_REMAINING_GAP, row["missing_evidence"])
                else:
                    self.assertIn(SCRIPT_MAP_CALLBACK_REMAINING_GAP, row["missing_evidence"])
                if report["script_map_content_materializers"]["warp_object_position_materializers_ready"]:
                    if report["script_map_content_runtime_replays"]["ready"]:
                        self.assertNotIn(SCRIPT_WARP_OBJECT_COLLISION_RUNTIME_REMAINING_GAP, row["missing_evidence"])
                        self.assertIn(SCRIPT_WARP_OBJECT_COLLISION_RUNTIME_EVIDENCE_ID, report["closed_evidence_ids"])
                    else:
                        self.assertIn(SCRIPT_WARP_OBJECT_COLLISION_RUNTIME_REMAINING_GAP, row["missing_evidence"])
                    if report["script_map_content_materializers"]["object_struct_visibility_materializers_ready"]:
                        self.assertNotIn(SCRIPT_OBJECT_STRUCT_VISIBILITY_REMAINING_GAP, row["missing_evidence"])
                    else:
                        self.assertIn(SCRIPT_OBJECT_STRUCT_VISIBILITY_REMAINING_GAP, row["missing_evidence"])
                else:
                    self.assertIn(SCRIPT_WARP_OBJECT_COLLISION_REMAINING_GAP, row["missing_evidence"])
            else:
                self.assertIn(SCRIPT_MAP_CALLBACK_MATERIALIZER_GAP, row["missing_evidence"])
                self.assertIn(SCRIPT_WARP_OBJECT_COLLISION_REPLAY_GAP, row["missing_evidence"])
            self.assertIn(SCRIPT_VM_EVENT_EVIDENCE_ID, report["closed_evidence_ids"])
        else:
            self.assertIn("script_vm_event_log", row["missing_evidence"])

    def _write_script_map_content_materializers(
        self,
        root: Path,
        *,
        scenario_ids: tuple[str, ...] = tuple(SCRIPT_MAP_CONTENT_MATERIALIZER_SCENARIOS),
        valid: bool = True,
    ) -> Path:
        out_dir = root / "audit" / "debugger_literal_anything"
        out_dir.mkdir(parents=True)
        def scenario_contract(scenario_id: str) -> tuple[str, str]:
            if scenario_id in SCRIPT_MAP_CONTENT_MATERIALIZER_SCENARIOS:
                return SCRIPT_MAP_CONTENT_MATERIALIZER_SCENARIOS[scenario_id]
            if scenario_id.startswith("script_corpus_"):
                return ("script_command_stream", "script_entry")
            return ("unknown", "unknown")

        scenario_rows = []
        for scenario_id in scenario_ids:
            scenario_type, precondition_kind = scenario_contract(scenario_id)
            scenario_rows.append(
                {
                    "id": scenario_id,
                    "scenario_type": scenario_type,
                    "source_file": "maps/AzaleaTown.asm",
                    "state_preconditions": [
                        {
                            "id": precondition_kind,
                            "kind": precondition_kind,
                            "values": {"source_file": "maps/AzaleaTown.asm"},
                        }
                    ],
                }
            )
        (out_dir / "script_map_content_scenarios.jsonl").write_text(
            "\n".join(json.dumps(row) for row in scenario_rows) + "\n",
            encoding="utf-8",
        )
        materializations = []
        for scenario_id in scenario_ids:
            scenario_type, precondition_kind = scenario_contract(scenario_id)
            patch_count = 6 if precondition_kind == "script_entry" else 4
            if precondition_kind == "script_entry":
                patches = [
                    {"symbol": "wScriptBank", "value": 0x48},
                    {"symbol": "wScriptPos", "value": 0xE5},
                    {"symbol": "wScriptPos+1", "value": 0x50},
                    {"symbol": "wScriptRunning", "value": 0xFF},
                    {"symbol": "wScriptMode", "value": 1},
                    {"symbol": "wScriptStackSize", "value": 0},
                ]
            else:
                patches = [
                    {"symbol": "wMapGroup", "value": 8},
                    {"symbol": "wMapNumber", "value": 7},
                    {"symbol": "wXCoord", "value": 15},
                    {"symbol": "wYCoord", "value": 9},
                ]
            canonical = build_canonical_state_class(
                surface="content_state",
                identity={
                    "rom_sha256": "A" * 64,
                    "symbols_sha256": "B" * 64,
                    "map_sha256": "C" * 64,
                    "rule_map_sha256": "D" * 64,
                    "source_tree_sha256": "test",
                    "dirty_diff_hash": "E" * 64,
                },
                public_facts={
                    "scenario_id": scenario_id,
                    "scenario_type": scenario_type,
                    "precondition_kind": precondition_kind,
                    "status": "ready",
                },
                surface_facts={
                    "content": {
                        "materialization_surface": "content_state",
                        "scenario_type": scenario_type,
                        "precondition_kind": precondition_kind,
                        "status": "ready",
                        "patch_count": patch_count,
                    }
                },
                backend="static",
                proof_status="static_mirror_only",
                missing_evidence=["content_state_runtime_replay_not_attached"],
                blocking_gaps=["content_state_runtime_replay_not_attached"],
            )
            materialization = {
                "scenario_id": scenario_id,
                "scenario_type": scenario_type,
                "precondition_kind": precondition_kind,
                "status": "ready",
                "patch_count": patch_count,
                "source_file": "maps/AzaleaTown.asm",
                "patches": patches,
                "canonical_state_class": canonical,
                "class_id": canonical["class_id"],
                "class_fingerprint": canonical["class_fingerprint"],
            }
            if scenario_id == "content_scenario_1_0019":
                object_patches = [
                    {"symbol": "wMap11ObjectStructID", "value": 1},
                    {"symbol": "wMap11ObjectSprite", "value": 0xF6},
                    {"symbol": "wMap11ObjectYCoord", "value": 14},
                    {"symbol": "wMap11ObjectXCoord", "value": 15},
                    {"symbol": "wMap11ObjectMovement", "value": 8},
                    {"symbol": "wMap11ObjectRadius", "value": 0},
                    {"symbol": "wMap11ObjectHour1", "value": 0xFF},
                    {"symbol": "wMap11ObjectHour2", "value": 0xFF},
                    {"symbol": "wMap11ObjectType", "value": 0},
                    {"symbol": "wMap11ObjectSightRange", "value": 0},
                    {"symbol": "wMap11ObjectScript", "value": 0},
                    {"symbol": "wMap11ObjectScript+1", "value": 0x40},
                    {"symbol": "wMap11ObjectEventFlag", "value": 0xBF},
                    {"symbol": "wMap11ObjectEventFlag+1", "value": 0x06},
                    {"symbol": "wObject1MapObjectIndex", "value": 11},
                    {"symbol": "wObject1Sprite", "value": 0xF6},
                    {"symbol": "wObject1MovementType", "value": 8},
                    {"symbol": "wObject1Flags", "value": 0},
                    {"symbol": "wObject1Flags+1", "value": 0},
                    {"symbol": "wObject1Palette", "value": 0},
                    {"symbol": "wObject1Walking", "value": 0xFF},
                    {"symbol": "wObject1Direction", "value": 8},
                    {"symbol": "wObject1StepType", "value": 0},
                    {"symbol": "wObject1Action", "value": 1},
                    {"symbol": "wObject1Facing", "value": 0xFF},
                    {"symbol": "wObject1MapX", "value": 15},
                    {"symbol": "wObject1MapY", "value": 14},
                    {"symbol": "wObject1LastMapX", "value": 15},
                    {"symbol": "wObject1LastMapY", "value": 14},
                    {"symbol": "wObject1InitX", "value": 15},
                    {"symbol": "wObject1InitY", "value": 14},
                    {"symbol": "wObject1Radius", "value": 0x11},
                    {"symbol": "wObject1Range", "value": 0},
                    {"symbol": "wObjectMasks+11", "value": 0},
                ]
                materialization["object_visibility_materializer"] = {
                    "kind": "object_struct_visibility_materializer",
                    "status": "ready",
                    "proof_status": "static_synthetic",
                    "scenario_id": scenario_id,
                    "source_file": "maps/AzaleaTown.asm",
                    "source_line": 435,
                    "map_object_index": 11,
                    "object_struct_index": 1,
                    "patch_count": len(object_patches),
                    "patch_symbols": [patch["symbol"] for patch in object_patches],
                    "patches": object_patches,
                    "source_values": {
                        "x": 11,
                        "y": 10,
                        "script": "ObjectEvent",
                        "event_flag": "EVENT_RIVAL_AZALEA_TOWN",
                    },
                }
            materializations.append(materialization)
        path = out_dir / "script_map_content_materializers.json"
        path.write_text(
            json.dumps(
                {
                    "kind": "unified_debugger_content_state_materialization",
                    "valid": valid,
                    "scenario_count": len(scenario_ids),
                    "materialization_count": len(materializations),
                    "patch_count": sum(int(item["patch_count"]) for item in materializations),
                    "input_scenarios": ["audit/debugger_literal_anything/script_map_content_scenarios.jsonl"],
                    "input_scenario_ids": list(scenario_ids),
                    "materializations": materializations,
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_script_map_content_materializer_status_accepts_selected_materializers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_script_map_content_materializers(root)

            status = script_map_content_materializer_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["ready_materialization_count"], len(SCRIPT_MAP_CONTENT_MATERIALIZER_SCENARIOS))
        self.assertEqual(status["patch_count"], 14)
        self.assertTrue(status["callback_script_entry_materializer_ready"])
        self.assertTrue(status["callback_script_entry_corpus_ready"])
        self.assertEqual(status["callback_script_entry_corpus_expected_count"], 1)
        self.assertEqual(status["callback_script_entry_corpus_ready_count"], 1)
        self.assertTrue(status["warp_object_position_materializers_ready"])
        self.assertTrue(status["object_struct_visibility_materializers_ready"])
        self.assertTrue(status["canonical_state_class_materializers_ready"])
        self.assertEqual(
            sorted(status["canonical_state_class_ids"]),
            sorted(SCRIPT_MAP_CONTENT_MATERIALIZER_SCENARIOS),
        )
        self.assertIn("wScriptBank", status["callback_script_entry_patch_symbols"])
        self.assertEqual(
            status["warp_object_position_scenario_ids"],
            ["content_scenario_1_0000", "content_scenario_1_0019"],
        )
        self.assertEqual(status["object_struct_visibility_scenario_ids"], ["content_scenario_1_0019"])
        self.assertIn("wObjectMasks+11", status["object_struct_visibility_patch_symbols"])

    def test_script_map_content_materializer_status_fails_closed_without_object_visibility(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_script_map_content_materializers(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            for row in payload["materializations"]:
                if row["scenario_id"] == "content_scenario_1_0019":
                    row.pop("object_visibility_materializer", None)
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = script_map_content_materializer_status(root=root)

        self.assertTrue(status["ready"])
        self.assertFalse(status["object_struct_visibility_materializers_ready"])
        self.assertIn(
            "content_scenario_1_0019 missing object_visibility_materializer",
            status["object_struct_visibility_errors"],
        )

    def test_script_map_content_materializer_status_fails_closed_on_bad_object_visibility_patch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_script_map_content_materializers(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            for row in payload["materializations"]:
                if row["scenario_id"] == "content_scenario_1_0019":
                    patches = row["object_visibility_materializer"]["patches"]
                    row["object_visibility_materializer"]["patches"] = [
                        patch for patch in patches if patch["symbol"] != "wObjectMasks+11"
                    ]
                    row["object_visibility_materializer"]["patch_count"] = len(
                        row["object_visibility_materializer"]["patches"]
                    )
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = script_map_content_materializer_status(root=root)

        self.assertTrue(status["ready"])
        self.assertFalse(status["object_struct_visibility_materializers_ready"])
        self.assertTrue(
            any("object visibility materializer missing patches" in error for error in status["object_struct_visibility_errors"])
        )

    def test_script_map_content_materializer_status_fails_closed_without_callback_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_script_map_content_materializers(
                root,
                scenario_ids=("content_scenario_1_0000", "content_scenario_1_0019"),
            )

            status = script_map_content_materializer_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("content_scenario_1_0032", status["missing_scenarios"])

    def test_script_map_content_materializer_status_fails_closed_without_script_runner_patches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_script_map_content_materializers(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            for row in payload["materializations"]:
                if row["scenario_id"] == "content_scenario_1_0032":
                    row["patches"] = [{"symbol": "wScriptBank", "value": 0x48}]
                    row["patch_count"] = 1
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = script_map_content_materializer_status(root=root)

        self.assertFalse(status["ready"])
        self.assertFalse(status["callback_script_entry_materializer_ready"])
        self.assertTrue(
            any("callback script-entry materializer missing patches" in error for error in status["errors"])
        )

    def test_script_map_content_materializer_status_fails_closed_without_corpus_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_script_map_content_materializers(
                root,
                scenario_ids=(
                    *SCRIPT_MAP_CONTENT_MATERIALIZER_SCENARIOS,
                    "script_corpus_extra",
                ),
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["materializations"] = [
                row
                for row in payload["materializations"]
                if row["scenario_id"] != "script_corpus_extra"
            ]
            payload["materialization_count"] = len(payload["materializations"])
            payload["patch_count"] = sum(
                int(item["patch_count"])
                for item in payload["materializations"]
            )
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = script_map_content_materializer_status(root=root)

        self.assertFalse(status["ready"])
        self.assertFalse(status["callback_script_entry_corpus_ready"])
        self.assertIn(
            "script_corpus_extra",
            status["callback_script_entry_corpus_missing_scenario_ids"],
        )

    def test_script_map_content_materializer_status_fails_closed_without_canonical_class(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_script_map_content_materializers(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["materializations"][0].pop("canonical_state_class", None)
            payload["materializations"][0].pop("class_id", None)
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = script_map_content_materializer_status(root=root)

        self.assertFalse(status["ready"])
        self.assertFalse(status["canonical_state_class_materializers_ready"])
        self.assertIn("content_scenario_1_0000 missing canonical_state_class", status["canonical_state_class_errors"])

    def test_script_map_content_materializer_status_fails_closed_on_class_id_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_script_map_content_materializers(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["materializations"][0]["class_id"] = "csc_MISMATCH"
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = script_map_content_materializer_status(root=root)

        self.assertFalse(status["ready"])
        self.assertFalse(status["canonical_state_class_materializers_ready"])
        self.assertTrue(
            any("class_id does not match canonical_state_class.class_id" in error for error in status["errors"])
        )

    def test_script_map_content_materializer_status_fails_closed_on_unproven_execution_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write_script_map_content_materializers(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["executed"] = True
            payload["execution"] = {"executed": True, "out_state": "", "runtime_events": []}
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = script_map_content_materializer_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("executed materializer report is missing output state", status["errors"])
        self.assertIn("executed materializer report is missing runtime evidence", status["errors"])

    def _write_script_map_content_runtime_fixture(
        self,
        root: Path,
        *,
        omit_case: str = "",
        bad_warp_destination: bool = False,
        bad_event_scope: bool = False,
        unobserved_case: str = "",
    ) -> Path:
        out_dir = root / "audit" / "debugger_literal_anything"
        out_dir.mkdir(parents=True)
        warp = {
            "case_id": "azalea_pokecenter_warp_runtime",
            "scenario_id": "content_scenario_1_0000",
            "transition_kind": "warp_collision_dispatch",
            "source_map": "AzaleaTown_MapEvents",
            "destination_map": "AZALEA_POKECENTER_1F",
            "destination_resolved_map": "AzaleaPokecenter1F",
            "destination_warp": 1,
            "after_warp_check": {
                "wNextWarp": 1,
                "wNextMapGroup": 8,
                "wNextMapNumber": 2 if bad_warp_destination else 1,
            },
            "after_enter_map_warp": {"wWarpNumber": 1, "wMapGroup": 8, "wMapNumber": 1},
            "helper_hits": {"WarpCheck": 1, "EnterMapWarp": 1},
            "helper_samples": [{"label": "WarpCheck"}, {"label": "EnterMapWarp"}],
            "warp_check_carry": True,
            "enter_map_warp_carry": False,
            "carry_observed": True,
            "transition_observed": unobserved_case != "azalea_pokecenter_warp_runtime",
        }
        obj = {
            "case_id": "azalea_rocket_object_runtime",
            "scenario_id": "content_scenario_1_0019",
            "transition_kind": "object_facing_script_dispatch",
            "source_map": "AzaleaTown_MapEvents",
            "script_label": "AzaleaTownRocket1Script",
            "expected_script_bank": 0x48,
            "expected_script_address": 0x517C,
            "map_object_index": 2,
            "after": {
                "wScriptBank": 0x48,
                "wScriptPosWord": 0x517C,
                "wScriptRunning": 0xFF,
                "hLastTalked": 2,
                "hObjectStructIndex": 1,
                "hMapObjectIndex": 0,
            },
            "helper_hits": {"TryObjectEvent": 1, "CheckFacingObject": 1, "CallScript": 1},
            "helper_samples": [{"label": "TryObjectEvent"}, {"label": "CheckFacingObject"}, {"label": "CallScript"}],
            "try_object_event_carry": True,
            "carry_observed": True,
            "transition_observed": unobserved_case != "azalea_rocket_object_runtime",
        }
        cases = [case for case in (warp, obj) if case["case_id"] != omit_case]
        events = []
        for seq, case in enumerate(cases):
            if not case["transition_observed"]:
                continue
            scope_surface = "wrong" if bad_event_scope and seq == 0 else "script_map_content"
            events.append(
                runtime_event_envelope(
                    event_kind="control_flow",
                    source_kind="pyboy_script_map_content_runtime",
                    source_report="debugger_deity_script_map_content_runtime_replays",
                    seq=seq,
                    proof_status="runtime_observed",
                    observation_type="instruction_pre_state",
                    scope={
                        "backend": "pyboy",
                        "surface": scope_surface,
                        "scenario_id": case["scenario_id"],
                    },
                    subjects={"helpers": sorted(case["helper_hits"])},
                    precision={
                        "transition_observed": case["transition_observed"],
                        "helper_hit_count": sum(case["helper_hits"].values()),
                    },
                    validation={
                        "case_id": case["case_id"],
                        "transition_kind": case["transition_kind"],
                    },
                    payload=case,
                )
            )
        path = out_dir / "script_map_content_runtime_replays.json"
        path.write_text(
            json.dumps(
                {
                    "kind": "debugger_deity_surface_replay",
                    "surface": "content",
                    "valid": True,
                    "runtime_replay": {
                        "kind": "debugger_deity_script_map_content_runtime_replays",
                        "valid": True,
                        "backend": "pyboy",
                        "case_count": len(cases),
                        "runtime_event_count": len(events),
                        "cases": cases,
                        "runtime_events": events,
                        "known_limits": [
                            "The selected warp and object cases execute ROM helper routines from synthesized WRAM state.",
                            "This is not full overworld button/input flow and not all map collisions or all object events.",
                        ],
                    },
                    "known_limits": [
                        "This is a direct PyBoy helper harness for selected Azalea warp/object content scenarios.",
                        "It proves selected ROM helper behavior after synthesized WRAM setup, not full overworld button/input flow coverage.",
                    ],
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_script_map_content_runtime_replay_status_accepts_selected_helper_replays(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_script_map_content_runtime_fixture(root)

            status = script_map_content_runtime_replay_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["case_count"], 2)
        self.assertEqual(status["runtime_event_count"], 2)
        self.assertEqual(
            sorted(status["validated_cases"]),
            ["azalea_pokecenter_warp_runtime", "azalea_rocket_object_runtime"],
        )

    def test_script_map_content_runtime_replay_status_fails_closed_on_missing_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_script_map_content_runtime_fixture(root, omit_case="azalea_rocket_object_runtime")

            status = script_map_content_runtime_replay_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn(
            "missing script/map content runtime case: azalea_rocket_object_runtime",
            status["errors"],
        )

    def test_script_map_content_runtime_replay_status_fails_closed_on_bad_observed_warp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_script_map_content_runtime_fixture(root, bad_warp_destination=True)

            status = script_map_content_runtime_replay_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("azalea_pokecenter_warp_runtime wNextMapNumber mismatch", status["errors"])

    def test_script_map_content_runtime_replay_status_fails_closed_on_bad_event_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_script_map_content_runtime_fixture(root, bad_event_scope=True)

            status = script_map_content_runtime_replay_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("azalea_pokecenter_warp_runtime: script/map content event scope mismatch", status["errors"])

    def test_script_map_content_runtime_replay_status_fails_closed_on_unobserved_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_script_map_content_runtime_fixture(root, unobserved_case="azalea_rocket_object_runtime")

            status = script_map_content_runtime_replay_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn(
            "azalea_rocket_object_runtime did not prove an observed runtime transition",
            status["errors"],
        )
        self.assertIn("azalea_rocket_object_runtime missing runtime event envelope", status["errors"])

    def test_script_map_content_materializers_replace_broad_gaps_with_residual_gaps(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["script_map_content"]
        if report["script_map_content_materializers"]["ready"]:
            self.assertIn(SCRIPT_MAP_CONTENT_MATERIALIZER_EVIDENCE_ID, report["closed_evidence_ids"])
            if report["script_map_content_materializers"]["canonical_state_class_materializers_ready"]:
                self.assertIn(
                    CANONICAL_STATE_CLASS_CONTENT_STATE_MATERIALIZER_EVIDENCE_ID,
                    report["closed_evidence_ids"],
                )
            self.assertNotIn(SCRIPT_MAP_CALLBACK_MATERIALIZER_GAP, row["missing_evidence"])
            self.assertNotIn(SCRIPT_WARP_OBJECT_COLLISION_REPLAY_GAP, row["missing_evidence"])
            self.assertNotIn(SCRIPT_MAP_CALLBACK_MATERIALIZER_GAP, report["missing_evidence"])
            self.assertNotIn(SCRIPT_WARP_OBJECT_COLLISION_REPLAY_GAP, report["missing_evidence"])
            if report["script_map_content_materializers"]["callback_script_entry_materializer_ready"]:
                self.assertIn(SCRIPT_MAP_CALLBACK_SELECTED_EVIDENCE_ID, report["closed_evidence_ids"])
                self.assertNotIn(SCRIPT_MAP_CALLBACK_REMAINING_GAP, report["missing_evidence"])
                if report["script_map_content_materializers"]["callback_script_entry_corpus_ready"]:
                    self.assertIn(SCRIPT_MAP_CALLBACK_CORPUS_EVIDENCE_ID, report["closed_evidence_ids"])
                    self.assertNotIn(SCRIPT_MAP_CALLBACK_CORPUS_REMAINING_GAP, row["missing_evidence"])
                    self.assertNotIn(SCRIPT_MAP_CALLBACK_CORPUS_REMAINING_GAP, report["missing_evidence"])
                else:
                    self.assertIn(SCRIPT_MAP_CALLBACK_CORPUS_REMAINING_GAP, row["missing_evidence"])
                    self.assertIn(SCRIPT_MAP_CALLBACK_CORPUS_REMAINING_GAP, report["missing_evidence"])
            else:
                self.assertIn(SCRIPT_MAP_CALLBACK_REMAINING_GAP, row["missing_evidence"])
            if report["script_map_content_materializers"]["warp_object_position_materializers_ready"]:
                self.assertIn(SCRIPT_WARP_OBJECT_POSITION_EVIDENCE_ID, report["closed_evidence_ids"])
                self.assertNotIn(SCRIPT_WARP_OBJECT_COLLISION_REMAINING_GAP, report["missing_evidence"])
                if report["script_map_content_runtime_replays"]["ready"]:
                    self.assertIn(SCRIPT_WARP_OBJECT_COLLISION_RUNTIME_EVIDENCE_ID, report["closed_evidence_ids"])
                    self.assertNotIn(SCRIPT_WARP_OBJECT_COLLISION_RUNTIME_REMAINING_GAP, row["missing_evidence"])
                    self.assertNotIn(SCRIPT_WARP_OBJECT_COLLISION_RUNTIME_REMAINING_GAP, report["missing_evidence"])
                else:
                    self.assertIn(SCRIPT_WARP_OBJECT_COLLISION_RUNTIME_REMAINING_GAP, row["missing_evidence"])
                    self.assertIn(SCRIPT_WARP_OBJECT_COLLISION_RUNTIME_REMAINING_GAP, report["missing_evidence"])
                if report["script_map_content_materializers"]["object_struct_visibility_materializers_ready"]:
                    self.assertIn(SCRIPT_OBJECT_STRUCT_VISIBILITY_EVIDENCE_ID, report["closed_evidence_ids"])
                    self.assertNotIn(SCRIPT_OBJECT_STRUCT_VISIBILITY_REMAINING_GAP, row["missing_evidence"])
                    self.assertNotIn(SCRIPT_OBJECT_STRUCT_VISIBILITY_REMAINING_GAP, report["missing_evidence"])
                else:
                    self.assertIn(SCRIPT_OBJECT_STRUCT_VISIBILITY_REMAINING_GAP, row["missing_evidence"])
                    self.assertIn(SCRIPT_OBJECT_STRUCT_VISIBILITY_REMAINING_GAP, report["missing_evidence"])
            else:
                self.assertIn(SCRIPT_WARP_OBJECT_COLLISION_REMAINING_GAP, row["missing_evidence"])
        else:
            self.assertIn(SCRIPT_MAP_CALLBACK_MATERIALIZER_GAP, row["missing_evidence"])
            self.assertIn(SCRIPT_WARP_OBJECT_COLLISION_REPLAY_GAP, row["missing_evidence"])

    def test_script_vm_event_log_status_requires_frame_sample_runtime_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "audit" / "debugger_literal_anything"
            out_dir.mkdir(parents=True)
            event = runtime_event_envelope(
                event_kind="script_vm",
                source_kind="script_vm_stream",
                source_report="script_probe.json",
                proof_status="runtime_observed",
                observation_type="frame_sample",
                payload={"script_bank": 0x60, "script_pos": 0x4038},
            )
            (out_dir / "script_vm_event_log.json").write_text(
                json.dumps(
                    {
                        "kind": "debugger_deity_surface_replay",
                        "surface": "script",
                        "valid": True,
                        "static_mirror": {"command_count": 1},
                        "runtime_replay": {
                            "distinct_script_pos_count": 1,
                            "runtime_events": [event],
                        },
                    }
                ),
                encoding="utf-8",
            )

            status = script_vm_event_log_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["event_count"], 1)

    def test_script_vm_event_log_status_fails_closed_without_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "audit" / "debugger_literal_anything"
            out_dir.mkdir(parents=True)
            (out_dir / "script_vm_event_log.json").write_text(
                json.dumps(
                    {
                        "kind": "debugger_deity_surface_replay",
                        "surface": "script",
                        "valid": True,
                        "static_mirror": {"command_count": 1},
                        "runtime_replay": {
                            "distinct_script_pos_count": 1,
                            "runtime_events": [],
                        },
                    }
                ),
                encoding="utf-8",
            )

            status = script_vm_event_log_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("no script VM runtime_event_envelope events", status["errors"])

    def test_graphics_digest_artifact_closes_only_digest_gap(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["graphics_ui"]
        if report["graphics_digest_parity"]["ready"]:
            self.assertNotIn("vram_oam_framebuffer_digest_parity", row["missing_evidence"])
            self.assertIn(GRAPHICS_DIGEST_EVIDENCE_ID, report["closed_evidence_ids"])
            if report["graphics_backend_labels"]["ready"]:
                self.assertNotIn("timing_sensitive_backend_labels", row["missing_evidence"])
                self.assertIn(GRAPHICS_BACKEND_LABEL_EVIDENCE_ID, report["closed_evidence_ids"])
            else:
                self.assertIn("timing_sensitive_backend_labels", row["missing_evidence"])
        else:
            self.assertIn("vram_oam_framebuffer_digest_parity", row["missing_evidence"])

    def test_graphics_backend_label_closes_only_timing_label_gap(self) -> None:
        report = build_literal_anything_report(read_only=True)
        rows = {row["surface_id"]: row for row in report["surfaces"]}
        row = rows["graphics_ui"]
        if report["graphics_backend_labels"]["ready"]:
            self.assertNotIn("timing_sensitive_backend_labels", row["missing_evidence"])
            self.assertIn(GRAPHICS_BACKEND_LABEL_EVIDENCE_ID, report["closed_evidence_ids"])
            if report["audio_apu_event_envelope"]["ready"]:
                self.assertNotIn(AUDIO_REMAINING_CRY_MUSIC_SFX_PARITY_GAP, report["missing_evidence"])
            else:
                self.assertIn(AUDIO_CRY_MUSIC_SFX_BACKEND_PARITY_GAP, report["missing_evidence"])
        else:
            self.assertIn("timing_sensitive_backend_labels", row["missing_evidence"])

    def test_graphics_backend_label_status_accepts_missing_cross_backend_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "audit" / "debugger_literal_anything"
            out_dir.mkdir(parents=True)
            (out_dir / "graphics_crossemu_backend_preflight.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_crossemu_preflight",
                        "valid": True,
                        "requested_backends": ["pyboy", "vba-m", "sameboy", "gambatte"],
                        "available_count": 1,
                        "cross_backend_available_count": 0,
                        "trusted_cross_backend_count": 0,
                        "ready_for_pyboy_run": True,
                        "ready_for_cross_backend_diff": False,
                        "blocking_reasons": ["no cross-emulator backend is installed"],
                        "backends": [
                            {"name": "pyboy", "available": True},
                            {"name": "vba-m", "available": False},
                            {"name": "sameboy", "available": False},
                            {"name": "gambatte", "available": False},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            status = graphics_backend_label_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["cross_backend_available_count"], 0)
        self.assertFalse(status["ready_for_cross_backend_diff"])

    def test_graphics_backend_label_status_fails_closed_if_it_should_run_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "audit" / "debugger_literal_anything"
            out_dir.mkdir(parents=True)
            (out_dir / "graphics_crossemu_backend_preflight.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_crossemu_preflight",
                        "valid": True,
                        "requested_backends": ["pyboy", "sameboy"],
                        "available_count": 2,
                        "cross_backend_available_count": 1,
                        "trusted_cross_backend_count": 1,
                        "ready_for_pyboy_run": True,
                        "ready_for_cross_backend_diff": True,
                        "blocking_reasons": [],
                        "backends": [
                            {"name": "pyboy", "available": True},
                            {"name": "sameboy", "available": True},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            status = graphics_backend_label_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("backend label artifact must not stand in for cross-backend parity", status["errors"])

    def test_graphics_backend_label_status_fails_closed_when_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "audit" / "debugger_literal_anything"
            out_dir.mkdir(parents=True)
            artifact = out_dir / "graphics_crossemu_backend_preflight.json"
            artifact.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_crossemu_preflight",
                        "valid": True,
                        "requested_backends": ["pyboy", "sameboy"],
                        "available_count": 1,
                        "cross_backend_available_count": 0,
                        "trusted_cross_backend_count": 0,
                        "ready_for_pyboy_run": True,
                        "ready_for_cross_backend_diff": False,
                        "blocking_reasons": ["no cross-emulator backend is installed"],
                        "backends": [
                            {"name": "pyboy", "available": True},
                            {"name": "sameboy", "available": False},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            source_path = root / "tools" / "debugger" / "crossemu.py"
            source_path.parent.mkdir(parents=True)
            source_path.write_text("# newer backend proof input\n", encoding="utf-8")
            os.utime(artifact, (100, 100))
            os.utime(source_path, (200, 200))

            status = graphics_backend_label_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("graphics backend label artifact is older than backend proof inputs", status["errors"])

    def test_graphics_digest_status_requires_framebuffer_vram_oam_and_lcd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "audit" / "debugger_literal_anything"
            out_dir.mkdir(parents=True)
            (out_dir / "graphics_vram_oam_framebuffer_digest_parity.json").write_text(
                json.dumps(
                    {
                        "kind": "debugger_deity_surface_replay",
                        "surface": "graphics",
                        "valid": True,
                        "replay_diff": {
                            "status": "captured_framebuffer_vram_oam",
                            "framebuffer": "sha256:frame",
                            "vram0_sha256": "vram0",
                            "vram1_sha256": "vram1",
                            "oam_sha256": "oam",
                            "lcd_state": {"lcd_enabled": True},
                        },
                        "runtime_replay": {
                            "kind": "unified_debugger_visual_snapshot",
                            "proof_status": "runtime_observed",
                            "hardware_behavior_proven": False,
                            "screen_frame": {"sha256": "frame"},
                            "surfaces": [
                                {"name": "VRAM0", "sha256": "vram0"},
                                {"name": "VRAM1", "sha256": "vram1"},
                                {"name": "OAM", "sha256": "oam"},
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )

            status = graphics_digest_parity_status(root=root)

        self.assertTrue(status["ready"])
        self.assertEqual(status["framebuffer"], "sha256:frame")

    def test_graphics_digest_status_fails_closed_without_oam_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "audit" / "debugger_literal_anything"
            out_dir.mkdir(parents=True)
            (out_dir / "graphics_vram_oam_framebuffer_digest_parity.json").write_text(
                json.dumps(
                    {
                        "kind": "debugger_deity_surface_replay",
                        "surface": "graphics",
                        "valid": True,
                        "replay_diff": {
                            "status": "captured_framebuffer_vram_oam",
                            "framebuffer": "sha256:frame",
                            "vram0_sha256": "vram0",
                            "vram1_sha256": "vram1",
                            "lcd_state": {"lcd_enabled": True},
                        },
                        "runtime_replay": {
                            "kind": "unified_debugger_visual_snapshot",
                            "proof_status": "runtime_observed",
                            "hardware_behavior_proven": False,
                            "screen_frame": {"sha256": "frame"},
                            "surfaces": [
                                {"name": "VRAM0", "sha256": "vram0"},
                                {"name": "VRAM1", "sha256": "vram1"},
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )

            status = graphics_digest_parity_status(root=root)

        self.assertFalse(status["ready"])
        self.assertIn("missing oam_sha256", status["errors"])
        self.assertIn("missing OAM runtime surface digest", status["errors"])

    def test_rom_index_artifacts_fail_closed_when_input_hashes_are_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "audit" / "debugger_literal_anything"
            out_dir.mkdir(parents=True)
            (root / "pokegold.gbc").write_bytes(b"rom")
            (root / "pokegold.sym").write_text("00:0100 Start\n", encoding="utf-8")
            (root / "pokegold.map").write_text("map\n", encoding="utf-8")
            stale_hashes = {
                "rom_sha256": "STALE",
                "symbols_sha256": "STALE",
                "map_sha256": "STALE",
            }
            (out_dir / "rom_surface_index.jsonl").write_text(
                json.dumps(
                    {
                        "kind": "rom_surface_index_row",
                        "surface_id": "surface:unit",
                        "input_hashes": stale_hashes,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (out_dir / "rom_byte_index.jsonl").write_text(
                json.dumps(
                    {
                        "kind": "rom_byte_index_row",
                        "row_id": "span:unit",
                        "confidence": "content_mirror_exact_span",
                        "input_hashes": stale_hashes,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (out_dir / "rom_index_report.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_rom_index",
                        "input_hashes": stale_hashes,
                    }
                ),
                encoding="utf-8",
            )

            status = rom_index_artifact_status(root=root)

        self.assertFalse(status["ready"])
        self.assertEqual(status["stale_artifact_count"], 3)
        self.assertEqual(status["surface_index"]["input_hash_mismatch_count"], 1)
        self.assertEqual(status["byte_index"]["input_hash_mismatch_count"], 1)
        self.assertEqual(status["report"]["input_hash_mismatch_count"], 1)
        self.assertIn("--json-out audit\\debugger_literal_anything\\rom_index_report.json", status["next_command"])

    def test_rom_index_report_staleness_fails_closed_when_jsonl_rows_are_fresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "audit" / "debugger_literal_anything"
            out_dir.mkdir(parents=True)
            (root / "pokegold.gbc").write_bytes(b"rom")
            (root / "pokegold.sym").write_text("00:0100 Start\n", encoding="utf-8")
            (root / "pokegold.map").write_text("map\n", encoding="utf-8")
            fresh_hashes = rom_index_input_hashes(root=root)
            stale_hashes = {
                "rom_sha256": "STALE",
                "symbols_sha256": "STALE",
                "map_sha256": "STALE",
            }
            (out_dir / "rom_surface_index.jsonl").write_text(
                json.dumps(
                    {
                        "kind": "rom_surface_index_row",
                        "surface_id": "surface:unit",
                        "input_hashes": fresh_hashes,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (out_dir / "rom_byte_index.jsonl").write_text(
                json.dumps(
                    {
                        "kind": "rom_byte_index_row",
                        "row_id": "span:unit",
                        "confidence": "content_mirror_exact_span",
                        "input_hashes": fresh_hashes,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (out_dir / "rom_index_report.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_rom_index",
                        "input_hashes": stale_hashes,
                    }
                ),
                encoding="utf-8",
            )

            status = rom_index_artifact_status(root=root)

        self.assertFalse(status["ready"])
        self.assertEqual(status["stale_artifact_count"], 1)
        self.assertEqual(status["surface_index"]["stale_row_count"], 0)
        self.assertEqual(status["byte_index"]["stale_row_count"], 0)
        self.assertEqual(status["report"]["input_hash_mismatch_count"], 1)


if __name__ == "__main__":
    unittest.main()
