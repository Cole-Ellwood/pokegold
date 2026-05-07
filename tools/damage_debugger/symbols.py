"""RGBDS .sym parser. Format: ``bank:addr name`` per line, comments with ``;``.

Builds both forward (name -> Symbol) and reverse ((bank,addr) -> sorted labels)
indexes so the tracer can render any PC as ``Label+0xNN``.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Symbol:
    bank: int
    address: int
    name: str

    def key(self) -> tuple[int, int]:
        return (self.bank, self.address)


def parse_sym(path: Path) -> list[Symbol]:
    out: list[Symbol] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2 or ":" not in parts[0]:
            continue
        bank_s, addr_s = parts[0].split(":", 1)
        try:
            bank = int(bank_s, 16)
            addr = int(addr_s, 16)
        except ValueError:
            continue
        out.append(Symbol(bank=bank, address=addr, name=parts[1]))
    return out


class SymbolTable:
    def __init__(self, symbols: Iterable[Symbol]):
        self._by_name: dict[str, Symbol] = {}
        # Per-bank sorted list of (addr, name) for nearest-label lookup.
        self._by_bank: dict[int, list[tuple[int, str]]] = {}
        for s in symbols:
            self._by_name[s.name] = s
            self._by_bank.setdefault(s.bank, []).append((s.address, s.name))
        for bank, items in self._by_bank.items():
            items.sort()

    @classmethod
    def load(cls, path: Path) -> "SymbolTable":
        return cls(parse_sym(path))

    def __contains__(self, name: str) -> bool:
        return name in self._by_name

    def __getitem__(self, name: str) -> Symbol:
        return self._by_name[name]

    def get(self, name: str) -> Symbol | None:
        return self._by_name.get(name)

    def as_legacy_dict(self) -> dict[str, tuple[int, int]]:
        """Return the old damage-debugger shape: name -> (bank, address)."""
        return {
            name: (symbol.bank, symbol.address)
            for name, symbol in self._by_name.items()
        }

    def render(self, bank: int, addr: int) -> str:
        """Render (bank, addr) as 'Label+0xNN' or '$BB:AAAA' if no nearby label."""
        items = self._by_bank.get(bank)
        if not items:
            return f"${bank:02x}:{addr:04x}"
        idx = bisect.bisect_right(items, (addr, "\xff")) - 1
        if idx < 0:
            return f"${bank:02x}:{addr:04x}"
        base_addr, base_name = items[idx]
        offset = addr - base_addr
        if offset == 0:
            return base_name
        if offset < 0 or offset > 0x1000:
            return f"${bank:02x}:{addr:04x}"
        return f"{base_name}+0x{offset:x}"

    def labels_in(self, bank: int) -> list[tuple[int, str]]:
        return list(self._by_bank.get(bank, []))
