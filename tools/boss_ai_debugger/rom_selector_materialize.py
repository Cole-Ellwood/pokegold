from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError
from tools.trace import boss_ai_trace_capture as capture
from tools.trace import runtime as trace_runtime

from .rom_scenarios import load_scenario_batch, normalize_tier, select_move


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_PATH = ROOT / "audit" / "boss_ai_trace" / "live_capture_manifest.json"
DEFAULT_BASE_ROUTE = "clair"
DEFAULT_WATCH_FRAMES = 80
DEFAULT_FAKE_MOVE_IDS = (1, 2, 3, 4)

REQUIRED_SYMBOLS = (
    "BossAI_SelectMove.first_pass",
    "wBossAIMoveChoiceReady",
    "wBossAITier",
    "wEnemyMonMoves",
    "wEnemyAIMoveScores",
    "wBossAITraceChosenMove",
    "wCurEnemyMove",
    "wCurEnemyMoveNum",
)

KNOWN_LIMITS = [
    (
        "This is selector materialization only: it patches generated final score "
        "bytes at BossAI_SelectMove.first_pass after ROM scoring and lookahead."
    ),
    (
        "It proves the generated selector surface against ROM selector code, not "
        "ROM score-model contribution accuracy."
    ),
    (
        "One ROM sample is stochastic when two actions have nonzero probability; "
        "agreement means the chosen action had nonzero Python selector probability."
    ),
]


@dataclass
class SelectorPatchContext:
    pyboy: Any
    symbols: dict[str, capture.Symbol]
    scenario: dict[str, Any] | None = None
    python_result: dict[str, Any] | None = None
    patched_count: int = 0

    def set_scenario(self, scenario: dict[str, Any], python_result: dict[str, Any]) -> None:
        self.scenario = scenario
        self.python_result = python_result
        self.patched_count = 0

    def patch_current(self) -> None:
        if self.scenario is None or self.python_result is None:
            return
        self.patched_count += 1
        patch_selector_inputs(
            self.pyboy,
            self.symbols,
            self.scenario,
            self.python_result,
        )


def run_rom_selector_materialization_from_path(
    scenarios_path: Path,
    *,
    limit: int = 20,
    base_route: str = DEFAULT_BASE_ROUTE,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    rom: Path = capture.DEFAULT_ROM,
    symbols_path: Path = capture.DEFAULT_SYMBOLS,
    button: str = "a",
    button_delay: int = 8,
    watch_frames: int = DEFAULT_WATCH_FRAMES,
) -> dict[str, Any]:
    scenarios = load_scenario_batch(scenarios_path)
    if limit > 0:
        scenarios = scenarios[:limit]
    return run_rom_selector_materialization(
        scenarios,
        base_route=base_route,
        manifest_path=manifest_path,
        rom=rom,
        symbols_path=symbols_path,
        button=button,
        button_delay=button_delay,
        watch_frames=watch_frames,
        source=str(scenarios_path),
    )


