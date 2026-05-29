from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .catalog import ROOT
from .clobber_graph import CallEdge, FunctionBlock, StaticCallGraph, build_static_call_graph


REGISTERS_8: frozenset[str] = frozenset({"a", "b", "c", "d", "e", "h", "l"})
REGISTER_PAIRS: frozenset[str] = frozenset({"af", "bc", "de", "hl", "sp"})
FLAGS: frozenset[str] = frozenset({"z", "n", "h", "c_flag"})


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

_FLAG_CLOBBERING_MNEMONICS: frozenset[str] = frozenset({
    "add", "adc", "sub", "sbc", "and", "or", "xor", "cp", "inc", "dec",
    "rlca", "rrca", "rla", "rra", "rlc", "rrc", "rl", "rr", "sla", "sra", "srl", "swap",
    "bit", "daa", "scf", "ccf",
})

_DEST_FIRST_MNEMONICS: frozenset[str] = frozenset({
    "ld", "ldh", "ldi", "ldd", "add", "adc", "sub", "sbc", "and", "or", "xor",
    "inc", "dec", "rlc", "rrc", "rl", "rr", "sla", "sra", "srl", "swap",
    "res", "set",
})


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


@dataclass(frozen=True)
class ClobberChainReport:
    function: str
    direct_clobbers: frozenset[str]
    transitive_clobbers: frozenset[str]
    call_targets: tuple[str, ...]
    farcall_targets: tuple[str, ...]
    farcall_abi_clobbers: tuple[dict[str, Any], ...]
    clobber_chains: dict[str, tuple[tuple[str, ...], ...]]
    unknown_mnemonics: tuple[str, ...]
    indirect_call_warnings: tuple[str, ...]
    query_register: str | None = None
    query_clobbered: bool | None = None
    query_register_tokens: tuple[str, ...] = ()


@dataclass(frozen=True)
class _AnalysisResult:
    direct_clobbers: frozenset[str]
    transitive_clobbers: frozenset[str]
    call_targets: tuple[str, ...]
    farcall_targets: tuple[str, ...]
    farcall_abi_clobbers: tuple[dict[str, Any], ...]
    clobber_chains: dict[str, tuple[tuple[str, ...], ...]]
    unknown_mnemonics: tuple[str, ...]
    indirect_call_warnings: tuple[str, ...]


@dataclass(frozen=True)
class _DirectScan:
    clobbers: frozenset[str]
    unknown_mnemonics: tuple[str, ...]
    protected_at_line: dict[tuple[str, int], frozenset[str]]


def build_clobber_chain_report(
    *,
    function: str,
    register: str | None = None,
    root: Path = ROOT,
    source_files: Iterable[str | Path] | None = None,
    max_depth: int = 8,
) -> dict[str, Any]:
    graph = build_static_call_graph(root=root, source_files=source_files)
    label = function.strip()
    if label not in graph.blocks:
        return {
            "schema_version": 1,
            "kind": "unified_debugger_clobber_chain",
            "valid": False,
            "function": label,
            "errors": [f"function label {label!r} was not found"],
        }
    analysis = _analyze_function(
        graph,
        label,
        chain=(label,),
        active=frozenset(),
        max_depth=max_depth,
    )
    query_register = register.strip().lower() if register else None
    query_tokens = _register_tokens(query_register) if query_register else frozenset()
    report = ClobberChainReport(
        function=label,
        direct_clobbers=analysis.direct_clobbers,
        transitive_clobbers=analysis.transitive_clobbers,
        call_targets=analysis.call_targets,
        farcall_targets=analysis.farcall_targets,
        farcall_abi_clobbers=analysis.farcall_abi_clobbers,
        clobber_chains=analysis.clobber_chains,
        unknown_mnemonics=analysis.unknown_mnemonics,
        indirect_call_warnings=analysis.indirect_call_warnings,
        query_register=query_register,
        query_clobbered=bool(query_tokens & analysis.transitive_clobbers) if query_register else None,
        query_register_tokens=tuple(sorted(query_tokens)),
    )
    return report_to_dict(report)


