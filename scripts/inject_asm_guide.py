#!/usr/bin/env python3
"""SessionStart hook: inject docs/asm_authoring_guide.md into model context.

Wired up via .claude/settings.json. Outputs a SessionStart hook JSON
envelope on stdout; Claude Code reads that and prepends additionalContext
to the session.

If the guide file is missing (e.g., the hook was inherited on a branch
that hasn't merged the guide yet), exit silently — no-op rather than
break the session.
"""
import json
import sys
from pathlib import Path

GUIDE = Path(__file__).resolve().parent.parent / "docs" / "asm_authoring_guide.md"

try:
    text = GUIDE.read_text(encoding="utf-8")
except FileNotFoundError:
    sys.exit(0)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": text,
    }
}))
