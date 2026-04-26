#!/usr/bin/env python3
"""Validate Boss AI live-capture ledger status and artifacts."""

from __future__ import annotations

import hashlib
import re
import sys
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "audit" / "boss_ai_trace" / "live_capture_ledger.md"
MANIFEST = ROOT / "audit" / "boss_ai_trace" / "live_capture_manifest.json"

ALLOWED_STATUSES = {"FINISHED", "IN PROGRESS", "UNTOUCHED"}
EXPECTED_BOSSES = {
    "Morty": "audit/boss_ai_trace/morty_live.txt",
    "Jasmine": "audit/boss_ai_trace/jasmine_live.txt",
    "Clair": "audit/boss_ai_trace/clair_live.txt",
    "Koga": "audit/boss_ai_trace/koga_live.txt",
    "Champion Lance": "audit/boss_ai_trace/champion_lance_live.txt",
    "Shared switch-loop": "audit/boss_ai_trace/shared_switch_loop_live.txt",
}
EXPECTED_CAPTURE_IDS = {
    "Morty": "morty",
    "Jasmine": "jasmine",
    "Clair": "clair",
    "Koga": "koga",
    "Champion Lance": "champion_lance",
    "Shared switch-loop": "shared_switch_loop",
}
REQUIRED_TOOLING_ARTIFACTS = (
    "audit/boss_ai_trace/trace_helper_smoke.txt",
    "audit/boss_ai_trace/trace_watch_smoke.txt",
)
REQUIRED_FINISHED_FIELDS = (
    "trace_rom",
    "trace_rom_sha256",
    "trace_symbols",
    "trace_symbols_sha256",
    "top_moves",
    "chosen",
    "switch_confidence",
    "plan_id",
    "plausible_mask",
    "risk_flags",
    "revealed_masks",
)

