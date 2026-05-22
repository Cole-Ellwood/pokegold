from __future__ import annotations

from dataclasses import dataclass


SM83_MODEL_SOURCE = "tools.debugger.sm83_model"


@dataclass(frozen=True)
class HliHldSemantics:
    opcode: int
    memory_operation: str
    hl_writeback_operation: str
    hl_delta: int

    def updated_hl(self, value: int | None) -> int | None:
        if value is None:
            return None
        return (int(value) + self.hl_delta) & 0xFFFF


@dataclass(frozen=True)
class StackControlSemantics:
    opcode: int
    stack_write_operation: str = ""
    stack_read_operation: str = ""
    register_write_operation: str = ""
    sp_write_operation: str = ""
    sp_delta: int = 0
    control_operation: str = ""
    register_pair: str = ""
    rst_target: int | None = None

    def updated_sp(self, value: int | None) -> int | None:
        if value is None:
            return None
        return (int(value) + self.sp_delta) & 0xFFFF


@dataclass(frozen=True)
class AluSemantics:
    opcode: int
    group: int
    name: str

    def operation(self, source_label: str) -> str:
        return f"{self.name} a, {source_label}"

    def result(self, *, a: int | None, source: int | None, flags: int | None) -> int | None:
        if self.group == 4 and source == 0:
            return 0
        if self.group == 5 and a is not None and source is not None:
            return (a ^ source) & 0xFF
        if self.group == 5 and source == 0:
            return a
        if a is None or source is None:
            return None
        if self.group == 0:
            return (a + source) & 0xFF
        if self.group == 1:
            if flags is None:
                return None
            return (a + source + (1 if flags & 0x10 else 0)) & 0xFF
        if self.group == 2:
            return (a - source) & 0xFF
        if self.group == 3:
            if flags is None:
                return None
            return (a - source - (1 if flags & 0x10 else 0)) & 0xFF
        if self.group == 4:
            return (a & source) & 0xFF
        if self.group == 6:
            return (a | source) & 0xFF
        return None

    def flags(self, *, a: int | None, source: int | None, flags: int | None) -> int | None:
        if a is None or source is None:
            return None
        carry = 0
        if self.group in {1, 3}:
            if flags is None:
                return None
            carry = 1 if flags & 0x10 else 0
        if self.group == 0:
            total = a + source
            result = total & 0xFF
            half = ((a & 0x0F) + (source & 0x0F)) > 0x0F
            full = total > 0xFF
            return flag_byte(zero=result == 0, half=half, carry=full)
        if self.group == 1:
            total = a + source + carry
            result = total & 0xFF
            half = ((a & 0x0F) + (source & 0x0F) + carry) > 0x0F
            full = total > 0xFF
            return flag_byte(zero=result == 0, half=half, carry=full)
        if self.group == 2:
            result = (a - source) & 0xFF
            half = (a & 0x0F) < (source & 0x0F)
            full = a < source
            return flag_byte(zero=result == 0, subtract=True, half=half, carry=full)
        if self.group in {3, 7}:
            total_source = source + carry
            result = (a - total_source) & 0xFF
            half = (a & 0x0F) < ((source & 0x0F) + carry)
            full = a < total_source
            return flag_byte(zero=result == 0, subtract=True, half=half, carry=full)
        if self.group == 4:
            result = a & source
            return flag_byte(zero=result == 0, half=True)
        if self.group == 5:
            result = a ^ source
            return flag_byte(zero=result == 0)
        if self.group == 6:
            result = a | source
            return flag_byte(zero=result == 0)
        return None


