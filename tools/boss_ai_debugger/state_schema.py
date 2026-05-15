from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import (
    DEFAULT_FIXTURES_PATH,
    PreferenceDataError,
    load_fixtures,
)

from .trace_replay import parse_int_list, parse_trace_file


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRACE_DIR = ROOT / "audit" / "boss_ai_trace"
DEFAULT_TRACE_GLOB = "*_live.txt"
PUBLIC_ONLY_SCOPE = "public_only"
SHA256_RE = re.compile(r"^[0-9A-F]{64}$")

HIDDEN_FIELD_NAMES = {
    "hidden",
    "hidden_info",
    "hidden_moves",
    "hidden_move_slots",
    "private_moves",
    "move_slots",
    "current_input",
    "current_turn_input",
    "selected_move",
    "selected_action",
}

REQUIRED_TRACE_FIELDS = ("trace_rom_sha256", "trace_symbols_sha256", "tier")


def validate_scenario_file(path: Path) -> dict[str, Any]:
    data = read_scenario_data(path)
    scenarios = scenario_rows(data)
    errors: list[str] = []
    for index, scenario in enumerate(scenarios):
        errors.extend(validate_scenario(scenario, f"{path}:scenario[{index}]"))
    return validation_report("scenario_file", len(scenarios), errors)


def validate_fixtures_file(path: Path = DEFAULT_FIXTURES_PATH) -> dict[str, Any]:
    fixtures = load_fixtures(path)
    errors: list[str] = []
    for index, fixture in enumerate(fixtures):
        errors.extend(validate_fixture(fixture, f"{path}:fixtures[{index}]"))
    return validation_report("fixtures", len(fixtures), errors)


def validate_trace_dir(
    path: Path = DEFAULT_TRACE_DIR,
    *,
    pattern: str = DEFAULT_TRACE_GLOB,
) -> dict[str, Any]:
    trace_paths = sorted(path.glob(pattern))
    if not trace_paths:
        return validation_report("trace_dir", 0, [f"{path}: no traces match {pattern!r}"])

    errors: list[str] = []
    checked = 0
    for trace_path in trace_paths:
        blocks = parse_trace_file(trace_path)
        if not blocks:
            errors.append(f"{trace_path}: no trace blocks found")
            continue
        for index, block in enumerate(blocks, start=1):
            checked += 1
            errors.extend(validate_trace_block(block, f"{trace_path}:block[{index}]"))
    return validation_report("trace_dir", checked, errors)


def validate_path(path: Path) -> dict[str, Any]:
    if path.is_dir():
        return validate_trace_dir(path)
    if not path.exists():
        return validation_report("path", 0, [f"{path}: does not exist"])
    if path.suffix.lower() == ".txt":
        errors: list[str] = []
        blocks = parse_trace_file(path)
        for index, block in enumerate(blocks, start=1):
            errors.extend(validate_trace_block(block, f"{path}:block[{index}]"))
        return validation_report("trace_file", len(blocks), errors)
    return validate_scenario_file(path)


def validate_fixture(fixture: dict[str, Any], source: str) -> list[str]:
    errors: list[str] = []
    state = fixture.get("state")
    if not isinstance(state, dict):
        return [f"{source}: state must be an object"]
    errors.extend(validate_public_state(state, f"{source}.state"))

    actions = fixture.get("actions")
    if not isinstance(actions, list) or not actions:
        errors.append(f"{source}: actions must be a non-empty list")
    else:
        for index, action in enumerate(actions):
            errors.extend(validate_action(action, f"{source}.actions[{index}]"))

    errors.extend(find_hidden_fields(fixture, source))
    return errors