def run_rom_selector_materialization(
    scenarios: list[dict[str, Any]],
    *,
    base_route: str = DEFAULT_BASE_ROUTE,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    rom: Path = capture.DEFAULT_ROM,
    symbols_path: Path = capture.DEFAULT_SYMBOLS,
    button: str = "a",
    button_delay: int = 8,
    watch_frames: int = DEFAULT_WATCH_FRAMES,
    source: str = "inline",
) -> dict[str, Any]:
    if not scenarios:
        raise PreferenceDataError("no scenarios supplied for ROM selector materialization")
    if watch_frames <= 0:
        raise PreferenceDataError("--watch-frames must be positive")

    manifest_entry = load_manifest_entry(manifest_path, base_route)
    base_state = resolve_manifest_path(manifest_entry["pre_choice_state"])
    if not base_state.exists():
        raise PreferenceDataError(f"missing base pre-choice state: {base_state}")

    symbols = capture.parse_symbols(symbols_path)
    require_selector_symbols(symbols)
    move_names = capture.parse_move_names(capture.MOVE_CONSTANTS)
    basis = capture.build_trace_basis_metadata(
        SimpleTraceArgs(rom=rom, symbols=symbols_path)
    )
    pyboy = trace_runtime.open_pyboy(
        rom,
        "PyBoy is required for ROM selector materialization",
    )
    trace_runtime.disable_realtime(pyboy)
    context = SelectorPatchContext(pyboy=pyboy, symbols=symbols)
    hook_symbol = symbols["BossAI_SelectMove.first_pass"]
    started = time.perf_counter()
    verdicts: list[dict[str, Any]] = []
    try:
        pyboy.hook_register(
            hook_symbol.bank,
            hook_symbol.address,
            selector_first_pass_hook,
            context,
        )
        for scenario in scenarios:
            python_result = select_move(scenario)
            if not python_result["ready"]:
                verdicts.append(skipped_unready_verdict(scenario, python_result))
                continue
            context.set_scenario(scenario, python_result)
            verdicts.append(
                materialize_one_scenario(
                    pyboy,
                    symbols,
                    move_names,
                    base_state=base_state,
                    scenario=scenario,
                    python_result=python_result,
                    context=context,
                    button=button,
                    button_delay=button_delay,
                    watch_frames=watch_frames,
                )
            )
    finally:
        pyboy.stop(save=False)

    elapsed = time.perf_counter() - started
    checked = [verdict for verdict in verdicts if verdict["status"] != "skipped_unready"]
    mismatches = [verdict for verdict in checked if not verdict["agreement"]]
    return {
        "schema_version": 1,
        "source": source,
        "kind": "rom_selector_materialization",
        "base_route": base_route,
        "base_state": trace_runtime.display_path(base_state),
        "scenario_count": len(scenarios),
        "checked_count": len(checked),
        "skipped_count": len(verdicts) - len(checked),
        "mismatch_count": len(mismatches),
        "agreement_count": len(checked) - len(mismatches),
        "agreement_rate": ratio(len(checked) - len(mismatches), len(checked)),
        "elapsed_seconds": elapsed,
        "materializations_per_minute": len(checked) / elapsed * 60 if elapsed else 0.0,
        "trace_basis": basis,
        "known_limits": KNOWN_LIMITS,
        "verdicts": verdicts,
    }


def materialize_one_scenario(
    pyboy: Any,
    symbols: dict[str, capture.Symbol],
    move_names: dict[int, str],
    *,
    base_state: Path,
    scenario: dict[str, Any],
    python_result: dict[str, Any],
    context: SelectorPatchContext,
    button: str,
    button_delay: int,
    watch_frames: int,
) -> dict[str, Any]:
    with base_state.open("rb") as fh:
        pyboy.load_state(fh)
    clear_selector_outputs(pyboy, symbols)
    if button:
        pyboy.button(button, delay=button_delay)

    values = None
    frame = 0
    for frame in range(watch_frames + 1):
        current = capture.read_trace_values(pyboy, symbols)
        if current["wBossAITraceChosenMove"][0] != 0:
            values = current
            break
        pyboy.tick(1, False, False)

    if values is None:
        return timeout_verdict(scenario, python_result, context, watch_frames)
    return selector_verdict_from_values(
        scenario,
        python_result,
        values,
        move_names,
        patched_count=context.patched_count,
        frame=frame,
    )


