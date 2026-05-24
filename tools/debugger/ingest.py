from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .catalog import ROOT, triage_request
from .save_state_format import inspect_save_state_header


SYMBOL_RE = re.compile(r"^(?P<bank>[0-9A-Fa-f]{2}):(?P<addr>[0-9A-Fa-f]{4})\s+(?P<label>\S+)")


def ingest_artifacts(
    *,
    roms: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    traces: tuple[str, ...] = (),
    save_states: tuple[str, ...] = (),
    scenarios: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    root: Path = ROOT,
) -> dict[str, Any]:
    artifacts: list[dict[str, Any]] = []
    for path in roms:
        artifacts.append(inspect_artifact("rom", path, root=root))
    for path in symbols:
        artifacts.append(inspect_artifact("symbols", path, root=root))
    for path in traces:
        artifacts.append(inspect_artifact("trace", path, root=root))
    for path in save_states:
        artifacts.append(inspect_artifact("save_state", path, root=root))
    for path in scenarios:
        artifacts.append(inspect_artifact("scenario", path, root=root))
    for path in changed_files:
        artifact = inspect_artifact(
            "source_change",
            path,
            root=root,
            require_exists=False,
        )
        triage = triage_request(changed_files=(path,), root=root)
        artifact["metadata"]["triage_match_ids"] = [
            match["id"] for match in triage["matches"]
        ]
        artifact["metadata"]["suggested_commands"] = triage["commands"]
        artifacts.append(artifact)

    error_count = sum(len(artifact["errors"]) for artifact in artifacts)
    warning_count = sum(len(artifact["warnings"]) for artifact in artifacts)
    return {
        "schema_version": 1,
        "kind": "unified_debugger_ingest_manifest",
        "root": str(root),
        "valid": error_count == 0,
        "artifact_count": len(artifacts),
        "error_count": error_count,
        "warning_count": warning_count,
        "artifacts": artifacts,
    }


def inspect_artifact(
    kind: str,
    raw_path: str,
    *,
    root: Path = ROOT,
    require_exists: bool = True,
) -> dict[str, Any]:
    path = resolve_path(raw_path, root=root)
    artifact = base_artifact(kind, raw_path, path, root=root)
    if not path.exists():
        message = f"{kind} path does not exist: {raw_path}"
        if require_exists:
            artifact["errors"].append(message)
        else:
            artifact["warnings"].append(message)
        return artifact
    if path.is_dir():
        artifact["errors"].append(f"{kind} path is a directory: {raw_path}")
        return artifact

    artifact["exists"] = True
    artifact["size_bytes"] = path.stat().st_size
    artifact["sha256"] = sha256_file(path)

    if kind == "rom":
        inspect_rom(path, artifact)
    elif kind == "symbols":
        inspect_symbols(path, artifact)
    elif kind == "trace":
        inspect_trace(path, artifact)
    elif kind == "scenario":
        inspect_scenario(path, artifact)
    elif kind == "save_state":
        inspect_save_state(path, artifact)
    elif kind == "source_change":
        inspect_source_change(path, artifact)
    return artifact


def base_artifact(kind: str, raw_path: str, path: Path, *, root: Path) -> dict[str, Any]:
    return {
        "kind": kind,
        "path": display_path(path, root=root),
        "input_path": raw_path,
        "exists": False,
        "size_bytes": 0,
        "sha256": "",
        "metadata": {},
        "warnings": [],
        "errors": [],
    }


def inspect_rom(path: Path, artifact: dict[str, Any]) -> None:
    size = artifact["size_bytes"]
    metadata = artifact["metadata"]
    metadata["extension"] = path.suffix.lower()
    metadata["size_multiple_16k"] = size % 0x4000 == 0
    if size < 0x150:
        artifact["errors"].append("ROM is too small to contain a Game Boy header.")
        return
    header = path.read_bytes()[0x100:0x150]
    title = header[0x34:0x44].split(b"\0", 1)[0]
    metadata["title"] = ascii_printable(title)
    metadata["cgb_flag"] = f"0x{header[0x43]:02X}"
    metadata["cartridge_type"] = f"0x{header[0x47]:02X}"
    metadata["rom_size_code"] = f"0x{header[0x48]:02X}"
    metadata["ram_size_code"] = f"0x{header[0x49]:02X}"
    metadata["header_checksum"] = f"0x{header[0x4D]:02X}"
    metadata["global_checksum"] = f"0x{header[0x4E]:02X}{header[0x4F]:02X}"
    if path.suffix.lower() not in {".gb", ".gbc"}:
        artifact["warnings"].append("ROM path does not use .gb or .gbc extension.")


def inspect_symbols(path: Path, artifact: dict[str, Any]) -> None:
    label_count = 0
    banks: set[str] = set()
    first_labels: list[str] = []
    bad_lines = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue
        match = SYMBOL_RE.match(stripped)
        if not match:
            bad_lines += 1
            continue
        label_count += 1
        banks.add(match.group("bank").upper())
        if len(first_labels) < 5:
            first_labels.append(match.group("label"))
    metadata = artifact["metadata"]
    metadata["label_count"] = label_count
    metadata["bank_count"] = len(banks)
    metadata["first_labels"] = first_labels
    metadata["unparsed_line_count"] = bad_lines
    if label_count == 0:
        artifact["errors"].append("symbol file contains no parsed labels.")