@dataclass(frozen=True)
class CbSemantics:
    subopcode: int
    group: int
    bit: int
    target: str

    @property
    def is_memory_target(self) -> bool:
        return self.target == "[hl]"

    @property
    def writes_value(self) -> bool:
        return self.group in {0, 2, 3}

    @property
    def writes_flags(self) -> bool:
        return self.group in {0, 1}

    @property
    def reads_carry_for_result(self) -> bool:
        return self.group == 0 and self.bit in {2, 3}

    @property
    def reads_carry_for_flags(self) -> bool:
        return self.group == 1 or self.reads_carry_for_result

    def operation(self, target: str | None = None) -> str:
        target = target or self.target
        if self.group == 0:
            return f"{CB_ROTATE_NAMES[self.bit]} {target}"
        if self.group == 1:
            return f"bit {self.bit}, {target}"
        if self.group == 2:
            return f"res {self.bit}, {target}"
        return f"set {self.bit}, {target}"

    def result(self, old_value: int | None, *, flags: int | None) -> int | None:
        if old_value is None:
            return None
        value = old_value & 0xFF
        if self.group == 0:
            if self.bit == 0:
                return ((value << 1) | (value >> 7)) & 0xFF
            if self.bit == 1:
                return ((value >> 1) | ((value & 0x01) << 7)) & 0xFF
            if self.bit == 2:
                if flags is None:
                    return None
                carry = 1 if flags & 0x10 else 0
                return ((value << 1) | carry) & 0xFF
            if self.bit == 3:
                if flags is None:
                    return None
                carry = 1 if flags & 0x10 else 0
                return ((carry << 7) | (value >> 1)) & 0xFF
            if self.bit == 4:
                return (value << 1) & 0xFF
            if self.bit == 5:
                return (value & 0x80) | (value >> 1)
            if self.bit == 6:
                return ((value << 4) | (value >> 4)) & 0xFF
            return value >> 1
        if self.group == 2:
            return value & ~(1 << self.bit) & 0xFF
        if self.group == 3:
            return value | (1 << self.bit)
        return None

    def flags(self, old_value: int | None, *, flags: int | None) -> int | None:
        if old_value is None:
            return None
        value = old_value & 0xFF
        if self.group == 0:
            result = self.result(old_value, flags=flags)
            if result is None:
                return None
            if self.bit in {0, 2, 4}:
                carry = bool(value & 0x80)
            elif self.bit in {1, 3, 5, 7}:
                carry = bool(value & 0x01)
            else:
                carry = False
            return flag_byte(zero=(result & 0xFF) == 0, carry=carry)
        if self.group == 1:
            if flags is None:
                return None
            return flag_byte(zero=not bool(value & (1 << self.bit)), half=True, carry=bool(flags & 0x10))
        return None


@dataclass(frozen=True)
class CpuStateSemantics:
    opcode: int
    kind: str
    operation: str
    category: str
    mode: str = ""


@dataclass(frozen=True)
class InterruptEntrySemantics:
    vector: int
    name: str
    operation: str
    sp_write_operation: str = "interrupt entry updates sp"
    stack_low_operation: str = "interrupt return low"
    stack_high_operation: str = "interrupt return high"
    sp_delta: int = -2

    def updated_sp(self, value: int | None) -> int | None:
        if value is None:
            return None
        return (int(value) + self.sp_delta) & 0xFFFF

    def return_address(self, pc: int, instruction_length: int) -> int:
        return (int(pc) + int(instruction_length)) & 0xFFFF

    def stack_value(self, return_address: int, operation: str) -> int:
        if operation == self.stack_high_operation:
            return (int(return_address) >> 8) & 0xFF
        return int(return_address) & 0xFF


@dataclass(frozen=True)
class HardwareTriggerSemantics:
    kind: str
    operation: str
    category: str
    register: str = ""
    hardware_model: str = ""


@dataclass(frozen=True)
class TimerOverflowSemantics:
    side_effect_kind: str = "timer_tima_overflow"
    reload_write_kind: str = "timer_tima_reload_write"
    interrupt_write_kind: str = "timer_interrupt_request_write"
    operation: str = "TIMA overflow reloads TMA and requests timer interrupt"
    reload_operation: str = "TIMA reload from TMA after overflow"
    interrupt_operation: str = "timer interrupt request sets IF bit 2"
    interrupt_bit: int = 2
    hardware_model: str = "timer_tima_overflow"

    @property
    def interrupt_mask(self) -> int:
        return 1 << self.interrupt_bit

    def observed_reload_and_interrupt(
        self,
        *,
        current_tima: int,
        current_tma: int,
        next_tima: int,
        current_if: int,
        next_if: int,
    ) -> bool:
        return (
            (int(current_tima) & 0xFF) == 0xFF
            and (int(next_tima) & 0xFF) == (int(current_tma) & 0xFF)
            and not (int(current_if) & self.interrupt_mask)
            and bool(int(next_if) & self.interrupt_mask)
        )


@dataclass(frozen=True)
class LoadSemantics:
    opcode: int
    target: str
    source: str
    target_kind: str
    source_kind: str
    width: int
    address_source: str = ""

    @property
    def operation(self) -> str:
        if self.opcode in {0xE0, 0xE2, 0xF0, 0xF2}:
            return f"ldh {self.target}, {self.source}"
        return f"ld {self.target}, {self.source}"

    @property
    def register_target(self) -> str:
        if self.target_kind != "register":
            return ""
        return self.target.upper()

    @property
    def register_source(self) -> str:
        if self.source_kind != "register":
            return ""
        return self.source

    @property
    def is_memory_read(self) -> bool:
        return self.target_kind == "register" and self.source_kind == "memory"

    @property
    def is_memory_write(self) -> bool:
        return self.target_kind == "memory"


