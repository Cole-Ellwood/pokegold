#!/usr/bin/env python3
r"""Audit date-anchored "shipped"/"done"/"fixed" claims in docs against git.

CLAUDE.md and tech_debt docs accumulate claims like "shipped 2026-05-02
(commit `1f5fd6af`)". When the cited commit lives only on a side branch
or got rebased away, the claim becomes doc-fiction — readers (humans and
agents) treat it as ground truth and act on a hallucinated state.

Two repeated incidents drove this audit:
  - 2026-05-03: CLAUDE.md described the wild-level-spread rewrite as
    "shipped 2026-05-02" while it sat uncommitted on a WIP snapshot.
  - 2026-05-03: TD-A13 cross-bank cleanup was prompted as "needs work"
    while already complete on `claude/kind-swanson-ae5a65`.

The audit walks .md files in CLAUDE.md, tech_debt/, docs/ (excluding
generated/), and .claude_handoffs/ (if present), looking for:
  - `(shipped|done|landed|fixed)\s+YYYY-MM-DD`
  - `commit \`?[0-9a-f]{7,40}\`?`
and for each cited commit hash verifies it resolves and is an ancestor
of the dev branch tip.

Output is candidates for human review, NOT auto-fix. False positives are
expected (e.g., a "shipped 2026-04-X" claim citing a function whose name
later got refactored is technically valid, just brittle). The audit's job
is to surface; you decide whether to re-cherry-pick, edit the claim, or
strip the date anchor.

Silencing legitimate exceptions: drop an HTML comment marker anywhere in
the same markdown block (paragraph/bullet) as the cite:

    <!-- audit:noqa stale-claims — historical session log; canonical SHA on dev is 5e40311c -->

The marker silences both date claims and commit references in that block.
Use it for deliberate cross-references to side-branch artifacts and for
historical session logs whose original SHA got rebased away. Always
annotate the marker with the reason and (when known) the new canonical SHA.

Exit codes:
  0 — every cited commit is on dev tip; no future-dated claims
  1 — at least one cited commit is missing from dev or doesn't resolve
"""
from __future__ import annotations

import datetime as _dt
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEV_BRANCH = "codex/cleanup-gsc-rebalance-split"

# Files/dirs to scan, relative to ROOT.
SCAN_TARGETS: tuple[Path, ...] = (
    ROOT / "CLAUDE.md",
    ROOT / "AGENTS.md",
    ROOT / "tech_debt",
    ROOT / "docs",
    ROOT / ".claude_handoffs",
)
# Subpaths under SCAN_TARGETS to skip.
SKIP_PARTS: tuple[str, ...] = (
    "generated",  # docs/generated/* is regenerated, treat as live snapshot
    "EVIDENCE",   # tech_debt/EVIDENCE/* is captured tool output
)

DATE_CLAIM_RE = re.compile(
    r"\b(?P<verb>shipped|done|landed|fixed)\s+(?P<date>\d{4}-\d{2}-\d{2})\b",
    re.IGNORECASE,
)
COMMIT_REF_RE = re.compile(r"\bcommit\s+`?(?P<hash>[0-9a-f]{7,40})`?")
# Inline exemption: drop in `<!-- audit:noqa stale-claims -->` (or just
# `audit:noqa`) on the flagged line OR the line immediately before. Use this
# for deliberate cross-references to side branches and historical session
# logs whose commit hashes got rebased under a different SHA. Annotate with
# the new SHA when known.
NOQA_RE = re.compile(r"audit:noqa(?:\s+stale-claims)?\b", re.IGNORECASE)


@dataclass
class Finding:
    path: Path
    lineno: int
    line: str
    kind: str           # "missing-commit", "stale-commit", "future-date"
    detail: str         # cited hash / date
    explanation: str    # human-readable reason


def _run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _resolve_dev_tip() -> str:
    proc = _run_git("rev-parse", "--verify", f"{DEV_BRANCH}^{{commit}}")
    if proc.returncode != 0:
        # Fall back to origin/<dev> if local ref isn't checked out.
        proc = _run_git("rev-parse", "--verify", f"origin/{DEV_BRANCH}^{{commit}}")
    if proc.returncode != 0:
        print(
            f"FAIL: cannot resolve dev branch tip ({DEV_BRANCH}). "
            f"git stderr: {proc.stderr.strip()}",
            file=sys.stderr,
        )
        sys.exit(1)
    return proc.stdout.strip()


def _commit_resolves(sha: str) -> bool:
    return _run_git("rev-parse", "--verify", f"{sha}^{{commit}}").returncode == 0


def _is_ancestor_of(sha: str, tip: str) -> bool:
    return _run_git("merge-base", "--is-ancestor", sha, tip).returncode == 0


