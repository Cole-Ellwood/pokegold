from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from tools.debugger.canonical_state_class import (
    build_canonical_state_class,
    stable_json_hash,
)
from tools.debugger.report_envelope import build_report_envelope
from tools.debugger.report_envelope import sha256_file

from .coverage_report import (
    coverage_target_worklist,
    public_read_provenance_summary,
    recommended_trace_mode,
    suggested_generator,
    summarize_contribution_sources,
)
from .rom_contribution_trace import load_rom_contribution_trace
from .canonical_classes import boss_ai_source_dirty_diff_hash, boss_ai_source_tree_hash
from .rule_map import (
    GENERIC_LOCAL_LABELS,
    LABEL_RE,
    ROOT,
    SOURCE_PATHS,
    build_rule_map,
    full_symbol_for_label,
)


SCHEMA_VERSION = 1
DEFAULT_TRACE_ROM = Path("pokegold_trace.gbc")
DEFAULT_TRACE_SYMBOLS = Path("pokegold_trace.sym")
EXHAUSTIVE_WITNESS_ROLES = (
    "positive",
    "negative",
    "boundary",
    "public_read_provenance",
    "counterfactual_flip",
)
EXHAUSTIVE_WITNESS_CATALOG_EVIDENCE_ID = "boss_ai_exhaustive_witness_class_catalog.cataloged"
DEFAULT_DEITY_PACKET_PATHS = (
    Path("audit/boss_ai_debugger/deity_benchmark/artifacts/falkner_first_decision.json"),
    Path("audit/boss_ai_debugger/deity_benchmark/artifacts/shared_switch_dispatch.json"),
    Path("audit/boss_ai_debugger/deity_benchmark/artifacts/generated_active_pressure.json"),
    Path("audit/boss_ai_debugger/deity_benchmark/artifacts/score_rule_spikes_spin.json"),
    Path("audit/boss_ai_debugger/deity_benchmark/artifacts/switch_sack_materialization.json"),
)
DEFAULT_SCORE_MATERIALIZATION_SOURCES = (
    (
        Path("audit/boss_ai_debugger/god_level_benchmark/artifacts/score_witness_materializations"),
        "*.json",
    ),
)
DEFAULT_COUNTERFACTUAL_MATERIALIZATION_SOURCES = (
    (
        Path("audit/boss_ai_debugger/god_level_benchmark/artifacts/counterfactual_witness_materializations"),
        "*.json",
    ),
)
COUNTERFACTUAL_MATERIALIZATION_KIND = "rom_counterfactual_witness_materialization"
COUNTERFACTUAL_MATERIALIZATION_PROOF_SCOPE = "boss_ai.counterfactual_flip"
COUNTERFACTUAL_MUTATION_ALLOWLIST = "boss_ai_public_or_boss_owned_counterfactual_v1"
SWITCH_OBSERVABLE_SHARED_RULE_IDS = frozenset(
    {
        "move.get_tier_plausible_risk_weight",
        "move.get_speculative_plausible_risk_weight",
        "move.maybe_mark_scout_pivot",
    }
)
MOVE_OBSERVABLE_SWITCH_RULE_IDS = frozenset(
    {
        "switch.choose_best_oracle_move",
        "switch.commit_haki_oracle_choice",
        "switch.oracle_haki_after_player_action",
        "switch.rebuild_haki_move_scores",
        "switch.decay_switch_cooldown",
    }
)
NON_DISCRIMINATING_COUNTERFACTUAL_BRANCH_OUTCOMES = frozenset(
    {
        "entered",
        "loaded",
    }
)
ALLOWED_COUNTERFACTUAL_MUTATION_KEYS = frozenset(
    {
        "wBossAISwitchConfidence",
        "wBossAITurnsElapsed",
        "wBossAIPlayerSwitchCount",
        "wBossAIObsCount",
        "wBossAIObsEntries",
        "wEnemySwitchMonParam",
        "wOtherTrainerClass",
        "wOtherTrainerID",
        "wEnemyMoveStruct",
        "wEnemyMoveStruct+1",
        "wEnemyMoveStruct+2",
        "wEnemyMoveStruct+3",
        "wEnemyMoveStruct+4",
        "wEnemyMonHP",
        "wEnemyMonHP+1",
        "wEnemyMonMaxHP",
        "wEnemyMonMaxHP+1",
        "wEnemyMonStatus",
        "wEnemyMonType1",
        "wEnemyMonType2",
        "wEnemyStatLevels",
        "wEnemyStatLevels+1",
        "wEnemyStatLevels+2",
        "wEnemyStatLevels+3",
        "wEnemyStatLevels+4",
        "wEnemyStatLevels+5",
        "wEnemyStatLevels+6",
        "wPlayerScreens",
        "wPlayerSubStatus1",
        "wPlayerSubStatus2",
        "wPlayerSubStatus3",
        "wPlayerSubStatus4",
        "wPlayerSubStatus5",
        "wBattleMonHP",
        "wBattleMonHP+1",
        "wBattleMonMaxHP",
        "wBattleMonMaxHP+1",
        "wBattleMonStatus",
        "wBattleMonType1",
        "wBattleMonType2",
        "wPlayerUsedMoves",
        "wPlayerUsedMoves+1",
        "wPlayerUsedMoves+2",
        "wPlayerUsedMoves+3",
        "wOTPartyCount",
        "wOTPartyMon1HP",
        "wOTPartyMon1HP+1",
        "wOTPartyMon2HP",
        "wOTPartyMon2HP+1",
        "wOTPartyMon3HP",
        "wOTPartyMon3HP+1",
        "wOTPartyMon4HP",
        "wOTPartyMon4HP+1",
        "wOTPartyMon5HP",
        "wOTPartyMon5HP+1",
        "wOTPartyMon6HP",
        "wOTPartyMon6HP+1",
    }
)