def _analyze_function(
    graph: StaticCallGraph,
    function: str,
    *,
    chain: tuple[str, ...],
    active: frozenset[str],
    max_depth: int,
) -> _AnalysisResult:
    body_blocks = _body_blocks(graph, function)
    scan = _scan_direct_clobbers(body_blocks)
    direct_clobbers = scan.clobbers
    unknown = list(scan.unknown_mnemonics)
    transitive_clobbers = set(direct_clobbers)
    call_targets: list[str] = []
    farcall_targets: list[str] = []
    farcall_abi_clobbers: list[dict[str, Any]] = []
    warnings: list[str] = []
    chains: dict[str, set[tuple[str, ...]]] = {
        register: {chain} for register in direct_clobbers
    }

    if function in active:
        return _analysis_result(
            direct_clobbers=direct_clobbers,
            transitive_clobbers=transitive_clobbers,
            call_targets=call_targets,
            farcall_targets=farcall_targets,
            farcall_abi_clobbers=farcall_abi_clobbers,
            clobber_chains=chains,
            unknown_mnemonics=unknown,
            indirect_call_warnings=[f"recursive call cycle reached at {' -> '.join(chain)}"],
        )
    if len(chain) > max_depth:
        return _analysis_result(
            direct_clobbers=direct_clobbers,
            transitive_clobbers=transitive_clobbers,
            call_targets=call_targets,
            farcall_targets=farcall_targets,
            farcall_abi_clobbers=farcall_abi_clobbers,
            clobber_chains=chains,
            unknown_mnemonics=unknown,
            indirect_call_warnings=[f"max depth {max_depth} reached at {' -> '.join(chain)}"],
        )

    for edge in _body_edges(graph, function):
        protected = scan.protected_at_line.get((edge.source_file, edge.line_number), frozenset())
        abi_clobbers = _expand_registers(edge.abi_clobbers) - protected
        if abi_clobbers:
            transitive_clobbers.update(abi_clobbers)
            for register in abi_clobbers:
                chains.setdefault(register, set()).add(chain)
            if edge.call_type == "farcall":
                farcall_abi_clobbers.append(
                    {
                        "caller": edge.caller,
                        "callee": edge.callee,
                        "source_file": edge.source_file,
                        "line_number": edge.line_number,
                        "instruction": edge.instruction,
                        "clobbers": sorted(abi_clobbers),
                        "notes": list(edge.notes),
                    }
                )
        if edge.is_unresolved:
            warnings.append(_format_unresolved_edge(edge))
            continue
        assert edge.callee is not None
        call_targets.append(edge.callee)
        if edge.call_type == "farcall":
            farcall_targets.append(edge.callee)
        if edge.callee not in graph.blocks:
            warnings.append(
                f"{edge.source_file}:{edge.line_number}: target {edge.callee} not found for {edge.instruction}"
            )
            continue
        child = _analyze_function(
            graph,
            edge.callee,
            chain=(*chain, edge.callee),
            active=active | {function},
            max_depth=max_depth,
        )
        child_clobbers = child.transitive_clobbers - protected
        transitive_clobbers.update(child_clobbers)
        unknown.extend(child.unknown_mnemonics)
        warnings.extend(child.indirect_call_warnings)
        farcall_targets.extend(child.farcall_targets)
        farcall_abi_clobbers.extend(child.farcall_abi_clobbers)
        for register, child_chains in child.clobber_chains.items():
            if register in protected:
                continue
            chains.setdefault(register, set()).update(child_chains)

    return _analysis_result(
        direct_clobbers=direct_clobbers,
        transitive_clobbers=transitive_clobbers,
        call_targets=call_targets,
        farcall_targets=farcall_targets,
        farcall_abi_clobbers=farcall_abi_clobbers,
        clobber_chains=chains,
        unknown_mnemonics=unknown,
        indirect_call_warnings=warnings,
    )


def _analysis_result(
    *,
    direct_clobbers: Iterable[str],
    transitive_clobbers: Iterable[str],
    call_targets: Iterable[str],
    farcall_targets: Iterable[str],
    farcall_abi_clobbers: Iterable[dict[str, Any]],
    clobber_chains: dict[str, set[tuple[str, ...]]],
    unknown_mnemonics: Iterable[str],
    indirect_call_warnings: Iterable[str],
) -> _AnalysisResult:
    return _AnalysisResult(
        direct_clobbers=frozenset(direct_clobbers),
        transitive_clobbers=frozenset(transitive_clobbers),
        call_targets=tuple(_unique(call_targets)),
        farcall_targets=tuple(_unique(farcall_targets)),
        farcall_abi_clobbers=tuple(farcall_abi_clobbers),
        clobber_chains={
            register: tuple(sorted(paths))
            for register, paths in sorted(clobber_chains.items())
        },
        unknown_mnemonics=tuple(_unique(unknown_mnemonics)),
        indirect_call_warnings=tuple(_unique(indirect_call_warnings)),
    )


