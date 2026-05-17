from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .catalog import ROOT, triage_request
from .ingest import sha256_file
from .provenance import (
    LABEL_DEF_RE,
    collect_source_paths,
    display_path,
    parse_symbol_table,
    resolve_path,
)


TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_.$])([A-Za-z_.$][A-Za-z0-9_.$]*)(?![A-Za-z0-9_.$])")
BARE_LABEL_RE = re.compile(r"^(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*)\s*$")
CALL_OPS = {"call", "farcall", "callfar", "predef", "rst"}
JUMP_OPS = {"jp", "jr", "farjp"}
DATA_OPS = {"db", "dw", "dl", "dba", "dab", "ds"}
LINE_OPS = CALL_OPS | JUMP_OPS | DATA_OPS | {
    "adc",
    "add",
    "and",
    "bit",
    "ccf",
    "cp",
    "cpl",
    "daa",
    "dec",
    "di",
    "ei",
    "halt",
    "inc",
    "ld",
    "ldh",
    "nop",
    "or",
    "pop",
    "push",
    "res",
    "ret",
    "reti",
    "rl",
    "rla",
    "rlc",
    "rlca",
    "rr",
    "rra",
    "rrc",
    "rrca",
    "sbc",
    "scf",
    "set",
    "sla",
    "sra",
    "srl",
    "stop",
    "sub",
    "swap",
    "xor",
}
IGNORED_TOKENS = {
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "h",
    "l",
    "af",
    "bc",
    "de",
    "hl",
    "sp",
    "pc",
    "nc",
    "nz",
    "z",
    "BANK",
    "BANKOF",
    "HIGH",
    "LOW",
    "SIZEOF",
    "STARTOF",
    "DEF",
    "EQU",
    "MACRO",
    "ENDM",
    "SECTION",
    "ENDC",
    "ELSE",
    "IF",
    "IFDEF",
    "IFNDEF",
    "INCLUDE",
    "INCBIN",
    "REPT",
    "ENDR",
}