ROW_RE = re.compile(r"^\|\s*(?P<name>[^|]+?)\s*\|\s*`(?P<status>[^`]+)`\s*\|")
LIVE_ROW_RE = re.compile(
    r"^\|\s*(?P<boss>[^|]+?)\s*\|\s*`(?P<status>[^`]+)`\s*\|"
    r"\s*(?P<checks>[^|]+?)\s*\|\s*`(?P<path>[^`]+)`\s*\|"
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(resolved)


def rel_or_abs(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def extract_status(status: str, context: str) -> str:
    if status not in ALLOWED_STATUSES:
        fail(f"{context}: invalid status `{status}`")
    return status


def has_nonzero_trace_value(text: str) -> bool:
    patterns = (
        r"chosen_id=(\d+)",
        r"switch_confidence=(\d+)",
        r"plan_id=(\d+)",
        r"plan_confidence=(\d+)",
        r"risk_flags=([0-9a-fA-F]{2})",
        r"top_moves=.*:(\d+)",
        r"plausible_mask=([0-9a-fA-F ]+)",
        r"revealed_masks=([0-9a-fA-F ]+)",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            value = match.group(1)
            if " " in value:
                if any(int(part, 16) for part in value.split()):
                    return True
            elif re.fullmatch(r"[0-9a-fA-F]{2}", value):
                if int(value, 16):
                    return True
            elif int(value):
                return True
    return False


def parse_key_values(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw in block.splitlines():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        fields.setdefault(key.strip(), value.strip())
    return fields


def audit_finished_live_file(
    path: Path,
    boss: str,
    trace_basis: dict[str, str],
) -> None:
    if not path.exists():
        fail(f"{boss}: status is FINISHED but {rel(path)} does not exist")
    text = path.read_text(encoding="utf-8", errors="replace")
    blocks = [block.strip() for block in text.split("\n---\n") if block.strip()]
    if not blocks:
        fail(f"{boss}: finished live capture is empty")
    for index, block in enumerate(blocks, start=1):
        fields = parse_key_values(block)
        context = f"{boss} capture #{index}"
        for required in REQUIRED_FINISHED_FIELDS:
            if not fields.get(required):
                fail(f"{context}: finished live capture missing `{required}=`")
        for key, expected in trace_basis.items():
            found = fields[key]
            if found.upper() != expected.upper():
                fail(
                    f"{context}: `{key}` does not match manifest "
                    f"(expected {expected}, found {found})"
                )
    if "no_captures=true" in text:
        fail(f"{boss}: finished live capture still reports no captures")
    if not has_nonzero_trace_value(text):
        fail(f"{boss}: finished live capture has no nonzero trace evidence")


def audit_manifest(expected_rows: dict[str, tuple[str, str]]) -> dict[str, str]:
    if not MANIFEST.exists():
        fail(f"missing live capture manifest: {rel(MANIFEST)}")
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid live capture manifest JSON: {exc}")
    if not isinstance(data, dict):
        fail("live capture manifest root must be an object")
    captures = data.get("captures")
    if not isinstance(captures, list):
        fail("live capture manifest must contain a captures list")

    trace_basis: dict[str, str] = {}
    for path_key, hash_key in (
        ("trace_rom", "trace_rom_sha256"),
        ("trace_symbols", "trace_symbols_sha256"),
    ):
        path_text = data.get(path_key)
        expected_hash = data.get(hash_key)
        if not isinstance(path_text, str) or not path_text:
            fail(f"live capture manifest must pin `{path_key}`")
        if not isinstance(expected_hash, str) or not expected_hash:
            fail(f"live capture manifest must pin `{hash_key}`")
        path = rel_or_abs(path_text)
        if not path.exists():
            fail(f"manifest {path_key} points to missing file: {path_text}")
        actual_hash = sha256_file(path)
        if actual_hash.upper() != expected_hash.upper():
            fail(
                f"manifest {path_key} hash mismatch: "
                f"expected {expected_hash.upper()}, found {actual_hash}"
            )
        trace_basis[path_key] = display_path(path)
        trace_basis[hash_key] = expected_hash.upper()

    found: dict[str, dict[str, object]] = {}
    seen_ids: dict[str, str] = {}
    for index, entry in enumerate(captures, start=1):
        if not isinstance(entry, dict):
            fail(f"manifest capture #{index}: entry must be an object")
        capture_id = entry.get("id")
        boss = entry.get("boss")
        status = entry.get("status")
        out = entry.get("out")
        if not isinstance(capture_id, str):
            fail(f"manifest capture #{index}: id must be a string")
        if not isinstance(boss, str):
            fail(f"manifest capture #{index}: boss must be a string")
        if boss not in EXPECTED_BOSSES:
            fail(f"manifest capture #{index}: unexpected boss `{boss}`")
        expected_id = EXPECTED_CAPTURE_IDS[boss]
        if capture_id != expected_id:
            fail(f"manifest capture {boss}: expected id `{expected_id}`, found `{capture_id}`")
        if capture_id in seen_ids:
            fail(f"manifest capture id `{capture_id}` is duplicated for {seen_ids[capture_id]} and {boss}")
        seen_ids[capture_id] = boss
        if not isinstance(status, str) or status not in ALLOWED_STATUSES:
            fail(f"manifest capture {boss}: invalid status `{status}`")
        if not isinstance(out, str):
            fail(f"manifest capture {boss}: out must be a string")
        for key in ("notes", "save_state"):
            if key in entry and not isinstance(entry[key], str):
                fail(f"manifest capture {boss}: `{key}` must be a string")
        found[boss] = entry

    missing = sorted(set(EXPECTED_BOSSES) - set(found))
    if missing:
        fail("live capture manifest missing bosses: " + ", ".join(missing))
    missing_ids = sorted(set(EXPECTED_CAPTURE_IDS.values()) - set(seen_ids))
    if missing_ids:
        fail("live capture manifest missing ids: " + ", ".join(missing_ids))

    for boss, expected_path in EXPECTED_BOSSES.items():
        entry = found[boss]
        ledger_status, ledger_path = expected_rows[boss]
        manifest_status = str(entry["status"])
        manifest_path = str(entry["out"]).replace("\\", "/")
        if manifest_path != expected_path:
            fail(f"manifest {boss}: expected out {expected_path}, found {manifest_path}")
        if manifest_path != ledger_path:
            fail(f"manifest {boss}: path does not match ledger")
        if manifest_status != ledger_status:
            fail(f"manifest {boss}: status {manifest_status} does not match ledger {ledger_status}")

    return trace_basis


def main() -> int:
    if not LEDGER.exists():
        fail(f"missing live capture ledger: {rel(LEDGER)}")

    text = LEDGER.read_text(encoding="utf-8", errors="replace")
    for artifact in REQUIRED_TOOLING_ARTIFACTS:
        path = ROOT / artifact
        if not path.exists():
            fail(f"missing required tooling artifact: {artifact}")

    found: dict[str, tuple[str, str]] = {}
    for line in text.splitlines():
        match = LIVE_ROW_RE.match(line)
        if not match:
            tooling_match = ROW_RE.match(line)
            if tooling_match:
                extract_status(
                    tooling_match.group("status"),
                    tooling_match.group("name").strip(),
                )
            continue

        boss = match.group("boss").strip()
        if boss not in EXPECTED_BOSSES:
            continue
        status = extract_status(match.group("status"), boss)
        path_text = match.group("path").strip().replace("\\", "/")
        found[boss] = (status, path_text)

    missing = sorted(set(EXPECTED_BOSSES) - set(found))
    if missing:
        fail("missing priority boss live rows: " + ", ".join(missing))

    trace_basis = audit_manifest(found)

    for boss, expected_path in EXPECTED_BOSSES.items():
        status, path_text = found[boss]
        if path_text != expected_path:
            fail(f"{boss}: expected output path {expected_path}, found {path_text}")

        output_path = ROOT / path_text
        if status == "FINISHED":
            audit_finished_live_file(output_path, boss, trace_basis)
        elif status == "UNTOUCHED" and output_path.exists():
            fail(f"{boss}: live capture file exists but ledger still says UNTOUCHED")

    print("Boss AI live capture ledger audit passed.")
    print("Priority live captures:")
    for boss in EXPECTED_BOSSES:
        status, path_text = found[boss]
        print(f"  - {boss}: {status} ({path_text})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
