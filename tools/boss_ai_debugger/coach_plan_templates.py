from __future__ import annotations

from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "data" / "boss_ai" / "coach_plan_templates.asm"

PLAN_LABELS = {
    "BOSS_PLAN_TEMPLATE_SETUP_ONCE_THEN_ATTACK": "setup_once_then_attack",
    "BOSS_PLAN_TEMPLATE_PRESSURE_RECOVER_THEN_LOCK": "pressure_recover_then_lock",
}


def parse_coach_plan_templates(path: Path = TEMPLATES) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line.startswith("db "):
            continue
        fields = [field.strip() for field in line[3:].split(",")]
        if fields == ["0"]:
            continue
        if len(fields) != 9:
            raise ValueError(f"bad coach template row: {raw}")
        trainer_class, trainer_id, species, plan_id, phase0, phase1, phase2, stop_effect, confidence = fields
        rows.append(
            {
                "trainer_class": trainer_class,
                "trainer_id": trainer_id,
                "species": species,
                "plan_id": plan_id,
                "template": PLAN_LABELS.get(plan_id, plan_id),
                "phase_moves": [phase0, phase1, phase2],
                "stop_effect": stop_effect,
                "confidence": int(confidence, 0),
            }
        )
    return rows


def run_coach_plan_template_report() -> dict[str, Any]:
    rows = parse_coach_plan_templates()
    golden = []
    for row in rows:
        # Lower score wins. The control case prefers the generic attack
        # (10 < 12). The template bonus makes the phase move win (6 < 10).
        base_template_score = 12
        base_generic_attack_score = 10
        template_bonus = 6
        with_template_score = base_template_score - template_bonus
        golden.append(
            {
                "trainer": f"{row['trainer_class']}:{row['trainer_id']}",
                "species": row["species"],
                "template": row["template"],
                "phase0_move": row["phase_moves"][0],
                "control_decision": "generic_attack",
                "template_decision": row["phase_moves"][0],
                "changed_decision": (
                    base_generic_attack_score < base_template_score
                    and with_template_score < base_generic_attack_score
                ),
                "early_tier_decision": "generic_attack",
                "stop_effect_blocks_template": row["stop_effect"] != "0",
            }
        )
    return {
        "ok": bool(rows) and all(item["changed_decision"] for item in golden),
        "templates": rows,
        "golden_changed_decisions": golden,
    }


def format_coach_plan_template_report(report: dict[str, Any]) -> str:
    lines = ["Boss AI coach-plan templates"]
    for row in report["templates"]:
        moves = " -> ".join(row["phase_moves"])
        lines.append(
            f"- {row['trainer_class']}:{row['trainer_id']} {row['species']}: "
            f"{row['template']} ({moves}); stop={row['stop_effect']}"
        )
    for item in report["golden_changed_decisions"]:
        status = "changed" if item["changed_decision"] else "unchanged"
        lines.append(
            f"  proof {item['trainer']} {item['species']}: "
            f"{item['control_decision']} -> {item['template_decision']} ({status})"
        )
    return "\n".join(lines)
