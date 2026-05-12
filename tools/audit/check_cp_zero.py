#!/usr/bin/env python3
"""Audit `cp 0` sites that should be `and a` (guide §3.9, AG-05).

`and a` is 1 byte / 1 cycle; `cp 0` is 2 bytes / 2 cycles. Both leave A
unchanged and produce identical Z and C:

  cp 0  -> A unchanged, Z = (A == 0), C = 0, N = 1, H = 0
  and a -> A unchanged, Z = (A == 0), C = 0, N = 0, H = 1

The Z/C-reading callers (`jr z/nz/c/nc`, `ret cc`, `adc`, `sbc`, etc.)
are unaffected by the substitution. The functional difference is N and H:
  cp 0  preserves nothing -- writes N=1, H=0
  and a writes N=0, H=1

Only `daa` reads N or H. So `cp 0` -> `and a` is safe IFF no `daa`
consumes the post-site N/H before any other flag-touching op overwrites
it. Almost every arithmetic/logic/shift/rotate kills N, so the dependency
window is short.

Algorithm (forward walk from each `cp 0` site):
  state = (n_alive,) = (True,)
  for each subsequent instruction (skipping comments/blanks):
    1. if instr is `daa`                  -> UNSAFE (reads N/H)
    2. if instr KILLS N (arith/logic/...) -> SAFE  (post-site N gone)
    3. if instr is unconditional jp/jr/ret/reti -> SAFE (no fall-through)
    4. if next line is a label / SECTION  -> UNSAFE (other code may branch in)
    5. otherwise (ld, push, pop-non-af, conditional jp/jr/call/ret,
       inc/dec r16, set/res, nop, scf, ccf) -> continue walking
    6. budget exhausted (WALK_BUDGET steps) -> INDETERMINATE

N-killers (the SAFE-confirming set):
  add/adc/sub/sbc/and/or/xor/cp  -- N=0 or N=1
  inc/dec r8 / inc/dec [hl]      -- N=0 (inc) or N=1 (dec)
  rlca/rrca/rla/rra              -- N=0
  CB-prefix shifts/rotates/swap  -- N=0
  bit n, r                       -- N=0
  cpl                            -- N=1
  add hl, r16 / add sp, e8 / ld hl, sp+e8  -- N=0
  pop af                         -- loads N from stack
  call / rst / farcall / callfar / homecall  -- callee leaves arbitrary N

N-preservers (continue the walk):
  ld / ldh / push / pop (!af)
  jp / jr / call / ret / reti  (unconditional or conditional; conditional
    reads Z or C but writes nothing)
  nop / halt / stop / di / ei
  inc/dec r16 / ld sp, hl
  set / res
  scf / ccf  (touch only C)

ALLOWLIST: a site can be marked intentionally-keep with a trailing
`; keep cp 0` comment (case-insensitive; matches `; keep` anywhere in
the comment). Useful for cases where the explicit `cp 0` reads better.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from asm_scan import (
    ROOT,
    TOP_LABEL_RE,
    LOCAL_LABEL_RE,
    SECTION_RE,
    code_part,
    has_keep_marker,
    iter_asm_files,
)

# `cp 0`, `cp $0`, `cp $00`. Decimal `0` and hex `$0`/`$00` only -- larger
# literals (`$01`, `1`, ...) are real comparisons, not no-ops.
CP_ZERO_RE = re.compile(
    r"^(?P<indent>\s*)cp\s+(?:0|\$0{1,2})\s*(?P<tail>;.*)?$",
    re.IGNORECASE,
)
# --- Reads ---
# `daa` is the only instruction that reads N (and H).
READS_N_RE = re.compile(r"^\s*daa\b", re.IGNORECASE)

# --- Kills ---
# Kills N: every 8-bit arith/logic, all CB shifts/rotates, inc/dec r8,
# inc/dec [hl], bit, rlca/rrca/rla/rra, cpl, add hl/sp, ld hl,sp+e8,
# pop af, call-class. NOT killed by: ld, ldh, push/pop (non-af),
# jp/jr/ret (cond or uncond), set/res, nop, scf, ccf, inc/dec r16.
KILLS_N_RE = re.compile(
    r"^\s*(?:"
    r"add\s+(?:a|[bcdehl]|\[hl\]|\$|-?\d|\w)"
    r"|adc\b|sub\b|sbc\b|and\b|or\b|xor\b|cp\b"
    r"|inc\s+(?:[abcdehl]|\[hl\])\b"
    r"|dec\s+(?:[abcdehl]|\[hl\])\b"
    r"|rlca\b|rrca\b|rla\b|rra\b"
    r"|sla\s+(?:[abcdehl]|\[hl\])\b"
    r"|sra\s+(?:[abcdehl]|\[hl\])\b"
    r"|srl\s+(?:[abcdehl]|\[hl\])\b"
    r"|rlc\s+(?:[abcdehl]|\[hl\])\b"
    r"|rrc\s+(?:[abcdehl]|\[hl\])\b"
    r"|rl\s+(?:[abcdehl]|\[hl\])\b"
    r"|rr\s+(?:[abcdehl]|\[hl\])\b"
    r"|swap\s+(?:[abcdehl]|\[hl\])\b"
    r"|bit\b"
    r"|cpl\b"
    r"|add\s+hl\b"
    r"|add\s+sp\b"
    r"|ld\s+hl\s*,\s*sp"
    r"|pop\s+af\b"
    r"|call\b|rst\b|farcall\b|callfar\b|homecall\b"
    r")",
    re.IGNORECASE,
)

# Unconditional control transfer -- ends fall-through dependency.
UNCOND_TRANSFER_RE = re.compile(
    r"^\s*(?:"
    r"jp\s+(?!n?z\b|n?c\b)"
    r"|jr\s+(?!n?z\b|n?c\b)"
    r"|reti?\s*(?:;.*)?$"
    r")",
    re.IGNORECASE,
)

WALK_BUDGET = 16


@dataclass
class Site:
    path: Path
    line_idx: int
    line_no: int
    raw: str
    classification: str = "UNKNOWN"
    reason: str = ""
    has_keep_marker: bool = False


def classify_site(lines: list[str], site_idx: int) -> tuple[str, str]:
    """Forward walk. Return (classification, reason) where classification is
    one of SAFE, UNSAFE, INDETERMINATE."""
    seen = 0
    for j in range(site_idx + 1, len(lines)):
        if seen >= WALK_BUDGET:
            return ("INDETERMINATE", f"walked {WALK_BUDGET} instrs without resolution")
        raw = lines[j]
        code = code_part(raw)
        if not code:
            continue
        # Label boundary: another path may branch in carrying its own N.
        if TOP_LABEL_RE.match(raw) or LOCAL_LABEL_RE.match(raw):
            return ("UNSAFE", f"label boundary at line {j + 1}")
        if SECTION_RE.match(raw):
            return ("UNSAFE", f"SECTION boundary at line {j + 1}")
        seen += 1
        # Reads BEFORE kills -- daa reads N then writes its own.
        if READS_N_RE.match(code):
            return ("UNSAFE", f"reads N via `{code}` at line {j + 1}")
        # N killed -> any subsequent daa reads post-instr N, not site's.
        if KILLS_N_RE.match(code):
            return ("SAFE", f"N overwritten by line {j + 1}: `{code}`")
        # Unconditional transfer -> no further fall-through.
        if UNCOND_TRANSFER_RE.match(code):
            return ("SAFE", f"control transfer `{code}` at line {j + 1}")
    return ("INDETERMINATE", "fell off file end")


def collect_sites() -> list[Site]:
    sites: list[Site] = []
    for asm_file in iter_asm_files():
        path = asm_file.path
        lines = asm_file.lines
        for i, raw in enumerate(lines):
            m = CP_ZERO_RE.match(raw)
            if not m:
                continue
            site = Site(
                path=path,
                line_idx=i,
                line_no=i + 1,
                raw=raw,
                has_keep_marker=has_keep_marker(raw),
            )
            site.classification, site.reason = classify_site(lines, i)
            sites.append(site)
    return sites


def apply_codemod(sites: list[Site]) -> int:
    """Rewrite each SAFE site's `cp 0` (or `cp $0`/`cp $00`) to `and a`,
    preserving the line's indent and any trailing comment. Skip
    UNSAFE / INDETERMINATE / keep-marked sites."""
    by_path: dict[Path, list[Site]] = {}
    for s in sites:
        if s.classification != "SAFE" or s.has_keep_marker:
            continue
        by_path.setdefault(s.path, []).append(s)
    changed = 0
    for path, path_sites in by_path.items():
        text = path.read_text(encoding="utf-8", errors="replace")
        if "\r\n" in text:
            newline = "\r\n"
            lines = text.split("\r\n")
        else:
            newline = "\n"
            lines = text.split("\n")
        for s in path_sites:
            old_line = lines[s.line_idx]
            m = CP_ZERO_RE.match(old_line)
            if not m:
                print(
                    f"SKIP {path.relative_to(ROOT)}:{s.line_no} -- line "
                    f"text changed since classification",
                    file=sys.stderr,
                )
                continue
            indent = m["indent"] or ""
            tail = m["tail"] or ""
            new_line = f"{indent}and a"
            if tail:
                new_line += f" {tail}"
            lines[s.line_idx] = new_line
            changed += 1
        path.write_text(newline.join(lines), encoding="utf-8")
    print(f"Codemod applied: {changed} `cp 0` -> `and a` rewrites across "
          f"{len(by_path)} file(s).")
    return 0


def main() -> int:
    sites = collect_sites()
    safe = [s for s in sites if s.classification == "SAFE" and not s.has_keep_marker]
    unsafe = [s for s in sites if s.classification == "UNSAFE"]
    indet = [s for s in sites if s.classification == "INDETERMINATE"]
    kept = [s for s in sites if s.has_keep_marker]

    if "--apply" in sys.argv:
        return apply_codemod(sites)

    if "--list" in sys.argv:
        for s in sorted(sites, key=lambda x: (x.path, x.line_no)):
            rel = s.path.relative_to(ROOT)
            tag = s.classification + (" [keep]" if s.has_keep_marker else "")
            print(f"{rel}:{s.line_no} {tag} -- {s.reason}")
        print(
            f"\nTotal: {len(sites)} sites "
            f"({len(safe)} SAFE, {len(unsafe)} UNSAFE, "
            f"{len(indet)} INDETERMINATE, {len(kept)} keep-marked)",
            file=sys.stderr,
        )
        return 0

    if safe:
        print("`cp 0` audit FAILED.", file=sys.stderr)
        print(
            f"{len(safe)} site(s) can safely be `and a` (1 byte vs 2, "
            "identical resulting A and Z/C; only N/H differ and no `daa` "
            "reads them within reach). Replace, or add a `; keep` comment "
            "marker to suppress.\n",
            file=sys.stderr,
        )
        for s in sorted(safe, key=lambda x: (x.path, x.line_no)):
            rel = s.path.relative_to(ROOT)
            print(f"  {rel}:{s.line_no}  -- {s.reason}", file=sys.stderr)
        print(
            f"\nSummary: {len(sites)} sites total "
            f"({len(safe)} SAFE, {len(unsafe)} UNSAFE, "
            f"{len(indet)} INDETERMINATE, {len(kept)} keep-marked)",
            file=sys.stderr,
        )
        return 1

    print("`cp 0` audit passed.")
    print(
        f"Scanned {len(sites)} `cp 0` site(s); "
        f"{len(unsafe)} flag-preserving (kept), "
        f"{len(indet)} indeterminate (kept), "
        f"{len(kept)} keep-marked."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
