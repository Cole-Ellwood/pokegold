#!/usr/bin/env python3
"""PreToolUse: block Edit/Write/MultiEdit when target file wasn't Read.

Reads a Claude Code PreToolUse JSON event from stdin. Extracts
`tool_name`, `tool_input.file_path`, and `transcript_path`. For an
existing target file, scans the transcript for a prior Read (or Write/
Edit/MultiEdit) call on the same path. For a new file (path does not
exist yet), accepts any prior Grep or Glob call as evidence that the
caller looked around before creating. On miss, prints the spec block
message to stderr and exits 1.

Exit codes: 0 allow, 1 block.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


BLOCK_MSG = (
    "Blocked: read {path} with Read before editing. "
    "For new files, run rg for existing helpers/patterns nearby before "
    "writing. Then retry."
)

GUARDED = frozenset({"Edit", "Write", "MultiEdit"})
KNOWS_CONTENT = frozenset({"Read", "Edit", "Write", "MultiEdit"})
SEARCH = frozenset({"Grep", "Glob"})


def normalize(p: str) -> str:
    if not p:
        return ""
    try:
        return str(Path(p).resolve()).lower().replace("\\", "/")
    except OSError:
        return p.lower().replace("\\", "/")


def iter_tool_uses(transcript: Path):
    try:
        handle = transcript.open("r", encoding="utf-8")
    except (OSError, FileNotFoundError):
        return
    with handle as stream:
        for raw in stream:
            raw = raw.strip()
            if not raw:
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            msg = event.get("message") if isinstance(event, dict) else None
            if not isinstance(msg, dict):
                continue
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") != "tool_use":
                    continue
                yield item.get("name", ""), item.get("input", {})


def target_known(transcript: Path, target: str) -> bool:
    target_norm = normalize(target)
    if not target_norm:
        return False
    for name, inp in iter_tool_uses(transcript):
        if name not in KNOWS_CONTENT:
            continue
        if not isinstance(inp, dict):
            continue
        candidate = inp.get("file_path", "")
        if normalize(candidate) == target_norm:
            return True
    return False


def search_seen(transcript: Path) -> bool:
    for name, _ in iter_tool_uses(transcript):
        if name in SEARCH:
            return True
    return False


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if not isinstance(event, dict):
        return 0
    tool_name = event.get("tool_name", "")
    if tool_name not in GUARDED:
        return 0
    tool_input = event.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return 0
    file_path = tool_input.get("file_path", "")
    if not file_path:
        return 0
    transcript_raw = event.get("transcript_path", "")
    if not transcript_raw:
        return 0
    transcript = Path(transcript_raw)

    if Path(file_path).exists():
        if target_known(transcript, file_path):
            return 0
    else:
        if search_seen(transcript):
            return 0

    sys.stderr.write(BLOCK_MSG.format(path=file_path) + "\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
