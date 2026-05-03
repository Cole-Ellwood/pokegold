#!/usr/bin/env python3
"""Layout pin invariant audit (TD-003 partial close).

`layout.link` uses explicit `org $XXXX` directives in five places. Each
exists for a real downstream reason — see `docs/layout_pins.md` for the
full per-pin rationale. This audit verifies the pin set matches the
documented invariant: same banks, same addresses, same following
section names.

If a pin is removed, moved, or a new pin appears that this audit
doesn't know about, the audit FAILs with a side-by-side diff. The
reviewer must then either:
  (a) revert the layout.link change, or
  (b) update `EXPECTED_PINS` here AND `docs/layout_pins.md` to reflect
      the new contract, then re-run.

This audit does NOT verify that section content is intact (the linker
catches that). It guards the layout *contract* — that the pins still
exist where downstream consumers expect them.

Usage:
    check_layout_orgs.py
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "layout.link"

# Canonical pin set as of 2026-05-03. Each tuple: (bank_hex, address_hex,
# section_name_following_pin). The section name is the *first* quoted
# section after the org directive; pins like ROMX $2e where the org sits
# between two sections are recorded with the section *after* the org.
EXPECTED_PINS = (
    ("12", "$4000", "Pic Pointers"),
    ("1f", "$4000", "Unown Pic Pointers"),
    ("2e", "$6300", "bank2E"),
    ("31", "$7a40", "bank31"),
    ("7f", "$7df8", "Stadium 2 Checksums"),
)

BANK_RE = re.compile(r"^ROMX\s+\$([0-9a-fA-F]+)\s*$")
NON_ROMX_REGION_RE = re.compile(r"^(ROM0|WRAM0|WRAMX|VRAM|SRAM|HRAM)\b")
ORG_RE = re.compile(r"^\s*org\s+(\$[0-9a-fA-F]+)\s*$")
SECTION_RE = re.compile(r'^\s*"([^"]+)"\s*$')


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def parse_pins(text: str) -> list[tuple[str, str, str]]:
    """Walk layout.link, return (bank, address, first_section_after_org) tuples."""
    pins: list[tuple[str, str, str]] = []
    current_bank: str | None = None
    pending_org: str | None = None
    for line in text.splitlines():
        bank_match = BANK_RE.match(line)
        if bank_match:
            current_bank = bank_match.group(1).lower().zfill(2)
            pending_org = None
            continue
        # Non-ROMX region (ROM0, WRAM0, SRAM, etc.) — leave ROMX scope so
        # any subsequent `org` directives don't get attributed to the
        # previous ROMX bank.
        if NON_ROMX_REGION_RE.match(line):
            current_bank = None
            pending_org = None
            continue
        org_match = ORG_RE.match(line)
        if org_match and current_bank is not None:
            pending_org = org_match.group(1).lower()
            continue
        section_match = SECTION_RE.match(line)
        if section_match and current_bank is not None and pending_org is not None:
            pins.append((current_bank, pending_org, section_match.group(1)))
            pending_org = None
    return pins


def main() -> int:
    if not LAYOUT.exists():
        fail(f"missing {LAYOUT.relative_to(ROOT)}")

    actual = parse_pins(LAYOUT.read_text(encoding="utf-8"))
    actual_set = {(b, a, s) for (b, a, s) in actual}
    expected_set = {(b, a.lower(), s) for (b, a, s) in EXPECTED_PINS}

    missing = expected_set - actual_set
    extra = actual_set - expected_set

    if missing or extra:
        print("Layout pin set has drifted from the documented contract.")
        print("See `docs/layout_pins.md` for the per-pin rationale.")
        if missing:
            print("\nExpected (from EXPECTED_PINS) but not found in layout.link:")
            for bank, addr, section in sorted(missing):
                print(f"  ROMX ${bank} {addr} -> {section!r}")
        if extra:
            print("\nFound in layout.link but not in EXPECTED_PINS:")
            for bank, addr, section in sorted(extra):
                print(f"  ROMX ${bank} {addr} -> {section!r}")
        fail(
            "If the change is intentional, update EXPECTED_PINS in this "
            "audit AND docs/layout_pins.md in the same change. If it's "
            "accidental, revert layout.link."
        )

    print(
        "Layout pins OK: "
        + ", ".join(f"${b}:{a} -> {s}" for (b, a, s) in actual)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