def _iter_md_files() -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for target in SCAN_TARGETS:
        if not target.exists():
            continue
        if target.is_file():
            if target.suffix.lower() == ".md" and target not in seen:
                files.append(target)
                seen.add(target)
            continue
        for p in target.rglob("*.md"):
            rel_parts = p.relative_to(ROOT).parts
            if any(part in SKIP_PARTS for part in rel_parts):
                continue
            if p in seen:
                continue
            files.append(p)
            seen.add(p)
    return sorted(files)


def _today() -> _dt.date:
    return _dt.date.today()


def _parse_iso_date(text: str) -> _dt.date | None:
    try:
        return _dt.date.fromisoformat(text)
    except ValueError:
        return None


def _noqa_in_block(lines: list[str], lineno: int) -> bool:
    """An audit:noqa marker silences any cite inside the same markdown block
    (paragraph/bullet), defined as the run of non-blank lines containing
    `lineno`. This handles multi-line bullets where the marker is at the
    bottom of the bullet and the cite is several lines up."""
    idx = lineno - 1  # to 0-based
    if idx < 0 or idx >= len(lines):
        return False
    start = idx
    while start > 0 and lines[start - 1].strip():
        start -= 1
    end = idx
    while end + 1 < len(lines) and lines[end + 1].strip():
        end += 1
    for i in range(start, end + 1):
        if NOQA_RE.search(lines[i]):
            return True
    return False


def _excerpt(line: str, limit: int = 120) -> str:
    s = line.strip()
    if len(s) <= limit:
        return s
    return s[: limit - 1] + "…"


def scan(files: list[Path], dev_tip: str, today: _dt.date) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"WARN: could not read {path}: {exc}", file=sys.stderr)
            continue
        lines = text.splitlines()
        for lineno, line in enumerate(lines, 1):
            if _noqa_in_block(lines, lineno):
                continue
            for m in DATE_CLAIM_RE.finditer(line):
                claim_date = _parse_iso_date(m["date"])
                if claim_date is None:
                    continue
                if claim_date > today:
                    findings.append(
                        Finding(
                            path=path,
                            lineno=lineno,
                            line=_excerpt(line),
                            kind="future-date",
                            detail=m["date"],
                            explanation=(
                                f"claim is dated {m['date']} but today is "
                                f"{today.isoformat()} — typo or placeholder?"
                            ),
                        )
                    )
            for m in COMMIT_REF_RE.finditer(line):
                sha = m["hash"]
                if not _commit_resolves(sha):
                    findings.append(
                        Finding(
                            path=path,
                            lineno=lineno,
                            line=_excerpt(line),
                            kind="missing-commit",
                            detail=sha,
                            explanation=(
                                f"cited commit {sha} does not resolve in this "
                                f"repo — was it rebased away or never pushed?"
                            ),
                        )
                    )
                    continue
                if not _is_ancestor_of(sha, dev_tip):
                    findings.append(
                        Finding(
                            path=path,
                            lineno=lineno,
                            line=_excerpt(line),
                            kind="stale-commit",
                            detail=sha,
                            explanation=(
                                f"cited commit {sha} is NOT an ancestor of "
                                f"{DEV_BRANCH} tip — lives on a side "
                                f"branch only?"
                            ),
                        )
                    )
    return findings


def main() -> int:
    dev_tip = _resolve_dev_tip()
    today = _today()
    files = _iter_md_files()
    findings = scan(files, dev_tip, today)

    if not findings:
        print(f"PASS: no stale shipped/done claims found.")
        print(f"  scanned {len(files)} .md files")
        print(f"  dev tip: {dev_tip[:12]} ({DEV_BRANCH})")
        return 0

    hard_fails = [f for f in findings if f.kind in ("missing-commit", "stale-commit")]
    soft_warns = [f for f in findings if f.kind == "future-date"]

    print("Stale shipped-claims audit findings.")
    print(f"  scanned {len(files)} .md files; dev tip: {dev_tip[:12]}")
    print(
        f"  {len(hard_fails)} cited-commit failure(s), {len(soft_warns)} future-date warning(s)"
    )
    print()
    print("These are candidates for human review, not auto-fix targets.")
    print("False positives possible: e.g., a function name later refactored or")
    print("cherry-picked under a different commit hash. Verify each before editing.")
    print()

    by_file: dict[Path, list[Finding]] = {}
    for f in findings:
        by_file.setdefault(f.path, []).append(f)
    for path in sorted(by_file):
        rel = path.relative_to(ROOT)
        for f in by_file[path]:
            tag = {"missing-commit": "FAIL", "stale-commit": "FAIL", "future-date": "WARN"}[f.kind]
            print(f"  [{tag}] {rel}:{f.lineno}  {f.kind} ({f.detail})")
            print(f"         line: {f.line}")
            print(f"         {f.explanation}")
            print()

    if hard_fails:
        print(
            f"FAIL: {len(hard_fails)} commit reference(s) cite work not on "
            f"{DEV_BRANCH} tip."
        )
        return 1
    print(f"PASS (with {len(soft_warns)} warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
