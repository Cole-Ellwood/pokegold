from __future__ import annotations

import json
import time
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
from .rom_contribution_trace import memory_patches_to_json
from .rom_contribution_trace import MemoryPatch
from .rom_contribution_trace import RomContributionTraceSession
from .rom_contribution_trace import SimpleTraceArgs
from .rom_scenarios import normalize_tier
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
SUPPORTED_FAMILIES = ("spikes_spin",)

MOVE_FALLBACK_IDS = {
    "move_spikes": 0xBF,
    "move_sludge_bomb": 0xBC,
    "move_surf": 0x39,
    "move_explosion": 0x99,
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
    "GHOST": 0x08,
    "WATER": 0x14,
    "PSYCHIC": 0x18,
}

MOVES = {
    "RAPID_SPIN": 0xE5,
}

ITEMS = {
    "NO_ITEM": 0x00,
}

SUBSTATUS_IDENTIFIED_MASK = 1 << 5

KNOWN_LIMITS = [
    (
        "Score materialization patches concrete WRAM bytes into a real trace-ROM "
        "pre-choice state before BossAI_ApplyMoveModel scores the first move."
    ),
    (
        "The first supported family is generated Spikes/Rapid Spin coverage, "
        "because it exercises the current public-info hazard-retention patch."
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
        self.pyboy.hook_register(
            score_move.bank,
            score_move.address,
            fast_score_patch_callback,
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
        metadata: dict[str, str] | None = None,
        memory_patches: list[MemoryPatch] | None = None,
    ) -> dict[str, Any]:
        if not save_state.exists():
            raise PreferenceDataError(f"missing save-state: {save_state}")

        patches = memory_patches or []
        self.memory_patches = patches
        self.score_start_patches_applied = False
        self.score_start_patch_count = 0
        with save_state.open("rb") as fh:
            self.pyboy.load_state(fh)
        apply_memory_patches(self.pyboy, self.symbols, patches)
        clear_chosen_move(self.pyboy, self.symbols)
        if button:
            self.pyboy.button(button, delay=button_delay)

        final_values = None
        for _frame in range(watch_frames + 1):
            values = capture.read_trace_values(self.pyboy, self.symbols)
            if values["wBossAITraceChosenMove"][0] != 0:
                final_values = values
                break
            self.pyboy.tick(1, False, False)
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
        )

    def apply_score_start_patches(self) -> None:
        if self.score_start_patches_applied:
            return
        apply_memory_patches(self.pyboy, self.symbols, self.memory_patches)
        self.score_start_patches_applied = True
        self.score_start_patch_count += 1


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
        source=str(scenarios_path),
    )


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
    source: str = "inline",
) -> dict[str, Any]:
    if not scenarios:
        raise PreferenceDataError("no scenarios supplied for ROM score materialization")
    if watch_frames <= 0:
        raise PreferenceDataError("--watch-frames must be positive")

    manifest_entry = load_manifest_entry(manifest_path, base_route)
    base_state = resolve_manifest_path(manifest_entry["pre_choice_state"])
    if not base_state.exists():
        raise PreferenceDataError(f"missing base pre-choice state: {base_state}")

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
    with session_class(rom=rom, symbols_path=symbols_path) as session:
        for scenario in scenarios:
            scenario_id = str(scenario.get("id", "unnamed"))
            if scenario.get("family") not in SUPPORTED_FAMILIES:
                verdicts.append(
                    skipped_verdict(scenario_id, "unsupported scenario family")
                )
                continue
            try:
                materialization = materialization_for_scenario(
                    scenario,
                    move_name_to_id=move_name_to_id,
                )
                rom_report = session.run(
                    save_state=base_state,
                    button=button,
                    button_delay=button_delay,
                    watch_frames=watch_frames,
                    metadata={
                        "boss": base_route,
                        "notes": f"generated-score-materialization:{scenario_id}",
                    },
                    memory_patches=materialization.patches,
                )
                rom_report["trace_id"] = scenario_id
                rom_report["scenario_id"] = scenario_id
                if collect_contribution_traces:
                    traces.append(rom_report)
                verdicts.append(
                    verdict_from_materialized_trace(
                        scenario,
                        materialization,
                        rom_report,
                        move_names=move_names,
                        compare_contributions=collect_contribution_traces,
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

    return {
        "schema_version": 1,
        "source": source,
        "kind": "rom_score_materialization",
        "base_route": base_route,
        "base_state": display_path(base_state),
        "scenario_count": len(scenarios),
        "checked_count": len(checked),
        "skipped_count": len(verdicts) - len(checked),
        "error_count": len(errors),
        "score_bytes_match_count": len(exact_matches),
        "selector_top_match_count": len(selector_top_matches),
        "contribution_matched_count": len(contribution_matched),
        "contribution_mismatch_count": len(contribution_mismatches),
        "elapsed_seconds": elapsed,
        "materializations_per_minute": len(checked) / elapsed * 60 if elapsed else 0.0,
        "score_replay_mode": (
            "contribution_trace" if collect_contribution_traces else "fast_score_only"
        ),
        "known_limits": KNOWN_LIMITS,
        "verdicts": verdicts,
        "traces": traces,
    }


def materialization_for_scenario(
    scenario: dict[str, Any],
    *,
    move_name_to_id: dict[str, int],
) -> ScenarioMaterialization:
    scenario_id = str(scenario.get("id", "unnamed"))
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
    return {
        "scenario_id": scenario_id,
        "status": "pass",
        "family": scenario.get("family", ""),
        "layers": materialization.layers,
        "score_bytes_match": observed_scores == expected_scores,
        "selector_top_match": selector_top_match,
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
        "patches": [
            {
                "symbol_name": item.symbol_name,
                "offset": item.offset,
                "value": item.value,
            }
            for item in materialization.patches
        ],
    }


def build_fast_score_report(
    *,
    save_state: Path,
    basis: dict[str, str],
    values: dict[str, list[int]],
    move_names: dict[int, str],
    memory_patches: list[MemoryPatch],
    score_start_patch_count: int = 0,
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
            f"contribution_matched={report['contribution_matched_count']}"
        ),
        (
            f"base_route={report['base_route']} "
            f"base_state={report['base_state']} "
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
        )
    ]
    if review:
        lines.append("")
        lines.append(f"Top {limit} review items:")
        for verdict in review[:limit]:
            comparison = verdict.get("contribution_comparison", {})
            lines.append(
                f"  {verdict['scenario_id']}: "
                f"rom={verdict.get('rom', {}).get('best_action_id')} "
                f"python={verdict.get('python', {}).get('best_action_id')} "
                f"score_match={verdict.get('score_bytes_match', False)} "
                f"contribution_mismatches={comparison.get('mismatch_count', 0)}"
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
