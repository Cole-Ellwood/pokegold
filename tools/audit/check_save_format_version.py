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

from _common import fail, load


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
TRACE_ONLY_IF_RE = re.compile(r"^\s*IF\s+DEF\(\s*BOSS_AI_TRACE\s*\)\s*$")
IF_RE = re.compile(r"^\s*IF\b")
ENDC_RE = re.compile(r"^\s*ENDC\b")


BOSS_AI_RESERVE_BYTES = 140
BOSS_AI_RESERVE_PAD_RE = re.compile(
    r"^\s*ds\s+(\d+)\s*-\s*\(\s*wBossAIStateEnd\s*-\s*wBossAITier\s*\)"
)


def normal_build_wram_lines() -> list[str]:
    """Return wram.asm source lines visible to normal, save-compatible builds.

    Also collapses the wBossAI* subrange (wBossAITier..wBossAIStateEnd) to
    just its start and end markers + a padding-sentinel line. The wBossAI*
    block lives inside wPlayerData3 and the wPlayerData3 raw-copy save
    path persists those bytes, but the block is sized by a fixed
    `ds 140 - (wBossAIStateEnd - wBossAITier)` reserve pad that keeps
    wEventFlags at the same byte offset regardless of how many wBossAI*
    labels live inside it. Treating every new wBossAI* label as save-layout
    drift over-constrains the audit. Instead, fingerprint the wBossAI*
    block as opaque AND assert the 140-byte reserve invariant remains.
    """

    lines = load(WRAM).splitlines()
    out: list[str] = []
    trace_only_depth = 0
    reserve_pad_found = False
    in_boss_ai_block = False
    for line in lines:
        if trace_only_depth:
            if IF_RE.match(line):
                trace_only_depth += 1
            elif ENDC_RE.match(line):
                trace_only_depth -= 1
            continue
        if TRACE_ONLY_IF_RE.match(line):
            trace_only_depth = 1
            continue
        if BOSS_AI_RESERVE_PAD_RE.match(line):
            pad_match = BOSS_AI_RESERVE_PAD_RE.match(line)
            pad_size = int(pad_match.group(1))
            if pad_size != BOSS_AI_RESERVE_BYTES:
                fail(
                    f"Boss AI reserve pad expected {BOSS_AI_RESERVE_BYTES} bytes, "
                    f"got {pad_size}; wBossAI* growth would shift saved event flags. "
                    "Either reduce wBossAI* usage or bump SAVE_FORMAT_VERSION + "
                    "update this audit's BOSS_AI_RESERVE_BYTES constant."
                )
            reserve_pad_found = True
            out.append(line)
            in_boss_ai_block = False
            continue
        label_match = WRAM_LABEL_RE.match(line)
        if label_match:
            label_name = label_match.group(1)
            if label_name == "wBossAITier":
                in_boss_ai_block = True
                out.append(line)
                continue
            if label_name == "wBossAIStateEnd":
                in_boss_ai_block = False
                out.append(line)
                continue
            if in_boss_ai_block:
                # Inner wBossAI* label: opaque to the fingerprint.
                continue
        out.append(line)
    if trace_only_depth:
        fail("wram.asm has an unterminated IF DEF(BOSS_AI_TRACE) block")
    if not reserve_pad_found:
        fail(
            f"wram.asm missing `ds {BOSS_AI_RESERVE_BYTES} - (wBossAIStateEnd - wBossAITier)` "
            "reserve pad; required to keep wEventFlags pinned regardless of wBossAI* growth."
        )
    return out


def parse_version() -> int:
    for line in load(CONSTANTS).splitlines():
        match = EQU_RE.match(line)
        if match:
            return int(match.group(1))
    fail(f"could not parse SAVE_FORMAT_VERSION from {CONSTANTS.relative_to(ROOT)}")
    return 0


def parse_wram_pairs() -> dict[str, list[str]]:
    lines = normal_build_wram_lines()
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
