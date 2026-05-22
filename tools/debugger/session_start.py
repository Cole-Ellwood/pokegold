"""Read-only session-orientation snapshot for the unified debugger.

Single-command summary so a fresh Claude/Codex session can orient in
seconds without learning every subsystem CLI. Composes existing v2
surfaces — selftest, hypothesis tracker, git log — into a bounded
readout.

Acceptance contract (Codex + Claude pair, 2026-05-21)
-----------------------------------------------------

- Single command, read-only — never writes to repo state.
- Bounded output — caps on every dynamic section so a long-running
  repo doesn't dump thousands of paths.
- Exits nonzero ONLY when the selftest health gate fails. Open
  hypotheses or a dirty working tree are informational signals and
  do NOT raise the exit code.

CLI: ``python -m tools.debugger.session_start`` and the top-level
``python -m tools.debugger session-start`` passthrough.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .catalog import ROOT


MAX_HYPOTHESES = 5
MAX_COMMITS = 3
RECOMMENDED_COMMANDS = (
    "python -m tools.debugger.selftest",
    "python -m tools.debugger triage --symptom \"<plain English>\"",
    "python -m tools.debugger hypothesis list --refresh-citations",
)


@dataclass
class WorkingTreeSummary:
    tracked_modified: int
    tracked_added: int
    tracked_deleted: int
    untracked: int

    def to_jsonable(self) -> dict[str, int]:
        return {
            "tracked_modified": self.tracked_modified,
            "tracked_added": self.tracked_added,
            "tracked_deleted": self.tracked_deleted,
            "untracked": self.untracked,
        }


@dataclass
class SessionStartReport:
    selftest_ok: bool
    selftest_components_failed: list[str]
    selftest_summary_line: str
    active_probe_count: int
    probe_store: str
    open_hypotheses: list[dict[str, Any]]
    open_hypothesis_count: int  # may exceed len(open_hypotheses) due to MAX_HYPOTHESES cap
    stale_citation_count: int
    latest_commits: list[str]
    working_tree: WorkingTreeSummary
    git_branch: str

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "selftest_ok": self.selftest_ok,
            "selftest_components_failed": list(self.selftest_components_failed),
            "selftest_summary_line": self.selftest_summary_line,
            "active_probe_count": self.active_probe_count,
            "probe_store": self.probe_store,
            "open_hypotheses": list(self.open_hypotheses),
            "open_hypothesis_count": self.open_hypothesis_count,
            "stale_citation_count": self.stale_citation_count,
            "latest_commits": list(self.latest_commits),
            "working_tree": self.working_tree.to_jsonable(),
            "git_branch": self.git_branch,
        }


def build_session_start_report(
    *,
    root: Path = ROOT,
    hypothesis_store: Path | None = None,
) -> SessionStartReport:
    # Selftest health gate.
    from .selftest import run_selftest as _run_selftest

    selftest = _run_selftest(root=root)
    failed_names = [r.component for r in selftest.results if not r.ok]
    summary = (
        f"selftest {'PASS' if selftest.ok else 'FAIL'} "
        f"({len(selftest.results) - len(failed_names)}/{len(selftest.results)} components healthy)"
    )

    # Open hypotheses with citation drift refresh.
    from .hypothesis_tracker import list_hypotheses as _list_hypotheses

    all_open = _list_hypotheses(
        root=root,
        status="open",
        refresh_citations=True,
        store=hypothesis_store,
    )
    stale_count = sum(1 for h in all_open if h.get("citation_stale"))
    bounded_open = all_open[-MAX_HYPOTHESES:]
    active_probe_count, probe_store = _active_probe_summary(root)

    commits = _git_oneline(root, MAX_COMMITS)
    branch = _git_branch(root)
    tree = _working_tree_summary(root)

    return SessionStartReport(
        selftest_ok=selftest.ok,
        selftest_components_failed=failed_names,
        selftest_summary_line=summary,
        active_probe_count=active_probe_count,
        probe_store=probe_store,
        open_hypotheses=[
            {
                "id": h["id"],
                "symptom": h.get("symptom", ""),
                "claim": h.get("claim", ""),
                "confidence": h.get("confidence", ""),
                "citation_stale": bool(h.get("citation_stale")),
            }
            for h in bounded_open
        ],
        open_hypothesis_count=len(all_open),
        stale_citation_count=stale_count,
        latest_commits=commits,
        working_tree=tree,
        git_branch=branch,
    )


def _git_oneline(root: Path, n: int) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "log", "--oneline", f"-{n}"],
            cwd=str(root),
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [line.rstrip() for line in out.splitlines() if line.strip()]


def _git_branch(root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(root),
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _working_tree_summary(root: Path) -> WorkingTreeSummary:
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(root),
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return WorkingTreeSummary(0, 0, 0, 0)
    modified = added = deleted = untracked = 0
    for line in out.splitlines():
        if len(line) < 2:
            continue
        prefix = line[:2]
        if prefix == "??":
            untracked += 1
            continue
        # Index status (first char) + worktree status (second char).
        # Count the strongest signal — modified beats added beats deleted —
        # so a file modified in both index and worktree counts once.
        if "M" in prefix:
            modified += 1
        elif "A" in prefix:
            added += 1
        elif "D" in prefix:
            deleted += 1
    return WorkingTreeSummary(modified, added, deleted, untracked)


def _active_probe_summary(root: Path) -> tuple[int, str]:
    from .probe import build_probe_list_report

    report = build_probe_list_report(root=root)
    return int(report.get("active_probe_count", 0)), str(report.get("store", ""))


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


def _format_text(report: SessionStartReport) -> str:
    lines: list[str] = [
        "Pokemon Gold romhack debugger — session orientation",
        "",
        f"branch: {report.git_branch or '(detached or no-git)'}",
        "",
        report.selftest_summary_line,
    ]
    if report.selftest_components_failed:
        for name in report.selftest_components_failed:
            lines.append(f"  FAIL: {name}")
        lines.append("")
        lines.append("Selftest failed — fix named component(s) before deeper debugging:")
        lines.append("  python -m tools.debugger.selftest")
    lines.append("")
    lines.append(
        f"open hypotheses: {report.open_hypothesis_count} "
        f"(stale citations: {report.stale_citation_count})"
    )
    if report.open_hypotheses:
        for h in report.open_hypotheses:
            stale = " [STALE-CITE]" if h["citation_stale"] else ""
            symptom = _truncate(h["symptom"] or "(no symptom)", 60)
            lines.append(f"  - {h['id']} [{h['confidence']}]{stale}  {symptom}")
        hidden = report.open_hypothesis_count - len(report.open_hypotheses)
        if hidden > 0:
            lines.append(
                f"  ... (+{hidden} older — `python -m tools.debugger hypothesis list`)"
            )
    lines.append("")
    lines.append(f"active probes: {report.active_probe_count}")
    if report.probe_store:
        lines.append(f"probe store: {report.probe_store}")
    lines.append("")
    lines.append(f"recent commits ({len(report.latest_commits)}):")
    if report.latest_commits:
        for commit_line in report.latest_commits:
            lines.append(f"  {commit_line}")
    else:
        lines.append("  (no commits / not a git repo)")
    lines.append("")
    tree = report.working_tree
    lines.append(
        "working tree: "
        f"modified={tree.tracked_modified}, "
        f"added={tree.tracked_added}, "
        f"deleted={tree.tracked_deleted}, "
        f"untracked={tree.untracked}"
    )
    lines.append("")
    lines.append("first recommended commands:")
    for cmd in RECOMMENDED_COMMANDS:
        lines.append(f"  {cmd}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger.session_start",
        description=(
            "Read-only session-orientation snapshot. Composes selftest + "
            "open hypotheses + recent commits + working-tree summary into "
            "one bounded readout. Exits nonzero ONLY if the selftest health "
            "gate fails."
        ),
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = build_session_start_report()
    if args.json:
        print(json.dumps(report.to_jsonable(), sort_keys=True))
    else:
        print(_format_text(report))
    return 0 if report.selftest_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