@dataclass(frozen=True)
class IncDecSemantics:
    opcode: int
    target: str
    delta: int

    @property
    def is_memory_target(self) -> bool:
        return self.target == "[hl]"

    @property
    def register_target(self) -> str:
        return "" if self.is_memory_target else self.target.upper()

    @property
    def operation(self) -> str:
        prefix = "inc" if self.delta > 0 else "dec"
        return f"{prefix} {self.target}"

    @property
    def flag_operation(self) -> str:
        return f"{self.operation} flags"

    def result(self, old_value: int | None) -> int | None:
        if old_value is None:
            return None
        return (int(old_value) + self.delta) & 0xFF

    def flags(self, *, old_value: int | None, flags: int | None) -> int | None:
        if old_value is None or flags is None:
            return None
        old_value = int(old_value) & 0xFF
        if self.delta > 0:
            result = (old_value + 1) & 0xFF
            half = (old_value & 0x0F) == 0x0F
            return flag_byte(zero=result == 0, half=half, carry=bool(int(flags) & 0x10))
        result = (old_value - 1) & 0xFF
        half = (old_value & 0x0F) == 0x00
        return flag_byte(zero=result == 0, subtract=True, half=half, carry=bool(int(flags) & 0x10))


@dataclass(frozen=True)
class RegisterPairIncDecSemantics:
    opcode: int
    register_pair: str
    delta: int

    @property
    def operation(self) -> str:
        prefix = "inc" if self.delta > 0 else "dec"
        return f"{prefix} {self.register_pair}"

    def updated_value(self, value: int | None) -> int | None:
        if value is None:
            return None
        return (int(value) + self.delta) & 0xFFFF


@dataclass(frozen=True)
class AddHlSemantics:
    opcode: int
    source_pair: str

    @property
    def operation(self) -> str:
        return f"add hl, {self.source_pair}"

    @property
    def flag_operation(self) -> str:
        return f"{self.operation} flags"

    def result(self, *, hl: int | None, source: int | None) -> int | None:
        if hl is None or source is None:
            return None
        return (int(hl) + int(source)) & 0xFFFF

    def flags(self, *, hl: int | None, source: int | None, flags: int | None) -> int | None:
        if hl is None or source is None or flags is None:
            return None
        total = int(hl) + int(source)
        half = ((int(hl) & 0x0FFF) + (int(source) & 0x0FFF)) > 0x0FFF
        carry = total > 0xFFFF
        return flag_byte(zero=bool(int(flags) & 0x80), half=half, carry=carry)


@dataclass(frozen=True)
class SpRelativeSemantics:
    opcode: int
    target_register: str
    operation: str

    @property
    def flag_operation(self) -> str:
        return f"{self.operation} flags"

    def result(self, *, sp: int | None, raw_offset: int) -> int | None:
        if sp is None:
            return None
        return (int(sp) + signed8(raw_offset)) & 0xFFFF

    def flags(self, *, sp: int | None, raw_offset: int) -> int | None:
        if sp is None:
            return None
        offset = int(raw_offset) & 0xFF
        half = ((int(sp) & 0x0F) + (offset & 0x0F)) > 0x0F
        carry = ((int(sp) & 0xFF) + offset) > 0xFF
        return flag_byte(half=half, carry=carry)


@dataclass(frozen=True)
class AccumulatorFlagSemantics:
    opcode: int
    operation: str
    flag_operation: str
    writes_accumulator: bool
    reads_flags_for_result: bool = False

    def result(self, *, a: int | None, flags: int | None) -> int | None:
        if not self.writes_accumulator or a is None:
            return None
        value = int(a) & 0xFF
        if self.opcode == 0x07:
            return ((value << 1) | (value >> 7)) & 0xFF
        if self.opcode == 0x0F:
            return ((value >> 1) | ((value & 0x01) << 7)) & 0xFF
        if self.opcode in {0x17, 0x1F}:
            if flags is None:
                return None
            carry = 1 if int(flags) & 0x10 else 0
            if self.opcode == 0x17:
                return ((value << 1) | carry) & 0xFF
            return ((carry << 7) | (value >> 1)) & 0xFF
        if self.opcode == 0x27:
            result, _flags = daa_result(a=a, flags=flags)
            return result
        if self.opcode == 0x2F:
            return (~value) & 0xFF
        return None

    def flags(self, *, a: int | None, flags: int | None) -> int | None:
        if self.opcode in {0x07, 0x0F, 0x17, 0x1F}:
            if a is None:
                return None
            value = int(a) & 0xFF
            if self.opcode in {0x07, 0x17}:
                return 0x10 if value & 0x80 else 0
            return 0x10 if value & 0x01 else 0
        if self.opcode == 0x27:
            _result, new_flags = daa_result(a=a, flags=flags)
            return new_flags
        if flags is None:
            return None
        if self.opcode == 0x2F:
            return ((int(flags) & 0x90) | 0x60) & 0xF0
        if self.opcode == 0x37:
            return (int(flags) & 0x80) | 0x10
        if self.opcode == 0x3F:
            return (int(flags) & 0x80) | (0 if int(flags) & 0x10 else 0x10)
        return None


