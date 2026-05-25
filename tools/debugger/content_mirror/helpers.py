"""Shared regexes, parsers, and factories for the content-mirror package.

Pure (no I/O, no other content_mirror imports). Every per-content-type module
depends on this; nothing here depends on them.
"""

from __future__ import annotations

import re
from typing import Any


LABEL_RE = re.compile(r"^\s*(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*)(?P<scope>::|:)")
LOCAL_LABEL_ONLY_RE = re.compile(r"^\s*(?P<label>\.[A-Za-z_.$][A-Za-z0-9_.$]*)\s*$")
TOKEN_RE = re.compile(r"^\s*(?P<token>[A-Za-z_?][A-Za-z0-9_?]*)\b")
INCBIN_RE = re.compile(r"\bINCBIN\s+\"(?P<path>[^\"]+)\"")
INCBIN_ARGS_RE = re.compile(r"\bINCBIN\s+(?P<args>.+)$")
SYM_LABEL_RE = re.compile(r"^(?P<bank>[0-9A-Fa-f]{2}):(?P<addr>[0-9A-Fa-f]{4})\s+(?P<label>\S+)$")
SYM_CONSTANT_RE = re.compile(r"^(?P<value>[0-9A-Fa-f]{1,8})\s+(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*)$")
DEF_EQU_RE = re.compile(r"^DEF\s+(?P<name>[A-Za-z_.$][A-Za-z0-9_.$]*)\s+EQU\s+(?P<expr>.+)$")
DEF_ASSIGN_RE = re.compile(r"^DEF\s+(?P<name>[A-Za-z_.$][A-Za-z0-9_.$]*)\s*=\s*(?P<expr>.+)$")
DEF_EQUS_RE = re.compile(r"^DEF\s+(?P<name>[A-Za-z_.$][A-Za-z0-9_.$]*)\s+EQUS\s+\"(?P<value>[^\"]+)\"$")

ALLOWED_INCBIN_TABLE_DIRECTIVES = {"table_width", "assert_table_length", "assert_table_length_nopad"}
DATA_BYTE_DIRECTIVES = {"db", "dw", "dn"}
DATA_STRING_CONTINUATION_DIRECTIVES = {"next", "line", "page", "para", "cont"}
ALLOWED_DATA_BLOCK_DIRECTIVES = (
    DATA_BYTE_DIRECTIVES | DATA_STRING_CONTINUATION_DIRECTIVES | ALLOWED_INCBIN_TABLE_DIRECTIVES
)


def strip_comment(line: str) -> str:
    out = []
    in_quote = False
    escaped = False
    for char in line:
        if char == '"' and not escaped:
            in_quote = not in_quote
        if char == ";" and not in_quote:
            break
        out.append(char)
        escaped = char == "\\" and not escaped
    return "".join(out)


def split_label(line: str) -> tuple[str, str]:
    match = LABEL_RE.match(line)
    if match:
        return match.group("label"), line[match.end():].strip()
    match = LOCAL_LABEL_ONLY_RE.match(line)
    if match:
        return match.group("label"), ""
    return "", line.strip()


def code_after_label(line: str) -> str:
    return split_label(line)[1]


def symbol_name_for_label(label: str, *, current_global_label: str) -> str:
    if label.startswith(".") and current_global_label:
        return f"{current_global_label}{label}"
    return label


def first_token(line: str) -> str:
    match = TOKEN_RE.match(line.strip())
    return match.group("token") if match else ""


def parse_incbin_entries(code: str, *, equs_macros: dict[str, str] | None = None) -> list[dict[str, Any]]:
    match = INCBIN_ARGS_RE.search(code.strip())
    if not match:
        return []
    args = split_macro_args(match.group("args"))
    if not args:
        return []
    aliases = equs_macros or {}
    if len(args) == 2 and args[1].strip() in aliases:
        args = [args[0], *split_macro_args(aliases[args[1].strip()])]
    path = args[0].strip()
    if len(path) < 2 or not path.startswith('"') or not path.endswith('"'):
        return []
    return [{"path": path[1:-1], "args": args}]


