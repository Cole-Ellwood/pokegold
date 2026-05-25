"""Phase 2 switch-expectations comparator.

Per ``docs/headless_batch_validation_implementation.md`` §5 Phase 2.

Wraps the Phase-1 batch switch-materialize runner with a JSON-schema'd
expectations comparator. Given a scenarios JSONL and an expectations JSON,
the comparator runs the batch and emits a per-scenario pass/fail/error/
no_expectation verdict plus a focused violation report.

Schema (one expectation row)::

    {
      "scenario_id": "morty_haunter_neutral_shadow_ball",
      "expected": {
        "action": "stay",                 // or "switch"
        "switch_probability_max": 0.10,   // optional upper bound on switch_prob
        "switch_probability_min": 0.05    // optional lower bound on switch_prob
      },
      "rationale": "Neutral Shadow Ball isn't a converter; switching loses tempo"
    }

Top-level shapes accepted (consistent with rom_scenarios.load_expectation_map):

- ``[ row, row, ... ]`` (flat list)
- ``{ "expectations": [ row, ... ], "schema_version": 1 }`` (envelope)
- ``{ row }`` (single row, scenario_id at top level)

Comparison rules
- ``status == "error"`` → ``"error"`` (verdict.reason carried through)
- ``scenario_id not in expectations`` → ``"no_expectation"`` (informational)
- ``expected.action != observed_action`` → ``"fail"`` (observed_action is
  "switch" when ``rom.proposed_switch`` is True, else "stay")
- ``switch_probability_max`` is set and ``switch_roll.switch_probability >
  switch_probability_max`` → ``"fail"``
- ``switch_probability_min`` is set and ``switch_roll.switch_probability <
  switch_probability_min`` → ``"fail"``
- A probability bound is set but ``switch_roll.available`` is False →
  ``"fail"`` with reason ``"switch_roll_unavailable_for_bound_check"``
- Otherwise → ``"pass"``
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from tools.boss_ai_debugger.rom_switch_materialize import (
    DEFAULT_BASE_ROUTE,
    DEFAULT_WATCH_FRAMES,
    write_rom_switch_materialization_json,
)
from tools.boss_ai_debugger.rom_selector_materialize import DEFAULT_MANIFEST_PATH
from tools.headless_battle.batch_switch import run_batch_switch_materialize
from tools.trace import boss_ai_trace_capture as capture


VALID_ACTIONS = frozenset({"stay", "switch"})


class SwitchExpectationError(ValueError):
    """Raised when an expectations file is malformed or invalid."""


@dataclass(frozen=True)
class SwitchExpectation:
    """A single switch-decision expectation for a scenario."""

    scenario_id: str
    action: str
    switch_probability_max: Optional[float] = None
    switch_probability_min: Optional[float] = None
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "scenario_id": self.scenario_id,
            "expected": {"action": self.action},
        }
        if self.switch_probability_max is not None:
            out["expected"]["switch_probability_max"] = self.switch_probability_max
        if self.switch_probability_min is not None:
            out["expected"]["switch_probability_min"] = self.switch_probability_min
        if self.rationale:
            out["rationale"] = self.rationale
        return out


@dataclass(frozen=True)
class ScenarioComparison:
    """Comparison result for one scenario_id."""

    scenario_id: str
    status: str  # "pass" | "fail" | "error" | "no_expectation"
    expected_action: Optional[str] = None
    observed_action: Optional[str] = None
    expected_switch_probability_max: Optional[float] = None
    expected_switch_probability_min: Optional[float] = None
    observed_switch_probability: Optional[float] = None
    probability_exact: Optional[bool] = None
    rationale: str = ""
    reason: str = ""
    verdict_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out = {
            "scenario_id": self.scenario_id,
            "status": self.status,
            "expected_action": self.expected_action,
            "observed_action": self.observed_action,
            "expected_switch_probability_max": self.expected_switch_probability_max,
            "expected_switch_probability_min": self.expected_switch_probability_min,
            "observed_switch_probability": self.observed_switch_probability,
            "probability_exact": self.probability_exact,
            "rationale": self.rationale,
            "reason": self.reason,
            "verdict_summary": dict(self.verdict_summary),
        }
        return out


def _coerce_optional_float(value: Any, field_name: str) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        # bool is a subclass of int; reject to avoid accidental True/False bounds.
        raise SwitchExpectationError(
            f"{field_name} must be a number between 0 and 1, got bool"
        )
    if not isinstance(value, (int, float)):
        raise SwitchExpectationError(
            f"{field_name} must be a number between 0 and 1, got {type(value).__name__}"
        )
    coerced = float(value)
    if coerced < 0.0 or coerced > 1.0:
        raise SwitchExpectationError(
            f"{field_name} must be between 0 and 1 (inclusive), got {coerced}"
        )
    return coerced


def _normalize_expectation_row(row: Any) -> SwitchExpectation:
    if not isinstance(row, dict):
        raise SwitchExpectationError(
            f"each expectation row must be an object, got {type(row).__name__}"
        )
    scenario_id = row.get("scenario_id")
    if not isinstance(scenario_id, str) or not scenario_id:
        raise SwitchExpectationError("each expectation row needs a non-empty scenario_id")
    expected = row.get("expected") or row.get("expectation") or {}
    if not isinstance(expected, dict):
        raise SwitchExpectationError(
            f"expectation 'expected' field for {scenario_id} must be an object"
        )
    action = expected.get("action")
    if action not in VALID_ACTIONS:
        raise SwitchExpectationError(
            f"expectation {scenario_id} action must be one of {sorted(VALID_ACTIONS)}, "
            f"got {action!r}"
        )
    prob_max = _coerce_optional_float(
        expected.get("switch_probability_max"),
        f"expectation {scenario_id} switch_probability_max",
    )
    prob_min = _coerce_optional_float(
        expected.get("switch_probability_min"),
        f"expectation {scenario_id} switch_probability_min",
    )
    if (
        prob_max is not None
        and prob_min is not None
        and prob_min > prob_max
    ):
        raise SwitchExpectationError(
            f"expectation {scenario_id} switch_probability_min ({prob_min}) "
            f"must not exceed switch_probability_max ({prob_max})"
        )
    rationale = row.get("rationale") or ""
    if not isinstance(rationale, str):
        raise SwitchExpectationError(
            f"expectation {scenario_id} rationale must be a string"
        )
    return SwitchExpectation(
        scenario_id=scenario_id,
        action=action,
        switch_probability_max=prob_max,
        switch_probability_min=prob_min,
        rationale=rationale,
    )


def parse_switch_expectations(data: Any) -> dict[str, SwitchExpectation]:
    """Normalize raw JSON content into a scenario_id-keyed map."""
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict) and isinstance(data.get("expectations"), list):
        rows = data["expectations"]
    elif isinstance(data, dict) and "scenario_id" in data:
        rows = [data]
    else:
        raise SwitchExpectationError(
            "expectations file must be a list of rows, an object with "
            "'expectations': [...], or a single expectation row with scenario_id"
        )
    expectations: dict[str, SwitchExpectation] = {}
    for row in rows:
        normalized = _normalize_expectation_row(row)
        if normalized.scenario_id in expectations:
            raise SwitchExpectationError(
                f"duplicate expectation scenario_id {normalized.scenario_id!r}"
            )
        expectations[normalized.scenario_id] = normalized
    return expectations


def load_switch_expectations(path: Path) -> dict[str, SwitchExpectation]:
    """Load + normalize expectations from a JSON file."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return parse_switch_expectations(raw)


