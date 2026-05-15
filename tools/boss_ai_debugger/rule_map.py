from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULE_MAP_PATH = ROOT / "audit" / "boss_ai_debugger" / "rule_map.json"
SOURCE_PATHS = (
    ROOT / "engine" / "battle" / "ai" / "boss_policy_move.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_policy_switch.asm",
)

LABEL_RE = re.compile(
    r"^(?:(?P<local>\.[A-Za-z0-9_]+)(?::)?|(?P<top>[A-Za-z_][A-Za-z0-9_]*):{1,2})$"
)
GENERIC_LOCAL_LABELS = {
    ".loop",
    ".next",
    ".done",
    ".no",
    ".yes",
    ".store",
    ".risk",
    ".none",
    ".none_found",
}

REQUIRED_LABELS = {
    "BossAI_ApplyMoveModel",
    "BossAI_SelectMove",
    ".ApplySpikesLayerBias",
    ".ApplyRevealedRapidSpinSpikesRisk",
    ".ApplySpikesLayer2UnrevealedSpinRisk",
    ".ApplySpikesLayer3UnrevealedSpinRisk",
    ".EnemyActiveBlocksRapidSpin",
    ".BossHasAvailableReserveGhost",
    ".PlayerHasSeenBenchRevealedRapidSpin",
    ".PlayerActiveLikelyCanRapidSpin",
    ".SpeciesLevelUpHasRapidSpin",
    "BossAI_SwitchOrTryItem",
    "BossAI_TryMortyHakiOracle",
    "BossAI_ComputeSwitchConfidence",
    "BossAI_ComputeSwitchCandidateRisk",
}

PUBLIC_READ_HINTS = {
    "Revealed": ["wPlayerUsedMoves"],
    "SeenBench": ["wBossAISeenPlayerSpecies"],
    "RapidSpin": ["wPlayerUsedMoves", "Moves + MOVE_EFFECT"],
    "Foresight": ["wPlayerSubStatus1"],
    "Ghost": ["wEnemyMonType1", "wEnemyMonType2"],
    "Spikes": ["wPlayerScreens", "wBossAITurnsElapsed"],
    "SpeciesLevelUp": ["wPlayerMonSpecies", "wBattleMonLevel", "EvosAttacks"],
    "Perish": ["wEnemySubStatus1", "wEnemyPerishCount"],
    "Priority": ["wPlayerUsedMoves", "Moves + MOVE_EFFECT"],
    "Protect": ["wPlayerUsedMoves", "Moves + MOVE_EFFECT"],
    "Recovery": ["wPlayerUsedMoves", "Moves + MOVE_EFFECT"],
    "Encore": ["wPlayerUsedMoves", "wLastPlayerMove"],
    "CounterCoat": ["wPlayerUsedMoves", "Moves + MOVE_EFFECT"],
}


@dataclass(frozen=True)
class RuleLabel:
    rule_id: str
    source_file: str
    source_label: str
    line: int
    parent_label: str | None
    classification: str
    public_reads: tuple[str, ...]
    expected_public_inputs: tuple[str, ...]
    executable: bool
    dynamic_coverage_target: bool
    score_trace_target: bool
    requires_public_read_provenance: bool
    coverage_mode: str


def build_rule_map(paths: tuple[Path, ...] = SOURCE_PATHS) -> dict[str, Any]:
    rules: list[RuleLabel] = []
    source_hashes: dict[str, str] = {}
    for path in paths:
        if not path.exists():
            raise PreferenceDataError(f"missing Boss AI source file: {path}")
        source_hashes[display_path(path)] = sha256_text(path)
        rules.extend(parse_rule_labels(path))

    payload = {
        "schema_version": 1,
        "generator": "tools.boss_ai_debugger.rule_map",
        "source_hashes": source_hashes,
        "rule_count": len(rules),
        "rules": [rule_to_json(rule) for rule in sorted(rules, key=rule_sort_key)],
    }
    errors = validate_rule_map(payload)
    if errors:
        raise PreferenceDataError("\n".join(errors))
    return payload


def parse_rule_labels(path: Path) -> list[RuleLabel]:
    rules: list[RuleLabel] = []
    parent: str | None = None
    subsystem = subsystem_for_path(path)
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.split(";", 1)[0].strip()
        match = LABEL_RE.match(line)
        if match is None:
            continue
        label = match.group("local") or match.group("top")
        if not label.startswith("."):
            parent = label
        if not is_rule_label(label):
            continue
        rule_id = make_rule_id(subsystem, label, parent)
        public_reads = tuple(public_reads_for(label, parent))
        executable = is_executable_rule_label(label, parent)
        score_trace_target = is_score_trace_rule(path, label, parent)
        rules.append(
            RuleLabel(
                rule_id=rule_id,
                source_file=display_path(path),
                source_label=label,
                line=line_number,
                parent_label=parent,
                classification=classify_label(label, parent),
                public_reads=public_reads,
                expected_public_inputs=public_reads,
                executable=executable,
                dynamic_coverage_target=executable,
                score_trace_target=score_trace_target,
                requires_public_read_provenance=(
                    classify_label(label, parent) == "public_info" and bool(public_reads)
                ),
                coverage_mode=coverage_mode_for(path, label, parent, executable),
            )
        )
    return rules


