from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError

from .generators import generate_scenarios, write_jsonl
from .trace_replay import (
    capture_id_for,
    load_move_names,
    parse_trace_file,
    replay_capture_fields,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DECISION_INPUT_DIR = ROOT / ".local" / "tmp" / "boss_ai_debugger" / "decision_inputs"
DEFAULT_GENERATED_INPUT_DIR = ROOT / ".local" / "tmp" / "boss_ai_debugger" / "generated_inputs"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def repo_rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_repo_path(path_text: str | Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def normalize_target_id(value: str) -> str:
    value = value.split("#", 1)[0]
    value = value.replace(".", "")
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()).strip("_") or "boss_ai_decision"


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def git_text(args: list[str]) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def dirty_diff_hash() -> str:
    diff = git_text(
        [
            "diff",
            "--",
            "tools/boss_ai_debugger",
            "tools/trace",
            "tools/audit/check_boss_ai*",
            "audit/boss_ai_trace",
            "audit/boss_ai_debugger",
        ]
    )
    return hashlib.sha256(diff.encode("utf-8")).hexdigest().upper()


def manifest_capture_matches(capture: dict[str, Any], target: str) -> bool:
    normalized = normalize_target_id(target)
    candidates = [
        str(capture.get("id", "")),
        str(capture.get("boss", "")),
        Path(str(capture.get("out", ""))).stem.replace("_live", ""),
    ]
    return normalized in {normalize_target_id(item) for item in candidates if item}


def find_manifest_capture(
    manifest: dict[str, Any],
    *,
    boss_route: str | None,
    capture_id: str | None,
) -> dict[str, Any]:
    target = boss_route or capture_id or ""
    if not target:
        raise PreferenceDataError("provide --boss-route or --capture-id for live decision resolution")
    captures = [
        item
        for item in manifest.get("captures", [])
        if isinstance(item, dict) and manifest_capture_matches(item, target)
    ]
    if not captures:
        known = ", ".join(
            str(item.get("id", ""))
            for item in manifest.get("captures", [])
            if isinstance(item, dict) and item.get("id")
        )
        raise PreferenceDataError(
            "unsupported Boss AI decision target "
            f"{target!r}; no live capture manifest row matches. "
            "next_action=refresh or add a replayable boss-route capture under "
            f"{repo_rel(ROOT / 'audit' / 'boss_ai_trace' / 'live_capture_manifest.json')}. "
            f"known_routes={known}"
        )
    if len(captures) > 1:
        ids = ", ".join(str(item.get("id", "")) for item in captures)
        raise PreferenceDataError(
            f"ambiguous Boss AI decision target {target!r}; pass --boss-route or "
            f"--capture-id with one of: {ids}"
        )
    return captures[0]


def default_decision_input_manifest_path(route_id: str, decision_index: int) -> Path:
    return DEFAULT_DECISION_INPUT_DIR / f"{safe_id(route_id)}_decision_{decision_index}.manifest.json"


def default_generated_input_manifest_path(target_id: str) -> Path:
    return DEFAULT_GENERATED_INPUT_DIR / f"{safe_id(target_id)}.manifest.json"


def default_generated_scenario_path(target_id: str) -> Path:
    return DEFAULT_GENERATED_INPUT_DIR / f"{safe_id(target_id)}.jsonl"


def generated_scenario_path_for_manifest(target_id: str, output_path: Path | None) -> Path:
    if output_path is None:
        return default_generated_scenario_path(target_id)
    return output_path.with_name(f"{output_path.stem}.{safe_id(target_id)}.jsonl")


def resolve_generated_boss_decision_input(
    *,
    generated_family: str | None = None,
    case: str | None = None,
    policy_question: str | None = None,
    score_rule: str | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    target_id, family, scenario_count = generated_target_family(
        generated_family=generated_family,
        policy_question=policy_question,
        score_rule=score_rule,
    )
    scenarios = generate_scenarios(family=family, count=scenario_count, seed=1)
    scenario = choose_generated_scenario(
        scenarios,
        target_id=target_id,
        policy_question=policy_question,
        score_rule=score_rule,
        case=case,
    )
    scenario_id = str(scenario.get("id") or target_id)
    scenario_path = generated_scenario_path_for_manifest(target_id, output_path)
    write_jsonl([scenario], scenario_path)

    trace_rom = ROOT / "pokegold_trace.gbc"
    trace_symbols = ROOT / "pokegold_trace.sym"
    manifest_record = {
        "schema_version": 1,
        "kind": "boss_ai_decision_input_manifest",
        "generated_at": utc_now(),
        "target": {
            "generated_family": family,
            "requested_generated_family": generated_family or "",
            "case": case or "",
            "policy_question": policy_question or "",
            "score_rule": score_rule or "",
            "decision_surface": "score_rule" if score_rule else "generated_policy",
        },
        "resolution": {
            "source": "generated_scenario",
            "scenario_path": repo_rel(scenario_path),
            "scenario_id": scenario_id,
            "scenario_family": family,
            "generator_seed": 1,
            "generated_count": scenario_count,
            "selected_case": str(scenario.get("case_id") or case or ""),
            "sufficient": True,
        },
        "hash_basis": {
            "current_trace_rom_sha256": sha256_file(trace_rom),
            "current_trace_symbols_sha256": sha256_file(trace_symbols),
        },
        "source_state": {
            "git_commit": git_text(["rev-parse", "HEAD"]),
            "dirty_diff_sha256": dirty_diff_hash(),
            "scenario_artifact_sha256": sha256_file(scenario_path),
        },
        "known_limits": [
            "Generated decision inputs are deterministic public-state scenarios, not a navigated live battle state.",
            "ROM materialization support depends on the generated family and current trace basis.",
        ],
        "closed_evidence_ids": ["decision_input.generated_auto"],
    }
    out = output_path or default_generated_input_manifest_path(target_id)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest_record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    manifest_record["artifact_path"] = repo_rel(out)
    return {
        "scenario_path": scenario_path,
        "scenario_id": scenario_id,
        "manifest": manifest_record,
        "manifest_path": out,
    }


def generated_target_family(
    *,
    generated_family: str | None,
    policy_question: str | None,
    score_rule: str | None,
) -> tuple[str, str, int]:
    requested = [bool(generated_family), bool(policy_question), bool(score_rule)]
    if sum(1 for item in requested if item) != 1:
        raise PreferenceDataError(
            "provide exactly one generated Boss AI target: "
            "--generated-family, --policy-question, or --score-rule"
        )
    if policy_question:
        return policy_question, "mastery_policy", 16
    if score_rule:
        if score_rule != "move.spikes.public_rapid_spin_risk":
            raise PreferenceDataError(
                f"unsupported score-rule target {score_rule!r}; "
                "next_action=add a generated scenario resolver for this rule id"
            )
        return score_rule, "spikes_spin", 12
    return generated_family or "", generated_family or "", 12


def choose_generated_scenario(
    scenarios: list[dict[str, Any]],
    *,
    target_id: str,
    policy_question: str | None,
    score_rule: str | None,
    case: str | None,
) -> dict[str, Any]:
    if not scenarios:
        raise PreferenceDataError(f"generated target {target_id!r} produced no scenarios")
    if policy_question:
        match = first_scenario_matching(scenarios, policy_question)
        if match:
            return match
        raise PreferenceDataError(
            f"policy question {policy_question!r} is not covered by the mastery_policy generator"
        )
    if score_rule:
        match = first_scenario_matching(scenarios, "active_revealed_rapid_spin")
        return match or scenarios[0]
    if case and case not in {"", "best_review", "first"}:
        match = first_scenario_matching(scenarios, case)
        if match:
            return match
        raise PreferenceDataError(
            f"generated family case {case!r} is not available; use --case best_review or first"
        )
    return scenarios[0]


def first_scenario_matching(
    scenarios: list[dict[str, Any]],
    needle: str,
) -> dict[str, Any] | None:
    normalized = normalize_target_id(needle)
    for scenario in scenarios:
        haystack = json.dumps(scenario, sort_keys=True)
        if normalized in normalize_target_id(haystack):
            return scenario
    return None


def resolve_live_boss_decision_input(
    *,
    manifest_path: Path,
    boss_route: str | None = None,
    capture_id: str | None = None,
    decision_index: int | None = None,
    turn: int | None = None,
    decision_surface: str | None = None,
    public_state_predicate: str | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    if turn not in {None, 1}:
        target = boss_route or capture_id or "unknown"
        raise PreferenceDataError(
            f"unsupported Boss AI decision target {target!r}: turn={turn} is not "
            "available from committed live first-decision captures. "
            "next_action=add a replayable navigation/input manifest for that boss turn, "
            "then rerun explain-decision with --boss-route and --turn."
        )
    index = decision_index or 1
    if index < 1:
        raise PreferenceDataError("--decision-index must be >= 1")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    capture_row = find_manifest_capture(
        manifest,
        boss_route=boss_route,
        capture_id=capture_id,
    )
    route_id = str(capture_row.get("id") or boss_route or capture_id or "")
    trace_path = resolve_repo_path(str(capture_row.get("out", "")))
    if not trace_path.exists():
        raise PreferenceDataError(
            f"unsupported Boss AI decision target {route_id!r}: trace artifact is missing: "
            f"{repo_rel(trace_path)}. next_action=refresh live trace capture for route {route_id}."
        )

    captures = parse_trace_file(trace_path)
    if index > len(captures):
        raise PreferenceDataError(
            f"unsupported Boss AI decision target {route_id!r}: decision_index={index} "
            f"but {repo_rel(trace_path)} contains {len(captures)} capture(s). "
            "next_action=refresh a trace with the requested decision index or use "
            "--decision-index 1 for the committed first-decision capture."
        )
    fields = captures[index - 1]
    trace_capture_id = capture_id_for(trace_path, fields, index)
    verdict = replay_capture_fields(fields, trace_capture_id, trace_path, load_move_names())
    replay_verified = bool(verdict.match and verdict.verdict != "mismatch")
    trace_rom = resolve_repo_path(str(manifest.get("trace_rom", "pokegold_trace.gbc")))
    trace_symbols = resolve_repo_path(str(manifest.get("trace_symbols", "pokegold_trace.sym")))
    hash_basis = {
        "manifest_trace_rom_sha256": str(manifest.get("trace_rom_sha256", "")).upper(),
        "manifest_trace_symbols_sha256": str(manifest.get("trace_symbols_sha256", "")).upper(),
        "current_trace_rom_sha256": sha256_file(trace_rom),
        "current_trace_symbols_sha256": sha256_file(trace_symbols),
    }
    hash_basis["trace_rom_matches_manifest"] = (
        hash_basis["current_trace_rom_sha256"] == hash_basis["manifest_trace_rom_sha256"]
    )
    hash_basis["trace_symbols_matches_manifest"] = (
        hash_basis["current_trace_symbols_sha256"] == hash_basis["manifest_trace_symbols_sha256"]
    )
    manifest_record = {
        "schema_version": 1,
        "kind": "boss_ai_decision_input_manifest",
        "generated_at": utc_now(),
        "target": {
            "boss_route": route_id,
            "requested_boss_route": boss_route or "",
            "requested_capture_id": capture_id or "",
            "decision_index": index,
            "turn": turn,
            "decision_surface": decision_surface or "live_boss",
            "public_state_predicate": public_state_predicate or "",
        },
        "resolution": {
            "source": "live_capture_manifest",
            "capture_manifest_path": repo_rel(manifest_path),
            "capture_manifest_id": str(capture_row.get("id", "")),
            "capture_status": str(capture_row.get("status", "")),
            "trace_path": repo_rel(trace_path),
            "trace_capture_id": trace_capture_id,
            "source_kind": "current_live_trace_capture",
            "sufficient": True,
        },
        "replay_verification": {
            "verified": replay_verified,
            "method": "BossAI_SelectMove trace replay over captured score bytes",
            "verdict": verdict.verdict,
            "match": verdict.match,
            "reason": verdict.reason,
            "mode": verdict.mode,
            "chosen_id": verdict.chosen_id,
            "expected_move_ids": verdict.expected_move_ids,
        },
        "hash_basis": hash_basis,
        "source_state": {
            "git_commit": git_text(["rev-parse", "HEAD"]),
            "dirty_diff_sha256": dirty_diff_hash(),
            "trace_artifact_sha256": sha256_file(trace_path),
        },
        "known_limits": [
            "This resolver uses a committed live first-decision trace capture, not deep boss-battle navigation.",
            "Replay verification proves selector agreement for the captured score bytes; full score-rule provenance still needs rom-contribution-trace when absent.",
        ],
        "closed_evidence_ids": [
            "decision_input.auto_resolved",
            *(
                ["input_manifest.replay_verified"]
                if replay_verified
                else []
            ),
        ],
    }
    out = output_path or default_decision_input_manifest_path(route_id, index)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest_record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    manifest_record["artifact_path"] = repo_rel(out)
    return {
        "trace_paths": [trace_path],
        "trace_capture_id": trace_capture_id if len(captures) > 1 else None,
        "manifest": manifest_record,
        "manifest_path": out,
    }
