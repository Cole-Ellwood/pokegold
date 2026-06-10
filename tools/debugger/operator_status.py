from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Sequence

from .catalog import ROOT
from .command_metadata import taxonomy_summary


MAX_STATUS_LINES = 40
MAX_FINDINGS = 5
MAX_QUEUE_ITEMS = 3
BOARD_PATH = Path(".local") / "multi_agent_board.json"
FALLBACK_NEXT_COMMANDS = (
    "python tools\\audit\\check_debugger_literal_anything.py --baseline --read-only",
    "python tools\\audit\\check_boss_ai_debugger_god.py --baseline --read-only",
    "python -m tools.debugger prove --symptom \"<symptom>\"",
)


def build_operator_status(root: Path = ROOT) -> dict[str, Any]:
    latest_run = latest_run_store(root)
    review_queue = review_queue_summary(root, latest_run)
    return {
        "schema_version": 1,
        "kind": "debugger_operator_status",
        "read_only": True,
        "root": str(root),
        "branch": git_stdout(root, "rev-parse", "--abbrev-ref", "HEAD") or "",
        "working_tree": working_tree_status(root),
        "hash_basis": boss_ai_hash_basis(),
        "latest_run_store": latest_run,
        "auto_watch": auto_watch_summary(root),
        "review_queue": review_queue,
        "command_taxonomy": {
            key: value
            for key, value in taxonomy_summary().items()
            if key != "commands"
        },
        "multi_agent_board": multi_agent_board_summary(root),
        "top_next_commands": top_next_commands(review_queue),
    }


def working_tree_status(root: Path) -> dict[str, Any]:
    status = git_stdout(root, "status", "--short") or ""
    lines = [line for line in status.splitlines() if line.strip()]
    return {
        "dirty": bool(lines),
        "line_count": len(lines),
        "tracked_modified": sum(1 for line in lines if len(line) >= 2 and "M" in line[:2]),
        "tracked_added": sum(1 for line in lines if len(line) >= 2 and "A" in line[:2]),
        "tracked_deleted": sum(1 for line in lines if len(line) >= 2 and "D" in line[:2]),
        "untracked": sum(1 for line in lines if line.startswith("??")),
        "shown_lines": lines[:MAX_STATUS_LINES],
        "truncated": len(lines) > MAX_STATUS_LINES,
    }


def latest_run_store(root: Path) -> dict[str, Any]:
    runs_dir = root / "audit" / "boss_ai_debugger" / "runs"
    candidates: list[tuple[str, Path, dict[str, Any]]] = []
    for metadata_path in runs_dir.glob("*/metadata.json"):
        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        candidates.append((str(data.get("created_at", "")), metadata_path, data))
    if not candidates:
        return {"available": False, "path": "", "reason": "no run metadata found"}
    candidates.sort(key=lambda item: (item[0], str(item[1])))
    _, path, data = candidates[-1]
    stale = artifact_hash_mismatches(root, data)
    return {
        "available": True,
        "path": repo_rel(root, path),
        "run_id": str(data.get("run_id", path.parent.name)),
        "profile": str(data.get("profile", "")),
        "created_at": str(data.get("created_at", "")),
        "git_commit": str(data.get("git_commit", "")),
        "batch_summary": data.get("batch_summary", {}),
        "review_queue_summary": data.get("review_queue_summary", {}),
        "known_gaps": list(data.get("known_gaps", []))[:8],
        "stale_artifact_count": len(stale),
        "stale_artifacts": stale[:12],
    }


def artifact_hash_mismatches(root: Path, metadata: dict[str, Any]) -> list[dict[str, str]]:
    artifacts = metadata.get("artifacts", {})
    hashes = metadata.get("artifact_hashes", {})
    if not isinstance(artifacts, dict) or not isinstance(hashes, dict):
        return []
    mismatches: list[dict[str, str]] = []
    for key, artifact_value in artifacts.items():
        expected_value = hashes.get(key)
        for artifact_path, expected in artifact_hash_entries(artifact_value, expected_value):
            path = root / artifact_path
            actual = sha256_file(path)
            if actual != expected:
                mismatches.append(
                    {
                        "artifact": str(key),
                        "path": repo_rel(root, path),
                        "expected_sha256": expected,
                        "actual_sha256": actual,
                    }
                )
    return mismatches


def artifact_hash_entries(artifact_value: Any, expected_value: Any) -> list[tuple[str, str]]:
    if isinstance(artifact_value, str) and isinstance(expected_value, str) and expected_value:
        return [(artifact_value, expected_value)]
    if not isinstance(artifact_value, list) or not isinstance(expected_value, dict):
        return []
    entries: list[tuple[str, str]] = []
    for artifact_path in artifact_value:
        if not isinstance(artifact_path, str):
            continue
        expected = expected_value.get(artifact_path)
        if not isinstance(expected, str) or not expected:
            continue
        entries.append((artifact_path, expected))
    return entries


def auto_watch_summary(root: Path) -> dict[str, Any]:
    path = root / "audit" / "auto_watch_findings.jsonl"
    rows = read_jsonl_tail(path, MAX_FINDINGS)
    return {
        "store": repo_rel(root, path),
        "available": path.exists(),
        "latest_count": len(rows),
        "latest": rows,
    }


