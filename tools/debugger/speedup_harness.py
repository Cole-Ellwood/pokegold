#!/usr/bin/env python3
"""Measured-speedup scaffold for P21.

The roadmap §3 P21 deliverable is a benchmark harness that emits per-scenario
ratios (baseline command path vs masterpiece command path) backed by
``EvidenceAtom`` s, so the "100x faster" claim is *measured* not asserted.

This is the **scaffold slice**, not the acceptance slice. It ships:

- Schema + validation for ``audit/lived_bug_scenarios.jsonl`` scenario records.
- A self-test that loads + validates the scenarios file and emits an honest
  status line ("speedup-report scaffold: N scenario records validated; ratios
  pending acceptance slice") that does NOT match the pgoal v5 acceptance
  regex ``scenarios=[6-9]|scenarios=1[0-9]``. Pgoal v5 deliberately stays
  red until the acceptance slice ships real measured ratios.

Out of scope for the scaffold slice (acceptance-slice work):

- Actually running each baseline + masterpiece command path and measuring
  elapsed time.
- Populating ``masterpiece_time_actual_seconds`` and ``ratio`` per scenario.
- Wiring ``speedup-report`` through ``tools/debugger/__main__.py``,
  ``tools/debugger/catalog.py``, or ``tools/debugger/selftest.py``.
- Committing ``docs/debugger_speedup_<date>.md``.
- The §3 P21 "refuse over overclaim" gate that calls into a real replay
  engine; a stub-shaped refusal on missing baseline evidence_atom lands
  now so the gate logic exists.

Codex approved this scope on 2026-05-22 with the explicit constraint that
``--self-test`` output must avoid ``scenarios=N`` exactly, that null
``masterpiece_time_actual_seconds`` + null ``ratio`` are only legal when
``status="scaffold_incomplete"``, and that baseline ``evidence_atoms`` must
be present.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from .catalog import ROOT


SCHEMA_VERSION = 1
KIND = "speedup_scenario"

DEFAULT_SCENARIOS_PATH = Path("audit") / "lived_bug_scenarios.jsonl"

VALID_STATUSES = ("scaffold_incomplete", "measured")
REQUIRED_FIELDS = (
    "id",
    "bug_class",
    "baseline_commands",
    "baseline_time_estimate_seconds",
    "masterpiece_commands",
    "masterpiece_time_actual_seconds",
    "ratio",
    "evidence_atoms",
    "status",
)

MIN_SCENARIOS = 6

CATALOG_PATH = Path("docs") / "debugger_bug_class_catalog.md"


def load_known_bug_classes(catalog_path: Path | None = None) -> set[str]:
    """Parse ``docs/debugger_bug_class_catalog.md`` and return the set of
    entry names.

    Used by ``validate_scenario`` to refuse scenarios whose ``bug_class``
    doesn't match a real catalog entry -- the taxonomy-drift gate Codex
    flagged in P21 scaffold review.

    Returns an empty set if the catalog is missing; callers should treat
    "no known classes" as "don't enforce the cross-check" so the
    validator stays useful when run outside the repo.
    """
    from tools.audit.check_debugger_bug_class_catalog import parse_catalog

    path = catalog_path or (ROOT / CATALOG_PATH)
    if not path.exists():
        return set()
    entries, _ = parse_catalog(path.read_text(encoding="utf-8"))
    return {str(entry["name"]) for entry in entries if entry.get("name")}


@dataclass(frozen=True)
class Scenario:
    """One historical-investigation scenario.

    The dataclass exists so callers can hold a parsed record with named
    attributes; the JSONL source of truth is a dict, and ``validate_scenario``
    works directly on dicts to match the on-disk shape.
    """

    id: str
    bug_class: str
    baseline_commands: tuple[str, ...]
    baseline_time_estimate_seconds: float
    masterpiece_commands: tuple[str, ...]
    masterpiece_time_actual_seconds: float | None
    ratio: float | None
    evidence_atoms: tuple[dict[str, Any], ...]
    status: str
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "Scenario":
        return cls(
            id=str(row["id"]),
            bug_class=str(row["bug_class"]),
            baseline_commands=tuple(row.get("baseline_commands", [])),
            baseline_time_estimate_seconds=float(
                row["baseline_time_estimate_seconds"]
            ),
            masterpiece_commands=tuple(row.get("masterpiece_commands", [])),
            masterpiece_time_actual_seconds=(
                None
                if row.get("masterpiece_time_actual_seconds") is None
                else float(row["masterpiece_time_actual_seconds"])
            ),
            ratio=None if row.get("ratio") is None else float(row["ratio"]),
            evidence_atoms=tuple(dict(a) for a in row.get("evidence_atoms", [])),
            status=str(row["status"]),
            extra={
                k: v
                for k, v in row.items()
                if k not in REQUIRED_FIELDS
            },
        )

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": self.id,
            "bug_class": self.bug_class,
            "baseline_commands": list(self.baseline_commands),
            "baseline_time_estimate_seconds": self.baseline_time_estimate_seconds,
            "masterpiece_commands": list(self.masterpiece_commands),
            "masterpiece_time_actual_seconds": self.masterpiece_time_actual_seconds,
            "ratio": self.ratio,
            "evidence_atoms": [dict(a) for a in self.evidence_atoms],
            "status": self.status,
        }
        for key, value in self.extra.items():
            if key not in out:
                out[key] = value
        return out


def validate_scenario(
    row: dict[str, Any],
    *,
    known_bug_classes: set[str] | None = None,
) -> list[str]:
    """Return validation errors for one scenario record.

    Empty list = valid. Enforces:

    - All ``REQUIRED_FIELDS`` present.
    - ``status`` in ``VALID_STATUSES``.
    - ``baseline_commands`` and ``masterpiece_commands`` are non-empty lists.
    - ``baseline_time_estimate_seconds`` is numeric (int or float, not str).
    - ``evidence_atoms`` is a non-empty list AND each entry is a non-empty
      dict (catches the ``[{}]`` taxonomy-drift gap Codex flagged).
    - ``bug_class`` matches a name from the P20 catalog when
      ``known_bug_classes`` is supplied (or auto-loadable from the
      committed catalog). Passing ``known_bug_classes=set()`` skips the
      cross-check; useful for tests that don't want to depend on the
      catalog being present.
    - ``masterpiece_time_actual_seconds`` / ``ratio`` are null iff
      ``status == "scaffold_incomplete"``.
    """
    errors: list[str] = []
    for required in REQUIRED_FIELDS:
        if required not in row:
            errors.append(f"missing required field: {required}")
    if errors:
        return errors

    status = row["status"]
    if status not in VALID_STATUSES:
        errors.append(f"status {status!r} not in {VALID_STATUSES}")

    baseline_commands = row.get("baseline_commands") or []
    if not isinstance(baseline_commands, list) or not baseline_commands:
        errors.append("baseline_commands must be a non-empty list")

    masterpiece_commands = row.get("masterpiece_commands") or []
    if not isinstance(masterpiece_commands, list) or not masterpiece_commands:
        errors.append("masterpiece_commands must be a non-empty list")

    baseline_time = row.get("baseline_time_estimate_seconds")
    if not isinstance(baseline_time, (int, float)) or isinstance(baseline_time, bool):
        errors.append(
            "baseline_time_estimate_seconds must be a number (int or float); "
            f"got {type(baseline_time).__name__}"
        )

    evidence_atoms = row.get("evidence_atoms") or []
    if not isinstance(evidence_atoms, list) or not evidence_atoms:
        errors.append(
            "evidence_atoms must be a non-empty list; scaffold slice "
            "requires at least one baseline-side EvidenceAtom naming the "
            "source commit, doc section, or handoff row"
        )
    else:
        for idx, atom in enumerate(evidence_atoms):
            if not isinstance(atom, dict) or not atom:
                errors.append(
                    f"evidence_atoms[{idx}] must be a non-empty dict; "
                    f"got {type(atom).__name__} {atom!r}"
                )

    # Catalog cross-check. The default lazily loads from the committed
    # catalog; tests can opt out with known_bug_classes=set().
    bug_class = row.get("bug_class")
    if known_bug_classes is None:
        known_bug_classes = load_known_bug_classes()
    if known_bug_classes and bug_class not in known_bug_classes:
        errors.append(
            f"bug_class {bug_class!r} not in the P20 catalog "
            f"(docs/debugger_bug_class_catalog.md); use one of "
            f"{sorted(known_bug_classes)[:5]}... or add the class to the "
            f"catalog first"
        )

    mt = row.get("masterpiece_time_actual_seconds")
    ratio = row.get("ratio")
    if status == "measured":
        if mt is None:
            errors.append(
                "status='measured' requires non-null masterpiece_time_actual_seconds"
            )
        if ratio is None:
            errors.append("status='measured' requires non-null ratio")
    elif status == "scaffold_incomplete":
        if mt is not None:
            errors.append(
                "status='scaffold_incomplete' requires null "
                "masterpiece_time_actual_seconds (not yet measured)"
            )
        if ratio is not None:
            errors.append(
                "status='scaffold_incomplete' requires null ratio "
                "(not yet computed)"
            )

    return errors


def load_scenarios(
    path: Path,
    *,
    known_bug_classes: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Parse the JSONL scenarios file.

    Returns (records, errors). Errors include per-line parse failures and
    per-record validation failures. Records are returned even when errors
    exist so the caller can render a partial table for debugging.

    Loads the P20 catalog ONCE and passes the known-bug-classes set into
    each ``validate_scenario`` call to avoid re-parsing the markdown per
    record. Tests can override with ``known_bug_classes=set()`` to skip
    the catalog cross-check.
    """
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    if not path.exists():
        return [], [f"scenarios file not found at {path}"]
    if known_bug_classes is None:
        known_bug_classes = load_known_bug_classes()
    text = path.read_text(encoding="utf-8")
    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        try:
            row = json.loads(stripped)
        except json.JSONDecodeError as exc:
            errors.append(f"line {lineno}: JSON parse error: {exc}")
            continue
        per_record = validate_scenario(row, known_bug_classes=known_bug_classes)
        if per_record:
            for err in per_record:
                errors.append(f"line {lineno} ({row.get('id', '?')}): {err}")
        records.append(row)
    return records, errors