HLI_HLD_SEMANTICS = {
    0x22: HliHldSemantics(
        opcode=0x22,
        memory_operation="ld [hli], a",
        hl_writeback_operation="ld [hli], a updates hl",
        hl_delta=1,
    ),
    0x2A: HliHldSemantics(
        opcode=0x2A,
        memory_operation="ld a, [hli]",
        hl_writeback_operation="ld a, [hli] updates hl",
        hl_delta=1,
    ),
    0x32: HliHldSemantics(
        opcode=0x32,
        memory_operation="ld [hld], a",
        hl_writeback_operation="ld [hld], a updates hl",
        hl_delta=-1,
    ),
    0x3A: HliHldSemantics(
        opcode=0x3A,
        memory_operation="ld a, [hld]",
        hl_writeback_operation="ld a, [hld] updates hl",
        hl_delta=-1,
    ),
}


PUSH_PAIRS = {
    0xC5: "bc",
    0xD5: "de",
    0xE5: "hl",
    0xF5: "af",
}
POP_PAIRS = {
    0xC1: "bc",
    0xD1: "de",
    0xE1: "hl",
    0xF1: "af",
}
CALL_OPCODES = {0xCD, 0xC4, 0xCC, 0xD4, 0xDC}
RET_OPCODES = {0xC9, 0xD9, 0xC0, 0xC8, 0xD0, 0xD8}
RST_TARGETS = {
    0xC7: 0x00,
    0xCF: 0x08,
    0xD7: 0x10,
    0xDF: 0x18,
    0xE7: 0x20,
    0xEF: 0x28,
    0xF7: 0x30,
    0xFF: 0x38,
}
CONDITIONAL_CALLS = {0xC4: "nz", 0xCC: "z", 0xD4: "nc", 0xDC: "c"}
CONDITIONAL_RETS = {0xC0: "nz", 0xC8: "z", 0xD0: "nc", 0xD8: "c"}
CONDITIONAL_JUMPS = {
    0x20: "nz",
    0x28: "z",
    0x30: "nc",
    0x38: "c",
    0xC2: "nz",
    0xCA: "z",
    0xD2: "nc",
    0xDA: "c",
}

ALU_GROUP_NAMES = {
    0: "add",
    1: "adc",
    2: "sub",
    3: "sbc",
    4: "and",
    5: "xor",
    6: "or",
    7: "cp",
}

IMMEDIATE_ALU_GROUPS = {
    0xC6: 0,
    0xCE: 1,
    0xD6: 2,
    0xDE: 3,
    0xE6: 4,
    0xEE: 5,
    0xF6: 6,
    0xFE: 7,
}

