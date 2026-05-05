"""Minimal Sharp SM83 instruction-length walker + mnemonic renderer.

The tracer needs to enumerate every PC inside a function so it can
register a hook at each one (PyBoy has no public single-step API).
That requires a length table; a mnemonic table is included for
human-readable trace output.

Spec source: https://gbdev.io/gb-opcodes/optables/
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

# 0=illegal/length-0 placeholder; we substitute 1 in the walker.
_LEN1 = 1
_LEN2 = 2
_LEN3 = 3

# Default = 1 unless overridden.
_OVERRIDES_2 = {
    # LD r,n
    0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x36, 0x3E,
    # JR e8 / JR cc,e8
    0x18, 0x20, 0x28, 0x30, 0x38,
    # ADD/ADC/SUB/SBC/AND/XOR/OR/CP A,n
    0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6, 0xFE,
    # LDH (n),A / LDH A,(n)
    0xE0, 0xF0,
    # ADD SP,e8 / LD HL,SP+e8
    0xE8, 0xF8,
    # CB prefix (always 2 bytes total)
    0xCB,
    # STOP (officially STOP 0x00, treat as 2)
    0x10,
}

_OVERRIDES_3 = {
    # 16-bit immediate loads
    0x01, 0x11, 0x21, 0x31,
    # LD (nn),SP
    0x08,
    # JP / JP cc
    0xC2, 0xC3, 0xCA, 0xD2, 0xDA,
    # CALL / CALL cc
    0xC4, 0xCC, 0xCD, 0xD4, 0xDC,
    # LD (nn),A / LD A,(nn)
    0xEA, 0xFA,
}

_ILLEGAL = {0xD3, 0xDB, 0xDD, 0xE3, 0xE4, 0xEB, 0xEC, 0xED, 0xF4, 0xFC, 0xFD}

# Unconditional terminators (control flow does not fall through)
TERMINATORS_UNCOND = {
    0xC9,  # RET
    0xD9,  # RETI
    0xC3,  # JP nn
    0x18,  # JR e
    0xE9,  # JP HL
}

CALL_OPCODES = {0xCD, 0xC4, 0xCC, 0xD4, 0xDC}
RST_OPCODES = {0xC7, 0xCF, 0xD7, 0xDF, 0xE7, 0xEF, 0xF7, 0xFF}


def opcode_length(op: int) -> int:
    if op in _OVERRIDES_3:
        return _LEN3
    if op in _OVERRIDES_2:
        return _LEN2
    return _LEN1


def is_call(op: int) -> bool:
    return op in CALL_OPCODES


def is_rst(op: int) -> bool:
    return op in RST_OPCODES


def is_ret(op: int) -> bool:
    # All RET variants
    return op in (0xC9, 0xD9, 0xC0, 0xC8, 0xD0, 0xD8)


# Mnemonics: minimal coverage for the ops that appear in DamageCalc.
# Format string applied to operand bytes (b1, b2 little-endian for 16-bit).
_MNEMONICS: dict[int, str] = {
    0x00: "nop",
    0x01: "ld bc, ${b21:04x}",
    0x02: "ld [bc], a",
    0x03: "inc bc",
    0x04: "inc b",
    0x05: "dec b",
    0x06: "ld b, ${b1:02x}",
    0x07: "rlca",
    0x08: "ld [${b21:04x}], sp",
    0x09: "add hl, bc",
    0x0A: "ld a, [bc]",
    0x0B: "dec bc",
    0x0C: "inc c",
    0x0D: "dec c",
    0x0E: "ld c, ${b1:02x}",
    0x0F: "rrca",
    0x10: "stop",
    0x11: "ld de, ${b21:04x}",
    0x12: "ld [de], a",
    0x13: "inc de",
    0x14: "inc d",
    0x15: "dec d",
    0x16: "ld d, ${b1:02x}",
    0x17: "rla",
    0x18: "jr ${e8}",
    0x19: "add hl, de",
    0x1A: "ld a, [de]",
    0x1B: "dec de",
    0x1C: "inc e",
    0x1D: "dec e",
    0x1E: "ld e, ${b1:02x}",
    0x1F: "rra",
    0x20: "jr nz, ${e8}",
    0x21: "ld hl, ${b21:04x}",
    0x22: "ld [hli], a",
    0x23: "inc hl",
    0x24: "inc h",
    0x25: "dec h",
    0x26: "ld h, ${b1:02x}",
    0x27: "daa",
    0x28: "jr z, ${e8}",
    0x29: "add hl, hl",
    0x2A: "ld a, [hli]",
    0x2B: "dec hl",
    0x2C: "inc l",
    0x2D: "dec l",
    0x2E: "ld l, ${b1:02x}",
    0x2F: "cpl",
    0x30: "jr nc, ${e8}",
    0x31: "ld sp, ${b21:04x}",
    0x32: "ld [hld], a",
    0x33: "inc sp",
    0x34: "inc [hl]",
    0x35: "dec [hl]",
    0x36: "ld [hl], ${b1:02x}",
    0x37: "scf",
    0x38: "jr c, ${e8}",
    0x39: "add hl, sp",
    0x3A: "ld a, [hld]",
    0x3B: "dec sp",
    0x3C: "inc a",
    0x3D: "dec a",
    0x3E: "ld a, ${b1:02x}",
    0x3F: "ccf",
    # 0x40-0x7F: ld r,r and ld r,[hl] — generated below
    # 0x80-0xBF: alu A,r — generated below
    0xC0: "ret nz",
    0xC1: "pop bc",
    0xC2: "jp nz, ${b21:04x}",
    0xC3: "jp ${b21:04x}",
    0xC4: "call nz, ${b21:04x}",
    0xC5: "push bc",
    0xC6: "add a, ${b1:02x}",
    0xC7: "rst $00",
    0xC8: "ret z",
    0xC9: "ret",
    0xCA: "jp z, ${b21:04x}",
    0xCB: "cb ${b1:02x}",
    0xCC: "call z, ${b21:04x}",
    0xCD: "call ${b21:04x}",
    0xCE: "adc a, ${b1:02x}",
    0xCF: "rst $08",
    0xD0: "ret nc",
    0xD1: "pop de",
    0xD2: "jp nc, ${b21:04x}",
    0xD4: "call nc, ${b21:04x}",
    0xD5: "push de",
    0xD6: "sub ${b1:02x}",
    0xD7: "rst $10",
    0xD8: "ret c",
    0xD9: "reti",
    0xDA: "jp c, ${b21:04x}",
    0xDC: "call c, ${b21:04x}",
    0xDE: "sbc a, ${b1:02x}",
    0xDF: "rst $18",
    0xE0: "ldh [${b1:02x}], a",
    0xE1: "pop hl",
    0xE2: "ldh [c], a",
    0xE5: "push hl",
    0xE6: "and ${b1:02x}",
    0xE7: "rst $20",
    0xE8: "add sp, ${e8}",
    0xE9: "jp hl",
    0xEA: "ld [${b21:04x}], a",
    0xEE: "xor ${b1:02x}",
    0xEF: "rst $28",
    0xF0: "ldh a, [${b1:02x}]",
    0xF1: "pop af",
    0xF2: "ldh a, [c]",
    0xF3: "di",
    0xF5: "push af",
    0xF6: "or ${b1:02x}",
    0xF7: "rst $30",
    0xF8: "ld hl, sp+${e8}",
    0xF9: "ld sp, hl",
    0xFA: "ld a, [${b21:04x}]",
    0xFB: "ei",
    0xFE: "cp ${b1:02x}",
    0xFF: "rst $38",
}

_REG8 = ("b", "c", "d", "e", "h", "l", "[hl]", "a")


def _build_alu_table() -> None:
    # 0x40-0x7F: LD r,r' (76 = HALT)
    for op in range(0x40, 0x80):
        if op == 0x76:
            _MNEMONICS[op] = "halt"
            continue
        dst = (op >> 3) & 0x07
        src = op & 0x07
        _MNEMONICS[op] = f"ld {_REG8[dst]}, {_REG8[src]}"
    # 0x80-0xBF: ALU A,r
    alu_names = ("add a,", "adc a,", "sub", "sbc a,", "and", "xor", "or", "cp")
    for op in range(0x80, 0xC0):
        alu = (op >> 3) & 0x07
        src = op & 0x07
        _MNEMONICS[op] = f"{alu_names[alu]} {_REG8[src]}"


_build_alu_table()


def render_mnemonic(op: int, operand_bytes: bytes) -> str:
    if op in _ILLEGAL:
        return f"db ${op:02x}"
    template = _MNEMONICS.get(op, f"db ${op:02x}")
    if op == 0xCB and len(operand_bytes) >= 1:
        return _render_cb(operand_bytes[0])
    b1 = operand_bytes[0] if operand_bytes else 0
    b2 = operand_bytes[1] if len(operand_bytes) > 1 else 0
    b21 = b1 | (b2 << 8)
    e8 = b1 if b1 < 0x80 else b1 - 0x100  # signed byte
    return template.format(b1=b1, b2=b2, b21=b21, e8=e8)


def _render_cb(sub: int) -> str:
    reg = _REG8[sub & 0x07]
    high = (sub >> 6) & 0x03
    bit = (sub >> 3) & 0x07
    if high == 0:
        ops = ("rlc", "rrc", "rl", "rr", "sla", "sra", "swap", "srl")
        return f"{ops[bit]} {reg}"
    if high == 1:
        return f"bit {bit}, {reg}"
    if high == 2:
        return f"res {bit}, {reg}"
    return f"set {bit}, {reg}"


@dataclass(frozen=True)
class Instruction:
    bank: int
    pc: int
    opcode: int
    operand: bytes
    length: int
    mnemonic: str

    @property
    def end(self) -> int:
        return self.pc + self.length


def walk_function(
    read_byte: Callable[[int, int], int],
    sym_table,
    start_name: str,
    *,
    max_bytes: int = 0x800,
    stop_at_next_top_level: bool = True,
) -> list[Instruction]:
    """Disassemble a function starting at start_name.

    read_byte(bank, addr) returns one byte from the ROM. sym_table is a
    SymbolTable. Walks linearly, decoding each instruction by length;
    stops when one of:
      - PC reaches max_bytes past the start
      - PC reaches the address of the next top-level symbol in the
        same bank (a label whose name is not "<start_name>.<sub>")
      - last instruction was an unconditional terminator AND we're past
        any forward-jump target seen so far (conservative).
    """
    start_sym = sym_table[start_name]
    bank, start = start_sym.bank, start_sym.address

    boundary = start + max_bytes
    if stop_at_next_top_level:
        for addr, name in sym_table.labels_in(bank):
            if addr <= start:
                continue
            if not name.startswith(start_name + "."):
                if addr < boundary:
                    boundary = addr
                break
            else:
                # sub-label, keep going
                continue

    out: list[Instruction] = []
    pc = start
    forward_targets: set[int] = set()  # pcs that are jumped TO from earlier in the func
    while pc < boundary:
        op = read_byte(bank, pc)
        length = opcode_length(op)
        if pc + length > boundary:
            break
        operand = bytes(read_byte(bank, pc + i) for i in range(1, length))
        mnemonic = render_mnemonic(op, operand)
        instr = Instruction(bank=bank, pc=pc, opcode=op, operand=operand,
                            length=length, mnemonic=mnemonic)
        out.append(instr)

        # Track forward branch targets so we don't stop a fall-through walker
        # before reaching code that's only reached via conditional jump.
        if op in (0x18, 0x20, 0x28, 0x30, 0x38):  # JR family
            e8 = operand[0] if operand[0] < 0x80 else operand[0] - 0x100
            target = pc + 2 + e8
            if target > pc and target < boundary:
                forward_targets.add(target)
        elif op in (0xC2, 0xC3, 0xCA, 0xD2, 0xDA):  # JP cc/JP nn
            target = operand[0] | (operand[1] << 8)
            if target > pc and target < boundary:
                forward_targets.add(target)

        next_pc = pc + length
        if op in TERMINATORS_UNCOND:
            # If no forward target lies past our current PC, we're done.
            if not any(t > next_pc for t in forward_targets):
                break

        pc = next_pc

    return out
