"""Consolidated symbol + map + bank-ownership service.

Builds indexed lookups from RGBDS .sym and .map files at startup.
Replaces ad-hoc parsing scattered across damage_debugger/symbols.py
and scripts/generate_dev_index.py with one authoritative service.

Usage:
    svc = SymbolService.from_project()
    sym = svc.resolve("wBattleMonHP")        # -> SymbolEntry
    label = svc.render(0x01, 0x4000)         # -> "SomeLabel"
    free = svc.bank_free_bytes(0x0b)         # -> int
    syms = svc.prefix_search("wBattleMon")   # -> list[SymbolEntry]
"""

from __future__ import annotations

import bisect
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


SYM_RE = re.compile(
    r"^(?P<bank>[0-9a-fA-F]{2}):(?P<address>[0-9a-fA-F]{4})\s+(?P<name>\S+)$"
)

SUMMARY_RE = re.compile(
    r"^\t(?P<memory>[A-Z0-9]+): (?P<used>\d+) bytes used / "
    r"(?P<free>\d+) free(?: in (?P<banks>\d+) banks)?"
)
BANK_RE = re.compile(r"^(?P<memory>[A-Z0-9]+) bank #(?P<bank>\d+):$")
SECTION_RE = re.compile(
    r'^\tSECTION: \$(?P<start>[0-9a-fA-F]+)'
    r'(?:-\$(?P<end>[0-9a-fA-F]+))? '
    r'\(\$(?P<size>[0-9a-fA-F]+) bytes?\) \["(?P<name>.+)"\]$'
)
EMPTY_RANGE_RE = re.compile(
    r"^\tEMPTY: \$(?P<start>[0-9a-fA-F]+)-\$(?P<end>[0-9a-fA-F]+) "
    r"\(\$(?P<size>[0-9a-fA-F]+) bytes?\)$"
)
LABEL_IN_MAP_RE = re.compile(
    r"^\t\s+\$(?P<address>[0-9a-fA-F]+) = (?P<name>\S+)$"
)


@dataclass(frozen=True)
class SymbolEntry:
    """A single symbol from the .sym file."""
    bank: int
    address: int
    name: str

    def key(self) -> tuple[int, int]:
        return (self.bank, self.address)

    def __str__(self) -> str:
        return f"${self.bank:02x}:{self.address:04x} {self.name}"


@dataclass(frozen=True)
class MapSection:
    """A SECTION block from the .map file."""
    memory: str
    bank: int
    start: int
    end: int
    size: int
    name: str
    labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class MapEmptyRange:
    """An EMPTY range from the .map file."""
    memory: str
    bank: int
    start: int
    end: int
    size: int


@dataclass(frozen=True)
class MemorySummary:
    """Per-memory-type usage summary from .map."""
    memory: str
    used: int
    free: int
    banks: int | None = None


@dataclass
class BankInfo:
    """Aggregated info for a single bank."""
    memory: str
    bank_number: int
    sections: list[MapSection] = field(default_factory=list)
    empty_ranges: list[MapEmptyRange] = field(default_factory=list)

    @property
    def total_free(self) -> int:
        return sum(r.size for r in self.empty_ranges)

    @property
    def total_used(self) -> int:
        return sum(s.size for s in self.sections)


def _parse_sym(path: Path) -> list[SymbolEntry]:
    out: list[SymbolEntry] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        m = SYM_RE.match(line)
        if not m:
            parts = line.split()
            if len(parts) >= 2 and ":" in parts[0]:
                bank_s, addr_s = parts[0].split(":", 1)
                try:
                    bank = int(bank_s, 16)
                    addr = int(addr_s, 16)
                except ValueError:
                    continue
                out.append(SymbolEntry(bank=bank, address=addr, name=parts[1]))
            continue
        out.append(SymbolEntry(
            bank=int(m["bank"], 16),
            address=int(m["address"], 16),
            name=m["name"],
        ))
    return out


