#!/usr/bin/env python3
"""Fail unless the omni-debugger v2 selftest passes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.debugger.selftest import SelftestReport, run_selftest


def build_audit_report(selftest: SelftestReport | None = None) -> dict[str, Any]:
    """Return a compact audit report for the debugger selftest."""

    report = selftest if selftest is not None else run_selftest()
    data = report.to_jsonable()
    failed = [item for item in data["results"] if not item["ok"]]
    return {
        "schema_version": 1,
        "kind": "debugger_selftest_audit",
        "passed": bool(data["ok"]),
        "component_count": data["components_total"],
        "failed_component_count": data["components_failed"],
        "components": data["results"],
        "failed_components": failed,
    }


def format_audit_report(report: dict[str, Any]) -> str:
    status = "PASS" if report["passed"] else "FAIL"
    lines = [
        (
            f"Debugger selftest audit {status}: "
            f"{report['component_count'] - report['failed_component_count']}/"
            f"{report['component_count']} components healthy"
        )
    ]
    for component in report["components"]:
        marker = "ok" if component["ok"] else "FAIL"
        detail = component.get("detail") or component.get("error") or ""
        line = f"  [{marker}] {component['component']}"
        if detail:
            line += f" - {detail}"
        lines.append(line)
        if not component["ok"] and component.get("next_command"):
            lines.append(f"       next command: {component['next_command']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the omni-debugger v2 selftest as a standalone audit gate. "
            "This script is intentionally separate from release smoke so v2 "
            "health does not silently redefine the v1 release floor."
        )
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = build_audit_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_audit_report(report))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