def _verdict_summary(verdict: dict[str, Any]) -> dict[str, Any]:
    rom = verdict.get("rom") or {}
    switch_roll = verdict.get("switch_roll") or {}
    return {
        "status": verdict.get("status"),
        "switch_confidence": rom.get("switch_confidence"),
        "observation_status": rom.get("observation_status"),
        "proposed_switch": rom.get("proposed_switch"),
        "switch_probability": switch_roll.get("switch_probability"),
        "probability_exact": switch_roll.get("probability_exact"),
        "proof_status": switch_roll.get("proof_status"),
    }


def _observed_action(verdict: dict[str, Any]) -> str:
    rom = verdict.get("rom") or {}
    if rom.get("proposed_switch"):
        return "switch"
    return "stay"


def compare_verdict_to_expectation(
    verdict: dict[str, Any],
    expectation: SwitchExpectation,
) -> ScenarioComparison:
    """Compare a single materialization verdict against one expectation."""
    summary = _verdict_summary(verdict)
    if verdict.get("status") == "error":
        return ScenarioComparison(
            scenario_id=expectation.scenario_id,
            status="error",
            expected_action=expectation.action,
            observed_action=None,
            expected_switch_probability_max=expectation.switch_probability_max,
            expected_switch_probability_min=expectation.switch_probability_min,
            observed_switch_probability=None,
            probability_exact=None,
            rationale=expectation.rationale,
            reason=str(verdict.get("reason") or "materialization error"),
            verdict_summary=summary,
        )
    observed = _observed_action(verdict)
    switch_roll = verdict.get("switch_roll") or {}
    observed_probability = switch_roll.get("switch_probability")
    if not isinstance(observed_probability, (int, float)):
        observed_probability = None
    probability_exact = switch_roll.get("probability_exact")
    if not isinstance(probability_exact, bool):
        probability_exact = None
    base_comparison = dict(
        scenario_id=expectation.scenario_id,
        expected_action=expectation.action,
        observed_action=observed,
        expected_switch_probability_max=expectation.switch_probability_max,
        expected_switch_probability_min=expectation.switch_probability_min,
        observed_switch_probability=observed_probability,
        probability_exact=probability_exact,
        rationale=expectation.rationale,
        verdict_summary=summary,
    )
    if observed != expectation.action:
        return ScenarioComparison(
            **base_comparison,
            status="fail",
            reason=(
                f"expected action={expectation.action!r}, observed={observed!r} "
                f"(observation_status={summary.get('observation_status')!r})"
            ),
        )
    has_bound = (
        expectation.switch_probability_max is not None
        or expectation.switch_probability_min is not None
    )
    if has_bound and switch_roll.get("available") is False:
        return ScenarioComparison(
            **base_comparison,
            status="fail",
            reason=(
                "switch_roll_unavailable_for_bound_check; "
                f"reason={switch_roll.get('reason', 'unknown')!r}"
            ),
        )
    if (
        expectation.switch_probability_max is not None
        and observed_probability is not None
        and observed_probability > expectation.switch_probability_max
    ):
        return ScenarioComparison(
            **base_comparison,
            status="fail",
            reason=(
                f"observed switch_probability={observed_probability:.4f} > "
                f"expected switch_probability_max={expectation.switch_probability_max:.4f}"
            ),
        )
    if (
        expectation.switch_probability_min is not None
        and observed_probability is not None
        and observed_probability < expectation.switch_probability_min
    ):
        return ScenarioComparison(
            **base_comparison,
            status="fail",
            reason=(
                f"observed switch_probability={observed_probability:.4f} < "
                f"expected switch_probability_min={expectation.switch_probability_min:.4f}"
            ),
        )
    return ScenarioComparison(**base_comparison, status="pass", reason="")


