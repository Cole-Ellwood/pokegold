#!/usr/bin/env python3
"""Check tech_debt/ doc freshness against current source.

The tech_debt/ workstream cites source paths and line numbers in its
immutable docs (TECH_DEBT_REPORT.md, FINDINGS_DETAIL.md). Source moves;
docs don't. This audit catches drift before a fresh agent acts on stale
guidance.

Checks performed (in order):

  1. Folder presence. If tech_debt/ does not exist on this branch, exit
     0 with a skip note — most branches don't have the folder.
  2. File-citation freshness. Every `path/to/file.ext[:line]` reference
     in the immutable docs is checked: file exists, line exists.
  3. STATUS / REPORT consistency. Every TD-### in TECH_DEBT_REPORT.md
     index has a row in STATUS.md; every row in STATUS.md exists in the
     report. No orphans either way.
  4. ADDENDUM coverage. Every TD-### mentioned in
     TECH_DEBT_REPORT_ADDENDUM.md has a corresponding STATUS.md entry
     reflecting the addendum (Notes column should mention "ADDENDUM" or
     similar).
  5. AGENT_LOG terminal-state coverage. Every `blocked` / `done` /
     `accepted` / `disputed` entry in AGENT_LOG.md has a matching
     STATUS.md state.

Exit codes:
  0  no drift, or folder absent
  1  drift detected

Usage: python3 tools/audit/check_tech_debt_freshness.py
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TECH_DEBT = ROOT / "tech_debt"

REPORT = TECH_DEBT / "TECH_DEBT_REPORT.md"
FINDINGS = TECH_DEBT / "FINDINGS_DETAIL.md"
STATUS = TECH_DEBT / "STATUS.md"
ADDENDUM = TECH_DEBT / "TECH_DEBT_REPORT_ADDENDUM.md"
AGENT_LOG = TECH_DEBT / "AGENT_LOG.md"

# Match `path/to/file.ext` and `path/to/file.ext:NN` and `path/to/file.ext:NN-MM`.
# Path components are word chars, dots, dashes, slashes; extension is one of the
# project's source/data/doc extensions. Anchored to common top-level dirs to
# avoid false positives on prose like "5e-08" or "version 1.0".
TOP_DIRS = (
    "engine|home|data|ram|constants|tools|scripts|docs|maps|audio|gfx|"
    "macros|charmap|includes|main|layout|rgbdscheck|hram|wram|sram|"
    "sound|stadium|.github|tech_debt"
)
PATH_RE = re.compile(
    rf"\b((?:{TOP_DIRS})[/\\][\w./\\-]+\.(?:asm|inc|md|py|link|yml|sh|sym|map|json|toml))"
    r"(?::(\d+)(?:-(\d+))?)?\b"
)

TD_RE = re.compile(r"\bTD-(\d{3})\b")
# Match `| TD-NNN | <severity cell> | <state cell> |` — cells may contain
# markdown emphasis (**bold**), asterisks, spaces, etc. Capture raw cell
# content; strip markdown when comparing.
STATUS_ROW_RE = re.compile(
    r"^\|\s*TD-(\d{3})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", re.M
)


def _strip_md(cell: str) -> str:
    """Strip markdown emphasis and trailing footnote asterisks from a cell."""
    cell = cell.strip()
    # Strip surrounding **bold**, *italic*, `code`.
    cell = re.sub(r"^\*+|\*+$", "", cell)
    cell = re.sub(r"^`+|`+$", "", cell)
    return cell.strip()
LOG_HEADER_RE = re.compile(
    r"^##\s+\d{4}-\d{2}-\d{2}.*?—\s+TD-(\d{3})\s+—\s+(\w+)", re.M
)
TERMINAL_STATES = {"done", "blocked", "accepted", "disputed", "partial", "pending-trigger"}


@dataclass
class Drift:
    kind: str  # "missing-file", "line-out-of-range", "orphan-status", etc.
    location: str  # which doc + line/section
    detail: str

    def __str__(self) -> str:
        return f"  [{self.kind}] {self.location}: {self.detail}"


@dataclass
class Report:
    drifts: list[Drift] = field(default_factory=list)
    file_refs_checked: int = 0
    td_ids_in_report: set[str] = field(default_factory=set)
    td_ids_in_status: set[str] = field(default_factory=set)
    td_ids_in_addendum: set[str] = field(default_factory=set)

    def add(self, kind: str, location: str, detail: str) -> None:
        self.drifts.append(Drift(kind, location, detail))


def check_folder_present() -> bool:
    return TECH_DEBT.is_dir() and REPORT.is_file() and FINDINGS.is_file()


def check_file_citations(doc_path: Path, report: Report) -> None:
    """Walk every path-like reference in `doc_path`, verify against ROOT."""
    if not doc_path.exists():
        report.add(
            "missing-doc",
            doc_path.name,
            f"expected at {doc_path}, file not present",
        )
        return

    text = doc_path.read_text(encoding="utf-8", errors="replace")
    seen: set[tuple[str, int | None, int | None]] = set()
    for m in PATH_RE.finditer(text):
        rel_path = m.group(1).replace("\\", "/")
        line_start = int(m.group(2)) if m.group(2) else None
        line_end = int(m.group(3)) if m.group(3) else None
        key = (rel_path, line_start, line_end)
        if key in seen:
            continue
        seen.add(key)

        # Skip references to tech_debt/ files themselves — self-references
        # are common in cross-doc links and don't need source verification.
        if rel_path.startswith("tech_debt/"):
            continue

        # Skip generated docs — they get regenerated and may legitimately
        # have shifted line numbers; freshness here is a category error.
        if rel_path.startswith("docs/generated/"):
            continue

        target = ROOT / rel_path
        report.file_refs_checked += 1

        if not target.exists():
            report.add(
                "missing-file",
                f"{doc_path.name}",
                f"cited path `{rel_path}` does not exist",
            )
            continue

        if line_start is not None:
            try:
                line_count = sum(1 for _ in target.open("rb"))
            except OSError as exc:
                report.add(
                    "unreadable-file",
                    f"{doc_path.name}",
                    f"cannot read `{rel_path}`: {exc}",
                )
                continue
            check_line = line_end if line_end is not None else line_start
            if check_line > line_count:
                report.add(
                    "line-out-of-range",
                    f"{doc_path.name}",
                    f"`{rel_path}:{m.group(0).split(':', 1)[1]}` "
                    f"but file has only {line_count} lines",
                )


def parse_td_ids_from_index(text: str) -> set[str]:
    """Pull TD-### IDs from a markdown table (any context — index, status,
    etc.). Filters TD-A### addenda (which use a different ID space)."""
    return {f"TD-{m.group(1)}" for m in TD_RE.finditer(text)}


