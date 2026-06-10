#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.debugger.catalog import build_capability_report
from tools.debugger.command_metadata import taxonomy_summary
from tools.debugger.report_envelope import build_report_envelope, sha256_file


BASELINE_DIR = ROOT / "audit" / "debugger_literal_anything"
DEFAULT_OUT = ROOT / ".local" / "tmp" / "debugger_literal_anything" / "baseline.json"
CANONICAL_STATE_CLASS_SELECTED_ADOPTION_EVIDENCE_ID = (
    "canonical_state_class.core_schema_boss_headless_adoption.validated"
)
CANONICAL_STATE_CLASS_CONTENT_STATE_MATERIALIZER_EVIDENCE_ID = (
    "canonical_state_class.content_state_selected_materializers.validated"
)
CANONICAL_STATE_CLASS_DAMAGE_MUTATION_EVIDENCE_ID = (
    "canonical_state_class.damage_mutation_campaign_cases.validated"
)
CANONICAL_STATE_CLASS_GLOBAL_GAP = "canonical state-class schema is not shared across all proof surfaces"
CANONICAL_STATE_CLASS_REMAINING_ADOPTION_GAP = "remaining_canonical_state_class_surface_adoptions"
HEADLESS_TURN_CLASS_EVIDENCE_ID = "headless_battle_turn_level_class_ids.validated"
HEADLESS_SPIKES_HAZARD_EVIDENCE_ID = "headless_battle_selected_spikes_hazard_rom_smoke.passed"
HEADLESS_COMPONENT_ROM_DIFFERENTIAL_EVIDENCE_ID = "headless_battle_component_rom_differentials.passed"
HEADLESS_PROMOTED_TURN_WORKLIST_EVIDENCE_ID = (
    "headless_battle_promoted_turn_differential_worklist.cataloged"
)
HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP = "rom_differentials_for_promoted_mechanics"
HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP = "remaining_promoted_mechanic_turn_differentials"
BOSS_AI_GOD_REQUIRED_EVIDENCE_IDS = (
    "boss_ai_god_gate.schema_checked",
    "boss_ai_changed_ai_run_metadata.reported",
    "boss_ai_pre_choice_replay.exact_match_corpus",
    "boss_ai_changed_ai_score_materialization.full_candidate_corpus",
    "boss_ai_changed_ai_contribution_comparison.generated_trace_ids_matched",
    "boss_ai_changed_ai_contribution_refresh.full_route_corpus",
    "boss_ai_universe_reachable_labels_classified.validated",
    "boss_ai_rule_target_materialization_paths.available",
    "boss_ai_rule_target_canonical_class_ids.validated",
    "boss_ai_exhaustive_witness_class_catalog.cataloged",
)
READ_ONLY_REFUSAL_EVIDENCE_ID = "read_only_command_refusal.enforced"
AFTER_HIT_ORDER_SCENARIO = "afterhit_rocky_helmet_before_shell_bell"
AFTER_HIT_ORDER_EVIDENCE_ID = "after_hit_item_order_rom_goldens.passed"
DAMAGE_MODIFIER_RECOIL_EVIDENCE_ID = "damage_debugger_selected_modifier_recoil_rom_smoke.passed"
DAMAGE_FUZZ_NO_DIVERGENCE_EVIDENCE_ID = "damage_debugger_fuzz_no_divergence.passed"
DAMAGE_MUTATION_CAMPAIGN_EVIDENCE_ID = "damage_debugger_phase6_initial_mutation_campaign.passed"
DAMAGE_MUTATION_RNG_DISTRIBUTION_EVIDENCE_ID = (
    "damage_debugger_phase6_rng_distribution_mutation_campaign.passed"
)
DAMAGE_MUTATION_SPECIES_WIDE_EVIOLITE_EVIDENCE_ID = (
    "damage_debugger_phase6_species_wide_eviolite_fuzz.passed"
)
DAMAGE_MUTATION_AUTO_MINIMIZED_DIVERGENCE_EVIDENCE_ID = (
    "damage_debugger_auto_minimized_divergence_artifacts.passed"
)
DAMAGE_MUTATION_SELECTED_STATUS_SIDE_EFFECTS_EVIDENCE_ID = (
    "damage_debugger_selected_status_side_effects_rom_components.passed"
)
DAMAGE_MUTATION_CAMPAIGN_EVIDENCE_IDS = {
    "oracle_assumptions": "damage_debugger_phase6_oracle_assumptions_mutation_campaign.passed",
    "damage_variation_and_type_matchup": "damage_debugger_phase6_damage_variation_type_matchup_mutation_campaign.passed",
    "status_item_interactions": "damage_debugger_phase6_status_item_interactions_mutation_campaign.passed",
    "after_hit_order": "damage_debugger_phase6_after_hit_order_mutation_campaign.passed",
    "recoil": "damage_debugger_phase6_recoil_mutation_campaign.passed",
    "replay_watchpoints": "damage_debugger_phase6_replay_watchpoints_mutation_campaign.passed",
}
DAMAGE_FUZZ_MIN_EXAMPLES = 100
DAMAGE_MUTATION_MIN_CASES = 18
AUDIO_APU_EVENT_EVIDENCE_ID = "audio_apu_event_stream.runtime_event_envelope"
AUDIO_TYPHLOSION_CRY_MATCH_EVIDENCE_ID = "audio_typhlosion_cry_static_runtime_apu_match.validated"
AUDIO_CRY_MUSIC_SFX_BACKEND_PARITY_GAP = "cry_music_sfx_backend_parity"
AUDIO_REMAINING_CRY_MUSIC_SFX_PARITY_GAP = "remaining_cry_music_sfx_cross_backend_parity"
SCRIPT_VM_EVENT_EVIDENCE_ID = "script_vm_event_log.runtime_event_envelope"
GRAPHICS_DIGEST_EVIDENCE_ID = "graphics_vram_oam_framebuffer_digest.captured"
GRAPHICS_BACKEND_LABEL_EVIDENCE_ID = "graphics_timing_sensitive_backend_labels.recorded"
SAVE_FORMAT_SRAM_BANK_EVIDENCE_ID = "save_format_sram_bank_ownership.validated"
RTC_SOURCE_ANCHOR_EVIDENCE_ID = "save_rtc_mbc.rtc_edge_case_source_anchors.indexed"
RTC_REGISTER_EDGE_RUNTIME_REPLAY_EVIDENCE_ID = (
    "save_rtc_mbc.rtc_carry_day_overflow_register_runtime_replay"
)
RTC_HALT_BIT_NEGATIVE_CONTROL_EVIDENCE_ID = (
    "save_rtc_mbc.rtc_halt_bit_readback_negative_control.observed"
)
MBC_BANK_TRANSITION_MODEL_EVIDENCE_ID = "save_rtc_mbc.mbc_bank_transition_model.validated"
MBC_RUNTIME_TRANSITION_REPLAY_EVIDENCE_ID = "save_rtc_mbc.mbc_runtime_transition_replay_corpus"
RTC_EDGE_CASE_REPLAY_GAP = "rtc_edge_case_replay"
RTC_RUNTIME_REPLAY_GAP = "rtc_halt_carry_day_overflow_runtime_replays"
RTC_HALT_SEMANTICS_RUNTIME_GAP = "rtc_halt_semantics_runtime_replay"
RTC_REMAINING_HALT_FREEZE_SEMANTICS_RUNTIME_GAP = (
    "remaining_rtc_halt_freeze_semantics_runtime_replay"
)
MBC_STATE_TRANSITION_GAP = "mbc_state_transitions"
MBC_RUNTIME_TRANSITION_REPLAY_GAP = "mbc_runtime_transition_replay_corpus"
DAMAGE_EXPANDED_MUTATION_CAMPAIGNS_GAP = "expanded_mutation_campaigns"
DAMAGE_REMAINING_EXPANDED_MUTATION_CAMPAIGNS_GAP = "remaining_expanded_damage_mutation_campaigns"
DAMAGE_REMAINING_RNG_DISTRIBUTION_CAMPAIGN_GAP = "remaining_damage_mutation_rng_distribution"
DAMAGE_REMAINING_SPECIES_WIDE_EVIOLITE_CAMPAIGN_GAP = "remaining_damage_mutation_species_wide_eviolite_fuzz"
DAMAGE_REMAINING_FULL_BATTLE_STATUS_SIDE_EFFECT_CAMPAIGN_GAP = (
    "remaining_damage_mutation_full_battle_status_side_effects"
)
DAMAGE_REMAINING_AUTO_MINIMIZED_DIVERGENCE_ARTIFACTS_GAP = (
    "remaining_damage_mutation_auto_minimized_divergence_artifacts"
)
DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS = (
    DAMAGE_REMAINING_RNG_DISTRIBUTION_CAMPAIGN_GAP,
    DAMAGE_REMAINING_SPECIES_WIDE_EVIOLITE_CAMPAIGN_GAP,
    DAMAGE_REMAINING_FULL_BATTLE_STATUS_SIDE_EFFECT_CAMPAIGN_GAP,
    DAMAGE_REMAINING_AUTO_MINIMIZED_DIVERGENCE_ARTIFACTS_GAP,
)
HARDWARE_INTERRUPT_MODEL_EVIDENCE_ID = "interrupts_dma_timers_lcd.interrupt_entry_ime_model.validated"
HARDWARE_INTERRUPT_RUNTIME_EVENT_EVIDENCE_ID = (
    "interrupts_dma_timers_lcd.interrupt_entry_exit_runtime_event_stream"
)
HARDWARE_DMA_MODEL_EVIDENCE_ID = "interrupts_dma_timers_lcd.dma_oam_vram_transfer_models.validated"
HARDWARE_DMA_RUNTIME_EVENT_EVIDENCE_ID = "interrupts_dma_timers_lcd.dma_oam_vram_runtime_event_stream"
HARDWARE_TIMER_LCD_MODEL_EVIDENCE_ID = "interrupts_dma_timers_lcd.timer_ppu_io_overflow_models.validated"
HARDWARE_TIMER_LCD_RUNTIME_EVENT_EVIDENCE_ID = (
    "interrupts_dma_timers_lcd.timer_lcd_mode_runtime_event_stream"
)
INTERRUPT_ENTRY_EXIT_EVENTS_GAP = "interrupt_entry_exit_events"
INTERRUPT_ENTRY_EXIT_RUNTIME_EVENT_STREAM_GAP = "interrupt_entry_exit_runtime_event_stream"
DMA_OAM_VRAM_EVENTS_GAP = "dma_oam_vram_events"
DMA_OAM_VRAM_RUNTIME_EVENT_STREAM_GAP = "dma_oam_vram_runtime_event_stream"
TIMER_LCD_MODE_EVENTS_GAP = "timer_lcd_mode_events"
TIMER_LCD_MODE_RUNTIME_EVENT_STREAM_GAP = "timer_lcd_mode_runtime_event_stream"
SERIAL_REGISTER_WRITE_MODEL_EVIDENCE_ID = "link_serial_mystery_gift.serial_register_write_model.validated"
SERIAL_TRANSFER_RUNTIME_EVENT_EVIDENCE_ID = (
    "link_serial_mystery_gift.pyboy_internal_clock_serial_transfer_runtime_event_stream"
)
LINK_BOUNDARY_SOURCE_ANCHOR_EVIDENCE_ID = "link_serial_mystery_gift.link_boundary_source_anchors.indexed"
LINK_BOUNDARY_RUNTIME_STATE_CLASS_CORPUS_EVIDENCE_ID = (
    "link_serial_mystery_gift.link_boundary_runtime_state_class_corpus.unsupported_classes_indexed"
)
SERIAL_EVENT_STREAM_GAP = "serial_event_stream"
SERIAL_TRANSFER_RUNTIME_EVENT_STREAM_GAP = "serial_transfer_runtime_event_stream"
LINK_BOUNDARY_STATE_CLASSES_GAP = "link_boundary_state_classes"
LINK_BOUNDARY_RUNTIME_STATE_CLASS_CORPUS_GAP = "link_boundary_runtime_state_class_corpus"
SCRIPT_MAP_CONTENT_MATERIALIZER_EVIDENCE_ID = "script_map_content_selected_materializers.resolved"
SCRIPT_MAP_CALLBACK_SELECTED_EVIDENCE_ID = "script_map_content.azalea_callback_script_entry_materializer.resolved"
SCRIPT_MAP_CALLBACK_CORPUS_EVIDENCE_ID = (
    "script_map_content.script_entry_corpus_materializers.resolved"
)
SCRIPT_WARP_OBJECT_POSITION_EVIDENCE_ID = "script_map_content.azalea_warp_object_position_materializers.resolved"
SCRIPT_OBJECT_STRUCT_VISIBILITY_EVIDENCE_ID = (
    "script_map_content.object_struct_visibility_materializers.resolved"
)
SCRIPT_WARP_OBJECT_COLLISION_RUNTIME_EVIDENCE_ID = (
    "script_map_content.azalea_warp_object_collision_runtime_replays.observed"
)
SCRIPT_MAP_CALLBACK_MATERIALIZER_GAP = "map_callback_materializers"
SCRIPT_MAP_CALLBACK_REMAINING_GAP = "remaining_map_callback_materializers"
SCRIPT_MAP_CALLBACK_CORPUS_REMAINING_GAP = "remaining_map_callback_corpus_materializers"
SCRIPT_WARP_OBJECT_COLLISION_REPLAY_GAP = "warp_object_collision_replays"
SCRIPT_WARP_OBJECT_COLLISION_REMAINING_GAP = "remaining_warp_object_collision_replays"
SCRIPT_WARP_OBJECT_COLLISION_RUNTIME_REMAINING_GAP = "remaining_warp_object_collision_runtime_replays"
SCRIPT_OBJECT_STRUCT_VISIBILITY_REMAINING_GAP = "remaining_object_struct_visibility_materializers"
SCRIPT_MAP_CONTENT_MATERIALIZER_SCENARIOS = {
    "content_scenario_1_0000": ("map_warp", "map_position"),
    "content_scenario_1_0019": ("map_object_event", "map_position"),
    "content_scenario_1_0032": ("script_command_stream", "script_entry"),
}
RTC_SOURCE_ANCHOR_LABELS = {
    "home/time.asm": ("LatchClock", "GetClock", "FixDays", "SetClock"),
    "engine/rtc/rtc.asm": ("SaveRTC", "_GetClock", "_FixDays"),
}
LINK_BOUNDARY_SOURCE_ANCHOR_LABELS = {
    "home/serial.asm": (
        "Serial",
        "Serial_ExchangeBytes",
        "Serial_ExchangeByte",
        "WaitLinkTransfer",
        "LinkTransfer",
        "LinkDataReceived",
    ),
    "engine/link/link.asm": (
        "LinkCommunications",
        "WaitForLinkedFriend",
        "CheckLinkTimeout_Receptionist",
        "Link_CheckCommunicationError",
        "CheckBothSelectedSameRoom",
        "TimeCapsule",
    ),
    "maps/Pokecenter2F.asm": (
        "LinkReceptionistScript_Trade",
        "LinkReceptionistScript_Battle",
        "LinkReceptionistScript_TimeCapsule",
    ),
}
HEADLESS_SPIKES_HAZARD_CASES = (
    "gll-spikes-001-player-0-to-1",
    "gll-spikes-001-player-1-to-2",
    "gll-spikes-001-player-2-to-3",
    "gll-spikes-001-enemy-0-to-1",
    "gll-spikes-002-fourth-click-fails",
    "gll-spin-001-player-clears-one-layer",
    "gll-spin-001-player-clears-two-layers",
    "gll-spin-001-player-clears-three-layers",
    "gll-spin-001-enemy-clears-three-layers",
    "gll-spin-002-no-layers-control",
    "gll-spikes-003-one-layer-fraction",
    "gll-spikes-003-two-layer-fraction",
    "gll-spikes-003-three-layer-fraction",
    "gll-spikes-004-player-flying-type1",
    "gll-spikes-004-player-flying-type2",
    "gll-spikes-004-enemy-flying-type1",
    "gll-spikes-004-enemy-flying-type2",
)
HEADLESS_COMPONENT_ROM_DIFFERENTIALS = (
    "normal_hit_fixed_rng_differential",
    "normal_hit_low_variation_differential",
    "normal_hit_critical_differential",
    "normal_hit_accuracy_miss_differential",
    "damage_variation_component_differential",
    "critical_component_differential",
    "damaging_status_component_differential",
    "drain_component_differential",
    "item_restore_component_differential",
    "full_restore_status_cure_component_differential",
    "basic_pp_decrement_component_differential",
    "weather_setup_component_differential",
    "selected_substitute_move_turn_differential",
    "selected_self_heal_move_turn_differential",
    "supported_after_hit_item_effects_differential",
    "basic_status_residual_component_differential",
)
DAMAGE_MODIFIER_RECOIL_SCENARIOS = (
    "physical_type_boost_item",
    "physical_muscle_band",
    "special_wise_glasses",
    "special_expert_belt",
    "special_metronome_item",
    "special_life_orb_damage",
    "recoil_basic_no_steel",
    "recoil_ko_clamp",
)
DAMAGE_MUTATION_REQUIRED_CAMPAIGNS = (
    "oracle_assumptions",
    "damage_variation_and_type_matchup",
    "status_item_interactions",
    "after_hit_order",
    "recoil",
    "replay_watchpoints",
)
DAMAGE_MUTATION_REQUIRED_IDS = (
    "oracle_assumption_critical_flip",
    "oracle_assumption_initial_damage_cap_add",
    "oracle_assumption_truncate_high_stats",
    "damage_variation_sun_fire_stab",
    "damage_variation_rain_solarbeam",
    "damage_variation_immunity_zero_damage",
    "status_item_life_orb_special",
    "status_item_metronome_count",
    "status_item_wise_glasses_status_pressure",
    "status_item_assault_vest_defender",
    "status_item_type_boost_physical",
    "smoke_afterhit_rocky_helmet",
    "smoke_afterhit_shell_bell",
    "smoke_afterhit_rocky_helmet_before_shell_bell",
    "smoke_afterhit_life_orb",
    "smoke_special_super_effective_variation",
    "smoke_recoil_basic_no_steel",
    "smoke_recoil_ko_clamp",
    "replay_afterhit_rocky_helmet_before_shell_bell_wBattleMonHP",
    "replay_special_super_effective_variation_wCurDamage",
    "replay_recoil_basic_no_steel_wBattleMonHP",
)
DAMAGE_MUTATION_REQUIRED_IDS_BY_CAMPAIGN = {
    "oracle_assumptions": (
        "oracle_assumption_critical_flip",
        "oracle_assumption_initial_damage_cap_add",
        "oracle_assumption_truncate_high_stats",
    ),
    "damage_variation_and_type_matchup": (
        "damage_variation_sun_fire_stab",
        "damage_variation_rain_solarbeam",
        "damage_variation_immunity_zero_damage",
        "smoke_special_super_effective_variation",
    ),
    "status_item_interactions": (
        "status_item_life_orb_special",
        "status_item_metronome_count",
        "status_item_wise_glasses_status_pressure",
        "status_item_assault_vest_defender",
        "status_item_type_boost_physical",
    ),
    "after_hit_order": (
        "smoke_afterhit_rocky_helmet",
        "smoke_afterhit_shell_bell",
        "smoke_afterhit_rocky_helmet_before_shell_bell",
        "smoke_afterhit_life_orb",
    ),
    "recoil": (
        "smoke_recoil_basic_no_steel",
        "smoke_recoil_ko_clamp",
    ),
    "replay_watchpoints": (
        "replay_afterhit_rocky_helmet_before_shell_bell_wBattleMonHP",
        "replay_special_super_effective_variation_wCurDamage",
        "replay_recoil_basic_no_steel_wBattleMonHP",
    ),
}
DAMAGE_MUTATION_SELECTED_STATUS_SIDE_EFFECT_CASE_IDS = (
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


@dataclass(frozen=True)
class SurfaceRow:
    surface_id: str
    owner_lane: str
    reachable: bool
    proof_status: str
    proof_capability: str
    unsupported_reason: str
    missing_evidence: tuple[str, ...]
    backend: str
    next_command: str

    def to_jsonable(self) -> dict[str, Any]:
        return asdict(self)


SURFACE_ROWS = (
    SurfaceRow(
        "unified_debugger_front_door",
        "unified_debugger_architecture",
        True,
        "partial",
        "current command surfaces import and selftest; not a whole-ROM proof inventory",
        "",
        ("whole_rom_surface_inventory", "no_partial_pass_literal_anything_gate"),
        "static",
        "python tools\\audit\\check_debugger_literal_anything.py --baseline --read-only",
    ),
    SurfaceRow(
        "boss_ai_debugger",
        "boss_ai_proof",
        True,
        "partial",
        "God gate consumes a generated Boss AI universe; generated scenario and rule-target class ids exist, but live trace/contribution classes are not fully integrated",
        "",
        (
            "boss_ai_universe_not_complete",
            "boss_ai_live_trace_and_contribution_class_ids_not_integrated",
            "exhaustive_class_proofs",
        ),
        "pyboy",
        "python tools\\audit\\check_boss_ai_debugger_god.py --baseline --read-only",
    ),
    SurfaceRow(
        "headless_battle",
        "battle_damage_state_space",
        True,
        "partial",
        "selected mechanics have proof labels; full-battle automatic choices are out of scope",
        "",
        ("turn_level_class_ids", HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP),
        "static_plus_component_rom",
        "python tools\\audit\\check_headless_battle_simulator.py",
    ),
    SurfaceRow(
        "damage_debugger",
        "battle_damage_state_space",
        True,
        "partial",
        "damage oracle is strong for math core, not every after-hit side effect",
        "",
        ("after_hit_item_order_rom_goldens", DAMAGE_EXPANDED_MUTATION_CAMPAIGNS_GAP),
        "pyboy",
        (
            "python -m tools.damage_debugger.fuzz --max-examples=100 --workers=2 "
            "--json-out audit\\damage_debugger\\fuzz_no_divergence.json"
        ),
    ),
    SurfaceRow(
        "script_map_content",
        "source_rom_provenance",
        True,
        "static_mirror_only",
        "static mirrors exist for many content bytes, but arbitrary script VM behavior is not universally replayed",
        "",
        ("script_vm_event_log", SCRIPT_MAP_CALLBACK_MATERIALIZER_GAP, SCRIPT_WARP_OBJECT_COLLISION_REPLAY_GAP),
        "static",
        "python -m tools.debugger replay --surface script --at \"map=ELMS_LAB and script=ProfElmScript\" --frames 120 --json-out audit\\debugger_literal_anything\\script_vm_event_log.json",
    ),
    SurfaceRow(
        "graphics_ui",
        "runtime_trace",
        True,
        "emulator_evidence",
        "PyBoy-only visual evidence is not backend parity or hardware proof",
        "",
        ("vram_oam_framebuffer_digest_parity", "timing_sensitive_backend_labels"),
        "pyboy",
        "python -m tools.debugger replay --surface graphics --at \"map=ECRUTEAK_GYM\" --json-out audit\\debugger_literal_anything\\graphics_vram_oam_framebuffer_digest_parity.json",
    ),
    SurfaceRow(
        "audio",
        "runtime_trace",
        True,
        "emulator_evidence",
        "APU register timelines and backend parity are not complete",
        "",
        ("apu_register_event_stream", AUDIO_CRY_MUSIC_SFX_BACKEND_PARITY_GAP),
        "pyboy",
        "python -m tools.debugger replay --surface audio --at \"cry(species=TYPHLOSION)\" --frames 120 --json-out audit\\debugger_literal_anything\\audio_apu_event_envelope.json",
    ),
    SurfaceRow(
        "save_rtc_mbc",
        "save_rtc_mbc_state",
        True,
        "unsupported",
        "save schema audits exist, but universal RTC/MBC behavior proof is not implemented",
        "needs runtime proof corpus",
        ("sram_bank_ownership", RTC_EDGE_CASE_REPLAY_GAP, MBC_STATE_TRANSITION_GAP),
        "none",
        "python tools\\audit\\check_save_format_version.py",
    ),
    SurfaceRow(
        "interrupts_dma_timers_lcd",
        "runtime_trace",
        True,
        "unsupported",
        "interrupt, DMA, timer, LCD-mode, and serial boundaries lack a unified event stream",
        "needs hardware/backend event stream",
        (INTERRUPT_ENTRY_EXIT_EVENTS_GAP, DMA_OAM_VRAM_EVENTS_GAP, TIMER_LCD_MODE_EVENTS_GAP),
        "none",
        "python -m tools.debugger trace-instructions --symbol VBlank --frames 60",
    ),
    SurfaceRow(
        "link_serial_mystery_gift",
        "runtime_trace",
        True,
        "unsupported",
        "link/serial and Mystery Gift boundaries are not currently behavior-proved",
        "needs backend support",
        (SERIAL_EVENT_STREAM_GAP, LINK_BOUNDARY_STATE_CLASSES_GAP),
        "none",
        "python -m tools.debugger triage --symptom \"link serial mystery gift\"",
    ),
    SurfaceRow(
        "rom_byte_index",
        "source_rom_provenance",
        True,
        "partial",
        "rom-byte provides confidence-scored linker/symbol/source lookup for individual bytes, but normalized whole-ROM byte-span indexes are not generated yet",
        "",
        ("rom_surface_index_jsonl", "rom_byte_index_jsonl", "content_mirror_exact_span_rows"),
        "static",
        "python -m tools.debugger rom-byte --address 0E:542B",
    ),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def today_stamp() -> str:
    return datetime.now().date().isoformat()


def build_literal_anything_report(*, root: Path = ROOT, read_only: bool = False) -> dict[str, Any]:
    capability = build_capability_report(root=root)
    taxonomy = taxonomy_summary()
    rows = [row.to_jsonable() for row in SURFACE_ROWS]
    rom_index_artifacts = rom_index_artifact_status(root=root)
    content_mirror_artifact = content_mirror_span_artifact_status(root=root)
    boss_ai_class_adoption = boss_ai_raw_class_adoption_status()
    boss_ai_god_gate = boss_ai_god_gate_status(root=root)
    headless_battle_class_adoption = headless_battle_class_adoption_status()
    canonical_state_class_schema = canonical_state_class_schema_status()
    after_hit_item_order = after_hit_item_order_status(root=root)
    damage_modifier_recoil_smoke = damage_modifier_recoil_smoke_status(root=root)
    audio_apu_event_envelope = audio_apu_event_envelope_status(root=root)
    script_vm_event_log = script_vm_event_log_status(root=root)
    script_map_content_materializers = script_map_content_materializer_status(root=root)
    script_map_content_runtime_replays = script_map_content_runtime_replay_status(root=root)
    graphics_digest_parity = graphics_digest_parity_status(root=root)
    graphics_backend_labels = graphics_backend_label_status(root=root)
    save_format_sram_bank_ownership = save_format_sram_bank_ownership_status(root=root)
    rtc_edge_case_source_anchors = rtc_edge_case_source_anchor_status(root=root)
    rtc_register_edge_runtime_replay = rtc_register_edge_runtime_replay_status(root=root)
    mbc_bank_transition_model = mbc_bank_transition_model_status()
    mbc_runtime_transition_replay_corpus = mbc_runtime_transition_replay_corpus_status(root=root)
    interrupt_entry_ime_model = interrupt_entry_ime_model_status()
    interrupt_entry_exit_runtime_events = interrupt_entry_exit_runtime_event_stream_status(root=root)
    dma_oam_vram_transfer_models = dma_oam_vram_transfer_model_status()
    dma_oam_vram_runtime_events = dma_oam_vram_runtime_event_stream_status(root=root)
    timer_ppu_io_overflow_models = timer_ppu_io_overflow_model_status()
    timer_lcd_mode_runtime_events = timer_lcd_mode_runtime_event_stream_status(root=root)
    serial_register_write_model = serial_register_write_model_status()
    serial_transfer_runtime_events = serial_transfer_runtime_event_stream_status(root=root)
    link_boundary_source_anchors = link_boundary_source_anchor_status(root=root)
    link_boundary_runtime_state_class_corpus = link_boundary_runtime_state_class_corpus_status(root=root)
    damage_fuzz_no_divergence = damage_fuzz_no_divergence_status(root=root)
    damage_mutation_campaign = damage_mutation_campaign_status(root=root)
    headless_spikes_hazard_smoke = headless_spikes_hazard_smoke_status(root=root)
    headless_component_rom_differentials = headless_component_rom_differential_status(root=root)
    headless_promoted_turn_worklist = headless_promoted_turn_worklist_status(root=root)
    canonical_selected_adoption_ready = (
        canonical_state_class_schema["ready"]
        and boss_ai_class_adoption["ready"]
        and headless_battle_class_adoption["ready"]
    )
    canonical_state_class_schema["selected_surface_adoptions"] = {
        "boss_ai": bool(boss_ai_class_adoption["ready"]),
        "headless_battle": bool(headless_battle_class_adoption["ready"]),
        "content_state_materializers": bool(
            script_map_content_materializers.get("canonical_state_class_materializers_ready", False)
        ),
        "damage_mutation_campaign": bool(
            damage_mutation_campaign.get("canonical_state_class_cases_ready", False)
        ),
    }
    canonical_state_class_schema["selected_surface_adoption_ready"] = canonical_selected_adoption_ready
    if rom_index_artifacts["ready"]:
        for row in rows:
            if row["surface_id"] != "unified_debugger_front_door":
                continue
            row["proof_capability"] = (
                "current command surfaces import and selftest; generated ROM surface/byte "
                "indexes exist, but whole-ROM ownership and proofs are still incomplete"
            )
            row["missing_evidence"] = [
                item
                for item in row["missing_evidence"]
                if item != "whole_rom_surface_inventory"
            ]
        for row in rows:
            if row["surface_id"] != "rom_byte_index":
                continue
            row["proof_capability"] = (
                "rom-index emits JSONL linker/symbol span indexes and rom-byte provides point lookup; "
                "content-mirror exact spans still need normalization"
            )
            row["missing_evidence"] = [
                item
                for item in row["missing_evidence"]
                if item not in {"rom_surface_index_jsonl", "rom_byte_index_jsonl"}
            ]
    if content_mirror_artifact["ready"]:
        for row in rows:
            if row["surface_id"] != "rom_byte_index":
                continue
            row["proof_capability"] = (
                "rom-index emits JSONL linker/symbol span indexes and rom-byte provides point lookup; "
                "content-mirror exact spans are reported for the generated mirror corpus"
            )
            row["missing_evidence"] = [
                item
                for item in row["missing_evidence"]
                if item != "content_mirror_exact_span_rows"
            ]
    if boss_ai_class_adoption["ready"]:
        for row in rows:
            if row["surface_id"] != "boss_ai_debugger":
                continue
            row["proof_capability"] = (
                "God gate consumes a generated Boss AI universe; supported generated, live-trace, "
                "materializer, and contribution trace surfaces carry class ids, but the universe "
                "and exhaustive proofs are still incomplete"
            )
            row["missing_evidence"] = [
                item
                for item in row["missing_evidence"]
                if item != "boss_ai_live_trace_and_contribution_class_ids_not_integrated"
            ]
    if boss_ai_god_gate.get("bridge_valid") and not boss_ai_god_gate["ready"]:
        for row in rows:
            if row["surface_id"] != "boss_ai_debugger":
                continue
            current_gaps = set(boss_ai_god_gate.get("blocking_gaps", []))
            missing_evidence: list[str] = []
            if "boss_ai_universe_not_complete" in current_gaps:
                missing_evidence.append("boss_ai_universe_not_complete")
            if "boss_ai_exhaustive_class_witness_roles_missing" in current_gaps:
                missing_evidence.append("exhaustive_class_proofs")
            for gap in sorted(current_gaps):
                if gap in {"boss_ai_universe_not_complete", "boss_ai_exhaustive_class_witness_roles_missing"}:
                    continue
                missing_evidence.append(gap)
            row["missing_evidence"] = missing_evidence
            row["next_command"] = "python tools\\audit\\check_boss_ai_debugger_god.py --read-only --json"
    if boss_ai_god_gate["ready"]:
        for row in rows:
            if row["surface_id"] != "boss_ai_debugger":
                continue
            row["proof_status"] = "runtime_proven"
            row["proof_capability"] = (
                "Current Boss AI God gate is complete: schema, changed-AI evidence, "
                "reachable-label classification, materialization paths, class ids, and "
                "exhaustive witness proofs are validated from the live gate report"
            )
            row["missing_evidence"] = []
            row["unsupported_reason"] = ""
            row["backend"] = "pyboy_plus_static"
            row["next_command"] = "python tools\\audit\\check_boss_ai_debugger_god.py --read-only --json"
    if headless_battle_class_adoption["ready"]:
        for row in rows:
            if row["surface_id"] != "headless_battle":
                continue
            row["proof_capability"] = (
                "selected mechanics have proof labels; exported switch-sack turn boards carry "
                "shared canonical class ids, but full-battle automatic choices and per-mechanic "
                "ROM differentials are still incomplete"
            )
            row["missing_evidence"] = [
                item
                for item in row["missing_evidence"]
                if item != "turn_level_class_ids"
            ]
    if headless_spikes_hazard_smoke["ready"]:
        for row in rows:
            if row["surface_id"] != "headless_battle":
                continue
            row["proof_capability"] = (
                "selected mechanics have proof labels; exported switch-sack turn boards carry "
                "shared canonical class ids, and Spikes/Rapid Spin layer, fraction, and "
                "Flying-immunity cases have a fresh ROM smoke log, but full-battle automatic choices and "
                "per-mechanic ROM differentials are still incomplete"
            )
    if headless_component_rom_differentials["ready"]:
        for row in rows:
            if row["surface_id"] != "headless_battle":
                continue
            row["proof_capability"] = (
                "selected mechanics have proof labels; exported switch-sack turn boards carry "
                "shared canonical class ids, Spikes/Rapid Spin hazard cases have a fresh ROM "
                "smoke log, and five component ROM differentials are persisted, but full-battle "
                "automatic choices and all promoted-mechanic turn differentials are still incomplete"
            )
            row["missing_evidence"] = [
                HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP
                if item == HEADLESS_PROMOTED_MECHANICS_DIFFERENTIAL_GAP
                else item
                for item in row["missing_evidence"]
            ]
    if headless_promoted_turn_worklist["ready"]:
        for row in rows:
            if row["surface_id"] != "headless_battle":
                continue
            row["proof_status"] = "runtime_proven"
            row["proof_capability"] = (
                "selected mechanics have proof labels; exported switch-sack turn boards carry "
                "shared canonical class ids, Spikes/Rapid Spin hazard cases have a fresh ROM "
                "smoke log, five component ROM differentials are persisted, and the remaining "
                "promoted-mechanic turn differential rows are cataloged with named unsupported "
                "scope; full-battle automatic choices remain outside this headless proof lane"
            )
            row["missing_evidence"] = [
                item
                for item in row["missing_evidence"]
                if item != HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP
            ]
            row["unsupported_reason"] = (
                "full-battle automatic choices and all promoted-mechanic turn differentials "
                "outside the component/selected-turn corpus are tracked as named unsupported scope"
            )
            row["backend"] = "static_plus_component_rom_with_named_limits"
    if after_hit_item_order["ready"]:
        for row in rows:
            if row["surface_id"] != "damage_debugger":
                continue
            row["proof_capability"] = (
                "damage oracle is strong for math core, and clobber_smoke ROM-proves "
                "Rocky Helmet before Shell Bell KO ordering; broader mutation campaigns "
                "are still incomplete"
            )
            row["missing_evidence"] = [
                item
                for item in row["missing_evidence"]
                if item != "after_hit_item_order_rom_goldens"
            ]
    if damage_modifier_recoil_smoke["ready"]:
        for row in rows:
            if row["surface_id"] != "damage_debugger":
                continue
            row["proof_capability"] = (
                "damage oracle is strong for math core, clobber_smoke ROM-proves "
                "Rocky Helmet before Shell Bell KO ordering when that log is fresh, and "
                "selected modifier/recoil cases have named ROM smoke rows; broader "
                "mutation campaigns are still incomplete"
            )
    if damage_fuzz_no_divergence["ready"]:
        for row in rows:
            if row["surface_id"] != "damage_debugger":
                continue
            selected_clause = (
                "selected modifier/recoil cases have named ROM smoke rows, "
                if damage_modifier_recoil_smoke["ready"]
                else ""
            )
            row["proof_capability"] = (
                "damage oracle is strong for math core, clobber_smoke ROM-proves "
                "Rocky Helmet before Shell Bell KO ordering when that log is fresh, "
                f"{selected_clause}and "
                "the damage fuzz no-divergence campaign has a persisted PASS artifact; "
                "broader mutation campaigns are still incomplete"
            )
    if damage_mutation_campaign["ready"]:
        for row in rows:
            if row["surface_id"] != "damage_debugger":
                continue
            if not row["missing_evidence"]:
                row["proof_status"] = "runtime_proven"
                row["backend"] = "pyboy_plus_rom_oracle"
            eviolite_clause = (
                "including species-wide Eviolite coverage"
                if damage_mutation_campaign["species_wide_eviolite_ready"]
                else "with species-wide Eviolite still incomplete"
            )
            selected_status_clause = (
                "selected damaging-status and Full Restore side-effect component differentials are embedded"
                if damage_mutation_campaign["selected_status_side_effects_ready"]
                else "full-battle status side effects are still incomplete"
            )
            auto_minimized_clause = (
                "auto-minimized divergence handoff is covered by a forced route proof"
                if damage_mutation_campaign["auto_minimized_divergence_ready"]
                else "auto-minimized divergence artifacts are still incomplete"
            )
            row["proof_capability"] = (
                "damage oracle is strong for math core, clobber_smoke ROM-proves "
                "Rocky Helmet before Shell Bell KO ordering when that log is fresh, "
                "selected modifier/recoil cases have named ROM smoke rows, the fuzz "
                "no-divergence campaign has a persisted PASS artifact when fresh, and "
                "the Phase 6 mutation campaign proves six sampled ROM-backed campaign "
                f"groups plus the DamageVariation RNG multiplier corpus when present, {eviolite_clause}; "
                f"{selected_status_clause}, and {auto_minimized_clause}"
            )
            missing_evidence: list[str] = []
            for item in row["missing_evidence"]:
                if item == DAMAGE_EXPANDED_MUTATION_CAMPAIGNS_GAP:
                    missing_evidence.extend(
                        damage_mutation_campaign.get(
                            "remaining_residual_gaps",
                            DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS,
                        )
                    )
                    continue
                missing_evidence.append(item)
            row["missing_evidence"] = missing_evidence
            if not row["missing_evidence"]:
                row["proof_status"] = "runtime_proven"
                row["backend"] = "pyboy_plus_rom_oracle"
    if audio_apu_event_envelope["ready"]:
        for row in rows:
            if row["surface_id"] != "audio":
                continue
            row["proof_status"] = "runtime_proven"
            row["proof_capability"] = (
                "APU register timelines are captured as runtime_event_envelope hardware "
                "events for the Typhlosion cry replay, and the source cry channels match "
                "the PyBoy runtime capture; cry/music/SFX cross-backend parity is a named "
                "unsupported local-backend limitation"
            )
            row["missing_evidence"] = [
                item
                for item in row["missing_evidence"]
                if item
                not in {
                    "apu_register_event_stream",
                    AUDIO_CRY_MUSIC_SFX_BACKEND_PARITY_GAP,
                    AUDIO_REMAINING_CRY_MUSIC_SFX_PARITY_GAP,
                }
            ]
            row["unsupported_reason"] = (
                "trusted cross-emulator audio backend parity is unavailable locally; "
                "the authoritative claim is PyBoy APU event-stream parity only"
            )
            row["backend"] = "pyboy_with_named_backend_limit"
    if script_vm_event_log["ready"]:
        for row in rows:
            if row["surface_id"] != "script_map_content":
                continue
            row["proof_capability"] = (
                "static mirrors exist for many content bytes, and a ProfElmScript replay "
                "captures script VM pointer/runtime samples as runtime_event_envelope rows; "
                "map callback materializers and warp/object collision replays are still incomplete"
            )
            row["missing_evidence"] = [
                item
                for item in row["missing_evidence"]
                if item != "script_vm_event_log"
            ]
    if script_map_content_materializers["ready"]:
        for row in rows:
            if row["surface_id"] != "script_map_content":
                continue
            callback_clause = (
                "the generated script-entry corpus materializes to concrete WRAM patches"
                if script_map_content_materializers["callback_script_entry_corpus_ready"]
                else "selected Azalea Town callback script-entry materializers resolve to concrete WRAM patches"
            )
            object_visibility_clause = (
                "derived object-struct visibility materializers resolve to concrete WRAM patches"
                if script_map_content_materializers["object_struct_visibility_materializers_ready"]
                else "derived object-struct visibility materializers are still incomplete"
            )
            row["proof_capability"] = (
                "static mirrors exist for many content bytes, a ProfElmScript replay captures "
                "script VM pointer/runtime samples as runtime_event_envelope rows, selected "
                "Azalea Town warp/object position materializers resolve to concrete WRAM patches, and "
                f"{callback_clause}; {object_visibility_clause}, and runtime warp/object "
                "collision replays are still incomplete"
            )
            missing_evidence: list[str] = []
            for item in row["missing_evidence"]:
                if item == SCRIPT_MAP_CALLBACK_MATERIALIZER_GAP:
                    if script_map_content_materializers["callback_script_entry_corpus_ready"]:
                        continue
                    if script_map_content_materializers["callback_script_entry_materializer_ready"]:
                        missing_evidence.append(SCRIPT_MAP_CALLBACK_CORPUS_REMAINING_GAP)
                    else:
                        missing_evidence.append(SCRIPT_MAP_CALLBACK_REMAINING_GAP)
                    continue
                if item == SCRIPT_WARP_OBJECT_COLLISION_REPLAY_GAP:
                    if script_map_content_materializers["warp_object_position_materializers_ready"]:
                        if not script_map_content_runtime_replays["ready"]:
                            missing_evidence.append(SCRIPT_WARP_OBJECT_COLLISION_RUNTIME_REMAINING_GAP)
                        if not script_map_content_materializers["object_struct_visibility_materializers_ready"]:
                            missing_evidence.append(SCRIPT_OBJECT_STRUCT_VISIBILITY_REMAINING_GAP)
                    else:
                        missing_evidence.append(SCRIPT_WARP_OBJECT_COLLISION_REMAINING_GAP)
                    continue
                missing_evidence.append(item)
            row["missing_evidence"] = missing_evidence
    if script_map_content_runtime_replays["ready"]:
        for row in rows:
            if row["surface_id"] != "script_map_content":
                continue
            row["proof_status"] = "runtime_proven"
            row["proof_capability"] = (
                "static mirrors exist for many content bytes, a ProfElmScript replay captures "
                "script VM pointer/runtime samples as runtime_event_envelope rows, selected "
                "Azalea Town callback and warp/object position materializers resolve to concrete "
                "WRAM patches, and selected Azalea warp/object helper replays observe runtime "
                "dispatch; full overworld button/input flow and all-map/all-object collision "
                "coverage are still outside this artifact"
            )
            row["missing_evidence"] = [
                item
                for item in row["missing_evidence"]
                if item != SCRIPT_WARP_OBJECT_COLLISION_RUNTIME_REMAINING_GAP
            ]
            row["backend"] = "pyboy_plus_static"
    if graphics_digest_parity["ready"]:
        for row in rows:
            if row["surface_id"] != "graphics_ui":
                continue
            row["proof_capability"] = (
                "PyBoy replay captures framebuffer, VRAM0, VRAM1, OAM, and LCD digests; "
                "timing-sensitive backend labels and cross-backend parity are still incomplete"
            )
            row["missing_evidence"] = [
                item
                for item in row["missing_evidence"]
                if item != "vram_oam_framebuffer_digest_parity"
            ]
            row["next_command"] = graphics_backend_labels["next_command"]
    if graphics_backend_labels["ready"]:
        for row in rows:
            if row["surface_id"] != "graphics_ui":
                continue
            row["proof_status"] = "runtime_proven"
            row["proof_capability"] = (
                "PyBoy replay captures framebuffer, VRAM0, VRAM1, OAM, and LCD digests, "
                "and crossemu preflight records that cross-backend timing parity is blocked "
                "by missing trusted emulator backends as a named local-backend limitation"
            )
            row["missing_evidence"] = [
                item
                for item in row["missing_evidence"]
                if item != "timing_sensitive_backend_labels"
            ]
            row["unsupported_reason"] = (
                "trusted cross-emulator graphics backend parity is unavailable locally; "
                "the authoritative claim is PyBoy framebuffer/VRAM/OAM/LCD digest capture only"
            )
            row["backend"] = "pyboy_with_named_backend_limit"
    if save_format_sram_bank_ownership["ready"]:
        for row in rows:
            if row["surface_id"] != "save_rtc_mbc":
                continue
            row["proof_status"] = "partial"
            row["proof_capability"] = (
                "save-format fingerprinting validates SAVE_FORMAT_VERSION against "
                "WRAM save ranges, SRAM section contents, and layout.link SRAM bank "
                "ownership; RTC edge-case replay and observed MBC state transitions "
                "are still incomplete"
            )
            row["unsupported_reason"] = "needs runtime proof corpus for RTC/MBC transitions"
            row["backend"] = "static"
            row["missing_evidence"] = [
                item
                for item in row["missing_evidence"]
                if item != "sram_bank_ownership"
            ]
    if rtc_edge_case_source_anchors["ready"]:
        for row in rows:
            if row["surface_id"] != "save_rtc_mbc":
                continue
            row["proof_capability"] = (
                "save-format fingerprinting validates SAVE_FORMAT_VERSION against "
                "WRAM save ranges, SRAM section contents, and layout.link SRAM bank "
                "ownership; RTC edge-case source anchors are indexed to current ROM "
                "surfaces, but halt/carry/day-overflow runtime replays and observed "
                "MBC state transitions are still incomplete"
            )
            row["missing_evidence"] = [
                RTC_RUNTIME_REPLAY_GAP if item == RTC_EDGE_CASE_REPLAY_GAP else item
                for item in row["missing_evidence"]
            ]
    if rtc_register_edge_runtime_replay["ready"]:
        for row in rows:
            if row["surface_id"] != "save_rtc_mbc":
                continue
            row["proof_capability"] = (
                "save-format fingerprinting validates SAVE_FORMAT_VERSION, RTC source anchors "
                "are indexed, selected PyBoy RTC carry/day-overflow register readback and "
                "halt-bit negative-control readback are captured, and MBC transition evidence "
                "is tracked separately; RTC halt freeze semantics remain unproven"
            )
            row["missing_evidence"] = [
                (
                    RTC_REMAINING_HALT_FREEZE_SEMANTICS_RUNTIME_GAP
                    if item == RTC_RUNTIME_REPLAY_GAP
                    else item
                )
                for item in row["missing_evidence"]
            ]
    if mbc_bank_transition_model["ready"]:
        for row in rows:
            if row["surface_id"] != "save_rtc_mbc":
                continue
            row["proof_capability"] = (
                (
                    "save-format fingerprinting validates SAVE_FORMAT_VERSION against "
                    "WRAM save ranges, SRAM section contents, and layout.link SRAM bank "
                    "ownership; RTC source anchors are indexed, the debugger models "
                    "RAM enable, ROM bank, SRAM/RTC select, and latch write ranges, "
                    "and selected PyBoy MBC3 runtime transitions are captured; "
                    + (
                        "selected PyBoy RTC carry/day-overflow register readback is captured, "
                        "the halt-bit negative-control readback is captured, but RTC halt "
                        "freeze semantics remain unproven"
                        if rtc_register_edge_runtime_replay["ready"]
                        else "RTC halt/carry/day-overflow runtime replays are still incomplete"
                    )
                )
                if mbc_runtime_transition_replay_corpus["ready"]
                else (
                    "save-format fingerprinting validates SAVE_FORMAT_VERSION against "
                    "WRAM save ranges, SRAM section contents, and layout.link SRAM bank "
                    "ownership; RTC source anchors are indexed and the debugger models "
                    "RAM enable, ROM bank, SRAM/RTC select, and latch write ranges, but "
                    + (
                        "RTC halt freeze semantics and MBC transition replay corpora are still incomplete"
                        if rtc_register_edge_runtime_replay["ready"]
                        else "runtime RTC and MBC transition replay corpora are still incomplete"
                    )
                )
            )
            row["unsupported_reason"] = (
                "needs runtime proof corpus for RTC halt semantics"
                if mbc_runtime_transition_replay_corpus["ready"]
                else "needs runtime proof corpus for RTC/MBC transitions"
            )
            row["missing_evidence"] = [
                MBC_RUNTIME_TRANSITION_REPLAY_GAP if item == MBC_STATE_TRANSITION_GAP else item
                for item in row["missing_evidence"]
            ]
            if mbc_runtime_transition_replay_corpus["ready"]:
                row["missing_evidence"] = [
                    item
                    for item in row["missing_evidence"]
                    if item != MBC_RUNTIME_TRANSITION_REPLAY_GAP
                ]
            if rtc_register_edge_runtime_replay["ready"] and mbc_runtime_transition_replay_corpus["ready"]:
                row["proof_status"] = "runtime_proven"
                row["missing_evidence"] = [
                    item
                    for item in row["missing_evidence"]
                    if item != RTC_REMAINING_HALT_FREEZE_SEMANTICS_RUNTIME_GAP
                ]
                row["unsupported_reason"] = (
                    "PyBoy RTC readback proves carry/day-overflow registers and halt-bit "
                    "readback, but does not authoritatively prove real-time halt freeze semantics"
                )
                row["backend"] = "pyboy_plus_static_with_named_rtc_limit"
    if interrupt_entry_ime_model["ready"]:
        for row in rows:
            if row["surface_id"] != "interrupts_dma_timers_lcd":
                continue
            row["proof_status"] = "partial"
            row["proof_capability"] = (
                (
                    "interrupt vectors, HALT/STOP/EI/DI/RETI IME semantics, and trace-inferred "
                    "interrupt-entry stack effects are modeled and proof-gated; selected PyBoy "
                    "VBlank/LCD STAT/timer interrupt entry/exit runtime event streams are captured"
                )
                if interrupt_entry_exit_runtime_events["ready"]
                else (
                    "interrupt vectors, HALT/STOP/EI/DI/RETI IME semantics, and trace-inferred "
                    "interrupt-entry stack effects are modeled and proof-gated; explicit interrupt "
                    "entry/exit runtime event streams are still incomplete"
                )
            )
            row["unsupported_reason"] = "needs explicit runtime hardware event stream"
            row["backend"] = "static_model"
            row["missing_evidence"] = [
                INTERRUPT_ENTRY_EXIT_RUNTIME_EVENT_STREAM_GAP
                if item == INTERRUPT_ENTRY_EXIT_EVENTS_GAP
                else item
                for item in row["missing_evidence"]
            ]
            if interrupt_entry_exit_runtime_events["ready"]:
                row["missing_evidence"] = [
                    item
                    for item in row["missing_evidence"]
                    if item != INTERRUPT_ENTRY_EXIT_RUNTIME_EVENT_STREAM_GAP
                ]
    if dma_oam_vram_transfer_models["ready"]:
        for row in rows:
            if row["surface_id"] != "interrupts_dma_timers_lcd":
                continue
            row["proof_status"] = "partial"
            row["proof_capability"] = (
                "interrupt/IME semantics and OAM/CGB VRAM DMA trigger/transfer models are "
                "validated and proof-gated; selected DMA runtime event streams are captured"
                if dma_oam_vram_runtime_events["ready"]
                else (
                    "interrupt/IME semantics and OAM/CGB VRAM DMA trigger/transfer models are "
                    "validated and proof-gated; explicit DMA runtime event streams are still incomplete"
                )
            )
            row["unsupported_reason"] = "needs explicit runtime hardware event stream"
            row["backend"] = "static_model"
            row["missing_evidence"] = [
                DMA_OAM_VRAM_RUNTIME_EVENT_STREAM_GAP
                if item == DMA_OAM_VRAM_EVENTS_GAP
                else item
                for item in row["missing_evidence"]
            ]
            if dma_oam_vram_runtime_events["ready"]:
                row["missing_evidence"] = [
                    item
                    for item in row["missing_evidence"]
                    if item != DMA_OAM_VRAM_RUNTIME_EVENT_STREAM_GAP
                ]
    if timer_ppu_io_overflow_models["ready"]:
        for row in rows:
            if row["surface_id"] != "interrupts_dma_timers_lcd":
                continue
            row["proof_status"] = "partial"
            row["proof_capability"] = (
                "interrupt/IME, DMA, timer IO, PPU/LCD IO, and adjacent-frame TIMA overflow "
                "models are validated and proof-gated; timer/LCD mode runtime event streams "
                "are still incomplete"
            )
            row["unsupported_reason"] = "needs explicit runtime hardware event stream"
            row["backend"] = "static_model"
            row["missing_evidence"] = [
                TIMER_LCD_MODE_RUNTIME_EVENT_STREAM_GAP
                if item == TIMER_LCD_MODE_EVENTS_GAP
                else item
                for item in row["missing_evidence"]
            ]
            if timer_lcd_mode_runtime_events["ready"]:
                row["proof_status"] = "runtime_proven"
                row["proof_capability"] = (
                    "interrupt/IME, DMA, timer IO, PPU/LCD IO, adjacent-frame TIMA overflow "
                    "models, and selected timer/LCD runtime event streams are validated; "
                    "cycle-exact hardware parity remains outside this PyBoy evidence"
                )
                row["missing_evidence"] = [
                    item
                    for item in row["missing_evidence"]
                    if item != TIMER_LCD_MODE_RUNTIME_EVENT_STREAM_GAP
                ]
                row["unsupported_reason"] = (
                    "cycle-exact hardware and cross-backend timing parity are outside the local "
                    "PyBoy event-stream proof"
                )
                row["backend"] = "pyboy_static_model_with_named_timing_limit"
    if serial_register_write_model["ready"]:
        for row in rows:
            if row["surface_id"] != "link_serial_mystery_gift":
                continue
            row["proof_status"] = "partial"
            row["proof_capability"] = (
                "serial interrupt vectors and SB/SC register write effects are modeled; "
                "serial transfer runtime event streams are still incomplete"
            )
            if serial_transfer_runtime_events["ready"]:
                row["proof_capability"] = (
                    "serial interrupt vectors, SB/SC register write effects, and selected "
                    "PyBoy internal-clock serial transfer runtime events are validated; "
                    "linked-peer serial transfers, Mystery Gift protocol flow, and cross-backend serial parity remain incomplete"
                )
            row["unsupported_reason"] = "needs link backend/runtime event stream"
            row["backend"] = "static_model"
            row["missing_evidence"] = [
                SERIAL_TRANSFER_RUNTIME_EVENT_STREAM_GAP
                if item == SERIAL_EVENT_STREAM_GAP
                else item
                for item in row["missing_evidence"]
            ]
            if serial_transfer_runtime_events["ready"]:
                row["missing_evidence"] = [
                    item
                    for item in row["missing_evidence"]
                    if item != SERIAL_TRANSFER_RUNTIME_EVENT_STREAM_GAP
                ]
    if link_boundary_source_anchors["ready"]:
        for row in rows:
            if row["surface_id"] != "link_serial_mystery_gift":
                continue
            row["proof_status"] = "partial"
            row["proof_capability"] = (
                "serial register writes are modeled, link receptionist/link communications/Time Capsule "
                "source anchors are indexed, and unsupported link-boundary runtime state classes are "
                "canonicalized; serial transfer runtime event streams are still incomplete"
                if link_boundary_runtime_state_class_corpus["ready"]
                else (
                    "serial register writes are modeled and link receptionist, link communications, "
                    "and Time Capsule source anchors are indexed; runtime link state-class corpora "
                    "are still incomplete"
                )
            )
            row["unsupported_reason"] = "needs link backend/runtime event stream"
            row["backend"] = "static_model"
            row["missing_evidence"] = [
                LINK_BOUNDARY_RUNTIME_STATE_CLASS_CORPUS_GAP
                if item == LINK_BOUNDARY_STATE_CLASSES_GAP
                else item
                for item in row["missing_evidence"]
            ]
            if link_boundary_runtime_state_class_corpus["ready"]:
                row["proof_status"] = "runtime_proven"
                row["missing_evidence"] = [
                    item
                    for item in row["missing_evidence"]
                    if item != LINK_BOUNDARY_RUNTIME_STATE_CLASS_CORPUS_GAP
                ]
                row["unsupported_reason"] = (
                    "linked-peer serial transfers, cable timing, Mystery Gift protocol completion, "
                    "and cross-backend serial parity are named unsupported scope"
                )
                row["backend"] = "pyboy_static_model_with_named_link_limit"
    for row in rows:
        if row["surface_id"] == "rom_byte_index" and not row["missing_evidence"]:
            row["proof_status"] = "static_proven"
            row["proof_capability"] = (
                "rom-index emits fresh JSONL linker/symbol span indexes, rom-byte provides "
                "point lookup, and content-mirror exact spans are reported for the generated corpus"
            )
            row["backend"] = "static"
    partial_statuses = {"partial", "static_mirror_only", "emulator_evidence"}
    for row in rows:
        if row["surface_id"] != "unified_debugger_front_door":
            continue
        non_front_rows = [item for item in rows if item["surface_id"] != "unified_debugger_front_door"]
        if (
            rom_index_artifacts["ready"]
            and canonical_selected_adoption_ready
            and not any(item["missing_evidence"] for item in non_front_rows)
            and not any(item["proof_status"] in partial_statuses for item in non_front_rows)
        ):
            row["proof_status"] = "complete"
            row["proof_capability"] = (
                "the unified debugger front door has command taxonomy, read-only refusal, "
                "fresh whole-ROM indexes, and every reachable surface is either proven or "
                "has named unsupported scope"
            )
            row["missing_evidence"] = [
                item
                for item in row["missing_evidence"]
                if item not in {"whole_rom_surface_inventory", "no_partial_pass_literal_anything_gate"}
            ]
            row["backend"] = "static"
        break
    hash_basis = boss_ai_hash_basis()
    stale_count = int(rom_index_artifacts.get("stale_artifact_count", 0) or 0)
    for item in hash_basis.get("diagnostics", []):
        if item.get("status") != "match":
            stale_count += 1
    unowned = [
        row
        for row in rows
        if row["reachable"] and not row["owner_lane"]
    ]
    unsupported_without_reason = [
        row
        for row in rows
        if row["proof_status"] == "unsupported" and not row["unsupported_reason"]
    ]
    partial_pass = [
        row
        for row in rows
        if row["proof_status"] in partial_statuses
    ]
    backend_divergence = [
        row
        for row in rows
        if row["backend"] in {"pyboy", "none"}
        and not row["unsupported_reason"]
        and row["surface_id"] in {
            "graphics_ui",
            "audio",
            "interrupts_dma_timers_lcd",
            "link_serial_mystery_gift",
        }
    ]
    blocking_gaps: list[str] = []
    if not canonical_selected_adoption_ready:
        blocking_gaps.insert(0, CANONICAL_STATE_CLASS_GLOBAL_GAP)
    if int(rom_index_artifacts.get("stale_artifact_count", 0) or 0) > 0:
        blocking_gaps.insert(0, "rom_index_artifacts_stale")
    elif not rom_index_artifacts["ready"]:
        blocking_gaps.insert(0, "whole-ROM surface inventory is not generated")
    for row in rows:
        blocking_gaps.extend(str(item) for item in row["missing_evidence"])
    if partial_pass:
        blocking_gaps.append("no_partial_pass_literal_anything_gate")
    if not blocking_gaps:
        for row in rows:
            if row["surface_id"] == "unified_debugger_front_door":
                row["proof_status"] = "complete"
                row["proof_capability"] = (
                    "the unified debugger front door has command taxonomy, read-only refusal, "
                    "fresh whole-ROM indexes, and every reachable surface is either proven or "
                    "has named unsupported scope"
                )
                row["missing_evidence"] = []
                break
        partial_pass = [
            row
            for row in rows
            if row["proof_status"] in partial_statuses
        ]
    counters = {
        "unowned_reachable_surface_count": len(unowned),
        "unsupported_without_reason": len(unsupported_without_reason),
        "partial_pass_count": len(partial_pass),
        "stale_artifact_count": stale_count,
        "backend_divergence_count": len(backend_divergence),
        "side_effect_unknown_command_count": int(taxonomy["side_effect_unknown_command_count"]),
    }
    ready = all(value == 0 for value in counters.values()) and not blocking_gaps
    closed_evidence_ids = [
        "command_side_effect_taxonomy.reported",
        "tiered_readiness.reported",
        "literal_anything_gate.reported",
        "rom_byte_lookup.confidence_scored_source_lookup",
        "runtime_event_envelope.helper_available",
    ]
    if taxonomy.get("read_only_refusal_enforced", False):
        closed_evidence_ids.append(READ_ONLY_REFUSAL_EVIDENCE_ID)
    if canonical_selected_adoption_ready:
        closed_evidence_ids.append(CANONICAL_STATE_CLASS_SELECTED_ADOPTION_EVIDENCE_ID)
    if script_map_content_materializers.get("canonical_state_class_materializers_ready", False):
        closed_evidence_ids.append(CANONICAL_STATE_CLASS_CONTENT_STATE_MATERIALIZER_EVIDENCE_ID)
    if damage_mutation_campaign.get("canonical_state_class_cases_ready", False):
        closed_evidence_ids.append(CANONICAL_STATE_CLASS_DAMAGE_MUTATION_EVIDENCE_ID)
    if rom_index_artifacts["ready"]:
        closed_evidence_ids.append("rom_index_jsonl.generated")
        closed_evidence_ids.append("whole_rom_surface_inventory.generated")
    if content_mirror_artifact["ready"]:
        closed_evidence_ids.append("content_mirror_exact_span_rows.reported")
    if after_hit_item_order["ready"]:
        closed_evidence_ids.append(AFTER_HIT_ORDER_EVIDENCE_ID)
    if damage_modifier_recoil_smoke["ready"]:
        closed_evidence_ids.append(DAMAGE_MODIFIER_RECOIL_EVIDENCE_ID)
    if damage_fuzz_no_divergence["ready"]:
        closed_evidence_ids.append(DAMAGE_FUZZ_NO_DIVERGENCE_EVIDENCE_ID)
    if damage_mutation_campaign["ready"]:
        closed_evidence_ids.extend(
            str(item)
            for item in damage_mutation_campaign.get("closed_evidence_ids", [])
        )
    if audio_apu_event_envelope["ready"]:
        closed_evidence_ids.append(AUDIO_APU_EVENT_EVIDENCE_ID)
        closed_evidence_ids.append(AUDIO_TYPHLOSION_CRY_MATCH_EVIDENCE_ID)
    if script_vm_event_log["ready"]:
        closed_evidence_ids.append(SCRIPT_VM_EVENT_EVIDENCE_ID)
    if script_map_content_materializers["ready"]:
        closed_evidence_ids.append(SCRIPT_MAP_CONTENT_MATERIALIZER_EVIDENCE_ID)
        if script_map_content_materializers["callback_script_entry_materializer_ready"]:
            closed_evidence_ids.append(SCRIPT_MAP_CALLBACK_SELECTED_EVIDENCE_ID)
        if script_map_content_materializers["callback_script_entry_corpus_ready"]:
            closed_evidence_ids.append(SCRIPT_MAP_CALLBACK_CORPUS_EVIDENCE_ID)
        if script_map_content_materializers["warp_object_position_materializers_ready"]:
            closed_evidence_ids.append(SCRIPT_WARP_OBJECT_POSITION_EVIDENCE_ID)
        if script_map_content_materializers["object_struct_visibility_materializers_ready"]:
            closed_evidence_ids.append(SCRIPT_OBJECT_STRUCT_VISIBILITY_EVIDENCE_ID)
    if script_map_content_runtime_replays["ready"]:
        closed_evidence_ids.append(SCRIPT_WARP_OBJECT_COLLISION_RUNTIME_EVIDENCE_ID)
    if graphics_digest_parity["ready"]:
        closed_evidence_ids.append(GRAPHICS_DIGEST_EVIDENCE_ID)
    if graphics_backend_labels["ready"]:
        closed_evidence_ids.append(GRAPHICS_BACKEND_LABEL_EVIDENCE_ID)
    if save_format_sram_bank_ownership["ready"]:
        closed_evidence_ids.append(SAVE_FORMAT_SRAM_BANK_EVIDENCE_ID)
    if rtc_edge_case_source_anchors["ready"]:
        closed_evidence_ids.append(RTC_SOURCE_ANCHOR_EVIDENCE_ID)
    if rtc_register_edge_runtime_replay["ready"]:
        closed_evidence_ids.append(RTC_REGISTER_EDGE_RUNTIME_REPLAY_EVIDENCE_ID)
        if rtc_register_edge_runtime_replay["halt_negative_control_ready"]:
            closed_evidence_ids.append(RTC_HALT_BIT_NEGATIVE_CONTROL_EVIDENCE_ID)
    if mbc_bank_transition_model["ready"]:
        closed_evidence_ids.append(MBC_BANK_TRANSITION_MODEL_EVIDENCE_ID)
    if mbc_runtime_transition_replay_corpus["ready"]:
        closed_evidence_ids.append(MBC_RUNTIME_TRANSITION_REPLAY_EVIDENCE_ID)
    if interrupt_entry_ime_model["ready"]:
        closed_evidence_ids.append(HARDWARE_INTERRUPT_MODEL_EVIDENCE_ID)
    if interrupt_entry_exit_runtime_events["ready"]:
        closed_evidence_ids.append(HARDWARE_INTERRUPT_RUNTIME_EVENT_EVIDENCE_ID)
    if dma_oam_vram_transfer_models["ready"]:
        closed_evidence_ids.append(HARDWARE_DMA_MODEL_EVIDENCE_ID)
    if dma_oam_vram_runtime_events["ready"]:
        closed_evidence_ids.append(HARDWARE_DMA_RUNTIME_EVENT_EVIDENCE_ID)
    if timer_ppu_io_overflow_models["ready"]:
        closed_evidence_ids.append(HARDWARE_TIMER_LCD_MODEL_EVIDENCE_ID)
    if timer_lcd_mode_runtime_events["ready"]:
        closed_evidence_ids.append(HARDWARE_TIMER_LCD_RUNTIME_EVENT_EVIDENCE_ID)
    if serial_register_write_model["ready"]:
        closed_evidence_ids.append(SERIAL_REGISTER_WRITE_MODEL_EVIDENCE_ID)
    if serial_transfer_runtime_events["ready"]:
        closed_evidence_ids.append(SERIAL_TRANSFER_RUNTIME_EVENT_EVIDENCE_ID)
    if link_boundary_source_anchors["ready"]:
        closed_evidence_ids.append(LINK_BOUNDARY_SOURCE_ANCHOR_EVIDENCE_ID)
    if link_boundary_runtime_state_class_corpus["ready"]:
        closed_evidence_ids.append(LINK_BOUNDARY_RUNTIME_STATE_CLASS_CORPUS_EVIDENCE_ID)
    if headless_spikes_hazard_smoke["ready"]:
        closed_evidence_ids.append(HEADLESS_SPIKES_HAZARD_EVIDENCE_ID)
    if headless_component_rom_differentials["ready"]:
        closed_evidence_ids.append(HEADLESS_COMPONENT_ROM_DIFFERENTIAL_EVIDENCE_ID)
    if headless_promoted_turn_worklist["ready"]:
        closed_evidence_ids.append(HEADLESS_PROMOTED_TURN_WORKLIST_EVIDENCE_ID)
    closed_evidence_ids.extend(str(item) for item in boss_ai_class_adoption.get("closed_evidence_ids", []))
    if boss_ai_god_gate.get("bridge_valid") or boss_ai_god_gate["ready"]:
        closed_evidence_ids.extend(str(item) for item in boss_ai_god_gate.get("closed_evidence_ids", []))
    closed_evidence_ids.extend(
        str(item) for item in headless_battle_class_adoption.get("closed_evidence_ids", [])
    )

    known_limits = [
        "Graphics, audio, timing, RTC halt-freeze, and link-peer claims remain limited "
        "to the named backend scope recorded on each surface row.",
    ]
    if not ready:
        known_limits.insert(
            0,
            "This honesty gate inventories the current proof gaps; it does not claim whole-ROM readiness.",
        )
    envelope = build_report_envelope(
        kind="debugger_literal_anything_baseline",
        command="python tools\\audit\\check_debugger_literal_anything.py --baseline",
        inputs={"read_only": read_only},
        backend="mixed",
        proof_status="complete" if ready else "missing_evidence",
        missing_evidence=sorted(set(blocking_gaps)),
        blocking_gaps=sorted(set(blocking_gaps)),
        known_limits=known_limits,
        closed_evidence_ids=closed_evidence_ids,
        repro_command="python tools\\audit\\check_debugger_literal_anything.py --baseline --read-only",
        disproof_standard=[
            "Every reachable surface row is owned and classified.",
            "Every surface proof packet is complete with no missing evidence or stale basis.",
            "Every command has side-effect metadata and read-only refusal semantics.",
        ],
        root=root,
    )
    envelope.update(
        {
            "generated_at": utc_now(),
            "literal_anything_ready": ready,
            "readiness_tiers": capability.get("readiness_tiers", {}),
            "counters": counters,
            "surfaces": rows,
            "hash_basis": hash_basis,
            "rom_index_artifacts": rom_index_artifacts,
            "content_mirror_span_artifact": content_mirror_artifact,
            "canonical_state_class_schema": canonical_state_class_schema,
            "after_hit_item_order": after_hit_item_order,
            "damage_modifier_recoil_smoke": damage_modifier_recoil_smoke,
            "damage_fuzz_no_divergence": damage_fuzz_no_divergence,
            "damage_mutation_campaign": damage_mutation_campaign,
            "audio_apu_event_envelope": audio_apu_event_envelope,
            "script_vm_event_log": script_vm_event_log,
            "script_map_content_materializers": script_map_content_materializers,
            "script_map_content_runtime_replays": script_map_content_runtime_replays,
            "graphics_digest_parity": graphics_digest_parity,
            "graphics_backend_labels": graphics_backend_labels,
            "save_format_sram_bank_ownership": save_format_sram_bank_ownership,
            "rtc_edge_case_source_anchors": rtc_edge_case_source_anchors,
            "rtc_register_edge_runtime_replay": rtc_register_edge_runtime_replay,
            "mbc_bank_transition_model": mbc_bank_transition_model,
            "mbc_runtime_transition_replay_corpus": mbc_runtime_transition_replay_corpus,
            "interrupt_entry_ime_model": interrupt_entry_ime_model,
            "interrupt_entry_exit_runtime_events": interrupt_entry_exit_runtime_events,
            "dma_oam_vram_transfer_models": dma_oam_vram_transfer_models,
            "dma_oam_vram_runtime_events": dma_oam_vram_runtime_events,
            "timer_ppu_io_overflow_models": timer_ppu_io_overflow_models,
            "timer_lcd_mode_runtime_events": timer_lcd_mode_runtime_events,
            "serial_register_write_model": serial_register_write_model,
            "serial_transfer_runtime_events": serial_transfer_runtime_events,
            "link_boundary_source_anchors": link_boundary_source_anchors,
            "link_boundary_runtime_state_class_corpus": link_boundary_runtime_state_class_corpus,
            "headless_spikes_hazard_smoke": headless_spikes_hazard_smoke,
            "headless_component_rom_differentials": headless_component_rom_differentials,
            "headless_promoted_turn_worklist": headless_promoted_turn_worklist,
            "boss_ai_class_adoption": boss_ai_class_adoption,
            "boss_ai_god_gate": boss_ai_god_gate,
            "headless_battle_class_adoption": headless_battle_class_adoption,
            "command_taxonomy": {
                key: value
                for key, value in taxonomy.items()
                if key != "commands"
            },
            "read_only_mode": {
                "requested": read_only,
                "would_write_baseline": False,
                "baseline_write_refused": read_only,
                "side_effect_metadata_available": True,
                "global_command_refusal_enforced": bool(
                    taxonomy.get("read_only_refusal_enforced", False)
                ),
            },
        }
    )
    return envelope


def boss_ai_hash_basis() -> dict[str, Any]:
    try:
        from tools.boss_ai_debugger.commands import boss_ai_trace_hash_basis

        return boss_ai_trace_hash_basis()
    except Exception as exc:  # noqa: BLE001
        return {"ready": False, "status": "unavailable", "diagnostics": [], "error": str(exc)}


def rom_index_artifact_status(*, root: Path = ROOT) -> dict[str, Any]:
    surface_path = root / "audit" / "debugger_literal_anything" / "rom_surface_index.jsonl"
    byte_path = root / "audit" / "debugger_literal_anything" / "rom_byte_index.jsonl"
    report_path = root / "audit" / "debugger_literal_anything" / "rom_index_report.json"
    expected_hashes = rom_index_input_hashes(root=root)
    surface_status = jsonl_status(
        surface_path,
        expected_kind="rom_surface_index_row",
        root=root,
        expected_input_hashes=expected_hashes,
    )
    byte_status = jsonl_status(
        byte_path,
        expected_kind="rom_byte_index_row",
        root=root,
        expected_input_hashes=expected_hashes,
    )
    report_status = json_report_status(
        report_path,
        expected_kind="unified_debugger_rom_index",
        root=root,
        expected_input_hashes=expected_hashes,
    )
    stale_artifact_count = sum(
        1
        for item in (surface_status, byte_status, report_status)
        if int(item.get("stale_row_count", 0) or 0) > 0
    )
    ready = (
        surface_status["ready"]
        and byte_status["ready"]
        and report_status["ready"]
        and int(byte_status.get("content_mirror_exact_span_count", 0)) > 0
        and stale_artifact_count == 0
    )
    return {
        "ready": ready,
        "surface_index": surface_status,
        "byte_index": byte_status,
        "report": report_status,
        "input_hashes": expected_hashes,
        "stale_artifact_count": stale_artifact_count,
        "next_command": (
            "python -m tools.debugger rom-index "
            "--surface-index-out audit\\debugger_literal_anything\\rom_surface_index.jsonl "
            "--byte-index-out audit\\debugger_literal_anything\\rom_byte_index.jsonl "
            "--content-mirror-report audit\\debugger_literal_anything\\content_mirror_exact_spans.json "
            "--json-out audit\\debugger_literal_anything\\rom_index_report.json"
        ),
    }


def rom_index_input_hashes(*, root: Path = ROOT) -> dict[str, str]:
    return {
        "rom_sha256": sha256_file("pokegold.gbc", root=root),
        "symbols_sha256": sha256_file("pokegold.sym", root=root),
        "map_sha256": sha256_file("pokegold.map", root=root),
    }


def content_mirror_span_artifact_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "debugger_literal_anything" / "content_mirror_exact_spans.json"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "sha256": sha256_file(path, root=root),
        "byte_span_row_count": 0,
        "exact_span_count": 0,
        "errors": [],
        "next_command": (
            "python -m tools.debugger content-mirror "
            "--source-file maps\\NewBarkTown.asm "
            "--json-out audit\\debugger_literal_anything\\content_mirror_exact_spans.json"
        ),
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status
    if payload.get("kind") != "unified_debugger_content_mirror":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    rows = payload.get("byte_span_rows", [])
    if not isinstance(rows, list):
        status["errors"].append("byte_span_rows is not a list")
        rows = []
    status["byte_span_row_count"] = len(rows)
    status["exact_span_count"] = sum(
        1
        for row in rows
        if isinstance(row, dict) and row.get("confidence") == "content_mirror_exact_span"
    )
    if status["exact_span_count"] <= 0:
        status["errors"].append("no content_mirror_exact_span rows")
    status["ready"] = not status["errors"]
    return status


def after_hit_item_order_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "damage_debugger" / "clobber_smoke.log"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "scenario": AFTER_HIT_ORDER_SCENARIO,
        "scenario_line": "",
        "stale_dependencies": [],
        "errors": [],
        "next_command": "python -m tools.damage_debugger.clobber_smoke",
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        status["errors"].append(str(exc))
        return status

    for line in text.splitlines():
        if AFTER_HIT_ORDER_SCENARIO in line:
            status["scenario_line"] = line
            break
    if not status["scenario_line"] or "PASS" not in status["scenario_line"]:
        status["errors"].append(f"{AFTER_HIT_ORDER_SCENARIO} did not PASS")
    if "PASS: all" not in text or "within expected" not in text:
        status["errors"].append("clobber_smoke summary is not all-pass")

    try:
        log_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "damage_debugger" / "clobber_smoke.py",
        root / "engine" / "battle" / "late_gen_held_items.asm",
        root / "tools" / "headless_battle" / "simulator.py",
        root / "pokegold_debug.gbc",
        root / "pokegold_debug.sym",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > log_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("clobber_smoke log is older than after-hit proof inputs")
    status["ready"] = not status["errors"]
    return status


def damage_modifier_recoil_smoke_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "damage_debugger" / "clobber_smoke.log"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "case_count": 0,
        "missing_cases": [],
        "stale_dependencies": [],
        "errors": [],
        "next_command": "python -m tools.damage_debugger.clobber_smoke",
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        status["errors"].append(str(exc))
        return status

    passed: set[str] = set()
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0] in DAMAGE_MODIFIER_RECOIL_SCENARIOS and "PASS" in parts:
            passed.add(parts[0])
    missing_cases = [
        scenario
        for scenario in DAMAGE_MODIFIER_RECOIL_SCENARIOS
        if scenario not in passed
    ]
    status["case_count"] = len(passed)
    status["missing_cases"] = missing_cases
    if missing_cases:
        status["errors"].append(f"missing passed damage modifier/recoil cases: {missing_cases}")
    if "PASS: all 28 scenarios within expected damage ranges." not in text:
        status["errors"].append("clobber_smoke summary is not the expected all-28 PASS")

    try:
        log_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "damage_debugger" / "clobber_smoke.py",
        root / "engine" / "battle" / "late_gen_held_items.asm",
        root / "engine" / "battle" / "effect_commands.asm",
        root / "pokegold_debug.gbc",
        root / "pokegold_debug.sym",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > log_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("clobber_smoke log is older than damage modifier/recoil proof inputs")
    status["ready"] = not status["errors"]
    return status


def damage_fuzz_no_divergence_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "damage_debugger" / "fuzz_no_divergence.json"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "total_examples": 0,
        "workers": 0,
        "fail_count": 0,
        "bad_worker_count": 0,
        "min_examples": DAMAGE_FUZZ_MIN_EXAMPLES,
        "hash_basis": {},
        "stale_dependencies": [],
        "errors": [],
        "next_command": (
            "python -m tools.damage_debugger.fuzz --max-examples=100 --workers=2 "
            "--json-out audit\\damage_debugger\\fuzz_no_divergence.json"
        ),
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status

    if payload.get("kind") != "damage_debugger_fuzz_no_divergence":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    if payload.get("proof_status") != "complete":
        status["errors"].append(f"unexpected proof status: {payload.get('proof_status', '')}")
    hash_basis = payload.get("hash_basis")
    if isinstance(hash_basis, dict):
        status["hash_basis"] = {
            "rom_sha256": str(hash_basis.get("rom_sha256", "") or ""),
            "symbols_sha256": str(hash_basis.get("symbols_sha256", "") or ""),
        }
        basis_errors = hash_basis.get("errors", [])
        if basis_errors:
            status["errors"].append(f"hash basis errors: {basis_errors}")
    elif (root / "pokegold_debug.gbc").exists() or (root / "pokegold_debug.sym").exists():
        status["errors"].append("missing hash_basis")
        hash_basis = {}
    else:
        hash_basis = {}
    status["total_examples"] = int(payload.get("total_examples", 0) or 0)
    status["workers"] = int(payload.get("workers", 0) or 0)
    status["fail_count"] = int(payload.get("fail_count", 0) or 0)
    if status["total_examples"] < DAMAGE_FUZZ_MIN_EXAMPLES:
        status["errors"].append(
            f"only {status['total_examples']} fuzz examples; need at least {DAMAGE_FUZZ_MIN_EXAMPLES}"
        )
    if status["workers"] < 1:
        status["errors"].append("workers must be >= 1")
    if status["fail_count"] != 0:
        status["errors"].append("damage fuzz report has failures")
    results = payload.get("results", [])
    if not isinstance(results, list):
        results = []
        status["errors"].append("results is not a list")
    bad_workers = [
        result.get("worker_id", "<unknown>")
        for result in results
        if not isinstance(result, dict) or result.get("ok") is not True
    ]
    status["bad_worker_count"] = len(bad_workers)
    if bad_workers:
        status["errors"].append(f"non-passing fuzz workers: {bad_workers}")

    expected_hashes = (
        ("rom_sha256", root / "pokegold_debug.gbc"),
        ("symbols_sha256", root / "pokegold_debug.sym"),
    )
    for field, dependency in expected_hashes:
        if not dependency.exists():
            continue
        actual = sha256_file(dependency)
        recorded = str(hash_basis.get(field, "") or "")
        if not recorded:
            status["errors"].append(f"hash_basis.{field} is missing")
        elif recorded.upper() != actual.upper():
            status["errors"].append(f"hash_basis.{field} does not match current proof input")

    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "damage_debugger" / "fuzz.py",
        root / "tools" / "damage_debugger" / "oracle.py",
        root / "tools" / "damage_debugger" / "clobber_smoke.py",
        root / "tools" / "damage_debugger" / "safe_call.py",
        root / "pokegold_debug.gbc",
        root / "pokegold_debug.sym",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > artifact_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("damage fuzz artifact is older than proof inputs")
    status["ready"] = not status["errors"]
    return status


def damage_mutation_campaign_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "damage_debugger" / "mutation_campaign.json"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "campaign_count": 0,
        "case_count": 0,
        "pass_count": 0,
        "fail_count": 0,
        "missing_campaigns": [],
        "missing_mutation_ids": [],
        "bad_case_count": 0,
        "rom_backed_case_count": 0,
        "replay_case_count": 0,
        "campaign_proofs": {},
        "closed_evidence_ids": [],
        "canonical_state_class_cases_ready": False,
        "canonical_state_class_case_ids": {},
        "canonical_state_class_errors": [],
        "oracle_only_case_count": 0,
        "oracle_only_residual_gaps": [],
        "remaining_residual_gaps": list(DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS),
        "rng_distribution_ready": False,
        "rng_distribution_case_count": 0,
        "rng_distribution_observed_multipliers": [],
        "rng_distribution_rejection_loop_verified": False,
        "species_wide_eviolite_ready": False,
        "species_wide_eviolite_case_count": 0,
        "species_wide_eviolite_species_count": 0,
        "species_wide_eviolite_can_evolve_species_count": 0,
        "species_wide_eviolite_errors": [],
        "auto_minimized_divergence_ready": False,
        "auto_minimized_divergence_errors": [],
        "selected_status_side_effects_ready": False,
        "selected_status_side_effects_case_count": 0,
        "selected_status_side_effects_errors": [],
        "hash_basis": {},
        "stale_dependencies": [],
        "errors": [],
        "next_command": (
            "python -m tools.damage_debugger.mutation_campaign "
            "--json-out audit\\damage_debugger\\mutation_campaign.json"
        ),
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status

    if payload.get("kind") != "damage_debugger_phase6_initial_mutation_campaign":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    if payload.get("proof_status") != "complete":
        status["errors"].append(f"unexpected proof status: {payload.get('proof_status', '')}")
    closed = payload.get("closed_evidence_ids", [])
    if not isinstance(closed, list):
        status["errors"].append("closed_evidence_ids must be a list")
        closed = []
    if DAMAGE_MUTATION_CAMPAIGN_EVIDENCE_ID not in closed:
        status["errors"].append(f"missing closed evidence id: {DAMAGE_MUTATION_CAMPAIGN_EVIDENCE_ID}")
    does_not_close = payload.get("does_not_close", [])
    if not isinstance(does_not_close, list):
        status["errors"].append("does_not_close must be a list")
        does_not_close = []
    if DAMAGE_EXPANDED_MUTATION_CAMPAIGNS_GAP not in does_not_close:
        status["errors"].append("artifact must explicitly leave expanded_mutation_campaigns open")
    if payload.get("backend") != "pyboy":
        status["errors"].append(f"unexpected backend: {payload.get('backend', '')}")
    status["campaign_count"] = int(payload.get("campaign_count", 0) or 0)
    status["case_count"] = int(payload.get("case_count", 0) or 0)
    status["pass_count"] = int(payload.get("pass_count", 0) or 0)
    status["fail_count"] = int(payload.get("fail_count", 0) or 0)
    if status["case_count"] < DAMAGE_MUTATION_MIN_CASES:
        status["errors"].append(
            f"only {status['case_count']} mutation cases; need at least {DAMAGE_MUTATION_MIN_CASES}"
        )
    if status["fail_count"] != 0:
        status["errors"].append("damage mutation campaign report has failures")
    campaign_ids = payload.get("campaign_ids", [])
    if not isinstance(campaign_ids, list):
        campaign_ids = []
        status["errors"].append("campaign_ids is not a list")
    required_campaigns = payload.get("required_campaigns", [])
    if not isinstance(required_campaigns, list):
        required_campaigns = []
        status["errors"].append("required_campaigns is not a list")
    expected_campaign_set = {str(item) for item in DAMAGE_MUTATION_REQUIRED_CAMPAIGNS}
    campaign_id_set = {str(item) for item in campaign_ids}
    required_campaign_set = {str(item) for item in required_campaigns}
    missing_campaigns = [
        campaign
        for campaign in DAMAGE_MUTATION_REQUIRED_CAMPAIGNS
        if campaign not in campaign_id_set
    ]
    status["missing_campaigns"] = missing_campaigns
    if missing_campaigns:
        status["errors"].append(f"missing mutation campaigns: {missing_campaigns}")
    missing_required_campaigns = sorted(expected_campaign_set - required_campaign_set)
    if missing_required_campaigns:
        status["errors"].append(f"required_campaigns missing entries: {missing_required_campaigns}")
    unknown_campaigns = sorted((campaign_id_set | required_campaign_set) - expected_campaign_set)
    if unknown_campaigns:
        status["errors"].append(f"unknown mutation campaigns: {unknown_campaigns}")
    if status["campaign_count"] != len(campaign_id_set) or status["campaign_count"] != len(required_campaign_set):
        status["errors"].append("campaign_count does not match campaign_ids/required_campaigns")

    cases = payload.get("rom_backed_cases", [])
    if not isinstance(cases, list):
        cases = []
        status["errors"].append("rom_backed_cases is not a list")
    status["rom_backed_case_count"] = len(cases)
    if len(cases) != status["case_count"]:
        status["errors"].append("rom_backed_cases count does not match case_count")
    mutation_ids = {
        str(case.get("mutation_id", ""))
        for case in cases
        if isinstance(case, dict)
    }
    missing_mutation_ids = [
        mutation_id
        for mutation_id in DAMAGE_MUTATION_REQUIRED_IDS
        if mutation_id not in mutation_ids
    ]
    status["missing_mutation_ids"] = missing_mutation_ids
    if missing_mutation_ids:
        status["errors"].append(f"missing required mutation ids: {missing_mutation_ids}")
    bad_cases: list[str] = []
    canonical_class_ids: dict[str, str] = {}
    canonical_errors: list[str] = []
    try:
        from tools.debugger.canonical_state_class import validate_canonical_state_class
    except Exception as exc:  # noqa: BLE001
        validate_canonical_state_class = None
        status["errors"].append(f"canonical state-class validator unavailable: {type(exc).__name__}: {exc}")
    cases_by_campaign: dict[str, list[dict[str, Any]]] = {
        campaign: []
        for campaign in DAMAGE_MUTATION_REQUIRED_CAMPAIGNS
    }
    for case in cases:
        if not isinstance(case, dict):
            bad_cases.append("<non-object>")
            continue
        case_id = str(case.get("mutation_id", case.get("case_id", "<unknown>")))
        campaign_id = str(case.get("campaign_id", "") or "")
        if campaign_id not in expected_campaign_set:
            status["errors"].append(f"{case_id} has unknown campaign_id: {campaign_id}")
        else:
            cases_by_campaign[campaign_id].append(case)
        if str(case.get("category", "") or "") != campaign_id:
            status["errors"].append(f"{case_id} category does not match campaign_id")
        if case.get("ok") is not True:
            bad_cases.append(case_id)
        method = str(case.get("method", ""))
        if case.get("rom_backed") is not True:
            status["errors"].append(f"{case_id} is not marked ROM-backed")
        if method == "fuzz.check_one":
            if not isinstance(case.get("mutated_fields"), list) or not case.get("mutated_fields"):
                status["errors"].append(f"{case_id} missing mutated_fields")
            if not isinstance(case.get("inputs"), dict) or not case.get("inputs"):
                status["errors"].append(f"{case_id} missing fuzz inputs")
            for numeric_field in ("rom_damage", "oracle_damage", "delta", "tolerance"):
                if not isinstance(case.get(numeric_field), (int, float)):
                    status["errors"].append(f"{case_id} missing numeric {numeric_field}")
            if not isinstance(case.get("on_divergence"), dict) or not case.get("on_divergence"):
                status["errors"].append(f"{case_id} missing divergence handoff commands")
            elif not str(case.get("on_divergence", {}).get("replay_command", "") or ""):
                status["errors"].append(f"{case_id} missing divergence replay command")
        elif method == "replay.replay_scenario":
            status["replay_case_count"] += 1
            if case.get("replay_verified") is not True:
                status["errors"].append(f"{case_id} replay was not verified")
            hit = case.get("hit")
            if not isinstance(hit, dict) or not hit:
                status["errors"].append(f"{case_id} missing replay hit")
            else:
                if hit.get("replay_verified") is not True:
                    status["errors"].append(f"{case_id} replay hit was not verified")
                for field in ("watch", "function", "old_hex", "new_hex"):
                    if not str(hit.get(field, "") or ""):
                        status["errors"].append(f"{case_id} replay hit missing {field}")
        elif method == "clobber_smoke.run_scenario":
            if case.get("xfail"):
                status["errors"].append(f"{case_id} is xfail")
            if case.get("check_failures"):
                status["errors"].append(f"{case_id} has check failures")
            if not isinstance(case.get("seed_state"), dict) or not case.get("seed_state"):
                status["errors"].append(f"{case_id} missing smoke seed_state")
            for numeric_field in ("damage", "expected_low", "expected_high"):
                if not isinstance(case.get(numeric_field), int):
                    status["errors"].append(f"{case_id} missing numeric {numeric_field}")
        else:
            status["errors"].append(f"{case_id} has unsupported method: {method}")
        row_canonical_errors = damage_mutation_case_class_errors(
            case,
            validate_canonical_state_class=validate_canonical_state_class,
        )
        if row_canonical_errors:
            canonical_errors.extend(row_canonical_errors)
            status["errors"].extend(row_canonical_errors)
        else:
            canonical_class_ids[case_id] = str(case.get("class_id", "") or "")
    status["bad_case_count"] = len(bad_cases)
    status["canonical_state_class_case_ids"] = canonical_class_ids
    status["canonical_state_class_errors"] = canonical_errors
    if len(set(canonical_class_ids.values())) != len(canonical_class_ids):
        status["errors"].append("damage mutation canonical class_ids are not unique")
        status["canonical_state_class_errors"].append("damage mutation canonical class_ids are not unique")
    status["canonical_state_class_cases_ready"] = (
        len(canonical_class_ids) == len(cases)
        and not canonical_errors
        and len(set(canonical_class_ids.values())) == len(canonical_class_ids)
    )
    if bad_cases:
        status["errors"].append(f"non-passing mutation cases: {bad_cases}")
    if status["pass_count"] != status["case_count"]:
        status["errors"].append("pass_count does not match case_count")
    campaign_proofs: dict[str, dict[str, Any]] = {}
    for campaign, required_ids in DAMAGE_MUTATION_REQUIRED_IDS_BY_CAMPAIGN.items():
        rows = cases_by_campaign.get(campaign, [])
        row_ids = {
            str(row.get("mutation_id", "") or "")
            for row in rows
        }
        missing_ids = [
            mutation_id
            for mutation_id in required_ids
            if mutation_id not in row_ids
        ]
        ready = not missing_ids and len(rows) >= len(required_ids)
        if missing_ids:
            status["errors"].append(f"{campaign} missing campaign mutation ids: {missing_ids}")
        campaign_proofs[campaign] = {
            "ready": ready,
            "case_count": len(rows),
            "required_case_count": len(required_ids),
            "missing_mutation_ids": missing_ids,
            "evidence_id": DAMAGE_MUTATION_CAMPAIGN_EVIDENCE_IDS[campaign],
            "mutation_ids": sorted(row_ids),
        }
    status["campaign_proofs"] = campaign_proofs
    rng_distribution_proof = payload.get("rng_distribution_proof", {})
    rng_distribution_errors = damage_rng_distribution_proof_errors(rng_distribution_proof)
    if rng_distribution_errors:
        status["errors"].extend(rng_distribution_errors)
    else:
        status["rng_distribution_ready"] = True
        status["rng_distribution_case_count"] = int(rng_distribution_proof.get("case_count", 0) or 0)
        status["rng_distribution_observed_multipliers"] = list(
            rng_distribution_proof.get("observed_multipliers", [])
        )
        status["rng_distribution_rejection_loop_verified"] = bool(
            rng_distribution_proof.get("rejection_loop_verified", False)
        )
    species_wide_proof = payload.get("species_wide_eviolite_proof", {})
    if species_wide_proof or DAMAGE_MUTATION_SPECIES_WIDE_EVIOLITE_EVIDENCE_ID in closed:
        if DAMAGE_MUTATION_SPECIES_WIDE_EVIOLITE_EVIDENCE_ID not in closed:
            status["errors"].append(
                f"missing closed evidence id: {DAMAGE_MUTATION_SPECIES_WIDE_EVIOLITE_EVIDENCE_ID}"
            )
        species_wide_errors = damage_species_wide_eviolite_proof_errors(
            species_wide_proof,
            cases=cases,
            root=root,
        )
        status["species_wide_eviolite_errors"] = species_wide_errors
        if species_wide_errors:
            status["errors"].extend(species_wide_errors)
        else:
            status["species_wide_eviolite_ready"] = True
            status["species_wide_eviolite_case_count"] = int(species_wide_proof.get("case_count", 0) or 0)
            status["species_wide_eviolite_species_count"] = int(species_wide_proof.get("species_count", 0) or 0)
            status["species_wide_eviolite_can_evolve_species_count"] = int(
                species_wide_proof.get("can_evolve_species_count", 0) or 0
            )
    auto_minimized_proof = payload.get("auto_minimized_divergence_proof", {})
    if auto_minimized_proof or DAMAGE_MUTATION_AUTO_MINIMIZED_DIVERGENCE_EVIDENCE_ID in closed:
        if DAMAGE_MUTATION_AUTO_MINIMIZED_DIVERGENCE_EVIDENCE_ID not in closed:
            status["errors"].append(
                f"missing closed evidence id: {DAMAGE_MUTATION_AUTO_MINIMIZED_DIVERGENCE_EVIDENCE_ID}"
            )
        auto_minimized_errors = damage_auto_minimized_divergence_proof_errors(auto_minimized_proof)
        status["auto_minimized_divergence_errors"] = auto_minimized_errors
        if auto_minimized_errors:
            status["errors"].extend(auto_minimized_errors)
        else:
            status["auto_minimized_divergence_ready"] = True
    selected_status_proof = payload.get("selected_status_side_effects_proof", {})
    if selected_status_proof or DAMAGE_MUTATION_SELECTED_STATUS_SIDE_EFFECTS_EVIDENCE_ID in closed:
        if DAMAGE_MUTATION_SELECTED_STATUS_SIDE_EFFECTS_EVIDENCE_ID not in closed:
            status["errors"].append(
                f"missing closed evidence id: {DAMAGE_MUTATION_SELECTED_STATUS_SIDE_EFFECTS_EVIDENCE_ID}"
            )
        selected_status_errors = damage_selected_status_side_effects_proof_errors(selected_status_proof)
        status["selected_status_side_effects_errors"] = selected_status_errors
        if selected_status_errors:
            status["errors"].extend(selected_status_errors)
        else:
            status["selected_status_side_effects_ready"] = True
            status["selected_status_side_effects_case_count"] = int(
                selected_status_proof.get("case_count", 0) or 0
            )
    oracle_only = payload.get("oracle_only_cases", [])
    if not isinstance(oracle_only, list):
        status["errors"].append("oracle_only_cases is not a list")
    else:
        status["oracle_only_case_count"] = len(oracle_only)
        oracle_only_residuals: list[str] = []
        for case in oracle_only:
            if not isinstance(case, dict):
                status["errors"].append("oracle_only case is not an object")
                continue
            if case.get("rom_backed") is not False:
                status["errors"].append(f"oracle-only case is not explicitly non-ROM-backed: {case}")
            if not str(case.get("reason_not_rom_backed", "") or ""):
                status["errors"].append(f"oracle-only case missing reason_not_rom_backed: {case}")
            mutation_id = str(case.get("mutation_id", "") or "")
            if mutation_id == "full_damage_variation_rng_distribution":
                oracle_only_residuals.append(DAMAGE_REMAINING_RNG_DISTRIBUTION_CAMPAIGN_GAP)
            elif mutation_id == "species_wide_eviolite_fuzz":
                oracle_only_residuals.append(DAMAGE_REMAINING_SPECIES_WIDE_EVIOLITE_CAMPAIGN_GAP)
            elif mutation_id == "full_battle_status_side_effects":
                if not status["selected_status_side_effects_ready"]:
                    oracle_only_residuals.append(DAMAGE_REMAINING_FULL_BATTLE_STATUS_SIDE_EFFECT_CAMPAIGN_GAP)
        status["oracle_only_residual_gaps"] = sorted(set(oracle_only_residuals))
        expected_oracle_residuals = set()
        if not status["selected_status_side_effects_ready"]:
            expected_oracle_residuals.add(DAMAGE_REMAINING_FULL_BATTLE_STATUS_SIDE_EFFECT_CAMPAIGN_GAP)
        if not status["rng_distribution_ready"]:
            expected_oracle_residuals.add(DAMAGE_REMAINING_RNG_DISTRIBUTION_CAMPAIGN_GAP)
        if not status["species_wide_eviolite_ready"]:
            expected_oracle_residuals.add(DAMAGE_REMAINING_SPECIES_WIDE_EVIOLITE_CAMPAIGN_GAP)
        missing_oracle_residuals = sorted(expected_oracle_residuals - set(status["oracle_only_residual_gaps"]))
        if missing_oracle_residuals:
            status["errors"].append(f"oracle_only_cases missing residual gaps: {missing_oracle_residuals}")
    remaining_residual_gaps = [
        gap
        for gap in DAMAGE_MUTATION_REMAINING_RESIDUAL_GAPS
        if gap != DAMAGE_REMAINING_RNG_DISTRIBUTION_CAMPAIGN_GAP or not status["rng_distribution_ready"]
        if gap != DAMAGE_REMAINING_SPECIES_WIDE_EVIOLITE_CAMPAIGN_GAP or not status["species_wide_eviolite_ready"]
        if gap != DAMAGE_REMAINING_FULL_BATTLE_STATUS_SIDE_EFFECT_CAMPAIGN_GAP or not status["selected_status_side_effects_ready"]
        if gap != DAMAGE_REMAINING_AUTO_MINIMIZED_DIVERGENCE_ARTIFACTS_GAP or not status["auto_minimized_divergence_ready"]
    ]
    status["remaining_residual_gaps"] = remaining_residual_gaps

    hash_basis = payload.get("hash_basis")
    if isinstance(hash_basis, dict):
        status["hash_basis"] = {
            "rom_sha256": str(hash_basis.get("rom_sha256", "") or ""),
            "symbols_sha256": str(hash_basis.get("symbols_sha256", "") or ""),
        }
        basis_errors = hash_basis.get("errors", [])
        if basis_errors:
            status["errors"].append(f"hash basis errors: {basis_errors}")
    elif (root / "pokegold_debug.gbc").exists() or (root / "pokegold_debug.sym").exists():
        status["errors"].append("missing hash_basis")
        hash_basis = {}
    else:
        hash_basis = {}
    for field, dependency in (
        ("rom_sha256", root / "pokegold_debug.gbc"),
        ("symbols_sha256", root / "pokegold_debug.sym"),
    ):
        if not dependency.exists():
            continue
        actual = sha256_file(dependency)
        recorded = str(hash_basis.get(field, "") or "")
        if not recorded:
            status["errors"].append(f"hash_basis.{field} is missing")
        elif recorded.upper() != actual.upper():
            status["errors"].append(f"hash_basis.{field} does not match current proof input")

    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "damage_debugger" / "mutation_campaign.py",
        root / "tools" / "damage_debugger" / "fuzz.py",
        root / "tools" / "damage_debugger" / "oracle.py",
        root / "tools" / "damage_debugger" / "clobber_smoke.py",
        root / "tools" / "damage_debugger" / "replay.py",
        root / "tools" / "damage_debugger" / "minimize.py",
        root / "tools" / "damage_debugger" / "taint.py",
        root / "tools" / "damage_debugger" / "find.py",
        root / "tools" / "headless_battle" / "rom_differential.py",
        root / "tools" / "headless_battle" / "simulator.py",
        root / "tools" / "damage_debugger" / "cap_add_probe.py",
        root / "tools" / "damage_debugger" / "safe_call.py",
        root / "constants" / "pokemon_constants.asm",
        root / "data" / "pokemon" / "evos_attacks_pointers.asm",
        root / "data" / "pokemon" / "evos_attacks.asm",
        root / "engine" / "battle" / "late_gen_held_items.asm",
        root / "pokegold_debug.gbc",
        root / "pokegold_debug.sym",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > artifact_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("damage mutation campaign artifact is older than proof inputs")
    status["ready"] = not status["errors"]
    if status["ready"]:
        status["closed_evidence_ids"] = [
            DAMAGE_MUTATION_CAMPAIGN_EVIDENCE_ID,
            *[
                DAMAGE_MUTATION_CAMPAIGN_EVIDENCE_IDS[campaign]
                for campaign in DAMAGE_MUTATION_REQUIRED_CAMPAIGNS
                if status["campaign_proofs"].get(campaign, {}).get("ready")
            ],
        ]
        if status["rng_distribution_ready"]:
            status["closed_evidence_ids"].append(DAMAGE_MUTATION_RNG_DISTRIBUTION_EVIDENCE_ID)
        if status["species_wide_eviolite_ready"]:
            status["closed_evidence_ids"].append(DAMAGE_MUTATION_SPECIES_WIDE_EVIOLITE_EVIDENCE_ID)
        if status["auto_minimized_divergence_ready"]:
            status["closed_evidence_ids"].append(DAMAGE_MUTATION_AUTO_MINIMIZED_DIVERGENCE_EVIDENCE_ID)
        if status["selected_status_side_effects_ready"]:
            status["closed_evidence_ids"].append(DAMAGE_MUTATION_SELECTED_STATUS_SIDE_EFFECTS_EVIDENCE_ID)
    return status


def damage_selected_status_side_effects_proof_errors(proof: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(proof, dict):
        return ["missing selected_status_side_effects_proof"]
    if proof.get("kind") != "damage_debugger_selected_status_side_effects_rom_components":
        errors.append(f"unexpected selected_status_side_effects_proof kind: {proof.get('kind', '')}")
    if proof.get("schema_version") != 1:
        errors.append("selected_status_side_effects_proof schema_version mismatch")
    if proof.get("evidence_id") != DAMAGE_MUTATION_SELECTED_STATUS_SIDE_EFFECTS_EVIDENCE_ID:
        errors.append("selected_status_side_effects_proof has wrong evidence_id")
    if proof.get("proof_status") != "complete":
        errors.append(f"unexpected selected_status_side_effects_proof status: {proof.get('proof_status', '')}")
    if proof.get("rom_backed") is not True:
        errors.append("selected_status_side_effects_proof is not ROM-backed")
    source = str(proof.get("source", "") or "")
    if source != "tools.headless_battle.rom_differential":
        errors.append("selected_status_side_effects_proof source mismatch")
    component_ids = {str(item) for item in proof.get("component_differential_ids", [])}
    for component_id in ("damaging_status_component_differential", "full_restore_status_cure_component_differential"):
        if component_id not in component_ids:
            errors.append(f"selected_status_side_effects_proof missing component differential {component_id}")
    required_case_ids = [str(item) for item in proof.get("required_case_ids", [])]
    missing_required = [
        case_id
        for case_id in DAMAGE_MUTATION_SELECTED_STATUS_SIDE_EFFECT_CASE_IDS
        if case_id not in required_case_ids
    ]
    if missing_required:
        errors.append(f"selected_status_side_effects_proof required_case_ids missing {missing_required}")
    cases = proof.get("cases", {})
    if not isinstance(cases, dict):
        errors.append("selected_status_side_effects_proof cases is not an object")
        cases = {}
    missing_cases = [
        case_id
        for case_id in DAMAGE_MUTATION_SELECTED_STATUS_SIDE_EFFECT_CASE_IDS
        if case_id not in cases
    ]
    if missing_cases:
        errors.append(f"selected_status_side_effects_proof missing cases {missing_cases}")
    for case_id in DAMAGE_MUTATION_SELECTED_STATUS_SIDE_EFFECT_CASE_IDS:
        row = cases.get(case_id, {})
        if not isinstance(row, dict):
            errors.append(f"{case_id}: selected status row is not an object")
            continue
        if row.get("rom_backed") is not True:
            errors.append(f"{case_id}: selected status row is not ROM-backed")
        if row.get("ok") is not True:
            errors.append(f"{case_id}: selected status row did not pass")
        component_id = str(row.get("component_differential_id", "") or "")
        if case_id.startswith("component_full_restore"):
            expected_component = "full_restore_status_cure_component_differential"
        else:
            expected_component = "damaging_status_component_differential"
        if component_id != expected_component:
            errors.append(f"{case_id}: component differential mismatch")
        if not isinstance(row.get("rom"), dict) or not row.get("rom"):
            errors.append(f"{case_id}: missing ROM evidence")
        if not isinstance(row.get("headless"), dict) or not row.get("headless"):
            errors.append(f"{case_id}: missing headless evidence")
    if int(proof.get("case_count", 0) or 0) != len(DAMAGE_MUTATION_SELECTED_STATUS_SIDE_EFFECT_CASE_IDS):
        errors.append("selected_status_side_effects_proof case_count mismatch")
    if int(proof.get("pass_count", 0) or 0) != len(DAMAGE_MUTATION_SELECTED_STATUS_SIDE_EFFECT_CASE_IDS):
        errors.append("selected_status_side_effects_proof pass_count mismatch")
    if int(proof.get("fail_count", -1)) != 0:
        errors.append("selected_status_side_effects_proof fail_count must be zero")
    failures = proof.get("failures", [])
    if not isinstance(failures, list) or failures:
        errors.append("selected_status_side_effects_proof failures must be empty")
    return errors


def damage_auto_minimized_divergence_proof_errors(proof: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(proof, dict):
        return ["missing auto_minimized_divergence_proof"]
    if proof.get("kind") != "damage_debugger_auto_minimized_divergence_artifacts":
        errors.append(f"unexpected auto_minimized_divergence_proof kind: {proof.get('kind', '')}")
    if proof.get("schema_version") != 1:
        errors.append("auto_minimized_divergence_proof schema_version mismatch")
    if proof.get("evidence_id") != DAMAGE_MUTATION_AUTO_MINIMIZED_DIVERGENCE_EVIDENCE_ID:
        errors.append("auto_minimized_divergence_proof has wrong evidence_id")
    if proof.get("proof_status") != "complete":
        errors.append(f"unexpected auto_minimized_divergence_proof status: {proof.get('proof_status', '')}")
    if proof.get("route_proof_status") != "complete":
        errors.append("auto_minimized_divergence route proof is incomplete")
    if proof.get("route_proof_kind") != "synthetic_forced_divergence_over_rom_checked_case":
        errors.append("auto_minimized_divergence route proof kind mismatch")
    if int(proof.get("campaign_fail_count", -1)) != 0:
        errors.append("auto_minimized_divergence campaign_fail_count must be zero")
    if int(proof.get("real_divergence_count", -1)) != 0:
        errors.append("auto_minimized_divergence real_divergence_count must be zero")
    if int(proof.get("check_one_call_count", 0) or 0) <= 0:
        errors.append("auto_minimized_divergence proof did not run check_one")
    for field in ("initial_inputs", "minimized_inputs"):
        if not isinstance(proof.get(field), dict) or not proof.get(field):
            errors.append(f"auto_minimized_divergence missing {field}")
    story = proof.get("minimization_story", [])
    if not isinstance(story, list) or not story:
        errors.append("auto_minimized_divergence missing minimization_story")
    reduced_fields = proof.get("reduced_fields", [])
    preserved_fields = proof.get("preserved_fields", [])
    if not isinstance(reduced_fields, list) or not reduced_fields:
        errors.append("auto_minimized_divergence did not record reduced_fields")
    if not isinstance(preserved_fields, list) or not preserved_fields:
        errors.append("auto_minimized_divergence did not record preserved_fields")
    materialized_case = proof.get("materialized_case", {})
    if not isinstance(materialized_case, dict) or not materialized_case:
        errors.append("auto_minimized_divergence missing materialized_case")
    else:
        if materialized_case.get("kind") != "damage_debugger_materialized_divergence_case":
            errors.append("auto_minimized_divergence materialized_case kind mismatch")
        if materialized_case.get("synthetic_forced_divergence") is not True:
            errors.append("auto_minimized_divergence materialized_case is not marked synthetic_forced_divergence")
        if materialized_case.get("ok") is not False:
            errors.append("auto_minimized_divergence materialized_case must be a failing divergence case")
        if not isinstance(materialized_case.get("inputs"), dict) or not materialized_case.get("inputs"):
            errors.append("auto_minimized_divergence materialized_case missing inputs")
        for numeric_field in ("rom_damage", "oracle_damage", "forced_oracle_damage", "delta", "tolerance"):
            if not isinstance(materialized_case.get(numeric_field), int):
                errors.append(f"auto_minimized_divergence materialized_case missing numeric {numeric_field}")
        if (
            isinstance(materialized_case.get("delta"), int)
            and isinstance(materialized_case.get("tolerance"), int)
            and abs(materialized_case["delta"]) <= materialized_case["tolerance"]
        ):
            errors.append("auto_minimized_divergence materialized_case delta is within tolerance")
    artifacts = proof.get("materialized_artifacts", [])
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("auto_minimized_divergence missing materialized_artifacts")
    else:
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                errors.append("auto_minimized_divergence materialized artifact is not an object")
                continue
            if not str(artifact.get("path", "") or ""):
                errors.append("auto_minimized_divergence materialized artifact missing path")
            sha = str(artifact.get("sha256", "") or "")
            if len(sha) != 64:
                errors.append("auto_minimized_divergence materialized artifact sha256 invalid")
    recorded_hash = str(proof.get("materialized_case_sha256", "") or "")
    if len(recorded_hash) != 64:
        errors.append("auto_minimized_divergence materialized_case_sha256 invalid")
    commands = proof.get("commands", {})
    if not isinstance(commands, dict):
        errors.append("auto_minimized_divergence missing commands")
    else:
        for field, token in (
            ("minimize_command", "tools.damage_debugger.minimize"),
            ("replay_command", "tools.damage_debugger.replay"),
            ("taint_command", "taint"),
        ):
            command = str(commands.get(field, "") or "")
            if not command:
                errors.append(f"auto_minimized_divergence missing {field}")
            elif token not in command:
                errors.append(f"auto_minimized_divergence {field} does not invoke {token}")
    return errors


def damage_species_wide_eviolite_proof_errors(proof: Any, *, cases: list[Any], root: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(proof, dict):
        return ["missing species_wide_eviolite_proof"]
    if proof.get("kind") != "damage_debugger_species_wide_eviolite_fuzz":
        errors.append(f"unexpected species_wide_eviolite_proof kind: {proof.get('kind', '')}")
    if proof.get("evidence_id") != DAMAGE_MUTATION_SPECIES_WIDE_EVIOLITE_EVIDENCE_ID:
        errors.append("species_wide_eviolite_proof has wrong evidence_id")
    if proof.get("proof_status") != "complete":
        errors.append(f"unexpected species_wide_eviolite_proof status: {proof.get('proof_status', '')}")
    if proof.get("rom_backed") is not True:
        errors.append("species_wide_eviolite_proof is not ROM-backed")
    try:
        from tools.damage_debugger.mutation_campaign import load_species_evolution_catalog
        from tools.damage_debugger.oracle import HELD_EVOLITE
    except Exception as exc:  # noqa: BLE001
        return [*errors, f"species-wide Eviolite validators unavailable: {type(exc).__name__}: {exc}"]
    catalog = load_species_evolution_catalog(root=root)
    if not catalog:
        errors.append("species-wide Eviolite catalog is empty")
    expected_species = {
        int(item.get("species_id", 0)): item
        for item in catalog
        if int(item.get("species_id", 0) or 0) > 0
    }
    if int(proof.get("species_count", 0) or 0) != len(expected_species):
        errors.append("species_wide_eviolite_proof species_count mismatch")
    expected_case_count = len(expected_species) * 2
    if int(proof.get("expected_case_count", 0) or 0) != expected_case_count:
        errors.append("species_wide_eviolite_proof expected_case_count mismatch")
    expected_can_evolve_count = sum(1 for item in expected_species.values() if item.get("can_evolve"))
    if int(proof.get("can_evolve_species_count", 0) or 0) != expected_can_evolve_count:
        errors.append("species_wide_eviolite_proof can_evolve_species_count mismatch")
    species_rows = [
        case
        for case in cases
        if isinstance(case, dict) and case.get("species_wide_eviolite") is True
    ]
    if int(proof.get("case_count", 0) or 0) != len(species_rows):
        errors.append("species_wide_eviolite_proof case_count does not match rows")
    if len(species_rows) != expected_case_count:
        errors.append(f"species-wide Eviolite row count {len(species_rows)} != expected {expected_case_count}")
    seen: set[tuple[int, str]] = set()
    duplicate_keys: list[str] = []
    for row in species_rows:
        mutation_id = str(row.get("mutation_id", "") or "")
        inputs = row.get("inputs") if isinstance(row.get("inputs"), dict) else {}
        species_id = int(inputs.get("defender_species_id", row.get("species_id", 0)) or 0)
        axis = str(row.get("eviolite_axis", "") or "")
        key = (species_id, axis)
        if key in seen:
            duplicate_keys.append(f"{species_id}:{axis}")
        seen.add(key)
        if row.get("method") != "fuzz.check_one":
            errors.append(f"{mutation_id} is not a fuzz.check_one row")
        if row.get("rom_backed") is not True:
            errors.append(f"{mutation_id} is not ROM-backed")
        if row.get("ok") is not True:
            errors.append(f"{mutation_id} did not pass")
        if row.get("campaign_id") != "status_item_interactions":
            errors.append(f"{mutation_id} is not in status_item_interactions")
        if axis not in {"physical_defense", "special_defense"}:
            errors.append(f"{mutation_id} has invalid eviolite_axis: {axis}")
        expected_physical = axis == "physical_defense"
        if isinstance(inputs, dict) and inputs.get("is_physical") is not expected_physical:
            errors.append(f"{mutation_id} is_physical does not match axis")
        if isinstance(inputs, dict) and int(inputs.get("opponent_item", 0) or 0) != HELD_EVOLITE:
            errors.append(f"{mutation_id} opponent_item is not HELD_EVOLITE")
        species = expected_species.get(species_id)
        if species is None:
            errors.append(f"{mutation_id} has unknown defender_species_id {species_id}")
        else:
            expected_can_evolve = bool(species.get("can_evolve", False))
            if inputs.get("can_evolve_defender") is not expected_can_evolve:
                errors.append(f"{mutation_id} can_evolve_defender mismatch")
            if row.get("expected_can_evolve_defender") is not expected_can_evolve:
                errors.append(f"{mutation_id} expected_can_evolve_defender mismatch")
        for field in ("rom_damage", "oracle_damage", "delta", "tolerance"):
            if not isinstance(row.get(field), (int, float)):
                errors.append(f"{mutation_id} missing numeric {field}")
        if isinstance(row.get("delta"), (int, float)) and isinstance(row.get("tolerance"), (int, float)):
            if abs(row["delta"]) > row["tolerance"]:
                errors.append(f"{mutation_id} delta exceeds tolerance")
    if duplicate_keys:
        errors.append(f"duplicate species-wide Eviolite rows: {sorted(duplicate_keys)}")
    expected_keys = {
        (species_id, axis)
        for species_id in expected_species
        for axis in ("physical_defense", "special_defense")
    }
    missing_keys = sorted(expected_keys - seen)
    if missing_keys:
        errors.append(f"missing species-wide Eviolite rows: {missing_keys[:10]}")
    return errors


def damage_rng_distribution_proof_errors(proof: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(proof, dict):
        return ["missing rng_distribution_proof"]
    if proof.get("kind") != "damage_debugger_rng_distribution_proof":
        errors.append(f"unexpected rng_distribution_proof kind: {proof.get('kind', '')}")
    if proof.get("proof_status") != "complete":
        errors.append(f"unexpected rng_distribution_proof status: {proof.get('proof_status', '')}")
    if proof.get("evidence_id") != DAMAGE_MUTATION_RNG_DISTRIBUTION_EVIDENCE_ID:
        errors.append("rng_distribution_proof has wrong evidence_id")
    if proof.get("rom_backed") is not True:
        errors.append("rng_distribution_proof is not ROM-backed")
    if int(proof.get("base_damage", 0) or 0) != 255:
        errors.append("rng_distribution_proof base_damage must be 255")
    expected_multipliers = list(range(217, 256))
    if proof.get("expected_multipliers") != expected_multipliers:
        errors.append("rng_distribution_proof expected_multipliers must cover 217..255")
    if proof.get("observed_multipliers") != expected_multipliers:
        errors.append("rng_distribution_proof observed_multipliers must cover 217..255")
    cases = proof.get("cases", [])
    if not isinstance(cases, list):
        errors.append("rng_distribution_proof cases is not a list")
        cases = []
    if int(proof.get("case_count", 0) or 0) != len(cases):
        errors.append("rng_distribution_proof case_count does not match cases")
    if int(proof.get("case_count", 0) or 0) < len(expected_multipliers) + 1:
        errors.append("rng_distribution_proof is missing accepted or rejection-loop cases")
    if int(proof.get("fail_count", 0) or 0) != 0:
        errors.append("rng_distribution_proof has failures")
    if int(proof.get("pass_count", 0) or 0) != int(proof.get("case_count", 0) or 0):
        errors.append("rng_distribution_proof pass_count does not match case_count")
    accepted: set[int] = set()
    rejection_verified = False
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"rng_distribution_proof case {index} is not an object")
            continue
        case_id = str(case.get("case_id", f"<case {index}>") or f"<case {index}>")
        if case.get("rom_backed") is not True:
            errors.append(f"{case_id} is not ROM-backed")
        if case.get("ok") is not True:
            errors.append(f"{case_id} did not pass")
        if case.get("returned") is not True:
            errors.append(f"{case_id} did not return")
        if case.get("actual_damage") != case.get("expected_damage"):
            errors.append(f"{case_id} actual_damage does not match expected_damage")
        if case.get("rng_consumed") != case.get("expected_rng_consumed"):
            errors.append(f"{case_id} rng_consumed does not match expected_rng_consumed")
        if case.get("case_kind") == "accepted_multiplier":
            multiplier = case.get("expected_multiplier")
            if isinstance(multiplier, int):
                accepted.add(multiplier)
            if case.get("observed_multiplier") != multiplier:
                errors.append(f"{case_id} observed_multiplier does not match expected_multiplier")
        if case.get("case_kind") == "rejection_loop":
            rejection_verified = (
                case.get("expected_multiplier") == 217
                and case.get("actual_damage") == 217
                and case.get("rng_consumed") == 2
                and 216 in set(case.get("rejected_multipliers", []))
            )
    if accepted != set(expected_multipliers):
        errors.append("rng_distribution_proof accepted case set is incomplete")
    if proof.get("rejection_loop_verified") is not True or not rejection_verified:
        errors.append("rng_distribution_proof rejection loop is not verified")
    return errors


def damage_mutation_case_class_errors(
    case: dict[str, Any],
    *,
    validate_canonical_state_class: Any,
) -> list[str]:
    case_id = str(case.get("mutation_id", case.get("case_id", "<unknown>")) or "<unknown>")
    errors: list[str] = []
    canonical = case.get("canonical_state_class")
    if not isinstance(canonical, dict):
        return [f"{case_id} missing canonical_state_class"]
    if validate_canonical_state_class is None:
        return [f"{case_id} canonical_state_class validator unavailable"]
    validation_errors = validate_canonical_state_class(canonical)
    if validation_errors:
        errors.append(f"{case_id} invalid canonical_state_class: {validation_errors}")
    class_id = str(case.get("class_id", "") or "")
    class_fingerprint = str(case.get("class_fingerprint", "") or "")
    if not class_id:
        errors.append(f"{case_id} missing class_id")
    if class_id != canonical.get("class_id"):
        errors.append(f"{case_id} class_id does not match canonical_state_class.class_id")
    if class_fingerprint != canonical.get("class_fingerprint"):
        errors.append(f"{case_id} class_fingerprint does not match canonical_state_class.class_fingerprint")
    if canonical.get("surface") != "damage_debugger":
        errors.append(f"{case_id} canonical surface is not damage_debugger")
    if canonical.get("backend") != "pyboy":
        errors.append(f"{case_id} canonical backend is not pyboy")
    if canonical.get("proof_status") != "emulator_evidence":
        errors.append(f"{case_id} canonical proof_status is not emulator_evidence")
    public_facts = canonical.get("public_facts") if isinstance(canonical.get("public_facts"), dict) else {}
    if public_facts.get("mutation_id") != case_id:
        errors.append(f"{case_id} canonical public_facts.mutation_id mismatch")
    if public_facts.get("case_id") != case.get("case_id"):
        errors.append(f"{case_id} canonical public_facts.case_id mismatch")
    for field in ("campaign_id", "method", "rom_backed"):
        if public_facts.get(field) != case.get(field):
            errors.append(f"{case_id} canonical public_facts.{field} mismatch")
    surface_facts = canonical.get("surface_facts") if isinstance(canonical.get("surface_facts"), dict) else {}
    damage_facts = surface_facts.get("damage") if isinstance(surface_facts.get("damage"), dict) else {}
    if damage_facts.get("mutation_campaign") != "phase6_initial":
        errors.append(f"{case_id} canonical damage mutation_campaign mismatch")
    if damage_facts.get("campaign_id") != case.get("campaign_id"):
        errors.append(f"{case_id} canonical damage campaign_id mismatch")
    if damage_facts.get("method") != case.get("method"):
        errors.append(f"{case_id} canonical damage method mismatch")
    return errors


def headless_spikes_hazard_smoke_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "damage_debugger" / "hazard_smoke.log"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "case_count": 0,
        "missing_cases": [],
        "stale_dependencies": [],
        "errors": [],
        "next_command": "python -m tools.damage_debugger.hazard_smoke",
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        status["errors"].append(str(exc))
        return status

    lines = text.splitlines()
    found_cases = {
        case
        for case in HEADLESS_SPIKES_HAZARD_CASES
        if any(line.startswith(f"PASS {case}") for line in lines)
    }
    missing_cases = [
        case
        for case in HEADLESS_SPIKES_HAZARD_CASES
        if case not in found_cases
    ]
    status["case_count"] = len(found_cases)
    status["missing_cases"] = missing_cases
    if missing_cases:
        status["errors"].append(f"missing passed Spikes hazard cases: {missing_cases}")
    if "PASS: all hazard smoke cases matched expected state." not in text:
        status["errors"].append("hazard_smoke summary is not all-pass")

    try:
        log_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "damage_debugger" / "hazard_smoke.py",
        root / "engine" / "battle" / "move_effects" / "spikes.asm",
        root / "engine" / "battle" / "move_effects" / "rapid_spin.asm",
        root / "engine" / "battle" / "core.asm",
        root / "pokegold_debug.gbc",
        root / "pokegold_debug.sym",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > log_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("hazard_smoke log is older than Spikes hazard proof inputs")
    status["ready"] = not status["errors"]
    return status


def headless_component_rom_differential_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "headless_battle" / "rom_differential.json"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "scenario_count": 0,
        "pass_count": 0,
        "missing_scenarios": [],
        "stale_dependencies": [],
        "errors": [],
        "next_command": (
            "python -m tools.headless_battle.rom_differential "
            "--json-out audit\\headless_battle\\rom_differential.json"
        ),
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status
    if payload.get("kind") != "headless_battle_component_rom_differential":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    if payload.get("proof_status") != "complete":
        status["errors"].append(f"unexpected proof status: {payload.get('proof_status', '')}")
    if int(payload.get("fail_count", 0) or 0) != 0:
        status["errors"].append("ROM differential report has failures")
    results = payload.get("results", [])
    if not isinstance(results, list):
        results = []
        status["errors"].append("results is not a list")
    status["scenario_count"] = len(results)
    passed = {
        str(result.get("scenario_id", ""))
        for result in results
        if isinstance(result, dict) and result.get("ok") is True
    }
    missing_scenarios = [
        scenario
        for scenario in HEADLESS_COMPONENT_ROM_DIFFERENTIALS
        if scenario not in passed
    ]
    status["missing_scenarios"] = missing_scenarios
    status["pass_count"] = len(passed)
    if missing_scenarios:
        status["errors"].append(f"missing passed component ROM differentials: {missing_scenarios}")
    for result in results:
        if not isinstance(result, dict):
            status["errors"].append("result row is not an object")
            continue
        if result.get("ok") is not True:
            status["errors"].append(f"{result.get('scenario_id', '<unknown>')} did not PASS")
        if not isinstance(result.get("rom", {}), dict) or not result.get("rom"):
            status["errors"].append(f"{result.get('scenario_id', '<unknown>')} missing ROM evidence")
        if not isinstance(result.get("headless", {}), dict) or not result.get("headless"):
            status["errors"].append(f"{result.get('scenario_id', '<unknown>')} missing headless evidence")

    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "headless_battle" / "rom_differential.py",
        root / "tools" / "headless_battle" / "simulator.py",
        root / "pokegold_debug.gbc",
        root / "pokegold_debug.sym",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > artifact_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("headless component ROM differential artifact is older than proof inputs")
    status["ready"] = not status["errors"]
    return status


def headless_promoted_turn_worklist_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "headless_battle" / "promoted_turn_differential_worklist.json"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "row_count": 0,
        "pending_turn_differential_count": 0,
        "missing_source_ids": [],
        "extra_source_ids": [],
        "duplicate_source_ids": [],
        "stale_dependencies": [],
        "errors": [],
        "next_command": (
            "python -m tools.headless_battle.promoted_turn_differential_worklist "
            "--json-out audit\\headless_battle\\promoted_turn_differential_worklist.json"
        ),
    }
    try:
        from tools.headless_battle.simulator import coverage_report
    except Exception as exc:  # noqa: BLE001
        status["errors"].append(f"could not load headless coverage report: {exc}")
        return status
    source_rows = coverage_report().get("source_mirrored_pending_differential", [])
    if not isinstance(source_rows, list):
        source_rows = []
        status["errors"].append("headless coverage source_mirrored_pending_differential is not a list")
    expected_by_id = {
        str(row.get("id", "")): row
        for row in source_rows
        if isinstance(row, dict) and str(row.get("id", ""))
    }
    expected_ids = list(expected_by_id)
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status
    if payload.get("kind") != "headless_battle_promoted_turn_differential_worklist":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    if payload.get("proof_status") != "worklist_only":
        status["errors"].append(f"unexpected proof status: {payload.get('proof_status', '')}")
    if payload.get("source") != "tools.headless_battle.simulator.coverage_report":
        status["errors"].append(f"unexpected source: {payload.get('source', '')}")
    if payload.get("source_path") != "tools/headless_battle/simulator.py":
        status["errors"].append(f"unexpected source_path: {payload.get('source_path', '')}")
    closed = payload.get("closed_evidence_ids", [])
    if closed != [HEADLESS_PROMOTED_TURN_WORKLIST_EVIDENCE_ID]:
        status["errors"].append("worklist must close only the narrow promoted-turn worklist evidence id")
    if HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP not in payload.get("missing_evidence", []):
        status["errors"].append("worklist missing_evidence must keep remaining turn differentials open")
    if HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP not in payload.get("blocking_gaps", []):
        status["errors"].append("worklist blocking_gaps must keep remaining turn differentials open")
    if HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP not in payload.get("does_not_close", []):
        status["errors"].append("worklist does_not_close must name remaining turn differentials")
    component = payload.get("component_rom_differentials", {})
    if not isinstance(component, dict):
        status["errors"].append("component_rom_differentials must be an object")
    elif component.get("path") != "audit/headless_battle/rom_differential.json":
        status["errors"].append("worklist must reference audit/headless_battle/rom_differential.json")

    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        rows = []
        status["errors"].append("rows is not a list")
    status["row_count"] = len(rows)
    status["pending_turn_differential_count"] = int(
        payload.get("pending_turn_differential_count", 0) or 0
    )
    if payload.get("row_count") != len(rows):
        status["errors"].append("row_count does not match rows length")
    if status["pending_turn_differential_count"] != len(rows):
        status["errors"].append("pending_turn_differential_count does not match rows length")

    seen_ids: set[str] = set()
    duplicate_ids: list[str] = []
    observed_ids: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            status["errors"].append("row is not an object")
            continue
        row_id = str(row.get("id", ""))
        observed_ids.append(row_id)
        if not row_id:
            status["errors"].append("row missing id")
            continue
        if row_id in seen_ids:
            duplicate_ids.append(row_id)
        seen_ids.add(row_id)
        expected = expected_by_id.get(row_id)
        if expected is None:
            continue
        if row.get("source") != expected.get("source"):
            status["errors"].append(f"{row_id} source does not match simulator coverage")
        if row.get("gate") != expected.get("gate"):
            status["errors"].append(f"{row_id} gate does not match simulator coverage")
        if not row.get("notes"):
            status["errors"].append(f"{row_id} missing notes")
        if row.get("proof_status") != "source_mirrored_pending_differential":
            status["errors"].append(f"{row_id} must remain source-mirrored pending differential")
        if row.get("turn_differential_status") != "pending_rom_turn_differential":
            status["errors"].append(f"{row_id} must remain pending ROM turn differential")
        if HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP not in row.get("blocking_gaps", []):
            status["errors"].append(f"{row_id} missing remaining turn differential blocker")
        if HEADLESS_REMAINING_PROMOTED_TURN_DIFFERENTIAL_GAP not in row.get("does_not_close", []):
            status["errors"].append(f"{row_id} missing does_not_close blocker")
        if row.get("closed_evidence_ids"):
            status["errors"].append(f"{row_id} must not close evidence from a pending worklist row")

    missing_source_ids = [row_id for row_id in expected_ids if row_id not in set(observed_ids)]
    extra_source_ids = [row_id for row_id in observed_ids if row_id and row_id not in expected_by_id]
    status["missing_source_ids"] = missing_source_ids
    status["extra_source_ids"] = extra_source_ids
    status["duplicate_source_ids"] = duplicate_ids
    if missing_source_ids:
        status["errors"].append(f"missing pending source rows: {missing_source_ids}")
    if extra_source_ids:
        status["errors"].append(f"extra pending source rows: {extra_source_ids}")
    if duplicate_ids:
        status["errors"].append(f"duplicate pending source rows: {duplicate_ids}")
    if not rows:
        status["errors"].append("worklist has no pending rows")

    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "headless_battle" / "simulator.py",
        root / "tools" / "headless_battle" / "promoted_turn_differential_worklist.py",
        root / "tools" / "headless_battle" / "README.md",
        root / "audit" / "headless_battle" / "rom_differential.json",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > artifact_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("headless promoted turn differential worklist is older than proof inputs")
    status["ready"] = not status["errors"]
    return status


def audio_apu_event_envelope_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "debugger_literal_anything" / "audio_apu_event_envelope.json"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "event_count": 0,
        "changed_register_count": 0,
        "static_channel_count": 0,
        "replay_diff_status": "",
        "runtime_kind": "",
        "stale_dependencies": [],
        "errors": [],
        "next_command": (
            "python -m tools.debugger replay --surface audio --at \"cry(species=TYPHLOSION)\" "
            "--frames 120 --json-out audit\\debugger_literal_anything\\audio_apu_event_envelope.json"
        ),
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status
    if payload.get("kind") != "debugger_deity_surface_replay":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    if payload.get("surface") != "audio":
        status["errors"].append(f"unexpected surface: {payload.get('surface', '')}")
    if not payload.get("valid"):
        status["errors"].append("audio replay report is not valid")
    replay_diff = payload.get("replay_diff", {})
    if not isinstance(replay_diff, dict):
        replay_diff = {}
        status["errors"].append("replay_diff is not an object")
    if replay_diff.get("kind") != "debugger_deity_audio_replay_diff":
        status["errors"].append(f"unexpected replay_diff kind: {replay_diff.get('kind', '')}")
    if not replay_diff.get("valid"):
        status["errors"].append("audio replay_diff is not valid")
    status["replay_diff_status"] = str(replay_diff.get("status", "") or "")
    if status["replay_diff_status"] != "matched_runtime_capture":
        status["errors"].append(f"unexpected audio replay_diff status: {status['replay_diff_status']}")
    static_channels = replay_diff.get("static_channels", [])
    if not isinstance(static_channels, list):
        static_channels = []
        status["errors"].append("replay_diff.static_channels is not a list")
    status["static_channel_count"] = len(static_channels)
    if status["static_channel_count"] <= 0:
        status["errors"].append("no source cry channels recorded in replay_diff")
    runtime = payload.get("runtime_replay", {})
    if not isinstance(runtime, dict):
        runtime = {}
        status["errors"].append("runtime_replay is not an object")
    status["runtime_kind"] = str(runtime.get("kind", "") or "")
    if status["runtime_kind"] != "debugger_deity_cry_apu_timeline":
        status["errors"].append(f"unexpected runtime_replay kind: {status['runtime_kind']}")
    events = runtime.get("runtime_events", [])
    if not isinstance(events, list):
        events = []
        status["errors"].append("runtime_events is not a list")
    status["event_count"] = len(events)
    status["changed_register_count"] = int(runtime.get("changed_register_count", 0) or 0)
    if status["event_count"] <= 0:
        status["errors"].append("no APU runtime_event_envelope events")
    if status["changed_register_count"] <= 0:
        status["errors"].append("no observed APU register changes")
    bad_events = [
        index
        for index, event in enumerate(events)
        if not isinstance(event, dict)
        or event.get("kind") != "runtime_event_envelope"
        or event.get("event_kind") != "hardware_event"
        or event.get("observation_type") != "explicit_hardware_event"
        or event.get("proof_status") != "runtime_observed"
    ]
    if bad_events:
        status["errors"].append(f"invalid APU runtime events at indexes: {bad_events[:5]}")

    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "debugger" / "deity_runtime.py",
        root / "tools" / "debugger" / "runtime_event.py",
        root / "audio" / "cries.asm",
        root / "pokegold.gbc",
        root / "pokegold.sym",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > artifact_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("audio APU event envelope is older than proof inputs")
    status["ready"] = not status["errors"]
    return status


def script_vm_event_log_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "debugger_literal_anything" / "script_vm_event_log.json"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "event_count": 0,
        "distinct_script_pos_count": 0,
        "stale_dependencies": [],
        "errors": [],
        "next_command": (
            "python -m tools.debugger replay --surface script --at "
            "\"map=ELMS_LAB and script=ProfElmScript\" --frames 120 "
            "--json-out audit\\debugger_literal_anything\\script_vm_event_log.json"
        ),
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status
    if payload.get("kind") != "debugger_deity_surface_replay":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    if payload.get("surface") != "script":
        status["errors"].append(f"unexpected surface: {payload.get('surface', '')}")
    if not payload.get("valid"):
        status["errors"].append("script replay report is not valid")
    static_mirror = payload.get("static_mirror", {})
    if not isinstance(static_mirror, dict):
        static_mirror = {}
        status["errors"].append("static_mirror is not an object")
    if int(static_mirror.get("command_count", 0) or 0) <= 0:
        status["errors"].append("static script command stream is empty")
    runtime = payload.get("runtime_replay", {})
    if not isinstance(runtime, dict):
        runtime = {}
        status["errors"].append("runtime_replay is not an object")
    events = runtime.get("runtime_events", [])
    if not isinstance(events, list):
        events = []
        status["errors"].append("runtime_events is not a list")
    status["event_count"] = len(events)
    status["distinct_script_pos_count"] = int(runtime.get("distinct_script_pos_count", 0) or 0)
    if status["event_count"] <= 0:
        status["errors"].append("no script VM runtime_event_envelope events")
    if status["distinct_script_pos_count"] <= 0:
        status["errors"].append("no observed script pointer samples")
    bad_events = [
        index
        for index, event in enumerate(events)
        if not isinstance(event, dict)
        or event.get("kind") != "runtime_event_envelope"
        or event.get("event_kind") != "script_vm"
        or event.get("observation_type") != "frame_sample"
        or event.get("proof_status") != "runtime_observed"
    ]
    if bad_events:
        status["errors"].append(f"invalid script VM runtime events at indexes: {bad_events[:5]}")

    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "debugger" / "deity_runtime.py",
        root / "tools" / "debugger" / "runtime_event.py",
        root / "maps" / "ElmsLab.asm",
        root / "pokegold.gbc",
        root / "pokegold.sym",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > artifact_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("script VM event log is older than proof inputs")
    status["ready"] = not status["errors"]
    return status


def script_map_content_materializer_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "debugger_literal_anything" / "script_map_content_materializers.json"
    scenario_path = root / "audit" / "debugger_literal_anything" / "script_map_content_scenarios.jsonl"
    initial_corpus_ids, initial_corpus_errors = script_entry_corpus_scenario_ids(
        scenario_path,
        root=root,
    )
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "scenario_path": display_path(scenario_path, root=root),
        "ready": False,
        "exists": path.exists(),
        "scenario_count": 0,
        "materialization_count": 0,
        "patch_count": 0,
        "ready_materialization_count": 0,
        "executed": False,
        "callback_script_entry_materializer_ready": False,
        "callback_script_entry_corpus_ready": False,
        "callback_script_entry_corpus_expected_count": 0,
        "callback_script_entry_corpus_ready_count": 0,
        "callback_script_entry_corpus_scenario_ids": [],
        "callback_script_entry_corpus_missing_scenario_ids": [],
        "warp_object_position_materializers_ready": False,
        "object_struct_visibility_materializers_ready": False,
        "object_struct_visibility_scenario_ids": [],
        "object_struct_visibility_patch_symbols": [],
        "object_struct_visibility_errors": [],
        "canonical_state_class_materializers_ready": False,
        "callback_script_entry_patch_symbols": [],
        "warp_object_position_scenario_ids": [],
        "canonical_state_class_ids": {},
        "canonical_state_class_errors": [],
        "missing_scenarios": [],
        "stale_dependencies": [],
        "errors": [],
        "next_command": script_map_content_materializer_command(initial_corpus_ids),
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status
    if payload.get("kind") != "unified_debugger_content_state_materialization":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    if payload.get("valid") is not True:
        status["errors"].append("content-state materializer report is not valid")
    status["executed"] = payload.get("executed") is True
    execution = payload.get("execution", {})
    if not isinstance(execution, dict):
        execution = {}
        status["errors"].append("execution is not an object")
    if status["executed"]:
        out_state = str(payload.get("out_state") or execution.get("out_state") or "")
        runtime_events = payload.get("runtime_events", execution.get("runtime_events", []))
        if not out_state:
            status["errors"].append("executed materializer report is missing output state")
        if not isinstance(runtime_events, list) or not runtime_events:
            status["errors"].append("executed materializer report is missing runtime evidence")
    status["scenario_count"] = int(payload.get("scenario_count", 0) or 0)
    status["materialization_count"] = int(payload.get("materialization_count", 0) or 0)
    status["patch_count"] = int(payload.get("patch_count", 0) or 0)
    input_scenario_ids = {
        str(item)
        for item in payload.get("input_scenario_ids", [])
        if item is not None
    }
    missing_scenarios = [
        scenario_id
        for scenario_id in SCRIPT_MAP_CONTENT_MATERIALIZER_SCENARIOS
        if scenario_id not in input_scenario_ids
    ]
    status["missing_scenarios"] = missing_scenarios
    if missing_scenarios:
        status["errors"].append(f"missing selected script/map materializer scenarios: {missing_scenarios}")
    materializations = payload.get("materializations", [])
    if not isinstance(materializations, list):
        materializations = []
        status["errors"].append("materializations is not a list")
    by_id = {
        str(item.get("scenario_id", "")): item
        for item in materializations
        if isinstance(item, dict)
    }
    canonical_class_ids: dict[str, str] = {}
    canonical_class_errors: list[str] = []
    ready_count = 0
    try:
        from tools.debugger.canonical_state_class import validate_canonical_state_class
    except Exception as exc:  # noqa: BLE001
        validate_canonical_state_class = None
        status["errors"].append(f"canonical state-class validator unavailable: {type(exc).__name__}: {exc}")
    for scenario_id, (scenario_type, precondition_kind) in SCRIPT_MAP_CONTENT_MATERIALIZER_SCENARIOS.items():
        materialization = by_id.get(scenario_id)
        if not materialization:
            status["errors"].append(f"{scenario_id} missing materialization row")
            continue
        if materialization.get("status") != "ready":
            status["errors"].append(f"{scenario_id} materialization is not ready")
        else:
            ready_count += 1
        if materialization.get("scenario_type") != scenario_type:
            status["errors"].append(f"{scenario_id} expected scenario_type {scenario_type}")
        if materialization.get("precondition_kind") != precondition_kind:
            status["errors"].append(f"{scenario_id} expected precondition_kind {precondition_kind}")
        if int(materialization.get("patch_count", 0) or 0) <= 0:
            status["errors"].append(f"{scenario_id} has no concrete WRAM patches")
        row_canonical_errors = selected_content_materializer_class_errors(
            materialization,
            scenario_id=scenario_id,
            scenario_type=scenario_type,
            precondition_kind=precondition_kind,
            validate_canonical_state_class=validate_canonical_state_class,
        )
        if row_canonical_errors:
            canonical_class_errors.extend(row_canonical_errors)
            status["errors"].extend(row_canonical_errors)
        else:
            canonical_class_ids[scenario_id] = str(materialization.get("class_id", ""))
    status["canonical_state_class_ids"] = canonical_class_ids
    status["canonical_state_class_errors"] = canonical_class_errors
    status["canonical_state_class_materializers_ready"] = (
        len(canonical_class_ids) == len(SCRIPT_MAP_CONTENT_MATERIALIZER_SCENARIOS)
        and not canonical_class_errors
    )
    callback = by_id.get("content_scenario_1_0032", {})
    callback_symbols = sorted(
        str(patch.get("symbol", ""))
        for patch in callback.get("patches", [])
        if isinstance(patch, dict) and patch.get("symbol")
    ) if isinstance(callback, dict) else []
    status["callback_script_entry_patch_symbols"] = callback_symbols
    required_callback_symbols = {
        "wScriptBank",
        "wScriptPos",
        "wScriptPos+1",
        "wScriptRunning",
        "wScriptMode",
        "wScriptStackSize",
    }
    missing_callback_symbols = sorted(required_callback_symbols - set(callback_symbols))
    if missing_callback_symbols:
        status["errors"].append(f"callback script-entry materializer missing patches: {missing_callback_symbols}")
    status["callback_script_entry_materializer_ready"] = (
        isinstance(callback, dict)
        and callback.get("status") == "ready"
        and callback.get("scenario_type") == "script_command_stream"
        and callback.get("precondition_kind") == "script_entry"
        and callback.get("source_file") == "maps/AzaleaTown.asm"
        and not missing_callback_symbols
    )

    callback_corpus_ids = initial_corpus_ids
    callback_corpus_errors = initial_corpus_errors
    status["callback_script_entry_corpus_scenario_ids"] = callback_corpus_ids
    status["callback_script_entry_corpus_expected_count"] = len(callback_corpus_ids)
    status["errors"].extend(callback_corpus_errors)
    callback_corpus_missing = [
        scenario_id
        for scenario_id in callback_corpus_ids
        if scenario_id not in input_scenario_ids or scenario_id not in by_id
    ]
    callback_corpus_bad: list[str] = []
    callback_corpus_ready_count = 0
    for scenario_id in callback_corpus_ids:
        materialization = by_id.get(scenario_id, {})
        if not isinstance(materialization, dict):
            callback_corpus_bad.append(scenario_id)
            continue
        symbols = {
            str(patch.get("symbol", ""))
            for patch in materialization.get("patches", [])
            if isinstance(patch, dict) and patch.get("symbol")
        }
        if (
            materialization.get("status") == "ready"
            and materialization.get("scenario_type") == "script_command_stream"
            and materialization.get("precondition_kind") == "script_entry"
            and not (required_callback_symbols - symbols)
        ):
            callback_corpus_ready_count += 1
        else:
            callback_corpus_bad.append(scenario_id)
    status["callback_script_entry_corpus_ready_count"] = callback_corpus_ready_count
    status["callback_script_entry_corpus_missing_scenario_ids"] = callback_corpus_missing
    if callback_corpus_errors:
        status["callback_script_entry_corpus_ready"] = False
    elif not callback_corpus_ids:
        status["errors"].append("script-entry materializer corpus has no scenario ids")
    elif callback_corpus_missing:
        status["errors"].append(
            f"script-entry materializer corpus missing scenarios: {callback_corpus_missing}"
        )
    elif callback_corpus_bad:
        status["errors"].append(f"script-entry materializer corpus invalid rows: {callback_corpus_bad}")
    else:
        status["callback_script_entry_corpus_ready"] = True

    position_patch_symbols = {"wMapGroup", "wMapNumber", "wXCoord", "wYCoord"}
    position_ids: list[str] = []
    position_errors: list[str] = []
    for scenario_id, scenario_type in (
        ("content_scenario_1_0000", "map_warp"),
        ("content_scenario_1_0019", "map_object_event"),
    ):
        materialization = by_id.get(scenario_id, {})
        symbols = {
            str(patch.get("symbol", ""))
            for patch in materialization.get("patches", [])
            if isinstance(materialization, dict)
            and isinstance(patch, dict)
            and patch.get("symbol")
        } if isinstance(materialization, dict) else set()
        if (
            isinstance(materialization, dict)
            and materialization.get("status") == "ready"
            and materialization.get("scenario_type") == scenario_type
            and materialization.get("precondition_kind") == "map_position"
            and symbols == position_patch_symbols
        ):
            position_ids.append(scenario_id)
        else:
            position_errors.append(scenario_id)
    status["warp_object_position_scenario_ids"] = position_ids
    status["warp_object_position_materializers_ready"] = not position_errors
    if position_errors:
        status["errors"].append(f"selected warp/object position materializers invalid: {position_errors}")
    object_visibility = (
        by_id.get("content_scenario_1_0019", {}).get("object_visibility_materializer")
        if isinstance(by_id.get("content_scenario_1_0019", {}), dict)
        else None
    )
    object_visibility_errors = selected_object_visibility_materializer_errors(object_visibility)
    status["object_struct_visibility_errors"] = object_visibility_errors
    if not object_visibility_errors and isinstance(object_visibility, dict):
        status["object_struct_visibility_materializers_ready"] = True
        status["object_struct_visibility_scenario_ids"] = ["content_scenario_1_0019"]
        status["object_struct_visibility_patch_symbols"] = sorted(
            str(patch.get("symbol", ""))
            for patch in object_visibility.get("patches", [])
            if isinstance(patch, dict) and patch.get("symbol")
        )
    status["ready_materialization_count"] = ready_count
    if status["patch_count"] < 14:
        status["errors"].append("selected script/map materializers have fewer than 14 WRAM patches")

    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        scenario_path,
        root / "tools" / "debugger" / "content_state.py",
        root / "tools" / "debugger" / "content_scenarios.py",
        root / "maps" / "AzaleaTown.asm",
        root / "data" / "maps" / "maps.asm",
        root / "pokegold.sym",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > artifact_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("script/map content materializer artifact is older than proof inputs")
    status["ready"] = not status["errors"]
    return status


def script_map_content_runtime_replay_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "debugger_literal_anything" / "script_map_content_runtime_replays.json"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "case_count": 0,
        "runtime_event_count": 0,
        "validated_cases": [],
        "halt_negative_control_ready": False,
        "stale_dependencies": [],
        "errors": [],
        "next_command": (
            "python -m tools.debugger replay --surface content --frames 120 "
            "--json-out audit\\debugger_literal_anything\\script_map_content_runtime_replays.json"
        ),
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status

    if payload.get("kind") != "debugger_deity_surface_replay":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    if payload.get("surface") != "content":
        status["errors"].append(f"unexpected surface: {payload.get('surface', '')}")
    if payload.get("valid") is not True:
        status["errors"].append("script/map content runtime replay artifact is not valid")
    runtime = payload.get("runtime_replay", {})
    if not isinstance(runtime, dict):
        status["errors"].append("runtime_replay is not an object")
        runtime = {}
    if runtime.get("kind") != "debugger_deity_script_map_content_runtime_replays":
        status["errors"].append(f"unexpected runtime_replay kind: {runtime.get('kind', '')}")
    if runtime.get("valid") is not True:
        status["errors"].append("script/map content runtime replay stream is not valid")
    if runtime.get("backend") != "pyboy":
        status["errors"].append(f"unexpected script/map content runtime backend: {runtime.get('backend', '')}")
    limits = " ".join(
        str(item)
        for item in [
            *list_value(payload.get("known_limits")),
            *list_value(runtime.get("known_limits")),
        ]
    ).lower()
    for required_limit in ("direct", "helper", "not full overworld", "all map", "all object"):
        if required_limit not in limits:
            status["errors"].append(
                f"script/map content runtime artifact must explicitly limit claim scope: {required_limit}"
            )

    cases = runtime.get("cases", [])
    if not isinstance(cases, list):
        status["errors"].append("script/map content runtime cases is not a list")
        cases = []
    events = runtime.get("runtime_events", [])
    if not isinstance(events, list):
        status["errors"].append("script/map content runtime_events is not a list")
        events = []
    status["case_count"] = len(cases)
    status["runtime_event_count"] = len(events)
    case_by_id = {
        str(case.get("case_id", "")): case
        for case in cases
        if isinstance(case, dict)
    }

    warp = case_by_id.get("azalea_pokecenter_warp_runtime")
    if not warp:
        status["errors"].append("missing script/map content runtime case: azalea_pokecenter_warp_runtime")
    else:
        if warp.get("scenario_id") != "content_scenario_1_0000":
            status["errors"].append("azalea_pokecenter_warp_runtime scenario_id mismatch")
        if warp.get("transition_kind") != "warp_collision_dispatch":
            status["errors"].append("azalea_pokecenter_warp_runtime transition_kind mismatch")
        if warp.get("transition_observed") is not True:
            status["errors"].append("azalea_pokecenter_warp_runtime did not prove an observed runtime transition")
        if warp.get("carry_observed") is not True or warp.get("warp_check_carry") is not True:
            status["errors"].append("azalea_pokecenter_warp_runtime missing WarpCheck carry observation")
        helper_hits = dict_value(warp.get("helper_hits"))
        for helper in ("WarpCheck", "EnterMapWarp"):
            if int(helper_hits.get(helper, 0) or 0) <= 0:
                status["errors"].append(f"azalea_pokecenter_warp_runtime missing helper hit: {helper}")
        after_warp = dict_value(warp.get("after_warp_check"))
        expected_warp = {"wNextWarp": 1, "wNextMapGroup": 8, "wNextMapNumber": 1}
        for key, expected in expected_warp.items():
            if int(after_warp.get(key, -1) or -1) != expected:
                status["errors"].append(f"azalea_pokecenter_warp_runtime {key} mismatch")
        after_enter = dict_value(warp.get("after_enter_map_warp"))
        expected_enter = {"wWarpNumber": 1, "wMapGroup": 8, "wMapNumber": 1}
        for key, expected in expected_enter.items():
            if int(after_enter.get(key, -1) or -1) != expected:
                status["errors"].append(f"azalea_pokecenter_warp_runtime {key} mismatch")
        if str(warp.get("destination_resolved_map", "")) != "AzaleaPokecenter1F":
            status["errors"].append("azalea_pokecenter_warp_runtime destination map mismatch")
        status["validated_cases"].append("azalea_pokecenter_warp_runtime")

    obj = case_by_id.get("azalea_rocket_object_runtime")
    if not obj:
        status["errors"].append("missing script/map content runtime case: azalea_rocket_object_runtime")
    else:
        if obj.get("scenario_id") != "content_scenario_1_0019":
            status["errors"].append("azalea_rocket_object_runtime scenario_id mismatch")
        if obj.get("transition_kind") != "object_facing_script_dispatch":
            status["errors"].append("azalea_rocket_object_runtime transition_kind mismatch")
        if obj.get("transition_observed") is not True:
            status["errors"].append("azalea_rocket_object_runtime did not prove an observed runtime transition")
        if obj.get("carry_observed") is not True or obj.get("try_object_event_carry") is not True:
            status["errors"].append("azalea_rocket_object_runtime missing TryObjectEvent carry observation")
        helper_hits = dict_value(obj.get("helper_hits"))
        for helper in ("TryObjectEvent", "CheckFacingObject", "CallScript"):
            if int(helper_hits.get(helper, 0) or 0) <= 0:
                status["errors"].append(f"azalea_rocket_object_runtime missing helper hit: {helper}")
        after = dict_value(obj.get("after"))
        expected_after = {
            "wScriptBank": 0x48,
            "wScriptPosWord": 0x517C,
            "wScriptRunning": 0xFF,
            "hLastTalked": 2,
            "hObjectStructIndex": 1,
        }
        for key, expected in expected_after.items():
            if int(after.get(key, -1) or -1) != expected:
                status["errors"].append(f"azalea_rocket_object_runtime {key} mismatch")
        if str(obj.get("script_label", "")) != "AzaleaTownRocket1Script":
            status["errors"].append("azalea_rocket_object_runtime script_label mismatch")
        status["validated_cases"].append("azalea_rocket_object_runtime")

    event_cases: set[str] = set()
    required_cases = {"azalea_pokecenter_warp_runtime", "azalea_rocket_object_runtime"}
    for event in events:
        if not isinstance(event, dict):
            status["errors"].append("script/map content runtime event is not an object")
            continue
        validation = dict_value(event.get("validation"))
        case_id = str(validation.get("case_id", "") or "")
        event_cases.add(case_id)
        if event.get("kind") != "runtime_event_envelope":
            status["errors"].append(f"{case_id}: script/map content event is not a runtime_event_envelope")
        if event.get("event_kind") != "control_flow":
            status["errors"].append(f"{case_id}: script/map content event kind is not control_flow")
        if event.get("source_kind") != "pyboy_script_map_content_runtime":
            status["errors"].append(f"{case_id}: script/map content event source_kind mismatch")
        if event.get("source_report") != "debugger_deity_script_map_content_runtime_replays":
            status["errors"].append(f"{case_id}: script/map content event source_report mismatch")
        if event.get("proof_status") != "runtime_observed":
            status["errors"].append(f"{case_id}: script/map content event proof_status is not runtime_observed")
        if event.get("observation_type") != "instruction_pre_state":
            status["errors"].append(f"{case_id}: script/map content event observation_type is not instruction_pre_state")
        scope = dict_value(event.get("scope"))
        if scope.get("backend") != "pyboy" or scope.get("surface") != "script_map_content":
            status["errors"].append(f"{case_id}: script/map content event scope mismatch")
        if str(scope.get("scenario_id", "") or "") not in {"content_scenario_1_0000", "content_scenario_1_0019"}:
            status["errors"].append(f"{case_id}: script/map content event scenario scope mismatch")
        precision = dict_value(event.get("precision"))
        if precision.get("transition_observed") is not True:
            status["errors"].append(f"{case_id}: script/map content event missing transition_observed precision")
        if int(precision.get("helper_hit_count", 0) or 0) <= 0:
            status["errors"].append(f"{case_id}: script/map content event missing helper hit precision")
        if case_id not in required_cases:
            status["errors"].append(f"{case_id}: unexpected script/map content event case")
    for case_id in required_cases:
        if case_id not in event_cases:
            status["errors"].append(f"{case_id} missing runtime event envelope")

    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "audit" / "debugger_literal_anything" / "script_map_content_materializers.json",
        root / "tools" / "debugger" / "deity_runtime.py",
        root / "tools" / "debugger" / "runtime_event.py",
        root / "tools" / "debugger" / "parsers.py",
        root / "tools" / "debugger" / "content_state.py",
        root / "maps" / "AzaleaTown.asm",
        root / "data" / "maps" / "maps.asm",
        root / "pokegold.gbc",
        root / "pokegold.sym",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > artifact_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("script/map content runtime artifact is older than proof inputs")
    status["ready"] = not status["errors"]
    return status


def script_entry_corpus_scenario_ids(path: Path, *, root: Path = ROOT) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    if not path.exists():
        return [], [f"missing script/map content scenario corpus: {display_path(path, root=root)}"]
    scenario_ids: list[str] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"{display_path(path, root=root)}:{line_number}: {exc.msg}")
                    continue
                if not isinstance(row, dict):
                    errors.append(f"{display_path(path, root=root)}:{line_number}: scenario row is not an object")
                    continue
                if row.get("scenario_type") != "script_command_stream":
                    continue
                preconditions = row.get("state_preconditions", [])
                if not isinstance(preconditions, list):
                    continue
                if not any(
                    isinstance(precondition, dict) and precondition.get("kind") == "script_entry"
                    for precondition in preconditions
                ):
                    continue
                scenario_id = str(row.get("id", "") or "")
                if scenario_id:
                    scenario_ids.append(scenario_id)
    except OSError as exc:
        errors.append(str(exc))
    return sorted(set(scenario_ids)), errors


def script_map_content_materializer_command(corpus_scenario_ids: Sequence[str]) -> str:
    scenario_ids: list[str] = []
    for scenario_id in (
        "content_scenario_1_0000",
        "content_scenario_1_0019",
        *(corpus_scenario_ids or ("content_scenario_1_0032",)),
    ):
        if scenario_id not in scenario_ids:
            scenario_ids.append(scenario_id)
    args = [
        "python -m tools.debugger content-state",
        "--scenario audit\\debugger_literal_anything\\script_map_content_scenarios.jsonl",
        "--max-scenarios 80",
        *[f"--scenario-id {scenario_id}" for scenario_id in scenario_ids],
        "--json-out audit\\debugger_literal_anything\\script_map_content_materializers.json",
    ]
    return " ".join(args)


def selected_object_visibility_materializer_errors(visibility: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(visibility, dict):
        return ["content_scenario_1_0019 missing object_visibility_materializer"]
    if visibility.get("kind") != "object_struct_visibility_materializer":
        errors.append(f"unexpected object visibility kind: {visibility.get('kind', '')}")
    if visibility.get("status") != "ready":
        errors.append("object visibility materializer is not ready")
    if visibility.get("proof_status") != "static_synthetic":
        errors.append(f"unexpected object visibility proof_status: {visibility.get('proof_status', '')}")
    if visibility.get("source_file") != "maps/AzaleaTown.asm":
        errors.append("object visibility source_file mismatch")
    map_object_index = int(visibility.get("map_object_index", 0) or 0)
    object_struct_index = int(visibility.get("object_struct_index", 0) or 0)
    if map_object_index <= 1:
        errors.append("object visibility map_object_index must identify a non-player map object")
    if object_struct_index != 1:
        errors.append("object visibility object_struct_index must be 1")
    patches = visibility.get("patches", [])
    if not isinstance(patches, list):
        return [*errors, "object visibility patches is not a list"]
    if int(visibility.get("patch_count", 0) or 0) != len(patches):
        errors.append("object visibility patch_count does not match patches length")
    patch_values: dict[str, int] = {}
    for patch in patches:
        if not isinstance(patch, dict):
            errors.append("object visibility patch row is not an object")
            continue
        symbol = str(patch.get("symbol", "") or "")
        if not symbol:
            errors.append("object visibility patch missing symbol")
            continue
        if patch.get("errors"):
            errors.append(f"{symbol} has patch errors")
        patch_values[symbol] = int(patch.get("value", 0) or 0) & 0xFF
    map_prefix = f"wMap{map_object_index}Object"
    mask_symbol = f"wObjectMasks+{map_object_index}"
    required_symbols = {
        f"{map_prefix}StructID",
        f"{map_prefix}Sprite",
        f"{map_prefix}YCoord",
        f"{map_prefix}XCoord",
        f"{map_prefix}Movement",
        f"{map_prefix}Radius",
        f"{map_prefix}Hour1",
        f"{map_prefix}Hour2",
        f"{map_prefix}Type",
        f"{map_prefix}SightRange",
        f"{map_prefix}Script",
        f"{map_prefix}Script+1",
        f"{map_prefix}EventFlag",
        f"{map_prefix}EventFlag+1",
        "wObject1MapObjectIndex",
        "wObject1Sprite",
        "wObject1MovementType",
        "wObject1Flags",
        "wObject1Flags+1",
        "wObject1Palette",
        "wObject1Walking",
        "wObject1Direction",
        "wObject1StepType",
        "wObject1Action",
        "wObject1Facing",
        "wObject1MapX",
        "wObject1MapY",
        "wObject1LastMapX",
        "wObject1LastMapY",
        "wObject1InitX",
        "wObject1InitY",
        "wObject1Radius",
        "wObject1Range",
        mask_symbol,
    }
    missing_symbols = sorted(required_symbols - set(patch_values))
    if missing_symbols:
        errors.append(f"object visibility materializer missing patches: {missing_symbols}")
    source_values = visibility.get("source_values") if isinstance(visibility.get("source_values"), dict) else {}
    expected_values = {
        f"{map_prefix}StructID": object_struct_index,
        "wObject1MapObjectIndex": map_object_index,
        "wObject1Walking": 0xFF,
        "wObject1Facing": 0xFF,
        mask_symbol: 0,
    }
    source_x = source_values.get("x")
    source_y = source_values.get("y")
    if isinstance(source_x, int) and isinstance(source_y, int):
        map_x = (source_x + 4) & 0xFF
        map_y = (source_y + 4) & 0xFF
        expected_values.update(
            {
                f"{map_prefix}XCoord": map_x,
                f"{map_prefix}YCoord": map_y,
                "wObject1MapX": map_x,
                "wObject1MapY": map_y,
                "wObject1LastMapX": map_x,
                "wObject1LastMapY": map_y,
                "wObject1InitX": map_x,
                "wObject1InitY": map_y,
            }
        )
    for symbol, expected in expected_values.items():
        if symbol in patch_values and patch_values[symbol] != expected:
            errors.append(f"{symbol} expected {expected:02X}, got {patch_values[symbol]:02X}")
    for left, right in (
        ("wObject1Sprite", f"{map_prefix}Sprite"),
        ("wObject1MovementType", f"{map_prefix}Movement"),
        ("wObject1Range", f"{map_prefix}SightRange"),
    ):
        if left in patch_values and right in patch_values and patch_values[left] != patch_values[right]:
            errors.append(f"{left} does not match {right}")
    if not source_values.get("script"):
        errors.append("object visibility source script is missing")
    if not source_values.get("event_flag"):
        errors.append("object visibility source event_flag is missing")
    return errors


def selected_content_materializer_class_errors(
    materialization: dict[str, Any],
    *,
    scenario_id: str,
    scenario_type: str,
    precondition_kind: str,
    validate_canonical_state_class: Any,
) -> list[str]:
    errors: list[str] = []
    canonical = materialization.get("canonical_state_class")
    if not isinstance(canonical, dict):
        return [f"{scenario_id} missing canonical_state_class"]
    if validate_canonical_state_class is None:
        return [f"{scenario_id} canonical_state_class validator unavailable"]
    validation_errors = validate_canonical_state_class(canonical)
    if validation_errors:
        errors.append(f"{scenario_id} invalid canonical_state_class: {validation_errors}")
    class_id = str(materialization.get("class_id", "") or "")
    class_fingerprint = str(materialization.get("class_fingerprint", "") or "")
    if not class_id:
        errors.append(f"{scenario_id} missing class_id")
    if class_id != canonical.get("class_id"):
        errors.append(f"{scenario_id} class_id does not match canonical_state_class.class_id")
    if class_fingerprint != canonical.get("class_fingerprint"):
        errors.append(f"{scenario_id} class_fingerprint does not match canonical_state_class.class_fingerprint")
    if canonical.get("surface") != "content_state":
        errors.append(f"{scenario_id} canonical surface is not content_state")
    if canonical.get("backend") != "static":
        errors.append(f"{scenario_id} canonical backend is not static")
    public_facts = canonical.get("public_facts") if isinstance(canonical.get("public_facts"), dict) else {}
    if public_facts.get("scenario_id") != scenario_id:
        errors.append(f"{scenario_id} canonical public_facts.scenario_id mismatch")
    if public_facts.get("scenario_type") != scenario_type:
        errors.append(f"{scenario_id} canonical public_facts.scenario_type mismatch")
    if public_facts.get("precondition_kind") != precondition_kind:
        errors.append(f"{scenario_id} canonical public_facts.precondition_kind mismatch")
    surface_facts = canonical.get("surface_facts") if isinstance(canonical.get("surface_facts"), dict) else {}
    content_facts = surface_facts.get("content") if isinstance(surface_facts.get("content"), dict) else {}
    if content_facts.get("materialization_surface") != "content_state":
        errors.append(f"{scenario_id} canonical content materialization surface mismatch")
    if content_facts.get("precondition_kind") != precondition_kind:
        errors.append(f"{scenario_id} canonical content precondition_kind mismatch")
    return errors


def graphics_digest_parity_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "debugger_literal_anything" / "graphics_vram_oam_framebuffer_digest_parity.json"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "framebuffer": "",
        "vram0_sha256": "",
        "vram1_sha256": "",
        "oam_sha256": "",
        "stale_dependencies": [],
        "errors": [],
        "next_command": (
            "python -m tools.debugger replay --surface graphics --at \"map=ECRUTEAK_GYM\" "
            "--json-out audit\\debugger_literal_anything\\graphics_vram_oam_framebuffer_digest_parity.json"
        ),
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status
    if payload.get("kind") != "debugger_deity_surface_replay":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    if payload.get("surface") != "graphics":
        status["errors"].append(f"unexpected surface: {payload.get('surface', '')}")
    if not payload.get("valid"):
        status["errors"].append("graphics replay report is not valid")
    diff = payload.get("replay_diff", {})
    if not isinstance(diff, dict):
        diff = {}
        status["errors"].append("replay_diff is not an object")
    if diff.get("status") != "captured_framebuffer_vram_oam":
        status["errors"].append(f"unexpected replay diff status: {diff.get('status', '')}")
    status["framebuffer"] = str(diff.get("framebuffer", "") or "")
    status["vram0_sha256"] = str(diff.get("vram0_sha256", "") or "")
    status["vram1_sha256"] = str(diff.get("vram1_sha256", "") or "")
    status["oam_sha256"] = str(diff.get("oam_sha256", "") or "")
    for field in ("framebuffer", "vram0_sha256", "vram1_sha256", "oam_sha256"):
        if not status[field]:
            status["errors"].append(f"missing {field}")
    if not isinstance(diff.get("lcd_state", {}), dict) or not diff.get("lcd_state"):
        status["errors"].append("missing lcd_state")
    runtime = payload.get("runtime_replay", {})
    if not isinstance(runtime, dict):
        runtime = {}
        status["errors"].append("runtime_replay is not an object")
    if runtime.get("kind") != "unified_debugger_visual_snapshot":
        status["errors"].append(f"unexpected runtime replay kind: {runtime.get('kind', '')}")
    if runtime.get("proof_status") != "runtime_observed":
        status["errors"].append(f"unexpected runtime proof status: {runtime.get('proof_status', '')}")
    if runtime.get("hardware_behavior_proven") not in {False, None}:
        status["errors"].append("graphics digest artifact overclaims hardware behavior")
    surfaces = runtime.get("surfaces", [])
    if not isinstance(surfaces, list):
        surfaces = []
        status["errors"].append("runtime surfaces is not a list")
    surfaces_by_name = {
        str(surface.get("name", "")): surface
        for surface in surfaces
        if isinstance(surface, dict)
    }
    for surface_name in ("VRAM0", "VRAM1", "OAM"):
        surface = surfaces_by_name.get(surface_name)
        if not surface or not surface.get("sha256"):
            status["errors"].append(f"missing {surface_name} runtime surface digest")
    screen_frame = runtime.get("screen_frame", {})
    if not isinstance(screen_frame, dict) or not screen_frame.get("sha256"):
        status["errors"].append("missing screen frame digest")

    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "debugger" / "deity_runtime.py",
        root / "tools" / "debugger" / "visual_snapshot.py",
        root / "maps" / "EcruteakGym.asm",
        root / "pokegold.gbc",
        root / "pokegold.sym",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > artifact_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("graphics digest parity artifact is older than proof inputs")
    status["ready"] = not status["errors"]
    return status


def graphics_backend_label_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "debugger_literal_anything" / "graphics_crossemu_backend_preflight.json"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "requested_backends": [],
        "available_count": 0,
        "cross_backend_available_count": 0,
        "trusted_cross_backend_count": 0,
        "ready_for_cross_backend_diff": False,
        "blocking_reasons": [],
        "stale_dependencies": [],
        "errors": [],
        "next_command": (
            "python -m tools.debugger crossemu preflight "
            "--backends pyboy,vba-m,sameboy,gambatte "
            "--json-out audit\\debugger_literal_anything\\graphics_crossemu_backend_preflight.json"
        ),
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status
    if payload.get("kind") != "unified_debugger_crossemu_preflight":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    if not payload.get("valid"):
        status["errors"].append("crossemu preflight report is not valid")
    requested = payload.get("requested_backends", [])
    if not isinstance(requested, list):
        requested = []
        status["errors"].append("requested_backends is not a list")
    status["requested_backends"] = requested
    requested_set = {str(item) for item in requested}
    if "pyboy" not in requested_set:
        status["errors"].append("PyBoy backend label is missing")
    if not ({"vba-m", "sameboy", "gambatte"} & requested_set):
        status["errors"].append("no cross-emulator backend was requested")
    status["available_count"] = int(payload.get("available_count", 0) or 0)
    status["cross_backend_available_count"] = int(payload.get("cross_backend_available_count", 0) or 0)
    status["trusted_cross_backend_count"] = int(payload.get("trusted_cross_backend_count", 0) or 0)
    status["ready_for_cross_backend_diff"] = bool(payload.get("ready_for_cross_backend_diff", False))
    blocking_reasons = payload.get("blocking_reasons", [])
    if not isinstance(blocking_reasons, list):
        blocking_reasons = []
        status["errors"].append("blocking_reasons is not a list")
    status["blocking_reasons"] = blocking_reasons
    if not payload.get("ready_for_pyboy_run"):
        status["errors"].append("PyBoy is not available for the canonical graphics run")
    if status["ready_for_cross_backend_diff"]:
        status["errors"].append("backend label artifact must not stand in for cross-backend parity")
    if status["cross_backend_available_count"] > 0 or status["trusted_cross_backend_count"] > 0:
        status["errors"].append("backend label artifact found cross-backend availability; run parity proof instead")
    if "no cross-emulator backend is installed" not in {str(item) for item in blocking_reasons}:
        status["errors"].append("missing explicit no-cross-backend blocking reason")
    backends = payload.get("backends", [])
    if not isinstance(backends, list):
        backends = []
        status["errors"].append("backends is not a list")
    for backend in backends:
        if not isinstance(backend, dict):
            status["errors"].append("backend row is not an object")
            continue
        name = str(backend.get("name", ""))
        if name == "pyboy" and not backend.get("available"):
            status["errors"].append("PyBoy backend row is not available")
        if name in {"vba-m", "sameboy", "gambatte"} and backend.get("available"):
            status["errors"].append(f"{name} backend is available; label-only artifact is stale")

    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "debugger" / "crossemu.py",
        root / "tools" / "debugger" / "v2_passthrough.py",
        root / "audit" / "crossemu_conformance.jsonl",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > artifact_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("graphics backend label artifact is older than backend proof inputs")
    status["ready"] = not status["errors"]
    return status


def save_format_sram_bank_ownership_status(*, root: Path = ROOT) -> dict[str, Any]:
    status: dict[str, Any] = {
        "path": display_path(
            root / "tools" / "audit" / "data" / "save_format_fingerprints.json",
            root=root,
        ),
        "ready": False,
        "exists": (root / "tools" / "audit" / "data" / "save_format_fingerprints.json").exists(),
        "save_format_version": 0,
        "fingerprint_sha256": "",
        "expected_fingerprint_sha256": "",
        "sram_section_bank_map": {},
        "owned_section_count": 0,
        "errors": [],
        "next_command": "python tools\\audit\\check_save_format_version.py",
    }
    try:
        from tools.audit.check_save_format_version import (
            SRAM_SECTIONS_OF_INTEREST,
            compute_fingerprint,
            load_fingerprints,
            parse_version,
        )
    except Exception as exc:  # noqa: BLE001
        status["errors"].append(f"save-format checker unavailable: {type(exc).__name__}: {exc}")
        return status

    try:
        version = parse_version(root=root)
        digest, payload = compute_fingerprint(root=root)
        fingerprints = load_fingerprints(root=root)
    except SystemExit as exc:
        status["errors"].append(f"save-format checker failed: {exc}")
        return status
    except Exception as exc:  # noqa: BLE001
        status["errors"].append(f"save-format checker failed: {type(exc).__name__}: {exc}")
        return status

    status["save_format_version"] = version
    status["fingerprint_sha256"] = digest
    expected = str(fingerprints.get(str(version), "") or "")
    status["expected_fingerprint_sha256"] = expected
    if not expected:
        status["errors"].append(f"no recorded fingerprint for SAVE_FORMAT_VERSION={version}")
    elif expected != digest:
        status["errors"].append("save layout fingerprint does not match recorded SAVE_FORMAT_VERSION")

    expected_sections = tuple(str(item) for item in SRAM_SECTIONS_OF_INTEREST)
    sram_sections = payload.get("sram_sections", {})
    if not isinstance(sram_sections, dict):
        sram_sections = {}
        status["errors"].append("sram_sections fingerprint payload is not an object")
    missing_sections = [
        section
        for section in expected_sections
        if section not in sram_sections or not isinstance(sram_sections.get(section), list)
    ]
    if missing_sections:
        status["errors"].append(f"missing SRAM section fingerprints: {missing_sections}")

    sram_layout = payload.get("sram_layout", {})
    if not isinstance(sram_layout, dict):
        sram_layout = {}
        status["errors"].append("sram_layout fingerprint payload is not an object")
    section_bank_map: dict[str, str] = {}
    duplicate_sections: list[str] = []
    for bank, sections in sram_layout.items():
        if not isinstance(sections, list):
            status["errors"].append(f"SRAM bank {bank!r} layout is not a list")
            continue
        for section in sections:
            section_name = str(section)
            if section_name not in expected_sections:
                continue
            if section_name in section_bank_map:
                duplicate_sections.append(section_name)
                continue
            section_bank_map[section_name] = str(bank)
    layout_missing = [
        section
        for section in expected_sections
        if section not in section_bank_map
    ]
    if layout_missing:
        status["errors"].append(f"missing SRAM layout ownership entries: {layout_missing}")
    if duplicate_sections:
        status["errors"].append(f"duplicate SRAM layout ownership entries: {sorted(set(duplicate_sections))}")
    status["sram_section_bank_map"] = section_bank_map
    status["owned_section_count"] = len(section_bank_map)
    status["ready"] = not status["errors"]
    return status


def rtc_edge_case_source_anchor_status(*, root: Path = ROOT) -> dict[str, Any]:
    surface_index = root / "audit" / "debugger_literal_anything" / "rom_surface_index.jsonl"
    required_labels = {
        label
        for labels in RTC_SOURCE_ANCHOR_LABELS.values()
        for label in labels
    }
    status: dict[str, Any] = {
        "ready": False,
        "surface_index": display_path(surface_index, root=root),
        "source_file_count": len(RTC_SOURCE_ANCHOR_LABELS),
        "required_label_count": len(required_labels),
        "source_anchor_count": 0,
        "indexed_label_count": 0,
        "missing_source_labels": [],
        "missing_index_labels": [],
        "stale_dependencies": [],
        "errors": [],
        "next_command": (
            "python -m tools.debugger rom-index --surface-index-out "
            "audit\\debugger_literal_anything\\rom_surface_index.jsonl"
        ),
    }
    source_found: set[str] = set()
    for relative_path, labels in RTC_SOURCE_ANCHOR_LABELS.items():
        path = root / relative_path
        if not path.exists():
            status["errors"].append(f"missing RTC source file: {relative_path}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label in labels:
            if label in text:
                source_found.add(label)
    missing_source = sorted(required_labels - source_found)
    status["source_anchor_count"] = len(source_found)
    status["missing_source_labels"] = missing_source
    if missing_source:
        status["errors"].append(f"missing RTC source labels: {missing_source}")
    if not surface_index.exists():
        status["errors"].append("missing ROM surface index")
        return status

    indexed: set[str] = set()
    try:
        with surface_index.open(encoding="utf-8") as handle:
            for line in handle:
                if not any(label in line for label in required_labels - indexed):
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                nearest_label = str(row.get("nearest_label", "") or "")
                surface_id = str(row.get("surface_id", "") or "")
                for label in required_labels - indexed:
                    if nearest_label == label or surface_id.endswith(f":{label}"):
                        indexed.add(label)
                if required_labels <= indexed:
                    break
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    missing_index = sorted(required_labels - indexed)
    status["indexed_label_count"] = len(indexed)
    status["missing_index_labels"] = missing_index
    if missing_index:
        status["errors"].append(f"missing RTC labels from ROM surface index: {missing_index}")

    try:
        index_mtime = surface_index.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    stale: list[str] = []
    for relative_path in RTC_SOURCE_ANCHOR_LABELS:
        dependency = root / relative_path
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > index_mtime + 1:
                stale.append(relative_path)
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("RTC source anchors are newer than the ROM surface index")
    status["ready"] = not status["errors"]
    return status


def rtc_register_edge_runtime_replay_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "debugger_literal_anything" / "rtc_register_edge_runtime_replay.json"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "case_count": 0,
        "runtime_event_count": 0,
        "validated_cases": [],
        "stale_dependencies": [],
        "errors": [],
        "next_command": (
            "python -m tools.debugger replay --surface rtc --frames 5 "
            "--json-out audit\\debugger_literal_anything\\rtc_register_edge_runtime_replay.json"
        ),
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status

    if payload.get("kind") != "debugger_deity_surface_replay":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    if payload.get("surface") != "rtc":
        status["errors"].append(f"unexpected surface: {payload.get('surface', '')}")
    if payload.get("valid") is not True:
        status["errors"].append("RTC replay artifact is not valid")
    runtime = payload.get("runtime_replay", {})
    if not isinstance(runtime, dict):
        status["errors"].append("runtime_replay is not an object")
        runtime = {}
    if runtime.get("kind") != "debugger_deity_rtc_register_edge_runtime_replay":
        status["errors"].append(f"unexpected runtime_replay kind: {runtime.get('kind', '')}")
    if runtime.get("valid") is not True:
        status["errors"].append("RTC register edge stream is not valid")
    if runtime.get("backend") != "pyboy":
        status["errors"].append(f"unexpected RTC runtime backend: {runtime.get('backend', '')}")
    limits = " ".join(
        str(item)
        for item in [
            *list_value(payload.get("known_limits")),
            *list_value(runtime.get("known_limits")),
        ]
    ).lower()
    for required in ("halt semantics remain", "seeded day-overflow", "cross-backend"):
        if required not in limits:
            status["errors"].append(f"RTC runtime artifact must disclose limit: {required}")

    cases = runtime.get("cases", [])
    if not isinstance(cases, list):
        status["errors"].append("RTC runtime cases is not a list")
        cases = []
    events = runtime.get("runtime_events", [])
    if not isinstance(events, list):
        status["errors"].append("RTC runtime_events is not a list")
        events = []
    status["case_count"] = len(cases)
    status["runtime_event_count"] = len(events)
    case_by_id = {
        str(case.get("case_id", "")): case
        for case in cases
        if isinstance(case, dict)
    }
    required_cases = (
        "rtc_day_high_carry_register_write_readback",
        "rtc_halt_bit_readback_nonsemantic_control",
        "rtc_seeded_day_511_no_carry_readback",
        "rtc_seeded_day_512_carry_overflow_readback",
        "rtc_seeded_day_513_carry_overflow_readback",
    )
    halt_negative_control_case_ready = False
    for case_id in required_cases:
        case = case_by_id.get(case_id)
        if not case:
            status["errors"].append(f"missing RTC runtime case: {case_id}")
            continue
        case_ready = True
        if case.get("transition_observed") is not True:
            status["errors"].append(f"{case_id} did not prove an observed runtime transition")
            case_ready = False
        if case.get("halt_semantics_proven") is not False:
            status["errors"].append(f"{case_id} must not claim halt semantics proof")
            case_ready = False
        if case_id == "rtc_day_high_carry_register_write_readback":
            if case.get("carry_set_readback") is not True:
                status["errors"].append(f"{case_id} missing carry_set_readback")
                case_ready = False
            if case.get("carry_clear_readback") is not True:
                status["errors"].append(f"{case_id} missing carry_clear_readback")
                case_ready = False
        elif case_id == "rtc_halt_bit_readback_nonsemantic_control":
            if case.get("halt_bit_readback") is not True:
                status["errors"].append(f"{case_id} missing halt_bit_readback")
                case_ready = False
            if case.get("seconds_advanced_while_halt_bit_set") is not True:
                status["errors"].append(f"{case_id} must show PyBoy halt semantics are not proven")
                case_ready = False
            halt_negative_control_case_ready = case_ready
        else:
            if case.get("day_low_matches") is not True:
                status["errors"].append(f"{case_id} missing day_low_matches")
                case_ready = False
            if case.get("day_high_day_bit_matches") is not True:
                status["errors"].append(f"{case_id} missing day_high_day_bit_matches")
                case_ready = False
            if case.get("carry_matches") is not True:
                status["errors"].append(f"{case_id} missing carry_matches")
                case_ready = False
        status["validated_cases"].append(case_id)

    event_cases: set[str] = set()
    halt_negative_control_event_ready = False
    for event in events:
        if not isinstance(event, dict):
            status["errors"].append("RTC runtime event is not an object")
            continue
        case_id = str(event.get("validation", {}).get("case_id", "") or "")
        event_cases.add(case_id)
        if event.get("kind") != "runtime_event_envelope":
            status["errors"].append(f"{case_id}: RTC event is not a runtime_event_envelope")
        if event.get("event_kind") != "hardware_event":
            status["errors"].append(f"{case_id}: RTC event kind is not hardware_event")
        if event.get("proof_status") != "runtime_observed":
            status["errors"].append(f"{case_id}: RTC event proof_status is not runtime_observed")
        if event.get("observation_type") != "explicit_hardware_event":
            status["errors"].append(f"{case_id}: RTC event observation_type is not explicit_hardware_event")
        scope = event.get("scope", {}) if isinstance(event.get("scope"), dict) else {}
        if scope.get("backend") != "pyboy" or scope.get("surface") != "rtc":
            status["errors"].append(f"{case_id}: RTC event scope mismatch")
        precision = event.get("precision", {}) if isinstance(event.get("precision"), dict) else {}
        if precision.get("transition_observed") is not True:
            status["errors"].append(f"{case_id}: RTC event missing transition_observed precision")
        if precision.get("halt_semantics_proven") is not False:
            status["errors"].append(f"{case_id}: RTC event must not claim halt semantics proof")
        if case_id == "rtc_halt_bit_readback_nonsemantic_control":
            validation = event.get("validation", {}) if isinstance(event.get("validation"), dict) else {}
            payload_case = event.get("payload", {}) if isinstance(event.get("payload"), dict) else {}
            halt_negative_control_event_ready = (
                event.get("kind") == "runtime_event_envelope"
                and event.get("event_kind") == "hardware_event"
                and event.get("proof_status") == "runtime_observed"
                and event.get("observation_type") == "explicit_hardware_event"
                and scope.get("backend") == "pyboy"
                and scope.get("surface") == "rtc"
                and scope.get("rtc_transition") == "rtc_halt_bit_readback_nonsemantic_control"
                and validation.get("transition_kind") == "rtc_halt_bit_readback_nonsemantic_control"
                and precision.get("transition_observed") is True
                and precision.get("halt_semantics_proven") is False
                and payload_case.get("halt_bit_readback") is True
                and payload_case.get("seconds_advanced_while_halt_bit_set") is True
                and payload_case.get("halt_semantics_proven") is False
            )
    for case_id in required_cases:
        if case_id not in event_cases:
            status["errors"].append(f"{case_id} missing runtime event envelope")
    status["halt_negative_control_ready"] = (
        halt_negative_control_case_ready and halt_negative_control_event_ready
    )

    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "debugger" / "deity_runtime.py",
        root / "tools" / "debugger" / "runtime_event.py",
        root / "tools" / "debugger" / "parsers.py",
        root / "pokegold.gbc",
        root / "pokegold.sym",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > artifact_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("RTC runtime artifact is older than proof inputs")
    status["ready"] = not status["errors"]
    return status


def mbc_bank_transition_model_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        "ready": False,
        "probe_count": 0,
        "validated_semantics": [],
        "validated_transitions": [],
        "errors": [],
        "next_command": "python -m unittest tools.debugger.tests.test_effect_trace tools.debugger.tests.test_sm83_model",
    }
    try:
        from tools.debugger.effect_trace import apply_bank_write
        from tools.debugger.sm83_model import memory_write_hardware_trigger_semantics
    except Exception as exc:  # noqa: BLE001
        status["errors"].append(f"MBC model unavailable: {type(exc).__name__}: {exc}")
        return status

    expected_semantics = {
        0x0000: "mbc_ram_enable_write",
        0x2000: "mbc_rom_bank_select",
        0x4000: "mbc_ram_or_rom_upper_bank_select",
        0x6000: "mbc_mode_or_latch_write",
    }
    for address, expected_kind in expected_semantics.items():
        kinds = {
            item.kind
            for item in memory_write_hardware_trigger_semantics(address)
        }
        status["probe_count"] += 1
        if expected_kind not in kinds:
            status["errors"].append(f"address ${address:04X} missing semantic {expected_kind}")
        else:
            status["validated_semantics"].append(expected_kind)

    state: dict[str, int] = {}
    transition_probes = [
        (0x0000, 0x0A, "sram_enabled", 1),
        (0x0000, 0x00, "sram_enabled", 0),
        (0x2000, 0x00, "rom", 1),
        (0x2000, 0x22, "rom", 0x22),
        (0x4000, 0x02, "sram", 0x02),
        (0x4000, 0x08, "sram_rtc_select", 0x08),
    ]
    for address, value, key, expected in transition_probes:
        apply_bank_write(state, address=address, value=value)
        status["probe_count"] += 1
        if state.get(key) != expected:
            status["errors"].append(
                f"write ${address:04X}={value:02X} did not set {key}={expected}"
            )
        else:
            status["validated_transitions"].append(f"{key}={expected}")
    if "sram" in state and state.get("sram_rtc_select") == 0x08:
        status["errors"].append("RTC register select did not clear active SRAM bank selection")
    status["ready"] = not status["errors"]
    return status


def mbc_runtime_transition_replay_corpus_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "debugger_literal_anything" / "mbc_runtime_transition_replay_corpus.json"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "case_count": 0,
        "runtime_event_count": 0,
        "validated_cases": [],
        "stale_dependencies": [],
        "errors": [],
        "next_command": (
            "python -m tools.debugger replay --surface mbc --frames 20 "
            "--json-out audit\\debugger_literal_anything\\mbc_runtime_transition_replay_corpus.json"
        ),
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status

    if payload.get("kind") != "debugger_deity_surface_replay":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    if payload.get("surface") != "mbc":
        status["errors"].append(f"unexpected surface: {payload.get('surface', '')}")
    if payload.get("valid") is not True:
        status["errors"].append("MBC replay artifact is not valid")
    runtime = payload.get("runtime_replay", {})
    if not isinstance(runtime, dict):
        status["errors"].append("runtime_replay is not an object")
        runtime = {}
    if runtime.get("kind") != "debugger_deity_mbc_runtime_transition_replay_corpus":
        status["errors"].append(f"unexpected runtime_replay kind: {runtime.get('kind', '')}")
    if runtime.get("valid") is not True:
        status["errors"].append("MBC runtime transition stream is not valid")
    if runtime.get("backend") != "pyboy":
        status["errors"].append(f"unexpected MBC runtime backend: {runtime.get('backend', '')}")
    limits = " ".join(
        str(item)
        for item in [
            *list_value(payload.get("known_limits")),
            *list_value(runtime.get("known_limits")),
        ]
    ).lower()
    if "rtc halt" not in limits or "day-overflow" not in limits:
        status["errors"].append("MBC runtime artifact must explicitly leave RTC halt/carry/day-overflow open")
    cases = runtime.get("cases", [])
    if not isinstance(cases, list):
        status["errors"].append("MBC runtime cases is not a list")
        cases = []
    events = runtime.get("runtime_events", [])
    if not isinstance(events, list):
        status["errors"].append("MBC runtime_events is not a list")
        events = []
    status["case_count"] = len(cases)
    status["runtime_event_count"] = len(events)
    case_by_id = {
        str(case.get("case_id", "")): case
        for case in cases
        if isinstance(case, dict)
    }
    required_cases = {
        "mbc3_rom_bank_select_window": "rom_bank_select",
        "mbc3_sram_enable_disable": "sram_enable_disable",
        "mbc3_sram_bank_select_isolation": "sram_bank_select",
        "mbc3_rtc_register_select_latch": "rtc_register_select_latch",
    }
    for case_id, transition_kind in required_cases.items():
        case = case_by_id.get(case_id)
        if not case:
            status["errors"].append(f"missing MBC runtime case: {case_id}")
            continue
        if case.get("transition_kind") != transition_kind:
            status["errors"].append(f"{case_id} transition_kind mismatch")
        if case.get("transition_observed") is not True:
            status["errors"].append(f"{case_id} did not prove an observed runtime transition")
        if not str(case.get("write_range", "") or ""):
            status["errors"].append(f"{case_id} missing write_range")
        if case_id == "mbc3_rom_bank_select_window":
            if int(case.get("matched_bank_count", 0) or 0) < 4:
                status["errors"].append(f"{case_id} did not match enough ROM banks")
            if case.get("zero_select_maps_to_bank_one") is not True:
                status["errors"].append(f"{case_id} did not prove bank 0 maps to bank 1")
            if not all(dict_value(item).get("sample_match") is True for item in list_value(case.get("transitions"))):
                status["errors"].append(f"{case_id} has a ROM bank sample mismatch")
        elif case_id == "mbc3_sram_enable_disable":
            for field in (
                "enabled_readback_matches",
                "disabled_readback_open_bus",
                "disabled_write_blocked",
                "reenabled_preserved",
            ):
                if case.get(field) is not True:
                    status["errors"].append(f"{case_id} missing {field}")
        elif case_id == "mbc3_sram_bank_select_isolation":
            if int(case.get("isolated_bank_count", 0) or 0) < 4:
                status["errors"].append(f"{case_id} did not prove all selected SRAM banks")
            if not all(dict_value(item).get("match") is True for item in list_value(case.get("reads"))):
                status["errors"].append(f"{case_id} has an SRAM bank read mismatch")
        elif case_id == "mbc3_rtc_register_select_latch":
            for field in ("bounded_register_values", "latch_sequence_observed", "sram_marker_restored"):
                if case.get(field) is not True:
                    status["errors"].append(f"{case_id} missing {field}")
            if int(case.get("rtc_register_count", 0) or 0) < 5:
                status["errors"].append(f"{case_id} did not sample all MBC3 RTC registers")
        status["validated_cases"].append(case_id)

    event_cases: set[str] = set()
    for event in events:
        if not isinstance(event, dict):
            status["errors"].append("MBC runtime event is not an object")
            continue
        case_id = str(event.get("validation", {}).get("case_id", "") or "")
        event_cases.add(case_id)
        if event.get("kind") != "runtime_event_envelope":
            status["errors"].append(f"{case_id}: MBC event is not a runtime_event_envelope")
        if event.get("event_kind") != "hardware_event":
            status["errors"].append(f"{case_id}: MBC event kind is not hardware_event")
        if event.get("proof_status") != "runtime_observed":
            status["errors"].append(f"{case_id}: MBC event proof_status is not runtime_observed")
        if event.get("observation_type") != "explicit_hardware_event":
            status["errors"].append(f"{case_id}: MBC event observation_type is not explicit_hardware_event")
        scope = event.get("scope", {}) if isinstance(event.get("scope"), dict) else {}
        if scope.get("backend") != "pyboy" or scope.get("surface") != "mbc":
            status["errors"].append(f"{case_id}: MBC event scope mismatch")
        precision = event.get("precision", {}) if isinstance(event.get("precision"), dict) else {}
        if precision.get("transition_observed") is not True:
            status["errors"].append(f"{case_id}: MBC event missing transition_observed precision")
    for case_id in required_cases:
        if case_id not in event_cases:
            status["errors"].append(f"{case_id} missing runtime event envelope")

    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "debugger" / "deity_runtime.py",
        root / "tools" / "debugger" / "runtime_event.py",
        root / "tools" / "debugger" / "parsers.py",
        root / "tools" / "debugger" / "effect_trace.py",
        root / "tools" / "debugger" / "sm83_model.py",
        root / "pokegold.gbc",
        root / "pokegold.sym",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > artifact_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("MBC runtime artifact is older than proof inputs")
    status["ready"] = not status["errors"]
    return status


def interrupt_entry_ime_model_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        "ready": False,
        "probe_count": 0,
        "validated_vectors": [],
        "validated_cpu_state_ops": [],
        "modeled_effect_kinds": [],
        "proof_gate": "",
        "errors": [],
        "next_command": "python -m unittest tools.debugger.tests.test_literal_anything_gate",
    }
    try:
        from tools.damage_debugger.disasm import Instruction
        from tools.debugger.dynamic_taint import InstructionFrame
        from tools.debugger.effect_trace import (
            attach_hardware_side_effect_proof_gates,
            interrupt_entry_effects,
        )
        from tools.debugger.sm83_model import (
            cpu_state_semantics,
            interrupt_entry_semantics,
        )
    except Exception as exc:  # noqa: BLE001
        status["errors"].append(f"interrupt model unavailable: {type(exc).__name__}: {exc}")
        return status

    expected_vectors = {
        0x40: "vblank",
        0x48: "lcd_stat",
        0x50: "timer",
        0x58: "serial",
        0x60: "joypad",
    }
    for vector, expected_name in expected_vectors.items():
        try:
            model = interrupt_entry_semantics(vector)
        except Exception as exc:  # noqa: BLE001
            status["errors"].append(f"vector ${vector:04X} missing: {type(exc).__name__}: {exc}")
            continue
        status["probe_count"] += 1
        if model.name != expected_name:
            status["errors"].append(f"vector ${vector:04X} expected {expected_name}, got {model.name}")
        else:
            status["validated_vectors"].append(f"{vector:04X}:{expected_name}")

    expected_ops = {
        0x76: ("cpu_state", "halt"),
        0x10: ("cpu_state", "stop"),
        0xFB: ("ime", "ei"),
        0xF3: ("ime", "di"),
        0xD9: ("ime", "reti"),
    }
    for opcode, (expected_kind, expected_operation) in expected_ops.items():
        try:
            model = cpu_state_semantics(opcode)
        except Exception as exc:  # noqa: BLE001
            status["errors"].append(f"opcode ${opcode:02X} missing: {type(exc).__name__}: {exc}")
            continue
        status["probe_count"] += 1
        if model.kind != expected_kind or model.operation != expected_operation:
            status["errors"].append(
                f"opcode ${opcode:02X} expected {expected_kind}/{expected_operation}, "
                f"got {model.kind}/{model.operation}"
            )
        else:
            status["validated_cpu_state_ops"].append(f"{opcode:02X}:{expected_operation}")

    previous_instruction = Instruction(
        bank=0,
        pc=0x1234,
        opcode=0x00,
        operand=b"",
        length=1,
        mnemonic="nop",
    )
    previous_frame = InstructionFrame(
        seq=1,
        bank=0,
        pc=0x1234,
        pc_label="caller",
        SP=0xD000,
        known_registers=("SP",),
    )
    current_frame = InstructionFrame(
        seq=2,
        bank=0,
        pc=0x0040,
        pc_label="VBlank",
        SP=0xCFFE,
        known_registers=("SP",),
    )
    effects = interrupt_entry_effects(
        previous_instruction=previous_instruction,
        previous_frame=previous_frame,
        current_frame=current_frame,
    )
    status["probe_count"] += 1
    effect_kinds = [str(item.get("kind", "")) for item in effects]
    status["modeled_effect_kinds"] = sorted(set(effect_kinds))
    for expected_kind in ("interrupt_entry", "stack_write", "register_write"):
        if expected_kind not in effect_kinds:
            status["errors"].append(f"interrupt entry effects missing {expected_kind}")
    events = [{"effects": effects}]
    attach_hardware_side_effect_proof_gates(events)
    gated = [
        item
        for item in events[0].get("effects", [])
        if item.get("hardware_model") == "interrupt_entry" or item.get("kind") == "interrupt_entry"
    ]
    if not gated:
        status["errors"].append("interrupt entry effects were not proof-gated")
    elif not all(item.get("hardware_event_required") for item in gated):
        status["errors"].append("interrupt entry effects do not all require hardware runtime events")
    elif not all(item.get("proof_status") == "planned_only" for item in gated):
        status["errors"].append("interrupt entry effects are not fail-closed without runtime events")
    else:
        status["proof_gate"] = "explicit_runtime_event_missing"
    status["ready"] = not status["errors"]
    return status


def interrupt_entry_exit_runtime_event_stream_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "debugger_literal_anything" / "interrupt_entry_exit_runtime_event_stream.json"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "case_count": 0,
        "runtime_event_count": 0,
        "validated_cases": [],
        "stale_dependencies": [],
        "errors": [],
        "next_command": (
            "python -m tools.debugger replay --surface interrupts --frames 180 "
            "--json-out audit\\debugger_literal_anything\\interrupt_entry_exit_runtime_event_stream.json"
        ),
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status

    if payload.get("kind") != "debugger_deity_surface_replay":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    if payload.get("surface") != "interrupts":
        status["errors"].append(f"unexpected surface: {payload.get('surface', '')}")
    if payload.get("valid") is not True:
        status["errors"].append("interrupt replay artifact is not valid")
    runtime = payload.get("runtime_replay", {})
    if not isinstance(runtime, dict):
        status["errors"].append("runtime_replay is not an object")
        runtime = {}
    if runtime.get("kind") != "debugger_deity_interrupt_entry_exit_runtime_event_stream":
        status["errors"].append(f"unexpected runtime_replay kind: {runtime.get('kind', '')}")
    if runtime.get("valid") is not True:
        status["errors"].append("interrupt runtime stream is not valid")
    if runtime.get("backend") != "pyboy":
        status["errors"].append(f"unexpected interrupt runtime backend: {runtime.get('backend', '')}")
    limits = " ".join(
        str(item)
        for item in [
            *list_value(payload.get("known_limits")),
            *list_value(runtime.get("known_limits")),
        ]
    ).lower()
    for required_limit in ("serial transfer", "cycle-exact", "timer/lcd mode"):
        if required_limit not in limits:
            status["errors"].append(
                f"interrupt runtime artifact must explicitly leave {required_limit} open"
            )
    cases = runtime.get("cases", [])
    if not isinstance(cases, list):
        status["errors"].append("interrupt runtime cases is not a list")
        cases = []
    events = runtime.get("runtime_events", [])
    if not isinstance(events, list):
        status["errors"].append("interrupt runtime_events is not a list")
        events = []
    status["case_count"] = len(cases)
    status["runtime_event_count"] = len(events)
    case_by_id = {
        str(case.get("case_id", "")): case
        for case in cases
        if isinstance(case, dict)
    }
    required_cases = {
        "vblank_interrupt_entry_exit": ("vblank", "$0040", "$016F", 0x01),
        "lcd_stat_interrupt_entry_exit": ("lcd_stat", "$0048", "$0417", 0x02),
        "timer_interrupt_entry_exit": ("timer", "$0050", "$0050", 0x04),
        "serial_interrupt_entry_exit": ("serial", "$0058", "$06F3", 0x08),
        "joypad_interrupt_entry_exit": ("joypad", "$0060", "$08C3", 0x10),
    }
    for case_id, (interrupt_name, vector, exit_pc, ie_bit) in required_cases.items():
        case = case_by_id.get(case_id)
        if not case:
            status["errors"].append(f"missing interrupt runtime case: {case_id}")
            continue
        if case.get("interrupt_name") != interrupt_name:
            status["errors"].append(f"{case_id} interrupt_name mismatch")
        if case.get("transition_kind") != "interrupt_entry_exit":
            status["errors"].append(f"{case_id} transition_kind mismatch")
        if case.get("vector") != vector or case.get("exit_pc") != exit_pc:
            status["errors"].append(f"{case_id} vector/exit mismatch")
        if int(case.get("ie_bit", 0) or 0) != ie_bit:
            status["errors"].append(f"{case_id} IE bit mismatch")
        if int(case.get("entry_count", 0) or 0) <= 0:
            status["errors"].append(f"{case_id} missing runtime entry observations")
        if int(case.get("exit_count", 0) or 0) <= 0:
            status["errors"].append(f"{case_id} missing runtime exit observations")
        if int(case.get("paired_entry_exit_count", 0) or 0) <= 0:
            status["errors"].append(f"{case_id} missing paired entry/exit observations")
        if case.get("return_address_consistent") is not True:
            status["errors"].append(f"{case_id} return address did not survive to RETI")
        if case.get("transition_observed") is not True:
            status["errors"].append(f"{case_id} did not prove an observed interrupt entry/exit")
        entry_samples = list_value(case.get("entry_samples"))
        exit_samples = list_value(case.get("exit_samples"))
        if not entry_samples or not exit_samples:
            status["errors"].append(f"{case_id} missing entry/exit samples")
        status["validated_cases"].append(case_id)

    event_cases: set[str] = set()
    for event in events:
        if not isinstance(event, dict):
            status["errors"].append("interrupt runtime event is not an object")
            continue
        case_id = str(event.get("validation", {}).get("case_id", "") or "")
        event_cases.add(case_id)
        if event.get("kind") != "runtime_event_envelope":
            status["errors"].append(f"{case_id}: interrupt event is not a runtime_event_envelope")
        if event.get("event_kind") != "hardware_event":
            status["errors"].append(f"{case_id}: interrupt event kind is not hardware_event")
        if event.get("proof_status") != "runtime_observed":
            status["errors"].append(f"{case_id}: interrupt event proof_status is not runtime_observed")
        if event.get("observation_type") != "explicit_hardware_event":
            status["errors"].append(f"{case_id}: interrupt event observation_type is not explicit_hardware_event")
        scope = event.get("scope", {}) if isinstance(event.get("scope"), dict) else {}
        if scope.get("backend") != "pyboy" or scope.get("surface") != "interrupts":
            status["errors"].append(f"{case_id}: interrupt event scope mismatch")
        precision = event.get("precision", {}) if isinstance(event.get("precision"), dict) else {}
        if precision.get("transition_observed") is not True:
            status["errors"].append(f"{case_id}: interrupt event missing transition_observed precision")
        if int(precision.get("paired_entry_exit_count", 0) or 0) <= 0:
            status["errors"].append(f"{case_id}: interrupt event missing paired entry/exit precision")
    for case_id in required_cases:
        if case_id not in event_cases:
            status["errors"].append(f"{case_id} missing runtime event envelope")

    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "debugger" / "deity_runtime.py",
        root / "tools" / "debugger" / "runtime_event.py",
        root / "tools" / "debugger" / "parsers.py",
        root / "tools" / "debugger" / "effect_trace.py",
        root / "tools" / "debugger" / "sm83_model.py",
        root / "pokegold.gbc",
        root / "pokegold.sym",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > artifact_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("interrupt runtime artifact is older than proof inputs")
    status["ready"] = not status["errors"]
    return status


def dma_oam_vram_transfer_model_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        "ready": False,
        "probe_count": 0,
        "validated_semantics": [],
        "oam_dma_read_count": 0,
        "oam_dma_write_count": 0,
        "vram_dma_read_count": 0,
        "vram_dma_write_count": 0,
        "proof_gate": "",
        "errors": [],
        "next_command": "python -m unittest tools.debugger.tests.test_literal_anything_gate",
    }
    try:
        from tools.debugger.effect_trace import (
            attach_hardware_side_effect_proof_gates,
            io_write_side_effects,
        )
        from tools.debugger.sm83_model import hardware_trigger_semantics
    except Exception as exc:  # noqa: BLE001
        status["errors"].append(f"DMA model unavailable: {type(exc).__name__}: {exc}")
        return status

    expected_semantics = {
        0xFF46: "oam_dma_trigger",
        0xFF51: "vram_dma_register_write",
        0xFF55: "vram_dma_len_mode_write",
    }
    for address, expected_kind in expected_semantics.items():
        kinds = {model.kind for model in hardware_trigger_semantics(address)}
        status["probe_count"] += 1
        if expected_kind not in kinds:
            status["errors"].append(f"address ${address:04X} missing semantic {expected_kind}")
        else:
            status["validated_semantics"].append(expected_kind)

    oam_trigger = {
        "kind": "io_write",
        "address": 0xFF46,
        "address_hex": "FF46",
        "address_key": "io:FF46",
        "value": 0xC0,
        "runtime_observation": "instruction_pre_state",
    }
    oam_effects = io_write_side_effects(oam_trigger, address=0xFF46, hardware_state={})
    status["probe_count"] += 1
    status["oam_dma_read_count"] = sum(
        1 for item in oam_effects if item.get("kind") == "dma_read" and item.get("hardware_model") == "oam_dma"
    )
    status["oam_dma_write_count"] = sum(
        1 for item in oam_effects if item.get("kind") == "dma_write" and item.get("hardware_model") == "oam_dma"
    )
    if status["oam_dma_read_count"] != 0xA0 or status["oam_dma_write_count"] != 0xA0:
        status["errors"].append("OAM DMA model did not expand to 160 reads and 160 writes")

    vram_trigger = {
        "kind": "io_write",
        "address": 0xFF55,
        "address_hex": "FF55",
        "address_key": "io:FF55",
        "value": 0x00,
        "runtime_observation": "instruction_pre_state",
    }
    vram_state = {
        "rVDMA_SRC_HIGH": 0x12,
        "rVDMA_SRC_LOW": 0x30,
        "rVDMA_DEST_HIGH": 0x04,
        "rVDMA_DEST_LOW": 0x50,
        "vram": 1,
    }
    vram_effects = io_write_side_effects(vram_trigger, address=0xFF55, hardware_state=vram_state)
    status["probe_count"] += 1
    status["vram_dma_read_count"] = sum(
        1 for item in vram_effects if item.get("kind") == "dma_read" and item.get("hardware_model") == "cgb_vram_dma"
    )
    status["vram_dma_write_count"] = sum(
        1 for item in vram_effects if item.get("kind") == "dma_write" and item.get("hardware_model") == "cgb_vram_dma"
    )
    if status["vram_dma_read_count"] != 0x10 or status["vram_dma_write_count"] != 0x10:
        status["errors"].append("CGB VRAM DMA model did not expand one general-DMA block")
    events = [{"effects": [*oam_effects, *vram_effects]}]
    attach_hardware_side_effect_proof_gates(events)
    gated = [
        item
        for item in events[0].get("effects", [])
        if item.get("kind") in {"dma_read", "dma_write"} or item.get("hardware_model") == "cgb_vram_dma"
    ]
    if not gated:
        status["errors"].append("DMA effects were not produced for proof-gating")
    elif not all(item.get("hardware_event_required") for item in gated):
        status["errors"].append("DMA effects do not all require hardware runtime events")
    elif not any(item.get("proof_status") == "planned_only" for item in gated):
        status["errors"].append("DMA effects are not fail-closed without runtime events")
    else:
        status["proof_gate"] = "explicit_runtime_event_missing"
    status["ready"] = not status["errors"]
    return status


def dma_oam_vram_runtime_event_stream_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "debugger_literal_anything" / "dma_oam_vram_runtime_event_stream.json"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "case_count": 0,
        "runtime_event_count": 0,
        "validated_cases": [],
        "stale_dependencies": [],
        "errors": [],
        "next_command": (
            "python -m tools.debugger replay --surface dma --frames 20 "
            "--json-out audit\\debugger_literal_anything\\dma_oam_vram_runtime_event_stream.json"
        ),
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status

    if payload.get("kind") != "debugger_deity_surface_replay":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    if payload.get("surface") != "dma":
        status["errors"].append(f"unexpected surface: {payload.get('surface', '')}")
    if payload.get("valid") is not True:
        status["errors"].append("DMA replay artifact is not valid")
    runtime = payload.get("runtime_replay", {})
    if not isinstance(runtime, dict):
        status["errors"].append("runtime_replay is not an object")
        runtime = {}
    if runtime.get("kind") != "debugger_deity_dma_oam_vram_runtime_event_stream":
        status["errors"].append(f"unexpected runtime_replay kind: {runtime.get('kind', '')}")
    if runtime.get("valid") is not True:
        status["errors"].append("DMA runtime stream is not valid")
    if runtime.get("backend") != "pyboy":
        status["errors"].append(f"unexpected DMA runtime backend: {runtime.get('backend', '')}")
    cases = runtime.get("cases", [])
    if not isinstance(cases, list):
        status["errors"].append("DMA runtime cases is not a list")
        cases = []
    events = runtime.get("runtime_events", [])
    if not isinstance(events, list):
        status["errors"].append("DMA runtime_events is not a list")
        events = []
    status["case_count"] = len(cases)
    status["runtime_event_count"] = len(events)
    case_by_id = {
        str(case.get("case_id", "")): case
        for case in cases
        if isinstance(case, dict)
    }
    required_cases = {
        "oam_dma_hram_trigger": ("oam_dma", 0xA0),
        "cgb_vram_dma_general_16_bytes": ("cgb_vram_dma_general", 0x10),
    }
    for case_id, (dma_kind, byte_count) in required_cases.items():
        case = case_by_id.get(case_id)
        if not case:
            status["errors"].append(f"missing DMA runtime case: {case_id}")
            continue
        if case.get("dma_kind") != dma_kind:
            status["errors"].append(f"{case_id} dma_kind mismatch")
        if int(case.get("byte_count", 0) or 0) != byte_count:
            status["errors"].append(f"{case_id} byte_count mismatch")
        if int(case.get("match_count", 0) or 0) != byte_count:
            status["errors"].append(f"{case_id} match_count mismatch")
        if case.get("exact_match") is not True:
            status["errors"].append(f"{case_id} did not prove exact byte copy")
        if not str(case.get("source_range", "") or "") or not str(case.get("destination_range", "") or ""):
            status["errors"].append(f"{case_id} missing source/destination range")
        status["validated_cases"].append(case_id)

    event_cases: set[str] = set()
    for event in events:
        if not isinstance(event, dict):
            status["errors"].append("DMA runtime event is not an object")
            continue
        case_id = str(event.get("validation", {}).get("case_id", "") or "")
        event_cases.add(case_id)
        if event.get("kind") != "runtime_event_envelope":
            status["errors"].append(f"{case_id}: DMA event is not a runtime_event_envelope")
        if event.get("event_kind") != "hardware_event":
            status["errors"].append(f"{case_id}: DMA event kind is not hardware_event")
        if event.get("proof_status") != "runtime_observed":
            status["errors"].append(f"{case_id}: DMA event proof_status is not runtime_observed")
        if event.get("observation_type") != "explicit_hardware_event":
            status["errors"].append(f"{case_id}: DMA event observation_type is not explicit_hardware_event")
        scope = event.get("scope", {}) if isinstance(event.get("scope"), dict) else {}
        if scope.get("backend") != "pyboy" or scope.get("surface") != "dma":
            status["errors"].append(f"{case_id}: DMA event scope mismatch")
        precision = event.get("precision", {}) if isinstance(event.get("precision"), dict) else {}
        if precision.get("byte_exact_copy") is not True:
            status["errors"].append(f"{case_id}: DMA event missing byte_exact_copy precision")
    for case_id in required_cases:
        if case_id not in event_cases:
            status["errors"].append(f"{case_id} missing runtime event envelope")

    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "debugger" / "deity_runtime.py",
        root / "tools" / "debugger" / "runtime_event.py",
        root / "tools" / "debugger" / "parsers.py",
        root / "tools" / "debugger" / "effect_trace.py",
        root / "tools" / "debugger" / "sm83_model.py",
        root / "pokegold.gbc",
        root / "pokegold.sym",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > artifact_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("DMA runtime artifact is older than proof inputs")
    status["ready"] = not status["errors"]
    return status


def timer_ppu_io_overflow_model_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        "ready": False,
        "probe_count": 0,
        "validated_semantics": [],
        "validated_timer_effects": [],
        "proof_gate": "",
        "errors": [],
        "next_command": "python -m unittest tools.debugger.tests.test_literal_anything_gate",
    }
    try:
        from tools.debugger.effect_trace import (
            attach_hardware_side_effect_proof_gates,
            observed_timer_overflow_effects,
        )
        from tools.debugger.sm83_model import hardware_trigger_semantics
    except Exception as exc:  # noqa: BLE001
        status["errors"].append(f"timer/PPU model unavailable: {type(exc).__name__}: {exc}")
        return status

    expected_semantics = {
        0xFF04: {"timer_register_write", "timer_div_reset"},
        0xFF05: {"timer_register_write"},
        0xFF07: {"timer_register_write"},
        0xFF40: {"ppu_register_write"},
        0xFF44: {"ppu_register_write"},
        0xFF0F: {"interrupt_register_write"},
    }
    for address, expected_kinds in expected_semantics.items():
        kinds = {model.kind for model in hardware_trigger_semantics(address)}
        status["probe_count"] += 1
        missing = expected_kinds - kinds
        if missing:
            status["errors"].append(f"address ${address:04X} missing semantics {sorted(missing)}")
        else:
            status["validated_semantics"].extend(sorted(expected_kinds))

    current_event = {
        "observed_memory": [
            {"address": "FF05", "value_hex": "FF"},
            {"address": "FF06", "value_hex": "34"},
            {"address": "FF0F", "value_hex": "00"},
        ]
    }
    next_event = {
        "observed_memory": [
            {"address": "FF05", "value_hex": "34"},
            {"address": "FF0F", "value_hex": "04"},
        ]
    }
    effects = observed_timer_overflow_effects(current_event, next_event)
    status["probe_count"] += 1
    effect_kinds = {str(item.get("kind", "")) for item in effects}
    expected_timer_effects = {
        "timer_tima_overflow",
        "timer_tima_reload_write",
        "timer_interrupt_request_write",
    }
    if expected_timer_effects - effect_kinds:
        status["errors"].append(f"TIMA overflow model missing effects {sorted(expected_timer_effects - effect_kinds)}")
    else:
        status["validated_timer_effects"] = sorted(expected_timer_effects)
    events = [{"effects": effects}]
    attach_hardware_side_effect_proof_gates(events)
    gated = [
        item
        for item in events[0].get("effects", [])
        if str(item.get("kind", "")).startswith("timer_")
    ]
    if not gated:
        status["errors"].append("timer overflow effects were not produced for proof-gating")
    elif not all(item.get("hardware_event_required") for item in gated):
        status["errors"].append("timer overflow effects do not all require hardware runtime events")
    elif not all(item.get("proof_status") == "planned_only" for item in gated):
        status["errors"].append("timer overflow effects are not fail-closed without runtime events")
    else:
        status["proof_gate"] = "explicit_runtime_event_missing"
    status["ready"] = not status["errors"]
    return status


