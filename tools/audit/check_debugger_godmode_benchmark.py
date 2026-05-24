#!/usr/bin/env python3
"""Score the omni-debugger against the godmode repo-question benchmark.

This audit treats the debugger as a user-facing Q&A oracle. Each benchmark row
asks an ordinary-language repo question and names the expected anchors for a
useful answer:

  * source/data locations
  * first proof command
  * regression gate
  * evidence standard
  * disproof standard

The checker runs the current `python -m tools.debugger` JSON surfaces, scores
those dimensions, and writes per-question artifacts under `.local/tmp` so the
misses can be inspected without polluting durable audit history.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_QUESTIONS = ROOT / "audit" / "debugger_godmode_benchmark" / "questions.jsonl"
DEFAULT_ARTIFACT_DIR = ROOT / ".local" / "tmp" / "debugger_godmode_benchmark"
DEFAULT_OUT = DEFAULT_ARTIFACT_DIR / "results.json"

PLACEHOLDER_RE = re.compile(r"<[^>]+>")
TOKEN_RE = re.compile(r"[a-z0-9_./:\\-]+")
WORD_RE = re.compile(r"[a-z0-9_]+")

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "from",
    "if",
    "in",
    "into",
    "is",
    "it",
    "of",
    "or",
    "run",
    "that",
    "the",
    "this",
    "to",
    "with",
}


@dataclass
class CommandRun:
    name: str
    command: list[str]
    json_path: str
    exit_code: int | None
    duration_seconds: float
    stdout_tail: str
    stderr_tail: str
    timed_out: bool = False


@dataclass
class QuestionScore:
    id: str
    archetype: str
    proof_mode: str
    symptom: str
    passed: bool
    source_anchor_pass: bool
    source_anchor_hits: list[str]
    source_anchor_misses: list[str]
    source_anchor_hit_rate: float
    proof_command_pass: bool
    proof_command_expected: str
    proof_command_match: str | None
    regression_gate_pass: bool
    regression_gate_expected: str
    regression_gate_match: str | None
    evidence_standard_pass: bool
    evidence_standard_overlap: int
    evidence_standard_match: str | None
    disproof_standard_pass: bool
    disproof_standard_overlap: int
    disproof_standard_match: str | None
    command_runs: list[CommandRun]
    artifact_paths: dict[str, str]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def repo_rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")[:120] or "question"


def normalize_text(value: str) -> str:
    return " ".join(value.replace("\\", "/").lower().split())


def iter_strings(value: Any) -> list[str]:
    out: list[str] = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            out.extend(iter_strings(item))
    elif isinstance(value, list):
        for item in value:
            out.extend(iter_strings(item))
    return out


def command_tokens(command: str) -> set[str]:
    without_placeholders = PLACEHOLDER_RE.sub(" ", command)
    tokens = set(TOKEN_RE.findall(normalize_text(without_placeholders)))
    return {token for token in tokens if token not in {"python", "-m"}}


def command_equivalent(expected: str, actual: str) -> bool:
    expected_norm = normalize_text(PLACEHOLDER_RE.sub(" ", expected))
    actual_norm = normalize_text(actual)
    if expected_norm and expected_norm in actual_norm:
        return True
    expected_tokens = command_tokens(expected)
    actual_tokens = command_tokens(actual)
    return bool(expected_tokens) and expected_tokens.issubset(actual_tokens)


def significant_words(value: str) -> set[str]:
    words = set(WORD_RE.findall(normalize_text(value)))
    return {word for word in words if len(word) > 2 and word not in STOP_WORDS}


def best_standard_match(
    expected: str,
    actual_values: list[str],
    required_overlap: int,
) -> tuple[bool, int, str | None]:
    expected_words = significant_words(expected)
    if not expected_words or not actual_values:
        return False, 0, None
    best_overlap = 0
    best_value: str | None = None
    for actual in actual_values:
        overlap = len(expected_words & significant_words(actual))
        if overlap > best_overlap:
            best_overlap = overlap
            best_value = actual
    required = min(required_overlap, len(expected_words))
    return best_overlap >= required, best_overlap, best_value


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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
        raise SystemExit(f"FAIL: no benchmark questions found in {repo_rel(path)}")
    return rows


def run_debugger_json(
    *,
    name: str,
    args: list[str],
    json_path: Path,
    timeout: int,
) -> tuple[CommandRun, Any | None]:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "tools.debugger", *args, "--json-out", str(json_path)]
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        duration = time.perf_counter() - start
        run = CommandRun(
            name=name,
            command=command,
            json_path=repo_rel(json_path),
            exit_code=completed.returncode,
            duration_seconds=round(duration, 3),
            stdout_tail=completed.stdout[-1200:],
            stderr_tail=completed.stderr[-1200:],
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.perf_counter() - start
        run = CommandRun(
            name=name,
            command=command,
            json_path=repo_rel(json_path),
            exit_code=None,
            duration_seconds=round(duration, 3),
            stdout_tail=(exc.stdout or "")[-1200:] if isinstance(exc.stdout, str) else "",
            stderr_tail=(exc.stderr or "")[-1200:] if isinstance(exc.stderr, str) else "",
            timed_out=True,
        )
        return run, None

    if completed.returncode != 0 or not json_path.exists():
        return run, None
    try:
        return run, load_json(json_path)
    except json.JSONDecodeError:
        return run, None


def collect_actual_strings(payloads: list[Any | None]) -> list[str]:
    strings: list[str] = []
    for payload in payloads:
        if payload is None:
            continue
        strings.extend(iter_strings(payload))
    return strings


def collect_standard_values(payloads: list[Any | None], field: str) -> list[str]:
    values: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            if field in value:
                field_value = value[field]
                if isinstance(field_value, str):
                    values.append(field_value)
                elif isinstance(field_value, list):
                    values.extend(item for item in field_value if isinstance(item, str))
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for payload in payloads:
        if payload is not None:
            visit(payload)
    return values


def first_equivalent(expected: str, actual_strings: list[str]) -> str | None:
    for actual in actual_strings:
        if command_equivalent(expected, actual):
            return actual
    return None


def score_question(
    *,
    row: dict[str, Any],
    index: int,
    artifact_dir: Path,
    timeout: int,
    source_anchor_threshold: float,
    standard_token_threshold: int,
    next_only: bool,
) -> QuestionScore:
    question_id = str(row["id"])
    symptom = str(row["symptom"])
    expected = row["expected_answer"]
    prefix = f"{index:02d}_{safe_id(question_id)}"

    next_path = artifact_dir / f"{prefix}_next.json"
    next_run, next_payload = run_debugger_json(
        name="next",
        args=["next", "--symptom", symptom],
        json_path=next_path,
        timeout=timeout,
    )

    command_runs = [next_run]
    payloads: list[Any | None] = [next_payload]
    artifact_paths = {"next_json": repo_rel(next_path)}

    score = build_question_score(
        row=row,
        command_runs=command_runs,
        payloads=payloads,
        artifact_paths=artifact_paths,
        source_anchor_threshold=source_anchor_threshold,
        standard_token_threshold=standard_token_threshold,
    )
    if next_only or score.passed:
        return score

    investigate_path = artifact_dir / f"{prefix}_investigate.json"
    investigate_run, investigate_payload = run_debugger_json(
        name="investigate",
        args=["investigate", "--symptom", symptom],
        json_path=investigate_path,
        timeout=timeout,
    )
    command_runs.append(investigate_run)
    payloads.append(investigate_payload)
    artifact_paths["investigate_json"] = repo_rel(investigate_path)

    return build_question_score(
        row=row,
        command_runs=command_runs,
        payloads=payloads,
        artifact_paths=artifact_paths,
        source_anchor_threshold=source_anchor_threshold,
        standard_token_threshold=standard_token_threshold,
    )


def build_question_score(
    *,
    row: dict[str, Any],
    command_runs: list[CommandRun],
    payloads: list[Any | None],
    artifact_paths: dict[str, str],
    source_anchor_threshold: float,
    standard_token_threshold: int,
) -> QuestionScore:
    question_id = str(row["id"])
    symptom = str(row["symptom"])
    expected = row["expected_answer"]
    actual_strings = collect_actual_strings(payloads)
    actual_norm = [normalize_text(value) for value in actual_strings]

    source_anchors = [str(anchor) for anchor in expected.get("source_anchors", [])]
    source_hits: list[str] = []
    source_misses: list[str] = []
    for anchor in source_anchors:
        anchor_norm = normalize_text(anchor)
        if any(anchor_norm in candidate for candidate in actual_norm):
            source_hits.append(anchor)
        else:
            source_misses.append(anchor)
    source_hit_rate = len(source_hits) / len(source_anchors) if source_anchors else 1.0
    required_hits = max(1, math.ceil(len(source_anchors) * source_anchor_threshold)) if source_anchors else 0
    source_pass = len(source_hits) >= required_hits

    proof_expected = str(expected.get("proof_command", ""))
    proof_match = first_equivalent(proof_expected, actual_strings) if proof_expected else None
    proof_pass = bool(proof_match)

    gate_expected = str(expected.get("regression_gate", ""))
    gate_match = first_equivalent(gate_expected, actual_strings) if gate_expected else None
    gate_pass = bool(gate_match)

    evidence_values = collect_standard_values(payloads, "evidence_standard")
    evidence_pass, evidence_overlap, evidence_match = best_standard_match(
        str(expected.get("evidence_standard", "")),
        evidence_values,
        standard_token_threshold,
    )

    disproof_values = collect_standard_values(payloads, "disproof_standard")
    disproof_pass, disproof_overlap, disproof_match = best_standard_match(
        str(expected.get("disproof_standard", "")),
        disproof_values,
        standard_token_threshold,
    )

    passed = source_pass and proof_pass and gate_pass and evidence_pass and disproof_pass
    return QuestionScore(
        id=question_id,
        archetype=str(row.get("archetype", "")),
        proof_mode=str(row.get("proof_mode", "")),
        symptom=symptom,
        passed=passed,
        source_anchor_pass=source_pass,
        source_anchor_hits=source_hits,
        source_anchor_misses=source_misses,
        source_anchor_hit_rate=round(source_hit_rate, 3),
        proof_command_pass=proof_pass,
        proof_command_expected=proof_expected,
        proof_command_match=proof_match,
        regression_gate_pass=gate_pass,
        regression_gate_expected=gate_expected,
        regression_gate_match=gate_match,
        evidence_standard_pass=evidence_pass,
        evidence_standard_overlap=evidence_overlap,
        evidence_standard_match=evidence_match,
        disproof_standard_pass=disproof_pass,
        disproof_standard_overlap=disproof_overlap,
        disproof_standard_match=disproof_match,
        command_runs=command_runs,
        artifact_paths=artifact_paths,
    )


def summarize(
    results: list[QuestionScore],
    *,
    threshold: float,
    baseline: bool,
    questions_path: Path,
    source_anchor_threshold: float,
    standard_token_threshold: int,
    next_only: bool,
) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for result in results if result.passed)
    command_runs = [run for result in results for run in result.command_runs]
    dimension_counts = {
        "source_anchor": sum(1 for result in results if result.source_anchor_pass),
        "proof_command": sum(1 for result in results if result.proof_command_pass),
        "regression_gate": sum(1 for result in results if result.regression_gate_pass),
        "evidence_standard": sum(1 for result in results if result.evidence_standard_pass),
        "disproof_standard": sum(1 for result in results if result.disproof_standard_pass),
    }
    return {
        "schema_version": 1,
        "kind": "debugger_godmode_benchmark",
        "generated_at": utc_now(),
        "baseline_mode": baseline,
        "threshold": threshold,
        "questions_path": repo_rel(questions_path),
        "source_anchor_threshold": source_anchor_threshold,
        "standard_token_threshold": standard_token_threshold,
        "next_only": next_only,
        "question_count": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total if total else 0.0, 3),
        "command_run_count": len(command_runs),
        "investigate_run_count": sum(1 for run in command_runs if run.name == "investigate"),
        "timed_out_count": sum(1 for run in command_runs if run.timed_out),
        "total_command_duration_seconds": round(
            sum(run.duration_seconds for run in command_runs),
            3,
        ),
        "dimension_counts": dimension_counts,
        "results": [asdict(result) for result in results],
    }


def write_markdown(path: Path, summary: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = summary["results"]
    lines = [
        "# Debugger Godmode Benchmark Baseline",
        "",
        f"- Generated: {summary['generated_at']}",
        f"- Baseline mode: {summary['baseline_mode']}",
        f"- Questions: {summary['question_count']}",
        f"- Questions path: {summary['questions_path']}",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        f"- Pass rate: {summary['pass_rate']:.3f}",
        f"- Threshold: {summary['threshold']:.3f}",
        f"- Command runs: {summary['command_run_count']}",
        f"- Investigate runs: {summary['investigate_run_count']}",
        f"- Timed out runs: {summary['timed_out_count']}",
        f"- Total command duration seconds: {summary['total_command_duration_seconds']:.3f}",
        f"- Source anchor threshold: {summary['source_anchor_threshold']:.3f}",
        f"- Standard token threshold: {summary['standard_token_threshold']}",
        f"- Next only: {summary['next_only']}",
        "",
        "A question passes only when source anchors, proof command, regression gate,",
        "evidence standard, and disproof standard all pass. `--baseline` records the",
        "score without failing the process when the pass rate is below the threshold.",
        "",
        "## Dimension Counts",
        "",
    ]
    for key, value in summary["dimension_counts"].items():
        lines.append(f"- {key}: {value}/{summary['question_count']}")
    lines.extend(
        [
            "",
            "## Question Results",
            "",
            "| id | pass | source | proof | gate | evidence | disproof |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        source = f"{len(row['source_anchor_hits'])}/{len(row['source_anchor_hits']) + len(row['source_anchor_misses'])}"
        lines.append(
            "| {id} | {passed} | {source} | {proof} | {gate} | {evidence} | {disproof} |".format(
                id=row["id"],
                passed="PASS" if row["passed"] else "FAIL",
                source=source,
                proof="PASS" if row["proof_command_pass"] else "FAIL",
                gate="PASS" if row["regression_gate_pass"] else "FAIL",
                evidence="PASS" if row["evidence_standard_pass"] else "FAIL",
                disproof="PASS" if row["disproof_standard_pass"] else "FAIL",
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score python -m tools.debugger against the godmode benchmark questions.",
    )
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--markdown-out", type=Path)
    parser.add_argument("--threshold", type=float, default=0.85)
    parser.add_argument("--source-anchor-threshold", type=float, default=0.5)
    parser.add_argument(
        "--standard-token-threshold",
        type=int,
        default=3,
        help="Minimum significant-token overlap required for evidence/disproof standards.",
    )
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--limit", type=int, default=0, help="Score only the first N questions.")
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Exit 0 after writing scores even when the pass rate is below --threshold.",
    )
    parser.add_argument(
        "--next-only",
        action="store_true",
        help="Run only `python -m tools.debugger next`; useful for fast harness smoke checks.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    questions_path = args.questions if args.questions.is_absolute() else ROOT / args.questions
    artifact_dir = args.artifacts_dir if args.artifacts_dir.is_absolute() else ROOT / args.artifacts_dir
    out_path = args.out if args.out.is_absolute() else ROOT / args.out
    markdown_path = None
    if args.markdown_out is not None:
        markdown_path = args.markdown_out if args.markdown_out.is_absolute() else ROOT / args.markdown_out

    questions = load_questions(questions_path)
    if args.limit:
        questions = questions[: args.limit]

    if not 0 < args.source_anchor_threshold <= 1:
        print("FAIL: --source-anchor-threshold must be in (0, 1].", file=sys.stderr)
        return 2
    if args.standard_token_threshold < 1:
        print("FAIL: --standard-token-threshold must be >= 1.", file=sys.stderr)
        return 2

    results: list[QuestionScore] = []
    for index, row in enumerate(questions, 1):
        result = score_question(
            row=row,
            index=index,
            artifact_dir=artifact_dir,
            timeout=args.timeout,
            source_anchor_threshold=args.source_anchor_threshold,
            standard_token_threshold=args.standard_token_threshold,
            next_only=args.next_only,
        )
        results.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(
            f"{status} {result.id}: "
            f"source={len(result.source_anchor_hits)}/"
            f"{len(result.source_anchor_hits) + len(result.source_anchor_misses)} "
            f"proof={result.proof_command_pass} gate={result.regression_gate_pass} "
            f"evidence={result.evidence_standard_pass} disproof={result.disproof_standard_pass}"
        )

    summary = summarize(
        results,
        threshold=args.threshold,
        baseline=args.baseline,
        questions_path=questions_path,
        source_anchor_threshold=args.source_anchor_threshold,
        standard_token_threshold=args.standard_token_threshold,
        next_only=args.next_only,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if markdown_path is not None:
        write_markdown(markdown_path, summary)

    print(
        "debugger_godmode_benchmark: "
        f"questions={summary['question_count']} passed={summary['passed']} "
        f"failed={summary['failed']} pass_rate={summary['pass_rate']:.3f} "
        f"threshold={summary['threshold']:.3f}"
    )
    print(f"json_out={repo_rel(out_path)}")
    if markdown_path is not None:
        print(f"markdown_out={repo_rel(markdown_path)}")

    if not args.baseline and summary["pass_rate"] < args.threshold:
        print("FAIL: pass rate is below threshold. Re-run with --baseline to record a known-low baseline.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