CB_ROTATE_NAMES = ("rlc", "rrc", "rl", "rr", "sla", "sra", "swap", "srl")
CB_TARGETS = ("b", "c", "d", "e", "h", "l", "[hl]", "a")
REGISTER_INDEX_TARGETS = {index: target for index, target in enumerate(CB_TARGETS)}
LOAD_TARGETS = CB_TARGETS
IMMEDIATE_8_LOAD_TARGETS = {
    0x06: "b",
    0x0E: "c",
    0x16: "d",
    0x1E: "e",
    0x26: "h",
    0x2E: "l",
    0x3E: "a",
}
IMMEDIATE_16_LOAD_TARGETS = {
    0x01: "bc",
    0x11: "de",
    0x21: "hl",
    0x31: "sp",
}
INC_DEC_TARGETS = {
    0x04: ("b", 1),
    0x05: ("b", -1),
    0x0C: ("c", 1),
    0x0D: ("c", -1),
    0x14: ("d", 1),
    0x15: ("d", -1),
    0x1C: ("e", 1),
    0x1D: ("e", -1),
    0x24: ("h", 1),
    0x25: ("h", -1),
    0x2C: ("l", 1),
    0x2D: ("l", -1),
    0x34: ("[hl]", 1),
    0x35: ("[hl]", -1),
    0x3C: ("a", 1),
    0x3D: ("a", -1),
}
DIRECT_LOADS = {
    0x02: ("[bc]", "a", "memory", "register", 1, "bc"),
    0x08: ("[nn]", "sp", "memory", "register", 2, "nn"),
    0x0A: ("a", "[bc]", "register", "memory", 1, "bc"),
    0x12: ("[de]", "a", "memory", "register", 1, "de"),
    0x1A: ("a", "[de]", "register", "memory", 1, "de"),
    0x36: ("[hl]", "n", "memory", "immediate", 1, "hl"),
    0xE0: ("[n]", "a", "memory", "register", 1, "n"),
    0xE2: ("[c]", "a", "memory", "register", 1, "c"),
    0xEA: ("[nn]", "a", "memory", "register", 1, "nn"),
    0xF0: ("a", "[n]", "register", "memory", 1, "n"),
    0xF2: ("a", "[c]", "register", "memory", 1, "c"),
    0xF9: ("sp", "hl", "register", "register", 2, ""),
    0xFA: ("a", "[nn]", "register", "memory", 1, "nn"),
}
REGISTER_PAIR_INC_DEC = {
    0x03: ("bc", 1),
    0x0B: ("bc", -1),
    0x13: ("de", 1),
    0x1B: ("de", -1),
    0x23: ("hl", 1),
    0x2B: ("hl", -1),
    0x33: ("sp", 1),
    0x3B: ("sp", -1),
}
ADD_HL_SOURCES = {
    0x09: "bc",
    0x19: "de",
    0x29: "hl",
    0x39: "sp",
}
SP_RELATIVE = {
    0xE8: ("SP", "add sp, e8"),
    0xF8: ("HL", "ld hl, sp+n"),
}
ACCUMULATOR_FLAG_OPS = {
    0x07: ("rlca", "rlca flags", True, False),
    0x0F: ("rrca", "rrca flags", True, False),
    0x17: ("rla", "rla flags", True, True),
    0x1F: ("rra", "rra flags", True, True),
    0x27: ("daa", "daa flags", True, True),
    0x2F: ("cpl", "cpl flags", True, False),
    0x37: ("scf", "scf flags", False, False),
    0x3F: ("ccf", "ccf flags", False, False),
}
CPU_STATE_SEMANTICS = {
    0x76: CpuStateSemantics(opcode=0x76, kind="cpu_state", operation="halt", category="cpu", mode="halted"),
    0x10: CpuStateSemantics(opcode=0x10, kind="cpu_state", operation="stop", category="cpu", mode="stopped"),
    0xFB: CpuStateSemantics(opcode=0xFB, kind="ime", operation="ei", category="interrupt"),
    0xF3: CpuStateSemantics(opcode=0xF3, kind="ime", operation="di", category="interrupt"),
    0xD9: CpuStateSemantics(opcode=0xD9, kind="ime", operation="reti", category="interrupt"),
}
CPU_STATE_OPCODES = frozenset(CPU_STATE_SEMANTICS)
INTERRUPT_VECTORS = {
    0x40: "vblank",
    0x48: "lcd_stat",
    0x50: "timer",
    0x58: "serial",
    0x60: "joypad",
}
PPU_IO_RANGES = ((0xFF40, 0xFF4B), (0xFF68, 0xFF6B))
AUDIO_IO_RANGE = (0xFF10, 0xFF3F)
TIMER_IO_RANGE = (0xFF04, 0xFF07)
TIMER_TIMA_ADDRESS = 0xFF05
TIMER_TMA_ADDRESS = 0xFF06
TIMER_TAC_ADDRESS = 0xFF07
INTERRUPT_FLAG_ADDRESS = 0xFF0F
CGB_VRAM_DMA_RANGE = (0xFF51, 0xFF55)
CGB_VRAM_DMA_REGISTERS = {
    0xFF51: "rVDMA_SRC_HIGH",
    0xFF52: "rVDMA_SRC_LOW",
    0xFF53: "rVDMA_DEST_HIGH",
    0xFF54: "rVDMA_DEST_LOW",
    0xFF55: "rVDMA_LEN",
}


def hli_hld_semantics(opcode: int) -> HliHldSemantics:
    try:
        return HLI_HLD_SEMANTICS[int(opcode) & 0xFF]
    except KeyError as exc:
        raise ValueError(f"opcode is not an HLI/HLD instruction: 0x{int(opcode) & 0xFF:02X}") from exc


