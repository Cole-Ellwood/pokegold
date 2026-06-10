from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.debugger.report_envelope import build_report_envelope, sha256_file

from .simulator import coverage_report


ROOT = Path(__file__).resolve().parents[2]
WORKLIST_KIND = "headless_battle_promoted_turn_differential_worklist"
WORKLIST_ROW_KIND = "headless_battle_promoted_turn_differential_worklist_row"
WORKLIST_EVIDENCE_ID = "headless_battle_promoted_turn_differential_worklist.cataloged"
REMAINING_TURN_DIFFERENTIAL_GAP = "remaining_promoted_mechanic_turn_differentials"
DEFAULT_OUT = ROOT / "audit" / "headless_battle" / "promoted_turn_differential_worklist.json"


def build_worklist(*, root: Path = ROOT) -> dict[str, Any]:
    coverage = coverage_report()
    pending_rows = coverage.get("source_mirrored_pending_differential", [])
    if not isinstance(pending_rows, list):
        pending_rows = []
    byte_proven_rows = coverage.get("byte_proven", [])
    if not isinstance(byte_proven_rows, list):
        byte_proven_rows = []

    rows = [
        {
            "kind": WORKLIST_ROW_KIND,
            "id": str(row.get("id", "")),
            "source": str(row.get("source", "")),
            "gate": str(row.get("gate", "")),
            "notes": str(row.get("notes", "")),
            "proof_status": "source_mirrored_pending_differential",
            "turn_differential_status": "pending_rom_turn_differential",
            "missing_evidence": ["rom_backed_turn_differential"],
            "blocking_gaps": [REMAINING_TURN_DIFFERENTIAL_GAP],
            "does_not_close": [REMAINING_TURN_DIFFERENTIAL_GAP],
            "next_command": "Add a ROM turn differential golden for this mechanic, then remove this row from the pending worklist.",
        }
        for row in pending_rows
        if isinstance(row, dict)
    ]

    command = (
        "python -m tools.headless_battle.promoted_turn_differential_worklist "
        "--json-out audit\\headless_battle\\promoted_turn_differential_worklist.json"
    )
    component_path = root / "audit" / "headless_battle" / "rom_differential.json"
    payload = build_report_envelope(
        kind=WORKLIST_KIND,
        command=command,
        inputs={
            "source": "tools.headless_battle.simulator.coverage_report",
            "source_path": "tools/headless_battle/simulator.py",
        },
        backend="static",
        proof_status="worklist_only",
        missing_evidence=[REMAINING_TURN_DIFFERENTIAL_GAP],
        blocking_gaps=[REMAINING_TURN_DIFFERENTIAL_GAP],
        known_limits=[
            "This artifact catalogs source-mirrored promoted mechanics that still need ROM-backed turn differentials.",
            "It closes only the worklist catalog evidence, not any promoted-mechanic turn differential.",
        ],
        closed_evidence_ids=[WORKLIST_EVIDENCE_ID],
        repro_command=command,
        disproof_standard=[
            "Every source-mirrored pending mechanic is represented exactly once.",
            "Every row remains marked pending until a ROM-backed turn differential exists.",
            "The artifact does not remove remaining_promoted_mechanic_turn_differentials from the literal-anything gate.",
        ],
        root=root,
    )
    payload.update(
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "tools.headless_battle.simulator.coverage_report",
            "source_path": "tools/headless_battle/simulator.py",
            "source_sha256": sha256_file(root / "tools" / "headless_battle" / "simulator.py", root=root),
            "generator_path": "tools/headless_battle/promoted_turn_differential_worklist.py",
            "generator_sha256": sha256_file(__file__, root=root),
            "row_count": len(rows),
            "pending_turn_differential_count": len(rows),
            "rows": rows,
            "source_mirrored_pending_ids": [row["id"] for row in rows],
            "byte_proven_ids": [
                str(row.get("id", ""))
                for row in byte_proven_rows
                if isinstance(row, dict)
            ],
            "component_rom_differentials": component_report_summary(component_path, root=root),
            "does_not_close": [REMAINING_TURN_DIFFERENTIAL_GAP],
            "next_command": command,
        }
    )
    return payload


def component_report_summary(path: Path, *, root: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "path": display_path(path, root=root),
        "exists": path.exists(),
        "kind": "",
        "proof_status": "",
        "pass_count": 0,
        "scenario_ids": [],
        "sha256": sha256_file(path, root=root),
    }
    if not path.exists():
        return summary
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        summary["error"] = str(exc)
        return summary
    results = payload.get("results", [])
    if not isinstance(results, list):
        results = []
    summary.update(
        {
            "kind": str(payload.get("kind", "")),
            "proof_status": str(payload.get("proof_status", "")),
            "pass_count": int(payload.get("pass_count", 0) or 0),
            "scenario_ids": [
                str(row.get("scenario_id", ""))
                for row in results
                if isinstance(row, dict) and row.get("ok") is True
            ],
        }
    )
    return summary


def display_path(path: Path, *, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def format_text(payload: dict[str, Any]) -> str:
    lines = [
        f"Headless promoted turn differential worklist: {payload['pending_turn_differential_count']} pending",
        f"Proof status: {payload['proof_status']}",
        "Does not close:",
    ]
    lines.extend(f"  - {item}" for item in payload.get("does_not_close", []))
    lines.append("Rows:")
    for row in payload.get("rows", []):
        if isinstance(row, dict):
            lines.append(f"  - {row.get('id', '')}: {row.get('source', '')}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate the headless promoted-mechanic ROM turn differential worklist."
    )
    parser.add_argument("--json", action="store_true", help="print the worklist JSON")
    parser.add_argument("--json-out", type=Path, help="write the worklist JSON to this path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = build_worklist()
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
