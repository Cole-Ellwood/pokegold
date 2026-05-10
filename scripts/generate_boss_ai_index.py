#!/usr/bin/env python3
"""Regenerate Boss AI source citations in the logic micro-index."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "agent_navigation" / "subsystems" / "boss_ai_logic.md"

BOSS_SOURCE_FILES = (
    ROOT / "engine" / "battle" / "ai" / "boss_platform.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_policy_move.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_policy_switch.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_data.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_thunks.asm",
)

TOP_LABEL_RE = re.compile(r"^([A-Za-z_]\w*)::?")
LOCAL_LABEL_RE = re.compile(r"^\.([A-Za-z_]\w*)")
RAW_LABEL_REF_RE = re.compile(
    r"`(?P<label>\.?[A-Za-z_]\w*):(?P<line>\d+)(?P<suffix>[-,]\d+(?:[-,]\d+)*)?`"
)
GENERATED_REF_RE = re.compile(
    r"`(?P<label>\.?[A-Za-z_]\w*)`\s+\(`(?P<path>[^`]+):(?P<line>\d+)(?P<suffix>-\d+)?`\)"
)


@dataclass(frozen=True)
class Location:
    path: Path
    line: int

    def citation(self, label: str, suffix: str = "") -> str:
        rel = self.path.relative_to(ROOT).as_posix()
        return f"`{label}` (`{rel}:{self.line}`)"


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def build_boss_label_index() -> dict[str, Location]:
    index: dict[str, Location] = {}
    local_index: dict[str, list[Location]] = {}
    for path in BOSS_SOURCE_FILES:
        for line_no, line in enumerate(read_lines(path), start=1):
            top = TOP_LABEL_RE.match(line)
            local = LOCAL_LABEL_RE.match(line)
            if top:
                index[top.group(1)] = Location(path, line_no)
                continue
            if local:
                local_index.setdefault(f".{local.group(1)}", []).append(
                    Location(path, line_no)
                )
    for label, locations in local_index.items():
        if len(locations) == 1:
            index[label] = locations[0]
    return index


def update_generated_refs(text: str, labels: dict[str, Location]) -> str:
    def replace(match: re.Match[str]) -> str:
        label = match.group("label")
        loc = labels.get(label)
        if loc is None:
            return match.group(0)
        return loc.citation(label, match.group("suffix") or "")

    return GENERATED_REF_RE.sub(replace, text)


def update_raw_refs(text: str, labels: dict[str, Location]) -> str:
    def replace(match: re.Match[str]) -> str:
        label = match.group("label")
        loc = labels.get(label)
        if loc is None:
            return match.group(0)
        return loc.citation(label, match.group("suffix") or "")

    return RAW_LABEL_REF_RE.sub(replace, text)


def generate() -> str:
    labels = build_boss_label_index()
    text = INDEX.read_text(encoding="utf-8")
    text = update_generated_refs(text, labels)
    text = update_raw_refs(text, labels)
    text = text.replace(
        "All Boss AI implementation paths are cited per split source file below.",
        "Boss AI paths are cited per split source file below.",
    )
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stdout", action="store_true", help="print generated index")
    parser.add_argument("--check", action="store_true", help="check without writing")
    args = parser.parse_args()

    generated = generate()
    if args.stdout:
        sys.stdout.buffer.write(generated.encode("utf-8"))
        return 0
    if args.check:
        current = INDEX.read_text(encoding="utf-8")
        if current != generated:
            print(f"FAIL: {INDEX.relative_to(ROOT).as_posix()} is stale")
            return 1
        print(f"PASS: {INDEX.relative_to(ROOT).as_posix()} matches generator output")
        return 0
    INDEX.write_text(generated, encoding="utf-8")
    print(f"wrote {INDEX.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
