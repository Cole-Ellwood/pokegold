"""Severity tables and ROM-surface calibration for ranked findings.

Two flat tables (``SEVERITY_BASE`` per finding type, ``ROM_SURFACE_SEVERITY_HINTS``
keyword bonuses) plus the calibration pass that bumps a finding's severity when
its text mentions a known ROM surface.
"""

from __future__ import annotations

from typing import Any

from .helpers import string_items, unique_string_items


SEVERITY_BASE = {
    "gate_failed": 95,
    "ingest_error": 85,
    "workflow_failed": 82,
    "watch_hit": 75,
    "capability_missing": 78,
    "capability_partial": 64,
    "compare_gap": 55,
    "fuzz_campaign": 62,
    "content_mirror_failed": 76,
    "content_mirror_warning": 35,
    "content_scenario": 46,
    "content_state_blocked": 68,
    "content_state_executed": 62,
    "content_state_ready": 58,
    "state_space_blocked": 68,
    "state_space_executed": 62,
    "state_space_ready": 58,
    "setup_trigger_gap": 64,
    "runtime_state_impossible": 88,
    "save_state_anomaly": 88,
    "expectation_failed": 78,
    "mirror_uncovered": 50,
    "test_gap": 45,
    "coverage_gap": 40,
    "taint_path": 66,
    "reverse_attribution": 70,
    "instruction_trace_miss": 74,
    "instruction_trace_partial": 64,
    "instruction_trace_limit": 68,
    "instruction_trace_ready": 60,
    "next_step": 52,
    "provenance_warning": 30,
    "ingest_warning": 25,
}

ROM_SURFACE_SEVERITY_HINTS = (
    (
        "banking_abi",
        "ROM banking / ABI",
        10,
        (
            "home/",
            "macros/",
            "farcall",
            "bankswitch",
            "hrombank",
            "hloadedrombank",
            "rst ",
            "rstvector",
            "banked",
        ),
    ),
    (
        "battle_damage",
        "Battle damage",
        8,
        (
            "wcurdamage",
            "battlecommand_damage",
            "engine/battle/effect_commands",
            "damage",
            "type chart",
            "type matchup",
            "held item",
            "weather",
        ),
    ),
    (
        "boss_ai",
        "Boss AI",
        8,
        (
            "bossai_",
            "wbossai",
            "wenemyaimovescores",
            "engine/battle/ai/",
            "boss ai",
            "policy",
            "selector",
        ),
    ),
    (
        "event_scripts_maps",
        "Event scripts and maps",
        7,
        (
            "engine/events/",
            "engine/overworld/",
            "maps/",
            "scripts/",
            "runscriptcommand",
            "callscript",
            "wscriptpos",
            "warp_event",
            "bg_event",
            "object_event",
            "mapscripts",
        ),
    ),
    (
        "movement_text",
        "Movement and text",
        6,
        (
            "data/moves/movement",
            "movement",
            "applymovement",
            "handlemovementdata",
            "wmovementpointer",
            "text/",
            "charmap",
        ),
    ),
    (
        "graphics_audio_ui",
        "Graphics, audio, and UI",
        5,
        (
            "gfx/",
            "audio/",
            "tilesets/",
            "palette",
            "tilemap",
            "sprite",
            "song",
            "sfx",
            "menu",
            "window",
        ),
    ),
    (
        "pokemon_move_data",
        "Pokemon and move data",
        4,
        (
            "data/pokemon/",
            "data/moves/",
            "base_stats",
            "learnsets",
            "evolutions",
            "tmhm",
        ),
    ),
)


def calibrate_finding_severity(item: dict[str, Any]) -> dict[str, Any]:
    match = first_rom_surface_match(finding_search_text(item))
    if not match:
        return item
    surface_id, surface, bonus = match
    base_severity = int(item.get("severity", 40))
    calibrated = dict(item)
    calibrated["severity_base"] = base_severity
    calibrated["severity_bonus"] = bonus
    calibrated["severity"] = min(95, base_severity + bonus)
    calibrated["surface_id"] = surface_id
    calibrated["surface"] = surface
    calibrated["evidence"] = unique_string_items(
        [
            *string_items(item.get("evidence")),
            f"ROM surface calibration: {surface} (+{bonus})",
        ]
    )
    return calibrated


def finding_search_text(item: dict[str, Any]) -> str:
    return " ".join(
        [
            str(item.get("type", "")),
            str(item.get("title", "")),
            " ".join(string_items(item.get("evidence"))),
            " ".join(string_items(item.get("next_actions"))),
        ]
    ).lower().replace("\\", "/")


def first_rom_surface_match(text: str) -> tuple[str, str, int] | None:
    for surface_id, surface, bonus, hints in ROM_SURFACE_SEVERITY_HINTS:
        if any(hint in text for hint in hints):
            return surface_id, surface, bonus
    return None
