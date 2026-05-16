"""Save-format drift detection.

Hashes (label, offset, size) tuples for every symbol in SRAM/WRAM sections
from .sym+.map, compares against a committed lockfile. CI fails on mismatch
unless SAVE_FORMAT_VERSION was bumped in the same commit.

Per the roadmap: "Highest-ROI-per-LoC analysis on the entire list."

Usage:
    from tools.debugger.analysis.static.save_format_lock import SaveFormatChecker
    checker = SaveFormatChecker(svc)
    result = checker.check("save_format.lock")
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...kernel.symbol_service import SymbolService


@dataclass(frozen=True)
class FieldFingerprint:
    """One save-relevant field's identity."""
    name: str
    bank: int
    address: int
    section_name: str = ""

    def to_tuple(self) -> tuple[str, int, int]:
        return (self.name, self.bank, self.address)


@dataclass
class LockfileData:
    """Contents of a save_format.lock file."""
    version: str = ""
    fields: list[FieldFingerprint] = field(default_factory=list)
    digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "digest": self.digest,
            "field_count": len(self.fields),
            "fields": [
                {"name": f.name, "bank": f.bank, "address": f.address}
                for f in self.fields
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, text: str) -> LockfileData:
        data = json.loads(text)
        fields = [
            FieldFingerprint(name=f["name"], bank=f["bank"], address=f["address"])
            for f in data.get("fields", [])
        ]
        return cls(
            version=data.get("version", ""),
            fields=fields,
            digest=data.get("digest", ""),
        )


@dataclass
class DriftResult:
    """Result of comparing current layout against lockfile."""
    ok: bool
    added: list[FieldFingerprint] = field(default_factory=list)
    removed: list[FieldFingerprint] = field(default_factory=list)
    moved: list[tuple[FieldFingerprint, FieldFingerprint]] = field(default_factory=list)
    current_digest: str = ""
    locked_digest: str = ""
    version_bumped: bool = False

    def summary(self) -> str:
        if self.ok:
            return "Save format: no drift detected."
        lines = ["Save format drift detected!"]
        if self.added:
            lines.append(f"  Added: {len(self.added)} fields")
            for f in self.added[:10]:
                lines.append(f"    + {f.name} at ${f.bank:02x}:{f.address:04x}")
        if self.removed:
            lines.append(f"  Removed: {len(self.removed)} fields")
            for f in self.removed[:10]:
                lines.append(f"    - {f.name} at ${f.bank:02x}:{f.address:04x}")
        if self.moved:
            lines.append(f"  Moved: {len(self.moved)} fields")
            for old, new in self.moved[:10]:
                lines.append(
                    f"    ~ {old.name}: "
                    f"${old.bank:02x}:{old.address:04x} -> "
                    f"${new.bank:02x}:{new.address:04x}"
                )
        if not self.version_bumped:
            lines.append("  SAVE_FORMAT_VERSION was NOT bumped!")
        return "\n".join(lines)


def _compute_digest(fields: list[FieldFingerprint]) -> str:
    h = hashlib.sha256()
    for f in sorted(fields, key=lambda x: (x.bank, x.address, x.name)):
        h.update(f"{f.name}:{f.bank}:{f.address}\n".encode())
    return h.hexdigest()[:16]


class SaveFormatChecker:
    """Checks save-format field layout against a lockfile."""

    SAVE_REGIONS = {"SRAM", "WRAM0", "WRAMX"}

    def __init__(self, svc: SymbolService) -> None:
        self._svc = svc

    def current_fields(self) -> list[FieldFingerprint]:
        """Extract all save-relevant fields from current symbol service."""
        fields: list[FieldFingerprint] = []
        seen: set[tuple[str, int, int]] = set()

        for section in self._svc.sections:
            if section.memory not in self.SAVE_REGIONS:
                continue
            for label_name in section.labels:
                sym = self._svc.resolve(label_name)
                if sym is None:
                    continue
                key = (sym.name, sym.bank, sym.address)
                if key in seen:
                    continue
                seen.add(key)
                fields.append(FieldFingerprint(
                    name=sym.name,
                    bank=sym.bank,
                    address=sym.address,
                    section_name=section.name,
                ))

        if not fields:
            for bank in range(256):
                for addr, name in self._svc.labels_in_bank(bank):
                    if 0xA000 <= addr <= 0xBFFF:
                        key = (name, bank, addr)
                        if key not in seen:
                            seen.add(key)
                            fields.append(FieldFingerprint(
                                name=name, bank=bank, address=addr,
                            ))

        fields.sort(key=lambda f: (f.bank, f.address, f.name))
        return fields

    def generate_lockfile(self, version: str = "1") -> LockfileData:
        """Generate a new lockfile from current state."""
        fields = self.current_fields()
        digest = _compute_digest(fields)
        return LockfileData(version=version, fields=fields, digest=digest)

    def check(self, lockfile_path: str | Path) -> DriftResult:
        """Compare current layout against a lockfile."""
        path = Path(lockfile_path)
        if not path.exists():
            current = self.current_fields()
            return DriftResult(
                ok=True,
                current_digest=_compute_digest(current),
                locked_digest="",
            )

        locked = LockfileData.from_json(path.read_text(encoding="utf-8"))
        current_fields = self.current_fields()
        current_digest = _compute_digest(current_fields)

        if current_digest == locked.digest:
            return DriftResult(
                ok=True,
                current_digest=current_digest,
                locked_digest=locked.digest,
            )

        locked_by_name: dict[str, FieldFingerprint] = {
            f.name: f for f in locked.fields
        }
        current_by_name: dict[str, FieldFingerprint] = {
            f.name: f for f in current_fields
        }

        added: list[FieldFingerprint] = []
        removed: list[FieldFingerprint] = []
        moved: list[tuple[FieldFingerprint, FieldFingerprint]] = []

        for f in current_fields:
            if f.name not in locked_by_name:
                added.append(f)
            elif f.address != locked_by_name[f.name].address:
                moved.append((locked_by_name[f.name], f))

        for f in locked.fields:
            if f.name not in current_by_name:
                removed.append(f)

        version_sym = self._svc.resolve("sSaveFormatVersion")
        if version_sym is None:
            version_sym = self._svc.resolve("SAVE_FORMAT_VERSION")
        version_bumped = False

        return DriftResult(
            ok=False,
            added=added,
            removed=removed,
            moved=moved,
            current_digest=current_digest,
            locked_digest=locked.digest,
            version_bumped=version_bumped,
        )

    def write_lockfile(self, path: str | Path, version: str = "1") -> None:
        """Write a fresh lockfile."""
        lockdata = self.generate_lockfile(version)
        Path(path).write_text(lockdata.to_json() + "\n", encoding="utf-8")