def selector_verdict_from_values(
    scenario: dict[str, Any],
    python_result: dict[str, Any],
    values: dict[str, list[int]],
    move_names: dict[int, str],
    *,
    patched_count: int,
    frame: int,
) -> dict[str, Any]:
    chosen_slot = int(values["wCurEnemyMoveNum"][0])
    chosen_move_id = int(values["wBossAITraceChosenMove"][0])
    action_id = action_id_for_slot(python_result, chosen_slot)
    probability = float(python_result["probabilities"].get(action_id or "", 0.0))
    agreement = action_id is not None and probability > 0.0
    expected_scores = expected_score_bytes(python_result)
    observed_scores = values["wEnemyAIMoveScores"]
    score_bytes_match = observed_scores[: len(expected_scores)] == expected_scores
    if not score_bytes_match:
        agreement = False

    return {
        "scenario_id": python_result["scenario_id"],
        "status": "pass" if agreement else "mismatch",
        "agreement": agreement,
        "frame": frame,
        "patched_count": patched_count,
        "python": {
            "ready": python_result["ready"],
            "tier": python_result["tier"],
            "best_action_id": python_result["best_action_id"],
            "second_action_id": python_result["second_action_id"],
            "probabilities": python_result["probabilities"],
            "final_scores": expected_scores,
        },
        "rom": {
            "chosen_slot_index": chosen_slot,
            "chosen_action_id": action_id,
            "chosen_action_probability": probability,
            "chosen_move_id": chosen_move_id,
            "chosen_move_name": move_names.get(chosen_move_id, f"#{chosen_move_id:02x}"),
            "move_ids": values["wEnemyMonMoves"],
            "move_scores": observed_scores,
            "tier": values["wBossAITier"][0],
        },
        "reason": selector_verdict_reason(
            action_id=action_id,
            probability=probability,
            score_bytes_match=score_bytes_match,
        ),
        "known_limits": KNOWN_LIMITS,
    }


def skipped_unready_verdict(
    scenario: dict[str, Any],
    python_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "scenario_id": str(scenario.get("id", "unnamed")),
        "status": "skipped_unready",
        "agreement": True,
        "python": {
            "ready": False,
            "probabilities": python_result.get("probabilities", {}),
        },
        "rom": {},
        "reason": "Python selector model has no selectable action; skipped materialization.",
        "known_limits": KNOWN_LIMITS,
    }


def timeout_verdict(
    scenario: dict[str, Any],
    python_result: dict[str, Any],
    context: SelectorPatchContext,
    watch_frames: int,
) -> dict[str, Any]:
    return {
        "scenario_id": str(scenario.get("id", "unnamed")),
        "status": "timeout",
        "agreement": False,
        "patched_count": context.patched_count,
        "python": {
            "ready": python_result["ready"],
            "best_action_id": python_result["best_action_id"],
            "second_action_id": python_result["second_action_id"],
            "probabilities": python_result["probabilities"],
        },
        "rom": {},
        "reason": f"no ROM selector choice observed within {watch_frames} frames",
        "known_limits": KNOWN_LIMITS,
    }


def selector_verdict_reason(
    *,
    action_id: str | None,
    probability: float,
    score_bytes_match: bool,
) -> str:
    if not score_bytes_match:
        return "patched ROM score bytes did not match Python final scores"
    if action_id is None:
        return "ROM chose a slot that is outside the generated scenario action list"
    if probability <= 0.0:
        return "ROM chose an action with zero Python selector probability"
    return "ROM chose an action with nonzero Python selector probability"


def patch_selector_inputs(
    pyboy: Any,
    symbols: dict[str, capture.Symbol],
    scenario: dict[str, Any],
    python_result: dict[str, Any],
) -> None:
    write_named_byte(pyboy, symbols, "wBossAITier", normalize_tier(scenario.get("tier", "late")))
    fake_move_ids = fake_move_ids_for_scenario(scenario)
    for offset, move_id in enumerate(fake_move_ids):
        write_named_byte(pyboy, symbols, "wEnemyMonMoves", move_id, offset)
    scores = expected_score_bytes(python_result)
    for offset in range(4):
        score = scores[offset] if offset < len(scores) else 80
        write_named_byte(pyboy, symbols, "wEnemyAIMoveScores", score, offset)


def clear_selector_outputs(
    pyboy: Any,
    symbols: dict[str, capture.Symbol],
) -> None:
    for name in (
        "wBossAITraceChosenMove",
        "wBossAIMoveChoiceReady",
        "wCurEnemyMove",
        "wCurEnemyMoveNum",
    ):
        write_named_byte(pyboy, symbols, name, 0)


def fake_move_ids_for_scenario(scenario: dict[str, Any]) -> list[int]:
    moves = scenario.get("moves", [])
    ids = []
    for index in range(4):
        if index < len(moves):
            raw = moves[index].get("move_id", DEFAULT_FAKE_MOVE_IDS[index])
            ids.append(validate_move_id(raw, index))
        else:
            ids.append(0)
    return ids


