#!/usr/bin/env python3
"""SessionStart hook: inject a compact summary + TOC of asm_authoring_guide.md.

The full guide is ~31 KB and exceeds the per-hook additionalContext size
limit (output gets persisted to disk and only a tiny preview reaches the
model). Instead we inject:
  1. A short header explaining how to use the rest.
  2. Section 0 verbatim — the load-bearing rules every session needs.
  3. Section 6 verbatim — the verification floor (audit checklist).
  4. An auto-generated TOC with line ranges so the agent can Read
     specific sections on demand.

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

GUIDE_PATH = Path(__file__).resolve().parent.parent / "docs" / "asm_authoring_guide.md"
GUIDE_REL = "docs/asm_authoring_guide.md"

try:
    text = GUIDE_PATH.read_text(encoding="utf-8")
except FileNotFoundError:
    sys.exit(0)

lines = text.splitlines()


def h2_ranges():
    """Return list of (title, start_idx_0based, end_idx_exclusive_0based)."""
    idx = [i for i, ln in enumerate(lines) if ln.startswith("## ")]
    out = []
    for n, i in enumerate(idx):
        end = idx[n + 1] if n + 1 < len(idx) else len(lines)
        out.append((lines[i][3:].strip(), i, end))
    return out


def find_section(prefix):
    for title, s, e in h2:
        if title.startswith(prefix):
            return title, s, e
    return None


def extract(s, e):
    return "\n".join(lines[s:e]).rstrip()


def build_toc():
    rows = []
    for title, s, e in h2:
        # 1-indexed inclusive line range
        rows.append(f"- §{title} — lines {s + 1}-{e}")
        for j in range(s + 1, e):
            ln = lines[j]
            if ln.startswith("### "):
                sub_end = e
                for k in range(j + 1, e):
                    if lines[k].startswith(("### ", "## ")):
                        sub_end = k
                        break
                rows.append(f"  - {ln[4:].strip()} — lines {j + 1}-{sub_end}")
    return "\n".join(rows)


h2 = h2_ranges()
sec0 = find_section("0)")
sec6 = find_section("6)")

parts = [
    "# Z80 / RGBDS Authoring Guide — session header",
    "",
    f"The full guide ({len(lines)} lines) lives at `{GUIDE_REL}`. Below:",
    "the always-true critical rules (§0), the verification floor (§6),",
    "and a TOC with line ranges for the rest. Read specific sections on",
    "demand with the Read tool (offset = first line, limit = line count)",
    "before writing .asm — don't rely on memory of the guide content.",
    "",
]

if sec0:
    parts.append(extract(sec0[1], sec0[2]))
    parts.append("")
if sec6:
    parts.append(extract(sec6[1], sec6[2]))
    parts.append("")

parts += [
    "## Table of contents",
    "",
    build_toc(),
]

bundled = "\n".join(parts)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": bundled,
    }
}))
