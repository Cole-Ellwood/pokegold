"""Haki coverage tool: parse the Haki Per-Leader Roster from docs/boss_ai_spec.md
and surface it for audit and balance review.

Per P0.5c (boss-AI ROM expansion roadmap 2026-05-23): this is the Claude-side
revision of the originally-proposed "Haki playbook tables" lever. The spec
already centralizes Haki via the Oracle pattern + per-leader ace + iconic move
in docs/boss_ai_spec.md. The lever value isn't a new data structure; it's
making the existing roster inspectable for Cole + the pair.

Tool-only, ROM cost 0, WRAMX cost 0.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


SPEC_PATH = Path("docs/boss_ai_spec.md")
ROSTER_HEADER = "### Per-Leader Roster"

EXPECTED_LEADERS_19 = (
    "Morty", "Chuck", "Jasmine", "Pryce", "Clair", "Will", "Koga", "Bruno",
    "Karen", "Lance", "Brock", "Misty", "Lt. Surge", "Erika", "Janine",
    "Sabrina", "Blaine", "Blue", "Red",
)


@dataclass(frozen=True)
class HakiEntry:
    leader: str
    ace_species: str
    ace_level: int
    iconic_move: str


def parse_roster(spec_text: str) -> list[HakiEntry]:
    """Parse the 19-leader Haki roster from a boss_ai_spec.md text body."""
    idx = spec_text.find(ROSTER_HEADER)
    if idx < 0:
        raise ValueError(f'roster header "{ROSTER_HEADER}" not found in spec')
    # Take lines after the header until the next ## or ### or end of file
    remaining = spec_text[idx + len(ROSTER_HEADER):]
    boundary = re.search(r"\n#{2,3} ", remaining)
    body = remaining[: boundary.start()] if boundary else remaining

    entries: list[HakiEntry] = []
    row_re = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*$")
    for line in body.splitlines():
        if not line.startswith("|"):
            continue
        m = row_re.match(line)
        if not m:
            continue
        leader = m.group(1).strip()
        # Skip header row ("Leader | Ace | Ace level | Iconic move on ace")
        # and separator row (|---|---|---|---|).
        if leader.lower() == "leader" or set(leader) <= {"-", " "}:
            continue
        entries.append(
            HakiEntry(
                leader=leader,
                ace_species=m.group(2).strip(),
                ace_level=int(m.group(3)),
                iconic_move=m.group(4).strip(),
            )
        )
    return entries


def run_haki_coverage() -> dict:
    """Return the parsed roster plus a coverage report."""
    if not SPEC_PATH.exists():
        return {"ok": False, "error": f"{SPEC_PATH} not found", "entries": []}
    text = SPEC_PATH.read_text(encoding="utf-8")
    try:
        entries = parse_roster(text)
    except ValueError as exc:
        return {"ok": False, "error": str(exc), "entries": []}
    leaders = [e.leader for e in entries]
    missing = [name for name in EXPECTED_LEADERS_19 if name not in leaders]
    extra = [name for name in leaders if name not in EXPECTED_LEADERS_19]
    return {
        "ok": not missing and not extra and len(entries) == 19,
        "entries": [e.__dict__ for e in entries],
        "count": len(entries),
        "expected_count": 19,
        "missing": missing,
        "extra": extra,
        "spec_path": str(SPEC_PATH),
    }


def format_haki_coverage(report: dict) -> str:
    lines = [f"Haki coverage from {report.get('spec_path', SPEC_PATH)}:"]
    if not report.get("ok") and report.get("error"):
        lines.append(f"  FAIL: {report['error']}")
        return "\n".join(lines)
    lines.append(f"  leaders: {report['count']} (expected {report['expected_count']})")
    if report.get("missing"):
        lines.append(f"  MISSING: {', '.join(report['missing'])}")
    if report.get("extra"):
        lines.append(f"  EXTRA:   {', '.join(report['extra'])}")
    lines.append("")
    lines.append("  Leader        Ace             Lv  Iconic move")
    lines.append("  ------------  --------------  --  ----------------")
    for e in report["entries"]:
        lines.append(
            f"  {e['leader']:<12}  {e['ace_species']:<14}  {e['ace_level']:<2}  {e['iconic_move']}"
        )
    return "\n".join(lines)


def run_self_test() -> int:
    """Self-test: exit 0 iff all 19 expected leaders are present."""
    report = run_haki_coverage()
    print(format_haki_coverage(report))
    if not report.get("ok"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run_self_test())