def validate_move_id(raw: Any, index: int) -> int:
    if isinstance(raw, str):
        raw = int(raw, 0)
    if not isinstance(raw, int):
        raise PreferenceDataError(f"move_id for slot {index + 1} must be an integer")
    if not 0 <= raw <= 0xFF:
        raise PreferenceDataError(f"move_id for slot {index + 1} is out of byte range")
    if raw == 0:
        raise PreferenceDataError(f"move_id for active slot {index + 1} cannot be 0")
    return raw


def expected_score_bytes(python_result: dict[str, Any]) -> list[int]:
    return [int(move["final_score"]) for move in python_result["moves"][:4]]


def action_id_for_slot(
    python_result: dict[str, Any],
    slot_index: int,
) -> str | None:
    for move in python_result["moves"]:
        if int(move["slot"]) - 1 == slot_index:
            return str(move["action_id"])
    return None


def load_manifest_entry(manifest_path: Path, route_id: str) -> dict[str, Any]:
    if not manifest_path.exists():
        raise PreferenceDataError(f"missing live capture manifest: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in data.get("captures", []):
        if entry.get("id") == route_id:
            if not entry.get("pre_choice_state"):
                raise PreferenceDataError(f"manifest route {route_id!r} has no pre_choice_state")
            return entry
    known = ", ".join(str(entry.get("id", "")) for entry in data.get("captures", []))
    raise PreferenceDataError(f"unknown manifest route {route_id!r}; known: {known}")


def resolve_manifest_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def require_selector_symbols(symbols: dict[str, capture.Symbol]) -> None:
    missing = [name for name in REQUIRED_SYMBOLS if name not in symbols]
    if missing:
        raise PreferenceDataError(
            "missing required selector materialization symbols: "
            + ", ".join(missing)
        )


def write_named_byte(
    pyboy: Any,
    symbols: dict[str, capture.Symbol],
    name: str,
    value: int,
    offset: int = 0,
) -> None:
    symbol = symbols[name]
    write_byte(pyboy, capture.Symbol(symbol.bank, symbol.address + offset), value)


def write_byte(pyboy: Any, symbol: capture.Symbol, value: int) -> None:
    value &= 0xFF
    if 0xD000 <= symbol.address <= 0xDFFF and symbol.bank:
        try:
            pyboy.memory[symbol.bank, symbol.address] = value
            return
        except Exception:
            old_bank = int(pyboy.memory[0xFF70])
            pyboy.memory[0xFF70] = symbol.bank
            try:
                pyboy.memory[symbol.address] = value
            finally:
                pyboy.memory[0xFF70] = old_bank
            return
    pyboy.memory[symbol.address] = value


def selector_first_pass_hook(context: SelectorPatchContext) -> None:
    context.patch_current()


def format_rom_selector_materialization(report: dict[str, Any], *, limit: int = 20) -> str:
    lines = [
        "Boss AI ROM selector materialization",
        (
            f"scenarios={report['scenario_count']} checked={report['checked_count']} "
            f"mismatches={report['mismatch_count']} "
            f"agreement={report['agreement_rate']:.4%}"
        ),
        (
            f"base_route={report['base_route']} "
            f"base_state={report['base_state']} "
            f"rate={report['materializations_per_minute']:.0f}/min"
        ),
    ]
    mismatches = [
        verdict for verdict in report["verdicts"] if not verdict.get("agreement", False)
    ]
    if mismatches:
        lines.append("")
        lines.append(f"Top {limit} mismatches:")
        for verdict in mismatches[:limit]:
            lines.append(
                f"  {verdict['status']} {verdict['scenario_id']}: {verdict['reason']}"
            )
    lines.append("")
    lines.append("Known limits:")
    for gap in report["known_limits"]:
        lines.append(f"  - {gap}")
    return "\n".join(lines)


def write_rom_selector_materialization_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


@dataclass(frozen=True)
class SimpleTraceArgs:
    rom: Path
    symbols: Path