def build_slice_report(
    *,
    symbols_path: str = "pokegold.sym",
    symbols: tuple[str, ...] = (),
    source_files: tuple[str, ...] = (),
    max_depth: int = 2,
    max_edges: int = 80,
    root: Path = ROOT,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    sym_path = resolve_path(symbols_path, root=root)
    symbol_table: dict[str, dict[str, Any]] = {}
    if sym_path.exists():
        symbol_table = parse_symbol_table(sym_path)
    else:
        errors.append(f"missing symbol file: {symbols_path}")

    source_paths = [
        path
        for path in collect_source_paths(root=root, include_docs=False, explicit_paths=source_files)
        if path.suffix.lower() == ".asm"
    ]
    graph = build_assembly_graph(
        source_paths=source_paths,
        symbol_table=symbol_table,
        root=root,
    )
    max_depth = max(1, max_depth)
    max_edges = max(1, max_edges)

    targets = [
        describe_target(
            symbol,
            graph=graph,
            symbol_table=symbol_table,
            max_depth=max_depth,
            max_edges=max_edges,
            root=root,
        )
        for symbol in symbols
    ]
    source_reports = [
        describe_source_slice(
            source_file,
            graph=graph,
            root=root,
            max_edges=max_edges,
        )
        for source_file in source_files
    ]
    warnings.extend(
        warning
        for target in targets
        for warning in target.get("warnings", [])
    )
    errors.extend(
        error
        for source in source_reports
        for error in source.get("errors", [])
    )

    return {
        "schema_version": 1,
        "kind": "unified_debugger_causal_slice",
        "root": str(root),
        "symbols_path": display_path(sym_path, root=root),
        "symbols_sha256": sha256_file(sym_path) if sym_path.exists() else "",
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "max_depth": max_depth,
        "max_edges": max_edges,
        "graph": {
            "node_count": len(graph["nodes"]),
            "edge_count": len(graph["edges"]),
            "source_file_count": len(source_paths),
        },
        "targets": targets,
        "source_files": source_reports,
        "known_limits": [
            "This is a static RGBDS source slice, not a runtime SM83 dataflow trace.",
            "Edges show plausible code/data/state contributors; prove runtime causality with watch, replay, trace, taint, or subsystem materialization.",
        ],
    }


def build_assembly_graph(
    *,
    source_paths: list[Path],
    symbol_table: dict[str, dict[str, Any]],
    root: Path,
) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    lines_by_node: dict[str, list[dict[str, Any]]] = {}
    local_parents: dict[str, str] = {}
    labels_by_file: dict[str, list[str]] = {}

    for path in source_paths:
        parse_labels(
            path=path,
            nodes=nodes,
            lines_by_node=lines_by_node,
            local_parents=local_parents,
            labels_by_file=labels_by_file,
            root=root,
            symbol_table=symbol_table,
        )

    known_labels = set(nodes) | set(symbol_table)
    edges: list[dict[str, Any]] = []
    edge_keys: set[tuple[str, str, int, str]] = set()
    for label, lines in lines_by_node.items():
        parent = local_parents.get(label, label)
        for line in lines:
            code = strip_comment(line["text"])
            for token in TOKEN_RE.findall(code):
                target = resolve_reference(token, current_global=parent, known_labels=known_labels)
                if not target or target == label or token in IGNORED_TOKENS:
                    continue
                edge = describe_edge(
                    source=label,
                    target=target,
                    line=line,
                    code=code,
                )
                key = (edge["source"], edge["target"], edge["line"], edge["access"])
                if key in edge_keys:
                    continue
                edge_keys.add(key)
                edges.append(edge)

    incoming: dict[str, list[dict[str, Any]]] = {}
    outgoing: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        incoming.setdefault(edge["target"], []).append(edge)
        outgoing.setdefault(edge["source"], []).append(edge)

    for edge_list in incoming.values():
        edge_list.sort(key=edge_sort_key)
    for edge_list in outgoing.values():
        edge_list.sort(key=edge_sort_key)

    return {
        "nodes": nodes,
        "edges": edges,
        "incoming": incoming,
        "outgoing": outgoing,
        "labels_by_file": labels_by_file,
    }


def parse_labels(
    *,
    path: Path,
    nodes: dict[str, dict[str, Any]],
    lines_by_node: dict[str, list[dict[str, Any]]],
    local_parents: dict[str, str],
    labels_by_file: dict[str, list[str]],
    root: Path,
    symbol_table: dict[str, dict[str, Any]],
) -> None:
    display = display_path(path, root=root)
    current_label = ""
    current_global = ""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return

    for line_no, text in enumerate(lines, 1):
        raw_label = match_label_definition(text)
        if raw_label:
            label = canonical_label(raw_label, current_global=current_global)
            if not raw_label.startswith("."):
                current_global = raw_label
            current_label = label
            if label not in nodes:
                address = symbol_table.get(label)
                nodes[label] = {
                    "label": label,
                    "path": display,
                    "line": line_no,
                    "scope": "local" if raw_label.startswith(".") else "global",
                    "parent": current_global if raw_label.startswith(".") else "",
                    "address": address,
                }
                labels_by_file.setdefault(display, []).append(label)
            if raw_label.startswith("."):
                local_parents[label] = current_global
            else:
                local_parents[label] = label

        if not current_label:
            continue
        lines_by_node.setdefault(current_label, []).append(
            {
                "path": display,
                "line": line_no,
                "text": text.strip()[:220],
            }
        )


def describe_target(
    symbol: str,
    *,
    graph: dict[str, Any],
    symbol_table: dict[str, dict[str, Any]],
    max_depth: int,
    max_edges: int,
    root: Path,
) -> dict[str, Any]:
    target = resolve_query(symbol, graph=graph, symbol_table=symbol_table)
    warnings = []
    if target is None:
        warnings.append(f"symbol not present in static slice graph: {symbol}")
        return {
            "query": symbol,
            "found": False,
            "address": symbol_table.get(symbol),
            "definition": None,
            "incoming": [],
            "outgoing": [],
            "impact_files": [],
            "triage_match_ids": [],
            "suggested_commands": [],
            "warnings": warnings,
        }

    incoming = walk_edges(
        target,
        adjacency=graph["incoming"],
        direction="incoming",
        max_depth=max_depth,
        max_edges=max_edges,
    )
    outgoing = walk_edges(
        target,
        adjacency=graph["outgoing"],
        direction="outgoing",
        max_depth=max_depth,
        max_edges=max_edges,
    )
    node = graph["nodes"].get(target, {})
    impact_files = sorted(
        {
            item["path"]
            for item in [*incoming, *outgoing]
            if item.get("path")
        }
        | ({node["path"]} if node.get("path") else set())
    )
    triage = triage_request(changed_files=tuple(impact_files), root=root) if impact_files else None
    return {
        "query": symbol,
        "resolved": target,
        "found": True,
        "address": symbol_table.get(target) or symbol_table.get(symbol),
        "definition": node,
        "incoming": incoming,
        "outgoing": outgoing,
        "impact_files": impact_files,
        "triage_match_ids": [
            match["id"] for match in triage["matches"]
        ] if triage else [],
        "suggested_commands": triage["commands"] if triage else [],
        "warnings": warnings,
    }


def describe_source_slice(
    source_file: str,
    *,
    graph: dict[str, Any],
    root: Path,
    max_edges: int,
) -> dict[str, Any]:
    path = resolve_path(source_file, root=root)
    display = display_path(path, root=root)
    report: dict[str, Any] = {
        "path": display,
        "input_path": source_file,
        "exists": path.exists(),
        "labels": [],
        "incoming": [],
        "outgoing": [],
        "triage_match_ids": [],
        "suggested_commands": [],
        "errors": [],
    }
    if not path.exists():
        report["errors"].append(f"source path does not exist: {source_file}")
        return report
    labels = graph["labels_by_file"].get(display, [])
    incoming = []
    outgoing = []
    for label in labels:
        incoming.extend(graph["incoming"].get(label, []))
        outgoing.extend(graph["outgoing"].get(label, []))
    triage = triage_request(changed_files=(display,), root=root)
    report.update(
        {
            "labels": [graph["nodes"][label] for label in labels[:80]],
            "label_count": len(labels),
            "incoming": sorted(incoming, key=edge_sort_key)[:max_edges],
            "outgoing": sorted(outgoing, key=edge_sort_key)[:max_edges],
            "triage_match_ids": [match["id"] for match in triage["matches"]],
            "suggested_commands": triage["commands"],
        }
    )
    return report


def walk_edges(
    start: str,
    *,
    adjacency: dict[str, list[dict[str, Any]]],
    direction: str,
    max_depth: int,
    max_edges: int,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    queue: list[tuple[str, int]] = [(start, 1)]
    seen_nodes = {start}
    seen_edges: set[tuple[str, str, int, str]] = set()
    while queue and len(out) < max_edges:
        node, depth = queue.pop(0)
        if depth > max_depth:
            continue
        for edge in adjacency.get(node, []):
            key = (edge["source"], edge["target"], edge["line"], edge["access"])
            if key in seen_edges:
                continue
            seen_edges.add(key)
            item = dict(edge)
            item["depth"] = depth
            out.append(item)
            next_node = edge["source"] if direction == "incoming" else edge["target"]
            if next_node not in seen_nodes and len(out) < max_edges:
                seen_nodes.add(next_node)
                queue.append((next_node, depth + 1))
            if len(out) >= max_edges:
                break
    return out


def describe_edge(
    *,
    source: str,
    target: str,
    line: dict[str, Any],
    code: str,
) -> dict[str, Any]:
    op = first_opcode(code)
    return {
        "source": source,
        "target": target,
        "kind": classify_edge_kind(op),
        "access": classify_access(target, code, op),
        "path": line["path"],
        "line": line["line"],
        "text": line["text"],
    }


def resolve_query(
    query: str,
    *,
    graph: dict[str, Any],
    symbol_table: dict[str, dict[str, Any]],
) -> str | None:
    if query in graph["nodes"] or query in symbol_table:
        return query
    matches = [label for label in graph["nodes"] if label.endswith("." + query)]
    if len(matches) == 1:
        return matches[0]
    return None


def resolve_reference(
    token: str,
    *,
    current_global: str,
    known_labels: set[str],
) -> str | None:
    if token in IGNORED_TOKENS:
        return None
    if token in known_labels:
        return token
    if token.startswith(".") and current_global:
        scoped = current_global + token
        if scoped in known_labels:
            return scoped
    return None


def canonical_label(raw_label: str, *, current_global: str) -> str:
    if raw_label.startswith(".") and current_global:
        return current_global + raw_label
    return raw_label


def classify_edge_kind(op: str) -> str:
    if op in CALL_OPS:
        return "call"
    if op in JUMP_OPS:
        return "jump"
    if op in DATA_OPS:
        return "data"
    return "reference"


def classify_access(target: str, code: str, op: str) -> str:
    if op in CALL_OPS:
        return "call"
    if op in JUMP_OPS:
        return "jump"
    if op in DATA_OPS:
        return "data"
    bracketed = rf"\[\s*{re.escape(target)}(?:\s*[+\-][^\]]*)?\s*\]"
    if re.search(bracketed + r"\s*,", code):
        return "write"
    if re.search(r",\s*" + bracketed, code) or re.search(bracketed, code):
        return "read"
    if re.search(rf"\b(h?l|bc|de)\s*,\s*{re.escape(target)}\b", code):
        return "pointer"
    return "reference"


def first_opcode(code: str) -> str:
    stripped = code.strip()
    if not stripped:
        return ""
    label = match_label_definition(stripped)
    if label:
        colon = stripped.find(":")
        stripped = stripped[colon + 1 :].strip() if colon >= 0 else ""
    if not stripped:
        return ""
    return stripped.split(None, 1)[0].lower()


def match_label_definition(line: str) -> str:
    match = LABEL_DEF_RE.match(line)
    if match:
        return match.group("label")
    if line[:1].isspace():
        return ""
    stripped = strip_comment(line).strip()
    match = BARE_LABEL_RE.match(stripped)
    if not match:
        return ""
    label = match.group("label")
    if label.lower() in LINE_OPS or label in IGNORED_TOKENS:
        return ""
    return label


def strip_comment(line: str) -> str:
    in_quote = False
    escaped = False
    out = []
    for char in line:
        if char == "\\" and in_quote:
            escaped = not escaped
            out.append(char)
            continue
        if char == '"' and not escaped:
            in_quote = not in_quote
        escaped = False
        if char == ";" and not in_quote:
            break
        out.append(char)
    return "".join(out)


def edge_sort_key(edge: dict[str, Any]) -> tuple[Any, ...]:
    return (
        edge.get("path", ""),
        int(edge.get("line", 0)),
        edge.get("source", ""),
        edge.get("target", ""),
        edge.get("access", ""),
    )