def stack_control_semantics(opcode: int) -> StackControlSemantics:
    opcode = int(opcode) & 0xFF
    if opcode in PUSH_PAIRS:
        pair = PUSH_PAIRS[opcode]
        return StackControlSemantics(
            opcode=opcode,
            stack_write_operation=f"push {pair}",
            sp_write_operation=f"push {pair} updates sp",
            sp_delta=-2,
            register_pair=pair,
        )
    if opcode in POP_PAIRS:
        pair = POP_PAIRS[opcode]
        return StackControlSemantics(
            opcode=opcode,
            stack_read_operation="pop",
            register_write_operation=f"pop {pair}",
            sp_write_operation=f"pop {pair} updates sp",
            sp_delta=2,
            register_pair=pair,
        )
    if opcode in CALL_OPCODES:
        return StackControlSemantics(
            opcode=opcode,
            stack_write_operation="call return",
            sp_write_operation="call updates sp",
            sp_delta=-2,
            control_operation="call",
        )
    if opcode in RET_OPCODES:
        return StackControlSemantics(
            opcode=opcode,
            stack_read_operation="ret",
            sp_write_operation="ret updates sp",
            sp_delta=2,
            control_operation="return",
        )
    if opcode in RST_TARGETS:
        return StackControlSemantics(
            opcode=opcode,
            stack_write_operation="rst return",
            sp_write_operation="rst updates sp",
            sp_delta=-2,
            control_operation="rst",
            rst_target=RST_TARGETS[opcode],
        )
    raise ValueError(f"opcode is not a modeled stack/control instruction: 0x{opcode:02X}")


def stack_pop_register_value(register_pair: str, low: int | None, high: int | None) -> int | None:
    if low is None or high is None:
        return None
    value = (((int(high) & 0xFF) << 8) | (int(low) & 0xFF)) & 0xFFFF
    if register_pair.lower() == "af":
        return value & 0xFFF0
    return value


def stack_pop_component_value(register_pair: str, component: str, value: int | None) -> int | None:
    if value is None:
        return None
    out = int(value) & 0xFF
    if register_pair.lower() == "af" and component.lower() == "f":
        return out & 0xF0
    return out


def alu_semantics(opcode: int) -> AluSemantics:
    opcode = int(opcode) & 0xFF
    if 0x80 <= opcode <= 0xBF:
        group = (opcode >> 3) & 0x07
        return AluSemantics(opcode=opcode, group=group, name=ALU_GROUP_NAMES[group])
    if opcode in IMMEDIATE_ALU_GROUPS:
        group = IMMEDIATE_ALU_GROUPS[opcode]
        return AluSemantics(opcode=opcode, group=group, name=ALU_GROUP_NAMES[group])
    raise ValueError(f"opcode is not a modeled ALU instruction: 0x{opcode:02X}")


def cb_semantics(subopcode: int) -> CbSemantics:
    subopcode = int(subopcode) & 0xFF
    return CbSemantics(
        subopcode=subopcode,
        group=(subopcode >> 6) & 0x03,
        bit=(subopcode >> 3) & 0x07,
        target=CB_TARGETS[subopcode & 0x07],
    )


def cpu_state_semantics(opcode: int) -> CpuStateSemantics:
    opcode = int(opcode) & 0xFF
    try:
        return CPU_STATE_SEMANTICS[opcode]
    except KeyError as exc:
        raise ValueError(f"opcode is not a modeled CPU-state instruction: 0x{opcode:02X}") from exc


def interrupt_entry_semantics(vector: int) -> InterruptEntrySemantics:
    vector = int(vector) & 0xFFFF
    try:
        name = INTERRUPT_VECTORS[vector]
    except KeyError as exc:
        raise ValueError(f"address is not an SM83 interrupt vector: 0x{vector:04X}") from exc
    return InterruptEntrySemantics(vector=vector, name=name, operation=f"{name} interrupt entry")


def timer_overflow_semantics() -> TimerOverflowSemantics:
    return TimerOverflowSemantics()


def hardware_trigger_semantics(address: int, *, write_kind: str = "io_write") -> tuple[HardwareTriggerSemantics, ...]:
    address = int(address) & 0xFFFF
    if write_kind == "memory_write" and address < 0xFF00:
        return memory_write_hardware_trigger_semantics(address)
    return io_write_hardware_trigger_semantics(address)


