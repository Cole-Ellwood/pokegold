#!/usr/bin/env python3
"""Audit the `python -m tools.debugger next` symptom-row coverage.

Paired audit for the debugger_next_command_paired_slice phase (Claude lane).
Codex's tools/debugger/next_steps.py exports NEXT_STEP_ROWS — a list of dicts
the router consumes to map a symptom string to the shortest proof path.

Each row carries:
  symptom_class       — stable class id (used by audits + CLI matchers)
  matched_lane        — workstream lane the symptom belongs to
  title               — human display string
  keywords            — list of matcher strings for the symptom router
  first_command       — the recommended `python ...` proof command
  required_inputs     — list describing what the user must supply
  proof_limit         — explicit statement of what the first command DOES NOT prove
  escalation_command  — follow-up command if the first command can't finish the diagnosis

This audit confirms that the row table covers the boss-AI feature classes that
shipped in the 7-phase + retrofit roadmap (P1H Haki, P2 KO-band oracle, P3
revealed-effect matrix, P5 observation log + tendency, P6 role classifier, P7
coach plan templates, plus the two general scoring symptom classes the locked
roadmap implied). If a future commit removes a row without replacing it, this
audit fires so the debugger UX doesn't silently regress for an entire feature
class.

Checks:

  (a) Module loads: `from tools.debugger.next_steps import NEXT_STEP_ROWS`
      succeeds and the constant is a non-empty list of dicts.

  (b) Required symptom_class coverage: every required class id appears in at
      least one row. The required set covers all 8 boss-AI feature classes
      shipped in the roadmap.

  (c) Required-field presence + non-empty (excluding escalation_command which
      may legitimately be empty for terminal rows):
        symptom_class, matched_lane, first_command, required_inputs, proof_limit
      Plus escalation_command must be PRESENT as a key (may be empty string).

  (d) Type discipline: first_command + proof_limit are strings; required_inputs
      is a list (even if it contains exactly one "none; ..." string); keywords
      is a list of strings when present; title is a string when present.

  (e) No duplicate symptom_class entries (a class id appearing twice would make
      the router's symptom -> row lookup ambiguous).

  (f) --json output sanity: a `general` fallback row is present so the router
      always has SOMETHING to return when no keyword matches.

The audit is intentionally simple — it doesn't try to validate that
first_command actually runs (that's the unittest's job) or that proof_limit
prose is honest (that's the slice review's job). It just confirms the table's
contract shape so downstream consumers (the CLI, unittests, future audits) can
rely on the row layout.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

REQUIRED_SYMPTOM_CLASSES = (
    # The 8 boss-AI feature classes shipped in the 7-phase + retrofit roadmap.
    "haki_taunt_read",
    "ko_band_pressure",
    "revealed_effect_response",
    "observation_tendency_behavior",
    "role_package",
    "coach_template",
    # The two scoring symptom classes the locked roadmap implied.
    "wrong_switch",
    "wrong_move_score",
)

NON_EMPTY_FIELDS = (
    "symptom_class",
    "matched_lane",
    "first_command",
    "required_inputs",
    "proof_limit",
)

# escalation_command must be present but may be empty for terminal rows.
PRESENT_FIELDS = NON_EMPTY_FIELDS + ("escalation_command",)


def check_module_loads() -> tuple[bool, str, list[dict] | None]:
    """(a) Module loads, NEXT_STEP_ROWS is a non-empty list of dicts."""
    try:
        from tools.debugger.next_steps import NEXT_STEP_ROWS  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return False, f"(a) FAIL: could not import NEXT_STEP_ROWS: {exc}", None
    if not isinstance(NEXT_STEP_ROWS, list):
        return False, f"(a) FAIL: NEXT_STEP_ROWS is {type(NEXT_STEP_ROWS).__name__}, expected list", None
    if not NEXT_STEP_ROWS:
        return False, "(a) FAIL: NEXT_STEP_ROWS is empty", None
    for i, row in enumerate(NEXT_STEP_ROWS):
        if not isinstance(row, dict):
            return False, f"(a) FAIL: NEXT_STEP_ROWS[{i}] is {type(row).__name__}, expected dict", None
    return True, f"(a) PASS: NEXT_STEP_ROWS loaded with {len(NEXT_STEP_ROWS)} row(s).", NEXT_STEP_ROWS


def check_symptom_class_coverage(rows: list[dict]) -> tuple[bool, str]:
    """(b) Every required symptom_class appears in at least one row."""
    seen = {row.get("symptom_class") for row in rows}
    missing = [c for c in REQUIRED_SYMPTOM_CLASSES if c not in seen]
    if missing:
        return False, (
            f"(b) FAIL: missing required symptom_class id(s): {', '.join(missing)}. "
            f"Add a row to tools/debugger/next_steps.py for each."
        )
    return True, f"(b) PASS: all {len(REQUIRED_SYMPTOM_CLASSES)} required symptom classes covered."


def check_required_fields(rows: list[dict]) -> tuple[bool, str]:
    """(c) Every row has the required keys, and the non-empty subset is non-empty."""
    errors: list[str] = []
    for i, row in enumerate(rows):
        cls = row.get("symptom_class", f"<row {i}>")
        for field in PRESENT_FIELDS:
            if field not in row:
                errors.append(f"{cls}: missing key '{field}'")
        for field in NON_EMPTY_FIELDS:
            value = row.get(field)
            if value is None or value == "" or value == []:
                errors.append(f"{cls}: '{field}' is empty (must be non-empty)")
    if errors:
        return False, "(c) FAIL: required-field issues:\n      " + "\n      ".join(errors[:12])
    return True, f"(c) PASS: all {len(rows)} rows have required fields with non-empty NON_EMPTY_FIELDS subset."


def check_field_types(rows: list[dict]) -> tuple[bool, str]:
    """(d) Type discipline on the row fields."""
    errors: list[str] = []
    for i, row in enumerate(rows):
        cls = row.get("symptom_class", f"<row {i}>")
        if "first_command" in row and not isinstance(row["first_command"], str):
            errors.append(f"{cls}: first_command should be str, got {type(row['first_command']).__name__}")
        if "proof_limit" in row and not isinstance(row["proof_limit"], str):
            errors.append(f"{cls}: proof_limit should be str, got {type(row['proof_limit']).__name__}")
        if "required_inputs" in row and not isinstance(row["required_inputs"], list):
            errors.append(f"{cls}: required_inputs should be list, got {type(row['required_inputs']).__name__}")
        if "escalation_command" in row and not isinstance(row["escalation_command"], str):
            errors.append(f"{cls}: escalation_command should be str (possibly ''), got {type(row['escalation_command']).__name__}")
        if "keywords" in row:
            if not isinstance(row["keywords"], list):
                errors.append(f"{cls}: keywords should be list, got {type(row['keywords']).__name__}")
            else:
                for j, kw in enumerate(row["keywords"]):
                    if not isinstance(kw, str):
                        errors.append(f"{cls}: keywords[{j}] should be str, got {type(kw).__name__}")
                        break
        if "title" in row and not isinstance(row["title"], str):
            errors.append(f"{cls}: title should be str, got {type(row['title']).__name__}")
    if errors:
        return False, "(d) FAIL: type-discipline issues:\n      " + "\n      ".join(errors[:12])
    return True, "(d) PASS: row field types are consistent."


def check_no_duplicate_classes(rows: list[dict]) -> tuple[bool, str]:
    """(e) No duplicate symptom_class entries."""
    seen: dict[str, int] = {}
    for row in rows:
        cls = row.get("symptom_class")
        if cls is None:
            continue
        seen[cls] = seen.get(cls, 0) + 1
    dupes = [(cls, count) for cls, count in seen.items() if count > 1]
    if dupes:
        return False, "(e) FAIL: duplicate symptom_class entries: " + ", ".join(
            f"{cls} x{count}" for cls, count in dupes
        )
    return True, f"(e) PASS: {len(seen)} unique symptom_class id(s); no duplicates."


def check_general_fallback(rows: list[dict]) -> tuple[bool, str]:
    """(f) A `general` fallback row is present for unmatched symptoms."""
    if not any(row.get("symptom_class") == "general" for row in rows):
        return False, (
            "(f) FAIL: no row with symptom_class='general'. The router needs a "
            "fallback row so unmatched symptoms still return a proof path."
        )
    return True, "(f) PASS: `general` fallback row present."


def main() -> int:
    ok_load, msg_load, rows = check_module_loads()
    print(msg_load)
    if not ok_load or rows is None:
        return 1
    checks = [
        check_symptom_class_coverage(rows),
        check_required_fields(rows),
        check_field_types(rows),
        check_no_duplicate_classes(rows),
        check_general_fallback(rows),
    ]
    for _, m in checks:
        print(m)
    print()
    if all(ok for ok, _ in checks):
        print("PASS: debugger `next` symptom-row coverage green (load + coverage + fields + types + uniqueness + fallback).")
        return 0
    print("FAIL: debugger `next` symptom-row coverage had failures above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