def compare_batch_against_expectations(
    batch_report: dict[str, Any],
    expectations: dict[str, SwitchExpectation],
) -> dict[str, Any]:
    """Walk a batch report and produce a comparison report.

    Returns a dict with ``schema_version``, ``base_route``, ``base_state``,
    ``summary`` (pass/fail/error/no_expectation counts + unexpected counts),
    and ``comparisons`` (list of ScenarioComparison.to_dict()).
    """
    comparisons: list[ScenarioComparison] = []
    seen_ids: set[str] = set()
    for verdict in batch_report.get("verdicts", []):
        scenario_id = str(verdict.get("scenario_id", ""))
        seen_ids.add(scenario_id)
        expectation = expectations.get(scenario_id)
        if expectation is None:
            comparisons.append(
                ScenarioComparison(
                    scenario_id=scenario_id,
                    status="no_expectation",
                    expected_action=None,
                    observed_action=_observed_action(verdict)
                    if verdict.get("status") != "error"
                    else None,
                    verdict_summary=_verdict_summary(verdict),
                    reason="no expectation defined for this scenario_id",
                )
            )
            continue
        comparisons.append(compare_verdict_to_expectation(verdict, expectation))
    missing_scenarios = sorted(set(expectations) - seen_ids)
    pass_count = sum(1 for c in comparisons if c.status == "pass")
    fail_count = sum(1 for c in comparisons if c.status == "fail")
    error_count = sum(1 for c in comparisons if c.status == "error")
    no_expectation_count = sum(1 for c in comparisons if c.status == "no_expectation")
    summary = {
        "scenario_count": len(comparisons),
        "pass": pass_count,
        "fail": fail_count,
        "error": error_count,
        "no_expectation": no_expectation_count,
        "missing_scenario_ids": missing_scenarios,
    }
    return {
        "schema_version": 1,
        "kind": "headless_battle_switch_expectations_comparison",
        "base_route": batch_report.get("base_route"),
        "base_state": batch_report.get("base_state"),
        "materializations_per_minute": batch_report.get("materializations_per_minute"),
        "batch_summary": batch_report.get("summary"),
        "summary": summary,
        "comparisons": [c.to_dict() for c in comparisons],
        "known_limits": batch_report.get("known_limits", []),
    }