def io_write_hardware_trigger_semantics(address: int) -> tuple[HardwareTriggerSemantics, ...]:
    address = int(address) & 0xFFFF
    if address == 0xFF46:
        return (HardwareTriggerSemantics("oam_dma_trigger", "OAM DMA transfer trigger", "dma", hardware_model="oam_dma"),)
    if address == 0xFF4F:
        return (HardwareTriggerSemantics("vram_bank_select", "VRAM bank select write", "banking"),)
    if address == 0xFF70:
        return (HardwareTriggerSemantics("wram_bank_select", "WRAM bank select write", "banking"),)
    if address == 0xFF04:
        return (
            HardwareTriggerSemantics("timer_register_write", "timer hardware register write", "timer"),
            HardwareTriggerSemantics("timer_div_reset", "DIV reset to 00", "timer", hardware_model="timer_div_reset"),
        )
    if in_range(address, CGB_VRAM_DMA_RANGE):
        register = CGB_VRAM_DMA_REGISTERS.get(address, f"FF{address & 0xFF:02X}")
        if address == 0xFF55:
            return (
                HardwareTriggerSemantics(
                    "vram_dma_len_mode_write",
                    "VRAM DMA length/mode/start write",
                    "dma",
                    register=register,
                    hardware_model="cgb_vram_dma",
                ),
            )
        return (
            HardwareTriggerSemantics(
                "vram_dma_register_write",
                "VRAM DMA setup register write",
                "dma",
                register=register,
                hardware_model="cgb_vram_dma",
            ),
        )
    if in_range(address, AUDIO_IO_RANGE):
        return (HardwareTriggerSemantics("audio_register_write", "audio hardware register write", "audio"),)
    if in_any_range(address, PPU_IO_RANGES):
        return (HardwareTriggerSemantics("ppu_register_write", "PPU hardware register write", "ppu"),)
    if in_range(address, TIMER_IO_RANGE):
        return (HardwareTriggerSemantics("timer_register_write", "timer hardware register write", "timer"),)
    if address in {0xFF0F, 0xFFFF}:
        operation = "interrupt enable register write" if address == 0xFFFF else "interrupt register write"
        return (HardwareTriggerSemantics("interrupt_register_write", operation, "interrupt"),)
    if address in {0xFF01, 0xFF02}:
        return (HardwareTriggerSemantics("serial_register_write", "serial hardware register write", "serial"),)
    if address == 0xFF00:
        return (HardwareTriggerSemantics("joypad_register_write", "joypad selector write", "input"),)
    return ()


def memory_write_hardware_trigger_semantics(address: int) -> tuple[HardwareTriggerSemantics, ...]:
    address = int(address) & 0xFFFF
    if 0x0000 <= address <= 0x1FFF:
        return (HardwareTriggerSemantics("mbc_ram_enable_write", "MBC external RAM enable write", "banking"),)
    if 0x2000 <= address <= 0x3FFF:
        return (HardwareTriggerSemantics("mbc_rom_bank_select", "MBC ROM bank select write", "banking"),)
    if 0x4000 <= address <= 0x5FFF:
        return (
            HardwareTriggerSemantics(
                "mbc_ram_or_rom_upper_bank_select",
                "MBC RAM bank or ROM upper-bit select write",
                "banking",
            ),
        )
    if 0x6000 <= address <= 0x7FFF:
        return (HardwareTriggerSemantics("mbc_mode_or_latch_write", "MBC mode or RTC latch write", "banking"),)
    return ()


def hardware_memory_bank(bank_state: dict[str, int], address: int) -> int | None:
    address &= 0xFFFF
    if 0x4000 <= address <= 0x7FFF:
        return bank_state.get("rom")
    if 0x8000 <= address <= 0x9FFF:
        return bank_state.get("vram")
    if 0xA000 <= address <= 0xBFFF:
        return bank_state.get("sram")
    if 0xD000 <= address <= 0xDFFF:
        return bank_state.get("wram")
    return None


def hardware_memory_bank_source(address: int) -> str:
    address &= 0xFFFF
    if 0x4000 <= address <= 0x7FFF:
        return "bank_state.rom"
    if 0x8000 <= address <= 0x9FFF:
        return "bank_state.vram"
    if 0xA000 <= address <= 0xBFFF:
        return "bank_state.sram"
    if 0xD000 <= address <= 0xDFFF:
        return "bank_state.wram"
    return ""


def load_semantics(opcode: int) -> LoadSemantics:
    opcode = int(opcode) & 0xFF
    if opcode in IMMEDIATE_8_LOAD_TARGETS:
        return LoadSemantics(
            opcode=opcode,
            target=IMMEDIATE_8_LOAD_TARGETS[opcode],
            source="n",
            target_kind="register",
            source_kind="immediate",
            width=1,
        )
    if opcode in IMMEDIATE_16_LOAD_TARGETS:
        return LoadSemantics(
            opcode=opcode,
            target=IMMEDIATE_16_LOAD_TARGETS[opcode],
            source="nn",
            target_kind="register",
            source_kind="immediate",
            width=2,
        )
    if 0x40 <= opcode <= 0x7F and opcode != 0x76:
        target = LOAD_TARGETS[(opcode >> 3) & 0x07]
        source = LOAD_TARGETS[opcode & 0x07]
        return LoadSemantics(
            opcode=opcode,
            target=target,
            source=source,
            target_kind="memory" if target == "[hl]" else "register",
            source_kind="memory" if source == "[hl]" else "register",
            width=1,
            address_source="hl" if target == "[hl]" or source == "[hl]" else "",
        )
    if opcode in DIRECT_LOADS:
        target, source, target_kind, source_kind, width, address_source = DIRECT_LOADS[opcode]
        return LoadSemantics(
            opcode=opcode,
            target=target,
            source=source,
            target_kind=target_kind,
            source_kind=source_kind,
            width=width,
            address_source=address_source,
        )
    raise ValueError(f"opcode is not a modeled load instruction: 0x{opcode:02X}")


