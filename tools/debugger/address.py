from __future__ import annotations

from dataclasses import dataclass
from typing import Any


BANK_QUALIFIED_SPACES = {"romx", "vram", "sram", "wramx"}


@dataclass(frozen=True)
class AddressSpec:
    raw: str
    address: int
    bank: int | None = None
    space: str = ""
    bank_semantics: str = "not_requested"
    bank_valid: bool = True
    exact_key_required: bool = False

    def cli(self) -> str:
        if self.bank is None:
            return f"{self.address:04X}"
        return f"{self.bank:02X}:{self.address:04X}"

    def evidence(self) -> str:
        if self.bank is None:
            return f"${self.address:04X}"
        return f"{self.bank:02X}:${self.address:04X}"

    def key(self) -> str:
        bank = f"{self.bank:02X}" if self.exact_key_required and self.bank is not None else "--"
        return f"{self.space}:{bank}:{self.address:04X}"

    def as_dict(self) -> dict[str, Any]:
        key = self.key()
        return {
            "raw": self.raw,
            "space": self.space,
            "bank": self.bank,
            "address": self.address,
            "address_hex": f"{self.address:04X}",
            "cli": self.cli(),
            "evidence": self.evidence(),
            "key": key,
            "address_key": key,
            "bank_semantics": self.bank_semantics,
            "bank_valid": self.bank_valid,
            "exact_key_required": self.exact_key_required,
        }


@dataclass(frozen=True)
class ObservedAddressKey:
    address: int
    space: str
    bank: int | None = None
    bank_source: str = ""
    bank_semantics: str = "not_requested"
    bank_valid: bool = True
    requested_bank: int | None = None
    requested_bank_source: str = ""

    def key(self) -> str:
        bank = f"{self.bank:02X}" if self.exact_key_required() and self.bank is not None else "--"
        return f"{self.space}:{bank}:{self.address & 0xFFFF:04X}"

    def exact_key_required(self) -> bool:
        return self.bank_valid and self.bank is not None and self.space in BANK_QUALIFIED_SPACES

    def cli(self) -> str:
        if self.exact_key_required() and self.bank is not None:
            return f"{self.bank:02X}:{self.address & 0xFFFF:04X}"
        return f"{self.address & 0xFFFF:04X}"

    def evidence(self) -> str:
        if self.exact_key_required() and self.bank is not None:
            return f"{self.bank:02X}:${self.address & 0xFFFF:04X}"
        return f"${self.address & 0xFFFF:04X}"

    def as_dict(self) -> dict[str, Any]:
        key = self.key()
        return {
            "space": self.space,
            "bank": self.bank,
            "bank_source": self.bank_source,
            "address": self.address & 0xFFFF,
            "address_hex": f"{self.address & 0xFFFF:04X}",
            "cli": self.cli(),
            "evidence": self.evidence(),
            "key": key,
            "address_key": key,
            "exact_key_required": self.exact_key_required(),
            "bank_semantics": self.bank_semantics,
            "bank_valid": self.bank_valid,
            "requested_bank": self.requested_bank,
            "requested_bank_source": self.requested_bank_source,
        }


def parse_address_spec(value: Any) -> AddressSpec:
    raw = str(value).strip()
    if not raw:
        raise ValueError("missing address")
    bank: int | None = None
    address_text = raw
    if ":" in raw:
        bank_text, address_text = [part.strip() for part in raw.split(":", 1)]
        bank = parse_address_component(bank_text, bank=True)
        if bank < 0 or bank > 0xFF:
            raise ValueError(f"bank out of range: {value}")
    address = parse_address_component(address_text, address=True)
    if address < 0 or address > 0xFFFF:
        raise ValueError(f"address out of range: {value}")
    space = memory_space(address, bank=bank)
    bank_semantics, bank_valid = address_bank_semantics(space=space, bank=bank)
    if not bank_valid:
        raise ValueError(f"bank prefix is not meaningful for {space} address: {value}")
    return AddressSpec(
        raw=raw,
        bank=bank,
        address=address,
        space=space,
        bank_semantics=bank_semantics,
        bank_valid=bank_valid,
        exact_key_required=bank is not None and space in BANK_QUALIFIED_SPACES,
    )


def observed_address_key(
    address: int,
    *,
    bank: int | None = None,
    space: str = "",
    bank_source: str = "",
) -> ObservedAddressKey:
    address &= 0xFFFF
    requested_bank = bank
    requested_bank_source = bank_source
    resolved_space = space or memory_space(address, bank=bank)
    bank_semantics, bank_valid = address_bank_semantics(space=resolved_space, bank=bank)
    if bank is not None and (not bank_valid or resolved_space not in BANK_QUALIFIED_SPACES):
        bank = None
        bank_source = ""
        if not space:
            resolved_space = memory_space(address)
    return ObservedAddressKey(
        address=address,
        space=resolved_space,
        bank=bank,
        bank_source=bank_source,
        bank_semantics=bank_semantics,
        bank_valid=bank_valid,
        requested_bank=requested_bank,
        requested_bank_source=requested_bank_source,
    )


