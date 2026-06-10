#!/usr/bin/env python3
"""Score the Boss AI debugger against the focused deity-mode bar.

This is the Boss-AI-only scorer for
``docs/boss_ai_debugger_deity_mode_roadmap.md``. A question passes only when a
deterministic, local, ``driver=auto`` proof command exits 0, emits its evidence
marker, writes its declared artifacts, and closes every declared evidence id.

The checker also reports the current trace ROM/symbol hash basis against the
manifest-pinned live-capture basis. Hash-basis-gated proofs fail closed by
default; ``--allow-hash-mismatch-skip`` may be used for local development to
record honest skips without weakening the gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BENCHMARK_DIR = ROOT / "audit" / "boss_ai_debugger" / "deity_benchmark"
DEFAULT_QUESTIONS = BENCHMARK_DIR / "questions.jsonl"
DEFAULT_OUT = ROOT / ".local" / "tmp" / "boss_ai_debugger" / "deity_benchmark" / "results.json"
LIVE_CAPTURE_MANIFEST = ROOT / "audit" / "boss_ai_trace" / "live_capture_manifest.json"

REQUIRED_FIELDS = (
    "id",
    "question",
    "decision_surface",
    "driver",
    "proof_command",
    "evidence_marker",
    "expected_closed_evidence_ids",
    "required_artifacts",
    "source_anchor_expectation",
    "public_info_standard",
    "disproof_standard",
    "phase",
)

DECISION_SURFACES = {
    "live_boss",
    "generated_policy",
    "switch_dispatch",
    "score_rule",
    "changed_ai",
    "coverage_gap",
}

HASH_MARKER = "BOSS_AI_DEITY_HASH_BASIS_DIAGNOSTIC"
COMPLETE_COVERAGE_WORKLIST_OPTIONAL_EVIDENCE = {
    "next_action.command",
    "source_anchors.present",
}


@dataclass
class HashFileDiagnostic:
    kind: str
    path: str
    expected_sha256: str | None
    actual_sha256: str | None
    status: str


@dataclass
class HashBasisDiagnostic:
    manifest_path: str
    manifest_found: bool
    ready: bool
    diagnostics: list[HashFileDiagnostic] = field(default_factory=list)

    @property
    def status(self) -> str:
        if not self.manifest_found:
            return "missing_manifest"
        if self.ready:
            return "ready"
        statuses = {item.status for item in self.diagnostics}
        if "missing" in statuses:
            return "missing"
        if "mismatch" in statuses:
            return "mismatch"
        return "unknown"


@dataclass
class ArtifactResult:
    path: str
    exists: bool
    fresh: bool


@dataclass
class QuestionResult:
    id: str
    question: str
    decision_surface: str
    phase: str
    driver: str
    proof_command: str
    status: str
    passed: bool
    skipped: bool
    reason: str
    exit_code: int | None
    evidence_marker: str
    evidence_found: bool
    expected_closed_evidence_ids: list[str]
    closed_evidence_ids_found: list[str]
    missing_evidence_ids: list[str]
    required_artifacts: list[str]
    artifact_results: list[ArtifactResult]
    hash_basis_required: bool
    hash_basis_status: str
    duration_seconds: float
    stdout_tail: str = ""
    stderr_tail: str = ""


@dataclass
class DeitySummary:
    schema_version: int = 1
    kind: str = "boss_ai_debugger_deity_benchmark"
    generated_at: str = ""
    questions_path: str = ""
    manifest_path: str = ""
    question_count: int = 0
    questions_passed: int = 0
    questions_failed: int = 0
    questions_skipped: int = 0
    pass_rate: float = 0.0
    boss_ai_deity_ready: bool = False
    gap_actions: int = 0
    hash_basis: dict[str, Any] = field(default_factory=dict)
    questions: list[dict[str, Any]] = field(default_factory=list)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def today_stamp() -> str:
    return datetime.now().date().isoformat()


def repo_rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def hash_basis_diagnostic(manifest_path: Path = LIVE_CAPTURE_MANIFEST) -> HashBasisDiagnostic:
    if not manifest_path.exists():
        return HashBasisDiagnostic(
            manifest_path=repo_rel(manifest_path),
            manifest_found=False,
            ready=False,
            diagnostics=[],
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checks = [
        (
            "trace_rom",
            manifest.get("trace_rom"),
            manifest.get("trace_rom_sha256"),
        ),
        (
            "trace_symbols",
            manifest.get("trace_symbols"),
            manifest.get("trace_symbols_sha256"),
        ),
    ]
    diagnostics: list[HashFileDiagnostic] = []
    for kind, rel_path, expected in checks:
        path = ROOT / str(rel_path) if rel_path else ROOT / "__missing_hash_basis_path__"
        actual = sha256_file(path)
        if actual is None:
            status = "missing"
        elif expected and actual == str(expected).upper():
            status = "match"
        else:
            status = "mismatch"
        diagnostics.append(
            HashFileDiagnostic(
                kind=kind,
                path=repo_rel(path),
                expected_sha256=str(expected).upper() if expected else None,
                actual_sha256=actual,
                status=status,
            )
        )
    return HashBasisDiagnostic(
        manifest_path=repo_rel(manifest_path),
        manifest_found=True,
        ready=all(item.status == "match" for item in diagnostics),
        diagnostics=diagnostics,
    )


def print_hash_diagnostic(hash_basis: HashBasisDiagnostic) -> int:
    print(HASH_MARKER)
    print(f"hash_basis_status={hash_basis.status}")
    print(f"manifest={hash_basis.manifest_path} found={hash_basis.manifest_found}")
    for item in hash_basis.diagnostics:
        print(
            "hash_file "
            f"kind={item.kind} path={item.path} status={item.status} "
            f"expected={item.expected_sha256} actual={item.actual_sha256}"
        )
    print("closed_evidence_ids=hash_basis.diagnostic")
    return 0


def load_questions(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"FAIL: {repo_rel(path)}:{line_no}: invalid JSONL row: {exc}") from exc
            rows.append(row)
    if not rows:
        raise SystemExit(f"FAIL: no Boss AI deity benchmark questions found in {repo_rel(path)}")
    return rows


def schema_errors(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field_name in REQUIRED_FIELDS:
        if field_name not in row:
            errors.append(f"missing required field {field_name!r}")
    if row.get("driver") != "auto":
        errors.append(f"driver must be 'auto', got {row.get('driver')!r}")
    surface = row.get("decision_surface")
    if surface not in DECISION_SURFACES:
        errors.append(f"decision_surface must be one of {sorted(DECISION_SURFACES)}, got {surface!r}")
    for list_field in ("expected_closed_evidence_ids", "required_artifacts"):
        if list_field in row and not isinstance(row[list_field], list):
            errors.append(f"{list_field} must be a list")
    return errors


def artifact_paths(row: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for item in row.get("required_artifacts", []):
        if isinstance(item, str):
            paths.append(item)
        elif isinstance(item, dict) and "path" in item:
            paths.append(str(item["path"]))
    return paths


def resolve_artifact(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def command_for_local_python(proof_command: str) -> str:
    if proof_command == "python":
        return f'"{sys.executable}"'
    if proof_command.startswith("python "):
        return f'"{sys.executable}" {proof_command[len("python "):]}'
    return proof_command


def run_proof(proof_command: str, *, timeout: int) -> tuple[int | None, str, str, float, int]:
    command = command_for_local_python(proof_command)
    start_ns = time.time_ns()
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            shell=True,
        )
    except subprocess.TimeoutExpired:
        return None, "", "timed out", round(time.perf_counter() - start, 3), start_ns
    duration = round(time.perf_counter() - start, 3)
    return completed.returncode, completed.stdout, completed.stderr, duration, start_ns


def collect_artifacts(paths: list[str], start_ns: int) -> list[ArtifactResult]:
    results: list[ArtifactResult] = []
    # Some filesystems expose coarse mtimes. Allow a small tolerance, but do not
    # let stale committed artifacts satisfy "writes its declared artifacts".
    tolerance_ns = 2_000_000_000
    for path_text in paths:
        path = resolve_artifact(path_text)
        exists = path.exists()
        fresh = False
        if exists:
            fresh = path.stat().st_mtime_ns + tolerance_ns >= start_ns
        results.append(ArtifactResult(path=repo_rel(path), exists=exists, fresh=fresh))
    return results


def artifact_text(paths: list[str]) -> str:
    chunks: list[str] = []
    for path_text in paths:
        path = resolve_artifact(path_text)
        if not path.exists() or not path.is_file():
            continue
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return "\n".join(chunks)


def artifact_closed_evidence_ids(paths: list[str]) -> set[str]:
    closed: set[str] = set()
    for path_text in paths:
        path = resolve_artifact(path_text)
        if not path.exists() or not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            closed.update(str(item) for item in data.get("closed_evidence_ids", []))
            proof_status = data.get("proof_status", {})
            if isinstance(proof_status, dict):
                closed.update(str(item) for item in proof_status.get("present_ids", []))
    return closed


def stdout_closed_evidence_ids(stdout: str) -> set[str]:
    closed: set[str] = set()
    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped.startswith("closed_evidence_ids="):
            continue
        payload = stripped.split("=", 1)[1].strip()
        payload = payload.strip("[]")
        for item in re_split_evidence(payload):
            closed.add(item)
    return closed


def re_split_evidence(payload: str) -> list[str]:
    parts = payload.replace("'", "").replace('"', "").split(",")
    return [part.strip() for part in parts if part.strip()]


def question_requires_hash_basis(row: dict[str, Any]) -> bool:
    if bool(row.get("hash_basis_required")):
        return True
    return str(row.get("hash_basis", "")).lower() in {"trace_rom", "manifest_trace_rom", "current_trace_rom"}


def result_from_schema_errors(row: dict[str, Any], errors: list[str]) -> QuestionResult:
    return QuestionResult(
        id=str(row.get("id", "?")),
        question=str(row.get("question", "")),
        decision_surface=str(row.get("decision_surface", "")),
        phase=str(row.get("phase", "")),
        driver=str(row.get("driver", "")),
        proof_command=str(row.get("proof_command", "")),
        status="FAIL",
        passed=False,
        skipped=False,
        reason="; ".join(errors),
        exit_code=None,
        evidence_marker=str(row.get("evidence_marker", "")),
        evidence_found=False,
        expected_closed_evidence_ids=[str(item) for item in row.get("expected_closed_evidence_ids", [])],
        closed_evidence_ids_found=[],
        missing_evidence_ids=[str(item) for item in row.get("expected_closed_evidence_ids", [])],
        required_artifacts=artifact_paths(row),
        artifact_results=[],
        hash_basis_required=question_requires_hash_basis(row),
        hash_basis_status="not_checked",
        duration_seconds=0.0,
    )


def score_question(
    row: dict[str, Any],
    *,
    timeout: int,
    hash_basis: HashBasisDiagnostic,
    allow_hash_mismatch_skip: bool,
) -> QuestionResult:
    errors = schema_errors(row)
    if errors:
        return result_from_schema_errors(row, errors)

    question_id = str(row["id"])
    proof_command = str(row["proof_command"])
    evidence_marker = str(row["evidence_marker"])
    expected_evidence = [str(item) for item in row.get("expected_closed_evidence_ids", [])]
    required_artifacts = artifact_paths(row)
    hash_required = question_requires_hash_basis(row)

    if hash_required and not hash_basis.ready:
        reason = (
            f"blocked_by_hash_basis: current trace ROM/symbol basis is {hash_basis.status}; "
            f"manifest={hash_basis.manifest_path}"
        )
        if allow_hash_mismatch_skip:
            return QuestionResult(
                id=question_id,
                question=str(row["question"]),
                decision_surface=str(row["decision_surface"]),
                phase=str(row["phase"]),
                driver=str(row["driver"]),
                proof_command=proof_command,
                status="SKIP",
                passed=False,
                skipped=True,
                reason=reason,
                exit_code=None,
                evidence_marker=evidence_marker,
                evidence_found=False,
                expected_closed_evidence_ids=expected_evidence,
                closed_evidence_ids_found=[],
                missing_evidence_ids=expected_evidence,
                required_artifacts=required_artifacts,
                artifact_results=[],
                hash_basis_required=True,
                hash_basis_status=hash_basis.status,
                duration_seconds=0.0,
            )
        return QuestionResult(
            id=question_id,
            question=str(row["question"]),
            decision_surface=str(row["decision_surface"]),
            phase=str(row["phase"]),
            driver=str(row["driver"]),
            proof_command=proof_command,
            status="FAIL",
            passed=False,
            skipped=False,
            reason=reason,
            exit_code=None,
            evidence_marker=evidence_marker,
            evidence_found=False,
            expected_closed_evidence_ids=expected_evidence,
            closed_evidence_ids_found=[],
            missing_evidence_ids=expected_evidence,
            required_artifacts=required_artifacts,
            artifact_results=[],
            hash_basis_required=True,
            hash_basis_status=hash_basis.status,
            duration_seconds=0.0,
        )

    exit_code, stdout, stderr, duration, start_ns = run_proof(proof_command, timeout=timeout)
    artifacts = collect_artifacts(required_artifacts, start_ns)
    emitted_text = stdout + "\n" + artifact_text(required_artifacts)
    closed_evidence = artifact_closed_evidence_ids(required_artifacts)
    closed_evidence.update(stdout_closed_evidence_ids(stdout))
    expected_evidence = effective_expected_evidence(
        question_id=question_id,
        expected_evidence=expected_evidence,
        required_artifacts=required_artifacts,
    )
    evidence_found = bool(evidence_marker) and evidence_marker in emitted_text
    found_evidence = [
        evidence_id
        for evidence_id in expected_evidence
        if evidence_id in closed_evidence
    ]
    missing_evidence = [
        evidence_id
        for evidence_id in expected_evidence
        if evidence_id not in closed_evidence
    ]
    stale_or_missing_artifacts = [item.path for item in artifacts if not (item.exists and item.fresh)]

    passed = False
    if exit_code is None:
        reason = stderr or "proof did not complete"
    elif exit_code != 0:
        reason = f"proof command exited {exit_code}"
    elif not evidence_found:
        reason = f"proof ran but did not emit evidence marker {evidence_marker!r}"
    elif missing_evidence:
        reason = "proof did not close evidence ids: " + ", ".join(missing_evidence)
    elif stale_or_missing_artifacts:
        reason = "proof did not freshly write required artifacts: " + ", ".join(stale_or_missing_artifacts)
    else:
        reason = "self-drove to a Boss AI proof and closed declared evidence"
        passed = True

    return QuestionResult(
        id=question_id,
        question=str(row["question"]),
        decision_surface=str(row["decision_surface"]),
        phase=str(row["phase"]),
        driver=str(row["driver"]),
        proof_command=proof_command,
        status="PASS" if passed else "FAIL",
        passed=passed,
        skipped=False,
        reason=reason,
        exit_code=exit_code,
        evidence_marker=evidence_marker,
        evidence_found=evidence_found,
        expected_closed_evidence_ids=expected_evidence,
        closed_evidence_ids_found=found_evidence,
        missing_evidence_ids=missing_evidence,
        required_artifacts=required_artifacts,
        artifact_results=artifacts,
        hash_basis_required=hash_required,
        hash_basis_status=hash_basis.status if hash_required else "not_required",
        duration_seconds=duration,
        stdout_tail=stdout[-1200:],
        stderr_tail=stderr[-1200:],
    )


def effective_expected_evidence(
    *,
    question_id: str,
    expected_evidence: list[str],
    required_artifacts: list[str],
) -> list[str]:
    if question_id != "boss_ai_deity_coverage_gap_worklist":
        return expected_evidence
    if not coverage_worklist_is_complete(required_artifacts):
        return expected_evidence
    return [
        evidence_id
        for evidence_id in expected_evidence
        if evidence_id not in COMPLETE_COVERAGE_WORKLIST_OPTIONAL_EVIDENCE
    ]


def coverage_worklist_is_complete(required_artifacts: list[str]) -> bool:
    for path_text in required_artifacts:
        path = resolve_artifact(path_text)
        if not path.exists() or not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        reachability = data.get("reachability_model", {})
        basis = data.get("coverage_basis", {})
        if not isinstance(reachability, dict) or not isinstance(basis, dict):
            continue
        if (
            data.get("kind") == "boss_ai_deity_coverage_worklist"
            and reachability.get("reachable_status") == "complete"
            and int(basis.get("target_count", 0) or 0) == 0
            and int(basis.get("group_count", 0) or 0) == 0
        ):
            return True
    return False


def build_summary(
    question_results: list[QuestionResult],
    *,
    questions_path: Path,
    hash_basis: HashBasisDiagnostic,
) -> DeitySummary:
    passed = sum(1 for result in question_results if result.passed)
    skipped = sum(1 for result in question_results if result.skipped)
    failed = len(question_results) - passed - skipped
    gap_actions = failed + skipped
    total = len(question_results)
    return DeitySummary(
        generated_at=utc_now(),
        questions_path=repo_rel(questions_path),
        manifest_path=hash_basis.manifest_path,
        question_count=total,
        questions_passed=passed,
        questions_failed=failed,
        questions_skipped=skipped,
        pass_rate=round(passed / total, 3) if total else 0.0,
        boss_ai_deity_ready=(failed == 0 and skipped == 0 and passed == total),
        gap_actions=gap_actions,
        hash_basis={
            "manifest_path": hash_basis.manifest_path,
            "manifest_found": hash_basis.manifest_found,
            "ready": hash_basis.ready,
            "status": hash_basis.status,
            "diagnostics": [asdict(item) for item in hash_basis.diagnostics],
        },
        questions=[asdict(result) for result in question_results],
    )


def write_markdown(path: Path, summary: DeitySummary) -> None:
    lines = [
        "# Boss AI Debugger Deity Benchmark Baseline",
        "",
        f"- Generated: {summary.generated_at}",
        f"- Questions path: {summary.questions_path}",
        f"- Manifest path: {summary.manifest_path}",
        f"- Questions: {summary.question_count}",
        f"- Passed: {summary.questions_passed}",
        f"- Failed: {summary.questions_failed}",
        f"- Skipped: {summary.questions_skipped}",
        f"- Pass rate: {summary.pass_rate:.3f}",
        f"- boss_ai_deity_ready: {summary.boss_ai_deity_ready}",
        f"- gap_actions: {summary.gap_actions}",
        "",
        "A question passes only when its `driver=auto` proof command exits 0,",
        "emits the evidence marker, freshly writes every declared artifact,",
        "and closes every declared evidence id.",
        "",
        "## Hash Basis",
        "",
        f"- Status: {summary.hash_basis.get('status')}",
        f"- Ready: {summary.hash_basis.get('ready')}",
        "",
        "| kind | path | status | expected | actual |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in summary.hash_basis.get("diagnostics", []):
        lines.append(
            f"| {item['kind']} | {item['path']} | {item['status']} | "
            f"{item.get('expected_sha256')} | {item.get('actual_sha256')} |"
        )
    lines.extend(
        [
            "",
            "## Question Results",
            "",
            "| id | surface | phase | status | reason |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for question in summary.questions:
        lines.append(
            f"| {question['id']} | {question['decision_surface']} | {question['phase']} | "
            f"{question['status']} | {question['reason']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_self_test() -> int:
    artifact = ROOT / ".local" / "tmp" / "boss_ai_debugger" / "deity_selftest_artifact.txt"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    if artifact.exists():
        artifact.unlink()

    marker = "SYNTH_BOSS_AI_DEITY_OK"
    evidence = "synthetic.evidence.closed"
    pass_command = (
        "python -c "
        f"\"from pathlib import Path; Path(r'{artifact}').write_text('ok', encoding='utf-8'); "
        f"print('{marker}'); print('closed_evidence_ids={evidence}')\""
    )
    base_row = {
        "id": "synthetic_pass",
        "question": "synthetic scorer pass",
        "decision_surface": "generated_policy",
        "driver": "auto",
        "proof_command": pass_command,
        "evidence_marker": marker,
        "expected_closed_evidence_ids": [evidence],
        "required_artifacts": [repo_rel(artifact)],
        "source_anchor_expectation": "synthetic",
        "public_info_standard": "synthetic",
        "disproof_standard": "synthetic",
        "phase": "0",
    }
    hash_ready = HashBasisDiagnostic(
        manifest_path="synthetic",
        manifest_found=True,
        ready=True,
        diagnostics=[
            HashFileDiagnostic(
                kind="trace_rom",
                path="synthetic.gbc",
                expected_sha256="A",
                actual_sha256="A",
                status="match",
            )
        ],
    )
    hash_stale = HashBasisDiagnostic(
        manifest_path="synthetic",
        manifest_found=True,
        ready=False,
        diagnostics=[
            HashFileDiagnostic(
                kind="trace_rom",
                path="synthetic.gbc",
                expected_sha256="A",
                actual_sha256="B",
                status="mismatch",
            )
        ],
    )

    cases: list[tuple[dict[str, Any], HashBasisDiagnostic, bool, str]] = [
        (dict(base_row), hash_ready, False, "PASS"),
        ({**base_row, "id": "synthetic_nonzero", "proof_command": "python -c \"import sys; sys.exit(3)\""}, hash_ready, False, "FAIL"),
        ({**base_row, "id": "synthetic_missing_marker", "proof_command": "python -c \"print('no marker')\""}, hash_ready, False, "FAIL"),
        ({**base_row, "id": "synthetic_missing_evidence", "expected_closed_evidence_ids": ["missing.evidence"]}, hash_ready, False, "FAIL"),
        ({**base_row, "id": "synthetic_not_auto", "driver": "manual"}, hash_ready, False, "FAIL"),
        ({**base_row, "id": "synthetic_hash_skip", "hash_basis_required": True}, hash_stale, True, "SKIP"),
    ]

    failures: list[str] = []
    results: list[QuestionResult] = []
    for row, basis, allow_skip, expected_status in cases:
        if artifact.exists():
            artifact.unlink()
        result = score_question(
            row,
            timeout=30,
            hash_basis=basis,
            allow_hash_mismatch_skip=allow_skip,
        )
        results.append(result)
        if result.status != expected_status:
            failures.append(f"{row['id']}: expected {expected_status}, got {result.status} ({result.reason})")

    summary = build_summary(results, questions_path=DEFAULT_QUESTIONS, hash_basis=hash_stale)
    if summary.questions_passed != 1 or summary.questions_failed != 4 or summary.questions_skipped != 1:
        failures.append(
            "summary status math wrong: "
            f"pass={summary.questions_passed} fail={summary.questions_failed} skip={summary.questions_skipped}"
        )
    if summary.boss_ai_deity_ready:
        failures.append("boss_ai_deity_ready should be False with failing/skipped synthetic rows")
    if summary.gap_actions != 5:
        failures.append(f"gap_actions should be 5, got {summary.gap_actions}")

    if failures:
        print("SELF-TEST FAIL:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("SELF-TEST PASS: Boss AI deity scorer logic verified.")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score the Boss AI debugger against the Boss-AI-only deity-mode bar.",
    )
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--markdown-out", type=Path)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Write a baseline report under audit/boss_ai_debugger/deity_benchmark and exit 0.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Verify the scorer's own logic with synthetic proofs and exit.",
    )
    parser.add_argument(
        "--allow-hash-mismatch-skip",
        action="store_true",
        help="Skip hash-basis-gated questions when local trace ROM/symbol files do not match the manifest.",
    )
    parser.add_argument(
        "--hash-diagnostic",
        action="store_true",
        help="Print the current Boss AI trace ROM/symbol hash-basis diagnostic and exit 0.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    hash_basis = hash_basis_diagnostic()

    if args.self_test:
        return run_self_test()
    if args.hash_diagnostic:
        return print_hash_diagnostic(hash_basis)

    questions_path = args.questions if args.questions.is_absolute() else ROOT / args.questions
    out_path = args.out if args.out.is_absolute() else ROOT / args.out
    markdown_path = args.markdown_out if args.markdown_out is None or args.markdown_out.is_absolute() else ROOT / args.markdown_out

    if args.baseline:
        stamp = today_stamp()
        if args.out == DEFAULT_OUT:
            out_path = BENCHMARK_DIR / f"baseline_{stamp}.json"
        if markdown_path is None:
            markdown_path = BENCHMARK_DIR / f"baseline_{stamp}.md"

    questions = load_questions(questions_path)
    question_results = [
        score_question(
            row,
            timeout=args.timeout,
            hash_basis=hash_basis,
            allow_hash_mismatch_skip=args.allow_hash_mismatch_skip,
        )
        for row in questions
    ]
    summary = build_summary(question_results, questions_path=questions_path, hash_basis=hash_basis)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(asdict(summary), indent=2) + "\n", encoding="utf-8")
    if markdown_path is not None:
        write_markdown(markdown_path, summary)

    for item in hash_basis.diagnostics:
        print(
            "HASH "
            f"{item.kind}: status={item.status} path={item.path} "
            f"expected={item.expected_sha256} actual={item.actual_sha256}"
        )
    for result in question_results:
        print(
            f"{result.status} {result.id} "
            f"(surface={result.decision_surface} phase={result.phase} hash={result.hash_basis_status}): "
            f"{result.reason}"
        )
    print(
        "boss_ai_deity: "
        f"questions={summary.question_count} passed={summary.questions_passed} "
        f"failed={summary.questions_failed} skipped={summary.questions_skipped} "
        f"pass_rate={summary.pass_rate:.3f}"
    )
    print(f"boss_ai_deity_ready={summary.boss_ai_deity_ready} gap_actions={summary.gap_actions}")
    print(f"json_out={repo_rel(out_path)}")
    if markdown_path is not None:
        print(f"markdown_out={repo_rel(markdown_path)}")

    if not args.baseline and not summary.boss_ai_deity_ready:
        print("FAIL: boss_ai_deity_ready is False. Re-run with --baseline to record a known-low baseline.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
