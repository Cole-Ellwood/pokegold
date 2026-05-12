#!/usr/bin/env python3
"""Audit farcall/callfar sites against functions that read hl as input.

The farcall macro expands to `ld hl, TARGET; ld a, BANK(TARGET); rst FarCall`,
which clobbers caller's hl with TARGET's address before TARGET runs. If TARGET
reads hl as input, the farcall silently passes garbage. This bug class shipped
to ROM twice (April 2026 one-shot damage corruption, May 2026 rival 1 softlock);
CLAUDE.md documents the gotcha but the only enforcement was code review.

The audit:
  1. Discovers hl-input functions by their canonical marker comment
     (`; Reach via ROM0 thunk ...`) within the function's header comment block.
  2. Flags any `farcall|callfar TARGET` where TARGET is in that set.

Fix when flagged: route through a HOME thunk that uses `homecall` (which
preserves hl), or pass the hl value via bc/de and reconstruct inside the
target. There is no safe form of `farcall|callfar` to an hl-input target —
push/pop only protects the caller's hl across the call, not the value
TARGET reads on entry.

Adding a new hl-input function: add the marker comment
    ; Reach via ROM0 thunk <ThunkName> — direct callfar would clobber hl.
to the function's header. The audit auto-discovers it on the next run.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from asm_scan import AsmFile, ROOT, iter_asm_files

LABEL_RE = re.compile(r"^(?P<label>[A-Za-z_][A-Za-z0-9_]*):{1,2}\s*(?:;.*)?$")
FARCALL_RE = re.compile(
    r"^\s*(?P<op>farcall|callfar)\s+(?P<target>[A-Za-z_][A-Za-z0-9_]*)\b"
)
HL_INPUT_MARKER_RE = re.compile(r"Reach\s+via\s+ROM0\s+thunk", re.IGNORECASE)
HEADER_LOOKAHEAD = 16

# Manual extension for hl-input functions whose definitions don't carry the
# marker comment. Empty by default — prefer adding the marker comment to the
# function definition so the audit self-maintains.
EXTRA_HL_INPUT_FUNCS: set[str] = set()


@dataclass(frozen=True)
class Issue:
    path: Path
    lineno: int
    line: str
    target: str


def discover_hl_input_funcs(files: list[AsmFile]) -> set[str]:
    """Find function definitions whose header comment block carries the
    `Reach via ROM0 thunk` marker. The header block ends at the first
    non-comment, non-blank line."""
    found: set[str] = set(EXTRA_HL_INPUT_FUNCS)
    for asm_file in files:
        lines = asm_file.lines
        for i, line in enumerate(lines):
            m = LABEL_RE.match(line)
            if not m:
                continue
            label = m["label"]
            for lookahead in lines[i + 1 : i + 1 + HEADER_LOOKAHEAD]:
                stripped = lookahead.strip()
                if not stripped:
                    continue
                if not stripped.startswith(";"):
                    break
                if HL_INPUT_MARKER_RE.search(lookahead):
                    found.add(label)
                    break
    return found


def scan_farcall_violations(files: list[AsmFile], hl_inputs: set[str]) -> list[Issue]:
    issues: list[Issue] = []
    for asm_file in files:
        path = asm_file.path
        lines = asm_file.lines
        for i, raw in enumerate(lines):
            code = raw.split(";", 1)[0]
            m = FARCALL_RE.match(code)
            if not m:
                continue
            target = m["target"]
            if target in hl_inputs:
                issues.append(
                    Issue(path=path, lineno=i + 1, line=raw.rstrip(), target=target)
                )
    return issues


def main() -> int:
    files = iter_asm_files()
    hl_inputs = discover_hl_input_funcs(files)
    if not hl_inputs:
        print(
            "ERROR: no hl-input functions discovered — marker convention broken?",
            file=sys.stderr,
        )
        print(
            "Expected at least SpeciesItemBoost_Far and ApplyLateGenDamageStatsItemMods_Far.",
            file=sys.stderr,
        )
        return 1
    issues = scan_farcall_violations(files, hl_inputs)
    if issues:
        print("Farcall hl-clobber audit FAILED.", file=sys.stderr)
        print(
            f"Functions known to read hl as input: {sorted(hl_inputs)}",
            file=sys.stderr,
        )
        for issue in issues:
            rel = issue.path.relative_to(ROOT)
            print(
                f"{rel}:{issue.lineno}: farcall/callfar to {issue.target!r} clobbers hl before entry",
                file=sys.stderr,
            )
            print(f"  {issue.line}", file=sys.stderr)
        print(
            "fix: route through a HOME thunk that uses `homecall`, or pass via bc/de.",
            file=sys.stderr,
        )
        return 1
    print("Farcall hl-clobber audit passed.")
    print(f"Functions known to read hl as input: {sorted(hl_inputs)}")
    print(f"Scanned {len(files)} ASM files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