def is_rule_label(label: str) -> bool:
    if label.startswith("BossAI_"):
        return True
    if label in GENERIC_LOCAL_LABELS:
        return False
    stripped = label.lstrip(".")
    return stripped.startswith(
        (
            "Apply",
            "Has",
            "Player",
            "Enemy",
            "Boss",
            "Species",
            "Status",
            "Utility",
            "Current",
            "Setup",
            "Rapid",
            "Spikes",
            "Self",
            "Choice",
            "Counter",
            "Known",
            "Find",
            "Compute",
            "Refine",
            "Should",
            "Is",
            "Try",
        )
    )


def make_rule_id(subsystem: str, label: str, parent: str | None) -> str:
    stem = label.lstrip(".")
    if label.startswith(".") and parent:
        parent_stem = parent.removeprefix("BossAI_")
        return f"{subsystem}.{snake(parent_stem)}.{snake(stem)}"
    if stem.startswith("BossAI_"):
        stem = stem.removeprefix("BossAI_")
    return f"{subsystem}.{snake(stem)}"


def classify_label(label: str, parent: str | None) -> str:
    combined = f"{parent or ''} {label}"
    if "Haki" in combined:
        return "haki_exception"
    if any(token in combined for token in ("Revealed", "Public", "Seen", "Known")):
        return "public_info"
    if any(token in combined for token in ("RapidSpin", "Spikes", "Foresight", "Ghost")):
        return "public_info"
    if label.startswith("BossAI_"):
        return "platform_boundary"
    return "internal"


def public_reads_for(label: str, parent: str | None) -> list[str]:
    combined = f"{parent or ''}{label}"
    reads: list[str] = []
    for hint, symbols in PUBLIC_READ_HINTS.items():
        if hint in combined:
            reads.extend(symbols)
    return sorted(set(reads))


def is_executable_rule_label(label: str, parent: str | None) -> bool:
    full_symbol = full_symbol_for_label(label, parent)
    if not full_symbol:
        return False
    hook_label = full_symbol.rsplit(".", 1)[-1]
    if hook_label.startswith("BossAI") and not hook_label.startswith("BossAI_"):
        return False
    return True


def full_symbol_for_label(label: str, parent: str | None) -> str:
    if label.startswith("."):
        if parent is None:
            return ""
        return f"{parent}{label}"
    return label


def is_score_trace_rule(path: Path, label: str, parent: str | None) -> bool:
    if path.name != "boss_policy_move.asm":
        return False
    return (parent in {"BossAI_ApplyMoveModel", "BossAI_SelectMove"}) or (
        label in {"BossAI_ApplyMoveModel", "BossAI_SelectMove"}
    )


def coverage_mode_for(
    path: Path,
    label: str,
    parent: str | None,
    executable: bool,
) -> str:
    if not executable:
        return "static_reference"
    if is_score_trace_rule(path, label, parent):
        return "rom_score_execution_hook"
    if path.name == "boss_policy_switch.asm":
        return "rom_route_execution_hook"
    return "rom_execution_hook"