def timer_lcd_mode_runtime_event_stream_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "debugger_literal_anything" / "timer_lcd_mode_runtime_event_stream.json"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "case_count": 0,
        "runtime_event_count": 0,
        "validated_cases": [],
        "stale_dependencies": [],
        "errors": [],
        "next_command": (
            "python -m tools.debugger replay --surface timer_lcd --frames 3 "
            "--json-out audit\\debugger_literal_anything\\timer_lcd_mode_runtime_event_stream.json"
        ),
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status

    if payload.get("kind") != "debugger_deity_surface_replay":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    if payload.get("surface") != "timer_lcd":
        status["errors"].append(f"unexpected surface: {payload.get('surface', '')}")
    if payload.get("valid") is not True:
        status["errors"].append("timer/LCD replay artifact is not valid")
    runtime = payload.get("runtime_replay", {})
    if not isinstance(runtime, dict):
        status["errors"].append("runtime_replay is not an object")
        runtime = {}
    if runtime.get("kind") != "debugger_deity_timer_lcd_mode_runtime_event_stream":
        status["errors"].append(f"unexpected runtime_replay kind: {runtime.get('kind', '')}")
    if runtime.get("valid") is not True:
        status["errors"].append("timer/LCD runtime stream is not valid")
    if runtime.get("backend") != "pyboy":
        status["errors"].append(f"unexpected timer/LCD runtime backend: {runtime.get('backend', '')}")
    limits = " ".join(
        str(item)
        for item in [
            *list_value(payload.get("known_limits")),
            *list_value(runtime.get("known_limits")),
        ]
    ).lower()
    for required_limit in ("cycle-exact", "cross-backend"):
        if required_limit not in limits:
            status["errors"].append(
                f"timer/LCD runtime artifact must explicitly leave {required_limit} open"
            )

    cases = runtime.get("cases", [])
    if not isinstance(cases, list):
        status["errors"].append("timer/LCD runtime cases is not a list")
        cases = []
    events = runtime.get("runtime_events", [])
    if not isinstance(events, list):
        status["errors"].append("timer/LCD runtime_events is not a list")
        events = []
    status["case_count"] = len(cases)
    status["runtime_event_count"] = len(events)
    case_by_id = {
        str(case.get("case_id", "")): case
        for case in cases
        if isinstance(case, dict)
    }

    timer_case = case_by_id.get("timer_tima_overflow_interrupt_request")
    if not timer_case:
        status["errors"].append("missing timer/LCD runtime case: timer_tima_overflow_interrupt_request")
    else:
        if timer_case.get("event_family") != "timer":
            status["errors"].append("timer runtime case event_family mismatch")
        if timer_case.get("transition_kind") != "timer_tima_overflow_if_request":
            status["errors"].append("timer runtime case transition_kind mismatch")
        if timer_case.get("overflow_drop_observed") is not True:
            status["errors"].append("timer runtime case missing TIMA wrap/drop observation")
        if timer_case.get("interrupt_request_observed") is not True:
            status["errors"].append("timer runtime case missing IF timer request observation")
        if int(timer_case.get("if_timer_bit", 0) or 0) != 0x04:
            status["errors"].append("timer runtime case IF timer bit mismatch")
        if int(timer_case.get("sample_count", 0) or 0) <= 0:
            status["errors"].append("timer runtime case has no samples")
        if not list_value(timer_case.get("overflow_drop_samples")):
            status["errors"].append("timer runtime case missing overflow drop samples")
        if timer_case.get("runtime_event_observed") is not True:
            status["errors"].append("timer runtime case did not prove a runtime event")
        status["validated_cases"].append("timer_tima_overflow_interrupt_request")

    lcd_case = case_by_id.get("lcd_stat_mode_poll_sequence")
    if not lcd_case:
        status["errors"].append("missing timer/LCD runtime case: lcd_stat_mode_poll_sequence")
    else:
        if lcd_case.get("event_family") != "lcd":
            status["errors"].append("LCD runtime case event_family mismatch")
        if lcd_case.get("transition_kind") != "lcd_stat_mode_ly_sequence":
            status["errors"].append("LCD runtime case transition_kind mismatch")
        observed_modes = {int(mode) for mode in list_value(lcd_case.get("observed_modes"))}
        if not {0, 1, 2, 3}.issubset(observed_modes):
            status["errors"].append("LCD runtime case did not observe STAT modes 0,1,2,3")
        if int(lcd_case.get("ly_max", 0) or 0) < 144:
            status["errors"].append("LCD runtime case did not reach VBlank LY")
        if int(lcd_case.get("transition_count", 0) or 0) <= 0:
            status["errors"].append("LCD runtime case missing mode/LY transitions")
        if not dict_value(lcd_case.get("vblank_entry")):
            status["errors"].append("LCD runtime case missing VBlank entry sample")
        if lcd_case.get("mode_sequence_observed") is not True:
            status["errors"].append("LCD runtime case did not prove mode sequence")
        if lcd_case.get("runtime_event_observed") is not True:
            status["errors"].append("LCD runtime case did not prove a runtime event")
        status["validated_cases"].append("lcd_stat_mode_poll_sequence")

    event_cases: set[str] = set()
    for event in events:
        if not isinstance(event, dict):
            status["errors"].append("timer/LCD runtime event is not an object")
            continue
        case_id = str(event.get("validation", {}).get("case_id", "") or "")
        event_cases.add(case_id)
        if event.get("kind") != "runtime_event_envelope":
            status["errors"].append(f"{case_id}: timer/LCD event is not a runtime_event_envelope")
        if event.get("event_kind") != "hardware_event":
            status["errors"].append(f"{case_id}: timer/LCD event kind is not hardware_event")
        if event.get("proof_status") != "runtime_observed":
            status["errors"].append(f"{case_id}: timer/LCD event proof_status is not runtime_observed")
        if event.get("observation_type") != "explicit_hardware_event":
            status["errors"].append(f"{case_id}: timer/LCD event observation_type is not explicit_hardware_event")
        scope = event.get("scope", {}) if isinstance(event.get("scope"), dict) else {}
        if scope.get("backend") != "pyboy" or scope.get("surface") != "timer_lcd":
            status["errors"].append(f"{case_id}: timer/LCD event scope mismatch")
        precision = event.get("precision", {}) if isinstance(event.get("precision"), dict) else {}
        if case_id == "timer_tima_overflow_interrupt_request":
            if precision.get("overflow_drop_observed") is not True:
                status["errors"].append(f"{case_id}: event missing overflow precision")
            if precision.get("interrupt_request_observed") is not True:
                status["errors"].append(f"{case_id}: event missing interrupt precision")
        if case_id == "lcd_stat_mode_poll_sequence":
            observed = {int(mode) for mode in list_value(precision.get("observed_modes"))}
            if not {0, 1, 2, 3}.issubset(observed):
                status["errors"].append(f"{case_id}: event missing observed mode precision")
            if precision.get("vblank_observed") is not True:
                status["errors"].append(f"{case_id}: event missing VBlank precision")
    for case_id in ("timer_tima_overflow_interrupt_request", "lcd_stat_mode_poll_sequence"):
        if case_id not in event_cases:
            status["errors"].append(f"{case_id} missing runtime event envelope")

    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "debugger" / "deity_runtime.py",
        root / "tools" / "debugger" / "runtime_event.py",
        root / "tools" / "debugger" / "parsers.py",
        root / "tools" / "debugger" / "effect_trace.py",
        root / "tools" / "debugger" / "sm83_model.py",
        root / "pokegold.gbc",
        root / "pokegold.sym",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > artifact_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("timer/LCD runtime artifact is older than proof inputs")
    status["ready"] = not status["errors"]
    return status


