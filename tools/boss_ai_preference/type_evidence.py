from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
import json
import re
from pathlib import Path
from typing import Any

from .benchmark_positions import (
    load_benchmark_oracles,
    load_benchmarks,
)
from .data import ROOT


TYPE_CHART_PATH = ROOT / "data" / "types" / "type_matchups.asm"
MECHANICS_OVERVIEW_PATH = (
    ROOT / "docs" / "agent_navigation" / "gen2_vs_modern_mechanics.md"
)
GENERATED_MECHANICS_TABLE_PATH = (
    ROOT / "docs" / "agent_navigation" / "hack_mechanics_reference.md"
)
TYPE_PASSIVES_PATH = ROOT / "engine" / "battle" / "type_passive_damage_mods.asm"
SPIKES_PATH = ROOT / "engine" / "battle" / "move_effects" / "spikes.asm"
RAPID_SPIN_PATH = ROOT / "engine" / "battle" / "move_effects" / "rapid_spin.asm"
BATTLE_CORE_PATH = ROOT / "engine" / "battle" / "core.asm"

DEFAULT_TYPE_EVIDENCE_REPORT_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "type_effectiveness_evidence.md"
)
DEFAULT_TYPE_EVIDENCE_JSON_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "type_effectiveness_evidence.json"
)
DEFAULT_POLICY_ANSWERS_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "state_transition_policy_answers.json"
)

ACTUAL_MECHANICS_SOURCE_PATHS = {
    "data/types/type_matchups.asm",
    "docs/agent_navigation/gen2_vs_modern_mechanics.md",
    "docs/agent_navigation/hack_mechanics_reference.md",
    "engine/battle/type_passive_damage_mods.asm",
    "engine/battle/move_effects/spikes.asm",
    "engine/battle/move_effects/rapid_spin.asm",
    "engine/battle/core.asm",
}
TYPE_EFFECTIVENESS_EVIDENCE_PATHS = {
    "data/types/type_matchups.asm",
    "docs/agent_navigation/gen2_vs_modern_mechanics.md",
    "docs/agent_navigation/hack_mechanics_reference.md",
    "engine/battle/type_passive_damage_mods.asm",
}
FACTOR_CONSTANTS = {
    "NO_EFFECT": 0,
    "NOT_VERY_EFFECTIVE": 5,
    "EFFECTIVE": 10,
    "SUPER_EFFECTIVE": 20,
}
FACTOR_LABELS = {
    0: "immune",
    5: "resisted",
    10: "neutral",
    20: "super_effective",
}
TYPE_CLAIM_RE = re.compile(
    r"\b(super[- ]effective|resisted|resists?|resistance|immune|immunity|"
    r"neutral|no[- ]effect|no effect)\b",
    re.IGNORECASE,
)
TYPE_CHART_TWEAKS = [
    {
        "id": "ground_ghost_immunity",
        "attack": "GROUND",
        "defend": "GHOST",
        "vanilla_factor": 10,
        "hack_factor": 0,
    },
    {
        "id": "water_ice_resisted",
        "attack": "WATER",
        "defend": "ICE",
        "vanilla_factor": 10,
        "hack_factor": 5,
    },
    {
        "id": "ground_fire_neutral",
        "attack": "GROUND",
        "defend": "FIRE",
        "vanilla_factor": 20,
        "hack_factor": 10,
    },
    {
        "id": "steel_fighting_resisted",
        "attack": "STEEL",
        "defend": "FIGHTING",
        "vanilla_factor": 10,
        "hack_factor": 5,
    },
    {
        "id": "rock_psychic_resisted",
        "attack": "ROCK",
        "defend": "PSYCHIC_TYPE",
        "vanilla_factor": 10,
        "hack_factor": 5,
    },
    {
        "id": "normal_psychic_resisted",
        "attack": "NORMAL",
        "defend": "PSYCHIC_TYPE",
        "vanilla_factor": 10,
        "hack_factor": 5,
    },
    {
        "id": "ghost_steel_no_effect",
        "attack": "GHOST",
        "defend": "STEEL",
        "vanilla_factor": 5,
        "hack_factor": 0,
    },
    {
        "id": "ghost_fighting_super_effective",
        "attack": "GHOST",
        "defend": "FIGHTING",
        "vanilla_factor": 10,
        "hack_factor": 20,
    },
    {
        "id": "poison_normal_super_effective",
        "attack": "POISON",
        "defend": "NORMAL",
        "vanilla_factor": 10,
        "hack_factor": 20,
    },
    {
        "id": "dark_steel_neutral",
        "attack": "DARK",
        "defend": "STEEL",
        "vanilla_factor": 5,
        "hack_factor": 10,
    },
    {
        "id": "steel_electric_neutral",
        "attack": "STEEL",
        "defend": "ELECTRIC",
        "vanilla_factor": 5,
        "hack_factor": 10,
    },
    {
        "id": "grass_flying_neutral",
        "attack": "GRASS",
        "defend": "FLYING",
        "vanilla_factor": 5,
        "hack_factor": 10,
    },
    {
        "id": "fighting_poison_neutral",
        "attack": "FIGHTING",
        "defend": "POISON",
        "vanilla_factor": 5,
        "hack_factor": 10,
    },
    {
        "id": "fighting_bug_neutral",
        "attack": "FIGHTING",
        "defend": "BUG",
        "vanilla_factor": 5,
        "hack_factor": 10,
    },
    {
        "id": "psychic_poison_neutral",
        "attack": "PSYCHIC_TYPE",
        "defend": "POISON",
        "vanilla_factor": 20,
        "hack_factor": 10,
    },
]


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def strip_comment(line: str) -> str:
    return line.split(";", 1)[0].strip()


