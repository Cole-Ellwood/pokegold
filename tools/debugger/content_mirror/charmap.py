"""Charmap-string encoding shared by text and labeled-data db continuations."""

from __future__ import annotations

import re

from .helpers import evaluate_int_expression


RGBDS_DECIMAL_FORMAT_RE = re.compile(r"\{d:(?P<expr>[^}]+)\}")


def append_charmap_token(
    out: list[int],
    token: str,
    *,
    charmap: dict[str, int],
    errors: list[str],
    line: int,
) -> None:
    value = charmap.get(token)
    if value is None:
        errors.append(f"line_{line}:unresolved_charmap_token={token}")
        return
    out.append(int(value) & 0xff)


def expand_rgbds_string_formats(
    text: str,
    *,
    constants: dict[str, int],
    errors: list[str],
    line: int,
) -> str:
    def replace_decimal(match: re.Match[str]) -> str:
        expr = match.group("expr").strip()
        value = evaluate_int_expression(expr, constants)
        if value is None:
            errors.append(f"line_{line}:unresolved_text_decimal={expr}")
            return ""
        return str(value)

    return RGBDS_DECIMAL_FORMAT_RE.sub(replace_decimal, text)


def encode_charmap_string(
    text: str,
    *,
    charmap: dict[str, int],
    errors: list[str],
    line: int,
) -> list[int]:
    out: list[int] = []
    tokens = sorted((str(token) for token in charmap), key=len, reverse=True)
    index = 0
    while index < len(text):
        match = next((token for token in tokens if text.startswith(token, index)), "")
        if not match:
            errors.append(f"line_{line}:unmapped_text={text[index]}")
            index += 1
            continue
        out.append(int(charmap[match]) & 0xff)
        index += len(match)
    return out
