#!/usr/bin/env python3
"""Audit `ld a, 0` sites that should be `xor a` (guide §3.9, AG-04).

`xor a` is 1 byte / 1 cycle; `ld a, 0` is 2 bytes / 2 cycles. Both leave
A=0. The functional difference is FLAGS:
  ld a, 0 — preserves Z, N, H, C
  xor a   — sets Z=1, clears N, H, C

So `ld a, 0` -> `xor a` is safe IFF no subsequent flag-reading instruction
can observe a flag that was set BEFORE the `ld a, 0` and that `xor a` would
overwrite. In practice we track Z and C (the two flags real code reads via
`jr z/nz/c/nc`, `ret cc`, `adc`, `sbc`, `daa`, `ccf`). N and H are
overwritten by every flag-touching op and are essentially never read.

Algorithm (forward walk from each `ld a, 0`):
  state = (z_alive, c_alive) = (True, True)
  for each subsequent instruction (skipping comments/blanks):
    1. if z_alive and instr READS Z      -> UNSAFE (consumes pre-`ld a, 0` Z)
    2. if c_alive and instr READS C      -> UNSAFE (consumes pre-`ld a, 0` C)
    3. if instr KILLS Z: z_alive = False
    4. if instr KILLS C: c_alive = False
    5. if not z_alive and not c_alive    -> SAFE  (no surviving dependency)
    6. if instr is unconditional jp/jr/ret/reti -> SAFE
    7. if next line is a label / SECTION -> UNSAFE (other code may branch in)
    8. budget exhausted (WALK_BUDGET steps) -> INDETERMINATE (treat as UNSAFE)

Instructions and their effects (the ones that matter):
                                READS    KILLS    PRESERVES
  ld / ldh / push / pop (!af)   -        -        Z, C
  pop af                        -        Z, C     -        (loads from stack)
  ld hl, sp+e8 / add sp, e8     -        Z, C     -
  inc/dec r16 / ld sp, hl       -        -        Z, C
  inc/dec r8 / inc/dec [hl]     -        Z        C        (preserves C!)
  bit n, r                      -        Z        C        (preserves C!)
  cpl                           -        -        Z, C     (preserves both!)
  scf                           -        C        Z        (preserves Z!)
  ccf                           C        C        Z        (reads C, preserves Z)
  add a,*  add [hl]  add d8     -        Z, C     -
  adc a,*                       C        Z, C     -        (reads C; UNSAFE if c_alive)
  sub  sbc  and  or  xor  cp    -|C      Z, C     -        (sbc reads C)
  daa                           N,H,C    Z, C     -        (reads N/H/C; UNSAFE if c_alive)
  rlca / rrca                   -        Z, C     -
  rla / rra                     C        Z, C     -        (reads C; UNSAFE if c_alive)
  rlc/rrc r                     -        Z, C     -
  rl/rr r                       C        Z, C     -        (reads C; UNSAFE if c_alive)
  sla/sra/srl r / swap r        -        Z, C     -
  add hl, r16                   -        C        Z        (preserves Z!)
  jp/jr Label                   -        -        Z, C     (unconditional: SAFE boundary)
  ret / reti                    -        -        Z, C     (unconditional: SAFE boundary)
  jp/jr/call/ret z/nz           Z        -        -        (UNSAFE if z_alive)
  jp/jr/call/ret c/nc           C        -        -        (UNSAFE if c_alive)
  call / rst / farcall / callfar / homecall
                                -        Z, C     -        (callee-clobbers; SAFE boundary)
  set/res n,r                   -        -        Z, C
  nop / halt / stop / di / ei   -        -        Z, C

DESIGN NOTE: this audit doubles as a one-shot codemod helper AND ongoing
drift catch. After the codemod ships, every remaining `ld a, 0` site
should be UNSAFE (flag-preserving on purpose) -- those stay. The audit
fails if any new SAFE site appears.

ALLOWLIST: a site can be marked intentionally-keep with a trailing
`; keep ld a, 0` comment (case-insensitive; matches `; keep` anywhere
in the comment).
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SKIP_DIR_PARTS = {".git", "rgbds-1.0.1", "tools", "scripts", ".local", "workspace", ".claude"}

LD_A_ZERO_RE = re.compile(r"^(?P<indent>\s*)ld\s+a\s*,\s*0\s*(?P<tail>;.*)?$", re.IGNORECASE)
TOP_LABEL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*:{1,2}\s*(?:;.*)?$")
LOCAL_LABEL_RE = re.compile(r"^\s*\.[A-Za-z_][A-Za-z0-9_]*:?\s*(?:;.*)?$")
SECTION_RE = re.compile(r"^\s*SECTION\s+\"", re.IGNORECASE)

# --- Reads ---
READS_Z_RE = re.compile(r"^\s*(?:jp|jr|call|ret)\s+n?z\b", re.IGNORECASE)
READS_C_RE = re.compile(
    r"^\s*(?:"
    r"(?:jp|jr|call|ret)\s+n?c\b"
    r"|adc\b"
    r"|sbc\b"
    r"|rla\b|rra\b"
    r"|rl\s+(?:[abcdehl]|\[hl\])\b"
    r"|rr\s+(?:[abcdehl]|\[hl\])\b"
    r"|daa\b"
    r"|ccf\b"
    r")",
    re.IGNORECASE,
)

# --- Kills ---
# Kills Z: any 8-bit arith/logic, all CB shifts/rotates, inc/dec r8,
# inc/dec [hl], bit, rlca/rrca/rla/rra, daa, sp arithmetic, pop af, call.
KILLS_Z_RE = re.compile(
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
    r"|daa\b"
    r"|add\s+sp\b"
    r"|ld\s+hl\s*,\s*sp"
    r"|pop\s+af\b"
    r"|call\b|rst\b|farcall\b|callfar\b|homecall\b"
    r")",
    re.IGNORECASE,
)
# Kills C: any 8-bit arith/logic, CB shifts/rotates (incl swap), rotates,
# daa, add hl, r16, sp arithmetic, scf, ccf, pop af, call.
# NOT killed by inc/dec r8, bit, cpl.
KILLS_C_RE = re.compile(
    r"^\s*(?:"
    r"add\s+(?:a|[bcdehl]|\[hl\]|\$|-?\d|\w)"
    r"|adc\b|sub\b|sbc\b|and\b|or\b|xor\b|cp\b"
    r"|rlca\b|rrca\b|rla\b|rra\b"
    r"|sla\s+(?:[abcdehl]|\[hl\])\b"
    r"|sra\s+(?:[abcdehl]|\[hl\])\b"
    r"|srl\s+(?:[abcdehl]|\[hl\])\b"
    r"|rlc\s+(?:[abcdehl]|\[hl\])\b"
    r"|rrc\s+(?:[abcdehl]|\[hl\])\b"
    r"|rl\s+(?:[abcdehl]|\[hl\])\b"
    r"|rr\s+(?:[abcdehl]|\[hl\])\b"
    r"|swap\s+(?:[abcdehl]|\[hl\])\b"
    r"|daa\b"
    r"|add\s+hl\b"
    r"|add\s+sp\b"
    r"|ld\s+hl\s*,\s*sp"
    r"|scf\b|ccf\b"
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


def code_part(line: str) -> str:
    return line.split(";", 1)[0].strip()


def has_keep_marker(line: str) -> bool:
    if ";" not in line:
        return False
    comment = line.split(";", 1)[1].lower()
    return "keep" in comment


def iter_asm_files() -> list[Path]:
    files: list[Path] = []
    for p in sorted(ROOT.rglob("*.asm")):
        rel_parts = p.relative_to(ROOT).parts
        if any(part in SKIP_DIR_PARTS for part in rel_parts):
            continue
        files.append(p)
    return files


def classify_site(lines: list[str], site_idx: int) -> tuple[str, str]:
    """Forward walk. Return (classification, reason) where classification is
    one of SAFE, UNSAFE, INDETERMINATE."""
    z_alive = True
    c_alive = True
    seen = 0
    for j in range(site_idx + 1, len(lines)):
        if seen >= WALK_BUDGET:
            return ("INDETERMINATE", f"walked {WALK_BUDGET} instrs without resolution")
        raw = lines[j]
        code = code_part(raw)
        if not code:
            continue
        # Label boundary: another path may branch in.
        if TOP_LABEL_RE.match(raw) or LOCAL_LABEL_RE.match(raw):
            return ("UNSAFE", f"label boundary at line {j + 1}")
        if SECTION_RE.match(raw):
            return ("UNSAFE", f"SECTION boundary at line {j + 1}")
        seen += 1
        # Check reads BEFORE kills (an instruction can both read and write).
        if z_alive and READS_Z_RE.match(code):
            return ("UNSAFE", f"reads Z via `{code}` at line {j + 1}")
        if c_alive and READS_C_RE.match(code):
            return ("UNSAFE", f"reads C via `{code}` at line {j + 1}")
        # Apply kills.
        if z_alive and KILLS_Z_RE.match(code):
            z_alive = False
        if c_alive and KILLS_C_RE.match(code):
            c_alive = False
        # Both flags overwritten -> any subsequent read sees post-instr values.
        if not z_alive and not c_alive:
            return ("SAFE", f"Z and C overwritten by line {j + 1}: `{code}`")
        # Unconditional transfer -> no further fall-through.
        if UNCOND_TRANSFER_RE.match(code):
            return ("SAFE", f"control transfer `{code}` at line {j + 1}")
    return ("INDETERMINATE", "fell off file end")


def collect_sites() -> list[Site]:
    sites: list[Site] = []
    for path in iter_asm_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        for i, raw in enumerate(lines):
            m = LD_A_ZERO_RE.match(raw)
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
    """Rewrite each SAFE site's `ld a, 0` to `xor a`, preserving the line's
    indent and any trailing comment. Skip UNSAFE / INDETERMINATE / keep-marked
    sites."""
    by_path: dict[Path, list[Site]] = {}
    for s in sites:
        if s.classification != "SAFE" or s.has_keep_marker:
            continue
        by_path.setdefault(s.path, []).append(s)
    changed = 0
    for path, path_sites in by_path.items():
        text = path.read_text(encoding="utf-8", errors="replace")
        # Preserve the file's line-ending style.
        if "\r\n" in text:
            newline = "\r\n"
            lines = text.split("\r\n")
        else:
            newline = "\n"
            lines = text.split("\n")
        for s in path_sites:
            old_line = lines[s.line_idx]
            m = LD_A_ZERO_RE.match(old_line)
            if not m:
                print(
                    f"SKIP {path.relative_to(ROOT)}:{s.line_no} -- line "
                    f"text changed since classification",
                    file=sys.stderr,
                )
                continue
            indent = m["indent"] or ""
            tail = m["tail"] or ""
            new_line = f"{indent}xor a"
            if tail:
                new_line += f" {tail}"
            lines[s.line_idx] = new_line
            changed += 1
        path.write_text(newline.join(lines), encoding="utf-8")
    print(f"Codemod applied: {changed} `ld a, 0` -> `xor a` rewrites across "
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
        print("`ld a, 0` audit FAILED.", file=sys.stderr)
        print(
            f"{len(safe)} site(s) can safely be `xor a` (1 byte vs 2, "
            "identical resulting A=0; subsequent code does not depend on "
            "pre-`ld a, 0` Z or C). Replace, or add a `; keep` comment "
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

    print("`ld a, 0` audit passed.")
    print(
        f"Scanned {len(sites)} `ld a, 0` site(s); "
        f"{len(unsafe)} flag-preserving (kept), "
        f"{len(indet)} indeterminate (kept), "
        f"{len(kept)} keep-marked."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