def parse_type_matchups(
    path: Path = TYPE_CHART_PATH,
) -> dict[tuple[str, str], int]:
    chart: dict[tuple[str, str], int] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        code = strip_comment(raw)
        if code == "db -1":
            break
        if not code or code == "db -2":
            continue
        match = re.match(
            r"db\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)",
            code,
        )
        if not match:
            continue
        attack_type, defend_type, factor = match.groups()
        chart[(attack_type, defend_type)] = FACTOR_CONSTANTS[factor]
    return chart


def factor_label(factor: int) -> str:
    return FACTOR_LABELS.get(factor, f"factor_{factor}")


def chart_factor(
    chart: dict[tuple[str, str], int],
    attack_type: str,
    defend_type: str,
) -> int:
    return chart.get((attack_type, defend_type), 10)


def build_type_chart_assertions() -> list[dict[str, Any]]:
    chart = parse_type_matchups()
    rows: list[dict[str, Any]] = []
    for tweak in TYPE_CHART_TWEAKS:
        actual = chart_factor(chart, tweak["attack"], tweak["defend"])
        expected = int(tweak["hack_factor"])
        rows.append(
            {
                "id": tweak["id"],
                "claim_plane": "chart_result",
                "mechanics_profile": "romhack_gym_leader_lab",
                "attack_type": tweak["attack"],
                "defend_type": tweak["defend"],
                "vanilla_factor": tweak["vanilla_factor"],
                "vanilla_label": factor_label(int(tweak["vanilla_factor"])),
                "expected_hack_factor": expected,
                "expected_hack_label": factor_label(expected),
                "actual_hack_factor": actual,
                "actual_hack_label": factor_label(actual),
                "source": "data/types/type_matchups.asm",
                "passes": actual == expected,
            }
        )
    return rows


def normalized_source_ref(source_ref: str) -> str:
    return source_ref.split(":", 1)[0].replace("\\", "/")


def source_paths_seen(source_refs: Iterable[Any]) -> list[str]:
    return sorted(
        {
            normalized_source_ref(str(source_ref))
            for source_ref in source_refs
            if isinstance(source_ref, str)
        }
    )


def has_environment_specific_type_evidence(source_refs: Iterable[Any]) -> bool:
    return bool(set(source_paths_seen(source_refs)) & TYPE_EFFECTIVENESS_EVIDENCE_PATHS)


