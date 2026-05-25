"""Shared helpers for tools/audit/*.py scripts.

The canonical implementations of helpers that 34 audit files were each
defining locally. Extracted per `audit/non_debugger_code_review_2026-05-26.md` §4.

Two outliers intentionally keep their local copies:

- `check_cheap_difficulty.py` and `check_gym_leader_wiring.py` use a
  list-collecting `fail(failures, message)` rather than the dying
  single-arg form. Different concept; not migrated.
- `bug_hunt_triage.py:strip_comment` adds a trailing `.rstrip()` and
  `check_vram_request_contract.py:code_lines(lines)` returns a dataclass
  list. Different signatures; not migrated.

ROOT is exported so audits can drop their local boilerplate, but local
`ROOT = Path(__file__).resolve().parents[2]` declarations remain valid.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load(path: Path) -> str:
    if not path.exists():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8", errors="replace")


def strip_comment(line: str) -> str:
    if ";" in line:
        return line.split(";", 1)[0]
    return line


def code_lines(text: str) -> list[str]:
    return [strip_comment(line).rstrip() for line in text.splitlines()]