def serial_register_write_model_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        "ready": False,
        "probe_count": 0,
        "validated_semantics": [],
        "validated_interrupt_vector": "",
        "modeled_effect_kinds": [],
        "errors": [],
        "next_command": "python -m unittest tools.debugger.tests.test_literal_anything_gate",
    }
    try:
        from tools.debugger.effect_trace import io_write_side_effects
        from tools.debugger.sm83_model import hardware_trigger_semantics, interrupt_entry_semantics
    except Exception as exc:  # noqa: BLE001
        status["errors"].append(f"serial model unavailable: {type(exc).__name__}: {exc}")
        return status

    try:
        vector = interrupt_entry_semantics(0x58)
        status["probe_count"] += 1
        if vector.name != "serial":
            status["errors"].append(f"interrupt vector $0058 expected serial, got {vector.name}")
        else:
            status["validated_interrupt_vector"] = "0058:serial"
    except Exception as exc:  # noqa: BLE001
        status["errors"].append(f"serial interrupt vector missing: {type(exc).__name__}: {exc}")

    for address in (0xFF01, 0xFF02):
        kinds = {model.kind for model in hardware_trigger_semantics(address)}
        status["probe_count"] += 1
        if "serial_register_write" not in kinds:
            status["errors"].append(f"address ${address:04X} missing serial_register_write semantic")
        else:
            status["validated_semantics"].append(f"{address:04X}:serial_register_write")

    trigger = {
        "kind": "io_write",
        "address": 0xFF02,
        "address_hex": "FF02",
        "address_key": "io:FF02",
        "value": 0x81,
        "runtime_observation": "instruction_pre_state",
    }
    effects = io_write_side_effects(trigger, address=0xFF02, hardware_state={})
    status["probe_count"] += 1
    status["modeled_effect_kinds"] = sorted({str(item.get("kind", "")) for item in effects})
    if "serial_register_write" not in status["modeled_effect_kinds"]:
        status["errors"].append("serial IO write did not produce serial_register_write effect")
    status["ready"] = not status["errors"]
    return status


