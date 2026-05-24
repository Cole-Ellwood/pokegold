"""Player-facing Boss AI move score probe."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Sequence

from tools.boss_ai_preference.data import PreferenceDataError
from tools.damage_debugger import battle_calc
from tools.damage_debugger import state as damage_state
from tools.damage_debugger import tables
from tools.trace import boss_ai_trace_capture as capture
from tools.trace import runtime as trace_runtime

from .rom_contribution_trace import (
    MemoryPatch,
    run_rom_contribution_trace,
    run_rom_contribution_trace_for_route,
)
from .rom_scenarios import select_from_score_bytes


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "audit/boss_ai_trace/live_capture_manifest.json"
AI_TIERS = ROOT / "data/trainers/ai_tiers.asm"
BLOCKED_SCORE = 80
PARTY_LENGTH = 6
TIER_VALUES = {
    "AI_TIER_EARLY": 1,
    "AI_TIER_MID": 2,
    "AI_TIER_LATE": 3,
}


class MoveScoreProbeError(PreferenceDataError):
    """User-facing move score probe error."""


@dataclass(frozen=True)
class ProbeInputs:
    trainer_id: str
    trainer_class: str
    trainer_index: int
    enemy_selector: str
    player_slot: int
    attacker: damage_state.ExactPokemonState
    defender: damage_state.ExactPokemonState
    enemy_party: tuple[damage_state.ExactPokemonState, ...]
    enemy_party_index: int
    enemy_party_dvs: tuple[int, int, int, int]
    route_id: str | None
    route_state: Path | None
    battery_save: Path


def run_move_score_probe(
    *,
    trainer: str,
    enemy: str,
    player_save: Path,
    player_slot: int,
    sleep_clause: str = "inactive",
    trace: bool = False,
    rom: Path = capture.DEFAULT_ROM,
    symbols: Path = capture.DEFAULT_SYMBOLS,
    manifest: Path = DEFAULT_MANIFEST,
) -> dict[str, Any]:
    inputs = resolve_probe_inputs(
        trainer=trainer,
        enemy=enemy,
        player_save=player_save,
        player_slot=player_slot,
        rom=rom,
        symbols=symbols,
        manifest=manifest,
    )
    return build_move_score_report(
        inputs,
        sleep_clause=sleep_clause,
        trace=trace,
        rom=rom,
        symbols=symbols,
    )


def build_move_score_report(
    inputs: ProbeInputs,
    *,
    sleep_clause: str,
    trace: bool,
    rom: Path = capture.DEFAULT_ROM,
    symbols: Path = capture.DEFAULT_SYMBOLS,
) -> dict[str, Any]:
    variants = ["inactive", "active"] if sleep_clause == "both" else [sleep_clause]
    damage_report = battle_calc.calculate_all_moves(inputs.attacker, inputs.defender)
    reports = []
    for variant in variants:
        reports.append(
            run_probe_variant(
                inputs,
                damage_report=damage_report,
                sleep_clause=variant,
                trace=trace,
                rom=rom,
                symbols=symbols,
            )
        )
    return {
        "schema_version": 1,
        "source": "boss_ai_move_score_probe",
        "trainer": {
            "trainer_id": inputs.trainer_id,
            "trainer_class": inputs.trainer_class,
            "trainer_index": inputs.trainer_index,
        },
        "enemy_selector": inputs.enemy_selector,
        "player_slot": inputs.player_slot,
        "attacker": damage_state.state_to_json(inputs.attacker),
        "defender": damage_state.state_to_json(inputs.defender),
        "damage": json.loads(battle_calc.report_to_json(damage_report)),
        "variants": reports,
    }


def _self_test_noctowl_drowzee_inputs(
    *,
    battery_save: Path,
    manifest: Path = DEFAULT_MANIFEST,
) -> ProbeInputs:
    trainer_constant, party = damage_state.resolve_trainer_party("FALKNER1")
    enemy_party_index = damage_state.select_trainer_mon_index(party, "NOCTOWL")
    dvs = damage_state.parse_trainer_dvs()[trainer_constant.trainer_class]
    enemy_party = tuple(
        damage_state.state_from_trainer_mon(party_mon, trainer_dvs=dvs)
        for party_mon in party.mons
    )
    attacker = enemy_party[enemy_party_index]
    defender = damage_state.state_from_exact_values(
        species="DROWZEE",
        level=13,
        item="NO_ITEM",
        moves=("TACKLE", "HYPNOSIS", "DISABLE", "NO_MOVE"),
        current_hp=50,
        max_hp=50,
        atk=18,
        defense=26,
        speed=16,
        sp_atk=18,
        sp_def=30,
    )
    route_id, route_state = find_route_probe(
        manifest,
        route_id_candidates(trainer_constant.trainer_class, trainer_constant.trainer_id),
    )
    return ProbeInputs(
        trainer_id=trainer_constant.trainer_id,
        trainer_class=trainer_constant.trainer_class,
        trainer_index=trainer_constant.trainer_index,
        enemy_selector="NOCTOWL",
        player_slot=1,
        attacker=attacker,
        defender=defender,
        enemy_party=enemy_party,
        enemy_party_index=enemy_party_index,
        enemy_party_dvs=dvs,
        route_id=route_id,
        route_state=route_state,
        battery_save=battery_save,
    )


def _self_test_spearow_gastly_inputs(
    *,
    battery_save: Path,
    manifest: Path = DEFAULT_MANIFEST,
) -> ProbeInputs:
    trainer_constant, party = damage_state.resolve_trainer_party("FALKNER1")
    enemy_party_index = damage_state.select_trainer_mon_index(party, "SPEAROW")
    dvs = damage_state.parse_trainer_dvs()[trainer_constant.trainer_class]
    enemy_party = tuple(
        damage_state.state_from_trainer_mon(party_mon, trainer_dvs=dvs)
        for party_mon in party.mons
    )
    attacker = enemy_party[enemy_party_index]
    defender = damage_state.state_from_exact_values(
        species="GASTLY",
        level=14,
        item="NO_ITEM",
        moves=("LICK", "HYPNOSIS", "CONFUSION", "NIGHT_SHADE"),
        current_hp=35,
        max_hp=35,
        atk=16,
        defense=15,
        speed=31,
        sp_atk=34,
        sp_def=18,
    )
    route_id, route_state = find_route_probe(
        manifest,
        route_id_candidates(trainer_constant.trainer_class, trainer_constant.trainer_id),
    )
    return ProbeInputs(
        trainer_id=trainer_constant.trainer_id,
        trainer_class=trainer_constant.trainer_class,
        trainer_index=trainer_constant.trainer_index,
        enemy_selector="SPEAROW",
        player_slot=1,
        attacker=attacker,
        defender=defender,
        enemy_party=enemy_party,
        enemy_party_index=enemy_party_index,
        enemy_party_dvs=dvs,
        route_id=route_id,
        route_state=route_state,
        battery_save=battery_save,
    )


def write_fresh_self_test_state(
    state_path: Path,
    *,
    rom: Path = capture.DEFAULT_ROM,
) -> None:
    pyboy = trace_runtime.open_pyboy(rom, "PyBoy is required for move-score probe self-tests")
    trace_runtime.disable_realtime(pyboy)
    try:
        pyboy.tick(300, False, False)
        with state_path.open("wb") as fh:
            pyboy.save_state(fh)
    finally:
        pyboy.stop(save=False)


def build_self_test_report(
    *,
    sleep_clause: str = "both",
    trace: bool = False,
) -> dict[str, Any]:
    with TemporaryDirectory(prefix="move_score_probe_") as temp_dir:
        state_path = Path(temp_dir) / "fresh.state"
        write_fresh_self_test_state(state_path)
        inputs = _self_test_noctowl_drowzee_inputs(battery_save=state_path)
        return build_move_score_report(
            replace(inputs, battery_save=state_path),
            sleep_clause=sleep_clause,
            trace=trace,
        )


def resolve_probe_inputs(
    *,
    trainer: str,
    enemy: str,
    player_save: Path,
    player_slot: int,
    rom: Path,
    symbols: Path,
    manifest: Path,
) -> ProbeInputs:
    trainer_constant, party = damage_state.resolve_trainer_party(trainer)
    enemy_party_index = damage_state.select_trainer_mon_index(party, enemy)
    dvs = damage_state.parse_trainer_dvs()[trainer_constant.trainer_class]
    enemy_party = tuple(
        damage_state.state_from_trainer_mon(party_mon, trainer_dvs=dvs)
        for party_mon in party.mons
    )
    attacker = enemy_party[enemy_party_index]
    if player_save.suffix.lower() == ".state":
        defender = damage_state.party_state_from_state(
            player_save,
            player_slot,
            rom=rom,
            symbols_path=symbols,
        )
    else:
        defender = damage_state.party_state_from_save(
            player_save,
            player_slot,
            rom=rom,
            symbols_path=symbols,
        )
    route_id, route_state = find_route_probe(
        manifest,
        route_id_candidates(trainer_constant.trainer_class, trainer_constant.trainer_id),
    )
    return ProbeInputs(
        trainer_id=trainer_constant.trainer_id,
        trainer_class=trainer_constant.trainer_class,
        trainer_index=trainer_constant.trainer_index,
        enemy_selector=enemy,
        player_slot=player_slot,
        attacker=attacker,
        defender=defender,
        enemy_party=enemy_party,
        enemy_party_index=enemy_party_index,
        enemy_party_dvs=dvs,
        route_id=route_id,
        route_state=route_state,
        battery_save=player_save,
    )


def route_id_candidates(trainer_class: str, trainer_id: str) -> tuple[str, ...]:
    class_route = trainer_class.lower()
    trainer_route = trainer_id.lower()
    trainer_base = trainer_route.rstrip("0123456789")
    candidates = [
        class_route,
        f"{class_route}_{trainer_route}",
        f"{class_route}_{trainer_base}",
        trainer_route,
        trainer_base,
    ]
    return tuple(dict.fromkeys(candidate for candidate in candidates if candidate))


def resolve_route_id(manifest_path: Path, route_ids: Sequence[str]) -> str:
    return str(resolve_route_entry(manifest_path, route_ids).get("id", "")).lower()


def resolve_route_entry(manifest_path: Path, route_ids: Sequence[str]) -> dict[str, Any]:
    if not manifest_path.exists():
        raise MoveScoreProbeError(f"missing Boss AI trace manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    captures = manifest.get("captures", [])
    if not isinstance(captures, list):
        raise MoveScoreProbeError(f"malformed manifest captures: {manifest_path}")
    route_id_set = {route_id.lower() for route_id in route_ids}
    for capture_entry in captures:
        if not isinstance(capture_entry, dict):
            continue
        capture_id = str(capture_entry.get("id", "")).lower()
        if capture_id not in route_id_set:
            continue
        return capture_entry
    raise MoveScoreProbeError(
        "no trace manifest route for trainer id(s): " + ", ".join(route_ids)
    )


def find_route_id(manifest_path: Path, route_ids: Sequence[str]) -> str | None:
    try:
        return resolve_route_id(manifest_path, route_ids)
    except MoveScoreProbeError as exc:
        if str(exc).startswith("no trace manifest route") or str(exc).startswith("missing Boss AI trace manifest"):
            return None
        raise


def find_route_probe(manifest_path: Path, route_ids: Sequence[str]) -> tuple[str | None, Path | None]:
    try:
        entry = resolve_route_entry(manifest_path, route_ids)
    except MoveScoreProbeError as exc:
        if str(exc).startswith("no trace manifest route") or str(exc).startswith("missing Boss AI trace manifest"):
            return None, None
        raise
    route_id = str(entry.get("id", "")).lower()
    route_state = route_state_path(entry)
    return route_id, route_state


def route_state_path(route_entry: dict[str, Any]) -> Path | None:
    raw = route_entry.get("pre_choice_state") or route_entry.get("save_state")
    if not isinstance(raw, str) or raw == "":
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    return path if path.exists() else None


def run_probe_variant(
    inputs: ProbeInputs,
    *,
    damage_report: battle_calc.BattleCalcReport,
    sleep_clause: str,
    trace: bool,
    rom: Path,
    symbols: Path,
) -> dict[str, Any]:
    if sleep_clause not in {"inactive", "active"}:
        raise MoveScoreProbeError("--sleep-clause must be inactive, active, or both")
    patches = memory_patches_for_probe(
        inputs,
        sleep_clause_active=(sleep_clause == "active"),
    )
    base_state_label = f"route:{inputs.route_id}" if inputs.route_id is not None else ""
    if inputs.route_state is not None:
        base_state_label = str(inputs.route_state)
        trace_report = run_rom_contribution_trace(
            save_state=inputs.route_state,
            rom=rom,
            symbols_path=symbols,
            metadata={
                "probe": "move-score-probe",
                "trainer": inputs.trainer_id,
                "enemy": inputs.attacker.species,
                "player": inputs.defender.species,
                "sleep_clause": sleep_clause,
            },
            memory_patches=patches,
        )
    elif inputs.route_id is not None:
        trace_report = run_rom_contribution_trace_for_route(
            boss_id=inputs.route_id,
            rom=rom,
            symbols_path=symbols,
            out_dir=probe_out_dir(inputs, sleep_clause),
            metadata={
                "probe": "move-score-probe",
                "trainer": inputs.trainer_id,
                "enemy": inputs.attacker.species,
                "player": inputs.defender.species,
                "sleep_clause": sleep_clause,
            },
            memory_patches=patches,
        )
    elif inputs.battery_save.suffix.lower() == ".state":
        base_state = inputs.battery_save
        base_state_label = str(base_state)
        trace_report = run_rom_contribution_trace(
            save_state=base_state,
            rom=rom,
            symbols_path=symbols,
            metadata={
                "probe": "move-score-probe",
                "trainer": inputs.trainer_id,
                "enemy": inputs.attacker.species,
                "player": inputs.defender.species,
                "sleep_clause": sleep_clause,
            },
            memory_patches=patches,
        )
    else:
        base_state = damage_state.cached_post_continue_state(
            inputs.battery_save,
            rom=rom,
            symbols_path=symbols,
        )
        base_state_label = str(base_state)
        trace_report = run_rom_contribution_trace(
            save_state=base_state,
            rom=rom,
            symbols_path=symbols,
            metadata={
                "probe": "move-score-probe",
                "trainer": inputs.trainer_id,
                "enemy": inputs.attacker.species,
                "player": inputs.defender.species,
                "sleep_clause": sleep_clause,
            },
            memory_patches=patches,
        )
    move_names = capture.parse_move_names(capture.MOVE_CONSTANTS)
    selector = select_from_score_bytes(
        scenario_id=f"{inputs.trainer_id}:{inputs.attacker.species}:{sleep_clause}",
        tier=int(trace_report.get("tier", 1) or 1),
        move_ids=list(trace_report["move_ids"]),
        scores=list(trace_report["move_scores"]),
        move_names=move_names,
    )
    rows = rows_for_variant(
        damage_report=damage_report,
        trace_report=trace_report,
        selector=selector,
    )
    warnings = warnings_for_rows(rows)
    result = {
        "sleep_clause": sleep_clause,
        "evidence": "seeded-ai-choose-move + hook-snapshot",
        "base_state": trace_report.get("base_state", base_state_label),
        "move_ids": trace_report["move_ids"],
        "pre_model_scores": trace_report["pre_model_scores"],
        "post_model_scores": trace_report["post_model_scores"],
        "final_scores": trace_report["move_scores"],
        "selector": selector,
        "chosen": trace_report["chosen"],
        "rows": rows,
        "warnings": warnings,
        "trace_summary": {
            "event_count": trace_report.get("event_count", 0),
            "changed_event_count": trace_report.get("changed_event_count", 0),
            "rule_entry_count": trace_report.get("rule_entry_count", 0),
            "helper_snapshot_count": trace_report.get("helper_snapshot_count", 0),
        },
    }
    if trace:
        result["trace_report"] = trace_report
    return result


def probe_out_dir(inputs: ProbeInputs, sleep_clause: str) -> Path:
    key = "|".join(
        [
            inputs.trainer_id,
            inputs.attacker.species,
            inputs.defender.species,
            str(inputs.player_slot),
            sleep_clause,
            str(inputs.battery_save.resolve()),
        ]
    )
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    return ROOT / ".local/tmp/damage_debugger/move_score_probe" / digest


def rows_for_variant(
    *,
    damage_report: battle_calc.BattleCalcReport,
    trace_report: dict[str, Any],
    selector: dict[str, Any],
) -> list[dict[str, Any]]:
    probabilities = {
        int(slot): float(probability)
        for slot, probability in selector.get("probabilities_by_slot", {}).items()
    }
    final_scores = [int(value) for value in trace_report["move_scores"]]
    pre_scores = [int(value) for value in trace_report["pre_model_scores"]]
    post_scores = [int(value) for value in trace_report["post_model_scores"]]
    helper_metrics = helper_metrics_by_slot(trace_report.get("helper_snapshots", []))
    block_reasons = block_reasons_by_slot(trace_report.get("events", []))
    rows: list[dict[str, Any]] = []
    for index, damage_row in enumerate(damage_report.moves):
        if damage_row.move_id == 0:
            continue
        score = final_scores[index] if index < len(final_scores) else 255
        probability = probabilities.get(index, 0.0)
        rows.append(
            {
                "slot": index + 1,
                "slot_index": index,
                "move_id": damage_row.move_id,
                "move_name": damage_row.move_name,
                "damage_category": damage_row.category,
                "damage_low": damage_row.damage_low,
                "damage_high": damage_row.damage_high,
                "damage_notes": list(damage_row.notes),
                "pre_model_score": pre_scores[index] if index < len(pre_scores) else None,
                "post_model_score": post_scores[index] if index < len(post_scores) else None,
                "final_score": score,
                "status": status_for_row(
                    index,
                    damage_row=damage_row,
                    rows=damage_report.moves,
                    blocked=score >= BLOCKED_SCORE,
                    block_reason=block_reasons.get(index, ""),
                ),
                "wont_pick": score >= BLOCKED_SCORE,
                "mismatch": False,
                "selector_probability": probability,
                "helper_metrics": helper_metrics.get(index, unavailable_metrics()),
            }
        )
    apply_mismatch_flags(rows)
    return rows


def block_reasons_by_slot(events: list[dict[str, Any]]) -> dict[int, str]:
    reasons: dict[int, str] = {}
    for event in events:
        if not event.get("changed"):
            continue
        if int(event.get("score_after", 0)) < BLOCKED_SCORE:
            continue
        candidate = event.get("candidate", {})
        if not isinstance(candidate, dict):
            continue
        slot_index = int(candidate.get("slot_index", -1))
        if slot_index < 0:
            continue
        source = event.get("source", {})
        source_label = str(source.get("source_label", "")) if isinstance(source, dict) else ""
        rule_id = str(source.get("rule_id", "")) if isinstance(source, dict) else ""
        callsite_symbol = str(source.get("callsite_symbol", "")) if isinstance(source, dict) else ""
        if "DamagingMoveBlockedByTypeImmunity" in callsite_symbol:
            reasons[slot_index] = "type immunity"
        elif "StatusMoveWouldFailPublicly" in source_label or "status_move_would_fail" in rule_id:
            reasons[slot_index] = "status would fail"
        elif "ApplyDamagePressureBias" in source_label or "apply_damage_pressure_bias" in rule_id:
            reasons[slot_index] = "damage gate"
        else:
            reasons[slot_index] = source_label or rule_id or "score gate"
    return reasons


def status_for_row(
    slot_index: int,
    *,
    damage_row: battle_calc.MoveDamageResult,
    rows: list[battle_calc.MoveDamageResult],
    blocked: bool,
    block_reason: str,
) -> str:
    if not blocked:
        return "eligible"
    if block_reason == "damage gate":
        stronger = strongest_other_damage(rows, slot_index)
        if stronger is not None and stronger.damage_high > damage_row.damage_high:
            return f"won't pick ({stronger.move_name} covers it)"
        return "won't pick (damage gate)"
    if block_reason:
        return f"won't pick ({block_reason})"
    return "won't pick"


def strongest_other_damage(
    rows: list[battle_calc.MoveDamageResult],
    slot_index: int,
) -> battle_calc.MoveDamageResult | None:
    candidates = [
        row
        for index, row in enumerate(rows)
        if index != slot_index and row.move_id != 0 and row.damage_high > 0
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda row: row.damage_high)


def apply_mismatch_flags(rows: list[dict[str, Any]]) -> None:
    blocked = [row for row in rows if row["wont_pick"]]
    selectable = [row for row in rows if not row["wont_pick"]]
    selectable_damage = [row for row in selectable if row["damage_high"] > 0]
    comparison_rows = selectable_damage or selectable
    for row in rows:
        row["mismatch"] = False
    for blocked_row in blocked:
        stronger_than_selectable = [
            row for row in comparison_rows if blocked_row["damage_high"] > row["damage_high"]
        ]
        if not stronger_than_selectable:
            continue
        blocked_row["mismatch"] = True
        for row in stronger_than_selectable:
            row["mismatch"] = True


def helper_metrics_by_slot(snapshots: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for snapshot in snapshots:
        candidate = snapshot.get("candidate", {})
        if not isinstance(candidate, dict):
            continue
        slot_index = int(candidate.get("slot_index", -1))
        if slot_index < 0:
            continue
        helper = snapshot.get("helper", {})
        helper_id = str(helper.get("helper_id", "")) if isinstance(helper, dict) else ""
        if not helper_id:
            continue
        out.setdefault(slot_index, {})[helper_id] = {
            "value": None,
            "evidence": "hook-snapshot",
            "snapshot_index": snapshot.get("index"),
            "registers": snapshot.get("registers", {}),
            "move_struct": snapshot.get("move_struct", {}),
        }
    return out


def unavailable_metrics() -> dict[str, Any]:
    return {
        "ai_damage_rank": {
            "value": None,
            "evidence": "unavailable",
            "reason": "no hook snapshot captured for this move",
        }
    }


def warnings_for_rows(rows: list[dict[str, Any]]) -> list[str]:
    selectable = [row for row in rows if not row["wont_pick"]]
    blocked = [row for row in rows if row["wont_pick"]]
    selectable_damage = [row for row in selectable if row["damage_high"] > 0]
    comparison_rows = selectable_damage or selectable
    pairs = [
        (left, right)
        for left in blocked
        for right in comparison_rows
        if int(left["damage_high"]) > int(right["damage_high"])
    ]
    if not pairs:
        return []
    left, right = max(
        pairs,
        key=lambda pair: (
            int(pair[0]["damage_high"]) - int(pair[1]["damage_high"]),
            int(pair[0]["damage_high"]),
        ),
    )
    return [
        f"{left['move_name']} does {left['damage_low']}-{left['damage_high']} "
        f"damage and {right['move_name']} does {right['damage_low']}-{right['damage_high']}, "
        f"but {left['move_name']} is marked won't pick while {right['move_name']} is selectable."
    ]


def memory_patches_for_probe(
    inputs: ProbeInputs,
    *,
    sleep_clause_active: bool,
) -> list[MemoryPatch]:
    tier, weight_row = ai_tier_for_trainer(inputs.trainer_class, inputs.trainer_id)
    patches: list[MemoryPatch] = []
    patches.extend(synthetic_boss_ai_state_clear_patches())
    patches.extend(mon_patches("wEnemyMon", inputs.attacker, include_base_stats=True))
    patches.extend(mon_patches("wBattleMon", inputs.defender, include_base_stats=False))
    patches.extend(byte_patches("wEnemyMonDVs", list(damage_state.dv_bytes(inputs.attacker.dvs))))
    patches.extend(enemy_party_patches(inputs.enemy_party, inputs.enemy_party_dvs))
    patches.extend(byte_patches("wEnemyAIMoveScores", [20, 20, 20, 20]))
    patches.extend(byte_patches("wEnemyMonPP", [30, 30, 30, 30]))
    patches.extend(byte_patches("wBattleMonPP", [30, 30, 30, 30]))
    patches.extend(byte_patches("wEnemyStatLevels", [7, 7, 7, 7, 7, 7, 7]))
    patches.extend(byte_patches("wPlayerStatLevels", [7, 7, 7, 7, 7, 7, 7]))
    patches.extend(
        [
            MemoryPatch("wOtherTrainerClass", 0, trainer_class_id(inputs.trainer_class)),
            MemoryPatch("wOtherTrainerID", 0, inputs.trainer_index),
            MemoryPatch("wTrainerClass", 0, trainer_class_id(inputs.trainer_class)),
            MemoryPatch("wBossAITier", 0, tier),
            MemoryPatch("wBossAITierWeightRow", 0, weight_row),
            MemoryPatch("wBossAIMoveChoiceReady", 0, 0),
            MemoryPatch("wBattleMode", 0, 2),
            MemoryPatch("wLinkMode", 0, 0),
            MemoryPatch("hBattleTurn", 0, 1),
            MemoryPatch("wCurBattleMon", 0, max(0, inputs.player_slot - 1)),
            MemoryPatch("wCurOTMon", 0, inputs.enemy_party_index),
            MemoryPatch("wCurEnemyMove", 0, 0),
            MemoryPatch("wCurEnemyMoveNum", 0, 0),
            MemoryPatch("wEnemyDisabledMove", 0, 0),
            MemoryPatch("wEnemyChoiceLockedMove", 0, 0),
            MemoryPatch("wPlayerScreens", 0, 0),
            MemoryPatch("wEnemyScreens", 0, 0),
            MemoryPatch("wBattleWeather", 0, 0),
            MemoryPatch("wEnemySleepClauseSlot", 0, inputs.player_slot if sleep_clause_active else 0),
            MemoryPatch("wPlayerSleepClauseSlot", 0, 0),
        ]
    )
    for symbol_name in (
        "wPlayerSubStatus1",
        "wPlayerSubStatus2",
        "wPlayerSubStatus3",
        "wPlayerSubStatus4",
        "wPlayerSubStatus5",
        "wEnemySubStatus1",
        "wEnemySubStatus2",
        "wEnemySubStatus3",
        "wEnemySubStatus4",
        "wEnemySubStatus5",
    ):
        patches.append(MemoryPatch(symbol_name, 0, 0))
    patches.extend(trace_field_clear_patches())
    return patches


def synthetic_boss_ai_state_clear_patches() -> list[MemoryPatch]:
    patches: list[MemoryPatch] = []
    for symbol_name in (
        "wBossAIMoveChoiceReady",
        "wBossAISwitchConfidence",
        "wBossAILastSwitchedOut",
        "wBossAISwitchCooldown",
        "wBossAIPlayerSwitchCount",
        "wBossAIPendingPlayerSwitchCount",
        "wBossAITurnsElapsed",
        "wBossAIPlanId",
        "wBossAIPlanPhase",
        "wBossAIPlanConfidence",
        "wBossAIWinconMonIdx",
        "wBossAITargetMonIdx",
        "wBossAIScoutedMask",
        "wBossAIRepeatCount",
        "wBossAILastChosenMove",
        "wBossAIPlausibleTypeMaskSpecies",
        "wBossAIPlausibleTypeMaskLevel",
        "wBossAISeenPlayerSpeciesCount",
        "wBossAISeenPlayerAliveMask",
        "wBossAITemp",
        "wBossAITemp2",
        "wBossAITemp3",
        "wBossAITemp4",
        "wBossAITemp5",
        "wLastPlayerMove",
        "wLastEnemyMove",
        "wEnemySwitchMonParam",
        "wEnemySwitchMonIndex",
    ):
        patches.append(MemoryPatch(symbol_name, 0, 0))
    patches.extend(word_patches("wBossAIScorePtr", 0))
    for symbol_name, width in (
        ("wBossAIPlausibleTypeMaskCache", 4),
        ("wBossAISeenPlayerSpecies", PARTY_LENGTH),
        ("wBossAIRevealedMovesBitmap", PARTY_LENGTH * damage_state.NUM_MOVES),
        ("wBossAILikelyTypeMaskCache", 4),
        ("wBossAIRevealedMovesBitmapSpare", 3),
        ("wBossAISpeciesUsedMoves", PARTY_LENGTH * damage_state.NUM_MOVES),
        ("wPlayerUsedMoves", damage_state.NUM_MOVES),
    ):
        patches.extend(byte_patches(symbol_name, [0] * width))
    for symbol_name in (
        "wBossAIHasKOMoveCache",
        "wBossAIPublicThreatCache",
        "wBossAIRevealedPriorityCache",
        "wBossAIPrimaryThreatCache",
    ):
        patches.append(MemoryPatch(symbol_name, 0, 0xFF))
    return patches


def enemy_party_patches(
    party: tuple[damage_state.ExactPokemonState, ...],
    dvs: tuple[int, int, int, int],
) -> list[MemoryPatch]:
    patches = [MemoryPatch("wOTPartyCount", 0, len(party))]
    species = [mon.species_id for mon in party]
    if len(species) < 6:
        species_values = species + [0xFF] + [0] * (5 - len(species))
        end_value = 0
    else:
        species_values = species[:6]
        end_value = 0xFF
    patches.extend(byte_patches("wOTPartySpecies", species_values))
    patches.append(MemoryPatch("wOTPartyEnd", 0, end_value))
    for slot in range(6):
        values = (
            party_mon_struct_values(party[slot], dvs)
            if slot < len(party)
            else [0] * damage_state.PARTYMON_STRUCT_LENGTH
        )
        patches.extend(byte_patches_at(
            "wOTPartyMon1Species",
            slot * damage_state.PARTYMON_STRUCT_LENGTH,
            values,
        ))
    return patches


def party_mon_struct_values(
    mon: damage_state.ExactPokemonState,
    dvs: tuple[int, int, int, int],
) -> list[int]:
    atk_def, speed_special = damage_state.dv_bytes(dvs)
    values = [0] * damage_state.PARTYMON_STRUCT_LENGTH
    values[0] = mon.species_id
    values[1] = mon.item_id
    values[2:6] = list(mon.moves)
    values[21] = atk_def
    values[22] = speed_special
    values[23:27] = pp_values_for_moves(mon.moves)
    values[27] = mon.happiness
    values[31] = mon.level
    values[32] = mon.status
    values[34] = (mon.current_hp >> 8) & 0xFF
    values[35] = mon.current_hp & 0xFF
    values[36] = (mon.max_hp >> 8) & 0xFF
    values[37] = mon.max_hp & 0xFF
    for offset, stat in zip(
        (38, 40, 42, 44, 46),
        (mon.atk, mon.defense, mon.speed, mon.sp_atk, mon.sp_def),
        strict=True,
    ):
        values[offset] = (stat >> 8) & 0xFF
        values[offset + 1] = stat & 0xFF
    return values


def pp_values_for_moves(moves: tuple[int, int, int, int]) -> list[int]:
    move_names = damage_state.move_name_by_id()
    move_rows = tables.load_moves()
    pps: list[int] = []
    for move_id in moves:
        move_name = move_names.get(move_id)
        row = move_rows.get(move_name or "")
        pps.append(row.pp if row is not None else 0)
    return pps


def ai_tier_for_trainer(trainer_class: str, trainer_id: str) -> tuple[int, int]:
    tier = 0
    weight_row = 0
    in_tier_map = False
    in_ramp_map = False
    for raw in AI_TIERS.read_text(encoding="utf-8").splitlines():
        code = raw.split(";", 1)[0].strip()
        if code == "BossAITierMap:":
            in_tier_map = True
            in_ramp_map = False
            continue
        if code == "BossAITierRampMap:":
            in_tier_map = False
            in_ramp_map = True
            continue
        if code.endswith(":"):
            in_tier_map = False
            in_ramp_map = False
            continue
        if not code.startswith("db "):
            continue
        values = [part.strip() for part in code[3:].split(",")]
        if values == ["0"]:
            in_tier_map = False
            in_ramp_map = False
            continue
        if in_tier_map and len(values) >= 3:
            if values[0] == trainer_class and values[1] == trainer_id:
                tier = TIER_VALUES.get(values[2], 0)
                weight_row = max(0, tier - 1)
        elif in_ramp_map and len(values) >= 3:
            if values[0] == trainer_class and values[1] == trainer_id:
                weight_row = int(values[2], 0)
    if tier == 0:
        raise MoveScoreProbeError(
            f"{trainer_class}, {trainer_id} is not in BossAITierMap"
        )
    return tier, weight_row


def trace_field_clear_patches() -> list[MemoryPatch]:
    patches: list[MemoryPatch] = []
    for symbol_name, width in capture.TRACE_FIELDS:
        fill = 0xFF if symbol_name in {
            "wBossAITracePreModelScores",
            "wBossAITracePostModelScores",
        } else 0
        patches.extend(byte_patches(symbol_name, [fill] * width))
    return patches


def trainer_class_id(trainer_class: str) -> int:
    constants = damage_state.load_trainer_constants()
    for item in constants.values():
        if item.trainer_class == trainer_class:
            return item.class_id
    raise MoveScoreProbeError(f"unknown trainer class {trainer_class}")


def mon_patches(
    prefix: str,
    mon: damage_state.ExactPokemonState,
    *,
    include_base_stats: bool,
) -> list[MemoryPatch]:
    patches = [
        MemoryPatch(f"{prefix}Species", 0, mon.species_id),
        MemoryPatch(f"{prefix}Item", 0, mon.item_id),
        MemoryPatch(f"{prefix}Level", 0, mon.level),
        MemoryPatch(f"{prefix}Status", 0, mon.status),
    ]
    patches.extend(byte_patches(f"{prefix}Moves", list(mon.moves)))
    patches.extend(word_patches(f"{prefix}HP", mon.current_hp))
    patches.extend(word_patches(f"{prefix}MaxHP", mon.max_hp))
    patches.extend(word_patches(f"{prefix}Attack", mon.atk))
    patches.extend(word_patches(f"{prefix}Defense", mon.defense))
    patches.extend(word_patches(f"{prefix}Speed", mon.speed))
    patches.extend(word_patches(f"{prefix}SpclAtk", mon.sp_atk))
    patches.extend(word_patches(f"{prefix}SpclDef", mon.sp_def))
    patches.extend(
        [
            MemoryPatch(f"{prefix}Type1", 0, mon.type1),
            MemoryPatch(f"{prefix}Type2", 0, mon.type2),
        ]
    )
    if include_base_stats:
        row = tables.load_base_stats()[mon.species]
        patches.extend(
            byte_patches(
                f"{prefix}BaseStats",
                [row.hp, row.atk, row.def_, row.spe, row.sat],
            )
        )
    return patches


def byte_patches(symbol_name: str, values: list[int]) -> list[MemoryPatch]:
    return byte_patches_at(symbol_name, 0, values)


def byte_patches_at(symbol_name: str, base_offset: int, values: list[int]) -> list[MemoryPatch]:
    return [
        MemoryPatch(symbol_name=symbol_name, offset=base_offset + offset, value=value)
        for offset, value in enumerate(values)
    ]


def word_patches(symbol_name: str, value: int) -> list[MemoryPatch]:
    return [
        MemoryPatch(symbol_name=symbol_name, offset=0, value=(value >> 8) & 0xFF),
        MemoryPatch(symbol_name=symbol_name, offset=1, value=value & 0xFF),
    ]


def format_move_score_probe(report: dict[str, Any]) -> str:
    lines: list[str] = []
    attacker = report["attacker"]
    defender = report["defender"]
    lines.append(
        f"{attacker['species']} L{attacker['level']} into "
        f"{defender['species']} L{defender['level']}"
    )
    for variant in report["variants"]:
        lines.extend(["", f"Sleep clause: {variant['sleep_clause']}"])
        lines.append(f"{'Move':<11} {'Damage':<8} {'Final':<6} {'Status':<12} Selector Notes")
        for row in variant["rows"]:
            damage = "0" if row["damage_high"] == 0 else f"{row['damage_low']}-{row['damage_high']}"
            probability = row["selector_probability"]
            selector = f"{probability * 100:.1f}%" if probability else "-"
            line = (
                f"{row['move_name']:<11} {damage:<8} {row['final_score']:<6} "
                f"{row['status']:<12} {selector}"
            )
            notes = "; ".join(row.get("damage_notes", []))
            if notes:
                line += f" {notes}"
            lines.append(line)
        for warning in variant["warnings"]:
            lines.append(f"Warning: {warning}")
    return "\n".join(lines)


def run_self_test() -> int:
    report = build_self_test_report()
    type_immunity_report = build_move_score_report(
        _self_test_spearow_gastly_inputs(battery_save=Path("unused.state")),
        sleep_clause="inactive",
        trace=False,
    )
    inputs = _self_test_noctowl_drowzee_inputs(battery_save=Path("unused.state"))
    patches = {
        (patch.symbol_name, patch.offset): patch.value
        for patch in memory_patches_for_probe(inputs, sleep_clause_active=False)
    }
    will_constant, will_party = damage_state.resolve_trainer_party("WILL1")
    will_dvs = damage_state.parse_trainer_dvs()[will_constant.trainer_class]
    will_party_states = tuple(
        damage_state.state_from_trainer_mon(party_mon, trainer_dvs=will_dvs)
        for party_mon in will_party.mons
    )
    will_inputs = ProbeInputs(
        trainer_id=will_constant.trainer_id,
        trainer_class=will_constant.trainer_class,
        trainer_index=will_constant.trainer_index,
        enemy_selector="1",
        player_slot=1,
        attacker=will_party_states[0],
        defender=inputs.defender,
        enemy_party=will_party_states,
        enemy_party_index=0,
        enemy_party_dvs=will_dvs,
        route_id=find_route_id(
            DEFAULT_MANIFEST,
            route_id_candidates(will_constant.trainer_class, will_constant.trainer_id),
        ),
        route_state=None,
        battery_save=Path("unused.state"),
    )
    if will_inputs.route_id is not None:
        raise AssertionError("expected seeded probes not to require a manifest route")
    if patches[("wCurOTMon", 0)] != 2:
        raise AssertionError("expected Noctowl probe to seed wCurOTMon to party slot 3")
    expected_dv_bytes = damage_state.dv_bytes(inputs.attacker.dvs)
    actual_dv_bytes = (patches[("wEnemyMonDVs", 0)], patches[("wEnemyMonDVs", 1)])
    if actual_dv_bytes != expected_dv_bytes:
        raise AssertionError(
            f"expected active enemy DVs {expected_dv_bytes}, got {actual_dv_bytes}"
        )
    base_stat_offsets = sorted(
        offset for (symbol_name, offset) in patches if symbol_name == "wEnemyMonBaseStats"
    )
    if base_stat_offsets != [0, 1, 2, 3, 4]:
        raise AssertionError(f"expected five enemy base stat bytes, got {base_stat_offsets}")
    for symbol_name in ("wBossAIPlanId", "wBossAISeenPlayerSpeciesCount"):
        if patches[(symbol_name, 0)] != 0:
            raise AssertionError(f"expected synthetic probe to clear {symbol_name}")
    if any(patches[("wPlayerUsedMoves", offset)] for offset in range(damage_state.NUM_MOVES)):
        raise AssertionError("expected synthetic probe to clear stale player used moves")
    if any(
        patches[("wBossAISpeciesUsedMoves", offset)]
        for offset in range(PARTY_LENGTH * damage_state.NUM_MOVES)
    ):
        raise AssertionError("expected synthetic probe to clear stale species-used moves")
    if patches[("wBossAIHasKOMoveCache", 0)] != 0xFF:
        raise AssertionError("expected synthetic probe to reset Boss AI cache sentinels")
    if patches[("wOTPartyCount", 0)] != 3:
        raise AssertionError("expected Falkner party count in move-score probe patches")
    if patches[("wOTPartySpecies", 2)] != inputs.attacker.species_id:
        raise AssertionError("expected selected enemy in wOTPartySpecies")
    if patches[("wOTPartyMon1Species", 2 * damage_state.PARTYMON_STRUCT_LENGTH)] != inputs.attacker.species_id:
        raise AssertionError("expected selected enemy party struct to be seeded")
    variants = {variant["sleep_clause"]: variant for variant in report["variants"]}
    inactive = {row["move_name"]: row for row in variants["inactive"]["rows"]}
    active = {row["move_name"]: row for row in variants["active"]["rows"]}
    if inactive["Peck"]["damage_high"] <= inactive["Confusion"]["damage_high"]:
        raise AssertionError("expected Peck oracle damage to exceed Confusion")
    if inactive["Peck"]["wont_pick"] or active["Peck"]["wont_pick"]:
        raise AssertionError("expected Peck to remain selectable against Drowzee")
    if inactive["Confusion"]["wont_pick"] or active["Confusion"]["wont_pick"]:
        raise AssertionError("expected Confusion to remain selectable against Drowzee")
    if inactive["Peck"]["final_score"] >= inactive["Tackle"]["final_score"]:
        raise AssertionError("expected damage ranking to prefer Peck over resisted Tackle")
    if inactive["Hypnosis"]["wont_pick"]:
        raise AssertionError("expected Hypnosis to be selectable when sleep clause is inactive")
    if not active["Hypnosis"]["wont_pick"]:
        raise AssertionError("expected Hypnosis to be blocked when sleep clause is active")
    if variants["inactive"]["warnings"] or variants["active"]["warnings"]:
        raise AssertionError("expected no damage-order mismatch warnings after rank fix")
    immunity_rows = {
        row["move_name"]: row
        for row in type_immunity_report["variants"][0]["rows"]
    }
    if immunity_rows["Peck"]["wont_pick"]:
        raise AssertionError("expected Falkner Spearow Peck to remain selectable into Gastly")
    if not immunity_rows["Fury Attack"]["wont_pick"]:
        raise AssertionError("expected immune Fury Attack to be blocked into Gastly")
    if immunity_rows["Fury Attack"]["selector_probability"] != 0.0:
        raise AssertionError("expected immune Fury Attack to have zero selector probability")
    print("PASS: move-score-probe self-test")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe Boss AI move scores for an exact matchup.")
    parser.add_argument("--trainer", required=False)
    parser.add_argument("--enemy", required=False)
    parser.add_argument("--player-save", type=Path)
    parser.add_argument("--player-slot", type=int, default=1)
    parser.add_argument("--sleep-clause", choices=("inactive", "active", "both"), default="inactive")
    parser.add_argument("--rom", type=Path, default=capture.DEFAULT_ROM)
    parser.add_argument("--symbols", type=Path, default=capture.DEFAULT_SYMBOLS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            return run_self_test()
        missing = [
            name
            for name in ("trainer", "enemy", "player_save")
            if getattr(args, name) in {None, ""}
        ]
        if missing:
            raise MoveScoreProbeError("missing required argument(s): " + ", ".join(missing))
        report = run_move_score_probe(
            trainer=args.trainer,
            enemy=args.enemy,
            player_save=args.player_save,
            player_slot=args.player_slot,
            sleep_clause=args.sleep_clause,
            trace=args.trace,
            rom=args.rom,
            symbols=args.symbols,
            manifest=args.manifest,
        )
        print(json.dumps(report, indent=2, sort_keys=True) if args.json else format_move_score_probe(report))
        return 0
    except (MoveScoreProbeError, PreferenceDataError, tables.InputError) as exc:
        print(f"error: {exc}")
        return 1
    except AssertionError as exc:
        print(f"FAIL: {exc}")
        return 1
    except Exception as exc:
        print(f"internal error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