def _body_blocks(graph: StaticCallGraph, function: str) -> tuple[FunctionBlock, ...]:
    block = graph.blocks[function]
    if block.parent_label == function:
        owner_by_label = _local_subroutine_owners(graph, parent=function)
        return tuple(
            candidate
            for candidate in _ordered_parent_blocks(graph, function)
            if owner_by_label.get(candidate.label) is None
        )
    owner_by_label = _local_subroutine_owners(graph, parent=block.parent_label)
    return tuple(
        candidate
        for candidate in _ordered_parent_blocks(graph, block.parent_label)
        if owner_by_label.get(candidate.label) == function
    )


def _body_edges(graph: StaticCallGraph, function: str) -> tuple[CallEdge, ...]:
    labels = {block.label for block in _body_blocks(graph, function)}
    return tuple(edge for edge in graph.edges if edge.caller in labels)


def _ordered_parent_blocks(graph: StaticCallGraph, parent: str) -> tuple[FunctionBlock, ...]:
    return tuple(
        sorted(
            (
                block
                for block in graph.blocks.values()
                if block.label == parent or block.parent_label == parent
            ),
            key=lambda block: (block.source_file, block.line_start),
        )
    )


def _local_subroutine_owners(graph: StaticCallGraph, *, parent: str) -> dict[str, str | None]:
    local_call_entries = {
        edge.callee
        for edge in graph.edges
        if edge.call_type == "call"
        and edge.callee in graph.blocks
        and graph.blocks[edge.callee].parent_label == parent
        and graph.blocks[edge.callee].label != parent
    }
    owner_by_label: dict[str, str | None] = {}
    current_owner: str | None = None
    for block in _ordered_parent_blocks(graph, parent):
        if block.label == parent:
            current_owner = None
        elif block.label in local_call_entries:
            current_owner = block.label
        owner_by_label[block.label] = current_owner
    return owner_by_label


def _scan_direct_clobbers(blocks: Iterable[FunctionBlock]) -> _DirectScan:
    clobbers: set[str] = set()
    unknown: list[str] = []
    protected_counts: dict[str, int] = {}
    protected_at_line: dict[tuple[str, int], frozenset[str]] = {}
    lines = sorted(
        (line for block in blocks for line in block.lines),
        key=lambda line: (line.source_file, line.line_number),
    )
    for line in lines:
        current_protected = frozenset(
            register for register, count in protected_counts.items() if count > 0
        )
        protected_at_line[(line.source_file, line.line_number)] = current_protected
        parsed = parse_instruction_line(line.code)
        if parsed is None:
            continue
        mnemonic, operands = parsed
        if mnemonic == "push" and operands:
            for register in _expand_registers((operands[0],)):
                protected_counts[register] = protected_counts.get(register, 0) + 1
            continue
        if mnemonic == "pop" and operands:
            for register in _expand_registers((operands[0],)):
                protected_counts[register] = max(0, protected_counts.get(register, 0) - 1)
            continue
        inferred = clobbers_for_instruction(mnemonic, operands)
        for item in inferred:
            if item.startswith("__unknown__:"):
                unknown.append(f"{line.source_file}:{line.line_number}: {item.removeprefix('__unknown__:')}")
            elif item.startswith("__needs_transitive"):
                continue
            else:
                clobbers.update(_expand_registers((item,)) - current_protected)
    return _DirectScan(
        clobbers=frozenset(clobbers),
        unknown_mnemonics=tuple(_unique(unknown)),
        protected_at_line=protected_at_line,
    )


def _expand_registers(registers: Iterable[str]) -> frozenset[str]:
    out: set[str] = set()
    for register in registers:
        token = register.lower()
        if token == "f":
            out.add("flags")
        elif token in REGISTER_PAIRS:
            out.update(pair_to_halves(token))
        elif token == "hl":
            out.update({"h", "l"})
        else:
            out.add(token)
    return frozenset(out)


