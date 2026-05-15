from __future__ import annotations

import json
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError
from tools.trace import boss_ai_trace_capture as capture
from tools.trace import runtime as trace_runtime

from .rule_map import build_rule_map


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROM_CONTRIBUTION_TRACE_PATH = (
    ROOT / "audit" / "boss_ai_debugger" / "rom_contribution_trace_smoke.json"
)

SCORE_HELPERS = {
    "BossAI_ApplyMoveModel.EncourageScoreByA": "encourage_tier_weight",
    "BossAI_ApplyMoveModel.DiscourageScoreByA": "discourage_tier_weight",
    "BossAI_SetScoreHL": "set_score",
    "BossAI_EncourageScoreHL": "encourage_score",
    "BossAI_DiscourageScoreHL": "discourage_score",
    "BossAI_ApplySignedDeltaToScore": "apply_signed_lookahead_delta",
}

POINTER_FROM_WRAM_SCORE_PTR = {
    "BossAI_SetScoreHL",
    "BossAI_EncourageScoreHL",
    "BossAI_DiscourageScoreHL",
}

CONTROL_HOOKS = {
    "BossAI_ApplyMoveModel.ScoreMove": "candidate_start",
    "BossAI_ApplyMoveModel.TracePostModelScore": "candidate_end",
}


@dataclass(frozen=True)
class HookTarget:
    kind: str
    full_symbol: str
    operation: str
    bank: int
    address: int


@dataclass(frozen=True)
class RuleFrame:
    sp: int
    full_symbol: str
    rule: dict[str, Any]


@dataclass(frozen=True)
class PendingScore:
    helper_symbol: str
    operation: str
    amount: int
    pointer: int
    before: int
    candidate: dict[str, Any]
    source: dict[str, Any]


class SymbolIndex:
    def __init__(
        self,
        symbols: dict[str, capture.Symbol],
        rule_map: dict[str, Any],
    ) -> None:
        self.symbols = symbols
        self.rule_by_full_symbol = build_rule_lookup(rule_map)
        self.symbols_by_bank: dict[int, list[tuple[int, str]]] = {}
        self.rules_by_bank: dict[int, list[tuple[int, str]]] = {}
        for name, symbol in symbols.items():
            self.symbols_by_bank.setdefault(symbol.bank, []).append(
                (symbol.address, name)
            )
        for items in self.symbols_by_bank.values():
            items.sort()
        for name in self.rule_by_full_symbol:
            symbol = symbols.get(name)
            if symbol is None:
                continue
            self.rules_by_bank.setdefault(symbol.bank, []).append(
                (symbol.address, name)
            )
        for items in self.rules_by_bank.values():
            items.sort()

    def hook_targets(self) -> list[HookTarget]:
        targets: list[HookTarget] = []
        names: dict[str, tuple[str, str]] = {}
        for name in self.rule_by_full_symbol:
            names[name] = ("rule", "")
        for name, operation in SCORE_HELPERS.items():
            names[name] = ("score_helper", operation)
        for name, operation in CONTROL_HOOKS.items():
            names[name] = ("control", operation)

        for name, (kind, operation) in names.items():
            symbol = self.symbols.get(name)
            if symbol is None:
                continue
            targets.append(
                HookTarget(
                    kind=kind,
                    full_symbol=name,
                    operation=operation,
                    bank=symbol.bank,
                    address=symbol.address,
                )
            )
        return targets

    def nearest_symbol(self, bank: int, address: int) -> str:
        return nearest_name(self.symbols_by_bank.get(bank, []), address)

    def nearest_rule_symbol(self, bank: int, address: int) -> str:
        return nearest_name(self.rules_by_bank.get(bank, []), address)

    def rule_for(self, full_symbol: str) -> dict[str, Any] | None:
        return self.rule_by_full_symbol.get(full_symbol)


