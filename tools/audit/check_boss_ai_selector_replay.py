#!/usr/bin/env python3
"""Verify exact BossAI_SelectMove replay against captured ROM score bytes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from _common import fail


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_debugger.trace_replay import replay_trace_paths
from tools.trace.runtime import display_path, sha256_file

from _trace_artifacts import require_manifest_basis


TRACE_DIR = ROOT / "audit" / "boss_ai_trace"
MANIFEST = TRACE_DIR / "live_capture_manifest.json"
MIN_EXACT_CAPTURES = 18
MIN_AGREEMENT = 0.9999


def rel_or_abs(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def parse_key_values(path: Path) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        fields[key.strip()] = value.strip()
    return fields


def load_trace_basis() -> dict[str, str]:
    if not MANIFEST.exists():
        fail(f"missing trace manifest: {MANIFEST}")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    basis: dict[str, str] = {}
    for path_key, hash_key in (
        ("trace_rom", "trace_rom_sha256"),
        ("trace_symbols", "trace_symbols_sha256"),
    ):
        path_text = data.get(path_key)
        expected_hash = data.get(hash_key)
        if not isinstance(path_text, str) or not path_text:
            fail(f"manifest missing {path_key}")
        if not isinstance(expected_hash, str) or not expected_hash:
            fail(f"manifest missing {hash_key}")
        path = rel_or_abs(path_text)
        actual_hash = sha256_file(path)
        if actual_hash.upper() != expected_hash.upper():
            fail(
                f"manifest {path_key} hash mismatch: "
                f"expected {expected_hash.upper()}, found {actual_hash}"
            )
        basis[path_key] = display_path(path)
        basis[hash_key] = expected_hash.upper()
    return basis


def selector_replay_paths() -> list[Path]:
    if not MANIFEST.exists():
        fail(f"missing trace manifest: {MANIFEST}")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    captures = data.get("captures", [])
    if not isinstance(captures, list):
        fail(f"manifest captures must be a list: {MANIFEST}")

    paths: list[Path] = []
    for capture in captures:
        if not isinstance(capture, dict):
            continue
        if capture.get("status") != "FINISHED":
            continue
        if capture.get("require_chosen_move") is False:
            continue
        out = capture.get("out")
        if not isinstance(out, str) or not out:
            continue
        paths.append(rel_or_abs(out))
    if not paths:
        fail(f"manifest has no finished chosen-move captures: {MANIFEST}")

    missing = [path for path in paths if not path.exists()]
    if missing:
        fail("missing selector trace file(s): " + ", ".join(str(path) for path in missing))
    return sorted(paths)


def validate_trace_basis(paths: list[Path], basis: dict[str, str]) -> None:
    for path in paths:
        fields = parse_key_values(path)
        for key, expected in basis.items():
            found = fields.get(key, "")
            if found.upper() != expected.upper():
                fail(
                    f"{path}: {key} does not match manifest "
                    f"(expected {expected}, found {found})"
                )


def main() -> int:
    require_manifest_basis()
    paths = selector_replay_paths()

    basis = load_trace_basis()
    validate_trace_basis(paths, basis)
    report = replay_trace_paths(paths)
    if report["checked_count"] != report["capture_count"]:
        missing = report["capture_count"] - report["checked_count"]
        fail(f"{missing} selector capture(s) had no replayable decision")
    if report["failure_count"]:
        fail(f"{report['failure_count']} selector replay mismatch(es)")
    if report["partial_count"]:
        fail(
            f"{report['partial_count']} capture(s) only have partial top-three evidence"
        )
    if report["exact_count"] != report["checked_count"]:
        fail(
            f"only {report['exact_count']} of {report['checked_count']} "
            "checked captures had exact score-byte evidence"
        )
    if report["exact_count"] < MIN_EXACT_CAPTURES:
        fail(
            f"only {report['exact_count']} exact captures; "
            f"expected at least {MIN_EXACT_CAPTURES}"
        )
    if report["exact_agreement_rate"] < MIN_AGREEMENT:
        fail(
            f"exact replay agreement {report['exact_agreement_rate']:.4%} "
            f"is below {MIN_AGREEMENT:.4%}"
        )

    print(
        "Boss AI selector replay audit passed: "
        f"{report['exact_match_count']} / {report['exact_count']} exact captures "
        f"matched ({report['exact_agreement_rate']:.4%})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