def claim_planes_for_text(text: str) -> list[str]:
    lower = text.lower()
    planes = ["chart_result"]
    if any(token in lower for token in ("passive", "majesty", "imperial scales")):
        planes.append("passive_adjusted_result")
    if any(token in lower for token in ("damage", "ko", "range", "hp", "%")):
        planes.append("final_damage")
    if any(
        token in lower
        for token in (
            "best",
            "acceptable",
            "catastrophic",
            "move",
            "line",
            "answer",
            "switch",
            "route",
        )
    ):
        planes.append("strategic_move_label")
    return planes


def iter_text_claims(value: Any, path: str = "$") -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "source_refs":
                continue
            yield from iter_text_claims(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_text_claims(child, f"{path}[{index}]")
    elif isinstance(value, str):
        terms = sorted({match.group(0).lower() for match in TYPE_CLAIM_RE.finditer(value)})
        if terms:
            yield {
                "path": path,
                "terms": terms,
                "text": value,
                "claim_planes": claim_planes_for_text(value),
            }


def card_claims(
    source_name: str,
    benchmark_id: str,
    mechanics_profile: str,
    source_refs: list[Any],
    payload: Any,
) -> list[dict[str, Any]]:
    evidence_paths = source_paths_seen(source_refs)
    has_evidence = has_environment_specific_type_evidence(source_refs)
    return [
        {
            "source_name": source_name,
            "benchmark_id": benchmark_id,
            "location": claim["path"],
            "mechanics_profile": mechanics_profile,
            "terms": claim["terms"],
            "claim_planes": claim["claim_planes"],
            "text": claim["text"],
            "source_paths_seen": evidence_paths,
            "has_environment_specific_evidence": has_evidence,
        }
        for claim in iter_text_claims(payload)
    ]


def load_policy_answers(path: Path = DEFAULT_POLICY_ANSWERS_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    answers = data.get("answers", [])
    return answers if isinstance(answers, list) else []


def build_type_evidence_report(
    benchmarks: list[dict[str, Any]] | None = None,
    oracles: list[dict[str, Any]] | None = None,
    policy_answers: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    benchmarks = benchmarks or load_benchmarks()
    oracles = oracles or load_benchmark_oracles()
    policy_answers = policy_answers if policy_answers is not None else load_policy_answers()
    benchmark_by_id = {benchmark["id"]: benchmark for benchmark in benchmarks}
    oracle_by_id = {row["id"]: row.get("oracle", {}) for row in oracles}

    text_claims: list[dict[str, Any]] = []
    for benchmark in benchmarks:
        text_claims.extend(
            card_claims(
                "public_card",
                benchmark["id"],
                benchmark["mechanics_profile"],
                list(benchmark.get("source_refs", [])),
                benchmark,
            )
        )
        oracle = oracle_by_id.get(benchmark["id"])
        if oracle is not None:
            text_claims.extend(
                card_claims(
                    "hidden_oracle",
                    benchmark["id"],
                    benchmark["mechanics_profile"],
                    list(benchmark.get("source_refs", [])),
                    oracle,
                )
            )

    for answer in policy_answers:
        benchmark_id = str(answer.get("benchmark_id", ""))
        benchmark = benchmark_by_id.get(benchmark_id)
        if benchmark is None:
            continue
        text_claims.extend(
            card_claims(
                "policy_answer",
                benchmark_id,
                str(answer.get("mechanics_profile_seen", benchmark["mechanics_profile"])),
                list(benchmark.get("source_refs", [])),
                answer,
            )
        )

    unsupported_claims = [
        claim for claim in text_claims if not claim["has_environment_specific_evidence"]
    ]
    chart_assertions = build_type_chart_assertions()
    steel_ghost_dark_assertion_ids = {
        "dark_steel_neutral",
        "ghost_steel_no_effect",
    }
    steel_ghost_dark_assertions = [
        row for row in chart_assertions if row["id"] in steel_ghost_dark_assertion_ids
    ]

    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "required_source_paths": sorted(ACTUAL_MECHANICS_SOURCE_PATHS),
        "type_evidence_source_paths": sorted(TYPE_EFFECTIVENESS_EVIDENCE_PATHS),
        "source_hierarchy": {
            "general_mechanics": "source code is authority for general mechanics",
            "exact_battle_state_damage": "validated debugger trace is authority for exact battle-state damage",
            "disagreement": "treat disagreement as source/tooling/version mismatch and investigate",
        },
        "claim_planes": [
            "chart_result",
            "passive_adjusted_result",
            "final_damage",
            "strategic_move_label",
        ],
        "chart_tweak_count": len(chart_assertions),
        "chart_tweaks_pass": all(row["passes"] for row in chart_assertions),
        "chart_tweaks": chart_assertions,
        "steel_ghost_dark_divergence_pass": all(
            row["passes"] for row in steel_ghost_dark_assertions
        ),
        "steel_ghost_dark_divergence": steel_ghost_dark_assertions,
        "text_claim_count": len(text_claims),
        "unsupported_text_claim_count": len(unsupported_claims),
        "text_claims_pass": not unsupported_claims,
        "unsupported_text_claims": unsupported_claims,
        "text_claims": text_claims,
        "all_pass": (
            all(row["passes"] for row in chart_assertions)
            and not unsupported_claims
        ),
    }


def render_type_evidence_report(report: dict[str, Any]) -> str:
    lines = [
        "# Type-Effectiveness Evidence Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Chart tweaks checked: {report['chart_tweak_count']}",
        f"- Chart tweaks pass: `{report['chart_tweaks_pass']}`",
        f"- Steel/Ghost/Dark divergence pass: `{report['steel_ghost_dark_divergence_pass']}`",
        f"- Text claims scanned: {report['text_claim_count']}",
        f"- Unsupported text claims: {report['unsupported_text_claim_count']}",
        f"- All pass: `{report['all_pass']}`",
        "",
        "## Source Hierarchy",
        "",
        f"- General mechanics: {report['source_hierarchy']['general_mechanics']}.",
        f"- Exact battle-state damage: {report['source_hierarchy']['exact_battle_state_damage']}.",
        f"- Disagreement: {report['source_hierarchy']['disagreement']}.",
        "",
        "## Required Source Paths",
        "",
        *[f"- `{path}`" for path in report["required_source_paths"]],
        "",
        "## Romhack Type-Chart Tweaks",
        "",
        "| ID | Attack | Defend | Vanilla | Romhack | Source | Pass |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["chart_tweaks"]:
        lines.append(
            "| "
            f"`{row['id']}` | "
            f"`{row['attack_type']}` | "
            f"`{row['defend_type']}` | "
            f"`{row['vanilla_label']}` | "
            f"`{row['actual_hack_label']}` | "
            f"`{row['source']}` | "
            f"`{row['passes']}` |"
        )

    lines.extend(["", "## Unsupported Text Claims", ""])
    if report["unsupported_text_claims"]:
        for claim in report["unsupported_text_claims"]:
            lines.extend(
                [
                    f"- `{claim['source_name']}:{claim['benchmark_id']}:{claim['location']}`",
                    f"  - terms: `{claim['terms']}`",
                    f"  - mechanics profile: `{claim['mechanics_profile']}`",
                    f"  - source paths seen: `{claim['source_paths_seen']}`",
                    f"  - text: {claim['text']}",
                ]
            )
    else:
        lines.append("- none")

    return "\n".join(lines)


def write_type_evidence_report(
    out_path: Path = DEFAULT_TYPE_EVIDENCE_REPORT_PATH,
    json_out_path: Path | None = DEFAULT_TYPE_EVIDENCE_JSON_PATH,
) -> dict[str, Any]:
    report = build_type_evidence_report()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_type_evidence_report(report), encoding="utf-8", newline="\n")
    if json_out_path is not None:
        json_out_path.parent.mkdir(parents=True, exist_ok=True)
        json_out_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return report
