"""Snapshot-ring replay for damage-debugger scenarios.

PyBoy does not expose hardware watchpoints or reverse execution. This tool
keeps a bounded ring of save-states while a function runs, stops when a
watched symbol changes, reloads the pre-change snapshot, and replays the
same tick window to prove the transition is reproducible.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from .clobber_smoke import SCENARIOS, parse_sym
from .paths import find_rom, find_sym
from .safe_call import SENTINEL_ADDR


@dataclass(frozen=True)
class WatchSpec:
    name: str
    bank: int
    addr: int
    size: int


@dataclass(frozen=True)
class Snapshot:
    seq: int
    function: str
    ticks: int
    pc: int
    watch_bytes: tuple[int, ...]
    state: bytes


@dataclass
class SnapshotRing:
    capacity: int

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("snapshot ring capacity must be positive")
        self._items: deque[Snapshot] = deque(maxlen=self.capacity)

    def push(self, snapshot: Snapshot) -> None:
        self._items.append(snapshot)

    def __len__(self) -> int:
        return len(self._items)

    def seqs(self) -> list[int]:
        return [snapshot.seq for snapshot in self._items]

    def latest(self) -> Snapshot:
        if not self._items:
            raise ValueError("snapshot ring is empty")
        return self._items[-1]


@dataclass(frozen=True)
class WatchHit:
    watch: str
    function: str
    before_seq: int
    after_seq: int
    before_pc: int
    after_pc: int
    old_bytes: tuple[int, ...]
    new_bytes: tuple[int, ...]
    tick_step: int
    ring_depth: int
    replay_verified: bool

    @property
    def old_hex(self) -> str:
        return _hex_bytes(self.old_bytes)

    @property
    def new_hex(self) -> str:
        return _hex_bytes(self.new_bytes)


def _hex_bytes(values: Sequence[int]) -> str:
    return "".join(f"{value & 0xFF:02x}" for value in values)


def _save_state(pyboy) -> bytes:
    buf = io.BytesIO()
    pyboy.save_state(buf)
    return buf.getvalue()


def _load_state(pyboy, data: bytes) -> None:
    pyboy.load_state(io.BytesIO(data))


def _read_watch(pyboy, spec: WatchSpec) -> tuple[int, ...]:
    out: list[int] = []
    if 0xD000 <= spec.addr <= 0xDFFF and spec.bank:
        old_svbk = int(pyboy.memory[0xFF70])
        pyboy.memory[0xFF70] = spec.bank
        try:
            for offset in range(spec.size):
                out.append(int(pyboy.memory[spec.addr + offset]))
        finally:
            pyboy.memory[0xFF70] = old_svbk
    else:
        for offset in range(spec.size):
            out.append(int(pyboy.memory[spec.addr + offset]))
    return tuple(out)


def _watch_from_symbol(syms: dict, name: str, size: int | None) -> WatchSpec:
    if name not in syms:
        raise KeyError(name)
    bank, addr = syms[name]
    if size is None:
        size = 2 if name == "wCurDamage" else 1
    if size <= 0:
        raise ValueError("watch size must be positive")
    return WatchSpec(name=name, bank=bank, addr=addr, size=size)


def _set_call_target(pyboy, syms: dict, name: str) -> None:
    bank, addr = syms[name]
    rf = pyboy.register_file

    pyboy.memory[SENTINEL_ADDR] = 0x18
    pyboy.memory[SENTINEL_ADDR + 1] = 0xFE

    sp = int(rf.SP)
    new_sp = (sp - 2) & 0xFFFF
    pyboy.memory[new_sp] = SENTINEL_ADDR & 0xFF
    pyboy.memory[new_sp + 1] = (SENTINEL_ADDR >> 8) & 0xFF
    rf.SP = new_sp
    rf.PC = addr

    rom_bank_sym = syms.get("hROMBank")
    if rom_bank_sym:
        pyboy.memory[rom_bank_sym[1]] = bank
    pyboy.memory[0x2000] = bank


def _capture_snapshot(
    pyboy,
    *,
    seq: int,
    function: str,
    ticks: int,
    watch: WatchSpec,
) -> Snapshot:
    return Snapshot(
        seq=seq,
        function=function,
        ticks=ticks,
        pc=int(pyboy.register_file.PC),
        watch_bytes=_read_watch(pyboy, watch),
        state=_save_state(pyboy),
    )


def _verify_replay(pyboy, before: Snapshot, after: Snapshot, step_ticks: int) -> bool:
    _load_state(pyboy, before.state)
    pyboy.tick(step_ticks, False, False)
    return int(pyboy.register_file.PC) == after.pc


def call_until_watch_change(
    pyboy,
    syms: dict,
    function: str,
    watch: WatchSpec,
    *,
    ring: SnapshotRing,
    seq_start: int,
    budget: int = 4800,
    step_ticks: int = 2,
) -> tuple[WatchHit | None, int, bool, int]:
    """Call one function and stop at the first watched-value change."""
    _set_call_target(pyboy, syms, function)
    ticked = 0
    seq = seq_start
    while ticked < budget:
        before = _capture_snapshot(
            pyboy,
            seq=seq,
            function=function,
            ticks=ticked,
            watch=watch,
        )
        ring.push(before)
        pyboy.tick(step_ticks, False, False)
        ticked += step_ticks
        seq += 1

        after = _capture_snapshot(
            pyboy,
            seq=seq,
            function=function,
            ticks=ticked,
            watch=watch,
        )
        if after.watch_bytes != before.watch_bytes:
            replay_pc_ok = _verify_replay(pyboy, before, after, step_ticks)
            replay_watch_ok = _read_watch(pyboy, watch) == after.watch_bytes
            return (
                WatchHit(
                    watch=watch.name,
                    function=function,
                    before_seq=before.seq,
                    after_seq=after.seq,
                    before_pc=before.pc,
                    after_pc=after.pc,
                    old_bytes=before.watch_bytes,
                    new_bytes=after.watch_bytes,
                    tick_step=step_ticks,
                    ring_depth=len(ring),
                    replay_verified=replay_pc_ok and replay_watch_ok,
                ),
                seq,
                False,
                after.pc,
            )

        pc = int(pyboy.register_file.PC)
        if pc == SENTINEL_ADDR or pc == SENTINEL_ADDR + 2:
            return None, seq, True, pc
    return None, seq, False, int(pyboy.register_file.PC)


def _find_scenario(name: str):
    for scenario in SCENARIOS:
        if scenario.name == name:
            return scenario
    known = ", ".join(sc.name for sc in SCENARIOS)
    raise ValueError(f"unknown scenario {name!r}; known scenarios: {known}")


def replay_scenario(
    scenario_name: str,
    watch_name: str,
    *,
    size: int | None = None,
    capacity: int = 64,
    step_ticks: int = 2,
) -> tuple[WatchHit | None, list[str]]:
    scenario = _find_scenario(scenario_name)
    rom = find_rom("pokegold_debug")
    sym = find_sym("pokegold_debug")
    syms = parse_sym(sym)
    watch = _watch_from_symbol(syms, watch_name, size)
    ring = SnapshotRing(capacity)

    from .boot_cache import BootStateCache

    cache = BootStateCache(rom)
    cache.prime()
    failures: list[str] = []
    seq = 0
    try:
        pyboy = cache.restore()
        scenario.seed(pyboy, syms)
        for function in scenario.chain:
            hit, seq, returned, post_pc = call_until_watch_change(
                pyboy,
                syms,
                function,
                watch,
                ring=ring,
                seq_start=seq,
                budget=scenario.call_budget,
                step_ticks=step_ticks,
            )
            if hit is not None:
                return hit, failures
            if not returned and not scenario.allow_nonreturn:
                failures.append(
                    f"{function} did not reach sentinel within {scenario.call_budget} "
                    f"ticks (PC=${post_pc:04x})"
                )
                break
    finally:
        cache.stop()
    return None, failures


def hit_to_dict(hit: WatchHit) -> dict:
    data = asdict(hit)
    data["old_hex"] = hit.old_hex
    data["new_hex"] = hit.new_hex
    return data


def self_test() -> int:
    ring = SnapshotRing(2)
    ring.push(Snapshot(0, "A", 0, 0x100, (0,), b"a"))
    ring.push(Snapshot(1, "A", 2, 0x101, (1,), b"b"))
    ring.push(Snapshot(2, "A", 4, 0x102, (2,), b"c"))
    assert len(ring) == 2
    assert ring.seqs() == [1, 2]
    assert ring.latest().watch_bytes == (2,)
    try:
        SnapshotRing(0)
    except ValueError as exc:
        assert "capacity" in str(exc)
    else:  # pragma: no cover - assertion path
        raise AssertionError("zero-capacity ring was accepted")
    print("replay self-test: PASS")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run pure snapshot-ring checks")
    parser.add_argument("--scenario", default="physical_no_items", help="clobber_smoke scenario to run")
    parser.add_argument("--watch", default="wCurDamage", help="symbol to watch")
    parser.add_argument("--size", type=int, default=None, help="watch size in bytes")
    parser.add_argument("--capacity", type=int, default=64, help="snapshot ring capacity")
    parser.add_argument("--step-ticks", type=int, default=2, help="tick window per replay step")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.step_ticks <= 0:
        print("--step-ticks must be positive", file=sys.stderr)
        return 2
    if args.capacity <= 0:
        print("--capacity must be positive", file=sys.stderr)
        return 2

    try:
        hit, failures = replay_scenario(
            args.scenario,
            args.watch,
            size=args.size,
            capacity=args.capacity,
            step_ticks=args.step_ticks,
        )
    except (KeyError, ValueError, FileNotFoundError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({
            "scenario": args.scenario,
            "watch": args.watch,
            "hit": hit_to_dict(hit) if hit is not None else None,
            "failures": failures,
        }, indent=2))
    elif hit is not None:
        print(
            f"{args.watch} changed in {hit.function}: "
            f"{hit.old_hex} -> {hit.new_hex}"
        )
        print(
            f"  before seq={hit.before_seq} PC=${hit.before_pc:04x}; "
            f"after seq={hit.after_seq} PC=${hit.after_pc:04x}; "
            f"ring_depth={hit.ring_depth}; replay_verified={hit.replay_verified}"
        )
    else:
        print(f"{args.watch} did not change in scenario {args.scenario!r}")
        for failure in failures:
            print(f"  {failure}")

    if failures:
        return 1
    if hit is None:
        return 1
    return 0 if hit.replay_verified else 1


if __name__ == "__main__":
    sys.exit(main())