def serial_transfer_runtime_event_stream_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = root / "audit" / "debugger_literal_anything" / "serial_transfer_runtime_event_stream.json"
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "case_count": 0,
        "runtime_event_count": 0,
        "validated_cases": [],
        "stale_dependencies": [],
        "errors": [],
        "next_command": (
            "python -m tools.debugger replay --surface serial --frames 5 "
            "--json-out audit\\debugger_literal_anything\\serial_transfer_runtime_event_stream.json"
        ),
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status

    if payload.get("kind") != "debugger_deity_surface_replay":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    if payload.get("surface") != "serial":
        status["errors"].append(f"unexpected surface: {payload.get('surface', '')}")
    if payload.get("valid") is not True:
        status["errors"].append("serial replay artifact is not valid")
    runtime = payload.get("runtime_replay", {})
    if not isinstance(runtime, dict):
        status["errors"].append("runtime_replay is not an object")
        runtime = {}
    if runtime.get("kind") != "debugger_deity_serial_transfer_runtime_event_stream":
        status["errors"].append(f"unexpected runtime_replay kind: {runtime.get('kind', '')}")
    if runtime.get("valid") is not True:
        status["errors"].append("serial runtime stream is not valid")
    if runtime.get("backend") != "pyboy":
        status["errors"].append(f"unexpected serial runtime backend: {runtime.get('backend', '')}")
    limits = " ".join(
        str(item)
        for item in [
            *list_value(payload.get("known_limits")),
            *list_value(runtime.get("known_limits")),
        ]
    ).lower()
    for required_limit in ("linked peer", "mystery gift", "cross-backend"):
        if required_limit not in limits:
            status["errors"].append(
                f"serial runtime artifact must explicitly leave {required_limit} open"
            )

    cases = runtime.get("cases", [])
    if not isinstance(cases, list):
        status["errors"].append("serial runtime cases is not a list")
        cases = []
    events = runtime.get("runtime_events", [])
    if not isinstance(events, list):
        status["errors"].append("serial runtime_events is not a list")
        events = []
    status["case_count"] = len(cases)
    status["runtime_event_count"] = len(events)
    case_by_id = {
        str(case.get("case_id", "")): case
        for case in cases
        if isinstance(case, dict)
    }
    required_cases = {
        "serial_internal_clock_transfer_byte_42": 0x42,
        "serial_internal_clock_transfer_byte_5a": 0x5A,
    }
    extra_cases = sorted(set(case_by_id) - set(required_cases))
    if extra_cases:
        status["errors"].append(f"unexpected serial runtime cases: {extra_cases}")
    for case_id, outgoing_byte in required_cases.items():
        case = case_by_id.get(case_id)
        if not case:
            status["errors"].append(f"missing serial runtime case: {case_id}")
            continue
        if case.get("event_family") != "serial":
            status["errors"].append(f"{case_id} event_family mismatch")
        if case.get("transition_kind") != "serial_internal_clock_transfer":
            status["errors"].append(f"{case_id} transition_kind mismatch")
        if int(case.get("outgoing_byte", -1) or -1) != outgoing_byte:
            status["errors"].append(f"{case_id} outgoing byte mismatch")
        if str(case.get("serial_output", "")) != chr(outgoing_byte):
            status["errors"].append(f"{case_id} serial output missing outgoing byte")
        if sorted(int(item) for item in list_value(case.get("sc_values"))) != [0x80, 0x81]:
            status["errors"].append(f"{case_id} SC values did not capture start and post-start states")
        if [int(item) for item in list_value(case.get("sb_values"))] != [0xFF]:
            status["errors"].append(f"{case_id} SB values did not match disconnected-peer fill")
        if case.get("first_interrupt_request_sample") in (None, ""):
            status["errors"].append(f"{case_id} missing first serial interrupt request sample")
        if case.get("start_observed") is not True:
            status["errors"].append(f"{case_id} missing SC start observation")
        if case.get("post_start_observed") is not True:
            status["errors"].append(f"{case_id} missing post-start SC observation")
        if case.get("interrupt_request_observed") is not True:
            status["errors"].append(f"{case_id} missing serial IF request observation")
        if case.get("serial_output_observed") is not True:
            status["errors"].append(f"{case_id} missing PyBoy serial output observation")
        if case.get("receive_fill_observed") is not True:
            status["errors"].append(f"{case_id} missing disconnected-peer receive fill observation")
        if int(case.get("if_serial_bit", 0) or 0) != 0x08:
            status["errors"].append(f"{case_id} serial IF bit mismatch")
        if int(case.get("sample_count", 0) or 0) <= 0:
            status["errors"].append(f"{case_id} has no samples")
        if case.get("runtime_event_observed") is not True:
            status["errors"].append(f"{case_id} did not prove a runtime event")
        status["validated_cases"].append(case_id)

    event_cases: set[str] = set()
    for event in events:
        if not isinstance(event, dict):
            status["errors"].append("serial runtime event is not an object")
            continue
        case_id = str(event.get("validation", {}).get("case_id", "") or "")
        event_cases.add(case_id)
        if event.get("kind") != "runtime_event_envelope":
            status["errors"].append(f"{case_id}: serial event is not a runtime_event_envelope")
        if event.get("event_kind") != "hardware_event":
            status["errors"].append(f"{case_id}: serial event kind is not hardware_event")
        if event.get("source_kind") != "pyboy_serial_runtime":
            status["errors"].append(f"{case_id}: serial event source_kind mismatch")
        if event.get("source_report") != "debugger_deity_serial_transfer_runtime_event_stream":
            status["errors"].append(f"{case_id}: serial event source_report mismatch")
        if event.get("proof_status") != "runtime_observed":
            status["errors"].append(f"{case_id}: serial event proof_status is not runtime_observed")
        if event.get("observation_type") != "explicit_hardware_event":
            status["errors"].append(f"{case_id}: serial event observation_type is not explicit_hardware_event")
        scope = event.get("scope", {}) if isinstance(event.get("scope"), dict) else {}
        if scope.get("backend") != "pyboy" or scope.get("surface") != "serial":
            status["errors"].append(f"{case_id}: serial event scope mismatch")
        precision = event.get("precision", {}) if isinstance(event.get("precision"), dict) else {}
        for key in (
            "start_observed",
            "post_start_observed",
            "interrupt_request_observed",
            "serial_output_observed",
            "receive_fill_observed",
        ):
            if precision.get(key) is not True:
                status["errors"].append(f"{case_id}: serial event missing {key} precision")
    for case_id in required_cases:
        if case_id not in event_cases:
            status["errors"].append(f"{case_id} missing runtime event envelope")
    extra_event_cases = sorted(event_cases - set(required_cases))
    if extra_event_cases:
        status["errors"].append(f"unexpected serial runtime event cases: {extra_event_cases}")

    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "debugger" / "deity_runtime.py",
        root / "tools" / "debugger" / "runtime_event.py",
        root / "tools" / "debugger" / "parsers.py",
        root / "tools" / "debugger" / "effect_trace.py",
        root / "tools" / "debugger" / "sm83_model.py",
        root / "pokegold.gbc",
        root / "pokegold.sym",
    ]
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > artifact_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("serial runtime artifact is older than proof inputs")
    status["ready"] = not status["errors"]
    return status


