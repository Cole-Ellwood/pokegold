from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REPORT_PATH = ROOT / ".local" / "tmp" / "boss_ai_debugger" / "done_gate.json"


@dataclass(frozen=True)
class GateCommand:
    gate_id: str
    command: list[str]
    requirement: str


GATE_COMMANDS = (
    GateCommand(
        "debugger_unit_tests",
        [sys.executable, "-m", "unittest", "discover", "tools\\boss_ai_debugger\\tests"],
        "debugger unit and integration test coverage",
    ),
    GateCommand(
        "no_cheat",
        [sys.executable, "tools\\audit\\check_boss_ai_no_cheat.py"],
        "hidden-info and no-cheat boundary",
    ),
    GateCommand(
        "gating",
        [sys.executable, "tools\\audit\\check_boss_ai_gating.py"],
        "Boss AI feature gating invariants",
    ),
    GateCommand(
        "trace_invariants",
        [sys.executable, "tools\\audit\\check_boss_ai_trace_invariants.py"],
        "trace hooks and policy/source invariants",
    ),
    GateCommand(
        "live_capture_ledger",
        [sys.executable, "tools\\audit\\check_boss_ai_live_capture_ledger.py"],
        "pinned live trace corpus and manifest",
    ),
    GateCommand(
        "selector_replay",
        [sys.executable, "tools\\audit\\check_boss_ai_selector_replay.py"],
        "exact selector replay from captured final score bytes",
    ),
    GateCommand(
        "pre_choice_replay",
        [sys.executable, "tools\\audit\\check_boss_ai_pre_choice_replay.py"],
        "pre-choice replay from manifest states",
    ),
    GateCommand(
        "debugger_foundations",
        [sys.executable, "tools\\audit\\check_boss_ai_debugger_foundations.py"],
        "canonical schema, rule map, generated stress, analysis, trust tools",
    ),
    GateCommand(
        "debugger_performance",
        [sys.executable, "tools\\audit\\check_boss_ai_debugger_performance.py"],
        "scenario throughput and review queue throughput",
    ),
    GateCommand(
        "changed_ai_suite",
        [
            sys.executable,
            "-m",
            "tools.boss_ai_debugger",
            "run-suite",
            "--profile",
            "changed-ai",
            "--count",
            "24",
            "--seed",
            "1",
            "--runs-dir",
            ".local\\tmp\\boss_ai_debugger\\changed_ai_runs",
            "--refresh-rom-contribution-trace",
            "--refresh-rom-score-materialization",
            "--rebuild-roms",
            "--refresh-live-traces",
        ],
        "changed-AI rebuild, live trace refresh, ROM score materialization, and run lineage",
    ),
    GateCommand(
        "docs_navigation",
        [sys.executable, "tools\\audit\\check_docs_navigation.py"],
        "docs and generated-index integration",
    ),
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the Boss AI debugger definition-of-done gate."
    )
    parser.add_argument("--json-out", type=Path, default=REPORT_PATH)
    parser.add_argument("--generated-count", type=int, default=24)
    parser.add_argument("--skip-slow-replay", action="store_true")
    parser.add_argument("--skip-changed-ai-suite", action="store_true")
    args = parser.parse_args()

    report = build_done_gate_report(
        generated_count=args.generated_count,
        skip_slow_replay=args.skip_slow_replay,
        skip_changed_ai_suite=args.skip_changed_ai_suite,
    )
    write_json(report, args.json_out)
    print(format_done_gate_report(report))
    print(f"wrote {display_path(args.json_out)}")
    return 0 if report["passed"] else 1


def build_done_gate_report(
    *,
    generated_count: int,
    skip_slow_replay: bool,
    skip_changed_ai_suite: bool,
) -> dict[str, Any]:
    started = time.perf_counter()
    commands = [
        command
        for command in GATE_COMMANDS
        if not (skip_slow_replay and command.gate_id == "pre_choice_replay")
        and not (
            skip_changed_ai_suite and command.gate_id == "changed_ai_suite"
        )
    ]
    command_results = [run_gate_command(command) for command in commands]
    roadmap = run_roadmap_audit(generated_count=generated_count)
    elapsed = time.perf_counter() - started
    failed_commands = [
        result for result in command_results if int(result["returncode"]) != 0
    ]
    passed = not failed_commands and roadmap["ready"]
    return {
        "schema_version": 1,
        "kind": "boss_ai_debugger_done_gate",
        "passed": passed,
        "elapsed_seconds": elapsed,
        "command_count": len(command_results),
        "failed_command_count": len(failed_commands),
        "commands": command_results,
        "roadmap_ready": roadmap["ready"],
        "roadmap_status_counts": roadmap["status_counts"],
        "roadmap_blocking_gap_count": roadmap["blocking_gap_count"],
        "roadmap_blocking_gaps": roadmap["blocking_gaps"],
        "requirements": done_requirements(),
    }


def run_gate_command(command: GateCommand) -> dict[str, Any]:
    started = time.perf_counter()
    completed = subprocess.run(
        command.command,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - started
    return {
        "gate_id": command.gate_id,
        "requirement": command.requirement,
        "command": command.command,
        "returncode": completed.returncode,
        "elapsed_seconds": elapsed,
        "stdout_tail": tail(completed.stdout),
        "stderr_tail": tail(completed.stderr),
    }


def run_roadmap_audit(*, generated_count: int) -> dict[str, Any]:
    from tools.audit.check_boss_ai_debugger_roadmap import build_roadmap_audit

    return build_roadmap_audit(
        generated_count=generated_count,
        seed=1,
        check_rom_selector_materialization=True,
        check_rom_score_materialization=True,
    )


def done_requirements() -> list[dict[str, str]]:
    return [
        {
            "requirement": "ROM accuracy",
            "evidence": "selector replay, pre-choice replay, live capture ledger, roadmap materialization checks",
        },
        {
            "requirement": "coverage",
            "evidence": "debugger foundation audit, rule map, roadmap coverage gaps",
        },
        {
            "requirement": "public-info safety",
            "evidence": "no-cheat, gating, trace invariants, roadmap provenance status",
        },
        {
            "requirement": "performance",
            "evidence": "debugger performance audit plus roadmap ROM-backed replay status",
        },
        {
            "requirement": "workflow integration",
            "evidence": "docs navigation, generated index, changed-AI suite coverage and final-gate command artifact",
        },
    ]


def format_done_gate_report(report: dict[str, Any]) -> str:
    lines = [
        "Boss AI debugger done gate",
        (
            f"passed={report['passed']} commands={report['command_count']} "
            f"failed_commands={report['failed_command_count']} "
            f"roadmap_ready={report['roadmap_ready']} "
            f"blocking_gaps={report['roadmap_blocking_gap_count']}"
        ),
    ]
    failed = [item for item in report["commands"] if int(item["returncode"]) != 0]
    if failed:
        lines.append("")
        lines.append("Failed commands:")
        for item in failed:
            lines.append(f"  - {item['gate_id']}: returncode={item['returncode']}")
    if report["roadmap_blocking_gaps"]:
        lines.append("")
        lines.append("Top roadmap blockers:")
        for gap in report["roadmap_blocking_gaps"][:8]:
            lines.append(f"  - {gap}")
    return "\n".join(lines)


def tail(text: str, *, max_lines: int = 20) -> list[str]:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    return lines[-max_lines:]


def write_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("/", "\\")
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