def inc_dec_semantics(opcode: int) -> IncDecSemantics:
    opcode = int(opcode) & 0xFF
    try:
        target, delta = INC_DEC_TARGETS[opcode]
    except KeyError as exc:
        raise ValueError(f"opcode is not a modeled 8-bit inc/dec instruction: 0x{opcode:02X}") from exc
    return IncDecSemantics(opcode=opcode, target=target, delta=delta)


def register_pair_inc_dec_semantics(opcode: int) -> RegisterPairIncDecSemantics:
    opcode = int(opcode) & 0xFF
    try:
        register_pair, delta = REGISTER_PAIR_INC_DEC[opcode]
    except KeyError as exc:
        raise ValueError(f"opcode is not a modeled 16-bit inc/dec instruction: 0x{opcode:02X}") from exc
    return RegisterPairIncDecSemantics(opcode=opcode, register_pair=register_pair, delta=delta)


def add_hl_semantics(opcode: int) -> AddHlSemantics:
    opcode = int(opcode) & 0xFF
    try:
        source_pair = ADD_HL_SOURCES[opcode]
    except KeyError as exc:
        raise ValueError(f"opcode is not a modeled add hl instruction: 0x{opcode:02X}") from exc
    return AddHlSemantics(opcode=opcode, source_pair=source_pair)


def sp_relative_semantics(opcode: int) -> SpRelativeSemantics:
    opcode = int(opcode) & 0xFF
    try:
        target_register, operation = SP_RELATIVE[opcode]
    except KeyError as exc:
        raise ValueError(f"opcode is not a modeled SP-relative instruction: 0x{opcode:02X}") from exc
    return SpRelativeSemantics(opcode=opcode, target_register=target_register, operation=operation)


def accumulator_flag_semantics(opcode: int) -> AccumulatorFlagSemantics:
    opcode = int(opcode) & 0xFF
    try:
        operation, flag_operation, writes_accumulator, reads_flags = ACCUMULATOR_FLAG_OPS[opcode]
    except KeyError as exc:
        raise ValueError(f"opcode is not a modeled accumulator/flag instruction: 0x{opcode:02X}") from exc
    return AccumulatorFlagSemantics(
        opcode=opcode,
        operation=operation,
        flag_operation=flag_operation,
        writes_accumulator=writes_accumulator,
        reads_flags_for_result=reads_flags,
    )


def in_range(value: int, bounds: tuple[int, int]) -> bool:
    return bounds[0] <= value <= bounds[1]


def in_any_range(value: int, ranges: tuple[tuple[int, int], ...]) -> bool:
    return any(in_range(value, bounds) for bounds in ranges)


def flag_byte(
    *,
    zero: bool = False,
    subtract: bool = False,
    half: bool = False,
    carry: bool = False,
) -> int:
    return (
        (0x80 if zero else 0)
        | (0x40 if subtract else 0)
        | (0x20 if half else 0)
        | (0x10 if carry else 0)
    )


def signed8(value: int) -> int:
    value = int(value) & 0xFF
    return value - 0x100 if value & 0x80 else value


def daa_result(*, a: int | None, flags: int | None) -> tuple[int | None, int | None]:
    if a is None or flags is None:
        return None, None
    value = int(a) & 0xFF
    subtract = bool(int(flags) & 0x40)
    half = bool(int(flags) & 0x20)
    carry = bool(int(flags) & 0x10)
    carry_out = carry
    if not subtract:
        if carry or value > 0x99:
            value = (value + 0x60) & 0xFF
            carry_out = True
        if half or (value & 0x0F) > 0x09:
            value = (value + 0x06) & 0xFF
    else:
        if carry:
            value = (value - 0x60) & 0xFF
        if half:
            value = (value - 0x06) & 0xFF
    return value, flag_byte(zero=value == 0, subtract=subtract, carry=carry_out)
