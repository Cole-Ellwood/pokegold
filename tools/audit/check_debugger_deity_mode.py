#!/usr/bin/env python3
"""Score the debugger against the *deity-mode* bar: self-driving runtime proofs.

The godmode benchmark (`check_debugger_godmode_benchmark.py`) scores the
debugger as a Q&A oracle that *prescribes* a proof command a human then runs
with hand-supplied inputs. Deity mode is the tier above: the debugger must
drive the proof itself — navigate to the state, capture the evidence, run it —
with **no hand-supplied save state, trace, or scenario**.

So this checker is stricter and different in kind: it does not score whether the
answer *cites* a proof command; it **runs** the proof command and checks it
actually self-drove to a result. Every benchmark row therefore carries
``driver: auto`` (the deity discriminator) and an ``evidence_marker`` the
self-driving proof must emit on success.

It also tracks the seven deity *capability components*. A component counts as
built when it has registered a (green) selftest component of the same name —
the selftest registry is the single source of truth for "is this capability
real," and selftest's own all-green gate guarantees a registered component
works end-to-end. This keeps the deity bar additive: the godmode triad
(`audit ready=True` 11/11, godmode benchmark 29/29, and the all-green selftest
gate) stays the frozen floor; deity is measured separately here. (The selftest
component count grows as each deity component lands green — see roadmap §5.)

Roadmap: ``docs/debugger_deity_mode_roadmap.md`` (Phase 0 builds this harness).
At baseline — before any capability phase lands — every runtime proof fails and
every component is unbuilt, so ``deity_ready=False`` with a large gap count.
That zero is the start line, not a regression.
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
# Run as a path (`python tools/audit/check_debugger_deity_mode.py`), so ROOT is
# not on sys.path by default; the in-process selftest-registry import needs it.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_QUESTIONS = ROOT / "audit" / "debugger_deity_benchmark" / "questions.jsonl"
DEFAULT_OUT = ROOT / ".local" / "tmp" / "debugger_deity_benchmark" / "results.json"

# The seven deity capability components, by the phase that builds each. A
# component is "built" when a selftest component of the same name exists (see
# module docstring). sm83_model_parity is selftest-only; the rest also back a
# front-door verb, but the selftest component is the canonical built signal.
DEITY_COMPONENTS: tuple[tuple[str, str], ...] = (
    ("auto_navigation", "1"),
    ("auto_taint", "2"),
    ("audio_replay", "3"),
    ("graphics_replay", "3"),
    ("script_vm_replay", "3"),
    ("sm83_model_parity", "4"),
    ("live_view", "5"),
)


@dataclass
class QuestionResult:
    id: str
    archetype: str
    phase: str
    symptom: str
    driver: str
    proof_command: str
    passed: bool
    reason: str
    exit_code: int | None
    evidence_marker: str
    evidence_found: bool
    duration_seconds: float
    stdout_tail: str = ""
    stderr_tail: str = ""


@dataclass
class ComponentResult:
    name: str
    phase: str
    built: bool


@dataclass
class DeitySummary:
    schema_version: int = 1
    kind: str = "debugger_deity_mode_benchmark"
    generated_at: str = ""
    questions_path: str = ""
    question_count: int = 0
    questions_passed: int = 0
    questions_failed: int = 0
    pass_rate: float = 0.0
    component_count: int = 0
    components_built: int = 0
    components_unbuilt: int = 0
    deity_ready: bool = False
    deity_gap_actions: int = 0
    questions: list[dict[str, Any]] = field(default_factory=list)
    components: list[dict[str, Any]] = field(default_factory=list)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def repo_rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def load_questions(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"FAIL: {repo_rel(path)}:{line_no}: invalid JSONL row: {exc}") from exc
    if not rows:
        raise SystemExit(f"FAIL: no deity benchmark questions found in {repo_rel(path)}")
    return rows


def selftest_component_names() -> set[str]:
    """The selftest registry — the source of truth for which capabilities are built."""
    from tools.debugger.selftest import NAMED_CHECKS

    return {name for name, _ in NAMED_CHECKS}


def resolve_argv(proof_command: str) -> list[str]:
    """Split a proof command into argv, substituting the running interpreter for `python`."""
    argv = shlex.split(proof_command, posix=True)
    if argv and argv[0] == "python":
        argv[0] = sys.executable
    return argv


def run_proof(proof_command: str, *, timeout: int) -> tuple[int | None, str, str, float]:
    argv = resolve_argv(proof_command)
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            argv,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "", "timed out", round(time.perf_counter() - start, 3)
    except FileNotFoundError as exc:
        return None, "", f"command not runnable: {exc}", round(time.perf_counter() - start, 3)
    duration = round(time.perf_counter() - start, 3)
    return completed.returncode, completed.stdout, completed.stderr, duration


def score_question(row: dict[str, Any], *, timeout: int) -> QuestionResult:
    question_id = str(row.get("id", "?"))
    driver = str(row.get("driver", ""))
    proof_command = str(row.get("proof_command", ""))
    evidence_marker = str(row.get("evidence_marker", ""))

    # The deity discriminator: a row that is not declared driver:auto cannot
    # score PASS here — that would be the godmode (prescribe) bar, not deity.
    if driver != "auto":
        return QuestionResult(
            id=question_id,
            archetype=str(row.get("archetype", "")),
            phase=str(row.get("phase", "")),
            symptom=str(row.get("symptom", "")),
            driver=driver,
            proof_command=proof_command,
            passed=False,
            reason=f"driver must be 'auto', got {driver!r}",
            exit_code=None,
            evidence_marker=evidence_marker,
            evidence_found=False,
            duration_seconds=0.0,
        )

    exit_code, stdout, stderr, duration = run_proof(proof_command, timeout=timeout)
    evidence_found = bool(evidence_marker) and evidence_marker in stdout

    if exit_code is None:
        reason = stderr or "proof did not complete"
        passed = False
    elif exit_code != 0:
        reason = f"proof command exited {exit_code} (capability not built / could not self-drive)"
        passed = False
    elif not evidence_found:
        reason = f"proof ran but did not emit evidence marker {evidence_marker!r}"
        passed = False
    else:
        reason = "self-drove to a proof emitting the evidence marker"
        passed = True

    return QuestionResult(
        id=question_id,
        archetype=str(row.get("archetype", "")),
        phase=str(row.get("phase", "")),
        symptom=str(row.get("symptom", "")),
        driver=driver,
        proof_command=proof_command,
        passed=passed,
        reason=reason,
        exit_code=exit_code,
        evidence_marker=evidence_marker,
        evidence_found=evidence_found,
        duration_seconds=duration,
        stdout_tail=stdout[-600:],
        stderr_tail=stderr[-600:],
    )


def build_summary(
    question_results: list[QuestionResult],
    component_results: list[ComponentResult],
    *,
    questions_path: Path,
) -> DeitySummary:
    passed = sum(1 for r in question_results if r.passed)
    total = len(question_results)
    built = sum(1 for c in component_results if c.built)
    unbuilt = len(component_results) - built
    failed_questions = total - passed
    gap_actions = failed_questions + unbuilt
    return DeitySummary(
        generated_at=utc_now(),
        questions_path=repo_rel(questions_path),
        question_count=total,
        questions_passed=passed,
        questions_failed=failed_questions,
        pass_rate=round(passed / total, 3) if total else 0.0,
        component_count=len(component_results),
        components_built=built,
        components_unbuilt=unbuilt,
        deity_ready=(failed_questions == 0 and unbuilt == 0),
        deity_gap_actions=gap_actions,
        questions=[asdict(r) for r in question_results],
        components=[asdict(c) for c in component_results],
    )


def write_markdown(path: Path, summary: DeitySummary) -> None:
    lines = [
        "# Debugger Deity-Mode Benchmark Baseline",
        "",
        f"- Generated: {summary.generated_at}",
        f"- Questions path: {summary.questions_path}",
        f"- Questions: {summary.question_count}",
        f"- Passed: {summary.questions_passed}",
        f"- Failed: {summary.questions_failed}",
        f"- Pass rate: {summary.pass_rate:.3f}",
        f"- Components built: {summary.components_built}/{summary.component_count}",
        f"- deity_ready: {summary.deity_ready}",
        f"- deity_gap_actions: {summary.deity_gap_actions}",
        "",
        "A question passes only when its `driver: auto` proof command runs to",
        "exit 0 AND emits its evidence marker — i.e. the debugger self-drove the",
        "proof with no hand-supplied state/trace/scenario. The godmode triad",
        "(audit 11/11, godmode benchmark 29/29, and the all-green selftest gate)",
        "is the frozen floor and is not scored here.",
        "",
        "## Capability components",
        "",
        "| component | phase | built |",
        "| --- | --- | --- |",
    ]
    for c in summary.components:
        lines.append(f"| {c['name']} | {c['phase']} | {'yes' if c['built'] else 'no'} |")
    lines.extend(
        [
            "",
            "## Question results",
            "",
            "| id | phase | pass | reason |",
            "| --- | --- | --- | --- |",
        ]
    )
    for q in summary.questions:
        lines.append(
            f"| {q['id']} | {q['phase']} | {'PASS' if q['passed'] else 'FAIL'} | {q['reason']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_self_test() -> int:
    """Verify the scorer logic with synthetic pass/fail proofs (no ROM/emulator)."""
    ok_marker = "SYNTH-DEITY-OK"
    passing = {
        "id": "synth_pass",
        "archetype": "WHAT",
        "phase": "0",
        "symptom": "synthetic passing proof",
        "driver": "auto",
        "proof_command": f'python -c "print(\'{ok_marker}\')"',
        "evidence_marker": ok_marker,
    }
    failing_exit = {
        "id": "synth_fail_exit",
        "archetype": "WHAT",
        "phase": "0",
        "symptom": "synthetic failing proof (nonzero exit)",
        "driver": "auto",
        "proof_command": 'python -c "import sys; sys.exit(3)"',
        "evidence_marker": ok_marker,
    }
    failing_marker = {
        "id": "synth_fail_marker",
        "archetype": "WHAT",
        "phase": "0",
        "symptom": "synthetic proof missing its evidence marker",
        "driver": "auto",
        "proof_command": 'python -c "print(\'nope\')"',
        "evidence_marker": ok_marker,
    }
    not_auto = {
        "id": "synth_not_auto",
        "archetype": "WHAT",
        "phase": "0",
        "symptom": "row that is not driver:auto must not pass",
        "driver": "manual",
        "proof_command": f'python -c "print(\'{ok_marker}\')"',
        "evidence_marker": ok_marker,
    }

    cases = [
        (passing, True),
        (failing_exit, False),
        (failing_marker, False),
        (not_auto, False),
    ]
    failures: list[str] = []
    for row, expected in cases:
        result = score_question(row, timeout=30)
        if result.passed != expected:
            failures.append(
                f"{row['id']}: expected passed={expected}, got {result.passed} ({result.reason})"
            )

    # Component detection: a name registered in selftest is built; a bogus name is not.
    registered = selftest_component_names()
    if not registered:
        failures.append("selftest registry came back empty")
    if "definitely_not_a_real_component_xyz" in registered:
        failures.append("bogus component name unexpectedly registered")

    # Summary math: 1 pass / 3 fail + all-unbuilt components -> not ready.
    results = [score_question(row, timeout=30) for row, _ in cases]
    components = [ComponentResult(name=n, phase=p, built=(n in registered)) for n, p in DEITY_COMPONENTS]
    summary = build_summary(results, components, questions_path=DEFAULT_QUESTIONS)
    if summary.questions_passed != 1 or summary.questions_failed != 3:
        failures.append(f"summary question math wrong: {summary.questions_passed}/{summary.questions_failed}")
    if summary.deity_ready:
        failures.append("deity_ready should be False at baseline component state")
    expected_gap = summary.questions_failed + summary.components_unbuilt
    if summary.deity_gap_actions != expected_gap:
        failures.append(f"gap math wrong: {summary.deity_gap_actions} != {expected_gap}")

    if failures:
        print("SELF-TEST FAIL:")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("SELF-TEST PASS: deity scorer logic verified (pass/fail/auto-gate/component-detect/summary).")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score python -m tools.debugger against the deity-mode (self-driving) bar.",
    )
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--markdown-out", type=Path)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Exit 0 after recording scores even when deity_ready is False.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Verify the scorer's own logic with synthetic proofs and exit.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.self_test:
        return run_self_test()

    questions_path = args.questions if args.questions.is_absolute() else ROOT / args.questions
    out_path = args.out if args.out.is_absolute() else ROOT / args.out
    markdown_path = None
    if args.markdown_out is not None:
        markdown_path = args.markdown_out if args.markdown_out.is_absolute() else ROOT / args.markdown_out

    questions = load_questions(questions_path)
    registered = selftest_component_names()

    question_results = [score_question(row, timeout=args.timeout) for row in questions]
    component_results = [
        ComponentResult(name=name, phase=phase, built=(name in registered))
        for name, phase in DEITY_COMPONENTS
    ]
    summary = build_summary(question_results, component_results, questions_path=questions_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(asdict(summary), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if markdown_path is not None:
        write_markdown(markdown_path, summary)

    for q in question_results:
        print(f"{'PASS' if q.passed else 'FAIL'} {q.id} (phase {q.phase}): {q.reason}")
    for c in component_results:
        print(f"{'BUILT  ' if c.built else 'UNBUILT'} component {c.name} (phase {c.phase})")

    print(
        "debugger_deity_mode: "
        f"questions={summary.question_count} passed={summary.questions_passed} "
        f"failed={summary.questions_failed} pass_rate={summary.pass_rate:.3f} "
        f"components_built={summary.components_built}/{summary.component_count}"
    )
    print(f"deity_ready={summary.deity_ready} deity_gap_actions={summary.deity_gap_actions}")
    print(f"json_out={repo_rel(out_path)}")
    if markdown_path is not None:
        print(f"markdown_out={repo_rel(markdown_path)}")

    if not args.baseline and not summary.deity_ready:
        print("FAIL: deity_ready is False. Re-run with --baseline to record a known-low baseline.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
