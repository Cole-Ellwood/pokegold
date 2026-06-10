from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.debugger.canonical_state_class import build_canonical_state_class, stable_json_hash
from tools.debugger.report_envelope import (
    PROOF_ARTIFACT_PATH_PREFIXES,
    dirty_diff_hash,
    sha256_file,
    source_tree_hash,
)

from .rule_map import ROOT, SOURCE_PATHS, build_rule_map


DEFAULT_TRACE_ROM = ROOT / "pokegold_trace.gbc"
DEFAULT_TRACE_SYMBOLS = ROOT / "pokegold_trace.sym"
BOSS_AI_PROOF_ARTIFACT_DIRS = PROOF_ARTIFACT_PATH_PREFIXES


def boss_ai_generated_identity(
    *,
    rom_path: Path | str = DEFAULT_TRACE_ROM,
    symbols_path: Path | str = DEFAULT_TRACE_SYMBOLS,
    root: Path = ROOT,
) -> dict[str, str]:
    rom = Path(rom_path)
    symbols = Path(symbols_path)
    rule_map = build_rule_map(SOURCE_PATHS)
    return {
        "rom_sha256": sha256_file(rom, root=root) or "missing",
        "symbols_sha256": sha256_file(symbols, root=root) or "missing",
        "map_sha256": sha256_file(rom.with_suffix(".map"), root=root) or "missing",
        "rule_map_sha256": stable_json_hash(
            {
                "schema_version": rule_map.get("schema_version"),
                "source_hashes": rule_map.get("source_hashes", {}),
                "rules": rule_map.get("rules", []),
            }
        ),
        "source_tree_sha256": boss_ai_source_tree_hash(root),
        "dirty_diff_hash": boss_ai_source_dirty_diff_hash(root),
    }


def boss_ai_source_dirty_diff_hash(root: Path = ROOT) -> str:
    return dirty_diff_hash(root, exclude_path_prefixes=BOSS_AI_PROOF_ARTIFACT_DIRS)


def boss_ai_source_tree_hash(root: Path = ROOT) -> str:
    # Content-scoped replacement for a HEAD pointer in the proof identity:
    # committing already-validated artifacts must not void them, while any
    # tracked source change still does.
    return source_tree_hash(root, exclude_path_prefixes=BOSS_AI_PROOF_ARTIFACT_DIRS)


def boss_ai_trace_identity(
    fields: dict[str, Any],
    *,
    root: Path = ROOT,
) -> dict[str, str]:
    identity = boss_ai_generated_identity(root=root)
    rom_sha = str(fields.get("trace_rom_sha256") or fields.get("rom_sha256") or "").strip()
    symbols_sha = str(
        fields.get("trace_symbols_sha256") or fields.get("symbols_sha256") or ""
    ).strip()
    if rom_sha:
        identity["rom_sha256"] = rom_sha
    if symbols_sha:
        identity["symbols_sha256"] = symbols_sha
    trace_rom = str(fields.get("trace_rom") or fields.get("rom") or "").strip()
    if trace_rom:
        identity["map_sha256"] = sha256_file(Path(trace_rom).with_suffix(".map"), root=root) or identity[
            "map_sha256"
        ]
    return identity