def inspect_trace(path: Path, artifact: dict[str, Any]) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    stripped = text.lstrip()
    metadata = artifact["metadata"]
    metadata["line_count"] = len(lines)
    if not lines:
        artifact["errors"].append("trace file is empty.")
        return
    if path.suffix.lower() == ".jsonl":
        inspect_jsonl_trace(lines, metadata, artifact)
        return
    if path.suffix.lower() == ".json" or stripped.startswith(("{", "[")):
        inspect_json_trace(text, metadata, artifact)
        return

    key_values: dict[str, str] = {}
    for line in lines:
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key_values[key.strip()] = value.strip()
    metadata["format"] = "key_value"
    metadata["key_count"] = len(key_values)
    metadata["keys_sample"] = sorted(key_values)[:12]
    metadata["trace_rom_sha256"] = key_values.get("trace_rom_sha256", "")
    metadata["trace_symbols_sha256"] = key_values.get("trace_symbols_sha256", "")
    metadata["chosen"] = key_values.get("chosen", "")
    metadata["move_scores"] = key_values.get("move_scores", "")
    if not key_values:
        artifact["warnings"].append("trace file has no key=value fields.")


def inspect_json_trace(text: str, metadata: dict[str, Any], artifact: dict[str, Any]) -> None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        artifact["errors"].append(f"invalid JSON trace: {exc.msg}")
        return
    metadata["format"] = "json"
    summarize_trace_data(data, metadata)


def inspect_jsonl_trace(lines: list[str], metadata: dict[str, Any], artifact: dict[str, Any]) -> None:
    records = []
    for line_no, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            artifact["errors"].append(f"line {line_no}: invalid JSON trace: {exc.msg}")
    metadata["format"] = "jsonl"
    metadata["record_count"] = len(records)
    summarize_trace_data(records, metadata)


def summarize_trace_data(data: Any, metadata: dict[str, Any]) -> None:
    keys: set[str] = set()
    symbols: list[str] = []
    source_files: list[str] = []
    walk_trace_data(data, keys=keys, symbols=symbols, source_files=source_files)
    metadata["key_count"] = len(keys)
    metadata["keys_sample"] = sorted(keys)[:12]
    metadata["symbol_sample"] = unique_list(symbols)[:12]
    metadata["source_file_sample"] = unique_list(source_files)[:12]


def walk_trace_data(
    data: Any,
    *,
    keys: set[str],
    symbols: list[str],
    source_files: list[str],
) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            keys.add(str(key))
            if key in {"full_symbol", "symbol", "pc_label", "watch", "query", "resolved"} and isinstance(value, str):
                symbols.append(value)
            if key == "source_file" and isinstance(value, str):
                source_files.append(value)
            walk_trace_data(value, keys=keys, symbols=symbols, source_files=source_files)
    elif isinstance(data, list):
        for item in data:
            walk_trace_data(item, keys=keys, symbols=symbols, source_files=source_files)


def inspect_scenario(path: Path, artifact: dict[str, Any]) -> None:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        records, errors, families, ids = inspect_jsonl_scenario(path)
    elif suffix == ".json":
        records, errors, families, ids = inspect_json_scenario(path)
    else:
        records, errors, families, ids = (0, [f"unsupported scenario extension: {suffix}"], set(), [])
    metadata = artifact["metadata"]
    metadata["record_count"] = records
    metadata["families"] = sorted(families)
    metadata["ids_sample"] = ids[:5]
    artifact["errors"].extend(errors)
    if records == 0 and not errors:
        artifact["warnings"].append("scenario file contains no records.")


def inspect_jsonl_scenario(path: Path) -> tuple[int, list[str], set[str], list[str]]:
    records = 0
    errors: list[str] = []
    families: set[str] = set()
    ids: list[str] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(data, dict):
            errors.append(f"line {line_no}: scenario record must be an object")
            continue
        records += 1
        collect_scenario_metadata(data, families, ids)
    return records, errors, families, ids


def inspect_json_scenario(path: Path) -> tuple[int, list[str], set[str], list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return 0, [f"invalid JSON: {exc.msg}"], set(), []
    records_data = data if isinstance(data, list) else [data]
    records = 0
    errors: list[str] = []
    families: set[str] = set()
    ids: list[str] = []
    for index, item in enumerate(records_data):
        if not isinstance(item, dict):
            errors.append(f"record {index}: scenario record must be an object")
            continue
        records += 1
        collect_scenario_metadata(item, families, ids)
    return records, errors, families, ids


def collect_scenario_metadata(data: dict[str, Any], families: set[str], ids: list[str]) -> None:
    family = data.get("family")
    if isinstance(family, str) and family:
        families.add(family)
    scenario_id = data.get("id")
    if isinstance(scenario_id, str) and scenario_id and len(ids) < 20:
        ids.append(scenario_id)


def inspect_save_state(path: Path, artifact: dict[str, Any]) -> None:
    metadata = artifact["metadata"]
    metadata.update(inspect_save_state_header(path))
    parse_warning = metadata.pop("parse_warning", "")
    if parse_warning:
        artifact["warnings"].append(parse_warning)
    if artifact["size_bytes"] == 0:
        artifact["errors"].append("save-state file is empty.")


def inspect_source_change(path: Path, artifact: dict[str, Any]) -> None:
    metadata = artifact["metadata"]
    metadata["extension"] = path.suffix.lower()
    try:
        metadata["line_count"] = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except UnicodeDecodeError:
        metadata["line_count"] = None
        artifact["warnings"].append("source-change path is not UTF-8 text.")


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def ascii_printable(value: bytes) -> str:
    text = value.decode("ascii", errors="ignore")
    return "".join(char for char in text if 32 <= ord(char) <= 126).strip()


def unique_list(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out
