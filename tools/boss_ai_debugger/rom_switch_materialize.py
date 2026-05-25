from __future__ import annotations

import io
import json
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError
from tools.headless_battle.simulator import boss_ai_switch_roll_threshold
from tools.trace import boss_ai_trace_capture as capture
from tools.trace import runtime as trace_runtime

from .rom_contribution_trace import apply_memory_patches
from .rom_contribution_trace import MemoryPatch
from .rom_scenarios import load_scenario_batch
from .rom_scenarios import normalize_tier
from .rom_scenarios import scenario_expectation
from .rom_score_materialize import ITEMS
from .rom_score_materialize import SPECIES
from .rom_score_materialize import TYPES
from .rom_score_materialize import patch
from .rom_score_materialize import word_patches
from .rom_selector_materialize import DEFAULT_MANIFEST_PATH


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE_ROUTE = "shared_switch_loop"
DEFAULT_WATCH_FRAMES = 180
SUPPORTED_FAMILIES = ("switch_sack",)
AI_SWITCH_THRESHOLD_EARLY = 80
AI_SWITCH_THRESHOLD_MID = 70
AI_SWITCH_THRESHOLD_LATE = 60
AI_SWITCH_ANTI_LOOP_PENALTY = 10
AI_SWITCH_SACK_BIAS = 8
AI_SWITCH_WINCON_BIAS = 10
BASE_ROUTE_TRAINER_CLASS = {
    "shared_switch_loop": "JASMINE",
}
CLASS_SWITCH_THRESHOLD_MODS = {
    "CHAMPION": -10,
    "KOGA": -8,
    "CLAIR": -6,
    "KAREN": -4,
    "BRUNO": -4,
    "JASMINE": 4,
    "CHUCK": 2,
}

KNOWN_LIMITS = [
    (
        "Switch materialization requires a base state before the real "
        "BossAI_SwitchOrTryItem path reaches switch confidence/param; stale "
        "snapshot states with already-populated switch outputs are rejected."
    ),
    (
        "This proves switch-dispatch proposal behavior and reports the final "
        "source-mirrored switch-roll frequency from observed confidence plus an "
        "explicit or source-derived threshold; it does not prove move score bytes."
    ),
    (
        "Only public battle facts and boss-owned party state are patched; hidden "
        "player party, hidden moves, PP, held items, and current input are not read."
    ),
]


