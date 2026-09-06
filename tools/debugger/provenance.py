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


def build_source_mapping_report(
    *, root: Path, destination: Path, candidate: dict[str, Any], bank: int, pc: int,
    build, rom_path: str = "pokegold.gbc", symbols_path: str = "pokegold.sym",
) -> dict[str, Any]:
    """Map a direct or far source call through an isolated label-only rebuild.

    root is a prepared RGBDS build tree; destination must be new and outside it.
    The trusted host supplies build(destination), returning a CompletedProcess.
    No command comes from candidate evidence. Object caches and .local artifacts are excluded so the
    annotated sources must be assembled. Invalid inputs raise before copying;
    failed builds retain their artifacts and return no mapping evidence.
    """
    import shutil
    from .clobber_graph import build_static_call_graph
    from .evidence import evidence_atom

    root, destination = root.resolve(), destination.resolve()
    if destination.exists():
        raise FileExistsError(destination)
    if destination.is_relative_to(root):
        raise ValueError("mapping destination must be outside the reference tree")
    if not isinstance(candidate, dict):
        raise ValueError("source candidate must be an object")
    for key in ("source_file", "source_symbol", "source_sha256", "instruction"):
        if not isinstance(candidate.get(key), str) or not candidate[key]:
            raise ValueError(f"missing candidate {key}")
    names = (candidate["source_file"], rom_path, symbols_path)
    if any(Path(name).is_absolute() or not (root / name).resolve().is_relative_to(root)
           or not (root / name).is_file() for name in names):
        raise ValueError("source, ROM, and symbols must be files within the reference tree")
    source = root / candidate["source_file"]
    payload = source.read_bytes()
    lines = payload.splitlines(keepends=True)
    line = candidate.get("source_line")
    if (type(line) is not int or not 1 <= line <= len(lines)
            or sha256_file(source) != candidate["source_sha256"]
            or lines[line - 1].decode("utf-8").strip() != candidate["instruction"]):
        raise ValueError("stale candidate source, line, or instruction")
    rom = root / rom_path
    if (type(bank) is not int or type(pc) is not int or bank < 0 or not 0 <= pc < 0x8000
            or (bank == 0) != (pc < 0x4000)
            or bank * 0x4000 + pc % 0x4000 + 3 > rom.stat().st_size):
        raise ValueError("call address is outside the ROM bank")
    graph = build_static_call_graph(root=root, source_files=(candidate["source_file"],))
    edges = [edge for edge in graph.edges_from(candidate["source_symbol"])
             if edge.line_number == line and edge.call_type in {"call", "farcall"} and edge.condition is None
             and edge.instruction == candidate["instruction"]]
    if len(edges) != 1:
        raise ValueError("candidate does not identify a source call in its block")
    original_symbols = parse_symbol_table(root / symbols_path)
    offset = bank * 0x4000 + pc % 0x4000
    rom_bytes = rom.read_bytes()
    if edges[0].call_type == "farcall":
        target = original_symbols.get(edges[0].callee, {})
        target_bank, target_pc = target.get("bank"), target.get("address")
        if (target_bank is None or target_pc is None or not 0 <= target_bank <= 255
                or pc % 0x4000 + 6 > 0x4000
                or rom_bytes[offset:offset + 6] != bytes([0x3E, target_bank, 0x21, target_pc & 255, target_pc >> 8, 0xCF])):
            raise ValueError("recorded location does not match the source far-call target and setup")
    elif rom_bytes[offset] != 0xCD:
        raise ValueError("recorded location is not a direct unconditional CALL")
    local_marker = f".__debugger_source_line_{line}"
    marker = graph.blocks[candidate["source_symbol"]].parent_label + local_marker
    if local_marker.encode() in payload or marker in original_symbols:
        raise ValueError("source mapping marker already exists")
    reference_hashes = {name: sha256_file(root / name) for name in names}
    lines.insert(line - 1, (local_marker + "\n").encode())
    annotated = b"".join(lines)
    report = build_provenance_report(root=root, symbols_path=symbols_path,
                                     symbols=(candidate["source_symbol"],), source_files=(candidate["source_file"],))
    report.update(valid=False, evidence_atoms=[], rom_sha256=reference_hashes[rom_path],
                  execution={"executed": False}, source_mapping={"candidate": dict(candidate), "marker": marker,
                  "destination": str(destination), "object_cache_excluded": True})
    try:
        shutil.copytree(root, destination, ignore=shutil.ignore_patterns(".git", ".local", "*.o"))
        (destination / candidate["source_file"]).write_bytes(annotated)
        report["execution"]["executed"] = True
        completed = build(destination)
        report["execution"].update(returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr,
                                     command=completed.args if isinstance(completed.args, str) else [str(arg) for arg in completed.args])
        if completed.returncode != 0:
            raise ValueError("source mapping build failed")
        if any(sha256_file(root / name) != digest for name, digest in reference_hashes.items()):
            raise ValueError("reference changed during build")
        if (destination / candidate["source_file"]).read_bytes() != annotated:
            raise ValueError("rebuilt source differs beyond the inserted marker")
        if sha256_file(destination / rom_path) != reference_hashes[rom_path]:
            raise ValueError("label-only build changed the ROM")
        rebuilt_symbols = parse_symbol_table(destination / symbols_path)
        linked = rebuilt_symbols.pop(marker, None)
        if not linked or linked["bank"] != bank or linked["address"] != pc:
            raise ValueError("linked source marker differs from the observed call address")
        if rebuilt_symbols != original_symbols:
            raise ValueError("label-only build changed original symbols")
        report["evidence_atoms"] = [evidence_atom(
            claim_type="provenance.source_mapping", origin="provenance", observation_type="label_only_rebuild",
            proof_status="mirror_passed", source_report=str(destination / symbols_path), source_kind="linker_symbols",
            precision={"source_file": candidate["source_file"], "source_symbol": candidate["source_symbol"],
                       "source_line": line, "bank": bank, "pc": pc},
            validation={"rom_identical": True, "original_symbols_unchanged": True, "only_label_added": True},
            detail={"source_sha256": reference_hashes[candidate["source_file"]],
                    "instrumented_source_sha256": sha256_file(destination / candidate["source_file"]),
                    "rebuilt_symbols_sha256": sha256_file(destination / symbols_path)},
        )]
    except Exception as exc:
        report["errors"].append(f"source mapping failed: {exc}")
    report["valid"] = not report["errors"]
    report["error_count"] = len(report["errors"])
    report["known_limits"].append("This verifies a source call address, not causal correctness; the host owns build configuration and toolchain provenance.")
    return report


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
