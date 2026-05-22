#!/usr/bin/env python3
"""Audit SM83 consumers for duplicated shared opcode tables.

P1's end state is one authoritative SM83 model. This audit is deliberately
narrow for the first structural slice: it blocks reintroducing the shared
control/index opcode tables into consumers while the remaining opcode emitters
are migrated incrementally.
"""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
SM83_MODEL_PATH = Path("tools/debugger/sm83_model.py")

SHARED_TABLE_NAMES = frozenset(
    {
        "INDEX_REG",
        "REGISTER_INDEX_TARGETS",
        "CONDITIONAL_CALLS",
        "CONDITIONAL_RETS",
        "CONDITIONAL_JUMPS",
        "RST_TARGETS",
        "CPU_STATE_OPCODES",
    }
)


@dataclass(frozen=True)
class ConsumerIssue:
    path: str
    line: int
    name: str
    message: str

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "line": self.line,
            "name": self.name,
            "message": self.message,
        }


def _target_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        out: list[str] = []
        for item in node.elts:
            out.extend(_target_names(item))
        return out
    return []


def _assignments(tree: ast.AST) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                for name in _target_names(target):
                    out.append((node.lineno, name))
        elif isinstance(node, ast.AnnAssign):
            for name in _target_names(node.target):
                out.append((node.lineno, name))
    return out


def scan_sm83_model_consumers(*, root: Path = ROOT) -> dict[str, Any]:
    issues: list[ConsumerIssue] = []
    debugger_root = root / "tools" / "debugger"
    for path in sorted(debugger_root.rglob("*.py")):
        rel = path.relative_to(root)
        if rel == SM83_MODEL_PATH:
            continue
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text, filename=str(rel))
        except SyntaxError as exc:
            issues.append(
                ConsumerIssue(
                    path=str(rel).replace("\\", "/"),
                    line=exc.lineno or 0,
                    name="<syntax>",
                    message=f"could not parse Python file: {exc.msg}",
                )
            )
            continue
        for line, name in _assignments(tree):
            if name not in SHARED_TABLE_NAMES:
                continue
            issues.append(
                ConsumerIssue(
                    path=str(rel).replace("\\", "/"),
                    line=line,
                    name=name,
                    message=(
                        f"{name} must live in tools.debugger.sm83_model and "
                        "be imported by consumers"
                    ),
                )
            )
    return {
        "ok": not issues,
        "checked_root": str(debugger_root),
        "issue_count": len(issues),
        "issues": [issue.to_jsonable() for issue in issues],
        "guarded_tables": sorted(SHARED_TABLE_NAMES),
    }


def _format_text(report: dict[str, Any]) -> str:
    lines = ["SM83 model consumer audit"]
    lines.append(f"checked: {report['checked_root']}")
    if report["ok"]:
        lines.append("PASS: no duplicated shared opcode tables outside tools/debugger/sm83_model.py")
        return "\n".join(lines)
    lines.append(f"FAIL: {report['issue_count']} duplicated shared opcode table assignment(s)")
    for issue in report["issues"]:
        lines.append(
            f"  {issue['path']}:{issue['line']} {issue['name']} - {issue['message']}"
        )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail if SM83 consumers define shared opcode tables locally."
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = scan_sm83_model_consumers()
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(_format_text(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
