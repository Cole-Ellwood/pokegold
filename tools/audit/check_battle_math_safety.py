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

HOME_BATTLE = ROOT / "home" / "battle.asm"
EFFECT_COMMANDS = ROOT / "engine" / "battle" / "effect_commands.asm"
LATE_GEN_HELD_ITEMS = ROOT / "engine" / "battle" / "late_gen_held_items.asm"
TYPE_PASSIVES = ROOT / "engine" / "battle" / "type_passive_damage_mods.asm"
COUNTER_EFFECT = ROOT / "engine" / "battle" / "move_effects" / "counter.asm"
MIRROR_COAT_EFFECT = ROOT / "engine" / "battle" / "move_effects" / "mirror_coat.asm"

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


def require_text(path: Path, needle: str, issues: list[Issue], reason: str) -> None:
    if not path.exists():
        issues.append(Issue(path=path, lineno=1, line="", reason="required file is missing"))
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    if needle in text:
        return
    issues.append(Issue(path=path, lineno=1, line="", reason=reason))


def require_one_of(path: Path, needles: tuple[str, ...], issues: list[Issue], reason: str) -> None:
    if not path.exists():
        issues.append(Issue(path=path, lineno=1, line="", reason="required file is missing"))
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    if any(needle in text for needle in needles):
        return
    issues.append(Issue(path=path, lineno=1, line="", reason=reason))


def require_count_at_least(
    path: Path,
    needle: str,
    minimum: int,
    issues: list[Issue],
    reason: str,
) -> None:
    if not path.exists():
        issues.append(Issue(path=path, lineno=1, line="", reason="required file is missing"))
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    count = text.count(needle)
    if count >= minimum:
        return
    issues.append(
        Issue(
            path=path,
            lineno=1,
            line="",
            reason=f"{reason} (found {count}, expected at least {minimum})",
        )
    )


def audit_late_gen_damage_multiplier_scratch_state() -> list[Issue]:
    issues: list[Issue] = []

    # Either inline (push hl + push bc around callfar GetUserItem) or via
    # the _CheckUserItemEquals helper, which preserves hl and bc internally.
    for label, held_effect in (
        (".ApplyChoiceBandBoost", "HELD_CHOICE_BAND"),
        (".ApplyChoiceSpecsBoost", "HELD_CHOICE_SPECS"),
    ):
        inline_pattern = (
            f"{label}:\n"
            "\tpush hl\n"
            "\tpush bc\n"
            "\tcallfar GetUserItem\n"
            "\tld a, b\n"
            "\tpop bc\n"
            "\tpop hl\n"
            f"\tcp {held_effect}\n"
            "\tret nz"
        )
        helper_pattern = (
            f"{label}:\n"
            f"\tld a, {held_effect}\n"
            "\tcall _CheckUserItemEquals\n"
            "\tret nz"
        )
        require_one_of(
            LATE_GEN_HELD_ITEMS,
            (inline_pattern, helper_pattern),
            issues,
            f"{label} must preserve attacker stat pointer in hl around GetUserItem",
        )

    # If the helper is in use, audit it directly: hl and bc must be preserved
    # across the cross-bank GetUserItem call.
    text = LATE_GEN_HELD_ITEMS.read_text(encoding="utf-8", errors="replace") if LATE_GEN_HELD_ITEMS.exists() else ""
    if "_CheckUserItemEquals:" in text:
        require_text(
            LATE_GEN_HELD_ITEMS,
            (
                "_CheckUserItemEquals:\n"
                "; Input:  a = item-effect constant to check\n"
                "; Output: zf set if user holds an item with that effect, nz otherwise\n"
                "; Preserves hl, bc; clobbers a (still equals input on return)\n"
                "\tpush hl\n"
                "\tpush bc\n"
                "\tpush af\n"
                "\tcallfar GetUserItem\n"
                "\tjr _CheckItemEquals_finish"
            ),
            issues,
            "_CheckUserItemEquals must preserve hl and bc across callfar GetUserItem",
        )
        require_text(
            LATE_GEN_HELD_ITEMS,
            (
                "_CheckItemEquals_finish:\n"
                "\tpop af\n"
                "\tcp b\n"
                "\tpop bc\n"
                "\tpop hl\n"
                "\tret"
            ),
            issues,
            "_CheckItemEquals_finish must restore caller's bc and hl before returning",
        )

    require_text(
        LATE_GEN_HELD_ITEMS,
        (
            ".expert_belt\n"
            "\tpush bc\n"
            "\tpush de\n"
            "\tldh a, [hQuotient + 0]\n"
            "\tld b, a\n"
            "\tldh a, [hQuotient + 1]\n"
            "\tld c, a\n"
            "\tldh a, [hQuotient + 2]\n"
            "\tld d, a\n"
            "\tldh a, [hQuotient + 3]\n"
            "\tld e, a\n"
            "\tpush bc\n"
            "\tpush de\n"
            "\tcallfar BattleCheckTypeMatchup\n"
            "\tpop de\n"
            "\tpop bc\n"
            "\tld a, b\n"
            "\tldh [hQuotient + 0], a\n"
            "\tld a, c\n"
            "\tldh [hQuotient + 1], a\n"
            "\tld a, d\n"
            "\tldh [hQuotient + 2], a\n"
            "\tld a, e\n"
            "\tldh [hQuotient + 3], a\n"
            "\tpop de\n"
            "\tpop bc\n"
            "\tld a, [wTypeMatchup]\n"
            "\tcp EFFECTIVE + 1"
        ),
        issues,
        "Expert Belt must preserve pending damage in hQuotient around BattleCheckTypeMatchup",
    )

    require_text(
        LATE_GEN_HELD_ITEMS,
        (
            "DittoMetalPowder_Far:\n"
            "\tcall TypePassive_GetEffectiveMoveCategory_Far\n"
            "\tcp SPECIAL\n"
            "\tret nc\n"
            "\tld a, MON_SPECIES"
        ),
        issues,
        "Metal Powder must only boost physical Defense, not Special Defense",
    )

    return issues


