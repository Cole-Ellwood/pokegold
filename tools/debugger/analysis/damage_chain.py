"""Player-facing damage chain diagram.

Renders the damage calculation pipeline as a readable breakdown:
  "Wing Attack base 60 -> STAB 90 -> SE 180 -> Variation 158-203 -> 38-46 actual"

This is the P5 "readable, not hex" deliverable. Uses the existing
damage_debugger oracle as the computation backend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChainStep:
    """One step in the damage chain."""
    label: str
    value: int | float | str
    multiplier: float = 1.0
    note: str = ""

    def __str__(self) -> str:
        if self.note:
            return f"{self.label}: {self.value} ({self.note})"
        return f"{self.label}: {self.value}"


@dataclass
class DamageChainDiagram:
    """Full damage chain from base power to final HP change."""
    attacker: str = ""
    defender: str = ""
    move: str = ""
    steps: list[ChainStep] = field(default_factory=list)
    final_low: int = 0
    final_high: int = 0
    hp_before: int = 0
    hp_max: int = 0

    def add_step(self, label: str, value: Any, multiplier: float = 1.0, note: str = "") -> None:
        self.steps.append(ChainStep(label=label, value=value, multiplier=multiplier, note=note))

    @property
    def final_range(self) -> str:
        return f"{self.final_low}-{self.final_high}"

    @property
    def percent_range(self) -> str:
        if self.hp_max <= 0:
            return "?"
        lo_pct = self.final_low * 100 // self.hp_max
        hi_pct = self.final_high * 100 // self.hp_max
        return f"{lo_pct}-{hi_pct}%"

    def render_text(self) -> str:
        lines = []
        header = f"{self.attacker}'s {self.move} vs {self.defender}"
        lines.append(header)
        lines.append("=" * len(header))

        for step in self.steps:
            lines.append(f"  {step}")

        lines.append("")
        lines.append(f"  Final damage: {self.final_range} ({self.percent_range} of {self.hp_max} HP)")
        if self.hp_before > 0:
            hp_after_lo = max(0, self.hp_before - self.final_high)
            hp_after_hi = max(0, self.hp_before - self.final_low)
            lines.append(f"  HP: {self.hp_before} -> {hp_after_lo}-{hp_after_hi}")
        return "\n".join(lines)

    def render_arrow(self) -> str:
        parts = []
        for step in self.steps:
            parts.append(f"{step.label} {step.value}")
        return " -> ".join(parts) + f" -> {self.final_range} actual"

    def render_markdown(self) -> str:
        lines = [
            f"### {self.attacker}'s {self.move} vs {self.defender}",
            "",
            "| Step | Value | Note |",
            "|------|-------|------|",
        ]
        for step in self.steps:
            lines.append(f"| {step.label} | {step.value} | {step.note} |")
        lines.append("")
        lines.append(f"**Damage: {self.final_range} ({self.percent_range})**")
        return "\n".join(lines)


def build_chain_from_oracle_result(
    attacker: str,
    defender: str,
    move: str,
    oracle_result: dict[str, Any],
) -> DamageChainDiagram:
    """Build a diagram from a damage_debugger oracle result dict."""
    chain = DamageChainDiagram(attacker=attacker, defender=defender, move=move)

    if "base_power" in oracle_result:
        chain.add_step("Base power", oracle_result["base_power"])
    if "attack_stat" in oracle_result:
        chain.add_step("Attack stat", oracle_result["attack_stat"])
    if "defense_stat" in oracle_result:
        chain.add_step("Defense stat", oracle_result["defense_stat"])
    if "level" in oracle_result:
        chain.add_step("Level", oracle_result["level"])
    if "base_damage" in oracle_result:
        chain.add_step("Base damage", oracle_result["base_damage"], note="floor((2*L/5+2)*P*A/D)/50+2")
    if "stab" in oracle_result and oracle_result["stab"]:
        chain.add_step("STAB", "x1.5", multiplier=1.5)
    if "type_effectiveness" in oracle_result:
        eff = oracle_result["type_effectiveness"]
        if eff != 1.0:
            chain.add_step("Type effectiveness", f"x{eff}", multiplier=eff)
    if "item_boost" in oracle_result:
        boost = oracle_result["item_boost"]
        if boost != 1.0:
            chain.add_step("Item boost", f"x{boost}", multiplier=boost)
    if "weather" in oracle_result:
        w = oracle_result["weather"]
        if w != 1.0:
            chain.add_step("Weather", f"x{w}", multiplier=w)
    if "critical" in oracle_result and oracle_result["critical"]:
        chain.add_step("Critical hit", "x2", multiplier=2.0)

    chain.final_low = oracle_result.get("damage_low", 0)
    chain.final_high = oracle_result.get("damage_high", 0)
    chain.hp_before = oracle_result.get("defender_hp", 0)
    chain.hp_max = oracle_result.get("defender_max_hp", 0)

    return chain
