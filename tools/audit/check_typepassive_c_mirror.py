#!/usr/bin/env python3
"""Audit in-bank callers of c-mirroring functions in the type-passive files.

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

Targets are AUTO-DISCOVERED: any top-level function in SOURCES whose
exit path reaches a `ret` through an `ld c, a` mirror (walking back
over c-neutral instructions, same idea as check_farcall_a_clobber's
return-direction walk). A hardcoded list rotted once already — the
original two-function TARGETS tuple missed at least five newer
functions carrying the identical pattern (2026-07-08 review finding).
SEED_TARGETS is a regression guard: if discovery ever fails to find
the two original functions, the discovery regexes broke — fail loudly.

This audit lists in-bank call sites of every discovered target and
warns when push bc / pop bc doesn't wrap the call. Fixed sites include
a comment reference; the audit only flags un-fixed sites.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED_TARGETS = (
    "TypePassive_GetEffectiveMoveCategory_Far",
    "TypePassive_GetLastCounterMoveCategory_Far",
)
SOURCES = (
    "engine/battle/late_gen_held_items.asm",
    "engine/battle/type_passive_damage_mods.asm",
)
# Sites that are intentionally fine without push/pop bc — caller's c is not
# load-bearing post-dispatch. Filename:label_keyword pairs.
KNOWN_SAFE = {
    # .muscle_band, .wise_glasses: jp tail-call after cp SPECIAL; bc not
    # consumed in any reachable post-tail code.
    ("engine/battle/late_gen_held_items.asm", "muscle_band"),
    ("engine/battle/late_gen_held_items.asm", "wise_glasses"),
    # CheckDamageStatsCritical_Far: push bc wraps the whole function body
    # (line 631 / pop bc at line 662); inner c-clobber doesn't escape.
    ("engine/battle/late_gen_held_items.asm", "CheckDamageStatsCritical_Far"),
    # TypePassive_ApplyDamageModifiers_Far .after_rock:
    # caller (BattleCommand_Stab via farcall) doesn't read bc after the
    # farcall — uses wCurDamage directly. Caller's bc is dispatcher-managed.
    ("engine/battle/type_passive_damage_mods.asm", "after_rock"),
    # TypePassive_TryDarkStatusShield_Far calling
    # TypePassive_IsDarkShieldEligibleEffect_Far (line ~1073): nothing is
    # staged in bc before the call; b is loaded fresh AFTER it (from
    # GetOpponentTypeContribution), and the later helper call that does
    # carry b is already push/pop-protected. Verified 2026-07-08.
    ("engine/battle/type_passive_damage_mods.asm", "TryDarkStatusShield_Far"),
}

TOP_LABEL_RE = re.compile(r"^(\w+)::?")
SUB_LABEL_RE = re.compile(r"^(\.\w+)")
RET_RE = re.compile(r"^\s*ret\b")
MIRROR_RE = re.compile(r"^\s*ld\s+c\s*,\s*a\b")
# Instructions that write c some other way — a mirror before one of these
# does not survive to the ret.
C_WRITE_RE = re.compile(
    r"^\s*(pop\s+bc\b|ld\s+c\s*,|ld\s+bc\s*,|inc\s+c\b|dec\s+c\b"
    r"|rl\s+c\b|rr\s+c\b|rlc\s+c\b|rrc\s+c\b|sla\s+c\b|sra\s+c\b"
    r"|srl\s+c\b|swap\s+c\b)"
)
# Control flow we refuse to walk back across: past one of these the value
# of c at the ret is no longer locally provable. Conservative: such an
# exit is treated as not-mirrored (under-discovery, never over-discovery
# of safety — a function only needs ONE provable mirrored exit to be a
# hazard for in-bank callers).
FLOW_RE = re.compile(r"^\s*(jp|jr|call|farcall|callfar|homecall|rst)\b")


def strip_comment(line: str) -> str:
    return line.split(";", 1)[0].rstrip()


def discover_mirrored_functions(paths: list[Path]) -> dict[str, str]:
    """Return {function_label: 'file:line' of the mirrored exit}."""
    found: dict[str, str] = {}
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        current = ""
        starts: dict[int, str] = {}
        for i, raw in enumerate(lines):
            m = TOP_LABEL_RE.match(raw)
            if m:
                current = m.group(1)
                starts[i] = current
        # walk back from each ret to see if an `ld c, a` mirror reaches it
        current = ""
        for i, raw in enumerate(lines):
            if i in starts:
                current = starts[i]
            code = strip_comment(raw)
            if not current or not RET_RE.match(code):
                continue
            j = i - 1
            while j >= 0 and j not in starts:
                back = strip_comment(lines[j])
                if not back or SUB_LABEL_RE.match(back):
                    # blank/comment/sub-label: fall-through, keep walking
                    j -= 1
                    continue
                if MIRROR_RE.match(back):
                    found.setdefault(current, f"{rel}:{j + 1}")
                    break
                if C_WRITE_RE.match(back) or FLOW_RE.match(back) or \
                        TOP_LABEL_RE.match(back):
                    break
                j -= 1
    return found


def find_call_sites(rom_path: Path, targets: dict[str, str]):
    """Yield (file, lineno, line, function_label, target) for call sites."""
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
        for target in targets:
            if re.search(rf"^\s*call\s+{re.escape(target)}\b", line):
                yield rom_path, i, line.rstrip(), current_label, target


def has_pushpop_bc_protection(lines: list[str], call_idx: int) -> bool:
    """Check if push bc precedes and pop bc follows the call within ~3 lines."""
    pre = "\n".join(lines[max(0, call_idx - 3):call_idx])
    post = "\n".join(lines[call_idx + 1:min(len(lines), call_idx + 4)])
    return bool(re.search(r"^\s*push\s+bc\b", pre, re.M)) and bool(
        re.search(r"^\s*pop\s+bc\b", post, re.M)
    )


def main() -> int:
    sources = [ROOT / s for s in SOURCES]
    targets = discover_mirrored_functions(sources)

    missing_seeds = [s for s in SEED_TARGETS if s not in targets]
    if missing_seeds:
        print("*** discovery regression: seed target(s) not auto-discovered:")
        for s in missing_seeds:
            print(f"    {s}")
        print("    The walk-back regexes no longer match the known mirror")
        print("    pattern — fix discover_mirrored_functions().")
        return 1

    print(f"auto-discovered {len(targets)} c-mirroring function(s):")
    for name in sorted(targets):
        print(f"  {name:<50s} mirror at {targets[name]}")
    print()

    findings = []
    for src in sources:
        text = src.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        for f, lineno, line, label, target in find_call_sites(src, targets):
            rel = src.relative_to(ROOT).as_posix()
            safe_key = next(
                (k for k in KNOWN_SAFE if k[0] == rel and k[1] in label), None
            )
            protected = has_pushpop_bc_protection(lines, lineno - 1)
            findings.append({
                "file": rel,
                "line": lineno,
                "label": label,
                "target": target,
                "protected": protected,
                "known_safe": bool(safe_key),
            })

    print("in-bank callers of discovered targets:")
    print(f"{'file':<40s} {'line':>5s} {'label':<40s} "
          f"{'target':<40s} {'prot':<5s} {'safe':<5s}")
    print("-" * 140)
    failures = []
    for f in findings:
        flag = "OK" if (f["protected"] or f["known_safe"]) else "***"
        print(
            f"{flag} {f['file']:<37s} {f['line']:>5d} {f['label']:<40s} "
            f"{f['target']:<40s} "
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
