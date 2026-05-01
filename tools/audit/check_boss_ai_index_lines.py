#!/usr/bin/env python3
"""Audit hand-typed line numbers in boss_ai_logic.md against current source.

The Boss AI navigation index pins behaviors to label-anchored lines in
``engine/battle/ai/boss.asm`` and a handful of nearby files. Those line
numbers shift on most non-trivial edits to ``boss.asm``, so they drift
silently between sessions. This audit walks every label-anchored backtick
reference in the index and verifies the cited line.

What it audits
  - Bare ``Label:NNN`` refs (no path). Searches ``boss.asm`` plus a small
    fallback set of related asm files (the ones in the index's
    "Source Files At A Glance" table). Pass if the named label appears at
    line ``NNN`` in any one of them.
  - Local ``\\.foo:NNN`` refs. Always resolved against ``boss.asm``. The
    local label must appear at the cited line *and* have an enclosing
    top-level parent routine before it.

What it skips (not a failure; surfaced as an "unaudited" count)
  - Range refs like ``Label:NNN-MMM``.
  - Comma-list refs like ``Label:N,M,P``.

What it ignores (different drift class; out of scope)
  - Path-prefixed refs containing ``/``. Those have no label to anchor to;
    file existence is ``check_docs_navigation.py``'s job.

Usage
  check_boss_ai_index_lines.py     # validate; exit 1 on any mismatch
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "docs" / "agent_navigation" / "subsystems" / "boss_ai_logic.md"
DEFAULT_SOURCE = ROOT / "engine" / "battle" / "ai" / "boss.asm"

# Files the index can name with bare ``Label:NNN`` refs. ``boss.asm`` first
# so it wins ties; the rest mirror the index's "Source Files At A Glance"
# plus a few cross-file callsites the index pins by label name.
FALLBACK_SOURCES: tuple[Path, ...] = (
    DEFAULT_SOURCE,
    ROOT / "engine" / "battle" / "ai" / "scoring.asm",
    ROOT / "engine" / "battle" / "ai" / "switch.asm",
    ROOT / "engine" / "battle" / "ai" / "items.asm",
    ROOT / "engine" / "battle" / "ai" / "move.asm",
    ROOT / "engine" / "battle" / "ai" / "redundant.asm",
    ROOT / "engine" / "battle" / "read_trainer_attributes.asm",
    ROOT / "engine" / "battle" / "start_battle.asm",
    ROOT / "engine" / "battle" / "core.asm",
    ROOT / "data" / "trainers" / "ai_tiers.asm",
    ROOT / "data" / "trainers" / "attributes.asm",
    ROOT / "home" / "battle.asm",
    ROOT / "ram" / "wram.asm",
)

# Backtick group is a label-line ref if and only if its full content matches
# this. Group 1: leading dot for local labels. Group 2: label name. Group 3:
# the cited line. Group 4 (non-empty for ranges/comma lists): everything
# after the first line number. The ``$`` anchor rejects file-style refs
# like ``boss.asm:6696`` because ``.asm`` isn't a label-name character.
LABEL_REF = re.compile(r"^(\.)?([A-Za-z_]\w*):(\d+)((?:[-,]\d+)*)$")
TOP_LABEL_RE = re.compile(r"^([A-Z]\w*)::?")
LOCAL_LABEL_RE = re.compile(r"^\.([A-Za-z_]\w*)")
BACKTICK_GROUP = re.compile(r"`([^`\n]+)`")


def fail(message: str) -> None:
    print(f"FAIL: {message}")


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def build_top_label_index() -> dict[str, list[tuple[Path, int]]]:
    """Return ``{label: [(path, 1-indexed-line), ...]}`` across fallback sources."""
    index: dict[str, list[tuple[Path, int]]] = {}
    for source in FALLBACK_SOURCES:
        for idx, line in enumerate(read_lines(source), start=1):
            match = TOP_LABEL_RE.match(line)
            if match:
                index.setdefault(match.group(1), []).append((source, idx))
    return index


def check_local_label(label: str, line_no: int, raw_ref: str) -> str | None:
    lines = read_lines(DEFAULT_SOURCE)
    rel = DEFAULT_SOURCE.relative_to(ROOT).as_posix()
    if line_no < 1 or line_no > len(lines):
        return (
            f"`{raw_ref}` cites line {line_no} but {rel} has only "
            f"{len(lines)} lines"
        )
    actual = lines[line_no - 1]
    match = LOCAL_LABEL_RE.match(actual)
    if not match or match.group(1) != label:
        return (
            f"`{raw_ref}` says local label `.{label}` at {rel}:{line_no}, "
            f"source line is: {actual.rstrip()!r}"
        )
    for prev_idx in range(line_no - 2, -1, -1):
        if TOP_LABEL_RE.match(lines[prev_idx]):
            return None
    return (
        f"`{raw_ref}` local label has no enclosing parent routine in {rel} "
        f"before line {line_no}"
    )


def check_top_label(
    label: str,
    line_no: int,
    raw_ref: str,
    label_index: dict[str, list[tuple[Path, int]]],
) -> str | None:
    candidates = label_index.get(label, [])
    if not candidates:
        return (
            f"`{raw_ref}` references unknown label `{label}` "
            f"(not found in any audited source file)"
        )
    if any(idx == line_no for _, idx in candidates):
        return None
    rendered = ", ".join(
        f"{path.relative_to(ROOT).as_posix()}:{idx}" for path, idx in candidates
    )
    return (
        f"index says `{label}:{line_no}`, source has `{label}` at {rendered}. "
        f"Update the index line."
    )


def main() -> int:
    if not INDEX.exists():
        fail(f"missing index file: {INDEX.relative_to(ROOT)}")
        return 1
    if not DEFAULT_SOURCE.exists():
        fail(f"missing default source: {DEFAULT_SOURCE.relative_to(ROOT)}")
        return 1

    label_index = build_top_label_index()
    text = INDEX.read_text(encoding="utf-8")

    audited = 0
    unaudited = 0
    errors: list[str] = []

    for raw in BACKTICK_GROUP.findall(text):
        if "/" in raw:
            continue
        match = LABEL_REF.match(raw)
        if not match:
            continue
        if match.group(4):
            unaudited += 1
            continue

        local = match.group(1) is not None
        label = match.group(2)
        line_no = int(match.group(3))
        audited += 1

        err = (
            check_local_label(label, line_no, raw)
            if local
            else check_top_label(label, line_no, raw, label_index)
        )
        if err is not None:
            errors.append(err)

    rel_index = INDEX.relative_to(ROOT).as_posix()
    print(
        f"Audited {audited} label-anchored line refs in {rel_index}; "
        f"{unaudited} range/comma refs unaudited."
    )

    if errors:
        for err in errors:
            print(f"FAIL: {err}")
        return 1

    print(f"PASS: all label line numbers in {rel_index} match source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
