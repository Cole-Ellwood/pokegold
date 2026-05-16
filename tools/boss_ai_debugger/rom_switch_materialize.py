from __future__ import annotations

import io
import json
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError
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

KNOWN_LIMITS = [
    (
        "Switch materialization replays the real BossAI_SwitchOrTryItem path from "
        "the shared switch-loop trace state and observes switch confidence/param."
    ),
    (
        "This proves switch-dispatch proposal behavior, not move score bytes and "
        "not a multi-sample stochastic switch-roll probability."
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
    source: str = "inline",
) -> dict[str, Any]:
    if not scenarios:
        raise PreferenceDataError("no scenarios supplied for ROM switch materialization")
    if watch_frames <= 0:
        raise PreferenceDataError("--watch-frames must be positive")

    manifest_entry = load_manifest_save_entry(manifest_path, base_route)
    base_state = resolve_manifest_path(str(manifest_entry["save_state"]))
    if not base_state.exists():
        raise PreferenceDataError(f"missing switch save-state: {base_state}")

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
                verdicts.append(switch_verdict_from_report(scenario, report))
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
    return {
        "source": "trace_rom_pyboy_switch",
        "save_state": trace_runtime.display_path(save_state),
        "trace_basis": basis,
        "frame": frame,
        "switch_confidence": int(values["wBossAITraceSwitchConfidence"][0]),
        "switch_param": param,
        "proposed_target_1_based": (param & 0x0F) + 1 if param else 0,
        "switch_index": switch_index,
        "actual_switch": switch_index != 0,
        "proposed_switch": param != 0,
        "chosen_move": int(values["wBossAITraceChosenMove"][0]),
        "memory_patches": [
            {
                "symbol_name": item.symbol_name,
                "offset": item.offset,
                "value": item.value,
            }
            for item in memory_patches
        ],
    }


def switch_verdict_from_report(
    scenario: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, Any]:
    scenario_id = str(scenario.get("id", "unnamed"))
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
    }


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
            f"rate={report['materializations_per_minute']:.0f}/min"
        ),
    ]
    review = [
        verdict
        for verdict in report["verdicts"]
        if int(verdict.get("rom_policy", {}).get("severity", 0)) > 0
    ]
    if review:
        lines.append("")
        lines.append(f"Top {limit} review items:")
        for verdict in review[:limit]:
            rom = verdict.get("rom", {})
            policy = verdict.get("rom_policy", {})
            lines.append(
                f"  {verdict['scenario_id']}: "
                f"policy={policy.get('verdict', 'unknown')} "
                f"expected_switch={verdict.get('expected_switch')} "
                f"proposed_switch={rom.get('proposed_switch')} "
                f"confidence={rom.get('switch_confidence')}"
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
