"""Target-state predicate language for deity-mode navigation (Phase 1, Task 1).

One query dialect shared by ``navigate`` / ``taint`` / ``replay`` / ``watch``:
a conjunction of clauses describing a *reachable* game state. Examples::

    battle(boss=MORTY) and turn==3 and enemy_active=GENGAR
    map=ROUTE_29 and facing=UP
    party_has(species=TYPHLOSION, level>=30)
    wild_battle and map=ROUTE_29

The point of parsing *and validating* up front is the Task-1 guarantee: a
typo'd field, an unknown predicate function, or a type mismatch must fail **at
parse**, not after the navigator has burned 100000 frames searching for a
state that can never match.

This module is pure logic — no emulator, no ROM. ``parse`` returns a structured
``Predicate``; ``evaluate`` checks one against a flat dict of observed,
RAM-derived values. The navigator (a later Phase-1 slice) is responsible for
populating that observed dict from ``runtime_state`` each frame; this module
owns only the *language*, not the driving.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


class PredicateError(ValueError):
    """A predicate failed to parse or validate. Carries a human-facing message."""


# --- vocabulary -------------------------------------------------------------
#
# Curated but extensible. A field/function/flag absent from these tables is a
# parse-time error, which is exactly the "fail early, not at frame 100000"
# guarantee. Grow these as the navigator learns to observe more state.

# Comparison fields and their value type. ``int`` fields only accept integer
# literals; ``str`` fields accept bare identifiers (species/map/facing names).
COMPARISON_FIELDS: dict[str, str] = {
    "turn": "int",
    "level": "int",
    "badges": "int",
    "map": "str",
    "facing": "str",
    "script": "str",
    "enemy_active": "str",
    "player_active": "str",
}

# Predicate functions and the argument names each accepts.
PREDICATE_FUNCTIONS: dict[str, frozenset[str]] = {
    "battle": frozenset({"boss"}),
    "party_has": frozenset({"species", "level"}),
    "cry": frozenset({"species"}),
}

# Bare flags: a clause that is just a name, asserting a boolean condition.
FLAGS: frozenset[str] = frozenset({"battle", "wild_battle"})

# Comparison operators, longest first so ``>=`` is matched before ``>``. ``=``
# is an accepted alias for ``==``.
_OPERATORS: tuple[str, ...] = ("==", "!=", ">=", "<=", "=", ">", "<")
_INT_OPERATORS: frozenset[str] = frozenset({"==", "!=", "=", ">=", "<=", ">", "<"})
_STR_OPERATORS: frozenset[str] = frozenset({"==", "!=", "="})

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_CALL_RE = re.compile(r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)\((?P<args>.*)\)$")
# Split on the word ``and`` (case-insensitive), surrounded by whitespace.
_AND_SPLIT_RE = re.compile(r"\s+and\s+", re.IGNORECASE)


# --- AST ---------------------------------------------------------------------


@dataclass(frozen=True)
class Comparison:
    field: str
    op: str  # normalized: "=" becomes "=="
    value: Any  # int for int fields, str for str fields

    def describe(self) -> str:
        return f"{self.field}{self.op}{self.value}"


@dataclass(frozen=True)
class Call:
    name: str
    # arg name -> (op, value); e.g. party_has(level>=30) -> {"level": (">=", 30)}
    args: tuple[tuple[str, str, Any], ...]

    def describe(self) -> str:
        inner = ", ".join(f"{name}{op}{value}" for name, op, value in self.args)
        return f"{self.name}({inner})"


@dataclass(frozen=True)
class Flag:
    name: str

    def describe(self) -> str:
        return self.name


Clause = Comparison | Call | Flag


@dataclass(frozen=True)
class Predicate:
    """A conjunction of clauses. ``source`` is the original text for messages."""

    clauses: tuple[Clause, ...]
    source: str

    def describe(self) -> str:
        return " and ".join(clause.describe() for clause in self.clauses)


# --- parsing -----------------------------------------------------------------


def _split_operator(text: str) -> tuple[str, str, str] | None:
    """Return (lhs, operator, rhs) for the first operator found, else None."""
    for op in _OPERATORS:
        idx = text.find(op)
        if idx > 0:  # operator must not be at position 0 (needs a left side)
            return text[:idx].strip(), op, text[idx + len(op) :].strip()
    return None


def _coerce_value(field: str, field_type: str, raw: str) -> Any:
    raw = raw.strip()
    if field_type == "int":
        try:
            return int(raw, 0)
        except ValueError as exc:
            raise PredicateError(
                f"{field!r} expects an integer, got {raw!r}"
            ) from exc
    # str field: accept a bare identifier (species/map/facing constant).
    if not _IDENT_RE.match(raw):
        raise PredicateError(
            f"{field!r} expects an identifier (e.g. MORTY, ROUTE_29), got {raw!r}"
        )
    return raw


def _parse_comparison(field: str, op: str, rhs: str) -> Comparison:
    if field not in COMPARISON_FIELDS:
        raise PredicateError(
            f"unknown field {field!r}; known fields: "
            f"{', '.join(sorted(COMPARISON_FIELDS))}"
        )
    field_type = COMPARISON_FIELDS[field]
    allowed = _INT_OPERATORS if field_type == "int" else _STR_OPERATORS
    if op not in allowed:
        raise PredicateError(
            f"operator {op!r} not valid for {field_type} field {field!r}; "
            f"allowed: {', '.join(sorted(allowed))}"
        )
    normalized = "==" if op == "=" else op
    return Comparison(field=field, op=normalized, value=_coerce_value(field, field_type, rhs))


def _parse_call(name: str, raw_args: str) -> Call:
    if name not in PREDICATE_FUNCTIONS:
        raise PredicateError(
            f"unknown predicate function {name!r}; known: "
            f"{', '.join(sorted(PREDICATE_FUNCTIONS))}"
        )
    allowed_args = PREDICATE_FUNCTIONS[name]
    parsed: list[tuple[str, str, Any]] = []
    seen: set[str] = set()
    for piece in (p for p in raw_args.split(",") if p.strip()):
        split = _split_operator(piece)
        if split is None:
            raise PredicateError(
                f"argument {piece.strip()!r} to {name}() needs an operator "
                f"(e.g. species=GENGAR, level>=30)"
            )
        arg_name, op, rhs = split
        if arg_name not in allowed_args:
            raise PredicateError(
                f"{name}() has no argument {arg_name!r}; allowed: "
                f"{', '.join(sorted(allowed_args)) or '(none)'}"
            )
        if arg_name in seen:
            raise PredicateError(f"{name}() repeats argument {arg_name!r}")
        seen.add(arg_name)
        # Treat a function arg like a comparison field if we know its type;
        # otherwise default to identifier (species/boss are str, level is int).
        arg_type = COMPARISON_FIELDS.get(arg_name, "str")
        allowed_ops = _INT_OPERATORS if arg_type == "int" else _STR_OPERATORS
        if op not in allowed_ops:
            raise PredicateError(
                f"operator {op!r} not valid for argument {arg_name!r} of {name}()"
            )
        normalized = "==" if op == "=" else op
        parsed.append((arg_name, normalized, _coerce_value(arg_name, arg_type, rhs)))
    return Call(name=name, args=tuple(parsed))


def _parse_clause(text: str) -> Clause:
    text = text.strip()
    if not text:
        raise PredicateError("empty clause (check for a stray 'and')")

    call_match = _CALL_RE.match(text)
    if call_match:
        return _parse_call(call_match.group("name"), call_match.group("args"))

    split = _split_operator(text)
    if split is not None:
        field, op, rhs = split
        return _parse_comparison(field, op, rhs)

    # No parens, no operator -> a bare flag.
    if not _IDENT_RE.match(text):
        raise PredicateError(f"cannot parse clause {text!r}")
    if text not in FLAGS:
        raise PredicateError(
            f"unknown flag {text!r}; known flags: {', '.join(sorted(FLAGS))}"
        )
    return Flag(name=text)


def parse(source: str) -> Predicate:
    """Parse a predicate string into a validated ``Predicate``.

    Raises ``PredicateError`` with a human-facing message on any unknown
    field/function/flag, bad operator, or type mismatch.
    """
    if not source or not source.strip():
        raise PredicateError("empty predicate")
    stripped = source.strip()
    # A leading or trailing bare ``and`` survives the inner-whitespace split, so
    # catch it explicitly with the same message a doubled ``and`` would give.
    if re.search(r"(?i)(^and\b|\band$)", stripped):
        raise PredicateError("empty clause (check for a stray 'and')")
    clauses = tuple(_parse_clause(part) for part in _AND_SPLIT_RE.split(stripped))
    return Predicate(clauses=clauses, source=stripped)


# --- evaluation --------------------------------------------------------------


@dataclass(frozen=True)
class EvalResult:
    satisfied: bool
    unmet: tuple[str, ...]  # human-facing descriptions of the clauses not (yet) met


def _compare(op: str, observed: Any, target: Any) -> bool:
    if op == "==":
        return observed == target
    if op == "!=":
        return observed != target
    # Ordered comparisons only make sense for numbers.
    try:
        if op == ">=":
            return observed >= target
        if op == "<=":
            return observed <= target
        if op == ">":
            return observed > target
        if op == "<":
            return observed < target
    except TypeError:
        return False
    return False


def _clause_satisfied(clause: Clause, observed: dict[str, Any]) -> bool:
    if isinstance(clause, Flag):
        return bool(observed.get(clause.name))
    if isinstance(clause, Comparison):
        if clause.field not in observed:
            return False  # cannot confirm an unobserved field
        return _compare(clause.op, observed[clause.field], clause.value)
    # Call: the function name must be observed truthy, and every arg must match
    # the same-named observed key (e.g. battle(boss=MORTY) -> observed["battle"]
    # truthy and observed["boss"] == "MORTY").
    if not observed.get(clause.name):
        return False
    for arg_name, op, value in clause.args:
        if arg_name not in observed:
            return False
        if not _compare(op, observed[arg_name], value):
            return False
    return True


def evaluate(predicate: Predicate, observed: dict[str, Any]) -> EvalResult:
    """Check a parsed predicate against observed RAM-derived values.

    ``observed`` is a flat dict the navigator builds from ``runtime_state``: it
    maps field/flag/arg names to their current values (e.g.
    ``{"battle": True, "boss": "MORTY", "turn": 3}``). A clause referencing a
    key not present in ``observed`` is treated as *not satisfied* (the navigator
    cannot confirm it), so ``evaluate`` never claims a state it could not see.
    """
    unmet = tuple(
        clause.describe()
        for clause in predicate.clauses
        if not _clause_satisfied(clause, observed)
    )
    return EvalResult(satisfied=not unmet, unmet=unmet)
