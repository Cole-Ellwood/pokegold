#!/usr/bin/env python3
"""Check that the boss-AI ROM-expansion roadmap has a non-stub locked-phases section.

Acceptance criterion `phase_a_locked` for the 2026-05-23 boss-AI ROM-expansion
/codex-pgoal. Passes iff:

  1. `docs/boss_ai_rom_expansion_2026-05-23_codex_task.md` exists.
  2. It contains the `## Implementation phases (locked)` H2 header.
  3. The section body (until next H2 or EOF) does NOT contain the
     `STATUS: empty` placeholder marker that ships with the initial
     roadmap commit.
  4. The section body has at least 200 non-whitespace characters of
     concrete phase content.

Fails fast with exit 1 on any of the above. Prints PASS/FAIL summary
to stdout for pgoal verifier capture.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROADMAP = Path("docs/boss_ai_rom_expansion_2026-05-23_codex_task.md")
HEADER = "## Implementation phases (locked)"
# Boundary form matches the section header only, not inline mentions
# of the same text inside paragraphs (e.g. "...produces **'## Implementation phases (locked)'** with...").
HEADER_BOUNDED = "\n" + HEADER + "\n"
STUB_MARKER = "STATUS: empty"
MIN_BODY_CHARS = 200


def main() -> int:
    if not ROADMAP.exists():
        print(f"FAIL: roadmap not found at {ROADMAP}")
        return 1

    text = ROADMAP.read_text(encoding="utf-8")
    # Find the actual section header (preceded and followed by newlines).
    # If the file ends without a trailing newline on the header, fall back
    # to a less strict match (start-of-string or after newline + header at
    # end of string).
    idx = text.find(HEADER_BOUNDED)
    if idx < 0:
        # Tolerate the section being the last header (no trailing \n).
        if text.startswith(HEADER + "\n"):
            idx = 0
            body_start = len(HEADER) + 1
        elif text.endswith("\n" + HEADER):
            print(f'FAIL: section "{HEADER}" is the file tail with no body')
            return 1
        else:
            print(f'FAIL: section header "{HEADER}" not found (only inline mentions, if any)')
            return 1
    else:
        body_start = idx + len(HEADER_BOUNDED)

    remaining = text[body_start:]
    next_h2 = remaining.find("\n## ")
    body = remaining[:next_h2] if next_h2 >= 0 else remaining

    if STUB_MARKER in body:
        print(f'FAIL: section still contains "{STUB_MARKER}" placeholder; Phase A.3 not done')
        return 1

    stripped_chars = len(body.strip())
    if stripped_chars < MIN_BODY_CHARS:
        print(
            f"FAIL: section body too short ({stripped_chars} chars, need >={MIN_BODY_CHARS}); "
            "needs concrete phase definitions"
        )
        return 1

    print(f"PASS: Implementation phases section has {stripped_chars} chars of content; no stub marker")
    return 0


if __name__ == "__main__":
    sys.exit(main())