def validate_rule_map(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("rule map schema_version must be 1")
    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        return [*errors, "rule map must contain a non-empty rules list"]

    seen_ids: set[str] = set()
    labels: set[str] = set()
    for index, rule in enumerate(rules):
        prefix = f"rules[{index}]"
        if not isinstance(rule, dict):
            errors.append(f"{prefix}: rule must be an object")
            continue
        rule_id = rule.get("rule_id")
        if not isinstance(rule_id, str) or not rule_id:
            errors.append(f"{prefix}: missing rule_id")
        elif rule_id in seen_ids:
            errors.append(f"{prefix}: duplicate rule_id {rule_id!r}")
        else:
            seen_ids.add(rule_id)
        label = rule.get("source_label")
        if isinstance(label, str):
            labels.add(label)
            if label.startswith(".") and not isinstance(rule.get("parent_label"), str):
                errors.append(f"{prefix}: local label {label!r} is missing parent_label")
        if rule.get("classification") not in {
            "public_info",
            "haki_exception",
            "platform_boundary",
            "internal",
        }:
            errors.append(f"{prefix}: invalid classification")
        for key in (
            "executable",
            "dynamic_coverage_target",
            "score_trace_target",
            "requires_public_read_provenance",
        ):
            if key in rule and not isinstance(rule.get(key), bool):
                errors.append(f"{prefix}: {key} must be a boolean")
        expected_inputs = rule.get("expected_public_inputs", [])
        if expected_inputs is not None and not isinstance(expected_inputs, list):
            errors.append(f"{prefix}: expected_public_inputs must be a list")
        if rule.get("requires_public_read_provenance") and not expected_inputs:
            errors.append(
                f"{prefix}: public-read provenance target has no expected inputs"
            )
        coverage_mode = rule.get("coverage_mode", "")
        if coverage_mode and coverage_mode not in {
            "rom_execution_hook",
            "rom_route_execution_hook",
            "rom_score_execution_hook",
            "static_reference",
        }:
            errors.append(f"{prefix}: invalid coverage_mode")

    missing = sorted(REQUIRED_LABELS - labels)
    if missing:
        errors.append("required Boss AI labels missing from rule map: " + ", ".join(missing))
    return errors


def compare_rule_maps(current: dict[str, Any], expected_path: Path) -> list[str]:
    if not expected_path.exists():
        return []
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    errors = validate_rule_map(expected)
    if errors:
        return [f"{expected_path}: {error}" for error in errors]
    current_ids = {rule["rule_id"] for rule in current["rules"]}
    expected_ids = {rule["rule_id"] for rule in expected["rules"]}
    missing = sorted(expected_ids - current_ids)
    added = sorted(current_ids - expected_ids)
    problems: list[str] = []
    if missing:
        problems.append("rule ids disappeared: " + ", ".join(missing[:20]))
    if added:
        problems.append("new rule ids not in stored map: " + ", ".join(added[:20]))
    if current.get("source_hashes") != expected.get("source_hashes"):
        problems.append("stored rule map source hashes differ from current source")

    expected_by_id = {rule["rule_id"]: rule for rule in expected["rules"]}
    for rule in current["rules"]:
        rule_id = rule["rule_id"]
        if rule_id not in expected_by_id:
            continue
        expected_rule = expected_by_id[rule_id]
        for key in (
            "source_label",
            "source_file",
            "parent_label",
            "classification",
            "public_reads",
            "expected_public_inputs",
            "executable",
            "dynamic_coverage_target",
            "score_trace_target",
            "requires_public_read_provenance",
            "coverage_mode",
        ):
            if rule.get(key) != expected_rule.get(key):
                problems.append(f"{rule_id}: stored {key} differs from current")
                break
    return problems


def write_rule_map(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def format_rule_map_summary(
    data: dict[str, Any],
    *,
    compare_errors: list[str] | None = None,
) -> str:
    errors = compare_errors or []
    status = "failed" if errors else "passed"
    counts: dict[str, int] = {}
    executable = 0
    dynamic_targets = 0
    score_targets = 0
    provenance_targets = 0
    for rule in data["rules"]:
        key = str(rule["classification"])
        counts[key] = counts.get(key, 0) + 1
        executable += int(bool(rule.get("executable", False)))
        dynamic_targets += int(bool(rule.get("dynamic_coverage_target", False)))
        score_targets += int(bool(rule.get("score_trace_target", False)))
        provenance_targets += int(
            bool(rule.get("requires_public_read_provenance", False))
        )
    count_text = " ".join(f"{key}={counts[key]}" for key in sorted(counts))
    lines = [
        f"Boss AI rule-map check {status}.",
        (
            f"rules={data['rule_count']} executable={executable} "
            f"dynamic_targets={dynamic_targets} score_targets={score_targets} "
            f"public_provenance_targets={provenance_targets} {count_text}"
        ),
    ]
    for error in errors[:20]:
        lines.append(f"  - {error}")
    return "\n".join(lines)


def subsystem_for_path(path: Path) -> str:
    name = path.name
    if "switch" in name:
        return "switch"
    if "move" in name:
        return "move"
    return snake(path.stem)


def rule_sort_key(rule: RuleLabel) -> tuple[str, int, str]:
    return (rule.source_file, rule.line, rule.rule_id)


def rule_to_json(rule: RuleLabel) -> dict[str, Any]:
    return {
        "rule_id": rule.rule_id,
        "source_file": rule.source_file,
        "source_label": rule.source_label,
        "line": rule.line,
        "parent_label": rule.parent_label,
        "classification": rule.classification,
        "public_reads": list(rule.public_reads),
        "expected_public_inputs": list(rule.expected_public_inputs),
        "executable": rule.executable,
        "dynamic_coverage_target": rule.dynamic_coverage_target,
        "score_trace_target": rule.score_trace_target,
        "requires_public_read_provenance": rule.requires_public_read_provenance,
        "coverage_mode": rule.coverage_mode,
    }


def snake(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return value.strip("_").lower()


def sha256_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("/", "\\")
    except ValueError:
        return str(path)
