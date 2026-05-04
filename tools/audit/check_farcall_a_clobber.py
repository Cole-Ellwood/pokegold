#!/usr/bin/env python3
"""Audit cross-bank functions reached via `farcall|callfar` for the `a -> c`
mirror that callers reading `a` post-farcall depend on.

Per home/farcall.asm:13-28, after `farcall` the caller's `a` = target's exit
`c`, NOT target's exit `a`. So functions that "return a value in a" via
farcall must mirror `ld c, a` at every ret, otherwise callers reading `a`
post-farcall get target's exit c (whatever happened to be there) instead of
the intended return value.

This bug class shipped to ROM three times in this repo:
- May 2026 wild-floor no-op (commit 1f5fd6af)
- AG-07: TypePassive_GetUserParalysisFailThreshold_Far returned threshold in
  a; callers compared random vs threshold; check was always-false ->
  paralysis dead. Fixed in commit 769d6dd4.
- AG-08: TypePassive_GetEffectiveMoveCategory_Far / sister returned category
  in a via the home wrapper; callers read category byte; bug was masked by
  callers happening to pass c < SPECIAL=19. Fixed in commit a6a00ea8.

The audit walks every `farcall|callfar TARGET` site, classifies each TARGET
as a-mirror-SAFE or UNSAFE, and flags sites where TARGET is UNSAFE and the
caller consumes `a` within the next few instructions (without an intervening
`a` reset).

CLASSIFICATION:
- For each ret in TARGET's body, walk backward until the first instruction
  that writes to register c.
  - SAFE if that instruction is `ld c, a` (the mirror).
  - UNSAFE otherwise (`pop bc`, `ld c, *`, `inc c`, walked off the function
    start, etc.).
- TARGET is SAFE if every ret is SAFE; UNSAFE if any ret is UNSAFE.

CALLER-SIDE CONSUMPTION:
A site is flagged only if, within ~6 instructions after the farcall, the
caller has an explicit `a` read (cp / arithmetic / `ld R, a` / `ldh [n], a`)
WITHOUT an intervening `a` reset (`ld a, *` / `xor a` / `pop af`). Flag
register reads (`jr c, ...`, `ret nz`, etc.) are NOT consumption -- flags
survive farcall intact.

ALLOWLIST:
Add a TARGET to ALLOWLIST below if it is intentionally not mirror-protected
(e.g. genuinely returns via c/b passthrough, or via flags only). Each entry
needs a one-line justification so future readers can audit the audit.

ADDING A NEW CROSS-BANK A-RETURN FUNCTION:
At every `ret` in the target, ensure the immediately preceding non-c-touching
chain ends in `ld c, a`. The simplest pattern is to add `ld c, a` right
before the ret (or before a trailing `pop`-chain that doesn't touch c -- the
audit walks back through pops/non-c-affecting instructions).

KNOWN LIMITATIONS (v1):
- Tail calls (`jp Label`) are not traced through; functions ending only in
  unconditional `jp` to another label are classified OPAQUE and skipped.
- `jp [hl]` / `jp hl` dispatch is OPAQUE.
- Lookahead from a farcall stops at unconditional jumps and at the next
  top-level label. Conditional jumps fall through.
- The audit does not inspect HOME wrappers transitively. If `Battle_FooBar::`
  is `farcall TypePassive_FooBar_Far :: ret`, the outer wrapper IS analyzed
  (HOME fn body contains the farcall, which IS scanned for a-consumption --
  the trailing `ret` doesn't read a, so callers OF the wrapper aren't flagged
  here; bugs in that shape are caught when AG-08-style fixes are applied at
  the inner target).
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SKIP_DIR_PARTS = {".git", "rgbds-1.0.1", "tools", "scripts", ".local", "workspace", ".claude"}

TOP_LABEL_RE = re.compile(r"^(?P<label>[A-Za-z_][A-Za-z0-9_]*):{1,2}\s*(?:;.*)?$")
SECTION_RE = re.compile(r'^\s*SECTION\s+"', re.IGNORECASE)
FARCALL_RE = re.compile(
    r"^\s*(?P<op>farcall|callfar)\s+(?P<target>[A-Za-z_][A-Za-z0-9_]*)\b"
)
RET_RE = re.compile(r"^\s*ret(?:\s+(?:nz|z|nc|c))?\s*(?:;.*)?$", re.IGNORECASE)

# Instructions that write to register c (clobber prior value).
WRITES_C_RE = re.compile(
    r"^\s*(?:"
    r"ld\s+c\s*,"
    r"|pop\s+bc\b"
    r"|inc\s+c\b"
    r"|dec\s+c\b"
    r"|inc\s+bc\b"
    r"|dec\s+bc\b"
    r"|swap\s+c\b"
    r"|sla\s+c\b|sra\s+c\b|srl\s+c\b"
    r"|rl\s+c\b|rr\s+c\b|rlc\s+c\b|rrc\s+c\b"
    r"|set\s+\w+\s*,\s*c\b"
    r"|res\s+\w+\s*,\s*c\b"
    r")",
    re.IGNORECASE,
)
MIRROR_RE = re.compile(r"^\s*ld\s+c\s*,\s*a\b", re.IGNORECASE)

# Instructions in the caller that read `a` (depending on its value).
# Excludes flag-conditional jumps (flags survive farcall intact).
CONSUMES_A_RE = re.compile(
    r"^\s*(?:"
    r"cp\s+"
    r"|and\s+"
    r"|or\s+"
    r"|xor\s+(?!a\b)"
    r"|add\s+(?!hl\b|sp\b)"
    r"|sub\s+"
    r"|adc\s+"
    r"|sbc\s+(?!hl\b)"
    r"|inc\s+a\b"
    r"|dec\s+a\b"
    r"|ld\s+[bcdehl]\s*,\s*a\b"
    r"|ldh\s+\[[^]]+\]\s*,\s*a\b"
    r"|ld\s+\[[^]]+\]\s*,\s*a\b"
    r"|swap\s+a\b"
    r"|rla\b|rra\b|rlca\b|rrca\b|cpl\b|daa\b"
    r"|bit\s+\w+\s*,\s*a\b"
    r"|set\s+\w+\s*,\s*a\b"
    r"|res\s+\w+\s*,\s*a\b"
    r")",
    re.IGNORECASE,
)
# Instructions in the caller that overwrite `a`, ending the consumption window.
# Any call/rst/farcall/callfar/homecall is conservatively treated as a-reset
# (the callee may clobber a; without per-target preservation contracts we can't
# assume otherwise). This is what makes `farcall X; call SomeOtherThing; ld b, a`
# a false-positive-FREE pattern -- the second call clobbers a before ld b, a.
RESETS_A_RE = re.compile(
    r"^\s*(?:"
    r"ld\s+a\s*,"
    r"|pop\s+af\b"
    r"|xor\s+a\b"
    r"|ldh\s+a\s*,"
    r"|farcall\b"
    r"|callfar\b"
    r"|homecall\b"
    r"|call\b"
    r"|rst\b"
    r")",
    re.IGNORECASE,
)
# Control transfers in the caller -- stop the consumption walk because
# control either leaves the function or branches non-locally.
TRANSFER_STOPS_LOOKAHEAD_RE = re.compile(
    r"^\s*(?:"
    r"jp\b"
    r"|jr\b"
    r"|ret\b"
    r"|reti\b"
    r")",
    re.IGNORECASE,
)
# `and a` / `or a` / `cp 0` are flag-only "tests" of a. When followed
# immediately by an unconditional `ret`, they form the carry-clear idiom
# (clear C, set Z based on a, return). The wrapper's caller may not actually
# read a's value through that flag. Suppress this exact pattern -- it's a
# very common false positive (audit doc 2026-05-03 second-pass scan listed
# it as one of the three false-positive shapes).
FLAG_ONLY_IDIOM_RE = re.compile(
    r"^\s*(?:and\s+a|or\s+a|cp\s+0)\b", re.IGNORECASE
)
UNCONDITIONAL_RET_RE = re.compile(r"^\s*ret\s*(?:;.*)?$", re.IGNORECASE)

# How far past a farcall to look for caller-side consumption.
LOOKAHEAD_INSTRUCTIONS = 6

# Targets known to be intentionally not a-mirror-protected. Each entry needs
# a justification so future readers can verify it stays correct.
ALLOWLIST: dict[str, str] = {
    # Empty by default. If a real false positive surfaces, add it here with
    # a short note about why caller consuming `a` post-farcall is correct
    # (e.g. target intentionally returns the value in c, and caller is reading
    # that c-value via its post-farcall `a` -- see home/farcall.asm:13-28).
}


@dataclass
class Function:
    label: str
    path: Path
    start_line: int  # 1-based line of the label itself
    body: list[str]  # lines AFTER the label, before next top-level / SECTION


@dataclass
class Issue:
    target: str
    target_path: Path
    target_line: int
    target_unsafe_rets: list[int]  # absolute line numbers in target file
    caller_path: Path
    caller_line: int
    caller_consumption: str


def code_part(line: str) -> str:
    return line.split(";", 1)[0].strip()


def iter_asm_files() -> list[Path]:
    files: list[Path] = []
    for p in sorted(ROOT.rglob("*.asm")):
        rel_parts = p.relative_to(ROOT).parts
        if any(part in SKIP_DIR_PARTS for part in rel_parts):
            continue
        files.append(p)
    return files


def collect_functions(files: list[Path]) -> dict[str, Function]:
    """Build label -> Function. Body = lines from the line after the label up
    to (but not including) the next top-level label or SECTION directive."""
    funcs: dict[str, Function] = {}
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        current: Function | None = None
        for i, raw in enumerate(lines):
            if SECTION_RE.match(raw):
                if current is not None:
                    funcs.setdefault(current.label, current)
                current = None
                continue
            m = TOP_LABEL_RE.match(raw)
            if m:
                if current is not None:
                    funcs.setdefault(current.label, current)
                current = Function(
                    label=m["label"],
                    path=path,
                    start_line=i + 1,
                    body=[],
                )
                continue
            if current is not None:
                current.body.append(raw)
        if current is not None:
            funcs.setdefault(current.label, current)
    return funcs


def classify_target(func: Function) -> tuple[str, list[int]]:
    """Return ('SAFE', []) | ('UNSAFE', [unsafe_ret_absolute_line_nos])
    | ('OPAQUE', []).

    SAFE: every ret in the function body has `ld c, a` as the most recent
        instruction that writes to register c (walking back past instructions
        that don't touch c).
    UNSAFE: at least one ret has either no preceding c-write at all, or the
        preceding c-write is something other than `ld c, a`.
    OPAQUE: function has no `ret` at all (likely tail-call only, jump-table,
        or non-function data label).
    """
    body = func.body
    ret_indices: list[int] = []
    for i, raw in enumerate(body):
        if RET_RE.match(raw):
            ret_indices.append(i)

    if not ret_indices:
        return ("OPAQUE", [])

    unsafe_abs_lines: list[int] = []
    for ret_idx in ret_indices:
        safe = False
        for j in range(ret_idx - 1, -1, -1):
            code = code_part(body[j])
            if not code:
                continue
            if WRITES_C_RE.match(code):
                if MIRROR_RE.match(code):
                    safe = True
                break
        if not safe:
            unsafe_abs_lines.append(func.start_line + 1 + ret_idx)

    if unsafe_abs_lines:
        return ("UNSAFE", unsafe_abs_lines)
    return ("SAFE", [])


def is_carry_clear_idiom(file_lines: list[str], idiom_idx: int) -> bool:
    """True if the idiom-line at idiom_idx is followed immediately by an
    unconditional `ret` (the carry-clear-and-return shape)."""
    for j in range(idiom_idx + 1, len(file_lines)):
        raw = file_lines[j]
        if not code_part(raw):
            continue
        return UNCONDITIONAL_RET_RE.match(raw) is not None
    return False


def find_caller_consumption(file_lines: list[str], farcall_idx: int) -> str | None:
    """Look at the next LOOKAHEAD_INSTRUCTIONS non-blank/non-comment lines
    after a farcall. Return the consuming line if `a` is read before any
    `a`-resetting instruction; return None otherwise.

    Special case: `and a` / `or a` / `cp 0` followed immediately by an
    unconditional `ret` is the carry-clear idiom -- suppressed."""
    seen = 0
    for j in range(farcall_idx + 1, len(file_lines)):
        if seen >= LOOKAHEAD_INSTRUCTIONS:
            break
        raw = file_lines[j]
        if TOP_LABEL_RE.match(raw):
            return None
        code = code_part(raw)
        if not code:
            continue
        seen += 1
        if RESETS_A_RE.match(code):
            return None
        if CONSUMES_A_RE.match(code):
            if FLAG_ONLY_IDIOM_RE.match(code) and is_carry_clear_idiom(file_lines, j):
                return None
            return raw.rstrip()
        if TRANSFER_STOPS_LOOKAHEAD_RE.match(code):
            return None
    return None


def main() -> int:
    files = iter_asm_files()
    functions = collect_functions(files)

    issues: list[Issue] = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        for i, raw in enumerate(lines):
            m = FARCALL_RE.match(code_part(raw))
            if not m:
                continue
            target = m["target"]
            if target in ALLOWLIST:
                continue
            target_func = functions.get(target)
            if target_func is None:
                continue  # target defined elsewhere (macro / external) -- skip
            safety, unsafe_lines = classify_target(target_func)
            if safety != "UNSAFE":
                continue
            consumption = find_caller_consumption(lines, i)
            if consumption is None:
                continue
            issues.append(
                Issue(
                    target=target,
                    target_path=target_func.path,
                    target_line=target_func.start_line,
                    target_unsafe_rets=unsafe_lines,
                    caller_path=path,
                    caller_line=i + 1,
                    caller_consumption=consumption,
                )
            )

    if issues:
        by_target: dict[str, list[Issue]] = {}
        for issue in issues:
            by_target.setdefault(issue.target, []).append(issue)
        print("Farcall a-clobber audit FAILED.", file=sys.stderr)
        print(
            "After farcall, caller's `a` = target's exit `c` (see "
            "home/farcall.asm:13-28). Targets that 'return a value in a' "
            "must mirror `ld c, a` at every ret.\n",
            file=sys.stderr,
        )
        for target in sorted(by_target):
            sites = by_target[target]
            ex = sites[0]
            rel_target = ex.target_path.relative_to(ROOT)
            unsafe_str = ", ".join(str(n) for n in ex.target_unsafe_rets)
            print(
                f"Target {target} ({rel_target}:{ex.target_line}) — "
                f"unsafe ret(s) at line(s) {unsafe_str}",
                file=sys.stderr,
            )
            for issue in sites:
                rel_caller = issue.caller_path.relative_to(ROOT)
                print(
                    f"  caller: {rel_caller}:{issue.caller_line}  "
                    f"reads `a` via: {issue.caller_consumption.strip()}",
                    file=sys.stderr,
                )
            print("", file=sys.stderr)
        print(
            "Fix options:\n"
            "  A. Mirror in target: add `ld c, a` immediately before each `ret`\n"
            "     (or anywhere in the trailing pop-chain that doesn't touch c).\n"
            "  B. Stash to HRAM in target, read back in caller via `ldh a, [hX]`.\n"
            "  C. Switch the calling wrapper to `homecall` (preserves a since\n"
            "     it bypasses rst FarCall — see macros/farcall.asm:19-27).\n"
            "If the consumption is intentional (target really returns in c\n"
            "and caller intends to read that), add the target to ALLOWLIST in\n"
            "this script with a one-line justification.",
            file=sys.stderr,
        )
        return 1

    print("Farcall a-clobber audit passed.")
    print(
        f"Scanned {len(files)} ASM files; analyzed {len(functions)} "
        "top-level functions for a/c mirror safety."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
