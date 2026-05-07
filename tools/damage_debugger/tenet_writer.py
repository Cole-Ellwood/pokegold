"""Tenet-style trace export for damage-debugger traces.

Tenet's public trace format is a line-oriented delta syntax:
``reg=0x...,mw=0xADDR:BYTES,pc=0x...``.  The damage debugger wraps that
syntax in JSONL so the trace is still queryable with jq/Python without an
IDA/Tenet viewer or a custom SM83 architecture file.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

from .emulator import DebugSession
from .safe_call import call_function_safe
from .tracer import TraceFrame, Tracer


SCHEMA = "damage-debugger.tenet-jsonl.v1"

REGISTER_FIELDS: tuple[tuple[str, str, int], ...] = (
    ("A", "a", 1),
    ("F", "f", 1),
    ("B", "b", 1),
    ("C", "c", 1),
    ("D", "d", 1),
    ("E", "e", 1),
    ("HL", "hl", 2),
    ("SP", "sp", 2),
)


@dataclass(frozen=True)
class WatchSpec:
    name: str
    bank: int
    addr: int
    size: int


@dataclass(frozen=True)
class WriteResult:
    records: int
    events: int
    memory_events: int


def _banked_pc(frame: TraceFrame) -> int:
    return (int(frame.bank) << 16) | int(frame.pc)


def _hex_value(value: int, width: int) -> str:
    return f"0x{value:0{width * 2}x}"


def _hex_bytes(values: Sequence[int]) -> str:
    return "".join(f"{int(v) & 0xFF:02x}" for v in values)


def _frame_registers(frame: TraceFrame) -> dict[str, int]:
    regs = {json_name: int(getattr(frame, attr)) for attr, json_name, _width in REGISTER_FIELDS}
    regs["pc"] = _banked_pc(frame)
    return regs


def watch_specs_from_tracer(tracer: Tracer) -> list[WatchSpec]:
    return [
        WatchSpec(name=name, bank=int(bank), addr=int(addr), size=int(size))
        for name, bank, addr, size in tracer.watch_list
    ]


def validate_frames(frames: Sequence[TraceFrame], watches: Sequence[WatchSpec]) -> None:
    if not frames:
        raise ValueError("cannot export an empty trace")
    for spec in watches:
        if spec.size <= 0:
            raise ValueError(f"watch {spec.name!r} has invalid size {spec.size}")
    for frame in frames:
        for spec in watches:
            if spec.name not in frame.watches:
                raise ValueError(f"frame {frame.seq} missing watch {spec.name!r}")
            got = frame.watches[spec.name]
            if len(got) != spec.size:
                raise ValueError(
                    f"frame {frame.seq} watch {spec.name!r} has {len(got)} bytes, "
                    f"expected {spec.size}"
                )


def iter_records(
    frames: Sequence[TraceFrame],
    watches: Sequence[WatchSpec],
) -> Iterator[dict[str, Any]]:
    """Yield JSONL records containing Tenet delta syntax plus structured events."""
    validate_frames(frames, watches)
    previous: TraceFrame | None = None
    for frame in frames:
        events: list[dict[str, Any]] = []
        tenet_parts: list[str] = []
        regs = _frame_registers(frame)
        previous_regs = _frame_registers(previous) if previous is not None else {}

        for _attr, name, width in REGISTER_FIELDS:
            value = regs[name]
            if previous is None or previous_regs.get(name) != value:
                encoded = _hex_value(value, width)
                tenet_parts.append(f"{name}={encoded}")
                events.append({
                    "kind": "reg",
                    "target": name,
                    "value": encoded,
                    "width": width,
                })

        if previous is not None:
            for spec in watches:
                old_values = previous.watches[spec.name]
                new_values = frame.watches[spec.name]
                if old_values == new_values:
                    continue
                encoded = _hex_bytes(new_values)
                old_encoded = _hex_bytes(old_values)
                changed_offsets = [
                    idx for idx, (old, new) in enumerate(zip(old_values, new_values))
                    if old != new
                ]
                tenet_parts.append(f"mw=0x{spec.addr:04x}:{encoded}")
                events.append({
                    "kind": "mem",
                    "access": "mw",
                    "target": spec.name,
                    "addr": f"0x{spec.addr:04x}",
                    "bank": spec.bank,
                    "size": spec.size,
                    "bytes": encoded,
                    "old_bytes": old_encoded,
                    "changed_offsets": changed_offsets,
                })

        pc_encoded = _hex_value(regs["pc"], 3)
        tenet_parts.append(f"pc={pc_encoded}")
        events.append({
            "kind": "reg",
            "target": "pc",
            "value": pc_encoded,
            "width": 3,
        })

        yield {
            "schema": SCHEMA,
            "seq": int(frame.seq),
            "bank": int(frame.bank),
            "gb_pc": f"0x{int(frame.pc):04x}",
            "pc": pc_encoded,
            "pc_label": frame.pc_label,
            "mnemonic": frame.mnemonic,
            "cycles": int(frame.cycles),
            "tenet": ",".join(tenet_parts),
            "events": events,
        }
        previous = frame


def write_jsonl(
    frames: Sequence[TraceFrame],
    watches: Sequence[WatchSpec],
    path: Path,
) -> WriteResult:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = 0
    events = 0
    memory_events = 0
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for record in iter_records(frames, watches):
            records += 1
            events += len(record["events"])
            memory_events += sum(1 for event in record["events"] if event.get("kind") == "mem")
            fh.write(json.dumps(record, separators=(",", ":")))
            fh.write("\n")
    return WriteResult(records=records, events=events, memory_events=memory_events)


def write_tenet_text(
    frames: Sequence[TraceFrame],
    watches: Sequence[WatchSpec],
    path: Path,
) -> WriteResult:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = 0
    events = 0
    memory_events = 0
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for record in iter_records(frames, watches):
            records += 1
            events += len(record["events"])
            memory_events += sum(1 for event in record["events"] if event.get("kind") == "mem")
            fh.write(record["tenet"])
            fh.write("\n")
    return WriteResult(records=records, events=events, memory_events=memory_events)


def matching_events(path: Path, target: str) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
            if record.get("schema") != SCHEMA:
                raise ValueError(f"{path}:{line_no}: unexpected schema {record.get('schema')!r}")
            for event in record.get("events", []):
                if event.get("target") == target:
                    event = dict(event)
                    event["seq"] = record.get("seq")
                    event["pc"] = record.get("pc")
                    event["pc_label"] = record.get("pc_label")
                    matches.append(event)
    return matches


def _find_scenario(name: str) -> Any:
    from .clobber_smoke import SCENARIOS

    for scenario in SCENARIOS:
        if scenario.name == name:
            return scenario
    names = ", ".join(sc.name for sc in SCENARIOS)
    raise ValueError(f"unknown scenario {name!r}; known scenarios: {names}")


def _default_output(target: str, scenario: str | None) -> Path:
    safe_target = target.replace(".", "_")
    prefix = scenario or "boot"
    return (
        Path(__file__).resolve().parents[2]
        / "audit"
        / "damage_debugger"
        / f"{prefix}_{safe_target}_tenet.jsonl"
    )


def capture_boot_trace(target: str, max_frames: int) -> tuple[list[TraceFrame], list[WatchSpec]]:
    with DebugSession.open("pokegold_debug") as sess:
        tracer = Tracer.for_function(sess, target)
        tracer.max_frames = max_frames
        if not tracer.instructions:
            raise RuntimeError(f"walker returned 0 instructions for {target}")
        tracer.install()
        try:
            sess.tick(120)
        finally:
            tracer.uninstall()
        return list(tracer.frames), watch_specs_from_tracer(tracer)


def capture_scenario_trace(
    scenario_name: str,
    target: str,
    max_frames: int,
) -> tuple[list[TraceFrame], list[WatchSpec]]:
    scenario = _find_scenario(scenario_name)
    from .clobber_smoke import parse_sym

    with DebugSession.open("pokegold_debug") as sess:
        sess.tick(240)
        syms = parse_sym(sess.sym_path)
        tracer = Tracer.for_function(sess, target)
        tracer.max_frames = max_frames
        if not tracer.instructions:
            raise RuntimeError(f"walker returned 0 instructions for {target}")
        tracer.install()
        try:
            scenario.seed(sess.pyboy, syms)
            for function_name in scenario.chain:
                ticks, returned, post_pc = call_function_safe(
                    sess.pyboy,
                    syms,
                    function_name,
                    budget=scenario.call_budget,
                )
                if not returned and not scenario.allow_nonreturn:
                    raise RuntimeError(
                        f"{function_name} did not reach the HRAM sentinel "
                        f"within {ticks} ticks; post_pc=${post_pc:04x}"
                    )
        finally:
            tracer.uninstall()
        return list(tracer.frames), watch_specs_from_tracer(tracer)


def _make_frame(
    seq: int,
    pc: int,
    *,
    a: int,
    damage: tuple[int, int],
) -> TraceFrame:
    return TraceFrame(
        seq=seq,
        bank=1,
        pc=pc,
        pc_label=f"Fixture+0x{pc - 0x4000:x}",
        mnemonic="nop",
        A=a,
        F=0,
        B=0,
        C=0,
        D=0,
        E=0,
        HL=0xC0AF,
        SP=0xDFFE,
        Z=0,
        N=0,
        H=0,
        Cf=0,
        cycles=seq * 4,
        watches={"wCurDamage": [damage[0], damage[1]]},
    )


def self_test() -> int:
    watches = [WatchSpec("wCurDamage", bank=1, addr=0xC0AF, size=2)]
    frames = [
        _make_frame(0, 0x4000, a=1, damage=(0, 4)),
        _make_frame(1, 0x4001, a=2, damage=(0, 4)),
        _make_frame(2, 0x4002, a=2, damage=(0, 6)),
    ]
    records = list(iter_records(frames, watches))
    assert len(records) == 3
    assert records[0]["schema"] == SCHEMA
    assert records[0]["tenet"].endswith("pc=0x014000")
    assert not [event for event in records[0]["events"] if event.get("target") == "wCurDamage"]
    assert any(event["target"] == "a" and event["value"] == "0x02" for event in records[1]["events"])

    damage_events = [
        event
        for record in records
        for event in record["events"]
        if event.get("target") == "wCurDamage"
    ]
    assert len(damage_events) == 1
    assert damage_events[0]["kind"] == "mem"
    assert damage_events[0]["access"] == "mw"
    assert damage_events[0]["bytes"] == "0006"
    assert damage_events[0]["old_bytes"] == "0004"
    assert damage_events[0]["changed_offsets"] == [1]
    assert "mw=0xc0af:0006" in records[2]["tenet"]

    try:
        list(iter_records([], watches))
    except ValueError as exc:
        assert "empty trace" in str(exc)
    else:  # pragma: no cover - assertion path
        raise AssertionError("empty trace was accepted")

    bad_watch = [WatchSpec("wCurDamage", bank=1, addr=0xC0AF, size=3)]
    try:
        list(iter_records(frames, bad_watch))
    except ValueError as exc:
        assert "expected 3" in str(exc)
    else:  # pragma: no cover - assertion path
        raise AssertionError("bad watch size was accepted")

    with tempfile.TemporaryDirectory() as tmp:
        jsonl_path = Path(tmp) / "fixture.jsonl"
        text_path = Path(tmp) / "fixture.tenet"
        json_result = write_jsonl(frames, watches, jsonl_path)
        text_result = write_tenet_text(frames, watches, text_path)
        assert json_result.records == 3
        assert json_result.memory_events == 1
        assert text_result.records == 3
        assert text_path.read_text(encoding="utf-8").splitlines()[2].endswith("pc=0x014002")
        queried = matching_events(jsonl_path, "wCurDamage")
        assert len(queried) == 1
        assert queried[0]["pc_label"] == "Fixture+0x2"

    print("tenet_writer self-test: PASS")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run synthetic schema/writer checks")
    parser.add_argument("--list-scenarios", action="store_true", help="list scenario names usable with --scenario")
    parser.add_argument("--scenario", help="run a clobber_smoke scenario and trace --target during its chain")
    parser.add_argument("--target", default=None, help="function symbol to trace (default: VBlank or BattleCommand_Stab)")
    parser.add_argument("--max-frames", type=int, default=50_000, help="maximum hook frames to capture")
    parser.add_argument("--output", type=Path, help="JSONL output path")
    parser.add_argument("--text-output", type=Path, help="optional raw Tenet-delta text output path")
    parser.add_argument("--print-target", default="wCurDamage", help="print count for matching event target")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.list_scenarios:
        from .clobber_smoke import SCENARIOS

        for scenario in SCENARIOS:
            print(scenario.name)
        return 0
    if args.max_frames <= 0:
        print("--max-frames must be positive", file=sys.stderr)
        return 2

    target = args.target or ("BattleCommand_Stab" if args.scenario else "VBlank")
    output = args.output or _default_output(target, args.scenario)
    try:
        if args.scenario:
            frames, watches = capture_scenario_trace(args.scenario, target, args.max_frames)
        else:
            frames, watches = capture_boot_trace(target, args.max_frames)
        if not frames:
            print(f"FAIL: captured 0 frames for {target}", file=sys.stderr)
            return 1
        result = write_jsonl(frames, watches, output)
        if args.text_output is not None:
            write_tenet_text(frames, watches, args.text_output)
        matching = matching_events(output, args.print_target)
    except (KeyError, RuntimeError, ValueError, FileNotFoundError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    print(
        f"wrote {result.records} records / {result.memory_events} memory events "
        f"to {output}"
    )
    if args.text_output is not None:
        print(f"wrote raw Tenet delta text to {args.text_output}")
    print(f"{args.print_target}: {len(matching)} matching event(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