def _parse_map(path: Path) -> tuple[
    list[MemorySummary],
    list[MapSection],
    list[MapEmptyRange],
]:
    summaries: list[MemorySummary] = []
    sections: list[MapSection] = []
    empties: list[MapEmptyRange] = []

    cur_memory = ""
    cur_bank = 0
    cur_section_labels: list[str] = []
    cur_section: MapSection | None = None

    def _flush_section():
        nonlocal cur_section
        if cur_section is not None:
            sections.append(MapSection(
                memory=cur_section.memory,
                bank=cur_section.bank,
                start=cur_section.start,
                end=cur_section.end,
                size=cur_section.size,
                name=cur_section.name,
                labels=tuple(cur_section_labels),
            ))
            cur_section_labels.clear()
            cur_section = None

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = SUMMARY_RE.match(raw_line)
        if m:
            summaries.append(MemorySummary(
                memory=m["memory"],
                used=int(m["used"]),
                free=int(m["free"]),
                banks=int(m["banks"]) if m["banks"] else None,
            ))
            continue

        m = BANK_RE.match(raw_line)
        if m:
            _flush_section()
            cur_memory = m["memory"]
            cur_bank = int(m["bank"])
            continue

        m = SECTION_RE.match(raw_line)
        if m:
            _flush_section()
            start = int(m["start"], 16)
            end = int(m["end"], 16) if m["end"] else start
            cur_section = MapSection(
                memory=cur_memory,
                bank=cur_bank,
                start=start,
                end=end,
                size=int(m["size"], 16),
                name=m["name"],
            )
            continue

        m = EMPTY_RANGE_RE.match(raw_line)
        if m:
            _flush_section()
            empties.append(MapEmptyRange(
                memory=cur_memory,
                bank=cur_bank,
                start=int(m["start"], 16),
                end=int(m["end"], 16),
                size=int(m["size"], 16),
            ))
            continue

        m = LABEL_IN_MAP_RE.match(raw_line)
        if m:
            cur_section_labels.append(m["name"])

    _flush_section()
    return summaries, sections, empties


def _candidate_roots(start: Path) -> Iterable[Path]:
    yield start
    cur = start
    for _ in range(6):
        cur = cur.parent
        yield cur
        if (cur / ".git").exists() or (cur / "Makefile").exists():
            break


def _find_artifact(name: str, start: Path | None = None) -> Path | None:
    if start is None:
        start = Path(__file__).resolve().parents[3]
    seen: set[Path] = set()
    for root in _candidate_roots(start):
        root = root.resolve()
        if root in seen:
            continue
        seen.add(root)
        candidate = root / name
        if candidate.exists():
            return candidate
    return None