def validate_scenario(scenario: dict[str, Any], source: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(scenario, dict):
        return [f"{source}: scenario must be an object"]
    if not scenario.get("id") and not scenario.get("scenario_id"):
        errors.append(f"{source}: missing id or scenario_id")
    for key in ("state_hash", "rom_sha256", "symbols_sha256"):
        value = scenario.get(key)
        if value is not None and value != "" and not valid_sha256(value):
            errors.append(f"{source}.{key}: must be an uppercase SHA-256 hex digest")

    if "state" in scenario:
        state = scenario["state"]
        if isinstance(state, dict):
            errors.extend(validate_public_state(state, f"{source}.state"))
        else:
            errors.append(f"{source}.state: must be an object")

    moves = scenario.get("moves")
    if moves is not None:
        if not isinstance(moves, list) or not moves:
            errors.append(f"{source}.moves: must be a non-empty list")
        else:
            for index, move in enumerate(moves):
                errors.extend(validate_action(move, f"{source}.moves[{index}]"))

    errors.extend(find_hidden_fields(scenario, source))
    return errors


def validate_public_state(state: dict[str, Any], source: str) -> list[str]:
    errors: list[str] = []
    for side in ("boss", "player"):
        side_state = state.get(side)
        if not isinstance(side_state, dict):
            errors.append(f"{source}.{side}: missing side object")
            continue
        active = side_state.get("active")
        if not isinstance(active, dict):
            errors.append(f"{source}.{side}.active: missing active object")
            continue
        for key in ("species", "hp", "status"):
            if key not in active:
                errors.append(f"{source}.{side}.active: missing {key}")
    field = state.get("field")
    if field is not None and not isinstance(field, dict):
        errors.append(f"{source}.field: must be an object")
    return errors


def validate_action(action: Any, source: str) -> list[str]:
    if not isinstance(action, dict):
        return [f"{source}: action must be an object"]
    errors: list[str] = []
    if not action.get("id"):
        errors.append(f"{source}: missing id")
    if not action.get("name"):
        errors.append(f"{source}: missing name")
    kind = action.get("kind")
    if kind is not None and not isinstance(kind, str):
        errors.append(f"{source}.kind: must be a string")
    return errors


def validate_trace_block(fields: dict[str, str], source: str) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_TRACE_FIELDS:
        if key not in fields:
            errors.append(f"{source}: missing {key}")

    move_ids = parse_trace_int_list(fields, "move_ids", source, errors)
    scores = parse_trace_int_list(fields, "move_scores", source, errors)
    pre_model_scores = parse_optional_trace_int_list(
        fields,
        "pre_model_scores",
        source,
        errors,
    )
    post_model_scores = parse_optional_trace_int_list(
        fields,
        "post_model_scores",
        source,
        errors,
    )
    if move_ids is not None and len(move_ids) != 4:
        errors.append(f"{source}: move_ids must contain four bytes")
    if scores is not None and len(scores) != 4:
        errors.append(f"{source}: move_scores must contain four bytes")
    if pre_model_scores is not None and len(pre_model_scores) != 4:
        errors.append(f"{source}: pre_model_scores must contain four bytes")
    if post_model_scores is not None and len(post_model_scores) != 4:
        errors.append(f"{source}: post_model_scores must contain four bytes")
    if move_ids is not None and scores is not None and len(move_ids) != len(scores):
        errors.append(f"{source}: move_ids and move_scores length mismatch")
    if (
        pre_model_scores is not None
        and post_model_scores is not None
        and len(pre_model_scores) != len(post_model_scores)
    ):
        errors.append(
            f"{source}: pre_model_scores and post_model_scores length mismatch"
        )

    tier = fields.get("tier")
    if tier is not None:
        try:
            value = int(tier, 0)
        except ValueError:
            errors.append(f"{source}: tier must be an integer")
        else:
            if value not in {0, 1, 2, 3}:
                errors.append(f"{source}: tier must be 0, 1, 2, or 3")
    return errors


def valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and SHA256_RE.match(value) is not None


def parse_trace_int_list(
    fields: dict[str, str],
    key: str,
    source: str,
    errors: list[str],
) -> list[int] | None:
    if key not in fields:
        errors.append(f"{source}: missing {key}")
        return None
    try:
        values = parse_int_list(fields[key])
    except ValueError:
        errors.append(f"{source}: {key} must be a comma-separated integer list")
        return None
    bad = [value for value in values if value < 0 or value > 255]
    if bad:
        errors.append(f"{source}: {key} contains byte outside 0..255")
    return values


def parse_optional_trace_int_list(
    fields: dict[str, str],
    key: str,
    source: str,
    errors: list[str],
) -> list[int] | None:
    if key not in fields:
        return None
    return parse_trace_int_list(fields, key, source, errors)


def scenario_rows(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict) and isinstance(data.get("scenarios"), list):
        rows = data["scenarios"]
    elif isinstance(data, dict):
        rows = [data]
    else:
        raise PreferenceDataError("scenario file must be an object, list, or scenarios object")
    if not all(isinstance(row, dict) for row in rows):
        raise PreferenceDataError("each scenario row must be an object")
    return list(rows)


def find_hidden_fields(value: Any, source: str) -> list[str]:
    errors: list[str] = []

    def walk(current: Any, path: str) -> None:
        if isinstance(current, dict):
            scope = current.get("public_info_scope", PUBLIC_ONLY_SCOPE)
            for key, child in current.items():
                child_path = f"{path}.{key}"
                if key in HIDDEN_FIELD_NAMES and scope == PUBLIC_ONLY_SCOPE:
                    errors.append(f"{child_path}: hidden-info field in public-only state")
                walk(child, child_path)
        elif isinstance(current, list):
            for index, child in enumerate(current):
                walk(child, f"{path}[{index}]")

    walk(value, source)
    return errors


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PreferenceDataError(f"{path}: invalid JSON: {exc}") from exc


def read_scenario_data(path: Path) -> Any:
    if path.suffix.lower() != ".jsonl":
        return read_json(path)
    rows = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            rows.append(json.loads(raw))
        except json.JSONDecodeError as exc:
            raise PreferenceDataError(f"{path}:{line_number}: invalid JSONL row: {exc}") from exc
    return rows


def validation_report(kind: str, checked_count: int, errors: list[str]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": kind,
        "checked_count": checked_count,
        "error_count": len(errors),
        "valid": not errors,
        "errors": errors,
    }


def combine_reports(kind: str, reports: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    checked = 0
    for report in reports:
        checked += int(report.get("checked_count", 0))
        errors.extend(str(error) for error in report.get("errors", []))
    return validation_report(kind, checked, errors)


def format_validation_report(report: dict[str, Any]) -> str:
    status = "passed" if report["valid"] else "failed"
    lines = [
        f"Boss AI state schema validation {status}.",
        f"kind={report['kind']} checked={report['checked_count']} errors={report['error_count']}",
    ]
    for error in report["errors"][:20]:
        lines.append(f"  - {error}")
    if len(report["errors"]) > 20:
        lines.append(f"  ... {len(report['errors']) - 20} more")
    return "\n".join(lines)