class RomSwitchReplaySession:
    def __init__(
        self,
        *,
        rom: Path = capture.DEFAULT_ROM,
        symbols_path: Path = capture.DEFAULT_SYMBOLS,
    ) -> None:
        self.rom = rom
        self.symbols_path = symbols_path
        self.symbols = capture.parse_symbols(symbols_path)
        capture.require_symbols(self.symbols)
        pyboy_class = trace_runtime.load_pyboy(
            "PyBoy is required for ROM switch materialization"
        )
        self.pyboy = pyboy_class(str(rom), window="null", sound=False, log_level="ERROR")
        trace_runtime.disable_realtime(self.pyboy)
        self.state_cache: dict[Path, bytes] = {}
        self.basis = capture.build_trace_basis_metadata(
            SimpleTraceArgs(rom=rom, symbols=symbols_path)
        )

    def __enter__(self) -> "RomSwitchReplaySession":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def close(self) -> None:
        self.pyboy.stop(save=False)

    def run(
        self,
        *,
        save_state: Path,
        memory_patches: list[MemoryPatch],
        watch_frames: int,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if not save_state.exists():
            raise PreferenceDataError(f"missing save-state: {save_state}")
        self.load_state(save_state)
        validate_switch_materialization_base(capture.read_trace_values(self.pyboy, self.symbols))
        apply_memory_patches(
            self.pyboy,
            self.symbols,
            [*clear_switch_trace_patches(), *memory_patches],
        )
        values, frame = drive_replay_to_switch_observation(
            self.pyboy,
            self.symbols,
            watch_frames=watch_frames,
        )
        basis = dict(self.basis)
        if metadata:
            basis.update(metadata)
        return build_switch_report(
            save_state=save_state,
            basis=basis,
            values=values,
            frame=frame,
            memory_patches=memory_patches,
        )

    def load_state(self, save_state: Path) -> None:
        state_bytes = self.state_cache.get(save_state)
        if state_bytes is None:
            state_bytes = save_state.read_bytes()
            self.state_cache[save_state] = state_bytes
        self.pyboy.load_state(io.BytesIO(state_bytes))


def run_rom_switch_materialization_from_path(
    scenarios_path: Path,
    *,
    limit: int = 20,
    base_route: str = DEFAULT_BASE_ROUTE,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    rom: Path = capture.DEFAULT_ROM,
    symbols_path: Path = capture.DEFAULT_SYMBOLS,
    watch_frames: int = DEFAULT_WATCH_FRAMES,
    switch_threshold: int | None = None,
) -> dict[str, Any]:
    scenarios = load_scenario_batch(scenarios_path)
    if limit > 0:
        scenarios = scenarios[:limit]
    return run_rom_switch_materialization(
        scenarios,
        base_route=base_route,
        manifest_path=manifest_path,
        rom=rom,
        symbols_path=symbols_path,
        watch_frames=watch_frames,
        switch_threshold=switch_threshold,
        source=str(scenarios_path),
    )


def run_rom_switch_materialization(
    scenarios: list[dict[str, Any]],
    *,
    base_route: str = DEFAULT_BASE_ROUTE,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    rom: Path = capture.DEFAULT_ROM,
    symbols_path: Path = capture.DEFAULT_SYMBOLS,
    watch_frames: int = DEFAULT_WATCH_FRAMES,
    switch_threshold: int | None = None,
    source: str = "inline",
) -> dict[str, Any]:
    if not scenarios:
        raise PreferenceDataError("no scenarios supplied for ROM switch materialization")
    if watch_frames <= 0:
        raise PreferenceDataError("--watch-frames must be positive")
    if switch_threshold is not None:
        switch_threshold = parse_optional_byte(switch_threshold, "switch_threshold")

    manifest_entry = load_manifest_save_entry(manifest_path, base_route)
    validate_manifest_trace_basis(manifest_path, rom=rom, symbols_path=symbols_path)
    base_state_field = switch_materialization_state_field(manifest_entry)
    base_state = resolve_manifest_path(str(manifest_entry[base_state_field]))
    if not base_state.exists():
        raise PreferenceDataError(
            f"missing switch {base_state_field}: {base_state}"
        )

    started = time.perf_counter()
    verdicts: list[dict[str, Any]] = []
    with ExitStack() as stack:
        session = stack.enter_context(
            RomSwitchReplaySession(rom=rom, symbols_path=symbols_path)
        )
        for scenario in scenarios:
            scenario_id = str(scenario.get("id", "unnamed"))
            if scenario.get("family") not in SUPPORTED_FAMILIES:
                verdicts.append(skipped_verdict(scenario_id, "unsupported scenario family"))
                continue
            try:
                report = session.run(
                    save_state=base_state,
                    watch_frames=watch_frames,
                    metadata={
                        "boss": base_route,
                        "notes": f"generated-switch-materialization:{scenario_id}",
                    },
                    memory_patches=switch_materialization_patches(scenario),
                )
                verdicts.append(
                    switch_verdict_from_report(
                        scenario,
                        report,
                        base_route=base_route,
                        switch_threshold=switch_threshold,
                    )
                )
            except Exception as exc:
                verdicts.append(skipped_verdict(scenario_id, str(exc), status="error"))

    elapsed = time.perf_counter() - started
    checked = [verdict for verdict in verdicts if verdict["status"] == "pass"]
    errors = [verdict for verdict in verdicts if verdict["status"] == "error"]
    disagreements = [
        verdict
        for verdict in checked
        if int(verdict.get("rom_policy", {}).get("severity", 0)) > 0
    ]
    return {
        "schema_version": 1,
        "source": source,
        "kind": "rom_switch_materialization",
        "base_route": base_route,
        "base_state": trace_runtime.display_path(base_state),
        "base_state_field": base_state_field,
        "scenario_count": len(scenarios),
        "checked_count": len(checked),
        "skipped_count": len(verdicts) - len(checked),
        "error_count": len(errors),
        "policy_disagreement_count": len(disagreements),
        "elapsed_seconds": elapsed,
        "materializations_per_minute": len(checked) / elapsed * 60 if elapsed else 0.0,
        "known_limits": KNOWN_LIMITS,
        "verdicts": verdicts,
    }


def switch_materialization_patches(scenario: dict[str, Any]) -> list[MemoryPatch]:
    tags = scenario_condition_tags(scenario)
    tier = normalize_tier(scenario.get("tier", "late"))
    active_converts = "active_pressure_converts" in tags
    defensive_sack = "defensive_sack_owner" in tags
    enemy_hp = 22 if defensive_sack else 80
    player_hp = 20 if active_converts else 80
    patches = [
        patch("wBossAITier", tier),
        patch("wBossAITierWeightRow", max(0, tier - 1)),
        patch("wEnemyMonItem", ITEMS["NO_ITEM"]),
        patch("wEnemyDisabledMove", 0),
        patch("wCurOTMon", 0),
        patch("wOTPartyCount", 2),
        patch("wOTPartySpecies", SPECIES["QWILFISH"], 0),
        patch("wOTPartySpecies", SPECIES["GENGAR"], 1),
        patch("wOTPartySpecies", 0xFF, 2),
        patch("wOTPartyMon2Species", SPECIES["GENGAR"]),
        patch("wOTPartyMon2Level", 50),
        patch("wBattleMonSpecies", SPECIES["STARMIE"]),
        patch("wBattleMonType1", TYPES["GROUND"]),
        patch("wBattleMonType2", TYPES["GROUND"]),
        patch("wEnemyMonSpecies", SPECIES["QWILFISH"]),
        patch("wEnemyMonType1", TYPES["POISON"]),
        patch("wEnemyMonType2", TYPES["WATER"]),
        patch("wBattleMonStatus", 0),
        patch("wEnemyMonStatus", 0),
        patch("wEnemySwitchMonParam", 0),
        patch("wEnemySwitchMonIndex", 0),
        patch("wBossAISwitchCooldown", 0),
        patch("wBossAILastSwitchedOut", 0),
        patch("wBossAIRepeatCount", 0),
        patch("wBossAILastChosenMove", 0),
        patch("wBossAIWinconMonIdx", 2),
        patch("wBossAIPlanId", 1 if "wincon_preservation" in tags else 0),
        patch("wBossAIPlanPhase", 1),
        patch("wBossAIPlanConfidence", 60),
        patch("wPlayerUsedMoves", 0x59, 0),
        patch("wPlayerUsedMoves", 0, 1),
        patch("wPlayerUsedMoves", 0, 2),
        patch("wPlayerUsedMoves", 0, 3),
    ]
    patches.extend(word_patches("wEnemyMonHP", enemy_hp))
    patches.extend(word_patches("wEnemyMonMaxHP", 100))
    patches.extend(word_patches("wBattleMonHP", player_hp))
    patches.extend(word_patches("wBattleMonMaxHP", 100))
    patches.extend(word_patches("wOTPartyMon2HP", 80))
    patches.extend(word_patches("wOTPartyMon2MaxHP", 100))
    return patches


def drive_replay_to_switch_observation(
    pyboy: Any,
    symbols: dict[str, capture.Symbol],
    *,
    watch_frames: int,
) -> tuple[dict[str, list[int]], int]:
    last_values: dict[str, list[int]] | None = None
    for frame in range(watch_frames + 1):
        values = capture.read_trace_values(pyboy, symbols)
        last_values = values
        if values["wBossAITraceSwitchConfidence"][0] != 0:
            return values, frame
        if values["wEnemySwitchMonIndex"][0] != 0:
            return values, frame
        if values["wBossAITraceChosenMove"][0] != 0:
            return values, frame
        pyboy.tick(1, False, False)
    if last_values is None:
        raise PreferenceDataError("no switch observation read")
    return last_values, watch_frames


def build_switch_report(
    *,
    save_state: Path,
    basis: dict[str, str],
    values: dict[str, list[int]],
    frame: int,
    memory_patches: list[MemoryPatch],
) -> dict[str, Any]:
    param = int(values["wEnemySwitchMonParam"][0])
    switch_index = int(values["wEnemySwitchMonIndex"][0])
    switch_confidence = int(values["wBossAITraceSwitchConfidence"][0])
    chosen_move = int(values["wBossAITraceChosenMove"][0])
    observed_switch_path = switch_confidence != 0 or param != 0 or switch_index != 0
    observed_decision = observed_switch_path or chosen_move != 0
    return {
        "source": "trace_rom_pyboy_switch",
        "save_state": trace_runtime.display_path(save_state),
        "trace_basis": basis,
        "frame": frame,
        "switch_confidence": switch_confidence,
        "switch_param": param,
        "proposed_target_1_based": (param & 0x0F) + 1 if param else 0,
        "switch_index": switch_index,
        "actual_switch": switch_index != 0,
        "proposed_switch": param != 0,
        "chosen_move": chosen_move,
        "observed_switch_path": observed_switch_path,
        "observed_decision": observed_decision,
        "observation_status": switch_observation_status(
            switch_confidence=switch_confidence,
            switch_param=param,
            switch_index=switch_index,
            chosen_move=chosen_move,
        ),
        "memory_patches": [
            {
                "symbol_name": item.symbol_name,
                "offset": item.offset,
                "value": item.value,
            }
            for item in memory_patches
        ],
    }


def switch_observation_status(
    *,
    switch_confidence: int,
    switch_param: int,
    switch_index: int,
    chosen_move: int,
) -> str:
    if switch_index != 0:
        return "actual_switch_observed"
    if switch_param != 0:
        return "switch_proposal_observed"
    if switch_confidence != 0:
        return "switch_confidence_observed"
    if chosen_move != 0:
        return "chosen_move_observed_without_switch_proposal"
    return "no_decision_observed"


def validate_switch_materialization_base(values: dict[str, list[int]]) -> None:
    problems: list[str] = []
    stale_checks = (
        ("wBossAITraceSwitchConfidence", "switch confidence is already set"),
        ("wEnemySwitchMonParam", "switch proposal param is already set"),
        ("wEnemySwitchMonIndex", "switch index is already set"),
        ("wBossAITraceChosenMove", "chosen move is already set"),
    )
    for field, message in stale_checks:
        if values[field][0] != 0:
            problems.append(f"{message} ({field}={values[field][0]:02x})")
    if problems:
        raise PreferenceDataError(
            "switch materialization base state is already inside or past "
            "BossAI_SwitchOrTryItem; use a pre-dispatch "
            "switch_materialization_state: "
            + "; ".join(problems)
        )


def switch_verdict_from_report(
    scenario: dict[str, Any],
    report: dict[str, Any],
    *,
    base_route: str = DEFAULT_BASE_ROUTE,
    switch_threshold: int | None = None,
) -> dict[str, Any]:
    scenario_id = str(scenario.get("id", "unnamed"))
    if report.get("observed_decision") is False:
        return {
            "scenario_id": scenario_id,
            "status": "error",
            "family": scenario.get("family", ""),
            "expected_switch": scenario_expects_switch(scenario),
            "reason": "no switch materialization decision observed within watch_frames",
            "rom": report,
            "switch_roll": switch_roll_frequency(
                scenario,
                report,
                base_route=base_route,
                switch_threshold=switch_threshold,
            ),
        }
    expected_switch = scenario_expects_switch(scenario)
    proposed_switch = bool(report.get("proposed_switch", False))
    if expected_switch and proposed_switch:
        rom_policy = switch_policy_result("pass", 0, "ROM proposes a switch")
    elif expected_switch:
        rom_policy = switch_policy_result(
            "best_never_rolled",
            75,
            "ROM switch dispatch does not propose the expected switch",
        )
    elif proposed_switch:
        rom_policy = switch_policy_result(
            "mismatch",
            70,
            "ROM switch dispatch proposes a switch when policy expects staying",
        )
    else:
        rom_policy = switch_policy_result("pass", 0, "ROM does not propose a switch")
    return {
        "scenario_id": scenario_id,
        "status": "pass",
        "family": scenario.get("family", ""),
        "expected_switch": expected_switch,
        "rom_policy": rom_policy,
        "rom": report,
        "switch_roll": switch_roll_frequency(
            scenario,
            report,
            base_route=base_route,
            switch_threshold=switch_threshold,
        ),
    }


def switch_roll_frequency(
    scenario: dict[str, Any],
    report: dict[str, Any],
    *,
    base_route: str = DEFAULT_BASE_ROUTE,
    switch_threshold: int | None = None,
) -> dict[str, Any]:
    confidence = parse_optional_byte(report.get("switch_confidence"), "switch_confidence")
    if report.get("observed_switch_path") is False:
        return {
            "available": False,
            "confidence": confidence,
            "reason": "no_switch_dispatch_observation",
            "observation_status": report.get("observation_status", "no_decision_observed"),
            "proof_status": "no_final_switch_roll_observed",
        }
    threshold_basis = switch_threshold_basis(
        scenario,
        base_route=base_route,
        switch_threshold=switch_threshold,
    )
    possible_thresholds = threshold_basis["possible_effective_thresholds"]
    possible = [
        {
            "effective_threshold": threshold,
            "switch_chance_threshold": boss_ai_switch_roll_threshold(confidence, threshold),
            "switch_probability": boss_ai_switch_roll_threshold(confidence, threshold) / 256,
        }
        for threshold in possible_thresholds
    ]
    chance_values = {item["switch_chance_threshold"] for item in possible}
    assumed_threshold = threshold_basis["assumed_effective_threshold"]
    assumed_chance = boss_ai_switch_roll_threshold(confidence, assumed_threshold)
    return {
        "available": True,
        "confidence": confidence,
        "threshold_source": threshold_basis["threshold_source"],
        "threshold_exact": threshold_basis["threshold_exact"],
        "probability_exact": len(chance_values) == 1,
        "base_threshold": threshold_basis["base_threshold"],
        "assumed_effective_threshold": assumed_threshold,
        "possible_effective_thresholds": possible_thresholds,
        "switch_chance_threshold": assumed_chance,
        "switch_probability": assumed_chance / 256,
        "stay_probability": 1 - (assumed_chance / 256),
        "possible_switch_probabilities": possible,
        "threshold_components": threshold_basis["components"],
        "proof_status": "source_mirrored_final_switch_roll_from_observed_confidence",
    }


def switch_threshold_basis(
    scenario: dict[str, Any],
    *,
    base_route: str,
    switch_threshold: int | None,
) -> dict[str, Any]:
    explicit_threshold = explicit_switch_threshold(scenario, switch_threshold)
    base = source_base_switch_threshold(scenario, base_route=base_route)
    if explicit_threshold is not None:
        return {
            "threshold_source": "explicit_switch_threshold",
            "threshold_exact": True,
            "base_threshold": base["threshold"],
            "assumed_effective_threshold": explicit_threshold,
            "possible_effective_thresholds": [explicit_threshold],
            "components": {
                **base,
                "explicit_threshold": explicit_threshold,
                "loop_penalty": None,
                "sack_bias": None,
                "wincon_bias": None,
            },
        }

    adjustments = switch_threshold_adjustments(scenario)
    if adjustments is not None:
        effective = base["threshold"]
        if adjustments["loop_penalty"]:
            effective += AI_SWITCH_ANTI_LOOP_PENALTY
        if adjustments["sack_bias"]:
            effective += AI_SWITCH_SACK_BIAS
        if adjustments["wincon_bias"]:
            effective += AI_SWITCH_WINCON_BIAS
        return {
            "threshold_source": "source_mirrored_base_plus_explicit_adjustments",
            "threshold_exact": True,
            "base_threshold": base["threshold"],
            "assumed_effective_threshold": effective,
            "possible_effective_thresholds": [effective],
            "components": {
                **base,
                **adjustments,
            },
        }

    possible = sorted(
        {
            base["threshold"],
            base["threshold"] + AI_SWITCH_SACK_BIAS,
            base["threshold"] + AI_SWITCH_WINCON_BIAS,
            base["threshold"] + AI_SWITCH_SACK_BIAS + AI_SWITCH_WINCON_BIAS,
        }
    )
    return {
        "threshold_source": "source_mirrored_base_threshold_with_untraced_bias_range",
        "threshold_exact": False,
        "base_threshold": base["threshold"],
        "assumed_effective_threshold": base["threshold"],
        "possible_effective_thresholds": possible,
        "components": {
            **base,
            "loop_penalty": False,
            "sack_bias": "untraced_possible",
            "wincon_bias": "untraced_possible",
        },
    }


def explicit_switch_threshold(
    scenario: dict[str, Any],
    switch_threshold: int | None,
) -> int | None:
    if switch_threshold is not None:
        return parse_optional_byte(switch_threshold, "switch_threshold")
    for key in ("boss_ai_switch_threshold", "switch_threshold"):
        if key in scenario:
            return parse_optional_byte(scenario[key], key)
    return None


def switch_threshold_adjustments(scenario: dict[str, Any]) -> dict[str, bool] | None:
    raw = scenario.get("switch_threshold_adjustments")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise PreferenceDataError("switch_threshold_adjustments must be an object")
    return {
        "loop_penalty": bool(raw.get("loop_penalty", False)),
        "sack_bias": bool(raw.get("sack_bias", False)),
        "wincon_bias": bool(raw.get("wincon_bias", False)),
    }


def source_base_switch_threshold(
    scenario: dict[str, Any],
    *,
    base_route: str,
) -> dict[str, Any]:
    tier = normalize_tier(scenario.get("tier", "late"))
    if tier == 1:
        threshold = AI_SWITCH_THRESHOLD_EARLY
        tier_name = "early"
    elif tier == 2:
        threshold = AI_SWITCH_THRESHOLD_MID
        tier_name = "mid"
    else:
        threshold = AI_SWITCH_THRESHOLD_LATE
        tier_name = "late"
    trainer_class = normalized_trainer_class(scenario.get("trainer_class"), base_route)
    class_mod = CLASS_SWITCH_THRESHOLD_MODS.get(trainer_class or "", 0)
    threshold = apply_class_threshold_mod(threshold, class_mod)
    return {
        "tier": tier_name,
        "trainer_class": trainer_class,
        "class_threshold_mod": class_mod,
        "threshold": threshold,
    }


def normalized_trainer_class(raw: Any, base_route: str) -> str | None:
    if raw is None:
        raw = BASE_ROUTE_TRAINER_CLASS.get(base_route)
    if raw is None:
        return None
    return str(raw).strip().upper().replace(" ", "_")


def apply_class_threshold_mod(threshold: int, class_mod: int) -> int:
    if class_mod < 0:
        return max(0, threshold + class_mod)
    if class_mod > 0:
        return min(95, threshold + class_mod)
    return threshold


def parse_optional_byte(raw: Any, field: str) -> int:
    if isinstance(raw, bool) or not isinstance(raw, int) or not 0 <= raw <= 255:
        raise PreferenceDataError(f"{field} must be an integer byte")
    return raw


def switch_policy_result(verdict: str, severity: int, reason: str) -> dict[str, Any]:
    return {"verdict": verdict, "severity": severity, "reason": reason}


def scenario_expects_switch(scenario: dict[str, Any]) -> bool:
    expectation = scenario_expectation(scenario)
    best_ids = list_of_strings(expectation.get("best_action_ids"))
    moves = scenario.get("moves", [])
    by_id = {
        str(move.get("id") or f"slot{slot}"): move
        for slot, move in enumerate(moves, start=1)
        if isinstance(move, dict)
    }
    return any(str(by_id.get(action_id, {}).get("kind", "")) == "switch" for action_id in best_ids)


def clear_switch_trace_patches() -> list[MemoryPatch]:
    patches: list[MemoryPatch] = []
    for name, size in capture.TRACE_FIELDS + capture.CONTEXT_FIELDS:
        for offset in range(size):
            patches.append(patch(name, 0, offset))
    return patches


def scenario_condition_tags(scenario: dict[str, Any]) -> set[str]:
    expectation = scenario.get("expectation", {})
    if not isinstance(expectation, dict):
        return set()
    tags = expectation.get("condition_tags", [])
    if isinstance(tags, str):
        return {tags}
    if not isinstance(tags, list):
        return set()
    return {str(tag) for tag in tags}


def list_of_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    raise PreferenceDataError("expected string or list of strings")


def load_manifest_save_entry(manifest_path: Path, route_id: str) -> dict[str, Any]:
    if not manifest_path.exists():
        raise PreferenceDataError(f"missing live capture manifest: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in data.get("captures", []):
        if entry.get("id") == route_id:
            if not entry.get("save_state"):
                raise PreferenceDataError(f"manifest route {route_id!r} has no save_state")
            return entry
    known = ", ".join(str(entry.get("id", "")) for entry in data.get("captures", []))
    raise PreferenceDataError(f"unknown manifest route {route_id!r}; known: {known}")


def validate_manifest_trace_basis(
    manifest_path: Path,
    *,
    rom: Path,
    symbols_path: Path,
) -> None:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_manifest_hash(
        data,
        manifest_key="trace_rom_sha256",
        actual_path=rom,
        label="trace_rom",
    )
    validate_manifest_hash(
        data,
        manifest_key="trace_symbols_sha256",
        actual_path=symbols_path,
        label="trace_symbols",
    )


def validate_manifest_hash(
    data: dict[str, Any],
    *,
    manifest_key: str,
    actual_path: Path,
    label: str,
) -> None:
    expected = data.get(manifest_key)
    if not isinstance(expected, str) or not expected:
        raise PreferenceDataError(
            f"live capture manifest missing {manifest_key}; cannot prove switch state basis"
        )
    if not actual_path.exists():
        raise PreferenceDataError(f"{label} points to a missing file: {actual_path}")
    actual = capture.sha256_file(actual_path)
    if actual.upper() != expected.upper():
        raise PreferenceDataError(
            f"live capture manifest {label} hash mismatch for {actual_path}: "
            f"expected {expected.upper()}, found {actual}; regenerate the switch "
            "materialization state for the current trace ROM/symbols"
        )


def switch_materialization_state_field(manifest_entry: dict[str, Any]) -> str:
    if manifest_entry.get("switch_materialization_state"):
        return "switch_materialization_state"
    return "save_state"


def resolve_manifest_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def skipped_verdict(
    scenario_id: str,
    reason: str,
    *,
    status: str = "skipped",
) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "status": status,
        "agreement": status == "skipped",
        "reason": reason,
    }


def format_rom_switch_materialization(
    report: dict[str, Any],
    *,
    limit: int = 20,
) -> str:
    lines = [
        "Boss AI ROM switch materialization",
        (
            f"scenarios={report['scenario_count']} checked={report['checked_count']} "
            f"skipped={report['skipped_count']} errors={report['error_count']} "
            f"policy_disagreements={report['policy_disagreement_count']}"
        ),
        (
            f"base_route={report['base_route']} "
            f"base_state={report['base_state']} "
            f"base_state_field={report.get('base_state_field', 'save_state')} "
            f"rate={report['materializations_per_minute']:.0f}/min"
        ),
    ]
    review = [
        verdict
        for verdict in report["verdicts"]
        if verdict.get("status") == "error"
        or int(verdict.get("rom_policy", {}).get("severity", 0)) > 0
    ]
    if review:
        lines.append("")
        lines.append(f"Top {limit} review items:")
        for verdict in review[:limit]:
            rom = verdict.get("rom", {})
            policy = verdict.get("rom_policy", {})
            roll = verdict.get("switch_roll", {})
            probability = roll.get("switch_probability")
            if roll.get("available") is False:
                probability_text = f"unavailable:{roll.get('reason', 'unknown')}"
                exact_text = "no-observation"
            else:
                probability_text = (
                    f"{probability:.1%}" if isinstance(probability, float) else "unknown"
                )
                exact_text = "exact" if roll.get("probability_exact") else "range"
            reason_text = ""
            if verdict.get("status") == "error":
                reason_text = f" reason={verdict.get('reason', 'unknown')}"
            lines.append(
                f"  {verdict['scenario_id']}: "
                f"status={verdict.get('status', 'unknown')} "
                f"policy={policy.get('verdict', 'unknown')} "
                f"expected_switch={verdict.get('expected_switch')} "
                f"proposed_switch={rom.get('proposed_switch')} "
                f"confidence={rom.get('switch_confidence')} "
                f"observation={rom.get('observation_status', 'unknown')} "
                f"switch_rate={probability_text}({exact_text})"
                f"{reason_text}"
            )
    lines.append("")
    lines.append("Known limits:")
    for limit_text in report["known_limits"]:
        lines.append(f"  - {limit_text}")
    return "\n".join(lines)


def write_rom_switch_materialization_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


class SimpleTraceArgs:
    def __init__(self, *, rom: Path, symbols: Path) -> None:
        self.rom = rom
        self.symbols = symbols
