"""Measured speedup harness for lived debugger scenarios (P21).

The harness intentionally reports per-scenario ratios only. The baseline side is
a cited historical estimate; the masterpiece side is re-run locally and timed
before a ratio is emitted.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from .evidence import evidence_atom

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCENARIOS = ROOT / "audit" / "lived_bug_scenarios.jsonl"
DEFAULT_REPORT = ROOT / "docs" / "debugger_speedup_2026-05-22.md"
MIN_SCENARIOS = 6
TIMEOUT_SECONDS = 180.0


@dataclass(frozen=True)
class Scenario:
    """Loaded scenario row with its original JSONL line number."""

    line_number: int
    record: dict[str, Any]

    @property
    def id(self) -> str:
        return str(self.record.get("id", ""))

    @property
    def bug_class(self) -> str:
        return str(self.record.get("bug_class", ""))


@dataclass(frozen=True)
class CommandResult:
    command: str
    exit_code: int
    elapsed_seconds: float
    stdout_tail: str
    stderr_tail: str


CommandRunner = Callable[[str], CommandResult]


def _tail(text: str, limit: int = 1200) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[-limit:]


def _json_dump(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _as_text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def load_known_bug_classes(catalog_path: Path | None = None) -> set[str]:
    """Return bug_class ids from the P20 catalog markdown."""

    catalog_path = catalog_path or ROOT / "docs" / "debugger_bug_class_catalog.md"
    ids: set[str] = set()
    if not catalog_path.exists():
        return ids
    for line in catalog_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("### "):
            continue
        heading = line[4:].strip()
        if not heading or " " in heading:
            continue
        ids.add(heading)
    return ids


def load_bug_class_tiers(catalog_path: Path | None = None) -> dict[str, str]:
    """Return bug_class -> AUTO/QUERY/JUDGMENT from the P20 catalog."""

    catalog_path = catalog_path or ROOT / "docs" / "debugger_bug_class_catalog.md"
    tiers: dict[str, str] = {}
    if not catalog_path.exists():
        return tiers

    current_id: str | None = None
    for line in catalog_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            heading = line[4:].strip()
            current_id = heading if heading and " " not in heading else None
            continue
        if not current_id:
            continue
        if line.startswith("**Tier:**"):
            tier = line.removeprefix("**Tier:**").strip().upper()
            if tier in {"AUTO", "QUERY", "JUDGMENT"}:
                tiers[current_id] = tier
    return tiers


def _atom_matches(atom: Mapping[str, Any], *, claim_type: str | None = None, origin: str | None = None) -> bool:
    if claim_type is not None and atom.get("claim_type") != claim_type:
        return False
    if origin is not None and atom.get("origin") != origin:
        return False
    return True


def _has_atom(row: Mapping[str, Any], *, claim_type: str | None = None, origin: str | None = None) -> bool:
    atoms = row.get("evidence_atoms")
    if not isinstance(atoms, list):
        return False
    return any(isinstance(atom, dict) and _atom_matches(atom, claim_type=claim_type, origin=origin) for atom in atoms)


def validate_scenario(
    row: Mapping[str, Any],
    *,
    known_bug_classes: set[str] | None = None,
    require_measured: bool = False,
) -> list[str]:
    """Return schema and honesty-gate errors for one scenario record."""

    errors: list[str] = []

    scenario_id = row.get("id")
    if not isinstance(scenario_id, str) or not scenario_id.strip():
        errors.append("id must be a non-empty string")

    bug_class = row.get("bug_class")
    if not isinstance(bug_class, str) or not bug_class.strip():
        errors.append("bug_class must be a non-empty string")
    elif known_bug_classes and bug_class not in known_bug_classes:
        errors.append(f"bug_class {bug_class!r} is not in docs/debugger_bug_class_catalog.md")

    baseline_commands = row.get("baseline_commands")
    if not _as_text_list(baseline_commands):
        errors.append("baseline_commands must be a non-empty list of strings")

    baseline_time = row.get("baseline_time_estimate_seconds")
    if not _is_number(baseline_time) or float(baseline_time) <= 0:
        errors.append("baseline_time_estimate_seconds must be a positive number")

    masterpiece_commands = row.get("masterpiece_commands")
    if not _as_text_list(masterpiece_commands):
        errors.append("masterpiece_commands must be a non-empty list of strings")

    atoms = row.get("evidence_atoms")
    if not isinstance(atoms, list) or not atoms:
        errors.append("evidence_atoms must be a non-empty list")
    else:
        for index, atom in enumerate(atoms):
            if not isinstance(atom, dict) or not atom:
                errors.append(f"evidence_atoms[{index}] must be a non-empty object")

    status = row.get("status")
    if status not in {"scaffold_incomplete", "measured"}:
        errors.append("status must be scaffold_incomplete or measured")

    actual = row.get("masterpiece_time_actual_seconds")
    ratio = row.get("ratio")
    has_actual = actual is not None
    has_ratio = ratio is not None
    if require_measured or has_actual or has_ratio or status == "measured":
        if status != "measured":
            errors.append("measured scenarios must have status=measured")
        if not _is_number(actual) or float(actual) <= 0:
            errors.append("masterpiece_time_actual_seconds must be a positive number")
        if not _is_number(ratio) or float(ratio) <= 0:
            errors.append("ratio must be a positive number")
        if not _has_atom(row, origin="baseline_history"):
            errors.append("measured scenarios require a baseline_history EvidenceAtom")
        if not _has_atom(row, origin="masterpiece_replay"):
            errors.append("measured scenarios require a masterpiece_replay EvidenceAtom")
        if not _has_atom(row, claim_type="speedup.ratio"):
            errors.append("measured scenarios require a speedup.ratio EvidenceAtom")

    return errors


def _iter_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number}: record must be a JSON object")
            yield line_number, record


def load_scenarios(
    path: Path | None = None,
    *,
    require_measured: bool = False,
    known_bug_classes: set[str] | None = None,
) -> list[Scenario]:
    """Load and validate lived bug scenarios from JSONL."""

    path = path or DEFAULT_SCENARIOS
    if not path.exists():
        raise FileNotFoundError(path)

    if known_bug_classes is None:
        known_bug_classes = load_known_bug_classes()

    scenarios: list[Scenario] = []
    all_errors: list[str] = []
    for line_number, record in _iter_jsonl(path):
        errors = validate_scenario(record, known_bug_classes=known_bug_classes, require_measured=require_measured)
        if errors:
            all_errors.extend(f"{path}:{line_number}: {error}" for error in errors)
        else:
            scenarios.append(Scenario(line_number=line_number, record=record))

    if all_errors:
        raise ValueError("\n".join(all_errors))
    return scenarios


def run_command(command: str, *, timeout_seconds: float = TIMEOUT_SECONDS, root: Path = ROOT) -> CommandResult:
    """Run one re-verification command and return timing plus output tails."""

    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=root,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    elapsed = time.perf_counter() - started
    return CommandResult(
        command=command,
        exit_code=completed.returncode,
        elapsed_seconds=round(elapsed, 3),
        stdout_tail=_tail(completed.stdout),
        stderr_tail=_tail(completed.stderr),
    )


def _baseline_atom(row: Mapping[str, Any]) -> dict[str, Any]:
    source_report = str(row.get("baseline_source", "audit/lived_bug_scenarios.jsonl"))
    return evidence_atom(
        claim_type="speedup.baseline_time_estimate",
        origin="baseline_history",
        observation_type="commit_or_handoff_citation",
        proof_status="planned_only",
        source_report=source_report,
        source_kind="repository_record",
        scope={"scenario_id": row.get("id"), "bug_class": row.get("bug_class")},
        subjects={"commands": row.get("baseline_commands", [])},
        precision={"time_seconds": "estimate"},
        validation={"note": "historical baseline estimate, not re-run by this harness"},
        detail={"baseline_time_estimate_seconds": row.get("baseline_time_estimate_seconds")},
    )


def _replay_atom(row: Mapping[str, Any], command_results: Sequence[CommandResult], total_seconds: float) -> dict[str, Any]:
    return evidence_atom(
        claim_type="speedup.masterpiece_replay",
        origin="masterpiece_replay",
        observation_type="subprocess_exit_zero",
        proof_status="runtime_observed",
        source_report="P21 speedup harness local replay",
        source_kind="local_command",
        scope={"scenario_id": row.get("id"), "bug_class": row.get("bug_class")},
        subjects={"commands": [result.command for result in command_results]},
        precision={"time_seconds": "perf_counter"},
        validation={"exit_codes": [result.exit_code for result in command_results]},
        detail={
            "masterpiece_time_actual_seconds": total_seconds,
            "command_results": [result.__dict__ for result in command_results],
        },
    )


def _ratio_atom(row: Mapping[str, Any], baseline_seconds: float, actual_seconds: float, ratio: float) -> dict[str, Any]:
    return evidence_atom(
        claim_type="speedup.ratio",
        origin="speedup_harness",
        observation_type="computed_from_baseline_estimate_and_replay_time",
        proof_status="state_materialized",
        source_report="P21 speedup harness local replay",
        source_kind="computed_metric",
        scope={"scenario_id": row.get("id"), "bug_class": row.get("bug_class")},
        subjects={"baseline_seconds": baseline_seconds, "masterpiece_seconds": actual_seconds},
        precision={"ratio": "baseline_time_estimate_seconds / masterpiece_time_actual_seconds"},
        validation={"baseline_time_kind": "historical_estimate", "masterpiece_time_kind": "local_runtime"},
        detail={"ratio": ratio},
    )


def _without_generated_atoms(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    atoms = row.get("evidence_atoms")
    if not isinstance(atoms, list):
        return kept
    for atom in atoms:
        if not isinstance(atom, dict) or not atom:
            continue
        if atom.get("origin") in {"masterpiece_replay", "speedup_harness"}:
            continue
        if str(atom.get("claim_type", "")).startswith("speedup."):
            continue
        kept.append(dict(atom))
    return kept


def measure_scenario(
    scenario: Scenario,
    *,
    runner: CommandRunner | None = None,
    timeout_seconds: float = TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Replay one scenario's masterpiece command path and return a measured row."""

    runner = runner or (lambda command: run_command(command, timeout_seconds=timeout_seconds))
    row = dict(scenario.record)
    commands = _as_text_list(row.get("masterpiece_commands"))
    if not commands:
        raise ValueError(f"{scenario.id}: no masterpiece_commands to replay")

    command_results = [runner(command) for command in commands]
    failing = [result for result in command_results if result.exit_code != 0]
    if failing:
        details = "; ".join(f"{result.command!r} exit={result.exit_code}" for result in failing)
        raise RuntimeError(f"{scenario.id}: masterpiece replay failed: {details}")

    total_seconds = round(sum(max(result.elapsed_seconds, 0.001) for result in command_results), 3)
    baseline_seconds = float(row["baseline_time_estimate_seconds"])
    ratio = round(baseline_seconds / total_seconds, 2)

    atoms = _without_generated_atoms(row)
    if not any(atom.get("origin") == "baseline_history" for atom in atoms):
        atoms.append(_baseline_atom(row))
    atoms.append(_replay_atom(row, command_results, total_seconds))
    atoms.append(_ratio_atom(row, baseline_seconds, total_seconds, ratio))

    row["status"] = "measured"
    row["masterpiece_time_actual_seconds"] = total_seconds
    row["ratio"] = ratio
    row["measured_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    row["evidence_atoms"] = atoms
    return row


def filter_scenarios(
    scenarios: Sequence[Scenario],
    *,
    tier: str | None = None,
    bug_class_tiers: Mapping[str, str] | None = None,
) -> list[Scenario]:
    if tier is None:
        return list(scenarios)
    tier = tier.upper()
    if tier not in {"AUTO", "QUERY", "JUDGMENT"}:
        raise ValueError("filter tier must be AUTO, QUERY, or JUDGMENT")
    bug_class_tiers = bug_class_tiers or load_bug_class_tiers()
    return [scenario for scenario in scenarios if bug_class_tiers.get(scenario.bug_class) == tier]


def build_speedup_report(
    scenarios_path: Path | None = None,
    *,
    filter_tier: str | None = None,
    refresh: bool = True,
    timeout_seconds: float = TIMEOUT_SECONDS,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Return the measured report data used by CLI, tests, and markdown."""

    scenarios_path = scenarios_path or DEFAULT_SCENARIOS
    known_bug_classes = load_known_bug_classes()
    loaded = load_scenarios(scenarios_path, require_measured=not refresh, known_bug_classes=known_bug_classes)
    selected = filter_scenarios(loaded, tier=filter_tier)

    measured: list[dict[str, Any]] = []
    errors: list[str] = []
    for scenario in selected:
        try:
            row = measure_scenario(scenario, runner=runner, timeout_seconds=timeout_seconds) if refresh else dict(scenario.record)
            validation_errors = validate_scenario(row, known_bug_classes=known_bug_classes, require_measured=True)
            if validation_errors:
                errors.extend(f"{scenario.id}: {error}" for error in validation_errors)
            else:
                measured.append(row)
        except Exception as exc:  # noqa: BLE001 - surfaced as report data for refusal.
            errors.append(str(exc))

    min_count = 1 if filter_tier else MIN_SCENARIOS
    ready = not errors and len(measured) >= min_count
    return {
        "schema_version": 1,
        "kind": "speedup_report",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "scenario_count": len(selected),
        "measured_count": len(measured),
        "minimum_required": min_count,
        "filter": filter_tier.upper() if filter_tier else None,
        "ready": ready,
        "errors": errors,
        "scenarios": measured,
    }


def _format_seconds(value: Any) -> str:
    if not _is_number(value):
        return "n/a"
    return f"{float(value):.3f}".rstrip("0").rstrip(".")


def _format_ratio(value: Any) -> str:
    if not _is_number(value):
        return "n/a"
    return f"{float(value):.2f}x"


def render_markdown_table(report: Mapping[str, Any]) -> str:
    """Render a decision-useful markdown report for the measured scenarios."""

    lines = [
        "# Debugger Speedup Report - 2026-05-22",
        "",
        "This report emits per-scenario ratios only. Baseline times are historical estimates cited by each scenario's EvidenceAtoms; masterpiece times are local command replays measured by this harness.",
        "",
        f"- Ready: {str(report.get('ready')).lower()}",
        f"- Scenarios measured: {report.get('measured_count')} / {report.get('scenario_count')}",
        f"- Minimum required: {report.get('minimum_required')}",
        "",
    ]

    errors = report.get("errors")
    if isinstance(errors, list) and errors:
        lines.append("## Refusals")
        lines.append("")
        for error in errors:
            lines.append(f"- {error}")
        lines.append("")

    lines.extend(
        [
            "## Per-Scenario Ratios",
            "",
            "| Scenario | Bug class | Baseline estimate (s) | Masterpiece replay (s) | Ratio | Evidence | Replay commands |",
            "| --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )

    scenarios = report.get("scenarios")
    if isinstance(scenarios, list):
        for row in scenarios:
            if not isinstance(row, dict):
                continue
            atoms = row.get("evidence_atoms") if isinstance(row.get("evidence_atoms"), list) else []
            atom_claims = [
                str(atom.get("claim_type"))
                for atom in atoms
                if isinstance(atom, dict) and atom.get("claim_type") in {"speedup.baseline_time_estimate", "speedup.masterpiece_replay", "speedup.ratio"}
            ]
            commands = " ; ".join(_as_text_list(row.get("masterpiece_commands")))
            lines.append(
                "| {id} | {bug_class} | {baseline} | {actual} | {ratio} | {evidence} | `{commands}` |".format(
                    id=row.get("id", ""),
                    bug_class=row.get("bug_class", ""),
                    baseline=_format_seconds(row.get("baseline_time_estimate_seconds")),
                    actual=_format_seconds(row.get("masterpiece_time_actual_seconds")),
                    ratio=_format_ratio(row.get("ratio")),
                    evidence=", ".join(atom_claims) if atom_claims else "missing",
                    commands=commands.replace("|", "\\|"),
                )
            )

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- A ratio is omitted when any masterpiece replay command fails or when required EvidenceAtoms are missing.")
    lines.append("- The harness does not emit an aggregate speedup claim.")
    lines.append("")
    return "\n".join(lines)


def write_scenarios(path: Path, scenarios: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in scenarios:
            handle.write(_json_dump(row))
            handle.write("\n")


def run_self_test(path: Path | None = None) -> int:
    report = build_speedup_report(path or DEFAULT_SCENARIOS, refresh=True)
    if report["errors"]:
        for error in report["errors"]:
            print(f"speedup-report error: {error}", file=sys.stderr)
    if not report["ready"]:
        print(
            f"speedup-report refused: scenarios={report['measured_count']} required={report['minimum_required']}",
            file=sys.stderr,
        )
        return 1
    print(f"speedup-report scenarios={report['measured_count']} measured={report['measured_count']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Measure debugger speedup against lived bug scenarios.")
    parser.add_argument("--self-test", action="store_true", help="Replay the default scenarios and require at least six measured ratios.")
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS, help="JSONL scenario file.")
    parser.add_argument("--filter", choices=("AUTO", "QUERY", "JUDGMENT"), help="Report only scenarios from one P20 taxonomy tier.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report instead of markdown.")
    parser.add_argument("--markdown", action="store_true", help="Emit markdown report. This is the default.")
    parser.add_argument("--no-refresh", action="store_true", help="Use stored measurements instead of re-running commands.")
    parser.add_argument("--timeout-seconds", type=float, default=TIMEOUT_SECONDS, help="Per-command timeout for replay.")
    parser.add_argument("--out", type=Path, help="Write emitted report text to this path.")
    parser.add_argument("--write-scenarios", type=Path, help="Write measured scenario JSONL to this path.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        return run_self_test(args.scenarios)

    report = build_speedup_report(
        args.scenarios,
        filter_tier=args.filter,
        refresh=not args.no_refresh,
        timeout_seconds=args.timeout_seconds,
    )
    if args.write_scenarios:
        write_scenarios(args.write_scenarios, report["scenarios"])

    output = _json_dump(report) + "\n" if args.json else render_markdown_table(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output, end="" if output.endswith("\n") else "\n")
    return 0 if report["ready"] else 1


if __name__ == "__main__":  # pragma: no cover - exercised by CLI tests.
    raise SystemExit(main())