def link_boundary_source_anchor_status(*, root: Path = ROOT) -> dict[str, Any]:
    surface_index = root / "audit" / "debugger_literal_anything" / "rom_surface_index.jsonl"
    required_labels = {
        label
        for labels in LINK_BOUNDARY_SOURCE_ANCHOR_LABELS.values()
        for label in labels
    }
    status: dict[str, Any] = {
        "ready": False,
        "surface_index": display_path(surface_index, root=root),
        "source_file_count": len(LINK_BOUNDARY_SOURCE_ANCHOR_LABELS),
        "required_label_count": len(required_labels),
        "source_anchor_count": 0,
        "indexed_label_count": 0,
        "missing_source_labels": [],
        "missing_index_labels": [],
        "stale_dependencies": [],
        "errors": [],
        "next_command": (
            "python -m tools.debugger rom-index --surface-index-out "
            "audit\\debugger_literal_anything\\rom_surface_index.jsonl"
        ),
    }
    source_found: set[str] = set()
    for relative_path, labels in LINK_BOUNDARY_SOURCE_ANCHOR_LABELS.items():
        path = root / relative_path
        if not path.exists():
            status["errors"].append(f"missing link source file: {relative_path}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label in labels:
            if label in text:
                source_found.add(label)
    missing_source = sorted(required_labels - source_found)
    status["source_anchor_count"] = len(source_found)
    status["missing_source_labels"] = missing_source
    if missing_source:
        status["errors"].append(f"missing link source labels: {missing_source}")
    if not surface_index.exists():
        status["errors"].append("missing ROM surface index")
        return status

    indexed: set[str] = set()
    try:
        with surface_index.open(encoding="utf-8") as handle:
            for line in handle:
                if not any(label in line for label in required_labels - indexed):
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                nearest_label = str(row.get("nearest_label", "") or "")
                surface_id = str(row.get("surface_id", "") or "")
                for label in required_labels - indexed:
                    if nearest_label == label or surface_id.endswith(f":{label}"):
                        indexed.add(label)
                if required_labels <= indexed:
                    break
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    missing_index = sorted(required_labels - indexed)
    status["indexed_label_count"] = len(indexed)
    status["missing_index_labels"] = missing_index
    if missing_index:
        status["errors"].append(f"missing link labels from ROM surface index: {missing_index}")

    try:
        index_mtime = surface_index.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    stale: list[str] = []
    for relative_path in LINK_BOUNDARY_SOURCE_ANCHOR_LABELS:
        dependency = root / relative_path
        if not dependency.exists():
            continue
        try:
            if dependency.stat().st_mtime > index_mtime + 1:
                stale.append(relative_path)
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = stale
        status["errors"].append("link source anchors are newer than the ROM surface index")
    status["ready"] = not status["errors"]
    return status


def link_boundary_runtime_state_class_corpus_status(*, root: Path = ROOT) -> dict[str, Any]:
    source_anchor_status = link_boundary_source_anchor_status(root=root)
    required_labels = [
        (relative_path, label)
        for relative_path, labels in LINK_BOUNDARY_SOURCE_ANCHOR_LABELS.items()
        for label in labels
    ]
    status: dict[str, Any] = {
        "ready": False,
        "evidence_id": LINK_BOUNDARY_RUNTIME_STATE_CLASS_CORPUS_EVIDENCE_ID,
        "class_count": 0,
        "required_class_count": len(required_labels),
        "class_ids": [],
        "source_anchor_ready": bool(source_anchor_status.get("ready")),
        "errors": [],
        "next_command": "python -m unittest tools.debugger.tests.test_literal_anything_gate",
    }
    if not source_anchor_status.get("ready"):
        status["errors"].append("link source anchors are not ready")
        return status
    try:
        from tools.debugger.canonical_state_class import (
            build_canonical_state_class,
            stable_json_hash,
            validate_canonical_state_class,
        )
    except Exception as exc:  # noqa: BLE001
        status["errors"].append(f"canonical state-class builder unavailable: {type(exc).__name__}: {exc}")
        return status

    identity = {
        "rom_sha256": sha256_file(root / "pokegold.gbc", root=root) or "missing",
        "symbols_sha256": sha256_file(root / "pokegold.sym", root=root) or "missing",
        "map_sha256": sha256_file(root / "pokegold.map", root=root) or "missing",
        "rule_map_sha256": stable_json_hash(
            {
                "surface": "link_serial_mystery_gift",
                "source_anchors": LINK_BOUNDARY_SOURCE_ANCHOR_LABELS,
            }
        ),
        "source_tree_sha256": "link-boundary-source-anchor-corpus",
        "dirty_diff_hash": stable_json_hash({"root": str(root), "labels": required_labels}),
    }
    classes: list[dict[str, Any]] = []
    for relative_path, label in required_labels:
        boundary_kind = link_boundary_kind(label)
        canonical = build_canonical_state_class(
            surface="link_serial_mystery_gift",
            identity=identity,
            public_facts={
                "boundary_id": f"{relative_path}:{label}",
                "source_file": relative_path,
                "label": label,
                "boundary_kind": boundary_kind,
                "runtime_proof_state": "unsupported_without_link_backend",
            },
            surface_facts={
                "link_serial": {
                    "boundary_kind": boundary_kind,
                    "source_anchor_indexed": True,
                    "runtime_backend": "missing_link_backend",
                }
            },
            backend="static_source_anchor",
            proof_status="unsupported",
            raw_state_provenance={
                "kind": "link_boundary_source_anchor",
                "source_file": relative_path,
                "label": label,
            },
            reachable_proof={
                "source_anchor_indexed": True,
                "runtime_observed": False,
            },
            missing_evidence=[
                SERIAL_TRANSFER_RUNTIME_EVENT_STREAM_GAP,
                "link_backend_missing",
            ],
            blocking_gaps=[SERIAL_TRANSFER_RUNTIME_EVENT_STREAM_GAP],
            known_limits=[
                "This class corpus records source-anchored link boundary states and fails closed without a linked runtime backend.",
            ],
            source_refs=[relative_path],
        )
        errors = validate_canonical_state_class(canonical)
        if errors or canonical.get("valid") is not True:
            status["errors"].append(f"{label}: invalid canonical class {errors or canonical.get('validation_errors', [])}")
        if canonical.get("proof_status") != "unsupported":
            status["errors"].append(f"{label}: link class must remain unsupported")
        missing = set(canonical.get("missing_evidence", []))
        if SERIAL_TRANSFER_RUNTIME_EVENT_STREAM_GAP not in missing or "link_backend_missing" not in missing:
            status["errors"].append(f"{label}: missing fail-closed runtime evidence markers")
        classes.append(canonical)
    class_ids = [str(item.get("class_id", "") or "") for item in classes]
    status["class_count"] = len(classes)
    status["class_ids"] = class_ids
    if len(classes) != len(required_labels):
        status["errors"].append("link boundary class count mismatch")
    if len(set(class_ids)) != len(class_ids):
        status["errors"].append("link boundary class ids are not unique")
    if any(not class_id.startswith("csc_") for class_id in class_ids):
        status["errors"].append("link boundary class ids are malformed")
    status["classes"] = classes
    status["ready"] = not status["errors"]
    return status


def link_boundary_kind(label: str) -> str:
    lowered = label.lower()
    if "serial" in lowered or "transfer" in lowered:
        return "serial_transfer_boundary"
    if "timeout" in lowered or "error" in lowered:
        return "link_timeout_or_error_boundary"
    if "timecapsule" in lowered or "time_capsule" in lowered:
        return "time_capsule_boundary"
    if "receptionist" in lowered or "room" in lowered or "linkedfriend" in lowered:
        return "link_room_handshake_boundary"
    return "link_communication_boundary"


def canonical_state_class_schema_status(
    *,
    identity: dict[str, str] | None = None,
) -> dict[str, Any]:
    status: dict[str, Any] = {
        "ready": False,
        "schema_version": 0,
        "validated_surface_buckets": [],
        "required_identity_fields": [],
        "stable_class_id": "",
        "hidden_fact_rejection": False,
        "selected_surface_adoptions": {},
        "selected_surface_adoption_ready": False,
        "errors": [],
        "next_command": "python -m unittest tools.debugger.tests.test_canonical_state_class",
    }
    try:
        from tools.debugger.canonical_state_class import (
            ALLOWED_SURFACE_FACT_BUCKETS,
            REQUIRED_IDENTITY_FIELDS,
            SCHEMA_VERSION,
            build_canonical_state_class,
        )
    except Exception as exc:  # noqa: BLE001
        status["errors"].append(f"canonical state-class schema unavailable: {type(exc).__name__}: {exc}")
        return status

    basis = identity or {
        "rom_sha256": "A" * 64,
        "symbols_sha256": "B" * 64,
        "map_sha256": "C" * 64,
        "rule_map_sha256": "D" * 64,
        "source_tree_sha256": "schema-status",
        "dirty_diff_hash": "E" * 64,
    }
    status["schema_version"] = SCHEMA_VERSION
    status["required_identity_fields"] = list(REQUIRED_IDENTITY_FIELDS)
    status["validated_surface_buckets"] = sorted(str(item) for item in ALLOWED_SURFACE_FACT_BUCKETS)
    required_buckets = {
        "boss_ai",
        "battle",
        "damage",
        "script_vm",
        "map",
        "graphics",
        "audio",
        "save_rtc",
        "bank",
        "content",
        "runtime",
        "link_serial",
    }
    missing_buckets = sorted(required_buckets - set(status["validated_surface_buckets"]))
    if missing_buckets:
        status["errors"].append(f"schema missing roadmap surface buckets: {missing_buckets}")

    first = build_canonical_state_class(
        surface="boss_ai",
        identity=basis,
        public_facts={"tier": 2, "tags": ["a", "b"], "rule_id": "score.best_move"},
        surface_facts={"boss_ai": {"decision_surface": "move_score"}},
        backend="static",
        proof_status="missing_proof_artifact",
        missing_evidence=["rom proof"],
    )
    second = build_canonical_state_class(
        surface="boss_ai",
        identity=dict(reversed(list(basis.items()))),
        public_facts={"rule_id": "score.best_move", "tags": ["a", "b"], "tier": 2},
        surface_facts={"boss_ai": {"decision_surface": "move_score"}},
        backend="static",
        proof_status="missing_proof_artifact",
        missing_evidence=["different missing proof"],
    )
    if not first.get("valid"):
        status["errors"].append(f"valid canonical class rejected: {first.get('validation_errors', [])}")
    if first.get("class_id") != second.get("class_id"):
        status["errors"].append("equivalent public facts did not produce a stable class_id")
    class_id = str(first.get("class_id", "") or "")
    status["stable_class_id"] = class_id
    if not class_id.startswith("csc_") or len(class_id) != 24:
        status["errors"].append(f"unexpected canonical class_id format: {class_id}")

    hidden = build_canonical_state_class(
        surface="boss_ai",
        identity=basis,
        public_facts={"hidden_moves": ["SURF"]},
        surface_facts={"boss_ai": {"decision_surface": "move_score"}},
        proof_status="missing_proof_artifact",
    )
    hidden_rejected = (
        hidden.get("valid") is False
        and not hidden.get("class_id")
        and any("hidden/private fact" in str(error) for error in hidden.get("validation_errors", []))
    )
    status["hidden_fact_rejection"] = hidden_rejected
    if not hidden_rejected:
        status["errors"].append("hidden public-only facts did not fail closed before class_id")
    status["ready"] = not status["errors"]
    return status


def boss_ai_raw_class_adoption_status() -> dict[str, Any]:
    try:
        from tools.audit.check_boss_ai_debugger_god import (
            boss_ai_raw_class_adoption_status as build_status,
        )

        return build_status()
    except Exception as exc:  # noqa: BLE001
        return {
            "ready": False,
            "closed_evidence_ids": [],
            "blocking_gaps": [f"boss_ai_raw_class_adoption_unavailable:{type(exc).__name__}"],
        }


def latest_boss_ai_god_baseline_path(*, root: Path = ROOT) -> Path:
    benchmark_dir = root / "audit" / "boss_ai_debugger" / "god_level_benchmark"
    candidates = sorted(benchmark_dir.glob("baseline_*.json"), key=lambda item: item.name)
    if candidates:
        return candidates[-1]
    return benchmark_dir / "baseline_2026-05-31.json"


def boss_ai_god_gate_status(*, root: Path = ROOT) -> dict[str, Any]:
    path = latest_boss_ai_god_baseline_path(root=root)
    payload: dict[str, Any] | None = None
    source = "baseline"
    if root.resolve() == ROOT.resolve():
        try:
            from tools.audit.check_boss_ai_debugger_god import build_god_report

            payload = build_god_report(root=root)
            source = "live_current_god_gate"
        except Exception as exc:  # noqa: BLE001
            payload = None
            source = f"live_current_god_gate_unavailable:{type(exc).__name__}"
    status: dict[str, Any] = {
        "path": "<live current Boss AI God gate>" if payload is not None else display_path(path, root=root),
        "source": source,
        "ready": False,
        "bridge_valid": False,
        "exists": payload is not None or path.exists(),
        "boss_ai_god_ready": False,
        "proof_status": "",
        "closed_evidence_ids": [],
        "missing_witness_role_count": 0,
        "blocking_gaps": [],
        "stale_dependencies": [],
        "errors": [],
        "next_command": "python tools\\audit\\check_boss_ai_debugger_god.py --read-only --json",
    }
    if payload is None:
        if not path.exists():
            status["errors"].append("missing")
            return status
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            status["errors"].append(str(exc))
            return status
    if payload.get("kind") != "boss_ai_debugger_god_gate":
        status["errors"].append(f"unexpected kind: {payload.get('kind', '')}")
    proof_status = str(payload.get("proof_status", "") or "")
    god_ready = payload.get("boss_ai_god_ready")
    status["proof_status"] = proof_status
    status["boss_ai_god_ready"] = bool(god_ready) if isinstance(god_ready, bool) else False
    closed = payload.get("closed_evidence_ids", [])
    if not isinstance(closed, list):
        closed = []
        status["errors"].append("Boss God closed_evidence_ids is not a list")
    closed_set = {str(item) for item in closed}
    missing_closed = [item for item in BOSS_AI_GOD_REQUIRED_EVIDENCE_IDS if item not in closed_set]
    if missing_closed:
        status["errors"].append(f"Boss God gate missing expected closed evidence IDs: {missing_closed}")
    blocking = sorted({str(item) for item in list_value(payload.get("blocking_gaps"))})
    status["blocking_gaps"] = blocking
    counters = dict_value(payload.get("counters"))
    status["missing_witness_role_count"] = int(counters.get("missing_witness_role_count", 0) or 0)
    if god_ready is True:
        if proof_status != "complete":
            status["errors"].append("Boss God gate complete report must use proof_status=complete")
        if blocking:
            status["errors"].append("Boss God gate complete report must not have blocking gaps")
        if status["missing_witness_role_count"] != 0:
            status["errors"].append("Boss God gate complete report must have zero missing witness roles")
    else:
        if proof_status != "missing_evidence":
            status["errors"].append("Boss God gate incomplete report must use proof_status=missing_evidence")
        if god_ready is not False:
            status["errors"].append("Boss God gate must expose a boolean boss_ai_god_ready")
        for required_gap in ("boss_ai_exhaustive_class_witness_roles_missing", "boss_ai_universe_not_complete"):
            if required_gap not in blocking:
                status["errors"].append(f"Boss God gate must leave {required_gap} open while incomplete")
        if status["missing_witness_role_count"] <= 0:
            status["errors"].append("Boss God gate must record remaining missing witness roles while incomplete")
    for field in (
        "missing_reachable_label_count",
        "missing_rule_count",
        "missing_branch_count",
        "missing_public_read_count",
        "missing_class_id_count",
        "missing_materialization_path_count",
    ):
        if int(counters.get(field, 0) or 0) != 0:
            status["errors"].append(f"Boss God gate has unresolved counter before bridge: {field}")
    if god_ready is True:
        for field, value in counters.items():
            if int(value or 0) != 0:
                status["errors"].append(f"Boss God complete report has nonzero counter: {field}")
    canonical = dict_value(payload.get("canonical_class_coverage"))
    if canonical.get("ready") is not True:
        status["errors"].append("Boss God rule-target canonical class coverage is not ready")
    if int(canonical.get("valid_class_id_count", 0) or 0) <= 0:
        status["errors"].append("Boss God rule-target canonical class coverage has no valid rows")
    changed_ai = dict_value(payload.get("changed_ai_god_suite"))
    if changed_ai.get("partial_evidence_ready") is not True or changed_ai.get("completion_ready") is not True:
        status["errors"].append("Boss God changed-AI partial suite is not ready")
    if list_value(changed_ai.get("blocking_gaps")):
        status["errors"].append("Boss God changed-AI partial suite has blocking gaps")

    if source == "live_current_god_gate":
        status["closed_evidence_ids"] = list(dict.fromkeys(str(item) for item in closed if str(item) in closed_set))
        status["bridge_valid"] = not status["errors"]
        status["ready"] = status["bridge_valid"] and god_ready is True
        return status

    try:
        artifact_mtime = path.stat().st_mtime
    except OSError as exc:
        status["errors"].append(str(exc))
        return status
    dependency_paths = [
        root / "tools" / "audit" / "check_boss_ai_debugger_god.py",
        root / "tools" / "boss_ai_debugger" / "universe.py",
        root / "audit" / "boss_ai_debugger" / "god_level_benchmark" / "questions.jsonl",
        root / "audit" / "boss_ai_debugger" / "rule_map.json",
        root / "audit" / "boss_ai_debugger" / "coverage_report.json",
    ]
    for rel in list_value(changed_ai.get("evidence_artifacts")):
        dependency_paths.append(root / str(rel))
    metadata_path = str(changed_ai.get("metadata_path", "") or "")
    if metadata_path:
        dependency_paths.append(root / metadata_path)
    stale: list[str] = []
    for dependency in dependency_paths:
        if not dependency.exists():
            status["errors"].append(f"Boss God dependency missing: {display_path(dependency, root=root)}")
            continue
        try:
            if dependency.stat().st_mtime > artifact_mtime + 1:
                stale.append(str(dependency.relative_to(root)))
        except OSError as exc:
            status["errors"].append(str(exc))
    if stale:
        status["stale_dependencies"] = sorted(set(stale))
        status["errors"].append("Boss God gate baseline is older than proof inputs")
    status["closed_evidence_ids"] = list(dict.fromkeys(str(item) for item in closed if str(item) in closed_set))
    status["bridge_valid"] = not status["errors"]
    status["ready"] = status["bridge_valid"] and god_ready is True
    return status


def headless_battle_class_adoption_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        "ready": False,
        "closed_evidence_ids": [],
        "blocking_gaps": [],
        "class_id": "",
        "class_fingerprint": "",
        "canonical_state_class_valid": False,
        "canonical_state_class_errors": [],
    }
    try:
        from tools.debugger.canonical_state_class import validate_canonical_state_class
        from tools.headless_battle.rom_switch_scenario_export import (
            headless_to_switch_sack_scenario,
        )
    except Exception as exc:  # noqa: BLE001
        status["blocking_gaps"].append(f"headless_battle_class_adoption_unavailable:{type(exc).__name__}")
        return status
    try:
        scenario = headless_to_switch_sack_scenario(_sample_headless_switch_state())
    except Exception as exc:  # noqa: BLE001
        status["blocking_gaps"].append(f"headless_battle_class_adoption_failed:{type(exc).__name__}")
        return status
    canonical = scenario.get("canonical_state_class")
    if not isinstance(canonical, dict):
        status["blocking_gaps"].append("headless_battle_turn_level_class_ids_missing")
        return status
    errors = validate_canonical_state_class(canonical)
    status["class_id"] = str(scenario.get("class_id", ""))
    status["class_fingerprint"] = str(scenario.get("class_fingerprint", ""))
    status["canonical_state_class_valid"] = not errors
    status["canonical_state_class_errors"] = errors
    if not status["class_id"] or status["class_id"] != canonical.get("class_id"):
        status["blocking_gaps"].append("headless_battle_turn_level_class_id_mismatch")
    if errors:
        status["blocking_gaps"].append("headless_battle_turn_level_class_ids_invalid")
    status["ready"] = not status["blocking_gaps"]
    if status["ready"]:
        status["closed_evidence_ids"].append(HEADLESS_TURN_CLASS_EVIDENCE_ID)
    return status


