from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .provenance import display_path, resolve_path


LABEL_RE = re.compile(r"^(?P<label>[A-Za-z_.$@][\w.$@]*):{1,2}(?:\s|$)")
LD_A_RE = re.compile(r"^ld\s+a\s*,\s*(?P<value>[^;\s]+)", re.IGNORECASE)
MACRO_SWITCH_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9_.$@]*set_wram_bank)\s+(?P<value>[^;\s]+)",
    re.IGNORECASE,
)
SET_WRAM_BANK_TRANSFER_RE = re.compile(
    r"^(?:call|jp)(?:\s+(?:nz|z|nc|c),)?\s+setwrambank\b",
    re.IGNORECASE,
)

DEFAULT_SCAN_ROOTS = (
    "home",
    "engine",
    "ram",
    "macros",
    "data",
    "maps",
    "main.asm",
    "home.asm",
)
EXEMPT_SOURCE_FILES = {
    "home/wram_bank.asm",
}


@dataclass
class RoutineState:
    routine: str = "<top-level>"
    current_bank: int | None = 1
    explicit_stack: list[tuple[int | None, int, str]] = field(default_factory=list)
    last_ld_a: int | None = None


def build_wram_bank_hazard_report(
    *,
    source_files: tuple[str, ...] = (),
    root: Path = ROOT,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    paths: list[Path] = []
    for path_text in source_files:
        path = resolve_path(path_text, root=root)
        if not path.exists():
            errors.append(f"missing source file: {path_text}")
            continue
        if path.is_dir():
            paths.extend(iter_source_files(path))
        else:
            paths.append(path)
    if not source_files:
        paths = default_source_files(root)

    findings: list[dict[str, Any]] = []
    for path in unique_paths(paths):
        findings.extend(scan_wram_bank_hazards(path, root=root))

    passed = not findings and not errors
    return {
        "schema_version": 1,
        "kind": "unified_debugger_wram_bank_hazard_report",
        "root": str(root),
        "source_files": [display_path(path, root=root) for path in unique_paths(paths)],
        "source_file_count": len(unique_paths(paths)),
        "valid": not errors,
        "passed": passed,
        "finding_count": len(findings),
        "findings": findings,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "commands": [
            "python tools\\audit\\check_rsvbk_write_discipline.py",
            "python -m tools.debugger watch --reset-sentinel --rom pokegold.gbc --symbols pokegold.sym --save-state <state-before-trigger> --frames 1200 --context-frames 20",
        ],
        "known_limits": [
            "This is a static assembly hazard scan, not a proof that the code path executed.",
            "It models explicit push/pop and direct WRAM bank switches inside one source routine; it does not expand every RGBDS macro body.",
        ],
    }


def scan_wram_bank_hazards(path: Path, *, root: Path) -> list[dict[str, Any]]:
    if display_path(path, root=root).replace("\\", "/") in EXEMPT_SOURCE_FILES:
        return []
    state = RoutineState()
    findings: list[dict[str, Any]] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for lineno, raw in enumerate(lines, start=1):
        code = strip_comment(raw).strip()
        label_match = LABEL_RE.match(code)
        label = label_match.group("label") if label_match else ""
        if label and not label.startswith("."):
            state = RoutineState(routine=label)
            code = code[label_match.end():].strip() if label_match else ""
        if not code:
            continue

        normalized = normalize_instruction(code)
        value = parse_ld_a_value(normalized)
        if value is not None:
            state.last_ld_a = value
            continue

        macro_bank = parse_macro_switch(normalized)
        if macro_bank is not None or is_rsvbk_write(normalized):
            target = macro_bank if macro_bank is not None else state.last_ld_a
            state.current_bank = target
            state.last_ld_a = None
            continue

        if is_call_set_wram_bank(normalized):
            target = state.last_ld_a
            if state.current_bank != 1 or target != 1:
                findings.append(
                    finding(
                        type="set_wram_bank_call",
                        severity=1,
                        title="SetWRAMBank call can return through the wrong WRAMX bank",
                        path=path,
                        root=root,
                        line=lineno,
                        routine=state.routine,
                        text=raw,
                        evidence=[
                            "SetWRAMBank writes rSVBK before its ret.",
                            "If the selected WRAMX bank differs from the stack bank, ret reads the return address from the wrong bank.",
                        ],
                    )
                )
            state.current_bank = target
            state.last_ld_a = None
            continue

        if is_push(normalized):
            state.explicit_stack.append((state.current_bank, lineno, raw))
            state.last_ld_a = None
            continue

        if is_pop(normalized):
            pushed = state.explicit_stack.pop() if state.explicit_stack else None
            if pushed is not None:
                pushed_bank, push_line, push_text = pushed
                if pushed_bank != state.current_bank:
                    findings.append(
                        finding(
                            type="stack_bank_mismatch",
                            severity=1,
                            title="Explicit stack value is popped under a different WRAMX bank",
                            path=path,
                            root=root,
                            line=lineno,
                            routine=state.routine,
                            text=raw,
                            evidence=[
                                f"push at line {push_line} used WRAM bank {render_bank(pushed_bank)}: {push_text.strip()}",
                                f"pop at line {lineno} uses WRAM bank {render_bank(state.current_bank)}.",
                            ],
                        )
                    )
            state.last_ld_a = None
            continue

        if is_ret(normalized):
            if state.current_bank != 1:
                findings.append(
                    finding(
                        type="ret_while_wram_switched",
                        severity=1,
                        title="Routine returns while WRAMX bank 1 is not selected",
                        path=path,
                        root=root,
                        line=lineno,
                        routine=state.routine,
                        text=raw,
                        evidence=[
                            f"current static WRAM bank model is {render_bank(state.current_bank)} at ret.",
                            "Caller return addresses are expected to live on the WRAMX bank-1 stack.",
                        ],
                    )
                )
            state.last_ld_a = None
            continue

        if not normalized.startswith("ldh [hwrambank]"):
            state.last_ld_a = None
    return findings


def default_source_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for item in DEFAULT_SCAN_ROOTS:
        path = root / item
        if not path.exists():
            continue
        if path.is_dir():
            paths.extend(iter_source_files(path))
        else:
            paths.append(path)
    return paths


def iter_source_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() in {".asm", ".inc"} else []
    return [
        item
        for item in path.rglob("*")
        if item.is_file()
        and item.suffix.lower() in {".asm", ".inc"}
        and ".git" not in item.parts
        and ".local" not in item.parts
    ]


def finding(
    *,
    type: str,
    severity: int,
    title: str,
    path: Path,
    root: Path,
    line: int,
    routine: str,
    text: str,
    evidence: list[str],
) -> dict[str, Any]:
    source_file = display_path(path, root=root)
    return {
        "type": type,
        "severity": severity,
        "title": title,
        "source_file": source_file,
        "line": line,
        "routine": routine,
        "text": text.strip(),
        "evidence": evidence,
        "commands": [
            f"python -m tools.debugger wram-bank-hazards --source-file {source_file}",
            "python -m tools.debugger trace-instructions --symbol "
            f"{routine} --watch-symbol hWRAMBank --execute --require-hit",
        ],
    }


def parse_label(code: str) -> str:
    match = LABEL_RE.match(code)
    return match.group("label") if match else ""


def parse_ld_a_value(code: str) -> int | None:
    match = LD_A_RE.match(code)
    if not match:
        return None
    return parse_bank_value(match.group("value"))


def parse_macro_switch(code: str) -> int | None:
    match = MACRO_SWITCH_RE.match(code)
    if not match:
        return None
    return parse_bank_value(match.group("value"))


def parse_bank_value(value: str) -> int | None:
    text = value.strip().rstrip(",")
    if not text:
        return None
    if text.startswith("$"):
        try:
            return int(text[1:], 16)
        except ValueError:
            return None
    try:
        return int(text, 0)
    except ValueError:
        return None


def strip_comment(line: str) -> str:
    return line.split(";", 1)[0]


def normalize_instruction(code: str) -> str:
    return " ".join(code.replace("\t", " ").strip().lower().split())


def is_call_set_wram_bank(code: str) -> bool:
    return bool(SET_WRAM_BANK_TRANSFER_RE.match(code))


def is_rsvbk_write(code: str) -> bool:
    return code.startswith("ldh [rsvbk], a") or code.startswith("ld [rsvbk], a")


def is_push(code: str) -> bool:
    return code.startswith("push ")


def is_pop(code: str) -> bool:
    return code.startswith("pop ")


def is_ret(code: str) -> bool:
    return code == "ret" or code.startswith("ret ")


def render_bank(bank: int | None) -> str:
    return "unknown" if bank is None else str(bank)


def unique_paths(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        out.append(path)
    return out
