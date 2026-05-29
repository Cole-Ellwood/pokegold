"""tdb — trace query language for the unified debugger.

P3 first slice. A small declarative language that runs against the
existing effect-trace evidence model and returns matches with the
underlying event's proof vector preserved.

Grammar (this slice)
--------------------

    query    := or_expr
    or_expr  := and_expr ("or" and_expr)*
    and_expr := not_expr ("and" not_expr)*
    not_expr := "not" not_expr
              | "(" or_expr ")"
              | predicate
    predicate := name "(" arglist ")"
    arglist  := arg ("," arg)*
    arg      := name "=" value
    value    := hex_int | dec_int | identifier | quoted_string

Predicates (this slice)
-----------------------

- ``writes(addr=$X)``       — effect.access == "write" and address matches
- ``writes(addr=$X, bank=N)`` — additionally bank-exact match
- ``reads(reg=R)``           — effect.access == "read" and (reg = R OR value_source = R)
- ``reads(addr=$X)``         — effect.access == "read" and address matches
- ``executes(pc=$X)``        — instruction frame pc match (bank-aware if ``$BB:AAAA``)
- ``executes(pc=Label)``     — instruction frame pc_label exact / prefix match

Combinators:

- ``and``, ``or``, ``not``, parens.

Output
------

A list of match dicts shaped:

    {
      "kind": "tdb_match",
      "predicate": "<canonical predicate string>",
      "seq": <int>,
      "pc_bank_address": <str>,
      "pc_label": <str>,
      "address_key": <str|"">,
      "value_hex": <str|"">,
      "proof_status": <str>,
      "evidence_atom_source": <"effect"|"frame">,
    }

Bank-exactness follows the P0 proof boundary: if the user requests
``addr=$X, bank=N`` and the event carries a different bank, the event
is rejected outright. If the event has no observed bank, the match is
allowed but the result's proof_status is downgraded to ``planned_only``
with ``proof_downgrade_reason=bank_unverified`` recorded in the match.

Out of scope for this slice
---------------------------

- ``caller=`` / ``between(A, B)`` span predicates (next P3 slice; requires
  call-stack reconstruction from the instruction trace).
- ``at bank=`` global filter (next P3 slice).
- ``frame>``/``<``/``==`` range filters (next P3 slice).
- ``--explain`` evaluation plan output (next P3 slice).

The predicate API is open: register more by adding entries to PREDICATES
and the corresponding evaluation closure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from .catalog import ROOT
from .reporting import load_reports


# ---------------------------------------------------------------------------
# Grammar tokens
# ---------------------------------------------------------------------------


TOKEN_RE = re.compile(
    r"""
    \s+                              |  # whitespace
    (?P<lparen>\()                   |
    (?P<rparen>\))                   |
    (?P<comma>,)                     |
    (?P<eq>=)                        |
    (?P<kw_and>\band\b)              |
    (?P<kw_or>\bor\b)                |
    (?P<kw_not>\bnot\b)              |
    (?P<hex>\$[0-9A-Fa-f]+)          |
    (?P<bankhex>[0-9A-Fa-f]{2}:[0-9A-Fa-f]{4}) |  # banked addresses 01:D141
    (?P<int>\d+)                     |
    (?P<ident>[A-Za-z_][\w]*(?:\+[0-9]+)?) |
    (?P<string>"[^"]*"|'[^']*')
    """,
    re.VERBOSE,
)


@dataclass(frozen=True)
class Token:
    kind: str
    text: str


def tokenize(source: str) -> list[Token]:
    out: list[Token] = []
    pos = 0
    while pos < len(source):
        m = TOKEN_RE.match(source, pos)
        if not m:
            raise SyntaxError(f"tdb: unexpected character at offset {pos}: {source[pos]!r}")
        if m.group(0).strip() == "":
            pos = m.end()
            continue
        kind = m.lastgroup
        text = m.group(0)
        out.append(Token(kind=kind or "?", text=text))
        pos = m.end()
    return out


# ---------------------------------------------------------------------------
# AST
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PredicateNode:
    name: str
    kwargs: tuple[tuple[str, str], ...]

    def canonical(self) -> str:
        args = ", ".join(f"{k}={v}" for k, v in self.kwargs)
        return f"{self.name}({args})"


@dataclass(frozen=True)
class NotNode:
    child: "Node"

    def canonical(self) -> str:
        return f"not {self.child.canonical()}"


@dataclass(frozen=True)
class AndNode:
    children: tuple["Node", ...]

    def canonical(self) -> str:
        return " and ".join(c.canonical() for c in self.children)


@dataclass(frozen=True)
class OrNode:
    children: tuple["Node", ...]

    def canonical(self) -> str:
        return " or ".join(c.canonical() for c in self.children)


Node = "PredicateNode | NotNode | AndNode | OrNode"


class _Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, kind: str) -> Token:
        tok = self.peek()
        if tok is None or tok.kind != kind:
            raise SyntaxError(f"tdb: expected {kind}, got {tok and tok.kind} ({tok and tok.text})")
        return self.advance()

    def parse_query(self) -> Node:
        node = self.parse_or()
        if self.peek() is not None:
            tok = self.peek()
            raise SyntaxError(f"tdb: trailing tokens at end of query: {tok.text!r}")
        return node

    def parse_or(self) -> Node:
        first = self.parse_and()
        children = [first]
        while self.peek() and self.peek().kind == "kw_or":
            self.advance()
            children.append(self.parse_and())
        if len(children) == 1:
            return children[0]
        return OrNode(children=tuple(children))

    def parse_and(self) -> Node:
        first = self.parse_not()
        children = [first]
        while self.peek() and self.peek().kind == "kw_and":
            self.advance()
            children.append(self.parse_not())
        if len(children) == 1:
            return children[0]
        return AndNode(children=tuple(children))

    def parse_not(self) -> Node:
        if self.peek() and self.peek().kind == "kw_not":
            self.advance()
            return NotNode(child=self.parse_not())
        if self.peek() and self.peek().kind == "lparen":
            self.advance()
            node = self.parse_or()
            self.expect("rparen")
            return node
        return self.parse_predicate()

    def parse_predicate(self) -> PredicateNode:
        name = self.expect("ident")
        if name.text not in PREDICATES:
            raise SyntaxError(
                f"tdb: unknown predicate {name.text!r}; supported in this slice: "
                f"{sorted(PREDICATES)}"
            )
        self.expect("lparen")
        kwargs: list[tuple[str, str]] = []
        while self.peek() and self.peek().kind != "rparen":
            key = self.expect("ident").text
            self.expect("eq")
            value_tok = self.advance()
            kwargs.append((key, value_tok.text))
            if self.peek() and self.peek().kind == "comma":
                self.advance()
        self.expect("rparen")
        return PredicateNode(name=name.text, kwargs=tuple(kwargs))


def parse(source: str) -> Node:
    return _Parser(tokenize(source)).parse_query()


PREDICATES = frozenset({"writes", "reads", "executes"})


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def _normalize_address_arg(value: str) -> tuple[int | None, int | None]:
    """Return (bank, address) or (None, None) on parse failure."""

    raw = value.strip()
    if raw.startswith("$"):
        raw = raw[1:]
    if ":" in raw:
        bank_text, addr_text = raw.split(":", 1)
        try:
            return int(bank_text, 16), int(addr_text, 16)
        except ValueError:
            return None, None
    if raw.isdigit():
        return None, int(raw)
    try:
        return None, int(raw, 16)
    except ValueError:
        return None, None


def _event_iter(reports: Iterable[dict[str, Any]]) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    """Yield (frame, effect) pairs from each loaded effect-trace report."""

    for report in reports:
        data = report.get("data") if isinstance(report, dict) else None
        if not isinstance(data, dict):
            continue
        if data.get("kind") != "unified_debugger_effect_trace":
            continue
        for event in data.get("events") or ():
            if not isinstance(event, dict):
                continue
            effects = event.get("effects") or ()
            if not effects:
                yield event, {}
                continue
            for effect in effects:
                if isinstance(effect, dict):
                    yield event, effect


def _match_predicate(pred: PredicateNode, frame: dict[str, Any], effect: dict[str, Any]) -> tuple[bool, str, str]:
    """Return (matches, proof_status_override_or_empty, downgrade_reason)."""

    name = pred.name
    kwargs = dict(pred.kwargs)
    if name == "writes":
        if effect.get("access") != "write":
            return False, "", ""
        return _match_address_effect(kwargs, effect)
    if name == "reads":
        if "reg" in kwargs:
            wanted_reg = kwargs["reg"].upper()
            value_source = str(effect.get("value_source") or "").upper()
            if value_source and value_source == wanted_reg:
                return True, "", ""
            return False, "", ""
        if effect.get("access") != "read":
            return False, "", ""
        return _match_address_effect(kwargs, effect)
    if name == "executes":
        return _match_executes(kwargs, frame)
    raise SyntaxError(f"tdb: unknown predicate {name!r}")


def _match_address_effect(kwargs: dict[str, str], effect: dict[str, Any]) -> tuple[bool, str, str]:
    if "addr" not in kwargs:
        return False, "", ""
    requested_bank, requested_address = _normalize_address_arg(kwargs["addr"])
    if requested_address is None:
        return False, "", ""
    eff_addr = effect.get("address_hex") or ""
    try:
        eff_address_int = int(eff_addr, 16) if eff_addr else None
    except ValueError:
        eff_address_int = None
    if eff_address_int != requested_address:
        return False, "", ""
    explicit_bank = kwargs.get("bank")
    if explicit_bank is not None:
        try:
            explicit_bank_int = int(explicit_bank, 0)
        except ValueError:
            explicit_bank_int = None
        if explicit_bank_int is not None:
            requested_bank = explicit_bank_int
    if requested_bank is not None:
        eff_bank = effect.get("bank")
        if eff_bank is None:
            # Bank requested but event has no observed bank — match but downgrade.
            return True, "planned_only", "bank_unverified"
        if int(eff_bank) != int(requested_bank):
            return False, "", ""
    return True, "", ""


def _match_executes(kwargs: dict[str, str], frame: dict[str, Any]) -> tuple[bool, str, str]:
    pc_target = kwargs.get("pc")
    if pc_target is None:
        return False, "", ""
    pc_target = pc_target.strip()
    frame_pc = str(frame.get("pc_bank_address") or "").strip()
    frame_label = str(frame.get("pc_label") or "").strip()
    if pc_target.startswith("$"):
        pc_target = pc_target[1:]
    # Bank-aware "01:5A00" form.
    if ":" in pc_target:
        return (frame_pc.lower() == pc_target.lower(), "", "")
    # Hex-only "5A00" matches the address portion of pc_bank_address.
    try:
        int(pc_target, 16)
        if ":" in frame_pc:
            return (frame_pc.split(":", 1)[1].lower() == pc_target.lower(), "", "")
        return (frame_pc.lower() == pc_target.lower(), "", "")
    except ValueError:
        pass
    # Otherwise treat as a symbol prefix.
    return (bool(frame_label) and frame_label.startswith(pc_target), "", "")


def _evaluate(node: Node, frame: dict[str, Any], effect: dict[str, Any]) -> tuple[bool, str, str]:
    if isinstance(node, PredicateNode):
        return _match_predicate(node, frame, effect)
    if isinstance(node, NotNode):
        matched, _, _ = _evaluate(node.child, frame, effect)
        return (not matched, "", "")
    if isinstance(node, AndNode):
        proof = ""
        reason = ""
        for child in node.children:
            matched, p, r = _evaluate(child, frame, effect)
            if not matched:
                return False, "", ""
            if p and not proof:
                proof = p
                reason = r
        return True, proof, reason
    if isinstance(node, OrNode):
        for child in node.children:
            matched, p, r = _evaluate(child, frame, effect)
            if matched:
                return True, p, r
        return False, "", ""
    raise SyntaxError(f"tdb: unrecognized AST node: {type(node).__name__}")


def _materialize_match(
    node: Node,
    frame: dict[str, Any],
    effect: dict[str, Any],
    *,
    proof_override: str,
    downgrade_reason: str,
) -> dict[str, Any]:
    seq_raw = frame.get("seq")
    try:
        seq = int(seq_raw)
    except (TypeError, ValueError):
        seq = -1
    base_proof = str(effect.get("proof_status") or frame.get("proof_status") or "")
    proof_status = proof_override or base_proof
    match = {
        "kind": "tdb_match",
        "predicate": node.canonical(),
        "seq": seq,
        "pc_bank_address": str(frame.get("pc_bank_address") or ""),
        "pc_label": str(frame.get("pc_label") or ""),
        "address_key": str(effect.get("address_key") or ""),
        "address_hex": str(effect.get("address_hex") or ""),
        "bank": effect.get("bank"),
        "value_hex": str(effect.get("value_hex") or ""),
        "value_source": str(effect.get("value_source") or ""),
        "proof_status": proof_status,
        "evidence_atom_source": "effect" if effect else "frame",
    }
    if downgrade_reason:
        match["proof_downgrade_reason"] = downgrade_reason
    return match


@dataclass(frozen=True)
class TdbReport:
    valid: bool
    query: str
    canonical: str
    matches: tuple[dict[str, Any], ...] = ()
    errors: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "unified_debugger_tdb_report",
            "valid": self.valid,
            "query": self.query,
            "canonical": self.canonical,
            "match_count": len(self.matches),
            "matches": list(self.matches),
            "errors": list(self.errors),
        }


def run_tdb(
    *,
    query: str,
    reports: tuple[str, ...] = (),
    root: Path = ROOT,
) -> dict[str, Any]:
    try:
        node = parse(query)
    except SyntaxError as exc:
        return TdbReport(valid=False, query=query, canonical="", errors=(str(exc),)).as_dict()
    if not reports:
        return TdbReport(
            valid=False,
            query=query,
            canonical=node.canonical(),
            errors=("at least one --report (effect trace JSON) is required",),
        ).as_dict()
    loaded_reports, load_errors = load_reports(reports=reports, root=root)
    if load_errors:
        return TdbReport(
            valid=False,
            query=query,
            canonical=node.canonical(),
            errors=tuple(str(e) for e in load_errors),
        ).as_dict()
    matches: list[dict[str, Any]] = []
    for frame, effect in _event_iter(loaded_reports):
        matched, proof_override, downgrade_reason = _evaluate(node, frame, effect)
        if matched:
            matches.append(
                _materialize_match(
                    node,
                    frame,
                    effect,
                    proof_override=proof_override,
                    downgrade_reason=downgrade_reason,
                )
            )
    return TdbReport(
        valid=True,
        query=query,
        canonical=node.canonical(),
        matches=tuple(matches),
    ).as_dict()


def _format_text(report: dict[str, Any]) -> str:
    lines: list[str] = ["unified debugger tdb"]
    lines.append(f"  query: {report.get('query', '')!r}")
    lines.append(f"  canonical: {report.get('canonical', '')}")
    if not report.get("valid"):
        for err in report.get("errors", []):
            lines.append(f"  error: {err}")
        return "\n".join(lines)
    matches = report.get("matches") or []
    lines.append(f"  matches: {len(matches)}")
    for match in matches:
        lines.append(
            f"    seq={match.get('seq')} pc={match.get('pc_bank_address') or '?'} "
            f"label={match.get('pc_label') or '-'} "
            f"addr={match.get('address_key') or match.get('address_hex') or '-'} "
            f"value={match.get('value_hex') or '-'} "
            f"proof={match.get('proof_status') or '?'}"
        )
        if match.get("proof_downgrade_reason"):
            lines.append(f"      downgrade: {match['proof_downgrade_reason']}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger.tdb",
        description="Trace query language (P3). Run a predicate query against effect-trace reports.",
    )
    parser.add_argument("query", help="The query expression, e.g. 'writes(addr=$D141)'.")
    parser.add_argument(
        "--report",
        action="append",
        default=[],
        help="Effect-trace report JSON file. Repeatable.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args(argv)

    report = run_tdb(query=args.query, reports=tuple(args.report))
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(_format_text(report))
    return 0 if report.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
