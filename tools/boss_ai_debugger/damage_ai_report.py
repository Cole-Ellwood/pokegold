"""Unified exact-damage plus Boss AI move-score report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError
from tools.trace import boss_ai_trace_capture as capture

from .move_score_probe import (
    DEFAULT_MANIFEST,
    _self_test_spearow_gastly_inputs,
    build_self_test_report,
    build_move_score_report,
    format_move_score_probe,
    run_move_score_probe,
)

class DamageAIReportError(PreferenceDataError):
    """User-facing damage AI report error."""


def run_damage_ai_report(
    *,
    trainer: str,
    enemy: str,
    player_save: Path,
    player_slot: int,
    sleep_clause: str = "both",
    trace: bool = False,
    rom: Path = capture.DEFAULT_ROM,
    symbols: Path = capture.DEFAULT_SYMBOLS,
    manifest: Path = DEFAULT_MANIFEST,
) -> dict[str, Any]:
    probe = run_move_score_probe(
        trainer=trainer,
        enemy=enemy,
        player_save=player_save,
        player_slot=player_slot,
        sleep_clause=sleep_clause,
        trace=trace,
        rom=rom,
        symbols=symbols,
        manifest=manifest,
    )
    return {
        "schema_version": 1,
        "source": "damage_ai_report",
        "trainer": probe["trainer"],
        "enemy_selector": probe["enemy_selector"],
        "player_slot": probe["player_slot"],
        "attacker": probe["attacker"],
        "defender": probe["defender"],
        "damage": probe["damage"],
        "variants": probe["variants"],
        "probe": probe,
    }


def format_damage_ai_report(report: dict[str, Any]) -> str:
    probe_view = {
        "attacker": report["attacker"],
        "defender": report["defender"],
        "variants": report["variants"],
    }
    return format_move_score_probe(probe_view)


def run_self_test() -> int:
    probe = build_self_test_report()
    type_immunity_probe = build_move_score_report(
        _self_test_spearow_gastly_inputs(battery_save=Path("unused.state")),
        sleep_clause="inactive",
        trace=False,
    )
    report = {
        "schema_version": 1,
        "source": "damage_ai_report",
        "trainer": probe["trainer"],
        "enemy_selector": probe["enemy_selector"],
        "player_slot": probe["player_slot"],
        "attacker": probe["attacker"],
        "defender": probe["defender"],
        "damage": probe["damage"],
        "variants": probe["variants"],
        "probe": probe,
    }
    variants = {variant["sleep_clause"]: variant for variant in report["variants"]}
    inactive = {row["move_name"]: row for row in variants["inactive"]["rows"]}
    active = {row["move_name"]: row for row in variants["active"]["rows"]}
    if inactive["Peck"]["damage_high"] <= inactive["Confusion"]["damage_high"]:
        raise AssertionError("expected Peck oracle damage to exceed Confusion")
    if inactive["Peck"]["wont_pick"] or active["Peck"]["wont_pick"]:
        raise AssertionError("expected report to keep Peck selectable")
    if inactive["Confusion"]["wont_pick"] or active["Confusion"]["wont_pick"]:
        raise AssertionError("expected report to keep Confusion selectable")
    if inactive["Peck"]["final_score"] >= inactive["Tackle"]["final_score"]:
        raise AssertionError("expected report to prefer Peck over resisted Tackle")
    if active["Hypnosis"]["final_score"] < 80 or not active["Hypnosis"]["wont_pick"]:
        raise AssertionError("expected active sleep clause to block Hypnosis")
    if variants["inactive"]["warnings"] or variants["active"]["warnings"]:
        raise AssertionError("expected no damage-order mismatch warnings after rank fix")
    immunity_rows = {
        row["move_name"]: row
        for row in type_immunity_probe["variants"][0]["rows"]
    }
    if immunity_rows["Peck"]["wont_pick"]:
        raise AssertionError("expected report to keep Falkner Spearow Peck selectable")
    if not immunity_rows["Fury Attack"]["wont_pick"]:
        raise AssertionError("expected report to block immune Fury Attack into Gastly")
    if immunity_rows["Fury Attack"]["selector_probability"] != 0.0:
        raise AssertionError("expected report to give immune Fury Attack zero selector probability")
    print("PASS: damage-ai-report self-test")
    return 0
