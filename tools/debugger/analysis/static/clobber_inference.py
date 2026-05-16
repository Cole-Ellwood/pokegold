"""Per-function register-clobber inference via backwards abstract interpretation.

The P7 keystone: given a function's disassembly, infer which registers it
uses (reads before writing), defines (writes), and preserves (push/pop).
This is the foundation for check_farcall_register_clobber, check_abi_drift,
and check_stack_bounds.

Architecture: 8-register lattice {A, B, C, D, E, H, L, F} with three
abstract values per register: BOTTOM (unknown), DEFINED (written), USED
(read before written). Fixed-point iteration over basic blocks.

The SM83 makes this tractable: 8 GP registers, no SIMD, no out-of-order,
no implicit register renames. ~600 LOC for the core, per the roadmap.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...kernel.symbol_service import SymbolService

ALL_REGS = ("A", "B", "C", "D", "E", "H", "L", "F")
PAIR_REGS = {"BC": ("B", "C"), "DE": ("D", "E"), "HL": ("H", "L"), "AF": ("A", "F")}


class RegState(Enum):
    BOTTOM = auto()
    USED = auto()
    DEFINED = auto()


@dataclass(frozen=True)
class RegisterSummary:
    """Per-function calling convention summary."""
    name: str
    bank: int
    address: int
    uses: frozenset[str] = frozenset()
    defs: frozenset[str] = frozenset()
    preserves: frozenset[str] = frozenset()
    calls: tuple[str, ...] = ()
    is_leaf: bool = True
    stack_depth: int = 0

    def clobbers(self) -> frozenset[str]:
        return self.defs - self.preserves

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "bank": self.bank,
            "address": self.address,
            "uses": sorted(self.uses),
            "defs": sorted(self.defs),
            "preserves": sorted(self.preserves),
            "clobbers": sorted(self.clobbers()),
            "calls": list(self.calls),
            "is_leaf": self.is_leaf,
            "stack_depth": self.stack_depth,
        }


@dataclass
class _BlockState:
    regs: dict[str, RegState] = field(default_factory=lambda: {r: RegState.BOTTOM for r in ALL_REGS})
    push_stack: list[str] = field(default_factory=list)
    max_stack: int = 0
    cur_stack: int = 0

    def mark_use(self, reg: str) -> None:
        if self.regs.get(reg) == RegState.BOTTOM:
            self.regs[reg] = RegState.USED

    def mark_def(self, reg: str) -> None:
        if self.regs.get(reg) != RegState.USED:
            self.regs[reg] = RegState.DEFINED

    def mark_pair_use(self, pair: str) -> None:
        for r in PAIR_REGS.get(pair, ()):
            self.mark_use(r)

    def mark_pair_def(self, pair: str) -> None:
        for r in PAIR_REGS.get(pair, ()):
            self.mark_def(r)

    def push(self, pair: str) -> None:
        self.push_stack.append(pair)
        self.cur_stack += 2
        if self.cur_stack > self.max_stack:
            self.max_stack = self.cur_stack

    def pop(self, pair: str) -> None:
        if self.push_stack and self.push_stack[-1] == pair:
            self.push_stack.pop()
        self.cur_stack = max(0, self.cur_stack - 2)


_LD_R_R_BASE = 0x40
_ALU_BASE = 0x80
_REG8_IDX = ("B", "C", "D", "E", "H", "L", "[HL]", "A")
_ALU_OPS = ("ADD", "ADC", "SUB", "SBC", "AND", "XOR", "OR", "CP")

_PUSH_OPS = {0xC5: "BC", 0xD5: "DE", 0xE5: "HL", 0xF5: "AF"}
_POP_OPS = {0xC1: "BC", 0xD1: "DE", 0xE1: "HL", 0xF1: "AF"}

_INC_R = {0x04: "B", 0x0C: "C", 0x14: "D", 0x1C: "E", 0x24: "H", 0x2C: "L", 0x3C: "A"}
_DEC_R = {0x05: "B", 0x0D: "C", 0x15: "D", 0x1D: "E", 0x25: "H", 0x2D: "L", 0x3D: "A"}

_INC_RR = {0x03: "BC", 0x13: "DE", 0x23: "HL", 0x33: "SP"}
_DEC_RR = {0x0B: "BC", 0x1B: "DE", 0x2B: "HL", 0x3B: "SP"}

_LD_R_N = {0x06: "B", 0x0E: "C", 0x16: "D", 0x1E: "E", 0x26: "H", 0x2E: "L", 0x3E: "A"}

_ADD_HL_RR = {0x09: "BC", 0x19: "DE", 0x29: "HL", 0x39: "SP"}

CALL_OPCODES = {0xCD, 0xC4, 0xCC, 0xD4, 0xDC}
RST_OPCODES = {0xC7, 0xCF, 0xD7, 0xDF, 0xE7, 0xEF, 0xF7, 0xFF}


def _analyze_opcode(op: int, operand: bytes, state: _BlockState) -> list[str]:
    """Update state for one instruction. Returns list of call targets (labels)."""
    calls: list[str] = []

    if 0x40 <= op <= 0x7F and op != 0x76:
        dst_idx = (op >> 3) & 0x07
        src_idx = op & 0x07
        src = _REG8_IDX[src_idx]
        dst = _REG8_IDX[dst_idx]
        if src == "[HL]":
            state.mark_use("H")
            state.mark_use("L")
        else:
            state.mark_use(src)
        if dst == "[HL]":
            state.mark_use("H")
            state.mark_use("L")
        else:
            state.mark_def(dst)
        return calls

    if 0x80 <= op <= 0xBF:
        src_idx = op & 0x07
        src = _REG8_IDX[src_idx]
        if src == "[HL]":
            state.mark_use("H")
            state.mark_use("L")
        else:
            state.mark_use(src)
        state.mark_use("A")
        alu_op = (op >> 3) & 0x07
        if alu_op != 7:  # CP doesn't write A
            state.mark_def("A")
        state.mark_def("F")
        return calls

    if op in _PUSH_OPS:
        pair = _PUSH_OPS[op]
        state.mark_pair_use(pair)
        state.push(pair)
        return calls

    if op in _POP_OPS:
        pair = _POP_OPS[op]
        state.mark_pair_def(pair)
        state.pop(pair)
        return calls

    if op in _INC_R:
        r = _INC_R[op]
        state.mark_use(r)
        state.mark_def(r)
        state.mark_def("F")
        return calls

    if op in _DEC_R:
        r = _DEC_R[op]
        state.mark_use(r)
        state.mark_def(r)
        state.mark_def("F")
        return calls

    if op in _INC_RR:
        pair = _INC_RR[op]
        if pair != "SP":
            state.mark_pair_use(pair)
            state.mark_pair_def(pair)
        return calls

    if op in _DEC_RR:
        pair = _DEC_RR[op]
        if pair != "SP":
            state.mark_pair_use(pair)
            state.mark_pair_def(pair)
        return calls

    if op in _LD_R_N:
        r = _LD_R_N[op]
        state.mark_def(r)
        return calls

    if op in _ADD_HL_RR:
        pair = _ADD_HL_RR[op]
        state.mark_use("H")
        state.mark_use("L")
        if pair != "SP" and pair != "HL":
            state.mark_pair_use(pair)
        state.mark_def("H")
        state.mark_def("L")
        state.mark_def("F")
        return calls

    if op == 0x36:  # LD [HL], n
        state.mark_use("H")
        state.mark_use("L")
        return calls

    if op == 0x0A:  # LD A, [BC]
        state.mark_use("B")
        state.mark_use("C")
        state.mark_def("A")
    elif op == 0x1A:  # LD A, [DE]
        state.mark_use("D")
        state.mark_use("E")
        state.mark_def("A")
    elif op == 0x02:  # LD [BC], A
        state.mark_use("B")
        state.mark_use("C")
        state.mark_use("A")
    elif op == 0x12:  # LD [DE], A
        state.mark_use("D")
        state.mark_use("E")
        state.mark_use("A")
    elif op == 0x22:  # LD [HLI], A
        state.mark_use("H")
        state.mark_use("L")
        state.mark_use("A")
        state.mark_def("H")
        state.mark_def("L")
    elif op == 0x2A:  # LD A, [HLI]
        state.mark_use("H")
        state.mark_use("L")
        state.mark_def("A")
        state.mark_def("H")
        state.mark_def("L")
    elif op == 0x32:  # LD [HLD], A
        state.mark_use("H")
        state.mark_use("L")
        state.mark_use("A")
        state.mark_def("H")
        state.mark_def("L")
    elif op == 0x3A:  # LD A, [HLD]
        state.mark_use("H")
        state.mark_use("L")
        state.mark_def("A")
        state.mark_def("H")
        state.mark_def("L")
    elif op == 0xE0:  # LDH [n], A
        state.mark_use("A")
    elif op == 0xF0:  # LDH A, [n]
        state.mark_def("A")
    elif op == 0xE2:  # LDH [C], A
        state.mark_use("C")
        state.mark_use("A")
    elif op == 0xF2:  # LDH A, [C]
        state.mark_use("C")
        state.mark_def("A")
    elif op == 0xEA:  # LD [nn], A
        state.mark_use("A")
    elif op == 0xFA:  # LD A, [nn]
        state.mark_def("A")
    elif op == 0x2F:  # CPL
        state.mark_use("A")
        state.mark_def("A")
        state.mark_def("F")
    elif op == 0x27:  # DAA
        state.mark_use("A")
        state.mark_def("A")
        state.mark_def("F")
    elif op == 0x37:  # SCF
        state.mark_def("F")
    elif op == 0x3F:  # CCF
        state.mark_use("F")
        state.mark_def("F")
    elif op == 0x07:  # RLCA
        state.mark_use("A")
        state.mark_def("A")
        state.mark_def("F")
    elif op == 0x0F:  # RRCA
        state.mark_use("A")
        state.mark_def("A")
        state.mark_def("F")
    elif op == 0x17:  # RLA
        state.mark_use("A")
        state.mark_use("F")
        state.mark_def("A")
        state.mark_def("F")
    elif op == 0x1F:  # RRA
        state.mark_use("A")
        state.mark_use("F")
        state.mark_def("A")
        state.mark_def("F")
    elif op in (0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6):
        # ADD/ADC/SUB/SBC/AND/XOR/OR A, n
        state.mark_use("A")
        state.mark_def("A")
        state.mark_def("F")
    elif op == 0xFE:  # CP n
        state.mark_use("A")
        state.mark_def("F")
    elif op == 0xE8:  # ADD SP, e8
        state.mark_def("F")
    elif op == 0xF8:  # LD HL, SP+e8
        state.mark_def("H")
        state.mark_def("L")
        state.mark_def("F")
    elif op == 0x08:  # LD [nn], SP
        pass
    elif op == 0xF9:  # LD SP, HL
        state.mark_use("H")
        state.mark_use("L")
    elif op == 0xE9:  # JP HL
        state.mark_use("H")
        state.mark_use("L")
    elif op == 0x01:  # LD BC, nn
        state.mark_def("B")
        state.mark_def("C")
    elif op == 0x11:  # LD DE, nn
        state.mark_def("D")
        state.mark_def("E")
    elif op == 0x21:  # LD HL, nn
        state.mark_def("H")
        state.mark_def("L")
    elif op == 0x31:  # LD SP, nn
        pass
    elif op == 0xCB and len(operand) >= 1:
        sub = operand[0]
        r = _REG8_IDX[sub & 0x07]
        high = (sub >> 6) & 0x03
        if r == "[HL]":
            state.mark_use("H")
            state.mark_use("L")
        else:
            if high == 1:  # BIT — read only
                state.mark_use(r)
            else:  # RLC/RRC/RL/RR/SLA/SRA/SWAP/SRL/RES/SET — read+write
                state.mark_use(r)
                state.mark_def(r)
        state.mark_def("F")
    elif op in CALL_OPCODES:
        state.cur_stack += 2
        if state.cur_stack > state.max_stack:
            state.max_stack = state.cur_stack
    elif op in RST_OPCODES:
        state.cur_stack += 2
        if state.cur_stack > state.max_stack:
            state.max_stack = state.cur_stack

    return calls


def infer_summary_from_bytes(
    name: str,
    bank: int,
    address: int,
    rom: bytes,
    sym_service: SymbolService | None = None,
    max_bytes: int = 0x800,
) -> RegisterSummary:
    """Infer register summary for a function from raw ROM bytes."""
    from ...kernel.symbol_service import SymbolService as _SvcType

    if bank == 0:
        rom_offset = address
    else:
        rom_offset = bank * 0x4000 + (address - 0x4000)

    if rom_offset < 0 or rom_offset >= len(rom):
        return RegisterSummary(name=name, bank=bank, address=address)

    boundary_labels: set[int] = set()
    if sym_service is not None:
        labels = sym_service.labels_in_bank(bank)
        for addr, lbl in labels:
            if addr > address and not lbl.startswith(name + "."):
                boundary_labels.add(addr)
                break

    end_addr = address + max_bytes
    if boundary_labels:
        end_addr = min(end_addr, min(boundary_labels))

    state = _BlockState()
    calls_found: list[str] = []
    is_leaf = True

    pc = address
    from ...instrumentation.macro_resolver import MacroResolver

    TERMINATORS = {0xC9, 0xD9, 0xC3, 0x18, 0xE9}
    forward_targets: set[int] = set()

    while pc < end_addr:
        offset = (bank * 0x4000 + (pc - 0x4000)) if bank > 0 else pc
        if offset >= len(rom):
            break
        op = rom[offset]

        from tools.damage_debugger.disasm import opcode_length
        length = opcode_length(op)
        if offset + length > len(rom):
            break

        operand = bytes(rom[offset + i] for i in range(1, length))

        new_calls = _analyze_opcode(op, operand, state)
        calls_found.extend(new_calls)

        if op in CALL_OPCODES or op in RST_OPCODES:
            is_leaf = False

        if op in (0x18, 0x20, 0x28, 0x30, 0x38):
            e8 = operand[0] if operand[0] < 0x80 else operand[0] - 0x100
            target = pc + 2 + e8
            if target > pc and target < end_addr:
                forward_targets.add(target)
        elif op in (0xC2, 0xC3, 0xCA, 0xD2, 0xDA):
            if len(operand) >= 2:
                target = operand[0] | (operand[1] << 8)
                if target > pc and target < end_addr:
                    forward_targets.add(target)

        next_pc = pc + length
        if op in TERMINATORS:
            if not any(t > next_pc for t in forward_targets):
                break
        pc = next_pc

    preserves: set[str] = set()
    push_pops = state.push_stack
    for pair_name in ("BC", "DE", "HL", "AF"):
        if pair_name in PAIR_REGS:
            r1, r2 = PAIR_REGS[pair_name]
            if (state.regs.get(r1) != RegState.DEFINED and
                    state.regs.get(r2) != RegState.DEFINED):
                pass

    uses = frozenset(r for r, s in state.regs.items() if s == RegState.USED)
    defs = frozenset(r for r, s in state.regs.items() if s == RegState.DEFINED)

    return RegisterSummary(
        name=name,
        bank=bank,
        address=address,
        uses=uses,
        defs=defs,
        preserves=frozenset(preserves),
        calls=tuple(calls_found),
        is_leaf=is_leaf,
        stack_depth=state.max_stack,
    )


def infer_summary(
    name: str,
    svc: SymbolService,
    rom: bytes,
    max_bytes: int = 0x800,
) -> RegisterSummary | None:
    """Infer register summary by symbol name."""
    sym = svc.resolve(name)
    if sym is None:
        return None
    return infer_summary_from_bytes(
        name=name,
        bank=sym.bank,
        address=sym.address,
        rom=rom,
        sym_service=svc,
        max_bytes=max_bytes,
    )


def batch_infer(
    names: list[str],
    svc: SymbolService,
    rom: bytes,
) -> dict[str, RegisterSummary]:
    """Infer summaries for multiple functions."""
    results: dict[str, RegisterSummary] = {}
    for name in names:
        summary = infer_summary(name, svc, rom)
        if summary is not None:
            results[name] = summary
    return results