def parse_int_literal(value: str) -> int:
    text = value.strip()
    if text.startswith("$"):
        return int(text[1:], 16)
    if text.lower().startswith("0x"):
        return int(text, 16)
    return int(text)


def split_macro_args(text: str) -> list[str]:
    fields = []
    current = []
    in_quote = False
    depth = 0
    for char in text.strip():
        if char == '"':
            in_quote = not in_quote
        elif not in_quote and char in "([{":
            depth += 1
        elif not in_quote and char in ")]}" and depth:
            depth -= 1
        if char == "," and not in_quote and depth == 0:
            fields.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    if current:
        fields.append("".join(current).strip())
    return fields


def evaluate_int_expression(expr: str, constants: dict[str, int]) -> int | None:
    text = str(expr).strip()
    if not text:
        return None
    if text in constants:
        return int(constants[text])
    text = re.sub(r"\$([0-9A-Fa-f]+)", r"0x\1", text)
    text = re.sub(r"%([01]+)", r"0b\1", text)
    unresolved: list[str] = []

    def replace_name(match: re.Match[str]) -> str:
        name = match.group(0)
        if name in constants:
            return str(constants[name])
        unresolved.append(name)
        return name

    text = re.sub(r"\b[A-Za-z_.$][A-Za-z0-9_.$]*\b", replace_name, text)
    if unresolved:
        return None
    if not re.fullmatch(r"[0-9xXa-fA-FbBoO\s<>()+\-*/|&]+", text):
        return None
    try:
        return int(eval(text, {"__builtins__": {}}, {}))
    except (ArithmeticError, NameError, SyntaxError, TypeError, ValueError):
        return None


def unique_list(values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def dict_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list | tuple):
        return [item for item in value if isinstance(item, dict)]
    return []


def is_quoted_rgbds_string(value: str) -> bool:
    text = value.strip()
    return len(text) >= 2 and text[0] == '"' and text[-1] == '"'


def first_mismatch(expected: bytes, actual: bytes) -> int:
    for index, (expected_byte, actual_byte) in enumerate(zip(expected, actual)):
        if expected_byte != actual_byte:
            return index
    if len(expected) != len(actual):
        return min(len(expected), len(actual))
    return -1


def format_optional_byte(value: int | None) -> str:
    return "<missing>" if value is None else f"${value:02x}"


def hex_window(data: bytes, index: int, *, radius: int = 8) -> str:
    if not data:
        return "<empty>"
    start = max(0, index - radius)
    end = min(len(data), index + radius + 1)
    return " ".join(f"{byte:02x}" for byte in data[start:end])


def padded_fields(row: dict[str, Any], count: int) -> list[str]:
    fields = [str(item).strip() for item in row.get("fields", [])]
    if len(fields) < count:
        fields.extend([""] * (count - len(fields)))
    return fields


def append_count(out: list[int], rows: list[dict[str, Any]], section: str, errors: list[str]) -> None:
    count = len(rows)
    if count > 0xff:
        errors.append(f"{section}_count_too_large={count}")
    out.append(count & 0xff)


def content_invariant(
    *,
    invariant_id: str,
    invariant_type: str,
    status: str,
    severity: int,
    title: str,
    source_file: str,
    line: int = 0,
    evidence: list[str] | None = None,
    commands: list[str] | None = None,
    related_files: list[str] | None = None,
    related_symbols: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": invariant_id,
        "type": invariant_type,
        "status": status,
        "severity": int(severity),
        "title": title,
        "source_file": source_file,
        "line": int(line),
        "evidence": unique_list(evidence or []),
        "commands": unique_list(commands or []),
        "related_files": unique_list(related_files or []),
        "related_symbols": unique_list(related_symbols or []),
    }


def source_commands(source_file: str) -> list[str]:
    return [
        f"python -m tools.debugger content-mirror --source-file {source_file}",
        f"python -m tools.debugger expect --source-file {source_file} --expect report-valid",
        f"python -m tools.debugger provenance --source-file {source_file}",
        f"python -m tools.debugger compare --changed-file {source_file}",
    ]
