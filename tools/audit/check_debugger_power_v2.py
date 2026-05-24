#!/usr/bin/env python3
"""Validate the debugger-power V2 upgrade.

V2 measures the surfaces that the saturated godmode benchmark cannot:

* old 29-question benchmark stays green while avoiding unnecessary investigate
  runs when `next` already satisfies the contract;
* ordinary wrong-switch phrasing routes to the exact Boss AI materializer lane;
* safe proof cards can execute real local proof commands, not only print plans.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES = ROOT / "audit" / "debugger_power_v2" / "questions.jsonl"
DEFAULT_OUT = ROOT / ".local" / "tmp" / "debugger_power_v2.json"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"FAIL: {path}:{line_no}: invalid JSONL: {exc}") from exc
    if not rows:
        raise SystemExit(f"FAIL: no V2 proof cases found in {path}")
    return rows


def run_json(command: list[str], *, json_path: Path, timeout: int) -> tuple[dict[str, Any], float]:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    proc = subprocess.run(
        [*command, "--json-out", str(json_path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    elapsed = time.perf_counter() - started
    if proc.returncode != 0:
        raise SystemExit(
            "FAIL: command exited "
            f"{proc.returncode}: {' '.join(command)}\n"
            f"{proc.stdout[-1200:]}\n{proc.stderr[-1200:]}"
        )
    return json.loads(json_path.read_text(encoding="utf-8")), elapsed


def run_benchmark(*, json_path: Path, timeout: int) -> tuple[dict[str, Any], float]:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "tools/audit/check_debugger_godmode_benchmark.py",
        "--out",
        str(json_path),
    ]
    started = time.perf_counter()
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    elapsed = time.perf_counter() - started
    if proc.returncode != 0:
        raise SystemExit(
            "FAIL: command exited "
            f"{proc.returncode}: {' '.join(command)}\n"
            f"{proc.stdout[-1200:]}\n{proc.stderr[-1200:]}"
        )
    return json.loads(json_path.read_text(encoding="utf-8")), elapsed


def proof_command_text(proof: dict[str, Any]) -> str:
    commands = [str(proof.get("chosen_command", ""))]
    for candidate in proof.get("command_candidates", []):
        if isinstance(candidate, dict):
            commands.append(str(candidate.get("command", "")))
    return "\n".join(commands)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--benchmark-max-seconds", type=float, default=60.0)
    parser.add_argument("--prove-timeout", type=int, default=120)
    args = parser.parse_args(argv)

    cases_path = args.cases if args.cases.is_absolute() else ROOT / args.cases
    out_path = args.out if args.out.is_absolute() else ROOT / args.out
    cases = load_jsonl(cases_path)

    benchmark_out = ROOT / ".local" / "tmp" / "debugger_power_v2_godmode.json"
    benchmark, benchmark_elapsed = run_benchmark(
        json_path=benchmark_out,
        timeout=int(max(args.benchmark_max_seconds, 10) + 30),
    )
    errors: list[str] = []
    if benchmark.get("pass_rate") != 1.0:
        errors.append(f"godmode benchmark pass_rate={benchmark.get('pass_rate')} expected 1.0")
    if benchmark.get("investigate_run_count", 999) > 0:
        errors.append(
            "godmode benchmark should short-circuit investigate when next passes; "
            f"investigate_run_count={benchmark.get('investigate_run_count')}"
        )
    if benchmark_elapsed > args.benchmark_max_seconds:
        errors.append(
            f"godmode benchmark took {benchmark_elapsed:.3f}s, max {args.benchmark_max_seconds:.3f}s"
        )

    proof_results = []
    for index, row in enumerate(cases, 1):
        proof_path = ROOT / ".local" / "tmp" / f"debugger_power_v2_proof_{index:02d}_{row['id']}.json"
        proof, _elapsed = run_json(
            [
                sys.executable,
                "-m",
                "tools.debugger",
                "prove",
                "--symptom",
                row["symptom"],
                "--execute",
                "--timeout-seconds",
                str(args.prove_timeout),
            ],
            json_path=proof_path,
            timeout=args.prove_timeout + 10,
        )
        proof_results.append(proof)
        if proof.get("symptom_class") != row["expected_class"]:
            errors.append(
                f"{row['id']}: symptom_class={proof.get('symptom_class')} "
                f"expected {row['expected_class']}"
            )
        if row["min_proof_depth"] == "executed" and proof.get("proof_depth") != "executed":
            errors.append(f"{row['id']}: proof_depth={proof.get('proof_depth')} expected executed")
        if row["expected_command"] not in proof_command_text(proof):
            errors.append(
                f"{row['id']}: chosen_command={proof.get('chosen_command')!r} "
                f"expected to contain {row['expected_command']!r}"
            )
        if proof.get("executed") and not proof.get("passed"):
            errors.append(f"{row['id']}: executed proof failed")

    executed_count = sum(1 for proof in proof_results if proof.get("proof_depth") == "executed")
    if executed_count < 5:
        errors.append(f"executed proof cards={executed_count}, expected at least 5")

    summary = {
        "schema_version": 1,
        "kind": "debugger_power_v2_audit",
        "valid": not errors,
        "benchmark_elapsed_seconds": round(benchmark_elapsed, 3),
        "benchmark_pass_rate": benchmark.get("pass_rate"),
        "benchmark_investigate_run_count": benchmark.get("investigate_run_count"),
        "proof_case_count": len(cases),
        "executed_proof_count": executed_count,
        "errors": errors,
        "proof_results": proof_results,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print(f"json_out={out_path.relative_to(ROOT).as_posix()}")
        return 1

    print(
        "PASS: debugger power V2 "
        f"benchmark={benchmark_elapsed:.3f}s "
        f"proofs={executed_count}/{len(cases)} "
        f"investigate_runs={benchmark.get('investigate_run_count')}"
    )
    print(f"json_out={out_path.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
