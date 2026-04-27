#!/usr/bin/env python3
"""Print ranked leads for future bug hunts.

This is intentionally a triage tool, not a release gate. It looks for bug
families that have already produced real fixes in this repo, then points a
human reviewer at the smallest suspicious surface it can name.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MOVE_EFFECTS = ROOT / "data" / "moves" / "effects.asm"
BOSS_AI = ROOT / "engine" / "battle" / "ai" / "boss.asm"
AI_ITEMS = ROOT / "engine" / "battle" / "ai" / "items.asm"
AI_SWITCH = ROOT / "engine" / "battle" / "ai" / "switch.asm"
TM_TUTOR = ROOT / "engine" / "events" / "tm_tutor.asm"
ITEM_ATTRIBUTES = ROOT / "data" / "items" / "attributes.asm"
ASM_SCAN_ROOTS = (
    ROOT / "constants",
    ROOT / "data",
    ROOT / "engine",
    ROOT / "home",
    ROOT / "maps",
)

TOP_LABEL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*:{1,2}\s*(?:;.*)?$")
LOCAL_LABEL_RE = re.compile(r"^\.[A-Za-z_][A-Za-z0-9_]*:?\s*(?:;.*)?$")
MOVE_EFFECT_LABEL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*:\s*(?:;.*)?$")
RAW_ITEM_READ_RE = re.compile(r"\bld\s+a,\s*\[(wEnemyMonItem|wBattleMonItem)\]")
HELD_COMPARE_RE = re.compile(r"\bcp\s+HELD_[A-Z0-9_]+")
CONVERT_HELD_EFFECT_RE = re.compile(
    r"\b(GetItemHeldEffect|GetUserItem|GetOpponentItem|BossAI_GetEnemyHeldEffect)\b"
)
COMMENTED_FLAG_REFRESH_RE = re.compile(r"^\s*;\s*(?:and\s+a|or\s+a|cp\s+[^;]+|bit\s+[^;]+)\s*(?:;.*)?$")
FLAG_CONSUMER_RE = re.compile(r"^\s*(?:ret|jr|jp|call)\s+(?:z|nz|c|nc)\b")
MEMORY_A_LOAD_RE = re.compile(r"^\s*ld\s+a,\s*\[[^\]]+\]\s*$")
ZN_BRANCH_RE = re.compile(r"^\s*(?:ret|jr|jp|call)\s+(?:z|nz)\b")
FLAG_SETTER_RE = re.compile(r"^\s*(?:cp|and|or|xor|sub|sbc|add|adc|dec|inc|bit)\b")
FLAG_FLOW_BARRIER_RE = re.compile(
    r"^\s*(?:call|farcall|callfar)\b|^\s*(?:ret|jr|jp)\s+(?:z|nz|c|nc)\b"
)

SUSPICIOUS_DUPLICATE_COMMANDS = {
    "effectchance",
    "damagecalc",
    "applydamage",
}

PRIORITY_LABELS = {
    1: "P1",
    2: "P2",
    3: "P3",
}


@dataclass(frozen=True)
class Lead:
    priority: int
    path: Path
    lineno: int
    title: str
    detail: str
    evidence: str
    next_step: str

    @property
    def priority_label(self) -> str:
        return PRIORITY_LABELS[self.priority]

    def format(self, index: int) -> str:
        rel = self.path.relative_to(ROOT).as_posix()
        return "\n".join(
            (
                f"{index}. [{self.priority_label}] {self.title}",
                f"   at {rel}:{self.lineno}",
                f"   why: {self.detail}",
                f"   evidence: {self.evidence}",
                f"   next: {self.next_step}",
            )
        )


@dataclass(frozen=True)
class AsmBlock:
    label: str
    path: Path
    start: int
    lines: tuple[str, ...]

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def strip_comment(line: str) -> str:
    return line.split(";", 1)[0].rstrip()


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8", errors="replace")


def code_lines(path: Path) -> list[tuple[int, str, str]]:
    out: list[tuple[int, str, str]] = []
    for lineno, raw in enumerate(read_text(path).splitlines(), start=1):
        code = strip_comment(raw).strip()
        if code:
            out.append((lineno, code, raw.rstrip()))
    return out


def top_blocks(path: Path) -> list[AsmBlock]:
    lines = read_text(path).splitlines()
    starts: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        stripped = strip_comment(line).strip()
        if TOP_LABEL_RE.match(stripped):
            starts.append((index, stripped.rstrip(":")))

    blocks: list[AsmBlock] = []
    for pos, (start, label) in enumerate(starts):
        end = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines)
        blocks.append(AsmBlock(label=label, path=path, start=start + 1, lines=tuple(lines[start:end])))
    return blocks


def local_block(text: str, label: str, end_label: str) -> str:
    lines = text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        stripped = strip_comment(line).strip()
        if stripped in {label, f"{label}:"}:
            start = index
            break
    if start is None:
        return ""

    for index in range(start + 1, len(lines)):
        stripped = strip_comment(lines[index]).strip()
        if stripped in {end_label, f"{end_label}:"}:
            return "\n".join(lines[start:index])
    return "\n".join(lines[start:])


def find_label_line(path: Path, label: str) -> int:
    for lineno, code, _raw in code_lines(path):
        if code in {f"{label}:", f"{label}::", label}:
            return lineno
    return 1


def add_lead(
    leads: list[Lead],
    priority: int,
    path: Path,
    lineno: int,
    title: str,
    detail: str,
    evidence: str,
    next_step: str,
) -> None:
    leads.append(
        Lead(
            priority=priority,
            path=path,
            lineno=lineno,
            title=title,
            detail=detail,
            evidence=evidence,
            next_step=next_step,
        )
    )


def is_label(code: str) -> bool:
    return TOP_LABEL_RE.match(code) is not None or LOCAL_LABEL_RE.match(code) is not None


def audit_move_effect_scripts(leads: list[Lead]) -> str:
    scripts: list[tuple[str, int, list[tuple[int, str]]]] = []
    current_label: str | None = None
    current_start = 0
    current_commands: list[tuple[int, str]] = []

    for lineno, raw_line in enumerate(read_text(MOVE_EFFECTS).splitlines(), start=1):
        code = strip_comment(raw_line).strip()
        if not code:
            continue
        if MOVE_EFFECT_LABEL_RE.match(code):
            if current_label is not None:
                scripts.append((current_label, current_start, current_commands))
            current_label = code.rstrip(":")
            current_start = lineno
            current_commands = []
            continue
        if current_label is None:
            continue
        current_commands.append((lineno, code.split()[0]))

    if current_label is not None:
        scripts.append((current_label, current_start, current_commands))

    for label, start, commands in scripts:
        positions: dict[str, list[int]] = {}
        for lineno, command in commands:
            positions.setdefault(command, []).append(lineno)

        for command in sorted(SUSPICIOUS_DUPLICATE_COMMANDS):
            hit_lines = positions.get(command, [])
            if len(hit_lines) <= 1:
                continue
            add_lead(
                leads,
                2,
                MOVE_EFFECTS,
                hit_lines[1],
                f"{label} repeats `{command}`",
                "Repeated stateful battle-script commands can double-roll, double-apply, or desync later text/state.",
                f"{command} appears at lines {', '.join(str(line) for line in hit_lines)}",
                "Inspect the exact move script; if intentional, add a narrow comment or teach this triage script the exception.",
            )

        effectchance = positions.get("effectchance", [])
        checkhit = positions.get("checkhit", [])
        applydamage = positions.get("applydamage", [])
        if effectchance and checkhit and min(effectchance) < min(checkhit):
            add_lead(
                leads,
                2,
                MOVE_EFFECTS,
                min(effectchance),
                f"{label} rolls effect chance before hit check",
                "Secondary effects should not roll before the move has proven it can connect.",
                f"first effectchance line {min(effectchance)}, first checkhit line {min(checkhit)}",
                "Compare with nearby hit+secondary scripts in data/moves/effects.asm.",
            )
        if effectchance and applydamage and min(effectchance) > max(applydamage):
            add_lead(
                leads,
                2,
                MOVE_EFFECTS,
                min(effectchance),
                f"{label} rolls effect chance after damage application",
                "Late effectchance can use stale hit/substitute/faint state.",
                f"first effectchance line {min(effectchance)}, last applydamage line {max(applydamage)}",
                "Check whether the status/stat command should move before applydamage or be guarded differently.",
            )

    return f"move-effect scripts scanned={len(scripts)}"


def audit_raw_held_effect_compares(leads: list[Lead]) -> str:
    scanned = 0
    for path in sorted((ROOT / "engine" / "battle").rglob("*.asm")):
        lines = code_lines(path)
        for index, (lineno, code, raw) in enumerate(lines):
            if not HELD_COMPARE_RE.search(code):
                continue
            scanned += 1
            saw_raw = False
            saw_conversion = False
            for _back_lineno, back_code, _back_raw in reversed(lines[max(0, index - 10) : index]):
                if CONVERT_HELD_EFFECT_RE.search(back_code):
                    saw_conversion = True
                    break
                if RAW_ITEM_READ_RE.search(back_code):
                    saw_raw = True
                    break
            if saw_raw and not saw_conversion:
                add_lead(
                    leads,
                    1,
                    path,
                    lineno,
                    "raw item id compared to held-effect constant",
                    "`wEnemyMonItem` and `wBattleMonItem` store item ids; `HELD_*` comparisons need GetItemHeldEffect or a wrapper first.",
                    raw.strip(),
                    "Convert the item id to a held effect, or prove this block intentionally works with item ids and should compare against item constants.",
                )
    return f"held-effect compares scanned={scanned}"


def audit_boss_setup_classifiers(leads: list[Lead]) -> str:
    boss = read_text(BOSS_AI)
    setup = next((block for block in top_blocks(BOSS_AI) if block.label == "BossAI_IsSetupEffect"), None)
    current = next((block for block in top_blocks(BOSS_AI) if block.label == "BossAI_IsCurrentEnemySetupMove"), None)

    if setup is None:
        add_lead(
            leads,
            2,
            BOSS_AI,
            1,
            "missing shared setup classifier",
            "Boss AI plan/role code needs one effect-only setup classifier to avoid drift.",
            "BossAI_IsSetupEffect label not found",
            "Restore the shared classifier or update the invariant audit and all callers together.",
        )
        return "setup classifiers checked=missing shared helper"

    setup_text = setup.text
    for effect in ("EFFECT_RAIN_DANCE", "EFFECT_SUNNY_DAY"):
        if effect not in setup_text:
            add_lead(
                leads,
                2,
                BOSS_AI,
                setup.start,
                "weather setup missing from shared setup classifier",
                "Weather is scored as setup locally; plan/role projection should not forget it.",
                f"{effect} absent from BossAI_IsSetupEffect",
                "Either add the weather effect to the shared helper or document why weather must stay local-only.",
            )
    if "EFFECT_CURSE" in setup_text:
        add_lead(
            leads,
            2,
            BOSS_AI,
            setup.start,
            "type-dependent Curse leaked into effect-only setup classifier",
            "Ghost Curse and non-Ghost Curse have different behavior; the effect-only helper cannot classify both safely.",
            "BossAI_IsSetupEffect contains EFFECT_CURSE",
            "Move Curse handling to a current-move helper that can check enemy typing.",
        )

    if current is None:
        add_lead(
            leads,
            2,
            BOSS_AI,
            setup.start,
            "missing current-move setup classifier",
            "Current move scoring needs a type-aware wrapper for non-Ghost Curse.",
            "BossAI_IsCurrentEnemySetupMove label not found",
            "Add a wrapper that handles EFFECT_CURSE by checking BossAI_EnemyIsGhostType, then delegates to BossAI_IsSetupEffect.",
        )
    else:
        current_text = current.text
        for needle in ("EFFECT_CURSE", "BossAI_EnemyIsGhostType", "BossAI_IsSetupEffect"):
            if needle not in current_text:
                add_lead(
                    leads,
                    2,
                    BOSS_AI,
                    current.start,
                    "current-move setup classifier lost a required branch",
                    "Curse setup handling is only safe when the wrapper checks typing and delegates other effects.",
                    f"`{needle}` missing from BossAI_IsCurrentEnemySetupMove",
                    "Restore the Curse branch and rerun check_boss_ai_trace_invariants.py.",
                )

    for label in (
        "BossAI_ApplyPlanMoveBias",
        "BossAI_EvaluateActionLookahead",
        "BossAI_ApplyMultiTurnProjection",
    ):
        block = next((candidate for candidate in top_blocks(BOSS_AI) if candidate.label == label), None)
        if block is None:
            continue
        if "BossAI_IsSetupEffect" in block.text and "BossAI_IsCurrentEnemySetupMove" not in block.text:
            add_lead(
                leads,
                2,
                BOSS_AI,
                block.start,
                f"{label} uses effect-only setup helper on current move",
                "Current move scoring can know enemy type, so it should handle non-Ghost Curse correctly.",
                "call BossAI_IsSetupEffect",
                "Route current-move plan/projection checks through BossAI_IsCurrentEnemySetupMove.",
            )

    return "setup classifiers checked"


def audit_base_data_restore_patterns(leads: list[Lead]) -> str:
    checked = 0
    for block in top_blocks(BOSS_AI):
        text = block.text
        direct_mutation = re.search(r"\bcall\s+GetBaseData\b", text) is not None
        delegated_mutation = "call BossAI_LoadPublicThreatSourceSpecies" in text
        if "ld [wCurSpecies], a" not in text or not (direct_mutation or delegated_mutation):
            continue
        checked += 1
        if block.label == "BossAI_LoadPublicThreatSourceSpecies":
            continue
        first_write = text.find("ld [wCurSpecies], a")
        last_write = text.rfind("ld [wCurSpecies], a")
        save_before_write = text.find("ld a, [wCurSpecies]") != -1 and text.find("ld a, [wCurSpecies]") < first_write
        stack_save = save_before_write and "push af" in text[: first_write + 80]
        temp_save = save_before_write and "wBossAITemp" in text[: first_write + 160]
        restore_tail = text[last_write:] if last_write > first_write else ""
        if delegated_mutation and last_write == first_write:
            restore_tail = text[first_write:]
        restore_after = last_write > first_write and (
            "call GetBaseData" in restore_tail or "call nz, GetBaseData" in restore_tail
        )
        if delegated_mutation and last_write == first_write:
            restore_after = "call GetBaseData" in restore_tail or "call nz, GetBaseData" in restore_tail
        if not ((stack_save or temp_save) and restore_after):
            add_lead(
                leads,
                2,
                BOSS_AI,
                block.start,
                f"{block.label} mutates base-data species without obvious restore",
                "Boss AI helpers that inspect candidate species can poison global base-data mirrors for later scoring.",
                "block writes wCurSpecies and calls GetBaseData",
                "Prove every return restores active wCurSpecies and reloads base data, or add a narrow save/restore wrapper.",
            )

    items = read_text(AI_ITEMS)
    switch = read_text(AI_SWITCH)
    if "AI_CheckAbleToSwitchPreserveCurSpecies" not in items:
        add_lead(
            leads,
            2,
            AI_ITEMS,
            1,
            "legacy switch entrypoint no longer preserves base data",
            "Legacy switch helpers scan candidate species through GetBaseData and need an outer restore wrapper.",
            "AI_CheckAbleToSwitchPreserveCurSpecies missing",
            "Restore the wrapper or make each candidate scanner save and reload active base data itself.",
        )
    for label in ("SwitchOften", "SwitchRarely", "SwitchSometimes"):
        block = next((candidate for candidate in top_blocks(AI_ITEMS) if candidate.label == label), None)
        if block and "call AI_CheckAbleToSwitchPreserveCurSpecies" not in block.text:
            add_lead(
                leads,
                2,
                AI_ITEMS,
                block.start,
                f"{label} bypasses base-data-preserving switch wrapper",
                "Direct CheckAbleToSwitch calls can leave candidate base data loaded.",
                "call AI_CheckAbleToSwitchPreserveCurSpecies missing",
                "Route the caller back through AI_CheckAbleToSwitchPreserveCurSpecies.",
            )
    if "ld e, 0\n\tpush hl\n\tpush bc" not in switch:
        add_lead(
            leads,
            2,
            AI_SWITCH,
            find_label_line(AI_SWITCH, "FindEnemyMonsWithASuperEffectiveMove"),
            "legacy super-effective switch scan may leak a previous candidate result",
            "The per-candidate result register should reset before scanning each mon's moves.",
            "`ld e, 0` before the candidate move loop not found",
            "Reset e at the candidate boundary and rerun check_boss_ai_trace_invariants.py.",
        )

    return f"base-data mutation blocks checked={checked}"


def audit_known_rejected_leads(leads: list[Lead]) -> str:
    checked = 0

    allowed_move_desc_paths = {
        "constants/text_constants.asm",
        "home/names.asm",
        "docs/bug_hunt_labeled_findings_2026-04-26.md",
    }
    for path in sorted(ROOT.rglob("*.asm")) + sorted((ROOT / "docs").rglob("*.md")):
        rel = path.relative_to(ROOT).as_posix()
        text = read_text(path)
        if "MOVE_DESC_NAME_BROKEN" not in text:
            continue
        checked += 1
        if rel in allowed_move_desc_paths:
            continue
        line = next(
            lineno
            for lineno, raw in enumerate(text.splitlines(), start=1)
            if "MOVE_DESC_NAME_BROKEN" in raw
        )
        add_lead(
            leads,
            2,
            path,
            line,
            "dead move-description name route gained a live caller",
            "MOVE_DESC_NAME_BROKEN is intentionally quarantined because the generic name-table route uses the wrong bank.",
            "MOVE_DESC_NAME_BROKEN referenced outside the known quarantine/docs",
            "Replace the caller with engine/pokemon/print_move_description.asm or build a tested GetName route.",
        )

    attrs = read_text(ITEM_ATTRIBUTES)
    if re.search(r"item_attribute\s+[^;\n]*HELD_PREVENT_POISON", attrs):
        checked += 1
        poison_bias = local_block(read_text(BOSS_AI), ".ApplyPoisonContactRiskBias", ".ApplyDarkShieldChanceBias")
        if "HELD_PREVENT_POISON" not in poison_bias:
            add_lead(
                leads,
                2,
                BOSS_AI,
                find_label_line(BOSS_AI, ".ApplyPoisonContactRiskBias"),
                "poison-contact AI ignores a newly assigned poison-prevention item",
                "The mechanic checks HELD_PREVENT_POISON; if an item now owns that effect, Boss AI contact-risk modeling should too.",
                "data/items/attributes.asm assigns HELD_PREVENT_POISON",
                "Teach .ApplyPoisonContactRiskBias the public item prevention case or document why the item is not visible to the AI.",
            )

    return f"rejected-lead sentinels checked={checked}"


def audit_commented_flag_refreshes(leads: list[Lead]) -> str:
    checked = 0
    for root in ASM_SCAN_ROOTS:
        for path in sorted(root.rglob("*.asm")):
            lines = read_text(path).splitlines()
            for index, raw in enumerate(lines):
                if COMMENTED_FLAG_REFRESH_RE.match(raw) is None:
                    continue
                for next_index in range(index + 1, len(lines)):
                    code = strip_comment(lines[next_index]).strip()
                    if not code:
                        continue
                    if FLAG_CONSUMER_RE.match(code):
                        checked += 1
                        add_lead(
                            leads,
                            2,
                            path,
                            index + 1,
                            "commented-out flag refresh before conditional control flow",
                            "A disabled flag-setting instruction next to a flag-sensitive branch is easy to turn into stale-flag logic.",
                            f"`{raw.strip()}` before `{code}`",
                            "Trace the intended return/branch convention; either restore the flag refresh or remove the stale commented instruction.",
                        )
                    break

    return f"commented flag-refresh sentinels checked={checked}"


def audit_tm_tutor_cur_item_restore(leads: list[Lead]) -> str:
    text = read_text(TM_TUTOR)
    block = next((candidate for candidate in top_blocks(TM_TUTOR) if candidate.label == "TMTutorTeachAnyTM"), None)
    if block is None:
        add_lead(
            leads,
            2,
            TM_TUTOR,
            1,
            "TM Tutor helper missing",
            "TM Tutor state restoration cannot be checked without TMTutorTeachAnyTM.",
            "TMTutorTeachAnyTM label not found",
            "Restore the helper or remove this check if the feature was intentionally deleted.",
        )
        return "TM Tutor state check failed=missing helper"

    required = (
        "ld a, [wCurItem]\n\tpush af\n\tld a, NO_ITEM\n\tld [wCurItem], a\n\tfarcall TeachTMHM",
        "pop af\n\tld [wCurItem], a\n\tld a, 2\n\tld [wScriptVar], a",
        ".taught_restore_cur_item\n\tpop af\n\tld [wCurItem], a",
    )
    for needle in required:
        if needle not in text:
            add_lead(
                leads,
                2,
                TM_TUTOR,
                block.start,
                "TM Tutor may leak synthetic no-consume item state",
                "The tutor temporarily sets wCurItem to NO_ITEM to avoid TM consumption; both success and failure paths must restore the selected TM item.",
                f"missing pattern: {needle.splitlines()[0]}",
                "Restore wCurItem on every return after the NO_ITEM substitution and rerun check_release_smoke.py.",
            )
            break

    return "TM Tutor wCurItem restore checked"


def stale_flag_reason_before_load(codes: list[str], load_index: int) -> str | None:
    for previous in range(load_index - 1, max(-1, load_index - 8), -1):
        code = codes[previous].strip()
        if not code:
            continue
        if is_label(code):
            return "no nearby flag setter before the load"
        if FLAG_FLOW_BARRIER_RE.match(code):
            return f"flag state crosses `{code}` before the load"
        if FLAG_SETTER_RE.match(code):
            return None
    return "no nearby flag setter before the load"


def audit_memory_load_flag_branches(leads: list[Lead]) -> str:
    checked = 0
    for root in ASM_SCAN_ROOTS:
        for path in sorted(root.rglob("*.asm")):
            lines = read_text(path).splitlines()
            codes = [strip_comment(line).strip() for line in lines]
            for index in range(len(codes) - 1):
                code = codes[index]
                next_code = codes[index + 1]
                if MEMORY_A_LOAD_RE.match(code) is None or ZN_BRANCH_RE.match(next_code) is None:
                    continue
                checked += 1
                reason = stale_flag_reason_before_load(codes, index)
                if reason is None:
                    continue
                add_lead(
                    leads,
                    2,
                    path,
                    index + 1,
                    "memory load followed by conditional branch without local flag refresh",
                    "`ld a, [addr]` does not update flags; this branch may be reading an older comparison.",
                    f"{lines[index].strip()} / {lines[index + 1].strip()} ({reason})",
                    "Trace the intended condition. If the loaded value is the condition, insert `and a`; if the old flags are intentional, add a narrow comment or teach this scanner the idiom.",
                )
    return f"memory-load flag branches checked={checked}"


def find_memory_load_branch(codes: list[str]) -> int | None:
    for index in range(len(codes) - 1):
        if MEMORY_A_LOAD_RE.match(codes[index]) and ZN_BRANCH_RE.match(codes[index + 1]):
            return index
    return None


def run_self_test() -> int:
    cases = (
        (
            "move reorder stale battle-mode flags",
            (
                "\tcall .copy_move",
                "\tld a, [wBattleMode]",
                "\tjr z, .swap_moves",
            ),
            True,
        ),
        (
            "seconds helper stale minute flags",
            (
                "\tld a, [wHoursSince]",
                "\tand a",
                "\tjr nz, GetTimeElapsed_ExceedsUnitLimit",
                "\tld a, [wMinutesSince]",
                "\tjr nz, GetTimeElapsed_ExceedsUnitLimit",
            ),
            True,
        ),
        (
            "side-selection return-value idiom",
            (
                "\tld a, [wMonType]",
                "\tand a",
                "\tld a, [wPartyCount]",
                "\tjr z, .next_mon",
            ),
            False,
        ),
    )

    failures: list[str] = []
    for name, lines, should_flag in cases:
        codes = [strip_comment(line).strip() for line in lines]
        load_index = find_memory_load_branch(codes)
        if load_index is None:
            failures.append(f"{name}: no memory-load branch pair found")
            continue
        flagged = stale_flag_reason_before_load(codes, load_index) is not None
        if flagged != should_flag:
            failures.append(f"{name}: expected flagged={should_flag}, got {flagged}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("Self-test passed: stale flag heuristic catches known regressions without flagging the side-selection idiom.")
    return 0


def run_triage() -> tuple[list[Lead], list[str]]:
    leads: list[Lead] = []
    checked = [
        audit_move_effect_scripts(leads),
        audit_raw_held_effect_compares(leads),
        audit_boss_setup_classifiers(leads),
        audit_base_data_restore_patterns(leads),
        audit_known_rejected_leads(leads),
        audit_commented_flag_refreshes(leads),
        audit_tm_tutor_cur_item_restore(leads),
        audit_memory_load_flag_branches(leads),
    ]
    leads.sort(key=lambda lead: (lead.priority, lead.path.as_posix(), lead.lineno, lead.title))
    return leads, checked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-leads",
        type=int,
        default=25,
        help="maximum ranked leads to print (default: 25)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run small regression examples for the triage heuristics",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    try:
        leads, checked = run_triage()
    except FileNotFoundError as exc:
        print(f"FAIL: missing required file: {Path(exc.filename).relative_to(ROOT)}")
        return 1

    print("Bug hunt triage complete.")
    print("Checked:")
    for item in checked:
        print(f"  - {item}")

    if not leads:
        print("\nRanked leads: none found.")
        print("This is not proof of correctness; it means the known high-yield bug shapes are quiet.")
        return 0

    shown = leads[: max(args.max_leads, 0)]
    print(f"\nRanked leads: {len(leads)} found, showing {len(shown)}.")
    for index, lead in enumerate(shown, start=1):
        print(lead.format(index))
    if len(shown) < len(leads):
        print(f"\n{len(leads) - len(shown)} more lead(s) hidden by --max-leads.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