def review_queue_summary(root: Path, latest_run: dict[str, Any]) -> dict[str, Any]:
    if not latest_run.get("available"):
        return {"available": False, "items": [], "reason": "no run store"}
    metadata_path = root / str(latest_run.get("path", ""))
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"available": False, "items": [], "reason": "metadata unreadable"}
    artifacts = metadata.get("artifacts", {})
    queue_path_text = artifacts.get("review_queue") if isinstance(artifacts, dict) else ""
    if not isinstance(queue_path_text, str) or not queue_path_text:
        return {"available": False, "items": [], "reason": "run has no review_queue artifact"}
    queue_path = root / queue_path_text
    try:
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"available": False, "items": [], "reason": "review_queue unreadable"}
    items = queue.get("items", []) if isinstance(queue, dict) else []
    return {
        "available": True,
        "path": repo_rel(root, queue_path),
        "returned_count": int(queue.get("returned_count", len(items))) if isinstance(queue, dict) else len(items),
        "items": items[:MAX_QUEUE_ITEMS] if isinstance(items, list) else [],
    }


def top_next_commands(review_queue: dict[str, Any]) -> list[str]:
    commands: list[str] = []
    items = review_queue.get("items", [])
    if isinstance(items, list):
        for item in items[:MAX_QUEUE_ITEMS]:
            command = explain_decision_command(item)
            if command and command not in commands:
                commands.append(command)
    for command in FALLBACK_NEXT_COMMANDS:
        if len(commands) >= MAX_QUEUE_ITEMS:
            break
        if command not in commands:
            commands.append(command)
    return commands


def explain_decision_command(item: Any) -> str:
    if not isinstance(item, dict):
        return ""
    explain = item.get("explain_decision")
    if not isinstance(explain, dict):
        return ""
    command = explain.get("command")
    return str(command) if isinstance(command, str) else ""


def multi_agent_board_summary(root: Path) -> dict[str, Any]:
    path = root / BOARD_PATH
    return {
        "path": repo_rel(root, path),
        "exists": path.exists(),
        "gitignored": git_check_ignored(root, BOARD_PATH),
        "schema_hint": {
            "lane": "string",
            "read_set": ["path"],
            "forbidden_write_set": ["path"],
            "status": "string",
            "commands_in_flight": ["command"],
            "blockers": ["blocker"],
            "handoff_note": "string",
        },
    }


def boss_ai_hash_basis() -> dict[str, Any]:
    try:
        from tools.boss_ai_debugger.commands import boss_ai_trace_hash_basis

        return boss_ai_trace_hash_basis()
    except Exception as exc:  # noqa: BLE001
        return {"ready": False, "status": "unavailable", "error": f"{type(exc).__name__}: {exc}"}


def read_jsonl_tail(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines[-limit:]:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def git_stdout(root: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip()


def git_check_ignored(root: Path, path: Path) -> bool:
    try:
        completed = subprocess.run(
            ["git", "check-ignore", "-q", str(path)],
            cwd=root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return False
    return completed.returncode == 0


def repo_rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def format_operator_status(report: dict[str, Any]) -> str:
    tree = report["working_tree"]
    latest = report["latest_run_store"]
    taxonomy = report["command_taxonomy"]
    lines = [
        "Pokemon Gold debugger operator status",
        f"branch={report['branch']} dirty={tree['dirty']} status_lines={tree['line_count']}",
        (
            "command_taxonomy="
            f"commands={taxonomy['command_count']} "
            f"unknown={taxonomy['side_effect_unknown_command_count']} "
            f"read_only_refused={taxonomy['read_only_refused_count']} "
            f"read_only_enforced={taxonomy.get('read_only_refusal_enforced', False)}"
        ),
        f"hash_basis={report['hash_basis'].get('status', 'unknown')}",
    ]
    if latest.get("available"):
        lines.append(
            "latest_run="
            f"{latest.get('run_id')} profile={latest.get('profile')} "
            f"stale_artifacts={latest.get('stale_artifact_count', 0)}"
        )
    else:
        lines.append(f"latest_run=unavailable reason={latest.get('reason', '')}")
    queue = report["review_queue"]
    lines.append(
        f"review_queue={'available' if queue.get('available') else 'unavailable'} "
        f"items={len(queue.get('items', []))}"
    )
    board = report["multi_agent_board"]
    lines.append(
        f"multi_agent_board={board['path']} exists={board['exists']} gitignored={board['gitignored']}"
    )
    if tree["shown_lines"]:
        lines.extend(["", "Dirty tree sample:"])
        for line in tree["shown_lines"][:12]:
            lines.append(f"  {line}")
    if latest.get("known_gaps"):
        lines.extend(["", "Latest run gaps:"])
        for gap in latest["known_gaps"][:5]:
            lines.append(f"  - {gap}")
    if queue.get("available") and queue.get("items"):
        lines.extend(["", "Top review queue items:"])
        for item in queue["items"][:MAX_QUEUE_ITEMS]:
            if not isinstance(item, dict):
                continue
            scenario_id = str(item.get("scenario_id", ""))
            verdict = str(item.get("verdict", ""))
            priority = str(item.get("priority_score", ""))
            next_action = str(item.get("next_action") or item.get("why") or "")
            command = explain_decision_command(item)
            lines.append(f"  - {scenario_id} verdict={verdict} priority={priority}")
            if next_action:
                lines.append(f"    next={next_action}")
            if command:
                lines.append(f"    command={command}")
    lines.extend(["", "Top next commands:"])
    for command in report["top_next_commands"]:
        lines.append(f"  - {command}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger.operator_status",
        description="Read-only debugger operator status for a fresh agent.",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = build_operator_status()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_operator_status(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