def build_generated_scenario_class(
    scenario: dict[str, Any],
    *,
    identity: dict[str, str],
) -> dict[str, Any]:
    expectation = scenario.get("expectation") if isinstance(scenario.get("expectation"), dict) else {}
    moves = scenario.get("moves") if isinstance(scenario.get("moves"), list) else []
    source_refs = expectation.get("evidence_refs", []) if isinstance(expectation, dict) else []
    public_facts = {
        "scenario_id": scenario.get("id") or scenario.get("scenario_id", ""),
        "family": scenario.get("family", ""),
        "policy_case": scenario.get("policy_case", ""),
        "tier": scenario.get("tier", ""),
        "seed": scenario.get("seed", ""),
        "case_index": scenario.get("case_index", ""),
        "condition_tags": expectation.get("condition_tags", []),
        "policy_tags": expectation.get("policy_tags", []),
        "best_action_ids": expectation.get("best_action_ids", []),
        "acceptable_action_ids": expectation.get("acceptable_action_ids", []),
        "bad_action_ids": expectation.get("bad_action_ids", []),
        "moves": [
            {
                "id": move.get("id", ""),
                "name": move.get("name", ""),
                "kind": move.get("kind", ""),
                "blocked": bool(move.get("blocked", False)),
            }
            for move in moves
            if isinstance(move, dict)
        ],
    }
    return build_canonical_state_class(
        surface="boss_ai",
        identity=identity,
        public_facts=public_facts,
        surface_facts={
            "boss_ai": {
                "decision_surface": "generated_scenario",
                "generator": scenario.get("generator", ""),
                "generator_source": scenario.get("generator_source", ""),
                "state_hash": scenario.get("state_hash", ""),
                "replay_source": scenario.get("replay_source", {}),
                "mastery_source": scenario.get("mastery_source", {}),
            }
        },
        backend="static_plus_generated_scenario",
        proof_status="missing_proof_artifact",
        raw_state_provenance={
            "kind": "boss_ai_generated_scenario",
            "scenario_id": scenario.get("id") or scenario.get("scenario_id", ""),
            "state_hash": scenario.get("state_hash", ""),
        },
        missing_evidence=["rom_backed_proof_artifact"],
        blocking_gaps=["boss_ai_generated_scenario_lacks_rom_proof_artifact"],
        known_limits=[
            "Generated scenario class ids identify public scenario classes before ROM proof.",
        ],
        source_refs=source_refs if isinstance(source_refs, list) else [],
    )


def build_live_trace_class(
    fields: dict[str, Any],
    *,
    trace_path: Path | str = "",
    capture_index: int | None = None,
    identity: dict[str, str] | None = None,
) -> dict[str, Any]:
    capture_id = live_trace_capture_id(fields, trace_path=trace_path, capture_index=capture_index)
    move_ids = parse_csv_ints(fields.get("move_ids", ""))
    move_scores = parse_csv_ints(fields.get("move_scores", ""))
    return build_canonical_state_class(
        surface="boss_ai",
        identity=identity or boss_ai_trace_identity(fields),
        public_facts={
            "boss": fields.get("boss", ""),
            "tier": fields.get("tier", ""),
            "move_ids": move_ids,
            "move_scores": move_scores,
            "pre_model_scores": parse_csv_ints(fields.get("pre_model_scores", "")),
            "post_model_scores": parse_csv_ints(fields.get("post_model_scores", "")),
            "model_score_deltas": parse_delta_list(fields.get("model_score_deltas", "")),
            "switch_confidence": parse_optional_int(fields.get("switch_confidence", "")),
            "plan_id": parse_optional_int(fields.get("plan_id", "")),
            "plan_phase": parse_optional_int(fields.get("plan_phase", "")),
            "plan_confidence": parse_optional_int(fields.get("plan_confidence", "")),
            "plausible_mask": parse_hex_byte_list(fields.get("plausible_mask", "")),
            "revealed_masks": parse_hex_byte_list(fields.get("revealed_masks", "")),
            "risk_flags": fields.get("risk_flags", ""),
            "lookahead_bonus_top": parse_csv_ints(fields.get("lookahead_bonus_top", "")),
            "switch_context": fields.get("switch_context", ""),
        },
        reachable_proof={
            "chosen": fields.get("chosen", ""),
            "top_moves": fields.get("top_moves", ""),
            "chosen_id": parse_optional_int(fields.get("chosen_id", "")),
            "chosen_slot": parse_optional_int(fields.get("chosen_slot", "")),
            "cur_enemy_move_id": parse_optional_int(fields.get("cur_enemy_move_id", "")),
        },
        surface_facts={
            "boss_ai": {
                "decision_surface": "live_trace_capture",
                "public_state_completeness": "selector_trace_fields_only",
            }
        },
        backend="pyboy",
        proof_status="emulator_evidence",
        raw_state_provenance={
            "kind": "boss_ai_live_trace_block",
            "capture_id": capture_id,
            "trace_path": str(trace_path),
            "capture_index": capture_index,
        },
        known_limits=[
            "Live trace class ids identify captured decisions; they are PyBoy evidence, not hardware proof.",
            "Live trace blocks omit full public battle state such as HP bands, species, status, hazards, and party facts.",
        ],
        source_refs=[str(trace_path)] if trace_path else [],
    )


