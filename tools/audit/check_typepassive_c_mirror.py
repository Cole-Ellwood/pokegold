#!/usr/bin/env python3
"""Audit in-bank callers of TypePassive_Get*Category_Far functions.

The AG-08 fix (commit a6a00ea8) added a `ld c, a` mirror at the .done
block of TypePassive_GetEffectiveMoveCategory_Far and its sister
TypePassive_GetLastCounterMoveCategory_Far. The mirror passes the
move-category byte through the farcall a/c-passthrough rule for
cross-bank callers via Battle_Get*Category home thunks.

Same-bank callers that consume `a` immediately via cp SPECIAL are
LOCALLY safe but may have OUTER callers whose c is load-bearing for
code AFTER the immediate post-call dispatch. The May 2026 5x-damage
bug (commit a5ebc095) was this exact pattern: ApplyLateGenDamage
StatsItemMods_Far and DittoMetalPowder_Far called the function in-bank
without push/pop bc; the c-clobber propagated through TruncateHL_BC
into ConfusionDamageCalc.

This audit lists in-bank call sites and warns when push bc / pop bc
doesn't wrap the call. Fixed sites include a comment reference; the
audit only flags un-fixed sites.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGETS = (
    "TypePassive_GetEffectiveMoveCategory_Far",
    "TypePassive_GetLastCounterMoveCategory_Far",
)
SOURCES = (
    "engine/battle/late_gen_held_items.asm",
    "engine/battle/type_passive_damage_mods.asm",
)
# Sites that are intentionally fine without push/pop bc — caller's c is not
# load-bearing post-dispatch. Filename:line_keyword pairs.
KNOWN_SAFE = {
    # .muscle_band, .wise_glasses: jp tail-call after cp SPECIAL; bc not
    # consumed in any reachable post-tail code.
    ("engine/battle/late_gen_held_items.asm", "muscle_band"),
    ("engine/battle/late_gen_held_items.asm", "wise_glasses"),
    # CheckDamageStatsCritical_Far: push bc wraps the whole function body
    # (line 631 / pop bc at line 662); inner c-clobber doesn't escape.
    ("engine/battle/late_gen_held_items.asm", "CheckDamageStatsCritical_Far"),
    # TypePassive_ApplyDamageModifiers_Far .after_rock / .after_bug:
    # caller (BattleCommand_Stab via farcall) doesn't read bc after the
    # farcall — uses wCurDamage directly. Caller's bc is dispatcher-managed.
    ("engine/battle/type_passive_damage_mods.asm", "after_rock"),
    ("engine/battle/type_passive_damage_mods.asm", "after_bug"),
}


def find_call_sites(rom_path: Path):
    """Yield (file, lineno, line, function_label) for each call site."""
    text = rom_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    current_label = ""
    for i, line in enumerate(lines, 1):
        # Track current label: top-level "Foo:" or sub-label ".bar" at col 0
        m = re.match(r"^([\w]+):", line)
        if m:
            current_label = m.group(1)
        elif re.match(r"^\.[\w]+", line):
            sub = re.match(r"^(\.[\w]+)", line).group(1)
            current_label = current_label.split(".")[0] + sub
        # Detect in-bank call to one of the targets
        for target in TARGETS:
            if re.search(rf"^\s*call\s+{re.escape(target)}\b", line):
                yield rom_path, i, line.rstrip(), current_label


def has_pushpop_bc_protection(lines: list[str], call_idx: int) -> bool:
    """Check if push bc precedes and pop bc follows the call within ~3 lines."""
    pre = "\n".join(lines[max(0, call_idx - 3):call_idx])
    post = "\n".join(lines[call_idx + 1:min(len(lines), call_idx + 4)])
    return bool(re.search(r"^\s*push\s+bc\b", pre, re.M)) and bool(
        re.search(r"^\s*pop\s+bc\b", post, re.M)
    )


def main() -> int:
    sources = [ROOT / s for s in SOURCES]
    findings = []
    for src in sources:
        text = src.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        for f, lineno, line, label in find_call_sites(src):
            rel = src.relative_to(ROOT).as_posix()
            safe_key = next(
                (k for k in KNOWN_SAFE if k[0] == rel and k[1] in label), None
            )
            protected = has_pushpop_bc_protection(lines, lineno - 1)
            findings.append({
                "file": rel,
                "line": lineno,
                "label": label,
                "protected": protected,
                "known_safe": bool(safe_key),
            })

    print(f"in-bank callers of {' / '.join(TARGETS)}:")
    print(f"{'file':<40s} {'line':>5s} {'label':<55s} {'prot':<5s} {'safe':<5s}")
    print("-" * 120)
    failures = []
    for f in findings:
        flag = "OK" if (f["protected"] or f["known_safe"]) else "***"
        print(
            f"{flag} {f['file']:<37s} {f['line']:>5d} {f['label']:<55s} "
            f"{'Y' if f['protected'] else 'N':<5s} "
            f"{'Y' if f['known_safe'] else 'N':<5s}"
        )
        if not (f["protected"] or f["known_safe"]):
            failures.append(f)

    if failures:
        print(f"\n*** {len(failures)} unprotected & unaudited site(s).")
        print("    Either wrap with push bc / pop bc OR add to KNOWN_SAFE")
        print("    after manually verifying caller's c is not load-bearing.")
        return 1

    print(f"\nPASS: all {len(findings)} sites are either push/pop-protected")
    print("      or audited as KNOWN_SAFE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
