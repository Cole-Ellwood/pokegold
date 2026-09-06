"""Shared static SM83 instruction parsing and register-write facts."""
from __future__ import annotations

import re


REGISTERS_8: frozenset[str] = frozenset({"a", "b", "c", "d", "e", "h", "l"})
REGISTER_PAIRS: frozenset[str] = frozenset({"af", "bc", "de", "hl", "sp"})


def pair_to_halves(pair: str) -> frozenset[str]:
    return {
        "af": frozenset({"a", "flags"}),
        "bc": frozenset({"b", "c"}),
        "de": frozenset({"d", "e"}),
        "hl": frozenset({"h", "l"}),
        "sp": frozenset({"sp"}),
    }.get(pair, frozenset())


def normalize_dest(token: str) -> str:
    return token.strip().rstrip(",").lower()


_INSTRUCTION_PATTERN = re.compile(r"^\s*([a-z][a-z0-9]*)(?:\s+(.+))?$", re.IGNORECASE)
_COMMENT_STRIP = re.compile(r";.*$")


def parse_instruction_line(line: str) -> tuple[str, list[str]] | None:
    stripped = _COMMENT_STRIP.sub("", line).strip()
    if not stripped:
        return None
    if stripped.endswith(":") or stripped.endswith("::"):
        return None
    if stripped.startswith(("INCLUDE ", "INCBIN ", "SECTION ", "ds ", "db ", "dw ", "dn ", "dl ", "MACRO ", "ENDM")):
        return None
    match = _INSTRUCTION_PATTERN.match(stripped)
    if not match:
        return None
    mnemonic = match.group(1).lower()
    operand_text = match.group(2) or ""
    operands = [tok.strip() for tok in operand_text.split(",")]
    if operands == [""]:
        operands = []
    return mnemonic, operands


# SM83 mnemonic -> (clobbered registers as tokens, sets flags, special)
# We model the clobber set per the operand position and shape rather than
# trying to enumerate every opcode encoding. The pattern dispatcher below
# converts an operand token (e.g. "bc", "[hl]", "a") into a clobber set.

def _clobbered_for_dest(operand: str) -> set[str]:
    token = normalize_dest(operand)
    if not token:
        return set()
    if token.startswith("[") and token.endswith("]"):
        # Memory store. No register clobber. The post-increment/decrement
        # variants of [hl+]/[hl-] update hl, captured separately below.
        if token in {"[hl+]", "[hli]"}:
            return {"h", "l"}
        if token in {"[hl-]", "[hld]"}:
            return {"h", "l"}
        return set()
    if token in REGISTERS_8:
        return {token}
    if token in REGISTER_PAIRS:
        return set(pair_to_halves(token))
    # Condition codes (z, nz, c, nc) are NOT clobber targets in `add hl, ...`
    # or similar — but ld doesn't accept them. Default empty.
    return set()


def clobbers_for_instruction(mnemonic: str, operands: list[str]) -> set[str]:
    """Static clobber inference for a single SM83 instruction.

    Returns the set of clobbered register tokens (e.g. {"a", "flags"}).
    Does NOT recurse into call targets — that's handled at the function level.
    """
    mnemonic = mnemonic.lower()
    clobbers: set[str] = set()

    if mnemonic in {"nop", "halt", "stop", "ei", "di", "reti", "ret"}:
        return clobbers

    if mnemonic in {"jr", "jp", "call", "rst"}:
        # call/rst/jp [hl] need transitive analysis at the function level.
        # `jp [hl]` clobbers nothing locally; the target call resolves elsewhere.
        if mnemonic == "call":
            # mark as needing-transitive at the call-graph layer
            return {"__needs_transitive__"}
        if mnemonic == "rst":
            return {"__needs_transitive__"}
        return clobbers

    if mnemonic in {"farcall", "callfar", "callba", "callab"}:
        # farcall ABI: clobbers a (mirrors target's exit c), hl (set before
        # target runs), and whatever the target clobbers transitively.
        return {"a", "h", "l", "__needs_transitive_farcall__"}

    if mnemonic == "homecall":
        return {"a", "__needs_transitive_homecall__"}

    if mnemonic == "push":
        # push doesn't clobber registers (it writes memory at SP).
        return clobbers

    if mnemonic == "pop":
        if operands:
            clobbers |= _clobbered_for_dest(operands[0])
        return clobbers

    if mnemonic in {"ld", "ldh", "ldi", "ldd"}:
        if operands:
            clobbers |= _clobbered_for_dest(operands[0])
        if any(normalize_dest(operand) in {"[hli]", "[hld]", "[hl+]", "[hl-]"} for operand in operands[1:]):
            clobbers |= {"h", "l"}
        if mnemonic == "ldi":
            clobbers |= {"h", "l"}
        if mnemonic == "ldd":
            clobbers |= {"h", "l"}
        return clobbers

    if mnemonic in {"add", "adc", "sub", "sbc"}:
        # add a, X / sub X / add hl, X
        if operands and normalize_dest(operands[0]) == "hl":
            clobbers |= {"h", "l", "flags"}
        elif operands and normalize_dest(operands[0]) == "sp" and mnemonic == "add":
            clobbers |= {"sp", "flags"}
        else:
            clobbers |= {"a", "flags"}
        return clobbers

    if mnemonic in {"and", "or", "xor"}:
        clobbers |= {"a", "flags"}
        return clobbers

    if mnemonic == "cp":
        clobbers |= {"flags"}
        return clobbers

    if mnemonic in {"inc", "dec"}:
        if operands:
            clobbers |= _clobbered_for_dest(operands[0])
        # inc bc/de/hl/sp do NOT set flags; inc on 8-bit registers does.
        if operands and normalize_dest(operands[0]) not in REGISTER_PAIRS:
            clobbers |= {"flags"}
        return clobbers

    if mnemonic in {"rlc", "rrc", "rl", "rr", "sla", "sra", "srl", "swap"}:
        if operands:
            clobbers |= _clobbered_for_dest(operands[0])
        clobbers |= {"flags"}
        return clobbers

    if mnemonic in {"rlca", "rrca", "rla", "rra"}:
        clobbers |= {"a", "flags"}
        return clobbers

    if mnemonic == "bit":
        clobbers |= {"flags"}
        return clobbers

    if mnemonic in {"res", "set"}:
        if len(operands) >= 2:
            clobbers |= _clobbered_for_dest(operands[1])
        return clobbers

    if mnemonic == "cpl":
        clobbers |= {"a", "flags"}
        return clobbers

    if mnemonic == "daa":
        clobbers |= {"a", "flags"}
        return clobbers

    if mnemonic in {"scf", "ccf"}:
        clobbers |= {"flags"}
        return clobbers

    # Unknown mnemonic — could be a local macro. Mark as unanalyzed.
    return {"__unknown__:" + mnemonic}