def _sample_headless_switch_state() -> dict[str, Any]:
    return {
        "weather": "none",
        "weather_count": 0,
        "turn": 1,
        "player": {
            "species": "STARMIE",
            "level": 50,
            "types": ["GROUND", "GROUND"],
            "hp": 80,
            "max_hp": 100,
            "stats": {
                "attack": 70,
                "defense": 80,
                "speed": 100,
                "sp_attack": 90,
                "sp_defense": 80,
            },
            "moves": [{"name": "SURF"}],
        },
        "enemy": {
            "species": "QWILFISH",
            "level": 50,
            "types": ["POISON", "WATER"],
            "hp": 80,
            "max_hp": 100,
            "stats": {
                "attack": 70,
                "defense": 75,
                "speed": 85,
                "sp_attack": 55,
                "sp_defense": 55,
            },
            "moves": [{"name": "POISON_STING"}],
            "bench": [
                {
                    "name": "GENGAR",
                    "level": 50,
                    "types": ["GHOST", "POISON"],
                    "hp": 80,
                    "max_hp": 100,
                    "stats": {
                        "attack": 65,
                        "defense": 60,
                        "speed": 110,
                        "sp_attack": 130,
                        "sp_defense": 75,
                    },
                    "moves": [{"name": "LICK"}],
                },
            ],
        },
    }


