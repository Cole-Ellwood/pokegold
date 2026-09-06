"""Reexecute an experiment report; this checks reproduction, not bug intent."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.debugger.runtime_experiment import replay_experiment_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        result = replay_experiment_report(args.report)
    except (ValueError, KeyError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
