#!/usr/bin/env python3
"""CLAUDE.md lint enforcement on staged Python additions.

Three rules, scoped to *.py files in the staged diff:

  1. Banned abbreviated identifiers in newly-defined names (function/class
     names, parameters, assignment targets): buf, len, cnt, usr, mgr, proc,
     tmp, cfg. Loop and comprehension targets are exempt.
  2. Duplicate top-level function/class names within the same staged file
     (when the duplicate definition line is in the staged additions).
  3. Commented-out code (heuristic): a "#" comment whose stripped body
     parses as Python AND contains one of: "=", "(", "import", "return",
     "def ", "class ".

Existing tracked code is untouched; only staged additions are scanned.

Exit codes:
  0  clean
  1  one or more violations

Usage: python3 tools/audit/check_claude_md_lint.py
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys


BANNED = frozenset({"buf", "len", "cnt", "usr", "mgr", "proc", "tmp", "cfg"})
CODE_TOKENS = ("=", "(", "import", "return", "def ", "class ")
HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def staged_py_files() -> list[str]:
    out = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=AM"],
        text=True,
    )
    return [p for p in out.splitlines() if p.endswith(".py")]


def staged_added_lines(path: str) -> set[int]:
    """New-file line numbers added in the staged diff for *path*."""
    out = subprocess.check_output(
        ["git", "diff", "--cached", "-U0", "--", path],
        text=True,
    )
    added: set[int] = set()
    new_line = 0
    in_hunk = False
    for raw in out.splitlines():
        m = HUNK_RE.match(raw)
        if m:
            new_line = int(m.group(1))
            in_hunk = True
            continue
        if not in_hunk or raw.startswith("+++"):
            continue
        if raw.startswith("+"):
            added.add(new_line)
            new_line += 1
        elif not raw.startswith("-"):
            new_line += 1
    return added


def staged_content(path: str) -> str:
    return subprocess.check_output(["git", "show", f":{path}"], text=True)


def find_banned_identifiers(tree: ast.AST, added: set[int]) -> list[tuple[int, str]]:
    """Return (lineno, name) for banned-set identifiers defined inside added lines."""
    loop_target_ids: set[int] = set()
    for node in ast.walk(tree):
        target = None
        if isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
            target = node.target
        if target is not None:
            for sub in ast.walk(target):
                if isinstance(sub, ast.Name):
                    loop_target_ids.add(id(sub))

    bad: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.lineno in added and node.name in BANNED:
                bad.append((node.lineno, node.name))
            args = node.args if hasattr(node, "args") and isinstance(getattr(node, "args", None), ast.arguments) else None
            if args is not None:
                pool = list(args.args) + list(args.kwonlyargs) + list(args.posonlyargs)
                if args.vararg:
                    pool.append(args.vararg)
                if args.kwarg:
                    pool.append(args.kwarg)
                for arg in pool:
                    if arg.lineno in added and arg.arg in BANNED:
                        bad.append((arg.lineno, arg.arg))
        elif isinstance(node, ast.Name):
            if (
                isinstance(node.ctx, ast.Store)
                and node.lineno in added
                and node.id in BANNED
                and id(node) not in loop_target_ids
            ):
                bad.append((node.lineno, node.id))
    return bad


def find_duplicate_definitions(tree: ast.AST, added: set[int]) -> list[tuple[int, str]]:
    """Top-level duplicate function/class names where the dup line is staged."""
    seen: dict[str, int] = {}
    dups: list[tuple[int, str]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in seen:
                if node.lineno in added:
                    dups.append((node.lineno, node.name))
            else:
                seen[node.name] = node.lineno
    return dups


def find_commented_code(content: str, added: set[int]) -> list[tuple[int, str]]:
    """`#` comments in staged additions whose stripped body parses as code."""
    out: list[tuple[int, str]] = []
    for i, line in enumerate(content.splitlines(), 1):
        if i not in added:
            continue
        stripped = line.lstrip()
        if not stripped.startswith("#"):
            continue
        body = stripped[1:].lstrip()
        if not body or not any(tok in body for tok in CODE_TOKENS):
            continue
        try:
            ast.parse(body)
        except SyntaxError:
            continue
        out.append((i, body))
    return out


def check_file(path: str) -> list[str]:
    try:
        content = staged_content(path)
    except subprocess.CalledProcessError as exc:
        return [f"{path}: could not read staged content: {exc}"]
    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        return [f"{path}:{exc.lineno}: staged content has syntax error: {exc.msg}"]

    added = staged_added_lines(path)
    if not added:
        return []

    msgs: list[str] = []
    for lineno, name in find_banned_identifiers(tree, added):
        msgs.append(f"{path}:{lineno}: banned abbreviated identifier '{name}'")
    for lineno, name in find_duplicate_definitions(tree, added):
        msgs.append(f"{path}:{lineno}: duplicate top-level definition '{name}'")
    for lineno, body in find_commented_code(content, added):
        msgs.append(f"{path}:{lineno}: commented-out code: {body!r}")
    return msgs


def main() -> int:
    msgs: list[str] = []
    for p in staged_py_files():
        msgs.extend(check_file(p))
    if not msgs:
        return 0
    sys.stderr.write("CLAUDE.md lint: violations in staged Python:\n")
    for m in msgs:
        sys.stderr.write(f"  {m}\n")
    sys.stderr.write(
        "Bypass with CLAUDE_MD_ALLOW_LINT=1 if user requested a deliberate exception.\n"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
