#!/usr/bin/env python3
"""Audit SM83 consumers for shared-table dispatch sites.

P1's end state is one authoritative SM83 model. This audit keeps the current
consumer dispatch sites explicit while future migration slices burn them down.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
SM83_MODEL_PATH = Path("tools/debugger/sm83_model.py")

MIGRATION_INTENT_MARKER = "Migration-intent: sm83_shared_tables_hold"

SHARED_TABLE_FAMILIES = {
    "INDEX_REG": "register_index",
    "REGISTER_INDEX_TARGETS": "register_index",
    "CONDITIONAL_CALLS": "control_flow",
    "CONDITIONAL_RETS": "control_flow",
    "CONDITIONAL_JUMPS": "control_flow",
    "RST_TARGETS": "control_flow",
    "CPU_STATE_OPCODES": "cpu_state",
}
SHARED_TABLE_NAMES = frozenset(SHARED_TABLE_FAMILIES)

ALLOWLIST: dict[tuple[str, str, str], dict[str, int]] = {
    ("tools/debugger/effect_trace.py", "alu_register_write_effects", "register_index"): {"count": 1},
    ("tools/debugger/effect_trace.py", "alu_source_label", "register_index"): {"count": 1},
    ("tools/debugger/effect_trace.py", "control_effects", "control_flow"): {"count": 8},
    ("tools/debugger/effect_trace.py", "control_effects", "cpu_state"): {"count": 1},
    ("tools/debugger/effect_trace.py", "event_takes_control_flow", "control_flow"): {"count": 10},
    ("tools/debugger/effect_trace.py", "memory_read_effects", "control_flow"): {"count": 2},
    ("tools/debugger/effect_trace.py", "memory_read_effects", "register_index"): {"count": 2},
    ("tools/debugger/effect_trace.py", "memory_write_effects", "control_flow"): {"count": 3},
    ("tools/debugger/effect_trace.py", "memory_write_effects", "register_index"): {"count": 1},
    ("tools/debugger/effect_trace.py", "register_write_effects", "control_flow"): {"count": 5},
    ("tools/debugger/effect_trace.py", "register_write_effects", "register_index"): {"count": 1},
    ("tools/debugger/dynamic_taint.py", "alu_register_write_records", "register_index"): {"count": 1},
    ("tools/debugger/dynamic_taint.py", "alu_source_label", "register_index"): {"count": 1},
    ("tools/debugger/dynamic_taint.py", "instruction_memory_writes", "control_flow"): {"count": 3},
    ("tools/debugger/dynamic_taint.py", "instruction_register_writes_for_attribution", "control_flow"): {"count": 5},
    ("tools/debugger/dynamic_taint.py", "instruction_register_writes_for_attribution", "register_index"): {"count": 1},
}


AllowlistKey = tuple[str, str, str]


@dataclass(frozen=True)
class ConsumerIssue:
    path: str
    line: int
    name: str
    function: str
    dispatch_family: str
    message: str
    observed_count: int | None = None
    expected_count: int | None = None

    def to_jsonable(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "path": self.path,
            "line": self.line,
            "name": self.name,
            "function": self.function,
            "dispatch_family": self.dispatch_family,
            "message": self.message,
        }
        if self.observed_count is not None:
            out["observed_count"] = self.observed_count
        if self.expected_count is not None:
            out["expected_count"] = self.expected_count
        return out


@dataclass(frozen=True)
class DispatchSite:
    path: str
    function: str
    dispatch_family: str
    name: str
    line: int


@dataclass(frozen=True)
class FunctionSpan:
    name: str
    start: int
    end: int


@dataclass(frozen=True)
class ModuleStore:
    path: str
    name: str
    line: int


class _DispatchSiteVisitor(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path
        self.scope: list[str] = []
        self.sites: list[DispatchSite] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load) and node.id in SHARED_TABLE_NAMES:
            self._add(node, node.id)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in SHARED_TABLE_NAMES:
            self._add(node, node.attr)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = _shared_table_name(node.func)
        if name:
            self._add(node, name)
            for arg in node.args:
                self.visit(arg)
            for keyword in node.keywords:
                if keyword.value is not None:
                    self.visit(keyword.value)
            return
        self.generic_visit(node)

    def _add(self, node: ast.AST, name: str) -> None:
        if not self.scope:
            return
        self.sites.append(
            DispatchSite(
                path=self.path,
                function=".".join(self.scope),
                dispatch_family=SHARED_TABLE_FAMILIES[name],
                name=name,
                line=getattr(node, "lineno", 0),
            )
        )


class _FunctionSpanVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.scope: list[str] = []
        self.spans: list[FunctionSpan] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.scope.append(node.name)
        self.spans.append(
            FunctionSpan(
                name=".".join(self.scope),
                start=node.lineno,
                end=getattr(node, "end_lineno", node.lineno),
            )
        )
        self.generic_visit(node)
        self.scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef


def _shared_table_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name) and node.id in SHARED_TABLE_NAMES:
        return node.id
    if isinstance(node, ast.Attribute) and node.attr in SHARED_TABLE_NAMES:
        return node.attr
    return ""


class _ModuleStoreVisitor(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path
        self.stores: list[ModuleStore] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        return

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store) and node.id in SHARED_TABLE_NAMES:
            self.stores.append(ModuleStore(path=self.path, name=node.id, line=node.lineno))


def _scan_module_stores(tree: ast.AST, *, path: str) -> list[ModuleStore]:
    visitor = _ModuleStoreVisitor(path)
    visitor.visit(tree)
    return visitor.stores


def _scan_dispatch_sites(tree: ast.AST, *, path: str) -> list[DispatchSite]:
    visitor = _DispatchSiteVisitor(path)
    visitor.visit(tree)
    return visitor.sites


def _function_spans(tree: ast.AST) -> list[FunctionSpan]:
    visitor = _FunctionSpanVisitor()
    visitor.visit(tree)
    return visitor.spans


def _count_dispatch_sites(sites: list[DispatchSite]) -> dict[AllowlistKey, int]:
    counts: dict[AllowlistKey, int] = {}
    for site in sites:
        key = (site.path, site.function, site.dispatch_family)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _first_site(sites: list[DispatchSite], key: AllowlistKey) -> DispatchSite | None:
    for site in sites:
        if (site.path, site.function, site.dispatch_family) == key:
            return site
    return None


def _git_output(root: Path, args: Sequence[str]) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout


def _commit_message(root: Path) -> str:
    return _git_output(root, ("log", "-1", "--format=%B", "HEAD"))


def _changed_line_ranges_from_diff(diff_text: str) -> dict[str, list[range]]:
    paths: dict[str, list[range]] = {}
    current_path = ""
    hunk_re = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_path = line[len("+++ b/") :]
            paths.setdefault(current_path, [])
            continue
        if line.startswith("+++ /dev/null"):
            current_path = ""
            continue
        match = hunk_re.match(line)
        if not match or not current_path:
            continue
        start = int(match.group(1))
        length = int(match.group(2) or "1")
        if length == 0:
            paths[current_path].append(range(start, start + 1))
        else:
            paths[current_path].append(range(start, start + length))
    return paths


def _changed_line_ranges(root: Path, allowlist: dict[AllowlistKey, dict[str, int]]) -> dict[str, list[range]]:
    allowlisted_paths = sorted({path for path, _function, _family in allowlist})
    if not allowlisted_paths:
        return {}
    ranges: dict[str, list[range]] = {}
    slice_base = _git_output(root, ("rev-parse", "--verify", "HEAD^")).strip()
    for args in (
        ("diff", "--unified=0", "--", *allowlisted_paths),
        ("diff", "--cached", "--unified=0", "--", *allowlisted_paths),
        ("diff", "--unified=0", f"{slice_base}..HEAD", "--", *allowlisted_paths) if slice_base else (),
    ):
        if not args:
            continue
        for path, path_ranges in _changed_line_ranges_from_diff(_git_output(root, args)).items():
            ranges.setdefault(path, []).extend(path_ranges)
    return ranges


def _touched_allowlist_keys(
    *,
    root: Path,
    allowlist: dict[AllowlistKey, dict[str, int]],
    parsed_trees: dict[str, ast.AST],
) -> set[AllowlistKey]:
    touched_ranges = _changed_line_ranges(root, allowlist)
    if not touched_ranges:
        return set()
    out: set[AllowlistKey] = set()
    for path, ranges in touched_ranges.items():
        if path not in parsed_trees:
            continue
        spans = _function_spans(parsed_trees[path])
        for span in spans:
            if not any(span.start <= line <= span.end for path_range in ranges for line in path_range):
                continue
            for key in allowlist:
                if key[0] == path and key[1] == span.name:
                    out.add(key)
    return out


def scan_sm83_shared_tables_consumers(
    *,
    root: Path = ROOT,
    allowlist: dict[AllowlistKey, dict[str, int]] | None = None,
    touched_allowlist_keys: set[AllowlistKey] | None = None,
    commit_message: str | None = None,
) -> dict[str, Any]:
    allowlist = ALLOWLIST if allowlist is None else allowlist
    issues: list[ConsumerIssue] = []
    sites: list[DispatchSite] = []
    stores: list[ModuleStore] = []
    parsed_trees: dict[str, ast.AST] = {}
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
                    function="<syntax>",
                    dispatch_family="<syntax>",
                    message=f"could not parse Python file: {exc.msg}",
                )
            )
            continue
        rel_path = str(rel).replace("\\", "/")
        parsed_trees[rel_path] = tree
        stores.extend(_scan_module_stores(tree, path=rel_path))
        sites.extend(_scan_dispatch_sites(tree, path=rel_path))

    for store in stores:
        issues.append(
            ConsumerIssue(
                path=store.path,
                line=store.line,
                name=store.name,
                function="<module>",
                dispatch_family=SHARED_TABLE_FAMILIES[store.name],
                message=(
                    f"{store.name} must not be rebound in a consumer module; "
                    "shared SM83 tables live in tools.debugger.sm83_model"
                ),
            )
        )

    counts = _count_dispatch_sites(sites)
    if touched_allowlist_keys is None:
        touched_allowlist_keys = _touched_allowlist_keys(
            root=root,
            allowlist=allowlist,
            parsed_trees=parsed_trees,
        )
    commit_message = _commit_message(root) if commit_message is None else commit_message
    has_migration_intent = MIGRATION_INTENT_MARKER in commit_message
    migrations: list[dict[str, Any]] = []

    for key in sorted(set(counts) | set(allowlist)):
        path, function, family = key
        observed = counts.get(key, 0)
        expected = int(allowlist.get(key, {}).get("count", 0))
        site = _first_site(sites, key)
        line = site.line if site else 0
        name = site.name if site else "<missing>"
        if key not in allowlist and observed:
            issues.append(
                ConsumerIssue(
                    path=path,
                    line=line,
                    name=name,
                    function=function,
                    dispatch_family=family,
                    message=(
                        "shared-table dispatch site is not in the shrinking allowlist; "
                        "move it through tools.debugger.sm83_model or add an explicit "
                        "dispatch-family allowlist entry"
                    ),
                    observed_count=observed,
                    expected_count=0,
                )
            )
            continue
        if observed > expected:
            issues.append(
                ConsumerIssue(
                    path=path,
                    line=line,
                    name=name,
                    function=function,
                    dispatch_family=family,
                    message="shared-table dispatch-site count increased above the allowlist",
                    observed_count=observed,
                    expected_count=expected,
                )
            )
            continue
        if observed < expected:
            migrations.append(
                {
                    "path": path,
                    "function": function,
                    "dispatch_family": family,
                    "observed_count": observed,
                    "expected_count": expected,
                }
            )
            continue
        if observed == expected and key in touched_allowlist_keys:
            if has_migration_intent:
                migrations.append(
                    {
                        "path": path,
                        "function": function,
                        "dispatch_family": family,
                        "observed_count": observed,
                        "expected_count": expected,
                        "reason": "touched_stable_with_migration_intent",
                    }
                )
                continue
            issues.append(
                ConsumerIssue(
                    path=path,
                    line=line,
                    name=name,
                    function=function,
                    dispatch_family=family,
                    message=(
                        "allowlisted shared-table dispatch site stayed stable in a touched function; include "
                        f"{MIGRATION_INTENT_MARKER!r} in the commit message for an intentional hold"
                    ),
                    observed_count=observed,
                    expected_count=expected,
                )
            )
    return {
        "ok": not issues,
        "checked_root": str(debugger_root),
        "issue_count": len(issues),
        "issues": [issue.to_jsonable() for issue in issues],
        "dispatch_site_count": sum(counts.values()),
        "allowlist_count": len(allowlist),
        "migrations": migrations,
        "migration_intent_marker": MIGRATION_INTENT_MARKER,
        "migration_intent_present": has_migration_intent,
        "touched_allowlist_keys": [
            {"path": path, "function": function, "dispatch_family": family}
            for path, function, family in sorted(touched_allowlist_keys)
        ],
        "guarded_tables": sorted(SHARED_TABLE_NAMES),
    }

def _format_text(report: dict[str, Any]) -> str:
    lines = ["SM83 shared-table consumer audit"]
    lines.append(f"checked: {report['checked_root']}")
    if report["ok"]:
        lines.append("PASS: shared-table dispatch sites match the shrinking allowlist")
        if report.get("migrations"):
            lines.append(f"allowlist reductions or holds: {len(report['migrations'])}")
        return "\n".join(lines)
    lines.append(f"FAIL: {report['issue_count']} shared-table consumer issue(s)")
    for issue in report["issues"]:
        lines.append(
            f"  {issue['path']}:{issue['line']} {issue['function']} "
            f"[{issue['dispatch_family']}] {issue['name']} - {issue['message']}"
        )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail if SM83 shared-table consumer dispatch sites escape the shrinking allowlist."
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = scan_sm83_shared_tables_consumers()
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(_format_text(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