class RomContributionTracer:
    def __init__(
        self,
        pyboy: Any,
        symbols: dict[str, capture.Symbol],
        symbol_index: SymbolIndex,
        move_names: dict[int, str],
    ) -> None:
        self.pyboy = pyboy
        self.symbols = symbols
        self.symbol_index = symbol_index
        self.move_names = move_names
        self.frames: list[RuleFrame] = []
        self.pending: PendingScore | None = None
        self.events: list[dict[str, Any]] = []

    def handle_hook(self, targets: list[HookTarget]) -> None:
        for target in sorted(targets, key=hook_order):
            if target.kind == "rule":
                self.handle_rule(target)
            elif target.kind == "score_helper":
                self.handle_score_helper(target)
            elif target.kind == "control":
                self.handle_control(target)

    def handle_rule(self, target: HookTarget) -> None:
        self.close_pending(trigger=target.full_symbol)
        sp = int(self.pyboy.register_file.SP)
        self.pop_returned_frames(sp)
        rule = self.symbol_index.rule_for(target.full_symbol)
        if rule is None:
            return
        frame = RuleFrame(sp=sp, full_symbol=target.full_symbol, rule=rule)
        if self.frames and self.frames[-1].sp == sp:
            self.frames[-1] = frame
        else:
            self.frames.append(frame)

    def handle_score_helper(self, target: HookTarget) -> None:
        self.close_pending(trigger=target.full_symbol)
        sp = int(self.pyboy.register_file.SP)
        self.pop_returned_frames(sp)
        pointer = self.score_pointer_for_helper(target)
        before = self.read_addr(pointer)
        amount = int(self.pyboy.register_file.A) & 0xFF
        self.pending = PendingScore(
            helper_symbol=target.full_symbol,
            operation=target.operation,
            amount=amount,
            pointer=pointer,
            before=before,
            candidate=self.candidate_for_score_pointer(pointer),
            source=self.source_for_score_helper(target),
        )

    def score_pointer_for_helper(self, target: HookTarget) -> int:
        if target.full_symbol in POINTER_FROM_WRAM_SCORE_PTR:
            symbol = self.symbols["wBossAIScorePtr"]
            high = trace_runtime.read_byte(self.pyboy, symbol)
            low = trace_runtime.read_byte(
                self.pyboy,
                capture.Symbol(symbol.bank, symbol.address + 1),
            )
            return (high << 8) | low
        return int(self.pyboy.register_file.HL)

    def handle_control(self, target: HookTarget) -> None:
        self.close_pending(trigger=target.full_symbol)
        if target.operation == "candidate_start":
            self.frames.clear()

    def close_pending(self, *, trigger: str) -> None:
        pending = self.pending
        if pending is None:
            return
        self.pending = None
        after = self.read_addr(pending.pointer)
        delta = after - pending.before
        self.events.append(
            {
                "index": len(self.events) + 1,
                "event_type": "score_delta",
                "helper_symbol": pending.helper_symbol,
                "operation": pending.operation,
                "amount_register_a": pending.amount,
                "score_pointer": f"{pending.pointer:04x}",
                "score_before": pending.before,
                "score_after": after,
                "delta": delta,
                "changed": delta != 0,
                "candidate": pending.candidate,
                "source": pending.source,
                "closed_by": trigger,
            }
        )

    def pop_returned_frames(self, sp: int) -> None:
        while self.frames and self.frames[-1].sp < sp:
            self.frames.pop()

    def active_frame(self) -> RuleFrame | None:
        if not self.frames:
            return None
        return self.frames[-1]

    def source_for_score_helper(self, target: HookTarget) -> dict[str, Any]:
        frame = self.active_frame()
        return_address = self.stack_return_address()
        callsite_symbol = self.symbol_index.nearest_symbol(
            target.bank,
            return_address,
        )
        callsite_rule_symbol = self.symbol_index.nearest_rule_symbol(
            target.bank,
            return_address,
        )
        callsite_rule = self.symbol_index.rule_for(callsite_rule_symbol)
        rule = frame.rule if frame is not None else callsite_rule
        full_symbol = frame.full_symbol if frame is not None else callsite_rule_symbol
        return {
            "rule_id": rule.get("rule_id", "") if rule else "",
            "source_label": rule.get("source_label", "") if rule else "",
            "full_symbol": full_symbol,
            "classification": rule.get("classification", "") if rule else "",
            "public_reads": rule.get("public_reads", []) if rule else [],
            "callsite_symbol": callsite_symbol,
            "callsite_rule_symbol": callsite_rule_symbol,
            "return_address": f"{return_address:04x}",
            "hook_bank": f"{target.bank:02x}",
        }

    def candidate_for_score_pointer(self, pointer: int) -> dict[str, Any]:
        base = self.symbols["wEnemyAIMoveScores"]
        offset = pointer - base.address
        if 0 <= offset < 4:
            move_symbol = self.symbols["wEnemyMonMoves"]
            move_id = self.read_symbol_offset(move_symbol, offset)
            return {
                "kind": "move",
                "slot_index": offset,
                "slot": offset + 1,
                "move_id": move_id,
                "move_name": self.move_names.get(move_id, f"#{move_id:02x}"),
            }
        return {
            "kind": "unknown_score_pointer",
            "slot_index": -1,
            "slot": 0,
            "move_id": 0,
            "move_name": "",
        }

    def stack_return_address(self) -> int:
        sp = int(self.pyboy.register_file.SP)
        low = int(self.pyboy.memory[sp])
        high = int(self.pyboy.memory[(sp + 1) & 0xFFFF])
        return low | (high << 8)

    def read_symbol_offset(self, symbol: capture.Symbol, offset: int) -> int:
        return int(
            trace_runtime.read_byte(
                self.pyboy,
                capture.Symbol(symbol.bank, symbol.address + offset),
            )
        )

    def read_addr(self, address: int) -> int:
        bank = self.symbols["wEnemyAIMoveScores"].bank if 0xD000 <= address <= 0xDFFF else 0
        return int(trace_runtime.read_byte(self.pyboy, capture.Symbol(bank, address)))