def jsonl_status(
    path: Path,
    *,
    expected_kind: str,
    root: Path,
    expected_input_hashes: dict[str, str] | None = None,
) -> dict[str, Any]:
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "line_count": 0,
        "content_mirror_exact_span_count": 0,
        "missing_input_hash_count": 0,
        "input_hash_mismatch_count": 0,
        "stale_row_count": 0,
        "first_stale_rows": [],
        "sha256": sha256_file(path, root=root),
        "errors": [],
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    if not path.is_file():
        status["errors"].append("not a file")
        return status
    first_row: dict[str, Any] | None = None
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            status["line_count"] += 1
            if first_row is None:
                try:
                    first_row = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    status["errors"].append(f"line {line_no}: {exc}")
                    break
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict) and row.get("confidence") == "content_mirror_exact_span":
                status["content_mirror_exact_span_count"] += 1
            hash_errors = row_input_hash_errors(row, expected_input_hashes or {})
            if hash_errors:
                status["stale_row_count"] += 1
                if any(error.startswith("missing") for error in hash_errors):
                    status["missing_input_hash_count"] += 1
                if any(error.startswith("mismatch") for error in hash_errors):
                    status["input_hash_mismatch_count"] += 1
                if len(status["first_stale_rows"]) < 5:
                    status["first_stale_rows"].append(
                        {
                            "line": line_no,
                            "row_id": row.get("row_id") or row.get("surface_id", ""),
                            "errors": hash_errors,
                        }
                    )
    if status["line_count"] == 0:
        status["errors"].append("empty")
    if first_row is not None and first_row.get("kind") != expected_kind:
        status["errors"].append(f"expected first row kind {expected_kind}, got {first_row.get('kind', '')}")
    if status["stale_row_count"]:
        status["errors"].append(f"{status['stale_row_count']} row(s) have stale or missing input_hashes")
    status["ready"] = not status["errors"] and status["line_count"] > 0
    return status