def check_status_consistency(report: Report) -> None:
    if not REPORT.exists():
        return
    if not STATUS.exists():
        report.add(
            "missing-doc",
            "STATUS.md",
            "expected projection of AGENT_LOG.md is missing",
        )
        return

    report_text = REPORT.read_text(encoding="utf-8", errors="replace")
    status_text = STATUS.read_text(encoding="utf-8", errors="replace")

    # Parse the index table at the bottom of TECH_DEBT_REPORT.md.
    # Match table rows of the form `| TD-NNN | <sev> | <title> |`.
    report_index = set(
        f"TD-{m.group(1)}"
        for m in re.finditer(r"^\|\s*TD-(\d{3})\s*\|", report_text, re.M)
    )
    status_rows = {
        f"TD-{m.group(1)}": (_strip_md(m.group(2)), _strip_md(m.group(3)))
        for m in STATUS_ROW_RE.finditer(status_text)
    }

    report.td_ids_in_report = report_index
    report.td_ids_in_status = set(status_rows.keys())

    missing_in_status = report_index - report.td_ids_in_status
    for tid in sorted(missing_in_status):
        report.add(
            "orphan-report",
            "TECH_DEBT_REPORT.md",
            f"{tid} appears in report index but not in STATUS.md",
        )

    missing_in_report = report.td_ids_in_status - report_index
    for tid in sorted(missing_in_report):
        report.add(
            "orphan-status",
            "STATUS.md",
            f"{tid} has a row in STATUS.md but not in TECH_DEBT_REPORT.md "
            "(addenda use TD-A###; main IDs must match the report)",
        )