def run_rom_contribution_trace(
    *,
    save_state: Path,
    rom: Path = capture.DEFAULT_ROM,
    symbols_path: Path = capture.DEFAULT_SYMBOLS,
    button: str = "a",
    button_delay: int = 8,
    watch_frames: int = 60,
    metadata: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not save_state.exists():
        raise PreferenceDataError(f"missing save-state: {save_state}")
    symbols = capture.parse_symbols(symbols_path)
    capture.require_symbols(symbols)
    require_hook_symbols(symbols)
    symbol_index = SymbolIndex(symbols, build_rule_map())
    move_names = capture.parse_move_names(capture.MOVE_CONSTANTS)
    PyBoy = trace_runtime.load_pyboy("PyBoy is required for ROM contribution tracing")
    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    trace_runtime.disable_realtime(pyboy)
    tracer = RomContributionTracer(pyboy, symbols, symbol_index, move_names)
    try:
        with save_state.open("rb") as fh:
            pyboy.load_state(fh)
        register_hooks(pyboy, symbol_index.hook_targets(), tracer)
        clear_chosen_move(pyboy, symbols)
        if button:
            pyboy.button(button, delay=button_delay)
        final_values = None
        for _frame in range(watch_frames + 1):
            values = capture.read_trace_values(pyboy, symbols)
            if values["wBossAITraceChosenMove"][0] != 0:
                final_values = values
                break
            pyboy.tick(1, False, False)
        tracer.close_pending(trigger="replay_end")
        if final_values is None:
            raise PreferenceDataError(
                f"no boss move choice observed within {watch_frames} frames"
            )
        basis = capture.build_trace_basis_metadata(
            SimpleTraceArgs(rom=rom, symbols=symbols_path)
        )
        if metadata:
            basis.update(metadata)
        return build_report(
            save_state=save_state,
            basis=basis,
            values=final_values,
            events=tracer.events,
            move_names=move_names,
        )
    finally:
        pyboy.stop(save=False)


def run_rom_contribution_trace_for_route(
    *,
    boss_id: str,
    rom: Path = capture.DEFAULT_ROM,
    symbols_path: Path = capture.DEFAULT_SYMBOLS,
    battery_save: Path | None = None,
    out_dir: Path | None = None,
    input_wait_frames: int = 0,
    max_a_presses: int = 0,
    metadata: dict[str, str] | None = None,
) -> dict[str, Any]:
    from tools.trace import boss_ai_state_factory as factory

    if boss_id not in factory.ROUTES:
        known = ", ".join(sorted(factory.ROUTES))
        raise PreferenceDataError(f"unknown boss route {boss_id!r}; known: {known}")
    route = factory.ROUTES[boss_id]
    battery = battery_save if battery_save is not None else factory.DEFAULT_BATTERY_SAVE
    output = out_dir if out_dir is not None else factory.DEFAULT_OUT_DIR
    args = Namespace(
        rom=rom,
        battery_save=battery,
        out_dir=output,
        input_wait_frames=input_wait_frames,
        max_a_presses=max_a_presses,
        log_every=20,
    )

    symbols = capture.parse_symbols(symbols_path)
    capture.require_symbols(symbols)
    factory.require_symbols(symbols, [route])
    require_hook_symbols(symbols)
    event_constants = factory.parse_simple_consts(factory.EVENT_FLAGS)
    map_constants = factory.parse_map_consts(factory.MAP_CONSTANTS)
    trainer_constants = factory.parse_trainer_consts(factory.TRAINER_CONSTANTS)
    trainer_constant = factory.expected_trainer(route, trainer_constants)

    symbol_index = SymbolIndex(symbols, build_rule_map())
    move_names = capture.parse_move_names(capture.MOVE_CONSTANTS)
    work_rom = factory.prepare_work_rom(args)
    pyboy = factory.open_pyboy(work_rom)
    tracer = RomContributionTracer(pyboy, symbols, symbol_index, move_names)
    log: list[str] = [
        f"ROUTE {route.capture_id}",
        "MODE contribution_trace",
        f"ROM_SOURCE {capture.display_path(rom)}",
        f"ROM_WORK {capture.display_path(work_rom)}",
        f"BATTERY_SAVE {capture.display_path(battery)}",
    ]
    try:
        register_hooks(pyboy, symbol_index.hook_targets(), tracer)
        frame = factory.boot_continue(pyboy, symbols, log)
        frame = factory.setup_route_entry(
            pyboy,
            route,
            symbols,
            event_constants,
            map_constants,
            output,
            log,
            frame,
        )
        values, frame = drive_route_until_choice(
            pyboy,
            route,
            trainer_constant,
            symbols,
            args,
            log,
            frame,
        )
        tracer.close_pending(trigger="route_replay_end")
        basis = capture.build_trace_basis_metadata(
            SimpleTraceArgs(rom=rom, symbols=symbols_path)
        )
        if metadata:
            basis.update(metadata)
        report = build_report(
            save_state=work_rom,
            save_state_label=f"route:{route.capture_id}",
            basis=basis,
            values=values,
            events=tracer.events,
            move_names=move_names,
        )
        report["boss_route"] = route.capture_id
        report["frame"] = frame
        report["work_rom"] = capture.display_path(work_rom)
        return report
    finally:
        pyboy.stop(save=False)


def drive_route_until_choice(
    pyboy: Any,
    route: Any,
    trainer_constant: Any,
    symbols: dict[str, capture.Symbol],
    args: Namespace,
    log: list[str],
    frame: int,
) -> tuple[dict[str, list[int]], int]:
    from tools.trace import boss_ai_state_factory as factory

    input_wait_frames = (
        route.input_wait_frames
        if args.input_wait_frames == 0
        else args.input_wait_frames
    )
    for button_name in route.prime_buttons:
        factory.press(pyboy, button_name, input_wait_frames)
        frame += input_wait_frames
        log.append(factory.watch_line(pyboy, symbols, frame, f"PRIME_{button_name.upper()}"))

    max_presses = args.max_a_presses or route.max_a_presses
    for step in range(max_presses):
        factory.press(pyboy, "a", input_wait_frames)
        frame += input_wait_frames
        values = capture.read_trace_values(pyboy, symbols)
        chosen = values["wBossAITraceChosenMove"][0]
        if step % args.log_every == 0 or chosen:
            log.append(factory.watch_line(pyboy, symbols, frame, f"DRIVE_A_{step + 1:03d}"))
        if not chosen:
            continue
        trainer_class = factory.read_one(pyboy, symbols, "wOtherTrainerClass")
        trainer_id = factory.read_one(pyboy, symbols, "wOtherTrainerID")
        if (
            trainer_class != trainer_constant.class_id
            or trainer_id != trainer_constant.trainer_id
        ):
            raise PreferenceDataError(
                f"{route.capture_id}: got chosen move for trainer "
                f"{trainer_class:02x}:{trainer_id:02x}, expected "
                f"{trainer_constant.class_id:02x}:{trainer_constant.trainer_id:02x}"
            )
        return values, frame

    raise PreferenceDataError(
        f"{route.capture_id}: no chosen move observed within {max_presses} A presses"
    )


def register_hooks(
    pyboy: Any,
    targets: list[HookTarget],
    tracer: RomContributionTracer,
) -> None:
    targets_by_address: dict[tuple[int, int], list[HookTarget]] = {}
    for target in targets:
        targets_by_address.setdefault((target.bank, target.address), []).append(target)
    for (bank, address), grouped in targets_by_address.items():
        pyboy.hook_register(bank, address, hook_callback, (tracer, grouped))


def hook_callback(context: tuple[RomContributionTracer, list[HookTarget]]) -> None:
    tracer, targets = context
    tracer.handle_hook(targets)


def hook_order(target: HookTarget) -> int:
    return {"control": 0, "rule": 1, "score_helper": 2}[target.kind]


def clear_chosen_move(
    pyboy: Any,
    symbols: dict[str, capture.Symbol],
) -> None:
    symbol = symbols["wBossAITraceChosenMove"]
    if 0xD000 <= symbol.address <= 0xDFFF and symbol.bank:
        try:
            pyboy.memory[symbol.bank, symbol.address] = 0
            return
        except Exception:
            pass
    pyboy.memory[symbol.address] = 0


def build_report(
    *,
    save_state: Path,
    save_state_label: str | None = None,
    basis: dict[str, str],
    values: dict[str, list[int]],
    events: list[dict[str, Any]],
    move_names: dict[int, str],
) -> dict[str, Any]:
    changed = [event for event in events if event["changed"]]
    return {
        "schema_version": 1,
        "source": "trace_rom_pyboy_hooks",
        "save_state": save_state_label or trace_runtime.display_path(save_state),
        "trace_basis": basis,
        "chosen": {
            "move_id": values["wBossAITraceChosenMove"][0],
            "move_name": move_names.get(
                values["wBossAITraceChosenMove"][0],
                f"#{values['wBossAITraceChosenMove'][0]:02x}",
            ),
            "slot_index": values["wCurEnemyMoveNum"][0],
        },
        "move_ids": values["wEnemyMonMoves"],
        "move_scores": values["wEnemyAIMoveScores"],
        "pre_model_scores": values["wBossAITracePreModelScores"],
        "post_model_scores": values["wBossAITracePostModelScores"],
        "event_count": len(events),
        "changed_event_count": len(changed),
        "events": events,
        "known_limits": [
            "Trace events are captured by PyBoy execution hooks, not by an in-ROM WRAM ring buffer.",
            "This records score helper deltas and source labels, but not every predicate false path yet.",
            "Public-read evidence is sourced from the rule map hints, not dynamic memory-read slicing yet.",
        ],
    }


def format_rom_contribution_trace(report: dict[str, Any], *, limit: int = 80) -> str:
    chosen = report["chosen"]
    lines = [
        "Boss AI ROM contribution trace",
        (
            f"source={report['source']} save_state={report['save_state']} "
            f"events={report['event_count']} changed={report['changed_event_count']}"
        ),
        (
            f"chosen={chosen['move_name']}#{chosen['move_id']} "
            f"slot={chosen['slot_index']}"
        ),
        (
            "scores: "
            f"pre={csv(report['pre_model_scores'])} "
            f"post={csv(report['post_model_scores'])} "
            f"final={csv(report['move_scores'])}"
        ),
        "",
        f"First {limit} score events:",
    ]
    for event in report["events"][:limit]:
        candidate = event["candidate"]
        source = event["source"]
        change = "*" if event["changed"] else " "
        lines.append(
            f"  {change} {event['index']:03d} "
            f"slot={candidate['slot_index']} {candidate['move_name']} "
            f"{event['operation']} a={event['amount_register_a']} "
            f"{event['score_before']}->{event['score_after']} "
            f"delta={event['delta']:+d}"
        )
        lines.append(
            "      "
            f"{source.get('rule_id') or source.get('full_symbol')} "
            f"callsite={source.get('callsite_symbol', '')}"
        )
    if len(report["events"]) > limit:
        lines.append(f"  ... {len(report['events']) - limit} more")
    lines.append("")
    lines.append("Known limits:")
    for limit_text in report["known_limits"]:
        lines.append(f"  - {limit_text}")
    return "\n".join(lines)


def write_rom_contribution_trace_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_rom_contribution_trace(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PreferenceDataError(f"missing ROM contribution trace: {path}") from exc
    if not isinstance(data, dict):
        raise PreferenceDataError(f"ROM contribution trace is not an object: {path}")
    if data.get("source") != "trace_rom_pyboy_hooks":
        raise PreferenceDataError(f"unsupported ROM contribution trace source: {path}")
    return data


def summarize_rom_contribution_trace(
    report: dict[str, Any],
    *,
    artifact_path: Path | None = None,
) -> dict[str, Any]:
    events = [event for event in report.get("events", []) if isinstance(event, dict)]
    changed_events = [event for event in events if event.get("changed")]
    covered_rule_ids = sorted(rule_ids_from_events(events))
    changed_rule_ids = sorted(rule_ids_from_events(changed_events))
    operation_counts = count_event_values(events, "operation")
    changed_operation_counts = count_event_values(changed_events, "operation")
    classification_counts = count_source_values(events, "classification")
    changed_classification_counts = count_source_values(changed_events, "classification")
    result = {
        "available": True,
        "source": report.get("source", ""),
        "save_state": report.get("save_state", ""),
        "boss_route": report.get("boss_route", ""),
        "artifact": relative_artifact_path(artifact_path) if artifact_path else "",
        "trace_rom_sha256": report.get("trace_basis", {}).get("trace_rom_sha256", ""),
        "trace_symbols_sha256": report.get("trace_basis", {}).get(
            "trace_symbols_sha256",
            "",
        ),
        "event_count": int(report.get("event_count", len(events))),
        "changed_event_count": int(report.get("changed_event_count", len(changed_events))),
        "covered_rule_count": len(covered_rule_ids),
        "changed_rule_count": len(changed_rule_ids),
        "covered_rule_ids": covered_rule_ids,
        "changed_rule_ids": changed_rule_ids,
        "operation_counts": operation_counts,
        "changed_operation_counts": changed_operation_counts,
        "classification_counts": classification_counts,
        "changed_classification_counts": changed_classification_counts,
        "unmapped_event_count": count_unmapped_events(events),
        "changed_unmapped_event_count": count_unmapped_events(changed_events),
        "candidate_count": len(candidate_keys(events)),
        "changed_candidate_count": len(candidate_keys(changed_events)),
        "chosen": report.get("chosen", {}),
        "known_limits": report.get("known_limits", []),
    }
    return result


def summarize_rom_contribution_trace_paths(paths: list[Path]) -> dict[str, Any]:
    loaded = [
        summarize_rom_contribution_trace(
            load_rom_contribution_trace(path),
            artifact_path=path,
        )
        for path in paths
        if path.exists()
    ]
    if not loaded:
        return {
            "available": False,
            "artifact_count": 0,
            "event_count": 0,
            "changed_event_count": 0,
            "covered_rule_count": 0,
            "changed_rule_count": 0,
            "covered_rule_ids": [],
            "changed_rule_ids": [],
            "operation_counts": {},
            "changed_operation_counts": {},
            "classification_counts": {},
            "changed_classification_counts": {},
            "unmapped_event_count": 0,
            "changed_unmapped_event_count": 0,
            "candidate_count": 0,
            "changed_candidate_count": 0,
            "artifacts": [],
        }

    covered_rule_ids = sorted(
        {
            rule_id
            for summary in loaded
            for rule_id in summary["covered_rule_ids"]
        }
    )
    changed_rule_ids = sorted(
        {
            rule_id
            for summary in loaded
            for rule_id in summary["changed_rule_ids"]
        }
    )
    return {
        "available": True,
        "artifact_count": len(loaded),
        "event_count": sum(int(summary["event_count"]) for summary in loaded),
        "changed_event_count": sum(
            int(summary["changed_event_count"]) for summary in loaded
        ),
        "covered_rule_count": len(covered_rule_ids),
        "changed_rule_count": len(changed_rule_ids),
        "covered_rule_ids": covered_rule_ids,
        "changed_rule_ids": changed_rule_ids,
        "operation_counts": merge_counts(
            summary["operation_counts"] for summary in loaded
        ),
        "changed_operation_counts": merge_counts(
            summary["changed_operation_counts"] for summary in loaded
        ),
        "classification_counts": merge_counts(
            summary["classification_counts"] for summary in loaded
        ),
        "changed_classification_counts": merge_counts(
            summary["changed_classification_counts"] for summary in loaded
        ),
        "unmapped_event_count": sum(
            int(summary["unmapped_event_count"]) for summary in loaded
        ),
        "changed_unmapped_event_count": sum(
            int(summary["changed_unmapped_event_count"]) for summary in loaded
        ),
        "candidate_count": sum(int(summary["candidate_count"]) for summary in loaded),
        "changed_candidate_count": sum(
            int(summary["changed_candidate_count"]) for summary in loaded
        ),
        "artifacts": loaded,
    }


def resolve_rom_contribution_trace_paths(paths: list[Path] | None) -> list[Path]:
    if paths is not None:
        return paths
    if DEFAULT_ROM_CONTRIBUTION_TRACE_PATH.exists():
        return [DEFAULT_ROM_CONTRIBUTION_TRACE_PATH]
    return []


def require_hook_symbols(symbols: dict[str, capture.Symbol]) -> None:
    missing = [
        name
        for name in [*SCORE_HELPERS, *CONTROL_HOOKS]
        if name not in symbols
    ]
    if missing:
        raise PreferenceDataError("missing hook symbols: " + ", ".join(missing))


def build_rule_lookup(rule_map: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for rule in rule_map["rules"]:
        full_symbol = full_symbol_for_rule(rule)
        if not full_symbol:
            continue
        out[full_symbol] = rule
    return out


def full_symbol_for_rule(rule: dict[str, Any]) -> str:
    label = str(rule["source_label"])
    if label.startswith("."):
        if not isinstance(rule.get("parent_label"), str):
            return ""
        return f"{rule['parent_label']}{label}"
    return label


def nearest_name(items: list[tuple[int, str]], address: int) -> str:
    name = ""
    for item_address, item_name in items:
        if item_address > address:
            break
        name = item_name
    return name


def csv(values: list[int]) -> str:
    return ",".join(str(value) for value in values)


def rule_ids_from_events(events: list[dict[str, Any]]) -> set[str]:
    rule_ids = set()
    for event in events:
        source = event.get("source", {})
        if not isinstance(source, dict):
            continue
        rule_id = str(source.get("rule_id", ""))
        if rule_id:
            rule_ids.add(rule_id)
    return rule_ids


def candidate_keys(events: list[dict[str, Any]]) -> set[tuple[str, int, int]]:
    keys = set()
    for event in events:
        candidate = event.get("candidate", {})
        if not isinstance(candidate, dict):
            continue
        keys.add(
            (
                str(candidate.get("kind", "")),
                int(candidate.get("slot_index", -1)),
                int(candidate.get("move_id", 0)),
            )
        )
    return keys


def count_event_values(events: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        value = str(event.get(key, ""))
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def count_source_values(events: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        source = event.get("source", {})
        if not isinstance(source, dict):
            continue
        value = str(source.get(key, ""))
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def count_unmapped_events(events: list[dict[str, Any]]) -> int:
    count = 0
    for event in events:
        if not rule_ids_from_events([event]):
            count += 1
    return count


def merge_counts(items: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for key, value in item.items():
            counts[key] = counts.get(key, 0) + int(value)
    return dict(sorted(counts.items()))


def relative_artifact_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.relative_to(ROOT)).replace("/", "\\")
    except ValueError:
        return str(path)


@dataclass(frozen=True)
class SimpleTraceArgs:
    rom: Path
    symbols: Path
