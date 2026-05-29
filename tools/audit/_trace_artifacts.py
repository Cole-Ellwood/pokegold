"""Skip-gating for audit checks that depend on the gitignored trace ROM build.

`pokegold_trace.gbc` / `.sym` / `.map` are gitignored build outputs. A fresh
checkout or CI run has none of them, and a from-current-source rebuild
legitimately differs from the SHA the tracked live-capture manifest
(`audit/boss_ai_trace/live_capture_manifest.json`) was recorded against.

These checks verify *dynamic* trace behavior (PyBoy replay, ROM contribution
materialization, selector agreement). They only mean something when run against
the exact trace ROM the recorded captures came from. Rather than hard-FAIL the
audit floor for a missing or stale local build, they SKIP with an actionable
message: build the trace ROM (docs/boss_ai_trace_capture.md) and refresh the
manifest + captures to re-enable them.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parents[2]
TRACE_ROM = ROOT / "pokegold_trace.gbc"
TRACE_SYM = ROOT / "pokegold_trace.sym"
TRACE_MAP = ROOT / "pokegold_trace.map"
MANIFEST = ROOT / "audit" / "boss_ai_trace" / "live_capture_manifest.json"


def skip(message: str) -> NoReturn:
    print(f"SKIP: {message}")
    raise SystemExit(0)


def _sha256_upper(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def require_present(*paths: Path) -> None:
    """SKIP unless every given trace artifact exists on disk."""
    missing = [p.name for p in paths if not p.exists()]
    if missing:
        skip(
            f"trace build artifact(s) absent ({', '.join(missing)}); build "
            "pokegold_trace.gbc per docs/boss_ai_trace_capture.md to run this check"
        )


def require_manifest_basis(manifest_path: Path = MANIFEST) -> None:
    """SKIP unless the on-disk trace ROM and symbols match the manifest-pinned SHAs.

    A fresh checkout has no trace ROM (-> SKIP). A from-current-source rebuild
    that has not been re-captured will not match the recorded SHA (-> SKIP).
    Only when the local build *is* the recorded capture basis does the caller
    proceed to its real dynamic assertions. A malformed or hash-less manifest is
    a genuine defect, so this returns and lets the caller surface it.
    """
    require_present(TRACE_ROM, TRACE_SYM)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    for artifact, hash_key in (
        (TRACE_ROM, "trace_rom_sha256"),
        (TRACE_SYM, "trace_symbols_sha256"),
    ):
        pinned = manifest.get(hash_key)
        if not isinstance(pinned, str) or not pinned:
            return
        actual = _sha256_upper(artifact)
        if actual != pinned.upper():
            skip(
                f"local {artifact.name} ({actual[:12]}...) does not match the "
                f"manifest-pinned capture basis ({pinned.upper()[:12]}...); rebuild "
                "the trace ROM and refresh the manifest + captures "
                "(docs/boss_ai_trace_capture.md) to run this check"
            )
