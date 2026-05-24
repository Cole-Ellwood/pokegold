#!/usr/bin/env python3
"""Audit farcall/callfar sites for both directions of the hl-clobber hazard.

The farcall macro expands to `ld hl, TARGET; ld a, BANK(TARGET); rst FarCall`,
which writes TARGET's address into caller's hl before TARGET runs. FarCall_hl
preserves bc across the bank switch but NOT hl, and the target is free to
clobber hl further. Two directions of bug fall out:

  CALLEE-side (read direction): TARGET reads hl as input. The macro's
  `ld hl, TARGET` overwrites whatever the caller set up; TARGET reads
  garbage. Shipped April 2026 (one-shot damage corruption) and May 2026
  (rival 1 softlock).

  CALLER-side (preserve direction): Caller had hl pointing at a struct
  before the farcall and dereferences it again afterward. The macro
  trashed hl; the post-farcall load reads a garbage address. Shipped
  May 2026 in BattleCommand_Recoil (Pinsir Double Edge HP-bar overflow):
  effect_commands.asm:5562 farcalled the Steel recoil adjuster, then
  immediately did `ld a, [hli]` to start the HP subtract.

Both scans run; failures from either fail the audit.

Callee-side discovery: marker comment in the function's header block:
    ; Reach via ROM0 thunk <ThunkName> — direct callfar would clobber hl.
Fix when flagged: route through a HOME thunk (`homecall` preserves hl),
or pass hl via bc/de and reconstruct inside the target.

Caller-side detection: for each farcall|callfar, walk forward instruction
by instruction until one of (a) hl is read → flag; (b) hl is rewritten →
safe; (c) unconditional flow exit → safe; (d) next top-level label →
safe (function ended). The valid escape patterns are documented in
docs/asm_authoring_guide.md §3.2:
  1. push hl :: farcall :: pop hl                (push/pop bracket)
  2. homecall via ROM0 thunk                     (preserves hl)
  3. reload hl from constant/label after farcall (caller doesn't care
     about pre-farcall hl)
Fix when flagged: usually pattern 1 (cheapest at 2 bytes / 7 cycles).
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

# Caller-side scan tuning.
CALLER_LOOKAHEAD = 30  # lines after farcall to scan for hl read/write/exit

# Matches instructions that fully or partially overwrite hl. Partial writes
# (`ld h, …` / `ld l, …`) are conservatively treated as resets because they
# indicate the caller is reconstructing hl rather than relying on the
# pre-farcall value. `hlcoord` is the canonical screen-coord setter macro
# (expands to `ld hl, _CoordsBase + …`), so it's an hl write at the source
# level. Anchored to start of stripped code so operands like `ld a, h`
# (which READ h, not write it) don't match.
HL_RESET_RE = re.compile(
    r"^(?:"
    r"ld\s+hl\s*,"
    r"|pop\s+hl\b"
    r"|ld\s+h\s*,"
    r"|ld\s+l\s*,"
    r"|hlcoord\b"
    r"|hlbgcoord\b"
    r")",
    re.IGNORECASE,
)

# Matches instructions that read hl. Memory dereferences through `[hl]`,
# `[hli]`, `[hld]` are the dominant shape; `add hl, …`, `inc hl`, `dec hl`,
# `jp hl`, `ld sp, hl` round it out. `push hl` is intentionally NOT here:
# pushing a garbage hl is benign as long as the matching pop discards it,
# and the surrounding push/pop bracket pattern would otherwise false-positive.
HL_READ_RE = re.compile(
    r"\[\s*hl[id]?\s*\]"
    r"|\badd\s+hl\s*,"
    r"|\binc\s+hl\b"
    r"|\bdec\s+hl\b"
    r"|\bjp\s+hl\b"
    r"|\bld\s+sp\s*,\s*hl\b",
    re.IGNORECASE,
)

# Any call-like instruction has unknown hl effects: the target may set hl
# (e.g. _GetSidedHL, GetUserStatusAddr return hl as output), or clobber it,
# or preserve it. The audit can't tell without inspecting every target, so
# it stops scanning here — analyzing past this point would either need a
# per-target hl-effect database (high maintenance) or produce many false
# positives. The cost is missing chained-clobber bugs where two farcalls
# happen back-to-back; those are caught by analyzing the second farcall.
HL_UNKNOWN_RE = re.compile(
    r"^\s*(?:call|callfar|farcall|predef|predef_jump|homecall|jumptable)\b",
    re.IGNORECASE,
)

# Manual extension for hl-input functions whose definitions don't carry the
# marker comment. Empty by default — prefer adding the marker comment to the
# function definition so the audit self-maintains.
EXTRA_HL_INPUT_FUNCS: set[str] = set()

# Functions that intentionally set hl as part of their return contract.
# Farcalls to these targets are treated as hl resets by the caller-side
# scan: a post-farcall hl read is reading the target's documented output.
# Auto-discovered from header comments containing "Returns hl =" or the
# legacy patterns "id at hl" / "address in hl" (case-insensitive). Add to
# EXTRA_HL_OUTPUT_FUNCS only when the function's contract isn't expressible
# as a header comment (e.g. macros).
HL_OUTPUT_MARKER_RE = re.compile(
    r"Returns?\s+hl\s*=|(?:id|address|addr)\s+(?:at|in)\s+hl",
    re.IGNORECASE,
)
EXTRA_HL_OUTPUT_FUNCS: set[str] = {
    # Documented "Return ... at hl" / "Return ... in hl" — header comment
    # auto-discovery covers these, listed here as a backstop.
    "GetUserItem",
    "GetOpponentItem",
    "GetBattleVarAddr",
    "_GetSidedHL",
    # Returns hl one byte past the printed time text — caller continues
    # writing (e.g. main_menu.asm prints ":MM" after the hour).
    "PrintHour",
    # Returns hl pointing at the relevant DV bytes — caller reads two bytes
    # off [hli] / [hl]. Routes through GetPartyLocation for transformed mons.
    "GetEnemyMonDVs",
}

# Caller-side allowlist: farcall sites where reading hl post-call is
# intentional and can't be expressed via the target's header marker (e.g.
# the caller is iterating off a pointer the target set in a sibling reg).
# Add (file, lineno_of_farcall) tuples here only after auditing the target.
CALLER_HL_USE_ALLOWED: set[tuple[str, int]] = set()


@dataclass(frozen=True)
class Issue:
    path: Path
    lineno: int
    line: str
    target: str


def _discover_marker_funcs(files: list[AsmFile], marker_re: re.Pattern, seed: set[str]) -> set[str]:
    """Find function definitions whose header comment block matches
    `marker_re`. The header block ends at the first non-comment,
    non-blank line."""
    found: set[str] = set(seed)
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
                if marker_re.search(lookahead):
                    found.add(label)
                    break
    return found


def discover_hl_input_funcs(files: list[AsmFile]) -> set[str]:
    return _discover_marker_funcs(files, HL_INPUT_MARKER_RE, EXTRA_HL_INPUT_FUNCS)


def discover_hl_output_funcs(files: list[AsmFile]) -> set[str]:
    return _discover_marker_funcs(files, HL_OUTPUT_MARKER_RE, EXTRA_HL_OUTPUT_FUNCS)


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


def _is_unconditional_exit(code: str) -> bool:
    """Return True if `code` ends the straight-line flow (no fallthrough)."""
    c = code.strip().lower()
    if not c:
        return False
    parts = c.split(None, 1)
    op = parts[0]
    rest = parts[1] if len(parts) > 1 else ""
    if op in ("ret", "reti"):
        # `ret` / `reti` alone = unconditional; `ret z` / `ret nc` etc. = conditional
        return rest == ""
    if op in ("jp", "jr"):
        first = rest.split(",", 1)[0].strip().lower()
        return first not in ("nz", "z", "nc", "c")
    return False


def scan_caller_hl_clobber(files: list[AsmFile], hl_outputs: set[str]) -> list[Issue]:
    """Flag farcall|callfar sites where hl is read after the call without
    being rewritten first. The farcall macro's `ld hl, target` clobbers
    caller's hl before the rst, and FarCall_hl does not restore it; any
    post-call read of hl reads garbage.

    Straight-line analysis: walk forward from each farcall until one of
      (a) hl is rewritten     → safe, stop
      (b) hl is read           → flag, stop
      (c) unconditional exit   → safe (no fallthrough), stop
      (d) next top-level label → safe (function ended), stop
      (e) `CALLER_LOOKAHEAD` lines exhausted → safe (probably), stop
    Local labels (`.foo`) are walked through; the function continues.
    """
    issues: list[Issue] = []
    for asm_file in files:
        path = asm_file.path
        rel_str = str(path.relative_to(ROOT)).replace("\\", "/")
        lines = asm_file.lines
        for i, raw in enumerate(lines):
            code = raw.split(";", 1)[0]
            m = FARCALL_RE.match(code)
            if not m:
                continue
            if (rel_str, i + 1) in CALLER_HL_USE_ALLOWED:
                continue
            target = m["target"]
            # Target is documented to return hl; using hl after is intended.
            if target in hl_outputs:
                continue
            stop = min(i + 1 + CALLER_LOOKAHEAD, len(lines))
            for j in range(i + 1, stop):
                next_raw = lines[j]
                next_code = next_raw.split(";", 1)[0].strip()
                if not next_code:
                    continue
                # New top-level function definition = previous function ended.
                if LABEL_RE.match(next_code):
                    break
                # Unconditional flow exit = no fallthrough that could use hl.
                if _is_unconditional_exit(next_code):
                    break
                # Another call-like instruction has unknown hl effects;
                # stop scanning. See HL_UNKNOWN_RE doc for the trade-off.
                if HL_UNKNOWN_RE.match(next_code):
                    break
                # hl reset (write before read) = safe.
                if HL_RESET_RE.match(next_code):
                    break
                # hl read with no prior reset = the bug.
                if HL_READ_RE.search(next_code):
                    issues.append(Issue(
                        path=path,
                        lineno=i + 1,
                        line=raw.rstrip(),
                        target=target,
                    ))
                    break
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
    hl_outputs = discover_hl_output_funcs(files)
    callee_issues = scan_farcall_violations(files, hl_inputs)
    caller_issues = scan_caller_hl_clobber(files, hl_outputs)
    failed = False
    if callee_issues:
        failed = True
        print("Farcall hl-clobber audit FAILED (callee-side).", file=sys.stderr)
        print(
            f"Functions known to read hl as input: {sorted(hl_inputs)}",
            file=sys.stderr,
        )
        for issue in callee_issues:
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
    if caller_issues:
        failed = True
        print("Farcall hl-clobber audit FAILED (caller-side).", file=sys.stderr)
        for issue in caller_issues:
            rel = issue.path.relative_to(ROOT)
            print(
                f"{rel}:{issue.lineno}: farcall/callfar to {issue.target!r} "
                f"is followed by an hl read with no intervening reset",
                file=sys.stderr,
            )
            print(f"  {issue.line}", file=sys.stderr)
        print(
            "fix: bracket with `push hl` / `pop hl`, or reload hl from a "
            "constant/label after the farcall (see docs/asm_authoring_guide.md §3.2).",
            file=sys.stderr,
        )
    if failed:
        return 1
    print("Farcall hl-clobber audit passed.")
    print(f"Functions known to read hl as input: {sorted(hl_inputs)}")
    print(f"Functions known to return hl as output: {len(hl_outputs)} ({sorted(hl_outputs)[:6]}…)" if len(hl_outputs) > 6 else f"Functions known to return hl as output: {sorted(hl_outputs)}")
    print(f"Scanned {len(files)} ASM files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