class SymbolService:
    """Fast indexed lookups over .sym + .map data.

    The service is immutable after construction. Build via
    ``SymbolService.from_project()`` or ``SymbolService.from_files()``.
    """

    def __init__(
        self,
        symbols: list[SymbolEntry],
        summaries: list[MemorySummary] | None = None,
        sections: list[MapSection] | None = None,
        empty_ranges: list[MapEmptyRange] | None = None,
    ):
        self._symbols = symbols
        self._summaries = summaries or []
        self._sections = sections or []
        self._empty_ranges = empty_ranges or []

        self._by_name: dict[str, SymbolEntry] = {}
        self._by_bank: dict[int, list[tuple[int, str]]] = {}
        self._names_sorted: list[str] = []

        for s in symbols:
            self._by_name[s.name] = s
            self._by_bank.setdefault(s.bank, []).append((s.address, s.name))
        for items in self._by_bank.values():
            items.sort()
        self._names_sorted = sorted(self._by_name.keys())

        self._bank_info: dict[tuple[str, int], BankInfo] = {}
        for sec in self._sections:
            key = (sec.memory, sec.bank)
            if key not in self._bank_info:
                self._bank_info[key] = BankInfo(
                    memory=sec.memory, bank_number=sec.bank
                )
            self._bank_info[key].sections.append(sec)
        for emp in self._empty_ranges:
            key = (emp.memory, emp.bank)
            if key not in self._bank_info:
                self._bank_info[key] = BankInfo(
                    memory=emp.memory, bank_number=emp.bank
                )
            self._bank_info[key].empty_ranges.append(emp)

    @classmethod
    def from_files(
        cls,
        sym_path: Path,
        map_path: Path | None = None,
    ) -> SymbolService:
        symbols = _parse_sym(sym_path)
        if map_path and map_path.exists():
            summaries, sections, empties = _parse_map(map_path)
        else:
            summaries, sections, empties = [], [], []
        return cls(symbols, summaries, sections, empties)

    @classmethod
    def from_project(
        cls,
        variant: str = "pokegold",
        start: Path | None = None,
    ) -> SymbolService:
        sym_path = _find_artifact(f"{variant}.sym", start)
        if sym_path is None:
            for alt in (f"{variant}_debug.sym",):
                sym_path = _find_artifact(alt, start)
                if sym_path is not None:
                    break
        if sym_path is None:
            raise FileNotFoundError(
                f"Could not find {variant}.sym or {variant}_debug.sym. "
                "Build the ROM first (see CLAUDE.md)."
            )
        stem = sym_path.stem
        map_path = sym_path.with_suffix(".map")
        return cls.from_files(sym_path, map_path)

    @property
    def symbol_count(self) -> int:
        return len(self._by_name)

    @property
    def bank_count(self) -> int:
        return len(self._by_bank)

    @property
    def summaries(self) -> list[MemorySummary]:
        return list(self._summaries)

    @property
    def sections(self) -> list[MapSection]:
        return list(self._sections)

    @property
    def empty_ranges(self) -> list[MapEmptyRange]:
        return list(self._empty_ranges)

    def resolve(self, name: str) -> SymbolEntry | None:
        return self._by_name.get(name)

    def render(self, bank: int, addr: int) -> str:
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

    def labels_in_bank(self, bank: int) -> list[tuple[int, str]]:
        return list(self._by_bank.get(bank, []))

    def prefix_search(self, prefix: str) -> list[SymbolEntry]:
        idx = bisect.bisect_left(self._names_sorted, prefix)
        results: list[SymbolEntry] = []
        while idx < len(self._names_sorted) and self._names_sorted[idx].startswith(prefix):
            results.append(self._by_name[self._names_sorted[idx]])
            idx += 1
        return results

    def bank_free_bytes(self, bank: int, memory: str = "ROMX") -> int | None:
        info = self._bank_info.get((memory, bank))
        if info is None:
            return None
        return info.total_free

    def bank_info(self, bank: int, memory: str = "ROMX") -> BankInfo | None:
        return self._bank_info.get((memory, bank))

    def all_bank_info(self) -> dict[tuple[str, int], BankInfo]:
        return dict(self._bank_info)

    def tight_banks(self, threshold: int = 256, memory: str = "ROMX") -> list[BankInfo]:
        return sorted(
            (info for key, info in self._bank_info.items()
             if key[0] == memory and info.total_free < threshold),
            key=lambda b: b.total_free,
        )

    def as_legacy_dict(self) -> dict[str, tuple[int, int]]:
        """Return the old damage-debugger shape: name -> (bank, address)."""
        return {
            name: (sym.bank, sym.address)
            for name, sym in self._by_name.items()
        }

    def as_legacy_symbol_table(self):
        """Return a damage_debugger.symbols.SymbolTable-compatible object."""
        return self

    def __contains__(self, name: str) -> bool:
        return name in self._by_name

    def __getitem__(self, name: str) -> SymbolEntry:
        return self._by_name[name]

    def get(self, name: str) -> SymbolEntry | None:
        return self._by_name.get(name)
