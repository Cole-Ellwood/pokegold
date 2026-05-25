"""Shared paths, regexes, and asm-block helpers for the trace-invariants audit family.

Extracted from `check_boss_ai_trace_invariants.py` per
`audit/non_debugger_code_review_2026-05-26.md` §2 item #8. The three sibling
modules (`trace_rom.py`, `trace_coverage.py`, `trace_logic.py`) import from
here so they can share the same asm-block parsing primitives without
duplicating them or pulling them through one of the audit families.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import fail, load, strip_comment


ROOT = Path(__file__).resolve().parents[2]

BOSS_FILES = (
    ROOT / "engine" / "battle" / "ai" / "boss_platform.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_policy_move.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_policy_switch.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_thunks.asm",
)
BOSS_TRACE_TOPMOVES = ROOT / "engine" / "battle" / "ai" / "boss_trace_topmoves.asm"
ITEMS = ROOT / "engine" / "battle" / "ai" / "items.asm"
SCORING = ROOT / "engine" / "battle" / "ai" / "scoring.asm"
SWITCH = ROOT / "engine" / "battle" / "ai" / "switch.asm"
WRAM = ROOT / "ram" / "wram.asm"
PARTIES = ROOT / "data" / "trainers" / "parties.asm"
AI_TIERS = ROOT / "data" / "trainers" / "ai_tiers.asm"
CONSTANTS = ROOT / "constants" / "battle_constants.asm"
CORE = ROOT / "engine" / "battle" / "core.asm"

TOP_LABEL_RE = re.compile(r"^[A-Za-z0-9_]+:{1,2}\s*(?:;.*)?$")
ADD_RE = re.compile(r"\badd\s+(\d+)\b")


def load_boss_source() -> str:
    return "\n".join(load(path) for path in BOSS_FILES)


def top_block(text: str, label: str) -> str:
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() in {f"{label}:", f"{label}::"}:
            start = i
            break
    if start is None:
        fail(f"missing label: {label}")

    end = len(lines)
    for i in range(start + 1, len(lines)):
        if TOP_LABEL_RE.match(strip_comment(lines[i]).strip()):
            end = i
            break
    return "\n".join(lines[start:end])


def local_block(text: str, label: str, end_label: str) -> str:
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        stripped = strip_comment(line).strip()
        if stripped in {label, f"{label}:"}:
            start = i
            break
    if start is None:
        fail(f"missing local label: {label}")

    end = None
    for i in range(start + 1, len(lines)):
        stripped = strip_comment(lines[i]).strip()
        if stripped in {end_label, f"{end_label}:"}:
            end = i
            break
    if end is None:
        fail(f"missing local block end {end_label} after {label}")
    return "\n".join(lines[start:end])


def require_contains(block: str, needle: str, context: str) -> None:
    if needle not in block:
        fail(f"{context}: missing `{needle}`")


def require_not_contains(block: str, needle: str, context: str) -> None:
    if needle in block:
        fail(f"{context}: must not contain `{needle}`")


def require_order(block: str, needles: list[str], context: str) -> None:
    pos = -1
    for needle in needles:
        nxt = block.find(needle, pos + 1)
        if nxt < 0:
            fail(f"{context}: missing `{needle}` in required order")
        pos = nxt


def first_add_value(block: str, context: str) -> int:
    match = ADD_RE.search(block)
    if not match:
        fail(f"{context}: missing add immediate")
    return int(match.group(1))
