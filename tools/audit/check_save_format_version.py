#!/usr/bin/env python3
"""Audit SAVE_FORMAT_VERSION against the in-game save layout fingerprint.

Computes a deterministic SHA-256 fingerprint over the source-level structure of
WRAM fields that get serialized to the in-game save (wOptions, wPlayerData1/2/3,
wCurMapData, wPokemonData), the SRAM section contents that hold them, and the
declared SRAM section ordering. When that fingerprint changes without a matching
SAVE_FORMAT_VERSION bump in constants/misc_constants.asm, this audit fails: any
old save written by the previous build would silently misalign on load.

Limitation: the source-only fingerprint catches added/removed/reordered/renamed
labels and changed section ordering, but not silent `ds N` size tweaks that
don't touch any label. A future revision can extend this by reading pokegold.sym
for actual byte sizes; the audit must keep working without a build artifact so
it can run pre-build.

Usage:
  check_save_format_version.py            # validate, exit 1 on mismatch
  check_save_format_version.py --update   # write current fingerprint as the
                                          # expected entry for the current
                                          # SAVE_FORMAT_VERSION (use after a
                                          # deliberate version bump)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONSTANTS = ROOT / "constants" / "misc_constants.asm"
WRAM = ROOT / "ram" / "wram.asm"
SRAM = ROOT / "ram" / "sram.asm"
LAYOUT = ROOT / "layout.link"
DATA_FILE = ROOT / "tools" / "audit" / "data" / "save_format_fingerprints.json"

WRAM_PAIRS = (
    ("wOptions", "wOptionsEnd"),
    ("wPlayerData1", "wPlayerData1End"),
    ("wPlayerData2", "wPlayerData2End"),
    ("wPlayerData3", "wPlayerData3End"),
    ("wCurMapData", "wCurMapDataEnd"),
    ("wPokemonData", "wPokemonDataEnd"),
)
SRAM_SECTIONS_OF_INTEREST = ("Save", "Backup Save 1", "Backup Save 2", "Backup Save 3")

EQU_RE = re.compile(r"^\s*DEF\s+SAVE_FORMAT_VERSION\s+EQU\s+(\d+)\b")
WRAM_LABEL_RE = re.compile(r"^(w[A-Za-z0-9_]+)::")
SRAM_LABEL_RE = re.compile(r"^(s[A-Za-z0-9_]+)::")
SECTION_RE = re.compile(r'^SECTION\s+"([^"]+)"\s*,\s*SRAM\b')
BANK_HEADER_RE = re.compile(r"^([A-Z][A-Z0-9_]*)\s+\$([0-9a-fA-F]+)\b")
LAYOUT_SECTION_RE = re.compile(r'^\s*"([^"]+)"\s*$')


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load(path: Path) -> str:
    if not path.exists():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8", errors="replace")


def parse_version() -> int:
    for line in load(CONSTANTS).splitlines():
        match = EQU_RE.match(line)
        if match:
            return int(match.group(1))
    fail(f"could not parse SAVE_FORMAT_VERSION from {CONSTANTS.relative_to(ROOT)}")
    return 0


def parse_wram_pairs() -> dict[str, list[str]]:
    lines = load(WRAM).splitlines()
    label_at: dict[str, int] = {}
    for idx, line in enumerate(lines):
        match = WRAM_LABEL_RE.match(line)
        if match:
            label_at.setdefault(match.group(1), idx)

    out: dict[str, list[str]] = {}
    for start_name, end_name in WRAM_PAIRS:
        if start_name not in label_at:
            fail(f"wram.asm missing start label: {start_name}")
        if end_name not in label_at:
            fail(f"wram.asm missing end label: {end_name}")
        start, end = label_at[start_name], label_at[end_name]
        if end <= start:
            fail(f"wram.asm: {end_name} not after {start_name}")
        labels = [
            WRAM_LABEL_RE.match(lines[i]).group(1)  # type: ignore[union-attr]
            for i in range(start + 1, end)
            if WRAM_LABEL_RE.match(lines[i])
        ]
        out[f"{start_name}..{end_name}"] = labels
    return out


def parse_sram_sections() -> dict[str, list[str]]:
    lines = load(SRAM).splitlines()
    section_starts: dict[str, int] = {}
    section_order: list[str] = []
    for idx, line in enumerate(lines):
        match = SECTION_RE.match(line)
        if match:
            name = match.group(1)
            section_starts[name] = idx
            section_order.append(name)

    out: dict[str, list[str]] = {}
    for name in SRAM_SECTIONS_OF_INTEREST:
        if name not in section_starts:
            fail(f"sram.asm missing section: {name}")
        start = section_starts[name]
        idx = section_order.index(name)
        end = section_starts[section_order[idx + 1]] if idx + 1 < len(section_order) else len(lines)
        labels = [
            SRAM_LABEL_RE.match(lines[i]).group(1)  # type: ignore[union-attr]
            for i in range(start + 1, end)
            if SRAM_LABEL_RE.match(lines[i])
        ]
        out[name] = labels
    return out


def parse_sram_layout() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    current_bank: str | None = None
    for line in load(LAYOUT).splitlines():
        bank_match = BANK_HEADER_RE.match(line)
        if bank_match:
            if bank_match.group(1) == "SRAM":
                current_bank = f"SRAM ${bank_match.group(2)}"
                out[current_bank] = []
            else:
                current_bank = None
            continue
        if current_bank is not None:
            sec_match = LAYOUT_SECTION_RE.match(line)
            if sec_match:
                out[current_bank].append(sec_match.group(1))
    if not out:
        fail("could not parse any SRAM banks from layout.link")
    return out


def compute_fingerprint() -> tuple[str, dict[str, object]]:
    payload = {
        "wram_pairs": parse_wram_pairs(),
        "sram_sections": parse_sram_sections(),
        "sram_layout": parse_sram_layout(),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest, payload


def load_fingerprints() -> dict[str, str]:
    if not DATA_FILE.exists():
        return {}
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save_fingerprints(data: dict[str, str]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--update",
        action="store_true",
        help=(
            "overwrite the recorded fingerprint for the current SAVE_FORMAT_VERSION."
            " Use only after a deliberate version bump."
        ),
    )
    args = parser.parse_args(argv)

    version = parse_version()
    digest, _payload = compute_fingerprint()
    fingerprints = load_fingerprints()
    key = str(version)

    if args.update:
        fingerprints[key] = digest
        save_fingerprints(fingerprints)
        print(f"Recorded SAVE_FORMAT_VERSION={version} fingerprint: {digest}")
        return 0

    expected = fingerprints.get(key)
    if expected is None:
        fail(
            f"no recorded fingerprint for SAVE_FORMAT_VERSION={version}. "
            "If this is an intentional bump, run with --update. "
            "If not, revert the version constant in "
            f"{CONSTANTS.relative_to(ROOT)}."
        )

    if expected != digest:
        print(f"current fingerprint:  {digest}")
        print(f"expected fingerprint: {expected}")
        fail(
            "save layout changed without bumping SAVE_FORMAT_VERSION. "
            "Either revert the layout change in ram/wram.asm + ram/sram.asm + "
            "layout.link, or bump SAVE_FORMAT_VERSION in "
            f"{CONSTANTS.relative_to(ROOT)} and run "
            "`python tools/audit/check_save_format_version.py --update`."
        )

    print(f"Save format fingerprint matches SAVE_FORMAT_VERSION={version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
