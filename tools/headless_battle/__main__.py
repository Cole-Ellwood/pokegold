from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .simulator import (
    SimulationInputError,
    format_text,
    load_payload,
    run_self_test,
    scenario_template,
    simulate_payload,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a headless text/JSON Pokemon Gold battle-turn simulation."
    )
    parser.add_argument("--scenario", type=Path, help="JSON scenario file")
    parser.add_argument("--json", action="store_true", help="write JSON report to stdout")
    parser.add_argument("--json-out", type=Path, help="write JSON report to this path")
    parser.add_argument("--template", action="store_true", help="print a minimal scenario template")
    parser.add_argument("--self-test", action="store_true", help="run simulator self-test")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            run_self_test()
            print("Headless battle simulator self-test passed.")
            return 0
        if args.template:
            print(json.dumps(scenario_template(), indent=2, sort_keys=True))
            return 0
        if args.scenario is None:
            parser.error("--scenario is required unless --template or --self-test is used")
        report = simulate_payload(load_payload(args.scenario))
        if args.json_out is not None:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(format_text(report))
        return 0
    except SimulationInputError as exc:
        print(f"headless-battle: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