def build_rom_contribution_trace_class(report: dict[str, Any]) -> dict[str, Any]:
    trace_basis = report.get("trace_basis", {}) if isinstance(report.get("trace_basis"), dict) else {}
    identity = boss_ai_trace_identity(
        {
            "trace_rom_sha256": trace_basis.get("trace_rom_sha256", ""),
            "trace_symbols_sha256": trace_basis.get("trace_symbols_sha256", ""),
        }
    )
    executed_rule_ids = sorted(str(item) for item in report.get("executed_rule_ids", []) if str(item))
    if not executed_rule_ids:
        executed_rule_ids = sorted(
            {
                str((event.get("source") or {}).get("rule_id", ""))
                for event in [
                    *dict_items(report.get("rule_entries")),
                    *dict_items(report.get("predicate_branch_entries")),
                    *dict_items(report.get("public_read_probe_entries")),
                    *dict_items(report.get("events")),
                ]
                if isinstance(event.get("source"), dict)
                and str(event.get("source", {}).get("rule_id", ""))
            }
        )
    trace_id = str(report.get("trace_id") or report.get("scenario_id") or report.get("save_state", ""))
    return build_canonical_state_class(
        surface="boss_ai",
        identity=identity,
        public_facts={
            "move_ids": report.get("move_ids", []),
            "move_scores": report.get("move_scores", []),
            "pre_model_scores": report.get("pre_model_scores", []),
            "post_model_scores": report.get("post_model_scores", []),
            "executed_rule_ids": executed_rule_ids,
            "changed_event_count": report.get("changed_event_count", 0),
        },
        known_to_engine_facts={"chosen": report.get("chosen", {})},
        surface_facts={
            "boss_ai": {
                "decision_surface": report.get("decision_surface", "rom_contribution_trace"),
                "source": report.get("source", ""),
                "event_count": report.get("event_count", 0),
                "rule_entry_count": report.get("rule_entry_count", 0),
                "predicate_branch_entry_count": report.get("predicate_branch_entry_count", 0),
                "public_read_probe_entry_count": report.get("public_read_probe_entry_count", 0),
            }
        },
        backend="pyboy",
        proof_status="emulator_evidence",
        raw_state_provenance={
            "kind": "boss_ai_rom_contribution_trace",
            "trace_id": trace_id,
            "save_state": report.get("save_state", ""),
        },
        known_limits=[
            "ROM contribution trace class ids identify PyBoy hook traces; they are not hardware proof.",
        ],
    )


def scenario_class_fields(scenario: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for key in ("class_id", "class_fingerprint", "canonical_state_class"):
        value = scenario.get(key)
        if value not in (None, ""):
            fields[key] = value
    return fields


def scenario_decision_class_fields(scenario: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    mapping = {
        "class_id": "decision_class_id",
        "class_fingerprint": "decision_class_fingerprint",
        "canonical_state_class": "decision_canonical_state_class",
    }
    for source_key, target_key in mapping.items():
        value = scenario.get(source_key)
        if value not in (None, ""):
            fields[target_key] = value
    return fields


def canonical_class_fields(canonical: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(canonical, dict):
        return {}
    return {
        "canonical_state_class": canonical,
        "class_id": canonical.get("class_id", ""),
        "class_fingerprint": canonical.get("class_fingerprint", ""),
    }


def live_trace_capture_id(
    fields: dict[str, Any],
    *,
    trace_path: Path | str = "",
    capture_index: int | None = None,
) -> str:
    boss = str(fields.get("boss") or Path(str(trace_path)).stem or "boss_ai_trace")
    index = str(fields.get("capture_index") or capture_index or 1)
    return f"{boss}#{index}"


def parse_csv_ints(value: Any) -> list[int]:
    if value in (None, ""):
        return []
    out: list[int] = []
    for part in str(value).split(","):
        part = part.strip()
        if not part:
            continue
        parsed = parse_optional_int(part)
        if parsed is not None:
            out.append(parsed)
    return out


def parse_delta_list(value: Any) -> list[int]:
    if value in (None, ""):
        return []
    out: list[int] = []
    for part in str(value).split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(int(part, 10))
        except ValueError:
            parsed = parse_optional_int(part)
            if parsed is not None:
                out.append(parsed)
    return out


def parse_hex_byte_list(value: Any) -> list[int]:
    if value in (None, ""):
        return []
    out: list[int] = []
    for part in str(value).replace(",", " ").split():
        parsed = parse_optional_int(f"0x{part}" if all(ch in "0123456789ABCDEFabcdef" for ch in part) else part)
        if parsed is not None:
            out.append(parsed & 0xFF)
    return out


def parse_optional_int(value: Any) -> int | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        return int(str(value).strip(), 0)
    except ValueError:
        return None


def dict_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []
