#!/usr/bin/env python3
"""Run Boss AI live trace captures from a manifest."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "audit" / "boss_ai_trace" / "live_capture_manifest.json"
CAPTURE_HELPER = ROOT / "tools" / "trace" / "boss_ai_trace_capture.py"
ALLOWED_STATUSES = {"FINISHED", "IN PROGRESS", "UNTOUCHED"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def rel_or_abs(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


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


def build_command(
    entry: dict[str, Any],
    default_watch_frames: int,
    default_poll_every: int,
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
    save_state = entry.get("save_state", "")
    if save_state:
        cmd.extend(["--save-state", str(rel_or_abs(save_state))])
    return cmd


def command_for_display(cmd: list[str]) -> str:
    return " ".join(f'"{part}"' if " " in part else part for part in cmd)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Boss AI trace captures from a manifest.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--execute", action="store_true", help="run captures with existing save-states")
    parser.add_argument("--strict", action="store_true", help="fail if any manifest entry lacks a save-state")
    parser.add_argument("--only", action="append", default=[], help="capture id to include; may be repeated")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    default_watch_frames = as_int(manifest, "default_watch_frames", 600)
    default_poll_every = as_int(manifest, "default_poll_every", 1)
    captures = manifest["captures"]

    selected = set(args.only)
    ran = 0
    skipped = 0
    missing_state = 0

    for index, raw_entry in enumerate(captures, start=1):
        if not isinstance(raw_entry, dict):
            fail(f"capture #{index}: entry must be an object")
        validate_capture(raw_entry, index)
        entry: dict[str, Any] = raw_entry
        if selected and entry["id"] not in selected:
            continue

        save_state_text = entry.get("save_state", "")
        save_state = rel_or_abs(save_state_text) if save_state_text else None
        state_exists = bool(save_state and save_state.exists())
        cmd = build_command(entry, default_watch_frames, default_poll_every)

        if not state_exists:
            missing_state += 1
            status = "MISSING_STATE"
            print(f"{entry['id']}: {status} {command_for_display(cmd)}")
            if args.strict:
                fail(f"{entry['id']}: missing save-state")
            skipped += 1
            continue

        if not args.execute:
            print(f"{entry['id']}: READY {command_for_display(cmd)}")
            skipped += 1
            continue

        print(f"{entry['id']}: RUN {command_for_display(cmd)}")
        subprocess.run(cmd, cwd=ROOT, check=True)
        ran += 1

    print(f"summary: ran={ran} skipped={skipped} missing_state={missing_state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
