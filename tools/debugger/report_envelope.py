from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

from .catalog import ROOT


SCHEMA_VERSION = 1
UNKNOWN_HASH = ""
UNKNOWN_GIT_VALUE = "unknown"

# Generated proof artifacts and emulator scratch outputs. Proof identities
# exclude these paths from their source basis so that refreshing or committing
# already-validated evidence does not void the evidence, while any real source
# change still does.
PROOF_ARTIFACT_PATH_PREFIXES = (
    "audit/boss_ai_debugger",
    "audit/boss_ai_trace",
    "audit/damage_debugger",
    "audit/debugger_literal_anything",
    "audit/debugger_checkpoints",
    "audit/headless_battle",
    ".local",
    "pokegold.gbc.ram",
    "pokegold.gbc.rtc",
    "pokegold.sav",
    "pokegold_debug.gbc.ram",
    "pokegold_debug.gbc.rtc",
    "pokegold_trace.gbc.ram",
    "pokegold_trace.gbc.rtc",
)


def sha256_file(path: Path | str | None, *, root: Path = ROOT) -> str:
    if path in (None, ""):
        return UNKNOWN_HASH
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = root / resolved
    if not resolved.exists() or not resolved.is_file():
        return UNKNOWN_HASH
    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def source_commit(root: Path = ROOT) -> str:
    return _git_stdout(root, "rev-parse", "HEAD") or UNKNOWN_GIT_VALUE


def source_tree_hash(
    root: Path = ROOT,
    *,
    exclude_path_prefixes: tuple[str, ...] = (),
) -> str:
    """Content hash of the tracked source tree, excluding artifact paths.

    Hashes `git ls-files -s` (mode, blob oid, stage, path) so the value pins
    the exact tracked content while staying stable when excluded artifact
    paths change or get committed. Pair with dirty_diff_hash (same excludes),
    which covers unstaged edits and untracked files, to pin the working state
    by content rather than by commit pointer - a commit that only adds
    artifacts does not shift the basis, so proofs can stay valid once their
    artifacts land in git.
    """
    pathspec = _exclude_pathspec(exclude_path_prefixes)
    listing = _git_stdout(root, "ls-files", "-s", *pathspec)
    if listing is None:
        return UNKNOWN_GIT_VALUE
    return hashlib.sha256(listing.encode("utf-8", errors="replace")).hexdigest().upper()


def proof_source_tree_hash(root: Path = ROOT) -> str:
    """Content-scoped source identity for proof artifacts (artifact dirs excluded)."""
    return source_tree_hash(root, exclude_path_prefixes=PROOF_ARTIFACT_PATH_PREFIXES)


def proof_dirty_diff_hash(root: Path = ROOT) -> str:
    """Working-state identity for proof artifacts (artifact dirs excluded)."""
    return dirty_diff_hash(root, exclude_path_prefixes=PROOF_ARTIFACT_PATH_PREFIXES)


def dirty_diff_hash(
    root: Path = ROOT,
    *,
    exclude_path_prefixes: tuple[str, ...] = (),
) -> str:
    pathspec = _exclude_pathspec(exclude_path_prefixes)
    status = _git_stdout(root, "status", "--porcelain=v1", "--untracked-files=all", *pathspec)
    diff = _git_stdout(root, "diff", "--binary", *pathspec)
    cached_diff = _git_stdout(root, "diff", "--cached", "--binary", *pathspec)
    if status is None and diff is None:
        return UNKNOWN_GIT_VALUE
    digest = hashlib.sha256()
    digest.update((status or "").encode("utf-8", errors="replace"))
    digest.update(b"\0")
    digest.update((diff or "").encode("utf-8", errors="replace"))
    digest.update(b"\0CACHED\0")
    digest.update((cached_diff or "").encode("utf-8", errors="replace"))
    digest.update(b"\0UNTRACKED\0")
    for rel_path in _untracked_paths(status or ""):
        path = root / rel_path
        digest.update(rel_path.as_posix().encode("utf-8", errors="replace"))
        digest.update(b"\0")
        if path.is_file():
            digest.update(_hash_untracked_file(path).encode("ascii"))
        elif path.exists():
            digest.update(b"non-file")
        else:
            digest.update(b"missing")
        digest.update(b"\0")
    return digest.hexdigest().upper()


def _exclude_pathspec(prefixes: tuple[str, ...]) -> list[str]:
    if not prefixes:
        return []
    pathspec = ["--", "."]
    for prefix in prefixes:
        normalized = prefix.replace("\\", "/").strip("/")
        if normalized:
            pathspec.append(f":(exclude){normalized}")
            pathspec.append(f":(exclude){normalized}/**")
    return pathspec


def build_report_envelope(
    *,
    kind: str,
    command: str,
    inputs: dict[str, Any] | None = None,
    rom_path: Path | str | None = None,
    symbols_path: Path | str | None = None,
    state_basis: dict[str, Any] | None = None,
    backend: str = "static",
    proof_status: str = "missing_evidence",
    missing_evidence: list[str] | tuple[str, ...] | None = None,
    blocking_gaps: list[str] | tuple[str, ...] | None = None,
    known_limits: list[str] | tuple[str, ...] | None = None,
    closed_evidence_ids: list[str] | tuple[str, ...] | None = None,
    repro_command: str = "",
    disproof_standard: list[str] | tuple[str, ...] | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Return the shared proof-report envelope required by the roadmap."""

    return {
        "schema_version": SCHEMA_VERSION,
        "kind": kind,
        "command": command,
        "inputs": dict(inputs or {}),
        "rom_sha256": sha256_file(rom_path, root=root),
        "symbols_sha256": sha256_file(symbols_path, root=root),
        "source_commit": source_commit(root),
        "dirty_diff_hash": dirty_diff_hash(root),
        "state_basis": dict(state_basis or {}),
        "backend": backend,
        "proof_status": proof_status,
        "missing_evidence": list(missing_evidence or ()),
        "blocking_gaps": list(blocking_gaps or ()),
        "known_limits": list(known_limits or ()),
        "closed_evidence_ids": list(closed_evidence_ids or ()),
        "repro_command": repro_command,
        "disproof_standard": list(disproof_standard or ()),
    }


def _git_stdout(root: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip()


def _untracked_paths(status: str) -> list[Path]:
    paths: list[Path] = []
    for line in status.splitlines():
        if not line.startswith("?? "):
            continue
        text = line[3:].strip()
        if text:
            paths.append(Path(text))
    return sorted(paths, key=lambda item: item.as_posix())


def _hash_untracked_file(path: Path) -> str:
    # Untracked files are part of the proof basis. Hash small/normal artifacts
    # directly; for unexpectedly large local outputs, hash size+mtime so the
    # basis still changes without loading arbitrary build products into memory.
    max_bytes = 8 * 1024 * 1024
    stat = path.stat()
    if stat.st_size > max_bytes:
        payload = f"large:{stat.st_size}:{stat.st_mtime_ns}".encode("ascii")
        return hashlib.sha256(payload).hexdigest().upper()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()
