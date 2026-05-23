#!/usr/bin/env python3
"""Audit: every post-roadmap commit on claude/boss-ai-rom-expansion has a
paired slice_review row from the OTHER LLM in the boss-AI handoff log.

Acceptance criterion `no_solo_commits` for the 2026-05-23 boss-AI
ROM-expansion /codex-pgoal. Implements structural defense #2
(feedback_codex_pgoal_structural_defenses.md): "no in-scope commit
without a prior or paired Codex slice_review row."

Algorithm (v1, lenient):
  1. Find the base commit: the most recent commit that introduces or
     last touches `docs/boss_ai_rom_expansion_2026-05-23_codex_task.md`
     WITHOUT also being an implementation commit. Heuristic: the
     first/oldest commit on the branch that touches this file.
     Fallback: read BASE_COMMIT_SHA from this file if heuristic fails.
  2. List all commits on HEAD after the base, in chronological order.
  3. For each commit:
     - Skip if it only touches the roadmap doc, the handoff log, or
       this audit's own scripts (Step-0 setup commits).
     - Otherwise, scan `audit/boss_ai_rom_expansion_2026-05-23_handoff_log.jsonl`
       for a `slice_review` row signed by the OTHER LLM (not the commit
       author) whose `claim`, `reviews`, or `files_changed` field cites
       the commit SHA (any prefix >= 7 chars).
     - If none found, flag as a violation.

Exits 0 if no violations. Exits 1 with violation list otherwise.

Setup-allowlist files (don't require paired review on their own):
  - docs/boss_ai_rom_expansion_2026-05-23_codex_task.md
  - audit/boss_ai_rom_expansion_2026-05-23_handoff_log.jsonl
  - tools/audit/check_boss_ai_phases_locked.py
  - tools/audit/check_no_solo_commits_boss_ai_rom_expansion.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROADMAP_PATH = "docs/boss_ai_rom_expansion_2026-05-23_codex_task.md"
HANDOFF_LOG = Path("audit/boss_ai_rom_expansion_2026-05-23_handoff_log.jsonl")
SETUP_ALLOWLIST = {
    ROADMAP_PATH,
    "audit/boss_ai_rom_expansion_2026-05-23_handoff_log.jsonl",
    "tools/audit/check_boss_ai_phases_locked.py",
    "tools/audit/check_no_solo_commits_boss_ai_rom_expansion.py",
}


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(f"git {args} failed: {result.stderr.strip()}")
    return result.stdout


def find_base_commit() -> str | None:
    """The first commit on HEAD that touches the roadmap (or its ancestor)."""
    out = _git("log", "--reverse", "--format=%H", "--", ROADMAP_PATH).strip().splitlines()
    return out[0] if out else None


def list_post_base_commits(base: str) -> list[tuple[str, str, str]]:
    """Return [(sha, author_email, subject)] for commits in chronological order after base."""
    out = _git("log", "--reverse", "--format=%H%x1f%ae%x1f%s", f"{base}..HEAD")
    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\x1f", 2)
        if len(parts) == 3:
            rows.append((parts[0], parts[1], parts[2]))
    return rows


def commit_only_touches_allowlist(sha: str) -> bool:
    out = _git("diff", "--name-only", f"{sha}^", sha)
    files = [line.strip() for line in out.splitlines() if line.strip()]
    if not files:
        return True
    return all(f in SETUP_ALLOWLIST for f in files)


def commit_author_llm(author_email: str, subject: str) -> str | None:
    """Heuristic: which LLM authored this commit."""
    e = author_email.lower()
    s = subject.lower()
    if "claude" in e or s.startswith("boss-ai:") or s.startswith("debugger:"):
        # boss-ai: / debugger: prefix is Claude's convention on this branch
        return "claude"
    if "codex" in e:
        return "codex"
    # Unknown — treat as claude for safety (Codex commits have explicit codex@local)
    return "claude"


def load_handoff_rows() -> list[dict]:
    if not HANDOFF_LOG.exists():
        return []
    rows = []
    for line in HANDOFF_LOG.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        rows.append(r)
    return rows


def row_cites_sha(row: dict, sha: str) -> bool:
    """Does this handoff row mention the commit SHA (>=7 char prefix) anywhere?"""
    needle = sha[:7]
    haystack_parts = []
    for key in ("claim", "reviews", "summary"):
        val = row.get(key)
        if isinstance(val, str):
            haystack_parts.append(val)
    for key in ("files_changed", "files_read", "verification_replayed", "validation", "evidence", "tests_running"):
        val = row.get(key)
        if isinstance(val, list):
            haystack_parts.extend(str(x) for x in val)
        elif isinstance(val, str):
            haystack_parts.append(val)
    haystack = " ".join(haystack_parts)
    return needle in haystack


def load_slice_reviews(rows: list[dict]) -> list[dict]:
    reviews = []
    for r in rows:
        if r.get("event") != "slice_review":
            continue
        status = r.get("status", "")
        if status not in {"slice_accepted", "approved", "complete"}:
            continue
        reviews.append(r)
    return reviews


def commit_primary_from_handoff(rows: list[dict], sha: str) -> str | None:
    """Prefer explicit paired-log primary when a slice_update cites the SHA."""
    for row in rows:
        if row.get("event") != "slice_update":
            continue
        if not row_cites_sha(row, sha):
            continue
        primary = (row.get("primary") or row.get("model") or "").lower()
        if primary in {"claude", "codex"}:
            return primary
    return None


def review_signer_other_than(review: dict, llm: str) -> bool:
    """The review is signed by an LLM that's NOT `llm`."""
    # masterpiece-log shape uses `model` for signer
    model = (review.get("model") or "").lower()
    if model and model != llm:
        return True
    # canonical helper shape uses `signed_by` list
    signed_by = review.get("signed_by")
    if isinstance(signed_by, list):
        others = [s for s in signed_by if s.lower() != llm]
        if others:
            return True
    return False


def main() -> int:
    base = find_base_commit()
    if base is None:
        print(f"PASS: roadmap {ROADMAP_PATH} not committed yet; nothing to audit")
        return 0

    commits = list_post_base_commits(base)
    if not commits:
        print(f"PASS: no post-roadmap commits on HEAD (base={base[:7]})")
        return 0

    handoff_rows = load_handoff_rows()
    reviews = load_slice_reviews(handoff_rows)

    violations = []
    for sha, author, subject in commits:
        if commit_only_touches_allowlist(sha):
            continue  # setup-allowlist commit, no review needed
        llm = commit_primary_from_handoff(handoff_rows, sha) or commit_author_llm(author, subject)
        # Find a paired slice_review row
        paired = [
            r for r in reviews
            if review_signer_other_than(r, llm) and row_cites_sha(r, sha)
        ]
        if not paired:
            violations.append((sha, llm, subject))

    if violations:
        print(f"FAIL: {len(violations)} commit(s) without paired slice_review:")
        for sha, llm, subject in violations:
            other = "codex" if llm == "claude" else "claude"
            print(f"  - {sha[:7]} ({llm}-authored) — missing {other} slice_review citing this SHA")
            print(f"      subject: {subject[:80]}")
        print("")
        print("Per structural defense #2: every in-scope commit needs a slice_review row from the other LLM citing the commit SHA.")
        return 1

    setup_count = sum(1 for sha, _, _ in commits if commit_only_touches_allowlist(sha))
    audited_count = len(commits) - setup_count
    print(f"PASS: {audited_count} in-scope commit(s) on HEAD past roadmap base, all paired with Codex slice_review")
    print(f"      ({setup_count} setup-allowlist commit(s) skipped as Step-0 sanctioned)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
