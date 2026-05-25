from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .formatters import FORMATTERS


def add_output_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--json-out", default="")


def emit_report(report: dict[str, Any], args: argparse.Namespace) -> None:
    if args.json_out:
        write_json(report, Path(args.json_out))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    formatter = FORMATTERS.get(report["kind"])
    if formatter is not None:
        print(formatter(report))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))


def write_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
    return rows
