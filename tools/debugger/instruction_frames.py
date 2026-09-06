"""Decode instruction frames shared by taint and effect reports."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tools.damage_debugger.disasm import Instruction, opcode_length, render_mnemonic
from .address import parse_address_spec


REGISTER_FIELDS = ("A", "F", "B", "C", "D", "E", "H", "L", "HL", "SP")


@dataclass(frozen=True)
class InstructionFrame:
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
    H: int = 0
    L: int = 0
    HL: int = 0
    SP: int = 0
    memory: tuple[tuple[int, int], ...] = ()
    bank_state: tuple[tuple[str, int], ...] = ()
    bank_state_sources: tuple[tuple[str, str], ...] = ()
    known_registers: tuple[str, ...] = ()


def parse_instruction_record(record: dict[str, Any], *, default_seq: int) -> dict[str, Any]:
    try:
        seq = parse_int(record.get("seq", record.get("index", default_seq)))
        bank = parse_int(record.get("bank", record.get("pc_bank", 0)))
        pc = parse_int(record.get("pc", 0))
        opcode = parse_int(record.get("opcode", record.get("op", "")))
    except ValueError as exc:
        return {"error": str(exc), "instruction": None, "frame": None}
    if opcode < 0 or opcode > 0xFF:
        return {"error": f"opcode out of byte range: {opcode}", "instruction": None, "frame": None}
    operand = parse_operand(record.get("operand", record.get("operands", record.get("operand_bytes", []))))
    if operand is None:
        return {"error": "operand must be a byte list or hex string", "instruction": None, "frame": None}
    length = opcode_length(opcode)
    if len(operand) != length - 1:
        return {"error": f"opcode {opcode:02X} requires {length - 1} operand bytes, got {len(operand)}", "instruction": None, "frame": None}
    mnemonic = str(record.get("mnemonic") or render_mnemonic(opcode, operand))
    try:
        registers = parse_registers(record)
    except ValueError as exc:
        return {"error": str(exc), "instruction": None, "frame": None}
    pc_label = str(record.get("pc_label") or record.get("label") or f"${bank:02X}:{pc:04X}")
    instruction = Instruction(
        bank=bank,
        pc=pc,
        opcode=opcode,
        operand=operand,
        length=length,
        mnemonic=mnemonic,
    )
    frame = InstructionFrame(
        seq=seq,
        bank=bank,
        pc=pc,
        pc_label=pc_label,
        A=registers["A"],
        F=registers["F"],
        B=registers["B"],
        C=registers["C"],
        D=registers["D"],
        E=registers["E"],
        H=registers["H"],
        L=registers["L"],
        HL=registers["HL"],
        SP=registers["SP"],
        memory=parse_raw_watch_memory(record),
        bank_state=parse_bank_state(record),
        bank_state_sources=parse_bank_state_sources(record),
        known_registers=parse_known_registers(record),
    )
    return {
        "error": "",
        "instruction": instruction,
        "frame": frame,
        "bank_state_record_conflicts": bank_state_record_conflicts(
            record, seq=seq, bank=bank, pc=pc, pc_label=pc_label
        ),
    }


def trace_records(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("instructions", "frames", "events", "trace", "records"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if "opcode" in data and "pc" in data:
            return [data]
    return []


def parse_registers(record: dict[str, Any]) -> dict[str, int]:
    nested = record.get("regs") if isinstance(record.get("regs"), dict) else {}
    nested_registers = record.get("registers") if isinstance(record.get("registers"), dict) else {}
    merged = {**nested, **nested_registers, **record}
    out = {}
    for name in REGISTER_FIELDS:
        try:
            out[name] = parse_int(register_value(merged, name), default=0)
        except ValueError as exc:
            raise ValueError(f"invalid register {name}: {exc}") from exc
    if not out["HL"]:
        out["HL"] = ((out["H"] & 0xFF) << 8) | (out["L"] & 0xFF)
    if not out["H"] and out["HL"]:
        out["H"] = (out["HL"] >> 8) & 0xFF
    if not out["L"] and out["HL"]:
        out["L"] = out["HL"] & 0xFF
    return out


def register_value(data: dict[str, Any], name: str) -> Any:
    for key in (name, name.lower(), f"register_{name.lower()}"):
        if key in data:
            return data[key]
    return 0


def parse_operand(value: Any) -> bytes | None:
    if value is None or value == "":
        return b""
    if isinstance(value, bytes):
        return value
    if isinstance(value, int):
        return bytes([value & 0xFF])
    if isinstance(value, list | tuple):
        try:
            return bytes(parse_int(item) & 0xFF for item in value)
        except ValueError:
            return None
    if isinstance(value, str):
        text = value.strip().replace("$", "").replace("0x", "").replace("0X", "")
        text = text.replace(",", " ").replace("[", "").replace("]", "")
        parts = [part for part in text.split() if part]
        if len(parts) > 1:
            try:
                return bytes(int(part, 16) for part in parts)
            except ValueError:
                return None
        if len(text) % 2:
            text = "0" + text
        try:
            return bytes(int(text[index : index + 2], 16) for index in range(0, len(text), 2))
        except ValueError:
            return None
    return None


def parse_int(value: Any, *, default: int | None = None) -> int:
    if value is None or value == "":
        if default is not None:
            return default
        raise ValueError("missing integer value")
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if text.startswith("$"):
        return int(text[1:], 16)
    if text.startswith(("0x", "0X")):
        return int(text, 16)
    if any(char in "ABCDEFabcdef" for char in text):
        return int(text, 16)
    return int(text, 10)


def dict_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list | tuple):
        return [item for item in value if isinstance(item, dict)]
    return []


def parse_known_registers(record: dict[str, Any]) -> tuple[str, ...]:
    nested = record.get("regs") if isinstance(record.get("regs"), dict) else {}
    nested_registers = record.get("registers") if isinstance(record.get("registers"), dict) else {}
    sources = (nested, nested_registers, record)
    known: set[str] = set()
    for name in REGISTER_FIELDS:
        for source in sources:
            if register_is_present(source, name):
                known.add(name)
                break
    return tuple(sorted(known))


def register_is_present(data: dict[str, Any], name: str) -> bool:
    return any(key in data for key in (name, name.lower(), f"register_{name.lower()}"))


def parse_raw_watch_memory(record: dict[str, Any]) -> tuple[tuple[int, int], ...]:
    out: dict[int, int] = {}
    parse_watch_value_specs_memory(record, out=out)
    values = record.get("watch_values")
    if not isinstance(values, dict):
        return tuple(sorted(out.items()))
    for raw_key, raw_value in values.items():
        try:
            spec = parse_address_spec(raw_key)
        except ValueError:
            continue
        if spec.bank is not None:
            continue
        bytes_value = parse_hex_byte_string(raw_value)
        if not bytes_value:
            continue
        for offset, byte in enumerate(bytes_value):
            out[(spec.address + offset) & 0xFFFF] = byte
    return tuple(sorted(out.items()))


def parse_watch_value_specs_memory(record: dict[str, Any], *, out: dict[int, int]) -> None:
    values = record.get("watch_values") if isinstance(record.get("watch_values"), dict) else {}
    for item in dict_items(record.get("watch_value_specs")):
        bank = watch_value_spec_bank(item)
        try:
            address = parse_int(item.get("address"))
        except ValueError:
            continue
        if not watch_value_spec_observed_on_bus(record, address=address, bank=bank):
            continue
        value = item.get("value_hex") or values.get(str(item.get("name", "")))
        bytes_value = parse_hex_byte_string(value)
        if not bytes_value:
            continue
        for offset, byte in enumerate(bytes_value):
            out[(address + offset) & 0xFFFF] = byte


def watch_value_spec_observed_on_bus(record: dict[str, Any], *, address: int, bank: int | None) -> bool:
    if bank is None:
        return True
    address &= 0xFFFF
    state = bank_state_mapping(record)
    if 0xD000 <= address <= 0xDFFF:
        return bank_state_value(state, "wram") == bank
    if 0x8000 <= address <= 0x9FFF:
        return bank_state_value(state, "vram") == bank
    if 0x4000 <= address <= 0x7FFF:
        return bank_state_value(state, "rom") == bank
    if 0xA000 <= address <= 0xBFFF:
        enabled = bank_state_value(state, "sram_enabled")
        return enabled != 0 and bank_state_value(state, "sram") == bank
    return bank == 0


def bank_state_value(state: dict[str, Any], key: str) -> int | None:
    value = state.get(key)
    if value in {None, ""}:
        return None
    try:
        return parse_int(value)
    except ValueError:
        return None


def watch_value_spec_bank(item: dict[str, Any]) -> int | None:
    value = item.get("bank")
    if value in {None, ""}:
        return None
    try:
        return parse_int(value)
    except ValueError:
        return None


def parse_hex_byte_string(value: Any) -> tuple[int, ...]:
    text = str(value).strip().replace(" ", "").replace("_", "")
    if text.startswith(("0x", "0X")):
        text = text[2:]
    if not text or len(text) % 2:
        return ()
    try:
        return tuple(int(text[index : index + 2], 16) for index in range(0, len(text), 2))
    except ValueError:
        return ()


def parse_bank_state(record: dict[str, Any]) -> tuple[tuple[str, int], ...]:
    state = bank_state_mapping(record)
    out: dict[str, int] = {}
    for key in ("wram", "wram_raw", "vram", "vram_raw", "rom", "loaded_rom", "sram", "sram_enabled"):
        value = state.get(key, record.get(f"{key}_bank"))
        if value in {None, ""}:
            continue
        try:
            out[key] = normalize_bank_state_value(key, parse_int(value))
        except ValueError:
            continue
    if "wram" not in out and "wram_raw" in out:
        out["wram"] = normalize_bank_state_value("wram", out["wram_raw"])
    if "vram" not in out and "vram_raw" in out:
        out["vram"] = normalize_bank_state_value("vram", out["vram_raw"])
    return tuple(sorted(out.items()))


def bank_state_mapping(record: dict[str, Any]) -> dict[str, Any]:
    out = dict(record.get("bank_state")) if isinstance(record.get("bank_state"), dict) else {}
    for item in dict_items(record.get("bank_state_records")):
        name = str(item.get("name") or "")
        if not name or name.endswith("_inferred") or name in out:
            continue
        value = parsed_bank_state_record_value(item.get("value"), value_hex=item.get("value_hex"))
        if value is None:
            continue
        out[name] = value
    return out


def bank_state_record_conflicts(
    record: dict[str, Any],
    *,
    seq: int,
    bank: int,
    pc: int,
    pc_label: str,
) -> list[dict[str, Any]]:
    legacy = record.get("bank_state")
    if not isinstance(legacy, dict):
        return []
    conflicts: list[dict[str, Any]] = []
    for item in dict_items(record.get("bank_state_records")):
        name = str(item.get("name") or "")
        if not name or name.endswith("_inferred") or name not in legacy:
            continue
        legacy_value = parsed_bank_state_record_value(legacy.get(name))
        typed_value = parsed_bank_state_record_value(item.get("value"), value_hex=item.get("value_hex"))
        if legacy_value is None or typed_value is None:
            continue
        legacy_value = normalize_bank_state_value(name, legacy_value)
        typed_value = normalize_bank_state_value(name, typed_value)
        if legacy_value == typed_value:
            continue
        conflicts.append(
            {
                "key": name,
                "legacy_value": legacy_value,
                "typed_value": typed_value,
                "typed_source": str(item.get("source") or ""),
                "typed_state_kind": str(item.get("state_kind") or ""),
                "conflict_kind": "value_mismatch",
                "frame_pc": f"{bank & 0xFF:02X}:{pc & 0xFFFF:04X}",
                "seq": seq,
                "pc_label": pc_label,
                "proof_action": "preferred_legacy_for_backward_compat",
            }
        )
    return conflicts


def parsed_bank_state_record_value(value: Any, *, value_hex: Any = None) -> int | None:
    raw = value
    if (raw is None or raw == "") and value_hex is not None and value_hex != "":
        raw = f"0x{value_hex}"
    if raw is None or raw == "":
        return None
    try:
        return parse_int(raw)
    except ValueError:
        return None


def parse_bank_state_sources(record: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    out: dict[str, str] = {}
    raw_sources = record.get("bank_state_sources")
    if isinstance(raw_sources, dict):
        out.update({str(key): str(value) for key, value in raw_sources.items() if str(value)})
    for item in dict_items(record.get("bank_state_records")):
        name = str(item.get("name") or "")
        source = str(item.get("source") or "")
        if name and source and name not in out:
            out[name] = source
    return tuple(sorted(out.items()))


def normalize_bank_state_value(key: str, value: int) -> int:
    value &= 0xFF
    if key == "wram":
        bank = value & 0x07
        return bank if bank else 1
    if key == "vram":
        return value & 0x01
    if key == "rom":
        bank = value & 0x7F
        return bank if bank else 1
    return value


def frame_register_known(frame: InstructionFrame, register: str) -> bool:
    known = set(frame.known_registers)
    register = register.upper()
    if register in known:
        return True
    if register in {"H", "L"} and "HL" in known:
        return True
    return False


def condition_true(condition: str, flags: int) -> bool:
    zero = bool(flags & 0x80)
    carry = bool(flags & 0x10)
    return {
        "nz": not zero,
        "z": zero,
        "nc": not carry,
        "c": carry,
    }[condition]


def frame_condition_true(frame: InstructionFrame, condition: str) -> bool:
    flags = frame_flags(frame)
    return flags is not None and condition_true(condition, flags)


def frame_flags(frame: InstructionFrame) -> int | None:
    if not frame_register_known(frame, "F"):
        return None
    return int(frame.F) & 0xFF
