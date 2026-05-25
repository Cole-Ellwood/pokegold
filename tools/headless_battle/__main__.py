from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .simulator import (
    SimulationInputError,
    format_text,
    load_payload,
    scenario_template,
    simulate_payload,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a headless text/JSON selected-turn battle simulation.")
    parser.add_argument("--template", action="store_true", help="print a starter scenario JSON")
    parser.add_argument("--scenario", type=Path, help="scenario JSON path")
    parser.add_argument("--json", action="store_true", help="print report JSON")
    parser.add_argument("--json-out", type=Path, help="write report JSON to this path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.template:
        print(json.dumps(scenario_template(), indent=2, sort_keys=True))
        return 0
    if args.scenario is None:
        parser.error("--scenario is required unless --template is used")
    try:
        report = simulate_payload(load_payload(args.scenario))
    except SimulationInputError as exc:
        print(f"headless battle simulation failed: {exc}", file=sys.stderr)
        return 2
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