def parse_address_int(value: Any) -> int:
    if value is None:
        raise ValueError("missing integer value")
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        raise ValueError("missing integer value")
    if text.startswith("$"):
        return int(text[1:], 16)
    if text.startswith(("0x", "0X")):
        return int(text, 16)
    if any(char in "ABCDEFabcdef" for char in text):
        return int(text, 16)
    return int(text, 10)


def parse_address_component(value: Any, *, bank: bool = False, address: bool = False) -> int:
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        raise ValueError("missing integer value")
    if text.startswith("$"):
        return int(text[1:], 16)
    if text.startswith(("0x", "0X")):
        return int(text, 16)
    if any(char in "ABCDEFabcdef" for char in text):
        return int(text, 16)
    if bank and len(text) == 2:
        return int(text, 16)
    if address and len(text) == 4:
        return int(text, 16)
    return int(text, 10)


def command_address_text(value: Any) -> str:
    text = str(value).strip()
    if not text:
        return ""
    if "=" in text:
        name, address = [part.strip() for part in text.split("=", 1)]
        rendered = command_address_text(address)
        return f"{name}={rendered}" if rendered else name
    try:
        return parse_address_spec(text).cli()
    except ValueError:
        return text.replace("$", "")


def address_key(value: Any) -> str:
    try:
        return parse_address_spec(value).key()
    except ValueError:
        return command_address_text(value).upper()


def address_spec_requires_exact_key(value: Any) -> bool:
    if isinstance(value, AddressSpec):
        return value.exact_key_required
    if isinstance(value, ObservedAddressKey):
        return value.exact_key_required()
    if isinstance(value, dict):
        bank = mapping_bank(value)
        if bank is None:
            return False
        space = str(value.get("space", ""))
        if not space:
            address = mapping_address(value)
            if address is None:
                return False
            space = memory_space(address, bank=bank)
        return space in BANK_QUALIFIED_SPACES and value.get("bank_valid", True) is not False
    try:
        return parse_address_spec(value).exact_key_required
    except ValueError:
        return False


def address_key_requires_exact_match(key: str) -> bool:
    parts = str(key).split(":")
    if len(parts) < 3:
        return False
    space, bank = parts[0], parts[1]
    return space in BANK_QUALIFIED_SPACES and bank not in {"", "--"}


def evidence_address(value: Any) -> str:
    try:
        return parse_address_spec(value).evidence()
    except ValueError:
        return str(value).strip()


def address_bank_semantics(*, space: str, bank: int | None) -> tuple[str, bool]:
    if bank is None:
        return "not_requested", True
    if space == "wramx":
        if 1 <= bank <= 7:
            return "runtime_bank_required", True
        return "invalid_wramx_bank_range", False
    if space == "vram":
        if bank in {0, 1}:
            return "runtime_bank_required", True
        return "invalid_vram_bank_range", False
    if space == "romx":
        if bank >= 1:
            return "runtime_bank_required", True
        return "invalid_romx_bank_range", False
    if space in BANK_QUALIFIED_SPACES:
        return "runtime_bank_required", True
    if bank == 0:
        return "static_bank_not_runtime_exact", True
    return "invalid_for_unbanked_space", False


def mapping_bank(value: dict[str, Any]) -> int | None:
    bank = value.get("bank")
    if bank in {None, ""}:
        return None
    try:
        return parse_address_component(bank, bank=True)
    except (TypeError, ValueError):
        return None


def mapping_address(value: dict[str, Any]) -> int | None:
    for key in ("address", "address_hex"):
        raw = value.get(key)
        if raw in {None, ""}:
            continue
        try:
            return parse_address_component(raw, address=True) & 0xFFFF
        except (TypeError, ValueError):
            continue
    return None


def memory_space(address: int, *, bank: int | None = None) -> str:
    address &= 0xFFFF
    if address < 0x4000:
        return "rom0"
    if address < 0x8000:
        return "romx"
    if address < 0xA000:
        return "vram"
    if address < 0xC000:
        return "sram"
    if address < 0xD000:
        return "wram0"
    if address < 0xE000:
        return "wramx" if bank is not None else "wram"
    if address < 0xFE00:
        return "echo"
    if address < 0xFEA0:
        return "oam"
    if address < 0xFF00:
        return "unusable"
    if address < 0xFF80:
        return "io"
    if address < 0xFFFF:
        return "hram"
    return "ie"
