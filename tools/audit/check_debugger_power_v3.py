#!/usr/bin/env python3
"""Validate the debugger-power V3 proof-campaign upgrade."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES = ROOT / "audit" / "debugger_power_v3" / "questions.jsonl"
DEFAULT_OUT = ROOT / ".local" / "tmp" / "debugger_power_v3.json"


def run_command(command: list[str], *, timeout: int) -> tuple[subprocess.CompletedProcess[str], float]:
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
    return proc, time.perf_counter() - started


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def command_text(command: list[str]) -> str:
    return " ".join(command)


def require_command(command: list[str], *, timeout: int) -> tuple[float, str]:
    proc, elapsed = run_command(command, timeout=timeout)
    if proc.returncode != 0:
        raise SystemExit(
            "FAIL: command exited "
            f"{proc.returncode}: {command_text(command)}\n"
            f"{proc.stdout[-1200:]}\n{proc.stderr[-1200:]}"
        )
    return elapsed, proc.stdout


def run_godmode(timeout: int) -> tuple[dict[str, Any], float]:
    out = ROOT / ".local" / "tmp" / "debugger_power_v3_godmode.json"
    elapsed, _stdout = require_command(
        [
            sys.executable,
            "tools/audit/check_debugger_godmode_benchmark.py",
            "--out",
            str(out),
        ],
        timeout=timeout,
    )
    return load_json(out), elapsed


def run_campaign(cases: Path, *, timeout: int, max_commands: int) -> tuple[dict[str, Any], float]:
    out = ROOT / ".local" / "tmp" / "debugger_power_v3_campaign.json"
    elapsed, _stdout = require_command(
        [
            sys.executable,
            "-m",
            "tools.debugger",
            "prove",
            "--suite",
            str(cases),
            "--all-routes",
            "--execute",
            "--timeout-seconds",
            "120",
            "--max-commands",
            str(max_commands),
            "--json-out",
            str(out),
        ],
        timeout=timeout,
    )
    return load_json(out), elapsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--max-seconds", type=float, default=90.0)
    parser.add_argument("--max-commands", type=int, default=50)
    args = parser.parse_args(argv)

    cases_path = args.cases if args.cases.is_absolute() else ROOT / args.cases
    out_path = args.out if args.out.is_absolute() else ROOT / args.out
    started = time.perf_counter()

    errors: list[str] = []

    v2_elapsed, _stdout = require_command(
        [sys.executable, "tools/audit/check_debugger_power_v2.py"],
        timeout=120,
    )
    v2 = load_json(ROOT / ".local" / "tmp" / "debugger_power_v2.json")
    if not v2.get("valid"):
        errors.append("V2 audit is not valid")

    godmode, godmode_elapsed = run_godmode(timeout=120)
    if godmode.get("pass_rate") != 1.0:
        errors.append(f"godmode pass_rate={godmode.get('pass_rate')} expected 1.0")
    if godmode.get("investigate_run_count") != 0:
        errors.append(
            f"godmode investigate_run_count={godmode.get('investigate_run_count')} expected 0"
        )

    campaign, campaign_elapsed = run_campaign(
        cases_path,
        timeout=120,
        max_commands=args.max_commands,
    )
    status_counts = campaign.get("status_counts", {})
    blocked_total = sum(campaign.get("blocked_reason_counts", {}).values())

    if not campaign.get("valid"):
        errors.append("proof campaign reported valid=False")
    if campaign.get("route_row_count", 0) < 35:
        errors.append(f"route rows classified={campaign.get('route_row_count')} expected >=35")
    if campaign.get("classified_symptom_class_count", 0) < 20:
        errors.append(
            "classified symptom classes="
            f"{campaign.get('classified_symptom_class_count')} expected >=20"
        )
    if campaign.get("executed_unique_command_count", 0) < 18:
        errors.append(
            "executed unique commands="
            f"{campaign.get('executed_unique_command_count')} expected >=18"
        )
    if status_counts.get("discrepancy_found", 0) < 1:
        errors.append("expected at least one discrepancy_found proof")
    if blocked_total < 10:
        errors.append(f"blocked commands={blocked_total} expected >=10")
    if campaign.get("unsafe_execution_attempts") != 0:
        errors.append(
            f"unsafe execution attempts={campaign.get('unsafe_execution_attempts')} expected 0"
        )

    elapsed_total = time.perf_counter() - started
    if elapsed_total > args.max_seconds:
        errors.append(f"V3 audit took {elapsed_total:.3f}s, max {args.max_seconds:.3f}s")

    summary = {
        "schema_version": 1,
        "kind": "debugger_power_v3_audit",
        "valid": not errors,
        "elapsed_seconds": round(elapsed_total, 3),
        "v2_elapsed_seconds": round(v2_elapsed, 3),
        "godmode_elapsed_seconds": round(godmode_elapsed, 3),
        "campaign_elapsed_seconds": round(campaign_elapsed, 3),
        "godmode_pass_rate": godmode.get("pass_rate"),
        "godmode_investigate_run_count": godmode.get("investigate_run_count"),
        "route_row_count": campaign.get("route_row_count"),
        "classified_symptom_class_count": campaign.get("classified_symptom_class_count"),
        "executed_unique_command_count": campaign.get("executed_unique_command_count"),
        "status_counts": status_counts,
        "blocked_reason_counts": campaign.get("blocked_reason_counts"),
        "errors": errors,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print(f"json_out={out_path.relative_to(ROOT).as_posix()}")
        return 1

    print(
        "PASS: debugger power V3 "
        f"elapsed={elapsed_total:.3f}s "
        f"executed={campaign.get('executed_unique_command_count')} "
        f"routes={campaign.get('route_row_count')} "
        f"discrepancies={status_counts.get('discrepancy_found', 0)}"
    )
    print(f"json_out={out_path.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
