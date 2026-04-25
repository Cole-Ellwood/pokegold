#!/usr/bin/env python3
"""Audit battle math scratch-register references for out-of-range offsets."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SCAN_ROOTS = [
    ROOT / "engine" / "battle",
    ROOT / "engine" / "pokemon",
    ROOT / "engine" / "overworld",
    ROOT / "home",
]

SCRATCH_SIZES = {
    "hMultiplicand": 3,
    "hProduct": 4,
    "hDividend": 4,
    "hQuotient": 4,
    "hMathBuffer": 5,
}

OFFSET_RE = re.compile(
    r"\b(?P<label>hMultiplicand|hProduct|hDividend|hQuotient|hMathBuffer)"
    r"\s*(?P<sign>[+-])\s*(?P<offset>\d+)\b"
)
GLOBAL_LABEL_RE = re.compile(r"^(?P<label>[A-Za-z_][A-Za-z0-9_]*):")
LOCAL_LABEL_RE = re.compile(r"^(?P<label>\.[A-Za-z_][A-Za-z0-9_]*):?$")


@dataclass(frozen=True)
class Issue:
    path: Path
    lineno: int
    line: str
    reason: str


def strip_comment(line: str) -> str:
    return line.split(";", 1)[0]


def is_allowed_exception(
    rel_path: str,
    global_label: str | None,
    local_label: str | None,
    label: str,
    sign: str,
    offset: int,
) -> bool:
    # The original Reversal/Flail routine intentionally uses the byte adjacent
    # to hProduct while rescaling a 32-bit intermediate. Keep the exception
    # narrow so new helper code cannot accidentally copy this pattern.
    if (
        rel_path == "engine/battle/effect_commands.asm"
        and global_label == "BattleCommand_ConstantDamage"
        and local_label in {".reversal", ".reversal_got_hp", ".skip_to_divide"}
        and label == "hProduct"
        and sign == "+"
        and offset == 4
    ):
        return True

    # _Multiply deliberately uses the byte before hMultiplicand as an internal
    # fourth input byte. Other code should use hMultiplier/hDivisor by name.
    if (
        rel_path == "engine/math/math.asm"
        and global_label == "_Multiply"
        and label == "hMultiplicand"
        and sign == "-"
        and offset == 1
    ):
        return True

    return False


def scan_file(path: Path) -> list[Issue]:
    issues: list[Issue] = []
    rel_path = path.relative_to(ROOT).as_posix()
    global_label: str | None = None
    local_label: str | None = None

    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        code = strip_comment(raw_line).strip()
        if not code:
            continue

        global_match = GLOBAL_LABEL_RE.match(code)
        if global_match:
            global_label = global_match.group("label")
            local_label = None

        local_match = LOCAL_LABEL_RE.match(code)
        if local_match:
            local_label = local_match.group("label")

        for match in OFFSET_RE.finditer(code):
            label = match.group("label")
            sign = match.group("sign")
            offset = int(match.group("offset"))
            size = SCRATCH_SIZES[label]
            in_range = sign == "+" and 0 <= offset < size
            if in_range:
                continue

            if is_allowed_exception(rel_path, global_label, local_label, label, sign, offset):
                continue

            if sign == "+":
                valid = f"{label} + 0..{size - 1}"
            else:
                valid = f"{label} + 0..{size - 1}; use the neighboring scratch label by name"
            issues.append(
                Issue(
                    path=path,
                    lineno=lineno,
                    line=raw_line.rstrip(),
                    reason=f"{label} {sign} {offset} is outside valid range ({valid})",
                )
            )

    return issues


def iter_asm_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if root.exists():
            files.extend(sorted(root.rglob("*.asm")))
    return files


def main() -> int:
    issues: list[Issue] = []
    for path in iter_asm_files():
        issues.extend(scan_file(path))

    if issues:
        print("Battle math scratch-register audit FAILED.", file=sys.stderr)
        for issue in issues:
            rel = issue.path.relative_to(ROOT)
            print(f"{rel}:{issue.lineno}: {issue.reason}", file=sys.stderr)
            print(f"  {issue.line}", file=sys.stderr)
        return 1

    print("Battle math scratch-register audit passed.")
    print(f"Scanned {len(iter_asm_files())} ASM files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
