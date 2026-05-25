#!/usr/bin/env python3
"""Audit paired-review coverage for claude/debugger-godmode commits.

The debugger-godmode roadmap requires that every commit on
``claude/debugger-godmode`` after ``claude/boss-ai-rom-expansion`` that
touches the omni-debugger workstream has a paired handoff-log phase: one
model starts the slice and the other model accepts it with repo-proven
review evidence. This script enforces that structural defense without
assuming every commit subject maps perfectly to a phase name.

Scope: a commit is audited only when it touches a path under
``OMNI_DEBUGGER_PATHS`` or the omni-debugger handoff log. Boss-AI perf
cleanups, ROM source edits, and other non-debugger work in ``BASE..HEAD``
are skipped as out-of-scope and reported separately.

For each in-scope commit it gathers candidate phases from:

* JSONL rows added to the handoff log by that commit,
* current handoff rows that cite the commit SHA,
* branch-local subject conventions such as ``iter 4`` and ``roadmap seed``.

A commit passes when any candidate phase has at least one ``ack_start`` row and
one accepted ``slice_review`` row, and the phase contains both ``claude`` and
``codex`` model signatures. Cole-approved solo continuation phases can
instead pass with an explicit ``solo_codex_approved_by_cole`` or
``solo_claude_approved_by_cole`` self-review row.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE = "claude/boss-ai-rom-expansion"
DEFAULT_HEAD = "HEAD"
DEFAULT_HANDOFF_LOG = Path("audit") / "omni_debugger_2026-05-24_handoff_log.jsonl"
EXPECTED_MODELS = {"claude", "codex"}
VALID_EVENTS = {"ack_start", "slice_update", "slice_review", "phase_done"}
ACCEPTED_REVIEW_STATUSES = {"slice_accepted", "phase_complete", "approved", "complete"}
SOLO_CODEX_APPROVAL_KEY = "solo_codex_approved_by_cole"
SOLO_CLAUDE_APPROVAL_KEY = "solo_claude_approved_by_cole"
# Paths that define the omni-debugger workstream. Commits in BASE..HEAD that
# touch none of these (and add no rows to the handoff log) are out of scope
# for this audit -- e.g. boss-AI perf cleanups, ROM source edits, build/asm
# work. The audit firing on those was a structural false positive and the
# fix is path-scoping, not retroactive paired-review of unrelated work.
OMNI_DEBUGGER_PATHS: tuple[str, ...] = (
    "tools/headless_battle/",
    "tools/debugger/",
    "tools/boss_ai_debugger/",
    "tools/damage_debugger/",
    "tools/trace/",
    "audit/boss_ai_trace/",
    "tools/audit/check_headless_battle_simulator.py",
    "tools/audit/check_two_llm_handoff_log.py",
    "tools/audit/check_no_solo_commits_omni_debugger.py",
    "tools/audit/check_debugger_godmode_benchmark.py",
    "tools/audit/check_debugger_next_coverage.py",
)


@dataclass(frozen=True)
class CommitInfo:
    sha: str
    author_name: str
    author_email: str
    subject: str


@dataclass
class LoadedRows:
    rows: list[dict[str, Any]]
    ignored_rows: list[str]


def repo_rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"FAIL: git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout


def ref_exists(ref: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def list_commits(base: str, head: str) -> list[CommitInfo]:
    out = run_git("log", "--reverse", "--format=%H%x1f%an%x1f%ae%x1f%s", f"{base}..{head}")
    commits: list[CommitInfo] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\x1f", 3)
        if len(parts) != 4:
            continue
        commits.append(CommitInfo(*parts))
    return commits


def load_handoff_rows(path: Path) -> LoadedRows:
    if not path.exists():
        return LoadedRows([], [f"{repo_rel(path)} is missing"])
    rows: list[dict[str, Any]] = []
    ignored: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                ignored.append(f"line {line_no}: invalid JSON ({exc})")
                continue
            if row.get("event") not in VALID_EVENTS:
                ignored.append(f"line {line_no}: ignored non-gate event {row.get('event')!r}")
            rows.append(row)
    return LoadedRows(rows, ignored)


def iter_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(iter_strings(item))
        return out
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(iter_strings(item))
        return out
    return []


def row_cites_sha(row: dict[str, Any], sha: str) -> bool:
    needles = {sha[:length] for length in range(7, min(12, len(sha)) + 1)}
    haystack = " ".join(iter_strings(row))
    return any(needle in haystack for needle in needles)


def added_handoff_rows_for_commit(sha: str, handoff_log: Path) -> list[dict[str, Any]]:
    output = run_git("show", "--format=", "--unified=0", sha, "--", repo_rel(handoff_log))
    rows: list[dict[str, Any]] = []
    for line in output.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        candidate = line[1:].strip()
        if not candidate.startswith("{"):
            continue
        try:
            rows.append(json.loads(candidate))
        except json.JSONDecodeError:
            continue
    return rows


def commit_changed_files(sha: str) -> list[str]:
    output = run_git("diff-tree", "--no-commit-id", "--name-only", "-r", sha)
    return [line.strip() for line in output.splitlines() if line.strip()]


def commit_touches_omni_debugger(sha: str, handoff_log: Path) -> bool:
    files = commit_changed_files(sha)
    handoff_rel = repo_rel(handoff_log)
    for path in files:
        if path == handoff_rel:
            return True
        for prefix in OMNI_DEBUGGER_PATHS:
            if path == prefix.rstrip("/") or path.startswith(prefix):
                return True
    return False


def subject_phase_candidates(subject: str, all_phases: set[str]) -> set[str]:
    subject_lower = subject.lower()
    candidates: set[str] = set()

    if "no-solo" in subject_lower or "no_solo" in subject_lower:
        phase = "iter5_no_solo_commits_audit_codex_lane"
        return {phase} if phase in all_phases else set()

    iter_match = re.search(r"\biter\s*(\d+)\b", subject_lower)
    if iter_match:
        prefix = f"iter{iter_match.group(1)}"
        candidates.update(phase for phase in all_phases if phase.startswith(prefix))
        spaced = f"iter_{iter_match.group(1)}"
        candidates.update(phase for phase in all_phases if spaced in phase)
        if iter_match.group(1) == "1":
            candidates.update(
                phase for phase in all_phases
                if phase in {"debugger_godmode_iter_1", "first_gap_action_proof"}
            )

    if "roadmap" in subject_lower and "handoff" in subject_lower:
        candidates.add("bootstrap")
    if "accept iter 1" in subject_lower or "proof review" in subject_lower:
        candidates.update({"debugger_godmode_iter_1", "first_gap_action_proof"})
    if "benchmark" in subject_lower and "merge" in subject_lower:
        candidates.add("iter3_benchmark_merge")
    if "benchmark scoring harness" in subject_lower:
        candidates.add("iter4_benchmark_harness")
    if "no-solo" in subject_lower or "no_solo" in subject_lower:
        candidates.add("iter5_no_solo_commits_audit_codex_lane")

    return {phase for phase in candidates if phase in all_phases}


def phase_has_pair(rows_by_phase: dict[str, list[dict[str, Any]]], phase: str) -> tuple[bool, str]:
    rows = rows_by_phase.get(phase, [])
    ack_rows = [
        row for row in rows
        if row.get("event") == "ack_start"
        and row.get("status") == "in_progress"
        and row.get("model") in EXPECTED_MODELS
    ]
    review_rows = [
        row for row in rows
        if row.get("event") == "slice_review"
        and row.get("status") in ACCEPTED_REVIEW_STATUSES
        and row.get("confidence") == "repo-proven"
        and row.get("model") in EXPECTED_MODELS
    ]
    if not ack_rows:
        return False, "missing ack_start"
    if not review_rows:
        return False, "missing accepted repo-proven slice_review"

    primary = (ack_rows[-1].get("primary") or ack_rows[-1].get("model") or "").lower()
    solo_codex_signed = (
        primary == "codex"
        and any(
            row.get("model") == "codex"
            and row.get(SOLO_CODEX_APPROVAL_KEY) is True
            for row in review_rows
        )
    )
    if solo_codex_signed:
        return True, "solo_codex_self_review"
    solo_claude_signed = (
        primary == "claude"
        and any(
            row.get("model") == "claude"
            and row.get(SOLO_CLAUDE_APPROVAL_KEY) is True
            for row in review_rows
        )
    )
    if solo_claude_signed:
        return True, "solo_claude_self_review"

    models = {row.get("model") for row in rows if row.get("model") in EXPECTED_MODELS}
    if not EXPECTED_MODELS.issubset(models):
        return False, f"missing model signature(s): {', '.join(sorted(EXPECTED_MODELS - models))}"
    if primary in EXPECTED_MODELS and not any(row.get("model") != primary for row in review_rows):
        return False, f"missing non-primary slice_review for primary={primary}"
    return True, "paired"


def candidate_phases_for_commit(
    commit: CommitInfo,
    *,
    rows: list[dict[str, Any]],
    all_phases: set[str],
    handoff_log: Path,
) -> dict[str, set[str]]:
    added = {
        str(row.get("phase"))
        for row in added_handoff_rows_for_commit(commit.sha, handoff_log)
        if row.get("phase")
    }
    cited = {
        str(row.get("phase"))
        for row in rows
        if row.get("phase") and row_cites_sha(row, commit.sha)
    }
    subject = subject_phase_candidates(commit.subject, all_phases)
    return {
        "subject": {phase for phase in subject if phase in all_phases},
        "added_rows": {phase for phase in added if phase in all_phases},
        "sha_citation": {phase for phase in cited if phase in all_phases},
    }


def build_rows_by_phase(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        phase = row.get("phase")
        if not isinstance(phase, str) or not phase:
            continue
        out.setdefault(phase, []).append(row)
    return out


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify debugger-godmode commits have paired Claude/Codex handoff evidence.",
    )
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--head", default=DEFAULT_HEAD)
    parser.add_argument("--handoff-log", type=Path, default=DEFAULT_HANDOFF_LOG)
    parser.add_argument("--json-out", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    handoff_log = args.handoff_log if args.handoff_log.is_absolute() else ROOT / args.handoff_log

    if not ref_exists(args.base):
        print(f"FAIL: base ref {args.base!r} does not exist.")
        return 2
    if not ref_exists(args.head):
        print(f"FAIL: head ref {args.head!r} does not exist.")
        return 2

    loaded = load_handoff_rows(handoff_log)
    rows_by_phase = build_rows_by_phase(loaded.rows)
    all_phases = set(rows_by_phase)
    commits = list_commits(args.base, args.head)

    violations: list[dict[str, Any]] = []
    passes: list[dict[str, Any]] = []
    out_of_scope: list[dict[str, Any]] = []
    for commit in commits:
        if not commit_touches_omni_debugger(commit.sha, handoff_log):
            out_of_scope.append(
                {
                    "sha": commit.sha,
                    "subject": commit.subject,
                    "reason": "no_omni_debugger_paths_touched",
                }
            )
            continue
        candidate_sources = candidate_phases_for_commit(
            commit,
            rows=loaded.rows,
            all_phases=all_phases,
            handoff_log=handoff_log,
        )
        candidates = sorted(set().union(*candidate_sources.values()))
        paired_phase: str | None = None
        candidate_reasons: dict[str, str] = {}
        for source_name in ("subject", "added_rows", "sha_citation"):
            for phase in sorted(candidate_sources[source_name]):
                ok, reason = phase_has_pair(rows_by_phase, phase)
                candidate_reasons[phase] = reason
                if ok and paired_phase is None:
                    paired_phase = phase
            if paired_phase is not None:
                break
        for phase in candidates:
            if phase not in candidate_reasons:
                _, reason = phase_has_pair(rows_by_phase, phase)
                candidate_reasons[phase] = reason
        entry = {
            "sha": commit.sha,
            "subject": commit.subject,
            "candidate_phases": candidates,
            "candidate_sources": {key: sorted(value) for key, value in candidate_sources.items()},
            "candidate_reasons": candidate_reasons,
            "paired_phase": paired_phase,
        }
        if paired_phase:
            passes.append(entry)
        else:
            violations.append(entry)

    summary = {
        "schema_version": 1,
        "kind": "no_solo_commits_omni_debugger",
        "base": args.base,
        "head": args.head,
        "handoff_log": repo_rel(handoff_log),
        "commit_count": len(commits),
        "audited_count": len(passes) + len(violations),
        "passed_count": len(passes),
        "violation_count": len(violations),
        "out_of_scope_count": len(out_of_scope),
        "omni_debugger_paths": list(OMNI_DEBUGGER_PATHS) + [repo_rel(handoff_log)],
        "ignored_handoff_rows": loaded.ignored_rows,
        "passes": passes,
        "violations": violations,
        "out_of_scope": out_of_scope,
    }

    if args.json_out is not None:
        json_out = args.json_out if args.json_out.is_absolute() else ROOT / args.json_out
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for warning in loaded.ignored_rows:
        print(f"WARN: {warning}")

    audited_count = len(passes) + len(violations)
    if violations:
        print(
            f"FAIL: {len(violations)} of {audited_count} audited commit(s) "
            f"lack paired handoff evidence "
            f"({len(out_of_scope)} of {len(commits)} commit(s) skipped as out of scope)."
        )
        for item in violations:
            print(f"  - {item['sha'][:7]} {item['subject']}")
            if item["candidate_phases"]:
                for phase, reason in item["candidate_reasons"].items():
                    print(f"      candidate {phase}: {reason}")
            else:
                print("      no candidate handoff phase found")
        return 1

    print(
        f"PASS: {len(passes)} commit(s) in {args.base}..{args.head} have paired "
        f"Claude/Codex handoff evidence "
        f"({len(out_of_scope)} of {len(commits)} commit(s) skipped as out of scope)."
    )
    if loaded.ignored_rows:
        print(
            "      Non-gate handoff rows were ignored by this audit; run "
            "check_two_llm_handoff_log.py --strict for schema enforcement."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
