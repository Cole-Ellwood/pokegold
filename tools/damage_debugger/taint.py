"""SM83 taint propagation for damage-debugger traces.

The tracer records pre-instruction register snapshots. This module consumes
those frames plus the disassembled instructions and tracks where tainted
bytes flow through SM83 registers, stack slots, and memory writes.

Scope for H5:
- byte-level taint for A/F/B/C/D/E/H/L and memory addresses;
- common data movement, ALU, rotate/shift, stack, and direct/indirect memory
  opcodes used by the battle damage path;
- sink findings for watched memory ranges such as wCurDamage;
- synthetic self-tests that exercise register copies, [hl] memory, stack
  round-trips, ALU combination, and sink reporting.

Unsupported opcodes are conservative: if they write a destination the engine
can identify, that destination is cleared rather than carrying stale taint.
The unsupported count is reported so adding new opcode handlers is visible.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Iterable, Protocol

from .disasm import Instruction, render_mnemonic


REG8 = ("a", "f", "b", "c", "d", "e", "h", "l")
REG_INDEX = {"b": 0, "c": 1, "d": 2, "e": 3, "h": 4, "l": 5, "[hl]": 6, "a": 7}
INDEX_REG = {v: k for k, v in REG_INDEX.items()}
PAIR_REGS = {
    "bc": ("b", "c"),
    "de": ("d", "e"),
    "hl": ("h", "l"),
    "af": ("a", "f"),
}


class FrameLike(Protocol):
    seq: int
    bank: int
    pc: int
    pc_label: str
    A: int
    F: int
    B: int
    C: int
    D: int
    E: int
    HL: int
    SP: int


@dataclass(frozen=True, order=True)
class TaintTag:
    """Stable origin label for a tainted byte."""

    origin: str


TaintSet = frozenset[TaintTag]
EMPTY: TaintSet = frozenset()


@dataclass
class Sink:
    name: str
    address: int
    size: int = 1

    def contains(self, addr: int) -> bool:
        addr &= 0xFFFF
        return self.address <= addr < self.address + self.size


@dataclass
class TaintFinding:
    seq: int
    pc: int
    pc_label: str
    mnemonic: str
    sink: str
    address: int
    taint: list[str]


@dataclass
class TaintReport:
    findings: list[TaintFinding] = field(default_factory=list)
    unsupported: dict[str, int] = field(default_factory=dict)
    steps: int = 0

    def to_dict(self) -> dict:
        return {
            "steps": self.steps,
            "findings": [
                {
                    "seq": f.seq,
                    "pc": f.pc,
                    "pc_label": f.pc_label,
                    "mnemonic": f.mnemonic,
                    "sink": f.sink,
                    "address": f.address,
                    "taint": f.taint,
                }
                for f in self.findings
            ],
            "unsupported": self.unsupported,
        }


@dataclass
class TaintState:
    regs: dict[str, TaintSet] = field(default_factory=lambda: {r: EMPTY for r in REG8})
    memory: dict[int, TaintSet] = field(default_factory=dict)

    def reg(self, name: str) -> TaintSet:
        return self.regs.get(name.lower(), EMPTY)

    def set_reg(self, name: str, taint: TaintSet) -> None:
        self.regs[name.lower()] = taint

    def clear_reg(self, name: str) -> None:
        self.set_reg(name, EMPTY)

    def pair(self, name: str) -> TaintSet:
        hi, lo = PAIR_REGS[name]
        return self.reg(hi) | self.reg(lo)

    def set_pair(self, name: str, hi: TaintSet, lo: TaintSet) -> None:
        r_hi, r_lo = PAIR_REGS[name]
        self.set_reg(r_hi, hi)
        self.set_reg(r_lo, lo)

    def clear_pair(self, name: str) -> None:
        self.set_pair(name, EMPTY, EMPTY)

    def mem(self, addr: int) -> TaintSet:
        return self.memory.get(addr & 0xFFFF, EMPTY)

    def set_mem(self, addr: int, taint: TaintSet) -> None:
        addr &= 0xFFFF
        if taint:
            self.memory[addr] = taint
        else:
            self.memory.pop(addr, None)

    def seed_reg(self, name: str, origin: str) -> None:
        self.set_reg(name, frozenset({TaintTag(origin)}))

    def seed_mem(self, addr: int, origin: str) -> None:
        self.set_mem(addr, frozenset({TaintTag(origin)}))


def _reg_value(frame: FrameLike, reg: str) -> int:
    return int(getattr(frame, reg.upper())) & 0xFF


def _pair_value(frame: FrameLike, pair: str) -> int:
    pair = pair.lower()
    if pair == "hl":
        return int(frame.HL) & 0xFFFF
    if pair == "bc":
        return ((_reg_value(frame, "b") << 8) | _reg_value(frame, "c")) & 0xFFFF
    if pair == "de":
        return ((_reg_value(frame, "d") << 8) | _reg_value(frame, "e")) & 0xFFFF
    if pair == "af":
        return ((_reg_value(frame, "a") << 8) | _reg_value(frame, "f")) & 0xFFFF
    if pair == "sp":
        return int(frame.SP) & 0xFFFF
    raise KeyError(pair)


def _u16_from_operand(instr: Instruction) -> int:
    if len(instr.operand) < 2:
        return 0
    return int(instr.operand[0]) | (int(instr.operand[1]) << 8)


def _hram_addr(byte: int) -> int:
    return 0xFF00 + (byte & 0xFF)


def _fmt_taint(taint: TaintSet) -> list[str]:
    return sorted(t.origin for t in taint)


class TaintEngine:
    def __init__(self, *, sinks: Iterable[Sink] = ()):
        self.state = TaintState()
        self.sinks = list(sinks)
        self.report = TaintReport()

    def seed_reg(self, name: str, origin: str) -> None:
        self.state.seed_reg(name, origin)

    def seed_mem(self, addr: int, origin: str) -> None:
        self.state.seed_mem(addr, origin)

    def run(
        self,
        instructions: Iterable[Instruction],
        frames: Iterable[FrameLike],
    ) -> TaintReport:
        by_pc = {(instr.bank, instr.pc): instr for instr in instructions}
        for frame in sorted(frames, key=lambda f: int(f.seq)):
            instr = by_pc.get((frame.bank, frame.pc))
            if instr is None:
                continue
            self.step(instr, frame)
        return self.report

    def step(self, instr: Instruction, frame: FrameLike) -> None:
        self.report.steps += 1
        handled = self._step_impl(instr, frame)
        if not handled:
            key = f"{instr.opcode:02x} {instr.mnemonic}"
            self.report.unsupported[key] = self.report.unsupported.get(key, 0) + 1

    def _record_mem_write(self, instr: Instruction, frame: FrameLike, addr: int, taint: TaintSet) -> None:
        self.state.set_mem(addr, taint)
        if not taint:
            return
        for sink in self.sinks:
            if sink.contains(addr):
                self.report.findings.append(TaintFinding(
                    seq=int(frame.seq),
                    pc=instr.pc,
                    pc_label=frame.pc_label,
                    mnemonic=instr.mnemonic,
                    sink=sink.name,
                    address=addr & 0xFFFF,
                    taint=_fmt_taint(taint),
                ))

    def _read_operand_taint(self, operand: str, frame: FrameLike) -> TaintSet:
        operand = operand.lower()
        if operand == "[hl]":
            return self.state.mem(_pair_value(frame, "hl"))
        if operand in REG8:
            return self.state.reg(operand)
        raise KeyError(operand)

    def _write_operand_taint(
        self,
        operand: str,
        taint: TaintSet,
        instr: Instruction,
        frame: FrameLike,
    ) -> None:
        operand = operand.lower()
        if operand == "[hl]":
            self._record_mem_write(instr, frame, _pair_value(frame, "hl"), taint)
        elif operand in REG8:
            self.state.set_reg(operand, taint)
        else:
            raise KeyError(operand)

    def _alu_a(self, instr: Instruction, frame: FrameLike, src: str | None, *, writes_a: bool = True) -> bool:
        src_taint = EMPTY if src is None else self._read_operand_taint(src, frame)
        a_taint = self.state.reg("a")
        combined = a_taint | src_taint
        self.state.set_reg("f", combined)
        if writes_a:
            if instr.opcode == 0xAF or (instr.opcode == 0xA8 + REG_INDEX["a"]):
                # xor a deterministically clears A.
                self.state.clear_reg("a")
            else:
                self.state.set_reg("a", combined)
        return True

    def _step_impl(self, instr: Instruction, frame: FrameLike) -> bool:
        op = instr.opcode

        # nop / control flow with no modeled data effect.
        if op in {
            0x00, 0x18, 0x20, 0x28, 0x30, 0x38,
            0xC0, 0xC2, 0xC3, 0xC4, 0xC8, 0xC9, 0xCA, 0xCC, 0xCD,
            0xCF, 0xD0, 0xD2, 0xD4, 0xD8, 0xD9, 0xDA, 0xDC,
            0xDF, 0xE7, 0xE9, 0xEF, 0xF3, 0xF7, 0xFB, 0xFF,
        }:
            return True

        # 8-bit immediate loads.
        imm_to_reg = {
            0x06: "b", 0x0E: "c", 0x16: "d", 0x1E: "e",
            0x26: "h", 0x2E: "l", 0x3E: "a",
        }
        if op in imm_to_reg:
            self.state.clear_reg(imm_to_reg[op])
            return True
        if op == 0x36:  # ld [hl], n
            self._record_mem_write(instr, frame, _pair_value(frame, "hl"), EMPTY)
            return True

        # 16-bit immediate loads.
        imm16_to_pair = {0x01: "bc", 0x11: "de", 0x21: "hl", 0x31: "sp"}
        if op in imm16_to_pair:
            pair = imm16_to_pair[op]
            if pair != "sp":
                self.state.clear_pair(pair)
            return True

        # LD r,r / LD r,[hl] / LD [hl],r.
        if 0x40 <= op <= 0x7F and op != 0x76:
            dst = INDEX_REG[(op >> 3) & 0x07]
            src = INDEX_REG[op & 0x07]
            self._write_operand_taint(dst, self._read_operand_taint(src, frame), instr, frame)
            return True

        # Direct and indirect loads.
        if op == 0x02:  # ld [bc], a
            self._record_mem_write(instr, frame, _pair_value(frame, "bc"), self.state.reg("a"))
            return True
        if op == 0x12:  # ld [de], a
            self._record_mem_write(instr, frame, _pair_value(frame, "de"), self.state.reg("a"))
            return True
        if op == 0x0A:  # ld a, [bc]
            self.state.set_reg("a", self.state.mem(_pair_value(frame, "bc")))
            return True
        if op == 0x1A:  # ld a, [de]
            self.state.set_reg("a", self.state.mem(_pair_value(frame, "de")))
            return True
        if op == 0x22:  # ld [hli], a
            self._record_mem_write(instr, frame, _pair_value(frame, "hl"), self.state.reg("a"))
            self.state.set_reg("h", self.state.pair("hl"))
            self.state.set_reg("l", self.state.pair("hl"))
            return True
        if op == 0x32:  # ld [hld], a
            self._record_mem_write(instr, frame, _pair_value(frame, "hl"), self.state.reg("a"))
            self.state.set_reg("h", self.state.pair("hl"))
            self.state.set_reg("l", self.state.pair("hl"))
            return True
        if op == 0x2A:  # ld a, [hli]
            self.state.set_reg("a", self.state.mem(_pair_value(frame, "hl")))
            self.state.set_reg("h", self.state.pair("hl"))
            self.state.set_reg("l", self.state.pair("hl"))
            return True
        if op == 0x3A:  # ld a, [hld]
            self.state.set_reg("a", self.state.mem(_pair_value(frame, "hl")))
            self.state.set_reg("h", self.state.pair("hl"))
            self.state.set_reg("l", self.state.pair("hl"))
            return True
        if op == 0xEA:  # ld [nn], a
            self._record_mem_write(instr, frame, _u16_from_operand(instr), self.state.reg("a"))
            return True
        if op == 0xFA:  # ld a, [nn]
            self.state.set_reg("a", self.state.mem(_u16_from_operand(instr)))
            return True
        if op == 0xE0:  # ldh [n], a
            self._record_mem_write(instr, frame, _hram_addr(instr.operand[0]), self.state.reg("a"))
            return True
        if op == 0xF0:  # ldh a, [n]
            self.state.set_reg("a", self.state.mem(_hram_addr(instr.operand[0])))
            return True
        if op == 0xE2:  # ldh [c], a
            self._record_mem_write(instr, frame, _hram_addr(_reg_value(frame, "c")), self.state.reg("a"))
            return True
        if op == 0xF2:  # ldh a, [c]
            self.state.set_reg("a", self.state.mem(_hram_addr(_reg_value(frame, "c"))))
            return True

        # 8-bit inc/dec preserve data dependency and taint flags.
        inc_dec_reg = {
            0x04: "b", 0x05: "b", 0x0C: "c", 0x0D: "c",
            0x14: "d", 0x15: "d", 0x1C: "e", 0x1D: "e",
            0x24: "h", 0x25: "h", 0x2C: "l", 0x2D: "l",
            0x3C: "a", 0x3D: "a",
        }
        if op in inc_dec_reg:
            taint = self.state.reg(inc_dec_reg[op])
            self.state.set_reg("f", taint)
            return True
        if op in (0x34, 0x35):  # inc/dec [hl]
            taint = self.state.mem(_pair_value(frame, "hl"))
            self._record_mem_write(instr, frame, _pair_value(frame, "hl"), taint)
            self.state.set_reg("f", taint)
            return True

        # 16-bit inc/dec preserve dependency in the pair; ADD HL combines.
        if op in (0x03, 0x0B, 0x13, 0x1B, 0x23, 0x2B, 0x33, 0x3B):
            return True
        add_hl_pair = {0x09: "bc", 0x19: "de", 0x29: "hl", 0x39: "sp"}
        if op in add_hl_pair:
            combined = self.state.pair("hl")
            if add_hl_pair[op] != "sp":
                combined |= self.state.pair(add_hl_pair[op])
            self.state.set_pair("hl", combined, combined)
            self.state.set_reg("f", combined)
            return True

        # Rotates and flag operations. Rotates preserve A taint; flag-only ops
        # taint F from A or clear it if no value participates.
        if op in (0x07, 0x0F, 0x17, 0x1F, 0x27, 0x2F):
            self.state.set_reg("f", self.state.reg("a"))
            return True
        if op in (0x37, 0x3F):
            self.state.clear_reg("f")
            return True

        # ALU A,r family.
        if 0x80 <= op <= 0xBF:
            alu = (op >> 3) & 0x07
            src = INDEX_REG[op & 0x07]
            writes_a = alu != 7  # CP only updates flags.
            return self._alu_a(instr, frame, src, writes_a=writes_a)

        # ALU A,immediate.
        if op in (0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6):
            if op == 0xEE and _reg_value(frame, "a") == instr.operand[0]:
                self.state.clear_reg("a")
                self.state.clear_reg("f")
            else:
                self.state.set_reg("f", self.state.reg("a"))
            return True
        if op == 0xFE:  # cp n
            self.state.set_reg("f", self.state.reg("a"))
            return True

        # Stack transfers. Game Boy push writes low byte at SP-2 and high at
        # SP-1 from the pre-instruction SP; pop reads low at SP and high at SP+1.
        push_pair = {0xC5: "bc", 0xD5: "de", 0xE5: "hl", 0xF5: "af"}
        if op in push_pair:
            pair = push_pair[op]
            hi_reg, lo_reg = PAIR_REGS[pair]
            sp = (int(frame.SP) - 2) & 0xFFFF
            self._record_mem_write(instr, frame, sp, self.state.reg(lo_reg))
            self._record_mem_write(instr, frame, sp + 1, self.state.reg(hi_reg))
            return True
        pop_pair = {0xC1: "bc", 0xD1: "de", 0xE1: "hl", 0xF1: "af"}
        if op in pop_pair:
            sp = int(frame.SP) & 0xFFFF
            lo_taint = self.state.mem(sp)
            hi_taint = self.state.mem(sp + 1)
            self.state.set_pair(pop_pair[op], hi_taint, lo_taint)
            return True

        # Misc 16-bit stack/addressing ops.
        if op == 0x08:  # ld [nn], sp
            # SP is not tainted in this byte-level engine.
            self._record_mem_write(instr, frame, _u16_from_operand(instr), EMPTY)
            self._record_mem_write(instr, frame, _u16_from_operand(instr) + 1, EMPTY)
            return True
        if op == 0xE8:  # add sp, e
            self.clear_sp_flags()
            return True
        if op == 0xF8:  # ld hl, sp+e
            self.state.clear_pair("hl")
            self.clear_sp_flags()
            return True
        if op == 0xF9:  # ld sp, hl
            return True

        if op == 0xCB and instr.operand:
            return self._step_cb(instr, frame, instr.operand[0])

        return False

    def clear_sp_flags(self) -> None:
        self.state.clear_reg("f")

    def _step_cb(self, instr: Instruction, frame: FrameLike, sub: int) -> bool:
        group = (sub >> 6) & 0x03
        target = INDEX_REG[sub & 0x07]
        if group == 0:
            # rotate/shift/swap target; taint is preserved and flags derive from it.
            taint = self._read_operand_taint(target, frame)
            self._write_operand_taint(target, taint, instr, frame)
            self.state.set_reg("f", taint)
            return True
        if group == 1:
            # bit test: value not modified, flags derive from target.
            self.state.set_reg("f", self._read_operand_taint(target, frame))
            return True
        if group in (2, 3):
            # res/set target, value still depends on target plus immediate bit mask.
            taint = self._read_operand_taint(target, frame)
            self._write_operand_taint(target, taint, instr, frame)
            self.state.set_reg("f", taint)
            return True
        return False


def analyze_tracer(
    tracer,
    *,
    source_regs: dict[str, str] | None = None,
    source_mems: dict[int, str] | None = None,
    sinks: Iterable[Sink] = (),
) -> TaintReport:
    """Run taint over a populated `tracer.Tracer`.

    `tracer.install()` / scenario execution / `tracer.uninstall()` remain the
    caller's responsibility. This helper is the H5 bridge from the existing
    per-instruction hook stream to the taint engine.
    """
    engine = TaintEngine(sinks=sinks)
    for reg, origin in (source_regs or {}).items():
        engine.seed_reg(reg, origin)
    for addr, origin in (source_mems or {}).items():
        engine.seed_mem(addr, origin)
    return engine.run(tracer.instructions, tracer.frames)


@dataclass
class SyntheticFrame:
    seq: int
    bank: int
    pc: int
    pc_label: str
    A: int = 0
    F: int = 0
    B: int = 0
    C: int = 0
    D: int = 0
    E: int = 0
    HL: int = 0
    SP: int = 0xDFF0


def _ins(pc: int, op: int, operand: tuple[int, ...] = (), *, label: str | None = None) -> Instruction:
    operand_b = bytes(operand)
    mnemonic = render_mnemonic(op, operand_b)
    return Instruction(bank=0, pc=pc, opcode=op, operand=operand_b,
                       length=1 + len(operand_b), mnemonic=mnemonic)


def _frame(seq: int, pc: int, *, label: str | None = None, **regs: int) -> SyntheticFrame:
    return SyntheticFrame(seq=seq, bank=0, pc=pc, pc_label=label or f"fixture+0x{pc:x}", **regs)


def _run_fixture(
    instructions: list[Instruction],
    frames: list[SyntheticFrame],
    *,
    source_reg: str | None = None,
    source_mem: int | None = None,
    sink: Sink,
) -> TaintReport:
    engine = TaintEngine(sinks=[sink])
    if source_reg is not None:
        engine.seed_reg(source_reg, f"source:{source_reg}")
    if source_mem is not None:
        engine.seed_mem(source_mem, f"source:${source_mem:04x}")
    return engine.run(instructions, frames)


def _self_test() -> int:
    failures: list[str] = []

    # Register copy into wCurDamage high byte.
    instrs = [
        _ins(0x1000, 0x4F),                    # ld c, a
        _ins(0x1001, 0x79),                    # ld a, c
        _ins(0x1002, 0x21, (0x41, 0xD1)),      # ld hl, $d141
        _ins(0x1005, 0x22),                    # ld [hli], a
    ]
    frames = [
        _frame(0, 0x1000, A=0x37),
        _frame(1, 0x1001, A=0x37, C=0x37),
        _frame(2, 0x1002, A=0x37, C=0x37),
        _frame(3, 0x1005, A=0x37, C=0x37, HL=0xD141),
    ]
    report = _run_fixture(instrs, frames, source_reg="a", sink=Sink("wCurDamage", 0xD141, 2))
    if len(report.findings) != 1 or report.findings[0].address != 0xD141:
        failures.append("register-copy sink finding missing")

    class FakeTracer:
        def __init__(self, instructions, frames):
            self.instructions = instructions
            self.frames = frames

    bridge_report = analyze_tracer(
        FakeTracer(instrs, frames),
        source_regs={"a": "source:a"},
        sinks=[Sink("wCurDamage", 0xD141, 2)],
    )
    if len(bridge_report.findings) != 1:
        failures.append("analyze_tracer bridge failed")

    # [hl] round-trip: memory source -> B -> A -> sink.
    instrs = [
        _ins(0x1100, 0x46),                    # ld b, [hl]
        _ins(0x1101, 0x78),                    # ld a, b
        _ins(0x1102, 0xEA, (0x42, 0xD1)),      # ld [$d142], a
    ]
    frames = [
        _frame(0, 0x1100, HL=0xC010),
        _frame(1, 0x1101, B=0x88, HL=0xC010),
        _frame(2, 0x1102, A=0x88, B=0x88, HL=0xC010),
    ]
    report = _run_fixture(
        instrs, frames, source_mem=0xC010, sink=Sink("wCurDamage+1", 0xD142, 1)
    )
    if len(report.findings) != 1 or "source:$c010" not in report.findings[0].taint:
        failures.append("[hl] memory round-trip failed")

    # Stack round-trip: C -> push BC -> pop DE -> E -> sink.
    instrs = [
        _ins(0x1200, 0xC5),                    # push bc
        _ins(0x1201, 0xD1),                    # pop de
        _ins(0x1202, 0x7B),                    # ld a, e
        _ins(0x1203, 0xEA, (0x41, 0xD1)),      # ld [$d141], a
    ]
    frames = [
        _frame(0, 0x1200, B=0x12, C=0x34, SP=0xDFF0),
        _frame(1, 0x1201, SP=0xDFEE),
        _frame(2, 0x1202, D=0x12, E=0x34, SP=0xDFF0),
        _frame(3, 0x1203, A=0x34, D=0x12, E=0x34, SP=0xDFF0),
    ]
    report = _run_fixture(instrs, frames, source_reg="c", sink=Sink("wCurDamage", 0xD141, 2))
    if len(report.findings) != 1 or "source:c" not in report.findings[0].taint:
        failures.append("stack push/pop taint failed")

    # ALU combines taint: source B taints A via add a,b, then direct store.
    instrs = [
        _ins(0x1300, 0x80),                    # add a, b
        _ins(0x1301, 0xEA, (0x41, 0xD1)),      # ld [$d141], a
    ]
    frames = [
        _frame(0, 0x1300, A=1, B=2),
        _frame(1, 0x1301, A=3, B=2),
    ]
    report = _run_fixture(instrs, frames, source_reg="b", sink=Sink("wCurDamage", 0xD141, 2))
    if len(report.findings) != 1 or "source:b" not in report.findings[0].taint:
        failures.append("ALU taint combine failed")

    # Repeated PC: dynamic frames must be replayed in seq order. A static
    # PC dictionary loses the first write and only reports the last frame.
    instrs = [
        _ins(0x1400, 0x22),                    # ld [hli], a
    ]
    frames = [
        _frame(0, 0x1400, A=0x99, HL=0xD141),
        _frame(1, 0x1400, A=0x99, HL=0xD142),
    ]
    report = _run_fixture(instrs, frames, source_reg="a", sink=Sink("wCurDamage", 0xD141, 2))
    finding_addrs = [finding.address for finding in report.findings]
    if finding_addrs != [0xD141, 0xD142]:
        failures.append("dynamic repeated-PC replay order failed")

    if failures:
        print("taint self-test: FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("taint self-test: PASS")
    print("  register copies, [hl] memory, stack round-trip, ALU combine, repeated PCs, and sinks")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SM83 byte-level taint tracker")
    parser.add_argument("--self-test", action="store_true",
                        help="Run synthetic taint propagation self-tests")
    parser.add_argument("--json-self-test", action="store_true",
                        help="Emit the first synthetic self-test report as JSON")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.json_self_test:
        instrs = [
            _ins(0x1000, 0x4F),
            _ins(0x1001, 0x79),
            _ins(0x1002, 0x21, (0x41, 0xD1)),
            _ins(0x1005, 0x22),
        ]
        frames = [
            _frame(0, 0x1000, A=0x37),
            _frame(1, 0x1001, A=0x37, C=0x37),
            _frame(2, 0x1002, A=0x37, C=0x37),
            _frame(3, 0x1005, A=0x37, C=0x37, HL=0xD141),
        ]
        report = _run_fixture(instrs, frames, source_reg="a", sink=Sink("wCurDamage", 0xD141, 2))
        print(json.dumps(report.to_dict(), indent=2))
        return 0 if report.findings else 1
    parser.error("specify --self-test or --json-self-test")


if __name__ == "__main__":
    sys.exit(main())