def format_violation_report(
    comparison_report: dict[str, Any],
    *,
    limit: int = 50,
) -> str:
    summary = comparison_report.get("summary", {})
    lines = [
        "Headless battle switch-expectations comparison",
        (
            f"base_route={comparison_report.get('base_route', '?')} "
            f"base_state={comparison_report.get('base_state', '?')}"
        ),
        (
            f"pass={summary.get('pass', 0)} "
            f"fail={summary.get('fail', 0)} "
            f"error={summary.get('error', 0)} "
            f"no_expectation={summary.get('no_expectation', 0)} "
            f"missing={len(summary.get('missing_scenario_ids', []))}"
        ),
    ]
    violations = [
        c
        for c in comparison_report.get("comparisons", [])
        if c.get("status") in ("fail", "error")
    ]
    if violations:
        lines.append("")
        lines.append(f"Violations ({len(violations)}):")
        for c in violations[:limit]:
            scenario_id = c.get("scenario_id", "?")
            status = c.get("status", "?")
            expected = c.get("expected_action") or "-"
            observed = c.get("observed_action") or "-"
            prob = c.get("observed_switch_probability")
            prob_text = f"{prob:.1%}" if isinstance(prob, (int, float)) else "n/a"
            reason = c.get("reason", "")
            lines.append(
                f"  [{status}] {scenario_id}: "
                f"expected={expected} observed={observed} prob={prob_text} -- {reason}"
            )
            rationale = c.get("rationale") or ""
            if rationale:
                lines.append(f"      rationale: {rationale}")
        if len(violations) > limit:
            lines.append(f"  ... ({len(violations) - limit} more violations truncated)")
    missing = summary.get("missing_scenario_ids", [])
    if missing:
        lines.append("")
        lines.append(f"Expectations with no matching scenario ({len(missing)}):")
        for scenario_id in missing[:limit]:
            lines.append(f"  - {scenario_id}")
        if len(missing) > limit:
            lines.append(f"  ... ({len(missing) - limit} more missing)")
    no_expectation_entries = [
        c
        for c in comparison_report.get("comparisons", [])
        if c.get("status") == "no_expectation"
    ]
    if no_expectation_entries:
        lines.append("")
        lines.append(
            f"Scenarios with no expectation ({len(no_expectation_entries)}; informational, "
            f"not a violation):"
        )
        for c in no_expectation_entries[:limit]:
            lines.append(f"  - {c.get('scenario_id', '?')}")
        if len(no_expectation_entries) > limit:
            lines.append(
                f"  ... ({len(no_expectation_entries) - limit} more no_expectation truncated)"
            )
    return "\n".join(lines)