def render_markdown_table(records: Sequence[dict[str, Any]]) -> str:
    """Render the loaded records as a markdown table.

    Scaffold-slice ratios are null and shown as ``—`` so the reader sees
    immediately that the measurement step has not run. This output is
    purely advisory; the on-disk artifact is the JSONL file.
    """
    lines = [
        "| id | bug_class | status | baseline_est_s | masterpiece_actual_s | ratio |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in records:
        mt = row.get("masterpiece_time_actual_seconds")
        ratio = row.get("ratio")
        lines.append(
            f"| {row.get('id', '?')}"
            f" | {row.get('bug_class', '?')}"
            f" | {row.get('status', '?')}"
            f" | {row.get('baseline_time_estimate_seconds', '?')}"
            f" | {'—' if mt is None else mt}"
            f" | {'—' if ratio is None else ratio} |"
        )
    return "\n".join(lines)


def run_self_test(
    *,
    scenarios_path: Path | None = None,
    verbose: bool = False,
) -> int:
    """Load and validate the scenarios file; emit scaffold status line.

    Exits 0 when validation passes AND the file has ``>= MIN_SCENARIOS``
    records. Critically does NOT emit the pgoal v5 acceptance regex
    ``scenarios=N``; the scaffold slice deliberately keeps pgoal v5 red.
    The acceptance slice (P21_speedup_harness_acceptance_slice) flips it
    green by populating real ratios and wiring the unified CLI.
    """
    path = scenarios_path or (ROOT / DEFAULT_SCENARIOS_PATH)
    records, errors = load_scenarios(path)
    if errors:
        sys.stderr.write(
            f"speedup-harness scaffold FAIL: {len(errors)} validation errors:\n"
        )
        for err in errors:
            sys.stderr.write(f"  - {err}\n")
        return 1
    if len(records) < MIN_SCENARIOS:
        sys.stderr.write(
            f"speedup-harness scaffold FAIL: only {len(records)} records; "
            f"minimum {MIN_SCENARIOS}\n"
        )
        return 1
    if verbose:
        sys.stdout.write(render_markdown_table(records) + "\n")
    sys.stdout.write(
        f"speedup-report scaffold: {len(records)} scenario records "
        f"validated; ratios pending acceptance slice\n"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger.speedup_harness",
        description=(
            "Measured-speedup harness scaffold (P21). Scaffold slice only: "
            "validates audit/lived_bug_scenarios.jsonl and emits an honest "
            "status line. Real ratio measurement is the acceptance slice."
        ),
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help=(
            "Load and validate the scenarios JSONL; emit scaffold status. "
            "Exits 0 on validation success with >= 6 records. Does NOT "
            "emit the pgoal v5 acceptance regex; v5 stays red by design."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the markdown summary table before the status line.",
    )
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=None,
        help="Override the scenarios JSONL path (default: repo audit/...).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test(
            scenarios_path=args.scenarios,
            verbose=args.verbose,
        )
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