def build_boss_ai_universe_report(
    *,
    source_paths: tuple[Path, ...] = SOURCE_PATHS,
    rule_map_data: dict[str, Any] | None = None,
    rom_contribution_trace_paths: list[Path] | None = None,
    rom_score_materialization_paths: list[Path] | None = None,
    rom_counterfactual_materialization_paths: list[Path] | None = None,
    deity_packet_paths: list[Path] | None = None,
    rom_path: Path | str = DEFAULT_TRACE_ROM,
    symbols_path: Path | str = DEFAULT_TRACE_SYMBOLS,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Inventory the current Boss AI proof universe without proving it complete."""

    rule_map = rule_map_data if rule_map_data is not None else build_rule_map(source_paths)
    rules = list(rule_map.get("rules", []))
    rule_by_full_symbol = {
        full_symbol_for_rule(rule): rule
        for rule in rules
        if full_symbol_for_rule(rule)
    }
    label_rows = scan_boss_ai_label_rows(source_paths, rule_by_full_symbol=rule_by_full_symbol, root=root)
    class_identity = boss_ai_class_identity(
        rule_map,
        rom_path=rom_path,
        symbols_path=symbols_path,
        root=root,
    )
    score_materialization_paths = resolve_score_materialization_paths(
        rom_score_materialization_paths,
        root=root,
    )
    counterfactual_materialization_paths = resolve_counterfactual_materialization_paths(
        rom_counterfactual_materialization_paths,
        root=root,
    )
    class_rows = build_canonical_class_rows(rules, identity=class_identity)
    rule_surfaces = {
        str(row.get("rule_id", "")): str(row.get("decision_surface", ""))
        for row in class_rows
        if row.get("rule_id")
    }
    score_materialization_contribution_reports = (
        contribution_reports_from_score_materializations(
            score_materialization_paths,
            root=root,
        )
    )
    contribution_summary = summarize_contribution_sources(
        rom_contribution_trace_paths=rom_contribution_trace_paths,
        rom_contribution_reports=score_materialization_contribution_reports,
    )
    covered_rule_ids = set(str(rule_id) for rule_id in contribution_summary.get("executed_rule_ids", []))
    coverage_targets = coverage_target_worklist(rule_map, covered_rule_ids)
    public_reads = public_read_provenance_summary(rule_map, contribution_summary)
    witness_evidence = build_witness_evidence_from_contribution_summary(
        contribution_summary,
        root=root,
    )
    add_witness_evidence_from_score_materialization_artifacts(
        witness_evidence,
        score_materialization_paths,
        root=root,
    )
    add_witness_evidence_from_counterfactual_materialization_artifacts(
        witness_evidence,
        counterfactual_materialization_paths,
        rule_surfaces=rule_surfaces,
        identity=class_identity,
        root=root,
    )
    add_witness_evidence_from_deity_packets(
        witness_evidence,
        deity_packet_paths if deity_packet_paths is not None else list(DEFAULT_DEITY_PACKET_PATHS),
        root=root,
    )
    witness_inventory = build_exhaustive_class_witness_inventory(
        class_rows,
        witness_evidence=witness_evidence,
    )
    witness_catalog = build_exhaustive_class_witness_catalog(
        class_rows,
        identity=class_identity,
        witness_evidence=witness_evidence,
    )
    counters = boss_ai_universe_counters(
        label_rows=label_rows,
        rules=rules,
        coverage_targets=coverage_targets,
        public_reads=public_reads,
        class_rows=class_rows,
        witness_inventory=witness_inventory,
    )
    blocking_gaps = boss_ai_universe_blocking_gaps(counters)
    ready = all(value == 0 for value in counters.values())
    closed_evidence_ids = [
        "boss_ai_universe.source_labels_scanned",
        "boss_ai_universe.rule_map_consumed",
        "boss_ai_universe.coverage_targets_reported",
    ]
    if witness_catalog.get("ready"):
        closed_evidence_ids.append(EXHAUSTIVE_WITNESS_CATALOG_EVIDENCE_ID)
    envelope = build_report_envelope(
        kind="boss_ai_debugger_universe",
        command="python -m tools.boss_ai_debugger universe",
        inputs={
            "source_paths": [repo_rel(root, path) for path in source_paths],
            "rom_contribution_trace_artifacts": contribution_summary.get("artifact_count", 0),
            "rom_counterfactual_materialization_artifacts": len(counterfactual_materialization_paths),
        },
        rom_path=rom_path,
        symbols_path=symbols_path,
        backend="static_plus_trace_artifacts",
        proof_status="complete" if ready else "missing_evidence",
        missing_evidence=blocking_gaps,
        blocking_gaps=blocking_gaps,
        known_limits=[
            "This is an inventory extractor, not a proof database.",
            "Unmapped labels are treated as reachable until a control-flow/dead-label proof classifies them.",
            "Rule-target class ids do not prove every raw live/generated/materialized decision class yet.",
        ],
        closed_evidence_ids=closed_evidence_ids,
        repro_command="python -m tools.boss_ai_debugger universe --json",
        disproof_standard=[
            "Every non-generic reachable Boss AI label is mapped to a rule id or an explicit unsupported/unreachable reason.",
            "Every public-read rule has observed public-input/probe provenance.",
            "Every dynamic rule has a canonical class id and materialization/proof path.",
        ],
        root=root,
    )
    envelope.update(
        {
            "schema_version": SCHEMA_VERSION,
            "source_hashes": dict(rule_map.get("source_hashes", {})),
            "class_identity": class_identity,
            "rule_count": len(rules),
            "reachable_label_count": sum(
                1 for row in label_rows if not row["reachable_status"].endswith("_ignored")
            ),
            "unmapped_label_count": counters["missing_reachable_label_count"],
            "dead_label_count": 0,
            "public_read_target_count": public_reads.get("target_rule_count", 0),
            "missing_public_read_provenance_count": counters["missing_public_read_count"],
            "dynamic_coverage_target_count": sum(
                1 for rule in rules if rule.get("dynamic_coverage_target", False)
            ),
            "dynamic_uncovered_rule_count": counters["missing_branch_count"],
            "stale_basis": False,
            "next_command": first_next_command(label_rows, class_rows),
            "counters": counters,
            "surface_rows": label_rows,
            "canonical_class_rows": class_rows,
            "exhaustive_class_witness_inventory": witness_inventory,
            "exhaustive_class_witness_catalog": witness_catalog,
            "coverage_targets": coverage_targets,
            "public_read_provenance": public_reads,
            "rom_contribution_trace": {
                key: value
                for key, value in contribution_summary.items()
                if key != "artifacts"
            },
        }
    )
    return envelope


def scan_boss_ai_label_rows(
    source_paths: Iterable[Path],
    *,
    rule_by_full_symbol: dict[str, dict[str, Any]],
    root: Path = ROOT,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in source_paths:
        parent: str | None = None
        for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            code = raw_line.split(";", 1)[0].strip()
            match = LABEL_RE.match(code)
            if match is None:
                continue
            label = match.group("local") or match.group("top")
            if not label.startswith("."):
                parent = label
            full_symbol = full_symbol_for_label(label, parent)
            rule = rule_by_full_symbol.get(full_symbol)
            generic = label in GENERIC_LOCAL_LABELS
            if rule is not None:
                reachable_status = (
                    "reachable_dynamic_target"
                    if rule.get("dynamic_coverage_target", False)
                    else "reachable_static_reference"
                )
                classification = str(rule.get("classification", ""))
                proof_mode = recommended_trace_mode(rule)
                unsupported_reason = ""
                rule_id = str(rule.get("rule_id", ""))
                materializer_command = materializer_command_for_rule(rule)
            elif label.startswith(".") and parent and parent in rule_by_full_symbol:
                parent_rule = rule_by_full_symbol[parent]
                reachable_status = "reachable_parent_rule_detail"
                classification = str(parent_rule.get("classification", ""))
                proof_mode = recommended_trace_mode(parent_rule)
                unsupported_reason = (
                    "local implementation label owned by parent rule; "
                    "not an independent proof target"
                )
                rule_id = str(parent_rule.get("rule_id", ""))
                materializer_command = materializer_command_for_rule(parent_rule)
            elif generic:
                reachable_status = "generic_control_flow_ignored"
                classification = "generic_control_flow"
                proof_mode = ""
                unsupported_reason = "generic local control-flow label; not a proof class in this slice"
                rule_id = ""
                materializer_command = ""
            else:
                reachable_status = "reachable_unmapped_label"
                classification = "unclassified"
                proof_mode = ""
                unsupported_reason = "label is not classified by Boss AI rule_map"
                rule_id = ""
                materializer_command = "python -m tools.boss_ai_debugger rule-map build --json"
            rows.append(
                {
                    "surface_id": safe_id(f"boss_ai:{full_symbol}"),
                    "rule_id": rule_id,
                    "source_file": repo_rel(root, path),
                    "line": line_number,
                    "source_label": label,
                    "parent_label": parent,
                    "full_symbol": full_symbol,
                    "classification": classification,
                    "reachable_status": reachable_status,
                    "unsupported_reason": unsupported_reason,
                    "proof_mode": proof_mode,
                    "materializer_command": materializer_command,
                }
            )
    return rows


def boss_ai_class_identity(
    rule_map: dict[str, Any],
    *,
    rom_path: Path | str,
    symbols_path: Path | str,
    root: Path,
) -> dict[str, str]:
    rom = Path(rom_path)
    symbols = Path(symbols_path)
    map_path = rom.with_suffix(".map")
    return {
        "rom_sha256": sha256_file(rom, root=root),
        "symbols_sha256": sha256_file(symbols, root=root),
        "map_sha256": sha256_file(map_path, root=root),
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


def build_canonical_class_rows(
    rules: list[dict[str, Any]],
    *,
    identity: dict[str, str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rule in rules:
        if not rule.get("dynamic_coverage_target", False):
            continue
        family = suggested_generator(rule)
        trace_mode = recommended_trace_mode(rule)
        decision_surface = decision_surface_for_rule(rule)
        source_ref = f"{rule.get('source_file', '')}:{rule.get('line', '')}"
        canonical = build_canonical_state_class(
            surface="boss_ai",
            identity=identity,
            public_facts={
                "rule_id": rule.get("rule_id", ""),
                "family": family,
                "classification": rule.get("classification", ""),
                "expected_public_inputs": rule.get("expected_public_inputs", []),
            },
            surface_facts={
                "boss_ai": {
                    "decision_surface": decision_surface,
                    "proof_mode": trace_mode,
                    "source_file": rule.get("source_file", ""),
                    "line": rule.get("line"),
                    "source_label": rule.get("source_label", ""),
                    "parent_label": rule.get("parent_label"),
                }
            },
            backend="static_plus_trace_artifacts",
            proof_status="missing_proof_artifact",
            raw_state_provenance={
                "kind": "rule_map_dynamic_target",
                "rule_id": rule.get("rule_id", ""),
            },
            missing_evidence=["rom_backed_proof_artifact"],
            blocking_gaps=["boss_ai_dynamic_target_lacks_proof_artifact"],
            known_limits=[
                "Rule-target class ids are stable schema fingerprints, not proof completion.",
            ],
            source_refs=[source_ref],
        )
        rows.append(
            {
                "class_id": canonical["class_id"],
                "class_fingerprint": canonical["class_fingerprint"],
                "canonical_state_class_valid": canonical["valid"],
                "canonical_state_class_errors": canonical["validation_errors"],
                "rule_id": rule.get("rule_id", ""),
                "family": family,
                "decision_surface": decision_surface,
                "trainer_class": "",
                "trainer_class_id": None,
                "trainer_id": None,
                "tier": None,
                "public_info_scope": "public_only",
                "state_hash": "",
                "generator_version": "tools.boss_ai_debugger.generators",
                "reachable_proof_status": canonical["proof_status"],
                "proof_mode": trace_mode,
                "materializer_command": materializer_command_for_rule(rule),
                "source_file": rule.get("source_file", ""),
                "line": rule.get("line"),
                "source_label": rule.get("source_label", ""),
                "parent_label": rule.get("parent_label"),
                "expected_public_inputs": rule.get("expected_public_inputs", []),
                "requires_public_read_provenance": bool(
                    rule.get("requires_public_read_provenance", False)
                ),
            }
        )
    return rows


def build_exhaustive_class_witness_inventory(
    class_rows: list[dict[str, Any]],
    *,
    witness_evidence: dict[tuple[str, str], list[dict[str, Any]]] | None = None,
    first_missing_limit: int = 20,
    first_satisfied_limit: int = 20,
) -> dict[str, Any]:
    witness_evidence = witness_evidence or {}
    missing_roles: list[dict[str, Any]] = []
    satisfied_roles: list[dict[str, Any]] = []
    status_counts: dict[str, int] = {
        "missing_evidence": 0,
        "not_applicable": 0,
        "satisfied": 0,
    }
    for row in class_rows:
        for role in EXHAUSTIVE_WITNESS_ROLES:
            if role == "public_read_provenance" and not row.get(
                "requires_public_read_provenance", False
            ):
                status_counts["not_applicable"] += 1
                continue
            evidence = witness_evidence.get((str(row.get("rule_id", "")), role), [])
            if evidence:
                status_counts["satisfied"] += 1
                if len(satisfied_roles) < first_satisfied_limit:
                    satisfied_roles.append(
                        {
                            "rule_id": row.get("rule_id", ""),
                            "seed_class_id": row.get("class_id", ""),
                            "witness_role": role,
                            "status": "satisfied",
                            "family": row.get("family", ""),
                            "decision_surface": row.get("decision_surface", ""),
                            "proof_mode": row.get("proof_mode", ""),
                            "source_file": row.get("source_file", ""),
                            "line": row.get("line"),
                            "source_label": row.get("source_label", ""),
                            "parent_label": row.get("parent_label"),
                            "evidence": evidence[:3],
                        }
                    )
                continue
            status_counts["missing_evidence"] += 1
            if len(missing_roles) >= first_missing_limit:
                continue
            missing_roles.append(
                {
                    "rule_id": row.get("rule_id", ""),
                    "seed_class_id": row.get("class_id", ""),
                    "witness_role": role,
                    "status": "missing_evidence",
                    "family": row.get("family", ""),
                    "decision_surface": row.get("decision_surface", ""),
                    "proof_mode": row.get("proof_mode", ""),
                    "source_file": row.get("source_file", ""),
                    "line": row.get("line"),
                    "source_label": row.get("source_label", ""),
                    "parent_label": row.get("parent_label"),
                    "materializer_command": row.get("materializer_command", ""),
                }
            )
    missing_count = status_counts["missing_evidence"]
    return {
        "schema_version": 1,
        "basis": "canonical_class_rows",
        "ready": missing_count == 0,
        "role_names": list(EXHAUSTIVE_WITNESS_ROLES),
        "rule_count": len(class_rows),
        "missing_witness_role_count": missing_count,
        "satisfied_witness_role_count": status_counts["satisfied"],
        "status_counts": status_counts,
        "blocking_gaps": (
            ["boss_ai_exhaustive_class_witness_roles_missing"]
            if missing_count
            else []
        ),
        "first_satisfied_roles": satisfied_roles,
        "first_missing_roles": missing_roles,
    }


def build_exhaustive_class_witness_catalog(
    class_rows: list[dict[str, Any]],
    *,
    identity: dict[str, str],
    witness_evidence: dict[tuple[str, str], list[dict[str, Any]]] | None = None,
    first_invalid_limit: int = 10,
) -> dict[str, Any]:
    witness_evidence = witness_evidence or {}
    catalog_rows: list[dict[str, Any]] = []
    invalid_classes: list[dict[str, Any]] = []
    expected_count = 0
    proven_count = 0
    role_counts = {role: 0 for role in EXHAUSTIVE_WITNESS_ROLES}
    for row in class_rows:
        for role in applicable_witness_roles(row):
            expected_count += 1
            role_counts[role] += 1
            canonical = witness_canonical_state_class(row, role=role, identity=identity)
            observed_evidence = witness_evidence.get((str(row.get("rule_id", "")), role), [])
            if observed_evidence:
                proven_count += 1
            witness = {
                "witness_id": stable_json_hash(
                    {
                        "rule_id": row.get("rule_id", ""),
                        "seed_class_id": row.get("class_id", ""),
                        "witness_role": role,
                    }
                )[:24],
                "rule_id": row.get("rule_id", ""),
                "seed_class_id": row.get("class_id", ""),
                "witness_role": role,
                "status": "rom_proven" if observed_evidence else "cataloged_missing_rom_proof",
                "witness_class_id": canonical.get("class_id", ""),
                "witness_class_fingerprint": canonical.get("class_fingerprint", ""),
                "canonical_state_class_valid": canonical.get("valid") is True,
                "canonical_state_class_errors": list(canonical.get("validation_errors", [])),
                "canonical_state_class": canonical,
                "proof_status": canonical.get("proof_status", ""),
                "missing_evidence": list(canonical.get("missing_evidence", [])),
                "blocking_gaps": list(canonical.get("blocking_gaps", [])),
                "evidence": observed_evidence[:3],
                "observed_evidence_count": len(observed_evidence),
                "family": row.get("family", ""),
                "decision_surface": row.get("decision_surface", ""),
                "proof_mode": row.get("proof_mode", ""),
                "source_file": row.get("source_file", ""),
                "line": row.get("line"),
                "source_label": row.get("source_label", ""),
                "parent_label": row.get("parent_label"),
                "materializer_command": row.get("materializer_command", ""),
                "expected_public_inputs": row.get("expected_public_inputs", []),
                "requires_public_read_provenance": bool(row.get("requires_public_read_provenance", False)),
            }
            catalog_rows.append(witness)
            if not witness["canonical_state_class_valid"]:
                invalid_classes.append(
                    {
                        "rule_id": witness["rule_id"],
                        "witness_role": role,
                        "errors": witness["canonical_state_class_errors"],
                    }
                )
    class_ids = [
        str(item.get("witness_class_id", ""))
        for item in catalog_rows
        if item.get("witness_class_id")
    ]
    duplicate_count = len(class_ids) - len(set(class_ids))
    invalid_count = len(invalid_classes)
    missing_count = expected_count - len(catalog_rows)
    ready = expected_count > 0 and missing_count == 0 and invalid_count == 0 and duplicate_count == 0
    missing_proof_count = expected_count - proven_count
    return {
        "schema_version": 1,
        "kind": "boss_ai_exhaustive_class_witness_catalog",
        "ready": ready,
        "catalog_complete": ready,
        "proof_complete": missing_proof_count == 0 and ready,
        "proof_status": "catalog_only",
        "closed_evidence_id": EXHAUSTIVE_WITNESS_CATALOG_EVIDENCE_ID,
        "closed_evidence_ids": [EXHAUSTIVE_WITNESS_CATALOG_EVIDENCE_ID] if ready else [],
        "basis": "canonical_class_rows",
        "role_names": list(EXHAUSTIVE_WITNESS_ROLES),
        "rule_count": len(class_rows),
        "required_witness_role_count": expected_count,
        "required_witness_class_count": expected_count,
        "not_applicable_role_count": len(class_rows) * len(EXHAUSTIVE_WITNESS_ROLES) - expected_count,
        "cataloged_witness_class_count": len(catalog_rows),
        "generated_witness_class_count": len(catalog_rows),
        "rom_proven_witness_role_count": proven_count,
        "missing_rom_proof_role_count": missing_proof_count,
        "missing_witness_class_count": missing_count,
        "invalid_witness_class_count": invalid_count,
        "duplicate_class_id_count": duplicate_count,
        "role_counts": role_counts,
        "status_counts": {
            "cataloged_missing_rom_proof": missing_proof_count,
            "rom_proven": proven_count,
            "not_applicable": len(class_rows) * len(EXHAUSTIVE_WITNESS_ROLES) - expected_count,
        },
        "blocking_gaps": ["boss_ai_exhaustive_class_witness_roles_missing"] if missing_proof_count else [],
        "first_invalid_witness_classes": invalid_classes[:first_invalid_limit],
        "catalog_rows": catalog_rows,
        "does_not_close": [
            "boss_ai_exhaustive_class_witness_roles_missing",
            "boss_ai_universe_not_complete",
            "exhaustive_class_proofs",
        ],
        "known_limits": [
            "Generated witness classes are proof targets for the exhaustive Boss AI vertical.",
            "They do not satisfy negative, boundary, counterfactual, or ROM-backed witness roles without observed evidence artifacts.",
        ],
    }


def applicable_witness_roles(row: dict[str, Any]) -> list[str]:
    return [
        role
        for role in EXHAUSTIVE_WITNESS_ROLES
        if role != "public_read_provenance" or row.get("requires_public_read_provenance", False)
    ]


def witness_canonical_state_class(
    row: dict[str, Any],
    *,
    role: str,
    identity: dict[str, str],
) -> dict[str, Any]:
    source_ref = f"{row.get('source_file', '')}:{row.get('line', '')}"
    return build_canonical_state_class(
        surface="boss_ai",
        identity=identity,
        public_facts={
            "rule_id": row.get("rule_id", ""),
            "seed_class_id": row.get("class_id", ""),
            "witness_role": role,
            "family": row.get("family", ""),
            "decision_surface": row.get("decision_surface", ""),
            "expected_public_inputs": row.get("expected_public_inputs", []),
        },
        surface_facts={
            "boss_ai": {
                "decision_surface": row.get("decision_surface", ""),
                "proof_mode": row.get("proof_mode", ""),
                "witness_role": role,
                "source_file": row.get("source_file", ""),
                "line": row.get("line"),
                "source_label": row.get("source_label", ""),
                "parent_label": row.get("parent_label"),
            }
        },
        backend="static_plus_trace_artifacts",
        proof_status="missing_proof_artifact",
        raw_state_provenance={
            "kind": "boss_ai_exhaustive_witness_class",
            "rule_id": row.get("rule_id", ""),
            "seed_class_id": row.get("class_id", ""),
            "witness_role": role,
        },
        missing_evidence=["rom_backed_witness_proof", f"rom_backed_{role}_witness_missing"],
        blocking_gaps=["boss_ai_exhaustive_class_witness_roles_missing"],
        known_limits=[
            "This canonical class is a generated proof target, not an observed ROM witness.",
        ],
        source_refs=[source_ref],
    )


def build_witness_evidence_from_contribution_summary(
    contribution_summary: dict[str, Any],
    *,
    root: Path = ROOT,
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for artifact in contribution_leaf_artifacts(contribution_summary):
        artifact_path = str(artifact.get("artifact", ""))
        for rule_id in artifact.get("executed_rule_ids", []):
            add_witness_evidence(
                evidence,
                rule_id=str(rule_id),
                role="positive",
                item={
                    "artifact": artifact_path,
                    "evidence_kind": "rom_rule_execution",
                    "status": "rom_execution_observed",
                },
            )
        if artifact_path:
            add_switch_dispatch_observation_boundary_witness_evidence(
                evidence,
                artifact_path=artifact_path,
                root=root,
            )
            add_platform_rule_entry_boundary_witness_evidence(
                evidence,
                artifact_path=artifact_path,
                root=root,
            )
            add_haki_exception_rule_entry_boundary_witness_evidence(
                evidence,
                artifact_path=artifact_path,
                root=root,
            )
            add_public_read_witness_evidence(
                evidence,
                artifact_path=artifact_path,
                root=root,
            )
            add_adaptive_lead_parent_witness_evidence(
                evidence,
                artifact_path=artifact_path,
                root=root,
            )
            add_score_margin_boundary_witness_evidence(
                evidence,
                artifact_path=artifact_path,
                root=root,
            )
            add_score_no_delta_negative_witness_evidence(
                evidence,
                artifact_path=artifact_path,
                root=root,
            )
    return evidence


def contribution_leaf_artifacts(summary: dict[str, Any]) -> list[dict[str, Any]]:
    leaves: list[dict[str, Any]] = []
    for artifact in dict_items(summary.get("artifacts")):
        leaves.extend(contribution_leaf_artifacts_from_item(artifact))
    return leaves


def contribution_leaf_artifacts_from_item(item: dict[str, Any]) -> list[dict[str, Any]]:
    nested = dict_items(item.get("artifacts"))
    if not nested:
        return [item]
    leaves: list[dict[str, Any]] = []
    if item.get("artifact"):
        leaves.append(item)
    for child in nested:
        leaves.extend(contribution_leaf_artifacts_from_item(child))
    return leaves


def add_witness_evidence_from_score_materialization_artifacts(
    evidence: dict[tuple[str, str], list[dict[str, Any]]],
    materialization_paths: Iterable[Path],
    *,
    root: Path = ROOT,
) -> None:
    for materialization_path in materialization_paths:
        add_witness_evidence_from_score_materialization(
            evidence,
            artifact_path=repo_rel(
                root,
                materialization_path
                if materialization_path.is_absolute()
                else root / materialization_path,
            ),
            root=root,
        )


def contribution_reports_from_score_materializations(
    materialization_paths: Iterable[Path],
    *,
    root: Path = ROOT,
) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for materialization_path in materialization_paths:
        path = (
            materialization_path
            if materialization_path.is_absolute()
            else root / materialization_path
        )
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(report, dict) or report.get("kind") != "rom_score_materialization":
            continue
        for trace in dict_items(report.get("traces")):
            if trace.get("source") != "trace_rom_pyboy_hooks":
                continue
            reports.append(trace)
    return reports


def add_witness_evidence_from_score_materialization(
    evidence: dict[tuple[str, str], list[dict[str, Any]]],
    *,
    artifact_path: str,
    root: Path = ROOT,
) -> None:
    path = Path(artifact_path)
    if not path.is_absolute():
        path = root / path
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    if not isinstance(report, dict) or report.get("kind") != "rom_score_materialization":
        return
    for trace in dict_items(report.get("traces")):
        if trace.get("source") != "trace_rom_pyboy_hooks":
            continue
        trace_artifact = score_materialization_trace_artifact(artifact_path, trace)
        for rule_id in trace.get("executed_rule_ids", []):
            add_witness_evidence(
                evidence,
                rule_id=str(rule_id),
                role="positive",
                item={
                    "artifact": trace_artifact,
                    "evidence_kind": "rom_score_materialization_nested_rule_execution",
                    "status": "rom_execution_observed",
                },
            )
        add_public_read_witness_evidence(
            evidence,
            artifact_path=trace_artifact,
            root=root,
            report=trace,
        )
        add_platform_rule_entry_boundary_witness_evidence(
            evidence,
            artifact_path=trace_artifact,
            root=root,
            report=trace,
        )
        add_haki_exception_rule_entry_boundary_witness_evidence(
            evidence,
            artifact_path=trace_artifact,
            root=root,
            report=trace,
        )
        add_switch_dispatch_observation_boundary_witness_evidence(
            evidence,
            artifact_path=trace_artifact,
            root=root,
            report=trace,
        )
        add_adaptive_lead_parent_witness_evidence(
            evidence,
            artifact_path=trace_artifact,
            root=root,
            report=trace,
        )
        add_score_margin_boundary_witness_evidence(
            evidence,
            artifact_path=trace_artifact,
            root=root,
            report=trace,
        )
        add_score_no_delta_negative_witness_evidence(
            evidence,
            artifact_path=trace_artifact,
            root=root,
            report=trace,
        )


def add_witness_evidence_from_counterfactual_materialization_artifacts(
    evidence: dict[tuple[str, str], list[dict[str, Any]]],
    materialization_paths: Iterable[Path],
    *,
    rule_surfaces: dict[str, str],
    identity: dict[str, str],
    root: Path = ROOT,
) -> None:
    for materialization_path in materialization_paths:
        path = (
            materialization_path
            if materialization_path.is_absolute()
            else root / materialization_path
        )
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        artifact = repo_rel(root, path)
        add_witness_evidence_from_counterfactual_materialization(
            evidence,
            report=report,
            artifact_path=artifact,
            rule_surfaces=rule_surfaces,
            identity=identity,
        )


def add_witness_evidence_from_counterfactual_materialization(
    evidence: dict[tuple[str, str], list[dict[str, Any]]],
    *,
    report: dict[str, Any],
    artifact_path: str,
    rule_surfaces: dict[str, str],
    identity: dict[str, str],
) -> None:
    if not counterfactual_materialization_report_is_usable(report, identity=identity):
        return
    for witness in dict_items(report.get("witnesses")):
        credited = counterfactual_witness_evidence_item(
            witness,
            artifact_path=artifact_path,
            rule_surfaces=rule_surfaces,
        )
        if credited is None:
            continue
        add_witness_evidence(
            evidence,
            rule_id=credited["rule_id"],
            role="counterfactual_flip",
            item=credited["item"],
        )


def counterfactual_materialization_report_is_usable(
    report: dict[str, Any],
    *,
    identity: dict[str, str],
) -> bool:
    if not isinstance(report, dict):
        return False
    if report.get("kind") != COUNTERFACTUAL_MATERIALIZATION_KIND:
        return False
    if report.get("proof_scope") != COUNTERFACTUAL_MATERIALIZATION_PROOF_SCOPE:
        return False
    if int(report.get("schema_version", 0) or 0) != SCHEMA_VERSION:
        return False
    if not str(report.get("source", "") or ""):
        return False
    if not str(report.get("generator", "") or ""):
        return False
    if int(report.get("checked_count", 0) or 0) <= 0:
        return False
    for key in ("skipped_count", "error_count", "policy_disagreement_count"):
        if int(report.get(key, 0) or 0) != 0:
            return False
    witnesses = report.get("witnesses")
    if not isinstance(witnesses, list) or not witnesses:
        return False
    basis = report.get("basis")
    if not isinstance(basis, dict):
        return False
    for key, expected in identity.items():
        if str(basis.get(key, "") or "") != str(expected):
            return False
    return True


def counterfactual_witness_evidence_item(
    witness: dict[str, Any],
    *,
    artifact_path: str,
    rule_surfaces: dict[str, str],
) -> dict[str, Any] | None:
    if not isinstance(witness, dict):
        return None
    if witness.get("status") != "pass":
        return None
    if witness.get("witness_role") != "counterfactual_flip":
        return None
    rule_id = str(witness.get("rule_id", "") or "")
    if not rule_id or rule_id not in rule_surfaces:
        return None
    decision_surface = str(witness.get("decision_surface", "") or "")
    if decision_surface != rule_surfaces[rule_id]:
        return None
    anchor = witness.get("source_anchor")
    if not isinstance(anchor, dict):
        return None
    if anchor.get("anchor_status") != "mapped":
        return None
    if str(anchor.get("rule_id", "") or "") != rule_id:
        return None
    mutation_key = counterfactual_mutation_key(witness.get("mutation"))
    if mutation_key is None:
        return None
    if not counterfactual_mutation_allowed_for_rule(
        rule_id,
        decision_surface=decision_surface,
        mutation_key=mutation_key,
    ):
        return None
    baseline_trace = witness.get("baseline_trace")
    counterfactual_trace = witness.get("counterfactual_trace")
    if not trace_is_rom_hook_trace(baseline_trace):
        return None
    if not trace_is_rom_hook_trace(counterfactual_trace):
        return None
    if rule_id not in set(str(item) for item in baseline_trace.get("executed_rule_ids", [])):
        return None
    baseline_observable = normalized_witness_observable(
        witness.get("baseline_observable"),
        trace=baseline_trace,
    )
    counterfactual_observable = normalized_witness_observable(
        witness.get("counterfactual_observable"),
        trace=counterfactual_trace,
    )
    if baseline_observable is None or counterfactual_observable is None:
        return None
    branch_item = counterfactual_branch_outcome_evidence_item(
        rule_id,
        decision_surface=decision_surface,
        artifact_path=artifact_path,
        anchor=anchor,
        mutation_key=mutation_key,
        baseline_trace=baseline_trace,
        counterfactual_trace=counterfactual_trace,
        baseline_observable=baseline_observable,
        counterfactual_observable=counterfactual_observable,
    )
    if branch_item is not None:
        return {"rule_id": rule_id, "item": branch_item}
    branch_application_item = counterfactual_branch_application_evidence_item(
        rule_id,
        decision_surface=decision_surface,
        artifact_path=artifact_path,
        anchor=anchor,
        mutation_key=mutation_key,
        baseline_trace=baseline_trace,
        counterfactual_trace=counterfactual_trace,
        baseline_observable=baseline_observable,
        counterfactual_observable=counterfactual_observable,
    )
    if branch_application_item is not None:
        return {"rule_id": rule_id, "item": branch_application_item}
    if not counterfactual_observables_flip(baseline_observable, counterfactual_observable):
        return None
    if counterfactual_has_predicate_branch_outcome_metadata(
        baseline_trace,
        rule_id,
    ) or counterfactual_has_predicate_branch_outcome_metadata(
        counterfactual_trace,
        rule_id,
    ):
        return None
    if not counterfactual_observable_supports_surface(
        rule_id,
        decision_surface,
        baseline_observable=baseline_observable,
        counterfactual_observable=counterfactual_observable,
    ):
        return None
    return {
        "rule_id": rule_id,
        "item": {
            "artifact": artifact_path,
            "evidence_kind": "rom_paired_counterfactual_decision_flip",
            "status": "paired_counterfactual_flip_observed",
            "source_label": str(anchor.get("source_label", "") or ""),
            "parent_label": str(anchor.get("parent_label", "") or ""),
            "baseline_trace_id": str(
                baseline_trace.get("trace_id")
                or baseline_trace.get("scenario_id")
                or ""
            ),
            "counterfactual_trace_id": str(
                counterfactual_trace.get("trace_id")
                or counterfactual_trace.get("scenario_id")
                or ""
            ),
            "mutation_key": mutation_key,
            "baseline_observable": baseline_observable,
            "counterfactual_observable": counterfactual_observable,
        },
    }


def counterfactual_branch_outcome_evidence_item(
    rule_id: str,
    *,
    decision_surface: str,
    artifact_path: str,
    anchor: dict[str, Any],
    mutation_key: str,
    baseline_trace: dict[str, Any],
    counterfactual_trace: dict[str, Any],
    baseline_observable: dict[str, Any],
    counterfactual_observable: dict[str, Any],
) -> dict[str, Any] | None:
    if decision_surface not in {"boss_ai_rule", "move_score", "switch_dispatch"}:
        return None
    baseline_outcomes = predicate_branch_outcome_set_for_rule(baseline_trace, rule_id)
    counterfactual_outcomes = predicate_branch_outcome_set_for_rule(
        counterfactual_trace,
        rule_id,
    )
    if not baseline_outcomes and not counterfactual_outcomes:
        return None
    if baseline_outcomes == counterfactual_outcomes:
        return None
    return {
        "artifact": artifact_path,
        "evidence_kind": "rom_paired_counterfactual_predicate_branch_flip",
        "status": "paired_counterfactual_branch_flip_observed",
        "source_label": str(anchor.get("source_label", "") or ""),
        "parent_label": str(anchor.get("parent_label", "") or ""),
        "baseline_trace_id": str(
            baseline_trace.get("trace_id")
            or baseline_trace.get("scenario_id")
            or ""
        ),
        "counterfactual_trace_id": str(
            counterfactual_trace.get("trace_id")
            or counterfactual_trace.get("scenario_id")
            or ""
        ),
        "mutation_key": mutation_key,
        "baseline_observable": baseline_observable,
        "counterfactual_observable": counterfactual_observable,
        "baseline_branch_outcomes": format_predicate_branch_outcome_set(
            baseline_outcomes
        ),
        "counterfactual_branch_outcomes": format_predicate_branch_outcome_set(
            counterfactual_outcomes
        ),
    }


def counterfactual_branch_application_evidence_item(
    rule_id: str,
    *,
    decision_surface: str,
    artifact_path: str,
    anchor: dict[str, Any],
    mutation_key: str,
    baseline_trace: dict[str, Any],
    counterfactual_trace: dict[str, Any],
    baseline_observable: dict[str, Any],
    counterfactual_observable: dict[str, Any],
) -> dict[str, Any] | None:
    if decision_surface not in {"boss_ai_rule", "move_score", "switch_dispatch"}:
        return None
    baseline_applications = predicate_branch_application_set_for_rule(
        baseline_trace,
        rule_id,
    )
    counterfactual_applications = predicate_branch_application_set_for_rule(
        counterfactual_trace,
        rule_id,
    )
    if not baseline_applications and not counterfactual_applications:
        return None
    if baseline_applications == counterfactual_applications:
        return None
    return {
        "artifact": artifact_path,
        "evidence_kind": "rom_paired_counterfactual_predicate_application_flip",
        "status": "paired_counterfactual_branch_application_flip_observed",
        "source_label": str(anchor.get("source_label", "") or ""),
        "parent_label": str(anchor.get("parent_label", "") or ""),
        "baseline_trace_id": str(
            baseline_trace.get("trace_id")
            or baseline_trace.get("scenario_id")
            or ""
        ),
        "counterfactual_trace_id": str(
            counterfactual_trace.get("trace_id")
            or counterfactual_trace.get("scenario_id")
            or ""
        ),
        "mutation_key": mutation_key,
        "baseline_observable": baseline_observable,
        "counterfactual_observable": counterfactual_observable,
        "baseline_branch_applications": format_predicate_branch_application_set(
            baseline_applications
        ),
        "counterfactual_branch_applications": format_predicate_branch_application_set(
            counterfactual_applications
        ),
    }


def counterfactual_has_predicate_branch_outcome_metadata(
    trace: dict[str, Any],
    rule_id: str,
) -> bool:
    return any(
        outcome not in NON_DISCRIMINATING_COUNTERFACTUAL_BRANCH_OUTCOMES
        for _predicate_id, outcome in predicate_branch_outcome_set_for_rule(
            trace,
            rule_id,
        )
    )


def predicate_branch_outcome_set_for_rule(
    trace: dict[str, Any],
    rule_id: str,
) -> set[tuple[str, str]]:
    outcomes: set[tuple[str, str]] = set()
    for entry in dict_items(trace.get("predicate_branch_entries")):
        source = entry.get("source") if isinstance(entry, dict) else None
        predicate = entry.get("predicate") if isinstance(entry, dict) else None
        if not isinstance(source, dict) or not isinstance(predicate, dict):
            continue
        if str(source.get("rule_id", "") or "") != rule_id:
            continue
        predicate_id = str(predicate.get("predicate_id", "") or "")
        outcome = str(predicate.get("outcome", "") or "")
        if predicate_id and outcome:
            outcomes.add((predicate_id, outcome))
    return outcomes


def predicate_branch_application_set_for_rule(
    trace: dict[str, Any],
    rule_id: str,
) -> set[tuple[str, str, str, str]]:
    applications: set[tuple[str, str, str, str]] = set()
    for entry in dict_items(trace.get("predicate_branch_entries")):
        source = entry.get("source") if isinstance(entry, dict) else None
        predicate = entry.get("predicate") if isinstance(entry, dict) else None
        if not isinstance(source, dict) or not isinstance(predicate, dict):
            continue
        if str(source.get("rule_id", "") or "") != rule_id:
            continue
        predicate_id = str(predicate.get("predicate_id", "") or "")
        outcome = str(predicate.get("outcome", "") or "")
        candidate_key = predicate_branch_candidate_key(entry)
        if predicate_id and outcome:
            applications.add((candidate_key, predicate_id, outcome, rule_id))
    return applications


def predicate_branch_candidate_key(entry: dict[str, Any]) -> str:
    candidate = entry.get("candidate")
    if not isinstance(candidate, dict):
        return ""
    kind = str(candidate.get("kind", "") or "")
    move_id = str(candidate.get("move_id", "") or "")
    slot_index = str(candidate.get("slot_index", "") or "")
    switch_index = str(candidate.get("switch_index", "") or "")
    switch_param = str(candidate.get("switch_param", "") or "")
    return "|".join((kind, move_id, slot_index, switch_index, switch_param))


def format_predicate_branch_application_set(
    applications: set[tuple[str, str, str, str]],
) -> list[dict[str, str]]:
    return [
        {
            "candidate_key": candidate_key,
            "predicate_id": predicate_id,
            "outcome": outcome,
        }
        for candidate_key, predicate_id, outcome, _rule_id in sorted(applications)
    ]


def format_predicate_branch_outcome_set(
    outcomes: set[tuple[str, str]],
) -> list[dict[str, str]]:
    return [
        {"predicate_id": predicate_id, "outcome": outcome}
        for predicate_id, outcome in sorted(outcomes)
    ]


def counterfactual_observable_supports_surface(
    rule_id: str,
    decision_surface: str,
    *,
    baseline_observable: dict[str, Any],
    counterfactual_observable: dict[str, Any],
) -> bool:
    baseline_kind = str(baseline_observable.get("kind", "") or "")
    counterfactual_kind = str(counterfactual_observable.get("kind", "") or "")
    if decision_surface in {"boss_ai_rule", "move_score"}:
        if (
            decision_surface == "boss_ai_rule"
            and rule_id in SWITCH_OBSERVABLE_SHARED_RULE_IDS
            and baseline_kind == "switch_dispatch"
            and counterfactual_kind == "switch_dispatch"
        ):
            return True
        return baseline_kind == "move_choice" and counterfactual_kind == "move_choice"
    if decision_surface == "switch_dispatch":
        if (
            rule_id in MOVE_OBSERVABLE_SWITCH_RULE_IDS
            and baseline_kind == "move_choice"
            and counterfactual_kind == "move_choice"
        ):
            return True
        return baseline_kind == "switch_dispatch" and counterfactual_kind == "switch_dispatch"
    return False


def counterfactual_mutation_key(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    if value.get("allowlist") != COUNTERFACTUAL_MUTATION_ALLOWLIST:
        return None
    changed_keys = value.get("changed_keys")
    if not isinstance(changed_keys, list) or len(changed_keys) != 1:
        return None
    key = str(changed_keys[0])
    if key not in ALLOWED_COUNTERFACTUAL_MUTATION_KEYS:
        return None
    return key


def counterfactual_mutation_allowed_for_rule(
    rule_id: str,
    *,
    decision_surface: str,
    mutation_key: str,
) -> bool:
    final_switch_keys = {"wBossAISwitchConfidence", "wEnemySwitchMonParam"}
    if mutation_key in final_switch_keys:
        return decision_surface == "switch_dispatch" and rule_id in {
            "switch.try_switch",
            "switch.get_switch_threshold",
            "switch.compute_switch_confidence",
        }
    return True


def trace_is_rom_hook_trace(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return value.get("source") == "trace_rom_pyboy_hooks"


def normalized_witness_observable(
    value: Any,
    *,
    trace: dict[str, Any],
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    kind = str(value.get("kind", "") or "")
    if kind == "move_choice":
        chosen = trace.get("chosen")
        if not isinstance(chosen, dict):
            return None
        move_id = safe_int(value.get("move_id"), -1)
        slot_index = safe_int(value.get("slot_index"), -1)
        if move_id <= 0 or slot_index < 0:
            return None
        if safe_int(chosen.get("move_id"), -1) != move_id:
            return None
        if safe_int(chosen.get("slot_index"), -1) != slot_index:
            return None
        return {
            "kind": "move_choice",
            "move_id": move_id,
            "slot_index": slot_index,
        }
    if kind == "switch_dispatch":
        observation = trace.get("switch_observation")
        if not isinstance(observation, dict):
            return None
        status = str(value.get("status", "") or "")
        confidence = safe_int(value.get("switch_confidence"), -1)
        param = safe_int(value.get("switch_param"), -1)
        index = safe_int(value.get("switch_index"), -1)
        if not status or confidence < 0 or param < 0 or index < 0:
            return None
        if str(observation.get("status", "") or "") != status:
            return None
        if safe_int(observation.get("switch_confidence"), -1) != confidence:
            return None
        if safe_int(observation.get("switch_param"), -1) != param:
            return None
        if safe_int(observation.get("switch_index"), -1) != index:
            return None
        return {
            "kind": "switch_dispatch",
            "status": status,
            "switch_confidence": confidence,
            "switch_param": param,
            "switch_index": index,
        }
    return None


def counterfactual_observables_flip(
    baseline: dict[str, Any],
    counterfactual: dict[str, Any],
) -> bool:
    if baseline.get("kind") == "move_choice" and counterfactual.get("kind") == "move_choice":
        return (
            baseline.get("move_id") != counterfactual.get("move_id")
            or baseline.get("slot_index") != counterfactual.get("slot_index")
        )
    if baseline.get("kind") == "switch_dispatch" and counterfactual.get("kind") == "switch_dispatch":
        return (
            baseline.get("switch_index") != counterfactual.get("switch_index")
            or baseline.get("switch_param") != counterfactual.get("switch_param")
            or baseline.get("status") != counterfactual.get("status")
        )
    return False


def score_materialization_trace_artifact(
    artifact_path: str,
    trace: dict[str, Any],
) -> str:
    trace_id = str(trace.get("trace_id") or trace.get("scenario_id") or "")
    return f"{artifact_path}#{trace_id}" if trace_id else artifact_path


def add_platform_rule_entry_boundary_witness_evidence(
    evidence: dict[tuple[str, str], list[dict[str, Any]]],
    *,
    artifact_path: str,
    root: Path,
    report: dict[str, Any] | None = None,
) -> None:
    if report is None:
        path = Path(artifact_path)
        if not path.is_absolute():
            path = root / path
        try:
            report = load_rom_contribution_trace(path)
        except Exception:
            return
    for entry in dict_items(report.get("rule_entries")):
        if entry.get("event_type") != "rule_enter":
            continue
        source = entry.get("source") if isinstance(entry, dict) else None
        if not isinstance(source, dict):
            continue
        if str(source.get("classification", "")) != "platform_boundary":
            continue
        rule_id = str(source.get("rule_id", ""))
        full_symbol = str(source.get("full_symbol", ""))
        hook_bank = str(source.get("hook_bank", ""))
        hook_address = str(source.get("hook_address", ""))
        if not rule_id or not full_symbol or not hook_bank or not hook_address:
            continue
        add_witness_evidence(
            evidence,
            rule_id=rule_id,
            role="boundary",
            item={
                "artifact": artifact_path,
                "evidence_kind": "rom_platform_rule_entry_boundary",
                "status": "platform_boundary_entry_observed",
                "rule_entry_index": entry.get("index"),
                "full_symbol": full_symbol,
                "hook_bank": hook_bank,
                "hook_address": hook_address,
                "source_label": str(source.get("source_label", "")),
            },
        )


def add_haki_exception_rule_entry_boundary_witness_evidence(
    evidence: dict[tuple[str, str], list[dict[str, Any]]],
    *,
    artifact_path: str,
    root: Path,
    report: dict[str, Any] | None = None,
) -> None:
    if report is None:
        path = Path(artifact_path)
        if not path.is_absolute():
            path = root / path
        try:
            report = load_rom_contribution_trace(path)
        except Exception:
            return
    if report.get("source") != "trace_rom_pyboy_hooks":
        return
    if not str(report.get("save_state", "")):
        return
    executed_rule_ids = {
        str(rule_id)
        for rule_id in report.get("executed_rule_ids", [])
        if str(rule_id)
    }
    if not executed_rule_ids:
        return
    for entry in dict_items(report.get("rule_entries")):
        if entry.get("event_type") != "rule_enter":
            continue
        source = entry.get("source") if isinstance(entry, dict) else None
        if not isinstance(source, dict):
            continue
        if str(source.get("classification", "")) != "haki_exception":
            continue
        rule_id = str(source.get("rule_id", ""))
        full_symbol = str(source.get("full_symbol", ""))
        hook_bank = str(source.get("hook_bank", ""))
        hook_address = str(source.get("hook_address", ""))
        if rule_id not in executed_rule_ids:
            continue
        if not rule_id.startswith("switch.") or "haki" not in rule_id:
            continue
        if "Haki" not in full_symbol:
            continue
        if not full_symbol or not hook_bank or not hook_address:
            continue
        add_witness_evidence(
            evidence,
            rule_id=rule_id,
            role="boundary",
            item={
                "artifact": artifact_path,
                "evidence_kind": "rom_haki_exception_rule_entry_boundary",
                "status": "haki_exception_boundary_entry_observed",
                "rule_entry_index": entry.get("index"),
                "full_symbol": full_symbol,
                "hook_bank": hook_bank,
                "hook_address": hook_address,
                "source_label": str(source.get("source_label", "")),
                "save_state": str(report.get("save_state", "")),
            },
        )


def add_switch_dispatch_observation_boundary_witness_evidence(
    evidence: dict[tuple[str, str], list[dict[str, Any]]],
    *,
    artifact_path: str,
    root: Path,
    report: dict[str, Any] | None = None,
) -> None:
    if report is None:
        path = Path(artifact_path)
        if not path.is_absolute():
            path = root / path
        try:
            report = load_rom_contribution_trace(path)
        except Exception:
            return
    if report.get("source") != "trace_rom_pyboy_hooks":
        return
    if report.get("decision_surface") != "switch_dispatch":
        return
    observation = report.get("switch_observation")
    if not switch_dispatch_observation_is_concrete(observation):
        return
    for entry in dict_items(report.get("rule_entries")):
        if entry.get("event_type") != "rule_enter":
            continue
        source = entry.get("source") if isinstance(entry, dict) else None
        if not isinstance(source, dict):
            continue
        rule_id = str(source.get("rule_id", ""))
        full_symbol = str(source.get("full_symbol", ""))
        hook_bank = str(source.get("hook_bank", ""))
        hook_address = str(source.get("hook_address", ""))
        if not rule_id.startswith("switch."):
            continue
        if not full_symbol or not hook_bank or not hook_address:
            continue
        add_witness_evidence(
            evidence,
            rule_id=rule_id,
            role="boundary",
            item={
                "artifact": artifact_path,
                "evidence_kind": "rom_switch_dispatch_observation_boundary",
                "status": "switch_dispatch_observed",
                "rule_entry_index": entry.get("index"),
                "full_symbol": full_symbol,
                "hook_bank": hook_bank,
                "hook_address": hook_address,
                "source_label": str(source.get("source_label", "")),
                "observation_status": str(observation.get("status", "")),
                "switch_confidence": safe_int(observation.get("switch_confidence"), 0),
                "switch_param": safe_int(observation.get("switch_param"), 0),
                "switch_index": safe_int(observation.get("switch_index"), 0),
                "chosen_move": safe_int(observation.get("chosen_move"), 0),
            },
        )


def switch_dispatch_observation_is_concrete(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    status = str(value.get("status", ""))
    if not status or status == "no_switch_observation":
        return False
    return any(
        key in value
        for key in (
            "switch_confidence",
            "switch_param",
            "switch_index",
            "chosen_move",
        )
    )


def add_witness_evidence_from_deity_packets(
    evidence: dict[tuple[str, str], list[dict[str, Any]]],
    packet_paths: Iterable[Path],
    *,
    root: Path = ROOT,
) -> None:
    for packet_path in packet_paths:
        path = packet_path if packet_path.is_absolute() else root / packet_path
        try:
            packet = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        artifact = repo_rel(root, path)
        switch_negative = deity_packet_switch_try_switch_no_proposal_negative(packet)
        if switch_negative is not None:
            add_witness_evidence(
                evidence,
                rule_id="switch.try_switch",
                role="negative",
                item={
                    "artifact": artifact,
                    "evidence_kind": "deity_switch_materialization_no_proposal_negative",
                    "status": "negative_no_switch_proposal_observed",
                    "source_label": switch_negative["source_label"],
                    "parent_label": switch_negative["parent_label"],
                    "scenario_id": switch_negative["scenario_id"],
                    "observation_status": switch_negative["observation_status"],
                    "switch_confidence": switch_negative["switch_confidence"],
                },
            )
        switch_boundary = deity_packet_switch_try_switch_roll_boundary(packet)
        if switch_boundary is not None:
            add_witness_evidence(
                evidence,
                rule_id="switch.try_switch",
                role="boundary",
                item={
                    "artifact": artifact,
                    "evidence_kind": "deity_switch_materialization_roll_boundary",
                    "status": "switch_roll_boundary_observed",
                    "source_label": switch_boundary["source_label"],
                    "parent_label": switch_boundary["parent_label"],
                    "scenario_id": switch_boundary["scenario_id"],
                    "observation_status": switch_boundary["observation_status"],
                    "switch_confidence": switch_boundary["switch_confidence"],
                    "switch_param": switch_boundary["switch_param"],
                    "switch_index": switch_boundary["switch_index"],
                    "switch_probability": switch_boundary["switch_probability"],
                    "switch_chance_threshold": switch_boundary["switch_chance_threshold"],
                },
            )
        pressure_boundary = deity_packet_enemy_under_pressure_score_boundary(packet)
        if pressure_boundary is not None:
            add_witness_evidence(
                evidence,
                rule_id="move.apply_move_model.enemy_under_pressure",
                role="boundary",
                item={
                    "artifact": artifact,
                    "evidence_kind": "deity_score_materialization_enemy_under_pressure_boundary",
                    "status": "score_boundary_observed",
                    "source_label": pressure_boundary["source_label"],
                    "parent_label": pressure_boundary["parent_label"],
                    "scenario_id": pressure_boundary["scenario_id"],
                    "candidate_move": pressure_boundary["candidate_move"],
                    "candidate_move_id": pressure_boundary["candidate_move_id"],
                    "slot_index": pressure_boundary["slot_index"],
                    "before": pressure_boundary["before"],
                    "after": pressure_boundary["after"],
                    "delta": pressure_boundary["delta"],
                    "operation": pressure_boundary["operation"],
                    "best_action_id": pressure_boundary["best_action_id"],
                    "second_action_id": pressure_boundary["second_action_id"],
                    "score_gap": pressure_boundary["score_gap"],
                },
            )
        spikes_negative = deity_packet_apply_spikes_layer_bias_non_spikes_negative(packet)
        if spikes_negative is not None:
            add_witness_evidence(
                evidence,
                rule_id="move.apply_move_model.apply_spikes_layer_bias",
                role="negative",
                item={
                    "artifact": artifact,
                    "evidence_kind": "deity_score_materialization_apply_spikes_layer_bias_non_spikes_negative",
                    "status": "negative_non_spikes_candidate_observed",
                    "source_label": spikes_negative["source_label"],
                    "parent_label": spikes_negative["parent_label"],
                    "scenario_id": spikes_negative["scenario_id"],
                    "candidate_action_id": spikes_negative["candidate_action_id"],
                    "candidate_move": spikes_negative["candidate_move"],
                    "candidate_move_id": spikes_negative["candidate_move_id"],
                    "slot_index": spikes_negative["slot_index"],
                    "initial_score": spikes_negative["initial_score"],
                    "pre_lookahead_score": spikes_negative["pre_lookahead_score"],
                    "final_score": spikes_negative["final_score"],
                    "only_contribution_rule_id": spikes_negative["only_contribution_rule_id"],
                    "lookahead_delta": spikes_negative["lookahead_delta"],
                    "best_action_id": spikes_negative["best_action_id"],
                    "second_action_id": spikes_negative["second_action_id"],
                    "score_gap": spikes_negative["score_gap"],
                    "input_id": spikes_negative["input_id"],
                    "outcome": spikes_negative["outcome"],
                    "snapshot_keys": spikes_negative["snapshot_keys"],
                },
            )
        if not deity_packet_has_decisive_counterfactual(packet):
            continue
        for anchor in dict_items(packet.get("source_anchors")):
            rule_id = str(anchor.get("rule_id", ""))
            if not rule_id:
                continue
            if str(anchor.get("anchor_status", "")) != "mapped":
                continue
            add_witness_evidence(
                evidence,
                rule_id=rule_id,
                role="counterfactual_flip",
                item={
                    "artifact": artifact,
                    "evidence_kind": "deity_explain_decision_counterfactual",
                    "status": "counterfactual_flip_observed",
                    "source_label": str(anchor.get("source_label", "")),
                    "parent_label": str(anchor.get("parent_label", "")),
                },
            )
        for public_anchor in deity_packet_public_info_source_anchors(packet):
            add_witness_evidence(
                evidence,
                rule_id=public_anchor["rule_id"],
                role="counterfactual_flip",
                item={
                    "artifact": artifact,
                    "evidence_kind": "deity_explain_decision_public_info_counterfactual",
                    "status": "counterfactual_flip_observed",
                    "input_kind": public_anchor["input_kind"],
                    "input_id": public_anchor["input_id"],
                    "outcome": public_anchor["outcome"],
                    "snapshot_keys": public_anchor["snapshot_keys"],
                    "source_label": public_anchor["source_label"],
                    "parent_label": public_anchor["parent_label"],
                },
            )


def deity_packet_has_decisive_counterfactual(packet: dict[str, Any]) -> bool:
    return deity_packet_has_present_ids(
        packet,
        ("observed_rom_decision", "counterfactual.decisive"),
    )


def deity_packet_has_present_ids(packet: dict[str, Any], required: Iterable[str]) -> bool:
    proof_status = packet.get("proof_status")
    if not isinstance(proof_status, dict):
        return False
    present_ids = proof_status.get("present_ids")
    if not isinstance(present_ids, list):
        return False
    present = {str(item) for item in present_ids}
    return all(item in present for item in required)


def deity_packet_switch_try_switch_no_proposal_negative(packet: dict[str, Any]) -> dict[str, Any] | None:
    if not deity_packet_has_present_ids(
        packet,
        ("observed_rom_decision", "switch_path", "switch_materialization"),
    ):
        return None
    anchor = None
    for item in dict_items(packet.get("source_anchors")):
        if str(item.get("rule_id", "")) != "switch.try_switch":
            continue
        if str(item.get("anchor_status", "")) != "mapped":
            continue
        anchor = item
        break
    if anchor is None:
        return None
    for rom_evidence in dict_items(packet.get("rom_evidence")):
        if rom_evidence.get("kind") != "rom_switch_materialization":
            continue
        if safe_int(rom_evidence.get("error_count"), -1) != 0:
            continue
        for verdict in dict_items(rom_evidence.get("verdicts")):
            rom = verdict.get("rom") if isinstance(verdict, dict) else None
            if not isinstance(rom, dict):
                continue
            if rom.get("source") != "trace_rom_pyboy_switch":
                continue
            if rom.get("switch_gate_evaluated") is not True:
                continue
            if rom.get("observation_status") != "switch_gate_evaluated_no_proposal":
                continue
            if rom.get("observed_decision") is not True:
                continue
            if rom.get("observed_switch_path") is not False:
                continue
            if rom.get("proposed_switch") is not False:
                continue
            if rom.get("actual_switch") is not False:
                continue
            switch_confidence = safe_int(rom.get("switch_confidence"), -1)
            if switch_confidence != 0:
                continue
            return {
                "source_label": str(anchor.get("source_label", "")),
                "parent_label": str(anchor.get("parent_label", "")),
                "scenario_id": str(verdict.get("scenario_id", "")),
                "observation_status": str(rom.get("observation_status", "")),
                "switch_confidence": switch_confidence,
            }
    return None


def deity_packet_switch_try_switch_roll_boundary(packet: dict[str, Any]) -> dict[str, Any] | None:
    if not deity_packet_has_present_ids(
        packet,
        ("observed_rom_decision", "switch_path", "switch_materialization"),
    ):
        return None
    anchor = None
    for item in dict_items(packet.get("source_anchors")):
        if str(item.get("rule_id", "")) != "switch.try_switch":
            continue
        if str(item.get("anchor_status", "")) != "mapped":
            continue
        if str(item.get("source_label", "")) != "BossAI_TrySwitch":
            continue
        anchor = item
        break
    if anchor is None:
        return None
    for rom_evidence in dict_items(packet.get("rom_evidence")):
        if rom_evidence.get("kind") != "rom_switch_materialization":
            continue
        if safe_int(rom_evidence.get("checked_count"), 0) <= 0:
            continue
        if safe_int(rom_evidence.get("error_count"), -1) != 0:
            continue
        if safe_int(rom_evidence.get("skipped_count"), -1) != 0:
            continue
        if safe_int(rom_evidence.get("policy_disagreement_count"), -1) != 0:
            continue
        for verdict in dict_items(rom_evidence.get("verdicts")):
            if verdict.get("scenario_id") != "generated_switch_sack_1_00006_preserve_wincon_over_comfort_damage":
                continue
            if verdict.get("status") != "pass":
                continue
            if verdict.get("family") != "switch_sack":
                continue
            if verdict.get("expected_switch") is not True:
                continue
            rom = verdict.get("rom") if isinstance(verdict, dict) else None
            if not isinstance(rom, dict):
                continue
            if rom.get("source") != "trace_rom_pyboy_switch":
                continue
            if rom.get("switch_gate_evaluated") is not True:
                continue
            if rom.get("observation_status") != "switch_proposal_observed":
                continue
            if rom.get("observed_decision") is not True:
                continue
            if rom.get("observed_switch_path") is not True:
                continue
            if rom.get("proposed_switch") is not True:
                continue
            if rom.get("actual_switch") is not False:
                continue
            if safe_int(rom.get("chosen_move"), -1) != 0:
                continue
            switch_confidence = safe_int(rom.get("switch_confidence"), -1)
            switch_param = safe_int(rom.get("switch_param"), -1)
            switch_index = safe_int(rom.get("switch_index"), -1)
            if switch_confidence != 99 or switch_param != 49 or switch_index != 0:
                continue
            switch_roll = verdict.get("switch_roll")
            if not isinstance(switch_roll, dict):
                continue
            if switch_roll.get("available") is not True:
                continue
            if switch_roll.get("proof_status") != "source_mirrored_final_switch_roll_from_observed_confidence":
                continue
            if safe_int(switch_roll.get("confidence"), -1) != switch_confidence:
                continue
            if switch_roll.get("probability_exact") is not True:
                continue
            switch_chance_threshold = safe_int(switch_roll.get("switch_chance_threshold"), -1)
            if switch_chance_threshold != 230:
                continue
            switch_probability = safe_float(switch_roll.get("switch_probability"), -1.0)
            if abs(switch_probability - (230 / 256)) > 1e-12:
                continue
            possible_probabilities = dict_items(switch_roll.get("possible_switch_probabilities"))
            if not possible_probabilities:
                continue
            if any(
                safe_int(item.get("switch_chance_threshold"), -1) != 230
                for item in possible_probabilities
            ):
                continue
            return {
                "source_label": str(anchor.get("source_label", "")),
                "parent_label": str(anchor.get("parent_label", "")),
                "scenario_id": str(verdict.get("scenario_id", "")),
                "observation_status": str(rom.get("observation_status", "")),
                "switch_confidence": switch_confidence,
                "switch_param": switch_param,
                "switch_index": switch_index,
                "switch_probability": switch_probability,
                "switch_chance_threshold": switch_chance_threshold,
            }
    return None


def deity_packet_enemy_under_pressure_score_boundary(packet: dict[str, Any]) -> dict[str, Any] | None:
    scenario_id = "generated_spikes_spin_1_00000"
    rule_id = "move.apply_move_model.enemy_under_pressure"
    if packet.get("scenario_id") != scenario_id:
        return None
    if packet.get("family") != "spikes_spin":
        return None
    if packet.get("deity_evidence_marker") != "BOSS_AI_DEITY_PROOF_COMPLETE":
        return None
    if packet.get("proof_blockers") != []:
        return None
    proof_status = packet.get("proof_status")
    if not isinstance(proof_status, dict):
        return None
    if proof_status.get("blockers") != [] or proof_status.get("missing_ids") != []:
        return None
    if not deity_packet_has_present_ids(
        packet,
        (
            "observed_rom_decision",
            "candidate_scores",
            "score_bytes",
            "selector_path",
            "rom_contribution_deltas",
            "score_rule.rom_delta_observed",
            "python_contribution.normalized",
            "rom_python_agreement.reported",
        ),
    ):
        return None

    anchor = None
    for item in dict_items(packet.get("source_anchors")):
        if str(item.get("rule_id", "")) != rule_id:
            continue
        if str(item.get("anchor_status", "")) != "mapped":
            continue
        if str(item.get("source_label", "")) != ".EnemyUnderPressure":
            continue
        anchor = item
        break
    if anchor is None:
        return None

    observed = packet.get("observed_rom_decision")
    if not isinstance(observed, dict):
        return None
    if observed.get("scenario_id") != scenario_id:
        return None
    if observed.get("kind") != "rom_score_materialization":
        return None
    if observed.get("available") is not True or observed.get("status") != "pass":
        return None
    policy = observed.get("policy")
    if not isinstance(policy, dict):
        return None
    if policy.get("verdict") != "pass" or policy.get("rom_best_action_id") != "move_spikes":
        return None
    agreement = observed.get("python_agreement")
    if not isinstance(agreement, dict):
        return None
    if safe_int(agreement.get("contribution_mismatches"), -1) != 0:
        return None
    if agreement.get("score_bytes_match") is not True:
        return None
    if agreement.get("selector_top_match") is not True:
        return None
    python_mirror = packet.get("python_mirror")
    if not isinstance(python_mirror, dict):
        return None
    mirror_comparison = python_mirror.get("rom_comparison")
    if not isinstance(mirror_comparison, dict):
        return None
    if safe_int(mirror_comparison.get("contribution_mismatches"), -1) != 0:
        return None
    if mirror_comparison.get("score_bytes_match") is not True:
        return None
    if mirror_comparison.get("selector_top_match") is not True:
        return None
    hook_equivalence = agreement.get("hook_equivalence")
    if not isinstance(hook_equivalence, dict):
        return None
    for field in ("checked", "match", "chosen_match", "score_bytes_match"):
        if hook_equivalence.get(field) is not True:
            return None

    decision = observed.get("decision")
    if not isinstance(decision, dict):
        return None
    selector_path = decision.get("selector_path")
    if not isinstance(selector_path, dict):
        return None
    if selector_path.get("source") != "rom_score_materialization_final_scores":
        return None
    if selector_path.get("best_action_id") != "move_spikes":
        return None
    if safe_int(selector_path.get("best_score"), -1) != 37:
        return None
    if selector_path.get("second_action_id") != "move_sludge_bomb":
        return None
    if safe_int(selector_path.get("second_score"), -1) != 38:
        return None
    score_gap = safe_int(selector_path.get("score_gap"), -1)
    if score_gap != 1:
        return None

    if not any(
        rom_evidence is observed
        or (
            rom_evidence.get("kind") == "rom_score_materialization"
            and rom_evidence.get("scenario_id") == scenario_id
            and rom_evidence.get("status") == "pass"
        )
        for rom_evidence in dict_items(packet.get("rom_evidence"))
    ):
        return None

    rom_contributions = packet.get("rom_contributions")
    if not isinstance(rom_contributions, dict):
        return None
    if rom_contributions.get("available") is not True:
        return None
    if safe_int(rom_contributions.get("matched_trace_count"), -1) != 1:
        return None
    if rom_contributions.get("unmatched_trace_ids") != []:
        return None
    matching_events = [
        event
        for event in dict_items(rom_contributions.get("events"))
        if event.get("rule_id") == rule_id
    ]
    if len(matching_events) != 1:
        return None
    event = matching_events[0]
    if event.get("trace_id") != scenario_id:
        return None
    if safe_int(event.get("before"), -1) != 20:
        return None
    if safe_int(event.get("after"), -1) != 19:
        return None
    if safe_int(event.get("delta"), 0) != -1:
        return None
    if event.get("operation") != "encourage_tier_weight":
        return None
    candidate = event.get("candidate")
    if not isinstance(candidate, dict):
        return None
    if candidate.get("move_name") != "SPIKES":
        return None
    candidate_move_id = safe_int(candidate.get("move_id"), -1)
    slot_index = safe_int(candidate.get("slot_index"), -1)
    if candidate_move_id != 191 or slot_index != 0:
        return None
    event_anchor = event.get("source_anchor")
    if not isinstance(event_anchor, dict):
        return None
    if event_anchor.get("anchor_status") != "mapped":
        return None
    if event_anchor.get("rule_id") != rule_id:
        return None
    if event_anchor.get("source_label") != ".EnemyUnderPressure":
        return None
    candidate_scores = dict_items(packet.get("candidate_scores"))
    if not any(
        candidate_score.get("action_id") == "move_spikes"
        and any(
            contribution.get("rule_id") == rule_id
            and safe_int(contribution.get("before"), -1) == 20
            and safe_int(contribution.get("after"), -1) == 19
            and safe_int(contribution.get("delta"), 0) == -1
            for contribution in dict_items(candidate_score.get("contributions"))
        )
        for candidate_score in candidate_scores
    ):
        return None

    return {
        "source_label": str(anchor.get("source_label", "")),
        "parent_label": str(anchor.get("parent_label", "")),
        "scenario_id": scenario_id,
        "candidate_move": str(candidate.get("move_name", "")),
        "candidate_move_id": candidate_move_id,
        "slot_index": slot_index,
        "before": safe_int(event.get("before"), -1),
        "after": safe_int(event.get("after"), -1),
        "delta": safe_int(event.get("delta"), 0),
        "operation": str(event.get("operation", "")),
        "best_action_id": str(selector_path.get("best_action_id", "")),
        "second_action_id": str(selector_path.get("second_action_id", "")),
        "score_gap": score_gap,
    }


def deity_packet_apply_spikes_layer_bias_non_spikes_negative(packet: dict[str, Any]) -> dict[str, Any] | None:
    scenario_id = "generated_spikes_spin_1_00000"
    rule_id = "move.apply_move_model.apply_spikes_layer_bias"
    lookahead_rule_id = "move.apply_lookahead_to_top_move_candidates"
    if packet.get("scenario_id") != scenario_id:
        return None
    if packet.get("family") != "spikes_spin":
        return None
    if packet.get("deity_evidence_marker") != "BOSS_AI_DEITY_PROOF_COMPLETE":
        return None
    if packet.get("proof_blockers") != []:
        return None
    proof_status = packet.get("proof_status")
    if not isinstance(proof_status, dict):
        return None
    if proof_status.get("blockers") != [] or proof_status.get("missing_ids") != []:
        return None
    if not deity_packet_has_present_ids(
        packet,
        (
            "observed_rom_decision",
            "candidate_scores",
            "score_bytes",
            "selector_path",
            "rom_contribution_deltas",
            "public_info_inputs",
            "public_reads.snapshotted",
            "python_contribution.normalized",
            "rom_python_agreement.reported",
        ),
    ):
        return None

    anchor_info = deity_packet_apply_spikes_layer_bias_public_anchor(packet)
    if anchor_info is None:
        return None

    observed = packet.get("observed_rom_decision")
    if not isinstance(observed, dict):
        return None
    if observed.get("scenario_id") != scenario_id:
        return None
    if observed.get("kind") != "rom_score_materialization":
        return None
    if observed.get("available") is not True or observed.get("status") != "pass":
        return None
    policy = observed.get("policy")
    if not isinstance(policy, dict):
        return None
    if policy.get("verdict") != "pass" or policy.get("rom_best_action_id") != "move_spikes":
        return None
    agreement = observed.get("python_agreement")
    if not isinstance(agreement, dict):
        return None
    if safe_int(agreement.get("contribution_mismatches"), -1) != 0:
        return None
    if agreement.get("score_bytes_match") is not True:
        return None
    if agreement.get("selector_top_match") is not True:
        return None
    hook_equivalence = agreement.get("hook_equivalence")
    if not isinstance(hook_equivalence, dict):
        return None
    for field in ("checked", "match", "chosen_match", "score_bytes_match"):
        if hook_equivalence.get(field) is not True:
            return None
    python_mirror = packet.get("python_mirror")
    if not isinstance(python_mirror, dict):
        return None
    mirror_comparison = python_mirror.get("rom_comparison")
    if not isinstance(mirror_comparison, dict):
        return None
    if safe_int(mirror_comparison.get("contribution_mismatches"), -1) != 0:
        return None
    if mirror_comparison.get("score_bytes_match") is not True:
        return None
    if mirror_comparison.get("selector_top_match") is not True:
        return None

    decision = observed.get("decision")
    if not isinstance(decision, dict):
        return None
    selector_path = decision.get("selector_path")
    if not isinstance(selector_path, dict):
        return None
    if selector_path.get("source") != "rom_score_materialization_final_scores":
        return None
    if selector_path.get("best_action_id") != "move_spikes":
        return None
    if safe_int(selector_path.get("best_score"), -1) != 37:
        return None
    if selector_path.get("second_action_id") != "move_sludge_bomb":
        return None
    if safe_int(selector_path.get("second_score"), -1) != 38:
        return None
    score_gap = safe_int(selector_path.get("score_gap"), -1)
    if score_gap != 1:
        return None

    candidate_score = None
    for candidate in dict_items(packet.get("candidate_scores")):
        if candidate.get("action_id") == "move_sludge_bomb":
            candidate_score = candidate
            break
    if candidate_score is None:
        return None
    if candidate_score.get("blocked") is not False:
        return None
    if candidate_score.get("kind") != "move":
        return None
    if candidate_score.get("name") != "Sludge Bomb":
        return None
    if safe_int(candidate_score.get("slot"), -1) != 2:
        return None
    if safe_int(candidate_score.get("initial_score"), -1) != 20:
        return None
    if safe_int(candidate_score.get("pre_lookahead_score"), -1) != 20:
        return None
    if safe_int(candidate_score.get("final_score"), -1) != 38:
        return None
    candidate_contributions = dict_items(candidate_score.get("contributions"))
    if len(candidate_contributions) != 1:
        return None
    contribution = candidate_contributions[0]
    if contribution.get("rule_id") != lookahead_rule_id:
        return None
    if safe_int(contribution.get("before"), -1) != 20:
        return None
    if safe_int(contribution.get("after"), -1) != 38:
        return None
    lookahead_delta = safe_int(contribution.get("delta"), 0)
    if lookahead_delta != 18:
        return None
    if any(
        item.get("rule_id") == rule_id
        for item in candidate_contributions
    ):
        return None

    rom_contributions = packet.get("rom_contributions")
    if not isinstance(rom_contributions, dict):
        return None
    if rom_contributions.get("available") is not True:
        return None
    if safe_int(rom_contributions.get("matched_trace_count"), -1) != 1:
        return None
    if rom_contributions.get("unmatched_trace_ids") != []:
        return None
    sludge_events = [
        event
        for event in dict_items(rom_contributions.get("events"))
        if event.get("trace_id") == scenario_id
        and isinstance(event.get("candidate"), dict)
        and event["candidate"].get("move_name") == "SLUDGE_BOMB"
    ]
    if any(event.get("rule_id") == rule_id for event in sludge_events):
        return None
    lookahead_events = [
        event
        for event in sludge_events
        if event.get("rule_id") == lookahead_rule_id
    ]
    if len(lookahead_events) != 1:
        return None
    event = lookahead_events[0]
    if safe_int(event.get("before"), -1) != 20:
        return None
    if safe_int(event.get("after"), -1) != 38:
        return None
    if safe_int(event.get("delta"), 0) != lookahead_delta:
        return None
    if event.get("operation") != "apply_signed_lookahead_delta":
        return None
    candidate = event.get("candidate")
    if not isinstance(candidate, dict):
        return None
    if safe_int(candidate.get("move_id"), -1) != 188:
        return None
    if safe_int(candidate.get("slot_index"), -1) != 1:
        return None

    return {
        "source_label": anchor_info["source_label"],
        "parent_label": anchor_info["parent_label"],
        "scenario_id": scenario_id,
        "candidate_action_id": "move_sludge_bomb",
        "candidate_move": str(candidate.get("move_name", "")),
        "candidate_move_id": safe_int(candidate.get("move_id"), -1),
        "slot_index": safe_int(candidate.get("slot_index"), -1),
        "initial_score": safe_int(candidate_score.get("initial_score"), -1),
        "pre_lookahead_score": safe_int(candidate_score.get("pre_lookahead_score"), -1),
        "final_score": safe_int(candidate_score.get("final_score"), -1),
        "only_contribution_rule_id": lookahead_rule_id,
        "lookahead_delta": lookahead_delta,
        "best_action_id": str(selector_path.get("best_action_id", "")),
        "second_action_id": str(selector_path.get("second_action_id", "")),
        "score_gap": score_gap,
        "input_id": anchor_info["input_id"],
        "outcome": anchor_info["outcome"],
        "snapshot_keys": anchor_info["snapshot_keys"],
    }


def deity_packet_apply_spikes_layer_bias_public_anchor(packet: dict[str, Any]) -> dict[str, Any] | None:
    public_info_inputs = packet.get("public_info_inputs")
    if not isinstance(public_info_inputs, dict):
        return None
    rule_id = "move.apply_move_model.apply_spikes_layer_bias"
    for field, id_key in (
        ("predicate_branches", "predicate_id"),
        ("public_read_probes", "probe_id"),
    ):
        for entry in dict_items(public_info_inputs.get(field)):
            if entry.get("trace_id") != "generated_spikes_spin_1_00000":
                continue
            if entry.get(id_key) != "spikes_existing_layer_count":
                continue
            if entry.get("outcome") != "zero_existing_layers":
                continue
            snapshot = entry.get("snapshot")
            if not isinstance(snapshot, dict):
                continue
            player_screens = snapshot.get("wPlayerScreens")
            if not isinstance(player_screens, dict):
                continue
            if player_screens.get("available") is not True:
                continue
            if player_screens.get("values") != [0]:
                continue
            anchor = entry.get("source_anchor")
            if not isinstance(anchor, dict):
                continue
            if anchor.get("anchor_status") != "mapped":
                continue
            if anchor.get("rule_id") != rule_id:
                continue
            if anchor.get("source_label") != ".ApplySpikesLayerBias":
                continue
            if anchor.get("parent_label") != "BossAI_ApplyMoveModel":
                continue
            public_reads = anchor.get("public_reads")
            if not isinstance(public_reads, list):
                continue
            if set(public_reads) != {"wBossAITurnsElapsed", "wPlayerScreens"}:
                continue
            return {
                "source_label": str(anchor.get("source_label", "")),
                "parent_label": str(anchor.get("parent_label", "")),
                "input_id": str(entry.get(id_key, "")),
                "outcome": str(entry.get("outcome", "")),
                "snapshot_keys": sorted(str(key) for key in snapshot),
            }
    return None


def deity_packet_public_info_source_anchors(packet: dict[str, Any]) -> list[dict[str, Any]]:
    public_info_inputs = packet.get("public_info_inputs")
    if not isinstance(public_info_inputs, dict):
        return []
    anchors: list[dict[str, Any]] = []
    for input_kind, field, id_key in (
        ("predicate_branch", "predicate_branches", "predicate_id"),
        ("public_read_probe", "public_read_probes", "probe_id"),
    ):
        for entry in dict_items(public_info_inputs.get(field)):
            outcome = entry.get("outcome")
            if outcome in ("", None):
                continue
            snapshot = entry.get("snapshot")
            if not isinstance(snapshot, dict) or not snapshot:
                continue
            anchor = entry.get("source_anchor")
            if not isinstance(anchor, dict):
                continue
            rule_id = str(anchor.get("rule_id", ""))
            if not rule_id:
                continue
            if str(anchor.get("anchor_status", "")) != "mapped":
                continue
            anchors.append(
                {
                    "rule_id": rule_id,
                    "input_kind": input_kind,
                    "input_id": str(entry.get(id_key, "")),
                    "outcome": str(outcome),
                    "snapshot_keys": sorted(str(key) for key in snapshot),
                    "source_label": str(anchor.get("source_label", "")),
                    "parent_label": str(anchor.get("parent_label", "")),
                }
            )
    return anchors


def add_public_read_witness_evidence(
    evidence: dict[tuple[str, str], list[dict[str, Any]]],
    *,
    artifact_path: str,
    root: Path,
    report: dict[str, Any] | None = None,
) -> None:
    if report is None:
        path = Path(artifact_path)
        if not path.is_absolute():
            path = root / path
        try:
            report = load_rom_contribution_trace(path)
        except Exception:
            return
    for entry in [
        *dict_items(report.get("rule_entries")),
        *dict_items(report.get("predicate_branch_entries")),
        *dict_items(report.get("public_read_probe_entries")),
        *dict_items(report.get("events")),
    ]:
        source = entry.get("source") if isinstance(entry, dict) else None
        if not isinstance(source, dict):
            continue
        rule_id = str(source.get("rule_id", ""))
        if not rule_id:
            continue
        public_reads = source.get("public_reads", [])
        if not isinstance(public_reads, list) or not public_reads:
            continue
        snapshot = entry.get("public_input_snapshot")
        if not isinstance(snapshot, dict) or not snapshot:
            continue
        add_witness_evidence(
            evidence,
            rule_id=rule_id,
            role="public_read_provenance",
            item={
                "artifact": artifact_path,
                "evidence_kind": str(entry.get("event_type", "public_input_snapshot")),
                "status": "public_input_snapshot_observed",
                "snapshot_keys": sorted(str(key) for key in snapshot),
            },
        )
    for entry in dict_items(report.get("predicate_branch_entries")):
        source = entry.get("source") if isinstance(entry, dict) else None
        if not isinstance(source, dict):
            continue
        rule_id = str(source.get("rule_id", ""))
        if not rule_id:
            continue
        predicate = entry.get("predicate")
        if not isinstance(predicate, dict):
            continue
        outcome = predicate.get("outcome")
        if outcome in ("", None):
            continue
        snapshot = entry.get("public_input_snapshot")
        if not isinstance(snapshot, dict) or not snapshot:
            continue
        add_witness_evidence(
            evidence,
            rule_id=rule_id,
            role="boundary",
            item={
                "artifact": artifact_path,
                "evidence_kind": "predicate_branch_boundary_snapshot",
                "status": "predicate_outcome_snapshot_observed",
                "predicate_id": str(predicate.get("predicate_id", "")),
                "outcome": str(outcome),
                "snapshot_keys": sorted(str(key) for key in snapshot),
            },
        )
        if predicate_outcome_is_negative(outcome):
            add_witness_evidence(
                evidence,
                rule_id=rule_id,
                role="negative",
                item={
                    "artifact": artifact_path,
                    "evidence_kind": "predicate_branch_negative_snapshot",
                    "status": "negative_predicate_outcome_observed",
                    "predicate_id": str(predicate.get("predicate_id", "")),
                    "outcome": str(outcome),
                    "snapshot_keys": sorted(str(key) for key in snapshot),
                },
            )


def predicate_outcome_is_negative(outcome: Any) -> bool:
    text = str(outcome).strip().lower()
    if not text:
        return False
    if text in {
        "disabled",
        "false",
        "unavailable",
    }:
        return True
    return text.startswith(("not_", "cannot_", "no_")) or text.endswith("_unavailable")


def add_adaptive_lead_parent_witness_evidence(
    evidence: dict[tuple[str, str], list[dict[str, Any]]],
    *,
    artifact_path: str,
    root: Path,
    report: dict[str, Any] | None = None,
) -> None:
    if report is None:
        path = Path(artifact_path)
        if not path.is_absolute():
            path = root / path
        try:
            report = load_rom_contribution_trace(path)
        except Exception:
            return
    executed_rule_ids = {
        str(rule_id)
        for rule_id in report.get("executed_rule_ids", [])
        if str(rule_id)
    }
    parent_rule_id = "move.maybe_pick_adaptive_enemy_lead"
    if parent_rule_id not in executed_rule_ids:
        return
    for entry in dict_items(report.get("predicate_branch_entries")):
        source = entry.get("source") if isinstance(entry, dict) else None
        predicate = entry.get("predicate") if isinstance(entry, dict) else None
        snapshot = entry.get("public_input_snapshot") if isinstance(entry, dict) else None
        if not isinstance(source, dict) or not isinstance(predicate, dict):
            continue
        if str(source.get("rule_id", "")) != (
            "move.maybe_pick_adaptive_enemy_lead.should_use_adaptive_lead_for_trainer"
        ):
            continue
        if str(predicate.get("predicate_id", "")) != "adaptive_lead_trainer_match":
            continue
        if str(predicate.get("outcome", "")) != "disabled":
            continue
        if not isinstance(snapshot, dict) or not snapshot:
            continue
        add_witness_evidence(
            evidence,
            rule_id=parent_rule_id,
            role="boundary",
            item={
                "artifact": artifact_path,
                "evidence_kind": "adaptive_lead_disabled_terminal_boundary",
                "status": "parent_boundary_child_predicate_observed",
                "child_rule_id": str(source.get("rule_id", "")),
                "predicate_id": "adaptive_lead_trainer_match",
                "outcome": "disabled",
                "snapshot_keys": sorted(str(key) for key in snapshot),
            },
        )
        add_witness_evidence(
            evidence,
            rule_id=parent_rule_id,
            role="negative",
            item={
                "artifact": artifact_path,
                "evidence_kind": "adaptive_lead_disabled_terminal_predicate",
                "status": "negative_child_predicate_stopped_parent_observed",
                "child_rule_id": str(source.get("rule_id", "")),
                "predicate_id": "adaptive_lead_trainer_match",
                "outcome": "disabled",
                "snapshot_keys": sorted(str(key) for key in snapshot),
            },
        )
        return


def add_score_margin_boundary_witness_evidence(
    evidence: dict[tuple[str, str], list[dict[str, Any]]],
    *,
    artifact_path: str,
    root: Path,
    report: dict[str, Any] | None = None,
) -> None:
    if report is None:
        path = Path(artifact_path)
        if not path.is_absolute():
            path = root / path
        try:
            report = load_rom_contribution_trace(path)
        except Exception:
            return
    if report.get("source") != "trace_rom_pyboy_hooks":
        return
    selector_scores = selector_score_bytes(report.get("selector_entry_scores"))
    if selector_scores is None:
        return
    best_second = selector_best_and_second_slots(selector_scores)
    if best_second is None:
        return
    best_slot, second_slot = best_second
    chosen = report.get("chosen")
    if not isinstance(chosen, dict) or safe_int(chosen.get("slot_index"), -1) != best_slot:
        return

    raw_move_ids = report.get("move_ids", [])
    move_ids = [safe_int(value, -1) for value in raw_move_ids] if isinstance(raw_move_ids, list) else []
    rule_slot_deltas: dict[tuple[str, tuple[int, int]], dict[str, Any]] = {}
    for event in dict_items(report.get("events")):
        if event.get("event_type") != "score_delta":
            continue
        if event.get("changed") is not True:
            continue
        candidate_key = score_candidate_key(event.get("candidate"))
        if candidate_key is None:
            continue
        slot_index, move_id = candidate_key
        if slot_index >= len(selector_scores):
            continue
        if slot_index < len(move_ids) and move_ids[slot_index] > 0 and move_ids[slot_index] != move_id:
            continue
        before = safe_int(event.get("score_before"), 999)
        after = safe_int(event.get("score_after"), 999)
        delta = safe_int(event.get("delta"), 0)
        if delta == 0 or after - before != delta:
            continue
        source = event.get("source") if isinstance(event, dict) else None
        if not isinstance(source, dict):
            continue
        rule_id = str(source.get("rule_id", ""))
        if not rule_id:
            continue
        key = (rule_id, candidate_key)
        aggregate = rule_slot_deltas.setdefault(
            key,
            {
                "rule_id": rule_id,
                "source_label": str(source.get("source_label", "")),
                "parent_label": str(source.get("parent_label", "")),
                "candidate": event.get("candidate"),
                "slot_index": slot_index,
                "move_id": move_id,
                "delta": 0,
                "event_count": 0,
            },
        )
        aggregate["delta"] = int(aggregate["delta"]) + delta
        aggregate["event_count"] = int(aggregate["event_count"]) + 1

    for aggregate in rule_slot_deltas.values():
        slot_index = int(aggregate["slot_index"])
        total_delta = int(aggregate["delta"])
        final_score = selector_scores[slot_index]
        score_without_rule = final_score - total_delta
        if slot_index == best_slot:
            boundary_observed = score_without_rule >= selector_scores[second_slot]
            compared_slot = second_slot
            boundary_relation = "best_candidate_would_reach_runner_up_score"
            counterfactual_observed = score_without_rule > selector_scores[second_slot]
            counterfactual_relation = "best_candidate_would_lose_to_runner_up"
        elif slot_index == second_slot:
            boundary_observed = score_without_rule <= selector_scores[best_slot]
            compared_slot = best_slot
            boundary_relation = "runner_up_would_reach_best_score"
            counterfactual_observed = score_without_rule < selector_scores[best_slot]
            counterfactual_relation = "runner_up_would_beat_best_candidate"
        else:
            continue
        if not boundary_observed:
            continue
        candidate = aggregate.get("candidate")
        if not isinstance(candidate, dict):
            candidate = {}
        add_witness_evidence(
            evidence,
            rule_id=str(aggregate["rule_id"]),
            role="boundary",
            item={
                "artifact": artifact_path,
                "evidence_kind": "rom_score_delta_selector_margin_boundary",
                "status": "score_margin_boundary_observed",
                "source_label": aggregate["source_label"],
                "parent_label": aggregate["parent_label"],
                "candidate_move": str(candidate.get("move_name", "")),
                "candidate_move_id": int(aggregate["move_id"]),
                "slot_index": slot_index,
                "compared_slot_index": compared_slot,
                "selector_score": final_score,
                "compared_selector_score": selector_scores[compared_slot],
                "observed_delta": total_delta,
                "score_without_rule": score_without_rule,
                "boundary_relation": boundary_relation,
                "event_count": int(aggregate["event_count"]),
            },
        )
        if not counterfactual_observed:
            continue
        add_witness_evidence(
            evidence,
            rule_id=str(aggregate["rule_id"]),
            role="counterfactual_flip",
            item={
                "artifact": artifact_path,
                "evidence_kind": "rom_score_delta_selector_margin_counterfactual",
                "status": "score_margin_counterfactual_flip_observed",
                "source_label": aggregate["source_label"],
                "parent_label": aggregate["parent_label"],
                "candidate_move": str(candidate.get("move_name", "")),
                "candidate_move_id": int(aggregate["move_id"]),
                "slot_index": slot_index,
                "compared_slot_index": compared_slot,
                "selector_score": final_score,
                "compared_selector_score": selector_scores[compared_slot],
                "observed_delta": total_delta,
                "score_without_rule": score_without_rule,
                "counterfactual_relation": counterfactual_relation,
                "event_count": int(aggregate["event_count"]),
            },
        )


def selector_score_bytes(value: Any) -> list[int] | None:
    if not isinstance(value, list) or len(value) < 2:
        return None
    scores: list[int] = []
    for item in value[:4]:
        score = safe_int(item, -1)
        if score < 0:
            return None
        scores.append(score)
    return scores if len(scores) >= 2 else None


def selector_best_and_second_slots(scores: list[int]) -> tuple[int, int] | None:
    legal = [
        (score, slot_index)
        for slot_index, score in enumerate(scores)
        if score < 80
    ]
    if len(legal) < 2:
        return None
    legal.sort()
    return legal[0][1], legal[1][1]


def add_score_no_delta_negative_witness_evidence(
    evidence: dict[tuple[str, str], list[dict[str, Any]]],
    *,
    artifact_path: str,
    root: Path,
    report: dict[str, Any] | None = None,
) -> None:
    if report is None:
        path = Path(artifact_path)
        if not path.is_absolute():
            path = root / path
        try:
            report = load_rom_contribution_trace(path)
        except Exception:
            return
    changed_delta_keys: set[tuple[str, tuple[int, int]]] = set()
    for event in dict_items(report.get("events")):
        source = event.get("source") if isinstance(event, dict) else None
        if not isinstance(source, dict):
            continue
        rule_id = str(source.get("rule_id", ""))
        if not rule_id or event.get("changed") is not True:
            continue
        candidate_key = score_candidate_key(event.get("candidate"))
        if candidate_key is None:
            continue
        changed_delta_keys.add((rule_id, candidate_key))

    seen_negative_keys: set[tuple[str, tuple[int, int]]] = set()
    for entry in dict_items(report.get("rule_entries")):
        source = entry.get("source") if isinstance(entry, dict) else None
        if not isinstance(source, dict):
            continue
        rule_id = str(source.get("rule_id", ""))
        if not rule_id:
            continue
        candidate_key = score_candidate_key(entry.get("candidate"))
        if candidate_key is None:
            continue
        key = (rule_id, candidate_key)
        if key in changed_delta_keys or key in seen_negative_keys:
            continue
        seen_negative_keys.add(key)
        candidate = entry.get("candidate")
        add_witness_evidence(
            evidence,
            rule_id=rule_id,
            role="negative",
            item={
                "artifact": artifact_path,
                "evidence_kind": "rom_rule_entry_without_score_delta",
                "status": "negative_no_score_delta_observed",
                "rule_entry_index": entry.get("index"),
                "candidate_move": str(candidate.get("move_name", "")),
                "candidate_move_id": candidate_key[1],
                "slot_index": candidate_key[0],
            },
        )


def score_candidate_key(value: Any) -> tuple[int, int] | None:
    if not isinstance(value, dict):
        return None
    if value.get("kind") != "move":
        return None
    try:
        slot_index = int(value.get("slot_index", -1))
        move_id = int(value.get("move_id", -1))
    except (TypeError, ValueError):
        return None
    if slot_index < 0 or move_id <= 0:
        return None
    return (slot_index, move_id)


def add_witness_evidence(
    evidence: dict[tuple[str, str], list[dict[str, Any]]],
    *,
    rule_id: str,
    role: str,
    item: dict[str, Any],
) -> None:
    if not rule_id or role not in EXHAUSTIVE_WITNESS_ROLES:
        return
    key = (rule_id, role)
    bucket = evidence.setdefault(key, [])
    if item not in bucket:
        bucket.append(item)


def dict_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def boss_ai_universe_counters(
    *,
    label_rows: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    coverage_targets: dict[str, Any],
    public_reads: dict[str, Any],
    class_rows: list[dict[str, Any]],
    witness_inventory: dict[str, Any] | None = None,
) -> dict[str, int]:
    unmapped_rows = [
        row for row in label_rows if row.get("reachable_status") == "reachable_unmapped_label"
    ]
    missing_public_read_count = int(public_reads.get("missing_probe_outcome_count", 0) or 0)
    if public_reads.get("target_rule_count", 0) and not public_reads.get("available", False):
        missing_public_read_count = int(public_reads.get("target_rule_count", 0) or 0)
    missing_materializers = [
        row for row in class_rows if not row.get("materializer_command")
    ]
    return {
        "missing_reachable_label_count": len(unmapped_rows),
        "missing_rule_count": len(unmapped_rows),
        "missing_branch_count": int(coverage_targets.get("target_count", 0) or 0),
        "missing_public_read_count": missing_public_read_count,
        "missing_class_id_count": sum(
            1
            for row in class_rows
            if not row.get("class_id") or not row.get("canonical_state_class_valid")
        ),
        "missing_proof_artifact_count": int(coverage_targets.get("target_count", 0) or 0),
        "missing_materialization_path_count": len(missing_materializers),
        "missing_witness_role_count": int(
            (witness_inventory or {}).get("missing_witness_role_count", 0) or 0
        ),
    }


def boss_ai_universe_blocking_gaps(counters: dict[str, int]) -> list[str]:
    gap_by_counter = {
        "missing_reachable_label_count": "boss_ai_universe_has_unmapped_reachable_labels",
        "missing_rule_count": "boss_ai_universe_has_labels_without_rule_ids",
        "missing_branch_count": "boss_ai_dynamic_targets_lack_complete_branch_proofs",
        "missing_public_read_count": "boss_ai_public_reads_lack_provenance",
        "missing_class_id_count": "boss_ai_canonical_class_ids_missing",
        "missing_proof_artifact_count": "boss_ai_dynamic_targets_lack_proof_artifacts",
        "missing_materialization_path_count": "boss_ai_materialization_paths_missing",
        "missing_witness_role_count": "boss_ai_exhaustive_class_witness_roles_missing",
    }
    return [
        gap
        for key, gap in gap_by_counter.items()
        if int(counters.get(key, 0)) > 0
    ]


def materializer_command_for_rule(rule: dict[str, Any]) -> str:
    rule_id = str(rule.get("rule_id", "boss_ai_rule"))
    family = suggested_generator(rule)
    trace_mode = recommended_trace_mode(rule)
    if trace_mode == "rom_route_contribution_trace":
        out = f".local\\tmp\\boss_ai_debugger\\universe_{safe_id(rule_id)}_rom_contribution.json"
        return f"python -m tools.boss_ai_debugger rom-contribution-trace --boss-route koga --json-out {out}"
    out = f".local\\tmp\\boss_ai_debugger\\universe_{safe_id(rule_id)}.json"
    proof = " --run-rom-proof auto" if trace_mode == "rom_score_materialization" else ""
    return (
        "python -m tools.boss_ai_debugger explain-decision "
        f"--generated-family {family}{proof} --json-out {out}"
    )


def full_symbol_for_rule(rule: dict[str, Any]) -> str:
    label = str(rule.get("source_label", ""))
    parent = rule.get("parent_label")
    return full_symbol_for_label(label, parent if isinstance(parent, str) else None)


def decision_surface_for_rule(rule: dict[str, Any]) -> str:
    if rule.get("score_trace_target", False):
        return "move_score"
    if str(rule.get("coverage_mode", "")) == "rom_route_execution_hook":
        return "switch_dispatch"
    return "boss_ai_rule"


def first_next_command(label_rows: list[dict[str, Any]], class_rows: list[dict[str, Any]]) -> str:
    for row in label_rows:
        if row.get("reachable_status") == "reachable_unmapped_label":
            return str(row.get("materializer_command", ""))
    for row in class_rows:
        if not row.get("class_id"):
            return str(row.get("materializer_command", ""))
    return "python -m tools.boss_ai_debugger universe --json"


def safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value).strip("_") or "boss_ai"


def resolve_score_materialization_paths(
    paths: list[Path] | None,
    *,
    root: Path = ROOT,
) -> list[Path]:
    if paths is not None:
        return paths
    discovered: list[Path] = []
    for directory, pattern in DEFAULT_SCORE_MATERIALIZATION_SOURCES:
        base = directory if directory.is_absolute() else root / directory
        discovered.extend(sorted(base.glob(pattern)))
    resolved: list[Path] = []
    seen: set[Path] = set()
    for path in discovered:
        key = path.resolve()
        if key in seen:
            continue
        seen.add(key)
        resolved.append(path)
    return resolved


def resolve_counterfactual_materialization_paths(
    paths: list[Path] | None,
    *,
    root: Path = ROOT,
) -> list[Path]:
    if paths is not None:
        return paths
    discovered: list[Path] = []
    for directory, pattern in DEFAULT_COUNTERFACTUAL_MATERIALIZATION_SOURCES:
        base = directory if directory.is_absolute() else root / directory
        discovered.extend(sorted(base.glob(pattern)))
    resolved: list[Path] = []
    seen: set[Path] = set()
    for path in discovered:
        key = path.resolve()
        if key in seen:
            continue
        seen.add(key)
        resolved.append(path)
    return resolved


def repo_rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def format_boss_ai_universe(report: dict[str, Any]) -> str:
    counters = report["counters"]
    lines = [
        "Boss AI debugger universe",
        f"proof_status={report['proof_status']} rules={report['rule_count']} labels={report['reachable_label_count']}",
        (
            "counters="
            + ", ".join(f"{key}={value}" for key, value in counters.items())
        ),
    ]
    if report["blocking_gaps"]:
        lines.extend(["", "Top blockers:"])
        for gap in report["blocking_gaps"][:8]:
            lines.append(f"  - {gap}")
    lines.extend(["", f"next={report['next_command']}"])
    return "\n".join(lines)