def _register_tokens(register: str | None) -> frozenset[str]:
    if not register:
        return frozenset()
    token = register.lower()
    if token in REGISTERS_8 or token in {"sp", "flags"}:
        return frozenset({token})
    if token == "f":
        return frozenset({"flags"})
    if token in REGISTER_PAIRS:
        return pair_to_halves(token)
    return frozenset({token})


def _format_unresolved_edge(edge: CallEdge) -> str:
    note = f" ({'; '.join(edge.notes)})" if edge.notes else ""
    return f"{edge.source_file}:{edge.line_number}: {edge.instruction}{note}"


def _unique(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def report_to_dict(report: ClobberChainReport) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema_version": 1,
        "kind": "unified_debugger_clobber_chain",
        "valid": True,
        "function": report.function,
        "direct_clobbers": sorted(report.direct_clobbers),
        "transitive_clobbers": sorted(report.transitive_clobbers),
        "call_targets": list(report.call_targets),
        "farcall_targets": list(report.farcall_targets),
        "farcall_abi_clobbers": list(report.farcall_abi_clobbers),
        "clobber_chains": {
            register: [list(chain) for chain in chains]
            for register, chains in report.clobber_chains.items()
        },
        "unknown_mnemonics": list(report.unknown_mnemonics),
        "indirect_call_warnings": list(report.indirect_call_warnings),
    }
    if report.query_register:
        out["query_register"] = report.query_register
        out["query_register_tokens"] = list(report.query_register_tokens)
        out["query_clobbered"] = report.query_clobbered
        out["query_clobber_chains"] = {
            register: [list(chain) for chain in report.clobber_chains.get(register, ())]
            for register in report.query_register_tokens
        }
    return out


def format_text(report: dict[str, Any]) -> str:
    if not report.get("valid"):
        errors = report.get("errors") or ["unknown error"]
        return "Clobber chain report: INVALID\n" + "\n".join(f"  {line}" for line in errors)
    lines: list[str] = []
    function = report["function"]
    lines.append("Unified Pokemon Gold romhack debugger clobber chain")
    lines.append(f"function={function}")
    lines.append("")
    direct = ", ".join(report["direct_clobbers"]) or "(none)"
    lines.append(f"direct clobbers (in this function's body): {direct}")
    transitive = ", ".join(report["transitive_clobbers"]) or "(none)"
    lines.append(f"transitive clobbers (including via call targets): {transitive}")
    if report.get("query_register"):
        verdict = "yes" if report.get("query_clobbered") else "no"
        tokens = ", ".join(report.get("query_register_tokens") or [])
        lines.append(f"query register {report['query_register']} ({tokens}): clobbered={verdict}")
    targets = report.get("call_targets") or []
    if targets:
        lines.append("")
        lines.append(f"call targets ({len(targets)}):")
        for target in targets:
            lines.append(f"  {target}")
    farcall_targets = report.get("farcall_targets") or []
    if farcall_targets:
        lines.append("")
        lines.append(f"farcall targets ({len(farcall_targets)}):")
        lines.append("  (note: farcall ABI also clobbers a=target's exit c, hl pre-target)")
        for target in farcall_targets:
            lines.append(f"  {target}")
    chains = report.get("clobber_chains") or {}
    if chains:
        lines.append("")
        lines.append("clobber proof chains:")
        for register in sorted(chains):
            shown = chains[register][:3]
            rendered = "; ".join(" -> ".join(chain) for chain in shown)
            suffix = "" if len(chains[register]) <= 3 else f" (+{len(chains[register]) - 3} more)"
            lines.append(f"  {register}: {rendered}{suffix}")
    warnings = report.get("indirect_call_warnings") or []
    if warnings:
        lines.append("")
        lines.append("analysis warnings (indirect or depth-limited):")
        for warning in warnings:
            lines.append(f"  {warning}")
    unknown = report.get("unknown_mnemonics") or []
    if unknown:
        lines.append("")
        lines.append("unanalyzed mnemonics (likely local macros):")
        for token in unknown:
            lines.append(f"  {token}")
    return "\n".join(lines)
