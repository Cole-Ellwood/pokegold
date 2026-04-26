#!/usr/bin/env python3
"""Run Boss AI live trace captures from a manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "audit" / "boss_ai_trace" / "live_capture_manifest.json"
CAPTURE_HELPER = ROOT / "tools" / "trace" / "boss_ai_trace_capture.py"
STATE_PROBE = ROOT / "tools" / "trace" / "boss_ai_trace_state_probe.py"
ALLOWED_STATUSES = {"FINISHED", "IN PROGRESS", "UNTOUCHED"}
PREFLIGHT_EXPECT_FLAGS = {
    "morty": "--expect-morty",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


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


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"missing manifest: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")
    if not isinstance(data, dict):
        fail("manifest root must be an object")
    captures = data.get("captures")
    if not isinstance(captures, list):
        fail("manifest must contain a captures list")
    return data


def as_int(data: dict[str, Any], key: str, default: int) -> int:
    value = data.get(key, default)
    if not isinstance(value, int) or value <= 0:
        fail(f"{key} must be a positive integer")
    return value


def optional_manifest_path(data: dict[str, Any], key: str) -> Path | None:
    value = data.get(key, "")
    if value == "":
        return None
    if not isinstance(value, str):
        fail(f"{key} must be a string")
    return rel_or_abs(value)


def validate_manifest_hash(data: dict[str, Any], path_key: str, hash_key: str) -> Path | None:
    path = optional_manifest_path(data, path_key)
    if path is None:
        return None
    if not path.exists():
        fail(f"{path_key} points to a missing file: {path}")

    expected = data.get(hash_key, "")
    if expected == "":
        return path
    if not isinstance(expected, str):
        fail(f"{hash_key} must be a string")
    actual = sha256_file(path)
    if actual.upper() != expected.upper():
        fail(
            f"{path_key} hash mismatch for {path}: "
            f"expected {expected.upper()}, found {actual}"
        )
    return path


def validate_capture(entry: dict[str, Any], index: int) -> None:
    for key in ("id", "boss", "status", "out", "notes"):
        if not isinstance(entry.get(key), str):
            fail(f"capture #{index}: `{key}` must be a string")
    if entry["status"] not in ALLOWED_STATUSES:
        fail(f"capture {entry['id']}: invalid status {entry['status']}")
    if "save_state" in entry and not isinstance(entry["save_state"], str):
        fail(f"capture {entry['id']}: `save_state` must be a string")
    if "watch_frames" in entry and (
        not isinstance(entry["watch_frames"], int) or entry["watch_frames"] <= 0
    ):
        fail(f"capture {entry['id']}: `watch_frames` must be a positive integer")
    if "poll_every" in entry and (
        not isinstance(entry["poll_every"], int) or entry["poll_every"] <= 0
    ):
        fail(f"capture {entry['id']}: `poll_every` must be a positive integer")
    preflight = entry.get("preflight")
    if preflight is None:
        return
    if not isinstance(preflight, dict):
        fail(f"capture {entry['id']}: `preflight` must be an object")
    expect = preflight.get("expect")
    if expect not in PREFLIGHT_EXPECT_FLAGS:
        fail(
            f"capture {entry['id']}: unsupported preflight expectation "
            f"`{expect}`"
        )
    if entry["id"] != expect:
        fail(
            f"capture {entry['id']}: preflight expectation `{expect}` "
            "must match capture id"
        )


def validate_capture_ids(captures: list[Any], selected: set[str]) -> None:
    ids: set[str] = set()
    duplicates: set[str] = set()
    for index, raw_entry in enumerate(captures, start=1):
        if not isinstance(raw_entry, dict):
            fail(f"capture #{index}: entry must be an object")
        validate_capture(raw_entry, index)
        capture_id = raw_entry["id"]
        if capture_id in ids:
            duplicates.add(capture_id)
        ids.add(capture_id)

    if duplicates:
        fail("duplicate capture ids: " + ", ".join(sorted(duplicates)))

    unknown = selected - ids
    if unknown:
        fail(
            "unknown capture id(s) for --only: "
            + ", ".join(sorted(unknown))
            + "; available ids: "
            + ", ".join(sorted(ids))
        )


def build_command(
    entry: dict[str, Any],
    default_watch_frames: int,
    default_poll_every: int,
    trace_rom: Path | None,
    trace_symbols: Path | None,
) -> list[str]:
    cmd = [
        sys.executable,
        str(CAPTURE_HELPER),
        "--watch-frames",
        str(entry.get("watch_frames", default_watch_frames)),
        "--poll-every",
        str(entry.get("poll_every", default_poll_every)),
        "--boss",
        entry["boss"],
        "--notes",
        entry["notes"],
        "--out",
        str(rel_or_abs(entry["out"])),
    ]
    if trace_rom is not None:
        cmd.extend(["--rom", str(trace_rom)])
    if trace_symbols is not None:
        cmd.extend(["--symbols", str(trace_symbols)])
    save_state = entry.get("save_state", "")
    if save_state:
        cmd.extend(["--save-state", str(rel_or_abs(save_state))])
    return cmd


def command_for_display(cmd: list[str]) -> str:
    return " ".join(f'"{part}"' if " " in part else part for part in cmd)


def build_state_probe_command(
    entry: dict[str, Any],
    save_state: Path,
    trace_rom: Path | None,
    trace_symbols: Path | None,
) -> list[str] | None:
    preflight = entry.get("preflight")
    if preflight is None:
        return None
    if not isinstance(preflight, dict):
        fail(f"capture {entry['id']}: `preflight` must be an object")
    expect = preflight.get("expect")
    flag = PREFLIGHT_EXPECT_FLAGS.get(str(expect))
    if flag is None:
        fail(f"capture {entry['id']}: unsupported preflight expectation `{expect}`")

    cmd = [
        sys.executable,
        str(STATE_PROBE),
        "--save-state",
        str(save_state),
        flag,
        "--strict",
    ]
    if trace_rom is not None:
        cmd.extend(["--rom", str(trace_rom)])
    if trace_symbols is not None:
        cmd.extend(["--symbols", str(trace_symbols)])
    return cmd


def print_probe_failure(probe_cmd: list[str], proc: subprocess.CompletedProcess[str]) -> None:
    print(f"  probe: {command_for_display(probe_cmd)}")
    output = (proc.stdout or "").strip()
    error = (proc.stderr or "").strip()
    if output:
        print("  probe stdout:")
        for line in output.splitlines():
            print(f"    {line}")
    if error:
        print("  probe stderr:")
        for line in error.splitlines():
            print(f"    {line}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Boss AI trace captures from a manifest.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--execute", action="store_true", help="run captures with existing save-states")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="fail if any manifest entry lacks a save-state or has an invalid preflight",
    )
    parser.add_argument("--only", action="append", default=[], help="capture id to include; may be repeated")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    default_watch_frames = as_int(manifest, "default_watch_frames", 600)
    default_poll_every = as_int(manifest, "default_poll_every", 1)
    trace_rom = validate_manifest_hash(manifest, "trace_rom", "trace_rom_sha256")
    trace_symbols = validate_manifest_hash(
        manifest,
        "trace_symbols",
        "trace_symbols_sha256",
    )
    captures = manifest["captures"]

    selected = set(args.only)
    validate_capture_ids(captures, selected)
    ran = 0
    skipped = 0
    missing_state = 0
    invalid_state = 0

    for index, raw_entry in enumerate(captures, start=1):
        assert isinstance(raw_entry, dict)
        entry: dict[str, Any] = raw_entry
        if selected and entry["id"] not in selected:
            continue

        save_state_text = entry.get("save_state", "")
        save_state = rel_or_abs(save_state_text) if save_state_text else None
        state_exists = bool(save_state and save_state.exists())
        cmd = build_command(
            entry,
            default_watch_frames,
            default_poll_every,
            trace_rom,
            trace_symbols,
        )

        if not state_exists:
            missing_state += 1
            status = "MISSING_STATE"
            print(f"{entry['id']}: {status} {command_for_display(cmd)}")
            if args.strict:
                fail(f"{entry['id']}: missing save-state")
            skipped += 1
            continue

        assert save_state is not None
        probe_cmd = build_state_probe_command(entry, save_state, trace_rom, trace_symbols)
        if probe_cmd is not None:
            proc = subprocess.run(
                probe_cmd,
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if proc.returncode != 0:
                invalid_state += 1
                print(f"{entry['id']}: INVALID_STATE {command_for_display(cmd)}")
                print_probe_failure(probe_cmd, proc)
                if args.strict or args.execute:
                    fail(f"{entry['id']}: state probe failed")
                skipped += 1
                continue

        if not args.execute:
            print(f"{entry['id']}: READY {command_for_display(cmd)}")
            skipped += 1
            continue

        print(f"{entry['id']}: RUN {command_for_display(cmd)}")
        subprocess.run(cmd, cwd=ROOT, check=True)
        ran += 1

    print(
        f"summary: ran={ran} skipped={skipped} "
        f"missing_state={missing_state} invalid_state={invalid_state}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