def audit_dynamic_category_consumers() -> list[Issue]:
    issues: list[Issue] = []

    require_text(
        HOME_BATTLE,
        "Battle_GetEffectiveMoveCategory::\n\tfarcall TypePassive_GetEffectiveMoveCategory_Far",
        issues,
        "missing home wrapper for current effective move category",
    )
    require_text(
        HOME_BATTLE,
        "Battle_GetLastCounterMoveCategory::\n\tfarcall TypePassive_GetLastCounterMoveCategory_Far",
        issues,
        "missing home wrapper for last-counter effective move category",
    )
    require_text(
        TYPE_PASSIVES,
        "TypePassive_GetEffectiveMoveCategory_Far::",
        issues,
        "missing current effective category helper",
    )
    require_text(
        TYPE_PASSIVES,
        "TypePassive_GetLastCounterMoveCategory_Far::",
        issues,
        "missing last-counter effective category helper",
    )
    require_count_at_least(
        TYPE_PASSIVES,
        "cp OUTRAGE",
        2,
        issues,
        "Dragon-only Outrage exception must be applied to current and last-counter categories",
    )
    require_count_at_least(
        EFFECT_COMMANDS,
        "call Battle_GetEffectiveMoveCategory",
        2,
        issues,
        "player and enemy damage-stat paths must use effective category wrapper",
    )
    require_count_at_least(
        LATE_GEN_HELD_ITEMS,
        "call TypePassive_GetEffectiveMoveCategory_Far",
        5,
        issues,
        "held-item stat and damage category checks must use effective category helper",
    )
    require_text(
        COUNTER_EFFECT,
        "call Battle_GetLastCounterMoveCategory",
        issues,
        "Counter must use last-counter effective category wrapper",
    )
    require_text(
        MIRROR_COAT_EFFECT,
        "call Battle_GetLastCounterMoveCategory",
        issues,
        "Mirror Coat must use last-counter effective category wrapper",
    )

    return issues


def main() -> int:
    issues: list[Issue] = []
    for path in iter_asm_files():
        issues.extend(scan_file(path))
    issues.extend(audit_dynamic_category_consumers())
    issues.extend(audit_late_gen_damage_multiplier_scratch_state())

    if issues:
        print("Battle math safety audit FAILED.", file=sys.stderr)
        for issue in issues:
            rel = issue.path.relative_to(ROOT)
            print(f"{rel}:{issue.lineno}: {issue.reason}", file=sys.stderr)
            if issue.line:
                print(f"  {issue.line}", file=sys.stderr)
        return 1

    print("Battle math safety audit passed.")
    print(f"Scanned {len(iter_asm_files())} ASM files.")
    print("Dynamic category consumers use the effective-category helpers.")
    print("Late-gen item stat/damage hooks preserve live battle math state and category gates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