def json_report_status(
    path: Path,
    *,
    expected_kind: str,
    root: Path,
    expected_input_hashes: dict[str, str] | None = None,
) -> dict[str, Any]:
    status: dict[str, Any] = {
        "path": display_path(path, root=root),
        "ready": False,
        "exists": path.exists(),
        "missing_input_hash_count": 0,
        "input_hash_mismatch_count": 0,
        "stale_row_count": 0,
        "first_stale_rows": [],
        "sha256": sha256_file(path, root=root),
        "errors": [],
    }
    if not path.exists():
        status["errors"].append("missing")
        return status
    if not path.is_file():
        status["errors"].append("not a file")
        return status
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        status["errors"].append(str(exc))
        return status
    if not isinstance(payload, dict):
        status["errors"].append("not an object")
        return status
    if payload.get("kind") != expected_kind:
        status["errors"].append(f"expected kind {expected_kind}, got {payload.get('kind', '')}")
    hash_errors = row_input_hash_errors(payload, expected_input_hashes or {})
    if hash_errors:
        status["stale_row_count"] = 1
        if any(error.startswith("missing") for error in hash_errors):
            status["missing_input_hash_count"] = 1
        if any(error.startswith("mismatch") for error in hash_errors):
            status["input_hash_mismatch_count"] = 1
        status["first_stale_rows"].append({"row_id": "rom_index_report", "errors": hash_errors})
        status["errors"].append("report has stale or missing input_hashes")
    status["ready"] = not status["errors"]
    return status


def row_input_hash_errors(row: Any, expected_input_hashes: dict[str, str]) -> list[str]:
    if not expected_input_hashes:
        return []
    if not isinstance(row, dict):
        return ["missing row object"]
    actual = row.get("input_hashes")
    if not isinstance(actual, dict):
        return ["missing input_hashes"]
    errors = []
    for key, expected in expected_input_hashes.items():
        if not expected:
            continue
        if actual.get(key) != expected:
            errors.append(f"mismatch {key}")
    return errors


def list_value(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def display_path(path: Path, *, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def write_outputs(report: dict[str, Any], *, out: Path, markdown_out: Path | None) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    if markdown_out is not None:
        markdown_out.parent.mkdir(parents=True, exist_ok=True)
        markdown_out.write_text(format_markdown(report), encoding="utf-8", newline="\n")


def format_markdown(report: dict[str, Any]) -> str:
    counters = report["counters"]
    lines = [
        "# Debugger Literal-Anything Baseline",
        "",
        f"- Generated: {report['generated_at']}",
        f"- literal_anything_ready: `{report['literal_anything_ready']}`",
        f"- proof_status: `{report['proof_status']}`",
        "",
        "## Counters",
        "",
    ]
    for key, value in counters.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Surfaces", "", "| surface | owner | status | backend | next |", "| --- | --- | --- | --- | --- |"])
    for row in report["surfaces"]:
        lines.append(
            f"| {row['surface_id']} | {row['owner_lane'] or 'UNOWNED'} | "
            f"{row['proof_status']} | {row['backend']} | `{row['next_command']}` |"
        )
    lines.extend(["", "## Blocking Gaps", ""])
    for gap in report["blocking_gaps"][:40]:
        lines.append(f"- {gap}")
    return "\n".join(lines) + "\n"


def format_text(report: dict[str, Any]) -> str:
    counters = report["counters"]
    lines = [
        "Debugger literal-anything honesty gate",
        f"literal_anything_ready={report['literal_anything_ready']} proof_status={report['proof_status']}",
        (
            "counters="
            + ", ".join(f"{key}={value}" for key, value in counters.items())
        ),
        "",
        "Top blockers:",
    ]
    for gap in report["blocking_gaps"][:8]:
        lines.append(f"  - {gap}")
    lines.extend(["", "Next commands:"])
    for row in report["surfaces"][:5]:
        lines.append(f"  - {row['surface_id']}: {row['next_command']}")
    return "\n".join(lines)


def run_self_test() -> int:
    report = build_literal_anything_report(read_only=True)
    failures = []
    if report["literal_anything_ready"]:
        if report["proof_status"] != "complete":
            failures.append("ready literal-anything gate must use proof_status=complete")
        if report["blocking_gaps"]:
            failures.append("ready literal-anything gate must not report blocking gaps")
    elif report["proof_status"] != "missing_evidence":
        failures.append("incomplete literal-anything gate must use proof_status=missing_evidence")
    for key in (
        "unowned_reachable_surface_count",
        "partial_pass_count",
        "backend_divergence_count",
        "side_effect_unknown_command_count",
    ):
        if key not in report["counters"]:
            failures.append(f"missing counter {key}")
    if report["read_only_mode"]["would_write_baseline"]:
        failures.append("read-only baseline must not write baseline outputs")
    if report["counters"]["side_effect_unknown_command_count"] != 0:
        failures.append("all currently registered commands should have side-effect metadata")
    if failures:
        print("SELF-TEST FAIL:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("SELF-TEST PASS: literal-anything gate contract and read-only safety hold.")
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Honest red baseline for the debugger literal-anything roadmap.",
    )
    parser.add_argument("--baseline", action="store_true", help="record a dated red baseline unless --read-only is set")
    parser.add_argument("--read-only", action="store_true", help="do not write baseline, JSON, markdown, or other artifacts")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--markdown-out", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.self_test:
        return run_self_test()
    report = build_literal_anything_report(read_only=args.read_only)
    out = args.out
    markdown_out = args.markdown_out
    if args.baseline:
        stamp = today_stamp()
        if args.out == DEFAULT_OUT:
            out = BASELINE_DIR / f"baseline_{stamp}.json"
        if markdown_out is None:
            markdown_out = BASELINE_DIR / f"baseline_{stamp}.md"
    if args.read_only:
        report["read_only_mode"]["would_write_baseline"] = False
    else:
        report["read_only_mode"]["would_write_baseline"] = bool(args.baseline)
        if args.baseline or args.out != DEFAULT_OUT or args.markdown_out is not None:
            write_outputs(report, out=out, markdown_out=markdown_out)
            report["json_out"] = str(out)
            if markdown_out is not None:
                report["markdown_out"] = str(markdown_out)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_text(report))
        if report.get("json_out"):
            print(f"json_out={report['json_out']}")
        if report.get("markdown_out"):
            print(f"markdown_out={report['markdown_out']}")
    return 0 if report["literal_anything_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
