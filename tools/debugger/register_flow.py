#!/usr/bin/env python3
"""Static register-flow / clobber-set analyzer for asm functions (P15).

Walks an .asm function from its top-level label and identifies which CPU
registers each instruction directly writes. Emits a clobber set plus
call/branch/push-pop sites. Targets the AG-NN transitive register-clobber
bug class (recurring in this repo: shipped twice as 5x-damage on physical
attacks via `c`-mirror added at function exits whose callers had `c`
load-bearing post-dispatch -- see docs/asm_authoring_guide.md §3.13, §3.14).

Generalizes the single-purpose pattern matchers in:
  - tools/audit/check_farcall_a_clobber.py (farcall a -> c mirror class)
  - tools/audit/check_typepassive_c_mirror.py (AG-08 c-mirror class)

CLI: `python -m tools.debugger clobbers --symbol GetUserItem`

First-slice scope (intentional v1 limits, documented as gaps in the
catalog surface):
  - Linear body scan from the function's label to the next top-level
    label or SECTION. No branch following; conditional branches are
    treated as definitely-taken (over-approximates writes).
  - Calls are LISTED but their target clobber sets are NOT resolved.
    A `call Foo` site is listed for follow-up; the analyzer does not
    chase callees.
  - No loop fixpoint; loops collapse to their single-pass write set
    (sound for "definite writes", lossy for cross-iteration state).
  - `jp [hl]` / dispatch-table tail-calls are marked OPAQUE.
  - Flags are not modeled in the first slice.
  - push/pop pairs are LISTED for context but do not retroactively
    suppress the writes between them; "ld de, X" still counts as a
    write to d/e even when bracketed by `push de` / `pop de`.

Output mirrors the v2 surface shape (`schema_version` + `valid` + per-
register write events + canonical call/branch arrays + warnings).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

from .catalog import ROOT


SCHEMA_VERSION = 1
KIND = "register_flow_summary"
SOURCE_ROOTS: tuple[str, ...] = (
    "engine",
    "home",
    "data",
    "gfx",
    "audio",
    "macros",
    "constants",
    "maps",
    "ram",
    "main.asm",
)


# Per-register direct write patterns. Each regex matches the START of a
# normalized (whitespace-trimmed, comment-stripped) instruction line.
# A match means: this instruction definitely writes the named register
# during normal SM83 execution. push/pop/call/ret are handled separately.
#
# Patterns intentionally OVER-MATCH writes (false positive on "wrote")
# rather than under-matching, because the analyzer's bug-prevention
# value depends on flagging anything that COULD clobber. Refinement of
# specific shapes (e.g. distinguishing `ld R, [...]` cycle counts) is a
# later-slice job; v1 just needs the write set.

_R_8BIT = ("a", "b", "c", "d", "e", "h", "l")

# Generic 8-bit-register write shapes. {r} is substituted per register.
# - `ld r, *`     -- explicit load INTO r
# - `inc r`       -- increment r
# - `dec r`       -- decrement r
# - `swap r`      -- nibble swap (CB)
# - `set n, r`    -- bit set (CB)
# - `res n, r`    -- bit reset (CB)
# - `rl r` / `rr r` / `rlc r` / `rrc r` / `sla r` / `sra r` / `srl r` -- rotates/shifts (CB)
_WRITE_8BIT_TEMPLATE = (
    r"^(?:"
    r"ld\s+{r}\s*,"
    r"|inc\s+{r}\b"
    r"|dec\s+{r}\b"
    r"|swap\s+{r}\b"
    r"|set\s+\w+\s*,\s*{r}\b"
    r"|res\s+\w+\s*,\s*{r}\b"
    r"|rl\s+{r}\b|rr\s+{r}\b|rlc\s+{r}\b|rrc\s+{r}\b"
    r"|sla\s+{r}\b|sra\s+{r}\b|srl\s+{r}\b"
    r")"
)
WRITES_R_RE: dict[str, re.Pattern[str]] = {
    r: re.compile(_WRITE_8BIT_TEMPLATE.format(r=r), re.IGNORECASE) for r in _R_8BIT
}

# Accumulator (a) is also written by ALU ops, accumulator rotates, daa,
# cpl, and special HRAM/memory loads. These are accumulator-only and do
# NOT appear in the generic template.
WRITES_A_EXTRA_RE = re.compile(
    r"^(?:"
    r"add\s+(?!hl\b|sp\b)"          # add a, X (excluding add hl/sp)
    r"|adc\s+"                       # adc a, X
    r"|sub\s+"                       # sub X  (= sub a, X)
    r"|sbc\s+(?!hl\b)"               # sbc a, X (excluding sbc hl, which doesn't exist on SM83 but exclude defensively)
    r"|and\s+(?!a\s*$)"              # and X, excluding the idiomatic flag-only `and a` test
    r"|or\s+"                        # or X
    r"|xor\s+"                       # xor X (xor a writes a=0)
    r"|rla\b|rra\b|rlca\b|rrca\b"    # accumulator rotates
    r"|cpl\b|daa\b"                  # bit-complement, decimal-adjust
    r"|ldh\s+a\s*,"                  # ldh a, [n] -- HRAM read into a
    r"|ld\s+a\s*,\s*\["              # ld a, [..] -- memory read into a
    r")",
    re.IGNORECASE,
)
# `and a` is a flag-only test (a is unchanged). Treat it as NOT writing
# a even though the ALU formally produces a. This matches the codebase
# idiom where `and a` precedes a conditional ret/jr to check zero.
AND_A_FLAG_TEST_RE = re.compile(r"^and\s+a\s*(?:;.*)?$", re.IGNORECASE)

# 16-bit register-pair operations that write both halves of the pair.
# `pop RR` writes both halves of RR. First-slice reports do not model
# flags, so `pop af` reports only the accumulator write.
# `inc RR` / `dec RR` write both halves (no flag effect).
# `add hl, RR` writes h and l (and flags).
# `ld RR, n16` writes both halves.
# `ld hl, sp+n` writes h and l.
# `ld A, [HLI/HLD]` / `ld [HLI/HLD], A` writes h and l (post inc/dec).
WRITES_PAIR_RE: dict[str, re.Pattern[str]] = {
    "bc": re.compile(
        r"^(?:pop\s+bc\b|inc\s+bc\b|dec\s+bc\b|ld\s+bc\s*,)",
        re.IGNORECASE,
    ),
    "de": re.compile(
        r"^(?:pop\s+de\b|inc\s+de\b|dec\s+de\b|ld\s+de\s*,)",
        re.IGNORECASE,
    ),
    "hl": re.compile(
        r"^(?:"
        r"pop\s+hl\b"
        r"|inc\s+hl\b|dec\s+hl\b"
        r"|ld\s+hl\s*,"
        r"|add\s+hl\s*,"
        r"|ld\s+a\s*,\s*\[\s*hl[id]\s*\]"     # ld a, [hli] / [hld]
        r"|ld\s+\[\s*hl[id]\s*\]\s*,\s*a"     # ld [hli], a / ld [hld], a
        r")",
        re.IGNORECASE,
    ),
    "af": re.compile(r"^pop\s+af\b", re.IGNORECASE),
}

# Call / jump / return sites. Recorded as control-flow events so the
# analyzer can note where execution might leave the function (and
# therefore where downstream register state becomes uncertain).
CALL_RE = re.compile(
    r"^(?P<kind>call|farcall|callfar|homecall|rst)\s+"
    r"(?:(?P<cond>nz|z|nc|c)\s*,\s*)?"
    r"(?P<target>\S+)",
    re.IGNORECASE,
)
JP_RE = re.compile(
    r"^jp\s+(?:(?P<cond>nz|z|nc|c)\s*,\s*)?(?P<target>\S+)",
    re.IGNORECASE,
)
JR_RE = re.compile(
    r"^jr\s+(?:(?P<cond>nz|z|nc|c)\s*,\s*)?(?P<target>\S+)",
    re.IGNORECASE,
)
RET_RE = re.compile(
    r"^(?:ret|reti)(?:\s+(?P<cond>nz|z|nc|c))?\s*$",
    re.IGNORECASE,
)

# Stack push/pop pairs for preservation context. push reads two
# registers and stores to the stack; pop writes them back. We track
# these so callers know "writes between push X and pop X are bracketed
# by a preservation window."
PUSH_RE = re.compile(r"^push\s+(?P<pair>bc|de|hl|af)\b", re.IGNORECASE)
POP_RE = re.compile(r"^pop\s+(?P<pair>bc|de|hl|af)\b", re.IGNORECASE)

# Label patterns mirrored from tools/audit/asm_scan.py so the analyzer
# can find a function's body without depending on that module.
TOP_LABEL_RE = re.compile(r"^(?P<label>[A-Za-z_][A-Za-z0-9_]*):{1,2}\s*(?:;.*)?$")
LOCAL_LABEL_RE = re.compile(r"^\s*(?P<label>\.[A-Za-z_][A-Za-z0-9_]*):?\s*(?:;.*)?$")
SECTION_RE = re.compile(r'^\s*SECTION\s+"', re.IGNORECASE)


@dataclass(frozen=True)
class FunctionLocation:
    """A located top-level asm function ready for body inspection."""

    symbol: str
    path: Path
    start_line: int  # 1-based line of the label itself
    body: tuple[str, ...]  # raw lines AFTER the label, before next top-level / SECTION


@dataclass
class WriteEvent:
    line: int  # 1-based absolute line in the source file
    instruction: str
    register: str

    def to_dict(self) -> dict[str, Any]:
        return {"line": self.line, "instruction": self.instruction}


def normalize_code(line: str) -> str:
    """Strip comment and surrounding whitespace; preserve internal spacing."""
    code, _, _ = line.partition(";")
    return code.strip()


def iter_source_paths(root: Path = ROOT) -> Iterable[Path]:
    """Yield .asm paths under the conventional source roots.

    Mirrors the project layout described in CLAUDE.md (engine/, home/,
    data/, etc.); excludes tools/scripts/.git/.local/workspace/.claude/
    by virtue of only walking the SOURCE_ROOTS set.
    """
    for relative in SOURCE_ROOTS:
        target = root / relative
        if not target.exists():
            continue
        if target.is_file():
            yield target
            continue
        for path in sorted(target.rglob("*.asm")):
            yield path


def find_function(symbol: str, root: Path = ROOT) -> FunctionLocation | None:
    """Return the first top-level function matching ``symbol``.

    Walks source roots in deterministic order and stops at the first
    file containing a top-level label matching ``symbol`` (with either
    `:` or `::`). The body is the slice of lines after the label up to
    (but not including) the next top-level label or SECTION directive.
    """
    pattern = re.compile(rf"^{re.escape(symbol)}:{{1,2}}\s*(?:;.*)?$")
    for path in iter_source_paths(root=root):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for i, raw in enumerate(lines):
            if pattern.match(raw):
                body = _collect_body(lines, label_index=i)
                return FunctionLocation(
                    symbol=symbol,
                    path=path,
                    start_line=i + 1,
                    body=tuple(body),
                )
    return None


def _collect_body(lines: list[str], *, label_index: int) -> list[str]:
    """Lines AFTER label_index up to next top-level label or SECTION."""
    body: list[str] = []
    for raw in lines[label_index + 1 :]:
        if SECTION_RE.match(raw):
            break
        if TOP_LABEL_RE.match(raw):
            break
        body.append(raw)
    return body


def writes_for_instruction(code: str) -> tuple[str, ...]:
    """Return the registers this instruction directly writes, normalized.

    Returns a sorted tuple of single-letter register names (a, b, c, d,
    e, h, l). 16-bit-pair writes are expanded into their modeled halves.
    `xor a` writes a; `and a` does NOT write a (it's a flag-only test
    -- the codebase idiom). Flags are not modeled in this first slice.
    """
    if not code:
        return ()
    if AND_A_FLAG_TEST_RE.match(code):
        return ()
    writes: set[str] = set()
    for register, pattern in WRITES_R_RE.items():
        if pattern.match(code):
            writes.add(register)
    if WRITES_A_EXTRA_RE.match(code):
        writes.add("a")
    for pair, pattern in WRITES_PAIR_RE.items():
        if pattern.match(code):
            for letter in pair:
                if letter in _R_8BIT:
                    writes.add(letter)
    return tuple(sorted(writes))


def classify_control(code: str) -> dict[str, Any] | None:
    """Return a control-flow descriptor for call/jp/jr/ret, or None."""
    if not code:
        return None
    if RET_RE.match(code):
        cond = RET_RE.match(code).group("cond")
        return {
            "kind": "ret_cond" if cond else "ret",
            "condition": cond,
            "instruction": code,
        }
    call_match = CALL_RE.match(code)
    if call_match:
        condition = call_match.group("cond")
        kind = call_match.group("kind").lower()
        return {
            "kind": "call_cond" if kind == "call" and condition else kind,
            "condition": condition,
            "target": call_match.group("target").rstrip(",").strip(),
            "instruction": code,
        }
    jp_match = JP_RE.match(code)
    if jp_match:
        cond = jp_match.group("cond")
        target = jp_match.group("target").rstrip(",").strip()
        if target.lower() == "[hl]":
            return {
                "kind": "jp_opaque",
                "condition": cond,
                "target": target,
                "instruction": code,
                "opaque": True,
            }
        return {
            "kind": "jp_cond" if cond else "jp_unconditional",
            "condition": cond,
            "target": target,
            "instruction": code,
        }
    jr_match = JR_RE.match(code)
    if jr_match:
        cond = jr_match.group("cond")
        return {
            "kind": "jr_cond" if cond else "jr_unconditional",
            "condition": cond,
            "target": jr_match.group("target").rstrip(",").strip(),
            "instruction": code,
        }
    return None


def analyze_function(symbol: str, *, root: Path = ROOT) -> dict[str, Any]:
    """Walk the function body and emit a register-flow summary report."""
    location = find_function(symbol, root=root)
    if location is None:
        return {
            "schema_version": SCHEMA_VERSION,
            "kind": KIND,
            "valid": False,
            "symbol": symbol,
            "errors": [f"no top-level function matching {symbol!r} under SOURCE_ROOTS"],
        }
    direct_writes: dict[str, list[WriteEvent]] = {r: [] for r in _R_8BIT}
    calls: list[dict[str, Any]] = []
    branches: list[dict[str, Any]] = []
    rets: list[dict[str, Any]] = []
    push_pop_pairs: list[dict[str, Any]] = []
    warnings: list[str] = []

    pending_pushes: list[tuple[str, int]] = []  # (pair, body_index)

    for body_index, raw in enumerate(location.body):
        code = normalize_code(raw)
        if not code:
            continue
        # Skip local labels -- they're branch targets, not instructions.
        if LOCAL_LABEL_RE.match(raw):
            continue
        absolute_line = location.start_line + 1 + body_index

        push_match = PUSH_RE.match(code)
        if push_match:
            pending_pushes.append((push_match.group("pair").lower(), body_index))
            continue
        pop_match = POP_RE.match(code)
        if pop_match:
            pair = pop_match.group("pair").lower()
            push_idx: int | None = None
            for stack_idx in range(len(pending_pushes) - 1, -1, -1):
                if pending_pushes[stack_idx][0] == pair:
                    push_idx = pending_pushes.pop(stack_idx)[1]
                    break
            if push_idx is not None:
                push_pop_pairs.append({
                    "register_pair": pair,
                    "push_line": location.start_line + 1 + push_idx,
                    "pop_line": absolute_line,
                })
            else:
                warnings.append(
                    f"pop {pair} at line {absolute_line} has no matching push in this function body"
                )
            # pop also writes the pair halves -- record as direct writes.
            for letter in pair:
                if letter in direct_writes:
                    direct_writes[letter].append(
                        WriteEvent(line=absolute_line, instruction=code, register=letter)
                    )
            continue

        for register in writes_for_instruction(code):
            direct_writes[register].append(
                WriteEvent(line=absolute_line, instruction=code, register=register)
            )

        control = classify_control(code)
        if control is None:
            continue
        control_with_line = {"line": absolute_line, **control}
        kind = control["kind"]
        if kind in {"call", "call_cond", "farcall", "callfar", "homecall", "rst"}:
            calls.append(control_with_line)
        elif kind.startswith("ret"):
            rets.append(control_with_line)
        elif kind.startswith("jp") or kind.startswith("jr"):
            branches.append(control_with_line)
            if control.get("opaque"):
                warnings.append(
                    f"opaque branch at line {absolute_line}: {control['instruction']}"
                )

    if pending_pushes:
        for pair, body_index in pending_pushes:
            warnings.append(
                f"push {pair} at line {location.start_line + 1 + body_index} has no matching pop in this function body"
            )

    if not rets and not any(
        branch["kind"].endswith("unconditional") or branch["kind"] == "jp_opaque"
        for branch in branches
    ):
        warnings.append(
            "function body has no `ret`/`reti`/unconditional jump -- may be fall-through to next label"
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "valid": True,
        "symbol": symbol,
        "path": str(location.path.relative_to(root)) if location.path.is_relative_to(root) else str(location.path),
        "start_line": location.start_line,
        "body_lines": len(location.body),
        "direct_writes": {
            register: [event.to_dict() for event in events]
            for register, events in direct_writes.items()
            if events
        },
        "clobber_set": sorted(
            register for register, events in direct_writes.items() if events
        ),
        "calls": calls,
        "branches": branches,
        "rets": rets,
        "push_pop_pairs": push_pop_pairs,
        "warnings": warnings,
        "errors": [],
    }


def render_text(report: dict[str, Any]) -> str:
    """Human-readable single-screen rendering of an analyzer report."""
    if not report.get("valid"):
        lines = [f"register-flow: INVALID for symbol {report.get('symbol')!r}"]
        for err in report.get("errors", []):
            lines.append(f"  error: {err}")
        return "\n".join(lines) + "\n"
    out: list[str] = []
    out.append(f"register-flow summary: {report['symbol']}")
    out.append(f"  path:        {report['path']}:{report['start_line']}")
    out.append(f"  body lines:  {report['body_lines']}")
    out.append(f"  clobber set: {', '.join(report['clobber_set']) or '(none)'}")
    out.append("  direct writes:")
    if not report["direct_writes"]:
        out.append("    (none)")
    else:
        for register in sorted(report["direct_writes"]):
            events = report["direct_writes"][register]
            out.append(f"    {register}: {len(events)} write(s)")
            for event in events:
                out.append(f"      line {event['line']}: {event['instruction']}")
    out.append("  calls:")
    if not report["calls"]:
        out.append("    (none)")
    else:
        for call in report["calls"]:
            target = call.get("target", "(opaque)")
            out.append(f"    line {call['line']}: {call['kind']} {target}")
    out.append("  branches:")
    if not report["branches"]:
        out.append("    (none)")
    else:
        for branch in report["branches"]:
            out.append(f"    line {branch['line']}: {branch['instruction']}")
    out.append("  rets:")
    if not report["rets"]:
        out.append("    (none)")
    else:
        for ret in report["rets"]:
            out.append(f"    line {ret['line']}: {ret['instruction']}")
    if report["push_pop_pairs"]:
        out.append("  push/pop pairs:")
        for pair in report["push_pop_pairs"]:
            out.append(
                f"    {pair['register_pair']}: push @ line {pair['push_line']} -> pop @ line {pair['pop_line']}"
            )
    if report["warnings"]:
        out.append("  warnings:")
        for warning in report["warnings"]:
            out.append(f"    {warning}")
    return "\n".join(out) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger.register_flow",
        description=(
            "Static register-flow / clobber-set analyzer for asm functions (P15). "
            "Walks a function from its top-level label, emits which registers it "
            "directly writes plus call/branch/ret/push-pop sites. First slice: "
            "linear body scan, no branch following, no inter-procedural resolution."
        ),
    )
    parser.add_argument(
        "--symbol",
        required=True,
        help="Top-level asm label to analyze (e.g. GetUserItem)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of human-readable text",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = analyze_function(args.symbol)
    if args.json:
        sys.stdout.write(json.dumps(report, sort_keys=True) + "\n")
    else:
        sys.stdout.write(render_text(report))
    return 0 if report.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
