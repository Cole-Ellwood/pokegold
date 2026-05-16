"""Analysis layer: coverage, counterfactuals, fuzz, static audits, battle viz.

Modules:
  damage_chain     — Player-facing damage chain diagram (P5)
  battle_inspector — Live battle state one-page summary (P5)
  metamorphic      — Damage metamorphic relations (P5)
  battle_fuzz      — Hypothesis RuleBasedStateMachine battle fuzz (P5)
  hdd_minimize     — Hierarchical Delta Debugging over scenario JSON (P5)
  static/          — Whole-ROM static analyzer (P7)
"""

__all__ = [
    "battle_inspector",
    "damage_chain",
    "metamorphic",
    "battle_fuzz",
    "hdd_minimize",
]