def check_addendum_coverage(report: Report) -> None:
    if not ADDENDUM.exists():
        return
    addendum_text = ADDENDUM.read_text(encoding="utf-8", errors="replace")
    # Find TD-### IDs mentioned in addendum section headers.
    report.td_ids_in_addendum = {
        f"TD-{m.group(1)}"
        for m in re.finditer(
            r"^##\s+\d{4}-\d{2}-\d{2}\s+—\s+TD-(\d{3})\b", addendum_text, re.M
        )
    }

    if not STATUS.exists():
        return
    status_text = STATUS.read_text(encoding="utf-8", errors="replace")

    for tid in sorted(report.td_ids_in_addendum):
        # Each addendum-mentioned TD-### should have STATUS.md row
        # whose Notes column references the addendum.
        row_pattern = re.compile(
            rf"^\|\s*{re.escape(tid)}\s*\|.*?\|.*?\|.*?\|\s*(.*?)\s*\|$",
            re.M,
        )
        m = row_pattern.search(status_text)
        if m is None:
            continue  # already flagged as orphan above
        notes = m.group(1).lower()
        if "addendum" not in notes and "see " not in notes:
            report.add(
                "addendum-uncited",
                "STATUS.md",
                f"{tid} has an ADDENDUM entry but STATUS.md notes don't "
                f"reference it (notes: {notes!r})",
            )


def check_log_terminal_states(report: Report) -> None:
    if not AGENT_LOG.exists() or not STATUS.exists():
        return
    log_text = AGENT_LOG.read_text(encoding="utf-8", errors="replace")
    status_text = STATUS.read_text(encoding="utf-8", errors="replace")

    # Group log entries by TD-###; track most recent terminal state.
    latest_terminal: dict[str, str] = {}
    for m in LOG_HEADER_RE.finditer(log_text):
        tid = f"TD-{m.group(1)}"
        state = m.group(2).lower()
        if state in TERMINAL_STATES:
            latest_terminal[tid] = state

    status_rows = {
        f"TD-{m.group(1)}": _strip_md(m.group(3)).lower()
        for m in STATUS_ROW_RE.finditer(status_text)
    }

    for tid, log_state in latest_terminal.items():
        status_state = status_rows.get(tid)
        if status_state is None:
            continue  # already flagged as orphan
        if status_state != log_state:
            report.add(
                "status-out-of-sync",
                "STATUS.md vs AGENT_LOG.md",
                f"{tid}: AGENT_LOG terminal state is {log_state!r} but "
                f"STATUS.md shows {status_state!r}",
            )


def main() -> int:
    if not check_folder_present():
        print("[skip] tech_debt/ folder not present on this branch — nothing to audit.")
        return 0

    report = Report()

    for doc in (REPORT, FINDINGS):
        check_file_citations(doc, report)

    check_status_consistency(report)
    check_addendum_coverage(report)
    check_log_terminal_states(report)

    if not report.drifts:
        print(
            f"[ok] tech_debt/ docs are fresh: "
            f"{report.file_refs_checked} file refs OK, "
            f"{len(report.td_ids_in_report)} TD-### IDs consistent across "
            f"REPORT/STATUS, "
            f"{len(report.td_ids_in_addendum)} ADDENDUM entries cross-linked."
        )
        return 0

    print(f"[FAIL] tech_debt/ docs have {len(report.drifts)} drift(s):")
    grouped: dict[str, list[Drift]] = defaultdict(list)
    for d in report.drifts:
        grouped[d.kind].append(d)
    for kind in sorted(grouped):
        print(f"\n{kind}:")
        for d in grouped[kind]:
            print(d)
    print(
        "\nFix the underlying source/cite, or update STATUS.md / "
        "FIX_PROPOSALS.md / TECH_DEBT_REPORT_ADDENDUM.md per the workflow. "
        "Do NOT edit TECH_DEBT_REPORT.md or FINDINGS_DETAIL.md."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
