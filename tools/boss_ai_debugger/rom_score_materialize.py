from __future__ import annotations

import io
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError
from tools.trace import boss_ai_trace_capture as capture
from tools.trace import runtime as trace_runtime

from .contribution_compare import compare_contribution_reports
from .contribution_compare import python_contribution_report_from_scenarios
from .rom_contribution_trace import apply_memory_patches
from .rom_contribution_trace import clear_chosen_move
from .rom_contribution_trace import drive_replay_to_choice
from .rom_contribution_trace import memory_patches_to_json
from .rom_contribution_trace import MemoryPatch
from .rom_contribution_trace import reset_boss_ai_turn_caches
from .rom_contribution_trace import RomContributionTraceSession
from .rom_contribution_trace import SimpleTraceArgs
from .rom_scenarios import normalize_tier
from .rom_scenarios import scenario_expectation
from .rom_scenarios import select_from_score_bytes
from .rom_scenarios import select_move
from .rom_selector_materialize import (
    DEFAULT_MANIFEST_PATH,
    load_manifest_entry,
    resolve_manifest_path,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE_ROUTE = "koga"
DEFAULT_WATCH_FRAMES = 90
PUBLIC_POLICY_FAMILIES = (
    "setup_heal",
    "prediction_mix",
    "support_handoff",
    "cashout_board_delta",
)
SUPPORTED_FAMILIES = ("spikes_spin", "score_rule_probe", *PUBLIC_POLICY_FAMILIES)

MOVE_FALLBACK_IDS = {
    "move_absorber_coverage": 0x59,
    "move_all_in_read": 0x55,
    "move_cashout_attack": 0xBC,
    "move_counter_handoff": 0xE2,
    "move_counter_switch": 0xE2,
    "move_cover_reset": 0x2E,
    "move_generic_chip": 0xBC,
    "move_generic_damage": 0xBC,
    "move_generic_status": 0x5C,
    "move_handoff": 0xE2,
    "move_handoff_converter": 0xE2,
    "move_low_risk_prediction": 0x59,
    "move_more_setup": 0xAE,
    "move_neutral_hit": 0x22,
    "move_obvious_stab": 0xBC,
    "move_passive_reset": 0x69,
    "move_receiver_coverage": 0x59,
    "move_reckless_prediction": 0xBC,
    "move_recover": 0x69,
    "move_recover_loop": 0x69,
    "move_recover_route": 0x69,
    "move_repeat_setup": 0xAE,
    "move_repeat_support": 0x5C,
    "move_roar_loop": 0x2E,
    "move_safe_active_ko": 0x59,
    "move_safe_default": 0xBC,
    "move_safe_handoff": 0xE2,
    "move_safe_setup": 0xAE,
    "move_spikes_reset": 0xBF,
    "move_status": 0x5C,
    "move_status_script": 0x5C,
    "move_switch": 0xE2,
    "move_switch_away": 0xE2,
    "move_switch_out": 0xE2,
    "move_weak_attack": 0x22,
    "move_spikes": 0xBF,
    "move_sludge_bomb": 0xBC,
    "move_surf": 0x39,
    "move_explosion": 0x99,
    "move_boom_now": 0x99,
    "move_earthquake_active": 0x59,
    "move_earthquake_branch_cover": 0x59,
    "move_explosion_board_delta": 0x99,
    "move_explosion_read": 0x99,
    "move_low_value_guard": 0xE2,
    "move_preserve_handoff": 0xE2,
    "move_preserve_piece": 0xE2,
    "move_reversible_branch_cover": 0x59,
    "move_setup_greed": 0xAE,
    "move_soft_status": 0x5C,
    "move_status_back": 0x5C,
    "move_valuable_damage": 0xBC,
}

SPECIES = {
    "PIKACHU": 0x19,
    "TENTACRUEL": 0x49,
    "MUK": 0x59,
    "GENGAR": 0x5E,
    "STARMIE": 0x79,
    "QWILFISH": 0xD3,
}

TYPES = {
    "NORMAL": 0x00,
    "POISON": 0x03,
    "GROUND": 0x04,
    "GHOST": 0x08,
    "STEEL": 0x09,
    "WATER": 0x14,
    "GRASS": 0x16,
    "ELECTRIC": 0x17,
    "PSYCHIC": 0x18,
}

MOVES = {
    "RAPID_SPIN": 0xE5,
}

ITEMS = {
    "NO_ITEM": 0x00,
}

SUBSTATUS_IDENTIFIED_MASK = 1 << 3

KNOWN_LIMITS = [
    (
        "Score materialization patches concrete WRAM bytes into a real trace-ROM "
        "pre-choice state before BossAI_ApplyMoveModel scores the first move."
    ),
    (
        "Generated Spikes/Rapid Spin scenarios are exact score-mirror checks; "
        "broad public-policy families also materialize observed ROM score bytes "
        "and policy verdicts, but their synthetic Python deltas are review aids."
    ),
    (
        "Switch/sack cases need switch-dispatch materialization. They are not "
        "treated as proved by move-score replay."
    ),
    (
        "ROM score traces and Python scenario contribution traces are compared "
        "under matching generated scenario ids; mismatches are review items, not "
        "evidence that the ROM trace failed to run."
    ),
    (
        "Fast score-only mode skips rule-level contribution hooks for throughput. "
        "Contribution-trace mode is diagnostic and should be checked against the "
        "fast score path before treating hook-heavy score bytes as behavior."
    ),
]


@dataclass(frozen=True)
class ScenarioMaterialization:
    scenario_id: str
    patches: list[MemoryPatch]
    move_ids: list[int]
    layers: int


@dataclass(frozen=True)
class ReplayControls:
    base_state: Path
    base_state_field: str
    button: str
    button_delay: int
    watch_frames: int
    button_presses: int
    button_interval_frames: int


class RomScoreReplaySession:
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
        self.move_names = capture.parse_move_names(capture.MOVE_CONSTANTS)
        pyboy_class = trace_runtime.load_pyboy(
            "PyBoy is required for ROM score materialization"
        )
        self.pyboy = pyboy_class(str(rom), window="null", sound=False, log_level="ERROR")
        trace_runtime.disable_realtime(self.pyboy)
        score_move = self.symbols.get("BossAI_ApplyMoveModel.ScoreMove")
        if score_move is None:
            raise PreferenceDataError(
                "missing hook symbol: BossAI_ApplyMoveModel.ScoreMove"
        )
        self.memory_patches: list[MemoryPatch] = []
        self.score_start_patches_applied = False
        self.score_start_patch_count = 0
        self.selector_entry_scores: list[int] = []
        self.state_cache: dict[Path, bytes] = {}
        self.pyboy.hook_register(
            score_move.bank,
            score_move.address,
            fast_score_patch_callback,
            self,
        )
        selector_start = self.symbols.get("BossAI_SelectMove")
        if selector_start is None:
            raise PreferenceDataError("missing hook symbol: BossAI_SelectMove")
        self.pyboy.hook_register(
            selector_start.bank,
            selector_start.address,
            fast_selector_start_callback,
            self,
        )
        self.basis = capture.build_trace_basis_metadata(
            SimpleTraceArgs(rom=rom, symbols=symbols_path)
        )

    def __enter__(self) -> "RomScoreReplaySession":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def close(self) -> None:
        self.pyboy.stop(save=False)

    def run(
        self,
        *,
        save_state: Path,
        button: str = "a",
        button_delay: int = 8,
        watch_frames: int = DEFAULT_WATCH_FRAMES,
        button_presses: int = 1,
        button_interval_frames: int = 0,
        metadata: dict[str, str] | None = None,
        memory_patches: list[MemoryPatch] | None = None,
    ) -> dict[str, Any]:
        if not save_state.exists():
            raise PreferenceDataError(f"missing save-state: {save_state}")

        patches = memory_patches or []
        self.memory_patches = patches
        self.score_start_patches_applied = False
        self.score_start_patch_count = 0
        self.selector_entry_scores = []
        self.load_state(save_state)
        apply_memory_patches(self.pyboy, self.symbols, patches)
        reset_boss_ai_turn_caches(self.pyboy, self.symbols)
        clear_chosen_move(self.pyboy, self.symbols)
        final_values, _presses_issued = drive_replay_to_choice(
            self.pyboy,
            self.symbols,
            button=button,
            button_delay=button_delay,
            button_presses=button_presses,
            button_interval_frames=button_interval_frames,
            watch_frames=watch_frames,
        )
        if final_values is None:
            raise PreferenceDataError(
                f"no boss move choice observed within {watch_frames} frames"
            )

        basis = dict(self.basis)
        if metadata:
            basis.update(metadata)
        return build_fast_score_report(
            save_state=save_state,
            basis=basis,
            values=final_values,
            move_names=self.move_names,
            memory_patches=patches,
            score_start_patch_count=self.score_start_patch_count,
            selector_entry_scores=self.selector_entry_scores,
        )

    def apply_score_start_patches(self) -> None:
        if self.score_start_patches_applied:
            return
        apply_memory_patches(self.pyboy, self.symbols, self.memory_patches)
        reset_boss_ai_turn_caches(self.pyboy, self.symbols)
        self.score_start_patches_applied = True
        self.score_start_patch_count += 1

    def record_selector_entry_scores(self) -> None:
        symbol = self.symbols["wEnemyAIMoveScores"]
        self.selector_entry_scores = [
            int(trace_runtime.read_byte(
                self.pyboy,
                capture.Symbol(symbol.bank, symbol.address + offset),
            ))
            for offset in range(4)
        ]

    def load_state(self, save_state: Path) -> None:
        state_bytes = self.state_cache.get(save_state)
        if state_bytes is None:
            state_bytes = save_state.read_bytes()
            self.state_cache[save_state] = state_bytes
        self.pyboy.load_state(io.BytesIO(state_bytes))


def run_rom_score_materialization_from_path(
    scenarios_path: Path,
    *,
    limit: int = 4,
    base_route: str = DEFAULT_BASE_ROUTE,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    rom: Path = capture.DEFAULT_ROM,
    symbols_path: Path = capture.DEFAULT_SYMBOLS,
    button: str = "a",
    button_delay: int = 8,
    watch_frames: int = DEFAULT_WATCH_FRAMES,
    collect_contribution_traces: bool = True,
    compare_fast_score: bool = False,
    workers: int = 1,
) -> dict[str, Any]:
    from .rom_scenarios import load_scenario_batch

    scenarios = load_scenario_batch(scenarios_path)
    if limit > 0:
        scenarios = scenarios[:limit]
    return run_rom_score_materialization(
        scenarios,
        base_route=base_route,
        manifest_path=manifest_path,
        rom=rom,
        symbols_path=symbols_path,
        button=button,
        button_delay=button_delay,
        watch_frames=watch_frames,
        collect_contribution_traces=collect_contribution_traces,
        compare_fast_score=compare_fast_score,
        workers=workers,
        source=str(scenarios_path),
    )


def replay_controls_from_manifest(
    manifest_entry: dict[str, Any],
    *,
    button: str,
    button_delay: int,
    watch_frames: int,
) -> ReplayControls:
    base_state_field = (
        "score_materialization_state"
        if manifest_entry.get("score_materialization_state")
        else "pre_choice_state"
    )
    base_state = resolve_manifest_path(str(manifest_entry[base_state_field]))
    score_button = str(manifest_entry.get("score_materialization_button", button))
    button_presses = int(manifest_entry.get("score_materialization_button_presses", 1))
    button_interval_frames = int(
        manifest_entry.get("score_materialization_button_interval_frames", 0)
    )
    manifest_watch_frames = int(
        manifest_entry.get("score_materialization_watch_frames", watch_frames)
    )
    min_watch_frames = (
        button_interval_frames * max(0, button_presses - 1) + 1
        if button_presses
        else 1
    )
    effective_watch_frames = max(watch_frames, manifest_watch_frames, min_watch_frames)
    return ReplayControls(
        base_state=base_state,
        base_state_field=base_state_field,
        button=score_button,
        button_delay=button_delay,
        watch_frames=effective_watch_frames,
        button_presses=button_presses,
        button_interval_frames=button_interval_frames,
    )


def validate_score_materialization_base(values: dict[str, list[int]]) -> None:
    problems: list[str] = []
    if values["wBossAITraceChosenMove"][0] != 0:
        problems.append("chosen move is already set")
    if any(values["wBossAITraceTopMoves"]):
        problems.append("top-move trace is already populated")
    for field in ("wBossAITracePreModelScores", "wBossAITracePostModelScores"):
        dirty = [value for value in values[field] if value not in (0, 0xFF)]
        if dirty:
            problems.append(f"{field} already contains score bytes {dirty}")
    if problems:
        raise PreferenceDataError(
            "score materialization base state is already inside or past Boss AI "
            "scoring: "
            + "; ".join(problems)
        )


def validate_base_state_file(
    pyboy: Any,
    symbols: dict[str, capture.Symbol],
    base_state: Path,
) -> None:
    with base_state.open("rb") as fh:
        pyboy.load_state(fh)
    validate_score_materialization_base(capture.read_trace_values(pyboy, symbols))


def run_rom_score_materialization(
    scenarios: list[dict[str, Any]],
    *,
    base_route: str = DEFAULT_BASE_ROUTE,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    rom: Path = capture.DEFAULT_ROM,
    symbols_path: Path = capture.DEFAULT_SYMBOLS,
    button: str = "a",
    button_delay: int = 8,
    watch_frames: int = DEFAULT_WATCH_FRAMES,
    collect_contribution_traces: bool = True,
    compare_fast_score: bool = False,
    workers: int = 1,
    source: str = "inline",
) -> dict[str, Any]:
    if not scenarios:
        raise PreferenceDataError("no scenarios supplied for ROM score materialization")
    if watch_frames <= 0:
        raise PreferenceDataError("--watch-frames must be positive")
    if workers < 1:
        raise PreferenceDataError("--workers must be positive")
    if workers > 1:
        if collect_contribution_traces:
            raise PreferenceDataError("--workers is only supported with fast score-only replay")
        return run_parallel_fast_score_materialization(
            scenarios,
            workers=workers,
            base_route=base_route,
            manifest_path=manifest_path,
            rom=rom,
            symbols_path=symbols_path,
            button=button,
            button_delay=button_delay,
            watch_frames=watch_frames,
            source=source,
        )

    manifest_entry = load_manifest_entry(manifest_path, base_route)
    controls = replay_controls_from_manifest(
        manifest_entry,
        button=button,
        button_delay=button_delay,
        watch_frames=watch_frames,
    )
    if not controls.base_state.exists():
        raise PreferenceDataError(
            f"missing {controls.base_state_field}: {controls.base_state}"
        )

    move_names = capture.parse_move_names(capture.MOVE_CONSTANTS)
    move_name_to_id = {normalize_name(name): move_id for move_id, name in move_names.items()}
    started = time.perf_counter()
    verdicts: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    session_class = (
        RomContributionTraceSession
        if collect_contribution_traces
        else RomScoreReplaySession
    )
    with ExitStack() as stack:
        session = stack.enter_context(session_class(rom=rom, symbols_path=symbols_path))
        validate_base_state_file(session.pyboy, session.symbols, controls.base_state)
        fast_session = None
        if collect_contribution_traces and compare_fast_score:
            fast_session = stack.enter_context(
                RomScoreReplaySession(rom=rom, symbols_path=symbols_path)
            )
        for scenario in scenarios:
            scenario_id = str(scenario.get("id", "unnamed"))
            if scenario.get("family") not in SUPPORTED_FAMILIES:
                verdicts.append(
                    skipped_verdict(scenario_id, "unsupported scenario family")
                )
                continue
            unsupported_reason = unsupported_move_score_reason(scenario)
            if unsupported_reason:
                verdicts.append(skipped_verdict(scenario_id, unsupported_reason))
                continue
            try:
                materialization = materialization_for_scenario(
                    scenario,
                    move_name_to_id=move_name_to_id,
                )
                rom_report = session.run(
                    save_state=controls.base_state,
                    button=controls.button,
                    button_delay=controls.button_delay,
                    watch_frames=controls.watch_frames,
                    button_presses=controls.button_presses,
                    button_interval_frames=controls.button_interval_frames,
                    metadata={
                        "boss": base_route,
                        "notes": f"generated-score-materialization:{scenario_id}",
                    },
                    memory_patches=materialization.patches,
                )
                rom_report["trace_id"] = scenario_id
                rom_report["scenario_id"] = scenario_id
                fast_report = None
                if fast_session is not None:
                    fast_report = fast_session.run(
                        save_state=controls.base_state,
                        button=controls.button,
                        button_delay=controls.button_delay,
                        watch_frames=controls.watch_frames,
                        button_presses=controls.button_presses,
                        button_interval_frames=controls.button_interval_frames,
                        metadata={
                            "boss": base_route,
                            "notes": f"fast-score-equivalence:{scenario_id}",
                        },
                        memory_patches=materialization.patches,
                    )
                if collect_contribution_traces:
                    traces.append(rom_report)
                verdicts.append(
                    verdict_from_materialized_trace(
                        scenario,
                        materialization,
                        rom_report,
                        move_names=move_names,
                        compare_contributions=collect_contribution_traces,
                        fast_score_report=fast_report,
                    )
                )
            except Exception as exc:
                verdicts.append(skipped_verdict(scenario_id, str(exc), status="error"))

    elapsed = time.perf_counter() - started
    checked = [verdict for verdict in verdicts if verdict["status"] == "pass"]
    errors = [verdict for verdict in verdicts if verdict["status"] == "error"]
    exact_matches = [
        verdict for verdict in checked if verdict.get("score_bytes_match", False)
    ]
    contribution_matched = [
        verdict
        for verdict in checked
        if verdict.get("contribution_comparison", {}).get("matched_trace_count", 0) > 0
    ]
    contribution_mismatches = [
        verdict
        for verdict in checked
        if verdict.get("contribution_comparison", {}).get("mismatch_count", 0) > 0
    ]
    selector_top_matches = [
        verdict for verdict in checked if verdict.get("selector_top_match", False)
    ]
    hook_equivalence_checked = [
        verdict
        for verdict in checked
        if verdict.get("hook_equivalence", {}).get("checked", False)
    ]
    hook_equivalence_mismatches = [
        verdict
        for verdict in hook_equivalence_checked
        if not verdict.get("hook_equivalence", {}).get("match", False)
    ]

    return {
        "schema_version": 1,
        "source": source,
        "kind": "rom_score_materialization",
        "base_route": base_route,
        "base_state": display_path(controls.base_state),
        "base_state_field": controls.base_state_field,
        "button_presses": controls.button_presses,
        "button_interval_frames": controls.button_interval_frames,
        "effective_watch_frames": controls.watch_frames,
        "scenario_count": len(scenarios),
        "checked_count": len(checked),
        "skipped_count": len(verdicts) - len(checked),
        "error_count": len(errors),
        "score_bytes_match_count": len(exact_matches),
        "selector_top_match_count": len(selector_top_matches),
        "contribution_matched_count": len(contribution_matched),
        "contribution_mismatch_count": len(contribution_mismatches),
        "hook_equivalence_checked_count": len(hook_equivalence_checked),
        "hook_equivalence_mismatch_count": len(hook_equivalence_mismatches),
        "elapsed_seconds": elapsed,
        "materializations_per_minute": len(checked) / elapsed * 60 if elapsed else 0.0,
        "score_replay_mode": (
            "contribution_trace" if collect_contribution_traces else "fast_score_only"
        ),
        "known_limits": KNOWN_LIMITS,
        "verdicts": verdicts,
        "traces": traces,
    }


def run_parallel_fast_score_materialization(
    scenarios: list[dict[str, Any]],
    *,
    workers: int,
    base_route: str,
    manifest_path: Path,
    rom: Path,
    symbols_path: Path,
    button: str,
    button_delay: int,
    watch_frames: int,
    source: str,
) -> dict[str, Any]:
    chunks = chunk_scenarios(scenarios, workers)
    if len(chunks) == 1:
        return run_rom_score_materialization(
            chunks[0],
            base_route=base_route,
            manifest_path=manifest_path,
            rom=rom,
            symbols_path=symbols_path,
            button=button,
            button_delay=button_delay,
            watch_frames=watch_frames,
            collect_contribution_traces=False,
            compare_fast_score=False,
            workers=1,
            source=source,
        )

    started = time.perf_counter()
    worker_args = [
        {
            "scenarios": chunk,
            "base_route": base_route,
            "manifest_path": str(manifest_path),
            "rom": str(rom),
            "symbols_path": str(symbols_path),
            "button": button,
            "button_delay": button_delay,
            "watch_frames": watch_frames,
            "source": f"{source}:worker{index + 1}",
        }
        for index, chunk in enumerate(chunks)
    ]
    with ProcessPoolExecutor(max_workers=len(chunks)) as executor:
        reports = list(executor.map(run_fast_score_worker, worker_args))
    elapsed = time.perf_counter() - started
    return merge_score_materialization_reports(
        reports,
        elapsed_seconds=elapsed,
        source=source,
        workers=len(chunks),
    )


def run_fast_score_worker(args: dict[str, Any]) -> dict[str, Any]:
    return run_rom_score_materialization(
        args["scenarios"],
        base_route=str(args["base_route"]),
        manifest_path=Path(str(args["manifest_path"])),
        rom=Path(str(args["rom"])),
        symbols_path=Path(str(args["symbols_path"])),
        button=str(args["button"]),
        button_delay=int(args["button_delay"]),
        watch_frames=int(args["watch_frames"]),
        collect_contribution_traces=False,
        compare_fast_score=False,
        workers=1,
        source=str(args["source"]),
    )


def chunk_scenarios(
    scenarios: list[dict[str, Any]],
    workers: int,
) -> list[list[dict[str, Any]]]:
    worker_count = min(max(1, workers), len(scenarios))
    chunks: list[list[dict[str, Any]]] = [[] for _ in range(worker_count)]
    for index, scenario in enumerate(scenarios):
        chunks[index % worker_count].append(scenario)
    return [chunk for chunk in chunks if chunk]


def merge_score_materialization_reports(
    reports: list[dict[str, Any]],
    *,
    elapsed_seconds: float,
    source: str,
    workers: int,
) -> dict[str, Any]:
    verdicts = [
        verdict
        for report in reports
        for verdict in report.get("verdicts", [])
    ]
    traces = [
        trace
        for report in reports
        for trace in report.get("traces", [])
    ]
    checked_count = sum(int(report.get("checked_count", 0)) for report in reports)
    known_limits = list(KNOWN_LIMITS)
    known_limits.append(
        f"Parallel fast score-only replay used {workers} worker process(es)."
    )
    return {
        "schema_version": 1,
        "source": source,
        "kind": "rom_score_materialization",
        "base_route": reports[0].get("base_route", "") if reports else "",
        "base_state": reports[0].get("base_state", "") if reports else "",
        "base_state_field": reports[0].get("base_state_field", "") if reports else "",
        "button_presses": reports[0].get("button_presses", 0) if reports else 0,
        "button_interval_frames": (
            reports[0].get("button_interval_frames", 0) if reports else 0
        ),
        "effective_watch_frames": (
            reports[0].get("effective_watch_frames", 0) if reports else 0
        ),
        "scenario_count": sum(int(report.get("scenario_count", 0)) for report in reports),
        "checked_count": checked_count,
        "skipped_count": sum(int(report.get("skipped_count", 0)) for report in reports),
        "error_count": sum(int(report.get("error_count", 0)) for report in reports),
        "score_bytes_match_count": sum(
            int(report.get("score_bytes_match_count", 0)) for report in reports
        ),
        "selector_top_match_count": sum(
            int(report.get("selector_top_match_count", 0)) for report in reports
        ),
        "contribution_matched_count": sum(
            int(report.get("contribution_matched_count", 0)) for report in reports
        ),
        "contribution_mismatch_count": sum(
            int(report.get("contribution_mismatch_count", 0)) for report in reports
        ),
        "hook_equivalence_checked_count": sum(
            int(report.get("hook_equivalence_checked_count", 0)) for report in reports
        ),
        "hook_equivalence_mismatch_count": sum(
            int(report.get("hook_equivalence_mismatch_count", 0)) for report in reports
        ),
        "elapsed_seconds": elapsed_seconds,
        "materializations_per_minute": (
            checked_count / elapsed_seconds * 60 if elapsed_seconds else 0.0
        ),
        "score_replay_mode": "fast_score_only_parallel",
        "worker_count": workers,
        "known_limits": known_limits,
        "verdicts": sorted(verdicts, key=lambda item: str(item.get("scenario_id", ""))),
        "traces": traces,
    }


def materialization_for_scenario(
    scenario: dict[str, Any],
    *,
    move_name_to_id: dict[str, int],
) -> ScenarioMaterialization:
    scenario_id = str(scenario.get("id", "unnamed"))
    family = str(scenario.get("family", ""))
    if family == "score_rule_probe":
        return score_rule_probe_materialization_for_scenario(
            scenario,
            move_name_to_id=move_name_to_id,
        )
    if family in PUBLIC_POLICY_FAMILIES:
        return public_policy_materialization_for_scenario(
            scenario,
            move_name_to_id=move_name_to_id,
        )

    tags = scenario_condition_tags(scenario)
    layers = parse_spikes_layers(tags)
    tier = normalize_tier(scenario.get("tier", "late"))
    active_revealed_spin = "active_revealed_rapid_spin" in tags
    active_ghost = "active_ghost_spinblock" in tags
    foresighted = "foresight_identified_ghost" in tags
    reserve_ghost = "reserve_ghost_available" in tags
    bench_revealed_spin = "bench_revealed_rapid_spin" in tags
    active_species_prior = "active_species_spin_prior" in tags

    move_ids = move_ids_for_scenario(scenario, move_name_to_id=move_name_to_id)
    patches = [
        patch("wBossAITier", tier),
        patch("wBossAITierWeightRow", max(0, tier - 1)),
        patch("wEnemyDisabledMove", 0),
        patch("wEnemyMonItem", ITEMS["NO_ITEM"]),
        patch("wPlayerScreens", layers & 0x03),
        patch("wEnemyScreens", 0),
        patch("wEnemySubStatus1", SUBSTATUS_IDENTIFIED_MASK if foresighted else 0),
        patch("wBattleMonLevel", 50),
        patch("wBattleMonStatus", 0),
        patch("wEnemyMonStatus", 0),
        patch("hBattleTurn", 1),
    ]
    for offset, move_id in enumerate(move_ids):
        patches.append(patch("wEnemyMonMoves", move_id, offset))
        patches.append(patch("wEnemyMonPP", 30, offset))
        patches.append(patch("wEnemyAIMoveScores", 20, offset))
    patches.extend(active_boss_type_patches(active_ghost))
    patches.extend(active_player_patches(active_species_prior))
    patches.extend(active_revealed_move_patches(active_revealed_spin))
    patches.extend(reserve_ghost_patches(reserve_ghost))
    patches.extend(bench_revealed_spin_patches(bench_revealed_spin))
    return ScenarioMaterialization(
        scenario_id=scenario_id,
        patches=patches,
        move_ids=move_ids,
        layers=layers,
    )


def unsupported_move_score_reason(scenario: dict[str, Any]) -> str | None:
    expectation = scenario_expectation(scenario)
    score_required_ids = set(list_of_strings(expectation.get("best_action_ids")))
    score_required_ids.update(list_of_strings(expectation.get("bad_action_ids")))
    score_required_ids.update(list_of_strings(expectation.get("catastrophic_action_ids")))
    if not score_required_ids:
        return None

    moves = scenario.get("moves", [])
    if not isinstance(moves, list):
        return None
    for move in moves:
        if not isinstance(move, dict):
            continue
        action_id = str(move.get("id", ""))
        if action_id in score_required_ids and move.get("kind") == "switch":
            return "labeled switch candidate needs switch materialization"
    return None


def public_policy_materialization_for_scenario(
    scenario: dict[str, Any],
    *,
    move_name_to_id: dict[str, int],
) -> ScenarioMaterialization:
    scenario_id = str(scenario.get("id", "unnamed"))
    tags = scenario_condition_tags(scenario)
    tier = normalize_tier(scenario.get("tier", "late"))
    layers = parse_optional_spikes_layers(tags)
    move_ids = move_ids_for_scenario(scenario, move_name_to_id=move_name_to_id)
    patches = base_public_policy_patches(
        tier=tier,
        layers=layers,
        tags=tags,
        policy_case=str(scenario.get("policy_case", "")),
    )
    for offset, move_id in enumerate(move_ids):
        patches.append(patch("wEnemyMonMoves", move_id, offset))
        patches.append(patch("wEnemyMonPP", 30, offset))
        patches.append(patch("wEnemyAIMoveScores", 20, offset))
    return ScenarioMaterialization(
        scenario_id=scenario_id,
        patches=patches,
        move_ids=move_ids,
        layers=layers,
    )


def score_rule_probe_materialization_for_scenario(
    scenario: dict[str, Any],
    *,
    move_name_to_id: dict[str, int],
) -> ScenarioMaterialization:
    scenario_id = str(scenario.get("id", "unnamed"))
    tags = scenario_condition_tags(scenario)
    tier = normalize_tier(scenario.get("tier", "late"))
    layers = parse_optional_spikes_layers(tags)
    move_ids = move_ids_for_scenario(scenario, move_name_to_id=move_name_to_id)
    patches = base_public_policy_patches(
        tier=tier,
        layers=layers,
        tags=tags,
        policy_case=str(scenario.get("policy_case", "")),
    )
    for offset, move_id in enumerate(move_ids):
        patches.append(patch("wEnemyMonMoves", move_id, offset))
        patches.append(patch("wEnemyMonPP", 30, offset))
        patches.append(patch("wEnemyAIMoveScores", 20, offset))
    patches.extend(extra_materialization_patches(scenario))
    return ScenarioMaterialization(
        scenario_id=scenario_id,
        patches=patches,
        move_ids=move_ids,
        layers=layers,
    )


def extra_materialization_patches(scenario: dict[str, Any]) -> list[MemoryPatch]:
    raw_patches = scenario.get("materialization_patches", [])
    if raw_patches is None:
        return []
    if not isinstance(raw_patches, list):
        raise PreferenceDataError("materialization_patches must be a list")
    patches = []
    for index, raw_patch in enumerate(raw_patches):
        if not isinstance(raw_patch, dict):
            raise PreferenceDataError("materialization_patches entries must be objects")
        symbol_name = str(raw_patch.get("symbol_name") or raw_patch.get("symbol") or "")
        if not symbol_name:
            raise PreferenceDataError(f"materialization_patches[{index}] missing symbol")
        offset = int(raw_patch.get("offset", 0))
        raw_value = raw_patch["value"]
        value = int(raw_value, 0) if isinstance(raw_value, str) else int(raw_value)
        patches.append(patch(symbol_name, value, offset))
    return patches


def base_public_policy_patches(
    *,
    tier: int,
    layers: int,
    tags: set[str],
    policy_case: str,
) -> list[MemoryPatch]:
    enemy_hp = 80
    if policy_case == "resisted_explosion_free_owner":
        enemy_hp = 18
    elif "recovery_preserves_route" in tags:
        enemy_hp = 34
    elif "defensive_sack_owner" in tags:
        enemy_hp = 18
    player_hp = 80
    if policy_case == "resisted_explosion_free_owner":
        player_hp = 22
    elif "active_pressure_converts" in tags:
        player_hp = 22

    player_type1 = TYPES["WATER"]
    player_type2 = TYPES["PSYCHIC"]
    if policy_case == "resisted_explosion_free_owner":
        player_type1 = TYPES["STEEL"]
        player_type2 = TYPES["STEEL"]
    elif "status_absorber_named" in tags:
        player_type1 = TYPES["POISON"]
        player_type2 = TYPES["POISON"]
    elif "worst_case_unguarded" in tags:
        player_type1 = TYPES["STEEL"]
        player_type2 = TYPES["STEEL"]
    elif policy_case == "reversible_before_irreversible":
        player_type1 = TYPES["POISON"]
        player_type2 = TYPES["POISON"]
    elif "prediction_branch_supported" in tags:
        player_type1 = TYPES["ELECTRIC"]
        player_type2 = TYPES["ELECTRIC"]

    patches: list[MemoryPatch] = [
        patch("wBossAITier", tier),
        patch("wBossAITierWeightRow", max(0, tier - 1)),
        patch("wEnemyDisabledMove", 0),
        patch("wEnemyMonItem", ITEMS["NO_ITEM"]),
        patch("wPlayerScreens", layers & 0x03),
        patch("wEnemyScreens", 0),
        patch("wEnemySubStatus1", 0),
        patch("wEnemySubStatus4", 0),
        patch("wPlayerSubStatus1", 0),
        patch("wPlayerSubStatus3", 0),
        patch("wPlayerSubStatus4", 0),
        patch("wPlayerSubStatus5", 0),
        patch("wBattleMonLevel", 50),
        patch("wEnemyMonLevel", 50),
        patch("wBattleMonStatus", 0),
        patch("wEnemyMonStatus", 0),
        patch("wBattleMonSpecies", SPECIES["STARMIE"]),
        patch("wEnemyMonSpecies", SPECIES["QWILFISH"]),
        patch("wBattleMonType1", player_type1),
        patch("wBattleMonType2", player_type2),
        patch("wEnemyMonType1", TYPES["POISON"]),
        patch("wEnemyMonType2", TYPES["WATER"]),
        patch("hBattleTurn", 1),
        patch("wBossAITurnsElapsed", 2 if "support_job_completed" in tags else 1),
        patch("wBossAIPlayerSwitchCount", 1 if "prediction_branch_supported" in tags else 0),
        patch("wBossAIPendingPlayerSwitchCount", 0),
        patch("wBossAIRepeatCount", 0),
        patch("wBossAILastChosenMove", 0),
        patch("wBossAIPlanId", plan_id_for_tags(tags)),
        patch("wBossAIPlanPhase", 1),
        patch("wBossAIPlanConfidence", 70 if tags & {"setup_window", "support_job_completed"} else 50),
        patch("wBossAIWinconMonIdx", 2),
    ]
    patches.extend(word_patches("wEnemyMonHP", enemy_hp))
    patches.extend(word_patches("wEnemyMonMaxHP", 100))
    patches.extend(word_patches("wBattleMonHP", player_hp))
    patches.extend(word_patches("wBattleMonMaxHP", 100))
    patches.extend(stat_level_patches("wEnemyStatLevels", enemy_stat_levels(tags)))
    patches.extend(stat_level_patches("wPlayerStatLevels", player_stat_levels(tags)))
    patches.extend(public_revealed_move_patches(tags, policy_case))
    patches.extend(generic_bench_party_patches())
    patches.extend(public_seen_player_patches(tags))
    return patches


def public_seen_player_patches(tags: set[str]) -> list[MemoryPatch]:
    patches = [
        patch("wBossAISeenPlayerSpeciesCount", 0),
        patch("wBossAISeenPlayerAliveMask", 0),
    ]
    for offset in range(6):
        patches.append(patch("wBossAISeenPlayerSpecies", 0, offset))
    if not ({"revealed_ghost_absorber", "reversible_line_covers_active_and_branch"} & tags):
        return patches
    patches.extend(
        [
            patch("wBossAISeenPlayerSpeciesCount", 2),
            patch("wBossAISeenPlayerSpecies", SPECIES["STARMIE"], 0),
            patch("wBossAISeenPlayerSpecies", SPECIES["GENGAR"], 1),
            patch("wBossAISeenPlayerAliveMask", 0b00000011),
        ]
    )
    return patches


def plan_id_for_tags(tags: set[str]) -> int:
    if "setup_window" in tags or "setup_already_bankrolled" in tags:
        return 3
    if "support_job_completed" in tags or "status_absorber_named" in tags:
        return 2
    if "active_pressure_converts" in tags or "prediction_ev_positive" in tags:
        return 1
    if "recovery_preserves_route" in tags:
        return 4
    return 0


def enemy_stat_levels(tags: set[str]) -> list[int]:
    levels = [7] * 7
    if "setup_already_bankrolled" in tags:
        levels[0] = 10
    return levels


def player_stat_levels(tags: set[str]) -> list[int]:
    levels = [7] * 7
    if "reset_loop_live" in tags or "phaze_loop_live" in tags:
        levels[0] = 9
    return levels


def stat_level_patches(symbol_name: str, levels: list[int]) -> list[MemoryPatch]:
    return [patch(symbol_name, value, offset) for offset, value in enumerate(levels)]


def public_revealed_move_patches(
    tags: set[str],
    policy_case: str,
) -> list[MemoryPatch]:
    moves = [0, 0, 0, 0]
    if "reset_loop_live" in tags:
        moves[0] = 0xE5
    if "named_receiver_branch" in tags or "prediction_branch_supported" in tags:
        moves[1] = 0x69
    if "phaze_loop_live" in tags:
        moves[2] = 0x2E
    if policy_case == "reject_reckless_prediction":
        moves[0] = 0x55
    return [patch("wPlayerUsedMoves", value, offset) for offset, value in enumerate(moves)]


def generic_bench_party_patches() -> list[MemoryPatch]:
    return [
        patch("wOTPartyCount", 2),
        patch("wOTPartySpecies", SPECIES["QWILFISH"], 0),
        patch("wOTPartySpecies", SPECIES["GENGAR"], 1),
        patch("wOTPartySpecies", 0xFF, 2),
        patch("wCurOTMon", 0),
        patch("wOTPartyMon2Species", SPECIES["GENGAR"]),
        patch("wOTPartyMon2Level", 50),
        *word_patches("wOTPartyMon2HP", 80),
        *word_patches("wOTPartyMon2MaxHP", 100),
    ]


def move_ids_for_scenario(
    scenario: dict[str, Any],
    *,
    move_name_to_id: dict[str, int],
) -> list[int]:
    moves = scenario.get("moves")
    if not isinstance(moves, list) or not moves:
        raise PreferenceDataError("scenario must contain moves")
    ids = []
    for index in range(4):
        if index >= len(moves):
            ids.append(0)
            continue
        move = moves[index]
        if not isinstance(move, dict):
            raise PreferenceDataError("scenario moves must be objects")
        raw = move.get("move_id")
        if raw is not None:
            ids.append(validate_byte(raw, f"move_id for slot {index + 1}"))
            continue
        action_id = str(move.get("id", ""))
        if action_id in MOVE_FALLBACK_IDS:
            ids.append(MOVE_FALLBACK_IDS[action_id])
            continue
        name = normalize_name(str(move.get("name", "")))
        try:
            ids.append(move_name_to_id[name])
        except KeyError as exc:
            raise PreferenceDataError(
                f"cannot map generated move {move.get('name')!r} to a ROM move id"
            ) from exc
    return ids


def active_boss_type_patches(active_ghost: bool) -> list[MemoryPatch]:
    if active_ghost:
        return [
            patch("wEnemyMonType1", TYPES["GHOST"]),
            patch("wEnemyMonType2", TYPES["GHOST"]),
        ]
    return [
        patch("wEnemyMonType1", TYPES["POISON"]),
        patch("wEnemyMonType2", TYPES["WATER"]),
    ]


def active_player_patches(active_species_prior: bool) -> list[MemoryPatch]:
    if active_species_prior:
        species = SPECIES["STARMIE"]
        type1 = TYPES["WATER"]
        type2 = TYPES["PSYCHIC"]
    else:
        species = SPECIES["MUK"]
        type1 = TYPES["POISON"]
        type2 = TYPES["POISON"]
    return [
        patch("wBattleMonSpecies", species),
        patch("wBattleMonType1", type1),
        patch("wBattleMonType2", type2),
    ]


def active_revealed_move_patches(active_revealed_spin: bool) -> list[MemoryPatch]:
    moves = [0, 0, 0, 0]
    if active_revealed_spin:
        moves[0] = MOVES["RAPID_SPIN"]
    return [patch("wPlayerUsedMoves", value, offset) for offset, value in enumerate(moves)]


def reserve_ghost_patches(reserve_ghost: bool) -> list[MemoryPatch]:
    if not reserve_ghost:
        return [
            patch("wOTPartyCount", 1),
            patch("wOTPartySpecies", SPECIES["QWILFISH"], 0),
            patch("wOTPartySpecies", 0xFF, 1),
            patch("wCurOTMon", 0),
        ]
    return [
        patch("wOTPartyCount", 2),
        patch("wOTPartySpecies", SPECIES["QWILFISH"], 0),
        patch("wOTPartySpecies", SPECIES["GENGAR"], 1),
        patch("wOTPartySpecies", 0xFF, 2),
        patch("wCurOTMon", 0),
        patch("wOTPartyMon2Species", SPECIES["GENGAR"]),
        patch("wOTPartyMon2Level", 50),
        patch("wOTPartyMon2HP", 0, 0),
        patch("wOTPartyMon2HP", 80, 1),
        patch("wOTPartyMon2MaxHP", 0, 0),
        patch("wOTPartyMon2MaxHP", 100, 1),
    ]


def bench_revealed_spin_patches(bench_revealed_spin: bool) -> list[MemoryPatch]:
    patches = [
        patch("wBossAISeenPlayerSpeciesCount", 0),
        patch("wBossAISeenPlayerAliveMask", 0),
    ]
    for offset in range(6):
        patches.append(patch("wBossAISeenPlayerSpecies", 0, offset))
    for offset in range(24):
        patches.append(patch("wBossAISpeciesUsedMoves", 0, offset))
    if not bench_revealed_spin:
        return patches
    patches.extend(
        [
            patch("wBossAISeenPlayerSpeciesCount", 2),
            patch("wBossAISeenPlayerSpecies", SPECIES["MUK"], 0),
            patch("wBossAISeenPlayerSpecies", SPECIES["TENTACRUEL"], 1),
            patch("wBossAISeenPlayerAliveMask", 0b00000010),
            patch("wBossAISpeciesUsedMoves", MOVES["RAPID_SPIN"], 4),
        ]
    )
    return patches


def verdict_from_materialized_trace(
    scenario: dict[str, Any],
    materialization: ScenarioMaterialization,
    rom_report: dict[str, Any],
    *,
    move_names: dict[int, str],
    compare_contributions: bool = True,
    fast_score_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scenario_id = materialization.scenario_id
    python_result = select_move(scenario)
    rom_selector = select_from_score_bytes(
        scenario_id=scenario_id,
        tier=scenario.get("tier", "late"),
        move_ids=rom_report["move_ids"],
        scores=rom_report["move_scores"],
        move_names=move_names,
    )
    expected_scores = [int(move["final_score"]) for move in python_result["moves"][:4]]
    observed_scores = [int(value) for value in rom_report["move_scores"][: len(expected_scores)]]
    if compare_contributions:
        comparison = compare_contribution_reports(
            rom_reports=[rom_report],
            python_reports=[python_contribution_report_from_scenarios([scenario])],
        )
    else:
        comparison = empty_contribution_comparison()
    rom_best_action_id = action_id_for_slot(scenario, rom_selector.get("best_slot_index"))
    selector_top_match = (
        bool(python_result.get("ready"))
        and rom_best_action_id == python_result.get("best_action_id")
    )
    rom_policy = policy_verdict_from_rom_selector(scenario, rom_selector)
    return {
        "scenario_id": scenario_id,
        "status": "pass",
        "family": scenario.get("family", ""),
        "layers": materialization.layers,
        "score_bytes_match": observed_scores == expected_scores,
        "selector_top_match": selector_top_match,
        "policy_agreement": rom_policy["severity"] == 0,
        "rom_policy": rom_policy,
        "python": {
            "best_action_id": python_result.get("best_action_id"),
            "second_action_id": python_result.get("second_action_id"),
            "final_scores": expected_scores,
        },
        "rom": {
            "best_action_id": rom_best_action_id,
            "best_move_id": rom_selector.get("best_move_id"),
            "best_score": rom_selector.get("best_score"),
            "possible_action_ids": [
                action_id_for_slot(scenario, slot)
                for slot in rom_selector.get("possible_slot_indices", [])
            ],
            "final_scores": observed_scores,
            "selector_entry_scores": rom_report.get("selector_entry_scores", []),
            "post_model_scores": rom_report.get("post_model_scores", []),
            "changed_event_count": rom_report.get("changed_event_count", 0),
            "score_start_patch_count": rom_report.get("score_start_patch_count", 0),
            "rule_entry_count": rom_report.get("rule_entry_count", 0),
            "predicate_branch_entry_count": rom_report.get(
                "predicate_branch_entry_count", 0
            ),
        },
        "contribution_comparison": {
            "matched_trace_count": comparison["matched_trace_count"],
            "mismatch_count": comparison["mismatch_count"],
            "mismatch_class_counts": comparison["mismatch_class_counts"],
        },
        "hook_equivalence": hook_equivalence_summary(
            traced_report=rom_report,
            fast_report=fast_score_report,
        ),
        "patches": [
            {
                "symbol_name": item.symbol_name,
                "offset": item.offset,
                "value": item.value,
            }
            for item in materialization.patches
        ],
    }


def policy_verdict_from_rom_selector(
    scenario: dict[str, Any],
    rom_selector: dict[str, Any],
) -> dict[str, Any]:
    expectation = scenario_expectation(scenario)
    best_ids = list_of_strings(expectation.get("best_action_ids"))
    acceptable_ids = list_of_strings(expectation.get("acceptable_action_ids"))
    bad_ids = list_of_strings(expectation.get("bad_action_ids"))
    catastrophic_ids = list_of_strings(expectation.get("catastrophic_action_ids"))

    probabilities = {
        action_id_for_slot(scenario, slot_index): float(probability)
        for slot_index, probability in rom_selector.get(
            "probabilities_by_slot",
            {},
        ).items()
    }
    probabilities = {
        str(action_id): probability
        for action_id, probability in probabilities.items()
        if action_id is not None
    }
    rom_best = action_id_for_slot(scenario, rom_selector.get("best_slot_index"))
    rom_best_probability = probabilities.get(str(rom_best), 0.0) if rom_best else 0.0
    rolled_bad = rolled_action_ids(probabilities, bad_ids)
    rolled_catastrophic = rolled_action_ids(probabilities, catastrophic_ids)
    zero_probability_best = [
        action_id for action_id in best_ids if probabilities.get(action_id, 0.0) == 0.0
    ]

    if not rom_selector.get("ready"):
        verdict = "no_rom_choice"
        severity = 95
        reason = str(rom_selector.get("reason", "no selectable ROM action"))
    elif rolled_catastrophic:
        verdict = "catastrophic_roll"
        severity = 100
        reason = "ROM score bytes give nonzero probability to catastrophic action(s)"
    elif rolled_bad:
        verdict = "bad_roll"
        severity = 80
        reason = "ROM score bytes give nonzero probability to bad action(s)"
    elif rom_best in best_ids:
        verdict = "pass"
        severity = 0
        reason = "ROM score bytes make an expected-best action top"
    elif rom_best in acceptable_ids:
        verdict = "acceptable_top"
        severity = 30
        reason = "ROM score bytes make an acceptable action top"
    elif best_ids and zero_probability_best == best_ids:
        verdict = "best_never_rolled"
        severity = 75
        reason = "ROM score bytes give every expected-best action zero probability"
    elif best_ids:
        verdict = "mismatch"
        severity = 70
        reason = "ROM score bytes top action is outside expected best/acceptable sets"
    else:
        verdict = "needs_expectation"
        severity = 0
        reason = "scenario has no expected best action ids"

    if verdict in {"pass", "acceptable_top"} and zero_probability_best:
        verdict = "partial_best_unrolled"
        severity = max(severity, 45)
        reason = "ROM score bytes give some expected-best actions zero probability"

    return {
        "verdict": verdict,
        "severity": severity,
        "reason": reason,
        "rom_best_action_id": rom_best,
        "rom_best_probability": rom_best_probability,
        "expected_best_action_ids": best_ids,
        "expected_acceptable_action_ids": acceptable_ids,
        "rolled_bad_action_ids": rolled_bad,
        "rolled_catastrophic_action_ids": rolled_catastrophic,
        "zero_probability_best_action_ids": zero_probability_best,
        "probabilities": probabilities,
    }


def rolled_action_ids(
    probabilities: dict[str, float],
    action_ids: list[str],
) -> list[str]:
    return [
        action_id
        for action_id in action_ids
        if probabilities.get(action_id, 0.0) > 0.0
    ]


def list_of_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    raise PreferenceDataError("expected string or list of strings")


def hook_equivalence_summary(
    *,
    traced_report: dict[str, Any],
    fast_report: dict[str, Any] | None,
) -> dict[str, Any]:
    if fast_report is None:
        return {"checked": False}
    traced_scores = [int(value) for value in traced_report.get("move_scores", [])]
    fast_scores = [int(value) for value in fast_report.get("move_scores", [])]
    traced_chosen = traced_report.get("chosen", {})
    fast_chosen = fast_report.get("chosen", {})
    score_match = traced_scores == fast_scores
    chosen_match = traced_chosen == fast_chosen
    return {
        "checked": True,
        "match": score_match and chosen_match,
        "score_bytes_match": score_match,
        "chosen_match": chosen_match,
        "traced_scores": traced_scores,
        "fast_scores": fast_scores,
        "traced_chosen": traced_chosen,
        "fast_chosen": fast_chosen,
    }


def build_fast_score_report(
    *,
    save_state: Path,
    basis: dict[str, str],
    values: dict[str, list[int]],
    move_names: dict[int, str],
    memory_patches: list[MemoryPatch],
    score_start_patch_count: int = 0,
    selector_entry_scores: list[int] | None = None,
) -> dict[str, Any]:
    chosen_move = values["wBossAITraceChosenMove"][0]
    return {
        "schema_version": 1,
        "source": "trace_rom_pyboy_fast_score",
        "save_state": trace_runtime.display_path(save_state),
        "trace_basis": basis,
        "chosen": {
            "move_id": chosen_move,
            "move_name": move_names.get(chosen_move, f"#{chosen_move:02x}"),
            "slot_index": values["wCurEnemyMoveNum"][0],
        },
        "memory_patches": memory_patches_to_json(memory_patches),
        "move_ids": values["wEnemyMonMoves"],
        "move_scores": values["wEnemyAIMoveScores"],
        "pre_model_scores": values["wBossAITracePreModelScores"],
        "post_model_scores": values["wBossAITracePostModelScores"],
        "selector_entry_scores": selector_entry_scores or [],
        "rule_entry_count": 0,
        "predicate_branch_entry_count": 0,
        "event_count": 0,
        "changed_event_count": 0,
        "score_start_patch_count": score_start_patch_count,
        "events": [],
        "rule_entries": [],
        "predicate_branch_entries": [],
        "known_limits": [
            "Fast score replay records ROM score bytes and selector output without contribution hooks.",
            "Run again with contribution traces enabled to localize rule-level score deltas.",
        ],
    }


def empty_contribution_comparison() -> dict[str, Any]:
    return {
        "matched_trace_count": 0,
        "mismatch_count": 0,
        "mismatch_class_counts": {},
        "mismatches": [],
    }


def fast_score_patch_callback(session: RomScoreReplaySession) -> None:
    session.apply_score_start_patches()


def fast_selector_start_callback(session: RomScoreReplaySession) -> None:
    session.record_selector_entry_scores()


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


def parse_spikes_layers(tags: set[str]) -> int:
    for tag in tags:
        prefix = "spikes_layers_"
        if tag.startswith(prefix):
            layers = int(tag[len(prefix) :], 10)
            if 0 <= layers <= 3:
                return layers
    raise PreferenceDataError("spikes_spin scenario is missing spikes_layers_N tag")


def parse_optional_spikes_layers(tags: set[str]) -> int:
    for tag in tags:
        prefix = "spikes_layers_"
        if not tag.startswith(prefix):
            continue
        layers = int(tag[len(prefix) :], 10)
        if 0 <= layers <= 3:
            return layers
    return 0


def action_id_for_slot(scenario: dict[str, Any], slot_index: Any) -> str | None:
    if slot_index is None:
        return None
    try:
        index = int(slot_index)
    except (TypeError, ValueError):
        return None
    moves = scenario.get("moves", [])
    if not isinstance(moves, list) or not 0 <= index < len(moves):
        return None
    move = moves[index]
    if not isinstance(move, dict):
        return None
    return str(move.get("id") or f"slot{index + 1}")


def patch(symbol_name: str, value: int, offset: int = 0) -> MemoryPatch:
    return MemoryPatch(symbol_name=symbol_name, offset=offset, value=value & 0xFF)


def word_patches(symbol_name: str, value: int) -> list[MemoryPatch]:
    if not 0 <= value <= 0xFFFF:
        raise PreferenceDataError(f"{symbol_name} word patch is out of range")
    return [
        patch(symbol_name, (value >> 8) & 0xFF, 0),
        patch(symbol_name, value & 0xFF, 1),
    ]


def validate_byte(raw: Any, label: str) -> int:
    if isinstance(raw, str):
        raw = int(raw, 0)
    if not isinstance(raw, int):
        raise PreferenceDataError(f"{label} must be an integer")
    if not 0 <= raw <= 0xFF:
        raise PreferenceDataError(f"{label} is out of byte range")
    return raw


def normalize_name(value: str) -> str:
    return value.strip().upper().replace(" ", "_").replace("-", "_")


def format_rom_score_materialization(
    report: dict[str, Any],
    *,
    limit: int = 20,
) -> str:
    lines = [
        "Boss AI ROM score materialization",
        (
            f"scenarios={report['scenario_count']} checked={report['checked_count']} "
            f"skipped={report['skipped_count']} errors={report['error_count']} "
            f"score_matches={report['score_bytes_match_count']} "
            f"contribution_matched={report['contribution_matched_count']} "
            f"hook_mismatches={report.get('hook_equivalence_mismatch_count', 0)}"
        ),
        (
            f"base_route={report['base_route']} "
            f"base_state={report['base_state']} "
            f"presses={report.get('button_presses', 1)} "
            f"interval={report.get('button_interval_frames', 0)} "
            f"mode={report.get('score_replay_mode', 'contribution_trace')} "
            f"rate={report['materializations_per_minute']:.0f}/min"
        ),
    ]
    review = [
        verdict
        for verdict in report["verdicts"]
        if verdict["status"] != "skipped"
        and (
            not verdict.get("score_bytes_match", False)
            or verdict.get("contribution_comparison", {}).get("mismatch_count", 0) > 0
            or int(verdict.get("rom_policy", {}).get("severity", 0)) > 0
        )
    ]
    if review:
        lines.append("")
        lines.append(f"Top {limit} review items:")
        for verdict in review[:limit]:
            comparison = verdict.get("contribution_comparison", {})
            hook_equivalence = verdict.get("hook_equivalence", {})
            rom_policy = verdict.get("rom_policy", {})
            lines.append(
                f"  {verdict['scenario_id']}: "
                f"rom={verdict.get('rom', {}).get('best_action_id')} "
                f"python={verdict.get('python', {}).get('best_action_id')} "
                f"policy={rom_policy.get('verdict', 'unknown')} "
                f"score_match={verdict.get('score_bytes_match', False)} "
                f"contribution_mismatches={comparison.get('mismatch_count', 0)} "
                f"hook_match={hook_equivalence.get('match', 'not_checked')}"
            )
    lines.append("")
    lines.append("Known limits:")
    for limit_text in report["known_limits"]:
        lines.append(f"  - {limit_text}")
    return "\n".join(lines)


def write_rom_score_materialization_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("/", "\\")
    except ValueError:
        return str(path)