def write_comparison_json(comparison_report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(comparison_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def run_switch_expectations_check(
    scenarios_path: Path,
    expectations_path: Path,
    *,
    limit: int = 0,
    base_route: str = DEFAULT_BASE_ROUTE,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    rom: Path = capture.DEFAULT_ROM,
    symbols_path: Path = capture.DEFAULT_SYMBOLS,
    watch_frames: int = DEFAULT_WATCH_FRAMES,
    switch_threshold: Optional[int] = None,
) -> dict[str, Any]:
    """End-to-end: run the batch materializer then compare verdicts."""
    expectations = load_switch_expectations(expectations_path)
    batch_report = run_batch_switch_materialize(
        scenarios_path,
        limit=limit,
        base_route=base_route,
        manifest_path=manifest_path,
        rom=rom,
        symbols_path=symbols_path,
        watch_frames=watch_frames,
        switch_threshold=switch_threshold,
    )
    return compare_batch_against_expectations(batch_report, expectations)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.headless_battle.switch_expectations",
        description=(
            "Compare a batch of family=switch_sack scenarios against an expectations "
            "JSON. Each expectation declares the expected action (stay or switch) and "
            "optional bounds on switch probability; failures are reported with reasons."
        ),
    )
    parser.add_argument("--scenarios", type=Path, required=True)
    parser.add_argument("--expectations", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--base-route", default=DEFAULT_BASE_ROUTE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--rom", type=Path, default=Path("pokegold_trace.gbc"))
    parser.add_argument("--symbols", type=Path, default=Path("pokegold_trace.sym"))
    parser.add_argument("--watch-frames", type=int, default=DEFAULT_WATCH_FRAMES)
    parser.add_argument("--switch-threshold", type=int, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--json-out", default="")
    parser.add_argument("--batch-json-out", default="",
                        help="also write the underlying batch materialization report")
    parser.add_argument("--display-limit", type=int, default=50)
    parser.add_argument(
        "--fail-on-violation",
        action="store_true",
        help="exit nonzero when any comparison is fail or error",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    expectations = load_switch_expectations(args.expectations)
    batch_report = run_batch_switch_materialize(
        args.scenarios,
        limit=args.limit,
        base_route=args.base_route,
        manifest_path=args.manifest,
        rom=args.rom,
        symbols_path=args.symbols,
        watch_frames=args.watch_frames,
        switch_threshold=args.switch_threshold,
    )
    if args.batch_json_out:
        write_rom_switch_materialization_json(batch_report, Path(args.batch_json_out))
    comparison = compare_batch_against_expectations(batch_report, expectations)
    if args.json_out:
        write_comparison_json(comparison, Path(args.json_out))
    if args.json:
        print(json.dumps(comparison, indent=2, sort_keys=True))
    else:
        print(format_violation_report(comparison, limit=args.display_limit))
        if args.json_out:
            print(f"wrote {args.json_out}")
        if args.batch_json_out:
            print(f"wrote {args.batch_json_out}")
    if args.fail_on_violation:
        summary = comparison.get("summary", {})
        if summary.get("fail", 0) or summary.get("error", 0):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
