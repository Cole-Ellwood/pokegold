#!/usr/bin/env python3
"""Fail unless the unified debugger capability audit is ready."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.debugger.catalog import build_capability_report


def main() -> int:
    report = build_capability_report()
    print(
        "Unified debugger readiness: "
        f"ready={report['ready']} "
        f"status_counts={report['status_counts']} "
        f"blocking_gaps={report['blocking_gap_count']}"
    )
    if report["ready"]:
        return 0

    for gap in report["blocking_gaps"][:5]:
        print(f"BLOCKER: {gap}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
