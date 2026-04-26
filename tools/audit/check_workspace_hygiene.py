#!/usr/bin/env python3
"""Summarize ignored workspace clutter without deleting anything."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Bucket:
    name: str
    description: str
    tracked_artifact: bool = False


BUCKETS = (
    Bucket("rom-linker-outputs", "Root ROMs plus .map/.sym linker truth.", True),
    Bucket("object-outputs", "RGBDS intermediate .o files.", True),
    Bucket(
        "generated-graphics",
        "Generated gfx/*.1bpp/*.2bpp/*.lz/*.gbcpal/*.dimensions files.",
    ),
    Bucket("tool-binaries", "Compiled helper binaries under tools/."),
    Bucket("toolchain-downloads", "Repo-local RGBDS binaries or downloaded archives."),
    Bucket("python-caches", "Python __pycache__ or .pyc output."),
    Bucket(
        "local-scratch",
        ".local investigation, temporary, dependency, or probe output.",
        True,
    ),
    Bucket("workspace-scratch", "workspace/ scratch or archived local work.", True),
    Bucket("release-artifacts", "dist/ outputs.", True),
    Bucket("emulator-state", "Save/state files from emulator runs.", True),
    Bucket("patch-outputs", "Patch artifacts.", True),
    Bucket("other-ignored", "Ignored files that do not match a known family yet."),
)

TRACKED_ARTIFACT_BUCKETS = {
    bucket.name for bucket in BUCKETS if bucket.tracked_artifact
}


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def clean_ignored_paths() -> list[str]:
    result = run_git(["clean", "-ndX"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git clean -ndX failed")

    paths: list[str] = []
    for line in result.stdout.splitlines():
        if line.startswith("Would remove "):
            paths.append(line.removeprefix("Would remove ").replace("\\", "/"))
    return paths


def root_file(path: str) -> bool:
    return "/" not in path.strip("/")


def generated_graphic(path: str) -> bool:
    return path.startswith("gfx/") and (
        path.endswith(".1bpp")
        or path.endswith(".2bpp")
        or path.endswith(".lz")
        or path.endswith(".gbcpal")
        or path.endswith(".dimensions")
        or path.endswith(".sgb.tilemap")
    )


def tool_binary(path: str) -> bool:
    if not path.startswith("tools/"):
        return False
    leaf = Path(path).name
    return leaf.endswith(".exe") or leaf in {
        "gbcpal",
        "gfx",
        "lzcomp",
        "make_patch",
        "png_dimensions",
        "scan_includes",
        "stadium",
    }


def classify(path: str) -> str:
    clean = path.rstrip("/")

    if clean == ".local" or clean.startswith(".local/"):
        return "local-scratch"
    if clean == "workspace" or clean.startswith("workspace/"):
        return "workspace-scratch"
    if clean == "dist" or clean.startswith("dist/"):
        return "release-artifacts"
    if (
        "__pycache__" in clean
        or clean.endswith(".pyc")
        or clean == "tools/balance_editor"
        or clean.startswith("tools/balance_editor/")
    ):
        return "python-caches"
    if clean == "rgbds-1.0.1" or clean.startswith("rgbds-") or clean.endswith(".zip"):
        return "toolchain-downloads"
    if generated_graphic(clean):
        return "generated-graphics"
    if tool_binary(clean):
        return "tool-binaries"
    if clean.endswith(".o"):
        return "object-outputs"
    if root_file(clean) and re.match(
        r"^poke(?:gold|silver)(?:_debug|_trace)?\.(?:gbc|map|sym)$", clean
    ):
        return "rom-linker-outputs"
    if clean.endswith((".sav", ".rtc", ".state", ".sgm", ".sn1", ".sa1")):
        return "emulator-state"
    if clean.endswith(".patch"):
        return "patch-outputs"
    return "other-ignored"


def short_status_lines() -> list[str]:
    result = run_git(["status", "--short", "--branch"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git status failed")
    return result.stdout.splitlines()


def unignored_untracked_lines() -> list[str]:
    result = run_git(["ls-files", "--others", "--exclude-standard"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git ls-files failed")
    return result.stdout.splitlines()


def tracked_artifact_paths() -> list[str]:
    result = run_git(["ls-files"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git ls-files failed")
    return [
        path
        for path in result.stdout.splitlines()
        if classify(path) in TRACKED_ARTIFACT_BUCKETS
    ]


def group_by_bucket(paths: list[str]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = defaultdict(list)
    for path in paths:
        buckets[classify(path)].append(path)
    return buckets


def print_samples(paths: list[str], limit: int) -> None:
    for path in paths[:limit]:
        print(f"      - {path}")
    if len(paths) > limit:
        print(f"      - ... {len(paths) - limit} more")


def print_bucket_report(
    title: str,
    paths: list[str],
    sample_limit: int,
) -> dict[str, list[str]]:
    print(f"{title}: {len(paths)}")
    buckets = group_by_bucket(paths)
    for bucket in BUCKETS:
        bucket_paths = buckets.get(bucket.name, [])
        if not bucket_paths:
            continue
        print(f"  {bucket.name}: {len(bucket_paths)}")
        print(f"    {bucket.description}")
        print_samples(bucket_paths, sample_limit)
    return buckets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize ignored repo clutter using read-only git commands."
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=4,
        help="number of sample paths to print per family",
    )
    args = parser.parse_args(argv)

    try:
        status = short_status_lines()
        unignored = unignored_untracked_lines()
        ignored = clean_ignored_paths()
        tracked_artifacts = tracked_artifact_paths()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("Workspace hygiene summary")
    print("=========================")
    print("Read-only: used git status, git ls-files, and git clean -ndX.")
    print()

    branch = status[0] if status else "## unknown"
    dirty = status[1:]
    print(f"Branch: {branch}")
    print(f"Tracked source status: {'clean' if not dirty else 'dirty'}")
    if dirty:
        print("Tracked changes:")
        for line in dirty:
            print(f"  {line}")
    print(f"Unignored untracked files: {len(unignored)}")
    if unignored:
        print_samples(unignored, args.samples)

    print_bucket_report("Tracked artifact/scratch paths", tracked_artifacts, args.samples)

    print()
    ignored_buckets = print_bucket_report(
        "Ignored cleanup candidates from dry run",
        ignored,
        args.samples,
    )

    unknown = ignored_buckets.get("other-ignored", [])
    if unknown:
        print()
        print("Review other-ignored paths before treating the clutter map as complete.")

    print()
    print("No files were deleted or moved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
