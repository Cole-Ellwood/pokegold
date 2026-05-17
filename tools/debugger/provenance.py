from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .catalog import ROOT, triage_request
from .ingest import sha256_file


SOURCE_ROOTS = (
    "ram",
    "engine",
    "home",
    "data",
    "maps",
    "constants",
    "macros",
)
SOURCE_SUFFIXES = {".asm", ".inc", ".py", ".md", ".json", ".jsonl", ".txt"}
SYMBOL_LINE_RE = re.compile(r"^(?P<bank>[0-9A-Fa-f]{2}):(?P<addr>[0-9A-Fa-f]{4})\s+(?P<label>\S+)")
LABEL_DEF_RE = re.compile(r"^\s*(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*)(?P<global>::|:)")


def build_provenance_report(
    *,
    symbols_path: str = "pokegold.sym",
    symbols: tuple[str, ...] = (),
    source_files: tuple[str, ...] = (),
    include_docs: bool = False,
    max_hits: int = 40,
    root: Path = ROOT,
) -> dict[str, Any]:
    sym_path = resolve_path(symbols_path, root=root)
    errors: list[str] = []
    warnings: list[str] = []
    symbol_table: dict[str, dict[str, Any]] = {}
    if sym_path.exists():
        symbol_table = parse_symbol_table(sym_path)
    else:
        errors.append(f"missing symbol file: {symbols_path}")

    source_paths = collect_source_paths(
        root=root,
        include_docs=include_docs,
        explicit_paths=source_files,
    )
    symbol_reports = [
        describe_symbol(
            symbol,
            symbol_table=symbol_table,
            source_paths=source_paths,
            max_hits=max_hits,
            root=root,
        )
        for symbol in symbols
    ]
    source_reports = [
        describe_source_file(
            source_file,
            symbol_table=symbol_table,
            root=root,
        )
        for source_file in source_files
    ]
    warnings.extend(
        warning
        for report in symbol_reports
        for warning in report.get("warnings", [])
    )
    errors.extend(
        error
        for report in source_reports
        for error in report.get("errors", [])
    )
    changed_files = tuple(
        report["path"]
        for report in source_reports
        if report.get("exists")
    )
    triage = triage_request(changed_files=changed_files, root=root) if changed_files else None

    return {
        "schema_version": 1,
        "kind": "unified_debugger_provenance_report",
        "root": str(root),
        "symbols_path": display_path(sym_path, root=root),
        "symbols_sha256": sha256_file(sym_path) if sym_path.exists() else "",
        "symbol_count": len(symbol_table),
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "symbols": symbol_reports,
        "source_files": source_reports,
        "triage": triage,
        "known_limits": [
            "This is static symbol/source provenance, not a runtime dataflow slice.",
            "Use subsystem traces or replay tools to prove dynamic execution paths.",
        ],
    }


def parse_symbol_table(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = SYMBOL_LINE_RE.match(line.strip())
        if not match:
            continue
        label = match.group("label")
        bank = int(match.group("bank"), 16)
        address = int(match.group("addr"), 16)
        out[label] = {
            "label": label,
            "bank": bank,
            "address": address,
            "bank_hex": f"{bank:02X}",
            "address_hex": f"{address:04X}",
            "bank_address": f"{bank:02X}:{address:04X}",
        }
    return out


def describe_symbol(
    symbol: str,
    *,
    symbol_table: dict[str, dict[str, Any]],
    source_paths: list[Path],
    max_hits: int,
    root: Path,
) -> dict[str, Any]:
    exact = symbol_table.get(symbol)
    all_source_hits = find_source_hits(symbol, source_paths, root=root)
    source_hits = all_source_hits[:max_hits]
    related_files = sorted({hit["path"] for hit in all_source_hits})
    triage = triage_request(changed_files=tuple(related_files), root=root) if related_files else None
    warnings = []
    if exact is None:
        warnings.append(f"symbol not present in symbol table: {symbol}")
    return {
        "query": symbol,
        "found_in_symbols": exact is not None,
        "address": exact,
        "source_hit_count": len(all_source_hits),
        "source_hits": source_hits,
        "related_files": related_files,
        "triage_match_ids": [
            match["id"] for match in triage["matches"]
        ] if triage else [],
        "suggested_commands": triage["commands"] if triage else [],
        "warnings": warnings,
    }


def find_source_hits(
    symbol: str,
    source_paths: list[Path],
    *,
    root: Path,
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    boundary = re.compile(rf"(?<![A-Za-z0-9_.$]){re.escape(symbol)}(?![A-Za-z0-9_.$])")
    for path in source_paths:
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, 1):
            if not boundary.search(line):
                continue
            hit_type = classify_hit(symbol, line)
            hits.append(
                {
                    "path": display_path(path, root=root),
                    "line": line_no,
                    "kind": hit_type,
                    "text": line.strip()[:180],
                }
            )
    hits.sort(key=lambda hit: (0 if hit["kind"] == "definition" else 1, hit["path"], hit["line"]))
    return hits


def classify_hit(symbol: str, line: str) -> str:
    match = LABEL_DEF_RE.match(line)
    if match and match.group("label") == symbol:
        return "definition"
    if line.lstrip().startswith(f"{symbol}::") or line.lstrip().startswith(f"{symbol}:"):
        return "definition"
    return "reference"


def describe_source_file(
    source_file: str,
    *,
    symbol_table: dict[str, dict[str, Any]],
    root: Path,
) -> dict[str, Any]:
    path = resolve_path(source_file, root=root)
    report: dict[str, Any] = {
        "path": display_path(path, root=root),
        "input_path": source_file,
        "exists": path.exists(),
        "labels": [],
        "label_count": 0,
        "symbols_matched_count": 0,
        "errors": [],
    }
    if not path.exists():
        report["errors"].append(f"source path does not exist: {source_file}")
        return report
    if path.is_dir():
        report["errors"].append(f"source path is a directory: {source_file}")
        return report
    labels = extract_labels(path, root=root)
    for label in labels:
        symbol = symbol_table.get(label["label"])
        if symbol:
            label["address"] = symbol
    report["labels"] = labels[:80]
    report["label_count"] = len(labels)
    report["symbols_matched_count"] = sum(1 for label in labels if "address" in label)
    return report


def extract_labels(path: Path, *, root: Path) -> list[dict[str, Any]]:
    labels: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        match = LABEL_DEF_RE.match(line)
        if not match:
            continue
        labels.append(
            {
                "label": match.group("label"),
                "line": line_no,
                "scope": "global" if match.group("global") == "::" else "local_or_file",
                "path": display_path(path, root=root),
            }
        )
    return labels


def collect_source_paths(
    *,
    root: Path,
    include_docs: bool,
    explicit_paths: tuple[str, ...],
) -> list[Path]:
    paths: list[Path] = []
    seen: set[Path] = set()
    roots = list(SOURCE_ROOTS)
    if include_docs:
        roots.append("docs")
    for source_root in roots:
        base = root / source_root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            paths.append(path)
    for explicit in explicit_paths:
        path = resolve_path(explicit, root=root)
        if path.exists() and path.is_file():
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                paths.append(path)
    return sorted(paths, key=lambda item: display_path(item, root=root))


def resolve_path(raw_path: str, *, root: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return root / path


def display_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve())
